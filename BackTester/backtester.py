import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt


class BackTester:
    def __init__(self, prices_open, prices_close, initial_capital=100000, rebalance='D', 
                 execution = 'next_open'):
        self.initial_capital = initial_capital
        self.rebalance = rebalance
        self.prices_open = prices_open
        self.prices_close = prices_close
        self.execution = execution   # TODO: Support different execution methods
        
        self.weights = None
        self.shares = None
        self.portfolio_value = None


    # Run backtest
    def run(self, weights, start, end):
        if(isinstance(start, str)):
            start = datetime.strptime(start, "%Y-%m-%d").date()
        if(isinstance(end, str)):
            end = datetime.strptime(end, "%Y-%m-%d").date()
        
        if start >= end:
            raise ValueError("Start date must be before end date.")
        
        # Shift weights to avoid look-ahead bias
        self.weights = weights.shift(1).fillna(0)
        
        # Select backtest dates
        self.weights = self.weights[(self.weights.index >= start) & (self.weights.index <= end)]
        dates = self.weights.index.tolist()
        self._validate_inputs()

        # Initialize shares and portfolio value
        self.shares = pd.DataFrame(0.0, index=self.weights.index, columns=self.weights.columns)
        self.portfolio_value = pd.Series(0.0, index=self.weights.index)

        # Backtest
        previous_date = None

        for date in dates:
            # Rebalance or not rebalance
            if(previous_date is None or self.should_rebalance(previous_date, date)):
                self.rebalance_portfolio(previous_date, date)
            else:
                self.shares.loc[date] = self.shares.loc[previous_date]

            # Update portfolio value
            self.update_portfolio_value(date)

            previous_date = date
        
        return self.get_backtest_results()
    

    # Check if should rebalance portfolio based on the rebalance strategy
    def should_rebalance(self, previous_date, current_date):

        if(self.rebalance == 'D'):
            if(previous_date.day != current_date.day):
                return True
            else:
                return False
        
        elif(self.rebalance == 'M'):
            if(previous_date.month != current_date.month):
                return True
            else:
                return False
            
        elif(self.rebalance == 'Y'):
            if(previous_date.year != current_date.year):
                return True
            else:
                return False
        
        else:
            raise ValueError("Rebalance frequency not found. Please check.")
        
    
    # Match portfolio shares with current weights
    def rebalance_portfolio(self, previous_date, date):

        # Use open prices to rebalance (buy/sell)
        open_prices = self.prices_open.loc[date]

        # Portfolio value before rebalancing
        if(previous_date is None):
            cur_portfolio_value = self.initial_capital
        else:
            cur_portfolio_value = float((self.shares.loc[previous_date] * self.prices_open.loc[date]).sum())
        
        # New weights
        weights = self.weights.loc[date]

        # How much value should be allocated in each asset
        value_per_asset = weights * cur_portfolio_value
        
        # How many shares of each asset match the asset's value
        shares_per_asset = value_per_asset / open_prices
        self.shares.loc[date] = shares_per_asset

    
    # At the end of the day, update portfolio value
    def update_portfolio_value(self, date):
        
        # Portfolio value is computed at the close of the day
        close_prices = self.prices_close.loc[date]

        # Compute portfolio value based on the number of shares of each asset
        shares = self.shares.loc[date]
        
        # New portfolio value
        new_value = float((shares * close_prices).sum())
        self.portfolio_value.loc[date] = new_value


    def get_backtest_results(self):
        # Daily Returns
        #daily_returns = self.portfolio_value.pct_change().fillna(0)

        # Cummulative returns
        #cumulative_returns = self.portfolio_value

        return {
            'Shares': self.shares,
            'Portfolio Value': self.portfolio_value,
            'Weights': self.weights,
            #'Daily Returns': ....,
            #'Cumulative Returns': ,
            #'Metrics': {
            #    'Sharpe': ...,
            #    'Max Drawdown': ...,
            #    'Volatility': ...,
            #    'CAGR': ...
            #}
        }
    

    # Validate that open prices, close prices and weights have the same index and columns
    def _validate_inputs(self):
        if not self.weights.index.isin(self.prices_open.index).all():
            raise ValueError("Some dates in weights are not present in prices_open.")

        if not self.weights.index.isin(self.prices_close.index).all():
            raise ValueError("Some dates in weights are not present in prices_close.")
        
        if not self.weights.columns.equals(self.prices_open.columns):
            raise ValueError("Weights and prices_open have different assets.")

        if not self.weights.columns.equals(self.prices_close.columns):
            raise ValueError("Weights and prices_close have different assets.")


    def plot_portfolio_value(self):
        if self.portfolio_value is None:
            raise ValueError("Run the backtest before plotting.")

        self.portfolio_value.plot(figsize=(10, 5))
        plt.title("Portfolio Value")
        plt.xlabel("Date")
        plt.ylabel("Portfolio Value")
        plt.grid(True)
        plt.show()