#!/usr/bin/env node
/**
 * map-label-check.mjs — 学习地图标签层验收闸（tdde2egrilln 的 TDD 红灯 + e2e）
 *
 * 为什么要有这个闸：
 *   上次事故是「技术指标全绿、用户价值为零」——HTTP 200 / 站点检查全过，
 *   但地图上一个站名都看不见。所以本闸全部用**读者视角**条款：
 *   用户到底看得到什么、站名在不在站号下面、标签跟母图是不是一套。
 *
 * 真实浏览器（Playwright/Chromium）加载本地站点，不 mock。
 *
 * 检查项（任一红灯即 exit 1）：
 *   L1  10 个站名框，没有一个落在站号圆点的下方（用户 2026-09-10 拍板）
 *   L2  10 站齐全，站号集合 = {1,1.5,2,3,4,5,6,7,8,9}
 *   L3  站名框不越出画布 1760x2368
 *   L4  站名框两两不重叠
 *   L5  站名框不压住别的站圆点
 *   L6  站名框是羊皮纸牌风格（米色底 + 深棕边 + 深棕字），不是深色 UI 框
 *   L7  10 个跳转链接全部可达
 *   L8  网站 SVG 布局 == map-stations.json 布局（坐标容差 1px）
 *   L9  375px 小屏无横向溢出
 *
 * 用法：node tools/dev/map-label-check.mjs
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '../..');
const PORT = 8231;

// 羊皮纸牌（风格 A）目标色 —— 与母图 PNG 严格一致
const PARCHMENT = { fill: 'rgb(245, 235, 214)', stroke: 'rgb(92, 64, 40)', text: 'rgb(58, 40, 24)' };

const MIME = { '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8', '.png': 'image/png', '.svg': 'image/svg+xml',
  '.json': 'application/json; charset=utf-8' };
const server = http.createServer((req, res) => {
  let p = decodeURIComponent(req.url.split('?')[0]);
  if (p === '/') p = '/index.html';
  const fp = path.join(ROOT, p);
  if (!fs.existsSync(fp) || fs.statSync(fp).isDirectory()) { res.writeHead(404); return res.end('nf'); }
  res.writeHead(200, { 'Content-Type': MIME[path.extname(fp).toLowerCase()] || 'application/octet-stream' });
  fs.createReadStream(fp).pipe(res);
});

const fails = [], oks = [];
const ok = (c, m) => (c ? oks : fails).push(m);

await new Promise(r => server.listen(PORT, r));
const browser = await chromium.launch();
const page = await browser.newPage();
await page.goto(`http://127.0.0.1:${PORT}/learning-map.html`, { waitUntil: 'load' });

const hotspots = await page.$$eval('.hotspot', els => els.map(a => {
  const g = s => a.querySelector(s);
  const attr = (el, k) => (el ? parseFloat(el.getAttribute(k)) : NaN);
  const cs = el => (el ? getComputedStyle(el) : null);
  const bg = g('rect.nb-bg'), cn = g('text.nb-cn'), vw = g('text.nb-view');
  const dot = g('circle.dot');
  return {
    href: a.getAttribute('href'),
    num: g('text.num')?.textContent?.trim(),
    name: cn?.textContent?.trim(),
    cx: attr(dot, 'cx'), cy: attr(dot, 'cy'), r: attr(dot, 'r'),
    bx: attr(bg, 'x'), by: attr(bg, 'y'), bw: attr(bg, 'width'), bh: attr(bg, 'height'),
    bgFill: cs(bg)?.fill, bgStroke: cs(bg)?.stroke, cnFill: cs(cn)?.fill,
    hasBox: !!bg, hasName: !!cn, hasView: !!vw,
    boxOpacity: cs(g('g.name-box'))?.opacity,
  };
}));

const JSON_PATH = path.join(__dirname, 'map-stations.json');
const truth = JSON.parse(fs.readFileSync(JSON_PATH, 'utf-8'));
const byNum = Object.fromEntries(truth.stations.map(s => [s.num, s]));

// L2 站齐全
const want = ['1', '1.5', '2', '3', '4', '5', '6', '7', '8', '9'];
const got = hotspots.map(h => h.num);
for (const n of want) {
  const h = hotspots.find(x => x.num === n);
  ok(!!h, `L2 站${n} 缺失`);
  if (h) ok(h.hasBox && h.hasName && h.hasView, `L2 站${n} 缺 name-box / 站名 / 视角文本（用户看不见站名）`);
}
ok(got.length === 10, `L2 站点数应为 10，实际 ${got.length}`);

for (const h of hotspots) {
  const t = byNum[h.num];
  // L1 站名不得在站号下方：框顶低于圆点中心即判违规
  ok(h.by < h.cy, `L1 站${h.num}「${h.name}」站名在站号下方（框顶 y=${h.by} ≥ 圆点 cy=${h.cy}）`);
  // L3 不越界
  ok(h.bx >= 0 && h.bx + h.bw <= truth.canvas.w && h.by >= 0 && h.by + h.bh <= truth.canvas.h,
     `L3 站${h.num} 站名框越界 (${h.bx},${h.by}) ${h.bw}x${h.bh}`);
  // L6 羊皮纸牌风格
  ok(h.bgFill === PARCHMENT.fill,
     `L6 站${h.num} 站名框底色 ${h.bgFill}，应为羊皮纸米色 ${PARCHMENT.fill}`);
  ok(h.bgStroke === PARCHMENT.stroke,
     `L6 站${h.num} 站名框描边 ${h.bgStroke}，应为深棕 ${PARCHMENT.stroke}`);
  ok(h.cnFill === PARCHMENT.text,
     `L6 站${h.num} 站名字色 ${h.cnFill}，应为深棕 ${PARCHMENT.text}`);
  // L8 与真相源一致
  if (t) {
    for (const [k, v] of [['x', h.bx], ['y', h.by], ['w', h.bw], ['h', h.bh]]) {
      ok(Math.abs(v - t[k]) <= 1,
         `L8 站${h.num} ${k}: 页面 ${v} vs 真相源 ${t[k]}（坐标漂移）`);
    }
  }
  // L7 链接可达
  if (h.href) {
    ok(fs.existsSync(path.join(ROOT, h.href)), `L7 站${h.num} 链接不可达: ${h.href}`);
  } else ok(false, `L7 站${h.num} 缺少跳转链接`);
}

// L4 框两两不重叠
for (let i = 0; i < hotspots.length; i++)
  for (let j = i + 1; j < hotspots.length; j++) {
    const a = hotspots[i], b = hotspots[j];
    if (a.bx < b.bx + b.bw && b.bx < a.bx + a.bw && a.by < b.by + b.bh && b.by < a.by + a.bh)
      ok(false, `L4 站${a.num} 与 站${b.num} 站名框重叠`);
  }

// L5 框不压别的站圆点
for (const a of hotspots)
  for (const b of hotspots) {
    if (a.num === b.num) continue;
    if (a.bx - b.r <= b.cx && b.cx <= a.bx + a.bw + b.r && a.by - b.r <= b.cy && b.cy <= a.by + a.bh + b.r)
      ok(false, `L5 站${a.num} 站名框压住 站${b.num} 圆点`);
  }

// L9 小屏无横向溢出
await page.setViewportSize({ width: 375, height: 812 });
await page.waitForTimeout(150);
const ov = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
ok(ov <= 1, `L9 375px 横向溢出 ${ov}px`);

// L10 已读进度：点标记 → 计数+1 → 刷新不丢 → 重置归零
await page.setViewportSize({ width: 1280, height: 900 });
await page.goto(`http://127.0.0.1:${PORT}/learning-map.html`, { waitUntil: 'load' });
const read0 = await page.textContent('#mpDone');
ok(read0?.trim() === '0', `L10 初始已读数应为 0，实际 ${read0}`);
await page.click('.station-card[data-num="1"] .sc-read');
await page.waitForTimeout(100);
const read1 = await page.textContent('#mpDone');
ok(read1?.trim() === '1', `L10 标记后已读数应为 1，实际 ${read1}`);
ok(await page.$eval('.station-card[data-num="1"]', el => el.classList.contains('is-read')),
   'L10 卡片未进入已读态');
ok(await page.$eval('.hotspot[data-num="1"]', el => el.classList.contains('is-read')),
   'L10 地图圆点未同步已读态');
const w = await page.$eval('#mpFill', el => el.style.width);
ok(w === '10%', `L10 进度条宽度应为 10%，实际 ${w}`);
await page.reload({ waitUntil: 'load' });          // 持久化
const read2 = await page.textContent('#mpDone');
ok(read2?.trim() === '1', `L10 刷新后已读数丢失（应为 1），实际 ${read2}`);
await page.click('#mpReset');
await page.waitForTimeout(100);
const read3 = await page.textContent('#mpDone');
ok(read3?.trim() === '0', `L10 重置后应归零，实际 ${read3}`);

// L11 首页有地图入口
await page.goto(`http://127.0.0.1:${PORT}/index.html`, { waitUntil: 'load' });
const entry = await page.$('.mapentry');
ok(!!entry, 'L11 首页正文缺少地图入口 .mapentry');
if (entry) {
  const href = await entry.getAttribute('href');
  ok(href === 'learning-map.html', `L11 入口链接应为 learning-map.html，实际 ${href}`);
  // 入口图是 loading="lazy"，不滚进视口不会加载——必须滚过去再验，否则假红
  await entry.scrollIntoViewIfNeeded();
  await page.waitForFunction(() => {
    const i = document.querySelector('.mapentry img');
    return i && i.complete && i.naturalWidth > 0;
  }, { timeout: 10000 }).catch(() => {});
  const st = await page.$eval('.mapentry img', el => ({ c: el.complete, w: el.naturalWidth }));
  ok(st.c && st.w > 0, `L11 入口配图未加载成功（complete=${st.c} naturalWidth=${st.w}）`);

  // 入口卡片是新加的栅格，必须在 375px 下不撑破页面（n7-scan 全站扫描在本机会超时，
  // 这里针对改动页单独兜住）
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto(`http://127.0.0.1:${PORT}/index.html`, { waitUntil: 'load' });
  await page.waitForTimeout(200);
  const ovIdx = await page.evaluate(() =>
    document.documentElement.scrollWidth - document.documentElement.clientWidth);
  ok(ovIdx <= 1, `L11 首页 375px 横向溢出 ${ovIdx}px`);
}

await browser.close();
server.close();

const gate = ['L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7', 'L8', 'L9', 'L10', 'L11'];
console.log('\n—— 学习地图标签层验收 ——');
for (const g of gate) {
  // 必须带空格：否则 "L1" 会误吞 L10/L11 的失败项
  const bad = fails.filter(f => f.startsWith(g + ' '));
  console.log(bad.length ? `🔴 ${g}  ${bad.length} 项` : `🟢 ${g}  通过`);
}
if (fails.length) {
  console.log(`\n❌ 红灯 ${fails.length} 项：`);
  [...new Set(fails)].slice(0, 40).forEach(f => console.log('   -', f));
  if (fails.length > 40) console.log(`   ... 另有 ${fails.length - 40} 项`);
  process.exit(1);
}
console.log(`\n✅ 全绿：${oks.length} 项断言通过，10 站站点名全部在站号上方/左右，羊皮纸牌风格一致`);
