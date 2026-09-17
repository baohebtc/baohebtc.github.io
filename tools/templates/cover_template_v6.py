#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cover_template_v6.py — 慢读宝盒 9+1 站封面（程序化品牌橙金深色卡）

设计要点（ADR-0003）：
- 900×383，核心锁定在中央 383×383 安全区（微信列表只显示中心方块）
- 深炭暖底 #141210 + v3.3 无标签母图「本站区域」低亮度纹理（母图升级只影响氛围层，版式不锁版本）
- 程序化官方 ₿ 徽标（brand-kit.draw_bitcoin_b，与国际同步）
- 居中纵向锁定：橙圆站号徽章 + 大字站名 + 英文 + 一句话副标
- 底部 9+1 站进度点（当前站橙色发光）——系列进度一眼可读
- 零积分、全参数化

用法:
  cover_template_v6.py --station 4 --out out/cover-v6/站4.png
  cover_template_v6.py --batch --out-dir out/cover-v6/
"""
import argparse
import json
import os
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path('/Users/mac/Desktop/宝盒知识库/比特币学习地图')
TEX_MAP = ROOT / 'assets/learning-map/v3.3-地图-10站立体-1760x2368.png'  # 无标签，纯地形
STATIONS_JSON = ROOT / 'tools/dev/map-stations.json'
BRAND_KIT = ROOT / 'tools/dev/brand-kit.py'

W, H = 900, 383
SAFE = 383  # 中央安全区
CX = W // 2

# ==== design tokens ====
BG = (20, 18, 16)          # #141210 深炭暖底
ORANGE = (247, 147, 26)    # #F7931A
GOLD = (184, 134, 11)      # #B8860B
WARM_WHITE = (255, 248, 231)
MUTED = (201, 188, 164)
DIM = (122, 111, 92)

import importlib.util
_spec = importlib.util.spec_from_file_location('brandkit', BRAND_KIT)
brandkit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(brandkit)

STATION_TEXT = {
    '1':   ('现金湾',     'BITCOIN BAY',         '货币的第一声'),
    '1.5': ('钱到底是什么', 'WHAT IS MONEY',      '货币哲学插篇'),
    '2':   ('银行堡',     'BANK FORT',           '货币的三大缺陷'),
    '3':   ('双花峡',     'DOUBLE-SPEND GORGE',  '一笔钱能花两次吗'),
    '4':   ('账本海',     'LEDGER SEA',          '谁来记这本账'),
    '5':   ('哈希岭',     'HASH RIDGE',          '一道数学封印'),
    '6':   ('共识峰',     'CONSENSUS PEAK',      '陌生人如何达成一致'),
    '7':   ('矿工谷',     'MINER VALLEY',        '谁来添加新的一页'),
    '8':   ('私钥崖',     'KEY CLIFF',           '你就是自己的银行'),
    '9':   ('代码之巅',   'CODE SUMMIT',         '比特币的全部秘密'),
}
ORDER = ['1', '1.5', '2', '3', '4', '5', '6', '7', '8', '9']

FONT_CN = '/System/Library/Fonts/PingFang.ttc'


def font(size, bold=True):
    try:
        return ImageFont.truetype(FONT_CN, size, index=1 if bold else 0)
    except Exception:
        return ImageFont.truetype(FONT_CN, size)


EMBLEM = ROOT / 'assets/brand/btc-emblem-official.png'
_EMBLEM_CACHE = {}


def emblem(size=34):
    """官方 ₿ 徽标（512px 源图缩小，天然锐利），带缓存"""
    if size not in _EMBLEM_CACHE:
        im = Image.open(EMBLEM).convert('RGBA')
        im = im.resize((size, size), Image.LANCZOS)
        _EMBLEM_CACHE[size] = im
    return _EMBLEM_CACHE[size]


def center_glow():
    """中央柔光暗底：提升标题对比"""
    m = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(m)
    d.ellipse([CX - 250, 60, CX + 250, 330], fill=110)
    return m.filter(ImageFilter.GaussianBlur(60))


def spaced(draw, cx, y, text, f, fill, tracking=5, max_width=320):
    """居中画带字距文本；超宽自动收字距→缩字号"""
    size = f.size
    for tr in range(tracking, 0, -1):
        widths = [draw.textlength(ch, font=f) for ch in text]
        total = sum(widths) + tr * (len(text) - 1)
        if total <= max_width:
            break
    else:
        while size > 10:
            size -= 1
            f = font(size)
            widths = [draw.textlength(ch, font=f) for ch in text]
            total = sum(widths) + max(1, tr) * (len(text) - 1)
            if total <= max_width:
                break
        tr = max(1, tr)
    x = cx - total / 2
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=f, fill=fill, anchor='lm')
        x += w + tr


def texture_layer(station):
    """v3.3 母图本站区域 → 灰度对比增强 → 低亮度屏幕混合层"""
    data = json.loads(STATIONS_JSON.read_text(encoding='utf-8'))
    st = next(s for s in data['stations'] if s['num'] == station)
    cx, cy = st['cx'], st['cy']
    im = Image.open(TEX_MAP).convert('L')
    # 裁 900:383 比例窗口，宽取母图 78%
    ww = int(im.width * 0.78)
    wh = int(ww * H / W)
    x0 = max(0, min(im.width - ww, cx - ww // 2))
    y0 = max(0, min(im.height - wh, cy - wh // 2))
    tex = im.crop((x0, y0, x0 + ww, y0 + wh)).resize((W, H), Image.LANCZOS)
    tex = ImageEnhance.Contrast(tex).enhance(1.25)
    tex = tex.point(lambda v: int(v * 0.16))  # 峰值亮度 16%
    return tex.convert('RGB')


def vignette():
    """边缘压暗蒙版"""
    m = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(m)
    d.ellipse([-W * 0.25, -H * 0.9, W * 1.25, H * 1.9], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(90))
    dark = Image.new('RGB', (W, H), (0, 0, 0))
    return m, dark


def make_cover(station, out_path):
    zh, en, tag = STATION_TEXT[station]
    idx = ORDER.index(station)

    # 1. 底色 + 纹理（屏幕混合）+ 暗角 + 中央柔光暗底
    base = Image.new('RGB', (W, H), BG)
    base = ImageChops.screen(base, texture_layer(station))
    vmask, vdark = vignette()
    base = Image.composite(base, ImageChops.multiply(base, vdark), vmask)
    base = Image.composite(base, ImageEnhance.Brightness(base).enhance(0.72), center_glow())
    d = ImageDraw.Draw(base)

    # 2. 内框（沉金细线，留白 14px）
    d.rectangle([14, 14, W - 15, H - 15], outline=GOLD, width=1)

    # 3. 顶部品牌行：₿ + 慢读宝盒·比特币学习地图
    base.paste(emblem(42), (26, 16), emblem(42))
    d.text((82, 27), '慢读宝盒', font=font(17), fill=WARM_WHITE, anchor='lm')
    d.text((82, 49), '比特币学习地图', font=font(11), fill=DIM, anchor='lm')

    # 4. 顶部右侧：连载进度 chip（1.5 计入篇序）
    seq = idx + 1
    chip = f'连载 {seq} / 10'
    cw = d.textlength(chip, font=font(12))
    d.rounded_rectangle([W - 28 - cw - 20, 22, W - 28, 48], radius=13,
                        outline=(107, 96, 76), width=1)
    d.text((W - 28 - cw / 2 - 10, 35), chip, font=font(12), fill=MUTED, anchor='mm')

    # 5. 中央锁定（垂直布局，全部落在 383 安全区内）
    # 5a. 站号徽章：橙圆 + 白字
    bcx, bcy, br = CX, 112, 42
    d.ellipse([bcx - br - 8, bcy - br - 8, bcx + br + 8, bcy + br + 8],
              outline=ORANGE, width=2)
    d.ellipse([bcx - br, bcy - br, bcx + br, bcy + br], fill=ORANGE)
    nf = font(40 if len(station) <= 2 else 30)
    d.text((bcx, bcy - 2), station, font=nf, fill=WARM_WHITE, anchor='mm')

    # 5b. 站名（自动缩字号：最长 6 字也在安全区内）
    zs = {1: 58, 2: 58, 3: 56, 4: 54, 5: 50, 6: 46}.get(len(zh), 44)
    zf = font(zs)
    d.text((CX, 184), zh, font=zf, fill=WARM_WHITE, anchor='mm')

    # 5c. 英文（字距拉开，橙金）
    spaced(d, CX, 240, en, font(15), (230, 168, 66), tracking=5)

    # 5d. 一句话副标
    d.text((CX, 276), tag, font=font(19), fill=MUTED, anchor='mm')

    # 5e. 分隔短线
    d.line([CX - 26, 314, CX + 26, 314], fill=(107, 96, 76), width=1)

    # 6. 底部 9+1 站进度点
    n = len(ORDER)
    gap = 22
    x0 = CX - gap * (n - 1) / 2
    for i, sid in enumerate(ORDER):
        x = x0 + i * gap
        if sid == station:
            d.ellipse([x - 6, 340 - 6, x + 6, 340 + 6], fill=ORANGE)
            d.ellipse([x - 10, 340 - 10, x + 10, 340 + 10],
                      outline=(247, 147, 26, 110), width=2)
        else:
            r = 3
            d.ellipse([x - r, 340 - r, x + r, 340 + r], fill=(96, 86, 68))

    # 7. 底部系列名（安全区外，右下）
    d.text((W - 28, H - 26), 'SLOW READ · BITCOIN MAP', font=font(10),
           fill=(96, 86, 68), anchor='rs')

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    base.save(out_path, optimize=True)
    print(f'✅ {out_path}  {base.size}  {out_path.stat().st_size/1024:.0f}KB')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--station')
    ap.add_argument('--out')
    ap.add_argument('--batch', action='store_true')
    ap.add_argument('--out-dir', default='out/cover-v6')
    a = ap.parse_args()
    if a.batch:
        for sid in ORDER:
            make_cover(sid, Path(a.out_dir) / f'封面-站{sid}-v6-900x383.png')
    else:
        make_cover(a.station, a.out)


if __name__ == '__main__':
    main()
