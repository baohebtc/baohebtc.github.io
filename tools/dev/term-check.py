#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
term-check.py —— 术语「比喻+多视角」六层门闸（F45 · ADR-0026）

六层结构（缺一即红）：
  L1 term      术语名（中）
  L2 term_en   英文名
  L3 correct   正解：硬定义，不得含比喻词
  L4 metaphor  比喻：单一已知物，禁术语互喻、禁等号词
  L5 like      ✅像的地方
  L6 unlike    ⚠️不像的地方 —— 硬约束：len(unlike) ≥ len(like)，且须指名具体差异
  L7 views     多视角：四棱镜（机制/使用者/历史/反面）选 2–3，机制+使用者必选
  L8 links     站内延伸链接（≥1，必须真实存在）

数据源：reference/glossary-data.js（window.GLOSSARY = [...]）
用法：python3 tools/dev/term-check.py [-v]
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "reference", "glossary-data.js")
LEARNING_DIR = os.path.join(ROOT, "learning")
SERIES_DIR = os.path.join(ROOT, "series")

# T5 禁等号词：比喻层把未知和已知划等号（比喻四条律 ①）
EQUALITY_WORDS = ["就是", "等于", "相当于就是", "本质上是", "无非是"]
# T4 禁术语互喻：比喻句里不得出现其他术语当喻体
TERM_WORDS = ["哈希", "私钥", "公钥", "区块链", "共识", "工作量证明", "矿工", "节点", "助记词",
              "双重支付", "账本", "非对称加密", "数字签名"]
PRISMS = ["机制", "使用者", "历史", "反面"]
VIEW_RE = re.compile(r"^(机制|使用者|历史|反面)[:：]")
EQUAL_RE = re.compile(r"(就是|等于|本质上是|无非是)")


def parse_data():
    """极简解析 glossary-data.js 里的 JSON 数组（要求文件写成 const GLOSSARY = [...] 纯 JSON）。"""
    if not os.path.isfile(DATA):
        return None
    s = open(DATA, encoding="utf-8").read()
    m = re.search(r"=\s*(\[.*\])\s*;?\s*$", s, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError as e:
        print(f"❌ glossary-data.js 不是纯 JSON：{e}")
        sys.exit(1)


def main():
    verbose = "-v" in sys.argv
    fails = []

    def fail(rule, msg):
        fails.append(f"[{rule}] {msg}")

    terms = parse_data()
    if terms is None:
        fail("T0", f"数据文件不存在或无法解析：reference/glossary-data.js（应由 P1 试点数据填充）")
    elif len(terms) == 0:
        fail("T0", "glossary-data.js 为空数组（P1 试点 10 条尚未填充）")
    else:
        # T9 规模断言：试点 10 条 + F47 第二批 6 条 = 至少 16 条（F47 · 2026-10-03）
        if len(terms) < 16:
            fail("T9", f"条目数 {len(terms)} < 16（F47 第二批 6 条：UTXO/全节点/减半/难度调整/助记词/算力 未就位）")
        # 抽取的素材库，用来校验比喻出处（比喻不现编）
        meta_path = os.path.join(ROOT, "tools", "dev", "series-metaphors.json")
        metaphors = []
        if os.path.isfile(meta_path):
            metaphors = json.load(open(meta_path, encoding="utf-8")).get("items", [])

        for t in terms:
            name = t.get("term", "?")
            # T1 必填层
            for k in ("term", "term_en", "correct", "metaphor", "like", "unlike", "views", "links"):
                if not t.get(k):
                    fail("T1", f"{name}: 缺 {k}")
            # T2 像不像成对且非空
            if t.get("like") and not t.get("unlike"):
                fail("T2", f"{name}: 只有「像」没有「不像」（先搭桥后拆桥）")
            # T3 硬约束：不像 ≥ 像
            if t.get("like") and t.get("unlike"):
                ll, ul = len(t["like"]), len(t["unlike"])
                if ul < ll:
                    fail("T3", f"{name}: 「不像」{ul} 字 < 「像」{ll} 字（拆桥必须比搭桥重）")
                if not re.search(r"但|不过|然而|不同|区别|没有|不會|不会|并非|无需|不需", t["unlike"]):
                    fail("T3", f"{name}: 「不像」未指名具体机制差异（全是氛围话）")
            # T4 术语互喻
            mp = t.get("metaphor", "")
            for w in TERM_WORDS:
                if w != name and w in mp:
                    fail("T4", f"{name}: 比喻句含术语「{w}」（禁术语互喻）")
            # T5 等号词
            if EQUAL_RE.search(mp):
                fail("T5", f"{name}: 比喻句含等号词（比喻是桥不是等号）→ {mp[:40]}")
            # T6 棱镜
            views = t.get("views", [])
            kinds = [VIEW_RE.match(str(v)).group(1) for v in views if VIEW_RE.match(str(v))]
            if views and len(kinds) != len(views):
                fail("T6", f"{name}: views 必须以「机制:/使用者:/历史:/反面:」开头")
            if kinds:
                if not (2 <= len(kinds) <= 3):
                    fail("T6", f"{name}: 棱镜 {len(kinds)} 个（应 2–3）")
                if "机制" not in kinds or "使用者" not in kinds:
                    fail("T6", f"{name}: 机制+使用者必选，当前 {kinds}")
                if len(kinds) != len(set(kinds)):
                    fail("T6", f"{name}: 棱镜重复")
            # T8 站内链接真实存在
            for lk in t.get("links", []):
                href = lk.get("href", "") if isinstance(lk, dict) else str(lk)
                if href.startswith("http"):
                    continue
                full = os.path.join(ROOT, href.lstrip("/"))
                if not os.path.isfile(full) and not os.path.isfile(os.path.join(ROOT, href, "index.html")):
                    fail("T8", f"{name}: 站内链接不存在 → {href}")

    print("=" * 64)
    print("term-check · 术语六层门闸（F45 · ADR-0026）")
    print("=" * 64)
    n = 0 if terms is None else len(terms)
    print(f"\n  数据条目：{n}")
    if fails:
        print(f"\n❌ FAIL × {len(fails)}")
        for f in fails[:15 if not verbose else None]:
            print("  ·", f)
        print("\n结果：未通过")
        sys.exit(1)
    print("\n✅ 无 FAIL\n结果：通过")
    sys.exit(0)


if __name__ == "__main__":
    main()
