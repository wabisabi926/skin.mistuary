"""皮肤设置的读写配对检查。

这组用例存在的理由：2026-10-26 的交接把 15 个设置判成"只读、永远停在默认值"，
实际它们全都有写入入口——只是写入用的是 Skin.SelectBool / SetNumeric /
SetPath / SetAddon，而当时的排查只 grep 了 SetString / ToggleSetting。
下面用合成用例把"每种写入内置函数都算写入"钉住，再用真仓库兜底。
"""

import sys
import unittest
import xml.etree.ElementTree as ET
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
        self.assertEqual(
            RESET_ONLY_SETTINGS,
            {"circle_none", "OriginalTitleFormat_Default", "rating_src_auto"},
        )


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


class RatingSourcePrecedenceTest(unittest.TestCase):
    """主评分来源：手选档位必须压过类型自动识别。

    回归理由（2026-10-28 实测）：Emby 插件默认把 `CommunityRating` 补写成 imdb 类型
    （`emby-next-gen` 的 `Set imdb as default rating provider` 默认开），于是
    `Rating(imdb)` 恒等于 `Rating`。自动识别只要排在设置前面，有类型字段的条目就永远
    命中 IMDb，设置 707「主评分来源」怎么切都没反应。
    """

    GUARDS = (
        "!Skin.HasSetting(douban_rating)",
        "!Skin.HasSetting(rating_src_imdb)",
        "!Skin.HasSetting(rating_src_tmdb)",
    )

    @classmethod
    def setUpClass(cls):
        root = ET.parse(XML_DIR / "Includes_DialogVideoInfo_Hero.xml").getroot()
        row = next(i for i in root.iter("include") if i.get("name") == "NaraOnlineRatingsRow")
        items = []
        for inc in row.iter("include"):
            if inc.get("content") != "NaraOnlineRatingItem":
                continue
            params = {p.get("name"): (p.get("value") or "").strip() for p in inc.findall("param")}
            # 主评分的 label 是 Rating，次评分的 label 带类型名
            if params.get("label") == "$INFO[$PARAM[item_prefix].Rating]":
                items.append(params)
        cls.items = items

    def _split(self):
        manual, auto = [], []
        for i, p in enumerate(self.items):
            (auto if all(g in p["visible"] for g in self.GUARDS) else manual).append((i, p))
        return manual, auto

    def test_manual_branches_cover_the_three_sources(self):
        manual, _ = self._split()
        self.assertEqual(
            sorted(p["icon"] for _, p in manual),
            ["flags/ratings/douban.png", "flags/ratings/imdb.png", "flags/ratings/tmdb.png"],
        )

    def test_manual_branches_ignore_rating_types(self):
        manual, _ = self._split()
        for _, p in manual:
            for typed in ("Rating(tmdb)", "Rating(trakt)", "Rating(imdb)"):
                self.assertNotIn(typed, p["visible"], f"手选分支不能依赖 {typed}")

    def test_auto_detect_requires_no_manual_choice(self):
        _, auto = self._split()
        # TMDb / Trakt / IMDb 三条 + 都没匹配上的 TMDb 兜底
        self.assertEqual(len(auto), 4)
        for _, p in auto:
            for guard in self.GUARDS:
                self.assertIn(guard, p["visible"])

    def test_manual_branches_render_before_auto_detect(self):
        manual, auto = self._split()
        self.assertTrue(manual and auto)
        self.assertLess(max(i for i, _ in manual), min(i for i, _ in auto))

    def test_auto_option_can_clear_manual_choice(self):
        """设置 707 必须留一档「自动」，否则选过档位就再也回不到自动识别。"""
        settings = (XML_DIR / "SkinSettings.xml").read_text(encoding="utf-8")
        self.assertIn("31767|rating_src_auto", settings)


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


class SettingsPageGeometryTest(unittest.TestCase):
    """设置中心下的页面共用一套几何（见 docs/skin-contracts.md 第五节）。

    钉住的理由：2026-10-28 给 `NaraSettingsRow` 补 28 的水平偏移时，有人把 `top` 也减了 28、
    `height` 又加了 56（`189/652` → `161/708`），用户配置页的两行设置比 PVR 页高 32px，
    用户一眼看出「四周空隙没对齐」。**28 只在水平方向补。**
    """

    PANEL = {"left": "505", "top": "145", "width": "1355", "height": "740"}
    CONTENT = {"left": "525", "top": "193", "width": "1315", "height": "644"}

    def _root(self, name):
        return ET.parse(XML_DIR / name).getroot()

    @staticmethod
    def _geom(ctrl):
        return {k: (ctrl.findtext(k) or "").strip() for k in ("left", "top", "width", "height")}

    def _find(self, root, ctype, cid=None, width=None):
        for c in root.iter("control"):
            if c.get("type") != ctype:
                continue
            if cid is not None and c.get("id") != cid:
                continue
            if width is not None and (c.findtext("width") or "").strip() != width:
                continue
            return c
        return None

    def test_glass_panel_is_identical_on_every_settings_page(self):
        for name in ("SettingsCategory.xml", "SettingsProfile.xml",
                     "SettingsSystemInfo.xml", "EventLog.xml"):
            panel = self._find(self._root(name), "image", width="1355")
            self.assertIsNotNone(panel, name)
            self.assertEqual(self._geom(panel), self.PANEL, name)

    def test_content_rect_follows_the_pvr_baseline(self):
        # 基准：原生设置分类页（播放器 / 媒体 / 界面 / 网络 / 系统 / PVR 与直播电视）
        cat = self._root("SettingsCategory.xml")
        self.assertEqual(self._geom(self._find(cat, "grouplist", "5")), self.CONTENT)

        # 用户配置：设置行容器带 NaraSettingsRow，横向 525/1315，纵向仍是 193/644
        prof = self._root("SettingsProfile.xml")
        self.assertEqual(self._geom(self._find(prof, "grouplist", "9001")), self.CONTENT)

        # 用户配置：卡片容器没有行 include，直接 553/1259；卡片自带 top 5，188+5=193
        cards = self._geom(self._find(prof, "panel", "2"))
        self.assertEqual((cards["left"], cards["width"]), ("553", "1259"))
        self.assertEqual(int(cards["top"]) + 5, 193)
        self.assertEqual(int(cards["top"]) + int(cards["height"]), 837)

        # 系统信息：纯 label 页，容器 553/1259
        info = self._find(self._root("SettingsSystemInfo.xml"), "grouplist", width="1259")
        self.assertIsNotNone(info)
        self.assertEqual(self._geom(info), {**self.CONTENT, "left": "553", "width": "1259"})

        # 事件日志：列表 525/1315，行内首个控件 left=28 → 视觉落在 553
        log = self._root("EventLog.xml")
        self.assertEqual(self._geom(self._find(log, "fixedlist", "50")), self.CONTENT)

    def test_help_bar_sits_at_the_same_place(self):
        for name in ("SettingsCategory.xml", "SettingsProfile.xml"):
            bar = self._find(self._root(name), "textbox", "6")
            self.assertIsNotNone(bar, name)
            self.assertEqual(self._geom(bar),
                             {"left": "545", "top": "915", "width": "1255", "height": "100"}, name)

    def test_scrollbar_track_matches_the_content_rect(self):
        """轨道高度必须等于**它服务的那个控件**的高度，否则滑块比例是错的。

        三页的列表/分组都是 644 高；`SettingsSystemInfo` 例外——它的滚动条服务的是
        「捐赠页」那个 `textbox id=30`（193→550，高 357），2026-10-29 之前写 644，
        滑块按 644 算比例，看起来永远"还有很多内容"。
        """
        expect = {
            "SettingsCategory.xml": "644",
            "SettingsProfile.xml": "644",
            "SettingsSystemInfo.xml": "357",
            "EventLog.xml": "644",
        }
        for name, height in expect.items():
            bar = self._find(self._root(name), "scrollbar", "60")
            self.assertIsNotNone(bar, name)
            g = self._geom(bar)
            self.assertEqual((g["left"], g["top"], g["width"], g["height"]),
                             ("1874", "193", "8", height), name)


class SelectionBarRoundingTest(unittest.TestCase):
    def test_settings_selection_bars_are_rounded(self):
        """默认/对话框设置行的焦点条必须用圆角，不能用 1x1 的 lists/focus.png。"""
        buttons = (XML_DIR / "Includes_Buttons.xml").read_text(encoding="utf-8")
        for name in ("DefaultSettingButton", "DialogSettingButton"):
            block = buttons.split(f'<include name="{name}">', 1)[1].split('</include>', 1)[0]
            self.assertIn('border="14">shapes/round14.png', block)
            self.assertNotIn('lists/focus.png', block)
        music = (XML_DIR / "Custom_1113_MusicAudioDialog.xml").read_text(encoding="utf-8")
        self.assertEqual(music.count('border="14">shapes/round14.png'), 3)
        self.assertNotIn('round4.png', music)

        osd = (XML_DIR / "Custom_1112_OSDPlaylistDialog.xml").read_text(encoding="utf-8")
        self.assertIn('border="14">shapes/round14.png', osd)
        self.assertNotIn('lists/focus.png', osd)
        metadata = buttons.split('<include name="InfoDialogMetadata">', 1)[1].split('</include>', 1)[0]
        self.assertIn('border="14">shapes/round14.png', metadata)
        self.assertNotIn('lists/focus.png', metadata)

        for name in ("Includes_PVR.xml", "MyPVRChannels.xml", "View_50_List.xml",
                     "Includes.xml", "Includes_DialogSelect.xml", "Includes_Buttons.xml",
                     "Includes_DialogGlass.xml"):
            self.assertNotIn('lists/focus.png', (XML_DIR / name).read_text(encoding="utf-8"), name)
        self.assertIn('border="12">shapes/round12.png',
                      (XML_DIR / "Includes_PVR.xml").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
