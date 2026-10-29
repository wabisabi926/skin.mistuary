# 最终优化方案（2026-10-29）

> 基线：`main` = `d29a225`（清理已提交），v1.2.0 已发布。**第 1 批清理已完成**，剩下的事见第八节。
> 这份是「文档 + 代码」全量复查的结论，分两块：**清理**（第 1–4 节）和**优化**（第 5–8 节）。
> 每条都给**实测证据**；凡是我一开始判错、后来自己纠正的，都标了「⚠️ 别照做」。

---

# 一、清理：死资源

## 1.1　`media/settings/background.png` —— 1.87 MB，全皮肤零引用 ✅ 已删

| | |
|---|---|
| 证据 | 1672×941、**1,912,199 B**；`grep -r 'settings/background' xml/ tools/` → 0 命中；但确实在 `Textures.xbt` 里 |
| 性质 | 4.x 时代设置页的背景图，改版后没人用 |
| 收益 | `Textures.xbt` 10.2 MB → **7.2 MB**（实测 −29%，2026-10-29 已执行） |

```bash
git rm media/settings/background.png && python tools/xbt_tool.py pack
```

**别顺手删 `media/settings/` 里别的**：那 15 张图标走 `settings/$PARAM[icon].png`
（`Includes_Settings.xml:235`），按文件名 grep 全是"未引用"的假阳性。

## 1.2　死贴图 ✅ 已删 21 张（`osd/nara/*_filled` 4 张留着待定）

| 位置 | 文件 | 判定依据 |
|---|---|---|
| `shapes/` | `glass16` `18` `28` `32` `42` | `shapes/glass$PARAM[radius].png` 是动态的，但 `NaraDialogGlassTexture` 的 `radius` 默认 **20**、**没有任何调用方覆盖** |
| `shapes/` | `round42` `round65` | 无字面引用（也没有 `shapes/round$` 这种动态写法） |
| `shapes/` | `ring12_3` | 早期 9-slice 环，已被 1:1 整图取代 |
| `shapes/` | `ring_btn_120x70_r35` `ring_card_250x358_r14` | 无引用 |
| `shapes/` | `ring_card_206x206_r12` `227x227_r12` `227x276_r6` `235x235_r6` `243x243_r6` `259x315_r6` `275x331_r11` | 生成出来但从没接上 |
| `osd/nara/` | `play_filled` `pause_filled` `next_filled` `previous_filled` | `gen_osd_filled_icons.py` 生成，XML 零引用 |
| `osd/nara/` | `metadata.png` `video.png` | 无引用 |
| `icons/` | `filemanager.png` `power.png` | 无引用（设置中心用的是 `settings/` 下同名文件） |

**做法**：删文件 → 同步改三张表（`gen_glass_plates.py` 只留 20、`gen_rings.py` 删 9 条、
`gen_osd_filled_icons.py` 删 4 条）→ `--check` 必须过 → `pack`。

**前置确认**：`osd/nara/*_filled` 如果是"实心/空心两态按钮"的备用素材，那就补引用而不是删。

---

# 二、清理：死代码（XML）

## 2.1　24 个没人引用的变量

```
AddonLifecycleType            BannerVar                     ContainerResolutionFlagVar
FocusLayoutTextColor21Var     FocusLayoutTextColor5000Var   ListSubLabelVar
MasterModeLabel               MovieSetOnClickActionVar      NaraProcessHDRTypeVar
NaraTechDvPlayer              NaraTechResolutionPlayer      NaraTechVideoPlayer
NowPlayingIconVar             OSDHelpTextVar                PlayerControlsPlayImageVar
PlotTextBoxVar                PremieredLabel                ResolutionFlagVar
SubtitleStreamDescriptionVar  VideoHWDecoder                VideoInfoMainLabelVar
VideoInfoSubLabelVar          WidgetPlaylistIconVar         WidgetStudioIconVar
```

全部集中在 `Variables.xml`，仓库里除定义外零出现（`xml/` `language/` `tools/` `docs/` 都查过）。

**其中 3 个是生成器产出的**：`NaraTechResolutionPlayer` / `NaraTechDvPlayer` /
`NaraTechVideoPlayer`。`gen_techflag_vars.py` 按 5 张 map 生成 5 个变量，
但 `Includes_VideoOSD.xml` 只用了 `NaraTechHdrPlayer` 和 `NaraTechAudioPlayer`。
→ 二选一：**把生成器的 map 列表砍到 2 个**（推荐），或 OSD 补上分辨率/编码显示（改观感）。

> ⚠️ **别照我第一版的 39 个删**。第一版正则漏了两种写法，多判了 15 个：
> `$ESCVAR[VideoInfoPlotVar]`（`$ESC` 前缀）和 `$VAR[StreamHDRTypeVar, | ]`（带格式参数）。
> 正确正则：`\$(?:ESC)?VAR\[([^,\]]+)`。

## 2.2　6 个没人引用的 include

`Animation_ActionFocusFade`（Includes_Animations）、`NaraAddonInfoGlassBackground`、
`NaraMusicOSDButtonGlass`、`PlaylistWindowButton`、`RDSInfoLine`、
`NaraDialogSolidSurface`（只在 `Includes.xml:912` 的**注释**里出现）。

> ⚠️ `HomeVideoRowNavigation` **不能删**：它经 `<param name="navigation" value="HomeVideoRowNavigation"/>`
> → `$PARAM[navigation]` 动态引用，Home.xml 里有 17 处。按名字 grep 只有定义处，很容易误判。

## 2.3　语言文件：**没有死字符串**（0 条）

239 条皮肤自有串（31000–31999）**全部有引用**。判定时容易踩两个坑：

- `<viewtype label="31100">` —— **裸数字**，不是 `$LOCALIZE[31100]`
- `Skin.SelectBool(31733, 31767|rating_src_auto, 31764|rating_src_tmdb, ...)` ——
  选项标签也是**裸数字**

按"任意位置出现这个数字"判定，死串 0 条。**语言文件不用清理**，别白费劲。

---

# 三、清理：工具与临时文件

| 项 | 现状 | 建议 |
|---|---|---|
| `docs/scratch/` | **17 MB / 62 个文件**（59 png + 1 svg + 1 xbt + README） | 清空前先做 3.1 |
| `tools/universalize.py` | 4.2.0 → 1.0.0 的一次性迁移脚本 | 删（git 历史里还有） |
| `tools/preview.html` | 8 KB，早期配色预览 | 删或留，看你还用不用 |
| `tools/music-cover-original.png` | **756 KB** 源图，`gen_music_cover.py` 的输入 | **保留**（删了封面就没法重新生成） |
| `tools/osd_icons/*.svg` | 7 KB，OSD 图标矢量源 | 保留（生成器要用） |
| `tools/test_nara_*.ps1` | 4 个 PowerShell 手动 UI 测试 | 保留，但没进 CI，属于"要人跑"的 |

## 3.1　⚠️ `docs/scratch/` 里有 7 处文档引用，文件**已经全丢了**

| 文档 | 引用 | 实际 |
|---|---|---|
| `techflag-icon-coverage.md:5` | `python docs/scratch/icon_coverage.py` | **脚本不存在** |
| `techflag-icon-coverage.md:66` | `docs/scratch/drawn-sample.png` | **不存在** |
| `techflag-icons-plan.md:322` | `docs/scratch/pill-color-compare.png` | **不存在** |
| `techflag-icons-plan.md:323` | `docs/scratch/layout-final.png` | **不存在** |
| `techflag-icons-plan.md:360` | `docs/scratch/layout-merged-below.png` | **不存在** |
| `rounded-corners-phase2.md:3` | `docs/scratch/scan_rounded.py` | 脚本已转正为 **`tools/scan_rounded.py`**，路径要改 |

**做法**：清 scratch **之前**先处理这 7 处——要么改成 `tools/` 下的正式路径，
要么删掉"复现/样张"这两句（图已经没了，留着是死链）。
`icon_coverage.py` 建议**重写进 `tools/`**（它算的是 109 个取值的图标覆盖，是个有用的检查）。

---

# 四、清理：文档失真（全部实测过）

| 位置 | 写的 | 实际 |
|---|---|---|
| `docs/README.md:12` | techflags「**96 张**图标」 | **97 张**（audio 50 / hdr 6 / resolution 7 / video 34） |
| `docs/README.md:33` | 透明度「21 处页面 / **25 处浮窗** / **29 处播放中**」 | 21 / **18** / **17**，另有 `NaraSettingsDialogTintVar` **15**、`NaraGlassScrimTintVar` **16** |
| `docs/README.md` 自检块 | 单测「**46 项**」，缺 `gen_rings` / `scan_rounded` | **58 项** |
| `docs/skin-contracts.md:277` | 单测「**42 项**全绿」 | **58 项** |
| `docs/HANDOVER.md:644` | HEAD `efea1ff` | `f71a891`（v1.2.0 之后又推了 1 个文档提交） |
| `docs/HANDOVER.md` §4 工具表 | 没有 `scan_rounded.py` | 它在 §8.3 被提到，但工具表漏了 |
| `addon.xml:31` | `<disclaimer lang="zh_CN">本皮肤有意省略天气、电台和游戏浏览界面；` | 结尾是**分号**，应是句号 |
| `addon.xml:19` | `<forum>http://forum.kodi.tv/</forum>` | 指向论坛首页，不是皮肤帖 |

---

# 五、优化：给自检加两条"反向检查"

现在 `audit_skin.py` 只查**正向**（引用了但文件不存在）。反向（定义了没人用）全靠人肉，
所以 1.87 MB 的死图藏了半个月。

## 5.1　`--orphans`：死贴图

规则（必须按这个顺序，否则全是假阳性）：

1. 收集 XML 里所有贴图路径字符串
2. 识别**动态前缀**并豁免整个目录/族：
   `techflags/color/$PARAM[icon].png`、`settings/$PARAM[icon].png`、
   `shapes/glass$PARAM[radius].png`、`$INFO[ListItem.Thumb,windows/subtitles/flags/,.png]`、
   `dialogs/volume/progress/p<N>.png`、`genres/<名>.png`、`Default*.png`（Kodi 默认图标）
3. 剩下报"疑似未引用"，**默认只提示、不返回非 0**（人工确认后加白名单）

## 5.2　`--dead`：死变量 / 死 include

- 变量：`\$(?:ESC)?VAR\[([^,\]]+)`（**两个坑都在这里**：`$ESC` 前缀、格式参数）
- include：`content="X"` + `<include[^>]*>X</include>` + **`$PARAM[...]` 间接引用**（最容易漏）

## 5.3　CI 补两条 `--check`

`release.yml` 的 test job 现在跑：单测 / `audit --strict` / `gen_techflag_vars --check` /
`gen_techflag_icons --check`。**缺 `gen_corner_masks --check` 和 `gen_rings --check`** ——
生成器表和盘上文件漂移时抓不到（`audit` 只查"XML 引用的贴图在不在"，
不查"表里登记的到底生成没有"）。

---

# 六、优化：`gen_techflag_vars.py` 只生成用得到的

见 2.1：5 个变量只用 2 个。砍掉 3 个能少约 100 条 `<value>`。**纯收益**，
但 `--check` 的标记区间要一起改。

---

# 七、功能待办（继承，非清理）

| 项 | 状态 | 说明 |
|---|---|---|
| `script.mistuary.helper` P0/P1 | 规划完成（`helper-plugin-plan.md`），代码零行 | 独立仓库。**1.2.0 拿掉了演员/类型搜索，只有这条路能补回来** |
| Kodi 21 实机 | 从没验过 | 双轨渲染只在 22.0-BETA2 上跑过。装便携版 30 分钟 |
| 系统信息/事件日志底部文字区 | 待决策 | 建议保持现状（理由在 `skin-contracts.md`） |
| `SettingsSystemInfo` 滚动条轨道 | 待决策 | 644 vs 被控控件 357，建议改成 357 |

---

# 八、接下来做什么（2026-10-29 更新）

## 已完成

| 批次 | 内容 | 结果 |
|---|---|---|
| 第 1 批 ① | 删 `settings/background.png` + 21 张死贴图 | `Textures.xbt` **10.2 → 7.2 MB（−29%）**，提交 `d29a225` |
| 第 1 批 ② | 三张生成器表同步收窄 | `gen_glass_plates` 1 张 / `gen_rings` 8 环 + 1 细边 |
| 第 1 批 ④ | 文档失真 8 处 | README / skin-contracts / HANDOVER 已对齐实测值 |

## 剩下 6 件事（按建议顺序）

### ① 发 1.2.1（把这次清理交出去）　5 分钟

```bash
# addon.xml: 1.2.0 → 1.2.1；changelog.txt 顶部加一段
python tools/audit_skin.py --strict && python -m unittest discover -s tools -p 'test_*.py'
git add addon.xml changelog.txt && git commit -m "release: 1.2.1" && git push
```

**changelog 怎么写**（只写用户能感知的）：包体从 10.2 MB 降到 7.2 MB、皮肤设置说明文案修正。
不写"删了 22 张图"——用户不关心实现。
**风险**：CI 的 test job 挂了就不打包（1.2.0 卡过一次）。本地四件套先跑绿。
**验收**：Actions 绿 + Releases 出现 v1.2.1。

### ② 给 `audit_skin.py` 加两条反向检查　✅ 2026-10-29 已完成

现在它只查"引用了但文件不存在"，不查"定义了没人用"——1.87 MB 的死图就是这么藏住的。

- `--orphans`：先收集 XML 里的贴图路径，**再识别动态前缀**（`techflags/color/$PARAM[icon].png`、
  `settings/$PARAM[icon].png`、`shapes/glass$PARAM[radius].png`、
  `$INFO[…,windows/subtitles/flags/,.png]`、`dialogs/volume/progress/p<N>.png`、
  `genres/<名>.png`、`Default*.png`），差集才准。默认只提示、不返回非 0。
- `--dead`：变量用 `\$(?:ESC)?VAR\[([^,\]]+)`（`$ESC` 前缀 + 格式参数两个坑），
  include 要算 `content="X"`、`<include …>X</include>`、**`$PARAM[...]` 间接引用**三种。
- CI 的 test job 补 `gen_corner_masks --check`、`gen_rings --check`、`gen_glass_plates --check`。

**实测结果（2026-10-29）**
- `--orphans`：783 张里报出 **33 张 / 50.6 KB** 疑似未引用（`flags/ratings` 的
  metacritic / popcorn / rtrotten / mdblist、`flags/starrating/1..10.png`、
  `icons/sidemenu` 7 张、`osd/fullscreen/buttons` 4 张、`icons/search.png`、`lists/duration.png`）。
  已经排除了 Kodi 按名字自己解析的贴图（`Overlay*.png` / `pointer_*.png` / `spinner.png` /
  `defaultgenre.png` / `Default*.png`）和 12 个动态前缀。
  **这批还没删**——等下一轮确认（都很小，共 50 KB）。
- `--dead`：变量 312 个里 24 个没人引用、include 301 个里 6 个——**和 2.1 / 2.2 完全一致**。
- CI 补了 `gen_corner_masks / gen_rings / gen_glass_plates --check` 一步。

### ③ 决定 4 张 `*_filled` 图标　2 分钟

- 要实心/空心两态按钮 → 现在补引用（改 OSD 主控）；
- 不要 → 删 4 张图 + 删 `tools/gen_osd_filled_icons.py` + `tools/osd_icons/` 的 SVG。

### ④ 两个待决策（都在 §七）　各 10 分钟

- 系统信息 / 事件日志的底部文字区：建议保持现状
- `SettingsSystemInfo` 滚动条轨道 644 → 357：建议改（滑块长度是功能信息）

### ⑤ Kodi 21 实机验证　30 分钟

双轨渲染只在 22.0-BETA2 上跑过。装 Kodi 21.2 便携版（解压即用、不动现有配置）→
皮肤拷进 `portable_data/addons/` → 看四处：技术标识不出现 `$MAP[...]` 原文、详情页评分、
字幕/音轨标签、PVR 台标回退。**风险 0**。

### ⑥ `script.mistuary.helper` 阶段 0 + 1　1~2 天

规划在 [`helper-plugin-plan.md`](helper-plugin-plan.md)。**这是唯一能补回
"1.2.0 拿掉的演员/类型搜索"的路径**，因为中文分词/全拼只在 Emby 服务端生效。

阶段 0：仓库骨架 + CI（pytest + zip）+ settings + 缓存/HTTP/配置 → 可安装、空跑通过。
阶段 1：搜索桥 + 皮肤侧 `System.AddonIsEnabled(script.mistuary.helper)` 分支 + 回退本地 XSP。

**需要你定**：仓库建在哪个账号、名字是否就叫 `script.mistuary.helper`。

## 暂缓（保守档的取舍）

| 项 | 为什么暂缓 |
|---|---|
| 24 个死变量 + 6 个死 include | 不影响渲染，删了以后想复用要重写。等 `--dead` 工具做出来再一次性清 |
| `docs/scratch/` 17 MB | 里面 7 处引用已失效（§3.1），清之前要先修文档 |
| PVR 台标 9 处圆角 | 透明台标抠四角看不出来，只有 `DialogPVRInfo` 显示剧照时明显 |

**统一验收**

```bash
python tools/audit_skin.py --strict
python -m unittest discover -s tools -p 'test_*.py'
python tools/gen_corner_masks.py --check && python tools/gen_rings.py --check
python tools/gen_glass_plates.py --check && python tools/gen_techflag_vars.py --check
python tools/scan_rounded.py
python tools/xbt_tool.py pack        # 只有动过 media/
```

---

# 附：本轮已改

| 文件 | 改动 |
|---|---|
| `media/` 22 张 | 删除零引用贴图，xbt 10.2 → 7.2 MB |
| 三张生成器表 | `RADII` / `RINGS` / PS1 的 `video`+`metadata` 块收窄 |
| `docs/README.md` | techflags 96→97；透明度 25/29→18/17（补 15/16）；单测 46→58；自检块补 `gen_rings` / `scan_rounded` |
| `docs/skin-contracts.md` | 单测 42→58 |
| `docs/HANDOVER.md` | §8.3.2 改写为「已清理」；§4 补 `scan_rounded.py`；§8.1 HEAD 更正 |
| `addon.xml` | zh_CN disclaimer 结尾分号 → 句号 |
