#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scan_rounded.py — 扫全皮肤，找出「该圆角但没挂 diffuse 遮罩」的图片控件。

它干什么
--------
把 xml/ 下所有 `<texture>` 按四类分开：
  shape       形状/纯色/九宫格贴图（shapes/ dialogs/ buttons/ ring mask_ edge_ …）→ 不用圆角
  transparent 透明 PNG（clearlogo / vendor_logo / DefaultActor）           → 没角可圆
  background  hero / fanart 大图                                          → 通常不做（贴边）
  content     其余（海报、缩略图、封面、台标）                            → **该圆角**

只报 content 类里**没写 `diffuse`** 的控件，按尺寸降序列出。

用法
----
  python tools/scan_rounded.py            # A 内容图 + B 背景图
  python tools/scan_rounded.py --all      # 再加 C 透明 PNG

判读
----
- `[尺寸未知]` 的行是尺寸来自 `<include>` 参数（`$PARAM[width]`）的控件，
  脚本静态解析不到，需要人工看调用点。
- 报出来的不一定都要改：`View_50_List` / `View_54_InfoWall` 的贴边大图是**故意**不做圆角的
  （圆角后四角会露出底板色），理由见 docs/HANDOVER.md §8.3.1。
"""

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
XML_DIR = os.path.join(ROOT, "xml")

# 形状 / 纯色 / 图标类贴图：本身不是"内容图"，不需要圆角
SHAPE_RE = re.compile(
    r"^(shapes/|colors/|overlays/|flagging/|dialogs/|buttons/|frame/|osd/|icons/|masks/|techflags/)"
    r"|glass\d+\.png|round\d+\.png|^ring|^mask_|^edge_|shadow|gradient|separator"
)
BG_RE = re.compile(r"fanart|backgrounds/primary|RandomFanart|SourceFanart", re.I)
TRANSPARENT_RE = re.compile(r"clearlogo|clearart|vendor_logo|DefaultActor|DefaultIcon|Logo\.png", re.I)

MIN_SIDE = 100  # 短边都小于这个值的控件不报（列表行小图标）


def text(el):
    return (el.text or "").strip()


def num(v):
    try:
        return float(v)
    except Exception:
        return None


def classify(tex):
    if SHAPE_RE.search(tex):
        return "shape"
    if TRANSPARENT_RE.search(tex):
        return "transparent"
    if BG_RE.search(tex):
        return "background"
    return "content"


def collect():
    rows = []
    for fn in sorted(os.listdir(XML_DIR)):
        if not fn.endswith(".xml"):
            continue
        try:
            root = ET.parse(os.path.join(XML_DIR, fn)).getroot()
        except Exception as e:  # noqa: BLE001
            print("!! 解析失败 %s: %s" % (fn, e), file=sys.stderr)
            continue

        def walk(el, stack):
            for child in el:
                if child.tag == "control":
                    stack = stack + [child]
                if child.tag == "texture":
                    owner = None
                    for anc in reversed(stack):
                        if anc.get("type") in ("image", "multiimage", "button", "resize", "group"):
                            owner = anc
                            break
                    if owner is not None:
                        w = h = None
                        for c in owner:
                            if c.tag == "width":
                                w = num(text(c))
                            if c.tag == "height":
                                h = num(text(c))
                        rows.append(dict(file=fn, w=w, h=h, tex=text(child),
                                         diffuse=child.get("diffuse"),
                                         ctype=owner.get("type"), cid=owner.get("id") or ""))
                walk(child, stack)

        walk(root, [])
    return rows


def dump(title, rows, kinds):
    print("=== %s ===" % title)
    seen = set()
    for r in sorted(rows, key=lambda r: (r["file"], -(r["w"] or 0))):
        if r["diffuse"] or classify(r["tex"]) not in kinds:
            continue
        if r["w"] is not None and r["h"] is not None and r["w"] < MIN_SIDE and r["h"] < MIN_SIDE:
            continue
        key = (r["file"], r["w"], r["h"], r["tex"])
        if key in seen:
            continue
        seen.add(key)
        if r["w"] is None or r["h"] is None:
            print("  [尺寸未知] %-36s id=%-6s tex=%s" % (r["file"], r["cid"], r["tex"][:66]))
        else:
            print("  %6dx%-6d %-36s id=%-6s tex=%s"
                  % (r["w"], r["h"], r["file"], r["cid"], r["tex"][:66]))
    if not seen:
        print("  （无）")
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="连透明 PNG 一起列")
    args = ap.parse_args()

    rows = collect()
    dump("A. 内容图（应圆角）— 未挂 diffuse", rows, {"content"})
    dump("B. 背景图（hero/fanart，通常不做）— 未挂 diffuse", rows, {"background"})
    if args.all:
        dump("C. 透明 PNG（clearlogo/默认图标，不用做）— 未挂 diffuse", rows, {"transparent"})
    return 0


if __name__ == "__main__":
    sys.exit(main())
