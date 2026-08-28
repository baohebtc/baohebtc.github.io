// n7-scan.mjs — lightweight mobile (375px) horizontal overflow scanner.
// Self-sufficient: spins its own static server (no external preview needed),
// waits for full layout (like e2e-site.mjs) so timing false-negatives are avoided.
// Scans every .html under the project root (excludes .git/node_modules, but
// INCLUDES assets/ so internal tool pages are also checked).
//
// Usage: node tools/dev/n7-scan.mjs [--lang=zh|en]   (default zh)
// Exit: 0 = all pass (no overflow > tolerance), 1 = N+ pages overflow / errors.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '../..');
const LANG = (process.argv.find(a => a.startsWith('--lang='))?.split('=')[1]) || 'zh';
const VIEWPORT = { width: 375, height: 800 };
const TOL = 2; // px tolerance for rounding

const MIME = { '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.woff2': 'font/woff2' };
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

function listHtml(dir, acc = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.name === '.git' || e.name === 'node_modules') continue;
    const p = path.join(dir, e.name);
    if (e.isDirectory()) listHtml(p, acc);
    else if (e.name.endsWith('.html')) acc.push(p);
  }
  return acc;
}
const htmlFiles = listHtml(ROOT);
const PORT = 8137;
const urlOf = p => 'http://127.0.0.1:' + PORT + '/' + path.relative(ROOT, p).split(path.sep).join('/');

async function run() {
  await new Promise(r => server.listen(PORT, '127.0.0.1', r));
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: VIEWPORT });
  const results = [];
  let n = 0;
  for (const file of htmlFiles) {
    n++;
    const rel = path.relative(ROOT, file);
    const page = await ctx.newPage();
    try {
      await page.goto(urlOf(file), { waitUntil: 'load', timeout: 15000 });
      await page.waitForTimeout(500); // full layout (fonts/deferred js)
      if (LANG === 'en') {
        const en = await page.$('[data-lang="en"]');
        if (en) { await en.click().catch(() => {}); await page.waitForTimeout(250); }
      }
      const m = await page.evaluate(() => {
        const docW = document.documentElement.scrollWidth;
        const cw = document.documentElement.clientWidth;
        const iw = window.innerWidth;
        const all = document.querySelectorAll('*');
        let worst = null;
        for (const el of all) {
          const r = el.getBoundingClientRect();
          const off = Math.max(r.right - iw, -r.left);
          if (off > 1) {
            const sel = el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : '');
            if (!worst || off > worst.off) worst = { sel, left: Math.round(r.left), right: Math.round(r.right), w: Math.round(r.width), off: Math.round(off) };
          }
        }
        return { docW, cw, iw, worst };
      });
      const overflow = m.docW - m.cw;
      results.push({ rel, overflow, worst: m.worst });
    } catch (e) {
      results.push({ rel, overflow: null, err: String(e.message || e).split('\n')[0].slice(0, 100) });
    } finally { await page.close(); }
  }
  await browser.close();
  await new Promise(r => server.close(r));

  const failures = results.filter(r => r.overflow != null && r.overflow > TOL);
  const errs = results.filter(r => r.err);
  console.log(`\nScanned ${results.length} pages @ ${VIEWPORT.width}px (lang=${LANG})`);
  console.log(`Failures (overflow > ${TOL}px): ${failures.length}`);
  console.log(`Errors: ${errs.length}`);
  for (const r of failures.sort((a, b) => b.overflow - a.overflow))
    console.log(`  +${r.overflow}px  ${r.rel}   ${r.worst ? '← ' + r.worst.sel + ' (L=' + r.worst.left + ' R=' + r.worst.right + ' w=' + r.worst.w + ')' : '(no overflowing element found)'}`);
  for (const r of errs) console.log(`  ERR  ${r.rel}  ${r.err}`);
  process.exit(failures.length === 0 && errs.length === 0 ? 0 : 1);
}
run().catch(e => { console.error(e); process.exit(2); });
