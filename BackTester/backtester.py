import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from .execution.perfect_execution import PerfectExecutionExecutor
from .execution.fixed_slippage import FixedSlippageExecutor
from .execution.volume_slippage import VolumeSlippageExecutor


class BackTester:
    def __init__(self, prices_open, prices_close, volume=None, initial_capital=100000, rebalance='D', 
                 execution_method = 'volume slippage', transaction_cost_rate = 0.0005, 
                 slippage_rate=0.001):
        
        self.initial_capital = initial_capital
        self.rebalance = rebalance
        self.prices_open = prices_open
        self.prices_close = prices_close
        self.volume = volume
        self.execution_method = execution_method
        self.transaction_cost_rate = transaction_cost_rate
        self.slippage_rate = slippage_rate
        
        self.cash = None
        self.weights = None
        self.shares = None
        self.portfolio_value = None
        self.order_executor = None


    def get_order_executor(self, execution_method, transaction_cost_rate, slippage_rate):
        if(execution_method == 'perfect execution'):
            return PerfectExecutionExecutor(transaction_cost_rate)
        
        elif(execution_method == 'fixed slippage'):
            return FixedSlippageExecutor(transaction_cost_rate, slippage_rate)
        
        elif(execution_method == 'volume slippage'):
            if(self.volume is None):
                raise ValueError("For volume-based slippage, you must pass Volume in the Backtester constructor.")
            
            volume = self.volume.shift(1).fillna(self.volume.median())
            return VolumeSlippageExecutor(transaction_cost_rate, volume)
        
        else:
            raise ValueError("Execution method invalid.")


    # Run backtest
    def run(self, weights, start, end):

        if(isinstance(start, str)):
            start = datetime.strptime(start, "%Y-%m-%d").date()
        if(isinstance(end, str)):
            end = datetime.strptime(end, "%Y-%m-%d").date()
        
        if start >= end:
            raise ValueError("Start date must be before end date.")
        
        # Order executor
        self.order_executor = self.order_executor = self.get_order_executor(self.execution_method, self.transaction_cost_rate, self.slippage_rate)
        
        # Shift weights to avoid look-ahead bias
        self.weights = weights.shift(1).fillna(0)
        
        # Select backtest dates
        self.weights = self.weights[(self.weights.index >= start) & (self.weights.index <= end)]
        dates = self.weights.index.tolist()
        self._validate_inputs()

        # Initialize shares, portfolio value and cash 
        initial_state_date = self.weights.index[0] - timedelta(days=1)
        new_index = self.weights.index.insert(0, initial_state_date)
        self.shares = pd.DataFrame(0.0, index=new_index, columns=self.weights.columns)
        self.cash = pd.Series(0.0, index=new_index)
        self.portfolio_value = pd.Series(0.0, index=self.weights.index)

        # initialize shares and cash
        self.shares.iloc[0] = 0
        self.cash.iloc[0] = self.initial_capital

        # Backtest
        previous_date = None

        for date in dates:
            # Rebalance or not rebalance
            if(previous_date is None or self.should_rebalance(previous_date, date)):
                if(previous_date is None): previous_date = initial_state_date
                self.rebalance_portfolio(previous_date, date)
            else:
                self.shares.loc[date] = self.shares.loc[previous_date]
                self.cash.loc[date] = self.cash.loc[previous_date]

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
            
        elif(self.rebalance == "W"):
            if(current_date.isocalendar()[1] != previous_date.isocalendar()[1]):
                return True
            else:
                return False
        
        else:
            raise ValueError("Rebalance frequency not found. Please check.")
        
    
    # Match portfolio shares with current weights
    def rebalance_portfolio(self, previous_date, date):

        ## First, compute current portfolio value - the available amount we'll have 
        ## to rebalance the position (buy/sell assets). 
        # We use the open prices to do so
        prices_open = self.prices_open.loc[date]
        current_shares = self.shares.loc[previous_date]
        current_cash = self.cash.loc[previous_date]

        # Portfolio value before rebalancing
        cur_portfolio_value = float(current_cash)
        cur_portfolio_value += float((current_shares * prices_open).sum())
        
        ## Now, compute the target shares amounts
        # Target weights
        weights = self.weights.loc[date]

        # How much value should be allocated in each asset
        value_per_asset = weights * cur_portfolio_value
        
        # How many shares of each asset match the asset's value
        target_shares = value_per_asset / prices_open
        target_shares = np.floor(target_shares)
        delta_shares = target_shares - current_shares

        ## Execute orders
        new_shares, new_cash = self.order_executor.execute_orders(date, prices_open, current_shares, delta_shares, current_cash)
        
        ## Update number of shares in the portfolio and cash amount
        self.shares.loc[date] = new_shares
        self.cash.loc[date] = new_cash

    
    # At the end of the day, update portfolio value
    def update_portfolio_value(self, date):
        # Portfolio value is computed at the close of the day
        prices_close = self.prices_close.loc[date]

        # Compute portfolio value based on the number of shares of each asset
        shares = self.shares.loc[date]
        cash = self.cash.loc[date]
        
        # New portfolio value
        self.portfolio_value.loc[date] = float(cash + (shares * prices_close).sum())


    def get_backtest_results(self):
        # Daily Returns
        self.daily_returns = self.portfolio_value.pct_change()
        self.daily_returns.iloc[0] = 0.0

        # Cummulative returns
        self.cum_daily_returns = float(self.portfolio_value.iloc[-1]) / self.initial_capital - 1

        # Drawdown
        running_max = self.portfolio_value.cummax()
        self.drawdown = (self.portfolio_value - running_max) / running_max
        self.max_drawdown = float(self.drawdown.min())

        # Annualized volatility
        self.annualized_volatility = float(self.daily_returns.iloc[1:].std() * np.sqrt(252))

        # CAGR = Annualized cumulative return
        years = (self.portfolio_value.index[-1] - self.portfolio_value.index[0]).days / 365.25
        self.cagr = float((self.portfolio_value.iloc[-1] / self.initial_capital) ** (1 / years) - 1)

        # Sharpe ratio
        excess_return = self.daily_returns.iloc[1:].mean()  # assuming no benchmark     # TODO Add benchmark
        self.sharpe = float((excess_return / self.daily_returns.iloc[1:].std()) * np.sqrt(252))

        return {
            'Orders': pd.DataFrame(self.order_executor.orders_history),
            'Shares': self.shares,
            'Portfolio Value': self.portfolio_value,
            'Weights': self.weights,
            'Cash': self.cash,
            'Daily Returns': self.daily_returns,
            'Cumulative Daily Returns': self.cum_daily_returns,
            'Metrics': {
                'Sharpe': self.sharpe,
                'Min': float(self.portfolio_value.min()),
                'Max': float(self.portfolio_value.max()),
                'Drawdown': self.drawdown,
                'Max Drawdown': self.max_drawdown,
                'Volatility': self.annualized_volatility,
                'CAGR': self.cagr
            }
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