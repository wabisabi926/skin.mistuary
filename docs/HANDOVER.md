# 交接说明（Mistuary 1.2.1）

> 读这个之前先读 `.workbuddy-ai/memory/MEMORY.md`（长期约定）。
> 本文只讲**现状、依赖、工具链、发版**，不讲历史。
> **新接手的三步**：① 本文 §8 看现状与待办 ② `docs/pending-work-plan.md` 看还剩什么
> ③ 要动音乐页或插件，读 `docs/vinyl-helper-plan.md`。

---

## 0. 三条铁律（每轮开工先看）

1. **不要擅自 `git commit` / `push` / 发版**。改完先说明改了什么 + 验证结果，等指令。
2. **改皮肤外观先给方案**（XML 结构、贴图、半径、布局），说清影响面 + 备选，
   等点头再动文件。只读排查（grep / 看图 / 读文档）不受限制。
3. **同步实机一律用散包**：`python tools/sync_to_kodi.py --loose`
   —— 跳过 `Textures.xbt` 并把它挪成 `.off`，改 png 只需重载皮肤（F5）即可生效。
   **只有用户明确说"打 tag / 发版"时才 `python tools/xbt_tool.py pack`。**
   打包会让用户必须完全重启 Kodi 才能看到新图，开发期极影响效率。
   ⚠️ 第一次切散包时 Kodi 正占用 `Textures.xbt`，挪不动 —— 让用户先完全退出 Kodi，
   再跑一次 `--loose` 即可。

---

## 1. 一句话现状

`main` 分支上的通用版皮肤，**Kodi 21 及以上**可用，版本 **1.2.1**
（2026-10-29 已发版，tag `v1.2.1`，CI 打包发布）。功能完整、静态自检全绿、工作区干净。
`Textures.xbt` **751 张 / 7.1 MB**（1.2.0 是 802 张 / 10.2 MB），单测 **58 项**。

> **本地还有 1 个未推送的提交**（`0ebccc5`：删 33 张死图 + 新增 `vinyl-helper-plan.md`），
> 见 §8.1。

### 2026-10-29 本轮改动（已随 1.2.0 发布）

| 主题 | 落点 |
|---|---|
| 主评分来源四档 + 手选优先 | 设置 707、`NaraOnlineRatingsRow`、`NaraDefaultRatingSourceVar`；Emby 补写 imdb 类型不再压过设置（§5.7） |
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
  **仍在暂存区外、未提交**（见 §8），交接到下一任前需要处理。
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
| `DialogMusicInfo` 专辑大图 | 570×570 | `mask_570x570_r12`（新增） | **未提交** |
| `View_55_WideList` 专辑图 / 横版图 | 340×340 / 438×246 | `mask_340x340_r12` / `mask_438x246_r12`（新增） | **未提交** |
| `View_50_List` 列表预览 | 224×300 / 160×160 / 184×184 | `mask_224x300_r12` / `mask_160x160_r9` / `mask_184x184_r9`（新增） | **未提交** |
| `Includes_VideoOSD` 播放列表缩略图 | 356×200 | `mask_356x200_r12`（新增） | **未提交** |
| `DialogAddonInfo` 插件信息截图 | 656×312 | `mask_656x312_r12`（新增） | **未提交** |
| `Includes_DialogVideoInfo_Cast` 演员头像 | 110×150 | `mask_110x150_r9`（新增） | **未提交** |

新遮罩都在 `tools/gen_corner_masks.py` 的 `DIFFUSE_MASKS` 表里登记过，且 `xbt_tool.py pack` 已重打包
（791 张）。`audit_skin.py --strict` 通过。

三条硬约束（§5.4.1 有完整说明）：
**① 遮罩尺寸必须和控件完全一致；② 环 = 卡片 +2、环外半径 = 遮罩半径 +1（内缘压进 2px）；
③ 海报下面的圆角底板（`round<N>.png`）半径不能小于遮罩半径，否则四角会从下面露出来。**

> 表里"目标遮罩"都沿用**当前半径**，即只换机制、不改观感 —— 迁移的目的是消掉
> "亮背景上四角露深色斑点"，半径统一是另一件事（见 §7 遗留）。

1.1.1 的重点是**影片技术标识图标化**：`media/techflags/color/` 存 97 张归一化图标
（`Includes_VideoTechnicalFlags.xml` 里 206 条 key → 图标的映射），
`tools/gen_techflag_icons.py` 负责生成（含冷门格式的白字标兜底）并维护 IconMap；
评分与技术标识合并成一行、整体移到简介下方。设计取舍与坐标见
`docs/techflag-icons-plan.md`，素材来源与许可见 README 的第三方声明段。

---

## 2. 运行时依赖

### 皮肤本体不需要任何 Python 脚本

`addon.xml` 只有一条依赖：

```xml
<import addon="xbmc.gui" version="5.17.0"/>
```

`tools/` 里的所有 `.py` / `.ps1` 都是**构建期工具**，不参与运行，也不进发布包。

### 皮肤会"探测"两个第三方插件，但都不是必需

| 插件 | 用在哪 | 没装会怎样 |
|---|---|---|
| `plugin.service.emby-next-gen` | 首页媒体库栏目、分类 widget 的显示条件 | 只是不显示那几行，其余正常 |
| `script.embuary.info` | 演员头像点击查人 | 点击无反应 |
| `script.mistuary.helper`（规划中） | 服务端搜索、豆瓣评分、剧集代表集标识 | 回退本地 XSP / 不显示豆瓣胶囊 |

都用 `System.AddonIsEnabled()` / `System.HasAddon()` 保护，**没有硬依赖**。
`script.mistuary.helper` 是**独立仓库**，契约与阶段规划见
[`helper-plugin-plan.md`](helper-plugin-plan.md)；**不要塞进皮肤包**
（Kodi 不允许 skin addon 携带可执行脚本）。

---

## 3. 仓库结构

### 会进发布包的

```
addon.xml  changelog.txt  README.md
LICENSE        GNU GPL v2 全文（代码部分；GitHub 靠它识别许可）
xml/            全部窗口与 include
colors/         defaults.xml（透黑）/ light.xml（透白，只写差异色）
fonts/          Inter-Unicode-Regular.ttf（自带 CJK，见 §5.1）
language/       resource.language.*/strings.po
media/          松散图片 + Textures.xbt（打包后只带 xbt）
extras/         随包素材，运行时用 special://skin/extras/... 引用
  backgrounds/    运行时背景图（primary.jpg）
  playlists/      widget 用的播放列表（*.xsp）
libraryart/     分类封面（按「分类名.jpg」匹配；2026-10-28 起随包发布，24 张封面 + default.jpg，约 1.4MB）
```

> `extras/` 这个名字是 Arctic 系皮肤的约定（jurialmunkey / narapeka 一脉）：
> **随包发布的素材**放这里，图片不进 `Textures.xbt`，是松散文件，用户可以直接替换。
> 不要把它和构建工具混在一起——构建工具在 `tools/`。

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

## 4. 开发工具（`tools/`）

### 必跑的三条

```bash
python tools/audit_skin.py          # 静态自检：缺失 include/变量/字体/贴图/字符串、浮窗遮蔽、设置读写配对
python tools/audit_skin.py --orphans        # 反向：盘上有、XML 里没人引用的贴图
python tools/audit_skin.py --dead           # 反向：定义了、没人用的变量 / include
python tools/gen_techflag_vars.py --check   # 技术标识变量是否与 map 同步
python -m unittest discover -s tools -p 'test_*.py'   # 单元测试
```

`--orphans` / `--dead` 是**报告模式，永远返回 0**（不进 CI 闸门）——它们只能按字面匹配，
动态引用（`$PARAM[...]` 传值、变量套变量）需要人工确认，所以不当作硬错误。
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

### 5.2 Kodi 21 兼容：双轨渲染

`addon.xml` 声明 `xbmc.gui 5.17.0`（= Kodi 21）。22 才有的能力靠双轨：
- `$MAP[]` / `<map>`（21 会原样显示表达式）
- 13 个新标签（`ListItem.HdrDetail` 等）21 上为空，被 `!String.IsEmpty` 保护

判据：`System.BuildVersion` 以 `21` 开头 → `$EXP[nara_kodi21]`。
OSD 的技术标识走生成的 `$VAR[NaraTechHdrPlayer]` / `NaraTechAudioPlayer`。

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

链路：三个设置共用同一套 `gl_1..6`；**遮蔽 `sc_1..6` 只跟页面档**（遮蔽干的是"把页面压暗"，
属于页面，不属于浮窗）。

| 变量 | 来源 | 用在哪 |
|---|---|---|
| `NaraGlassPageTintVar` | 页面档 | 全屏页面面板、页面内卡片、顶部导航条、设置中心/设置侧栏 |
| `NaraGlassFloatTintVar` | 浮窗档 | 对话框、插件详情/设置、菜单、键盘、非播放时的设置选择框 |
| `NaraPlaybackDialogTintVar` | 播放中档 | 播放 OSD 全系 + 播放控制条 |
| `NaraSettingsDialogTintVar` | 播放中档 / 浮窗档（按是否播放切换） | 视频/音乐 OSD 设置、播放中的设置选择框 |
| `NaraGlassScrimTintVar` | 页面档 | 所有遮蔽层（播放中改走 `scrim_osd`） |

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
1. **行级** `Control.HasFocus(<行 id>)` —— 25 个设置行各一条，先写
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
| 常规 | 702 / 710 / 705 / 706 | 31736 / 31737 / 31738 / 31739 | 自动滚动 / 封面文件夹 / 媒体标识 / 显示哪个评分 |
| 常规 | 707 / 708 / 711 / 712 / 713 | 31740 / 31741 / 31742 / 31761 / 31743 | 主评分来源 / 标题格式 / 页面透明度 / 弹窗透明度 / 播放中透明度 |
| 艺术图片 | 605 / 6067 | 31744 / 31745 | 背景图当背景 / 音乐电视海报 |
| 主菜单项 | 611 / 6111 / 627 | 31746 / 31747 / 31748 | 电影 / 编辑小组件 / 系列打开方式 |
| 主菜单项 | 612 / 6121 / 626 | 31749 / 31750 / 31751 | 电视剧 / 编辑小组件 / 打开方式 |
| 主菜单项 | 613 / 6132 / 625 | 31752 / 31753 / 31754 | 音乐 / 编辑小组件 / 专辑打开方式 |
| 主菜单项 | 618 / 6181 | 31755 / 31756 | 电视 / 编辑小组件 |
| 屏幕菜单式调节 | 623 / 624 | 31757 / 31758 | 自动关闭 OSD / 关闭时间 |

### 5.3.2 设置页的分类（2026-10-29 重排）

4 个分类，名字对齐 Kodi 自己的词汇（不用自造词，也不要用 Kodi 那句机翻的
「屏幕菜单式调节」）：

| 分类 | 侧栏 id | grouplist | 行数 | 内容 |
|---|---|---|---|---|
| **首页** | 1 | `700` | 11 | 主菜单 4 个开关 + 4 个编辑小组件 + 3 个默认打开方式 |
| **媒体** | 2 | `610` | 7 | 封面文件夹、媒体标识、技术标识用图标、显示哪个评分、主评分来源、标题格式、音乐电视海报 |
| **界面** | 3 | `600` | 5 | 页面 / 弹窗 / 播放中透明度、媒体背景图、剧情评论自动滚动 |
| **播放** | 4 | `622` | 2 | OSD 自动关闭、OSD 自动关闭时间 |

**改分类时只换 grouplist 的子项，别动 grouplist 本身** —— `onup`/`ondown` 的跳转链
和 4 个分类一一对应，保持 4 个 grouplist 就不用重连导航。这也是当初从 5 类改回 4 类的
实质原因（不只是命名）。

- `700` 有 11 行，装不下，必须有 `<pagecontrol>60</pagecontrol>`。
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
| **≥ 200** | **r12** | 海报墙/信息墙 244、搜索&横排卡 214、封面 420/378、Shift 334、详情页&横排大图 452、宽列表 438×366 / 340² / 438×246、列表预览 224×300、OSD 播放列表 356×200、插件信息截图 656×312、音乐专辑 570² / **音乐播放页封面 450²**、**视频管理器海报 400×630**、**播放控制条 250²**、**书签缩略图 330×250**、**文件浏览预览 260×380**、**播放中 seek 封面 200²** |
| **< 200** | **r9** | 首页横版 320×180、专辑 186²、宽列表缩略图 160²、列表预览 160²/184²、剧集缩略图 336×189、首页类别卡 276×160、演员头像 110×150、**列表行小缩略图 110²**、**音乐信息专辑 190²**、**用户配置头像 162²**、**图标墙缩略图 160×116** |
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

### 5.5 四个反复踩过的坑

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

### 5.6 排查顺序

某窗口不跟设置走时：① grep 写死的 `AARRGGBB` 板 → ② grep `<include condition=`
→ ③ 最后才查 `$VAR` / `$PARAM`。
"面板/底色不对"先把它刷成荧光色，一眼看它到底在不在 —— 比连改三轮快得多。

---

### 5.7 评分：按类型读，别自己造标签

Kodi 20+ 的视频信息标签支持**多个带类型的评分**：

| 写法 | 含义 |
|---|---|
| `ListItem.Rating` | 默认类型（`m_strDefaultRating`） |
| `ListItem.Rating(imdb)` / `(tmdb)` / `(tomatometerallcritics)` | 指定类型的评分 |
| `ListItem.Votes(<type>)` / `ListItem.RatingAndVotes(<type>)` | 同类型的票数 |

`CVideoInfoTag::SetRating` 会**丢弃 0 和 >10 的值**，所以 0-100 的分数必须先换算。

**能直接拿到的评分类型，只有下面这些**（2026-10-27 按已安装插件源码逐条核对）：

| 数据源 | 类型名 | 来源字段 | 范围 |
|---|---|---|---|
| Emby | `default`（`ListItem.Rating`） | `CommunityRating` | 电影 / 剧集 / 单集 / 音乐视频 |
| Emby | `tomatometerallcritics` | `CriticRating / 10` | **只有电影**（`movies.py` / `videos.py`） |
| Kodi 官方 TMDb 刮削器 | **`themoviedb`** | `vote_average` | 电影（`tmdb.py:140`） |
| Kodi 官方 TMDb 刮削器 | **`tmdb`** | `vote_average` | 剧集 / 季 / 单集（剧集刮削器） |
| Kodi 官方 TMDb 刮削器 | `imdb` | IMDb 网站 | 需把刮削器「评分来源」设为 IMDb，或勾「总是获取 IMDb 评分」 |
| Kodi 官方 TMDb 刮削器 | `trakt` | Trakt | 需登录 + 勾选 |

**两个坑**：

1. **电影和剧集的 TMDB 类型名不一样** —— 电影写 `themoviedb`、剧集写 `tmdb`（两个刮削器各写各的）。
   只读其中一个会漏一半。皮肤两个都读，标签直接拼接（同一条目只会命中一个）。
2. Emby **不写** `imdb` / `tmdb` / `metacritic` 类型，`UserRating` 也不写
   （个人评分圆标显示的是 Kodi 自己的 `SetRating` 星标，与影评人分无关）。

Emby for Kodi（`plugin.service.emby-next-gen`）的写入点：`core/movies.py:91-92`，
`videos.py` / `episode.py` / `series.py` / `musicvideo.py` 同构，都只有 `default` 一行
（`videos.py` / `movies.py` 多一行 `tomatometerallcritics`）。

因此 Emby 库下：电影最多 2 颗胶囊（默认 + 烂番茄），剧集/单集只有 1 颗。

**豆瓣覆盖**：StrmAssistant（神医助手）的「豆瓣评分覆盖」会把 Emby 的 `CommunityRating`
改写成豆瓣分，同步到 Kodi 后仍是 `default` 类型——Kodi 侧**没有任何来源标志**，
无法自动判断是豆瓣还是 IMDb。皮肤用设置 707「主评分来源」（自动 / TMDb / IMDb / 豆瓣）
只切换第一颗胶囊的图标，数值都读 `ListItem.Rating`。

**手选优先，自动识别只在「自动」档生效**（2026-10-28 修正）。原因：Emby 插件
（`plugin.service.emby-next-gen` 的 `Set imdb as default rating provider`，默认开）
会把 `CommunityRating` 补写成 **imdb 类型**的评分，`Rating(imdb)` 恒等于 `Rating`。
自动识别若排在前面，有类型字段的条目永远命中 IMDb，设置 707 就完全失效（实测现象：
怎么切都显示 IMDb）。用户指定来源后只按档位画图标；「自动」= 三档手动设置全假，
随时可以切回去。

**一行最多两个胶囊**：主评分是同一个字段、由 707 四档互斥决定，所以"最多两个"
退化成一条规则——**烂番茄给 TMDB 让位**（TMDB 有值时烂番茄隐藏）。
优先顺序：豆瓣 > IMDb > TMDb；「自动」时按 TMDb → Trakt → IMDb 识别，最后默认 TMDb。

取不到的类型返回空字符串，所以"多列几种类型 + 用 `!String.IsEmpty` 控制可见"是安全的写法。
**不要自己发明标签名**（`ListItem.NaraRating(x)` 这类是魔改内核的，官方 Kodi 恒空）。

**TMDbHelper 的豆瓣分进不来**：它写在 list item 的 infoproperties（`douban_rating`），
而且要 URL 带 `?ratings=true` 才查，只存在于 TMDbHelper 自己生成的列表里。
皮肤没有用 TMDbHelper 的任何路径，所以详情页读不到。接入方式（`script.mistuary.helper`
调豆瓣双通道、写 `Window.Property(Mistuary.Rating.*)`）见
[`helper-plugin-plan.md`](helper-plugin-plan.md) §5.2。

### 5.8 音乐播放页：歌词 / 评分 / 背景

- **歌词**：OSD 有「歌词」按钮，播放入口是歌词插件（默认 `script.cu.lrclyrics`）。
  皮肤用 `xml/script-cu-lrclyrics-main.xml` 覆盖插件窗口，列表固定在屏幕右侧、
  无全屏遮罩；播放页 `onload` 自动启动、`onunload` 关闭。
  插件的取词顺序是「内嵌 → 同名 .lrc → 在线源」，本地有词就不会联网。
- **评分**：OSD 有「我的评分」按钮（`SetRating`，写 Kodi 用户评分）。
- **背景**：默认图是 `media/osd/nara/music-background.jpg`（进 XBT）；
  用户可在「设置 → 外观 → 音乐背景」换图，变量
  `NaraImgSkinStringNaraMusicBackgroundDefMusicBackground` 统一给播放页和音乐信息页兜底。
- **豆瓣**：StrmAssistant 的豆瓣覆盖改写的是 Emby `CommunityRating`（Kodi 侧为默认类型，
  无来源标志），皮肤用设置项 `douban_rating` 手动切换第一颗评分胶囊的图标（IMDb / Douban）。

### 5.9 海报墙的列宽预算（2026-10-28 实测）

海报墙（`View_500_Wall` / `View_54_InfoWall`）的卡片格 = 海报 + 左右空档：

| | 值 | 说明 |
|---|---|---|
| 海报 | 244×352 | 从 1.1.0 起没变过 |
| 卡片格 | **264**（原 260） | 空档 = 264 − 244 = **20px**（原 16） |
| 行高 | 430 | 海报 `top` 18（Wall 是 10） |

**为什么不能随便加**：面板是 `width=98%`，1920 逻辑宽下只有 **1881px**。
7 列 × 264 = 1848，余 33px。**卡片格超过 268 就会掉成 6 列**
（7×268 = 1876，只剩 5px，取整就会翻车）。要更大的缝只能缩海报，见下。

**4K 不用单独考虑**：`addon.xml` 声明了 8 组 `<res>`，但全部 `folder="xml"`（同一套 XML）。
Kodi 按当前宽高比选一组逻辑坐标渲染，4K 16:9 走的就是 1920×1080 那组、放大 2 倍输出。
1920 下不溢出，4K / 16:10 / 4:3 都不会溢出。

**想把海报本身改小**（比如 236×340 + 缝 24）的连带成本，别低估：
① 要新生成 `mask_236x340_r19`、`ring_card_238x342_r20`；② 改 focus 参数与 caption 位置；
③ **`Custom_1111_MovieSetDialog` 里那套「111.11% / 120.37% 缩放对应 240×360 真实海报」
的补偿数必须重算**，否则合集弹窗的焦点框会错位。

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
  人员与类型搜索归服务端桥（[`helper-plugin-plan.md`](helper-plugin-plan.md) §6）。
- **首字母必须前缀匹配**：`contains` 会把首字母出现在词中的条目捞进来
  （`HZ` 命中 14 部 → 前缀只剩 4 部）。2026-10-28 已改 `startswith`。
- **不要给结果列表加 `limit`**：`<content limit="30">` 会同时截断结果和标签计数。
  2026-10-28 已移除。
- **覆盖不到**：分集（Kodi 22 没有全局 `videodb://episodes/` 节点，皮肤层拿不到）、
  合集（22 个，可用 `videodb://movies/sets/` 单独做页签）、Emby 索引里尚未同步到
  Kodi 库的条目（当时差 6 部电影 / 131 集）。

## 6. 发版流程

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

---

## 7. 已知遗留

| 项 | 说明 |
|---|---|
| 圆角半径两档制 | 短边 ≥200 → r12、<200 → r9（见 §5.4.1）。改任何一档都要连带改遮罩、焦点环、底板 `round<N>`、细边 `edge_*` 四样 |
| addon 简介措辞 | ✅ 2026-10-28 已补：中英两条 description 都写了「（同时最多两个）」/「(up to two at a time)」，随 1.2.0 发 |
| 系统信息 / 事件日志的底部文字区 | 这两页底部**故意**和 PVR 不一样：`SettingsSystemInfo` 没有"当前项"，底部 y 555–885 被内存/CPU 浮层占用，所以不挂帮助条；`EventLog` 用 `label id=70`（915, h40）+ `textbox id=71`（955, h60）拼成两行，合起来仍占 915–1015 那 100px。**如果希望三页底部完全一致，需要先决定这两页要不要让出那块区域** |
| `SettingsSystemInfo` 滚动条轨道 | ✅ 2026-10-29 已改：`id=60` 轨道 644 → **357**（它服务的是 `textbox id=30`，193→550 高 357；写 644 会让滑块按两屏算比例）。几何回归测试已按页取期望值 |
| 首页「类别」行的名字 | 显示的是 Emby 插件节点名（`EMBY DYNAMIC: 音乐 (music)`），皮肤层无法截断字符串。要么在 Emby 里改库名，要么补 `libraryart/<新名字>.jpg` |
| 本地搜索不含人员/类型 | 1.2.0 起快速搜索只匹配 `title` / `originaltitle` / `sorttitle` 前缀；演员、导演、类型等服务端桥（§8.9）。**已拍板，不要加回来** |
| 类别行 / 专辑行左边缘 | 差 18px（60 vs 78），用户明确说"不用统一" |
| 专辑卡片长标题 | 卡宽 186，font12 只放得下 8 个汉字；超长靠聚焦时滚动 |
| `tools/universalize.py` | 4.2.0 → 1.0.0 的一次性迁移脚本，已完成使命，留作参考 |

> **已修（2026-10-27）**：`ListItem.BMP` → `ListItem.BPM`（BPM 徽标现在能显示了）；
> `ListItem.MusicBitsPerSample` 那条删掉了 —— Kodi 没有列表项位深标签，
> 位深只有播放器上下文的 `Player.Process(AudioBitsPerSample)`。
> 当时的判据是拿 Kodi 21.2 与 master 的 `xbmc/GUIInfoManager.cpp` 标签名总表逐条比对
> `$INFO[...]`。**排查同类问题的方法**：把皮肤里所有 `$INFO[X]` 的 X 取出来，
> 去掉 `(...)` 参数和 `$PARAM[...]` 前缀，取最后一段，与标签表求差集。

---

## 8. 交接前状态（2026-10-29）

### 8.1 当前 git 状态

**这里不钉 commit hash 和"领先几个提交"** —— 那种快照提交完就过时（踩过：刚写完就又不准）。
要现状直接跑：

```bash
git log -1 --oneline        # HEAD
git status -sb              # 与远端的关系 + 工作区
```

稳定的只有这几项：

| 项 | 值 |
|---|---|
| 版本 | `addon.xml` = 1.2.1，`v1.2.1` 已发版 |
| 贴图 | `Textures.xbt` 754 张 / 7.3 MB；`media/` 松散 PNG 753 张（+1 张 jpg） |

> 要发新版才升 `addon.xml`（§6）。

### 8.2 发版记录

| 版本 | 要点 |
|---|---|
| v1.0.0 / v1.1.0 / v1.1.1 | 通用版落地、透明度三档、技术标识图标化 |
| **v1.2.0** | 真圆角（diffuse 遮罩）+ 播放条重排 + 搜索增强 + 主评分四档 |
| **v1.2.1** | 包体 10.2 → 7.2 MB（清死图）+ 系统信息页滚动条 |

> **1.2.0 卡过一次**：升版本号后 CI 的 `test` job 因 `xbt_tool` 缺 Pillow 失败，
> 当时只修了 CI 没再升版本 → 工作流判定「版本号未变化」跳过，Release 一直没生成。
> 后来 `5020f1f` 把版本号退回 1.1.1、再重新升到 1.2.0 才发出去。
> **教训**：CI 失败后要重发**同版本**，走 `workflow_dispatch` + `force=true`。

### 8.3 最近两天做过什么（免得重做）

| 主题 | 落点 |
|---|---|
| 主评分来源四档 + 手选优先 | 设置 707、`NaraOnlineRatingsRow`、`NaraDefaultRatingSourceVar`（§5.7） |
| 搜索首字母改前缀匹配 | `sorttitle` 用 `startswith`，并**移除** `actor` / `director` / `genre`（§5.10） |
| 帮助文案统一 | 「弹窗透明度」、26 条帮助条改陈述式、双引号 |
| 圆角二期 | 全库收口，30 张 diffuse 遮罩、8 环 + 1 细边（§5.4.1） |
| 死资源清理 | 22 + 33 张零引用贴图删除，包体 −29%（`d29a225` / `0ebccc5`） |
| 自检补反向检查 | `audit_skin.py --orphans` / `--dead`（§4） |
| 插件规划 | `docs/helper-plugin-plan.md`，含「可选安装」契约 §3.1 |
| 黑胶唱片模式 | OSD 最右按钮切换，素材 `tools/gen_vinyl.py`（§8.9 之后的新条目） |
| 死代码清零 | 21 死变量 + 6 死 include；`--dead` 现在 0/0 |
| 设置页重排 | 4 类：首页 11 / 媒体 7 / 界面 5 / 播放 2（§5.3.2） |

### 8.4 现在可以直接接着做的四件事

| # | 事项 | 材料在哪 | 需要什么 |
|---|---|---|---|
| 1 | **音乐播放页黑胶唱片效果** | `docs/vinyl-helper-plan.md` §2（含动画写法、素材清单、**暂停回弹这个硬伤**） | 用户先认可硬伤 |
| 2 | **`script.mistuary.helper` 阶段 0 + 1** | `docs/helper-plugin-plan.md` + `vinyl-helper-plan.md` §3（骨架清单） | 定仓库位置 / token 来源 / 播放地址形态 |
| 3 | **删 24 个死变量 + 6 个死 include** | `audit_skin.py --dead` 直接列出来 | 逐个确认（`HomeVideoRowNavigation` 是活的，别删） |
| 4 | 背景兜底图 | `vinyl-helper-plan.md` §1 | 用户选 A/B/C（建议 A 不动） |

### 8.5 新接手先跑这五条

```bash
python tools/audit_skin.py --strict                      # 必须 EXIT=0
python tools/audit_skin.py --orphans                     # 应报 0 张
python tools/audit_skin.py --dead                        # 24 变量 + 6 include（已知，未清）
python -m unittest discover -s tools -p 'test_*.py'       # 58 项
python tools/gen_corner_masks.py --check && python tools/gen_rings.py --check   && python tools/gen_glass_plates.py --check && python tools/gen_techflag_vars.py --check
```

### 8.6 待决策（4 项，都要用户点头）

1. **黑胶的暂停回弹**：Kodi 条件动画条件消失会 reset，唱片"啪"回 0°。接受还是不做？
2. **helper 仓库位置**：`D:/下载/AI/script.mistuary.helper/`（独立仓库）可以吗？
3. **helper 的 Emby token**：读 Emby 插件配置，还是让用户在插件设置里填？
4. **背景兜底**：A 不动 / B 换图 / C 按主题两张。

### 8.7 从没验证过的

**Kodi 21 实机**：双轨渲染（`$MAP` 在 21 上退化成原始值、13 个 v22 标签靠
`!String.IsEmpty` 保护）**只在 22.0-BETA2 上跑过**。装 Kodi 21.2 便携版
（解压即用、不动现有配置）→ 皮肤拷进 `portable_data/addons/` → 看四处：
技术标识不出现 `$MAP[...]` 原文、详情页评分、字幕/音轨标签、PVR 台标回退。**风险 0。**

### 8.8 给下一任的提醒

- **提交纪律**（§4）：永远 `git add <具体文件>`、`git diff --cached --name-only` 核对再 commit。
  这个仓库可能多个 agent 并行改，工作区里随时有别人的未提交改动，别一把扫进自己的提交。
- **开发期同步实机用散包**：`python tools/sync_to_kodi.py --loose`（改 png 只重载皮肤就生效）；
  **递交 / 发版前**才 `python tools/xbt_tool.py pack` + 普通 `sync_to_kodi.py`。
  ⚠️ `--loose` 要把目标端 `Textures.xbt` 挪成 `.off`，**Kodi 开着时挪不动**，会只同步散文件。
- **版本号没升 = 没发版**：push 会触发发版，"提交"和"发版"要分开确认（§6）。
- 圆角机制只有一条正确路子：`<texture diffuse="shapes/mask_<w>x<h>_r<N>.png">` + 遮罩尺寸与控件一致
  （§5.4.1）；`scale` 才写 `scalediffuse="false"`，`keep` **不要写**（写了等于没圆角）。
- **不要擅自 commit / push / 发版**：改完先说明什么 + 验证结果，等指令。同步到实机也一样，先问。

### 8.9 下一步：`script.mistuary.helper`（独立仓库）

规划、契约、阶段验收全在 [`helper-plugin-plan.md`](helper-plugin-plan.md)，
骨架清单与三个待定项在 [`vinyl-helper-plan.md`](vinyl-helper-plan.md) §3。要点：

- **定位**：皮肤的运行时脚本能力都进这一个插件（不要再建第二个 `script.mistuary.*`）。
  独立仓库、GPL-3.0、只用标准库。
- **可选安装（2026-10-29 定）**：**不装就少功能，装了就多**。`addon.xml` **不写** `<import>`，
  只用 `System.AddonIsEnabled` 软探测；缺插件时搜索回退本地 XSP、豆瓣胶囊隐藏、
  代表集走皮肤自己的推断。降级表与四条硬约束见 `helper-plugin-plan.md` §3.1。
  ⚠️ 装/卸插件后要**重载皮肤**才生效（`<include condition>` 与 `<content>` 是加载时求值）。
- **P0 服务端搜索**：调 Emby `/Items?searchTerm=`（中文分词/全拼只在服务端生效）。
- **P1 豆瓣评分**、**P2 代表集标识** 见规划文档。

> ⚠️ 行为变化：1.2.0 起本地快速搜索不再匹配演员 / 导演 / 类型（见 §5.10），
> 人员搜索要等服务端桥补回来。**交接时别当成 bug 又加回去。**
