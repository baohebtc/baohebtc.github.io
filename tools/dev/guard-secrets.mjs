#!/usr/bin/env node
/**
 * guard-secrets.mjs — 保密 L1 守门（公开仓库铁律）
 *
 * 用法: node tools/dev/guard-secrets.mjs
 * 退出码: 0 = 通过, 1 = 发现红线内容（非零退出，可挂 pre-commit）
 *
 * 守两条线：
 *   1) 私密内容不得进入公开仓库（路径匹配）：运营私有库 / memory / 运营总体规划 / 公众号未发布文章
 *   2) 密钥形态字符串不得进版本历史：私钥块 / API Secret / Token / Access Key
 *
 * 注意：公众号文章目前以「未跟踪」形式留在公开仓库工作区，属用户本地运营素材，
 *       不算已提交，故「未跟踪文章」只告警不拦；一旦被 git add 进暂存区即变红灯。
 */

import { execSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '../..');

// 红线路径片段（出现即违规）
const FORBIDDEN_PATH = [
  '宝盒运营私有',
  'memory/',
  '运营总体规划',
  'content-source/articles/公众号',
];

// 密钥形态正则（命中即违规）
const SECRET_RE = [
  /-----BEGIN (RSA |EC |OPENSSH |DSA |PRIVATE KEY)-----/,
  /sk-[A-Za-z0-9]{20,}/,
  /AKIA[0-9A-Z]{16}/,
  /ghp_[A-Za-z0-9]{36}/,
  /xox[baprs]-[A-Za-z0-9-]{10,}/,
  /AppSecret/i,
  /app_secret/i,
  /wx[a-f0-9]{32}/i, // 微信 AppID 之外的 secret 形态（谨慎）
];

// 1) 取暂存区 + 已跟踪文件清单
let trackedFiles = [];
try {
  trackedFiles = execSync('git -c core.quotepath=false ls-files', { cwd: ROOT, encoding: 'utf8' }).trim().split('\n').filter(Boolean);
} catch {
  trackedFiles = [];
}
let staged = [];
try {
  staged = execSync('git -c core.quotepath=false diff --cached --name-only', { cwd: ROOT, encoding: 'utf8' }).trim().split('\n').filter(Boolean);
} catch {
  staged = [];
}
// 未跟踪但匹配私密路径（只告警）
let untracked = [];
try {
  const out = execSync('git -c core.quotepath=false status --porcelain', { cwd: ROOT, encoding: 'utf8' });
  untracked = out.split('\n').filter(l => l.startsWith('??')).map(l => l.slice(3).trim());
} catch {
  untracked = [];
}

const reds = [];
const warns = [];

// 2) 路径红线：暂存区 / 已跟踪
const checkPaths = [...new Set([...staged, ...trackedFiles])];
for (const f of checkPaths) {
  for (const frag of FORBIDDEN_PATH) {
    if (f.includes(frag)) reds.push(`路径红线: ${f}（含 ${frag}）`);
  }
}
// 未跟踪文章只告警
for (const f of untracked) {
  if (f.includes('content-source/articles/公众号')) warns.push(`未跟踪公众号文章(本地素材，未提交): ${f}`);
}

// 3) 密钥形态：检查暂存区内容与已跟踪文本
const textExt = /\.(md|js|mjs|ts|json|html|css|txt|yml|yaml|env|sh|py)$/;
// 跳过 tools/dev 自身（检查脚本源码含秘密形态字样的正则定义，会自匹配）
const filesToScan = [...new Set([...staged, ...trackedFiles]
  .filter(f => textExt.test(f) && !f.includes('tools/dev/')))
];
for (const f of filesToScan) {
  const abs = path.join(ROOT, f);
  if (!fs.existsSync(abs)) continue;
  let content = '';
  try { content = fs.readFileSync(abs, 'utf8'); } catch { continue; }
  for (const re of SECRET_RE) {
    if (re.test(content)) reds.push(`密钥形态命中 ${re.source} in ${f}`);
  }
}

// —— 汇总 ——
console.log('\n════════ 保密守门（guard-secrets）════════');
if (reds.length === 0) {
  console.log('🟢 无红线内容');
} else {
  console.log('🔴 发现红线：');
  reds.forEach(r => console.log('   ', r));
}
if (warns.length) {
  console.log('🟡 告警（未提交，不阻断）：');
  warns.forEach(w => console.log('   ', w));
}
console.log('══════════════════════════════════════════');

process.exit(reds.length ? 1 : 0);
