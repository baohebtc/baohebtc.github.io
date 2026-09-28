# -*- coding: utf-8 -*-
"""F27 安全阀：比对站1 草稿 update 前后的正文是否完好（内容长度 / 图片数 / 标题）"""
import json, os, re, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wx_cover_upload import load_env, post_json, ENV_PATH

env = load_env(ENV_PATH)
AT = json.load(urllib.request.urlopen(
    'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential'
    f"&appid={env['WECHAT_APPID']}&secret={env['WECHAT_APPSECRET']}"))['access_token']

old = json.load(open('/tmp/draft_backup.json'))
now = post_json('https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token=' + AT,
                {'offset': 0, 'count': 30, 'no_content': 0})['item']

old_map = {it['media_id']: it['content']['news_item'][0] for it in old}
bad = 0
for it in now:
    mid = it['media_id']
    a = it['content']['news_item'][0]
    o = old_map.get(mid)
    if o is None:
        continue
    if not o.get('thumb_media_id'):          # 只校验「本次动过」的篇
        if a.get('thumb_media_id'):
            continue
        else:
            continue
    # 本次补传过的篇：逐项比对
    checks = [
        ('标题', o['title'] == a['title']),
        ('正文长度', len(o['content']) == len(a['content'])),
        ('图片数', len(re.findall(r'mmbiz\.qpic\.cn', o['content']))
                  == len(re.findall(r'mmbiz\.qpic\.cn', a['content']))),
        ('摘要', (o.get('digest') or '') == (a.get('digest') or '')),
    ]
    n_img = len(re.findall(r'mmbigx\.qpic|mmbiz\.qpic\.cn', a['content']))
    print(f"\n[{a['title'][:26]}] 正文 {len(a['content'])} 字 / 图 {n_img} 张 / thumb "
          f"{'非空' if a.get('thumb_media_id') else '空'}")
    for name, ok in checks:
        print(f"   {'✅' if ok else '❌'} {name}")
        if not ok:
            bad += 1

print('\n结论：正文与标题' + ('完好 ✅' if bad == 0 else f'受损 ❌（{bad} 项）'))
sys.exit(1 if bad else 0)
