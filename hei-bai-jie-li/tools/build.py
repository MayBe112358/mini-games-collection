"""把 tiers.json 填进 template.html。每关带固定 ID（由关卡内容算出），存档按 ID 记录。"""
import json, sys

def level_id(l):
    s = f"{l['w']}|{l['h']}|{l['c']}|{l['bs']}|{l['ws']}|{l['bg']}|{l['wg']}|{','.join(map(str, l['st']))}"
    h = 2166136261
    for ch in s.encode():
        h = ((h ^ ch) * 16777619) & 0xffffffff
    n, out = h, ''
    while True:
        n, r = divmod(n, 36); out = '0123456789abcdefghijklmnopqrstuvwxyz'[r] + out
        if n == 0: break
    return 'L' + out

T = json.load(open('tiers.json'))
out, ids = [], set()
for t in T:
    lv = []
    for l in t['levels']:
        d = {k: l[k] for k in ('w', 'h', 'c', 'bs', 'ws', 'bg', 'wg')} | {'st': l['st'], 'L': l['L'], 'id': level_id(l)}
        assert d['id'] not in ids, '重复关卡 ' + d['id']
        ids.add(d['id']); lv.append(d)
    out.append(dict(name=t['name'], desc=t['desc'], levels=lv))
# 250 关首版的顺序，用于把旧存档（档-序号）迁移成 ID；之后不要改这个文件
old = json.load(open('old_order_v1.json'))
html = open('template.html').read()
html = html.replace('__TIERS__', json.dumps(out, ensure_ascii=False, separators=(',', ':')))
html = html.replace('__OLD_ORDER__', json.dumps(old, separators=(',', ':')))
open(sys.argv[1] if len(sys.argv) > 1 else 'index.html', 'w').write(html)
print(len(html), 'bytes,', len(ids), 'levels')
