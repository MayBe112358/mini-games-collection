# 黑白接力 关卡工具

关卡全部由程序生成并验证，流程：

```bash
gcc -O2 -o bwsolve bwsolve.c
mkdir -p pool
./bwsolve gen 5 5 0 150000 > pool/g_5x5.jsonl   # 每种尺寸各跑一批随机关卡，只输出能三星通关的
python3 select_levels.py   # 去掉走不到的格子、裁边、去重，按难度分 5 档 -> tiers.json
python3 verify.py          # 用求解器复核每关，写入三星最短解
python3 build.py ../index.html   # 把 tiers.json 填进 template.html
```

- `bwsolve.c`：BFS 求解器。算三星最短步数、陷阱率（走不到三星的局面占比）、关键抉择数（最短解上有多少步走错就拿不满三星）。
- `solver.py`：同样规则的 Python 版，便于阅读。
- 难度分档主要看关键抉择数，其次是步数和陷阱率，见 `select_levels.py`。
