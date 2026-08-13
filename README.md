# 比特币学习地图 · Bitcoin Learning Map

> 从零到专家，建立准确的比特币心智模型。
> AI 时代的学习方式 —— 心智模型优先，开放、免费、中立。
> 中英双语 · 5 大阶段 · 38 篇内容 · 3 个交互计算器。

---

## 📁 项目结构（多页静态站点）

整个网站由 **多个文件** 组成，靠相对路径互相引用，需整体保留、整体部署：

```
📁 比特币学习地图/
├── index.html              ← 首页 / 学习路线图（入口）
├── shared/
│   ├── style.css           ← 全局样式（所有页面共用）
│   └── nav.js              ← 导航栏 + 中英双语切换 + 阅读进度
├── learning/               ← 5 大阶段 · 38 篇内容
│   ├── 00-overview.html    ← 总览 / 认知觉醒入口
│   ├── 01-philosophy/      ← 阶段一：哲学与认知觉醒（4 篇）
│   ├── 02-basics/          ← 阶段二：基础（8 篇）
│   ├── 03-economics/       ← 阶段三：经济学（9 篇）
│   ├── 04-technology/      ← 阶段四：技术（9 篇）
│   └── 05-ecosystem/       ← 阶段五：生态（7 篇）
├── tools/                  ← 3 个交互计算器
│   ├── index.html
│   ├── dca-calculator.html     ← 定投 vs 一次性买入
│   ├── supply-calculator.html  ← 比特币总量理解器
│   └── hodl-simulator.html     ← 长期持有模拟器
├── reference/
│   └── index.html          ← 延伸阅读 / 参考资源
└── README.md               ← 本文件
```

> ⚠️ 部署时请连同 `shared/`、`learning/`、`tools/`、`reference/` 一起上传，
> 只传 `index.html` 会导致样式与脚本丢失。

---

## 🎯 内容覆盖

### 5 大阶段 · 38 篇（含总览）

| 阶段 | 主题 | 篇数 |
|------|------|------|
| 0 | 总览 / 认知觉醒入口 | 1 |
| 1 | 哲学与认知觉醒 | 4 |
| 2 | 基础（私钥·区块链·挖矿·买卖·安全·支付） | 8 |
| 3 | 经济学（通胀·奥地利学派·货币政策·价值储存·费率市场·周期叙事·法币对比·估值模型） | 9 |
| 4 | 技术（密码学·密钥地址·交易·区块结构·挖矿共识·节点网络·升级·扩容 Layer2） | 9 |
| 5 | 生态（全景·钱包·交易所托管·机构 ETF·矿业·协议层） | 7 |

---

## 🌐 中英双语

- **机制**：`shared/nav.js` 中的 `I18N_MAP` 字典（共 155 条，覆盖全部 143 个页面正文键 `data-i18n` + 导航与静态标签 `data-i18n-static`），由 `BTCMap.switchLang()` 在加载时自动挂载。
- **自动**：检测浏览器语言（中文 / 英文）默认展示；顶部栏可手动切换 `中 / EN`。
- **状态**：✅ 全站双语已补全 —— 143 个正文键均含英文翻译，无任何空缺。

---

## 🧮 交互工具（3 个）

1. **定投 vs 一次性买入计算器** (`tools/dca-calculator.html`) —— 对比 DCA 与 Lump Sum 长期收益。
2. **比特币总量理解器** (`tools/supply-calculator.html`) —— 直观理解 2100 万上限与你所占的"多少分之一"。
3. **长期持有模拟器** (`tools/hodl-simulator.html`) —— 模拟不同买入时点与持有周期的资产变化。

> 三个计算器均通过 `node --check` 语法校验，无脚本错误。

---

## 🚀 部署指南

### 方式一：本地预览（最简）

直接双击打开 `index.html` 即可（相对路径在 `file://` 下同样有效）。
如部分浏览器对 `file://` 有限制，可用任意静态服务器：

```bash
cd ~/Desktop/宝盒知识库/比特币学习地图/
python3 -m http.server 8080
# 浏览器打开 http://localhost:8080
```

### 方式二：GitHub Pages（免费、永久、完全开源）

本仓库已在本机完成 `git init` 并提交了全部内容（含 `LICENSE` 与 `.nojekyll`）。
你只需要在 GitHub 网页建好空仓库后，连接远程并推送即可：

```bash
cd ~/Desktop/宝盒知识库/比特币学习地图/
git branch -M main                      # 把默认分支统一为 main（GitHub Pages 推荐）
git remote add origin https://github.com/baohebtc/baohebtc.github.io.git
git push -u origin main
```

> 第一次 `git push` 会弹窗让你登录 GitHub 并授权；用 GitHub 账号密码通常不行，
> 请使用 **Personal Access Token (PAT)** 当作密码（下文「实操步骤」会教你怎么生成）。

然后在仓库 **Settings → Pages → Build and deployment** 选 `main` 分支、`/ (root)` 目录，
点击 Save，等待约 1–2 分钟上线：
`https://baohebtc.github.io/`

> 注：本站采用 GitHub **用户站（user site）** 模式 —— 仓库名必须精确为 `baohebtc.github.io`（与账号名一致）才能拿到根域名 `https://baohebtc.github.io/`，网址即品牌。若用任意其他仓库名则是项目站，网址会带 `/仓库名` 路径。

> - 已内置 `.gitignore`，自动排除 `node_modules/`、`.DS_Store` 等无关文件。
> - 已内置 `.nojekyll`，关闭 GitHub 的 Jekyll 处理，确保纯静态文件原样托管。
> - 想用自定义域名（如 btc.example.com）也在这里填，但需要该域名的 DNS 管理权。

### 方式三：CloudStudio / 任意静态托管

将整个 `比特币学习地图/` 文件夹作为静态站点上传即可（入口文件 `index.html`）。

### 方式四：IMA 知识库嵌入

将整个文件夹上传到 IMA 知识库的"比特币学习地图"中，即可随时在 IMA 内浏览。

---

## 🤝 如何一起贡献（开源协作）

本站以 MIT 许可证完全开源，欢迎任何人学习、复用、纠错、补充。最常见的协作方式：

1. **提 Issue**：在仓库 `Issues` 里反馈错别字、事实错误、想补充的内容。
2. **提 PR（Pull Request）**：
   - 点仓库右上角 **Fork** 把仓库复制到你自己的账号；
   - 在你的副本里修改（可本地 `git clone` 后用任意编辑器）；
   - `git commit` + `git push` 到你自己的 Fork；
   - 回原仓库点 **Contribute → Open pull request** 把改动发回来。
3. **翻译**：双语机制已就绪（`nav.js` 的 `I18N_MAP`），欢迎补充更多语言或润色英文。

新手友好提示：第一次 PR 可以从「修正一处错别字」开始，流程跑通就懂了。

---

## 📄 许可证

本项目以 **MIT License** 开源 —— 详见仓库根目录 [`LICENSE`](LICENSE) 文件。
你可以自由地阅读、复制、修改、再发布本站的代码与内容，只需在副本中保留版权声明与许可声明。
