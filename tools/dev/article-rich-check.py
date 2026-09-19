# -*- coding: utf-8 -*-
"""
article-rich-check.py — 「图文表并茂」门闸（ADR-0009）
======================================================
每篇微信版文章必须满足：
  R1 配图 >= 2 张（含回扣图）
  R2 表格 >= 1 个
  R3 类比块 >= 2 个（✅ **像的地方** 格式）

用法：
    python3 article-rich-check.py                 # 检查全部
    python3 article-rich-check.py 站1-现金湾       # 只查一站（站名子串匹配）

退出码：0 = 全绿；1 = 有 FAIL。
"""
import re
import sys
import glob
import os

BASE = "/Users/mac/Desktop/宝盒知识库/比特币学习地图/慢读宝盒公众号"

# R1: markdown 图片
RE_IMG = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
# R3: 类比块（容错：✅ 与 **像的地方** 之间可有空格）
RE_ANALOGY = re.compile(r"✅\s*\*{0,2}\s*像的地方\*{0,2}")


def check_md(path):
    t = open(path, encoding="utf-8").read()
    lines = t.split("\n")

    imgs = RE_IMG.findall(t)

    # 表格计数：连续以 | 开头的行块
    tables = 0
    in_t = False
    for ln in lines:
        if ln.strip().startswith("|"):
            if not in_t:
                tables += 1
                in_t = True
        else:
            in_t = False

    analogies = len(RE_ANALOGY.findall(t))

    checks = {
        "R1 配图>=2": (len(imgs) >= 2, f"{len(imgs)}张"),
        "R2 表格>=1": (tables >= 1, f"{tables}个"),
        "R3 类比块>=2": (analogies >= 2, f"{analogies}个"),
    }
    return checks, {"imgs": len(imgs), "tables": tables, "analogies": analogies}


def main():
    sub = sys.argv[1] if len(sys.argv) > 1 else ""
    mds = sorted(glob.glob(os.path.join(BASE, "站*/02-文章/*微信版.md")))
    mds = [m for m in mds if sub in m]
    if not mds:
        print(f"未找到匹配的文章: {sub}")
        return 1

    n_fail = 0
    print(f'{"文章":34s} R1配图  R2表格  R3类比')
    for md in mds:
        station = os.path.basename(os.path.dirname(os.path.dirname(md)))
        checks, n = check_md(md)
        cells = []
        for name, (ok, detail) in checks.items():
            mark = "PASS" if ok else "FAIL"
            if not ok:
                n_fail += 1
            cells.append(f"{mark}({detail})")
        print(f"{station:36s} " + "  ".join(cells))

    print()
    if n_fail:
        print(f"🔴 红灯：{n_fail} 项未达标")
        return 1
    print("🟢 全绿：图文表并茂达标")
    return 0


if __name__ == "__main__":
    sys.exit(main())
