#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""replace_btc_marks.py —— 把历史配图里的手绘/凑字 ₿ 替换为官方 SVG 复刻标准件
（ADR-0006：₿ 只准官方矢量复刻，禁止手绘/AI 生成）

三处定点修复（2026-09-19）：
  1. 站4-账本海/01-public-ledger.png  大橙圆中心衬线 B → 官方 emblem d380（同色 #F7931A 无缝融合）
  2. 站4-账本海/07-mindmap-summary.png 化名卡歪 ₿ → 深底遮盖 + 官方 emblem d66
  3. 站1-现金湾/06-limited-supply.png 「20BF」凑字方框 → 官方白色 ₿ 符号（高 24px）

原图先备份到各站 03-配图/_原图备份-YYYYMMDD/（不覆盖原则）。
用法：python3 tools/dev/replace_btc_marks.py
"""
import os, shutil, math
from PIL import Image, ImageDraw

BASE = "/Users/mac/Desktop/宝盒知识库/比特币学习地图/慢读宝盒公众号"
BRAND = "/Users/mac/Desktop/宝盒知识库/比特币学习地图/assets/brand"
BACKUP_TAG = "20260919"

JOBS = [
    # (文章目录, 文件, 修复函数名)
    ("站4-账本海", "01-public-ledger.png", "fix_ledger_center"),
    ("站4-账本海", "07-mindmap-summary.png", "fix_mindmap_coin"),
    ("站1-现金湾", "06-limited-supply.png", "fix_supply_icon"),
]


def backup(path, station):
    bdir = os.path.join(BASE, station, "03-配图", f"_原图备份-{BACKUP_TAG}")
    os.makedirs(bdir, exist_ok=True)
    dst = os.path.join(bdir, os.path.basename(path))
    if not os.path.exists(dst):
        shutil.copy2(path, dst)
    return dst


def paste_emblem(img, cx, cy, d):
    """贴官方橙圆白 ₿（emblem），以 (cx,cy) 为中心、直径 d。统一 paste+mask（alpha_composite 不带 dest 会贴到 (0,0)）。"""
    emb = Image.open(os.path.join(BRAND, "btc-emblem-official.png")).convert("RGBA")
    emb = emb.resize((d, d), Image.LANCZOS)
    img.paste(emb, (int(cx - d / 2), int(cy - d / 2)), emb)


def fix_ledger_center(img):
    """站4-01：大纯橙圆中心 (639,671) 贴官方币 d380（圆为纯 #F7931A，同色无缝）。"""
    paste_emblem(img, 639, 671, 380)
    return img, "中心衬线B → 官方币 d380（同色无缝）"


def fix_mindmap_coin(img):
    """站4-07：歪 ₿ 中心 (640,430)。先深底圆 d84 盖旧币+光晕，再贴官方币 d66。"""
    d = ImageDraw.Draw(img)
    bg = img.getpixel((640, 388))  # 采样背景 (24,24,24)
    r = 42
    d.ellipse([640 - r, 430 - r, 640 + r, 430 + r], fill=bg)
    paste_emblem(img, 640, 430, 66)
    return img, "歪手绘₿ → 深底遮盖 + 官方币 d66"


def fix_supply_icon(img):
    """站1-06：「20BF」Unicode 凑字方框（中心 ~(639,62)）→ 官方白 ₿ 符号高 26px。"""
    sym = Image.open(os.path.join(BRAND, "btc-symbol-white.png")).convert("RGBA")
    h = 30
    w = int(sym.width * h / sym.height)
    sym = sym.resize((w, h), Image.LANCZOS)
    img.paste(sym, (int(639 - w / 2), int(62 - h / 2)), sym)
    return img, "「20BF」凑字框 → 官方白 ₿ h26"


def main():
    for station, fname, fn in JOBS:
        path = os.path.join(BASE, station, "03-配图", fname)
        backup(path, station)
        img = Image.open(path).convert("RGBA")
        img, note = globals()[fn](img)
        out = img.convert("RGB") if path.endswith(".png") and Image.open(path).mode == "RGB" else img
        out.save(path)
        print(f"✅ {station}/{fname}: {note}")


if __name__ == "__main__":
    main()
