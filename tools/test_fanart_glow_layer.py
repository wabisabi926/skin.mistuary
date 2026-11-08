"""色光底层序与兜底约束。

锁死 2026-11-08 定的结构：fanart_void 黑底 → 色光 → 清晰剧照 → 左缘渐隐
→ 底部渐变。色光层必须「属性为空就整层消失」，保证 helper 没装/没更新/
PIL 缺失时自动退回原来的纯黑，不出现色块。
"""

import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
XML = ROOT / 'xml'
GLOW = 'Mistuary.FanartGlow'
PAGES = ('Home.xml', 'DialogVideoInfo.xml', 'View_51_Poster.xml')


def _root(name):
    return ET.parse(XML / name).getroot()


def _controls(name):
    return list(_root(name).iter('control'))


def _glow_layers(name):
    return [c for c in _controls(name)
            if GLOW in (c.findtext('texture') or '')]


def _text(node):
    return ' '.join(node.itertext()) if node is not None else ''


def _texture_attr(node, key):
    texture = node.find('texture')
    return (texture.get(key) or '') if texture is not None else ''


class LayerOrderTests(unittest.TestCase):
    def test_exactly_one_glow_layer_on_each_of_three_pages(self):
        for name in PAGES:
            with self.subTest(page=name):
                self.assertEqual(len(_glow_layers(name)), 1)

    def test_glow_sits_between_black_backing_and_clear_fanart(self):
        for name in PAGES:
            with self.subTest(page=name):
                nodes = _controls(name)
                void = [i for i, c in enumerate(nodes)
                        if _texture_attr(c, 'colordiffuse') == 'fanart_void']
                glow = [i for i, c in enumerate(nodes)
                        if GLOW in (c.findtext('texture') or '')]
                # 只认「右上 2/3」那一层：View_51 文件开头还有一层旧的
                # fanart_dim 共享剧照，primary 兜底和渐隐层的 visible 里也有
                # Art(fanart)，都不能算清晰图。
                clear = [i for i, c in enumerate(nodes)
                         if (c.findtext('left') or '').strip() == '33.33%'
                         and ('Art(fanart)' in (c.findtext('texture') or '')
                              or 'HomeFanartVar' in (c.findtext('imagepath') or ''))]
                self.assertTrue(void, '找不到黑底层')
                self.assertTrue(glow, '找不到色光层')
                self.assertTrue(clear, '找不到清晰剧照层')
                self.assertLess(void[0], glow[0], '色光必须盖在黑底之上')
                self.assertLess(glow[0], clear[0], '色光必须在清晰图之下')

    def test_home_glow_is_outside_the_focus_zoom_group(self):
        """清晰图聚焦时会 zoom；色光跟着缩放会让边缘闪一下。"""
        root = _root('Home.xml')
        parent = {child: p for p in root.iter() for child in p}
        nodes = list(root.iter('control'))
        glow = next(c for c in nodes if GLOW in (c.findtext('texture') or ''))
        clear = next(c for c in nodes if c.get('id') == '9090')
        self.assertNotEqual(parent[glow].get('type'), 'group')
        self.assertEqual(parent[clear].get('type'), 'group')

    def test_glow_stretches_full_screen(self):
        for name in PAGES:
            with self.subTest(page=name):
                layer = _glow_layers(name)[0]
                self.assertEqual((layer.findtext('aspectratio') or '').strip(),
                                 'scale')


class FallbackTests(unittest.TestCase):
    def test_glow_hides_when_property_is_empty(self):
        """helper 旧版 / 关掉开关 / 无剧照 → 属性为空 → 整层消失露纯黑。"""
        for name in PAGES:
            with self.subTest(page=name):
                visible = _glow_layers(name)[0].findtext('visible') or ''
                self.assertIn('!String.IsEmpty(Window(home).Property(%s))' % GLOW,
                              visible)

    def test_no_fanart_setting_disables_glow(self):
        for name in PAGES:
            with self.subTest(page=name):
                visible = _glow_layers(name)[0].findtext('visible') or ''
                self.assertIn('!Skin.HasSetting(no_fanart)', visible)

    def test_glow_never_uses_primary_fallback_image(self):
        for name in PAGES:
            with self.subTest(page=name):
                self.assertNotIn('primary.jpg', _text(_glow_layers(name)[0]))

    def test_clear_fanart_two_thirds_layout_unchanged(self):
        """色光是新插的一层，不改变已递交的 2/3 清晰图构图。"""
        for name in PAGES:
            with self.subTest(page=name):
                nodes = _controls(name)
                clear = [c for c in nodes
                         if (c.findtext('left') or '').strip() == '33.33%'
                         and (c.findtext('width') or '').strip() == '66.67%']
                self.assertTrue(clear, '%s 的右上 2/3 清晰图不见了' % name)


class ScopeTests(unittest.TestCase):
    def test_only_the_three_video_pages_carry_glow(self):
        """音乐页 / View_50 / View_501 一律不动。"""
        touched = sorted(p.name for p in XML.glob('*.xml')
                         if GLOW in p.read_text(encoding='utf-8'))
        self.assertEqual(touched, sorted(PAGES))

    def test_source_labels_are_unique_and_match_clear_fanart(self):
        expected = {
            'Home.xml': ('9099', '$VAR[HomeFanartVar]'),
            'DialogVideoInfo.xml': ('9098', '$INFO[ListItem.Art(fanart)]'),
            'View_51_Poster.xml': ('9097', '$INFO[Container(51).ListItem.Art(fanart)]'),
        }
        used = set()
        for name, (cid, label) in expected.items():
            with self.subTest(page=name):
                matches = [c for c in _controls(name) if c.get('id') == cid]
                self.assertEqual(len(matches), 1)
                self.assertEqual((matches[0].findtext('label') or '').strip(), label)
                self.assertNotIn(cid, used)
                used.add(cid)
                # 屏幕外 1x1，不能写 visible=false（隐藏控件可能不求值 label）
                self.assertIsNone(matches[0].find('visible'))

    def test_settings_toggle_routes_to_helper(self):
        settings = (XML / 'SkinSettings.xml').read_text(encoding='utf-8')
        self.assertIn('action=toggle_setting,key=fanart_glow', settings)
        self.assertIn('Mistuary.Helper.FanartGlow', settings)

    def test_localised_string_exists_in_both_languages(self):
        for lang in ('resource.language.zh_cn', 'resource.language.en_gb'):
            with self.subTest(lang=lang):
                po = (ROOT / 'language' / lang / 'strings.po').read_text(
                    encoding='utf-8')
                self.assertIn('msgctxt "#31824"', po)

    def test_no_tmdbhelper_dependency_added(self):
        addon = (ROOT / 'addon.xml').read_text(encoding='utf-8')
        self.assertNotIn('plugin.video.themoviedb.helper', addon)
        self.assertIn('script.mistuary.helper', addon)


if __name__ == '__main__':
    unittest.main()
