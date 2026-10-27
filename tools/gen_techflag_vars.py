#!/usr/bin/env python3
"""把 Includes_VideoTechnicalFlags.xml 里的 <map> 展开成条件 <variable>。

背景：`$MAP[]` 是 Kodi 22 才加的标签查表语法，21 的解析器只认
`$INFO/$ESCINFO/$VAR/$ESCVAR`（见 21.2 的 guiinfo/GUIInfoLabel.cpp）。

凡是"标签名写死"的地方（例如 `VideoPlayer.AudioCodec`），用 `String.IsEqual`
条件链就能还原出和 `$MAP` 一样的显示名，21/22 都能用。
"标签名由 `$PARAM` 传入"的地方（详情页技术标识，容器 id 会变）无法用静态变量表达，
那里保留 `$MAP`，并用 `$EXP[nara_kodi21]` 在 21 上退化成原始值。

本脚本只生成"标签名固定"的那一族（Player），写进 Variables.xml 的标记区间，
可重复执行；`--check` 供 CI 校验是否与 map 同步。

用法：
    python tools/gen_techflag_vars.py
    python tools/gen_techflag_vars.py --check
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
XML = ROOT / "xml"
SRC = XML / "Includes_VideoTechnicalFlags.xml"
DST = XML / "Variables.xml"

BEGIN = "\t<!-- BEGIN generated: technical flag maps (Kodi 21 compatible) -->"
END = "\t<!-- END generated: technical flag maps (Kodi 21 compatible) -->"

# map 名 -> (变量名中缀, VideoPlayer 命名空间下的标签名)
MAPS = {
    "NaraTechnicalResolutionTextMap": ("Resolution", "VideoResolution"),
    "NaraTechnicalHdrTextMap": ("Hdr", "HdrType"),
    "NaraTechnicalDolbyVisionProfileTextMap": ("Dv", "HdrDetail"),
    "NaraTechnicalVideoCodecTextMap": ("Video", "VideoCodec"),
    "NaraTechnicalAudioCodecTextMap": ("Audio", "AudioCodec"),
}


def load_maps() -> dict[str, list[tuple[str, str]]]:
    root = ET.parse(SRC).getroot()
    return {
        m.get("name"): [
            (e.get("key"), (e.text or "").strip()) for e in m.findall("entry")
        ]
        for m in root.findall("map")
    }


def render(maps: dict[str, list[tuple[str, str]]]) -> str:
    out = [BEGIN]
    for map_name, (infix, label) in MAPS.items():
        entries = maps.get(map_name)
        if not entries:
            continue
        out.append(f'\t<variable name="NaraTech{infix}Player">')
        seen: set[str] = set()
        for key, text in entries:
            # String.IsEqual 用的是 EqualsNoCase，大小写不同的重复条目可以去掉
            if key.lower() in seen:
                continue
            seen.add(key.lower())
            out.append(
                f'\t\t<value condition="String.IsEqual(VideoPlayer.{label},{key})">{text}</value>'
            )
        out.append(f"\t\t<value>$INFO[VideoPlayer.{label}]</value>")
        out.append("\t</variable>")
    out.append(END)
    return "\n".join(out)


def main() -> int:
    block = render(load_maps())
    text = DST.read_text(encoding="utf-8")

    if BEGIN in text:
        head, _, rest = text.partition(BEGIN)
        _, _, tail = rest.partition(END)
        new = head + block + tail
    else:
        # 首次运行：插到 </includes> 之前
        new = text.replace("</includes>", block + "\n</includes>")

    if "--check" in sys.argv:
        if new != text:
            print("Variables.xml 与 map 不同步，请运行 tools/gen_techflag_vars.py")
            return 1
        print("Variables.xml 与 map 同步")
        return 0

    DST.write_text(new, encoding="utf-8")
    print(f"已更新 {DST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
