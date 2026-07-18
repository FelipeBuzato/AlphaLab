import psycopg2
import yfinance as yf
import pandas as pd
from datetime import datetime
from datetime import timedelta


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
    SELECT ticker
    FROM assets
    ORDER BY ticker ASC
    """)

tickers = {output[0] for output in cursor.fetchall()}

## Query for adding new market data
insert_query = """
INSERT INTO daily_prices (
    ticker,
    date,
    open,
    high,
    low,
    close,
    adj_close,
    volume,
    last_updated
)
VALUES (
    %s,%s,%s,%s,%s,
    %s,%s,%s,%s
)
ON CONFLICT (ticker, date)
DO NOTHING
"""

select_query = """
            SELECT MAX(date)
            FROM daily_prices
            WHERE ticker = %s
            """

fail, success = 0, 0

for ticker in tickers:

    try:
        asset = yf.Ticker(ticker)
        update_time = datetime.now()

        # find out the last date that has already been added to the database
        cursor.execute(select_query, (ticker,))
        latest_date = cursor.fetchall()[0][0]

        if latest_date is None:
            history = asset.history(period="max", interval="1d", auto_adjust=False)
        else:
            start_date = latest_date + timedelta(days=1)
            history = asset.history(start=start_date, interval="1d", auto_adjust=False)
            history = history[history.index.date > latest_date]

        if(history.empty):
            print(f"No new daily price data for {ticker}.")
            continue
        
        rows = []
        for date, row in history.iterrows():
            rows.append((
                ticker,
                date.date(),
                row["Open"].item(),
                row["High"].item(),
                row["Low"].item(),
                row["Close"].item(),
                row["Adj Close"].item(),
                row["Volume"].item(),
                update_time
            ))

        cursor.executemany(insert_query, rows)
        conn.commit()
        print(f"{ticker}: inserted {len(rows)} rows.")
        success+=1

    except Exception as e:
        print(f"Failed updating daily prices for ticker {ticker}: {e}")
        conn.rollback()
        fail+=1
        continue

cursor.close()
conn.close()
print(f"Successful updates: {success}. Failed updates: {fail}.")