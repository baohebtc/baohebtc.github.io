#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seo-check.py —— 发现层（SEO / 社交分享）门闸（F46）

起因（2026-10-02 核实）：
  全站 67 个 HTML **0 canonical / 0 OG**；`sitemap.xml` 停留在 2026-08-14、
  仅 44 条 URL、**零条 `/series/`**。
  → 最厚的资产（10 篇连载 30,246 汉字）上线了，但搜索引擎靠偶然收录，
    分享到微信 / X 只有一个裸链接，没有标题、描述、缩略图。
  → **上线 ≠ 被发现**。

规则：
  C1 canonical：每页 head 必须有 <link rel="canonical">，且 URL 与自身路径一致
      （URL 形态：index.html → /目录/；其余 → /路径/文件.html）
  C2 OG + Twitter Card：og:title / og:type / og:url / og:image / og:description
      五件套 + twitter:card + twitter:image 齐全；og:url 必须与 canonical 同值
  C3 sitemap.xml：存在；覆盖全部 git 跟踪 HTML；每条 loc 对应文件真实存在；
      必须含 /series/ 全部条目
  C4 description：非空、长度 40–160 汉字区间、全站唯一（重复说明文案偷懒，
      搜索引擎会判低质）
  C5 og:image：指向的文件真实存在、宽 ≥ 600px、宽高比 ≥ 1.3（社交卡横向优先）
  C6 JSON-LD 一致性：不得声明 SearchAction（站内搜索 F40 尚未建成，
      声明了等于名不副实）；inLanguage 必须只含 zh-CN（ADR-0022 UI 锁 zh-CN）

用法：
  python3 tools/dev/seo-check.py            # 全站
  python3 tools/dev/seo-check.py -v         # 逐条列出
"""
import os
import re
import sys
import glob
import subprocess
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SITE = "https://baohebtc.github.io"

SKIP_DIRS = {".git", "node_modules", ".github", "archive", "out", "samples",
             "content-source", "__pycache__", "慢读宝盒公众号"}

OG_REQUIRED = ["og:title", "og:type", "og:url", "og:image", "og:description"]
TW_REQUIRED = ["twitter:card", "twitter:image"]


# ---------------- 工具 ----------------
def git_tracked_html():
    try:
        out = subprocess.run(["git", "ls-files", "*.html"], cwd=ROOT,
                             capture_output=True, text=True).stdout
        return sorted(l.strip() for l in out.splitlines() if l.strip())
    except Exception:
        return []


def url_of(rel):
    """页面相对路径 → 站点绝对 URL（index.html 收敛到目录形态）。"""
    if rel == "index.html":
        return SITE + "/"
    if rel.endswith("/index.html"):
        return SITE + "/" + rel[: -len("index.html")]
    return SITE + "/" + rel


def head_of(html):
    i = html.find("</head>")
    return html[: i + 7] if i > 0 else html[:3000]


def meta_content(head, key, attr="property"):
    m = re.search(r'<meta\s[^>]*%s=["\']%s["\'][^>]*>' % (attr, re.escape(key)), head, re.I)
    if not m:
        return None
    c = re.search(r'content=["\']([^"\']*)["\']', m.group(0), re.I)
    return c.group(1) if c else None


def check():
    fails, warns, stats = [], [], {"pages": 0, "canonical": 0, "og": 0, "desc": 0}

    pages = git_tracked_html()
    if not pages:
        return ["C0 未取到 git 跟踪的 HTML 列表（在仓库内运行？）"], [], stats

    descs = {}
    for rel in pages:
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            continue
        stats["pages"] += 1
        html = open(path, encoding="utf-8").read()
        head = head_of(html)
        want = url_of(rel)

        # ---------- C1 canonical ----------
        cm = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']', head, re.I)
        if not cm:
            fails.append(f"C1 {rel}: 缺 <link rel=\"canonical\">")
        else:
            got = cm.group(1).rstrip("/")
            if got != want.rstrip("/"):
                fails.append(f"C1 {rel}: canonical={got} ≠ 应为 {want}")
            else:
                stats["canonical"] += 1

        # ---------- C2 OG / Twitter ----------
        missing = [k for k in OG_REQUIRED if meta_content(head, k) is None]
        missing += [k for k in TW_REQUIRED
                    if meta_content(head, k, "name") is None]
        if missing:
            fails.append(f"C2 {rel}: 缺社交卡字段 → {', '.join(missing)}")
        else:
            stats["og"] += 1
            og_url = meta_content(head, "og:url")
            if og_url and og_url.rstrip("/") != want.rstrip("/"):
                fails.append(f"C2 {rel}: og:url={og_url} 与 canonical({want}) 不一致")
            if meta_content(head, "twitter:card") not in (None, "summary_large_image"):
                warns.append(f"C2 {rel}: twitter:card 建议用 summary_large_image")

        # ---------- C4 description ----------
        dm = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']*)["\']', head, re.I)
        desc = dm.group(1).strip() if dm else ""
        if not desc:
            fails.append(f"C4 {rel}: 缺 description")
        else:
            stats["desc"] += 1
            if not (40 <= len(desc) <= 160):
                fails.append(f"C4 {rel}: description 长度 {len(desc)} 超出 40–160 区间")
            descs.setdefault(desc, []).append(rel)

        # ---------- C5 og:image ----------
        og_img = meta_content(head, "og:image")
        if og_img:
            if og_img.startswith(SITE + "/"):
                local = os.path.join(ROOT, og_img[len(SITE) + 1:])
                if not os.path.isfile(local):
                    fails.append(f"C5 {rel}: og:image 文件不存在 → {og_img}")
                else:
                    try:
                        from PIL import Image
                        with Image.open(local) as im:
                            w, h = im.size
                        if w < 600:
                            fails.append(f"C5 {rel}: og:image 宽 {w} < 600 → {og_img}")
                        elif w / h < 1.3:
                            warns.append(f"C5 {rel}: og:image 偏方（{w}×{h}），社交卡建议横向")
                    except ImportError:
                        if "C5 未装 PIL，跳过尺寸校验" not in warns:
                            warns.append("C5 未装 PIL，跳过尺寸校验（venv 或 CI 安装 pillow 后生效）")
            elif not og_img.startswith("http"):
                fails.append(f"C5 {rel}: og:image 必须绝对 URL → {og_img}")

        # ---------- C6 JSON-LD 一致性 ----------
        for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
            blob = m.group(1)
            if "SearchAction" in blob:
                fails.append(
                    f"C6 {rel}: JSON-LD 声明 SearchAction，但站内搜索（F40）尚未建成——名不副实")
            lm = re.search(r'"inLanguage"\s*:\s*\[([^\]]*)\]', blob)
            if lm and "en" in lm.group(1):
                fails.append(
                    f"C6 {rel}: JSON-LD inLanguage 含 en，与 ADR-0022（UI 锁 zh-CN）冲突")

    # ---------- C4 重复 ----------
    for desc, rels in descs.items():
        if len(rels) > 1:
            fails.append(f"C4 description 重复于 {len(rels)} 页 → {rels[0]} 等：{desc[:34]}…")

    # ---------- C3 sitemap ----------
    sp = os.path.join(ROOT, "sitemap.xml")
    if not os.path.isfile(sp):
        fails.append("C3 缺 sitemap.xml")
    else:
        try:
            tree = ET.parse(sp)
            ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
            locs = [e.text.strip() for e in tree.iter(ns + "loc") if e.text]
        except Exception as e:
            fails.append(f"C3 sitemap.xml 解析失败：{e}")
            locs = []

        if locs:
            # 死链
            for u in locs:
                if not u.startswith(SITE + "/"):
                    fails.append(f"C3 sitemap 域名不符：{u}")
                    continue
                rel = u[len(SITE) + 1:]
                cand = os.path.join(ROOT, rel)
                if not os.path.isfile(cand) and not os.path.isfile(os.path.join(cand, "index.html")):
                    fails.append(f"C3 sitemap 条目文件不存在 → {u}")
            # 覆盖度
            want_urls = {url_of(r).rstrip("/") for r in pages}
            have_urls = {u.rstrip("/") for u in locs}
            miss = sorted(want_urls - have_urls)
            if miss:
                fails.append(f"C3 sitemap 缺 {len(miss)} 页：{', '.join(miss[:6])}"
                             + ("…" if len(miss) > 6 else ""))
            # /series/ 必须齐全
            series_pages = [r for r in pages if r.startswith("series/")]
            for r in series_pages:
                if url_of(r).rstrip("/") not in have_urls:
                    fails.append(f"C3 sitemap 缺连载页 → {url_of(r)}")

    return fails, warns, stats


def main():
    verbose = "-v" in sys.argv or "--verbose" in sys.argv
    fails, warns, stats = check()

    print("=" * 72)
    print(f"seo-check · 页面 {stats['pages']} · canonical {stats['canonical']} · "
          f"OG 齐全 {stats['og']} · description {stats['desc']}")
    print("=" * 72)

    if warns:
        print(f"\n⚠️  警告 {len(warns)} 条：")
        for w in warns[:20]:
            print("   " + w)
        if len(warns) > 20:
            print(f"   …还有 {len(warns) - 20} 条")

    if fails:
        by_rule = {}
        for f in fails:
            by_rule.setdefault(f.split()[0], []).append(f)
        print(f"\n🔴 FAIL {len(fails)} 条：")
        for rule in sorted(by_rule):
            items = by_rule[rule]
            print(f"\n  [{rule}] {len(items)} 条")
            for it in (items if verbose else items[:8]):
                print("     " + it[:150])
            if not verbose and len(items) > 8:
                print(f"     …还有 {len(items) - 8} 条（加 -v 全列）")
        print(f"\n❌ 发现层门闸未通过（{len(fails)}）")
        return 1

    print("\n✅ 发现层门闸全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
