"""皮肤静态自检：找出引用缺失的 include / 变量 / 文本串 / 贴图 / 字体，
以及残留的魔改内核专属属性、只在 Kodi 22 才有的写法。

用法：
    python extras/audit_skin.py [--verbose] [--strict]

退出码：发现"硬错误"（XML 解析失败、缺失 include / 变量 / 字体 / 贴图、
$MAP 缺 Kodi 21 守卫）返回 1；只有软提示（皮肤字符串缺失）返回 0。
`--strict` 时软提示也算失败。
"""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
XML = ROOT / "xml"
MEDIA = ROOT / "media"
LANG = ROOT / "language"

INCLUDE_REF = re.compile(r"<include(?:\s+content=\"([^\"]+)\"|\s*>([^<]+)</include>)")
VAR_REF = re.compile(r"\$VAR\[([^\]]+)\]")
LOC_REF = re.compile(r"\$LOCALIZE\[(\d+)\]")
FONT_REF = re.compile(r"<font>([^<]+)</font>")
TEXTURE_REF = re.compile(
    r"<(?:texture|texturefocus|texturenofocus|bordertexture|alttexturefocus"
    r"|alttexturenofocus|midtexture|lefttexture|righttexture|texturebg|thumb|icon|fallback)"
    r"[^>]*>([^<]+)</"
)

FORK_ATTRS = [
    "material", "glassstyle", "glassedge", "blurradius", "glassprogressiveblur",
    "glassbackgroundopacity", "glassrefractionlevel", "glassbodyrefraction",
    "glassspecularopacity", "glassspecularsaturation",
    "cornerradius", "cornerinset", "cornerborder", "cornerglow",
    "texturebackground", "selectionsettledelay",
    "holdscrollmaxspeed", "holdscrolltargettime", "slotlist",
    "playbacktarget", "checkautoplaynextitem", "focusplaying",
]

# 只在 Kodi 22 才有的写法（21 上会原样显示成表达式文本）
KODI22_ONLY = ["$MAP[", "$ESCMAP["]


def main() -> int:
    verbose = "--verbose" in sys.argv
    strict = "--strict" in sys.argv
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
    kodi22_hits: dict[str, list[str]] = defaultdict(list)
    parse_errors: list[str] = []
    has_kodi21_guard = False

    for path in files:
        raw = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ET.parse(path)
        except ET.ParseError as exc:
            parse_errors.append(f"{path.name}: {exc}")
            continue

        root = tree.getroot()
        for node in root.iter():
            tag = node.tag
            if tag == "include" and node.get("name"):
                includes_defined.add(node.get("name"))
            elif tag == "variable" and node.get("name"):
                variables_defined.add(node.get("name"))
            elif tag == "font" and node.find("name") is not None:
                fonts_defined.add((node.find("name").text or "").strip())
            elif tag == "expression" and node.get("name") == "nara_kodi21":
                has_kodi21_guard = True

            # 只统计真实节点：注释已被 ElementTree 丢弃，不会误报
            for attr_name in node.attrib:
                if attr_name in FORK_ATTRS:
                    fork_hits[attr_name].append(path.name)
            for value in list(node.attrib.values()) + ([node.text] if node.text else []):
                for token in KODI22_ONLY:
                    if token in value:
                        kodi22_hits[token].append(path.name)

        # 引用类检查仍扫原文：Kodi 允许 <include content="X" /> 这种写法
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
        for tex in TEXTURE_REF.findall(raw):
            if tex.strip():
                textures_used[tex.strip()].append(path.name)

    # 语言串：皮肤自有区间是 31000-31999，其余都是 Kodi 内置串
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

    missing_loc = {
        k: v for k, v in loc_used.items() if 31000 <= int(k) < 32000 and k not in skin_strings
    }

    print(f"文件 {len(files)} 个；include {len(includes_defined)} 个定义 / "
          f"{len(includes_used)} 个引用；变量 {len(variables_defined)} 个定义；"
          f"字体 {len(fonts_defined)} 个定义")

    if parse_errors:
        print(f"\n## XML 解析失败：{len(parse_errors)} 个")
        for err in parse_errors:
            print(f"  - {err}")

    report("缺失 include", missing_include)
    report("缺失变量", missing_var)
    report("缺失字体", missing_font)
    report("缺失贴图", missing_texture)
    report("缺失皮肤字符串", missing_loc)

    print(f"\n## 残留魔改内核属性：{len(fork_hits)} 类")
    for attr, where in sorted(fork_hits.items()):
        print(f"  - {attr}  ← {', '.join(sorted(set(where)))}")

    print(f"\n## 仅 Kodi 22 支持的写法：{len(kodi22_hits)} 类")
    for token, where in sorted(kodi22_hits.items()):
        print(f"  - {token}  ← {', '.join(sorted(set(where)))}")
    if kodi22_hits and not has_kodi21_guard:
        print("  ! 用了 $MAP 却没有 nara_kodi21 表达式，Kodi 21 上会原样显示表达式文本")

    if verbose:
        print("\n## 贴图引用总数", len(textures_used))

    if (parse_errors or missing_include or missing_var or missing_font or missing_texture
            or (kodi22_hits and not has_kodi21_guard)):
        return 1
    if strict and missing_loc:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
