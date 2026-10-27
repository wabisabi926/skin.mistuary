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

| 部分 | 许可 |
| --- | --- |
| 皮肤代码（`xml/`、`colors/`、`tools/`） | GNU GPL v2 —— 全文见 [`LICENSE`](LICENSE) |
| 美术素材（配色、布局、图标重绘、背景图） | CC BY-SA 4.0 |
| UI 字体 | SIL OFL 1.1 —— 见 [`fonts/OFL.txt`](fonts/OFL.txt) |

本皮肤衍生自 [Estuary](https://github.com/xbmc/xbmc/tree/master/addons/skin.estuary)
（phil65 / Team Kodi）与 Estuary N，按上游要求保留署名。
第三方素材的来源与许可见 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。
