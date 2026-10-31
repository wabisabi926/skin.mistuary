# -*- coding: utf-8 -*-
"""生成首页导航胶囊底板的宽度表（32 种组合 × 中英文 = 64 条）。

背景：导航是一条居中的胶囊，宽度必须等于「当前可见标签的总宽」。Kodi 没有
「控件宽度 = 子项总宽」这种能力，所以只能穷举组合、每条写死一个宽度。

宽度怎么来的（与原来 8 个实测数字逐个吻合，可作为回归基准）：
    每个按钮 width = round(文本宽) + textoffsetx×2(60)
    font_home_tabs = Inter-Unicode-Regular.ttf / 26px
    中文：搜索112 电影112 电视剧138 音乐112 电视112 收藏夹138 文件112
    英文：Search147 Movies149 TV shows182 Music133 TV95 Favourites190 File102
    中文 5 个 = 612 / +音乐 724 / +电视 724 / 都有 836
    英文 5 个 = 770 / +音乐 903 / +电视 865 / 都有 998

用法：
    python tools/gen_home_nav_plates.py          # 重新生成 Home.xml 里的底板块
    python tools/gen_home_nav_plates.py --check   # 只校验是否与生成结果一致

固定显示：电影 / 电视剧 / 文件（用户 2026-10-31 决定，避免组合数爆炸）。
可隐藏：搜索 / 音乐 / 电视 / 收藏夹 → 2^4 = 16 组合 × 中英文 = 32 条底板。
"""
import argparse
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOME = os.path.join(ROOT, "xml", "Home.xml")
FONT = os.path.join(ROOT, "fonts", "Inter-Unicode-Regular.ttf")
SIZE = 26
PADDING = 60          # textoffsetx 30 × 2
BEGIN = "<!-- BEGIN generated: home nav plates"
END = "<!-- END generated: home nav plates -->"
T = "\t"

# 顺序 = 导航条从左到右的顺序
ALWAYS = [("电影", "Movies"), ("电视剧", "TV shows"), ("文件", "File")]
TOGGLE = [
    ("搜索", "Search", "HomeMenuNoSearchButton"),
    ("音乐", "Music", "HomeMenuNoMusicButton"),
    ("电视", "TV", "HomeMenuNoTVButton"),
    ("收藏夹", "Favourites", "HomeMenuNoFavoritesButton"),
]

COMMENT = [
    T * 4 + "<!-- 导航条背景。宽度 = 当前可见标签的总宽。",
    T * 4 + "     固定显示：电影 / 电视剧 / 文件；可隐藏：搜索 / 音乐 / 电视 / 收藏夹 → 16 种组合 × 中英文 = 32 条。",
    T * 4 + "     每个标签的宽度 = 文本宽 + textoffsetx×2(60)，实测（font_home_tabs 26px）：",
    T * 4 + "       中文 搜索112 电影112 电视剧138 音乐112 电视112 收藏夹138 文件112",
    T * 4 + "       英文 Search147 Movies149 TV shows182 Music133 TV95 Favourites190 File102",
    T * 4 + "     中文 5 个 612 / +音乐 724 / +电视 724 / 都有 836；英文 770 / 903 / 865 / 998。",
    T * 4 + "     **这一段由 tools/gen_home_nav_plates.py 生成，不要手改**；",
    T * 4 + "     改标签文字、字号或增删开关后重新跑它（加 check 参数可校验）。",
    T * 4 + "     电影 / 电视剧 / 文件 固定显示（2026-10-31 用户决定），所以组合只有 4 个开关。",
    T * 4 + "     以后想让某个标签也能隐藏：把它从 ALWAYS 挪进 TOGGLE 重跑本脚本即可。",
    T * 4 + "     定位用 centerleft 50%：父 group 已显式给 width 100%，任何分辨率都自动居中。 -->",
]


def measure():
    try:
        from PIL import ImageFont
    except ImportError:
        sys.exit("需要 Pillow：pip install pillow")
    f = ImageFont.truetype(FONT, SIZE)
    zh = {}
    en = {}
    for zh_label, en_label in ALWAYS + [(t[0], t[1]) for t in TOGGLE]:
        zh[zh_label] = int(round(f.getlength(zh_label))) + PADDING
        en[en_label] = int(round(f.getlength(en_label))) + PADDING
    return zh, en


def build():
    zh, en = measure()
    base_zh = sum(zh[z] for z, _ in ALWAYS)
    base_en = sum(en[e] for _, e in ALWAYS)

    rows = []
    for mask in range(1 << len(TOGGLE)):
        hidden = [TOGGLE[i] for i in range(len(TOGGLE)) if mask >> i & 1]
        w_zh = base_zh + sum(zh[t[0]] for t in TOGGLE if t not in hidden)
        w_en = base_en + sum(en[t[1]] for t in TOGGLE if t not in hidden)
        cond = " + ".join(
            ("Skin.HasSetting(%s)" if t in hidden else "!Skin.HasSetting(%s)") % t[2] for t in TOGGLE)
        rows.append((w_zh, w_en, cond, [t[0] for t in hidden]))

    rows.sort(key=lambda r: (-r[0], r[2]))

    out = []
    for w_zh, w_en, cond, hidden in rows:
        tag = "、".join(hidden) if hidden else "全部显示"
        out += [
            T * 4 + "<!-- %s -->" % tag,
            T * 4 + '<control type="image">',
            T * 5 + "<centerleft>50%</centerleft>",
            T * 5 + "<top>20</top>",
            T * 5 + "<width>%d</width>" % w_zh,
            T * 5 + "<height>60</height>",
            T * 5 + '<texture colordiffuse="$VAR[NaraGlassPageTintVar]" border="26">shapes/round26.png</texture>',
            T * 5 + "<visible>String.StartsWith(System.Language,Chinese) + %s</visible>" % cond,
            T * 4 + "</control>",
            T * 4 + '<control type="image">',
            T * 5 + "<centerleft>50%</centerleft>",
            T * 5 + "<top>20</top>",
            T * 5 + "<width>%d</width>" % w_en,
            T * 5 + "<height>60</height>",
            T * 5 + '<texture colordiffuse="$VAR[NaraGlassPageTintVar]" border="26">shapes/round26.png</texture>',
            T * 5 + "<visible>!String.StartsWith(System.Language,Chinese) + %s</visible>" % cond,
            T * 4 + "</control>",
        ]
    return out


def locate(lines):
    start = next((i for i, l in enumerate(lines) if "BEGIN generated: home nav plates" in l), None)
    comment = next((i for i, l in enumerate(lines) if "导航条背景。宽度" in l), None)
    if comment is not None and (start is None or comment < start):
        start = comment
    if start is None:
        sys.exit("找不到导航底板块（既没有 BEGIN 标记，也没有注释行）")
    end = next((i for i, l in enumerate(lines) if END in l), None)
    if end is None:
        end = next(i for i, l in enumerate(lines) if 'id="9000"' in l) - 1
        while lines[end].strip() == "":
            end -= 1
    return start, end


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    raw = io.open(HOME, "r", encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.split(nl)

    start, end = locate(lines)
    block = [T * 4 + BEGIN + " (tools/gen_home_nav_plates.py) -->"] + COMMENT + build() + [T * 4 + END]
    current = lines[start:end + 1]

    if args.check:
        if current == block:
            print("✓ 导航底板与生成结果一致（%d 行）" % len(block))
            return 0
        print("✗ 导航底板与生成结果不一致，跑一次不带 --check 重新生成")
        return 1

    lines[start:end + 1] = block
    io.open(HOME, "w", encoding="utf-8", newline="").write(nl.join(lines))
    print("已重新生成导航底板：%d 行（原 %d 行）" % (len(block), len(current)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
