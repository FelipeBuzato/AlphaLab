from .order_executor import OrderExecutor
import numpy as np


class PerfectExecutionExecutor(OrderExecutor):
    def __init__(self, transaction_cost_rate):
        super().__init__()
        self.transaction_cost_rate = transaction_cost_rate


    def execute_orders(self, date, prices_open, current_shares, delta_shares, cash):
        buy_shares = delta_shares.clip(lower=0)
        sell_shares = (-delta_shares).clip(lower=0)

        # execution prices
        execution_prices = prices_open

        # sell first
        for ticker in sell_shares[sell_shares > 0].index:
            trade_value = sell_shares[ticker] * execution_prices[ticker]
            transaction_cost = trade_value * self.transaction_cost_rate
            cash += trade_value - transaction_cost

            self.orders_history.append({
                "date": date,
                "ticker": ticker,
                "side": "SELL",
                "shares": sell_shares[ticker],
                "price": execution_prices[ticker],
                "transaction cost": transaction_cost,
                "cash after transaction": cash
            })

        # then buy
        for ticker in buy_shares[buy_shares > 0].index:
            trade_value = buy_shares[ticker] * execution_prices[ticker]
            transaction_cost = trade_value * self.transaction_cost_rate
            cash_reduction = trade_value + transaction_cost

            # if the transaction costs result in the need of more cash than we actually
            # have, compute the maximum number of shares that can be bought 
            if(cash < cash_reduction):
                adjusted_buy_shares = self.adjust_buy_order(cash, execution_prices[ticker], self.transaction_cost_rate)
                print(f"Reducing buy order size for ticker {ticker} on {date}: {buy_shares[ticker]} -> {adjusted_buy_shares} shares (-{buy_shares[ticker]-adjusted_buy_shares} = -{(100*(1 - adjusted_buy_shares/buy_shares[ticker])):.2f}%).")
                
                buy_shares[ticker] = adjusted_buy_shares
                delta_shares[ticker] = adjusted_buy_shares
                
                if(adjusted_buy_shares == 0): continue

                trade_value = buy_shares[ticker] * execution_prices[ticker]
                transaction_cost = trade_value * self.transaction_cost_rate
                cash_reduction = trade_value + transaction_cost

            cash -= cash_reduction

            self.orders_history.append({
                "date": date,
                "ticker": ticker,
                "side": "BUY",
                "shares": buy_shares[ticker],
                "price": execution_prices[ticker],
                "transaction cost": transaction_cost,
                "cash after transaction": cash
            })

        if(cash < 0):
            raise ValueError("Cash can not become negative.")

        new_shares = current_shares + delta_shares
        new_cash = float(cash)
        return new_shares, new_cash
    

    def adjust_buy_order(self, cash, market_open_price, transaction_cost_rate):
        adjusted_shares = cash / (market_open_price * (1 + transaction_cost_rate))
        adjusted_shares = np.floor(adjusted_shares)
        return float(adjusted_shares)