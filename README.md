# CSA08 – Python Programming – Assignment 5 (CO5)
**City Air-Quality Monitoring Network: acquire → clean → store → query → visualise → profile → interpret**

| | |
|---|---|
| Name | `<YOUR NAME>` |
| Register number | `<REGISTER NUMBER>` |
| GitHub repository | `https://github.com/<you>/CSA08-<RegisterNumber>-Assignment5` |
| Python version | 3.12 (3.10+ works) |
| Libraries | `pandas`, `matplotlib` (see `requirements.txt`); standard library: csv, sqlite3, statistics, re, cProfile, timeit |

> Replace the `<...>` placeholders, rename the folder to `CSA08-<RegisterNumber>-Assignment5`, and put your own execution
> screenshots in each task's `outputs/` folder (the assignment says screenshots alone are not enough, but they are required).

## How to run (VS Code terminal, from this folder)
```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate        macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
pip freeze | findstr /i "pandas matplotlib"      # (macOS/Linux: pip freeze | grep -iE "pandas|matplotlib")  -> write versions here

python run_all.py                    # everything, in order (about 1 minute)
```
Run each program separately:

| Task | Command | What it does |
|---|---|---|
| B1 | `python Task01_B1/generate_data.py` | creates 12 October station CSVs (with faults) and the small test file |
| B1 | `python Task01_B1/complete_code.py` | Complete-the-Code (TODO 1/2) + `> 999` check and test row |
| B1 | `python Task01_B1/b1_pipeline.py` | before/after cleaning, SQLite (`executemany`), 3 SQL questions, 5 charts, interpretation |
| B1 | `python Task01_B1/b1_pandas_vs_csv.py` | alternative: pandas vs loops at 1k / 100k / 1M rows (time + memory) |
| B2 | `python Task02_B2/complete_code.py` | Complete-the-Code (`executemany`, parameterised SELECT) |
| B2 | `python Task02_B2/b2_adversarial.py` | bad files, SQL injection, `executemany` vs loop, sentiment failures |
| B3 | `python Task03_B3/b3_benchmark.py` | loops vs pandas vs SQL at 1/12/120 stations, cProfile, running-sum alternative |
| B4 | `python Task04_B4/complete_code.py` | Complete-the-Code (negation scorer) + wrongly labelled example |
| B4 | `python Task04_B4/b4_decision.py` | 51 complaints agreement, summariser comparison, index timing, production decision |

Part A (designs, rules, pseudocode, complexity analysis) is in `PartA_Design/A1…A5.md`.
`shared/` holds the cleaning rules, data generator and sentiment functions used by several tasks.

## Short result of each task (numbers from my run – yours will differ slightly in timings)
- **B1** – 16-row messy file: all problems handled (duplicate, NA/blank, negative, 9999, Fahrenheit, bad date/hour, name/date formats);
  assertions pass. Full October data: 8,954 rows → 8,928 clean rows in SQLite. 5 charts in `Task01_B1/charts/`, interpretation in
  `Task01_B1/outputs/interpretation.md`. pandas was ≈5.6× faster than loops at 1,000,000 rows.
- **B2** – naive CSV loader crashed on latin-1/UTF-16 files and silently accepted wrong delimiter/empty file; the robust loader rejects or
  adapts with a clear message. String concatenation breaks on `O'Brien` and `Adyar' OR '1'='1` returns all rows; `?` is safe (None).
  6 of 10 adversarial sentences were mislabelled by the sentiment scorer.
- **B3** – the four methods agree on all sizes; for 1,051,200 rows: pandas 0.39 s, running sum 1.1 s, SQL 1.3 s, loops 1.8 s.
  cProfile: most own time is in `csv.DictReader.__next__`, then `statistics.mean`.
- **B4** – scorer agrees with my labels on 43/51 (84 %, optimistic). Index on (station, day): 32.8 ms → 0.07 ms (≈450×).
  Decision: indexed relational DB, incremental pandas cleaning, lexicon only as first filter and a trained model for reported sentiment.

## Commit history
The commit history is checked. Create the GitHub repo and run `bash git_commits.sh <repo-url>` (Git Bash on Windows) – it makes one
commit per task. Better: commit after finishing each task on your own machine.

## Honest notes
- Data is **synthetic** (generated with a fixed random seed) but has every problem listed in the case study.
- Timings depend on your computer; re-run and paste your own numbers in your report.
- Pseudocode in Part A uses a generic structured style; adjust keywords if your "SIMATS Engineering – Standard for Algorithmic
  Pseudocode" document requires a specific format.
