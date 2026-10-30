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

**环和卡片的位置关系（2026-10-28 定论）**

| | 尺寸 | 半径 | 效果 |
|---|---|---|---|
| 配 **diffuse 遮罩**的海报 | 卡片 **+2**（外扩 1px） | 遮罩半径 **+1** | 内缘压进海报 2px，盖住遮罩羽化边，环贴在海报上 |
| 方角卡片（无遮罩） | 卡片 +6（外扩 3px） | 卡片圆角 +3 | 环在卡片外面一圈 |

外扩 3px 配圆角海报会读成"浮在卡片外的一圈框"（用户原话：比海报大了一点点）；
而且环内缘正好落在海报边界上时，遮罩的 3px 羽化会露出一条暗缝。
**圆角海报一律用 +2 / +1。**

用法
----
  python tools/gen_rings.py           # 生成表里所有尺寸
  python tools/gen_rings.py --check   # 只检查是否齐全
"""

import argparse
import os
import sys

from PIL import Image, ImageDraw

SS = 4          # 超采样倍数
STROKE = 3.0    # 描边宽度（像素）

# (文件名, 宽, 高, 圆角半径)
RINGS = (
    # 首页横版卡（320×180，遮罩 r9）→ 环 322×182、半径 10，内缘压进海报 2px
    ("ring_card_322x182_r10.png", 322, 182, 10),
    # 剧集缩略图焦点环：缩略图 336×189（遮罩 r9）→ 环 338×191、半径 10（外扩 1px）
    ("ring_card_338x191_r10.png", 338, 191, 10),
    # OSD 播放列表卡片焦点环：缩略图 356×200（遮罩 r12）→ 环 358×202、半径 13
    ("ring_card_358x202_r13.png", 358, 202, 13),
    # 片单弹窗（Custom_1111）的焦点框：控件 237.6x345.6，原来用 ring12_3.png(14x14)
    # 配 border="12" —— border 比贴图一半还大，9-slice 直接退化
    ("ring_card_238x346_r12.png", 238, 346, 12),
    # 首页专辑卡 186：遮罩 r9 → 环 188×188、半径 10（外扩 1px、内缘压进 2px）
    ("ring_card_188x188_r10.png", 188, 188, 10),
    # 海报墙焦点环：海报 244×352（diffuse 遮罩 r12）。
    # 外扩 1px、描边 3px → 内缘压进海报 2px；环外半径 = 遮罩半径 + 1 = 13。
    # 2026-10-30：海报缩到 236×340，环同步为 238×342（仍是卡片 +2、半径 13）。
    ("ring_card_238x342_r13.png", 238, 342, 13),
    # 搜索结果卡：海报 214×321（遮罩 r12）→ 环 216×323、半径 13
    ("ring_card_216x323_r13.png", 216, 323, 13),
    # 书签弹窗缩略图：海报 330×250（遮罩 r12）→ 环 332×252、半径 13
    # （原来是 colors/white.png border="3" 的方形框，2026-10-28 换成圆角环）
    ("ring_card_332x252_r13.png", 332, 252, 13),
)

# 发丝细边（1px）：不是焦点环，是"贴边那圈很淡的线"（海报墙用）。
# 圆角必须和角部遮盖一致，否则方角会从圆角外面戳出来。
EDGES = (
    ("edge_440x660_r12.png", 440, 660, 12),
)


def build_ring(w: int, h: int, radius: int, stroke: float = STROKE) -> Image.Image:
    W, H = w * SS, h * SS
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    sw = max(1, int(round(stroke * SS)))
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
    for table, stroke in ((RINGS, STROKE), (EDGES, 1.0)):
        for name, w, h, r in table:
            path = os.path.join(out_dir, name)
            if args.check:
                if not os.path.exists(path):
                    missing.append(name)
                continue
            img = build_ring(w, h, r, stroke)
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
        print("描边环齐全（%d 张环 + %d 张细边）" % (len(RINGS), len(EDGES)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
