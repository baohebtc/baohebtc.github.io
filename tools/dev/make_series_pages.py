#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_series_pages.py —— 慢读连载上线生成器（F42 · ADR-0025）

为什么要有这个脚本：
  十篇连载的母本躺在 `慢读宝盒公众号/`，被 .gitignore 排除（里面有调研笔记、
  推送台账、封面工程文件，不适合进公开站）。但那 35,289 个汉字是全站最厚的
  资产，却对网站访客完全不可见——首页检索「连载/文章/慢读」零命中。

  本脚本做「提纯」而不是「搬运」：
    母本（untracked，永远不动） ──提纯──> series/ + assets/series/（进 git）
    ① 剥掉发布配置头（里头有公众号后台字段）
    ② 剥掉固定尾板（关注引导 / 在看 / 下篇预告），换成站内化的风险提示 + 上下篇
    ③ 剥掉备忘注释
    ④ 把 ../03-配图/xx.png 复制进仓库并改写路径（文件名序号对齐图注编号）

  母本永远不被修改、不被入库。重新生成 = 重跑本脚本，幂等。

用法：
  python3 tools/dev/make_series_pages.py                    # 全部 10 篇
  python3 tools/dev/make_series_pages.py --only 08-private-key-cliff   # 单篇样张
  python3 tools/dev/make_series_pages.py --dry-run          # 只报告不落盘
"""
import argparse
import html
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_ROOT = os.path.join(ROOT, "慢读宝盒公众号")
SERIES_DIR = os.path.join(ROOT, "series")
ASSETS_DIR = os.path.join(ROOT, "assets", "series")

# 顺序即连载顺序 —— 必须与 tools/dev/series-check.py 的 EXPECTED_SLUGS 一致
STATIONS = [
    ("站1-现金湾",            "01-cash-bay",           "现金湾",   "第 1 站"),
    ("站1.5-钱到底是什么",     "01x-what-is-money",     "钱到底是什么", "第 1.5 站"),
    ("站2-银行堡-货币三大缺陷", "02-bank-fortress",      "银行堡",   "第 2 站"),
    ("站3-双花峡-双花难题",    "03-double-spend-gorge", "双花峡",   "第 3 站"),
    ("站4-账本海",            "04-ledger-sea",         "账本海",   "第 4 站"),
    ("站5-哈希岭",            "05-hash-ridge",         "哈希岭",   "第 5 站"),
    ("站6-共识峰",            "06-consensus-peak",     "共识峰",   "第 6 站"),
    ("站7-矿工谷",            "07-miner-valley",       "矿工谷",   "第 7 站"),
    ("站8-私钥崖",            "08-private-key-cliff",  "私钥崖",   "第 8 站"),
    ("站9-代码之巅",          "09-code-summit",        "代码之巅", "第 9 站"),
]

# 连载站 ↔ learning 知识页 1:1 映射（2026-10-01 重配定稿，玺跞已授权）
# 纠正两处错位：站3 双花峡 04-06(网络节点)→04-03(交易)；站9 代码之巅 04-00(总览)→04-06(节点网络)
LEARNING_MAP = {
    "01-cash-bay":           ("learning/01-philosophy/01-03-bitcoin-answer.html",      "比特币的答案"),
    "01x-what-is-money":     ("learning/01-philosophy/01-01-money.html",               "货币的千年之问"),
    "02-bank-fortress":      ("learning/01-philosophy/01-02-three-flaws.html",         "货币的三大历史缺陷"),
    "03-double-spend-gorge": ("learning/04-technology/04-03-transactions.html",        "交易与 UTXO"),
    "04-ledger-sea":         ("learning/04-technology/04-04-blockchain-structure.html","区块链的数据结构"),
    "05-hash-ridge":         ("learning/04-technology/04-01-cryptography.html",        "密码学基础"),
    "06-consensus-peak":     ("learning/04-technology/04-05-mining-consensus.html",    "挖矿与共识"),
    "07-miner-valley":       ("learning/02-basics/02-04-mining.html",                  "挖矿入门"),
    "08-private-key-cliff":  ("learning/02-basics/02-02-keys-ownership.html",          "私钥与所有权"),
    "09-code-summit":        ("learning/04-technology/04-06-nodes-network.html",       "节点与网络"),
}

STATION_EMOJI = {
    "01-cash-bay": "🏖️", "01x-what-is-money": "❓", "02-bank-fortress": "🏰",
    "03-double-spend-gorge": "🌉", "04-ledger-sea": "🌊", "05-hash-ridge": "⛰️",
    "06-consensus-peak": "🗻", "07-miner-valley": "⛏️", "08-private-key-cliff": "🧗",
    "09-code-summit": "🏔️",
}

COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
IMG_LINE_RE = re.compile(r"^!\[([^\]]*)\]\(([^)\s]+)\)\s*$")
FRONT_TITLE_RE = re.compile(r"^\s*-\s*标题[：:]\s*(.+?)\s*$", re.M)
FRONT_SUMMARY_RE = re.compile(r"^\s*-\s*摘要[：:]\s*(.+?)\s*$", re.M)
TAIL_ANCHOR_RE = re.compile(r"^>\s*(🧭|📮)?\s*.*固定尾板")


# ═══════════════════════════════════════════════ 行内渲染
def render_inline(text):
    """处理行内元素：代码 / 链接 / 粗体 / 斜体。顺序敏感。"""
    codes = []

    def stash(m):
        codes.append(m.group(1))
        return "\x00%d\x00" % (len(codes) - 1)

    text = re.sub(r"`([^`]+)`", stash, text)
    text = html.escape(text, quote=False)

    def link(m):
        label, href = m.group(1), m.group(2)
        if href.startswith(("http://", "https://")):
            return '<a href="%s" target="_blank" rel="noopener noreferrer">%s</a>' % (href, label)
        return '<a href="%s">%s</a>' % (href, label)

    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, text)
    text = re.sub(r"\*\*([^*]+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__([^_]+?)__", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\*\w])\*([^*\n]+?)\*(?!\*)", r"<em>\1</em>", text)

    def restore(m):
        return "<code>%s</code>" % html.escape(codes[int(m.group(1))])

    return re.sub("\x00(\\d+)\x00", restore, text)


# ═══════════════════════════════════════════════ 块级渲染
def _table_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def _is_sep(line):
    return bool(re.match(r"^\s*\|?[\s:\-|]+\|?\s*$", line)) and "-" in line


def render_md(md_text, copy_figure):
    """
    md_text  →  HTML
    copy_figure(caption_raw, rel_src) → (img_src, figcaption_html)
    """
    lines = md_text.split("\n")
    out = []
    i, n = 0, len(lines)
    para = []
    fig_no = 0

    def flush_para():
        if para:
            joined = " ".join(para).strip()
            if "![" in joined:
                raise SystemExit("✗ 图片写在了段落里难以拆分，请改成独占一行：%s" % joined[:60])
            out.append("<p>%s</p>" % render_inline(joined))
            para.clear()

    while i < n:
        raw = lines[i]
        line = raw.rstrip()

        # ---- 代码块
        if re.match(r"^\s*```", line):
            flush_para()
            lang = line.strip()[3:].strip()
            i += 1
            buf = []
            while i < n and not re.match(r"^\s*```", lines[i]):
                buf.append(lines[i])
                i += 1
            i += 1
            cls = ' class="lang-%s"' % html.escape(lang) if lang else ""
            out.append("<pre><code%s>%s</code></pre>" % (cls, html.escape("\n".join(buf))))
            continue

        # ---- 空行
        if not line.strip():
            flush_para()
            i += 1
            continue

        # ---- 分割线
        if re.match(r"^\s*([-*_])\s*\1\s*\1[\s\-*_]*$", line) and "|" not in line:
            flush_para()
            out.append('<hr class="series-hr">')
            i += 1
            continue

        # ---- 图片（独占一行）
        m = IMG_LINE_RE.match(line.strip())
        if m:
            flush_para()
            fig_no += 1
            cap_raw, rel = m.group(1).strip(), m.group(2)
            src, cap_html = copy_figure(fig_no, cap_raw, rel)
            out.append(
                '<figure class="series-fig">\n'
                '  <img src="%s" alt="%s" loading="lazy">\n'
                "  <figcaption>%s</figcaption>\n"
                "</figure>" % (src, html.escape(cap_raw, quote=True), cap_html)
            )
            i += 1
            continue

        # ---- 表格
        if line.strip().startswith("|") and i + 1 < n and _is_sep(lines[i + 1]):
            flush_para()
            head = _table_row(line)
            i += 2
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(_table_row(lines[i]))
                i += 1
            th = "".join("<th>%s</th>" % render_inline(c) for c in head)
            tb = "".join(
                "<tr>%s</tr>" % "".join(
                    "<td>%s</td>" % render_inline(c if k < len(r) else "")
                    for k, c in enumerate(r)
                )
                for r in rows
            )
            out.append(
                '<div class="series-table-wrap"><table>\n<thead><tr>%s</tr></thead>\n'
                "<tbody>\n%s\n</tbody>\n</table></div>" % (th, tb)
            )
            continue

        # ---- 标题
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            flush_para()
            lv = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (lv, render_inline(m.group(2).strip()), lv))
            i += 1
            continue

        # ---- 引用（逐行渲染再拼接，<br> 必须在转义之后加，否则会显示成字面文本）
        if re.match(r"^\s*>\s?", line):
            flush_para()
            buf = []
            while i < n and re.match(r"^\s*>\s?", lines[i]):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append("<blockquote>%s</blockquote>"
                       % "<br>".join(render_inline(l) for l in buf))
            continue

        # ---- 列表
        m = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", line)
        if m:
            flush_para()
            ordered = bool(re.match(r"^\d+[.)]", m.group(2)))
            tag = "ol" if ordered else "ul"
            items = []
            while i < n:
                mm = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", lines[i])
                if not mm:
                    if items and lines[i].strip() and re.match(r"^\s{2,}\S", lines[i]):
                        items[-1] += " " + lines[i].strip()
                        i += 1
                        continue
                    break
                cur_ordered = bool(re.match(r"^\d+[.)]", mm.group(2)))
                if cur_ordered != ordered and len(mm.group(1)) == 0:
                    break
                items.append(mm.group(3).strip())
                i += 1
            lis = "".join("<li>%s</li>" % render_inline(it) for it in items)
            out.append("<%s>%s</%s>" % (tag, lis, tag))
            continue

        para.append(line.strip())
        i += 1

    flush_para()
    return "\n".join(out)


# ═══════════════════════════════════════════════ 母本清洗
def clean_source(md_text):
    """返回 (front, body_lines)。剥注释、剥尾板、剥标题。"""
    front = {}
    raw_nc = COMMENT_RE.sub("", md_text)

    # 发布配置头在剥注释前提取
    fm = COMMENT_RE.search(md_text)
    if fm:
        blk = fm.group(0)
        mt = FRONT_TITLE_RE.search(blk)
        ms = FRONT_SUMMARY_RE.search(blk)
        if mt:
            front["title"] = mt.group(1).strip()
        if ms:
            front["summary"] = ms.group(1).strip()

    lines = raw_nc.split("\n")

    # 去掉开头的空行 + `# 主标题` + `> 副标题`
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and lines[0].startswith("# "):
        front.setdefault("h1", lines[0][2:].strip())
        lines.pop(0)
        while lines and not lines[0].strip():
            lines.pop(0)
        if lines and lines[0].startswith("> "):
            front.setdefault("lead", lines[0][2:].strip())
            lines.pop(0)

    # 切掉固定尾板及其之后的一切
    cut = None
    for k, l in enumerate(lines):
        if TAIL_ANCHOR_RE.match(l.strip()):
            cut = k
            break
    tail_remaining = []
    if cut is not None:
        # 尾板是一整个引用块，连续消费到引用结束；之后若还有正文，说明猜错了结构
        j = cut
        while j < len(lines) and (re.match(r"^\s*>\s?", lines[j]) or not lines[j].strip()):
            j += 1
        tail_remaining = [l for l in lines[j:] if l.strip() and not re.match(r"^\s*---+\s*$", l)]
        if any(len(l.strip()) > 20 for l in tail_remaining):
            print("  ⚠️ 尾板之后仍有内容被丢弃：%s" % tail_remaining[0][:60])
        lines = lines[:cut]

    # 收尾：去掉末尾多余的分割线与空行
    while lines and (not lines[-1].strip() or re.match(r"^\s*---+\s*$", lines[-1])):
        lines.pop()

    return front, lines


# ═══════════════════════════════════════════════ 图片搬运
def normalize_img_name(fig_no, src_path):
    """目标文件名：{序号:02d}-{原名}。序号必须在最前，门闸 S3 靠文件名首段校验。"""
    base = os.path.basename(src_path)
    base = re.sub(r"^\d{1,3}[-_]", "", base)  # 去掉原名自带的序号前缀，避免重复
    return "%02d-%s" % (fig_no, base)


def build_caption_html(fig_no, cap_raw):
    """图注：原文的「图 N：标题｜副标」→ 三段层次。序号由门闸 S3 校验。"""
    m = re.match(r"^图\s*(\d+)\s*[：:]\s*(.*)$", cap_raw)
    if m:
        num, rest = m.group(1), m.group(2)
        parts = [p.strip() for p in re.split(r"[｜|]", rest) if p.strip()]
        cap = '<span class="cap-no">图 %s</span>' % num
        cap += '<span class="cap-main">%s</span>' % html.escape(parts[0])
        if len(parts) > 1:
            cap += '<span class="cap-sub">%s</span>' % html.escape("｜".join(parts[1:]))
        return cap
    return ('<span class="cap-no">图 %s</span><span class="cap-main">%s</span>'
            % (fig_no, html.escape(cap_raw)))


def make_figure_copier(slug, md_dir, stats, do_copy=True):
    dest_dir = os.path.join(ASSETS_DIR, slug)

    def copy_figure(fig_no, cap_raw, rel_src):
        abs_src = os.path.normpath(os.path.join(md_dir, rel_src))
        if not os.path.isfile(abs_src):
            raise SystemExit("✗ 配图不存在：%s （母本的相对路径可能变了）" % abs_src)
        dest_name = normalize_img_name(fig_no, abs_src)
        if do_copy:
            os.makedirs(dest_dir, exist_ok=True)
            shutil.copy2(abs_src, os.path.join(dest_dir, dest_name))
        stats["images"] += 1
        stats["bytes"] += os.path.getsize(abs_src)
        return "../assets/series/%s/%s" % (slug, dest_name), build_caption_html(fig_no, cap_raw)

    return copy_figure


# ═══════════════════════════════════════════════ 页面模板
def page_html(slug, station, emoji, title, lead, summary, body_html, idx, stats=None):
    total = len(STATIONS)
    prev_s = STATIONS[idx - 1] if idx > 0 else None
    next_s = STATIONS[idx + 1] if idx < total - 1 else None

    nav_prev = (
        '<a href="{s}.html" class="chapter-nav-link prev"><span class="nav-icon">←</span>'
        '<div class="nav-text"><div class="nav-label">上一篇 · {sn}</div>'
        '<div class="nav-title">{st}</div></div></a>'.format(
            s=prev_s[1], sn=prev_s[2], st=html.escape(prev_s[2]))
        if prev_s else
        '<a href="index.html" class="chapter-nav-link prev"><span class="nav-icon">←</span>'
        '<div class="nav-text"><div class="nav-label">已是第一篇</div>'
        '<div class="nav-title">回到连载目录</div></div></a>'
    )
    nav_next = (
        '<a href="{s}.html" class="chapter-nav-link next">'
        '<div class="nav-text" style="text-align:right"><div class="nav-label">下一篇 · {sn}</div>'
        '<div class="nav-title">{st}</div></div><span class="nav-icon">→</span></a>'.format(
            s=next_s[1], sn=next_s[2], st=html.escape(next_s[2]))
        if next_s else
        '<a href="index.html" class="chapter-nav-link next">'
        '<div class="nav-text" style="text-align:right"><div class="nav-label">连载完结</div>'
        '<div class="nav-title">重读第 1 站</div></div><span class="nav-icon">→</span></a>'
    )

    return """<!DOCTYPE html>
<html lang="zh-CN" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="manifest" href="../manifest.json">
<meta name="theme-color" content="#f7931a">
<title>{title} · 慢读连载 · 比特币学习地图</title>
<meta name="description" content="{summary}">
<link rel="stylesheet" href="../shared/style.css">
<link rel="stylesheet" href="../shared/series.css">
</head>
<body data-no-auto-toc>

<div class="reading-progress"><div class="fill" id="progress-fill"></div></div>

<nav class="top-nav">
  <div class="nav-inner container">
    <a href="../index.html" class="nav-logo">
      <span class="logo-icon">₿</span>
      <span class="logo-text">学习地图</span>
      <span class="logo-sub">Learning Map</span>
    </a>
    <div class="nav-center">
      <div class="nav-links">
        <a href="../index.html" class="nav-link" data-section="home">🏠 首页</a>
        <a href="../learning/00-overview.html" class="nav-link" data-section="learning">📚 学习区</a>
        <a href="../learning-map.html" class="nav-link" data-section="map">🗺️ 学习地图</a>
        <a href="../tools/index.html" class="nav-link" data-section="tools">🛠️ 工具</a>
        <a href="../reference/index.html" class="nav-link" data-section="reference">📖 参考</a>
        <a href="../collection/index.html" class="nav-link" data-section="collection">🗂️ 文集</a>
        <a href="../series/index.html" class="nav-link" data-section="series">📕 慢读连载</a>
      </div>
    </div>
    <div class="nav-right">
      <button class="btn btn-icon btn-sm btn-ghost" data-action="toggle-theme" onclick="BTCMap.toggleTheme()">🌓</button>
    </div>
  </div>
</nav>

<main class="article-wrap series-wrap">
  <div class="container">
    <div class="breadcrumb">
      <a href="../index.html">首页</a><span>›</span>
      <a href="index.html">慢读连载</a><span>›</span>
      <span>{station}</span>
    </div>

    <div class="article-header">
      <span class="chapter-label">📕 慢读连载 · {seq}</span>
      <h1><span class="emoji">{emoji}</span>{station}</h1>
      <p class="series-subtitle">{lead}</p>
      <div class="article-meta">
        <span>✍️ 慢读宝盒</span><span>·</span>
        <span>{wordcount} 字</span><span>·</span>
        <span>{figcount} 图</span><span>·</span>
        <span>约 {minutes} 分钟读完</span>
      </div>
    </div>

    <div class="article-body series-body">
{body}
    </div>

    <div class="series-xlink">
      🔗 <b>延伸阅读</b>：这一站的知识点在学习区的对应页——
      <a href="../{learn_path}">{learn_title}</a>（结构化的知识条目版）
    </div>

    <div class="series-endcard">
      <p class="series-endcard-lead">这一站读完了。</p>
      <p>慢读宝盒从 0 开始，十站一篇一篇把比特币讲清楚。每站的比喻都会先搭桥、再拆桥——
      重点不在「像什么」，而在「不像什么」。</p>
      <a href="index.html" class="btn btn-primary" style="display:inline-flex;margin-top:8px">📕 回到连载目录</a>
    </div>

  </div>
</main>

<nav class="chapter-nav">
  <div class="container" style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
    {nav_prev}
    {nav_next}
  </div>
</nav>

<footer>
  <div class="container">
    <div class="series-risk">
      <strong>⚠️ 风险提示</strong>：比特币价格波动剧烈，本文仅作区块链科普，不构成任何投资建议。
      比特币在中国大陆并非法定货币，参与相关活动请注意合规风险。投资需谨慎，盈亏自负。
    </div>
    <div class="footer-inner">
      <div class="footer-left"><a href="../index.html">首页</a> · <a href="../learning/00-overview.html">学习区</a> · <a href="../tools/index.html">工具</a> · <a href="../reference/index.html">参考</a> · <a href="../collection/index.html">文集</a> · <a href="../series/index.html">慢读连载</a></div>
      <div class="footer-links"><span style="font-size:0.75rem;color:var(--text-muted)">₿ 比特币学习地图</span></div>
    </div>
    <p style="margin-top:12px;font-size:0.75rem;color:var(--text-muted)">⚠️ 教育目的，不构成投资建议</p>
  </div>
</footer>

<script src="../shared/nav.js"></script>
<script>
(function() {{
  const fill = document.getElementById('progress-fill');
  if (!fill) return;
  window.addEventListener('scroll', function() {{
    const st = document.documentElement.scrollTop || document.body.scrollTop;
    const sh = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    fill.style.width = (sh > 0 ? (st / sh) * 100 : 0) + '%';
  }}, {{ passive: true }});
}})();
</script>
</body>
</html>
""".format(
        title=html.escape(title), station=html.escape(station), emoji=emoji,
        lead=html.escape(lead) if lead else "", summary=html.escape(summary)[:150],
        seq=STATIONS[idx][3], body=body_html, nav_prev=nav_prev, nav_next=nav_next,
        wordcount=stats.get("words", 0) if stats else 0,
        figcount=stats.get("images", 0) if stats else 0,
        minutes=max(1, (stats.get("words", 0) if stats else 0) // 400),
        learn_path=LEARNING_MAP[slug][0],
        learn_title=LEARNING_MAP[slug][1],
    )


def index_html(entries):
    cards = []
    for it in entries:
        cards.append("""      <a href="{slug}.html" class="series-card">
        <div class="sc-seq">{seq}</div>
        <div class="sc-body">
          <div class="sc-emoji">{emoji}</div>
          <h3>{station}</h3>
          <p class="sc-lead">{lead}</p>
          <div class="sc-meta">{words} 字 · {figs} 图 · 约 {mins} 分钟</div>
        </div>
        <div class="sc-go">→</div>
      </a>""".format(
            slug=it["slug"], seq=it["seq"], emoji=it["emoji"],
            station=html.escape(it["station"]), lead=html.escape(it["lead"]),
            words=it["words"], figs=it["figs"], mins=max(1, it["words"] // 400),
        ))
    cards_html = "\n".join(cards)
    total_words = sum(e["words"] for e in entries)
    total_figs = sum(e["figs"] for e in entries)

    return """<!DOCTYPE html>
<html lang="zh-CN" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="manifest" href="../manifest.json">
<meta name="theme-color" content="#f7931a">
<title>慢读连载 · 比特币学习地图</title>
<meta name="description" content="慢读宝盒《比特币学习地图》十站连载全文：从现金湾到代码之巅，用比喻和多视角把比特币讲清楚。">
<link rel="stylesheet" href="../shared/style.css">
<link rel="stylesheet" href="../shared/series.css">
</head>
<body data-no-auto-toc>

<nav class="top-nav">
  <div class="nav-inner container">
    <a href="../index.html" class="nav-logo">
      <span class="logo-icon">₿</span>
      <span class="logo-text">学习地图</span>
      <span class="logo-sub">Learning Map</span>
    </a>
    <div class="nav-center">
      <div class="nav-links">
        <a href="../index.html" class="nav-link" data-section="home">🏠 首页</a>
        <a href="../learning/00-overview.html" class="nav-link" data-section="learning">📚 学习区</a>
        <a href="../learning-map.html" class="nav-link" data-section="map">🗺️ 学习地图</a>
        <a href="../tools/index.html" class="nav-link" data-section="tools">🛠️ 工具</a>
        <a href="../reference/index.html" class="nav-link" data-section="reference">📖 参考</a>
        <a href="../collection/index.html" class="nav-link" data-section="collection">🗂️ 文集</a>
        <a href="../series/index.html" class="nav-link" data-section="series">📕 慢读连载</a>
      </div>
    </div>
    <div class="nav-right">
      <button class="btn btn-icon btn-sm btn-ghost" data-action="toggle-theme" onclick="BTCMap.toggleTheme()">🌓</button>
    </div>
  </div>
</nav>

<main class="series-index-wrap">
  <div class="container">
    <div class="series-hero">
      <span class="chapter-label">📕 慢读连载 · Bitcoin Learning Map</span>
      <h1>从现金湾到代码之巅，十站讲透比特币</h1>
      <p class="series-hero-lead">
        慢读宝盒的十站连载。每一站都用<b>一个比喻</b>作为桥，然后<b>认认真真把桥拆掉</b>——
        因为理解的关键不在「像什么」，而在「不像什么」。
      </p>
      <div class="series-hero-stats">
        <div><b>{n}</b><span>站</span></div>
        <div><b>{words}</b><span>字</span></div>
        <div><b>{figs}</b><span>张图解</span></div>
        <div><b>6</b><span>个视角</span></div>
      </div>
    </div>

    <div class="series-list">
{cards}
    </div>

    <div class="series-notice">
      <strong>怎么读这套连载？</strong>
      顺序读最好——后一站会站在前一站的肩膀上。如果只想挑一篇，第 1 站讲全局、
      第 5 站讲哈希、第 8 站讲私钥，各自独立成篇也能读懂。<br>
      遇到没见过的名词，去<a href="../reference/index.html">参考 · 术语表</a>；
      想看同一件事的六种说法，去<a href="../learning/00-overview.html">学习区</a>。
    </div>
  </div>
</main>

<footer>
  <div class="container">
    <div class="series-risk">
      <strong>⚠️ 风险提示</strong>：本连载为区块链科普，不构成任何投资建议。
      比特币在中国大陆并非法定货币。投资需谨慎，盈亏自负。
    </div>
    <div class="footer-inner">
      <div class="footer-left"><a href="../index.html">首页</a> · <a href="../learning/00-overview.html">学习区</a> · <a href="../tools/index.html">工具</a> · <a href="../reference/index.html">参考</a> · <a href="../collection/index.html">文集</a> · <a href="../series/index.html">慢读连载</a></div>
      <div class="footer-links"><span style="font-size:0.75rem;color:var(--text-muted)">₿ 比特币学习地图</span></div>
    </div>
    <p style="margin-top:12px;font-size:0.75rem;color:var(--text-muted)">⚠️ 教育目的，不构成投资建议</p>
  </div>
</footer>

<script src="../shared/nav.js"></script>
</body>
</html>
""".format(n=len(entries), words=total_words, figs=total_figs, cards=cards_html)


# ═══════════════════════════════════════════════ 主流程
def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    ap = argparse.ArgumentParser(description="慢读连载上线生成器（F42 · ADR-0025）")
    ap.add_argument("--only", default=None, help="只生成某一篇，传 slug")
    ap.add_argument("--dry-run", action="store_true", help="只报告不落盘")
    ap.add_argument("--src", default=SRC_ROOT, help="母本根目录")
    args = ap.parse_args()

    if not os.path.isdir(args.src):
        print("✗ 母本目录不存在：%s" % args.src)
        sys.exit(1)

    targets = STATIONS
    if args.only:
        targets = [s for s in STATIONS if s[1] == args.only]
        if not targets:
            print("✗ 未知 slug：%s" % args.only)
            sys.exit(1)

    entries = []
    print("=" * 68)
    print("make_series_pages · 慢读连载上线生成器（F42 · ADR-0025）")
    print("=" * 68)

    for idx, (dir_name, slug, station, seq) in enumerate(targets):
        md_dir = os.path.join(args.src, dir_name, "02-文章")
        cands = [f for f in os.listdir(md_dir) if f.endswith("-微信版.md")] if os.path.isdir(md_dir) else []
        if not cands:
            print("✗ 找不到微信版母本：%s" % md_dir)
            sys.exit(1)
        md_path = os.path.join(md_dir, sorted(cands)[0])

        raw = open(md_path, encoding="utf-8").read()
        front, lines = clean_source(raw)
        title = front.get("title") or front.get("h1") or station
        lead = front.get("lead", "")
        summary = front.get("summary", lead)

        stats = {"images": 0, "bytes": 0}
        copier = make_figure_copier(slug, md_dir, stats, do_copy=not args.dry_run)
        body = render_md("\n".join(lines), copier)
        words = len(re.findall(r"[\u4e00-\u9fff]", re.sub(r"<[^>]+>", "", body)))
        stats["words"] = words

        html_out = page_html(slug, station, STATION_EMOJI[slug], title, lead,
                             summary, body, STATIONS.index((dir_name, slug, station, seq)),
                             stats)
        out_path = os.path.join(SERIES_DIR, slug + ".html")
        if not args.dry_run:
            write_file(out_path, html_out)

        entries.append({
            "slug": slug, "station": station, "seq": seq, "lead": lead or summary[:40],
            "words": words, "figs": stats["images"], "emoji": STATION_EMOJI[slug],
        })
        print("  ✅ %-24s %6d 字  %2d 图  %5.1fMB  %s" % (
            slug, words, stats["images"], stats["bytes"] / 1024 / 1024,
            os.path.basename(md_path)))

    if not args.only:
        idx_path = os.path.join(SERIES_DIR, "index.html")
        if not args.dry_run:
            write_file(idx_path, index_html(entries))
        print("\n  ✅ 栏目首页 series/index.html（列出 %d 篇）" % len(entries))

    print()
    print("合计 %d 篇 · %s 汉字 · %d 张图 · %.1f MB" % (
        len(entries),
        "{:,}".format(sum(e["words"] for e in entries)),
        sum(e["figs"] for e in entries),
        sum(os.path.getsize(os.path.join(dp, f))
            for dp, dn, fn in os.walk(ASSETS_DIR) for f in fn) / 1024 / 1024
        if os.path.isdir(ASSETS_DIR) else 0,
    ))
    if args.dry_run:
        print("\n（--dry-run：未落盘）")
    else:
        print("\n下一步：python3 tools/dev/series-check.py -v")


if __name__ == "__main__":
    main()
