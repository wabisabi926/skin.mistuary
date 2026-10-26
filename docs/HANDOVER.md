# 交接说明（2026-10-26）

> 给接手的人看。这一轮把外部审查报告（`docs/skin.mistuary.md`）里的问题全部修完，
> 另外补了三个报告没发现的缺陷。代码已提交在 `universal`（**未 push、未合 main**），
> 已同步实机并在 Kodi 22.0-RC1 上验证通过（见 §5），**尚未发版**。

---

## 1. 一句话现状

皮肤 `skin.mistuary`（Kodi 皮肤，基于 Estuary 魔改）现在**同时支持 Kodi 21 和 22**，
字体自带中文字形，PVR 分组管理器恢复可用，首页文件源跳转修好，
`xbt_tool.py` 的解包路径穿越堵上，发布流水线只在真升版本时打包。
剩下的是**功能取舍决策**，不是 bug。

---

## 2. 环境与路径

| 项 | 值 |
|---|---|
| 源码 | `D:\下载\AI\skin.mistuary`（分支 `universal`，与 `origin/main` 同源） |
| 实机皮肤目录 | `C:\Users\liwl\AppData\Roaming\Kodi\addons\skin.mistuary` |
| 实机 Kodi | **22.0-RC1**（build version code `21.90.901`，build 20260927） |
| 日志 | `C:\Users\liwl\AppData\Roaming\Kodi\kodi.log` |
| Python（带 Pillow） | `C:\Users\liwl\AppData\Local\Programs\Python\Python312\python.exe` |
| 贴图打包 | `python xbt_tool.py pack`（662 张 → 7.6 MB） |

> 实机 Kodi 会随用户升级而变（BETA2 → RC1 就是一次）。看版本别看本文档，
> 看 `kodi.log` 首行：`Starting Kodi (22.0-RC1 (21.90.901) Git:...)`。

**部署命令**（改完代码必须同步，用户靠这个实机验证）：

```powershell
$src = "D:\下载\AI\skin.mistuary"
$dst = "C:\Users\liwl\AppData\Roaming\Kodi\addons\skin.mistuary"
robocopy $src $dst /MIR /XD .git .workbuddy-ai __pycache__ /XF *.pyc .gitignore /NJH /NJS /NDL /NP /NFL
```

- 退出码 0–7 都算成功；`/MIR` 会删掉目标端多余文件（包括本地的 `build/`）。
- **不要写成 .ps1/.bat 脚本文件**（源码路径含中文，脚本编码会出问题），直接执行命令。
- 贴图改过要重新 `pack` 并重启 Kodi；只改 XML 也要重启（皮肤在启动时加载）。

---

## 3. 本轮改了什么（按文件）

### 3.1 新增文件

| 文件 | 作用 |
|---|---|
| `fonts/Inter-Unicode-Regular.ttf` | UI 字体，Inter 4.000 + 16502 汉字，OFL 1.1，4.94 MB |
| `fonts/OFL.txt` | 上面字体的授权全文 |
| `extras/gen_techflag_vars.py` | 从 `<map>` 生成 Kodi 21 可用的条件 `<variable>`；`--check` 供 CI |
| `extras/test_xbt_tool.py` | XBT 解包边界测试（10 条：路径穿越/绝对路径/畸形容器） |
| `extras/test_skin_settings.py` | 皮肤设置读写配对测试（7 条），锁住"11 个写入内置函数都算写入" |
| `docs/fix-plan.md` | 审查报告的核验结论 + 全部修复方案与实施记录（**主文档**） |
| `docs/skin-contracts.md` | 窗口属性 / 皮肤设置 / 控件 ID 的隐式契约清单 |
| `docs/HANDOVER.md` | 本文件 |

### 3.2 修改文件

| 文件 | 改了什么 |
|---|---|
| `addon.xml` | `<license>` 追加 SIL OFL 1.1。**`xbmc.gui` 仍是 5.17.0（继续支持 21）** |
| `xml/Font.xml` | 47 处 `<filename>` → `Inter-Unicode-Regular.ttf`（原来是 `inter.ttf`，文件不存在） |
| `xml/Includes.xml` | 新增 `<expression name="nara_kodi21">String.StartsWith(System.BuildVersion,21)</expression>` |
| `xml/Includes_VideoTechnicalFlags.xml` | 胶囊改**双按钮**（`$MAP` 给 22 / `$INFO` 原值给 21），5 个调用点补 `flag_label_raw` |
| `xml/Includes_VideoOSD.xml` | 两处 `$MAP` 改 `$VAR[NaraTechHdrPlayer]` / `NaraTechAudioPlayer`（标签名写死，两版都有友好名称） |
| `xml/Variables.xml` | 生成器写入 5 个 `NaraTech*Player` 变量（在 BEGIN/END 标记区间内，勿手改） |
| `xml/Includes_PVR.xml` | `ChannelManagerList` 补 `<definition>` + 5 个参数默认值（原来整条 include 被 Kodi 丢弃） |
| `xml/DialogPlayerProcessInfo.xml` | `System.CurrentDisplayMode`（不存在的标签）→ `System.ScreenMode` |
| `xml/Home.xml` | 删掉文件源卡片的失效 `onclick`；整块删除「常用文件夹」8 槽位（panel 15020 + 标题 + 导航 + 返回焦点分支） |
| `xml/Includes_Home.xml` | 删除 `HomeFileShortcutItems`、`HomeFolderCardLayout`；`HomeFocusedFilePathVar` 去掉 15020 分支 |
| `extras/audit_skin.py` | 重写：注释不再误报、字符串只查 31000–31999、真错误返回 1、新增 22 专属写法检查；**新增皮肤设置读写配对统计**（覆盖 11 个写入内置函数） |
| `extras/test_nara_search_navigation.py` | 过时断言 `$VAR[GlassTint_regular]` → `glass_regular` |
| `extras/test_nara_settings_navigation.py` | 焦点回归用例去掉已删除的 15020 |
| `xbt_tool.py` | 加 `_safe_target()` + `_need()` 边界检查 + 尺寸/解压量上限 |
| `.github/workflows/release.yml` | 版本判断改比 `github.event.before` + Release 幂等闸门；`rsync` 排除 `build/`；`pillow==11.3.0`；新增 `test` job，`build` 依赖它 |
| `README.md` | 新增「Kodi 21 与 22 的差异」表 |
| `changelog.txt` | 1.0.0 段补修复/发布/清理条目 |
| `THIRD_PARTY_NOTICES.md` | 新增 Inter 字体章节（来源/版本/授权/重建方法） |
| `docs/mistuary-plan.md` | 顶部标注为历史文档，列出已解决项 |

---

## 4. 关键事实（省得重新翻源码）

### 4.1 字体

- **Kodi 没有字形级回退**。`GUIFontManager::LoadTTF` 按文件名找一个**完整文件**：
  皮肤 `fonts/` → `special://home/media/Fonts` → `special://xbmc/media/Fonts` → `resource.font.*` 插件。
  缺字不会去别的字体借，所以皮肤字体文件必须自带 CJK。
- Kodi 自带的 `arial.ttf`（4.6 MB）实际是 **DejaVu Sans 2.32 + 16502 汉字**，不是 Windows Arial。
- 粗体由 FreeType 的 `FT_Outline_Embolden` **合成**（`GUIFontTTF.cpp:973`），
  所以 47 个字体全指向一个 Regular 文件时 `[B]` 依然会变粗，**不需要 Bold 文件**。
- **字体文件名用原始名，不要缩写**（用户明确要求）。

### 4.2 Kodi 21 / 22 差异

- `$MAP[]` / `<map>` 是 **22 才有**（commit 2026-07-27 进 master）。21 的
  `CGUIInfoLabel::Parse` 只认 `$INFO/$ESCINFO/$VAR/$ESCVAR`，未知写法会**原样显示成文本**。
- 13 个标签也是 22 才有：`ListItem.HdrDetail`、`VideoPlayer.HdrDetail`、`ListItem.ChannelLogo`、
  `MediaProviders`、`PVRClientName`、`PVRInstanceName`、`PVRGroupOrigin`、
  `DecodedFileNameAndPath`、`TitleExtraInfo`、`EpisodePart`、`VideoPlayer.SubtitleCodec`、
  `SubtitleName`、`AudioLanguageEx`、`SubtitleLanguageEx`。
  21 上都是空，但都被 `!String.IsEmpty` 保护 → 只是那一行/那个胶囊不出现。
- **标签名总表在 `xbmc/GUIInfoManager.cpp`（不在 `guiinfo/` 下）**。
  比对方法：拿 `21.2-Omega` 和 `master` 各一份，`grep '"labelname"'` 求差集。
- `String.IsEqual` 用的是 `EqualsNoCase`，**大小写不敏感**。
- `System.BuildVersionCode` 在 22 里**被删了**，只能用 `System.BuildVersion`（字符串）。
  22 新增的标签在没数据时也是空，**无法用"标签是否为空"探测版本**，只能用主版本号。
- **别被 `21.90.901` 骗了**：22.0-RC1 的日志首行是
  `Starting Kodi (22.0-RC1 (21.90.901) Git:...)`，那个 `21.90.901` 是
  `CCompileInfo::GetVersionCode()`（构建版本号），只出现在括号里。
  `System.BuildVersion` 取的是 `GetVersionShort()`，返回 **`22.0-RC1`**——
  以 `22` 开头，所以 `String.StartsWith(System.BuildVersion,21)` 在 22 上判为假，
  双轨渲染走 `$MAP` 分支，**判断是对的**。（`GetVersion()` 才是
  `短版本 + " (" + code + ")" + " Git:" + hash`，同样以 `22.0-RC1` 开头。）

### 4.3 为什么 21 兼容要用"双轨渲染"

技术标识的标签名是**动态**的（`Container($PARAM[list_id]).ListItem`，实测 20+ 个前缀），
而 `<variable>` 的 `<value>` 只能写死标签名。按前缀生成要 2000+ 行且每加 widget 都要重生成。
所以：**标签名静态的地方用变量（两版都友好），动态的地方用双轨（22 用 `$MAP`、21 用原值）**。

### 4.4 其他踩过的点

- `<include>` 有 `<param>` 却**没有 `<definition>`** → Kodi 整条丢弃并告警（`GUIIncludes.cpp:221-227`）。
  参数本身**不声明也能用**，调用点传的值会和默认值合并。
- grouplist 布局会跳过隐藏子控件（`GUIControlGroupList` 里 `if (!control->IsVisible()) continue;`），
  所以双按钮方案不会留空位、也不进焦点链。
- `content target="X"` 是有效导航：`CDirectoryProvider::GetTarget()` 用条目**真实路径**跳转
  （保留 SMB 凭据）；`ListItem.FolderPath` / `FileNameAndPath` 都会 `GetWithoutUserDetails()` 掉凭据。
- 皮肤的语言文件在**根目录 `language/resource.language.xx/strings.po`**（不是 `resources/language/`，
  那是普通插件的位置）。皮肤自有字符串区间是 **31000–31999**。
- 皮肤设置名**大小写敏感**（踩过 `autoscroll` / `AutoScroll`）。
- 对话框里的开关用 `Skin.ToggleSetting` / `Skin.HasSetting`，不要用 `Window.Property`。

### 4.5 皮肤设置：写入内置函数有 11 个，别只认 SetString

**判断"某个设置有没有写入入口"时，必须搜全下面这一组**，否则会得出错误结论：

| 写入内置函数 | 说明 |
|---|---|
| `Skin.SetBool(name[,value])` | 置真/置假 |
| `Skin.SetString(name[,value])` | 无 value 时弹键盘输入 |
| `Skin.SetNumeric(name)` | 弹数字输入框 |
| `Skin.SetPath(name[,value])` | 选目录 |
| `Skin.SetAddon(name,type)` | 选附加组件 |
| `Skin.SetImage` / `SetFile` / `SetColor` | 选图 / 选文件 / 选颜色（v20+） |
| `Skin.ToggleSetting(name)` | 取反 |
| `Skin.Reset(name)` | 恢复默认（**没有 `Skin.Unset`**，用这个） |
| `Skin.SelectBool(header, 标签\|设置名, …)` | **单选互斥**：选中项置真、同组其余全部置假；取消则全不变 |

`Skin.SelectBool` 特别容易漏——它把设置名藏在 `数字\|设置名` 的配对里，
按 `Skin.Set` 前缀搜是搜不到的。2026-10-26 的交接就是因此把 15 个设置
误判成"只读、永远停在默认值"，实际它们全都能改。

两个容易踩的实现细节：

- **`Skin.SetNumeric` 在源码里没有调 `Settings()->Save()`**（其它写函数都调了）。
  目前只影响 `OSDAutoCloseTime`：值会进内存，正常退出 Kodi 时照样落盘，
  但**非正常结束（崩溃/强杀）可能丢**。介意的话可以在设置项后面接一个
  `Skin.ToggleSetting(...)` 之类的调用触发保存。
- 选择器类函数（`SetImage`/`SetFile`/`SetColor`/`SetNumeric`）都是同样情况。

`extras/audit_skin.py` 现在会统计读写配对并打印"有读无写 / 有写无读"，
`extras/test_skin_settings.py` 把"每种写入内置函数都算写入"钉成了用例。

---

## 5. 验证（现在就能跑）

```bash
cd /d "D:\下载\AI\skin.mistuary"
set PY="C:\Users\liwl\AppData\Local\Programs\Python\Python312\python.exe"

%PY% -m unittest discover -s extras -p "test_*.py"     # 期望 35 项全绿
%PY% extras/audit_skin.py --strict                      # 期望 EXIT=0
%PY% extras/gen_techflag_vars.py --check                # 期望"与 map 同步"
%PY% xbt_tool.py unpack media/Textures.xbt -o %TEMP%\xbt_check   # 期望 662/662
```

实机检查（重启 Kodi 后）：

```bash
grep -c "LoadTTF: Couldn't load" %APPDATA%\Kodi\kodi.log        # 期望 0（改之前 3525）
grep -c "invalid include definition" %APPDATA%\Kodi\kodi.log    # 期望 0
```

> **陷阱：同步完必须重启 Kodi，否则日志骗人。**
> 2026-10-26 那次部署（10:51）时 Kodi 从 09:59 就在跑，`kodi.log` 里一直是旧的
> 94 条字体错误 + 2 条 include 错误，看起来像"没修好"，其实只是运行时还在用旧皮肤。
> 11:35 重启后两项立刻归零。
> 判断方法：`kodi.log` 首行的 `Starting Kodi` 时间必须**晚于**部署时间。

**实测结果（2026-10-26 11:35 重启，Kodi 22.0-RC1）**：

| 检查项 | 结果 |
|---|---|
| `LoadTTF: Couldn't load` | **0**（修复前 3525） |
| `invalid include definition` | **0**（修复前 2，均为 `ChannelManagerList`） |
| 单元测试 | **42 项全绿** |
| `audit_skin.py --strict` | 退出码 **0**；缺失 include/变量/字体/贴图/字符串全 0；皮肤设置 66 读 / 68 写，有读无写 0、有写无读 0 |
| `gen_techflag_vars.py --check` | 与 map 同步 |

日志里剩余的无害噪声（不用管）：

- `libraryart/<分类名>.png` 加载失败 —— 皮肤按"先 png 后 jpg"试两种扩展名，
  而 `libraryart/` 里只有 jpg，所以每个分类必然报一条 png 缺失，jpg 正常。
  只有 `临时` 是连 jpg 都没有（用户自己的分类没配封面）。
- `special://masterprofile/Thumbnails/...` 失败 —— Emby 插件缩略图，与皮肤无关。
- `EMBY.emby.http: Websocket receive interrupted` —— 网络，与皮肤无关。

1. 字体变成 Inter（中文正常、粗体正常）
2. PVR → 分组管理，左右两个频道列表都能出频道
3. 首页「文件」里点不同文件源卡片，进对应目录（配两个源测）
4. 播放中按 `O`，「显示输出」那行有值（`System.ScreenMode`）
5. 详情页技术标识：22 上 `4K UHD` / `DOLBY VISION`；21 上 `4K` / `DOLBYVISION`，
   **不能出现 `$MAP[` 原文**

想在 21 上验：装个 **Kodi 21.2 便携版**（解压即用，不动现有配置），
把皮肤拷到它的 `portable_data/addons/` 下跑一遍。

---

## 6. 待办 / 需要决策

### 6.1 已澄清：不存在"15 个只读设置"

上一版交接留了一个待决策项，说 `circle_rating`、`album_onclick_*`、`tvshow_onclick_*`、
`movieset_onclick_*`、`OriginalTitleFormat_*`、`OSDAutoCloseTime`、`library_art_folder`、
`LyricScript_Path` 这些"有读取、全仓库无写入入口，永远停在默认值"。

**这个结论是错的**，2026-10-26 已核实推翻。它们全都有写入入口：

| 设置 | 写入点 | 内置函数 |
|---|---|---|
| `circle_rating` / `circle_userrating` | `SkinSettings.xml:59` | `Skin.SelectBool` |
| `movieset_onclick_*` | `SkinSettings.xml:138` | `Skin.SelectBool` |
| `tvshow_onclick_*` | `SkinSettings.xml:168` | `Skin.SelectBool` |
| `album_onclick_*` | `SkinSettings.xml:198` | `Skin.SelectBool` |
| `OriginalTitleFormat_*` | `SkinSettings.xml:68` | `Skin.SelectBool` |
| `OSDAutoCloseTime` | `SkinSettings.xml:250` | `Skin.SetNumeric` |
| `library_art_folder` | `SkinSettings.xml:41` | `Skin.SetPath` |
| `LyricScript_Path` | `Includes_SettingsDialog.xml:242` | `Skin.SetAddon` |

入口也都在可达 UI 里：设置中心（`skinsettings`）的 4 个侧边栏页面
（第 1/2/4 页），歌词插件在设置对话框里。

误判原因只有一个：**排查时只搜了 `Skin.SetString` / `Skin.ToggleSetting`**，
漏了 `SelectBool`（设置名藏在 `数字|设置名` 配对里）、`SetNumeric`、`SetPath`、`SetAddon`。
完整的 11 个写入内置函数见 §4.5——以后判断"有没有写入入口"照那张表搜。

现状：`audit_skin.py` 报 **66 读 / 68 写，有读无写 0、有写无读 0**。

### 6.2 剩余待办

| 项 | 说明 | 建议 |
|---|---|---|
| **action 钉 SHA** | `release.yml` 用 `checkout@v4`、`setup-python@v5`、`action-gh-release@v2`，**三个都是 node20 运行时**，而 GitHub 已弃用 node20 | 不只是钉 SHA，建议直接升到 node24 的 `v7.0.1` / `v7.1.0` / `v3.0.3` 再钉（输入参数已核对完全一致，见 §6.3） |
| Kodi 21 实机验收 | 用户决定**暂不测试** | 已做静态核对 + 22.0-RC1 实机；21 上的结论仍是"推断"，README 里的兼容声明未实机验证 |
| git 提交 / 发版 | 改动在 `universal` 上，**未 push、未合 main** | 21 验收不再是阻塞项，可合 main 发 1.0.0 |
| `OSDAutoCloseTime` 落盘 | `Skin.SetNumeric` 不调 `Save()`，非正常退出可能丢值 | 低优先，见 §4.5 |
| `libraryart` 日志噪声 | 皮肤按"先 png 后 jpg"试两种扩展名，而内置目录只有 jpg → 每次启动约 12 条 `Direct texture file loading failed` | 可选：内置目录只留 jpg 分支（用户目录仍保留双扩展名），噪声归零 |

### 6.3 action 版本核查结果（2026-10-26）

| action | 现用 | 运行时 | 最新 | 运行时 | 关键输入是否兼容 |
|---|---|---|---|---|---|
| `actions/checkout` | `v4` | node20 | **v7.0.1** | node24 | `fetch-depth`/`ref`/`repository`/`persist-credentials` 均在 |
| `actions/setup-python` | `v5` | node20 | **v7.1.0** | node24 | `python-version`/`cache`/`architecture` 均在 |
| `softprops/action-gh-release` | `v2` | node20 | **v3.0.3** | node24 | 输入参数表**逐项一致**（18 个全同名） |

钉 SHA 用的 commit（`git ls-remote` 取，`--refs` 之外再取 peeled 避免拿到 tag 对象）：

```
actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1              # v7.0.1
actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0           # v7.1.0
softprops/action-gh-release@efb35369e0ad2afab669f228072c1b0d510eae64    # v3.0.3
```

> `action-gh-release` 的 v3.0.3 是 **annotated tag**：`refs/tags/v3.0.3` 指向 tag 对象
> `e598afbe…`，真正的 commit 是 peeled 的 `efb35369…`。Actions 要用后者。
> 另外两个是轻量 tag，`--refs` 拿到的就是 commit。

---

## 7. 交接注意

- 本轮改动已在 `universal` 分支提交为 **`4f7d90e`**（27 个文件，+1744/−407），
  **没有 push**。接手后先 `git log -1 --stat` 看一眼，确认要不要合到 `main`。
  提交时注意 `fonts/*.ttf` 是二进制（4.94 MB），`libraryart/*.jpg` 被 `.gitignore` 排除（用户自备封面）。
- **不要删 `.workbuddy-ai/`**：里面是项目记忆（`memory/MEMORY.md` 是长期约定，
  `memory/2026-10-26.md` 是本轮全过程），下一个人接手先读这两个文件能省很多时间。
- 记忆文件里已沉淀的约定：字体原始名、双轨渲染方案、首页文件区导航、部署命令、文档索引。
- 改导航/删控件前先看 `docs/skin-contracts.md`（数字 ID 和窗口属性是隐式契约，
  删了不会报错，只会静默失效）。
- 审查报告原文在 `docs/skin.mistuary.md`，**未做任何修改**，留作对照。
