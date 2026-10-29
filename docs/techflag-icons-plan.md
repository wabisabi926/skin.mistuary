# 技术标识图标化 —— 最终方案（定稿）

> 状态：**已确认，待执行**（2026-10-27）
> 范围：**只做彩色一套**，5 类标识，约 60 个图标。白色套、宽高比、8K 等均不在本期。

---

## 一、锁定决策

| 项 | 决定 | 备注 |
|---|---|---|
| 形态 | 图标 + 胶囊底 | 沿用 `shapes/round4.png` + `colordiffuse=33FFFFFF` |
| 配色 | 仅彩色 | 白色套留到第二期 |
| 图标高 | 28（框 48×28） | 胶囊 36 内上下各留 4 |
| 胶囊宽 | 72；Dolby Vision 带档位时 104 | 左右内边距 12，档位小字 `font13` |
| itemgap | 8（不变） | 行高 36、top 290 全不动 |
| DV 档位 | 保留 `P7` 小字 | 只有 DV 且 `HdrDetail` 非空时出现 |
| 开关 | `hide_techflag_icons`，未设置 = 图标开 | 关掉 = 完全回到现在的文字胶囊 |
| 宽高比 | **不加** | `VideoAspect` 是浮点原值，格式不可控 |
| 手绘 | 只画 `av3a`、`mjpeg` | 依据真实片库，其余冷门值走文字 |
| Kodi 21 | 仍走文字胶囊 | 无 `$MAP`，与现有架构一致 |

---

## 二、素材来源

全部为 **CC BY-NC-SA 4.0**（与 Mistuary 自身 CC BY-SA 4.0 同族，不引入 3.0 的版本冲突）。

| 类别 | 来源目录 | 说明 |
|---|---|---|
| 分辨率 | `skin.arctic.fuse.3/media/flags/color/resolution` | 480–4K |
| HDR | `skin.arctic.fuse.3-avdvplus&p3i/media/flags/color/hdr` | DV / DV-FEL / DV-MEL / HDR10 / HDR10+ / HLG |
| 视频编码 | `skin.arctic.fuse.3/media/flags/color/source` | h264 / h265 / hevc / av1 / vc1 / vp9 … |
| 音频编码 | `skin.arctic.fuse.3/media/flags/color/audio` | Dolby / DTS 全家 + AAC / FLAC / PCM … |
| 声道 | `skin.arctic.fuse.3/media/flags/color/channels` | 0–8、10；`12.png` 单文件取自 `zephyr.martian` |
| 手绘 | 脚本内生成 | `av3a`、`mjpeg` 两个白字标 |

**只收录真实存在的图标**：`IconMap` 由脚本按素材目录 + 别名表生成，素材里没有的 key 不写 entry，
运行时 `$MAP` 返回空 → 自动落到文字分支。不为冷门值造图。

---

## 三、图标规格

| 项 | 值 |
|---|---|
| 画布 | **96×56（约 2:1）**，按 2 倍存，显示 48×28 |
| 内容 | 按高度 contain 等比缩放、居中，裁掉原始留白 |
| 格式 | PNG-32，透明底 |
| 输出 | `media/techflags/color/{resolution,hdr,video,audio,channels}/` |

归一化是必须的：原始素材混着 `66×48` / `71×48` / `128×66` / `161×109`，
而 Kodi 的 `image` 控件不支持 `width auto`，grouplist 又要求固定宽度。

素材库没有对应 logo 的 16 个冷门取值（8K / HDR Vivid / HD DVD / HDMV / MPEG-1 /
ProRes / TV / VHS / VP8 / WMV / AAC-LATM / AV3A / AVC / WavPack / MJPEG / Theora），
由脚本按 TextMap 里的显示名渲染成白字标（光学高度固定 0.45 画布高，长词自动缩字号），
所以 **110 个取值全部有图标**，运行时不需要判断"有没有图"。

---

## 四、XML 设计

### 4.1 生成的 IconMap 区

在 `xml/Includes_VideoTechnicalFlags.xml` 内插一段带标记的生成区（与 `gen_techflag_vars.py` 同套路）：

```xml
<!-- BEGIN generated: techflag icon maps -->
<map name="NaraTechnicalResolutionIconMap">
    <entry key="4K">resolution/4K</entry>
    ...
</map>
<map name="NaraTechnicalHdrIconMap"> ... </map>
<map name="NaraTechnicalVideoCodecIconMap"> ... </map>
<map name="NaraTechnicalAudioCodecIconMap"> ... </map>
<map name="NaraTechnicalChannelsIconMap"> ... </map>
<!-- END generated: techflag icon maps -->
```

key 与现有 TextMap 完全一致（`h265` 与 `hevc` 两条 entry 指向同一个 `video/hevc`）。

### 4.2 图标胶囊

新增 `NaraTechnicalIconPill`，用 `group`（grouplist 内已验证可用，评分行就是 group）：

```
group  宽 80 / 高 36
├─ image  背景  shapes/round4.png + colordiffuse 33FFFFFF，border 4
├─ image  图标  left 12 / top 4 / 56×28 / aspectratio keep
│         texture = techflags/color/$PARAM[icon].png
└─ label  档位  left 70 / width 30 / font13 / white   （空则隐藏）
```

`$PARAM[icon]` 由调用方传入 `$MAP[...]` 的结果。

### 4.3 双分支渲染

`VideoTechnicalFlagsContent` 里每个 flag 变成两条：

| 分支 | 可见条件 | 内容 |
|---|---|---|
| 图标 | `$PARAM[visible] + !Skin.HasSetting(hide_techflag_icons) + !$EXP[nara_kodi21]` | `NaraTechnicalIconPill` |
| 文字 | `$PARAM[visible] + [Skin.HasSetting(hide_techflag_icons) | $EXP[nara_kodi21]]` | 现有 `NaraTechnicalTextPill` |

grouplist 会跳过不可见控件（现有代码已依赖此行为），两条不会占位。

> **为什么条件里没有"图标是否存在"**：`$MAP` 只被用在 `<label>` / `<texture>` 里，
> 现有代码没有把它放进 `<visible>` 表达式的先例，行为未经验证。改成"每个取值都有图标"
> （缺 logo 的用字标兜底）后，判断只剩 Kodi 版本和开关两个确定项，风险归零。

Dolby Vision 因为要带档位，宽度 104 与 72 是**两个不同控件**，各自独立判可见。

### 4.4 开关

`SkinSettings.xml` 视觉页（`hide_mediaflags` 那行旁）加一行：

- 写入：`Skin.ToggleSetting(techflag_icons)`
- 读取：图标分支的可见条件里加 `Skin.HasSetting(techflag_icons)`
- 新字符串：`31762`（现有最大 31761），写进 `zh_cn` 与 `en_gb`

---

## 五、声道映射

`AudioChannels(DefaultLayout)` 返回 `7.1` / `5.1.2` 这类字符串，图标按**声道数**命名：

| 布局 | 图标 | 布局 | 图标 |
|---|---|---|---|
| `1.0` | 1 | `5.1` | 6 |
| `2.0` | 2 | `6.1` | 7 |
| `2.1` | 3 | `7.1` | 8 |
| `3.0` | 3 | `5.1.2` | 8 |
| `4.0` | 4 | `7.1.2` | 10 |
| `4.1` | 5 | `7.1.4` | 12 |
| `5.0` | 5 | 其它 | 无图标 → 文字 |

**为什么不做"直接拿声道数查图"**：`5.1.2` 也是 8 声道，但 `8.png` 上印着 `7.1`，
直接用会显示错误信息。按布局字符串精确映射，命中不了的走文字。

---

## 六、文件清单

| 文件 | 动作 |
|---|---|
| `media/techflags/color/**` | **新增**，110 个 PNG（80 素材 + 16 字标 + 14 声道），约 0.9 MB |
| `tools/gen_techflag_icons.py` | **新增**：拷素材 → 归一化 → 手绘 2 个 → 生成 IconMap → 覆盖率报告，`--check` 供 CI |
| `xml/Includes_VideoTechnicalFlags.xml` | 改：插生成区、加 `NaraTechnicalIconPill`、内容段双分支 |
| `xml/SkinSettings.xml` | 改：+1 开关行 |
| `language/resource.language.{zh_cn,en_gb}/strings.po` | 改：+1 条 `31762` |
| `README.md` | 改：第三方声明补 Arctic Fuse 3 flags（照现有 Arctic Fuse 2 genre icons 的写法） |
| `docs/skin-contracts.md` | 改：补一节"技术标识图标"，说明两条渲染路径 + 生成脚本 |
| `docs/techflag-icons-plan.md` | 本文档 |

**不动**：4 个调用点（详情页 Hero / 首页 / 搜索 / View_51）、行高、坐标、grouplist、评分行、`Variables.xml`。

---

## 七、验收

1. 详情页打开一部 4K DV 片 → 分辨率 / DV+P7 / HEVC / TrueHD 等图标齐全、等高、间距均匀
2. 打开一部 1080p 非 HDR 片 → 换成 `HD 1080p`，无空洞
3. 打开一部 AV3A 音频的片 → 显示手绘的 `AV3A` 字标
4. 打开一部 7.1.4 的片 → 声道图标为 `7.1.4`
5. 设置里关掉 `techflag_icons` → 立刻回到现在的文字胶囊
6. 首页 Hero / 搜索 / 海报视图 51 与详情页一致
7. `audit_skin.py`、`gen_techflag_vars.py --check`、`gen_techflag_icons.py --check` 全通过

---

## 八、明确不做

- 白色图标套（第二期，等彩色验收后）
- 宽高比、分级、片源介质等其它 flag
- 8K / HDR Vivid / ProRes / VHS / HD DVD / TV / WavPack / AAC-LATM / AVC 等零出现的值
- 声道 9 / 11 / 13（对应不到真实布局）
- 修改行高或调用点几何

---

## 九、第二轮调整（2026-10-27 晚，已实施）

用户要求「去掉胶囊底板」+「与评分同一行」，两件事一起做。

### 9.1 去底板

| 项 | 第一版 | 现在 |
|---|---|---|
| 底板 | `round4.png` + `33FFFFFF` | **不画**（图标和文字胶囊都去掉了） |
| 图标框 | 48×28，left 12 | 48×28，**left 0** |
| 单枚宽度 | 72（DV 104） | **48（DV 76）** |
| 档位小字 | left 64 / width 32 | **left 52 / width 24** |
| itemgap | 8 | **12** |

去底板后与评分项（图标 + 数字，本来就没有底板）视觉统一，整行成为一条信息条。

### 9.2 与评分同行

- `NaraOnlineRatingsRow` 新增 `inline_flags` / `technical_visible` / `technical_item_prefix`，
  为 true 时在同一个 grouplist 里追加「1px 分隔线 + 技术标识」
- 流信息映射抽成 `VideoTechnicalFlagsByPrefix`，独立行与内联行共用，避免写两遍
- 详情页删掉独立的 `VideoTechnicalFlagsRow`（top 290），tagline `331→290`、简介组 `369→328`
- 首页 / 搜索 / 海报视图仍用独立行，只是图标也变成裸的

### 9.3 声道改回文字（放弃图标）

**原因**：素材按声道数命名且**图上印死了布局文字**（`ch_8` 印 `7.1`、`ch_10` 印 `9.1`），
而 `5.1.2` 与 `7.1` 都是 8 声道、`5.1.4` 与 `7.1.2` 都是 10 声道——图标必然说谎。

**参考**：`skin.estuary.nara`（本皮肤祖先）用「Atmos 码 + 声道数」推断（`eac3_ddp_atmos` + 6 → 5.1.2），
但用户片库里 `truehd` 242 / `eac3` 4979，**没有任何 `*_atmos`**，Kodi 在片库里没存 Atmos 标记，
推断不成立。所以声道只用文字，如实反映 `AudioChannels(DefaultLayout)`，字号 `font13` 与评分数字对齐。

`NaraTechnicalChannelsIconMap` 与 `media/techflags/color/channels/` 已移除。

### 9.4 胶囊回归（同日，用户看过裸图标后要求）

裸图标在真实画面上偏弱，用户要求连评分一起都加回胶囊。最终形态：

| 项 | 值 |
|---|---|
| 评分胶囊 | 豆瓣/TMDb/烂番茄 **114**，IMDb **128**（徽标更宽），内边距 12 |
| 技术标识胶囊 | 普通 **72**（图标 48 + 12×2），DV 带档位 **100**（档位小字 left 64 / width 24） |
| itemgap | **8** |
| 分隔线 | 已移除（两边都是胶囊，靠间距分段，加线反而脏） |

`NaraOnlineRatingItem` 新增 `pad` 参数（默认 12），底板用同一张 `round4.png` + `33FFFFFF`，
与技术标识完全同款；整行因此变成统一的「图标 + 文字」胶囊条。

---

## 十、Atmos 叠加徽章（照 fuse3 的做法）

fuse3 不是"推断"全景声，而是**在音频编码图标右边再叠一枚 atmos 徽章**：

```xml
<visible>String.Contains($PARAM[infolabel_audiocodec],atmos)</visible>
<texture>flags/color/audio/atmos.png</texture>
```

照搬到本皮肤：

- 素材：`skin.arctic.fuse.3/media/flags/color/audio/atmos.png` → `media/techflags/color/audio/atmos.png`
  （由 `gen_techflag_icons.py` 的 `EXTRA_ICONS` 生成，不进 TextMap）
- 条件：`String.Contains($PARAM[audio_codec],atmos)`，并排除 `truehd_atmos` / `eac3_ddp_atmos`
  —— 这两者的编码图标本身就印着 ATMOS，再叠一枚是重复
- 位置：紧跟在音频编码胶囊右侧
- Kodi 21 上退化为一个 `ATMOS` 文字胶囊

**注意**：`ListItem.AudioFeatures`（fuse3 里的另一个控件）在 Kodi 22.0-BETA1 里不存在
（`kodi.exe` 字符串 0 次命中），那个控件是死的，所以没有照搬。

当前本机片库的 `AudioCodec` 全是 `truehd`/`eac3`，**这枚徽章暂时不会出现**；
等 Emby 或 Kodi 把 Atmos 标记带进媒体库，它会自动亮。

---

## 十一、四处视图全部合并（2026-10-27 深夜）

第一轮只合并了详情页，用户截图反馈「首页还是两行」。现在四个位置全部内联：

| 视图 | 原评分 top | 原技术标识 top | 现在 | 下方元素 |
|---|---|---|---|---|
| 详情页 Hero | 247 | 290 | 合并到 247 | tagline 331→**290**，简介 369→**328** |
| 首页 Hero | 42 | 84 | 合并到 42 | 简介 126→**84** |
| 搜索 | 232 | 273 | 合并到 232 | tagline 316→**274** |
| 海报视图 51 | 262 | 305 | 合并到 262 | tagline 354→**311** |

`VideoTechnicalFlagsRow`（独立行组件）已无调用者，**删除**。
四处的调用统一为 `NaraOnlineRatingsRow` + `inline_flags=true` + `technical_item_prefix`。

### 剧集（show 层级）怎么显示（2026-10-28 更新）

show 本身没有 streamdetails。详情页现在的做法是：取**当前选中季的第一集**
（`Container(5101).ListItemAbsolute(0)`）作为代表集，展开它的分辨率/编码/音轨，
并在行尾标注「代表集 S01E01」（Season/Episode 补零到两位）。切季时跟着变；如果没有季/集货架（纯 Emby 动态节点、
DBID=0），仍然只显示评分。

`TvShowRepresentative.*` 分支保留给脚本方案：目前没有组件写这组属性，
搜索页/首页的 TV show 行仍不显示技术标识。**单集页**仍然显示该集自己的流信息。

---

## 十二、终版排布：标识在上、评分沉底（2026-10-27 夜，已实施）

参考用户给的 Arctic 系截图：技术参数属于"这片子是什么规格"，评分属于"别人怎么评价"，
两者之间应该隔着简介，而不是并排。

### 版式

```
① Clearlogo / 标题
② 元数据    2026 · PG · 01:41:52 · 动画 / 家庭 / 喜剧 / 冒险
③ 技术标识  4K · DV P7 · HEVC · TRUEHD · 7.1
④ Tagline
⑤ 简介
⑥ 评分      豆瓣 7.4 · IMDb 7.9
```

### 坐标

| 视图 | ③ 技术标识 | ⑥ 评分 | 备注 |
|---|---|---|---|
| 详情页 | 247 | 简介组内 top **140**（绝对 ≈468） | 评分行放进简介 group，tagline 缺失时整组上滑会自动带上它 |
| 首页 | 42 | **184** | 简介 textbox 105→**92**（A 方案），给评分行腾位 |
| 搜索 | 232 | **464** | 简介 textbox 之后 |
| 海报 51 | 262 | **534** | 新增 group，带 season 的滑动动画 |

### 同时定稿的视觉参数

| 项 | 值 |
|---|---|
| 胶囊底 | **黑 40% `66000000`**（原白 20% 在亮画面上会消失） |
| 图标间距 | 8 → **12** |
| 文字胶囊内边距 | 18 → **14** |
| 评分胶囊 | 与技术标识同款黑底（114 / IMDb 128） |

`NaraOnlineRatingsRow` 的 `inline_flags` 机制已删除（四处都改成"标识在上、评分在下"，
这个开关没有调用者了）。`VideoTechnicalFlagsRow` 重新加回，四处复用。

---

## 十三、终版（第三次修订，已实施）

用户明确：**评分和技术标识合并成一行，整体放在简介下方**；首页简介高度恢复 105。

### 版式

```
① Clearlogo / 标题
② 元数据    2026 · PG · 01:41:52 · 动画 / 家庭 / 喜剧 / 冒险
③ Tagline
④ 简介
⑤ 评分 + 技术标识 一行   ← 豆瓣 · IMDb · 4K · DV · HEVC · TRUEHD · 7.1
```

### 坐标（简介底 → 合并行 = 24px，2026-10-27 23:02 定稿）

| 视图 | 元数据 | Tagline | 简介 | 合并行 | 简介底→行 |
|---|---|---|---|---|---|
| 详情页 | 205 | **247** | 285（组内 textbox top 2 / h132） | 组内 **158** | 24 |
| 首页 | 0 | — | **42**（h105） | **171** | 24 |
| 搜索 | 194 | **232** | **272**（h100） | **396** | 24 |
| 海报 51 | — | **262** | **300**（h134） | **458** | 24 |

### 结构

- `NaraOnlineRatingsRow` 的 `inline_flags` 机制保留并启用（四处都传 true）
- `VideoTechnicalFlagsRow`（独立标识行）再次删除 —— 四处都走合并行，没有调用者
- 详情页的合并行放在**简介组内部**（相对坐标 150），随 tagline 缺失时的整组上滑一起动

### 视觉参数（不变）

胶囊底 黑 40% `66000000` · 图标间距 12 · 文字内边距 14

> 间距迭代记录：8 → 16（用户嫌小）→ **24（定稿）**。24 的依据：16 太挤、32 会让胶囊行
> 与上文脱节；且简介是固定高度 textbox，文字短时框内本来就有空白，实际视觉间距已大于设定值。

### 13.1 简介上方补 12px 间距（2026-10-27 23:08）

元数据 label 声明高度 38，但文字实际只有 ~18px，所以"元数据 → 简介"的坐标间隙
虽然只有 0–4px，视觉上约 24px，仍然偏挤（用户截图确认）。四处统一把简介下移 12：

| 视图 | 简介 | 合并行（跟移） |
|---|---|---|
| 详情页 | 简介组 285 → **295** | 组内 158（不变） |
| 首页 | 42 → **54** | 171 → **183** |
| 搜索 | 272 → **282** | 396 → **406** |
| 海报 51 | 300 → **310** | 458 → **468** |

详情页有 tagline 时 tagline→简介 12px；无 tagline 时整组上滑 38，元数据→简介 14px。

**首页紧凑态**（hero 收起时）的简介同样偏挤（元数据行 202–242 → 简介 245，仅 3px），
已一并下移 12：**245 → 257**。电影合集 Hero 的简介上方间距本来就是 14px，未动。

### 13.2 简介上下间距统一为 24（2026-10-27 23:14，定稿）

原则：**简介作为一个独立文本块，上下留白对称**。复算结果：

| 视图 | 上方元素底 | 简介顶 | 上间距 | 简介底 | 合并行 | 下间距 |
|---|---|---|---|---|---|---|
| 详情页 | 285 | 309 | **24** | 441 | 465 | **24** |
| 首页展开 | 38 | 62 | **24** | 167 | 191 | **24** |
| 首页紧凑 | 242 | 266 | **24** | 357 | —（评分在元数据行右侧） | — |
| 搜索 | 270 | 294 | **24** | 394 | 418 | **24** |
| 海报 51 | 300 | 324 | **24** | 458 | 482 | **24** |

坐标：详情页简介组 307（组内合并行 158）；首页 简介 62 / 合并行 191、紧凑态 266；
搜索 294 / 418；海报 51 324 / 482。

### 13.3 修正：合并行位置必须按调用方的简介高度算（2026-10-27 23:19）

**错误**：13.2 里把合并行写死在组内 158，是按 `synopsis_height` 默认值 132 算的。
但三个调用方传的高度都不同：

| 调用方 | synopsis_height | 正确位置 = 高 + 26 |
|---|---|---|
| DialogVideoInfo（详情页） | **105** | **131** |
| View_501_Poster | 100（电影）/ 134（剧集） | 126 / 160 |
| View_50_List | 134 / 134 | 160 / 160 |

写死 158 导致详情页多空 51px（158 − 107）。

**修复**：`VideoInfoHeroContent` 新增 `ratings_top` / `ratings_top_tv` 两个参数，
调用方按「简介高 + 26」传入；组内改成电影/剧集两条评分行，各自按 DBType 显示。
复算后四处下间距都是 **24**。

**教训**：改共享组件的位置前，必须先列出**所有调用方实际传的参数值**，
不能拿 `param` 的默认值当事实。

### 13.4 修正：评分行必须跟随简介框的条件位移（2026-10-27 23:22）

搜索和海报视图的简介框带**条件上滑动画**（tagline 缺失 / 剧集 / 季时整块上移），
但我把评分行放成了独立控件、没带同样的位移 —— 简介上移、评分行不动，间距被撑大。

| 视图 | 简介框位移 | 评分行原来 | 已补 |
|---|---|---|---|
| 搜索 | movie+无 tagline **−38**；is_tv+无 tagline **−32** | 无 | 同两条 |
| 海报 51 | tvshow **−57**；season **−64** | +32（season） | −57 / −64 |

其余三处本来就安全：详情页三视图的评分行在简介**组内部**（组带动画）；
首页展开态和紧凑态的简介与评分行都没有位移动画。

**规则**：评分行与简介框分离时，**必须复制简介框的全部 `<animation effect="slide">` 条件**，
否则任何一条条件命中都会让间距失配。

### 13.5 评分胶囊收窄（2026-10-27 23:35）

用户反馈"评分胶囊右边空太多"。原因：`font13` 在 1080p 下是 27px，
`7.4` 实测 40px、`8.9` 42px、`10.0` 53px；label 框按最长的 `10.0` 给了 56px，
且左对齐 → 16px 空白全堆在右侧，加内边距 12 共空 28px。

| 项 | 原 | 现 |
|---|---|---|
| 豆瓣 / TMDb / 烂番茄 | 宽 114，label 56 | **102 / 44** |
| IMDb | 宽 128，label 52 | **120 / 44** |

`10.0` 会裁掉末位右边缘 —— 已确认实际不会出现（豆瓣最高 9.7 / IMDb 9.3）。
不改成"显示成 10"或"显示空白"：前者要给四种评分源各写一份条件变量，后者直接丢信息，都不值。
