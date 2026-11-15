"""Synthetic data generator for the City Air-Quality Monitoring Network.

Creates station CSV files with the SAME problems described in the case study:
blank / "NA" readings, negative and impossibly large sensor values, duplicate
rows, and two stations (Guindy, Velachery) that report temperature in Fahrenheit.
"""
import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path

STATIONS = ["Adyar", "Guindy", "Velachery", "T Nagar", "Anna Nagar", "Mylapore",
            "Perungudi", "Kodambakkam", "Tambaram", "Ambattur", "Porur", "Royapuram"]
F_STATIONS = {"Guindy", "Velachery"}          # report temperature in Fahrenheit
HEADER = ["station", "date", "hour", "pm25", "pm10", "no2", "temp"]


def station_rows(station, start, days, seed, faults=True):
    """Hourly rows (as lists) for one station."""
    rnd = random.Random(seed)
    offset = rnd.uniform(-10, 25)
    rows = []
    for d in range(days):
        day = start + timedelta(days=d)
        for h in range(24):
            temp_c = 27 + 5 * math.sin((h - 9) / 24 * 2 * math.pi) + rnd.gauss(0, 1)
            rush = 25 if h in (8, 9, 10, 18, 19, 20, 21) else 0
            pm25 = max(5, 45 + offset + rush - 0.8 * (temp_c - 27) + rnd.gauss(0, 8))
            pm10 = pm25 * 1.6 + rnd.gauss(0, 10)
            no2 = 20 + 0.3 * pm25 + rnd.gauss(0, 5)
            temp = temp_c * 9 / 5 + 32 if station in F_STATIONS else temp_c
            row = [station, day.isoformat(), h,
                   round(pm25, 1), round(pm10, 1), round(no2, 1), round(temp, 1)]
            if faults:
                for i in range(3, 7):
                    r = rnd.random()
                    if r < 0.02:
                        row[i] = ""
                    elif r < 0.04:
                        row[i] = "NA"
                    elif r < 0.045:
                        row[i] = -round(rnd.uniform(1, 50), 1)
                    elif r < 0.05:
                        row[i] = 9999
            rows.append(row)
            if faults and rnd.random() < 0.003:
                rows.append(list(row))        # duplicate row
    return rows


def write_station_files(folder, start=date(2026, 10, 1), days=31, seed=42):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, st in enumerate(STATIONS):
        p = folder / f"station_{st.replace(' ', '_')}.csv"
        with open(p, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(HEADER)
            w.writerows(station_rows(st, start, days, seed + i))
        paths.append(p)
    return paths


def write_big_file(path, n_stations, days=365, seed=1):
    """Simple file (station,date,pm25) for the scaling experiments in B3/B4.
    24 readings per station per day -> about 8,760 readings per station per year."""
    rnd = random.Random(seed)
    start = date(2026, 1, 1)
    days_list = [(start + timedelta(days=d)).isoformat() for d in range(days)]
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["station", "date", "pm25"])
        for s in range(n_stations):
            name = f"ST{s:03d}"
            base = rnd.uniform(30, 70)
            for dd in days_list:
                for _ in range(24):
                    w.writerow([name, dd, round(max(1, rnd.gauss(base, 15)), 1)])
    return Path(path)
