# 许可与第三方声明

本皮肤同时包含**代码**与**美术素材**，两者许可不同；另外还有若干第三方素材，
其原始许可要求"随副本一并分发声明"。发布包必须同时带上本文件、`LICENSE` 和 `fonts/OFL.txt`。

## 一、许可构成

| 部分 | 许可 | 全文 |
|---|---|---|
| 皮肤代码（`xml/`、`colors/`、`tools/`） | GNU GPL v2 | [`LICENSE`](LICENSE) |
| 美术素材（配色、布局、图标重绘、背景图） | CC BY-SA 4.0 | <https://creativecommons.org/licenses/by-sa/4.0/> |
| UI 字体 `fonts/Inter-Unicode-Regular.ttf` | SIL OFL 1.1 | [`fonts/OFL.txt`](fonts/OFL.txt) |
| `script.tinyppi` 播放器图标 | MIT | 见下文 |
| Arctic Fuse 2 类型图标 | 上游许可 | 见下文 |

## 二、来源与署名

本皮肤衍生自 **Estuary**（phil65 / Team Kodi）与 **Estuary N**，按上游许可保留署名：

- Estuary 代码：GNU GPL v2
- Estuary 美术：CC BY-SA 4.0
- Mistuary 自身的改动（配色、布局、玻璃面板、不透明度设置、图标重绘等）沿用同一许可：
  代码部分 GPL v2，美术部分 CC BY-SA 4.0。

## 三、第三方素材

本皮肤包含下列第三方素材，各自按其原始许可分发。
原始许可要求"随副本一并分发版权声明"，因此本节必须随皮肤一起发布。


--- script.tinyppi player-process icons ---

The player-process information panel includes copies of the following
icons from script.tinyppi:

- arrow-progress.png
- camcorder.png
- chart.png
- check-circle.png
- circle-xmark.png
- dv-logo.png
- layer-group.png
- memory.png
- volume.png

Source: https://github.com/CE-Repo/script.tinyppi

Source revision: 45ef08917b2a4943b25d71963553a907adad0259

MIT License

Copyright (c) 2026 U3knOwn

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

--- Inter (with CJK coverage) — fonts/Inter-Unicode-Regular.ttf ---

The skin's UI font is fonts/Inter-Unicode-Regular.ttf, a build of Inter that also carries CJK
glyphs, so Latin and Chinese share one set of metrics. It is the same
Inter-Unicode-Regular.ttf file shipped by the resource.font.robotocjksc
addon, used unmodified.

- Family / version (from the font's name table): Inter / Version 4.000
- Glyph coverage: 49 833 glyphs, 16 502 CJK ideographs, full Latin + CJK punctuation
- License: SIL Open Font License 1.1 — full text in fonts/OFL.txt
- Inter upstream: https://github.com/rsms/inter
- The CJK-merged build is distributed by
  https://github.com/jurialmunkey/resource.font.robotocjksc (Apache-2.0 addon
  packaging; the font itself carries the OFL notice above)

If you prefer to rebuild the file yourself, merge Inter (OFL) with Noto Sans SC
(OFL) using fontTools.merge; the result stays OFL and can replace
fonts/Inter-Unicode-Regular.ttf without touching xml/Font.xml.

--- Arctic Fuse 2 genre icons ---

The 27 PNG images in media/genres/ are copied without modification from
genres/ in the supplied Arctic Fuse 2 asset checkout.
The fallback icon media/DefaultGenre.png is copied without modification
from DefaultGenres.png in the same checkout.

Source: https://github.com/narapeka/skin.arctic.fuse.2

Upstream: https://github.com/jurialmunkey/skin.arctic.fuse.2

Source revision: 91c6fd8f932879dbe57e789d4651052ae25fb567
