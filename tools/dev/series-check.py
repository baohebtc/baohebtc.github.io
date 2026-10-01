#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
series-check.py —— 慢读连载栏目门闸（F42 · ADR-0025）

为什么要有这道闸：
  连载是从不被 git 跟踪的母本生成的。母本里有调研笔记、推送台账、发布备忘，
  还有「关注/点个在看/转发」这类公众号专属动作——它们一旦上线到网站就是噪音。
  另外 76 张图靠手工对齐极易漏文件、中文文件名又容易编码错位，必须机器兜底。

规则：
  S1 连载栏目与 10 篇文章页必须存在（防「说上线其实没上线」）
  S2 每张 <img> 的目标文件必须真实存在（防 404 + 中文路径编码错位）
  S3 图注「图 N」必须与图片文件名序号一致且连续
  S4 外链必须 target=_blank 且含 rel=noopener；正文不得出现占位语
  S5 合规：不得出现极限词 / 诱导交易词
  S6 尾板：必须含风险提示，且不得残留公众号专属动作词
  S7 上下篇链接闭环（首篇无上一篇、末篇无下一篇，中间篇必须两边都有）

用法：
  python3 tools/dev/series-check.py            # 全检
  python3 tools/dev/series-check.py --warn     # 只警告不计 FAIL
  python3 tools/dev/series-check.py -v         # 列出每条细节
"""
import os
import re
import sys
import glob
import html as htmllib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SERIES_DIR = os.path.join(ROOT, "series")
ASSETS_DIR = os.path.join(ROOT, "assets", "series")

# 期望的文章 slug（顺序即连载顺序）
EXPECTED_SLUGS = [
    "01-cash-bay",            # 站1 现金湾
    "01x-what-is-money",      # 站1.5 钱到底是什么
    "02-bank-fortress",       # 站2 银行堡
    "03-double-spend-gorge",  # 站3 双花峡
    "04-ledger-sea",          # 站4 账本海
    "05-hash-ridge",          # 站5 哈希岭
    "06-consensus-peak",      # 站6 共识峰
    "07-miner-valley",        # 站7 矿工谷
    "08-private-key-cliff",   # 站8 私钥崖
    "09-code-summit",         # 站9 代码之巅
]

PLACEHOLDER_TOKENS = [
    "🚧", "整理中", "敬请期待", "规划中", "即将上线", "建设中",
    "Coming soon", "coming soon", "TBD", "TODO",
]

# 公众号专属动作词：在网站语境是噪音，必须站内化
# ⚠️ 不收「转发给」——正文比喻（双花=同一份文件转发两次）合法使用，字面匹配会误伤
WX_ONLY_PHRASES = [
    "点个在看", "点击在看", "长按关注", "点击上方",
    "扫码关注", "识别二维码", "星标", "设为星标", "转发到朋友圈",
]

# 合规词分两档，豁免规则与 tools/dev/content-lint.mjs 保持同一套（别让两道闸打架）：
#   SENSITIVE 投资诱导词 —— 行内有否定/澄清语境（不是/没有/误解…）即豁免
#   EXTREME 极限词 —— R1 否定 / R2 序数 / R3 排他性技术陈述 / R4 唯一性说明
SENSITIVE_WORDS = [
    "稳赚", "保本", "翻倍", "暴涨", "抄底", "逃顶", "进场", "出货",
    "收益率", "投资回报率", "年化收益",
]
EXTREME_WORDS = [
    "最好", "最佳", "最强", "最全", "最便宜", "唯一", "国家级", "绝无仅有",
]
NEG_CTX = ["不", "不是", "≠", "并非", "别", "勿", "请勿", "没有", "无", "避免",
           "误解", "有人", "传说", "被说成", "讲成", "而非"]
NEG_NEAR = ["不", "没有", "并非", "而非", "不等于", "≠", "非绝对"]
ORDINAL = ["第一笔", "第一次", "第一步", "第一层", "第一站", "第一年", "第一批",
           "第一版", "第一节", "第一题", "第一时间", "第一个", "第一个解出"]
EXCLUSIVE = ["唯一办法", "唯一方式", "唯一途径", "唯一能"]
ONLY_SUPPORT = ["只有", "只能", "仅有"]

RISK_NOTICE_RE = re.compile(r"风险提示")

IMG_RE = re.compile(r"<img\b[^>]*>", re.I)
SRC_RE = re.compile(r'src\s*=\s*["\']([^"\']+)["\']', re.I)
ALT_RE = re.compile(r'alt\s*=\s*["\']([^"\']*)["\']', re.I)
FIGCAPTION_RE = re.compile(r"<figcaption[^>]*>(.*?)</figcaption>", re.S | re.I)
A_TAG_RE = re.compile(r"<a\b[^>]*>", re.I)
HREF_RE = re.compile(r'href\s*=\s*["\']([^"\']+)["\']', re.I)
TARGET_RE = re.compile(r'target\s*=\s*["\']([^"\']+)["\']', re.I)
REL_RE = re.compile(r'rel\s*=\s*["\']([^"\']+)["\']', re.I)
SCRIPT_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.S | re.I)
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
TAG_RE = re.compile(r"<[^>]+>")


def strip_tags(s):
    return TAG_RE.sub("", s)


def is_external(href):
    return href.startswith(("http://", "https://", "//"))


def main():
    argv = sys.argv[1:]
    warn_only = "--warn" in argv
    verbose = "-v" in argv or "--verbose" in argv

    fails = []
    warns = []

    def fail(rule, msg):
        fails.append((rule, msg))

    def warn(rule, msg):
        warns.append((rule, msg))

    # ---------- S1：文件存在性 ----------
    if not os.path.isdir(SERIES_DIR):
        fail("S1", f"连载栏目目录不存在：{SERIES_DIR}（期望由 make_series_pages.py 生成）")
        print_report(fails, warns, warn_only, verbose)
        return

    index_path = os.path.join(SERIES_DIR, "index.html")
    if not os.path.isfile(index_path):
        fail("S1", "缺少栏目首页 series/index.html")
    else:
        check_index(index_path, fail, warn, verbose)

    for i, slug in enumerate(EXPECTED_SLUGS):
        p = os.path.join(SERIES_DIR, slug + ".html")
        if not os.path.isfile(p):
            fail("S1", f"缺少连载页 series/{slug}.html")
            continue
        if verbose:
            print(f"  · 检查 series/{slug}.html")
        check_post(p, slug, i, len(EXPECTED_SLUGS), fail, warn, verbose)

    print_report(fails, warns, warn_only, verbose)


def check_index(path, fail, warn, verbose):
    raw = open(path, encoding="utf-8").read()
    body = strip_comments_scripts(raw)
    # 栏目页必须链到全部 10 篇
    for slug in EXPECTED_SLUGS:
        if f'{slug}.html' not in raw:
            fail("S1", f"栏目首页未列出 {slug}.html")
    for token in PLACEHOLDER_TOKENS:
        if token in strip_tags(body):
            fail("S4", f"series/index.html 出现占位语：{token}")
    if RISK_NOTICE_RE.search(raw) is None:
        warn("S6", "栏目首页未含风险提示（建议在页脚统一放置）")


def strip_comments_scripts(raw):
    out = COMMENT_RE.sub("", raw)
    out = SCRIPT_RE.sub("", out)
    return out


def check_post(path, slug, idx, total, fail, warn, verbose):
    raw = open(path, encoding="utf-8").read()
    body = strip_comments_scripts(raw)
    text = htmllib.unescape(strip_tags(body))

    # ---------- S2：图片文件真实存在 ----------
    figs = []
    for tag in IMG_RE.findall(body):
        m = SRC_RE.search(tag)
        if not m:
            fail("S2", f"{slug}: <img> 缺少 src")
            continue
        src = htmllib.unescape(m.group(1))
        if is_external(src) or src.startswith("data:"):
            continue
        full = os.path.normpath(os.path.join(SERIES_DIR, src))
        if not os.path.isfile(full):
            fail("S2", f"{slug}: 图片不存在 → {src}")
        else:
            figs.append((src, ALT_RE.search(tag).group(1) if ALT_RE.search(tag) else ""))
    if len(figs) == 0:
        fail("S2", f"{slug}: 未检测到任何本地配图")

    # ---------- S3：图注「图 N」与文件名序号一致且连续 ----------
    caps_html = FIGCAPTION_RE.findall(body)
    caps = [htmllib.unescape(strip_tags(c)).strip() for c in caps_html]
    if len(caps) != len(figs):
        fail("S3", f"{slug}: 图注 {len(caps)} 个 vs 图片 {len(figs)} 张，数量不等")
    else:
        for n, ((src, _alt), (cap, cap_raw)) in enumerate(zip(figs, zip(caps, caps_html)), 1):
            # 编号优先读 cap-no span（图注正文可能含「2100 万」这类数字，泛匹配会被带偏）
            cm = re.search(r'<span class="cap-no">\s*图\s*(\d+)\s*</span>', cap_raw)
            if not cm:
                cm = re.match(r"\s*图\s*(\d+)", cap)
            fm = re.search(r"(\d+)-", os.path.basename(src))
            if not cm:
                fail("S3", f"{slug}: 图注缺编号「图 N」→ {cap[:30]}")
                continue
            cn = int(cm.group(1))
            if cn != n:
                fail("S3", f"{slug}: 图注编号 {cn} ≠ 实际顺序 {n}")
            if fm and int(fm.group(1)) != n:
                fail("S3", f"{slug}: 文件名序号 {fm.group(1)} ≠ 图注编号 {cn}")

    # ---------- S4：外链规范 + 占位语 ----------
    for tag in A_TAG_RE.findall(body):
        hm = HREF_RE.search(tag)
        if not hm:
            continue
        href = htmllib.unescape(hm.group(1))
        tm = TARGET_RE.search(tag)
        rm = REL_RE.search(tag)
        if is_external(href):
            if not tm or tm.group(1) != "_blank":
                fail("S4", f"{slug}: 外链未开新标签 → {href[:60]}")
            if not rm or "noopener" not in rm.group(1):
                fail("S4", f"{slug}: 外链缺 rel=noopener → {href[:60]}")
        else:
            if tm and tm.group(1) == "_blank":
                fail("S4", f"{slug}: 站内链误加 target=_blank → {href[:60]}")

    for token in PLACEHOLDER_TOKENS:
        if token in text:
            fail("S4", f"{slug}: 出现占位语 → {token}")

    # ---------- S5：合规（语境豁免与 content-lint.mjs 同一套） ----------
    # 把 HTML 还原成「行」：块级闭合标签 / <br> 都是行边界
    lines = re.sub(r"</?(p|li|ul|ol|blockquote|h[1-6]|table|tr|div|figure)[^>]*>|\s*<br\s*/?>\s*",
                   "\n", body)
    lines = [htmllib.unescape(strip_tags(l)).strip() for l in lines.split("\n")]
    lines = [l for l in lines if l]

    def sens_exempt(line):
        return any(n in line for n in NEG_CTX)

    def extreme_exempt(word, line):
        near = ""
        i = line.find(word)
        if i >= 0:
            near = line[max(0, i - 24): i + len(word) + 24]
        if any(x in near for x in NEG_NEAR):
            return "R1 否定/澄清"
        if any(o in line for o in ORDINAL):
            return "R2 序数/时间"
        if any(e in line for e in EXCLUSIVE):
            return "R3 排他性技术陈述"
        if word == "唯一" and any(o in line for o in ONLY_SUPPORT):
            return "R4 唯一性说明"
        return None

    for w in SENSITIVE_WORDS:
        bad_lines = [l for l in lines if w in l and not sens_exempt(l)]
        for l in bad_lines:
            fail("S5", f"{slug}: 命中投资诱导词「{w}」→ …{l[:40]}…")
    for w in EXTREME_WORDS:
        for l in lines:
            if w not in l:
                continue
            # 一个词可能在同一行出现多次，逐个位置判定
            start = 0
            while True:
                i = l.find(w, start)
                if i == -1:
                    break
                seg = l[max(0, i - 24): i + len(w) + 24]
                if not extreme_exempt(w, seg) and not extreme_exempt(w, l):
                    fail("S5", f"{slug}: 命中极限词「{w}」→ …{l[max(0,i-20):i+len(w)+20]}…")
                    break
                start = i + len(w)

    # ---------- S6：尾板风险提示 + 无公众号动作词 ----------
    if RISK_NOTICE_RE.search(text) is None:
        fail("S6", f"{slug}: 缺风险提示")
    for ph in WX_ONLY_PHRASES:
        if ph in text:
            fail("S6", f"{slug}: 残留公众号专属动作词 → {ph}")

    # ---------- S7：上下篇闭环 ----------
    if idx > 0:
        prev = EXPECTED_SLUGS[idx - 1] + ".html"
        if prev not in raw:
            fail("S7", f"{slug}: 缺上一篇链接 → {prev}")
    else:
        if "上一篇" in text and re.search(r'href="[^"]*\.html"[^>]*class="[^"]*prev', raw) is None:
            pass  # 首篇允许只写「已是第一篇」
    if idx < total - 1:
        nxt = EXPECTED_SLUGS[idx + 1] + ".html"
        if nxt not in raw:
            fail("S7", f"{slug}: 缺下一篇链接 → {nxt}")


def print_report(fails, warns, warn_only, verbose):
    print("=" * 68)
    print("series-check · 慢读连载栏目门闸（F42 · ADR-0025）")
    print("=" * 68)
    if fails:
        print(f"\n❌ FAIL × {len(fails)}")
        by_rule = {}
        for rule, msg in fails:
            by_rule.setdefault(rule, []).append(msg)
        for rule in sorted(by_rule):
            items = by_rule[rule]
            print(f"\n  [{rule}] {len(items)} 项")
            for msg in items[:12 if not verbose else len(items)]:
                print(f"    · {msg}")
            if len(items) > 12 and not verbose:
                print(f"    · …… 其余 {len(items)-12} 项（-v 展开）")
    else:
        print("\n✅ 无 FAIL")

    if warns:
        print(f"\n⚠️  WARN × {len(warns)}")
        for rule, msg in warns[:10]:
            print(f"  [{rule}] {msg}")

    print()
    if fails and not warn_only:
        print("结果：未通过")
        sys.exit(1)
    print("结果：通过" if not fails else "结果：未通过（--warn 模式，未阻断）")
    sys.exit(0)


if __name__ == "__main__":
    main()
