# -*- coding: utf-8 -*-
"""
渲染「带标签」母图 PNG —— 图片产品线（公众号配图 / 视频片头尾 / 社媒分享卡）。

为什么与网站 SVG 分开两条链路：
    网站用「无标签底图 + SVG 标签层」，因为标签要能 hover、能中英切换、能小屏让位、
    能挂已读状态——烧进像素里就全没了。但公众号和视频要的就是一张成品图，
    所以这里单独出图。两条链路读同一份 map-stations.json，保证长相一致。

风格：A 羊皮纸牌（用户 2026-09-10 选定）
   米色半透明底 + 深棕细边 + 深棕字，像贴在古地图上的标签牌。

产物：
   assets/learning-map/v3.3-地图-10站立体-带标签-1760x2368.png   竖版成品
   assets/learning-map/v3.3-地图-横版片头-1760x990.png           横版裁切（视频片头尾）

用法：python3 tools/dev/render_map_labels.py
"""
import json, pathlib
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent.parent
SRC = ROOT / "assets/learning-map/v3.3-地图-10站立体-1760x2368.png"
OUT_DIR = ROOT / "assets/learning-map"
JSON_PATH = HERE / "map-stations.json"
FONT_PATH = "/System/Library/Fonts/PingFang.ttc"

C_FILL = (245, 235, 214, 236)     # 羊皮纸底
C_EDGE = (92, 64, 40)             # 深棕边
C_TEXT = (58, 40, 24)             # 深棕字
C_TEXT_MID = (118, 86, 54)        # 视角小字
C_WHITE = (255, 255, 255)
C_STROKE = (48, 32, 18)

# 横版裁切：覆盖站点最多的带状区（8 站：9/8/6/5/7/4/2/3）
# 下边界必须 > 站3 圆点下缘 1121+38=1159，否则站3 标签指向一个不存在的圆点
CROP = (0, 130, 1760, 1160)

# srcset 档位（无标签底图，给网站响应式用）
SRCSET = [880, 1320, 1760]


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def font(size):
    return ImageFont.truetype(FONT_PATH, size)


def draw_labels(im, stations, P):
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f_cn, f_view, f_num = font(P["font_cn"]), font(P["font_view"]), font(P["font_num"])
    R = P["dot_r"]

    for L in stations:
        cx, cy = L["cx"], L["cy"]
        bx, by, bw, bh = L["x"], L["y"], L["w"], L["h"]
        bcx = bx + bw / 2
        col = hex2rgb(L["color"])

        # 引线：圆点边缘 → 框近边中点
        if L["dir"].startswith("上"):   p0, p1 = (cx, cy - R), (cx, by + bh)
        elif L["dir"].startswith("下"): p0, p1 = (cx, cy + R), (cx, by)
        elif L["dir"].startswith("右"): p0, p1 = (cx + R, cy), (bx, cy)
        else:                           p0, p1 = (cx - R, cy), (bx + bw, cy)
        d.line([p0, p1], fill=C_STROKE + (150,), width=3)

        # 羊皮纸牌
        d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=16,
                            fill=C_FILL, outline=C_EDGE, width=3)
        tb = d.textbbox((0, 0), L["name"], font=f_cn)
        vb = d.textbbox((0, 0), L["view"], font=f_view)
        d.text((bcx - (tb[2] - tb[0]) / 2 - tb[0], by + 14 - tb[1]),
               L["name"], font=f_cn, fill=C_TEXT)
        d.text((bcx - (vb[2] - vb[0]) / 2 - vb[0], by + 62 - vb[1]),
               L["view"], font=f_view, fill=C_TEXT_MID)

        # 序号圆点
        d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=col, outline=C_WHITE, width=4)
        nb = d.textbbox((0, 0), L["num"], font=f_num)
        d.text((cx - (nb[2] - nb[0]) / 2 - nb[0], cy - (nb[3] - nb[1]) / 2 - nb[1]),
               L["num"], font=f_num, fill=(14, 8, 5))

    return Image.alpha_composite(im, layer).convert("RGB")


if __name__ == "__main__":
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    stations, P = data["stations"], data["params"]

    bad = [s["num"] for s in stations if s["dir"].startswith("下")]
    assert not bad, f"❌ 有站名落在站号下方：{bad}"

    im = Image.open(SRC).convert("RGBA")
    out = draw_labels(im, stations, P)

    p1 = OUT_DIR / "v3.3-地图-10站立体-带标签-1760x2368.png"
    out.save(p1, optimize=True)
    print(f"✅ 竖版成品 {p1.name}  {out.size}  {p1.stat().st_size/1024/1024:.2f}MB")

    # 量化版：PNG-256 FASTOCTREE，视觉近无损（实测 PSNR≈37dB），体积约降 70%，便于传播
    p1q = OUT_DIR / "v3.3-地图-10站立体-带标签-1760x2368-q256.png"
    out.quantize(colors=256, method=Image.FASTOCTREE).save(p1q, optimize=True)
    print(f"✅ 竖版量化 {p1q.name}  {p1q.stat().st_size/1024/1024:.2f}MB（传播用）")

    p2 = OUT_DIR / f"v3.3-地图-横版-{CROP[2]}x{CROP[3]-CROP[1]}.png"
    out.crop(CROP).save(p2, optimize=True)
    in_crop = [s["num"] for s in stations
               if CROP[1] <= s["cy"] - P["dot_r"] and s["cy"] + P["dot_r"] <= CROP[3]
               and CROP[1] <= s["y"] and s["y"] + s["h"] <= CROP[3]]
    print(f"✅ 横版裁切 {p2.name}  {Image.open(p2).size}  "
          f"完整含 {len(in_crop)} 站：{'、'.join(in_crop)}")

    # 横版小图：首页入口卡片用，别让首页为了一张入口图扛 2MB
    crop = out.crop(CROP)
    p3 = OUT_DIR / "v3.3-地图-横版-880w.png"
    crop.resize((880, round(880 * crop.height / crop.width)), Image.LANCZOS).quantize(
        colors=256, method=Image.FASTOCTREE).save(p3, optimize=True)
    print(f"✅ 横版小图 {p3.name}  {Image.open(p3).size}  {p3.stat().st_size/1024/1024:.2f}MB（首页入口）")
    base = Image.open(SRC).convert("RGB")
    for w in SRCSET:
        if w >= base.width:
            continue
        h = round(base.height * w / base.width)
        p = OUT_DIR / f"v3.3-地图-10站立体-{w}w.png"
        # 必须量化：LANCZOS 插值会生成大量新颜色，直接存反而比原图更大
        base.resize((w, h), Image.LANCZOS).quantize(
            colors=256, method=Image.FASTOCTREE).save(p, optimize=True)
        print(f"✅ srcset {p.name}  {w}x{h}  {p.stat().st_size/1024/1024:.2f}MB")
