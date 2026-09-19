# -*- coding: utf-8 -*-
"""
make_s13_figs_light.py — 站1/站1.5/站3 配图迁移批次 2（ADR-0008 已采纳：方向 B paper-light）
============================================================================================
18 张全部走 brand_figs.Theme("paper-light")：色板/规格/字体/品牌三件套单一来源。
原脚本已全盘丢失（含 archive），本脚本按各站微信版文章的图注语义 + 原图结构重建。
站1 现金湾：01 银行vs比特币 / 02 双花决策树 / 03 村账vs公开账本 / 04 私钥公钥 / 05 PoW生命周期 / 06 比特币vs黄金
站1.5 钱到底是什么：01 锚点四次迁移 / 02 信任三次升级 / 03 钱=记账约定 / 04 四种钱对比 / 05 锚点前后 / 07 三句话
站3 双花峡：01 双花分叉 / 02 银行vs公开账本 / 03 UTXO消耗 / 04 时间戳哈希链 / 05 PoW矿工 / 07 三句话
用法：python make_s13_figs_light.py [s1|s15|s3|all]
"""
import pathlib, sys, math
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from PIL import Image, ImageDraw
from brand_figs import (Theme, canvas, card, chip, arrow, btc, save,
                        font, SIZES, TOPBAR_H, FOOTBAR_H, R_BIG, R_SM, _wrap)

TH = Theme("paper-light")
ROOT = pathlib.Path("/Users/mac/Desktop/宝盒知识库/比特币学习地图/慢读宝盒公众号")
OUT1 = ROOT / "站1-现金湾" / "03-配图"
OUT15 = ROOT / "站1.5-钱到底是什么" / "03-配图"
OUT3 = ROOT / "站3-双花峡-双花难题" / "03-配图"

# 浅底语义色（与批次1 同源）
RED, RED_BG = (198, 40, 40), (250, 235, 232)
GREEN, GREEN_BG = (27, 122, 80), (233, 244, 238)
BLUE, BLUE_BG = (58, 124, 186), (233, 241, 248)


def wrap(d, text, x, y, maxw, f, fill, lh, max_lines=3, anchor="la"):
    return _wrap(d, text, x, y, maxw, f, fill, lh, max_lines)


def box_text(d, box, th, title, sub="", ts=26, ss=20, hi=False, ac=False):
    """卡内标题 + 副标题（统一左对齐 24px 内边距）。"""
    x0, y0, x1, y1 = box
    d.text((x0 + 24, y0 + 30), title, font=font(ts, True),
           fill=th.ACCENT if ac else th.TXT, anchor="la")
    if sub:
        wrap(d, sub, x0 + 24, y0 + 30 + ts + 14, (x1 - x0) - 48, font(ss), th.MID, ss + 11, 3)


def v_chain(d, x0, x1, y, nodes, th, hi=False, bh=84, gap=34):
    """竖排节点链（返回结束 y）。"""
    for i, n in enumerate(nodes):
        card(d, [x0, y, x1, y + bh], TH, hi=hi, r=R_SM)
        d.text(((x0 + x1) // 2, y + bh // 2), n, font=font(26, True), fill=TH.TXT, anchor="mm")
        if i < len(nodes) - 1:
            arrow(d, ((x0 + x1) // 2, y + bh + 5), ((x0 + x1) // 2, y + bh + gap - 5), TH)
        y += bh + gap
    return y


def footer_bar(d, th, W, H, text, color=None, bg=None, h=64, fs=26):
    """底部结论条（在合规条上方）。"""
    fy = H - FOOTBAR_H - h - 26
    d.rounded_rectangle([60, fy, W - 60, fy + h], radius=R_SM,
                        fill=bg or th.CARD_HI, outline=color or th.ACCENT, width=2)
    d.text((W // 2, fy + h // 2), text, font=font(fs, True), fill=th.TXT, anchor="mm")
    return fy


# ============================================================ 站1 现金湾
def s1_01():
    """银行转账 vs 比特币转账（4:3 双栏对照）。"""
    im, d = canvas(TH, "银行转账 vs 比特币转账", "站1 · 现金湾", size="4:3")
    W, H = im.size
    cols = [
        (60, 620, "银行转账", ["你", "你的银行", "对方银行", "对方"], "中间人「说了算」", False),
        (660, 1220, "比特币转账", ["你", "比特币网络（全网共同记账）", "对方"], "点对点，没有中间人", True),
    ]
    for x0, x1, title, nodes, note, hi in cols:
        d.text(((x0 + x1) // 2, 112), title, font=font(31, True),
               fill=TH.ACCENT if hi else TH.TXT, anchor="mm")
        y = v_chain(d, x0, x1, 158, nodes, TH, hi=hi, bh=82, gap=32)
        d.text(((x0 + x1) // 2, y + 4), note, font=font(22), fill=TH.MID, anchor="mm")
    footer_bar(d, TH, W, H, "关键差别：有没有一个「说了算」的中间人")
    save(im, OUT1 / "01-cash-vs-bank.png")


def s1_02():
    """双花难题决策树（16:9）。"""
    im, d = canvas(TH, "双花难题：同一笔币，想付给两个人", "站1 · 现金湾", size="16:9")
    W, H = im.size
    # 顶部问题卡
    card(d, [400, 106, 880, 186], TH, hi=True, r=R_BIG)
    d.text((640, 146), "同一笔 1 BTC，同时发给 A 和 B", font=font(27, True), fill=TH.TXT, anchor="mm")
    # 分叉
    arrow(d, (640, 192), (355, 250), TH)
    arrow(d, (640, 192), (925, 250), TH)
    # 左右分支
    left = [("有中心账本", "银行查余额：这枚币已经花过", "→ 直接拒付第二笔")]
    card(d, [80, 254, 630, 470], TH, r=R_BIG)
    box_text(d, [80, 254, 630, 470], TH, "① 有中心账本（银行）", "账本只有一本，由银行保管", ts=28, ac=True)
    y = 344
    for t, s1_, s2_ in left:
        d.text((112, y), t, font=font(24, True), fill=TH.TXT)
        d.text((112, y + 40), s1_, font=font(21), fill=TH.MID)
        d.text((112, y + 74), s2_, font=font(21, True), fill=GREEN)
    card(d, [650, 254, 1200, 470], TH, hi=True, r=R_BIG)
    box_text(d, [650, 254, 1200, 470], TH, "② 没有中心账本（比特币）", "没人说了算，靠什么拦住？", ts=28, ac=True)
    y = 344
    d.text((682, y), "数学规则", font=font(24, True), fill=TH.TXT)
    d.text((682, y + 40), "先到先得，重复花一眼露馅", font=font(21), fill=TH.MID)
    d.text((682, y + 74), "利益奖励：老实记账更划算", font=font(21, True), fill=TH.ACCENT)
    footer_bar(d, TH, W, H, "没有裁判，也能防止作弊 —— 这就是比特币要解决的核心问题")
    save(im, OUT1 / "02-double-spending.png")


def s1_03():
    """从村账到公开账本（4:3 双栏）。"""
    im, d = canvas(TH, "从村账到比特币公开账本", "站1 · 现金湾", size="4:3")
    W, H = im.size
    # 左：村账
    d.text((340, 112), "村里的账 · 人情信任", font=font(29, True), fill=TH.TXT, anchor="mm")
    # 先画连线（随后被卡片覆盖，视觉上自然）
    people = [("你", 130, 150), ("邻居", 550, 150), ("村长", 130, 400), ("商人", 550, 400)]
    for nm, px, py in people:
        d.line([(px, py), (340, 268)], fill=TH.EDGE, width=2)
    card(d, [240, 200, 440, 336], TH, r=R_BIG)
    d.text((340, 244), "一本村账", font=font(26, True), fill=TH.TXT, anchor="mm")
    d.text((340, 292), "谁欠谁，都记在这本上", font=font(19), fill=TH.MID, anchor="mm")
    for nm, px, py in people:
        card(d, [px - 66, py - 32, px + 66, py + 32], TH, hi=True, r=R_SM)
        d.text((px, py), nm, font=font(23, True), fill=TH.TXT, anchor="mm")
    d.text((340, 500), "大家彼此认识，靠人情管住", font=font(22), fill=TH.MID, anchor="mm")
    d.text((340, 560), "换一批陌生人来，这本账就转不动了", font=font(21), fill=TH.MID, anchor="mm")
    # 右：公开账本
    d.text((940, 112), "比特币公开账本 · 陌生人互信", font=font(29, True), fill=TH.ACCENT, anchor="mm")
    btc(d, im, 940, 300, 150)
    card(d, [680, 400, 1200, 500], TH, hi=True, r=R_BIG)
    d.text((940, 424), "人人手里都有一本完整副本", font=font(25, True), fill=TH.TXT, anchor="mm")
    d.text((940, 466), "数学规则 + 利益奖励管住陌生人", font=font(21), fill=TH.MID, anchor="mm")
    d.text((940, 560), "人人能查 · 没人能偷偷改", font=font(24, True), fill=TH.ACCENT, anchor="mm")
    d.text((940, 610), "任何一本对不上，全村立刻发现", font=font(21), fill=TH.MID, anchor="mm")
    footer_bar(d, TH, W, H, "人情信任 → 陌生人也能互信：这就是区块链的起点")
    save(im, OUT1 / "03-public-ledger.png")


def s1_04():
    """私钥与公钥（16:9）。"""
    im, d = canvas(TH, "私钥与公钥：一把钥匙，一个门牌号", "站1 · 现金湾", size="16:9")
    W, H = im.size
    # 左：私钥
    card(d, [80, 150, 520, 420], TH, hi=True, r=R_BIG)
    d.text((300, 196), "私钥", font=font(32, True), fill=TH.ACCENT, anchor="mm")
    d.ellipse([272, 232, 328, 288], outline=TH.GOLD, width=5)
    d.line([(300, 288), (300, 340)], fill=TH.GOLD, width=6)
    d.line([(300, 340), (324, 356)], fill=TH.GOLD, width=5)
    d.line([(300, 340), (276, 356)], fill=TH.GOLD, width=5)
    d.text((300, 378), "你家唯一的钥匙", font=font(23, True), fill=TH.TXT, anchor="mm")
    # 右：公钥/地址
    card(d, [760, 150, 1200, 420], TH, r=R_BIG)
    d.text((980, 196), "公钥（地址）", font=font(32, True), fill=TH.TXT, anchor="mm")
    card(d, [890, 240, 1070, 310], TH, r=R_SM, fill=TH.CARD_HI, edge=TH.EDGE)
    d.text((980, 275), "1A2b…9Zx", font=font(24, True), fill=TH.GOLD, anchor="mm")
    d.text((980, 378), "你家的门牌号，可以公开", font=font(23, True), fill=TH.TXT, anchor="mm")
    # 正向箭头
    arrow(d, (540, 250), (740, 250), TH, width=5, head=14)
    d.text((640, 218), "能推出", font=font(23, True), fill=TH.ACCENT, anchor="mm")
    # 反向虚线 + 禁止
    yy = 344
    for x in range(556, 716, 26):
        d.line([(x, yy), (x + 15, yy)], fill=RED, width=4)
    d.ellipse([626, yy - 22, 674, yy + 22], fill=TH.BG, outline=RED, width=3)
    d.line([(637, yy - 10), (663, yy + 10)], fill=RED, width=4)
    d.line([(663, yy - 10), (637, yy + 10)], fill=RED, width=4)
    d.text((640, 300), "推不回", font=font(23, True), fill=RED, anchor="mm")
    d.text((640, 390), "数学上几乎不可能（单向）", font=font(20), fill=RED, anchor="mm")
    footer_bar(d, TH, W, H, "丢了私钥 = 没有客服 · Not your keys, not your coins",
               color=RED, bg=RED_BG)
    save(im, OUT1 / "04-keys.png")


def s1_05():
    """工作量证明的生命周期（16:9 流程）。"""
    im, d = canvas(TH, "工作量证明的生命周期", "站1 · 现金湾", size="16:9")
    W, H = im.size
    steps = [
        ("新交易", "有人发起一笔转账"),
        ("广播全网", "瞬间传给所有节点"),
        ("解数学题", "矿工比拼算力找答案"),
        ("第一个解出", "拿到「写这一页」的权利"),
        ("新区块上链", "接上前一页，永久留痕"),
    ]
    n = len(steps)
    gap = 20
    cw = (1220 - 60 - gap * (n - 1)) / n
    y0, bh = 200, 250
    for i, (t, s) in enumerate(steps):
        x0 = 60 + i * (cw + gap)
        card(d, [x0, y0, x0 + cw, y0 + bh], TH, hi=(i == 3), r=R_BIG)
        d.ellipse([x0 + 22, y0 + 22, x0 + 56, y0 + 56], fill=TH.CARD_HI, outline=TH.ACCENT, width=2)
        d.text((x0 + 39, y0 + 39), str(i + 1), font=font(22, True), fill=TH.ACCENT, anchor="mm")
        d.text((x0 + 22, y0 + 84), t, font=font(26, True),
               fill=TH.ACCENT if i == 3 else TH.TXT)
        wrap(d, s, x0 + 22, y0 + 132, cw - 44, font(20), TH.MID, 30, 3)
        if i < n - 1:
            arrow(d, (x0 + cw + 3, y0 + bh // 2), (x0 + cw + gap - 3, y0 + bh // 2), TH, width=3, head=8)
    card(d, [60, 486, 1220, 566], TH, hi=True, r=R_SM)
    d.text((640, 526), "胜者所得：写这一页的权利 + 一点新比特币奖励",
           font=font(24, True), fill=TH.TXT, anchor="mm")
    footer_bar(d, TH, W, H, "算力「浪费」= 没有老板也能安全的代价")
    save(im, OUT1 / "05-pow.png")


def s1_06():
    """比特币 vs 黄金（4:3 对比表）。"""
    im, d = canvas(TH, "比特币 vs 黄金：稀缺的来源不同", "站1 · 现金湾", size="4:3")
    W, H = im.size
    xl, xm, xr = 70, 400, 700
    # 表头
    card(d, [xl, 130, 1210, 196], TH, r=R_SM, fill=TH.CARD_HI)
    d.text((xl + 26, 163), "维度", font=font(25, True), fill=TH.TXT, anchor="lm")
    d.text((xm, 163), "黄金", font=font(25, True), fill=TH.TXT, anchor="lm")
    d.text((700, 163), "比特币", font=font(25, True), fill=TH.ACCENT, anchor="lm")
    rows = [
        ("稀缺性来源", "地球上就那么多", "代码里写死：2100 万枚"),
        ("新增速度", "挖到新矿就增加", "约每 4 年「减半」一次"),
        ("上限", "不确定，可能有新矿", "数学保证，谁也改不了"),
    ]
    y = 210
    for i, (dim, a, b) in enumerate(rows):
        fill = TH.CARD if i % 2 == 0 else TH.CARD_HI
        d.rounded_rectangle([xl, y, 1210, y + 116], radius=10, fill=fill,
                            outline=TH.EDGE, width=1)
        d.text((xl + 26, y + 58), dim, font=font(24, True), fill=TH.TXT, anchor="lm")
        wrap(d, a, xm, y + 36, 240, font(21), TH.MID, 30, 2)
        wrap(d, b, 700, y + 36, 480, font(21, True), TH.GOLD, 30, 2)
        y += 126
    footer_bar(d, TH, W, H, "黄金的上限由地球决定，比特币的上限由代码和共识决定")
    save(im, OUT1 / "06-limited-supply.png")


# ============================================================ 站1.5 钱到底是什么
def s15_01():
    """信任锚点的四次迁移（16:9 时间线）。"""
    im, d = canvas(TH, "信任锚点的四次迁移", "站1.5 · 钱到底是什么", size="16:9")
    W, H = im.size
    steps = [
        ("实物", "贝壳 / 牲畜 / 黄金", "东西本身就有价值"),
        ("国家", "铸币 / 法定纸币", "国家信用背书"),
        ("账户", "银行电子余额", "机构记账，你信任它"),
        ("代码", "比特币", "规则写死，无人可改"),
    ]
    n = len(steps)
    gap = 30
    cw = (1220 - 60 - gap * (n - 1)) / n
    y0, bh = 196, 268
    for i, (t, mid, s) in enumerate(steps):
        x0 = 60 + i * (cw + gap)
        card(d, [x0, y0, x0 + cw, y0 + bh], TH, hi=(i == n - 1), r=R_BIG)
        d.text((x0 + cw / 2, y0 + 38), f"第 {i + 1} 次", font=font(20), fill=TH.MID, anchor="mm")
        d.text((x0 + cw / 2, y0 + 86), t, font=font(30, True),
               fill=TH.ACCENT if i == n - 1 else TH.TXT, anchor="mm")
        d.line([(x0 + 40, y0 + 116), (x0 + cw - 40, y0 + 116)], fill=TH.EDGE, width=2)
        wrap(d, mid, x0 + 22, y0 + 138, cw - 44, font(21, True), TH.TXT, 32, 2)
        wrap(d, s, x0 + 22, y0 + 206, cw - 44, font(19), TH.MID, 28, 2)
        if i < n - 1:
            arrow(d, (x0 + cw + 5, y0 + bh // 2), (x0 + cw + gap - 5, y0 + bh // 2), TH, width=3, head=9)
    footer_bar(d, TH, W, H, "锚点方向：越来越不依赖「某个特定的人」")
    save(im, OUT15 / "03-money-anchor-timeline.png")


def s15_02():
    """信任的三次升级（16:9 三阶段）。"""
    im, d = canvas(TH, "信任的三次升级", "站1.5 · 钱到底是什么", size="16:9")
    W, H = im.size
    steps = [
        ("认识对方", "熟人社会", "村里借钱靠抬头不见低头见，跑不掉"),
        ("信任机构", "银行 · 法律", "陌生人之间靠一个第三方居中担保"),
        ("信任规则", "代码 · 数学", "不信任何人，只信写在代码里的规则"),
    ]
    n = 3
    gap = 34
    cw = (1220 - 60 - gap * (n - 1)) / n
    y0, bh = 200, 280
    for i, (t, mid, s) in enumerate(steps):
        x0 = 60 + i * (cw + gap)
        card(d, [x0, y0, x0 + cw, y0 + bh], TH, hi=(i == n - 1), r=R_BIG)
        d.text((x0 + 28, y0 + 34), f"第 {i + 1} 阶段", font=font(20), fill=TH.MID)
        d.text((x0 + 28, y0 + 74), t, font=font(31, True),
               fill=TH.ACCENT if i == n - 1 else TH.TXT)
        card(d, [x0 + 28, y0 + 128, x0 + cw - 28, y0 + 178], TH, r=R_SM, fill=TH.CARD_HI)
        d.text(((x0 + 28 + x0 + cw - 28) / 2, y0 + 153), mid, font=font(22, True),
               fill=TH.GOLD, anchor="mm")
        wrap(d, s, x0 + 28, y0 + 200, cw - 56, font(20), TH.MID, 30, 3)
        if i < n - 1:
            arrow(d, (x0 + cw + 6, y0 + bh // 2), (x0 + cw + gap - 6, y0 + bh // 2), TH, width=3, head=10)
    footer_bar(d, TH, W, H, "不是人变好了，而是信任对象从「人」换成了「规则」")
    save(im, OUT15 / "02-trust-three-stages.png")


def s15_03():
    """钱 = 一群人共同的记账约定（16:9）。"""
    im, d = canvas(TH, "钱 = 一群人共同的记账约定", "站1.5 · 钱到底是什么", size="16:9")
    W, H = im.size
    card(d, [90, 210, 300, 360], TH, r=R_BIG)
    d.text((195, 262), "A", font=font(46, True), fill=TH.TXT, anchor="mm")
    d.text((195, 322), "借钱的人", font=font(21), fill=TH.MID, anchor="mm")
    card(d, [980, 210, 1190, 360], TH, r=R_BIG)
    d.text((1085, 262), "B", font=font(46, True), fill=TH.TXT, anchor="mm")
    d.text((1085, 322), "借出的人", font=font(21), fill=TH.MID, anchor="mm")
    # 中间借条
    card(d, [440, 190, 840, 380], TH, hi=True, r=R_BIG)
    d.text((640, 228), "借 条", font=font(26, True), fill=TH.ACCENT, anchor="mm")
    d.text((640, 288), "A 欠 B 10 元", font=font(34, True), fill=TH.TXT, anchor="mm")
    d.text((640, 344), "2026 年 · 凭此条结清", font=font(19), fill=TH.MID, anchor="mm")
    arrow(d, (305, 285), (432, 285), TH, width=4, head=12)
    arrow(d, (848, 285), (975, 285), TH, width=4, head=12)
    card(d, [200, 440, 1080, 530], TH, r=R_SM)
    d.text((640, 485), "这张借条之所以成立，不因为它有实体，而因为 A 和 B 都认这笔账",
           font=font(23), fill=TH.TXT, anchor="mm")
    footer_bar(d, TH, W, H, "共识，就是钱的地基 —— 换一批人认，钱就没了")
    save(im, OUT15 / "01-shared-ledger.png")


def s15_04():
    """四种钱的对比（4:3 表）。"""
    im, d = canvas(TH, "四种钱的对比", "站1.5 · 钱到底是什么", size="4:3")
    W, H = im.size
    cols = [("实物钱", 430, 640), ("金属钱", 640, 850), ("法币", 850, 1035), ("比特币", 1035, 1210)]
    xl = 70
    # 表头
    card(d, [xl, 128, 1210, 192], TH, r=R_SM, fill=TH.CARD_HI)
    d.text((xl + 24, 160), "维度", font=font(24, True), fill=TH.TXT, anchor="lm")
    for name, a, b in cols:
        d.text(((a + b) / 2, 160), name, font=font(23, True),
               fill=TH.ACCENT if name == "比特币" else TH.TXT, anchor="mm")
    rows = [
        ("锚点", "东西本身", "稀缺金属", "国家信用", "代码规则"),
        ("发行方", "自然产生", "挖矿 / 铸造", "央行", "无人（算法）"),
        ("上限", "有限", "有限", "可增发", "2100 万枚"),
    ]
    y = 202
    for i, r in enumerate(rows):
        fill = TH.CARD if i % 2 == 0 else TH.CARD_HI
        d.rounded_rectangle([xl, y, 1210, y + 112], radius=10, fill=fill, outline=TH.EDGE, width=1)
        d.text((xl + 24, y + 56), r[0], font=font(23, True), fill=TH.TXT, anchor="lm")
        for (name, a, b), tv in zip(cols, r[1:]):
            d.text(((a + b) / 2, y + 56), tv, font=font(21, name == "比特币"),
                   fill=TH.GOLD if name == "比特币" else TH.MID, anchor="mm")
        y += 122
    footer_bar(d, TH, W, H, "锚点越往后，越不依赖「某个权威」")
    save(im, OUT15 / "04-money-compare.png")


def s15_05():
    """传统法币 vs 比特币：锚点换掉了（16:9 双栏）。"""
    im, d = canvas(TH, "比特币换掉了信任锚点", "站1.5 · 钱到底是什么", size="16:9")
    W, H = im.size
    card(d, [70, 150, 610, 470], TH, r=R_BIG)
    d.text((340, 194), "传统法币", font=font(30, True), fill=TH.TXT, anchor="mm")
    d.text((340, 244), "锚点 = 机构的信用", font=font(24), fill=TH.MID, anchor="mm")
    card(d, [110, 288, 570, 368], TH, r=R_SM, fill=RED_BG, edge=RED)
    d.text((340, 328), "规则可改 · 账户可冻结", font=font(24, True), fill=RED, anchor="mm")
    d.text((340, 412), "你拥有的是「使用权」", font=font(23), fill=TH.MID, anchor="mm")
    card(d, [670, 150, 1210, 470], TH, hi=True, r=R_BIG)
    d.text((940, 194), "比特币", font=font(30, True), fill=TH.ACCENT, anchor="mm")
    d.text((940, 244), "锚点 = 代码的规则", font=font(24), fill=TH.MID, anchor="mm")
    card(d, [710, 288, 1170, 368], TH, r=R_SM, fill=GREEN_BG, edge=GREEN)
    d.text((940, 328), "写死的上限 · 无人能单方改", font=font(24, True), fill=GREEN, anchor="mm")
    d.text((940, 412), "私钥在手，才是「所有权」", font=font(23), fill=TH.MID, anchor="mm")
    footer_bar(d, TH, W, H, "锚点从「某个人说了算」换成「规则说了算」")
    save(im, OUT15 / "05-anchor-before-after.png")


def s15_07():
    """三句话带走（16:9）。"""
    im, d = canvas(TH, "三句话带走本篇", "站1.5 · 钱到底是什么", size="16:9")
    W, H = im.size
    items = [
        ("①", "钱是约定", "不是因为它有实体，而是因为一群人都认这笔账 —— 共识才是地基"),
        ("②", "信任三次升级", "从「认识对方」到「信任机构」，再到「信任规则」，一次比一次少依赖人"),
        ("③", "锚点四次迁移", "实物 → 国家 → 账户 → 代码：方向是越来越不依赖「某个特定的人」"),
    ]
    y = TOPBAR_H + 56
    for num, t, s in items:
        card(d, [100, y, 1180, y + 128], TH, r=18)
        d.text((140, y + 64), num, font=font(44, True), fill=TH.ACCENT, anchor="lm")
        d.text((220, y + 42), t, font=font(29, True), fill=TH.TXT)
        wrap(d, s, 220, y + 84, 900, font(21), TH.MID, 30, 2)
        y += 156
    save(im, OUT15 / "07-mindmap-summary.png")


# ============================================================ 站3 双花峡
def s3_01():
    """双花：一份凭证被用了两次（16:9）。"""
    im, d = canvas(TH, "双花：一份凭证，被用了两次", "站3 · 双花峡", size="16:9")
    W, H = im.size
    btc(d, im, 250, 330, 168)
    d.text((250, 442), "同一笔 1 BTC", font=font(24, True), fill=TH.TXT, anchor="mm")
    # 分叉
    arrow(d, (350, 300), (600, 220), TH, width=4, head=14)
    arrow(d, (350, 362), (600, 470), TH, width=4, head=14)
    card(d, [610, 160, 1150, 280], TH, r=R_BIG)
    d.text((650, 200), "A 收到 1 BTC", font=font(27, True), fill=TH.TXT)
    d.text((650, 242), "系统认了这笔", font=font(21), fill=TH.MID)
    card(d, [610, 410, 1150, 530], TH, r=R_BIG)
    d.text((650, 450), "B 也收到 1 BTC", font=font(27, True), fill=TH.TXT)
    d.text((650, 492), "系统也认了这笔", font=font(21), fill=TH.MID)
    d.text((880, 352), "同一枚币，被算了两遍", font=font(24, True), fill=RED, anchor="mm")
    footer_bar(d, TH, W, H, "一份凭证被用了两次 —— 这就是双花", color=RED, bg=RED_BG)
    save(im, OUT3 / "01-double-spend.png")


def s3_02():
    """银行中央账本 vs 比特币公开账本（16:9 双栏）。"""
    im, d = canvas(TH, "银行中央账本 vs 比特币公开账本", "站3 · 双花峡", size="16:9")
    W, H = im.size
    card(d, [70, 150, 610, 470], TH, r=R_BIG)
    d.text((340, 190), "银行 · 中央账本", font=font(28, True), fill=TH.TXT, anchor="mm")
    card(d, [180, 240, 500, 350], TH, r=R_SM, fill=TH.CARD_HI)
    for k in range(4):
        d.line([(210, 268 + k * 24), (470, 268 + k * 24)], fill=TH.DIM, width=2)
    d.text((340, 388), "账本只有一本，银行说了算", font=font(22), fill=TH.MID, anchor="mm")
    d.text((340, 428), "你信任它不改、不丢、不拒付", font=font(21), fill=TH.MID, anchor="mm")
    card(d, [670, 150, 1210, 470], TH, hi=True, r=R_BIG)
    d.text((940, 190), "比特币 · 公开账本", font=font(28, True), fill=TH.ACCENT, anchor="mm")
    for i, px in enumerate([760, 880, 1000, 1120]):
        card(d, [px - 52, 240, px + 52, 350], TH, r=10)
        for k in range(3):
            d.line([(px - 32, 268 + k * 28), (px + 32, 268 + k * 28)], fill=TH.DIM, width=2)
    d.text((940, 388), "人人手里都有完整副本", font=font(22), fill=TH.MID, anchor="mm")
    d.text((940, 428), "改一页 = 对全网说谎，立刻被识破", font=font(21), fill=TH.GOLD, anchor="mm")
    footer_bar(d, TH, W, H, "一个靠中介兜底，一个靠全网验证")
    save(im, OUT3 / "02-ledger-compare.png")


def s3_03():
    """UTXO：一笔花掉即失效（16:9）。"""
    im, d = canvas(TH, "UTXO：一笔花掉，就再也花不了", "站3 · 双花峡", size="16:9")
    W, H = im.size
    cy = TOPBAR_H + 230
    # 左：你的币
    d.ellipse([130, cy - 78, 290, cy + 82], fill=TH.CARD, outline=TH.ACCENT, width=5)
    d.text((210, cy), "1.0", font=font(40, True), fill=TH.TXT, anchor="mm")
    d.text((210, cy + 116), "你手里的一枚 UTXO", font=font(22), fill=TH.MID, anchor="mm")
    arrow(d, (310, cy), (430, cy), TH, width=4, head=13)
    # 中：销毁
    d.ellipse([450, cy - 62, 570, cy + 58], fill=RED_BG, outline=RED, width=4)
    d.line([(478, cy - 34), (542, cy + 30)], fill=RED, width=5)
    d.line([(542, cy - 34), (478, cy + 30)], fill=RED, width=5)
    d.text((510, cy + 96), "整枚作废", font=font(23, True), fill=RED, anchor="mm")
    arrow(d, (590, cy), (700, cy), TH, width=4, head=13)
    # 右：两枚新币
    for i, (v, lbl, col) in enumerate([("0.7", "付给对方", TH.ACCENT), ("0.3", "找零回你", TH.GOLD)]):
        cxx, cyy = 800 + i * 200, cy - 66
        d.ellipse([cxx - 66, cyy - 60, cxx + 66, cyy + 72], fill=TH.CARD, outline=col, width=5)
        d.text((cxx, cyy + 4), v, font=font(32, True), fill=TH.TXT, anchor="mm")
        d.text((cxx, cyy + 122), lbl, font=font(22, True), fill=col, anchor="mm")
    footer_bar(d, TH, W, H, "不是从余额里扣数字，而是「烧掉整枚旧币、铸出新币」")
    save(im, OUT3 / "03-utxo.png")


def s3_04():
    """时间戳 + 哈希链（16:9）。"""
    im, d = canvas(TH, "时间戳 + 哈希链：先后次序被数学锁死", "站3 · 双花峡", size="16:9")
    W, H = im.size
    blocks = [("区块 #1", "00:00", "指纹 8f2a…"),
              ("区块 #2", "00:10", "指纹 03e9…"),
              ("区块 #3", "00:20", "指纹 c71b…")]
    notes = ["创世块 · 链的起点", "含 #1 的指纹", "含 #2 的指纹"]
    bw, bh, gap = 320, 264, 42
    x0, y0 = 68, TOPBAR_H + 96
    for i, (name, t, hsh) in enumerate(blocks):
        bx = x0 + i * (bw + gap)
        card(d, [bx, y0, bx + bw, y0 + bh], TH, hi=(i == 2), r=R_BIG)
        d.text((bx + 26, y0 + 34), name, font=font(26, True),
               fill=TH.ACCENT if i == 2 else TH.TXT)
        d.text((bx + 26, y0 + 76), f"时间戳 {t}", font=font(20), fill=TH.MID)
        card(d, [bx + 26, y0 + 112, bx + bw - 26, y0 + 172], TH, r=10, fill=TH.CARD_HI)
        d.text((bx + bw / 2, y0 + 142), hsh, font=font(21, True), fill=TH.GOLD, anchor="mm")
        d.text((bx + 26, y0 + 196), notes[i], font=font(19), fill=TH.MID)
        if i > 0:
            arrow(d, (bx - gap + 6, y0 + 100), (bx - 6, y0 + 100), TH, width=4, head=12)
            d.text((bx - gap / 2, y0 + 74), "链接", font=font(18), fill=TH.MID, anchor="mm")
        if i < 2:
            arrow(d, (bx + bw + 6, y0 + 176), (bx + bw + gap - 6, y0 + 176), TH, width=4, head=12)
    card(d, [68, 490, 560, 570], TH, r=R_SM, fill=RED_BG, edge=RED)
    d.text((314, 530), "改一块 → 后面全对不上", font=font(22, True), fill=RED, anchor="mm")
    card(d, [600, 490, 1212, 570], TH, r=R_SM, fill=GREEN_BG, edge=GREEN)
    d.text((906, 530), "先后顺序被写进数学，无法偷偷调换", font=font(22, True), fill=GREEN, anchor="mm")
    save(im, OUT3 / "04-timestamp-chain.png")


def s3_05():
    """PoW：矿工算力赛跑（16:9）。"""
    im, d = canvas(TH, "PoW：矿工的算力赛跑", "站3 · 双花峡", size="16:9")
    W, H = im.size
    # 题目条
    card(d, [340, 118, 940, 186], TH, r=R_SM, fill=TH.CARD_HI)
    d.text((640, 152), "题目：找一个 nonce，让哈希开头有足够多的 0",
           font=font(23, True), fill=TH.TXT, anchor="mm")
    miners = [("矿工 A", "算力 10", "慢", False),
              ("矿工 B", "算力 45", "最快 → 拿到记账权", True),
              ("矿工 C", "算力 20", "中等", False)]
    cw, gap = 330, 45
    x0, y0 = 76, TOPBAR_H + 160
    for i, (nm, pw, res, winner) in enumerate(miners):
        bx = x0 + i * (cw + gap)
        card(d, [bx, y0, bx + cw, y0 + 250], TH, hi=winner, r=R_BIG)
        d.text((bx + cw / 2, y0 + 40), nm, font=font(28, True),
               fill=TH.ACCENT if winner else TH.TXT, anchor="mm")
        # 算力条
        d.rounded_rectangle([bx + 40, y0 + 88, bx + cw - 40, y0 + 116], radius=8, fill=TH.DIM)
        ratio = {"矿工 A": 0.25, "矿工 B": 1.0, "矿工 C": 0.5}[nm]
        d.rounded_rectangle([bx + 40, y0 + 88, bx + 40 + (cw - 80) * ratio, y0 + 116],
                            radius=8, fill=TH.ACCENT if winner else TH.GOLD)
        d.text((bx + cw / 2, y0 + 152), pw, font=font(22, True), fill=TH.TXT, anchor="mm")
        d.text((bx + cw / 2, y0 + 200), res, font=font(22, True),
               fill=TH.ACCENT if winner else TH.MID, anchor="mm")
        if winner:
            btc(d, im, bx + cw - 46, y0 + 46, 52)
    footer_bar(d, TH, W, H, "作弊要吞下全网一半算力，成本远超回报 —— 诚实更划算")
    save(im, OUT3 / "05-pow-miners.png")


def s3_06():
    """T1 表图：中本聪五件套 vs 挡双花机制（4:3，微信端以此图呈现表格）。"""
    im, d = canvas(TH, "T1 \u00b7 中本聪五件套 vs 挡双花机制", "站3 \u00b7 双花峡", size="4:3")
    W, H = im.size
    rows = [
        ("公开账本（区块链）", "重复花一眼露馅", "人人能查的共享总账"),
        ("UTXO 模型", "同一 output 用掉即失效", "粮票撕掉作废"),
        ("时间戳 + 哈希链", "先后次序被数学锁死", "盖了骑缝章的账页"),
        ("PoW + 矿工竞争", "作弊代价远超回报", "作弊要吞下半座电厂"),
        ("全网广播 + 节点验证", "先到先得，6 确认后改不动", "全村作证"),
    ]
    nums = "\u2460\u2461\u2462\u2463\u2464"
    x0, x1 = 110, 1180
    cx_name, cx_stop, cx_ana = 136, 450, 870
    y = TOPBAR_H + 16
    # 表头
    d.rounded_rectangle([x0, y, x1, y + 54], radius=R_SM, fill=TH.CARD_HI,
                        outline=TH.EDGE, width=2)
    d.text((cx_name, y + 27), "五件套", font=font(24, True), fill=TH.MID, anchor="lm")
    d.text((cx_stop, y + 27), "它挡住了什么", font=font(24, True), fill=TH.MID, anchor="lm")
    d.text((cx_ana, y + 27), "一句类比", font=font(24, True), fill=TH.ACCENT, anchor="lm")
    y += 74
    for i, (name, stop, ana) in enumerate(rows):
        h = 124
        bg = TH.CARD if i % 2 == 0 else TH.CARD_HI
        d.rounded_rectangle([x0, y, x1, y + h], radius=12, fill=bg,
                            outline=TH.EDGE, width=1)
        d.rectangle([x0 + 6, y + 18, x0 + 11, y + h - 18], fill=TH.ACCENT)
        wrap(d, f"{nums[i]} {name}", x0 + 26, y + 26, 280, font(23, True), TH.TXT, 30, 2)
        wrap(d, stop, cx_stop, y + 26, 390, font(22), TH.TXT, 30, 2)
        wrap(d, ana, cx_ana, y + 26, 300, font(22), TH.GOLD, 30, 2)
        y += h + 16
    d.text(((x0 + x1) // 2, y + 22),
           "五件套各挡一环：看见 \u00b7 作废 \u00b7 定序 \u00b7 贵到不划算 \u00b7 全村作证",
           font=font(24, True), fill=TH.MID, anchor="mm")
    save(im, OUT3 / "06-t1-five-tools-table.png")


def s3_07():
    """三句话带走（16:9）。"""
    im, d = canvas(TH, "三句话带走本篇", "站3 · 双花峡", size="16:9")
    W, H = im.size
    items = [
        ("①", "双花是「一份凭证用两次」", "数字能零成本复制，所以「同一笔钱花两遍」必须靠规则本身拦住"),
        ("②", "银行靠中央账本兜底", "所有交易过银行一本总账，余额不够直接拒付 —— 但这要求你信任那个中心"),
        ("③", "中本聪靠「五件套 + 博弈」", "公开账本 · UTXO · 时间戳哈希链 · PoW · 全网验证，让诚实成为更划算的选择"),
    ]
    y = TOPBAR_H + 56
    for num, t, s in items:
        card(d, [100, y, 1180, y + 128], TH, r=18)
        d.text((140, y + 64), num, font=font(44, True), fill=TH.ACCENT, anchor="lm")
        d.text((220, y + 42), t, font=font(28, True), fill=TH.TXT)
        wrap(d, s, 220, y + 84, 900, font(21), TH.MID, 30, 2)
        y += 156
    save(im, OUT3 / "07-mindmap-summary.png")


FN = {"s1": [s1_01, s1_02, s1_03, s1_04, s1_05, s1_06],
      "s15": [s15_01, s15_02, s15_03, s15_04, s15_05, s15_07],
      "s3": [s3_01, s3_02, s3_03, s3_04, s3_05, s3_06, s3_07]}

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    todo = FN["s1"] + FN["s15"] + FN["s3"] if arg == "all" else FN[arg]
    for f in todo:
        f()
        print("✅", f.__name__, "->", f.__doc__.split("（")[0])
