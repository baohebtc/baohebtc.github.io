#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
station-kit-check.py — 站点六件套门闸（ADR-0010 配套，new in 2026-09-20）

为什么要有：配图/排版/图文表都有门闸，但「这一站到底齐没齐」没人管——
站6 开工时目录全空，任何单篇门闸都跑不到它（文件不存在即跳过）。
本门闸按站目录扫描，保证连载每一站都具备可发布的最小资产集。

规则（🔴 硬项，任一不满足即红灯）：
  K1 文章    02-文章/*微信版.md 存在且唯一
  K2 封面    04-封面/封面-站N-v8-900x383.png 存在
  K3 回扣图  03-配图/寻宝路线-站N-v3.png 存在
  K4 配图数  03-配图/ 下 PNG ≥ 3 张（回扣图 + 正文图）
  K5 发布    已推送的站必须有 05-发布/推送记录.md 且含 media_id
软项（🟡 只报告）：
  K6 序号对齐 文件名前缀序号 == 图注编号（mindmap / 回扣图豁免，规范 §2.2）

用法：python3 station-kit-check.py [站目录名，如 站6-共识峰]
退出码：0 全绿 / 1 有红灯
"""
import re
import sys
import pathlib

ROOT = pathlib.Path("/Users/mac/Desktop/宝盒知识库/比特币学习地图/慢读宝盒公众号")

# 豁免 K6 的文件（回扣图按站号命名；mindmap 固定 07 为历史先例）
EXEMPT_K6 = re.compile(r"(寻宝路线-|mindmap)")


def station_num(dirname: str) -> str:
    m = re.match(r"站([\d.]+)", dirname)
    return m.group(1) if m else ""


def check_station(station_dir: pathlib.Path):
    name = station_dir.name
    num = station_num(name)
    reds, ambers = [], []

    arts = sorted((station_dir / "02-文章").glob("*微信版.md"))
    if len(arts) == 0:
        reds.append("K1 缺微信版文章")
    elif len(arts) > 1:
        reds.append(f"K1 微信版文章不唯一（{len(arts)} 个）")
    art = arts[0] if len(arts) == 1 else None

    cover = station_dir / "04-封面" / f"封面-站{num}-v8-900x383.png"
    if not cover.exists():
        reds.append("K2 缺封面 v8")

    route = station_dir / "03-配图" / f"寻宝路线-站{num}-v3.png"
    if not route.exists():
        reds.append("K3 缺回扣图 v3")

    pngs = sorted(p for p in (station_dir / "03-配图").glob("*.png")
                  if not p.name.startswith("_"))
    if len(pngs) < 3:
        reds.append(f"K4 配图不足（{len(pngs)} 张，需 ≥3）")

    rec = station_dir / "05-发布" / "推送记录.md"
    if rec.exists():
        t = rec.read_text(encoding="utf-8")
        if "media_id" not in t:
            reds.append("K5 推送记录缺 media_id")
    else:
        ambers.append("K5 未推送（无推送记录）")

    # K6 序号对齐（软）
    if art:
        md = art.read_text(encoding="utf-8")
        for m in re.finditer(r"!\[图\s*(\d+)[：:][^\]]*\]\(\.\./03-配图/([^)]+)\)", md):
            caption_no, fname = int(m.group(1)), m.group(2)
            if EXEMPT_K6.search(fname):
                continue
            fm = re.match(r"(\d+)[-_]", fname)
            if not fm:
                ambers.append(f"K6 文件名无序号：{fname}")
            elif int(fm.group(1)) != caption_no:
                ambers.append(f"K6 序号不符：图{caption_no} → {fname}")

    return name, reds, ambers


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    dirs = sorted(d for d in ROOT.iterdir() if d.is_dir() and d.name.startswith("站"))
    if only:
        dirs = [d for d in dirs if only in d.name]

    total_red = 0
    print("站点六件套门闸（station-kit-check）")
    print("=" * 62)
    for d in dirs:
        name, reds, ambers = check_station(d)
        flag = "🔴" if reds else ("🟡" if ambers else "🟢")
        print(f"{flag} {name}")
        for r in reds:
            print(f"     🔴 {r}")
        for a in ambers:
            print(f"     🟡 {a}")
        total_red += len(reds)
    print("=" * 62)
    if total_red:
        print(f"❌ 红灯 {total_red} 项")
        return 1
    print("✅ 全绿（无红灯）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
