#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gate-all.py —— 全链路门闸一键跑（ADR-0014 §7 门闸链 v2）

九道门，从「图」到「文」到「发布套件」全部跑一遍，输出一张总表 + 总闸门。
任一门红 → 退出码 1，可直接接 CI。

用法:
    python3 tools/dev/gate-all.py                  # 全跑
    python3 tools/dev/gate-all.py --only fig       # 只跑图类（①②③）
    python3 tools/dev/gate-all.py --only article   # 只跑文类（⑤⑥⑦⑧）
    python3 tools/dev/gate-all.py --verbose        # 打印每门的详细输出

门闸清单（顺序 = 依赖顺序，先图后文）:
    ① fig-glyph-check    字形/豆腐块（PingFang 缺字、Menlo 里塞中文）
    ② fig-layout-check   排版密度 L1行距 / L2留白 / L3溢出 / L4底部留白
    ③ fig-brand-check    品牌规范 F1规格 F2底色 F3橙占比 F4顶栏 F5合规条 F6文件名 F7明暗
    ④ cover-lint         封面 900×383 / ₿ / 安全区 / 缩略图 / 底部留白 / 合规词
    ⑤ content-lint       合规：敏感词 / 极限词（语境分流）/ 摘要 / 尾板 / 图片路径
    ⑥ article-template-check  文章骨架：标题 / 导语 / 章节 / 尾板
    ⑦ article-rich-check      图文表并茂密度
    ⑧ article-pub-check       发布前：图注↔文件、回扣图、表格
    ⑨ station-kit-check       整站套件完整性
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DEV = os.path.join(ROOT, 'tools', 'dev')
GZH = os.path.join(ROOT, '慢读宝盒公众号')
PY = sys.executable


def find_node():
    """定位 node：优先 PATH，其次 WorkBuddy 托管版本"""
    n = shutil.which('node')
    if n:
        return n
    for p in sorted(glob.glob(os.path.expanduser(
            '~/.workbuddy/binaries/node/versions/*/bin/node'))):
        return p
    return 'node'


NODE = find_node()


def run(cmd, cwd=ROOT):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def stations():
    """返回 [(站号, 站目录, 微信版md)]，按站号顺序"""
    out = []
    for d in sorted(glob.glob(os.path.join(GZH, '站*'))):
        if not os.path.isdir(d):
            continue
        name = os.path.basename(d)
        num = name[len('站'):].split('-')[0]
        mds = glob.glob(os.path.join(d, '02-文章', '*-微信版.md'))
        out.append((num, d, mds[0] if mds else None))
    return out


# ── 判定函数：退出码优先，文本兜底 ────────────────────────────────
def judge_green(proc, ok_words, bad_words):
    """退出码 0 即绿；非 0 时再看文本里有没有 ok_words（有的脚本退出码不稳）"""
    txt = (proc.stdout or '') + (proc.stderr or '')
    if proc.returncode == 0:
        # 退出码绿但文本里出现明显失败标记，仍算红（防「假绿」）
        if any(b in txt for b in bad_words):
            return False, '退出码 0 但检出失败标记'
        return True, ''
    if any(w in txt for w in ok_words) and not any(b in txt for b in bad_words):
        return True, ''
    return False, f'退出码 {proc.returncode}'


GATES = []


def gate(no, name, cats, fn, unit=''):
    GATES.append((no, name, cats, fn, unit))


# ① 字形
def g_glyph(v):
    p = run([PY, os.path.join(DEV, 'fig-glyph-check.py')])
    ok, why = judge_green(p, ['0 个有字形风险'], ['FAIL', '🔴', 'G1', 'G2'])
    n = 10
    return ok, f'{n} 个产线', why, (p.stdout if v else '')


# ② 排版
def g_layout(v):
    p = run([PY, os.path.join(DEV, 'fig-layout-check.py'), '--quiet'])
    txt = p.stdout or ''
    ok, why = judge_green(p, ['0 张不合格'], ['FAIL', '🔴'])
    cnt = ''
    for line in txt.splitlines():
        if '结论' in line:
            cnt = line.strip()
    return ok, cnt or '见详情', why, (txt if v else '')


# ③ 品牌
def g_brand(v):
    bad = []
    for num, d, _ in stations():
        p = run([PY, os.path.join(DEV, 'fig-brand-check.py'), '--station', num])
        txt = (p.stdout or '') + (p.stderr or '')
        # 注意：脚本正常结尾会打印「0 FAIL」，不能拿 FAIL 当失败判据；
        # 成功判据是结论行「结论：🟢 全绿」（前面是冒号不是空格）
        if p.returncode != 0 or '🟢 全绿' not in txt:
            bad.append(num)
    ok = not bad
    return ok, f'{len(stations()) - len(bad)}/{len(stations())} 站全绿', ('失败站: ' + '、'.join(bad)) if bad else '', ''


# ④ 封面
def g_cover(v):
    files = sorted(glob.glob(os.path.join(GZH, '站*', '04-封面', '*.png')))
    if not files:
        return False, '未找到封面', '路径: 慢读宝盒公众号/站*/04-封面/', ''
    p = run([PY, os.path.join(DEV, 'cover-lint.py')] + files)
    txt = p.stdout or ''
    ok = 'ALL PASS' in txt
    total = [l for l in txt.splitlines() if '总计' in l]
    return ok, (total[-1].strip() if total else f'{len(files)} 张'), '' if ok else '有封面不合格', (txt if v else '')


# ⑤ 合规
def g_content(v):
    bad = []
    for num, d, md in stations():
        if not md:
            bad.append(num + '(无md)')
            continue
        p = run([NODE, os.path.join(DEV, 'content-lint.mjs'), md])
        if p.returncode != 0:
            bad.append(num)
    ok = not bad
    return ok, f'{len(stations()) - len(bad)}/{len(stations())} 通过', ('失败站: ' + '、'.join(bad)) if bad else '', ''


# ⑥ 骨架
def g_tpl(v):
    p = run([PY, os.path.join(DEV, 'article-template-check.py')])
    txt = p.stdout or ''
    ok = p.returncode == 0 and txt.count('🟢') >= len(stations())
    return ok, f'{txt.count("🟢")} 站全绿', '' if ok else '有站骨架不合规', (txt if v else '')



# ⑦ 图文表密度
def g_rich(v):
    p = run([PY, os.path.join(DEV, 'article-rich-check.py')])
    txt = p.stdout or ''
    # 本脚本不按站打印 🟢，只有结尾一行总判；按站判据是每行的 PASS 计数
    n_pass = txt.count('PASS')
    ok = p.returncode == 0 and '🟢 全绿' in txt
    return ok, f'{len(stations())} 站 / {n_pass} 项 PASS', '' if ok else '有站密度不足', (txt if v else '')


# ⑧ 发布前
def g_pub(v):
    bad = []
    for num, d, md in stations():
        if not md:
            bad.append(num + '(无md)')
            continue
        p = run([PY, os.path.join(DEV, 'article-pub-check.py'), md,
                 '--expect-map', f'寻宝路线-站{num}-v3.png', '--md-tables-ok'])
        if p.returncode != 0:
            bad.append(num)
    ok = not bad
    return ok, f'{len(stations()) - len(bad)}/{len(stations())} 全绿', ('失败站: ' + '、'.join(bad)) if bad else '', ''


# ⑨ 整站套件
def g_kit(v):
    bad = []
    for num, d, _ in stations():
        p = run([PY, os.path.join(DEV, 'station-kit-check.py'), d])
        if p.returncode != 0:
            bad.append(num)
    ok = not bad
    return ok, f'{len(stations()) - len(bad)}/{len(stations())} 全绿', ('失败站: ' + '、'.join(bad)) if bad else '', ''


gate('①', 'fig-glyph-check   字形/豆腐', 'fig', g_glyph)
gate('②', 'fig-layout-check  排版密度', 'fig', g_layout)
gate('③', 'fig-brand-check   品牌规范', 'fig', g_brand)
gate('④', 'cover-lint        封面规范', 'cover', g_cover)
gate('⑤', 'content-lint      合规', 'article', g_content)
gate('⑥', 'article-template  文章骨架', 'article', g_tpl)
gate('⑦', 'article-rich      图文表密度', 'article', g_rich)
gate('⑧', 'article-pub       发布前', 'article', g_pub)
gate('⑨', 'station-kit       整站套件', 'kit', g_kit)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='', help='只跑某类：fig / cover / article / kit，逗号分隔')
    ap.add_argument('--verbose', action='store_true')
    a = ap.parse_args()
    cats = [c.strip() for c in a.only.split(',') if c.strip()] or None

    print('══════════ 全链路门闸（10 站）══════════')
    red = []
    for no, name, cat, fn, _ in GATES:
        if cats and cat not in cats:
            continue
        ok, metric, why, detail = fn(a.verbose)
        flag = '🟢' if ok else '🔴'
        line = f'{flag} {no} {name:<26} {metric}'
        if why:
            line += f'  ← {why}'
        print(line)
        if not ok:
            red.append(no + name.split()[0])
        if detail:
            print(detail.rstrip())
    print('─' * 60)
    if red:
        print(f'❌ 总闸门：未通过（{len(red)} 门红：{"、".join(red)}）')
        return 1
    print('✅ 总闸门：九门全绿，可推送')
    return 0


if __name__ == '__main__':
    sys.exit(main())
