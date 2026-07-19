""" 
This script contains the core implementation of algorithmic trading strategies

Data must be indexed by dates

The ouput of each strategy are the ideal weights each asset should have in the portfolio

The Backtester receives these weights and builds a portfolio with those targeted weights
and appropriate rebalancing strategy
"""

import sys
sys.path.append("..")
from Features.features import *


def top_n_equal_weights(data, n):
    rank = cross_sectional_rank(data)
    selected = rank <= n
    weights = selected.div(selected.sum(axis=1), axis="index").fillna(0)
    return weights


def momentum_strategy(prices, window, n, equal_weights=True):
    """
    MOMENTUM STRATEGY

    Buy assets with top n momentum.
    """
    mom = momentum(prices, window=window)
    if(equal_weights):
        return top_n_equal_weights(mom, n)
    else:
        return None # TODO
    

def MA_strategy(prices, long_window, short_window=None):
    """
    MA CROSSOVER STRATEGY

    Buy assets when short MA is greater than long MA.
    
    The portfolio will be equally weighted, that is, if there are 2 assets 
    whose short_ma is greater than long_ma at a certain date, the portfolio
    weights will be 50% each.

    If short window is None, the short window is simply the price.
    """
    if(short_window is not None and short_window >= long_window):
        raise ValueError("Short window must be smaller than long window.")
    
    short_ma = prices if short_window is None else sma(prices, window=short_window)
    long_ma = sma(prices, long_window)
    signal = short_ma > long_ma
    weights = signal.div(signal.sum(axis=1), axis="index").fillna(0)
    return weights