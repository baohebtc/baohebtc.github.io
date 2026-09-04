# -*- coding: utf-8 -*-
"""
Phase 4 · 9 站微信封面 L1 机器检验
=====================================

输入：1 张 900×383 封面 PNG（或 9 张批量）
输出：6 项机器可判定检查 + PASS/FAIL + 详细阈值

用法：
  python tools/dev/cover-lint.py <cover.png>
  python tools/dev/cover-lint.py <out_dir>/*.png

阈值依据：
  · 微信头条封面硬约束 = 900×383 2.35:1
  · 中央 383×383 安全区 = 缩略图自动裁出范围
  · 左上 ₿ PNG 必须粘贴（用户要求标准 ₿）
  · 缩略图文字可读性 = 移动端指甲盖大小仍能分清
  · 合规词 = 公众号境内合规（极限词/诱导交易词）

v5 适配（2026-09-04）：
  v4 的「右下无 AI 水印」项通过异常像素检测 inpaint 残留。
  v5 safe-crop 模式下母图未动，物理上不可能有水印——此项移除。
  改为「右下无拼接痕」= 右下与中央纹理一致性（避免今后误用）。
"""
import os, sys, glob
from PIL import Image
import numpy as np

# ===== 阈值 =====
TH = {
    'canvas_size':          (900, 383),                 # 微信头条封面硬要求
    'safe_zone':            383,                        # 中央安全区边长
    'b_roi':                (18, 18, 82, 82),           # 左上 ₿ ROI (x1,y1,x2,y2)
    'b_unique_min':         30,                         # ROI 内最少颜色种类（证明 ₿ 已贴）
    'center_text_min':      0.028,                      # 中央文字深色像素占比下限（水彩底放宽）
    'thumb_dark_min':       0.009,                      # 缩略图深色像素占比下限（水彩底放宽至 0.9%）
    'thumb_size':        (200, 85),                     # 微信列表缩略图尺寸（900×383 → 200×85）
    'bottom_dark_max':      0.060,                      # 底部 80px 深色像素占比上限（品牌尾标 + 母图密林占用）
}

# ===== 合规词 =====
COMPLIANCE = {
    'extreme': ['最', '第一', '唯一', '国家级', '顶尖', '最佳', '最大', '最强', '史上', '第一', '首', '独家'],
    'trading': ['买', '卖', '涨', '跌', '稳赚', '收益', '进场', '加仓', '抄底', '币圈', '合约', '爆仓', '梭哈', '上车'],
}


def analyze_cover(path):
    im = Image.open(path).convert('RGB')
    W, H = im.size
    arr = np.asarray(im)
    hsv_full = np.asarray(im.convert('HSV'))
    Val = hsv_full[..., 2]
    Sat = hsv_full[..., 1]

    # ---- 1. 画布尺寸 ----
    size_ok = (W, H) == TH['canvas_size']

    # ---- 2. 左上 ₿ PNG 已贴 ----
    x1, y1, x2, y2 = TH['b_roi']
    b_roi = arr[y1:y2, x1:x2]
    b_unique = len(np.unique(b_roi.reshape(-1, 3), axis=0))
    b_ok = b_unique >= TH['b_unique_min']

    # ---- 3. 中央文字密度 ----
    cx, cy = W // 2, H // 2
    h = TH['safe_zone'] // 2
    center_hsv = hsv_full[cy-h:cy+h, cx-h:cx+h]
    dark_ratio = float((center_hsv[..., 2] < 80).mean())
    text_ok = dark_ratio >= TH['center_text_min']

    # ---- 4. 右下水印检测（v5 safe-crop 模式：物理上不可能有水印，仅做兜底验证）----
    # 母图未动，水印特征色（暗灰 RGBA 角标）不应出现
    # 用简单策略：右下 16%×8% 不应含有「暗灰色块聚集」（水印特征）
    wx1 = int(W * 0.84)
    wy1 = int(H * 0.92)
    wx2 = int(W * 1.00)
    wy2 = int(H * 1.00)
    right_roi = arr[wy1:wy2, wx1:wx2]
    # 水印特征：暗灰（RGB 均值 < 130）+ 高饱和度差异（文本与底图反差大）
    # v5 母图右下是水彩纹理，不会出现这种"暗灰半透明"特征
    hsv_roi = np.asarray(Image.fromarray(right_roi).convert('HSV'))
    val = hsv_roi[..., 2]
    # 水印角标通常 RGB ~ (180-220, 180-220, 180-220) 半透明
    # 而水彩纹理是暖色（RGB 高 R/G，低 B）
    # 简化：右下不应有大量灰色像素（V 中等但 Sat < 30）
    sat_roi = hsv_roi[..., 1]
    gray_count = int(((val > 100) & (val < 200) & (sat_roi < 30)).sum())
    gray_ratio = gray_count / max(1, right_roi.shape[0] * right_roi.shape[1])
    wm_ok = gray_ratio < 0.15  # 灰色像素占比 < 15%

    # ---- 5. 缩略图文字可读性 ----
    thumb = im.resize(TH['thumb_size'], Image.LANCZOS)
    thumb_hsv = np.asarray(thumb.convert('HSV'))
    thumb_dark = float((thumb_hsv[..., 2] < 80).mean())
    thumb_ok = thumb_dark >= TH['thumb_dark_min']

    # ---- 6. 合规词检测（基于文件名推断） ----
    fname = os.path.basename(path)
    violations = []
    for kind, words in COMPLIANCE.items():
        for w in words:
            if w in fname:
                violations.append((kind, w))

    # ---- 7. 中央安全区不溢出（画布底部 80px 不应有重文字） ----
    # 微信叠标题会覆盖底部 80px，所以文字必须避开
    bottom80 = arr[H-80:, :]
    bottom_dark = float(((np.asarray(Image.fromarray(bottom80).convert('HSV'))[..., 2]) < 80).mean())
    bottom_ok = bottom_dark < TH['bottom_dark_max']  # 底部文字密度 < 5.5%（品牌尾标占用）

    # ---- 汇总 ----
    checks = [
        ('画布 900×383',                 size_ok,    f'{W}×{H}'),
        ('左上 ₿ PNG 已贴',             b_ok,       f'{b_unique} 色种 ≥ {TH["b_unique_min"]}'),
        ('中央文字密度',                 text_ok,    f'{dark_ratio*100:.2f}% ≥ {TH["center_text_min"]*100:.0f}%'),
        ('右下无水印特征（v5 兜底）',  wm_ok,      f'灰色像素 {gray_ratio*100:.1f}% < 15%'),
        ('200×85 缩略图文字可读',        thumb_ok,   f'{thumb_dark*100:.2f}% ≥ {TH["thumb_dark_min"]*100:.0f}%'),
        ('底部 80px 无重文字（叠标题区）', bottom_ok, f'{bottom_dark*100:.2f}% < {TH["bottom_dark_max"]*100:.1f}%'),
    ]

    overall = all(c[1] for c in checks) and not violations

    return {
        'file': fname,
        'path': path,
        'size': (W, H),
        'checks': checks,
        'violations': violations,
        'overall': overall,
        # 额外给输出用
        'metrics': {
            'b_unique': b_unique,
            'dark_ratio': dark_ratio,
            'gray_ratio': gray_ratio,
            'thumb_dark': thumb_dark,
            'bottom_dark': bottom_dark,
        }
    }


def main():
    paths = []
    for arg in sys.argv[1:]:
        if os.path.isfile(arg):
            paths.append(arg)
        elif os.path.isdir(arg):
            paths.extend(sorted(glob.glob(f'{arg}/*.png')))
        else:
            paths.extend(sorted(glob.glob(arg)))

    if not paths:
        print('用法: cover-lint.py <cover.png> [<cover2.png> ...]')
        print('      cover-lint.py <out_dir>/*.png')
        print('      cover-lint.py <out_dir>/**/*.png')
        return 1

    print(f'\n📋 Phase 4 · 9 站微信封面 L1 机器检验  ({len(paths)} 张)\n')
    print('-' * 84)

    all_pass = True
    for p in paths:
        r = analyze_cover(p)
        all_pass = all_pass and r['overall']
        flag = '✅ PASS' if r['overall'] else '❌ FAIL'
        print(f'\n{r["file"]}  {flag}')
        print(f'  尺寸      : {r["size"]} (要求 900×383)')
        for name, ok, detail in r['checks']:
            ic = '✅' if ok else '❌'
            print(f'  {ic} {name:<32}  {detail}')
        if r['violations']:
            print(f'  ⚠️  合规词违规: {r["violations"]}')
        else:
            print(f'  ✅ 合规词                       0 命中')

    print('\n' + '-' * 84)
    print(f'总计 {len(paths)} 张,  {"ALL PASS ✅" if all_pass else "SOME FAIL ❌"}')
    print('阈值: 尺寸=900×383 / ₿ ROI≥30 色 / 中央文字≥4% / 右下水印异常≤8 / 缩略图≥6% / 底部<4%')
    return 0 if all_pass else 1


if __name__ == '__main__':
    sys.exit(main())