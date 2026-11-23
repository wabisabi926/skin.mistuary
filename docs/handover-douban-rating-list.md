# 交接：首页/媒体库显示豆瓣评分（未完成，待开发）

> 状态：**需求明确、方案已调研、代码已全部回滚**。接手从零开始按本文路径实现。
> 创建：2026-11-23。上一份交接：[`handover-2026-11-20.md`](handover-2026-11-20.md)。

## 1. 需求（用户原话要点）

- 首页「电影 / 电视剧」tab 的 Hero，评分行现在只显示**一颗主评分**（TMDb/IMDb）。
- 希望：**选中的每部片，如果详情页有豆瓣评分，首页也显示那颗豆瓣**（主评分后面）。
- 没有豆瓣分的就不显示，不要占位、不要错配。
- 媒体库视图（View_50/501）同样适用。
- 用户明确选的是**方案乙**：首页选哪部就补哪部的豆瓣分（不是"只显示详情页刚看过那部"）。

## 2. 当前皮肤行为（已确认的事实）

### 2.1 评分行结构

`xml/Includes_DialogVideoInfo_Hero.xml` 的 `NaraOnlineRatingsRow` 里，评分分两类：

| 位置 | 行号（约） | 数据源 | 显示条件要点 |
|---|---|---|---|
| 主评分（1 颗） | 97-183 | `Rating(tmdb/themoviedb/imdb/douban)`，按设置手选或自动 | 设置 `douban_rating` / `rating_src_*` 决定 |
| 次评分·豆瓣（库内类型分） | 185-189 | `Rating(douban)` | 有值 + `!hide_sec_douban` + `!douban_rating` + 与主评分不同 |
| 次评分·豆瓣（helper 联网补分） | 190-194 | `Window(10000).Property(Mistuary.Rating.Douban)` | 有 `Rating(douban)` 时不显示；**当前写死 `Window.IsVisible(12003)`（仅详情页）** |

`NaraRatingDoubanReady` = `String.IsEqual(Window(home).Property(Mistuary.Rating.Status),ok)`
（定义在 `Includes_DialogVideoInfo_Hero.xml:4`）。

### 2.2 为什么列表页只出一颗

- 库里普遍**没有 `Rating(douban)` 类型分**（实测 `MyVideos150.db` 的 `rating` 表：
  「可能的爱」只有 `tmdb 7.3` + `tomatometerallcritics 9.8`；「阳光女子合唱团」只有 `tmdb 7.2`）。
- 详情页那颗豆瓣来自 **helper 联网补分**，写在**全局单例** property
  `Window(10000).Property(Mistuary.Rating.Douban)`。
- 该 property 一次只存**一部片**的分，跟着"最后打开的详情页"走。首页 hero 选中另一部时，
  读到的仍是上一部 → 要么不显示（若加匹配校验），要么**张冠李戴**（当前若不校验就是错配）。

## 3. 关键结论：纯皮肤侧走不通（不要再试）

**Kodi 硬限制**：`itemlayout` / `focusedlayout` 里控件的 `<onfocus>` **不会**在列表项获得焦点时触发。
列表项只是渲染模板，焦点属于 list 控件本身，子控件不参与焦点系统。

实测证据（2026-11-23）：
- 在 `WidgetListPoster` 的 `focusedlayout` 里加 1×1 隐藏 button + `<onfocus>RunScript(...)</onfocus>`，
  F5 后左右切换 movie item（dbid 747→746），`Window(home).Property(Mistuary.Rating.LastReqDBID)`
  **始终为空** → onfocus 完全没触发。
- list 控件自身的 `<onfocus>` 只在"焦点进入列表"时触发一次，不随项变化。

**已试过并失败/回滚的方案**（不要重复）：
1. focusedlayout 隐藏 button onfocus 触发 helper —— 不触发（见上）。
2. 放开次评分 `Window.IsVisible(12003)` 限制 —— 显示条件虽全为真，但 property 是别的片的分，
   会错配；且不会自动补当前片，已 `git restore` 回滚。
3. 加 `LastReqDBID` 去重 —— 因 onfocus 根本不触发，无意义。

## 4. 可行方案（推荐实现路径）

因为皮肤触发不了，**必须由 helper 后台 service 主动补分**。

### 4.1 helper 侧（仓库 `D:/下载/AI/script.mistuary.helper`）

已有资产（直接复用，不要重写）：
- `lib/douban.py` → `run_action(req)`：入口，带 30 天 TTL 缓存 + 失败短缓存，
  写 `Mistuary.Rating.Status/Douban/Source/Votes/FetchedAt` 到 home property。
- `lib/router.py` → `Request`：解析 `action/type/dbid/imdb/title/year`。
- `service.py`：常驻后台（已有 `HelperPlayer` 等），加一个监听线程即可。

建议实现：
1. `service.py` 新增后台线程（或复用 `xbmc.Monitor().waitForAbort` 循环），每 **1~2 秒**采样：
   - `Home.Section`（movies / tvshows / libraries）
   - `Home.movies.Hero` / `Home.tvshows.Hero`（当前 hero 来自哪个 list）
   - 对应 `Container(<list_id>).ListItem.DBID` + `DBType`
2. DBID 与上次不同 → 构造 `Request` 调 `douban.run_action()`（走缓存，命中不发网络）。
3. 注意：只对 `DBType in (movie, tvshow)` 触发；`tag/set/genre` 等跳过。
4. 频率控制：同一 DBID 不重复请求；切换过快时可加 300~500ms 防抖。

### 4.2 皮肤侧（仓库 `D:/下载/AI/skin.mistuary`）

改动很小，只需放开显示条件 + 防错配：

1. `Includes_DialogVideoInfo_Hero.xml:190-194` 去掉 `Window.IsVisible(12003)`。
2. **必须加防错配校验**：只有当全局 property 记录的条目 == 当前条目时才显示。
   目前 helper 写的是 `Mistuary.Rating.Query`（标题）/`Mistuary.Rating.Year`，
   但**详情页调用时可能没传 title，实测 Query 为空**。
   → **建议 helper 侧新增一个 property**（如 `Mistuary.Rating.DBID`），补分时写入 dbid；
   皮肤条件改成 `String.IsEqual($PARAM[item_prefix].DBID, Window(10000).Property(Mistuary.Rating.DBID))`。
   这样只有 hero 当前片 == 刚补分的那部，才显示豆瓣，杜绝张冠李戴。
3. 需要覆盖的页面：首页 11 个 hero 实例（`Includes_HomeVideo.xml` 的 `HomeVideoHeroDetails`
   评分行 + `Includes_Home.xml` 紧凑态合并行）、`View_50_List.xml`、`View_501_Poster.xml`。
   注意：这些评分行都走 `NaraOnlineRatingsRow`，改一处 include 即可全局生效。

## 5. 验收标准

- 首页电影 tab 选中「可能的爱」（详情页有豆瓣 8.6）→ 评分行出现豆瓣 8.6，**稳定不闪**。
- 左右切到另一部无豆瓣分的片 → 豆瓣那颗消失，**不显示上一部的分**。
- 快速左右滚动 → 不卡顿（缓存命中）、不报错。
- 详情页行为不变（仍显示豆瓣）。
- 媒体库 View_50/501 选中剧集 → 同上。

## 6. 参考：现有 helper 调用方式

详情页触发（`xml/DialogVideoInfo.xml:18`）：

```xml
<onload condition="System.AddonIsEnabled(script.mistuary.helper) + [String.IsEqual(ListItem.DBType,movie) | String.IsEqual(ListItem.DBType,tvshow)]">RunScript(script.mistuary.helper,action=rating,type=$INFO[ListItem.DBType],dbid=$INFO[ListItem.DBID],imdb=$INFO[ListItem.IMDBNumber])</onload>
```

RPC 手动验证（本机 Kodi 已开 JSON-RPC，端口 8080，认证 `kodi:kodi`）：

```bash
curl -s -u kodi:kodi -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","method":"Addons.ExecuteAddon","params":{"addonid":"script.mistuary.helper","params":["action=rating","type=movie","dbid=91","imdb=tt1481955","title=阳光女子合唱团","year=2025"]},"id":1}' \
  http://127.0.0.1:8080/jsonrpc
# 再读结果：
curl -s -u kodi:kodi -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","method":"XBMC.GetInfoLabels","params":{"labels":["Window(10000).Property(Mistuary.Rating.Status)","Window(10000).Property(Mistuary.Rating.Douban)"]},"id":1}' \
  http://127.0.0.1:8080/jsonrpc
```

> 注意：2026-11-23 实测手动调 helper 对多部片都返回 `missing`（可能网络/Emby 侧问题）。
> 接手时先确认 helper 补分链路本身是通的，再调 UI。

## 7. 已回滚，工作区是干净的

本次为调研做过的皮肤改动（放开 `Window.IsVisible(12003)`、focusedlayout 触发按钮）**全部已
`git restore`**，`git status` 只剩未跟踪的 `.workbuddy/`。当前 HEAD：

- `400e09b` style: 首页电影/电视剧页简介与评分参数行间距调至30px
- `13189a5` feat: 首页电影/电视剧页紧凑态评分与技术参数同行显示
- `a50cf5c` feat: 媒体库50/501视图电视剧首屏显示技术参数与代表集集号

接手直接按 §4 开工，皮肤侧只需 §4.2 那三小步。
