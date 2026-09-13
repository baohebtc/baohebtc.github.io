#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_map_callout.py — 从 v3.3 母图生成「本站高亮」回扣图（公众号正文用）

为什么不烧可灵：v3.3 带标签成品图已在手（单一真相源 map-stations.json），
裁切 + PIL 画高亮圈 + 底部合规条，零积分、与网站完全同源。

用法: python3 make_map_callout.py <站号> [输出路径]
"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path('/Users/mac/Desktop/宝盒知识库/比特币学习地图')
SRC = ROOT / 'assets/learning-map/v3.3-地图-10站立体-带标签-1760x2368-q256.png'
JSON = ROOT / 'tools/dev/map-stations.json'
ORANGE = (247, 147, 26)
FONT = '/System/Library/Fonts/PingFang.ttc'

def main():
    num = sys.argv[1] if len(sys.argv) > 1 else '4'
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    if out is None:
        out = ROOT / f'assets/articles/公众号/站{num}-{"账本海" if num=="4" else "站"+num}/map-figure-v3.3.png'

    data = json.loads(JSON.read_text(encoding='utf-8'))
    sts = data['stations'] if isinstance(data, dict) else data
    me = next(s for s in sts if str(s['num']) == num)
    cx, cy = me['cx'], me['cy']
    name = me.get('name', f'站{num}')

    im = Image.open(SRC).convert('RGB')
    W, H = im.size  # 1760x2368

    # 16:9 窗口：x 全宽，y 以本站为中心
    win_h = int(W * 9 / 16)          # 990
    y0 = max(0, min(H - win_h, cy - win_h // 2))
    crop = im.crop((0, y0, W, y0 + win_h)).resize((1280, 720), Image.LANCZOS)
    d = ImageDraw.Draw(crop, 'RGBA')
    sc = 1280 / W

    # 本站高亮：双环（白细环 + 橙粗环）+ 脉冲点
    px, py = cx * sc, (cy - y0) * sc
    r1, r2 = 66, 80
    d.ellipse([px-r2, py-r2, px+r2, py+r2], outline=(255,255,255,200), width=3)
    d.ellipse([px-r1, py-r1, px+r1, py+r1], outline=ORANGE+(255,), width=8)

    # 「我们在这里」标签：站标上方
    f = ImageFont.truetype(FONT, 30)
    fb = ImageFont.truetype(FONT, 24)
    tag = f'📍 本站｜站{num} {name}'
    tb = d.textbbox((0,0), tag, font=f)
    tw, th = tb[2]-tb[0], tb[3]-tb[1]
    tx, ty = px - tw/2, py - r2 - 18 - th
    if ty < 8: ty = py + r2 + 18
    d.rounded_rectangle([tx-14, ty-10, tx+tw+14, ty+th+12], radius=10,
                        fill=(13,13,13,215), outline=ORANGE+(255,), width=3)
    d.text((tx-tb[0], ty-tb[1]), tag, font=f, fill=(255,255,255,255))

    # 底部合规条（与旧 map-figure 同款：黑条 + 两行小字）
    bar_h = 92
    d.rectangle([0, 720-bar_h, 1280, 720], fill=(10,8,6,235))
    d.line([(0, 720-bar_h), (1280, 720-bar_h)], fill=ORANGE+(255,), width=3)
    l1 = '⚠️ 风险提示：比特币价格波动剧烈，本文仅作区块链科普，不构成任何投资建议。'
    l2 = '投资需谨慎，盈亏自负｜慢读宝盒 · 一张比特币学习地图'
    d.text((640, 720-bar_h+16), l1, font=fb, fill=(232,225,210), anchor='ma')
    d.text((640, 720-bar_h+50), l2, font=fb, fill=(180,170,150), anchor='ma')

    out.parent.mkdir(parents=True, exist_ok=True)
    crop.save(out, optimize=True)
    print(f'✅ {out}  {crop.size}  {out.stat().st_size/1024:.0f}KB')
    print(f'   窗口 y∈[{y0},{y0+win_h}]  本站({num}) 画布位 ({px:.0f},{py:.0f})')

if __name__ == '__main__':
    main()
