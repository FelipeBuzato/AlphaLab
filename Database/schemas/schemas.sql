CREATE TABLE IF NOT EXISTS assets (
    ticker VARCHAR(20) PRIMARY KEY,
    company_name VARCHAR(255), 
    exchange VARCHAR(30),
    currency VARCHAR(10),
    asset_type VARCHAR(30),
    country VARCHAR(100),
    sector VARCHAR(100),
    industry VARCHAR(100),
    timezone VARCHAR(100),
    
    last_updated TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_prices (
    ticker VARCHAR(20) REFERENCES assets(ticker),
    date DATE,

    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION, 
    close DOUBLE PRECISION,
    adj_close DOUBLE PRECISION,
    volume BIGINT,

    last_updated TIMESTAMP,

    PRIMARY KEY (ticker, date)
);

CREATE TABLE IF NOT EXISTS dividends (
    ticker VARCHAR(20) REFERENCES assets(ticker),
    ex_date DATE,
    dividend DOUBLE PRECISION,

    last_updated TIMESTAMP,

    PRIMARY KEY (ticker, ex_date)
);