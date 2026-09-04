#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""宝盒 9 站封面 v3 — 品牌统一方案
────────────────────────────────────────────
核心：底图 = 网站同源 `在可灵P1提示词生成好原图0822.png`（v5 的零文字母图）
      → 网站与公众号共用同一张地图 = 品牌 100% 统一

方案 2：按站裁不同横条
  - 原图 3520×4672 竖版 → 每站裁该站位置的 2.35:1 横条（clamp 进画布）
  - 9 张封面背景不同（站位置不同），但同一张地图同一风格 = 统一中有变化

元素（微信 2026 规范）：
  - 900×383 (2.35:1)
  - 中心 383×383 安全区：官方 ₋ PNG + 站名 + 英文 + 副标
  - 大数字站号（56pt，缩略图可读）
  - 底部留白（微信叠加标题会遮挡）
  - 暖米纸底（深色模式友好）
"""
import importlib.util, os, sys
from PIL import Image, ImageDraw, ImageFilter

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
spec = importlib.util.spec_from_file_location("brandkit", os.path.join(REPO, "tools/dev/brand-kit.py"))
bk = importlib.util.module_from_spec(spec); spec.loader.exec_module(bk)

ORIG = os.path.join(REPO, "assets/比特币学习地图/在可灵P1提示词生成好原图0822.PNG")
NORM = (1440, 1920)   # STATION_COORDS 基准系

PAPER      = (245, 239, 224)
BTC_ORANGE = (247, 147, 26)
GOLD       = (198, 156, 74)

STATIONS = {
    "1":   {"name": "现金湾",     "en": "CASH BAY",          "sub": "一张学习地图，看懂比特币的来路"},
    "1.5": {"name": "钱到底是什么", "en": "WHAT IS MONEY",     "sub": "从贝壳到比特币，重新理解货币"},
    "2":   {"name": "银行堡",     "en": "VAULT KEEP",        "sub": "银行城堡里的三道裂缝"},
    "3":   {"name": "双花峡",     "en": "DOUBLE-SPEND GORGE","sub": "一笔钱能不能花两次？"},
    "4":   {"name": "账本海",     "en": "LEDGER SEA",        "sub": "一张公开的账本，全网共同记账"},
    "5":   {"name": "哈希岭",     "en": "HASH RIDGE",        "sub": "一座用算力堆出的山"},
    "6":   {"name": "共识峰",     "en": "CONSENSUS PEAK",    "sub": "一台没有老板的机器"},
    "7":   {"name": "矿工谷",     "en": "MINER VALLEY",      "sub": "记账的工蜂与它们的奖赏"},
    "8":   {"name": "私钥崖",     "en": "KEY CLIFF",         "sub": "只属于你的那把钥匙"},
    "9":   {"name": "代码之巅",   "en": "CODE SUMMIT",       "sub": "九段代码，构成比特币的全部"},
}

def F(sz, bold=False, song=False):
    return bk.get_font(sz, bold=bold, song=song)

def paste_emblem(canvas, cx, cy, target_diam):
    """官方 bitboy ₋ PNG（100% 国际标准）"""
    src = os.path.join(REPO, "assets/brand/btcoin-symbol-bitboy.png")
    if not os.path.exists(src): return
    em = Image.open(src).convert("RGBA").resize((target_diam, target_diam), Image.LANCZOS)
    canvas.alpha_composite(em, (cx - target_diam//2, cy - target_diam//2))

def crop_station_strip(orig_img, st, ratio=900/383):
    """从原图裁该站位置的 2.35:1 横条（clamp 进画布）"""
    W, H = orig_img.size
    cw, ch = W, int(W / ratio)
    if ch > H: ch, cw = H, int(H * ratio)
    # 站坐标（NORM 1440×1920 基准）→ 原图坐标
    sx = int(st["x"] * W / NORM[0])
    sy = int(st["y"] * H / NORM[1])
    x0 = max(0, min(W - cw, sx - cw//2))
    y0 = max(0, min(H - ch, sy - ch//2))
    return orig_img.crop((x0, y0, x0+cw, y0+ch)), (x0, y0, cw, ch)

def compose(st_id, out_path, W=900, H=383):
    st = dict(bk.STATION_COORDS[st_id])
    st.update(STATIONS[st_id])
    orig = Image.open(ORIG).convert("RGB")
    strip, box = crop_station_strip(orig, bk.STATION_COORDS[st_id])
    canvas = strip.resize((W, H), Image.LANCZOS).convert("RGBA")
    d = ImageDraw.Draw(canvas)

    # 顶部条 48px（品牌 + 大站号）
    d.rectangle([0, 0, W, 48], fill=(0, 0, 0, 110))
    d.text((28, 10), "慢读宝盒", fill=PAPER, font=F(20, bold=True))
    nf_num = F(56, bold=True)
    bb = d.textbbox((0,0), st_id, font=nf_num); nw = bb[2]-bb[0]
    d.text((W - 32 - nw, -4), st_id, fill=BTC_ORANGE, font=nf_num)
    d.line([(28, 52), (W-28, 52)], fill=GOLD, width=1)

    # 中央 383 安全区：椭圆暗化（覆盖底图，保证文字/₋ 可读）
    cx, cy = W//2, 200
    overlay = Image.new("RGBA", (W, H), (0,0,0,0))
    ImageDraw.Draw(overlay).ellipse([cx-250, cy-130, cx+250, cy+130], fill=(0,0,0,150))
    canvas.alpha_composite(overlay.filter(ImageFilter.GaussianBlur(28)))
    d = ImageDraw.Draw(canvas)

    # 官方 ₋ PNG
    paste_emblem(canvas, cx-90, cy, 80)
    # 站名 + 英文 + 副标（暖白，缩略图/深色模式都可读）
    d.text((cx-5, cy-32), st["name"], fill=PAPER, font=F(34, bold=True, song=True))
    d.text((cx-5, cy+8),  st["en"],   fill=BTC_ORANGE, font=F(14, bold=True))
    sub = st["sub"]
    if len(sub) > 18: sub = sub[:18] + "…"
    d.text((cx-5, cy+30), sub, fill=PAPER, font=F(13))

    # 底部留白（不放文字 — 微信叠加标题遮挡）
    d.line([(28, H-12), (W-28, H-12)], fill=(180, 165, 145), width=1)

    canvas.convert("RGB").save(out_path, quality=95)
    print(f"✅ {os.path.basename(out_path)}  {W}x{H}  站{st_id} {st['name']}  原图裁切box={box}")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--stations", nargs="+", default=["4"])
    ap.add_argument("--outdir", default="/tmp/cover-v3")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    for sid in a.stations:
        compose(sid, f"{a.outdir}/宝盒v3-站{sid}-{STATIONS[sid]['name']}-900x383.png")
