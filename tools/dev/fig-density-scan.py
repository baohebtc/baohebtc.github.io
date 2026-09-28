# -*- coding: utf-8 -*-
"""
fig-density-scan.py — 配图「可读性困难指数」筛查（ADR-0018）
=============================================================
为什么需要它（ADR-0017 的教训）：
  上一版用「正文 <34px 即不合格」的**单一绝对门槛**扫全系列，结果 65/65 张全部判红，
  被迫走上「全量拆图重做」路线 —— 用户明确否决：破坏了图的构图美感，收益却不成比例。

  难读是**组合成因**：字小 × 行距挤 × 信息量大 × 挤容器边。单一维度必然误判：
    · 一个 19px 的大标题孤零零放在画布中央 → 不难读，却被门槛判红
    · 一个 24px 的字挤在 20 行密排里 → 很难读，却全绿放行

  所以改为**多维加权困难指数 RDI**，排序取 Top-N，只修真正该修的那几张。

RDI 构成（0–100，越高越难读）：
  P_fs    35%  字体过小：取正文层最小三个字号均值 → 手机等效 pt = fs × 0.293
               低于 9 CSS px（近似微信图注下限）开始计惩罚
  P_tight 30%  行距挤：容器内相邻行"行距比 < 0.35"的行对占比 ← 用户主诉「字间距密集」
  P_ink   25%  信息量过载：文字 bbox 面积 / 内容区面积，超过 12% 开始计惩罚
  P_pad   10%  挤容器边：文本到容器最小边距 / fs，低于 0.45 计亏空

用法：
    python3 tools/dev/fig-density-scan.py              # 全系列，按 RDI 降序
    python3 tools/dev/fig-density-scan.py --station 8  # 单站
    python3 tools/dev/fig-density-scan.py --top 15     # 只看前 15
    python3 tools/dev/fig-density-scan.py --json       # 机器可读输出
"""
from __future__ import annotations
import argparse, importlib.util, json, pathlib, statistics, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "dev"))

# 复用 fig-layout-check 的绘制层 hook，避免重复实现
_spec = importlib.util.spec_from_file_location("flc", ROOT / "tools" / "dev" / "fig-layout-check.py")
flc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(flc)

PHONE = 375 / 1280          # 1280px 图 → 微信正文显示 375 CSS px
TOPBAR_H, FOOTBAR_H = flc.TOPBAR_H, flc.FOOTBAR_H
READABLE_PT = 9.0           # 手机上「基本可辨识」下限（微信正文 15 / 图注 13）
INK_BUDGET = 0.12           # 文字占内容区面积的信息密度预算
PAD_TARGET = 0.45           # 文本到容器边距 / 字号
L1_TARGET = 0.35            # 行距比


def collect(args):
    jobs = flc._collect()
    if args.station:
        jobs = [j for j in jobs if j[0] == args.station]
        if not jobs:
            print(f"未知站号：{args.station}")
            sys.exit(1)
    figs = [(fg, fn) for _st, g in jobs for fg, fn in g]
    flc._run(figs)
    return figs


def analyse(fg):
    ts = [t for t in flc.REC["texts"] if t["fig"] == fg]
    bs = [b for b in flc.REC["boxes"] if b["fig"] == fg]
    if not ts:
        return None
    fulls = [b for b in bs if b.get("full")]
    if fulls:
        W = max(max(b["box"][2] for b in fulls), 1280)
        H = max(max(b["box"][3] for b in fulls), 720)
    else:
        W = max([b["box"][2] for b in bs] + [1280])
        H = 960 if any(b["box"][3] > 780 for b in bs) else 720

    def is_chrome(t):
        cy = (t["box"][1] + t["box"][3]) / 2
        return cy <= TOPBAR_H + 2 or cy >= H - FOOTBAR_H - 2

    ts = [t for t in ts if not is_chrome(t)]
    if not ts:
        return None

    area_content = max(1, (W - 16) * (H - TOPBAR_H - FOOTBAR_H - 16))
    ink = sum((t["box"][2] - t["box"][0]) * (t["box"][3] - t["box"][1]) for t in ts)
    ink_ratio = ink / area_content

    # ── P_fs：主诉"看不清"，取最小三档字号均值（最小单个值易被特例带偏）
    sizes = sorted(t["fs"] for t in ts)
    fs_lo = statistics.mean(sizes[:3]) if len(sizes) >= 3 else sizes[0]
    pt = fs_lo * PHONE
    p_fs = max(0.0, (READABLE_PT - pt) / READABLE_PT)

    # ── P_tight：主诉"字间距密集"，行距比 < 0.35 的行对占比
    l1s, pads = [], []
    for c in [c for c in bs if not c.get("full")]:
        inn = sorted([t for t in ts if flc._inside(t, c)], key=lambda t: t["box"][1])
        for i in range(len(inn) - 1):
            a, b = inn[i], inn[i + 1]
            if flc._h_overlap(a["box"], b["box"]) < 0.5:
                continue
            gap = b["box"][1] - a["box"][3]
            hgt = min(a["box"][3] - a["box"][1], b["box"][3] - b["box"][1])
            if hgt < 6 or gap < 0:
                continue
            l1s.append(gap / hgt)
    for t in ts:
        c = flc._contain_of(t, bs)
        if c is not None:
            cx0, cy0, cx1, cy1 = c["box"]
            tx0, ty0, tx1, ty1 = t["box"]
            pads.append(min(tx0 - cx0, cx1 - tx1, ty0 - cy0, cy1 - ty1) / t["fs"])

    n_tight = sum(1 for x in l1s if x < L1_TARGET)
    p_tight = (n_tight / len(l1s)) if l1s else 0.0
    p_ink = max(0.0, (ink_ratio - INK_BUDGET) / INK_BUDGET)
    p_pad = max(0.0, (PAD_TARGET - min(pads)) / PAD_TARGET) if pads else 0.0

    rdi = 100 * (0.35 * p_fs + 0.30 * p_tight + 0.25 * p_ink + 0.10 * p_pad)

    # ── 修复策略（按主控病因定，保证「最小干预 + 保留构图」）
    causes = []
    if p_tight >= 0.25:
        causes.append("行距挤")
    if p_ink >= 0.25:
        causes.append("信息过载")
    if p_fs >= 0.25:
        causes.append("字小")
    if p_pad >= 0.25:
        causes.append("挤边")
    if "信息过载" in causes or "行距挤" in causes:
        strategy = "精简文案为主 + 温和提字（保结构）"
    elif causes:
        strategy = "温和提字（保结构）"
    else:
        strategy = "无需改动"

    # ── 定级：小字占比 × 最小字号（真正决定「该修哪几张」的判据）
    #    一张图若有 30 个字只有 2 个小 → 无关痛痒；若 32 个字 27 个小 → 整图难读
    fs_min = min(t["fs"] for t in ts)
    n_small = sum(1 for t in ts if t["fs"] < 22)
    small_ratio = n_small / len(ts)
    if fs_min <= 19 and small_ratio >= 0.40:
        tier, action = "P1", "必修：整图字普遍偏小"
    elif fs_min <= 19:
        tier, action = "P2", "建议：仅个别小注/标签偏小"
    elif fs_min <= 21 and small_ratio >= 0.50:
        tier, action = "P2", "建议：接近达标但小字占多数"
    else:
        tier, action = "P3", "无需改动"

    return dict(fig=fg, rdi=rdi, fs_lo=fs_lo, pt=pt, n=len(ts), rows=len(l1s),
                n_tight=n_tight, ink=ink_ratio, pad=min(pads) if pads else None,
                causes=causes, strategy=strategy, tier=tier, action=action,
                fs_min=fs_min, n_small=n_small, small_ratio=small_ratio)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--station", default=None)
    ap.add_argument("--top", type=int, default=0)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    figs = collect(args)
    rows = [r for r in (analyse(fg) for fg, _ in figs) if r]
    rows.sort(key=lambda r: -r["rdi"])

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return 0

    print("=" * 118)
    print(f"fig-density-scan · 可读性困难指数 RDI（加权：字小35% 行距挤30% 信息过载25% 挤边10%）")
    print(f"手机换算 {PHONE:.3f}｜可读下限 {READABLE_PT} CSS px｜信息密度预算 {INK_BUDGET:.0%}")
    print("=" * 118)
    print(f"{'级别':<6}{'fig':<20}{'最小px':>7}{'手机pt':>8}{'小字/总数':>11}{'占比':>7}{'密度':>7}{'挤行':>5}  处置")
    print("-" * 118)
    for tier, emoji in (("P1", "🔴"), ("P2", "🟠"), ("P3", "🟢")):
        grp = [r for r in rows if r["tier"] == tier]
        if not grp:
            continue
        print(f"{emoji}{tier} 必修组({len(grp)} 张)" if tier == "P1" else
              f"{emoji}{tier} 建议组({len(grp)} 张)" if tier == "P2" else
              f"{emoji}{tier} 无需改动({len(grp)} 张)")
        for r in sorted(grp, key=lambda x: (x["fs_min"], -x["small_ratio"])):
            cnt = "%d/%d" % (r['n_small'], r['n'])
            print(f"  {'':<4}{r['fig']:<20}{r['fs_min']:>7}{r['pt']:>8.1f}"
                  f"{cnt:>11}{r['small_ratio']*100:>6.0f}%"
                  f"{r['ink']*100:>6.1f}%{r['n_tight']:>5}  {r['action']}")
        print("-" * 118)
    n1 = sum(1 for r in rows if r["tier"] == "P1")
    n2 = sum(1 for r in rows if r["tier"] == "P2")
    n3 = sum(1 for r in rows if r["tier"] == "P3")
    print(f"共 {len(rows)} 张 → 🔴P1 必修 {n1} ｜ 🟠P2 建议 {n2} ｜ 🟢P3 不动 {n3}")
    print(f"小字总数 {sum(r['n_small'] for r in rows)} 处（<22px，手机 <6.4pt）")
    print("\n修复原则（ADR-0018）：保留原构图与视觉层次，优先「精简次要文案」+「温和提字」，")
    print("                    禁止为达标而重构版面；目标 = 最小字 ≥22px（手机 6.4pt）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
