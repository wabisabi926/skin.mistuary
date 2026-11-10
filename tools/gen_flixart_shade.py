"""生成背景剧照的配套遮罩：底部垂直渐隐 + 35% 淡色光范围。

2026-11-10 起背景图铺满全屏（不再右上 2/3），左缘没有硬切线要柔化，
`flixart-shade.png` 已删除；左侧改由半透阅读遮罩 + 淡色光负责。

两张图：
  flixart-bottom.png     8x512       RGBA 黑，上 0 → 下 225（垂直，压住图底边）
  flixart-edge-glow.png 1920x1080   RGBA 白，左 1/3 恒定 35% 不透明，之后 20% 宽淡出

edge-glow 是「淡色光」层的 diffuse 遮罩：白色 RGB 不改变贴图颜色，alpha
决定模糊色光以多大透明度覆在清晰图上。35% 意味着清晰图保留 65%，只多一层
彩色光晕；2.2.0 的 100% 会把图左 1/3 整块换成模糊图，看起来像磨砂玻璃。
底部渐变的实际浓度由「背景压暗」设置（0.35/0.50/0.60/1.00）在运行时缩放，
这里按原浓度生成。

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
BOTTOM = MEDIA / 'flixart-bottom.png'
EDGE_GLOW = MEDIA / 'flixart-edge-glow.png'

SIDE_GAMMA = 1.3

BOTTOM_W, BOTTOM_H = 8, 512

# 屏幕尺寸，diffuse 随控件全屏拉伸；淡色光覆盖左 1/3，再用 20% 屏宽淡出。
EDGE_W, EDGE_H = 1920, 1080
EDGE_START = 1 / 3
EDGE_WIDTH = 0.20
EDGE_OPACITY = 0.35


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


def build_bottom():
    img = Image.new('RGBA', (BOTTOM_W, BOTTOM_H))
    px = img.load()
    for y in range(BOTTOM_H):
        a = bottom_alpha(y / (BOTTOM_H - 1))
        for x in range(BOTTOM_W):
            px[x, y] = (0, 0, 0, a)
    return img


def edge_alpha(t):
    """全屏横向：左 1/3 恒定 35% 不透明，之后 20% 屏宽淡出。

    35% 是「淡色光」的浓度：图保持清晰可辨，色光只做彩色光晕。
    淡出段沿用 side_alpha 的 gamma 曲线，保证边缘过渡与旧的黑色渐隐同手感。
    """
    if t <= EDGE_START:
        return round(255 * EDGE_OPACITY)
    k = (t - EDGE_START) / EDGE_WIDTH
    if k >= 1:
        return 0
    return round(side_alpha(k) * EDGE_OPACITY)


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

    targets = [(BOTTOM, build_bottom()), (EDGE_GLOW, build_edge_glow())]

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
