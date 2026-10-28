# docs/ 索引

皮肤 `skin.mistuary`（Mistuary）的开发文档。**三份必读 + 两份专题 + 两份历史资料。**

| 文件 | 什么时候读 |
|---|---|
| [`HANDOVER.md`](HANDOVER.md) | **接手第一份**。现状、运行时依赖、仓库结构、开发工具、发版流程、必须知道的约定、已知遗留 |
| [`skin-contracts.md`](skin-contracts.md) | 改任何窗口/设置前。窗口属性、皮肤设置、跨窗口控件 ID 的隐式契约清单，外加环境路径、验证命令、素材规格 |
| [`glass-opacity-plan.md`](glass-opacity-plan.md) | 改玻璃面板、不透明度、圆角、描边环前。含数值推导、实测锚点、踩过的坑 |
| [`techflag-icons-plan.md`](techflag-icons-plan.md) | 改影片技术标识（4K/HDR/Atmos…）的图标或布局前。图标规格、IconMap、评分行合并的取舍 |
| [`techflag-icon-coverage.md`](techflag-icon-coverage.md) | 查某个格式/音轨到底有没有图标。96 张图标的覆盖盘点 |
| [`kernel-extensions.md`](kernel-extensions.md) | **历史资料，不对应当前代码**。原魔改内核的 `material="glass"` / `slotlist` / 稳定选中项等扩展规格，本分支已全部移除，只留作对照 |
| [`repo-layout-plan.md`](repo-layout-plan.md) | **历史资料**。2026-10-27 把 `extras/` 归位成素材目录、构建工具移到 `tools/` 的整改记录 |

---

## 运行时依赖

**皮肤本体不需要任何 Python 脚本。** `addon.xml` 只依赖 `xbmc.gui 5.17.0`。
`tools/` 全是构建期工具，不进发布包。

皮肤会探测 `plugin.service.emby-next-gen` 和 `script.embuary.info`，
两者都只是"装了才显示"的可选增强，没有硬依赖。

---

## 一句话速查

- **不透明度**：`colors/defaults.xml` 的 `gl_*` / `sc_*` → `Variables.xml` 的
  `NaraGlass*TintVar` → 21 处页面 / 25 处浮窗 / 29 处播放中 `colordiffuse`。
  三档设置 × 6 档，默认 播放中 60% < 页面 73% < 浮窗 83%。见 HANDOVER §5.3。
- **圆角（面板）**：玻璃面板只有 `glass20`，选中行只有 `round14`。`border` 只给实心填充。
- **圆角（图片）**：`<texture diffuse="shapes/mask_<w>x<h>_r<半径>.png">`，
  **唯一正确做法**，遮罩尺寸必须和控件完全一致。见 HANDOVER §5.4.1。
  `corner_*.png` 实色遮盖是弯路，正在淘汰（亮背景会露深色角）。
- **描边环**：一律 1:1 整张图（`tools/gen_rings.py` 生成），**不要 border**，
  而且必须是该卡片**最后绘制**的控件。配遮罩时：环 = 卡片 +2、环半径 = 遮罩半径 +1
  （内缘压进海报 2px，环才贴得住）。**不要给环加 `bordersize`**（会走九宫格）。
- **不要相信 `Window.Property(NaraMusic.*)`**：全皮肤无人写入，是死属性。
- **`<include condition="X">` 是加载时求值的**，按运行时状态切外观只能用 `<visible>` / `$VAR`。
- **panel 不裁剪子控件**：想让行尾不露半张卡，得让"下一张起点 ≥ 1920"。
- **排查「某窗口不跟设置走」**：① grep 写死的 `AARRGGBB` 板 → ② grep `<include condition=`
  → ③ 最后才查 `$VAR` / `$PARAM`。

## 自检

```bash
python tools/audit_skin.py --strict                      # 静态自检，必须 EXIT=0
python tools/gen_techflag_vars.py --check                # 技术标识变量同步
python tools/gen_corner_masks.py --check                 # 圆角贴图是否齐全
python -m unittest discover -s tools -p 'test_*.py'      # 42 项
python tools/xbt_tool.py pack                            # 改过 media/ 之后必须重打包
```

## 已清理的旧稿

1.0.0（改名 + 通用版收尾）之前的规划稿、外部审查报告、逐项修复清单已删除：
内容全部落地，剩下的有效部分（环境路径、验证命令、`<texture fallback>` 那条）
已并入 `skin-contracts.md` 的附录。旧皮肤的 4.x changelog 也已从 `changelog.txt` 移除。
