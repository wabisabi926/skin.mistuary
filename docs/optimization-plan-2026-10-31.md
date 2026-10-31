# 皮肤 + 插件全量梳理与优化方案（2026-10-31）

> 范围：`<仓库根>`（1.5.0，工作区含 1.5.1 未提交改动）
> 和 `<插件仓库根>`（0.3.3，未提交）。
> **本文只出方案，未改任何代码。**
> 基线证据：皮肤 `audit_skin.py --strict` 全 0、`--orphans` 0 张、`--dead` 0 项、
> 89 项单测全绿；helper 101 项单测全绿。

---

## 0. 版本矩阵（先看这张）

| | 仓库 | 实机 | 差距 |
|---|---|---|---|
| 皮肤 | `addon.xml` **1.5.0**，changelog 已写 1.5.1 | **1.4.1** | **实机落后一个版本** |
| helper | **0.3.3**（工作区未提交） | 0.3.3 | 代码同版本，但**文件内容不同**（见 P0-3） |
| 远端 | 皮肤 ahead 5、helper ahead 1 | — | **两边远端都没有新东西可拉** |

**先回答你上一个问题**：`git fetch` 后两边远端都没有新提交，本地反而领先
（皮肤 5 个、helper 1 个）。所以"从 GitHub 同步到本地"这一步没有内容可拉 ——
**真正需要同步的是反方向：本地 → 实机**（实机皮肤还停在 1.4.1）。

---

## P0：会导致出错或已出错的问题（3 条）

### P0-1　helper 的 `addon.xml` 指向了不存在的图标文件

**证据**

```bash
cd script.mistuary.helper
git diff addon.xml
-  <icon>resources/icon.png</icon>
-  <fanart>resources/fanart.jpg</fanart>
+  <icon>icon.png</icon>
+  <fanart>fanart.jpg</fanart>

ls icon.png            → No such file or directory
ls fanart.jpg          → No such file or directory
git ls-files | grep -i icon → 只有 resources/icon.png
```

**后果**：这份改动一旦提交发版，插件在 Kodi 里**图标和背景全空**（addon 管理器会回退到
默认方块图标）。你截图里"icon 不出来"，如果指的是插件本身的图标，很可能就是这个原因
（取决于实机装的是哪一版 addon.xml）。

**修法**（二选一，推荐 A）：

| | 做法 | 代价 |
|---|---|---|
| **A** | assets 改回 `resources/icon.png` / `resources/fanart.jpg` | 一行，零风险 |
| B | `git mv resources/icon.png icon.png` + 同样搬 fanart，`tools/gen_assets.py` 输出目录一起改 | Kodi 19+ 官方推荐根目录，但要改生成器和 CI |

**回退**：改回 `resources/` 前缀即可。

---

### P0-2　helper 的 `xbmc.service` 声明指向已被删除的 `service.py`

**证据**

```bash
git show HEAD:addon.xml | grep service   → 11: <extension point="xbmc.service" library="service.py"/>
ls service.py                            → No such file or directory
git status --short                       →  D service.py  /  D lib/rating_sync.py
实机 addon.xml                           → xbmc.service 出现 0 次
```

**根因**：0.3.3 决定「移除评分同步：写库无消费方」（changelog 有写），
`service.py` 和 `lib/rating_sync.py` 已删，但**仓库里这份删除还没提交**。
实机是手动拷的（已经没这个声明），所以实机没报错，仓库里是坏的。

**后果**：若按 HEAD 发版，Kodi 启动日志会刷
`Failed to load service.py`，并且 service 会一直起不来。

**修法**：把 `D service.py`、`D lib/rating_sync.py` 和 `M addon.xml` 一起提交（同一主题）。

---

### P0-3　实机 helper 目录被 StrmAssistant 源码污染

**证据**：`%APPDATA%\Kodi\addons\script.mistuary.helper\` 里存在这些**不属于本插件**的文件：

```
StrmAssistant/          StrmAssistant.Tests/     StrmAssistant.sln
CHANGELOG.md            CONTRIBUTING.md          README.en.md
build-local.sh          docs.7z
```

**性质**：StrmAssistant（神医助手）是另一个项目的源码树，被解压/拷贝到了 addon 目录。
Kodi 只加载 `addon.xml` 声明的入口，所以**不会崩**，但：
- 白白占用空间（`StrmAssistant/` + `docs.7z` 通常几十 MB）
- 以后排查"这个文件哪来的"会反复踩坑
- 升级插件时若用"覆盖拷贝"方式，这些残留会一直在

**修法**：删除上述 8 项（**保留** `addon.xml` `default.py` `lib/` `resources/` `tests/`
`tools/` `changelog.txt` `icon.png` `fanart.jpg` `__pycache__`）。
删之前建议先 `tar` 一份到 `<备份目录>\`。

**风险**：极低。这些文件不被 addon.xml 引用。

---

## P1：文档失真（4 条，都会误导下一个接手的人）

| # | 位置 | 现状 | 应为 |
|---|---|---|---|
| P1-1 | 皮肤 `changelog.txt`（工作区已改） | 已从「需 Helper 0.3.4+」改成 0.3.3 | ✅ 工作区已修正，待提交 |
| P1-2 | helper `docs/HANDOVER.md` 标题 | 「交接说明（Mistuary Helper **0.2.2**）」 | 0.3.3，且内容停在 0.2.2，落后两个版本 |
| P1-3 | 皮肤 `docs/helper-plugin-plan.md:121` | 「实机仍是 0.3.2，待同步 0.3.3」 | 实机已是 0.3.3 |
| P1-4 | helper `docs/roadmap.md` M2 行 | 「次评分设置已在皮肤 1.5.1 移除」 | 与皮肤 1.5.1 实际一致 ✅，但需确认"次评分四档"仍在（皮肤确实保留了次评分来源） |

**修法**：P1-2 重写（或按现有 `docs/architecture.md` / `contract.md` 的格式重出一版）；
P1-3 改一行；P1-4 核对后决定是否改措辞。

---

## P2：可以清理的（3 条，不影响功能）

| # | 项 | 证据 | 建议 |
|---|---|---|---|
| P2-1 | 实机 helper 根目录 `icon.png` / `fanart.jpg` 与 `resources/` 下同名文件**重复** | `md5sum` 两份一致（18697 B） | 跟着 P0-1 一起定：assets 指哪份就留哪份 |
| P2-2 | 皮肤 `docs/` 下 16 个 md，其中 4 个是历史快照 | `audit-2026-10-30.md`（v1.3.1 基线）、`report-triage-2026-10-29.md`、`rounded-corners-phase2.md`、`handover-2026-10-30.md` | 不用删，但应在 `docs/README.md` 里标"历史归档，勿按此执行" |
| P2-3 | helper `tools/gen_assets.py` 已改成输出方角图标 | 工作区 `M tools/gen_assets.py`，删掉了 `rounded_mask()` | 确认 `resources/icon.png` 已用新脚本重新生成（工作区 `M resources/icon.png` 说明跑过了） |

---

## P3：体验优化（2026-10-31 新增，你提的两条）

### P3-1　「Emby 服务器」帮助文案说不清"什么时候才需要填"

**现状**（`resources/language/resource.language.zh_cn/strings.po`）

| id | 当前中文 |
|---|---|
| 32050（服务器 ID 的帮助） | 留空使用第一个 Emby 服务器；多服务器时填 Server ID。 |
| 32051（地址覆盖的帮助） | 默认跟随 Emby 插件；仅为评分查询指定另一台服务器时填写。 |
| 32052（令牌覆盖的帮助） | 与地址覆盖配合；只影响豆瓣评分查询。 |
| 32053（测试连接的帮助） | 检查地址与 API Key，结果显示在通知中。 |

**问题**：32050 说的是"怎么做"，没说"什么情况下才需要做"。
用户看到「服务器 ID」根本不知道这跟自己的场景有没有关系，只会觉得"这是高级用户才碰的东西"。

**改法**：每条都以「不确定就留空 / 默认就够」开头，把判断门槛前置。
Kodi 的帮助条只有 `1130×64`（font24，约两行），必须短。

| id | 建议文案 |
|---|---|
| 32050 | **不确定就留空**。只有装了多台 Emby、要指定其中一台时才填。 |
| 32051 | **默认跟随 Emby 插件，一般不用填**。评分要查另一台服务器时才填地址。 |
| 32052 | 配合上面的地址用；只影响豆瓣评分查询，不影响搜索。 |
| 32053 | 测一下上面的地址和 API Key 能不能用，结果弹通知。 |

英文 po 同步改（`strings.po` 的 en_gb），措辞对齐。

**影响面**：只改语言文件，不动逻辑。改完需重新 `pack` 或直接同步实机（语言文件不进 xbt）。
**回退**：还原 po 即可。

---

### P3-2　设置级别按钮（基础 / 标准 / 高级 / 专家）位置下沉到底部

**现状**（`xml/DialogAddonSettings.xml`，**所有 addon 的设置页共用**）

| 控件 | 坐标 |
|---|---|
| 分类列表 `grouplist id=3` | `left 32, top 115, w 350, h 580` → 底边 **695** |
| 级别按钮 `button id=20` | `left 32, top 712, w 350, h 65` → 底边 **777** |
| 底部按钮行 `grouplist id=9000`（确定/取消/默认） | `left 420, top 797, w 1170, h 65` → 底边 **862** |
| 帮助条 `textbox id=6` | `left 440, top 708, w 1130, h 64` |

**问题**：级别按钮卡在 712，比底部按钮行高 85px，左右两栏的底边不齐
（左边 777 / 右边 862），视觉上像"掉在半空"。

**改法**：把级别按钮的 `top` 从 **712 改成 797**，和右侧按钮行同一水平线；
文字改居中，让 350 宽的按钮在左栏里不偏。

```xml
<control type="button" id="20">
    <left>32</left>
    <top>797</top>          <!-- 712 → 797，与 id=9000 同高 -->
    <width>350</width>
    <height>65</height>
    <font>font26</font>
    <align>center</align>   <!-- 新增：文字在按钮内居中 -->
    <onclick>SettingsLevelChange</onclick>
    ...
</control>
```

**顺带要修的导航**（现在 `<onleft>9000</onleft>` 是错的 —— 9000 在右边）：

| 属性 | 现值 | 建议 |
|---|---|---|
| `onleft` | 9000 | 去掉（左边没东西了），或指向 5 |
| `onright` | 5 | 保持 |
| `onup` | 3 | 保持（回到分类列表） |
| `ondown` | 3 | 保持（循环回列表） |

**副作用**：分类列表底边 695 到级别按钮 797 之间空出 102px。
如果觉得空，可以把列表 `height` 从 580 加到 660（底边 775），
但那样列表能显示更多分类，4 个分类时反而更空 —— **建议先只移按钮，不动列表高度**。

**影响面**：`DialogAddonSettings.xml` 是**所有插件**的设置页模板，
改完 Kodi 内所有 addon 设置页都会变（这正是你要的）。
**回退**：`top` 改回 712、删掉 `<align>center</align>`。

**待你确认一个细节**：截图里红字「专家」落在左栏偏左（x≈130），
如果「在左边居中」指的是**按钮文字居中**，就是上面的写法；
如果指的是**按钮整体在 350 宽里居中**（两侧留白），那 `left` 要改成 `32`、`width` 保持 350 —— 
两者其实等价（按钮已占满左栏）。我按"文字居中"理解。

---

## 未提交改动：建议先递交，但顺序要对

**结论：先递交，而且必须在动 P3 之前递交。** 理由三条：

1. **当前状态是完整的**：皮肤 89 项单测全绿、`audit_skin.py --strict` 全 0；
   helper 101 项全绿。放着不提交，后面改文案/布局会和这些混在一起，又得拆一遍。
2. **不提交会一直滚雪球**：皮肤 12 个文件、helper 12 个文件都停在"改了一半"的状态，
   下次再动任何一处，`git diff` 就没法一眼看出哪条是新改的。
3. **"递交"只是 commit，不 push**（AGENTS.md §5），风险可控，随时能回退。

**但顺序必须是：先修 P0-1，再提交。** 否则等于把"assets 指向不存在的图标"这个 bug
写进历史，回头还得再提一个修复提交。

建议的提交拆分：

| 仓库 | 提交 | 包含 |
|---|---|---|
| helper | ① `fix(addon): assets 指回 resources/` | `addon.xml`（先修 P0-1） |
| helper | ② `feat(settings): 设置页改 4 分类 + 专家级 + 帮助条（0.3.3）` | `resources/settings.xml`、两个 po、`default.py`、`lib/config.py`、`tools/gen_assets.py`、`resources/icon.png`、`tests/test_config.py`、`changelog.txt` |
| helper | ③ `chore: 移除评分同步后台服务` | `D service.py`、`D lib/rating_sync.py`、`docs/contract.md` |
| 皮肤 | ④ `fix(rating): 评分徽标 44px，可见性包进 group` | `xml/Includes.xml`、`xml/Includes_DialogVideoInfo_Hero.xml`、`tools/test_skin_settings.py` |
| 皮肤 | ⑤ `fix(addon): 插件图标补 Art(thumb) 兜底` | `xml/Variables.xml` |
| 皮肤 | ⑥ `docs: 同步 1.5.1 状态与 helper 0.3.3` | 7 个 md + `changelog.txt` |

②③ 也可以合成一个（都是 0.3.3 的收尾），看你想不想让"移除后台服务"单独留痕 ——
我倾向**合并**，因为 service 删除和 settings 重构是同一批工作。

---

## 专项：你截图里的两个现象

### ① 「专家 和其他模式一样，设置少了很多」

**先给结论：少了 4 项是 0.3.3 有意删的，不是 bug。**

helper `changelog.txt` 0.3.3 段原文：

> `[调整]` 移除评分同步：写库无消费方；插件图标改为方角

被删的 4 项来自 0.3.0：优先 Emby 评分、同步开关、同步间隔、立即同步。
现在 settings.xml 剩 **10 项 / 4 分类**，和截图完全对得上。

**但「专家级别下看不到那 5 项」这条要单独查。** 当前 settings.xml 的级别分布：

| 级别 | 项 |
|---|---|
| `<level>0</level>`（基本，永远可见） | `test_connection`、`douban_enabled`、`douban_prefer_emby`、`debug_log`、`clear_cache` |
| `<level>3</level>`（专家） | `server_id`、`emby_url_override`、`emby_token_override`、`page_size`、`cache_ttl` |

截图里 Emby 服务器分类**只有「测试 Emby 连接」** —— 这是 level 0 的那一项，
说明当时**不是专家级**（Kodi 的级别按钮显示的是当前级别，点一次升一级、循环）。

**验证方法**（30 秒，不用改代码）：

1. 进设置页，点左下角按钮直到显示「专家」；
2. **退出设置页再重进**（Kodi 的 addon settings 级别切换偶尔不实时刷新）；
3. 看 Emby 服务器分类下是否多出 3 行。

- 多出来了 → 机制正常，只是之前没切到专家，**无需改代码**
- 仍只有 1 行 → 是 Kodi 解析 `<level>` 的问题，改法见下

**如果确认是 bug，修法**：把 5 处 `<level>3</level>` 降成 `<level>2</level>`
（高级就可见，比专家门槛低一档）。改动只有 `resources/settings.xml` 一个文件，
回退就是改回 3。**代价**：这几项（服务器 ID、URL 覆盖、令牌、分页、缓存）本来就偏底层，
降到高级会让普通用户更容易误改 —— 所以我**不建议**先降级，先做上面的验证。

---

### ② 「icon 的图也不出来」

要分清是**哪个 icon**，两种情况结论完全相反：

| 位置 | 现状 | 是不是 bug |
|---|---|---|
| **设置页左侧分类列表**（截图这个） | Kodi 的 `settings.xml` 里 `<category>` **没有 icon 属性**，`CGUIDialogAddonSettings` 也不会给分类塞图标；皮肤 `NaraSettingsCategoryButton` 模板里也没有 `<icon>` 控件 | **不是 bug，Kodi 原生就这样** |
| **插件浏览器 / 插件详情页的插件图标** | 皮肤未提交改动已经在修：`NaraImgAddonBrowserIcon` / `NaraAddonListItemIcon` 加了 `ListItem.Art(thumb)` 兜底（原来只读 `ListItem.Icon`，而 helper 这类插件往往只有 thumb） | 这是**真 bug，且已修待提交** |
| **插件本身的 icon.png** | 见 P0-1：assets 路径指向了不存在的根目录文件 | **是 bug** |

**如果确实想给设置页分类加图标**（纯观感增强，可选）：

皮肤侧在 `DialogAddonSettings.xml` 的 grouplist id=3 里加 itemlayout，
按分类 label 或序号映射 4 张图标（Emby 服务器 / 搜索 / 豆瓣 / 日志）。
**代价**：4 张新贴图 + 一段 itemlayout；**风险**：label 是本地化字符串，
换语言就匹配不上，只能按**索引**映射（第 1/2/3/4 项），加分类就得同步改。
**我的建议：不做。** 收益是 4 个小图标，代价是给一个随时会变的列表加硬编码。

---

## 建议执行顺序

| 步骤 | 内容 | 预估 |
|---|---|---|
| 1 | **P0-3** 备份后清理实机 helper 目录里的 StrmAssistant 残留 | 5 分钟 |
| 2 | **P0-1** helper `addon.xml` 的 assets 改回 `resources/` | 1 分钟 |
| 3 | 递交 helper（合并成 1 个提交：settings 重构 + 移除 service） | 1 个提交 |
| 4 | 递交皮肤（3 个提交：评分 / 图标兜底 / 文档） | 3 个提交 |
| 5 | **同步皮肤到实机**（实机 1.4.1 → 1.5.0+），这是你现在最该做的一步 | 1 分钟 |
| 6 | 实机验证「专家级别」（切到专家 → 退出重进设置页） | 30 秒 |
| 7 | **P3-2** 级别按钮 `top 712 → 797` + 文字居中 + 修导航 | 1 个提交 |
| 8 | **P3-1** Emby 服务器四条帮助文案改写（中英 po） | 1 个提交 |
| 9 | P1 文档失真（helper HANDOVER 还写着 0.2.2） | 1 个 docs 提交 |
| 10 | 发版：皮肤 1.5.1 + helper 0.3.3（**要你明确说"发版"才做**） | — |

> 7 和 8 可以合成一个"设置页体验"提交，也可以分开 —— 它们改的是两个仓库，
> 物理上没法合并，只能各自提交。

---

## 不建议做的

| 项 | 理由 |
|---|---|
| 给设置分类硬编码图标 | 见上，收益低、维护成本高 |
| 把 `<level>3</level>` 直接降到 2 | 先验证再说；降级会让底层参数暴露给普通用户 |
| 删除 `docs/` 下的历史文档 | 它们是决策留档，删了以后无法追溯"为什么当初不做" |
| 把 helper 塞进皮肤包 | Kodi 不允许 skin addon 携带可执行脚本，这是硬约束 |
| 给皮肤加 `script.mistuary.helper` 硬依赖 | 没装插件的用户会整个皮肤加载失败，必须保持软探测 |
