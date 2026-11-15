# 截图目录

README 里引用的图片放这里。**只放最终成品图**，调试用的对比图、裁剪图不要进这个目录。

## 现有

| 文件 | 内容 | 来源 |
|---|---|---|
| `techflags.png` | 技术标识 108 枚图标一览（1200×662，分辨率 / 视频 / HDR / 音频 / 声道五行） | 由 `tools/gen_readme_sheet.py` 从 `media/techflags/color/` 拼成，**素材是真实的**；枚数标题由脚本动态统计，图标增删后重跑即可 |
| `home.jpg` | 首页电影分区（继续观看 + 媒体库，剧照铺满） | 实机截图 2026-11-15，1920×1080（全屏 DESKTOP） |
| `info.jpg` | 电影详情页（《年会不能停！》豆瓣 7.5 + 8.1、DOLBY/HEVC/DV/DTS/5.1 五标识） | 同上 |
| `wall.jpg` | 海报墙 7 列（圆角遮罩 + 评分环） | 同上 |
| `episodes.jpg` | 剧集详情页（《12.1枪杀大案》季标签 + 本季集卡片同屏） | 同上 |
| `search.jpg` | 搜索页（T9 键盘 + 全键盘按钮 + 剧照渐变背景） | 同上 |

## 还缺

**2026-11-15 已用 JSON-RPC 远程补拍**：Kodi 全屏 1920×1080（`videoscreen.screenmode=DESKTOP`），
导航走 `Input.Right` + 行末 `Input.Down` 换行（0.55s/步；只按 Right 会卡在行末撞滚动条），
`Input.Info` 打开详情页（窗口名在 Kodi 22 是「视频信息」，`Window.IsActive(movieinformation)`
infolabel 已失效，用 `System.CurrentWindow` 判断）。截图经 JPEG q88 压缩到 ≤480 KB。
还差两张：

| 拍什么 | 文件名 | 要求 |
|---|---|---|
| **音乐播放页**（右侧歌词 / 黑胶模式） | `music.jpg` | 需本地音乐库；开发机曲库为 0 首，无法拍 |
| **透明度对比**（同页「平衡」vs「实心」） | `opacity-a.jpg` / `opacity-b.jpg` | 同一页面、同一部片，只改透明度设置 |

拍完放本目录并在 README「界面预览」引用即可。要求同下。

### 怎么拍

- **Kodi 内置截图**：按 `PrintScreen`（Windows）或 `F11`，存到 Kodi 的临时目录；
  也可以在 设置 → 系统 → 日志 里找"截屏"按钮
- **Windows 通用**：`Win + Shift + S` 区域截图，或 `Alt + PrintScreen` 截当前窗口
- **别用手机拍屏幕** —— 会有摩尔纹和反光，README 上很难看

### 拍之前清掉这些

- 播放进度条、OSD（等它自动消失）
- 通知弹窗（Kodi 右下角）
- 调试用的红色标注、半透明遮罩
- 个人隐私：文件名里带本地路径的、私人片源名字的（可以换一部大众片）

## 注意

`docs/` 整个目录**不进发布包**（`release.yml` 里排除了），所以这里放多大的图都不影响
zip 体积。但为了 GitHub 页面加载速度，单张控制在 500 KB 以内，宽不超过 2000px。
