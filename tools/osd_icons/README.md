# OSD 图标源文件

这里放 OSD 主控按钮（上一首 / 播放 / 下一首 / 暂停）的 **SVG 源**。

> **2026-10-29：生成脚本和产物已删除。** 这四个实心图标做出来之后 OSD 改成了描边方案，
> 一直没人引用（`grep -rn '_filled' xml/` 零命中），属于死资源。
> 源 SVG 保留在这里（不随包发布），将来真要做「实心 / 空心两态」按钮时，
> 从 git 历史恢复 `tools/gen_osd_filled_icons.py` 再跑一次即可：
> `git log --all --oneline -- tools/gen_osd_filled_icons.py`

| 文件 | 用于 | 说明 |
|---|---|---|
| `play_arrow.svg` | `play_filled.png` | 主键「播放」 |
| `pause.svg` | `pause_filled.png` | 主键「暂停」 |
| `skip_previous.svg` | `previous_filled.png` | 上一首 |
| `skip_previous.svg`（镜像） | `next_filled.png` | 下一首 |

## 来源与许可

图标取自 **Material Symbols Rounded（FILL=1）**，Google 出品，**Apache License 2.0**。

- 上游：<https://fonts.google.com/icons> / npm `@material-symbols/svg-400`
- 许可：<https://www.apache.org/licenses/LICENSE-2.0>

选它而不是从别的皮肤搬图标，是因为多数 Kodi 皮肤（如 Arctic Fuse）是
**CC BY-NC-SA 4.0**（禁止商用 + 相同方式共享），把它们的素材并入本皮肤
会让整套作品被迫改成非商用许可。Apache-2.0 没有这个传染性。

## 重新生成

```bash
pip install resvg-py          # Rust 版 SVG 渲染器，自带二进制
python tools/gen_osd_filled_icons.py
```

输出统一 192×192、纯白、真透明；Kodi 里按 40~48px 使用。
