import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import warnings
from .execution.perfect_execution import PerfectExecutionExecutor
from .execution.fixed_slippage import FixedSlippageExecutor
from .execution.volume_slippage import VolumeSlippageExecutor


class BackTester:
    def __init__(self, prices_open, prices_close, volume=None, initial_capital=100000, rebalance='Daily', 
                 execution_method = 'volume slippage', transaction_cost_rate = 0.0005, 
                 slippage_rate=0.001, risk_free=None, benchmark=None):
        
        self.initial_capital = initial_capital
        self.rebalance = rebalance
        self.prices_open = prices_open
        self.prices_close = prices_close
        self.volume = volume
        self.execution_method = execution_method
        self.transaction_cost_rate = transaction_cost_rate
        self.slippage_rate = slippage_rate
        self.risk_free = risk_free
        self.benchmark = benchmark
        # Benchmark must be a strategy previously backtested!
        
        self.strategy_name = None
        self.start_date = None
        self.end_date = None
        self.cash = None
        self.weights = None
        self.realized_weights = None
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
    def run(self, strategy, start, end):

        if(isinstance(start, str)):
            start = datetime.strptime(start, "%Y-%m-%d").date()
        if(isinstance(end, str)):
            end = datetime.strptime(end, "%Y-%m-%d").date()
        
        if start >= end:
            raise ValueError("Start date must be before end date.")

        self.start_date = start
        self.end_date = end

        # Initialize strategy name and weights
        self.strategy_name = strategy['name']
        weights = strategy['weights']
        
        # Order executor
        self.order_executor = self.order_executor = self.get_order_executor(self.execution_method, self.transaction_cost_rate, self.slippage_rate)
        
        # Shift weights to avoid look-ahead bias
        self.weights = weights.shift(1).fillna(0)
        
        # Select backtest dates
        dates = self._align_dates(start, end)

        # Initialize shares, portfolio value and cash 
        initial_state_date = self.weights.index[0] - timedelta(days=1)
        new_index = self.weights.index.insert(0, initial_state_date)
        self.shares = pd.DataFrame(0.0, index=new_index, columns=self.weights.columns)
        self.cash = pd.Series(0.0, index=new_index)
        self.portfolio_value = pd.Series(0.0, index=self.weights.index)

        # Realized weights (weights computed at the close of each day)
        self.realized_weights = pd.DataFrame(0.0, index=self.weights.index, columns=self.weights.columns)

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

        if(self.rebalance == 'Daily'):
            if(previous_date.day != current_date.day):
                return True
            else:
                return False
        
        elif(self.rebalance == 'Montlhy'):
            if(previous_date.month != current_date.month):
                return True
            else:
                return False
            
        elif(self.rebalance == 'Yearly'):
            if(previous_date.year != current_date.year):
                return True
            else:
                return False
            
        elif(self.rebalance == "Weekly"):
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
        target_shares = (value_per_asset / prices_open).fillna(0)
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
        position_values = shares.fillna(0) * prices_close.fillna(0)
        self.portfolio_value.loc[date] = float(cash + position_values.sum())

        # Updating realized weights
        self.realized_weights.loc[date] = position_values / self.portfolio_value.loc[date]


    def get_backtest_results(self):
        # Daily Returns
        self.daily_returns = self.portfolio_value.pct_change()

        # Cummulative returns
        self.cum_daily_returns = self.portfolio_value / self.initial_capital - 1
        self.cum_return = float(self.portfolio_value.iloc[-1]) / self.initial_capital - 1

        # CAGR = Annualized cumulative return
        years = (self.portfolio_value.index[-1] - self.portfolio_value.index[0]).days / 365.25
        self.cagr = float((self.portfolio_value.iloc[-1] / self.initial_capital) ** (1 / years) - 1)

        # Drawdown
        running_max = self.portfolio_value.cummax()
        self.drawdown = (self.portfolio_value - running_max) / running_max
        self.max_drawdown = float(self.drawdown.min())

        # Rolling  Annualized Volatility
        self.rolling_volatility = self.daily_returns.rolling(window=252).std() * np.sqrt(252)
        
        # Annualized volatility
        self.annualized_volatility = float(self.daily_returns.std() * np.sqrt(252))

        # daily risk-free returns and risk-free portfolio
        if(self.risk_free is None):
            self.risk_free = {'name': None, 'values': pd.Series(0.0, index=self.portfolio_value.index)}
        self.risk_free['daily_returns'] = (1 + self.risk_free['values'] / 100)**(1/252)-1
        self.risk_free['cum_return'] = (1 + self.risk_free['daily_returns']).prod() - 1
        self.risk_free['portfolio_value'] = (1 + self.risk_free['daily_returns']).cumprod() * self.initial_capital

        # Sharpe ratio
        excess_return = self.daily_returns - self.risk_free['daily_returns']
        if(self.daily_returns.std() > 0):
            self.sharpe = float((excess_return.mean() / self.daily_returns.std()) * np.sqrt(252))
        else: 
            self.sharpe = np.nan

        # Rolling sharpe
        self.rolling_sharpe = (excess_return.rolling(window=252).mean() / self.rolling_volatility) * 252

        # Exposure
        self.exposure = 1 - self.cash.loc[self.portfolio_value.index] / self.portfolio_value
        
        # Trades
        orders = self.order_executor.orders_history
        if(len(orders) == 0):
            orders_columns = ["date", "ticker", "side", "shares", "market price", "execution price",
                             "transaction cost", "cash after transaction"]
            orders = pd.DataFrame(columns=orders_columns)
        else:
            orders = pd.DataFrame(orders)

        # Benchmark
        excess_return_over_benchmark, benchmark_correlation, beta, alpha = self.get_benchmark_stats()
        
        return {
            'Start Date': self.start_date,
            'End Date': self.end_date,
            'Strategy Name': self.strategy_name,
            'Rebalancing Frequency': self.rebalance,
            'Initial Capital': self.initial_capital,
            'Portfolio Value': self.portfolio_value,
            'Target Weights': self.weights,
            'Realized Weights': self.realized_weights,
            'Shares': self.shares,
            'Cash': self.cash,
            'Daily Returns': self.daily_returns,
            'Cumulative Daily Returns': self.cum_daily_returns,
            'Drawdown': self.drawdown,
            'Rolling Volatility': self.rolling_volatility,
            'Rolling Sharpe': self.rolling_sharpe,
            'Exposure': self.exposure,
            'Orders': orders,
            'Risk-free': self.risk_free,
            'Benchmark': self.benchmark,
            'Metrics': {
                'Min': float(self.portfolio_value.min()),
                'Max': float(self.portfolio_value.max()),
                'Cumulative Return': self.cum_return,
                'CAGR': self.cagr,
                'Max Drawdown': self.max_drawdown,
                'Volatility': self.annualized_volatility,
                'Sharpe': self.sharpe,
                'Benchmark': {
                    'Excess Return': excess_return_over_benchmark,
                    'Correlation': benchmark_correlation,
                    'Alpha': alpha,
                    'Beta': beta
                }
            }
        }


    def get_benchmark_stats(self):
        if(self.benchmark is None):
            self.benchmark = {'Strategy Name': None, 
                              'Portfolio Value': pd.Series(np.nan, index=self.portfolio_value.index),
                              'Metrics': {'Cumulative Return': None}}
            return None, None, None, None

        # Compute excess return over benchmark, correlation, beta and alpha
        benchmark_total_return = self.benchmark['Metrics']['Cumulative Return']
        excess_return = self.cum_return - benchmark_total_return

        benchmark_daily_returns = self.benchmark['Daily Returns']
        risk_free_daily_returns = self.risk_free['daily_returns']
        strategy_daily_returns = self.daily_returns

        correlation = strategy_daily_returns.corr(benchmark_daily_returns)

        rp = strategy_daily_returns - risk_free_daily_returns
        rb = benchmark_daily_returns - risk_free_daily_returns

        beta = rp.cov(rb) / rb.var()
        alpha_daily = rp.mean() - beta * rb.mean()
        alpha_annual = (1 + alpha_daily)**252 - 1

        return excess_return, correlation, beta, alpha_annual
            

    # Makes sure all dates in the weights df are the same dates in risk-free, benchmark
    # and prices dfs. Weigths df is the "source of truth"
    def _align_dates(self, start, end):
        self.weights = self.weights[(self.weights.index >= start) & (self.weights.index <= end)]
        dates = self.weights.index

        if(self.risk_free is not None):
            risk_free_values = self.risk_free['values']
            risk_free_values = risk_free_values[(risk_free_values.index >= start) & (risk_free_values.index <= end)]
            risk_free_values = risk_free_values.reindex(dates)
            # fills nans with the previous value. if first value is nan, fills with next value
            risk_free_values = risk_free_values.ffill().bfill()
            self.risk_free['values'] = risk_free_values

        if(self.benchmark is not None):
            benchmark_values = self.benchmark['Portfolio Value']
            benchmark_values = benchmark_values[(benchmark_values.index >= start) & (benchmark_values.index <= end)]
            benchmark_values = benchmark_values.reindex(dates)

            if benchmark_values.isna().any():
                warnings.warn("Benchmark does not fully cover the backtest period. Missing values were filled.", UserWarning)
                # fills nans with the previous value. if first value is nan, fills with next value
                benchmark = benchmark.ffill().bfill()
                
            self.benchmark['Portfolio Value'] = benchmark_values

        self._validate_prices_inputs()
        return dates.tolist()

    
    # Validate that open prices, close prices and weights have the same index and columns
    # It has to be true, since the weights df was built from the prices_df
    def _validate_prices_inputs(self):
        if not self.weights.index.isin(self.prices_open.index).all():
            raise ValueError("Some dates in weights are not present in prices_open.")

        if not self.weights.index.isin(self.prices_close.index).all():
            raise ValueError("Some dates in weights are not present in prices_close.")
        
        if not self.weights.columns.equals(self.prices_open.columns):
            raise ValueError("Weights and prices_open have different assets.")

        if not self.weights.columns.equals(self.prices_close.columns):
            raise ValueError("Weights and prices_close have different assets.")