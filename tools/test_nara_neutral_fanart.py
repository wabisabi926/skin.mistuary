"""剧照层亮度的结构性约束（HANDOVER §5.11.1）。

现在分成两类基准，定义在 `colors/defaults.xml`，改亮度只动那两行：

- `fanart_dim` = `FF808080`（×0.50）：无阅读遮罩的共享页 + 媒体库页
- `fanart_dim_reading` = `FFA8A8A8`（×0.66）：自带烘焙阅读遮罩的页
  （首页文件·收藏 / 搜索空查询），以及插件详情里插件自己的 fanart

照片不透明，所以不需要再垫一层中性底，玻璃面板背后照样有明暗层次。

这套契约有四条，破了就会重新出现「某页发紫」或「某页过亮」：
1. 八页只允许这两个 token，同类必须是同一个值（分叉就会按页漂移）；
2. 必须不透明（alpha FF），否则 primary 的蓝紫会透上来；
3. 系数必须是中性（R=G=B），带色偏等于换个方向染色；
4. 不能再引入中性底 / 半透明叠灰这类额外图层。

这些约束 audit_skin.py 发现不了（它不检查 expression），所以用测试锁住。
"""
import re
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

XML = Path(__file__).resolve().parents[1] / 'xml'
COLORS = Path(__file__).resolve().parents[1] / 'colors' / 'defaults.xml'
EXP_ONLY = re.compile(r'^\$EXP\[([A-Za-z0-9_.]+)\]$')
TINT = re.compile(r'^([0-9A-F]{2})([0-9A-F]{2})([0-9A-F]{2})([0-9A-F]{2})$')

# 自带烘焙阅读遮罩的两页，底图系数要更高一档（遮罩会再压暗）
READING_PAGES = {'Home.xml', 'Includes_Search.xml'}


def parse(name):
    return ET.parse(XML / name).getroot()


def colors():
    root = ET.parse(COLORS).getroot()
    return {node.get('name'): (node.text or '').strip() for node in root.iter('color')}


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

    def test_each_page_uses_its_documented_token(self):
        tints = {name: texture.get('colordiffuse') for name, _, texture in self.layers}
        for name, tint in tints.items():
            expected = 'fanart_dim_reading' if name in READING_PAGES else 'fanart_dim'
            self.assertEqual(tint, expected, f'{name} 应使用 {expected}，实际 {tint}')

    def test_tokens_are_neutral_opaque_and_in_range(self):
        palette = colors()
        expected_red = {'fanart_dim': 0x80, 'fanart_dim_reading': 0xA8, 'primary_dim': 0x99}
        for name, red_value in expected_red.items():
            self.assertIn(name, palette, f'colors/defaults.xml 缺少 {name}')
            match = TINT.match(palette[name])
            self.assertIsNotNone(match, f'{name} 不是 8 位十六进制：{palette[name]}')
            # Kodi 的 colordiffuse 是 AARRGGBB，不是 RRGGBBAA —— 写反会变成
            # 「蓝通道满值 + 半透明」，照片立刻发紫（2026-11-05 踩过）。
            alpha, red, green, blue = (int(group, 16) for group in match.groups())
            self.assertEqual(alpha, 0xFF, f'{name} 必须不透明，否则 primary 的蓝紫会透上来')
            self.assertEqual(red, green, f'{name} 必须是中性系数，不能带色偏')
            self.assertEqual(green, blue, f'{name} 必须是中性系数，不能带色偏')
            self.assertEqual(red, red_value, f'{name} 的压暗系数变了')
            self.assertTrue(0x80 <= red <= 0xC0, f'{name} 偏离 0.5~0.75 的约定范围')

    def test_addon_info_plugin_fanart_uses_reading_token(self):
        root = parse('DialogAddonInfo.xml')
        tints = []
        for control in root.iter('control'):
            texture = control.find('texture')
            if texture is None or texture.get('background') != 'true':
                continue
            if (texture.text or '').strip() == '$INFO[ListItem.Art(fanart)]':
                tints.append(texture.get('colordiffuse'))
        self.assertTrue(tints, '插件自己的 fanart 层不见了')
        self.assertEqual(tints, ['fanart_dim_reading'], '插件 fanart 也要压暗，且和遮罩页同一档')

    def test_primary_dim_layers_respect_no_fanart(self):
        layers = []
        for path in sorted(XML.glob('*.xml')):
            for control in parse(path.name).iter('control'):
                texture = control.find('texture')
                if texture is None or texture.get('colordiffuse') != 'primary_dim':
                    continue
                layers.append((path.name, (control.findtext('visible') or '').strip()))
        self.assertTrue(layers, '没有找到 primary_dim 兜底层')
        for name, visible in layers:
            self.assertIn('!Skin.HasSetting(no_fanart)', visible,
                          f'{name} 的 primary_dim 层必须排除 no_fanart（关背景时保持原图）')

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


if __name__ == '__main__':
    unittest.main()
