#!/usr/bin/env node
/**
 * mirror-articles.mjs — 文章镜像脚本（解决 untracked 备份问题）
 *
 * 背景：公开仓 content-source/articles 与 content-source/topics 下的
 *       公众号文章（母文+微信版）以 untracked 形式存在本地工作区，
 *       不入 git 历史；一旦改丢或盘坏即无法恢复。
 *
 * 做法：把上述目录所有 *.md 复制到私有仓 articles/ 镜像目录，
 *       然后 git add + commit。私有仓为本地仓库（默认路径 ../宝盒运营私有），
 *       一旦加了 remote 即可同步上云。
 *
 * 用法：
 *   node tools/dev/mirror-articles.mjs                # 自动生成日期 commit message
 *   node tools/dev/mirror-articles.mjs "手动备注"      # 自定义 message
 *   MIRROR_PRIVATE_REPO=/path/to/private node ...     # 覆盖私有仓路径
 *
 * 退出码：0 = 成功（或无变化），1 = 失败
 */

import { execSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PUBLIC = path.resolve(__dirname, '../..');
const PRIVATE = process.env.MIRROR_PRIVATE_REPO
  || path.resolve(PUBLIC, '../宝盒运营私有');

const SRC_ARTICLES = path.join(PUBLIC, 'content-source/articles/公众号');
const SRC_TOPICS = path.join(PUBLIC, 'content-source/topics');
const DST_ARTICLES = path.join(PRIVATE, 'articles/公众号');
const DST_TOPICS = path.join(PRIVATE, 'articles/topics');

function log(s) { console.log(`[mirror] ${s}`); }

function sync(srcDir, dstDir, label) {
  if (!fs.existsSync(srcDir)) {
    log(`⚠️  源不存在跳过: ${path.relative(PUBLIC, srcDir)}`);
    return 0;
  }
  fs.mkdirSync(dstDir, { recursive: true });
  const files = fs.readdirSync(srcDir).filter(f => f.endsWith('.md'));
  for (const f of files) {
    fs.copyFileSync(path.join(srcDir, f), path.join(dstDir, f));
    log(`📄  ${label} · ${f}`);
  }
  return files.length;
}

function gitIn(repo, ...args) {
  return execSync(
    `git -C ${JSON.stringify(repo)} -c core.quotepath=false ${args.map(a => /[\s'"\\]/.test(a) ? JSON.stringify(a) : a).join(' ')}`,
    { encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] },
  );
}

try {
  log('===== 开始镜像 =====');
  log(`公开仓: ${PUBLIC}`);
  log(`私有仓: ${PRIVATE}`);

  const n1 = sync(SRC_ARTICLES, DST_ARTICLES, '公众号文章');
  const n2 = sync(SRC_TOPICS, DST_TOPICS, '母文  ');
  const total = n1 + n2;
  log(`共同步 ${total} 篇`);

  log('===== 提交到私有仓 =====');
  gitIn(PRIVATE, 'add', 'articles/');
  // 精准判断是否有 staged 变化（diff --cached --quiet 退出 0=无变化，1=有变化）
  let hasStaged = true;
  try {
    execSync(`git -C ${JSON.stringify(PRIVATE)} -c core.quotepath=false diff --cached --quiet`, { stdio: 'pipe' });
    hasStaged = false;
  } catch (_) { /* 退出 1 = 有 staged 变化 */ }
  if (!hasStaged) {
    log('🟢  无变化，无需 commit');
    process.exit(0);
  }
  // 给用户看一下会提交啥（中文路径用 -c core.quotepath=false 显示）
  const status = gitIn(PRIVATE, 'status', '--short').trim();
  log(`待提交变更：\n${status.split('\n').map(l => '  ' + l).join('\n')}`);

  const today = new Date().toISOString().slice(0, 10);
  const msg = process.argv[2] || `mirror(${today}): 文章镜像 ${total} 篇`;

  gitIn(PRIVATE, 'commit', '-m', msg);
  log(`✅  已 commit: ${msg}`);
  log(`💡  私有仓加了 remote 之后会自动推送到云端；目前仅本地，请尽快配置 remote（参考产物清单.md）`);
  process.exit(0);
} catch (e) {
  console.error('[mirror] ❌  失败:', e.message);
  process.exit(1);
}
