"""B1 - Complete the Code (TODO 1 and TODO 2 completed) + extra check for pm25 > 999.
Run:  python Task01_B1/complete_code.py
"""
import csv
import io

RAW = """station,date,pm25
Adyar,2026-10-01,48
Adyar,2026-10-02,NA
Adyar,2026-10-03,
Guindy,2026-10-01,95
Guindy,2026-10-02,-5
Guindy,2026-10-03,121
"""

def load_clean(text):
    """Returns (station, date, pm25) tuples for valid, non-negative readings only."""
    rows = []
    # TODO 1: Read the text with csv.DictReader; skip rows whose pm25 is empty, 'NA' or
    # negative; convert pm25 to float
    for r in csv.DictReader(io.StringIO(text)):
        raw = r["pm25"].strip()
        if raw == "" or raw.upper() == "NA":
            continue
        value = float(raw)
        if value < 0:
            continue
        if value > 999:          # ADDED CHECK: impossible sensor value
            continue
        rows.append((r["station"], r["date"], value))
    return rows

def min_max(values):
    # TODO 2: Scale each value to the range 0-1 using (v - min) / (max - min), rounded
    # to 3 decimals
    lo, hi = min(values), max(values)
    if hi == lo:             # avoid division by zero when all values are equal
        return [0.0 for _ in values]
    return [round((v - lo) / (hi - lo), 3) for v in values]

clean = load_clean(RAW)
print(clean)
print(min_max([pm for _, _, pm in clean]))

# ---- Added test row for the "pm25 above 999" check ----------------------------
RAW_WITH_FAULT = RAW + "Adyar,2026-10-04,5000\n"      # sensor fault: must be skipped
clean2 = load_clean(RAW_WITH_FAULT)
print("\nWith the extra faulty row (5000):")
print(clean2)
assert clean2 == clean, "row with pm25 > 999 must be skipped"
assert clean == [('Adyar', '2026-10-01', 48.0), ('Guindy', '2026-10-01', 95.0), ('Guindy', '2026-10-03', 121.0)]
assert min_max([pm for _, _, pm in clean]) == [0.0, 0.644, 1.0]
print("All checks passed.")
