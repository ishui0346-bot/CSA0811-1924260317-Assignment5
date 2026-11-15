"""B2 - Adversarial data: bad files, SQL injection, sentiment failures, executemany timing.
Run:  python Task02_B2/b2_adversarial.py      (writes outputs/b2_output.txt)
"""
import csv
import io
import sqlite3
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from shared.sentiment import label, score  # noqa: E402

DATA = HERE / "data"
DATA.mkdir(exist_ok=True)
LOG = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    LOG.append(s)


REQUIRED = ["station", "date", "hour", "pm25"]

# ------------------------------------------------------------------ 1. adversarial files
GOOD = "station,date,hour,pm25\nAdyar,2026-10-01,8,48\nAdyar,2026-10-01,9,52\n"
(DATA / "missing_column.csv").write_text("station,date,hour\nAdyar,2026-10-01,8\n", encoding="utf-8")
(DATA / "wrong_delimiter.csv").write_text(GOOD.replace(",", ";"), encoding="utf-8")
(DATA / "latin1_encoding.csv").write_bytes("station,date,hour,pm25\nThiruvanmiyur é,2026-10-01,8,48\n".encode("latin-1"))
(DATA / "utf16_encoding.csv").write_bytes(GOOD.encode("utf-16"))
(DATA / "empty.csv").write_bytes(b"")
(DATA / "good.csv").write_text(GOOD, encoding="utf-8")


def naive_load(path):
    """What a careless program does: assume UTF-8 and comma."""
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def decode(raw):
    for enc in ("utf-8-sig", "utf-16", "latin-1"):    # latin-1 never fails, so it is last
        try:
            if enc == "utf-16" and not raw.startswith((b"\xff\xfe", b"\xfe\xff")):
                continue
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue


def safe_load(path):
    """Robust loader: returns (rows, message). Never crashes on a bad file."""
    raw = Path(path).read_bytes()
    if not raw.strip():
        return [], "REJECTED: file is empty"
    text, enc = decode(raw)
    try:
        dialect = csv.Sniffer().sniff(text.splitlines()[0], delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    rows = list(csv.DictReader(io.StringIO(text), dialect=dialect))
    header = list(rows[0].keys()) if rows else text.splitlines()[0].split(dialect.delimiter)
    missing = [c for c in REQUIRED if c not in header]
    if missing:
        return [], f"REJECTED: missing column(s) {missing} (delimiter={dialect.delimiter!r}, encoding={enc})"
    return rows, f"OK: {len(rows)} rows (delimiter={dialect.delimiter!r}, encoding={enc})"


log("=" * 70, "\n1. ADVERSARIAL FILES: naive loader vs robust loader\n" + "=" * 70)
for name in ["good", "missing_column", "wrong_delimiter", "latin1_encoding", "utf16_encoding", "empty"]:
    p = DATA / f"{name}.csv"
    try:
        r = naive_load(p)
        keys = list(r[0].keys()) if r else []
        naive = f"no crash, but header read as {keys}" if r else "no crash, 0 rows (silent!)"
    except Exception as e:                                          # noqa: BLE001
        naive = f"CRASH {type(e).__name__}: {str(e)[:60]}"
    _, msg = safe_load(p)
    log(f"{name:16} | naive: {naive}\n{'':16} | robust: {msg}")

# ------------------------------------------------------------------ 2. SQL injection
log("\n" + "=" * 70, "\n2. SQL: string concatenation (+) vs ? placeholder\n" + "=" * 70)
con = sqlite3.connect(":memory:")
con.execute("CREATE TABLE aq (station TEXT, day TEXT, pm25 REAL)")
con.executemany("INSERT INTO aq VALUES (?,?,?)",
                [("Adyar", "2026-10-01", 48.0), ("Guindy", "2026-10-01", 95.0), ("O'Brien Nagar", "2026-10-01", 70.0)])


def avg_concat(name):
    sql = "SELECT AVG(pm25) FROM aq WHERE station = '" + name + "'"
    return sql, con.execute(sql).fetchone()[0]


def avg_param(name):
    return con.execute("SELECT AVG(pm25) FROM aq WHERE station = ?", (name,)).fetchone()[0]


for name in ["O'Brien Nagar", "Adyar' OR '1'='1"]:
    try:
        sql, res = avg_concat(name)
        log(f"concat  | input={name!r}\n        | SQL sent: {sql}\n        | result: {res}")
    except sqlite3.Error as e:
        log(f"concat  | input={name!r}\n        | SQL sent: SELECT ... WHERE station = '{name}'\n        | ERROR: {type(e).__name__}: {e}")
    log(f"param ? | input={name!r}\n        | result: {avg_param(name)}\n")
log("Explanation: with +, the quote in the data closes the SQL string early. 'O'Brien Nagar' becomes a "
    "syntax error, and  Adyar' OR '1'='1  becomes the condition  station='Adyar' OR '1'='1'  which is always "
    "true, so ALL rows are averaged (injection). With ?, the value is passed separately from the SQL text and is "
    "always treated as data: the quote is harmless and the injection matches no station (None).")

# ------------------------------------------------------------------ 3. executemany vs execute loop
log("\n" + "=" * 70, "\n3. executemany() vs execute() in a loop (on-disk database, one commit)\n" + "=" * 70)
rows_all = [(f"ST{i % 12:02d}", f"2026-10-{i % 28 + 1:02d}", float(i % 150)) for i in range(200_000)]
for n in (1_000, 10_000, 100_000, 200_000):
    sub = rows_all[:n]
    res = {}
    for mode in ("execute-loop", "executemany"):
        dbp = HERE / "tmp_bench.db"
        dbp.unlink(missing_ok=True)
        c = sqlite3.connect(dbp)
        c.execute("CREATE TABLE aq (station TEXT, day TEXT, pm25 REAL)")
        t = time.perf_counter()
        if mode == "executemany":
            c.executemany("INSERT INTO aq VALUES (?,?,?)", sub)
        else:
            for r in sub:
                c.execute("INSERT INTO aq VALUES (?,?,?)", r)
        c.commit()
        res[mode] = time.perf_counter() - t
        c.close()
        dbp.unlink(missing_ok=True)
    log(f"n={n:>7,} | execute loop {res['execute-loop']:.4f}s | executemany {res['executemany']:.4f}s | "
        f"ratio {res['execute-loop'] / res['executemany']:.2f}x")
log("Both are O(n); executemany keeps the loop in C and prepares the statement once, so the constant is smaller. "
    "(Real gain is larger if commit() is called inside the loop: n disk syncs instead of 1.)")

# ------------------------------------------------------------------ 4. sentiment adversarial
log("\n" + "=" * 70, "\n4. SENTIMENT SCORER ON ADVERSARIAL SENTENCES\n" + "=" * 70)
tests = [
    ("Oh great, another day of choking smoke. Wonderful.", "negative", "sarcasm"),
    ("Yeah right, the air is SO clean today, I can barely breathe.", "negative", "sarcasm"),
    ("The service is not bad.", "positive", "single negation (works)"),
    ("It is not that the staff were not helpful.", "positive", "double negative"),
    ("I can't say the officers were not rude.", "negative", "double negative"),
    ("Roads are clean but the smoke is terrible.", "neutral", "mixed opinion"),
    ("Fast response, helpful staff, but the dust is still bad and the drain is broken.", "negative", "mixed opinion"),
    ("The air was never good and never clean.", "negative", "negation scope over 'and'"),
    ("Not at all helpful.", "negative", "negator not directly before word"),
    ("The air quality index is 312 today.", "negative", "no sentiment words, but is bad news"),
]
fails = 0
log(f"{'verdict':7} | {'got':8} | {'expected':8} | {'type':32} | sentence")
for text, expected, kind in tests:
    got = label(text)
    ok = got == expected
    fails += not ok
    log(f"{'OK' if ok else 'FAIL':7} | {got:8} | {expected:8} | {kind:32} | {text}  (score={score(text)})")
log(f"\n{fails} of {len(tests)} adversarial sentences are mislabelled.")

log("""
==================================================================
5. WHAT EACH ADVERSARIAL INPUT REVEALS ABOUT THE DESIGN
==================================================================
- Missing column / empty file : the naive loader either crashes later (KeyError) or silently returns nothing.
  Design lesson: validate the header and file size BEFORE processing and report a clear reason.
- Wrong delimiter             : the header becomes ONE column named 'station;date;hour;pm25'. Without detection every
  value would be treated as missing. Lesson: sniff the dialect and check required columns.
- Different encoding          : UTF-8 assumption raises UnicodeDecodeError (latin-1 / utf-16 files). Lesson: detect BOM,
  try encodings in a defined order, and log which one was used.
- Quote in a station name     : string building is not just an inconvenience, it is a security hole. Lesson: always
  use ? placeholders; never trust text from files, apps or users.
- Sarcasm / double negatives / mixed opinions : a word-list scorer has no understanding of context, tone or scope.
  Lesson: treat the score as a rough signal, measure agreement with human labels (B4), and use a trained model
  (or human review) where accuracy matters.
""")
(HERE / "outputs" / "b2_output.txt").write_text("\n".join(LOG), encoding="utf-8")
