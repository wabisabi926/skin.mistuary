#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_rings.py — 生成 1:1 的卡片描边环贴图。

为什么不用 9-slice
------------------
空心描边环的描边正好落在贴图**最外圈**，也就是九宫格的"角"里。
边条一拉伸，四边粗细就对不上（实测 2.5px vs 3.75px），
严重时某条边直接消失（剧集缩略图的上边就是这么丢的）。
**正确做法：按控件实际尺寸生成整张描边图，不要 border 属性，1:1 绘制。**

规格（与既有 ring_card_* 保持一致）
-----------------------------------
- 描边 3px，贴着控件最外圈画
- alpha 剖面 ≈ [254, 255, 238, 17]（0.5px 外扩 + 1px 抗锯齿）
- 用 4× 超采样画直角/圆角矩形描边再降采样

用法
----
  python extras/gen_rings.py           # 生成表里所有尺寸
  python extras/gen_rings.py --check   # 只检查是否齐全
"""

import argparse
import os
import sys

from PIL import Image, ImageDraw

SS = 4          # 超采样倍数
STROKE = 3.0    # 描边宽度（像素）

# (文件名, 宽, 高, 圆角半径)
RINGS = (
    # 剧集缩略图焦点环：缩略图 336x189，环外扩 3px（与首页 widget 的 3px 一致）
    ("ring_card_342x195_r6.png", 342, 195, 6),
    # OSD 播放列表卡片焦点环：缩略图 356x200，同样外扩 3px
    ("ring_card_362x206_r6.png", 362, 206, 6),
    # 首页「专辑/歌手」方块卡片（80% 紧凑版）：卡片 253x309，外扩 11px
    ("ring_card_275x331_r11.png", 275, 331, 11),
    # 同上但外扩 3px —— 和海报 / 横版 widget 统一，环贴着卡片而不是套一个框
    ("ring_card_259x315_r6.png", 259, 315, 6),
    # 方块卡片 70% 版：卡片 221x270，外扩 3px
    ("ring_card_227x276_r6.png", 227, 276, 6),
    # 方块卡片 75% 版：**只贴封面图**（237x237 + 3px），和电影/电视剧 widget 一样
    ("ring_card_243x243_r6.png", 243, 243, 6),
    # 方块卡片 72.5% 版：封面 229x229 + 3px
    ("ring_card_235x235_r6.png", 235, 235, 6),
    # 70% 版，照抄海报墙：环外扩 3px、描边 3px → 内缘 r9 与遮盖半径对齐
    ("ring_card_227x227_r12.png", 227, 227, 12),
    # 片单弹窗（Custom_1111）的焦点框：控件 237.6x345.6，原来用 ring12_3.png(14x14)
    # 配 border="12" —— border 比贴图一半还大，9-slice 直接退化
    ("ring_card_238x346_r12.png", 238, 346, 12),
    # 首页专辑卡 200 版：封面 200 + 外扩 3px
    ("ring_card_206x206_r12.png", 206, 206, 12),
    # 首页专辑卡 186 版：封面 186 + 外扩 3px
    ("ring_card_192x192_r12.png", 192, 192, 12),
)


def build_ring(w: int, h: int, radius: int) -> Image.Image:
    W, H = w * SS, h * SS
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    sw = max(1, int(round(STROKE * SS)))
    box = [0, 0, W - 1, H - 1]
    if radius <= 0:
        d.rectangle(box, outline=255, width=sw)
    else:
        d.rounded_rectangle(box, radius=radius * SS, outline=255, width=sw)
    mask = mask.resize((w, h), Image.LANCZOS)
    out = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    out.putalpha(mask)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.abspath(args.out or os.path.join(here, os.pardir, "media", "shapes"))

    missing = []
    for name, w, h, r in RINGS:
        path = os.path.join(out_dir, name)
        if args.check:
            if not os.path.exists(path):
                missing.append(name)
            continue
        img = build_ring(w, h, r)
        img.save(path)
        a = img.split()[3]
        print("写入 %s  %dx%d r%d  左边缘=%s  中心=%d"
              % (name, w, h, r,
                 [a.getpixel((x, h // 2)) for x in range(0, 5)],
                 a.getpixel((w // 2, h // 2))))

    if args.check:
        if missing:
            print("缺少 %d 张：%s" % (len(missing), ", ".join(missing)))
            return 1
        print("描边环齐全（%d 张）" % len(RINGS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
