# -*- coding: utf-8 -*-
"""把 media/techflags 里的真实图标拼成一张一览图，供 README 展示。

用法: python tools/gen_readme_sheet.py
输出: docs/screenshots/techflags.png（docs/ 不进发布包）
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
TECH = os.path.join(ROOT, "media", "techflags", "color")
FONT = os.path.join(ROOT, "fonts", "Inter-Unicode-Regular.ttf")
OUT_DIR = os.path.join(ROOT, "docs", "screenshots")

BG = (26, 26, 30, 255)
FG = (200, 200, 208, 255)
DIM = (130, 130, 140, 255)
ACCENT = (120, 200, 255, 255)

ROWS = [
    ("分辨率", "resolution", ["8K", "4K", "1080", "720", "576", "480"]),
    ("视频", "video", ["bluray", "h265", "h264", "av1", "xvid", "dvd"]),
    ("HDR", "hdr", ["dolbyvision", "hdr10", "hdr10plus", "hdr_vivid", "hlg"]),
    ("音频", "audio", ["truehd_atmos", "dtshd_ma", "dtshd_hra", "eac3", "ac3", "aac", "flac"]),
]

ICON_H = 46          # 图标统一高度
GAP = 26             # 图标间距
PAD = 56             # 画布内边距
LABEL_W = 108        # 左侧行标签宽
ROW_H = 96           # 行高

W = 1200
H = PAD * 2 + ROW_H * len(ROWS) + 70   # 顶部留标题


def load(name, folder):
    path = os.path.join(TECH, folder, name + ".png")
    if not os.path.exists(path):
        print("  !! 缺图:", path)
        return None
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    nw = max(1, round(w * ICON_H / h))
    return im.resize((nw, ICON_H), Image.LANCZOS)


canvas = Image.new("RGBA", (W, H), BG)
d = ImageDraw.Draw(canvas)

f_title = ImageFont.truetype(FONT, 30)
f_label = ImageFont.truetype(FONT, 22)
f_small = ImageFont.truetype(FONT, 17)

# 标题
d.text((PAD, PAD - 6), "技术标识 · 97 枚图标", font=f_title, fill=FG)
d.text((PAD, PAD + 34), "详情页 / OSD / 列表用同一套，按片源实际规格显示", font=f_small, fill=DIM)

y = PAD + 86
for label, folder, names in ROWS:
    d.text((PAD, y + ICON_H // 2 - 14), label, font=f_label, fill=ACCENT)
    x = PAD + LABEL_W
    for n in names:
        im = load(n, folder)
        if im is None:
            continue
        canvas.alpha_composite(im, (x, y))
        x += im.size[0] + GAP
    y += ROW_H

os.makedirs(OUT_DIR, exist_ok=True)
out = os.path.join(OUT_DIR, "techflags.png")
canvas.convert("RGB").save(out, optimize=True)
print("写入 %s  %dx%d  %.1f KB" % (out, W, H, os.path.getsize(out) / 1024.0))
