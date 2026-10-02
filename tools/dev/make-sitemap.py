#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make-sitemap.py —— 全量重建 sitemap.xml（F46 · ADR-0027）

起因：手工维护的 sitemap 停留在 2026-08-14、44 条 URL、零条 /series/。
     每次新增页面都要人肉补——欠账的根源是「没有生成器」。

规则：
  · 覆盖 git 跟踪的全部 *.html（与 seo-check C3 同一清单来源，两闸不打架）
  · URL 形态与 canonical 一致（index.html → /目录/）
  · lastmod 取该文件的最近一次 git commit 日期（无提交历史则今天）
  · priority：/ = 1.0；*/index.html 栏目页 = 0.8；连载正文 = 0.9；其余 = 0.7
  · changefreq：首页/栏目 weekly，内容页 monthly

用法：
  python3 tools/dev/make-sitemap.py
"""
import os
import re
import subprocess
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SITE = "https://baohebtc.github.io"


def git_tracked_html():
    out = subprocess.run(["git", "ls-files", "*.html"], cwd=ROOT,
                         capture_output=True, text=True).stdout
    return sorted(l.strip() for l in out.splitlines() if l.strip())


def lastmod_of(rel):
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%as", "--", rel], cwd=ROOT,
            capture_output=True, text=True).stdout.strip()
        return out or date.today().isoformat()
    except Exception:
        return date.today().isoformat()


def url_of(rel):
    if rel == "index.html":
        return SITE + "/"
    if rel.endswith("/index.html"):
        return SITE + "/" + rel[: -len("index.html")]
    return SITE + "/" + rel


def priority_of(rel):
    if rel == "index.html":
        return "1.0"
    if rel.startswith("series/") and not rel.endswith("index.html"):
        return "0.9"
    if rel.endswith("/index.html"):
        return "0.8"
    return "0.7"


def main():
    pages = git_tracked_html()
    if not pages:
        print("✗ 未取到 HTML 清单")
        return 1

    rows = []
    for rel in pages:
        u = url_of(rel)
        lm = lastmod_of(rel)
        freq = "weekly" if (rel == "index.html" or rel.endswith("/index.html")) else "monthly"
        rows.append(
            "  <url>\n"
            f"    <loc>{u}</loc>\n"
            f"    <lastmod>{lm}</lastmod>\n"
            f"    <changefreq>{freq}</changefreq>\n"
            f"    <priority>{priority_of(rel)}</priority>\n"
            "  </url>")

    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + "\n".join(rows) + "\n</urlset>\n")

    out = os.path.join(ROOT, "sitemap.xml")
    open(out, "w", encoding="utf-8").write(xml)

    n_series = sum(1 for r in pages if r.startswith("series/"))
    print(f"✅ sitemap.xml 重建：{len(pages)} 条（连载 {n_series} 条）→ {os.path.relpath(out, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
