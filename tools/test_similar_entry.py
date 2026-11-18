# -*- coding: utf-8 -*-
"""详情页「更多 → 相似影片」入口契约。

- 只对库里的 movie/tvshow 出现（DBID>0）；
- 调 helper 的 mode=similar，参数用 DBType/DBID；
- More 弹层从 5 项扩到 6 项，高度/位置同步。
"""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
XML = ROOT / "xml"


class SimilarEntryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.info = (XML / "DialogVideoInfo.xml").read_text(encoding="utf-8")

    def test_more_menu_has_similar_item(self):
        block = self.info.split('id="5199"', 1)[1].split("</content>", 1)[0]
        self.assertIn("$LOCALIZE[31844]", block)
        self.assertIn("mode=similar", block)
        self.assertIn("type=$INFO[ListItem.DBType]", block)
        self.assertIn("dbid=$INFO[ListItem.DBID]", block)

    def test_item_is_limited_to_library_movies_and_tvshows(self):
        block = self.info.split('id="5199"', 1)[1].split("</content>", 1)[0]
        self.assertIn("String.IsEqual(ListItem.DBType,movie)", block)
        self.assertIn("String.IsEqual(ListItem.DBType,tvshow)", block)
        self.assertIn("Integer.IsGreater(ListItem.DBID,0)", block)
        self.assertIn("System.AddonIsEnabled(script.mistuary.helper)", block)

    def test_more_panel_grew_to_six_rows(self):
        self.assertIn("<height>414</height>", self.info)
        self.assertIn("<height>390</height>", self.info)
        self.assertIn("<top>345</top>", self.info)

    def test_string_exists_in_both_languages(self):
        for lang, text in (("zh_cn", "相似影片"), ("en_gb", "Similar titles")):
            with self.subTest(lang=lang):
                po = (ROOT / "language" / ("resource.language.%s" % lang) / "strings.po").read_text(
                    encoding="utf-8")
                self.assertIn('msgctxt "#31844"', po)
                self.assertIn(text, po)


if __name__ == "__main__":
    unittest.main()
