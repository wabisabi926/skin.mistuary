# -*- coding: utf-8 -*-
"""收藏夹封面回退：没有海报/缩略图时，先用条目自己的 Icon，最后才用星标。"""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
XML = ROOT / "xml"


def read(name):
    return (XML / name).read_text(encoding="utf-8")


class FavouritesArtFallbackTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home = read("Home.xml")
        cls.info_wall = read("View_54_InfoWall.xml")

    def _landscape_layout(self, tag):
        return self.home.split('<%s width="347"' % tag, 1)[1].split("</%s>" % tag, 1)[0]

    def test_home_landscape_cards_use_icon_before_star(self):
        for tag in ("itemlayout", "focusedlayout"):
            with self.subTest(layout=tag):
                block = self._landscape_layout(tag)
                self.assertIn("$INFO[ListItem.Icon]", block)
                self.assertIn(
                    "String.IsEmpty(ListItem.Art(landscape))", block)
                self.assertIn(
                    "String.IsEmpty(ListItem.Art(fanart))", block)
                self.assertIn("String.Contains(ListItem.Art(thumb),noimage)", block)
                self.assertIn("!String.IsEmpty(ListItem.Icon)", block)
                # 星标垫底，Icon 在它上面；自定义封面仍在最上层
                star = block.index("$VAR[NaraImgListItemIconDefDefaultFavourites]")
                icon = block.index("$INFO[ListItem.Icon]")
                custom = block.index("Skin.String(favorites_art_folder)")
                self.assertLess(star, icon)
                self.assertLess(icon, custom)

    def test_info_wall_favourite_layout_uses_icon_before_star(self):
        block = self.info_wall.split(
            '<include name="InfoWallFavouriteLayout">', 1)[1].split("</include>", 1)[0]
        self.assertIn("$INFO[ListItem.Icon]", block)
        self.assertIn("String.IsEmpty(ListItem.Art(poster))", block)
        self.assertIn("String.IsEmpty(ListItem.Thumb)", block)
        self.assertIn("String.Contains(ListItem.Thumb,noimage)", block)
        self.assertIn("!String.IsEmpty(ListItem.Icon)", block)
        star = block.index("$VAR[NaraImgListItemIconDefDefaultFavourites]")
        icon = block.index("$INFO[ListItem.Icon]")
        custom = block.index("Skin.String(favorites_art_folder)")
        self.assertLess(star, icon)
        self.assertLess(icon, custom)


if __name__ == "__main__":
    unittest.main()
