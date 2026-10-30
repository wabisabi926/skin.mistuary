#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_corner_masks.py — 生成「圆角」贴图：diffuse 遮罩（推荐）+ 老式实色角部遮盖（淘汰中）。

它干什么
--------
给**图片**（海报、缩略图）裁真圆角，唯一正确的做法是 `<texture diffuse="遮罩.png">`：
Kodi 把遮罩**逐像素乘**到图片上（RGB 和 alpha 一起乘），所以「圆角外全 0」的遮罩
会把图片的四角真的抠掉，背景直接透出来。详见 docs/HANDOVER.md §5.4.1。

  DIFFUSE_MASKS → mask_<w>x<h>_r<半径>.png     圆角内 255 / 圆角外 0 / 3px 羽化  ← 用这个
  MASKS         → corner_<w>x<h>_r<半径>.png   圆角外填 #2A2A2E @78%            ← 老方案

老方案（corner_*）为什么不行
----------------------------
遮盖色必须和"背后"一致，而背后是变化的 fanart —— 亮背景上四角会露出深色斑点，
只在纯色/深色背景上勉强成立。**新视图一律加 DIFFUSE_MASKS，不要再新增 corner_*。**
（ALPHA 是它唯一能调的旋钮：255 是硬黑缺口，200 是柔和暗角，<170 会露出海报方角残影。）

几何约束（改之前先读）
----------------------
- 遮罩画布必须和图片控件**完全一致**（一尺寸一张），否则会被拉伸、圆角变形。
- 焦点环 = 卡片 **+2**（外扩 1px），**环半径 = 遮罩半径 + 1**，两个圆弧才同心，
  环内缘压进海报 2px 盖住遮罩羽化。**外扩 3px / 半径 +3 是错的**（环会读成浮在卡片外，
  角上还会露缝），2026-10-28 已全面改掉，只剩方角卡片用 +6 / 圆角 +3。
- 1px 发丝边（`edge_*`，由 tools/gen_rings.py 生成）画在海报原位 →
  **半径 = 遮罩半径**（不是 +3）。
- 海报下面如果垫了圆角底板（`round<N>.png`），**底板半径不能小于遮罩半径**，
  否则四角会从海报下面露出来。

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
# 表里只留**还有 XML 引用**的尺寸（2026-10-28 清掉 3 张无引用：
# corner_244x352_r18 / corner_221x221_r9 / corner_200x200_r9）。
MASKS = ()   # 2026-10-28：所有视图已迁移到 diffuse 遮罩，实色遮盖不再使用

# 遮盖色。**不要再改回接近纯黑**：
#   #0F0F12 压在亮背景上只剩 24 级灰，看起来就是个黑洞；
#   #2A2A2E 同样条件下是 53 级灰，读作"灰影"，而且放在暗背景上几乎看不见。
# alpha 决定缺口有多硬：
#   255 = 硬边（最干净，但亮背景上最显眼）
#   200 = 78%，透出两成背景，缺口变成柔和的暗角（当前取值）
#   < 170 时海报方角的残影会明显显形
FILL_RGB = (0x2A, 0x2A, 0x2E)
ALPHA = 200

# 纯白不透明遮盖（由 colordiffuse 着色）：目前没用到，留着备用。
SOLID_MASKS = ()

# ==== diffuse 遮罩（真圆角）====
# Kodi 的 `<texture diffuse="...">` 是**逐像素相乘，连 alpha 一起乘**，
# 所以给一张"圆角内 alpha=255、圆角外 alpha=0"的白色图，
# 海报的四角就是真的透明 —— 背景透出来，不是盖一块深色。
# Fuse3 就是这么做圆角的（media/diffuse/card_w731_h310.png）。
# **遮罩尺寸必须和控件完全一致**，否则会被拉伸、圆角变形。
DIFFUSE_MASKS = (
    # 海报墙 244×352：r12（= 搜索页 214×321 r11 的同比例；用户对比后更喜欢那个）
    # 2026-10-30 缩到 236×340（等比例 0.9672）给左右缝让出 8px：卡片格 260 是实测上限，
    # 想加宽间距只能缩海报。半径仍 r12。
    ("mask_236x340_r12.png", 236, 340, 12),
    # 封面视图 View_51：卡片 440×660，半径 12
    # （和底板 round12、细边 edge_*_r12 同一个半径，三者才对齐）
    ("mask_440x660_r12.png", 440, 660, 12),
    # 首页：横版 hero / 媒体库封面 320×180（r9）、专辑方块 186×186（r9）
    ("mask_320x180_r9.png", 320, 180, 9),
    ("mask_186x186_r9.png", 186, 186, 9),
    # 次级页面的卡片：音乐信息专辑图 452²、宽列表 340²/438×246、
    # 列表预览 224×300/184²/160²、OSD 播放列表 356×200、插件信息 656×312、演员头像 110×150
    ("mask_452x452_r12.png", 452, 452, 12),
    ("mask_340x340_r12.png", 340, 340, 12),
    ("mask_438x246_r12.png", 438, 246, 12),
    ("mask_224x300_r12.png", 224, 300, 12),
    ("mask_356x200_r12.png", 356, 200, 12),
    ("mask_656x312_r12.png", 656, 312, 12),
    ("mask_184x184_r9.png", 184, 184, 9),
    ("mask_110x150_r9.png", 110, 150, 9),
    # 剧集详情页的剧集缩略图 336×189（短边 <200 → r9）
    ("mask_336x189_r9.png", 336, 189, 9),
    # 首页「类别」卡的背景图 276×160（短边 <200 → r9）
    ("mask_276x160_r9.png", 276, 160, 9),
    # 搜索结果卡 214×321（r12，与海报墙统一）
    ("mask_214x321_r12.png", 214, 321, 12),
    # 详情页 / 横排的大海报 452×672（r12）
    ("mask_452x672_r12.png", 452, 672, 12),
    # Shift 视图 334×480（r12）
    ("mask_334x480_r12.png", 334, 480, 12),
    # 宽列表：主缩略图 438×366（r12）、小缩略图 160×160 / 240×240（r9，短边 <200 档）
    ("mask_438x366_r12.png", 438, 366, 12),
    ("mask_160x160_r9.png", 160, 160, 9),
    ("mask_240x240_r9.png", 240, 240, 9),
    # 2026-10-28 补：音乐播放页封面 450²（正方形专辑图，光晕/光泽角上全透明）
    ("mask_450x450_r12.png", 450, 450, 12),
    # 视频管理器左侧海报 400×630（keep，海报 2:3 = 400×600）
    ("mask_400x630_r12.png", 400, 630, 12),
    # 列表行小缩略图 110×110（媒体信息列表 / 选择对话框）
    ("mask_110x110_r9.png", 110, 110, 9),
    # ==== 2026-10-28 二期：补掉最后 7 处方框 / 方角卡片 ====
    # 播放控制条封面 250²（keep，海报 2:3 实显 166×250，遮罩跟图走）
    ("mask_250x250_r12.png", 250, 250, 12),
    # 书签弹窗缩略图 330×250（scale，遮罩写 scalediffuse="false"）
    ("mask_330x250_r12.png", 330, 250, 12),
    # 文件浏览器右侧预览 260×380（keep aligny=bottom）
    ("mask_260x380_r12.png", 260, 380, 12),
    # 图标墙缩略图 160×116（卡片本体是 round32，图是方角）
    ("mask_160x116_r9.png", 160, 116, 9),
    # 播放中 seek 封面 200²（短边 = 200，归 r12 档）
    ("mask_200x200_r12.png", 200, 200, 12),
    # 用户配置页头像 162²（短边 <200 → r9）
    ("mask_162x162_r9.png", 162, 162, 9),
)


def build_diffuse(w: int, h: int, radius: int, feather: float = 3.0) -> Image.Image:
    """圆角遮罩：圆角内 (255,255,255,255)，圆角外全 0，边缘 feather 像素羽化。

    RGB 和 alpha 一起给 —— 不管 Kodi 的 diffuse 乘的是 RGB 还是 RGBA 都能生效：
    乘 RGBA → 四角真透明；只乘 RGB → 四角是柔和暗角（和 Fuse3 一个观感）。
    """
    cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
    inner_x, inner_y = cx - radius, cy - radius

    buf = bytearray(w * h * 4)
    for y in range(h):
        dy = abs(y - cy) - inner_y
        for x in range(w):
            dx = abs(x - cx) - inner_x
            qx = dx if dx > 0 else 0.0
            qy = dy if dy > 0 else 0.0
            sdf = (qx * qx + qy * qy) ** 0.5 + min(max(dx, dy), 0.0) - radius
            # 0.5 落在边界上，向内/向外各羽化 feather/2
            t = 0.5 - sdf / feather
            if t <= 0.0:
                t = 0.0
            elif t >= 1.0:
                t = 1.0
            v = int(round(255 * t))
            i = (y * w + x) * 4
            buf[i] = v
            buf[i + 1] = v
            buf[i + 2] = v
            buf[i + 3] = v
    return Image.frombytes("RGBA", (w, h), bytes(buf))


def build_mask(w: int, h: int, radius: int, fill=FILL_RGB, alpha=ALPHA) -> Image.Image:
    """实色角部遮盖：圆角矩形内透明、外部填色（"把方角涂掉"的老方案）。"""
    cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
    inner_x, inner_y = cx - radius, cy - radius

    buf = bytearray(w * h * 4)
    for y in range(h):
        dy = abs(y - cy) - inner_y
        for x in range(w):
            dx = abs(x - cx) - inner_x
            qx = dx if dx > 0 else 0.0
            qy = dy if dy > 0 else 0.0
            sdf = (qx * qx + qy * qy) ** 0.5 + min(max(dx, dy), 0.0) - radius
            cov = 1.0 - sdf
            if cov <= 0.0:
                cov = 0.0
            elif cov >= 1.0:
                cov = 1.0
            # 内部透明、外部填色 —— 所以 alpha 用 (1-cov)
            a = int(round(alpha * (1.0 - cov)))
            i = (y * w + x) * 4
            buf[i] = fill[0]
            buf[i + 1] = fill[1]
            buf[i + 2] = fill[2]
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
    tables = ((MASKS, FILL_RGB, ALPHA), (SOLID_MASKS, (255, 255, 255), 255))
    for table, fill, alpha in tables:
        for name, w, h, r in table:
            path = os.path.join(out_dir, name)
            if args.check:
                if not os.path.exists(path):
                    missing.append(name)
                continue
            img = build_mask(w, h, r, fill, alpha)
            img.save(path)
            a = img.split()[3]
            print("写入 %s  %dx%d r%d  中心alpha=%d 角alpha=%d"
                  % (name, w, h, r, a.getpixel((w // 2, h // 2)), a.getpixel((0, 0))))

    for name, w, h, r in DIFFUSE_MASKS:
        path = os.path.join(out_dir, name)
        if args.check:
            if not os.path.exists(path):
                missing.append(name)
            continue
        img = build_diffuse(w, h, r)
        img.save(path)
        a = img.split()[3]
        print("写入 %s  %dx%d r%d  中心alpha=%d 角alpha=%d（diffuse 遮罩）"
              % (name, w, h, r, a.getpixel((w // 2, h // 2)), a.getpixel((0, 0))))

    if args.check:
        if missing:
            print("缺少 %d 张：%s" % (len(missing), ", ".join(missing)))
            return 1
        print("圆角贴图齐全（diffuse %d 张 / 实色遮盖 %d 张 / 纯白遮盖 %d 张）"
              % (len(DIFFUSE_MASKS), len(MASKS), len(SOLID_MASKS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
