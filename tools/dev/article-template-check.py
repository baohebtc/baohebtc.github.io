#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""article-template-check.py —— 文章排版与视觉模板 v1.0 门闸（ADR-0007）

对 慢读宝盒公众号/*/02-文章/*微信版.md 逐篇检查模板 v1.0 的可程序化规则。
分级：
  MUST（退出码 1，阻塞发布）：
    M1 图注双段式「图 N：标题｜要点」
    M2 固定尾板四关键词（波动剧烈/不构成任何投资建议/盈亏自负/关注「慢读宝盒」）+ 下篇预告
    M3 正文无 Unicode ₿ (U+20BF)
    M4 图号按出现顺序连续
    M5 MD 表格数据行 >5 且无表图豁免
  SHOULD（警告，不阻塞）：
    S1 MD 表格数据行 =5（微信端可读边界，建议下版做表图）
    S2 H2 章节 <3

表图豁免规则：MD 表格上下 12 行内存在图片引用，且图 alt 与表头共享 ≥1 个
非泛词关键词（泛词表见 GENERIC）→ 视为「表有对应图」，豁免 M5/S1。

用法：
  python3 tools/dev/article-template-check.py            # 检查全部微信版
  python3 tools/dev/article-template-check.py <md路径>   # 检查单篇
退出码：0=全绿（可有警告） 1=存在 MUST 红灯
"""
import os, re, sys, glob

BASE = "/Users/mac/Desktop/宝盒知识库/比特币学习地图/慢读宝盒公众号"
GENERIC = {"维度", "对比", "区别", "模型", "示例", "说明", "内容", "项目", "类型", "代表",
           "场景", "比喻", "一共", "总结", "特点", "方式", "结果"}

TAIL_KEYWORDS = ["波动剧烈", "不构成任何投资建议", "盈亏自负", "关注「慢读宝盒」"]


def strip_comments(md):
    return re.sub(r'<!--.*?-->', '', md, flags=re.S)


def parse_tables(body_lines):
    """返回 [(起始行号, 表头list, 数据行数)]"""
    tables, cur, start = [], [], None
    for i, line in enumerate(body_lines):
        if line.strip().startswith('|'):
            if start is None:
                start = i
            cur.append(line)
        else:
            if len(cur) >= 3:
                header = [c.strip() for c in cur[0].strip('|').split('|')]
                data_rows = len(cur) - 2
                tables.append((start, header, data_rows))
            cur, start = [], None
    if len(cur) >= 3:
        header = [c.strip() for c in cur[0].strip('|').split('|')]
        tables.append((start, header, len(cur) - 2))
    return tables


def header_keys(header):
    words = set()
    for c in header:
        c = re.sub(r'（[^）]*）|\([^)]*\)', '', c).strip()
        if c and c not in GENERIC and len(c) >= 2:
            words.add(c)
            # 拆词：银行账本 → 银行/账本
            for n in (2, 3):
                if len(c) > n:
                    words.update(c[i:i+n] for i in range(len(c)-n+1))
    return {w for w in words if w not in GENERIC and len(w) >= 2}


def table_has_fig(lines, t_start, header):
    """表上下 12 行内的图片 alt 与表头共享 ≥1 关键词 → 豁免"""
    keys = header_keys(header)
    if not keys:
        return False
    lo, hi = max(0, t_start - 12), min(len(lines), t_start + 16)
    for line in lines[lo:hi]:
        m = re.search(r'!\[([^\]]*)\]', line)
        if m and any(k in m.group(1) for k in keys):
            return True
    return False


def check(md_path):
    md = open(md_path, encoding='utf-8').read()
    body = strip_comments(md)
    lines = body.split('\n')
    issues, warns = [], []

    # M1 图注双段式
    for alt in re.findall(r'!\[([^\]]*)\]', body):
        if '｜' not in alt:
            issues.append(f"M1 图注缺「｜」：{alt[:38]}")
    # M2 尾板
    for kw in TAIL_KEYWORDS:
        if kw not in body:
            issues.append(f"M2 尾板缺关键词：{kw}")
    # 终章（站9）以「连载收官」替代「下篇预告」（ADR-0013 §4.2，向后兼容）
    if '下篇预告' not in body and '连载收官' not in body:
        issues.append("M2 尾板缺收尾块（下篇预告 / 连载收官 二选一）")
    # M3 Unicode ₿
    n = body.count('₿')
    if n:
        issues.append(f"M3 正文含 Unicode ₿ x{n}（只准图形层用标准件）")
    # M4 图号连续
    nums = [int(m) for m in re.findall(r'!\[图 (\d+)：', body)]
    if nums and nums != list(range(1, len(nums) + 1)):
        issues.append(f"M4 图号不连续：{nums}")
    # M5/S1 表格
    for t_start, header, data_rows in parse_tables(lines):
        if data_rows <= 4:
            continue
        if table_has_fig(lines, t_start, header):
            continue
        (issues if data_rows > 5 else warns).append(
            f"{'M5' if data_rows > 5 else 'S1'} 表格 {data_rows} 数据行无表图豁免（第{t_start+1}行起）")
    # S2 章节
    if len(re.findall(r'^## ', body, re.M)) < 3:
        warns.append("S2 H2 章节少于 3")
    return issues, warns


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    files = args or sorted(glob.glob(os.path.join(BASE, '*/02-文章/*微信版.md')))
    fail = False
    for f in files:
        issues, warns = check(f)
        tag = os.path.basename(os.path.dirname(os.path.dirname(f)))
        if issues:
            fail = True
            print(f"🔴 {tag}: " + "; ".join(issues))
        elif warns:
            print(f"🟡 {tag}: " + "; ".join(warns))
        else:
            print(f"🟢 {tag}: 全绿")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
