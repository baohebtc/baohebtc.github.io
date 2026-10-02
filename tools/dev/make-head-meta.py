#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make-head-meta.py —— 全站注入 canonical + OG + Twitter Card + description
（F46 · ADR-0027；幂等可重复执行）

规则：
  · canonical / og:url 形态：index.html → /目录/（根 → /）；其余 → /路径.html
  · og:image：series/<slug>.html → /assets/series/<slug>/og-1200x630.png
              其余页            → /assets/brand/og-site-1200x630.png
  · description：已有则沿用；缺失则从正文首段提取（<40 字时拼 h1 补足），
    保证 40–160 字且全站唯一（seo-check C4 把关）
  · 注入块用 <!-- F46 SEO/OG --> ... <!-- /F46 --> 包裹，重跑先删旧块
  · 顺带修 index.html 的 JSON-LD：删 SearchAction（F40 未建）、inLanguage → zh-CN

用法：
  python3 tools/dev/make-head-meta.py [--dry-run]
"""
import os
import re
import sys
import html as htmllib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SITE = "https://baohebtc.github.io"
MARK_O = "<!-- F46 SEO/OG -->"
MARK_C = "<!-- /F46 -->"

SKIP_DIRS = {".git", "node_modules", ".github", "archive", "out", "samples",
             "content-source", "__pycache__", "慢读宝盒公众号"}


def git_tracked_html():
    out = os.popen(f'cd "{ROOT}" && git ls-files "*.html"').read()
    return sorted(l.strip() for l in out.splitlines() if l.strip())


def url_of(rel):
    if rel == "index.html":
        return SITE + "/"
    if rel.endswith("/index.html"):
        return SITE + "/" + rel[: -len("index.html")]
    return SITE + "/" + rel


def clean_title(raw):
    t = re.sub(r"\s+", " ", raw).strip()
    return htmllib.unescape(t)


def extract_desc(rel, html):
    """description：已有且 ≥40 字沿用；缺失或过短则从正文提取。
    提取优先级：page-subtitle/lead 段 → main 内首个 ≥25 字的 <p>；<40 字拼 h1 补足。"""
    head = html[: html.find("</head>")] if "</head>" in html else ""
    m = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']*)["\']', head, re.I)
    if m and len(m.group(1).strip()) >= 40:
        return m.group(1).strip(), False

    body = html[html.find("</head>"):]
    main_i = body.find("<main")
    if main_i > 0:
        body = body[main_i:]
    body = re.sub(r"<(script|style|nav)\b.*?</\1>", "", body, flags=re.S | re.I)
    h1m = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
    h1 = re.sub(r"<[^>]+>", "", h1m.group(1)).strip() if h1m else ""
    h1 = re.sub(r"^[\U0001F300-\U0001FAFF\u2600-\u27BF\s]+", "", h1)  # 去 emoji
    h1 = re.sub(r"\s+", " ", htmllib.unescape(h1))

    strip = lambda raw: re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", "", raw))).strip()
    # 1) page-subtitle / lead
    p = ""
    sm = re.search(r'<p[^>]*class="[^"]*(?:page-subtitle|lead|subtitle)[^"]*"[^>]*>(.*?)</p>', body, re.S)
    if sm:
        p = strip(sm.group(1))
    # 2) main 内首个 ≥25 字的段落（跳过卡片引导短句）
    if len(p) < 25:
        for pm in re.finditer(r"<p[^>]*>(.*?)</p>", body, re.S):
            cand = strip(pm.group(1))
            if len(cand) >= 25:
                p = cand
                break

    desc = p
    if len(desc) < 40 and h1:
        desc = f"{h1}：{p}" if p else h1
    if len(desc) < 40:
        desc += "——比特币学习地图，六个视角理解比特币。"
    return desc[:160], True


def og_image_for(rel):
    if rel.startswith("series/") and rel.endswith(".html") and "index" not in rel:
        slug = os.path.basename(rel)[:-5]
        p = os.path.join(ROOT, "assets/series", slug, "og-1200x630.png")
        if os.path.isfile(p):
            return f"{SITE}/assets/series/{slug}/og-1200x630.png"
    return f"{SITE}/assets/brand/og-site-1200x630.png"


def build_block(rel, title, desc, og_img, url):
    esc = lambda s: htmllib.escape(s, quote=True)
    lines = [MARK_O]
    lines.append(f'  <link rel="canonical" href="{esc(url)}">')
    lines.append(f'  <meta property="og:title" content="{esc(title)}">')
    lines.append('  <meta property="og:type" content="website">')
    lines.append(f'  <meta property="og:url" content="{esc(url)}">')
    lines.append(f'  <meta property="og:image" content="{esc(og_img)}">')
    lines.append('  <meta property="og:image:width" content="1200">')
    lines.append('  <meta property="og:image:height" content="630">')
    lines.append('  <meta property="og:site_name" content="比特币学习地图">')
    lines.append('  <meta property="og:locale" content="zh_CN">')
    lines.append(f'  <meta property="og:description" content="{esc(desc)}">')
    lines.append('  <meta name="twitter:card" content="summary_large_image">')
    lines.append(f'  <meta name="twitter:title" content="{esc(title)}">')
    lines.append(f'  <meta name="twitter:description" content="{esc(desc)}">')
    lines.append(f'  <meta name="twitter:image" content="{esc(og_img)}">')
    lines.append(MARK_C)
    return "\n".join(lines)


def fix_jsonld(html, rel):
    """C6：删 SearchAction（F40 未建）；inLanguage 收敛 zh-CN。"""
    n = 0
    def repl(m):
        nonlocal n
        blob = m.group(1)
        if "SearchAction" in blob:
            blob2 = re.sub(r',\s*"potentialAction"\s*:\s*\{.*?\}\s*(?=\})', "", blob, flags=re.S)
            if blob2 != blob:
                n += 1
                blob = blob2
        blob2 = re.sub(r'"inLanguage"\s*:\s*\[[^\]]*\]', '"inLanguage": ["zh-CN"]', blob)
        if blob2 != blob:
            n += 1
            blob = blob2
        return f'<script type="application/ld+json">{blob}</script>'
    html = re.sub(r'<script type="application/ld\+json">(.*?)</script>', repl, html, flags=re.S)
    return html, n


def main():
    dry = "--dry-run" in sys.argv
    pages = git_tracked_html()
    injected = desc_added = jsonld_fixed = 0

    for rel in pages:
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            continue
        s = open(path, encoding="utf-8").read()

        # 幂等：删旧注入块
        s = re.sub(re.escape(MARK_O) + r".*?" + re.escape(MARK_C) + r"\n?", "", s, flags=re.S)

        tm = re.search(r"<title>(.*?)</title>", s, re.S)
        title = clean_title(tm.group(1)) if tm else "比特币学习地图"
        desc, added = extract_desc(rel, s)

        # description 重写时：删掉原生旧标签（新标签随注入块进入）
        if added:
            s = re.sub(r'\s*<meta\s+name=["\']description["\']\s+content=["\'][^"\']*["\']>',
                       "", s, count=1, flags=re.I)
        og = og_image_for(rel)
        url = url_of(rel)
        block = build_block(rel, title, desc, og, url)

        # description 缺失 → 连同注入块一起补
        if added and not dry:
            if f'name="description"' not in s[: s.find("</head>")]:
                dmeta = f'  <meta name="description" content="{htmllib.escape(desc, quote=True)}">\n'
                block = block.replace(MARK_O + "\n", MARK_O + "\n" + dmeta, 1)
        if added:
            desc_added += 1

        # 注入到 </head> 前
        i = s.find("</head>")
        assert i > 0, rel
        s = s[:i] + block + "\n" + s[i:]

        # JSON-LD 一致性
        s, nfix = fix_jsonld(s, rel)
        jsonld_fixed += nfix

        if not dry:
            open(path, "w", encoding="utf-8").write(s)
        injected += 1

    act = "（dry-run，未写入）" if dry else ""
    print(f"✅ 注入 {injected} 页{act}｜补 description {desc_added}｜JSON-LD 修复 {jsonld_fixed} 处")


if __name__ == "__main__":
    main()
