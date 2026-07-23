import pandas as pd
import numpy as np
from datetime import datetime, timedelta
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
        self.orders_history = None


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

        # Initialize shares, portfolio value, cash and orders history
        initial_state_date = self.weights.index[0] - timedelta(days=1)
        new_index = self.weights.index.insert(0, initial_state_date)
        self.shares = pd.DataFrame(0.0, index=new_index, columns=self.weights.columns)
        self.cash = pd.Series(0.0, index=new_index)
        self.portfolio_value = pd.Series(0.0, index=self.weights.index)
        self.orders_history = []

        # initialize shares and cash
        self.shares.iloc[0] = 0
        self.cash.iloc[0] = self.initial_capital

        # Backtest
        previous_date = None

        for date in dates:
            # Rebalance or not rebalance
            if(previous_date is None or self.should_rebalance(previous_date, date)):
                if(previous_date is None): previous_date = self.shares.index[0]
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
        ## to rebalance the position (buy/sell assets). We use the open prices to do so
        open_prices = self.prices_open.loc[date]

        # Portfolio value before rebalancing
        cur_portfolio_value = float(self.cash.loc[previous_date])
        cur_portfolio_value += float((self.shares.loc[previous_date] * self.prices_open.loc[date]).sum())
        
        ## Now, compute the target shares amounts
        # Target weights
        weights = self.weights.loc[date]

        # How much value should be allocated in each asset
        value_per_asset = weights * cur_portfolio_value
        
        # How many shares of each asset match the asset's value
        target_shares = value_per_asset / open_prices
        target_shares = np.floor(target_shares)

        current_shares = self.shares.loc[previous_date]
        delta_shares = target_shares - current_shares
        current_cash = self.cash.loc[previous_date]

        ## Execute orders
        new_shares, new_cash = self.execute_orders(date, current_shares, delta_shares, current_cash)
        
        ## Update number of shares in the portfolio and cash amount
        self.shares.loc[date] = new_shares
        self.cash.loc[date] = new_cash
        

    def execute_orders(self, date, current_shares, delta_shares, cash, method='perfect execution'):
        
        buy_shares = delta_shares.clip(lower=0)
        sell_shares = (-delta_shares).clip(lower=0)

        if(method == 'perfect execution'):
            # execution prices
            execution_prices = self.prices_open.loc[date]

            # sell first
            cash += (sell_shares * execution_prices).sum()
            for ticker in sell_shares[sell_shares > 0].index:
                self.orders_history.append({
                    "date": date,
                    "ticker": ticker,
                    "side": "SELL",
                    "shares": sell_shares[ticker],
                    "price": execution_prices[ticker],
                    "cash after transaction": cash
                })

            # then buy
            cash -= (buy_shares * execution_prices).sum()
            for ticker in buy_shares[buy_shares > 0].index:
                self.orders_history.append({
                    "date": date,
                    "ticker": ticker,
                    "side": "BUY",
                    "shares": buy_shares[ticker],
                    "price": execution_prices[ticker],
                    "cash after transaction": cash
                })

            if(cash < 0):
                raise ValueError("Cash can not become negative.")

            new_shares = current_shares + delta_shares
            new_cash = float(cash)
            return new_shares, new_cash

        elif(method == 'fixed slippage'):
            pass

        else:
            raise ValueError("Execution method not found.")

    
    # At the end of the day, update portfolio value
    def update_portfolio_value(self, date):
        
        # Portfolio value is computed at the close of the day
        close_prices = self.prices_close.loc[date]

        # Compute portfolio value based on the number of shares of each asset
        shares = self.shares.loc[date]
        
        # New portfolio value
        new_value = float(self.cash.loc[date] + (shares * close_prices).sum())
        self.portfolio_value.loc[date] = new_value


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
            'Orders': pd.DataFrame(self.orders_history),
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