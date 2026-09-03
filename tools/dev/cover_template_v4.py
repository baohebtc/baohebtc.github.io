# -*- coding: utf-8 -*-
"""
Phase 4 · 9 站微信封面模板生成器 v4
=====================================

用法：
  # 1. 单张样张（站 4）
  python tools/dev/cover_template_v4.py \
      --mother samples/edu-mothermap/v2/v2-B-01-clean.png \
      --b assets/brand/btcoin-symbol-bitboy-128.png \
      --station 4 \
      --scheme A \
      --out out/cover-A-station-4.png

  # 2. 9 张批量
  python tools/dev/cover_template_v4.py \
      --mother samples/edu-mothermap/v2/v2-B-01-clean.png \
      --b assets/brand/btcoin-symbol-bitboy-128.png \
      --batch \
      --scheme A \
      --out out/scheme-A/

方案 A：整图共用（缩放到 900×383）
方案 B：按可识别地标裁切（站 1/2/4/5/7/9）+ 其它站共用整图
方案 C：整图共用 + 程序化高亮环
"""
import os, sys, glob, json, argparse
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

# ====== 画布 ======
CANVAS_W = 900
CANVAS_H = 383
SAFE = 383                       # 中央安全区

# ====== 品牌色（暖色教育风） ======
COLOR_DARK_BROWN  = (92, 58, 33)     # 主文字 暖棕
COLOR_BROWN       = (107, 74, 43)    # 副标 棕
COLOR_LIGHT_BROWN = (139, 115, 85)   # 英文小字 灰棕
COLOR_IVORY       = (245, 239, 224)  # 暖象牙白
COLOR_ACCENT      = (247, 147, 26)   # 官方 ₿ 橙
COLOR_HALO        = (92, 58, 33, 180)  # 高亮环（方案 C 用）
COLOR_BG_PILL     = (245, 239, 224, 220)  # 半透明白底（防字糊）

# ====== 中文字体 ======
FONT_HEITI_BOLD = "/System/Library/Fonts/STHeiti Medium.ttc"
FONT_HEITI_REG  = "/System/Library/Fonts/STHeiti Medium.ttc"
FONT_PINGFANG   = "/System/Library/Fonts/PingFang.ttc"
FONT_SONG       = "/System/Library/Fonts/Songti.ttc"


def get_font(size, bold=False, kind='hei'):
    """font kind: hei/PingFang/song/mono"""
    paths = {
        'hei': [FONT_HEITI_BOLD, FONT_HEITI_REG, FONT_PINGFANG],
        'pf':  [FONT_PINGFANG, FONT_HEITI_REG],
        'song':[FONT_SONG, FONT_HEITI_BOLD, FONT_PINGFANG],
        'mono':["/System/Library/Fonts/SFNSMono.ttf", FONT_PINGFANG],
    }.get(kind, [FONT_PINGFANG])
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


# ====== 9 站文字字典（中文+英文+副标） ======
STATION_TEXT = {
    '1':   {'name': '现金湾',     'en': 'CASH BAY',          'sub': '—— 比特币的第一声',     'pinyin': 'CASH BAY'},
    '1.5': {'name': '钱到底是什么', 'en': 'WHAT IS MONEY',     'sub': '—— 货币哲学插篇',      'pinyin': 'WHAT IS MONEY'},
    '2':   {'name': '银行堡',     'en': 'VAULT KEEP',        'sub': '—— 货币的三大缺陷',     'pinyin': 'VAULT KEEP'},
    '3':   {'name': '双花峡',     'en': 'TWIN GORGE',        'sub': '—— 一笔钱能花两次吗？', 'pinyin': 'TWIN GORGE'},
    '4':   {'name': '账本海',     'en': 'LEDGER SEA',        'sub': '—— 谁来记这本账？',     'pinyin': 'LEDGER SEA'},
    '5':   {'name': '哈希岭',     'en': 'HASH RIDGE',        'sub': '—— 一道数学封印',       'pinyin': 'HASH RIDGE'},
    '6':   {'name': '共识峰',     'en': 'CONSENSUS PEAK',    'sub': '—— 陌生人如何达成一致？', 'pinyin': 'CONSENSUS PEAK'},
    '7':   {'name': '矿工谷',     'en': 'MINER VALLEY',      'sub': '—— 谁来添加新的一页？', 'pinyin': 'MINER VALLEY'},
    '8':   {'name': '私钥崖',     'en': 'KEY CLIFF',         'sub': '—— 你就是自己的银行',   'pinyin': 'KEY CLIFF'},
    '9':   {'name': '代码之巅',   'en': 'CODE SUMMIT',       'sub': '—— 比特币的全部秘密',   'pinyin': 'CODE SUMMIT'},
}

# ====== 9 站在 v2-B-01 上的归一化坐标（nx, ny 都在 0-1） ======
# 实测网格读图：站1/2/4/5/7/9 可识别；其余按路径走向
STATION_COORDS_NORM = {
    '1':   (0.10, 0.85),   # 海湾水池+账本（左下）
    '1.5': (0.10, 0.78),   # 站1 略上
    '2':   (0.15, 0.05),   # 城堡（顶部偏左）
    '3':   (0.40, 0.35),   # 中央河+小屋
    '4':   (0.60, 0.45),   # 桥+蓝色水面
    '5':   (0.65, 0.27),   # 水晶山脊
    '6':   (0.30, 0.55),   # 多路径汇聚
    '7':   (0.75, 0.35),   # 采矿机器
    '8':   (0.65, 0.85),   # 孤钥匙（推断）
    '9':   (0.70, 0.12),   # 皇冠
}


# ============== 底层工具 ==============
def paste_b_icon(canvas, b_img_path, x=18, y=18, size=64):
    """贴官方 ₿ PNG（RGBA → 转 RGB 到画布）"""
    b = Image.open(b_img_path).convert('RGBA')
    b = b.resize((size, size), Image.LANCZOS)
    canvas.paste(b, (x, y), b)


def draw_text_with_outline(draw, xy, text, font, fill, outline=None, outline_w=2):
    """文字加描边（防暖色背景糊字）"""
    if outline:
        x, y = xy
        for dx in range(-outline_w, outline_w + 1):
            for dy in range(-outline_w, outline_w + 1):
                if dx == 0 and dy == 0:
                    continue
                draw.text((x + dx, y + dy), text, font=font, fill=outline)
    draw.text(xy, text, font=font, fill=fill)


def text_size(draw, text, font):
    """文字包围盒（兼容老 Pillow）"""
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    except Exception:
        try:
            return font.getsize(text)
        except Exception:
            return len(text) * font.size // 2, font.size


def center_x_for(draw, text, font, target_x):
    """返回让文字水平居中于 target_x 的 x 坐标"""
    w, _ = text_size(draw, text, font)
    return int(target_x - w / 2)


# ============== 主生成器 ==============
def make_cover(mother_path, b_path, station_id, scheme='A', halo_color=None):
    """生成 1 张 900×383 封面
    scheme: A=整图共用 / B=按站裁切 / C=整图共用+高亮环
    """
    info = STATION_TEXT[station_id]
    nx, ny = STATION_COORDS_NORM[station_id]

    # ---- 画布 ----
    canvas = Image.new('RGB', (CANVAS_W, CANVAS_H), COLOR_IVORY)
    draw = ImageDraw.Draw(canvas)

    # ---- 母图铺底（方案 A/C：整图缩放） ----
    mother = Image.open(mother_path).convert('RGB')
    Mw, Mh = mother.size

    if scheme == 'B' and station_id in {'1', '2', '4', '5', '7', '9'}:
        # 方案 B：按站裁切（保留地标 + 上下文）
        # 母图是 1760×2368 竖版，裁 900×383 的横条
        # 裁切中心 = 该站归一化坐标
        cx_m, cy_m = int(nx * Mw), int(ny * Mh)
        # 横条宽度 = 母图全宽；高度 = 383×(Mh/CANVAS_H) 等比缩放
        ratio = CANVAS_H / 383  # 母图相对画布的纵向比
        h_strip = 383  # 固定裁 383 高
        w_strip = Mw   # 母图全宽
        y1 = max(0, cy_m - h_strip // 2)
        y2 = min(Mh, y1 + h_strip)
        y1 = max(0, y2 - h_strip)  # 保证高度
        strip = mother.crop((0, y1, Mw, y2))
        strip = strip.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
        canvas.paste(strip, (0, 0))
    else:
        # 方案 A / 方案 C（非 B 的）/ 方案 B 不可识别的站
        # 整图等比缩放 → 铺满 900×383（裁上下）
        ratio = CANVAS_W / Mw
        new_h = int(Mh * ratio)
        scaled = mother.resize((CANVAS_W, new_h), Image.LANCZOS)
        # 上下裁切，保留该站区域
        target_y_in_scaled = int(ny * new_h)
        y1 = max(0, target_y_in_scaled - CANVAS_H // 2)
        y2 = y1 + CANVAS_H
        if y2 > new_h:
            y2 = new_h
            y1 = max(0, y2 - CANVAS_H)
        canvas.paste(scaled.crop((0, y1, CANVAS_W, y2)), (0, 0))

    # ---- 方案 C：程序化高亮环 ----
    if scheme == 'C':
        # 在画布的 (nx, ny) 位置画半透明橙色虚线圆
        hx = int(nx * CANVAS_W)
        hy = int(ny * CANVAS_H)
        r = 70
        # 在新图层画
        overlay = Image.new('RGBA', (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        # 虚线圆：12 段
        import math
        for i in range(12):
            a0 = 2 * math.pi * i / 12
            a1 = 2 * math.pi * (i + 0.65) / 12
            x0 = hx + r * math.cos(a0); y0 = hy + r * math.sin(a0)
            x1 = hx + r * math.cos(a1); y1 = hy + r * math.sin(a1)
            od.line([(x0, y0), (x1, y1)], fill=(247, 147, 26, 220), width=4)
        # 内圈细描
        od.ellipse([hx-r-3, hy-r-3, hx+r+3, hy+r+3], outline=(247, 147, 26, 110), width=2)
        canvas = canvas.convert('RGBA')
        canvas.alpha_composite(overlay)
        canvas = canvas.convert('RGB')
        draw = ImageDraw.Draw(canvas)

    # ---- 右下角安全蒙版（防微信叠分享卡片/水印）----
    # 微信公众号头条封面右下 22%×42% 会被白色分享卡片覆盖
    # 该区域直接贴纯象牙白——反正被微信分享卡覆盖，渐变无意义
    mask = Image.new('RGBA', (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    mx0, my0, mx1, my1 = 700, 220, 900, 383
    solid = Image.new('RGBA', (mx1 - mx0, my1 - my0), (245, 239, 224, 255))
    mask.paste(solid, (mx0, my0), solid)

    # ---- 底部叠标题蒙版（防标题区撞主体文字）----
    # 微信叠标题占底部约 60-80px，渐变到象牙白
    # 用 L mask 直接 paste，避免 alpha_composite 预乘问题
    bmh = 60
    bottom_grad = Image.new('L', (CANVAS_W, bmh))
    bgd = ImageDraw.Draw(bottom_grad)
    for i in range(bmh):
        a = int(255 * ((bmh - 1 - i) / max(1, bmh - 1)))  # 上不透明(255) → 下透明(0)
        bgd.line([(0, i), (CANVAS_W, i)], fill=a)
    bm_im = Image.new('RGB', (CANVAS_W, bmh), COLOR_IVORY)
    canvas.paste(bm_im, (0, CANVAS_H - bmh), bottom_grad)

    canvas = canvas.convert('RGBA')
    canvas.alpha_composite(mask)
    canvas = canvas.convert('RGB')
    draw = ImageDraw.Draw(canvas)

    # ---- 文字层（全部居中于中央安全区） ----
    cx = CANVAS_W // 2
    cy = CANVAS_H // 2

    # 大站号（单字符 180pt / 双字符 110pt）
    is_two_char = '.' in station_id or len(station_id) > 1
    num_font_size = 110 if is_two_char else 180
    num_font = get_font(num_font_size, bold=True, kind='hei')

    num_text = station_id
    num_x = center_x_for(draw, num_text, num_font, cx)
    num_y = cy - num_font_size // 2 - 10
    # 文字加象牙白描边（防止暖色背景糊字）
    draw_text_with_outline(draw, (num_x, num_y), num_text, num_font,
                           fill=COLOR_DARK_BROWN, outline=COLOR_IVORY, outline_w=4)

    # 站名（48pt）
    name_font = get_font(48, bold=True, kind='hei')
    name_text = info['name']
    name_x = center_x_for(draw, name_text, name_font, cx)
    name_y = num_y + num_font_size + 4
    draw_text_with_outline(draw, (name_x, name_y), name_text, name_font,
                           fill=COLOR_DARK_BROWN, outline=COLOR_IVORY, outline_w=3)

    # 副标（22pt）
    sub_font = get_font(22, bold=False, kind='pf')
    sub_text = info['sub']
    sub_x = center_x_for(draw, sub_text, sub_font, cx)
    sub_y = name_y + 56
    draw_text_with_outline(draw, (sub_x, sub_y), sub_text, sub_font,
                           fill=COLOR_BROWN, outline=COLOR_IVORY, outline_w=2)

    # 英文小字（12pt 居中放在站号上方）
    en_font = get_font(14, bold=False, kind='pf')
    en_text = info['en']
    en_x = center_x_for(draw, en_text, en_font, cx)
    en_y = num_y - 22
    draw.text((en_x, en_y), en_text, font=en_font, fill=COLOR_LIGHT_BROWN)

    # ---- 左上 ₿ + 慢读宝盒 ----
    paste_b_icon(canvas, b_path, x=18, y=18, size=64)
    draw = ImageDraw.Draw(canvas)
    brand_font = get_font(16, bold=True, kind='hei')
    draw.text((92, 22), '慢读宝盒', font=brand_font, fill=COLOR_DARK_BROWN)
    brand_en_font = get_font(11, bold=False, kind='pf')
    draw.text((92, 44), 'CASHBOX · 比特币学习地图', font=brand_en_font, fill=COLOR_LIGHT_BROWN)

    # ---- 右下英文小字（避开底部 80px 叠标题区，所以放右下 50px 高度内）----
    # 不放内容，避免叠标题遮挡

    # ---- 顶部右侧站号水印（半透明大字，作为缩略图识别用）----
    # 已通过中央站号覆盖，这里不加

    return canvas


# ============== 批量 ==============
def batch_generate(mother_path, b_path, scheme, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    results = []
    for sid in ['1', '1.5', '2', '3', '4', '5', '6', '7', '8', '9']:
        out = os.path.join(out_dir, f'cover-{scheme}-station-{sid}.png')
        im = make_cover(mother_path, b_path, sid, scheme=scheme)
        im.save(out, 'PNG', quality=95)
        results.append((sid, out))
        print(f'  ✓ 站 {sid}: {out}')
    return results


# ============== CLI ==============
def main():
    p = argparse.ArgumentParser()
    p.add_argument('--mother', required=True, help='母图路径')
    p.add_argument('--b', required=True, help='官方 ₿ PNG 路径')
    p.add_argument('--station', help='单张站号（1, 1.5, 2...9）')
    p.add_argument('--scheme', default='A', choices=['A', 'B', 'C'])
    p.add_argument('--out', required=True, help='输出 PNG 路径或目录')
    p.add_argument('--batch', action='store_true', help='批量 9 站')
    args = p.parse_args()

    if args.batch:
        results = batch_generate(args.mother, args.b, args.scheme, args.out)
        print(f'\n✅ 批量完成 {len(results)} 张 → {args.out}')
        return 0
    else:
        if not args.station:
            print('ERROR: 单张模式必须 --station')
            return 1
        im = make_cover(args.mother, args.b, args.station, scheme=args.scheme)
        os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
        im.save(args.out, 'PNG', quality=95)
        print(f'✅ 站 {args.station} → {args.out}')
        return 0


if __name__ == '__main__':
    sys.exit(main())