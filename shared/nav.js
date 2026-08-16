/**
 * 宝盒比特币 · Bitcoin Learning Map — Shared Navigation
 * 开宝盒的钥匙
 */

window.BTCMap = window.BTCMap || {};

/* ================================================
   语言与主题管理
   ================================================ */
BTCMap.lang = localStorage.getItem('btc-lang') || 
  (navigator.language.startsWith('zh') ? 'zh' : 'en');
BTCMap.theme = localStorage.getItem('btc-theme') || 'dark';

/* ================================================
   初始化
   ================================================ */
let __btcNavInited = false;
function initNav() {
  if (__btcNavInited) return;
  __btcNavInited = true;
  applyTheme(BTCMap.theme);
  applyLanguage();
  buildBreadcrumb();
  buildAutoTOC();
  initScrollProgress();
  initSidebarHighlight();
  initSectionScrollSpy();
  updateActiveNavLink();
  initPerspectiveCards();
}

/* ================================================
   自动目录侧栏（缺手写侧栏的页面自动生成，统一 scroll-spy）
   根治「模板不统一 / scroll-spy 只在部分页生效」问题
   ================================================ */
function slugify(text) {
  return (text || '').toString().trim().toLowerCase()
    .replace(/[^\w一-龥]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 40) || 'sec';
}

function buildAutoTOC() {
  // 落地 / 导航页（首页、总览、各 index 枢纽）不自动生成文章式 TOC
  const _loc = (typeof window !== 'undefined' && window.location) ? window.location.pathname : '';
  const _base = _loc.split('/').pop();
  if (_base === 'index.html' || _base === '00-overview.html') return;

  const existing = document.querySelector('.sidebar-nav');
  if (existing && existing.querySelectorAll('a[href^="#"]').length) return; // 已有有效侧栏

  let chapters = [];
  // 按「父容器」分组所有 section，取直接子 section 最多的容器作为章节容器（兼容任意嵌套深度）
  const secGroups = new Map();
  document.querySelectorAll('section').forEach(s => {
    const p = s.parentElement;
    if (!secGroups.has(p)) secGroups.set(p, []);
    secGroups.get(p).push(s);
  });
  let bestSec = null, bestSecN = 0;
  for (const g of secGroups.values()) { if (g.length > bestSecN) { bestSecN = g.length; bestSec = g; } }
  if (bestSec && bestSecN >= 2) chapters = bestSec;

  // 无 section，则用「顶级 h2」切分章节
  if (chapters.length < 2) {
    const topH2 = Array.from(document.querySelectorAll('h2'))
      .filter(h => !(h.parentElement && h.parentElement.closest('section')));
    if (topH2.length >= 2) {
      const groups = new Map();
      topH2.forEach(h => { if (!groups.has(h.parentElement)) groups.set(h.parentElement, []); groups.get(h.parentElement).push(h); });
      let best = null, bestN = 0;
      for (const g of groups.values()) { if (g.length > bestN) { bestN = g.length; best = g; } }
      if (best && bestN >= 2) {
        best.forEach(h => {
          const ph = h.parentNode;
          const sec = document.createElement('section');
          const nodes = [h];
          let n = h.nextElementSibling;
          while (n && n.tagName !== 'H2' && n.tagName !== 'SECTION') { nodes.push(n); n = n.nextElementSibling; }
          const ref = n; // 第一个不被移动的节点（下一个 H2/SECTION 或末尾）
          nodes.forEach(nd => sec.appendChild(nd));
          ph.insertBefore(sec, ref);
        });
        chapters = best.map(h => h.parentElement);
      }
    }
  }
  if (chapters.length < 2) return;

  // 生成 id + 标签
  const items = [];
  const used = {};
  chapters.forEach((sec, i) => {
    let id = sec.id;
    if (!id) {
      const h = sec.querySelector('h1, h2, h3');
      let base = h ? slugify(h.textContent) : ('sec-' + (i + 1));
      let cand = base, k = 1;
      while (used[cand]) { cand = base + '-' + (++k); }
      used[cand] = true; id = cand; sec.id = id;
    } else if (used[id]) {
      let cand = id + '-' + (++used[id]); used[id]++; id = cand; sec.id = id;
    } else { used[id] = 1; }
    const h = sec.querySelector('h1, h2, h3');
    const label = h ? h.textContent.trim().replace(/\s+/g, ' ') : ('第 ' + (i + 1) + ' 节');
    items.push({ id, label });
  });
  if (items.length < 2) return;

  // 构建 nav
  const nav = document.createElement('nav');
  const ul = document.createElement('ul');
  ul.style.listStyle = 'none'; ul.style.margin = '0'; ul.style.padding = '0';
  items.forEach(it => {
    const li = document.createElement('li');
    const a = document.createElement('a');
    a.href = '#' + it.id;
    a.textContent = it.label;
    li.appendChild(a); ul.appendChild(li);
  });
  nav.appendChild(ul);

  // 已有空侧栏且在 two-col 中 → 直接填充（不重建布局）
  const existingInTwoCol = existing && existing.closest('.container.two-col');
  if (existingInTwoCol) { existing.appendChild(nav); return; }
  if (existing) existing.remove(); // 丢弃游离空侧栏

  // 新建两栏：aside.sidebar-nav + div.main-content（包裹章节）
  const wrap = document.createElement('div');
  wrap.className = 'container two-col';
  const aside = document.createElement('aside');
  aside.className = 'sidebar-nav';
  aside.appendChild(nav);
  const mc = document.createElement('div');
  mc.className = 'main-content';
  wrap.appendChild(aside);
  wrap.appendChild(mc);
  const parent = chapters[0].parentNode;
  parent.insertBefore(wrap, chapters[0]);
  chapters.forEach(sec => mc.appendChild(sec));
}

/* ================================================
   主题
   ================================================ */
function toggleTheme() {
  BTCMap.theme = BTCMap.theme === 'dark' ? 'light' : 'dark';
  localStorage.setItem('btc-theme', BTCMap.theme);
  applyTheme(BTCMap.theme);
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  const btn = document.querySelector('[data-action="toggle-theme"]');
  if (btn) {
    btn.textContent = theme === 'dark' ? '🌓' : '🌞';
    btn.title = theme === 'dark' ? '切换到浅色主题' : '切换到深色主题';
  }
}

/* ================================================
   语言
   ================================================ */
function switchLang(lang) {
  BTCMap.lang = lang;
  localStorage.setItem('btc-lang', lang);
  applyLanguage();
  buildBreadcrumb();
  document.querySelectorAll('[data-i18n],[data-i18n-static]').forEach(el => {
    const key = el.dataset.i18n || el.dataset.i18nStatic;
    const val = t(key);
    if (val !== key) el.textContent = val;
  });
  initSidebarHighlight();
  initPerspectiveCards(); // 重新初始化多视角卡片
}

function applyLanguage() {
  const lang = BTCMap.lang;
  document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';
  document.querySelectorAll('[data-lang]').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.lang === lang);
  });
}

function t(key) {
  const lang = BTCMap.lang;
  const map = I18N_MAP[key];
  if (!map) return key;
  return map[lang] || map.zh || key;
}

const I18N_MAP = {
  "book1": { zh: "• 《货币的非国家化》— 哈耶克", en: "• *Denationalisation of Money* — Friedrich Hayek" },
  "book2": { zh: "• 《人的行为》— 米塞斯", en: "• *Human Action* — Ludwig von Mises" },
  "book3": { zh: "• 《精通比特币》— Andreas M. Antonopoulos", en: "• *Mastering Bitcoin* — Andreas M. Antonopoulos" },
  "book4": { zh: "• 《金钱的秘密》— 比特囤币（ahr999）", en: "• *The Secret of Money* — ahr999 (Bitcoin HODLer)" },
  "books_h": { zh: "📚 必读书籍", en: "📚 Essential Reading" },
  "callout1_p": { zh: "中本聪从未在公共场合露面，完美承袭了密码朋克匿名传统。他没有发表哲学论文，而是直接写代码——一个运行在互联网上、完全去中心化、无需许可即可参与、无法被关闭的货币系统。", en: "Satoshi Nakamoto never appeared in public, perfectly inheriting the Cypherpunk tradition of anonymity. Rather than publishing a philosophical paper, he wrote code directly — a monetary system running on the internet, fully decentralized, permissionless to join, and impossible to shut down." },
  "callout1_title": { zh: "比特币是密码朋克理想的「活体实现」", en: "Bitcoin is the living embodiment of the Cypherpunk ideal" },
  "callout2_p": { zh: "奥地利学派区分两种货币：健全货币", en: "The Austrian School distinguishes two kinds of money: sound money" },
  "callout2_title": { zh: "健全货币（Sound Money）vs 法定货币（Fiat Money）", en: "\"Sound Money vs Fiat Money\"" },
  "cp1": { zh: "隐私权是基本人权，非「有所隐藏」才需要隐私", en: "Privacy is a basic human right; you don't need something to hide to want privacy" },
  "cp2": { zh: "强加密 = 权力从政府向个人的重新分配", en: "Strong cryptography = a redistribution of power from government to the individual" },
  "cp3": { zh: "去中心化系统 > 中央控制系统的安全性", en: "Decentralized systems > centrally controlled systems in security" },
  "cp4": { zh: "代码即法律（Code is Law）", en: "Code is Law" },
  "cp5": { zh: "开放协议胜于封闭平台", en: "Open protocols beat closed platforms" },
  "cp6": { zh: "信用要最小化——用数学代替对机构的信任", en: "Minimize trust — replace trust in institutions with mathematics" },
  "cp_icons": { zh: "密码朋克核心思想", en: "Core Cypherpunk Ideas" },
  "cp_tree": { zh: "密码朋克思想谱系", en: "Cypherpunk Intellectual Lineage" },
  "dig_title": { zh: "🔍 延伸阅读推荐", en: "🔍 Recommended Further Reading" },
  "epigraph_cite": { zh: "—— Eric Hughes，《密码朋克宣言》，1993", en: "— Eric Hughes, *A Cypherpunk's Manifesto*, 1993" },
  "epigraph_text": { zh: "「隐私对于电子时代里的开放社会而言是必不可少的。隐私不是秘密，隐私是你不想让全世界都知道的事，但秘密是你不想让任何人知道的事。隐私是选择性向世界透露自己想法的权利。」", en: "\"Privacy is necessary for an open society in the electronic age. Privacy is not secrecy, privacy is the power to selectively reveal oneself to the world.\"" },
  "era1": { zh: "~5000年前", en: "~5000 years ago" },
  "era1_desc": { zh: "货币以真实存在的商品形态出现——贝壳、盐、牛、铜、铁，最终稳定为金银。价值来自天然稀缺性，无人可随意\"创造\"。问题是：携带不便、难以分割、存在假币。", en: "Money first appeared as real commodities — shells, salt, cattle, copper, iron, eventually settling on gold and silver. Value came from natural scarcity; no one could arbitrarily 'create' it. The problem: inconvenient to carry, hard to divide, and vulnerable to counterfeiting." },
  "era1_title": { zh: "商品货币：贝壳与金银", en: "Commodity Money: Shells, Gold and Silver" },
  "era2": { zh: "~1000年前", en: "~1000 years ago" },
  "era2_desc": { zh: "政府开始铸造标准化铸币，并逐步掺杂贱金属（「剪币」现象）。铸币权成为权力核心——谁掌控铸币，谁就掌控财富再分配。", en: "Governments began minting standardized coins and gradually debased them with base metals ('coin clipping'). The power to mint became central to power — whoever controls coinage controls wealth redistribution." },
  "era2_title": { zh: "金属铸币：国家开始介入", en: "Metal Coins: The State Steps In" },
  "era3": { zh: "1694年", en: "1694" },
  "era3_desc": { zh: "私人银行家贷款给政府，政府授予其货币发行垄断权。部分准备金制度（fractional reserve）由此诞生——银行只需持有少量黄金便可贷出10倍的\"存款\"。", en: "Private bankers lent to the government, which granted them a monopoly on money issuance. Fractional reserve banking was born — banks could lend out 10x their gold holdings as 'deposits'." },
  "era3_title": { zh: "中央银行诞生：英格兰银行", en: "Birth of the Central Bank: the Bank of England" },
  "era4": { zh: "1971年", en: "1971" },
  "era4_desc": { zh: "尼克松宣布美元与黄金脱钩。人类正式进入纯法定货币（Fiat Money）", en: "Nixon severed the dollar's link to gold. Humanity entered the era of pure fiat money." },
  "era4_title": { zh: "布雷顿森林体系终结", en: "The End of Bretton Woods" },
  "era5": { zh: "2009年", en: "2009" },
  "era5_desc": { zh: "中本聪在创世区块中写入当天《泰晤士报》的头版标题：「财政大臣站在第二轮救助银行业的边缘」。比特币用算法取代国家信用，用数学取代中央银行，用共识取代强制。", en: "Satoshi embedded the day's Times headline in the genesis block: \"Chancellor on brink of second bailout for banks.\" Bitcoin replaced state credit with algorithms, central banks with mathematics, and coercion with consensus." },
  "era5_title": { zh: "比特币：数学货币诞生", en: "Bitcoin: The Birth of Mathematical Money" },
  "footer": { zh: "© 2026 比特币学习地图 · Bitcoin Learning Map", en: "© 2026 Bitcoin Learning Map" },
  "hayek": { zh: "1976年《货币的非国家化》提出：废除央行货币垄断，允许私人银行发行竞争性货币，市场竞争会让最好的货币胜出。比特币是这一理念的代码实现。", en: "In *Denationalisation of Money* (1976), Hayek proposed abolishing the central bank monopoly and letting private banks issue competing currencies, where market competition lets the best money win. Bitcoin is the code implementation of this idea." },
  "max1": { zh: "货币的价值来自网络效应——越多人用越好用，比特币拥有最强的网络效应", en: "Money's value comes from network effects — the more people use it, the more useful it becomes; Bitcoin has the strongest network effect" },
  "max2": { zh: "「健全货币」的市场只会容纳一种——竞争性货币理论中，赢者通吃", en: "The 'sound money' market can only hold one — in competing-currency theory, winner takes all" },
  "max3": { zh: "绝大多数Altcoin本质是证券或庞氏——而非真正的货币", en: "The vast majority of altcoins are essentially securities or Ponzi schemes — not real money" },
  "max4": { zh: "比特币的开发去中心化程度最高，代码最成熟，安全记录最长", en: "Bitcoin has the most decentralized development, the most mature code, and the longest security track record" },
  "max5": { zh: "先发优势 + 抗审查 = 其他币无法复制的「护城河」", en: "First-mover advantage + censorship resistance = a moat no other coin can replicate" },
  "max_agree": { zh: "多元声音：V神也认同的比特币价值", en: "Diverse Voices: Even Vitalik Recognizes Bitcoin's Value" },
  "max_title": { zh: "比特币最大主义的核心理由", en: "The Core Reasons for Bitcoin Maximalism" },
  "mf_p1": { zh: "1993年，Eric Hughes（加州大学伯克利数学家）、Timothy May（英特尔退休高管）和John Gilmore（Sun Microsystems创始人）三人，在加州共同创立了密码朋克邮件组（Cypherpunks Mailing List）", en: "In 1993, Eric Hughes (UC Berkeley mathematician), Timothy May (retired Intel executive), and John Gilmore (Sun Microsystems founder) co-founded the Cypherpunks mailing list in California" },
  "mf_p2": { zh: "这个邮件组迅速聚集了 Julian Assange（维基解密创始人）、Nick Szabo（智能合约之父，Bit Gold发明者）、Wei Dai（b-money提出者）、Hal Finney（首笔比特币交易的接收者）等思想家。", en: "The list quickly gathered thinkers like Julian Assange (WikiLeaks founder), Nick Szabo (father of smart contracts, inventor of Bit Gold), Wei Dai (proposer of b-money), and Hal Finney (recipient of the first Bitcoin transaction)." },
  "mf_p3": { zh: "他们的核心信条是：「密码学是保卫个人自由、抵抗审查压迫的关键武器。」", en: "Their core creed: 'Cryptography is the key weapon for defending individual freedom and resisting censorship and oppression.'" },
  "mf_title": { zh: "《密码朋克宣言》（Cypherpunk Manifesto, 1993）", en: "A Cypherpunk's Manifesto (1993)" },
  "misc.done": { zh: "✅ 已读完", en: "✅ Done" },
  "misc.mark": { zh: "标记为已读", en: "Mark as Read" },
  "misc.next": { zh: "下一篇 →", en: "Next →" },
  "misc.prev": { zh: "← 上一篇", en: "← Prev" },
  "mises": { zh: "「没有价格信号的指引，计划者无法进行任何理性的经济计算。」比特币通过市场价格发现机制，为全球每个人提供统一的价格参照系。", en: "\"Without price signals, planners cannot perform any rational economic calculation.\" Bitcoin provides a unified price reference for everyone on earth through market price discovery." },
  "nav.home": { zh: "首页", en: "Home" },
  "nav.learn": { zh: "学习区", en: "Learning" },
  "nav.ref": { zh: "参考", en: "Reference" },
  "nav.tools": { zh: "工具", en: "Tools" },
  "next_chapter": { zh: "入门篇", en: "Basics" },
  "next_title": { zh: "一句话入门", en: "The One-Sentence Intro" },
  "online1": { zh: "• Bitcoin.org — 官方比特币网站", en: "• Bitcoin.org — Official Bitcoin Website" },
  "online2": { zh: "• Cypherpunk Cogitations — Jameson Lopp 博客", en: "• Cypherpunk Cogitations — Jameson Lopp's Blog" },
  "online3": { zh: "• Satoshi Nakamoto Institute — 中本聪文库", en: "• Satoshi Nakamoto Institute — Satoshi's Writings" },
  "online4": { zh: "• ahr999.com 镜像 — 囤币哲学中文经典", en: "• ahr999.com mirror — Chinese classic on HODLing philosophy" },
  "online_h": { zh: "🌐 在线资源", en: "🌐 Online Resources" },
  "p1_desc": { zh: "比特币的2100万枚上限写在共识规则里，由全球数万个节点共同执行。没有中央银行可以\"开会决定\"增发——中本聪将铸币权归还给算法和网络。", en: "Bitcoin's 21 million cap is written into the consensus rules, enforced by tens of thousands of nodes worldwide. No central bank can 'vote' to issue more — Satoshi returned the power to mint to algorithms and the network." },
  "p1_title": { zh: "去中心化发行", en: "Decentralized Issuance" },
  "p2_desc": { zh: "比特币区块奖励每21万个区块（约4年）减半一次，2140年左右最终产出将趋于零。减半事件（Halving）历史上每次都引发供应紧缩预期，推动价格上涨。", en: "Bitcoin's block reward halves every 210,000 blocks (~4 years); total issuance approaches zero around 2140. Each Halving has historically triggered supply-deflation expectations and driven prices up." },
  "p2_title": { zh: "抗通胀设计", en: "Inflation-Resistant Design" },
  "p3_desc": { zh: "只要记住私钥，任何人可以在任何有网络的地方转移比特币。没有任何政府可以冻结链上资产、阻止跨境转账，或对持有者实施金融禁令。", en: "With just a private key, anyone can transfer Bitcoin anywhere with internet access. No government can freeze on-chain assets, block cross-border transfers, or impose financial sanctions on holders." },
  "p3_title": { zh: "抗审查 & 跨境", en: "Censorship Resistance & Cross-Border" },
  "p4_desc": { zh: "2100万总量、货币政策规则、区块奖励时间表——全部写在开源代码里，任何人可审计。这消除了对任何机构\"诚信\"的依赖，改为信任数学本身。", en: "The 21M cap, monetary policy rules, and reward schedule are all in open-source code, auditable by anyone. This removes dependence on any institution's 'integrity' and replaces it with trust in mathematics itself." },
  "p4_title": { zh: "透明可验证", en: "Transparent & Verifiable" },
  "p5_desc": { zh: "持有比特币就是直接持有私钥——没有银行倒闭风险，没有托管机构跑路，没有交易对手违约。真正的「最大可还原财富」（Maximum Extractable Value）属于所有者本人。", en: "Holding Bitcoin means directly holding the private key — no bank-failure risk, no custodian runaway, no counterparty default. The true value belongs to the owner." },
  "p5_title": { zh: "无交易对手风险", en: "No Counterparty Risk" },
  "p6_desc": { zh: "与黄金一样稀有（2100万枚上限），同时可以无限分割（Satoshi，1 BTC = 1亿聪），还能瞬间传输。这让\"数字黄金\"比实物黄金更高效、比债券更稀缺。", en: "As scarce as gold (21M cap) yet infinitely divisible (a satoshi = 1/100 million BTC) and instantly transferable. This makes 'digital gold' more efficient than physical gold and scarcer than bonds." },
  "p6_title": { zh: "稀缺性传递", en: "Scarcity Transmitted" },
  "persp.auto": { zh: "自动播放 ·", en: "Auto ·" },
  "persp.click": { zh: "点击切换视角", en: "Click to switch" },
  "persp.multiview": { zh: "多视角重新解释", en: "Multi-perspective reinterpretation" },
  "phil_eyebrow": { zh: "哲学篇 · 第四章", en: "Philosophy · Chapter 4" },
  "phil_h1_1": { zh: "密码朋克、健全货币", en: "Cypherpunks, Sound Money" },
  "phil_h1_2": { zh: "与自主主权", en: "and Self-Sovereignty" },
  "phil_subtitle": { zh: "比特币不只是一种技术发明，它是一场跨越40年的思想运动——从密码朋克到奥地利经济学派，从哈耶克的货币非国家化到中本聪的共识机制，所有线索汇聚成一句话：", en: "Bitcoin is not just a technical invention; it is a 40-year intellectual movement — from Cypherpunks to the Austrian School, from Hayek's denationalisation of money to Satoshi's consensus mechanism, all converging into one sentence:" },
  "pill_desc": { zh: "在电影《黑客帝国》中，Neo 被给予两颗药丸：蓝色代表继续活在虚假的现实中，红色代表接受残酷的真相。比特币社区借用这个隐喻，创造出「橙色药丸」——", en: "In *The Matrix*, Neo is offered two pills: blue to stay in a false reality, red to accept a harsh truth. The Bitcoin community borrowed this metaphor to create the 'Orange Pill' — representing the fundamental shift in thinking after accepting Bitcoin's truth." },
  "pill_s1": { zh: "Before", en: "Before" },
  "pill_s1p": { zh: "「政府印钱是为了大家好，通胀是发展必需代价」", en: "\"The government prints money for our own good; inflation is the necessary cost of progress.\"" },
  "pill_s2": { zh: "Orange Pill", en: "Orange Pill" },
  "pill_s2p": { zh: "「货币是国家权力的工具，通胀是对储户的隐蔽税收」", en: "\"Money is a tool of state power; inflation is a hidden tax on savers.\"" },
  "pill_s3": { zh: "After", en: "After" },
  "pill_s3p": { zh: "「健全货币是自由的基础，2100万上限是文明的馈赠」", en: "\"Sound money is the foundation of freedom; the 21M cap is a gift to civilization.\"" },
  "pill_title": { zh: "「橙色药丸」：被比特币改变的思维方式", en: "The 'Orange Pill': A Mindset Changed by Bitcoin" },
  "prev_chapter": { zh: "上一章", en: "Previous" },
  "prev_title": { zh: "比特币的答案", en: "Bitcoin's Answer" },
  "rothbard": { zh: "将奥地利学派推向「自由意志主义」极端，提出「自我所有权」（Self-Ownership）：个人对自己的身体、劳动和财产拥有绝对主权，不受国家强制。比特币是这一权利在数字时代的延伸。", en: "Pushed the Austrian School to its libertarian extreme, proposing 'self-ownership': individuals have absolute sovereignty over their own body, labor, and property, free from state coercion. Bitcoin is the digital-age extension of this right." },
  "s1_intro": { zh: "货币的本质是什么？它从何而来，又为何走向衰败？比特币之前，人类经历了漫长的货币试错史。每一次\"进步\"都带来了新的权力，也埋下了新的祸根。", en: "What is money, where does it come from, and why does it decay? Before Bitcoin, humanity went through a long trial-and-error history of money. Every 'progress' brought new power and sowed new seeds of ruin." },
  "s1_num": { zh: "Chapter 01", en: "Chapter 01" },
  "s1_title": { zh: "货币的千年之问", en: "The Millennial Question of Money" },
  "s2_intro": { zh: "在第二章", en: "In Chapter 2" },
  "s2_link": { zh: "第二章", en: "Chapter 2" },
  "s2_num": { zh: "Chapter 02", en: "Chapter 02" },
  "s2_title": { zh: "比特币解决了货币史的三大历史缺陷", en: "Bitcoin Solves Three Historical Flaws of Money" },
  "s3_num": { zh: "Chapter 03", en: "Chapter 03" },
  "s3_title": { zh: "密码朋克运动：比特币的思想祖先", en: "The Cypherpunk Movement: Bitcoin's Intellectual Ancestor" },
  "s4_intro": { zh: "比特币的拥趸中相当一部分是奥地利经济学派（Austrian School of Economics）的信徒——他们认为比特币是哈耶克「货币非国家化」理论的技术实践，是对抗凯恩斯主义通胀机器的数字武器。", en: "A sizable share of Bitcoin believers are followers of the Austrian School of Economics — they see Bitcoin as the technical practice of Hayek's 'denationalisation of money' and a digital weapon against the Keynesian inflation machine." },
  "s4_num": { zh: "Chapter 04", en: "Chapter 04" },
  "s4_title": { zh: "奥地利学派：比特币的经济学血缘", en: "The Austrian School: Bitcoin's Economic Lineage" },
  "s5_intro": { zh: "「成为你自己的银行」（Be Your Own Bank）是比特币最深刻的哲学宣言。传统金融体系中，你的存款安全依赖于银行的健康运营、政府的监管善意、以及国家的不崩溃。比特币将这一切替换为：数学 + 你自己", en: "\"Be Your Own Bank\" is Bitcoin's deepest philosophical statement. In traditional finance, your deposits' safety depends on the bank's health, the government's regulatory goodwill, and the state's survival. Bitcoin replaces all this with: mathematics + yourself." },
  "s5_num": { zh: "Chapter 05", en: "Chapter 05" },
  "s5_title": { zh: "自主主权：你的钱，你做主", en: "Self-Sovereignty: Your Money, Your Control" },
  "s6_intro": { zh: "「比特币最大主义」（Bitcoin Maximalism）是一种文化立场：相信比特币是唯一真正值得长期持有的加密资产，其他币（Altcoins）在货币属性上无法与比特币竞争。Vitalik Buterin（以太坊创始人）曾专门撰文为此立场辩护。", en: "Bitcoin Maximalism is a cultural stance: the belief that Bitcoin is the only crypto asset truly worth holding long-term, and that altcoins cannot compete with Bitcoin in monetary properties. Vitalik Buterin (Ethereum's founder) once wrote specifically to defend this position." },
  "s6_num": { zh: "Chapter 06", en: "Chapter 06" },
  "s6_title": { zh: "比特币主义：一种文化运动的兴起", en: "Bitcoinism: The Rise of a Cultural Movement" },
  "s7_num": { zh: "Chapter 07", en: "Chapter 07" },
  "s7_title": { zh: "为什么这一切重要", en: "Why All This Matters" },
  "sov1_h": { zh: "自我所有权", en: "Self-Ownership" },
  "sov1_p": { zh: "你对自己的身体、劳动和财产拥有最高主权。任何强制征税或财产征用，原则上需要你的同意。", en: "You hold supreme sovereignty over your own body, labor, and property. Any forced taxation or expropriation, in principle, requires your consent." },
  "sov2_h": { zh: "私钥即主权", en: "Private Key = Sovereignty" },
  "sov2_p": { zh: "在比特币中，持有私钥 = 持有该地址上的全部资产。没有你的私钥，任何人——包括政府——都无法动用你的币。", en: "In Bitcoin, holding the private key = holding all assets at that address. Without your key, no one — not even the government — can move your coins." },
  "sov3_h": { zh: "无需许可", en: "Permissionless" },
  "sov3_p": { zh: "开设银行账户需要身份证明、KYC审核和信用评分。运行比特币节点只需一台电脑和互联网——无需任何人批准。", en: "Opening a bank account needs ID, KYC checks, and credit scores. Running a Bitcoin node needs only a computer and the internet — no one's permission required." },
  "sov4_h": { zh: "跨境自由", en: "Cross-Border Freedom" },
  "sov4_p": { zh: "传统跨境汇款受外汇管制，每人每年5万美元限额。比特币转账没有国界，没有限额，没有审批——只要有网络。", en: "Traditional cross-border remittance is subject to capital controls (e.g., a $50k/year limit per person). Bitcoin transfers have no borders, no limits, no approval — just internet." },
  "sov5_h": { zh: "抗没收", en: "Confiscation-Resistant" },
  "sov5_p": { zh: "政府可以通过法院命令冻结银行账户、扣押房产。但只要私钥是分散存储的，链上比特币无法被强制转移。", en: "Governments can freeze bank accounts or seize property by court order. But as long as keys are stored securely, on-chain Bitcoin cannot be forcibly transferred." },
  "sov6_h": { zh: "时间价值", en: "Store of Time Value" },
  "sov6_p": { zh: "法定货币因通胀持续稀释购买力。比特币的通缩设计（减半+上限）使其成为财富长期保值工具，而非消耗性消费。", en: "Fiat currency constantly dilutes purchasing power through inflation. Bitcoin's deflationary design (halving + cap) makes it a long-term wealth-preservation tool, not consumptive spending." },
  "sov_title": { zh: "财产权：文明的基础", en: "Property Rights: The Foundation of Civilization" },
  "stat.chapters": { zh: "核心章节", en: "Chapters" },
  "stat.modes": { zh: "阅读模式", en: "Modes" },
  "stat.phases": { zh: "学习阶段", en: "Phases" },
  "stat.tools": { zh: "交互工具", en: "Tools" },
  "td_audit": { zh: "可审计性", en: "Auditability" },
  "td_censorship": { zh: "抗审查", en: "Censorship Resistance" },
  "td_counterfeit": { zh: "防伪/防双花", en: "Counterfeit / Double-Spend Prevention" },
  "td_divisible": { zh: "可分割性", en: "Divisibility" },
  "td_scarcity": { zh: "稀缺性上限", en: "Scarcity Cap" },
  "td_transfer": { zh: "可转移性", en: "Transferability" },
  "th_btc": { zh: "比特币（Bitcoin）", en: "Bitcoin" },
  "th_fiat": { zh: "法定货币（Fiat）", en: "Fiat Currency" },
  "th_gold": { zh: "黄金（Gold）", en: "Gold" },
  "th_property": { zh: "货币属性", en: "Monetary Properties" },
  "v1": { zh: "「在一个充满敌意和不确定性的世界里，比特币最大主义是对欺诈文化的有效防御」", en: "\"In a hostile and uncertain world, Bitcoin maximalism is an effective defense against a culture of fraud.\"" },
  "v2": { zh: "「健全货币（Sound Money）的理念值得认真对待，而非轻蔑地嘲笑」", en: "\"The idea of sound money deserves to be taken seriously, not dismissed with sneers.\"" },
  "v3": { zh: "「比特币的文化和结构优势，使其成为值得持有的强大资产」", en: "\"Bitcoin's cultural and structural advantages make it a powerful asset worth holding.\"" },
  "v4": { zh: "「自我主权验证（Self-Sovereign Verification）的意识形态在未来将更加重要」", en: "\"The ideology of self-sovereign verification will matter even more in the future.\"" },
  "w1_h": { zh: "对政府的意义", en: "Implications for Government" },
  "w1_p": { zh: "比特币迫使政府约束货币发行——如果任意超发，持币者会用脚投票", en: "Bitcoin forces governments to constrain money issuance — if they over-issue, holders vote with their feet" },
  "w2_h": { zh: "对银行业的意义", en: "Implications for Banking" },
  "w2_p": { zh: "比特币证明了无需银行也可以实现安全、全球、低成本的支付系统", en: "Bitcoin proves a secure, global, low-cost payment system is possible without banks" },
  "w3_h": { zh: "对通胀国家居民的意义", en: "Implications for Residents of High-Inflation Countries" },
  "w3_p": { zh: "委内瑞拉、阿根廷、土耳其……比特币为那些无法使用本国货币保值的人提供了避难所", en: "Venezuela, Argentina, Turkey... Bitcoin offers a refuge for those who cannot preserve wealth in their own currency" },
  "w4_h": { zh: "对每个人的意义", en: "Implications for Everyone" },
  "w4_p": { zh: "选择自己信任的货币，是个人自由的基本表达——比特币让这种选择第一次真正成为可能", en: "Choosing the money you trust is a basic expression of individual freedom — Bitcoin makes this choice possible for the first time" },
  "why_h": { zh: "一个更公平的世界需要更公平的货币", en: "A Fairer World Needs Fairer Money" },
  "why_p": { zh: "比特币的意义远超过价格涨跌。它是一套思想体系——关于隐私、财产权、去中心化信任和自我主权的整套哲学。当人们说「持有比特币」时，他们实际上在说：", en: "Bitcoin means far more than price swings. It is a system of thought — a philosophy of privacy, property rights, decentralized trust, and self-sovereignty. When people say 'I hold Bitcoin,' they are really saying: 'I trust mathematics over politicians, code over banks, myself over any authority.'" },
};

function getCurrentPageKey() {
  const path = window.location.pathname;
  const file = path.split('/').pop().replace(/\.html$/, '') || 'index';
  const dir = path.match(/\/learning\/([^/]+)/)?.[1] || '';
  if (path.includes('/learning/')) return `learning/${dir}/${file}`;
  if (path.includes('/tools/')) return `tools/${file}`;
  if (path.includes('/reference/')) return `reference/${file}`;
  return file === '' ? 'index' : file;
}

/* ================================================
   面包屑导航
   ================================================ */
function buildBreadcrumb() {
  const el = document.querySelector('.breadcrumb');
  if (!el) return;
  const path = window.location.pathname;
  const lang = BTCMap.lang;
  const HOME = lang === 'zh' ? '首页' : 'Home';
  const LEARN = lang === 'zh' ? '学习区' : 'Learning';

  let crumbs = [{ label: HOME, href: '../index.html' }];

  if (path.includes('/learning/')) {
    crumbs.push({ label: LEARN, href: '../00-overview.html' });
    const dir = path.match(/\/learning\/([^/]+)/)?.[1];
    if (dir) {
      const names = {
        '01-philosophy': lang === 'zh' ? '哲学篇' : 'Philosophy',
        '02-basics':     lang === 'zh' ? '入门篇' : 'Basics',
        '04-technology': lang === 'zh' ? '技术篇' : 'Technology',
        '03-economics':   lang === 'zh' ? '经济学篇' : 'Economics',
        '05-ecosystem':  lang === 'zh' ? '生态篇' : 'Ecosystem',
      };
      crumbs.push({ label: names[dir] || dir });
    }
  } else if (path.includes('/tools/')) {
    crumbs.push({ label: lang === 'zh' ? '工具' : 'Tools' });
  } else if (path.includes('/reference/')) {
    crumbs.push({ label: lang === 'zh' ? '参考' : 'Reference' });
  } else if (path.includes('/collection/')) {
    crumbs.push({ label: lang === 'zh' ? '文集' : 'Collections', href: '../index.html' });
  }

  el.innerHTML = crumbs.map((c, i) => {
    if (c.href) return `<a href="${c.href}">${c.label}</a><span>›</span>`;
    return `<span>${c.label}</span>`;
  }).join('');
}

/* ================================================
   阅读进度条
   ================================================ */
function initScrollProgress() {
  const fill = document.querySelector('.reading-progress .fill');
  if (!fill) return;
  window.addEventListener('scroll', () => {
    const doc = document.documentElement;
    const st = doc.scrollTop || document.body.scrollTop;
    const sh = doc.scrollHeight - doc.clientHeight;
    fill.style.width = (sh > 0 ? (st / sh) * 100 : 0) + '%';
  }, { passive: true });
}

/* ================================================
   侧栏高亮
   ================================================ */
function initSidebarHighlight() {
  const links = document.querySelectorAll('.sidebar-nav a');
  if (!links.length) return;
  const currentFile = window.location.pathname.split('/').pop();
  links.forEach(link => {
    const href = link.getAttribute('href');
    link.classList.toggle('active', href === currentFile);
  });
}


/* ================================================
   章节滚动高亮（scroll-spy）
   读到哪一节，左侧总览对应条目高亮/变色
   ================================================ */
function initSectionScrollSpy() {
  const sidebar = document.querySelector('.sidebar-nav');
  if (!sidebar) return;
  const links = Array.from(sidebar.querySelectorAll('a[href^="#"]'));
  if (!links.length) return;

  const map = {};
  const sections = [];
  links.forEach(link => {
    const id = (link.getAttribute('href') || '').slice(1);
    if (!id) return;
    const sec = document.getElementById(id);
    if (sec) { map[id] = link; sections.push(sec); }
  });
  if (!sections.length) return;

  const offset = 130; // 顶部导航栏高度 + 余量
  let currentId = null;

  function setActive(id) {
    if (id === currentId) return;
    currentId = id;
    links.forEach(l => l.classList.remove('active'));
    if (map[id]) map[id].classList.add('active');
  }

  const observer = new IntersectionObserver(() => {
    // 在所有 section 中，选出「顶部已越过 offset 线、且最接近该线」的那一节
    let bestId = null, bestTop = -Infinity;
    for (const sec of sections) {
      const rect = sec.getBoundingClientRect();
      if (rect.top <= offset + 10 && rect.top > bestTop) {
        bestTop = rect.top; bestId = sec.id;
      }
    }
    if (bestId) setActive(bestId);
  }, { rootMargin: `-${offset}px 0px -65% 0px`, threshold: [0, 1] });

  sections.forEach(sec => observer.observe(sec));
  setActive(sections[0].id); // 初始高亮第一节
}

function updateActiveNavLink() {
  const path = window.location.pathname;
  document.querySelectorAll('.nav-link[data-section]').forEach(link => {
    const section = link.dataset.section;
    let active = false;
    if (section === 'home' && (path.endsWith('index.html') || path.endsWith('/') || path.endsWith('index'))) active = true;
    if (section === 'learning' && path.includes('/learning/')) active = true;
    if (section === 'tools' && path.includes('/tools/')) active = true;
  if (section === 'reference' && path.includes('/reference/')) active = true;
  if (section === 'collection' && path.includes('/collection/')) active = true;
  link.classList.toggle('active', active);
  });
}

/* ================================================
   多视角一句话卡片（核心组件）
   ================================================ */

const PERSPECTIVE_CONFIG = {
  philosophy: {
    color: '#F97316',
    bg: 'rgba(249,115,22,0.12)',
    icon: '🏛️',
    label: '哲学视角',
    label_en: 'Philosophy',
  },
  technology: {
    color: '#3B82F6',
    bg: 'rgba(59,130,246,0.12)',
    icon: '⚙️',
    label: '技术视角',
    label_en: 'Technology',
  },
  history: {
    color: '#10B981',
    bg: 'rgba(16,185,129,0.12)',
    icon: '📜',
    label: '历史视角',
    label_en: 'History',
  },
  humanity: {
    color: '#EC4899',
    bg: 'rgba(236,72,153,0.12)',
    icon: '🧠',
    label: '人性视角',
    label_en: 'Humanity',
  },
  finance: {
    color: '#EAB308',
    bg: 'rgba(234,179,8,0.12)',
    icon: '💰',
    label: '金融视角',
    label_en: 'Finance',
  },
  business: {
    color: '#8B5CF6',
    bg: 'rgba(139,92,246,0.12)',
    icon: '🏢',
    label: '商业视角',
    label_en: 'Business',
  },
  // —— 技术篇·密码学页专用视角 ——
  dev: {
    color: '#3B82F6',
    bg: 'rgba(59,130,246,0.12)',
    icon: '💻',
    label: '开发者视角',
    label_en: 'Developer',
  },
  security: {
    color: '#EF4444',
    bg: 'rgba(239,68,68,0.12)',
    icon: '🔐',
    label: '安全视角',
    label_en: 'Security',
  },
  user: {
    color: '#10B981',
    bg: 'rgba(16,185,129,0.12)',
    icon: '👤',
    label: '用户视角',
    label_en: 'User',
  },
  math: {
    color: '#8B5CF6',
    bg: 'rgba(139,92,246,0.12)',
    icon: '🔢',
    label: '数学视角',
    label_en: 'Math',
  },
  historian: {
    color: '#EAB308',
    bg: 'rgba(234,179,8,0.12)',
    icon: '📜',
    label: '历史视角',
    label_en: 'History',
  },
  analogy: {
    color: '#F97316',
    bg: 'rgba(249,115,22,0.12)',
    icon: '🎭',
    label: '比喻视角',
    label_en: 'Analogy',
  },
};

function initPerspectiveCards() {
  const cards = document.querySelectorAll('.perspective-card');
  cards.forEach(card => initOneCard(card));
}

function initOneCard(card) {
  if (card.dataset.perspInit) return;   // 防止与页面自带 init 函数重复绑定
  card.dataset.perspInit = '1';
  const tabs = card.querySelectorAll('.p-tab');
  const contents = card.querySelectorAll('.p-content');
  const dots = card.querySelectorAll('.p-dot');
  const autoProgress = card.querySelector('.p-auto-progress .p-bar');
  
  let currentIdx = 0;
  let autoTimer = null;
  const INTERVAL = 5000; // 5秒自动切换
  
  // 获取所有视角
  const angles = Array.from(tabs).map(t => t.dataset.angle);
  const total = angles.length;

  // 显示指定索引
  function showIndex(idx) {
    currentIdx = ((idx % total) + total) % total;
    tabs.forEach((t, i) => {
      t.classList.toggle('active', i === currentIdx);
      const angle = t.dataset.angle;
      t.style.borderColor = i === currentIdx ? PERSPECTIVE_CONFIG[angle]?.color || 'var(--orange)' : '';
    });
    contents.forEach((c, i) => c.classList.toggle('active', i === currentIdx));
    dots.forEach((d, i) => d.classList.toggle('active', i === currentIdx));
    
    // 重置自动播放进度
    if (autoProgress) {
      autoProgress.style.transition = 'none';
      autoProgress.style.width = '0%';
      void autoProgress.offsetWidth; // 强制重绘
      autoProgress.style.transition = `width ${INTERVAL}ms linear`;
      autoProgress.style.width = '100%';
    }
  }

  // 点击Tab切换
  tabs.forEach((tab, i) => {
    tab.addEventListener('click', () => {
      showIndex(i);
      resetAuto();
    });
  });

  // 点击Dot切换
  dots.forEach((dot, i) => {
    dot.addEventListener('click', () => {
      showIndex(i);
      resetAuto();
    });
  });

  function startAuto() {
    stopAuto();
    autoTimer = setInterval(() => {
      showIndex(currentIdx + 1);
    }, INTERVAL);
  }

  function stopAuto() {
    if (autoTimer) { clearInterval(autoTimer); autoTimer = null; }
  }

  function resetAuto() {
    stopAuto();
    startAuto();
  }

  // 鼠标悬停暂停自动播放
  card.addEventListener('mouseenter', stopAuto);
  card.addEventListener('mouseleave', () => {
    if (card.dataset.autoPlay !== 'false') startAuto();
  });

  // 触摸切换
  let touchStartX = 0;
  card.addEventListener('touchstart', e => { touchStartX = e.touches[0].clientX; }, { passive: true });
  card.addEventListener('touchend', e => {
    const dx = e.changedTouches[0].clientX - touchStartX;
    if (Math.abs(dx) > 50) {
      showIndex(currentIdx + (dx < 0 ? 1 : -1));
      resetAuto();
    }
  });

  // 启动自动播放
  if (card.dataset.autoPlay !== 'false') {
    startAuto();
  } else {
    // 隐藏自动进度条
    if (autoProgress) autoProgress.style.display = 'none';
  }

  // 初始化
  showIndex(0);
}

/* ================================================
   工具函数
   ================================================ */
function scrollToAnchor(id) {
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function fmtUSD(n) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n);
}
function fmtBTC(n) {
  return n.toFixed(Math.max(6, 8 - Math.floor(Math.log10(Math.max(n, 0.000001))))) + ' BTC';
}
function fmtNum(n) {
  return new Intl.NumberFormat('en-US').format(n);
}

// 标记已读
function markChapterRead(phase, chapter) {
  try {
    let read = JSON.parse(localStorage.getItem('btc-read-chapters') || '{}');
    read[phase] = read[phase] || {};
    read[phase][chapter] = true;
    localStorage.setItem('btc-read-chapters', JSON.stringify(read));
    localStorage.setItem('btc-progress-update', Date.now().toString());
    // 更新UI
    const btn = document.getElementById('read-btn');
    if (btn) {
      btn.classList.add('read');
      const icon = btn.querySelector('#read-icon');
      const text = btn.querySelector('#read-text');
      if (icon) icon.textContent = '✅';
      if (text) text.textContent = BTCMap.lang === 'zh' ? '已读完' : 'Done';
    }
  } catch(e) {}
}

function isChapterRead(phase, chapter) {
  try {
    let read = JSON.parse(localStorage.getItem('btc-read-chapters') || '{}');
    return !!(read[phase] && read[phase][chapter]);
  } catch(e) { return false; }
}

// 导出
window.BTCMap = {
  ...window.BTCMap,
  toggleTheme,
  switchLang,
  t,
  fmtUSD,
  fmtBTC,
  fmtNum,
  scrollToAnchor,
  markChapterRead,
  isChapterRead,
  initNav,
  PERSPECTIVE_CONFIG,
  initPerspectiveCards,
};

/* ================================================
   自动初始化（无需每页手动调用，根治漏调用问题）
   ================================================ */
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initNav);
} else {
  initNav();
}

/* ================================================
   2026-08-14 改进轮：PWA + Giscus 论坛（纯增量，零破坏）
   - PWA：注册根作用域 Service Worker，使站点可安装、可离线
   - Giscus：每篇 /learning/ 页自动成为独立讨论帖（默认关闭，配好即开）
   ================================================ */

// PWA：注册 Service Worker（仅 https 或 localhost，失败静默忽略）
function initPWA() {
  if (!('serviceWorker' in navigator)) return;
  if (location.protocol !== 'https:' && location.hostname !== 'localhost') return;
  navigator.serviceWorker.register('/sw.js').catch(function () {});
}

// Giscus 评论/论坛配置：enabled 改为 true 并填好 id 后生效（见 docs/GISCUS-SETUP.md）
const GISCUS_CONFIG = {
  repo: 'baohebtc/baohebtc.github.io',
  repoId: 'REPO_ID',
  category: '讨论区',
  categoryId: 'CAT_ID',
  theme: 'dark',
  lang: 'zh-CN',
  reactions: '1',
  enabled: false
};

function initGiscus() {
  if (!GISCUS_CONFIG.enabled) return;
  if (GISCUS_CONFIG.repoId === 'REPO_ID') return; // 未配置则不渲染
  if (!location.pathname.includes('/learning/')) return; // 仅学习页开启讨论
  var mount = document.querySelector('main') || document.body;
  if (!mount || mount.querySelector('.giscus')) return;
  var box = document.createElement('div');
  box.className = 'giscus';
  box.style.marginTop = '48px';
  mount.appendChild(box);
  var s = document.createElement('script');
  s.src = 'https://giscus.app/client.js';
  s.async = true;
  s.crossOrigin = 'anonymous';
  s.setAttribute('data-repo', GISCUS_CONFIG.repo);
  s.setAttribute('data-repo-id', GISCUS_CONFIG.repoId);
  s.setAttribute('data-category', GISCUS_CONFIG.category);
  s.setAttribute('data-category-id', GISCUS_CONFIG.categoryId);
  s.setAttribute('data-mapping', 'pathname');
  s.setAttribute('data-strict', '0');
  s.setAttribute('data-reactions-enabled', GISCUS_CONFIG.reactions);
  s.setAttribute('data-emit-metadata', '0');
  s.setAttribute('data-input-position', 'bottom');
  s.setAttribute('data-theme', GISCUS_CONFIG.theme);
  s.setAttribute('data-lang', GISCUS_CONFIG.lang);
  s.setAttribute('data-loading', 'lazy');
  box.appendChild(s);
}

(function enhance() {
  function run() {
    try { initPWA(); } catch (e) {}
    try { initGiscus(); } catch (e) {}
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
})();
