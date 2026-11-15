"""B1 Alternative Concept: csv module + loops  vs  pandas (read_csv, replace, dropna, vectorised
min-max) for 1,000 / 100,000 / 1,000,000 rows. Measures time (perf_counter) and peak memory (tracemalloc).
Run:  python Task01_B1/b1_pandas_vs_csv.py
"""
import csv
import random
import tempfile
import time
import tracemalloc
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent


def make_file(path, n, seed=7):
    rnd = random.Random(seed)
    with open(path, "w", newline="") as f:
        f.write("station,date,pm25\n")
        for i in range(n):
            r = rnd.random()
            v = "NA" if r < 0.03 else "" if r < 0.06 else "-5" if r < 0.07 else "5000" if r < 0.08 else f"{rnd.uniform(10, 150):.1f}"
            f.write(f"ST{i % 12:02d},2026-10-{i % 28 + 1:02d},{v}\n")


def loops(path):
    vals = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            t = r["pm25"].strip()
            if t == "" or t.upper() == "NA":
                continue
            x = float(t)
            if x < 0 or x > 999:
                continue
            vals.append(x)
    lo, hi = min(vals), max(vals)
    return [round((v - lo) / (hi - lo), 3) for v in vals]


def with_pandas(path):
    df = pd.read_csv(path)
    df["pm25"] = pd.to_numeric(df["pm25"].replace("NA", float("nan")), errors="coerce")
    df = df.dropna(subset=["pm25"])
    df = df[(df["pm25"] >= 0) & (df["pm25"] <= 999)]
    lo, hi = df["pm25"].min(), df["pm25"].max()
    return ((df["pm25"] - lo) / (hi - lo)).round(3)


def measure(fn, path):
    """Time and memory are measured in two separate runs (tracemalloc slows code down)."""
    t = time.perf_counter()
    out = fn(path)
    dt = time.perf_counter() - t
    tracemalloc.start()
    fn(path)
    peak = tracemalloc.get_traced_memory()[1] / 1e6
    tracemalloc.stop()
    return dt, peak, len(out)


if __name__ == "__main__":
    lines = ["| rows | loops time (s) | loops peak MB | pandas time (s) | pandas peak MB | kept rows (loops/pandas) |",
             "|---|---|---|---|---|---|"]
    with tempfile.TemporaryDirectory() as d:
        for n in (1_000, 100_000, 1_000_000):
            p = Path(d) / f"pm_{n}.csv"
            make_file(p, n)
            a = measure(loops, p)
            b = measure(with_pandas, p)
            assert a[2] == b[2], "both methods must keep the same number of rows"
            lines.append(f"| {n:,} | {a[0]:.4f} | {a[1]:.1f} | {b[0]:.4f} | {b[1]:.1f} | {a[2]:,} / {b[2]:,} |")
            print(lines[-1])
    text = "\n".join(lines)
    (HERE / "outputs" / "pandas_vs_csv.md").write_text(
        "# B1 Alternative: csv+loops vs pandas\n\n" + text +
        "\n\nBoth are O(n) in time and space. pandas is faster by a constant factor because loops run in C "
        "(vectorised) instead of the Python interpreter; for 1,000 rows pandas start-up overhead dominates.\n", encoding="utf-8")
    print("\n" + text)
