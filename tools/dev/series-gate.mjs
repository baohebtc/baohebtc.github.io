#!/usr/bin/env node
/**
 * series-gate.mjs — 把 Python 门闸接进 ci-run.mjs 的 node 编排。
 * 为什么要有这层：ci-run.mjs 统一以 `node <gate>` 拉起各闸；Python 闸包一层，
 * 退出码原样透传，CI 不需要知道实现语言。
 *
 * 用法：node series-gate.mjs [python脚本名] [传给脚本的参数...]
 *   默认脚本 = series-check.py；例：node series-gate.mjs term-check.py -v
 */
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const first = args[0] || '';
const script = first.endsWith('.py') ? first : 'series-check.py';
const rest = first.endsWith('.py') ? args.slice(1) : args;
const py = process.env.PYTHON || 'python3';
const r = spawnSync(py, [path.join(__dirname, script), ...rest], {
  stdio: 'inherit',
});
process.exit(r.status ?? 1);
