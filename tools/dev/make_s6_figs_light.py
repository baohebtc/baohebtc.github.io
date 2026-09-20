# -*- coding: utf-8 -*-
"""
make_s6_figs_light.py — 站6「共识峰」配图产线（paper-light / ADR-0008 + ADR-0010）
=====================================================================================
7 张全部走 brand_figs.Theme("paper-light")：色板/规格/字体/品牌三件套单一来源。
  01 共识问题全景（两份账平票）  16:9
  02 工作量即选票（身份 vs 算力） 16:9
  03 分叉收敛生命周期（4 步）     16:9
  04 最重链 vs 最长链（误解纠正） 16:9
  05 T1 表图·确认数 vs 概率       4:3
  06 守规矩 vs 作弊（博弈）       16:9
  07 三句话小结                   16:9
用法：python3 make_s6_figs_light.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from brand_figs import (Theme, canvas, card, arrow, save, font,
                        TOPBAR_H, FOOTBAR_H, R_BIG, R_SM)

TH = Theme("paper-light")
ROOT = pathlib.Path("/Users/mac/Desktop/宝盒知识库/比特币学习地图/慢读宝盒公众号")
OUT = ROOT / "站6-共识峰" / "03-配图"

# 浅底语义色（ADR-0008：语义色唯一来源）
RED, RED_BG = (198, 40, 40), (250, 235, 232)
GREEN, GREEN_BG = (27, 122, 80), (233, 244, 238)
BLUE, BLUE_BG = (58, 124, 186), (233, 241, 248)


def wrap(d, text, x, y, maxw, f, fill, lh, max_lines=3):
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


def bar(d, text, y0=540, y1=630, fs=27, fill=None):
    """底部结论条（全系列统一画法）。"""
    d.rounded_rectangle([70, y0, 1210, y1], radius=R_SM,
                        fill=TH.CARD_HI, outline=TH.ACCENT, width=2)
    d.text((640, (y0 + y1) // 2), text, font=font(fs, True),
           fill=fill or TH.TXT, anchor="mm")


def blocks(d, x, y, n, size, gap, fill, outline, width=2, per_row=8, label=None):
    """画一串区块小方块（用于链对比）。"""
    for i in range(n):
        r, c = divmod(i, per_row)
        bx = x + c * (size + gap)
        by = y + r * (size + gap)
        d.rounded_rectangle([bx, by, bx + size, by + size], radius=6,
                            fill=fill, outline=outline, width=width)
        if label:
            d.text((bx + size / 2, by + size / 2), str(i + 1),
                   font=font(13, True), fill=TH.MID, anchor="mm")


# ────────────────────────────────────────────────────────────
def s6_01():
    """共识问题全景：两个矿工同时出块 → 全网短暂两份账。"""
    im, d = canvas(TH, "共识问题：两份账，听谁的？", "站6 · 共识峰", size="16:9")
    y0 = TOPBAR_H + 42
    d.text((640, y0 - 22), "同一秒，两边都算出了合格区块",
           font=font(23), fill=TH.MID, anchor="mm")
    for box, name, blk, col in (
            ([90, y0, 500, y0 + 112], "矿工甲", "区块 A", BLUE),
            ([780, y0, 1190, y0 + 112], "矿工乙", "区块 B", BLUE)):
        d.rounded_rectangle(box, radius=R_SM, fill=TH.CARD, outline=col, width=3)
        cx = (box[0] + box[2]) // 2
        d.text((cx, box[1] + 40), name, font=font(28, True), fill=TH.TXT, anchor="mm")
        d.text((cx, box[1] + 82), f"算出 {blk}", font=font(22), fill=col, anchor="mm")
    arrow(d, (500, y0 + 56), (640, y0 + 130), TH, color=TH.DIM, width=3)
    arrow(d, (780, y0 + 56), (640, y0 + 130), TH, color=TH.DIM, width=3)

    yl = y0 + 190
    for box, title, sub, col in (
            ([70, yl, 600, yl + 196], "一半节点：先听到 A", "跟着 A 这条继续挖", BLUE),
            ([680, yl, 1210, yl + 196], "一半节点：先听到 B", "跟着 B 这条继续挖", BLUE)):
        d.rounded_rectangle(box, radius=R_BIG, fill=TH.CARD, outline=TH.EDGE, width=2)
        cx = (box[0] + box[2]) // 2
        d.text((cx, box[1] + 40), title, font=font(28, True), fill=col, anchor="mm")
        d.text((cx, box[1] + 78), sub, font=font(21), fill=TH.MID, anchor="mm")
        blocks(d, box[0] + 60, box[1] + 106, 5, 34, 12,
               fill=TH.CARD_HI, outline=col, width=2)
    bar(d, "此刻全网出现了两份都合法的账 —— 没有裁判，谁来判？")
    save(im, OUT / "01-consensus-problem.png")


def s6_02():
    """投票资格：身份能伪造，工作量不能。"""
    im, d = canvas(TH, "投票资格：把「说话权」换成「干活权」", "站6 · 共识峰", size="16:9")
    y0, h = TOPBAR_H + 46, 340
    # 左：身份票（红）
    d.rounded_rectangle([80, y0, 600, y0 + h], radius=R_BIG, fill=RED_BG,
                        outline=RED, width=3)
    d.text((340, y0 + 46), "一人一票（靠身份）", font=font(30, True), fill=RED, anchor="mm")
    d.text((340, y0 + 88), "用不上", font=font(22), fill=TH.MID, anchor="mm")
    wrap(d, "一个人可以开出一万个假身份，票就被刷爆了", 120, y0 + 140, 440,
         font(23), TH.TXT, 36, 3)
    d.text((120, y0 + 262), "× 女巫攻击：身份可以无限复制", font=font(22), fill=RED)
    d.text((120, y0 + 300), "× 节点随时进出，没有稳定名单", font=font(22), fill=RED)
    # 右：工作量票（绿）
    d.rounded_rectangle([680, y0, 1200, y0 + h], radius=R_BIG, fill=GREEN_BG,
                        outline=GREEN, width=3)
    d.text((940, y0 + 46), "一份算力一票（靠工作量）", font=font(30, True), fill=GREEN, anchor="mm")
    d.text((940, y0 + 88), "比特币的选择", font=font(22), fill=TH.MID, anchor="mm")
    wrap(d, "票不是投出来的，是干出来的：算出合格区块那一刻，票自动生效",
         720, y0 + 140, 440, font(23), TH.TXT, 36, 3)
    d.text((720, y0 + 262), "✓ 刷票没有意义：每票都要真烧电", font=font(22), fill=GREEN)
    d.text((720, y0 + 300), "✓ 不用报名、不用认证、不用被同意", font=font(22), fill=GREEN)
    arrow(d, (610, y0 + h // 2), (670, y0 + h // 2), TH, color=TH.ACCENT, width=4, head=14)
    bar(d, "中本聪的原话：节点用算力投票 —— 不是一人一票", y0=520, y1=610)
    save(im, OUT / "02-pow-vote.png")


def s6_03():
    """分叉收敛生命周期（4 步）。"""
    im, d = canvas(TH, "分叉收敛：不急着判胜负，让下一个人来判", "站6 · 共识峰", size="16:9")
    steps = [
        ("①", "同时出块 · 平票", "两条链都合法，谁也不比谁差", BLUE),
        ("②", "各挖各的", "节点先跟着自己听到的那条继续挖", TH.MID),
        ("③", "一方先延伸", "累计工作量超过对手，胜负出现", TH.ACCENT),
        ("④", "全网切换", "另一条成孤块，交易回到待确认池", GREEN),
    ]
    boxes = [[80, 130, 620, 300], [660, 130, 1200, 300],
             [80, 342, 620, 512], [660, 342, 1200, 512]]
    for (num, t, s, col), box in zip(steps, boxes):
        d.rounded_rectangle(box, radius=R_BIG, fill=TH.CARD, outline=col, width=3)
        d.text((box[0] + 30, box[1] + 52), num, font=font(40, True), fill=col, anchor="lm")
        d.text((box[0] + 100, box[1] + 44), t, font=font(29, True), fill=TH.TXT)
        wrap(d, s, box[0] + 34, box[1] + 104, 500, font(22), TH.MID, 34, 2)
    arrow(d, (625, 215), (655, 215), TH, color=TH.DIM, width=3, head=10)
    d.line([(930, 300), (930, 321), (350, 321), (350, 342)], fill=TH.DIM, width=3)
    arrow(d, (345, 342), (350, 342), TH, color=TH.DIM, width=3, head=10)
    arrow(d, (625, 427), (655, 427), TH, color=TH.DIM, width=3, head=10)
    bar(d, "整个过程通常几分钟内结束 —— 承认暂时不一致，换来最终收敛", y0=546, y1=636)
    save(im, OUT / "03-fork-converge.png")


def s6_04():
    """常见误解：最长链 ≠ 区块最多，是累计工作量最大。"""
    im, d = canvas(TH, "最重链：比的是总工作量，不是块数", "站6 · 共识峰", size="16:9")
    y0, h = TOPBAR_H + 40, 400
    # 左：15 块低难度（空心小圆＝轻）
    d.rounded_rectangle([70, y0, 540, y0 + h], radius=R_BIG, fill=TH.CARD,
                        outline=TH.EDGE, width=2)
    d.text((305, y0 + 44), "链 X · 15 个块", font=font(29, True), fill=TH.TXT, anchor="mm")
    d.text((305, y0 + 84), "早期低难度挖出", font=font(21), fill=TH.MID, anchor="mm")
    blocks(d, 110, y0 + 120, 15, 26, 14, fill=TH.CARD, outline=TH.DIM, width=2, per_row=8)
    d.text((305, y0 + 348), "块数更多，但每个块很「轻」", font=font(22), fill=TH.MID, anchor="mm")
    # 右：10 块高难度（实心金块＝重）
    d.rounded_rectangle([740, y0, 1210, y0 + h], radius=R_BIG, fill=TH.CARD_HI,
                        outline=TH.GOLD, width=3)
    d.text((975, y0 + 44), "链 Y · 10 个块", font=font(29, True), fill=TH.TXT, anchor="mm")
    d.text((975, y0 + 84), "当下高难度挖出", font=font(21), fill=TH.MID, anchor="mm")
    blocks(d, 780, y0 + 120, 10, 40, 16, fill=TH.CARD_HI, outline=TH.GOLD, width=3, per_row=5)
    d.text((975, y0 + 348), "块数更少，但每个块很「重」", font=font(22), fill=TH.GOLD, anchor="mm")
    # 中间：比什么
    d.line([(640, y0 + 20), (640, y0 + h - 20)], fill=TH.DIM, width=2)
    d.text((640, y0 + 150), "比", font=font(26, True), fill=TH.MID, anchor="mm")
    d.text((640, y0 + 192), "总", font=font(26, True), fill=TH.ACCENT, anchor="mm")
    d.text((640, y0 + 234), "工", font=font(26, True), fill=TH.ACCENT, anchor="mm")
    d.text((640, y0 + 276), "作", font=font(26, True), fill=TH.ACCENT, anchor="mm")
    d.text((640, y0 + 318), "量", font=font(26, True), fill=TH.ACCENT, anchor="mm")
    bar(d, "节点选最重链：想靠「刷块数」改写历史，先烧够电再说", y0=520, y1=610)
    save(im, OUT / "04-heaviest-chain.png")


def s6_05():
    """T1 表图：确认数 vs 追上概率（白皮书 §11，q=0.1）。"""
    im, d = canvas(TH, "T1 · 确认数 vs 追上概率（白皮书 §11）", "站6 · 共识峰", size="4:3")
    rows = [
        ("1 个确认", "约 20.5%", "还早，完全可能追上"),
        ("2 个确认", "约 5.1%", "风险明显下降"),
        ("3 个确认", "约 1.3%", "多数交易所小额入账线"),
        ("4 个确认", "约 0.35%", "已经很稳"),
        ("5 个确认", "约 0.09%", "首次跌破 0.1%"),
        ("6 个确认", "约 0.024%", "行业惯例：约万分之 2.4"),
    ]
    x0, x1 = 90, 1190
    cx_n, cx_p, cx_s = 150, 520, 860
    y = TOPBAR_H + 18
    d.rounded_rectangle([x0, y, x1, y + 54], radius=R_SM, fill=TH.CARD_HI,
                        outline=TH.EDGE, width=2)
    d.text((cx_n, y + 27), "确认数", font=font(24, True), fill=TH.MID, anchor="lm")
    d.text((cx_p, y + 27), "手握 10% 算力者追上的概率", font=font(24, True), fill=TH.MID, anchor="lm")
    d.text((cx_s, y + 27), "一句话", font=font(24, True), fill=TH.ACCENT, anchor="lm")
    y += 66
    for i, (n, p, s) in enumerate(rows):
        h = 92
        bg = TH.CARD if i % 2 == 0 else TH.CARD_HI
        hot = (i == 5)
        d.rounded_rectangle([x0, y, x1, y + h], radius=12, fill=bg,
                            outline=TH.GOLD if hot else TH.EDGE,
                            width=3 if hot else 1)
        d.rectangle([x0 + 6, y + 16, x0 + 11, y + h - 16],
                    fill=TH.ACCENT if hot else TH.GOLD)
        d.text((cx_n, y + 46), n, font=font(25, True), fill=TH.TXT, anchor="lm")
        d.text((cx_p, y + 46), p, font=font(25, True),
               fill=TH.ACCENT if hot else TH.TXT, anchor="lm")
        d.text((cx_s, y + 46), s, font=font(22), fill=TH.MID, anchor="lm")
        y += h + 12
    bar(d, "6 不是协议写死的规则，是行业惯例；概率永远不为零", y0=y + 6, y1=y + 66, fs=25)
    save(im, OUT / "05-t1-confirm-prob-table.png")


def s6_06():
    """博弈：守规矩 vs 作弊。"""
    im, d = canvas(TH, "守规矩 vs 作弊：哪条路更划算", "站6 · 共识峰", size="16:9")
    y0, h = TOPBAR_H + 40, 400
    d.rounded_rectangle([80, y0, 600, y0 + h], radius=R_BIG, fill=GREEN_BG,
                        outline=GREEN, width=3)
    d.text((340, y0 + 46), "守规矩", font=font(32, True), fill=GREEN, anchor="mm")
    for i, t in enumerate(["块被全网接受 → 拿到回报",
                           "电费没白烧，成本能收回",
                           "可以长期重复这样做"]):
        d.text((120, y0 + 116 + i * 62), "✓ " + t, font=font(24), fill=TH.TXT)
    d.rounded_rectangle([680, y0, 1200, y0 + h], radius=R_BIG, fill=RED_BG,
                        outline=RED, width=3)
    d.text((940, y0 + 46), "作弊", font=font(32, True), fill=RED, anchor="mm")
    for i, t in enumerate(["先买下并供养过半算力",
                           "块若被拒 → 电全白烧",
                           "即便成功 → 砸掉自己的资产"]):
        d.text((720, y0 + 116 + i * 62), "× " + t, font=font(24), fill=TH.TXT)
    wrap(d, "注意：矿工负责提议，节点负责裁决 —— 出块的人没有最终解释权",
         120, y0 + 312, 1000, font(22), TH.MID, 32, 2)
    bar(d, "不靠好人，靠自私的人：让诚实成为回报更高的那条路", y0=520, y1=610)
    save(im, OUT / "06-game-incentive.png")


def s6_07():
    """三句话带走本篇（与站4/5 同款小结卡）。"""
    im, d = canvas(TH, "三句话带走本篇", "站6 · 共识峰", size="16:9")
    items = [
        ("①", "说话权换成干活权", "身份能伪造、算力不能；一 CPU 一票，票是干出来的"),
        ("②", "最重链说了算", "不是块数最多的链，是累计工作量最大的那条链"),
        ("③", "自私的人撑起公共账本", "守规矩更划算，而验证权握在每个全节点手里"),
    ]
    y = TOPBAR_H + 56
    for num, t, s in items:
        card(d, [100, y, 1180, y + 128], TH, r=18)
        d.text((140, y + 64), num, font=font(44, True), fill=TH.ACCENT, anchor="lm")
        d.text((220, y + 40), t, font=font(29, True), fill=TH.TXT)
        d.text((220, y + 90), s, font=font(21), fill=TH.MID)
        y += 156
    save(im, OUT / "07-mindmap-summary.png")


FN = [s6_01, s6_02, s6_03, s6_04, s6_05, s6_06, s6_07]
for f in FN:
    f()
print(f"done: {len(FN)} figs (paper-light) -> {OUT}")
