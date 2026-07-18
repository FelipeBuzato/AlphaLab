import psycopg2
import yfinance as yf
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

## Adding new equity tickers
insert_query = """
INSERT INTO dividends (
    ticker,
    ex_date,
    dividend,
    last_updated
)
VALUES (
    %s,%s,%s,%s
)
ON CONFLICT (ticker, ex_date)
DO NOTHING
"""

select_query = """
            SELECT MAX(ex_date)
            FROM dividends
            WHERE ticker = %s
            """

success, fail = 0, 0

for ticker in tickers:

    try:
        asset = yf.Ticker(ticker)
        update_time = datetime.now()

        # find out the last date that has already been added to the database
        cursor.execute(select_query, (ticker,))
        latest_date = cursor.fetchall()[0][0]

        dividends = asset.dividends
        if latest_date is not None:
            start_date = latest_date + timedelta(days=1)
            dividends = dividends[dividends.index.date >= start_date]
        
        if(dividends.empty):
            print(f"No new dividend data for {ticker}.")
            continue
        
        rows=[]
        for ex_date, dividend in dividends.items():
                rows.append((
                    ticker,
                    ex_date.date(),
                    float(dividend),
                    update_time
                ))

        cursor.executemany(insert_query, rows)
        conn.commit()
        print(f"{ticker}: inserted {len(rows)} dividend rows.")
        success+=1

    except Exception as e:
        print(f"Failed updating dividends for ticker {ticker}: {e}")
        conn.rollback()
        fail+=1
        continue
    
cursor.close()
conn.close()
print(f"Successful updates: {success}. Failed updates: {fail}.")