# 最终优化方案（2026-10-29）

> 基线：`main` = `v1.4.0`（2026-10-30 发版）。**第 1 批清理已完成**。
> **2026-10-29 后续进度**：黑胶唱片（`c67ffb4`）和死变量 / 死 include（`9851941`）已完成；
> 外部校验报告的 P0 / P1 / P2 也已清完（`report-triage-2026-10-29.md`）。
> **2026-10-31 更新**：M1b 搜索 / M2 豆瓣 / M1c 实机验收均已完成，插件已发 0.3.2；
> 原 1.4.1 的 tag 已撤回，其全部改动并入 **1.5.0（本次发版）**。
> M1d / M3 / M4 暂缓或不做。Kodi 21 实机验证已放弃（`HANDOVER.md` §8.7）。
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

| 项 | 现状 | 结论 |
|---|---|---|
| `docs/scratch/` | 本地 20 MB，已 gitignore；7 处失效文档引用已修完 | 随时可清（`rm -rf docs/scratch/*`，只留 README），不影响仓库 |
| `tools/universalize.py` | 4.2.0 → 1.0.0 的一次性迁移脚本 | **保留**：HANDOVER §7 定为参考；`release.yml` 排除 `tools/`，不进包 |
| `tools/preview.html` | 8 KB，早期配色预览 | 保留，无成本 |
| `tools/music-cover-original.png` | **756 KB** 源图，`gen_music_cover.py` 的输入 | **保留**（删了封面就没法重新生成） |
| `tools/osd_icons/*.svg` | 7 KB，OSD 图标矢量源 | 保留（生成器要用） |
| `tools/test_nara_*.ps1` | 4 个 PowerShell 手动 UI 测试 | 保留，但没进 CI，属于"要人跑"的 |

## 3.1　`docs/scratch/` 的 7 处失效引用（已修）

`techflag-icon-coverage.md` 改成"复现脚本已丢失，下表是 2026-10-28 快照"；
`techflag-icons-plan.md` 里三张样张引用已删；`rounded-corners-phase2.md`
指向已转正的 `tools/scan_rounded.py`。`icon_coverage.py` 暂未重写进 `tools/`，
需要时按 `techflags/color/*` 与 5 张 map 重新实现。

---

# 四、清理：文档失真（已全部处理）

8 处已按实测值改写：README 的图标张数 / 透明度处数 / 单测项数，`skin-contracts`
的 35 → 当前 84 项与 xbt 662 → 当前 749 张，HANDOVER 的去掉的提交号，工具表补 `scan_rounded.py`，
`addon.xml` 免责声明结尾分号 → 句号。

**唯一遗留**：`addon.xml:19` 的 `<forum>` 仍指向 `http://forum.kodi.tv/` 首页。
没有皮肤帖的真实地址，不猜；拿到帖子 URL 再换。

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
| `script.mistuary.helper` | **插件 0.3.2 已发布**（91 项单测），皮肤侧 M1b/M2/M1c 均已完成 | 独立仓库 `D:/下载/AI/script.mistuary.helper`。M1d 演员/类型暂缓 |
| Kodi 21 实机 | **已放弃**（2026-10-30） | 双轨渲染至今只在 22 系列上验过。21 的库版本不兼容、便携环境也没有媒体库，详情页四项验不了；尝试时出过配置重置事故，详见 `HANDOVER.md` §8.7 |
| 系统信息/事件日志底部文字区 | 待决策 | 建议保持现状（理由在 `skin-contracts.md`） |
| `SettingsSystemInfo` 滚动条轨道 | ✅ 已改 | 644 → 357（`2cda76f`，含几何回归测试） |

---

# 八、接下来做什么（2026-10-29 收尾）

## 已完成（1.2.1 之后）

| 项 | 结果 |
|---|---|
| 发 1.2.1 | ✅ tag `v1.2.1` → `fc61e7e`，GitHub 已打包 |
| 删 22 张死图 | ✅ `d29a225`，包体 10.2 → 7.2 MB |
| 删 33 张死图 | ✅ `0ebccc5`（`--orphans` 首次实战），包体 → **7.1 MB / 751 张**（后删 2 张，现 749） |
| `--orphans` / `--dead` | ✅ 已加，`--orphans` 复检 **0 张** |
| 系统信息页滚动条 644 → 357 | ✅ 含几何回归测试 |
| 4 张 `*_filled` + 生成器 | ✅ 已删（源 SVG 留在 `tools/osd_icons/`） |
| 文档失真 8 处 | ✅ 已对齐实测值 |
| helper「可选安装」契约 | ✅ `helper-plugin-plan.md` §2 |

## 2026-10-31 已修（`8fd80d8`）

交接文档里那三个「新发现的问题」已全部关闭，另外顺手收了三个：

| 项 | 结果 |
|---|---|
| 搜索 hero 没有技术标识 | 根因在 helper：没请求 `MediaSources`、没调 `addStreamInfo`。helper 侧已补 |
| 电视剧卡片没有 4K / Blu-ray 角标 | 角标是 Emby 叠在海报图里的，剧集层级没有文件流信息 → 皮肤侧无解，不再尝试 |
| 电视剧小组件右侧留白 | 搜索网格去掉写死 `width=1780`；卡片槽 240→252（2160 上 8 列刚好铺满） |
| 技术标识一格画出 3~4 颗 | 三个条件求值坑，见 `skin-contracts.md` §4.1.1 |
| 首页剧集行没有技术标识 | 两级隐藏探针（季→集）取第一集当代表集，见 §4.3 |
| 首页豆瓣次评分不显示 | **1.5.0 定稿：详情页显示豆瓣次评分，列表 / 首页不显示**（读 helper 窗口属性；插件写库的 `rating_type=douban` 暂无消费方） |

## 剩下的 2 件事（2026-10-31 更新）

> 黑胶、死变量、外部校验报告 P0/P1/P2、M1b/M2/M1c、搜索封面 / 背景兜底都已完成；
> 插件已发 0.3.2。当前只剩：**发 1.5.0（本次）**，以及 M1d 是否开工。

### ① 发 1.5.0（本次）

- `addon.xml` 已是 1.5.0 → 提交 + push；CI 全绿后自动打包建 Release。
- 1.4.1 的 tag 已撤回，无需 force、也无需删 Release。
- 发版前跑文末统一验收。

### ② M1d 搜索补齐（演员 / 类型，暂缓）

- 插件侧方案见 `script.mistuary.helper/docs/roadmap.md` §M1d；用户确认需求后再开工。
- 皮肤侧支持人员/类型搜索也需要新容器，不只是插件改动。

### 已完成（留档）

- M1c 实机验收（搜索 + 播放）：2026-10-30 通过。
- 搜索封面：插件 `c4ac966`；搜索背景兜底：皮肤 `baae9ef`。

## 不建议做的

| 项 | 为什么 |
|---|---|
| 背景兜底换图 | `DefaultBackground` 有 `primary.jpg` 兜底；但搜索页的 `NaraSearchBackground` 会用纯黑层盖住它，这是 ② 的已知问题，不是换图能解决 |
| PVR 台标 9 处圆角 | 透明台标抠四角看不出来 |
| `docs/scratch/` 清理 | 20 MB 本地缓存、已 gitignore，删了不影响仓库；要清随时清 |
| `<scroll>` 运行时条件（12 处） | 只认布尔字面量；"聚焦才滚动"要拆两套 label，收益只是长标题滚动 |

**统一验收**

```bash
python tools/audit_skin.py --strict                      # EXIT=0
python tools/audit_skin.py --orphans                     # 0 张
python tools/audit_skin.py --dead                        # 0 变量 / 0 include
python -m unittest discover -s tools -p 'test_*.py'       # 84 项
python tools/gen_corner_masks.py --check && python tools/gen_rings.py --check \
  && python tools/gen_glass_plates.py --check && python tools/gen_techflag_vars.py --check
python tools/xbt_tool.py pack                            # 只有动过 media/
```
