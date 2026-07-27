import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
from dash import Dash, dcc, html, Input, Output, dash_table
from datetime import datetime
import pandas as pd
from Dashboard.helper_classes import MetricRow, SummaryCard
from Dashboard.themes import THEME_COLORS


class Dashboard:
    def __init__(self, results=None, theme='light'):
        self.results = results
        self.theme = theme
        self.colors = THEME_COLORS[self.theme]


    def show(self):
        fig = self.make_curves()
        app = self.show_dashboard(fig)
        app.run(jupyter_mode='tab')


    def define_template(self):
        alpha_template = go.layout.Template(
            layout=go.Layout(
                font=dict(family="IBM Plex Mono", size=12),
                xaxis=dict(tickfont=dict(family="IBM Plex Mono")),
                yaxis=dict(tickfont=dict(family="IBM Plex Mono"))
            )
        )
        pio.templates["alpha"] = alpha_template
        pio.templates.default = "alpha"


    def make_curves(self):
        if self.results is None:
            raise ValueError("Run the backtest before plotting.")
        
        self.portfolio_value = self.results['Portfolio Value']
        self.drawdown = self.results['Drawdown']
        self.cum_daily_returns = self.results['Cumulative Daily Returns']
        self.daily_returns = self.results['Daily Returns']
        self.rolling_volatility = self.results['Rolling Volatility']
        self.rolling_sharpe = self.results['Rolling Sharpe']
        self.exposure = self.results['Exposure']

        self.define_template()
        
        fig = make_subplots(
            rows=7, 
            cols=1, 
            subplot_titles=("Portfolio Value", "Drawdown", "Cumulative Returns", "Daily Returns", 
                            "Rolling Annualized Volatility", "Rolling Annualized Sharpe", "Exposure"),
            shared_xaxes=True,
            row_heights=[0.25, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125],
            vertical_spacing=0.03
        )

        # Portfolio Value 
        y = self.portfolio_value
        x = y.index
        padding = 0.05 * (y.max() - y.min())
        lower = y.min() - padding
        upper = y.max() + padding

        # Linha invisível que servirá de base para o preenchimento
        fig.add_trace(
            go.Scatter(
                x=x,
                y=[lower] * len(x),
                mode="lines",
                line=dict(width=0),
                hoverinfo="skip",
                showlegend=False,
            ),
            row=1,
            col=1
        )

        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines",
                line=dict(color=self.colors['portfolio_value'], width=1),
                fill="tonexty",
                fillcolor=self.colors['plot_pv_fill'],
                name="Portfolio Value"
            ),
            row=1, col=1
        )
        fig.update_yaxes(title_text="Value", range=[lower, upper], row=1, col=1)

        # Drawdown
        fig.add_trace(
            go.Scatter(
                x=self.drawdown.index.tolist(),
                y=round(100*self.drawdown, 2),
                mode="lines",
                line=dict(color=self.colors['drawdown'], width=1),
                fill="tozeroy",
                fillcolor=self.colors['plot_drawdown_fill'],
                name="Drawdown"
            ),
            row=2, col=1
        )
        fig.update_yaxes(title_text="Drawdown (%)", row=2, col=1)

        # Cummulative Returns
        y = round(100*self.cum_daily_returns, 2)
        x = y.index
        padding = 0.05 * (y.max() - y.min())
        lower = y.min() - padding
        upper = y.max() + padding

        # Linha invisível que servirá de base para o preenchimento
        fig.add_trace(
            go.Scatter(
                x=x,
                y=[lower] * len(x),
                mode="lines",
                line=dict(width=0),
                hoverinfo="skip",
                showlegend=False,
            ),
            row=3,
            col=1
        )

        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines",
                line=dict(color=self.colors['cum_returns'], width=1),
                fill="tonexty",
                fillcolor=self.colors['plot_cum_returns_fill'],
                name="Cumulative Returns"
            ),
            row=3, col=1
        )
        fig.update_yaxes(title_text="Cum Returns (%)", range=[lower, upper], row=3, col=1)

        # Daily Returns
        bar_colors = ["#00FF66" if x >= 0 else "#FF3333"
                        for x in 100*self.daily_returns]
        fig.add_trace(
            go.Bar(
                x=self.daily_returns.index.tolist(),
                y=round(100*self.daily_returns, 2),
                marker_color=bar_colors,
                name="Daily Returns"
            ),
            row=4, col=1
        )
        fig.update_yaxes(title_text="Daily Returns (%)", row=4, col=1)

        # Rolling Volatility
        fig.add_trace(
            go.Scatter(
                x=self.rolling_volatility.index.tolist(),
                y=round(100*self.rolling_volatility, 2),
                mode="lines",
                line_color=self.colors['volatility'],
                name="Rolling Volatility"
            ),
            row=5, col=1
        )
        fig.update_yaxes(title_text="Rolling Vol (%)", row=5, col=1)

        # Rolling Sharpe
        fig.add_trace(
            go.Scatter(
                x=self.rolling_sharpe.index.tolist(),
                y=round(self.rolling_sharpe, 2),
                mode="lines",
                line_color=self.colors['sharpe'],
                name="Rolling Sharpe"
            ),
            row=6, col=1
        )
        fig.update_yaxes(title_text="Rolling Sharpe", row=6, col=1)

        # Exposure
        fig.add_trace(
            go.Scatter(
                x=self.exposure.index.tolist(),
                y=round(self.exposure, 2),
                mode="lines",
                line_color=self.colors['exposure'],
                fill="tozeroy",
                fillcolor=self.colors['plot_exposure_fill'],
                name="Exposure"
            ),
            row=7, col=1
        )
        fig.update_yaxes(title_text="Exposure", row=7, col=1)
        
        fig.update_xaxes(title_text="Date", row=7, col=1)

        fig.update_xaxes(showgrid=True, 
                         gridcolor=self.colors['gridcolor'],
                         gridwidth=1, 
                         zeroline=False, 
                         showline=True, 
                         linecolor=self.colors['linecolor'],
                         tickfont={"color": self.colors["plot_font"]},
                         title_font={"color": self.colors["plot_font"]},
        )
        fig.update_yaxes(showgrid=True, 
                         gridcolor=self.colors['gridcolor'],
                         gridwidth=1, 
                         zeroline=False, 
                         showline=True, 
                         linecolor=self.colors['linecolor'],
                         tickfont={"color": self.colors["plot_font"]},
                         title_font={"color": self.colors["plot_font"]},
        )
        fig.update_layout(
            title="Backtest Results",
            title_x=0.5,
            title_xanchor='center',
            height=1400,
            showlegend=False,
            template="alpha",
            plot_bgcolor=self.colors['plot_bgcolor'],
            paper_bgcolor=self.colors['paper_bgcolor'],
            font={"color": self.colors["plot_font"], "size": 12}
        )

        return fig
    

    def show_dashboard(self, fig):

        self.cash = self.results['Cash']
        self.realized_weights = self.results['Realized Weights']
        self.shares = self.results['Shares']
        self.orders = self.results['Orders']
        self.orders["market price"] = self.orders["market price"].map(lambda x: f"${x:,.4f}")
        self.orders["execution price"] = self.orders["execution price"].map(lambda x: f"${x:,.4f}")
        self.orders["transaction cost"] = self.orders["transaction cost"].map(lambda x: f"${x:,.2f}")
        self.orders["cash after transaction"] = self.orders["cash after transaction"].map(lambda x: f"${x:,.2f}")
        pv = self.portfolio_value.iloc[-1]
        total_return = self.cum_daily_returns.iloc[-1]
        cagr = self.results['Metrics']['CAGR']
        sharpe = self.results['Metrics']['Sharpe']
        max_drawdown = self.results['Metrics']['Max Drawdown']
        volatility = self.results['Metrics']['Volatility']
        trades = self.orders.shape[0]

        app = Dash(__name__)

        stats_html = html.Div([
                html.H3("Summary Statistics", style={"marginLeft": "20px", "marginTop": "15px", "marginBottom": "15px", "color": self.colors['titles']}),
                html.Div([
                        SummaryCard("Portfolio Value", f"${pv:,.2f}", self.theme).render("#16A34A" if total_return >= 0 else "#DC2626"),
                        SummaryCard("Total Return", f"{100*total_return:.2f}%", self.theme).render("#16A34A" if total_return >= 0 else "#DC2626"),
                        SummaryCard("CAGR", f"{100*cagr:.2f}%", self.theme).render("#16A34A" if total_return >= 0 else "#DC2626"),
                        SummaryCard("Sharpe Ratio", f"{sharpe:.2f}", self.theme).render(self.colors['sum_sharpe']),
                        SummaryCard("Max Drawdown", f"{100*max_drawdown:.2f}%", self.theme).render("#DC2626"),
                        SummaryCard("Volatility", f"{100*volatility:.2f}%", self.theme).render(),

                        html.Div([
                                html.Div("Trades",
                                    style={
                                        "fontSize": "13px",
                                        "fontWeight": "600",
                                        "color": self.colors['sum_names'],
                                        "textTransform": "uppercase",
                                        "marginBottom": "10px"
                                    }
                                ),
                                html.Div(f"{trades:,}",
                                    style={
                                        "fontSize": "24px",
                                        "fontWeight": "700",
                                        "color": self.colors['sum_values']
                                    }
                                )
                            ],
                            style={
                                "flex": "1",
                                "padding": "18px",
                                "textAlign": "center"
                            }
                        )
                    ],
                    style={"display": "flex"}
                )
            ],
            style={
                "borderTop": "2px solid " + self.colors['border'],
                "borderRight": "2px solid " + self.colors['border'],
                "borderLeft": "2px solid " + self.colors['border'],
                "backgroundColor": self.colors['sum_backgroundColor'],
                "marginBottom": "0px"
            }
        )

        plots_html = html.Div([dcc.Graph(id="backtest-graph", figure=fig, style={"height": "1400px"})],
                               style={"width": "77%"})
        
        portfolio_performance_html = html.Div(id="info")

        positions_html = html.H5("Positions", style={"fontSize": "18px", "marginBottom": "20px", "marginTop": "15px", "color": self.colors['titles']})
        positions_dash_table = dash_table.DataTable(id="positions-table",
                                                    columns=[
                                                        {"name": "Asset", "id": "Asset"},
                                                        {"name": "Shares", "id": "Shares"},
                                                        {"name": "Weight", "id": "Weight"},
                                                        {"name": "Value", "id": "Value"}
                                                    ],
                                                    data=[],
                                                    style_table={"overflowY": "auto"},
                                                    style_header={
                                                        "backgroundColor": self.colors['header_backgroundColor'],
                                                        "fontWeight": "bold",
                                                        "border": "1px solid " + self.colors['header_border'],
                                                        "color": self.colors['header_font_color']
                                                    },
                                                    style_cell={
                                                        "backgroundColor": self.colors['cell_backgroundColor'],
                                                        "border": "1px solid " + self.colors['cell_border'],
                                                        "padding": "6px",
                                                        "textAlign": "center",
                                                        "fontSize": "13px",
                                                        "color": self.colors['cell_font_color']
                                                    },
                                                    style_data_conditional=[
                                                        {
                                                            "if": {"row_index": "odd"},
                                                            "backgroundColor": self.colors['cell_backgroundColor_odd'],
                                                        },
                                                        {
                                                            "if": {"row_index": "even"},
                                                            "backgroundColor": self.colors['cell_backgroundColor_even'],
                                                        },
                                                    ],
        )

        trades_html = html.H5("Trades", style={"fontSize": "18px", "marginBottom": "20px", "color": self.colors['titles']})
        trades_dash_table = dash_table.DataTable(id="trades-table",
                                                columns=[
                                                    {"name": "Asset", "id": "Asset"},
                                                    {"name": "Shares", "id": "Shares"},
                                                    {"name": "Side", "id": "Side"},
                                                    {"name": "Market Price", "id": "Market Price"},
                                                    {"name": "Execution Price", "id": "Execution Price"},
                                                    {"name": "Transaction Cost", "id": "Transaction Cost"}
                                                ],
                                                data=[],
                                                style_table={"overflowY": "auto"},
                                                style_header={
                                                    "backgroundColor": self.colors['header_backgroundColor'],
                                                    "fontWeight": "bold",
                                                    "border": "1px solid " + self.colors['header_border'],
                                                    "color": self.colors['header_font_color']
                                                },
                                                style_cell={
                                                    "backgroundColor": self.colors['cell_backgroundColor'],
                                                    "border": "1px solid " + self.colors['cell_border'],
                                                    "padding": "6px",
                                                    "textAlign": "center",
                                                    "fontSize": "13px",
                                                    "color": self.colors['cell_font_color']
                                                },
                                                style_data_conditional=[
                                                    {
                                                        "if": {"row_index": "odd"},
                                                        "backgroundColor": self.colors['cell_backgroundColor_odd'],
                                                    },
                                                    {
                                                        "if": {"row_index": "even"},
                                                        "backgroundColor": self.colors['cell_backgroundColor_even'],
                                                    },
                                                ],
        )
        
        pannel_html = html.Div([
                                portfolio_performance_html,
                                html.Br(),
                                positions_html,
                                positions_dash_table,
                                html.Hr(style={"border": "0", "borderTop": "1px solid " + self.colors['pannel_horizontal_border'], "margin": "20px 0"}),
                                trades_html,
                                trades_dash_table
                                ],
                                style={
                                    "width": "23%",
                                    "padding": "20px",
                                    "backgroundColor": self.colors['pannel_backgroundColor'],
                                    "marginTop": "0px",
                                    "borderLeft": "2px solid " + self.colors['border'],
                                }
        )
        
        
        orders_history_html = html.H3("Orders History", style={"marginBottom": "25px", "paddingLeft": "25px", "color": self.colors['titles']})
        orders_history_dash_table = dash_table.DataTable(id="order-history",
                                                        columns=[{"name": c, "id": c} for c in self.orders.columns],
                                                        data=self.orders.to_dict("records"),
                                                        filter_action="native",
                                                        sort_action="native",
                                                        sort_mode="multi",
                                                        page_size=1000,
                                                        export_format="csv",
                                                        style_table={"height": "500px", "overflowY": "auto"},
                                                        style_header={
                                                            "backgroundColor": self.colors['header_backgroundColor'],
                                                            "fontWeight": "bold",
                                                            "border": "1px solid " + self.colors['header_border'],
                                                            "color": self.colors['header_font_color']
                                                        },
                                                        style_cell={
                                                            #"backgroundColor": self.colors['cell_backgroundColor'],
                                                            "border": "1px solid " + self.colors['cell_border'],
                                                            "padding": "6px",
                                                            "textAlign": "center",
                                                            "fontSize": "13px",
                                                            "color": self.colors['cell_font_color']
                                                        },
                                                        style_data_conditional=[
                                                            {
                                                                "if": {"row_index": "odd"},
                                                                "backgroundColor": self.colors['cell_backgroundColor_odd'],
                                                            },
                                                            {
                                                                "if": {"row_index": "even"},
                                                                "backgroundColor": self.colors['cell_backgroundColor_even'],
                                                            },
                                                        ],
        )

        app.layout = html.Div([
            # Summary statistics
            stats_html,
            # Plots + Lateral Pannel
            html.Div([
                      plots_html, 
                      pannel_html
                      ], 
                      style={
                             "display": "flex", 
                             "flexDirection": "row", 
                             "borderTop": "2px solid " + self.colors['border'],
                             "borderLeft": "2px solid " + self.colors['border'],
                             "borderRight": "2px solid " + self.colors['border'],
                            }
            ),
            # Orders History
            html.Div([
                    orders_history_html,
                    orders_history_dash_table
                    ], 
                    style={
                        "marginTop": "0px",
                        "padding": "0px",
                        "border": "2px solid " + self.colors['border'],
                        "backgroundColor": self.colors['orders_backgroundColor'],
                        "borderRadius": "0px"
                    }
            )
        ])

        @app.callback(
            Output("info", "children"),
            Output("positions-table", "data"),
            Output("trades-table", "data"),
            Input("backtest-graph", "clickData")
        )

        def update(clickData):

            if clickData is None:
                return (html.Div("Click on any point.", style={"color": "#64748B"}),
                        [], [])

            date = clickData["points"][0]["x"]
            date = datetime.strptime(date, "%Y-%m-%d").date()

            cash = self.cash.loc[date]
            pv = self.portfolio_value.loc[date]
            exposure = self.exposure.loc[date]
            daily_return = self.daily_returns.loc[date]
            cum_return = self.cum_daily_returns.loc[date]
            drawdown = self.drawdown.loc[date]
            shares = self.shares.loc[date]
            weights = self.realized_weights.loc[date]
            values = pv * weights

            positions = pd.DataFrame({
                "Asset": shares.index,
                "Shares": shares.values,
                "Weight": (100 * weights.values).round(2),
                "Value": values.values
            })

            positions = positions[positions["Shares"] != 0]
            positions = positions.sort_values("Weight", ascending=False)
            positions["Weight"] = positions["Weight"].map(lambda x: f"{x:.2f}%")
            positions["Value"] = positions["Value"].map(lambda x: f"${x:,.2f}")

            orders = self.orders[self.orders['date'] == date].copy()
            orders = orders[["ticker", "shares", "side", "market price", "execution price", "transaction cost"]]
            orders = orders.rename(columns={
                "ticker": "Asset",
                "shares": "Shares",
                "side": "Side",
                "market price": "Market Price",
                "execution price": "Execution Price",
                "transaction cost": "Transaction Cost"
            })

            return (html.Div([
                        html.Div([
                            html.Span("Selected Date", style={"fontSize": "18px", "fontWeight": "600", "color": self.colors['titles']}),
                            html.Span(date.strftime("%d %B %Y"), style={"fontSize": "18px", "color": self.colors['date'], "marginLeft": "10px"})],
                            style={"display": "flex", "alignItems": "baseline", "marginBottom": "20px",
                                    "paddingBottom": "15px", "borderBottom": "1px solid " + self.colors['pannel_horizontal_border']}),
                        html.Div([
                            html.H5("Portfolio", style={"fontSize": "18px", "marginBottom": "15px", "color": self.colors['titles']}),
                            MetricRow("Portfolio Value", f"${pv:,.2f}", self.theme).render(),
                            MetricRow("Cash", f"${cash:,.2f}", self.theme).render(),
                            MetricRow("Exposure", f"{100*exposure:.2f}%", self.theme).render(),
                        ],
                        style={
                            "paddingBottom": "15px",
                            "borderBottom": "1px solid " + self.colors['pannel_horizontal_border']
                        }),
                        html.Div([
                            html.H5("Performance", style={"fontSize": "18px", "marginBottom": "15px", "color": self.colors['titles']}),
                            MetricRow("Daily Return", f"{100*daily_return:.2f}%", self.theme).render(),
                            MetricRow("Drawdown", f"{100*drawdown:.2f}%", self.theme).render(),
                            MetricRow("Cum Return", f"{100*cum_return:.2f}%", self.theme).render(),
                        ],
                        style={
                            "paddingBottom": "15px",
                            "borderBottom": "1px solid " + self.colors['pannel_horizontal_border']
                        }),
                ]), 
                positions.to_dict("records"),
                orders.to_dict("records")
            )

        return app