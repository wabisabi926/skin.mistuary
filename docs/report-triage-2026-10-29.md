# 外部校验报告分诊与修复计划（2026-10-29）

> **交接用快照，不是长期规范。** 输入是 [`skin.mistuary_report.txt`](skin.mistuary_report.txt)
> （生成于 2026-10-29 12:49，445 errors / 458 warnings），分诊基于 `f3426cc` / v1.2.1。
> 之后仓库又有并行提交（音乐库背景兜底、卡片格宽度、本分诊文档本身等），
> **执行前以 `git log` / `git status` 为准**，不要照抄本文的提交快照。
>
> 当前工作区若还有别人的未提交改动，不要把 `Includes.xml` / `MyMusicNav.xml` 之类的
> 文件混进修复提交。

---

## 0. 一句话结论

**这不是 445 个 bug。** 按校验器的目标版本（`addon.xml` 声明 `xbmc.gui 5.17.0` = Kodi 21）
拆开后：

| 分类 | 数量 | 结论 |
|---|---:|---|
| Windows 工作区 CRLF | 91 E | 假阳性；仓库里存的是 LF |
| Kodi 22 才有的标签 | 221 E | 双轨设计；21 上为空，22 上正常 |
| Kodi 22 才有的窗口名 | 96 E | 双轨设计；`dialogselectvideo/audio/subtitle`、`RadioProviders` |
| Kodi 22 的 `<map>` | 1 E | 刻意使用；21 走文字分支 |
| **真问题（error 级）** | **约 36 E** | 见 §2 |
| `Redundant ... same as default` | 322 W | 无行为影响，不建议追 |
| 其余 warning | 约 136 W | 字体、无效标签、仓库规范、翻译等 |

真正建议动的是：**§2 的 P0/P1 + §3 的 3 个 Kodi 21 回退点**。
其余 v22 项不要为了“让报告变绿”删掉——那会删掉技术标识图标、HDR 详情、
PVR 扩展和 `<map>` 渲染。

---

## 1. 报告分诊

### 1.1 文件完整性（91 E / 43 W）

- **91 条 CRLF 全是假阳性。** `git ls-files --eol` 显示索引里全部是 `i/lf`，
  本机 `core.autocrlf=true` 把工作区检出成了 CRLF。校验器扫的是工作区，所以报错。
  - 处理：加 `.gitattributes`（`* text=auto eol=lf`），**不要**为了这个跑全库 renormalize；
    索引本来就是 LF。用干净 clone / `git archive` 跑校验器也不会再报。
- 24 条 `libraryart/*.jpg` 非 ASCII 文件名：**按分类名匹配的运行时设计**，
  改名会让封面匹配失效。只有提交官方仓库时才需要另做映射。
- 19 条 `tools/*.py`：`release.yml` 的 Stage addon 已排除 `tools/`，**不进发布包**。

### 1.2 IDS（106 E / 3 W）

- **96 E 是 Kodi 22 窗口名**：`dialogselectvideo` / `dialogselectaudio` /
  `dialogselectsubtitle`（Kodi 22 的 12300–12302）和 `RadioProviders`
  （Kodi 22 的 10713）。已核对 Kodi master 的 `xbmc/input/WindowTranslator.cpp`：
  这些名字在 22 才注册，21 上条件恒假。**属双轨，不是错误。**
- **9 E 是真正的死导航**：见 §2 第 6 条。
- 3 W 是“用窗口 id 也能工作，但推荐用名字”（`10025` / `12016` / `10502`），
  纯风格，不必改。

### 1.3 XML Validation（247 E / 397 W）

错误构成：

| 项 | 数量 | 判定 |
|---|---:|---|
| `HdrDetail`（各容器 / `ListItem` / `VideoPlayer`） | 约 140 | v22 标签，21 上为空 |
| `VideoPlayer.SubtitleCodec` | 23 | v22 标签 |
| `TitleExtraInfo` | 14 | v22 标签 |
| `EpisodePart` | 9 | v22 标签 |
| `ChannelLogo` | 9 | v22 标签 |
| `MusicPlayer.BMP` | 6 | **真错字**，应为 `MusicPlayer.BPM` |
| `PVRClientName` / `PVRInstanceName` / `PVRGroupOrigin` / `PVR.*` | 14 | v22 标签 |
| `MediaProviders` / `SubtitleName` / `AudioLanguageEx` / `VideoStreamCount` / `Bookmarks` | 9 | v22 标签 |
| `DecodedFileNameAndPath` | 1 | v22 标签（21 上空白） |
| `Player.DecodedFilenameAndPath` | 2 | **不存在的标签**（21/22 都没有） |
| `VideoPlayer.SubtitleIsExternal` | 1 | **不存在的标签** |
| `<scroll>` 传条件表达式 | 12 | **真错** |
| 空 `<onclick>` | 3 | **真错（低）** |
| `height min/max="100%"` | 2 | 无效写法（低） |

警告构成：

| 项 | 数量 | 判定 |
|---|---:|---|
| `Redundant ... same as default` | 322 | 皮肤 `Defaults.xml` 已设默认值，控件里重复写；无行为影响 |
| image 上的 `<align>/<aligny>` | 51 | 无效标签，当前无效果，可选清理 |
| fixedlist 的 `startmovement/endmovement` | 10 | Kodi 22 才认，21 忽略 |
| fixedlist 的 `<aligny>` | 5 | 无效标签 |
| 未用字体 | 3 | 可删 |
| `<texture>` 风格的 `<fallback>` | 3 | **真错**，见 §2 第 4 条 |
| `libraryart` 非 ASCII / tools / 仓库规范 / 翻译 | 其余 | 见 §1.1 / §4 |

---

## 2. 真问题清单

按优先级排；行号是报告/基线快照，执行前重新 `grep` 确认。

| 优先级 | 位置 | 影响 | 修法 | 状态 |
|---|---|---|---|---|
| P0 | [`xml/MusicVisualisation.xml:12`](../xml/MusicVisualisation.xml#L12)、[`:194`](../xml/MusicVisualisation.xml#L194) | 实机 `kodi.log` 已报 `Window Translator: Can't find window script-cu-lrclyrics-main`；`onunload` 关不掉歌词窗口，右侧占位层判断也不可靠 | 删掉 `Dialog.Close(script-cu-lrclyrics-main)`：插件自己在离开可视化窗口时会关（`script.cu.lrclyrics/lib/gui.py:479`）。可见性改用插件写在 home 窗口的 `culrc.guirunning` 属性（`lib/utils.py:34`、`gui.py:336/398`） | 待办 |
| P0 | [`xml/Includes.xml:556`](../xml/Includes.xml#L556) | `MusicPlayer.BMP` 拼错，音乐播放页 BPM 徽标永远不显示 | 改 `MusicPlayer.BPM`（Kodi 19+ 标签） | 待办（等并行改动） |
| P0 | [`xml/DialogPlayerProcessInfo.xml:460`](../xml/DialogPlayerProcessInfo.xml#L460)、[`:463`](../xml/DialogPlayerProcessInfo.xml#L463) | `Player.DecodedFilenameAndPath` 在 21/22 都不存在，播放信息页路径永远空 | 改 `Player.FilenameAndPath` | 待办 |
| P0 | [`xml/AddonBrowser.xml:30`](../xml/AddonBrowser.xml#L30)、[`116`](../xml/AddonBrowser.xml#L116)、[`155`](../xml/AddonBrowser.xml#L155) | `<fallback>` 不是 image 的子标签；Kodi 只支持 `<label fallback="...">` 属性。插件图标缺失时空白 | 用现有 `NaraImg*` 变量兜底，或加一层条件默认图 | 待办 |
| P0 | [`xml/Includes_Search.xml:314`](../xml/Includes_Search.xml#L314)、[`329`](../xml/Includes_Search.xml#L329) 及调用点 | `<scroll>` 只接受 `true/false` 等字面量，传 `Control.HasFocus(...)` 会被判非法，搜索/首页长标题不滚动（12 处） | 给 include 增加独立 `scroll` 参数（默认 `false`），聚焦布局传 `true`；不要把条件表达式塞进 `<scroll>` | 待办 |
| P1 | [`xml/DialogMusicInfo.xml:418-421`](../xml/DialogMusicInfo.xml#L418)、[`DialogPVRInfo.xml:137`](../xml/DialogPVRInfo.xml#L137)、[`DialogVideoManager.xml:71`](../xml/DialogVideoManager.xml#L71)、[`PlayerControls.xml:140-141`](../xml/PlayerControls.xml#L140) | 9 个 `onup/onleft` 指向不存在的控件 ID，方向键跳转失效 | 删掉无效 `onX`，让 Kodi 按几何自动导航；或按实际布局重指 | 待办 |
| P1 | [`xml/EventLog.xml:166`](../xml/EventLog.xml#L166)、[`189`](../xml/EventLog.xml#L189)、[`xml/Includes_Buttons.xml:167`](../xml/Includes_Buttons.xml#L167) | 空 `<onclick>` 在 13 个窗口里产生错误 | 默认 `onclick` 改 `noop`；EventLog 两处也改 `noop` | 待办 |
| P2 | [`xml/Font.xml:77`](../xml/Font.xml#L77)、[`142`](../xml/Font.xml#L142)、[`239`](../xml/Font.xml#L239) | 3 个字体定义无人引用 | 删除 | 待办 |
| P2 | [`xml/View_52_IconWall.xml:26`](../xml/View_52_IconWall.xml#L26)、[`Custom_1116_OSDPlaylistShelf.xml:36`](../xml/Custom_1116_OSDPlaylistShelf.xml#L36) | `sharedglassbackdrop` / `defaultfocusposition` 不是 Kodi 标签，死代码 | 删除 | 待办 |
| P2 | [`xml/Includes_Home.xml:68`](../xml/Includes_Home.xml#L68) | `<height min="100%" max="100%">auto</height>` 的 min/max 不是整数 | 删 min/max，或改成合法数值；当前基本无效 | 待办 |

---

## 3. Kodi 21 兼容：报告归为“v22 正常”，但实际有降级

| 位置 | Kodi 21 上的表现 | 建议 |
|---|---|---|
| [`xml/Includes_SettingsDialog.xml:168`](../xml/Includes_SettingsDialog.xml#L168) `VideoPlayer.VideoStreamCount` | 21 读 0，「视频版本」按钮永远禁用 | 改用 `VideoPlayer.HasVideoVersions`（21/22 都有） |
| [`xml/DialogVideoManager.xml:37`](../xml/DialogVideoManager.xml#L37) `ListItem.DecodedFileNameAndPath` | 21 上路径空白 | 建变量按 `$EXP[nara_kodi21]` 分支：22 用 Decoded，21 用 `ListItem.FileNameAndPath` |
| [`xml/Variables.xml:1524`](../xml/Variables.xml#L1524) `ListItem.ChannelLogo` | 21 上台标退化成 `DefaultTVShows.png` | 补 `ListItem.Art(thumb)` / `ListItem.Icon` fallback，实机确认 |
| `VideoPlayer.SubtitleCodec` | 21 上字幕徽标没有编码，语言仍显示 | 接受为 v22 增强，文档写清；不要为 21 硬造标签 |
| `PVRClientName` / `PVRInstanceName` / `PVR.ClientCount` / `PVRGroupOrigin` | 21 上 PVR 信息行部分为空 | 接受，或只在 22 显示这些字段 |
| `HdrDetail` / `TitleExtraInfo` / `EpisodePart` / `MediaProviders` / `Bookmarks` / `SubtitleName` | 21 上为空/隐藏，多数有兜底 | 抽查标题、PVR 行是否会变空；其余接受 |
| `<map>` 与 v22 窗口名 | 21 上可能产生 `Window Translator` 日志噪声 | 用 Kodi 21.2 便携版验一次：不能出现 `$MAP[` 原文；日志可接受少量噪声 |

**兼容策略三选一：**

- **A（推荐）保持 Kodi 21+**：修 3 个 21 回退点，v22 功能继续双轨；报告里的
  318 条 v22 项明确标为“预期”。
- **B 只支持 Kodi 22**：把 `xbmc.gui` 升到 5.18，报告里 318 条立刻合法，
  但 21 用户装不上。
- **C 冲官方仓库**：还要把 `tools/` 移出源码、`media/` 只留 xbt、`libraryart`
  改 ASCII、补 `<screenshot>`，工作量另算，不建议现在做。

---

## 4. 校验器误报 / 不要动的项

1. **CRLF 那 91 条**：不是仓库问题，见 §1.1。
2. **v22 标签、窗口名、`<map>`**：不要为了消错删掉。删了会同时失去：
   技术标识图标（`<map>`）、HDR 详情、PVR 客户端/实例信息、视频版本计数、
   书签、`MediaProviders` 等。
3. **322 条 `Redundant ... same as default`**：控件写了和 `Defaults.xml` 相同的值，
   Kodi 接受，无行为影响。清理只会产生大 diff，收益低。
4. **image 上的 `<align>/<aligny>`（51 条）**：确实是无效标签，但当前也没效果；
   如果要“报告干净”可以脚本化删除，每步 diff 复核，否则不建议动。
5. **`<enable>`（slider）和 `pulseonselect`（spincontrol）不是误报？**
   - 这两个是 `GUIControlFactory` 的通用控件标签（master 的
     `GUIControlFactory.cpp:1012` / `1179`），Kodi 会读，校验器按控件类型白名单
     误判成了无效。**不要删。**
6. **`<fallback>` 是另一回事**：Kodi 的 `GetTexture` 不解析 `fallback`，
   `<fallback>` 作为 image 子标签完全无效（只有 `<label fallback="...">` 属性有效）。
   这条要修，见 §2 第 4 条。
7. **`libraryart` 非 ASCII、`tools/*.py`、`Textures.xbt` 旁边有源图、缺 screenshot**：
   只影响“提交官方仓库”，不影响 GitHub Releases。`release.yml` 已经排除了
   `tools/`、`docs/` 和松散图片，包内只留 `Textures.xbt`。

---

## 5. 执行批次

### 第 1 批：P0 真 bug（约 1.5 小时）

改这些文件：

```text
xml/MusicVisualisation.xml         歌词窗口关闭 + 可见性
xml/Includes.xml                   MusicPlayer.BMP → BPM（等并行改动落地）
xml/DialogPlayerProcessInfo.xml    Player.FilenameAndPath
xml/AddonBrowser.xml               3 处 <fallback> 改变量兜底
xml/Includes_Search.xml            scroll 参数 + 调用点
xml/Includes_Home.xml              scroll 调用点
xml/View_501_Poster.xml            scroll 调用点
xml/DialogMusicInfo.xml            删除死导航
xml/DialogPVRInfo.xml              删除死导航
xml/DialogVideoManager.xml         删除死导航
xml/PlayerControls.xml             删除死导航
xml/EventLog.xml                   空 onclick → noop
xml/Includes_Buttons.xml           默认 onclick → noop
xml/Font.xml                       删 3 个未用字体
xml/View_52_IconWall.xml           删 sharedglassbackdrop
xml/Custom_1116_OSDPlaylistShelf.xml 删 defaultfocusposition
```

验收：

```bash
python tools/audit_skin.py --strict
python tools/audit_skin.py --orphans
python tools/audit_skin.py --dead
python -m unittest discover -s tools -p 'test_*.py'
python tools/sync_to_kodi.py --loose
```

实机检查 4 件事：

1. 离开音乐播放页，歌词窗口是否关；
2. 音乐 OSD 的 BPM 徽标是否出现；
3. 播放信息页路径是否有值；
4. 搜索/首页长标题聚焦时是否滚动。

`kodi.log` 里不应再出现 `Window Translator: Can't find window`。

### 第 2 批：Kodi 21 回退（约 1.5 小时）

- `xml/Includes_SettingsDialog.xml`：`VideoStreamCount` → `HasVideoVersions`。
- `xml/DialogVideoManager.xml`：路径变量按 21/22 分支。
- `xml/Variables.xml`：台标补 `Art(thumb)` / `Icon` 兜底。
- 装 Kodi 21.2 便携版，验：技术标识不出现 `$MAP[` 原文、版本切换可用、
  PVR 台标、字幕/音轨标签。

### 第 3 批：降噪（可选，约 2 小时）

- 加 `.gitattributes`（`* text=auto eol=lf`）。
- 删 3 个字体、3 个 `<fallback>`、2 个死标签（已含在第 1 批）。
- 如确需报告全绿：脚本化清 322 条冗余默认值和 51 条 image `align/aligny`；
  一次只清一类，`git diff` 复核，避免误伤 `<aspectratio align>`。
- 重新跑外部校验器；预期 error 从 445 降到约 318（剩余全是 v22 双轨）。

### 第 4 批：文档收口

- 等并行改动落地后，修 §6 的文档失真。
- 在 `HANDOVER.md §5.2` 补一张「Kodi 22-only 标签/窗口/`<map>`」清单，
  下次再跑这个校验器可以一眼分诊。

---

## 6. 文档失真（2026-10-29 已处理）

| 位置 | 原先写的 | 处理 |
|---|---|---|
| `HANDOVER.md:28` | 751 张 / 7.1 MB | 已改为 754 张 / 7.3 MB |
| `HANDOVER.md:30` | 还有 1 个未推送提交 `0ebccc5` | 已改为「以 §8.1 的 `git status -sb` 为准」，不再钉提交号 |
| `HANDOVER.md §8.4` | 黑胶、删 24 死变量仍是待办 | 已改成当前三件事：报告 P0/P1、helper、Kodi 21 实机 |
| `HANDOVER.md §8.5` | `--dead` 还有 24 变量 + 6 include | 已改为「应为 0 / 0」 |
| `HANDOVER.md §8.6` | 黑胶暂停回弹、背景兜底仍待决策 | 已删除；保留兼容目标、helper 仓库、token 三项 |
| `pending-work-plan.md` | 基线 `d29a225` / v1.2.0；还剩 3 件事；滚动条待决策 | 顶部已更新到 v1.2.1；①③ 标 ✅；滚动条标 ✅ |

> `HANDOVER.md` 的「三条铁律」是并行开发刚提交的内容，本次只改状态行，没有动那一段。

---

## 7. 并行开发与提交纪律

这个仓库可能有多个 agent 并行改。这份分诊写完后，音乐背景兜底、卡片格宽度、
以及本分诊文档本身都已经被并行提交；随后仍可能出现新的未提交改动。
**每次动手前先 `git status`，只 stage 自己改的文件。**

固定动作：

```bash
git status
git add <自己改的文件>
git diff --cached --name-only   # 核对，出现别人的文件就撤
git commit -F -
```

- **永远不要 `git add -A` / `git commit -a`。**
- **不要擅自 commit / push / 发版**；改完先说明 + 验证结果，等指令。
- 开发期同步实机用 `python tools/sync_to_kodi.py --loose`；
  只有用户明确说“打 tag / 发版”时才 `python tools/xbt_tool.py pack`。

---

## 8. 待决策

1. **兼容目标**：A 保持 Kodi 21+（推荐）/ B 只支持 22 / C 冲官方仓库。
2. **本轮范围**：只做第 1 批 / 第 1+2 批（推荐）/ 连第 3 批降噪一起做。
3. **并行改动**：等对方落地 / 只改互不冲突文件 / 现在全量改（需确认对方已停手）。

---

## 9. 验收基线（写文档时实测）

```text
audit_skin.py --strict   EXIT=0
audit_skin.py --orphans  0 张
audit_skin.py --dead     0 变量 / 0 include
unittest                 58 项 OK
Textures.xbt             754 张 / 7.3 MB
分诊时 main              f3426cc；之后有并行提交（含本分诊文档）
```

> 执行前以 `git status` / `git log origin/main..main` 为准，不要照抄这里的提交快照。

---

## 10. 证据索引

- 报告原文：`docs/skin.mistuary_report.txt`（2026-10-29 12:49，445 E / 458 W）。
- CRLF：`git ls-files --eol` 全部 `i/lf`；`git config --get core.autocrlf` = `true`。
- Kodi 22 标签：Kodi master `xbmc/GUIInfoManager.cpp` 的
  `HdrDetail` / `TitleExtraInfo` / `EpisodePart` / `ChannelLogo` /
  `SubtitleCodec` / `PVRClientName` / `PVRInstanceName` / `MediaProviders` /
  `Bookmarks` / `VideoStreamCount` / `PVR.ClientCount` 均为 `@skinning_v22`。
- Kodi 22 窗口名：Kodi master `xbmc/input/WindowTranslator.cpp`
  （`dialogselectvideo` / `dialogselectaudio` / `dialogselectsubtitle` /
  `radioproviders`）。
- 歌词窗口：`kodi.log` 的 `Window Translator: Can't find window
  script-cu-lrclyrics-main`；插件 `script.cu.lrclyrics` 的 `lib/utils.py`
  `WIN = xbmcgui.Window(10000)`，`lib/gui.py` 设置/清除 `culrc.guirunning`。
- `MusicPlayer.BMP`：Kodi 标签是 `MusicPlayer.BPM`（v19 起就有）。
- `Player.DecodedFilenameAndPath`：Kodi 21/22 都没有；`Player.FilenameAndPath` 有。
- `VideoPlayer.VideoStreamCount`：v22；`VideoPlayer.HasVideoVersions` 是 v21。
- `<fallback>`：Kodi `CGUIControlFactory::GetTexture` 不解析 `fallback`；
  只有 `<label fallback="...">` 有效。
- `<scroll>`：允许值只有 `0/disabled/enabled/false/no/off/on/true/yes`。
