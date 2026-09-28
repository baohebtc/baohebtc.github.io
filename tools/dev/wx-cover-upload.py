# -*- coding: utf-8 -*-
"""
F27 · 草稿封面补传（ADR-0016 确诊：10/10 草稿 thumb_media_id 为空）
================================================================
为什么需要它：publish_locally.py 用 media/uploadimg 传封面（临时 URL），
而草稿封面字段要的是**永久素材 media_id**（material/add_material?type=image）。
两类素材不通 → 封面一直是空的。

做法（三步，不新建草稿、media_id 不变）：
  1. draft/batchget（no_content=0）拉**完整**草稿 → 备份到 /tmp/draft_backup.json
  2. material/add_material?type=image 上传封面 → 拿到永久 media_id
  3. draft/update 原样回填整篇 + 新 thumb_media_id
     ⚠️ draft/update 的 articles 是**完整对象**，缺字段会被置空 → 必须整篇原样回传

用法（服务器 ~/mandu_push/ 下）：
  python3 wx_cover_upload.py --only 站1      # 单篇试点
  python3 wx_cover_upload.py                 # 全量 10 篇
  python3 wx_cover_upload.py --dry-run       # 只打印不写
"""
import argparse, json, os, sys, urllib.request, urllib.parse, mimetypes, uuid

ENV_PATH = os.path.expanduser('~/wechat_draft_push/accounts/mandu.env')
COVER_ROOT = os.path.expanduser('~/mandu_push')
MAP_PATH = os.path.expanduser('~/mandu_push/cover_map.json')
BACKUP_PATH = '/tmp/draft_backup.json'


def load_env(path):
    env = {}
    for line in open(path):
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def post_json(url, payload):
    data = json.dumps(payload, ensure_ascii=False).encode()
    req = urllib.request.Request(url, data=data,
                                 headers={'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req))


def upload_material(AT, path):
    """material/add_material?type=image —— multipart/form-data"""
    url = ('https://api.weixin.qq.com/cgi-bin/material/add_material'
           f'?access_token={AT}&type=image')
    boundary = uuid.uuid4().hex
    fn = os.path.basename(path)
    with open(path, 'rb') as f:
        content = f.read()
    body = b''
    body += f'--{boundary}\r\n'.encode()
    body += (f'Content-Disposition: form-data; name="media"; filename="{fn}"\r\n').encode()
    body += b'Content-Type: image/png\r\n\r\n'
    body += content + b'\r\n'
    body += f'--{boundary}--\r\n'.encode()
    req = urllib.request.Request(
        url, data=body,
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
    return json.load(urllib.request.urlopen(req))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default=None, help='只处理某一站（如 站1）')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    env = load_env(ENV_PATH)
    AT = json.load(urllib.request.urlopen(
        'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential'
        f"&appid={env['WECHAT_APPID']}&secret={env['WECHAT_APPSECRET']}"))['access_token']

    cmap = json.load(open(MAP_PATH))          # [{"station","title","cover"}...]
    r = post_json('https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token=' + AT,
                  {'offset': 0, 'count': 30, 'no_content': 0})
    items = r.get('item', [])
    json.dump(items, open(BACKUP_PATH, 'w'), ensure_ascii=False, indent=1)
    print(f'草稿 {len(items)} 篇，已备份 → {BACKUP_PATH}')

    title2mid = {it['content']['news_item'][0]['title']: it['media_id'] for it in items}
    title2item = {it['content']['news_item'][0]['title']: it for it in items}

    ok, fail = [], []
    for row in cmap:
        st, title, cov = row['station'], row['title'], row['cover']
        if args.only and st != args.only:
            continue
        if title not in title2item:
            fail.append((st, '标题未匹配到草稿'))
            continue
        path = os.path.join(COVER_ROOT, cov)
        if not os.path.exists(path):
            fail.append((st, f'封面文件缺失 {path}'))
            continue
        it = title2item[title]
        art = dict(it['content']['news_item'][0])
        if args.dry_run:
            print(f'[dry] {st} → {cov}')
            ok.append(st)
            continue

        up = upload_material(AT, path)
        if 'media_id' not in up:
            fail.append((st, f"上传失败 {up}"))
            continue
        thumb = up['media_id']
        art['thumb_media_id'] = thumb
        # draft/update 只接受这些字段
        allowed = ('title', 'author', 'digest', 'content', 'content_source_url',
                   'thumb_media_id', 'need_open_comment', 'only_fans_can_comment',
                   'pic_crop_235_1', 'pic_crop_1_1')
        art = {k: v for k, v in art.items() if k in allowed}
        res = post_json('https://api.weixin.qq.com/cgi-bin/draft/update?access_token=' + AT,
                        {'media_id': it['media_id'], 'index': 0, 'articles': art})
        if res.get('errcode'):
            fail.append((st, f"update 失败 {res}"))
            continue
        ok.append(st)
        print(f'✅ {st:<14} thumb={thumb[:26]}…')

    print(f'\n补传完成：成功 {len(ok)} / 失败 {len(fail)}')
    for f in fail:
        print('  ❌', f)
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main())
