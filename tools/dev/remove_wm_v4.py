# -*- coding: utf-8 -*-
"""
去水印 v4 · 整片纹理替换
==========================
水印位置：1760×2368 图右下角约 x:0.70-0.97, y:0.85-0.98
策略：
  1. 确定水印 ROI（右下区域）
  2. 从 ROI **正上方**取同宽 × 700px 的纹理，往下整片 blit
  3. 边界高斯羽化，避免硬接缝
特点：不做 inpaint、不靠颜色阈值，对半透明文字/装饰线条/任何图案都稳定
"""
import os, sys, glob, argparse
from PIL import Image, ImageFilter
import numpy as np


# 水印 ROI 比例（按全图归一化）
WM_RATIO = dict(
    x0=0.70, x1=0.97,    # 横向：70% 起 97% 止
    y0=0.85, y1=0.98,    # 纵向：85% 起 98% 止
    src_shift=700,      # 上方取样距离
    feather=3,           # 边界羽化像素
)


def remove_wm(im, verbose=True):
    """处理一张图，返回 Image"""
    W, H = im.size
    arr = np.asarray(im).copy()

    rx0 = int(W * WM_RATIO['x0']); rx1 = int(W * WM_RATIO['x1'])
    ry0 = int(H * WM_RATIO['y0']); ry1 = int(H * WM_RATIO['y1'])
    h_roi = ry1 - ry0
    w_roi = rx1 - rx0

    # 上方纹理源：rx0..rx1 同宽，向上 src_shift 像素起取 h_roi 高
    src_y0 = max(0, ry0 - WM_RATIO['src_shift'])
    src_y1 = src_y0 + h_roi
    if src_y1 > ry0:
        # 截短以避免与 ROI 重叠
        src_y1 = ry0
    if src_y1 - src_y0 < h_roi:
        # 上方纹理不够高，水平拼接左邻
        supplement_h = h_roi - (src_y1 - src_y0)
        # 取 ROI 左邻同 y 范围作为补丁
        left_x0 = max(0, rx0 - w_roi)
        patch = arr[src_y1 - supplement_h:src_y1, left_x0:rx0]
        top = arr[src_y0:src_y1, rx0:rx1]
        if patch.size > 0 and top.size > 0:
            src = np.vstack([patch, top])[:h_roi]
        else:
            src = top
    else:
        src = arr[src_y0:src_y1, rx0:rx1].copy()

    # 高斯羽化隐藏接缝
    src_im = Image.fromarray(src).filter(ImageFilter.GaussianBlur(radius=WM_RATIO['feather']))
    src = np.asarray(src_im)

    # 写入 ROI
    arr[ry0:ry1, rx0:rx1] = src

    if verbose:
        print(f'  替换 ROI: x:{rx0}-{rx1} y:{ry0}-{ry1} (源 y:{src_y0}-{src_y1})')

    return Image.fromarray(arr)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('inputs', nargs='+')
    p.add_argument('--out', help='输出目录')
    args = p.parse_args()

    paths = []
    for a in args.inputs:
        if os.path.isdir(a):
            paths.extend(sorted(glob.glob(f'{a}/*.png')))
        elif os.path.isfile(a):
            paths.append(a)

    for p_in in paths:
        if '-clean' in p_in or '-nowm' in p_in:
            continue
        im = Image.open(p_in).convert('RGB')
        print(f'\n[{os.path.basename(p_in)}]  {im.size}')
        out = remove_wm(im)
        if args.out:
            os.makedirs(args.out, exist_ok=True)
            base = os.path.basename(p_in).replace('.png', '-nowm.png')
            out_path = os.path.join(args.out, base)
        else:
            out_path = p_in.replace('.png', '-nowm.png')
        out.save(out_path, 'PNG')
        print(f'  → {out_path}')


if __name__ == '__main__':
    main()