# -*- coding: utf-8 -*-
"""
fig-glyph-check.py — 配图字形门闸（ADR-0014 P2）
==================================================
静态扫描全部配图产线脚本，两类检测：

  G1  PingFang 缺字形：把源码里的字符串常量逐字符用 PIL 实际渲染，
      与 .notdef（豆腐块）基准比对 —— 与基准相同或无墨迹 → 缺字。
      （不用 fontTools 的 cmap：AAT 字体渲染时有 fallback 机制，
       cmap 查询会大量误报——「远」「杂」被误判的教训，2026-09-27）
  G2  fmono(...) 实参含 CJK：Menlo 无中文字形，中文进 fmono 必然豆腐块
      （站4 图6「hash:篡改!」曾中招，2026-09-27 已修）。

已知限制：抓不到「cmap 有、单字渲染正常、句中被吞」的字（如「稳」，
见用户级记忆 2026-09-21）——该类问题只能逐字眼验兜底。

用法：
    python3 tools/dev/fig-glyph-check.py            # 全部产线
    python3 tools/dev/fig-glyph-check.py 站9        # 单站
"""
from __future__ import annotations
import ast, pathlib, sys

from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[2]
DEV = ROOT / "tools" / "dev"

PRODUCERS = {
    "站1": "make_s13_figs_light.py", "站1.5": "make_s13_figs_light.py",
    "站2": "make_s2_figs_light.py", "站3": "make_s13_figs_light.py",
    "站4": "make_s45_figs_light.py", "站5": "make_s45_figs_light.py",
    "站6": "make_s6_figs_light.py", "站7": "make_s7_figs_light.py",
    "站8": "make_s8_figs_light.py", "站9": "make_s9_figs_light.py",
}

PINGFANG = "/System/Library/Fonts/PingFang.ttc"


def strings_from(src, func_name=None):
    """func_name=None 取全部字符串常量；否则只取该函数调用的实参"""
    tree = ast.parse(src)
    out = []
    for node in ast.walk(tree):
        if func_name is None:
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                out.append(node.value)
        elif isinstance(node, ast.Call):
            f = node.func
            name = f.id if isinstance(f, ast.Name) else (
                f.attr if isinstance(f, ast.Attribute) else "")
            if name == func_name:
                for a in node.args:
                    if isinstance(a, ast.Constant) and isinstance(a.value, str):
                        out.append(a.value)
    return out


_RENDER_CACHE = {}


def glyph_missing(f, ch):
    """True = 该字符在此 face 下渲染为豆腐块/空白"""
    key = (id(f), ch)
    if key in _RENDER_CACHE:
        return _RENDER_CACHE[key]
    im1 = Image.new("L", (52, 52), 255)
    ImageDraw.Draw(im1).text((4, 4), ch, font=f, fill=0)
    im2 = Image.new("L", (52, 52), 255)
    ImageDraw.Draw(im2).text((4, 4), "\uE01F", font=f, fill=0)   # PUA → .notdef 基准
    miss = (im1.getbbox() is None) or (ImageChops.difference(im1, im2).getbbox() is None)
    _RENDER_CACHE[key] = miss
    return miss


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    targets = PRODUCERS
    if arg:
        if arg in PRODUCERS:
            targets = {arg: PRODUCERS[arg]}
        else:
            targets = {k: v for k, v in PRODUCERS.items() if v == arg}

    faces = [ImageFont.truetype(PINGFANG, 40, index=i) for i in (0, 2)]  # HK/SC 并测

    bad = 0
    for st in sorted(targets):
        f = DEV / targets[st]
        src = f.read_text(encoding="utf-8")
        g1 = sorted({ch for s in strings_from(src) for ch in s
                     if ord(ch) > 0x7E and not ch.isspace()
                     and all(glyph_missing(fa, ch) for fa in faces)})
        g2 = sorted({ch for s in strings_from(src, "fmono") for ch in s
                     if ord(ch) > 0x2E7F and not ch.isspace()})
        problems = []
        if g1:
            problems.append(f"G1 PingFang豆腐块: {''.join(g1)}")
        if g2:
            problems.append(f"G2 fmono含CJK: {''.join(g2)}")
        print(f"{st:<8}{targets[st]:<28}{'；'.join(problems) if problems else 'ok'}")
        bad += bool(problems)

    print()
    print(f"结论：{len(targets)} 个产线，{bad} 个有字形风险")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
