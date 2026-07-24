from .order_executor import OrderExecutor
import numpy as np


class VolumeSlippageExecutor(OrderExecutor):
    def __init__(self, transaction_cost_rate, volume):
        super().__init__()
        self.transaction_cost_rate = transaction_cost_rate
        self.volume = volume
        self.k = 0.05


    def execute_orders(self, date, prices_open, current_shares, delta_shares, cash):
        # make sure we don't trade when volume = 0
        volume = self.volume.loc[date]
        delta_shares = delta_shares.where(volume > 0, 0)
        
        buy_shares = delta_shares.clip(lower=0)
        sell_shares = (-delta_shares).clip(lower=0)
        
        # market prices
        market_open_prices = prices_open

        # participation
        participation = (abs(delta_shares) / volume).fillna(0)
        if(participation.max() > 1):
            offender = participation.idxmax()
            raise ValueError(f"{offender}: participation={participation[offender]:.2%} exceeds 100%.")

        # sell first
        for ticker in sell_shares[sell_shares > 0].index:
            slippage_rate = self.k * np.sqrt(participation[ticker])
            execution_sell_price = market_open_prices[ticker] * (1 - slippage_rate)
            trade_value = sell_shares[ticker] * execution_sell_price
            transaction_cost = trade_value * self.transaction_cost_rate
            cash += trade_value - transaction_cost

            self.orders_history.append({
                "date": date,
                "ticker": ticker,
                "side": "SELL",
                "shares": sell_shares[ticker],
                "market price": market_open_prices[ticker],
                "execution price": execution_sell_price,
                "transaction cost": transaction_cost,
                "cash after transaction": cash
            })

        # then buy
        for ticker in buy_shares[buy_shares > 0].index:
            slippage_rate = self.k * np.sqrt(participation[ticker])
            execution_buy_price = market_open_prices[ticker] * (1 + slippage_rate)
            trade_value = buy_shares[ticker] * execution_buy_price
            transaction_cost = trade_value * self.transaction_cost_rate
            cash_reduction = trade_value + transaction_cost
            
            # if slippage + transaction costs result in the need of more cash than we actually
            # have, compute the maximum number of shares that can be bought 
            if(cash < cash_reduction):
                adjusted_buy_shares = self.adjust_buy_order(cash, volume[ticker], market_open_prices[ticker], self.transaction_cost_rate, self.k, buy_shares[ticker])
                print(f"Reducing buy order size for ticker {ticker} on {date}: {buy_shares[ticker]} -> {adjusted_buy_shares} shares (-{buy_shares[ticker]-adjusted_buy_shares} = -{(100*(1 - adjusted_buy_shares/buy_shares[ticker])):.2f}%).")
                
                buy_shares[ticker] = adjusted_buy_shares
                delta_shares[ticker] = adjusted_buy_shares
                
                if(adjusted_buy_shares == 0): continue

                participation[ticker] = adjusted_buy_shares / volume[ticker]
                slippage_rate = self.k * np.sqrt(participation[ticker])
                execution_buy_price = market_open_prices[ticker] * (1 + slippage_rate)
                trade_value = buy_shares[ticker] * execution_buy_price
                transaction_cost = trade_value * self.transaction_cost_rate
                cash_reduction = trade_value + transaction_cost
            
            cash -= cash_reduction

            self.orders_history.append({
                "date": date,
                "ticker": ticker,
                "side": "BUY",
                "shares": buy_shares[ticker],
                "market price": market_open_prices[ticker],
                "execution price": execution_buy_price,
                "transaction cost": transaction_cost,
                "cash after transaction": cash
            })

        if(cash < 0):
            raise ValueError(f"Cash ({cash}, {date}) can not become negative. {delta_shares}, {volume}, {participation}")

        new_shares = current_shares + delta_shares
        new_cash = float(cash)
        return new_shares, new_cash
    

    def adjust_buy_order(self, cash, volume, market_open_price, transaction_cost_rate, k, unadjusted_shares):
        if(volume <= 0):
            return 0
        
        low, high = 0, int(unadjusted_shares)

        while low < high:
            mid = (low + high + 1) // 2

            execution_price = market_open_price * (1 + k * np.sqrt(mid / volume))
            total_cost = mid * execution_price * (1 + transaction_cost_rate)

            if total_cost <= cash:
                low = mid
            else:
                high = mid - 1

        return float(low)