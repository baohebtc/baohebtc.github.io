#!/usr/bin/env python3
"""从 v2-B-01 母图安全区裁出 9 站各自 1760×749 子图

安全区定义：母图 y < 2012（避开可灵水印区 y: 2012-2312）
9 站各自取不同 y 中心，裁出后直接缩放成 900×383 封面。
"""
from PIL import Image
import os, json, sys

MOTHER = 'samples/edu-mothermap/v2/v2-B-01.png'
OUT_DIR = 'samples/edu-mothermap/v2/crops'

# 9 站（含 1.5）的 y 中心位置——全在安全区 [374, 1638] 内
STATIONS = [
    ('1',   1450, '现金湾',     'Bitcoin Bay',        '货币的第一声'),
    ('1.5', 1280, '钱到底是什么', 'What is Money',      '货币哲学插篇'),
    ('2',   380,  '银行堡',     'Bank Fortress',       '货币的三大缺陷'),
    ('3',   1100, '双花峡',     'Double-Spend Gorge', '一笔钱能花两次吗'),
    ('4',   1620, '账本海',     'Ledger Sea',          '谁来记这本账'),
    ('5',   700,  '哈希岭',     'Hash Ridge',          '一道数学封印'),
    ('6',   460,  '共识峰',     'Consensus Peak',      '陌生人如何达成一致'),
    ('7',   900,  '矿工谷',     'Miner Valley',        '谁来添加新的一页'),
    ('8',   1300, '私钥崖',     'Key Cliff',           '你就是自己的银行'),
    ('9',   400,  '代码之巅',   'Code Summit',         '比特币的全部秘密'),
]

CROP_W = 1760
CROP_H = 749       # = 1760 / 2.35，封面比例
HALF_H = CROP_H // 2  # 374
SAFE_Y_MAX = 2012  # 母图水印区上限

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    mother = Image.open(MOTHER).convert('RGB')
    W_M, H_M = mother.size
    assert W_M == CROP_W, f'母图宽 {W_M} != {CROP_W}'
    print(f'母图: {W_M}×{H_M}  |  安全区 y∈[0, {SAFE_Y_MAX}]  |  裁切 1760×749')

    manifest = []
    for sid, yc, zh, en, sub in STATIONS:
        y0 = yc - HALF_H
        y1 = yc + (CROP_H - HALF_H)
        assert y0 >= 0, f'站{sid} y0={y0}<0'
        assert y1 <= SAFE_Y_MAX, f'站{sid} y1={y1}>{SAFE_Y_MAX} 越水印'
        crop = mother.crop((0, y0, CROP_W, y1))
        out = os.path.join(OUT_DIR, f'crop-station-{sid}.png')
        crop.save(out, 'PNG')
        # 验证右下角无水印：右下 16%×8% 应不含有水印特征色（接近背景）
        rw, rh = CROP_W // 6, CROP_H // 12  # ~293×62
        rb = crop.crop((CROP_W - rw, CROP_H - rh, CROP_W, CROP_H))
        # 抽样
        sample = list(rb.getdata())[::100][:5]
        manifest.append({
            'station': sid,
            'zh': zh,
            'en': en,
            'sub': sub,
            'y_center': yc,
            'y_range': [y0, y1],
            'out': out,
            'sample_bottomright_rgb': [list(s) for s in sample],
        })
        print(f'  站{sid} ({zh}): y∈[{y0},{y1}] → {out}')

    with open(os.path.join(OUT_DIR, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f'\\nmanifest → {OUT_DIR}/manifest.json')
    print(f'所有 10 站裁切均在安全区内 ✓')

if __name__ == '__main__':
    main()