#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""慢读宝盒 9 站封面模板系统（v1.0）

模板 = 固定层 + 变量层 + 适配层
────────────────────────────────────────────
【固定层】(9 站不变)
  - 暖米纸底 PAPER #F5EFE0（宝盒 = 容器 = 品牌）
  - 深棕墨字 INK   #3D3226（书卷气，非黑金科技）
  - 比特币橙点缀   #F7931A（只占 10%）
  - ₿ 官方标志（程序化 draw_bitcoin_b，100% 国际同步）固定左侧 15%

【变量层】(每站变化)
  - 站号（大数字）、站名、英文名、副标题
  - 该站意象图（可灵 kling-image-v3_0_omni 生成，21:9）

【适配层】
  - 微信头条 900×383 (2.35:1) ← 本脚本
  - 文章首图 1080×1440 (3:4)  ← 后续扩展
"""
import importlib.util, os, sys
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
spec = importlib.util.spec_from_file_location("brandkit", os.path.join(REPO, "tools/dev/brand-kit.py"))
bk = importlib.util.module_from_spec(spec); spec.loader.exec_module(bk)

# ===== 固定层：色彩 token =====
PAPER      = (245, 239, 224)   # 暖米纸（宝盒的盒）
PAPER_DEEP = (235, 226, 205)   # 纸的暗部
INK        = (61, 50, 38)      # 深棕墨（书卷气）
INK_SOFT   = (120, 105, 85)    # 次级文字
BTC_ORANGE = (247, 147, 26)    # 比特币橙（点缀 10%）
GOLD       = (198, 156, 74)    # 金（分隔线/装饰）

# ===== 变量层：9 站文案 =====
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

def compose(st_id, img_path, out_path, W=900, H=383):
    st = STATIONS[st_id]
    # ---------- 1. 纸底（固定层）----------
    canvas = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(canvas)
    # 纸的微妙暗部（左上到右下渐深，模拟纸张受光）
    grad = np.linspace(0, 1, W)[None, :] * np.ones((H, 1))
    arr = np.asarray(canvas).astype(float)
    arr = arr * (1 - 0.06 * grad[..., None])
    canvas = Image.fromarray(arr.astype(np.uint8))
    d = ImageDraw.Draw(canvas)

    # ---------- 2. 右侧意象区（变量层，40%）----------
    img_x0 = int(W * 0.60)
    img_w, img_h = W - img_x0, H
    if img_path and os.path.exists(img_path):
        im = Image.open(img_path).convert("RGB")
        iw, ih = im.size
        # 取意象图右侧 40%（比例≈0.94，匹配 360×383）
        crop_x0 = int(iw * 0.60)
        im = im.crop((crop_x0, 0, iw, ih)).resize((img_w, img_h), Image.LANCZOS)
        # 左边缘羽化渐变融合到纸底
        mask = Image.new("L", (img_w, img_h), 255)
        md = ImageDraw.Draw(mask)
        fade = int(img_w * 0.30)
        for i in range(fade):
            md.line([(i, 0), (i, img_h)], fill=int(255 * i / fade))
        canvas.paste(im, (img_x0, 0), mask)
        d = ImageDraw.Draw(canvas)
        # 意象区左侧一条金色细线（分隔品牌区/意象区）
        d.line([(img_x0, int(H*0.12)), (img_x0, int(H*0.88))], fill=GOLD, width=2)

    # ---------- 3. 顶部品牌条（固定层）----------
    d.text((36, 22), "慢读宝盒", fill=INK, font=F(19, bold=True, song=True))
    # 站号大数字（右上角，变量层）
    num = st_id.split(".")[0]
    nf = F(30, bold=True)
    bb = d.textbbox((0, 0), num, font=nf)
    nw = bb[2] - bb[0]
    d.text((W - 36 - nw, 18), num, fill=BTC_ORANGE, font=nf)
    # 分隔线
    d.line([(36, 56), (W - 36, 56)], fill=GOLD, width=1)

    # ---------- 4. 左侧 ₿ 标志（固定层，品牌锚点）----------
    bx = 76
    by = int(H * 0.56)
    bk.draw_bitcoin_b(canvas, bx, by, 30)

    # ---------- 5. 中部文字区（变量层）----------
    tx = 140
    # 站名（主）
    nf2 = F(40, bold=True, song=True)
    d.text((tx, int(H*0.26)), st["name"], fill=INK, font=nf2)
    # 英文名（橙金小字）
    d.text((tx + 2, int(H*0.50)), st["en"], fill=BTC_ORANGE, font=F(13, bold=True))
    # 副标题
    d.text((tx, int(H*0.63)), st["sub"], fill=INK_SOFT, font=F(15))

    canvas.save(out_path, quality=95)
    print(f"✅ {os.path.basename(out_path)}  {W}x{H}  站{st_id} {st['name']}")
    return out_path

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--station", default="4")
    ap.add_argument("--img", default="/tmp/kling-pilot/站4-账本海-意象.png")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or f"/tmp/kling-pilot/宝盒模板v1-站{a.station}-{STATIONS[a.station]['name']}-900x383.png"
    compose(a.station, a.img, out)
