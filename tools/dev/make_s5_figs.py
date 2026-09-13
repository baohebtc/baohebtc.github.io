# -*- coding: utf-8 -*-
"""站5《哈希岭》配图产线：品牌橙金深色卡，1280x720，程序化零积分。
用法：python make_s5_figs.py [01|02|03|04|05|07|all]
"""
import pathlib, sys, hashlib
from PIL import Image, ImageDraw, ImageFont

OUT = pathlib.Path("/Users/mac/Desktop/宝盒知识库/比特币学习地图/assets/articles/公众号/站5-哈希岭")
F = "/System/Library/Fonts/PingFang.ttc"

# 品牌色（站3技术蓝/站4海蓝为既成事实；站5无既定配色 → 默认品牌橙金）
BG      = (13, 13, 13)        # 深底
CARD    = (26, 26, 26)        # 卡片
EDGE    = (58, 58, 58)        # 卡边
TXT     = (229, 229, 229)     # 主文字
MID     = (160, 160, 160)     # 次文字
ORANGE  = (247, 147, 26)      # 品牌橙 #F7931A
GOLD    = (255, 215, 0)       # 金
BLUE    = (59, 130, 246)      # 站5站标蓝（地图同源）

W, H = 1280, 720
def font(sz, w=0):
    return ImageFont.truetype(F, sz, index=w)

def base(draw_title, sub=""):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, W, 66], radius=0, fill=(20, 20, 20))
    d.text((48, 16), draw_title, font=font(30, 1), fill=ORANGE)
    if sub:
        d.text((W - 48 - d.textlength(sub, font=font(22)), 22), sub, font=font(22), fill=MID)
    # 底部合规条
    d.rectangle([0, H - 56, W, H], fill=(20, 20, 20))
    d.text((W//2, H - 28), "风险提示：比特币价格波动剧烈 · 本文仅作区块链科普 · 不构成投资建议",
           font=font(20), fill=MID, anchor="mm")
    return im, d

def save(im, name):
    p = OUT / name
    im.save(p, optimize=True)
    print(f"✅ {name}  {im.size}  {p.stat().st_size/1024:.0f}KB")

# ---------- 01 指纹机：任意输入 → 固定输出 ----------
def fig01():
    im, d = base("哈希函数：数字世界的指纹机", "站5 · 哈希岭")
    cy = 330
    # 输入卡（三个不同长度）
    inputs = [("一个字「比」", 120), ("一篇 4500 字文章", 200), ("整部《红楼梦》", 280)]
    for i, (t, wd) in enumerate(inputs):
        y = 150 + i * 130
        d.rounded_rectangle([80, y, 80 + wd, y + 86], radius=14, fill=CARD, outline=EDGE, width=2)
        d.text((80 + wd/2, y + 43), t, font=font(26), fill=TXT, anchor="mm")
        d.text((80 + wd/2, y - 18), f"输入 {i+1}", font=font(18), fill=MID, anchor="mm")
        # 箭头
        d.line([90 + wd, y + 43, 500, cy], fill=ORANGE, width=3)
    # 中间搅拌机
    d.rounded_rectangle([500, cy - 110, 780, cy + 110], radius=24, fill=(30, 24, 16),
                        outline=ORANGE, width=4)
    d.text((640, cy - 40), "SHA-256", font=font(38, 1), fill=ORANGE, anchor="mm")
    d.text((640, cy + 14), "哈希函数", font=font(28), fill=TXT, anchor="mm")
    d.text((640, cy + 62), "只进不出 · 单向", font=font(20), fill=MID, anchor="mm")
    # 输出
    hx = hashlib.sha256("比特币".encode()).hexdigest()
    d.rounded_rectangle([860, cy - 100, 1220, cy + 100], radius=16, fill=(16, 16, 16),
                        outline=GOLD, width=3)
    d.text((1040, cy - 70), "输出 · 永远 64 字符", font=font(22), fill=GOLD, anchor="mm")
    for r in range(4):
        d.text((1040, cy - 30 + r * 34), hx[r*16:(r+1)*16], font=font(21, 1), fill=TXT, anchor="mm")
    d.line([780, cy, 860, cy], fill=GOLD, width=3)
    # 结论条
    d.rounded_rectangle([80, 580, 1200, 640], radius=14, fill=(30, 24, 16))
    d.text((640, 610), "一串 64 字符的「指纹」＝ 这份数据改不掉的身份证明", font=font(28, 1),
           fill=ORANGE, anchor="mm")
    save(im, "01-hash-machine.png")

# ---------- 02 四条性质 2x2 ----------
def fig02():
    im, d = base("凭什么被全网信任：四条硬性质", "缺一条，整座楼塌")
    cards = [
        ("确定性", "同一输入 → 永远同一输出", "今天算、一百年后算、任何设备算，逐位相同", "🔒"),
        ("单向性", "算得出指纹，倒推不出原文", "除了逐个猜，没有任何更快的办法", "➡️"),
        ("雪崩效应", "改一丁点 → 输出面目全非", "改 1 个字，约一半比特位翻转", "💥"),
        ("抗碰撞", "找不到两份数据共用一枚指纹", "2²⁵⁶ 种输出 ≈ 10⁷⁷，比地球原子还多", "🛡️"),
    ]
    cw, ch, gx, gy = 560, 210, 40, 36
    x0, y0 = (W - cw*2 - gx)//2, 110
    for i, (t, s1, s2, ic) in enumerate(cards):
        r, c = divmod(i, 2)
        x, y = x0 + c*(cw+gx), y0 + r*(ch+gy)
        d.rounded_rectangle([x, y, x+cw, y+ch], radius=18, fill=CARD, outline=ORANGE if i in (1,2) else EDGE, width=3)
        d.text((x+28, y+26), ic + " " + t, font=font(32, 1), fill=ORANGE)
        d.text((x+28, y+88), s1, font=font(26), fill=TXT)
        d.text((x+28, y+140), s2, font=font(21), fill=MID)
    save(im, "02-four-properties.png")

# ---------- 03 雪崩效应 ----------
def fig03():
    im, d = base("雪崩效应：改一个字，指纹翻脸", "「改不动」的物理基础")
    rows = [
        ("SHA-256(\"比特币\")",  hashlib.sha256("比特币".encode()).hexdigest(),  ORANGE),
        ("SHA-256(\"比特币！\")", hashlib.sha256("比特币！".encode()).hexdigest(), BLUE),
    ]
    y = 150
    for title, hx, col in rows:
        d.rounded_rectangle([80, y, 1200, y+130], radius=16, fill=CARD, outline=col, width=3)
        d.text((110, y+28), title, font=font(30, 1), fill=col)
        d.text((110, y+82), hx[:64], font=font(24, 1), fill=TXT)
        y += 180
    # 差异可视化：逐位对比
    a = rows[0][1]; b = rows[1][1]
    diff = sum(1 for x, y2 in zip(a, b) if x != y2)
    d.rounded_rectangle([80, 520, 1200, 600], radius=14, fill=(30, 24, 16))
    d.text((640, 545), f"64 个字符里 {diff} 个不同 · 输入只多了一个感叹号",
           font=font(28, 1), fill=GOLD, anchor="mm")
    d.text((640, 582), "新旧指纹之间看不出任何关联 —— 这就是「改一个字，链条全断」的原因",
           font=font(20), fill=MID, anchor="mm")
    save(im, "03-avalanche.png")

# ---------- 04 哈希 vs 加密（T1 表图） ----------
def fig04():
    im, d = base("常见误解：哈希 ≠ 加密", "T1 · 一张表分清")
    headers = ["", "哈希", "加密"]
    rows = [
        ("能不能还原", "不能 · 单向", "能 · 有密钥就能解"),
        ("要不要密钥", "不要", "要"),
        ("输出长度", "固定 64 字符", "跟输入差不多长"),
        ("典型用途", "校验完整性 · 指纹", "保密传输"),
    ]
    colx = [140, 470, 850]
    cw2 = [300, 340, 330]
    y = 130
    # 表头
    d.rounded_rectangle([100, y, 1180, y+70], radius=12, fill=(30, 24, 16))
    for j, htxt in enumerate(headers):
        if j:
            d.text((colx[j]+cw2[j]//2-100, y+35), htxt, font=font(30, 1), fill=ORANGE, anchor="mm")
    y += 86
    for i, (dim, a, b) in enumerate(rows):
        fill = CARD if i % 2 == 0 else (22, 22, 22)
        d.rounded_rectangle([100, y, 1180, y+86], radius=10, fill=fill)
        d.text((colx[0], y+43), dim, font=font(26, 1), fill=TXT, anchor="lm")
        d.text((colx[1]+cw2[1]//2-100, y+43), a, font=font(24), fill=GOLD, anchor="mm")
        d.text((colx[2]+cw2[2]//2-80, y+43), b, font=font(24), fill=(120, 180, 255), anchor="mm")
        y += 100
    d.rounded_rectangle([100, y+16, 1180, y+96], radius=14, fill=(30, 24, 16))
    d.text((640, y+56), "判断口诀：算完还能变回原文的，就不是哈希", font=font(28, 1),
           fill=ORANGE, anchor="mm")
    save(im, "04-hash-vs-encryption.png")

# ---------- 05 挖矿 = 全网掷骰子 ----------
def fig05():
    im, d = base("挖矿到底在算什么：掷骰子", "没有巧妙解法 · 纯暴力试错")
    tries = [
        ("nonce = 0",      "8f2a1c...", "❌ 开头不是 0", MID),
        ("nonce = 1",      "c71b9e...", "❌", MID),
        ("nonce = 2",      "03e97f...", "❌ 还不够小", MID),
        ("…",              "…", "", MID),
        ("nonce = 847293", "0000a3f2...", "✅ 中了！拿到记账权", GOLD),
    ]
    y = 130
    for nonce, hx, verdict, col in tries:
        d.rounded_rectangle([120, y, 1160, y+74], radius=12, fill=CARD,
                            outline=GOLD if "✅" in verdict else EDGE, width=3 if "✅" in verdict else 1)
        d.text((150, y+37), nonce, font=font(26, 1), fill=TXT, anchor="lm")
        d.text((520, y+37), "SHA-256 →  " + hx, font=font(24, 1), fill=ORANGE, anchor="lm")
        if verdict:
            d.text((1130, y+37), verdict, font=font(24), fill=col, anchor="rm")
        y += 90
    d.rounded_rectangle([120, y+10, 1160, y+96], radius=14, fill=(30, 24, 16))
    d.text((640, y+38), "难做：要试几百万次 ｜ 易验证：其他人代一遍 1 秒就知道真假",
           font=font(27, 1), fill=GOLD, anchor="mm")
    d.text((640, y+76), "算力即门票，但不保证收益 —— 这正是下一站「共识峰」的引子",
           font=font(20), fill=MID, anchor="mm")
    save(im, "05-mining-nonce.png")

# ---------- 07 三句话小结 ----------
def fig07():
    im, d = base("三句话带走本篇", "站5 · 哈希岭")
    items = [
        ("①", "哈希是指纹机，不是保险箱", "任意长度输入 → 固定 64 字符输出；它不藏内容，它盖章"),
        ("②", "四条性质撑起信任", "确定 · 单向 · 雪崩 · 抗碰撞 —— 缺一条，改不动的账本就不成立"),
        ("③", "挖矿 = 全网掷骰子", "改 nonce 撞出足够小的哈希；难做易验证，所以无裁判也能记账"),
    ]
    y = 130
    for num, t, s in items:
        d.rounded_rectangle([100, y, 1180, y+130], radius=18, fill=CARD, outline=EDGE, width=2)
        d.text((140, y+65), num, font=font(44, 1), fill=ORANGE, anchor="lm")
        d.text((220, y+44), t, font=font(30, 1), fill=TXT)
        d.text((220, y+92), s, font=font(22), fill=MID)
        y += 160
    save(im, "07-mindmap-summary.png")

FN = {"01": fig01, "02": fig02, "03": fig03, "04": fig04, "05": fig05, "07": fig07}
arg = sys.argv[1] if len(sys.argv) > 1 else "all"
if arg == "all":
    for k in FN: FN[k]()
else:
    FN[arg]()
