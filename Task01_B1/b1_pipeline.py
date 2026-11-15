"""B1 - Implement and validate the cleaning pipeline, store in SQLite, query, visualise.
Run:  python Task01_B1/b1_pipeline.py
Outputs: outputs/b1_output.txt, outputs/sql_results.txt, outputs/interpretation.md,
         air_quality.db, charts/*.png
"""
import csv
import sqlite3
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from shared.aq_clean import clean_rows, read_csv_files, min_max, z_score, NUM_COLS  # noqa: E402
from shared.aq_gen import F_STATIONS  # noqa: E402

OUT, CH, DB = HERE / "outputs", HERE / "charts", HERE / "air_quality.db"
OUT.mkdir(exist_ok=True); CH.mkdir(exist_ok=True)
LOG = []


def log(*a):
    line = " ".join(str(x) for x in a)
    print(line)
    LOG.append(line)


def show(rows, title, cols=("station", "date", "hour", "pm25", "pm10", "no2", "temp")):
    log(f"\n--- {title} ---")
    log(" | ".join(f"{c:>10}" for c in cols))
    for r in rows:
        log(" | ".join(f"{str(r.get(c, '')):>10}" for c in cols))


# ---------------------------------------------------------------- B1.1 small file
small_path = HERE / "data" / "small_messy.csv"
with open(small_path, newline="", encoding="utf-8") as f:
    before = list(csv.DictReader(f))
show(before, f"BEFORE cleaning ({len(before)} rows)")
stats = {}
after = clean_rows(before, stats)
show(after, f"AFTER cleaning ({len(after)} rows)")
log("\nCleaning counters:", stats)
# automated checks: every problem from A1.1 must be handled
assert stats["duplicates"] == 1, "duplicate row not removed"
assert stats["bad_key"] == 2, "bad date / bad hour rows must be rejected"
assert stats["fahrenheit_converted"] >= 4
assert all(0 <= r["pm25"] <= 999 for r in after), "pm25 out of range remains"
assert all(r["pm25"] is not None and r["temp"] is not None for r in after), "missing values remain"
assert all(-10 <= r["temp"] <= 60 for r in after), "temperature out of range / Fahrenheit remains"
assert {r["station"] for r in after} == {"Adyar", "Guindy", "Velachery", "Porur"}
log("B1.1 validation: all assertions passed.")

# ---------------------------------------------------------------- full data
paths = sorted((HERE / "data" / "raw").glob("station_*.csv"))
if not paths:
    sys.exit("Run generate_data.py first.")
stats = {}
rows = clean_rows(read_csv_files(paths), stats)
log(f"\nFull October data: {len(paths)} files -> {len(rows)} clean rows")
log("Counters:", stats)

pm = [r["pm25"] for r in rows[:6]]
log("\nNormalisation demo (first 6 PM2.5 values):")
log("  raw      :", pm)
log("  min-max  :", min_max(pm))
log("  z-score  :", z_score(pm))

# ---------------------------------------------------------------- B1.3 SQLite
if DB.exists():
    DB.unlink()
con = sqlite3.connect(DB)
con.executescript("""
CREATE TABLE stations (
    station_id   INTEGER PRIMARY KEY,
    name         TEXT NOT NULL UNIQUE,
    temp_unit_in TEXT NOT NULL CHECK (temp_unit_in IN ('C','F'))
);
CREATE TABLE readings (
    station_id   INTEGER NOT NULL REFERENCES stations(station_id),
    day          TEXT    NOT NULL,              -- ISO yyyy-mm-dd
    hour         INTEGER NOT NULL CHECK (hour BETWEEN 0 AND 23),
    pm25         REAL, pm10 REAL, no2 REAL,
    temp_c       REAL,                          -- always Celsius after cleaning
    pm25_imputed INTEGER NOT NULL DEFAULT 0,    -- 1 = value was filled, not measured
    PRIMARY KEY (station_id, day, hour)
);
""")
names = sorted({r["station"] for r in rows})
con.executemany("INSERT INTO stations(name, temp_unit_in) VALUES (?, ?)",
                [(n, "F" if n in F_STATIONS else "C") for n in names])
sid = dict(con.execute("SELECT name, station_id FROM stations"))
con.executemany(
    "INSERT INTO readings VALUES (?,?,?,?,?,?,?,?)",
    [(sid[r["station"]], r["date"], r["hour"], r["pm25"], r["pm10"], r["no2"], r["temp"],
      r["pm25_imputed"]) for r in rows])
con.commit()
n = con.execute("SELECT COUNT(*) FROM readings").fetchone()[0]
log(f"\nSQLite: loaded {n} readings with executemany into {DB.name}")

SQL = []


def ask(title, sql, params=()):
    cur = con.execute(sql, params)
    res = cur.fetchall()
    head = [d[0] for d in cur.description]
    SQL.append(f"\n### {title}\n{sql.strip()}\nparams={params}\n{head}")
    SQL.extend(str(r) for r in res[:15])
    return res

q1 = ask("Q1  Average PM2.5 of Adyar in October 2026",
         """SELECT s.name, ROUND(AVG(r.pm25),2) AS avg_pm25, COUNT(*) AS n
            FROM readings r JOIN stations s USING(station_id)
            WHERE s.name = ? AND r.day BETWEEN '2026-10-01' AND '2026-10-31'""", ("Adyar",))
q2 = ask("Q2  Number of days per station whose daily mean PM2.5 exceeded 60",
         """SELECT name, COUNT(*) AS bad_days FROM (
                SELECT s.name, r.day, AVG(r.pm25) AS m FROM readings r
                JOIN stations s USING(station_id) GROUP BY s.name, r.day HAVING m > 60)
            GROUP BY name ORDER BY bad_days DESC""")
q3 = ask("Q3  Hour of the day with the worst average PM2.5 (city-wide)",
         """SELECT hour, ROUND(AVG(pm25),1) AS avg_pm25 FROM readings
            GROUP BY hour ORDER BY avg_pm25 DESC LIMIT 5""")
q4 = ask("Daily summary table (A3.2) - Adyar, first 5 days",
         """SELECT s.name, r.day, ROUND(MIN(pm25),1) AS min_pm25, ROUND(MAX(pm25),1) AS max_pm25,
                   ROUND(AVG(pm25),1) AS mean_pm25,
                   SUM(1 - pm25_imputed) AS valid_readings
            FROM readings r JOIN stations s USING(station_id)
            WHERE s.name = ? GROUP BY s.name, r.day ORDER BY r.day LIMIT 5""", ("Adyar",))
(OUT / "sql_results.txt").write_text("\n".join(SQL), encoding="utf-8")
log("\n".join(SQL))

# ---------------------------------------------------------------- B1.4 charts
daily = con.execute("""SELECT day, AVG(pm25) FROM readings r JOIN stations s USING(station_id)
                       WHERE s.name='Adyar' GROUP BY day ORDER BY day""").fetchall()
by_station = con.execute("""SELECT s.name, AVG(pm25) FROM readings r JOIN stations s USING(station_id)
                            GROUP BY s.name ORDER BY 2 DESC""").fetchall()
by_hour = con.execute("SELECT hour, AVG(pm25) FROM readings GROUP BY hour ORDER BY hour").fetchall()
scatter = con.execute("""SELECT temp_c, pm25 FROM readings WHERE station_id=
                         (SELECT station_id FROM stations WHERE name='Adyar')""").fetchall()
box = {s: [x[0] for x in con.execute(
    "SELECT pm25 FROM readings r JOIN stations s USING(station_id) WHERE s.name=?", (s,))] for s in names}

fig, ax = plt.subplots(figsize=(8, 4))
ax.plot([d[5:] for d, _ in daily], [m for _, m in daily], marker="o", color="tab:red")
ax.axhline(60, ls="--", color="grey", label="60 µg/m³ (24-h limit)")
ax.set_xlabel("Date (MM-DD, Oct 2026)"); ax.set_ylabel("Daily mean PM2.5 (µg/m³)")
ax.set_title("Adyar: daily mean PM2.5, October 2026"); ax.legend()
ax.set_xticks(range(0, len(daily), 3)); ax.set_xticklabels([daily[i][0][5:] for i in range(0, len(daily), 3)])
fig.tight_layout(); fig.savefig(CH / "1_trend_line.png", dpi=120); plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 4))
ax.bar([n for n, _ in by_station], [m for _, m in by_station], color="tab:blue")
ax.set_xlabel("Station"); ax.set_ylabel("Mean PM2.5 (µg/m³)"); ax.set_title("Mean PM2.5 by station, October 2026")
plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
fig.tight_layout(); fig.savefig(CH / "2_station_bar.png", dpi=120); plt.close(fig)

fig, ax = plt.subplots(figsize=(6, 4.5))
ax.scatter([t for t, _ in scatter], [p for _, p in scatter], s=8, alpha=0.5)
ax.set_xlabel("Temperature (°C)"); ax.set_ylabel("PM2.5 (µg/m³)"); ax.set_title("Adyar: temperature vs PM2.5 (hourly)")
fig.tight_layout(); fig.savefig(CH / "3_temp_scatter.png", dpi=120); plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 4))
colors = ["tab:red" if m == max(v for _, v in by_hour) else "tab:green" for _, m in by_hour]
ax.bar([h for h, _ in by_hour], [m for _, m in by_hour], color=colors)
ax.set_xlabel("Hour of day (0-23)"); ax.set_ylabel("Mean PM2.5 (µg/m³)"); ax.set_title("Which hours have the worst air? (all stations)")
fig.tight_layout(); fig.savefig(CH / "4_hour_bar.png", dpi=120); plt.close(fig)

fig, ax = plt.subplots(figsize=(9, 4.5))
ax.boxplot(list(box.values()), tick_labels=list(box.keys()))
ax.set_xlabel("Station"); ax.set_ylabel("PM2.5 (µg/m³)"); ax.set_title("Spread of hourly PM2.5 by station")
plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
fig.tight_layout(); fig.savefig(CH / "5_station_box.png", dpi=120); plt.close(fig)
log("\nCharts saved in", CH)

# ---------------------------------------------------------------- interpretation (numbers computed)
import statistics
xs = [t for t, _ in scatter]; ys = [p for _, p in scatter]
corr = statistics.correlation(xs, ys)
worst_h = max(by_hour, key=lambda x: x[1]); best_h = min(by_hour, key=lambda x: x[1])
(OUT / "interpretation.md").write_text(f"""# B1.4 Interpretation of the charts (numbers computed by the program)

1. **Trend (line)** - Adyar's daily mean PM2.5 ranges from {min(m for _, m in daily):.1f} to {max(m for _, m in daily):.1f} µg/m³
   over October; {sum(m > 60 for _, m in daily)} of {len(daily)} days are above the 60 µg/m³ line. A line chart is used because time
   is ordered and the eye follows the slope and spikes.
2. **Stations (bar)** - {by_station[0][0]} is the most polluted station ({by_station[0][1]:.1f}) and {by_station[-1][0]} the cleanest
   ({by_station[-1][1]:.1f}). The bar chart is sorted so the ranking is read at once. The box plot shows that the spread inside a
   station is also large, so means alone hide the bad hours.
3. **Temperature vs PM2.5 (scatter)** - Pearson correlation = {corr:.2f}. {'A weak-to-moderate negative' if corr < -0.1 else 'A weak'} relationship: this is correlation, not causation -
   both temperature and PM2.5 depend on the hour of the day (traffic and boundary-layer effects).
4. **Worst hours (bar)** - Worst hour is {worst_h[0]}:00 ({worst_h[1]:.1f}), best is {best_h[0]}:00 ({best_h[1]:.1f}); the morning (8-10) and
   evening (18-21) rush hours form the two peaks, which suggests traffic is a major source.
""", encoding="utf-8")
(OUT / "b1_output.txt").write_text("\n".join(LOG), encoding="utf-8")
con.close()
