# 第三方素材来源与署名

本皮肤包含若干第三方素材，各自的许可要求「随副本一并分发声明」。
本文件是这些声明的完整版本；`LICENSE` 末尾有摘要和指向。

> **发布时这两个文件都要进包**：`LICENSE` + `CREDITS.md`（都在仓库根目录，
>  `release.yml` 只排除 `docs/` 和 `tools/`，根目录文件默认会进包）。
> 少任何一个，OFL 字体和 CC BY-SA 素材的分发条件就不完整。

## 目录

| 素材 | 位置 | 许可 |
|---|---|---|
| Estuary / Estuary N 衍生基础 | 全皮肤 | 代码 GPL v2 / 美术 CC BY-SA 4.0 |
| `script.tinyppi` 播放器图标 | `media/` 若干 PNG | MIT |
| Inter（含 CJK）字体 | `fonts/Inter-Unicode-Regular.ttf` | SIL OFL 1.1 |
| Arctic Fuse 2 类型图标 | `media/genres/`、`media/DefaultGenre.png` | 上游许可 |
| 技术标识图标 | `media/techflags/` | CC BY-NC-SA 4.0 |

---

## 衍生来源

本皮肤衍生自 **Estuary**（phil65 / Team Kodi）与 **Estuary N**，按上游许可保留署名：

- Estuary 代码：GNU GPL v2
- Estuary 美术：CC BY-SA 4.0
- Mistuary 自身的改动（配色、布局、玻璃面板、不透明度设置、图标重绘等）沿用同一许可：
  代码部分 GPL v2，美术部分 CC BY-SA 4.0

---

## script.tinyppi 播放器图标（MIT）

播放处理信息面板包含以下来自 script.tinyppi 的图标副本：

- arrow-progress.png
- camcorder.png
- chart.png
- check-circle.png
- circle-xmark.png
- dv-logo.png
- layer-group.png
- memory.png
- volume.png

Source: <https://github.com/CE-Repo/script.tinyppi>

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

---

## Inter（含 CJK）字体（SIL OFL 1.1）

皮肤字体 `fonts/Inter-Unicode-Regular.ttf` 是带有 CJK 字形的 Inter 构建版，
拉丁与中文共用一套度量；它和 `resource.font.robotocjksc` 插件随附的
`Inter-Unicode-Regular.ttf` 是同一个文件，未做修改。

- 字族 / 版本（取自字体 name 表）：Inter / Version 4.000
- 字形覆盖：49833 个字形，16502 个 CJK 统一表意文字，完整拉丁与 CJK 标点
- 许可：SIL Open Font License 1.1 —— 全文见 [`fonts/OFL.txt`](fonts/OFL.txt)
- Inter 上游：<https://github.com/rsms/inter>
- 合并 CJK 的字体由 <https://github.com/jurialmunkey/resource.font.robotocjksc>
  分发（插件打包用 Apache-2.0，字体本身适用上面的 OFL 声明）

若想自行重建：用 fontTools.merge 合并 Inter（OFL）与 Noto Sans SC（OFL），
产物仍是 OFL，可直接替换 `fonts/Inter-Unicode-Regular.ttf`，无需改动 `xml/Font.xml`。

---

## Arctic Fuse 2 类型图标

`media/genres/` 里的 27 张 PNG 原样复制自 Arctic Fuse 2 素材中的 `genres/` 目录；
回退图标 `media/DefaultGenre.png` 原样复制自同一份素材里的 `DefaultGenres.png`。

Source: <https://github.com/narapeka/skin.arctic.fuse.2>

Upstream: <https://github.com/jurialmunkey/skin.arctic.fuse.2>

Source revision: 91c6fd8f932879dbe57e789d4651052ae25fb567

---

## 技术标识图标（`media/techflags/`）

详情页技术标识行的彩色图标，来自 Arctic Fuse 3 系列皮肤，按原许可
（CC BY-NC-SA 4.0）随副本分发；仅做了等比缩放与去留白，未改动图形本身：

- `skin.arctic.fuse.3` → `media/flags/color/{resolution,source,audio,channels}`
- `skin.arctic.fuse.3-avdvplus&p3i` → `media/flags/color/hdr`
- `skin.arctic.zephyr.martian` → `media/flags/color/channels/12.png`（fuse3 只到 10）

素材库没有对应 logo 的冷门格式（8K、HD DVD、ProRes、VHS、AVC、AV3A、WavPack 等 16 个），
由 `tools/gen_techflag_icons.py` 用 Inter 字体渲染成同风格白字标，不涉及第三方美术。

Upstream: `skin.arctic.fuse.3` / `skin.arctic.fuse.3-avdvplus&p3i` / `skin.arctic.zephyr.martian`
（三者均为 CC BY-NC-SA 4.0 / 3.0，图形版权归原作者）

重新生成：`python tools/gen_techflag_icons.py`
