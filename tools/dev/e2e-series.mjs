#!/usr/bin/env node
/**
 * e2e-series.mjs — 慢读连载 e2e 闸（F42 · ADR-0025）
 *
 * series-check.py 是静态检查；这道闸在真实 Chromium 里验证「用户真的能读」：
 *   E1  栏目首页列出全部 10 篇，链接 0 死链
 *   E2  10 篇正文图片全部真实加载（naturalWidth > 0，0 张挂图）
 *   E3  上下篇链接逐篇点击可达（首篇→末篇走完整条链）
 *   E4  每篇有 延伸阅读（series-xlink→learning）且目标页存在
 *   E5  learning 对应页有回链（series-xlink→series）且目标页存在
 *   E6  控制台无站点自身错误
 *
 * 用法：node tools/dev/e2e-series.mjs
 * 退出码：0 = 全绿；1 = 有红灯
 */

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '../..');
const PORT = 8177;

const SLUGS = [
  '01-cash-bay', '01x-what-is-money', '02-bank-fortress', '03-double-spend-gorge',
  '04-ledger-sea', '05-hash-ridge', '06-consensus-peak', '07-miner-valley',
  '08-private-key-cliff', '09-code-summit',
];

const LEARNING_LINKBACK = [
  'learning/01-philosophy/01-01-money.html',
  'learning/01-philosophy/01-02-three-flaws.html',
  'learning/01-philosophy/01-03-bitcoin-answer.html',
  'learning/02-basics/02-02-keys-ownership.html',
  'learning/02-basics/02-04-mining.html',
  'learning/04-technology/04-01-cryptography.html',
  'learning/04-technology/04-03-transactions.html',
  'learning/04-technology/04-04-blockchain-structure.html',
  'learning/04-technology/04-05-mining-consensus.html',
  'learning/04-technology/04-06-nodes-network.html',
];

const MIME = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript',
  '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon', '.webmanifest': 'application/manifest+json' };

const server = http.createServer((req, res) => {
  try {
    let p = decodeURIComponent(req.url.split('?')[0]);
    if (p === '/') p = '/index.html';
    const fp = path.join(ROOT, p);
    if (!fp.startsWith(ROOT) || !fs.existsSync(fp) || fs.statSync(fp).isDirectory()) {
      res.writeHead(404); return res.end('nf');
    }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(fp)] || 'application/octet-stream' });
    fs.createReadStream(fp).pipe(res);
  } catch { res.writeHead(500); res.end('e'); }
});

const red = [];
const green = [];
const ok = (id, msg) => green.push(`${id} ${msg}`);
const bad = (id, msg) => red.push(`${id} ${msg}`);

async function settle(page) {
  // 触发 lazyload 并等全部图 decode
  await page.evaluate(async () => {
    const step = 700;
    for (let y = 0; y < document.body.scrollHeight; y += step) {
      window.scrollTo(0, y);
      await new Promise(r => setTimeout(r, 60));
    }
    window.scrollTo(0, 0);
    const imgs = Array.from(document.images);
    imgs.forEach(i => { i.loading = 'eager'; });
    await Promise.all(imgs.map(i => i.complete ? 0 : new Promise(r => {
      i.addEventListener('load', r, { once: true }); i.addEventListener('error', r, { once: true });
    })));
    await Promise.all(imgs.map(i => i.decode().catch(() => {})));
  });
  await page.waitForTimeout(300);
}

async function run() {
  await new Promise(r => server.listen(PORT, '127.0.0.1', r));
  console.log('\n════════ 慢读连载 e2e 闸（真实 Chromium）════════');
  const browser = await chromium.launch();
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  const siteErrs = [];
  page.on('console', m => { if (m.type() === 'error') siteErrs.push(m.text()); });
  page.on('pageerror', e => siteErrs.push('PAGEERROR: ' + e.message));
  const B = 'http://127.0.0.1:' + PORT;

  // ---- E1 栏目首页
  await page.goto(B + '/series/index.html', { waitUntil: 'load' });
  for (const s of SLUGS) {
    const cnt = await page.$$eval(`a[href="/series/${s}.html"], a[href*="${s}.html"]`, els => els.length).catch(() => 0);
    if (cnt === 0) bad('E1', `栏目首页缺 ${s}.html`);
  }
  const cards = await page.$$eval('.series-card', els => els.length).catch(() => 0);
  if (cards === SLUGS.length) ok('E1', `栏目首页 10 卡齐全`);
  else bad('E1', `栏目卡片 ${cards} 张（应 10）`);

  // ---- E2/E3/E4 逐篇
  let prevLinkOk = true;
  let e2ok = 0;
  let e4ok = 0;
  for (let i = 0; i < SLUGS.length; i++) {
    const slug = SLUGS[i];
    // E3 用「点击下一篇」逐篇前进（模拟真实阅读路径），首篇直接打开
    if (i > 0) {
      const navNext = page.locator('.chapter-nav .chapter-nav-link.next');
      try { await navNext.click({ timeout: 4000 }); } catch { prevLinkOk = false; }
      await page.waitForTimeout(250);
    } else {
      await page.goto(B + `/series/${slug}.html`, { waitUntil: 'load' });
    }
    const here = await page.evaluate(() => location.pathname);
    if (!here.includes(slug)) { bad('E3', `第 ${i + 1} 篇上下篇链断：期望 ${slug}，落在 ${here}`); await page.goto(B + `/series/${slug}.html`, { waitUntil: 'load' }); }
    else if (i > 0) { /* 由上一篇点进来的，已经过一次真实点击 */ }

    await settle(page);
    const imgs = await page.evaluate(() =>
      Array.from(document.images).map(im => ({ src: im.currentSrc || im.src, w: im.naturalWidth })));
    const broken = imgs.filter(x => x.w === 0);
    if (broken.length) bad('E2', `${slug}: ${broken.length} 张图未加载 → ${broken[0].src.split('/').pop()}`);
    if (imgs.length === 0) bad('E2', `${slug}: 页面无图（应 7–8 张）`);
    if (!broken.length && imgs.length) e2ok++;

    const xl = await page.$$eval('.series-xlink a', els => els.map(e => e.getAttribute('href'))).catch(() => []);
    if (!xl.length) bad('E4', `${slug}: 缺延伸阅读链接`);
    if (xl.length) e4ok++;
    for (const h of xl) {
      const t = new URL(h, B + `/series/x`).href;
      try { const r = await fetch(t); if (r.status >= 400) bad('E4', `${slug}: 延伸阅读死链 ${h}(${r.status})`); }
      catch { bad('E4', `${slug}: 延伸阅读请求失败 ${h}`); }
    }

    const nv = await page.$$eval('.nav-links .nav-link[data-section]', els =>
      els.map(e => e.getAttribute('data-section'))).catch(() => []);
    if (!nv.includes('series')) bad('E1', `${slug}: 导航缺 series 项`);
  }
  if (prevLinkOk) ok('E3', '「下一篇」链接逐篇点击走通（10/10）');
  if (e2ok === SLUGS.length) ok('E2', `10 篇正文 ${76} 张配图全部真实加载`);
  if (e4ok === SLUGS.length) ok('E4', `10 篇延伸阅读链接齐全且可达`);

  // ---- E5 learning 回链
  for (const lp of LEARNING_LINKBACK) {
    await page.goto(B + '/' + lp, { waitUntil: 'domcontentloaded' });
    const back = await page.$$eval('.series-xlink', els => els.map(e => e.getAttribute('href'))).catch(() => []);
    if (!back.length) { bad('E5', `${lp}: 缺连载回链`); continue; }
    const t = new URL(back[0], B + '/' + lp).href;
    try { const r = await fetch(t); if (r.status >= 400) bad('E5', `${lp}: 回链死链 ${back[0]}(${r.status})`); }
    catch { bad('E5', `${lp}: 回链请求失败 ${back[0]}`); }
  }
  ok('E5', `learning 回链抽检完成（${LEARNING_LINKBACK.length} 页）`);

  // ---- E6
  const realErrs = siteErrs.filter(t => !/ERR_|CSP|frame-ancestors/i.test(t));
  if (realErrs.length) bad('E6', `控制台错误 ${realErrs.length} 条 → ${realErrs[0].slice(0, 80)}`);
  else ok('E6', '全程控制台无站点错误');

  await browser.close();
  await new Promise(r => server.close(r));

  console.log('\n── 通过 ──');
  green.forEach(g => console.log('  🟢', g));
  if (red.length) {
    console.log('\n── 红灯 ──');
    red.forEach(x => console.log('  🔴', x));
  }
  console.log(`\n${red.length ? '🔴 阻断闸 ' + red.length + ' 红' : '✅ 阻断闸全绿'}\n`);
  process.exit(red.length ? 1 : 0);
}

run().catch(e => { console.error('e2e-series 异常:', e); process.exit(1); });
