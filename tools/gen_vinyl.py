#!/usr/bin/env python3
"""黑胶唱片素材生成器（音乐播放页的「黑胶模式」）。

产出三张随包贴图：
  media/osd/nara/vinyl-disc.png      1024²  盘面（同心纹 + 标签环 + 边缘高光），中央透明
  media/osd/nara/vinyl-tonearm.png   460×660 唱臂（支点在 ARM_PIVOT）
  media/osd/nara/vinyl-label.png     512²   没专辑图时贴在中圈的兜底标签

另加 `--preview`：把播放页按真实坐标渲染成 1920×1080 效果图，放 docs/scratch/。

用法：
    python tools/gen_vinyl.py            # 生成素材
    python tools/gen_vinyl.py --check    # 校验素材在不在
    python tools/gen_vinyl.py --preview  # 生成素材 + 效果图
"""
from __future__ import annotations

import argparse
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "media", "osd", "nara")
SCRATCH = os.path.join(ROOT, "docs", "scratch")
FONT_PATH = os.path.join(ROOT, "fonts", "Inter-Unicode-Regular.ttf")

# ── 素材规格 ────────────────────────────────────────────────────────────
DISC_SIZE = 1024
DISC_R = 504                     # 留 8px 透明边，旋转时不被控件边界切到
BASE = (13, 13, 16)              # 盘面底色；纹路由它掺白得到
SS = 3                           # 超采样：Pillow 画细圆会走样，画大再缩才圆
COVER_RATIO = 170 / 260          # 播放页里：封面半径 170 / 盘面半径 260
LABEL_R = int(DISC_R * COVER_RATIO)   # 封面盖住的那圈，纹路从它外面开始

ARM_W, ARM_H = 460, 660
ARM_PIVOT = (400, 60)            # 支点在画布内的坐标（XML 的 center 要对齐这里）
ARM_TIP = (297, 374)             # 唱头位置，由几何算出（见 build_tonearm 注释）

LABEL_SIZE = 512

ACCENT = (216, 236, 244)         # 和皮肤白色焦点环同色系

# ── 播放页真实坐标（改 XML 时以此为准）────────────────────────────────
PAGE_W, PAGE_H = 1920, 1080
COVER = (220, 190, 450)          # 方形模式：left, top, size
VINYL_DISC = 520                 # 黑胶模式盘面直径
VINYL_COVER = 340                # 黑胶模式圆封面直径
VINYL_CY = 405                   # 黑胶模式竖直中心（盘面底边 665，标题 674，不冲突）
CX = COVER[0] + COVER[2] // 2    # 两种模式共用同一水平中心 = 445
DISC_LEFT = CX - VINYL_DISC // 2
DISC_TOP = VINYL_CY - VINYL_DISC // 2
VCOVER_LEFT = CX - VINYL_COVER // 2
VCOVER_TOP = VINYL_CY - VINYL_COVER // 2
ARM_LEFT = 760 - ARM_PIVOT[0]    # 支点落在页面的 (760, 130)
ARM_TOP = 130 - ARM_PIVOT[1]


def build_disc() -> Image.Image:
    """盘面：黑胶本体 + 稀疏同心纹 + 标签环 + 边缘高光。中央透明，由封面盖住。

    3 倍超采样再缩回 —— 直接在小画布上画 1px 椭圆会得到锯齿乱线，不是圆。
    纹路要**稀疏且淡**：密而亮的线在 520 显示尺寸下就是噪点（第一版踩过）。
    """
    S = DISC_SIZE * SS
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = S / 2
    R = DISC_R * SS
    lab = LABEL_R * SS

    def ring(r: float, **kw):
        d.ellipse([c - r, c - r, c + r, c + r], **kw)

    ring(R, fill=BASE + (255,))

    # ⚠️ Pillow 在 RGBA 上画 outline 是**覆盖像素**、不是混合：
    # 用 (255,255,255,小alpha) 画出来的不是"很淡的白线"，而是**半透明的洞**，
    # 会透出页面背景 —— 所以无论怎么压 alpha，线永远比盘面亮（这就是前几版
    # "白圈怎么调都还是很白"的真正原因）。
    # 正确做法：把颜色和盘面底色按比例混合成**实色**，alpha 恒为 255。
    def mix(k: float) -> tuple:
        """盘面底色里掺 k 的白，返回不透明色。"""
        return tuple(int(BASE[i] + (255 - BASE[i]) * k) for i in range(3)) + (255,)

    # 纹路：稀疏（26px 间距 ≈ 6 圈）+ 极淡（掺白 1.5%~4%）
    step = 26 * SS
    r = lab + 16 * SS
    while r < R - 6 * SS:
        u = (r - lab) / (R - lab)
        k = 0.015 + 0.025 * (1 - abs(u - 0.5) * 2)
        ring(r, outline=mix(k), width=SS)
        r += step

    # 封面边缘 / 盘面外缘：只留一点暗示（掺白 6% / 4%）
    ring(lab + 4 * SS, outline=mix(0.06), width=SS)
    ring(R - 2 * SS, outline=mix(0.04), width=SS)

    return im.resize((DISC_SIZE, DISC_SIZE), Image.LANCZOS)


def _bezier(p0, c1, c2, p1, n=72):
    """三次贝塞尔采样成折线。Pillow 没有画曲线的接口，采样后用 joint="curve" 连。"""
    pts = []
    for i in range(n + 1):
        u = i / n
        v = 1 - u
        pts.append((v**3 * p0[0] + 3 * v**2 * u * c1[0] + 3 * v * u**2 * c2[0] + u**3 * p1[0],
                    v**3 * p0[1] + 3 * v**2 * u * c1[1] + 3 * v * u**2 * c2[1] + u**3 * p1[1]))
    return pts


def build_tonearm() -> Image.Image:
    """唱臂：配重盘 + **弯曲的**臂管 + 唱头。

    真实唱臂不是一条直线：管身是 S 形，末端唱头再按切线偏一个角度。
    这里用三次贝塞尔画管身（两个控制点在弦的两侧 → 出 S），
    唱头按 t=1 处的切线方向旋转绘制。

    几何：支点距盘心 418、臂长 330，唱针落在半径 215 的纹路区（盘面 260 / 封面 170 之间），
    由两圆求交定唱头位置 —— 不能"支点直指盘心"，那样看着像戳在盘上。
    """
    S = 2
    im = Image.new("RGBA", (ARM_W * S, ARM_H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    px, py = ARM_PIVOT[0] * S, ARM_PIVOT[1] * S
    tx, ty = ARM_TIP[0] * S, ARM_TIP[1] * S

    # 配重盘（在支点后方，照片里是个圆柱配重）
    d.ellipse([px - 42 * S, py - 42 * S, px + 42 * S, py + 42 * S], fill=(22, 22, 28, 255))
    d.ellipse([px - 42 * S, py - 42 * S, px + 42 * S, py + 42 * S],
              outline=(255, 255, 255, 55), width=2 * S)
    d.ellipse([px - 13 * S, py - 13 * S, px + 13 * S, py + 13 * S], fill=(74, 74, 84, 255))
    d.ellipse([px - 5 * S, py - 5 * S, px + 5 * S, py + 5 * S], fill=(150, 152, 160, 255))

    # 管身：S 形。两个控制点落在弦的两侧，出来就是弯的
    dx, dy = tx - px, ty - py
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux                      # 弦的法线
    c1 = (px + dx * 0.34 + nx * 30 * S, py + dy * 0.34 + ny * 30 * S)
    c2 = (px + dx * 0.72 - nx * 18 * S, py + dy * 0.72 - ny * 18 * S)
    tube = _bezier((px, py), c1, c2, (tx, ty))

    d.line(tube, fill=(26, 26, 32, 255), width=13 * S, joint="curve")
    d.line(tube, fill=(148, 150, 158, 255), width=6 * S, joint="curve")
    d.line(tube, fill=(214, 216, 222, 255), width=2 * S, joint="curve")

    # 唱头：按末端切线方向旋转，像真机那样斜着贴住纹路
    ang = math.atan2(ty - c2[1], tx - c2[0])
    ca, sa = math.cos(ang), math.sin(ang)

    def rot(ox, oy):
        return (tx + ox * ca - oy * sa, ty + ox * sa + oy * ca)

    # 唱头：薄一点、带顶面高光，别做成黑方块
    head = [rot(-13 * S, -26 * S), rot(13 * S, -26 * S), rot(16 * S, 20 * S), rot(-11 * S, 20 * S)]
    d.polygon(head, fill=(30, 30, 36, 255))
    d.polygon([rot(-11 * S, -26 * S), rot(11 * S, -26 * S), rot(12 * S, -10 * S), rot(-10 * S, -10 * S)],
              fill=(92, 94, 102, 255))
    d.line([rot(-13 * S, -26 * S), rot(13 * S, -26 * S)], fill=ACCENT + (190,), width=2 * S)
    # 不画唱针：细针在实机上像画错的线，用户要求去掉。

    return im.resize((ARM_W, ARM_H), Image.LANCZOS)


def build_label() -> Image.Image:
    """没专辑图时贴在中圈的兜底标签。

    不能兜到 `music-cover.png` —— 那张图本身就是「盘面 + 唱臂」，
    圆形裁切后会变成碟中碟。
    """
    S = LABEL_SIZE * 2
    im = Image.new("RGBA", (S, S), (0, 0, 0, 255))
    d = ImageDraw.Draw(im)
    for y in range(S):                              # 斜向深蓝渐变
        t = y / S
        d.line([(0, y), (S, y)], fill=(int(26 + 26 * t), int(30 + 26 * t), int(46 + 40 * t), 255))

    c = S / 2
    d.ellipse([c - 250, c - 250, c + 250, c + 250], outline=(255, 255, 255, 26), width=2)
    d.ellipse([c - 220, c - 220, c + 220, c + 220], outline=ACCENT + (60,), width=2)

    # 音符：符头 + 符干 + 符尾，纯几何画，不依赖字体有没有 U+266A
    nx, ny = c - 30, c + 70
    d.ellipse([nx - 46, ny - 34, nx + 46, ny + 34], fill=(232, 240, 246, 235))
    d.rectangle([nx + 32, ny - 200, nx + 46, ny], fill=(232, 240, 246, 235))
    d.polygon([(nx + 46, ny - 200), (nx + 146, ny - 162), (nx + 146, ny - 112),
               (nx + 46, ny - 150)], fill=(232, 240, 246, 235))
    return im.resize((LABEL_SIZE, LABEL_SIZE), Image.LANCZOS)


def _album_placeholder(size: int) -> Image.Image:
    """预览用的占位封面：斜向渐变 + 文案，用来判断圆形裁切和对比度。"""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 255))
    d = ImageDraw.Draw(im)
    for y in range(size):
        t = y / max(1, size - 1)
        d.line([(0, y), (size, y)],
               fill=(int(38 + 60 * t), int(44 + 40 * t), int(70 + 70 * t), 255))
    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse(
        [-size * 0.25, -size * 0.35, size * 0.85, size * 0.55],
        fill=(255, 255, 255, 26))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(size * 0.08)))
    if os.path.exists(FONT_PATH):
        f = ImageFont.truetype(FONT_PATH, int(size * 0.075))
        d.text((size * 0.5, size * 0.46), "ALBUM", font=f, fill=(255, 255, 255, 235), anchor="mm")
        f2 = ImageFont.truetype(FONT_PATH, int(size * 0.045))
        d.text((size * 0.5, size * 0.56), "COVER ART", font=f2, fill=(255, 255, 255, 150), anchor="mm")
    return im


def build_preview(vinyl: bool, disc_size: int = VINYL_DISC, cover_size: int = VINYL_COVER,
                  center_y: int = VINYL_CY, no_cover: bool = False) -> Image.Image:
    """按播放页真实坐标渲染 1920×1080 效果图。no_cover=True 时用兜底标签。"""
    im = Image.new("RGBA", (PAGE_W, PAGE_H), (0, 0, 0, 255))
    d = ImageDraw.Draw(im)
    for y in range(PAGE_H):
        t = y / PAGE_H
        d.line([(0, y), (PAGE_W, y)], fill=(int(16 + 10 * t), int(16 + 10 * t), int(20 + 12 * t), 255))

    art = build_label().resize((cover_size, cover_size), Image.LANCZOS) if no_cover \
        else _album_placeholder(cover_size)
    disc = build_disc()
    arm = build_tonearm()
    cover_left = CX - cover_size // 2
    cover_top = center_y - cover_size // 2

    if vinyl:
        im.alpha_composite(disc.resize((disc_size, disc_size), Image.LANCZOS),
                           (CX - disc_size // 2, center_y - disc_size // 2))
        mask = Image.new("L", (cover_size, cover_size), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, cover_size - 1, cover_size - 1], fill=255)
        im.paste(art, (cover_left, cover_top), mask)
        # 支点固定落在页面 (760,130)，与 ARM_LEFT/ARM_TOP 一致
        im.alpha_composite(arm, (ARM_LEFT, ARM_TOP))
        text_top = 744 if center_y + disc_size // 2 > 660 else 674
    else:
        mask = Image.new("L", (cover_size, cover_size), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, cover_size - 1, cover_size - 1], 12, fill=255)
        im.paste(art, (cover_left, cover_top), mask)
        text_top = 674

    if os.path.exists(FONT_PATH):
        f1 = ImageFont.truetype(FONT_PATH, 44)
        f2 = ImageFont.truetype(FONT_PATH, 30)
        f3 = ImageFont.truetype(FONT_PATH, 24)
        d.text((COVER[0], text_top), "夜曲", font=f1, fill=(240, 240, 244, 255))
        d.text((COVER[0], text_top + 64), "周杰伦", font=f2, fill=(200, 200, 210, 255))
        d.text((COVER[0], text_top + 106), "2005 · 十一月的萧邦", font=f3, fill=(150, 150, 162, 255))
    return im


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()

    targets = [("vinyl-disc.png", build_disc),
               ("vinyl-tonearm.png", build_tonearm),
               ("vinyl-label.png", build_label)]

    if args.check:
        missing = [n for n, _ in targets if not os.path.exists(os.path.join(OUT_DIR, n))]
        if missing:
            print("缺失：%s" % ", ".join(missing))
            return 1
        print("黑胶素材齐全（%d 张）" % len(targets))
        return 0

    os.makedirs(OUT_DIR, exist_ok=True)
    for name, fn in targets:
        img = fn()
        # 盘面是「深色平涂 + 少量淡环」，量化到 256 色体积从 437 KB 掉到 ~71 KB，
        # 观感无损。渐变类的标签图不量化，避免出现色带。
        if name == "vinyl-disc.png":
            img = img.quantize(colors=256, method=Image.FASTOCTREE)
        img.save(os.path.join(OUT_DIR, name))
        print("  %s" % name)

    if args.preview:
        os.makedirs(SCRATCH, exist_ok=True)
        build_preview(True).save(os.path.join(SCRATCH, "vinyl-final.png"))
        build_preview(True, no_cover=True).save(os.path.join(SCRATCH, "vinyl-nocover.png"))
        build_preview(False).save(os.path.join(SCRATCH, "vinyl-square.png"))
        print("  预览：vinyl-final / vinyl-nocover / vinyl-square")
    return 0


if __name__ == "__main__":
    sys.exit(main())
