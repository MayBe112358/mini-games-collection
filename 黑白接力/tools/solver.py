"""黑白接力 规则引擎 + BFS 求解器
规则：
- 格子：'#' 墙，'w' 白，'k' 黑
- 黑小人只能走到白格，走上去后该格变黑；白小人相反
- 轮流移动，黑先手；小人不能进入对方所在的格子
- 小人到达自己的终点后停在那里，之后只轮另一个走
- 两人都到终点即通关；轮到的人无路可走即卡死
- 星星：任一小人走上该格即拾取
"""
from collections import deque

DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0)]


def parse(rows):
    """文本关卡 -> dict
    '#' 墙  '.' 白  'x' 黑
    'B' 黑起点(黑格) 'W' 白起点(白格)
    'b' 黑终点(白格) 'p' 黑终点(黑格)
    'w' 白终点(黑格) 'q' 白终点(白格)
    '*' 星(白格)  '+' 星(黑格)
    """
    h, wd = len(rows), len(rows[0])
    cells, stars = [], []
    lv = dict(w=wd, h=h)
    for y, r in enumerate(rows):
        assert len(r) == wd, r
        for x, c in enumerate(r):
            i = y * wd + x
            col = {'#': '#', '.': 'w', 'x': 'k', 'B': 'k', 'W': 'w', 'b': 'w', 'p': 'k',
                   'w': 'k', 'q': 'w', '*': 'w', '+': 'k'}[c]
            cells.append(col)
            if c == 'B': lv['bs'] = i
            if c == 'W': lv['ws'] = i
            if c in 'bp': lv['bg'] = i
            if c in 'wq': lv['wg'] = i
            if c in '*+': stars.append(i)
    lv['cells'] = cells
    lv['stars'] = stars
    return lv


def neighbors(lv):
    w, h = lv['w'], lv['h']
    nb = []
    for i in range(w * h):
        x, y = i % w, i // w
        out = []
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and lv['cells'][ny * w + nx] != '#':
                out.append(ny * w + nx)
            else:
                out.append(-1)
        nb.append(out)
    return nb


def initial(lv):
    mask = 0
    for i, c in enumerate(lv['cells']):
        if c == 'k':
            mask |= 1 << i
    smask = 0
    for k, s in enumerate(lv['stars']):
        if s in (lv['bs'], lv['ws']):
            smask |= 1 << k
    return (lv['bs'], lv['ws'], mask, 0, smask)  # turn 0=黑 1=白


def moves(lv, nb, st):
    """返回 [(dir, newstate, won)]；空列表表示卡死（或已胜利）"""
    b, wp, mask, turn, sm = st
    bl = b == lv['bg']
    wl = wp == lv['wg']
    if bl and wl:
        return []
    if turn == 0 and bl: turn = 1
    if turn == 1 and wl: turn = 0
    cur = b if turn == 0 else wp
    oth = wp if turn == 0 else b
    res = []
    for d, n in enumerate(nb[cur]):
        if n < 0 or n == oth:
            continue
        isblack = (mask >> n) & 1
        if turn == 0 and isblack: continue
        if turn == 1 and not isblack: continue
        nmask = mask | (1 << n) if turn == 0 else mask & ~(1 << n)
        nsm = sm
        for k, s in enumerate(lv['stars']):
            if s == n: nsm |= 1 << k
        nb_, nw_ = (n, wp) if turn == 0 else (b, n)
        won = nb_ == lv['bg'] and nw_ == lv['wg']
        res.append((d, (nb_, nw_, nmask, 1 - turn, nsm), won))
    return res


def solve(lv, limit=3_000_000):
    """BFS。返回 dict: best[stars]=最少步数, states=可达状态数, dead=卡死状态数,
    path_all=全星最短解方向序列"""
    nb = neighbors(lv)
    s0 = initial(lv)
    full = (1 << len(lv['stars'])) - 1
    prev = {s0: None}
    q = deque([s0])
    dist = {s0: 0}
    best = {}
    win_state = {}
    dead = 0
    while q:
        st = q.popleft()
        ms = moves(lv, nb, st)
        if not ms:
            dead += 1
        for d, ns, won in ms:
            if ns in dist:
                continue
            dist[ns] = dist[st] + 1
            prev[ns] = (st, d)
            if won:
                c = bin(ns[4]).count('1')
                if c not in best:
                    best[c] = dist[ns]
                    win_state[c] = ns
                continue
            q.append(ns)
            if len(dist) > limit:
                return None
    def path(ns):
        out = []
        while prev[ns] is not None:
            ps, d = prev[ns]
            out.append(d)
            ns = ps
        return out[::-1]
    res = dict(best=best, states=len(dist), dead=dead)
    nst = len(lv['stars'])
    if nst in best:
        res['path_all'] = path(win_state[nst])
    if best:
        res['path_min'] = path(win_state[max(best)] if False else min(win_state.items(), key=lambda kv: best[kv[0]])[1])
    return res


def can_reach_all(lv, limit=3_000_000):
    """从每个状态出发是否还能全星通关 -> 计算'陷阱率'"""
    nb = neighbors(lv)
    s0 = initial(lv)
    full = (1 << len(lv['stars'])) - 1
    graph = {}
    q = deque([s0]); seen = {s0}
    goods = set()
    while q:
        st = q.popleft()
        ms = moves(lv, nb, st)
        graph[st] = []
        for d, ns, won in ms:
            if won:
                if ns[4] == full:
                    goods.add(st)
                continue
            graph[st].append(ns)
            if ns not in seen:
                seen.add(ns); q.append(ns)
                if len(seen) > limit: return None
    rev = {}
    for s, outs in graph.items():
        for t in outs:
            rev.setdefault(t, []).append(s)
    good = set(goods); q = deque(goods)
    while q:
        s = q.popleft()
        for p in rev.get(s, []):
            if p not in good:
                good.add(p); q.append(p)
    return len(good) / len(graph), s0 in good


if __name__ == '__main__':
    lv = parse([
        "B..#",
        "x#.b",
        "W.xw",
    ])
    print(solve(lv))
