# script.mistuary.helper（皮肤侧摘要）

> **本文是摘要，不是权威。** 实现细节、进度表、测试策略都在插件仓库：
> `<插件仓库根>\docs\`
> （`roadmap.md` / `architecture.md` / `contract.md` / `testing.md`）
>
> 本文只写**皮肤需要知道的那部分**：怎么调、怎么退、最低版本。

> **正式接入随皮肤 1.4.0 发布（2026-10-30 用户定）**：M1b 搜索软探测和 M2 豆瓣评分
> 已接在 `main`；1.x 仍保持可选安装，**不写硬依赖**，没装插件的路径才是主路径。
> M1c 实机验收（搜索 + 播放）已于 2026-10-30 通过；M3 代表集明确不做。
>
> **2026-11-05 改写（用户决定，覆盖上一条）**：媒体库封面改由 Helper 从 Emby 同步，
> 皮肤删除 24 张内置封面，`addon.xml` 改为**硬依赖** `script.mistuary.helper`；
> 未安装时皮肤不加载。下面的"没装会怎样"列只作为运行时降级说明保留。

## 定位

皮肤包不能携带 Python（Kodi 限制），凡是「发 HTTP / 解析 JSON / 写别人的 ListItem 属性」
这类 XML 做不到的事，都进这个独立插件。**不再新增第二个 `script.mistuary.*`。**

## 五项功能

| # | 功能 | 不装插件时 | 状态 |
|---|---|---|---|
| 1 | 服务端搜索（中文 / 原名 / 全拼 / 首字母） | 本地 XSP（标题 `contains` + 首字母 `startswith`） | 皮肤侧已接（`a6b9f59`）；演员/类型 0.3.3 起支持（仅非 ASCII） |
| 2 | 豆瓣评分（详情页胶囊） | 胶囊不显示，其余评分照常 | ✅ 已接（插件 0.2.0+，`79b7eba`）；1.5.1 起次评分只在详情页显示豆瓣 |
| 3 | 代表集技术标识 | 皮肤自己的 `ListItemAbsolute(0)` 推断，行为不变 | 暂缓（收益为零，见插件 roadmap） |
| 4 | 行级增强（首页豆瓣角标、节点名整理） | 无影响 | 不做（架构限制） |
| 5 | 播放列表补全（媒体库剧集按季 / 文件夹播放按目录） | 无（Kodi 原生只播当前项） | ✅ 插件 0.3.5，按季/按目录/跨季三个开关默认关；事件驱动 service、不轮询 |
| 6 | 文件播放记录（文件管理器 10003 / 视频「文件」10025） | 无（Kodi 只给库内条目续播） | ✅ 插件 0.3.7；10003 弹窗 + 焦点行圆环，10025 原生镜像 |

**明确不做**：**通用轮询型**常驻 service（0.3.5 的补全服务是事件驱动、默认关；
0.3.7 只有 10003 焦点行圆环在窗口激活时做 0.4 秒一次的轻量轮询）、
播放代理 / 转码、写 Kodi 库或皮肤设置、自建歌词（歌词继续用 `script.cu.lrclyrics`，见 §6）。

## 1. 调用方式

```
plugin://script.mistuary.helper/?mode=search&type=movies&query=$INFO[Control.GetLabel(16999).index(1)]
plugin://script.mistuary.helper/?mode=search&type=shows&query=<搜索词>
RunScript(script.mistuary.helper,action=rating,type=movie,dbid=<id>)     # M2
RunScript(script.mistuary.helper,action=techflags,dbid=<剧集 id>)        # M3 暂缓
```

**`query` 必须是最后一个参数**——插件用 `raw.split("query=", 1)` 取值，
这样中文、`&`、`?`、`=` 都不会被截断。`#` 会被 Kodi 当锚点截掉，无法绕开。

## 2. 安装方式：2026-11-05 起为必需依赖

| 功能 | 装了插件 | **没装 / 禁用 / 版本低** |
|---|---|---|
| 搜索：中文标题 / 原名 | Emby 服务端，与官方 App 一致 | 本地 XSP（`contains`） |
| 搜索：首字母 | 服务端 2–4 位严格前缀（0.3.3+） | 本地 XSP（`startswith`） |
| 搜索：演员 / 导演 / 类型 | ✅ 仅非 ASCII、≥2 字（0.3.3） | ❌ 没有（1.2.0 起本地已移除） |
| 搜索：全拼 / 原名 | ✅ | ❌ 没有 |
| 搜索：别名 / 分词 | ❌ 未实现 | ❌ 没有 |
| 详情页豆瓣胶囊 | ✅ | 整行不显示，其余胶囊照常 |
| 播放列表补全 | ✅ 0.3.5，三个开关默认关 | Kodi 原生只播当前项 |
| 文件播放记录 | ✅ 0.3.7，默认开 | Kodi 只给库内条目续播 |
| 剧集代表集技术标识 | 不做（M3） | 皮肤自己推断，**行为不变** |
| 启动 / 播放 / 设置 | 不受影响 | 不受影响 |

### 四条硬约束

1. **皮肤侧只加分支，不替换**：新条件写进已有 `<variable>`，原来那行无条件 `<value>` 永远留在最后。
2. 任何分支都必须有"未装"兜底，**兜底是当前已有行为**，不是空白。
3. 插件返回空 / 报错 / 超时 → 按"没装"处理，**不弹错误框**。
4. 设置开关 `helper_search_off`（反向命名 = 默认开），**插件或 Emby 不可用时整行隐藏**——别给用户一个拨不动的开关。

### 皮肤侧写法

皮肤实际写法（`xml/Includes_Search.xml`）：

```xml
<expression name="helper_search_ready">System.AddonIsEnabled(script.mistuary.helper) + System.AddonIsEnabled(plugin.service.emby-next-gen)</expression>

<variable name="NaraSearchMoviesPathVar">
    <value condition="$EXP[helper_search_ready] + !Skin.HasSetting(helper_search_off) + !String.IsEmpty(Control.GetLabel(16999).index(1))">plugin://script.mistuary.helper/?mode=search&amp;type=movies&amp;query=$INFO[Control.GetLabel(16999).index(1)]</value>
    <value condition="!String.IsEmpty(Control.GetLabel(16999).index(1))">videodb://...</value>
</variable>
```

两个 fixedlist（`16101` 电影 / `16102` 剧集）不再写死 `<content>`，
改为按来源 include 两套：

| include | 容器属性 |
|---|---|
| `NaraSearch*ContentLocal` | `sortby="sorttitle" sortorder="ascending"` |
| `NaraSearch*ContentServer` | **不写 `sortby`**，保留服务端相关度 |

**接线点一览**：

| 文件 | 内容 |
|---|---|
| `Includes_Search.xml` | `helper_search_ready` expression；两个路径变量；4 个 content include；两个容器的 include 条件 |
| `SkinSettings.xml` | `onload` 调 `settings_snapshot`；媒体页 `714` 搜索开关 / `720` 详情页联网取豆瓣，播放页 `721–724` 按季/按目录/跨季/文件记录，均走插件设置桥 |
| 设置桥 | 插件把五个 bool 写成 `Mistuary.Helper.*` 窗口属性；皮肤只读属性、点击 `toggle_setting` |
| `Variables.xml` | 帮助条 `Control.HasFocus(714 / 720 / 721–725)` |
| `language/*.po` | 31780/31781 搜索、31808/31812 豆瓣、31813–31815 补全、31822 文件记录、31823 封面同步 |

> 排序方案最终用 **B**（两套 content），没有用 A（直接删 `sortby`）：
> 本地 XSP 是没装插件用户的唯一路径，不能拿它做实验。

## 3. 版本契约

| 皮肤功能 | 最低插件版本 |
|---|---|
| 服务端搜索 | 0.1.0（建议 0.2.1+，修 `resume:false` 污染） |
| 详情页豆瓣 | 0.2.0 |
| 代表集标识 | 不适用（M3 暂缓，不承诺版本） |

皮肤**不做版本比较**（Kodi 没有可靠的版本比较表达式）：旧版插件对新增功能
什么都不写，皮肤自然隐藏，等价于没装。最低版本只写在 README / Release 说明里。

## 4. 一个必须写进用户文档的坑

`<include condition="...">` 和容器的 `<content>` 都是**加载时求值**的。
所以**装完 / 卸载插件后要重载皮肤**（设置 → 界面 → 皮肤 → 重新加载）才生效。
不写这句，用户会以为插件没起作用。

卸载后回退是**立即**的（探测每次渲染求值，不是缓存）。

## 5. 当前状态

| 项 | 状态 |
|---|---|
| 插件仓库 | `<插件仓库根>`，`main`，**发布 0.3.11**（229 项单测） |
| 已完成 | 搜索桥 + 详情页豆瓣；M1b / M2 / M1c 完成。0.3.3 起：设置 4 类（覆盖项进专家）、帮助条、非 ASCII 查询并入演员/类型、首字母前缀严格；评分同步已移除。0.3.4：播放列表补全。0.3.7：文件播放记录（10003 弹窗 + 焦点行圆环；10025 原生镜像）。0.3.9：媒体库封面同步 + 按目录补全默认开。0.3.10：搜索剧集跳 Kodi 媒体库。0.3.11：未同步剧集进插件自己的季/集列表。皮肤侧「皮肤助手」页直接切换服务端搜索、豆瓣评分、按季/按目录/跨季、文件播放记录；高级项仍进插件设置 |
| 未完成 | 别名 / 分词未实现；M3 / M4 不做 |
| 已同步实机 | `%APPDATA%\Kodi\addons\script.mistuary.helper`（实机为 0.3.11） |

皮肤侧已接（`Includes_Search.xml` + `SkinSettings.xml` + 语言），插件在 Kodi 里已启用
（`Addons33.db.enabled = 1`，2026-10-30 复查）。装 / 启用后仍需重载皮肤，
`<include condition>` 和容器 `<content>` 才会重新求值。

M1c 已通过：中文 / 原名 / 全拼 / 首字母搜索、分页、点进播放全部正常；
`RZD` 现在是 **1 条**（0.3.3 起严格前缀），本地/服务端一致。

> **现实限制**：皮肤搜索键盘只能输入字母，没有中文输入法。演员 / 类型搜索虽然插件支持，
> 在皮肤 UI 里实际不可达；日常只能用全拼 / 首字母搜作品。要真用起来，需要人物拼音首字母
> 或皮肤新增「人物」页签。

## 5.1 已知问题（2026-10-31 全部关闭）

| 问题 | 状态 |
|---|---|
| 服务端搜索结果没有封面 | ✅ 插件 `c4ac966`（0.3.0+）回退读 `ImageTags.Primary` |
| 搜索页背景没有兜底图 | ✅ 皮肤 `baae9ef` 重排 `NaraSearchBackground` |
| 搜索结果点击播放未验证 | ✅ M1c 实机通过（`mode=play`） |

## 6. 歌词为什么不进插件

皮肤现在用第三方插件 `script.cu.lrclyrics`（v6.7.6）做歌词，皮肤提供窗口覆盖文件
`xml/script-cu-lrclyrics-main.xml` 把它的列表放到播放页右侧。

**不重做自建歌词的理由**：

| 用户场景 | 自建桥能做到吗 | CU LRC |
|---|---|---|
| 自动下载歌词 | ❌ 要多源搜索 + 鉴权 + 模糊匹配，最难的部分 | ✅ 已做 |
| 本地同名 `.lrc` | ✅ | ✅ |
| 内嵌歌词 | ⚠️ 格式多，只覆盖一部分 | ✅ |

最常用的"自动下载"恰恰是自建做不了的那个。而且 Kodi 22-BETA2 上 CU LRC 工作正常
（`kodi.log` 里 `Window Translator` 错误为 0）。

**唯一风险**：CU LRC 升级改了控件 id（覆盖文件里硬编码了 `list id="110"`），
或用户换成别的歌词插件——两种情况都是「右侧排版失效、歌词以插件自己的全屏界面出现」，
**不报错、不影响播放**。

要重做的话，`.lrc` 解析本身只有 100 行，真正贵的是在线搜索，所以**延后没有额外成本**。
