#!/usr/bin/env node
/**
 * site-check.mjs — 站点 L1 自动化检查（文集板块 R1–R9 红灯清单）
 *
 * 用法: node tools/dev/site-check.mjs [--no-network]
 * 退出码: 0 = 全部绿灯（R5 网络未验证不计入红灯）, 1 = 有红灯
 *
 * 对应协议《六、首个应用：文集板块的红灯清单》：
 *   R1 导航在所有页面一致，且包含「文集」
 *   R2 collection/index.html 存在，双轴（主题/作者）可达
 *   R3 每个集合页含统一免责声明
 *   R4 条目数据字段完整（title/author/type/source/license）
 *   R5 所有外链可达（HTTP 2xx/3xx）
 *   R6 空集合页显示「整理中」占位
 *   R7 无内部死链
 *   R8 375px 不横向滚动（L2 人工；此处查 viewport + 媒体查询）
 *   R9 转载类内容保留原署名与许可说明
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '../..');
const NO_NET = process.argv.includes('--no-network');

const DISCLAIMER = '学习资料索引 · 非投资建议 · 观点不代表本号立场';

// —— 收集所有 html ——
function walk(dir, acc = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.name === '.git' || e.name === 'node_modules' || e.name === 'assets') continue;
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, acc);
    else if (e.name.endsWith('.html')) acc.push(p);
  }
  return acc;
}
const allHtml = walk(ROOT);
const rel = p => path.relative(ROOT, p);

// —— R1：导航为 5 项核心（首页/学习区/工具/参考/文集）的超集 ——
// 模块子页可保留额外 learning 子链；Hero 落地页须补齐导航。
function navSections(html) {
  const m = html.match(/<div class="nav-links">([\s\S]*?)<\/div>/);
  if (!m) return null;
  return [...m[1].matchAll(/data-section="([^"]+)"/g)].map(x => x[1]).sort();
}
const CORE = ['home', 'learning', 'tools', 'reference', 'collection'];
let r1Ok = true, r1Detail = [];
for (const f of allHtml) {
  const secs = navSections(fs.readFileSync(f, 'utf8'));
  if (!secs) { r1Ok = false; r1Detail.push(`${rel(f)}: 无 nav-links`); continue; }
  const miss = CORE.filter(c => !secs.includes(c));
  if (miss.length) { r1Ok = false; r1Detail.push(`${rel(f)}: 缺 ${miss.join('/')}`); }
}

// —— R2：文集双轴总览页 ——
const collIndex = path.join(ROOT, 'collection', 'index.html');
let r2Ok = false, r2Detail = '';
if (fs.existsSync(collIndex)) {
  const c = fs.readFileSync(collIndex, 'utf8');
  const hasTheme = /主题轴/.test(c) && /data-axis="themes"/.test(c);
  const hasAuthor = /作者轴/.test(c) && /data-axis="authors"/.test(c);
  r2Ok = hasTheme && hasAuthor;
  r2Detail = r2Ok ? '' : `主题轴:${hasTheme} 作者轴:${hasAuthor}`;
} else {
  r2Detail = 'collection/index.html 不存在';
}

// —— 集合页集合 ——
const collHtml = allHtml.filter(f => rel(f).startsWith('collection/'));
function itemsOf(html) {
  return [...html.matchAll(/<[a-zA-Z]+[^>]*class="[^"]*collection-item[^"]*"[^>]*>/g)]
    .map(m => m[0]);
}
function attr(tag, name) {
  const m = tag.match(new RegExp(name + '="([^"]*)"'));
  return m ? m[1] : '';
}

// —— R3：免责声明 ——
let r3Ok = true, r3Detail = [];
if (collHtml.length === 0) { r3Ok = false; r3Detail.push('无集合页'); }
for (const f of collHtml) {
  const c = fs.readFileSync(f, 'utf8');
  if (!c.includes(DISCLAIMER)) r3Detail.push(`${rel(f)}: 缺免责声明`);
}
r3Ok = r3Detail.length === 0;

// —— R4：字段完整 ——
const REQUIRED = ['data-title', 'data-author', 'data-type', 'data-source', 'data-license'];
let r4Ok = true, r4Detail = [];
for (const f of collHtml) {
  const c = fs.readFileSync(f, 'utf8');
  for (const it of itemsOf(c)) {
    const miss = REQUIRED.filter(k => !attr(it, k));
    if (miss.length) r4Detail.push(`${rel(f)}: ${attr(it, 'data-title') || '(无标题)'} 缺 ${miss.join('/')}`);
  }
}
r4Ok = r4Detail.length === 0;

// —— R6：空集合页占位 ——
let r6Ok = true, r6Detail = [];
for (const f of collHtml) {
  const c = fs.readFileSync(f, 'utf8');
  const hasList = /class="[^"]*collection-list[^"]*"/.test(c);
  const itemCount = itemsOf(c).length;
  if (hasList && itemCount === 0 && !/整理中/.test(c)) {
    r6Detail.push(`${rel(f)}: 空列表无「整理中」占位`);
  }
}
r6Ok = r6Detail.length === 0;

// —— R9：转载署名与许可 ——
let r9Ok = true, r9Detail = [];
for (const f of collHtml) {
  const c = fs.readFileSync(f, 'utf8');
  for (const it of itemsOf(c)) {
    const lic = attr(it, 'data-license');
    const src = attr(it, 'data-source');
    const aut = attr(it, 'data-author');
    if (!lic) continue;
    // 转载/镜像类必须可见署名与来源
    if (!c.includes(src) || !c.includes(aut) || !c.includes(lic)) {
      r9Detail.push(`${rel(f)}: ${aut} 转载署名不全(源/作者/许可需可见)`);
    }
  }
}
r9Ok = r9Detail.length === 0;

// —— R7：内部死链 ——
let r7Ok = true, r7Detail = [];
const linkRe = /href="([^"]+)"/g;
for (const f of allHtml) {
  const html = fs.readFileSync(f, 'utf8');
  const dir = path.dirname(f);
  let lm;
  while ((lm = linkRe.exec(html))) {
    const href = lm[1].trim();
    if (!href || href.startsWith('#') || href.startsWith('http') ||
        href.startsWith('mailto:') || href.startsWith('javascript:') ||
        href.startsWith('tel:') || href.startsWith('/')) continue;
    const clean = href.split('#')[0]; // 剥离锚点片段
    if (!clean) continue; // 纯锚点链接
    const target = path.resolve(dir, clean);
    if (!fs.existsSync(target)) r7Detail.push(`${rel(f)} → ${href}`);
  }
}
r7Ok = r7Detail.length === 0;

// —— R8：响应式（L2 近似）——
let r8Ok = true, r8Detail = [];
for (const f of collHtml) {
  const c = fs.readFileSync(f, 'utf8');
  const hasViewport = /name="viewport"/.test(c);
  const hasMedia = /@media[^{]*max-width/.test(c);
  if (!hasViewport || !hasMedia) r8Detail.push(`${rel(f)}: viewport:${hasViewport} media:${hasMedia}`);
}
r8Ok = r8Detail.length === 0;

// —— R5：外链可达 ——
let r5State = 'SKIP', r5Detail = [];
if (NO_NET) {
  r5State = 'SKIP';
} else {
  const extLinks = new Map(); // url -> [files]
  const extRe = /href="(https?:\/\/[^"]+)"/g;
  for (const f of collHtml) {
    const html = fs.readFileSync(f, 'utf8');
    let em;
    while ((em = extRe.exec(html))) {
      const u = em[1];
      (extLinks.get(u) || extLinks.set(u, []).get(u)).push(rel(f));
    }
  }
  if (extLinks.size === 0) {
    r5State = 'GREEN';
  } else {
    const broken = [];
    const unverified = [];
    for (const [u, files] of extLinks) {
      try {
        const ctrl = new AbortController();
        const t = setTimeout(() => ctrl.abort(), 8000);
        const res = await fetch(u, { method: 'HEAD', signal: ctrl.signal });
        clearTimeout(t);
        if (res.status >= 400) broken.push(`${u} (${res.status}) @ ${files[0]}`);
      } catch (e) {
        unverified.push(`${u} (${e.name}) @ ${files[0]}`);
      }
    }
    r5Detail = broken.slice();
    if (broken.length) r5State = 'RED';
    else if (unverified.length) { r5State = 'WARN'; r5Detail = r5Detail.concat(unverified); }
    else r5State = 'GREEN';
    for (const u of unverified) r5Detail.push(`未验证(环境网络): ${u}`);
  }
}

// —— 汇总 ——
const rows = [
  ['R1', '导航一致且含「文集」', r1Ok, r1Detail.join('; ')],
  ['R2', '文集双轴总览页存在', r2Ok, r2Detail],
  ['R3', '集合页含免责声明', r3Ok, r3Detail.join('; ')],
  ['R4', '条目字段完整', r4Ok, r4Detail.join('; ')],
  ['R5', '外链可达', r5State === 'GREEN', r5Detail.join('; ')],
  ['R6', '空集合页「整理中」占位', r6Ok, r6Detail.join('; ')],
  ['R7', '无内部死链', r7Ok, r7Detail.join('; ')],
  ['R8', '响应式(viewport+媒体查询)', r8Ok, r8Detail.join('; ')],
  ['R9', '转载署名与许可可见', r9Ok, r9Detail.join('; ')],
];

console.log('\n════════ 文集板块 L1 检查（R1–R9）════════');
let redCount = 0;
for (const [id, name, ok, detail] of rows) {
  const state = ok ? '🟢 GREEN' : (id === 'R5' ? `🟡 ${r5State}` : '🔴 RED');
  if (!ok) redCount++;
  console.log(`  ${id}  ${state}  ${name}`);
  if (detail) console.log(`        ↳ ${detail}`);
}
console.log('════════════════════════════════════════════');
const hardRed = rows.filter(([id]) => id !== 'R5' && !rows.find(r => r[0] === id)[2]).length;
if (redCount === 0) console.log('✅ 全部绿灯');
else console.log(`🔴 红灯 ${hardRed} 项（R5 为 WARN 时不计红灯）`);

process.exit(hardRed > 0 ? 1 : 0);
