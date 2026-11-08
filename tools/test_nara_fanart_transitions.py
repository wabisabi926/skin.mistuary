import re
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET


XML = Path(__file__).resolve().parents[1] / 'xml'
ANIMATIONS = ET.parse(XML / 'Includes_Animations.xml').getroot()
HOME = ET.parse(XML / 'Includes_Home.xml').getroot()
INFO = ET.parse(XML / 'DialogVideoInfo.xml').getroot()
BACKDROP = next(node for node in ET.parse(XML / 'Home.xml').findall('controls/control')
                if node.findtext('texture') == '$VAR[NaraSharedRandomFanartVar]')
EXPRESSIONS = {node.get('name'): node.text for node in HOME.findall('expression')}
SOURCE = ANIMATIONS.find('variable[@name="NaraVideoInfoFanartSourceVar"]')
CAMERA = ANIMATIONS.find('include[@name="Animation_NaraFanartDetail"]/definition/animation')
FOLLOW = INFO.findall('.//control[@id="5900"]/animation[@source]')


def window_id(value):
    return {'home': '10000', 'videos': '10025', 'movieinformation': '12003'}.get(
        value.lower(), value)


class DialogStack:
    def __init__(self, page='home', section='search'):
        self.visible = {window_id(page)}
        self.closing = set()
        self.properties = {('10000', 'Home.Section'): section}
        self.labels = {
            'Skin.String(Nara.SharedRandomFanart.LockedPath)': '',
            'Window(home).Property(Home.SharedRandomFanart.SessionPath)': '',
            'Container(16090).ListItem.Art(fanart)': 'random.jpg',
        }
        self.no_fanart = False
        self.video = False

    def evaluate(self, condition, context='12003'):
        condition = re.sub(r'\$EXP\[([^]]+)\]',
                           lambda m: '[' + EXPRESSIONS[m[1]] + ']', condition)
        condition = re.sub(
            r'String.IsEqual\(Window(?:\(([^)]+)\))?\.Property\(([^)]+)\),([^)]*)\)',
            lambda m: str(self.properties.get((window_id(m[1] or context), m[2]), '') == m[3]),
            condition)
        condition = re.sub(r'Window.IsVisible\(([^)]+)\)',
                           lambda m: str(window_id(m[1]) in self.visible), condition)
        condition = re.sub(r'Window.IsActive\(([^)]+)\)',
                           lambda m: str(window_id(m[1]) in self.visible - self.closing), condition)
        for label, value in self.labels.items():
            condition = condition.replace('String.IsEmpty(' + label + ')', str(not value))
        condition = condition.replace('Skin.HasSetting(no_fanart)', str(self.no_fanart))
        condition = condition.replace('Player.HasVideo', str(self.video))
        condition = condition.replace('Player.HasAudio', 'False').replace('Player.HasGame', 'False')
        condition = re.sub(r'\btrue\b', 'True', condition)
        condition = condition.replace('!', ' not ').replace('+', ' and ').replace('|', ' or ')
        condition = condition.replace('[', '(').replace(']', ')')
        if re.sub(r'True|False|\band\b|\bor\b|\bnot\b|[()\s]', '', condition):
            raise ValueError('Unsupported condition: ' + condition)
        return eval(condition, {'__builtins__': {}}, {})

    def open_info(self, dialog='12003'):
        self.visible.add(dialog)
        source = next(value.text for value in SOURCE
                      if self.evaluate(value.get('condition', 'true'), dialog))
        self.properties[(dialog, 'VideoInfo.FanartSource')] = source
        return source

    def camera_active(self, source):
        condition = CAMERA.get('condition').replace('$PARAM[source]', source)
        condition = condition.replace('$PARAM[enabled]', '!Player.HasVideo' if source == 'library' else 'true')
        return self.evaluate(condition)

    def follow(self, dialog='12003'):
        return [(node.get('sourcewindow'), node.get('source')) for node in FOLLOW
                if self.evaluate(node.get('condition'), dialog)]


class FanartTransitionsTest(unittest.TestCase):
    def test_favorites_backdrop_is_retained_and_revealed_when_closing_starts(self):
        animation = BACKDROP.find('animation[.="Conditional"]')
        self.assertIsNotNone(animation)
        self.assertEqual((animation.get('effect'), animation.get('start'),
                          animation.get('end'), animation.get('time')), ('fade', '100', '0', '0'))
        for source in DialogStack().labels:
            with self.subTest(source=source):
                stack = DialogStack(section='favorites')
                stack.labels = {label: 'random.jpg' if label == source else ''
                                for label in stack.labels}
                for state, transparent in [('closed', False), ('open', True),
                                           ('closing', False), ('closed', False)]:
                    if state == 'closed':
                        stack.visible.discard('12003')
                        stack.closing.clear()
                    elif state == 'open':
                        stack.open_info()
                    else:
                        stack.closing.add('12003')
                    self.assertTrue(stack.evaluate(BACKDROP.findtext('visible')))
                    self.assertEqual(stack.evaluate(animation.get('condition')), transparent)

    def test_backdrop_handoff_does_not_change_other_home_sections(self):
        animation = BACKDROP.find('animation[.="Conditional"]')
        for section in ('movies', 'tvshows', 'search', 'files'):
            for state in ('closed', 'open', 'closing'):
                with self.subTest(section=section, state=state):
                    stack = DialogStack(section=section)
                    if state != 'closed':
                        stack.open_info()
                    if state == 'closing':
                        stack.closing.add('12003')
                    self.assertFalse(stack.evaluate(animation.get('condition')))
                    self.assertEqual(stack.evaluate(BACKDROP.findtext('visible')),
                                     section == 'files' and state == 'closed')

    def test_search_only_zooms_for_detail_and_holds_through_closing_fade(self):
        stack = DialogStack()
        self.assertFalse(stack.camera_active('search'))
        self.assertEqual(stack.open_info(), 'search')
        self.assertTrue(stack.camera_active('search'))
        # A closing dialog remains visible until its exit animation completes.
        self.assertIn('12003', stack.visible)
        self.assertTrue(stack.camera_active('search'))
        stack.visible.remove('12003')
        self.assertFalse(stack.camera_active('search'))
        stack.open_info()
        self.assertTrue(stack.camera_active('search'))

    def test_collection_owns_the_camera_above_home_or_library(self):
        for page in ('home', 'videos'):
            with self.subTest(page=page):
                stack = DialogStack(page, 'movies')
                stack.visible.add('11111')
                self.assertFalse(stack.camera_active('movieset'))
                self.assertEqual(stack.open_info(), 'movieset')
                self.assertTrue(stack.camera_active('movieset'))
                self.assertFalse(stack.camera_active('library'))
                stack.visible.remove('12003')
                self.assertFalse(stack.camera_active('movieset'))

    def test_nested_info_does_not_reassign_the_underlying_detail_camera(self):
        stack = DialogStack(section='movies')
        self.assertEqual(stack.open_info(), 'home')
        stack.visible.add('11111')
        self.assertFalse(stack.camera_active('movieset'))
        self.assertEqual(stack.open_info('12016'), 'movieset')
        self.assertTrue(stack.camera_active('movieset'))
        stack.visible.remove('12016')
        self.assertFalse(stack.camera_active('movieset'))

    def test_video_and_disabled_fanart_do_not_zoom_library_background(self):
        stack = DialogStack(page='videos')
        self.assertEqual(stack.open_info(), 'library')
        self.assertTrue(stack.camera_active('library'))
        stack.video = True
        self.assertFalse(stack.camera_active('library'))
        stack.video = False
        stack.no_fanart = True
        self.assertFalse(stack.camera_active('library'))

    def test_fork_only_follow_animation_is_not_used(self):
        # 通用版移除了魔改内核的 Follow 动画，镜头改由 VideoInfo.FanartSource 驱动。
        self.assertEqual(FOLLOW, [])

    def test_detail_fanart_uses_black_backing_and_left_shade(self):
        """详情页背景：满屏清晰图 + 左侧黑渐变，不再 150% 放大（2026-11-08 改）。

        2026-11-07 是外层 group 的 100→150 放大（HANDOVER §5.11.2）。现在改成
        「黑底 + 满屏清晰图 + 25% 左缘渐隐」，构图对齐 fuse3 的 flixart：
        人物回到 100%，左侧从纯黑里浮出来，不需要真模糊。
        这里锁三条契约：
        1. 5900 自己不挂 animation；
        2. 5900 之前有一层铺满屏幕的纯黑底；
        3. 5900 之后有一条 25% 宽的 flixart-shade 遮罩，且同样受 no_fanart 控制。
        """
        image = INFO.find('.//control[@id="5900"]')
        self.assertIsNotNone(image, '详情页背景层 id=5900 不见了')
        self.assertEqual(image.findall('animation'), [], '5900 自己不该再挂动画')
        self.assertEqual((image.findtext('left') or '').strip(), '33.33%',
                         '清晰图应从屏幕 1/3 处开始（右上 2/3）')
        self.assertEqual((image.findtext('top') or '').strip(), '0')
        self.assertEqual((image.findtext('width') or '').strip(), '66.67%',
                         '清晰图宽度应为屏幕 2/3')
        self.assertEqual((image.findtext('height') or '').strip(), '100%')
        aspect = image.find('aspectratio')
        self.assertEqual(aspect.get('aligny'), 'top', '贴顶，多出来的高度交给底部渐变')
        self.assertEqual((aspect.text or '').strip(), 'keep',
                         '必须 keep：框是 4:3，scale 会裁左边并留下亮竖条')

        group = next(control for control in INFO.iter('control')
                     if control.find('control[@id="5900"]') is not None)
        children = group.findall('control')
        index = next(i for i, child in enumerate(children) if child.get('id') == '5900')

        blacks = [c for c in children[:index]
                  if (c.findtext('texture') or '').strip() == 'colors/black.png']
        self.assertTrue(blacks, '5900 之前应有一层纯黑底')
        self.assertEqual((blacks[-1].findtext('include') or '').strip(), 'FullScreenDimensions',
                         '黑底必须铺满屏幕，不能写死 1920')

        shades = [c for c in children[index + 1:]
                  if (c.findtext('texture') or '').strip() == 'overlays/flixart-shade.png']
        self.assertTrue(shades, '5900 之后应有左缘渐隐遮罩')
        shade = shades[0]
        self.assertEqual((shade.findtext('width') or '').strip(), '20%', '遮罩宽度应为图宽的 30%')
        self.assertEqual((shade.findtext('aspectratio') or '').strip(), 'stretch',
                         '遮罩必须拉伸铺满，否则渐变会按贴图原始比例排版')
        self.assertIn('no_fanart', shade.findtext('visible') or '',
                      '遮罩也要受 no_fanart 控制')

        bottoms = [c for c in children[index + 1:]
                   if (c.findtext('texture') or '').strip() == 'overlays/flixart-bottom.png']
        self.assertTrue(bottoms, '5900 之后应有底部渐变，否则图片下缘是硬切线')

        zooms = [node for node in group.findall('animation') if node.get('effect') == 'zoom']
        self.assertEqual(zooms, [], '详情页背景不再做 150% 放大')

    def test_home_fanart_uses_black_backing_and_left_shade(self):
        """首页：黑底 + 右上 2/3 清晰图 + 左缘遮罩，且 zoom 必须挂在包住两者的 group 上。

        聚焦动画（Animation_NaraFanartFocus，100→104）只放大图片、不放大遮罩的话，
        图片左缘会向左溢出，遮罩盖不到，就会在聚焦状态下露出一条竖边。
        """
        root = ET.parse(XML / 'Home.xml').getroot()
        image = root.find('.//control[@id="9090"]')
        self.assertIsNotNone(image, '首页背景 9090 不见了')
        self.assertEqual((image.findtext('left') or '').strip(), '33.33%',
                         '首页清晰图也应在右上 2/3')
        self.assertEqual((image.findtext('top') or '').strip(), '0')
        self.assertEqual((image.findtext('width') or '').strip(), '66.67%')
        self.assertEqual((image.findtext('height') or '').strip(), '100%')
        self.assertEqual(image.find('aspectratio').get('aligny'), 'top')
        self.assertEqual((image.find('aspectratio').text or '').strip(), 'keep')

        wrapper = next(c for c in root.iter('control')
                       if c.find('control[@id="9090"]') is not None)
        focus = [i for i in wrapper.findall('include')
                 if (i.get('content') or '') == 'Animation_NaraFanartFocus']
        self.assertEqual(len(focus), 1,
                         '聚焦 zoom 必须挂在包住 9090 和遮罩的 group 上；只放图片会让聚焦时左缘溢出')
        self.assertEqual([i for i in image.findall('include')
                          if (i.get('content') or '') == 'Animation_NaraFanartFocus'], [],
                         '聚焦 zoom 不该还留在 9090 自己身上')

        shades = [c for c in wrapper.findall('control')
                  if (c.findtext('texture') or '').strip() == 'overlays/flixart-shade.png']
        self.assertTrue(shades, 'group 里应有左缘遮罩')
        self.assertEqual((shades[0].findtext('width') or '').strip(), '20%')

        all_controls = list(root.iter('control'))
        self.assertTrue([c for c in all_controls
                         if (c.findtext('texture') or '').strip() == 'colors/black.png'],
                        '缺少纯黑底')
        self.assertTrue([c for c in all_controls
                         if (c.findtext('texture') or '').strip() == 'overlays/flixart-bottom.png'],
                        '缺少底部渐变')

        zooms150 = [node for node in root.iter('animation') if node.get('end') == '150,150']
        self.assertEqual(zooms150, [], '首页不再做 150% 放大')


if __name__ == '__main__':
    unittest.main()
