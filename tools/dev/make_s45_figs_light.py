# -*- coding: utf-8 -*-
"""
make_s45_figs_light.py — 站4/站5 配图迁移批次 1（ADR-0008 已采纳：方向 B paper-light）
=====================================================================================
13 张全部走 brand_figs.Theme("paper-light")：色板/规格/字体/品牌三件套单一来源。
站4：01 公开账本 / 02 银行vs比特币 / 03 化名 / 04 UTXO / 05 只追加 / 06 T2表 / 07 三句话
站5：01 指纹机 / 02 四性质 / 03 雪崩 / 04 哈希vs加密 / 05 挖矿 / 07 三句话
用法：python make_s45_figs_light.py [s4|s5|all]
"""
import pathlib, sys, hashlib, math
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from PIL import Image, ImageDraw, ImageFont
from brand_figs import (Theme, canvas, card, chip, arrow, btc, save,
                        font, SIZES, TOPBAR_H, FOOTBAR_H, R_BIG, R_SM)

TH = Theme("paper-light")
ROOT = pathlib.Path("/Users/mac/Desktop/宝盒知识库/比特币学习地图/慢读宝盒公众号")
OUT4 = ROOT / "站4-账本海" / "03-配图"
OUT5 = ROOT / "站5-哈希岭" / "03-配图"

# 浅底语义色（ADR-0008：语义色唯一来源，深色变体保证浅底对比度）
RED,  RED_BG  = (198, 40, 40),  (250, 235, 232)
GREEN, GREEN_BG = (27, 122, 80), (233, 244, 238)
BLUE, BLUE_BG = (58, 124, 186), (233, 241, 248)

def fmono(sz):
    return ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", sz) \
        if pathlib.Path("/System/Library/Fonts/Menlo.ttc").exists() else font(sz)

def dashed(d, p0, p1, dash=10, gap=8, fill=None, width=3):
    x0, y0 = p0; x1, y1 = p1
    L = math.hypot(x1 - x0, y1 - y0); n = int(L // (dash + gap))
    for i in range(n + 1):
        t0 = i * (dash + gap) / L; t1 = min((i * (dash + gap) + dash) / L, 1)
        if t0 >= 1: break
        d.line([(x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0),
                (x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1)], fill=fill or TH.GOLD, width=width)

def wrap(d, text, x, y, maxw, f, fill, lh, max_lines=3):
    lines, cur = [], ""
    for ch in text:
        if d.textlength(cur + ch, font=f) > maxw:
            lines.append(cur); cur = ch
            if len(lines) >= max_lines: break
        else:
            cur += ch
    if cur and len(lines) < max_lines: lines.append(cur)
    for i, ln in enumerate(lines):
        d.text((x, y + i * lh), ln, font=f, fill=fill)

def coin(d, cx, cy, r, label, col):
    """带锁硬币（站4-04 语义图元：UTXO）。"""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=TH.CARD, outline=col, width=4)
    d.rectangle([cx - 10, cy - 4, cx + 10, cy + 12], fill=col)
    d.arc([cx - 14, cy - 22, cx + 14, cy + 2], 180, 360, fill=col, width=4)
    d.text((cx, cy + r + 16), label, font=font(22, True), fill=TH.TXT, anchor="mm")

# ==================== 站4 ====================
def s4_01():
    """公开账本：中心官方标识 + 8 本同步账册（1:1）。"""
    im, d = canvas(TH, "公开账本：人人手里都有一本完整的账", "站4 · 账本海", size="1:1")
    W, H = im.size
    cx, cy = W // 2, (TOPBAR_H + H - FOOTBAR_H) // 2
    d.ellipse([cx - 180, cy - 180, cx + 180, cy + 180], outline=TH.ACCENT, width=4)
    d.ellipse([cx - 150, cy - 150, cx + 150, cy + 150], outline=TH.GOLD, width=2)
    btc(d, im, cx, cy, 300)
    for i in range(8):
        a = 2 * math.pi * i / 8 - math.pi / 2
        lx, ly = cx + int(400 * math.cos(a)), cy + int(400 * math.sin(a))
        d.line([(cx, cy), (lx, ly)], fill=TH.GOLD, width=2)
        lw, lh = 130, 160
        x0, y0 = lx - lw // 2, ly - lh // 2
        card(d, [x0, y0, x0 + lw, y0 + lh], TH, r=10)
        for k in range(4):
            yy = y0 + 26 + k * 28
            d.line([(x0 + 16, yy), (x0 + lw - 16, yy)], fill=TH.DIM, width=2)
        btc(d, im, x0 + lw - 20, y0 + lh - 20, 26)
    save(im, OUT4 / "01-public-ledger.png")

def s4_02():
    """银行 vs 比特币：6 维度对比（4:3，重建图——原脚本已丢失）。"""
    im, d = canvas(TH, "银行账本 vs 比特币公开账本", "站4 · 账本海", size="4:3")
    W, H = im.size
    rows = [
        ("管理者", "单一机构（内部账）", "全球分布式网络（无单点）"),
        ("可见性", "仅本人 / 授权方", "全网公开可查"),
        ("可否篡改", "管理员可直接改", "数学上不可行（需重算整链）"),
        ("验证方式", "信任机构", "任何人独立验证"),
        ("停机风险", "服务器宕机即中断", "永远在线（只要互联网在）"),
        ("一句类比", "保险柜里的私密本", "广场上同步的公开碑"),
    ]
    x_dim, x_l, x_r = 110, 350, 790
    w_l, w_r = 410, 420
    y = TOPBAR_H + 40
    # 列头
    for x, w, t, col in [(x_l, w_l, "银行账本", TH.MID), (x_r, w_r, "比特币公开账本", TH.ACCENT)]:
        d.rounded_rectangle([x, y, x + w, y + 64], radius=R_SM, fill=TH.CARD_HI,
                            outline=col, width=3)
        d.text((x + w / 2, y + 32), t, font=font(30, True), fill=col, anchor="mm")
    y += 84
    for i, (dim, a, b) in enumerate(rows):
        fill = TH.CARD if i % 2 == 0 else TH.CARD_HI
        d.rounded_rectangle([x_dim, y, 1230, y + 88], radius=10, fill=fill,
                            outline=TH.EDGE, width=1)
        d.text((x_dim + 24, y + 44), dim, font=font(26, True), fill=TH.TXT, anchor="lm")
        d.text((x_l + w_l / 2, y + 44), a, font=font(24), fill=TH.MID, anchor="mm")
        d.text((x_r + w_r / 2, y + 44), b, font=font(24, True), fill=TH.GOLD, anchor="mm")
        y += 100
    save(im, OUT4 / "02-bank-vs-btc.png")

def s4_03():
    """化名 ≠ 匿名：左面具地址 / 右真名证件 / 中间 KYC 揭面（16:9）。"""
    im, d = canvas(TH, "化名 ≠ 匿名：面具什么时候被揭开", "站4 · 账本海", size="16:9")
    W, H = im.size
    y0, ch = TOPBAR_H + 70, 400
    # 左：化名（绿）
    lx, lw = 90, 360
    d.rounded_rectangle([lx, y0, lx + lw, y0 + ch], radius=R_BIG, fill=GREEN_BG,
                        outline=GREEN, width=3)
    d.text((lx + 30, y0 + 30), "化名 Pseudonym", font=font(34, True), fill=GREEN)
    mx, my = lx + lw // 2, y0 + 190
    d.ellipse([mx - 70, my - 80, mx + 70, my + 80], fill=TH.CARD, outline=GREEN, width=3)
    for sgn in (-1, 1):
        d.line([(mx + sgn * 45, my - 10), (mx + sgn * 15, my - 10)], fill=GREEN, width=4)
    d.text((mx, y0 + 320), "bc1q…x7f9k2p", font=fmono(28), fill=TH.TXT, anchor="mm")
    # 右：真名（红）
    rx, rw = W - 90 - 360, 360
    d.rounded_rectangle([rx, y0, rx + rw, y0 + ch], radius=R_BIG, fill=RED_BG,
                        outline=RED, width=3)
    d.text((rx + 30, y0 + 30), "真名 Real ID", font=font(34, True), fill=RED)
    d.rounded_rectangle([rx + 30, y0 + 110, rx + 140, y0 + 250], radius=10,
                        fill=TH.CARD, outline=TH.EDGE, width=2)
    d.text((rx + 180, y0 + 140), "张三", font=font(30, True), fill=TH.TXT)
    d.text((rx + 180, y0 + 196), "身份证 5201…", font=font(22), fill=TH.MID)
    # 中间：揭面
    bx0, bx1 = lx + lw + 16, rx - 16
    by = y0 + ch // 2
    dashed(d, (bx0, by), (bx1, by))
    t = "KYC / 地址复用 → 面具揭开"
    f = font(24, True); tw = d.textlength(t, font=f)
    cxm = (bx0 + bx1) // 2
    d.rounded_rectangle([cxm - tw / 2 - 16, by - 40, cxm + tw / 2 + 16, by + 40],
                        radius=10, fill=RED_BG, outline=RED, width=2)
    d.text((cxm, by), t, font=f, fill=RED, anchor="mm")
    d.text((cxm, y0 + ch + 36), "地址本身不透露身份 —— 关联行为才透露",
           font=font(24), fill=TH.MID, anchor="mm")
    save(im, OUT4 / "03-pseudonym.png")

def s4_04():
    """UTXO：没有余额，只有带锁硬币（16:9）。"""
    im, d = canvas(TH, "没有「余额」，只有带锁硬币", "站4 · 账本海", size="16:9")
    W, H = im.size
    cy = TOPBAR_H + 240
    coin(d, 190, cy - 90, 62, "0.5", TH.ACCENT)
    coin(d, 190, cy + 100, 62, "0.3", TH.GOLD)
    d.text((190, cy + 210), "你的 UTXO 集", font=font(22), fill=TH.MID, anchor="mm")
    arrow(d, (300, cy), (460, cy), TH)
    cxm = 545
    d.ellipse([cxm - 62, cy - 62, cxm + 62, cy + 62], fill=RED_BG, outline=RED, width=4)
    d.line([(cxm - 44, cy - 44), (cxm + 44, cy + 44)], fill=RED, width=4)
    d.line([(cxm + 44, cy - 44), (cxm - 44, cy + 44)], fill=RED, width=4)
    d.text((cxm, cy + 100), "花掉 0.5（整枚）", font=font(22), fill=RED, anchor="mm")
    arrow(d, (640, cy), (800, cy), TH)
    coin(d, 890, cy - 90, 58, "0.3 → 对方", TH.ACCENT)
    coin(d, 890, cy + 100, 58, "0.2 → 找零", TH.GOLD)
    d.text((1080, cy - 90), "旧币销毁", font=font(22), fill=TH.MID, anchor="lm")
    d.text((1080, cy + 100), "找零回新币", font=font(22), fill=TH.MID, anchor="lm")
    fy = H - FOOTBAR_H - 90
    d.rounded_rectangle([80, fy, W - 80, fy + 62], radius=R_SM, fill=TH.CARD_HI,
                        outline=TH.ACCENT, width=2)
    d.text((W // 2, fy + 31), "不是从账户里扣数字，而是「烧掉整枚旧硬币，铸出两枚新硬币」",
           font=font(26, True), fill=TH.TXT, anchor="mm")
    save(im, OUT4 / "04-utxo.png")

def s4_05():
    """只追加 + 指纹锁链：改一页，后续全断（16:9）。"""
    im, d = canvas(TH, "改不动：只追加 + 指纹锁链", "站4 · 账本海", size="16:9")
    W, H = im.size
    pages = [("创世页", "0000...", False), ("第 99 页", "a1b2...", False),
             ("第 100 页", "XXXXXX", True), ("第 101 页", "......", True),
             ("第 102 页", "......", True)]
    pw, ph, gap = 210, 330, 30
    x0, y0 = 70, TOPBAR_H + 90
    for i, (label, hsh, broken) in enumerate(pages):
        px = x0 + i * (pw + gap)
        fill = RED_BG if broken else TH.CARD
        outl = RED if broken else TH.EDGE
        d.rounded_rectangle([px, y0, px + pw, y0 + ph], radius=10, fill=fill,
                            outline=outl, width=3)
        d.text((px + pw / 2, y0 + 36), label, font=font(24, True),
               fill=RED if broken else TH.TXT, anchor="mm")
        d.text((px + pw / 2, y0 + 110), f"hash:{hsh}", font=fmono(22),
               fill=RED if broken else TH.GOLD, anchor="mm")
        if i:
            d.text((px + pw / 2, y0 + 158), f"prev:{pages[i-1][1]}", font=fmono(22),
                   fill=RED if broken else TH.MID, anchor="mm")
        else:
            d.text((px + pw / 2, y0 + 158), "prev: —", font=fmono(22),
                   fill=TH.MID, anchor="mm")
        if i < 4:
            ax = px + pw + 3
            if broken:
                d.text((ax + gap // 2, y0 + ph // 2), "×", font=font(34, True),
                       fill=RED, anchor="mm")
            else:
                d.polygon([(ax, y0 + ph // 2), (ax + gap - 4, y0 + ph // 2 - 12),
                           (ax + gap - 4, y0 + ph // 2 + 12)], fill=TH.ACCENT)
        if broken:
            d.text((px + pw / 2, y0 + ph - 34), "链断裂", font=font(22, True),
                   fill=RED, anchor="mm")
    fy = y0 + ph + 42
    d.text((W // 2, fy + 20), "改一页 → 后面每一页的 prev 指纹对不上 → 立刻穿帮",
           font=font(27, True), fill=TH.TXT, anchor="mm")
    save(im, OUT4 / "06-append-only.png")

def s4_06():
    """T2 对比表：账户模型 vs UTXO 模型（4:3，沿用 make_t2_table 数据）。"""
    im, d = canvas(TH, "T2 对比：账户模型 vs UTXO 模型", "站4 · 账本海", size="4:3")
    W, H = im.size
    rows = [
        ("状态表示", "地址 → 余额（账户表）", "一组未花输出（硬币集）"),
        ("余额查询", "直接读账户余额", "累加属于你的 UTXO"),
        ("隐私", "地址常复用，易画像", "可换新地址，更难关联"),
        ("双花防御", "靠 nonce / 状态校验", "花掉即失效，天然防重花"),
        ("并行验证", "改共享状态需排序", "独立 UTXO 可并行校验"),
        ("代表", "以太坊 / Solana", "比特币 / 莱特币"),
    ]
    x_dim, x_a, x_b = 110, 480, 860
    y = TOPBAR_H + 40
    d.rounded_rectangle([x_a, y, 1180, y + 62], radius=R_SM, fill=TH.CARD_HI,
                        outline=TH.EDGE, width=2)
    d.text(((x_a + 1180) / 2, y + 31), "账户模型", font=font(28, True), fill=TH.MID, anchor="mm")
    d.rounded_rectangle([x_b, y, 1180, y + 62], radius=R_SM, fill=TH.CARD_HI,
                        outline=TH.ACCENT, width=3)
    d.text(((x_b + 1180) / 2, y + 31), "UTXO 模型", font=font(28, True), fill=TH.ACCENT, anchor="mm")
    y += 82
    for i, (dim, a, b) in enumerate(rows):
        fill = TH.CARD if i % 2 == 0 else TH.CARD_HI
        d.rounded_rectangle([x_dim, y, 1180, y + 92], radius=10, fill=fill,
                            outline=TH.EDGE, width=1)
        d.text((x_dim + 22, y + 46), dim, font=font(25, True), fill=TH.TXT, anchor="lm")
        d.text((x_a + 40, y + 46), a, font=font(23), fill=TH.MID, anchor="lm")
        d.text((x_b + 30, y + 46), b, font=font(23, True), fill=TH.GOLD, anchor="lm")
        y += 102
    save(im, OUT4 / "05-t2-utxo-table.png")

def s4_07():
    """三句话带走（16:9，三竖卡 + 官方标识）。"""
    im, d = canvas(TH, "三句话带走本篇", "站4 · 账本海 · 公开却不泄密", size="16:9")
    W, H = im.size
    cards = [
        ("①", "账本是什么", "全球同步、人人可查的公开碑", TH.ACCENT),
        ("②", "化名不匿名", "地址≠你；KYC / 复用会揭开", GREEN),
        ("③", "改不动", "只追加 + 指纹锁链，改一页全断", RED),
    ]
    cw, ch, gap = 380, 380, 40
    x0 = (W - (cw * 3 + gap * 2)) // 2
    y = TOPBAR_H + 60
    for i, (no, t, sub, col) in enumerate(cards):
        cx = x0 + i * (cw + gap)
        card(d, [cx, y, cx + cw, y + ch], TH, r=R_BIG, edge=col, width=3)
        d.ellipse([cx + 30, y + 30, cx + 90, y + 90], fill=col)
        d.text((cx + 60, y + 60), no, fill=TH.BG, font=font(40, True), anchor="mm")
        d.text((cx + cw // 2, y + 150), t, font=font(36, True), fill=TH.TXT, anchor="mm")
        wrap(d, sub, cx + 40, y + 210, cw - 80, font(23), TH.MID, 34)
        btc(d, im, cx + cw // 2, y + ch - 66, 52)
    save(im, OUT4 / "08-mindmap-summary.png")

# ==================== 站5 ====================
def s5_01():
    """指纹机：任意输入 → 固定输出（16:9）。"""
    im, d = canvas(TH, "哈希函数：数字世界的指纹机", "站5 · 哈希岭", size="16:9")
    W, H = im.size
    cy = TOPBAR_H + 250
    inputs = [("一个字「比」", 175), ("一篇 4500 字文章", 245), ("整部《红楼梦》", 280)]
    for i, (t, wd) in enumerate(inputs):
        y = TOPBAR_H + 66 + i * 128
        d.rounded_rectangle([80, y, 80 + wd, y + 84], radius=R_SM, fill=TH.CARD,
                            outline=TH.EDGE, width=2)
        d.text((80 + wd / 2, y + 42), t, font=font(25), fill=TH.TXT, anchor="mm")
        d.text((80 + wd / 2, y - 18), f"输入 {i+1}", font=font(22), fill=TH.MID, anchor="mm")
        d.line([90 + wd, y + 42, 500, cy], fill=TH.ACCENT, width=3)
    d.rounded_rectangle([500, cy - 110, 780, cy + 110], radius=R_BIG, fill=TH.CARD_HI,
                        outline=TH.ACCENT, width=4)
    d.text((640, cy - 40), "SHA-256", font=font(38, True), fill=TH.ACCENT, anchor="mm")
    d.text((640, cy + 14), "哈希函数", font=font(27), fill=TH.TXT, anchor="mm")
    d.text((640, cy + 60), "只进不出 · 单向", font=font(22), fill=TH.MID, anchor="mm")
    hx = hashlib.sha256("比特币".encode()).hexdigest()
    d.rounded_rectangle([860, cy - 100, 1220, cy + 100], radius=16, fill=TH.CARD,
                        outline=TH.GOLD, width=3)
    d.text((1040, cy - 68), "输出 · 永远 64 字符", font=font(22), fill=TH.GOLD, anchor="mm")
    for r in range(4):
        d.text((1040, cy - 30 + r * 34), hx[r * 16:(r + 1) * 16],
               font=fmono(22), fill=TH.TXT, anchor="mm")
    d.line([780, cy, 860, cy], fill=TH.GOLD, width=3)
    d.rounded_rectangle([80, 574, 1200, 636], radius=R_SM, fill=TH.CARD_HI,
                        outline=TH.ACCENT, width=2)
    d.text((640, 605), "一串 64 字符的「指纹」＝ 这份数据改不掉的身份证明",
           font=font(27, True), fill=TH.TXT, anchor="mm")
    save(im, OUT5 / "01-hash-machine.png")

def s5_02():
    """四条性质 2×2（16:9）。"""
    im, d = canvas(TH, "凭什么被全网信任：四条硬性质", "站5 · 缺一条，整座楼塌", size="16:9")
    W, H = im.size
    cards = [
        ("01", "确定性", "同一输入 → 永远同一输出", "今天算、一百年后算、任何设备算，逐位相同"),
        ("02", "单向性", "算得出指纹，倒推不出原文", "除了逐个猜，没有任何更快的办法"),
        ("03", "雪崩效应", "改一丁点 → 输出面目全非", "改 1 个字，约一半比特位翻转"),
        ("04", "抗碰撞", "找不到两份数据共用一枚指纹", "2²⁵⁶ 种输出 ≈ 10⁷⁷，比地球原子还多"),
    ]
    cw, ch, gx, gy = 560, 214, 40, 34
    x0, y0 = (W - cw * 2 - gx) // 2, TOPBAR_H + 44
    for i, (no, t, s1, s2) in enumerate(cards):
        r, c = divmod(i, 2)
        x, y = x0 + c * (cw + gx), y0 + r * (ch + gy)
        card(d, [x, y, x + cw, y + ch], TH, hi=(i in (1, 2)), r=18,
             edge=TH.ACCENT if i in (1, 2) else TH.EDGE, width=3)
        d.text((x + 28, y + 30), no, font=font(30, True), fill=TH.GOLD)
        d.text((x + 90, y + 32), t, font=font(32, True), fill=TH.TXT)
        d.text((x + 28, y + 106), s1, font=font(25), fill=TH.TXT)
        wrap(d, s2, x + 28, y + 152, cw - 56, font(20), TH.MID, 30)
    save(im, OUT5 / "02-four-properties.png")

def s5_03():
    """雪崩效应（16:9，实测哈希）。"""
    im, d = canvas(TH, "雪崩效应：改一个字，指纹翻脸", "站5 · 「改不动」的物理基础", size="16:9")
    W, H = im.size
    rows = [
        ('SHA-256("比特币")', hashlib.sha256("比特币".encode()).hexdigest(), TH.ACCENT),
        ('SHA-256("比特币！")', hashlib.sha256("比特币！".encode()).hexdigest(), BLUE),
    ]
    y = TOPBAR_H + 60
    for title, hx, col in rows:
        d.rounded_rectangle([80, y, 1200, y + 140], radius=16, fill=TH.CARD,
                            outline=col, width=3)
        d.text((110, y + 34), title, font=font(29, True), fill=col)
        d.text((110, y + 92), hx[:64], font=fmono(22), fill=TH.TXT)
        y += 190
    diff = sum(1 for a, b in zip(rows[0][1], rows[1][1]) if a != b)
    d.rounded_rectangle([80, 540, 1200, 636], radius=R_SM, fill=TH.CARD_HI,
                        outline=TH.GOLD, width=2)
    d.text((640, 572), f"64 个字符里 {diff} 个不同 · 输入只多了一个感叹号",
           font=font(27, True), fill=TH.TXT, anchor="mm")
    d.text((640, 612), "新旧指纹之间看不出任何关联 —— 这就是「改一个字，链条全断」的原因",
           font=font(20), fill=TH.MID, anchor="mm")
    save(im, OUT5 / "03-avalanche.png")

def s5_04():
    """哈希 ≠ 加密 表图（16:9）。"""
    im, d = canvas(TH, "常见误解：哈希 ≠ 加密", "站5 · T1 一张表分清", size="16:9")
    W, H = im.size
    headers = ["", "哈希", "加密"]
    rows = [
        ("能不能还原", "不能 · 单向", "能 · 有密钥就能解"),
        ("要不要密钥", "不要", "要"),
        ("输出长度", "固定 64 字符", "跟输入差不多长"),
        ("典型用途", "校验完整性 · 指纹", "保密传输"),
    ]
    colx = [140, 470, 850]; cw2 = [300, 340, 330]
    y = TOPBAR_H + 46
    d.rounded_rectangle([100, y, 1180, y + 68], radius=12, fill=TH.CARD_HI,
                        outline=TH.EDGE, width=2)
    for j, htxt in enumerate(headers):
        if j:
            d.text((colx[j] + cw2[j] // 2, y + 34), htxt, font=font(29, True),
                   fill=TH.ACCENT if j == 1 else BLUE, anchor="mm")
    y += 84
    for i, (dim, a, b) in enumerate(rows):
        fill = TH.CARD if i % 2 == 0 else TH.CARD_HI
        d.rounded_rectangle([100, y, 1180, y + 84], radius=10, fill=fill)
        d.text((colx[0], y + 42), dim, font=font(25, True), fill=TH.TXT, anchor="lm")
        d.text((colx[1] + cw2[1] // 2, y + 42), a, font=font(23), fill=TH.GOLD, anchor="mm")
        d.text((colx[2] + cw2[2] // 2, y + 42), b, font=font(23), fill=BLUE, anchor="mm")
        y += 92
    d.rounded_rectangle([100, y + 10, 1180, y + 82], radius=R_SM, fill=TH.CARD_HI,
                        outline=TH.ACCENT, width=2)
    d.text((640, y + 46), "判断口诀：算完还能变回原文的，就不是哈希",
           font=font(27, True), fill=TH.TXT, anchor="mm")
    save(im, OUT5 / "04-hash-vs-encryption.png")

def s5_05():
    """挖矿 = 掷骰子（16:9）。"""
    im, d = canvas(TH, "挖矿到底在算什么：掷骰子", "站5 · 没有巧妙解法 · 纯暴力试错", size="16:9")
    W, H = im.size
    tries = [
        ("nonce = 0", "8f2a1c…", "× 开头不是 0", TH.MID),
        ("nonce = 1", "c71b9e…", "×", TH.MID),
        ("nonce = 2", "03e97f…", "× 还不够小", TH.MID),
        ("…", "…", "", TH.MID),
        ("nonce = 847293", "0000a3f2…", "√ 中了！拿到记账权", TH.GOLD),
    ]
    y = TOPBAR_H + 44
    for nonce, hx, verdict, col in tries:
        win = "√" in verdict
        d.rounded_rectangle([120, y, 1160, y + 72], radius=12,
                            fill=TH.CARD_HI if win else TH.CARD,
                            outline=TH.GOLD if win else TH.EDGE,
                            width=3 if win else 1)
        d.text((150, y + 36), nonce, font=font(25, True), fill=TH.TXT, anchor="lm")
        d.text((520, y + 36), "SHA-256 →  " + hx, font=fmono(21), fill=TH.ACCENT, anchor="lm")
        if verdict:
            d.text((1130, y + 36), verdict, font=font(22), fill=col, anchor="rm")
        y += 88
    d.rounded_rectangle([120, y + 8, 1160, y + 92], radius=R_SM, fill=TH.CARD_HI,
                        outline=TH.GOLD, width=2)
    d.text((640, y + 34), "难做：要试几百万次 ｜ 易验证：其他人代一遍 1 秒就知道真假",
           font=font(26, True), fill=TH.TXT, anchor="mm")
    d.text((640, y + 72), "算力即门票，但不保证收益 —— 这正是下一站「共识峰」的引子",
           font=font(19), fill=TH.MID, anchor="mm")
    save(im, OUT5 / "05-mining-nonce.png")

def s5_07():
    """三句话带走（16:9）。"""
    im, d = canvas(TH, "三句话带走本篇", "站5 · 哈希岭", size="16:9")
    W, H = im.size
    items = [
        ("①", "哈希是指纹机，不是保险箱", "任意长度输入 → 固定 64 字符输出；它不藏内容，它盖章"),
        ("②", "四条性质撑起信任", "确定 · 单向 · 雪崩 · 抗碰撞 —— 缺一条，改不动的账本就不成立"),
        ("③", "挖矿 = 全网掷骰子", "改 nonce 撞出足够小的哈希；难做易验证，所以无裁判也能记账"),
    ]
    y = TOPBAR_H + 56
    for num, t, s in items:
        card(d, [100, y, 1180, y + 128], TH, r=18)
        d.text((140, y + 64), num, font=font(44, True), fill=TH.ACCENT, anchor="lm")
        d.text((220, y + 42), t, font=font(29, True), fill=TH.TXT)
        d.text((220, y + 90), s, font=font(21), fill=TH.MID)
        y += 156
    save(im, OUT5 / "07-mindmap-summary.png")

FN = {"s4": [s4_01, s4_02, s4_03, s4_04, s4_05, s4_06, s4_07],
      "s5": [s5_01, s5_02, s5_03, s5_04, s5_05, s5_07]}
arg = sys.argv[1] if len(sys.argv) > 1 else "all"
todo = FN["s4"] + FN["s5"] if arg == "all" else FN[arg]
for f in todo:
    f()
print(f"done: {len(todo)} figs (paper-light)")
