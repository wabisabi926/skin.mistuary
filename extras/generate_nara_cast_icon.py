"""生成详情页「演员」开关图标：三个人（前一大、后两小），线性描边风格。

输出 media/icons/infodialogs/cast.png（64x64，白色不透明像素 + 透明底，
由皮肤用 colordiffuse="text_primary" 上色）。

用法：
    python extras/generate_nara_cast_icon.py
"""

from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 64          # 最终尺寸
SS = 16            # 超采样倍数
STROKE = 3.0       # 主描边宽度（64 空间）
STROKE_BACK = 2.6  # 后排描边
HALO = 2.4         # 前后人物之间的留白

OUT = Path(__file__).resolve().parent.parent / "media/icons/infodialogs/cast.png"


def s(v):
    return v * SS


def person(cx, head_cy, head_r, body_cy, body_rx, body_ry, bottom, stroke):
    """返回一组绘图指令：头（圆）+ 肩（上半个椭圆弧 + 两条竖边）。"""
    return {
        "head": (cx, head_cy, head_r),
        "body": (cx, body_cy, body_rx, body_ry, bottom),
        "stroke": stroke,
    }


def draw_person(draw, p, width, color):
    cx, cy, r = p["head"]
    draw.ellipse(
        [s(cx - r), s(cy - r), s(cx + r), s(cy + r)],
        outline=color,
        width=int(round(s(width))),
    )
    bcx, bcy, brx, bry, bottom = p["body"]
    draw.arc(
        [s(bcx - brx), s(bcy - bry), s(bcx + brx), s(bcy + bry)],
        start=180,
        end=360,
        fill=color,
        width=int(round(s(width))),
    )
    for edge in (bcx - brx, bcx + brx):
        draw.line([s(edge), s(bcy), s(edge), s(bottom)], fill=color, width=int(round(s(width))))


def body_polygon(p, steps=64):
    """肩部区域的实心多边形（用于挖掉后排人物）。"""
    bcx, bcy, brx, bry, bottom = p["body"]
    pts = [(bcx - brx, bottom)]
    for i in range(steps + 1):
        import math

        a = math.pi + math.pi * i / steps
        pts.append((bcx + brx * math.cos(a), bcy + bry * math.sin(a)))
    pts.append((bcx + brx, bottom))
    return pts


def main():
    img = Image.new("RGBA", (SIZE * SS, SIZE * SS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    front = person(32, 18.5, 8, 49, 13, 17, 55, STROKE)
    back_l = person(13, 25.5, 5.2, 48, 8.5, 12, 54, STROKE_BACK)
    back_r = person(51, 25.5, 5.2, 48, 8.5, 12, 54, STROKE_BACK)

    # 1) 后排两人
    for p in (back_l, back_r):
        draw_person(draw, p, p["stroke"], (255, 255, 255, 255))

    # 2) 把前排人物的“实心轮廓 + 留白”从图层里抠掉，让后排在前排处断开
    cut = Image.new("L", img.size, 0)
    cdraw = ImageDraw.Draw(cut)
    hx, hy, hr = front["head"]
    cdraw.ellipse(
        [s(hx - hr - HALO), s(hy - hr - HALO), s(hx + hr + HALO), s(hy + hr + HALO)], fill=255
    )
    poly = [(s(x), s(y)) for x, y in body_polygon(front)]
    cdraw.polygon(poly, fill=255)
    # 边界再向外扩一圈，形成留白
    cdraw.line(poly + [poly[0]], fill=255, width=int(round(s(HALO * 2))), joint="curve")
    img.putalpha(Image.composite(Image.new("L", img.size, 0), img.getchannel("A"), cut))

    # 3) 前排人物
    draw = ImageDraw.Draw(img)
    draw_person(draw, front, front["stroke"], (255, 255, 255, 255))

    out = img.resize((SIZE, SIZE), Image.LANCZOS)
    # 去掉 LANCZOS 在边缘留下的 alpha=1~4 的振铃，避免包围盒撑到画布边界
    out.putalpha(out.getchannel("A").point(lambda v: 0 if v < 8 else v))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.save(OUT)
    print(f"written {OUT}  bbox={out.getbbox()}")


if __name__ == "__main__":
    main()
