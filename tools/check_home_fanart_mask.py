"""首页背景遮罩的静态一致性检查（2026-11-06 统一规则）。

规则：首页所有非搜索分区（电影 / 电视剧 / 音乐 / 电视 / 文件 / 收藏）都叠
同一张烘焙阅读区遮罩，不再区分「真剧照 / primary 兜底 / 音乐背景」。
搜索分区有自己的背景栈（Includes_Search.xml 的 NaraSearchBackground），不在这里重复；
`no_fanart` 打开时两张遮罩都不显示。

守四条：
1. 遮罩组的可见条件排除 search、但不排除 music；
2. hero 遮罩排除文件 / 收藏，list 遮罩只用于文件 / 收藏；
3. 两张遮罩都受 no_fanart 控制；
4. HomeFanartVar 的兜底仍是 primary.jpg。

用法：
    python tools/check_home_fanart_mask.py
    python tools/check_home_fanart_mask.py --check

退出码：0 = 一致；1 = 有缺漏或写法退化。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
XML = ROOT / "xml"

errors: list[str] = []
checks = 0


def check(cond: bool, msg: str) -> None:
    global checks
    checks += 1
    if cond:
        print(f"[OK]   {msg}")
    else:
        errors.append(msg)
        print(f"[FAIL] {msg}")


def read(name: str) -> str:
    return (XML / name).read_text(encoding="utf-8")


def control_visible(text: str, needle: str) -> str | None:
    """取包含指定贴图的那个 image 控件里的 <visible>。"""
    m = re.search(
        r'<control type="image">((?:(?!</control>).)*?%s(?:(?!</control>).)*?)</control>'
        % re.escape(needle),
        text,
        re.S,
    )
    if not m:
        return None
    v = re.search(r"<visible>(.*?)</visible>", m.group(1), re.S)
    return v.group(1).strip() if v else ""


def main() -> int:
    parser = argparse.ArgumentParser(description="首页背景遮罩一致性检查")
    parser.add_argument("--check", action="store_true", help="显式检查模式（默认即检查）")
    parser.parse_args()

    home = read("Home.xml")
    variables = read("Variables.xml")

    # 遮罩组：紧邻 hero overlay 之前那个 group 的 visible
    m = re.search(
        r'<control type="group">\s*<visible>(.*?)</visible>.*?fanart-overlay-hero\.png',
        home,
        re.S,
    )
    group_visible = m.group(1).strip() if m else ""
    check(bool(group_visible), "Home.xml 找到遮罩组")
    check("Home.Section),search" in group_visible, "遮罩组排除 search（搜索栈自带遮罩）")
    check("Home.Section),music" not in group_visible, "遮罩组不再排除 music")

    hero_visible = control_visible(home, "overlays/fanart-overlay-hero.png")
    list_visible = control_visible(home, "overlays/fanart-overlay-list.png")

    check(hero_visible is not None, "找到 hero 遮罩控件")
    check(list_visible is not None, "找到 list 遮罩控件")
    check(bool(hero_visible) and "no_fanart" in hero_visible, "hero 遮罩受 no_fanart 控制")
    check(bool(list_visible) and "no_fanart" in list_visible, "list 遮罩受 no_fanart 控制")
    check(
        bool(hero_visible)
        and "Home.Section),files" in hero_visible
        and "Home.Section),favorites" in hero_visible,
        "hero 遮罩排除文件 / 收藏",
    )
    check(
        bool(list_visible)
        and "Home.Section),files" in list_visible
        and "Home.Section),favorites" in list_visible,
        "list 遮罩只用于文件 / 收藏",
    )

    fanart_var = re.search(
        r'<variable name="HomeFanartVar">(.*?)</variable>', variables, re.S
    )
    check(
        bool(fanart_var) and "special://skin/extras/backgrounds/primary.jpg" in fanart_var.group(1),
        "HomeFanartVar 的兜底仍是 primary.jpg",
    )

    print()
    if errors:
        print(f"结果：{checks} 项检查，{len(errors)} 项失败")
        return 1
    print(f"结果：{checks} 项检查全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
