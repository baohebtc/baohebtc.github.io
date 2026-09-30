#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文集新源验证器（Feature Ledger F33 / 门闸 R6 前置）

用途：把「候选外链」变成「可入白名单的已验证外链」。
纪律：HTTP 200 ≠ 有效条目。本脚本同时查四件事：

  V1 状态码 200（跟随跳转，取最终 URL）
  V2 正文非空（去标签后纯文本 ≥ MIN_TEXT 字符）
  V3 非登录墙 / 非 SPA 空壳（命中登录墙关键词即判 FAIL）
  V4 非纯占位页（文本里必须出现至少 MIN_HITS 个目标关键词，可选）

用法：
  python3 collection-verify-sources.py URL [URL ...]
  python3 collection-verify-sources.py -f 候选清单.txt     # 每行一个 URL，# 开头为注释
  python3 collection-verify-sources.py -f inbox.md --expect 比特币 bitcoin

输出：每个 URL 一行结论（PASS / FAIL + 原因），末尾给汇总。
退出码：全部 PASS = 0；有 FAIL = 1（方便 CI 或人工批量筛）。

已实测过的坑（写在这里防止重复踩）：
  - bitcoin.org / bitcointalk.org / x.com / twitter.com：本机连接失败（000），不可验证 → 不可收
  - strategy.com：403
  - www.saylor.org 子页：200 但正文只有一句口号（SPA 空壳）→ V2 拦下
  - lopp.net 子页：403 / 301 不稳
"""
import argparse
import html
import re
import sys
import urllib.request
import gzip
import io

MIN_TEXT = 200          # V2：去标签后纯文本最小长度
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# V3 强特征：命中即判 FAIL（无论正文多长）
WALL_STRONG = [
    "you must be logged in", "login required", "sign in to continue",
    "please log in", "log in to view", "log in to access",
    "authentication required", "you are not authorized",
    "access denied", "enable javascript", "you need to enable javascript",
    "just a moment", "checking your browser", "attention required",
    "您需要登录", "请先登录", "无权访问",
]

# V3 弱特征：仅在正文很短时才判 FAIL。
# 原因：Moodle（learn.saylor.org）等站点的全局导航里永远带着 "Log in"，
#       但游客照样能读正文——一刀切会把已收录的合法来源全误杀。
WALL_WEAK = ["log in", "sign in", "forbidden"]

# 游客可读标记：出现即说明「Log in」只是导航，正文是公开的
GUEST_OK = ["guest access", "you are currently using guest", "logged in as guest"]

WEAK_MIN_TEXT = 1200  # 弱特征在此长度以下才视为登录墙


def fetch(url, timeout=25):
    # 注意：不要发 Accept-Encoding: gzip —— 本机网络下带该头会在 GitHub 等站点超时
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    })
    # 本机 HTTP_PROXY 会干扰部分域；外链验证一律直连（空 ProxyHandler = 绕过环境变量代理）
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        resp = opener.open(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        return e.code, "", e.geturl()
    except Exception:
        return 0, "", url
    # 分块传输在不稳定网络下常 IncompleteRead；容错读取，拿多少算多少
    try:
        raw = resp.read()
    except Exception:
        raw = b""
        try:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                raw += chunk
        except Exception:
            pass
    if resp.headers.get("Content-Encoding") == "gzip":
        try:
            raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
        except Exception:
            pass
    return resp.status, raw.decode("utf-8", errors="ignore"), resp.geturl()


def strip_html(s):
    s = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", "", s, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def verify(url, expect=None, timeout=25):
    code, body, final = fetch(url, timeout)
    reasons = []
    if code != 200:
        return False, final, [f"V1 状态码 {code}（000=本机连不上，不可验证）"]

    text = strip_html(body)
    if len(text) < MIN_TEXT:
        return False, final, [f"V2 正文过短（{len(text)} 字符 < {MIN_TEXT}），疑为 SPA 空壳或跳转页"]

    low = text.lower()
    for w in WALL_STRONG:
        if w in low:
            return False, final, [f"V3 命中登录墙强特征：'{w}'"]
    guest = any(g in low for g in GUEST_OK)
    if not guest and len(text) < WEAK_MIN_TEXT:
        for w in WALL_WEAK:
            if w in low:
                return False, final, [f"V3 疑为登录墙（正文仅 {len(text)} 字符且含 '{w}'）"]

    if expect:
        hits = [k for k in expect if k.lower() in low]
        if not hits:
            return False, final, [f"V4 正文未命中任一预期关键词 {expect}"]
        reasons.append(f"V4 命中 {hits}")

    reasons.insert(0, f"V2 正文 {len(text)} 字符")
    reasons.insert(0, "V1 200")
    return True, final, reasons


def main():
    ap = argparse.ArgumentParser(description="文集新源验证器（R6 前置）")
    ap.add_argument("urls", nargs="*", help="候选 URL")
    ap.add_argument("-f", "--file", help="候选清单文件（每行一个 URL，# 开头为注释）")
    ap.add_argument("--expect", nargs="*", default=None, help="V4 预期关键词（出现任一即通过）")
    ap.add_argument("--timeout", type=int, default=25)
    args = ap.parse_args()

    urls = list(args.urls)
    if args.file:
        with open(args.file, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                urls.append(line)
    if not urls:
        print("用法：collection-verify-sources.py URL [URL ...] 或 -f 清单.txt", file=sys.stderr)
        return 2

    ok = fail = 0
    print("=" * 78)
    print(f"文集新源验证器  —  候选 {len(urls)} 条")
    print("=" * 78)
    for u in urls:
        good, final, reasons = verify(u, args.expect, args.timeout)
        mark = "🟢 PASS" if good else "🔴 FAIL"
        print(f"{mark}  {u}")
        if final != u:
            print(f"        跳转至：{final}")
        for r in reasons:
            print(f"        · {r}")
        ok += good
        fail += (not good)
    print("=" * 78)
    print(f"汇总：PASS {ok} / FAIL {fail}")
    print("PASS 的 URL 才可写入 collection-sources-allowlist.txt（门闸 R6 会拦未登记源）")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
