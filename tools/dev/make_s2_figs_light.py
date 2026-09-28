# -*- coding: utf-8 -*-
"""
make_s2_figs_light.py — 站2 银行堡 配图迁移批次 3（ADR-0008 已采纳：方向 B paper-light）
========================================================================================
原图是 6 张可灵 AI 生成的深色 3D 插画（1024×1024，无任何文字标签）。
按规范 §7 COULD 批次：「重绘为扁平信息图（信息保留优先，不追求 3D 质感）」。
本脚本保留原插画的核心隐喻（城堡储物柜 / 车位缩小 / 打印循环 / 锁链没收 / 砖墙裂缝 / 三节点），
并补上原图缺失的文字说明 —— 科普图没有文字，读者只能靠图注猜，这是原方案的缺陷。
用法：python make_s2_figs_light.py [all|01|02|...]
"""
import pathlib, sys, math
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from PIL import Image, ImageDraw
from brand_figs import (Theme, canvas, card, chip, arrow, btc, save,
                        font, SIZES, TOPBAR_H, FOOTBAR_H, R_BIG, R_SM, _wrap)

TH = Theme("paper-light")
OUT = pathlib.Path("/Users/mac/Desktop/宝盒知识库/比特币学习地图/慢读宝盒公众号/站2-银行堡-货币三大缺陷/03-配图")
STATION = "站2 · 银行堡"

RED, RED_BG = (198, 40, 40), (250, 235, 232)
GREEN, GREEN_BG = (27, 122, 80), (233, 244, 238)
DEEP = (120, 84, 40)          # 砖墙/城堡砖色（暖棕，非品牌橙）


def wrap(d, text, x, y, maxw, f, fill, lh, max_lines=3):
    return _wrap(d, text, x, y, maxw, f, fill, lh, max_lines)


def footer_bar(d, th, W, H, text, color=None, bg=None, h=64, fs=25):
    fy = H - FOOTBAR_H - h - 26
    d.rounded_rectangle([60, fy, W - 60, fy + h], radius=R_SM,
                        fill=bg or th.CARD_HI, outline=color or th.ACCENT, width=2)
    d.text((W // 2, fy + h // 2), text, font=font(fs, True), fill=th.TXT, anchor="mm")
    return fy


def castle(d, x0, y0, x1, y1, th, wall=3):
    """城堡剪影：垛口城墙 + 拱门 + 双侧塔楼（原 01 插画的核心隐喻）。"""
    cx = (x0 + x1) // 2
    bw = (x1 - x0) / 9.0
    # 城墙主体
    d.rectangle([x0, y0 + 46, x1, y1], fill=th.CARD, outline=th.EDGE, width=wall)
    # 垛口
    for i in range(0, 9, 2):
        bx = x0 + i * bw
        d.rectangle([bx, y0, bx + bw, y0 + 46], fill=th.CARD, outline=th.EDGE, width=wall)
    # 双侧塔楼
    for tx in (x0 - 34, x1 - 6):
        d.rectangle([tx, y0 - 30, tx + 40, y1], fill=th.CARD, outline=th.EDGE, width=wall)
        d.polygon([(tx, y0 - 30), (tx + 20, y0 - 70), (tx + 40, y0 - 30)],
                  fill=th.CARD_HI, outline=th.EDGE)
    # 拱门
    d.rectangle([cx - 44, y1 - 96, cx + 44, y1], fill=th.BG, outline=th.EDGE, width=wall)
    d.pieslice([cx - 44, y1 - 132, cx + 44, y1 - 60], 180, 360, fill=th.BG, outline=th.EDGE, width=wall)
    # 门上的锁
    d.rectangle([cx - 16, y1 - 74, cx + 16, y1 - 44], fill=th.CARD_HI, outline=th.ACCENT, width=3)
    d.arc([cx - 11, y1 - 92, cx + 11, y1 - 66], 180, 360, fill=th.ACCENT, width=3)


def key_icon(d, cx, cy, s, th, col=None):
    """钥匙图标（原 01/04 的「钥匙不在你手里」）。"""
    c = col or th.GOLD
    d.ellipse([cx - s, cy - s, cx - s + 2 * s * 0.8, cy + s * 0.8], outline=c, width=4)
    d.line([(cx + s * 0.5, cy + s * 0.2), (cx + 2 * s, cy + s * 1.7)], fill=c, width=5)
    d.line([(cx + 1.5 * s, cy + 1.2 * s), (cx + 2 * s, cy + s * 0.9)], fill=c, width=5)


def lock_icon(d, cx, cy, s, th, col=None):
    c = col or RED
    d.rounded_rectangle([cx - s, cy - s * 0.2, cx + s, cy + s * 1.3], radius=6,
                        fill=TH.CARD, outline=c, width=4)
    d.arc([cx - s * 0.6, cy - s * 1.1, cx + s * 0.6, cy + s * 0.3], 180, 360, fill=c, width=4)


# ============================================================ 站2 六张
def s2_01():
    """城堡储物柜：柜子结实，钥匙在物业手里（4:3）。"""
    im, d = canvas(TH, "银行堡：柜子结实，钥匙却在别人手里", STATION, size="4:3")
    W, H = im.size
    # 左：城堡
    castle(d, 130, 230, 470, 560, TH)
    d.text((300, 596), "城堡 = 替我们记账、保管的机构", font=font(21), fill=TH.MID, anchor="mm")
    # 右：储物柜 + 钥匙归属
    card(d, [700, 230, 1080, 480], TH, r=R_BIG)
    d.text((890, 268), "你的储物柜", font=font(26, True), fill=TH.TXT, anchor="mm")
    # 柜门格
    for i in range(3):
        gx = 740 + i * 105
        d.rounded_rectangle([gx, 300, gx + 88, 400], radius=8, fill=TH.CARD_HI,
                            outline=TH.EDGE, width=2)
        lock_icon(d, gx + 44, 330, 14, TH, col=TH.ACCENT)
    d.text((890, 432), "柜子很结实，比塞床垫里安全", font=font(20), fill=TH.MID, anchor="mm")
    # 钥匙标注
    card(d, [700, 500, 1080, 580], TH, r=R_SM, fill=RED_BG, edge=RED)
    key_icon(d, 748, 528, 16, TH, col=RED)
    d.text((790, 540), "钥匙在物业（银行）手里", font=font(23, True), fill=RED, anchor="lm")
    footer_bar(d, TH, W, H, "「钥匙不在你手里」—— 这是三大缺陷的总根", color=RED, bg=RED_BG)
    save(im, OUT / "01-castle-vault.png")


def s2_02():
    """通胀税：车位被偷偷缩小 10%（16:9）。"""
    im, d = canvas(TH, "通胀税：没人敲门通知你，购买力就少了一截", STATION, size="16:9")
    W, H = im.size
    # 上排：车位对比
    y0 = TOPBAR_H + 46
    d.text((150, y0), "去年", font=font(24, True), fill=TH.TXT, anchor="lm")
    d.rounded_rectangle([230, y0 - 56, 560, y0 + 56], radius=10, fill=TH.CARD, outline=TH.EDGE, width=3)
    d.rounded_rectangle([280, y0 - 30, 510, y0 + 30], radius=8, fill=TH.CARD_HI, outline=TH.EDGE, width=2)
    d.text((395, y0), "你的车位", font=font(23), fill=TH.MID, anchor="mm")
    arrow(d, (585, y0), (675, y0), TH, width=4, head=13)
    d.text((150, y0 + 112), "今年", font=font(24, True), fill=TH.TXT, anchor="lm")
    d.rounded_rectangle([230, y0 + 56, 560, y0 + 168], radius=10, fill=TH.CARD, outline=TH.EDGE, width=3)
    d.rounded_rectangle([305, y0 + 82, 485, y0 + 142], radius=8, fill=RED_BG, outline=RED, width=2)
    d.text((395, y0 + 112), "缩小 10%", font=font(23, True), fill=RED, anchor="mm")
    # 右侧说明
    card(d, [700, y0 - 60, 1215, y0 + 226], TH, hi=True, r=R_BIG)
    d.text((746, y0 - 22), "车位还在，只是变小了", font=font(27, True), fill=TH.ACCENT)
    wrap(d, "社会的商品总量没变，但流通的钱变多了 —— 结果就是物价上涨。",
         746, y0 + 26, 450, font(24), TH.TXT, 38, 2)
    wrap(d, "你的 100 块还是 100 块，能买到的东西却少了，而且没人通知你。",
         746, y0 + 118, 450, font(24), TH.MID, 38, 2)
    # 底部两组货币
    by = 460
    d.text((200, by + 46), "100 元", font=font(30, True), fill=TH.TXT, anchor="mm")
    d.text((200, by + 96), "面额没变", font=font(22), fill=TH.MID, anchor="mm")
    arrow(d, (300, by + 50), (420, by + 50), TH, width=4, head=13)
    for i in range(4):
        d.rounded_rectangle([460 + i * 56, by + 16, 500 + i * 56, by + 84], radius=8,
                            fill=TH.CARD, outline=TH.EDGE, width=2)
    d.text((830, by + 50), "能买到的东西变少了", font=font(26, True), fill=RED, anchor="lm")
    footer_bar(d, TH, W, H, "加税要立法、要投票；稀释购买力只需要一场会议", color=RED, bg=RED_BG)
    save(im, OUT / "02-inflation-tax.png")


def s2_03():
    """债务货币：现代法币是「借」出来的（16:9 循环）。"""
    im, d = canvas(TH, "债务货币：现代法币是「借」出来的", STATION, size="16:9")
    W, H = im.size
    nodes = [("① 政府花钱", False), ("② 发债借钱", False),
             ("③ 央行买债印钱", True), ("④ 稀释所有人", True)]
    n = len(nodes)
    gap = 26
    cw = (1140 - gap * (n - 1)) / n
    x0, y0, bh = 70, TOPBAR_H + 120, 104
    for i, (label, hi) in enumerate(nodes):
        bx = x0 + i * (cw + gap)
        card(d, [bx, y0, bx + cw, y0 + bh], TH, hi=hi, r=R_SM)
        d.text((bx + cw / 2, y0 + bh / 2), label, font=font(23, True), fill=TH.TXT, anchor="mm")
        if i < n - 1:
            arrow(d, (bx + cw + 4, y0 + bh / 2), (bx + cw + gap - 4, y0 + bh / 2), TH, width=3, head=9)
    # 回环箭头：④ 底部 → ① 底部
    ry = y0 + bh + 66
    xl_, xr_ = x0 + cw / 2, x0 + (n - 1) * (cw + gap) + cw / 2
    d.line([(xr_, y0 + bh + 8), (xr_, ry)], fill=TH.ACCENT, width=4)
    d.line([(xr_, ry), (xl_, ry)], fill=TH.ACCENT, width=4)
    arrow(d, (xl_, ry), (xl_, y0 + bh + 8), TH, width=4, head=13)
    d.text(((xl_ + xr_) / 2, ry - 32), "死循环：债务越滚越多", font=font(26, True),
           fill=TH.ACCENT, anchor="mm")
    card(d, [200, 460, 1080, 546], TH, r=R_SM)
    d.text((640, 503), "钱不是「印」出来，而是「借」出来 —— 每放一笔贷款，就凭空多一笔存款",
           font=font(22, True), fill=TH.TXT, anchor="mm")
    footer_bar(d, TH, W, H, "如果所有人同时还清债务，流通中的钱几乎会消失")
    save(im, OUT / "03-debt-money.png")


def s2_04():
    """无锚点 → 审查与没收：存款是对机构的债权（16:9）。"""
    im, d = canvas(TH, "你的「存款」本质是「对机构的债权」", STATION, size="16:9")
    W, H = im.size
    # 左：存款单
    card(d, [70, 150, 470, 420], TH, r=R_BIG)
    d.text((270, 190), "银行存单", font=font(26, True), fill=TH.TXT, anchor="mm")
    d.line([(110, 230), (430, 230)], fill=TH.EDGE, width=2)
    d.text((270, 280), "存款 100,000", font=font(34, True), fill=TH.TXT, anchor="mm")
    d.text((270, 340), "本质：机构欠你的一笔债", font=font(22, True), fill=TH.GOLD, anchor="mm")
    d.text((270, 384), "不是「你拥有的财富」", font=font(21), fill=TH.MID, anchor="mm")
    arrow(d, (480, 285), (560, 285), TH, width=4, head=13)
    # 中：冻结
    card(d, [570, 150, 810, 420], TH, r=R_BIG, fill=RED_BG, edge=RED)
    lock_icon(d, 690, 226, 34, TH, col=RED)
    d.text((690, 310), "账户冻结", font=font(28, True), fill=RED, anchor="mm")
    d.text((690, 358), "无需法院令", font=font(21), fill=RED, anchor="mm")
    # 右：两个真实案例
    d.text((1030, 150), "真实发生过", font=font(24, True), fill=TH.TXT, anchor="mm")
    card(d, [850, 186, 1215, 304], TH, r=R_SM)
    d.text((880, 208), "2022 · 加拿大", font=font(22, True), fill=TH.TXT)
    wrap(d, "援引《紧急状态法》直接冻结抗议者账户", 880, 244, 310, font(19), TH.MID, 26, 2)
    card(d, [850, 320, 1215, 438], TH, r=R_SM)
    d.text((880, 342), "2013 · 塞浦路斯", font=font(22, True), fill=TH.TXT)
    wrap(d, "对超过 10 万欧元存款征收约 48%", 880, 378, 310, font(19), TH.MID, 26, 2)
    footer_bar(d, TH, W, H, "账户说冻就冻、说收就收 —— 你拥有的是「使用权」，不是「所有权」",
               color=RED, bg=RED_BG, fs=24)
    save(im, OUT / "04-no-anchor-confiscation.png")


def s2_05():
    """三大缺陷同源：一道裂缝的三处渗水（16:9 砖墙）。"""
    im, d = canvas(TH, "三大缺陷：同一道裂缝的三处渗水", STATION, size="16:9")
    W, H = im.size
    x0, y0, x1, y1 = 80, TOPBAR_H + 40, 1200, 458
    rows, cols = 4, 7
    bw, bh = (x1 - x0) / cols, (y1 - y0) / rows
    for r in range(rows):
        off = bw / 2 if r % 2 else 0
        for c in range(-1, cols + 1):
            bx = x0 + c * bw + off
            if bx < x0 - 1 or bx + bw > x1 + 1:
                continue
            d.rounded_rectangle([bx + 4, y0 + r * bh + 4, bx + bw - 4, y0 + (r + 1) * bh - 4],
                                radius=6, fill=TH.CARD, outline=TH.EDGE, width=2)
    # 三道裂缝（之字红线）
    for cx_ in (300, 640, 980):
        pts = [(cx_, y0 + 6)]
        yy = y0 + 6
        dx = 16
        while yy < y1 - 6:
            yy += 44
            pts.append((cx_ + dx, yy))
            dx = -dx
        d.line(pts, fill=RED, width=5, joint="curve")
    # 三处标注
    labels = [("通胀税", 300, "购买力被稀释"), ("债务货币", 640, "发行量随债务膨胀"), ("审查与没收", 980, "账户可被冻结")]
    for name, lx, sub in labels:
        card(d, [lx - 150, 476, lx + 150, 556], TH, r=R_SM, fill=RED_BG, edge=RED)
        d.text((lx, 498), name, font=font(23, True), fill=RED, anchor="mm")
        d.text((lx, 534), sub, font=font(22), fill=TH.MID, anchor="mm")
    footer_bar(d, TH, W, H, "根因都是「规则可改」—— 只要有人能改规则，规则迟早会被改到对他有利")
    save(im, OUT / "05-common-root.png")


def s2_07():
    """三句话带走（16:9）。"""
    im, d = canvas(TH, "三句话带走本篇", STATION, size="16:9")
    W, H = im.size
    items = [
        ("①", "银行不是反派", "它替我们记账、保管，极大降低了贸易成本；但风险是架构自带的，不是品德问题"),
        ("②", "三大缺陷同源", "无锚点 → 债务货币 → 通胀 → 审查没收：同一条「货币权力被少数人垄断」"),
        ("③", "解法是删掉改规则的权力", "不是换一批更正直的人，而是让规则本身不可被单方修改"),
    ]
    y = TOPBAR_H + 56
    for num, t, s in items:
        card(d, [100, y, 1180, y + 128], TH, r=18, hi=(num == "③"))
        d.text((140, y + 64), num, font=font(44, True), fill=TH.ACCENT, anchor="lm")
        d.text((220, y + 42), t, font=font(29, True), fill=TH.TXT)
        wrap(d, s, 220, y + 84, 900, font(21), TH.MID, 30, 2)
        y += 156
    save(im, OUT / "07-mindmap-summary.png")


FN = {"01": s2_01, "02": s2_02, "03": s2_03, "04": s2_04, "05": s2_05, "07": s2_07}

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    todo = list(FN.values()) if arg == "all" else [FN[arg]]
    for f in todo:
        f()
        print("[OK]", f.__name__, "->", f.__doc__.split("（")[0])
