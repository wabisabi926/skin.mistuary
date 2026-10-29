# 黑胶唱片 + helper 框架 方案（2026-10-29）

> 基线：`main` = `fc61e7e`（v1.2.1 已发）。本文回答四件事：
> ① 1.2.1 状态　② 33 张死图清理　③ **背景兜底到底有没有**　④ **黑胶唱片怎么做**　⑤ **helper 框架怎么搭**

---

## 0. 已完成

| 项 | 结果 |
|---|---|
| 1.2.1 | ✅ 已发（tag `v1.2.1` → `fc61e7e`，GitHub 已打包） |
| 删 33 张零引用贴图 | ✅ `--orphans` 首次实战，`Textures.xbt` 784 → **751 张 / 7.1 MB** |
| `--orphans` 复检 | ✅ **0 张**（783 → 750 张里已无死图） |
| audit / 单测 | ✅ EXIT=0 / 58 项全绿 |

删掉的 33 张：`flags/ratings` 的 metacritic / popcorn / popcorn_spilt / rtrotten / mdblist
（评分行改版后只剩 imdb / rtfresh / tmdb / douban）、`flags/starrating/1..10.png`
（实际用的是 `rating0..5.png`）、`icons/sidemenu` 7 张、`osd/fullscreen/buttons` 4 张、
`icons/search.png`、`lists/{duration,focus,panel,panel-mediamenu}.png`、`shapes/ring6_3.png`、
`colors/grey.png`。

---

## 1. 背景兜底：**有，而且是无条件绘制的最底层**

你问的这张就是 `extras/backgrounds/primary.jpg`（**1920×1080、228 KB**）。链路：

```
每个窗口 <include>DefaultBackground</include>
  └─ 组内第一层：<include>ColoredBackgroundImages</include>     ← 无 visible，永远画
        └─ <texture colordiffuse="primary_background">special://skin/extras/backgrounds/primary.jpg</texture>
  └─ 组内第二层（id=31111）：MediaFanartVar 的 fanart / 剧照      ← 叠在上面
```

- 设置页另有 `NaraSettingsBackground` = `DefaultBackground` + primary.jpg + 一个隐藏的随机 fanart 列表。
- `no_fanart` 开关只把 fanart 清空（`MediaFanartVar` 返回空），**primary.jpg 还在**。
- 20 个窗口声明了 `<backgroundcolor>`（`background` = `FF000000` 纯黑），那是**兜底色**，不是兜底图。

**所以"没有兜底图"的印象，来源是 primary.jpg 本身是深色抽象图，和纯黑底对比很低。** 三个选项：

| 选项 | 做法 | 代价 |
|---|---|---|
| **A 不动** | 现状够用，fanart 才是主体 | 0 |
| **B 换图** | 换一张辨识度更高的 primary.jpg（1920×1080）。注意透白主题下它会被白字压着，得选能压得住的 | 一张图 |
| **C 按主题两张** | 透黑用深色、透白用浅色，新增 `$VAR[PrimaryBackgroundVar]` 切换 | 两张图 + 一个变量 + 两处引用 |

我倾向 **A**：兜底图的作用是"别黑屏"，现在它做到了；再花哨反而和 fanart 抢戏。

---

## 2. 黑胶唱片效果（音乐播放页）

### 2.1 现状

`MusicVisualisation.xml` 是三层叠出来的：

| 控件 | 尺寸 | 内容 |
|---|---|---|
| `id=431` | 618² | 光晕 `music-cover-glow.png` |
| `id=430` | 450² | 专辑封面（**刚加了 r12 圆角遮罩**） |
| `id=432` grouplist → `id=433` | 450² | 光泽 `music-cover-sheen.png` |

### 2.2 目标

唱片转起来：**黑胶盘面（转）+ 中央圆形封面（转）+ 唱臂（不转，播放时搭上去）**。

### 2.3 技术可行性（已核实，不是猜的）

**① 连续旋转**：Kodi 的 `<animation>` 有 `loop` 属性，源码 `GUIControlFactory.cpp:1148`
`XMLUtils::GetBoolean(pControlNode, "loop", loop)`，默认 `true`。写法：

```xml
<animation effect="rotate" start="0" end="360" loop="true" time="24000"
           center="auto" condition="Player.Playing">Conditional</animation>
```

已装皮肤 Arctic Fuse 3 的 busy spinner 就是这么写的（`Includes_Objects.xml:352`），说明这条路走得通。

**② 圆形遮罩**：`media/masks/circle.png` 是 **256²** 的正圆。等比放大到 450² 仍是正圆，
所以可以直接当 `diffuse` 用，不用新生成 450 的圆（`mask_*` 那条"尺寸必须一致"的规则
是针对**非等比**缩放，正方形遮罩不受影响）。

### 2.4 要新增的素材

| 文件 | 规格 | 说明 |
|---|---|---|
| `osd/nara/vinyl-disc.png` | 1024² 透明底 | 黑胶盘面：同心细纹 + 中央标签环 + 轴心 + 边缘高光 |
| `osd/nara/vinyl-tonearm.png` | ~360×520 透明底 | 唱臂：配重盘 + 臂管 + 唱头，**支点在右上角**，旋转轴就是那里 |

生成器 `tools/gen_vinyl.py`：把 `gen_music_cover.py` 里已经画过的盘面/唱臂绘制代码拆出来
（它现在把两者压成一张 768² 的兜底封面，**拆开才能让盘面转、唱臂不转**）。
兜底封面 `music-cover.png` 保持不动。

### 2.5 XML 草案

```xml
<control type="group" id="430">
    <left>220</left><top>190</top><width>450</width><height>450</height>

    <!-- ① 盘面：比封面大一圈（450 + 2×48），跟着转 -->
    <control type="image">
        <left>-48</left><top>-48</top><width>546</width><height>546</height>
        <texture>osd/nara/vinyl-disc.png</texture>
        <animation effect="rotate" start="0" end="360" loop="true" time="24000"
                   center="auto" condition="Player.Playing">Conditional</animation>
    </control>

    <!-- ② 封面：裁成正圆，和盘面同一个旋转 -->
    <control type="image">
        <width>450</width><height>450</height>
        <texture background="true" diffuse="masks/circle.png">$VAR[NaraMusicCoverVar]</texture>
        <animation effect="rotate" start="0" end="360" loop="true" time="24000"
                   center="auto" condition="Player.Playing">Conditional</animation>
    </control>

    <!-- ③ 唱臂：不转；播放时从抬起 18° 落到 0° -->
    <control type="image">
        <left>300</left><top>-40</top><width>360</width><height>520</height>
        <texture>osd/nara/vinyl-tonearm.png</texture>
        <animation effect="rotate" start="-18" end="0" time="700" reversible="true"
                   center="360,40" condition="Player.Playing">Conditional</animation>
    </control>
</control>
```

（坐标是草案，实机要调；唱臂的 `center` 必须和 PNG 里的支点像素对齐。）

### 2.6 风险——先说清楚再动手

1. **暂停会回弹到 0°**。Kodi 的条件动画在条件消失时会 reset，唱片会"啪"地跳回起始角度，
   没有 API 能"停在当前角度"。缓解：周期拉长到 24s/圈（跳变时角度差小）+ `reversible="true"`；
   或者干脆接受。**这是这套方案唯一的硬伤，你要先认这个再决定做不做。**
2. **方形 → 圆形是观感大改**。现在 450² 方形封面 + r12 圆角会消失，变成圆形。
   要不要留一条"关闭黑胶效果"的皮肤设置（`vinyl_off` → 回到方形 + r12）？我建议留。
3. **性能**：旋转 + 遮罩 + 光晕三层同时画，N1 / S905 这类盒子可能掉帧。要实测。
4. **唱臂坐标**依赖 450² 容器；换尺寸（比如 OSD 里的小封面）要重算，所以做成 include 带 `size` 参数。

### 2.7 工作量

素材生成器 + 2 张图 ≈ 1h；XML ≈ 30min；实机调坐标 ≈ 30min。**合计约 2h。**

---

## 3. helper 插件：先把框架搭出来（阶段 0）

### 3.1 放哪

| 方案 | 位置 | 评价 |
|---|---|---|
| **A（推荐）** | `D:/下载/AI/script.mistuary.helper/`，独立 git 仓库 | 与 `helper-plugin-plan.md` §二 一致：独立发版，皮肤仓库只留探测与回退 |
| B | 皮肤仓库子目录 `skin.mistuary/helper/` | 会被 `release.yml` 的 rsync 排除规则搞乱，且违反"独立发版"，不推荐 |

### 3.2 骨架清单（每个文件的职责）

```
script.mistuary.helper/
├── addon.xml                  id=script.mistuary.helper，version 0.0.1，xbmc.python 3.0.1，provides=video
├── default.py                 入口：按 mode / action 分发（不写业务）
├── lib/
│   ├── router.py              参数解析。**query 必须是最后一个参数**，用 raw.split("query=", 1)[1]，
│   │                          中文 / & / ? 才不会截断（# 是已知限制）
│   ├── config.py              读插件设置 + 定位 Emby 服务器（server_id 空 = 第一个）
│   ├── http.py                urllib 封装：超时 6s、UA、失败返回 None 不抛到 UI
│   ├── cache.py               磁盘缓存：搜索 300s、豆瓣 7 天；json + mtime，写在 addon_data
│   ├── log.py                 debug_log 开关，前缀 MISTUARY.HELPER，**绝不打印 token**
│   ├── emby.py                Emby 客户端：/Items?searchTerm=、/Users、图片地址拼装
│   └── douban.py              P1 才填，先留空壳
├── resources/
│   ├── settings.xml           server_id / page_size / douban_enabled / cache_ttl / debug_log
│   └── language/resource.language.zh_cn/strings.po
├── tests/
│   ├── test_router.py         中文/&/?/# 各种 query
│   ├── test_cache.py          TTL、过期、损坏文件
│   └── test_emby.py           HTTP 全 mock
└── .github/workflows/ci.yml   pytest + 打包 zip + Release
```

### 3.3 阶段 0 的验收（做完就能验证"框架是通的"）

- 装进 Kodi →「我的插件」里能看到 **Mistuary Helper**，点开显示"请从皮肤进入或打开插件设置"
- `python -m pytest` 全绿（不依赖 Emby、不依赖网络）
- CI 能产出 `script.mistuary.helper-0.0.1.zip`
- 皮肤侧**什么都不用改**（还没接搜索）

### 3.4 阶段 1（搜索桥）要点

- `plugin://script.mistuary.helper/?mode=search&type=movies&query=中文`
- 返回 `ListItem`：`IsFolder=false`，`Path` 用 Emby 的直链（或 `plugin://plugin.video.emby/...`，
  看哪个在 Kodi 里能直接播——**这点要先在实机验**，决定阶段 1 的返回形态）
- 皮肤侧：`NaraSearchMoviesPathVar` / `NaraSearchTVShowsPathVar` 加 `$EXP[helper_ready]` 分支，
  服务端模式下**不要** `sortby="sorttitle"`（否则相关度排序被覆盖成字母序）

### 3.5 需要你定三件事

1. **仓库位置**：`D:/下载/AI/script.mistuary.helper/` 可以吗？（方案 A）
2. **Emby token 怎么取**：读 Emby 插件的 `settings.xml`（用户不用二次输入，但依赖插件装了），
   还是让用户在 helper 设置里自己填？（我倾向读插件配置 + 允许手填覆盖）
3. **阶段 1 的播放地址**：先做"返回 Emby 直链"，还是"返回 `plugin://plugin.video.emby`"？
   这个要在实机上点一下才知道哪个能播。

---

## 4. 建议顺序

```
① 黑胶唱片（2h + 实机调）        ← 你点名要先做，1.2.2 的亮点
② helper 阶段 0（半天）           ← 骨架 + 测试 + CI，做完能在 Kodi 里看到插件
③ helper 阶段 1（1 天）           ← 搜索桥 + 皮肤分支
④ 背景兜底                       ← 等你选 A/B/C（我建议 A 不动）
```

黑胶那条我建议**先只做素材 + 一条可开关的分支**，实机看过转速和回弹再决定要不要作为默认。
