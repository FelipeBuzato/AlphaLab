import psycopg2
import yfinance as yf
import pandas as pd
from datetime import datetime

## Connect to PostGres database
conn = psycopg2.connect(
    host="localhost",
    database="alphalab",
    user="postgres",
    password="alphalab",
    port="5432"
)
cursor = conn.cursor()

## Get tickers that are already in the database
cursor.execute(
    """
    SELECT ticker, asset_type
    FROM assets
    """
)

existing_assets = {ticker: asset_type for ticker, asset_type in cursor.fetchall()}
print(len(existing_assets), " assets currently in the database.")

## Get assets universe
assets_universe_df = pd.read_csv("../assets_universe.csv")
assets_universe = {ticker: asset_type for ticker, asset_type in assets_universe_df.values}

## For the future:
# Get ETF tickers
# Get crypto tickers
# Get index tickers 
# Get future tickers 
# Get commodity tickers

## Find out which tickers need to be added to the database
assets_to_add = {ticker: asset_type for ticker, asset_type in assets_universe.items()
                 if ticker not in existing_assets}

if(len(assets_to_add) >= 1):
    print(f"Adding {len(assets_to_add)} assets to the database.")
else:
    print("No new assets")

## Adding new tickers
query = """
INSERT INTO assets (
    ticker,
    company_name,
    exchange,
    currency,
    asset_type,
    country,
    sector,
    industry,
    timezone,
    last_updated
)
VALUES (
    %s,%s,%s,%s,%s,
    %s,%s,%s,%s,%s
)
ON CONFLICT (ticker)
DO NOTHING
"""

update_time = datetime.now()
success, fail = 0, 0

for ticker, asset_type in assets_to_add.items():
    try:
        asset = yf.Ticker(ticker)
        info = asset.info
        timezone = (info.get("exchangeTimezoneName") or info.get("timezone") or None)

        data = (
            ticker,
            info.get("longName"),
            info.get("exchange"),
            info.get("currency"),
            asset_type,
            info.get("country"),
            info.get("sector"),
            info.get("industry"),
            timezone,
            update_time
        )
        cursor.execute(query, data)
        conn.commit()
        print(f"ticker {ticker},{asset_type}: Inserted.")
        success += 1

    except Exception as e:
        print(f"Failed inserting ticker {ticker},{asset_type} to the database: {e}")
        conn.rollback()
        fail += 1
        continue 

cursor.close()
conn.close()
print(f"Successful insertions: {success}. Failed insertions: {fail}.")