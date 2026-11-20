import random, sys, json
from multiprocessing import Pool
from solver import solve, can_reach_all, neighbors

def rand_level(rng, w, h, wall_p, black_p, nstars=3):
    cells = []
    for i in range(w * h):
        r = rng.random()
        cells.append('#' if r < wall_p else ('k' if rng.random() < black_p else 'w'))
    free = [i for i, c in enumerate(cells) if c != '#']
    if len(free) < 4 + nstars:
        return None
    pick = rng.sample(free, 4 + nstars)
    bs, ws, bg, wg = pick[:4]
    cells[bs] = 'k'; cells[ws] = 'w'
    return dict(w=w, h=h, cells=cells, bs=bs, ws=ws, bg=bg, wg=wg, stars=pick[4:])

def evaluate(args):
    seed, w, h = args
    rng = random.Random(seed)
    lv = rand_level(rng, w, h, rng.uniform(0.05, 0.25), rng.uniform(0.3, 0.6))
    if lv is None: return None
    r = solve(lv, limit=60_000)
    if not r or 3 not in r['best']: return None
    mn = min(r['best'].values())
    L = r['best'][3]
    cr = can_reach_all(lv, limit=60_000)
    if cr is None: return None
    goodfrac, _ = cr
    # 难度分：全星步数长、陷阱多、全星需要额外绕路
    score = L * (1 - goodfrac) + 2 * (L - mn)
    return dict(seed=seed, lv=lv, L=L, mn=mn, good=goodfrac, states=r['states'], score=score,
                path=r['path_all'])

if __name__ == '__main__':
    w, h, n, start = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
    with Pool() as p:
        res = [x for x in p.imap_unordered(evaluate, [(s, w, h) for s in range(start, start + n)], chunksize=50) if x]
    res.sort(key=lambda x: -x['score'])
    json.dump([x for x in res if x["L"]<=40], open(f'cand_{w}x{h}.json', 'w'))
    for x in res[:8]:
        print(x['seed'], 'L', x['L'], 'mn', x['mn'], 'good %.3f' % x['good'], 'states', x['states'], 'score %.1f' % x['score'])
