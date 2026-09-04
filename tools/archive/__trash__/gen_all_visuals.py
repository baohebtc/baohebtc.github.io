#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
慢读宝盒 · 视觉批量生成器 v1.0
================================
基于 brand-kit.py（design tokens 可执行实现）批量产出：
  A. 9 站 map-figure（P1-v4 底图 + 校准坐标 + 程序化 ₿）
  B. 站1/2/3/4 封面（6 元素 + P1-v4 裁切 + 程序化 ₿ + medallion）
  C. 站4 配图 01-07（程序化信息图，全部品牌一致）

用法：
  python3 tools/dev/gen_all_visuals.py [map|cover|station4|all]
"""
import os
import importlib.util

BASE = "/Users/mac/Desktop/宝盒知识库/比特币学习地图"
MAP_BASE = os.path.join(BASE, "assets/比特币学习地图/比特币学习地图-P1-可灵版-9站-v4.png")
ART = os.path.join(BASE, "assets/articles/公众号")
COVER_DIR = os.path.join(BASE, "assets/cover")

# ---- 动态加载 brand-kit（文件名带连字符，无法 import）----
spec = importlib.util.spec_from_file_location(
    "brandkit", os.path.join(BASE, "tools/dev/brand-kit.py"))
bk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bk)

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

# 复用 brand-kit 的 tokens / 函数
SAND, TERRAIN, BTC_ORANGE = bk.SAND, bk.TERRAIN, bk.BTC_ORANGE
WARM_WHITE, DARK, CARD_DARK = bk.WARM_WHITE, bk.DARK, bk.CARD_DARK
ANTIQUE_GOLD, ALERT_RED = bk.ANTIQUE_GOLD, bk.ALERT_RED
TRUST_GREEN, WISDOM_VIOLET = bk.TRUST_GREEN, bk.WISDOM_VIOLET
STATION_COORDS = bk.STATION_COORDS
get_font = bk.get_font
draw_bitcoin_b = bk.draw_bitcoin_b
clamp = bk.clamp

FONT_MONO = "/System/Library/Fonts/Menlo.ttc"

def fmono(size):
    if os.path.exists(FONT_MONO):
        return ImageFont.truetype(FONT_MONO, size)
    return get_font(size)

def text_w(d, txt, fnt):
    b = d.textbbox((0, 0), txt, font=fnt)
    return b[2]-b[0], b[3]-b[1]

def dashed_line(d, p0, p1, dash=10, gap=8, **kw):
    import math
    x0, y0 = p0; x1, y1 = p1
    dist = math.hypot(x1-x0, y1-y0)
    if dist == 0:
        return
    steps = int(dist // (dash+gap))
    ux, uy = (x1-x0)/dist, (y1-y0)/dist
    for i in range(steps+1):
        s = i*(dash+gap)
        e = min(s+dash, dist)
        d.line([(x0+ux*s, y0+uy*s), (x0+ux*e, y0+uy*e)], **kw)

# 站 → 文章文件夹
FOLDERS = {
    "1": "站1-现金湾", "1.5": "站1.5-钱到底是什么", "2": "站2-银行堡-货币三大缺陷",
    "3": "站3-双花峡-双花难题", "4": "站4-账本海", "5": "站5-哈希岭",
    "6": "站6-共识峰", "7": "站7-矿工谷", "8": "站8-私钥崖", "9": "站9-代码之巅",
}


# ============================================================
# A. MAP-FIGURE（9 站）
# ============================================================
def gen_map_figures():
    print("\n===== A. MAP-FIGURE =====")
    # 9 站（含 1.5）
    for sid in ["1", "1.5", "2", "3", "4", "5", "6", "7", "8", "9"]:
        folder = FOLDERS[sid]
        out_dir = os.path.join(ART, folder)
        os.makedirs(out_dir, exist_ok=True)
        out = os.path.join(out_dir, "map-figure.png")
        bk.make_map_figure(MAP_BASE, sid, out, target_size=(1100, 1466))


# ============================================================
# B. COVERS（站1/2/3/4）
# ============================================================
def cover_spec(sid, win_w=900, win_h=1460, src_w=1440, src_h=1920):
    st = STATION_COORDS[sid]
    sx, sy = st["x"], st["y"]
    cl = clamp(sx - win_w//2, 0, src_w - win_w)
    ct = clamp(sy - win_h//2, 0, src_h - win_h)
    crop = (cl, ct, cl+win_w, ct+win_h)
    hx = (sx - cl) * 1440/win_w
    hy = (sy - ct) * 1920/win_h
    return crop, (int(hx), int(hy))

COVER_SPECS = {
    "1":   ("什么是比特币？", "一张学习地图，看懂比特币的来路"),
    "2":   ("货币的三大缺陷", "银行为什么没能守住你的钱"),
    "3":   ("双花难题", "没有银行，怎么防止一笔钱花两次"),
    "4":   ("账本海", "一张公开的账本，整个网络的共识"),
}

def gen_covers():
    print("\n===== B. COVERS =====")
    for sid, (title, subtitle) in COVER_SPECS.items():
        crop, hl = cover_spec(sid)
        name = STATION_COORDS[sid]["name"]
        out = os.path.join(COVER_DIR, f"封面-{name}.png")
        bk.make_cover(MAP_BASE, sid, title, subtitle, out,
                      crop_box=crop, crop_w=1440, crop_h=1920, highlight_pos=hl)


# ============================================================
# C. 站4 配图 01-07（程序化信息图）
# ============================================================
def _frame(canvas, d, sid, no, W, H):
    """统一边框：左上品牌 tag + 右下 badge"""
    f = get_font(20, bold=True)
    d.text((30, 22), f"慢读宝盒 · {STATION_COORDS[sid]['name']}", fill=WARM_WHITE, font=f)
    btxt = f"站 {sid} · {no:02d}"
    bf = get_font(20, bold=True)
    bw, bh = text_w(d, btxt, bf)
    bx, by = W - bw - 50, H - bh - 28
    d.rounded_rectangle([bx-14, by-8, bx+bw+14, by+bh+8], radius=10,
                        fill=(13,13,13,210), outline=BTC_ORANGE, width=2)
    d.text((bx, by), btxt, fill=WARM_WHITE, font=bf)

def _title(canvas, d, cn, en, W, H, y=None):
    y = y or (H - 120)
    fc = get_font(44, bold=True, song=True)
    fw = get_font(22, bold=False)
    cw, _ = text_w(d, cn, fc)
    d.text(((W-cw)//2, y), cn, fill=WARM_WHITE, font=fc)
    ew, _ = text_w(d, en, fw)
    d.text(((W-ew)//2, y+56), en, fill="#FFD8A0", font=fw)

def gen_station4():
    print("\n===== C. 站4 配图 01-07 =====")
    out_dir = os.path.join(ART, FOLDERS["4"])
    os.makedirs(out_dir, exist_ok=True)
    gen_01(os.path.join(out_dir, "01-public-ledger.png"))
    gen_03(os.path.join(out_dir, "03-pseudonym.png"))
    gen_04(os.path.join(out_dir, "04-utxo.png"))
    gen_05(os.path.join(out_dir, "05-append-only.png"))
    gen_07(os.path.join(out_dir, "07-mindmap-summary.png"))


# ---------- 01 公开账本（提升密度）----------
def gen_01(out):
    W, H = 1280, 1280
    img = Image.new("RGB", (W, H), DARK)
    d = ImageDraw.Draw(img)
    # 背景柔光
    glow = Image.new("RGBA", (W, H), (0,0,0,0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W//2-520, H//2-520, W//2+520, H//2+520], fill=(247,147,26,18))
    img.paste(Image.alpha_composite(glow, Image.new("RGBA",(W,H),(0,0,0,0))).convert("RGB"), (0,0))

    cx, cy = W//2, H//2 - 20
    # 全球（橙圈）
    d.ellipse([cx-180, cy-180, cx+180, cy+180], outline=BTC_ORANGE, width=4)
    d.ellipse([cx-150, cy-150, cx+150, cy+150], outline=(139,111,58), width=2)
    # 中心 ₿
    draw_bitcoin_b(img, cx, cy, 70)
    # 8 本账本环绕，金线连到中心，每本带 3 条账目线
    n = 8
    for i in range(n):
        a = 2*np.pi*i/n - np.pi/2
        lx = cx + int(380*np.cos(a)); ly = cy + int(380*np.sin(a))
        # 金线
        d.line([(cx, cy), (lx, ly)], fill=ANTIQUE_GOLD, width=2)
        # 账本矩形
        lw, lh = 120, 150
        lx0, ly0 = lx-lw//2, ly-lh//2
        d.rounded_rectangle([lx0, ly0, lx0+lw, ly0+lh], radius=8, fill=(26,26,26), outline=TERRAIN, width=2)
        # 账目线（密度）
        for k in range(4):
            yy = ly0+22 + k*28
            d.line([(lx0+14, yy), (lx0+lw-14, yy)], fill=(90,80,60), width=2)
        # 右下角微 ₿ 印章
        draw_bitcoin_b(img, lx0+lw-18, ly0+lh-18, 13)
    _title(img, d, "公开账本", "EVERY NODE HOLDS A FULL COPY", W, H, y=H-150)
    _frame(img, d, "4", 1, W, H)
    img.save(out, quality=95)
    print(f"✅ 01: {out}")


# ---------- 03 伪匿名 ----------
def gen_03(out):
    W, H = 1280, 800
    img = Image.new("RGB", (W, H), DARK)
    d = ImageDraw.Draw(img)
    # 左：化名面具
    lx0, ly0, lw, lh = 80, 180, 360, 440
    d.rounded_rectangle([lx0, ly0, lx0+lw, ly0+lh], radius=14, fill=(26,26,26), outline=TRUST_GREEN, width=3)
    fmask = get_font(40, bold=True, song=True)
    d.text((lx0+30, ly0+30), "化名 Pseudonym", fill=TRUST_GREEN, font=fmask)
    # 面具图标（圆+眼缝）
    mx, my = lx0+lw//2, ly0+200
    d.ellipse([mx-70, my-80, mx+70, my+80], fill=(20,40,30), outline=TRUST_GREEN, width=3)
    d.line([(mx-45, my-10), (mx-15, my-10)], fill=TRUST_GREEN, width=4)
    d.line([(mx+15, my-10), (mx+45, my-10)], fill=TRUST_GREEN, width=4)
    # 地址
    fm = fmono(30)
    addr = "bc1q…x7f9k2p"
    aw, _ = text_w(d, addr, fm)
    d.text((lx0+lw//2-aw//2, ly0+lh-90), addr, fill=WARM_WHITE, font=fm)
    # 右：真名身份证
    rx0, ry0, rw, rh = 840, 180, 360, 440
    d.rounded_rectangle([rx0, ry0, rx0+rw, ry0+rh], radius=14, fill=(26,26,26), outline=ALERT_RED, width=3)
    fid = get_font(40, bold=True, song=True)
    d.text((rx0+30, ry0+30), "真名 Real ID", fill=ALERT_RED, font=fid)
    d.rounded_rectangle([rx0+30, ry0+110, rx0+30+110, ry0+110+130], radius=8, fill=(40,40,40), outline=(120,120,120), width=2)
    fn = get_font(30, bold=True)
    d.text((rx0+170, ry0+120), "张三", fill=WARM_WHITE, font=fn)
    d.text((rx0+170, ry0+170), "身份证 5201…", fill="#CFCFCF", font=get_font(22))
    # 中间桥：KYC / 地址复用
    bx0, by0 = lx0+lw+20, H//2-50
    bx1 = rx0-20
    dashed_line(d, (bx0, by0), (bx1, by0), dash=10, gap=8, fill=ANTIQUE_GOLD, width=3)
    fb = get_font(24, bold=True)
    bt = "KYC / 地址复用 → 面具揭开"
    btw, _ = text_w(d, bt, fb)
    d.rectangle([(bx0+bx1)//2-btw//2-14, by0-44, (bx0+bx1)//2+btw//2+14, by0-10], fill=(60,20,20))
    d.text(((bx0+bx1)//2-btw//2, by0-40), bt, fill=ALERT_RED, font=fb)
    _title(img, d, "化名 ≠ 匿名", "地址看得见，真人看不见；KYC 一关联就破", W, H, y=H-120)
    _frame(img, d, "4", 3, W, H)
    img.save(out, quality=95)
    print(f"✅ 03: {out}")


# ---------- 04 UTXO 带锁硬币 ----------
def gen_04(out):
    W, H = 1280, 800
    img = Image.new("RGB", (W, H), DARK)
    d = ImageDraw.Draw(img)
    # 左钱包：3 枚带锁硬币
    def coin(cx, cy, r, label, color):
        d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(30,30,30), outline=color, width=4)
        # 锁
        d.rectangle([cx-10, cy-4, cx+10, cy+12], fill=color)
        d.arc([cx-14, cy-22, cx+14, cy+2], 180, 360, fill=color, width=4)
        fl = get_font(22, bold=True)
        lw, _ = text_w(d, label, fl)
        d.text((cx-lw//2, cy+r+10), label, fill=WARM_WHITE, font=fl)
    coin(180, 250, 60, "0.5", BTC_ORANGE)
    coin(180, 430, 60, "0.3", (139,111,58))
    d.text((180, 540), "你的 UTXO 集", fill="#CFCFCF", font=get_font(22), anchor="mm")
    # 箭头
    d.polygon([(320, 360), (420, 335), (420, 385)], fill=BTC_ORANGE)
    d.line([(330, 360), (415, 360)], fill=BTC_ORANGE, width=4)
    # 中：消费一枚 0.5
    d.ellipse([470, 300, 590, 420], fill=(30,30,30), outline=ALERT_RED, width=4)
    d.line([(478,308),(582,412)], fill=ALERT_RED, width=4)
    d.line([(582,308),(478,412)], fill=ALERT_RED, width=4)
    d.text((530, 430), "花掉 0.5", fill=ALERT_RED, font=get_font(22), anchor="mm")
    d.polygon([(610, 360), (710, 335), (710, 385)], fill=BTC_ORANGE)
    d.line([(620, 360), (705, 360)], fill=BTC_ORANGE, width=4)
    # 右：生成两枚新币
    coin(820, 250, 56, "0.3 → 对方", BTC_ORANGE)
    coin(820, 430, 56, "0.2 → 找零", (139,111,58))
    d.text((820, 540), "旧币销毁，新币生成", fill="#CFCFCF", font=get_font(22), anchor="mm")
    _title(img, d, "没有「余额」，只有带锁硬币", "UTXO：花掉即销毁，找零回新地址", W, H, y=H-120)
    _frame(img, d, "4", 4, W, H)
    img.save(out, quality=95)
    print(f"✅ 04: {out}")


# ---------- 05 只追加 + 指纹锁链 ----------
def gen_05(out):
    W, H = 1280, 800
    img = Image.new("RGB", (W, H), DARK)
    d = ImageDraw.Draw(img)
    # 链：5 页
    pages = [("创世", "0000", False), ("第99页", "a1b2", False),
             ("第100页", "篡改!", True), ("第101页", "—断—", True), ("第102页", "—断—", True)]
    pw, ph, gap = 200, 300, 40
    x0 = 60
    y = 230
    prev_x = None
    for i, (label, hsh, broken) in enumerate(pages):
        px = x0 + i*(pw+gap)
        col = ALERT_RED if broken else (30,30,30)
        outl = ALERT_RED if broken else TERRAIN
        d.rounded_rectangle([px, y, px+pw, y+ph], radius=10, fill=col, outline=outl, width=3)
        # 标题
        ft = get_font(24, bold=True)
        tw, _ = text_w(d, label, ft)
        d.text((px+pw//2-tw//2, y+20), label, fill=(WARM_WHITE if not broken else WARM_WHITE), font=ft)
        # 指纹/哈希
        fh = fmono(20)
        hw, _ = text_w(d, f"hash:{hsh}", fh)
        d.text((px+pw//2-hw//2, y+90), f"hash:{hsh}", fill=("#FFD8A0" if not broken else ALERT_RED), font=fh)
        # prev 指纹（接上一页）
        if i > 0:
            ptxt = "prev: " + pages[i-1][1]
            pw2, _ = text_w(d, ptxt, fh)
            d.text((px+pw//2-pw2//2, y+140), ptxt, fill=("#A0A0A0" if not broken else ALERT_RED), font=fh)
        else:
            d.text((px+pw//2-30, y+140), "prev: —", fill="#A0A0A0", font=fh)
        # 连接箭头（右）
        if i < len(pages)-1:
            ax = px+pw+4
            if broken:
                d.text((ax+8, y+ph//2-14), "✗", fill=ALERT_RED, font=get_font(30, bold=True))
            else:
                d.polygon([(ax, y+ph//2), (ax+gap-6, y+ph//2-12), (ax+gap-6, y+ph//2+12)], fill=BTC_ORANGE)
        if broken:
            d.text((px+pw//2-40, y+ph-40), "链断裂", fill=ALERT_RED, font=get_font(22, bold=True))
    _title(img, d, "改不动：只追加 + 指纹锁链", "改一页→后续指纹全对不上→断裂", W, H, y=H-120)
    _frame(img, d, "4", 5, W, H)
    img.save(out, quality=95)
    print(f"✅ 05: {out}")


# ---------- 07 思维导图（三句话）----------
def gen_07(out):
    W, H = 1280, 720
    img = Image.new("RGB", (W, H), DARK)
    d = ImageDraw.Draw(img)
    cards = [
        ("①", "账本是什么", "全球同步、人人可查的公开碑", BTC_ORANGE),
        ("②", "化名不匿名", "地址≠你；KYC / 复用会揭开", TRUST_GREEN),
        ("③", "改不动", "只追加 + 指纹锁链，改一页全断", ALERT_RED),
    ]
    cw, ch, gap = 380, 380, 40
    x0 = (W - (cw*3+gap*2))//2
    y = 120
    for i, (no, t, sub, col) in enumerate(cards):
        cx = x0 + i*(cw+gap)
        d.rounded_rectangle([cx, y, cx+cw, y+ch], radius=16, fill=(24,24,24), outline=col, width=3)
        # 序号圆
        d.ellipse([cx+30, y+30, cx+90, y+90], fill=col)
        fn = get_font(40, bold=True)
        d.text((cx+60, y+50), no, fill=DARK, font=fn, anchor="mm")
        ft = get_font(36, bold=True, song=True)
        tw, _ = text_w(d, t, ft)
        d.text((cx+cw//2-tw//2, y+130), t, fill=WARM_WHITE, font=ft)
        fs = get_font(24, bold=False)
        sw, _ = text_w(d, sub, fs)
        # 自动换行（按字宽）
        d.text((cx+cw//2-sw//2, y+200), sub, fill="#CFCFCF", font=fs)
        draw_bitcoin_b(img, cx+cw//2, y+ch-70, 30)
    _title(img, d, "三句话带走本篇", "账本海 · 公开却不泄密", W, H, y=H-90)
    _frame(img, d, "4", 7, W, H)
    img.save(out, quality=95)
    print(f"✅ 07: {out}")


if __name__ == "__main__":
    import sys
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("map", "all"):
        gen_map_figures()
    if which in ("cover", "all"):
        gen_covers()
    if which in ("station4", "all"):
        gen_station4()
    print("\n🎉 生成完成。")
