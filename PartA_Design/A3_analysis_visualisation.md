# A3: Design the Analysis and Visualisation (5 marks, K4)

## A3.1 Chart choices (3)
| Question | Chart | Justification |
|---|---|---|
| Trend of PM2.5 over a month | **Line** (x = date, y = daily mean) with a limit line | Time is ordered and continuous; slope, spikes and the number of days over the limit are visible. |
| Comparison of stations | **Bar** (sorted mean per station); a **box plot** as a companion | Bars compare one number across categories; the box plot shows the spread and outliers that a mean hides. |
| Temperature vs PM2.5 | **Scatter** (x = temp °C, y = PM2.5) + Pearson r | Two numeric variables; scatter shows direction, strength and shape; correlation is not causation. |
| Hours with the worst air | **Bar** (x = hour 0-23, y = mean PM2.5), worst hour highlighted (histogram is for *distribution* of values, not for per-hour means) | 24 categories on a cycle; the rush-hour peaks stand out. |
All charts: labelled axes with units, title, readable tick labels, a colour that has meaning.

## A3.2 Daily summary table (2)
Columns: `station, day, min_pm25, max_pm25, mean_pm25, valid_readings` (valid = not imputed).
```
ALGORITHM DailySummary(db)
  EXECUTE SQL: SELECT station, day, MIN(pm25), MAX(pm25), AVG(pm25), SUM(1 - pm25_imputed)
               FROM readings JOIN stations GROUP BY station, day ORDER BY station, day
  RETURN rows (store as a table / DataFrame, export to CSV for the report)
```
GROUP BY is done inside the database in C, uses the (station, day, hour) key, and returns only the small summary.

## Alternative concept and complexity analysis
**Alternative:** read all rows into Python and compute the summary with loops.
```
ALGORITHM SummaryByLoops(rows)
  groups <- empty dictionary of lists
  FOR EACH r IN rows: APPEND r.pm25 TO groups[(r.station, r.day)]
  FOR EACH key IN groups: MIN, MAX, MEAN, COUNT of groups[key]
```
| | Python loops | SQL GROUP BY |
|---|---|---|
| Time | O(n) to group + O(n) to aggregate = O(n) (large constant: interpreter) | O(n) (or O(n log n) if it must sort); C speed |
| Memory | all n values held in lists: **O(n)** | only the aggregate per group in the engine: **O(groups)**, and only the summary reaches Python |
Measured in B3 (loops 1.77 s vs SQL 1.30 s for 1.05 M rows; running-sum variant uses O(stations × days) memory).
