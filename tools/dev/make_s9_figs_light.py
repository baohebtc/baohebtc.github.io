# -*- coding: utf-8 -*-
"""
make_s9_figs_light.py — 站9「代码之巅」配图产线（paper-light / ADR-0008 + ADR-0013）
=====================================================================================
7 张全部走 brand_figs.Theme("paper-light")：色板/规格/字体/品牌三件套单一来源。
  01 它不是公司（层级 vs 无中心网）    16:9
  02 写它的人走了（退出时间线）        16:9
  03 改规则的三条路                    16:9
  04 T1 表图·规则真的被动过            4:3
  05 2100 万是算出来的                 16:9
  06 九站回望                          4:3
  07 三句话带走本篇                    16:9
用法：python3 make_s9_figs_light.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from brand_figs import (Theme, canvas, card, arrow, chip, save, font,
                        TOPBAR_H, FOOTBAR_H, R_BIG, R_SM)

TH = Theme("paper-light")
ROOT = pathlib.Path("/Users/mac/Desktop/宝盒知识库/比特币学习地图/慢读宝盒公众号")
OUT = ROOT / "站9-代码之巅" / "03-配图"

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
def s9_01():
    """01 它不是公司：层级金字塔 vs 无中心节点网。"""
    im, d = canvas(TH, "它不是公司 · 没有 CEO / 总部 / 拍板的人", "站9 · 代码之巅", size="16:9")
    W, H = im.size

    # 左：公司（金字塔）
    card(d, [90, TOPBAR_H + 36, 610, 578], TH, r=18)
    d.text((120, TOPBAR_H + 62), "公司", font=font(28, True), fill=TH.MID)
    d.text((196, TOPBAR_H + 68), "有一个能拍板的人", font=font(19), fill=TH.MID)
    lv = [("董事会", 300, 92), ("CEO / 管理层", 340, 92), ("员工 · 用户", 380, 92)]
    y = TOPBAR_H + 118
    for label, w_, h_ in lv:
        x0 = 350 - w_ // 2
        d.rounded_rectangle([x0, y, x0 + w_, y + h_], radius=10,
                            fill=TH.CARD_HI, outline=TH.EDGE, width=2)
        d.text((350, y + h_ // 2), label, font=font(23, True), fill=TH.TXT, anchor="mm")
        if label != "员工 · 用户":
            d.line([(350, y + h_), (350, y + h_ + 16)], fill=TH.EDGE, width=3)
        y += h_ + 16
    d.text((120, TOPBAR_H + 456), "规则由内部决定，改了就生效", font=font(20), fill=TH.MID)

    # 右：比特币（无中心网）
    card(d, [670, TOPBAR_H + 36, 1190, 578], TH, r=18)
    d.text((700, TOPBAR_H + 62), "比特币", font=font(28, True), fill=TH.ACCENT)
    d.text((778, TOPBAR_H + 68), "没有人能替所有人拍板", font=font(19), fill=TH.ACCENT)
    cx, cy = 930, TOPBAR_H + 250
    # 规则方块（中心不是人，是一份规则）
    d.rounded_rectangle([cx - 74, cy - 40, cx + 74, cy + 40], radius=10,
                        fill=TH.ACCENT)
    d.text((cx, cy - 16), "一份", font=font(21, True), fill=(255, 255, 255), anchor="mm")
    d.text((cx, cy + 18), "公开规则", font=font(21, True), fill=(255, 255, 255), anchor="mm")
    # 环绕节点
    import math
    nodes = []
    for i in range(8):
        a = -math.pi / 2 + i * math.pi / 4
        nx, ny = cx + 200 * math.cos(a), cy + 130 * math.sin(a)
        nodes.append((nx, ny))
    for i in range(8):
        x1, y1 = nodes[i]
        x2, y2 = nodes[(i + 1) % 8]
        d.line([(x1, y1), (x2, y2)], fill=TH.EDGE, width=2)
        d.line([(cx, cy), ((x1 + x2) / 2, (y1 + y2) / 2)], fill=TH.EDGE, width=1)
    for nx, ny in nodes:
        d.ellipse([nx - 22, ny - 22, nx + 22, ny + 22], fill=TH.CARD_HI,
                  outline=TH.ACCENT, width=2)
    d.text((700, TOPBAR_H + 476), "每家各自照着跑 · 改了要各自同意", font=font(20), fill=TH.MID)

    # 底部结论条
    d.rounded_rectangle([90, 590, 1190, 652], radius=R_SM,
                        fill=TH.CARD_HI, outline=TH.EDGE, width=2)
    d.text((640, 621), "没有人拥有它 · 也没有人能替所有人决定下一版规则",
           font=font(25, True), fill=TH.TXT, anchor="mm")
    save(im, OUT / "01-summit-intro.png")


# ─────────────────────────────────────────────────────────
def s9_02():
    """02 写它的人走了：中本聪退出时间线。"""
    im, d = canvas(TH, "写它的人走了 · 2010 年 12 月最后一次公开发言", "站9 · 代码之巅", size="16:9")
    W, H = im.size

    axis_y = TOPBAR_H + 190
    d.line([(110, axis_y), (1170, axis_y)], fill=TH.EDGE, width=4)
    # 尾部虚线（之后再无可验证消息）
    x = 1010
    while x < 1170:
        d.line([(x, axis_y), (x + 18, axis_y)], fill=TH.DIM, width=4)
        x += 34

    pts = [
        (190, "2008-10", "白皮书发布", TH.ACCENT),
        (420, "2009-01", "创世区块启动", TH.ACCENT),
        (650, "2010-12-12", "最后一次公开论坛发言", TH.ACCENT),
        (880, "2011-04", "\"I've moved on to other things.\"", RED),
        (1010, "2011-04-26", "请别把我塑造成神秘人物", RED),
    ]
    for i, (px, date, desc, col) in enumerate(pts):
        up = (i % 2 == 0)
        d.ellipse([px - 13, axis_y - 13, px + 13, axis_y + 13],
                  fill=col, outline=TH.CARD, width=3)
        d.line([(px, axis_y - 13 if up else axis_y + 13),
                (px, axis_y - 52 if up else axis_y + 52)], fill=col, width=3)
        ty = axis_y - 92 if up else axis_y + 66
        d.text((px, ty), date, font=font(23, True), fill=col, anchor="mm")
        wrap(d, desc, px - 105, ty + 32, 210, font(19), TH.TXT, 26, 2)

    d.text((1112, axis_y + 66), "之后", font=font(22, True), fill=TH.DIM, anchor="mm")
    d.text((1112, axis_y + 100), "再无可验证消息", font=font(18), fill=TH.DIM, anchor="mm")

    # 底部结论条
    d.rounded_rectangle([90, 590, 1190, 652], radius=R_SM,
                        fill=TH.CARD_HI, outline=TH.EDGE, width=2)
    d.text((640, 621), "它不是某个人的项目 · 它是一份被留下来、然后自己长大的规则",
           font=font(24, True), fill=TH.TXT, anchor="mm")
    save(im, OUT / "02-satoshi-exit.png")


# ─────────────────────────────────────────────────────────
def s9_03():
    """03 改规则的三条路（软分叉 / 硬分叉 / 只改自己的）。"""
    im, d = canvas(TH, "改规则的三条路 · 能改是技术问题，有人跟才是权力问题", "站9 · 代码之巅", size="16:9")
    W, H = im.size

    # 顶部：想改规则
    d.rounded_rectangle([452, TOPBAR_H + 28, 828, TOPBAR_H + 100], radius=R_SM,
                        fill=TH.ACCENT)
    d.text((640, TOPBAR_H + 64), "想改规则？技术上随时可以", font=font(26, True),
           fill=(255, 255, 255), anchor="mm")

    lanes = [
        (90, "路径一 · 收紧（软分叉）", "以前允许的事，现在有一部分不允许",
         "没升级的节点仍能接受", "同一条链，继续走", GREEN),
        (452, "路径二 · 放宽（硬分叉）", "以前不允许的事，现在允许了",
         "没升级的节点判定为非法", "链一分为二，各走各的", BLUE),
        (814, "路径三 · 只改自己的", "你改你的，跑你自己的那份",
         "没有别人跟过来", "不是改了它，是新开一条没人走的链", RED),
    ]
    for x0, title, l1, l2, res, col in lanes:
        card(d, [x0, TOPBAR_H + 140, x0 + 362, 566], TH, r=18)
        d.text((x0 + 22, TOPBAR_H + 164), title, font=font(23, True), fill=col)
        d.text((x0 + 22, TOPBAR_H + 214), l1, font=font(19), fill=TH.TXT)
        d.text((x0 + 22, TOPBAR_H + 250), l2, font=font(19), fill=TH.TXT)
        arrow(d, (x0 + 181, TOPBAR_H + 292), (x0 + 181, TOPBAR_H + 344), TH, width=4)
        d.rounded_rectangle([x0 + 22, TOPBAR_H + 356, x0 + 340, TOPBAR_H + 470],
                            radius=12, fill=TH.CARD_HI, outline=col, width=2)
        wrap(d, res, x0 + 42, TOPBAR_H + 382, 282, font(21, True), col, 30, 2)
        # 顶部连线
        d.line([(640, TOPBAR_H + 100), (640, TOPBAR_H + 124)], fill=TH.EDGE, width=3)
        d.line([(x0 + 181, TOPBAR_H + 124), (x0 + 181, TOPBAR_H + 140)], fill=TH.EDGE, width=3)
    d.line([(271, TOPBAR_H + 124), (1009, TOPBAR_H + 124)], fill=TH.EDGE, width=3)

    # 底部结论条
    d.rounded_rectangle([90, 590, 1190, 652], radius=R_SM,
                        fill=TH.CARD_HI, outline=TH.EDGE, width=2)
    d.text((640, 621), "「谁也改不了」的准确含义：没有人能替所有人改",
           font=font(25, True), fill=TH.TXT, anchor="mm")
    save(im, OUT / "03-three-paths.png")


# ─────────────────────────────────────────────────────────
def s9_04():
    """04 T1 表图：规则真的被动过（5 行）。"""
    im, d = canvas(TH, "T1 · 发生过什么 · 规则真的被动过", "站9 · 代码之巅", size="4:3")
    W, H = im.size
    rows = [
        ("2010-08-15", "区块 74638 凭空造出 1844 亿枚（整数溢出）",
         "数小时内发 0.3.10；好链在 74691 反超，坏链被丢弃", "事故修复（回滚）", RED),
        ("2013-03-11", "区块 225430 让新旧版本判断不一致，链一分为二",
         "矿池主动退回旧版本、让网络重组；事后 BIP50 复盘", "事故修复（回滚）", RED),
        ("2017-08-01", "主张大区块的一边正式分出去",
         "变成两条链各自运行，各自带防重放机制", "硬分叉（分家）", BLUE),
        ("2017-08-24", "SegWit 在区块 481824 激活",
         "节点与矿工信号逐步锁定，旧节点仍在同一条链上", "软分叉（升级）", GREEN),
        ("2021-11-14", "Taproot 在区块 709632 激活",
         "三个月信号窗口达 90% 才生效，并留出升级时间", "软分叉（升级）", GREEN),
    ]
    x0, x1 = 70, 1210
    cx_a, cx_b, cx_c, cx_d = 92, 268, 640, 962
    y = TOPBAR_H + 10

    d.rounded_rectangle([x0, y, x1, y + 50], radius=R_SM, fill=TH.CARD_HI,
                        outline=TH.EDGE, width=2)
    for cx, label in ((cx_a, "时间"), (cx_b, "发生了什么"), (cx_c, "怎么收场的"), (cx_d, "属于哪一类")):
        d.text((cx, y + 25), label, font=font(22, True), fill=TH.MID, anchor="lm")
    y += 66

    for i, (a, b, c, e, col) in enumerate(rows):
        h = 128
        d.rounded_rectangle([x0, y, x1, y + h], radius=12,
                            fill=TH.CARD if i % 2 == 0 else TH.CARD_HI,
                            outline=TH.EDGE, width=1)
        d.rectangle([x0 + 6, y + 16, x0 + 11, y + h - 16], fill=col)
        d.text((cx_a, y + 22), a, font=font(21, True), fill=TH.TXT)
        wrap(d, b, cx_b, y + 20, 350, font(20), TH.TXT, 28, 3)
        wrap(d, c, cx_c, y + 20, 300, font(19), TH.TXT, 27, 3)
        chip(d, (cx_d, y + 22), TH, e, fs=19, color=col, bg=TH.CARD)
        y += h + 10

    d.text(((x0 + x1) // 2, H - FOOTBAR_H - 42),
           "每一次都不是谁下令做的 · 都是有人提方案、公开讨论、大家各自选择装不装",
           font=font(22, True), fill=TH.MID, anchor="mm")
    save(im, OUT / "04-t1-rule-changes-table.png")


# ─────────────────────────────────────────────────────────
def s9_05():
    """05 2100 万是算出来的：两条规则 → 收敛出上限。"""
    im, d = canvas(TH, "2100 万是算出来的 · 不是写死的参数", "站9 · 代码之巅", size="16:9")
    W, H = im.size

    # 左：两条规则
    card(d, [90, TOPBAR_H + 40, 560, 470], TH, r=18)
    d.text((120, TOPBAR_H + 66), "规则只有两条", font=font(26, True), fill=TH.ACCENT)
    d.rounded_rectangle([120, TOPBAR_H + 108, 530, TOPBAR_H + 178], radius=10,
                        fill=TH.CARD_HI, outline=TH.EDGE, width=2)
    d.text((140, TOPBAR_H + 140), "① 每个新区块：产生 50 枚", font=font(21), fill=TH.TXT)
    d.rounded_rectangle([120, TOPBAR_H + 196, 530, TOPBAR_H + 268], radius=10,
                        fill=TH.CARD_HI, outline=TH.EDGE, width=2)
    wrap(d, "② 每过 210,000 个区块：奖励减半", 140, TOPBAR_H + 212, 370,
         font(21), TH.TXT, 28, 2)
    d.text((120, TOPBAR_H + 306), "代码里没有一句", font=font(21), fill=TH.MID)
    d.text((120, TOPBAR_H + 344), "「总量 = 2100 万」", font=font(24, True), fill=RED)

    # 中：序列
    seq = ["50", "25", "12.5", "6.25", "3.125", "…"]
    sx = 620
    for i, v in enumerate(seq):
        yy = TOPBAR_H + 74 + i * 54
        d.rounded_rectangle([sx, yy, sx + 150, yy + 44], radius=8,
                            fill=TH.CARD_HI, outline=TH.EDGE, width=2)
        d.text((sx + 75, yy + 22), v, font=font(22, True), fill=TH.TXT, anchor="mm")
        if i < len(seq) - 1:
            d.line([(sx + 75, yy + 44), (sx + 75, yy + 62)], fill=TH.ACCENT, width=3)
    arrow(d, (600, TOPBAR_H + 236), (612, TOPBAR_H + 236), TH, width=4)

    # 右：收敛
    card(d, [800, TOPBAR_H + 40, 1190, 470], TH, r=18)
    d.text((830, TOPBAR_H + 66), "一直加下去，会收敛到", font=font(24, True), fill=GREEN)
    d.text((830, TOPBAR_H + 140), "≈ 2100 万", font=font(58, True), fill=GREEN)
    d.text((830, TOPBAR_H + 234), "实际天花板约 20,999,999.9769 枚",
           font=font(19), fill=TH.MID)
    d.rounded_rectangle([830, TOPBAR_H + 258, 1160, TOPBAR_H + 336], radius=10,
                        fill=GREEN_BG, outline=GREEN, width=2)
    wrap(d, "要改它，得说服所有节点接受另一套算术", 850, TOPBAR_H + 274, 290,
         font(20, True), GREEN, 27, 2)

    # 底部结论条
    d.rounded_rectangle([90, 500, 1190, 570], radius=R_SM,
                        fill=TH.CARD_HI, outline=TH.EDGE, width=2)
    d.text((640, 535), "2100 万不是一个被写下来的数字 · 它是那两条规则算出来的结果",
           font=font(25, True), fill=TH.TXT, anchor="mm")
    save(im, OUT / "05-21m-emergent.png")


# ─────────────────────────────────────────────────────────
def s9_06():
    """06 九站回望：从「钱是什么」走到「规则是什么」。"""
    im, d = canvas(TH, "九站回望 · 从「钱是什么」走到「规则是什么」", "站9 · 代码之巅", size="4:3")
    W, H = im.size
    rows = [
        ("站1", "现金湾", "想成为什么：不靠某个机构也能转移的价值"),
        ("站1.5", "钱到底是什么", "退一步问：钱凭什么是钱"),
        ("站2", "银行堡", "看清它要取代的东西有什么缺陷"),
        ("站3", "双花峡", "数字世界真正的难题：同一笔钱别被花两次"),
        ("站4", "账本海", "前一半答案：人人各拿一本公开账本"),
        ("站5", "哈希岭", "后一半答案：让改动的代价高到不划算"),
        ("站6", "共识峰", "账本有很多份时，以哪份为准"),
        ("站7", "矿工谷", "谁在提供这份工作量，能做什么、做不到什么"),
        ("站8", "私钥崖", "凭什么说是你的：那串字符与全部责任"),
        ("站9", "代码之巅", "收口：它不是机构，是一套公开规则"),
    ]
    y = TOPBAR_H + 18
    for i, (num, name, desc) in enumerate(rows):
        col = 0 if i < 5 else 1
        row = i % 5
        x0 = 70 if col == 0 else 660
        yy = y + row * 150
        cur = (i == 9)
        card(d, [x0, yy, x0 + 560, yy + 132], TH, hi=cur, r=14)
        ncol = TH.ACCENT if cur else TH.MID
        d.text((x0 + 22, yy + 30), num, font=font(22, True), fill=ncol, anchor="lm")
        d.text((x0 + 92, yy + 30), name, font=font(26, True),
               fill=TH.ACCENT if cur else TH.TXT, anchor="lm")
        wrap(d, desc, x0 + 22, yy + 72, 516, font(20), TH.TXT, 28, 2)
        if cur:
            chip(d, (x0 + 400, yy + 18), TH, "本站 · 到顶", fs=18,
                 color=TH.ACCENT, bg=TH.CARD_HI)

    d.text((640, H - FOOTBAR_H - 42),
           "它立得住，靠的不是没人能改它 · 而是改它的人说服不了所有人",
           font=font(23, True), fill=TH.MID, anchor="mm")
    save(im, OUT / "06-nine-stations-recap.png")


# ─────────────────────────────────────────────────────────
def s9_07():
    """07 三句话带走本篇。"""
    im, d = canvas(TH, "三句话带走本篇", "站9 · 代码之巅", size="16:9")
    items = [
        ("①", "它不是公司，是一套公开规则", "没有 CEO、没有总部，写它的人十五年前就退出了"),
        ("②", "改得了，但没人跟你走", "改代码很自由；让全网接受才是门槛"),
        ("③", "立得住靠认同，不靠禁止", "不是没人能改，是改的人说服不了所有人"),
    ]
    y = TOPBAR_H + 52
    for num, t, s in items:
        card(d, [100, y, 1180, y + 132], TH, r=18)
        d.text((140, y + 66), num, font=font(44, True), fill=TH.ACCENT, anchor="lm")
        d.text((220, y + 40), t, font=font(29, True), fill=TH.TXT)
        d.text((220, y + 94), s, font=font(20), fill=TH.MID)
        y += 160
    save(im, OUT / "08-mindmap-summary.png")


FN = [s9_01, s9_02, s9_03, s9_04, s9_05, s9_06, s9_07]
for f in FN:
    f()
print(f"done: {len(FN)} figs (paper-light) -> {OUT}")
