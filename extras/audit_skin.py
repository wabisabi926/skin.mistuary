"""皮肤静态自检：找出引用缺失的 include / 变量 / 文本串 / 贴图 / 字体，
以及残留的魔改内核专属属性。

用法：
    python extras/audit_skin.py [--verbose]
"""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
XML = ROOT / "xml"
MEDIA = ROOT / "media"
LANG = ROOT / "language"

INCLUDE_REF = re.compile(r"<include(?:\s+content=\"([^\"]+)\"|\s*>([^<]+)</include>)")
VAR_REF = re.compile(r"\$VAR\[([^\]]+)\]")
LOC_REF = re.compile(r"\$LOCALIZE\[(\d+)\]")
FONT_REF = re.compile(r"<font>([^<]+)</font>")
TEXTURE_REF = re.compile(r"<(?:texture|texturefocus|texturenofocus|bordertexture|alttexturefocus|alttexturenofocus|midtexture|lefttexture|righttexture|texturebg|thumb|icon|fallback)[^>]*>([^<]+)</")

FORK_ATTRS = [
    "material=", "glassstyle=", "glassedge=", "blurradius=", "glassprogressiveblur=",
    "glassbackgroundopacity=", "glassrefractionlevel=", "glassbodyrefraction=",
    "glassspecularopacity=", "glassspecularsaturation=",
    "cornerradius=", "cornerinset=", "cornerborder=", "cornerglow=",
    "ListItemSettled", "texturebackground", "selectionsettledelay",
    "holdscrollmaxspeed", "holdscrolltargettime", "slotlist", "ImageChange",
    "playbacktarget=", "checkautoplaynextitem=", "focusplaying=",
]


def main() -> int:
    verbose = "--verbose" in sys.argv
    files = sorted(XML.glob("*.xml"))

    includes_defined: set[str] = set()
    variables_defined: set[str] = set()
    fonts_defined: set[str] = set()
    includes_used: dict[str, list[str]] = defaultdict(list)
    variables_used: dict[str, list[str]] = defaultdict(list)
    fonts_used: dict[str, list[str]] = defaultdict(list)
    loc_used: dict[str, list[str]] = defaultdict(list)
    textures_used: dict[str, list[str]] = defaultdict(list)
    fork_hits: dict[str, list[str]] = defaultdict(list)

    for path in files:
        raw = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ET.parse(path)
        except ET.ParseError as exc:
            print(f"[XML 解析失败] {path.name}: {exc}")
            continue

        for node in tree.iter():
            tag = node.tag
            if tag == "include" and node.get("name"):
                includes_defined.add(node.get("name"))
            elif tag == "variable" and node.get("name"):
                variables_defined.add(node.get("name"))
            elif tag == "font" and node.find("name") is not None:
                fonts_defined.add((node.find("name").text or "").strip())

        for name in INCLUDE_REF.findall(raw):
            for candidate in name:
                if candidate and not candidate.startswith("$"):
                    includes_used[candidate.strip()].append(path.name)
        for name in VAR_REF.findall(raw):
            variables_used[name.split(",")[0].strip()].append(path.name)
        for name in FONT_REF.findall(raw):
            if not name.startswith("$"):
                fonts_used[name.strip()].append(path.name)
        for name in LOC_REF.findall(raw):
            loc_used[name].append(path.name)
        for name in TEXTURE_REF.findall(raw):
            textures_used[name.strip()].append(path.name)
        for attr in FORK_ATTRS:
            if attr in raw:
                fork_hits[attr].append(path.name)

    # 语言串：Kodi 内置 0-35999 之外的部分由皮肤 po 提供
    skin_strings: set[str] = set()
    for po in LANG.glob("*/strings.po"):
        for line in po.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("msgctxt"):
                skin_strings.add(line.split('"')[1].lstrip("#"))

    def report(title: str, missing: dict[str, list[str]]) -> None:
        print(f"\n## {title}：{len(missing)} 个")
        for name, where in sorted(missing.items()):
            files_txt = ", ".join(sorted(set(where))[:4])
            more = "" if len(set(where)) <= 4 else f" …(+{len(set(where)) - 4})"
            print(f"  - {name}  ← {files_txt}{more}")

    missing_include = {k: v for k, v in includes_used.items() if k not in includes_defined}
    missing_var = {k: v for k, v in variables_used.items() if k not in variables_defined}
    missing_font = {k: v for k, v in fonts_used.items() if k not in fonts_defined}

    def texture_exists(tex: str) -> bool:
        if not tex or "$" in tex:
            return True
        if tex.startswith("special://xbmc/") or tex.startswith("special://temp/"):
            return True
        if tex.startswith("special://"):
            return (ROOT / tex.replace("special://skin/", "")).exists()
        return (MEDIA / tex).exists()

    missing_texture = {k: v for k, v in textures_used.items() if not texture_exists(k)}

    # 32000 以上是皮肤自定义字符串；检查 po 里有没有
    missing_loc = {
        k: v
        for k, v in loc_used.items()
        if int(k) >= 31000 and k not in skin_strings
    }

    print(f"文件 {len(files)} 个；include {len(includes_defined)} 个定义 / "
          f"{len(includes_used)} 个引用；变量 {len(variables_defined)} 个定义；"
          f"字体 {len(fonts_defined)} 个定义")

    report("缺失 include", missing_include)
    report("缺失变量", missing_var)
    report("缺失字体", missing_font)
    report("缺失贴图", missing_texture)
    report("缺失皮肤字符串", missing_loc)

    print(f"\n## 残留魔改内核属性：{len(fork_hits)} 类")
    for attr, where in sorted(fork_hits.items()):
        print(f"  - {attr}  ← {', '.join(sorted(set(where)))}")

    if verbose:
        print("\n## 贴图引用总数", len(textures_used))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
