import subprocess
import sys


scripts = [
    "update_assets.py",
    "update_daily_prices.py",
    "update_dividends.py"
]

for script in scripts:
    print(f"\nRunning {script}...")

    result = subprocess.run(
        [sys.executable, script]
    )

    if result.returncode != 0:
        print(f"{script} failed. Stopping update process.")
        break

    print(f"{script} completed successfully.")

print("\nDatabase update finished.")