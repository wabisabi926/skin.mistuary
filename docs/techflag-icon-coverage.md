# 技术标识图标 —— 素材库盘点与缺口清单

> 按 `xml/Includes_VideoTechnicalFlags.xml` 里 5 张 map 的**实际 key**逐个比对，
> 大小写不敏感 + 别名归一（`h265/hvc1 → hevc`、`truehd_atmos → dolby_truehd_atmos` 等）。
> 复现脚本已随 `docs/scratch/` 清理丢失；下表是 2026-10-28 的素材库快照。

合计 **109** 个取值需要图标。

> **最终实现已覆盖全部取值**：素材库拿不到 logo 的 16 个冷门格式，由
> `tools/gen_techflag_icons.py` 按显示名渲染成白字标。本表只反映"哪些能拿到真实 logo"。

## 一、素材库清单

| 来源 | 色彩 | 风格 | 许可 | 覆盖 |
|---|---|---|---|---|
| `fuse3 color` | 彩色 | 品牌彩色 logo（红 UHD / 青 DOLBY / 橙 DTS） | CC BY-NC-SA 4.0 | 87/109 |
| `martian color` | 彩色 | 与 fuse3 同一设计语言，多出 HDR | CC BY-NC-SA 3.0 | 80/109 |
| `martian mono` | 白色 | 品牌白色剪影，带描边盒 | CC BY-NC-SA 3.0 | 78/109 |
| `tinyppi` | 白色 | 高分辨率品牌白标（512px），只覆盖编解码/HDR | AGPL-3.0 + 素材条款 | 27/109 |
| `limasky` | 白色 | 方框标签风（DOLBY-HD / DTS-MA / AAC），与上面两家不同族 | GPL-2.0 | 83/109 |

## 二、推荐组合的覆盖率

| 组合 | 覆盖 | 缺口 |
|---|---|---|
| 彩色 fuse3+martian | 94/109 | `8K`、`hdrvivid`、`hdr_vivid`、`hddvd`、`mjpeg`、`prores`、`tv`、`vhs`、`aac_latm`、`av3a`、`avc`、`wavpack`、`9`、`11`、`13` |
| 白色 tinyppi+martian | 90/109 | `8K`、`hdrvivid`、`hdr_vivid`、`bluray`、`dvd`、`hddvd`、`hdmv`、`mjpeg`、`prores`、`theora`、`tv`、`vhs`、`av3a`、`avc`、`wav`、`wavpack`、`9`、`11`、`13` |
| 白色 +limasky 兜底 | 100/109 | `hdrvivid`、`hdr_vivid`、`mjpeg`、`prores`、`theora`、`av3a`、`9`、`11`、`13` |

## 三、分项明细（推荐组合）

### 彩色 fuse3+martian

| 类别 | 命中 | 缺口 |
|---|---|---|
| 分辨率 | 6/7 | `8K` |
| HDR 类型 | 4/6 | `hdrvivid`、`hdr_vivid` |
| 视频编码 | 29/34 | `hddvd`、`mjpeg`、`prores`、`tv`、`vhs` |
| 音频编码 | 45/49 | `aac_latm`、`av3a`、`avc`、`wavpack` |
| 声道 | 10/13 | `9`、`11`、`13` |

### 白色 tinyppi+martian

| 类别 | 命中 | 缺口 |
|---|---|---|
| 分辨率 | 6/7 | `8K` |
| HDR 类型 | 4/6 | `hdrvivid`、`hdr_vivid` |
| 视频编码 | 25/34 | `bluray`、`dvd`、`hddvd`、`hdmv`、`mjpeg`、`prores`、`theora`、`tv`、`vhs` |
| 音频编码 | 45/49 | `av3a`、`avc`、`wav`、`wavpack` |
| 声道 | 10/13 | `9`、`11`、`13` |

### 白色 +limasky 兜底

| 类别 | 命中 | 缺口 |
|---|---|---|
| 分辨率 | 7/7 | — |
| HDR 类型 | 4/6 | `hdrvivid`、`hdr_vivid` |
| 视频编码 | 31/34 | `mjpeg`、`prores`、`theora` |
| 音频编码 | 48/49 | `av3a` |
| 声道 | 10/13 | `9`、`11`、`13` |

## 四、手绘补充（11 个）

| 值 | 做法 |
|---|---|
| `8K` | 改 `4K.png` 的 `2160p` → `4320p`，像素级，与原生无差 |
| `hdrvivid` | `HDR` 白 + `VIVID` 青双行，画布对齐 hdr10 |
| `aac_latm` | 复用 `aac.png` 同心弧 + 小号 `LATM` |
| `hddvd` | 白字标 `HD DVD`，深色圆角底 |
| `prores` | 白字标 `ProRes` |
| `theora` | 白字标 `Theora`（彩色版已有，只补白色） |
| `tv` | 白字标 `TV` |
| `vhs` | 白字标 `VHS`，深色圆角底 |
| `av3a` | 白字标 `AV3A` |
| `avc` | 白字标 `AVC` |
| `wavpack` | 白字标 `WavPack` |

## 五、放弃的 3 个

声道 `9` / `11` / `13`：对应不到任何真实音箱布局（5.1.2=8、7.1.2=10、7.1.4=12），
画出来是编造信息；按「只对纯 `N.M` 用图标」的白名单，它们本来就走文字分支。

