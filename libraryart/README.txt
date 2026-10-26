媒体库封面 / Media library covers
==================================

把图片放在本目录，文件名必须与 Kodi 里显示的库名完全一致。

Put images here. The file name must exactly match the library name shown in Kodi.

支持 .png 和 .jpg（同名时 png 优先）。
Both .png and .jpg are supported (png wins if both exist).

注意：放在本目录（皮肤内置目录）的图片**只认 .jpg**——Kodi 对加载不到的贴图会打一条
error，多试一个 .png 就等于每次启动多刷一屏假错误。需要 .png 的话，请在
「设置 - 外观 - 媒体库封面文件夹」里指定一个自定义目录，那个目录 png / jpg 都支持。
Note: only .jpg is picked up from this built-in folder. To use .png, point the
"Media library cover folder" setting at your own folder - both formats work there.

建议尺寸：640 × 360（16:9）。卡片本身是 320 × 180，用 2 倍图是为了焦点放大时不糊；
再大就是浪费——1920 × 1080 的图在这里只会让皮肤体积涨 15 倍。
其它比例会被裁成 16:9 再缩放填满卡片。
Recommended size: 640 x 360 (16:9). The card itself is 320 x 180; 2x keeps it sharp
when the focused card scales up. Larger is wasted - a 1920x1080 image just makes the
skin 15x bigger. Other ratios are centre-cropped to 16:9, then scaled to fill.

示例 / Examples
--------------
  华语电影.jpg
  外语电影.jpg
  动画电影.jpg
  临时.jpg
  国产剧.jpg
  欧美剧.jpg
  日韩剧.jpg
  纪录片.jpg
  国漫.jpg
  日番.jpg

说明
----
- 本目录是默认位置；在「设置 - 外观 - 媒体库封面文件夹」里指定了其它目录时，
  会优先使用设置里的目录。
- 文件名对不上、或没有对应图片时，卡片会显示原来的文件夹图标，不会出现空白。
