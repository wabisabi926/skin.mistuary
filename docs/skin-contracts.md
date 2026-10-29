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
| 视觉 | `no_fanart`（12 处读取）、`hide_background_fanart`、`animate_background_fanart`、`hide_mediaflags`、`hide_techflag_icons`、`show_musicvideoposter` | 背景与媒体标识开关 |
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
| `rating_src_auto` / `rating_src_tmdb` / `rating_src_imdb` / `douban_rating` | `SkinSettings.xml:81`（主评分来源四档） | `SelectBool` |
| `glass_page_op_1..6` / `glass_float_op_1..6` / `glass_play_op_1..6` | `SkinSettings.xml:711/712/713` | `SelectBool` |

入口都在可达 UI：设置中心（`skinsettings`）4 个侧边栏页面，歌词插件在设置对话框。

**主评分来源四档互斥，读取端 `NaraOnlineRatingsRow` 里手选优先**：只要用户指定了来源
（`douban_rating` / `rating_src_imdb` / `rating_src_tmdb` 任一为真），就只按档位画图标；
选「自动」（`rating_src_auto`，三档手动全假，等同于从未设置）时才比对
`Rating(tmdb/trakt/imdb)` 自动识别，最后默认 TMDb。
**不要让自动识别排在设置前面**：Emby 插件（`Set imdb as default rating provider`，默认开）
会把 `CommunityRating` 补写成 imdb 类型，届时有类型字段的条目永远命中 IMDb，设置就失效了。

`circle_none`、`OriginalTitleFormat_Default` 和 `rating_src_auto` 是 `SelectBool` 里的
"恢复默认"选项：选中它等于把同组其它开关全置假，**自己永远不会被读取**（读取端只看
其余三档是否为假），所以它们在 `audit_skin.py` 的"有写无读"统计里被列入白名单（`RESET_ONLY_SETTINGS`）。

现状（`python tools/audit_skin.py` 输出）：**88 读 / 91 写，有读无写 0、有写无读 0**。

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
4. **技术标识胶囊现在有四条渲染路径**：图标 / 文字 × Kodi 22 / 21。
   入口统一在 `NaraTechnicalFlag`，不要在内容段直接调 `NaraTechnicalTextPill`——
   那样会绕过图标分支。细节见下一节。
5. **皮肤字符串 31000–31999 是自有区间**，`$LOCALIZE[31xxx]` 必须在 `language/*/strings.po` 里；
   31xxx 以下都是 Kodi 内置串，`audit_skin.py` 不会再报缺失。

### 4.1 技术标识图标（techflags）

| 项 | 约定 |
|---|---|
| 入口 | `NaraTechnicalFlag`（图标 / 文字双分支）→ `NaraTechnicalIconPill` / `NaraTechnicalTextPill` |
| 图标路径 | `techflags/color/<类别>/<原始值>.png`，由 `NaraTechnical*IconMap` 查表 |
| 生成脚本 | `tools/gen_techflag_icons.py`（`--check` 供 CI） |
| 素材规格 | 96×56 画布（约 2:1），显示框 48×28；胶囊 72（DV 带档位 100），itemgap 8 |
| 评分胶囊 | `NaraOnlineRatingItem` 同款底板：114（IMDb 128），内边距 12 |
| 开关 | `hide_techflag_icons`，关掉 = 回到纯文字胶囊 |
| 位置 | 四处（详情页 / 首页 / 搜索 / 海报视图 51）**全部并入评分行**：`NaraOnlineRatingsRow` + `inline_flags=true`；已无独立行组件 |

**三条硬约束**：

1. **每个取值都必须有图标。** `IconMap` 覆盖 TextMap 的全部 key；素材库没有 logo 的
   冷门格式由脚本用显示名渲染成白字标。所以运行时不判断"这个值有没有图"——
   `$MAP` 只出现在 `<texture>` 里，和原有用法一致。**不要把 `$MAP` 写进 `<visible>`**：
   现有代码里没有先例，行为未经验证。
2. **加新取值要改两处**：`*TextMap`（显示名）+ 重跑生成脚本（补图标）。只改前者的话，
   Kodi 22 上会因为 IconMap 缺 entry 而显示空图。
3. **声道不用图标，只出文字。** 素材按声道数命名且图上印死了布局文字，而
   `5.1.2`/`7.1` 同为 8 声道、`5.1.4`/`7.1.2` 同为 10 声道，图必然说谎。
   `skin.estuary.nara` 的「Atmos 码 + 声道数」推断在本机片库不成立（DB 里没有 `*_atmos`）。

---

## 五、设置页内容区标准（2026-10-27 统一）

设置中心下的所有页面共用一套几何。**注意区分「内容矩形」和「视觉文字边界」**——
这是踩过的坑：只看矩形会把文字摆得比 PVR 靠左 28px。

| 元素 | 坐标 | 说明 |
|---|---|---|
| 玻璃面板 | `left 505 / top 145`，`1355 × 740` | |
| **内容矩形** | **`left 525 / top 193`，`1315 × 644`** | 焦点范围、滚动条、进度条用这个 |
| **视觉文字/卡片边界** | **`left 553 / right 1812`，`top 193 / bottom 837`** | 宽 `1259`，高 `644` |
| 滚动条 | `left 1874 / top 193`，`8 × 644` | 在面板外侧，**轨道要和列表同高**，否则滑块比例算错 |
| 左侧栏 | `left 76 / top 165`，`368 × 685` | |
| 底部帮助条 | `left 545 / top 915`，`1255 × 100` | |

**四边内边距都是 48**：左 `553−505`、右 `1860−1812`、上 `193−145`、下 `885−837`。
用 `bottom` 写是 `1080 − 837 = 243`。

> `SettingsProfile` 的卡片容器要写 `top 188`（不是 193）——它的 itemlayout 里
> 卡片本身有 `<top>5</top>`，`188 + 5 = 193` 才对齐。其它页面没有这个偏移，直接写 193。

**为什么是 28**：PVR 那页的设置行用 `<include>NaraSettingsRow</include>`，
它自带 `<textoffsetx>28</textoffsetx>`，所以容器从 525 起、**文字实际从 553 起**。

**判断规则：容器里有没有 `NaraSettingsRow`**

| 容器内容 | 容器 left / width | 文字落点 |
|---|---|---|
| **有** `NaraSettingsRow`（设置行） | **525 / 1315** | 525 + 28 = **553** |
| **没有**（卡片、纯 label、进度条） | **553 / 1259** | **553** |

⚠️ **28 只能加一次**。容器放到 553、里面又是 `NaraSettingsRow`，文字会跑到 581，
比 PVR 右 28px（2026-10-27 踩过，用户拿 PVR 截图对比才发现）。

⚠️ **28 只补水平方向，纵向一律 193 / 644**。2026-10-28 修 `SettingsProfile` 时发现
`grouplist id=9001` 被写成了 `top 161 / h 708` —— 明显是把 `189/652` 连 top 一起减 28、
height 又加 56 的结果。那两行设置比 PVR 页高 32px，用户一眼看出"四周空隙没对齐"。
**横向用 `NaraSettingsRow` 就减 28，纵向永远不跟着动。**

各页实际取值：

| 页面 | 做法 |
|---|---|
| `SettingsCategory.xml`（播放器/媒体/界面/网络/系统/PVR） | 容器 525 / 1315；行和标题都带 textoffsetx=28 → 553 |
| `SettingsProfile.xml` | **两个容器分开**：设置行 `grouplist id=9001` → **525 / 1315 / top 193 / h 644**；卡片 `panel id=2` → **553 / 1259 / top 188 / h 649**（卡片 itemlayout 自带 `top=5`，188+5=193 才对齐；高度别小于 660 的那套算法——现在卡片缩到 90% 后 2 行只要 594，够用） |
| `SettingsSystemInfo.xml` | 纯 label / textbox，没有行 include → **553 / 1259** |
| `EventLog.xml` | 列表矩形 **525 / 1315 / top 193 / h 644**，行内第一个控件 `left=28` → 视觉落在 553 |

- 内容矩形右下角 = `1840, 837`；用 `bottom` 写是 `1080 − 837 = 243`。
- 纵向也统一成 48：原来上下只有 16，2026-10-27 按用户要求改成 48。
- **不要拿 `AddonBrowser.xml`（插件管理）当基准**：面板 `1355 × 830`，
  左侧栏下半区被插件详情占用，和设置页不是一套版式。
- 帮助条分工：
  | 页面 | 控件 | 内容 |
  |---|---|---|
  | SettingsCategory | `textbox id=6` | Kodi 设置窗口自动填当前项说明 |
  | SettingsProfile | `textbox id=6` + `$VAR[NaraSettingsProfileHelpVar]` | **id=6 在这一页不会被自动填（实测空白）**，必须自己绑；按焦点切 31734/31735 |
  | EventLog | `label id=70` + `textbox id=71` | 标题 = `ListItem.Label`，正文 = `Property(Event.Description)` |
  | SettingsSystemInfo | 无 | 没有"当前项"，底部 y 555–885 已被内存/CPU 浮层占用 |

其它踩过的坑：`SettingsSystemInfo` 的 grouplist 曾只有 370 高，装不下 12 行（合计 564），
最后 4 行被截断；`textbox id=30` 与 `group id=102` 的 `bottom` 曾是 545/80，
内容溢出到 y=1000（超出面板 115px）。都已修正。

---

# 附：环境、验证与素材规格（原 docs/HANDOVER.md 合并而来）

## 2. 环境与路径

| 项 | 值 |
|---|---|
| 源码 | `D:\下载\AI\skin.mistuary`（分支 `universal`，与 `origin/main` 同源） |
| 实机皮肤目录 | `C:\Users\liwl\AppData\Roaming\Kodi\addons\skin.mistuary` |
| 实机 Kodi | **22.0-RC1**（build version code `21.90.901`，build 20260927） |
| 日志 | `C:\Users\liwl\AppData\Roaming\Kodi\kodi.log` |
| Python（带 Pillow） | `C:\Users\liwl\AppData\Local\Programs\Python\Python312\python.exe` |
| 贴图打包 | `python tools/xbt_tool.py pack`（662 张 → 7.6 MB） |

> 实机 Kodi 会随用户升级而变（BETA2 → RC1 就是一次）。看版本别看本文档，
> 看 `kodi.log` 首行：`Starting Kodi (22.0-RC1 (21.90.901) Git:...)`。

**部署命令**（改完代码必须同步，用户靠这个实机验证）：

```powershell
$src = "D:\下载\AI\skin.mistuary"
$dst = "C:\Users\liwl\AppData\Roaming\Kodi\addons\skin.mistuary"
robocopy $src $dst /MIR /XD .git .workbuddy-ai __pycache__ /XF *.pyc .gitignore /NJH /NJS /NDL /NP /NFL
```

- 退出码 0–7 都算成功；`/MIR` 会删掉目标端多余文件（包括本地的 `build/`）。
- **不要写成 .ps1/.bat 脚本文件**（源码路径含中文，脚本编码会出问题），直接执行命令。
- 贴图改过要重新 `pack` 并重启 Kodi；只改 XML 也要重启（皮肤在启动时加载）。

---
## 5. 验证（现在就能跑）

```bash
cd /d "D:\下载\AI\skin.mistuary"
set PY="C:\Users\liwl\AppData\Local\Programs\Python\Python312\python.exe"

%PY% -m unittest discover -s tools -p "test_*.py"     # 期望 59 项全绿
%PY% tools/audit_skin.py --strict                      # 期望 EXIT=0
%PY% tools/gen_techflag_vars.py --check                # 期望"与 map 同步"
%PY% tools/xbt_tool.py unpack media/Textures.xbt -o %TEMP%\xbt_check   # 期望 751/751
```

实机检查（重启 Kodi 后）：

```bash
grep -c "LoadTTF: Couldn't load" %APPDATA%\Kodi\kodi.log        # 期望 0（改之前 3525）
grep -c "invalid include definition" %APPDATA%\Kodi\kodi.log    # 期望 0
```

> **陷阱：同步完必须重启 Kodi，否则日志骗人。**
> 2026-10-26 那次部署（10:51）时 Kodi 从 09:59 就在跑，`kodi.log` 里一直是旧的
> 94 条字体错误 + 2 条 include 错误，看起来像"没修好"，其实只是运行时还在用旧皮肤。
> 11:35 重启后两项立刻归零。
> 判断方法：`kodi.log` 首行的 `Starting Kodi` 时间必须**晚于**部署时间。

**实测结果（2026-10-26 11:35 重启，Kodi 22.0-RC1）**：

| 检查项 | 结果 |
|---|---|
| `LoadTTF: Couldn't load` | **0**（修复前 3525） |
| `invalid include definition` | **0**（修复前 2，均为 `ChannelManagerList`） |
| 单元测试 | **58 项全绿** |
| `audit_skin.py --strict` | 退出码 **0**；缺失 include/变量/字体/贴图/字符串全 0；皮肤设置 66 读 / 68 写，有读无写 0、有写无读 0 |
| `gen_techflag_vars.py --check` | 与 map 同步 |

日志里剩余的无害噪声（不用管）：

- `libraryart/<分类名>.png` 加载失败 —— 皮肤按"先 png 后 jpg"试两种扩展名，
  而 `libraryart/` 里只有 jpg，所以每个分类必然报一条 png 缺失，jpg 正常。
  只有 `临时` 是连 jpg 都没有（用户自己的分类没配封面）。
- `special://masterprofile/Thumbnails/...` 失败 —— Emby 插件缩略图，与皮肤无关。
- `EMBY.emby.http: Websocket receive interrupted` —— 网络，与皮肤无关。

1. 字体变成 Inter（中文正常、粗体正常）
2. PVR → 分组管理，左右两个频道列表都能出频道
3. 首页「文件」里点不同文件源卡片，进对应目录（配两个源测）
4. 播放中按 `O`，「显示输出」那行有值（`System.ScreenMode`）
5. 详情页技术标识：22 上 `4K UHD` / `DOLBY VISION`；21 上 `4K` / `DOLBYVISION`，
   **不能出现 `$MAP[` 原文**

想在 21 上验：装个 **Kodi 21.2 便携版**（解压即用，不动现有配置），
把皮肤拷到它的 `portable_data/addons/` 下跑一遍。

---
### 6.4 已修：`<texture fallback="...">` 在官方 Kodi 上完全无效（原 69 处）

**事实**：`CGUIControlFactory::GetTexture`（`GUIControlFactory.cpp:424-455`）只解析
`border` / `infill` / `flipx` / `flipy` / `diffuse` / `colordiffuse` / `background` /
`mipmap` / `subpixel`。**没有 `fallback`**。

全仓库搜 `fallback` 只有两处是真的：
- `<label fallback="...">`（`GUIControlFactory.cpp:690`，信息标签取不到值时的兜底文字）——有效；
- `CTextureManager` 里 "check all fallbacks" 指的是**贴图搜索目录**，不是占位图。

官方 wiki 的 [Texture Attributes](https://kodi.wiki/view/Texture_Attributes) 也只列了上面那几个。

**后果**：`<texture fallback="DefaultVideo.png">$INFO[ListItem.Art(thumb)]</texture>`
在取不到图时**什么也不画**，占位图不会出现。

**现状：69 处已全部改写（2026-10-26），`audit_skin.py` 报 0 类。**
（`<texture fallback>` 是原魔改内核的扩展属性，官方版没有；`<label fallback>` 是官方属性。）

改法分三条路线，以后再加新图控件照这个来：

| 路线 | 用在哪 | 做法 |
|---|---|---|
| **A. 修变量** | 标签本身是 `$VAR[X]` 的 22 处 | 把变量末尾那条**无条件** `<value>` 改成 `condition="!String.IsEmpty(...)"`，后面补一条占位图 |
| **B. 建变量** | 标签是固定 `$INFO[...]` 的 37 处（20 种组合） | 按 (主标签, 占位图) 建 `NaraImg*` 变量，`<texture>` 改引用 `$VAR[...]` |
| **C. 改参数默认值** | 标签是 `$PARAM[...]` 的 9 处 | 把 include 的默认参数指向带兜底的变量（`NaraImgIconOrFolder` / `NaraImgIconOrTvShows` / `NaraImgArtThumbOrIcon`） |

**踩坑提醒**：
- 变量是**自上而下取第一条成立的 `<value>`**。无条件值放在中间或末尾会挡住后面的兜底，
  必须先把最后那条改成条件式再补兜底。
- 带格式参数的标签（`$INFO[ListItem.ActualIcon,flags/...,.png]`）要用**第一个参数**
  做空值判断，不能把整串塞进 `String.IsEmpty()`。
- `$PARAM[...]` 没法判断空值，所以只能在参数默认值/调用点做兜底，不要试图加垫底控件——
  这些控件的 `aspectratio` 多是 `keep`，垫底图会从四周露出来。

---

### 6.5 素材规格：`libraryart/` 分类封面

- **推荐 640 × 360（16:9）**。卡片本身是 320 × 180，用 2 倍是为了焦点放大时不糊；
  再大纯属浪费——2026-10-26 之前那批是 1920 × 1080，24 张共 19.16 MB，
  压到 640 × 360 后只有 1.24 MB（JPEG q86 + progressive，等比居中裁剪不变形）。
- 原图备份在 `.workbuddy-ai/backup/libraryart-originals/`（该目录被 git 忽略，
  也不会同步到实机之外的地方）。
- 这批图**不入库**（`.gitignore` 里排除 `libraryart/*.jpg|png`），发布包里也没有，
  所以终端用户装上后看到的是文件夹图标——这是设计如此，`libraryart/README.txt` 已说明。
- 内置目录**只认 .jpg**（自定义封面目录 png/jpg 都支持）。
