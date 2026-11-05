# 给 Kodi 皮肤接入 Emby 媒体库封面

> **2026-11-05 实测更正（针对本皮肤）**
>
> 1. **节点 label 有两种前缀**：`EMBY: ` 和 `EMBY DYNAMIC: `；类型也不止
>    `movies` / `tvshows`，还有 `boxsets` / `mixedvideo`。下面 `library_icons()`
>    只认 `emby: ` 前缀，会把本机 14 个库里的 8 个动态节点全部漏掉。
> 2. **`<texture fallback="…">` 在官方 Kodi 上无效**：`CGUIControlFactory::GetTexture`
>    只解析 `border` / `infill` / `flipx` / `flipy` / `diffuse` / `colordiffuse` /
>    `background` / `mipmap` / `subpixel`。取不到图时什么也不画，兜底必须用下层图层
>    （证据见 `skin-contracts.md` §6.4，历史上有 69 处已改掉）。
> 3. **本皮肤首页媒体库行是 `videodb://movies/tags/`**，条目不带 art；要用本方案
>    必须由 Helper 接管整行（换成 `plugin://` 列表）。本皮肤当前采用本地落盘方案
>    （`addon_data/script.mistuary.helper/library_icons/<库名>.png`），Emby 离线也能显示。
>    本文保留作参考，不作为现行实现。

适用场景：已经通过 Kodi 的 tags 找到同步媒体库，希望用 Python helper 给媒体库入口补图。

## 图片从哪里拿

读取当前 Kodi 配置中的 Gen 节点：

```text
special://profile/library/video/emby_movies_*/index.xml
special://profile/library/video/emby_tvshows_*/index.xml
```

节点示例：

```xml
<node order="0">
    <label>EMBY: 电影库 (movies)</label>
    <icon>图片地址</icon>
</node>
```

去掉 label 的 `EMBY: ` 前缀和最后的 ` (movies)`／` (tvshows)`，与已有 tag 名称匹配；将 **icon 的原值**交给 Kodi。

`icon` 可能是本地文件、HTTP 地址或 `image://…` 地址。不要自行解码、重新编码或下载，也不要猜测 `library_icons/` 目录。让 Kodi 图片系统处理地址及缓存。

## Helper 核心代码

以下函数每次刷新列表调用一次，返回“库名 → 图片地址”的映射。`content` 使用 `movies` 或 `tvshows`。

```python
import xml.etree.ElementTree as ET
import xbmcvfs


def library_icons(content):
    base = "special://profile/library/video/"
    folders, _ = xbmcvfs.listdir(base)
    prefix = f"emby_{content}_"
    suffix = f" ({content})"
    exact, mixed = {}, {}

    for folder in folders:
        if not folder.casefold().startswith(prefix):
            continue
        path = f"{base}{folder}/index.xml"
        if not xbmcvfs.exists(path):
            continue
        f = xbmcvfs.File(path)
        data = f.read()
        f.close()
        root = ET.fromstring(data)
        label = root.findtext("label", "")
        icon = root.findtext("icon", "")
        if not (label.casefold().startswith("emby: ")
                and label.casefold().endswith(suffix)):
            continue
        name = label[6:-len(suffix)]
        exact[name.casefold()] = icon
        # 部分混合库的节点标签会重复追加类型后缀。
        if name.casefold().endswith(suffix):
            mixed[name[:-len(suffix)].casefold()] = icon

    return {**mixed, **exact}
```

在 helper 自己生成媒体库入口的代码中接入：

```python
icons = library_icons("movies")  # 剧集使用 tvshows
# 遍历已有 tags 时：tag_name、target_url 沿用现有代码。
item = xbmcgui.ListItem(label=tag_name)
icon = icons.get(tag_name.casefold(), "")
item.setArt({"thumb": icon, "icon": icon})
xbmcplugin.addDirectoryItem(handle, target_url, item, isFolder=True)
```

上述接入片段需要 `import xbmcgui, xbmcplugin`；`handle` 是插件目录句柄。皮肤以 helper 的 `plugin://插件ID/…` 为列表内容源，卡片读取：

> 注意：下面的 `fallback` 属性官方 Kodi 不支持（见文首第 2 条），取不到图时不会显示占位；
> 实际落地要在下面再垫一层兜底图。

```xml
<texture background="true" fallback="DefaultMovies.png">$INFO[ListItem.Art(thumb)]</texture>
```

## 接入时注意

- helper 必须返回携带 artwork 的列表项。普通脚本不能直接给皮肤现有的原生 `videodb://` 容器条目追加图片；可以沿用已有 tags 和跳转地址，由 helper 重新提供列表。
- 图片解析与媒体库识别分开：匹配不到图片时保留入口，显示默认图。需要封面兜底时，不要因此丢掉整个库。
- `image://…127.0.0.1…` 地址首次加载通常需要 Gen 服务已启动；已有纹理缓存时可以直接使用缓存。
- 当前配置必须有对应节点；服务器上有库、只有动态浏览入口，并不保证存在这些同步节点。多个服务器同名库无法仅靠库名可靠区分。
