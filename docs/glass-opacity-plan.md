# 浮窗（对话框）不透明度梳理 + 分层方案

> 2026-10-26 全量盘点。目标：默认**透黑**模式下，浮窗既不"糊成一块灰板"，
> 也不"透到能读出下面的字"。
>
> **状态：已实施（第三轮定稿，2026-10-26 14:15）。**
> 86% 太透（能逐条读字）→ 96% 太实（像黑板）→ **最终 92%**。
> 浅色主题押后。三轮踩坑记录见 §5.2 / §7之二 / §7之三。

---

## 一、结论摘要

1. 皮肤里共有 **34 个 `Dialog*.xml` + 12 个 `Custom_11xx` 自定义窗口**，其中 **24 个是"带面板的浮窗"**。
2. 它们的不透明度**完全没有统一标准**，现状横跨 **30% ~ 85%** 四档，同一种视觉语言被拆成了四种。
3. **最严重的一档是 50%**：11 个浮窗只有一层 50% 玻璃面板、**连全屏遮蔽层都没有**（`DialogPVRInfo`、
   `DialogMusicInfo`、`DialogPictureInfo`、`DialogKeyboard`、`DialogSlider`、`DialogPVRChannelGuide`、
   `DialogPVRChannelsOSD`、`DialogPVRGuideControls`、`DialogNotification`、`Custom_1100_AddonLauncher`、
   `Custom_1116_OSDPlaylistShelf`）。底下 50% 的画面是**清晰原图**，文字直接跟海报标题打架。
4. 插件设置页 70%、插件详情页 85% —— 两个"本该一致"的页面差了 15 个百分点，
   而源码注释还写着"两页观感一致"。
5. **加遮蔽层是对的，但单靠遮蔽层会变成"整页压黑"**。真正的解法是三层分工：
   **遮蔽层管"底噪"，面板贴图管"边缘通透"，文字底板管"局部对比度"**。
6. Kodi 皮肤引擎**没有实时模糊**（没有 `<blur>`，`colordiffuse` 只做 RGBA 相乘），
   所以"毛玻璃"必须靠**预渲染贴图自带的 alpha 渐变**来伪造，不能指望运行时滤镜。

---

## 二、技术前提（先钉死能力边界）

| 能力 | 结论 | 依据 |
|---|---|---|
| 实时模糊 / 背景滤镜 | **不存在** | 皮肤引擎只有 `texture` / `colordiffuse` / `border` / `diffuse`，无 filter 节点 |
| `colordiffuse` 语义 | 与贴图 **RGBA 逐通道相乘** | 所以贴图自带的 alpha 渐变会保留，颜色 alpha 只是"上限" |
| 渐变 / 噪点 | **可以**（画进 PNG） | 贴图是 1:1 绘制的，不依赖 9-slice |
| 半透明叠加 | 线性合成：`1 − (1−a)·(1−b)` | 遮蔽层 + 面板 + 底板可以精确算总遮盖率 |
| `<textcolor>` 支持 `$VAR` | **不支持**（整段文字变透明） | 已在项目里踩过，颜色只能走 `colors/*.xml` 主题 |
| `colordiffuse` 支持 `$VAR` | 支持 | `CGUIInfoColor::Parse` |

**推论**：想同时要"透明感"和"可读性"，唯一可控的自由度是
**把不透明度做成"空间上的分布"**——中心实、边缘透。这是本方案的核心。

---

## 三、现状全量清单（默认透黑模式）

合成不透明度 = `1 − (1−遮蔽) × (1−面板)`。

### 3.1 有全屏遮蔽 + 玻璃面板（6 类）

| 窗口 | 全屏遮蔽 | 面板 | 合成 | 判定 |
|---|---|---|---|---|
| `DialogAddonInfo`（插件详情） | `B3000000` 70% | `glass_frosted` 50% | **85.2%** | 勉强 |
| `DialogBackgroundCommons` 系 **20 个调用点** | `overlay_medium` `B3000000` 70% | 50% | **85.2%** | 勉强 |
| `NaraSettingsDialogFrame` 系（`DialogSettings`、`NaraSettingsHub`、`NaraSkinSettingsDialogLayout`、`NaraSettingsSelectLayout`） | 硬编码 `66000000` 40% | 50% | **70.0%** | ❌ 过透 |
| `DialogAddonSettings`（**插件设置页**） | `66000000` 40% | 50% | **70.0%** | ❌ 过透 |
| `DialogButtonMenu`（电源菜单） | `66000000` 40% | 50% | **70.0%** | ❌ 过透 |
| `DialogContextMenu`（右键菜单） | `4D000000` 30% | 50% | **65.2%** | ❌ 过透 |
| `Custom_1102_TextViewer` | `66000000` 40% | `glass_regular` 40% | **64.0%** | ❌ 过透 |

`DialogBackgroundCommons` 的 20 个调用点：`DialogConfirm`、`DialogColorPicker`、`DialogMediaSource`、
`DialogNumeric`、`DialogPVRChannelManager`、`DialogPVRGroupManager`、`DialogPVRGuideSearch`、
`DialogSubtitles`、`DialogTextViewer`、`DialogVideoManager`、`FileBrowser`、`SmartPlaylistEditor`、
`SmartPlaylistRule`、`PlayerControls`、`Includes_SettingsOSD`（OSD 设置）、
`Includes_SettingsDialog`（皮肤设置弹窗）、`Includes_DialogSelect` ×2、`Includes_DialogGlass`（电源菜单旧布局）。

### 3.2 只有面板、没有全屏遮蔽（严重过透）

| 窗口 | 遮蔽 | 面板 | 合成 | 判定 |
|---|---|---|---|---|
| `DialogPVRInfo`（直播信息侧栏） | **无** | `glass_frosted` 50% | **50%** | ❌❌ 严重 |
| `DialogMusicInfo`（音乐信息侧栏） | **无** | 50% | **50%** | ❌❌ 严重 |
| `DialogPictureInfo`（图片信息侧栏） | **无** | 50% | **50%** | ❌❌ 严重 |
| `DialogKeyboard`（键盘面板） | **无** | 50% | **50%** | ❌❌ 严重 |
| `DialogSlider` | **无** | 50% | **50%** | ❌❌ 严重 |
| `DialogNotification`（通知条） | **无** | 50% | **50%** | ❌ 可接受（短时） |
| `DialogPVRGuideControls` | **无** | 50% | **50%** | ❌❌ 严重 |
| `DialogPVRChannelGuide`（频道节目单） | **无** | `ContentPanel` 50% | **50%** | ❌❌ 严重 |
| `DialogPVRChannelsOSD` | **无** | `ContentPanel` 50% | **50%** | ❌❌ 严重 |
| `Custom_1100_AddonLauncher` | **无** | `ContentPanel` 50% | **50%** | ❌ 严重 |
| `Custom_1116_OSDPlaylistShelf` | **无** | 硬编码 `80141418` 50% | **50%** | ❌ 严重 |
| `Custom_1113_MusicAudioDialog` | **无** | `glass_regular` 40% | **40%** | ❌❌ 严重 |
| `Custom_1112_OSDPlaylistDialog` | 局部 30% 条 | `glass_regular` 40% | **40%** | ❌❌ 严重 |
| `Custom_1114_MusicPlaylistDialog` | **无** | `glass_regular` 40% | **40%** | ❌❌ 严重 |
| `DialogVideoInfo`（影片信息弹出） | 局部 `detail-left-scrim` | `glass_regular` 40% | **40%** | ❌❌ 严重 |

### 3.3 OSD 场景（保持现状，别压黑画面）

| 窗口 | 现状 | 说明 |
|---|---|---|
| `DialogPlayerProcessInfo` | 整块 `4D000000` 30% | 播放中看参数，压黑会挡画面 |
| `VideoOSDBookmarks` | `4D000000` 30% | 同上 |
| `DialogSeekBar` | `osdfade` 渐变 70% 白 | 底部渐变，非面板 |
| `DialogVolumeBar` / `DialogExtendedProgressBar` / `DialogBusy` | 无面板 | 纯图标 |

### 3.4 全屏页（不是浮窗，但同一个病根）

`AddonBrowser`、`EventLog`、`SkinSettings`、`SettingsCategory`、`SettingsProfile`、`SettingsSystemInfo`
都用 `glass_frosted` 50% 当**整页底板**，下面压的是 `NaraSettingsBackground`：
fanart 以 `B3FFFFFF`（70% 不透明度）叠在 `primary.jpg` 上，再叠 `1A000000` 10%。
**面板 50% + 背景刻意保持 70% 亮度** = 亮部直接透上来。

---

## 四、问题归因（4 条，前两条是 bug）

### ① `darken_bg` 参数从未声明 → 遮蔽层是"靠运气"在显示
`Includes.xml:871` 写 `<visible>$PARAM[darken_bg]</visible>`，但 `DialogBackgroundCommons`
的参数表里**没有 `darken_bg`**，20 个调用点也**没有一个传它**。
它能工作，是因为 Kodi 的 `CGUIControlFactory::GetConditionalVisibility` 里：

```cpp
if (!node->NoChildren())
  conditions.emplace_back(node->FirstChild()->Value());
...
if (!conditions.size()) return false;   // 不注册任何可见条件 → 控件默认可见
```

空 `<visible>` 被过滤掉 → 不注册条件 → `m_visibleCondition == 0` → `UpdateVisibility` 整块跳过 →
**控件保持默认 VISIBLE**。所以 70% 遮蔽层确实在显示。

**但这是隐式契约**：任何人为了"补默认值"加一句 `default="false"`，20 个对话框的遮蔽层瞬间全灭。
必须显式声明。

### ② `NaraDialogGlassTexture` 的 `radius` / `style` 参数是死参数
```xml
<include name="NaraDialogGlassTexture">
    <param name="radius">32</param>
    <param name="style">frosted</param>
    <definition>
        <texture colordiffuse="glass_frosted" border="32">shapes/round32.png</texture>  <!-- 写死 -->
    </definition>
</include>
```
两个参数**函数体里一次都没用**。所以 `DialogKeyboard` 传 `style="dialog"`、
`PlayerControls` 传 `glass_style="frosted"`、`NaraSettingsDialogFrame` 传 `glass_style`/`tint`
——**全是空转**。这意味着"按 style 分档调不透明度"这条最自然的路现在是断的。

### ③ `glass_dialog`（75%）是死色
`colors/*.xml` 里定义了 75% 的 `glass_dialog`，但**全仓库只有 `NaraSettingsDialogFrame` 的
`tint` 默认值引用它**，而 4 个调用点全部覆盖成 `glass_frosted`。
——现成的 75% 档位从来没被用上。启用它，插件设置页一行就能从 70% 提到 85%。

### ④ 面板贴图是"纯白圆角矩形"，没有任何 alpha 变化
`shapes/round*.png` 是均匀全白的圆角块，乘 `glass_frosted` 得到**均匀 50% 的灰板**。
均匀 = 既没有"玻璃的厚度感"，也没有"边缘化开"的通透感。
**这是"透"和"糊"同时存在的根本原因**：中心不够实（文字飘），边缘不够透（像块塑料板）。

### ⑤ 顺带查出的老问题：条件 include 是**加载时**求值的
`GUIIncludes::ResolveIncludes()` 里，`<include condition="X">` 的 `X` 会在展开 XML 时
`conditionID->Get()` **求一次值**，之后不再更新。后果是：

```xml
<include condition="$EXP[nara_dialog_glass]">NaraDialogGlassTexture</include>
<include condition="!$EXP[nara_dialog_glass]">NaraDialogSolidSurface</include>
```

`nara_dialog_glass` 里含 `Window.IsActive(fullscreenvideo)`，而皮肤加载时**永远不在全屏播放**
→ 该表达式恒为真 → **全皮肤只注入了玻璃分支，`NaraDialogSolidSurface` 从未存在过**。
也就是说"全屏播放时对话框自动变不透明"这个设计从来没生效。

本次没有改它（属于另一个话题，改动面很大），但两个结论要记住：
- 想按运行时状态切换面板外观，**不能用条件 include**，只能用 `<visible>` 或 `$VAR`。
- 反过来说，本次新增的 `NaraDialogScrim` 全是**无条件** include，不受这个坑影响。

---

## 五、方案：三层模型

### 5.1 分工

```
┌─────────────────────────────────────────────┐
│ ③ 文字底板 glass_plate   12%  ── 只管列表/长文本区域，抬局部对比度
├─────────────────────────────────────────────┤
│ ② 玻璃面板（渐变贴图）    中心 80% / 边缘 56%  ── 管"这块面是实的"，边缘化开留一点玻璃感
├─────────────────────────────────────────────┤
│ ① 全屏遮蔽 scrim         60% (浮窗) / 55% (侧边)  ── 只管"底噪"，页面压暗但仍认得出
└─────────────────────────────────────────────┘
```

**为什么分三层，而不是把面板一口气改成 96%？**

同样 96% 的总遮盖率，`60% + 90%` 和 `0% + 96%` 的观感不同：
- 后者：面板外**完全没压暗**，页面保持原亮度，浮窗像一张贴在照片上的不透明卡片，边界很突兀；
- 前者：面板外的背景被压暗 60%，仍有空间感和"我还在这页上"的定位感，
  面板本身边缘有 12px 渐隐 —— 这才像一块浮起来的玻璃。

**但不要指望面板本体还能透**：第一轮想"面板 50% 靠遮蔽补"，结果 86% 照样能读字。
面板本体的不透明度就是可读性的唯一决定因素，遮蔽层只能决定"面板外面暗不暗"。

### 5.2 数值表（透黑模式，**第三轮定稿**）

> **两轮失败记录，免得以后再犯。**
> - 第一轮 `scrim 72% + 面板 50% = 86%`：以为 86% 就"认不出内容"，
>   实机截图证明**完全能读出底下的插件列表文字**。
>   算一下：白字 237 在 86% 遮盖下仍贡献 `0.14 × 237 ≈ 33` 灰阶，面板底色才 ~14，对比度 3:1。
> - 第二轮 `60% + 90% = 96%`：字是读不出了，但**面板变成一块黑板**，透明感全无。
> - **定稿 `60% + 80% = 92%`**：能看出底下有东西，读起来费劲。
>
> 结论：**可读性只由面板本体不透明度决定**。86% 能读、92% 勉强、96% 读不出。
> 想要"既看得出底下、又读不出字"，就只能是 90~93% 这一小段，别想更宽。

| token | 值 | 用在哪 |
|---|---|---|
| `glass_dialog` | `CC0F0F12` (80%) | **浮窗面板**（插件详情/设置/确认/键盘/上下文菜单/侧栏/播放列表…） |
| `glass_page` | `BF0F0F12` (75%) | **全屏页内容面板**（插件浏览/事件日志/皮肤设置/设置分类/系统信息） |
| `glass_frosted` | `800F0F12` (50%) | 卡片 / 页面背景层 / 不承载长文本的装饰面板 |
| `scrim_dialog` | `99000000` (60%) | 普通浮窗全屏遮蔽 |
| `scrim_sheet` | `8C000000` (55%) | 侧边 / 条状浮窗 |
| `scrim_osd` | `4D000000` (30%) | 播放中 OSD |
| `glass_plate` | `1F000000` (12%) | 文字底板（仍未接线） |

合成结果：

| 场景 | 计算 | 结果 |
|---|---|---|
| 普通浮窗 · 面板中心 | `1−(0.40×0.20)` | **92.0%** |
| 普通浮窗 · 面板边缘（贴图 alpha ≈ 184） | `1−(0.40×0.42)` | **83.1%** |
| 侧边浮窗 · 面板中心 | `1−(0.45×0.20)` | **91.0%** |
| OSD 小挂件（滑条 / 频道列表 / 播放列表） | `1−(0.70×0.20)` | **86.0%** |
| 全屏页 · 内容面板 | `1−(0.25×0.45)` | **88.8%** |

**可读性阈值（实测修正版）**：

| 总遮盖率 | 白字（237）剩余灰阶 | 观感 |
|---|---|---|
| ≥ 96% | ≤ 9.5 | 认不出，只有极淡的形 |
| 92 ~ 96% | 9.5 ~ 19 | 隐约知道下面有东西，读不出 |
| **88 ~ 92%** | 19 ~ 28 | 努力能读，长文本会累 |
| 84 ~ 88% | 28 ~ 38 | **能读 ← 第一轮就是这里** |
| < 84% | > 38 | 一眼就读出来 |

### 5.3 档位：最终取"面板实 + 遮蔽轻"

第一轮的思路是"遮蔽重、面板轻"（72% + 50%），观感偏"整页压黑、浮窗还透"。
第二轮反过来：**遮蔽轻一点（60%，页面还认得出）、面板实一点（90%，文字区域干净）**。

这样得到的是标准桌面弹窗的观感：页面被压暗 60% 但仍可辨认，浮窗是一块近乎实心的
深色卡片，边缘 12px 轻微渐隐保留一点玻璃感。

> 如果还是嫌太实：改 `glass_dialog` 从 `E6` 到 `CC`（80%）→ 中心 92%，能隐约看出底下。
> 如果嫌面板外压得太暗：改 `scrim_dialog` 从 `99` 到 `80`（50%）。两个互不影响。

---

## 六、四个可选手段（含代价）

### A. 全屏遮蔽层（`scrim_dialog` / `scrim_sheet`）—— **必做**
- 收益：一刀切掉"底噪"，所有浮窗同时受益；成本最低。
- 代价：面板外的页面会被压暗，失去一点"我还在这页上"的定位感 → 所以上限压在 72%。
- 现状问题：遮蔽层有的 30%、有的 40%、有的 70%、有的没有。统一后观感立刻一致。

### B. 玻璃面板贴图做 alpha 渐变 —— **推荐（已实施）**
- 新增 `media/shapes/glass16/18/20/28/32/42.png`（生成器 `tools/gen_glass_plates.py`）：
  - 中心 alpha **255**（配 `glass_dialog` 80% 得 80%）
  - 边缘 alpha **180**（得 56%），18px 平滑过渡
  - 圆角用 SDF + 1px 抗锯齿裁出来，角落自然"化开"
- 收益：面板中心 92%、边缘 83%，差 9 个点——**这一圈渐隐是"看起来像玻璃"的唯一来源**。
  面板本体只负责可读性，边缘负责质感，两者分开调，互不干扰。
- **两条不能违反的技术约束**：
  1. 贴图是 **9-slice** 用的（`border` = 圆角半径，画布 = 2r+2）。
     渐变带必须完全落在最外圈 r 像素内，且**沿直边方向必须均匀**，
     否则边条拉伸后会出现横向条纹。实现上把「到四边的距离」和「圆角遮罩」分开算再相乘。
  2. **不要加噪点**：中间只有 2×2 像素，会被拉伸到整块面板，噪点变成明显涂抹痕迹。
     想要颗粒感只能另起一个 `<control type="image">` 去 tiling，成本不划算。
- 代价：需要重打包 `Textures.xbt`；`colordiffuse` 的 alpha 与贴图 alpha 相乘，
  所以颜色 token 的 alpha 语义是"**不透明度上限**"。
- `shapes/round*.png` **不要动**：focus 高亮等地方还在用（面板已经全部切到 `glass*.png`）。

### C. 面板投影（分离感）—— **推荐，极便宜**
- 给面板加 `bordertexture` 阴影（`overlays/shadow.png` 已有实现：
  `NaraDialogLegacyShadow` 里的 `bordertexture border="21" infill="false"`）。
- 收益：**不提高任何不透明度**，靠"面板浮在背景之上"的视觉暗示提升可读性感知。
  这是 Windows / macOS 弹窗的正统做法：不压暗全屏，靠阴影分离。
- 代价：需要一张 9-slice 阴影图（现有 `overlays/shadow.png` 可直接复用，但要确认 alpha 够淡）。
- **如果只做 A + C 不做 B，也能显著改善**——C 是性价比最高的一项。

### D. 文字底板 `glass_plate`（12%）—— 可选
- 只给**列表区 / 长文本区**垫一层圆角块（`18FFFFFF` 的反色版：深色 `1F000000`）。
- 已有先例：`NaraDialogInsetTexture`（`18FFFFFF`）已经在键盘、选择框里用了，只是方向是"提白"。
- 适用：`DialogTextViewer`、`DialogAddonSettings` 的设置列表、`DialogAddonInfo` 的描述区、
  `EventLog` 的日志列表。
- 代价：每个窗口要按列表尺寸单独摆，且要保证和面板圆角内缩一致（建议内缩 24px）。

### 明确**不要做**的事
- ❌ 指望运行时模糊（不存在）。
- ❌ 把 `glass_frosted` 直接提到 70%+ 而不做渐变 → 变成均匀灰板，透明感全失。
- ❌ 用 `$VAR` 做 `<textcolor>`（整段文字变透明，已踩过）。
- ❌ 在透白主题里用白色遮蔽配白字（必死，见 §8）。

---

## 七、实施记录（2026-10-26 已完成 Phase 0~3）

采用 **β 可读优先**。以下是**实际**改动，与初稿有出入的地方都注明了原因。

### Phase 0 —— 背景亮度（1 行）
`Includes_Settings.xml:31` 背景 fanart `B3FFFFFF`（70%）→ `8CFFFFFF`（55%）。
所有设置页 / 插件页 / 日志页的"透过内容"整体暗一档，不动任何面板。

### Phase 1 —— 骨架
1. **颜色 token**：`colors/defaults.xml` 新增 `scrim_dialog` `B8000000` / `scrim_sheet`
   `A6000000` / `scrim_osd` `4D000000` / `glass_plate` `1F000000`；
   `colors/light.xml` 同步（**遮蔽层仍用深色**，见 §8）。
2. **`NaraDialogScrim`**（`Includes_DialogGlass.xml`）：只有一个 `<control type="image">`，
   param 只有 `tint`。**没有做成"可点击关闭"版**——需要点空白关闭的窗口自己已经有 button，
   多插一个 button 会抢焦点。
3. **`NaraDialogGlassTexture` 修死参数**：`radius` / `style` 原来完全没用。
   现在 `style` 改名 `tint` 且语义是**颜色名**（`glass_frosted` / `glass_dialog`），
   `radius` 真正参与 `border` 和贴图路径，新增 `shadow` 开关。
   调用点同步：`DialogKeyboard` / `DialogSlider` 的 `style="dialog"` → `tint="glass_frosted"`，
   `PlayerControls` / `Includes.xml:1173` 的 `glass_style="frosted"` → `glass_frosted`。
4. **`DialogBackgroundCommons`**：补 `<param name="darken_bg">true</param>`（修 §4①），
   补 `<param name="scrim">scrim_dialog</param>`，遮蔽色 `overlay_medium` → `$PARAM[scrim]`，
   `glass_style` 默认值 `dialog` → `glass_frosted`。
5. **`NaraSettingsDialogFrame`**：遮蔽 `66000000` → `scrim_dialog`；
   **`tint` 保持 `glass_frosted`**（初稿说改成 `glass_dialog` 75%，实施时否掉了——
   72% + 75% = 93%，直接变死板，没必要）；
   顺手删掉从未被使用的 `glass_style` 参数及其调用点。

### Phase 2 —— 逐窗口接线

**走 72% 遮蔽（`scrim_dialog`）**
| 文件 | 改动 |
|---|---|
| `DialogAddonInfo.xml:20` | `B3000000` → `scrim_dialog` |
| `Custom_1102_TextViewer.xml:9` | `66000000` → `scrim_dialog`；面板 `glass_regular` → `glass_frosted` |
| `Includes_DialogGlass.xml` `NaraPowerMenuLayout` | `66000000` → `scrim_dialog` |
| `Includes_Settings.xml` `NaraSettingsDialogFrame` | `66000000` → `scrim_dialog` |

**走 65% 遮蔽（`scrim_sheet`，浮窗但不在播放画面上）**
`DialogPVRInfo` / `DialogMusicInfo` / `DialogPictureInfo` / `DialogKeyboard`
—— 这四个原来**完全没有遮蔽层**，面板裸露在清晰原图上。

**走 30% 遮蔽（`scrim_osd`，压在播放画面上，不能压黑画面）**
| 文件 | 改动 |
|---|---|
| `DialogContextMenu.xml:17` | `4D000000` → `scrim_sheet`（右键菜单不在播放画面上，用 sheet） |
| `DialogSlider.xml` | 新增 `scrim_osd` |
| `DialogPVRGuideControls.xml` | 新增 `scrim_osd` |
| `DialogPVRChannelGuide.xml` | 新增 `scrim_osd`（插在 `ColoredBackgroundImages` 之后，否则被底图盖住） |
| `DialogPVRChannelsOSD.xml` | 新增 `scrim_osd` |
| `Custom_1112_OSDPlaylistDialog.xml` | `NaraStreamDialogBackground` 内加 `scrim_osd`（一处改，三个调用点受益） |
| `Custom_1114_MusicPlaylistDialog.xml` | `NaraMusicPlaylistBackground` 内加 `scrim_osd` |
| `Custom_1113_MusicAudioDialog.xml:22` | 面板 `glass_regular` → `glass_frosted` + 新增 `scrim_osd` |
| `Custom_1116_OSDPlaylistShelf.xml:25` | `80141418` → `glass_frosted` + 新增 `scrim_osd` |
| `DialogPlayerProcessInfo.xml` / `VideoOSDBookmarks.xml` | `4D000000` → `scrim_osd`（值不变，收口成 token） |

**只改面板 / 不动遮蔽**
| 文件 | 改动 |
|---|---|
| `DialogVideoInfo.xml:175` | "更多"弹层的 `glass_regular` → `glass_frosted`，背后按钮 `4D000000` → `scrim_sheet`。主页面靠 `detail-left-scrim.png`，不动 |
| `DialogAddonSettings.xml` | 无需改（走 `NaraSettingsDialogFrame`） |
| `EventLog` / `AddonBrowser` / `SkinSettings` / `SettingsCategory` 等全屏页 | 整页玻璃保留，靠 Phase 0 压背景 |

**有意不加遮蔽（已列入 `audit_skin.py` 豁免）**
- `DialogNotification` —— 瞬时提示条，加全屏遮蔽会干扰观看。
- `Custom_1100_AddonLauncher` —— 是**整页**不是浮窗，背景自己就是 40% 的 fanart，
  该压的是背景层而不是加遮蔽。

### Phase 3 —— 贴图
1. `tools/gen_glass_plates.py` 生成 `media/shapes/glass16/18/20/28/32/42.png`：
   中心 alpha 255、边缘 150、约 19px 过渡、SDF 圆角 + 1px 抗锯齿。
   **去掉了初稿里的噪点**——9-slice 中间只有 2×2 像素，噪点会被拉伸成明显涂抹。
2. `NaraDialogGlassTexture` 指向 `glass$PARAM[radius].png`。
3. 面板投影 `NaraDialogGlassShadow`（`overlays/shadow.png` + `bordersize` 20），
   由 `NaraDialogGlassSurface` **无条件**注入。没有做成条件 include——
   `GUIIncludes::ResolveIncludes()` 里 `condition` 是**加载时**求值的
   （`conditionID->Get()` 在展开 XML 时调一次），写成 `condition="$PARAM[shadow]"`
   要靠"参数替换早于条件求值"才成立，不可依赖。
4. `tools/xbt_tool.py pack` → 668 张贴图，7.6MB。

### Phase 4 —— 审计兜底（已加两条规则）
`tools/audit_skin.py`：
- **浮窗缺遮蔽层**：`Dialog*.xml` / `Custom_11*.xml` 里有玻璃面板 token 但没有遮蔽 token → 报出。
- **浮窗里的硬编码遮蔽色**：`colordiffuse="XXXX0000"` + `colors/black.png` → 提示改用 token。
两条都是软提示（不影响退出码），现状均 **0**。

### 尚未做
- **`glass_plate` 文字底板**：token 已定义，但还没接到任何窗口。
  面板本体定在 80% 之后基本不需要了，等实机确认。
- **浅色主题**：按你的要求押后，当前 `light.xml` 用的是 L2 方案
  （浮窗遮蔽层仍是深色，`glass_dialog` / `glass_page` 保持原来的半透明白，不跟随透黑模式加厚）。

---

## 七之二、第二轮修正（2026-10-26 14:10）

### 触发的反馈
第一轮上线后（Kodi 已于 14:04 重启，确认生效）截图显示：
插件详情页的底下插件列表**仍然能逐条读出**，右键菜单背后的海报**仍然清晰可辨**。

### 原因（算一下就明白）
`scrim 72% + 面板 50% = 86%`，白字 237 在 86% 遮盖下仍贡献 `0.14 × 237 ≈ 33` 灰阶，
面板底色只有 ~14 —— 对比度 3:1，肉眼毫无压力。
**86% 这个数不是"勉强够"，是远远不够。**

### 改法：思路反转
| | 第一轮 | 第二轮 |
|---|---|---|
| 遮蔽 | 72%（重） | **60%**（轻，页面仍认得出） |
| 面板 | 50%（轻） | **90%**（实，文字区干净） |
| 合成 | 86% | **96%** |
| 观感 | 整页压黑，浮窗还透 | 页面压暗，浮窗是实心卡片 |

### 具体改动
1. `colors/defaults.xml`
   - `glass_dialog` `BF141418` → **`E60F0F12`（90%）** —— 从"死色"变成"浮窗面板标准色"
   - 新增 **`glass_page` `BF0F0F12`（75%）** —— 全屏页内容面板
   - `scrim_dialog` `B8000000` → **`99000000`（60%）**
   - `scrim_sheet` `A6000000` → **`8C000000`（55%）**
2. `colors/light.xml`：`glass_dialog` / `glass_page` **不跟随**，保持半透明白（见 §8）
3. **面板 token 全量替换**（30 处 → 浮窗用 `glass_dialog`，全屏页用 `glass_page`）：
   - 浮窗：`DialogAddonInfo`、`DialogAddonSettings`、`DialogContextMenu`、`DialogKeyboard`、
     `DialogSlider`、`DialogVideoInfo`、`Custom_1102`、`Custom_1113`、`Custom_1116`、
     `NaraSettingsDialogFrame`（4 个调用点）、`NaraSettingsSidebar`、`NaraSettingsHub`、
     `Includes_DialogSelect`（NaraSettingsSelectLayout）、`Includes_SettingsDialog`、
     `PlayerControls`、`NaraDialogGlassTexture` / `NaraDialogGlassSurface` 默认值、
     `ContentPanel`、`NaraPowerMenuLayout`、`MediaMenu` 侧边栏
   - 全屏页：`AddonBrowser`、`EventLog`、`FileManager`、`SettingsCategory`、
     `SettingsProfile`、`SettingsSystemInfo`、`SkinSettings`
4. 面板贴图统一换成带渐变的 `shapes/glass<N>.png`（原来是均匀的 `round<N>.png`）
5. 贴图参数回退：`EDGE_ALPHA 150→200`、`RAMP_MAX 24→12`
   （面板已经 90%，边缘不能再低，否则四周会有一圈明显的"破洞"）

### 现在的口径
**浮窗本体不再追求"能透出底下"**。透明感留在两处：
面板外 60% 的遮蔽（页面被压暗但认得出），以及面板边缘 12px 从 96% 渐隐到 88%。

---

## 七之三、第三轮修正（2026-10-26 14:15）

### 反馈
"面板本体基本不透了，但是它现在过于不透了。"

### 诊断
96% 在数字上是"认不出"，但观感上变成**一块没有层次的死板**。
上一轮的错在于：把"面板本体"和"边缘渐隐"两件事都用同一个旋钮（alpha）调，
结果要么太透要么太实。

### 改法：拆成两个旋钮
| 旋钮 | 管什么 | 定稿 |
|---|---|---|
| `glass_dialog` alpha | **只**管可读性 | `E6`(90%) → **`CC`(80%)**，合成 96% → **92%** |
| 贴图边缘 alpha / 渐变宽度 | **只**管"像不像玻璃" | `200`/`12px` → **`180`/`18px`** |

于是：面板中心 92%（读起来费劲），边缘 18px 渐隐到 83%（看得出是块有厚度的玻璃）。
**可读性靠中心，质感靠边缘，以后只调其中一个不会互相打架。**

### 遗留
`glass_page`（全屏页）仍是 75%，没动 —— 用户反馈只涉及浮窗。

## 八、浅色（透白）主题的额外决策

**问题**：`colors/light.xml` 的 `glass_frosted` 是 `33FFFFFF`（20% 白）。
如果照搬上面的方案，遮蔽层用白色 72% → 白玻璃 + 白字 = **文字彻底消失**。
如果遮蔽层用深色，那"透白"就不叫透白了。

**两条路，需要你选**：

| 选项 | 做法 | 范围 | 观感 |
|---|---|---|---|
| **L1（推荐）** | 透白主题的**浮窗**改用 `ink_primary`（`FF14141A`）深色字 + 白色遮蔽 60% | 只改 24 个浮窗内的 `<textcolor>`，约 30~40 处 | 真·白玻璃 + 黑字，浮窗与全屏页形成对比 |
| **L2** | 透白主题的浮窗遮蔽层仍用**深色**（如 `8C000000`），白字不变 | 只改 `light.xml` 4 行 | 浮窗是"浅灰玻璃"，全屏页是"白玻璃"，两者不一致 |

**本次方案（Phase 0~3）只针对透黑模式**，浅色主题的 token 先按 L2 落地（一行不改代码结构），
L1 作为独立的后续任务。

---

## 九、验收清单

- [ ] 插件设置页 / 插件详情页 / 设置中心 / 右键菜单 / 电源菜单，两页观感一致（同色同透明度）
- [ ] 直播信息栏、音乐信息栏、图片信息栏、频道节目单、键盘——打开时**认不出底下是什么**
- [ ] 面板边缘仍能看出底下有画面（不能是死板）
- [ ] `kodi.log` 无新增贴图加载失败（`Starting Kodi` 时间必须晚于部署时间）
- [ ] `tools/audit_skin.py` 的"浮窗缺遮蔽层"归零
- [ ] 全屏播放时打开对话框，仍是**不透明**（`nara_dialog_glass` 分支，别破坏）
- [ ] 透白主题不崩（浮窗文字仍可读）

---

## 十、改动量（实际）

| Phase | 文件数 | 改动 | 风险 |
|---|---|---|---|
| 0 | 1 | 1 行 | 极低 |
| 1 | 4 | ~70 行 | 低 |
| 2 | 21 | ~90 行 | 中（新增遮蔽层，需实机确认观感） |
| 3 | 1 脚本 + 6 张图 | 新增 6 张贴图，重打包 xbt | 中（要重启 Kodi 才重载） |
| 4 | 1 | ~45 行 | 低 |

**调参入口（都在 `colors/defaults.xml`，改完不用动任何窗口文件）**：

| 想要的效果 | 改哪个 | 怎么改 |
|---|---|---|
| 浮窗本体再透一点 | `glass_dialog` | `CC`(80%) → `BF`(75%)，合成 92%→90%（开始能读出字） |
| 浮窗本体更实 | `glass_dialog` | `CC` → `D9`(85%)，合成 94% |
| 浮窗本体很实（不推荐） | `glass_dialog` | `CC` → `E6`(90%)，合成 96%，黑板 |
| 面板外压暗轻一点 | `scrim_dialog` | `99`(60%) → `80`(50%) |
| 面板外压暗重一点 | `scrim_dialog` | `99` → `B3`(70%) |
| 全屏页更实 | `glass_page` | `BF`(75%) → `D9`(85%) |
| 边缘渐隐更明显 | `tools/gen_glass_plates.py` 的 `EDGE_ALPHA` / `RAMP_MAX` | `180`/`18` → `150`/`24`，重跑脚本 + 重打包 |

`scrim_sheet`（侧边浮窗）和 `scrim_osd`（播放中 OSD）同理。
Phase 0+1+2 就能拿到 80% 的收益，Phase 3 是"从能用变好看"。

---

## 十一、做成皮肤设置项（2026-10-27 重构定稿）

### 为什么重构
旧方案是「浮窗不透明度 6 档」+「页面面板不透明度 4 档」。三个问题：

1. **维度选错了**：用户感知的是"我在浏览"还是"我在看片"，不是"这是浮窗还是页面面板"。
   两个设置普通人分不清该调哪个。
2. **档位太密**：6 档里后三档只差 7-8 个点，肉眼分不出，等于白给。
3. **有旁路**：`glass_regular` 这类固定色名绕过了所有设置，侧栏/菜单/音乐播放器
   调了设置也不变——这才是"侧栏过于透明"的真正原因。

### 新方案：三个设置，按「离用户多近」分

第一版是「界面 / 播放中」两个。实际用下来发现「界面」把四种完全不同的东西捆在一起了：
全屏页面面板、页面里的卡片、**叠在页面上的浮窗**（插件详情/插件设置/对话框/侧栏）、播放控制条。
浮窗压在页面之上、底下还有内容要透出来，它需要比页面更实 —— 所以拆成三档。

| 设置 | 皮肤设置名 | 管什么 | 默认 |
|---|---|---|---|
| **页面透明度** | `glass_page_op_1..6` | 全屏页面面板 + 页面里的卡片 / 胶囊 / 顶部导航条 | 3 平衡 73% |
| **浮窗透明度** | `glass_float_op_1..6` | 叠在页面上的层：对话框、插件详情、插件设置、右键菜单、键盘、搜索键盘、设置页左侧栏 | 4 偏实 83% |
| **播放中透明度** | `glass_play_op_1..6` | 播放时的浮窗：OSD 设置、播放列表、书签、处理信息、播放控制条 | 2 通透 60% |

默认值按"越靠前的层越黑"排：播放中 60% < 页面 73% < 浮窗 83%。

### 档位：6 档，档差 13

| 档 | 面板 `gl_*` | 遮蔽 `sc_*` | **合成遮盖** | label2 显示 |
|---|---|---|---|---|
| 1 | 32% (`52`) | 19% (`30`) | 45% | 极透 |
| 2 | 45% (`73`) | 27% (`45`) | 60% | 通透 |
| **3** | 58% (`94`) | 35% (`59`) | **73%（页面默认）** | **平衡** |
| 4 | 71% (`B5`) | 43% (`6E`) | 83%（浮窗默认） | 偏实 |
| 5 | 84% (`D6`) | 50% (`80`) | 92% | 厚实 |
| 6 | 97% (`F7`) | 58% (`94`) | 99% | 实心 |

**为什么从 5 档变 6 档**：5 档那版「平衡」= 83%，实机偏实。整条梯子下移一格、底下补一档 45%，
默认档名不变但值降 10 个点。档差仍然是 13（以前 6 档失败是因为后三档只差 7-8）。

三个设置共用这一套 `gl_*`（浮窗只是默认高一档，没有单独的色板）。

遮蔽层不单独配，跟页面档的面板 alpha 联动（×0.6）。**遮蔽只跟页面档** ——
它干的是"把页面压暗"，属于页面，不属于浮窗；浮窗只改自己的面板。

### 变量映射（引用数不变，只是改接）

| 变量 | 来源 | 处数 |
|---|---|---|
| `NaraGlassPageTintVar` | 页面档 | 21（页面面板 + 卡片 + 导航条） |
| `NaraGlassFloatTintVar` | 浮窗档 | 25（对话框 / 插件详情 / 插件设置 / 菜单 / 键盘 / 设置侧栏） |
| `NaraPlaybackDialogTintVar` | 播放中档 | 播放 OSD 全系 + 播放控制条 |
| `NaraGlassScrimTintVar` | 页面档的遮蔽 | 所有遮蔽层 |
| `NaraSettingsDialogScrimVar` | 播放中用 `scrim_osd`，否则跟页面遮蔽 | 设置类对话框 |

`NaraGlassDialogTintVar` 已删除（原来 37 处引用按上面三类拆开）。漏改一处 `audit` 就报"缺失变量"。

### 堵掉旁路
`glass_regular` / `glass_frosted` / `glass_dialog` / `glass_page` 四个固定色名**全部删除**，
引用改接 `$VAR[...]`。现在没有任何玻璃面板能绕过设置。

### UI 长什么样

设置行只有两段：**设置名 + 当前档位名**

```
页面透明度                          平衡
浮窗透明度                          偏实
播放中透明度                        通透
```

- ❌ 不加常驻说明文字（试过 4 行灰字，太丑，已删）
- ❌ label2 不带百分比（试过"平衡 89%"，太丑，已删）
- ✅ 主题差异只放在 `Skin.SelectBool` 的**对话框标题**里（只在选档时出现）
- ✅ 每行管哪些地方写进底部**帮助条**（焦点落到该行时显示，见 `SkinSettingsHelpTextVar`）

档位名 5 个词：极透 / 通透 / 平衡 / 偏实 / 实心。

### 实现（五段）
1. **颜色**：`colors/defaults.xml` → `gl_1..6` / `sc_1..6` 共 12 个 token
   （`light.xml` 覆盖同一批 token 为白玻璃值）。三个设置共用，浮窗没有单独色板
2. **变量**（`Variables.xml`）：`NaraGlassPageTintVar` + `NaraGlassScrimTintVar`（页面档）、
   `NaraGlassFloatTintVar`（浮窗档）、`NaraPlaybackDialogTintVar`（播放中档）
   + 三个 label 变量。**最后一条无 condition 的 value 是默认档**（`gl_3` / `sc_3` / `gl_4` / `gl_2`）
3. **接线**：37 处 `colordiffuse` / `tint` 参数 → `$VAR[...]`
   （`colordiffuse` 支持 `$VAR`，`<textcolor>` 不支持）。
   `ContentPanel` 这个 include 加了 `tint` 参数，默认页面档，PVR 频道 OSD 传播放中档
4. **UI**：`SkinSettings.xml` grouplist 700 的三个 button（711 / 712 / 713），
   行内只有「设置名 + 档位名」，说明文字全部移到弹窗标题和底部帮助条
5. **文案**：皮肤字符串 31722~31731 + 31759~31761 + 31733
   （档位名 5 个、三个设置名、三条弹窗标题、默认评分来源）；帮助条文案 31736~31758 + 31761

### 坑
- **默认档位会被审计误报"有写无读"**：它是变量里无 condition 的兜底 value。
  2026-10-27 起每档都写了显式条件，`DEFAULT_ONLY_SETTINGS` 已清空。
- **注释里不能直接写 `$VAR[...]`**：审计的 `VAR_REF` 会当成真引用，报"缺失变量 ..."。
- **浅色主题**：`light.xml` 把 `gl_*` 压到 15%~36%、`sc_*` 固定 55%，
  档位差别比透黑小得多。原因见 §8（白玻璃 + 白字）。

---

## 十二、能不能"只在透黑模式下显示这两个设置"？——不能

### 查证结论
**Kodi 没有暴露"当前颜色主题"的 info 标签。**
查了 `xbmc/GUIInfoManager.cpp` 的全部翻译表（`string_bools[]` / `integer_bools[]` /
`system_labels[]` / `system_param[]` …），`theme`、`skincolors` 一个都没有命中。
`System.HasCMS` 是最接近"颜色"的标签，但它只是"Kodi 是否支持色彩管理"，与主题无关。

主题存在 `guisettings.xml` 的 `lookandfeel.skincolors`（`SKINDEFAULT` / `light`），
但皮肤读不到 `guisettings`。

所以：
- ❌ `<visible>` 判断主题 → 做不到
- ❌ 变量按主题分支 → 做不到
- ⚠️ 加一个"我当前用透白"的手动开关 → 技术上能做，但让用户自己同步两套设置，很蠢，不做

### 改用的办法：让透白主题也有自己的档位
既然藏不掉，就让它在两个主题下都**真的起作用**，只是绝对值区间不同：

| 档 | 透黑（黑玻璃） | 透白（白玻璃） |
|---|---|---|
| 1 极透 | 50% | 15% |
| 2 通透 | 60% | 20% |
| 3 偏透 | 70% | 24% |
| 4 平衡（默认） | 78% | 28% |
| 5 偏实 | 85% | 32% |
| 6 实心 | 92% | 36% |

页面面板：透黑 45/60/75/88%，透白 20/30/40/50%。

**为什么差这么多**：透白主题是白玻璃 + 白字，玻璃越不透明、白字越看不见。
上限只能到 36%，再往上文字就糊了。透黑是黑玻璃 + 白字，方向正好相反，可以做到 92%。

**代价**：同一个"档 4"在两个主题下的实际不透明度差了一倍多，用户切主题会觉得"设置没生效"。
所以在设置页加了第 4 行提示（31734）说明这件事。

### 真正的解法（押后）
把浮窗内的文字换成 `ink_primary`（深色），白玻璃就能做到 90%，
两个主题的档位可以完全一致。这就是 §8 的 L1 方案，
只改浮窗（约 30~40 处 `<textcolor>`），不碰全皮肤的 666 处。
用户已明确要求浅色主题押后，所以先按上面的"两套区间"顶着。
