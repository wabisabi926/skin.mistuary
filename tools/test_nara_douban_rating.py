"""详情页豆瓣评分的窗口属性契约。

这组用例存在的理由：M2 接入时皮肤写属性漏了两个东西，功能会"静默失效"——
不报错、界面上看不出来，只有标题带逗号或没有 IMDb 的条目查不到分：

1. **漏 `home`**：`SetProperty(x,y)` 默认写在**当前窗口**（详情页 12005），
   而插件读的是 `Window(10000)`（`lib/kodi.py: get_home_property`），
   离开详情页时 `ClearProperty(x,home)` 清的又是 home —— 三处对不上。
2. **漏 `$ESCINFO`**：内置函数的参数按逗号切分，`$INFO[ListItem.Title]` 里
   带逗号会把值截断（本仓库其它地方写文本属性都用 `$ESCINFO`，
   见 `DialogPVRInfo.xml: SetProperty(TextViewer_Text,$ESCINFO[ListItem.Plot],home)`）。

下面把契约钉住：写 home、转义、离开时清掉、调用前判断插件是否启用。
"""

import re
import unittest
from pathlib import Path

XML_DIR = Path(__file__).resolve().parents[1] / "xml"
VIDEO_INFO = XML_DIR / "DialogVideoInfo.xml"

# 皮肤写、插件读（script.mistuary.helper/lib/kodi.py: get_home_property）
PROPS = ("Mistuary.Rating.Query", "Mistuary.Rating.Year")


class DoubanRatingPropContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = VIDEO_INFO.read_text(encoding="utf-8")

    def _lines(self, prop: str, action: str) -> list[str]:
        return [
            line.strip()
            for line in self.text.splitlines()
            if action in line and prop in line
        ]

    def test_written_to_home_window(self):
        """SetProperty 必须带 ,home —— 插件读的是 Window(10000)。"""
        for prop in PROPS:
            lines = self._lines(prop, "SetProperty")
            self.assertTrue(lines, f"{prop} 没有写入语句")
            for line in lines:
                self.assertIn(",home)", line, f"{prop} 没写 home 窗口：{line}")

    def test_value_is_comma_escaped(self):
        """值必须走 $ESCINFO，否则标题带逗号会被截断。"""
        for prop in PROPS:
            for line in self._lines(prop, "SetProperty"):
                self.assertIn("$ESCINFO[", line, f"{prop} 没用 $ESCINFO：{line}")
                self.assertNotIn("$INFO[", line.replace("$ESCINFO[", ""),
                                 f"{prop} 混用了 $INFO：{line}")

    def test_cleared_on_unload(self):
        """离开详情页要清掉，否则切换条目时插件读到上一条的标题。"""
        for prop in PROPS:
            lines = self._lines(prop, "ClearProperty")
            self.assertTrue(lines, f"{prop} 没有清理语句")
            for line in lines:
                self.assertIn(",home)", line, f"{prop} 清理的窗口不对：{line}")

    def test_runscript_guarded_by_addon_check(self):
        """插件没装时不能调 RunScript，否则弹"找不到插件"。"""
        line = next(
            (l for l in self.text.splitlines() if "RunScript(script.mistuary.helper" in l),
            None,
        )
        self.assertIsNotNone(line, "没有找到 RunScript 调用")
        self.assertIn("System.AddonIsEnabled(script.mistuary.helper)", line)

    def test_runscript_only_for_movie_and_tvshow(self):
        """单集 / 季不请求豆瓣（豆瓣没有单集分）。"""
        line = next(
            (l for l in self.text.splitlines() if "RunScript(script.mistuary.helper" in l),
            None,
        )
        self.assertIsNotNone(line)
        self.assertIn("String.IsEqual(ListItem.DBType,movie)", line)
        self.assertIn("String.IsEqual(ListItem.DBType,tvshow)", line)


if __name__ == "__main__":
    unittest.main()
