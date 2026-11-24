# -*- coding: utf-8 -*-
"""详情页多版本面板契约。

- 版本按钮 5004 不再直接弹原生对话框，而是进 5215 继电器 -> 5211 面板；
- 列表内容走官方节点 videodb://movies/titles/<DBID>/1/；
- 卡片只显示源文件信息，管理按钮仍保留原生 SendClick(14) 兜底；
- 只用官方 K22 属性，不引入魔改的 cornerradius/glass 标签。
"""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
XML = ROOT / "xml"


class VersionsPanelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.versions = (XML / "Includes_DialogVideoInfo_Versions.xml").read_text(encoding="utf-8")
        cls.info = (XML / "DialogVideoInfo.xml").read_text(encoding="utf-8")
        cls.actions = (XML / "Includes_DialogVideoInfo_Actions.xml").read_text(encoding="utf-8")

    def test_picker_is_loaded_and_invoked(self):
        self.assertIn('Includes_DialogVideoInfo_Versions.xml', (XML / "Includes.xml").read_text(encoding="utf-8"))
        self.assertIn("<include>VideoInfoVersionPicker</include>", self.info)

    def test_versions_button_opens_picker_relay(self):
        block = self.actions.split('<control type="button" id="5004">', 1)[1].split("</control>", 1)[0]
        self.assertIn("<onclick>SetFocus(5215)</onclick>", block)
        self.assertNotIn("<onclick>SendClick(14)</onclick>", block)

    def test_list_uses_official_versions_node(self):
        self.assertIn("videodb://movies/titles/$INFO[ListItem.DBID]/1/", self.versions)
        self.assertIn("<onclick>Action(Play)</onclick>", self.versions)
        self.assertIn("<onclick>SendClick(14)</onclick>", self.versions)

    def test_panel_ids_and_relays(self):
        for cid in ("5210", "5211", "5212", "5213", "5214", "5215", "5216"):
            with self.subTest(id=cid):
                self.assertIn('id="%s"' % cid, self.versions)
        self.assertIn("SetProperty(VideoInfo.Versions,true,home)", self.versions)
        self.assertIn("ClearProperty(VideoInfo.Versions,home)", self.versions)
        self.assertIn("AlarmClock(VideoInfoVersionsFocus,SetFocus(5212),00:00,silent)", self.versions)

    def test_dialog_clears_versions_state(self):
        self.assertIn("<onload>ClearProperty(VideoInfo.Versions,home)</onload>", self.info)
        self.assertIn("<onunload>CancelAlarm(VideoInfoVersionsFocus,true)</onunload>", self.info)
        self.assertIn("<onunload>ClearProperty(VideoInfo.Versions,home)</onunload>", self.info)

    def test_no_kernel_only_attributes(self):
        for bad in ("cornerradius=", "material=\"glass\"", "glassstyle=", "<texturebackground>"):
            with self.subTest(attr=bad):
                self.assertNotIn(bad, self.versions)

    def test_strings_exist(self):
        for cid, zh, en in ((31845, "选择版本", "Select version"),
                            (31846, "管理版本", "Manage versions"),
                            (31847, "当前", "Current"),
                            (31848, "无可用版本", "No versions available")):
            with self.subTest(id=cid):
                po_zh = (ROOT / "language" / "resource.language.zh_cn" / "strings.po").read_text(encoding="utf-8")
                po_en = (ROOT / "language" / "resource.language.en_gb" / "strings.po").read_text(encoding="utf-8")
                self.assertIn('msgctxt "#%d"' % cid, po_zh)
                self.assertIn(zh, po_zh)
                self.assertIn(en, po_en)


if __name__ == "__main__":
    unittest.main()
