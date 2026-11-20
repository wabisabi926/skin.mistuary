# -*- coding: utf-8 -*-
"""首页两行续播 / 电影·电视剧页 Hero 布局的契约。

锁 2026-11-18 最终形态：
- 导航默认落在「首页」(9018)，两行分别是电影/剧集续播；
- 电影/电视剧页隐藏续播行，媒体库行与首页剧集行同一 y（spacer 818）；
- 电影/电视剧页 Hero 下移 200，内部间距 215/282；首页 Hero 保持 202/258；
- 背景轮播源必须是带 fanart 的续播电影，不再是库 tag；
- 不再使用魔改内核的 ListItemSettled。
"""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
XML = ROOT / "xml"


def read(name):
    return (XML / name).read_text(encoding="utf-8")


class HomeLibrariesPageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home = read("Home.xml")
        cls.includes = read("Includes_Home.xml")
        cls.variables = read("Variables.xml")

    def test_default_focus_is_home_tab(self):
        self.assertIn(
            '<onload condition="String.IsEmpty(Window(home).Property(Home.Section))">SetFocus(9018)</onload>',
            self.home,
        )
        self.assertIn('<control type="togglebutton" id="9018">', self.home)
        self.assertIn('<label>$LOCALIZE[31769]</label>', self.home)

    def test_two_continue_watching_rows(self):
        self.assertIn('<param name="list_id" value="18010"/>', self.home)
        self.assertIn('<param name="list_id" value="18012"/>', self.home)
        self.assertEqual(self.home.count('<param name="rail_visible" value="false"/>'), 2)

    def test_rotation_uses_in_progress_movies(self):
        start = self.home.index('id="18011"')
        end = self.home.index('<!-- 第一行', start)
        block = self.home[start:end]
        self.assertIn(
            'special://skin/extras/playlists/home_inprogress_movies.xsp', block)
        self.assertIn('no_home_fanart_rotation', block)
        # 轮播分支必须先于静态兜底
        fanart = self.variables.split('name="HomeFanartVar"', 1)[1].split('</variable>', 1)[0]
        first_18011 = fanart.find('Container(18011).ListItem.Art(fanart)')
        first_18010 = fanart.find('Container(18010).ListItemAbsolute(0).Art(fanart)')
        self.assertGreater(first_18011, -1)
        self.assertGreater(first_18010, first_18011)

    def test_no_settled_infolabel(self):
        for name in ("Home.xml", "Includes_Home.xml", "Variables.xml"):
            with self.subTest(file=name):
                self.assertNotIn("ListItemSettled", read(name))

    def test_hero_layout_b(self):
        # include 默认值：首页用 202/258
        self.assertIn('<param name="ratings_top">202</param>', self.includes)
        self.assertIn('<param name="plot_top">258</param>', self.includes)
        self.assertIn('<top>$PARAM[ratings_top]</top>', self.includes)
        self.assertIn('<top>$PARAM[plot_top]</top>', self.includes)
        # 电影/电视剧页 11 个 Hero：200 / 215 / 271（2026-11-20 简介上移 11px，评分行→简介间距 56 对齐首页）
        self.assertEqual(self.home.count('<param name="hero_top" value="200"/>'), 11)
        self.assertEqual(self.home.count('<param name="ratings_top" value="215"/>'), 11)
        self.assertEqual(self.home.count('<param name="plot_top" value="271"/>'), 11)
        self.assertEqual(self.home.count('<param name="hero_top" value="0"/>'), 2)
        # 媒体库行与首页「正在观看的电视剧」同高（spacer 818）
        for sid in ("5002001", "6002001"):
            with self.subTest(spacer=sid):
                block = self.home.split('value="%s"' % sid, 1)[1].split("</include>", 1)[0]
                self.assertIn('<param name="height" value="818"/>', block)

    def test_music_album_grid_option_a(self):
        card = self.includes.split('<include name="HomeWidgetAlbumCard">', 1)[1]
        card = card.split('<include name="WidgetListSquare">', 1)[0]
        self.assertIn('<width>222</width>', card)
        self.assertIn('<height>222</height>', card)
        self.assertIn('mask_222x222_r9.png', card)
        self.assertIn('ring_card_224x224_r10.png', card)
        self.assertIn('<top>226</top>', card)
        self.assertIn('<top>228</top>', card)
        self.assertIn('<top>260</top>', card)

        square = self.includes.split('<include name="WidgetListSquare">', 1)[1]
        square = square.split('<include name="WidgetListCategories">', 1)[0]
        self.assertIn('<right>70</right>', square)
        self.assertIn('<itemlayout width="258" height="290">', square)
        self.assertIn('<focusedlayout width="258" height="290">', square)

    def test_music_categories_scaled_down(self):
        # 音乐页 7 张类别卡等比缩小，其他页走默认尺寸
        home = self.home
        for token in ('<param name="item_width" value="262"/>',
                      '<param name="card_width" value="200"/>',
                      '<param name="card_mask" value="shapes/mask_200x116_r9.png"/>'):
            self.assertIn(token, home)
        # 音乐 grouplist 内联 itemgap 20（三行完整、第4行随机专辑出屏）；共享 include 默认仍 -160
        self.assertIn('<itemgap>-160</itemgap>', self.includes)
        music = self.home.split('<control type="grouplist" id="7001">', 1)[1]
        music = music.split('<pagecontrol>7010</pagecontrol>', 1)[0]
        self.assertIn('<itemgap>28</itemgap>', music)

    def test_hidden_rail_does_not_leave_trailing_spacer(self):
        self.assertIn(
            '$PARAM[rail_visible] + $PARAM[media_row_visible]', self.includes)
        self.assertIn(
            '$PARAM[rail_visible] + ![$PARAM[media_row_visible]]', self.includes)

    def test_home_hero_falls_back_to_tv_only(self):
        # 18012 在 property 为空且电影行也空时也要显示
        self.assertIn(
            'String.IsEmpty(Window(home).Property(Home.LibHero)) + !Integer.IsGreater(Container(18010).NumItems,0)',
            self.home)
        # 18010 在剧集行变空时重新接管
        self.assertIn(
            '!Integer.IsGreater(Container(18012).NumItems,0)] + Integer.IsGreater(Container(18010).NumItems,0)',
            self.home)

    def test_nav_and_back(self):
        self.assertIn(
            '<ondown condition="!Integer.IsGreater(Container(18010).NumItems,0) + Integer.IsGreater(Container(18012).NumItems,0)">18012</ondown>',
            self.home)
        nav = self.includes.split('<include name="HomeLibNavigation">', 1)[1].split('</include>', 1)[0]
        self.assertIn('<onback>9000</onback>', nav)
        self.assertIn('Container($PARAM[list_id]).Position(0)', nav)

    def test_empty_state_waits_for_loading(self):
        self.assertIn(
            '!Container(18010).IsUpdating + !Integer.IsGreater(Container(18012).NumItems,0) + !Container(18012).IsUpdating',
            self.home)

    def test_empty_state_distinguishes_local_library(self):
        self.assertIn(
            '!Library.HasContent(movies) + !Library.HasContent(tvshows)',
            self.home)
        self.assertIn(
            'Library.HasContent(movies) | Library.HasContent(tvshows)',
            self.home)
        self.assertIn('$LOCALIZE[31849]', self.home)
        for cid in (31835, 31836, 31849):
            for lang in ("zh_cn", "en_gb"):
                with self.subTest(id=cid, lang=lang):
                    po = (ROOT / "language" / ("resource.language.%s" % lang) / "strings.po").read_text(
                        encoding="utf-8")
                    self.assertIn('msgctxt "#%d"' % cid, po)

    def test_fanart_fallbacks(self):
        fanart = self.variables.split('name="HomeFanartVar"', 1)[1].split('</variable>', 1)[0]
        self.assertIn('Container.ListItem.Art(landscape)', fanart)
        self.assertNotIn('Container.ListItem.Art(thumb)', fanart)
        self.assertIn('Container(5200).ListItem.Art(fanart)', self.variables)
        self.assertIn('Container(6200).ListItem.Art(fanart)', self.variables)
        self.assertIn('Container(18012).ListItemAbsolute(0).Art(fanart)', self.variables)
        self.assertNotIn('emby.library.art', self.variables)


if __name__ == "__main__":
    unittest.main()
