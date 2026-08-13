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

### 方式二：GitHub Pages（免费、永久）

需把**整个文件夹**推送到仓库（不是单个文件）：

```bash
cd ~/Desktop/宝盒知识库/比特币学习地图/
git init
git add .
git commit -m "🎉 Bitcoin Learning Map v1.0"
git branch -M main
git remote add origin https://github.com/你的用户名/bitcoin-learning-map.git
git push -u origin main
```

然后在仓库 **Settings → Pages** 选择 `main` 分支根目录，等待约 2 分钟上线：
`https://你的用户名.github.io/bitcoin-learning-map`

> 已内置 `.gitignore`，会自动排除 `node_modules/`、`.DS_Store` 等无关文件。

### 方式三：CloudStudio / 任意静态托管

将整个 `比特币学习地图/` 文件夹作为静态站点上传即可（入口文件 `index.html`）。

### 方式四：IMA 知识库嵌入

将整个文件夹上传到 IMA 知识库的"比特币学习地图"中，即可随时在 IMA 内浏览。

---

## 📄 许可证

本学习网站为教育目的创作，内容开放使用。
