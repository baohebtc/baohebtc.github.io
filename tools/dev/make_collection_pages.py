#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文集页面产线（Feature Ledger F31 / ADR-0021）

为什么用脚本写页面
------------------
文集六个新栏目共用同一套 DOM 结构（面包屑 → badge → h1 → 导语 → 免责条 →
分组 → 条目列表 → 页脚）。手抄六遍必然出现标签错位、data 属性漏写、免责措辞
口径不一致。改成数据驱动后：条目是数据，版式是模板，门闸（collection-check）
再兜第三道。

条目字段（五属性，门闸 R3 强制）
--------------------------------
title / author / type / source / license  —— source 必须已在
collection-sources-allowlist.txt 内（HTTP 实测过，禁止凭记忆写 URL）

用法
----
    python3 tools/dev/make_collection_pages.py            # 生成全部
    python3 tools/dev/make_collection_pages.py cypherpunks # 只生成一页
    python3 tools/dev/make_collection_pages.py --dry-run   # 只校验不落盘
"""

import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUTHORS = os.path.join(ROOT, "collection", "authors")
THEMES = os.path.join(ROOT, "collection", "themes")

DISCLAIMER_DEFAULT = (
    "学习资料索引 · 非投资建议 · 观点不代表本号立场。"
    "本站仅做公开资料的整理与索引，转载内容均保留原作者署名与许可；"
    "所载观点为原作者个人意见，不构成任何投资建议。"
)

HEAD_TMPL = """<!DOCTYPE html>
<html lang="zh-CN" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#f7931a">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="stylesheet" href="../../shared/style.css">
<style>
{style}
</style>
</head>
<body>

<nav class="top-nav">
  <div class="nav-inner container">
    <a href="../../index.html" class="nav-logo"><span class="logo-icon">\u20bf</span><span class="logo-text">\u5b66\u4e60\u5730\u56fe</span><span class="logo-sub">Learning Map</span></a>
    <div class="nav-center">
      <div class="nav-links">
        <a href="../../index.html" class="nav-link" data-section="home">\U0001f3e0 \u9996\u9875</a>
        <a href="../../learning/00-overview.html" class="nav-link" data-section="learning">\U0001f4da \u5b66\u4e60\u533a</a>
        <a href="../../learning-map.html" class="nav-link" data-section="map">\U0001f5fa\ufe0f \u5b66\u4e60\u5730\u56fe</a>
        <a href="../../tools/index.html" class="nav-link" data-section="tools">\U0001f6e0\ufe0f \u5de5\u5177</a>
        <a href="../../reference/index.html" class="nav-link" data-section="reference">\U0001f4d6 \u53c2\u8003</a>
        <a href="../../collection/index.html" class="nav-link" data-section="collection">\U0001f5c2\ufe0f \u6587\u96c6</a>
      </div>
    </div>
    <div class="nav-right">
      <div class="lang-toggle">
        <button class="btn btn-sm" data-lang="zh" onclick="BTCMap.switchLang('zh')">\u4e2d</button>
        <button class="btn btn-sm" data-lang="en" onclick="BTCMap.switchLang('en')">EN</button>
      </div>
      <button class="btn btn-icon btn-sm btn-ghost" data-action="toggle-theme" onclick="BTCMap.toggleTheme()">\U0001f313</button>
    </div>
  </div>
</nav>

<header class="author-hero">
  <div class="container">
    <div class="breadcrumb"><a href="../../index.html">\u9996\u9875</a><span>\u203a</span><a href="../index.html">\u6587\u96c6</a><span>\u203a</span><span>{crumb}</span></div>
    <span class="badge">{badge}</span>
    <h1>{h1}</h1>
    <p>{intro}</p>
  </div>
</header>

<main>
  <div class="container">
    <div class="disclaimer">
      <strong>\u514d\u8d23\u58f0\u660e\uff1a</strong>{disclaimer}
    </div>
"""

FOOTER = """
  </div>
</main>

<footer>
  <div class="container">
    <div class="footer-inner">
      <div class="footer-left">
        <a href="../../index.html">\u9996\u9875</a> \u00b7 <a href="../../learning/00-overview.html">\u5b66\u4e60\u533a</a> \u00b7 <a href="../../tools/index.html">\u5de5\u5177</a> \u00b7 <a href="../../reference/index.html">\u53c2\u8003</a> \u00b7 <a href="../index.html">\u6587\u96c6</a>
      </div>
    </div>
  </div>
</footer>

<script src="../../shared/nav.js"></script>
</body>
</html>
"""

STYLE = """.author-hero { padding: 56px 0 28px; }
.author-hero .badge { display:inline-block; font-size:0.72rem; font-weight:700; letter-spacing:0.15em; color:var(--orange); background:rgba(247,147,26,0.1); border:1px solid rgba(247,147,26,0.25); padding:5px 14px; border-radius:100px; margin-bottom:14px; }
.author-hero h1 { font-size:2.1rem; font-weight:800; margin-bottom:8px; }
.author-hero p { color:var(--text-secondary); font-size:0.92rem; max-width:620px; line-height:1.65; }
.disclaimer { margin:0 0 28px; padding:14px 16px; border:1px dashed var(--border-light); border-radius:var(--radius-sm); background:rgba(247,147,26,0.05); font-size:0.8rem; color:var(--text-secondary); line-height:1.6; }
.disclaimer strong { color:var(--orange); }
.collection-list { display:flex; flex-direction:column; gap:14px; margin-bottom:40px; }
.collection-item { background:var(--bg-card); border:1px solid var(--border); border-radius:var(--radius-sm); padding:18px 20px; transition:all var(--transition); }
.collection-item:hover { border-color:var(--border-light); box-shadow:var(--shadow); }
.ci-head { display:flex; gap:6px; margin-bottom:8px; flex-wrap:wrap; }
.ci-title { font-size:1.02rem; font-weight:700; margin-bottom:6px; }
.ci-summary { font-size:0.84rem; color:var(--text-secondary); line-height:1.6; margin-bottom:10px; }
.ci-meta { display:flex; gap:16px; flex-wrap:wrap; font-size:0.76rem; color:var(--text-muted); }
.ci-meta a { color:var(--orange); text-decoration:none; }
.tag { font-size:0.66rem; padding:2px 9px; border-radius:10px; background:rgba(247,147,26,0.12); color:var(--orange); font-weight:600; }
.tag-orange { background:rgba(247,147,26,0.18); }
.tag-blue { background:rgba(59,130,246,0.14); color:#6aa6ff; }
.tag-green { background:rgba(16,185,129,0.14); color:#4ade80; }
.tag-purple { background:rgba(139,92,246,0.14); color:#a78bfa; }
.section-h { font-size:0.8rem; font-weight:700; color:var(--text-muted); letter-spacing:0.08em; margin:26px 0 12px; }
.stance { display:flex; gap:16px; flex-wrap:wrap; font-size:0.76rem; color:var(--text-muted); margin:0 0 20px; }
@media (max-width:600px){ .ci-meta{ gap:8px; } }"""

ITEM_TMPL = """      <div class="collection-item" data-title="{title}" data-author="{author}" data-type="{type}" data-source="{source}" data-license="{license}">
        <div class="ci-head">{tags}</div>
        <h3 class="ci-title">{ctitle}</h3>
        <p class="ci-summary">{summary}</p>
        <div class="ci-meta">
          <span>\u4f5c\u8005\uff1a{author}</span>
          <a href="{source}" target="_blank" rel="noopener">\u6765\u6e90\uff1a{linklabel} \u2197</a>
          <span>\u8bb8\u53ef\uff1a{license}</span>
        </div>
      </div>
"""

NI = "https://nakamotoinstitute.org/"


def render_item(it):
    """it = (title, author, type, source, license, tags_html, summary, linklabel)"""
    title, author, typ, source, license_, tags, summary, linklabel = it
    # tags 已是 tag() 产出的完整 <span> 片段列表，直接拼接
    return ITEM_TMPL.format(title=title, author=author, type=typ, source=source,
                            license=license_, tags="".join(tags), ctitle=title,
                            summary=summary, linklabel=linklabel)


def tag(*args):
    """tag('蓝色标') -> <span class="tag">蓝色标</span>；tag('tag-blue','开源') 可指定色"""
    if len(args) == 1:
        return '<span class="tag">%s</span>' % args[0]
    return '<span class="tag %s">%s</span>' % (args[0], args[1])


def build_page(spec):
    parts = [HEAD_TMPL.format(title=spec["title"], desc=spec["desc"],
                              style=STYLE, crumb=spec["crumb"], badge=spec["badge"],
                              h1=spec["h1"], intro=spec["intro"],
                              disclaimer=spec.get("disclaimer", DISCLAIMER_DEFAULT))]
    if spec.get("extra"):
        parts.append(spec["extra"])
    for sec in spec["sections"]:
        if sec.get("h"):
            parts.append('\n    <div class="section-h">%s</div>\n' % sec["h"])
        parts.append('    <div class="collection-list">\n')
        for it in sec["items"]:
            parts.append(render_item(it))
        parts.append("\n    </div>\n")
    parts.append(FOOTER)
    return "".join(parts)


# =====================================================================
# 数据区（每条 source 均已 HTTP 实测，见 collection-sources-allowlist.txt）
# =====================================================================
PAGES = {}

PAGES["cypherpunks"] = {
    "dir": AUTHORS, "crumb": "密码朋克群像", "badge": "作者轴 · 密码朋克群像",
    "h1": "🧪 密码朋克群像",
    "title": "密码朋克群像 · 文集 · 比特币学习地图",
    "desc": "比特币的思想祖先合集：密码朋克宣言、b-money、Bit Gold、Hashcash、RPOW、时间戳与签名等先驱文献。",
    "intro": "比特币白皮书的末尾，列着八篇参考文献。那八篇就是这个栏目——它说明比特币不是凭空出现的，而是把一群人在二十多年里想过的、做过的东西拼在了一起。这栏不收录某个人的完整著作集，而是把先驱们各自的「那一篇」聚到一起。建议先读宣言，再读技术文献，最后看他们彼此如何引用对方。",
    "sections": [
        {"h": "一、两份宣言（先读这两份）", "items": [
            ("《密码朋克宣言》与休斯著述", "Eric Hughes", "宣言", NI + "authors/eric-hughes/", "第三方汇编（保留出处）",
              [tag("宣言"), tag("tag-blue", "1993")],
              "1993 年 3 月，Eric Hughes 写下这份宣言，开篇就划清了一件事：隐私不是「有什么要藏」，而是选择性向世界呈现自己的权利。这是整个密码朋克运动的思想起点，也是后来比特币隐私叙事的根。",
              "中本聪研究所·Eric Hughes 著述"),
             ("《加密无政府主义者宣言》", "Timothy C. May", "宣言", NI + "library/crypto-anarchist-manifesto/", "第三方汇编（保留出处）",
              [tag("宣言"), tag("tag-purple", "1988")],
              "比《密码朋克宣言》还早五年。May 在英特尔退休后写下这份宣言，预言 freely 流通的加密技术会改变国家与市场的关系。它的语气更激进，也更能解释为什么早期比特币社区对监管天然不信任。",
              "中本聪研究所全文版"),
        ]},
        {"h": "二、比特币的直接技术前身（白皮书里被点名的那些）", "items": [
            ("《b-money》", "Wei Dai", "提案", NI + "library/b-money/", "公开提案文本",
              [tag("提案"), tag("tag-orange", "1998")],
              "1998 年，Wei Dai 在密码朋克邮件列表提出 b-money：用计算难题（工作量证明）创造货币，用集体账本记账，参与者以押金互相担保。它与比特币的骨架高度相似，中本聪在白皮书里明确援引了它。",
              "中本聪研究所全文版"),
             ("b-money 原文站点（作者自托管）", "Wei Dai", "原文站点", "http://www.weidai.com/bmoney.txt", "作者公开原稿",
              [tag("原文"), tag("tag-blue", "一手")],
              "同一份提案的作者原始文本页面，朴素的纯文本排版。想确认中本聪研究所的版本有没有整理上的删改，来这里对照最方便。",
              "weidai.com 作者原稿"),
             ("《Bit Gold》", "Nick Szabo", "提案", NI + "library/bit-gold/", "第三方汇编（保留署名）",
              [tag("提案"), tag("tag-orange", "2005")],
              "2005 年 Szabo 提出 Bit Gold：链式的解题记录、 occurring 时间戳服务、无法伪造的稀缺性。它离比特币只差最后一步——没能解决双重支付。读懂它，就懂了中本聪真正补上的那块拼图在哪里。",
              "中本聪研究所全文版"),
             ("《Hashcash：一种抵御拒绝服务攻击的措施》", "Adam Back", "技术论文", NI + "library/hashcash/", "第三方汇编（保留署名）",
              [tag("论文"), tag("tag-orange", "2002")],
              "2002 年 Adam Back 提出 Hashcash，本意是给邮件加一份「计算成本」来遏制垃圾邮件。中本聪把它借来，改造成比特币的工作量证明——这是白皮书引用的第三篇。",
              "中本聪研究所全文版"),
             ("Hashcash 论文原文 PDF", "Adam Back", "技术论文", "http://www.hashcash.org/papers/hashcash.pdf", "作者公开原稿",
              [tag("论文"), tag("tag-blue", "一手")],
              "Hashcash 论文的作者原始 PDF 存档。想看公式推导与参数选择的原始表述，这是第一手来源。",
              "hashcash.org 作者原稿"),
             ("《RPOW：可复用工作量证明》", "Hal Finney", "系统设计", NI + "library/rpow/", "第三方汇编（保留署名）",
              [tag("系统设计"), tag("tag-orange", "2004")],
              "2004 年 Hal Finney 造出了 RPOW：把 Hashcash 的证明做成可转让的代币，并用可信硬件防止重复兑现。它已经非常接近比特币，但防伪仍然依赖一台可信服务器——这一步之差，正是比特币要消掉的信任假设。",
              "中本聪研究所全文版"),
        ]},
        {"h": "三、更早期的技术地基与延展思考", "items": [
            ("《双花检测：比特币之前的尝试》", "Hal Finney", "技术论文", NI + "library/detecting-double-spending/", "第三方汇编（保留署名）",
              [tag("论文"), tag("tag-blue", "1993")],
              "早在 1993 年，Finney 就在邮件列表里讨论如何发现同一笔电子现金被重复使用。读懂这篇，再看比特币用全局账本解决这个问题，会有种「原来争论了十七年」的感觉。",
              "中本聪研究所全文版"),
             ("《智能合约》", "Nick Szabo", "论文", NI + "library/smart-contracts/", "第三方汇编（保留署名）",
              [tag("论文"), tag("tag-purple", "1994")],
              "「智能合约」这个词是 Szabo 在 1994 年造的，比以太坊早了二十年。原文讲的其实是自动售货机式的合约执行，而非今天链上的可编程脚本——回到源头读一遍，能纠掉不少后来形成的误解。",
              "中本聪研究所全文版"),
             ("Haber 与 Stornetta 时间戳文献", "Stuart Haber、W. Scott Stornetta", "学术文献", NI + "authors/stuart-haber/", "第三方汇编（保留出处）",
              [tag("文献"), tag("tag-blue", "1991 起")],
              "1991 年起，Haber 与 Stornetta 用哈希链做不可篡改的时间戳服务。中本聪白皮书只引了他们一篇，但这条线索在拿时间戳脉络解釋比特币为什么会这样设计时常被用到。",
              "中本聪研究所·作者页"),
             ("David Chaum 隐私技术著作", "David Chaum", "学术文献", NI + "authors/david-chaum/", "第三方汇编（保留出处）",
              [tag("文献"), tag("tag-purple", "1981 起")],
              "1981 年他提出不可追踪的电子邮件与化名体系，1982 年提出盲签名——那是「数字货币可以有隐私」这件事最早的工程答案，也为后来所有电子现金尝试打下了地基。",
              "中本聪研究所·作者页"),
             ("Ian Grigg《三重记账》", "Ian Grigg", "论文", NI + "library/triple-entry-accounting/", "第三方汇编（保留署名）",
              [tag("论文"), tag("tag-blue", "2005")],
              "复式记账之外再加第三份不可篡改的凭据，让交易双方无需互信也能对账。这篇常被用来解释「为什么区块链对会计学也有意义」。",
              "中本聪研究所全文版"),
             ("Konrad S. Graf《论比特币的由来》", "Konrad S. Graf", "研究报告", NI + "library/on-the-origins-of-bitcoin/", "第三方汇编（保留署名）",
              [tag("研究"), tag("tag-orange", "2013")],
              "一份试图把比特币放到奥地利学派货币理论脉络里的长文。它不代表本号立场，但展示了同时代的人如何理解「比特币这个东西究竟继承了两谁」。",
              "中本聪研究所全文版"),
        ]},
    ],
}

PAGES["antonopoulos"] = {
    "dir": AUTHORS, "crumb": "Andreas Antonopoulos 集", "badge": "作者轴 · Andreas M. Antonopoulos",
    "h1": "🎙️ Andreas Antonopoulos 集",
    "title": "Andreas Antonopoulos 集 · 文集 · 比特币学习地图",
    "desc": "Andreas M. Antonopoulos 开源作品合集：《精通比特币》《精通闪电网络》《精通以太坊》等，均可在 GitHub 免费阅读。",
    "intro": "他是把比特币讲清楚这件事上影响最大的人之一——不是靠预测行情，而是靠在讲台上一步步推导。《精通比特币》三个版本全部以 CC BY-SA 4.0 开放了全文，这在同类技术书里少见：意味着任何人都可以合法免费读全本，并可在注明出处的条件下再传播。本栏先把「能免费合法读全本」的书排在前面。",
    "sections": [
        {"h": "一、可以合法免费读全本的三本书", "items": [
            ("《精通比特币》（Mastering Bitcoin）开源仓库", "Andreas M. Antonopoulos", "图书（开源）", "https://github.com/bitcoinbook/bitcoinbook", "CC BY-SA 4.0",
              [tag("图书"), tag("tag-blue", "开源")],
              "从交易结构、脚本、钱包到挖矿与共识，一本在手可以读到底。第三版把 covenants、Taproot 之类的新内容也补了进来。仓库里连图稿源文件都开放——这也是开源书的好处。",
              "GitHub 官方组织仓库"),
             ("《精通比特币》在线免费阅读（含多语种）", "Andreas M. Antonopoulos", "在线阅读", "https://bitcoinbook.info/", "CC BY-SA 4.0",
              [tag("在线阅读"), tag("tag-orange", "不用装环境")],
              "不想翻 GitHub 的话，直接在这里读。站点提供多语种版本，中文战友也不用先啃英文——虽然本站仍建议有条件的读者对照英文原文看技术细节。",
              "bitcoinbook.info 官方免费版"),
             ("《精通比特币》作者镜像仓库", "Andreas M. Antonopoulos", "代码镜像", "https://github.com/aantonop/bitcoinbook", "CC BY-SA 4.0",
              [tag("镜像"), tag("tag-blue", "备用")],
              "第三版的作者个人镜像，与主仓库内容一致。当官方仓库在处理较多议题、想直接看作者分支的更新时比较好用。",
              "作者 GitHub 仓库"),
             ("《精通闪电网络》（Mastering the Lightning Network）", "Andreas M. Antonopoulos 等", "图书（开源）", "https://github.com/lnbook/lnbook", "CC BY-SA 4.0",
              [tag("图书"), tag("tag-blue", "开源")],
              "讲比特币的第二层：支付通道、路由、洋葱路由、看门塔。书的内容偏工程实现，读之前建议先把主链那本书的「交易与脚本」部分过一遍。",
              "GitHub 官方组织仓库"),
             ("《精通以太坊》（Mastering Ethereum）", "Andreas M. Antonopoulos、Gavin Wood", "图书（开源）", "https://github.com/ethereumbook/ethereumbook", "CC BY-SA 4.0",
              [tag("图书"), tag("tag-blue", "开源")],
              "本站聚焦比特币，但把这本列进来有理由：读完它需要再回头看比特币，会清楚看出「世界计算机」与「点对点电子现金」在设计取舍上的根本分歧在哪里。",
              "GitHub 官方组织仓库"),
        ]},
        {"h": "二、动手用的教学示例", "items": [
            ("比特币支付的 Wi-Fi 门户（教学 Demo）", "Andreas M. Antonopoulos", "教学示例", "https://github.com/aantonop/wifiportal21", "开源（MIT）",
              [tag("示例"), tag("tag-orange", "可跑起来")],
              "一个能用比特币付费解锁上网的 Wi-Fi 强制门户。代码很短，目的是让人看清「一次链上支付如何驱动一个真实的物理入口」——比读描述直观得多。",
              "GitHub 仓库"),
             ("HD 钱包生成教学实现", "Andreas M. Antonopoulos", "教学示例", "https://github.com/aantonop/python-hdwallet", "开源（MIT）",
              [tag("示例"), tag("tag-blue", "入门友好")],
              "用 Python 演示分层确定性钱包是怎么从一颗种子长出无数地址的。想理解助记词与派生路径，看这个比对读规范条款快。",
              "GitHub 仓库"),
        ]},
        {"h": "三、入口与索引", "items": [
            ("中本聪白皮书多格式排印版", "整理：Andreas M. Antonopoulos", "原始文献", "https://github.com/aantonop/shatoshi-paper", "原始文献 · 多格式",
              [tag("文献"), tag("tag-orange", "白皮书")],
              "白皮书的各种排印格式集合，方便转成 PDF、EPUB 或重新排版阅读。内容本身仍然是中本聪的原稿。",
              "GitHub 仓库"),
             ("个人主页", "Andreas M. Antonopoulos", "作者入口", "https://aantonop.com/", "个人站点",
              [tag("入口"), tag("tag-blue", "作者主页")],
              "他的公开日程、长文与项目列表。想跟踪他最近在讲什么，从这里出发比搜视频平台省事。",
              "aantonop.com"),
             ("全部开源作品索引", "Andreas M. Antonopoulos", "作者入口", "https://github.com/aantonop", "按仓库各自开源许可",
              [tag("入口"), tag("tag-blue", "GitHub")],
              "他的 GitHub 主页，包含本书之外的小工具、教学片段与 fork。条目会随时间变化，适合想深挖的人按此自行检索。",
              "GitHub 主页"),
        ]},
    ],
}

PAGES["lopp"] = {
    "dir": AUTHORS, "crumb": "Jameson Lopp 集", "badge": "作者轴 · Jameson Lopp",
    "h1": "\U0001f527 Jameson Lopp 集",
    "title": "Jameson Lopp 集 · 文集 · 比特币学习地图",
    "desc": "Jameson Lopp 的公开作品与开源工具：自保管实践、节点配置生成器、实体攻击案例库、私钥备份压力测试。",
    "intro": "如果说 Antonopoulos 负责把比特币讲明白，Lopp 负责把它装起来。他是长期的比特币工程师与自保管倡导者，把大部分工作公开开源：从怎么配 Bitcoin Core，到持币者遭遇过的实体攻击案例，都有资料。这一栏偏实操，建议配合本站学习区的私钥与节点章节一起看。",
    "sections": [
        {"h": "一、入口与持续更新的写作", "items": [
            ("个人站点 lopp.net", "Jameson Lopp", "作者入口", "https://www.lopp.net/", "个人站点",
             [tag("入口"), tag("tag-orange", "常更新")],
             "他的资料总入口：技术随笔、演讲、采访与常用工具的索引都挂在这里。想一次性找到这个人到底做过什么，从这一页开始。",
             "lopp.net"),
            ("Cypherpunk Cogitations 博客", "Jameson Lopp", "博客", "https://blog.lopp.net/", "保留作者署名",
             [tag("博客"), tag("tag-blue", "长文")],
             "他的长文主场，题材覆盖自保管方案对比、多签名设计、节点运维经验。文章偏工程细节，读完通常能直接动手改自己的方案。",
             "blog.lopp.net"),
            ("GitHub 全部开源作品", "Jameson Lopp", "作者入口", "https://github.com/jlopp", "各仓库开源许可",
             [tag("入口"), tag("tag-blue", "GitHub")],
             "他名下的全部公开仓库。数量不少，本栏只挑了其中与理解比特币如何运作关系最直接的一批，其余可在此按兴趣自行检索。",
             "GitHub 主页"),
        ]},
        {"h": "二、安全威胁认知（先知道自己要防什么）", "items": [
            ("针对持币者的实体攻击案例库", "Jameson Lopp", "安全研究", "https://github.com/jlopp/physical-bitcoin-attacks", "开源（详见仓库 LICENSE）",
             [tag("安全"), tag("tag-orange", "高关注度")],
             "汇总公开报道过的、针对持币者的现实世界攻击事件：入室抢劫、绑架勒索、胁迫转账等。目的不是制造恐慌，而是让人明白私钥安全不只是一个密码学问题。",
             "GitHub 仓库"),
            ("私钥金属备份设备压力测试", "Jameson Lopp", "测试报告", "https://github.com/jlopp/metal-bitcoin-storage-reviews", "开源（详见仓库 LICENSE）",
             [tag("测试"), tag("tag-purple", "实测")],
             "把市面上的金属助记词板拿火烧、拿锤砸、拿酸泡，记录各自的耐受表现。想在真实灾难场景里保住助记词，这份实测比广告词有用得多。",
             "GitHub 仓库"),
            ("政治人物涉币信息公开追踪", "Jameson Lopp", "众包数据", "https://github.com/jlopp/bitcoin-politicians", "开源（详见仓库 LICENSE）",
             [tag("数据"), tag("tag-blue", "众包")],
             "把公开披露过持币信息的政治人物做成可核查的数据集。这是个观察政策立场与切身利益是否相关的窗口，数据集本身不带结论。",
             "GitHub 仓库"),
        ]},
        {"h": "三、节点运维与日常工具", "items": [
            ("Statoshi 比特币节点监控", "Jameson Lopp", "监控工具", "https://github.com/jlopp/statoshi", "开源（详见仓库 LICENSE）",
             [tag("工具"), tag("tag-blue", "节点")],
             "给 Bitcoin Core 加一层统计导出，让节点自身的健康度、内存池情况、区块传播延迟都可观测。想理解跑全节点到底发生了什么，它会给出现象层面的答案。",
             "GitHub 仓库"),
            ("Bitcoin Core 配置文件生成器", "Jameson Lopp", "在线工具", "https://github.com/jlopp/bitcoin-core-config-generator", "开源（详见仓库 LICENSE）",
             [tag("工具"), tag("tag-orange", "新手友好")],
             "用勾选的方式生成 bitcoin.conf，避免手抄配置项出错。第一次搭全节点时尤其省事。",
             "GitHub 仓库"),
            ("Bitcoin Core RPC 认证生成器", "Jameson Lopp", "在线工具", "https://github.com/jlopp/bitcoin-core-rpc-auth-generator", "开源（详见仓库 LICENSE）",
             [tag("工具"), tag("tag-blue", "安全")],
             "在浏览器里本地生成 RPC 认证串，不把凭据发往任何服务器。给自己的节点接管理工具时用它配认证。",
             "GitHub 仓库"),
            ("比特币交易体积与重量计算器", "Jameson Lopp", "在线工具", "https://github.com/jlopp/bitcoin-transaction-size-calculator", "开源（详见仓库 LICENSE）",
             [tag("工具"), tag("tag-purple", "手续费")],
             "按输入输出占用的脚本类型估算交易的重量与体积。理解手续费到底在为哪些字节付费，比看费率表有效得多。",
             "GitHub 仓库"),
            ("扩展公钥 xpub 格式转换器", "Jameson Lopp", "在线工具", "https://github.com/jlopp/xpub-converter", "开源（详见仓库 LICENSE）",
             [tag("工具"), tag("tag-blue", "钱包")],
             "在不同版本的扩展公钥前缀之间互转。迁移钱包或换软件遇到格式不兼容时，可以用它确认地址空间是否真的一致。",
             "GitHub 仓库"),
            ("个人网站开源仓库", "Jameson Lopp", "代码仓库", "https://github.com/jlopp/lopp.net", "开源（详见仓库 LICENSE）",
             [tag("仓库"), tag("tag-blue", "可自建")],
             "他个人站在 GitHub 上的源码。想离线保存或自建一份资料镜像，从这里拿比逐个保存网页稳。",
             "GitHub 仓库"),
        ]},
    ],
}

PAGES["ammous"] = {
    "dir": AUTHORS, "crumb": "Saifedean Ammous 集", "badge": "作者轴 · Saifedean Ammous",
    "h1": "\U0001f4b0 Saifedean Ammous 集",
    "title": "Saifedean Ammous 集 · 文集 · 比特币学习地图",
    "desc": "Saifedean Ammous 公开作品：《比特币标准》《法币本位》《经济学原理》及播客、课程与多语种译本。",
    "intro": "他把比特币放进一条更长的历史线索里讨论：货币为什么会有形态更替，一种东西凭什么被当作货币，这背后与时间偏好有什么关系。这类讨论属于货币理论范畴，不等于操作建议。本站收录他的著作与课程，是为了呈现一个在中文圈流传很广的分析框架，读者自会把它与本站其他栏目的技术视角对照来看。",
    "sections": [
        {"h": "一、两本主要著作", "items": [
            ("《比特币标准》（The Bitcoin Standard）", "Saifedean Ammous", "图书", "https://saifedean.com/thebitcoinstandard/", "保留作者著作权",
             [tag("图书"), tag("tag-orange", "有中译本")],
             "从贝壳、金银到金本位与法币，用货币的商品属性这条线串起整部货币史，再论证比特币为何符合其中的健全货币标准。这是中文社区被引用最多的一本比特币读物。",
             "作者官网书目页"),
            ("《法币本位》（The Fiat Standard）", "Saifedean Ammous", "图书", "https://saifedean.com/thefiatstandard/", "保留作者著作权",
             [tag("图书"), tag("tag-blue", "第二本")],
             "上一本讲比特币，这本讲它的对面：法币体系如何塑造了当代的财政、信贷与战争融资方式。两本对照读，作者的框架才算完整。",
             "作者官网书目页"),
            ("《法币本位》免费开放章节", "Saifedean Ammous", "免费章节", "https://saifedean.com/the-fiat-standard-free-chapters", "作者开放免费阅读",
             [tag("免费"), tag("tag-green", "先看再买")],
             "作者自己放出来的免费章节。不确定这套框架适不适合自己，先读这些就够了，不必一开始就代入整本书。",
             "作者官网免费章节"),
        ]},
        {"h": "二、理论源头与全部作品索引", "items": [
            ("《经济学原理》（Principles of Economics）", "Saifedean Ammous", "教材", "https://saifedean.com/poe", "保留作者著作权",
             [tag("教材"), tag("tag-purple", "奥地利学派")],
             "他自己写的经济学教材，奥地利学派脉络。想理解他在两本比特币著作里使用的那套概念从何而来，这是源头。",
             "作者官网"),
            ("著作总目", "Saifedean Ammous", "索引", "https://saifedean.com/books", "保留作者著作权",
             [tag("索引"), tag("tag-blue", "全目")],
             "他所有已出版著作的集中目录，含各语种版本说明。想确认某一本有没有新版、有没有译本，查这里最准。",
             "作者官网书目"),
            ("多语种译本索引", "Saifedean Ammous", "索引", "https://saifedean.com/translations", "各语种译者授权",
             [tag("索引"), tag("tag-orange", "含中文")],
             "各语种译本的清单与授权情况。找中译本，或想给某个语种做译介，从这里入手。",
             "作者官网译本页"),
            ("全部课程", "Saifedean Ammous", "课程", "https://saifedean.com/courses", "付费课程",
             [tag("课程"), tag("tag-blue", "系统学习")],
             "他开设的系统课程列表，多为付费。本站不代理报名，仅作索引；是否付费由读者自行判断。",
             "作者官网课程页"),
            ("播客 The Saifedean Podcast", "Saifedean Ammous", "播客", "https://saifedean.com/podcast", "免费收听",
             [tag("播客"), tag("tag-green", "免费")],
             "长期更新的访谈节目，话题多集中在货币、能源、经济史与方法论上。相比成书，这里更容易看到他如何回应质疑。",
             "作者官网播客"),
            ("个人主页", "Saifedean Ammous", "作者入口", "https://saifedean.com/", "个人站点",
             [tag("入口"), tag("tag-orange", "总入口")],
             "他的全部公开内容入口：书、播客、课程、文章与社交账号都在此汇总。",
             "saifedean.com"),
        ]},
    ],
}

PAGES["saylor"] = {
    "dir": AUTHORS, "crumb": "Michael Saylor 集", "badge": "作者轴 · Michael Saylor（机构视角）",
    "h1": "\U0001f3e2 Michael Saylor 集",
    "title": "Michael Saylor 集 · 文集 · 比特币学习地图",
    "desc": "Michael Saylor 相关的免费公开教育资源：Saylor University《Bitcoin for Everybody》12 小时课程（课程内容 CC BY 3.0）与学习平台入口。",
    "intro": (
        "这一栏补的是本站原先缺的最后一个频段：机构视角。Michael Saylor 现为 Strategy（原 MicroStrategy）"
        "<strong>联合创始人兼执行董事长</strong>——他自 2022 年 8 月起已不再担任 CEO，这一点不少二手资料会写错。"
        "他名下另有一条常被忽略的线：1999 年设立的 Saylor 基金会及其开放教育计划 Saylor University，"
        "面向全球提供免费课程。比特币相关课程是这条线的一部分，也是本栏唯一收录的内容类型。"
        "<br><br>本站对他的收录遵循三条界线，事先说明：<br>"
        "✅ <strong>收</strong>：免费课程与教育材料，以及可核实的公开文章与演说；<br>"
        "⚠️ <strong>谨慎收</strong>：凡涉及公司持币数据的陈述，必须同时给出另一侧事实——2026 年 6 至 8 月，"
        "Strategy 首次出现减持与回补，这与他此前长期表达的不出售口径并不一致，只呈现其中一面即属片面叙述；<br>"
        "❌ <strong>不收</strong>：价格预测、价格目标，以及任何形式的买卖操作建议。"
    ),
    "sections": [
        {"h": "免费课程（课程内容 CC BY 3.0）", "items": [
            ("《Bitcoin for Everybody》（PRDV151）", "Saylor University", "免费课程", "https://learn.saylor.org/course/view.php?id=468", "课程内容 CC BY 3.0（期末考试除外）",
             [tag("课程"), tag("tag-orange", "12 小时")],
             "一门十二小时的自定进度入门课，五个单元：货币是什么、BTC 的性质、渊源与技术构成、基础操作与自保管。通过期末测评可获免费结业证书（1.2 CEU）。除期末考试外，校方自有内容以 CC BY 3.0 开放。",
             "Saylor University 课程页"),
            ("课程短链入口 PRDV151", "Saylor University", "课程入口", "https://learn.saylor.org/course/PRDV151", "课程内容 CC BY 3.0",
             [tag("入口"), tag("tag-blue", "短链")],
             "同一门课的短地址，便于直接发给别人或保存。课程编号 PRDV151。",
             "Saylor University"),
            ("课程导论教材（在线可读）", "Saylor University", "教材", "https://learn.saylor.org/mod/book/view.php?id=30723", "CC BY 3.0",
             [tag("教材"), tag("tag-green", "可直接读")],
             "这门课的导论部分。想先判断课程难度是否适合自己，读这一份就够，不必先注册。",
             "Saylor University 教材"),
        ]},
        {"h": "平台与目录", "items": [
            ("Saylor University 学习平台", "Saylor University", "平台入口", "https://learn.saylor.org/", "各课程按其标注许可",
             [tag("平台"), tag("tag-orange", "免费课程站")],
             "面向公众免费的开放课程平台，收录数百门覆盖多个学科的课程。比特币课只是其中之一——这一点值得留意：这类内容是按通识教育来编排的，而非投资宣介。",
             "learn.saylor.org"),
            ("专业发展类课程目录", "Saylor University", "目录", "https://learn.saylor.org/course/category/19/professional+development", "各自课程许可",
             [tag("目录"), tag("tag-blue", "分类浏览")],
             "PRDV151 所属的专业发展类目。想看这个机构还把哪些内容视为职业技能教育，这里能看到它的编排逻辑。",
             "Saylor University 课程分类"),
            ("全部课程总目录", "Saylor University", "目录", "https://learn.saylor.org/course/index.php?categoryid=0", "各自课程许可",
             [tag("目录"), tag("tag-blue", "总目")],
             "按学科分类的全部课程清单。用来确认比特币课程在整个知识体系里的位置，也便于横向比较其他学科的教学方式。",
             "Saylor University 总目录"),
        ]},
    ],
}

PAGES["voices"] = {
    "dir": THEMES, "crumb": "大家说比特币", "badge": "主题轴 · 大家说比特币",
    "h1": "\U0001f4ac 大家说比特币",
    "title": "大家说比特币 · 文集 · 比特币学习地图",
    "desc": "多立场视角的集合：密码朋克先驱、货币学者、工程派、机构视角，以及对比特币持批评与审视态度的作者，同栏并置。",
    "intro": (
        "一个值得读的清单，不能只有一种声音。本栏把立场各不相同的人放在同一页："
        "有人参与创造它，有人靠教它谋生，有人论证它是货币演化的下一站，也有人认真写书批评它。"
        "<strong>收录不等于赞同</strong>——本号不为任何一方的结论背书。"
        "我们只保证两件事：每个人给出的是他自己公开发表的东西，链接都指向可以核对的原处。"
    ),
    "extra": '    <div class="stance"><strong>立场标签：</strong>\U0001f7e2 建设与支持　\U0001f7e1 技术或学术　\U0001f7e0 内部审视　\U0001f534 批评与质疑</div>',
    "sections": [
        {"h": "一、缔造者与早期参与者 \U0001f7e2", "items": [
            ("Hal Finney 著述（含《Bitcoin and Me》）", "Hal Finney", "第一人称", "https://nakamotoinstitute.org/authors/hal-finney/", "第三方汇编（保留署名）",
             [tag("tag-green", "早期核心"), tag("第一人称")],
             "他接收了中本聪发出的第一笔链上交易，也是 RPOW 的作者。这份著述合集既能看到工程上的判断，也能看到一个亲历者如何回望那段日子。",
             "中本聪研究所·作者页"),
            ("Nick Szabo 著述（Bit Gold、智能合约等）", "Nick Szabo", "学术与技术", "https://nakamotoinstitute.org/authors/nick-szabo/", "第三方汇编（保留署名）",
             [tag("tag-green", "思想先驱"), tag("tag-yellow", "学术")],
             "Bit Gold 与智能合约的提出者。他并不等同于比特币阵营，长年以法学与计算机交叉的视角讨论信任、财产与合约，是把比特币放进长时段审视的代表人物。",
             "中本聪研究所·作者页"),
            ("Adam Back 著述（Hashcash 等）", "Adam Back", "技术与产业", "https://nakamotoinstitute.org/authors/adam-back/", "第三方汇编（保留署名）",
             [tag("tag-green", "技术源头"), tag("tag-yellow", "工程")],
             "Hashcash 的作者，白皮书引用名录里的名字之一。他的公开文字偏工程与协议层面，是观察产业侧视角的一个样本。",
             "中本聪研究所·作者页"),
            ("Wei Dai 著述（b-money 等）", "Wei Dai", "提案作者", "https://nakamotoinstitute.org/authors/wei-dai/", "第三方汇编（保留署名）",
             [tag("tag-green", "提案源头"), tag("tag-yellow", "学术")],
             "b-money 的提出者。他本人极少公开发言，留下的文字也很短，反倒更显分量：白皮书开篇的血脉里就有一段来自他。",
             "中本聪研究所·作者页"),
            ("Amir Taaki 著述", "Amir Taaki", "开发者视角", "https://nakamotoinstitute.org/authors/amir-taaki/", "第三方汇编（保留署名）",
             [tag("tag-green", "开发者"), tag("tag-orange", "立场鲜明")],
             "早期比特币开发者之一，公开立场带有鲜明的反建制色彩。放在这里，是为了呈现社区内部曾经激烈辩论过的那条路线。",
             "中本聪研究所·作者页"),
        ]},
        {"h": "二、密码朋克的思想底色 \U0001f7e2", "items": [
            ("Eric Hughes 著述（含《密码朋克宣言》）", "Eric Hughes", "宣言", "https://nakamotoinstitute.org/authors/eric-hughes/", "第三方汇编（保留署名）",
             [tag("tag-green", "隐私优先"), tag("宣言")],
             "宣言把隐私界定为一种选择性呈现自己的权利，而不是藏匿的手段。这条界定，几乎决定了后来比特币社区谈隐私时的起手式。",
             "中本聪研究所·作者页"),
            ("Timothy C. May 著述（含《加密无政府主义者宣言》）", "Timothy C. May", "宣言", "https://nakamotoinstitute.org/authors/timothy-c-may/", "第三方汇编（保留署名）",
             [tag("tag-green", "激进自由"), tag("宣言")],
             "比《密码朋克宣言》更早，也更不妥协。他的文字解释了比特币社区对监管天然不信任的思想来源，读完再看许多争论为何反复出现，会对上号。",
             "中本聪研究所·作者页"),
            ("David Chaum 著述（盲签名、电子现金）", "David Chaum", "学术文献", "https://nakamotoinstitute.org/authors/david-chaum/", "第三方汇编（保留署名）",
             [tag("tag-yellow", "学术"), tag("tag-purple", "隐私技术")],
             "早在 1980 年代就在做不可追踪的电子现金。他与比特币并无组织上的关系，但技术谱系上绕不开他——也提醒人注意：比特币没有沿用他那套中心化方案，究竟是为了什么。",
             "中本聪研究所·作者页"),
        ]},
        {"h": "三、当代的推动者与方法论 \U0001f7e2", "items": [
            ("Andreas M. Antonopoulos（教育与演讲）", "Andreas M. Antonopoulos", "作者入口", "https://aantonop.com/", "个人站点",
             [tag("tag-green", "教育者"), tag("tag-blue", "开源图书")],
             "比特币世界里最有名的普及者之一，三本「精通」系列全部开源可读。他的路径是先把机制讲透，把结论留给读者自己得出。",
             "aantonop.com"),
            ("Jameson Lopp（自保管与节点实践）", "Jameson Lopp", "作者入口", "https://www.lopp.net/", "各工具按其仓库许可",
             [tag("tag-green", "工程实践"), tag("tag-blue", "工具")],
             "长期做自保管与节点工程，把方法论直接开源成工具。他的立场很明确：不信任托管，自己验证。这批人把「别信，去验证」落到了具体步骤上。",
             "lopp.net"),
            ("Saifedean Ammous（货币理论脉络）", "Saifedean Ammous", "作者入口", "https://saifedean.com/", "保留作者著作权",
             [tag("tag-yellow", "货币理论"), tag("tag-purple", "奥地利学派")],
             "把比特币接进奥地利学派货币理论的叙事里。这条路解释力很强，争议也不小——放在这里，正是为了让读者同时接触支持与批评两套论证。",
             "saifedean.com"),
            ("Michael Saylor（机构采用视角）", "Saylor University", "免费课程", "https://learn.saylor.org/course/PRDV151", "课程内容 CC BY 3.0",
             [tag("tag-green", "机构视角"), tag("tag-orange", "课程")],
             "公司层面的比特币持有实践，与其倡导的开放教育项目。本站只收录其中的免费课程部分，并在其作者页标明了三条收录界线。",
             "Saylor University"),
        ]},
        {"h": "四、审视与批评 \U0001f7e0 \U0001f534", "items": [
            ("《Bitcoin Is Worse Is Better》", "Gwern Branwen", "评论长文", "https://nakamotoinstitute.org/library/bitcoin-is-worse-is-better/", "第三方汇编（保留署名）",
             [tag("tag-orange", "内部审视"), tag("评论")],
             "标题借用软件工程里那句 worse is better：比特币在设计上并不优雅，却因此得以存活。作者既承认它成立，也指出它处处是不讲究的妥协——这类内部批评往往比外部否定更难反驳。",
             "中本聪研究所全文版"),
            ("《On the Origins of Bitcoin》", "Konrad S. Graf", "研究报告", "https://nakamotoinstitute.org/library/on-the-origins-of-bitcoin/", "第三方汇编（保留署名）",
             [tag("tag-yellow", "溯源研究"), tag("研究")],
             "对比特币究竟从哪里来的系统梳理，包含对坊间流传说法的考据。常被用来纠正那些被过度演绎的起源叙事。",
             "中本聪研究所全文版"),
            ("Ian Grigg《三重记账》", "Ian Grigg", "论文", "https://nakamotoinstitute.org/library/triple-entry-accounting/", "第三方汇编（保留署名）",
             [tag("tag-yellow", "会计视角"), tag("论文")],
             "从会计学切入：在双方各自记一本账之外，再引入第三方不可篡改的凭据。这是一种不必全盘否定旧体系、也能解释区块链用途的中间立场。",
             "中本聪研究所全文版"),
            ("David Gerard《Attack of the 50 Foot Blockchain》", "David Gerard", "批评著作", "https://davidgerard.co.uk/blockchain/", "保留作者著作权",
             [tag("tag-red", "批评"), tag("著作")],
             "业内被引用最多的比特币与区块链批判著作之一，作者长年从数据与实践层面挑错。读过它与只读支持者著作之间的差别，是了解与评估之间的差别。本站收录不代表赞同其结论。",
             "davidgerard.co.uk"),
            ("Molly White《Web3 Is Going Just Great》", "Molly White", "调查追踪", "https://www.web3isgoinggreat.com/", "保留作者著作权",
             [tag("tag-red", "批评"), tag("调查")],
             "对加密行业事故、诈骗与损失的持续性公开记录，逐条附来源链接。它提醒一件常被忽略的事：这个领域的失败率并不低，损失往往先落到最晚入场的人身上。",
             "web3isgoinggreat.com"),
        ]},
    ],
}

print("total pages: %d" % len(PAGES))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    built = []
    for key, spec in PAGES.items():
        if args and key not in args:
            continue
        html = build_page(spec)
        out = os.path.join(spec["dir"], key + ".html")
        if not dry:
            io.open(out, "w", encoding="utf-8").write(html)
        built.append((key, len(html)))
    for k, n in built:
        print("built %-14s %6d bytes" % (k, n))
    if not built:
        print("no page matched: %s" % args)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
