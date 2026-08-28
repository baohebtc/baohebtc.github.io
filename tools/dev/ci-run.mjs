#!/usr/bin/env node
/**
 * ci-run.mjs — e2e CI 编排器（tdde2egrilln 的「做之后」自动化闸）
 *
 * 把六个回归闸串成一条 red-line，任一 HARD 闸红灯即整体失败（exit 1）。
 * 运行环境：tools/dev（playwright 由此目录的 node_modules 解析）。
 *
 * 闸清单（全部 HARD，任一红灯即整体失败 exit 1）：
 *   HARD  site-check.mjs              站点 L1 红灯清单 R1–R9（纯 node，无浏览器）
 *   HARD  n7-scan.mjs --lang=zh       375px 移动端横向溢出（中文）
 *   HARD  n7-scan.mjs --lang=en       375px 移动端横向溢出（英文）
 *   HARD  btcnav-check.mjs --lang=zh  BTCMap 导航/主题切换回归
 *   HARD  btcnav-check.mjs --lang=en  BTCMap 导航/主题切换回归（英文）
 *   HARD  e2e-site.mjs                全量 e2e 闸 N1–N7（56 页 · 本地实测 ~3.5min · 56MB；RUN_FULL_E2E=0 跳过）
 *
 * 环境变量：
 *   RUN_FULL_E2E = '1'（默认）6 闸全跑，全量 e2e-site.mjs 作 HARD 阻断闸
 *                = '0'          跳过全量 e2e-site（仅跑前 5 闸，本地快速验证用）
 *
 * 退出码：0 = HARD 闸全绿；1 = 任一 HARD 闸红灯。
 */

import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DEV = __dirname; // tools/dev

const RUN_FULL_E2E = process.env.RUN_FULL_E2E !== '0'; // 默认跑全量（HARD）

// 顺序执行，避免多 Chromium 实例抢端口/内存
const HARD_GATES = [
  { name: 'site-check (R1–R9)', cmd: ['site-check.mjs'] },
  { name: 'n7-scan zh (移动端溢出)', cmd: ['n7-scan.mjs', '--lang=zh'] },
  { name: 'n7-scan en (移动端溢出)', cmd: ['n7-scan.mjs', '--lang=en'] },
  { name: 'btcnav zh (BTCMap 导航)', cmd: ['btcnav-check.mjs', '--lang=zh'] },
  { name: 'btcnav en (BTCMap 导航)', cmd: ['btcnav-check.mjs', '--lang=en'] },
  // 全量 e2e：重，但本地实测 ~3.5min / 56MB，远未 OOM，已升格为 HARD 阻断闸
  { name: 'e2e-site (全量 N1–N7)', cmd: ['e2e-site.mjs'], timeout: 540000, fullOnly: true },
];

function runGate(file, args, timeout = 240000) {
  return new Promise((resolve) => {
    const t0 = Date.now();
    const child = spawn('node', [file, ...args], {
      cwd: DEV,
      env: { ...process.env },
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    let out = '';
    let err = '';
    child.stdout.on('data', (d) => (out += d));
    child.stderr.on('data', (d) => (err += d));
    let killed = false;
    const timer = setTimeout(() => {
      killed = true;
      try { child.kill('SIGKILL'); } catch (_) {}
    }, timeout);
    child.on('close', (code) => {
      clearTimeout(timer);
      const ms = ((Date.now() - t0) / 1000).toFixed(1);
      // 取末 6 行作为摘要
      const tail = (out + err).split('\n').filter(Boolean).slice(-6).join('\n');
      resolve({ code, ms, tail, killed });
    });
  });
}

async function main() {
  console.log('\n══════════════════════════════════════════════════════');
  console.log('  E2E CI GATE RUNNER  (tdde2egrilln · 做之后自动化闸)');
  console.log('══════════════════════════════════════════════════════\n');

  let hardFail = 0;
  let totalRun = 0;
  let idx = 0;
  for (const g of HARD_GATES) {
    idx++;
    if (g.fullOnly && !RUN_FULL_E2E) {
      console.log(`  [${idx}/${HARD_GATES.length}] ${g.name.padEnd(28)} … SKIP (RUN_FULL_E2E=0)`);
      continue;
    }
    totalRun++;
    process.stdout.write(`  [${idx}/${HARD_GATES.length}] ${g.name.padEnd(28)} … `);
    const r = await runGate(g.cmd[0], g.cmd.slice(1), g.timeout);
    const ok = r.code === 0 && !r.killed;
    if (!ok) hardFail++;
    if (ok) console.log(`PASS  (${r.ms}s)`);
    else console.log(`FAIL  (${r.ms}s${r.killed ? ' · TIMEOUT/KILL' : ''})`);
    if (!ok) {
      console.log('    ── 摘要 ──');
      console.log('    ' + r.tail.replace(/\n/g, '\n    '));
      console.log('');
    }
  }

  console.log('\n────────────────────────────────────────────────────');
  console.log(`  HARD GATES: ${totalRun - hardFail}/${totalRun} passed, ${hardFail} failed`);
  const overall = hardFail === 0;
  console.log(`  OVERALL: ${overall ? '✅ GREEN' : '❌ RED'}`);
  console.log('══════════════════════════════════════════════════════\n');
  process.exit(overall ? 0 : 1);
}

main();
