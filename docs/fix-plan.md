# Mistuary 修复方案（详细版）

日期：2026-10-26　基线：`universal` / `1c2e239`（= `origin/main`）
配套文档：`docs/skin.mistuary.md`（外部审查报告）、`docs/mistuary-plan.md`（历史计划）

---

## 0. 摘要

| 状态 | 内容 |
|---|---|
| ✅ 已完成 | **字体已落地**：`fonts/Inter-Unicode-Regular.ttf`（Inter 4.000 + 16502 汉字，OFL），`Font.xml` 47 处已指向它 |
| ✅ 已完成 | **`ChannelManagerList` 补 `<definition>`**、**`System.CurrentDisplayMode` 死标签**、**过时测试断言** |
| ✅ 已完成 | **Kodi 21 兼容**：胶囊双轨渲染 + OSD 静态变量 + `nara_kodi21` 探测 + 自检关卡（§2.6） |
| ✅ 已完成 | 首页文件源导航 + 8 个空槽位清理、`release.yml` 版本判断与 CI 关卡、`xbt_tool` 边界与测试（§3.2–3.4） |
| 📄 新增文档 | `docs/skin-contracts.md`：窗口属性 / 皮肤设置 / 控件 ID 的隐式契约清单 |

审查报告列出的问题**已全部处理**，另加三处报告没发现的（`ChannelManagerList`、
字体、`System.CurrentDisplayMode`）。

---

## 1. 字体（已落地）

### 1.1 为什么必须自带中文字体

先排除一个常见误解：**Kodi 没有"字形级回退"**。

`GUIFontManager::LoadTTF`（Kodi 21.2）找字体的顺序是——皮肤 `fonts/` → `special://home/media/Fonts` →
`special://xbmc/media/Fonts` → `resource.font.*` 插件，**都是按文件名找一个完整文件**；
一旦找到就整份加载，缺字时不会去别的字体里借字形（`GUIFontTTF` 里只有 FreeType 的合成粗体，
没有 fallback 字体列表）。所以皮肤用的那个文件必须**自己包含 CJK**。

这解释了当前为什么中文没变豆腐块：`Inter-Unicode-Regular.ttf` 找不到 → 回退 `arial.ttf`，
而 Kodi 自带的那个 `arial.ttf`（4.6 MB）实际是 **DejaVu Sans 2.32 + 16502 个汉字**的合并版，
不是 Windows 的 Arial。代价是：拉丁字母变成 DejaVu，Inter 的设计全丢了。

### 1.2 候选对比

| 方案 | 拉丁 | 中文 | 体积 | 授权 | 评价 |
|---|---|---|---|---|---|
| **A. Inter-Unicode（已采用）** | Inter 4.000 | 16502 汉字 | 4.9 MB | OFL 1.1 | 和原设计完全一致，就是 Estuary N 用的那份 |
| B. 自己合并 Inter + Noto Sans SC | Inter | 全量 CJK | 8–12 MB | OFL | 授权最干净，但需要 fontTools 构建步骤，度量要手工对齐 |
| C. 只放 Inter（拉丁） | Inter | 无 → 豆腐块 | 0.3 MB | OFL | **不可行**，见 1.1 |
| D. 引用 `resource.font.robotocjksc` 里的文件名 | Inter | 16502 汉字 | 0 MB | OFL | 可行但要用户装插件，缺插件就退回 DejaVu |

选 A 的理由：文件就是 B 的成品（jurialmunkey 已经把 Inter 和中文字形合好并放在
`resource.font.robotocjksc` 里，本项目 `THIRD_PARTY_NOTICES.md` 里已有来自同一作者的素材），
零构建、零 XML 改动、观感和原设计一致。D 留作备选（省 4.9 MB，但增加一个外部依赖）。

### 1.3 已做的事

```
fonts/Inter-Unicode-Regular.ttf   4 944 416 B   Inter 4.000（Version 4.000;git-a52131595）
fonts/OFL.txt                     4 380 B       SIL OFL 1.1 全文
xml/Font.xml                      47 处 <filename> 改为 Inter-Unicode-Regular.ttf
THIRD_PARTY_NOTICES.md                         新增 Inter 章节（来源/版本/授权/重建方法）
addon.xml                                      <license> 追加 "SIL OFL 1.1"
```

字体文件**用原始文件名**，不缩写：`Inter-Unicode-Regular.ttf` 就是
`resource.font.robotocjksc` 里那份文件的本名，`Font.xml` 47 处引用同步改成它。
Kodi 的查找路径是 `special://skin/fonts/<filename>`，文件名与 `<filename>` 完全一致即可。

### 1.4 已验证

- 字形覆盖：皮肤 `language/*/strings.po` + `README.md` + 全部 `xml/*.xml` 里用到的
  **697 个非 ASCII 字符，字体缺 0 个**；常用中文标点 `“”。，、：；！？—` 全在。
- 粗体：Kodi 用 FreeType 的 `FT_Outline_Embolden` 合成（`GUIFontTTF.cpp:973-975`），
  所以只有一个 Regular 文件时 `[B]` 标签依然会变粗，不需要单独的 Bold 文件。
- 体积：发布 zip 从 ~10 MB 涨到 ~15 MB（`media/` 里的松散 PNG 不进包，`Textures.xbt` 7.7 MB）。

### 1.5 如果你想更省体积

- 子集化到 GB2312（6763 字）能压到 ~2.5 MB，但片名里的生僻字会变豆腐块，不建议。
- 换 D 方案（引用插件里的文件名、仓库不存字体）：文件名已经和插件里的一致，
  只要删掉 `fonts/` 并在 `addon.xml` 加
  `<import addon="resource.font.robotocjksc" version="0.0.3" optional="true"/>` 即可。
  缺插件时自动退回 DejaVu（中文仍在，只是不是 Inter）。

### 1.6 你需要做的

重启 Kodi（或切换皮肤）后看日志：

```bash
grep -c "LoadTTF: Couldn't load" %APPDATA%\Kodi\kodi.log     # 应该是 0
```

改之前是 3525 条。字体文件不需要重打包 `Textures.xbt`（字体不走贴图包）。

---

## 2. Kodi 21 兼容性：能做，但要先认清代价

### 2.1 现在的矛盾

| 位置 | 说的是 |
|---|---|
| `addon.xml` | `<import addon="xbmc.gui" version="5.17.0"/>` → 允许装在 **Kodi 21** |
| `README.md:5` | "面向未做任何修改的官方 **Kodi 21 Omega 及以上**版本" |
| 你的实机 | **Kodi 22.0-BETA2**（`kodi.log` 首行） |

于是所有 22 专属写法在你的机器上都不会暴露，但 21 用户装上就会踩。

### 2.2 实测：这个皮肤用了哪些 22 专属能力

把 Kodi 21.2 与 master 的 `xbmc/GUIInfoManager.cpp`（标签名总表）和
`guiinfo/GUIInfoLabels.h`（标签枚举）逐条比对，皮肤实际踩到的是：

**（1）`$MAP` / `<map>` —— 全局性，影响 5 张映射表**

| 位置 | 用法 |
|---|---|
| `Includes_VideoTechnicalFlags.xml:5,15,24,41,77` | 5 个 `<map>` 定义（分辨率/HDR/DV 档位/视频编码/音频编码，共 100 条） |
| 同上 `:157,161,173,207,211` | 5 处 `$MAP[...]` |
| `Includes_VideoOSD.xml:23,82` | 2 处 `$MAP[...]` |

Kodi 21.2 的 `CGUIInfoLabel::Parse` 只认 `$INFO/$ESCINFO/$VAR/$ESCVAR`（`infoformatmap[]`，第 278–281 行），
`<map>` 也不在 `GUIIncludes` 的加载范围（只处理 `constant/variable/include`）。
`$MAP` 是 2026-07-27 才进 master 的（commit 标题 "[guilib] Skinning: Add $MAP[] label syntax"）。
→ **在 21 上这些标签会原样显示成 `$MAP[NaraTechnicalHdrTextMap,ListItem.HdrType]` 这串字**。

**（2）13 个只有 22 才有的标签 —— 逐条比对结果**

| 标签 | 用在哪 | 21 上的后果 | 21 可替代 |
|---|---|---|---|
| `ListItem.HdrDetail` / `VideoPlayer.HdrDetail` | 技术标识（DV 档位 P7 FEL…） | 空 → 档位胶囊不显示 | 无（21 根本没这信息） |
| `ListItem.ChannelLogo` | 频道列表/EPG 台标 | 空 → 回退 `Art(thumb)`/`EpgEventIcon` | `ListItem.Art(thumb)` |
| `ListItem.MediaProviders` | PVR 信息对话框 | 空 → 该行自动隐藏 | 无 |
| `ListItem.PVRClientName` | PVR 信息 / 分组管理 | 空 → 该行隐藏 | 无 |
| `ListItem.PVRInstanceName` | 同上 | 空 | 无 |
| `ListItem.PVRGroupOrigin` | 分组管理 | 空 | 无 |
| `ListItem.DecodedFileNameAndPath` | 播放器进程信息 | 空 | `Player.FileNameAndPath` 近似 |
| `ListItem.TitleExtraInfo` | EPG 标题修饰 | 空 → 走其它分支 | 无 |
| `ListItem.EpisodePart` | 剧集 `S01E01/2` | 空 → 少一段 | 无 |
| `VideoPlayer.SubtitleCodec` | OSD 字幕胶囊 | 空 → 胶囊隐藏 | 无 |
| `VideoPlayer.SubtitleName` | OSD 字幕名 | 空 | `VideoPlayer.SubtitlesLanguage` |
| `VideoPlayer.AudioLanguageEx` | 播放器进程信息 | 空 | `VideoPlayer.AudioLanguage` |
| `VideoPlayer.SubtitleLanguageEx` | OSD 字幕语言 | 空 | `VideoPlayer.SubtitleLanguage` |

好消息：这些用法绝大多数都被 `!String.IsEmpty(...)` 包着，**21 上只是"这一行/这个胶囊不出现"，
不会错位、不会报错**。真正刺眼的只有 `$MAP` 那一处（显示原始表达式）。

**（3）顺手发现的死标签（21/22 都没有）**

`DialogPlayerProcessInfo.xml:76` 用了 `$INFO[System.CurrentDisplayMode]`，
两个版本的标签表里都查不到这个名字 → 这一行在你的机器上**现在就是空的**。
这是审查报告没发现的第 3 个漏报。**已修**：改为 `$INFO[System.ScreenMode]`
（= `RESOLUTION_INFO::strMode`，形如 `1920x1080 @ 60.00 - Full Screen`，21/22 都有）。

### 2.3 静态表核查的局限

我把皮肤用到的 178 个标签名整体过了一遍：161 个能在 21 的名称表里找到，
另外 17 个里有 13 个是上面确认的 v22 新增、3 个是我的解析器误抓（`Skin.String(...)` 之类）、
1 个是死标签。**但静态表只能证明"名字在不在"，证明不了"值对不对"**——
21 上的最终确认还是要装一个 Kodi 21 便携版跑一遍日志。

### 2.4 "干脆不支持 21" 的四条常见理由，逐条看

| 理由 | 实际情况 |
|---|---|
| "21 快过时了" | 22 还是 BETA，**21 是当前稳定版**，绝大多数用户装在 21 上。1.0.0 首发就排除稳定版，等于自断一半用户 |
| "$VAR 写法太啰嗦" | 啰嗦的是机器，不是人。map 仍然是唯一数据源，脚本生成，加新编码只改 map |
| "要维护两套代码" | **不是两套**。`$VAR` + 条件链在 21 和 22 上都有效，改写完只有一套 |
| "改 addon.xml 声明 22+ 最省事" | 确实最省事（1 行），但会让 21 用户直接装不上，且与 README 的承诺冲突 |

我的结论：**没有技术理由不做 21 兼容**，唯一代价是一次性改写 + 13 个字段在 21 上留白。

### 2.5 结论：能做，但不是"生成一堆变量"那么简单

先把一个容易想错的方案排除掉。最直觉的做法是"把 5 张 map 展开成 `<variable>` 条件链"，
但**这条路走不通**：技术标识胶囊的标签名是动态的——

```xml
<param name="item_prefix" value="Container($PARAM[list_id]).ListItem" />
<param name="resolution"  value="$PARAM[item_prefix].VideoResolution" />
```

`<variable>` 的 `<value>` 里只能写**写死**的标签名，而这里的标签名随容器 id 变化。
实测皮肤里会出现的技术标识前缀有 **20 多个**（首页 13 个 widget 行、搜索 7 个容器、
视图 50/51/501、详情页的 `ListItem`），要按前缀生成就是 20+ 套 × 5 张表 ≈ 2000 行，
而且每加一个首页 widget 就得重新生成——不可维护。

所以真正可行的是 **双轨渲染**：胶囊里放两个按钮，一个用 `$MAP`（22），一个用原始值（21），
用 `System.BuildVersion` 探测切换。22 保持 `DOLBY DIGITAL`、`4K UHD`，21 显示
`DOLBYVISION`、`AC3` 这种原值。**改动集中在 1 个 include + 5 个参数，不碰架构。**

| 路线 | 做法 | 工作量 | 21 上的效果 |
|---|---|---|---|
| A. 放弃 21 | `addon.xml` 改 `5.18.0` | 5 分钟 | 装不上 |
| **B1. 双轨渲染（已实施）** | 胶囊加一条原始值分支 + 版本探测 | 半天 | 能看，技术标识显示原值 |
| B2. 按前缀生成变量 | 20+ 套变量 | 不可维护 | 名称完整，但每加 widget 要重生成 |
| C. 全部改原始值 | 删掉 `$MAP` | 30 分钟 | 22 也失去友好名称 |

### 2.6 已实施的方案（B1）

#### 2.6.1 版本探测表达式

`xml/Includes.xml`：

```xml
<!-- Kodi 21 没有 $MAP[] 标签查表（22 才加），技术标识胶囊在 21 上退化为原始值。 -->
<expression name="nara_kodi21">String.StartsWith(System.BuildVersion,21)</expression>
```

为什么用 `System.BuildVersion` 而不是"探测某个标签是否存在"：22 新增的标签
（`HdrDetail`、`SubtitleCodec`…）在没有对应数据时也是空字符串，**无法区分"不支持"和"没数据"**；
而 21 是唯一没有 `$MAP` 的版本，用主版本号判断是确定的。将来 23 也走 `$MAP` 分支，不会过期。

#### 2.6.2 胶囊双按钮

`xml/Includes_VideoTechnicalFlags.xml` 的 `NaraTechnicalTextPill` 现在有两个按钮，
共用同一张圆角底，靠 `visible` 二选一：

```xml
<control type="button">
    <label>[B][UPPERCASE]$PARAM[flag_label][/UPPERCASE][/B]</label>   <!-- $MAP，22 -->
    <visible>$PARAM[flag_visible] + !$EXP[nara_kodi21]</visible>
</control>
<control type="button">
    <label>[B][UPPERCASE]$PARAM[flag_label_raw][/UPPERCASE][/B]</label> <!-- 原值，21 -->
    <visible>$PARAM[flag_visible] + $EXP[nara_kodi21]</visible>
</control>
```

关键前提：**grouplist 布局会跳过隐藏子控件**（`GUIControlGroupList.cpp` 的布局循环里
`if (!control->IsVisible()) continue;`，焦点链也只收可见控件），所以隐藏的那个不会留空位。

5 个调用点各补一条 `flag_label_raw`：

| 胶囊 | 22 用（`$MAP`） | 21 用（原值） |
|---|---|---|
| 分辨率 | `NaraTechnicalResolutionTextMap` | `$INFO[$PARAM[resolution]]` |
| HDR | `NaraTechnicalHdrTextMap` | `$INFO[$PARAM[hdr_type]]` |
| DV 档位 | `NaraTechnicalDolbyVisionProfileTextMap` | `$INFO[$PARAM[hdr_detail], ]` |
| 视频编码 | `NaraTechnicalVideoCodecTextMap` | `$INFO[$PARAM[video_codec]]` |
| 音频编码 | `NaraTechnicalAudioCodecTextMap` | `$INFO[$PARAM[audio_codec]]` |

#### 2.6.3 标签名固定的地方直接换成变量（21/22 都显示友好名称）

OSD 的两处 `$MAP` 用的是**写死的** `VideoPlayer.*` 标签，不涉及容器 id，
所以可以用条件 `<variable>` 完整还原映射，21 上也有 `DOLBY VISION`、`DOLBY DIGITAL`：

```xml
<variable name="VideoOSDHdrTypeVar">
    <value condition="!String.IsEmpty(Player.Process(hdrsource))">$INFO[Player.Process(hdrsource)]</value>
    <value condition="!String.IsEmpty(VideoPlayer.HdrType)">$VAR[NaraTechHdrPlayer]</value>
    <value>SDR</value>
</variable>
```

变量由 `extras/gen_techflag_vars.py` 从 `<map>` 生成（5 个变量、约 100 条 `<value>`），
写进 `Variables.xml` 的标记区间，`--check` 供 CI 校验同步。`String.IsEqual` 是
`EqualsNoCase`，所以 map 里 `7fel`/`7FEL` 这类大小写重复条目生成时会自动去重。

> 一句话总结：**标签名静态的地方用变量（两版都漂亮），标签名动态的地方用双轨（22 漂亮、21 原值）。**

#### 2.6.4 自检关卡

`extras/audit_skin.py` 现在会：
- 扫到 `$MAP[` / `$ESCMAP[` 时报出来，**若同时没有 `nara_kodi21` 表达式就返回非 0**；
- 只检查 31000–31999 的皮肤自有字符串（不再把 41 个 Kodi 内置 ID 当缺失）；
- 用解析后的节点判断魔改属性（注释里的 `slotlist` / `texturebackground` 不再误报）；
- 真错误返回 1（原来恒为 0），`--strict` 时软提示也算失败。

当前输出：缺失 include / 变量 / 字体 / 贴图 / 字符串 **全部 0**，魔改属性 0 类，
`$MAP` 1 类（已守卫）。

### 2.7 21 上的取舍（写进 README）

| 项目 | Kodi 22 | Kodi 21 |
|---|---|---|
| 技术标识（分辨率/HDR/编码） | `4K UHD`、`DOLBY VISION`、`DOLBY DIGITAL` | `4K`、`DOLBYVISION`、`DOLBY DIGITAL`（OSD 仍完整） |
| 杜比视界档位（P7 FEL） | 显示 | 不显示（21 没有 `HdrDetail`） |
| 字幕名 / 字幕编码 / 音频语言 Ex | 显示 | 退化为空或普通语言名 |
| PVR 客户端名 / 实例名 / 分组来源 / 媒体提供方 | 显示 | 整行自动隐藏 |
| 台标 `ChannelLogo` | 显示 | 回退 `Art(thumb)` / `EpgEventIcon` |


## 3. 其余修复项

### 3.1 `ChannelManagerList` 缺 `<definition>`（P1，功能坏）—— **已修**

`xml/Includes_PVR.xml:171`：include 直接写控件、没有 `<definition>`，却带了 `<param>`。
Kodi 的 `GUIIncludes.cpp:221-227` 对这种写法直接**丢弃整条 include**并告警，
所以 `DialogPVRGroupManager.xml` 的两个频道列表（id 11/12）完全不渲染。

```xml
<include name="ChannelManagerList">
    <param name="header_id">21</param>
    <param name="list_id">11</param>
    <param name="scrollbar_id">71</param>
    <param name="onleft">noop</param>
    <param name="onright">noop</param>
    <param name="focus_textcolor">$VAR[NaraDialogFocusForegroundVar]</param>
    <definition>
        <!-- 原来的 grouplist / image / list / scrollbar 四段控件整体缩进一级搬进来 -->
    </definition>
</include>
```

关于参数声明：Kodi 只在**"有 `<param>` 却没有 `<definition>`"**这一种情况下丢弃整条 include
（`GUIIncludes.cpp:221-227`）。参数本身**不声明也能用**——调用点传的 `<param>` 会和声明的默认值
合并后再替换 `$PARAM[...]`（`ResolveIncludes` 里 `params.insert(defaultParams...)`）。
所以真正的 bug 只有缺 `<definition>` 这一个；我把另外 5 个参数补成默认值，只是给直接调用留兜底。

验收：日志不再出现 `invalid include definition`；PVR → 分组管理左右两个列表都能出频道。

**实施记录（2026-10-26）**
- `Home.xml` 删掉 `ActivateWindow(filemanager,$ESCINFO[ListItem.Property(homepath)],return)`，
  交给 `content target="filemanager"` 的官方导航（Kodi 的 `CDirectoryProvider::GetTarget`
  用条目**真实路径**跳转，能保留 SMB 凭据；`ListItem.FolderPath` 会 `GetWithoutUserDetails()` 掉凭据）。
- 常用文件夹 8 槽位整块删除：`HomeFileShortcutItems`、`HomeFolderCardLayout`、
  面板 `15020`、标题 `$LOCALIZE[13398]`、以及 `Home.FileReturnControl` 里对 15020 的分支。
  导航改为 `15010` 到底后 `noop`；`HomeFocusedFilePathVar` 只保留 15010 分支。
- `test_nara_settings_navigation.py` 的焦点回归用例去掉 15020。

### 3.2 首页文件源跳转（P1）—— 已完成

**a) 文件源卡片**（`Home.xml:961`）：`ListItem.Property(homepath)` 在 `sources://files/`
条目上永远是空——`SourcesDirectory` 构造条目时只设了 path/label/art，
`CFileItem(CMediaSource)` 也不设任何 property（已核对源码）。而 `homepath`
在 Kodi 21/22 的标签表里都**根本不存在**，它只是本皮肤自己给"常用文件夹"定义的属性名。

修法（二选一，先试第一个）：

```xml
<!-- 首选：删掉 onclick，交给 content target="filemanager" 的官方导航 -->
<!-- <onclick>ActivateWindow(filemanager,$ESCINFO[ListItem.Property(homepath)],return)</onclick> -->

<!-- 备选：显式跳转，用真实路径标签（21/22 都有 LISTITEM_FOLDERPATH） -->
<onclick>ActivateWindow(filemanager,$ESCINFO[ListItem.FolderPath],return)</onclick>
```

**b) 常用文件夹 8 个槽位**（`Includes_Home.xml:104-190`）：这里的 `homepath`
是皮肤自己用 `<property>` 定义的，读得到，但值是 `skin-home-root:/xxx` ——
这个协议只有魔改内核认识，官方 Kodi 打开会失败。改成直接传真实路径：

```xml
<property name="homepath">$INFO[Skin.String(Home.FileShortcut.1.Path)]</property>
<onclick>ActivateWindow(filemanager,$ESCINFO[ListItem.Property(homepath)],return)</onclick>
```

**c) 这 8 个槽位没有任何写入入口**（全仓库搜不到 `SetString(Home.FileShortcut.*)`，
只有读取和右键"清空"），是永远空着的死功能。二选一：

- 删掉（推荐，先清理干净）：移除 `HomeFileShortcutItems` + `Home.xml` 的 15020 面板；
- 补入口：设置中心加"首页文件夹"页，用 `Skin.SetString` 写 `.Path/.Label/.DisplayPath`。

### 3.3 发布版本判断（P2）—— 已完成

`release.yml:48` 的 `git log -1 --skip=1 -- addon.xml` 跳过的是"上一次改 addon.xml 的提交"，
不是"上一次 push"。只改 README 的提交也会让它取到升版前的版本号 → `changed=true` → 重发同一版本。

```yaml
      - name: Check version change
        id: check
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          set -euo pipefail
          NEW="${{ steps.meta.outputs.version }}"
          BASE="${{ github.event.before }}"
          if [ -z "${BASE}" ] || [ "${BASE}" = "0000000000000000000000000000000000000000" ] \
             || ! git cat-file -e "${BASE}^{commit}" 2>/dev/null; then
            BASE="$(git rev-parse HEAD^ 2>/dev/null || true)"
          fi
          OLD=""
          if [ -n "${BASE}" ]; then
            OLD="$(git show "${BASE}:addon.xml" 2>/dev/null | python -c \
              'import sys,xml.etree.ElementTree as ET; print(ET.fromstring(sys.stdin.read()).get("version"))' || true)"
          fi
          echo "基线版本: ${OLD:-<无>} / 本次版本: ${NEW}"
          if [ "${OLD}" = "${NEW}" ]; then
            echo "changed=false" >> "$GITHUB_OUTPUT"
          elif gh release view "v${NEW}" >/dev/null 2>&1; then
            echo "v${NEW} 已发布过，跳过（避免同名附件被覆盖）"
            echo "changed=false" >> "$GITHUB_OUTPUT"
          else
            echo "changed=true" >> "$GITHUB_OUTPUT"
          fi
```

**实施记录**：版本判断已改为比较 `github.event.before`（workflow_dispatch 时退回 `HEAD^`），
并加了"该 tag 的 Release 已存在就跳过"的闸门；`pillow==11.3.0` 已固定；
`rsync` 加了 `--exclude='build/'`；新增 `test` job（unittest + audit --strict + 生成器 --check），
`build` 依赖它。action 仍用大版本标签——查 SHA 的接口当天取不到可信值，留着下次做，
不建议凭记忆手写。

### 3.4 XBT 解包路径穿越（P2）—— 已完成

`xbt_tool.py:421` 直接 `os.path.join(output_dir, *path.split('/'))`。加校验：

```python
def _safe_target(root: str, rel: str) -> str:
    if rel.startswith(('/', '\\')) or (len(rel) > 1 and rel[1] == ':'):
        raise ValueError('拒绝绝对路径条目: %r' % rel)
    parts = [p for p in rel.replace('\\', '/').split('/') if p not in ('', '.')]
    if any(p == '..' for p in parts):
        raise ValueError('拒绝父目录跳转条目: %r' % rel)
    root_real = os.path.realpath(root)
    target = os.path.realpath(os.path.join(root_real, *parts))
    if os.path.commonpath([target, root_real]) != root_real:
        raise ValueError('条目越出输出目录: %r' % rel)
    return target
```

再补输入边界校验：`len(data) >= 9`、`count <= 10000`、每次 `unpack_from` 前校验偏移、
`data_off + packed_size <= len(data)`、`w*h*4 == unpacked_size`、`w/h <= 8192`。
测试：`../escaped.png`、`/abs.png`、`C:\x.png`、`a/../../b.png` 各一条，断言抛错且目录外无新文件。

**实施记录**：已加 `_safe_target()`（拒绝绝对路径 / 盘符 / `..`，再用 `realpath` + `commonpath`
兜底）与 `_need()` 边界检查（头部、条目头、帧头、帧数据偏移；`MAX_ENTRIES=10000`、
`MAX_DIM=8192`、`MAX_UNPACKED=64MB`、`w*h*4 == unpacked_size`）。
新增 `extras/test_xbt_tool.py`（10 条用例）。回归验证：用新校验解包现有
`media/Textures.xbt`，**662/662 全部通过**，没有误杀真实数据。

### 3.5 测试与自检工具（P2）—— 已完成

- `extras/test_nara_search_navigation.py:369-371`：期望值 `$VAR[GlassTint_regular]` → `glass_regular`。
- `extras/audit_skin.py` 已改：
  - 字符串只查皮肤自有区间（31000–31999），42 个假阳性归零；
  - 魔改属性改用解析后的节点判断，注释里的 `70127` / `slotlist` / `texturebackground` 不再误报；
  - 真错误返回 1（原来恒为 0），`--strict` 时软提示也算失败；
  - 新增"仅 Kodi 22 支持的写法"检查 + `$MAP` 缺 `nara_kodi21` 守卫时报错。
- 当前结果：缺失 include / 变量 / 字体 / 贴图 / 字符串 **全部 0**，魔改属性 0 类，
  `$MAP` 1 类（已守卫），退出码 0；25 项单元测试全绿。
- 待办：CI 加 `test` job（`unittest` + `audit_skin.py --strict` + `gen_techflag_vars.py --check`），
  `build` 依赖它。

### 3.6 零碎（P3）—— 已完成

- `release.yml:87` 加 `--exclude='build/'`，或把 staging 挪到 `$RUNNER_TEMP`。
- `docs/mistuary-plan.md` 顶部标"历史记录"，已修项（autoscroll 大小写、`$VAR` 颜色、圆角蒙版）打 ✅。
- README 补"21 与 22 的能力差异"表（即 §2.2 的 13 条）。

---

## 4. 落地顺序

1. ✅ **字体**：已落地并同步实机，重启后看日志归零。
2. ✅ **止血**：`ChannelManagerList`、死标签、测试断言 —— 已完成。
3. ✅ **21 兼容**：双轨渲染 + OSD 变量 + 自检关卡 —— 已完成，待 21 实机验收。
4. ✅ **功能**：3.2 首页文件源导航（删失效 onclick）+ 8 槽位整块移除。
5. ✅ **发布链路**：3.3 `release.yml` 版本判断 + `build/` 排除 + `test` job、3.4 `xbt_tool` 边界与测试。

## 5. 验收清单

- [ ] `kodi.log` 无 `LoadTTF: Couldn't load`（字体已就位）
- [ ] `kodi.log` 无 `invalid include definition`
- [ ] PVR 分组管理器左右列表都能出频道
- [ ] 播放中按 `O`，"显示输出"那行有值（`System.ScreenMode`）
- [ ] 详情页技术标识显示 `4K UHD` / `DOLBY VISION`（22），21 上显示 `4K` / `DOLBYVISION` 且**不出现 `$MAP[` 原文**
- [ ] 首页点不同文件源卡片，进的是对应目录（配两个源测）
- [ ] `python -m unittest discover -s extras` 全绿
- [ ] `python extras/audit_skin.py --strict` 返回 0
- [ ] 连续两次 push（第二次只改 README）只产生一个 Release
- [ ] 发布 zip 能装进 Kodi 21 与 22，字体、中文、粗体都正常

---

## 附录：本次核验的证据

| 结论 | 证据 |
|---|---|
| `$MAP` 是 22 才有的 | Kodi 21.2 `guiinfo/GUIInfoLabel.cpp:270-281`（只有 4 种格式）；master 有 `$MAP[`/`$ESCMAP[`；commit "Add $MAP[] label syntax" 2026-07-27 |
| `<map>` 21 不加载 | `GUIIncludes.cpp:178-243` 只处理 `constant/variable/include` |
| 13 个标签 22 专属 | `GUIInfoManager.cpp` 名称表 + `GUIInfoLabels.h` 枚举逐条比对（21=0 / 22≥1） |
| `homepath` 不是标签 | 21/22 的 `GUIInfoManager.cpp` 都没有 `"homepath"`；`SourcesDirectory.cpp:49` 只 `new CFileItem(share)` |
| 源条目没有 property | `FileItem.cpp:392-414` 的 `CFileItem(CMediaSource)` 只设 path/label/art/lock |
| `ListItem.FolderPath` 可用 | `GUIInfoManager.cpp:7022` + `11355` 返回 `item->GetPath()`（去凭据） |
| 字体全挂 | 实机 `kodi.log` 3525 条 `LoadTTF: Couldn't load ... (inter.ttf)` |
| 日志里的 `arial.ttf` 是 DejaVu | 字体 name 表：`family=DejaVu Sans`，16502 汉字 |
| 粗体是合成的 | `GUIFontTTF.cpp:973-975` `FT_Outline_Embolden` |
| include 缺 definition 会被丢弃 | `GUIIncludes.cpp:221-227` |
| 42 个字符串是假阳性 | 逐个比对 Kodi 21 `strings.po`：41 个内置、1 个在注释里 |
| `String.IsEqual` 不区分大小写 | `GUIInfoManager.cpp:11001` `EqualsNoCase` |
