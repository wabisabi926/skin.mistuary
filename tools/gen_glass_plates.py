#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_glass_plates.py — 生成浮窗面板用的「渐变玻璃」贴图。

为什么需要它
------------
原来的 shapes/round<N>.png 是**均匀全白**的圆角块，乘上 glass_frosted(50%)
得到的是一块均匀的 50% 灰板：中心不够实（文字飘）、边缘不够透（像塑料板）。
所以「透」和「糊」同时存在。

本脚本生成 shapes/glass<N>.png：**中心 alpha 255、边缘 alpha 150**，
中间一段平滑过渡。配合 colordiffuse 的 alpha（glass_frosted = 50%），得到
    中心 50%  ·  边缘 29%
——面板中心足够实，边缘仍能明显透出底下的画面。

技术约束（改之前先读）
----------------------
1. 贴图是 **9-slice** 使用的（border = 圆角半径 N，画布尺寸 = 2N+2）。
   所以渐变带必须完全落在最外圈 N 像素之内，且**沿直边方向必须是均匀的**，
   否则边条被拉伸后会出现横向条纹。实现上把「到四边的距离」和「圆角遮罩」
   分开算再相乘，就天然满足这个条件。
2. 不要往里加噪点：中间 2×2 像素的区域会被拉伸到整块面板，
   噪点会被拉成明显的涂抹痕迹。
3. colordiffuse 的 alpha 与贴图 alpha **相乘**，所以颜色 token 的 alpha
   语义是「不透明度上限」，不是「均匀不透明度」。

用法
----
  python tools/gen_glass_plates.py            # 生成全部半径
  python tools/gen_glass_plates.py --check    # 只检查是否已存在/是否过期
"""

import argparse
import os
import sys

from PIL import Image

# 与 media/shapes/round<N>.png 保持同一套半径，避免 NaraDialogGlassTexture
# 换了 radius 参数却找不到贴图。
# 只有 20 在用：NaraDialogGlassTexture 的 radius 参数默认 20、没有调用方覆盖。
# 其余半径（16/18/28/32/42）2026-10-29 清理时删掉，要加回来在这里补。
RADII = (20,)

EDGE_ALPHA = 180   # 边缘不透明度（0-255），配 glass_dialog 80% → 约 56%
CORE_ALPHA = 255   # 中心不透明度，配 glass_dialog 80% → 80%
RAMP_MAX = 18      # 渐变带最大宽度（像素）
                   # 面板本体 80% 时，边缘这一圈是"看起来像玻璃"的唯一来源：
                   # 拉宽到 18px 让面板"化"进背景；拉太宽（>24）会变成一圈发光晕，显脏


def build_plate(radius: int) -> Image.Image:
    """生成单张玻璃板：圆角半径 radius，画布 (2r+2)²。"""
    size = radius * 2 + 2
    ramp = min(RAMP_MAX, max(6, int(radius * 0.6)))

    # 圆角矩形的有符号距离场，用来做 1px 抗锯齿的形状遮罩。
    cx = cy = (size - 1) / 2.0
    half = (size - 1) / 2.0
    inner = half - radius          # 圆心到直边的距离

    px = bytearray(size * size * 4)
    for y in range(size):
        dy = abs(y - cy) - inner
        # 到四边的最近距离（忽略圆角），渐变沿直边方向均匀 —— 9-slice 拉伸安全
        edge_dist = min(y, size - 1 - y)
        t = min(1.0, edge_dist / float(ramp))
        band = EDGE_ALPHA + (CORE_ALPHA - EDGE_ALPHA) * t

        for x in range(size):
            dx = abs(x - cx) - inner
            # 圆角矩形的 SDF：< 0 在内部
            qx = dx if dx > 0 else 0.0
            qy = dy if dy > 0 else 0.0
            sdf = (qx * qx + qy * qy) ** 0.5 + min(max(dx, dy), 0.0) - radius
            # 1px 抗锯齿：sdf ∈ [-1, 0] 线性过渡
            if sdf >= 0.0:
                cov = 0.0
            elif sdf <= -1.0:
                cov = 1.0
            else:
                cov = -sdf
            a = int(round(band * cov))
            i = (y * size + x) * 4
            px[i] = 255      # R 留白，实际颜色由 colordiffuse 决定
            px[i + 1] = 255
            px[i + 2] = 255
            px[i + 3] = a

    return Image.frombytes("RGBA", (size, size), bytes(px))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None, help="输出目录（默认 <脚本目录>/../media/shapes）")
    ap.add_argument("--check", action="store_true", help="只检查，不写文件")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = args.out or os.path.join(here, os.pardir, "media", "shapes")
    out_dir = os.path.abspath(out_dir)

    missing = []
    for r in RADII:
        path = os.path.join(out_dir, "glass%d.png" % r)
        if args.check:
            if not os.path.exists(path):
                missing.append(path)
            continue
        img = build_plate(r)
        img.save(path)
        print("写入 %s  (%dx%d)" % (path, img.width, img.height))

    if args.check:
        if missing:
            print("缺少贴图 %d 张：" % len(missing))
            for p in missing:
                print("  " + p)
            return 1
        print("glass 贴图齐全（%d 张）" % len(RADII))
    return 0


if __name__ == "__main__":
    sys.exit(main())
