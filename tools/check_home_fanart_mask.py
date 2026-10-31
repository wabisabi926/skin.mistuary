"""首页背景遮罩判据的静态一致性检查。

规则：走 primary.jpg 兜底时不压暗，真剧照才压暗。
「哪些来源算真剧照」的事实写在 Variables.xml 的 HomeFanartVar 和
Includes_HomeVideo.xml 的 HomeVideoHeroFanartVar；判据写在 Includes_Home.xml 的
三条 expression（NaraHomeFanartSubItems / SubHero / SubOther），由 Home.xml 引用。

两份数据必须同步：改了变量分支而忘了改表达式，表现就是「某个分区的真剧照
不压暗、明显比别处亮」——而且看截图前很难发现。这个脚本就是那道闸门。

用法：
    python tools/check_home_fanart_mask.py
    python tools/check_home_fanart_mask.py --check   # 显式写法，和 gen_techflag_*.py 对齐

退出码：0 = 一致；1 = 有缺漏或写法退化（表达式里混进了 $EXP/$VAR/$INFO、
Hero 分支丢了 target_folder 门、Home.xml 没接上判据等）。
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
XML = ROOT / "xml"

HERO_VAR = "HomeVideoHeroFanartVar"
FANART_VAR = "HomeFanartVar"
ITEMS_EXPR = "NaraHomeFanartSubItems"
HERO_EXPR = "NaraHomeFanartSubHero"
OTHER_EXPR = "NaraHomeFanartSubOther"

CONTAINER_RE = re.compile(r"Container\((\d+)\)")
# 条件里一旦出现这些，Kodi 的 InfoExpression::Parse 会把整串当分组拆开，
# operand 注册失败 → 整条表达式判 false（本项目 docs/HANDOVER.md:606 有实测记录）。
FORBIDDEN = ("$EXP[", "$VAR[", "$INFO[", "$MAP[")

errors: list[str] = []
warnings: list[str] = []
checks = 0


def ok(msg: str) -> None:
    global checks
    checks += 1
    print(f"[OK]   {msg}")


def fail(msg: str) -> None:
    global checks
    checks += 1
    errors.append(msg)
    print(f"[FAIL] {msg}")


def warn(msg: str) -> None:
    global checks
    checks += 1
    warnings.append(msg)
    print(f"[WARN] {msg}")


def read(name: str) -> str:
    return (XML / name).read_text(encoding="utf-8")


def block(text: str, tag: str, name: str, filename: str) -> str:
    m = re.search(rf'<{tag} name="{name}">(.*?)</{tag}>', text, re.S)
    if not m:
        fail(f"{filename} 里找不到 <{tag} name=\"{name}\">")
        return ""
    return m.group(1)


def ids(text: str) -> set[str]:
    return set(CONTAINER_RE.findall(text))


def main() -> int:
    parser = argparse.ArgumentParser(description="首页背景遮罩判据一致性检查")
    parser.add_argument("--check", action="store_true", help="显式检查模式（默认即检查）")
    parser.parse_args()

    includes = read("Includes_Home.xml")
    variables = read("Variables.xml")
    home_video = read("Includes_HomeVideo.xml")
    home = read("Home.xml")

    items = block(includes, "expression", ITEMS_EXPR, "Includes_Home.xml")
    hero = block(includes, "expression", HERO_EXPR, "Includes_Home.xml")
    other = block(includes, "expression", OTHER_EXPR, "Includes_Home.xml")
    hero_var = block(home_video, "variable", HERO_VAR, "Includes_HomeVideo.xml")
    fanart_var = block(variables, "variable", FANART_VAR, "Variables.xml")

    for name, body in ((ITEMS_EXPR, items), (HERO_EXPR, hero), (OTHER_EXPR, other),):
        if not body:
            continue
        bad = [token for token in FORBIDDEN if token in body]
        if bad:
            fail(f"{name} 里出现 {', '.join(bad)}：条件解析会把整条判 false，只能平铺写")
        else:
            ok(f"{name} 没有嵌套 $EXP/$VAR/$INFO/$MAP")

    hero_ids = ids(hero_var)
    home_ids = ids(fanart_var)
    subhero_ids = ids(hero)
    required = hero_ids | home_ids

    if not hero_ids:
        fail(f"{HERO_VAR} 里没解析出任何容器 id，检查 Variables/Includes_HomeVideo 是否被改坏")
    else:
        ok(f"{HERO_VAR} 覆盖 {len(hero_ids)} 个容器 id：{', '.join(sorted(hero_ids))}")

    missing = sorted(required - subhero_ids)
    if missing:
        fail(f"{HERO_EXPR} 缺少容器 id：{', '.join(missing)}（改 HomeFanartVar / HomeVideoHeroFanartVar 后必须同步）")
    else:
        ok(f"{HERO_EXPR} 覆盖了全部 {len(required)} 个需要的容器 id")

    extra = sorted(subhero_ids - required)
    if extra:
        warn(f"{HERO_EXPR} 多了容器 id：{', '.join(extra)}（确认它们是否还在用）")

    # Hero 分支必须保留 target_folder 门 + 前一张卡，否则「条目没剧照、前一张卡有」
    # 会被误判成真图，兜底图跟着被压暗（反向错误）。
    gate_failures = 0
    for cid in sorted(hero_ids):
        gate = (
            f"[String.IsEqual(Container({cid}).ListItem.Property(node.type),target_folder) "
            f"+ !String.IsEmpty(Container({cid}).ListItem(-1).Art(fanart))]"
        )
        if gate not in hero:
            gate_failures += 1
            fail(f"{HERO_EXPR} 的 {cid} 分支缺少 target_folder 门（{gate}）")
    if hero_ids and not gate_failures:
        ok(f"{HERO_EXPR} 的 {len(hero_ids)} 个 Hero 分支都带 target_folder 门")

    # 非 Hero 的容器（HomeFanartVar 里的 5100/6100，导航聚焦且 Hero 为空时用）只需看自己的 fanart
    for cid in sorted(home_ids - hero_ids):
        needle = f"!String.IsEmpty(Container({cid}).ListItem.Art(fanart))"
        if needle not in hero:
            fail(f"{HERO_EXPR} 缺少导航聚焦分支的 {needle}")

    # SubItems 必须覆盖：当前条目、文件夹行前一张卡、Emby 封面
    for needle, label in (
        ("!String.IsEmpty(Container.ListItem.Art(fanart))", "当前条目 fanart"),
        ("!String.IsEmpty(Container.ListItemNoWrap(-1).Art(fanart))", "文件夹行的前一张卡"),
        ("Container.ListItem.Property(emby.library.art)", "Emby 库封面"),
        ("String.IsEqual(Container.ListItem.Property(node.type),target_folder)", "文件夹行判据"),
    ):
        if needle in items:
            ok(f"{ITEMS_EXPR} 覆盖 {label}")
        else:
            fail(f"{ITEMS_EXPR} 缺少 {label}（{needle}）")

    for needle, label in (
        ("Home.LastMovieFanart", "Home.LastMovieFanart"),
        ("Home.LastTVShowFanart", "Home.LastTVShowFanart"),
        ("Property(Home.Section),music", "音乐分区背景"),
    ):
        if needle in other:
            ok(f"{OTHER_EXPR} 覆盖 {label}")
        else:
            fail(f"{OTHER_EXPR} 缺少 {label}")

    # Home.xml 必须真的接上三条判据
    for name in (ITEMS_EXPR, HERO_EXPR, OTHER_EXPR):
        ref = f"$EXP[{name}]"
        if ref in home:
            ok(f"Home.xml 引用了 {ref}")
        else:
            fail(f"Home.xml 没有引用 {ref}：判据写了却没人用")

    # 兜底路径如果换了，判据语义要重新确认
    if "special://skin/extras/backgrounds/primary.jpg" in fanart_var:
        ok(f"{FANART_VAR} 的兜底仍是 primary.jpg")
    else:
        warn(f"{FANART_VAR} 的兜底不再是 primary.jpg，确认遮罩语义是否仍然成立")

    print()
    if errors:
        print(f"结果：{checks} 项检查，{len(errors)} 项失败，{len(warnings)} 项提醒")
        return 1
    print(f"结果：{checks} 项检查全部通过，{len(warnings)} 项提醒")
    return 0


if __name__ == "__main__":
    sys.exit(main())
