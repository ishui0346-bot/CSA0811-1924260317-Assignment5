"""Runs every program in order.   Usage:  python run_all.py"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STEPS = [
    "Task01_B1/generate_data.py",
    "Task01_B1/complete_code.py",
    "Task01_B1/b1_pipeline.py",
    "Task01_B1/b1_pandas_vs_csv.py",
    "Task02_B2/complete_code.py",
    "Task02_B2/b2_adversarial.py",
    "Task03_B3/b3_benchmark.py",
    "Task04_B4/complete_code.py",
    "Task04_B4/b4_decision.py",
]
for step in STEPS:
    print(f"\n######## {step} ########", flush=True)
    r = subprocess.run([sys.executable, str(ROOT / step)], cwd=ROOT)
    if r.returncode:
        sys.exit(f"FAILED: {step}")
print("\nAll programs finished.")
