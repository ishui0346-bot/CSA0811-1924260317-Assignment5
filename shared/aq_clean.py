"""Cleaning, normalisation and formatting rules (implements Part A2)."""
import csv
import statistics
from datetime import datetime

from shared.aq_gen import F_STATIONS

NUM_COLS = ["pm25", "pm10", "no2", "temp"]
LIMITS = {"pm25": (0, 999), "pm10": (0, 1999), "no2": (0, 999), "temp": (-10, 60)}  # temp in Celsius
DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d")
MISSING = {"", "na", "n/a", "nan", "null", "none"}


def parse_number(text):
    """'12.5' -> 12.5 ; blank / NA -> None ; garbage -> None."""
    if text is None:
        return None
    t = str(text).strip()
    if t.lower() in MISSING:
        return None
    try:
        return float(t)
    except ValueError:
        return None


def normalise_date(text):
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(str(text).strip(), fmt).date().isoformat()
        except ValueError:
            pass
    return None


def normalise_station(name):
    return " ".join(str(name).split()).title()


def f_to_c(f):
    return (f - 32) * 5 / 9


def clean_rows(raw_rows, stats=None):
    """raw_rows: iterable of dicts (csv.DictReader). Returns list of clean dicts.

    Rules (A2.1):
      1. station -> trimmed Title Case; date -> ISO yyyy-mm-dd; hour int 0-23
         (rows with bad date/hour are rejected: they cannot be placed in time)
      2. Fahrenheit stations -> convert temp to Celsius BEFORE range checking
      3. impossible values (negative, > limit) -> treated as missing
      4. duplicates on (station, date, hour) -> keep first
      5. missing -> forward fill within station (time ordered), else station median
    """
    st = stats if stats is not None else {}
    for k in ("input", "bad_key", "duplicates", "impossible", "missing", "filled_ffill",
              "filled_median", "fahrenheit_converted"):
        st.setdefault(k, 0)
    seen, rows = set(), []
    for r in raw_rows:
        st["input"] += 1
        station = normalise_station(r.get("station", ""))
        day = normalise_date(r.get("date", ""))
        hour = parse_number(r.get("hour"))
        if not station or day is None or hour is None or not 0 <= hour <= 23:
            st["bad_key"] += 1
            continue
        key = (station, day, int(hour))
        if key in seen:
            st["duplicates"] += 1
            continue
        seen.add(key)
        rec = {"station": station, "date": day, "hour": int(hour), "pm25_imputed": 0}
        for c in NUM_COLS:
            v = parse_number(r.get(c))
            if v is not None and c == "temp" and station in F_STATIONS:
                v = round(f_to_c(v), 1)
                st["fahrenheit_converted"] += 1
            if v is None:
                st["missing"] += 1
            else:
                lo, hi = LIMITS[c]
                if not lo <= v <= hi:
                    st["impossible"] += 1
                    v = None
            rec[c] = v
        rows.append(rec)
    rows.sort(key=lambda r: (r["station"], r["date"], r["hour"]))
    med = {}
    for r in rows:
        for c in NUM_COLS:
            if r[c] is not None:
                med.setdefault((r["station"], c), []).append(r[c])
    med = {k: statistics.median(v) for k, v in med.items()}
    last = {}
    for r in rows:
        for c in NUM_COLS:
            k = (r["station"], c)
            if r[c] is None:
                if k in last:
                    r[c] = last[k]
                    st["filled_ffill"] += 1
                elif k in med:
                    r[c] = med[k]
                    st["filled_median"] += 1
                if c == "pm25" and r[c] is not None:
                    r["pm25_imputed"] = 1
            if r[c] is not None:
                last[k] = r[c]
    return rows


def read_csv_files(paths):
    for p in paths:
        with open(p, newline="", encoding="utf-8") as f:
            yield from csv.DictReader(f)


def min_max(values):
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.0 for _ in values]
    return [round((v - lo) / (hi - lo), 3) for v in values]


def z_score(values):
    mu, sd = statistics.mean(values), statistics.pstdev(values)
    if sd == 0:
        return [0.0 for _ in values]
    return [round((v - mu) / sd, 3) for v in values]
