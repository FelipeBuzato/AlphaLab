## This script contains the computation of features 
## The functions in this script are meant to receive dataframes and return dataframes
## The columns of the dataframes must be the assets' tickers, and it must be indexed by dates. 

import numpy as np


def get_returns(prices):
    return prices.pct_change() 


def get_log_returns(prices):
    return np.log(prices / prices.shift(1))


def momentum(data, window=252):
    return data.pct_change(window) 


def realized_vol(prices, window=20):
    returns = get_returns(prices)
    return returns.rolling(window).std() * np.sqrt(252)


def sma(prices, window=50):
    return prices.rolling(window).mean()


def ema(prices, window=50):
    return prices.ewm(span=window, adjust=False).mean()


def rolling_beta():
    pass


def rsi():
    pass


def cross_sectional_rank(data, ascending=False):
    return data.rank(axis=1, ascending=ascending, method="dense")


def zscore(data):
    mean = data.mean(axis=1)
    std = data.std(axis=1).replace(0, np.nan)

    return data.sub(mean, axis=0).div(std, axis=0)

