# -*- coding: utf-8 -*-
"""
make_s8_figs_light.py — 站8「私钥崖」配图产线（paper-light / ADR-0008 + ADR-0012）
=====================================================================================
7 张全部走 brand_figs.Theme("paper-light")：色板/规格/字体/品牌三件套单一来源。
  01 私钥崖（没有护栏的小路）        16:9
  02 T1 表图·保管权的三次交出        4:3
  03 这串数字有多大（2^256）         16:9
  04 从一堆散钥匙到一棵种子树        16:9
  05 签名不是加密                    16:9
  06 崖下三个真实故事                16:9
  07 三句话带走本篇                  16:9
用法：python3 make_s8_figs_light.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from brand_figs import (Theme, canvas, card, arrow, chip, save, font,
                        TOPBAR_H, FOOTBAR_H, R_BIG, R_SM)

TH = Theme("paper-light")
ROOT = pathlib.Path("/Users/mac/Desktop/宝盒知识库/比特币学习地图/慢读宝盒公众号")
OUT = ROOT / "站8-私钥崖" / "03-配图"

# 浅底语义色（ADR-0008：语义色唯一来源）
RED, RED_BG = (198, 40, 40), (250, 235, 232)
GREEN, GREEN_BG = (27, 122, 80), (233, 244, 238)
BLUE, BLUE_BG = (58, 124, 186), (233, 241, 248)


def wrap(d, text, x, y, maxw, f, fill, lh, max_lines=3):
    """按像素宽度折行（PingFang 无特殊字形，禁用表情符号）。"""
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
        d.text((x, y + i * lh), ln, font=f, fill=fill)
    return y + len(lines) * lh


# ─────────────────────────────────────────────────────────
def s8_01():
    """01 私钥崖：没有护栏的小路（拿回判定权 vs 摔下去没人捞）。"""
    im, d = canvas(TH, "私钥崖 · 一条没有护栏的小路", "站8 · 私钥崖", size="16:9")
    W, H = im.size

    # 山脊曲线（多边形填充表示山体）
    pts = [(120, 560), (300, 430), (470, 480), (640, 330),
           (820, 400), (990, 300), (1160, 380), (1160, 600), (120, 600)]
    d.polygon(pts, fill=TH.CARD_HI)
    d.line([(120, 560), (300, 430), (470, 480), (640, 330),
            (820, 400), (990, 300), (1160, 380)], fill=TH.EDGE, width=4)

    # 顶部：没有客服
    d.rounded_rectangle([380, TOPBAR_H + 26, 900, TOPBAR_H + 96],
                        radius=R_SM, fill=TH.CARD, outline=TH.ACCENT, width=2)
    d.text((640, TOPBAR_H + 61), "没有客服 · 没有挂失 · 没有找回",
           font=font(27, True), fill=TH.ACCENT, anchor="mm")

    # 左下：拿到什么
    card(d, [110, 470, 560, 596], TH, r=16)
    d.text((140, 500), "你拿回的东西", font=font(23, True), fill=GREEN)
    d.text((140, 540), "判定权：谁能动这笔钱，由数学说了算",
           font=font(21), fill=TH.TXT)

    # 右下：代价
    card(d, [720, 470, 1170, 596], TH, r=16)
    d.text((750, 500), "同时接过来的代价", font=font(23, True), fill=RED)
    d.text((750, 540), "责任：摔下去，没有人来捞你",
           font=font(21), fill=TH.TXT)

    # 中间竖线分隔（悬崖的"边"）
    d.line([640, 470, 640, 596], fill=TH.EDGE, width=2)
    save(im, OUT / "01-cliff-intro.png")


# ─────────────────────────────────────────────────────────
def s8_02():
    """02 T1 表图：保管权的三次交出（4:3）。"""
    im, d = canvas(TH, "T1 · 保管权的三次交出", "站8 · 私钥崖", size="4:3")
    W, H = im.size
    rows = [
        ("自己拿着（实物）", "——", "无需信任任何人", "抢、偷、搬不动、无法远程"),
        ("交给记账人", "\"谁有多少\"的判定权", "可远程、可清算、可追责", "记录者的诚实与能力"),
        ("交给保管人", "实物本身", "看管、支付便利、利息", "偿付能力 · 被冻结的可能"),
        ("交给屏幕", "全部", "即时到账、跨地域", "系统可用性 · 机构信用 · 审查没收"),
    ]
    x0, x1 = 90, 1190
    cx_a, cx_b, cx_c, cx_d = 112, 400, 640, 900
    y = TOPBAR_H + 12

    d.rounded_rectangle([x0, y, x1, y + 54], radius=R_SM, fill=TH.CARD_HI,
                        outline=TH.EDGE, width=2)
    d.text((cx_a, y + 27), "阶段", font=font(23, True), fill=TH.MID, anchor="lm")
    d.text((cx_b, y + 27), "交出什么", font=font(23, True), fill=TH.MID, anchor="lm")
    d.text((cx_c, y + 27), "换来什么", font=font(23, True), fill=TH.MID, anchor="lm")
    d.text((cx_d, y + 27), "风险转移到哪", font=font(23, True), fill=TH.ACCENT, anchor="lm")
    y += 72

    for i, (a, b, c, e) in enumerate(rows):
        h = 132
        bg = TH.CARD if i % 2 == 0 else TH.CARD_HI
        d.rounded_rectangle([x0, y, x1, y + h], radius=12, fill=bg,
                            outline=TH.EDGE, width=1)
        accent = GREEN if i == 0 else (TH.ACCENT if i == 3 else TH.MID)
        d.rectangle([x0 + 6, y + 18, x0 + 11, y + h - 18], fill=accent)
        wrap(d, a, x0 + 26, y + 24, 250, font(22, True), TH.TXT, 30, 2)
        wrap(d, b, cx_b, y + 40, 215, font(21), TH.TXT, 30, 2)
        wrap(d, c, cx_c, y + 24, 235, font(21), TH.TXT, 30, 2)
        wrap(d, e, cx_d, y + 24, 270, font(21), TH.MID, 30, 2)
        y += h + 14

    d.text(((x0 + x1) // 2, y + 26),
           "两千年里交出去三次 · 每一步都用风险换来了便利",
           font=font(23, True), fill=TH.MID, anchor="mm")
    save(im, OUT / "02-t1-custody-history-table.png")


# ─────────────────────────────────────────────────────────
def s8_03():
    """03 这串数字有多大：2^256 与宇宙原子数同一把尺子。"""
    im, d = canvas(TH, "这串数字有多大 · 2^256", "站8 · 私钥崖", size="16:9")
    W, H = im.size

    # 左卡：私钥总数
    card(d, [100, TOPBAR_H + 44, 610, 430], TH, r=R_BIG)
    d.text((150, TOPBAR_H + 82), "私钥的可能取值", font=font(24, True), fill=TH.MID)
    d.text((150, TOPBAR_H + 156), "2^256", font=font(64, True), fill=TH.ACCENT)
    d.text((150, TOPBAR_H + 226), "≈ 1.16 × 10^77", font=font(30), fill=TH.TXT)
    d.text((150, TOPBAR_H + 286), "1 后面跟着 77 个零", font=font(21), fill=TH.MID)

    # 右卡：宇宙原子数
    card(d, [670, TOPBAR_H + 44, 1180, 430], TH, r=R_BIG)
    d.text((720, TOPBAR_H + 82), "可观测宇宙的原子总数", font=font(24, True), fill=TH.MID)
    d.text((720, TOPBAR_H + 156), "≈ 10^80", font=font(64, True), fill=BLUE)
    d.text((720, TOPBAR_H + 226), "同一把尺子", font=font(30), fill=TH.TXT)
    d.text((720, TOPBAR_H + 286), "私钥总数还比它少约三个数量级",
           font=font(21), fill=TH.MID)

    # 底部结论
    d.rounded_rectangle([100, 470, 1180, 566], radius=R_SM,
                        fill=TH.CARD_HI, outline=TH.EDGE, width=2)
    d.text((640, 498), "所以「猜不出来」不是修辞，是物理结论",
           font=font(26, True), fill=TH.TXT, anchor="mm")
    d.text((640, 540), "真正被突破的从来不是这个数字 · 而是人：随机数不够随机、私钥存联网、被骗走",
           font=font(20), fill=RED, anchor="mm")
    save(im, OUT / "03-key-scale.png")


# ─────────────────────────────────────────────────────────
def s8_04():
    """04 从一堆散钥匙到一棵种子树（BIP32 / BIP39）。"""
    im, d = canvas(TH, "从一堆散钥匙到一棵种子树", "站8 · 私钥崖", size="16:9")
    W, H = im.size

    # 左：2009–2012 散钥匙
    card(d, [90, TOPBAR_H + 34, 590, 540], TH, r=18)
    d.text((120, TOPBAR_H + 62), "2009–2012 · 一堆散钥匙", font=font(25, True), fill=RED)
    d.text((120, TOPBAR_H + 100), "每要一个新地址，就随机生成一把新私钥",
           font=font(19), fill=TH.MID)
    # 散钥匙格子
    gx, gy = 120, TOPBAR_H + 132
    for i in range(12):
        cx = gx + (i % 6) * 74
        cy = gy + (i // 6) * 62
        late = i >= 8   # 后 4 把 = 超出备份的新钥匙
        d.rounded_rectangle([cx, cy, cx + 58, cy + 44], radius=8,
                            fill=RED_BG if late else TH.CARD_HI,
                            outline=RED if late else TH.EDGE, width=2 if late else 1)
        d.text((cx + 29, cy + 22), "k%d" % (i + 1), font=font(18, True),
               fill=RED if late else TH.MID, anchor="mm")
    d.text((120, TOPBAR_H + 276), "wallet.dat 密钥池只预留 100 把",
           font=font(20), fill=TH.TXT)
    d.rounded_rectangle([120, TOPBAR_H + 308, 560, TOPBAR_H + 366], radius=10,
                        fill=RED_BG, outline=RED, width=2)
    d.text((140, TOPBAR_H + 337), "转账还会自动生成找零地址 →",
           font=font(20, True), fill=RED)
    d.text((140, TOPBAR_H + 371), "超出 100 把之后的新钥匙，不在备份里",
           font=font(20, True), fill=RED)
    d.text((120, TOPBAR_H + 424), "硬盘一坏，用旧备份恢复 → 那部分币没了",
           font=font(19), fill=TH.MID)

    # 右：2012 起 种子树
    card(d, [690, TOPBAR_H + 34, 1190, 540], TH, r=18)
    d.text((720, TOPBAR_H + 62), "2012 起 · 一棵种子树（BIP32）",
           font=font(25, True), fill=GREEN)
    d.text((720, TOPBAR_H + 100), "一个种子，按固定规则推导全部钥匙",
           font=font(19), fill=TH.MID)
    # 种子
    seed_cx, seed_y = 940, TOPBAR_H + 150
    d.ellipse([seed_cx - 92, seed_y - 32, seed_cx + 92, seed_y + 32],
              fill=TH.ACCENT)
    d.text((seed_cx, seed_y), "种子 Seed", font=font(24, True),
           fill=(255, 255, 255), anchor="mm")
    # 分支
    branches_y = TOPBAR_H + 262
    for i, (bx, label) in enumerate([(790, "地址 1"), (940, "地址 2"), (1090, "地址 3")]):
        d.line([(seed_cx, seed_y + 32), (bx + 50, branches_y - 20)],
               fill=TH.EDGE, width=3)
        d.rounded_rectangle([bx, branches_y - 20, bx + 100, branches_y + 24],
                            radius=8, fill=GREEN_BG, outline=GREEN, width=2)
        d.text((bx + 50, branches_y + 2), label, font=font(19, True),
               fill=GREEN, anchor="mm")
    d.text((720, TOPBAR_H + 324), "再下一层还能继续分（分层确定性）",
           font=font(19), fill=TH.MID)
    d.rounded_rectangle([720, TOPBAR_H + 356, 1160, TOPBAR_H + 414], radius=10,
                        fill=GREEN_BG, outline=GREEN, width=2)
    d.text((740, TOPBAR_H + 385), "备份一次，就能重新长出所有钥匙",
           font=font(21, True), fill=GREEN)
    d.text((720, TOPBAR_H + 448), "2013 BIP39：种子 → 12/24 个英文单词（2048 词表）",
           font=font(19), fill=TH.TXT)

    # 中间箭头
    arrow(d, (600, TOPBAR_H + 285), (676, TOPBAR_H + 285), TH, width=5)
    save(im, OUT / "04-seed-tree.png")


# ─────────────────────────────────────────────────────────
def s8_05():
    """05 签名不是加密：一个藏内容，一个盖印章。"""
    im, d = canvas(TH, "签名不是加密", "站8 · 私钥崖", size="16:9")
    W, H = im.size

    # 左：加密
    card(d, [100, TOPBAR_H + 40, 600, 500], TH, r=R_BIG)
    d.text((140, TOPBAR_H + 78), "加密 Encryption", font=font(27, True), fill=BLUE)
    d.text((140, TOPBAR_H + 122), "把内容藏起来", font=font(22), fill=TH.TXT)
    # 信封
    d.rounded_rectangle([150, TOPBAR_H + 160, 550, TOPBAR_H + 280], radius=10,
                        fill=BLUE_BG, outline=BLUE, width=2)
    d.text((350, TOPBAR_H + 220), "原文 → 密文", font=font(26, True),
           fill=BLUE, anchor="mm")
    d.text((350, TOPBAR_H + 258), "看到的人读不懂，需要解密",
           font=font(19), fill=TH.MID, anchor="mm")
    d.text((140, TOPBAR_H + 330), "目的：保密", font=font(23, True), fill=BLUE)
    d.text((140, TOPBAR_H + 380), "链上不适用 —— 比特币账本是全公开的",
           font=font(19), fill=TH.MID)

    # 右：签名
    card(d, [680, TOPBAR_H + 40, 1180, 500], TH, r=R_BIG)
    d.text((720, TOPBAR_H + 78), "签名 Signature", font=font(27, True), fill=TH.ACCENT)
    d.text((720, TOPBAR_H + 122), "给内容盖一个章", font=font(22), fill=TH.TXT)
    # 文件 + 印章
    d.rounded_rectangle([730, TOPBAR_H + 160, 1130, TOPBAR_H + 280], radius=10,
                        fill=TH.CARD_HI, outline=TH.ACCENT, width=2)
    d.text((930, TOPBAR_H + 200), "「我把这笔钱转给谁」· 内容公开可见",
           font=font(21, True), fill=TH.TXT, anchor="mm")
    d.text((930, TOPBAR_H + 244), "＋ 一个用私钥生成的数学标记",
           font=font(21), fill=TH.ACCENT, anchor="mm")
    d.text((720, TOPBAR_H + 330), "目的：证明授权，不隐藏内容",
           font=font(23, True), fill=TH.ACCENT)
    d.text((720, TOPBAR_H + 380), "任何人都能用公钥验证真伪 · 但谁也伪造不了",
           font=font(19), fill=TH.MID)

    # 底部提示
    d.rounded_rectangle([100, 520, 1180, 610], radius=R_SM,
                        fill=TH.CARD_HI, outline=TH.EDGE, width=2)
    d.text((640, 548), "钱包 App 的密码，保护的是你手机上的文件 —— 不是链上的币",
           font=font(25, True), fill=TH.TXT, anchor="mm")
    d.text((640, 590), "别人拿到种子词，不需要知道你的 App 密码，也能在别处转走",
           font=font(19), fill=RED, anchor="mm")
    save(im, OUT / "05-sign-not-encrypt.png")


# ─────────────────────────────────────────────────────────
def s8_06():
    """06 崖下三个真实故事（只报 BTC 数量，不写估值）。"""
    im, d = canvas(TH, "崖下三个真实故事", "站8 · 私钥崖", size="16:9")
    W, H = im.size
    items = [
        ("故事一 · 一块硬盘", "2013 · 英国", "清理房子时扔掉一块旧硬盘，",
         "里面是约 7500 枚的私钥", "硬盘进了垃圾场 · 挖掘申请十余年未获准 · 币在链上，看得见动不了", RED),
        ("故事二 · 一个密码", "IronKey 加密盘", "密码写在纸上，纸找不到了",
         "只剩 2 次尝试机会", "内含 7002 枚 · 本人公开提醒：定期测试备份是不是还能用", RED),
        ("故事三 · 一张欠条", "托管平台暴雷", "私钥没丢 —— 他们从来就没有过私钥",
         "手里只有账户里的一行数字", "看得见的余额，不等于能动的币", BLUE),
    ]
    y = TOPBAR_H + 30
    for title, tag, l1, l2, note, col in items:
        h = 152
        card(d, [100, y, 1180, y + h], TH, r=16)
        d.rectangle([100, y + 16, 106, y + h - 16], fill=col)
        d.text((130, y + 34), title, font=font(26, True), fill=TH.TXT)
        chip(d, (975, y + 30), TH, tag, fs=18, color=TH.MID, bg=TH.CARD_HI)
        d.text((130, y + 84), l1, font=font(21), fill=TH.TXT)
        d.text((130, y + 114), "　　" + l2, font=font(21, True), fill=col)
        d.text((640, y + 84), note, font=font(19), fill=TH.MID)
        y += h + 16

    d.text((640, y + 6), "链上永久丢失估计：287 万 – 379 万枚（占已开采量 17%–23%）· 这是一个关于人的数字",
           font=font(20, True), fill=TH.MID, anchor="mm")
    save(im, OUT / "06-lost-stories.png")


# ─────────────────────────────────────────────────────────
def s8_07():
    """07 三句话带走本篇。"""
    im, d = canvas(TH, "三句话带走本篇", "站8 · 私钥崖", size="16:9")
    items = [
        ("①", "保管权交出去过三次", "实物 → 记账人 → 保管人 → 屏幕；2009 年首次拿回来"),
        ("②", "数学厚得离谱，人是纸糊的", "2^256 硬猜不可能；历史上丢币几乎都绕开了数学这道墙"),
        ("③", "看得见不等于能动", "交易所余额是平台对你的负债；没有私钥就没有那笔币"),
    ]
    y = TOPBAR_H + 52
    for num, t, s in items:
        card(d, [100, y, 1180, y + 132], TH, r=18)
        d.text((140, y + 66), num, font=font(44, True), fill=TH.ACCENT, anchor="lm")
        d.text((220, y + 40), t, font=font(29, True), fill=TH.TXT)
        d.text((220, y + 94), s, font=font(20), fill=TH.MID)
        y += 160
    save(im, OUT / "07-mindmap-summary.png")


FN = [s8_01, s8_02, s8_03, s8_04, s8_05, s8_06, s8_07]
for f in FN:
    f()
print(f"done: {len(FN)} figs (paper-light) -> {OUT}")
