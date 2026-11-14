# 交接说明（Mistuary 2.2.1）

> ⚠️ **短期交接快照看 [`docs/handover-2026-10-30.md`](handover-2026-10-30.md)** ——
> 那份是 2026-10-30 夜的短期交接（当时改了什么、还剩哪三件事、分辨率约束、
> 踩过的坑）；本文是长期文档，讲依赖、工具链与发版，现状以 `addon.xml` / `git status` 为准。

> 读这个之前先读 `.workbuddy-ai/memory/MEMORY.md`（长期约定）。
> 本文只讲**现状、依赖、工具链、发版**，不讲历史。
> **新接手的三步**：① 本文 §8 看现状与待办 ② `docs/README.md` 看文档索引
> ③ 要动音乐页读 `docs/vinyl-helper-plan.md`；要动插件读 `docs/helper-plugin-plan.md`
> 和插件仓库 `docs/HANDOVER.md`。
> ④ 拿到外部校验报告（如 `docs/skin.mistuary_report.txt`）时，先读
> `docs/report-triage-2026-10-29.md` 分诊，不要按 445 errors 全量修。

---

## 0. 四条铁律（每轮开工先看）

1. **不要擅自 `git commit` / `push` / 发版**。改完先说明改了什么 + 验证结果，等指令。
   **"改一次就递交一次"是错的**（2026-10-30 用户明确要求）：同一处问题经常要反复调
   —— 例：OSD 技术标识连改 4 轮（图标→文字→图标→文字），每轮都提交就把一个问题的
   试错过程拆成了一串无意义提交，后面全是同一个问题。
   固定动作：**改 → 同步实机 → 说明 → 等用户确认 → 用户说"递交"时再按主题分类提交**。
   同一主题的反复修改**合并成一个提交**，别按时间线切。
   **"递交"只是 `git commit`，不是 `git push`**（2026-10-31 用户明确纠正）：
   用户说"递交"时 commit 完就停，报提交列表；只有明确说"推送"才 push，
   说"发版 / 打 tag"才升版本号。三个动作分开确认。
2. **改皮肤外观先给方案**（XML 结构、贴图、半径、布局），说清影响面 + 备选，
   等点头再动文件。只读排查（grep / 看图 / 读文档）不受限制。
3. **同步实机一律用散包**：`python tools/sync_to_kodi.py --loose`
   —— 跳过 `Textures.xbt` 并把它挪成 `.off`，改 png 只需重载皮肤（F5）即可生效。
   **只有用户明确说"打 tag / 发版"时才 `python tools/xbt_tool.py pack`。**
   打包会让用户必须完全重启 Kodi 才能看到新图，开发期极影响效率。
   ⚠️ 第一次切散包时 Kodi 正占用 `Textures.xbt`，挪不动 —— 让用户先完全退出 Kodi，
   再跑一次 `--loose` 即可。
4. **改完就自动同步实机，不用再问**（2026-10-30 用户要求，覆盖以前"同步前先问"那条）。
   每完成一次修改，自己跑一遍 `python tools/sync_to_kodi.py --loose`，再告诉用户
   "已同步、重载皮肤（F5）即可"。
   **这条是有代价换来的**：2026-10-30 修「排序方式点了没反应」时，因为等用户点头才同步，
   用户先自己重载了一次皮肤，跑的还是旧文件，结论变成"还是没生效"——白绕一轮。
   同步本身不改仓库、不影响别人，没有需要征询的理由；**要问的是 commit / push / 发版**。

> **分 hunk stage 之后要立刻提交，不能留到下一批。**
> 场景：`docs/HANDOVER.md` 两个人同时改，用 `git apply --cached` 只 stage 自己那几个 hunk
> 是对的；但 stage 完如果先去提交别的文件，`git add <别的文件>` 之后
> **已 stage 的 hunk 会被一起带进那个提交**，结果文档改动混进了功能提交
> （2026-10-30 实际发生：`6a40452` 电源菜单提交里混了 2 行文档）。
> 固定动作：**分 hunk stage → 当场 commit → 再做下一批**。

---

## 1. 一句话现状

`main` 分支上的通用版皮肤，**Kodi 22 及以上**可用（1.5.2 起不再支持 21，见 §5.2），
版本以 `addon.xml` 为准（当前 **2.2.1** 已发布）；历史发版记录见 §8.2。
最近一次已发布说明见 `changelog.txt` 顶部 2.2.1 段。
`handover-2026-11-03.md` 已归档，只作当时快照。helper **0.5.0** 已发布。
原计划单独发布的 1.4.1 与 1.5.0（两个 tag/Release 均已撤回）已合并进 1.5.1。

**接手时先看工作区状态**：截至 2026-11-10，`main` 已同步，**`v2.2.1` 已发布**
（背景压暗四档收尾、文件/收藏 list 遮罩同档）。
具体以 `git status` / `git log origin/main..HEAD` 为准，本节不钉 hash 和提交数。
`Textures.xbt` **858 张 / 8.8 MB**（1.2.0 是 802 张 / 10.2 MB，1.9.0 因续播圆环 101 帧增加），单测 **118 项全过**。

> 推送 / 工作区状态以 §8.1 的 `git status -sb` 为准，本文不钉提交号和领先数。

### 2026-10-29 下午（随 1.3.0 发布）

| 主题 | 落点 | 提交 |
|---|---|---|
| **音乐库无 fanart 背景兜底** | `DefaultBackground` 新增可选参数 `fallback` / `fallback_visible`（默认空 + false，其余 18 个调用方行为完全不变）；`MyMusicNav` 传音乐页那张背景图。原先歌曲没有 fanart 时整页只剩 `primary.jpg × #404040 ≈ RGB(16,19,27)`，看着就是纯黑 | `6c357c4` |
| **海报墙卡片格 264 → 260** | 恢复 7 列（264 时 7×264=1848 吃光余量，真机掉成 6 列）。`View_500_Wall` 4 处 + `View_54_InfoWall` 2 处 | `d5e0461` |
| **电源菜单补齐** | 从只有「退出」变成 6 个：退出 / 关机 / 重启 / 待机 / 休眠 / 重载皮肤。全部挂 `System.Can*` 能力标志自动显隐 —— Windows / CoreELEC 5 个，安卓只剩 2 个。面板 600×530 → **400×456**（有休眠时 526，两层背景按 `System.CanHibernate` 切）。「关闭系统电源」改用皮肤字符串 `31774`「关机」 | `dcecec7` |
| **Windows 电源菜单只留「退出 / 设置」** | 2026-11-05 用户要求：Windows 上不再显示重启 / 待机 / 休眠 / 关机（4 个按钮加 `!System.Platform.Windows`），背景新增 2 条 Windows 档（202 / 142），其余 16 条非 Windows 档加 `!System.Platform.Windows` 前缀。CoreELEC / Linux / macOS / Android 行为不变（Android 天然只有退出 / 设置） | 本次 |
| **死分支清理** | `nara_dialog_glass` 恒 true 留下的 40 处死分支、65 处恒真条件、6 个 `NaraDialogLegacy*` 定义、1 张孤儿贴图（`dialogs/dialog-bg.png`）全部删除，**表达式本身也删了**。净减 180 行（§5.5 第 5 条） | `1bf854a` `128cfd4` |
| **文档** | 顶部新增 §0 三条铁律；§5.5 增加第 4、5 条 | 同上 |

> **死分支清理怎么验证的**（这批改动看着大，其实可证明）：把改动前的 XML 用脚本做一次
> "机械变换"（删 `!$EXP[...]` 块 + 去恒真 condition），再和现状**逐字节比对** ——
> 25 个文件里 **24 个完全一致**，剩下 1 个（`Includes_DialogGlass.xml`）是额外删了孤儿
> include 和改注释，人工逐行核对。另外 `$PARAM` 违规集合改动前后完全相同（177 → 177），
> 说明没留下悬空参数。实测 6 个可无上下文打开的窗口全部 0 条皮肤错误。

### 2026-10-29 本轮改动（已随 1.2.0 发布）

| 主题 | 落点 |
|---|---|
| 主评分来源四档 + 手选优先 | 设置 707、`NaraOnlineRatingsRow`、`NaraDefaultRatingSourceVar`（2026-11-05 改为按类型读取，见 §5.7） |
| 搜索首字母改前缀匹配 | `sorttitle` 用 `startswith`，并移除 `actor` / `director` / `genre`（§5.10） |
| 帮助文案统一 | 三档透明度改名「弹窗透明度」，26 条帮助条改陈述式、双引号 |
| 依赖插件规划 | 新增 `docs/helper-plugin-plan.md`（服务端搜索 / 豆瓣 / 代表集标识） |

### 2026-10-28 圆角改造（已随 1.2.0 发布）

一批改动，主题是"海报真圆角 + 焦点环贴边 + 卡片间距"：

| 文件 | 改了什么 |
|---|---|
| `xml/View_54_InfoWall.xml` | `InfoWallMovieLayout` 的海报改用 `diffuse` 遮罩；焦点环改 `ring_card_246x354_r13` @ `(7,−1)`（外扩 1px、内缘压进海报 2px）；清掉 7 处 `bordersize`；卡片格 260 → **264** |
| `xml/View_500_Wall.xml` | 电影/剧集 + 收藏三个卡片格 260 → **264**（左右空档 16 → 20，见 §5.9） |
| `xml/View_51_Poster.xml` | 卡片改用 diffuse 遮罩；**电影与季列表合并成一套布局**（378×567 @ (21,205)），细边 `edge_378x567_r12` 保留 |
| `xml/Includes_Search.xml` | 搜索结果卡 214×321 改遮罩 r11，环换 `ring_card_216x323_r12` |
| `xml/Includes_Home.xml` | 横版 320×180（正在观看 ×2、媒体库 ×2，含 5 层封面）改遮罩 r9；专辑 186×186 改遮罩 r9；环换成 322×182 / 188×188 |
| `tools/gen_corner_masks.py` | 新增 `DIFFUSE_MASKS` + `build_diffuse()`（羽化遮罩）；文件头结论改正；清掉 3 张无引用尺寸 |
| `tools/gen_rings.py` | 新增 `ring_card_246x354_r13`、`EDGES`（1px 圆角细边）；文件头补「环怎么摆」的规则表 |
| `media/shapes/` | 新增 `mask_244x352_r12`、`ring_card_246x354_r13`、`corner_*_r12`、`edge_*_r12`；删 3 张无引用 |
| `docs/HANDOVER.md` / `docs/README.md` | 文档同步 |

**第一批**：7 处视图换成了 diffuse 真圆角（2026-10-28），实色角部遮盖 `corner_*.png`
已彻底退役（`media/shapes/` 里一张不剩，`gen_corner_masks.py` 的 `MASKS` 表也清空了）。

| # | 位置 | 卡片 | 遮罩 | 配套 |
|---|---|---|---|---|
| 1 | `View_51_Poster` 封面（电影/剧集/合集/季 共用） | 378×567 | `mask_378x567_r12` | 底板 `round12` + 细边 `edge_378x567_r12`（半径 = 遮罩） |
| 2 | `View_51_Poster` `NaraPosterDeckCard` | 378×567 | `mask_378x567_r12` | 细边 `edge_378x567_r12` |
| 3 | `Includes_Search` 结果卡（搜索 + 横排共用） | 214×321 | `mask_214x321_r12` | 环 `ring_card_216x323_r13`；底板也挂同一张遮罩 |
| 4 | `Includes_Home` `HomeContinueWatchingRail` ×2 | 320×180 | `mask_320x180_r9` | 环 `ring_card_322x182_r10` |
| 5 | `Includes_Home` `HomeMediaLibraryRail` ×2（5 层封面全部挂遮罩） | 320×180 | 同上 | 同上 |
| 6 | `Includes_Home` `HomeWidgetAlbumCard` | 186×186 | `mask_186x186_r9` | 环 `ring_card_188x188_r10` |
| 7 | `View_54` `InfoWallFavouriteLayout` | 244×352 | `mask_244x352_r12`（与电影卡统一） | 环 `ring_card_246x354_r13` |

2026-10-28 第二批补上了四个**从来没做过圆角**的视图：

| 位置 | 卡片 | 遮罩 |
|---|---|---|
| `DialogVideoInfo` 详情页大海报 | 452×672 | `mask_452x672_r12` |
| `View_501_Poster` 横排大图 | 452×672 | 同上（复用） |
| `View_53_Shift`（2 层） | 334×480 | `mask_334x480_r12` |
| `View_55_WideList`（3 层） | 438×366 / 160×160 / 240×240 | `mask_438x366_r12` / `mask_160x160_r9` / `mask_240x240_r9` |

2026-10-28（换人开发前）最后扫了一遍全皮肤的图片控件：共 **33 个** ≥100px、非全屏、没挂遮罩的图片控件。
按"该不该圆角"分成三类，A 类全部补齐，B / C 类故意不做：

- **A 类（卡片，全做）**：见下表。其中前 3 条已随 `f225819` 提交；后 9 条（含 8 张新遮罩）
  已随后续提交进入仓库；当前工作区状态以 `git status` 为准。
- **B 类（贴边 hero 大图，故意不做）**：圆角会露出后面那层底色，反而难看。包括 `View_50_List`
  的 540×850 / 540×470（视频分支）、730×318，`View_54_InfoWall` 的 336×300 / 316×316 / 316×218。
  > **2026-10-29 试过又撤回**：给 `View_50_List` 540×470 的歌曲分支、`View_54_InfoWall` 的
  > 316×316 / 316×218 加过 `diffuse`，实测**不生效** —— `aspectratio keep` 时控件尺寸和
  > 实际画出来的图片尺寸不一致，遮罩对不齐，结果还是方角。三处已全部回退。
  > **结论：`keep` + 绘制尺寸随图片变化的控件，不要挂 diffuse。**
- **C 类（透明 PNG，不用做）**：clearlogo（720×145 / 660×170）、默认图标（DefaultActor 128×128、
  收藏默认 244×352）—— 本身没角。

| 位置 | 卡片 | 遮罩 | 提交状态 |
|---|---|---|---|
| `Includes_DialogVideoInfo_TvEpisodes` 剧集缩略图（item + focus 两处） | 336×189 | `mask_336x189_r9`（新增） | 已提交 `f225819` |
| `Includes_Home` 首页「类别」卡背景（两处） | 276×160 | `mask_276x160_r9`（新增） | 已提交 `f225819` |
| `Includes_Search` 搜索 hero 海报（无 fanart 时） | 452×672 | `mask_452x672_r12`（复用） | 已提交 `f225819` |
| `DialogMusicInfo` 封面（2026-10-29 重做） | 452×452 | `mask_452x452_r12`（新增） | 已落地 |
| `View_55_WideList` 专辑图 / 横版图 | 340×340 / 438×246 | `mask_340x340_r12` / `mask_438x246_r12`（新增） | 已提交 |
| `View_50_List` 列表预览 | 224×300 / 160×160 / 184×184 | `mask_224x300_r12` / `mask_160x160_r9` / `mask_184x184_r9`（新增） | 已提交 |
| `Includes_VideoOSD` 播放列表缩略图 | 356×200 | `mask_356x200_r12`（新增） | 已提交 |
| `DialogAddonInfo` 插件信息截图 | 656×312 | `mask_656x312_r12`（新增） | 已提交 |
| `Includes_DialogVideoInfo_Cast` 演员头像 | 110×150 | `mask_110x150_r9`（新增） | 已提交 |

> **2026-10-29 音乐信息页重做**：`DialogMusicInfo` 改用 `mask_452x452_r12`；
> 旧的 `mask_570x570_r12` / `mask_190x190_r9` 已删除，生成器表同步移除。
> `--orphans` 当前 0 张。

新遮罩都在 `tools/gen_corner_masks.py` 的 `DIFFUSE_MASKS` 表里登记过；发版时 `xbt_tool.py pack`
会重打包。`audit_skin.py --strict` / `gen_corner_masks.py --check` 通过。

三条硬约束（§5.4.1 有完整说明）：
**① 遮罩尺寸必须和控件完全一致；② 环 = 卡片 +2、环外半径 = 遮罩半径 +1（内缘压进 2px）；
③ 海报下面的圆角底板（`round<N>.png`）半径不能小于遮罩半径，否则四角会从下面露出来。**

> 表里"目标遮罩"都沿用**当前半径**，即只换机制、不改观感 —— 迁移的目的是消掉
> "亮背景上四角露深色斑点"，半径统一是另一件事（见 §7 遗留）。

1.1.1 的重点是**影片技术标识图标化**：`media/techflags/color/` 存 97 张归一化图标
（`Includes_VideoTechnicalFlags.xml` 里 206 条 key → 图标的映射），
`tools/gen_techflag_icons.py` 负责生成（含冷门格式的白字标兜底）并维护 IconMap；
评分与技术标识合并成一行、整体移到简介下方。设计取舍与坐标见
`docs/techflag-icons-plan.md`，素材来源与许可见根目录 `CREDITS.md`。

---

## 2. 运行时依赖

### 皮肤本体不含 Python 脚本，但依赖 Mistuary Helper

`addon.xml` 的依赖：

```xml
<import addon="xbmc.gui" version="5.18.0"/>
<import addon="script.mistuary.helper" version="0.5.0"/>
```

`script.mistuary.helper` 自 **2026-11-05** 起是**硬依赖**（用户决定）：未安装 /
被禁用时，Kodi 会判定依赖不满足，皮肤**无法加载**。安装顺序必须是先装插件再切皮肤。
`tools/` 里的所有 `.py` / `.ps1` 都是**构建期工具**，不参与运行，也不进发布包。

### 皮肤探测两个第三方插件

| 插件 | 用在哪 | 没装会怎样 |
|---|---|---|
| `plugin.service.emby-next-gen` | 首页媒体库栏目、分类 widget 的显示条件 | 只是不显示那几行，其余正常 |
| `script.embuary.info` | 演员头像点击查人 | 点击无反应 |
| `script.mistuary.helper`（**必需**） | 服务端搜索、豆瓣评分、媒体库封面同步、播放列表补全、文件播放记录 | 皮肤**不加载**（`addon.xml` 硬依赖） |

两个可选插件用 `System.AddonIsEnabled()` / `System.HasAddon()` 做运行时保护。
`script.mistuary.helper` 是**独立仓库**，契约与阶段规划见
[`helper-plugin-plan.md`](helper-plugin-plan.md)；**不要塞进皮肤包**
（Kodi 不允许 skin addon 携带可执行脚本）。

---

## 3. 仓库结构

### 会进发布包的

```
addon.xml  changelog.txt  README.md
LICENSE        GNU GPL v2 全文 + 第三方素材声明摘要（GitHub 靠它识别许可）
CREDITS.md     第三方素材的完整来源/版本/许可正文（OFL、CC BY-SA 要求随副本分发）
xml/            全部窗口与 include
colors/         defaults.xml（透黑）/ light.xml（透白，只写差异色）
fonts/          Inter-Unicode-Regular.ttf（自带 CJK，见 §5.1）
language/       resource.language.*/strings.po
media/          松散图片 + Textures.xbt（打包后只带 xbt）
extras/         随包素材，运行时用 special://skin/extras/... 引用
  backgrounds/    运行时背景图（primary.jpg）
  artwork/        首页媒体库卡片兜底图（library-default.jpg）
  playlists/      widget 用的播放列表（*.xsp）
```

> `extras/` 这个名字是 Arctic 系皮肤的约定（jurialmunkey / narapeka 一脉）：
> **随包发布的素材**放这里，图片不进 `Textures.xbt`，是松散文件，用户可以直接替换。
> 不要把它和构建工具混在一起——构建工具在 `tools/`。

> 首页「媒体库」卡片的分区封面全部由 Mistuary Helper 同步：
> `addon_data/script.mistuary.helper/library_icons/<库名>.png`。
> Helper 给每个库都写文件（Emby 没设封面时写 1×1 透明占位），所以皮肤那层永远能加载。
> 优先级：自定义目录 > Helper 同步 > `extras/artwork/library-default.jpg`。
> E4K 本身不导出库封面，别去找它的 `libraryart` / `library_icons` 目录。

### 不进发布包的（`release.yml` 里显式排除）

```
.github/  .workbuddy-ai/  docs/  build/  __pycache__/  *.pyc
tools/         自检、测试、贴图生成器、xbt_tool.py
```

**`tools/` 整个目录都不进包** —— 它是纯构建期工具，Kodi 运行时不加载任何一行。
2026-10-27 之前它叫 `extras/`，与素材目录撞名；`xbt_tool.py` 原本在根目录，也一并收了进来。

---

## 3.5 开发临时文件放哪

**不要丢在插件根目录。** 渲染预览图、调试输出、一次性脚本一律放 `docs/scratch/`：

- 已 gitignore（`docs/scratch/*`，只保留 README）
- `docs/` 整个目录不进发布包，所以放这里天然安全
- 用完就清：`rm -rf docs/scratch/*`

之前根目录堆过 7 张效果图，试打包时才发现它们会被打进包里。

---

## 3.9 全量审计报告

`docs/audit-2026-10-30.md` —— 按「依赖残留 / 语法兼容 / 资源清理 / 性能渲染 /
UI 逻辑 / 打包合规」六个维度做的一次完整审计（v1.3.1 基线）。

结论：**0 个 🔴**，6 个 🟡（已修，文末有修复记录），3 个 🟢、5 个 ⚪。
文末还有一份**打包前自检清单**，发版前照着跑一遍。

> 再审计时优先复用里面的检查方法，尤其这两条踩过的坑：
> ① 重复 id 要按 `include` / `window` **作用域**查，按文件查会被 `$PARAM[id]` 大量误报；
> ② 焦点引用里 `39999` 是**故意的阻断标记**（`SetFocus(39999)` 让焦点不动），不是 bug。

## 4. 开发工具（`tools/`）

### 必跑的三条

```bash
python tools/audit_skin.py          # 静态自检：缺失 include/变量/字体/贴图/字符串、浮窗遮蔽、设置读写配对
python tools/audit_skin.py --orphans        # 反向：盘上有、XML 里没人引用的贴图
python tools/audit_skin.py --dead           # 反向：没人用的变量 / include / 皮肤字符串
python tools/gen_techflag_vars.py --check   # 技术标识变量是否与 map 同步
python tools/gen_techflag_icons.py --check  # 技术标识图标与 IconMap / TextMap 是否对齐
python tools/gen_home_nav_plates.py --check # 首页导航底板是否与生成结果一致
python tools/check_home_fanart_mask.py --check  # 首页遮罩判据是否与背景变量分支一致
python -m unittest discover -s tools -p 'test_*.py'   # 单元测试
```

`--orphans` / `--dead` 是**报告模式，永远返回 0**（不进 CI 闸门）——它们只能按字面匹配，
动态引用（`$PARAM[...]` 传值、变量套变量）需要人工确认，所以不当作硬错误。

> **删皮肤字符串之前先跑 `--dead`，别自己 grep `$LOCALIZE`。**
> 字符串有两种引用形态，只认第一种会误删：
> ① `$LOCALIZE[31764]`；
> ② `Skin.SelectBool(头部id, 31764|setting_name, …)` —— **头部和配对里的数字都是字符串 id**，
>    都不走 `$LOCALIZE`。2026-10-30 就是因为只扫了 ①，把三档透明度标题和 TMDb/IMDb
>    这 5 条正在用的字符串删掉了（已回滚）。
> `string_refs()` 现在两种都认，`tools/test_audit_strings.py` 有 8 条用例钉着。
它们存在的理由：`audit --strict` 只查"引用了但文件不存在"，查不出"文件在但没人用"，
`media/settings/background.png`（1.87 MB）就是这么在包里躺了半个月。

CI（`.github/workflows/release.yml`）在发版前会把这三条跑一遍，任一失败就中止。

### 贴图生成器（改了 `media/shapes/` 之后重跑）

| 脚本 | 生成 |
|---|---|
| `gen_glass_plates.py` | `glass<N>.png` 玻璃面板（9-slice，中心实、1px 透明边） |
| `gen_rings.py` | `ring_card_*.png` 描边环（**1:1 整图，不能 9-slice**） |
| `gen_corner_masks.py` | `mask_*.png` **diffuse 圆角遮罩**（真圆角，见 §5.4.1）。`corner_*.png` 老式实色角部遮盖**已退役**，`MASKS` 表清空 |
| `gen_techflag_icons.py` | `techflags/color/` 的技术标识图标（含冷门格式白字标兜底），并维护 IconMap；`--check` 供 CI |
| `scan_rounded.py` | 列「应圆角但没挂 `diffuse`」的控件（A 类内容图）；`--all` 连透明 PNG 一起列 |
| `gen_osd_filled_icons.py` | ~~OSD 实心图标~~ **2026-10-29 已删**：产物从没被引用，源 SVG 留在 `tools/osd_icons/` |
| `gen_osd_filled_icons.py` | OSD 实心功能图标 |
| `gen_music_cover.py` | 音乐播放页兜底封面（黑胶 + 唱臂） |
| `generate_nara_cast_icon.py` | 演员图标 |
| `generate_nara_fanart_mask.py` | fanart 遮罩 |
| `generate_nara_osd_icons.ps1` | OSD 图标（PowerShell） |
| `generate_nara_settings_icons.ps1` | 设置图标（PowerShell） |

### 专项校验（2026-11-03 补）

| 脚本 | 校验 |
|---|---|
| `gen_home_nav_plates.py --check` | `Home.xml` 导航底板是否与「文字宽 + 60、100% 居中」的生成结果一致 |
| `check_home_fanart_mask.py --check` | 首页遮罩三条 `expression` 与 `HomeFanartVar` / `HomeVideoHeroFanartVar` 的容器分支是否一致；表达式里是否混进了 `$EXP` 等非法写法 |
| `dedupe_favourites.py` | 收藏夹同名条目去重（维护脚本，不进 CI） |

#### 开发期用散包，递交/发版才打包（2026-10-28 定）

打包成 `Textures.xbt` 之后，**改一张图要重打包 + 重启 Kodi**，迭代太慢。
所以分两种同步方式：

```bash
# 开发期（默认）：散包。跳过 Textures.xbt，并把目标端那份挪成 .off
python tools/sync_to_kodi.py --loose

# 递交 / 发版前：打包 + 正常同步
python tools/xbt_tool.py pack
python tools/sync_to_kodi.py
```

- `--loose` 会**跳过** `media/Textures.xbt`，并尝试把实机那份改名成 `.xbt.off`，
  强制 Kodi 读散图 → 之后改 png 只要**重载皮肤**就生效，不用打包、不用重启
- **Kodi 运行时 xbt 是被锁住的**，改名会失败，脚本会提示"先完全退出 Kodi 再跑一次"。
  只需要退出这一次，之后一直是散图状态
- 只改 XML 的话两种模式都一样（XML 不进 xbt）

**递交/发版前必须打包**：`python tools/xbt_tool.py pack`，否则包里还是旧图。

#### 提交纪律：只 stage 自己改的文件（2026-10-28 事故）

这个仓库**可能有多个 agent 并行改**，工作区里随时会有别人的未提交改动。
`git add -A` 会把它们一起扫进我的提交 —— 实际发生过一次：搜索 XML 被扫进
「音乐播放条渐变」提交、测试/文档/同步脚本被扫进「音质信息文字」提交，
最后只能重写 12 个提交的 hash 来拆开。

固定动作：

```bash
git status                      # 先看工作区有没有别人的改动
git add xml/Includes_MusicPlayer.xml   # 只加自己动过的文件
git diff --cached --name-only   # 核对：出现不属于本次的文件就撤
git commit -F -                 # 提交信息里写清改了哪几个文件
```

**永远不要 `git add -A` / `git commit -a`。**

#### 为什么 XBT 仍然写 v2，不跟 Kodi 22 升 v3（2026-10-28 结论）

| | Kodi 21 (Omega) | Kodi 22 (master) |
|---|---|---|
| 打包器写的版本 | `"2"` | `"3"` |
| 读取端最低版本 | 硬编码 ≥ 2 | `XBTF_VERSION_MIN = '2'` |
| 读取端最高版本 | **没有检查** | **没有检查** |

读取端只有 `if (version < MIN) return false;`，**不判上限**，而且解析逻辑与版本号无关
（宽/高/格式 u32、packed/unpacked u64、duration u32、offset u64 —— 两种版本布局完全一致）。
v3 是 Kodi 22 打包器的标记，配套新的 KD_TEX 格式字段；我们写的是普通 `XB_FMT`，用不上。

**结论：保持 v2。** 一个包同时给 Kodi 19/20/21/22 用；写 v3 没有任何收益，
只会把"能不能读"变成依赖未文档化行为。真正决定兼容性的是格式字段，不是这个版本字节。

### 手动 UI 测试（需要实机 Kodi）

PowerShell 三个（走 `SendMessage` 发按键）：

`test_nara_video_osd.ps1`、`test_nara_music_player.ps1`、`test_nara_window_ids.ps1`

Python 两个（`unittest`，纯逻辑校验，CI 也会跑）：

`test_nara_search_navigation.py`、`test_nara_settings_navigation.py`

---

## 5. 必须知道的约定

### 5.1 字体：Kodi 没有字形回退

`GUIFontManager::LoadTTF` 按文件名找一个完整文件，**缺字不会去别的字体借**。
现用 `fonts/Inter-Unicode-Regular.ttf`（Inter 4.000 + 16502 汉字，OFL 1.1，4.94MB），
`Font.xml` 全部 47 处 `<filename>` 指向它。粗体由 `FT_Outline_Embolden` 合成。
**文件名用原始名，不要缩写。**

### 5.2 只支持 Kodi 22（2026-10-31 改定）

`addon.xml` 声明 `xbmc.gui 5.18.0`（= Kodi 22）。**1.5.2 起不再兼容 Kodi 21。**

原因：技术标识用 `$MAP[]` 做「值 → 图标」映射，这是 22 才引入的语法，21 不展开、
会把 `$MAP[NaraTechnicalHdrIconMap,dv]` 原样画在屏幕上。1.5.1 及以前还有
`$EXP[nara_kodi21]` 的双轨分支，但两版行为差异越修越多、21 也从没实机验证过
（见 §8.7），索性砍掉，只留一条渲染路径 —— 少一个分支就少一类
「只有某种设备上才复现」的 bug。

Kodi 21 会在**安装时被拒绝**（依赖不满足），不会出现「装上了但界面是坏的」。
还在 21 上的人用 1.5.1 及以前的版本。

**Kodi 22 才有的标签 / 窗口（跑外部校验器时先看这里，别当成 bug 修）：**

| 类型 | 名称 | 备注 |
|---|---|---|
| 窗口名 | `dialogselectvideo` / `dialogselectaudio` / `dialogselectsubtitle`（12300–12302） | 旧版本靠兜底分支，现直接用 |
| 窗口名 | `RadioProviders`（10713） | 同上 |
| 标签 | `HdrDetail` / `TitleExtraInfo` / `EpisodePart` / `MediaProviders` / `Bookmarks` | 均配 `!String.IsEmpty` 保护 |
| 标签 | `SubtitleCodec` / `SubtitleName` / `AudioLanguageEx` | 字幕编码、音轨语言扩展名 |
| 标签 | `VideoStreamCount` / `PVRClientName` / `PVRInstanceName` / `PVRGroupOrigin` / `PVR.ClientCount` | 已分别改用 `HasVideoVersions` 或接受为空 |
| 标签 | `ListItem.ChannelLogo` / `ListItem.DecodedFileNameAndPath` | 版本列表路径统一用 `FileNameAndPath` |

**不要写的写法：**
- `<scroll>` 只认布尔字面量，写 `Control.HasFocus(...)` 会被判非法且不生效；
  需要“聚焦才滚动”只能拆成两套 label。
- 数字字面量不能进 `String.IsEqual(...)`，会被当作 info 标签（音乐 OSD 踩过）。
- `<texture>` 下写 `<fallback>` 无效，只有 `<label fallback="...">` 属性有效。

完整分诊见 `docs/report-triage-2026-10-29.md`。

### 5.3 透明度（用户可调）

两套主题：`colors/defaults.xml`（透黑）+ `colors/light.xml`（透白，只写差异）。

**2026-10-27 重构：从「浮窗 6 档 + 页面面板 4 档」→「两场景 × 5 档」→「三档 × 6 档」。**

| 设置项 | 皮肤设置名 | 管什么 | 默认 |
|---|---|---|---|
| **页面透明度** | `glass_page_op_1..6` | 全屏页面面板 + 页面里的卡片 / 胶囊 / 顶部导航条 + **设置中心 / 设置页侧栏** | 第 3 档 平衡 73% |
| **弹窗透明度** | `glass_float_op_1..6` | 叠在页面上的层：对话框、插件详情、插件设置、右键菜单、键盘、搜索键盘、非播放时的设置选择框 | 第 4 档 偏实 83% |
| **播放中透明度** | `glass_play_op_1..6` | 播放时的浮窗：OSD 设置（含视频/音乐 OSD 设置）、播放列表、书签、处理信息、播放控制条 | 第 2 档 通透 60% |

| 档 | 面板 `gl_*` | 遮蔽 `sc_*`（×0.6） | 合成 |
|---|---|---|---|
| 1 极透 | 32% | 19% | 45% |
| 2 通透 | 45% | 27% | 60% |
| **3 平衡** | 58% | 35% | **73%（页面默认）** |
| 4 偏实 | 71% | 43% | 83%（浮窗默认） |
| 5 厚实 | 84% | 50% | 92% |
| 6 实心 | 97% | 58% | 99% |

链路：三个设置共用同一套 `gl_1..6`；**遮蔽分两条，各跟各的档**（2026-10-30 改）：
页面级遮蔽跟页面档，浮窗级遮蔽跟浮窗档。原来浮窗借用页面档，
用户调「页面透明度」会连带改变所有对话框的观感（合成在 76%~88% 之间摆）。

| 变量 | 来源 | 用在哪 |
|---|---|---|
| `NaraGlassPageTintVar` | 页面档 | 全屏页面面板、页面内卡片、顶部导航条、设置中心/设置侧栏 |
| `NaraGlassFloatTintVar` | 浮窗档 | 对话框、插件详情/设置、菜单、键盘、非播放时的设置选择框 |
| `NaraPlaybackDialogTintVar` | 播放中档 | 播放 OSD 全系 + 播放控制条 |
| `NaraSettingsDialogTintVar` | 播放中档 / 浮窗档（按是否播放切换） | 视频/音乐 OSD 设置、播放中的设置选择框 |
| `NaraGlassScrimTintVar` | 页面档 | 页面级遮蔽：整屏页面、`DialogVideoInfo` / `DialogAddonInfo`、侧栏、`NaraPageScrim`（播放中改走 `scrim_osd`） |
| `NaraGlassFloatScrimVar` | 浮窗档 | 浮窗级遮蔽：对话框共用底、`NaraDialogScrim`、电源菜单、键盘、图片/PVR 信息、右键菜单、文本查看器、Home 左上角菜单弹层、设置类对话框 |

**为什么换维度**：用户感知的是"我在看片 / 我在翻页面 / 我打开了一个浮窗"，不是"这是浮窗还是页面面板"。
浮窗压在页面之上、底下还有内容要透出来，所以它要比页面更实 —— 三档默认值就是按这个顺序排的
（播放中 60% < 页面 73% < 浮窗 83%）。

**为什么是 6 档**：第一版 5 档的「平衡」是 83%，实机看下来偏实。整条梯子下移一格
（每档仍差 13 个点）+ 底下补一档 45%，默认档名不变（还是「平衡」）但值从 83% 变 73%，
用户不用手动调就透了一格；同时保留「实心」给亮背景。**档位名是 op_1..6，含义跟着梯子走，
所以调梯子等于调所有用户的观感** —— 动之前想清楚。

**已堵掉的旁路**：`glass_regular` / `glass_frosted` / `glass_dialog` / `glass_page`
四个固定色名全部删除，引用改接变量。侧栏"调了设置也不变"就是被 `glass_regular`
（固定 40% 黑）绕过去的。**以后不要再加固定色名的玻璃面板。**

**加新窗口时怎么选**：问自己"这块玻璃是页面的一部分，还是浮在页面上面"——
设置中心 / 设置页侧栏 / 设置页内容属于页面，走 `NaraGlassPageTintVar`；
非播放时弹出的设置对话框 / 选择框走 `NaraGlassFloatTintVar`；
播放中打开的 OSD 设置走 `NaraSettingsDialogTintVar`（播放中档，非播放时回落浮窗档）；
纯播放 OSD 走 `NaraPlaybackDialogTintVar`。`ContentPanel` 这个 include 默认走页面档，
调用方可以用 `<param name="tint">` 覆盖（PVR 频道 OSD 就是这么传播放中档的）。

### 5.3.1 皮肤设置的帮助条

底部帮助条 `textbox id=6`（`545,915` `1255×100`），内容来自
`Variables.xml` 的 `SkinSettingsHelpTextVar`。

**结构（顺序不能反）**：
1. **行级** `Control.HasFocus(<行 id>)` —— 40 个设置行各一条，先写
2. **分类级** `Container(9000).HasFocus(1..4)` —— 4 个侧栏分类兜底

变量是自上而下取第一条成立的 value，分类条件**一直成立**，放前面就永远轮不到行级。

**文案规矩**：
1. 写「怎么选」，不写「这是什么」——一句用途 + 默认值 + 什么情况该改。
   反例：「这是设置评分来源的地方」。正例：「开了神医助手的豆瓣覆盖就打开
   （值显示 Douban），没开就关掉（显示 IMDb）。」
2. **一句话说完，不超过 40 字**（三条透明度要列清覆盖范围，可以到 50 字）。
   删掉「想…就…」「比如」这类口头语。
3. **引号用 `“”`（弯双引号），不用 `「」`**。Kodi 官方中文包里 `“”` 出现 92 次、`「」` 只有 1 次，
   皮肤更早的字符串（「请进入“文件”区」）也是 `“`。`Inter-Unicode-Regular.ttf`
   含 U+201C / U+201D 字形（实测有墨迹，不是豆腐块）。

**行 id → 字符串 id 对照**（改文案只动 po，别动条件）：

| 页 | 行 id | 字符串 | 设置 |
|---|---|---|---|
| 首页 | 6110 / 611 / 6111 / 627 | 31802 / 31746 / 31747 / 31748 | 搜索 / 电影 / 编辑小组件 / 系列打开方式 |
| 首页 | 612 / 6121 / 626 | 31749 / 31750 / 31751 | 电视剧 / 编辑小组件 / 打开方式 |
| 首页 | 613 / 6132 / 625 | 31752 / 31753 / 31754 | 音乐 / 编辑小组件 / 专辑打开方式 |
| 首页 | 618 / 6181 / 619 | 31755 / 31756 / 31803 | 电视 / 编辑小组件 / 收藏夹 |
| 媒体 | 707 / 715 / 720 / 706 | 31740 / 31784 / 31812 / 31739 | 主评分来源 / 详情页显示豆瓣 / 详情页联网取豆瓣 / 视频卡片评分 |
| 媒体 | 708 / 705 / 709 / 6067 | 31741 / 31738 / 31773 / 31745 | 标题格式 / 媒体标识 / 技术标识 / 音乐电视海报 |
| 媒体 | 710 / 725 / 714 / 719 | 31737 / 31823 / 31781 / 31799 | 封面目录 / 同步封面 / 服务端搜索 / 高级设置 |
| 界面 | 711 / 712 / 713 | 31742 / 31761 / 31743 | 页面 / 弹窗 / 播放中透明度 |
| 界面 | 605 / 702 / 716 / 717 | 31744 / 31736 / 31698 / 31804 | 媒体背景图 / 自动滚动 / 收藏夹横版 / 收藏夹封面目录 |
| 播放 | 623 / 624 / 630 / 631 | 31757 / 31758 / 31805 / 31806 | 视频 OSD 自动关闭 / 关闭时间 / 音乐 OSD 自动隐藏 / 自动关闭时间 |
| 播放 | 721 / 722 / 723 / 724 | 31813 / 31814 / 31815 / 31822 | 按季补全 / 按目录补全 / 跨季补全 / 文件播放记录 |

### 5.3.2 设置页的分类（2026-10-29 重排）

4 个分类，名字对齐 Kodi 自己的词汇（不用自造词，也不要用 Kodi 那句机翻的
「屏幕菜单式调节」）：

| 分类 | 侧栏 id | grouplist | 行数 | 内容 |
|---|---|---|---|---|
| **首页** | 1 | `700` | 13 | 主菜单 4 个开关 + 4 个编辑小组件 + 3 个默认打开方式 |
| **媒体** | 2 | `610` | 12 | 封面文件夹、封面同步、媒体标识、技术标识、评分、标题格式、音乐电视海报、服务端搜索、豆瓣评分、高级设置 |
| **界面** | 3 | `600` | 7 | 页面 / 弹窗 / 播放中透明度、媒体背景图、剧情评论自动滚动、收藏夹横版 / 封面文件夹 |
| **播放** | 4 | `622` | 8 | 视频 / 音乐 OSD 自动关闭与时间、播放列表补全三项、文件播放记录 |

> **2026-11-05 起 helper 是硬依赖，不再单列「皮肤助手」分组**：侧栏从 5 项回到 4 项，
> 714 服务端搜索 / 720 豆瓣评分 / 719 高级设置并入「媒体」，721–724 补全与文件播放记录并入「播放」。
> 原有的 `System.AddonIsEnabled(script.mistuary.helper)` 运行时判断一并删除。

**改分类时只换 grouplist 的子项，别动 grouplist 本身** —— `onup`/`ondown` 的跳转链
和 4 个分类一一对应，保持 4 个 grouplist 就不用重连导航。这也是当初从 5 类改回 4 类的
实质原因（不只是命名）。

- `700` 有 13 行、`610` 有 12 行，都装不下，必须有 `<pagecontrol>60</pagecontrol>`。
- 每个 grouplist 的 `top 161 / width 1315 / height 708` 写在**子项之后**，
  用脚本重排时别把尾部属性丢了。
- 分类名是 `31769`–`31772`；分类说明复用 `31129`/`31130`/`31169`/`31171`
  四个旧 id（按 `HasFocus(1..4)` 的位置对应，所以变量不用改）。

### 5.4 圆角

| 元素 | 半径 |
|---|---|
| 玻璃面板 | **20**（只有 `glass20`） |
| 选中行 / 焦点条 | **14**（只有 `round14`） |
| 胶囊（导航、动作栏） | 接近半高，单独保留 |

**`border` 只给实心填充用。描边环一律 1:1 整图，且必须最后绘制。**

#### 5.4.1 给**图片**裁圆角：用 `<texture diffuse="遮罩.png">`（2026-10-28 定论）

**这是唯一正确的路子，别再自己发明。** Kodi 的 `<texture>` 有个 `diffuse` 属性：

```xml
<texture background="true" diffuse="shapes/mask_244x352_r12.png">$INFO[ListItem.Art(poster)]</texture>
<aspectratio scalediffuse="false">scale</aspectratio>
```

- `diffuse` 指定的图会**逐像素乘到原图上**，所以遮罩里"黑的/透明的地方"就把图压暗/抠掉，
  海报四角就是**真的圆角**，背景直接透出来。
- 遮罩长这样：圆角内 `(255,255,255,255)`，圆角外 `(0,0,0,0)`，边缘羽化 3px 左右。
  **RGB 和 alpha 要一起给** —— 实测只给"白 + alpha 0"完全没效果。
- **遮罩尺寸必须和控件完全一致**，否则会被拉伸、圆角变形。所以是"一尺寸一张"，
  放在 `media/shapes/mask_<w>x<h>_r<半径>.png`，由 `tools/gen_corner_masks.py` 的
  `DIFFUSE_MASKS` 表生成。
- 参考实现：Arctic Fuse 3 的 `media/diffuse/card_w731_h310.png`（731×310，r≈14）。

**`scalediffuse` 必须和 `aspectratio` 配对（2026-10-28 补，踩过）**

| aspectratio | 要不要写 `scalediffuse="false"` | 为什么 |
|---|---|---|
| `scale` / `stretch`（图填满控件） | **要写** | 遮罩映射到控件矩形；图和控件同尺寸，两者等价 |
| `keep`（图可能比控件窄/矮） | **不要写**（用默认 `true`） | 默认时遮罩**跟着图片走**，圆角才真的落在图上 |

写成 `keep` + `scalediffuse="false"` 会**完全没有圆角效果**：源码里
`m_diffuseScaleU = m_diffuseU * m_vertex.Width() / m_width`，采样窗口只覆盖遮罩中间那块，
四角的圆弧被窗口切掉了（`GUITexture.cpp:441`）。2026-10-28 一次性清掉了 10 处
（`DialogAddonInfo` ×2、`View_50_List` ×3、`View_55_WideList` ×5）。

**配套：焦点环怎么摆（2026-10-28 修正，之前的「+3」是错的）**

| | 环尺寸 | 环外半径 | 结果 |
|---|---|---|---|
| 配遮罩的圆角卡片 | 卡片 **+2**（外扩 1px） | 遮罩半径 **+1** | 内缘压进海报 2px，盖住羽化边，环贴在海报上 |
| 方角卡片（无遮罩） | 卡片 +6（外扩 3px） | 卡片圆角 +3 | 环在卡片外面一圈 |

海报墙实测：`mask_244x352_r12` 配 `ring_card_246x354_r13` @ `(7,−1)`。
圆心 (8−1+13, 0−1+13) = (20,12)，与海报圆角圆心 (8+12, 0+12) 重合 → 两个圆弧同心。

**圆角半径按短边分两档（2026-10-28 定论）**

| 短边 | 半径 | 用在哪 |
|---|---|---|
| **≥ 200** | **r12** | 海报墙/信息墙 244、搜索&横排卡 214、封面 420/378、Shift 334、详情页&横排大图 452、宽列表 438×366 / 340² / 438×246、列表预览 224×300、OSD 播放列表 356×200、插件信息截图 656×312、**音乐信息封面 452²** / **音乐播放页封面 450²**、**视频管理器海报 400×630**、**播放控制条 250²**、**书签缩略图 330×250**、**播放中 seek 封面 200²** |
| **< 200** | **r9** | 首页横版 320×180、专辑 186²、宽列表缩略图 160²、列表预览 160²/184²、剧集缩略图 336×189、首页类别卡 276×160、演员头像 110×150、**列表行小缩略图 110²**、**用户配置头像 162²**、**图标墙缩略图 160×116** |
| 特例 | r9 | **宽列表 240²**：和同视图的 160² 保持同一个圆角，不按短边升到 r12（同一个列表里两种半径更难看） |

绝对半径统一（都 r12）会让小卡明显变圆，纯比例（短边 5%）又让大卡显得过圆 ——
两档制是折中：小卡观感不动，大卡统一到 r12。

**为什么不是 +3**：环外扩 3px 时，环内缘正好落在海报边界上，读起来是"浮在卡片外的一圈框"
（用户原话：比海报大了一点点）；而且遮罩的 3px 羽化让海报最外 1.5px 半透明，
两者之间必然露出一条暗缝。改成外扩 1px、内缘压进 2px，缝和"框感"一起消失。

**别再给环加 `<bordersize>`**：`GUIControlFactory.cpp:1493` —— 有 `<bordersize>` 或
`<bordertexture>` 时控件实例化成 `CGUIBorderedImage`（九宫格），而描边环必须 1:1 整图。
`View_54_InfoWall.xml` 里原本 7 个环控件都带着 `bordersize=20/14`，已清掉。

#### 5.4.2 已经被淘汰的弯路：实色角部遮盖（**已全部清除**）

`media/shapes/corner_<w>x<h>_r<半径>.png`（圆角内透明、四角填 `#2A2A2E` @ 78%）
是 2026-10-27 的做法，**只在纯色/深色背景下勉强成立**：
遮盖色必须和背后的像素一致，而背后是变化的 fanart，于是亮背景上会露出四块深色斑点，
远看轮廓还是方的。

2026-10-28 全部 7 处视图迁移到 5.4.1 的 diffuse 遮罩后，`corner_*.png` 一张不剩，
`gen_corner_masks.py` 的 `MASKS` 表已清空（函数保留，只是不再有实色遮盖产物）。
**新视图一律只写 `DIFFUSE_MASKS`。**

### 5.5 七个反复踩过的坑

1. **`<include condition="X">` 是加载时求值的** —— 按运行时状态切外观只能用
   `<visible>` 或 `$VAR`。曾导致"播放中打开的对话框永远不跟设置"。
2. **panel 不裁剪子控件** —— 想让行尾不露半张卡，必须让"下一张起点 ≥ 1920"。
3. **批量替换先数命中次数** —— 短串（`<left>0</left>`、`start="100" end="112"`）
   往往命中多处，误伤过 PVR 面板和电影 widget 的缩放。
4. **条件里不能嵌套 `$VAR` / `$INFO`** —— `String.IsEmpty($VAR[x])`、
   `System.HasAddon($INFO[y])` 这类写法会让 Kodi 的布尔表达式解析器直接报
   `Misplaced [` + `Error parsing boolean expression ...`，**整条条件失效**，
   控件该显示时不显示（2026-10-29 在音乐页背景兜底上踩过：控件永远不出现，页面纯黑）。
   正确做法：用独立的布尔参数（`<param name="xxx_visible">true</param>` +
   `<visible>$PARAM[xxx_visible]</visible>`），或用 `<visible>` 分开写多条。
   **排查时先 `grep "Misplaced\|Error parsing boolean" kodi.log`** —— 一眼就能看到。
   **补充（2026-10-31）**：`<expression>` 内部同样不能出现 `$EXP[...]` / `$VAR[...]` ——
   Kodi 的 `InfoExpression::Parse` 把 `[` / `]` 当分组运算符，`$EXP[...]` 会被拆成
   未注册的 operand，整条表达式判 `false`（源码见 `InfoExpression.cpp` 与
   `GUIInfoManager.cpp` 的 `Register`）。表达式之间**不能互引**，只能由 `<visible>`
   直接引用表达式。
5. **对话框只有玻璃一套，别再找"旧面"** —— 历史上曾有第二条不透明旧面
   （`NaraDialogLegacy*`），由 `nara_dialog_glass` 表达式切换。它被废弃有两个原因：
   ① `<include condition="X">` 是**加载时**求值的，窗口在播放中被加载过一次就永久钉死；
   ② 旧面 100% 不透明，完全不跟「界面透明度」走。
   **2026-10-29 已整体清理完毕**：40 处死分支、65 处恒真条件、6 个 `NaraDialogLegacy*`
   定义、1 张孤儿贴图（`dialogs/dialog-bg.png`）全部删除，表达式本身也删了。
   现在改对话框**只有一个分支可改**；若在别处看到 `!$EXP[nara_dialog_glass]` 之类的写法，
   那是历史遗留的注释，不是活代码。
6. **设置类列表的高度必须是「整行」的整数倍**（2026-11-13）——
   Kodi 的 `grouplist` / `fixedlist` 对超出容器的行是**硬切断**（裁一半，不是隐藏），
   底部会露出半截中文。判据：`(height + gap) % (row + gap) == 0`。
   旧约定「设置页内容矩形一律 644」是万恶之源——644 无法被任何整数行高整除
   （76+2 时 = 78×8.25），必然切半截。现在位置仍是 525/193/1315，**高度各页自算**：
   设置分类页 622、用户配置页 622、事件日志 608、OSD 设置 700、插件设置 590。
   **`image id="11"`（组间分隔模板）必须删掉**：Kodi 会在每个分组之间克隆它、
   渲染成一整行空白，设 76 组间多一行、设 22 断点漂移 6px、设 0 仍占 itemgap。
   `label id="14"`（分组标题）高度也必须等于行高。
   详见 `skin-contracts.md` §5.0，回归测试 `test_skin_settings.py::_assert_whole_rows`。
7. **系统键盘只能靠 `OnAction` 弹，`SendClick` 是死路**（2026-11-13）——
   想让隐藏 edit（16999）弹出 `DialogKeyboard.xml`，写 `<onclick>SendClick(16999)</onclick>`
   **完全没反应**：它发的是 `GUI_MSG_CLICKED`，而 `CGUIButtonControl::OnMessage` 只处理
   LABEL 类消息，不会转成 `OnClick()`（Kodi 22 源码 `GUIButtonControl.cpp`）。
   能走通的只有 `OnAction`：`SetFocus(16999)` → `Action(Select)` → `CGUIButtonControl::OnAction`
   → `OnClick()` → `CGUIKeyboardFactory::ShowAndGetInput()`；后面再补一条 `SetFocus(16992)`
   兜底，键盘没弹时焦点不会卡在隐藏 edit 上。
   **键盘标题固定是「输入数值」**：`CGUIEditControl` 把 `m_inputHeading` 初始化成内置串
   16028（"Enter value"），`GUIControlFactory` 只解析 `password`，皮肤 XML 没有
   `heading` / `inputtype` 标签可改。
   三条手机输入的实机行为（Kodi 22.0-RC2）：`Input.SendText` 是**追加**不是替换；
   `done=true` 不保证关闭对话框；容器刷新有 **4–7 秒延迟**，验收别只看 2 秒。


### 5.6 排查顺序

某窗口不跟设置走时：① grep 写死的 `AARRGGBB` 板 → ② grep `<include condition=`
→ ③ 最后才查 `$VAR` / `$PARAM`。
"面板/底色不对"先把它刷成荧光色，一眼看它到底在不在 —— 比连改三轮快得多。

---

### 5.7 评分：按类型读，别自己造标签

**三个设置项各管一段，别混用**：

| 设置 | 行 id | 存什么 | 管什么 | 默认 |
|---|---|---|---|---|
| 主评分来源 | `707` | `rating_src_tmdb` / `rating_src_imdb` / `douban_rating` / `rating_src_auto` | 第一颗胶囊读哪个 `Rating(type)`；豆瓣档读本地 `Rating(douban)`，为空时退回 `ListItem.Rating` | TMDb |
| 详情页显示豆瓣 | `715` | `hide_sec_douban`（反向开关） | 详情页第二颗豆瓣胶囊：开（默认）/ 关；主评分已选豆瓣时不重复 | 开 |
| 详情页联网取豆瓣 | `720` | helper setting `douban_enabled`（`toggle_setting` 写），皮肤读 `Window(home).Property(Mistuary.Helper.DoubanEnabled)` | 是否允许 helper 在详情页联网取豆瓣；715 选烂番茄/关闭或主评分选豆瓣时整行隐藏 | 开 |

四条边界：

1. **主评分的豆瓣档不联网**：只读库里的 `Rating(douban)`（StrmAssistant 写入的
   `ProviderIds.DoubanRating`）；读不到退回 `ListItem.Rating`，图标仍是豆瓣。
2. **次评分只剩豆瓣**：只在详情页显示（`Window.IsVisible(12003)`），库里没有时由 helper 联网补；
   列表 / 首页不触发联网。
3. **720 关掉不等于隐藏豆瓣分**：它只停 helper 请求，库里已有的 `Rating(douban)` 照常显示；
   主评分已选豆瓣时第二颗隐藏。
4. **715 是开关**：默认开；关闭后只显示主评分一颗。烂番茄不再作为次评分显示。

Kodi 20+ 的视频信息标签支持**多个带类型的评分**：

| 写法 | 含义 |
|---|---|
| `ListItem.Rating` | 默认类型（`m_strDefaultRating`） |
| `ListItem.Rating(imdb)` / `(tmdb)` / `(tomatometerallcritics)` | 指定类型的评分 |
| `ListItem.Votes(<type>)` / `ListItem.RatingAndVotes(<type>)` | 同类型的票数 |

`CVideoInfoTag::SetRating` 会**丢弃 0 和 >10 的值**，所以 0-100 的分数必须先换算。

**可用的评分类型**（2026-11-05 按 E4K fork 与官方版源码核对）：

| 数据源 | 类型名 | 来源字段 | 覆盖 |
|---|---|---|---|
| E4K fork | 主评分类型（`tmdb` / `imdb` / `trakt` / `douban`，或 `default`） | `CommunityRating` | 电影 / 剧集 / 单集 / 音乐视频 / video |
| E4K fork | `tomatometerallcritics` | `CriticRating / 10` | 同上，有影评人分时 |
| E4K fork | `douban` | `ProviderIds.DoubanRating` | 同上，由 StrmAssistantPlus 写入 |
| 官方 E4K | `default` | `CommunityRating` | 电影 / 剧集 / 单集 / 音乐视频 / video |
| 官方 E4K | `tomatometerallcritics` | `CriticRating / 10` | 电影 |
| Kodi TMDb 刮削器 | `themoviedb` / `tmdb` / `imdb` / `trakt` | 刮削器 | 本地库 |

E4K 不写票数，`ListItem.Votes(...)` 恒空；个人评分不进 `Ratings`，只走 `ListItem.UserRating`。

**评分行的规则**（2026-11-05）：

- **主评分四档互斥、手选优先**（设置 707）：TMDb / IMDb / 豆瓣 / 自动。
  手选时读对应类型，读不到才退回 `ListItem.Rating`（官方 E4K 只有 `default`）；
  TMDb 档同时兼容本地电影的 `themoviedb`。自动档比对
  `Rating(tmdb/themoviedb/trakt/imdb/douban)`，全部不匹配用中性图标。
  条目没有 `DoubanRating` 时，E4K fork 把社区评分写回 `default`，不会标成豆瓣。
- **次评分只剩豆瓣**（设置 715，开关，默认开）：
  详情页优先读 `Rating(douban)`（库里有就用）；读不到时**仅在详情页**
  回退 `script.mistuary.helper`（先问 Emby `/Douban/RatingsByImdb`，失败再走豆瓣公开接口，
  写 `Window.Property(Mistuary.Rating.*)`）。关闭或主评分已选豆瓣时整颗隐藏。
- **烂番茄不再显示**：数据仍由 E4K 写入库（Emby `CriticRating/10`），皮肤不再消费。

> **Kodi 22 评分读取限制（2026-11-13 实测 22.0-RC12）**：库列表 / 卡片里的 ListItem
> 只带**默认评分**；非默认类型（`Rating(douban)`、`Rating(imdb)` 等）在列表 / 卡片上
> 恒为空。详情页（视频信息窗口）同样只带默认评分，非默认类型只有它是默认评分时才可读。
> 因此墙上、信息墙、列表不能显示第二颗评分，视频卡片评分继续读 `ListItem.Rating`；
> 详情页的豆瓣第二颗实际来自皮肤助手的窗口属性（联网），不是库里的类型评分。
> 上游从 v23 起才在库列表 / 小组件填充类型评分（`GUIInfoManager.cpp` 的 skinning_v23 更新）。

取不到的类型返回空字符串，所以"多列几种类型 + 用 `!String.IsEmpty` 控制可见"是安全的写法。
**不要自己发明标签名**（`ListItem.NaraRating(x)` 这类是魔改内核的，官方 Kodi 恒空）。

**TMDbHelper 的豆瓣分进不来**：它写在 list item 的 infoproperties（`douban_rating`），
且要 URL 带 `?ratings=true` 才查，只存在于 TMDbHelper 自己生成的列表里。
皮肤不依赖 TMDbHelper；豆瓣统一走 `Rating(douban)`，详情页读不到时才由
`script.mistuary.helper` 联网兜底（实现细节见插件仓库 `docs/contract.md`）。

### 5.8 音乐播放页：歌词 / 评分 / 背景

- **歌词**：进入播放页时自动启动歌词插件（默认 `script.cu.lrclyrics`），
  OSD 里**没有**歌词按钮（那个位置让给了黑胶模式）。
  皮肤用 `xml/script-cu-lrclyrics-main.xml` 覆盖插件窗口，列表固定在屏幕右侧、
  无全屏遮罩；关闭由插件自己处理（皮肤不再发 `Dialog.Close`）。
  插件的取词顺序是「内嵌 → 同名 .lrc → 在线源」，本地有词就不会联网。
- **控制条**：主控制条 include 在 `xml/script-cu-lrclyrics-main.xml` 里，和歌词列表
  同窗口；`MusicOSD` 只作为没有歌词时的兜底（播放页 `onload` 会先打开它，
  这样 CU LRC 的 `ACTION_OSD` 不会重复再开一个）。
  歌词列表：↑/↓ 仍归 CU LRC 选行/同步，←/→ 聚焦同一窗口的 OSD 播放键。
  OSD 按钮行：←/→ 切按钮，↑ 进度条，↓ 回歌词列表。
  进度条：↑/↓ 回按钮行，←/→ seek；焦点控件是 `slider id=87`。
  `NaraMusicPlayerControls` 通过 `ondown` 参数决定按钮 ↓ 去 87 还是去歌词列表
  （MusicOSD 默认 87，歌词窗口传 110）。**不要改回 `lyrics_id` + 数字条件**：
  Kodi 会把 `0/110` 当 info 标签，条件不可靠。
  **不要把 `NaraMusicPlayerControls` 塞回播放页**：Kodi 的 `<Visualisation>` 键位把
  ←→ 映射成快退/快进、↑↓ 映射成上一曲/下一曲，放在 visualisation 里的按钮永远
  收不到方向键导航。也不要用 timer 把 OSD 顶在歌词窗口上面——会把歌词上下键锁死。
- **评分**：OSD 有「我的评分」按钮（`SetRating`，写 Kodi 用户评分）。
- **背景**：默认图是 `media/osd/nara/music-background.jpg`（进 XBT）；
  用户可在「设置 → 外观 → 音乐背景」换图，变量
  `NaraImgSkinStringNaraMusicBackgroundDefMusicBackground` 给播放页和音乐库背景兜底。
  音乐信息页（2026-10-29 重做）在**没有 fanart** 时也用它兜底；有 fanart 时优先 fanart，
  `primary.jpg` 原色常驻最底层。
- **豆瓣**：StrmAssistant 的豆瓣覆盖改写的是 Emby `CommunityRating`（Kodi 侧为默认类型，
  无来源标志），皮肤用设置项 `douban_rating` 手动切换第一颗评分胶囊的图标（IMDb / Douban）。

#### 5.8.1 音乐信息页（2026-10-29 重做）

`DialogMusicInfo` 不再走旧的「左封面 + 中间面板 + 右侧元数据列表」，按电影详情页骨架：

- **全幅背景**：`primary.jpg`（原色，`primary_background_info`）+ 无 fanart 时音乐背景图
  + fanart；左侧 `detail-left-scrim.png`，没有玻璃大卡
- **左列** `x=209 / y=303`：标题、艺人/专辑、年份/类型/时长、评分 + 音频规格；
  只显示有值的字段，不铺空行
- **右列** `452×452 @ (1259,303)`：圆角 `mask_452x452_r12`，下方说明居中
- **底部动作条** `x=209 / y=681`：播放白色主按钮 + 我的评分 / 选择艺术图片 / 专辑信息
- **内置动作**：Kodi 的 `7/8/10/12` 用 `HiddenObject` 隐藏，可见按钮用
  `70080–70083` + `SendClick()` 转发；直接给可见按钮用内置 ID 会把 Kodi 的
  文字标签压进 70×70 圆里
- **简介**：只在 `Comment` / `Album_Description` / `Artist_Description` 有内容时出现；
  `EmbyLibraryId-...` 技术注释自动隐藏
- **已删**：`Includes_MusicInfo.xml`、`VideoInfoButtonsCommon`、`MusicInfoTextboxVar`、
  `mask_570x570_r12`、`mask_190x190_r9`；新增 `mask_452x452_r12`

#### 5.8.2 详情页背景兜底

| 页面 | 兜底 |
|---|---|
| `DialogVideoInfo` | `primary.jpg` 原色（`no_fanart`）/ `primary_dim` ×0.60（缺 fanart）+ fanart + 左侧压暗 |
| `DialogMusicInfo` | 同上；无 fanart 时先用音乐背景图（`NaraFanartDimVar`），再退到 primary |
| `DialogAddonInfo` | **共享真剧照** + 插件自己的 fanart，两处都走 `NaraFanartDimVar`；有 fanart 用页面档遮罩，无 fanart 固定 `sc_2`（27%） |
| `DialogPVRInfo` / `DialogPictureInfo` | **故意透出直播画面 / 当前图片**，不铺不透明底图 |

> 插件详情 2026-11-05 起不再用 `primary.jpg` 兜底：底层换成与设置页 / 文件管理同一张
> 共享随机剧照（§5.11.1），插件自己有 fanart 时仍显示插件那张。

> `primary_background`（`FF404040`）会把 `primary.jpg` 乘到 25% 亮度，详情页不要再用它；
> 详情页统一用 `primary_background_info`（`FFFFFFFF`）。PVR / 图片详情不在此列。

### 5.9 海报墙的列宽预算（2026-10-30 更新）

海报墙（`View_500_Wall` / `View_54_InfoWall`）的卡片格 = 海报 + 左右空档：

| | 值 | 说明 |
|---|---|---|
| 海报 | **236×340** | 2026-10-30 从 244×352 等比缩小（0.9672），给间距让出 8px |
| 卡片格 | **260** | 空档 = 260 − 236 = **24px**（原 16） |
| 行高 | **418** | 海报矮 12，行高跟着减（原 430） |
| 左右边距 | **62 / 62** | 7×260 = 1820，容器 left 50，海报左 62 右 1858 |

**卡片格 260 是实测上限，不能超**：曾经调 264（缝 20）在真机电视上掉成 6 列
（面板 `width=98%` 且整体右移 50，实际可用宽度不足 1848）。**要加宽间距只能缩海报**——
海报缩多少，缝就宽多少。

**焦点环必须跟着海报变**：环 = 卡片 +2（`ring_card_238x342_r13`）、环外半径 = 遮罩半径 +1、
圆心与海报圆角同心（12−1+13 = 12+12 = 24）。遮罩 `mask_236x340_r12` 尺寸必须和控件完全一致。

**4K 不用单独考虑**：`addon.xml` 声明了 8 组 `<res>`，但全部 `folder="xml"`（同一套 XML）。
Kodi 按当前宽高比选一组逻辑坐标渲染，4K 16:9 走的就是 1920×1080 那组、放大 2 倍输出。

**改海报尺寸的连带清单**（漏一个就错位）：

1. `tools/gen_corner_masks.py` 加遮罩条目、`tools/gen_rings.py` 加环条目，跑生成器
2. `InfoWallMovieLayout` + `InfoWallFavouriteLayout` **两套都要改**（注释写着"和 MovieLayout 对齐"）
3. 状态图标 `top`、已看标记、进度条、caption `top` 全要跟着海报高度减
4. `View_500_Wall` 和 `View_54_InfoWall` 的 `itemlayout height` 共 6 处
5. **`Custom_1111_MovieSetDialog` 不用动**——它用独立的 240×360 + `ring_card_238x346_r12`，
   和海报墙无关（早期文档说"必须重算补偿数"是误判，2026-10-30 核对过）

### 5.9.1 卡片信息区布局（2026-10-30 定稿）

海报上的三个信息块，边距全部 12px、垂直中心统一 315：

| 元素 | 位置 | 说明 |
|---|---|---|
| 评分圈 | **右上角** left 188, top 12 | 40×40 描边圈（2px 白环 + 50% 黑底），数字 `font20_title` |
| 状态图标 | **左下角** left 24, top 301 | 28×28，离海报左边 12px |
| 类型/花絮图标 | 状态图标右侧 58 / 92 | 有则显示，不做占位 |
| 集数 `已看/总数` | **右下角** left 96 宽 140 右对齐 | 右边缘 236，离海报右边 12px |

**状态图标着色**（`StatusIconColorVar`）：已看完 → `status_done`（`FF03B585`，和 `progress_watched`
同色），其余 → `badge_foreground`（白）。判断条件必须和 `ItemStatusIconVar` 第一条严格一致，
否则会出现"图标是已看完、颜色不是绿"的错位。**故意不给「继续看」上黄色**：`status_warning`
已是黄，两黄会混。`$VAR` 在 `colordiffuse` 里生效，实机验证过。

**图标素材统一**：全部 32×32 源图、24~28px 渲染。`played-total` 用**实心眼睛**（用户偏好，
2026-10-30 从线条版改回）；`lists/played-total.png` 被 `ItemStatusIconVar` 和 `DialogPVRInfo`
两处引用，改它两处同时变。

### 5.10 搜索（首页「搜索」页签）

- **接口**：不是 Kodi 原生 `Search`，也不是 JSON-RPC。皮肤把输入拼进视频库路径
  `videodb://movies/titles/?xsp={...}` / `videodb://tvshows/titles/?xsp={...}`，
  由 Kodi 视频库按 XSP 规则执行。输入来自隐藏 edit `16999`。
- **规则**（`Includes_Search.xml`）：三字段 `or` —— `title` / `originaltitle`
  （`contains`）、`sorttitle`（**`startswith`**）。`sorttitle` 是神医助手生成的拼音首字母，
  由 Emby for Kodi 同步写入（本机 742 部电影、512 部剧集都有），所以 A-Z 键盘只打
  首字母也能搜到中文片名。换元数据源后要确认这项还在；没有拼音排序时拼音搜索会失效，
  中文标题和原名搜索不受影响。
- **不要再加回 `actor` / `director` / `genre`**：一个 flat `or` 只能共用一个 operator，
  子串匹配会把演员名当命中（实测单字母 `Z` 命中 238/742 部、`S` 命中 371/742）。
  本地搜索仍不支持人员/类型；服务端桥 0.3.3 起支持中文演员名与类型，
  2026-11-13 起英文 ≥5 位连写（`NOLAN` / `ACTION`）或含空格人名（`Tom Hanks`）也并入；
  **2–4 位 ASCII 连写仍按拼音首字母，不扩展**。
- **首字母必须前缀匹配**：`contains` 会把首字母出现在词中的条目捞进来
  （`HZ` 命中 14 部 → 前缀只剩 4 部）。2026-10-28 已改 `startswith`。
- **不要给结果列表加 `limit`**：`<content limit="30">` 会同时截断结果和标签计数。
  2026-10-28 已移除。
- **覆盖不到**：分集（Kodi 22 没有全局 `videodb://episodes/` 节点，皮肤层拿不到）、
  合集（22 个，可用 `videodb://movies/sets/` 单独做页签）、Emby 索引里尚未同步到
  Kodi 库的条目（当时差 6 部电影 / 131 集）。

### 5.9.2 评分圈按来源着色（已实施，2026-10-31）

实现方式：`RatingCircle` 的环 `overlays/badge_ring.png` 加
`colordiffuse="$VAR[NaraRatingRingColorVar]"`。手选档位优先；自动档比对
`ListItem.Rating` 与 `Rating(tmdb/themoviedb/trakt/imdb/douban)`：豆瓣绿
`FF2BB24C` / IMDb 黄 `FFF5C518` / TMDb 蓝 `FF01B4E4`，判不出来白色。
数字仍用 `badge_foreground`，因为 `$VAR` 在 `<textcolor>` 里不生效。

用户要求：为多评分源预留颜色区分（豆瓣绿 / IMDb 黄 / TMDb 蓝 / 烂番茄红）。

**已验证的技术事实**：

1. **`ListItem.RatingSource` 是空的** —— 皮肤层拿不到"当前 default 是哪个源"，必须自己判断。
2. **`ListItem.Rating(<source>)` 语法可用**（实测 `Rating(imdb)` 返回 7.5），
   且 `RatingMap` 是 `std::map<std::string, CRating>` —— 任意字符串都能当源名。

**实施步骤**：

```xml
<!-- 1. 颜色 token（colors/defaults.xml） -->
<color name="rating_douban">FF00B51D</color>
<color name="rating_imdb">FFF5C518</color>
<color name="rating_tmdb">FF01B4E4</color>
<color name="rating_rotten">FFFA320A</color>

<!-- 2. 值和颜色用同一串条件（Variables.xml）—— 保证永不错位 -->
<variable name="RatingValueVar">
    <value condition="!String.IsEmpty(ListItem.Rating(douban))">$INFO[ListItem.Rating(douban)]</value>
    <value condition="!String.IsEmpty(ListItem.Rating(tmdb))">$INFO[ListItem.Rating(tmdb)]</value>
    <value condition="!String.IsEmpty(ListItem.Rating(themoviedb))">$INFO[ListItem.Rating(themoviedb)]</value>
    <value>$INFO[ListItem.Rating]</value>
</variable>
<variable name="RatingColorVar">
    <value condition="!String.IsEmpty(ListItem.Rating(douban))">rating_douban</value>
    <value condition="!String.IsEmpty(ListItem.Rating(tmdb))">rating_tmdb</value>
    <value condition="!String.IsEmpty(ListItem.Rating(themoviedb))">rating_tmdb</value>
    <value>rating_imdb</value>
</variable>
```

**贴图要拆两张**（`colordiffuse` 是整体相乘，会把黑底也染色）：

| 文件 | 内容 | 着色 |
|---|---|---|
| `badge_disc.png`（新） | 纯黑圆，50% 透明 | ❌ |
| `badge_ring.png`（改） | 只有白环，内部透明 | ✅ `colordiffuse="$VAR[RatingColorVar]"` |

**控件三层**：黑底 → 彩色环 → 数字（白色）。

> ⚠️ **`$VAR` 在 `<textcolor>` 里不生效**（整段变透明），这是踩过的坑。
> 所以**数字不能跟着变色**，只能靠环区分来源。

> **Kodi 22 评分读取限制（2026-11-13 实测 22.0-RC12）**：卡片上的自动档按值比对
> 只能识别默认类型；`Rating(douban)` / `Rating(imdb)` 等非默认类型在列表 / 卡片上恒空，
> 非默认来源只能靠手选档位着色。详情页也只带默认评分；豆瓣第二颗靠助手联网窗口属性。

**烂番茄的定位**（2026-11-13 更新）：不再作为次评分显示；数据仍入库但不消费。
主评分四档见 §5.7。

### 5.11 背景遮罩：首页统一加阅读区（2026-11-06 定）

- **首页所有非搜索分区一律叠烘焙阅读遮罩**，不再区分「真剧照 / `primary.jpg` 兜底 / 音乐背景」；
  电视（livetv）与音乐分区以前没有遮罩，看起来比电影/电视剧亮一档，现在统一
- **搜索分区不叠这一组**：`NaraSearchBackground` 自带完整的遮罩栈，重复叠会二次压暗
- 文件 / 收藏用 `list` 变体，其余分区用 `hero` 变体；`no_fanart` 打开时两张都不显示
- 旧的三条 `Sub*` 判据（`NaraHomeFanartSubItems` / `SubHero` / `SubOther`）已删除：
  统一后不再需要判断「背景是不是真图」，也就不存在「判据与变量分支漂移」这类问题
- `tools/check_home_fanart_mask.py --check` 现在守三条：
  遮罩组排除 `search`、不排除 `music`；两张遮罩都受 `no_fanart` 控制

#### 5.11.1 半透明剧照：乘法压暗，不再垫中性底（2026-11-05 定稿）

`primary.jpg` 的平均色约 `63,77,110`（偏蓝紫）。设置页 / 文件管理 / 搜索空查询 /
首页「文件·收藏」的剧照曾经是半透明叠在它上面，于是被染成紫灰。

**现行做法**（2026-11-10 第二批）：剧照底层跟随「背景压暗」四档，
系数集中在 `colors/defaults.xml`，**不要再写死十六进制**：

| token | 值 | 用在哪 |
|---|---|---|
| `fanart_dim_35` | `FF595959`（×0.35） | `NaraFanartDimVar` 极透档 |
| `fanart_dim_50` | `FF808080`（×0.50） | `NaraFanartDimVar` 通透档 / 默认 |
| `fanart_dim_60` | `FF999999`（×0.60） | `NaraFanartDimVar` 平衡档 |
| `fanart_dim_100` | `FFFFFFFF`（×1.00） | `NaraFanartDimVar` 原浓度 |
| `primary_dim` | `FF999999`（×0.60） | 缺 fanart 时的 `primary.jpg` 兜底层（View_51 / View_501 / DialogVideoInfo）；`no_fanart` 仍画原图 |

实际扫到 **14 个 XML、16 处** `fanart_dim` / `fanart_dim_reading`，全部改成
`$VAR[NaraFanartDimVar]`；阅读遮罩仍用 `$VAR[NaraFanartVeilVar]`，两个变量共用
`fanart_veil_*` 设置。`primary_dim` 的 3 处是缺 fanart 兜底，不在本批。全部保持不透明（alpha `FF`）。

**全皮肤亮度阶梯**（2026-11-07 定）：

| 位置 | 目标 |
|---|---|
| 媒体库内容页 / View_50（已有 40% 页遮罩） | 0.24–0.30 |
| 八共享页 / View_51 海报墙 / MovieSet / 音乐信息兜底 | 0.40–0.50 |
| 首页（真图 / primary 兜底 / 音乐，统一 hero 遮罩） | 0.44 |
| 视频详情 / 音乐信息（stage mask + 左 scrim + 底部渐变） | 0.45–0.50 |
| primary 兜底（缺 fanart） | 0.60 |
| 音乐播放 / PVR / 图片信息 / 视频播放 | 原图 |

| 做法 | 合成亮度（剧照亮度 L） | 玻璃面板后面 |
|---|---|---|
| 55% + 20% 黑 + 10% 黑（设置页初版） | `0.495L + 24.9` | 灰雾，没层次 |
| 50% 叠在 `#313131` 上（第二轮） | `0.5L + 24.5` | 同上 |
| ×0.50 / ×0.66 不透明（第二批前） | `0.50L` / `0.66L` | 照片的明暗和色彩都在；无遮罩页 0.50，带烘焙遮罩页 0.66 |
| **四档底层 + 同档遮罩（现行）** | `0.35L` ~ `1.00L` | 底层和遮罩共用 `fanart_veil_*`；默认 0.50 / 0.50 |

三者在 L=150 时都约 99，亮度等价；但乘法压暗**不需要中性底那一层**，
玻璃背后有真实的明暗过渡。**别再用纯色兜底图当背景** —— 面板会糊在背景上，玻璃感直接没了。

**四条约束**（`tools/test_nara_neutral_fanart.py` 锁着）：

1. 14 个 XML 的 16 处 fanart 底层统一用 `$VAR[NaraFanartDimVar]`，遮罩用 `$VAR[NaraFanartVeilVar]`；
   两处共用 `fanart_veil_*` 四档，不要按页写死 0.50/0.66；
2. 必须**不透明**（alpha `FF`），否则 primary 的蓝紫会透上来；
3. 系数必须是**中性**（R=G=B），带色偏等于换个方向染色；
4. 不要再引入中性底 / 半透明叠灰这类额外图层。

⚠️ **`colordiffuse` 是 `AARRGGBB`，不是 `RRGGBBAA`**。写成 `A8A8A8FF` 会被解释成
「alpha `A8`（66% 半透明）+ 颜色 `(168,168,255)`」——蓝通道满值、红绿压掉，
照片立刻发紫，而且半透明会把 primary 的蓝紫透上来。2026-11-05 踩过一次。

| 页面 | 显隐表达式 | 定义在 |
|---|---|---|
| 设置页、文件管理器 | `nara_page_shared_fanart_visible` | `Includes.xml` |
| 搜索（空查询随机剧照） | `nara_search_empty_fanart_visible` | `Includes.xml` |
| 首页「文件 / 收藏」 | `nara_home_files_fanart_visible` | `Includes_Home.xml` |

**首页「文件 / 收藏」还有一条动画**：收藏详情弹窗打开时剧照要淡出
（`condition="…favorites + Window.IsActive(movieinformation)"`），否则弹窗后面会剩一块图。

**音乐分区也吃阅读区**（2026-11-06 统一）：音乐背景图本身亮度约 73，以前为省 4 层不叠遮罩，
结果比电影/电视剧亮一档；现在和其它分区一样叠 `hero` 变体，保证整个首页亮度一致。

**阅读区是一张烘焙图**：遮罩 + 顶部渐变 + 底部渐变 + 左侧 scrim 合成一张 720p overlay，
由 `tools/gen_fanart_overlay.py` 生成（`--check` 进 CI）。改那四层的几何或透明度后必须重跑，
否则画面和生成器不一致。三个变体：`hero`（电影/电视剧/音乐/电视/兜底）、`list`（首页文件/收藏）、
`empty`（搜索空查询）。烘焙后这些页面各少画 3 层。

**还有哪些剧照层**：`grep -o 'colordiffuse="\$VAR\[NaraFanartDimVar\]"' xml/*.xml` 应能看到 16 个使用点。
搜索结果剧照是不透明的，不参与这套。加新的半透明剧照页时先判断它属于哪一类（有无阅读遮罩）。

#### 5.11.2 首页与详情页背景构图：150% 左 25% 锚点（2026-11-07 定）

**目的**：让剧照里的人物整体右移、略微下移，给左侧文字让出空间。

| 位置 | 实现 |
|---|---|
| `Home.xml` 背景 | 全屏 `multiimage`（`$VAR[HomeFanartVar]`）外包一层 group，`<animation effect="zoom" center="0,25%" start="100,100" end="150,150" time="1">WindowOpen</animation>` |
| `DialogVideoInfo.xml` fanart | 同样的 group + 同一条 zoom；fanart 控件必须 `FullScreenDimensions` |

**150% 的实际效果**：人物约放大 50%，在屏幕上右移约 25% 屏宽、下移约 12.5% 屏高；
右侧裁掉约 33%，上下各裁约 8%。左侧空档由阅读区 scrim 盖住。

**为什么不是 AF3 的写法**：AF3 的 `Background_FlixArt` 基准是 1280×720（Large 1440×810、ExtraLarge 1600×900），
Home 上 zoom 到 150%（133% / 120%），乘完正好 1920×1080，**稳态等于全屏、没有裁切**；
它的人物大小来自剧照本身。我们这里是**持续放大 + 左中偏上锚点**，是刻意偏离，目的是固定构图。

**两条不能破坏的约束**：

1. 详情页 fanart 不能再加 `-120/-80` 外扩或内部 `zoom 100→104`。
   两者叠加会让实际放大到约 169%，垂直锚点也变，表现就是「详情页比首页更近、更靠上」。
2. 两个窗口的 `center` 与 `end` 必须保持一致；改一处就要同步另一处，否则两边构图会分叉。

`zoom` 的 `end` 不支持 `$VAR`，所以目前不做「居中 / 偏右」运行时开关：
要做只能复制整组背景并用 `Skin.HasSetting()` 互斥显隐，层数和维护成本都会上去。

### 5.12 播放/暂停图标：音乐与视频共用一套（2026-10-31 定）

- 视频 OSD（`NaraVideoOSDPlayButton`）和音乐 OSD（`NaraMusicOSDButtonPrimary`）
  都引用 `osd/nara/play.png` / `pause.png`（画布 64×64），不是两套图标
- 视频：按钮 52×52、图标 50×50、`text_primary`、无底板（聚焦才出 `button-fo.png`）
- 音乐：按钮 61×61、图标 50×50、`text_primary`；主键**不再加 56×56 白色实心圆底**，
  聚焦用 `glass_focus_medium`
- 对照图见 `docs/playpause-compare.png`

### 5.13 OK 弹窗：DialogConfirm 是唯一底版

- Kodi 的 `CGUIDialogOK` 固定加载 `DialogConfirm.xml`（源码 `GUIDialogOK.cpp`），
  改它 = 改所有 OK 提示框（“游戏运行失败”“操作失败”等）
- 内边距：标题与正文都 left **48**；正文 top **92**、width **837**、height **155**
  （底边仍是 247，不挤进度条）；进度条同步 left 48 / width 837
- 右上角 vendor 图标 **32×32 @ right 60 / top 36**（2026-11-05 从 48px @ 10/11 收进来的，
  原来压在 20px 圆角上）；标题的 `header_left` 传 48，与正文左边缘齐平

### 5.14 评分胶囊尺寸（2026-11-03 定）

- 方形徽标（豆瓣 / TMDb / 烂番茄 / trakt）：胶囊宽 **108** =
  内边距 12 + 图标 28 + 文字左起 46 + 文字框 56 + 右距 6
- IMDb 词标（2:1）：胶囊宽 **126**（图标 46×23、文字左起 64）
- 文字框 **56**：Inter 27px 实测 `8.9` = 42px、`10.0` = 53px。库里真实有
  **821 条 IMDb + 25 条烂番茄** 评分为 10.0（如《东邪西毒：终极版》），
  44px 会裁掉末位 —— 不要再把文字框缩回去
- 分数在 56px 框内**居中**：3 位 / 4 位分数左右留白对称
- 底板 `4D000000`（30%）；视频 OSD 与插件弹窗仍是 `66000000`（40%），不要一起改

### 5.15 文件播放记录（2026-11-04 定稿，随 1.9.0 发布）

**目标**：从文件管理器播放的视频，下次打开能续播。

**两个入口**

| 入口 | Kodi 窗口 | 原生续播 | 本方案 |
|---|---|---|---|
| 设置 → 文件管理器；首页「文件」源卡片（`target=filemanager`） | 10003 `WINDOW_FILES` | 不支持 | helper 弹窗 + 焦点行圆环 |
| 视频 → 文件 | 10025 `WINDOW_VIDEO_NAV` | 支持 | Kodi 原生；helper 不记、不弹窗、不写点 |

**数据一层**

| 层 | 位置 | 写什么 | 频率 |
|---|---|---|---|
| 账本 | `userdata/addon_data/script.mistuary.helper/resume.db`（SQLite WAL） | 只记 10003 里的视频/STRM 进度 | 每 30 秒 + 暂停/拖动/停止/切集 |

- **不写 `MyVideos.db` / Kodi 原生续播点**，也不依赖 `myvideos.resume` 开关；账本没有时只读回退已有原生点，不写回。
- 账本主键：统一斜杠、去尾斜杠、**保留大小写**；另存 `key_fold` 做大小写回退（Windows/SMB）。
- `.strm` 用 `.strm` 文件本身作 key，不用解析后的 http 地址。
- 只收真实路径（`/`、`smb://`、`nfs://`、`.strm`、`.iso`、UNC 等）；排除 `plugin://`、`pvr://`、目录、带库 ID 的条目；`http(s)://` 默认排除，可在 helper 设置里打开。
- 起播 180 秒内不写；剩余 ≤8% 清除；读 `advancedsettings` 的 `ignoresecondsatstart` / `ignorepercentatend`。
- 不依赖 `myvideos.resume`；本版本不写任何 Kodi 原生续播点。
- 保留默认 90 天 / 5000 条，可在 helper 设置里调整；启动时 + 每 6 小时清理；清理媒体库不再触发原生恢复。

**行为**

- **10003 弹窗**：播放开始后打开皮肤自定义窗口 **1115**（`Custom_1115_FileResume.xml`，560×180）：
  无标题、无正文，上下两个 400×44 按钮（间距 16），
  文案「从 01:07 继续播放」/「从头播放」；时间补两位分钟（超过 1 小时仍 `1:23:45`）。
  `<onload>SetFocus(10)</onload>` 保证默认焦点在「继续播放」。
  返回/点空白 = 取消：停止播放并保留记录；从头播放 = 删除该文件记录并 seek 到 0。无 vendor 图标、无圆环预览。
  `FileResumeDialogButton` 里的 `<label>$PARAM[label]</label>` 不能省，否则按钮只剩空底板（2026-11-04 实机）。
  原通用 `DialogSelect`（1220×750）不再用于这里。
  播放开始后 helper 先暂停、再弹窗；选完才 seek / 恢复 / 停止。
  面板用与 OSD 设置相同的 `round20` 实体板（不是 glass20 渐变）；
  遮蔽与档位走 `NaraGlassFloatScrimVar` / `NaraGlassFloatTintVar`（浮窗档，合成 83.5%），
  因为这是必须做选择的模态窗，不是边看边调的 OSD。要与 OSD 完全一致时改用
  `NaraSettingsDialogTintVar` / `NaraSettingsDialogScrimVar`（播放中档 61.5%）。
- **10003 焦点行圆环**：helper 仅在 `Window.IsActive(10003)` 时每 0.1 秒读当前焦点项（只查内存字典），把 `Mistuary.FileResume.HasResume / Percent / PercentKey` 写到 `Window(home)`；皮肤聚焦行读属性。
  - 位置：文件名与修改时间之间，40px。文件名列统一 1000，日期列从 1170 移到 **1213**（宽 160），
    文件名末尾到日期的距离由 85 增到 **128**（+50%）；圆环 left **1129**，正好在 44 / 44 中间。
  - 账本没有记录时回退 Kodi/Emby 的 `Files.GetFileDetails` 续播点（按路径缓存 10 秒），
    与弹窗口径一致；否则只在账本里的文件才显示圆环。
  - 配色：绿弧 `#89C19F` = 已播，白轨 `60FFFFFF` = 全长；百分比数字**烘焙在每帧里**（白色 14px，不带 `%`），与弧长同源，不再用独立 label，因此不会出现贴图在、数字空的情况；**不显示具体时间**。
  - 圆环帧无暗色圆底，中心透明。
  - `PercentKey` 是 `000`–`100` 三位字符串，经 `FileResumeRingVar` 101 条静态映射到 `progress/resume_ring/ring_XXX.png`。
  - 焦点切换瞬间 `ListItem.FolderPath` 会短暂为空：先保留上一次属性，持续空 0.2 秒才清；换行时 helper 先隐藏旧圆环、30ms 后再发新值，缩短上一行进度的残留；只有焦点落到文件夹行、读到非空文件路径后查不到记录、或离开 10003 时才立即清。
  - 只有 `total>0` 的记录才显示圆环：原生续播点只有位置没有总长时按无记录处理，避免退出播放后先闪一个 0%。
  - **不做 ListItem 属性注入**——Kodi 内置文件管理器的控件 Python 拿不到（`Window.getControl(20)` 报 Non-Existent Control），原生 `ListItem.IsResumable` 在 10003 也是 false；所以常显只能走自定义「继续观看」聚合页或插件式列表。
- **带参数的 include 必须用 `<definition>` 包住控件**；否则 `$PARAM[left/top/size]` 解析为空，
  控件尺寸变 0，圆环静默不显示（2026-11-04 实测）。圆环贴图用 `FileResumeRingVar`
  101 条静态映射（`000`–`100`），不再走动态贴图路径。
- **10025**：`View_50_List` 的 3px 进度条 + 「续播 h:mm:ss」仍按 Kodi 原生 `ListItem.IsResumable` 显示；helper 不再为它写原生续播点。
- 库内条目（movie/episode/musicvideo）跳过，Kodi / Emby 已处理。
- 文件夹连播切换条目时不当成新会话，不重复弹窗；**同一个文件在 120 秒内重新打开仍会弹窗**（按路径判断，
  只有路径不同的自动连播才跳过）。

**落点**

- helper（随 0.3.7 发布）：`lib/file_resume.py`、`service.py`、`resources/settings.xml`（`file_resume` 默认开）、`lib/skin_bridge.py`、`lib/i18n.py`、`tests/test_file_resume.py`
- 皮肤（随 1.9.0 发布）：`xml/FileManager.xml`、`xml/Includes_FileResume.xml`、`xml/Includes.xml`、`xml/Custom_1115_FileResume.xml`、`xml/Variables.xml`（`FileResumeRingVar`）、`tools/gen_resume_ring.py`、`media/progress/resume_ring/*.png`（101 帧）

**限制**

| 项 | 说明 |
|---|---|
| 纯 http(s) 直链 | 默认不记录；可在 helper 设置打开；`.strm` 仍记 `.strm` 文件路径 |
| 改名 / 移动 | 记录按完整路径存，改名后等于新文件 |
| 清理媒体库 | 不影响账本；helper 不再从账本恢复 Kodi 原生续播点 |
| 10003 圆环 | 依赖 helper 轮询（0.1 秒），属性最多滞后一个轮询周期；**只在焦点行显示**。Kodi 内置 FileManager 的控件 Python 拿不到，逐行常显需另做「继续观看」聚合页/插件式列表 |
| 原生续播点 | helper 不写；只读回退 Kodi/Emby 已有的续播点 |

**实机验证（2026-11-04，Windows Kodi 22 RC1）**

1. `.strm` 的 `Player.GetItem.file` 返回 `.strm` 本体路径（不是解析后的 URL），`type=unknown`
2. `Window.Previous(filemanager)` 在 10003 起播时为真
3. 再播后弹出 1115 紧凑弹窗（560×180）：两个上下按钮「从 10:00 继续播放」「从头播放」；默认「继续播放」，回车跳到 10:00；返回停止并保留记录
4. 10003 焦点行圆环属性 true / 7 / 007，圆环取 `ring_007.png`；离开窗口清空
5. 额外修复：`Player.GetItem` 的 properties 不能带 `type`/`id`；30 秒采样器必须过 180 秒阈值；
   文件管理器 `ListItem.Path` 是目录，聚焦项完整路径在 `ListItem.FolderPath`

> `Files.GetDirectory` / `Files.GetFileDetails` 只对**已配置媒体源**内的路径生效；
> 本轮只读回退，不再用 `Files.SetFileDetails` 写点；非源路径以 `resume.db` 账本为准。

### 5.16 弹窗表头：4 套规格，标题与正文左对齐（2026-11-05 定）

弹窗的「标题 + 右上 vendor 图标」不是一套代码，有 4 处实现：

| 套 | 用在哪 | 标题 | 右上图标 |
|---|---|---|---|
| `DialogBackgroundCommons` | **16 个窗口**：OK 弹窗、选择列表、媒体源、数字输入、文本查看器、PVR、字幕、视频管理、文件浏览器、播放控制、智能播放列表… | `font28_title`，top 24，`header_left` 逐弹窗传 | **32px @ right 60 / top 36** |
| `NaraSettingsDialogFrame` | 设置类弹窗、OSD 设置 | `font32`，left 42 / top 24 | 无 |
| `NaraStreamDialog*` | 播放中选流 / 选集 | `font13`(27px)，left 40 / top 0 | 无 |
| `DialogAddonInfo` | 插件信息 | 32px，x=168（跟在 128px 图标后面） | 无 |

**`header_left` 参数**：标题左边距按各弹窗**正文的左距**传，不要用统一值 —— 各弹窗正文起点从 10 到 48 不等：

| 弹窗 | 正文 left | `header_left` |
|---|---|---|
| OK 弹窗 / 字幕 / 文本查看器 | 48 | 48（默认） |
| 文件浏览器 | 列表 36 + 图标 20 = **56** | **56**（2026-11-05 用户定：标题对齐行图标列） |
| 选择列表 | 列表 36（行内文字在 56） | **56** |
| 媒体源 / PVR 分组 / 智能播放列表编辑器 | 32 | 32 |
| 数字输入 | 44（输入框左边缘） | 44 |
| 视频管理 / 播放控制 / 智能播放列表规则 / 颜色选择 | 20 | 20 |
| PVR 频道管理 / PVR 搜索 | 10（1800 宽全屏页） | **32**（贴边太难看，故意不严格对齐） |

⚠️ **文件浏览器按「图标列」对齐**：标题 56 与行图标左边缘共线；行文字在图标右侧
（绝对 104），不可能与图标同时压到 56（会盖住图标）。底部路径 / 计数同样从 56 起。
⚠️ **选择列表按「文字列」对齐**：列表 36 + 行内缩进 20 = 56。

⚠️ **改 `DialogBackgroundCommons` 一次影响 16 个窗口**：至少开两个不同尺寸的弹窗验收
（915×400 的 OK 弹窗 + 1220×750 的选择列表）。

**选择列表只有一层底板**：`NaraDialogInsetTexture` 内嵌层 2026-11-05 已删 ——
底板 + 内嵌区两层叠着是「板中板」，去掉后列表行直接铺在底板上。

---

## 6. 发版流程

### 发布顺序：先插件，后皮肤（2026-11-07 定）

皮肤 `addon.xml` 对 `script.mistuary.helper` 是**硬依赖**（§2），所以顺序固定：

1. **先发 Helper**：插件仓库升版本 → push → CI 建 `vX.Y.Z` Release
2. 等 Release 出现，核对 tag 与 zip（`git ls-remote --tags origin` + Release 里能下载）
3. **再发皮肤**：皮肤 `addon.xml` 的 import 版本下限只能 ≤ **已发布**的 Helper 版本

反过来的代价：先发皮肤时，用户升级后若本地 Helper 低于新下限，Kodi 直接判定依赖不满足 →
**皮肤不加载**（不是少个功能，是整屏打不开）。所以皮肤用到 Helper 新能力时，必须同时写
运行时软探测（`System.AddonIsEnabled()` / 版本判断），保证旧 Helper 下能降级显示。

兼容表两头同步维护：Helper 仓库 `docs/release.md` §5，以及本文 §2 与本节。

- **不要擅自升版本号**（2026-10-31 用户明确要求）：一天最多升一次；做完功能/修复也先给
  建议、等确认再升。"递交"只提交代码，不等于发版。插件仓库同理。

1. 改 `addon.xml` 的 `version`（**必须升**，否则 CI 判定"版本没变"直接跳过）
2. `changelog.txt` 顶部加一段
3. push 到 `main`
4. `release.yml` 自动：跑测试 → 静态自检 → 打包贴图 → 暂存 → zip → 建 Release

`workflow_dispatch` 可以勾 `force` 强制发同名版本 —— **版本号不升、又要把改动打进包时走这条**。
普通 push 会因为"版本没变"直接跳过，Release 删掉了也不会重建。

没有 `gh` 也能触发：

```bash
POST /repos/<owner>/<repo>/actions/workflows/release.yml/dispatches
body: {"ref":"main","inputs":{"force":"true"}}   # 204 = 受理
```

token 从本机 git 凭据取：`git credential fill`（只放进变量，别打印、别落盘）。

### 写 changelog 的规矩

- **同一个问题反复改过的，只写最后落地的做法和数值。** 中间过程（先改成 A、后来又改成 B）
  不要写进去 —— 用户看的是"这一版有什么变化"，不是改动流水。
- 别把过程值写进条目：例如"合成 84.6%"后来调到 72%，就只写 72%；
  "行距 420"后来改成 358，就只写 358。
- 一条问题只占一个条目。同一件事在 `[修复]` 和 `[调整]` 里各写一遍属于重复，合并掉。
- 写"为什么"比写"改了哪个参数"有用。参数细节留给 git log 和 docs。
- **不要写开发工具。** `tools/` 整个目录都不进包，用户拿不到那些脚本，
  写进 changelog 只会让人以为包里有 .py。changelog 只写用户能看到的变化。
- **一条一行，尽量控制在 40 字内。** 不换行展开解释；抽样数量、根因、调研过程写进
  `docs/`，不进 changelog。
- **用 Kodi 术语**：窗口 / 控件 / grouplist / label / fanart / OSD / 底板 / 遮罩。
  不写"优化体验""打磨细节"这类空话，写法参照 1.5.x 及更早的段落。
- **数值写「旧 → 新」**，不写成"从 A 改为 B，因为……"，结论先行。

---

## 7. 已知遗留

| 项 | 说明 |
|---|---|
| 圆角半径两档制 | 短边 ≥200 → r12、<200 → r9（见 §5.4.1）。改任何一档都要连带改遮罩、焦点环、底板 `round<N>`、细边 `edge_*` 四样 |
| addon 简介措辞 | ✅ 2026-10-28 已补：中英两条 description 都写了「（同时最多两个）」/「(up to two at a time)」，随 1.2.0 发 |
| 系统信息 / 事件日志的底部文字区 | 这两页底部**故意**和 PVR 不一样：`SettingsSystemInfo` 没有"当前项"，底部 y 555–885 被内存/CPU 浮层占用，所以不挂帮助条；`EventLog` 用 `label id=70`（915, h40）+ `textbox id=71`（955, h60）拼成两行，合起来仍占 915–1015 那 100px。**如果希望三页底部完全一致，需要先决定这两页要不要让出那块区域** |
| `SettingsSystemInfo` 滚动条轨道 | ✅ 2026-10-29 已改：`id=60` 轨道 644 → **357**（它服务的是 `textbox id=30`，193→550 高 357；写 644 会让滑块按两屏算比例）。几何回归测试已按页取期望值 |
| 首页「类别」行的名字 | 显示的是 Emby 插件节点名（`EMBY DYNAMIC: 音乐 (music)`），皮肤层无法截断字符串。要么在 Emby 里改库名（Helper 下次同步会跟着改名），要么在「自定义媒体库封面目录」里放 `<新名字>.jpg` |
| 音乐「类别」行的 `EMBY DYNAMIC:` 前缀 | **皮肤层修不了**。Emby 把媒体库名写成 Kodi 的 `tag`（视频库有 `tag` 表），但**音乐库没有 tag 表**，只能退回动态节点。`String.Replace` 两种写法实测均失败。想改只有「Emby 端关动态节点」或「换成 `musicdb://genres/`」两条路，2026-10-30 决定不改。详见 `skin-contracts.md` §4.2 |
| 歌词只对 CU LRC 有内嵌排版 | `xml/script-cu-lrclyrics-main.xml` 里硬编码了 `script.cu.lrclyrics` 的窗口和 `list id="110"`。**两种情况会失效**：① CU LRC 升级改了控件 id；② 用户在设置里换成别的歌词插件。表现是「右侧内嵌排版没了、歌词以插件自己的全屏界面出现」——**不报错、不影响播放**。歌词继续用 CU LRC 而不自建，理由见 `helper-plugin-plan.md` §6（用户最常用的"自动下载歌词"是自建做不了的那部分） |
| 本地搜索不含人员/类型 | 1.2.0 起本地快速搜索只匹配 `title` / `originaltitle` / `sorttitle` 前缀，**不要加回来**；人员/类型走服务端桥（0.3.3+，仅中文查询并入） |
| 类别行 / 专辑行左边缘 | 差 18px（60 vs 78），用户明确说"不用统一" |
| 专辑卡片长标题 | 卡宽 186，font12 只放得下 8 个汉字；超长靠聚焦时滚动 |
| `tools/universalize.py` | 4.2.0 → 1.0.0 的一次性迁移脚本，已完成使命，留作参考 |
| 文件管理器点 flac/wav 弹「选择模拟器」 | **Kodi 侧行为，皮肤改不了**（2026-11-05 查清链条，见 §7.1）。`playercorefactory.xml` 这条路**已确认无效，别再试**。规避：从音乐库 / Emby 播放 |
| 文件管理器路径行的中文是 `%E7%BD%91%E7%9B%98` | **皮肤改不了**（2026-11-05 实测）：① 该窗口会**按 `id=101` 强写路径标签**，XML 里的 `<label>` / `<visible>` 对它无效，连写死的中文都会被覆盖；② `Container.FolderPath` / `Container.FolderName` / `Container.NumItems` 在 10003 里全是空串，只有焦点项的 `ListItem.FolderPath` 有值。试过用 helper 解码写窗口属性，最终方案要靠"把 101 用动画滑出屏幕"来绕，太脆，**已回退**。要修只能等 Kodi 支持 URL 解码 |

> **已修（2026-10-27）**：`ListItem.BMP` → `ListItem.BPM`（BPM 徽标现在能显示了）；
> `ListItem.MusicBitsPerSample` 那条删掉了 —— Kodi 没有列表项位深标签，
> 位深只有播放器上下文的 `Player.Process(AudioBitsPerSample)`。
> 当时的判据是拿 Kodi 21.2 与 master 的 `xbmc/GUIInfoManager.cpp` 标签名总表逐条比对
> `$INFO[...]`。**排查同类问题的方法**：把皮肤里所有 `$INFO[X]` 的 X 取出来，
> 去掉 `(...)` 参数和 `$PARAM[...]` 前缀，取最后一段，与标签表求差集。

### 7.1 文件管理器里的音频被当成游戏（2026-11-05 定论）

**现象**：设置 → 文件管理器 点 `.flac` / `.wav`，弹「选择 .flac 文件的模拟器」，里面列着一个
Sega 模拟器核心。

**链条**：

1. 官方仓库索引里 `game.libretro.blastem` 的 extensions 含 `flac|wav`（Genesis 核心支持 CD 音轨）
2. `CFileItem::IsGame()` 在条目没有音视频标签时调 `CGameUtils::HasGameExtension()`，
   而它**不只看已装核心，还扫「可安装」列表**（`LoadInstallableAddons()`）→ 返回 true
3. 文件管理器列表项没有音乐标签 → `IsAudio()` 为假，音视频两个默认分支都进不去
4. `CPlayerCoreFactory::GetPlayers()` 末尾是 `players = {"RetroPlayer"}` —— **赋值覆盖**，
   规则里加进去的 PAPlayer 会被整条丢掉

**实测日志**（2026-11-05，22.0-RC1，开 debug 后用 JSON-RPC 播 `D:\音乐\*.flac`）：

```
CPlayerSelectionRule::GetPlayers: matches rule: mistuary-audio-files
CPlayerSelectionRule::GetPlayers: adding player: PAPlayer for rule: mistuary-audio-files
CPlayerCoreFactory::GetPlayers: matched 1 rules with players
CPlayerCoreFactory::GetPlayers: adding player: VideoPlayer
CPlayerCoreFactory::GetPlayers: forcing retroplayer
CPlayerCoreFactory::GetPlayers: added 1 players
```

**结论：`playercorefactory.xml` 这条路是死的。** 规则能命中，结果会被 `forcing retroplayer`
覆盖。2026-10-30 试过一次、2026-11-05 又试了一次（两次都删了测试文件）——
**不要试第三次**，直接看这一节。

**能不能修**：只有让 `IsGame()` 变假，两条路都不通：

- 条目带音乐标签 —— 文件管理器给不了，皮肤和配置都做不到
- `HasGameExtension()` 变假 —— 需要「已装 + 可安装」里没人声明 flac；禁用
  `repository.xbmc.org` 能做到，但会连带装不了 / 更新不了插件，代价太大

**规避**：从音乐库 / Emby 播（有条目标签，不走这条判定）。上游 master 仍是
`players = {"RetroPlayer"}`，2026-11-05 决定不提 issue。

---

## 8. 交接前状态（2026-10-30）

### 8.1 当前 git 状态

**这里不钉 commit hash 和"领先几个提交"** —— 那种快照提交完就过时（踩过：刚写完就又不准）。
要现状直接跑：

```bash
git log -1 --oneline        # HEAD
git status -sb              # 与远端的关系 + 工作区
```

稳定的只有这几项：

> 下表是 **2026-10-30 的发版快照**；当前版本、贴图数量和测试项数以 §1 与 `git` 为准。

| 项 | 值 |
|---|---|
| 版本 | `addon.xml` = 1.4.0，本次发版 |
| 贴图 | `Textures.xbt` 749 张 / 7.2 MB；`media/` 是 748 张 PNG + 1 张 JPG（另有 `LICENSE.txt`） |
| 打包状态 | `xbt` 与 `media/` 一致（`unpack` 749/749），改过 png 才需要重打包 |

> 要发新版才升 `addon.xml`（§6）。

**开发机当前状态**：实机已经是**散图模式** —— `media/` 下没有 `Textures.xbt`，
改 png 只需 F5 重载皮肤，不用重启（§0 第 3 条）。

> 注意：实机 `media/` 里可能残留历年删除的旧图（`--loose` 同步只覆盖不删除）。
> 仓库当前是 748 张 PNG + 1 张 JPG；残留图没有引用、不影响运行，想要干净可以整目录删掉
> 重新同步一次。
>
> 发版前记得 `python tools/xbt_tool.py pack` 把散图打回包（§6）。

### 8.1.1 本轮（1.3.1）改了什么 —— 2026-10-30

**已提交并推送的 6 个**：

| 提交 | 内容 |
|---|---|
| `3e43cf5` | 详情页 6 处文字加 `shadow_hard` 阴影（亮 fanart 下可读） |
| `905689f` | 文档更正 + Emby 节点调研 |
| `453e37b` | 海报墙 244×352 → 236×340，缝 16 → 24 |
| `49c1fc0` | 卡片信息重排 + 状态图标绿色 + 图标素材统一 |
| `b30e3e2` | 评分移到右上、边距统一 12px、垂直居中 |
| `f17d8a3` | HANDOVER §5.9 / §5.9.1 更新 |

**已提交并随 1.3.1 发布**：

- `addon.xml` 1.3.0 → **1.3.1**
- `changelog.txt` 新增 1.3.1 段
- `HANDOVER.md` / `pending-work-plan.md` 版本号
- `media/Textures.xbt` 已重打包（当前 749 张 / 7.2 MB；`89b71a5` 又删了 2 张孤儿贴图）

### 8.1.2 1.4.0 本轮改了什么

- `addon.xml` 1.3.1 → **1.4.0**，summary / description 补可选 helper
- `changelog.txt` 新增 1.4.0 段（豆瓣评分、次评分来源、服务端搜索、已知问题）
- `README.md`：749 张贴图、可选 helper 安装说明、已知问题
- 详情页豆瓣评分接线：`DialogVideoInfo.xml` / `Includes_DialogVideoInfo_Hero.xml` / `Variables.xml`
- 「次评分来源」设置：`SkinSettings.xml`
- 文档同步：`HANDOVER.md` / `pending-work-plan.md` / `helper-plugin-plan.md` / `docs/README.md` / `skin-contracts.md`
- 测试：`tools/test_nara_douban_rating.py`

> 提交前用 `git diff --cached --name-only` 核对，不要把两个仓库混在一起。
> 另一个仓库 `script.mistuary.helper` 独立发布；1.4.0 时未包含其代码。helper **0.3.11 已发布**，皮肤 **2.1.0 已发布**。

### 8.2 发版记录

| 版本 | 要点 |
|---|---|
| v1.0.0 / v1.1.0 / v1.1.1 | 通用版落地、透明度三档、技术标识图标化 |
| **v1.2.0** | 真圆角（diffuse 遮罩）+ 播放条重排 + 搜索增强 + 主评分四档 |
| **v1.2.1** | 包体 10.2 → 7.2 MB（清死图）+ 系统信息页滚动条 |
| **v1.3.0** | 黑胶模式 + 音乐信息页重做 + 电源菜单 + 详情页背景兜底；Kodi 21 标签/导航修复 |
| **v1.3.1** | 详情页文字阴影（亮背景可读）+ 海报墙间距 16→24 + 卡片信息重排（评分右上/状态左下/集数右下）+ 已看完绿色 |
| **v1.4.0** | 详情页豆瓣评分（可选 helper 0.2.0+）+ 次评分来源四档 + 服务端搜索可用 + 豆瓣查询修复；已知：搜索无封面、搜索页无背景兜底 |
| **v1.5.1** | 状态图标区分未看/部分/看完 + 主评分四档定稿（TMDb/IMDb/豆瓣/自动）+ 移除次评分设置 + 技术标识/评分行条件修复 + 2160 百分比适配 + 搜索背景重排 + 用户评分徽标补 definition + 详情页豆瓣次评分修复 + 插件图标读 thumb + 设置级别按钮下沉。**含原 1.4.1 与 1.5.0 的全部改动；两个 tag/Release 均已撤回** |
| **v1.5.2**（待发） | **只支持 Kodi 22**（`xbmc.gui` 5.17.0 → 5.18.0，砍掉 21 双轨）+ 图片浏览对话框改双向锚定（2160 屏不再空一条）。改动来自 `docs/audit-2026-10-31.md` 的 🟡2-1 / 🟡2-2 |
| **v1.6.0** | 首页收藏夹横版卡 + 背景遮罩统一 + OSD / 弹窗打磨 |
| **v1.7.0** | 音乐 OSD 自动隐藏 + 收藏夹自定义封面 + 全部未看首页行 + 皮肤助手页；电视剧详情页起播直接全屏 |
| **v1.8.0** | 皮肤助手页直接开关豆瓣/播放列表补全/跨季 + 设置帮助整理 + 卡片评分口径统一 + 音乐封面圆角 |
| **v1.8.1** | 主页「退出」按平台执行（退出 / 关机 / 电源菜单）+ 自动评分帮助修正 |
| **v1.8.2** | 首页 Hero 评分左移并与年份同一条 grouplist + 评分胶囊加宽/居中（10.0 不再裁）+ 底板 30% + 首页卡片标题居中 / 集数右下 + 设置页背景 20% 轻遮罩 |
| **v1.8.3** | 首页末项固定「电源」并打开电源菜单 + 电源菜单高度按 `System.Can*` 适配（Windows/CE/Android 不再多出空白）+ 设置中心平台标签改为纯显示 |
| **v1.9.0** | 文件播放记录（10003 焦点行续播圆环 + 起播续播询问 + 设置项，需 helper 0.3.7）+ 列表续播进度与时间 + 文件管理器列宽（日期 1170→1213、文件名 1080→1000）+ CoreELEC 电源菜单「重启到安卓」+ 设置页剧照中性底（去紫灰） |
| **v1.9.1** | 背景统一 + 弹窗表头统一：文件管理 / 搜索 / 首页「文件」「收藏」剧照统一 ×0.66 压暗；弹窗标题 28px 与正文左对齐、右上角图标 48→32；选择列表改整块底板 |
| **v1.9.2** | 媒体库封面逐层兜底（E4K 导出 → 自定义目录 → 内置图）；后续证实 E4K 不落盘库封面 |
| **v2.0.0** | 媒体库封面改由 Helper 从 Emby 同步（删除 24 张内置分类封面，兜底图移入 `extras/artwork/`）+ Helper 改硬依赖 + 设置页去掉「皮肤助手」分组并重排（媒体 12 / 播放 8）+ 720 改名「详情页联网取豆瓣」并与 715 联动 + 722 按目录补全默认开 + 文件浏览器 / 弹窗改真剧照玻璃背景 + Windows 电源菜单只留退出 / 设置 |
| **v2.1.0** | 季视图改为剧集详情页版式（hero + 播放 + 季标签 + 本季集卡片，全入口一致）+ 季页背景与详情页同参数 + 季标签升序 + 侧边栏「横排」改名「海报行」+ 剧集卡片标题下移 + 共用随机背景对话框补齐独立取图；最低 Helper 0.3.9 |
| **v2.1.1** | 弹窗补齐不透明剧照底层 + 随机剧照改为一会话一张 + 背景亮度统一 + 首页与详情页 150% 构图 |
| **v2.2.0** | 背景剧照色光底 + 技术标识重画；最低 Helper 0.5.0 |
| **v2.2.1** | 背景剧照铺满全屏 + 35% 淡色光 + 四档压暗扩到 14 个 XML / 16 处 + 文件/收藏 list 遮罩同档；清理 1 张孤儿贴图、1 个死 include |

> **当前版本以 `addon.xml` 为准（2.2.1，已发布）**；本节是历史发版记录，1.5.2 行的“待发”保留为当时状态。

> **1.2.0 卡过一次**：升版本号后 CI 的 `test` job 因 `xbt_tool` 缺 Pillow 失败，
> 当时只修了 CI 没再升版本 → 工作流判定「版本号未变化」跳过，Release 一直没生成。
> 后来 `5020f1f` 把版本号退回 1.1.1、再重新升到 1.2.0 才发出去。
> **教训**：CI 失败后要重发**同版本**，走 `workflow_dispatch` + `force=true`。
> **1.4.1 / 1.5.0**：两个 tag/Release 均已撤回；改动并入 **1.5.1** 一起发布。
> 不存在「Release 已存在」的闸门问题。

### 8.3 最近两天做过什么（免得重做）

| 主题 | 落点 |
|---|---|
| 主评分来源四档 + 手选优先 | 设置 707、`NaraOnlineRatingsRow`、`NaraDefaultRatingSourceVar`（§5.7） |
| 搜索首字母改前缀匹配 | `sorttitle` 用 `startswith`，并**移除** `actor` / `director` / `genre`（§5.10） |
| 帮助文案统一 | 「弹窗透明度」、26 条帮助条改陈述式、双引号 |
| 圆角二期 | 全库收口，30 张 diffuse 遮罩、8 环 + 1 细边（§5.4.1） |
| 死资源清理 | 22 + 33 张零引用贴图删除，包体 −29%（`d29a225` / `0ebccc5`） |
| 自检补反向检查 | `audit_skin.py --orphans` / `--dead`（§4） |
| 插件规划 | `docs/helper-plugin-plan.md`（摘要），含 Helper 契约 §2（2026-11-05 起为硬依赖） |
| **helper 插件落地** | 独立仓库 `<插件仓库根>`，**0.3.11 已发布**（229 项单测）：服务端搜索 + 详情页豆瓣评分（优先读 Emby `/Douban/RatingsByImdb`）+ 播放列表补全 + 文件播放记录（10003）+ 媒体库封面 + 未同步剧集浏览（0.3.10 搜索剧集跳库 / 0.3.11 插件自己的季/集列表）。皮肤侧 M1b / M2 / M1c 已完成；M1d 演员/类型已完成（0.3.3 仅非 ASCII，2026-11-13 起英文 ≥5 位连写 / 含空格也并入）；M3 不做 |
| 黑胶唱片模式 | OSD 最右按钮切换，素材 `tools/gen_vinyl.py`（§8.9 之后的新条目） |
| 音乐库背景兜底 | 无 fanart 时用音乐页背景图，`6c357c4` |
| 死代码清零 | 21 死变量 + 6 死 include；`--dead` 现在 0/0 |
| 电源菜单补齐 | 退出/关机/重启/待机/休眠/重载皮肤，按平台能力自动显隐；面板收到 400×456 |
| 死分支清理 | 40 处 `!$EXP[nara_dialog_glass]` + 65 恒真条件 + 6 个 `NaraDialogLegacy*` + 1 张贴图 |
| 卡片格回到 260 | 264 在真机掉成 6 列，回 260 恢复 7 列 |
| 设置页重排 | 4 类：首页 11 / 媒体 7 / 界面 5 / 播放 2（§5.3.2） |
| 音乐信息页 v4 | 全幅两栏、452 封面、内置 7/8/10/12 隐藏 + SendClick（§5.8.1） |
| 详情页背景兜底 | Video/Music/Addon 用 `primary_background_info`；Addon 无 fanart `sc_2`（§5.8.2） |

### 8.4 发版前检查（2026-11-10 更新）

> 2.2.1 已发。当前版本以 `addon.xml` 为准。

| # | 事项 | 材料在哪 | 需要什么 |
|---|---|---|---|
| 1 | **2.2.1**（已发布） | `changelog.txt` 2.2.1 段、§6 发版流程 | `v2.2.1` tag/Release 已生成 |
| 2 | **helper 0.5.0**（已发布） | helper 仓 `docs/release.md` §6 | 皮肤 import 下限 0.5.0 |
| 3 | 首字母严格性 | — | ✅ 已完成 |

> **Kodi 21 实机验证已放弃**（2026-10-30，用户决定），原因与事故记录见 §8.7。
> 外部校验报告的 P0 / P1 / P2 已在 1.3.0 清完，`report-triage-2026-10-29.md`
> 里剩下的 `<scroll>` 与校验器噪音都是刻意不做的项。

### 8.5 新接手先跑这五条

```bash
python tools/audit_skin.py --strict                      # 必须 EXIT=0
python tools/audit_skin.py --orphans                     # 应报 0 张
python tools/audit_skin.py --dead                        # 应为 0 变量 / 0 include
python -m unittest discover -s tools -p 'test_*.py'       # 118 项
python tools/gen_corner_masks.py --check && python tools/gen_rings.py --check   && python tools/gen_glass_plates.py --check && python tools/gen_techflag_vars.py --check
```

### 8.6 待决策（0 项）

1. ~~**剧集「未看」仍显示眼睛**~~ —— **已解决**（本轮 `a88d0df`）：
   `ItemStatusIconVar` 改用 `PlayCount` / `TotalEpisodes` 判断，纯 Kodi 库也有兜底；
   未看不再挂眼睛，看了一部分才挂。旧的 `Property(has_progress)` 方案不再需要。

2. ~~**评分圈按来源着色**~~ —— **已实施**（2026-10-31）：
   `NaraRatingRingColorVar` 按 707 给 `badge_ring.png` 着色，数字保持白色。


> **播放地址已定，只剩实机验证**（2026-10-30 更正）：`lib/emby.py:56` 的 `play_url()`
> 已经写成 `plugin://plugin.service.emby-next-gen/?mode=play&item=…`，退路是 Emby 直链。
> 搜索列表接线**不依赖**这条路径 —— 列表渲染失败不影响接线本身，播放路径要改也只是插件里一行。
>
> 兼容目标**已改为 Kodi 22 only**（2026-10-31，见 §5.2）。原来定的「保持 Kodi 21+」
> 已作废：21 的回退分支在 1.5.2 里删掉了，`addon.xml` 声明 `xbmc.gui 5.18.0`。

### 8.7 Kodi 21 实机：已放弃（2026-10-30）

**决定**：不做。双轨渲染（`$MAP` 在 21 上退化成原始值、13 个 v22 标签靠
`!String.IsEmpty` 保护）**至今只在 22 系列上跑过**，21 上从没验证过。

**为什么放弃**：21 的媒体库版本和 22 不兼容（`MyVideos131` vs `149`），
便携环境就算搭对了也**没有媒体库**，只能验首页渲染和皮肤能否加载；
详情页的技术标识 / 评分 / 音轨 / PVR 台标这四项**验不了**——
要验得在 21 里重新连 Emby 同步一次库，成本远高于收益。

**残留风险**：21 用户遇到问题我们没有任何实机依据。
`report-triage-2026-10-29.md` 里的 21 回退点是按源码逐条比对得出的，不是实测。

#### 事故记录（2026-10-30，务必别重犯）

用 7z 解包 `kodi-21.3-Omega-x64.exe` 到 `D:\Kodi21-test\kodi21\`，
但 **`portable_data` 建在了 exe 的上一级**（必须在 **exe 同级**）。
Kodi 没认出便携模式，直接读写 `%APPDATA%\Kodi`，于是：

```
error: CSettings: unable to load settings from special://masterprofile/guisettings.xml,
       creating new default settings
```

**Kodi 21 读不懂 22 的 `guisettings.xml`，不降级读取，直接新建默认设置并写回。**

| 损失 | 状态 |
|---|---|
| `guisettings.xml` | 全量重置（界面 / 播放 / 字幕 / 音频 / 皮肤设置全丢） |
| `lookandfeel.skin` | 变 `skin.applify`，22 加载失败回退 Estuary |
| `locale.language` / `country` | 变 `en_gb` / `Australia (12h)` |
| 数据库 / `addon_data` / `sources.xml` / `advancedsettings.xml` / `keymaps` | 全部完好 |

修复：皮肤 / 语言 / 时区已改回。**皮肤设置一条没手写** —— 三个 tint 变量的兜底值
就是文档默认（`NaraGlassPageTintVar`→`gl_3`、`FloatTintVar`→`gl_4`、
`PlaybackDialogTintVar`→`gl_2`），不设置等于默认，手写 XML 反而有格式风险。
用户仍需自己重设音频输出设备、直通、刷新率、播放器设置（21 默认值，无法恢复）。

**三条教训**：

1. Kodi 便携模式判据是 **exe 同级**的 `portable_data`，建之前先确认 exe 路径。
2. 跨版本验任何东西，**启动前把 `%APPDATA%\Kodi` 改名成 `Kodi.disabled`**。
   物理隔绝比"我建了 portable_data 应该没事"可靠一万倍。
3. **启动前备份 `guisettings.xml`**。当时备份了 478 MB 的数据库，
   却漏了这个几 KB 但**不可恢复**的文件。

### 8.8 给下一任的提醒

- **提交纪律**（§4）：永远 `git add <具体文件>`、`git diff --cached --name-only` 核对再 commit。
  这个仓库可能多个 agent 并行改，工作区里随时有别人的未提交改动，别一把扫进自己的提交。
- **开发期同步实机用散包**：`python tools/sync_to_kodi.py --loose`（改 png 只重载皮肤就生效）；
  **递交 / 发版前**才 `python tools/xbt_tool.py pack` + 普通 `sync_to_kodi.py`。
  ⚠️ `--loose` 要把目标端 `Textures.xbt` 挪成 `.off`，**Kodi 开着时挪不动**，会只同步散文件。
- **版本号没升 = 没发版**：push 会触发发版，"提交"和"发版"要分开确认（§6）。
- 圆角机制只有一条正确路子：`<texture diffuse="shapes/mask_<w>x<h>_r<N>.png">` + 遮罩尺寸与控件一致
  （§5.4.1）；`scale` 才写 `scalediffuse="false"`，`keep` **不要写**（写了等于没圆角）。
- **不要擅自 commit / push / 发版**：改完先说明什么 + 验证结果，等指令。
  **但同步实机不用问**：改完自己跑 `sync_to_kodi.py --loose`（§0 第 4 条）。

### 8.9 helper：接入状态（2026-11-05 更新）

- 插件 `script.mistuary.helper` **0.5.0 已发布**（229 项单测）：服务端搜索 +
  详情页豆瓣评分 + 播放列表补全 + 文件播放记录 + 媒体库封面 + 未同步剧集浏览。
  0.3.10 修搜索剧集跳转（按标题 + tmdb/tvdb 在 Kodi 库里定位）；0.3.11 让库里没有的
  剧集进插件自己的季/集列表（子列表只拉一层，ParentId + Limit 500，缓存 5 分钟；
  播放仍走 Emby 插件的 mode=play）。
  **补全三个开关（721 按季 / 722 按目录 / 723 跨季）**：722 **默认开**，721 / 723 默认关
  （721 依赖 E4K 建好的剧集库，723 依赖 721）。722 只列举本地 / SMB / NFS 目录，
  `plugin://`、`http(s)://`、`pvr://` 直接跳过；条目带季集信息时优先走 721 同季，
  不会重复入队。文件播放记录只记 10003，10025 走 Kodi 原生续播。
  电影 `season=-1` 误判和 HTTP 流目录列举报错已修。
- **720 详情页联网取豆瓣**：helper setting `douban_enabled`，**默认开**。只控制详情页是否请求
  （先问 Emby `/Douban/RatingsByImdb`，失败再走豆瓣公开接口）；关闭后不写 `Mistuary.Rating.*`，
  库里已有的 `Rating(douban)` 照常显示。715 选烂番茄/关闭或主评分选豆瓣时该行隐藏。
  细则见 §5.7。
- 0.3.x 起豆瓣分优先读 StrmAssistant 的 Emby `/Douban/RatingsByImdb`，失败才回退
  豆瓣公开接口；窗口属性新增 `Mistuary.Rating.Source`（emby / douban）。
- 0.3.3 的设置改动（4 分类、逐项帮助条、专家级覆盖项）已并入 0.3.4 发布；
  新增「测试 Emby 连接」。
- 皮肤侧 M1b 搜索与 M2 豆瓣已接；**M1c 实机验收已完成**（含播放）。
- 1.5.1 起主评分四档、次评分 豆瓣→烂番茄；**列表 / 首页不显示豆瓣次评分**，
  插件写的 `rating_type=douban` 暂无消费方。
- **M1d 演员/导演/类型**：0.3.3 起支持非 ASCII 查询并入结果；2026-11-13 起英文 ≥5 位连写或含空格也并入，2–4 位 ASCII 连写仍按拼音首字母做前缀严格匹配；**M3 代表集**不做（皮肤用两级探针自行解决）；
  **M4 行级增强**不做（首页行拿不到逐条插件属性，节点名无法由皮肤改写）。
- 装/卸/启用插件后要**重载皮肤**；卸载后的回退是下一帧生效。
- 规划与契约见 [`helper-plugin-plan.md`](helper-plugin-plan.md)；实现文档在
  `<插件仓库根>\docs\`。

### 8.10 已知问题：搜索封面 / 背景兜底（已解决）

- **搜索封面**：插件 `c4ac966`（0.3.0+）让 `image_tag` 回退读 `ImageTags.Primary`，
  并返回 backdrop；实机已确认有封面。
- **搜索背景兜底**：皮肤 `baae9ef` 重排了 `NaraSearchBackground`（百分比 + 渐变 +
  随机剧照 / 结果剧照两级）；无 fanart 时不再纯黑。
- **播放地址**：`mode=play` 已随 M1c 实机通过。

历史细节保留在 `docs/handover-2026-10-30.md` 与插件仓库 `docs/roadmap.md`。

### 8.11 2026-11-03 当日改动

> 详见 [`handover-2026-11-03.md`](handover-2026-11-03.md)。
> **1.8.3 已发**；标「未发」的三条已随 **1.9.0** 进包。

- `39eccde`：清理 Home / 设置页重复的 `primary.jpg` 兜底层；设置页真图下加不透明黑隔层
- `5cc2af0`：首页卡片标题居中、集数移到缩略图右下角（纯白 + 黑阴影）；`.gitignore` 加 `vibe_images/`
- `2793d17`：设置页不透明黑隔层 → **20% 轻遮罩**，剧照不透明度 63% → **55%**，紫色兜底保留
- `d3d0c9d` / `d20a74d` / `ceaca5e`：1.8.2 发版（Hero 评分重排、胶囊加宽、文档）
- `5e92db6`：设置中心 LibreELEC / CoreELEC 标签改为纯显示（不可聚焦）
- `82797c9`：首页末项固定「电源」并打开电源菜单；菜单高度按 `System.Can*` 适配
- `a4b5206`：**release 1.8.3**
- `b114052`（随 1.9.0 发）：CoreELEC 电源菜单新增「重启到安卓」，16 条背景高度
- `efc4ae8`（随 1.9.0 发）：`.gitignore` 忽略根目录 `kodi.log`
- `9d9022a`（随 1.9.0 发）：31817 文案「切换到安卓」→「重启到安卓」
- helper 仓库 `aee200f` / `0c54c64`：**0.3.6** 发布包补上 `service.py`
  （此前 Release zip 里的播放列表补全服务从未启动，CE 日志报 `service.py` 不存在）

### 8.12 2026-11-04 当日改动（随 1.9.0 发布）

- `49cc54c`：**文件播放记录**。10003 焦点行 40px 续播圆环（101 帧、百分比烘焙在贴图里、
  无暗底）+ 1115 两行续播弹窗（`round20` + 浮窗档，默认焦点「继续播放」）+
  设置页「文件播放记录」开关 + 列表视图续播进度条与「续播 h:mm:ss」；
  文件管理器日期列 `1170 → 1213`、文件名列 `1080 → 1000`，中间留出 40px 圆环位。
  详见 §5.15。
- `24dd1ce`：文档同步 10003 范围、保留设置与「不写原生续播点」。
- `a990266`：设置页半透明剧照改用中性底 `FF4D4D4D`（`NaraNeutralFanartBase`），
  去掉 `primary.jpg` 平均色（约 `63,77,110`）带来的紫灰罩；显隐与剧照层共用
  `$EXP[nara_settings_shared_fanart_visible]`，避免两层条件漂移。
  （该表达式 2026-11-05 已改名为 `nara_page_shared_fanart_visible` 并移入 `Includes.xml`，
  见 §8.13）
- helper 仓库 `bcc3656`：**release 0.3.7**（文件播放记录首次发布）。

### 8.13 2026-11-05 未发改动：中性底色推广到 4 个页面

> **已递交并推送**（`5ea3757`，随同批还有 `9a14dc1` CI、`c2aba50` 文档）。
> 静态检查全绿；**首页「文件 / 收藏」已实机确认**（2026-11-05，JSON-RPC 截图）；
> 设置页 / 文件管理 / 搜索空查询沿用设置页那套已验证的结构。方法见 §5.11.1。

把设置页那一处中性底推广到全部半透明剧照页，并把设置页的私有表达式提成通用：

| 文件 | 改动 |
|---|---|
| `Includes.xml` | 新增 `nara_page_shared_fanart_visible`（设置页 / 文件管理）、`nara_search_empty_fanart_visible`（搜索空查询） |
| `Includes_Home.xml` | 新增 `nara_home_files_fanart_visible`（首页文件 / 收藏） |
| `Includes_Settings.xml` | 删掉旧的 `nara_settings_shared_fanart_visible`，两处 `$EXP` 改用通用名 |
| `FileManager.xml` / `Includes_Search.xml` | 加中性底 + 剧照层改用通用表达式 |
| `Home.xml` | 文件 / 收藏的中性底，带 `DepthBackground`，并与剧照层共用收藏详情弹窗的淡出动画 |

验证：`audit_skin.py --strict` 缺失项 0、`check_home_fanart_mask.py --check` 17/17、
单测 91 项 OK、124 个 XML 全部可解析；6 个文件 md5 与 Kodi 目标一致；四条旧条件与新表达式
**逐字相同**（只是提成命名表达式，显隐语义没变）。

⚠️ **`--dead` 不检查 expression**（只查 include / 皮肤字符串 / 贴图），别拿它当"表达式没写错"的证据；
三条新表达式是否有引用点，用 `grep -rn '\$EXP\[nara_' xml/` 确认。

**收藏页的坑**：此前记成"`homemenunofavoritesbutton=true` 所以被隐藏"，实际是 **`false`**，
按钮一直显示（`Home.xml:1703` 的判据是 `!Skin.HasSetting(HomeMenuNoFavoritesButton)`，
Kodi 存储时设置名小写；`NaraHomeMenuDefaultsMusicTVOff` 标记已置位，首启默认值不会再覆盖）。收藏与「文件」共用同一张随机剧照，可用像素比对验收：
同一区域最大通道差 0；详情弹窗开/关无灰块残留。

**这批没进 1.9.0 的包**：`release.yml` 只在 `addon.xml` 版本变化时打包，所以要让用户拿到，
必须先升版本号（1.9.1 或 1.10.0）再 push。光 push 只跑测试。

**第三轮（定稿）：乘法压暗 + 烘焙阅读区**。

1. **乘法压暗**：剧照改 `FFA8A8A8`（RGB ×0.66、不透明），照片的层次和色彩都保留，
   **中性底整块删掉**（`NaraNeutralFanartBase` 已从 `Includes.xml` 移除），四页各少 1 层。
   （2026-11-06 调整为两档 token：无阅读遮罩的六页降到 `fanart_dim` 0.50，见 §5.11.1）
2. **烘焙阅读区**：遮罩 + 顶部渐变 + 底部渐变 + 左侧 scrim 合成一张 720p overlay
   （`tools/gen_fanart_overlay.py`，三个变体 hero / list / empty），每页少画 3 层。
   做过受控 A/B：固定测试图分别用「4 层」和「烘焙 1 层」渲染，逐像素平均差 **0.5~3.9/255**
   （最大 9），肉眼不可见。
3. **音乐分区不吃阅读区**：背景图本身亮度约 73，遮罩 + 三条渐变纯属白画，6 层 → 2 层。

| 页面状态 | 改前 | 改后 |
|---|---|---|
| 电影 / 电视剧 | 6 | **3** |
| 搜索 · 有结果 | 6 | **3** |
| 搜索 · 空查询 | 6 | **3** |
| 文件 / 收藏 | 6 | **3** |
| 文件管理 | 4 | 3 |
| 设置页 | 3 | 2 |
| 音乐 | 6 | 2 |
| **合计** | **37** | **19** |

**overlay 是 720p 不是 1080p**：四层都是平滑渐变，拉伸看不出差别；1080p RGBA 一张 8MB，
720p 只要 3.5MB，三个变体合计 10.5MB，比原来的 3840×2160 遮罩（33MB）还省。

**下版 changelog 草稿**（升版本时贴到 `changelog.txt` 顶部，按 §6 的规矩再压一遍字数）：

```
[修复]
- 文件管理、搜索与首页「文件 / 收藏」的半透明剧照不再被兜底背景染成紫灰
- 这四个页面的背景亮度统一到设置页的水平（剧照一律 ×0.66 压暗，不再发灰）
- 音乐页背景不再叠 4 层遮罩与渐变
- 电影 / 电视剧 / 搜索的阅读区合并为一张贴图，滚动与切页更省
- 弹窗标题统一 28px 并与正文左对齐，右上角图标缩小内收
- 选择列表去掉内嵌层，标题与列表文字对齐

```

### 8.14 2026-11-05 弹窗表头统一（`dc33920`，已推送）

**问题**：表头 4 套规格，字号 27 / 30 / 32、内边距 40 / 42 / 64；`DialogBackgroundCommons`
那套的 vendor 图标 48px 放在 `right 10 / top 11`，直接压在 20px 圆角上；标题 32px 配 48 左距，
在小弹窗上只有 1.5 倍字高留白。

**改动**（13 个文件，33 增 21 删）：

| 项 | 改前 | 改后 |
|---|---|---|
| 标题字号 | `font32_title` | **`font28_title`**（新增） |
| 标题位置 | left 48 / top 18 / h 56 | top 24 / h 52，left 由 `header_left` 逐弹窗传 |
| 右上图标 | 48px @ right 10 / top 11 | **32px @ right 60 / top 36** |
| 选择列表底板 | 底板 + 内嵌层两层 | **只剩底板** |
| 选择列表计数 | 右边缘 1200 / bottom 10 | 1180 / bottom 24 |
| 右侧按钮列 | left 948 | left 936 |

**没做的**：B/C/D 三套表头（设置弹窗 / 流选择 / 插件信息）仍是各自老数值，见 §5.16。

### 8.15 2026-11-05 背景统一收尾 + 弹窗表头统一（待发 1.9.1）

**这批的内容**

| 主题 | 提交 | 详见 |
|---|---|---|
| 半透明剧照改乘法压暗 + 阅读区烘焙 | `5ea3757` | §5.11.1 |
| CI 校验烘焙 overlay 与生成器一致 | `9a14dc1` | §6 |
| 弹窗表头统一 + 选择列表去内嵌层 | `dc33920` | §5.16 |
| 文档 | `c2aba50` + 本批 | — |

**这批踩到的坑（比改动本身值钱）**

1. **文件管理器按 `id=101` 强写路径标签**：XML 里给这个 id 写的 `<label>` / `<visible>` 全部无效，
   连写死的中文都会被窗口覆盖。想在路径行做任何自定义，只能另起控件 + 把 101 用动画移出屏幕
   —— 太脆，放弃（§7 有记录）。
2. **10003 里 `Container.*` 全是空**：`Container.FolderPath` / `FolderName` / `NumItems` /
   `Container(1..3).FolderPath` 都取不到，只有焦点项的 `ListItem.FolderPath` 有值。
   判断"当前目录"只能从焦点项去掉最后一段推。
3. **helper 的 `log.info` 受 `debug_log` 门控**：没开 debug 时日志里**看不到** `service started`，
   别据此判断服务没起。判断服务是否在跑，用 `XBMC.GetInfoLabels` 查它写的窗口属性。
4. **helper 没有同步脚本**：真机曾长期停在 0.3.6（仓库早已 0.3.7）。已补
   `tools/sync_to_kodi.py`（排除 `tests/tools/docs/__pycache__`，跑完打印版本号）。

### 8.16 2026-11-06 当日改动（随 2.1.0 发布）

**季视图 B（`5654e77`）**

- 改动：`View_51_Poster.xml` 的 `Container.Content(seasons)` 分支改为 hero + 播放 + 季标签 + 本季集面板；原 deck 只在非季内容出现。
- 覆盖：首页导航、媒体库卡片、分类、搜索都落同一页（原生电视窗口的季视图）。
- 背景：详情页同一套（fanart `-120/-80`、`align=right`、stage mask、left scrim、`opacity_medium` 底部渐变）；View 51 的 deck 背景在季内容时关闭。
- 排序：原生季列表可能倒序，聚焦时强制 `Container.SetSortMethod(24)` + 升序。
- 播放键：`208` 播放 / `13362` 继续播放（不是 `1024` 浏览）；`PlayMedia(...,resume,tvshowtarget)`。
- 已知：季条目没有剧集总评分，技术标识取本季第一集；没有右侧四图标；标签最多 7 季；焦点在标签上按 OK 仍进该季集列表（Kodi 文件夹行为）。
- 实测：JSON-RPC 打开 5 季剧，右/左切季、下进集面板、上回标签/播放；无皮肤报错。

**共用随机背景（`a7898e5`）**

- 锁定 `nara.sharedrandomfanart.lockedpath` 指向的 Emby 图片已 404 → 设置页无随机图；清空后恢复。
- 插件信息 / 插件设置 / 添加文件源 / 文件浏览器各补隐藏 `16090`，无锁/无首页属性时自取一张；正常共享时不额外取图。
- 备份：`%TEMP%\skin.mistuary.settings.before-fanart-unlock.xml`。

**其他**

- `f9c2bfb` 侧边栏「横排」→「海报行」（胶囊固定 81，无几何改动）。
- `d1f8c75` 两张 1920×1080 季页预览图进 `docs/preview/`。
- `aa8a75b` 集卡片标题移到缩略图下方 + 聚焦滚动（随 2.1.0）。
- `5c6afbe` 最低 Helper 依赖 0.3.9；本轮 helper 已发布 0.3.11（0.3.10 搜索跳库 / 0.3.11 未同步剧集浏览）。
- 拼音排序排查：`SortTitle` 为拼音首字母（`RJZDSCS`），`videonavtvshows` 用 29；4 部仍是中文；Home/分类另有排序，首字母≠全拼。

### 8.17 2026-11-13 搜索页「输入」按钮：接上系统键盘（未发版）

**改动**

- `Includes_Search.xml`：输入框 group 让出右侧 104px，新增 `16997`「输入」按钮；`16998` / label / 两条下划线宽 904（五处成对改）。
- 按钮 `onclick` = `SetFocus(16999)` → `Action(Select)` → `SetFocus(16992)` 兜底。
- 2026-11-14：「输入」两个字换成全键盘图标（`media/icons/keyboard/keyboard.png`，48×30 LA，比原两字略高、同心；`16997` 的 label 留空，图标由紧随其后的两个 image 画，focus 时叠 `text_primary`）。`#31831` 随之从 zh/en 两个 po 删除（单测拦未引用串）。
- `strings.po` zh/en 各加 `#31831`（输入 / Text input）。
- `skin-contracts.md` §三补 16997/16998/16999 三行 + 系统键盘契约；§5.5 加第 7 个坑。

**为什么不是 SendClick**

`SendClick(16999)` 发的是 `GUI_MSG_CLICKED`，`CGUIButtonControl::OnMessage` 只处理 LABEL 类消息，不会转 `OnClick()`（Kodi 22 `GUIButtonControl.cpp`）。必须走 `OnAction` 的 `ACTION_SELECT_ITEM → OnClick()`。

**实机（Kodi 22.0-RC2，JSON-RPC + 截图验证）**

- 按钮 → 弹 `DialogKeyboard.xml`（窗口 10103，QWERTY + 空格 + 确定/取消）。
- `Input.SendText` 注入「诺兰」→ 回填 16999 → 约 4–7 秒后容器出结果；`Tom Hanks` / `NOLAN` 仍空（英文人名匹配待查，helper 侧）。
- 键盘标题固定「输入数值」：`m_inputHeading` 默认内置串 16028，皮肤 XML 无 `heading` / `inputtype` 标签。
- `Input.SendText` 是追加不是替换；`done=true` 不保证关对话框。
