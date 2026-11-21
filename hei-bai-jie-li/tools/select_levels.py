"""从候选池里按难度分档挑关卡，输出 tiers.json"""
import json, random
from post import load

TIERS = [
    # 名称, 说明, 数量, 筛选条件
    ('入门', '熟悉规则：黑踩白、白踩黑，轮流走', 30,
     lambda o: o['area'] <= 12 and 1 <= o['crit'] <= 3 and o['L'] <= 12),
    ('简单', '开始需要想好谁先走', 50,
     lambda o: o['area'] <= 16 and 3 <= o['crit'] <= 5 and o['L'] <= 18 and o['L'] > o['L0']),
    ('中等', '星星要绕路，走错一步就拿不满', 60,
     lambda o: 5 <= o['crit'] <= 8 and 12 <= o['L'] <= 26 and o['L'] > o['L0']),
    ('困难', '陷阱很多，得提前规划好几步', 60,
     lambda o: 9 <= o['crit'] <= 12 and o['L'] <= 34 and o['good'] <= 0.3 and o['L'] > o['L0']),
    ('大师', '长线接力，满星路线非常窄', 50,
     lambda o: o['crit'] >= 13 and o['L'] <= 50 and o['good'] <= 0.25 and o['L'] > o['L0']),
]

def score(o):
    return o['crit'] + 0.2 * o['L'] + 3 * (1 - o['good'])

def pick(pool, n, rng):
    """按难度排序后等距抽样，同时尽量让棋盘尺寸多样"""
    pool = sorted(pool, key=score)
    if len(pool) <= n:
        return pool
    chosen, used = [], set()
    for k in range(n):
        lo = int(k * len(pool) / n); hi = int((k + 1) * len(pool) / n)
        seg = pool[lo:hi]
        rng.shuffle(seg)
        # 优先选和上一关尺寸不同的
        prev = (chosen[-1]['w'], chosen[-1]['h']) if chosen else None
        seg.sort(key=lambda o: ((o['w'], o['h']) == prev, id(o) in used))
        chosen.append(seg[0]); used.add(id(seg[0]))
    return sorted(chosen, key=score)

if __name__ == '__main__':
    rng = random.Random(2026)
    allc = load()
    print('candidates', len(allc))
    taken = set()
    out = []
    tutorial = dict(w=5, h=2, c='x.....xxxx', bs=0, ws=5, bg=4, wg=9, st=[1, 3, 7])  # 手工教学关
    for ti, (name, desc, n, f) in enumerate(TIERS):
        pool = [o for o in allc if f(o) and id(o) not in taken]
        sel = pick(pool, n - (1 if ti == 0 else 0), rng)
        for o in sel: taken.add(id(o))
        levels = ([tutorial] if ti == 0 else []) + sel
        print(name, 'pool', len(pool), 'picked', len(levels),
              'L %d-%d' % (min(o.get('L', 8) for o in levels), max(o.get('L', 8) for o in levels)),
              'crit %d-%d' % (min(o.get('crit', 1) for o in levels), max(o.get('crit', 1) for o in levels)),
              'sizes', sorted({(o['w'], o['h']) for o in levels}))
        out.append(dict(name=name, desc=desc, levels=levels))
    json.dump(out, open('tiers.json', 'w'))
