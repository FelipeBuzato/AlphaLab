from dash import Dash, html, dcc, Input, Output
from Dashboard.dashboard import Dashboard
from Dashboard.comparison_dashboard import ComparisonDashboard


class AlphalabApp:

    def __init__(self, theme="light"):
        self.theme = theme
        self.app = Dash(__name__, suppress_callback_exceptions=True)
        self.results = {}
        self.is_comparison_mode = False

        self.dashboard = Dashboard(theme)
        self.comparison_dashboard = ComparisonDashboard(theme)


    def register_callbacks(self):

        @self.app.callback(
            Output("page-content", "children"),
            Input("current-page", "data"),
            Input("selected-strategy", "data")
        )
        def render_page(page, strategy_id):
            if page == "comparison":
                return self.comparison_dashboard.build_layout()

            if page == "dashboard" and strategy_id in self.results:
                # Atualiza a referência de resultados da estratégia selecionada
                self.dashboard.results = self.results[strategy_id]
                return self.dashboard.build_layout(show_back_button=self.is_comparison_mode)

            return html.Div("Nenhum backtest selecionado.")


    def show(self, results):
        if isinstance(results, list):
            self.is_comparison_mode = True
            self.comparison_dashboard.results = results
            self.results = {}
            for i, result in enumerate(results):
                strategy_id = f"S{i}"
                self.results[strategy_id] = result

            page = "comparison"
            selected = None
        else:
            self.is_comparison_mode = False
            strategy_id = results["Strategy Name"]
            self.results = {strategy_id: results}
            self.dashboard.results = results
            
            page = "dashboard"
            selected = strategy_id

        self.app.layout = html.Div([
            dcc.Store(id="current-page", data=page),
            dcc.Store(id="selected-strategy", data=selected),
            html.Div(id="page-content")
        ])

        # Registrar todos os callbacks da aplicação
        self.dashboard.register_callbacks(self.app)
        self.comparison_dashboard.register_callbacks(self.app)
        self.register_callbacks()

        self.app.run(jupyter_mode="tab")