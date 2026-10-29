# 圆角二期方案（待确认，未执行）

> 2026-10-28 全库扫描后制定。扫描脚本：`docs/scratch/scan_rounded.py`。
> 规范依据：`docs/HANDOVER.md` §5.4.1。**本文只描述改动，不改任何文件。**

---

## 0. 结论

`HANDOVER.md` §8.3.1 写的「圆角还剩 2 处」已过时。实际扫出来：

| 批次 | 性质 | 处数 | 风险 |
|---|---|---|---|
| **C-1** | 圆角被写法破坏（环被九宫格化） | 3 | 零，纯删属性 |
| **A** | 真漏的圆角（方框 / 方角卡片） | 11 | 低，只改单个控件 |
| **C-2** | 圆角卡片配方形投影 | 9 | 中，要新增贴图 |
| **B** | PVR / 插件台标类 | 9 | 低，但收益小 |
| **D** | 确认不做 | — | — |

建议顺序：**C-1 → A → C-2 → B**。C-1 单独提交（属修 bug），A 一个提交，C-2 一个提交。

---

## 1. C-1：3 处焦点环被九宫格化（修 bug，先做）

`View_54_InfoWall.xml` 有 3 个环控件仍带 `<bordersize>20</bordersize>`。

§5.4.1 明确：有 `<bordersize>` 时控件实例化成 `CGUIBorderedImage`（九宫格），
而描边环必须 1:1 整图。文档说这批 7 处已清，**这 3 处是漏网的**。
当前环尺寸（403.45×407.45）与贴图（403×407）只差 0.45px，所以肉眼还看不出来 ——
但这是定时炸弹：以后任何尺寸调整都会让环变形。

| 行号 | 控件 | 贴图 | 动作 |
|---|---|---|---|
| 26 | `InfoWallPictureLayout` 焦点环 | `ring_card_403x407_r14.png` | 删 `<bordersize>20</bordersize>` |
| 87 | `InfoWallMusicLayout` 焦点环 | `ring_card_343x413_r14.png` | 同上 |
| 179 | `InfoWallEpisodeLayout` 焦点环 | `ring_card_343x315_r14.png` | 同上 |

**注意**：同文件里紧邻的底板控件（13–19 / 74–80 / 166–172 行，`dialogs/dialog-bg-nobo.png`）
也带 `bordersize=20`，**那是纯色块，必须保留**。只删环控件那 3 个。

---

## 2. A 档：11 处真漏的圆角

统一手法（§5.4.1）：`<texture background="true" diffuse="shapes/mask_WxH_rN.png">`，
同时删掉 `bordertexture` / `bordersize` / `texture` 上的 `border` 属性。
`aspectratio` 一律保持原值。

半径按短边分档：**≥200 → r12，<200 → r9**。

### A-1 `PlayerControls.xml` 播放控制条封面 · 250×250 · 1 处

```
186–196  当前：<texture border="2">$VAR[NowPlayingPosterVar]</texture>
                + bordertexture(colors/black.png) + bordersize=4
         改为：<texture background="true" diffuse="shapes/mask_250x250_r12.png">
                aspectratio=keep 不变，删 border / bordertexture / bordersize
```
keep 下海报是 166×250 居中，遮罩跟图走（**不要写 `scalediffuse="false"`**），
实际圆角约 r8 —— 可以接受。

### A-2 `VideoOSDBookmarks.xml` 书签缩略图 · 330×250 · 2 处 + 焦点框

```
106–115  itemlayout 缩略图：加 mask_330x250_r12，删 border="4" / bordertexture / bordersize
130–139  focusedlayout 同上
149–156  焦点框：colors/white.png(border=3, 328×248 @ 1,6) 方形
         改为：<texture colordiffuse="focus_media">shapes/ring_card_332x252_r13.png</texture>
                @ left=-1, top=4，尺寸 332×252，删 border
```
环几何：海报 330×250 @ (0,5) → 环 +2 外扩 1px = 332×252 @ (-1,4)，半径 12+1=13。
这里 `aspectratio=scale`，遮罩写 `scalediffuse="false"`。

### A-3 `DialogMusicInfo.xml` 专辑缩略图 · 190×190 · 2 处

```
325–334  itemlayout（artists）：加 mask_190x190_r9，删 border="2" / bordertexture / bordersize
362–371  focusedlayout 同上
```

### A-4 `FileBrowser.xml` 右侧预览 · 260×380 · 1 处

```
55–64  加 mask_260x380_r12，删 border="4" / bordertexture / bordersize
       aspectratio aligny="bottom" keep 不变
```

### A-5 `View_52_IconWall.xml` 图标墙缩略图 · 160×116 · 2 处

```
47–55   itemlayout：加 mask_160x116_r9
85–93   focusedlayout：同上
```
这处最违和：卡片本体是 `round32` 圆角玻璃，中间嵌一张方角海报（`IconWallThumbVar`
在 `Container.Content()` 下取 `Art(poster)`）。
**已知局限**：控件 160×116 + `keep`，2:3 海报实际只有 77×116，遮罩缩放后圆角约 r4，
观感改善有限。做完先看实机，不够再考虑把控件改成海报比例。

### A-6 `DialogSeekBar.xml` 播放中封面 · 200×200 · 1 处

```
229–236  加 mask_200x200_r12，aspectratio keep 不变
```

### A-7 `SettingsProfile.xml` 用户头像 · 162×162 · 2 处

```
38–45   itemlayout：加 mask_162x162_r9（aspectratio=scale → 写 scalediffuse="false"）
95–102  focusedlayout：同上
```
外面已经是 `round24` 卡片，头像方角是唯一破绽。

---

## 3. C-2：9 处方圆不一的投影（可选，收益小）

`overlays/shadow.png` 是 80×80 九宫格（border=21）的**直角**描边：
线在距边缘 17–19px，alpha 12/33/63（很淡）。挂在圆角卡片上时，
卡片四角走圆弧、阴影走直角，亮背景上会看到角部阴影与卡片之间那条缝。

### 3.1 新增贴图（2 张）

| 文件 | 尺寸 | 说明 |
|---|---|---|
| `overlays/shadow_r9.png` | 80×80 LA | 圆角 9 版 |
| `overlays/shadow_r12.png` | 80×80 LA | 圆角 12 版 |

生成算法（写进新脚本 `tools/gen_soft_shadow.py`，供 `--check`）：

```
画布 80×80 / LA，9-slice border 仍为 21
三层同心 1px 圆角矩形，圆心都在 (32,32)：
  rounded_rectangle([17,17,62,62], radius=r+3, width=1, fill=12)
  rounded_rectangle([18,18,61,61], radius=r+2, width=1, fill=33)
  rounded_rectangle([19,19,60,60], radius=r+1, width=1, fill=63)
三层用 ImageChops.lighter 合并 → 中心天然透明（等价 infill=false）
```
半径取 r+3 是因为阴影线画在卡片外侧 1–3px（现有直角版的线就在卡片外）。

### 3.2 新增底板贴图（1 张）

`shapes/round9.png`（20×20，纯白圆角块 r9 + 1px 透明边，与 `round12.png` 同构）。
`media/shapes/` 现在只有 round12 起的底板，**没有 round9**。

### 3.3 替换清单

| 文件 | 行 | 当前底板 | 改为 |
|---|---|---|---|
| `Includes_Home.xml` | 277 | 320×180 `dialog-bg-nobo`(1×1 纯色) | 底板换 `round9`(border=9) + `shadow_r9` |
| `Includes_Home.xml` | 378 | 同上 | 同上 |
| `Includes_Home.xml` | 287 | 348×208 `round12` | 仅 `shadow` → `shadow_r12` |
| `Includes_Home.xml` | 388 | 同上 | 同上 |
| `Includes_Home.xml` | 625 | 320×180 `round12` | 仅 `shadow` → `shadow_r12` |
| `Includes_Home.xml` | 668 | 同上 | 同上 |
| `View_53_Shift.xml` | 139 | 334×480 `round12` | 仅 `shadow` → `shadow_r12` |
| `View_53_Shift.xml` | 151 | 334×480 遮罩卡 | 仅 `shadow` → `shadow_r12` |
| `View_53_Shift.xml` | 163 | 同上 | 仅 `shadow` → `shadow_r12` |

> 277/378 两处的底板是 1×1 纯色（alpha 204，很深），海报四角透出的就是它 ——
> 这两处必须连底板一起换成 `round9`，只换 shadow 没用。
>
> 625/668 的底板是 320×180 `round12`，但海报遮罩是 r9。底板比海报更圆 →
> 角部露出的是页面背景而不是底板色，视觉上不露底，**只换 shadow 即可**。

**收益评估**：现有阴影最大 alpha 只有 63（25% 黑），深色背景下完全看不见。
这批量力最小，**可以砍掉**。砍掉不影响 A 档。

---

## 4. B 档：PVR / 插件台标类（可选）

这些多数是 `keep` 居中的**透明台标 / 插件 logo**，抠四角看不出差别；
只有 `DialogPVRInfo` 走 `Art(thumb)` 剧照时才明显。60×60 的几处太小，不做。

| 文件 | 尺寸 | 处数 | 遮罩 |
|---|---|---|---|
| `MyPVRGuide.xml` | 290×250 | 2 | `mask_290x250_r12` |
| `Includes_PVR.xml` | 200×200 | 1 | `mask_200x200_r12`（复用 A-6） |
| `DialogPVRInfo.xml` | 505×655 | 3 | `mask_505x655_r12` |
| `DialogPVRInfo.xml` | 505×315 | 3 | `mask_505x315_r12` |
| `DialogPVRChannelGuide.xml` | 320×280 | 1 | `mask_320x280_r12` |
| `DialogPVRGroupManager.xml` | 314×200 | 1 | `mask_314x200_r12` |
| `AddonBrowser.xml` | 180×180 | 1 | `mask_180x180_r9` |

`DialogPVRInfo` 那 6 处还带 `aspectratio=keep` 且三种图源（台标/剧照/缩略图）互斥切换，
挂遮罩后对台标无影响、对剧照有圆角，是安全的。

---

## 5. D 档：确认不做（沿用旧判断）

- `View_50_List` 540×850 / 540×470 / 540×330 / 730×318 —— 列表预览大图，圆角后四角露出底板色
- `View_54_InfoWall` 336×300 / 316×316 / 316×218 —— 同上
- `DialogPictureInfo` 1180×720 —— 全屏看照片，切角不合适
- clearlogo（720×145 / 660×170 / 624×134 / 356×100）、`DefaultActor.png`、各类默认图标 —— 透明 PNG
- 所有 ≤60px 的列表行小图标

---

## 6. 新增资源汇总

| 类型 | 数量 | 文件 |
|---|---|---|
| diffuse 遮罩 | **7** | `mask_250x250_r12` `mask_330x250_r12` `mask_260x380_r12` `mask_190x190_r9` `mask_160x116_r9` `mask_200x200_r12` `mask_162x162_r9` |
| 焦点环 | **1** | `ring_card_332x252_r13` |
| 圆角底板 | **1** | `round9`（仅 C-2 需要） |
| 圆角阴影 | **2** | `shadow_r9` `shadow_r12`（仅 C-2 需要） |

若砍掉 C-2，则只需 **7 遮罩 + 1 环**。

生成器改动：
- `tools/gen_corner_masks.py` → `DIFFUSE_MASKS` 加 7 条
- `tools/gen_rings.py` → `RINGS` 加 1 条
- （C-2）新建 `tools/gen_soft_shadow.py`，并补 `round9` 的生成

---

## 7. 验证与同步

```bash
python tools/gen_corner_masks.py           # 生成 7 张遮罩
python tools/gen_rings.py                  # 生成 1 枚环
python tools/gen_corner_masks.py --check
python tools/gen_rings.py --check
python tools/audit_skin.py --strict        # 静态自检
python -m unittest discover -s tools -p 'test_*.py'
python tools/sync_to_kodi.py --loose       # 散包同步，改图只需重载皮肤
```

**发版前**才 `python tools/xbt_tool.py pack` + 普通 `sync_to_kodi.py`。

---

## 8. 风险与注意事项

1. **别写 `scalediffuse="false"`**：只有 `scale` / `stretch` 的控件才写。
   全库已验 0 处失效写法，改动时不要引入。
2. **删 `bordersize` 要认准控件**：C-1 里底板和环在同一段代码，别把底板的删了。
3. **`keep` 的控件圆角会按比例缩水**：A-1 / A-3 / A-4 / A-5 / A-6 都是 keep，
   遮罩跟图走，实际半径 = 声明半径 × (图片尺寸 / 控件尺寸)。观感以实机为准。
4. **A 档每处都会让图「大一点点」**：原来 4px `bordertexture` 会占掉一圈，
   去掉后图片边缘外移。若觉得海报变大了，再单独调控件尺寸，别在遮罩上找补。
5. **C-2 会影响 9 处，其中 3 处在 View_53_Shift**（已挂遮罩的卡片），
   `diffuse` 与 `bordertexture` 共存时圆角仍生效，只换 `bordertexture` 路径即可。
6. 提交纪律：`git add <具体文件>`，**不要 `git add -A`**。
7. 改完不要擅自 commit / push，先报改动清单和验证结果。

---

## 9. 需要你拍板

1. **C-2 做不做？**（收益最小，alpha 最高才 63）
2. **B 档做不做？**（PVR 台标类，多数是透明 logo）
3. **A-5 图标墙**那张 160×116 要不要顺手改控件比例（现在是方角小海报浮在圆角卡上）？
4. 确认后我从 **C-1** 开始，一批一个提交。

---

## 10. 执行记录（2026-10-28 23:5x）

### 决策

用户授权按建议定：**C-2 延后不做、B 档不做、A-5 只挂遮罩不改控件比例**
（160×116 是 itemlayout 给的，卡片高 205、label 在 top 134，没有空间放大缩略图）。
实际执行范围 = **C-1 + A 档**。

### 改动清单

| 文件 | 改动 |
|---|---|
| `xml/View_54_InfoWall.xml` | 删 3 处环控件的 `<bordersize>20</bordersize>`（底板那 3 处保留） |
| `xml/PlayerControls.xml` | 250×250 → `mask_250x250_r12`，删 `border="2"` / bordertexture / bordersize |
| `xml/VideoOSDBookmarks.xml` | 330×250 ×2 → `mask_330x250_r12`（scale，写 `scalediffuse="false"`）；焦点框 `colors/white.png` 方框 → `ring_card_332x252_r13` @ `(-1,4)` 332×252 |
| `xml/DialogMusicInfo.xml` | 190×190 ×2 → `mask_190x190_r9`，删方框 |
| `xml/FileBrowser.xml` | 260×380 → `mask_260x380_r12`，删方框 |
| `xml/View_52_IconWall.xml` | 160×116 ×2 → `mask_160x116_r9` |
| `xml/DialogSeekBar.xml` | 200×200 → `mask_200x200_r12` |
| `xml/SettingsProfile.xml` | 162×162 ×2 → `mask_162x162_r9`（scale，写 `scalediffuse="false"`） |
| `tools/gen_corner_masks.py` | `DIFFUSE_MASKS` +7（现 30 张） |
| `tools/gen_rings.py` | `RINGS` +1（现 15 张环 + 1 细边） |
| `media/shapes/` | 新增 7 遮罩 + 1 环，共 8 个文件 |

### 验证结果

- `gen_corner_masks.py --check` → 齐全（diffuse 30 / 实色 0 / 纯白 0）
- `gen_rings.py --check` → 齐全（15 环 + 1 细边）

> **2026-10-29 更新**：清理死资源时删掉 7 枚没接上的环（`206x206_r12` / `227x227_r12` /
> `227x276_r6` / `235x235_r6` / `243x243_r6` / `259x315_r6` / `275x331_r11`）与
> `ring12_3` / `ring_btn_120x70_r35` / `ring_card_250x358_r14`，`RINGS` 表同步收窄，
> 现在 `--check` 报 **8 环 + 1 细边**。
- `audit_skin.py --strict` → 缺失 include / 变量 / 字体 / 贴图 / 字符串 全 0，
  残留魔改属性 0，`<texture>` 非法属性 0
- 单元测试 56 个全过
- `gen_techflag_vars.py --check` → 同步
- 自定义校验：XML 里引用的 `diffuse` 贴图**全部存在**；
  `keep` + `scalediffuse="false"` 失效组合 **0 处**；
  环/细边带 `bordersize`/`bordertexture` 的违规 **0 处**（原 3 处已清）

### 同步状态

`sync_to_kodi.py --loose` 已同步 1061 个文件到 `%APPDATA%\Kodi\addons\skin.mistuary`。
**但 `Textures.xbt` 被运行中的 Kodi 占用，没能挪成 `.off`** ——
新增的 8 张贴图不在旧 xbt 里，靠 Kodi 的"bundle 未命中回落松散文件"机制加载，
理论上生效；要百分百确定，需**完全退出 Kodi 后重跑一次 `--loose`**。

### 未做

- C-2（9 处方圆投影 + `shadow_r9`/`shadow_r12`/`round9` 三张新图）
- B 档（PVR 台标类 9 处）
- 未 commit、未 push、未发版

