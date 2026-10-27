#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_music_cover.py — 生成音乐播放页的「无专辑图」兜底图（黑胶唱片 + 唱臂）。

为什么要重画
------------
原来那张 `media/osd/nara/music-cover.png` 是一整块不透明的产品照（768×768 全 alpha=255）。
想把它抠成"只有圆盘+唱臂、背景透明"做不到：
  · 背景和唱臂的暗部是同一个色阶，阈值抠不干净；
  · 唱头压在盘面上，圆形裁切会留一块缺口；
  · 标签盘里有波形花纹，不是旋转对称的，按半径取均值补会留下扇形痕。
所以改成程序绘制：真透明、颜色可换、边缘干净。

设计
----
- 盘体：近黑 #0D0D10 + 60 圈细纹 + 外缘高光
- 发光环：accent 色，三层描边再高斯模糊
- 标签盘：深色 + accent 细边 + 中心轴孔
- 唱臂：配重盘 + 臂管（三层叠出金属感）+ 唱头 + 针尖（accent）

用法
----
  python tools/gen_music_cover.py                 # 用默认冷白
  python tools/gen_music_cover.py --accent 4FC3E8 # 换色（RRGGBB）
"""

import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SIZE = 768
CX, CY, R = 300, 400, 300          # 盘心与半径
LABEL_R = 132

# 冷白偏青：和皮肤的白色焦点环同一色系，放在深色玻璃上不抢眼
DEFAULT_ACCENT = "D8ECF4"


def hex2rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def build(accent, font_path, title="Music", sub="THERE IS A STORY IN EVERY SOUND"):
    acc = hex2rgb(accent)
    im = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    # ── 盘体 ──
    d.ellipse([CX - R, CY - R, CX + R, CY + R], fill=(13, 13, 16, 255))
    for r in range(LABEL_R - 36, R - 4, 7):
        a = int(10 + 8 * (1 - abs(r - 200) / 200))
        d.ellipse([CX - r, CY - r, CX + r, CY + r], outline=(255, 255, 255, max(4, a)))
    d.ellipse([CX - R, CY - R, CX + R, CY + R], outline=(255, 255, 255, 70), width=2)

    # ── 发光环 ──
    glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for r, w, a in ((150, 26, 90), (160, 14, 150), (168, 6, 210)):
        gd.ellipse([CX - r, CY - r, CX + r, CY + r], outline=acc + (a,), width=w)
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(16)))

    # ── 标签盘 ──
    d.ellipse([CX - LABEL_R, CY - LABEL_R, CX + LABEL_R, CY + LABEL_R], fill=(20, 20, 25, 255))
    d.ellipse([CX - LABEL_R, CY - LABEL_R, CX + LABEL_R, CY + LABEL_R],
              outline=acc + (200,), width=3)
    d.ellipse([CX - 7, CY - 7, CX + 7, CY + 7], fill=(40, 40, 48, 255))

    # ── 文字 ──
    if font_path and os.path.exists(font_path):
        f1 = ImageFont.truetype(font_path, 64)
        w = d.textlength(title, font=f1)
        d.text((CX - w / 2, CY - 58), title, font=f1, fill=(240, 240, 244, 255))
        # 副标题自动缩到标签圆内（留 40px 边距），避免超出圆外
        maxw = (LABEL_R - 20) * 2
        size = 15
        while size > 9:
            f2 = ImageFont.truetype(font_path, size)
            if d.textlength(sub, font=f2) <= maxw:
                break
            size -= 1
        w2 = d.textlength(sub, font=f2)
        d.text((CX - w2 / 2, CY + 22), sub, font=f2, fill=acc + (210,))

    # ── 唱臂 ──
    px, py = 700, 96
    d.ellipse([px - 46, py - 46, px + 46, py + 46], fill=(24, 24, 30, 255))
    d.ellipse([px - 46, py - 46, px + 46, py + 46], outline=(255, 255, 255, 45), width=2)
    d.ellipse([px - 14, py - 14, px + 14, py + 14], fill=(70, 70, 80, 255))

    x1, y1 = 676, 124
    x2, y2 = 556, 436
    d.line([x1, y1, x2, y2], fill=(28, 28, 34, 255), width=20)
    d.line([x1, y1, x2, y2], fill=(150, 152, 160, 255), width=10)
    d.line([x1, y1, x2, y2], fill=(210, 212, 218, 255), width=3)

    d.polygon([(x2 - 26, y2 + 6), (x2 + 26, y2 - 10), (x2 + 34, y2 + 46), (x2 - 18, y2 + 62)],
              fill=(26, 26, 32, 255))
    d.line([(x2 + 34, y2 + 46), (x2 - 18, y2 + 62)], fill=acc + (200,), width=3)
    d.line([(x2 + 8, y2 + 56), (x2 + 22, y2 + 104)], fill=(190, 192, 200, 255), width=5)
    d.ellipse([x2 + 18, y2 + 100, x2 + 28, y2 + 110], fill=acc + (255,))
    return im


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--accent", default=DEFAULT_ACCENT, help="发光环颜色 RRGGBB")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    skin = os.path.abspath(os.path.join(here, os.pardir))
    out = args.out or os.path.join(skin, "media", "osd", "nara", "music-cover.png")
    font = os.path.join(skin, "fonts", "Inter-Unicode-Regular.ttf")

    img = build(args.accent, font)
    img.save(out)
    a = img.split()[3]
    print("写入 %s  %dx%d  accent=#%s" % (out, img.width, img.height, args.accent))
    print("四角 alpha = %s（0 = 透明）" % [a.getpixel(p) for p in
                                       ((0, 0), (SIZE - 1, 0), (0, SIZE - 1), (SIZE - 1, SIZE - 1))])
    return 0


if __name__ == "__main__":
    sys.exit(main())
