#!/usr/bin/env python3
"""
学习地图升级 · Before/After 对比图
- BEFORE: 0822 v5 旧版（无 9 站标注 / 风格与微信封面割裂）
- AFTER:  v2-B-01 教育风母图 + PIL 烧 9 站标注
- 输出: out/comparison/learning-map-before-after.png
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OLD = os.path.join(ROOT, "assets/比特币学习地图/比特币学习地图-P1-0822-可灵版-9站-v5.png")
NEW = os.path.join(ROOT, "assets/learning-map/v2-B-01-教育风-with-stations.png")
OUT = os.path.join(ROOT, "out/comparison/learning-map-before-after.png")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

# 缩放
TGT_W = 600
PAD = 24
LABEL_H = 56
TITLE_H = 64

def shrink(path, w):
    img = Image.open(path).convert("RGB")
    ratio = w / img.width
    h = int(img.height * ratio)
    return img.resize((w, h), Image.LANCZOS)

def font(size):
    # macOS 系统字体
    return ImageFont.truetype("/System/Library/Fonts/Hiragino Sans GB.ttc", size)

old = shrink(OLD, TGT_W)
new = shrink(NEW, TGT_W)

# 画布
W = TGT_W * 2 + PAD * 3
H = TITLE_H + LABEL_H + max(old.height, new.height) + PAD * 2

canvas = Image.new("RGB", (W, H), (245, 239, 224))  # ivory
draw = ImageDraw.Draw(canvas)

# 标题
title_font = font(28)
draw.text((PAD, 18), "学习地图升级 · BEFORE / AFTER", fill=(60, 40, 0), font=title_font)

# 标签
label_font = font(22)
# BEFORE 红，AFTER 绿
draw.text((PAD + TGT_W // 2 - 60, TITLE_H + 12), "BEFORE · 0822 v5", fill=(180, 50, 50), font=label_font)
draw.text((PAD * 2 + TGT_W + TGT_W // 2 - 60, TITLE_H + 12), "AFTER · v2-B-01 教育风", fill=(40, 140, 60), font=label_font)

# 贴图
y_img = TITLE_H + LABEL_H + PAD
canvas.paste(old, (PAD, y_img))
canvas.paste(new, (PAD * 2 + TGT_W, y_img))

# 边框
border_color = (200, 180, 140)
draw.rectangle([(PAD - 1, y_img - 1), (PAD + TGT_W, y_img + old.height)], outline=border_color, width=1)
draw.rectangle([(PAD * 2 + TGT_W - 1, y_img - 1), (PAD * 2 + TGT_W * 2, y_img + new.height)], outline=border_color, width=1)

# 保存
canvas.save(OUT, optimize=True)
print(f"✅ {OUT}")
print(f"   {W}x{H}  ({os.path.getsize(OUT)/1024:.1f} KB)")
