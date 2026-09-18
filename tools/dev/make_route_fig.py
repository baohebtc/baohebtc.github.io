# -*- coding: utf-8 -*-
"""
make_route_fig.py · 文章内「寻宝路线图」回扣图（ADR-0004）
==========================================================
替代位图地图裁切：程序化矢量蛇形路线，10 站进度一览。
1200×900 浅纸底；已走=系列色实心，当前=大圆光环+站名牌，未来=空心。
可扩展：--series eth 换色即成宝盒以太坊路线图。

用法：python3 make_route_fig.py <站号> <输出路径> [--series btc]
"""
import argparse
import os
import sys

sys.path.insert(0, '/Users/mac/Desktop/宝盒知识库/比特币学习地图/tools/dev')
from baohe_kit import SERIES, FONT, draw_baohe_box, series_chip

from PIL import Image, ImageDraw

W, H = 1200, 900
PAPER = (251, 246, 236)
INK = (42, 34, 24)
MUTED = (140, 126, 104)
LINE_OFF = (216, 204, 182)

STATIONS = [
    ('1', '现金湾'), ('1.5', '钱到底是什么'), ('2', '银行堡'), ('3', '双花峡'),
    ('4', '账本海'), ('5', '哈希岭'), ('6', '共识峰'), ('7', '矿工谷'),
    ('8', '私钥崖'), ('9', '代码之巅'),
]
# 蛇形 3 行坐标（4 + 4 + 2）
ROWS = [
    (280, [(180,), (480,), (780,), (1080,)], False),   # 左→右
    (560, [(1080,), (780,), (480,), (180,)], True),    # 右→左
    (790, [(180,), (480,)], False),                    # 左→右
]


def layout():
    pts = []
    for row_i, (y, cols, _) in enumerate(ROWS):
        for col_i, (x,) in enumerate(cols):
            pts.append((x, y))
    return pts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('station')
    ap.add_argument('out')
    ap.add_argument('--series', default='btc')
    a = ap.parse_args()
    col = SERIES[a.series]['color']
    accent = SERIES[a.series]['accent']
    scol = SERIES[a.series]['color']

    idx = next(i for i, s in enumerate(STATIONS) if s[0] == a.station)
    pts = layout()

    im = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(im, 'RGBA')

    # ---- 页眉：mini 宝盒 + 标题 + 系列 chip ----
    draw_baohe_box(im, 56, 66, 15, series=a.series, mini=True)
    d = ImageDraw.Draw(im, 'RGBA')
    d.text((96, 58), '比特币学习地图 · 寻宝路线', font=FONT(30), fill=INK, anchor='lm')
    d.text((96, 88), '从现金湾到代码之巅，十站走完比特币的核心逻辑', font=FONT(15), fill=MUTED, anchor='lm')
    series_chip(d, W - 40, 50, a.series, fs=15)

    # ---- 路径：先画线（已走实线 / 未走虚线） ----
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        walked_to = i < idx          # 这段是否已走完
        width = 5 if walked_to else 3
        if walked_to:
            # 实线（短折线转圆角：直接画线段+端点圆）
            d.line([x1, y1, x2, y2], fill=col + (230,), width=width)
            d.ellipse([x2 - width / 2, y2 - width / 2, x2 + width / 2, y2 + width / 2], fill=col + (230,))
        else:
            # 虚线
            import math
            L = math.hypot(x2 - x1, y2 - y1)
            n = int(L / 22)
            for k in range(n):
                t0, t1 = k / n, min((k + 0.55) / n, 1)
                d.line([x1 + (x2 - x1) * t0, y1 + (y2 - y1) * t0,
                        x1 + (x2 - x1) * t1, y1 + (y2 - y1) * t1],
                       fill=LINE_OFF, width=width)

    # ---- 节点 ----
    def name_plate(x, y, text, f, fill):
        """站名：先垫纸底（防止竖线穿字），再写字"""
        tw = d.textlength(text, font=f)
        d.rectangle([x - tw / 2 - 4, y - 14, x + tw / 2 + 4, y + 14], fill=PAPER)
        d.text((x, y), text, font=f, fill=fill, anchor='mm')

    for i, ((x, y), (num, name)) in enumerate(zip(pts, STATIONS)):
        if i == idx:
            # 当前站：光环 + 大圆
            d.ellipse([x - 74, y - 74, x + 74, y + 74], outline=col + (90,), width=2)
            d.ellipse([x - 58, y - 58, x + 58, y + 58], fill=col)
            nf = FONT(34 if len(num) <= 2 else 27)
            d.text((x, y - 2), num, font=nf, fill=(255, 248, 231), anchor='mm')
            # 站名牌（节点上方）
            tag = f'站 {num} · {name}'
            tf = FONT(26)
            tw = d.textlength(tag, font=tf)
            ty = y - 96
            d.rounded_rectangle([x - tw / 2 - 22, ty - 24, x + tw / 2 + 22, ty + 24],
                                radius=24, fill=col)
            d.polygon([(x - 12, ty + 23), (x + 12, ty + 23), (x, ty + 36)], fill=col)
            d.text((x, ty - 1), tag, font=tf, fill=(30, 24, 16), anchor='mm')
        elif i < idx:
            # 已走：实心
            d.ellipse([x - 42, y - 42, x + 42, y + 42], fill=col + (200,))
            d.text((x, y - 2), num, font=FONT(26), fill=(255, 248, 231), anchor='mm')
            name_plate(x, y + 62, name, FONT(19), (96, 82, 62))
        else:
            # 未来：空心
            d.ellipse([x - 42, y - 42, x + 42, y + 42], outline=LINE_OFF, width=4, fill=(246, 240, 228))
            d.text((x, y - 2), num, font=FONT(26), fill=(170, 158, 138), anchor='mm')
            name_plate(x, y + 62, name, FONT(19), (170, 158, 138))

    # ---- 终点旗（站 9 圆外上方，不遮数字） ----
    ex, ey = pts[-1]
    d.polygon([(ex + 14, ey - 66), (ex + 42, ey - 57), (ex + 14, ey - 48)], fill=LINE_OFF)
    d.line([ex + 14, ey - 66, ex + 14, ey - 34], fill=LINE_OFF, width=3)

    # ---- 页脚：当前站一句话 + 品牌行 ----
    d.line([60, 852, W - 60, 852], fill=(226, 214, 190), width=1)
    d.text((60, 876), '慢读宝盒 · 宝盒比特币 · 学习连载', font=FONT(14), fill=MUTED, anchor='lm')
    d.text((W - 60, 876), '科普内容，不构成投资建议', font=FONT(14), fill=MUTED, anchor='rm')

    im.save(a.out)
    print('saved', a.out)


if __name__ == '__main__':
    main()
