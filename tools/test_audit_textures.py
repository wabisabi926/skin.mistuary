"""贴图存在性检查的三种写法。

这组用例存在的理由：审计报"缺失贴图 0 个"时要能确认**它真的在查**，
而不是因为路径写法不认识、一律放过去了。皮肤里有三种贴图写法：

    ① shapes/glass20.png                    ← 相对 media/
    ② special://skin/libraryart/x.jpg       ← 根目录（libraryart / extras / resources）
    ③ special://xbmc/...                    ← Kodi 自己的，不在包里

另外含 `$` 的是动态路径（`libraryart/$INFO[ListItem.Label].jpg`），
静态查不了，只能放行 —— 2026-10-30 日志里 `libraryart/临时.png` 加载失败就是这么来的：
分类名在运行时才知道，皮肤和审计都判断不了。
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_skin import texture_exists  # noqa: E402


class TextureExistsTest(unittest.TestCase):
    def test_relative_media_path_exists(self):
        """① 相对 media/ 的短名。"""
        self.assertTrue(texture_exists("shapes/glass20.png"))

    def test_relative_media_path_missing(self):
        self.assertFalse(texture_exists("shapes/definitely-not-here.png"))

    def test_special_skin_libraryart_exists(self):
        """② special://skin/ 指向仓库根目录，libraryart 走这条。"""
        self.assertTrue(texture_exists("special://skin/libraryart/default.jpg"))

    def test_special_skin_libraryart_missing(self):
        """② 缺失时**必须报出来** —— 这是审计能覆盖 libraryart 的证据。"""
        self.assertFalse(texture_exists("special://skin/libraryart/不存在的封面.jpg"))

    def test_special_skin_extras_exists(self):
        self.assertTrue(texture_exists("special://skin/extras/backgrounds/primary.jpg"))

    def test_special_xbmc_always_ok(self):
        """③ Kodi 自带的贴图不在包里，不能报缺失。"""
        self.assertTrue(texture_exists("special://xbmc/media/icon.png"))

    def test_dynamic_path_is_skipped(self):
        """含 $ 的动态路径无法静态判断，一律放行。"""
        self.assertTrue(texture_exists("special://skin/libraryart/$INFO[ListItem.Label].jpg"))

    def test_empty_is_ok(self):
        self.assertTrue(texture_exists(""))


if __name__ == "__main__":
    unittest.main()
