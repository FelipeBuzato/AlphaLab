from BackTester.experiment_runner import ExperimentRunner


class Experiment:
    def __init__(self, name, strategy, strategy_params, 
                 start, end, initial_capital=None, risk_free=None, rebalance=None, execution_method=None, transaction_cost_rate=None, slippage_rate=None,
                 benchmark_name=None, benchmark_strategy=None, benchmark_params=None,):

        self.name = name
        self.strategy = strategy
        self.strategy_params = strategy_params
        self.start = start
        self.end = end
        self.initial_capital = initial_capital
        self.risk_free = risk_free
        self.rebalance = rebalance
        self.execution_method = execution_method
        self.transaction_cost_rate = transaction_cost_rate
        self.slippage_rate = slippage_rate
        self.benchmark_name = benchmark_name
        self.benchmark_strategy = benchmark_strategy
        self.benchmark_params = benchmark_params

        self._validate_inputs()


    def _validate_inputs(self):
        if(not all(x in self.strategy_params for x in ('assets', 'field'))):
            raise ValueError("You must specify the assets and field in strategy_params.")

        # if one benchmark variable is not None, all must be not None
        benchmark_variables = (self.benchmark_name, self.benchmark_strategy, self.benchmark_params)
        n_none = sum(v is None for v in benchmark_variables)
        if n_none not in (0, len(benchmark_variables)):
            raise ValueError("benchmark, benchmark_params and benchmark_name must be all None or all not None.")

        if(self.benchmark_params is not None and not all(x in self.benchmark_params for x in ('assets', 'field'))):
            raise ValueError("You must specify the assets and field in benchmark_params.")


    def backtester_params(self):
        params = {'initial_capital': self.initial_capital, 'rebalance': self.rebalance, 'execution_method': self.execution_method,
                  'transaction_cost_rate': self.transaction_cost_rate, 'slippage_rate': self.slippage_rate}

        return {k: v for k, v in params.items() if v is not None}


    def benchmark_info(self):
        return {'name': self.benchmark_name, 'strategy': self.benchmark_strategy, 'params': self.benchmark_params}


    def strategy_info(self):
        return {'name': self.name, 'strategy': self.strategy, 'params': self.strategy_params}


    def run(self):
        return ExperimentRunner([self]).run()[0]

    
        