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
        self.assertEqual(RESET_ONLY_SETTINGS, {"circle_none", "OriginalTitleFormat_Default"})

    def test_default_only_options_are_declared(self):
        """默认档位没有显式读取，必须留在 DEFAULT_ONLY 白名单里。"""
        self.assertEqual(DEFAULT_ONLY_SETTINGS, {"rating_src_tmdb"})


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
    """主评分来源：四档（TMDb / IMDb / 豆瓣 / 自动）显式互斥。

    回归理由：E4K fork 会把 `CommunityRating` 归到具体类型（tmdb/imdb/trakt/douban），
    皮肤优先读类型评分；官方 E4K 只有 `default`，读不到类型时退回 `ListItem.Rating`。
    手选三档仍然显式互斥，自动识别必须选「自动」才跑；TMDb 档同时是「都没选」时的兜底。
    """

    AUTO_GUARD = "Skin.HasSetting(rating_src_auto)"

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
            visible = p["visible"]
            # 手动 TMDb 兜底写的是 !Skin.HasSetting(rating_src_auto)，
            # 不能只按子串判断，否则会被误分进自动组。
            is_auto = self.AUTO_GUARD in visible and f"!{self.AUTO_GUARD}" not in visible
            (auto if is_auto else manual).append((i, p))
        return manual, auto

    def test_manual_branches_cover_the_three_sources(self):
        manual, _ = self._split()
        self.assertEqual(
            sorted(p["icon"] for _, p in manual),
            ["flags/ratings/douban.png", "flags/ratings/imdb.png", "flags/ratings/tmdb.png"],
        )

    def test_manual_branches_prefer_typed_ratings(self):
        """手选档位优先读对应类型；类型为空才退回 ListItem.Rating（官方 E4K 只有 default）。

        手选组的 label 都是 `$INFO[...,Rating]`（兜底分支），因此这里检查它们同时带
        “类型为空”和“默认值非空”两个判据；类型存在时由同源的 typed 分支接手。
        """
        manual, _ = self._split()
        for _, p in manual:
            self.assertIn("String.IsEmpty($PARAM[item_prefix].Rating", p["visible"])
            self.assertIn("!String.IsEmpty($PARAM[item_prefix].Rating)", p["visible"])

    def test_auto_branches_require_explicit_auto(self):
        _, auto = self._split()
        # TMDb / themoviedb / Trakt / IMDb / 豆瓣 五条 + 类型都匹配不上时的中性兜底
        self.assertEqual(len(auto), 6)
        for _, p in auto:
            self.assertIn(self.AUTO_GUARD, p["visible"])
            self.assertNotIn(f"!{self.AUTO_GUARD}", p["visible"])

    def test_manual_branches_render_before_auto_detect(self):
        manual, auto = self._split()
        self.assertTrue(manual and auto)
        self.assertLess(max(i for i, _ in manual), min(i for i, _ in auto))

    def test_auto_option_can_clear_manual_choice(self):
        """设置 707 必须留一档「自动」，否则选过档位就再也回不到自动识别。"""
        settings = (XML_DIR / "SkinSettings.xml").read_text(encoding="utf-8")
        self.assertIn("|rating_src_auto", settings)


class IncludeParamDefinitionTest(unittest.TestCase):
    """定义里带 <param> 的 include 必须有 <definition>，否则 Kodi 会整条丢弃。"""

    def test_param_includes_have_definition(self):
        bad = []
        for path in sorted(XML_DIR.glob("*.xml")):
            root = ET.parse(path).getroot()
            for inc in root.iter("include"):
                if inc.get("name") and inc.find("param") is not None and inc.find("definition") is None:
                    bad.append("%s:%s" % (path.name, inc.get("name")))
        self.assertEqual(bad, [], "带 param 却没有 definition 的 include: %s" % bad)


class SecondaryDoubanToggleTest(unittest.TestCase):
    """详情页豆瓣次评分（设置 715）：开关，默认开；不再有来源四档。"""

    def test_setting_is_toggle(self):
        settings = (XML_DIR / "SkinSettings.xml").read_text(encoding="utf-8")
        row = settings.split('id="715"', 1)[1].split("</control>", 1)[0]
        self.assertIn("Skin.ToggleSetting(hide_sec_douban)", row)
        self.assertIn("<selected>!Skin.HasSetting(hide_sec_douban)</selected>", row)
        for old in ("rating_sec_auto", "rating_sec_douban", "rating_sec_rt", "rating_sec_off"):
            self.assertNotIn(old, row)

    def test_douban_branch_respects_toggle(self):
        hero = (XML_DIR / "Includes_DialogVideoInfo_Hero.xml").read_text(encoding="utf-8")
        douban = hero.split("次评分：豆瓣", 1)[1].split("<!-- 可选元数据", 1)[0]
        self.assertIn("Window.IsVisible(12003)", douban)
        self.assertIn("!Skin.HasSetting(hide_sec_douban)", douban)
        self.assertIn("!Skin.HasSetting(douban_rating)", douban)

    def test_rotten_tomatoes_secondary_removed(self):
        """次评分只剩豆瓣；烂番茄不再占第二颗。"""
        hero = (XML_DIR / "Includes_DialogVideoInfo_Hero.xml").read_text(encoding="utf-8")
        self.assertNotIn("rtfresh.png", hero)
        self.assertNotIn("次评分 ②：烂番茄", hero)


class VideoInfoAutoScrollTest(unittest.TestCase):
    def test_synopsis_textboxes_follow_autoscroll_setting(self):
        """详情页剧情必须受 autoscroll 控制；列表和 PVR 之外最容易漏的就是这里。"""
        hero = (XML_DIR / "Includes_DialogVideoInfo_Hero.xml").read_text(encoding="utf-8")
        binding = '<autoscroll time="3000" delay="7000" repeat="5000">Skin.HasSetting(autoscroll)'
        self.assertEqual(hero.count(binding), 2)


class VideoInfoTechFlagsCaptionTest(unittest.TestCase):
    def test_tvshow_techflags_use_current_season_first_episode(self):
        """剧集页用当前季第一集当代表集，并在行尾标 SxxExx。

        2026-10-29：行尾只留集号，不再写「代表集」三个字 —— 这一行的宽度上限
        是剧情简介的 790，三个字要 81px，加上集号后两个评分时直接超 133px。
        """
        hero = (XML_DIR / "Includes_DialogVideoInfo_Hero.xml").read_text(encoding="utf-8")
        variables = (XML_DIR / "Variables.xml").read_text(encoding="utf-8")
        self.assertIn('<param name="technical_item_prefix" value="Container(5101).ListItemAbsolute(0)" />', hero)
        self.assertIn('<param name="technical_visible" value="Integer.IsGreater(Container(5101).NumItems,0)" />', hero)
        self.assertIn('<param name="technical_caption" value="$VAR[NaraRepCaptionVar]" />', hero)
        self.assertIn('<variable name="NaraRepCaptionVar">', variables)
        self.assertIn('>S$VAR[NaraRepSeasonVar]E$VAR[NaraRepEpisodeVar]<', variables)
        self.assertIn('<value condition="String.IsEqual(Container(5101).ListItemAbsolute(0).Season,1)">01</value>', variables)
        self.assertIn('<value condition="String.IsEqual(Container(5101).ListItemAbsolute(0).Episode,1)">01</value>', variables)

    def test_ratings_row_never_wider_than_the_synopsis(self):
        """评分 + 技术标识那一行的宽度必须和剧情简介一致（790）。

        这一行和简介左右对齐，宽了就会顶到简介右边界外。790 下
        「两个评分 + 5 个标识 + 集号」= 757，还剩 33px。
        """
        hero = (XML_DIR / "Includes_DialogVideoInfo_Hero.xml").read_text(encoding="utf-8")
        root = ET.fromstring(hero)
        for inc in root.iter("include"):
            if inc.get("name") != "NaraOnlineRatingsRow":
                continue
            widths = {p.get("name"): (p.text or "").strip() for p in inc.findall("param")}
            self.assertEqual(widths.get("width"), "790")
            break
        else:
            self.fail("没找到 NaraOnlineRatingsRow")
        # 简介正文的宽度也是 790，两处必须一致
        self.assertGreaterEqual(hero.count("<width>790</width>"), 2)


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
    # 内容矩形的**位置**是跨页契约（525/193/1315）；**高度**不是——
    # 它必须是各页「整行高度」的整数倍，否则最后一行会被容器底边切断、露出半截文字
    # （2026-11-13 用户报的就是这个：644 = 78×8.25，第 9 行只露出文字上半截）。
    CONTENT = {"left": "525", "top": "193", "width": "1315", "height": "644"}
    # 行高与行间距：NaraSettingsRow 默认 76 + itemgap 2
    ROW = 76
    GAP = 2
    # fixedlist 的 itemlayout 高 76，无 itemgap
    PLAIN_ROW = 76

    def _assert_whole_rows(self, geom, row, gap, name):
        """容器高度必须正好装下整数行，否则底部会切出半截。

        n 行占 `n*row + (n-1)*gap`，所以判据是 `(height + gap) % (row + gap) == 0`。
        例：76 + 2 的行，8 行 = 622，(622+2) % 78 = 0。
        """
        height = int(geom["height"])
        self.assertEqual((height + gap) % (row + gap), 0,
                         f"{name}: 高度 {height} 装不下整数行（行高 {row} + 间距 {gap}），"
                         f"最后一行会被切断")
        self.assertGreaterEqual(height, row, f"{name}: 高度 {height} 装不下一行")

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
        # 位置契约：525/193/1315（跨页一致）；高度按各自行高取整行
        cat = self._geom(self._find(self._root("SettingsCategory.xml"), "grouplist", "5"))
        self.assertEqual((cat["left"], cat["top"], cat["width"]), ("525", "193", "1315"))
        self._assert_whole_rows(cat, self.ROW, self.GAP, "SettingsCategory.xml")

        # 用户配置：设置行容器带 NaraSettingsRow，横向 525/1315，纵向仍是 193
        prof = self._root("SettingsProfile.xml")
        rows = self._geom(self._find(prof, "grouplist", "9001"))
        self.assertEqual((rows["left"], rows["top"], rows["width"]), ("525", "193", "1315"))
        self._assert_whole_rows(rows, self.ROW, self.GAP, "SettingsProfile.xml")

        # 用户配置：卡片容器没有行 include，直接 553/1259；卡片自带 top 5，188+5=193
        cards = self._geom(self._find(prof, "panel", "2"))
        self.assertEqual((cards["left"], cards["width"]), ("553", "1259"))
        self.assertEqual(int(cards["top"]) + 5, 193)
        self.assertEqual(int(cards["top"]) + int(cards["height"]), 837)

        # 系统信息：纯 label 页，容器 553/1259（没有"行"的概念，保持 644）
        info = self._find(self._root("SettingsSystemInfo.xml"), "grouplist", width="1259")
        self.assertIsNotNone(info)
        self.assertEqual(self._geom(info), {**self.CONTENT, "left": "553", "width": "1259"})

        # 事件日志：列表 525/1315，行内首个控件 left=28 → 视觉落在 553
        log = self._geom(self._find(self._root("EventLog.xml"), "fixedlist", "50"))
        self.assertEqual((log["left"], log["top"], log["width"]), ("525", "193", "1315"))
        self._assert_whole_rows(log, self.PLAIN_ROW, 0, "EventLog.xml")

    def test_help_bar_sits_at_the_same_place(self):
        for name in ("SettingsCategory.xml", "SettingsProfile.xml"):
            bar = self._find(self._root(name), "textbox", "6")
            self.assertIsNotNone(bar, name)
            self.assertEqual(self._geom(bar),
                             {"left": "545", "top": "915", "width": "1255", "height": "100"}, name)

    def test_scrollbar_track_matches_the_content_rect(self):
        """轨道高度必须等于**它服务的那个控件**的高度，否则滑块比例是错的。

        设置分类页 / 用户配置页：8 整行 = 622（76+2）；事件日志：8 整行 = 608（行高 76、无间距）。
        `SettingsSystemInfo` 例外——它的滚动条服务的是「捐赠页」那个 `textbox id=30`
        （193→550，高 357），2026-10-29 之前写 644，滑块按 644 算比例，看起来永远"还有很多内容"。
        """
        expect = {
            "SettingsCategory.xml": "622",
            "SettingsProfile.xml": "622",
            "SettingsSystemInfo.xml": "357",
            "EventLog.xml": "608",
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
