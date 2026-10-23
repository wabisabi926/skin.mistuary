#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xbt_tool.py - Kodi 皮肤 Textures.xbt (XBT v2) 打包/解包工具 (纯 Python, 仅依赖 Pillow)

用法:
  python xbt_tool.py pack   [输入目录] [-o 输出.xbt]     # 默认: 打包 <脚本目录>/media -> media/Textures.xbt
  python xbt_tool.py unpack <文件.xbt> [-o 输出目录]     # 解包 XBT 为 PNG 图片

说明:
  - XBT v2 容器格式与 Kodi 19~22+ 兼容 (Kodi 22 的 XBTF_VERSION_MIN='2')。
  - 贴图统一存储为未压缩 A8R8G8B8 (BGRA 字节序, 与官方 TexturePacker 相同),
    全不透明的贴图置 XB_FMT_OPAQUE (0x10000) 标志。
  - 帧数据用 LZO1X 压缩 (与官方 liblzo lzo1x 兼容); 压缩无收益时存原始数据。
  - LZO1X 实现移植自 Linux kernel lib/lzo (GPL-2.0, Markus F.X.J. Oberhumer 的 LZO 算法)。
  - 与官方工具一致: 路径转小写、256 字节定长、loop=0、静态图 duration=0。
  - 不支持 GIF 多帧 (本皮肤无 GIF); 输入仅接受 .png/.jpg/.jpeg。
"""

import argparse
import os
import struct
import sys

from PIL import Image

# ---------------------------------------------------------------------------
# LZO1X 压缩 (移植自 Linux kernel lib/lzo/lzo1x_compress.c, bitstream_version=0,
# 即经典 liblzo lzo1x_1 格式, Kodi 的 lzo1x_decompress 可直接解压)
# ---------------------------------------------------------------------------

_D_BITS = 13
_D_MASK = (1 << _D_BITS) - 1
_M2_MAX_LEN = 8
_M2_MAX_OFFSET = 0x0800
_M3_MAX_LEN = 33
_M3_MAX_OFFSET = 0x4000
_M4_MAX_LEN = 9
_M3_MARKER = 32
_M4_MARKER = 16
_M4_MAX_OFFSET_V0 = 0xbfff

_u32 = struct.Struct('<I').unpack_from


def lzo1x_1_compress(data):
    """压缩 bytes, 返回 bytes。输出可直接被 liblzo lzo1x_decompress(_safe) 解压。

    单趟实现: 字典全程保留(位置严格递增, 不会自匹配), 偏移超过 M4 上限(0xbfff)
    时按字面量处理。与官方 lzo1x_1 输出格式完全兼容, 压缩率相近。
    """
    n = len(data)
    out = bytearray()
    state_offset = -2   # 上一条匹配指令的控制字节/偏移低位相对 out 末尾的位置

    def le32(pos):
        return _u32(data, pos)[0]

    def emit_literals(start, cnt):
        # 输出 [start, start+cnt) 的字面量; cnt >= 4
        if cnt <= 16:
            out.append(cnt - 3)
        elif cnt <= 18:
            out.append(cnt - 3)
        else:
            tt = cnt - 18
            out.append(0)
            while tt > 255:
                out.append(0)
                tt -= 255
            out.append(tt)
        out.extend(data[start:start + cnt])

    dict_ = [0] * (1 << _D_BITS)
    ii = 0          # 挂起字面量起点
    ipx = 4         # 搜索位置(前 4 字节无更早位置可比, 直接进首段字面量)
    ip_end = n - 20 if n > 20 else 0

    while ipx < ip_end:
        dv = le32(ipx)
        h = ((dv * 0x1824429d) >> (32 - _D_BITS)) & _D_MASK
        m_pos = dict_[h]
        dict_[h] = ipx
        if dv != le32(m_pos) or ipx - m_pos > _M4_MAX_OFFSET_V0:
            ipx += 1 + ((ipx - ii) >> 5)
            continue

        # 命中: 先输出挂起字面量
        lit = ipx - ii
        if lit > 0:
            if lit <= 3:
                out[len(out) + state_offset] |= lit
                out.extend(data[ii:ii + lit])
            else:
                emit_literals(ii, lit)
            ii = ipx

        # 扩展匹配(不超过 ip_end)
        m_len = 4
        while ipx + m_len < ip_end and data[ipx + m_len] == data[m_pos + m_len]:
            if (ipx + m_len + 8 <= ip_end and
                    data[ipx + m_len:ipx + m_len + 8] == data[m_pos + m_len:m_pos + m_len + 8]):
                m_len += 8
            else:
                m_len += 1

        m_off = ipx - m_pos
        ipx += m_len
        if m_len <= _M2_MAX_LEN and m_off <= _M2_MAX_OFFSET:
            mo = m_off - 1
            out.append(((m_len - 1) << 5) | ((mo & 7) << 2))
            out.append(mo >> 3)
        elif m_off <= _M3_MAX_OFFSET:
            mo = m_off - 1
            if m_len <= _M3_MAX_LEN:
                out.append(_M3_MARKER | (m_len - 2))
            else:
                r = m_len - _M3_MAX_LEN
                out.append(_M3_MARKER)
                while r > 255:
                    out.append(0)
                    r -= 255
                out.append(r)
            out.append((mo << 2) & 0xFF)
            out.append((mo >> 6) & 0xFF)
        else:
            mo = m_off - 0x4000
            bit = (mo >> 11) & 8
            if m_len <= _M4_MAX_LEN:
                out.append(_M4_MARKER | bit | (m_len - 2))
            else:
                r = m_len - _M4_MAX_LEN
                out.append(_M4_MARKER | bit)
                while r > 255:
                    out.append(0)
                    r -= 255
                out.append(r)
            out.append((mo << 2) & 0xFF)
            out.append((mo >> 6) & 0xFF)
        state_offset = -2
        ii = ipx

    # 尾部字面量
    t = n - ii
    if t > 0:
        if len(out) == 0 and t <= 238:
            out.append(17 + t)
        elif t <= 3:
            out[len(out) + state_offset] |= t
        elif t <= 18:
            out.append(t - 3)
        else:
            tt = t - 18
            out.append(0)
            while tt > 255:
                out.append(0)
                tt -= 255
            out.append(tt)
        out.extend(data[ii:n])

    # 结束标记 (M4_MARKER|1, 0, 0)
    out.append(_M4_MARKER | 1)
    out.append(0)
    out.append(0)
    return bytes(out)


# ---------------------------------------------------------------------------
# LZO1X 解压 (移植自 Linux kernel lib/lzo/lzo1x_decompress_safe.c 的经典路径,
# 与 liblzo lzo1x_decompress 兼容)
# ---------------------------------------------------------------------------

def lzo1x_decompress(data):
    """解压 LZO1X 数据, 返回 bytes; 格式错误抛 ValueError。"""
    n = len(data)
    if n < 3:
        raise ValueError('lzo: input too short')
    out = bytearray()
    ip = 0
    state = 0

    def le16(pos):
        return data[pos] | (data[pos + 1] << 8)

    def copy_match(m_pos, cnt):
        # 从 out 的 m_pos 处复制 cnt 字节(允许重叠)
        if m_pos < 0:
            raise ValueError('lzo: lookbehind overrun')
        if m_pos + cnt <= len(out):
            out.extend(out[m_pos:m_pos + cnt])
        else:
            p = m_pos
            for _ in range(cnt):
                out.append(out[p])
                p += 1

    # 流首: 首字节 > 17 表示开头是一段字面量(仅此时消费该字节)
    if data[0] > 17:
        ip = 1
        t = data[0] - 17
        if t < 4:
            out += data[ip:ip + t]
            ip += t
            state = t
        else:
            out += data[ip:ip + t]
            ip += t
            state = 4

    while True:
        if ip >= n:
            raise ValueError('lzo: input overrun')
        t = data[ip]
        ip += 1
        if t < 16:
            if state == 0:
                if t == 0:
                    k = 0
                    while data[ip] == 0:
                        ip += 1
                        k += 1
                    t += ((k << 8) - k) + 15 + data[ip]
                    ip += 1
                t += 3
                if ip + t > n:
                    raise ValueError('lzo: input overrun')
                out += data[ip:ip + t]
                ip += t
                state = 4
            elif state != 4:
                nxt = t & 3
                m_pos = len(out) - 1 - (t >> 2) - (data[ip] << 2)
                ip += 1
                copy_match(m_pos, 2)
                if ip + nxt > n:
                    raise ValueError('lzo: input overrun')
                out += data[ip:ip + nxt]
                ip += nxt
                state = nxt
            else:
                nxt = t & 3
                m_pos = len(out) - (1 + _M2_MAX_OFFSET) - (t >> 2) - (data[ip] << 2)
                ip += 1
                copy_match(m_pos, 3)
                if ip + nxt > n:
                    raise ValueError('lzo: input overrun')
                out += data[ip:ip + nxt]
                ip += nxt
                state = nxt
        elif t >= 64:
            nxt = t & 3
            m_pos = len(out) - 1 - ((t >> 2) & 7) - (data[ip] << 3)
            ip += 1
            m_len = (t >> 5) - 1 + 2
            copy_match(m_pos, m_len)
            if ip + nxt > n:
                raise ValueError('lzo: input overrun')
            out += data[ip:ip + nxt]
            ip += nxt
            state = nxt
        elif t >= 32:
            t = (t & 31) + 2
            if t == 2:
                k = 0
                while data[ip] == 0:
                    ip += 1
                    k += 1
                t += ((k << 8) - k) + 31 + data[ip]
                ip += 1
            m_pos = len(out) - 1
            nxt = le16(ip)
            ip += 2
            m_pos -= nxt >> 2
            nxt &= 3
            copy_match(m_pos, t)
            if ip + nxt > n:
                raise ValueError('lzo: input overrun')
            out += data[ip:ip + nxt]
            ip += nxt
            state = nxt
        else:  # 16 <= t < 32 : M4
            nxt = le16(ip)
            m_pos = len(out) - ((t & 8) << 11)
            t = (t & 7) + 2
            if t == 2:
                k = 0
                while data[ip] == 0:
                    ip += 1
                    k += 1
                t += ((k << 8) - k) + 7 + data[ip]
                ip += 1
                nxt = le16(ip)
            ip += 2
            m_pos -= nxt >> 2
            nxt &= 3
            if m_pos == len(out):
                if t != 3:
                    raise ValueError('lzo: bad EOF marker')
                return bytes(out)
            m_pos -= 0x4000
            copy_match(m_pos, t)
            if ip + nxt > n:
                raise ValueError('lzo: input overrun')
            out += data[ip:ip + nxt]
            ip += nxt
            state = nxt


# ---------------------------------------------------------------------------
# XBT v2 容器
# ---------------------------------------------------------------------------

XB_FMT_A8R8G8B8 = 0x10
XB_FMT_OPAQUE = 0x10000
IMAGE_EXTS = {'.png', '.jpg', '.jpeg'}


def pack(input_dir, output_file, verify=True):
    input_dir = os.path.abspath(input_dir)
    # 收集图片(排序保证确定性), 路径用 '/' 并转小写(与官方一致)
    files = []
    for root, dirs, names in os.walk(input_dir):
        dirs.sort()
        for name in sorted(names):
            ext = os.path.splitext(name)[1].lower()
            if ext not in IMAGE_EXTS:
                if ext not in ('.db', '.txt'):
                    print('  跳过(非图片): %s' % os.path.relpath(os.path.join(root, name), input_dir))
                continue
            rel = os.path.relpath(os.path.join(root, name), input_dir).replace('\\', '/').lower()
            files.append((rel, os.path.join(root, name)))

    entries = []   # (path, w, h, fmt, packed_size, unpacked_size, duration, offset)
    content = bytearray()

    for rel, full in files:
        try:
            im = Image.open(full)
            rgba = im.convert('RGBA')
        except Exception as e:
            print('  无法读取 %s: %s' % (rel, e))
            continue
        w, h = rgba.size
        if w <= 0 or h <= 0:
            print('  跳过空图: %s' % rel)
            continue
        raw = rgba.tobytes('raw', 'BGRA')
        fmt = XB_FMT_A8R8G8B8
        alpha_min, alpha_max = rgba.getchannel('A').getextrema()
        if alpha_min == 255:
            fmt |= XB_FMT_OPAQUE

        packed = lzo1x_1_compress(raw)
        if verify:
            if lzo1x_decompress(packed) != raw:
                raise RuntimeError('LZO 往返校验失败: %s' % rel)
        if len(packed) >= len(raw):
            packed = raw   # 压缩无收益, 存原始数据(与官方一致)
        entries.append([rel, w, h, fmt, len(packed), len(raw), 0, 0])
        content += packed

    # 写文件: 头部 + 数据
    header_size = 9 + sum(264 + 40 for _ in entries)
    offset = header_size
    for e in entries:
        e[7] = offset
        offset += e[4]

    with open(output_file, 'wb') as f:
        f.write(b'XBTF')
        f.write(b'2')
        f.write(struct.pack('<I', len(entries)))
        for rel, w, h, fmt, packed_size, unpacked_size, duration, off in entries:
            path_mem = rel.encode('utf-8')[:255]
            f.write(path_mem.ljust(256, b'\x00'))
            f.write(struct.pack('<II', 0, 1))            # loop, 帧数
            f.write(struct.pack('<III', w, h, fmt))
            f.write(struct.pack('<QQ', packed_size, unpacked_size))
            f.write(struct.pack('<I', duration))
            f.write(struct.pack('<Q', off))
        f.write(content)

    total_raw = sum(e[5] for e in entries)
    total_packed = sum(e[4] for e in entries)
    print('打包完成: %s' % output_file)
    print('  贴图数量: %d, 原始数据 %.1f MB -> 压缩后文件 %.1f MB'
          % (len(entries), total_raw / 1048576.0, os.path.getsize(output_file) / 1048576.0))


def unpack(xbt_file, output_dir):
    data = open(xbt_file, 'rb').read()
    if data[:4] != b'XBTF':
        raise ValueError('不是有效的 XBT 文件')
    version = data[4:5]
    count = struct.unpack_from('<I', data, 5)[0]
    os.makedirs(output_dir, exist_ok=True)
    off = 9
    ok = 0
    for _ in range(count):
        path = data[off:off + 256].split(b'\x00')[0].decode('utf-8')
        loop, nframes = struct.unpack_from('<II', data, off + 256)
        off += 264
        for _f in range(nframes):
            w, h, fmt = struct.unpack_from('<III', data, off)
            packed_size, unpacked_size = struct.unpack_from('<QQ', data, off + 12)
            duration, = struct.unpack_from('<I', data, off + 28)
            data_off, = struct.unpack_from('<Q', data, off + 32)
            off += 40
            frame = data[data_off:data_off + packed_size]
            if packed_size < unpacked_size:
                raw = lzo1x_decompress(frame)
            else:
                raw = frame
            if len(raw) != unpacked_size:
                raise ValueError('%s: 解压后大小不符 (%d != %d)' % (path, len(raw), unpacked_size))
            base_fmt = fmt & 0xFFFF
            if base_fmt != XB_FMT_A8R8G8B8:
                print('  跳过不支持的格式 0x%x: %s' % (fmt, path))
                continue
            im = Image.frombytes('RGBA', (w, h), raw, 'raw', 'BGRA')
            out_path = os.path.join(output_dir, *path.split('/'))
            os.makedirs(os.path.dirname(out_path) or output_dir, exist_ok=True)
            im.save(out_path)
            ok += 1
    print('解包完成: %d/%d 张贴图 -> %s' % (ok, count, output_dir))


def main():
    ap = argparse.ArgumentParser(description='Kodi 皮肤 XBT v2 打包/解包工具')
    sub = ap.add_subparsers(dest='cmd', required=True)

    p_pack = sub.add_parser('pack', help='把图片目录打包成 XBT')
    p_pack.add_argument('input', nargs='?', default=None, help='图片目录 (默认: <脚本目录>/media)')
    p_pack.add_argument('-o', '--output', default=None, help='输出 XBT (默认: <输入目录>/Textures.xbt)')
    p_pack.add_argument('--no-verify', action='store_true', help='跳过逐帧 LZO 往返校验')

    p_up = sub.add_parser('unpack', help='把 XBT 解包成 PNG 图片')
    p_up.add_argument('xbt', help='XBT 文件')
    p_up.add_argument('-o', '--output', default=None, help='输出目录 (默认: <XBT所在目录>/Textures_unpacked)')

    args = ap.parse_args()
    if args.cmd == 'pack':
        script_dir = os.path.dirname(os.path.abspath(__file__))
        input_dir = args.input or os.path.join(script_dir, 'media')
        output = args.output or os.path.join(input_dir, 'Textures.xbt')
        pack(input_dir, output, verify=not args.no_verify)
    else:
        out_dir = args.output or os.path.join(
            os.path.dirname(os.path.abspath(args.xbt)), 'Textures_unpacked')
        unpack(args.xbt, out_dir)


if __name__ == '__main__':
    main()
