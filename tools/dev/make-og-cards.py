#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make-og-cards.py —— 生成社交分享卡（OG image，1200×630）（F46 · ADR-0027）

为什么要有自己的卡：
  分享到微信 / X / Telegram 时，og:image 就是别人看到的第一眼。
  全站此前 0 张 → 分享出去只有一个裸链接。

设计约束：
  · 尺寸 1200×630（1.91:1，OG 推荐规格；seo-check C5 校验 ≥600 宽且横向）
  · 色板取 brand_figs 的 warm-dark（与封面 #1F150B 同源，深色是封面专属符号）
  · ₿ 只准官方标准件（ADR-0006），走 bf.btc() 贴 assets/brand/btc-emblem-official.png
  · 文案**零现编**：站名与副标全部从已上线的 series/*.html 的 <title> 解析
    （格式「站名：副标 · 慢读连载 · 比特币学习地图」），保证与页面一致
  · 底栏沿用 ADR-0009 定稿文案：左品牌系别 / 右「科普内容 · 不构成投资建议」

产出：
  assets/brand/og-site-1200x630.png          站点默认卡（非连载页共用）
  assets/series/<slug>/og-1200x630.png       十站各一张

用法：
  python3 tools/dev/make-og-cards.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import brand_figs as bf
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERIES = os.path.join(ROOT, "series")
W, H = 1200, 630

TH = bf.Theme("warm-dark")
BRAND_LINE = "慢读宝盒 · 宝盒比特币 · 学习连载"
COMPLIANCE = "科普内容 · 不构成投资建议"
BRAND_SUB = "慢读宝盒 · 宝盒比特币"


def _new():
    im = Image.new("RGB", (W, H), TH.BG)
    return im, ImageDraw.Draw(im)


def _footer(im, d):
    """底栏：左品牌系别 / 右合规短句（与 brand_figs.canvas 同构）。"""
    fy = H - 62
    d.rectangle([0, fy, W, H], fill=TH.FOOTBAR)
    d.line([0, fy, W, fy], fill=TH.EDGE, width=2)
    d.text((72, fy + 31), BRAND_LINE, font=bf.font(19), fill=TH.MID, anchor="lm")
    d.text((W - 72, fy + 31), COMPLIANCE, font=bf.font(19), fill=TH.MID, anchor="rm")


def _chip(d, x, y, text):
    """橙色胶囊（站号）。返回右边界 x。"""
    f = bf.font(22, True)
    tw = d.textlength(text, font=f)
    pad_x, pad_y = 18, 9
    d.rounded_rectangle([x, y, x + tw + pad_x * 2, y + 22 + pad_y * 2],
                        radius=14, fill=TH.ACCENT)
    d.text((x + pad_x, y + pad_y + 11), text, font=f, fill=(26, 17, 8), anchor="lm")
    return x + tw + pad_x * 2


def _wrap(d, text, x, y, maxw, font_, fill, lh, max_lines=2):
    """贪心折行（中文按字断行即可）。返回终 y。"""
    line = ""
    n = 0
    for ch in text:
        if d.textlength(line + ch, font=font_) > maxw:
            d.text((x, y), line, font=font_, fill=fill, anchor="lm")
            y += lh
            n += 1
            line = ch
            if n == max_lines - 1:
                continue
            if n >= max_lines:
                break
        else:
            line += ch
    if line and n < max_lines:
        d.text((x, y), line, font=font_, fill=fill, anchor="lm")
        y += lh
    return y


def site_card(out):
    im, d = _new()
    d.text((72, 96), BRAND_SUB, font=bf.font(24), fill=TH.MID, anchor="lm")
    d.text((72, 190), "比特币学习地图", font=bf.font(72, True), fill=TH.TXT, anchor="lm")
    _wrap(d, "六个视角理解比特币 · 十站慢读连载 · 交互工具与精选文集",
          72, 300, 640, bf.font(28), TH.MID, 46, max_lines=2)
    d.text((72, 430), "从「钱到底是什么」一路走到「代码之巅」",
           font=bf.font(26), fill=TH.GOLD, anchor="lm")
    bf.btc(d, im, 950, 300, 300)
    _footer(im, d)
    bf.save(im, out)
    return out


def series_card(slug, station, seq, sub, out):
    im, d = _new()
    d.text((72, 92), BRAND_SUB, font=bf.font(24), fill=TH.MID, anchor="lm")
    _chip(d, 72, 138, seq)
    _wrap(d, station, 72, 218, 660, bf.font(66, True), TH.TXT, 82, max_lines=2)
    if sub:
        _wrap(d, sub, 72, 330, 660, bf.font(28), TH.MID, 44, max_lines=2)
    bf.btc(d, im, 950, 300, 300)
    _footer(im, d)
    bf.save(im, out)
    return out


def parse_series_meta(slug):
    """从已上线页面解析站名与副标（零现编）。分隔符：：或｜。"""
    p = os.path.join(SERIES, slug + ".html")
    if not os.path.isfile(p):
        return None, ""
    html = open(p, encoding="utf-8").read()
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    if not m:
        return None, ""
    title = re.sub(r"\s+", " ", m.group(1)).strip()
    title = title.split(" · ")[0]               # 去掉「慢读连载 · 比特币学习地图」后缀
    title = title.replace("&quot;", '"').replace("&amp;", "&")
    for sep in ("：", "｜"):
        if sep in title:
            station, sub = title.split(sep, 1)
            return station.strip(), sub.strip()
    return title.strip(), ""


def main():
    made = []

    # 1) 站点默认卡
    made.append(site_card(os.path.join(ROOT, "assets/brand/og-site-1200x630.png")))

    # 2) 十站连载卡（从 make_series_pages.py 用 ast 安全取 STATIONS）
    import ast
    src = open(os.path.join(ROOT, "tools/dev/make_series_pages.py"),
               encoding="utf-8").read()
    i = src.index("STATIONS = [")
    j = src.index("]", i)
    stations = ast.literal_eval(src[i + len("STATIONS = "): j + 1])
    assert len(stations) == 10, f"STATIONS 应 10 站，实得 {len(stations)}"

    for row in stations:
        _dir, slug, station, seq = row[0], row[1], row[2], row[3]
        st, sub = parse_series_meta(slug)
        station = st or station                     # 以页面 title 为准（单源）
        chip = seq.replace("第 ", "").replace(" 站", "")   # 「第 8 站」→ 8
        out = os.path.join(ROOT, "assets/series", slug, "og-1200x630.png")
        made.append(series_card(slug, station, chip, sub[:44], out))

    print(f"✅ 生成 {len(made)} 张 OG 卡（1200×630）")
    for m in made:
        print("   ", os.path.relpath(m, ROOT), f"{os.path.getsize(m)//1024}KB")


if __name__ == "__main__":
    main()
