# 比特币学习地图 · GitHub Pages 部署运行手册（手把手）

> ✅ **已上线**：`https://baohebtc.github.io/`（2026-08-13 实测全路径 HTTP 200）。下方步骤为历史记录与复用参考。

> 目标：把本文件夹作为 **用户站** 部署到 `https://baohebtc.github.io/`（网址即品牌）。
> 本机已就绪：分支 `main`、远程 `origin` 已指向 `https://github.com/baohebtc/baohebtc.github.io.git`、52 文件已提交。
> 你只需完成「网页改用户名 → 网页建仓库 → 网页生成 PAT → 终端 push → 网页开 Pages」五步。

---

## 阶段 ① 改 GitHub 用户名为 baohebtc（网页，一次性）

1. 登录 github.com → 右上角头像 → **Settings → Account**。
2. 找到 **Change username**，输入 `baohebtc` → 按提示确认（可能要再输密码 / 2FA）。
3. 改完主页变 `github.com/baohebtc`。

> 现在改最划算：你还没对外发过旧链接，零损失。旧用户名下的项目站链接之后会失效，但无所谓。

---

## 阶段 ② 新建仓库（网页，关键！）

1. 右上角 **＋ → New repository**。
2. 填写（照抄）：
   - **Repository name**：`baohebtc.github.io`  ← **必须一字不差**，否则拿不到根域名
   - **Description（可选）**：`比特币学习地图 · 中英双语开源学习站`
   - **Public** ✅（必须公开，否则不能免费 Pages，也不叫开源）
3. ⚠️ **不要**勾选 "Add a README file" / "Add .gitignore" / "Choose a license"——本地都有了，勾了会导致首次 push 冲突。
4. 点 **Create repository**，停在空仓库页（**不要**照它给的 `git init` 命令做，本地已 init 过）。

---

## 阶段 ③ 生成 Personal Access Token（网页，一次性）

前置（第一次才需要）：
- `Settings → Emails`：确认邮箱已 **Verified**（带绿勾），没验证不能建 token。
- 确认已开 2FA（`Settings → Password and authentication` 里 Two-factor authentication = Enabled）。

生成：
1. 右上角头像 → **Settings → Developer settings → Personal access tokens → Tokens (classic)**。
2. 点 **Generate new token (classic)**（若弹密码+2FA 属正常，填就是）。
3. **Note** 填：`bitcoin-learning-map deploy`
4. **Expiration** 选：`90 days`（也可自定义 / 永不过期，按安全权衡；classic 不是"最长 90 天"，可更长）
5. **Scopes** 勾选：`repo`（点一下，子项自动全选）
6. 拉到底点 **Generate token** → **立刻复制** `ghp_xxx`（只显示这一次，存备忘录）

---

## 阶段 ④ 终端推送（本机，一条命令）

```bash
cd ~/Desktop/宝盒知识库/比特币学习地图
git push -u origin main
```

- 弹 **Username**：填 `baohebtc`（新用户名，不是邮箱）
- 弹 **Password**：**粘贴刚才的 `ghp_xxx`**（不是账号密码；屏幕不显示，正常）
- 看到 `main -> main` 和 `100%` 即成功
- macOS 首次输过后会存进钥匙串，之后很久不用再输

> 备选长期方案（可选，不必现在做）：`gh auth login`（GitHub CLI，浏览器授权，免 token）或 SSH 密钥。

---

## 阶段 ⑤ 开启 Pages（网页，拿公网网址）

1. 进仓库 **Settings → Pages**（左侧）。
2. **Build and deployment**：Source 选 **Deploy from a branch**；Branch 选 **`main`**；目录 **`/ (root)`**。
3. 点 **Save**。
4. 等 1–2 分钟，顶部绿条提示 `Your site is published at https://baohebtc.github.io/`。
5. 浏览器打开验证（首次可能稍慢 / 强制刷新一次）。

---

## 阶段 ⑥ 上线后验证（交给我或自查）

```bash
curl -I https://baohebtc.github.io/
```
返回 `HTTP/2 200` 即成功。把网址发我，我帮你 curl 验路径、相对链接有没有问题。

---

## 常见问题

- **push 报 `Support for password authentication was removed` 或 `No anonymous write access` / `Authentication failed`** → 密码那栏填的是 GitHub 登录密码，应填 PAT（`ghp_xxx`）。自 2021 起 GitHub 禁用密码做 git 操作；若本机 `credential.helper` 为空则每次手动输，输错就报这个。最稳办法是把 token 嵌进远程地址（`git remote set-url origin https://ghp_xxx@github.com/baohebtc/baohebtc.github.io.git`）再 push。
- **push 报 `Invalid username or password`** → PAT 过期 / 复制缺字符；去重新生成。
- **Pages 一直 404** → 仓库名不是 `baohebtc.github.io` 一字不差，或分支/目录没选对（必须 `main` + `/root`）。
- **样式/JS 没加载** → 确认根目录有 `.nojekyll`（已加，关掉 Jekyll 才认相对路径）。
- **国内偶尔慢** → `github.io` 在海外、无法 ICP 备案；认真做国内推广时再买 `baohebtc.com` 绑自定义域名，或迁国内托管。

---

## 本地仓库状态速查

```bash
git branch --show-current   # -> main
git remote -v               # -> origin -> https://github.com/baohebtc/baohebtc.github.io.git
git status --short          # -> 空=干净
git log --oneline -1        # -> 最新提交
```
