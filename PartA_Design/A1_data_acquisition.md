# A1: Design the Data Acquisition (7 marks, K3)

## A1.1 Inspect the source (2)
**Structure of one station file** (one file per station per day, header + one row per hour, up to 24 rows):

| column | meaning | type | example |
|---|---|---|---|
| station | station name | text | `Adyar` |
| date | date of reading | text (yyyy-mm-dd) | `2026-10-01` |
| hour | hour of day 0-23 | integer | `8` |
| pm25, pm10, no2 | pollutant readings (µg/m³) | decimal | `48.0` |
| temp | temperature (°C; °F for two stations) | decimal | `30.1` / `86.0` |

**Expected data-quality problems (with an example of each)**

| # | Problem | Example row |
|---|---|---|
| 1 | Missing value, blank | `Adyar,2026-10-01,10,,90,38,31.5` |
| 2 | Missing value, "NA" | `Adyar,2026-10-01,9,NA,85,36,30.8` |
| 3 | Negative value (sensor fault) | `Adyar,2026-10-01,11,-5,70,30,32.0` |
| 4 | Impossibly large value | `Adyar,2026-10-01,12,9999,75,31,32.4` |
| 5 | Duplicate row (file sent twice) | same row repeated |
| 6 | Fahrenheit temperature | `Guindy,2026-10-01,8,95,150,60,86.0` |
| 7 | Inconsistent station name | `  adyar ` instead of `Adyar` |
| 8 | Inconsistent date format | `02/10/2026`, `31-10-2026` |
| 9 | Invalid date / hour | `not-a-date`, hour `25` |
| 10 | Wrong type / text in numeric column | `4o` instead of `40` |
| 11 | Structural: missing column, wrong delimiter, other encoding, empty file | see B2 |

## A1.2 Storage design (3)
```
stations(station_id INTEGER PRIMARY KEY,
         name TEXT NOT NULL UNIQUE,
         temp_unit_in TEXT NOT NULL CHECK (temp_unit_in IN ('C','F')))

readings(station_id INTEGER NOT NULL REFERENCES stations,
         day TEXT NOT NULL,           -- ISO yyyy-mm-dd
         hour INTEGER NOT NULL CHECK (hour BETWEEN 0 AND 23),
         pm25 REAL, pm10 REAL, no2 REAL,
         temp_c REAL,                 -- always Celsius
         pm25_imputed INTEGER NOT NULL DEFAULT 0,   -- 1 = filled value
         PRIMARY KEY (station_id, day, hour))
```
**Mapping:** `station` → look up / insert in `stations`, store `station_id`; `date` → `day`; `hour` → `hour`;
`pm25, pm10, no2` → same names; `temp` → `temp_c` (converted if `temp_unit_in = 'F'`).
**Why:** the composite primary key (station, day, hour) *is* the natural identity of a reading, so duplicates
are impossible and the key doubles as an index for station/date queries. A separate `stations` table avoids
repeating names (normalisation) and holds the unit flag. Dates are ISO text so that they sort correctly.

## A1.3 CSV or SQL? (2)
| Board question | From CSV files | With SQL |
|---|---|---|
| 1. Average PM2.5 of Adyar in October | open all files, filter rows by name/date, average: full scan O(n) | `SELECT AVG(pm25) FROM readings JOIN stations USING(station_id) WHERE name=? AND day BETWEEN ? AND ?` - uses the primary-key index, ~O(log n + k) |
| 2. Days per station with daily mean > 60 | read everything, group in a dict, then count | `GROUP BY station, day HAVING AVG(pm25) > 60` |
| 3. Hour with the worst average PM2.5 | read everything, group by hour | `GROUP BY hour ORDER BY AVG(pm25) DESC LIMIT 1` |

CSV needs no set-up and suits a one-off look; SQL stores cleaned data once, gives constraints (no duplicates, valid hours), safe
parameters, and answers repeated questions without re-parsing text.

## Alternative concept and complexity analysis
**Alternative:** keep only CSV files; for each question `pandas.read_csv` all files, then filter.
```
ALGORITHM AnswerFromCSV(question)
  df <- CONCAT(READ_CSV(f) FOR EACH f IN files)      // O(n) every time
  df <- CLEAN(df)                                    // O(n) every time
  RETURN APPLY(question, df)                         // O(n)
```
| | CSV + DataFrame per question | SQLite |
|---|---|---|
| Time per question | O(n) (parse + clean + scan) every time | O(n) only for the first load; then indexed query ≈ O(log n + k) |
| Space | whole data in **memory** O(n) per question (about 10-60 MB per million rows, see B1/B3) | data on **disk** O(n); memory small (page cache) |
| Integrity | none (duplicates, bad values may re-appear) | constraints enforced |
Measured evidence: B4.2 (index: scan 32 ms vs 0.07 ms per query) and B3 (loading cost).
