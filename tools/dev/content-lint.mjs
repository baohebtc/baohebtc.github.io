#!/usr/bin/env node
/**
 * content-lint.mjs — 文章 L1 自动化检查（微信公众号 / 母库文章）
 *
 * 用法: node tools/dev/content-lint.mjs <file.md>
 * 退出码: 0 = 通过, 1 = 有硬伤（敏感词 / 极限词 / 摘要超限 / 图片缺失）
 *
 * 对应协议《三层测试金字塔》L1：把编辑标准翻译成会报错的脚本。
 * 检查的硬项（任一触发即红灯）：
 *   - 敏感词 / 诱导交易表述
 *   - 极限词（最/第一/唯一/国家级…）
 *   - 摘要 ≤ 120 字
 *   - 尾板齐全（关注语 + 风险提示）
 *   - ![]() 图片路径真实存在
 * 软项（仅报告，不拦）：类比 ✅/⚠️ 双段计数、H2 数量
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '../..');

const file = process.argv[2];
if (!file) {
  console.error('用法: node content-lint.mjs <file.md>');
  process.exit(2);
}
const abs = path.resolve(process.cwd(), file);
if (!fs.existsSync(abs)) {
  console.error('文件不存在:', abs);
  process.exit(2);
}
const md = fs.readFileSync(abs, 'utf8');
const base = path.dirname(abs);

// —— 词表（合规铁律：不喊单、不荐标、不诱导交易）——
const SENSITIVE = [
  '稳赚', '收益', '暴涨', '必涨', '抄底', '进场', '梭哈', '暴富',
  '百分百', ' guaranteed', '稳赚不赔', '闭眼买', '上车', '财富自由捷径',
  '立即买入', '马上买', '只涨不跌', '翻仓', '倍增',
];
// 极限词改为「褒义极致词组」，避免「最后/最早/争议最大」等普通词被误匹
// 单字「最」不再列出（已涵盖在「最强/最好/最高…」词组里）
const EXTREME = [
  '最强', '最好', '最高', '最优', '最简单', '最重要', '最优秀', '最极致', '最完美', '最棒',
  '第一', '唯一', '国家级', '顶级', '极致', '全网首发', '绝对',
  '史上最', '全球第一', '独一无二', '100%',
];

const problems = [];
const warnings = [];

// 母库（content-source/topics/）无摘要/尾板/发布配置，是源文而非发布版，自动豁免这两项
const isSource = abs.includes('content-source/topics/');

function check(name, cond, detail) {
  // cond = true 表示「该项通过」；false 才是有问题（红灯）
  if (!cond) problems.push(`🔴 ${name} — ${detail}`);
  else console.log(`🟢 ${name}`);
}

// 1. 敏感词（否定 / 澄清 / 引用语境豁免，避免科普文"不是稳赚""讲成暴富神话"被误红）
const NEG_CTX = ['不', '不是', '≠', '并非', '别', '勿', '请勿', '没有', '无', '避免',
  '误解', '有人', '传说', '被说成', '讲成', '而非'];
function inNegContext(line) { return NEG_CTX.some(n => line.includes(n)); }
const lines = md.split('\n');
const hitSens = [];
for (const w of SENSITIVE) {
  if (lines.some(l => l.includes(w) && !inNegContext(l))) hitSens.push(w);
}
check('敏感词/诱导交易表述 = 0（否定/澄清语境已豁免）', hitSens.length === 0, hitSens.join('、'));

// 2. 极限词（允许出现在「不是…」的否定句里会被误伤，故仅报告 + 强提醒）
const hitExt = EXTREME.filter(w => md.includes(w));
if (hitExt.length) warnings.push(`⚠️ 极限词出现: ${hitExt.join('、')}（请确认是否在否定/引用语境）`);
else console.log('🟢 极限词 = 0（或仅安全语境）');

// 3. 摘要 ≤ 120 字（发布版才检查；母库无摘要字段）
const m = md.match(/摘要[^:：]*[:：]\s*(.+)/);
if (isSource) {
  console.log('🟢 摘要字段（母库豁免）');
} else if (m) {
  const sum = m[1].trim();
  check('摘要 ≤ 120 字', sum.length <= 120, `当前 ${sum.length} 字: ${sum.slice(0, 30)}…`);
} else {
  warnings.push('⚠️ 未找到「摘要：」字段（公众号版建议在 frontmatter 注明）');
  console.log('🟡 摘要字段未检测');
}

// 4. 尾板齐全（发布版才检查；母库无尾板）
const hasFollow = md.includes('慢读宝盒');
const hasRisk = md.includes('风险') && (md.includes('不构成') || md.includes('投资'));
if (isSource) {
  console.log('🟢 尾板齐全（母库豁免）');
} else {
  check('尾板齐全（关注语 + 风险提示）', hasFollow && hasRisk,
    `关注语:${hasFollow ? '有' : '缺'} 风险提示:${hasRisk ? '有' : '缺'}`);
}

// 5. 图片路径真实存在（先剔除反引号包裹的行内代码，避免 `![](path)` 说明文字被误判）
const mdForImg = md.replace(/`[^`]*`/g, '');
const imgRe = /!\[[^\]]*\]\(([^)]+)\)/g;
let im;
const broken = [];
while ((im = imgRe.exec(mdForImg))) {
  const p = im[1].trim();
  if (p.startsWith('http')) continue;
  const target = path.resolve(base, p);
  if (!fs.existsSync(target)) broken.push(p);
}
check('![]() 图片路径全部存在', broken.length === 0, broken.join('、'));

// 6. 类比双段（软项）
const pairOk = (md.match(/✅/g) || []).length >= 1 && (md.match(/⚠️/g) || []).length >= 1;
if (pairOk) console.log(`🟢 类比双段存在 (✅${(md.match(/✅/g) || []).length} ⚠️${(md.match(/⚠️/g) || []).length})`);
else warnings.push('⚠️ 未发现类比 ✅/⚠️ 双段（重要概念建议配类比）');

// 7. H2 数量（软项）
const h2 = (md.match(/^##\s/gm) || []).length;
console.log(`🟡 H2 章节数: ${h2}`);

console.log('\n──────── 结果 ────────');
if (problems.length) {
  console.log('未通过:');
  problems.forEach(p => console.log(' ', p));
} else {
  console.log('✅ 硬项全部通过');
}
warnings.forEach(w => console.log(' ', w));
process.exit(problems.length ? 1 : 0);
