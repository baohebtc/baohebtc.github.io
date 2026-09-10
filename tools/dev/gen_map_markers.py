# -*- coding: utf-8 -*-
"""
给 learning-map.html 生成 10 站 SVG 标记层（读单一真相源 map-stations.json）。

为什么读 JSON 而不内置坐标：
    上次翻车就是「图上改了、代码没改」——母图 PNG 与网站 SVG 各写一份坐标，
    结果网站标签全在圆点下方，与母图完全是两套。现在坐标只存在 map-stations.json
    一处，PNG 与 SVG 都由它生成，任何改动必须先跑 map_layout.py 再重新生成。

本轮变更（2026-09-10）：
    1. 标签方向改为「上 8 / 左 2 / 下 0」，站名不再出现在站号下方
    2. 标签样式改为 A 羊皮纸牌（米色底 + 深棕边 + 深棕字），与母图 PNG 一致
    3. 新增引线 leader，斜引线把圆点与标签连起来（轴移避障后尤其必要）
    4. 热区改为「圆点 ∪ 标签框」包围盒，支持上方/左右布局

用法：python3 tools/dev/gen_map_markers.py
"""
import re, json, pathlib, sys

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent.parent
HTML = ROOT / "learning-map.html"
JSON_PATH = HERE / "map-stations.json"

NUM_DY = 12   # 数字基线垂直微调（近似居中）


def leader_points(L, r):
    """引线：圆点边缘 → 标签框上离圆点最近那条边的中点"""
    cx, cy, x, y, w, h, d = L["cx"], L["cy"], L["x"], L["y"], L["w"], L["h"], L["dir"]
    if d.startswith("上"):   return (cx, cy - r, cx, y + h)
    if d.startswith("下"):   return (cx, cy + r, cx, y)
    if d.startswith("右"):   return (cx + r, cy, x, cy)
    return (cx - r, cy, x + w, cy)


def build_svg(stations, dot_r):
    out = ['    <svg class="map-overlay" viewBox="0 0 1760 2368" preserveAspectRatio="xMidYMid meet"',
           '         aria-hidden="false" aria-label="10 站可点击热点（含 1.5 站）">']
    for L in stations:
        cx, cy = L["cx"], L["cy"]
        bx, by, bw, bh = L["x"], L["y"], L["w"], L["h"]
        bcx = bx + bw / 2                      # 文字必须按框中心居中，不能用 cx
        # 热区：圆点 ∪ 标签框 的包围盒
        hx, hy = min(cx - dot_r, bx), min(cy - dot_r, by)
        hw = max(cx + dot_r, bx + bw) - hx
        hh = max(cy + dot_r, by + bh) - hy
        x1, y1, x2, y2 = leader_points(L, dot_r)
        out += ["",
                f'      <a class="hotspot" data-num="{L["num"]}" href="{L["href"]}" '
                f'style="--c:{L["color"]};color:{L["color"]}">',
                f'        <title>{L["num"]} · {L["name"]}（{L["view"]}视角）</title>',
                f'        <rect class="hit-area" x="{hx:.0f}" y="{hy:.0f}" width="{hw:.0f}" height="{hh:.0f}"/>',
                f'        <line class="leader" x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}"/>',
                f'        <circle class="dot" cx="{cx}" cy="{cy}" r="{dot_r}"/>',
                f'        <text class="num" x="{cx}" y="{cy + NUM_DY}">{L["num"]}</text>',
                 '        <g class="name-box">',
                f'          <rect class="nb-bg" x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="16"/>',
                f'          <text class="nb-cn" x="{bcx:.0f}" y="{by + 50}">{L["name"]}</text>',
                f'          <text class="nb-view" x="{bcx:.0f}" y="{by + 86}">{L["view"]}</text>',
                 '        </g>',
                 '      </a>']
    out += ["", "    </svg>"]
    return "\n".join(out)


if __name__ == "__main__":
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    stations, P = data["stations"], data["params"]
    dot_r = P["dot_r"]

    # 出图前硬校验：站名不得在下方 + 不越界
    errs = []
    for L in stations:
        if L["dir"].startswith("下"):
            errs.append(f"站{L['num']} 站名在站号下方")
        if not (0 <= L["x"] and L["x"] + L["w"] <= data["canvas"]["w"]):
            errs.append(f"站{L['num']} 横向越界")
        if not (0 <= L["y"] and L["y"] + L["h"] <= data["canvas"]["h"]):
            errs.append(f"站{L['num']} 纵向越界")
    if errs:
        print("❌ 校验未通过，拒绝生成：")
        for e in errs:
            print("   -", e)
        sys.exit(1)
    print(f"✅ 真相源校验通过：{len(stations)} 站，0 站在下方")

    s = HTML.read_text(encoding="utf-8")
    new_svg = build_svg(stations, dot_r)
    s2, n = re.subn(r'    <svg class="map-overlay".*?</svg>', new_svg, s, flags=re.S)
    if n != 1:
        print(f"❌ SVG 块替换失败，匹配到 {n} 处")
        sys.exit(1)
    HTML.write_text(s2, encoding="utf-8")
    print(f"✅ 已写入 {HTML.name}")
    print(f"   dot {s2.count('class=\"dot\"')} · name-box {s2.count('class=\"name-box\"')} "
          f"· leader {s2.count('class=\"leader\"')} · hit-area {s2.count('class=\"hit-area\"')}")
