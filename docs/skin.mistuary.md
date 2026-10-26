# skin.mistuary 代码审查报告

审查日期：2026-10-23  
仓库：[wabisabi926/skin.mistuary](https://github.com/wabisabi926/skin.mistuary)  
分支：`main`  
插件版本：`1.0.0`  
审查提交：[`f7f821edc84184b7ee19cf6d07f91085fff2be7f`](https://github.com/wabisabi926/skin.mistuary/tree/f7f821edc84184b7ee19cf6d07f91085fff2be7f)

## 审查范围与结论

本次检查覆盖主要窗口及公共 XML 组件、主题颜色、语言及贴图资源、XBT 工具、现有测试和发布工作流，并对官方 Kodi 21.2 的相关实现进行了源码对照。审查未修改被审查仓库，也未连接真实媒体服务或执行真实媒体删除。

资源组织、公共组件拆分和现有贴图包完整性较好，XBT 压缩器与系统 LZO 解压器的互操作验证通过。但 README 声明的“未修改的官方 Kodi 21 Omega 及以上版本”兼容性仍有缺口，发布版本判断也存在可复现错误。本报告确认四项 P2 问题：两项运行时兼容问题、一项发布流程问题，以及一项开发工具的归档路径校验问题。

没有可用的 Kodi GUI 或 PowerShell 环境。因此，界面问题依据仓库代码与官方 Kodi 源码确认，未在实机上观察；临时 Git 仓库、XBT 路径穿越、资源一致性和 LZO 互操作检查则已实际执行。报告分别标明验证状态。

严重性定义：

- **P1：高优先级。** 可能导致严重数据损失、越权或核心功能大范围不可用，应优先修复。本次未确认此级别问题。
- **P2：中优先级。** 在明确条件下造成重要功能错误、发布结果不可靠，或有限范围的安全问题，应进入修复计划。

## 1. 逻辑与功能正确性

### F1 · P2：技术信息标签仍依赖官方 Kodi 21 不支持的 `$MAP`

**代码位置：** [Includes_VideoTechnicalFlags.xml:157–173](https://github.com/wabisabi926/skin.mistuary/blob/f7f821edc84184b7ee19cf6d07f91085fff2be7f/xml/Includes_VideoTechnicalFlags.xml#L157-L173)、[编码标签映射:207–211](https://github.com/wabisabi926/skin.mistuary/blob/f7f821edc84184b7ee19cf6d07f91085fff2be7f/xml/Includes_VideoTechnicalFlags.xml#L207-L211)、[Includes_VideoOSD.xml:23](https://github.com/wabisabi926/skin.mistuary/blob/f7f821edc84184b7ee19cf6d07f91085fff2be7f/xml/Includes_VideoOSD.xml#L23)、[音频 OSD:82](https://github.com/wabisabi926/skin.mistuary/blob/f7f821edc84184b7ee19cf6d07f91085fff2be7f/xml/Includes_VideoOSD.xml#L82)。

**触发条件：** 在 README 承诺支持的原版 Kodi 21 上，打开含分辨率、视频/音频编码或 HDR 信息的详情页、视频 OSD。

**原因与影响：** 组件定义 `<map>` 并使用 `$MAP[...]` 读取。但官方 Kodi 21.2 的 includes 加载过程不加载 map；标签解析支持的格式为 `$INFO`、`$ESCINFO`、`$VAR`、`$ESCVAR`，没有 `$MAP`。因此相应表达式会留作普通文字，技术信息无法按预期显示为 `4K UHD`、`DOLBY VISION`、`DOLBY DIGITAL` 等标签。

官方依据：[Kodi 21.2 的 includes 加载入口](https://github.com/xbmc/xbmc/blob/21.2-Omega/xbmc/guilib/GUIIncludes.cpp#L120-L125)、[标签格式表及解析逻辑](https://github.com/xbmc/xbmc/blob/21.2-Omega/xbmc/guilib/guiinfo/GUIInfoLabel.cpp#L252-L337)。本结论针对其明确支持的 Kodi 21，不推定所有未来版本的行为。

**修复建议：** 改用官方支持的条件 `<variable>` 与 `$VAR`；未知编码值通过 `$INFO` 回退。把 `<map>`、`$MAP` 及其他内核扩展纳入兼容性检查，并在官方 Kodi 上验证媒体详情与 OSD。

**验证状态：** 仓库代码与官方 Kodi 21.2 源码对照确认；未运行 Kodi GUI，未宣称实机显示已复现。

### F2 · P2：首页文件源跳转读取不存在的 `homepath` 属性

**代码位置：** [Home.xml:961](https://github.com/wabisabi926/skin.mistuary/blob/f7f821edc84184b7ee19cf6d07f91085fff2be7f/xml/Home.xml#L961)、[文件源列表内容:983](https://github.com/wabisabi926/skin.mistuary/blob/f7f821edc84184b7ee19cf6d07f91085fff2be7f/xml/Home.xml#L983)。相关自定义路径约定见 [Includes_Home.xml:104–112](https://github.com/wabisabi926/skin.mistuary/blob/f7f821edc84184b7ee19cf6d07f91085fff2be7f/xml/Includes_Home.xml#L104-L112)。

**触发条件：** 原版 Kodi 中配置文件源，进入首页“文件”并点击文件源卡片。配置两个不同文件源更容易识别跳转错误。

**原因与影响：** 列表内容来自 `sources://files/`，但点击操作显式读取 `ListItem.Property(homepath)`。官方 `CSourcesDirectory` 构造的源条目及 `CFileItem(CMediaSource)` 不设置该属性。显式 `<onclick>` 又优先于 provider 的默认点击处理，因此实际传给文件管理器的是空路径，进入默认目录或此前目录，不能按所选卡片跳转。

官方依据：[源条目构造](https://github.com/xbmc/xbmc/blob/21.2-Omega/xbmc/filesystem/SourcesDirectory.cpp#L43-L94)、[CFileItem 的媒体源构造函数](https://github.com/xbmc/xbmc/blob/21.2-Omega/xbmc/FileItem.cpp#L369-L391)、[显式 onclick 的优先级](https://github.com/xbmc/xbmc/blob/21.2-Omega/xbmc/guilib/GUIBaseContainer.cpp#L821-L841)、[文件管理器初始路径处理](https://github.com/xbmc/xbmc/blob/21.2-Omega/xbmc/windows/GUIWindowFileManager.cpp#L1194-L1254)。

**修复建议：** 优先移除显式 `<onclick>`，使用已声明的 `target="filemanager"` 默认导航；若保留自定义操作，使用官方实际路径标签并正确转义。对常用文件夹中的 `skin-home-root:` 路径也应清理自定义内核约定，改用官方可识别的路径。

**验证状态：** 仓库与官方 Kodi 21.2 导航链路静态对照确认；未执行 GUI 跳转。

### F3 · P2：发布版本判断会在普通代码提交后重复发布相同版本

**代码位置：** [release.yml:42–62](https://github.com/wabisabi926/skin.mistuary/blob/f7f821edc84184b7ee19cf6d07f91085fff2be7f/.github/workflows/release.yml#L42-L62)，关键表达式在第 48 行；[上传到版本 tag:121–130](https://github.com/wabisabi926/skin.mistuary/blob/f7f821edc84184b7ee19cf6d07f91085fff2be7f/.github/workflows/release.yml#L121-L130)。

**触发条件：** 最近一次修改 `addon.xml` 的提交升了版本；随后只修改 README、XML 等其他文件，再触发 `main` 的 push 工作流。

**原因与影响：** `git log -1 --skip=1 --format=%H -- addon.xml` 跳过的是最近一次修改 `addon.xml` 的提交，而不是当前 push 对应的提交。普通代码提交后，这条命令仍取到版本升级之前的旧版本，输出 `changed=true`。工作流于是重新打包并向同一个 `v<version>` Release 上传同名附件，可能更新已发布附件，使版本标识/tag 与包中源码不一致。这与文件顶部“不升版本不打包”的约定不符。

**修复建议：** 明确发布条件：若要求“本次 push 升版本才发布”，比较 push 事件前后的版本；若要求“每个版本只发布一次”，检查对应 tag/Release 是否已发布。发布附件应与固定提交绑定；仅通过显式 force 操作允许重打包。

**验证状态：** 已在隔离的临时 Git 仓库实际复现：建立旧版本提交、升版本提交，再添加不修改 `addon.xml` 的提交，现有表达式仍判断版本有变化。未触发真实 GitHub Release 或上传附件。

## 2. 设计与架构

### 优点

- 首页、详情页、音乐、OSD、技术标识等按公共 include 文件拆分，主题色集中管理，减少多个窗口独立维护同一视觉规则的成本。
- XML 控件直接复用 Kodi 原生窗口和 provider，主体没有额外常驻服务。现有代码统计包含 296 个 include 定义、270 个 variable 定义、47 个字体名称定义。
- 贴图维护同时保留松散资源与 XBT 包，开发者可以修改原图；工作流在发布前重新打包，降低忘记更新 XBT 的概率。

### 不足与建议

- 官方 Kodi 与自定义内核之间的能力边界没有成为可执行的兼容层。F1、F2 表明，仅去掉玻璃、圆角等扩展还不足以保证动态标签和路径协议兼容。应建立所支持 Kodi 版本的标签、属性、协议清单，并将其用于静态检查和实机验收。
- 多个窗口通过数字控制 ID、`Window(home).Property(...)` 和皮肤设置共享状态。这些隐式契约不易由 XML 解析检查发现，修改导航或模态窗口时容易产生回归。应集中说明关键属性、所属窗口、初始化与清理时机。
- 首页常用文件夹的八个槽位只有读取与清空操作，没有查到用户添加入口。参见 [HomeFileShortcutItems](https://github.com/wabisabi926/skin.mistuary/blob/f7f821edc84184b7ee19cf6d07f91085fff2be7f/xml/Includes_Home.xml#L100-L193)。建议补充管理入口，或移除默认配置无法建立的空白功能区域。

## 3. 代码质量与可读性

命名、公共组件边界及解释设计意图的注释总体清楚，导航和背景交接也有针对性的测试。不过，历史实现、转换脚本、文档与最终代码并存，当前状态不易辨认。

- `docs/mistuary-plan.md` 中部分缺陷记录已过时。例如文档描述的 autoscroll 大小写问题在当前代码已修复：设置写入与读取均使用 `autoscroll`，不应再次作为现存缺陷报告。相关实现见 [SkinSettings.xml:30–31](https://github.com/wabisabi926/skin.mistuary/blob/f7f821edc84184b7ee19cf6d07f91085fff2be7f/xml/SkinSettings.xml#L30-L31)。建议区分已解决记录、历史能力说明与当前支持范围。
- 字体定义统一引用 `inter.ttf`，仓库没有字体文件，也没有声明字体资源依赖。参见 [Font.xml:3–8](https://github.com/wabisabi926/skin.mistuary/blob/f7f821edc84184b7ee19cf6d07f91085fff2be7f/xml/Font.xml#L3-L8)。官方 Kodi 加载失败会回退 `arial.ttf`，因此不能据此断言界面无文字，但默认字体与预期排版依赖未被完整交付。官方依据：[字体搜索与 Arial 回退](https://github.com/xbmc/xbmc/blob/21.2-Omega/xbmc/guilib/GUIFontManager.cpp#L153-L201)。
- `audit_skin.py` 使用正则扫描原始 XML，包含注释误报；其“缺失字体”检查仅核对字体名称定义，不检查字体文件。应优先基于解析后的有效节点检查资源，并单独检测实际字体依赖。
- 发布 staging 把目标放在源码的 `build/` 内，但 rsync 未排除 `build/`。参见 [release.yml:85–99](https://github.com/wabisabi926/skin.mistuary/blob/f7f821edc84184b7ee19cf6d07f91085fff2be7f/.github/workflows/release.yml#L85-L99)。最小复现只生成一层空的嵌套目录，没有无限递归；这是打包卫生问题，建议排除构建目录或把 staging 放在源码树外。

## 4. 安全性

### F4 · P2：开发用 XBT 解包器允许路径穿越

**代码位置：** [xbt_tool.py:423–425](https://github.com/wabisabi926/skin.mistuary/blob/f7f821edc84184b7ee19cf6d07f91085fff2be7f/xbt_tool.py#L423-L425)。

**触发条件：** 开发者手动使用此工具解包不可信 XBT，其中条目路径为 `../escaped.png` 等含父目录跳转的路径；进程对目标位置有写权限。

**原因与影响：** 容器中的路径直接进入 `os.path.join(output_dir, *path.split('/'))`，随后创建目录并保存图片，没有校验规范化后的路径仍在输出目录内。恶意条目可把解码出的图片写到指定目录之外，并可能覆盖现有图片。此工具被发布工作流排除在插件安装包之外，风险范围是手动解包不可信归档的开发场景，不是 Kodi 皮肤运行时远程漏洞。排除规则见 [release.yml:95](https://github.com/wabisabi926/skin.mistuary/blob/f7f821edc84184b7ee19cf6d07f91085fff2be7f/.github/workflows/release.yml#L95)。

**修复建议：** 拒绝绝对路径和 `..` 路径分量；解析并确认最终目标仍位于输出目录内，处理符号链接风险。另应校验 XBT 版本、头部与帧数据边界、图片尺寸及最大解压量，为畸形输入给出可控错误。

**验证状态：** 已实际调用仓库解包函数复现。构造含一张 1×1 BGRA 图片的合法 XBTF2 容器，条目名为 `../escaped.png`；以临时 `extracted/` 为输出目录后，图片出现在其父目录。全部文件位于 `/tmp`，未覆盖用户文件。

### 其他安全观察

皮肤主体以声明式 XML 为主，没有自带网络监听服务或命令执行后端；多处动态动作使用了 `$ESCINFO` 转义。本次未确认皮肤运行时的远程代码执行问题。

发布工作流使用浮动 action 大版本，且 Pillow 未固定版本。参见 [release.yml:26–27](https://github.com/wabisabi926/skin.mistuary/blob/f7f821edc84184b7ee19cf6d07f91085fff2be7f/.github/workflows/release.yml#L26-L27)、[Pillow 安装:70–72](https://github.com/wabisabi926/skin.mistuary/blob/f7f821edc84184b7ee19cf6d07f91085fff2be7f/.github/workflows/release.yml#L70-L72)。建议固定经过验证的 action 提交和依赖版本，以提高供应链可追溯性及构建可复现性；这不代表已发现依赖遭到入侵。

## 5. 测试与验证

### 已执行检查

| 检查 | 结果及含义 |
| --- | --- |
| 全仓库 XML 解析 | **128/128 通过**，其中 `xml/` 内 125 个；只能证明 XML 语法有效，不能证明 Kodi 支持所有标签。 |
| 智能播放列表 `.xsp` 解析 | **38/38 通过**。 |
| Python 测试 | `python -m unittest discover -s extras -p 'test_*.py' -v`：**25 项，24 通过、1 失败**。 |
| Python 测试失败原因 | `test_nara_search_navigation.py:370` 仍期待旧值 `$VAR[GlassTint_regular]`，实际已改为主题颜色 `glass_regular`；属于测试预期过时，不能据此断言界面配色失效。 |
| 现有 XBT 与源图片一致性 | **662 张贴图逐帧解压，与松散图片的 BGRA 字节逐一比较，662/662 一致**；未发现漏打包或缺少对应源图。 |
| LZO 互操作 | 使用系统 `liblzo2.so.2` 的 `lzo1x_decompress_safe` 解压仓库压缩器输出；空输入、极小输入、长重复、多字节模式及固定种子随机输入共 **505/505 通过**。 |
| 发布版本判断 | 临时 Git 仓库实际复现 F3；未触发真实发布。 |
| XBT 输出目录边界 | 实际解包复现 F4；写入限定于临时目录。 |
| rsync staging | 最小复现生成一层空嵌套构建目录，没有无限递归。 |
| Kodi GUI、PowerShell 测试 | 环境无 `kodi`、`pwsh`，**未执行**。 |

过时断言位置：[test_nara_search_navigation.py:369–371](https://github.com/wabisabi926/skin.mistuary/blob/f7f821edc84184b7ee19cf6d07f91085fff2be7f/extras/test_nara_search_navigation.py#L369-L371)。XBT 一致性和 LZO 检查验证了数据与格式互操作，没有替代 Kodi 中的实际渲染验证，也没有覆盖任意畸形归档输入。

### 静态审计工具的结果与局限

`python extras/audit_skin.py` 输出缺失 include、variable、字体名称、贴图均为 0，另报告 42 个“缺失皮肤字符串”和 2 类“残留魔改内核属性”。**不能把这些输出当作 44 项真实缺陷**：字符串列表包含 Kodi 内置 ID 和注释中的 `70127`；本次两类扩展命中也位于注释中。

工具在 XML 解析失败后仅打印并继续，最后始终返回 0；检测到缺失引用同样不会形成失败退出码。代码见 [audit_skin.py:52–58](https://github.com/wabisabi926/skin.mistuary/blob/f7f821edc84184b7ee19cf6d07f91085fff2be7f/extras/audit_skin.py#L52-L58)、[结果输出与返回:126–138](https://github.com/wabisabi926/skin.mistuary/blob/f7f821edc84184b7ee19cf6d07f91085fff2be7f/extras/audit_skin.py#L126-L138)。另外，它漏查了 F1 的 `$MAP` 和 F2 的动态属性契约，不能单独作为官方 Kodi 兼容性证明。

### 覆盖缺口与验收建议

现有测试主要检查 XML 结构和自行实现的导航/窗口状态模型，覆盖搜索抽屉、设置返回、背景交接等场景，但不会运行 Kodi 实际的标签解析、焦点处理、窗口堆栈和渲染。发布工作流当前只打包发布，没有运行现有 Python/PowerShell 测试，也没有 XML 或兼容性检查关卡。

建议按以下顺序补齐验证：

1. 修复 F1、F2，并在官方 Kodi 21/22 上验收首页不同文件源跳转、媒体详情技术标识和视频 OSD。
2. 修正过时的测试断言，让 XML 语法错误、真实缺失引用形成非零退出码，并把可执行检查接入发布前 CI。
3. 为 F3 增加“升版本后普通提交不再发布”的回归场景，为 F4 增加父目录跳转、绝对路径及符号链接边界检查。
4. 使用遥控器/键盘和鼠标验收搜索、模态窗口返回、音乐及视频播放列表、两种配色；记录 Kodi 版本与平台，明确哪些结果来自模型测试、哪些来自实机。

