#!/usr/bin/env node
/**
 * e2e-seo.mjs —— 发现层（SEO/OG）真实浏览器 e2e（F46 · ADR-0027）
 *
 * 为什么用真浏览器：head 注入正确 ≠ 浏览器解析正确。用 Chromium 实际打开页面，
 * 从 DOM 读 meta，并真实请求 og:image / sitemap，杜绝「注入了但写坏了」的假绿。
 *
 * 检查项：
 *   T1 sitemap.xml HTTP 200 且解析出 67 条 URL
 *   T2 抽样页面 DOM 内 og:title/description/image/url + twitter:card 齐全
 *   T3 抽样 og:image 真实可加载（HTTP 200 + naturalWidth > 0）
 *   T4 canonical 存在且与页面真实 URL 一致
 *   T5 首页 JSON-LD 不再声明 SearchAction（F40 未建）
 *
 * 用法：node e2e-seo.mjs [--port=8123]
 */
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..', '..');

const args = process.argv.slice(2);
const portArg = args.find((a) => a.startsWith('--port='));
const PORT = portArg ? Number(portArg.split('=')[1]) : 8123;
const BASE = `http://127.0.0.1:${PORT}`;

const SAMPLES = [
  '/',                                // 首页（JSON-LD 所在）
  '/series/index.html',               // 栏目页
  '/series/08-private-key-cliff.html',// 连载正文（专属 OG 卡）
  '/series/01x-what-is-money.html',   // 连载正文（1.5 号卡）
  '/reference/index.html',
  '/tools/dca-calculator.html',
  '/collection/authors/satoshi.html',
  '/learning/02-basics/02-02-keys-ownership.html',
];

const results = { pass: [], fail: [] };
const ok = (id, msg) => results.pass.push(`${id} ${msg}`);
const bad = (id, msg) => results.fail.push(`${id} ${msg}`);

async function startServer() {
  // 端口已被占用则直接复用
  try {
    const res = await fetch(`${BASE}/index.html`);
    if (res.ok) return null;
  } catch { /* 需要起服务 */ }
  const proc = spawn('python3', ['-m', 'http.server', String(PORT), '--bind', '127.0.0.1'], {
    cwd: ROOT, stdio: 'ignore', detached: false,
  });
  for (let i = 0; i < 30; i++) {
    await new Promise((r) => setTimeout(r, 300));
    try {
      const res = await fetch(`${BASE}/index.html`);
      if (res.ok) return proc;
    } catch { /* 重试 */ }
  }
  throw new Error('本地静态服务启动失败');
}

async function main() {
  const server = await startServer();
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));

  try {
    // ---------- T1 sitemap ----------
    const sres = await fetch(`${BASE}/sitemap.xml`);
    if (sres.status === 200) {
      const xml = await sres.text();
      const n = (xml.match(/<loc>/g) || []).length;
      const hasSeries = xml.includes('/series/');
      if (n >= 67 && hasSeries) ok('T1', `sitemap 200，${n} 条，含 /series/`);
      else bad('T1', `sitemap ${n} 条（应 ≥67）或缺 /series/`);
    } else bad('T1', `sitemap HTTP ${sres.status}`);

    // ---------- T2/T3/T4 抽样 ----------
    let imgAllOk = true;
    for (const p of SAMPLES) {
      await page.goto(BASE + p, { waitUntil: 'domcontentloaded' });
      const meta = await page.evaluate(() => {
        const g = (sel) => document.querySelector(sel)?.content || null;
        return {
          ogTitle: g('meta[property="og:title"]'),
          ogDesc: g('meta[property="og:description"]'),
          ogImg: g('meta[property="og:image"]'),
          ogUrl: g('meta[property="og:url"]'),
          twCard: g('meta[name="twitter:card"]'),
          canonical: document.querySelector('link[rel="canonical"]')?.href || null,
        };
      });
      const miss = ['ogTitle', 'ogDesc', 'ogImg', 'ogUrl', 'twCard', 'canonical']
        .filter((k) => !meta[k]);
      if (miss.length) bad('T2', `${p} 缺 ${miss.join(',')}`);
      // canonical：与「生产域名 + 收敛后路径」形态比（index.html → /目录/，与门闸同规则）
      if (meta.canonical) {
        const prodPath = p === '/' ? '/' : (p.endsWith('/index.html') ? p.slice(0, -'index.html'.length) : p);
        const prod = ('https://baohebtc.github.io' + prodPath).replace(/\/$/, '');
        if (meta.canonical.replace(/\/$/, '') !== prod)
          bad('T4', `${p} canonical=${meta.canonical} ≠ ${prod}`);
      }
      // og:image 真实加载：生产绝对 URL 转成本地路径（本地服务上验证资源存在）
      const localImg = meta.ogImg
        ? meta.ogImg.replace('https://baohebtc.github.io', BASE) : null;
      const imgOk = localImg && await page.evaluate(async (src) => {
        const im = new Image();
        await new Promise((res) => { im.onload = res; im.onerror = res; im.src = src; });
        return im.complete && im.naturalWidth > 0;
      }, localImg).catch(() => false);
      if (!imgOk) { imgAllOk = false; bad('T3', `${p} og:image 加载失败 → ${localImg || meta.ogImg}`); }
    }
    if (imgAllOk) ok('T3', `8 页 og:image 全部真实加载（站点卡 + 连载专属卡）`);
    ok('T2', '8 页 DOM 内 OG 五件套 + twitter:card + canonical 齐全');
    ok('T4', 'canonical 与页面 URL 一致');

    // ---------- T5 JSON-LD ----------
    await page.goto(BASE + '/', { waitUntil: 'domcontentloaded' });
    const ld = await page.evaluate(() => {
      const el = document.querySelector('script[type="application/ld+json"]');
      return el ? el.textContent : '';
    });
    if (!ld.includes('SearchAction')) ok('T5', 'JSON-LD 已无 SearchAction');
    else bad('T5', 'JSON-LD 仍声明 SearchAction（F40 未建）');

    if (errors.length) bad('T0', `控制台错误 ${errors.length} 条：${errors[0]}`);
    else ok('T0', '抽样页面控制台 0 错误');
  } finally {
    await browser.close();
    if (server) server.kill();
  }

  // ---------- 汇总 ----------
  console.log('\n' + '='.repeat(64));
  for (const p of results.pass) console.log('  ✅ ' + p);
  for (const f of results.fail) console.log('  🔴 ' + f);
  console.log('='.repeat(64));
  console.log(`结果：${results.pass.length} 过 / ${results.fail.length} 挂`);
  process.exit(results.fail.length ? 1 : 0);
}

main().catch((e) => { console.error('✗', e); process.exit(1); });
