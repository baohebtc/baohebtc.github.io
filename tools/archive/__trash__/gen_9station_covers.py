#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""9 站微信公众号头条封面（900×383），方案 A 整图 + 方案 B 裁切，₿ 用原图抠出的 3D 金色字徽。
- 底图：在可灵P1提示词生成好原图0822.PNG（无文字高清）
- 字徽：assets/brand/btc-emblem-0822.png（RGBA 透明）
- 6 元素模板（规范 §五）
- 微信头条 900×383 (2.35:1)，高亮环落微信 383 安全区 x258~642
"""
import importlib.util, os, sys
from PIL import Image, ImageDraw

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "tools/dev"))
spec = importlib.util.spec_from_file_location("brandkit", os.path.join(REPO, "tools/dev/brand-kit.py"))
bk = importlib.util.module_from_spec(spec); spec.loader.exec_module(bk)

ORIG = os.path.join(REPO, "assets/比特币学习地图/在可灵P1提示词生成好原图0822.PNG")
EMBLEM = os.path.join(REPO, "assets/brand/btc-emblem-0822.png")
OUT_A = os.path.join(REPO, "assets/cover")
OUT_B = os.path.join(REPO, "assets/cover")
NORM = (1440, 1920)  # STATION_COORDS 基准系
os.makedirs(OUT_A, exist_ok=True)

# 9 站副标题（一句话钩子）
SUBS = {
    "1": "一张学习地图，看懂比特币的来路",
    "1.5": "从贝壳到比特币，重新理解货币",
    "2": "银行城堡里的三道裂缝",
    "3": "一笔钱能不能花两次？",
    "4": "一张公开的账本，全网共同记账",
    "5": "一座用算力堆出的山",
    "6": "一台没有老板的机器",
    "7": "记账的工蜂与它们的奖赏",
    "8": "只属于你的那把钥匙",
    "9": "九段代码，构成比特币的全部",
}

def load_norm():
    return Image.open(ORIG).convert("RGBA").resize(NORM, Image.LANCZOS)
def load_emblem():
    return Image.open(EMBLEM).convert("RGBA")

def paste_emblem(canvas, cx, cy, target_radius):
    """把原图抠出的 3D 金色 ₿ 字徽 paste 到画布 (cx,cy) 位置，目标半径 target_radius。"""
    em = load_emblem()
    sz = int(target_radius * 2.4)   # 字徽略大于高亮环
    em = em.resize((sz, sz), Image.LANCZOS)
    canvas.alpha_composite(em, (cx - sz // 2, cy - sz // 2))

def draw_six_headline(img, station_id):
    """6 元素头条版（900×383）。徽章式中心：深色圆盘+金边+原图₿字徽+站名+英文。"""
    st = bk.STATION_COORDS[station_id]
    sub = SUBS[station_id]
    W, H = img.size
    d = ImageDraw.Draw(img)

    # 暗化蒙版（顶部 logo+图例 / 底部 副标题+站号）—— 缩小底部暗化
    d.rectangle([0, 0, W, 70], fill=(0, 0, 0, 110))
    d.rectangle([0, H - 80, W, H], fill=(0, 0, 0, 150))

    def F(px, **kw): return bk.get_font(max(8, int(px * 0.55)), **kw)

    # 元素1：logo（左上）
    d.text((20, 16), "慢读宝盒", fill=bk.WARM_WHITE, font=F(34, bold=True))
    # 元素2：视角图例（6 圆点，右上）
    for i, (nm, col) in enumerate(bk.VIEW_COLORS):
        cx = W - 200 + i * 28
        d.ellipse([cx - 3, 28 - 3, cx + 3, 28 + 3], fill=col)

    # 元素4：徽章式中心（深色圆盘 + 金边 + 3 环 + ₿ 字徽 + 站名 + 英文）
    hx, hy = W // 2, int(H * 0.42)
    disk_r = 54
    # 2 道金环（在圆盘外，干净不挤）
    for rr, al in [(disk_r + 18, 220), (disk_r + 32, 150)]:
        d.ellipse([hx - rr, hy - rr, hx + rr, hy + rr], outline=(247, 147, 26, al), width=3)
    # 深色圆盘（**不透明**，遮住原图中央地形避免双层）
    md_sz = disk_r * 2 + 8
    medallion = Image.new("RGBA", (md_sz, md_sz), (0, 0, 0, 0))
    ImageDraw.Draw(medallion).ellipse([0, 0, md_sz, md_sz], fill=(15, 15, 15, 250),
                                       outline=bk.BTC_ORANGE, width=3)
    img.alpha_composite(medallion, (hx - md_sz // 2, hy - md_sz // 2))
    # 字徽（缩放到 95% 圆盘直径）
    paste_emblem(img, hx, hy, int(disk_r * 0.95))
    # 站名（圆盘下方）
    nf = F(28, bold=True, song=True)
    bb = d.textbbox((0, 0), st["name"], font=nf); nw = bb[2] - bb[0]
    d.text((hx - nw // 2, hy + disk_r + 10), st["name"], fill=bk.WARM_WHITE, font=nf)
    # 英文（站名下方）
    ef = F(13, bold=True)
    bb2 = d.textbbox((0, 0), st["en"], font=ef); ew = bb2[2] - bb2[0]
    d.text((hx - ew // 2, hy + disk_r + 36), st["en"], fill=bk.BTC_ORANGE, font=ef)

    # 元素5+6：副标题（底部）
    d.text((20, H - 70), sub, fill=bk.WARM_WHITE, font=F(18, bold=True))
    # 元素7：站号 badge（右下）
    bt = f"站 {station_id}"; bf = F(16, bold=True)
    bb3 = d.textbbox((0, 0), bt, font=bf); bwid = bb3[2] - bb3[0] + 22
    d.rounded_rectangle([W - bwid - 16, H - 42, W - 16, H - 12], radius=8,
                        fill=(13, 13, 13), outline=bk.BTC_ORANGE, width=2)
    d.text((W - bwid - 6, H - 39), bt, fill=bk.WARM_WHITE, font=bf)
    return img

def crop_around(bg, cx, cy, ratio, max_cw=None, max_ch=None):
    """以 (cx,cy) 为中心按 ratio 裁矩形，clamp 进 1440×1920。"""
    W, H = NORM
    cw, ch = W, int(W / ratio)
    if ch > H: ch, cw = H, int(H * ratio)
    if max_cw and cw > max_cw:
        cw = max_cw; ch = int(cw / ratio)
    if max_ch and ch > max_ch:
        ch = max_ch; cw = int(ch * ratio)
    x0 = max(0, min(W - cw, cx - cw // 2))
    y0 = max(0, min(H - ch, cy - ch // 2))
    return bg.crop((x0, y0, x0 + cw, y0 + ch))

def make_cover(station_id, scheme):
    """scheme='A' 整图横条 | 'B' 站特写横条"""
    st = bk.STATION_COORDS[station_id]
    bg = load_norm()
    if scheme == "A":
        # 整图横条：取整图最大 2.35:1（ch=613），以站为中心
        crop = crop_around(bg, st["x"], st["y"], 900 / 383)
    else:
        # 站特写横条：取整图 50% 宽 2.35:1（ch=306），以站为中心（特写）
        crop = crop_around(bg, st["x"], st["y"], 900 / 383, max_cw=720, max_ch=306)
    img = crop.resize((900, 383), Image.LANCZOS).convert("RGBA")
    img = draw_six_headline(img, station_id)
    out = os.path.join(OUT_A if scheme == "A" else OUT_B,
                       f"站{station_id}-{st['name']}-方案{scheme}-头条900x383.png")
    img.convert("RGB").save(out, quality=95)
    print(f"✅ {os.path.basename(out)}  scheme={scheme}  center=({st['x']},{st['y']})")

if __name__ == "__main__":
    SIDS = ["1", "1.5", "2", "3", "4", "5", "6", "7", "8", "9"]
    # 先做站4 样张
    if "--all" not in sys.argv:
        for sch in ("A", "B"):
            make_cover("4", sch)
    else:
        for sid in SIDS:
            for sch in ("A", "B"):
                make_cover(sid, sch)
        print(f"\n共 {len(SIDS)*2} 张封面已生成")
