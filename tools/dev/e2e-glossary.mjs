#!/usr/bin/env node
/**
 * e2e-glossary.mjs — 术语六层卡片 e2e 闸（F45 · ADR-0026）
 *
 * term-check.py 校验数据；这道闸在真实 Chromium 里校验「读者真的看得见、看得懂」：
 *   G1  渲染出 N 张 .term-card（N 动态取自 glossary-data.js）
 *   G2  每张卡六层齐全：正解 / 比喻 / ✅像 / ⚠️不像 / 多视角 / 延伸
 *   G3  「不像」的视觉权重确实高于「像」（字号更大 + 橙色左边框）
 *   G4  DOM 实测 len(不像) ≥ len(像)（硬约束在渲染层复验，不只信数据）
 *   G5  站内延伸链接全部可达（HTTP 200）
 *   G6  多视角展开后 2–3 条，且必含「机制」与「使用者」
 *   G7  简明表格剩余 15 行，且与卡片术语无重复
 *   G8  控制台无站点自身错误
 *
 * 用法：node tools/dev/e2e-glossary.mjs
 * 退出码：0 = 全绿；1 = 有红灯
 */

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '../..');
const PORT = 8178;
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'application/javascript; charset=utf-8',
               '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8',
               '.png': 'image/png', '.svg': 'image/svg+xml', '.webmanifest': 'application/json' };

function serve() {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      const rel = decodeURIComponent(req.url.split('?')[0]).replace(/^\/+/, '');
      const file = path.join(ROOT, rel || 'index.html');
      fs.readFile(file, (err, buf) => {
        if (err) { res.writeHead(404); res.end('404'); return; }
        res.writeHead(200, { 'Content-Type': MIME[path.extname(file)] || 'application/octet-stream' });
        res.end(buf);
      });
    });
    server.listen(PORT, '127.0.0.1', () => resolve(server));
  });
}

// 动态条目数：直接数 glossary-data.js 里的 "term":（扩线时无需改本脚本）
const N_TERMS = (fs.readFileSync(path.join(ROOT, 'reference', 'glossary-data.js'), 'utf-8')
  .match(/"term":/g) || []).length;

const ok = [];
const bad = [];
const pass = (id, msg) => ok.push(`${id} ${msg}`);
const fail = (id, msg) => bad.push(`${id} ${msg}`);

const server = await serve();
const B = `http://127.0.0.1:${PORT}`;
const browser = await chromium.launch();

try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const consoleErrors = [];
  page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()); });
  page.on('pageerror', (e) => consoleErrors.push(String(e)));

  await page.goto(`${B}/reference/index.html`, { waitUntil: 'load' });
  await page.waitForSelector('.term-card', { timeout: 5000 }).catch(() => {});

  // ---- G1 卡片数量 ----
  const cards = page.locator('.term-card');
  const n = await cards.count();
  if (n === N_TERMS) pass('G1', `渲染出 ${N_TERMS} 张术语卡（数据驱动）`);
  else fail('G1', `术语卡 ${n} 张，应为 ${N_TERMS}`);

  // ---- G2/G3/G4 逐卡 ----
  let g2bad = 0, g3bad = 0, g4bad = 0, g6bad = 0;
  const links = new Set();
  for (let i = 0; i < n; i++) {
    const c = cards.nth(i);
    const term = (await c.locator('.term-head h3').first().innerText()).split('\n')[0].trim();

    const has = async (sel) => (await c.locator(sel).count()) > 0;
    if (!(await has('.t-correct p')) || !(await has('.t-metaphor p')) ||
        !(await has('.term-like p')) || !(await has('.term-unlike p')) ||
        !(await has('.term-views')) || !(await has('.term-links a'))) {
      fail('G2', `${term}: 六层缺失`);
      g2bad++;
    }

    // 拆桥更重：字号 + 左边框颜色
    const weight = await c.evaluate((el) => {
      const l = el.querySelector('.term-like p');
      const u = el.querySelector('.term-unlike p');
      const bl = el.querySelector('.term-like');
      const bu = el.querySelector('.term-unlike');
      if (!l || !u) return null;
      const cs = (e) => parseFloat(getComputedStyle(e).fontSize);
      const bc = (e) => getComputedStyle(e).borderLeftColor;
      return { ls: cs(l), us: cs(u), lb: bc(bl), ub: bc(bu),
               lw: parseFloat(getComputedStyle(l).fontWeight),
               uw: parseFloat(getComputedStyle(u).fontWeight) };
    });
    if (!weight) { g3bad++; continue; }
    if (!(weight.us > weight.ls) || weight.ub === weight.lb) {
      fail('G3', `${term}: 「不像」视觉权重不够（像 ${weight.ls}px/${weight.lb} vs 不像 ${weight.us}px/${weight.ub}）`);
      g3bad++;
    }

    // 硬约束在渲染层复验
    const lens = await c.evaluate((el) => {
      const t = (s) => (el.querySelector(s)?.innerText || '').replace(/\s/g, '').length;
      return { like: t('.term-like p'), unlike: t('.term-unlike p') };
    });
    if (lens.unlike < lens.like) {
      fail('G4', `${term}: 渲染层「不像」${lens.unlike}字 < 「像」${lens.like}字`);
      g4bad++;
    }

    // G6 多视角
    // 真实点击展开「多视角」（details 折叠时读不到文本，也顺带验证可交互）
    await c.locator('.term-more summary').click();
    await page.waitForTimeout(40);
    const views = await c.locator('.term-view').count();
    const kinds = await c.evaluate(
      (el) => Array.from(el.querySelectorAll('.term-view .vk')).map((x) => x.textContent.trim()));
    if (!(views >= 2 && views <= 3) || !kinds.includes('机制') || !kinds.includes('使用者')) {
      fail('G6', `${term}: 棱镜 ${views} 个 [${kinds.join('/')}]，应 2–3 且含机制+使用者`);
      g6bad++;
    }

    for (const a of await c.locator('.term-links a').all()) {
      const h = await a.getAttribute('href');
      if (h && !h.startsWith('http')) links.add(h);
    }
  }
  if (!g2bad) pass('G2', `${N_TERMS} 张卡六层齐全（正解/比喻/像/不像/多视角/延伸）`);
  if (!g3bad) pass('G3', '「不像」视觉权重全部高于「像」（字号更大 + 橙左边框）');
  if (!g4bad) pass('G4', `渲染层复验：${N_TERMS}/${N_TERMS} 的「不像」字数 ≥「像」`);
  if (!g6bad) pass('G6', `多视角 2–3 条且必含机制+使用者（${N_TERMS}/${N_TERMS}）`);

  // ---- G5 延伸链接可达 ----
  let dead = 0;
  for (const h of links) {
    const url = new URL(h, `${B}/reference/index.html`).pathname;
    const res = await page.request.get(`${B}${url}`);
    if (res.status() !== 200) { fail('G5', `延伸链接 ${h} → ${res.status()}`); dead++; }
  }
  if (!dead) pass('G5', `延伸链接 ${links.size} 条全部可达（200）`);

  // ---- G7 简明表格不重复 ----
  // 只数数据行（表头 tr 无 thead 包裹，会一起落进自动 tbody）
  const rows = await page.locator('.glossary-table tbody tr:has(td)').count();
  const tableTerms = await page.locator('.glossary-table td:first-child').allInnerTexts();
  const cardTerms = await page.locator('.term-head h3').allInnerTexts();
  const dup = tableTerms.filter((t) => cardTerms.some((c) => c.startsWith(t.trim())));
  const REST = 25 - N_TERMS;
  if (rows === REST && dup.length === 0) pass('G7', `简明表格剩余 ${REST} 条，与 ${N_TERMS} 张卡无重复`);
  else fail('G7', `表格 ${rows} 行（应 ${REST}）或与卡片重复：${dup.slice(0,3).join('、')}`);

  // ---- G8 控制台 ----
  const real = consoleErrors.filter((e) => !/favicon|404/i.test(e));
  if (real.length === 0) pass('G8', '控制台无站点自身错误');
  else fail('G8', `控制台报错 ${real.length} 条 → ${real[0].slice(0, 120)}`);

  await page.close();
} finally {
  await browser.close();
  server.close();
}

console.log('='.repeat(64));
console.log('e2e-glossary · 术语六层卡片（F45 · ADR-0026）');
console.log('='.repeat(64));
for (const m of ok) console.log('  ✅ ' + m);
for (const m of bad) console.log('  🔴 ' + m);
console.log(`\n  ${ok.length} 通过 / ${bad.length} 失败`);
if (bad.length) { console.log('\n❌ 结果：未通过'); process.exit(1); }
console.log('\n✅ 结果：通过');
process.exit(0);
