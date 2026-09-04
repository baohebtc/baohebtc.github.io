#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
md-preview.py —— 零依赖 Markdown → 单文件 HTML 预览工具

背景：macOS 上 .md 默认无关联应用（本机未装 VS Code / Typora / Obsidian），
      双击无法打开。本工具把 md 渲染为自包含 HTML，浏览器直接打开即可阅读。

特点：
  - 零第三方依赖（仅标准库），不联网、不装包
  - 单文件 HTML，CSS 内嵌，可随意拷贝/邮件发送
  - 支持：标题/表格/列表/代码块/引用/分隔线/行内 code·粗体·斜体·链接
  - 自动跟随系统深浅色主题
  - 多文件输入时自动生成 index.html 索引页
  - 输出目录默认 out/preview/（已 gitignore）

用法：
  python3 tools/dev/md-preview.py <file.md> [file2.md ...]   # 转并自动打开
  python3 tools/dev/md-preview.py plans/2026-09-04-xxx.md    # 单个文件
  python3 tools/dev/md-preview.py --out /tmp/p a.md b.md     # 指定输出目录
  python3 tools/dev/md-preview.py --no-open a.md             # 只生成不打开

示例：
  python3 tools/dev/md-preview.py README.md plans/2026-09-04-方案E-项目文件管理规范v1.0.md
"""

import argparse
import html
import os
import re
import subprocess
import sys
import urllib.parse
from datetime import datetime

# ---------------------------------------------------------------- 行内渲染

def render_inline(text: str) -> str:
    """处理行内元素：code / 链接 / 粗体 / 斜体。顺序很重要。"""
    # 1) 先把 code span 抽出来存起来，避免里面的 * 或 [] 被后续规则误伤
    codes = []

    def stash(match):
        codes.append(match.group(1))
        return "\x00%d\x00" % (len(codes) - 1)

    text = re.sub(r'`([^`]+)`', stash, text)

    # 2) 转义 HTML 特殊字符（在插入任何标签之前）
    text = html.escape(text, quote=False)

    # 3) 链接 [标题](url)
    text = re.sub(
        r'\[([^\]]+)\]\(([^)\s]+)\)',
        lambda m: '<a href="%s">%s</a>' % (m.group(2), m.group(1)),
        text,
    )

    # 4) 粗体 **x**  /  __x__
    text = re.sub(r'\*\*([^*]+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__([^_]+?)__', r'<strong>\1</strong>', text)

    # 5) 斜体 *x* / _x_（避开已处理的 **）
    text = re.sub(r'(?<![\*\w])\*([^*\n]+?)\*(?!\*)', r'<em>\1</em>', text)
    text = re.sub(r'(?<![_\w])_([^_\n]+?)_(?!_)', r'<em>\1</em>', text)

    # 6) 还原 code span
    def restore(match):
        return '<code>%s</code>' % html.escape(codes[int(match.group(1))])

    return re.sub('\x00(\\d+)\x00', restore, text)


# ---------------------------------------------------------------- 表格

def split_row(line: str):
    line = line.strip()
    if line.startswith('|'):
        line = line[1:]
    if line.endswith('|'):
        line = line[:-1]
    return [c.strip() for c in line.split('|')]


def is_table_sep(line: str) -> bool:
    s = line.strip()
    if '|' not in s and ':' not in s:
        return False
    return bool(re.match(r'^\|?[\s:\-\|]+\|?$', s)) and '-' in s


def is_table_row(line: str) -> bool:
    s = line.strip()
    return s.startswith('|') and s.count('|') >= 1


# ---------------------------------------------------------------- 主体转换

def md_to_html(md_text: str, title: str, src_path: str) -> str:
    lines = md_text.split('\n')
    out = []
    i = 0
    n = len(lines)
    in_code = False
    code_buf = []
    code_lang = ''
    para = []

    def flush_para():
        if para:
            out.append('<p>%s</p>' % render_inline(' '.join(para).strip()))
            para.clear()

    while i < n:
        raw = lines[i]
        line = raw.rstrip()

        # ---- 代码块（优先，内部不做任何解析）
        if re.match(r'^\s*```', line):
            if in_code:
                out.append(
                    '<pre><code class="lang-%s">%s</code></pre>'
                    % (html.escape(code_lang), html.escape('\n'.join(code_buf)))
                )
                in_code = False
                code_buf = []
                code_lang = ''
            else:
                flush_para()
                in_code = True
                code_lang = line.strip()[3:].strip()
            i += 1
            continue

        if in_code:
            code_buf.append(raw)
            i += 1
            continue

        # ---- 空行
        if not line.strip():
            flush_para()
            i += 1
            continue

        # ---- 表格（需要 lookahead 判断分隔行）
        if is_table_row(line) and i + 1 < n and is_table_sep(lines[i + 1]):
            flush_para()
            header = split_row(line)
            aligns = []
            for cell in split_row(lines[i + 1]):
                c = cell.strip()
                if c.startswith(':') and c.endswith(':'):
                    aligns.append('center')
                elif c.endswith(':'):
                    aligns.append('right')
                elif c.startswith(':'):
                    aligns.append('left')
                else:
                    aligns.append('')
            i += 2
            rows = []
            while i < n and is_table_row(lines[i]):
                rows.append(split_row(lines[i]))
                i += 1
            th = ''.join(
                '<th%s>%s</th>' % (
                    ' style="text-align:%s"' % a if a else '',
                    render_inline(c),
                )
                for c, a in zip(header, aligns + [''] * len(header))
            )
            body = []
            for r in rows:
                tds = ''.join(
                    '<td%s>%s</td>' % (
                        ' style="text-align:%s"' % a if a and idx < len(aligns) else '',
                        render_inline(c if idx < len(r) else ''),
                    )
                    for idx, (c, a) in enumerate(zip(r, aligns + [''] * len(r)))
                )
                body.append('<tr>%s</tr>' % tds)
            out.append(
                '<table>\n<thead><tr>%s</tr></thead>\n<tbody>\n%s\n</tbody>\n</table>'
                % (th, '\n'.join(body))
            )
            continue

        # ---- 标题
        m = re.match(r'^(#{1,6})\s+(.*)$', line)
        if m:
            flush_para()
            lv = len(m.group(1))
            out.append('<h%d>%s</h%d>' % (lv, render_inline(m.group(2).strip()), lv))
            i += 1
            continue

        # ---- 分隔线（无 | 的 --- 才算）
        if re.match(r'^\s*([-*_])\s*\1\s*\1[\s\-*_]*$', line) and '|' not in line:
            flush_para()
            out.append('<hr>')
            i += 1
            continue

        # ---- 引用
        if re.match(r'^\s*>\s?', line):
            flush_para()
            buf = []
            while i < n and re.match(r'^\s*>\s?', lines[i]):
                buf.append(re.sub(r'^\s*>\s?', '', lines[i]))
                i += 1
            out.append('<blockquote>%s</blockquote>' % render_inline('<br>'.join(buf)))
            continue

        # ---- 列表（无序 / 有序，支持一层缩进）
        m = re.match(r'^(\s*)([-*+]|\d+[.)])\s+(.*)$', line)
        if m:
            flush_para()
            ordered = bool(re.match(r'^\d+[.)]', m.group(2)))
            tag = 'ol' if ordered else 'ul'
            items = []
            while i < n:
                mm = re.match(r'^(\s*)([-*+]|\d+[.)])\s+(.*)$', lines[i])
                if not mm:
                    # 续行（缩进且非列表项）并入上一项
                    if items and lines[i].strip() and re.match(r'^\s{2,}\S', lines[i]):
                        items[-1] += ' ' + lines[i].strip()
                        i += 1
                        continue
                    break
                cur_ordered = bool(re.match(r'^\d+[.)]', mm.group(2)))
                if cur_ordered != ordered and len(mm.group(1)) == 0:
                    break
                items.append(mm.group(3).strip())
                i += 1
            lis = ''.join('<li>%s</li>' % render_inline(it) for it in items)
            out.append('<%s>%s</%s>' % (tag, lis, tag))
            continue

        # ---- 普通段落行
        para.append(line.strip())
        i += 1

    flush_para()
    if in_code and code_buf:  # 容错：未闭合的代码块
        out.append('<pre><code>%s</code></pre>' % html.escape('\n'.join(code_buf)))

    body = '\n'.join(out)
    return PAGE_TPL % {
        'title': html.escape(title),
        'src': html.escape(src_path),
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'body': body,
    }


# ---------------------------------------------------------------- 模板

PAGE_TPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s</title>
<style>
  :root{
    --bg:#FDFBF7; --card:#FFFFFF; --text:#2A2118; --muted:#7A6E5F;
    --border:#E7DFD2; --accent:#F7931A; --accent-soft:#FDF1E3;
    --code-bg:#F5F1EA; --thead:#FBF6EE; --shadow:0 1px 3px rgba(60,45,25,.07);
  }
  @media (prefers-color-scheme: dark){
    :root{
      --bg:#0D0D0D; --card:#1A1A1A; --text:#E5E5E5; --muted:#9A9A9A;
      --border:#2E2E2E; --accent:#F7931A; --accent-soft:#2A2016;
      --code-bg:#141414; --thead:#212121; --shadow:0 1px 3px rgba(0,0,0,.4);
    }
  }
  *{box-sizing:border-box}
  body{
    margin:0; background:var(--bg); color:var(--text);
    font:16px/1.75 -apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB",
         "Microsoft YaHei","Helvetica Neue",Arial,sans-serif;
    -webkit-font-smoothing:antialiased;
  }
  .bar{
    position:sticky; top:0; z-index:9; background:var(--card);
    border-bottom:1px solid var(--border); box-shadow:var(--shadow);
    padding:10px 20px; font-size:13px; color:var(--muted);
    display:flex; gap:10px; align-items:center; flex-wrap:wrap;
  }
  .bar .dot{width:8px;height:8px;border-radius:50%%;background:var(--accent);flex:none}
  .bar .name{color:var(--text);font-weight:600;font-size:14px}
  .bar code{background:var(--code-bg);padding:2px 7px;border-radius:5px;
    font-size:12px;border:1px solid var(--border);word-break:break-all}
  .wrap{max-width:900px; margin:0 auto; padding:36px 24px 96px}
  h1,h2,h3,h4,h5,h6{line-height:1.35; margin:1.8em 0 .7em; font-weight:650}
  h1{font-size:1.9em; margin-top:0; padding-bottom:.45em; border-bottom:2px solid var(--accent)}
  h2{font-size:1.42em; padding-left:.6em; border-left:4px solid var(--accent)}
  h3{font-size:1.16em; color:var(--accent)}
  h4{font-size:1.02em; color:var(--muted)}
  p{margin:.85em 0}
  a{color:var(--accent); text-decoration:none; border-bottom:1px solid rgba(247,147,26,.32)}
  a:hover{border-bottom-color:var(--accent)}
  strong{font-weight:650; color:var(--text)}
  em{color:var(--muted)}
  ul,ol{margin:.85em 0; padding-left:1.6em}
  li{margin:.32em 0}
  code{
    background:var(--code-bg); padding:.16em .42em; border-radius:5px;
    font:13px/1.6 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
    border:1px solid var(--border);
  }
  pre{
    background:var(--code-bg); border:1px solid var(--border);
    border-radius:10px; padding:14px 16px; overflow-x:auto; margin:1.1em 0;
  }
  pre code{background:none;border:none;padding:0;font-size:13px;line-height:1.65}
  blockquote{
    margin:1.1em 0; padding:.7em 1.1em; background:var(--accent-soft);
    border-left:4px solid var(--accent); border-radius:0 8px 8px 0; color:var(--text);
  }
  blockquote p{margin:.3em 0}
  hr{border:none; border-top:1px solid var(--border); margin:2em 0}
  table{
    width:100%%; border-collapse:collapse; margin:1.2em 0; font-size:14.5px;
    background:var(--card); border:1px solid var(--border); border-radius:10px;
    overflow:hidden; display:block; overflow-x:auto;
  }
  th,td{padding:10px 13px; border-bottom:1px solid var(--border); text-align:left; vertical-align:top}
  thead th{background:var(--thead); font-weight:650; white-space:nowrap; border-bottom:2px solid var(--accent)}
  tbody tr:last-child td{border-bottom:none}
  tbody tr:hover{background:var(--accent-soft)}
  @media (max-width:600px){ .wrap{padding:24px 15px 72px} h1{font-size:1.5em} }
</style>
</head>
<body>
  <div class="bar">
    <span class="dot"></span>
    <span class="name">%(title)s</span>
    <span>源文件</span><code>%(src)s</code>
    <span style="margin-left:auto">渲染于 %(date)s</span>
  </div>
  <div class="wrap">
%(body)s
  </div>
</body>
</html>
"""

INDEX_TPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Markdown 预览索引</title>
<style>
  :root{--bg:#FDFBF7;--card:#FFF;--text:#2A2118;--muted:#7A6E5F;--border:#E7DFD2;
        --accent:#F7931A;--accent-soft:#FDF1E3}
  @media (prefers-color-scheme: dark){
    :root{--bg:#0D0D0D;--card:#1A1A1A;--text:#E5E5E5;--muted:#9A9A9A;
          --border:#2E2E2E;--accent:#F7931A;--accent-soft:#2A2016}
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--text);
    font:16px/1.7 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}
  .wrap{max-width:860px;margin:0 auto;padding:44px 24px 80px}
  h1{font-size:1.7em;padding-bottom:.4em;border-bottom:2px solid var(--accent);margin-top:0}
  .sub{color:var(--muted);font-size:14px;margin:.6em 0 2em}
  ul{list-style:none;padding:0;margin:0}
  li{margin:0 0 12px}
  a{display:block;padding:15px 18px;background:var(--card);border:1px solid var(--border);
    border-radius:11px;text-decoration:none;color:var(--text);transition:.15s}
  a:hover{border-color:var(--accent);background:var(--accent-soft);transform:translateY(-1px)}
  .t{font-weight:650;font-size:15.5px}
  .p{color:var(--muted);font-size:12.5px;margin-top:5px;
    font-family:ui-monospace,Menlo,monospace;word-break:break-all}
  .tip{margin-top:32px;padding:14px 18px;background:var(--accent-soft);
    border-left:4px solid var(--accent);border-radius:0 9px 9px 0;font-size:14px}
  code{background:rgba(247,147,26,.13);padding:2px 6px;border-radius:5px;font-size:13px}
</style>
</head>
<body><div class="wrap">
  <h1>📄 Markdown 预览索引</h1>
  <p class="sub">共 %(count)d 个文档 · 渲染于 %(date)s · 点击标题用浏览器打开阅读</p>
  <ul>%(items)s</ul>
  <div class="tip">
    <strong>为什么有这个页面？</strong> macOS 上 <code>.md</code> 默认没有关联应用
    （本机未装 VS Code / Typora / Obsidian），双击打不开。
    本工具把 md 渲染成 HTML，浏览器可直接阅读。
    重新生成：<code>python3 tools/dev/md-preview.py 文件.md</code>
  </div>
</div></body></html>
"""


# ---------------------------------------------------------------- 主流程

def write_file(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def main():
    ap = argparse.ArgumentParser(
        description='零依赖 Markdown → HTML 预览（解决 macOS 双击 md 打不开）'
    )
    ap.add_argument('files', nargs='+', help='一个或多个 .md 文件')
    ap.add_argument('-o', '--out', default=None, help='输出目录，默认 <仓库根>/out/preview')
    ap.add_argument('--no-open', action='store_true', help='只生成，不自动打开')
    args = ap.parse_args()

    # 仓库根推断：tools/dev/xxx.py → 上两级
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out_dir = args.out or os.path.join(repo_root, 'out', 'preview')

    made = []
    for f in args.files:
        f = os.path.abspath(f)
        if not os.path.exists(f):
            print('  ⚠️  跳过（不存在）: %s' % f)
            continue
        with open(f, encoding='utf-8') as fh:
            md = fh.read()
        name = os.path.splitext(os.path.basename(f))[0]
        # 相对路径展示，便于用户知道文件在哪
        try:
            rel = os.path.relpath(f, repo_root)
        except ValueError:
            rel = f
        out_html = os.path.join(out_dir, name + '.html')
        write_file(out_html, md_to_html(md, name, rel))
        made.append((name, rel, out_html))
        print('  ✅ %-46s → %s' % (rel, os.path.relpath(out_html, repo_root)))

    if not made:
        print('没有生成任何文件。')
        return 1

    # 索引页
    if len(made) > 1:
        items = ''.join(
            '<li><a href="%s"><div class="t">%s</div><div class="p">%s</div></a></li>'
            % (urllib.parse.quote(os.path.basename(h)), html.escape(t), html.escape(r))
            for t, r, h in made
        )
        idx = os.path.join(out_dir, 'index.html')
        write_file(idx, INDEX_TPL % {
            'count': len(made),
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'items': items,
        })
        print('  📇 索引页 → %s' % os.path.relpath(idx, repo_root))
        target = idx
    else:
        target = made[0][2]

    print('\n输出目录: %s' % out_dir)

    if not args.no_open:
        try:
            subprocess.run(['open', target], check=False)
            print('已在默认浏览器打开：%s' % os.path.basename(target))
        except Exception as e:
            print('自动打开失败（可手动双击 html）：%s' % e)

    return 0


if __name__ == '__main__':
    sys.exit(main())
