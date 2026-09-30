#!/usr/bin/env node
/**
 * e2e-collection-links.mjs — 文集外链行为端到端闸（F35 配套）
 *
 * 起因（2026-09-30 用户反馈）：「文集下面的文章是直接跳转了，没有新标签页打开」。
 * 静态属性检查（target="_blank"）只能证明 HTML 写对了，证明不了浏览器真的开新标签页。
 * 本脚本在真实 Chromium 里点击，监听 context 是否产生新 page —— 这是唯一有说服力的证据。
 *
 * 检查项：
 *   E1 文集首页无外露语言切换按钮（ADR-0022）
 *   E2 词条来源链接全部 target=_blank + rel 含 noopener（DOM 实测，非源码正则）
 *   E3 点击来源链接确实产生新标签页（核心证据）
 *   E4 ↗ 外链角标实际渲染出来（getComputedStyle ::after）
 *   E5 撤下的五个空壳页不再可达（应为 404）
 *   E6 控制台无站点自身错误
 *
 * 说明：外链请求用 route 拦截返回桩响应，因此不依赖外网连通性。
 *
 * 用法：node tools/dev/e2e-collection-links.mjs [--port 8130]
 * 退出码：0 = 全绿；1 = 有红
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '../..');
const PORT = Number(process.argv.find(a => a.startsWith('--port'))?.split('=')[1]) || 8130;

const MIME = {
  '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8', '.webmanifest': 'application/manifest+json',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml',
};

const missing = [];
const server = http.createServer((req, res) => {
  const urlPath = decodeURIComponent(req.url.split('?')[0]);
  const filePath = path.join(ROOT, urlPath === '/' ? 'index.html' : urlPath);
  if (!filePath.startsWith(ROOT) || !fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
    missing.push(urlPath);
    res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
    return res.end('404');
  }
  res.writeHead(200, { 'Content-Type': MIME[path.extname(filePath)] || 'application/octet-stream' });
  res.end(fs.readFileSync(filePath));
});

// 注意：index.html 是栏目入口，本身没有词条（只有卡片），不参与 E2/E3/E4
const PAGES = [
  'collection/themes/whitepapers.html',
  'collection/authors/satoshi.html',
  'collection/themes/voices.html',
];
const RETIRED = [
  'collection/authors/community.html',
  'collection/authors/others.html',
  'collection/themes/papers.html',
  'collection/themes/essays.html',
  'collection/themes/videos.html',
];

const results = [];
const errors = [];

function check(name, cond, detail = '') {
  results.push({ name, ok: !!cond, detail });
}

await new Promise(r => server.listen(PORT, r));
const browser = await chromium.launch();
const context = await browser.newContext();
await context.route('**/*', route => {
  const url = route.request().url();
  if (url.startsWith(`http://127.0.0.1:${PORT}/`)) return route.continue();
  // 外链桩：不依赖外网，只验证浏览器是否真的开新标签页
  return route.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: '<html><body>external stub</body></html>' });
});

const page = await context.newPage();
const siteErrors = [];
page.on('console', m => { if (m.type() === 'error') siteErrors.push(m.text()); });
page.on('pageerror', e => siteErrors.push(String(e)));

try {
  // ---- E1 语言按钮已移除 ----
  await page.goto(`http://127.0.0.1:${PORT}/collection/index.html`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(400);
  const langBtns = await page.$$('[data-lang]');
  check('E1 文集首页无外露语言切换按钮', langBtns.length === 0, `找到 ${langBtns.length} 个 [data-lang]`);
  const htmlLang = (await page.getAttribute('html', 'lang')) || '';
  check('E1b html[lang] 为 zh-CN', htmlLang.toLowerCase().startsWith('zh'), `lang=${htmlLang}`);

  // ---- E5 撤下的空壳页应 404 ----
  const retiredBefore = new Set(missing);
  for (const rp of RETIRED) {
    const resp = await page.goto(`http://127.0.0.1:${PORT}/${rp}`, { waitUntil: 'domcontentloaded' }).catch(() => null);
    const code = resp ? resp.status() : 0;
    check(`E5 空壳页已下架 ${rp.split('/').pop()}`, code === 404, `HTTP ${code}`);
  }

  // ---- E2/E3/E4：逐页验证词条来源链接 ----
  for (const rel of PAGES) {
    await page.goto(`http://127.0.0.1:${PORT}/${rel}`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(350);
    const name = rel.split('/').pop();

    const links = await page.$$('.collection-item .ci-meta a[href^="http"]');
    if (links.length === 0) {
      check(`E2 ${name} 有词条来源链接`, false, '0 个');
      continue;
    }

    const attrs = await Promise.all(links.map(async a => ({
      target: await a.getAttribute('target'),
      relAttr: await a.getAttribute('rel'),
    })));
    const badTarget = attrs.filter(a => a.target !== '_blank').length;
    const badRel = attrs.filter(a => !a.relAttr || !a.relAttr.includes('noopener')).length;
    check(`E2 ${name} 全部 ${links.length} 条外链 target=_blank`, badTarget === 0, `${badTarget} 条异常`);
    check(`E2b ${name} 全部外链含 rel=noopener`, badRel === 0, `${badRel} 条异常`);

    // E4 角标
    const after = await page.evaluate(() => {
      const a = document.querySelector('.collection-item .ci-meta a[href^="http"]');
      if (!a) return '';
      return getComputedStyle(a, '::after').content || '';
    });
    check(`E4 ${name} 外链渲染 ↗ 角标`, after.includes('↗'), `content=${after}`);

    // E3 核心：点击是否真开新标签页
    const newPages = [];
    context.on('page', p => newPages.push(p));
    await links[0].click();
    await page.waitForTimeout(700);
    check(`E3 ${name} 点击来源链接开了新标签页`, newPages.length >= 1,
      `新开 ${newPages.length} 个标签页`);
    // 新标签页 URL 应与来源一致
    if (newPages.length) {
      const u = newPages[0].url();
      check(`E3b ${name} 新标签页指向外部源`, /^https?:\/\//.test(u) && !u.includes('127.0.0.1'), u.slice(0, 60));
      await newPages[0].close().catch(() => {});
    }
  }

  // E5 阶段故意访问已下架页面，必然产生 404 —— 属预期噪声，不计入
  const own = siteErrors.filter(e => !/frame-ancestors|Content Security Policy|ERR_|cross-origin|Failed to load resource/i.test(e));
  check('E6 控制台无站点自身错误', own.length === 0, own.slice(0, 2).join(' | '));
} catch (e) {
  errors.push(String(e));
} finally {
  await browser.close();
  server.close();
}

console.log('='.repeat(72));
console.log('e2e-collection-links · 文集外链行为端到端闸（真实 Chromium）');
console.log('='.repeat(72));
let fails = 0;
for (const r of results) {
  console.log(`${r.ok ? '🟢' : '🔴'}  ${r.name}${r.detail ? '  — ' + r.detail : ''}`);
  if (!r.ok) fails++;
}
if (errors.length) { console.log('\n执行异常：'); errors.forEach(e => console.log('  ' + e)); }
console.log('-'.repeat(72));
console.log(fails === 0 && errors.length === 0 ? '✅ ALL PASS（0 FAIL）' : `❌ ${fails} FAIL`);
process.exit(fails === 0 && errors.length === 0 ? 0 : 1);
