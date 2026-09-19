# -*- coding: utf-8 -*-
"""
brand_figs.py — 慢读宝盒「品牌配图模板库」（ADR-0008 候选实现）
================================================================
把配图从「每站各写一个脚本 + 各自调色」收敛为「一套主题色板 + 一套图元 + 一份规格」。

设计目标：
  1. 色调只有一个来源（THEMES），换主题 = 换一个字符串
  2. 规格只有一个来源（SIZES），不再出现 16 种画布比例
  3. 品牌元素（顶栏/合规条/站标/₿）由 base() 统一盖，不靠每张图自觉

用法（库）：
    from brand_figs import Theme, canvas, card, arrow, save
    th = Theme("warm-dark")          # 或 "paper-light" / "neutral-dark"
    im, d = canvas(th, "哈希函数：数字世界的指纹机", "站5 · 哈希岭")
"""

from __future__ import annotations
import math, pathlib
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/System/Library/Fonts/PingFang.ttc"
BRAND = pathlib.Path("/Users/mac/Desktop/宝盒知识库/比特币学习地图/assets/brand")

# ---------------- 规格（唯一定义源） ----------------
SIZES = {
    "16:9": (1280, 720),      # 主规格：叙事/流程/多卡
    "4:3":  (1280, 960),      # 次规格：对比/表格
    "1:1":  (1280, 1280),     # 深挖图：大结构（如公开账本）
}
TOPBAR_H = 66
FOOTBAR_H = 56
R_BIG, R_SM = 24, 14          # 圆角统一两档

COMPLIANCE = "风险提示：比特币价格波动剧烈 · 本文仅作区块链科普 · 不构成投资建议"


# ---------------- 主题色板（唯一定义源） ----------------
class Theme:
    """一个主题 = 一套完整色板。字段语义固定，换值即换风格。"""

    def __init__(self, key):
        self.key = key
        self.__dict__.update(THEMES[key])

    def __repr__(self):
        return f"<Theme {self.key}>"


THEMES = {
    # ============ A. 品牌暖黑卡（与封面 #1F150B 同源） ============
    "warm-dark": dict(
        label="品牌暖黑卡",
        BG=(31, 21, 11),          # #1F150B 封面同源暖黑
        CARD=(45, 33, 20),        # 卡面比底亮一档
        CARD_HI=(58, 43, 26),     # 高亮卡（当前/结论）
        EDGE=(84, 64, 40),        # 卡边（暖棕金）
        TOPBAR=(24, 16, 9),
        FOOTBAR=(24, 16, 9),
        TXT=(245, 237, 216),      # #F5EDD8 米白
        MID=(176, 158, 126),      # 次文字（暖灰）
        ACCENT=(247, 147, 26),    # #F7931A 品牌橙
        GOLD=(201, 160, 80),      # #C9A050 品牌金
        DIM=(70, 54, 34),         # 未激活/未来态
    ),
    # ============ B. 暖米浅卡（与正文底 #FBF7F0 同源） ============
    "paper-light": dict(
        label="暖米浅卡",
        BG=(251, 247, 240),       # #FBF7F0 文章正文底同源
        CARD=(255, 253, 248),
        CARD_HI=(248, 238, 218),
        EDGE=(224, 211, 188),
        TOPBAR=(243, 237, 225),
        FOOTBAR=(243, 237, 225),
        TXT=(61, 43, 31),         # #3D2B1F 深棕（比纯黑柔和）
        MID=(139, 118, 96),
        ACCENT=(247, 147, 26),
        GOLD=(138, 90, 16),       # 浅底上的金必须压深否则看不清
        DIM=(205, 194, 176),
    ),
    # ============ C. 中性纯黑卡（现行站4/5，作对照基线） ============
    "neutral-dark": dict(
        label="中性纯黑卡（现行）",
        BG=(13, 13, 13),          # #0D0D0D 网站深色主题同源
        CARD=(26, 26, 26),
        CARD_HI=(34, 34, 34),
        EDGE=(58, 58, 58),
        TOPBAR=(20, 20, 20),
        FOOTBAR=(20, 20, 20),
        TXT=(229, 229, 229),
        MID=(160, 160, 160),
        ACCENT=(247, 147, 26),
        GOLD=(255, 215, 0),
        DIM=(48, 48, 48),
    ),
}


def font(sz, bold=False):
    return ImageFont.truetype(FONT_PATH, sz, index=1 if bold else 0)


def _hex(c):
    return "#%02X%02X%02X" % c


# ---------------- 画布 + 品牌元素 ----------------
def canvas(th, title, station, size="16:9", sub=""):
    """返回 (im, draw)。自动盖：顶栏（左图题 / 右站别）+ 底合规条。"""
    W, H = SIZES[size]
    im = Image.new("RGB", (W, H), th.BG)
    d = ImageDraw.Draw(im)

    # 顶栏：图题（品牌橙）+ 站别（次文字，右对齐）
    d.rectangle([0, 0, W, TOPBAR_H], fill=th.TOPBAR)
    d.line([0, TOPBAR_H, W, TOPBAR_H], fill=th.EDGE, width=2)   # 分隔线（品牌金）
    d.text((48, TOPBAR_H // 2), title, font=font(30, True), fill=th.ACCENT, anchor="lm")
    if station:
        d.text((W - 48, TOPBAR_H // 2), station, font=font(22), fill=th.MID, anchor="rm")

    # 底栏：合规条（全系列固定文案，图上可溯源）
    d.rectangle([0, H - FOOTBAR_H, W, H], fill=th.FOOTBAR)
    d.line([0, H - FOOTBAR_H, W, H - FOOTBAR_H], fill=th.EDGE, width=2)
    d.text((W // 2, H - FOOTBAR_H // 2), COMPLIANCE, font=font(19), fill=th.MID, anchor="mm")

    if sub:
        d.text((48, TOPBAR_H + 26), sub, font=font(21), fill=th.MID)
    return im, d


# ---------------- 通用图元 ----------------
def card(d, box, th, hi=False, r=R_SM, fill=None, edge=None, width=2):
    """标准卡片：圆角 + 边线。hi=True 用高亮色（当前态/结论）。"""
    x0, y0, x1, y1 = box
    f = fill or (th.CARD_HI if hi else th.CARD)
    e = edge or (th.ACCENT if hi else th.EDGE)
    d.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=f, outline=e, width=width)


def chip(d, xy, th, text, fs=20, color=None, bg=None, pad=(14, 8), r=10):
    """胶囊标签（用于"已走/当前/未来"、语义标记）。"""
    f = font(fs)
    w = d.textlength(text, font=f)
    x, y = xy
    box = [x, y, x + w + pad[0] * 2, y + fs + pad[1] * 2]
    d.rounded_rectangle(box, radius=r, fill=bg or th.CARD, outline=color or th.MID, width=2)
    d.text((x + pad[0], y + fs / 2 + pad[1]), text, font=f, fill=color or th.TXT, anchor="lm")
    return box


def arrow(d, p0, p1, th, color=None, width=3, head=11):
    """直线箭头（图元统一宽度，避免每张图各自调）。"""
    c = color or th.ACCENT
    d.line([p0, p1], fill=c, width=width)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    for s in (+1, -1):
        a = ang + s * 0.42
        d.line([p1, (p1[0] - head * math.cos(a), p1[1] - head * math.sin(a))], fill=c, width=width)


def btc(d, im, cx, cy, dia):
    """在 (cx,cy) 贴官方 ₿ 标准件（ADR-0006：只准官方 SVG 复刻件）。"""
    p = BRAND / "btc-emblem-official.png"
    if not p.exists():
        return False
    e = Image.open(p).convert("RGBA").resize((dia, dia), Image.LANCZOS)
    im.paste(e, (int(cx - dia / 2), int(cy - dia / 2)), e)
    return True


def save(im, path):
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    im.save(path, optimize=True)
    return path


# ---------------- 通用版式：四卡信息图（最常用的一种） ----------------
def four_cards(th, title, station, items, size="16:9", footer=None):
    """items: [(序号, 标题, 说明), ...] 最多 4 条，横向四卡。"""
    im, d = canvas(th, title, station, size)
    W, H = im.size
    n = len(items)
    gap = 26
    x0, x1 = 60, W - 60
    cw = (x1 - x0 - gap * (n - 1)) / n
    cy0, cy1 = TOPBAR_H + 72, H - FOOTBAR_H - (96 if footer else 46)
    for i, (num, t, desc) in enumerate(items):
        cx0 = x0 + i * (cw + gap)
        card(d, [cx0, cy0, cx0 + cw, cy1], th, hi=(i == 0), r=R_BIG)
        d.text((cx0 + 26, cy0 + 30), num, font=font(34, True), fill=th.GOLD, anchor="la")
        d.text((cx0 + 26, cy0 + 92), t, font=font(28, True), fill=th.TXT, anchor="la")
        # 说明文字自动折行
        _wrap(d, desc, cx0 + 26, cy0 + 146, cw - 52, font(20), th.MID, 32, max_lines=4)
    if footer:
        fy = H - FOOTBAR_H - 76
        d.rounded_rectangle([60, fy, W - 60, fy + 56], radius=R_SM,
                            fill=th.CARD_HI, outline=th.ACCENT, width=2)
        d.text((W // 2, fy + 28), footer, font=font(22, True), fill=th.TXT, anchor="mm")
    return im


def _wrap(d, text, x, y, maxw, f, fill, lh, max_lines=3):
    """中英混排折行（按字符宽度累加，中文逐字）。"""
    lines, cur = [], ""
    for ch in text:
        if d.textlength(cur + ch, font=f) > maxw:
            lines.append(cur)
            cur = ch
            if len(lines) >= max_lines:
                break
        else:
            cur += ch
    if cur and len(lines) < max_lines:
        lines.append(cur)
    for i, ln in enumerate(lines):
        d.text((x, y + i * lh), ln, font=f, fill=fill, anchor="la")
    return len(lines)


# ---------------- 预览：把图嵌进"文章底色"里看融合效果 ----------------
def preview_in_article(img, out, article_bg=(251, 247, 240), width=677):
    """模拟微信正文：暖米底 + 居中图 + 上下文字块，判断'图是否硬塞'。"""
    ratio = width / img.width
    im_s = img.resize((width, int(img.height * ratio)), Image.LANCZOS)
    pad, txt_h = 24, 54
    W = width + pad * 2
    H = txt_h + im_s.height + txt_h + pad * 2
    canvas_ = Image.new("RGB", (W, H), article_bg)
    d = ImageDraw.Draw(canvas_)
    f = font(17)
    for i, (cy, txt) in enumerate([(pad, "上一段正文……"), (pad + txt_h + im_s.height + 18, "下一段正文……")]):
        d.text((pad, cy), txt, font=f, fill=(70, 60, 50))
    canvas_.paste(im_s, (pad, pad + txt_h))
    canvas_.save(out)
    return canvas_
