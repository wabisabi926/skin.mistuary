#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
universalize.py — 把依赖魔改 Kodi 内核的玻璃/圆角皮肤，转换成官方 Kodi 可用的
纯色圆角版本。

处理内容
--------
1. <texture material="glass" ...>  ->  圆角贴图 + colordiffuse="$VAR[GlassTint_*]"
2. <texture cornerradius="R">纯色</texture>  ->  border="R" + shapes/roundR.png
3. 图片类纹理（海报/缩略图等）上的 cornerradius 直接移除（官方 Kodi 无法裁切）
4. cornerinset / cornerborder / cornerglow / glass* / blurradius 全部移除

用法
----
  python extras/universalize.py --dry-run    # 只统计，不写文件
  python extras/universalize.py              # 实际改写
"""

import argparse
import collections
import os
import re
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XML_DIR = os.path.join(ROOT, 'xml')
MEDIA_DIR = os.path.join(ROOT, 'media')
SHAPE_DIR = os.path.join(MEDIA_DIR, 'shapes')

# 这些是纯色填充纹理，可以安全换成圆角遮罩
SOLID_TEXTURES = {
    'colors/white.png',
    'colors/black.png',
    'colors/grey.png',
    'colors/white50.png',
    'colors/white70.png',
}

# glassstyle -> 颜色变量名
STYLE_TINT = {
    'clear': 'GlassTint_clear',
    'regular': 'GlassTint_regular',
    'frosted': 'GlassTint_frosted',
    'dialog': 'GlassTint_dialog',
}
DEFAULT_TINT = 'GlassTint_regular'
# 参数化 glassstyle 无法在 XML 里拼变量名，统一落到 dialog（对话框主用档位）
PARAM_TINT = 'GlassTint_dialog'
# 参数化 cornerradius 的实际取值（已核对全部调用点）
PARAM_RADIUS = 32

# 需要剥离的扩展属性
DROP_ATTRS = {
    'material', 'glassstyle', 'glassedge', 'blurradius',
    'glassprogressiveblur', 'glassbackgroundopacity', 'glassrefractionlevel',
    'glassbodyrefraction', 'glassspecularopacity', 'glassspecularsaturation',
    'cornerradius', 'cornerinset', 'cornerborder', 'cornerglow',
}

TAG_RE = re.compile(
    r'<(?P<name>(?:alt)?texture[a-z]*|bordertexture)'
    r'(?P<attrs>(?:\s+[a-zA-Z_][\w-]*\s*=\s*"[^"]*")*)'
    r'\s*(?:/>|>(?P<content>[^<]*)</(?P=name)>)'
)
ATTR_RE = re.compile(r'([a-zA-Z_][\w-]*)\s*=\s*"([^"]*)"')


def parse_radius(value):
    """把 cornerradius 属性值解析成整数像素。"""
    if value is None:
        return 0
    if value.startswith('$PARAM['):
        return PARAM_RADIUS
    try:
        return int(round(float(value)))
    except ValueError:
        return 0


def make_round_png(radius, path):
    """生成 9-slice 用的圆角方块：尺寸 2R+2，四角半径 R，白色不透明。"""
    r = radius
    size = 2 * r + 2
    ss = 4  # 超采样倍数，保证圆角抗锯齿
    mask = Image.new('L', (size * ss, size * ss), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, size * ss - 1, size * ss - 1], radius=r * ss, fill=255)
    mask = mask.resize((size, size), Image.LANCZOS)
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    img.putalpha(mask)
    img.save(path)


def transform_tag(match, stats, radii):
    """处理单个纹理标签，返回替换后的文本。"""
    name = match.group('name')
    raw_attrs = match.group('attrs') or ''
    content = match.group('content')

    attrs = ATTR_RE.findall(raw_attrs)
    if not attrs:
        return match.group(0)

    adict = dict(attrs)
    is_glass = adict.get('material') == 'glass'
    has_radius = 'cornerradius' in adict

    if not is_glass and not has_radius:
        # 只有 cornerinset/border/glow 的情况，清掉即可
        if not (set(adict) & {'cornerinset', 'cornerborder', 'cornerglow'}):
            return match.group(0)

    radius = parse_radius(adict.get('cornerradius'))
    tint = None
    shape = None

    if is_glass:
        style = adict.get('glassstyle', 'regular')
        if style.startswith('$PARAM['):
            tint = PARAM_TINT
            stats['glass_param_style'] += 1
        else:
            tint = STYLE_TINT.get(style, DEFAULT_TINT)
            stats['glass_%s' % style] = stats.get('glass_%s' % style, 0) + 1
        if radius > 0:
            shape = 'shapes/round%d.png' % radius
            radii.add(radius)
        stats['glass_total'] += 1
    elif radius > 0 and content is not None:
        path = content.strip()
        if path in SOLID_TEXTURES:
            shape = 'shapes/round%d.png' % radius
            radii.add(radius)
            stats['corner_solid'] += 1
        else:
            stats['corner_artwork'] += 1
    elif radius > 0:
        stats['corner_unknown'] += 1

    # 重建属性
    out = []
    for key, value in attrs:
        if key in DROP_ATTRS:
            continue
        out.append((key, value))

    if shape:
        # border 必须等于圆角半径，已有 border 也要覆盖，否则 9-slice 失效、圆角被拉伸
        out = [(k, v) for k, v in out if k != 'border']
        out.append(('border', str(radius)))
    if tint:
        out = [(k, v) for k, v in out if k != 'colordiffuse']
        out.insert(0, ('colordiffuse', '$VAR[%s]' % tint))

    if not out and content is None:
        return match.group(0)

    attr_text = ''.join(' %s="%s"' % (k, v) for k, v in out)
    body = shape if shape else content
    if body is None:
        return '<%s%s />' % (name, attr_text)
    return '<%s%s>%s</%s>' % (name, attr_text, body, name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    files = sorted(f for f in os.listdir(XML_DIR) if f.endswith('.xml'))
    stats = collections.defaultdict(int)
    radii = set()
    changed = []

    # 第一遍：只收集半径并统计
    for fn in files:
        path = os.path.join(XML_DIR, fn)
        with open(path, encoding='utf-8') as f:
            text = f.read()
        TAG_RE.sub(lambda m: transform_tag(m, stats, radii), text)

    print('=== 统计 ===')
    for k in sorted(stats):
        print('  %-22s %d' % (k, stats[k]))
    print('  需要生成的圆角档位: %s' % sorted(radii))

    if args.dry_run:
        return 0

    # 生成圆角贴图
    os.makedirs(SHAPE_DIR, exist_ok=True)
    for r in sorted(radii):
        make_round_png(r, os.path.join(SHAPE_DIR, 'round%d.png' % r))
    print('已生成 %d 张圆角贴图 -> %s' % (len(radii), SHAPE_DIR))

    # 第二遍：实际改写
    for fn in files:
        path = os.path.join(XML_DIR, fn)
        with open(path, encoding='utf-8') as f:
            text = f.read()
        new = TAG_RE.sub(lambda m: transform_tag(m, collections.defaultdict(int), set()), text)
        if new != text:
            with open(path, 'w', encoding='utf-8', newline='') as f:
                f.write(new)
            changed.append(fn)

    print('已改写 %d 个 XML 文件' % len(changed))
    for fn in changed:
        print('  -', fn)
    return 0


if __name__ == '__main__':
    sys.exit(main())
