# script.mistuary.helper（皮肤侧摘要）

> **本文是摘要，不是权威。** 实现细节、进度表、测试策略都在插件仓库：
> `D:\下载\AI\script.mistuary.helper\docs\`
> （`roadmap.md` / `architecture.md` / `contract.md` / `testing.md`）
>
> 本文只写**皮肤需要知道的那部分**：怎么调、怎么退、最低版本。

> ⚠️ **正式接入排在 2.0.0（2026-10-30 用户定）**：1.x 只保留已经接上的软探测分支
> （`Includes_Search.xml` 的 M1b 那套），**不再继续推进** M1c 验证和新功能接线；
> 搜索 / 豆瓣评分 / 代表集技术标识三条统一在 2.0.0 一次做完。
> 换句话说：**1.x 的功能改动不许依赖 helper 可用**，没装插件的路径才是主路径。

## 定位

皮肤包不能携带 Python（Kodi 限制），凡是「发 HTTP / 解析 JSON / 写别人的 ListItem 属性」
这类 XML 做不到的事，都进这个独立插件。**不再新增第二个 `script.mistuary.*`。**

## 四项功能

| # | 功能 | 不装插件时 | 状态 |
|---|---|---|---|
| 1 | 服务端搜索（中文 / 原名 / 全拼 / 首字母） | 本地 XSP（标题 `contains` + 首字母 `startswith`） | 皮肤侧已接（`a6b9f59`），演员/类型见 M1d |
| 2 | 豆瓣评分（详情页胶囊） | 胶囊不显示，其余评分照常 | 未实现 |
| 3 | 代表集技术标识 | 皮肤自己的 `ListItemAbsolute(0)` 推断，行为不变 | 暂缓（收益为零，见插件 roadmap） |
| 4 | 行级增强（首页豆瓣角标、节点名整理） | 无影响 | 可选，不排期 |

**明确不做**：常驻 `service.py`、播放代理 / 转码、写 Kodi 库或皮肤设置、自建歌词
（歌词继续用 `script.cu.lrclyrics`，见 §6）。

## 1. 调用方式

```
plugin://script.mistuary.helper/?mode=search&type=movies&query=$INFO[Control.GetLabel(16999).index(1)]
plugin://script.mistuary.helper/?mode=search&type=shows&query=<搜索词>
RunScript(script.mistuary.helper,action=rating,type=movie,dbid=<id>)     # P1
RunScript(script.mistuary.helper,action=techflags,dbid=<剧集 id>)        # P2
```

**`query` 必须是最后一个参数**——插件用 `raw.split("query=", 1)` 取值，
这样中文、`&`、`?`、`=` 都不会被截断。`#` 会被 Kodi 当锚点截掉，无法绕开。

## 2. 可选安装：装了就多，不装就少

| 功能 | 装了插件 | **没装 / 禁用 / 版本低** |
|---|---|---|
| 搜索：中文标题 / 原名 | Emby 服务端，与官方 App 一致 | 本地 XSP（`contains`） |
| 搜索：首字母 | 服务端 | 本地 XSP（`startswith`） |
| 搜索：演员 / 导演 / 类型 | ❌ 未实现（M1d） | ❌ 没有（1.2.0 起本地已移除） |
| 搜索：全拼 / 原名 | ✅ | ❌ 没有 |
| 搜索：别名 / 分词 | ❌ 未实现 | ❌ 没有 |
| 详情页豆瓣胶囊 | ✅ | 整行不显示，其余胶囊照常 |
| 剧集代表集技术标识 | 暂缓（M3） | 皮肤自己推断，**行为不变** |
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
| `SkinSettings.xml` | 媒体分类的 `id=714` 开关，`Skin.ToggleSetting(helper_search_off)`，`visible="$EXP[helper_search_ready]"` |
| `Variables.xml` | 帮助条 `Control.HasFocus(714)` |
| `language/*.po` | 31780 开关名、31781 帮助 |

> 排序方案最终用 **B**（两套 content），没有用 A（直接删 `sortby`）：
> 本地 XSP 是没装插件用户的唯一路径，不能拿它做实验。

## 3. 版本契约

| 皮肤功能 | 最低插件版本 |
|---|---|
| 服务端搜索 | 0.1.0 |
| 详情页豆瓣 | 0.2.0 |
| 代表集标识 | 0.3.0 |

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
| 插件仓库 | `D:\下载\AI\script.mistuary.helper`，`main`，首个提交 `352e12e` |
| 已完成 | 骨架 + 搜索桥代码（58 项单测全绿）；M1b 皮肤侧已接并提交（`a6b9f59`） |
| 未完成 | M1b 实机验证（M1c）、播放地址、豆瓣 M2、代表集 M3 |
| 已同步实机 | `%APPDATA%\Kodi\addons\script.mistuary.helper` |

皮肤侧已接（`Includes_Search.xml` + `SkinSettings.xml` + 语言），**但插件在 Kodi 里是禁用状态**
（`Addons33.db.enabled = 0`，2026-10-30 实测），所以开关隐藏、搜索仍走本地。
M1c 第一步：设置 → 插件 → 我的插件 → 程序插件 → 启用 Mistuary Helper → 重载皮肤。

启用后待验：装/开、装/关、禁用、卸载、只装 helper 没装 Emby 五种组合；
`RZD` 应为 3 条（服务端）而不是 1 条（本地）。演员/类型搜索尚未实现，见插件仓库 roadmap M1d。

> **接线不必等播放地址验证**（2026-10-30 更正）：列表能不能显示、能不能点进去，
> 和 `play_url` 通不通是两件事。播放路径要改也只是插件里一行，皮肤侧不用动。
> 所以 M1b 可以直接做，与实机验证并行 —— 原稿写的"要等实机验证播放地址后再加分支"
> 是错的顺序。

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
