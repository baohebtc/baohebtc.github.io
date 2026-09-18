#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
封面模板 v8 —— 慢读宝盒·头像品牌延伸版（ADR-0005）

视觉 = 用户已选定头像（IMG_7170）的同款宝箱（抠图资产）+ 官方 ₿ 标准件，
构图复刻「宝盒比特币头像」的箱+币语言；文字排版程序化。
底色/金调全部取自头像实测色。900×383，核心元素居中落在 383 安全区。

用法:
    python3 cover_template_v8.py --station 4 --out out.png
    python3 cover_template_v8.py --batch --out-dir /tmp/cv8-batch
"""
import argparse
import json
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'dev'))

W, H = 900, 383
CX = W // 2
SAFE_L, SAFE_R = 258, 642          # 微信列表 383×383 安全区

# ---- 头像实测色板（ADR-0005） ----
BG_EDGE = (23, 16, 8)      # #171008
BG_CENTER = (42, 31, 18)   # #2A1F12
GOLD = (201, 160, 80)      # #C9A050 次级标题/金线
GOLD_DIM = (107, 85, 38)   # 暗金 线框/进度点
CREAM = (245, 237, 216)    # #F5EDD8 主标题/米白
MUTED = (168, 152, 122)    # 弱化文字
ORANGE = (247, 147, 26)    # ₿ / 当前进度点

MEDALLION = os.path.join(ROOT, 'assets', 'brand', 'baohe-medallion.png')
BTC_EMBLEM = os.path.join(ROOT, 'assets', 'brand', 'btc-emblem-official.png')
STATIONS_JSON = os.path.join(ROOT, 'tools', 'dev', 'map-stations.json')


def FONT(size, weight='bold'):
    """PingFang SC 粗体/常规"""
    idx = 1 if weight == 'bold' else 0
    return ImageFont.truetype('/System/Library/Fonts/PingFang.ttc', size, index=idx)


def load_stations():
    with open(STATIONS_JSON, encoding='utf-8') as f:
        data = json.load(f)
    return [(str(s['num']), s['name'], s.get('en', '')) for s in data['stations']]


STATIONS = load_stations()


def bg_layer():
    """径向渐变底 + 极轻颗粒暗角"""
    small = Image.new('RGB', (90, 39))
    px = small.load()
    for y in range(39):
        for x in range(90):
            t = ((x - 45) / 45) ** 2 * 0.65 + ((y - 26) / 30) ** 2 * 0.35
            t = min(t, 1.0)
            px[x, y] = tuple(int(BG_CENTER[i] + (BG_EDGE[i] - BG_CENTER[i]) * t) for i in range(3))
    return small.resize((W, H), Image.BICUBIC)


def draw_series_chip(d, right_x, cy, fs=12):
    """右上系列 chip：官方₿ + 宝盒比特币 · 学习连载"""
    coin = Image.open(BTC_EMBLEM).convert('RGBA').resize((fs * 2, fs * 2), Image.LANCZOS)
    text = '宝盒比特币 · 学习连载'
    f = FONT(fs, 'regular')
    tw = d.textlength(text, font=f)
    pad_l, pad_r, pad_y = fs + 14, 16, 8
    x0 = right_x - (pad_l + fs * 2 + 6 + tw + pad_r)
    y0 = cy - fs - pad_y
    y1 = cy + fs + pad_y
    d.rounded_rectangle([x0, y0, right_x, y1], radius=(y1 - y0) // 2,
                        outline=GOLD_DIM, width=1)
    coin_y = cy - fs
    base = d._image if hasattr(d, '_image') else None
    # 直接贴币（d 是 RGBA draw，paste 走 image 对象）
    return coin, (int(x0 + pad_l), int(coin_y)), (int(x0 + pad_l + fs * 2 + 6), cy), text, f


def render(station, theme='dark'):
    idx = next(i for i, s in enumerate(STATIONS) if s[0] == str(station))
    num, zh, en = STATIONS[idx]

    base = bg_layer().convert('RGBA')
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    # ---- 中央：头像徽章（medallion，品牌母体） + 官方 ₿ 系列徽记压角 ----
    med_s = 196
    med = Image.open(MEDALLION).convert('RGBA').resize((med_s, med_s), Image.LANCZOS)
    med_cy = 108
    med_x, med_y = CX - med_s // 2, med_cy - med_s // 2
    # 徽章后一圈柔光（金棕，从头像光晕延伸）
    halo = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    hd.ellipse([med_x - 26, med_y - 20, med_x + med_s + 26, med_y + med_s + 24],
               fill=(210, 170, 95, 52))
    halo = halo.filter(ImageFilter.GaussianBlur(30))
    overlay.alpha_composite(halo)
    overlay.alpha_composite(med, (med_x, med_y))
    # ₿ 徽记：徽章右下压角（宝盒比特币 = 头像 + ₿）
    coin_r = 24
    coin = Image.open(BTC_EMBLEM).convert('RGBA').resize((coin_r * 2, coin_r * 2), Image.LANCZOS)
    badge_cx, badge_cy = med_x + med_s - 16, med_y + med_s - 14
    ring_bg = ImageDraw.Draw(overlay)
    ring_bg.ellipse([badge_cx - coin_r - 4, badge_cy - coin_r - 4,
                     badge_cx + coin_r + 4, badge_cy + coin_r + 4], fill=BG_EDGE + (255,))
    overlay.alpha_composite(coin, (badge_cx - coin_r, badge_cy - coin_r))
    d = ImageDraw.Draw(overlay)

    # ---- 左上品牌行：mini 徽章 + 慢读宝盒 ----
    mini_s = 52
    mini = Image.open(MEDALLION).convert('RGBA').resize((mini_s, mini_s), Image.LANCZOS)
    overlay.alpha_composite(mini, (24, 14))
    d = ImageDraw.Draw(overlay)
    d.text((86, 30), '慢读宝盒', font=FONT(18), fill=CREAM, anchor='lm')
    d.text((86, 52), '把难的知识，装进宝盒', font=FONT(10, 'regular'), fill=MUTED, anchor='lm')

    # ---- 右上系列 chip ----
    coin_s, coin_pos, text_xy, chip_text, chip_f = draw_series_chip(d, W - 26, 33)
    overlay.alpha_composite(coin_s, coin_pos)
    d = ImageDraw.Draw(overlay)
    d.text(text_xy, chip_text, font=chip_f, fill=MUTED, anchor='lm')

    # ---- 次级标题：一张比特币学习地图 · 第 N 站 ----
    sub = f'一张比特币学习地图 · 第 {num} 站'
    sf = FONT(17, 'regular')
    # 手动加字距
    tracking = 2
    widths = [d.textlength(ch, font=sf) for ch in sub]
    total = sum(widths) + tracking * (len(sub) - 1)
    x = CX - total / 2
    for ch, cw in zip(sub, widths):
        d.text((x, 236), ch, font=sf, fill=GOLD, anchor='lm')
        x += cw + tracking

    # ---- 主标题：站名（宋体 Black 大字 + 轻投影） ----
    zs = 60 if len(zh) <= 5 else 54
    zf = ImageFont.truetype('/System/Library/Fonts/Supplemental/Songti.ttc', zs, index=0)
    # 投影
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.text((CX, 285 + 3), zh, font=zf, fill=(0, 0, 0, 160), anchor='mm')
    sh = sh.filter(ImageFilter.GaussianBlur(5))
    overlay.alpha_composite(sh)
    d = ImageDraw.Draw(overlay)
    d.text((CX, 285), zh, font=zf, fill=CREAM, anchor='mm')

    # ---- 底部进度点（9+1） ----
    n = len(STATIONS)
    gap = 26
    x0 = CX - gap * (n - 1) / 2
    py = 340
    for i in range(n):
        x = x0 + i * gap
        if i == idx:
            d.ellipse([x - 6, py - 6, x + 6, py + 6], fill=ORANGE)
            d.ellipse([x - 10, py - 10, x + 10, py + 10], outline=ORANGE + (120,), width=1)
        elif i < idx:
            d.ellipse([x - 3, py - 3, x + 3, py + 3], fill=GOLD + (200,))
        else:
            d.ellipse([x - 3, py - 3, x + 3, py + 3], fill=(90, 74, 46))

    out = Image.alpha_composite(base, overlay).convert('RGB')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--station', default='4')
    ap.add_argument('--out', default='')
    ap.add_argument('--batch', action='store_true')
    ap.add_argument('--out-dir', default='/tmp/cv8-batch')
    args = ap.parse_args()

    if args.batch:
        for theme_dir in ():
            pass
        for num, _, _ in STATIONS:
            out = os.path.join(args.out_dir, f'封面-站{num}-v8-900x383.png')
            os.makedirs(os.path.dirname(out), exist_ok=True)
            render(num).save(out)
            print('✅', out)
        return

    render(args.station).save(args.out)
    print('✅', args.out)


if __name__ == '__main__':
    main()
