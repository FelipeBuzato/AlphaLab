from abc import ABC, abstractmethod


class OrderExecutor(ABC):
    def __init__(self):
        self.orders_history = []

    def clear_orders_history(self):
        self.orders_history = []

    @abstractmethod
    def execute_orders(self, date, prices_open, current_shares, delta_shares, cash):
        pass