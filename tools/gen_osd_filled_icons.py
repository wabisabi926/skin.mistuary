#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_osd_filled_icons.py — 由 SVG 源生成 OSD 主控的实心图标。

为什么换成 Material Symbols
---------------------------
之前用 PIL 手画的三角形，比例和视觉重心怎么调都不够专业（用户评价"歪""丑"）。
改成直接渲染 **Material Symbols Rounded（fill）** 的官方路径 —— Apache-2.0，
许可干净（Arctic Fuse 那套是 CC BY-NC-SA，搬进来会把整套皮肤变成非商用）。

源文件在 `tools/osd_icons/`：
    play_arrow.svg         → media/osd/nara/play_filled.png
    pause.svg              → media/osd/nara/pause_filled.png
    skip_previous.svg      → media/osd/nara/previous_filled.png
    skip_previous.svg 镜像 → media/osd/nara/next_filled.png

输出统一 192×192、纯白、真透明（Kodi 里缩到 48 用）。

依赖
----
    pip install resvg-py             # Rust 版 SVG 渲染器，自带二进制，不需要原生 cairo

用法
----
    python tools/gen_osd_filled_icons.py
    python tools/gen_osd_filled_icons.py --check    # 只检查产物在不在
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tools" / "osd_icons"
OUT_DIR = ROOT / "media" / "osd" / "nara"
SIZE = 192

# 输出名 → (源 SVG, 是否水平镜像)
JOBS = {
    "play_filled": ("play_arrow.svg", False),
    "pause_filled": ("pause.svg", False),
    "previous_filled": ("skip_previous.svg", False),
    "next_filled": ("skip_previous.svg", True),
}


def render(svg: Path, mirror: bool) -> Image.Image:
    import resvg_py

    data = resvg_py.svg_to_bytes(svg_path=str(svg), width=SIZE * 4, height=SIZE * 4)
    im = Image.open(io.BytesIO(bytes(data))).convert("RGBA")
    im = im.crop(im.getbbox())                       # 去掉四周留白
    k = SIZE / max(im.size)
    im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    canvas.alpha_composite(im, ((SIZE - im.width) // 2, (SIZE - im.height) // 2))

    if mirror:
        canvas = canvas.transpose(Image.FLIP_LEFT_RIGHT)

    # 统一成纯白：保留 alpha，RGB 全填 255
    white = Image.new("RGBA", canvas.size, (255, 255, 255, 255))
    white.putalpha(canvas.split()[3])
    return white


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只检查产物是否存在")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    missing = []
    for out, (src, mirror) in JOBS.items():
        dst = OUT_DIR / f"{out}.png"
        if args.check:
            if not dst.exists():
                missing.append(dst.name)
            continue
        render(SRC / src, mirror).save(dst)
        print(f"写入 {dst.name}  ← {src}{' (镜像)' if mirror else ''}")

    if args.check:
        if missing:
            print("缺失：" + "、".join(missing))
            return 1
        print(f"实心图标齐全（{len(JOBS)} 张）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
