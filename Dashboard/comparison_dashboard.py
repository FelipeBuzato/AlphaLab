from dash import html, Input, Output, State, dash_table, dcc
from dash.dash_table.Format import Format, Scheme, Symbol, Group
import plotly.io as pio
from plotly.subplots import make_subplots
import plotly.express as px
import plotly.graph_objects as go
from Dashboard.themes import THEME_COLORS
import pandas as pd


class ComparisonDashboard:
    def __init__(self, theme='light'):
        self.theme = theme
        self.colors = THEME_COLORS[self.theme]
        self.results = None


    def _define_template(self):
        alpha_template = go.layout.Template(
            layout=go.Layout(
                font=dict(family="IBM Plex Mono", size=12),
                xaxis=dict(tickfont=dict(family="IBM Plex Mono")),
                yaxis=dict(tickfont=dict(family="IBM Plex Mono"))
            )
        )
        pio.templates["alpha"] = alpha_template
        pio.templates.default = "alpha"


    def build_layout(self):
        if self.results is None:
            raise ValueError("No backtest results available.")

        self._define_template()

        metrics_table = self._build_metrics_table()
        metrics_table_html = html.Div(
            metrics_table,
            style={
                "marginTop": "0px",
                "padding": "0px",
                "borderLeft": "2px solid " + self.colors['border'],
                "borderRight": "2px solid " + self.colors['border'],
                "borderBottom": "2px solid " + self.colors['border'],
                "backgroundColor": self.colors['orders_backgroundColor'],
                "borderRadius": "0px",
            }
        )

        metrics_interactive_html = self._build_metrics_interactive()
        metrics_interactive_html = html.Div(
            metrics_interactive_html,
            style={
                "padding": "20px",
                "borderLeft": "2px solid " + self.colors["border"],
                "borderRight": "2px solid " + self.colors["border"],
                "borderBottom": "2px solid " + self.colors["border"],
                "backgroundColor": self.colors["orders_backgroundColor"],
            }
        )

        layout = html.Div([
                html.Div(
                    "Backtests Comparison",
                    style={
                        "backgroundColor": self.colors['ct_backgroundColor'],
                        "color": self.colors['titles'],
                        "borderLeft": "2px solid " + self.colors["border"],
                        "borderRight": "2px solid " + self.colors["border"],
                        "borderTop": "2px solid " + self.colors["border"],
                        "padding": "10px",
                        "fontWeight": "600",
                        "fontSize": "18px",
                    }
                ),
                metrics_table_html,
                html.Div(
                    "Metrics Visualization",
                    style={
                        "backgroundColor": self.colors['ct_backgroundColor'],
                        "color": self.colors['titles'],
                        "borderLeft": "2px solid " + self.colors["border"],
                        "borderRight": "2px solid " + self.colors["border"],
                        "padding": "10px",
                        "fontWeight": "600",
                        "fontSize": "18px",
                    }
                ),
                metrics_interactive_html,
        ])

        return layout


    def _build_metrics_table(self):
        rows = []
        tooltip_data = []

        for i, result in enumerate(self.results):
            strategy_id = f"S{i}"

            params = result['Strategy Params']
            params_str = " | ".join(f"{k}: {v}" for k, v in params.items())

            params_tooltip = "| Parameter | Value |\n"
            params_tooltip += "|-----------|------:|\n"
            for key, value in params.items():
                params_tooltip += f"| {key} | {value} |\n"

            bench_params = result['Benchmark']['Strategy Params']
            if(bench_params is not None):
                bench_params_tooltip = "| Parameter | Value |\n"
                bench_params_tooltip += "|-----------|------:|\n"
                for key, value in bench_params.items():
                    bench_params_tooltip += f"| {key} | {value} |\n"

            new_row = {
                "id": strategy_id,  # usado internamente pelo callback
                "Name": result['Strategy Name'],
                "Params": params_str if len(params_str) < 30 else params_str[:30] + "...",
                "Start": result['Start Date'],
                "End": result['End Date'],
                "Initial Capital": result['Initial Capital'],
                "Final Portfolio Value": float(result['Portfolio Value'].iloc[-1]),
                "Cum. Return": result['Metrics']['Cumulative Return'],
                "CAGR": result['Metrics']["CAGR"],
                "Sharpe": result['Metrics']["Sharpe"],
                "Max DD": result['Metrics']["Max Drawdown"],
                "Volatility": result['Metrics']["Volatility"],
                "Risk-free Rate": result['Risk-free']['name'],
                "Benchmark": result['Benchmark']['Strategy Name'],
                "Excess Return": result['Metrics']['Benchmark']['Excess Return'],
                "Correlation": result['Metrics']['Benchmark']['Correlation'],
                "Beta": result['Metrics']['Benchmark']['Beta'],
                "Alpha": result['Metrics']['Benchmark']['Alpha']
            }
            rows.append(new_row)
            tooltip = {
                "Params": {
                    "value": params_tooltip,
                    "type": "markdown"
                }
            }
            if(bench_params is not None):
                tooltip["Benchmark"] = {
                    "value": bench_params_tooltip,
                    "type": "markdown"
                }
            tooltip_data.append(tooltip)

        self.table_df = pd.DataFrame(rows)

        percent = Format(precision=2, scheme=Scheme.percentage)
        money = Format(precision=2, scheme=Scheme.fixed, group=Group.yes, groups=3, symbol=Symbol.yes, symbol_prefix="$")
        decimal = Format(precision=2)
        tricimal = Format(precision=3)

        columns = [
            {"name": "id", "id": "id"},
            {"name": "Name", "id": "Name", "type": "text"},
            {"name": "Params", "id": "Params", "type": "text"},
            {"name": "Start", "id": "Start", "type": "text"},
            {"name": "End", "id": "End", "type": "text"},
            {"name": "Initial Capital", "id": "Initial Capital", "type": "numeric", "format": money},
            {"name": "Final Portfolio Value", "id": "Final Portfolio Value", "type": "numeric", "format": money},
            {"name": "Cum. Return", "id": "Cum. Return", "type": "numeric", "format": percent},
            {"name": "CAGR", "id": "CAGR", "type": "numeric", "format": percent},
            {"name": "Sharpe", "id": "Sharpe", "type": "numeric", "format": decimal},
            {"name": "Max DD", "id": "Max DD", "type": "numeric", "format": percent},
            {"name": "Volatility", "id": "Volatility", "type": "numeric", "format": percent},
            {"name": "Risk-free Rate", "id": "Risk-free Rate", "type": "text"},
            {"name": "Benchmark", "id": "Benchmark", "type": "text"},
            {"name": "Excess Return", "id": "Excess Return", "type": "numeric", "format": percent},
            {"name": "Correlation", "id": "Correlation", "type": "numeric", "format": percent},
            {"name": "Beta", "id": "Beta", "type": "numeric", "format": tricimal},
            {"name": "Alpha", "id": "Alpha", "type": "numeric", "format": tricimal},
        ]

        table = dash_table.DataTable(
            id="backtests-comparison",
            hidden_columns=[],
            columns=columns,
            data=rows,
            tooltip_data=tooltip_data,
            tooltip_duration=None,
            css=[{
                    "selector": ".dash-table-tooltip",
                    "rule": f"""
                        background-color: {self.colors['cell_backgroundColor_even']};
                        color: {self.colors['header_font_color']};
                        border: 1px solid {self.colors['cell_border']};
                        font-family: 'IBM Plex Mono';
                        font-size: 12px;
                        padding: 10px;
                    """
            }],
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            page_size=20,
            export_format="csv",
            row_selectable="single",
            style_table={
                "maxHeight": "600px",
                "overflowY": "auto"
            },
            style_header={
                "backgroundColor": self.colors['header_backgroundColor'],
                "fontWeight": "bold",
                "border":"1px solid " + self.colors['header_border'],
                "color": self.colors['header_font_color']
            },
            style_cell={
                "border": "1px solid " + self.colors['cell_border'],
                "padding": "12px",
                "textAlign": "center",
                "fontSize": "13px",
                "color": self.colors['cell_font_color']
            },
            style_data_conditional=[
                {
                    "if": {"row_index": "odd"},
                    "backgroundColor": self.colors['cell_backgroundColor_odd']
                },
                {
                    "if": {"row_index": "even"},
                    "backgroundColor": self.colors['cell_backgroundColor_even']
                },
                # Sharpe > 1
                {
                    "if": {
                        "filter_query": "{Sharpe} >= 1",
                        "column_id": "Sharpe"
                    },
                    "color": "#16A34A",
                    "fontWeight": "bold",
                },
                # Sharpe < 0
                {
                    "if": {
                        "filter_query": "{Sharpe} < 0",
                        "column_id": "Sharpe"
                    },
                    "color": "#B11C11",
                    "fontWeight": "bold",
                },
                # Max Drawdown melhor que -20%
                {
                    "if": {
                        "filter_query": "{Max DD} > -0.20",
                        "column_id": "Max DD"
                    },
                    "color": "#16A34A",
                },
                # CAGR > 15%
                {
                    "if": {
                        "filter_query": "{CAGR} > 0.15",
                        "column_id": "CAGR"
                    },
                    "color": "#16A34A",
                },
                # CAGR > 15%
                {
                    "if": {
                        "filter_query": "{CAGR} < 0.0",
                        "column_id": "CAGR"
                    },
                    "color": "#A31616",
                },
                # Alpha > 10%
                {
                    "if": {
                        "filter_query": "{Alpha} > 0.10",
                        "column_id": "Alpha"
                    },
                    "color": "#16A34A",
                },
                # Cum. Return < 0
                {
                    "if": {
                        "filter_query": "{Cum. Return} < 0",
                        "column_id": "Cum. Return"
                    },
                    "color": "#B11C11",
                    "fontWeight": "bold",
                },
                # Excess Return < 0
                {
                    "if": {
                        "filter_query": "{Excess Return} < 0",
                        "column_id": "Excess Return"
                    },
                    "color": "#B11C11",
                    "fontWeight": "bold",
                },
                # Excess Return > 0
                {
                    "if": {
                        "filter_query": "{Excess Return} > 0",
                        "column_id": "Excess Return"
                    },
                    "color": "#16A34A",
                    "fontWeight": "bold",
                },
                {
                    "if": {"column_id": "Name"},
                    "fontWeight": "600"
                }
            ],
        )

        return table


    def _build_metrics_interactive(self):

        metrics = [
            "Cum. Return",
            "CAGR",
            "Sharpe",
            "Max DD",
            "Volatility",
            "Excess Return",
            "Correlation",
            "Beta",
            "Alpha",
        ]

        return html.Div([
                html.Div([
                        html.Div([
                            html.Label("X Axis", style={
                                                            "color": self.colors["plot_font"],
                                                            "fontSize": "13px",
                                                            "fontWeight": "600",
                                                        }),
                            dcc.Dropdown(
                                id="metrics-x",
                                options=[{"label": m, "value": m} for m in metrics],
                                value="Sharpe",
                                clearable=False,
                            ),
                        ], style={"width": "48%"}),

                        html.Div([
                                html.Label("Y Axis", style={
                                                            "color": self.colors["plot_font"],
                                                            "fontSize": "13px",
                                                            "fontWeight": "600",
                                                        }),
                                dcc.Dropdown(
                                    id="metrics-y",
                                    options=[
                                        {"label": m, "value": m}
                                        for m in metrics
                                    ],
                                    value="Cum. Return",
                                    clearable=False,
                                ),
                            ],
                            style={"width": "48%"},
                        ),
                    ],
                    style={
                        "display": "flex",
                        "justifyContent": "space-between",
                        "marginBottom": "20px",
                        "marginLeft": "auto",
                        "marginRight": "auto",
                        "width": "50%"
                    },
                ),
                dcc.Graph(
                    id="metrics-scatter",
                    config={"displaylogo": False, "responsive": True},
                    style={"height": "350px", "width": "100%"},
                ),
            ],
            style={
                "width": "50%",          
                "maxWidth": "1100px",    
                "margin": "0 auto", 
            }
    )
    

    def register_callbacks(self, app):
        @app.callback(
            Output("current-page", "data", allow_duplicate=True),
            Output("selected-strategy", "data", allow_duplicate=True),
            Input("backtests-comparison", "selected_rows"),
            State("backtests-comparison", "data"),
            prevent_initial_call=True
        )
        def open_strategy(selected_rows, data):
            if not selected_rows or data is None:
                return "comparison", None
            
            row = selected_rows[0]
            strategy_id = data[row]["id"]
            return "dashboard", strategy_id

        @app.callback(
            Output("metrics-scatter", "figure"),
            Input("metrics-x", "value"),
            Input("metrics-y", "value"),
        )
        def update_metrics_scatter(x_metric, y_metric):
            table_df = self.table_df.copy()

            percentage_metrics = {
                "Cum. Return",
                "CAGR",
                "Max DD",
                "Volatility",
                "Excess Return",
                "Correlation",
            }

            for metric in percentage_metrics:
                if metric in table_df.columns:
                    table_df[metric] = (100 * table_df[metric]).round(2)

            custom_hover_data = ["id", "Name", "Cum. Return", "CAGR", "Sharpe", "Max DD", "Volatility", "Beta", "Alpha"]

            fig = px.scatter(
                table_df,
                x=x_metric,
                y=y_metric,
                custom_data=custom_hover_data
            )

            fig.update_traces(textposition="top center", marker=dict(size=13),
                              hovertemplate=
                                            "<b>%{customdata[0]}</b><br><br>" +
                                            "<b>%{customdata[1]}</b><br><br>" +
                                            "Cum. Return: %{customdata[2]:.2f}%<br>" +
                                            "CAGR: %{customdata[3]:.2f}%<br>" +
                                            "Sharpe: %{customdata[4]:.2f}<br>" +
                                            "Max DD: %{customdata[5]:.2f}%<br>" +
                                            "Volatility: %{customdata[6]:.2f}%<br>" +
                                            "Beta: %{customdata[7]:.2f}<br>" +
                                            "Alpha: %{customdata[8]:.2f}<br>" +
                                            "<extra></extra>"
            )

            fig.update_xaxes(
                title_text=x_metric + " (%)" if x_metric in percentage_metrics else x_metric,
                showgrid=True,
                gridcolor=self.colors["gridcolor"],
                gridwidth=1.5,
                zeroline=False,
                showline=True,
                linecolor=self.colors["linecolor"],
                tickfont={
                    "size": 11,
                    "color": self.colors["plot_font"],
                },
                title_font={
                    "color": self.colors["plot_font"],
                    "size": 13,
                },
            )

            fig.update_yaxes(
                title_text=y_metric + " (%)" if y_metric in percentage_metrics else y_metric,
                showgrid=True,
                gridcolor=self.colors["gridcolor"],
                gridwidth=1.5,
                zeroline=False,
                showline=True,
                linecolor=self.colors["linecolor"],
                tickfont={
                    "size": 11,
                    "color": self.colors["plot_font"],
                },
                title_font={
                    "color": self.colors["plot_font"],
                    "size": 13,
                },
                title_standoff=100
            )

            fig.update_layout(
                template="alpha",
                plot_bgcolor=self.colors['plot_bgcolor'],
                paper_bgcolor=self.colors['paper_bgcolor'],
                font={
                    "color": self.colors["plot_font"],
                    "size": 12,
                },
                hoverlabel=dict(
                    bgcolor=self.colors["hover_background"],
                    font=dict(
                        color=self.colors["hover_font"],
                        family="IBM Plex Mono",
                        size=12
                    ),
                    bordercolor=self.colors["hover_font"]
                ),
                margin=dict(l=40, r=30, t=30, b=40)
            )

            return fig