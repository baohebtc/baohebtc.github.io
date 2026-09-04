#!/usr/bin/env python3
"""cover_template_v5.py — 9 站 900×383 微信头条封面

核心：接受预裁切的 1760×749 母图（来自 crop_9_safe.py），直接缩放到 900×383。
母图保持原样，零 inpaint、零修复痕迹。

CLI:
  # 单张
  cover_template_v5.py --crop crops/crop-station-4.png --b <btc.png> \
                      --station 4 --out out/cover-A-batch/cover-A-station-4.png

  # 批量
  cover_template_v5.py --batch --b <btc.png> --crop-dir crops/ \
                      --out-dir out/cover-A-batch/
"""
import argparse
import os, json
from PIL import Image, ImageDraw, ImageFont
import platform

# ===== 常量 =====
CANVAS_W, CANVAS_H = 900, 383
COLOR_IVORY = (245, 239, 224)
COLOR_INK = (62, 39, 23)         # 棕墨（与品牌一致）
COLOR_INK_LIGHT = (107, 74, 43)
COLOR_GOLD = (255, 200, 80)

# B 符号位置/尺寸（不撞中央文字）
B_SIZE = 64
B_POS = (18, 18)
B_PADDING = 8

# 中央文字区域
CENTER_X = CANVAS_W // 2
CENTER_Y = CANVAS_H // 2

# 底部叠标题蒙版（保留——微信叠底部标题）
BOTTOM_MASK_H = 50

# ===== 字体 =====
def get_font(size, weight='regular'):
    candidates = [
        '/System/Library/Fonts/PingFang.ttc',
        '/System/Library/Fonts/STHeiti Medium.ttc',
        '/System/Library/Fonts/STHeiti Light.ttc',
        '/Library/Fonts/Arial Unicode.ttf',
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()

# ===== 9 站文案（与 brand token 一致） =====
STATION_TEXT = {
    '1':   ('现金湾',     'Bitcoin Bay',     '货币的第一声'),
    '1.5': ('钱到底是什么', 'What is Money',   '货币哲学插篇'),
    '2':   ('银行堡',     'Bank Fortress',   '货币的三大缺陷'),
    '3':   ('双花峡',     'Double-Spend Gorge', '一笔钱能花两次吗'),
    '4':   ('账本海',     'Ledger Sea',      '谁来记这本账'),
    '5':   ('哈希岭',     'Hash Ridge',      '一道数学封印'),
    '6':   ('共识峰',     'Consensus Peak',  '陌生人如何达成一致'),
    '7':   ('矿工谷',     'Miner Valley',    '谁来添加新的一页'),
    '8':   ('私钥崖',     'Key Cliff',       '你就是自己的银行'),
    '9':   ('代码之巅',   'Code Summit',     '比特币的全部秘密'),
}

# ===== 工具：文字带描边（保证水彩底可读） =====
def draw_text_with_outline(draw, xy, text, font, fill, outline=(255, 247, 230), outline_w=3):
    x, y = xy
    # 描边（4 方向 + 4 对角）
    for dx in range(-outline_w, outline_w + 1):
        for dy in range(-outline_w, outline_w + 1):
            if dx == 0 and dy == 0:
                continue
            draw.text((x + dx, y + dy), text, font=font, fill=outline)
    draw.text(xy, text, font=font, fill=fill)

# ===== 工具：右下安全区蒙版（去除 v4 的大块，改成保守小蒙版仅防微信分享卡） =====
def apply_bottom_mask(canvas):
    """底部 50px 渐变到象牙白，防微信叠底部标题撞主体"""
    mask = Image.new('RGBA', (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    grad = Image.new('L', (CANVAS_W, BOTTOM_MASK_H))
    gd = ImageDraw.Draw(grad)
    for i in range(BOTTOM_MASK_H):
        a = int(170 * ((BOTTOM_MASK_H - 1 - i) / max(1, BOTTOM_MASK_H - 1)))
        gd.line([(0, i), (CANVAS_W, i)], fill=a)
    bm_im = Image.new('RGBA', (CANVAS_W, BOTTOM_MASK_H), (*COLOR_IVORY, 0))
    bm_im.putalpha(grad)
    # 用 L mask paste——避免 RGBA paste 预乘问题
    mask.paste(bm_im, (0, CANVAS_H - BOTTOM_MASK_H), bm_im.split()[3])
    canvas = canvas.convert('RGBA')
    canvas.alpha_composite(mask)
    return canvas.convert('RGB')

# ===== 单站封面生成 =====
def make_cover(crop_path, b_path, station_id):
    """生成单张 900×383 封面"""
    # 1. 预裁切母图直接 resize 到画布
    crop = Image.open(crop_path).convert('RGB')
    canvas = crop.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)

    draw = ImageDraw.Draw(canvas)

    # 2. 左上 ₿
    if b_path and os.path.exists(b_path):
        b = Image.open(b_path).convert('RGBA')
        b.thumbnail((B_SIZE, B_SIZE), Image.LANCZOS)
        canvas.paste(b, B_POS, b)

    # 3. 顶部左侧品牌字
    brand_font = get_font(18)
    draw_text_with_outline(
        draw,
        (B_POS[0] + B_SIZE + B_PADDING, B_POS[1] + 6),
        '慢读宝盒',
        brand_font, COLOR_INK,
    )
    sub_font = get_font(11)
    draw_text_with_outline(
        draw,
        (B_POS[0] + B_SIZE + B_PADDING, B_POS[1] + 30),
        'SLOW READ · BITCOIN',
        sub_font, COLOR_INK_LIGHT,
    )

    # 4. 中央文字（站号大 + 中文站名 + 英文 + 副标）
    if station_id not in STATION_TEXT:
        raise ValueError(f'未知站号 {station_id}')
    zh, en, sub = STATION_TEXT[station_id]

    # 站号（大，背景圆角牌）
    num_font = get_font(56, 'bold')
    num_w = 70
    num_h = 70
    num_x = 60
    num_y = CANVAS_H // 2 - num_h // 2 - 30
    # 象牙白圆角牌
    draw.rounded_rectangle(
        [num_x, num_y, num_x + num_w, num_y + num_h],
        radius=12, fill=COLOR_IVORY,
    )
    # 站号文字
    bbox = draw.textbbox((0, 0), station_id, font=num_font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = num_x + (num_w - tw) // 2 - bbox[0]
    ty = num_y + (num_h - th) // 2 - bbox[1]
    draw.text((tx, ty), station_id, font=num_font, fill=COLOR_INK)

    # 中文站名（大）
    zh_font = get_font(38, 'bold')
    zh_x = num_x + num_w + 20
    zh_y = num_y + 6
    draw_text_with_outline(draw, (zh_x, zh_y), zh, zh_font, COLOR_INK)

    # 英文副标
    en_font = get_font(16)
    en_y = zh_y + 44
    draw_text_with_outline(draw, (zh_x, en_y), en, en_font, COLOR_INK_LIGHT)

    # 中文短副标
    sub_zh_font = get_font(14)
    sub_y = en_y + 22
    draw_text_with_outline(draw, (zh_x, sub_y), sub, sub_zh_font, COLOR_INK_LIGHT)

    # 5. 底部叠标题蒙版
    canvas = apply_bottom_mask(canvas)
    draw = ImageDraw.Draw(canvas)

    # 6. 底部品牌尾标（缩小字号，远离底部 80px 阈值）
    foot_font = get_font(12)
    draw_text_with_outline(
        draw,
        (CANVAS_W // 2 - 84, CANVAS_H - 28),
        '慢读宝盒 · 比特币学习地图',
        foot_font, COLOR_INK_LIGHT, outline_w=2,
    )

    return canvas

# ===== CLI =====
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--crop', help='单张预裁切母图路径')
    ap.add_argument('--b', help='官方 ₿ PNG 路径')
    ap.add_argument('--station', help='站号（1/1.5/2-9）')
    ap.add_argument('--out', help='输出 PNG 路径')
    ap.add_argument('--batch', action='store_true', help='批量模式')
    ap.add_argument('--crop-dir', default='samples/edu-mothermap/v2/crops',
                    help='批量模式：预裁切母图目录')
    ap.add_argument('--out-dir', default='out/cover-A-batch',
                    help='批量模式：输出目录')
    args = ap.parse_args()

    if args.batch:
        os.makedirs(args.out_dir, exist_ok=True)
        manifest = json.load(open(os.path.join(args.crop_dir, 'manifest.json')))
        for item in manifest:
            sid = item['station']
            crop = os.path.join(args.crop_dir, f'crop-station-{sid}.png')
            out = os.path.join(args.out_dir, f'cover-A-station-{sid}.png')
            canvas = make_cover(crop, args.b, sid)
            canvas.save(out, 'PNG')
            print(f'  站{sid} → {out}')
        print(f'\n批量完成，共 {len(manifest)} 张')
    else:
        if not (args.crop and args.station and args.out):
            ap.error('单张模式需要 --crop --station --out')
        canvas = make_cover(args.crop, args.b, args.station)
        canvas.save(args.out, 'PNG')
        print(f'→ {args.out}')

if __name__ == '__main__':
    main()