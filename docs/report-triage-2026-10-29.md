# 外部校验报告分诊与修复计划（2026-10-29）

> **交接用快照，不是长期规范。** 输入是 [`skin.mistuary_report.txt`](skin.mistuary_report.txt)
> （生成于 2026-10-29 16:44，**456 errors / 448 warnings**），分诊基于
> `e68fcad`（更新报告那次提交）附近的代码。仓库有并行开发，执行前先看
> `git status` / `git log`，不要照抄本文的提交快照。

---

## 0. 一句话结论

**这不是 456 个 bug。** 按校验器目标版本（`addon.xml` 声明 `xbmc.gui 5.17.0` = Kodi 21）
拆开后：

| 分类 | 数量 | 结论 |
|---|---:|---|
| Windows 工作区 CRLF | 88 E | 假阳性；仓库索引是 LF |
| Kodi 22 才有的标签 | 220 E | 双轨设计；21 上为空，22 上正常 |
| Kodi 22 才有的窗口名 | 96 E | 双轨设计；`dialogselectvideo/audio/subtitle`、`RadioProviders` |
| Kodi 22 的 `<map>` | 1 E | 刻意使用；21 走文字分支 |
| **真问题（error 级）** | **约 51 E** | 见 §2 |
| `Redundant ... same as default` | 310 W | 无行为影响，不建议追 |
| 其余 warning | 约 138 W | 字体、无效标签、仓库规范、翻译等 |

**新版报告的变化（相对 445/458 那版）：**

- 新增了 `Variables` 分类：9 个旧的 `FocusLayoutTextColor*` 变量已没人用
- 新增 7 条 `Invalid multiple tags`：`DialogPVRGroupManager` 和 `SettingsItemCommon` 重复设置字体/宽度
- 新增 6 条 `no info '0' / '110'`：上一轮音乐 OSD 的 `lyrics_id` 数字条件导致，**这是真 bug**
- 旧的 `DialogMusicInfo` 5 条死导航和 570/190 遮罩问题已随重做消失
- 旧的 445/458 分诊结论已过时，以本文为准

### 复核修正（2026-10-29 晚）

- **`<scroll>` 从 P1 降到 P2，本轮不做。** 当前 8 个显式
  `Control.HasFocus(...)` 调用点都在 `focusedlayout`，但 include 嵌套后确实可能把
  运行时条件带进 `itemlayout`。完整修法要把标题拆成“聚焦可滚 / 非聚焦不滚”两套
  label，收益只是长标题滚动，成本 12 处 + 布局错位风险，不值。
- 并行开发已修：`MusicPlayer.BMP`、`Player.FilenameAndPath`、AddonBrowser 3 处
  `<fallback>`、EventLog 2 处空 `onclick`、`VideoStreamCount` → `HasVideoVersions`、
  新增 `.gitattributes`。
- 报告里的 3 条空 `onclick` 已降到 **1 条**（`DefaultDialogButton` 的默认参数仍为空）。
- `--dead` 仍有 **9 个** `FocusLayoutTextColor*` 死变量，尚未清。

**P1 / P2 执行后（2026-10-29 晚）：** 上面两项都已清零——空 `onclick` 改为 `noop`，
9 个死变量删除，`--dead` 归零。详见 §2 / §5。

---

## 1. 报告分诊

### 1.1 文件完整性（88 E / 43 W）

- **88 条 CRLF 全是假阳性。** `git ls-files --eol` 索引里是 `i/lf`，本机
  `core.autocrlf=true` 把工作区检出成 CRLF。加 `.gitattributes` 即可，不要全库 renormalize。
- 24 条 `libraryart/*.jpg` 非 ASCII：按分类名匹配的运行时设计，改名会失效。
- 19 条 `tools/*.py`：`release.yml` 排除 `tools/`，不进发布包。

### 1.2 IDS（101 E / 3 W）

- **96 E 是 Kodi 22 窗口名**：`dialogselectvideo/audio/subtitle`（22 的 12300–12302）
  和 `RadioProviders`（22 的 10713）。21 上条件恒假，属双轨。
- **4 E 是真死导航**：`DialogPVRInfo:128`（ID 50）、`DialogVideoManager:67`（9001）、
  `PlayerControls:140-141`（1000 ×2）。
- **1 E 是歌词窗口名**：`MusicVisualisation:14` 的
  `Dialog.Close(script-cu-lrclyrics-main)` 无法解析。
- 3 W 是“用窗口 id 也能工作，但推荐用名字”，纯风格。

### 1.3 Variables（9 E）

`Variables.xml` 里 9 个旧变量没人引用：

```text
FocusLayoutTextColor10Var / 12Var / 13Var / 20Var / 120Var
FocusLayoutTextColor450Var / 451Var / 9010Var / 9000Var
```

XML 已经改走 `NaraDialogFocusLayoutTextColor*`（Includes_DialogGlass.xml）。
**注意**：`6 / 11 / 50 / 51 / 52 / 53 / 55` 仍在用，别一起删。

### 1.4 XML Validation（257 E / 385 W）

错误构成：

| 项 | 数量 | 判定 |
|---|---:|---|
| v22 标签（HdrDetail / SubtitleCodec / TitleExtraInfo / EpisodePart / ChannelLogo / PVR* / MediaProviders 等） | 220 | 双轨，21 上为空 |
| `MusicPlayer.BMP` | 4 | **真错字**，应为 `MusicPlayer.BPM` |
| `no info '0' / '110'` | 6 | **真 bug**，音乐 OSD 的 `lyrics_id` 数字条件 |
| `<scroll>` 传条件表达式 | 12 | **真错**，长标题不滚动 |
| `Player.DecodedFilenameAndPath` | 2 | **不存在的标签**（21/22 都没有） |
| `VideoPlayer.SubtitleIsExternal` | 1 | **不存在的标签** |
| 空 `<onclick>` | 3 | **真错（低）** |
| `height min/max="100%"` | 2 | 无效写法（低） |
| 重复标签（PVRGroupManager） | 7 | **真错**，后写的 font/radiowidth 被忽略 |
| 窗口名 | 96 | 见 §1.2 |
| CRLF | 88 | 见 §1.1 |
| `<map>` | 1 | 双轨 |

警告构成：

| 项 | 数量 | 判定 |
|---|---:|---|
| `Redundant ... same as default` | 310 | 无行为影响，不建议追 |
| image `align/aligny`、fixedlist、grouplist 等无效标签 | 72 | 多为无效/22-only |
| 未用字体 | 4 | `font23_narrow` / `font27_narrow` / `font_clock` / `font_MainMenu` |
| 未翻译标签 | 3 | `MUSIC INFO · 音乐信息`（我们）、RPU / BL / EL、Git |
| 其它 | 其余 | 仓库规范 / XSP 编码 / 窗名写法 |

---

## 2. 真问题清单

按优先级排；行号按 16:44 报告，执行前重新 grep。

### P0：功能 / 日志（已完成）

| 数 | 位置 | 影响 | 修法 | 状态 |
|---:|---|---|---|---|
| 6 | [`xml/Includes_MusicPlayer.xml:99`](../xml/Includes_MusicPlayer.xml#L99) 等 | `String.IsEqual($PARAM[lyrics_id],0)` 里的 `0/110` 被 Kodi 当作 info 标签；OSD ↓ 导航条件不可靠 | 改成直接传目标 ID：`<param name="ondown">87</param>`，歌词窗口传 `110`；不再用数字条件 | ✅ 已改 |
| 4 | [`xml/Includes.xml:555`](../xml/Includes.xml#L555) | `MusicPlayer.BMP` 拼错，BPM 徽标不显示 | 改 `MusicPlayer.BPM` | ✅ 当前代码已是 BPM（报告滞后） |
| 2 | [`xml/DialogPlayerProcessInfo.xml:460`](../xml/DialogPlayerProcessInfo.xml#L460) | `Player.DecodedFilenameAndPath` 不存在，路径永远空 | 改 `Player.FilenameAndPath` | ✅ 当前代码已正确（报告滞后） |
| 1 | [`xml/MusicVisualisation.xml:14`](../xml/MusicVisualisation.xml#L14) | `Dialog.Close(script-cu-lrclyrics-main)` 无法解析，离开播放页报错 | 删掉；插件自己会关 | ✅ 已删 |
| 1 | [`xml/MusicVisualisation.xml:195`](../xml/MusicVisualisation.xml#L195) | `Window.IsVisible(script-cu-lrclyrics-main.xml)` 不可靠 | 改用 `Window(home).Property(culrc.guirunning)` | ✅ 已改 |

### P1：导航 / 可感知（已完成）

| 数 | 位置 | 影响 | 修法 | 状态 |
|---:|---|---|---|---|
| 4 | [`DialogPVRInfo.xml:128`](../xml/DialogPVRInfo.xml#L128)、[`DialogVideoManager.xml:67`](../xml/DialogVideoManager.xml#L67)、[`PlayerControls.xml:140`](../xml/PlayerControls.xml#L140) | `onup/onleft` 指向不存在的控件 ID | 删无效 `onX`，让 Kodi 自动导航 | ✅ 已删（PVRInfo `50`、VideoManager `9001`、PlayerControls `1000`×2） |
| 1 | [`DialogVideoManager.xml:37`](../xml/DialogVideoManager.xml#L37) | `ListItem.DecodedFileNameAndPath` 22 才有，21 路径空白 | 直接改 `ListItem.FileNameAndPath`：21/22 都有，显示内容对版本列表足够，免去 `$EXP` 双分支 | ✅ 已改 |
| 1 | [`Variables.xml:865`](../xml/Variables.xml#L865) | `VideoPlayer.SubtitleIsExternal` 不存在，外部字幕前缀永不成立 | 删掉该分支；`31716 "External"` 因此暂时没有引用，保留在 `.po` 里备用 | ✅ 已删 |

> `<scroll>` 12 条暂缓，理由见上面的“复核修正”。

### P2：清理 / 文案（已完成）

| 数 | 位置 | 问题 | 状态 |
|---:|---|---|---|
| 9 | `Variables.xml:1360-1453` | 旧 `FocusLayoutTextColor*` 死变量，见 §1.3 | ✅ 已删（保留 6/11/50/51/52/53/55）；`--dead` 归零 |
| 4 | `Font.xml` | `font23_narrow` / `font27_narrow` / `font_clock` / `font_MainMenu` 无人引用 | ✅ 已删 |
| 7 | `DialogPVRGroupManager.xml:185-227` | 6 个 `<font>` + 1 个 `<radiowidth>` 和 `SettingsItemCommon` 重复；Kodi 忽略后写的，删掉即与实际一致 | ✅ 已删，实际生效值（font26 / radiowidth72）不变 |
| 1 | `DialogMusicInfo.xml:83` | `MUSIC INFO · 音乐信息` 硬编码；加 `31779` 后走 `$LOCALIZE` | ✅ 中英 `.po` 均已加 31779 |
| 1 | `Includes_Buttons.xml:178` | `DefaultDialogButton` 的 `onclick` 默认参数为空；EventLog 两处已由并行改动改 `noop` | ✅ 默认值改 `noop` |
| 2 | `View_52_IconWall.xml:26`、`Custom_1116_OSDPlaylistShelf.xml:36` | `sharedglassbackdrop` / `defaultfocusposition` 不是 Kodi 标签 | ✅ 已删 |
| 3 | `AddonBrowser.xml:30/116/155` | `<fallback>` 不是 image 子标签；并行已改用 `NaraImgAddonBrowserIcon` / `NaraImgAddonListItemIcon` | ✅ 并行已修 |
| 12 | `NaraSearchPosterLayout` | `<scroll>` 运行时条件；完整修需拆两套 label，**暂缓** | ⏸ 本轮不做 |

### P3：降噪（可选）

- 加 `.gitattributes` 清 88 条 CRLF。
- 310 条冗余默认值、50 条 image `align`、15 条 fixedlist：不建议现在动。
- `libraryart` 中文名 / `tools/` / 官方仓库规范：走 GitHub Releases 不影响。
- XSP 的 `&` / `+` URL 编码：归 `script.mistuary.helper` P0，不在皮肤层硬修。

---

## 3. Kodi 21 兼容：v22 项的实际降级

| 位置 | 21 上的表现 | 建议 |
|---|---|---|
| `Includes_SettingsDialog.xml:168` `VideoStreamCount` | 读 0，视频版本按钮永远禁用 | ✅ 并行已改 `HasVideoVersions` |
| `DialogVideoManager.xml:37` `DecodedFileNameAndPath` | 路径空白 | ✅ 已改 `FileNameAndPath` |
| `Variables.xml:1487` `ChannelLogo` | 台标取不到；但 `DialogPVRInfo` 的可见条件也依赖该标签，21 上会自动落到 `Art(thumb)` / `EpgEventIcon` 分支。`MyPVRGuide` 的台标在 21 上为空 | 低价值：只补 texture 变量不会显示，改可见条件风险大于收益；**不改**，文档记录 |
| `VideoPlayer.AudioLanguageEx` | 播放信息页音轨语言行空 | ✅ 已加 `$VAR[NaraAudioLanguageVar]`：22 用 Ex，21 回退 `VideoPlayer.AudioLanguage` |
| `VideoPlayer.SubtitleCodec` | 字幕徽标没有编码，语言仍显示 | 接受为 v22 增强 |
| `PVRClientName` / `PVRInstanceName` / `PVR.ClientCount` / `PVRGroupOrigin` | PVR 信息行部分为空 | 接受，或只在 22 显示 |
| `HdrDetail` / `TitleExtraInfo` / `EpisodePart` / `MediaProviders` / `Bookmarks` / `SubtitleName` | 为空/隐藏，多数有兜底 | 抽查标题、PVR 行 |
| `<map>` / v22 窗口名 | 可能产生日志噪声 | 用 Kodi 21.2 便携版验一次：不能出现 `$MAP[` 原文 |

**策略仍建议 A：保持 Kodi 21+**，v22 功能继续双轨；不要为了报告全绿删掉
`<map>`、HDR、PVR 扩展标签。

---

## 4. 校验器误报 / 不要动的项

1. **CRLF 88 条**：不是仓库问题，见 §1.1。
2. **v22 标签/窗口/`<map>` 317 条**：删了会失去技术标识图标、HDR 详情、
   PVR 客户端信息、书签、`MediaProviders` 等。
3. **310 条 `Redundant`**：无行为影响，清理只产生大 diff。
4. **image `align/aligny` 50 条、fixedlist 15 条**：无效/22-only，当前不影响显示；
   想报告干净可脚本化清理，否则不建议动。
5. **`<enable>`（slider）和 `pulseonselect`（spincontrol）**：是 `GUIControlFactory`
   的通用标签，校验器按控件白名单误判，不要删。
6. **`<fallback>`**：只有 `<label fallback="...">` 属性有效；image 子标签要改。
7. **`libraryart` 非 ASCII / `tools/` / xbt 旁有源图 / 缺 screenshot**：
   只影响官方仓库，不影响 GitHub Releases。`release.yml` 已排除 `tools/`、`docs/`
   和松散图片。

---

## 5. 执行批次

### 第 1 批：P0（已完成，待实机验收）

```text
xml/Includes_MusicPlayer.xml       lyrics_id 数字条件 → 直接 ondown 参数
xml/Includes.xml                   MusicPlayer.BMP → BPM
xml/DialogPlayerProcessInfo.xml    Player.FilenameAndPath
xml/MusicVisualisation.xml         删无效 Dialog.Close；改用 culrc.guirunning
```

验收：

```bash
python tools/audit_skin.py --strict
python tools/audit_skin.py --orphans
python tools/audit_skin.py --dead
python -m unittest discover -s tools -p 'test_*.py'
python tools/sync_to_kodi.py --loose
```

实机看：OSD 的 ↓ 在歌词/按钮/进度条之间是否按预期走；BPM 是否出现；
播放信息页路径是否有值；离开音乐页 `kodi.log` 不再出现
`Window Translator: Can't find window`。

### 第 2 批：P1（已完成）

- `DialogPVRInfo.xml` / `DialogVideoManager.xml` / `PlayerControls.xml`：
  删 4 个死导航。
- `DialogVideoManager.xml`：路径统一用 `ListItem.FileNameAndPath`（21/22 通用）。
- `Variables.xml`：删 `VideoPlayer.SubtitleIsExternal` 死分支。
- **不做 `<scroll>`**：完整修法要拆两套 label，本轮暂缓。

### 第 3 批：P2（已完成）

- 删 9 个旧 `FocusLayoutTextColor*` 变量。
- 删 4 个未用字体。
- `DialogPVRGroupManager.xml`：删 6 个重复 `<font>` + 1 个 `<radiowidth>`。
- `DialogMusicInfo.xml`：`MUSIC INFO` 走 `31779`。
- `Includes_Buttons.xml`：`DefaultDialogButton` 默认 `onclick` 改 `noop`（EventLog 已修）。
- 删 2 个死标签；AddonBrowser 3 处 `<fallback>` 已由并行改动修好。

### 第 4 批：P3（可选）

- `.gitattributes` 已由并行改动加入；确认后不再需要。
- 如需报告全绿，再脚本化清 310 条冗余默认值和无效标签；
  一次只清一类，`git diff` 复核。
- 重新跑校验器；预期 error 从 456 降到约 317（只剩 v22 双轨 + CRLF）。

---

## 6. 验收基线（P1 / P2 后实测）

```text
外部报告         456 E / 448 W（修前快照，需重跑）
audit --strict   EXIT=0
audit --orphans  0 张
audit --dead     0 变量 / 0 include
unittest         59 项 OK
Textures.xbt     751 张 / 7.2 MB
```

执行前以 `git status` / `git log origin/main..main` 为准。

---

## 7. 证据索引

- 报告原文：`docs/skin.mistuary_report.txt`（16:44，456 E / 448 W）。
- CRLF：`git ls-files --eol` 索引 `i/lf`；`core.autocrlf=true`。
- v22 标签：Kodi master `xbmc/GUIInfoManager.cpp` 的 `HdrDetail` / `TitleExtraInfo` /
  `EpisodePart` / `ChannelLogo` / `SubtitleCodec` / `PVRClientName` /
  `PVRInstanceName` / `MediaProviders` / `Bookmarks` / `VideoStreamCount` /
  `PVR.ClientCount` 均为 `@skinning_v22`。
- v22 窗口名：Kodi master `xbmc/input/WindowTranslator.cpp`。
- 音乐参数：`Includes_MusicPlayer.xml` 的 `String.IsEqual($PARAM[lyrics_id],0)`；
  校验器把 `0/110` 当 info 标签，报告 6 条 `no info '0'/'110'`。
- 歌词窗口：插件 `script.cu.lrclyrics` 的 `WIN = xbmcgui.Window(10000)`，
  `lib/gui.py` 设置/清除 `culrc.guirunning`。
- `MusicPlayer.BMP`：Kodi 标签是 `MusicPlayer.BPM`（v19 起）。
- `Player.DecodedFilenameAndPath`：21/22 都没有；`Player.FilenameAndPath` 有。
- `VideoPlayer.HasVideoVersions`：v21。
- `<fallback>`：`CGUIControlFactory::GetTexture` 不解析 `fallback`。
- `<scroll>`：允许 `0/disabled/enabled/false/no/off/on/true/yes`。
