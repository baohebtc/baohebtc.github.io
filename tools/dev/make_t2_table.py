#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_t2_table.py — T2「账户模型 vs UTXO 模型」对比表图（站4 微信版用）

微信后台不认 Markdown 表格 → 必须转图。风格对齐站4 既有深色信息图：
深黑底 / 卡片分区 / 橙金强调 / PingFang。程序化绘制，不烧积分。
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 800
BG, CARD = (13, 13, 13), (26, 26, 26)
ORANGE = (247, 147, 26)
GREEN = (63, 178, 127)
BLUE = (91, 155, 213)
TXT, DIM = (229, 229, 229), (154, 154, 154)
FONT = '/System/Library/Fonts/PingFang.ttc'

ROWS = [
    # (维度, 账户模型, UTXO 模型)
    ('状态表示',   '地址 → 余额（账户表）',        '一组未花输出（硬币集）'),
    ('余额查询',   '直接读账户余额',              '累加属于你的所有 UTXO'),
    ('隐私',       '地址常复用，易画像',           '每收一笔可换新地址，更难关联'),
    ('双花防御',   '靠 nonce / 状态校验',         '输出花掉即失效，天然防重花'),
    ('并行验证',   '改共享状态需排序',             '独立 UTXO 可并行校验'),
    ('代表',       '以太坊 / Solana',             '比特币 / 莱特币'),
]

f_title = ImageFont.truetype(FONT, 40)
f_head  = ImageFont.truetype(FONT, 30)
f_dim   = ImageFont.truetype(FONT, 27)
f_cell  = ImageFont.truetype(FONT, 28)
f_foot  = ImageFont.truetype(FONT, 22)

im = Image.new('RGB', (W, H), BG)
d = ImageDraw.Draw(im)

# 标题
d.text((W/2, 52), '账户模型 vs UTXO 模型', font=f_title, fill=TXT, anchor='ma')
d.text((W/2, 108), 'T2 · 账本海｜比特币账本里没有「余额」这个字段', font=f_foot, fill=DIM, anchor='ma')

# 表头
y = 170
col_x = [64, 320, 800]          # 维度 / 账户模型 / UTXO
col_w = [216, 440, 416]
heads = [('维度', DIM), ('账户模型（如以太坊）', BLUE), ('UTXO 模型（比特币）', GREEN)]
for (t, c), x, wd in zip(heads, col_x, col_w):
    d.rounded_rectangle([x, y, x+wd, y+56], radius=10, fill=CARD, outline=c, width=3)
    d.text((x+wd/2, y+28), t, font=f_head, fill=c, anchor='mm')

# 行
rh = 72
for i, (dim, a, b) in enumerate(ROWS):
    y = 240 + i * rh
    if i % 2 == 0:
        d.rounded_rectangle([52, y-6, W-52, y+rh-14], radius=8, fill=(20, 20, 20))
    d.text((col_x[0]+col_w[0]/2, y+rh/2-10), dim, font=f_dim, fill=DIM, anchor='mm')
    d.text((col_x[1]+8, y+rh/2-10), a, font=f_cell, fill=TXT, anchor='lm')
    d.text((col_x[2]+8, y+rh/2-10), b, font=f_cell, fill=(255, 213, 128), anchor='lm')

# 底部一句话
d.line([(64, H-108), (W-64, H-108)], fill=(51, 51, 51), width=2)
d.text((W/2, H-72), '一句话：账本海记的不是数字，是一堆带锁的硬币。', font=f_head, fill=ORANGE, anchor='mm')
d.text((W/2, H-30), '慢读宝盒 · 站4 账本海', font=f_foot, fill=DIM, anchor='mm')

out = Path('/Users/mac/Desktop/宝盒知识库/比特币学习地图/assets/articles/公众号/站4-账本海/06-t2-utxo-table.png')
im.save(out, optimize=True)
print(f'✅ {out}  {im.size}  {out.stat().st_size/1024:.0f}KB')
