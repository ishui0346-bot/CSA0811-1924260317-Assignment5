# A2: Design the Cleaning and Normalisation (5 marks, K4)

## A2.1 Cleaning rules (2)
| Problem | Rule | Justification |
|---|---|---|
| Missing (blank / NA) | **Forward-fill within the station** (time-ordered); if no previous value exists, fill with the **station median**; set `pm25_imputed = 1` | Air quality changes slowly hour to hour, so the previous hour is a good estimate. The median is robust against outliers when there is nothing earlier. Dropping would leave gaps and bias daily means (see alternative). The flag keeps honesty: valid-reading counts stay correct. |
| Impossible values (pm25 < 0 or > 999; pm10 > 1999; no2 > 999; temp outside -10..60 °C) | Treat as **missing**, then apply the missing-value rule | A sensor fault gives no information; one 9999 would ruin a mean. Limits are physical/instrument limits, written as constants. |
| Duplicate rows | Key = (station, date, hour); **keep the first**, drop the rest | A reading is identified by that key; duplicates come from files sent twice and would double-count. |
| Fahrenheit temperatures | For stations in `F_STATIONS` convert `C = (F - 32) × 5/9`, round to 1 decimal, **before** range checking | One unit in the database; checking range on unconverted values would wrongly reject 86 °F. |
| Bad date / hour | Reject the row and count it in a reject log | Without a valid time the reading cannot be placed. |

```
ALGORITHM CleanRows(rows)
  INPUT  rows: list of raw records        OUTPUT clean: list of clean records, stats
  seen <- empty set;  clean <- empty list
  FOR EACH r IN rows DO
     station <- TITLECASE(TRIM(r.station));  day <- PARSE_DATE(r.date);  hour <- TO_INT(r.hour)
     IF day IS INVALID OR hour NOT IN 0..23 THEN COUNT reject; CONTINUE
     IF (station, day, hour) IN seen THEN COUNT duplicate; CONTINUE
     ADD (station, day, hour) TO seen
     FOR EACH column c IN (pm25, pm10, no2, temp) DO
        v <- TO_NUMBER(r[c])                       // blank / NA -> NULL
        IF c = temp AND station IN F_STATIONS AND v NOT NULL THEN v <- (v - 32) * 5 / 9
        IF v NOT NULL AND (v < LOW[c] OR v > HIGH[c]) THEN v <- NULL
        r[c] <- v
     APPEND r TO clean
  SORT clean BY (station, day, hour)
  FOR EACH station, column: median[station, c] <- MEDIAN(valid values)
  FOR EACH r IN clean (in order) DO
     FOR EACH column c DO
        IF r[c] IS NULL THEN
            IF last[station, c] EXISTS THEN r[c] <- last[station, c]
            ELSE IF median[station, c] EXISTS THEN r[c] <- median[station, c]
        IF r[c] NOT NULL THEN last[station, c] <- r[c]
  RETURN clean
```

## A2.2 Normalisation (2)
- **Min-max:** `x' = (x - min) / (max - min)` → range 0..1. Appropriate when a bounded scale is needed (colour scales,
  index-like scores, neural-network inputs) and the data has no extreme outliers (one outlier squeezes all others). Guard: if
  `max = min`, return 0.
- **Z-score:** `z = (x - mean) / std`. Appropriate for comparing stations or detecting outliers (|z| > 3), for methods that assume
  roughly normal data, and when outliers exist. Unbounded; guard `std = 0`.
```
ALGORITHM MinMax(values): lo <- MIN(values); hi <- MAX(values)
   IF hi = lo THEN RETURN list of 0 ELSE RETURN [ROUND((v - lo)/(hi - lo), 3) FOR v IN values]
ALGORITHM ZScore(values): mu <- MEAN(values); sd <- STDEV(values)
   IF sd = 0 THEN RETURN list of 0 ELSE RETURN [ROUND((v - mu)/sd, 3) FOR v IN values]
```
Both O(n) time, O(n) space for the output.

## A2.3 Formatting (1)
- **Dates:** ISO 8601 text `yyyy-mm-dd` (input formats `dd/mm/yyyy`, `dd-mm-yyyy` are converted); hour is an integer 0-23.
- **Station names:** trimmed, single spaces, Title Case (`T Nagar`, `Anna Nagar`); unique per station.
- **Numbers:** decimal point, no thousands separators, stored as REAL; pollutants rounded to 1 decimal (µg/m³); temperature in °C,
  1 decimal; missing = NULL (never 0, "NA" or -999).

## Alternative concept and complexity analysis
**Alternative:** drop rows with missing readings.
```
ALGORITHM DropMissing(rows): RETURN [r FOR r IN rows IF ALL(r[c] NOT NULL FOR c IN columns)]
```
| | Fill (ffill / median) | Drop |
|---|---|---|
| Effect on daily average | keeps 24 values/day; smooth, slightly under-states variance; flagged | fewer values; if faults happen at peak hours (e.g. sensor overload) the mean is **biased low**; days with all values missing vanish |
| Time | forward fill O(n); median by sorting O(m log m) per group | O(n) |
| Space | O(n) plus a list per group for the median | O(n) (result smaller) |
Because a row is dropped if *any* of 4 columns is bad (≈ 5-10 % of rows in my data), dropping loses much more data than filling one column.
