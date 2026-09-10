# -*- coding: utf-8 -*-
"""
学习地图 10 站布局 —— 单一真相源。

为什么要有这一层：
    上次的翻车点是「图上改了、代码没改」——母图 PNG 与网站 SVG 各写一份坐标，
    改一处忘一处，结果网站标签全在圆点下方（违反用户 2026-09-10 拍板的规则），
    而母图是另一套。本模块把坐标/方向/轴移收进一份 JSON，PNG 与 SVG 都从它生成。

数据流：
    map_layout.py ──生成──> map-stations.json ──┬──> gen_map_markers.py   → 网站 SVG
                                                ├──> 母图 PNG 标签渲染     → 图片产品
                                                └──> map-label-check.mjs  → 一致性校验

布局规则（用户拍板）：
    方向优先级 上 > 右 > 左 >> 下（下方仅兜底，站名不得出现在站号圆点下方）
    用户指定：站5 上方、站7 左侧
"""
import json, pathlib

HERE = pathlib.Path(__file__).parent
OUT = HERE / "map-stations.json"

CANVAS = {"w": 1760, "h": 2368}

# 版面参数（SVG 用户单位；容器 760px 时缩放比 ≈0.432）
PARAMS = {
    "font_cn": 40,    # 中文站名 → 实际约 17px
    "font_view": 26,  # 视角小字 → 实际约 11px
    "font_num": 34,   # 序号数字
    "dot_r": 38,      # 序号圆点半径
    "pad_x": 25,      # 标签框左右内边距
    "box_h": 100,     # 标签框高度
    "blend_r": 110,   # 立体地标 blend 半径（标签必须避让）
}

# 站数据：序号, cx, cy, 中文名, 英文名, 视角, 颜色, 链接
STATIONS = [
    ("1",   395, 1648, "现金湾",       "CASH BAY",            "金融", "#FFD700", "learning/01-philosophy/01-01-money.html"),
    ("1.5", 826, 1690, "钱到底是什么", "WHAT IS MONEY",       "金融", "#FFD700", "learning/01-philosophy/01-01-money.html"),
    ("2",   388, 1076, "银行堡",       "BANK FORT",           "商业", "#A78BFA", "learning/01-philosophy/01-02-three-flaws.html"),
    ("3",   961, 1121, "双花峡",       "DOUBLE-SPEND GORGE",  "技术", "#3B82F6", "learning/01-philosophy/01-03-bitcoin-answer.html"),
    ("4",   793,  843, "账本海",       "LEDGER SEA",          "历史", "#22C55E", "learning/02-basics/02-03-blockchain.html"),
    ("5",  1312,  600, "哈希岭",       "HASH RIDGE",          "技术", "#3B82F6", "learning/04-technology/04-01-cryptography.html"),
    ("6",   469,  538, "共识峰",       "CONSENSUS PEAK",      "哲学", "#F7931A", "learning/04-technology/04-05-mining-consensus.html"),
    ("7",  1524,  729, "矿工谷",       "MINER VALLEY",        "人性", "#F472B6", "learning/02-basics/02-04-mining.html"),
    ("8",  1186,  360, "私钥崖",       "KEY CLIFF",           "历史", "#22C55E", "learning/02-basics/02-02-keys-ownership.html"),
    ("9",   931,  207, "代码之巅",     "CODE SUMMIT",         "哲学", "#F7931A", "learning/04-technology/04-00-overview.html"),
]

# 用户指定方向（2026-09-10）：站5 站名放上方、站7 站名放左侧
DIR_OVERRIDE = {"5": "上", "7": "左"}

# 沿轴微调：正对位放不下时，上/下横向滑、左/右纵向滑
SLIDE = [0, 20, -20, 40, -40, 60, -60, 80, -80, 100, -100, 120, -120, 150, -150]

MARGIN, GAPB = 8, 14
CLEAR = PARAMS["blend_r"] + 20   # 与圆点中心的最小净距


def compute_layout():
    """四方向择优 + 沿轴滑动避障，返回 {站号: 布局}"""
    W, H = CANVAS["w"], CANVAS["h"]
    bw_of = lambda name: len(name) * PARAMS["font_cn"] + PARAMS["pad_x"] * 2
    bh = PARAMS["box_h"]
    R = PARAMS["blend_r"]
    placed, layout = {}, {}

    # 用户指定方向的站先占位，避免被自动布局挤掉
    order = ([s for s in STATIONS if s[0] in DIR_OVERRIDE] +
             [s for s in STATIONS if s[0] not in DIR_OVERRIDE])

    for num, cx, cy, name, en, view, color, href in order:
        bw, dirs = bw_of(name), ["上", "右", "左", "下"]
        if num in DIR_OVERRIDE:
            d0 = DIR_OVERRIDE[num]
            dirs = [d0] + [d for d in dirs if d != d0]

        def base(d, off=0):
            if d == "上":   x, y = cx - bw / 2,      cy - CLEAR - bh
            elif d == "下": x, y = cx - bw / 2,      cy + CLEAR
            elif d == "右": x, y = cx + CLEAR,       cy - bh / 2
            else:           x, y = cx - CLEAR - bw,  cy - bh / 2
            return (x + off, y) if d in ("上", "下") else (x, y + off)

        def in_canvas(x, y):
            return not (x < MARGIN or x + bw > W - MARGIN or y < MARGIN or y + bh > H - MARGIN)

        def no_overlap(x, y):
            return all(x + bw + GAPB <= px or px + pw + GAPB <= x or
                       y + bh + GAPB <= py or py + ph + GAPB <= y
                       for px, py, pw, ph in placed.values())

        def no_intrude(x, y):
            for _, sx, sy, *_ in STATIONS:
                if (min(x + bw, sx + R) - max(x, sx - R) > 0 and
                        min(y + bh, sy + R) - max(y, sy - R) > 0):
                    return False
            return True

        chosen = None
        for d in dirs:                       # 第一轮：严格不侵入
            for off in SLIDE:
                x, y = base(d, off)
                if in_canvas(x, y) and no_overlap(x, y) and no_intrude(x, y):
                    chosen = (d, x, y, off); break
            if chosen: break
        if chosen is None:                   # 第二轮：放宽「不侵入」
            for d in dirs:
                for off in SLIDE:
                    x, y = base(d, off)
                    if in_canvas(x, y) and no_overlap(x, y):
                        chosen = (d + "(放宽)", x, y, off); break
                if chosen: break
        if chosen is None:
            raise SystemExit(f"❌ 站{num} 找不到可行标签位置")

        d, x, y, off = chosen
        placed[num] = (x, y, bw, bh)
        layout[num] = {"num": num, "cx": cx, "cy": cy, "name": name, "en": en,
                       "view": view, "color": color, "href": href,
                       "dir": d, "x": round(x), "y": round(y),
                       "w": round(bw), "h": bh, "off": off}
    return layout


def validate(layout):
    """出图前硬校验：越界 / 重叠 / 压盖 / 站名在下方"""
    W, H = CANVAS["w"], CANVAS["h"]
    R = PARAMS["dot_r"]
    errs = []
    for num, L in layout.items():
        if L["x"] < 0 or L["x"] + L["w"] > W or L["y"] < 0 or L["y"] + L["h"] > H:
            errs.append(f"站{num} 标签越界")
        if L["dir"].startswith("下"):
            errs.append(f"站{num} 站名落在站号下方（违反布局规则）")
    items = list(layout.values())
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i], items[j]
            if (max(0, min(a["x"]+a["w"], b["x"]+b["w"]) - max(a["x"], b["x"])) > 0 and
                    max(0, min(a["y"]+a["h"], b["y"]+b["h"]) - max(a["y"], b["y"])) > 0):
                errs.append(f"站{a['num']} 与 站{b['num']} 标签框重叠")
    for a in items:
        for num, cx, cy, *_ in STATIONS:
            if a["x"] - R <= cx <= a["x"] + a["w"] + R and a["y"] - R <= cy <= a["y"] + a["h"] + R:
                if num != a["num"]:
                    errs.append(f"站{a['num']} 标签压住 站{num} 圆点")
    return errs


if __name__ == "__main__":
    layout = compute_layout()
    errs = validate(layout)
    if errs:
        print("❌ 版面校验未通过，拒绝生成 JSON：")
        for e in errs:
            print("   -", e)
        raise SystemExit(1)

    data = {"canvas": CANVAS, "params": PARAMS,
            "dir_override": DIR_OVERRIDE,
            "stations": [layout[s[0]] for s in STATIONS]}
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print("✅ 版面校验通过：无越界 / 无重叠 / 无压盖 / 无站名在下")
    for s in data["stations"]:
        print(f"   站{s['num']:3s} → {s['dir']:4s} ({s['x']:4d},{s['y']:4d}) "
              f"{s['w']}x{s['h']}  轴移{s['off']:+d}px")
    print(f"✅ 已写入 {OUT.relative_to(HERE.parent.parent)}")
