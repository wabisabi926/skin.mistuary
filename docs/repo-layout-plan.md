# 仓库目录整改方案：`extras/` 归位

日期：2026-10-27　状态：**已执行**

> 执行结果：`extras/` → `tools/`（14 个 .py + 5 个 .ps1 原样迁走，代码未改）；
> `backgrounds/` `home-images/` `playlists/` → `extras/`；XML 引用替换 30 处、
> 文档与工具内的路径替换 28 处；`release.yml` 改为排除 `tools/`、包含 `extras/`。
> 验证：`audit_skin.py --strict` 缺失贴图 0（它会真实校验 `special://skin/extras/...`）、
> 单测 42 项全绿、`gen_techflag_vars.py --check` 同步。

---

## 一、问题

现在仓库里的 `extras/` 装的是**构建期工具**（14 个 `.py` + 5 个 `.ps1`），
而 Arctic 系皮肤（jurialmunkey / narapeka 一脉）里 `extras/` 是**随包发布的素材包**，
运行时用 `special://skin/extras/...` 引用。名字撞车有三个后果：

1. 从别的皮肤过来的人会以为这里的 `extras/` 是素材目录，找不到东西；
2. 以后要移植 AF 系特性（可选背景包、图标包、viewtypes 预览图）没有约定位置；
3. 更实际的：`release.yml` 现在**整目录排除 `extras/`**，真往里放素材会被静默丢掉。

顺带一提，这个仓库早期确实是 AF 布局——`memory/2026-10-23.md` 里记着
`extras/backgrounds/primary.jpg`、`extras/home-images/{movie,music}.jpg`，
后来被挪到了根目录。

---

## 二、实测：Arctic Fuse 3 的 `extras/`（本机已装 `skin.arctic.fuse.3`）

| 目录 | 文件数 | 干什么 | 引用写法 | 本皮肤需要吗 |
|---|---|---|---|---|
| `backgrounds/` | 94 | 可选背景包 | `special://skin/extras/backgrounds/*.jpg`（139 处） | **要** —— 现有根目录 `backgrounds/primary.jpg` |
| `icons/` | 1792 | 可选图标包 | `special://skin/extras/icons/...`（523 处） | 暂不需要（图标在 `media/icons/`，且没有"换图标包"功能） |
| `playlists/` | 24 | widget 用的 `.xsp` | `special://skin/extras/playlists/*.xsp`（38 处） | **要** —— 现有根目录 `playlists/`（38 个） |
| `profiles/` | 15 | 背景预设缩略图 | `extras/profiles/...`（5 处） | 暂不需要 |
| `modes/` | 3 | widget 模式预览图 | `extras/modes/...`（3 处） | 不需要（没有 widget 模式切换） |
| `viewtypes/` | 34 | 视图类型预览图 | 设置页预览 | 不需要（视图切换没有预览图） |
| `hub/` | 50 | hub 页图片 | `extras/hub/...`（4 处） | 不需要（没有 hub 页） |
| `nodes/` | 1 | 自定义节点 XML | 由 `script.skinvariables` 读 | 不需要（用 Emby 动态节点） |
| `tmdbhelper/` | 1 | TMDbHelper `baseitem.json` | 由 TMDbHelper 读 | 不需要（不用 TMDbHelper） |
| `screenshots/` | 11 | 皮肤截图（README 用） | 无 | 可选，**而且不该进包** |

结论：**十个目录里我们实际只用得上两个（backgrounds / playlists），加上自己特有的 home-images。**
其余七个硬建空目录只会误导，写进 README 说明"将来做对应功能时再建"更合适。

---

## 三、目标结构

```
skin.mistuary/
├── addon.xml  changelog.txt  README.md  LICENSE  THIRD_PARTY_NOTICES.md
├── xml/  colors/  fonts/  language/  media/  resources/     ← 皮肤本体
├── extras/                       ← 随包发布的素材（新，进包）
│   ├── backgrounds/primary.jpg   ← 原 backgrounds/
│   ├── home-images/{movie,music}.jpg
│   └── playlists/*.xsp           ← 原 playlists/（38 个）
├── libraryart/                   ← 用户自备分类封面（留在根目录：体积大、可替换、gitignore）
├── tools/                        ← 构建期工具（原 extras/，不进包）
├── docs/                         ← 文档（不进包）
└── .github/                      ← CI（不进包）
```

为什么 `libraryart/` 不搬：它是**用户自己放图**的目录（`.gitignore` 只留 `default.jpg`），
路径一旦变化，已部署的 25 张封面就失效；而且它不在 AF 的 `extras/` 约定里。

为什么 `backgrounds/` 要搬进 `extras/`：它就是 AF 的 `extras/backgrounds` 语义（可替换背景），
现在只有一个 `primary.jpg`，将来要做"背景包选择"时直接往里加图即可，不用再动结构。

---

## 四、迁移步骤

### 步骤 1：开发工具改名（`extras/` → `tools/`）

```bash
git mv extras tools
```

需要同步改的引用（**只有 3 类，共 5 个文件**）：

| 文件 | 改什么 |
|---|---|
| `.github/workflows/release.yml` | `--exclude='extras/'` → `--exclude='tools/'`；test job 里 `python extras/audit_skin.py` 等 3 条命令 |
| `docs/README.md` | 「自检」代码块 4 条命令 |
| `docs/HANDOVER.md` | §3 仓库结构、§4 开发工具、§5 相关描述 |
| `docs/skin-contracts.md` | 附录里的验证命令 |
| `docs/glass-opacity-plan.md` | 生成脚本路径（若有） |

`tools/` 里的 Python **不需要改代码**：`audit_skin.py` 用 `Path(__file__).parent.parent`
定位仓库根，测试用 `Path(__file__).parent` 找同目录，改名后自动跟随。

### 步骤 2：素材归位（`backgrounds/`、`home-images/`、`playlists/` → `extras/`）

```bash
mkdir -p extras
git mv backgrounds extras/backgrounds
git mv home-images extras/home-images
git mv playlists extras/playlists
```

需要替换的 XML 引用（**共 30 处**，都在 `special://skin/` 前缀下）：

| 原路径 | 新路径 | 处数 |
|---|---|---|
| `special://skin/backgrounds/` | `special://skin/extras/backgrounds/` | 5 |
| `special://skin/home-images/` | `special://skin/extras/home-images/` | 1 |
| `special://skin/playlists/` | `special://skin/extras/playlists/` | 24 |

**批量替换前先数命中次数**（本项目踩过坑）：三条 `sed` 各跑一次，
替换后立刻 `grep` 确认旧路径 0 命中、新路径 30 命中。

### 步骤 3：打包规则

`release.yml` 的 `rsync` 排除项改一处即可：

```diff
-            --exclude='extras/' \
+            --exclude='tools/' \
```

`extras/` 从"被排除"变成"被包含"，随包发布。
`media/` 那条"只留 Textures.xbt"的清理**不影响** `extras/`（它是独立目录），
所以 `extras/` 里的图片是**松散文件**，用户可以替换——这正是 AF 的做法。

### 步骤 4：验证

```bash
# 1) 残留检查（应为 0）
grep -rn 'special://skin/backgrounds/\|special://skin/home-images/\|special://skin/playlists/' xml/
grep -rn 'python extras/' docs/ .github/

# 2) 静态自检会顺带验证 special://skin/ 下的贴图是否存在
python tools/audit_skin.py --strict
python -m unittest discover -s tools -p 'test_*.py'
python tools/gen_techflag_vars.py --check

# 3) 实机：背景、首页 widget 的播放列表、首页兜底图
```

`audit_skin.py` 的 `texture_exists()` 对 `special://skin/...` 会按仓库根解析，
所以 `extras/backgrounds/primary.jpg` 这类路径会被真实校验——搬错位置会直接报"缺失贴图"。

---

## 五、影响面与回滚

| 项 | 影响 |
|---|---|
| 发布包 | `extras/` 首次进包（约 620 KB：backgrounds 224K + home-images 349K + playlists 46K） |
| 已部署的实机 | 路径变化，必须重新 `robocopy /MIR` 一次；旧目录会被镜像删除 |
| 用户自定义 | 无（`libraryart/` 不动；`extras/` 里的文件本来就随包） |
| 回滚 | 三步 `git mv` 反向 + 还原 3 个文件即可，不涉及数据 |

---

## 六、执行顺序建议

1. **步骤 1（工具改名）先做**——它不碰运行路径，风险最低，先把 `extras/` 腾空。
2. 步骤 2/3 一起做（路径 + 打包是一件事，分两次会有一个中间态）。
3. 步骤 4 验证后再同步实机。

## 七、需要你确认的两点

1. 开发工具目录名用 **`tools/`** 可以吗？（备选 `dev/`、`scripts/`；`build/` 已被 CI 暂存目录占用）
2. `backgrounds/`、`home-images/`、`playlists/` 三个一起搬进 `extras/`，还是只搬 `playlists/`
   （它最符合 AF 约定）？我建议三个一起，语义统一。
