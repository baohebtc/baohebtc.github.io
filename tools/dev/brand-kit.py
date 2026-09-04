"""
慢读宝盒 · 视觉品牌工具包 v1.0
=================================
design tokens 的可执行实现。任何图（封面/配图/map-figure）都走这个工具包，
保证 9 站品牌一致。

依赖：PIL (Pillow), numpy
字体：macOS 系统（PingFang/Songti/STHeiti）
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

# ============== design tokens ==============
# 色
SAND       = "#E8D5A8"   # 底 60%
TERRAIN    = "#8B6F3A"   # 棕地形 25%
BTC_ORANGE = "#F7931A"   # 河/主色 8%
WARM_WHITE = "#FFF8E7"   # 强调 4%
DARK       = "#0D0D0D"   # 深色块 3%
CARD_DARK  = "#1A1A1A"   # 卡片底
ANTIQUE_GOLD = "#B8860B"
ALERT_RED  = "#DC2626"
TRUST_GREEN= "#10B981"
WISDOM_VIOLET="#8B5CF6"

# 6 视角色（点缀，不超过 4 个同时出现）
VIEW_COLORS = [
    ("哲学", "#F7931A"),
    ("技术", "#3B82F6"),
    ("历史", "#10B981"),
    ("人性", "#EC4899"),
    ("金融", "#F59E0B"),
    ("商业", "#8B5CF6"),
]

# 9 站中心点坐标（基于 P1-v4 1440x1920 源图，标注：站意象位置，非标签位置）
STATION_COORDS = {
    "1":  {"name": "现金湾",     "en": "CASH BAY",        "x": 220,  "y": 1820},
    "1.5":{"name": "钱到底是什么", "en": "WHAT IS MONEY",  "x": 380,  "y": 1720},
    "2":  {"name": "银行堡",     "en": "VAULT KEEP",      "x": 320,  "y": 1490},
    "3":  {"name": "双花峡",     "en": "DOUBLE-SPEND GORGE","x": 360, "y": 1200},
    "4":  {"name": "账本海",     "en": "LEDGER SEA",      "x": 1000, "y": 1000},
    "5":  {"name": "哈希岭",     "en": "HASH RIDGE",      "x": 330,  "y": 720},
    "6":  {"name": "共识峰",     "en": "CONSENSUS PEAK",  "x": 1020, "y": 540},
    "7":  {"name": "矿工谷",     "en": "MINER VALLEY",    "x": 950,  "y": 700},
    "8":  {"name": "私钥崖",     "en": "KEY CLIFF",       "x": 1130, "y": 220},
    "9":  {"name": "代码之巅",   "en": "CODE SUMMIT",     "x": 480,  "y": 110},
}

# 字体（macOS 系统字体）
FONT_REGULAR    = "/System/Library/Fonts/STHeiti Medium.ttc"
FONT_BOLD       = "/System/Library/Fonts/STHeiti Bold.ttc"
FONT_SONG_BOLD  = "/System/Library/Fonts/Songti.ttc"
FONT_PINGFANG   = "/System/Library/Fonts/PingFang.ttc"


def clamp(v, lo, hi):
    return max(lo, min(v, hi))


def get_font(size, bold=False, song=False):
    """获取字体（带 fallback）"""
    if song:
        paths = [FONT_SONG_BOLD, FONT_BOLD, FONT_PINGFANG]
    elif bold:
        paths = [FONT_BOLD, FONT_PINGFANG, FONT_REGULAR]
    else:
        paths = [FONT_REGULAR, FONT_PINGFANG]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


# ============== ₿ 标志（programmatic，国际同步） ==============
def draw_bitcoin_b(canvas, cx, cy, r):
    """在 canvas 上画官方 ₿ 标志（橙圆+白B 14° 倾斜，含 2 道横）。
    cx, cy: 圆心；r: 圆半径
    """
    s = int(r * 2.8)
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx_s, cy_s = s/2, s/2

    # 1. 柔光（外层金色光晕）
    glow = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([cx_s-r*1.15, cy_s-r*1.15, cx_s+r*1.15, cy_s+r*1.15], fill=(247, 147, 26, 60))
    glow = glow.filter(ImageFilter.GaussianBlur(r*0.08))
    img.alpha_composite(glow)
    d = ImageDraw.Draw(img)

    # 2. 橙圆
    d.ellipse([cx_s-r, cy_s-r, cx_s+r, cy_s+r], fill=BTC_ORANGE)

    # 3. B 几何
    sw = r * 0.16
    b_outer_w = r * 0.95
    b_total_h = r * 1.5
    bx0 = cx_s - b_outer_w/2
    bx1 = cx_s + b_outer_w/2
    by0 = cy_s - b_total_h/2
    by1 = cy_s + b_total_h/2

    # 左竖
    d.rectangle([bx0, by0, bx0+sw, by1], fill=WARM_WHITE)
    # 3 横
    d.rectangle([bx0, by0, bx1, by0+sw], fill=WARM_WHITE)
    d.rectangle([bx0, cy_s-sw/2, bx1, cy_s+sw/2], fill=WARM_WHITE)
    d.rectangle([bx0, by1-sw, bx1, by1], fill=WARM_WHITE)
    # 右半圆（D 形外缘）
    d.chord([bx0, by0, bx1+sw*0.4, cy_s+sw/2], 270, 90, fill=WARM_WHITE)
    d.chord([bx0, cy_s-sw/2, bx1+sw*0.4, by1], 270, 90, fill=WARM_WHITE)
    # 挖空（用圆色填充"假孔"）
    hole_w = b_outer_w - sw*2.5
    d.chord([bx0 + sw*1.5, by0+sw*1.3, bx0+sw*1.5+hole_w, cy_s-sw*0.5], 270, 90, fill=BTC_ORANGE)
    d.chord([bx0 + sw*1.5, cy_s+sw*0.5, bx0+sw*1.5+hole_w, by1-sw*1.3], 270, 90, fill=BTC_ORANGE)
    # 2 道横（₿ 特征）
    bar_w = r * 0.30
    bar_h = sw * 0.65
    d.rectangle([bx0-bar_w, by0-bar_h*0.3, bx0+sw, by0+bar_h*0.5], fill=WARM_WHITE)
    d.rectangle([bx0-bar_w, by1-bar_h*0.5, bx0+sw, by1+bar_h*0.3], fill=WARM_WHITE)

    # 4. 旋转 14°
    rotated = img.rotate(14, resample=Image.BICUBIC, center=(cx_s, cy_s), expand=False)
    canvas.paste(rotated, (int(cx-s/2), int(cy-s/2)), rotated)


# ============== 6 元素封面合成 ==============
def make_cover(bg_path, station_id, title, subtitle, output_path, crop_box=None, crop_w=1440, crop_h=1920, highlight_pos=None):
    """6 元素封面 = 底图 + 6 元素 + ₿ 标志。
    bg_path: 底图路径（P1-v4 完整图，或 AI 生成的抽象场景）
    station_id: 站号（字符串 "1" / "1.5" / "2" ...）
    title: 大标题
    subtitle: 副标题
    output_path: 输出路径
    crop_box: 如果提供，裁切底图 (l, t, r, b)
    highlight_pos: 高亮环在最终画布的 (x, y)。如果 None，默认画布中心
    """
    st = STATION_COORDS[station_id]
    # 1. 加载底图
    bg = Image.open(bg_path).convert("RGBA")
    if crop_box:
        bg = bg.crop(crop_box)
    bg = bg.resize((crop_w, crop_h), Image.LANCZOS)
    W, H = bg.size
    canvas = bg.copy()
    d = ImageDraw.Draw(canvas)

    # 暗化蒙版（让文字更可读）
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    # 顶部暗化（放 logo+图例）——加强，盖住源图顶部可能自带的 Bitcoin 标志
    od.rectangle([0, 0, W, 170], fill=(0, 0, 0, 135))
    # 底部暗化（放大标题+副标题+站号）
    od.rectangle([0, H-360, W, H], fill=(0, 0, 0, 160))
    # 左下更大暗化
    od.rectangle([0, H-360, W*0.7, H], fill=(0, 0, 0, 90))
    canvas.alpha_composite(overlay)
    d = ImageDraw.Draw(canvas)

    # ===== 元素 1：品牌 logo（左上） =====
    logo_font = get_font(36, bold=True)
    d.text((40, 50), "慢读宝盒", fill=WARM_WHITE, font=logo_font)

    # ===== 元素 2：视角图例（右上） =====
    legend_font = get_font(16, bold=False)
    d.text((W-280, 50), "六视角 · 读懂比特币", fill=WARM_WHITE, font=legend_font)
    # 6 圆点 + 标签（用 6 视角色）
    lx, ly = W-280, 80
    for i, (name, color) in enumerate(VIEW_COLORS):
        cx_dot = lx + i*45 + 8
        cy_dot = ly + 8
        d.ellipse([cx_dot-6, cy_dot-6, cx_dot+6, cy_dot+6], fill=color)
        d.text((cx_dot+12, cy_dot-8), name, fill=WARM_WHITE, font=legend_font)

    # ===== 元素 3+4：中心区（站名 + 官方 ₿ 标志） =====
    if highlight_pos:
        ring_cx, ring_cy = highlight_pos
        center_y = ring_cy
    else:
        ring_cx, ring_cy = W//2, H//2 - 80
        center_y = ring_cy
    # 中央深色徽章（medallion）—— 隔离程序化 ₿ 与背景，消除源图自带 B 的视觉冲突
    med = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    md = ImageDraw.Draw(med)
    med_r = 250
    md.ellipse([ring_cx-med_r, ring_cy-med_r, ring_cx+med_r, ring_cy+med_r], fill=(13, 13, 13, 150))
    med = med.filter(ImageFilter.GaussianBlur(38))
    canvas.alpha_composite(med)
    d = ImageDraw.Draw(canvas)
    # 站名环背景
    ring_r = 200
    # 双层金环
    for i, (rr, alpha) in enumerate([(ring_r, 220), (ring_r+18, 180), (ring_r+36, 140)]):
        d.ellipse([ring_cx-rr, ring_cy-rr, ring_cx+rr, ring_cy+rr], outline=(247, 147, 26, alpha), width=4)
    # 中心₿ 标志
    draw_bitcoin_b(canvas, ring_cx, ring_cy - 50, 56)
    # 站名（中）
    name_font = get_font(72, bold=True, song=True)
    # 居中（用 textbbox 算宽）
    bbox = d.textbbox((0, 0), st["name"], font=name_font)
    name_w = bbox[2] - bbox[0]
    d.text((ring_cx - name_w//2, ring_cy + 30), st["name"], fill=WARM_WHITE, font=name_font)
    # 英文名
    en_font = get_font(28, bold=True)
    bbox2 = d.textbbox((0, 0), st["en"], font=en_font)
    en_w = bbox2[2] - bbox2[0]
    d.text((ring_cx - en_w//2, ring_cy + 130), st["en"], fill=BTC_ORANGE, font=en_font)

    # ===== 元素 5+6：大标题 + 副标题（左下） =====
    title_font = get_font(64, bold=True)
    d.text((60, H-260), title, fill=WARM_WHITE, font=title_font)
    sub_font = get_font(28, bold=False)
    d.text((60, H-160), subtitle, fill=WARM_WHITE, font=sub_font)

    # ===== 元素 7：站号 badge（右下） =====
    badge_text = f"站 {station_id}"
    badge_font = get_font(28, bold=True)
    bbox3 = d.textbbox((0, 0), badge_text, font=badge_font)
    bw, bh = bbox3[2]-bbox3[0]+40, bbox3[3]-bbox3[1]+20
    bx, by = W - bw - 40, H - bh - 40
    d.rounded_rectangle([bx, by, bx+bw, by+bh], radius=12, fill=DARK, outline=BTC_ORANGE, width=2)
    d.text((bx+20, by+10), badge_text, fill=WARM_WHITE, font=badge_font)

    # 保存
    canvas.convert("RGB").save(output_path, quality=95)
    print(f"✅ 封面已生成: {output_path}  ({W}x{H})")


# ============== map-figure 9 张共享底图 + 高亮环 ==============
def make_map_figure(base_path, station_id, output_path, target_size=(1100, 1466)):
    """map-figure = P1-v4 完整底图 + 当前站黄金高亮环 + 站名放大。
    9 张共用同一张底图。"""
    st = STATION_COORDS[station_id]
    bg = Image.open(base_path).convert("RGBA")
    # 等比缩到目标尺寸
    bg.thumbnail(target_size, Image.LANCZOS)
    canvas = bg.copy()
    d = ImageDraw.Draw(canvas)
    W, H = canvas.size
    # 把 P1-v4 原图坐标按缩放比换算
    src_w, src_h = 1440, 1920
    sx, sy = W/src_w, H/src_h
    cx, cy = int(st["x"]*sx), int(st["y"]*sy)

    # 边缘站 clamp：保证高亮环(r=110)+柔光(r=140)+站名标签(下方~202px)全部落在画布内
    ring_r, glow_r, label_down, margin = 110, 140, 210, 24
    cx = clamp(cx, margin + ring_r, W - margin - ring_r)
    cy = clamp(cy, margin + glow_r, H - margin - label_down)

    # 高亮环：3 道金环（细到粗），外加一层柔光
    # 柔光层
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for r_g in range(140, 70, -3):
        a = int(40 * (r_g-70)/70)
        gd.ellipse([cx-r_g, cy-r_g, cx+r_g, cy+r_g], fill=(247, 147, 26, a))
    glow = glow.filter(ImageFilter.GaussianBlur(8))
    canvas.alpha_composite(glow)
    d = ImageDraw.Draw(canvas)
    # 3 道金环
    for r, w in [(110, 3), (90, 4), (70, 5)]:
        d.ellipse([cx-r, cy-r, cx+r, cy+r], outline=BTC_ORANGE, width=w)
    # 中心₿ 标志
    draw_bitcoin_b(canvas, cx, cy, 38)
    # 站名大字号 + 描边（在环下方）
    name_font = get_font(56, bold=True, song=True)
    name = st["name"]
    bbox = d.textbbox((0, 0), name, font=name_font)
    nw = bbox[2]-bbox[0]
    tx, ty = cx - nw//2, cy + 130
    # 描边
    for ox, oy in [(-2,0),(2,0),(0,-2),(0,2)]:
        d.text((tx+ox, ty+oy), name, fill=DARK, font=name_font)
    d.text((tx, ty), name, fill=WARM_WHITE, font=name_font)
    # 英文名
    en_font = get_font(22, bold=True)
    en = st["en"]
    bbox2 = d.textbbox((0, 0), en, font=en_font)
    ew = bbox2[2]-bbox2[0]
    d.text((cx-ew//2, ty+72), en, fill=BTC_ORANGE, font=en_font)

    canvas.convert("RGB").save(output_path, quality=95)
    print(f"✅ map-figure 已生成: {output_path}  ({W}x{H})  站{station_id} {name}")


# ============== 配图合成（基础款 — 留作扩展） ==============
def make_concept_image(bg_path, station_id, output_path, concept_title="", subtitle="", crop_box=None):
    """配图通用合成：底图 + 顶部小 logo+站名 + 底部站号 + 中部标题"""
    bg = Image.open(bg_path).convert("RGBA")
    if crop_box:
        bg = bg.crop(crop_box)
    W, H = bg.size
    canvas = bg.copy()
    d = ImageDraw.Draw(canvas)

    # 顶部小 logo
    logo_font = get_font(20, bold=True)
    d.text((30, 20), f"慢读宝盒 · {STATION_COORDS[station_id]['name']}", fill=WARM_WHITE, font=logo_font)
    # 底部站号 badge
    badge_text = f"站 {station_id}"
    badge_font = get_font(20, bold=True)
    bbox = d.textbbox((0, 0), badge_text, font=badge_font)
    bw = bbox[2]-bbox[0]+24
    bh = bbox[3]-bbox[1]+12
    bx, by = W-bw-30, H-bh-30
    d.rounded_rectangle([bx, by, bx+bw, by+bh], radius=8, fill=DARK, outline=BTC_ORANGE, width=2)
    d.text((bx+12, by+6), badge_text, fill=WARM_WHITE, font=badge_font)
    # 中部标题
    if concept_title:
        title_font = get_font(48, bold=True)
        bbox2 = d.textbbox((0, 0), concept_title, font=title_font)
        tw = bbox2[2]-bbox2[0]
        d.text((W//2-tw//2, H-160), concept_title, fill=WARM_WHITE, font=title_font)
    if subtitle:
        sub_font = get_font(22, bold=False)
        bbox3 = d.textbbox((0, 0), subtitle, font=sub_font)
        sw = bbox3[2]-bbox3[0]
        d.text((W//2-sw//2, H-90), subtitle, fill=WARM_WHITE, font=sub_font)

    canvas.convert("RGB").save(output_path, quality=95)
    print(f"✅ 配图已生成: {output_path}  ({W}x{H})")


# ============== 对比表（FT 风格，程序化） ==============
def make_comparison_table(out_path, title, subtitle, columns, rows, takeaway="", station_id="4"):
    """FT 风格对比表：标题即结论 + 直接标签 + 2 列 + 暗红信息编码 + 品牌金箭头。
    columns: ["传统银行", "比特币网络"]
    rows: [(row_name, left_text, right_text), ...] 4 行
    takeaway: 底部一句收束
    """
    W, H = 1280, 960
    canvas = Image.new("RGBA", (W, H), DARK)
    d = ImageDraw.Draw(canvas)

    # 顶部 logo
    logo_font = get_font(20, bold=True)
    d.text((30, 20), f"慢读宝盒 · {STATION_COORDS[station_id]['name']}", fill=WARM_WHITE, font=logo_font)
    # 右上站号 badge
    badge_text = f"站 {station_id}"
    badge_font = get_font(20, bold=True)
    bbox = d.textbbox((0, 0), badge_text, font=badge_font)
    bw = bbox[2]-bbox[0]+24
    bh = 32
    bx, by = W-bw-30, 20
    d.rounded_rectangle([bx, by, bx+bw, by+bh], radius=8, fill=DARK, outline=BTC_ORANGE, width=2)
    d.text((bx+12, by+6), badge_text, fill=WARM_WHITE, font=badge_font)

    # 大标题（标题即结论）
    title_font = get_font(48, bold=True)
    d.text((60, 70), title, fill=WARM_WHITE, font=title_font)
    # 副标题
    sub_font = get_font(22, bold=False)
    d.text((60, 140), subtitle, fill=WARM_WHITE, font=sub_font)
    # 装饰细线
    d.line([(60, 180), (W-60, 180)], fill=ANTIQUE_GOLD, width=1)

    # 列头
    col_header_y = 220
    col_left_x = 60
    col_right_x = W//2 + 60
    head_font = get_font(32, bold=True)
    bbox_l = d.textbbox((0,0), columns[0], font=head_font)
    d.text((col_left_x, col_header_y), columns[0], fill=(120, 120, 120), font=head_font)
    bbox_r = d.textbbox((0,0), columns[1], font=head_font)
    d.text((W - 60 - (bbox_r[2]-bbox_r[0]), col_header_y), columns[1], fill=BTC_ORANGE, font=head_font)

    # 行
    row_h = 130
    start_y = 300
    for i, (row_name, left_text, right_text) in enumerate(rows):
        y = start_y + i * row_h
        # 分隔线
        d.line([(60, y - 5), (W-60, y-5)], fill=(60, 60, 60), width=1)
        # 行名（左对齐，红色）
        row_font = get_font(28, bold=True)
        d.text((col_left_x, y + 35), row_name, fill=ALERT_RED, font=row_font)
        # 左列内容
        text_font = get_font(26, bold=False)
        d.text((col_left_x + 180, y + 40), left_text, fill=(180, 180, 180), font=text_font)
        # 右列：暖白文字，右对齐
        bbox_rt = d.textbbox((0,0), right_text, font=text_font)
        rt_w = bbox_rt[2] - bbox_rt[0]
        d.text((W - 60 - rt_w, y + 40), right_text, fill=WARM_WHITE, font=text_font)

    # 底部 takeaway
    if takeaway:
        take_font = get_font(22, bold=True)
        d.text((60, H - 80), takeaway, fill=BTC_ORANGE, font=take_font)

    canvas.convert("RGB").save(out_path, quality=95)
    print(f"✅ 对比表已生成: {out_path}")


if __name__ == "__main__":
    print("brand-kit loaded.  示例调用见 README。")
