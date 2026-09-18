# -*- coding: utf-8 -*-
"""
cover_template_v7.py · 宝盒母品牌封面（ADR-0004）
================================================
900×383；383×383 安全区居中（x∈[258.5,641.5]）。
零地图元素。视觉主体 = 程序化宝盒（baohe_kit.draw_baohe_box）。
系列可配置：--series btc（宝盒比特币）/ eth（宝盒以太坊，预留）。
方向：--theme dark（暖黑）/ light（米白纸）。

用法：
  python3 cover_template_v7.py --station 4 --out out.png [--theme dark] [--series btc]
  python3 cover_template_v7.py --batch --out-dir DIR
"""
import argparse
import os
import sys

sys.path.insert(0, '/Users/mac/Desktop/宝盒知识库/比特币学习地图/tools/dev')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dev'))
from baohe_kit import (SERIES, BG_DARK, PAPER, WARM_WHITE, MUTED, DIM, FONT,
                       draw_baohe_box, series_chip)
from PIL import Image, ImageDraw, ImageFilter

W, H = 900, 383
CX = W // 2
SAFE_L, SAFE_R = 259, 642          # 383×383 列表安全区

STATIONS = [
    ('1',   '现金湾', 'CASH BAY'),
    ('1.5', '钱到底是什么', 'WHAT IS MONEY'),
    ('2',   '银行堡', 'BANK FORT'),
    ('3',   '双花峡', 'DOUBLE-SPEND GORGE'),
    ('4',   '账本海', 'LEDGER SEA'),
    ('5',   '哈希岭', 'HASH RIDGE'),
    ('6',   '共识峰', 'CONSENSUS PEAK'),
    ('7',   '矿工谷', 'MINER VALLEY'),
    ('8',   '私钥崖', 'KEY CLIFF'),
    ('9',   '代码之巅', 'CODE SUMMIT'),
]

# 深浅两方向色板
THEMES = {
    'dark': {
        'bg': BG_DARK, 'halo': (60, 44, 26),
        'title': WARM_WHITE, 'sub': (196, 182, 160), 'muted': MUTED,
        'line': (86, 74, 58), 'dot_off': (74, 64, 52),
    },
    'light': {
        'bg': PAPER, 'halo': (255, 236, 205),
        'title': (42, 34, 24), 'sub': (96, 82, 62), 'muted': (140, 126, 104),
        'line': (214, 198, 168), 'dot_off': (216, 204, 182),
    },
}


def render(station: str, theme='dark', series='btc') -> Image.Image:
    col = SERIES[series]['color']
    t = THEMES[theme]
    idx = next(i for i, s in enumerate(STATIONS) if s[0] == station)
    num, zh, en = STATIONS[idx]

    base = Image.new('RGB', (W, H), t['bg'])
    d = ImageDraw.Draw(base, 'RGBA')

    # 1. 中央柔光（宝盒后方，系列色 8%；浅色版减淡防脏）
    glow = Image.new('L', (W, H), 0)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([CX - 260, 30, CX + 260, 330], fill=42 if theme == 'dark' else 24)
    glow = glow.filter(ImageFilter.GaussianBlur(70))
    halo = Image.new('RGB', (W, H), t['halo'])
    base = Image.composite(halo, base, glow)
    d = ImageDraw.Draw(base, 'RGBA')

    # 2. 内框
    d.rectangle([12, 12, W - 13, H - 13], outline=t['line'], width=1)

    # 3. 左上品牌行：小宝盒 + 慢读宝盒
    draw_baohe_box(base, 40, 42, 12, series=series, mini=True)
    d = ImageDraw.Draw(base, 'RGBA')
    d.text((70, 28), '慢读宝盒', font=FONT(17), fill=t['title'], anchor='lm')
    d.text((70, 49), '把难的知识，装进宝盒', font=FONT(10), fill=t['muted'], anchor='lm')

    # 4. 右上系列 chip
    series_chip(d, W - 26, 26, series, fs=13)

    # 5. 中央宝盒（视觉主体；盒底 y=160+15+40.5≈216，不与 pill 重叠）
    draw_baohe_box(base, CX, 156, 34, series=series, glow=True)
    d = ImageDraw.Draw(base, 'RGBA')

    # 6. 站号 pill
    pill = f'站 {num}'
    pf = FONT(15)
    pw = d.textlength(pill, font=pf)
    px, py = CX, 246
    d.rounded_rectangle([CX - pw / 2 - 16, py - 14, CX + pw / 2 + 16, py + 14],
                        radius=14, outline=col + (160,), width=1)
    d.text((CX, py - 1), pill, font=pf, fill=col, anchor='mm')

    # 7. 站名大字
    zs = {5: 46, 6: 42, 7: 38}.get(len(zh), 50)
    d.text((CX, 286), zh, font=FONT(zs, serif=True), fill=t['title'], anchor='mm')

    # 8. 英文（自适应缩放不超安全区）
    ef = FONT(14)
    while d.textlength(en, font=ef) > (SAFE_R - SAFE_L - 40) and ef.size > 9:
        ef = FONT(ef.size - 1)
    d.text((CX, 318), en, font=ef, fill=col if theme == 'dark' else (150, 96, 20), anchor='mm')

    # 9. 底部进度点（9+1）
    n = len(STATIONS)
    gap = 26
    x0 = CX - gap * (n - 1) / 2
    for i in range(n):
        x = x0 + i * gap
        if i == idx:
            d.ellipse([x - 7, 350 - 7, x + 7, 350 + 7], fill=col)
            d.ellipse([x - 11, 350 - 11, x + 11, 350 + 11], outline=col + (110,), width=1)
        else:
            r = 3.2
            d.ellipse([x - r, 350 - r, x + r, 350 + r], fill=t['dot_off'])

    return base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--station', default='4')
    ap.add_argument('--out', default='/tmp/cover-v7.png')
    ap.add_argument('--theme', default='dark', choices=['dark', 'light'])
    ap.add_argument('--series', default='btc', choices=list(SERIES.keys()))
    ap.add_argument('--batch', action='store_true')
    ap.add_argument('--out-dir', default='/tmp/cover-v7-batch')
    a = ap.parse_args()

    if a.batch:
        os.makedirs(a.out_dir, exist_ok=True)
        for theme in ('dark', 'light'):
            td = os.path.join(a.out_dir, theme)
            os.makedirs(td, exist_ok=True)
            for s in STATIONS:
                im = render(s[0], theme=theme, series=a.series)
                p = os.path.join(td, f'封面-站{s[0]}-{s[1]}-v7-{theme}-900x383.png')
                im.save(p)
                print('saved', p)
    else:
        render(a.station, theme=a.theme, series=a.series).save(a.out)
        print('saved', a.out)


if __name__ == '__main__':
    main()
