import pandas as pd
from sqlalchemy import create_engine, text, bindparam


engine = create_engine(
    "postgresql://postgres:alphalab@localhost:5432/alphalab"
)


def get_assets(assets=None, asset_types=None):

    query = """
            SELECT * 
            FROM assets
            """
    params = {}
    conditions = []

    if(assets is not None):
        if isinstance(assets, str):
            conditions.append("ticker = :asset")
            params['asset'] = assets

        elif(isinstance(assets, list)):
            conditions.append("ticker IN :assets")
            params['assets'] = assets
        
        else:
            raise TypeError("assets must be None, a string or a list.")

    if(asset_types is not None):
        if isinstance(asset_types, str):
            conditions.append("asset_type = :asset_type")
            params['asset_type'] = asset_types

        elif(isinstance(asset_types, list)):
            conditions.append("asset_type IN :asset_types")
            params['asset_types'] = asset_types
        
        else:
            raise TypeError("asset_types must be None, a string or a list.")

    # Add conditions to query
    if(conditions):
        query += " WHERE " + " AND ".join(conditions)
    
    # Sorting criteria
    query += " ORDER BY ticker ASC"

    query = text(query)

    if isinstance(assets, list):
        query = query.bindparams(bindparam("assets", expanding=True))

    if isinstance(asset_types, list):
        query = query.bindparams(bindparam("asset_types", expanding=True))

    return pd.read_sql(query, engine, params=params)


def get_rates_info(rates=None, countries=None):
    query = """
            SELECT * 
            FROM rates
            """
    params = {}
    conditions = []

    if(rates is not None):
        if isinstance(rates, str):
            conditions.append("name = :rate")
            params['rate'] = rates

        elif(isinstance(rates, list)):
            conditions.append("name IN :rates")
            params['rates'] = rates
        
        else:
            raise TypeError("rates must be None, a string or a list.")

    if(countries is not None):
        if isinstance(countries, str):
            conditions.append("country = :country")
            params['country'] = countries

        elif(isinstance(countries, list)):
            conditions.append("country IN :countries")
            params['countries'] = countries
        
        else:
            raise TypeError("countries must be None, a string or a list.")

    # Add conditions to query
    if(conditions):
        query += " WHERE " + " AND ".join(conditions)
    
    # Sorting criteria
    query += " ORDER BY name ASC"

    query = text(query)

    if isinstance(rates, list):
        query = query.bindparams(bindparam("rates", expanding=True))

    if isinstance(countries, list):
        query = query.bindparams(bindparam("countries", expanding=True))

    return pd.read_sql(query, engine, params=params)


def get_daily_prices(assets=None, start=None, end=None):
    
    query = """
            SELECT * 
            FROM daily_prices
            """
    params = {}
    conditions = []

    if(start and end and start > end):
        raise ValueError("Start date greater than end date.")
    
    # Assets
    if(assets is not None):
        
        if isinstance(assets, str):
            conditions.append("ticker = :asset")
            params['asset'] = assets

        elif(isinstance(assets, list)):
            conditions.append("ticker IN :assets")
            params['assets'] = assets
        
        else:
            raise TypeError("assets must be None, a string or a list.")
    
    # start date
    if(start is not None):
        conditions.append("date >= :start")
        params['start'] = start
    
    # end date
    if(end is not None):
        conditions.append("date <= :end")
        params['end'] = end
    
    # Add conditions to query
    if(conditions):
        query += " WHERE " + " AND ".join(conditions)
    
    # Sorting criteria
    query += " ORDER BY date ASC, ticker ASC"

    query = text(query)

    if isinstance(assets, list):
        query = query.bindparams(bindparam("assets", expanding=True))

    return pd.read_sql(query, engine, params=params)


def get_rates_values(rates=None, start=None, end=None):

    query = """
            SELECT * 
            FROM rates_values
            """
    params = {}
    conditions = []

    if(start and end and start > end):
        raise ValueError("Start date greater than end date.")
    
    # Assets
    if(rates is not None):
        
        if isinstance(rates, str):
            conditions.append("name = :rate")
            params['rate'] = rates

        elif(isinstance(rates, list)):
            conditions.append("name IN :rates")
            params['rates'] = rates
        
        else:
            raise TypeError("rates must be None, a string or a list.")
    
    # start date
    if(start is not None):
        conditions.append("date >= :start")
        params['start'] = start
    
    # end date
    if(end is not None):
        conditions.append("date <= :end")
        params['end'] = end
    
    # Add conditions to query
    if(conditions):
        query += " WHERE " + " AND ".join(conditions)
    
    # Sorting criteria
    query += " ORDER BY date ASC, name ASC"

    query = text(query)

    if isinstance(rates, list):
        query = query.bindparams(bindparam("rates", expanding=True))

    return pd.read_sql(query, engine, params=params)


def get_dividends(assets=None, start=None, end=None):
    query = """
            SELECT * 
            FROM dividends
            """
    params = {}
    conditions = []

    if(start and end and start > end):
        raise ValueError("Start date greater than end date.")
    
    # Assets
    if(assets is not None):
        
        if isinstance(assets, str):
            conditions.append("ticker = :asset")
            params['asset'] = assets

        elif(isinstance(assets, list)):
            conditions.append("ticker IN :assets")
            params['assets'] = assets
        
        else:
            raise TypeError("assets must be None, a string or a list.")
    
    # start date
    if(start is not None):
        conditions.append("ex_date >= :start")
        params['start'] = start
    
    # end date
    if(end is not None):
        conditions.append("ex_date <= :end")
        params['end'] = end
    
    # Add conditions to query
    if(conditions):
        query += " WHERE " + " AND ".join(conditions)
    
    # Sorting criteria
    query += " ORDER BY ex_date ASC, ticker ASC"

    query = text(query)

    if isinstance(assets, list):
        query = query.bindparams(bindparam("assets", expanding=True))

    return pd.read_sql(query, engine, params=params)


def get_latest_price(assets=None):
    query = """
            SELECT *
            FROM (
                SELECT ticker, date, open, high, low, close, adj_close, volume, last_updated
                FROM (
                    SELECT *,
                    MAX(date) OVER (PARTITION BY ticker ORDER BY date DESC ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS max_date
                    FROM daily_prices
                    )
                WHERE date = max_date
            )
            """
    params = {}
    conditions = []

    # Assets
    if(assets is not None):
        
        if isinstance(assets, str):
            conditions.append("ticker = :asset")
            params['asset'] = assets

        elif(isinstance(assets, list)):
            conditions.append("ticker IN :assets")
            params['assets'] = assets
        
        else:
            raise TypeError("assets must be None, a string or a list.")
    
    # Add conditions to query
    if(conditions):
        query += " WHERE " + " AND ".join(conditions)
    
    # Sorting criteria
    query += " ORDER BY ticker ASC"

    query = text(query)

    if isinstance(assets, list):
        query = query.bindparams(bindparam("assets", expanding=True))

    return pd.read_sql(query, engine, params=params)


def get_latest_dividend(assets=None):
    query = """
            SELECT *
            FROM (
                SELECT ticker, ex_date, dividend, last_updated
                FROM (
                    SELECT *,
                    MAX(ex_date) OVER (PARTITION BY ticker ORDER BY ex_date DESC ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS max_date
                    FROM dividends
                    )
                WHERE ex_date = max_date
            )
            """
    params = {}
    conditions = []

    # Assets
    if(assets is not None):
        
        if isinstance(assets, str):
            conditions.append("ticker = :asset")
            params['asset'] = assets

        elif(isinstance(assets, list)):
            conditions.append("ticker IN :assets")
            params['assets'] = assets
        
        else:
            raise TypeError("assets must be None, a string or a list.")
    
    # Add conditions to query
    if(conditions):
        query += " WHERE " + " AND ".join(conditions)
    
    # Sorting criteria
    query += " ORDER BY ticker ASC"

    query = text(query)

    if isinstance(assets, list):
        query = query.bindparams(bindparam("assets", expanding=True))

    return pd.read_sql(query, engine, params=params)


def get_latest_rate(rates=None):
    query = """
            SELECT *
            FROM (
                SELECT name, date, value, last_updated
                FROM (
                    SELECT *,
                    MAX(date) OVER (PARTITION BY name ORDER BY date DESC ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS max_date
                    FROM rates_values
                    )
                WHERE date = max_date
            )
            """
    params = {}
    conditions = []

    # Rates
    if(rates is not None):
        
        if isinstance(rates, str):
            conditions.append("name = :rate")
            params['rate'] = rates

        elif(isinstance(rates, list)):
            conditions.append("name IN :rates")
            params['rates'] = rates
        
        else:
            raise TypeError("rates must be None, a string or a list.")
    
    # Add conditions to query
    if(conditions):
        query += " WHERE " + " AND ".join(conditions)
    
    # Sorting criteria
    query += " ORDER BY name ASC"

    query = text(query)

    if isinstance(rates, list):
        query = query.bindparams(bindparam("rates", expanding=True))

    return pd.read_sql(query, engine, params=params)


def get_prices(assets=None, start=None, end=None, field="close", pivot=False):
    prices = get_daily_prices(assets, start, end)

    if(not pivot):
        return prices[["date", "ticker", field]]
    else:
        return prices.pivot(index="date", columns="ticker", values=field)


def get_rates(rates=None, start=None, end=None, pivot=False):
    rates_values = get_rates_values(rates, start, end)

    if(not pivot):
        return rates_values[["date", "name", "value"]]
    else:
        return rates_values.pivot(index="date", columns="name", values="value")