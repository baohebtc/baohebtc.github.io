# -*- coding: utf-8 -*-
"""
fig-layout-check.py — 配图排版体检门闸（ADR-0014）
=====================================================
做法：hook PIL 绘图层，在配图**真实生成过程**中记录
  · 每段文字的精确 bbox + 字号 + 内容
  · 每个容器（卡片/圆角框）的 box
再做四项检测（中文科普图经验阈值）：

  L1 行距：同容器内垂直相邻、水平重叠>50% 的文本，(行间距 / 字高) ≥ 0.35
           —— 相当于 lh/fs ≥ 1.35，低于此中文会显得糊在一起
  L2 内边距：文本到所在容器四边 ≥ 0.45 × fs
  L3 溢出：文本 bbox 超出所在容器（含超出内容区：画布去掉顶/底栏）
  L4 贴底：文本内容区底部留白 < 28px（会蹭到合规条）

为什么用 hook 而不是像素反推：像素反推会把"同高度但不同列"的两段文字误判为相邻，
产生大量假阳性。hook 拿到的是绘制时的真实 bbox，精确且可定位到具体文字。

用法：
    python3 tools/dev/fig-layout-check.py                 # 全系列
    python3 tools/dev/fig-layout-check.py --station 9     # 单站
    python3 tools/dev/fig-layout-check.py --strict        # L1 阈值提高到 0.45
    python3 tools/dev/fig-layout-check.py --quiet         # 只打印结论
"""
from __future__ import annotations
import argparse, importlib, pathlib, sys, collections, statistics

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "dev"))

from PIL import ImageDraw

# (站号, 产线模块, 该站在 FN 里的 key；key=None 表示 FN 是扁平列表)
STATIONS = [
    ("站1", "make_s13_figs_light.py", "s1"),
    ("站1.5", "make_s13_figs_light.py", "s15"),
    ("站2", "make_s2_figs_light.py", None),
    ("站3", "make_s13_figs_light.py", "s3"),
    ("站4", "make_s45_figs_light.py", "s4"),
    ("站5", "make_s45_figs_light.py", "s5"),
    ("站6", "make_s6_figs_light.py", None),
    ("站7", "make_s7_figs_light.py", None),
    ("站8", "make_s8_figs_light.py", None),
    ("站9", "make_s9_figs_light.py", None),
]

TOPBAR_H, FOOTBAR_H = 66, 56
SIZES = {"16:9": (1280, 720), "4:3": (1280, 960), "1:1": (1280, 1280)}

# ── 录制器 ────────────────────────────────────────────────
REC = {"texts": [], "boxes": [], "fig": None}

_orig_text = ImageDraw.ImageDraw.text
_orig_rr = ImageDraw.ImageDraw.rounded_rectangle
_orig_rect = ImageDraw.ImageDraw.rectangle


def _rec_text(self, xy, text, font=None, fill=None, *a, **kw):
    if isinstance(text, str) and text.strip():
        anchor = kw.get("anchor")
        try:
            bb = self.textbbox(xy, text, font=font, anchor=anchor)
        except Exception:
            bb = None
        if bb:
            REC["texts"].append(dict(fig=REC["fig"], box=bb,
                                     fs=getattr(font, "size", 0) or 20,
                                     text=text, anchor=anchor))
    return _orig_text(self, xy, text, font=font, fill=fill, *a, **kw)


def _rec_box(self, xy, *a, **kw):
    if isinstance(xy, list):
        x0, y0, x1, y1 = xy
    else:
        x0, y0, x1, y1 = xy[0], xy[1], xy[2], xy[3]
    if isinstance(y0, tuple):                  # 兼容 polygon 式调用
        return None
    w, h = x1 - x0, y1 - y0
    if w <= 60 or h <= 40:                     # 排除细线条 / 色条
        return None
    # full = 顶栏/底栏/全宽底块：它们是画布框架，不是"容器"，但用来推算画布尺寸
    full = (x0 <= 2 and w >= 1200)
    REC["boxes"].append(dict(fig=REC["fig"], box=(x0, y0, x1, y1), full=full))
    return None


def _rec_rr(self, xy, radius=0, *a, **kw):
    _rec_box(self, xy)
    return _orig_rr(self, xy, radius=radius, *a, **kw)


def _rec_rect(self, xy, *a, **kw):
    _rec_box(self, xy)
    return _orig_rect(self, xy, *a, **kw)


ImageDraw.ImageDraw.text = _rec_text
ImageDraw.ImageDraw.rounded_rectangle = _rec_rr
ImageDraw.ImageDraw.rectangle = _rec_rect


# ── 几何判定 ──────────────────────────────────────────────
def _inside(t, c, tol=3):
    tx0, ty0, tx1, ty1 = t["box"]
    cx0, cy0, cx1, cy1 = c["box"]
    mx, my = (tx0 + tx1) / 2, (ty0 + ty1) / 2
    return (cx0 - tol) <= mx <= (cx1 + tol) and (cy0 - tol) <= my <= (cy1 + tol)


def _contain_of(t, boxes):
    cands = [c for c in boxes if not c.get("full") and _inside(t, c)]
    if not cands:
        return None
    return min(cands, key=lambda c: (c["box"][2] - c["box"][0]) * (c["box"][3] - c["box"][1]))


def _h_overlap(a, b):
    ax0, _, ax1, _ = a
    bx0, _, bx1, _ = b
    inter = max(0, min(ax1, bx1) - max(ax0, bx0))
    return inter / max(1, min(ax1 - ax0, bx1 - bx0))


def _run(figs):
    """逐个 fig 函数重跑（module import 时的副作用记录会被清掉）"""
    REC["texts"], REC["boxes"] = [], []
    for fg, fn in figs:
        REC["fig"] = fg
        n_t, n_b = len(REC["texts"]), len(REC["boxes"])
        fn()
        for t in REC["texts"][n_t:]:
            t["fig"] = fg
        for b in REC["boxes"][n_b:]:
            b["fig"] = fg


def _collect():
    """返回 [(站号, [(fig名, fn), ...])]；import 时屏蔽 argv，防产线脚本误读门闸参数"""
    jobs = []
    saved = sys.argv
    sys.argv = [saved[0]]
    try:
        for st, mod, key in STATIONS:
            mod3 = mod[:-3] if mod.endswith(".py") else mod
            m = importlib.import_module(mod3)
            fns = getattr(m, "FN", None)
            if fns is None:
                continue
            if isinstance(fns, dict):
                raw = fns.get(key, []) if key else list(fns.values())
            elif isinstance(fns, (list, tuple)):
                raw = list(fns)
            else:
                raw = [fns]
            flat = []
            for x in raw:
                flat.extend(x) if isinstance(x, (list, tuple)) else flat.append(x)
            jobs.append((st, [(f"{st}:{fn.__name__}", fn) for fn in flat]))
    finally:
        sys.argv = saved
    return jobs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--station", default=None)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    l1_th = 0.45 if args.strict else 0.35
    pad_th = 0.45
    bottom_th = 28

    jobs = _collect()
    if args.station:
        jobs = [j for j in jobs if j[0] == args.station]
        if not jobs:
            print(f"未知站号：{args.station}")
            return 1

    figs = []
    for st, group in jobs:
        figs.extend(group)
    _run(figs)

    if not args.quiet:
        print("=" * 110)
        print(f"fig-layout-check · L1行距比≥{l1_th} · L2内边距≥{pad_th}×fs · L3溢出 · L4底部留白≥{bottom_th}px")
        print("=" * 110)
        print(f"{'fig':<22}{'文字':<6}{'L1中位':<9}{'L1最小':<9}{'L2最小':<9}{'L3':<5}{'L4':<5}判定")
        print("-" * 110)

    rows, n_l3, n_l4, n_l1, n_l2 = [], 0, 0, 0, 0
    for fg, _fn in figs:
        ts = [t for t in REC["texts"] if t["fig"] == fg]
        bs = [b for b in REC["boxes"] if b["fig"] == fg]
        if not ts:
            continue
        fulls = [b for b in bs if b.get("full")]
        if fulls:
            W = max(max(b["box"][2] for b in fulls), 1280)
            H = max(max(b["box"][3] for b in fulls), 720)
        else:
            W = max([b["box"][2] for b in bs] + [1280])
            H = 960 if any(b["box"][3] > 780 for b in bs) else 720

        # chrome = 框架文字（顶栏图题/站别、底栏品牌系别/合规短句），不参与体检
        def is_chrome(t):
            ty0, ty1 = t["box"][1], t["box"][3]
            cy = (ty0 + ty1) / 2
            return cy <= TOPBAR_H + 2 or cy >= H - FOOTBAR_H - 2

        ts = [t for t in ts if not is_chrome(t)]
        if not ts:
            continue

        l1s, pads, l3, l4 = [], [], [], []
        for t in ts:
            tx0, ty0, tx1, ty1 = t["box"]
            fs = t["fs"]
            # L3：超出内容区
            if tx0 < 8 or tx1 > W - 8 or ty0 < TOPBAR_H + 2 or ty1 > H - FOOTBAR_H - 2:
                l3.append(("画布", t["text"][:22]))
            # L4：贴底
            if ty1 > H - FOOTBAR_H - bottom_th:
                l4.append(t["text"][:22])
            c = _contain_of(t, bs)
            if c is not None:
                cx0, cy0, cx1, cy1 = c["box"]
                pads.append(min(tx0 - cx0, cx1 - tx1, ty0 - cy0, cy1 - ty1) / fs)
                if tx0 < cx0 - 3 or tx1 > cx1 + 3 or ty0 < cy0 - 3 or ty1 > cy1 + 3:
                    l3.append(("容器", t["text"][:22]))

        # L1：容器内垂直相邻、水平重叠的文本
        for c in [c for c in bs if not c.get("full")]:
            inn = sorted([t for t in ts if _inside(t, c)], key=lambda t: t["box"][1])
            for i in range(len(inn) - 1):
                a, b = inn[i], inn[i + 1]
                if _h_overlap(a["box"], b["box"]) < 0.5:
                    continue
                gap = b["box"][1] - a["box"][3]
                hgt = min(a["box"][3] - a["box"][1], b["box"][3] - b["box"][1])
                if hgt < 6 or gap < 0:
                    continue
                l1s.append((gap / hgt, a["text"][:16], b["text"][:16]))

        med = statistics.median([x[0] for x in l1s]) if l1s else float("nan")
        mn = min([x[0] for x in l1s]) if l1s else float("nan")
        pmn = min(pads) if pads else float("nan")
        bad = []
        if l1s and mn < l1_th:
            bad.append("L1挤")
            n_l1 += 1
        if pads and pmn < pad_th:
            bad.append("L2挤边")
            n_l2 += 1
        if l3:
            bad.append("L3溢出")
            n_l3 += len(l3)
        if l4:
            bad.append("L4贴底")
            n_l4 += len(l4)
        rows.append((fg, len(ts), med, mn, pmn, l3, l4, l1s, ",".join(bad) or "ok"))
        if not args.quiet:
            print(f"{fg:<22}{len(ts):<6}{med:<9.2f}{mn:<9.2f}{pmn:<9.2f}{len(l3):<5}{len(l4):<5}{rows[-1][-1]}")
        if pads and pmn < pad_th and not args.quiet:
            worst = sorted(zip(pads, ts_route))[:3] if False else None
            # 找出 pad 最小的文本
            pairs = []
            for t2 in ts:
                c2 = _contain_of(t2, [c for c in bs if not c.get("full")])
                if c2 is None:
                    continue
                tx0, ty0, tx1, ty1 = t2["box"]
                cx0, cy0, cx1, cy1 = c2["box"]
                pd = min(tx0 - cx0, cx1 - tx1, ty0 - cy0, cy1 - ty1) / (t2["fs"] or 20)
                pairs.append((pd, t2["text"][:18], (tx0, ty0, tx1, ty1), c2["box"]))
            for pd, txt, tb, cb in sorted(pairs)[:3]:
                if pd < pad_th:
                    print(f"{'':<22}L2 {pd:<6.2f} 「{txt}」 text={tb} box={cb}")

    if not args.quiet:
        print()
        print("=" * 110)
        print(f"L1 明细（低于 {l1_th} 的最挤相邻文本对，每图最多列 3 条）")
        print("=" * 110)
        cnt = 0
        for r in rows:
            for x in sorted(r[7], key=lambda v: v[0])[:3]:
                if x[0] < l1_th:
                    cnt += 1
                    print(f"  {r[0]:<20}{x[0]:<7.2f} 「{x[1]}」 → 「{x[2]}」")
        print(f"  小计 {cnt} 处")

        print()
        print("=" * 110)
        print("L3/L4 明细")
        print("=" * 110)
        cnt2 = 0
        for r in rows:
            for kind, tx in (r[5] or []) + [("贴底", y) for y in (r[6] or [])]:
                cnt2 += 1
                print(f"  {r[0]:<20}{kind:<6}{tx}")
        if cnt2 == 0:
            print("  无")
        print(f"  小计 {cnt2} 处")

    tot_bad = sum(1 for r in rows if r[-1] != "ok")
    print()
    print(f"结论：{len(rows)} 张图，{tot_bad} 张不合格 "
          f"（L1 {n_l1} / L2 {n_l2} / L3 {n_l3} / L4 {n_l4}）")
    return 1 if tot_bad else 0


if __name__ == "__main__":
    sys.exit(main())
