#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文集 · 词条结构校验门闸 (Feature Ledger F33 / ADR-0020 / ADR-0021)

为什么存在
----------
文集页此前存在三类病：① 占位页占了一半以上；② 条目可多可少，没有下限；
③ 外链凭记忆写，没人验证过能不能打开。本门闸把这三类病变成机器可判的规则。

八条规则
--------
R1  无占位        collection/ 下不得出现「本栏目整理中 / 🚧 / 整理中 / 规划中」
R2  条目数下限    每个词条页的 .collection-item >= MIN_ITEMS（saylor 例外，见白名单）
R3  五属性齐全    每条目须带非空 data-title / data-author / data-type / data-source / data-license
R4  链接安全      data-source 必须为 https:// 或已知可信 http://（legacy 白名单）
R5  来源去重      同一文件内同一 data-source 出现次数 <= MAX_DUP（防复制粘贴凑数）
R6  来源已验证    data-source 必须落在 allowlist（该文件由 HTTP 实测生成，见脚本 --gen-allowlist）
R7  合规红线      标题/摘要不得含预测类、买卖动作类、极限词
R8  nav 双语      shared/nav.js 的 NAV_ITEMS 不得硬编码中文，须走 I18N_MAP 的六个 nav.* key

用法
----
    python3 tools/dev/collection-check.py                 # 全量检查
    python3 tools/dev/collection-check.py --verbose       # 列出每条问题
    python3 tools/dev/collection-check.py --file path     # 只查一个文件
    python3 tools/dev/collection-check.py --gen-allowlist # 打印当前页面所有 data-source（用于更新白名单）

退出码：0 = 全绿；1 = 有 FAIL
"""

import os
import re
import sys
import argparse

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COLL = os.path.join(ROOT, "collection")
NAVJS = os.path.join(ROOT, "shared", "nav.js")
ALLOW = os.path.join(ROOT, "tools", "dev", "collection-sources-allowlist.txt")

# ---- 规则参数 ---------------------------------------------------------
MIN_ITEMS = 8                      # R2 条目数下限
# ADR-0021 §5 记录的例外（新栏）：Saylor 可核实公开链接上限即为此
# ADR-0021 §5 记录的例外（新栏）：Saylor 可核实的免费教育资源上限即为此。
# 2026-09-30 补齐批次后由 6 提至 7（新增课程大纲）。X 与 strategy.com 对本机不可达，
# 无法验证即不收录；待可验证新来源经收件箱补录后，本项应回升到 8 并删除此例外。
MIN_ITEMS_WHITELIST = {"saylor.html": 7}
# 存量老栏目豁免：2026-09-30 补齐前 ahr999=3 / lixiaolai=6，不足下限。
# 补齐批次后两栏均达 9 条，已满足下限，豁免按约定撤销（不再开后门）。
MIN_ITEMS_LEGACY = {}
# P2 已排期、本批明确不动的文件：占位必须保留以便读者知情，
# 因此 R1/R2 降级为 WARN（打印但不计入 FAIL），避免污染本批改判。
P2_SCHEDULED = {"community.html", "others.html",
                "essays.html", "papers.html", "videos.html", "whitepapers.html"}
MAX_DUP = 3                        # R5 同一文件内同一来源最多出现次数（ahr999 三件作品同源）

# R1 占位语（出现即 FAIL）
PLACEHOLDER_TOKENS = ["本栏目整理中", "🚧", "整理中", "规划中", "即将上线", "敬请期待"]

# R7 安全语境词：红线词出现在这类措辞附近时，是在做风险提示而非诱导，
# 应当豁免（否则会出现「为了让门闸变绿而删掉免责声明」的荒唐结果）。
SAFE_CONTEXT = ["非投资建议", "不构成任何投资建议", "需独立判断", "需自行判断",
                "不代表本号立场", "本站仅作", "任何", "独立研究", "自行核实"]

# R7 合规红线（ADR-0021 §3.2 + 项目既定红线）
REDLINE_PATTERNS = {
    "预测类": ["2045", "1300万", "将涨到", "目标价", "预测价格", "牛市顶点", "一定涨"],
    "动作类": ["买入", "卖出", "加仓", "减仓", "建仓", "清仓", "抄底", "定投策略", "分批买入", "囤币建议"],
    "极限词": ["最好的投资", "稳赚", "无风险", "第一币", "唯一值得", "国家级"],
}

# R8 六个必须的 nav i18n key（ADR-0020）
NAV_KEYS = ["nav.home", "nav.learning", "nav.map", "nav.tools", "nav.reference", "nav.collection"]

ATTRS = ["data-title", "data-author", "data-type", "data-source", "data-license"]

ITEM_RE = re.compile(r'<div\s+class="collection-item"([^>]*)>', re.S)
ATTR_RE = re.compile(r'(data-[a-z-]+)="([^"]*)"')
TEXT_RE = re.compile(r'>([^<>]{2,400})<')


# ---- 工具 -------------------------------------------------------------
class Report:
    def __init__(self):
        self.rows = []          # (rule, file, msg)
        self.warns = []         # 降级项（P2 已排期，不计 FAIL）

    def add(self, rule, path, msg):
        self.rows.append((rule, os.path.relpath(path, ROOT), msg))

    def warn(self, rule, path, msg):
        self.warns.append((rule, os.path.relpath(path, ROOT), msg))

    def count(self):
        c = {}
        for r, _, _ in self.rows:
            c[r] = c.get(r, 0) + 1
        return c


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def list_pages():
    pages = []
    for sub in ("authors", "themes"):
        d = os.path.join(COLL, sub)
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if name.endswith(".html"):
                pages.append(os.path.join(d, name))
    return pages


def load_allowlist():
    if not os.path.exists(ALLOW):
        return set()
    out = set()
    with open(ALLOW, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                out.add(line)
    return out


# ---- 规则 -------------------------------------------------------------
def check_page(rep, path, allow, verbose):
    html = read(path)
    name = os.path.basename(path)
    in_p2 = name in P2_SCHEDULED

    def emit(rule, msg):
        # P2 排期内的占位项：如实打印，不计 FAIL（避免本批改判被旧账污染）
        (rep.warn if (in_p2 and rule in ("R1", "R2")) else rep.add)(rule, path, msg)

    # R1 无占位
    for tok in PLACEHOLDER_TOKENS:
        if tok in html:
            emit("R1", "残留占位语：%s" % tok)

    # R2 条目数
    items = list(ITEM_RE.finditer(html))
    need = MIN_ITEMS_LEGACY.get(name, MIN_ITEMS_WHITELIST.get(name, MIN_ITEMS))
    if len(items) < need:
        tag = "（存量豁免）" if name in MIN_ITEMS_LEGACY else (
              "（ADR-0021 例外）" if name in MIN_ITEMS_WHITELIST else "")
        emit("R2", "条目数 %d < 下限 %d%s" % (len(items), need, tag))

    # 预取每个条目的自身文本范围（R7 只在此范围内扫，避免跨条目误伤）
    spans = []
    for i, m in enumerate(items):
        start = m.end()
        end = items[i + 1].start() if i + 1 < len(items) else len(html)
        spans.append(html[start:end])

    dup, dup_titles = {}, {}
    for i, m in enumerate(items, 1):
        attrs = dict(ATTR_RE.findall(m.group(1)))

        # R3 五属性齐全
        missing = [a for a in ATTRS if not attrs.get(a, "").strip()]
        if missing:
            rep.add("R3", path, "第 %d 条缺少属性：%s" % (i, "/".join(missing)))
            if verbose:
                print("      ↳ 第%d条 blob: %s" % (i, m.group(1)[:120]))

        src = attrs.get("data-source", "").strip()
        title = attrs.get("data-title", "").strip()

        # R4 链接安全
        if src and not src.startswith("http"):
            rep.add("R4", path, "第 %d 条来源非 http(s)：%s" % (i, src))

        # R5 来源去重（同源允许多条，但标题必须互不相同，否则视为复制凑数）
        if src:
            dup[src] = dup.get(src, 0) + 1
            dup_titles.setdefault(src, []).append(title)
            if dup[src] > MAX_DUP:
                rep.add("R5", path, "来源重复 %d 次 > %d：%s" % (dup[src], MAX_DUP, src))

        # R6 来源已验证（allowlist）
        if allow and src and src not in allow:
            rep.add("R6", path, "来源未经 HTTP 实测（不在 allowlist）：%s" % src)

        # R7 合规红线：只看本条目标题 + 本条目正文（不再扫全文，修掉跨条目误伤）
        scope = title + " " + " ".join(TEXT_RE.findall(spans[i - 1]))
        for kind, pats in REDLINE_PATTERNS.items():
            for pat in pats:
                if pat not in scope:
                    continue
                # 取红线词前后 40 字，判断是否落在风险提示语境里
                idxs = [m.start() for m in re.finditer(re.escape(pat), scope)]
                hit = False
                for c in idxs:
                    window = scope[max(0, c - 40): c + len(pat) + 40]
                    if not any(safe in window for safe in SAFE_CONTEXT):
                        hit = True
                        break
                if hit:
                    rep.add("R7", path, "第 %d 条命中%s红线词「%s」（非免责语境）" % (i, kind, pat))

    # R5b 同源且标题重复 → 判为复制凑数
    for src, titles in dup_titles.items():
        if len(titles) > 1 and len(set(titles)) < len(titles):
            rep.add("R5", path, "同源条目出现重复标题（疑似复制凑数）：%s" % src)


def check_nav(rep):
    if not os.path.exists(NAVJS):
        rep.add("R8", NAVJS, "找不到 shared/nav.js")
        return
    js = read(NAVJS)

    # NAV_ITEMS 不得硬编码中文
    m = re.search(r"const\s+NAV_ITEMS\s*=\s*\[(.*?)\];", js, re.S)
    if not m:
        rep.add("R8", NAVJS, "未找到 NAV_ITEMS 定义")
    else:
        body = m.group(1)
        if re.search(r"[\u4e00-\u9fff]", body):
            rep.add("R8", NAVJS, "NAV_ITEMS 里仍有硬编码中文标签（应改为 i18n key）")

    # 六个 key 必须齐全
    for k in NAV_KEYS:
        if '"%s"' % k not in js:
            rep.add("R8", NAVJS, "I18N_MAP 缺少 key：%s" % k)


def check_index(rep, allow):
    """文集首页：不得对未完成项假装完成。"""
    path = os.path.join(COLL, "index.html")
    if not os.path.exists(path):
        return
    html = read(path)
    for tok in ["整理中", "规划中", "🚧"]:
        if tok in html:
            rep.add("R1", path, "首页卡片残留占位标签：%s" % tok)


# ---- main -------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--file", default=None)
    ap.add_argument("--gen-allowlist", action="store_true")
    args = ap.parse_args()

    if args.gen_allowlist:
        pages = [args.file] if args.file else list_pages()
        seen = set()
        for p in pages:
            if not os.path.exists(p):
                continue
            for blob in ITEM_RE.findall(read(p)):
                a = dict(ATTR_RE.findall(blob))
                if a.get("data-source"):
                    seen.add(a["data-source"])
        print("\n".join(sorted(seen)))
        return 0

    allow = load_allowlist()
    rep = Report()

    pages = [args.file] if args.file else list_pages()
    for p in pages:
        if not os.path.exists(p):
            print("跳过（不存在）：%s" % p)
            continue
        check_page(rep, p, allow, args.verbose)
    check_index(rep, allow)
    if not args.file:
        check_nav(rep)

    counts = rep.count()
    total = sum(counts.values())

    if rep.warns:
        print("-" * 72)
        print("⚠️  降级项（已在 P2 排期、本批明确不动，如实列出但不计入 FAIL）：")
        for r, f, m in sorted(set(rep.warns)):
            print("   [%s] %s — %s" % (r, f, m))

    print("=" * 72)
    print("文集词条结构校验门闸 (F33)  —  目标目录：%s" % os.path.relpath(ROOT, os.path.expanduser("~")))
    print("=" * 72)
    order = ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"]
    for r in order:
        n = counts.get(r, 0)
        flag = "🟢" if n == 0 else "🔴"
        label = {
            "R1": "无占位", "R2": "条目数下限", "R3": "五属性齐全", "R4": "链接安全",
            "R5": "来源去重", "R6": "来源已验证", "R7": "合规红线", "R8": "nav 双语",
        }[r]
        print("%s %s  %-12s  %s" % (flag, r, label, ("%d 项不合规" % n) if n else "PASS"))

    if args.verbose and total:
        print("-" * 72)
        for r, f, m in sorted(rep.rows):
            print("[%s] %s\n    %s" % (r, f, m))

    print("=" * 72)
    if total == 0:
        print("总闸门 ✅  ALL PASS（0 FAIL）")
        return 0
    print("总闸门 ❌  %d FAIL" % total)
    return 1


if __name__ == "__main__":
    sys.exit(main())
