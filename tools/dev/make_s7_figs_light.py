# -*- coding: utf-8 -*-
"""
make_s7_figs_light.py — 站7「矿工谷」配图产线（paper-light / ADR-0008 + ADR-0011）
=====================================================================================
7 张全部走 brand_figs.Theme("paper-light")：色板/规格/字体/品牌三件套单一来源。
  01 矿工到底在干什么（掷骰子）    16:9
  02 T1 表图·区块补贴减半时间表     4:3
  03 难度自动校准闭环              16:9
  04 矿机四代进化                  16:9
  05 矿池份额怎么分账              16:9
  06 矿池不拥有算力（误解纠正）     16:9
  07 三句话小结                    16:9
用法：python3 make_s7_figs_light.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from brand_figs import (Theme, canvas, card, arrow, chip, save, font,
                        TOPBAR_H, FOOTBAR_H, R_BIG, R_SM)

TH = Theme("paper-light")
ROOT = pathlib.Path("/Users/mac/Desktop/宝盒知识库/比特币学习地图/慢读宝盒公众号")
OUT = ROOT / "站7-矿工谷" / "03-配图"

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


def footer_note(d, W, H, text):
    """底部结论条（合规条之上，带底块，全站样式统一）。"""
    fy = H - FOOTBAR_H - 76
    d.rounded_rectangle([90, fy, W - 90, fy + 56], radius=R_SM,
                        fill=TH.CARD_HI, outline=TH.EDGE, width=2)
    d.text((W // 2, fy + 28), text, font=font(22, True),
           fill=TH.TXT, anchor="mm")


# ─────────────────────────────────────────────────────────
def s7_01():
    """01 矿工到底在干什么：不是解数学题，是掷骰子。"""
    im, d = canvas(TH, "矿工到底在干什么", "站7 · 矿工谷", size="16:9")
    W, H = im.size
    y = TOPBAR_H + 40

    # 误区 vs 正解
    card(d, [90, y, 620, y + 108], TH, fill=RED_BG, edge=RED, r=16)
    d.text((110, y + 24), "常见说法", font=font(21, True), fill=RED)
    d.text((110, y + 60), "矿工在「解一道复杂的数学题」", font=font(24), fill=TH.TXT)
    card(d, [660, y, 1190, y + 108], TH, hi=True, r=16)
    d.text((680, y + 24), "实际情况", font=font(21, True), fill=TH.ACCENT)
    d.text((680, y + 60), "矿工在没完没了地掷骰子", font=font(24), fill=TH.TXT)
    y += 128

    # 三步流程
    steps = [
        ("① 打包", "把这一批待确认的交易打包好"),
        ("② 加数", "再填一个随便的数字"),
        ("③ 哈希", "整体做一次哈希，看结果是否落在极小范围"),
    ]
    x = 90
    for i, (t, s) in enumerate(steps):
        card(d, [x, y, x + 340, y + 132], TH, r=16)
        d.text((x + 22, y + 26), t, font=font(26, True), fill=TH.ACCENT)
        wrap(d, s, x + 22, y + 68, 300, font(20), TH.TXT, 28, 2)
        if i < 2:
            arrow(d, (x + 348, y + 66), (x + 392, y + 66), TH, width=3)
        x += 400
    y += 160

    # 判定分叉
    card(d, [90, y, 590, y + 106], TH, fill=RED_BG, edge=RED, r=16)
    d.text((112, y + 30), "不合格（绝大多数）", font=font(24, True), fill=RED)
    d.text((112, y + 66), "把那个数字换一个，从头再来", font=font(20), fill=TH.TXT)
    card(d, [690, y, 1190, y + 106], TH, hi=True, r=16)
    d.text((712, y + 30), "合格（极小概率）", font=font(24, True), fill=TH.ACCENT)
    d.text((712, y + 66), "广播出去，这一页账归你写", font=font(20), fill=TH.TXT)

    # 回到第②步的回环箭头
    arrow(d, (340, y), (340, y - 26), TH, width=3)
    d.line([(340, y - 26), (500, y - 26)], fill=TH.ACCENT, width=3)
    arrow(d, (500, y - 26), (500, y - 2), TH, width=3)

    footer_note(d, W, H, "没有公式可以倒推，没有捷径可以抄——只能一遍一遍试")
    save(im, OUT / "01-miner-job.png")


# ─────────────────────────────────────────────────────────
def s7_02():
    """02 T1 表图：区块补贴减半时间表（4:3）。"""
    im, d = canvas(TH, "T1 · 区块补贴减半时间表", "站7 · 矿工谷", size="4:3")
    W, H = im.size
    rows = [
        ("2009 年 1 月", "0", "50"),
        ("2012 年 11 月", "210,000", "25"),
        ("2016 年 7 月", "420,000", "12.5"),
        ("2020 年 5 月", "630,000", "6.25"),
        ("2024 年 4 月", "840,000", "3.125"),
        ("预计 2028 年", "1,050,000", "1.5625"),
    ]
    x0, x1 = 110, 1180
    cx_t, cx_h, cx_v = 140, 520, 880
    y = TOPBAR_H + 14

    d.rounded_rectangle([x0, y, x1, y + 52], radius=R_SM, fill=TH.CARD_HI,
                        outline=TH.EDGE, width=2)
    d.text((cx_t, y + 26), "时间", font=font(23, True), fill=TH.MID, anchor="lm")
    d.text((cx_h, y + 26), "区块高度", font=font(23, True), fill=TH.MID, anchor="lm")
    d.text((cx_v, y + 26), "每块新铸造（枚）", font=font(23, True), fill=TH.ACCENT, anchor="lm")
    y += 68

    for i, (tm, hh, vv) in enumerate(rows):
        h = 98
        bg = TH.CARD if i % 2 == 0 else TH.CARD_HI
        d.rounded_rectangle([x0, y, x1, y + h], radius=12, fill=bg,
                            outline=TH.EDGE, width=1)
        # 递降条：按 50 为满宽，越往下越短
        ratio = float(vv.replace(",", "")) / 50.0
        bar_w = int(180 * (ratio ** 0.45))
        d.rectangle([x0 + 6, y + 16, x0 + 11, y + h - 16], fill=TH.ACCENT)
        d.text((cx_t, y + h // 2), tm, font=font(22, True), fill=TH.TXT, anchor="lm")
        d.text((cx_h, y + h // 2), hh, font=font(22), fill=TH.TXT, anchor="lm")
        d.rounded_rectangle([cx_v, y + 30, cx_v + max(bar_w, 40), y + 62],
                            radius=6, fill=TH.ACCENT)
        d.text((cx_v + max(bar_w, 40) + 16, y + 46), vv, font=font(26, True),
               fill=TH.TXT, anchor="lm")
        y += h + 10

    footer_note(d, W, H, "每 210,000 块砍一半 · 写死在代码里 · 2140 年前后归零")
    save(im, OUT / "02-t1-subsidy-halving-table.png")


# ─────────────────────────────────────────────────────────
def s7_03():
    """03 难度自动校准闭环。"""
    im, d = canvas(TH, "难度怎么自动校准", "站7 · 矿工谷", size="16:9")
    W, H = im.size
    # ADR-0018 温和提字：20 → 22 / 24 → 26 / 19 → 22，构图不动
    y = TOPBAR_H + 44

    # 目标条
    card(d, [90, y, 1190, y + 106], TH, hi=True, r=16)
    d.text((112, y + 24), "目标", font=font(22, True), fill=TH.ACCENT)
    d.text((112, y + 60), "2016 个区块 × 10 分钟 = 两星期（20,160 分钟）",
           font=font(26), fill=TH.TXT)
    y += 138

    # 四步闭环
    steps = [
        ("① 数时间", "这 2016 块实际花了多久？", TH.CARD),
        ("② 快了", "机器变多 → 门槛调紧", RED_BG),
        ("③ 慢了", "机器走了 → 门槛放松", GREEN_BG),
        ("④ 回到 10 分钟", "校准完成，继续挖", TH.CARD_HI),
    ]
    x = 90
    for i, (t, s, fill) in enumerate(steps):
        edge = TH.ACCENT if i == 3 else (RED if i == 1 else (GREEN if i == 2 else TH.EDGE))
        card(d, [x, y, x + 260, y + 150], TH, fill=fill, edge=edge, r=16)
        d.text((x + 20, y + 26), t, font=font(26, True),
               fill=(RED if i == 1 else (GREEN if i == 2 else TH.ACCENT)))
        wrap(d, s, x + 20, y + 72, 224, font(22), TH.TXT, 34, 2)
        if i < 3:
            arrow(d, (x + 268, y + 75), (x + 308, y + 75), TH, width=3)
        x += 280
    y += 190

    # 公式
    card(d, [90, y, 1190, y + 106], TH, r=16)
    d.text((112, y + 26), "公式", font=font(22, True), fill=TH.ACCENT)
    d.text((112, y + 60), "新门槛 = 旧门槛 ×（实际耗时 ÷ 理论耗时）",
           font=font(26, True), fill=TH.TXT)

    footer_note(d, W, H, "按区块高度触发不是按日历 · 单次最多 4 倍 · 护栏史上从未被触发")
    save(im, OUT / "03-difficulty-loop.png")


# ─────────────────────────────────────────────────────────
def s7_04():
    """04 矿机四代进化。"""
    # ADR-0018 温和提字：19-20 → 22，文案不动；仅纵向重新排布以容纳更大字号
    im, d = canvas(TH, "矿机换了四代", "站7 · 矿工谷", size="16:9")
    W, H = im.size
    y = TOPBAR_H + 38
    gens = [
        ("CPU", "2009 年", "普通电脑的中央处理器", "爱好者，一台笔记本就能挖", 1),
        ("GPU", "2010 年起", "显卡，擅长大量并行运算", "正好对上「疯狂掷骰子」", 2),
        ("FPGA", "2011 年前后", "可现场编程的芯片", "更贴近这道特定工序", 3),
        ("ASIC", "2013 年至今", "专用芯片，只干这一件事", "能效高出若干个数量级", 4),
    ]
    x = 90
    for i, (nm, yr, what, why, lvl) in enumerate(gens):
        hi = (i == 3)
        card(d, [x, y, x + 260, y + 246], TH, hi=hi, r=16)
        d.text((x + 20, y + 24), nm, font=font(30, True), fill=TH.ACCENT)
        d.text((x + 20, y + 66), yr, font=font(22), fill=TH.MID)
        wrap(d, what, x + 20, y + 98, 224, font(22), TH.TXT, 34, 2)
        wrap(d, why, x + 20, y + 168, 224, font(22), TH.GOLD, 34, 2)
        # 能效阶梯条
        by = y + 226
        bw = [40, 88, 140, 224][i]
        d.rounded_rectangle([x + 20, by, x + 20 + bw, by + 10], radius=5, fill=TH.ACCENT)
        if i < 3:
            arrow(d, (x + 268, y + 123), (x + 308, y + 123), TH, width=3)
        x += 280
    y += 270

    card(d, [90, y, 1190, y + 108], TH, hi=True, r=16)
    d.text((112, y + 26), "结果", font=font(22, True), fill=TH.ACCENT)
    d.text((112, y + 62), "一台今天的主流矿机，顶得上早年成千上万台电脑；"
                          "矿工对电价极度敏感，哪里电便宜就往哪里搬",
           font=font(24), fill=TH.TXT)

    footer_note(d, W, H, "通用 → 专用：不是被禁止，是概率上没意义")
    save(im, OUT / "04-machine-evolution.png")


# ─────────────────────────────────────────────────────────
def s7_05():
    """05 矿池份额怎么分账。"""
    im, d = canvas(TH, "矿池怎么分账", "站7 · 矿工谷", size="16:9")
    W, H = im.size
    # ADR-0018 温和提字：19-21 → 22-25，构图不动
    y = TOPBAR_H + 34

    # 两条门槛对比
    card(d, [90, y, 1190, y + 158], TH, r=16)
    d.text((112, y + 22), "两道门槛", font=font(22, True), fill=TH.ACCENT)
    # 全网门槛（高）
    d.text((112, y + 62), "全网门槛", font=font(23, True), fill=TH.TXT)
    d.rounded_rectangle([230, y + 52, 1130, y + 78], radius=6, fill=RED_BG)
    d.rounded_rectangle([230, y + 52, 430, y + 78], radius=6, fill=RED)
    d.text((1160, y + 65), "极难撞上", font=font(22), fill=RED, anchor="rm")
    # 份额门槛（低）
    d.text((112, y + 116), "份额门槛", font=font(23, True), fill=TH.TXT)
    d.rounded_rectangle([230, y + 106, 1130, y + 132], radius=6, fill=GREEN_BG)
    d.rounded_rectangle([230, y + 106, 940, y + 132], radius=6, fill=GREEN)
    d.text((1160, y + 119), "几秒一次，用来计数", font=font(22), fill=GREEN, anchor="rm")
    y += 186

    # 三台机器 → 矿池 → 分账
    machines = [("矿工 A", "37%"), ("矿工 B", "28%"), ("矿工 C", "35%")]
    x = 90
    for nm, pct in machines:
        card(d, [x, y, x + 210, y + 148], TH, r=16)
        d.text((x + 20, y + 24), nm, font=font(25, True), fill=TH.TXT)
        d.text((x + 20, y + 60), "提交份额", font=font(22), fill=TH.MID)
        d.text((x + 20, y + 98), pct, font=font(28, True), fill=TH.ACCENT)
        arrow(d, (x + 218, y + 74), (x + 264, y + 74), TH, width=3)
        x += 274

    card(d, [912, y, 1190, y + 148], TH, hi=True, r=16)
    d.text((932, y + 26), "矿池", font=font(25, True), fill=TH.ACCENT)
    wrap(d, "按份额比例分奖励", 932, y + 70, 236, font(22), TH.TXT, 34, 2)
    y += 176

    card(d, [90, y, 1190, y + 106], TH, r=16)
    d.text((112, y + 26), "为什么要抱团", font=font(22, True), fill=TH.ACCENT)
    d.text((112, y + 62), "单干要等上一年；进池后每天固定到账，总额差不多但波动被摊平",
           font=font(24), fill=TH.TXT)

    footer_note(d, W, H, "份额本身在链上没有价值，只用来证明你干了多少")
    save(im, OUT / "05-pool-share.png")


# ─────────────────────────────────────────────────────────
def s7_06():
    """06 矿池不拥有算力（误解纠正）。"""
    im, d = canvas(TH, "矿池集中 ≠ 算力集中", "站7 · 矿工谷", size="16:9")
    # ADR-0018 温和提字：18-22 → 22-26，构图不动
    W, H = im.size
    y = TOPBAR_H + 36

    # 左：误解
    card(d, [90, y, 620, y + 268], TH, fill=RED_BG, edge=RED, r=18)
    d.text((114, y + 26), "听起来是这样", font=font(24, True), fill=RED)
    d.text((114, y + 66), "矿池 = 一个拥有大量机器的大老板", font=font(26), fill=TH.TXT)
    wrap(d, "它握着这些算力，想怎么用就怎么用。", 114, y + 108, 480,
         font(22), TH.TXT, 34, 2)
    # 误解示意：一个大块压着三个小方块
    d.rounded_rectangle([130, y + 172, 580, y + 218], radius=8, fill=RED)
    d.text((355, y + 195), "矿池（以为它拥有）", font=font(22, True),
           fill=(255, 255, 255), anchor="mm")
    for i in range(3):
        bx = 150 + i * 150
        d.rounded_rectangle([bx, y + 222, bx + 120, y + 254], radius=6, fill=RED_BG,
                            outline=RED, width=2)
        d.text((bx + 60, y + 238), "矿工机器", font=font(22), fill=RED, anchor="mm")

    # 右：实际
    card(d, [660, y, 1190, y + 268], TH, hi=True, r=18)
    d.text((684, y + 26), "实际上是", font=font(24, True), fill=TH.ACCENT)
    d.text((684, y + 66), "矿池是记账员，机器在矿工手里", font=font(26), fill=TH.TXT)
    wrap(d, "矿工把机器指向哪个池，只是改一行配置的事。", 684, y + 108, 480,
         font(22), TH.TXT, 34, 2)
    # 实际示意：三个机器各自有双向箭头指向矿池
    d.rounded_rectangle([700, y + 172, 1150, y + 218], radius=8, fill=TH.CARD_HI,
                        outline=TH.ACCENT, width=2)
    d.text((925, y + 195), "矿池（只记账、不拥有）", font=font(22, True),
           fill=TH.ACCENT, anchor="mm")
    for i in range(3):
        bx = 706 + i * 150
        d.rounded_rectangle([bx, y + 222, bx + 126, y + 254], radius=6, fill=TH.CARD,
                            outline=TH.ACCENT, width=2)
        d.text((bx + 63, y + 238), "可随时走", font=font(22), fill=TH.ACCENT, anchor="mm")

    # 中间对比箭头
    arrow(d, (628, y + 134), (652, y + 134), TH, width=4)
    y += 296

    card(d, [90, y, 1190, y + 108], TH, r=16)
    d.text((112, y + 26), "还在推进的一件事", font=font(22, True), fill=TH.ACCENT)
    d.text((112, y + 62), "Stratum V2：把「打包哪些交易」的选择权从矿池拿回来，交还给矿工本人",
           font=font(24), fill=TH.TXT)

    footer_note(d, W, H, "矿池的份额更像一个每天可以重新投票的席位，不是固定资产")
    save(im, OUT / "06-pool-not-owner.png")


# ─────────────────────────────────────────────────────────
def s7_07():
    """三句话带走本篇。"""
    im, d = canvas(TH, "三句话带走本篇", "站7 · 矿工谷", size="16:9")
    items = [
        ("①", "掷骰子换票", "不是解数学题；票不是身份发的，是已经烧掉的电换来的"),
        ("②", "门槛自动校准", "每 2016 块按实际耗时调一次，所以算力翻万亿倍还是 10 分钟"),
        ("③", "抱团不等于被控制", "矿池不拥有任何一台机器，矿工换池的成本几乎为零"),
    ]
    y = TOPBAR_H + 56
    for num, t, s in items:
        card(d, [100, y, 1180, y + 128], TH, r=18)
        d.text((140, y + 64), num, font=font(44, True), fill=TH.ACCENT, anchor="lm")
        d.text((220, y + 40), t, font=font(29, True), fill=TH.TXT)
        d.text((220, y + 92), s, font=font(20), fill=TH.MID)
        y += 156
    save(im, OUT / "08-mindmap-summary.png")


FN = [s7_01, s7_02, s7_03, s7_04, s7_05, s7_06, s7_07]
for f in FN:
    f()
print(f"done: {len(FN)} figs (paper-light) -> {OUT}")
