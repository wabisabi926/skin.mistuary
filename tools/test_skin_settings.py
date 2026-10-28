"""皮肤设置的读写配对检查。

这组用例存在的理由：2026-10-26 的交接把 15 个设置判成"只读、永远停在默认值"，
实际它们全都有写入入口——只是写入用的是 Skin.SelectBool / SetNumeric /
SetPath / SetAddon，而当时的排查只 grep 了 SetString / ToggleSetting。
下面用合成用例把"每种写入内置函数都算写入"钉住，再用真仓库兜底。
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_skin import (  # noqa: E402
    DEFAULT_ONLY_SETTINGS,
    RESET_ONLY_SETTINGS,
    collect_skin_settings,
)

XML_DIR = Path(__file__).resolve().parents[1] / "xml"


class SkinSettingWriteBuiltinsTest(unittest.TestCase):
    def test_selectbool_pairs_count_as_writes(self):
        """SelectBool 是单选互斥，每个 name|setting 对都是写入点。"""
        text = (
            '<onclick>Skin.SelectBool(31024, 38018|circle_userrating, '
            "563|circle_rating, 16018|circle_none)</onclick>"
            "<visible>Skin.HasSetting(circle_rating)</visible>"
        )
        reads, writes = collect_skin_settings([("SkinSettings.xml", text)])
        for key in ("circle_userrating", "circle_rating", "circle_none"):
            self.assertIn(key, writes)
        self.assertIn("circle_rating", reads)

    def test_other_write_builtins_count_as_writes(self):
        text = (
            "<onclick>Skin.SetNumeric(OSDAutoCloseTime)</onclick>"
            "<onclick>Skin.SetPath(library_art_folder)</onclick>"
            "<onclick>Skin.SetAddon(LyricScript_Path,xbmc.python.lyrics)</onclick>"
            "<onclick>Skin.ToggleSetting(nara_cast_open)</onclick>"
            "<onclick>Skin.SetBool(some_flag,false)</onclick>"
            "<onclick>Skin.Reset(Nara.MusicBackground)</onclick>"
        )
        _, writes = collect_skin_settings([("x.xml", text)])
        for key in (
            "OSDAutoCloseTime",
            "library_art_folder",
            "LyricScript_Path",
            "nara_cast_open",
            "some_flag",
            "Nara.MusicBackground",
        ):
            self.assertIn(key, writes, f"{key} 应被识别为写入点")

    def test_read_forms_are_detected(self):
        text = (
            "<visible>Skin.HasSetting(no_fanart)</visible>"
            "<label>$INFO[Skin.String(library_art_folder)]</label>"
            "<visible>Skin.Numeric(OSDAutoCloseTime)</visible>"
        )
        reads, _ = collect_skin_settings([("y.xml", text)])
        for key in ("no_fanart", "library_art_folder", "OSDAutoCloseTime"):
            self.assertIn(key, reads)

    def test_dynamic_setting_name_is_not_truncated(self):
        """Skin.SetBool(home_no_$PARAM[s]_widget) 不能被截成 home_no_。"""
        _, writes = collect_skin_settings(
            [("z.xml", "Skin.SetBool(home_no_$PARAM[section]_$PARAM[widget]_widget)")]
        )
        self.assertEqual({k for k in writes if not k.startswith("$")}, set())

    def test_reset_only_options_are_declared(self):
        """恢复默认选项必须留在白名单里，否则会一直被报成有写无读。"""
        self.assertEqual(RESET_ONLY_SETTINGS, {"circle_none", "OriginalTitleFormat_Default"})


class RepoSkinSettingsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.texts = [
            (p.name, p.read_text(encoding="utf-8", errors="replace"))
            for p in sorted(XML_DIR.glob("*.xml"))
        ]
        cls.reads, cls.writes = collect_skin_settings(cls.texts)

    def test_no_read_only_setting(self):
        """有读取但全仓库没有写入入口 = 永远停在默认值，属于缺陷。"""
        readonly = sorted(set(self.reads) - set(self.writes))
        self.assertEqual(readonly, [], f"这些设置只读，没有写入入口: {readonly}")

    def test_no_orphan_write(self):
        """写入了却没人读 = 功能没接上。

        两类豁免：
        - RESET_ONLY_SETTINGS：只用来"恢复默认"的选项，本来就不需要读；
        - DEFAULT_ONLY_SETTINGS：档位类设置里代表**默认值**的那一档，
          变量用最后一条无条件的 <value> 兜底，所以没有显式的 Skin.HasSetting 读取。
        """
        orphan = sorted(
            set(self.writes) - set(self.reads) - RESET_ONLY_SETTINGS - DEFAULT_ONLY_SETTINGS
        )
        self.assertEqual(orphan, [], f"这些设置写了没人读: {orphan}")


class VideoInfoAutoScrollTest(unittest.TestCase):
    def test_synopsis_textboxes_follow_autoscroll_setting(self):
        """详情页剧情必须受 autoscroll 控制；列表和 PVR 之外最容易漏的就是这里。"""
        hero = (XML_DIR / "Includes_DialogVideoInfo_Hero.xml").read_text(encoding="utf-8")
        binding = '<autoscroll time="3000" delay="7000" repeat="5000">Skin.HasSetting(autoscroll)'
        self.assertEqual(hero.count(binding), 2)


class VideoInfoTechFlagsCaptionTest(unittest.TestCase):
    def test_tvshow_techflags_use_current_season_first_episode(self):
        """剧集页用当前季第一集当代表集，并在行尾标 SxxExx。"""
        hero = (XML_DIR / "Includes_DialogVideoInfo_Hero.xml").read_text(encoding="utf-8")
        variables = (XML_DIR / "Variables.xml").read_text(encoding="utf-8")
        self.assertIn('<param name="technical_item_prefix" value="Container(5101).ListItemAbsolute(0)" />', hero)
        self.assertIn('<param name="technical_visible" value="Integer.IsGreater(Container(5101).NumItems,0)" />', hero)
        self.assertIn('<param name="technical_caption" value="$VAR[NaraRepCaptionVar]" />', hero)
        self.assertIn('<variable name="NaraRepCaptionVar">', variables)
        self.assertIn('代表集 S$VAR[NaraRepSeasonVar]E$VAR[NaraRepEpisodeVar]', variables)
        self.assertIn('<value condition="String.IsEqual(Container(5101).ListItemAbsolute(0).Season,1)">01</value>', variables)
        self.assertIn('<value condition="String.IsEqual(Container(5101).ListItemAbsolute(0).Episode,1)">01</value>', variables)


class SettingsSurfaceTintTest(unittest.TestCase):
    def test_settings_pages_and_osd_dialogs_use_expected_layers(self):
        """设置页=页面档；播放中的设置对话框=播放中档，非播放时回落浮窗档。"""
        variables = (XML_DIR / "Variables.xml").read_text(encoding="utf-8")
        settings = (XML_DIR / "Includes_Settings.xml").read_text(encoding="utf-8")
        settings_dialog = (XML_DIR / "Includes_SettingsDialog.xml").read_text(encoding="utf-8")
        music_audio = (XML_DIR / "Custom_1113_MusicAudioDialog.xml").read_text(encoding="utf-8")
        dialog_select = (XML_DIR / "Includes_DialogSelect.xml").read_text(encoding="utf-8")

        self.assertIn('<variable name="NaraSettingsDialogTintVar">', variables)
        self.assertIn('Player.HasVideo | Player.HasAudio', variables)

        sidebar = settings.split('<include name="NaraSettingsSidebar">', 1)[1].split('</include>', 1)[0]
        self.assertIn('$VAR[NaraGlassPageTintVar]', sidebar)
        self.assertNotIn('$VAR[NaraGlassFloatTintVar]', sidebar)

        hub = settings.split('<include name="NaraSettingsHub">', 1)[1].split(
            '<include content="NaraSettingsHubEntry">', 1)[0]
        self.assertIn('$VAR[NaraGlassPageTintVar]', hub)
        self.assertNotIn('$VAR[NaraGlassFloatTintVar]', hub)

        self.assertEqual(settings_dialog.count('$VAR[NaraSettingsDialogTintVar]'), 2)
        self.assertEqual(music_audio.count('$VAR[NaraSettingsDialogTintVar]'), 2)
        self.assertEqual(dialog_select.count('$VAR[NaraSettingsDialogTintVar]'), 11)


if __name__ == "__main__":
    unittest.main()
