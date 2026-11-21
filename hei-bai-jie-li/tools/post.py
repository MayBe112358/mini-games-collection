"""汇总生成结果：去掉走不到的格子、裁边、去重（含旋转翻转）、计算难度"""
import json, glob

def crop(r):
    w, h = r['w'], r['h']
    c = [ch if r['vis'][i] == '1' else '#' for i, ch in enumerate(r['c'])]
    xs = [i % w for i in range(w * h) if c[i] != '#']
    ys = [i // w for i in range(w * h) if c[i] != '#']
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    nw, nh = x1 - x0 + 1, y1 - y0 + 1
    m = lambda i: (i // w - y0) * nw + (i % w - x0)
    nc = ''.join(c[(y + y0) * w + (x + x0)] for y in range(nh) for x in range(nw))
    o = dict(w=nw, h=nh, c=nc, bs=m(r['bs']), ws=m(r['ws']), bg=m(r['bg']), wg=m(r['wg']),
             st=[m(s) for s in r['st']])
    for k in ('L', 'L0', 'crit', 'good', 'states', 'path'):
        o[k] = r[k]
    return o

def tokens(o):
    t = list(o['c'])
    for k, ch in (('bs', 'B'), ('ws', 'W'), ('bg', 'G'), ('wg', 'H')):
        t[o[k]] += ch
    for s in o['st']:
        t[s] += '*'
    return t

def canon(o):
    w, h, t = o['w'], o['h'], tokens(o)
    grid = [[t[y * w + x] for x in range(w)] for y in range(h)]
    keys = []
    g = grid
    for _ in range(4):
        g = [list(r) for r in zip(*g[::-1])]  # 旋转 90°
        for gg in (g, [r[::-1] for r in g]):
            keys.append('/'.join('|'.join(r) for r in gg))
    return min(keys)

def load():
    seen, out = set(), []
    for f in sorted(glob.glob('pool/g_*.jsonl')):
        for line in open(f):
            try:
                r = json.loads(line)
            except ValueError:
                continue  # 生成中途的半行
            o = crop(r)
            if o['w'] < 2 or o['h'] < 2:
                continue
            k = canon(o)
            if k in seen:
                continue
            seen.add(k)
            o['area'] = sum(ch != '#' for ch in o['c'])
            out.append(o)
    return out

if __name__ == '__main__':
    import collections
    L = load()
    print('unique', len(L))
    for key in ('L', 'crit', 'area'):
        cnt = collections.Counter(min(x[key] // 4 * 4, 60) for x in L)
        print(key, sorted(cnt.items()))
