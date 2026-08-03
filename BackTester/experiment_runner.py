from Database.queries import *
from BackTester.backtester import BackTester
from Strategies.strategies import *


class ExperimentRunner:
    def __init__(self, experiments):
        self.experiments = experiments
        self.results = []


    def run(self):
        for experiment in self.experiments:
            # backtest strategy
            result = self.run_experiment(experiment)
            self.results.append(result)
            print(f"Done backtesting {experiment.name}.")
        return self.results


    def run_experiment(self, experiment):
        # Backtester Parameters
        backtester_params = experiment.backtester_params()
        start, end = experiment.start, experiment.end

        if(experiment.risk_free is not None):
            # Build risk-free rate object
            rate_name = experiment.risk_free
            rate_values = get_rates(rates=rate_name, start=start, end=end, pivot=True).squeeze()
            risk_free = {'name': rate_name, 'values': rate_values}
        else: 
            risk_free = None

        backtester_params['risk_free'] = risk_free

        if(experiment.benchmark_name is not None):
            # Run benchmark backtest
            benchmark_backtester_params = backtester_params.copy()
            benchmark_info = experiment.benchmark_info()
            benchmark = self.execute_backtest(benchmark_backtester_params, benchmark_info, start, end)
        else:
            benchmark = None

        backtester_params['benchmark'] = benchmark

        # Backtest Strategy
        strategy_info = experiment.strategy_info()
        result = self.execute_backtest(backtester_params, strategy_info, start, end)
        return result


    def run_strategy(self, strategy_info):
        strategy_name = strategy_info['name']
        strategy_type = strategy_info['strategy']
        strategy_params = strategy_info['params'].copy()
        strategy = STRATEGIES[strategy_type]
        assets = strategy_params.pop('assets')
        field = strategy_params.pop('field')
        prices = get_prices(assets=assets, field=field, pivot=True)
        strategy_params['prices'] = prices

        ideal_weights = strategy(**strategy_params)
        return {'name': strategy_name, 'weights': ideal_weights}


    def execute_backtest(self, backtester_params, strategy_info, start, end):
        # Generate ideal weights according to strategy
        strategy = self.run_strategy(strategy_info)
        strategy['params'] = strategy_info['params']
        
        # Backtest Strategy
        assets = strategy_info['params']['assets']
        backtester_params['prices_open'] = get_prices(assets=assets, field='open', pivot=True)
        backtester_params['prices_close'] = get_prices(assets=assets, field='close', pivot=True)
        backtester_params['volume'] = get_prices(assets=assets, field='volume', pivot=True)
        bt = BackTester(**backtester_params)
        result = bt.run(strategy, start=start, end=end)
        return result


    def show_results(self):
        if(len(self.results) == 0):
            raise ValueError('You must run an experiment before showing the results.')

        # show dashboard with results
