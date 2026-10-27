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

    def test_standalone_entry_queues_zoom_before_onload_captures_source(self):
        animation = INFO.find('.//control[@id="5900"]/animation[.="WindowOpen"]')
        for page, section, expected in [('home', 'files', True), ('home', 'search', False),
                                        ('home', 'movies', False), ('videos', 'movies', False)]:
            with self.subTest(page=page, section=section):
                stack = DialogStack(page, section)
                self.assertEqual(stack.evaluate(animation.get('condition')), expected)
                self.assertEqual(stack.open_info() == 'fallback', expected)
        stack = DialogStack(section='files')
        stack.visible.add('11111')
        self.assertFalse(stack.evaluate(animation.get('condition')))
        self.assertEqual(stack.open_info(), 'movieset')


if __name__ == '__main__':
    unittest.main()
