# script.mistuary.helper 规划（独立插件）

> 状态：**计划中，未实施**。本文是皮肤与插件之间的契约，改代码前先改本文。
> 皮肤包不能携带 Python（Kodi 限制），所有运行时逻辑走这个独立 addon。

## 一、为什么需要

皮肤是声明式 XML：不能发 HTTP、不能解析 JSON/HTML、不能把中文转拼音、
也不能给别的窗口的 ListItem 写属性。文档里已经出现过三处「必须脚本」的需求：

| 需求 | 出处 | 皮肤侧现状 |
|---|---|---|
| 服务端搜索（中文/全拼/模糊） | 本文 §5.1 | 本地 XSP 只能匹配 `contains`，全拼/分词/别名吃不到 |
| 豆瓣评分 | HANDOVER §5.7 | TMDbHelper 的豆瓣分在 infoproperties，皮肤读不到 |
| 剧集代表集技术标识 | `techflag-icons-plan.md` §280 | `TvShowRepresentative.*` 分支已留好，无人写入 |

后续凡是「皮肤拿不到、算不了」的功能都进这个插件，不再新增第二个 `script.mistuary.*`。

## 二、命名、仓库、许可

- **addon id**：`script.mistuary.helper`（HANDOVER §5.7 已按此名预留）。
- **仓库**：独立仓库，与皮肤分开发版；皮肤仓库只保留探测与回退逻辑。
- **许可**：GPL-3.0。豆瓣取分复用 `plugin.video.themoviedb.helper-douban` 的实现
  （TMDbHelper，GPL-3.0），必须保留版权声明与来源说明。
- **依赖**：只用 Python 标准库（`urllib` / `json` / `hmac` 等），不打包第三方库。

## 三、与皮肤的契约

| 功能 | 皮肤触点 | 数据方向 | 失败时 |
|---|---|---|---|
| 搜索 | 容器内容 `plugin://script.mistuary.helper/?mode=search&type=movies&query=<原始词>` | 插件 → 列表 | 回退现有 XSP |
| 豆瓣评分 | `RunScript(script.mistuary.helper,action=rating&type=movie&dbid=<id>)`；读 `Window(home).Property(Mistuary.Rating.Douban)` / `.Votes` / `.FetchedAt` | 插件 → 窗口属性 | 属性为空，皮肤不显示 |
| 代表集标识 | 读 `ListItem.Property(TvShowRepresentative.*)`，已有 include 分支 | 插件 → 列表项 | 属性为空，不显示 |
| 版本探测 | `System.AddonIsEnabled(script.mistuary.helper)` + `System.AddonVersion(script.mistuary.helper)` | 皮肤 ← 插件 | 视为未安装 |

硬约束：

1. `query` 必须是插件的**最后一个参数**，插件用 `raw.split("query=", 1)[1]` 取值，
   这样中文、`&`、`?` 不会截断（`#` 除外，属已知限制）。
2. 插件只读 Emby 配置与 Kodi 库，**不改库、不写皮肤设置**。
3. 任何失败静默降级，不弹错误框；错误写 `kodi.log` 且**不含 token**。

## 四、功能与优先级

| 阶段 | 功能 | 依赖 |
|---|---|---|
| P0 | 服务端搜索（电影 / 剧集） | Emby 在线 |
| P1 | 豆瓣评分（详情页优先） | 网络 + IMDb id |
| P2 | 剧集代表集技术标识 | Kodi 库或 Emby API |
| P3（可选） | 行级数据增强（首页/搜索行带豆瓣角标）、动态节点名整理 | 皮肤换数据源 |

## 五、详细设计

### 5.1 搜索桥

**入口**：`default.py` 解析 `mode=search&type=movies|shows&query=…`。

**服务器发现**：扫描
`special://profile/addon_data/plugin.service.emby-next-gen/servers_*.json`，
读取 `ServerId / ServerUrl / LocalAddress / RemoteAddress / AccessToken / UserId`；
`ServerUrl` 为空时按 `LocalAddress → RemoteAddress` 回退。多服务器时按设置里选中的
`ServerId`，默认取第一个。

**请求**：

```
GET {base}/emby/Items
  ?searchTerm={query}
  &Recursive=true
  &IncludeItemTypes=Movie,Series
  &Fields=ProductionYear,PremiereDate,CommunityRating,Overview,RunTimeTicks,
          PrimaryImageTag,BackdropImageTags,ProviderIds,UserData
  &ImageTypeLimit=1&EnableImageTypes=Primary,Backdrop
  &Limit=100&UserId={UserId}
Header: X-Emby-Token: {AccessToken}
超时: 5s
```

神医助手的中文分词/全拼在服务端生效，这条路径与 Emby 官方 App 等价。

**结果映射**：

| 类型 | ListItem | 路径 |
|---|---|---|
| Movie | `setInfo('video', {...})`、`IsPlayable=true` | `plugin://plugin.service.emby-next-gen/?mode=play&item={Id}&server={ServerId}`（插件已支持，`webservice.py:451`） |
| Series | 文件夹 + 海报/简介 | `plugin://plugin.service.emby-next-gen/?mode=browse&id={Id}&parentid=0&content=tvshows&libraryid=0&query=Series&server={ServerId}`（实现时按插件实测校准） |

- 图片：`{base}/Items/{Id}/Images/Primary?tag={PrimaryImageTag}&maxWidth=400&quality=90&api_key={token}`；
  无图回退 `DefaultVideo.png`。
- 已看/进度：`UserData.Played`、`PlaybackPositionTicks`。
- 排序：按服务端相关度返回，皮肤容器**不要**再按 `sorttitle` 重排（见 §6）。

**分页**：默认 100 条；超出时追加「加载更多」（`offset` 递增）。

**缓存**：key = sha1(`ServerId|type|query`)，TTL 5 分钟，存
`addon_data/script.mistuary.helper/cache/`，避免容器重绘反复打服务端。

**错误映射**：

| 情况 | 行为 |
|---|---|
| `401/403` | 结果里放一条「Emby 登录已失效，请在 Emby 插件重新连接」 |
| 连接失败/超时 | 一条「Emby 服务端不可达」 |
| 空结果 | 空列表，皮肤显示现有空态 |

### 5.2 豆瓣评分

**取分方式（采用 `plugin.video.themoviedb.helper-douban` 的方案）**：

- 双通道、按概率分流，失败互备：
  - Legacy：`POST https://api.douban.com/v2/movie/imdb/{imdbid}` + `apikey`
  - Frodo：`GET https://frodo.douban.com/api/v2/search/movie?q={imdbid}`，
    `_sig` = base64(HMAC-SHA1(secret, `GET&{path}&{yyyymmdd}`))，随机 `User-Agent`、
    固定 `bid` Cookie
- 归一：`average × 10` 取整（0–100），另存 `numRaters`。
- 输入：优先 Kodi `uniqueid` 的 imdb，其次 Emby `ProviderIds`；没有 IMDb id 直接返回空。

**缓存**：磁盘 JSON，key = imdb id，TTL **7 天**；失败结果缓存 30 分钟避免反复重试；
并发上限 1，失败指数退避（1s/2s/4s）。

**皮肤交互**：详情页 `onload` 调 `RunScript(script.mistuary.helper,action=rating&type=movie&dbid=…)`，
插件写：

```
Window(home).Property(Mistuary.Rating.Douban)     # 8.6
Window(home).Property(Mistuary.Rating.Votes)      # 123456
Window(home).Property(Mistuary.Rating.FetchedAt)  # epoch
Window(home).Property(Mistuary.Rating.Status)     # ok / missing / error
```

皮肤只负责显示，不判断来源；`Status != ok` 时隐藏胶囊。

### 5.3 剧集代表集技术标识

- 取「当前季首集」作为代表集（与详情页现有规则一致）。
- 数据源：库内条目走 Kodi JSON-RPC（`VideoLibrary.GetEpisodes` + `GetItemDetails`）；
  Emby 动态节点走 `/emby/Items?ParentId=…&IncludeItemTypes=Episode&Limit=1`。
- 写 `ListItem.Property(TvShowRepresentative.VideoResolution / HdrType / HdrDetail /
  VideoCodec / AudioCodec / AudioChannels …)`，皮肤已有 include 分支直接生效。
- 仅对插件自己生成的列表生效；库里的行保持现状（见 §4 P3）。

### 5.4 基础设施（lib/）

| 模块 | 职责 |
|---|---|
| `emby.py` | 服务器发现、HTTP 客户端、token 注入、错误映射 |
| `douban.py` | 双通道取分、签名、限速、缓存 |
| `kodi.py` | ListItem 构造、属性桥、翻译、日志 |
| `cache.py` | 磁盘缓存（JSON + TTL + 原子写） |
| `techflags.py` | 代表集解析与属性拼装 |
| `default.py` | 路由：`mode=search` / `action=rating` / `action=techflags` |

## 六、皮肤侧改动（含本地搜索修复）

1. **首字母搜索修复（2026-10-28 已实施）**
   - `sorttitle` 的 operator：`contains` → **`startswith`**。实测：`HZ` 从 14 部降到 4 部，
     `Z` 从 221 部降到 37 部。
   - 从快速搜索的 `or` 里**去掉 `actor` / `director` / `genre`**：同一 `or` 只能共用一个
     operator，拉丁字母查询会把演员名当命中（`Z` 命中 238/742 部、`S` 命中 371/742），
     而且首字母与人员搜索语义不同。人员/类型搜索交给服务端桥。
   - 保留 `title` / `originaltitle` 的 `contains`（中文标题、原名靠它）。
2. **搜索容器**：`NaraSearchMoviesPathVar` / `NaraSearchTVShowsPathVar` 增加
   `System.AddonIsEnabled(script.mistuary.helper)` 分支（§3 的路径），原 XSP 条件整体退为 fallback。
   服务端模式下容器不要 `sortby="sorttitle"`，避免把相关度排序覆盖成字母序。
3. **豆瓣胶囊**：详情页新增一行属性绑定；`Status != ok` 时整行隐藏。
4. **设置开关**：常规新增「使用 Emby 服务端搜索」（默认开，未装插件时隐藏）。

## 七、实施阶段与验收

| 阶段 | 内容 | 验收 |
|---|---|---|
| 0 | 仓库骨架、CI（pytest + zip）、settings、缓存/HTTP/配置 | 可安装，空跑通过 |
| 1 | 搜索桥 + 皮肤分支 + 回退 | 中文/全拼/别名结果与 Emby 官方 App 抽查一致；未装插件行为不变 |
| 2 | 豆瓣评分（详情页） | 首屏 ≤ 500ms（命中缓存）；失败静默；7 天缓存生效 |
| 3 | 代表集标识 | 首页/搜索剧集行显示与详情页一致 |
| 4（可选） | 行级增强 / 节点名 | 按需另立方案 |

**单集搜索**：v1 只做电影 + 剧集；v1.1 再把单集并入「剧集」页签（带 SxxExx，点击直接播放），
避免 v1 同时改两套映射与页签逻辑。

**常驻服务**：v1 **不做** `service.py`，纯按需调用 + 磁盘缓存。理由：少一个常驻线程、
少一类崩溃面、无后台网络；若实测详情页豆瓣首屏 > 1s，再增加「只预取、不轮询」的轻服务。

## 八、测试

- 单测（pytest，HTTP 全 mock）：参数解析（中文/空格/`&`）、服务器选择、错误映射、
  ListItem 字段、缓存 TTL、豆瓣签名与归一、代表集解析。
- 静态（皮肤仓库）：`tools/` 新增断言——搜索变量必须同时包含 helper 分支与 XSP 回退；
  `audit_skin.py` 不受影响。
- 手工矩阵：Emby 在线/离线、helper 未装/禁用、Kodi 刮削库、中文/全拼/首字母/演员、
  特殊字符、已看进度、剧集二级页。

## 九、发版与版本契约

- 独立仓库 + GitHub Actions：pytest → zip → Release（`script.mistuary.helper-<ver>.zip`）。
- 皮肤文档列出每个功能要求的最低版本：

| 皮肤功能 | 最低 helper 版本 |
|---|---|
| 服务端搜索 | 0.1.0 |
| 详情页豆瓣 | 0.2.0 |
| 代表集标识 | 0.3.0 |

- 皮肤不声明硬依赖，只做软探测；插件升级不影响皮肤回退路径。

## 十、风险与回滚

| 风险 | 处置 |
|---|---|
| Emby for Kodi 改 `servers_*.json` 结构 | 读取失败即回退，不动用户数据；版本适配写进插件 changelog |
| 豆瓣接口变更/风控 | 双通道互备 + 失败缓存；持续失败时属性置 `error`，皮肤隐藏 |
| GPL-3.0 传染 | 插件整体 GPL-3.0，保留 TMDbHelper 版权声明 |
| Token 泄露 | 只读、不打印、不落缓存文件；日志只记 ServerId 与状态码 |
| 搜索延迟 | 100 条上限 + 5 分钟缓存 + 超时 5s；必要时降级本地 XSP |

## 附录 A：参考实现

- 豆瓣：`plugin.video.themoviedb.helper-douban/resources/tmdbhelper/lib/api/douban/api.py`
  （legacy + frodo 双通道、HMAC 签名、随机 UA）
- Emby 路由：`plugin.service.emby-next-gen/hooks/webservice.py`
  （`mode=search` 见 375 行，`mode=play` 见 451 行）、`emby/views.py`（动态节点路径）
- 中文搜索增强：`StrmAssistant-mod/decompiled/StrmAssistant/Patch/ChineseSearch.cs`（服务端 FTS 分词）
- 拼音首字母：`StrmAssistant-mod/decompiled/StrmAssistant/Patch/PinyinSortName.cs`（写 Emby `SortName`）
