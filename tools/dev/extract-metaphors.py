#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract-metaphors.py —— 从十篇连载微信版抽取「✅像 / ⚠️不像」素材库（F45 · ADR-0026）

为什么是脚本而不是手抄：
  P1 方案铁律「比喻不现编」——术语卡的比喻必须从文章里已跑通的 50 组提炼，
  保证站内两处讲同一概念不会打架。手抄必漏、必漂移，所以脚本抽、门闸验。

输出：tools/dev/series-metaphors.json
  [{station, slug, anchor, like, unlike, like_len, unlike_len}, ...]

用法：python3 tools/dev/extract-metaphors.py
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "慢读宝盒公众号")
OUT = os.path.join(ROOT, "tools", "dev", "series-metaphors.json")

SLUG = {
    "站1-现金湾": "01-cash-bay", "站1.5-钱到底是什么": "01x-what-is-money",
    "站2-银行堡-货币三大缺陷": "02-bank-fortress", "站3-双花峡-双花难题": "03-double-spend-gorge",
    "站4-账本海": "04-ledger-sea", "站5-哈希岭": "05-hash-ridge",
    "站6-共识峰": "06-consensus-peak", "站7-矿工谷": "07-miner-valley",
    "站8-私钥崖": "08-private-key-cliff", "站9-代码之巅": "09-code-summit",
}

# ⚠️ 教训：emoji「⚠️」= U+26A0 + U+FE0F 变体选择符，两个码位。单字符类 [⚠️] 只吃掉
# 第一个，剩下 FE0F 卡死后续匹配（2026-10-01 实锤）。所以先剥掉全部装饰前缀再匹配。
DECOR_RE = re.compile(r"^[^\u4e00-\u9fffA-Za-z0-9（(\"]+")
LIKE_RE = re.compile(r"^(?:像的地方|相同的地方|相似之处|相同之处|像)[：:]\s*(.+)$")
UNLIKE_RE = re.compile(r"^(?:不一样的地方|不同的地方|不像的地方|区别于|不一样之处)[：:]\s*(.+)$")


def norm(line):
    return DECOR_RE.sub("", line.strip().replace("*", ""))


def clean(s):
    return re.sub(r"\*+", "", s).strip()


def main():
    items = []
    for path in sorted(glob.glob(os.path.join(SRC, "站*", "02-文章", "*微信版.md"))):
        station = os.path.basename(os.path.dirname(os.path.dirname(path)))
        slug = SLUG.get(station, station)
        lines = open(path, encoding="utf-8").read().split("\n")
        i = 0
        while i < len(lines):
            lm = LIKE_RE.match(norm(lines[i]))
            if lm:
                like = clean(lm.group(1))
                unlike = ""
                # ⚠️不像 必须紧跟（允许隔一个空行），这就是「先搭桥后拆桥」的结构证据
                for j in (i + 1, i + 2):
                    if j < len(lines):
                        um = UNLIKE_RE.match(norm(lines[j]))
                        if um:
                            unlike = clean(um.group(1))
                            i = j
                            break
                        if lines[j].strip():
                            break
                items.append({
                    "station": station, "slug": slug,
                    "line": i + 1, "like": like, "unlike": unlike,
                    "like_len": len(like), "unlike_len": len(unlike),
                })
            i += 1

    paired = [x for x in items if x["unlike"]]
    longer = sum(1 for x in paired if x["unlike_len"] >= x["like_len"])
    print("=" * 64)
    print("extract-metaphors · 比喻素材库抽取（F45）")
    print("=" * 64)
    by_station = {}
    for x in items:
        by_station.setdefault(x["station"], [0, 0])
        by_station[x["station"]][0] += 1
        if x["unlike"]:
            by_station[x["station"]][1] += 1
    for st, (a, b) in by_station.items():
        print(f"  {st:<24} 像 {a:>2} 组 · 配对 {b:>2} 组")
    print("-" * 64)
    print(f"  合计 {len(items)} 组「像」，其中 {len(paired)} 组带「不像」配对")
    if paired:
        al = sum(x["like_len"] for x in paired) // len(paired)
        ul = sum(x["unlike_len"] for x in paired) // len(paired)
        print(f"  「像」平均 {al} 字 · 「不像」平均 {ul} 字 · 「不像」更长占 {longer * 100 // len(paired)}%")

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"generated_by": "tools/dev/extract-metaphors.py",
                   "rule": "比喻四条律（ADR-0026）：像→不像固定顺序；不像≥像",
                   "count": len(items), "paired": len(paired), "items": items},
                  f, ensure_ascii=False, indent=1)
    print(f"\n  ✅ 已写出 {os.path.relpath(OUT, ROOT)}（{len(items)} 组）")
    if len(items) < 40:
        print("  ⚠️ 抽取数明显低于预期 50 组，正则可能漏配，需人工核对")
        sys.exit(1)


if __name__ == "__main__":
    main()
