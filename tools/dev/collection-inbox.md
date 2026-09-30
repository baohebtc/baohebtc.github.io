# 文集新源收件箱（补录通道）

> 用途：把「想收录但还没验证」的链接先丢在这里，验通一条，进页面一条。
> 这是本站「先验证后收录」纪律的落地点——**未经验证的链接不进白名单，也不进页面。**
> 建立日期：2026-09-30

## 怎么用

1. 把候选链接按下面的格式写进「待验证」区，一行一条，可加备注
2. 跑验证器：

   ```bash
   python3 tools/dev/collection-verify-sources.py -f tools/dev/collection-inbox.md --expect 比特币 bitcoin
   ```

   （`--expect` 可选，用来确认正文确实跟主题相关，避免出现「链接活着但内容不对」）

3. PASS 的链接：
   - 追加进 `collection-sources-allowlist.txt`（否则门闸 R6 会拦）
   - 写进对应栏目的 HTML（或直接改 `make_collection_pages.py` 的数据表再重新生成）
   - 从「待验证」区移除
4. 重跑门闸：`python3 tools/dev/collection-check.py`

## 已知不可达（本机网络层面，不要再反复试）

| 域名 | 现象 | 结论 |
|---|---|---|
| `x.com` / `twitter.com` | 连接直接失败（000） | 推文类来源无法自动验证 |
| `strategy.com` / `www.strategy.com` | 一律 403（Cloudflare 拦机器人） | 需人工在浏览器确认后再议 |
| `r.jina.ai` | 连接失败（000） | 代理阅读通道也不可用 |
| `web.archive.org` | 连接失败（000） | 归档快照通道不可用 |
| `bitcoin.org` / `bitcointalk.org` | 连接失败（000） | 原始文献改走 nakamotoinstitute.org |
| `www.saylor.org` 子页 | 200 但正文只有一句口号 | SPA 空壳，判无效 |

> 注意：上面这些域名**在真实浏览器里可能是好的**。这里记录的只是「本机验证不了」，
> 所以结论是「不能自动收」，不是「内容不存在」。若人工确认过，可在借条区登记。

---

## 待验证

（在这里追加候选链接，一行一条；`#` 开头为注释；空行忽略）

https://github.com/Bwy999/Bitcoin

---

## 已借条收录（人工确认、机器不可验）

> 仅在本机不可达但已由人在浏览器里打开确认过时填写，需写明谁在什么时候确认的。
> 目前为空——Saylor 的 X 长文与 Strategy 官网文章尚未人工确认，故一条未收。

---

## 变更记录

- 2026-09-30 建立。同步交付 `collection-verify-sources.py`（V1 状态码 / V2 正文长度 /
  V3 登录墙与 SPA 空壳识别 / V4 主题关键词命中 四道检查）。
- 2026-09-30 首批实测发现两个坑并已写进脚本注释：
  1. 请求头带 `Accept-Encoding: gzip` 会让 GitHub 在本机网络下超时（表现为 000）；
  2. Moodle（learn.saylor.org）全局导航永远带 "Log in"，一刀切会误杀合法来源，
     改为「强特征直接 FAIL / 弱特征仅在正文过短时才 FAIL / 出现 guest access 则视为公开可读」。
