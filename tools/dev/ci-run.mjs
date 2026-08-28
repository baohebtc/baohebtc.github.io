#!/usr/bin/env node
/**
 * ci-run.mjs — e2e CI 编排器（tdde2egrilln 的「做之后」自动化闸）
 *
 * 把四个回归闸串成一条 red-line，任一 HARD 闸红灯即整体失败（exit 1）。
 * 运行环境：tools/dev（playwright 由此目录的 node_modules 解析）。
 *
 * 闸清单：
 *   HARD  site-check.mjs              站点 L1 红灯清单 R1–R9（纯 node，无浏览器）
 *   HARD  n7-scan.mjs --lang=zh       375px 移动端横向溢出（中文）
 *   HARD  n7-scan.mjs --lang=en       375px 移动端横向溢出（英文）
 *   HARD  btcnav-check.mjs --lang=zh  BTCMap 导航/主题切换回归
 *   HARD  btcnav-check.mjs --lang=en  BTCMap 导航/主题切换回归（英文）
 *   ADV   e2e-site.mjs                全量 e2e 闸 N1–N7（重、易 OOM，仅记录不阻断）
 *
 * 环境变量：
 *   RUN_FULL_E2E = '1'（默认）运行全量 e2e-site.mjs（作 ADVISORY）
 *                = '0'          跳过全量 e2e（本地快速验证用）
 *
 * 退出码：0 = HARD 闸全绿；1 = 任一 HARD 闸红灯。
 */

import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import fs from 'node:fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DEV = __dirname; // tools/dev

const RUN_FULL_E2E = process.env.RUN_FULL_E2E !== '0'; // 默认跑全量（advisory）

// 顺序执行，避免多 Chromium 实例抢端口/内存
const HARD_GATES = [
  { name: 'site-check (R1–R9)', cmd: ['site-check.mjs'] },
  { name: 'n7-scan zh (移动端溢出)', cmd: ['n7-scan.mjs', '--lang=zh'] },
  { name: 'n7-scan en (移动端溢出)', cmd: ['n7-scan.mjs', '--lang=en'] },
  { name: 'btcnav zh (BTCMap 导航)', cmd: ['btcnav-check.mjs', '--lang=zh'] },
  { name: 'btcnav en (BTCMap 导航)', cmd: ['btcnav-check.mjs', '--lang=en'] },
];

function runGate(file, args) {
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
    }, 240000); // 单闸超时 4 分钟
    child.on('close', (code) => {
      clearTimeout(timer);
      const ms = ((Date.now() - t0) / 1000).toFixed(1);
      // 取末 6 行作为摘要
      const tail = (out + err).split('\n').filter(Boolean).slice(-6).join('\n');
      resolve({ code, ms, tail, killed });
    });
  });
}

function runAdvisory(file, args) {
  return new Promise((resolve) => {
    const child = spawn('node', [file, ...args], {
      cwd: DEV, env: { ...process.env }, stdio: ['ignore', 'pipe', 'pipe'],
    });
    let out = '';
    child.stdout.on('data', (d) => (out += d));
    child.stderr.on('data', (d) => (out += d));
    const timer = setTimeout(() => { try { child.kill('SIGKILL'); } catch (_) {} }, 300000);
    child.on('close', (code) => {
      clearTimeout(timer);
      const tail = out.split('\n').filter(Boolean).slice(-4).join('\n');
      resolve({ code, tail });
    });
  });
}

async function main() {
  console.log('\n══════════════════════════════════════════════════════');
  console.log('  E2E CI GATE RUNNER  (tdde2egrilln · 做之后自动化闸)');
  console.log('══════════════════════════════════════════════════════\n');

  let hardFail = 0;
  let idx = 0;
  for (const g of HARD_GATES) {
    idx++;
    process.stdout.write(`  [${idx}/${HARD_GATES.length}] ${g.name.padEnd(28)} … `);
    const r = await runGate(g.cmd[0], g.cmd.slice(1));
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

  // 全量 e2e-site（advisory）
  console.log('\n  ── 全量 e2e-site.mjs（ADVISORY，不阻断）──');
  if (RUN_FULL_E2E) {
    const a = await runAdvisory('e2e-site.mjs', []);
    const tag = a.code === 0 ? 'GREEN' : `REVIEW(code=${a.code})`;
    console.log(`  FULL E2E: ${tag}`);
    if (a.code !== 0) console.log('    ' + a.tail.replace(/\n/g, '\n    '));
  } else {
    console.log('  FULL E2E: SKIPPED (RUN_FULL_E2E=0)');
  }

  console.log('\n────────────────────────────────────────────────────');
  console.log(`  HARD GATES: ${HARD_GATES.length - hardFail}/${HARD_GATES.length} passed, ${hardFail} failed`);
  const overall = hardFail === 0;
  console.log(`  OVERALL: ${overall ? '✅ GREEN' : '❌ RED'}`);
  console.log('══════════════════════════════════════════════════════\n');
  process.exit(overall ? 0 : 1);
}

main();
