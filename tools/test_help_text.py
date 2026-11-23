# -*- coding: utf-8 -*-
"""设置页帮助条的文案契约（HANDOVER.md §5.3.1）。

规范原文：
1. 写「怎么选」，不写「这是什么」——一句用途 + 默认值 + 什么情况该改；
2. 一句话说完，不超过 40 字；
3. 引号用 “”（弯双引号），不用「」。

外加 2026-11-23 用户要求：**清掉版本对比**。
「原浓度等于 2.2.0 的观感」「标准为当前观感」这类对用户没有任何信息量，
他要的是「现在这档是什么效果」，不是「跟旧版比怎么样」。版本演进写进 docs，不写进帮助条。
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VARIABLES = ROOT / "xml" / "Variables.xml"
PO = ROOT / "language" / "resource.language.zh_cn" / "strings.po"

MAX_CHARS = 40

# 版本对比词：帮助条里出现即判失败。要写版本演进请写进 docs/。
VERSION_WORDS = ("观感", "旧版", "改版", "以前是", "原来的", "还原到")
VERSION_RE = re.compile(r"\d+\.\d+\.\d+")


def _help_ids():
    """帮助条里行级引用的全部字符串 id（分类级兜底也在同一个变量里）。"""
    text = VARIABLES.read_text(encoding="utf-8")
    block = re.search(
        r'<variable name="SkinSettingsHelpTextVar">(.*?)</variable>', text, re.S
    ).group(1)
    return sorted({int(n) for n in re.findall(r"\$LOCALIZE\[(\d+)\]", block)})


def _strings():
    text = PO.read_text(encoding="utf-8")
    return {
        int(n): s
        for n, s in re.findall(r'msgctxt "#(\d+)"\n(?:msgid ".*?"\n)?msgstr "(.*?)"\n', text)
    }


class HelpTextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ids = _help_ids()
        cls.text = _strings()

    def test_ids_are_not_empty(self):
        self.assertGreater(len(self.ids), 40, "帮助条引用的字符串数量异常")

    def test_all_ids_have_text(self):
        missing = [i for i in self.ids if not self.text.get(i)]
        self.assertEqual(missing, [], "帮助条引用了不存在或为空的字符串")

    def test_length_within_limit(self):
        too_long = {
            i: (len(self.text[i]), self.text[i])
            for i in self.ids
            if len(self.text.get(i, "")) > MAX_CHARS
        }
        self.assertEqual(
            too_long, {}, "帮助条超过 %d 字（写进 docs，别塞帮助条）" % MAX_CHARS
        )

    def test_no_version_comparison(self):
        bad = {}
        for i in self.ids:
            s = self.text.get(i, "")
            hits = [w for w in VERSION_WORDS if w in s]
            if VERSION_RE.search(s):
                hits.append("版本号")
            if hits:
                bad[i] = (hits, s)
        self.assertEqual(bad, {}, "帮助条里不许写版本对比，版本演进写进 docs")

    def test_quotes_are_curly(self):
        bad = {}
        for i in self.ids:
            s = self.text.get(i, "")
            if '"' in s or "「" in s or "」" in s:
                bad[i] = s
        self.assertEqual(bad, {}, "帮助条引号只许用 “”（Kodi 官方中文包同款）")

    def test_no_placeholder_left(self):
        bad = [i for i in self.ids if "TODO" in self.text.get(i, "")]
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
