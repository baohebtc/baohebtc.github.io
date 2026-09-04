#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""5 个新封面模板：程序化官方 ₿（draw_bitcoin_b，100% 国际同步）+ 极简 6 元素。
底图：在可灵P1提示词生成好原图0822.PNG
字徽：brand-kit.draw_bitcoin_b（程序化官方 ₿）
尺寸：微信头条 900×383
全部用站 4 演示
"""
import importlib.util, os, sys
from PIL import Image, ImageDraw

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
spec = importlib.util.spec_from_file_location("brandkit", os.path.join(REPO, "tools/dev/brand-kit.py"))
bk = importlib.util.module_from_spec(spec); spec.loader.exec_module(bk)

ORIG = os.path.join(REPO, "assets/比特币学习地图/在可灵P1提示词生成好原图0822.PNG")
OUT = "/tmp/template-pilot"
os.makedirs(OUT, exist_ok=True)
NORM = (1440, 1920)

SUBS = {
    "4": "一张公开的账本，全网共同记账",
}

def load_bg():
    return Image.open(ORIG).convert("RGBA").resize(NORM, Image.LANCZOS)

def crop_around(bg, cx, cy, ratio):
    """以 (cx,cy) 为中心按 ratio 裁矩形，clamp 进 1440×1920。"""
    W, H = NORM
    cw, ch = W, int(W / ratio)
    if ch > H: ch, cw = H, int(H * ratio)
    x0 = max(0, min(W - cw, cx - cw // 2))
    y0 = max(0, min(H - ch, cy - ch // 2))
    return bg.crop((x0, y0, x0 + cw, y0 + ch))

def draw_emblem(canvas, cx, cy, r, with_ring=True):
    """程序化官方 ₿ + 可选金环"""
    if with_ring:
        for rr, al in [(int(r*1.45), 220), (int(r*1.85), 140)]:
            ImageDraw.Draw(canvas).ellipse(
                [cx-rr, cy-rr, cx+rr, cy+rr], outline=(247, 147, 26, al), width=2)
    bk.draw_bitcoin_b(canvas, cx, cy, r)

# ========== 模板 T1：极简居中 ==========
def t1_minimal_center(bg, station_id, out_path):
    st = bk.STATION_COORDS[station_id]
    sub = SUBS[station_id]
    crop = crop_around(bg, st["x"], st["y"], 900/383)
    img = crop.resize((900, 383), Image.LANCZOS).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 900, 60], fill=(0, 0, 0, 110))
    d.rectangle([0, 280, 900, 383], fill=(0, 0, 0, 140))
    # logo
    d.text((20, 14), "慢读宝盒", fill=bk.WARM_WHITE,
           font=bk.get_font(18, bold=True))
    # 中央字徽
    draw_emblem(img, 450, 165, 42)
    # 站名 + 站号（上移避开底部暗化）
    nf = bk.get_font(26, bold=True, song=True)
    bb = d.textbbox((0,0), st["name"], font=nf); nw = bb[2]-bb[0]
    d.text((450-nw//2, 208), st["name"], fill=bk.WARM_WHITE, font=nf)
    es = f"站 {station_id}  ·  {st['en']}"
    ef = bk.get_font(12, bold=True)
    bb2 = d.textbbox((0,0), es, font=ef); ew = bb2[2]-bb2[0]
    d.text((450-ew//2, 238), es, fill=bk.BTC_ORANGE, font=ef)
    # 副标题
    sf = bk.get_font(14)
    bb3 = d.textbbox((0,0), sub, font=sf); sw_ = bb3[2]-bb3[0]
    d.text((450-sw_//2, 320), sub, fill=bk.WARM_WHITE, font=sf)
    img.convert("RGB").save(out_path, quality=95)
    print(f"✅ T1  {out_path}")

# ========== 模板 T2：左字右图 ==========
def t2_left_text_right_emblem(bg, station_id, out_path):
    st = bk.STATION_COORDS[station_id]
    sub = SUBS[station_id]
    crop = crop_around(bg, st["x"], st["y"], 900/383)
    img = crop.resize((900, 383), Image.LANCZOS).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 900, 50], fill=(0, 0, 0, 110))
    d.rectangle([0, 290, 900, 383], fill=(0, 0, 0, 150))
    d.rectangle([0, 60, 600, 290], fill=(0, 0, 0, 70))  # 左侧暗化
    d.text((20, 14), "慢读宝盒", fill=bk.WARM_WHITE,
           font=bk.get_font(18, bold=True))
    # 左侧文字
    d.text((40, 100), f"站 {station_id}", fill=bk.BTC_ORANGE,
           font=bk.get_font(16, bold=True))
    d.text((40, 130), st["name"], fill=bk.WARM_WHITE,
           font=bk.get_font(34, bold=True, song=True))
    d.text((42, 175), st["en"], fill=bk.WARM_WHITE,
           font=bk.get_font(13, bold=True))
    d.text((40, 220), sub, fill=bk.WARM_WHITE,
           font=bk.get_font(15))
    # 右侧字徽（居中靠右，确保不被裁切）
    draw_emblem(img, 750, 200, 50)
    img.convert("RGB").save(out_path, quality=95)
    print(f"✅ T2  {out_path}")

# ========== 模板 T3：上下分层（字徽顶 + 信息底） ==========
def t3_top_emblem_bottom_info(bg, station_id, out_path):
    st = bk.STATION_COORDS[station_id]
    sub = SUBS[station_id]
    crop = crop_around(bg, st["x"], st["y"], 900/383)
    img = crop.resize((900, 383), Image.LANCZOS).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 900, 50], fill=(0, 0, 0, 110))
    d.rectangle([0, 250, 900, 383], fill=(0, 0, 0, 150))
    d.text((20, 14), "慢读宝盒", fill=bk.WARM_WHITE,
           font=bk.get_font(18, bold=True))
    # 顶部中央字徽
    draw_emblem(img, 450, 145, 38)
    # 底部信息
    es = f"站 {station_id}"
    d.text((40, 275), es, fill=bk.BTC_ORANGE,
           font=bk.get_font(14, bold=True))
    d.text((100, 270), st["name"], fill=bk.WARM_WHITE,
           font=bk.get_font(30, bold=True, song=True))
    d.text((40, 315), sub, fill=bk.WARM_WHITE, font=bk.get_font(16))
    d.text((40, 345), st["en"], fill=bk.BTC_ORANGE,
           font=bk.get_font(12, bold=True))
    img.convert("RGB").save(out_path, quality=95)
    print(f"✅ T3  {out_path}")

# ========== 模板 T4：方形全宽（字徽大 + 站名大字居中） ==========
def t4_emblem_centered(bg, station_id, out_path):
    st = bk.STATION_COORDS[station_id]
    sub = SUBS[station_id]
    crop = crop_around(bg, st["x"], st["y"], 900/383)
    img = crop.resize((900, 383), Image.LANCZOS).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 900, 50], fill=(0, 0, 0, 110))
    d.rectangle([0, 290, 900, 383], fill=(0, 0, 0, 150))
    d.text((20, 14), "慢读宝盒", fill=bk.WARM_WHITE,
           font=bk.get_font(18, bold=True))
    # 居中字徽（更大）
    draw_emblem(img, 450, 180, 55)
    # 站名
    nf = bk.get_font(28, bold=True, song=True)
    bb = d.textbbox((0,0), st["name"], font=nf); nw = bb[2]-bb[0]
    d.text((450-nw//2, 245), st["name"], fill=bk.WARM_WHITE, font=nf)
    es = f"STATION {station_id}  ·  {st['en']}"
    ef = bk.get_font(11, bold=True)
    bb2 = d.textbbox((0,0), es, font=ef); ew = bb2[2]-bb2[0]
    d.text((450-ew//2, 275), es, fill=bk.BTC_ORANGE, font=ef)
    # 副标题
    sf = bk.get_font(13)
    bb3 = d.textbbox((0,0), sub, font=sf); sw_ = bb3[2]-bb3[0]
    d.text((450-sw_//2, 330), sub, fill=bk.WARM_WHITE, font=sf)
    img.convert("RGB").save(out_path, quality=95)
    print(f"✅ T4  {out_path}")

# ========== 模板 T5：徽章+分隔线（最有"系列地图"感） ==========
def t5_emblem_station_below(bg, station_id, out_path):
    st = bk.STATION_COORDS[station_id]
    sub = SUBS[station_id]
    crop = crop_around(bg, st["x"], st["y"], 900/383)
    img = crop.resize((900, 383), Image.LANCZOS).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 900, 50], fill=(0, 0, 0, 110))
    d.rectangle([0, 260, 900, 383], fill=(0, 0, 0, 160))
    d.text((20, 14), "慢读宝盒", fill=bk.WARM_WHITE,
           font=bk.get_font(18, bold=True))
    # 大字徽
    draw_emblem(img, 450, 150, 50)
    # 分隔线
    d.line([(280, 245), (620, 245)], fill=bk.BTC_ORANGE, width=1)
    # 站名
    nf = bk.get_font(26, bold=True, song=True)
    bb = d.textbbox((0,0), st["name"], font=nf); nw = bb[2]-bb[0]
    d.text((450-nw//2, 245), st["name"], fill=bk.WARM_WHITE, font=nf)
    # 副标题 + 站号横排
    es = f"站 {station_id}  ·  {sub}"
    ef = bk.get_font(12)
    bb2 = d.textbbox((0,0), es, font=ef); ew = bb2[2]-bb2[0]
    d.text((450-ew//2, 335), es, fill=bk.WARM_WHITE, font=ef)
    img.convert("RGB").save(out_path, quality=95)
    print(f"✅ T5  {out_path}")

if __name__ == "__main__":
    bg = load_bg()
    t1_minimal_center(bg, "4", f"{OUT}/T1-极简居中.png")
    t2_left_text_right_emblem(bg, "4", f"{OUT}/T2-左字右图.png")
    t3_top_emblem_bottom_info(bg, "4", f"{OUT}/T3-上下分层.png")
    t4_emblem_centered(bg, "4", f"{OUT}/T4-字徽大居中.png")
    t5_emblem_station_below(bg, "4", f"{OUT}/T5-徽章分隔线.png")
