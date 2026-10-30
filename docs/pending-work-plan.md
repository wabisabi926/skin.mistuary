# 最终优化方案（2026-10-29）

> 基线：`main` = `v1.3.1`（2026-10-30，tag 待打）。**第 1 批清理已完成**。
> **2026-10-29 后续进度**：黑胶唱片（`c67ffb4`）和死变量 / 死 include（`9851941`）已完成；
> 外部校验报告的 P0 / P1 / P2 也已清完（`report-triage-2026-10-29.md`）。
> **2026-10-30 更新**：Kodi 21 实机验证已放弃（`HANDOVER.md` §8.7，含一次配置重置事故）；
> 剩下只有 `script.mistuary.helper` 的皮肤侧接线和两个新功能 —— **但 helper 的正式接入
> 已排到 2.0.0（2026-10-30 定）**，1.x 不再推进，见 `HANDOVER.md` §8.9。
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
的 35 → 59 项与 xbt 662 → 751，HANDOVER 的去掉的提交号，工具表补 `scan_rounded.py`，
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
| `script.mistuary.helper` P0 | **插件侧已完成**（58 项单测），皮肤侧未接 | 独立仓库 `D:/下载/AI/script.mistuary.helper`。**1.2.0 拿掉了演员/类型搜索，只有这条路能补回来** |
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
| 删 33 张死图 | ✅ `0ebccc5`（`--orphans` 首次实战），包体 → **7.1 MB / 751 张** |
| `--orphans` / `--dead` | ✅ 已加，`--orphans` 复检 **0 张** |
| 系统信息页滚动条 644 → 357 | ✅ 含几何回归测试 |
| 4 张 `*_filled` + 生成器 | ✅ 已删（源 SVG 留在 `tools/osd_icons/`） |
| 文档失真 8 处 | ✅ 已对齐实测值 |
| helper「可选安装」契约 | ✅ `helper-plugin-plan.md` §2 |

## 还剩 1 件事（2026-10-30 更新）

> ① 黑胶、③ 死变量清理、外部校验报告 P0/P1/P2 都已完成。
> ② 的**插件侧已完成**（58 项单测全绿），只剩皮肤侧接线（M1b）。

### ① 黑胶唱片效果 ✅ 已完成（`c67ffb4`）

方案在 [`vinyl-helper-plan.md`](vinyl-helper-plan.md) §2，技术已核实：
`<animation effect="rotate" loop="true">` 能连续转（`GUIControlFactory.cpp:1148`），
圆形遮罩直接用 256² 的 `masks/circle.png` 等比放大。

**先要用户认可一个硬伤**：Kodi 条件动画在条件消失时 reset，**暂停时唱片会"啪"回 0°**，
没有 API 能停在当前角度。缓解是周期拉到 24s/圈 + `reversible`。

素材要拆：`gen_music_cover.py` 现在把盘面 + 唱臂压成一张 768² 兜底图，
要拆成 `vinyl-disc.png`（转）+ `vinyl-tonearm.png`（不转）。

### ② `script.mistuary.helper` 皮肤侧接线（M1b）　半天

**插件侧已完成**：独立仓库 `D:/下载/AI/script.mistuary.helper`（`main`，2 个提交），
阶段 0 骨架 + 阶段 1 服务端搜索，58 项单测全绿，已同步实机。
**但还没建远端仓库** —— 推不出去用户就装不了，这是当前的卡点。

皮肤侧一行未改。接分支要动三处（详见 [`helper-plugin-plan.md`](helper-plugin-plan.md) §2）：

1. `Includes_Search.xml` 的 `NaraSearchMoviesPathVar` / `NaraSearchTVShowsPathVar` 各加一条分支，
   原 value 留作最后兜底
2. `SkinSettings.xml` 媒体类（`grouplist id=610`）加 `hide_helper_search` 开关
   —— **反向命名才能默认开**，`Skin.HasSetting` 在没设置过时返回 false
3. 帮助条 + 两个语言文件各加一条（id 从 **31780** 起，31779 是当前最大值）

**唯一待决策**：Emby token 来源（读插件配置 vs 让用户填）。
播放地址代码已选 `emby-next-gen mode=play`，只剩实机验证，**不阻塞接线**。

**最大的技术不确定点**：`<content sortby="sorttitle">` 写死在两个结果容器上
（`Includes_Search.xml:674` / `:695`），服务端模式会覆盖相关度排序。
优先试删掉它、靠 XSP 自带的 `order`；不行再用两套 `<content>` 按条件切换。
见 [`helper-plugin-plan.md`](helper-plugin-plan.md) §2。

### ③ 24 个死变量 + 6 个死 include ✅ 已完成（`9851941`）

`python tools/audit_skin.py --dead` 直接列。删前逐个确认——
**`HomeVideoRowNavigation` 是活的**（经 `<param name="navigation">` → `$PARAM` 动态引用）。

## 不建议做的

| 项 | 为什么 |
|---|---|
| 背景兜底换图 | 有兜底（`extras/backgrounds/primary.jpg`，1920×1080 / 228 KB，`DefaultBackground` 里无条件绘制）。只是深色图和纯黑对比低，换图收益小 |
| PVR 台标 9 处圆角 | 透明台标抠四角看不出来 |
| `docs/scratch/` 清理 | 20 MB 本地缓存、已 gitignore，删了不影响仓库；要清随时清 |
| `<scroll>` 运行时条件（12 处） | 只认布尔字面量；"聚焦才滚动"要拆两套 label，收益只是长标题滚动 |

**统一验收**

```bash
python tools/audit_skin.py --strict                      # EXIT=0
python tools/audit_skin.py --orphans                     # 0 张
python tools/audit_skin.py --dead                        # 0 变量 / 0 include
python -m unittest discover -s tools -p 'test_*.py'       # 59 项
python tools/gen_corner_masks.py --check && python tools/gen_rings.py --check \
  && python tools/gen_glass_plates.py --check && python tools/gen_techflag_vars.py --check
python tools/xbt_tool.py pack                            # 只有动过 media/
```
