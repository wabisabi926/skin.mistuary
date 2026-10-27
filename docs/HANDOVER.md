# 交接说明（Mistuary 1.1.0）

> 读这个之前先读 `.workbuddy-ai/memory/MEMORY.md`（长期约定）。
> 本文只讲**现状、依赖、工具链、发版**，不讲历史。

---

## 1. 一句话现状

`universal` 分支上的通用版皮肤，**Kodi 21 及以上**可用，版本 **1.1.0**。
功能完整、静态自检全绿、可随时发版。

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

两处都用 `System.AddonIsEnabled()` / `System.HasAddon()` 保护，**没有硬依赖**。
如果以后确实需要随皮肤分发脚本，再单独建 `script.mistuary.*` 依赖插件，
**不要塞进皮肤包**（Kodi 不允许 skin addon 携带可执行脚本）。

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
libraryart/     分类封面（按「分类名.jpg」匹配；用户自备，gitignore 除 default.jpg）
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
python tools/gen_techflag_vars.py --check   # 技术标识变量是否与 map 同步
python -m unittest discover -s tools -p 'test_*.py'   # 单元测试
```

CI（`.github/workflows/release.yml`）在发版前会把这三条跑一遍，任一失败就中止。

### 贴图生成器（改了 `media/shapes/` 之后重跑）

| 脚本 | 生成 |
|---|---|
| `gen_glass_plates.py` | `glass<N>.png` 玻璃面板（9-slice，中心实、1px 透明边） |
| `gen_rings.py` | `ring_card_*.png` 描边环（**1:1 整图，不能 9-slice**） |
| `gen_corner_masks.py` | `corner_*.png` 圆角角部遮盖（实色填角外） |
| `gen_music_cover.py` | 音乐播放页兜底封面（黑胶 + 唱臂） |
| `generate_nara_cast_icon.py` | 演员图标 |
| `generate_nara_fanart_mask.py` | fanart 遮罩 |
| `generate_nara_osd_icons.ps1` | OSD 图标（PowerShell） |
| `generate_nara_settings_icons.ps1` | 设置图标（PowerShell） |

**改过 `media/` 一定要重打包**：`python tools/xbt_tool.py pack`（否则实机还是旧图）。

### 手动 UI 测试（PowerShell，需要实机 Kodi）

`test_nara_video_osd.ps1`、`test_nara_music_player.ps1`、
`test_nara_search_navigation.ps1`、`test_nara_settings_navigation.ps1`、
`test_nara_window_ids.ps1`。

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

### 5.3 不透明度（用户可调）

两套主题：`colors/defaults.xml`（透黑）+ `colors/light.xml`（透白，只写差异）。

| 设置项 | 档位 | 影响 |
|---|---|---|
| 浮窗不透明度 | 6 档（62.7%~97.3%，档差 11） | `gd_1..6` 面板 + `sc_1..6` 遮蔽 |
| 页面面板不透明度 | 4 档（45/60/75/88%） | `gp_1..4` |

链路：颜色 token → `NaraGlassDialogTintVar` / `NaraGlassScrimTintVar` /
`NaraGlassPageTintVar` → 43 处 `colordiffuse`。

**播放中的浮窗**（OSD 设置、播放列表、书签、处理信息、流选择）走
`NaraPlaybackDialogTintVar` —— 在用户档位上**下移两档**，合成 72%。

### 5.4 圆角

| 元素 | 半径 |
|---|---|
| 玻璃面板 | **20**（只有 `glass20`） |
| 选中行 / 焦点条 | **14**（只有 `round14`） |
| 胶囊（导航、动作栏） | 接近半高，单独保留 |

**`border` 只给实心填充用。描边环一律 1:1 整图，且必须最后绘制。**

### 5.5 三个反复踩过的坑

1. **`<include condition="X">` 是加载时求值的** —— 按运行时状态切外观只能用
   `<visible>` 或 `$VAR`。曾导致"播放中打开的对话框永远不跟设置"。
2. **panel 不裁剪子控件** —— 想让行尾不露半张卡，必须让"下一张起点 ≥ 1920"。
3. **批量替换先数命中次数** —— 短串（`<left>0</left>`、`start="100" end="112"`）
   往往命中多处，误伤过 PVR 面板和电影 widget 的缩放。

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

Emby for Kodi（`plugin.service.emby-next-gen`，2026-10-27 按已安装版本核对）实际写入的是：

- `CommunityRating` → 类型 **`default`**（不是 `imdb`）：电影 / 剧集 / 单集 / 音乐视频都写
- `CriticRating / 10` → 类型 `tomatometerallcritics`：**只有电影**写（`movies.py` / `videos.py`）
- **不写 `UserRating`**：个人评分圆标（`circle_userrating`）显示的是 Kodi 自己的用户评分
  （`SetRating` 打的星），与影评人分无关。早前"CriticRating 同时写进 UserRating"的记录已过时
- `tmdb` / `metacritic` 类型只有**本地刮削器**（TMDb/Trakt）才会写，Emby 库恒空

因此 Emby 库下：电影最多 2 颗胶囊（默认 + 烂番茄），剧集/单集只有 1 颗。

**豆瓣覆盖**：StrmAssistant（神医助手）的「豆瓣评分覆盖」会把 Emby 的 `CommunityRating`
改写成豆瓣分，同步到 Kodi 后仍是 `default` 类型——Kodi 侧**没有任何来源标志**，
无法自动判断是豆瓣还是 IMDb。皮肤用设置项 `douban_rating`（设置 → 外观 → 默认评分来源）
只切换第一颗胶囊的图标（IMDb ↔ 豆瓣），数值都读 `ListItem.Rating`。

取不到的类型返回空字符串，所以"多列几种类型 + 用 `!String.IsEmpty` 控制可见"是安全的写法。
**不要自己发明标签名**（`ListItem.NaraRating(x)` 这类是魔改内核的，官方 Kodi 恒空）。

## 6. 发版流程

1. 改 `addon.xml` 的 `version`（**必须升**，否则 CI 判定"版本没变"直接跳过）
2. `changelog.txt` 顶部加一段
3. push 到 `universal`
4. `release.yml` 自动：跑测试 → 静态自检 → 打包贴图 → 暂存 → zip → 建 Release

`workflow_dispatch` 可以勾 `force` 强制发同名版本。

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
| 详情页**评分行** | 原来用 `ListItem.NaraRating(<source>)` / `NaraRatingIcon(<source>)`（Estuary N 依赖魔改内核的标签，官方 Kodi 没有）→ 8 个胶囊全部隐藏。**2026-10-27 已改**为标准写法：`ListItem.Rating`（Emby 社区评分）+ `ListItem.Rating(tomatometerallcritics)`（Emby 影评人评分/10）+ `tmdb` / `metacritic`，图标改成每个胶囊写死，取不到的类型自动隐藏 |
| `ListItem.BMP` 拼写错误 | `Includes.xml` 音乐媒体标识里写的是 `BMP`（位图），本意是 `BPM`。Kodi 的标签是 `ListItem.BPM`，现在这个徽标永远不显示 |
| `ListItem.MusicBitsPerSample` 不存在 | Kodi 只有 `MusicPlayer.BitsPerSample`（播放器上下文），列表项没有位深标签 → 该徽标永远不显示 |
| 首页「类别」行的名字 | 显示的是 Emby 插件节点名（`EMBY DYNAMIC: 音乐 (music)`），皮肤层无法截断字符串。要么在 Emby 里改库名，要么补 `libraryart/<新名字>.jpg` |
| 类别行 / 专辑行左边缘 | 差 18px（60 vs 78），用户明确说"不用统一" |
| 专辑卡片长标题 | 卡宽 186，font12 只放得下 8 个汉字；超长靠聚焦时滚动 |
| `tools/universalize.py` | 4.2.0 → 1.0.0 的一次性迁移脚本，已完成使命，留作参考 |

> 上面四条"标签不存在"是拿 Kodi 21.2 与 master 的 `xbmc/GUIInfoManager.cpp` 标签名总表
> 逐条比对 `$INFO[...]` 得出的。**排查同类问题的方法**：把皮肤里所有 `$INFO[X]` 的 X
> 取出来，去掉 `(...)` 参数和 `$PARAM[...]` 前缀，取最后一段，与标签表求差集。
