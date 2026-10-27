# Mistuary（雾汐）

雾汐｜轻量透明皮肤，基于 Nara 魔改的 Estuary N，支持透黑、透白双模式，建议搭配 Emby for kodi next gen 自动同步。

Mistuary 是衍生自 Estuary N 的视频优先皮肤，面向**未做任何内核修改的 Kodi 21 Omega 及以上版本**，
CoreELEC 设备同样可用。原分支依赖魔改内核的玻璃、圆角、slot 列表与稳定选中项扩展，
均已换成普通贴图和标准控件，因此不需要定制内核即可运行。

### Kodi 21 与 22 的差异

皮肤同时支持 21 和 22，两版都能正常使用；22 独有的标签在 21 上会自动隐藏或退化为原值
（`$MAP[]` 标签查表是 22 才加的，21 上技术标识显示 `DOLBYVISION`、`AC3` 这类原始值）：

| 项目 | Kodi 22 | Kodi 21 |
| --- | --- | --- |
| 详情页技术标识 | `4K UHD` / `DOLBY VISION` / `DOLBY DIGITAL` | `4K` / `DOLBYVISION` / `AC3`（OSD 上仍是完整名称） |
| 杜比视界档位（P7 FEL 等） | 显示 | 不显示 |
| 字幕名 / 字幕编码 / 音频语言扩展名 | 显示 | 退化为空或普通语言名 |
| PVR 客户端名 / 实例名 / 分组来源 / 媒体提供方 | 显示 | 整行自动隐藏 |
| 频道台标 | `ListItem.ChannelLogo` | 回退 `Art(thumb)` / `EpgEventIcon` |

- 电影与剧集详情页：全屏沉浸式布局，演员栏默认收起、点图标展开
- 首页顶部导航、媒体库视图：统一海报标题与年份排版
- 设置中心：把 Kodi 原生设置与皮肤选项放在一起
- 音乐：播放页右侧歌词（CU LRC）、OSD 评分与歌词按钮、可替换的播放背景
- 省略天气、电台与游戏浏览界面，仅维护英文和简体中文

## 安装

1. 下载本仓库，把整个目录放到 Kodi 的 `addons/` 下，目录名改为 `skin.mistuary`
2. 重启 Kodi
3. 设置 → 界面 → 皮肤 → 皮肤 → 选择 **Mistuary**

## 透黑 / 透白

两套主题都在「设置 → 界面 → 皮肤 → 颜色」里切换：

- `SKINDEFAULT` = 透黑（玻璃压黑，默认）
- `light` = 透白（玻璃提白）

面板统一使用与文件管理器同款的磨砂玻璃（`glass_frosted`），文字在两种模式下都是白色。

## 打包贴图

改动 `media/` 里的图片后需要重新打包（Kodi 优先读 `Textures.xbt`）：

```bash
python tools/xbt_tool.py pack
```

## 许可

本皮肤同时包含**代码**与**美术素材**，两者许可不同；另外还有若干第三方素材，
其原始许可要求"随副本一并分发声明"。本节的第三方声明必须随皮肤一起发布。

| 部分 | 许可 | 全文 |
| --- | --- | --- |
| 皮肤代码（`xml/`、`colors/`、`tools/`） | GNU GPL v2 | [`LICENSE`](LICENSE) |
| 美术素材（配色、布局、图标重绘、背景图） | CC BY-SA 4.0 | <https://creativecommons.org/licenses/by-sa/4.0/> |
| UI 字体 `fonts/Inter-Unicode-Regular.ttf` | SIL OFL 1.1 | [`fonts/OFL.txt`](fonts/OFL.txt) |
| `script.tinyppi` 播放器图标 | MIT | 见下文 |
| Arctic Fuse 2 类型图标 | 上游许可 | 见下文 |

### 来源与署名

本皮肤衍生自 **Estuary**（phil65 / Team Kodi）与 **Estuary N**，按上游许可保留署名：

- Estuary 代码：GNU GPL v2
- Estuary 美术：CC BY-SA 4.0
- Mistuary 自身的改动（配色、布局、玻璃面板、不透明度设置、图标重绘等）沿用同一许可：
  代码部分 GPL v2，美术部分 CC BY-SA 4.0。

### script.tinyppi 播放器图标（MIT）

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

### Inter（含 CJK）字体（SIL OFL 1.1）

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

### Arctic Fuse 2 类型图标

`media/genres/` 里的 27 张 PNG 原样复制自 Arctic Fuse 2 素材中的 `genres/` 目录；
回退图标 `media/DefaultGenre.png` 原样复制自同一份素材里的 `DefaultGenres.png`。

Source: <https://github.com/narapeka/skin.arctic.fuse.2>

Upstream: <https://github.com/jurialmunkey/skin.arctic.fuse.2>

Source revision: 91c6fd8f932879dbe57e789d4651052ae25fb567
