"""海报卡状态图标：图标形状和着色必须一一对应。

背景（2026-10-30）：`StatusIconColorVar` 第一版只覆盖了剧集/季/系列，
电影已看完走的是 `ItemStatusIconVar` 最后那条 `Playcount > 0` → `$INFO[ListItem.Overlay]`，
于是"图标是绿色对勾的样子、颜色却是白的"。这个测试锁住两者的一致性。
"""

import unittest
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
VARIABLES = ROOT / 'xml' / 'Variables.xml'


def load_variable(root, name):
    for node in root.iter('variable'):
        if node.get('name') == name:
            return node
    raise AssertionError('variable %s not found' % name)


def values(node):
    return [(v.get('condition'), (v.text or '').strip()) for v in node.findall('value')]


class StatusIconTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ElementTree.parse(VARIABLES).getroot()

    def test_green_covers_every_watched_branch(self):
        """产出 OverlayWatched 的每个分支，都要有对应的 status_done。"""
        colors = values(load_variable(self.root, 'StatusIconColorVar'))
        done = [c for c, v in colors if v == 'status_done']
        self.assertTrue(done, 'StatusIconColorVar 没有任何 status_done 分支')

        # 剧集/季：WatchedEpisodes == TotalEpisodes
        self.assertTrue(any('WatchedEpisodes' in c and 'tvshow' in c for c in done))
        # 电影系列：Watched == Total
        self.assertTrue(any('Property(Watched)' in c and 'set' in c for c in done))
        # 电影 / 单集 / 音乐电视：Playcount > 0（走 $INFO[ListItem.Overlay] 那条）
        movie = [c for c in done if 'Integer.IsGreater(ListItem.Playcount,0)' in c]
        self.assertTrue(movie, '电影已看完没有 status_done 分支——这就是漏改的那种情况')
        for dbtype in ('movie', 'episode', 'musicvideo'):
            self.assertIn('DBType,%s' % dbtype, movie[0])

    def test_movie_branch_excludes_resume_and_playing(self):
        """继续观看 / 正在播放的图标不是对勾，不能上绿。"""
        colors = values(load_variable(self.root, 'StatusIconColorVar'))
        movie = [c for c, v in colors
                 if v == 'status_done' and 'Integer.IsGreater(ListItem.Playcount,0)' in c][0]
        self.assertIn('!ListItem.IsResumable', movie)
        self.assertIn('!ListItem.IsPlaying', movie)

    def test_fallback_is_white(self):
        colors = values(load_variable(self.root, 'StatusIconColorVar'))
        self.assertIsNone(colors[-1][0], '最后一条必须是无条件兜底')
        self.assertEqual(colors[-1][1], 'badge_foreground')

    def test_every_status_icon_is_coloured(self):
        """所有渲染状态图标的地方都必须接 colordiffuse，否则变量改了也不生效。

        漏一处就会出现"同一个电影，海报墙里绿、首页行里白"。
        """
        plain, coloured = [], []
        for path in sorted((ROOT / 'xml').glob('*.xml')):
            for tex in ElementTree.parse(path).getroot().iter('texture'):
                if '$VAR[ItemStatusIconVar]' not in (tex.text or ''):
                    continue
                if tex.get('colordiffuse') == '$VAR[StatusIconColorVar]':
                    coloured.append(path.name)
                else:
                    plain.append(path.name)
        self.assertEqual(plain, [], '这些地方的状态图标没有接着色变量：%s' % plain)
        self.assertEqual(len(coloured), 6,
                         '状态图标应共有 6 处（海报墙卡 / 缩略面板 / 列表 / 首页 x2 / 共用海报卡布局），实际 %d 处' % len(coloured))


if __name__ == '__main__':
    unittest.main()
