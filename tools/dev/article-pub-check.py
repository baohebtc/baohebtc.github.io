#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
article-pub-check.py — 微信版文章发布闸（L1.5，content-lint 之外的人工陷阱层）

为什么存在：content-lint 只查文字合规，查不出这三类「发出去才是事故」的问题——
  1. 配图过时（如旧 9 站地图 vs 已上线的 10 站 v3.3，品牌割裂）
  2. Markdown 表格声称「已存为配图」但图实际不存在（微信后台不认 MD 表 → 乱码）
  3. 发布配置块里的封面/摘要与正文实际不符

用法:
  python3 tools/dev/article-pub-check.py <微信版.md> [--expect-map 新地图文件名] [--expect-figs 图1,图2,...]

退出码: 0 = 全绿, 1 = 有红灯
"""
import argparse, os, re, sys
from pathlib import Path

def fail(msgs, m):
    msgs.append(m)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('md')
    ap.add_argument('--expect-map', default=None,
                    help='回扣地图图应使用的文件名（防旧图复活）')
    ap.add_argument('--stale-words', default='9 站学习地图,九站学习地图',
                    help='过时话术（逗号分隔，命中即红）')
    ap.add_argument('--table-figs', default='',
                    help='表格配图显式映射，如 "T1=02-bank-vs-btc.png,T2=06-t2-utxo-table.png"'
                         '（T 编号表在微信端必须以图呈现，MD 表会乱码）')
    ap.add_argument('--md-tables-ok', action='store_true',
                    help='豁免：本管线 wechat_push 会把 MD 表渲染为带内联样式 HTML 表'
                         '（已有草稿箱实证），跳过强制配图要求')
    args = ap.parse_args()

    md_path = Path(args.md).resolve()
    if not md_path.exists():
        print(f'❌ 文件不存在: {md_path}'); sys.exit(2)
    s = md_path.read_text(encoding='utf-8')
    base = md_path.parent
    ok, bad = [], []

    # 1. 发布配置块
    if re.search(r'<!--\s*发布配置', s):
        ok.append('发布配置块存在')
    else:
        fail(bad, '缺「发布配置」块（标题/封面/摘要）')

    # 2. 过时话术
    for w in [x for x in args.stale_words.split(',') if x]:
        if w in s:
            fail(bad, f'过时话术「{w}」仍在正文（地图资产已升级，需同步）')
    if not any(w in s for w in args.stale_words.split(',') if w):
        ok.append('无过时地图话术')

    # 3. 图片引用存在 + 收集
    refs = re.findall(r'!\[[^\]]*\]\(([^)]+)\)', s)
    missing = []
    names = []
    for rel in refs:
        p = (base / rel).resolve()
        names.append(Path(rel).name)
        if not p.exists():
            missing.append(rel)
    if missing:
        for m in missing: fail(bad, f'图片缺失: {m}')
    else:
        ok.append(f'正文 {len(refs)} 张图片全部存在')

    # 4. 回扣地图必须是新版（文件名含「地图回扣」或 map-figure；排除 mindmap）
    if args.expect_map:
        map_refs = [n for n in names
                    if ('map' in n.lower() or '地图回扣' in n or '寻宝路线' in n) and 'mindmap' not in n.lower()]
        if not map_refs:
            fail(bad, '未找到回扣地图引用（map-figure）')
        elif args.expect_map not in map_refs:
            fail(bad, f'回扣地图用了 {map_refs}，应为 {args.expect_map}（旧图/缺失）')
        else:
            ok.append(f'回扣地图已指向新版 {args.expect_map}')
        # 地图必须是 v3 品牌规格：4:3 横版 1200×900（矢量寻宝路线图，ADR-0004）
        for n in map_refs:
            for rel in refs:
                if Path(rel).name == n:
                    from PIL import Image
                    im = Image.open((base / rel).resolve())
                    if im.size != (1200, 900):
                        fail(bad, f'回扣地图 {n} 是 {im.size}，应为 4:3 横版 1200×900（make_route_fig 产出）')
                    else:
                        ok.append(f'回扣地图 {n} 4:3 横版 {im.size}')

    # 5. 表格配图核对（显式映射：T编号=文件名；或 --md-tables-ok 豁免）
    tables = sorted(set(re.findall(r'\*\*(T\d+)\s*[·•]', s)))
    if tables and not args.md_tables_ok:
        if not args.table_figs:
            fail(bad, f'文中 {len(tables)} 张 MD 表（{"、".join(tables)}）'
                      f'但未声明 --table-figs 映射——微信端将乱码')
        else:
            tmap = dict(x.split('=', 1) for x in args.table_figs.split(',') if '=' in x)
            for t in tables:
                if t not in tmap:
                    fail(bad, f'{t} 未在 --table-figs 声明配图')
                    continue
                fig = tmap[t]
                if fig not in names:
                    fail(bad, f'{t} 的配图 {fig} 未被正文引用')
                elif not (base / next(r for r in refs if Path(r).name == fig)).resolve().exists():
                    fail(bad, f'{t} 的配图 {fig} 文件不存在')
                else:
                    ok.append(f'{t} 表配图就位：{fig}')

    # 6. 尾板与下篇预告
    if '不构成任何投资建议' in s: ok.append('风险提示尾板在')
    else: fail(bad, '缺风险提示尾板')
    if '下篇预告' in s: ok.append('下篇预告在')
    else: fail(bad, '缺下篇预告')

    print('──────── 发布闸结果 ────────')
    for o in ok: print('  🟢', o)
    for b in bad: print('  🔴', b)
    print(f'—— {"✅ 全绿" if not bad else f"❌ {len(bad)} 项红灯"}')
    sys.exit(1 if bad else 0)

if __name__ == '__main__':
    main()
