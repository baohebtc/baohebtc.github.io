#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""封面对比矩阵：底图 A(v5带文字) vs B(原图无文字高清) × 版式(整图/裁切竖版/微信头条)。
统一用站4（试点站），6 元素模板（规范§五），₿ 程序化。输出到 /tmp/cover-compare/
"""
import importlib.util, os
from PIL import Image, ImageDraw

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
spec = importlib.util.spec_from_file_location("brandkit", os.path.join(REPO, "tools/dev/brand-kit.py"))
bk = importlib.util.module_from_spec(spec); spec.loader.exec_module(bk)

OUT = "/tmp/cover-compare"
os.makedirs(OUT, exist_ok=True)
NORM = (1440, 1920)  # STATION_COORDS 基准坐标系

# 底图候选
A_V5   = os.path.join(REPO, "assets/比特币学习地图/比特币学习地图-P1-0822-可灵版-9站-v5.png")
B_ORIG = os.path.join(REPO, "assets/比特币学习地图/在可灵P1提示词生成好原图0822.PNG")

TITLES = {"4": ("账本海", "一张公开的账本，全网共同记账")}

def load_norm(path):
    """加载底图并归一化到 1440×1920 基准系（STATION_COORDS 基准）。"""
    return Image.open(path).convert("RGBA").resize(NORM, Image.LANCZOS)

def crop_around(bg, cx, cy, ratio, target):
    """以 (cx,cy) 为中心，按 ratio 裁切最大矩形（clamp 进画布），再 resize 到 target。"""
    W, H = NORM
    cw, ch = W, int(W / ratio)
    if ch > H:
        ch, cw = H, int(H * ratio)
    x0 = max(0, min(W - cw, cx - cw // 2))
    y0 = max(0, min(H - ch, cy - ch // 2))
    return bg.crop((x0, y0, x0 + cw, y0 + ch)).resize(target, Image.LANCZOS), x0, y0, cw, ch

def draw_six(img, station_id, mode):
    """6+1 元素模板（规范§五）。mode: 'full'整图 | 'crop'裁切竖版 | 'head'微信头条"""
    st = bk.STATION_COORDS[station_id]
    name, sub = TITLES[station_id]
    W, H = img.size
    d = ImageDraw.Draw(img)
    small = (mode == "head")   # 头条版空间小，字号/元素等比缩小

    # 元素3：底图（已是 img）；暗化蒙版保证文字可读
    top_h   = int(H * (0.075 if small else 0.078))
    bot_h   = int(H * (0.30 if small else 0.177))
    d.rectangle([0, 0, W, top_h], fill=(0, 0, 0, 120))
    d.rectangle([0, H - bot_h, W, H], fill=(0, 0, 0, 150))
    d.rectangle([0, H - bot_h, int(W * 0.65), H], fill=(0, 0, 0, 80))

    s = 0.55 if small else 1.0   # 全局缩放系数
    def F(px, **kw): return bk.get_font(max(8, int(px * s)), **kw)

    # 元素1：logo（左上）
    d.text((int(28*s), int(20*s)), "慢读宝盒", fill=bk.WARM_WHITE, font=F(34, bold=True))
    # 元素2：视角图例（右上）
    lg = "六视角 · 读懂比特币"
    lgf = F(15)
    bb = d.textbbox((0,0), lg, font=lgf); lwid = bb[2]-bb[0]
    d.text((W - lwid - int(28*s), int(20*s)), lg, fill=bk.WARM_WHITE, font=lgf)
    dot_y = int(48*s)
    for i, (nm, col) in enumerate(bk.VIEW_COLORS):
        cx = W - lwid - int(28*s) + i * int(42*s) + int(8*s)
        r = max(3, int(5*s))
        d.ellipse([cx-r, dot_y-r, cx+r, dot_y+r], fill=col)
        d.text((cx + int(10*s), dot_y - int(7*s)), nm, fill=bk.WARM_WHITE, font=F(13))

    # 元素4：站名标（黄金高亮环 + 程序化 ₿ + 站名 + 英文名）
    if mode == "head":
        hx, hy = W // 2, int(H * 0.46)          # 头条：高亮环居中（383 安全区）
    elif mode == "crop":
        hx, hy = W // 2, int(H * 0.42)          # 裁切竖版：环在中心
    else:
        hx, hy = st["x"], st["y"]               # 整图：环落在该站真实坐标
    rings = [(110,230),(128,180),(146,140)] if not small else [(58,230),(70,175),(84,130)]
    for rr, al in rings:
        rr = int(rr * s)
        d.ellipse([hx-rr, hy-rr, hx+rr, hy+rr], outline=(247,147,26,al), width=max(2,int(4*s)))
    bk.draw_bitcoin_b(img, hx, hy, int(34*s) if not small else int(22*s))
    nf = F(42, bold=True, song=True)
    bb = d.textbbox((0,0), st["name"], font=nf); nw = bb[2]-bb[0]
    d.text((hx - nw//2, hy + int(70*s)), st["name"], fill=bk.WARM_WHITE, font=nf)
    ef = F(18, bold=True)
    bb2 = d.textbbox((0,0), st["en"], font=ef); ew = bb2[2]-bb2[0]
    d.text((hx - ew//2, hy + int(108*s)), st["en"], fill=bk.BTC_ORANGE, font=ef)

    # 元素5+6：大标题 + 副标题（左下 / 底部）
    d.text((int(40*s), H - int(150*s)), name, fill=bk.WARM_WHITE, font=F(58, bold=True))
    d.text((int(40*s), H - int(78*s)),  sub,  fill=bk.WARM_WHITE, font=F(26))
    # 元素7：站号 badge（右下）
    bt = f"站 {station_id}"; bf = F(26, bold=True)
    bb3 = d.textbbox((0,0), bt, font=bf); bwid = bb3[2]-bb3[0] + int(40*s); bhid = bb3[3]-bb3[1] + int(20*s)
    bx, by = W - bwid - int(28*s), H - bhid - int(28*s)
    d.rounded_rectangle([bx, by, bx+bwid, by+bhid], radius=int(12*s),
                        fill=(13,13,13), outline=bk.BTC_ORANGE, width=max(1,int(2*s)))
    d.text((bx + int(20*s), by + int(10*s)), bt, fill=bk.WARM_WHITE, font=bf)
    return img

def make(bg_path, station_id, out_path, mode, target):
    st = bk.STATION_COORDS[station_id]
    bg = load_norm(bg_path)
    if mode == "full":
        img = bg.resize(target, Image.LANCZOS)
    elif mode == "crop":
        ratio = target[0] / target[1]
        img, *_ = crop_around(bg, st["x"], st["y"], ratio, target)
    else:  # head
        ratio = target[0] / target[1]
        img, *_ = crop_around(bg, st["x"], st["y"], ratio, target)
    img = draw_six(img, station_id, mode)
    img.convert("RGB").save(out_path, quality=95)
    print(f"✅ {os.path.basename(out_path):44s} {target[0]}x{target[1]}  mode={mode}")

if __name__ == "__main__":
    SID = "4"
    make(A_V5,   SID, f"{OUT}/A1-v5-整图竖版-1440x1920.png",   "full", (1440,1920))
    make(A_V5,   SID, f"{OUT}/A2-v5-站4裁切竖版-1080x1440.png", "crop", (1080,1440))
    make(A_V5,   SID, f"{OUT}/A3-v5-微信头条-900x383.png",      "head", (900,383))
    make(B_ORIG, SID, f"{OUT}/B1-原图-整图竖版-1440x1920.png",   "full", (1440,1920))
    make(B_ORIG, SID, f"{OUT}/B2-原图-站4裁切竖版-1080x1440.png", "crop", (1080,1440))
    make(B_ORIG, SID, f"{OUT}/B3-原图-微信头条-900x383.png",      "head", (900,383))
