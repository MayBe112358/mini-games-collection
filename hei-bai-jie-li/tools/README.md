# 黑白接力 关卡工具

关卡全部由程序生成并验证，流程：

```bash
gcc -O2 -o bwsolve bwsolve.c
mkdir -p pool
./bwsolve gen 5 5 0 150000 > pool/g_5x5.jsonl   # 每种尺寸各跑一批随机关卡，只输出能三星通关的
python3 select_levels.py --add 10   # 在现有关卡基础上每档追加 10 关（去重、按难度插到合适位置）
python3 verify.py          # 用求解器复核每关，写入三星最短解
python3 build.py ../index.html   # 把 tiers.json 填进 template.html
```

- `bwsolve.c`：BFS 求解器。算三星最短步数、陷阱率（走不到三星的局面占比）、关键抉择数（最短解上有多少步走错就拿不满三星）。
- `solver.py`：同样规则的 Python 版，便于阅读。
- 难度分档主要看关键抉择数，其次是步数和陷阱率，见 `select_levels.py`。

## 加关卡时保住玩家存档

- 每关的 ID 由关卡内容算出（`build.py` 里的 `level_id`），存档按 ID 记录，和关卡排在第几位无关。所以插入、追加关卡都不会让进度错位。
- **已发布的关卡不要改内容**（格子、起点、终点、星星任何一项）。改了 ID 就变了，这一关的存档会丢。想换掉某关，就加一关新的。
- 加关请用 `--add`。不带参数运行 `select_levels.py` 会从头重新挑关，旧关卡可能被换掉。
- `old_order_v1.json` 是 250 关首版的顺序，页面用它把当时按「档-序号」记的旧存档迁移成 ID。不要改动或删除。
- `build.py` 会检查 ID 不重复。
