// series-shot.mjs —— 连载页真实浏览器截图（含 404 与控制台错误捕获）
// 用法：node tools/dev/series-shot.mjs <相对路径> <输出png> [light|dark]
import { chromium } from 'playwright';

const path = process.argv[2] || '/series/08-private-key-cliff.html';
const out = process.argv[3] || '/tmp/series-shot.png';
const theme = process.argv[4] || 'dark';
const base = 'http://127.0.0.1:8123';

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });

const errors = [];
const bad = [];
page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
page.on('pageerror', e => errors.push('pageerror: ' + e.message));
page.on('response', r => { if (r.status() >= 400) bad.push(r.status() + ' ' + r.url()); });

await page.goto(base + path, { waitUntil: 'load' });
await page.waitForTimeout(900);

// 切主题（站点明暗双主题都要验）
if (theme === 'light') {
  await page.evaluate(() => document.documentElement.setAttribute('data-theme', 'light'));
  await page.waitForTimeout(400);
}

// 滚到底，触发 lazyload
await page.evaluate(async () => {
  const step = 600;
  for (let y = 0; y < document.body.scrollHeight; y += step) {
    window.scrollTo(0, y);
    await new Promise(r => setTimeout(r, 150));
  }
  window.scrollTo(0, 0);
});
// 图片加载体检（等所有图真正 decode 完，lazy 图最多等 15s）
await page.evaluate(async () => {
  const imgs = Array.from(document.images);
  imgs.forEach(i => { i.loading = 'eager'; });
  await Promise.all(imgs.map(i => i.complete ? Promise.resolve() : new Promise(r => {
    i.addEventListener('load', r, { once: true });
    i.addEventListener('error', r, { once: true });
  })));
  await Promise.all(imgs.map(i => i.decode().catch(() => {})));
});
await page.waitForTimeout(500);
const imgs = await page.evaluate(() =>
  Array.from(document.images).map(i => ({
    src: i.currentSrc || i.src, w: i.naturalWidth, h: i.naturalHeight,
  }))
);
const broken = imgs.filter(i => i.w === 0);

await page.screenshot({ path: out, fullPage: true });

// 顺便截首屏
await page.screenshot({ path: out.replace('.png', '-fold.png') });

console.log('页面:', path);
console.log('图片总数:', imgs.length, '| 加载失败:', broken.length);
broken.slice(0, 8).forEach(b => console.log('  ✗', b.src));
console.log('HTTP >=400:', bad.length);
bad.slice(0, 8).forEach(b => console.log('  ✗', b));
console.log('控制台错误:', errors.length);
errors.slice(0, 8).forEach(e => console.log('  ✗', e));
console.log('截图:', out);

await browser.close();
