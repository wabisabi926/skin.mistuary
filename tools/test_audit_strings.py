"""字符串引用识别（$LOCALIZE + Skin.SelectBool）。

这组用例存在的理由：2026-10-30 清理"未引用皮肤字符串"时，只扫了 `$LOCALIZE[n]`，
把 5 条**正在使用**的字符串删掉了 —— 它们是通过 `Skin.SelectBool` 引用的：

    <onclick>Skin.SelectBool(31730, 31723|glass_page_op_1, ...)</onclick>
    <onclick>Skin.SelectBool(31733, 31767|rating_src_auto, 31764|rating_src_tmdb, ...)</onclick>

第一个参数是**头部标签的字符串 id**，`数字|设置名` 里的数字是**选项标签的字符串 id**，
两者都不走 `$LOCALIZE`。下面把这两种形态钉住，再用真仓库兜底。
"""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_skin import LOC_REF, string_refs  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
XML_DIR = ROOT / "xml"
LANG_DIR = ROOT / "language"


class StringRefsTest(unittest.TestCase):
    def test_localize_is_detected(self):
        self.assertEqual(string_refs("<label>$LOCALIZE[31782]</label>"), {"31782"})

    def test_selectbool_header_id_is_detected(self):
        """SelectBool 第一个参数是头部标签的字符串 id。"""
        text = '<onclick>Skin.SelectBool(31730, 31723|glass_page_op_1)</onclick>'
        self.assertIn("31730", string_refs(text))

    def test_selectbool_pair_ids_are_detected(self):
        """`数字|设置名` 里的数字是选项标签的字符串 id。"""
        text = (
            "<onclick>Skin.SelectBool(31733, 31767|rating_src_auto, "
            "31764|rating_src_tmdb, 31766|rating_src_imdb)</onclick>"
        )
        refs = string_refs(text)
        for expected in ("31733", "31767", "31764", "31766"):
            self.assertIn(expected, refs)

    def test_setting_name_digits_are_not_ids(self):
        """设置名里的数字（glass_page_op_1）不能当成字符串 id。"""
        text = "<onclick>Skin.SelectBool(31730, 31723|glass_page_op_1)</onclick>"
        self.assertEqual(string_refs(text), {"31730", "31723"})

    def test_mixed_forms_in_one_file(self):
        text = (
            "<label>$LOCALIZE[31001]</label>\n"
            "<onclick>Skin.SelectBool(31002, 31003|a, 31004|b)</onclick>"
        )
        self.assertEqual(string_refs(text), {"31001", "31002", "31003", "31004"})


class RepoStringRefsTest(unittest.TestCase):
    """真仓库兜底：皮肤字符串不许出现"定义了没人引用"或"引用了没定义"。"""

    @classmethod
    def setUpClass(cls):
        cls.texts = [
            p.read_text(encoding="utf-8", errors="replace") for p in sorted(XML_DIR.glob("*.xml"))
        ]
        cls.refs = set()
        for t in cls.texts:
            cls.refs |= string_refs(t)
        cls.skin = set()
        for po in LANG_DIR.glob("*/strings.po"):
            for line in po.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.startswith("msgctxt"):
                    sid = line.split('"')[1].lstrip("#")
                    if sid.startswith("31"):
                        cls.skin.add(sid)

    def test_no_unreferenced_skin_string(self):
        """定义了但 $LOCALIZE 和 SelectBool 都没引用 —— 说明该删了。"""
        dead = sorted(self.skin - self.refs)
        self.assertEqual(dead, [], f"未引用的皮肤字符串：{dead}")

    def test_no_dangling_skin_string_reference(self):
        """引用了 31000-31999 区间、但 po 里没有 —— 会显示成空。"""
        missing = sorted(
            r for r in self.refs
            if r.isdigit() and 31000 <= int(r) < 32000 and r not in self.skin
        )
        self.assertEqual(missing, [], f"缺失的皮肤字符串：{missing}")

    def test_two_language_files_match(self):
        """中英两个 po 的 id 集合必须一致，否则切换语言会缺串。"""
        sets = {}
        for po in LANG_DIR.glob("*/strings.po"):
            ids = {
                line.split('"')[1].lstrip("#")
                for line in po.read_text(encoding="utf-8", errors="replace").splitlines()
                if line.startswith("msgctxt")
            }
            sets[po.parent.name] = ids
        self.assertEqual(len(set(map(frozenset, sets.values()))), 1,
                         f"语言文件 id 不一致：{ {k: len(v) for k, v in sets.items()} }")


if __name__ == "__main__":
    unittest.main()
