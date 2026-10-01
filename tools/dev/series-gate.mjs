#!/usr/bin/env node
/**
 * series-gate.mjs — 把 series-check.py（Python 门闸）接进 ci-run.mjs 的 node 编排。
 * 为什么要有这层：ci-run.mjs 统一以 `node <gate>` 拉起各闸；Python 闸包一层，
 * 退出码原样透传，CI 不需要知道实现语言。
 */
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const py = process.env.PYTHON || 'python3';
const r = spawnSync(py, [path.join(__dirname, 'series-check.py'), ...process.argv.slice(2)], {
  stdio: 'inherit',
});
process.exit(r.status ?? 1);
