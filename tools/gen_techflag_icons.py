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
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
XML = ROOT / "xml" / "Includes_VideoTechnicalFlags.xml"
OUTDIR = ROOT / "media" / "techflags" / "color"

FUSE = Path(r"D:/Downloads/ai/skin.arctic.fuse.3/media/flags/color")
AVDV = Path(r"D:/Downloads/ai/skin.arctic.fuse.3-avdvplus&p3i/media/flags/color")
MART = Path(r"D:/Downloads/ai/skin.arctic.zephyr.martian/media/flags/color")

CANVAS_W, CANVAS_H = 96, 56          # 2:1 偏方一点，显示框 48x28 时留白最小
FONT_PATH = ROOT / "fonts" / "Inter-Unicode-Regular.ttf"

BEGIN = "\t<!-- BEGIN generated: techflag icon maps -->"
END = "\t<!-- END generated: techflag icon maps -->"

# 每个类别：输出子目录 + 候选源目录 + 别名（原始值 -> 素材文件名）
CATEGORIES = {
    "NaraTechnicalResolutionIconMap": ("resolution", [FUSE / "resolution"], {}),
    "NaraTechnicalHdrIconMap": ("hdr", [AVDV / "hdr"],
                                {"hdr_vivid": "hdrvivid"}),
    "NaraTechnicalVideoCodecIconMap": ("video", [FUSE / "source"],
                                       {"h265": "hevc", "hvc1": "hevc"}),
    "NaraTechnicalAudioCodecIconMap": ("audio", [FUSE / "audio"],
                                       {"dtsma": "dtshd_ma", "mp3float": "mp3",
                                        "wmav2": "wma", "pcm_bluray": "pcm",
                                        "pcm_s32le": "pcm_s24le", "dca": "dts"}),
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


def draw_wordmark(text: str) -> Image.Image:
    """白色字标：与素材里 Xvid / WMA 那类纯白 logo 同一种观感。"""
    ss = 4
    im = Image.new("RGBA", (CANVAS_W * ss, CANVAS_H * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # 固定光学高度：短词（VHS）不能因为字少就被放大，长词（WAVPACK）超宽才缩
    size = int(CANVAS_H * ss * 0.45)
    stroke = max(1, ss // 2)
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
                draw_wordmark(label or key).save(dest, optimize=True)
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
