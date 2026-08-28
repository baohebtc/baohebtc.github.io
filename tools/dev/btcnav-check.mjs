// BTCMap 回归闸：确保「凡引用 BTCMap 的页面都正确加载 nav.js，且运行时可切换主题/语言」。
// 静态：每个 .html 若引用 BTCMap（onclick 或内联脚本）必须包含 nav.js 引入。
// 运行时：逐页加载 → 点击主题切换按钮 → 断言 BTCMap 已定义且无（本站来源的）pageerror。
//   注：跨域第三方 iframe（如 player.bilibili.com / mempool.space）的报错与 BTCMap 无关，
//       由 #4 的「iframe→链接」修复处理，本闸过滤之，保持精准聚焦 BTCMap。
// 用法：node tools/dev/btcnav-check.mjs  [--lang=zh|en]
// 退出码：0=全绿，1=有违规/报错。
import { chromium } from 'playwright';
import http from 'http';
import fs from 'fs';
import path from 'path';

const ROOT = process.cwd();
const LANG = process.argv.find(a => a.startsWith('--lang='))?.split('=')[1] || 'zh';
const MIME = { '.html':'text/html', '.js':'text/javascript', '.css':'text/css', '.png':'image/png', '.svg':'image/svg+xml', '.json':'application/json' };

function listHtml(dir, acc=[]) {
  for (const e of fs.readdirSync(dir)) {
    if (e === 'node_modules' || e.startsWith('.')) continue;
    const p = path.join(dir, e);
    const s = fs.statSync(p);
    if (s.isDirectory()) listHtml(p, acc);
    else if (path.extname(p) === '.html') acc.push(p);
  }
  return acc;
}

// 页面是否真的使用了 BTCMap（onclick 或内联脚本引用）。内部工具页（如坐标拾取器）不算。
function usesBTCMap(txt) {
  return /onclick=["']BTCMap\.|[^.a-zA-Z]BTCMap\.[a-zA-Z]/.test(txt);
}

// 页面错误是否来自本站（localhost/127.0.0.1）。跨域 iframe 报错返回 false。
function isFirstParty(err) {
  const stack = (err && err.stack) || '';
  const urls = stack.match(/https?:\/\/[^\s:]+/g) || [];
  if (urls.length === 0) return true; // 无来源信息则保守视为本站
  return urls.every(u => /127\.0\.0\.1|localhost/.test(u));
}

// ---------- 静态检查 ----------
function staticCheck(files) {
  const violations = [];
  for (const f of files) {
    const txt = fs.readFileSync(f, 'utf8');
    if (usesBTCMap(txt) && !/nav\.js/.test(txt)) {
      violations.push({ f: path.relative(ROOT, f), why: '引用 BTCMap 但缺少 nav.js 引入' });
    }
  }
  return violations;
}

// ---------- 运行时检查 ----------
const server = http.createServer((req, res) => {
  let u = decodeURIComponent(req.url.split('?')[0]);
  if (u === '/') u = '/index.html';
  const fp = path.join(ROOT, u);
  if (!fp.startsWith(ROOT) || !fs.existsSync(fp)) { res.writeHead(404); res.end('nf'); return; }
  res.writeHead(200, { 'Content-Type': MIME[path.extname(fp)] || 'text/plain' });
  fs.createReadStream(fp).pipe(res);
});
await new Promise(r => server.listen(8132, r));

const browser = await chromium.launch();
const page = await browser.newPage();
const files = listHtml(ROOT);
const runtimeBad = [];

for (const f of files) {
  const rel = path.relative(ROOT, f);
  const txt = fs.readFileSync(f, 'utf8');
  const uses = usesBTCMap(txt);
  const url = 'http://127.0.0.1:8132/' + rel.split(path.sep).join('/');
  const errs = [];
  page.removeAllListeners('pageerror');
  page.on('pageerror', e => { if (isFirstParty(e)) errs.push(e.message); });
  try {
    await page.goto(url, { waitUntil: 'load', timeout: 15000 });
    await page.waitForTimeout(350);
    if (LANG === 'en') {
      try { await page.evaluate(() => window.BTCMap && BTCMap.switchLang && BTCMap.switchLang('en')); } catch (_) {}
      await page.waitForTimeout(150);
    }
    if (uses) {
      // 仅对「使用 BTCMap 的页」做 BTCMap 断言
      const t = await page.evaluate(() => typeof window.BTCMap);
      if (t !== 'object' && t !== 'function') errs.push('BTCMap 未定义 (typeof=' + t + ')');
      try {
        await page.evaluate(() => { const b = document.querySelector('[data-action="toggle-theme"]'); if (b) b.click(); });
        await page.waitForTimeout(120);
      } catch (e) { errs.push('click theme: ' + e.message); }
    }
  } catch (e) { errs.push('GOTO_FAIL:' + e.message); }
  if (errs.length) runtimeBad.push({ f: rel, errs });
}
await browser.close();
server.close();

// ---------- 汇总 ----------
const staticViol = staticCheck(files);
console.log(`BTCMap 回归闸 (lang=${LANG})`);
console.log(`扫描页面: ${files.length}（其中使用 BTCMap 的页做运行时断言）`);
console.log(`静态违规: ${staticViol.length}`);
for (const v of staticViol) console.log(`  ✗ ${v.f} — ${v.why}`);
console.log(`运行时 BTCMap 报错: ${runtimeBad.length}`);
for (const b of runtimeBad) {
  console.log(`  ✗ ${b.f}`);
  for (const e of b.errs) console.log(`      → ${e}`);
}
const ok = staticViol.length === 0 && runtimeBad.length === 0;
console.log(ok ? '\n✅ BTCMap 闸全绿' : '\n❌ BTCMap 闸存在失败');
process.exit(ok ? 0 : 1);
