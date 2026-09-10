# -*- coding: utf-8 -*-
"""
给 learning-map.html 生成「可见的」10 站 SVG 标记层。

背景：之前替换热点坐标时把 dot / name-box 结构删了，只剩透明的 hit-area，
导致地图上什么都看不见（CSS 样式成了孤儿样式）。本脚本重建可见标记层。

设计约束（全部由脚本硬校验）：
1. 标签默认常驻可见（不再 hover 才出现）
2. 标签框不越出画布 1760x2368
3. 标签框两两不重叠（不遮挡）
4. 标签框不压住别的站点圆点
5. 热区 rect 覆盖「圆点 + 标签框」，点哪都能跳转
"""
import re, pathlib, sys

HTML = pathlib.Path("/Users/mac/Desktop/宝盒知识库/比特币学习地图/learning-map.html")
W, H = 1760, 2368

# 站数据：序号, cx, cy, 中文名, 视角, 颜色, 链接
STATIONS = [
    ("1",   395, 1648, "现金湾",       "金融", "#FFD700", "learning/01-philosophy/01-01-money.html"),
    ("1.5", 826, 1690, "钱到底是什么", "金融", "#FFD700", "learning/01-philosophy/01-01-money.html"),
    ("2",   388, 1076, "银行堡",       "商业", "#A78BFA", "learning/01-philosophy/01-02-three-flaws.html"),
    ("3",   961, 1121, "双花峡",       "技术", "#3B82F6", "learning/01-philosophy/01-03-bitcoin-answer.html"),
    ("4",   793,  843, "账本海",       "历史", "#22C55E", "learning/02-basics/02-03-blockchain.html"),
    ("5",  1312,  600, "哈希岭",       "技术", "#3B82F6", "learning/04-technology/04-01-cryptography.html"),
    ("6",   469,  538, "共识峰",       "哲学", "#F7931A", "learning/04-technology/04-05-mining-consensus.html"),
    ("7",  1524,  729, "矿工谷",       "人性", "#F472B6", "learning/02-basics/02-04-mining.html"),
    ("8",  1186,  360, "私钥崖",       "历史", "#22C55E", "learning/02-basics/02-02-keys-ownership.html"),
    ("9",   931,  207, "代码之巅",     "哲学", "#F7931A", "learning/04-technology/04-00-overview.html"),
]

# 版面参数（SVG 用户单位；容器 760px 时缩放比 ≈0.432，故数值取大）
FONT_CN   = 40   # 中文站名字号 → 实际约 17px
FONT_VIEW = 26   # 视角小字     → 实际约 11px
FONT_NUM  = 34   # 序号数字
DOT_R     = 38   # 序号圆点半径 → 实际约 16px
PAD_X     = 25   # 标签框左右内边距
BOX_H     = 100  # 标签框高度
GAP_TOP   = 60   # 圆点中心 → 框顶距离
NUM_DY    = 12   # 数字基线垂直微调（近似居中）

def box_geom(cx, cy, name):
    """按字数算标签框几何"""
    w = len(name) * FONT_CN + PAD_X * 2
    x = cx - w / 2
    y = cy + GAP_TOP
    return x, y, w, BOX_H

# ---------- 硬校验 ----------
def validate():
    errs, warns = [], []
    boxes = []
    for num, cx, cy, name, view, color, href in STATIONS:
        bx, by, bw, bh = box_geom(cx, cy, name)
        boxes.append((num, bx, by, bw, bh))
        # 1. 越界
        if bx < 0 or bx + bw > W:
            errs.append(f"站{num} 标签框横向越界: x[{bx:.0f},{bx+bw:.0f}] 超出 0..{W}")
        if by < 0 or by + bh > H:
            errs.append(f"站{num} 标签框纵向越界: y[{by:.0f},{by+bh:.0f}] 超出 0..{H}")
        # 圆点越界
        if cx - DOT_R < 0 or cx + DOT_R > W or cy - DOT_R < 0 or cy + DOT_R > H:
            errs.append(f"站{num} 圆点越界")

    # 2. 框两两重叠
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            n1, x1, y1, w1, h1 = boxes[i]
            n2, x2, y2, w2, h2 = boxes[j]
            ox = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
            oy = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
            if ox > 0 and oy > 0:
                errs.append(f"站{n1} 与 站{n2} 标签框重叠 {ox:.0f}x{oy:.0f}px")

    # 3. 框压住别的站点圆点
    for n1, x1, y1, w1, h1 in boxes:
        for num, cx, cy, *_ in STATIONS:
            if num == n1:
                continue
            if x1 <= cx <= x1 + w1 and y1 <= cy <= y1 + h1:
                errs.append(f"站{n1} 的标签框压住了 站{num} 的圆点")

    # 4. 圆点间距（提示性）
    import math
    for i in range(len(STATIONS)):
        for j in range(i + 1, len(STATIONS)):
            a, b = STATIONS[i], STATIONS[j]
            d = math.hypot(a[1] - b[1], a[2] - b[2])
            if d < DOT_R * 2 + 20:
                warns.append(f"站{a[0]} 与 站{b[0]} 圆点过近: {d:.0f}px")

    return errs, warns

# ---------- 生成 SVG ----------
def build_svg():
    out = ['    <svg class="map-overlay" viewBox="0 0 1760 2368" preserveAspectRatio="xMidYMid meet"',
           '         aria-hidden="false" aria-label="10 站可点击热点（含 1.5 站）">']
    for num, cx, cy, name, view, color, href in STATIONS:
        bx, by, bw, bh = box_geom(cx, cy, name)
        # 热区：覆盖 圆点 + 标签框
        hx, hy = min(cx - DOT_R, bx), cy - DOT_R - 22
        hw = max(DOT_R * 2, bx + bw - hx)
        hh = (by + bh) - hy
        out.append("")
        out.append(f'      <a class="hotspot" href="{href}" style="--c:{color};color:{color}">')
        out.append(f'        <title>{num} · {name}（{view}视角）</title>')
        out.append(f'        <rect class="hit-area" x="{hx:.0f}" y="{hy:.0f}" width="{hw:.0f}" height="{hh:.0f}"/>')
        out.append(f'        <circle class="dot" cx="{cx}" cy="{cy}" r="{DOT_R}"/>')
        out.append(f'        <text class="num" x="{cx}" y="{cy + NUM_DY}">{num}</text>')
        out.append( '        <g class="name-box">')
        out.append(f'          <rect class="nb-bg" x="{bx:.0f}" y="{by:.0f}" width="{bw:.0f}" height="{bh}" rx="16"/>')
        out.append(f'          <text class="nb-cn" x="{cx}" y="{by + 50}">{name}</text>')
        out.append(f'          <text class="nb-view" x="{cx}" y="{by + 86}">{view}</text>')
        out.append( '        </g>')
        out.append( '      </a>')
    out.append("")
    out.append("    </svg>")
    return "\n".join(out)

if __name__ == "__main__":
    errs, warns = validate()
    if warns:
        print("⚠️  提示:")
        for w in warns:
            print("   -", w)
    if errs:
        print("❌ 校验未通过，拒绝生成:")
        for e in errs:
            print("   -", e)
        sys.exit(1)
    print(f"✅ 版面校验通过：{len(STATIONS)} 站，无越界 / 无重叠 / 无压盖")

    s = HTML.read_text(encoding="utf-8")
    new_svg = build_svg()
    s2, n = re.subn(r'    <svg class="map-overlay".*?</svg>', new_svg, s, flags=re.S)
    assert n == 1, f"SVG 块替换失败，匹配到 {n} 处"
    HTML.write_text(s2, encoding="utf-8")
    print(f"✅ 已写入 {HTML.name}：SVG 标记层重建完成")
    print(f"   dot 元素   : {s2.count('class=\"dot\"')} 个")
    print(f"   name-box   : {s2.count('class=\"name-box\"')} 个")
    print(f"   hit-area   : {s2.count('class=\"hit-area\"')} 个")
