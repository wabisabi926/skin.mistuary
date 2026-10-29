# script.mistuary.helper（皮肤侧摘要）

> **本文是摘要，不是权威。** 实现细节、进度表、测试策略都在插件仓库：
> `D:\下载\AI\script.mistuary.helper\docs\`
> （`roadmap.md` / `architecture.md` / `contract.md` / `testing.md`）
>
> 本文只写**皮肤需要知道的那部分**：怎么调、怎么退、最低版本。

## 定位

皮肤包不能携带 Python（Kodi 限制），凡是「发 HTTP / 解析 JSON / 写别人的 ListItem 属性」
这类 XML 做不到的事，都进这个独立插件。**不再新增第二个 `script.mistuary.*`。**

## 四项功能

| # | 功能 | 不装插件时 | 状态 |
|---|---|---|---|
| 1 | 服务端搜索（中文 / 全拼 / 别名 / 演员 / 类型） | 本地 XSP（标题 `contains` + 首字母 `startswith`） | 插件侧已完成，**皮肤侧未接** |
| 2 | 豆瓣评分（详情页胶囊） | 胶囊不显示，其余评分照常 | 未实现 |
| 3 | 代表集技术标识 | 皮肤自己的 `ListItemAbsolute(0)` 推断，行为不变 | 未实现 |
| 4 | 行级增强（首页豆瓣角标、节点名整理） | 无影响 | 可选，不排期 |

**明确不做**：常驻 `service.py`、播放代理 / 转码、写 Kodi 库或皮肤设置、自建歌词
（歌词继续用 `script.cu.lrclyrics`，见 §6）。

## 1. 调用方式

```
plugin://script.mistuary.helper/?mode=search&type=movies&query=<搜索词>
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
| 搜索：演员 / 导演 / 类型 | ✅ | ❌ 没有（1.2.0 起本地已移除） |
| 搜索：全拼 / 别名 / 分词 | ✅ | ❌ 没有 |
| 详情页豆瓣胶囊 | ✅ | 整行不显示，其余胶囊照常 |
| 剧集代表集技术标识 | 插件写属性 | 皮肤自己推断，**行为不变** |
| 启动 / 播放 / 设置 | 不受影响 | 不受影响 |

### 四条硬约束

1. **皮肤侧只加分支，不替换**：新条件写进已有 `<variable>`，原来那行无条件 `<value>` 永远留在最后。
2. 任何分支都必须有"未装"兜底，**兜底是当前已有行为**，不是空白。
3. 插件返回空 / 报错 / 超时 → 按"没装"处理，**不弹错误框**。
4. 设置开关 `helper_search` 默认开，但**未装插件时整行隐藏**——别给用户一个拨不动的开关。

### 皮肤侧写法

```xml
<expression name="helper_ready">System.AddonIsEnabled(script.mistuary.helper)</expression>

<variable name="NaraSearchMoviesPathVar">
    <value condition="$EXP[helper_ready] + Skin.HasSetting(helper_search)">plugin://script.mistuary.helper/?mode=search&amp;type=movies&amp;query=</value>
    <value>library://video/movies/...</value>
</variable>
```

服务端模式下**不要**给容器加 `sortby="sorttitle"`，否则相关度排序会被覆盖成字母序。

## 3. 版本契约

| 皮肤功能 | 最低插件版本 |
|---|---|
| 服务端搜索 | 0.1.0 |
| 详情页豆瓣 | 0.2.0 |
| 代表集标识 | 0.3.0 |

低于要求按"未装"处理，避免用户装了早期测试版却拿到半截数据。

## 4. 一个必须写进用户文档的坑

`<include condition="...">` 和容器的 `<content>` 都是**加载时求值**的。
所以**装完 / 卸载插件后要重载皮肤**（设置 → 界面 → 皮肤 → 重新加载）才生效。
不写这句，用户会以为插件没起作用。

卸载后回退是**立即**的（探测每次渲染求值，不是缓存）。

## 5. 当前状态

| 项 | 状态 |
|---|---|
| 插件仓库 | `D:\下载\AI\script.mistuary.helper`，`main`，首个提交 `352e12e` |
| 已完成 | 骨架 + 搜索桥代码（58 项单测全绿） |
| 未完成 | **皮肤侧分支未接**、播放地址未实机验证、豆瓣 P1、代表集 P2 |
| 已同步实机 | `%APPDATA%\Kodi\addons\script.mistuary.helper` |

**皮肤侧一行都还没改**——所以现在装不装插件，搜索行为都一样。
接分支是 M1b，单独一步，做完立刻验证降级。

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
