#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_corner_masks.py — 生成海报/缩略图的「角部遮盖」贴图。

它干什么
--------
Kodi 没法给位图裁圆角（`<texture diffuse=...>` 只做 RGB 相乘，不改 alpha），
所以圆角是"盖"出来的：一张和图片等大的贴图，**圆角矩形之外填深色、之内全透明**，
叠在图片上，就把四个方角盖掉了。

代价
----
盖必须用不透明色，所以四角在亮背景（fanart）上会露出深色缺口。
这是方案固有的，调半径救不了 —— 半径由描边环决定，缩半径会在环内缘和圆角之间
露出一圈深色，比缺口更脏。

ALPHA 是唯一能调的旋钮：100% 是硬黑缺口，88% 会透出一点背景、看起来像暗角。

几何约束（改之前先读）
----------------------
- 遮盖半径 = **描边环内缘 − 1**。当前环是 `ring_card_*_r14`（外径 14、描边 3 → 内缘 11），
  所以遮盖半径取 11；`corner_320x180` 配 r12 的环，取 9。
- 画布尺寸必须和图片控件**完全一致**，否则缺口会跑到图片外面。

用法
----
  python tools/gen_corner_masks.py            # 重新生成
  python tools/gen_corner_masks.py --check    # 只检查是否齐全
"""

import argparse
import os
import sys

from PIL import Image

# (文件名, 宽, 高, 圆角半径)
MASKS = (
    ("corner_244x352_r11.png", 244, 352, 11),
    ("corner_214x321_r11.png", 214, 321, 11),
    ("corner_320x180_r9.png", 320, 180, 9),
    ("corner_221x221_r9.png", 221, 221, 9),
    ("corner_200x200_r9.png", 200, 200, 9),
    ("corner_186x186_r9.png", 186, 186, 9),
)

# 遮盖色。**不要再改回接近纯黑**：
#   #0F0F12 压在亮背景上只剩 24 级灰，看起来就是个黑洞；
#   #2A2A2E 同样条件下是 53 级灰，读作"灰影"，而且放在暗背景上几乎看不见。
# alpha 决定缺口有多硬：
#   255 = 硬边（最干净，但亮背景上最显眼）
#   200 = 78%，透出两成背景，缺口变成柔和的暗角（当前取值）
#   < 170 时海报方角的残影会明显显形
FILL_RGB = (0x2A, 0x2A, 0x2E)
ALPHA = 200


def build_mask(w: int, h: int, radius: int) -> Image.Image:
    cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
    hx, hy = (w - 1) / 2.0, (h - 1) / 2.0
    inner_x, inner_y = hx - radius, hy - radius

    buf = bytearray(w * h * 4)
    for y in range(h):
        dy = abs(y - cy) - inner_y
        for x in range(w):
            dx = abs(x - cx) - inner_x
            qx = dx if dx > 0 else 0.0
            qy = dy if dy > 0 else 0.0
            sdf = (qx * qx + qy * qy) ** 0.5 + min(max(dx, dy), 0.0) - radius
            # 圆角矩形内的覆盖率：sdf<0 在内部。+1 让边界那一像素算满，
            # 免得图片最外圈漏出一条原色。
            cov = 1.0 - sdf
            if cov <= 0.0:
                cov = 0.0
            elif cov >= 1.0:
                cov = 1.0
            # 内部透明、外部填色 —— 所以 alpha 用 (1-cov)
            a = int(round(ALPHA * (1.0 - cov)))
            i = (y * w + x) * 4
            buf[i] = FILL_RGB[0]
            buf[i + 1] = FILL_RGB[1]
            buf[i + 2] = FILL_RGB[2]
            buf[i + 3] = a
    return Image.frombytes("RGBA", (w, h), bytes(buf))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.abspath(args.out or os.path.join(here, os.pardir, "media", "shapes"))

    missing = []
    for name, w, h, r in MASKS:
        path = os.path.join(out_dir, name)
        if args.check:
            if not os.path.exists(path):
                missing.append(name)
            continue
        img = build_mask(w, h, r)
        img.save(path)
        a = img.split()[3]
        print("写入 %s  %dx%d r%d  中心alpha=%d 角alpha=%d"
              % (name, w, h, r, a.getpixel((w // 2, h // 2)), a.getpixel((0, 0))))

    if args.check:
        if missing:
            print("缺少 %d 张：%s" % (len(missing), ", ".join(missing)))
            return 1
        print("角部遮盖齐全（%d 张）" % len(MASKS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
