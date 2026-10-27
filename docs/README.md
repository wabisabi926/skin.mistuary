# docs/ 索引

皮肤 `skin.mistuary`（Mistuary）的开发文档。**三份必读 + 一份历史资料。**

| 文件 | 什么时候读 |
|---|---|
| [`HANDOVER.md`](HANDOVER.md) | **接手第一份**。现状、运行时依赖、仓库结构、开发工具、发版流程、必须知道的约定、已知遗留 |
| [`skin-contracts.md`](skin-contracts.md) | 改任何窗口/设置前。窗口属性、皮肤设置、跨窗口控件 ID 的隐式契约清单，外加环境路径、验证命令、素材规格 |
| [`glass-opacity-plan.md`](glass-opacity-plan.md) | 改玻璃面板、不透明度、圆角、描边环、角部遮盖前。含数值推导、实测锚点、踩过的坑 |
| [`kernel-extensions.md`](kernel-extensions.md) | **历史资料，不对应当前代码**。原魔改内核的 `material="glass"` / `slotlist` / 稳定选中项等扩展规格，本分支已全部移除，只留作对照 |

---

## 运行时依赖

**皮肤本体不需要任何 Python 脚本。** `addon.xml` 只依赖 `xbmc.gui 5.17.0`。
`tools/` 全是构建期工具，不进发布包。

皮肤会探测 `plugin.service.emby-next-gen` 和 `script.embuary.info`，
两者都只是"装了才显示"的可选增强，没有硬依赖。

---

## 一句话速查

- **不透明度**：`colors/defaults.xml` 的 `gd_*` / `sc_*` / `gp_*` → `Variables.xml` 的
  `NaraGlass*TintVar` → 43 处 `colordiffuse`。设置项在「皮肤设置 → 外观」。
  播放中浮窗走 `NaraPlaybackDialogTintVar`（下移两档，合成 72%）。
- **圆角**：玻璃面板只有 `glass20`，选中行只有 `round14`。`border` 只给实心填充。
- **描边环**：一律 1:1 整张图（`tools/gen_rings.py` 生成），**不要 border**，
  而且必须是该卡片**最后绘制**的控件。
- **角部遮盖**：`tools/gen_corner_masks.py`，`ALPHA=200` / `#2A2A2E`。
- **不要相信 `Window.Property(NaraMusic.*)`**：全皮肤无人写入，是死属性。
- **`<include condition="X">` 是加载时求值的**，按运行时状态切外观只能用 `<visible>` / `$VAR`。
- **panel 不裁剪子控件**：想让行尾不露半张卡，得让"下一张起点 ≥ 1920"。
- **排查「某窗口不跟设置走」**：① grep 写死的 `AARRGGBB` 板 → ② grep `<include condition=`
  → ③ 最后才查 `$VAR` / `$PARAM`。

## 自检

```bash
python tools/audit_skin.py                        # 静态自检
python tools/gen_techflag_vars.py --check         # 技术标识变量同步
python -m unittest discover -s tools -p 'test_*.py'
python tools/xbt_tool.py pack                            # 改过 media/ 之后必须重打包
```

## 历史文档

- [`kernel-extensions.md`](kernel-extensions.md)：魔改内核的皮肤 XML 扩展规格（玻璃、圆角、
  `texturebackground`、`selectionsettledelay`、`slotlist`、`ImageChange`/`Follow`、
  `playbacktarget` 等）。2026-10-27 从根目录 README 拆出来，避免用户照着写不生效的标签。
- [`repo-layout-plan.md`](repo-layout-plan.md)：2026-10-27 把 `extras/` 归位成素材目录、
  构建工具移到 `tools/` 的整改记录。

1.0.0（改名 + 通用版收尾）之前的规划稿、外部审查报告、逐项修复清单已清理：
内容全部落地，剩下的有效部分（环境路径、验证命令、`<texture fallback>` 那条）
已并入 `skin-contracts.md` 的附录。旧皮肤的 4.x changelog 也已从 `changelog.txt` 移除。
