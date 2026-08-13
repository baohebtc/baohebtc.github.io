# Giscus 评论 / 论坛讨论区 接入指引

> 站点已内置 Giscus 注入代码（`shared/nav.js` 中的 `initGiscus()`），
> 当前为 **默认关闭** 状态。按以下步骤启用后，每篇 `/learning/` 下的页面都会自动成为一条独立讨论帖——
> 这就是你要的「访问者论坛讨论区」（按主题聚类的去中心化论坛）。

## 为什么选 Giscus（而非 Disqus / 自建后端）
- **零后端、零成本**：评论数据存在你自己的 GitHub Issues 里，不用买服务器、不用管数据库。
- **开源免费、无追踪**：不塞广告、不卖数据，符合「宝盒比特币」中立科普定位。
- **和现有仓库天然一体**：直接复用 `baohebtc/baohebtc.github.io` 公开仓库， visitors 的评论 = Issues。
- **轻量**：一行 client.js + 一个容器 div，已为你注入在 `nav.js`，无需改 44 个页面。

## 启用步骤（只需做一次）
1. 仓库必须 **Public**（已满足）。
2. 安装 Giscus GitHub App：打开 https://github.com/apps/giscus ，点击 **Install**，
   授权范围选 `baohebtc/baohebtc.github.io`。
3. 在仓库 **Settings → General → Features** 勾选 **Issues**（Giscus 依赖 Issues 存评论）。
4. 到 https://giscus.app 填配置，得到两个关键值：
   - **Repository ID**（形如 `R_kgD...`）
   - **Discussion Category ID**（你新建一个分类，例如叫「讨论区」，得到 `DIC_...`）
5. 打开 `shared/nav.js`，把 `GISCUS_CONFIG` 改为：
   ```js
   const GISCUS_CONFIG = {
     repo: 'baohebtc/baohebtc.github.io',
     repoId: 'R_xxx...',          // 第4步拿到
     category: '讨论区',
     categoryId: 'DIC_xxx...',    // 第4步拿到
     theme: 'dark',
     lang: 'zh-CN',
     reactions: '1',
     enabled: true                // ← 关键：改为 true 即生效
   };
   ```
6. 提交并 push，GitHub Pages 自动发布后刷新任意学习页，底部即出现评论框。

## 合规提醒
- 评论区属于 UGC，按国内平台惯例你作为运营方对内容负管理责任。
- 建议在「讨论区」置顶一条规则：禁止喊单、场外交易、引流微信/QQ、代币推广。
- 如发现违规评论，直接在对应 Issue 里删除即可（删 Issue 评论 = 删站上评论）。

## 想先不开评论？
保持 `enabled: false` 即可。代码已就位，随时一键开启，不影响任何现有功能。
