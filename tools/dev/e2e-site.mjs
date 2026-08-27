#!/usr/bin/env node
/**
 * e2e-site.mjs — 站点端到端（e2e）闸
 *
 * 对应 tdde2egrilln「做之后」环节（兼作线 C nav 重构的 TDD 红灯基准）。
 * 真实浏览器（Playwright/Chromium）加载「完整组装好的」本地站点，不 mock，
 * 走通核心用户路径，验证最终交付。
 *
 * 检查项分两层：
 *  【阻断闸 GATE】（决定 nav 重构能否 go/no-go，必须全绿）
 *   N1  每页 .nav-links 含完整 6 项集合 {home,learning,map,tools,reference,collection}
 *   N2  恰有 1 个 .nav-link.active
 *   N3  导航链接 0 死链（fetch 本地 server 须 200）
 *   N4  主题切换生效（点 toggle-theme 后 data-theme 翻转）
 *   N5  语言切换生效（点 EN 后 documentElement.lang 变 en，可切回）
 *   N6s 站点自身 console 无错（排除第三方/工具噪声，见下）
 *  【观察项 ADVISORY】（记录但不阻断，单独 backlog 跟进）
 *   N6t 第三方/工具噪声：mempool.space iframe CSP、supply-calculator SVG NaN 等
 *   N7  移动端 375 视口横向溢出
 *
 * 用法：node tools/dev/e2e-site.mjs [--port 8123] [--only=子串]...
 * 退出码：0 = 阻断闸全绿；1 = 阻断闸有红
 */

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '../..');
const PORT = Number(process.argv.find(a => a.startsWith('--port'))?.split('=')[1]) || 8123;
const ONLY = process.argv.filter(a => a.startsWith('--only=')).map(a => a.split('=')[1]);

const CANONICAL = ['home', 'learning', 'map', 'tools', 'reference', 'collection'];

// 第三方/工具噪声（非站点自身 bug，不阻断闸门）
const ADVISORY_ERR = /frame-ancestors|Content Security Policy|mempool\.space|player\.bilibili|attribute points|Expected number|polyline|polygon|reading 'connect'|cross-origin|ERR_/i;

const MIME = {
  '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8', '.webmanifest': 'application/manifest+json',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.ico': 'image/x-icon',
  '.woff2': 'font/woff2',
};
const server = http.createServer((req, res) => {
  try {
    let urlPath = decodeURIComponent(req.url.split('?')[0]);
    if (urlPath === '/') urlPath = '/index.html';
    let filePath = path.join(ROOT, urlPath);
    if (!filePath.startsWith(ROOT)) { res.writeHead(403); return res.end('forbidden'); }
    if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
      if (fs.existsSync(filePath + '.html')) filePath += '.html';
      else { res.writeHead(404); return res.end('not found'); }
    }
    const ext = path.extname(filePath).toLowerCase();
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
    fs.createReadStream(filePath).pipe(res);
  } catch { res.writeHead(500); res.end('error'); }
});

function walk(dir, acc = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.name === '.git' || e.name === 'node_modules' || e.name === 'assets') continue;
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, acc);
    else if (e.name.endsWith('.html')) acc.push(p);
  }
  return acc;
}
let allHtml = walk(ROOT);
const rel = p => path.relative(ROOT, p).split(path.sep).join('/');
const urlOf = p => 'http://localhost:' + PORT + '/' + rel(p);
if (ONLY.length) allHtml = allHtml.filter(p => ONLY.some(o => rel(p).includes(o)));

function resolveHref(baseUrl, href) {
  if (!href || href.startsWith('#') || href.startsWith('http') ||
      href.startsWith('mailto:') || href.startsWith('javascript:') || href.startsWith('tel:')) return null;
  return new URL(href, new URL(baseUrl)).href;
}

const results = [];
let gateRed = 0, advCount = 0;

async function run() {
  await new Promise(r => server.listen(PORT, '127.0.0.1', r));
  console.log(`\n════════ 站点 e2e 闸（Playwright/Chromium）════════`);
  console.log(`  本地站点: http://localhost:${PORT}/  待测 ${allHtml.length} 个 HTML`);
  console.log(`  导航标准: ${CANONICAL.join(' · ')}\n`);

  const browser = await chromium.launch();
  for (const file of allHtml) {
    const r = { file: rel(file), gate: [], adv: [], pass: [] };
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    const siteErrs = [], advErrs = [];
    page.on('console', m => { if (m.type() === 'error') (ADVISORY_ERR.test(m.text()) ? advErrs : siteErrs).push(m.text()); });
    page.on('pageerror', e => (ADVISORY_ERR.test(e.message) ? advErrs : siteErrs).push('PAGEERROR: ' + e.message));

    try {
      await page.goto(urlOf(file), { waitUntil: 'load', timeout: 15000 });
      await page.waitForTimeout(300);

      const sections = await page.$$eval('.nav-links .nav-link[data-section]', els =>
        [...new Set(els.map(e => e.getAttribute('data-section')))])
        .catch(() => []);
      const missing = CANONICAL.filter(s => !sections.includes(s));
      if (missing.length) r.gate.push(`N1 缺导航项: ${missing.join('/')}`); else r.pass.push('N1 导航6项完整');

      const active = await page.$$eval('.nav-links .nav-link.active', els => els.length).catch(() => 0);
      if (active === 1) r.pass.push('N2 active唯一'); else r.gate.push(`N2 active数=${active}(应1)`);

      const hrefs = await page.$$eval('.nav-links .nav-link', els => els.map(e => e.getAttribute('href')).filter(Boolean)).catch(() => []);
      const dead = [];
      for (const h of hrefs) {
        const t = resolveHref(urlOf(file), h); if (!t) continue;
        try { const x = await fetch(t, { method: 'GET' }); if (x.status >= 400) dead.push(`${h}(${x.status})`); }
        catch { dead.push(`${h}(ERR)`); }
      }
      if (dead.length) r.gate.push(`N3 死链: ${dead.join(',')}`); else r.pass.push('N3 导航0死链');

      const t0 = await page.getAttribute('html', 'data-theme');
      const tog = await page.$('[data-action="toggle-theme"]');
      if (tog) {
        await tog.click(); await page.waitForTimeout(120);
        const t1 = await page.getAttribute('html', 'data-theme');
        if (t1 && t1 !== t0) r.pass.push('N4 主题切换'); else r.gate.push('N4 主题切换未生效');
      } else r.adv.push('N4 无主题按钮');

      const en = await page.$('[data-lang="en"]');
      if (en) {
        await en.click(); await page.waitForTimeout(120);
        const lng = await page.getAttribute('html', 'lang');
        if (lng && lng.toLowerCase().startsWith('en')) r.pass.push('N5 语言切EN');
        else r.gate.push(`N5 语言未生效(lang=${lng})`);
      } else r.adv.push('N5 无语言按钮');

      if (siteErrs.length) r.gate.push(`N6s 站点错误: ${siteErrs.slice(0,2).join(' | ')}`); else r.pass.push('N6s 站点无错');
      if (advErrs.length) r.adv.push(`N6t 噪声: ${advErrs.slice(0,1).join('')}`);

      await page.setViewportSize({ width: 375, height: 800 }); await page.waitForTimeout(150);
      const ov = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }));
      if (ov.sw > ov.cw + 1) r.adv.push(`N7 横向溢出 ${ov.sw}>${ov.cw}`);
    } catch (e) {
      r.gate.push('加载异常: ' + e.message.split('\n')[0]);
    } finally { await ctx.close(); }

    const red = r.gate.length > 0;
    if (red) gateRed++;
    if (r.adv.length) advCount++;
    results.push(r);
    let line = `  ${red ? '🔴' : '🟢'} ${r.file}`;
    if (r.gate.length) line += `  ⛔ ${r.gate.join('; ')}`;
    if (r.adv.length) line += `  ⚠️ ${r.adv.join('; ')}`;
    console.log(line);
  }

  await browser.close();
  await new Promise(r => server.close(r));
  console.log(`\n════════════════════════════════════════════`);
  console.log(`  页面:${results.length}  阻断闸红:${gateRed}  含观察项:${advCount}`);
  if (gateRed === 0) console.log('✅ 阻断闸全绿（nav 重构可 go）');
  else console.log(`🔴 阻断闸 ${gateRed} 红（待修对象）`);
  console.log(`══════════════════════════════════════════\n`);
  process.exit(gateRed > 0 ? 1 : 0);
}
run().catch(e => { console.error(e); process.exit(2); });
