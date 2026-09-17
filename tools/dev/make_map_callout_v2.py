#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_map_callout_v2.py — 「本站在哪」回扣图 v2（ADR-0003）

v1 的问题：大同心圆+黑横幅+厚重黑合规条，粗陋。
v2 设计语言（品牌橙金深色卡家族）：
- 源图 = v3.3 带标签母图（单点真相源 map-stations.json），与网站完全同源
- 4:5 竖窗 1080×1350（手机正文阅读比例）
- 全图暗化 + 本站径向聚光 → "我们在哪"一眼可见，无需大圆圈
- 品牌橙细环 + 上方小徽章牌（站号+站名），克制不抢戏
- 底部单行细合规条（金线压顶），不再占 1/8 画面

用法: make_map_callout_v2.py <站号> <输出路径>
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path('/Users/mac/Desktop/宝盒知识库/比特币学习地图')
SRC = ROOT / 'assets/learning-map/v3.3-地图-10站立体-带标签-1760x2368-q256.png'
JSON = ROOT / 'tools/dev/map-stations.json'
ORANGE = (247, 147, 26)
WARM_WHITE = (255, 248, 231)
GOLD = (184, 134, 11)
FONT = '/System/Library/Fonts/PingFang.ttc'

OUT_W, OUT_H = 1080, 1350          # 4:5
WIN_W = 1760                        # 全图宽——回扣图展示完整地图（系列的锚）
WIN_H = 2200                        # 覆盖母图 93% 高度


def f(size, bold=True):
    return ImageFont.truetype(FONT, size, index=1 if bold else 0)


def main():
    num = sys.argv[1]
    out = Path(sys.argv[2])
    data = json.loads(JSON.read_text(encoding='utf-8'))
    me = next(s for s in data['stations'] if s['num'] == num)
    cx, cy, name = me['cx'], me['cy'], me['name']

    im = Image.open(SRC).convert('RGB')
    W, H = im.size
    x0 = max(0, min(W - WIN_W, cx - WIN_W // 2))
    y0 = max(0, min(H - WIN_H, cy - WIN_H // 2))
    crop = im.crop((x0, y0, x0 + WIN_W, y0 + WIN_H)).resize((OUT_W, OUT_H), Image.LANCZOS)

    sc = OUT_W / WIN_W
    px, py = (cx - x0) * sc, (cy - y0) * sc

    # 1. 暗化 + 本站径向聚光
    dark = ImageEnhance_Brightness(crop, 0.36)
    mask = Image.new('L', (OUT_W, OUT_H), 0)
    md = ImageDraw.Draw(mask)
    for r, a in [(150, 255), (260, 210), (400, 120), (560, 40)]:
        md.ellipse([px - r, py - r, px + r, py + r], fill=a)
    mask = mask.filter(ImageFilter.GaussianBlur(80))
    base = Image.composite(crop, dark, mask)
    d = ImageDraw.Draw(base)

    # 2. 本站标记：白细环 + 橙主环（母图自带数字站标保留外露）
    d.ellipse([px - 74, py - 74, px + 74, py + 74], outline=(255, 255, 255), width=3)
    d.ellipse([px - 60, py - 60, px + 60, py + 60], outline=ORANGE, width=7)

    # 3. 徽章牌：精准覆盖母图自带标签框（json 的 x/y/w/h 即标签框），fallback 环上方
    tag = f'站{num} · {name}'
    tf = f(34)
    tw = d.textlength(tag, font=tf)
    pill_w, pill_h = tw + 56, 62
    if 'x' in me:
        tx = (me['x'] + me['w'] / 2 - x0) * sc
        ty = (me['y'] + me['h'] / 2 - y0) * sc
    else:
        tx, ty = px, py - 60 - 40 - pill_h / 2
    tx = min(max(tx, pill_w / 2 + 24), OUT_W - pill_w / 2 - 24)
    ty = max(ty, pill_h / 2 + 66)  # 不压顶部装饰
    # 连接线（先画，牌压其上）
    d.line([tx, ty, px, py], fill=ORANGE, width=4)
    d.rounded_rectangle([tx - pill_w / 2, ty - pill_h / 2, tx + pill_w / 2, ty + pill_h / 2],
                        radius=31, fill=ORANGE)
    d.text((tx, ty - 2), tag, font=tf, fill=(20, 18, 16), anchor='mm')

    # 4. 底部单行细合规条
    bar_h = 58
    d.rectangle([0, OUT_H - bar_h, OUT_W, OUT_H], fill=(16, 14, 12))
    d.line([(0, OUT_H - bar_h), (OUT_W, OUT_H - bar_h)], fill=GOLD, width=2)
    msg = '⚠️ 风险提示：本文仅作区块链科普，不构成投资建议｜慢读宝盒 · 比特币学习地图'
    d.text((OUT_W / 2, OUT_H - bar_h / 2 - 1), msg, font=f(24, bold=False),
           fill=(201, 188, 164), anchor='mm')

    out.parent.mkdir(parents=True, exist_ok=True)
    base.save(out, optimize=True)
    print(f'✅ {out}  {base.size}  {out.stat().st_size/1024:.0f}KB  窗口y[{y0},{y0+WIN_H}] 站位({px:.0f},{py:.0f})')


def ImageEnhance_Brightness(im, factor):
    from PIL import ImageEnhance
    return ImageEnhance.Brightness(im).enhance(factor)


if __name__ == '__main__':
    main()
