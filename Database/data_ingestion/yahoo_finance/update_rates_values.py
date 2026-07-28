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
    SELECT name, ticker
    FROM rates
    ORDER BY name ASC
    """)

rates = {name: ticker for name, ticker in cursor.fetchall()}

## Query for adding new market data
insert_query = """
INSERT INTO rates_values (
    name,
    date,
    value,
    last_updated
)
VALUES (
    %s,%s,%s,%s
)
ON CONFLICT (name, date)
DO NOTHING
"""

select_query = """
            SELECT MAX(date)
            FROM rates_values
            WHERE name = %s
            """

fail, success = 0, 0

for rate_name, ticker in rates.items():

    try:
        rate_info = yf.Ticker(ticker)
        update_time = datetime.now()

        # find out the last date that has already been added to the database
        cursor.execute(select_query, (rate_name,))
        latest_date = cursor.fetchall()[0][0]

        if latest_date is None:
            history = rate_info.history(period="max", interval="1d")
        else:
            start_date = latest_date
            if(latest_date < datetime.today().date()):
                start_date += timedelta(days=1)
            history = rate_info.history(start=start_date, interval="1d")
            history = history[history.index.date > latest_date]

        if(history.empty):
            print(f"No new rate values for {rate_name}.")
            continue
        
        rows = []
        for date, row in history.iterrows():
            rows.append((
                rate_name,
                date.date(),
                row["Close"].item(),
                update_time
            ))

        cursor.executemany(insert_query, rows)
        conn.commit()
        print(f"{rate_name}: inserted {len(rows)} rows.")
        success+=1

    except Exception as e:
        print(f"Failed updating rate values for rate {rate_name}: {e}")
        conn.rollback()
        fail+=1
        continue

cursor.close()
conn.close()
print(f"Successful updates: {success}. Failed updates: {fail}.")