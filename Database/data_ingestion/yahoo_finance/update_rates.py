import psycopg2
import pandas as pd
from datetime import datetime
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent

## Connect to PostGres database
conn = psycopg2.connect(
    host="localhost",
    database="alphalab",
    user="postgres",
    password="alphalab",
    port="5432"
)
cursor = conn.cursor()

## Get rates that are already in the database
cursor.execute(
    """
    SELECT name, ticker, country, currency, unit
    FROM rates
    """
)

existing_rates = {name: {'ticker': ticker, 'country': country, 'currency': currency, 'unit': unit} for name, ticker, country, currency, unit in cursor.fetchall()}
print(len(existing_rates), " rates currently in the database.")

## Get assets universe
rates_universe_df = pd.read_csv(CURRENT_DIR.parent / "rates_universe.csv")
rates_universe = {row['name']: {'ticker': row['ticker'], 'country': row['country'], 'currency': row['currency'], 'unit': row['unit']} for _, row in rates_universe_df.iterrows()}

## Find out which tickers need to be added to the database
rates_to_add = {name: info for name, info in rates_universe.items()
                 if name not in existing_rates}

if(len(rates_to_add) >= 1):
    print(f"Adding {len(rates_to_add)} rates to the database.")
else:
    print("No new rates.")

## Adding new rates
query = """
INSERT INTO rates (
    name,
    ticker,
    country,
    currency,
    unit,
    last_updated
)
VALUES (
    %s,%s,%s,%s,%s,
    %s
)
ON CONFLICT (name)
DO NOTHING
"""

update_time = datetime.now()
success, fail = 0, 0

for name, info in rates_to_add.items():
    try:
        data = (
            name,
            info['ticker'],
            info['country'],
            info['currency'],
            info['unit'],
            update_time
        )
        cursor.execute(query, data)
        conn.commit()
        print(f"Rate {name}, {info['ticker']}, {info['country']}, {info['currency']}, {info['unit']}: Inserted.")
        success += 1

    except Exception as e:
        print(f"Failed inserting rate {name}, {info['ticker']}, {info['country']}, {info['currency']}, {info['unit']} to the database: {e}")
        conn.rollback()
        fail += 1
        continue 

cursor.close()
conn.close()
print(f"Successful insertions: {success}. Failed insertions: {fail}.")