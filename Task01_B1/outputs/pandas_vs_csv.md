# B1 Alternative: csv+loops vs pandas

| rows | loops time (s) | loops peak MB | pandas time (s) | pandas peak MB | kept rows (loops/pandas) |
|---|---|---|---|---|---|
| 1,000 | 0.0057 | 0.2 | 0.0094 | 0.4 | 908 / 908 |
| 100,000 | 0.4699 | 6.0 | 0.0594 | 6.8 | 92,003 / 92,003 |
| 1,000,000 | 4.7783 | 59.2 | 0.4552 | 90.2 | 920,167 / 920,167 |

Both are O(n) in time and space. pandas is faster by a constant factor because loops run in C (vectorised) instead of the Python interpreter; for 1,000 rows pandas start-up overhead dominates.
