# -*- coding: utf-8 -*-
"""只读探测：拉草稿箱 10 篇的 media_id / title / thumb_media_id（F27 封面补传 TDD 红灯基线）"""
import json, os, urllib.request

def load_env(path):
    env = {}
    for line in open(path):
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env

env = load_env(os.path.expanduser('~/wechat_draft_push/accounts/mandu.env'))
APPID = env['WECHAT_APPID']
SECRET = env['WECHAT_APPSECRET']

tok = json.load(urllib.request.urlopen(
    'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential'
    f'&appid={APPID}&secret={SECRET}'))
AT = tok['access_token']

body = json.dumps({'offset': 0, 'count': 30, 'no_content': 1}).encode()
req = urllib.request.Request(
    'https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token=' + AT,
    data=body, headers={'Content-Type': 'application/json'})
r = json.load(urllib.request.urlopen(req))
print('total_count =', r.get('total_count'))
items = r.get('item', [])
print('returned =', len(items))
out = []
for it in items:
    c = it['content']['news_item'][0]
    out.append({'media_id': it['media_id'],
                'title': c.get('title'),
                'thumb': c.get('thumb_media_id', '')})
for i, o in enumerate(out, 1):
    flag = '空' if not o['thumb'] else '有'
    print(f"{i:>2}. [{flag}封面] {o['title'][:44]} | mid={o['media_id'][:22]}...")
json.dump(out, open('/tmp/draft_probe.json', 'w'), ensure_ascii=False, indent=1)
