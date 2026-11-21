import json,sys
T=json.load(open('tiers.json'))
out=[dict(name=t['name'],desc=t['desc'],levels=[{k:l[k] for k in ('w','h','c','bs','ws','bg','wg')}|{'st':l['st'],'L':l['L']} for l in t['levels']]) for t in T]
html=open('template.html').read().replace('__TIERS__',json.dumps(out,ensure_ascii=False,separators=(',',':')))
open(sys.argv[1] if len(sys.argv)>1 else 'index.html','w').write(html)
print(len(html),'bytes')
