#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""慢读宝盒 9 站封面 v2 模板 — 基于微信 2026 规范 + bitboy 官方 ₋ PNG
────────────────────────────────────────────
硬约束（多源 2026 调研一致）：
  - 尺寸 900×383 (2.35:1) 头条首图
  - 中心 383×383 安全区（转发/列表自动裁切到这里）
  - 缩略图 ≈ 1:1 指甲盖大小 → 站号/站名必须超大字号
  - 底部不放文字（微信会叠加标题遮挡）
  - 暖米纸底（深色模式友好，非纯白）

突出（视觉锚点）：
  1. 9 站学习地图（底图）— "一张学习比特币的地图"作为核心课程封面感
  2. 官方 ₋ PNG（bitboy 设计，#f7931a + 白 B + 14° 倾斜）— 100% 标准
  3. 大数字站号 + 大字号站名 — 缩略图可读

弱化：
  - 副标 → 移到中部（不在底部）
  - 装饰元素最小化
"""
import importlib.util, os, sys
from PIL import Image, ImageDraw, ImageFilter

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
spec = importlib.util.spec_from_file_location("brandkit", os.path.join(REPO, "tools/dev/brand-kit.py"))
bk = importlib.util.module_from_spec(spec); spec.loader.exec_module(bk)

PAPER      = (245, 239, 224)
INK        = (61, 50, 38)
INK_SOFT   = (120, 105, 85)
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
    """贴官方 ₋ PNG（透明背景 RGBA）"""
    src = os.path.join(REPO, "assets/brand/btcoin-symbol-bitboy.png")
    if not os.path.exists(src):
        return
    em = Image.open(src).convert("RGBA")
    em = em.resize((target_diam, target_diam), Image.LANCZOS)
    canvas.alpha_composite(em, (cx - target_diam//2, cy - target_diam//2))

def compose(st_id, map_path, out_path, W=900, H=383):
    st = STATIONS[st_id]
    # 1. 地图底图（占满 900×383）
    if map_path and os.path.exists(map_path):
        bg = Image.open(map_path).convert("RGB")
        # 21:9 底图（3136×1344）→ 缩放到 900×383
        canvas = bg.resize((W, H), Image.LANCZOS).convert("RGBA")
    else:
        canvas = Image.new("RGBA", (W, H), PAPER + (255,))
    d = ImageDraw.Draw(canvas)

    # 2. 顶部条（暗化 48px + 品牌 + 大站号）
    d.rectangle([0, 0, W, 48], fill=(0, 0, 0, 110))
    d.text((28, 10), "慢读宝盒", fill=PAPER, font=F(20, bold=True))
    # 大数字站号（右上角，56pt — 缩略图可读）
    nf_num = F(56, bold=True)
    bb = d.textbbox((0, 0), st_id, font=nf_num); nw = bb[2]-bb[0]
    d.text((W - 32 - nw, -4), st_id, fill=BTC_ORANGE, font=nf_num)
    # 分隔线（金色细线）
    d.line([(28, 52), (W-28, 52)], fill=GOLD, width=1)

    # 3. 中央 383 安全区（暗化椭圆，**完全覆盖**底图中央图标）
    cx, cy = W//2, 200
    overlay = Image.new("RGBA", (W, H), (0,0,0,0))
    od = ImageDraw.Draw(overlay)
    # 大椭圆暗化（覆盖底图中央 ₋ 花等图标）
    od.ellipse([cx-250, cy-130, cx+250, cy+130], fill=(0,0,0,140))
    overlay = overlay.filter(ImageFilter.GaussianBlur(28))
    canvas.alpha_composite(overlay)
    d = ImageDraw.Draw(canvas)

    # 4. 官方 ₋ PNG（80px 直径，中央偏左）
    paste_emblem(canvas, cx-90, cy, 80)

    # 5. 大站名（中央偏右 + ₋ 右侧，34pt 缩略图可读）
    nf_name = F(34, bold=True, song=True)
    bb_n = d.textbbox((0,0), st["name"], font=nf_name); nw_n = bb_n[2]-bb_n[0]
    d.text((cx-5, cy-32), st["name"], fill=PAPER, font=nf_name)
    # 英文名（中等，橙金小字）
    nf_en = F(14, bold=True)
    bb_e = d.textbbox((0,0), st["en"], font=nf_en); nw_e = bb_e[2]-bb_e[0]
    d.text((cx-5, cy+8), st["en"], fill=BTC_ORANGE, font=nf_en)
    # 副标（暖白色，清晰可读）
    sf = F(13)
    sub = st["sub"]
    if len(sub) > 14: sub = sub[:14] + "…"
    d.text((cx-5, cy+30), sub, fill=PAPER, font=sf)

    # 6. 底部留白（不放文字 — 微信会叠加标题遮挡）
    # 仅一条极淡的分隔线（不显眼）
    d.line([(28, H-12), (W-28, H-12)], fill=(180, 165, 145), width=1)

    canvas.convert("RGB").save(out_path, quality=95)
    print(f"✅ {os.path.basename(out_path)}  {W}x{H}  站{st_id} {st['name']}")
    return out_path

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--station", default="4")
    ap.add_argument("--map", default="/tmp/btc-official/9station-map.png")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or f"/tmp/btc-official/宝盒模板v2-站{a.station}-{STATIONS[a.station]['name']}-900x383.png"
    compose(a.station, a.map, out)