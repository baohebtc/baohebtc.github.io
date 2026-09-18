# -*- coding: utf-8 -*-
"""
baohe-kit.py · 慢读宝盒 母品牌视觉资产库
=====================================
ADR-0004：宝盒图标 = 母品牌 logo（封面/头像/文章头图共用）。
系列色带可配置：宝盒比特币 #F7931A / 宝盒以太坊 #627EEA（预留）。

用法（供其他模板 import）：
    from baohe_kit import draw_baohe_box, SERIES, FONT
"""
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
import math

# ---------- 系列（子品牌）注册表：新增系列只需加一行 ----------
SERIES = {
    'btc': {
        'zh': '宝盒比特币', 'en': 'BAOHE BITCOIN',
        'color': (247, 147, 26),     # #F7931A 官方橙
        'color_dim': (196, 112, 12),
        'accent': (255, 209, 120),   # 橙金高光
    },
    'eth': {
        'zh': '宝盒以太坊', 'en': 'BAOHE ETHEREUM',
        'color': (98, 126, 234),     # #627EEA 官方紫蓝
        'color_dim': (66, 90, 178),
        'accent': (150, 175, 245),
    },
}

# ---------- 母品牌色 ----------
BG_DARK = (22, 17, 12)        # 暖黑 #16110C
PAPER = (251, 246, 236)       # 纸白 #FBF6EC
WARM_WHITE = (255, 248, 231)  # #FFF8E7
MUTED = (168, 156, 138)       # 暖灰
DIM = (120, 110, 96)

_FONT_PATHS = [
    '/System/Library/Fonts/PingFang.ttc',
    '/System/Library/Fonts/Supplemental/Songti.ttc',
]


def FONT(size, serif=False):
    """中文字体；serif=True 用宋体（标题衬线）"""
    if serif:
        try:
            return ImageFont.truetype('/System/Library/Fonts/Supplemental/Songti.ttc', size, index=4)
        except Exception:
            pass
    for i in range(4):
        try:
            return ImageFont.truetype(_FONT_PATHS[0], size, index=i)
        except Exception:
            continue
    return ImageFont.load_default()


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def radial_glow(size, color, max_alpha=90):
    """径向光晕图层（RGBA）"""
    m = Image.new('L', (size, size), 0)
    d = ImageDraw.Draw(m)
    c = size // 2
    for r in range(c, 0, -2):
        a = int(max_alpha * (1 - r / c) ** 1.8)
        d.ellipse([c - r, c - r, c + r, c + r], fill=a)
    glow = Image.new('RGBA', (size, size), color + (0,))
    glow.putalpha(m)
    return glow


def draw_baohe_box(canvas, cx, cy, s, series='btc', glow=True, mini=False):
    """
    程序化绘制「宝盒」logo：等距开启宝箱 + 盒口光柱 + 浮起系列币。
    canvas: RGB Image；cx,cy: 盒身中心；s: 盒身半宽（整体≈3.2s 宽、3.6s 高）
    mini=True: 品牌行小图模式——只画盒身+开口，无盖/币/光柱
    """
    col = SERIES.get(series, SERIES['btc'])['color']
    accent = SERIES.get(series, SERIES['btc'])['accent']
    d = ImageDraw.Draw(canvas, 'RGBA')
    K = 0.5  # 等距 2:1

    if mini:
        hw, hh = s, s * K
        bh = s * 1.1
        top = [(cx - hw, cy), (cx, cy + hh), (cx + hw, cy), (cx, cy - hh)]
        left = [(cx - hw, cy), (cx, cy + hh), (cx, cy + hh + bh), (cx - hw, cy + bh)]
        right = [(cx, cy + hh), (cx + hw, cy), (cx + hw, cy + bh), (cx, cy + hh + bh)]
        d.polygon(left, fill=_lerp(col, (10, 8, 6), 0.30))
        d.polygon(right, fill=_lerp(col, (10, 8, 6), 0.12))
        d.polygon(top, fill=_lerp(col, (12, 9, 6), 0.45))
        ok_ = 0.6
        d.polygon([(cx - hw * ok_, cy), (cx, cy + hh * ok_),
                   (cx + hw * ok_, cy), (cx, cy - hh * ok_)], fill=(14, 10, 6))
        # 微光从盒口冒出
        g = radial_glow(int(s * 2.6), accent, max_alpha=60)
        canvas.paste(g, (int(cx - s * 1.3), int(cy - s * 1.3)), g)
        return

    # --- 光晕（盒后） ---
    if glow:
        g = radial_glow(int(s * 6), col, max_alpha=70)
        canvas.paste(g, (int(cx - s * 3), int(cy - s * 3)), g)

    # --- 盒身（等距立方体下半，h=1.35s） ---
    hw, hh = s, s * K          # 半宽/半菱高
    bh = s * 1.35              # 盒身高
    top = [(cx - hw, cy), (cx, cy + hh), (cx + hw, cy), (cx, cy - hh)]
    left_face = [(cx - hw, cy), (cx, cy + hh), (cx, cy + hh + bh), (cx - hw, cy + bh)]
    right_face = [(cx, cy + hh), (cx + hw, cy), (cx + hw, cy + bh), (cx, cy + hh + bh)]
    d.polygon(left_face, fill=_lerp(col, (10, 8, 6), 0.40))
    d.polygon(right_face, fill=_lerp(col, (10, 8, 6), 0.18))
    d.polygon(top, fill=_lerp(col, (12, 9, 6), 0.55))

    # 盒身装饰线（箱箍）
    for t, w in [(0.22, 3), (0.78, 3)]:
        d.line([ (cx - hw, cy + bh * t), (cx, cy + hh + bh * t) ], fill=accent + (120,), width=w)
        d.line([ (cx, cy + hh + bh * t), (cx + hw, cy + bh * t) ], fill=accent + (120,), width=w)

    # --- 盒口内衬（顶面挖出的开口菱形） ---
    open_k = 0.66
    mouth = [(cx - hw * open_k, cy), (cx, cy + hh * open_k), (cx + hw * open_k, cy), (cx, cy - hh * open_k)]
    d.polygon(mouth, fill=(14, 10, 6))

    # --- 盒口光柱（向上渐隐的梯形光） ---
    beam_h = s * 1.5
    beam = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(beam)
    bw1, bw2 = hw * open_k * 0.9, hw * open_k * 1.5
    bd.polygon([
        (cx - bw1, cy - 2), (cx + bw1, cy - 2),
        (cx + bw2, cy - beam_h), (cx - bw2, cy - beam_h),
    ], fill=accent + (150,))
    beam = beam.filter(ImageFilter.GaussianBlur(6))
    canvas.alpha_composite(beam) if canvas.mode == 'RGBA' else canvas.paste(
        Image.alpha_composite(canvas.convert('RGBA'), beam).convert('RGB'), (0, 0))

    # --- 掀开的盖（等距薄菱形，悬浮在盒口上方偏右后） ---
    lift = s * 0.42
    gx, gy = cx + s * 0.10, cy - hh - bh * 0.42 - lift   # 盖心
    gw, gh = s * 1.06, s * 1.06 * K
    cap_top = [(gx - gw, gy), (gx, gy + gh), (gx + gw, gy), (gx, gy - gh)]
    cap_l = [(gx - gw, gy), (gx, gy + gh), (gx, gy + gh + s * 0.28), (gx - gw, gy + s * 0.28)]
    cap_r = [(gx, gy + gh), (gx + gw, gy), (gx + gw, gy + s * 0.28), (gx, gy + gh + s * 0.28)]
    d.polygon(cap_l, fill=_lerp(col, (10, 8, 6), 0.38))
    d.polygon(cap_r, fill=_lerp(col, (10, 8, 6), 0.18))
    d.polygon(cap_top, fill=_lerp(col, (12, 9, 6), 0.50))

    # --- 浮起的系列币（盒口正上方光柱中，₿/Ξ 用程序化字符圆） ---
    coin_r = s * 0.52
    coin_cy = cy - hh - s * 0.62
    # 币底光
    cg = radial_glow(int(coin_r * 5), accent, max_alpha=110)
    canvas.paste(cg, (int(cx - coin_r * 2.5), int(coin_cy - coin_r * 2.5)), cg)
    d.ellipse([cx - coin_r, coin_cy - coin_r, cx + coin_r, coin_cy + coin_r],
              fill=col, outline=accent + (200,), width=max(2, int(coin_r * 0.10)))
    if series == 'btc':
        # ₿：官方形 —— B + 上下贯穿横划，整体右倾 14°
        bf = FONT(int(coin_r * 1.55))
        b_img = Image.new('RGBA', (int(coin_r * 3.2), int(coin_r * 3.2)), (0, 0, 0, 0))
        bd2 = ImageDraw.Draw(b_img)
        bcx = b_img.width / 2
        bb = bd2.textbbox((0, 0), 'B', font=bf)
        bcy2 = b_img.height / 2
        bd2.text((bcx - (bb[0] + bb[2]) / 2, bcy2 - (bb[1] + bb[3]) / 2), 'B', font=bf, fill=WARM_WHITE)
        bl = d.textlength('B', font=bf)
        pen = max(2, int(coin_r * 0.10))
        # 官方 ₿：横划从 B 左侧贯穿到右缘外
        bd2.line([bcx - bl * 0.52, bcy2 - coin_r * 0.50, bcx + bl * 0.52, bcy2 - coin_r * 0.50], fill=WARM_WHITE, width=pen)
        bd2.line([bcx - bl * 0.52, bcy2 + coin_r * 0.50, bcx + bl * 0.52, bcy2 + coin_r * 0.50], fill=WARM_WHITE, width=pen)
        b_img = b_img.rotate(14, resample=Image.BICUBIC, center=(bcx, bcy2))
        canvas.paste(b_img, (int(cx - b_img.width / 2), int(coin_cy - b_img.height / 2)), b_img)
    else:
        ef = FONT(int(coin_r * 1.2))
        eb = d.textbbox((0, 0), 'Ξ', font=ef)
        d.text((cx - (eb[0] + eb[2]) / 2, coin_cy - (eb[1] + eb[3]) / 2), 'Ξ', font=ef, fill=WARM_WHITE)


def series_chip(d, x_right, y, series, fs=15):
    """系列色带 chip：● 宝盒比特币 · 学习连载（返回占用宽度）"""
    col = SERIES[series]['color']
    zh = SERIES[series]['zh']
    f = FONT(fs)
    text = f'{zh} · 学习连载'
    w = d.textlength(text, font=f)
    dot_r = fs * 0.38
    total = w + dot_r * 2 + 12
    d.ellipse([x_right - total, y + fs / 2 - dot_r, x_right - total + dot_r * 2, y + fs / 2 + dot_r], fill=col)
    d.text((x_right - total + dot_r * 2 + 12, y), text, font=f, fill=MUTED, anchor='lm')
    return total


if __name__ == '__main__':
    # 自测：深底画一个大宝盒
    im = Image.new('RGB', (600, 640), BG_DARK)
    draw_baohe_box(im, 300, 390, 80)
    im.save('/tmp/baohe-box-test.png')
    print('saved /tmp/baohe-box-test.png')
