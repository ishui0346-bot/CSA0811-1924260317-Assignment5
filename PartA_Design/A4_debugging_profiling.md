# A4: Plan Debugging and Profiling (4 marks, K4)

## A4.1 Debugging plan (2)
| Tool | Use in the cleaning code |
|---|---|
| `print()` | quick look at one suspicious record: `print(repr(row))` (repr shows hidden spaces / `''` vs `None`) |
| `assert` | encode rules as checks after each stage: `assert 0 <= pm25 <= 999`, `assert len(clean) <= len(raw)`, `assert key not in seen`; they fail loudly at the first violation (B1 uses them) |
| `logging` | `logging.getLogger("aq")` with levels: DEBUG per rejected row, INFO counters per file, WARNING for missing columns, ERROR for unreadable files; output to console and `cleaning.log` |
| `pdb` / IDE debugger | `breakpoint()` or a VS Code breakpoint at the rule that gives wrong output; inspect `r`, step with `n`/`s`, print with `p`, conditional breakpoint (`station == "Guindy"`) |
Method: reproduce on the 16-row `small_messy.csv`, locate the stage with the first wrong value (bisect: raw → parsed → converted → filled), fix, add an assert/test so it cannot return.

## A4.2 Profiling plan (2)
1. `time.perf_counter()` - wall-clock of each stage (load, clean, store, query, plot): `t0 = perf_counter(); ...; print(perf_counter() - t0)`.
2. `timeit` - compare two small alternatives fairly (e.g. `executemany` vs loop) with many repeats.
3. `cProfile` + `pstats` (`sort_stats("tottime")`) - find the function with the largest own time; optimise only that part (B3.3).
```
ALGORITHM ProfilePlan
  FOR EACH stage IN (load, clean, store, query, plot): MEASURE with perf_counter
  stage* <- stage with largest time
  RUN cProfile on stage*; SORT by tottime; READ top 5 functions
  CHANGE one thing; MEASURE again; KEEP only if faster and results identical
```

## Alternative concept and complexity analysis
**Alternative:** `print()` everywhere.
| | print | logging + debugger |
|---|---|---|
| Extra time | each print is an I/O call; thousands inside a loop of n rows add O(n) calls and can slow the loop by many times (console is slow) | `logger.debug()` is skipped cheaply when the level is above DEBUG; the cost is a level check |
| Switch off | must delete/comment every print (easy to miss one, or break code) | change one setting: `logging.basicConfig(level=logging.WARNING)`; a debugger leaves no code in the program |
| Information | just text | timestamp, level, module, can go to a file |
Measure: call 100,000 prints (redirected) vs 100,000 disabled `logger.debug` calls with `perf_counter`; expect logging-disabled ≈ 10-100× cheaper than print.
