#!/usr/bin/env python3
"""
make_stations_overlay.py — 在 v2-B-01 教育风母图上 PIL 程序贴 9 站中文/英文/数字标注
==============================================================================

输入：v2-B-01-教育风.png (1760×2368)
输出：v2-B-01-教育风-with-stations.png（同名 + -with-stations）

9 站坐标基于 v2-B-01 视觉对位（已确认）：
  1 现金湾 → 海湾入海口中部
  2 银行堡 → 上方城堡主体
  3 双花峡 → 中部桥 + 峡谷
  4 账本海 → 海湾纸币密集区
  5 哈希岭 → 水晶山主体
  6 共识峰 → 水晶山顶
  7 矿工谷 → 矿机区
  8 私钥崖 → 瀑布悬崖
  9 代码之巅 → 皇冠

样式：
  - 数字圆点：实心视角色 + 白字数字（直径 80px）
  - 中文站名：粗体 56px，象牙白底 + 深色描边（避免画布任意位置都能读）
  - 英文站名：小字 24px，象牙白底 + 深色描边
  - 标签底框：圆角 12px 象牙白 + 视角色 2px 描边 + 半透明 90%

调色（与 v5 微信封面 + 网站六视角一致）：
  金融 #FFD700 / 技术 #3B82F6 / 历史 #22C55E / 人性 #F472B6 / 哲学 #F7931A / 商业 #A78BFA

验证：9 站坐标全在安全区 y < 1900（远在水印区 y ∈ [2012, 2312] 之上）
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

# ============ 配置 ============
MOTHER_PATH = 'assets/learning-map/v2-B-01-教育风.png'
OUT_PATH = 'assets/learning-map/v2-B-01-教育风-with-stations.png'

# 9 站定义：(id, cn_name, en_name, x, y, color, view_label)
STATIONS = [
    (1, '现金湾',     'CASH BAY',         520,  1380, '#FFD700', '金融视角'),
    (2, '银行堡',     'BANK FORT',        700,  300,  '#A78BFA', '商业视角'),
    (3, '双花峡',     'DOUBLE-SPEND GORGE', 850,  1080, '#3B82F6', '技术视角'),
    (4, '账本海',     'LEDGER SEA',       280,  1700, '#22C55E', '历史视角'),
    (5, '哈希岭',     'HASH RIDGE',       1100, 450,  '#3B82F6', '技术视角'),
    (6, '共识峰',     'CONSENSUS PEAK',   950,  220,  '#F7931A', '哲学视角'),
    (7, '矿工谷',     'MINER VALLEY',     1350, 800,  '#F472B6', '人性视角'),
    (8, '私钥崖',     'KEY CLIFFS',       200,  1200, '#22C55E', '历史视角'),
    (9, '代码之巅',   'CODE SUMMIT',      1300, 150,  '#F7931A', '哲学视角'),
]

# 颜色常量
COLOR_INK = (30, 22, 14)            # 棕黑描边
COLOR_IVORY = (245, 239, 224)       # 象牙白底
COLOR_IVORY_DARK = (220, 213, 195)  # 象牙白描边（淡）

# 字体路径（macOS）
FONT_CN_BOLD = '/System/Library/Fonts/PingFang.ttc'
FONT_EN = '/System/Library/Fonts/PingFang.ttc'  # 也用 PingFang（支持中英文）

# 字号（基于 1760×2368 画布）
SZ_NUM = 36              # 数字字号
SZ_CN = 48               # 中文站名字号
SZ_EN = 22               # 英文站名字号
SZ_VIEW = 18             # 视角标签字号

# 标签尺寸
LABEL_W = 280            # 标签宽度
LABEL_H = 140            # 标签高度（中文+英文+视角）

# 圆点半径
DOT_R = 38

# ============ 工具函数 ============

def hex2rgb(hex_str):
    h = hex_str.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0,2,4))

def get_font(path, size):
    return ImageFont.truetype(path, size)

def text_with_outline(draw, xy, text, font, fill, outline=COLOR_INK, outline_w=3):
    """描边文字（先描边后填充，确保任何背景下都清晰）"""
    x, y = xy
    # 描边 8 方向
    for dx in range(-outline_w, outline_w+1):
        for dy in range(-outline_w, outline_w+1):
            if dx*dx + dy*dy <= outline_w*outline_w:
                draw.text((x+dx, y+dy), text, font=font, fill=outline)
    draw.text(xy, text, font=font, fill=fill)

def make_label_box(w, h, color_hex):
    """生成圆角矩形标签 RGBA 层（半透明 ivory 底 + 视角色描边）"""
    layer = Image.new('RGBA', (w, h), (0,0,0,0))
    d = ImageDraw.Draw(layer)
    color = hex2rgb(color_hex)
    # 半透明 ivory 填充（alpha=235 让文字清晰）
    d.rounded_rectangle([(0,0),(w,h)], radius=14, fill=(245,239,224,235))
    # 视角色描边 2.5px
    d.rounded_rectangle([(1,1),(w-2,h-2)], radius=14, outline=color+(255,), width=3)
    return layer

# ============ 主流程 ============

def main():
    if not os.path.exists(MOTHER_PATH):
        print(f'❌ 母图不存在: {MOTHER_PATH}')
        sys.exit(1)

    base = Image.open(MOTHER_PATH).convert('RGBA')
    W, H = base.size
    print(f'母图尺寸: {W}×{H}')
    assert (W, H) == (1760, 2368), f'期望 1760×2368，实际 {W}×{H}'

    # 安全区检查
    for sid, cn, en, x, y, color, view in STATIONS:
        if y > 1900:
            print(f'❌ 站{sid} {cn} y={y} 进入水印区 (>1900)！')
            sys.exit(1)
    print('✓ 9 站坐标全在安全区 (y < 1900)')

    canvas = base.copy()

    # ===== 水印蒙版（v5 同款思路：右下角整片象牙白渐变覆盖 + 品牌尾板）=====
    # 水印位于 y∈[2260, 2360], x∈[1100, 1700]，画一整片象牙白蒙版盖住
    # + 加品牌尾板 "© 慢读宝盒 · 比特币学习地图" 取代水印位
    mask_layer = Image.new('RGBA', (W, H), (0,0,0,0))
    md = ImageDraw.Draw(mask_layer)
    # 右下矩形 1100,2230 → 1720,2360（含文字 + 圆圈）
    # 右下矩形 980,2230 → 1760,2368（整片纯不透明 ivory 覆盖水印区）
    mx0, my0, mx1, my1 = 980, 2230, 1760, 2368
    # 整片纯不透明（避免渐变漏出水印）
    solid_ivory = Image.new('RGBA', (mx1-mx0, my1-my0), (245, 239, 224, 255))
    mask_layer.paste(solid_ivory, (mx0, my0))

    canvas.alpha_composite(mask_layer)

    # 品牌尾板文字（盖在水印位上）
    overlay = Image.new('RGBA', canvas.size, (0,0,0,0))
    od = ImageDraw.Draw(overlay)
    fc = get_font(FONT_CN_BOLD, 30)
    brand = '慢读宝盒 · 比特币学习地图'
    text_with_outline(od, (mx0 + 180, my0 + 55), brand, font=fc,
                      fill=(120, 80, 40), outline=COLOR_IVORY, outline_w=2)
    fe = get_font(FONT_EN, 22)
    brand_en = 'A Learning Map of Bitcoin'
    text_with_outline(od, (mx0 + 230, my0 + 100), brand_en, font=fe,
                      fill=(160, 120, 80), outline=COLOR_IVORY, outline_w=2)
    canvas.alpha_composite(overlay)

    draw = ImageDraw.Draw(canvas)

    for sid, cn, en, x, y, color_hex, view in STATIONS:
        color_rgb = hex2rgb(color_hex)

        # ===== 圆点（数字）=====
        # 实心视角色圆 + 白边描边
        draw.ellipse([(x-DOT_R-3, y-DOT_R-3), (x+DOT_R+3, y+DOT_R+3)],
                     outline=COLOR_IVORY, width=4)
        draw.ellipse([(x-DOT_R, y-DOT_R), (x+DOT_R, y+DOT_R)],
                     fill=color_rgb)
        # 白色数字
        fn = get_font(FONT_CN_BOLD, SZ_NUM)
        tw = draw.textlength(str(sid), font=fn)
        draw.text(((x-tw/2), y-SZ_NUM/2), str(sid), font=fn, fill=(255,255,255))

        # ===== 标签底框（中文站名 + 英文站名 + 视角）=====
        # 标签贴在圆点下方（避免撞主体）
        ly = y + DOT_R + 30  # 距圆点 30px
        # 不溢出画布底部
        if ly + LABEL_H > H - 100:
            ly = y - DOT_R - 30 - LABEL_H  # 改贴圆点上方
        lx = x - LABEL_W // 2
        # 不溢出左右
        if lx < 20: lx = 20
        if lx + LABEL_W > W - 20: lx = W - 20 - LABEL_W

        # 画底框
        box = make_label_box(LABEL_W, LABEL_H, color_hex)
        canvas.alpha_composite(box, (lx, ly))

        # 在 box 上画文字
        overlay = Image.new('RGBA', canvas.size, (0,0,0,0))
        od = ImageDraw.Draw(overlay)

        # 中文名（粗体）
        fc = get_font(FONT_CN_BOLD, SZ_CN)
        text_with_outline(od, (lx + LABEL_W//2 - draw.textlength(cn, font=fc)/2, ly + 14),
                          cn, font=fc, fill=(40, 30, 20))

        # 英文名
        fe = get_font(FONT_EN, SZ_EN)
        text_with_outline(od, (lx + LABEL_W//2 - draw.textlength(en, font=fe)/2, ly + 76),
                          en, font=fe, fill=(80, 60, 40))

        # 视角标签（小字 + 视角色）
        fv = get_font(FONT_EN, SZ_VIEW)
        text_with_outline(od, (lx + LABEL_W//2 - draw.textlength(view, font=fv)/2, ly + 110),
                          view, font=fv, fill=color_rgb)

        canvas.alpha_composite(overlay)

    canvas.convert('RGB').save(OUT_PATH, 'PNG', optimize=True)
    print(f'✓ 输出: {OUT_PATH}')

    # 简单统计
    sz = os.path.getsize(OUT_PATH) / 1024 / 1024
    print(f'✓ 文件大小: {sz:.1f} MB')


if __name__ == '__main__':
    main()