"""剧照层亮度的结构性约束（HANDOVER §5.11.1）。

primary.jpg 的平均色偏蓝紫（约 63,77,110），让剧照半透明叠上去会被染成紫灰。
现在八页统一用**乘法压暗**：`colordiffuse="FFA8A8A8"` —— RGB 乘 0.66、alpha 保持不透明。
照片不透明，所以不需要再垫一层中性底，玻璃面板背后照样有明暗层次。

这套契约有三条，破了就会重新出现「某页发紫」或「某页过亮」：
1. 八页的剧照层必须是同一个乘法系数（分叉就会按页漂移）；
2. 必须不透明（alpha FF），否则 primary 的蓝紫会透上来；
3. 不能再引入中性底 / 半透明叠灰这类额外图层。

这些约束 audit_skin.py 发现不了（它不检查 expression），所以用测试锁住。
"""
import re
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

XML = Path(__file__).resolve().parents[1] / 'xml'
EXP_ONLY = re.compile(r'^\$EXP\[([A-Za-z0-9_.]+)\]$')
TINT = re.compile(r'^([0-9A-F]{2})([0-9A-F]{2})([0-9A-F]{2})([0-9A-F]{2})$')


def parse(name):
    return ET.parse(XML / name).getroot()


def all_expressions():
    found = {}
    for path in sorted(XML.glob('*.xml')):
        for node in parse(path.name).iter('expression'):
            found[node.get('name')] = (node.text or '').strip()
    return found


def fanart_layers():
    """剧照层：background="true" 且纹理是共享随机剧照变量（不是固定路径）。"""
    layers = []
    for path in sorted(XML.glob('*.xml')):
        for control in parse(path.name).iter('control'):
            texture = control.find('texture')
            if texture is None or texture.get('background') != 'true':
                continue
            var = (texture.text or '').strip()
            if 'RandomFanartVar' not in var:
                continue
            layers.append((path.name, control, texture))
    return layers


class FanartDimTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layers = fanart_layers()
        cls.expressions = all_expressions()

    def test_fanart_layer_count_is_eight(self):
        where = sorted(name for name, _, _ in self.layers)
        self.assertEqual(len(self.layers), 8, where)
        self.assertEqual(where, ['DialogAddonInfo.xml', 'DialogAddonSettings.xml',
                                 'DialogMediaSource.xml', 'FileBrowser.xml',
                                 'FileManager.xml', 'Home.xml',
                                 'Includes_Search.xml', 'Includes_Settings.xml'])

    def test_all_four_share_one_multiplier(self):
        tints = {name: texture.get('colordiffuse') for name, _, texture in self.layers}
        self.assertEqual(len(set(tints.values())), 1, tints)
        tint = next(iter(tints.values()))
        match = TINT.match(tint or '')
        self.assertIsNotNone(match, f'colordiffuse 不是 8 位十六进制：{tint}')
        # Kodi 的 colordiffuse 是 AARRGGBB，不是 RRGGBBAA —— 写反会变成
        # 「蓝通道满值 + 半透明」，照片立刻发紫（2026-11-05 踩过）。
        alpha, red, green, blue = (int(group, 16) for group in match.groups())
        self.assertEqual(alpha, 0xFF, '剧照必须不透明，否则 primary 的蓝紫会透上来')
        self.assertEqual(red, green, '乘法压暗必须是中性系数，不能带色偏')
        self.assertEqual(green, blue)
        self.assertTrue(0x80 <= red <= 0xC0, f'压暗系数 {red:#04x} 偏离 0.5~0.75 的约定范围')

    def test_no_neutral_base_layer_returns(self):
        for path in sorted(XML.glob('*.xml')):
            text = (XML / path.name).read_text(encoding='utf-8')
            self.assertNotIn('NaraNeutralFanartBase', text,
                             f'{path.name} 又引入了中性底：乘法压暗后它只会多画一层')

    def test_fanart_visibility_still_uses_named_expressions(self):
        for name, control, _ in self.layers:
            with self.subTest(file=name):
                visible = (control.findtext('visible') or '').strip()
                match = EXP_ONLY.match(visible)
                self.assertIsNotNone(match, f'{name} 的剧照层应直接用 $EXP[...]：{visible}')
                self.assertIn(match.group(1), self.expressions,
                              f'表达式 {match.group(1)} 没有定义')

    def test_music_section_skips_the_reading_zone(self):
        # 音乐背景图本身亮度约 73，再叠遮罩和三条渐变只是白花 4 层。
        home = (XML / 'Home.xml').read_text(encoding='utf-8')
        self.assertIn('!String.IsEqual(Window(home).Property(Home.Section),music)', home)


if __name__ == '__main__':
    unittest.main()
