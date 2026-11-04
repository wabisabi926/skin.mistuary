#!/usr/bin/env python3
"""生成文件管理器续播圆环（101 帧，1% 一档）。

Kodi 没有原生圆形进度控件，所以用预渲染贴图：
`media/progress/resume_ring/ring_000.png` … `ring_100.png`（101 帧）。
helper 把 `Mistuary.FileResume.PercentKey` 写成 `000/001/…/100`，
皮肤用 `ring_$INFO[Window(home).Property(...)].png` 动态取帧。

用法：
    python tools/gen_resume_ring.py
    python tools/gen_resume_ring.py --check
"""

from __future__ import annotations

import argparse
import io
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "media" / "progress" / "resume_ring"
FONT_PATH = ROOT / "fonts" / "Inter-Unicode-Regular.ttf"

SIZE = 40
SCALE = 4
RING_WIDTH = 3
TRACK_ALPHA = 153
GREEN = (0x89, 0xC1, 0x9F, 255)
DIGIT_COLOR = (255, 255, 255, 255)


def render(percent: int) -> Image.Image:
    px = SIZE * SCALE
    image = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    center = px / 2

    # 白轨 = 全长
    ring_r = (SIZE / 2 - 2.5) * SCALE
    ring_w = RING_WIDTH * SCALE
    box = [center - ring_r, center - ring_r, center + ring_r, center + ring_r]
    draw.arc(box, 0, 360, fill=(255, 255, 255, TRACK_ALPHA), width=ring_w)

    # 绿弧 = 已播；从 12 点方向顺时针
    if percent > 0:
        end = -90 + 360 * percent / 100.0
        draw.arc(box, -90, end, fill=GREEN, width=ring_w)
        for angle in (-90, end):
            x = center + ring_r * math.cos(math.radians(angle))
            y = center + ring_r * math.sin(math.radians(angle))
            cap = ring_w / 2
            draw.ellipse([x - cap, y - cap, x + cap, y + cap], fill=GREEN)

    # 数字烘焙进帧，和弧长永远同一个百分位
    font = ImageFont.truetype(str(FONT_PATH), 14 * SCALE)
    draw.text((center, center), str(percent), font=font,
              fill=DIGIT_COLOR, anchor="mm")

    return image.resize((SIZE, SIZE), Image.LANCZOS)


def png_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, "PNG", optimize=True)
    return buffer.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    failures = []
    for percent in range(0, 101):
        path = OUT_DIR / ("ring_%03d.png" % percent)
        data = png_bytes(render(percent))
        if args.check:
            if not path.exists() or path.read_bytes() != data:
                failures.append(path.name)
            continue
        path.write_bytes(data)

    if args.check:
        if failures:
            print("FAIL: ring frames differ: %s" % ", ".join(failures))
            return 1
        print("OK: 101 ring frames match the generator")
        return 0

    print("OK: generated 101 frames in %s" % OUT_DIR.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
