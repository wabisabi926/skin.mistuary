# -*- coding: utf-8 -*-
"""影视背景统一契约（2026-11-19）。

- 清晰图统一 scale：铺满裁切，不是拉伸，也不再用 keep 留左侧色光条；
- 满屏背景只吃宽图：fanart → landscape；竖版 thumb 只给卡片；
- 首页色光层必须有源图护栏，helper 保留上一张时不会只剩色光；
- 详情 / View_51 的 fanart 与 landscape 都参与背景和色光。
"""

import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
XML = ROOT / "xml"


def _root(name):
    return ET.parse(XML / name).getroot()


def _controls(name):
    return list(_root(name).iter("control"))


def _texture(control):
    return (control.findtext("texture") or "").strip()


class BackgroundStyleTest(unittest.TestCase):
    def test_detail_clear_art_is_scale_and_uses_funnel(self):
        control = next(c for c in _controls("DialogVideoInfo.xml") if c.get("id") == "5900")
        self.assertEqual((control.findtext("aspectratio") or "").strip(), "scale")
        self.assertIn("$VAR[VideoInfoArtVar]", _texture(control))
        visible = control.findtext("visible") or ""
        self.assertIn("ListItem.Art(fanart)", visible)
        self.assertIn("ListItem.Art(landscape)", visible)

    def test_view51_clear_art_is_scale_and_uses_funnel(self):
        control = next(c for c in _controls("View_51_Poster.xml")
                       if "$VAR[NaraWallArtVar]" in _texture(c))
        self.assertEqual((control.findtext("aspectratio") or "").strip(), "scale")
        visible = control.findtext("visible") or ""
        self.assertIn("Container(51).ListItem.Art(fanart)", visible)
        self.assertIn("Container(51).ListItem.Art(landscape)", visible)

    def test_primary_only_when_both_wide_art_missing(self):
        for name, prefix in (("DialogVideoInfo.xml", "ListItem"),
                             ("View_51_Poster.xml", "Container(51).ListItem")):
            with self.subTest(page=name):
                primaries = [c for c in _controls(name)
                             if "primary.jpg" in _texture(c)
                             and "!Skin.HasSetting(no_fanart)" in (c.findtext("visible") or "")]
                self.assertTrue(primaries)
                for primary in primaries:
                    visible = primary.findtext("visible") or ""
                    self.assertIn("%s.Art(fanart)" % prefix, visible)
                    self.assertIn("%s.Art(landscape)" % prefix, visible)
                    self.assertIn("String.IsEmpty", visible)

    def test_detail_and_view51_glow_accept_landscape(self):
        for name, prefix in (("DialogVideoInfo.xml", "ListItem"),
                             ("View_51_Poster.xml", "Container(51).ListItem")):
            with self.subTest(page=name):
                glow = [c for c in _controls(name)
                        if "Mistuary.FanartGlow" in _texture(c)]
                self.assertTrue(glow)
                for control in glow:
                    visible = control.findtext("visible") or ""
                    self.assertIn("%s.Art(landscape)" % prefix, visible)

    def test_home_glow_has_source_guard(self):
        glow = [c for c in _controls("Home.xml")
                if "Mistuary.FanartGlow" in _texture(c)]
        self.assertEqual(len(glow), 2)
        for control in glow:
            self.assertIn("Control.GetLabel(9099)", control.findtext("visible") or "")

    def test_home_funnel_is_wide_only(self):
        variables = (XML / "Variables.xml").read_text(encoding="utf-8")
        block = variables.split('name="HomeFanartVar"', 1)[1].split("</variable>", 1)[0]
        self.assertIn("Container.ListItem.Art(landscape)", block)
        self.assertNotIn("Container.ListItem.Art(thumb)", block)
        for name in ("VideoInfoArtVar", "NaraWallArtVar"):
            self.assertIn('name="%s"' % name, variables)

    def test_home_nav_falls_back_to_default_hero(self):
        variables = (XML / "Variables.xml").read_text(encoding="utf-8")
        block = variables.split('name="HomeFanartVar"', 1)[1].split("</variable>", 1)[0]
        self.assertIn("Control.HasFocus(9012)", block)
        self.assertIn("Container(5200).ListItem.Art(fanart)", block)
        self.assertIn("Control.HasFocus(9013)", block)
        self.assertIn("Container(6200).ListItem.Art(fanart)", block)


if __name__ == "__main__":
    unittest.main()
