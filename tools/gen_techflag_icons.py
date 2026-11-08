#!/usr/bin/env python3
"""生成技术标识图标（techflags）。

做四件事：
1. 从本机其它皮肤拷素材，归一化成统一画布（2:1、等高、居中、去留白）
2. 手绘素材库里没有的图标（av3a / mjpeg）
3. 把"原始值 -> 图标路径"写进 xml/Includes_VideoTechnicalFlags.xml 的生成区
4. 打印覆盖率报告

素材里没有的值不写 map entry —— 运行时 $MAP 返回空，皮肤自动落回文字胶囊。
所以"缺图"不是一个要处理的异常，而是默认行为。

用法：
    python tools/gen_techflag_icons.py            # 生成
    python tools/gen_techflag_icons.py --check    # CI：产物与 map 是否同步
    python tools/gen_techflag_icons.py --report    # 只打印覆盖率，不写文件

素材来源（全部 CC BY-NC-SA 4.0）：
    skin.arctic.fuse.3                     resolution / source / audio / channels
    skin.arctic.fuse.3-avdvplus&p3i        hdr
    skin.arctic.zephyr.martian             channels/12（fuse3 只到 10）
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
XML = ROOT / "xml" / "Includes_VideoTechnicalFlags.xml"
OUTDIR = ROOT / "media" / "techflags" / "color"

FUSE = Path(r"D:/Downloads/ai/skin.arctic.fuse.3/media/flags/color")
AVDV = Path(r"D:/Downloads/ai/skin.arctic.fuse.3-avdvplus&p3i/media/flags/color")
MART = Path(r"D:/Downloads/ai/skin.arctic.zephyr.martian/media/flags/color")
# zephyr 2.core 的单色素材：tv / hdmv 这类在 color 目录里根本没有
ZMONO = Path(r"D:/Downloads/ai/skin.arctic.zephyr.2.core/media/flags/monochrome")

CANVAS_W, CANVAS_H = 96, 56          # 2:1 偏方一点，显示框 48x28 时留白最小
FONT_PATH = ROOT / "fonts" / "Inter-Unicode-Regular.ttf"

BEGIN = "\t<!-- BEGIN generated: techflag icon maps -->"
END = "\t<!-- END generated: techflag icon maps -->"

# 每个类别：输出子目录 + 候选源目录 + 别名（原始值 -> 素材文件名）
CATEGORIES = {
    "NaraTechnicalResolutionIconMap": ("resolution", [FUSE / "resolution"], {}),
    "NaraTechnicalHdrIconMap": ("hdr", [AVDV / "hdr"],
                                {"hdr_vivid": "hdrvivid"}),
    # 来源按分类锁死（2026-11-08）：一个分类只吃一套皮肤，绝不跨套补缺。
    #   resolution / video / audio -> fuse3（覆盖最全：6/7、25/34、43/48）
    #   hdr                        -> avdv（只有它有 hdr 目录）
    #   channels                   -> zephyr（唯一覆盖到 16）
    # 缺的 key 不搬别套的图，由 draw_wordmark 按同类 logo 的排版重画。
    "NaraTechnicalVideoCodecIconMap": ("video", [FUSE / "source", AVDV / "source", MART / "video"],
                                       {"h265": "hevc", "hvc1": "hevc",
                                        "mpeg1": "mpeg1video"}),
    "NaraTechnicalAudioCodecIconMap": ("audio", [FUSE / "audio", AVDV / "audio"],
                                       {"dtsma": "dtshd_ma", "mp3float": "mp3",
                                        "wmav2": "wma", "pcm_bluray": "pcm",
                                        "pcm_s32le": "pcm_s24le", "dca": "dts",
                                        "wavpack": "wv"}),
    # 声道：zephyr 覆盖 0~16（fuse3 只到 10），所以 zephyr 在前、fuse3 补缺。
    # key 是 AudioChannels 的数字，不是布局串 —— 5.1.2 与 7.1 都是 8，本来就分不出来。
    "NaraTechnicalChannelIconMap": ("channels", [MART / "channels", FUSE / "channels"], {}),
}

CATEGORIES_BY_SUBDIR = {sub: (name, dirs, alias)
                        for name, (sub, dirs, alias) in CATEGORIES.items()}

# 不在 TextMap 里的额外徽章：Atmos 是「叠加」在音频编码图标右边的，
# 由 AudioCodec 是否包含 atmos 决定（fuse3 同款做法）。
EXTRA_ICONS = {"audio": ["atmos"]}


def index_dirs(dirs: list[Path]) -> dict[str, Path]:
    """文件名小写索引，同时登记把 - 和空格换成 _ 的变体。"""
    out: dict[str, Path] = {}
    for d in dirs:
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.png")):
            out.setdefault(f.stem.lower(), f)
            out.setdefault(f.stem.lower().replace("-", "_").replace(" ", "_"), f)
    return out


def normalize(src: Path | Image.Image) -> Image.Image:
    """裁掉透明留白，等比缩放到画布内并居中。"""
    im = Image.open(src).convert("RGBA") if isinstance(src, Path) else src
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    k = min(CANVAS_W / im.width, CANVAS_H / im.height)
    im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))),
                   Image.LANCZOS)
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    canvas.alpha_composite(im, ((CANVAS_W - im.width) // 2, (CANVAS_H - im.height) // 2))
    return canvas


# ===== 素材库确实没有的 8 个格式：照同类 logo 的结构手绘 =====
# 参考原型全部来自 fuse3 / avdv，配色从原型采样：
#   8K    <- resolution/4K.png（红 UHD + 2160p 行，直接换数字）
#   vhs   <- source/dvd.png（银灰渐变字 + 下方器物）
#   tv    <- source/hdtv.png（蓝圆 H + 银灰字）
#   hdmv  <- source/bluray.png（蓝弧 BD + 小字）
#   mjpeg <- source/mpeg4.png（蓝斜体 + 小字）
#   prores<- source/quicktime.png（蓝圆 Q + 字）
#   av3a  <- audio/aac.png（橙棕弧 + 字）
#   hdrvivid <- avdv/hdr/hdr10.png（彩色扇形 + 字）
BLUE = (0, 120, 215, 255)
QT_BLUE = (0, 144, 216, 255)
AAC_BROWN = (168, 96, 72, 255)
RED = (252, 10, 10, 255)
GREY = (168, 172, 178, 255)
LGREY = (228, 230, 234, 255)

# zephyr 2.core 的 tv / hdmv 是纯白线稿（彩色像素 0%），放在同排里明显脱节：
# 同排 bluray / h264 / mpeg4 / prores / mjpeg 全是「青蓝图形 + 白字」。
# 蓝值直接从这些真素材采样（高光 #80C0E0 / 暗部 #0070A0），不是另配一种蓝。
FLAG_BLUE_HI = (128, 192, 224)
FLAG_BLUE_DARK = (0, 112, 160)
FLAG_WHITE = (238, 242, 246)


def _blank():
    return Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))


def _trim(im):
    """裁掉透明边，返回只剩有效像素的图。"""
    bbox = im.getbbox()
    return im.crop(bbox) if bbox else im


def _paste_fit(im, src, w, h, xy):
    """把 src 等比缩到 (w,h) 的框内，贴到 xy。"""
    k = min(w / src.width, h / src.height)
    s = src.resize((max(1, round(src.width * k)), max(1, round(src.height * k))), Image.LANCZOS)
    im.alpha_composite(s, xy)
    return s


def _font(size, ss=1):
    return ImageFont.truetype(str(FONT_PATH), int(size * ss))


def _draw_8k():
    """拿 4K.png 的底，只把 2160p 换成 4320p。

    两个坑（2026-11-08 都踩过）：
    1. 必须在 4K 的**原生像素空间**（66x48）里改，改完交给 normalize() 裁边放大。
       自己 thumbnail 一遍只会得到 53x35，比 4K 的 87x56 小一大圈。
    2. 4K 的第二行不是「白字」，是**白色斜条挖空字**（字是透明的，露出背景）。
       所以不能直接画白字，要把挖空的字换掉、白条保留。
    """
    im = Image.open(FUSE / "resolution" / "4K.png").convert("RGBA")
    w, h = im.size
    px = im.load()

    # 1) 只留上半部分（红色 UHD），下半部分重做
    top = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for y in range(26):
        for x in range(w):
            top.putpixel((x, y), px[x, y])

    # 2) 还原白条的实心形状：逐行取最左/最右白像素，填满（字是洞，会被填掉）。
    #    逐行取边界能保留原文的斜体轮廓和圆角，不用自己画平行四边形。
    solid = Image.new("L", (w, h), 0)
    sp = solid.load()
    for y in range(26, h):
        xs = [x for x in range(w) if px[x, y][3] > 40 and px[x, y][0] > 190]
        if xs:
            for x in range(min(xs), max(xs) + 1):
                sp[x, y] = 255

    # 3) 在同样的位置上重新挖出 4320p。
    #    实测 4K 里 "2160p" 的洞是 35x10、中心 (34, 33.5)；arialbi 12 号是 36x11，
    #    最接近这一格的字面，再大就会把白条吃光。
    glyph = Image.new("L", (w, h), 0)
    ImageDraw.Draw(glyph).text((34, 33.0), "4320p", font=_font(12), fill=255, anchor="mm")
    gp = glyph.load()
    bar = Image.new("L", (w, h), 0)
    bp = bar.load()
    for y in range(26, h):
        for x in range(w):
            if sp[x, y] and gp[x, y] < 128:
                bp[x, y] = 255

    white = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    white.putalpha(bar)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.alpha_composite(top)
    out.alpha_composite(white)
    return out


def _draw_vhs():
    im = _blank()
    grad = Image.new("RGBA", (CANVAS_W, CANVAS_H)); gp = grad.load()
    for y in range(CANVAS_H):
        v = int(248 - 104 * (y / (CANVAS_H - 1)))
        for x in range(CANVAS_W):
            gp[x, y] = (v, v, v, 255)
    mask = Image.new("L", (CANVAS_W, CANVAS_H), 0)
    ImageDraw.Draw(mask).text((CANVAS_W / 2, 23), "VHS", font=_font(26), fill=255,
                              anchor="mm", stroke_width=1, stroke_fill=255)
    im.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([20, 36, 76, 54], radius=3, fill=(52, 52, 60, 255),
                        outline=(140, 140, 150, 255), width=1)
    for cx in (36, 60):
        d.ellipse([cx - 9, 39, cx + 9, 51], fill=(232, 232, 238, 255))
        d.ellipse([cx - 4, 42, cx + 4, 48], fill=(52, 52, 60, 255))
    return im


def _recolor_lineart(name: str) -> Image.Image:
    """把 zephyr 单色线稿重配成「蓝图形 + 白字」，与同排 logo 同一套配色。

    线稿本身是白色 alpha 图形，不能整张染一个蓝——那会变成一块死板的
    实色。这里用连通域把主体图形和文字分开：文字要么是主体框里的独立
    小块（tv 的 TV），要么落在下三分之一（hdmv 的 Blu-ray Disc）。
    主体按 y 做亮→深渐变（同排 logo 都有这种金属渐变），文字保持白。
    """
    im = Image.open(ZMONO / "source" / f"{name}.png").convert("RGBA")
    w, h = im.size
    src = im.load()
    seen = [[False] * w for _ in range(h)]
    parts: list[tuple[list[tuple[int, int]], tuple[int, int, int, int]]] = []
    for y in range(h):
        for x in range(w):
            if seen[y][x] or src[x, y][3] < 60:
                continue
            queue = deque([(x, y)])
            seen[y][x] = True
            pts = []
            while queue:
                a, b = queue.popleft()
                pts.append((a, b))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = a + dx, b + dy
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and src[nx, ny][3] >= 60:
                        seen[ny][nx] = True
                        queue.append((nx, ny))
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            parts.append((pts, (min(xs), min(ys), max(xs), max(ys))))
    parts.sort(key=lambda c: len(c[0]), reverse=True)
    main_box = parts[0][1]
    bbox = im.getbbox()
    y0, y1 = bbox[1], bbox[3]
    span = max(1, y1 - y0 - 1)
    text: set[tuple[int, int]] = set()
    for pts, (x0, a0, x1, a1) in parts[1:]:
        lower = a0 > y0 + 0.55 * span
        inner = (x0 > main_box[0] and x1 < main_box[2]
                 and a0 > main_box[1] and a1 < main_box[3]
                 and len(pts) < len(parts[0][0]) * 0.6)
        if lower or inner:
            text.update(pts)

    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dst = out.load()
    for y in range(h):
        t = min(1.0, max(0.0, (y - y0) / span))
        blue = tuple(round(FLAG_BLUE_HI[i] + (FLAG_BLUE_DARK[i] - FLAG_BLUE_HI[i]) * t)
                     for i in range(3))
        for x in range(w):
            dst[x, y] = (*(FLAG_WHITE if (x, y) in text else blue), src[x, y][3])
    return out


def _draw_tv():
    """TV：zephyr 2.core 的电视线稿，重配成蓝框 + 白 TV 字（照 h264）。

    color 目录里没有 tv，fuse3 的 hdtv 是 20x20 的糊图，放大后一团。
    zephyr 这张是干净的矢量级线条，缩到 48x28 仍然锐利。
    """
    return _recolor_lineart("tv")


def _draw_hdmv():
    """HDMV：蓝光电影模式，用蓝光官方图形，配色对齐同排 bluray。

    HDMV 就是蓝光的电影模式，用蓝光标准标是对的；这张线稿比从
    bluray.png 裁 45x19 的位图再放大清楚得多。
    """
    return _recolor_lineart("hdmv")


def _draw_mjpeg():
    """MJPEG：照 mpeg4 的排版——上面彩色粗字，下面白色胶囊。

    胶囊直接用 mpeg4 原图里的那个（里面本来就写着 MPEG4，语义也对），
    只把上面的 DivX 换成 MJPEG。
    """
    im = _blank()
    # 白胶囊实测 y 29..37 / x 11..61，上一版从 y=26 切，只切到胶囊上半截
    oval = _trim(Image.open(FUSE / "source" / "mpeg4.png").convert("RGBA").crop((10, 28, 63, 39)))
    o = _paste_fit(im, oval, 60, 13, (18, 38))
    d = ImageDraw.Draw(im)
    d.text((48, 22), "MJPEG", font=_font(20), fill=(0, 150, 205, 255), anchor="mm",
           stroke_width=1, stroke_fill=(0, 150, 205, 255))
    return im


def _draw_prores():
    """ProRes：沿用 QuickTime 的 Q，下面换成 ProRes。"""
    im = _blank()
    # 蓝 Q 实测 x 25..45 / y 11..31
    q = _trim(Image.open(FUSE / "source" / "quicktime.png").convert("RGBA").crop((24, 10, 46, 32)))
    q = _paste_fit(im, q, 34, 34, (31, 2))
    d = ImageDraw.Draw(im)
    d.text((48, 45), "ProRes", font=_font(15), fill=(226, 226, 229, 255), anchor="mm",
           stroke_width=1, stroke_fill=(226, 226, 229, 255))
    return im


def _vivid_mark():
    """菁彩视听（HDR Vivid / Audio Vivid）共用的官方三角标识。

    从官方 VI 图里抠的：白底按「离白多远」估 alpha 去掉，红 #F8525E /
    蓝 #0040B0 / 青三个色块都是原图像素。两个标识共用同一个 mark，
    这正是官方的做法——图形相同，只有右侧文字不同。
    """
    return Image.open(ROOT / "tools" / "assets" / "vivid-mark.png").convert("RGBA")


def _draw_av3a():
    """AV3A = 三维菁彩声 / Audio Vivid。

    官方标识是「三角 + ΛUDIO Vivid」，和 HDR Vivid 同一个图形，只有文字不同。
    所以这里不再自己编图形，直接沿用官方那套。
    """
    im = _blank()
    m = _vivid_mark()
    k = 26 / m.height
    m = m.resize((max(1, round(m.width * k)), 26), Image.LANCZOS)
    im.alpha_composite(m, (2, 15))
    d = ImageDraw.Draw(im)
    d.text((m.width + 7, 19), "AUDIO", font=_font(14), fill=(242, 242, 242, 255), anchor="lm")
    d.text((m.width + 7, 35), "Vivid", font=_font(15), fill=(242, 242, 242, 255), anchor="lm")
    return im


def _draw_hdrvivid():
    """HDR Vivid = 菁彩 HDR，官方标识「三角 + HDR Vivid」。

    上一版是照 HDR10 的放射楔形画的，那是杜比的视觉语言，不是菁彩的。
    现在换成官方三角，和 AV3A 共用同一个图形。
    """
    im = _blank()
    m = _vivid_mark()
    k = 26 / m.height
    m = m.resize((max(1, round(m.width * k)), 26), Image.LANCZOS)
    im.alpha_composite(m, (2, 15))
    d = ImageDraw.Draw(im)
    d.text((m.width + 7, 19), "HDR", font=_font(16), fill=(242, 242, 242, 255), anchor="lm")
    d.text((m.width + 7, 36), "Vivid", font=_font(16), fill=(242, 242, 242, 255), anchor="lm")
    return im


CUSTOM_WORDMARKS = {
    "8k": _draw_8k, "vhs": _draw_vhs, "tv": _draw_tv, "hdmv": _draw_hdmv,
    "mjpeg": _draw_mjpeg, "prores": _draw_prores, "av3a": _draw_av3a,
    "hdrvivid": _draw_hdrvivid, "hdr_vivid": _draw_hdrvivid,
}

def draw_wordmark(text: str, key: str | None = None) -> Image.Image:
    """白色字标：与素材里 Xvid / WMA 那类纯白 logo 同一种观感。

    key 命中 CUSTOM_WORDMARKS 时走手绘（照同类 logo 的结构画），否则走白字。
    """
    custom = CUSTOM_WORDMARKS.get((key or "").lower())
    if custom is not None:
        # 和真素材走同一条归一化：裁掉透明边 + 等比放大填满画布。
        # 不这么做，画得小的图（tv / 8K）会比同排的 logo 小一圈。
        return normalize(custom())
    ss = 4
    im = Image.new("RGBA", (CANVAS_W * ss, CANVAS_H * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # 固定光学高度：短词（VHS）不能因为字少就被放大，长词（WAVPACK）超宽才缩。
    # 0.52 比原来的 0.45 更饱满，和 AV1 / VP9 那类 logo 的可视高度对齐。
    size = int(CANVAS_H * ss * 0.52)
    # 只有 Regular 字重，用同色描边模拟粗体：按字号 7% 加粗，短词短到 1px 也不糊
    stroke = max(ss, int(size * 0.07))
    font = ImageFont.truetype(str(FONT_PATH), size)
    box = d.textbbox((0, 0), text, font=font, stroke_width=stroke)
    while (box[2] - box[0]) > (CANVAS_W * ss - 6 * ss) and size > 8:
        size -= 1
        font = ImageFont.truetype(str(FONT_PATH), size)
        box = d.textbbox((0, 0), text, font=font, stroke_width=stroke)
    # 按文字实际包围盒居中（textbbox 的原点不是左上角，要减掉偏移）
    d.text(((im.width - (box[2] - box[0])) // 2 - box[0],
            (im.height - (box[3] - box[1])) // 2 - box[1]),
           text, font=font, fill=(255, 255, 255, 255),
           stroke_width=stroke, stroke_fill=(255, 255, 255, 255))
    return im.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)


def load_text_maps() -> dict[str, list[tuple[str, str]]]:
    """从 XML 的 TextMap 读真实取值和显示名，避免脚本和皮肤各写一份清单。"""
    root = ET.parse(XML).getroot()
    return {
        m.get("name"): [(e.get("key"), (e.text or "").strip()) for e in m.findall("entry")]
        for m in root.findall("map")
    }


def build() -> tuple[dict[str, list[tuple[str, str]]], list[str], list[str]]:
    """返回 (map 名 -> [(key, 图标相对路径)], 用素材画的, 用字标兜底的)。

    每个取值都会拿到图标：素材库有就归一化，没有就用它的显示名渲染成白字标。
    这样运行时不依赖"这个值有没有图标"的判断 —— $MAP 只出现在 <texture> 里，
    和现有代码的用法一致，不会踩到"$MAP 能不能进 <visible>"这个未知数。
    """
    text_maps = load_text_maps()
    maps: dict[str, list[tuple[str, str]]] = {}
    from_assets: list[str] = []
    from_text: list[str] = []

    for map_name, (subdir, dirs, alias) in CATEGORIES.items():
        text_map = map_name.replace("IconMap", "TextMap")
        idx = index_dirs(dirs)
        entries: list[tuple[str, str]] = []
        seen: set[str] = set()
        for key, label in text_maps.get(text_map, []):
            k = key.lower()
            if k in seen:
                continue
            seen.add(k)
            src = idx.get(k) or idx.get(alias.get(k, ""))
            dest = OUTDIR / subdir / f"{key}.png"
            dest.parent.mkdir(parents=True, exist_ok=True)
            if src is not None:
                normalize(src).save(dest, optimize=True)
                from_assets.append(f"{subdir}/{key}")
            else:
                # 素材库没有这个格式的 logo，用显示名画白字标，风格与 Xvid / WMA 那类一致
                draw_wordmark(label or key, key).save(dest, optimize=True)
                from_text.append(f"{subdir}/{key}  ({label or key})")
            entries.append((key, f"{subdir}/{key}"))
        maps[map_name] = entries

    # 额外徽章：不进 TextMap 的独立图标（fuse3 的 Atmos 叠加徽章就是这种用法）
    for subdir, names in EXTRA_ICONS.items():
        idx = index_dirs(CATEGORIES_BY_SUBDIR[subdir][1])
        for name in names:
            src = idx.get(name)
            if src is None:
                continue
            dest = OUTDIR / subdir / f"{name}.png"
            dest.parent.mkdir(parents=True, exist_ok=True)
            normalize(src).save(dest, optimize=True)
            from_assets.append(f"{subdir}/{name}")

    return maps, from_assets, from_text


def verify() -> list[str]:
    """校验产物自洽：TextMap 的每个 key 都有 IconMap entry，且对应文件存在。

    不读本机的源皮肤目录 —— CI 上没有 skin.arctic.* 那些素材，
    重跑 build() 会退化成全字标，反而误报。
    """
    problems: list[str] = []
    text = XML.read_text(encoding="utf-8")
    root = ET.fromstring(text)
    text_maps = {m.get("name"): [e.get("key") for e in m.findall("entry")]
                 for m in root.findall("map") if m.get("name", "").endswith("TextMap")}
    icon_maps = {m.get("name"): {e.get("key"): (e.text or "").strip() for e in m.findall("entry")}
                 for m in root.findall("map") if m.get("name", "").endswith("IconMap")}

    # 只校验本脚本负责的四类；DolbyVisionProfileTextMap 是"P7/P8"小字，本来就没有图标
    for icon_name in CATEGORIES:
        text_name = icon_name.replace("IconMap", "TextMap")
        keys = text_maps.get(text_name, [])
        entries = icon_maps.get(icon_name)
        if entries is None:
            problems.append(f"缺少 {icon_name}")
            continue
        for key in keys:
            rel = entries.get(key)
            if not rel:
                problems.append(f"{icon_name} 缺 key: {key}")
            elif not (OUTDIR / f"{rel}.png").is_file():
                problems.append(f"文件缺失: media/techflags/color/{rel}.png")
    return problems


def render_block(maps: dict[str, list[tuple[str, str]]]) -> str:
    out = [BEGIN]
    for name, entries in maps.items():
        out.append(f'\t<map name="{name}">')
        for key, rel in entries:
            out.append(f"\t\t<entry key=\"{key}\">{rel}</entry>")
        out.append("\t</map>")
    out.append(END)
    return "\n".join(out)


def sync_xml(block: str, check: bool) -> bool:
    text = XML.read_text(encoding="utf-8")
    if BEGIN in text:
        head, _, rest = text.partition(BEGIN)
        _, _, tail = rest.partition(END)
        new = head + block + tail
    else:
        new = text.replace("\t<!-- The shared row owns all display-name normalization",
                           block + "\n\n\t<!-- The shared row owns all display-name normalization")
    if check:
        return new == text
    if new != text:
        XML.write_text(new, encoding="utf-8")
    return True


def main() -> int:
    check = "--check" in sys.argv
    report_only = "--report" in sys.argv

    # --check 只校验已入库的产物，不重跑 build()：CI 上没有源皮肤素材，
    # 重跑会把图标全退化成字标，反而掩盖问题。
    if check:
        problems = verify()
        if problems:
            print("✗ 图标产物与 map 不一致：")
            for x in problems[:20]:
                print("   ", x)
            print("\n   请运行 tools/gen_techflag_icons.py 重新生成")
            return 1
        print("✓ 图标产物、IconMap 与 TextMap 一致")
        return 0

    maps, from_assets, from_text = build()
    block = render_block(maps)

    total = sum(len(v) for v in maps.values())
    for name, entries in maps.items():
        print(f"{name:38} {len(entries):3} 个")
    print(f"{'合计':38} {total:3} 个"
          f"（素材 {len(from_assets)} + 字标兜底 {len(from_text)}）")
    if from_text:
        print("\n素材库没有 logo、用显示名渲染成白字标的：")
        for m in from_text:
            print("   ", m)

    if report_only:
        return 0
    sync_xml(block, check=False)
    print(f"\n已写入 {XML.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
