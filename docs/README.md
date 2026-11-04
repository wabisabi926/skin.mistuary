# docs/ 索引

皮肤 `skin.mistuary`（Mistuary）的开发文档。**三份必读 + 三份专题 + 历史资料与报告。**

| 文件 | 什么时候读 |
|---|---|
| [`HANDOVER.md`](HANDOVER.md) | **接手第一份**。现状、运行时依赖、仓库结构、开发工具、发版流程、必须知道的约定、已知遗留 |
| [`handover-2026-11-03.md`](handover-2026-11-03.md) | **最近一次交接快照**（2026-11-03）：当天本地改动、未发布项、遗留问题 |
| [`skin-contracts.md`](skin-contracts.md) | 改任何窗口/设置前。窗口属性、皮肤设置、跨窗口控件 ID 的隐式契约清单，外加环境路径、验证命令、素材规格 |
| [`glass-opacity-plan.md`](glass-opacity-plan.md) | 改玻璃面板、不透明度、圆角、描边环前。含数值推导、实测锚点、踩过的坑 |
| [`helper-plugin-plan.md`](helper-plugin-plan.md) | 改 helper 接线前。**皮肤侧摘要**：调用方式、降级表、版本要求；M1b/M2/M1c 已完成。实现细节、进度表、测试在插件仓库 `D://下载//AI//script.mistuary.helper//docs//` |
| [`techflag-icons-plan.md`](techflag-icons-plan.md) | 改影片技术标识（4K/HDR/Atmos…）的图标或布局前。图标规格、IconMap、评分行合并的取舍 |
| [`techflag-icon-coverage.md`](techflag-icon-coverage.md) | 查某个格式/音轨到底有没有图标。97 张图标的覆盖盘点 |
| [`kernel-extensions.md`](kernel-extensions.md) | **历史资料，不对应当前代码**。原魔改内核的 `material="glass"` / `slotlist` / 稳定选中项等扩展规格，本分支已全部移除，只留作对照 |
| [`vinyl-helper-plan.md`](vinyl-helper-plan.md) | 做音乐播放页的黑胶唱片效果、或开始搭 `script.mistuary.helper` 前。含动画可行性核实、素材清单、骨架文件职责、暂停回弹等硬伤 |
| [`pending-work-plan.md`](pending-work-plan.md) | **历史方案（2026-10-29，已归档）**。清理项已执行，仅作背景；当前发版状态看 `addon.xml` / `HANDOVER.md` |
| [`report-triage-2026-10-29.md`](report-triage-2026-10-29.md) | **外部校验报告怎么读**。456 errors / 448 warnings 的分诊：哪些是 CRLF 假阳性、哪些是 Kodi 22 双轨、哪些是真 bug；含修复批次、Kodi 21 回退点和待决策项 |
| [`skin.mistuary_report.txt`](skin.mistuary_report.txt) | **历史外部报告原文**（2026-10-29）。只看分诊结论，不要按原文逐条修 |
| [`repo-layout-plan.md`](repo-layout-plan.md) | **历史资料**。2026-10-27 把 `extras/` 归位成素材目录、构建工具移到 `tools/` 的整改记录 |

---

## 运行时依赖

**皮肤本体不需要任何 Python 脚本。** `addon.xml` 只依赖 `xbmc.gui 5.18.0`。
`tools/` 全是构建期工具，不进发布包。

皮肤会探测 `plugin.service.emby-next-gen`、`script.embuary.info` 和
`script.mistuary.helper`（可选，0.3.6 已发布；本地 0.3.7 未发），都是"装了才启用"的可选增强，没有硬依赖。
helper 的契约见 [`helper-plugin-plan.md`](helper-plugin-plan.md)（摘要）；权威文档在插件仓库 `docs/`。

> **历史问题（2026-10-30，已解决）**：服务端搜索结果封面与无 fanart 时的搜索背景
> 均已修复，细节见 [`HANDOVER.md`](HANDOVER.md) §8.10。

---

## 一句话速查

- **不透明度**：`colors/defaults.xml` 的 `gl_*` / `sc_*` → `Variables.xml` 的
  `NaraGlass*TintVar` → 21 处页面 / 18 处浮窗 / 17 处播放中 `colordiffuse`
  （另有 15 处设置对话框、16 处遮蔽）。
  三档设置 × 6 档，默认 播放中 60% < 页面 73% < 浮窗 83%。见 HANDOVER §5.3。
- **圆角（面板）**：玻璃面板只有 `glass20`，选中行只有 `round14`。`border` 只给实心填充。
- **圆角（图片）**：`<texture diffuse="shapes/mask_<w>x<h>_r<半径>.png">`，
  **唯一正确做法**，遮罩尺寸必须和控件完全一致。见 HANDOVER §5.4.1。
  `corner_*.png` 实色遮盖已彻底退役（`media/shapes/` 里一张不剩）。
- **描边环**：一律 1:1 整张图（`tools/gen_rings.py` 生成），**不要 border**，
  而且必须是该卡片**最后绘制**的控件。配遮罩时：环 = 卡片 +2、环半径 = 遮罩半径 +1
  （内缘压进海报 2px，环才贴得住）。**不要给环加 `bordersize`**（会走九宫格）。
- **`Window.Property(NaraMusic.*)` 已清理**：原先无写入方的下一首/歌词状态死属性 UI
  已在 2026-11-01 删除；以后要恢复，先补写入方（helper service 或 CU LRC 补丁）。
- **背景遮罩**：真剧照压暗、`primary.jpg` 兜底不压；判据在 `Includes_Home.xml` 的三条
  `expression`，改 `HomeFanartVar` / `HomeVideoHeroFanartVar` 必须同步，
  `check_home_fanart_mask.py --check` 会拦。见 HANDOVER §5.11。
- **`<include condition="X">` 是加载时求值的**，按运行时状态切外观只能用 `<visible>` / `$VAR`。
- **panel 不裁剪子控件**：想让行尾不露半张卡，得让"下一张起点 ≥ 1920"。
- **排查「某窗口不跟设置走」**：① grep 写死的 `AARRGGBB` 板 → ② grep `<include condition=`
  → ③ 最后才查 `$VAR` / `$PARAM`。

## 自检

```bash
python tools/audit_skin.py --strict                      # 静态自检，必须 EXIT=0
python tools/audit_skin.py --orphans                     # 反向：没人引用的贴图（应 0 张）
python tools/audit_skin.py --dead                        # 反向：没人用的变量 / include
python tools/gen_techflag_vars.py --check                # 技术标识变量同步
python tools/gen_techflag_icons.py --check               # 技术标识图标 / IconMap / TextMap 对齐
python tools/gen_home_nav_plates.py --check              # 首页导航底板与生成结果一致
python tools/check_home_fanart_mask.py --check           # 首页遮罩判据与背景变量分支一致
python tools/gen_corner_masks.py --check                 # 圆角遮罩是否齐全（30 张）
python tools/gen_rings.py --check                        # 焦点环是否齐全（8 环 + 1 细边）
python tools/gen_resume_ring.py --check                  # 续播圆环 101 帧与生成器一致
python tools/scan_rounded.py                             # 列「应圆角但没挂 diffuse」的控件
python -m unittest discover -s tools -p 'test_*.py'      # 86 项
python tools/xbt_tool.py pack                            # 改过 media/ 之后必须重打包
```

## 已清理的旧稿

1.0.0（改名 + 通用版收尾）之前的规划稿、外部审查报告、逐项修复清单已删除：
内容全部落地，剩下的有效部分（环境路径、验证命令、`<texture fallback>` 那条）
已并入 `skin-contracts.md` 的附录。旧皮肤的 4.x changelog 也已从 `changelog.txt` 移除。
