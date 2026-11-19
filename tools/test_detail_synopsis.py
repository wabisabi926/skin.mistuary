# -*- coding: utf-8 -*-
"""详情页动作栏：按上键直接打开完整简介（Kodi 官方 TextViewer 1102）。"""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
XML = ROOT / "xml"
BUTTONS = ("5000", "5001", "5006", "5004", "5005", "5003", "5107")


def read(name):
    return (XML / name).read_text(encoding="utf-8")


class DetailSynopsisTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.actions = read("Includes_DialogVideoInfo_Actions.xml")
        cls.include = cls.actions.split(
            '<include name="VideoInfoOpenSynopsis">', 1)[1].split("</include>", 1)[0]

    def test_include_sets_header_and_full_plot(self):
        self.assertIn("SetProperty(TextViewer_Header,$LOCALIZE[207],home)", self.include)
        self.assertIn("SetProperty(TextViewer_Text,$ESCVAR[VideoInfoPlotVar],home)", self.include)
        self.assertIn("ActivateWindow(1102)", self.include)

    def test_every_action_button_opens_synopsis_on_up(self):
        for button_id in BUTTONS:
            with self.subTest(button=button_id):
                block = self.actions.split('id="%s"' % button_id, 1)[1].split("</control>", 1)[0]
                self.assertIn("<include>VideoInfoOpenSynopsis</include>", block)
                self.assertNotIn("<onup>138</onup>", block)


if __name__ == "__main__":
    unittest.main()
