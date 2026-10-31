"""皮肤静态自检：找出引用缺失的 include / 变量 / 文本串 / 贴图 / 字体，
残留的魔改内核专属属性、只在 Kodi 22 才有的写法，以及皮肤设置的读写是否配对。

用法：
    python tools/audit_skin.py [--verbose] [--strict]
    python tools/audit_skin.py --orphans    # 反向：盘上有、XML 里没人引用的贴图
    python tools/audit_skin.py --dead       # 反向：定义了、没人用的变量 / include

`--orphans` / `--dead` 是**报告模式**，永远返回 0（只提示，不进 CI 闸门）。

退出码：发现"硬错误"（XML 解析失败、缺失 include / 变量 / 字体 / 贴图、
$MAP 缺 Kodi 21 守卫）返回 1；只有软提示（皮肤字符串缺失）返回 0。
`--strict` 时软提示也算失败。

皮肤设置的"有读无写 / 有写无读"只做提示，不影响退出码——设置可能由外部
脚本或 guisettings.xml 直接写入，静态分析无法证明它一定是死功能。
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

# 贴图存在性：三种写法都要认，否则会漏报（或误报）
#   ① 相对 media/ 的短名（`shapes/glass20.png`）—— 皮肤里最常见
#   ② `special://skin/...` —— 根目录下的 libraryart/ extras/ resources/ 都走这条
#   ③ `special://xbmc/` `special://temp/` —— Kodi 自己的，不在包里，一律当存在
# 含 `$` 的是动态路径（`libraryart/$INFO[ListItem.Label].jpg`），静态查不了，跳过。
def texture_exists(tex: str) -> bool:
    if not tex or "$" in tex:
        return True
    if tex.startswith("special://xbmc/") or tex.startswith("special://temp/"):
        return True
    if tex.startswith("special://"):
        return (ROOT / tex.replace("special://skin/", "")).exists()
    return (MEDIA / tex).exists()


INCLUDE_REF = re.compile(r"<include(?:\s+content=\"([^\"]+)\"|\s*>([^<]+)</include>)")
VAR_REF = re.compile(r"\$VAR\[([^\]]+)\]")
LOC_REF = re.compile(r"\$LOCALIZE\[(\d+)\]")
FONT_REF = re.compile(r"<font>([^<]+)</font>")
TEXTURE_REF = re.compile(
    r"<(?:texture|texturefocus|texturenofocus|bordertexture|alttexturefocus"
    r"|alttexturenofocus|midtexture|lefttexture|righttexture|texturebg|thumb|icon|fallback)"
    r"[^>]*>([^<]+)</"
)
# `diffuse="..."` 是贴图级的遮罩（HANDOVER §5.4.1），**也要检查文件是否存在**。
# 2026-10-28 漏生成 mask_214x321_r11 时这里没报，搜索页就一直是方角 —— 补上这条。
# 前面用 (?<![A-Za-z]) 排除 colordiffuse / scalediffuse（它们的尾巴也是 "diffuse="）。
DIFFUSE_REF = re.compile(r'(?<![A-Za-z])diffuse="([^"]+)"')

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

# Kodi 的 GUIControlFactory::GetTexture 只解析这些属性，其余一律静默忽略。
# fallback= 是 Kodi 22 新增的贴图级兜底（官方 Estuary 22 大量使用），
# 缺图时显示占位贴图；Kodi 21 会忽略该属性，只影响兜底效果，不会报错。
TEXTURE_ATTRS_OK = {
    "border", "infill", "flipx", "flipy", "diffuse",
    "colordiffuse", "background", "mipmap", "subpixel",
}

# 皮肤设置的读取 / 写入内置函数。
# 写入端必须列全：2026-10-26 那次判断"15 个设置只读"，就是因为只搜了
# SetString / ToggleSetting，漏掉了 SelectBool / SetNumeric / SetPath / SetAddon。
# 正则尾部要求紧跟 , 或 ) —— 否则动态名（Skin.SetBool(home_no_$PARAM[x])）
# 会被截成半截名字 home_no_，凭空造出一个"写入了但没人读"的假象。
SKIN_READ = re.compile(
    r"Skin\.(?:HasSetting|String|Numeric)\(\s*([A-Za-z0-9_.\-]+)\s*[),]"
)
SKIN_WRITE = re.compile(
    r"Skin\.(?:SetBool|SetString|SetNumeric|SetPath|SetAddon|SetImage|SetFile"
    r"|SetColor|ToggleSetting|Reset)\(\s*([A-Za-z0-9_.\-]+)\s*[),]"
)
SELECT_BOOL_ARGS = re.compile(r"Skin\.SelectBool\(([^)]*)\)")

# SelectBool(头部id, 数字|设置名, ...) 里**两个数字都是字符串 id**，都不走 $LOCALIZE：
#   头部 id 后面跟逗号，配对里的 id 后面跟竖线。
# 2026-10-30 删"未引用字符串"时只扫了 $LOCALIZE，把这 5 条删错了
# （31730/31731/31760 三档透明度标题、31764 TMDb、31766 IMDb）。
SELECT_BOOL_IDS = re.compile(r"(?<![_\w])(\d+)\s*[|,]")


def string_refs(text: str) -> set[str]:
    """一条 XML 文本里引用到的全部字符串 id（$LOCALIZE + Skin.SelectBool）。"""
    refs: set[str] = set(LOC_REF.findall(text))
    for m in SELECT_BOOL_ARGS.finditer(text):
        refs |= set(SELECT_BOOL_IDS.findall(m.group(1)))
    return refs


WRITE_BUILTINS_DOC = (
    "SetBool/SetString/SetNumeric/SetPath/SetAddon/SetImage/SetFile/SetColor/"
    "ToggleSetting/Reset + SelectBool 的 name|setting 对"
)

# SelectBool 里的"恢复默认"选项：选中它等于把同组的其它开关全部置假，
# 它自己永远不会被读取，所以"有写无读"对它们是正常状态。
RESET_ONLY_SETTINGS = {"circle_none", "OriginalTitleFormat_Default"}
# 默认档位：它是变量里那条**无 condition** 的兜底 value，所以不会出现在
# Skin.HasSetting(...) 里。属于"写了但按设计没人直接读"。
# rating_src_tmdb / rating_sec_auto = 主/次评分来源的默认档。
DEFAULT_ONLY_SETTINGS: set[str] = {"rating_src_tmdb", "rating_sec_auto"}

# ---------------------------------------------------------------------------
# 浮窗不透明度检查（docs/glass-opacity-plan.md）
# ---------------------------------------------------------------------------
# 有这些 token 之一 = 该窗口有玻璃面板
# （面板色 2026-10-26 起改由 $VAR 提供，所以变量名也要算作"有面板"）
PANEL_TOKENS = (
    "glass_frosted", "glass_dialog", "glass_page",
    "NaraGlassPageTintVar", "NaraGlassFloatTintVar", "NaraPlaybackDialogTintVar",
    "NaraDialogGlassTexture", "NaraDialogGlassSurface",
    "ContentPanel", "NaraSettingsDialogFrame",
)
# 有这些 token 之一 = 该窗口有遮蔽层（或走的是自带遮蔽层的公共 include）
SCRIM_TOKENS = (
    "scrim_dialog", "scrim_sheet", "scrim_osd", "NaraGlassScrimTintVar",
    "NaraGlassFloatScrimVar",
    "NaraDialogScrim", "DialogBackgroundCommons", "NaraSettingsDialogFrame",
    "NaraPowerMenuLayout", "NaraStreamDialogBackground",
    "NaraMusicPlaylistBackground",
)
# 有意不加全屏遮蔽的浮窗：
#   DialogNotification       瞬时提示条，加全屏遮蔽会干扰观看
#   Custom_1100_AddonLauncher 整页（不是浮窗），靠自己的背景层压暗
SCRIM_EXEMPT = {"DialogNotification.xml", "Custom_1100_AddonLauncher.xml"}

HARDCODED_BLACK_SCRIM = re.compile(
    r'colordiffuse="([0-9A-Fa-f]{8})"[^>]*>colors/black\.png'
)


def is_floating_window(name: str) -> bool:
    """Dialog*.xml 与 Custom_11xx 是浮窗/弹出层；其余是全屏页。"""
    return name.startswith("Dialog") or name.startswith("Custom_11")



def collect_skin_settings(raw_texts) -> tuple[dict, dict]:
    """从 XML 原文收集皮肤设置的读取点与写入点。

    raw_texts 是 (文件名, 原文) 的可迭代对象。返回 (reads, writes)，
    两个 dict 的键是设置名、值是出现位置列表。
    """
    reads: dict[str, list[str]] = defaultdict(list)
    writes: dict[str, list[str]] = defaultdict(list)

    for name, text in raw_texts:
        for key in SKIN_READ.findall(text):
            reads[key].append(name)
        for key in SKIN_WRITE.findall(text):
            writes[key].append(name)
        # SelectBool(header, 标签|设置名, ...)：单选互斥，每个配对都是写入点
        for args in SELECT_BOOL_ARGS.findall(text):
            for part in args.split(","):
                if "|" in part:
                    key = part.split("|", 1)[1].strip()
                    if key and not key.startswith("$"):
                        writes[key].append(name)

    return reads, writes


def main() -> int:
    if "--orphans" in sys.argv:
        return report_orphans()
    if "--dead" in sys.argv:
        return report_dead()
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
    texture_attr_hits: dict[str, list[str]] = defaultdict(list)
    parse_errors: list[str] = []
    has_kodi21_guard = False
    raw_texts: list[tuple[str, str]] = []

    for path in files:
        raw = path.read_text(encoding="utf-8", errors="replace")
        raw_texts.append((path.name, raw))
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
                if tag == "texture" and attr_name not in TEXTURE_ATTRS_OK:
                    texture_attr_hits[attr_name].append(path.name)
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
        for name in string_refs(raw):
            loc_used[name].append(path.name)
        for tex in TEXTURE_REF.findall(raw):
            if tex.strip():
                textures_used[tex.strip()].append(path.name)
        for tex in DIFFUSE_REF.findall(raw):
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

    print(f"\n## Kodi 不解析的 <texture> 属性：{len(texture_attr_hits)} 类")
    if texture_attr_hits:
        print(f"  （合法属性只有 {', '.join(sorted(TEXTURE_ATTRS_OK))}）")
    for attr, where in sorted(texture_attr_hits.items()):
        files_txt = ", ".join(sorted(set(where))[:4])
        more = "" if len(set(where)) <= 4 else f" …(+{len(set(where)) - 4})"
        print(f"  - {attr}=  ← {len(where)} 处，{files_txt}{more}")

    # ------------------------------------------------------------------
    # 浮窗不透明度：玻璃面板必须配一层遮蔽层
    # 见 docs/glass-opacity-plan.md。只有面板、没有遮蔽的浮窗，底下是清晰原图，
    # 白字会跟海报标题打架——2026-10-26 全量梳理时 11 个浮窗栽在这上面。
    # ------------------------------------------------------------------
    no_scrim = [n for n, raw in raw_texts
                if is_floating_window(n) and n not in SCRIM_EXEMPT
                and any(t in raw for t in PANEL_TOKENS)
                and not any(t in raw for t in SCRIM_TOKENS)]
    hard_scrim: list[str] = []
    for name, raw in raw_texts:
        if not is_floating_window(name):
            continue
        for m in HARDCODED_BLACK_SCRIM.finditer(raw):
            v = m.group(1).upper()
            # 只看半透明黑（alpha != FF 且 RGB 全 0），那才是"遮蔽色"
            if v[:2] != "FF" and v[2:] == "000000":
                hard_scrim.append(f"{name}: {v}")

    print(f"\n## 浮窗缺遮蔽层：{len(no_scrim)} 个")
    if no_scrim:
        print("  （有玻璃面板但既没有 scrim_* 也没有 DialogBackgroundCommons）")
        for name in no_scrim:
            print(f"  - {name}")
    print(f"\n## 浮窗里的硬编码遮蔽色：{len(hard_scrim)} 处")
    if hard_scrim:
        print("  （应改用 scrim_dialog / scrim_sheet / scrim_osd token）")
        for hit in hard_scrim:
            print(f"  - {hit}")

    settings_read, settings_written = collect_skin_settings(raw_texts)
    readonly = {k: v for k, v in settings_read.items() if k not in settings_written}
    writeonly = {
        k: v for k, v in settings_written.items()
        if k not in settings_read
        and k not in RESET_ONLY_SETTINGS
        and k not in DEFAULT_ONLY_SETTINGS
    }

    print(f"\n## 皮肤设置：{len(settings_read)} 个读取 / {len(settings_written)} 个写入")
    print(f"  （写入内置函数已覆盖：{WRITE_BUILTINS_DOC}）")
    print(f"  - 有读无写（永远停在默认值）：{len(readonly)} 个")
    for name, where in sorted(readonly.items()):
        print(f"    - {name}  ← {', '.join(sorted(set(where))[:4])}")
    print(f"  - 有写无读（写了没人用）：{len(writeonly)} 个")
    for name, where in sorted(writeonly.items()):
        print(f"    - {name}  ← {', '.join(sorted(set(where))[:4])}")

    if verbose:
        print("\n## 贴图引用总数", len(textures_used))

    if (parse_errors or missing_include or missing_var or missing_font or missing_texture
            or (kodi22_hits and not has_kodi21_guard)):
        return 1
    if strict and missing_loc:
        return 1
    return 0


# ---------------------------------------------------------------- 反向检查
# 2026-10-29 补：以前只查"引用了但文件不存在"，不查"文件在但没人用"。
# media/settings/background.png（1.87 MB）就是这么在包里躺了半个月。

# 贴图路径里的动态段：$PARAM[...] / $INFO[...] / $VAR[...] —— 整族都算被引用
_DYN = re.compile(r"\$(?:ESC)?(?:PARAM|INFO|VAR|ESCINFO|ESCVAR)\[([^\]]*)\]")
# Kodi 自带的默认图标（DefaultAddon.png 之类），由 <fallback>/<icon> 隐式引用
# Kodi 按**文件名**自己去 media/ 找的贴图，XML 里不会出现：
#   OverlayWatched.png / OverlayHD.png …  → CFileItem::GetOverlayImage()
#   pointer_arrow.png / pointer_click.png → 鼠标指针
#   spinner.png（DialogBusy）、defaultgenre.png（Estuary 默认类型图）
_IMPLICIT = re.compile(
    r"^(?:Default[A-Za-z0-9]*|Overlay[A-Za-z]*|pointer_[a-z]+|spinner|defaultgenre)\.png$")
# 任何位置出现的 png 路径（含空格和 & —— genres 里有 "sci-fi & fantasy.png"）
PATH_RE = re.compile(r"[A-Za-z0-9_\-./ &]+\.png")


def _strip_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def _texture_refs() -> tuple[set[str], set[str]]:
    """返回 (字面路径集合, 动态前缀集合)。

    贴图路径不只出现在 `<texture>` 里——`<variable><value>`、`<param value="...">`、
    itemlayout 的 `<icon>` 都可能写路径，所以这里**整段文本扫**。

    动态写法有三类，都要认：
      `techflags/color/$PARAM[icon].png`      → 前缀 `techflags/color/`
      `shapes/glass$PARAM[radius].png`        → 前缀 `shapes/glass`
      `$INFO[ListItem.Thumb,windows/subtitles/flags/,.png]` → 参数里的 `windows/subtitles/flags/`
    """
    literal: set[str] = set()
    dynamic: set[str] = set()
    for path in sorted(XML.glob("*.xml")):
        raw = _strip_comments(path.read_text(encoding="utf-8", errors="replace"))
        raw = raw.replace("&amp;", "&").replace("\\", "/")

        # ① $INFO/$VAR 参数里的路径片段
        for args in _DYN.findall(raw):
            for frag in args.split(","):
                frag = frag.strip()
                if "/" in frag and "$" not in frag:
                    dynamic.add(frag)

        # ② 把 $XXX[...] 整体替换成一个占位符，占位符紧邻的前缀就是动态前缀
        marked = _DYN.sub("\x00", raw)
        for m in re.finditer(r"[A-Za-z0-9_\-./ &]+\x00", marked):
            head = m.group(0)[:-1]
            if "/" in head and head[0].isalnum() and " " not in head:
                dynamic.add(head)

        # ③ 剩下的字面路径（占位符已经把动态段切掉了）
        for s in PATH_RE.findall(marked):
            s = s.strip()
            if not s or "\x00" in s:
                continue
            if s.startswith("special://skin/"):
                s = s[len("special://skin/"):]
            literal.add(s)
    return literal, dynamic


def report_orphans() -> int:
    literal, dynamic = _texture_refs()
    lit_lower = {p.lower() for p in literal}
    names = {p.rsplit("/", 1)[-1].lower() for p in literal}
    dyn_lower = [d.lower() for d in dynamic if d]
    orphans: list[tuple[str, int]] = []
    total = 0
    for f in sorted(MEDIA.rglob("*.png")):
        total += 1
        rel = str(f.relative_to(MEDIA)).replace("\\", "/")
        low = rel.lower()
        if low in lit_lower or f.name.lower() in names:
            continue
        if _IMPLICIT.match(f.name):
            continue
        if any(low.startswith(prefix) for prefix in dyn_lower):
            continue
        orphans.append((rel, f.stat().st_size))

    print(f"media 下 PNG {total} 张；XML 里没有任何引用 {len(orphans)} 张"
          f"（已排除动态前缀 {len(dynamic)} 个、Default*.png；大小写不敏感）")
    if orphans:
        size = sum(s for _, s in orphans)
        print(f"合计 {size / 1024:.1f} KB，按体积排序：")
        for rel, s in sorted(orphans, key=lambda x: -x[1]):
            print(f"  {s / 1024:9.1f} KB  {rel}")
        print("\n确认后可删：`git rm <文件>` + 同步改生成器表 + `python tools/xbt_tool.py pack`")
    return 0


def report_dead() -> int:
    texts = {p.name: _strip_comments(p.read_text(encoding="utf-8", errors="replace"))
             for p in sorted(XML.glob("*.xml"))}
    joined = "\n".join(texts.values())
    # 定义标签里的名字要去掉，否则每个定义都会把自己算成"被引用"
    no_def = re.sub(r'<variable\s+name="[^"]+"', "<variable", joined)
    no_def = re.sub(r'<include\s+name="[^"]+"', "<include", no_def)

    dead_vars = []
    for p in sorted(XML.glob("*.xml")):
        for el in ET.parse(p).getroot().iter("variable"):
            name = el.get("name")
            if not name:
                continue
            # $VAR[X] / $ESCVAR[X] / $VAR[X, fmt] —— 两个坑：ESC 前缀、格式参数
            if not re.search(r"\$(?:ESC)?VAR\[\s*" + re.escape(name) + r"\s*[,]?[^\]]*\]", joined):
                dead_vars.append(name)

    dead_incs = []
    for p in sorted(XML.glob("*.xml")):
        for el in ET.parse(p).getroot().iter("include"):
            name = el.get("name")
            if not name:
                continue
            # 三种引用：content="X"、<include>X</include>、$PARAM[...] 间接引用（值里出现名字）
            if not re.search(r"(?<![\w])" + re.escape(name) + r"(?![\w])", no_def):
                dead_incs.append(name)

    total_vars = sum(1 for p in sorted(XML.glob("*.xml"))
                     for el in ET.parse(p).getroot().iter("variable") if el.get("name"))
    total_incs = sum(1 for p in sorted(XML.glob("*.xml"))
                     for el in ET.parse(p).getroot().iter("include") if el.get("name"))
    print(f"变量：定义 {total_vars} 个，没人引用 {len(set(dead_vars))} 个")
    for n in sorted(set(dead_vars)):
        print(f"    {n}")
    print(f"\ninclude：定义 {total_incs} 个，没人引用 {len(set(dead_incs))} 个")
    for n in sorted(set(dead_incs)):
        print(f"    {n}")
    # 皮肤字符串：定义了，但 $LOCALIZE 和 Skin.SelectBool 都没引用。
    # 只扫 $LOCALIZE 会漏掉 SelectBool 里的 id（2026-10-30 因此删错 5 条）。
    str_refs: set[str] = set()
    for t in texts.values():
        str_refs |= string_refs(t)
    skin = {
        line.split('"')[1].lstrip("#")
        for po in LANG.glob("*/strings.po")
        for line in po.read_text(encoding="utf-8", errors="replace").splitlines()
        if line.startswith("msgctxt") and line.split('"')[1].lstrip("#").startswith("31")
    }
    dead_str = sorted(skin - str_refs)
    print(f"\n皮肤字符串：定义 {len(skin)} 条，没人引用 {len(dead_str)} 条")
    for n in dead_str:
        print(f"    {n}")

    print("\n注意：动态引用（$PARAM[name] 传值、变量套变量）只能按字面匹配，"
          "删之前逐个确认；`HomeVideoRowNavigation` 那种是活的。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
