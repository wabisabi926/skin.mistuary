"""把「遮罩 + 三条渐变」烘成一张 720p overlay。

电影/电视剧/搜索原来用 4 个独立控件给文字做阅读区（遮罩 + 顶部渐变 + 底部渐变 +
左侧 scrim），四层都是纯黑 + alpha，合成结果和一张预烘焙的 PNG 等价。
烘焙后这些页面少画 3 层。720p 足够 —— 四层都是平滑渐变，拉伸到 1080p 看不出差别，
而 1080p 的 RGBA 要 8MB 一张，720p 只要 3.5MB。

三个变体（几何取自 Home.xml / Includes_Search.xml）：
  hero   遮罩 + 顶部 220 + 底部 420..1080 + 左侧 1200  —— 电影/电视剧/搜索结果
  list   遮罩 + 顶部 220 + 底部窄条 860..1080           —— 首页文件/收藏
  empty  遮罩 + 顶部 220 + 左侧 1200                    —— 搜索空查询（无底部渐变）

用法：
  python tools/gen_fanart_overlay.py            # 重新生成
  python tools/gen_fanart_overlay.py --check    # 只校验（CI 用）
"""
import argparse
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / 'media' / 'overlays'
W, H = 1280, 720

MASK = MEDIA / 'fanart-stage-mask.png'
FADE = MEDIA / 'overlayfade.png'
LEFT = MEDIA / 'detail-left-scrim.png'

# 屏幕几何按 1920×1080 写，输出时等比缩到 W×H
SCREEN_W, SCREEN_H = 1920, 1080
MASK_BOX = (-960, -540, 3840, 2160)     # 2 倍屏幕居中，只露中间 50%
TOP_STRIP = (0, 220, 0x33 / 255)        # 顶部 220px，colordiffuse 33FFFFFF
HERO_BOTTOM = (420, 660, 0xA0 / 255)    # top 420 / height 660，opacity_medium
LIST_BOTTOM = (860, 220, 0x4D / 255)    # top 860 / height 220，4DFFFFFF
LEFT_SCRIM = (1200, 1080)               # 左侧 1200×1080


def scale(value):
    return round(value * H / SCREEN_H)


def mask_layer():
    left, top, width, height = MASK_BOX
    img = Image.open(MASK).convert('RGBA').resize((width, height), Image.BILINEAR)
    visible = img.crop((-left, -top, -left + SCREEN_W, -top + SCREEN_H))
    return visible.resize((W, H), Image.BILINEAR)


def fade_layer(top, height, opacity, flip=False):
    img = Image.open(FADE).convert('RGBA').resize((W, scale(height)), Image.BILINEAR)
    if flip:
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
    img.putalpha(img.getchannel('A').point(lambda v: round(v * opacity)))
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    canvas.alpha_composite(img, (0, scale(top)))
    return canvas


def left_layer():
    width, height = LEFT_SCRIM
    img = Image.open(LEFT).convert('RGBA').resize((scale(width), scale(height)), Image.BILINEAR)
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    canvas.alpha_composite(img, (0, 0))
    return canvas


def compose(layers):
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for layer in layers:
        out.alpha_composite(layer)
    return out


def hero():
    return compose([
        mask_layer(),
        fade_layer(*TOP_STRIP, flip=True),
        fade_layer(*HERO_BOTTOM),
        left_layer(),
    ])


def listing():
    return compose([
        mask_layer(),
        fade_layer(*TOP_STRIP, flip=True),
        fade_layer(*LIST_BOTTOM),
    ])


def empty():
    return compose([
        mask_layer(),
        fade_layer(*TOP_STRIP, flip=True),
        left_layer(),
    ])


TARGETS = {
    'fanart-overlay-hero.png': hero,
    'fanart-overlay-list.png': listing,
    'fanart-overlay-empty.png': empty,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true', help='只校验产物是否最新')
    args = ap.parse_args()

    stale = []
    for name, build in TARGETS.items():
        path = MEDIA / name
        img = build()
        if args.check:
            if not path.exists():
                stale.append(f'{name}: 缺失')
            elif Image.open(path).convert('RGBA').tobytes() != img.tobytes():
                stale.append(f'{name}: 与生成器不一致')
            continue
        img.save(path)
        print(f'写出 {path.relative_to(ROOT)}  {img.size}')

    if args.check:
        if stale:
            print('✗ overlay 需要重新生成：')
            for line in stale:
                print('  -', line)
            print('  跑 python tools/gen_fanart_overlay.py')
            return 1
        print('✓ overlay 与生成器一致')
    return 0


if __name__ == '__main__':
    sys.exit(main())
