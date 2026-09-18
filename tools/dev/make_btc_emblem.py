#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_btc_emblem.py —— 官方比特币 ₿ 徽记复刻器（矢量光栅化）

来源：Wikimedia Commons《Bitcoin logo.svg》（公共领域，bitcoin.org 官方标识）。
原理：直接解析官方 SVG path 数据（贝塞尔曲线拍平 + 奇偶规则扫描线填充），
D 形孔 / 断笔缺口在数学上必然镂空——不是手绘，是复刻，与国际标准逐点一致。

产出（assets/brand/）：
    btc-emblem-official.png   橙圆 + 白 ₿（主标准件，1024 透明底）
    btc-symbol-white.png      纯白 ₿（深色底用）
    btc-symbol-orange.png     纯橙 ₿（浅色底用）
    btc-symbol-black.png      纯黑 ₿（印刷/白底用）
    btc-appicon-rounded.png   橙色圆角方 + 白 ₿（App 图标风格）
    btc-coin-white-mono.png   白圆 + 橙 ₿（深底反白币）
    btc-logo-lockup-white.png 币 + "bitcoin" 官方字标（白字，横版）
"""
import os
import re

from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'brand')

ORANGE = (247, 147, 26, 255)    # #F7931A 官方橙
WHITE = (255, 255, 255, 255)
BLACK = (17, 17, 17, 255)       # #111111 近纯黑

# ---- 官方 SVG path 数据（逐字取自 Bitcoin logo.svg, 公共领域） ----
D_CIRCLE = ("m352.64,357.25c-4.274,17.143-21.637,27.576-38.782,23.301"
            "-17.138-4.274-27.571-21.638-23.295-38.78,4.272-17.145,21.635-27.579,"
            "38.775-23.305,17.144,4.274,27.576,21.64,23.302,38.784z")

D_GLYPH = ("m335.71,344.95c0.637-4.258-2.605-6.547-7.038-8.074l1.438-5.768"
           "-3.511-0.875-1.4,5.616c-0.923-0.23-1.871-0.447-2.813-0.662l1.41-5.653"
           "-3.509-0.875-1.439,5.766c-0.764-0.174-1.514-0.346-2.242-0.527l0.004"
           "-0.018-4.842-1.209-0.934,3.75s2.605,0.597,2.55,0.634c1.422,0.355,"
           "1.679,1.296,1.636,2.042l-1.638,6.571c0.098,0.025,0.225,0.061,0.365,"
           "0.117-0.117-0.029-0.242-0.061-0.371-0.092l-2.296,9.205c-0.174,0.432"
           "-0.615,1.08-1.609,0.834,0.035,0.051-2.552-0.637-2.552-0.637l-1.743,"
           "4.019,4.569,1.139c0.85,0.213,1.683,0.436,2.503,0.646l-1.453,5.834,"
           "3.507,0.875,1.439-5.772c0.958,0.26,1.888,0.5,2.798,0.726l-1.434,5.745,"
           "3.511,0.875,1.453-5.823c5.987,1.133,10.489,0.676,12.384-4.739,1.527"
           "-4.36-0.076-6.875-3.226-8.515,2.294-0.529,4.022-2.038,4.483-5.155z"
           "m-8.022,11.249c-1.085,4.36-8.426,2.003-10.806,1.412l1.928-7.729c2.38,"
           "0.594,10.012,1.77,8.878,6.317zm1.086-11.312c-0.99,3.966-7.1,1.951"
           "-9.082,1.457l1.748-7.01c1.982,0.494,8.365,1.416,7.334,5.553z")

# 官方 "bitcoin" 字标（7 个字母路径, 原始 fill #4d4d4d）
D_WORDMARK = [
    "m383.38,336.87c2.595,0,4.837,0.465,6.721,1.378,1.893,0.922,3.455,2.164,4.708,3.726,1.236,1.57,2.156,3.405,2.75,5.508,0.59,2.109,0.886,4.376,0.886,6.803,0,3.728-0.683,7.25-2.062,10.57-1.379,3.325-3.25,6.209-5.63,8.669-2.378,2.457-5.186,4.394-8.424,5.825-3.233,1.432-6.748,2.148-10.522,2.148-0.488,0-1.346-0.014-2.558-0.039s-2.605-0.15-4.165-0.361c-1.57-0.219-3.23-0.543-4.983-0.977-1.752-0.426-3.416-1.023-4.983-1.781l14.012-58.876,12.55-1.945-5.017,20.893c1.074-0.484,2.156-0.859,3.236-1.132,1.081-0.269,2.241-0.409,3.481-0.409zm-10.527,34.671c1.89,0,3.671-0.465,5.344-1.378,1.678-0.914,3.126-2.148,4.339-3.685,1.213-1.544,2.173-3.283,2.873-5.226s1.054-3.97,1.054-6.079c0-2.591-0.433-4.612-1.296-6.073-0.863-1.455-2.46-2.187-4.779-2.187-0.76,0-1.739,0.145-2.953,0.404-1.218,0.275-2.308,0.846-3.285,1.705l-5.342,22.188c0.322,0.057,0.607,0.111,0.85,0.162,0.238,0.055,0.501,0.094,0.763,0.121,0.277,0.031,0.594,0.047,0.977,0.047s0.862,0.001,1.455,0.001z",
    "m411.46,380.37h-11.987l10.123-42.597h12.069l-10.205,42.597zm5.833-47.787c-1.673,0-3.19-0.498-4.536-1.496-1.357-0.992-2.029-2.519-2.029-4.577,0-1.132,0.23-2.194,0.686-3.196,0.463-1,1.068-1.861,1.826-2.593,0.757-0.726,1.634-1.306,2.63-1.743,1.002-0.43,2.068-0.645,3.204-0.645,1.672,0,3.181,0.498,4.532,1.496,1.346,1.003,2.023,2.53,2.023,4.577,0,1.136-0.229,2.202-0.689,3.202-0.457,1-1.062,1.861-1.82,2.593-0.751,0.727-1.636,1.305-2.63,1.738-1.003,0.437-2.065,0.644-3.197,0.644z",
    "m432.17,327.16,12.555-1.945-3.083,12.556h13.446l-2.428,9.878h-13.365l-3.56,14.9c-0.328,1.242-0.514,2.402-0.566,3.48-0.059,1.083,0.078,2.013,0.402,2.796,0.322,0.785,0.901,1.39,1.741,1.818,0.836,0.435,2.033,0.654,3.603,0.654,1.293,0,2.553-0.123,3.771-0.367,1.211-0.24,2.438-0.574,3.68-1.011l0.894,9.236c-1.62,0.594-3.374,1.105-5.264,1.535-1.893,0.436-4.134,0.646-6.724,0.646-3.724,0-6.611-0.553-8.668-1.654-2.054-1.109-3.506-2.624-4.375-4.542-0.857-1.911-1.24-4.114-1.133-6.596,0.111-2.488,0.486-5.103,1.133-7.857l7.941-33.527z",
    "m454.56,363.36c0-3.669,0.594-7.129,1.781-10.368,1.185-3.242,2.892-6.077,5.107-8.51,2.207-2.421,4.896-4.339,8.061-5.747,3.15-1.4,6.677-2.106,10.564-2.106,2.433,0,4.606,0.23,6.518,0.691,1.92,0.465,3.657,1.066,5.228,1.82l-4.134,9.4c-1.08-0.438-2.201-0.824-3.36-1.174-1.16-0.357-2.576-0.529-4.251-0.529-4.001,0-7.164,1.379-9.518,4.128-2.345,2.751-3.526,6.454-3.526,11.099,0,2.753,0.594,4.979,1.786,6.682,1.186,1.703,3.377,2.55,6.558,2.55,1.57,0,3.085-0.164,4.536-0.484,1.462-0.324,2.753-0.732,3.89-1.214l0.895,9.636c-1.516,0.588-3.188,1.119-5.022,1.584-1.838,0.449-4.026,0.682-6.563,0.682-3.349,0-6.184-0.49-8.503-1.455-2.32-0.98-4.237-2.281-5.747-3.929-1.518-1.652-2.608-3.581-3.282-5.795-0.674-2.212-1.018-4.536-1.018-6.961z",
    "m507.81,381.5c-2.861,0-5.346-0.436-7.454-1.299-2.102-0.863-3.843-2.074-5.22-3.644-1.379-1.562-2.411-3.413-3.118-5.546-0.707-2.132-1.047-4.493-1.047-7.08,0-3.245,0.521-6.489,1.574-9.724,1.048-3.242,2.603-6.155,4.661-8.744,2.042-2.593,4.561-4.713,7.527-6.366,2.963-1.642,6.371-2.468,10.199-2.468,2.809,0,5.281,0.437,7.418,1.3,2.127,0.861,3.879,2.082,5.264,3.644,1.37,1.57,2.411,3.413,3.111,5.549,0.705,2.128,1.053,4.495,1.053,7.084,0,3.235-0.514,6.479-1.534,9.724-1.021,3.229-2.536,6.149-4.536,8.744-1.996,2.589-4.492,4.708-7.49,6.354-2.994,1.646-6.466,2.472-10.408,2.472zm5.991-34.662c-1.777,0-3.348,0.516-4.693,1.535-1.35,1.031-2.484,2.327-3.398,3.89-0.924,1.57-1.609,3.282-2.072,5.143-0.459,1.865-0.684,3.628-0.684,5.303,0,2.703,0.436,4.808,1.293,6.323,0.869,1.507,2.43,2.265,4.699,2.265,1.783,0,3.346-0.512,4.699-1.542,1.342-1.023,2.477-2.32,3.398-3.886,0.918-1.562,1.609-3.279,2.072-5.143,0.453-1.859,0.684-3.632,0.684-5.304,0-2.696-0.434-4.806-1.299-6.319-0.864-1.507-2.432-2.265-4.699-2.265z",
    "m544.84,380.37h-11.997l10.123-42.597h12.075l-10.201,42.597zm5.824-47.787c-1.672,0-3.188-0.498-4.532-1.496-1.35-0.992-2.028-2.519-2.028-4.577,0-1.132,0.233-2.194,0.69-3.196,0.457-1,1.066-1.861,1.824-2.593,0.753-0.726,1.638-1.306,2.632-1.743,0.996-0.43,2.062-0.645,3.194-0.645,1.676,0,3.19,0.498,4.538,1.496,1.349,1.003,2.03,2.53,2.03,4.577,0,1.136-0.242,2.202-0.695,3.202s-1.062,1.861-1.817,2.593c-0.76,0.727-1.634,1.305-2.63,1.738-1.004,0.437-2.068,0.644-3.206,0.644z",
    "m563.68,339.71c0.91-0.266,1.926-0.586,3.031-0.934,1.109-0.348,2.348-0.672,3.732-0.964,1.369-0.301,2.914-0.545,4.613-0.734,1.699-0.193,3.635-0.287,5.786-0.287,6.322,0,10.68,1.841,13.086,5.512,2.404,3.671,2.82,8.695,1.26,15.063l-5.514,23h-12.066l5.344-22.516c0.326-1.406,0.582-2.765,0.771-4.093,0.191-1.316,0.18-2.476-0.043-3.48-0.213-0.992-0.715-1.804-1.494-2.433-0.791-0.619-1.986-0.93-3.607-0.93-1.563,0-3.153,0.168-4.776,0.492l-7.857,32.959h-12.071l9.805-40.655z",
]

TOKEN_RE = re.compile(r'[MmLlHhVvCcSsQqTtZz]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?')


def _cubic(p0, p1, p2, p3, n=24):
    pts = []
    for k in range(1, n + 1):
        t = k / n
        mt = 1 - t
        a = mt * mt * mt
        b = 3 * mt * mt * t
        c = 3 * mt * t * t
        e = t * t * t
        pts.append((a * p0[0] + b * p1[0] + c * p2[0] + e * p3[0],
                    a * p0[1] + b * p1[1] + c * p2[1] + e * p3[1]))
    return pts


def parse_path(d):
    """解析 SVG path → 子路径列表（每条为拍平后的点列）。"""
    tokens = TOKEN_RE.findall(d)
    subpaths, cur = [], []
    x = y = sx = sy = 0.0
    px = py = None            # 上一段三次曲线第二控制点（供 S 反射）
    i, cmd = 0, None

    def num():
        nonlocal i
        v = float(tokens[i])
        i += 1
        return v

    def flush():
        nonlocal cur
        if len(cur) >= 3:
            subpaths.append(cur)
        cur = []

    while i < len(tokens):
        t = tokens[i]
        if t.isalpha():
            cmd = t
            i += 1
            if cmd in 'Zz':
                flush()
                x, y = sx, sy
                px = py = None
                continue
        elif cmd is None:
            break

        rel = cmd.islower()
        C = cmd.upper()
        if C == 'M':
            if cur:
                flush()
            nx, ny = num(), num()
            if rel:
                x += nx
                y += ny
            else:
                x, y = nx, ny
            sx, sy = x, y
            px = py = None
            cmd = 'm' if rel else 'M'   # 后续隐式对变 lineto
        elif C == 'L':
            nx, ny = num(), num()
            if rel:
                x += nx
                y += ny
            else:
                x, y = nx, ny
            cur.append((x, y))
            px = py = None
        elif C == 'H':
            nx = num()
            x = x + nx if rel else nx
            cur.append((x, y))
            px = py = None
        elif C == 'V':
            ny = num()
            y = y + ny if rel else ny
            cur.append((x, y))
            px = py = None
        elif C == 'C':
            while i < len(tokens) and not tokens[i].isalpha():
                x1, y1, x2, y2, x3, y3 = (num(), num(), num(), num(), num(), num())
                if rel:
                    x1 += x
                    y1 += y
                    x2 += x
                    y2 += y
                    x3 += x
                    y3 += y
                cur.extend(_cubic((x, y), (x1, y1), (x2, y2), (x3, y3)))
                px, py = x2, y2
                x, y = x3, y3
        elif C == 'S':
            while i < len(tokens) and not tokens[i].isalpha():
                x2, y2, x3, y3 = num(), num(), num(), num()
                if rel:
                    x2 += x
                    y2 += y
                    x3 += x
                    y3 += y
                rx, ry = (2 * x - px, 2 * y - py) if px is not None else (x, y)
                cur.extend(_cubic((x, y), (rx, ry), (x2, y2), (x3, y3)))
                px, py = x2, y2
                x, y = x3, y3
        else:
            raise ValueError('unsupported command: %s' % cmd)
    flush()
    return subpaths


def rasterize_evenodd(subpaths, size, pad_frac=0.03, supersample=4):
    """奇偶规则扫描线填充 → 灰度 mask（孔洞必然镂空）。"""
    pts = [p for sp in subpaths for p in sp]
    minx = min(p[0] for p in pts)
    maxx = max(p[0] for p in pts)
    miny = min(p[1] for p in pts)
    maxy = max(p[1] for p in pts)
    span = max(maxx - minx, maxy - miny)
    scale = size * (1 - 2 * pad_frac) / span
    ox = (size - (maxx - minx) * scale) / 2
    oy = (size - (maxy - miny) * scale) / 2

    N = size * supersample
    edges = []
    for sp in subpaths:
        n = len(sp)
        for k in range(n):
            x0, y0 = sp[k]
            x1, y1 = sp[(k + 1) % n]
            X0 = (x0 - minx) * scale * supersample + ox * supersample
            Y0 = (y0 - miny) * scale * supersample + oy * supersample
            X1 = (x1 - minx) * scale * supersample + ox * supersample
            Y1 = (y1 - miny) * scale * supersample + oy * supersample
            if Y0 != Y1:
                edges.append((X0, Y0, X1, Y1))

    img = Image.new('L', (N, N), 0)
    dr = ImageDraw.Draw(img)
    for row in range(N):
        yc = row + 0.5
        xs = []
        for (ex0, ey0, ex1, ey1) in edges:
            if (ey0 <= yc) != (ey1 <= yc):
                t = (yc - ey0) / (ey1 - ey0)
                xs.append(ex0 + t * (ex1 - ex0))
        if not xs:
            continue
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            a = int(xs[k] + 0.5)
            b = int(xs[k + 1] + 0.5)
            if b > a:
                dr.line((a, row, b - 1, row), fill=255)
    return img.resize((size, size), Image.LANCZOS)


def mask_to_color(mask, color):
    out = Image.new('RGBA', mask.size, (0, 0, 0, 0))
    solid = Image.new('RGBA', mask.size, color)
    out.paste(solid, (0, 0), mask)
    return out


def circle_mask(size, supersample=4):
    """标准圆 mask（用于徽记圆底，比贝塞尔圆更圆）。"""
    N = size * supersample
    img = Image.new('L', (N, N), 0)
    dr = ImageDraw.Draw(img)
    m = int(N * 0.015)                     # 1.5% 边距
    dr.ellipse([m, m, N - 1 - m, N - 1 - m], fill=255)
    return img.resize((size, size), Image.LANCZOS)


def rounded_square(size, radius_frac, color, supersample=4):
    N = size * supersample
    img = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    r = int(N * radius_frac)
    dr.rounded_rectangle([0, 0, N - 1, N - 1], radius=r, fill=color)
    return img.resize((size, size), Image.LANCZOS)


def main():
    os.makedirs(OUT, exist_ok=True)
    circle_sp = parse_path(D_CIRCLE)
    glyph_sp = parse_path(D_GLYPH)

    # 1) 主标准件：橙圆 + 白 ₿（同一坐标系，相对位置与官方一致）
    emblem = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
    m_circle = circle_mask(1024)
    emblem.paste(mask_to_color(m_circle, ORANGE), (0, 0), m_circle)
    m_glyph = rasterize_evenodd(glyph_sp, 1024, pad_frac=0.015)
    emblem.paste(mask_to_color(m_glyph, WHITE), (0, 0), m_glyph)
    emblem.save(os.path.join(OUT, 'btc-emblem-official.png'))

    # 2) 纯 ₿ 符号三色
    for name, color in [('btc-symbol-white', WHITE),
                        ('btc-symbol-orange', ORANGE),
                        ('btc-symbol-black', BLACK)]:
        mask = rasterize_evenodd(glyph_sp, 1024, pad_frac=0.06)
        mask_to_color(mask, color).save(os.path.join(OUT, name + '.png'))

    # 3) App 图标风：橙圆角方 + 白 ₿
    app = rounded_square(1024, 0.2237, ORANGE)
    gm = rasterize_evenodd(glyph_sp, 660, pad_frac=0.02)
    app.paste(mask_to_color(gm, WHITE), ((1024 - 660) // 2, (1024 - 660) // 2), gm)
    app.save(os.path.join(OUT, 'btc-appicon-rounded.png'))

    # 4) 反白币：白圆 + 橙 ₿
    mono = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
    mono.paste(mask_to_color(m_circle, WHITE), (0, 0), m_circle)
    mo = rasterize_evenodd(glyph_sp, 1024, pad_frac=0.015)
    mono.paste(mask_to_color(mo, ORANGE), (0, 0), mo)
    mono.save(os.path.join(OUT, 'btc-coin-white-mono.png'))

    # 5) 横版字标锁排：币 + bitcoin 官方字标（白字）
    word_sp = []
    for d in D_WORDMARK:
        word_sp.extend(parse_path(d))
    all_sp = circle_sp + glyph_sp + word_sp
    pts = [p for sp in all_sp for p in sp]
    minx = min(p[0] for p in pts)
    maxx = max(p[0] for p in pts)
    miny = min(p[1] for p in pts)
    maxy = max(p[1] for p in pts)
    W_OUT, H_OUT = 2048, 428
    pad = 0.02
    scale = min(W_OUT * (1 - 2 * pad) / (maxx - minx),
                H_OUT * (1 - 2 * pad) / (maxy - miny))

    def render(sp_list, color, supersample=3):
        N_w, N_h = int(W_OUT * supersample), int(H_OUT * supersample)
        ox = (N_w - (maxx - minx) * scale * supersample) / 2
        oy = (N_h - (maxy - miny) * scale * supersample) / 2
        edges = []
        for sp in sp_list:
            n = len(sp)
            for k in range(n):
                x0, y0 = sp[k]
                x1, y1 = sp[(k + 1) % n]
                X0 = (x0 - minx) * scale * supersample + ox
                Y0 = (y0 - miny) * scale * supersample + oy
                X1 = (x1 - minx) * scale * supersample + ox
                Y1 = (y1 - miny) * scale * supersample + oy
                if Y0 != Y1:
                    edges.append((X0, Y0, X1, Y1))
        img = Image.new('L', (N_w, N_h), 0)
        dr = ImageDraw.Draw(img)
        for row in range(N_h):
            yc = row + 0.5
            xs = []
            for (ex0, ey0, ex1, ey1) in edges:
                if (ey0 <= yc) != (ey1 <= yc):
                    t = (yc - ey0) / (ey1 - ey0)
                    xs.append(ex0 + t * (ex1 - ex0))
            if not xs:
                continue
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                a = int(xs[k] + 0.5)
                b = int(xs[k + 1] + 0.5)
                if b > a:
                    dr.line((a, row, b - 1, row), fill=255)
        out = Image.new('RGBA', (N_w, N_h), (0, 0, 0, 0))
        out.paste(Image.new('RGBA', (N_w, N_h), color), (0, 0), img)
        return out.resize((W_OUT, H_OUT), Image.LANCZOS)

    lockup = Image.new('RGBA', (W_OUT, H_OUT), (0, 0, 0, 0))
    lockup.alpha_composite(render(circle_sp, ORANGE))
    lockup.alpha_composite(render(glyph_sp, WHITE))
    lockup.alpha_composite(render(word_sp, WHITE))
    lockup.save(os.path.join(OUT, 'btc-logo-lockup-white.png'))

    print('done ->', OUT)
    for f in sorted(os.listdir(OUT)):
        if f.startswith('btc-'):
            print('  ', f)


if __name__ == '__main__':
    main()
