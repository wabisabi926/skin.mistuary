#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_osd_filled_icons.py — 生成 OSD「实心」播放控制图标。

为什么不用现有的 play.png / pause.png
--------------------------------------
现有那套是**空心描边**：三角只有 2px 轮廓，43px 下实际着色面积不到实心的 1/5，
放在按钮里显得空、显得"瘦"。主控三键（上一首/播放/下一首）需要更重的视觉重量，
但整套皮肤是玻璃 + 细线的语言，把按钮放大到 80px 又会变笨重。
所以改成：**尺寸基本不动，靠实心填充把重量提上来。**

只给主控用，功能键（随机/循环/列表/设置/歌词）继续用线性图标 ——
层级靠「实心 vs 线性」区分，不靠大小。

输出
----
    media/osd/nara/play_filled.png
    media/osd/nara/pause_filled.png
    media/osd/nara/previous_filled.png
    media/osd/nara/next_filled.png

全部 192×192 白图 + 真透明背景，Kodi 里缩到 48 用（4 倍超采样后缩放，边缘干净）。

用法
----
    python tools/gen_osd_filled_icons.py
    python tools/gen_osd_filled_icons.py --check    # 只检查文件在不在
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "media" / "osd" / "nara"

SIZE = 192          # 输出尺寸（Kodi 里缩到 48，4 倍余量）
SS = 4              # 绘制时的超采样倍数
WHITE = (255, 255, 255, 255)

NAMES = ("play", "pause", "previous", "next")


def _canvas() -> tuple[Image.Image, ImageDraw.ImageDraw, int]:
    u = SIZE * SS
    im = Image.new("RGBA", (u, u), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im), u


def _tri(d: ImageDraw.ImageDraw, box: tuple[int, int, int, int], right: bool) -> None:
    x0, y0, x1, y1 = box
    if right:
        d.polygon([(x0, y0), (x1, (y0 + y1) // 2), (x0, y1)], fill=WHITE)
    else:
        d.polygon([(x1, y0), (x0, (y0 + y1) // 2), (x1, y1)], fill=WHITE)


def build(name: str) -> Image.Image:
    im, d, u = _canvas()
    m = int(u * 0.10)          # 外边距
    bar = int(u * 0.10)        # 竖条宽

    if name == "play":
        # 等边比例（宽 = 高 × 0.866），包围盒略偏右 2% 做视觉居中。
        # 之前是 0.52u 宽 × 0.80u 高，偏窄偏高，看起来"被压过"。
        h = int(u * 0.74)
        w = int(h * 0.866)
        x0 = int((u - w) / 2 + u * 0.02)
        y0 = (u - h) // 2
        _tri(d, (x0, y0, x0 + w, y0 + h), True)

    elif name == "pause":
        w, gap = int(u * 0.20), int(u * 0.14)
        for cx in (int(u * 0.5) - gap - w, int(u * 0.5) + gap):
            d.rounded_rectangle([cx, int(u * 0.16), cx + w, int(u * 0.84)],
                                radius=w // 3, fill=WHITE)

    elif name == "previous":
        d.rounded_rectangle([m, int(u * 0.16), m + bar, int(u * 0.84)],
                            radius=bar // 2, fill=WHITE)
        _tri(d, (m + bar + int(u * 0.04), int(u * 0.20), int(u * 0.60), int(u * 0.80)), False)
        _tri(d, (int(u * 0.40), int(u * 0.20), int(u * 0.90), int(u * 0.80)), False)

    elif name == "next":
        _tri(d, (int(u * 0.10), int(u * 0.20), int(u * 0.60), int(u * 0.80)), True)
        _tri(d, (int(u * 0.40), int(u * 0.20), int(u * 0.90), int(u * 0.80)), True)
        d.rounded_rectangle([u - m - bar, int(u * 0.16), u - m, int(u * 0.84)],
                            radius=bar // 2, fill=WHITE)

    else:
        raise SystemExit(f"未知图标：{name}")

    return im.resize((SIZE, SIZE), Image.LANCZOS)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只检查文件是否存在")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    missing = []
    for name in NAMES:
        dst = OUT_DIR / f"{name}_filled.png"
        if args.check:
            if not dst.exists():
                missing.append(dst.name)
            continue
        build(name).save(dst)
        print(f"写入 {dst.name}  {SIZE}×{SIZE}  纯白 + 真透明")

    if args.check:
        if missing:
            print("缺失：" + "、".join(missing))
            return 1
        print(f"实心图标齐全（{len(NAMES)} 张）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
