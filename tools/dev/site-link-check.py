#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
site-link-check.py —— 全站外链与占位语门闸（F35）

起因（2026-09-30 用户反馈）：
  · 文集条目点击后原地跳走、没开新标签页 → 访客会离开本站
  · 六个 P2 栏目页仍是「🚧 整理中」空壳 → 违反「绝不再出现第三个整理中」
  · 61 页挂着「中 / EN」按钮，但只有 3 页有真实英文 → 累赘且误导

规则：
  L1 外链必须在新标签页打开（target="_blank"）
  L2 外链必须带 rel 且含 noopener（安全：防 tabnabbing）
  L3 全站正文不得出现占位语（🚧 / 整理中 / 敬请期待 / 规划中 / Coming soon）
  L4 站内链接不得误加 target="_blank"（站内应原地跳转，否则每点一次开一个标签）
  L5 不得残留外露的「中 / EN」语言切换按钮（已按用户拍板取消）
  L6 外链需在视觉上可辨识（带 data-external 或 ↗ 标识）
  L7 导航链接结构完整：禁止嵌套 <a>，且 .nav-link 必须有可见文字
     （2026-10-01 事故：批量插导航时把 <a> 插进了前一个 <a> 内部，56 页「文集」链接失效）

用法：
  python3 tools/dev/site-link-check.py            # 全站
  python3 tools/dev/site-link-check.py --warn     # 违规只警告不计 FAIL
"""
import os
import re
import sys
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SKIP_DIRS = {
    ".git", "node_modules", ".github", "archive", "out", "samples",
    "content-source", "tools/dev/node_modules", "__pycache__",
}

# 占位语（命中即 FAIL；这是用户明令禁止的「第三个整理中」）
PLACEHOLDER_TOKENS = [
    "🚧", "整理中", "敬请期待", "规划中", "即将上线", "建设中",
    "Coming soon", "coming soon", "TBD", "TODO",
]

A_TAG_RE = re.compile(r"<a\b[^>]*>", re.I)
HREF_RE = re.compile(r'href\s*=\s*["\']([^"\']+)["\']', re.I)
TARGET_RE = re.compile(r'target\s*=\s*["\']([^"\']+)["\']', re.I)
REL_RE = re.compile(r'rel\s*=\s*["\']([^"\']+)["\']', re.I)
SCRIPT_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.S | re.I)
TAG_RE = re.compile(r"<[^>]+>")
NAV_A_RE = re.compile(r"<a\\b[^>]*>", re.I)


def iter_pages():
    for p in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True):
        rel = os.path.relpath(p, ROOT)
        parts = rel.split(os.sep)
        if any(part in SKIP_DIRS for part in parts):
            continue
        yield rel, p


def is_external(href):
    return href.startswith("http://") or href.startswith("https://")


def body_text(html):
    """去掉 script/style 与标签后的正文，用于占位语与标识检测"""
    s = SCRIPT_RE.sub(" ", html)
    return TAG_RE.sub(" ", s)


def check():
    fails = []
    warns = []
    stats = {"pages": 0, "ext": 0, "int": 0}

    # L6 全局机制检查：外链角标由 shared/style.css 统一加，不要求逐条标属性
    css_path = os.path.join(ROOT, "shared", "style.css")
    try:
        css = open(css_path, encoding="utf-8", errors="ignore").read()
    except OSError:
        css = ""
    if 'a[target="_blank"]::after' not in css:
        fails.append("L6 外链无全局角标：shared/style.css 缺少 a[target=\"_blank\"]::after 规则")

    for rel, path in iter_pages():
        try:
            html = open(path, encoding="utf-8", errors="ignore").read()
        except OSError as e:
            warns.append(f"{rel}: 读取失败 {e}")
            continue
        stats["pages"] += 1

        # ---- L3 占位语（只看正文，不看属性）----
        text = body_text(html)
        for tok in PLACEHOLDER_TOKENS:
            if tok in text:
                idx = text.find(tok)
                snippet = re.sub(r"\s+", " ", text[max(0, idx - 40):idx + 40]).strip()
                fails.append(f"L3 占位语 {rel}: 命中「{tok}」…{snippet}…")

        # ---- L5 外露语言切换按钮 ----
        if 'class="lang-toggle"' in html or "class='lang-toggle'" in html:
            fails.append(f"L5 残留语言切换按钮 {rel}: 存在 .lang-toggle")

        # ---- L7 导航链接结构（禁嵌套 + 文字非空）----
        for nm in NAV_A_RE.finditer(html):
            tag = nm.group(0)
            if 'class="nav-link"' not in tag and "class='nav-link'" not in tag:
                continue
            # 找到本标签之后的正文，直到 </a>；中间若再出现 <a 即为嵌套
            start = nm.end()
            end = html.find("</a>", start)
            if end < 0:
                fails.append(f"L7 导航链接未闭合 {rel}: {tag[:70]}")
                continue
            inner = html[start:end]
            if "<a" in inner.lower():
                fails.append(
                    f"L7 导航链接嵌套 <a> {rel}: …{re.sub(r'\\s+',' ',inner)[:50]}… "
                    f"（会把相邻导航项的文字吞成纯文本）")
            visible = re.sub(r"<[^>]+>|\\s|[^\\w\\u4e00-\\u9fff]", "", inner)
            if not visible:
                fails.append(f"L7 导航链接文字为空 {rel}: {tag[:70]}")

        # ---- L1/L2/L4/L6 链接 ----
        for m in A_TAG_RE.finditer(html):
            tag = m.group(0)
            hm = HREF_RE.search(tag)
            if not hm:
                continue
            href = hm.group(1)
            if href.startswith("mailto:") or href.startswith("#") or href.startswith("javascript:"):
                continue

            tm = TARGET_RE.search(tag)
            rm = REL_RE.search(tag)
            target = tm.group(1) if tm else None
            rel_attr = rm.group(1) if rm else None

            if is_external(href):
                stats["ext"] += 1
                if target != "_blank":
                    fails.append(
                        f"L1 外链未开新标签 {rel}: {href[:80]} (target={target})")
                if not rel_attr or "noopener" not in rel_attr.lower():
                    fails.append(
                        f"L2 外链缺 noopener {rel}: {href[:80]} (rel={rel_attr})")
            else:
                stats["int"] += 1
                if target == "_blank":
                    fails.append(
                        f"L4 站内链误开新标签 {rel}: {href[:80]}")

    return fails, warns, stats


def main():
    warn_only = "--warn" in sys.argv
    fails, warns, stats = check()

    print("=" * 72)
    print(f"site-link-check · 扫描 {stats['pages']} 页 · "
          f"外链 {stats['ext']} · 站内链 {stats['int']}")
    print("=" * 72)

    if warns:
        print(f"\n⚠️  警告 {len(warns)} 条：")
        for w in warns[:25]:
            print("   " + w)
        if len(warns) > 25:
            print(f"   …还有 {len(warns) - 25} 条")

    if fails:
        # 按规则聚合
        by_rule = {}
        for f in fails:
            by_rule.setdefault(f.split()[0], []).append(f)
        print(f"\n🔴 FAIL {len(fails)} 条：")
        for rule in sorted(by_rule):
            items = by_rule[rule]
            print(f"\n  [{rule}] {len(items)} 条")
            for f in items[:8]:
                print("    " + f)
            if len(items) > 8:
                print(f"    …还有 {len(items) - 8} 条")
        if warn_only:
            print("\n(--warn 模式：不判失败)")
            return 0
        print("\n❌ 总闸门 FAIL")
        return 1

    print("\n✅ ALL PASS（0 FAIL）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
