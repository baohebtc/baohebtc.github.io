#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""封面试点：对比「带文字 v5 整图」vs「无文字 0822 base 整图」做 9 站单站封面底图。
复用 brand-kit 的 ₿ 程序化 + tokens。输出到 /tmp/cover-pilot/，不污染正式 assets。
"""
import importlib.util, os
from PIL import Image, ImageDraw, ImageFilter

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
spec = importlib.util.spec_from_file_location("brandkit", os.path.join(REPO, "tools/dev/brand-kit.py"))
bk = importlib.util.module_from_spec(spec); spec.loader.exec_module(bk)

OUT = "/tmp/cover-pilot"
os.makedirs(OUT, exist_ok=True)
NORM = (1440, 1920)  # STATION_COORDS 基准坐标系

V5   = os.path.join(REPO, "assets/比特币学习地图/比特币学习地图-P1-0822-可灵版-9站-v5.png")
BASE = os.path.join(REPO, "assets/比特币学习地图/P1-0822-base-720.png")

TITLES = {
    "4": ("账本海", "一张公开的账本，全网共同记账"),
}

def _load_norm(bg_path):
    """统一归一化到 1440×1920（STATION_COORDS 基准）。"""
    return Image.open(bg_path).convert("RGBA").resize(NORM, Image.LANCZOS)

def make_cover_v2(bg_path, station_id, out_path, target=(1440, 1920)):
    st = bk.STATION_COORDS[station_id]
    name, sub = TITLES[station_id]
    bg = _load_norm(bg_path)
    W, H = target
    canvas = bg.copy()
    d = ImageDraw.Draw(canvas)

    # 暗化蒙版（顶部 logo+图例 / 底部 标题+副标题+站号）
    od = ImageDraw.Draw(canvas)
    od.rectangle([0, 0, W, 150], fill=(0, 0, 0, 120))
    od.rectangle([0, H-340, W, H], fill=(0, 0, 0, 150))
    od.rectangle([0, H-340, int(W*0.65), H], fill=(0, 0, 0, 80))

    # 元素1：logo（左上）
    d.text((40, 45), "慢读宝盒", fill=bk.WARM_WHITE, font=bk.get_font(34, bold=True))
    # 元素2：图例（右上）
    d.text((W-260, 45), "六视角 · 读懂比特币", fill=bk.WARM_WHITE, font=bk.get_font(15))
    lx, ly = W-260, 72
    for i, (nm, col) in enumerate(bk.VIEW_COLORS):
        cx = lx + i*42 + 8; cy = ly + 6
        d.ellipse([cx-5, cy-5, cx+5, cy+5], fill=col)
        d.text((cx+10, cy-7), nm, fill=bk.WARM_WHITE, font=bk.get_font(13))

    # 高亮环：定位到「该站」坐标（基准系）
    hx, hy = st["x"], st["y"]
    hx = max(160, min(W-160, hx)); hy = max(210, min(H-210, hy))
    for rr, al in [(110, 230), (128, 180), (146, 140)]:
        d.ellipse([hx-rr, hy-rr, hx+rr, hy+rr], outline=(247, 147, 26, al), width=4)
    bk.draw_bitcoin_b(canvas, hx, hy, 34)
    # 站名标签（环下方）
    nf = bk.get_font(42, bold=True, song=True)
    bb = d.textbbox((0,0), st["name"], font=nf); nw = bb[2]-bb[0]
    d.text((hx-nw//2, hy+118), st["name"], fill=bk.WARM_WHITE, font=nf)
    ef = bk.get_font(18, bold=True)
    bb2 = d.textbbox((0,0), st["en"], font=ef); ew = bb2[2]-bb2[0]
    d.text((hx-ew//2, hy+174), st["en"], fill=bk.BTC_ORANGE, font=ef)

    # 元素5+6：大标题 + 副标题（底部）
    d.text((60, H-250), name, fill=bk.WARM_WHITE, font=bk.get_font(58, bold=True))
    d.text((60, H-160), sub, fill=bk.WARM_WHITE, font=bk.get_font(26))
    # 元素7：站号 badge（右下）
    bt = f"站 {station_id}"; bf = bk.get_font(26, bold=True)
    bb3 = d.textbbox((0,0), bt, font=bf); bwid = bb3[2]-bb3[0]+40; bhid = bb3[3]-bb3[1]+20
    bx, by = W-bwid-40, H-bhid-40
    d.rounded_rectangle([bx, by, bx+bwid, by+bhid], radius=12, fill=(13,13,13), outline=bk.BTC_ORANGE, width=2)
    d.text((bx+20, by+10), bt, fill=bk.WARM_WHITE, font=bf)

    if (W, H) != NORM:
        canvas = canvas.resize((W, H), Image.LANCZOS)
    canvas.convert("RGB").save(out_path, quality=95)
    print(f"✅ {out_path}  ({W}x{H})  ring@norm({st['x']},{st['y']})")

def make_headline(bg_path, station_id, out_path, target=(900, 383)):
    """微信头条封面 900×383 (2.35:1)。从 norm 整图取中间横条适配。"""
    st = bk.STATION_COORDS[station_id]
    name, sub = TITLES[station_id]
    bg = _load_norm(bg_path)
    W, H = target
    crop_h = int(NORM[1] * 0.34)
    top = (NORM[1] - crop_h) // 2
    bg = bg.crop((0, top, NORM[0], top+crop_h)).resize(target, Image.LANCZOS)
    canvas = bg.copy()
    d = ImageDraw.Draw(canvas)
    d.rectangle([0,0,W,70], fill=(0,0,0,110))
    d.rectangle([0,H-120,W,H], fill=(0,0,0,140))
    d.text((24, 18), "慢读宝盒", fill=bk.WARM_WHITE, font=bk.get_font(22, bold=True))
    hx = int(st["x"] * W / NORM[0])
    hy = int((st["y"] - top) * H / crop_h)
    hy = max(80, min(H-80, hy))
    for rr, al in [(60, 230), (74, 170), (88, 120)]:
        d.ellipse([hx-rr, hy-rr, hx+rr, hy+rr], outline=(247,147,26,al), width=3)
    bk.draw_bitcoin_b(canvas, hx, hy, 20)
    nf = bk.get_font(30, bold=True, song=True)
    bb = d.textbbox((0,0), st["name"], font=nf); nw = bb[2]-bb[0]
    d.text((hx-nw//2, hy+58), st["name"], fill=bk.WARM_WHITE, font=nf)
    d.text((24, H-70), sub, fill=bk.WARM_WHITE, font=bk.get_font(18))
    bt = f"站 {station_id}"; bf = bk.get_font(18, bold=True)
    bb3 = d.textbbox((0,0), bt, font=bf); bwid = bb3[2]-bb3[0]+28
    d.rounded_rectangle([W-bwid-20, H-52, W-20, H-20], radius=8, fill=(13,13,13), outline=bk.BTC_ORANGE, width=2)
    d.text((W-bwid-6, H-46), bt, fill=bk.WARM_WHITE, font=bf)
    canvas.convert("RGB").save(out_path, quality=95)
    print(f"✅ {out_path}  ({W}x{H})  ring@({hx},{hy})")

if __name__ == "__main__":
    make_cover_v2(V5,   "4", f"{OUT}/pilot-v5-站4-1440.png",   target=(1440,1920))
    make_cover_v2(BASE, "4", f"{OUT}/pilot-base-站4-1440.png", target=(1440,1920))
    make_headline(V5,  "4", f"{OUT}/pilot-v5-站4-900headline.png", target=(900,383))
