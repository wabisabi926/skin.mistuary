"""生成背景剧照的两张配套遮罩：左缘水平渐隐 + 底部垂直渐隐。

背景构图对齐 fuse3 的 flixart（`Includes_Constants.xml:73` 是 1280x720）：
清晰图只占屏幕右上角 2/3，左边和下方交给黑底。缩了就必须配渐变，
否则图片的底边和左边缘会是一条硬切线。

三张图：
  flixart-shade.png      512x8       RGBA 黑，左 alpha 255 → 右 0（水平，盖住图左缘）
  flixart-bottom.png     8x512       RGBA 黑，上 0 → 下 255（垂直，盖住图底边）
  flixart-edge-glow.png 1920x1080   RGBA 白，左 1/3 全不透明、之后 20% 宽淡出

edge-glow 是给「色光过渡层」用的 diffuse 遮罩：白色 RGB 不改变贴图颜色，
alpha 决定色光覆盖清晰图左缘的范围。fuse3 是给清晰图贴 diffuse 让左缘透明，
我们用同一张色光图 + 全屏 alpha 遮罩覆在清晰图上，效果等价，且不用依赖
multiimage 的 imagepath 是否支持 diffuse。黑色渐隐层常驻、不与色光层互斥：
色光 jpg 异步加载的那几帧由它兜住清晰图左缘，不会一闪露出硬切线，
属性为空时也就是原来的纯黑渐隐，零回归。
底部曲线比线性更陡：图片底边落在屏幕 2/3 处，那里要已经压到约 78%，
否则「暗图 → 纯黑」还是一眼能看出台阶。

用法：
  python tools/gen_flixart_shade.py            # 重新生成
  python tools/gen_flixart_shade.py --check    # 只校验（CI 用）
"""
import argparse
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / 'media' / 'overlays'
SHADE = MEDIA / 'flixart-shade.png'
BOTTOM = MEDIA / 'flixart-bottom.png'
EDGE_GLOW = MEDIA / 'flixart-edge-glow.png'

SHADE_W, SHADE_H = 512, 8
SIDE_GAMMA = 1.3

BOTTOM_W, BOTTOM_H = 8, 512

# 屏幕尺寸，diffuse 随控件全屏拉伸；清晰图从 1/3 开始，渐隐带占屏 20%。
EDGE_W, EDGE_H = 1920, 1080
EDGE_START = 1 / 3
EDGE_WIDTH = 0.20


def side_alpha(t):
    return round(255 * (1 - t) ** SIDE_GAMMA)


def bottom_alpha(t):
    """屏幕纵向：0~0.4 全透，0.4~0.72 升到 200，0.72~1 收到 225。

    峰值不用 255：底色已经是 fanart_void（#0F0F12），再压到纯黑就成了死黑，
    右下角会像被切掉一块。225 相当于 88%，留一点底色透气。
    """
    if t <= 0.40:
        return 0
    if t <= 0.72:
        k = (t - 0.40) / 0.32
        return round(200 * k ** 1.2)
    k = (t - 0.72) / 0.28
    return round(200 + 25 * k ** 0.9)


def build_shade():
    img = Image.new('RGBA', (SHADE_W, SHADE_H))
    px = img.load()
    for x in range(SHADE_W):
        a = side_alpha(x / (SHADE_W - 1))
        for y in range(SHADE_H):
            px[x, y] = (0, 0, 0, a)
    return img


def build_bottom():
    img = Image.new('RGBA', (BOTTOM_W, BOTTOM_H))
    px = img.load()
    for y in range(BOTTOM_H):
        a = bottom_alpha(y / (BOTTOM_H - 1))
        for x in range(BOTTOM_W):
            px[x, y] = (0, 0, 0, a)
    return img


def edge_alpha(t):
    """全屏横向：清晰图左侧全遮，左缘 20% 宽淡出，之后不遮。

    与 side_alpha 用同一条 gamma 曲线，保证「色光版」和「黑色版」的渐隐
    宽度、衰减手感完全一致，切换开关时构图不会跳。
    """
    if t <= EDGE_START:
        return 255
    k = (t - EDGE_START) / EDGE_WIDTH
    if k >= 1:
        return 0
    return side_alpha(k)


def build_edge_glow():
    """白色 RGB + alpha 渐变，作 diffuse 用；先画一行再纵向复制，避免百万次循环。"""
    row = Image.new('RGBA', (EDGE_W, 1))
    px = row.load()
    for x in range(EDGE_W):
        px[x, 0] = (255, 255, 255, edge_alpha(x / (EDGE_W - 1)))
    return row.resize((EDGE_W, EDGE_H), Image.NEAREST)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='只校验，不写文件')
    args = parser.parse_args()

    targets = [(SHADE, build_shade()), (BOTTOM, build_bottom()),
               (EDGE_GLOW, build_edge_glow())]

    if args.check:
        failed = False
        for path, img in targets:
            if not path.exists():
                print(f'[FAIL] 缺少 {path.name}，运行 python tools/gen_flixart_shade.py 生成')
                failed = True
                continue
            current = Image.open(path).convert('RGBA')
            if current.size != img.size:
                print(f'[FAIL] {path.name} 尺寸应为 {img.size}，实际 {current.size}')
                failed = True
            elif current.tobytes() != img.tobytes():
                print(f'[FAIL] {path.name} 与生成器不一致，请重新生成')
                failed = True
            else:
                print(f'[OK]   {path.name} {img.size[0]}x{img.size[1]} 与生成器一致')
        return 1 if failed else 0

    MEDIA.mkdir(parents=True, exist_ok=True)
    for path, img in targets:
        img.save(path)
        print(f'[OK]   写出 {path} ({img.size[0]}x{img.size[1]})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
