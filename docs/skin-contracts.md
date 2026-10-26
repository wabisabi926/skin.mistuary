# 皮肤隐式契约（窗口属性 / 皮肤设置 / 控件 ID）

审查报告 §2 提到：皮肤大量依赖"数字控件 ID + `Window(home).Property(...)` + 皮肤设置"
这三类隐式契约，XML 解析检查发现不了，改导航或模态窗口时容易回归。
这份文档把主要契约集中记下来，改相关代码前先看一眼。

生成方式：`grep` 全仓库 `xml/*.xml` 的 `SetProperty/ClearProperty/Window(home).Property`、
`Skin.Set*/HasSetting/String`，再人工归类。数字是"出现次数"，不是权威计数。

---

## 一、窗口属性（`Window(home).Property`）

全部挂在 **Home 窗口**上（`SetProperty(x,v,home)` 的第三个参数就是窗口名）。
其它窗口要读必须写 `Window(home).Property(x)`，不要用裸 `Window.Property(x)`——
裸写法会落到 `GetActiveWindowOrDialog()`，在非模态对话框里读不到。

| 属性 | 谁写 | 谁读 | 生命周期 |
|---|---|---|---|
| `Home.Section` | 首页顶部导航的 `<onfocus>`（`SetProperty(Home.Section,<section>,home)`） | 8 个文件（Home / Includes_Home / 各种 Hero） | 常驻；`onload` 只在为空时选默认焦点 |
| `Home.FileReturnControl` | `Home.xml` 的 `<onunload condition="Window.Next(filemanager) + Control.HasFocus(N)">` | `Home.xml` 的 `<onload condition="Window.Previous(filemanager) ...">` | **进入文件管理器时写，回首页时读并清空**；`<onunload>` 里还有一条无条件 Clear 防残留 |
| `Home.SharedRandomFanart` / `.SessionPath` | `onunload`（离开去 filemanager 时） | 搜索、收藏、文件管理器的共享背景 | 会话级，切窗口时重建 |
| `Home.LastMovieFanart` / `Home.LastTVShowFanart` | 媒体库视图 | 首页背景 | 常驻，用于"没有新 fanart 时沿用上一张" |
| `Home.movies.Hero/Page/Row`、`Home.tvshows.*` | `SetProperty(Home.$PARAM[section].*)` 动态拼名 | 首页分组导航 | 常驻；注意是**动态属性名**，grep 静态字符串搜不到 |
| `Search.ActiveType` / `NumbersVisible` / `KeyboardHidden` / `SettingsTransition` | 搜索抽屉的键盘/数字区交互 | 搜索抽屉 | 每次开抽屉重建，关闭时 Clear |
| `VideoInfo.More` / `VideoInfo.FanartSource` | 详情页"更多"按钮 | 详情页 | 对话框级 |
| `MovieSetDialog.SetId/SetName/SourceFanart` | 合集对话框 | 合集对话框 + 影片列表 | 关闭时 Clear |
| `settingsdialog_header/content` | 设置对话框入口 | 设置对话框 | 打开时写，关闭时 Clear |
| `TextViewer_Header/Text` | 文本查看器 | 文本查看器 | 打开时写 |
| `VideoOSDPlaylist.FocusControl` / `CloseOSD` | OSD 播放列表 | OSD | 关闭时 Clear |
| `infobackground` / `fanart` | 多个窗口 | 背景层 | 常驻，最容易被别处覆盖 |
| `NaraMediaMenu.Browse` | — | — | 只在 `onunload` 里 Clear，是**历史残留** |

**新增属性时的规矩**：写在 Home 上就一律带 `,home`；对话框关闭路径里必须有 `ClearProperty`，
否则下次打开会沿用上一次的值（`Search.SettingsTransition` 就是为此加的）。

---

## 二、皮肤设置（`Skin.String` / `Skin.HasSetting` / `Skin.SetBool`）

Kodi 的皮肤设置名是**大小写敏感的字符串**。本皮肤踩过 `autoscroll` / `AutoScroll` 的坑，
写入端和读取端必须逐字一致。`Settings.xml` 里 `<setting>` 数量为 0，
所以所有开关都是皮肤自己用 `Skin.Set*/ToggleSetting` 管理的。

| 分组 | 键 | 说明 |
|---|---|---|
| 首页菜单 | `HomeMenuNoMovieButton`、`HomeMenuNoMusicButton`、`HomeMenuNoTVButton`、`HomeMenuNoTVShowButton` | 隐藏顶部导航项；`NaraHomeMenuDefaultsMusicTVOff` 是"首次运行给音乐/电视默认关掉"的一次性标记 |
| 首页小组件 | `home_no_<section>_<widget>_widget`（约 22 个） | 逐个小组件的开关，命名规则固定为 `home_no_` + 段名 + 组件名 + `_widget` |
| 视觉 | `no_fanart`（12 处读取）、`hide_background_fanart`、`animate_background_fanart`、`hide_mediaflags`、`show_musicvideoposter` | 背景与媒体标识开关 |
| 播放 | `autoscroll`、`OSDAutoClose`、`OSDAutoCloseTime`、`nara_cast_open` | 自动滚动 / OSD 自动关闭 / 演员栏展开 |
| 数据 | `Nara.MusicBackground`、`Nara.SharedRandomFanart.LockedPath`、`library_art_folder` | 字符串型；`LockedPath` 表示"用户手动锁定的背景" |
| 一次性标记 | `NaraHomeMenuDefaultsMusicTVOff` | `onload` 里判断后立刻 SetBool，避免重复初始化 |

**写入内置函数有 11 个，判断"有没有写入入口"时必须搜全**：
`Skin.SetBool` / `SetString` / `SetNumeric` / `SetPath` / `SetAddon` / `SetImage` /
`SetFile` / `SetColor` / `ToggleSetting` / `Reset`，以及
**`Skin.SelectBool(header, 标签|设置名, …)`**——单选互斥，选中项置真、同组其余全部置假。

`SelectBool` 最容易漏：设置名藏在 `数字|设置名` 的配对里，按 `Skin.Set` 前缀搜不到。
**2026-10-26 就因此把 15 个设置误判成"只读"**，实际它们全都有入口：

| 设置 | 写入点 | 内置函数 |
|---|---|---|
| `circle_rating` / `circle_userrating` | `SkinSettings.xml:59` | `SelectBool` |
| `movieset_onclick_*` | `SkinSettings.xml:138` | `SelectBool` |
| `tvshow_onclick_*` | `SkinSettings.xml:168` | `SelectBool` |
| `album_onclick_*` | `SkinSettings.xml:198` | `SelectBool` |
| `OriginalTitleFormat_*` | `SkinSettings.xml:68` | `SelectBool` |
| `OSDAutoCloseTime` | `SkinSettings.xml:250` | `SetNumeric` |
| `library_art_folder` | `SkinSettings.xml:41` | `SetPath` |
| `LyricScript_Path` | `Includes_SettingsDialog.xml:242` | `SetAddon` |

入口都在可达 UI：设置中心（`skinsettings`）4 个侧边栏页面，歌词插件在设置对话框。

`circle_none` 和 `OriginalTitleFormat_Default` 是 `SelectBool` 里的"恢复默认"选项：
选中它等于把同组其它开关全置假，**自己永远不会被读取**，所以它们在
`audit_skin.py` 的"有写无读"统计里被列入白名单（`RESET_ONLY_SETTINGS`）。

现状（`python extras/audit_skin.py` 输出）：**66 读 / 68 写，有读无写 0、有写无读 0**。

---

## 三、跨窗口共享的控件 ID

Kodi 的 `SetFocus(id)` / `onleft/onright` 都按数字 ID 找控件，改名或删控件会静默失效。

| ID | 用途 | 备注 |
|---|---|---|
| `9000` | 首页顶部导航 grouplist | 几乎所有 `onback`/`onup` 的归宿 |
| `9011`/`9012` | 首页初始焦点（有/无"电影"按钮两种） | `onload` 里按 `HomeMenuNoMovieButton` 二选一 |
| `9017` | 文件区的"返回"按钮 | 与 `Home.FileReturnControl` 一起用 |
| `15010` | 首页文件源卡片 panel | 内容 `sources://files/`，`target="filemanager"` |
| `50`/`51`/`501` | 列表/海报视图容器 | 技术标识行用 `Container(50).ListItem` 之类的前缀 |
| `5100`…`6800` | 首页各小组件容器 | `HomeVideoHeroDetails` 通过 `list_id` 参数拿到 |
| `16090` | 搜索结果的共享 fanart 容器 | `onunload` 里读它的 `Art(fanart)` |
| `804` | 顶部导航的"文件"按钮 | `onfocus` 写 `Home.Section=files` |

**已删除的 ID**：`15020`（常用文件夹 8 槽位 panel，2026-10-26 移除，因为没有写入入口）。
如果以后要恢复，`git log -S"HomeFileShortcutItems"` 能找到原实现。

---

## 四、改这些地方时要注意

1. **对话框里的开关**用 `Skin.ToggleSetting` / `Skin.HasSetting`，不要用 `SetProperty`——
   非模态对话框的 `SetProperty` 会落到别处，读端永远 false（踩过两次）。
2. **grouplist 里的 button 必须自己写 `onleft`/`onright`**，并且指向目标按钮的 id；
   包装用的 `<control type="group">` 没有 id，Kodi 串不出导航链。
3. **`<include>` 有 `<param>` 就必须有 `<definition>`**，否则整条 include 被丢弃（`ChannelManagerList` 就是这么坏的）。
   参数本身不声明也能用，调用点传的值会和默认值合并。
4. **技术标识胶囊有两条渲染路径**：`$MAP`（Kodi 22）和原始值（Kodi 21），
   由 `$EXP[nara_kodi21]` 切换。改胶囊时两个分支都要改，`flag_label_raw` 别漏。
5. **皮肤字符串 31000–31999 是自有区间**，`$LOCALIZE[31xxx]` 必须在 `language/*/strings.po` 里；
   31xxx 以下都是 Kodi 内置串，`audit_skin.py` 不会再报缺失。
