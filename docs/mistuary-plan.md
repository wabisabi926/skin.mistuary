# Mistuary 改名 / 设置梳理 / 缺陷清单

> **历史文档（2026-10-23）。** 记录的是当时的改名计划与缺陷盘点，部分条目已经修掉，
> 保留是为了留决策过程。当前状态请看 `README.md` 与 `docs/fix-plan.md`。
> 已解决（2026-10-26 复核）：`autoscroll` 大小写（现写入/读取均为小写）、
> `$VAR` 做文字颜色（已改为颜色名 + 主题）、海报圆角蒙版（已改为实色角部遮盖）、
> 字体缺失（已补 `fonts/Inter-Unicode-Regular.ttf`）、`ChannelManagerList` 缺 `<definition>`。
> 日期：2026-10-23（2026-10-26 标注状态）

---

## 一、addon.xml（已改）

```xml
<addon id="skin.mistuary" name="Mistuary" version="1.0.0" provider-name="wabisabi926">
```

保留未动：`xbmc.gui 5.17.0` 依赖、8 条 `<res>`（与官方 Estuary 完全一致，删掉反而会丢分辨率匹配）、
license、assets 路径。

重写的部分：

| 字段 | 处理 |
| --- | --- |
| summary / description（en + zh） | 按皮肤实际特性重写：深色玻璃、视频优先、**不依赖魔改内核**（官方 Kodi 21+ / CoreELEC）、可折叠演员栏、设置中心 |
| disclaimer | 保留"省略天气/电台/游戏"的说明 |
| `<source>` | 暂时仍指向 Estuary 上游（代码来源），已加 TODO 注释，等你给仓库地址后替换 |
| `<forum>` | 仍是 forum.kodi.tv 通用链接，有专帖再换 |

**待你确认**：原作者 phil65 / Ichabod Fletchman 是否要保留在描述或 `THIRD_PARTY_NOTICES.md` 里。
我的建议是**保留署名**（Estuary 是 CC BY-SA 4.0，要求保留署名），在 THIRD_PARTY_NOTICES 里加一段
"Derived from Estuary (phil65, Ichabod Fletchman)" 即可，addon.xml 的 provider-name 写你自己。

---

## 二、改名落地步骤（确认后我一次性做完）

改 addon id 不是改一行字，配套要做 5 件事，**任何一件漏掉都会让 Kodi 掉回 Estuary**：

1. **目录改名**
   `D:\下载\AI\skin.estuary.nara-RC1` → `D:\下载\AI\skin.mistuary`
   Kodi 的 addon 路径与 addon id 必须一致，否则升级/回滚/依赖解析会乱。
2. **部署路径改名**
   `Kodi\addons\skin.estuary.nara-RC1` → `Kodi\addons\skin.mistuary`（robocopy 目标一起改）
3. **皮肤设置迁移**
   `Kodi\userdata\addon_data\skin.estuary.nara\settings.xml` → `...\skin.mistuary\settings.xml`
   不迁移的话，你现有的首页布局、小组件开关、玻璃模式等设置**全部丢失**。
4. **活动皮肤指向**
   `guisettings.xml` 里 `lookandfeel.skin` 从 `skin.estuary.nara` 改成 `skin.mistuary`；
   或者改完后手动进 设置 → 界面 → 皮肤 重新选一次（推荐后者，避免改配置文件时 Kodi 正在运行把改动覆盖掉）。
5. **品牌串收尾**
   `language/*/strings.po` 头部注释、3 条 "…not available in Estuary N." 文案、`changelog.txt`、`README.md` 标题。

版本号：`4.2.0` → `1.0.0`（新身份重新起算），changelog 加一条改名记录。

**风险**：如果只改 addon.xml 不改目录名，Kodi 会把它当成"另一个 addon"装在旧路径下，
而 `lookandfeel.skin` 还指着旧 id，重启就回退到 Estuary —— 这次我只改了源码里的 addon.xml，
**没有同步到实机**，就是为了避免这个。

---

## 三、皮肤设置梳理（16 项 / 4 类）

设置窗口分 4 页：外观、主菜单项、艺术图片、屏幕菜单式调节。

| 设置 | 分类 | 状态 | 建议 |
| --- | --- | --- | --- |
| 自动滚动 `autoscroll` | 外观 | ❌ **无效** | 见缺陷 1，改大小写即可 |
| 玻璃面板透白 `nara_glass_light` | 外观 | ⚠️ 半残 | 见下文"透白模式" |
| 媒体库封面文件夹 `library_art_folder` | 外观 | ✅ 可用 | 保留，但依赖"文件名=媒体库标题"，建议加说明 |
| 显示媒体标识 `hide_mediaflags` | 外观 | ✅ 可用 | 保留 |
| 评分样式 `circle_rating` / `circle_userrating` | 外观 | ✅ 可用 | 保留 |
| 电影标题格式 `OriginalTitleFormat_*` | 外观 | ✅ 可用 | 保留 |
| 主菜单：电影 / 电视剧 / 音乐 / 电视 | 主菜单项 | ✅ 可用 | 保留 |
| 编辑小组件 ×4（进入 1101 窗口） | 主菜单项 | ✅ 可用 | 保留 |
| 默认打开方式：电影系列 / 电视剧 / 音乐专辑 | 主菜单项 | ✅ 可用 | 保留 |
| 显示媒体背景图为背景 `no_fanart` | 艺术图片 | ✅ 可用（33 处引用） | 保留 |
| 音乐电视显示海报 `show_musicvideoposter` | 艺术图片 | ✅ 可用 | 保留 |
| 自动关闭视频 OSD + 时间 | 屏幕菜单式调节 | ✅ 可用 | 保留 |

### 需要清理的

1. **首页文件快捷方式 `Home.FileShortcut.1..8`** —— 只读不写。
   `Includes_Home.xml` 里 8 个槽位读 `Skin.String(Home.FileShortcut.N.Label/Path/DisplayPath)`，
   全皮肤**没有任何写入入口**（只有右键 `Skin.Reset(...Path)` 能清空）。
   结果：首页这一行永远是空的，功能等于不存在。
   → 二选一：补"添加文件快捷方式"（`Skin.SetFile` + 自动填 Label），或者整段删掉。
2. **`MyWeather.xml`** —— 天气已从导航移除，窗口文件还留在包里（1000+ 行死代码）。
   → 删。
3. **PGS 自动选择提示**（`Includes_VideoOSD.xml` 的 `NaraPgsSuccessContent` /
   `NaraPgsSuccessNotifications`）—— 依赖魔改内核的 `VideoPlayer.PgsAutoSelectionStatus`，
   官方 Kodi 里这个 info 不存在，两个文案 70198/70199 也不存在。
   → 整块删（10 处引用）。

### 透白模式怎么办

根因：皮肤正文/标题都是 `text_primary`（纯白），玻璃一白就是白底白字。
现在把白色不透明度压到 ≤30% 只是"能用"，观感其实是"淡一点的深色玻璃"，和名字对不上。

**现状盘点（透白模式下每档的白度）**

| 档位 | 深色 | 浅色 | 谁在用 |
| --- | --- | --- | --- |
| `GlassTint_clear` | 30% 黑 | 10% 白 | （暂无引用） |
| `GlassTint_regular` | 40% 黑 | 15% 白 | 首页卡片、动作栏、搜索、TextViewer、音乐弹窗、列表视图 |
| `GlassTint_frosted` | 50% 黑 | 20% 白 | FileManager、电源菜单、通用对话框框体 |
| `GlassTint_dialog` | 75% 黑 | **25% 白** | 插件详情页、插件设置页、AddonBrowser、设置主页、分类页、EventLog、Profiles、系统信息 |
| `GlassTint_dialog_strong` | 90% 黑 | **30% 白** | 上下文菜单、媒体库侧边栏（432 宽那个） |

所以"过透"的不是个别页面，是**所有面板都只有 10%~30% 白**，因为它们头顶上压着白字。

**为什么不能简单调高**：Kodi 没有背景模糊，面板只能靠"不透明度"遮住底下的内容。
白度 ≥ 80% 才能盖住，但那时白字就消失了 —— 这就是上次白屏的成因。

**技术上可行的正解**：Kodi 的 `CGUIInfoColor::Parse` 支持 `$VAR[...]`
（已核对源码：`StringUtils::StartsWithNoCase(label, "$var[")` 分支），
所以把 `textcolor="text_primary"` 换成 `textcolor="$VAR[NaraTextPrimaryVar]"`，
浅色模式下这个变量返回深墨色，就能做到"面板白 + 文字黑"。
代价是要动 **666 处文字色 + 113 处焦点色**，而且首页/视图/详情页的文字直接压在
fanart 上（没有面板），浅色模式还得给这些区域补一层浅色遮罩，否则黑字压在暗背景上同样看不见。

三个选项：

- **A（最省事）** 删掉这个开关，皮肤定位就是"深色电影感"。
- **B（真正修好）** 分三批做完整浅色主题：① 对话框族（插件详情/插件设置/上下文菜单/侧边栏/AddonBrowser/设置页，约 170 处）
  ② 视图与列表 ③ 首页与详情页 + 浅色遮罩。每批都能单独验收。
- **C（折中）** 只做 ①，面板变实、文字变深；首页/视图仍是深色 —— 会出现"半浅色"的割裂感。


---

## 四、"之前说会有些功能失效"——文档在哪

有三份，都在仓库里：

1. **`README.md` 顶部对照表**（最直接的一份）：明确写了 7 类扩展标签在通用版里"已全部移除或降级"。
2. **`changelog.txt` 的 4.2.0「通用化」小节**：逐条列出降级方案。
3. **`.workbuddy-ai/memory/2026-10-23.md`**：改造过程的诊断记录（哪个文件、多少处）。

用户能感知到的损失，按影响排序：

| 丢失的能力 | 现在的样子 |
| --- | --- |
| 玻璃模糊/折射（`material="glass"` 全套） | 纯色半透明，**没有背景模糊**，暗背景上接近纯黑 |
| 内核级圆角（`cornerradius` 等 222 处） | 9-slice 圆角贴图；**图片/海报本身不能圆角**（只能靠描边环+角部遮盖暗示） |
| slotlist 3D 排列 | 降级 fixedlist，海报墙没有"选中放大、两侧缩小"的景深过渡 |
| 稳定选中项 `ListItemSettled` | 快滚时背景跟着焦点实时跳变（原来有延迟稳定） |
| `ImageChange` / `Follow` 动画 | 图片切换、控件联动动画消失 |
| `SkinExtended.xml` 扩展交互 | 详情页/播放/文件管理的定制行为回退原生 |
| `<content playbacktarget / checkautoplaynextitem / loaditemdetails / focusplaying>` | "播放目标预览""自动播放下一集"等行为回原生 |
| `holdscrollmaxspeed` / `holdscrolltargettime` | 长按方向键的加速曲线回 Kodi 默认 |

这些不是 bug，是移植的必然代价。**如果要补，只有"没有模糊"和"海报不能圆角"值得补**：
前者可以预先渲染模糊底图（性能开销大），后者只能改设计（描边环方案已经在用）。

---

## 五、缺陷清单

### P0 — 功能是坏的

1. **"自动滚动"开关无效**
   写入端 `Skin.ToggleSetting(autoscroll)`（全小写），读取端 `Skin.HasSetting(AutoScroll)`（驼峰），
   共 20 处引用。Kodi 的皮肤设置是**大小写敏感**的字符串匹配（`CSkinSettings` 按 name 精确查），
   所以读端永远拿到空值 → 开关怎么点都没反应。
   修法：把 20 处读取改成 `autoscroll`（写入端不动，因为你现有设置文件里存的就是小写）。

2. **PGS 自动选择提示是死代码**（见"清理项 3"）

3. **首页文件快捷方式无法使用**（见"清理项 1"）

### P1 — 能用但不干净

4. `MyWeather.xml` 孤儿窗口（死文件）
5. `DialogMusicInfo.xml` 里 `id="130"` 定义了两次 —— 两个按钮在互斥的 visible 组里，
   实际只会有一个可见，所以不出错，但属于隐患，建议改 id。
6. 点演员头像会触发 `script.embuary.info` 的安装提示 —— 这个插件你本机没装。
   要么装它（能看演员作品），要么把点击行为改成 noop。
7. 43 个 include 定义疑似没被引用（`NaraDialogInsetTexture`、`SongsListLayout`…）。
   注意：多数是通过 `content="$PARAM[...]"` 动态引用的，**不能盲删**，需要逐个人工确认。

### 已修复（今天）

- 演员开关点击无效（属性挂错窗口 → 统一挂 home）
- 演员开关焦点不可达（grouplist 匿名 group 的导航链失效 → 显式 onright）
- 插件详情页 90% 黑 / 插件设置 60% 透 → 统一 75%
- 透白模式下插件详情页、上下文菜单白屏 → 白色不透明度压到 30%
- 演员图标重画（三人）

### 静态自检结果（`extras/audit_skin.py`，可随时重跑）

```
文件 126 个 XML 全部解析通过
缺失 include / 变量 / 字体 / 贴图：0
缺失皮肤字符串：3（70127 只在注释里，70198/70199 属于 PGS 死代码）
残留魔改内核属性：0（命中的全是注释）
```

---

## 六、建议顺序

1. 先定 addon.xml 的署名/仓库地址 → 一次性做改名（目录 + 设置迁移 + 部署路径）
2. 修 `autoscroll` 大小写（1 分钟，立刻见效）
3. 删 PGS 死代码 + `MyWeather.xml`（减包体，去隐患）
4. 首页文件快捷方式：决定"补功能"还是"删代码"
5. 透白开关：A / B / C 选一个
6. 最后再考虑"海报圆角""背景模糊"这类视觉补课
