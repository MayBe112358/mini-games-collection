"""用 C 求解器复核每关；返回带 L/path 的 tiers.json"""
import json,subprocess
T=json.load(open('tiers.json'))
inp=''.join(f"{l['w']} {l['h']} {l['c']} {l['bs']} {l['ws']} {l['bg']} {l['wg']} {' '.join(map(str,l['st']))}\n" for t in T for l in t['levels'])
res=iter(subprocess.run(['./bwsolve','solve'],input=inp,capture_output=True,text=True).stdout.splitlines())
bad=0
for t in T:
    for l in t['levels']:
        r=json.loads(next(res))
        if 'fail' in r: bad+=1; print('FAIL',t['name'],l); continue
        if 'L' in l and l['L']!=r['L']: bad+=1; print('MISMATCH',t['name'],l['L'],r['L'])
        l['L']=r['L']; l['path']=r['path']; l['crit']=r['crit']
json.dump(T,open('tiers.json','w'))
print('verified',sum(len(t['levels']) for t in T),'bad',bad)
