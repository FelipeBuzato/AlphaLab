import pandas as pd
from sqlalchemy import create_engine, text, bindparam


engine = create_engine(
    "postgresql://postgres:alphalab@localhost:5432/alphalab"
)


def get_universe(asset_types=None):

    query = """
            SELECT * 
            FROM assets
            """
    params = {}

    if(asset_types is not None):

        if isinstance(asset_types, str):
            query += " WHERE asset_type = :asset_type"
            params['asset_type'] = asset_types

        elif(isinstance(asset_types, list)):
            query += " WHERE asset_type IN :asset_types"
            params['asset_types'] = asset_types
        
        else:
            raise TypeError("asset types must be None, a string or a list.")
    
    query += " ORDER BY ticker ASC"

    query = text(query)

    if isinstance(asset_types, list):
        query = query.bindparams(bindparam("asset_types", expanding=True))

    return pd.read_sql(query, engine, params=params)


def get_assets(assets=None):
    
    query = """
            SELECT * 
            FROM assets
            """
    params = {}

    if(assets is not None):

        if isinstance(assets, str):
            query += " WHERE ticker = :asset"
            params['asset'] = assets

        elif(isinstance(assets, list)):
            query += " WHERE ticker IN :assets"
            params['assets'] = assets
        
        else:
            raise TypeError("assets must be None, a string or a list.")
    
    query += " ORDER BY ticker ASC"

    query = text(query)

    if isinstance(assets, list):
        query = query.bindparams(bindparam("assets", expanding=True))

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


def get_prices(assets=None, start=None, end=None, field="close", pivot=False):
    prices = get_daily_prices(assets, start, end)

    if(not pivot):
        return prices[["date", "ticker", field]]
    else:
        return prices.pivot(index="date", columns="ticker", values=field)


def get_returns(assets=None, start=None, end=None, field="close"):
    prices = get_daily_prices(assets=assets, start=start, end=end)

    prices = prices.pivot(index="date", columns="ticker", values=field)
    returns = prices.pct_change()

    return returns