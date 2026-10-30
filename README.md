# Mistuary（雾汐）

雾汐｜轻量透明皮肤，衍生自 Estuary N，视频优先。支持**透黑 / 透白**双主题，
三档独立透明度，原生 Kodi 21 Omega 及以上即可运行，**不需要任何内核改动**。

> 建议搭配 **Emby for Kodi next gen** 使用（媒体库自动同步、豆瓣评分）。

---

## 支持范围

| 项 | 说明 |
|---|---|
| Kodi 版本 | **21 Omega 及以上**（22 有额外标签支持，见下文） |
| 平台 | Windows / Linux / CoreELEC / Android 均可 |
| 语言 | 简体中文、English |
| 必需插件 | 无。装 Emby 插件会更好用，但不装也能跑 |

## 安装

**从压缩包安装（推荐）**

1. 到 [Releases](https://github.com/wabisabi926/skin.mistuary/releases) 下载最新 `skin.mistuary-x.y.z.zip`
2. Kodi → 设置 → 插件 → 从 zip 文件安装
3. 设置 → 界面 → 皮肤 → 皮肤 → 选 **Mistuary**

**手动安装**：把整个仓库目录放到 Kodi 的 `addons/` 下，目录名改成 `skin.mistuary`，重启 Kodi。

## 主要功能

- **三档透明度**：页面 / 浮窗 / 播放中，各 6 级（皮肤设置 → 外观），互不干扰
- **详情页**：全屏沉浸式布局，演员栏默认收起，点图标展开
- **评分胶囊**：豆瓣 / IMDb / TMDB / 烂番茄，按数据源自动取最多两个
- **技术标识**：分辨率、编码、HDR 等做成图标，放在简介下方
- **海报墙**：真圆角（遮罩裁切，不是盖角），焦点环贴边
- **音乐**：播放页右侧歌词（CU LRC）、黑胶唱片模式、可替换播放背景
- **电源菜单**：长按返回键，退出 / 重启 / 待机 / 休眠 / 设置，按平台能力自动显隐
- **设置中心**：把 Kodi 原生设置和皮肤选项放在一起

## 透黑 / 透白

在「设置 → 界面 → 皮肤 → 颜色」切换：

- `SKINDEFAULT` = 透黑（玻璃压黑，默认）
- `light` = 透白（玻璃提白）

面板统一走 `gl_1..6` 档位，由「皮肤设置 → 外观」的三个透明度设置控制；文字在两种模式下都是白色。

## Kodi 21 与 22 的差异

两版都能正常用。22 独有的标签在 21 上会自动隐藏或退化为原值：

| 项目 | Kodi 22 | Kodi 21 |
| --- | --- | --- |
| 详情页技术标识 | `4K UHD` / `DOLBY VISION` / `DOLBY DIGITAL` | `4K` / `DOLBYVISION` / `AC3`（OSD 上仍是完整名称） |
| 杜比视界档位（P7 FEL 等） | 显示 | 不显示 |
| 字幕名 / 字幕编码 / 音频语言扩展名 | 显示 | 退化为空或普通语言名 |
| PVR 客户端名 / 实例名 / 分组来源 / 媒体提供方 | 显示 | 整行自动隐藏 |
| 频道台标 | `ListItem.ChannelLogo` | 回退 `Art(thumb)` / `EpgEventIcon` |

## 已知限制

- **安卓上电源菜单只有「退出 / 设置」**：Kodi 在安卓没有关机、重启的系统权限，皮肤补不了
- **杜比视界档位（P7 / P7 FEL）只在 Kodi 22 显示**：Kodi 的播放信息里没有这个字段
- **不维护天气、电台、游戏界面**：只保留视频、音乐、图片、PVR、插件
- **只维护中英双语**：其他语言会显示英文

## 许可

本皮肤**代码**与**美术素材**许可不同，另有若干第三方素材：

| 部分 | 许可 |
| --- | --- |
| 皮肤代码（`xml/`、`colors/`、`tools/`） | GNU GPL v2 —— 全文见 [`LICENSE`](LICENSE) |
| 美术素材（配色、布局、图标重绘、背景图） | CC BY-SA 4.0 |
| UI 字体 `fonts/Inter-Unicode-Regular.ttf` | SIL OFL 1.1 —— 全文见 [`fonts/OFL.txt`](fonts/OFL.txt) |

第三方素材的**完整来源、版本与许可声明**见 [`CREDITS.md`](CREDITS.md)
（tinyppi 图标 MIT、Inter 字体 OFL、Arctic Fuse 类型图标与技术标识 CC BY-NC-SA）。
分发或再发布时，`LICENSE`、`fonts/OFL.txt`、`CREDITS.md` 三个文件必须一起带上。

## 反馈

问题、建议、皮肤想法都可以开 issue：
<https://github.com/wabisabi926/skin.mistuary/issues>

---

<sub>开发相关（改皮肤、打包贴图、发版流程）见 [`docs/HANDOVER.md`](docs/HANDOVER.md)。</sub>
