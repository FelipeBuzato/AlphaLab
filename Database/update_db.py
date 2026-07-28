from pathlib import Path
import subprocess
import sys
import time


SCRIPT_DIR = Path(__file__).resolve().parent
INGESTION_DIR = SCRIPT_DIR / "data_ingestion" / "yahoo_finance"

scripts = [
    "update_assets.py",
    "update_daily_prices.py",
    "update_dividends.py",
    "update_rates.py",
    "update_rates_values.py"
]

for script in scripts:
    script_path = INGESTION_DIR / script
    print(f"\nRunning {script}...")

    start = time.time()
    result = subprocess.run(
        [sys.executable, str(script_path)]
    )
    time_update = time.time() - start

    if result.returncode != 0:
        print(f"{script} failed. Stopping update process.")
        break

    print(f"{script} completed successfully. Time: {time_update:.2f} seconds.")

print("\nDatabase update finished.")