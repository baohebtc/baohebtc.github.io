/**
 * md-to-html.mjs — 公众号文章 → 图文并茂独立 HTML
 *
 * 作用：
 *   把公开仓 content-source 下的公众号文章（微信版 + 母文）转成
 *   一个自带样式、图片以 base64 内嵌的独立 .html 文件，写入私有仓
 *   articles/html/，再 git commit + push（若已配置 origin）。
 *
 * 图片处理：
 *   正文里的 ![](../../../assets/...) 本地相对路径 → 读 PNG/JPG/SVG
 *   → 转成 data: URI 内嵌，使 HTML 单文件即可在任何浏览器打开，
 *   不依赖外部资源。私有仓不需要同步 assets 目录。
 *
 * 发布块剥离：
 *   微信版顶部的「发布配置」「图片上传清单」「发布前删除」等为后台
 *   发布专用，读者版 HTML 中全部剔除（HTML 注释 + 相关 blockquote）。
 *
 * 调用方式：
 *   node tools/dev/md-to-html.mjs            # 生成全部并推送私有仓
 *   node tools/dev/md-to-html.mjs --dry      # 只生成不提交
 * 也可被 mirror-articles.mjs 通过 generateAllHtml() 复用。
 */

import { createRequire } from 'module';
import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';

const require = createRequire(import.meta.url);
const { marked } = require('/Users/mac/.workbuddy/binaries/node/workspace/node_modules/marked');

const PUBLIC_REPO = '/Users/mac/Desktop/宝盒知识库/比特币学习地图';
const PRIVATE_REPO = '/Users/mac/Desktop/宝盒知识库/宝盒运营私有';
const HTML_DIR = path.join(PRIVATE_REPO, 'articles', 'html');

// 让 git 调用对中文路径友好（沿用之前修过的 core.quotepath 技巧）
function gitIn(repo, ...args) {
  const safe = args.map((a) => /[\s'";\\]/.test(a) ? JSON.stringify(a) : a).join(' ');
  return execSync(`git -C ${JSON.stringify(repo)} -c core.quotepath=false ${safe}`, {
    encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'],
  });
}

// ---------- 发布块剥离 ----------
function stripPublishBlocks(md) {
  // 1) 删掉所有 HTML 注释（文章体里只有发布配置类注释，无正文注释）
  let out = md.replace(/<!--[\s\S]*?-->/g, '');
  // 2) 删掉含发布关键词的行，及其后连续的 > 引用块（01 微信版残留）
  const lines = out.split('\n');
  const cleaned = [];
  let skipping = false;
  for (const line of lines) {
    if (/发布配置|图片上传清单|发布前删除/.test(line)) {
      skipping = true;
      continue;
    }
    if (skipping) {
      if (/^\s*>/.test(line)) continue; // 连续引用块一并跳过
      skipping = false;
    }
    cleaned.push(line);
  }
  return cleaned.join('\n').replace(/\n{3,}/g, '\n\n').trim() + '\n';
}

// ---------- 图片 base64 内嵌 ----------
const MIME = { '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.svg': 'image/svg+xml', '.webp': 'image/webp' };

function embedImages(html, baseDir) {
  return html.replace(/<img\b[^>]*>/g, (tag) => {
    const m = tag.match(/src="([^"]+)"/);
    if (!m) return tag;
    let src = m[1];
    if (/^(https?:|data:)/.test(src)) return tag; // 外链/已内嵌不动
    const full = path.resolve(baseDir, decodeURI(src)); // marked v16 会对中文路径 percent 编码，先解码
    if (!fs.existsSync(full)) {
      return `<span class="img-missing">[图片缺失：${decodeURI(src)}]</span>`;
    }
    const ext = path.extname(full).toLowerCase();
    const mime = MIME[ext] || 'image/png';
    const b64 = fs.readFileSync(full).toString('base64');
    return tag.replace(/src="[^"]*"/, `src="data:${mime};base64,${b64}"`);
  });
}

// ---------- 样式模板 ----------
const STYLE = `
:root{
  --bg:#f3ede0; --card:#fffdf8; --ink:#2b2b2b; --muted:#6b6457;
  --orange:#f7931a; --orange-d:#c8760f; --line:#e7ddc9;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Heiti SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  line-height:1.85;font-size:17px;}
.page{padding:32px 16px 64px;}
.post{max-width:720px;margin:0 auto;background:var(--card);
  border:1px solid var(--line);border-radius:16px;overflow:hidden;
  box-shadow:0 8px 30px rgba(120,90,30,.08);}
.post-head{padding:28px 28px 18px;background:linear-gradient(135deg,#fff7e9,#fffdf8);
  border-bottom:3px solid var(--orange);}
.brand{font-size:13px;letter-spacing:2px;color:var(--orange-d);font-weight:700;}
.post-head h1{margin:10px 0 4px;font-size:26px;line-height:1.35;color:#1f1a12;}
.sub{font-size:14px;color:var(--muted);}
.content{padding:24px 28px 8px;}
.content h1,.content h2,.content h3{line-height:1.4;color:#1f1a12;}
.content h2{margin-top:34px;padding-left:12px;border-left:5px solid var(--orange);}
.content h3{margin-top:24px;color:var(--orange-d);}
.content p{margin:14px 0;}
.content a{color:var(--orange-d);}
.content img{max-width:100%;height:auto;border-radius:12px;border:1px solid var(--line);
  margin:18px 0;display:block;background:#faf6ee;}
.img-missing{display:inline-block;padding:8px 12px;background:#fff0e0;color:#a35a00;
  border:1px dashed #e0a85a;border-radius:8px;font-size:13px;}
.content blockquote{margin:18px 0;padding:12px 16px;background:#fbf5e9;
  border-left:4px solid var(--orange);border-radius:0 10px 10px 0;color:#4a4334;}
.content code{background:#f1ead9;padding:2px 6px;border-radius:5px;font-size:14px;
  font-family:"SFMono-Regular",Consolas,monospace;}
.content pre{background:#2b2b2b;color:#f3ede0;padding:14px 16px;border-radius:10px;overflow:auto;}
.content pre code{background:none;color:inherit;padding:0;}
.content table{border-collapse:collapse;width:100%;margin:18px 0;font-size:15px;}
.content th,.content td{border:1px solid var(--line);padding:8px 10px;text-align:left;}
.content th{background:#fbf5e9;color:var(--orange-d);}
.content ul,.content ol{padding-left:22px;}
.content hr{border:none;border-top:1px solid var(--line);margin:28px 0;}
.post-foot{padding:18px 28px 28px;color:var(--muted);font-size:13px;
  border-top:1px dashed var(--line);margin-top:20px;}
.post-foot .risk{background:#fff3e6;padding:12px 14px;border-radius:10px;color:#a35a00;
  border:1px solid #f0d3a8;}
`;

function wrapHtml(title, sub, body) {
  return `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${title} · 慢读宝盒</title>
<style>${STYLE}</style>
</head>
<body>
<div class="page"><article class="post">
<header class="post-head">
  <div class="brand">慢读宝盒 · 比特币学习地图</div>
  <h1>${title}</h1>
  ${sub ? `<div class="sub">${sub}</div>` : ''}
</header>
<div class="content">${body}</div>
<footer class="post-foot">
  <div class="risk">⚠️ 风险提示：比特币价格波动剧烈，本文仅作区块链科普，不构成任何投资建议。投资需谨慎，盈亏自负。</div>
  <p style="margin-top:12px">本文由「慢读宝盒」出品 · 关注公众号获取连载更新</p>
</footer>
</article></div>
</body>
</html>`;
}

// ---------- 单篇转换 ----------
function convertFile(mdPath) {
  const raw = fs.readFileSync(mdPath, 'utf8');
  const clean = stripPublishBlocks(raw);
  const baseDir = path.dirname(mdPath);
  let html = marked.parse(clean, { gfm: true, breaks: false });
  html = embedImages(html, baseDir);
  // 取首个 H1 作标题
  const h1 = (clean.match(/^#\s+(.+)$/m) || [,'未命名'])[1].trim();
  // 副标题：从文件名首部数字推导系列编号（01 / btc-01x → 1 / 01）
  const num = (path.basename(mdPath).match(/(\d+)/) || [,''])[1];
  const sub = num ? `比特币学习地图 · 第 ${num} 篇` : '';
  return { html: wrapHtml(h1, sub, html), title: h1, imgCount: (html.match(/data:image/g) || []).length };
}

// ---------- 全部生成 ----------
export async function generateAllHtml({ dry = false, commit = true } = {}) {
  const targets = [];
  const wxDir = path.join(PUBLIC_REPO, 'content-source', 'articles', '公众号');
  const topicDir = path.join(PUBLIC_REPO, 'content-source', 'topics');
  if (fs.existsSync(wxDir)) {
    for (const f of fs.readdirSync(wxDir)) {
      if (/-微信版\.md$/.test(f)) targets.push({ md: path.join(wxDir, f), out: f.replace(/\.md$/, '.html') });
    }
  }
  if (fs.existsSync(topicDir)) {
    for (const f of fs.readdirSync(topicDir)) {
      if (/\.md$/.test(f)) targets.push({ md: path.join(topicDir, f), out: f.replace(/\.md$/, '-母文.html') });
    }
  }

  fs.mkdirSync(HTML_DIR, { recursive: true });
  const results = [];
  for (const t of targets) {
    const { html, title, imgCount } = convertFile(t.md);
    const outPath = path.join(HTML_DIR, t.out);
    fs.writeFileSync(outPath, html, 'utf8');
    results.push({ out: t.out, title, imgCount });
    console.log(`  ✅ ${t.out}  （${title} · 内嵌图片 ${imgCount} 张）`);
  }

  if (dry) {
    console.log(`[dry] 已生成 ${results.length} 个 HTML 到 ${HTML_DIR}，未提交`);
    return results;
  }
  if (!commit) {
    console.log(`[no-commit] 已生成 ${results.length} 个 HTML 到 ${HTML_DIR}（由调用方统一提交）`);
    return results;
  }

  // 提交 + 推送私有仓
  gitIn(PRIVATE_REPO, 'add', 'articles/html/');
  const status = gitIn(PRIVATE_REPO, 'status', '--short').trim();
  if (!status) {
    console.log('🟢  HTML 无变化，无需提交');
    return results;
  }
  const today = new Date().toISOString().slice(0, 10);
  const msg = `html(${today}): 图文 HTML 生成 ${results.length} 篇（base64 内嵌，单文件可读）`;
  gitIn(PRIVATE_REPO, 'commit', '-m', msg);
  console.log(`✅  已 commit: ${msg}`);
  try {
    gitIn(PRIVATE_REPO, 'push');
    console.log('🚀  已 push 到 origin');
  } catch (e) {
    console.log('⚠️  push 失败（本地备份仍在），请检查 remote：', e.message.split('\n')[0]);
  }
  return results;
}

// CLI 入口
import { fileURLToPath } from 'url';
const __thisFile = fileURLToPath(import.meta.url);
if (process.argv[1] && path.resolve(process.argv[1]) === __thisFile) {
  const dry = process.argv.includes('--dry');
  console.log('===== 生成图文 HTML =====');
  generateAllHtml({ dry }).catch((e) => { console.error('HTML_ERR', e); process.exit(1); });
}
