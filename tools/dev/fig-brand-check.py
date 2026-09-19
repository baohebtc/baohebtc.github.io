#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fig-brand-check.py — 公众号正文配图「品牌一致性门闸」（ADR-0008）
================================================================
检查每张配图是否遵守《慢读宝盒·配图视觉规范 v1.0》。
设计原则：只检查"可程序化客观量化"的项，不检查需要人眼的项（构图美感等）。

检查项（MoSCoW）：
  F1 画布规格      MUST    宽高必须在白名单内（CONFIG.ALLOWED_SIZES）
  F2 底色          MUST    四角众数必须命中品牌底色白名单（容差 Δ）
  F3 橙占比        MUST    品牌橙像素占比 ≤ MAX_ORANGE_PCT（防"刺眼/廉价"）
  F4 顶部标题条    SHOULD  上缘 66px 带内主色接近标题条色（品牌元素在位）
  F5 底部合规条    SHOULD  下缘 56px 带内主色接近合规条色
  F6 文件名规范    SHOULD  NN-slug.png（两位序号 + 短横线 + 英文 slug）
  F7 亮度一致性    MUST    同系列明暗必须与 CONFIG.THEME 一致（dark/light）

用法：
  python3 tools/dev/fig-brand-check.py                  # 检查全部站
  python3 tools/dev/fig-brand-check.py --theme dark     # 指定期望主题
  python3 tools/dev/fig-brand-check.py --station 4      # 只查某站
  python3 tools/dev/fig-brand-check.py --json           # 机器可读输出
退出码：0 = 全绿（仅 WARN 允许）；1 = 有 FAIL
"""
from __future__ import annotations
import argparse, glob, json, os, re, sys
from collections import Counter

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("需要 PIL + numpy：请用 venv python 运行", file=sys.stderr)
    sys.exit(2)

BASE = "/Users/mac/Desktop/宝盒知识库/比特币学习地图/慢读宝盒公众号"

# ---------------- 规范配置（改这里 = 改规范） ----------------
CONFIG = {
    # F1 画布白名单（v1.0 收敛为 3 种主规格）
    "ALLOWED_SIZES": {(1280, 720), (1280, 960), (1280, 1280)},
    # F2 品牌底色白名单（深色主轨 + 浅色副轨，容差 = 每通道 ±24）
    "ALLOWED_BG": {
        "dark":  [(13, 13, 13), (26, 26, 26), (17, 15, 11)],
        "light": [(251, 247, 240), (245, 237, 216)],
    },
    "BG_TOL": 26,
    # F3 品牌橙占比上限（%）
    "MAX_ORANGE_PCT": 12.0,
    # F4/F5 品牌元素带
    "TOPBAR_H": 66, "TOPBAR_TOL": 30,
    "FOOTBAR_H": 56, "FOOTBAR_TOL": 30,
    # F7 期望主题（None = 不检查明暗，只查是否在任一白名单）
    "THEME": None,
    # 语义豁免：这些是"系列固定图元"，另有专属规格，跳过 F1/F2/F3 检测
    #   寻宝路线 = 回扣图 4:3 1200×900（ADR-0004）
    #   learning-map = 学习地图全图（跨站共用叙事图）
    "EXEMPT_PATTERNS": [r"寻宝路线", r"bitcoin-learning-map"],
    # 豁免文件允许的专属规格
    "EXEMPT_SIZES": {(1200, 900), (900, 1350)},
}

ORANGE = (247, 147, 26)


def _q(c, n=16):
    return tuple(min(255, int(v) // n * n) for v in c[:3])


def _near(c, ref, tol):
    return all(abs(int(c[i]) - int(ref[i])) <= tol for i in range(3))


def analyze(path):
    """返回单张图的客观量化画像 + 逐项判定。"""
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(int)
    h, w, _ = a.shape
    r, g, b = a[..., 0], a[..., 1], a[..., 2]

    # 底色 = 四角众数
    corners = [_q(a[y, x]) for y, x in ((6, 6), (h - 7, 6), (6, w - 7), (h - 7, w - 7))]
    bg = Counter(corners).most_common(1)[0][0]

    # 亮度（整体）
    lum = float(0.299 * r.mean() + 0.587 * g.mean() + 0.114 * b.mean())

    # 品牌橙占比
    orange_pct = float(((r > 200) & (g > 100) & (g < 190) & (b < 90)).mean() * 100)

    # 顶/底带主色（用于品牌元素存在性）
    def band_color(y0, y1):
        band = a[y0:y1, :, :].reshape(-1, 3)
        return Counter(_q(c) for c in band[::7]).most_common(1)[0][0]

    topbar = band_color(0, min(CONFIG["TOPBAR_H"], h))
    footbar = band_color(max(0, h - CONFIG["FOOTBAR_H"]), h)

    checks = {}
    name = os.path.basename(path)
    exempt = any(re.search(p, name) for p in CONFIG["EXEMPT_PATTERNS"])

    # F1 规格
    if exempt:
        checks["F1 画布规格"] = ("PASS" if (w, h) in CONFIG["EXEMPT_SIZES"] else "FAIL",
                              f"{w}×{h}（豁免）")
    else:
        checks["F1 画布规格"] = ("PASS" if (w, h) in CONFIG["ALLOWED_SIZES"] else "FAIL",
                              f"{w}×{h}")

    # F2 底色（在任一白名单内即通过）
    hit = None
    for theme, refs in CONFIG["ALLOWED_BG"].items():
        for ref in refs:
            if _near(bg, ref, CONFIG["BG_TOL"]):
                hit = f"{theme}:{ref}"
                break
        if hit:
            break
    checks["F2 底色"] = ("PASS" if (hit or exempt) else "FAIL",
                        f"#{bg[0]:02X}{bg[1]:02X}{bg[2]:02X}" + (f"→{hit}" if hit else ("（豁免）" if exempt else "")))

    # F3 橙占比
    checks["F3 橙占比"] = ("PASS" if (orange_pct <= CONFIG["MAX_ORANGE_PCT"] or exempt) else "FAIL",
                          f"{orange_pct:.1f}% ≤{CONFIG['MAX_ORANGE_PCT']}%")

    # F4 顶部标题条（仅深色系要求；浅色系跳过）
    is_dark = lum < 140
    if is_dark:
        ok = _near(topbar, (20, 20, 20), CONFIG["TOPBAR_TOL"]) or \
             _near(topbar, CONFIG["ALLOWED_BG"]["dark"][0], CONFIG["TOPBAR_TOL"])
        checks["F4 标题条"] = ("PASS" if ok else "SHOULD",
                              f"#{topbar[0]:02X}{topbar[1]:02X}{topbar[2]:02X}")
        okf = _near(footbar, (20, 20, 20), CONFIG["FOOTBAR_TOL"]) or \
              _near(footbar, CONFIG["ALLOWED_BG"]["dark"][0], CONFIG["FOOTBAR_TOL"])
        checks["F5 合规条"] = ("PASS" if okf else "SHOULD",
                              f"#{footbar[0]:02X}{footbar[1]:02X}{footbar[2]:02X}")
    else:
        checks["F4 标题条"] = ("N/A", "浅色系")
        checks["F5 合规条"] = ("N/A", "浅色系")

    # F6 文件名
    if exempt:
        checks["F6 文件名"] = ("N/A", "豁免")
    else:
        checks["F6 文件名"] = ("PASS" if re.fullmatch(r"\d{2}-[a-z0-9\-]+\.png", name)
                              else "SHOULD", name)

    # F7 主题一致性
    if CONFIG["THEME"]:
        want_dark = CONFIG["THEME"] == "dark"
        checks["F7 明暗"] = ("PASS" if (is_dark == want_dark) else "FAIL",
                            "深" if is_dark else "浅")

    return {"file": path, "size": (w, h), "bg": bg, "lum": round(lum, 1),
            "orange_pct": round(orange_pct, 2), "checks": checks}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--theme", choices=["dark", "light"], default=None)
    ap.add_argument("--station", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--root", default=BASE)
    args = ap.parse_args()
    CONFIG["THEME"] = args.theme

    pat = f"{args.root}/站{args.station}*/03-配图/*.png" if args.station \
        else f"{args.root}/站*/03-配图/*.png"
    files = sorted(f for f in glob.glob(pat) if "_原图备份" not in f)

    results, n_fail, n_should = [], 0, 0
    for f in files:
        res = analyze(f)
        results.append(res)
        n_fail += sum(1 for s, _ in res["checks"].values() if s == "FAIL")
        n_should += sum(1 for s, _ in res["checks"].values() if s == "SHOULD")

    if args.json:
        print(json.dumps({"results": results, "fail": n_fail, "should": n_should},
                         ensure_ascii=False, indent=2))
        return 1 if n_fail else 0

    print("=" * 118)
    print("慢读宝盒 · 配图品牌一致性门闸 (ADR-0008)   "
          f"检查 {len(files)} 张 | FAIL={n_fail} SHOULD={n_should}")
    print("=" * 118)
    hdr = f'{"文件":44s} {"规格":>10s} {"底色":>9s} {"橙%":>6s}  F1 F2 F3 F4 F5 F6 F7'
    print(hdr)
    print("-" * 118)
    for r in results:
        tag = "/".join(r["file"].split("/")[-3:-1])
        marks = []
        for k in ["F1 画布规格", "F2 底色", "F3 橙占比", "F4 标题条",
                  "F5 合规条", "F6 文件名", "F7 明暗"]:
            if k in r["checks"]:
                s = r["checks"][k][0]
                marks.append({"PASS": " ✅", "FAIL": " ❌", "SHOULD": " ⚠️", "N/A": " ·"}[s])
            else:
                marks.append("  ")
        print(f'{tag+"/"+os.path.basename(r["file"]):44s} '
              f'{r["size"][0]}×{r["size"][1]:<6} '
              f'#{r["bg"][0]:02X}{r["bg"][1]:02X}{r["bg"][2]:02X} '
              f'{r["orange_pct"]:>5.1f} {" ".join(marks)}')
    print("-" * 118)
    # 汇总失败原因
    reasons = Counter()
    for r in results:
        for k, (s, _) in r["checks"].items():
            if s == "FAIL":
                reasons[k] += 1
    if reasons:
        print("红灯汇总：", " | ".join(f"{k}×{n}" for k, n in reasons.most_common()))
    print(f"结论：{'🔴 有 FAIL，不符合规范' if n_fail else ('🟡 仅 SHOULD 警告' if n_should else '🟢 全绿')}")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
