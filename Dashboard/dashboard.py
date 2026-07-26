import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
from dash import Dash, dcc, html, Input, Output, dash_table
from datetime import datetime
import pandas as pd

class Dashboard:
    def __init__(self, results=None):
        self.results = results


    def show(self):
        #self.show_statistics()
        fig = self.plot_curves()
        app = self.show_dashboard(fig)
        app.run(jupyter_mode='tab')
        

    def show_dashboard(self, fig):

        self.cash = self.results['Cash']
        self.realized_weights = self.results['Realized Weights']
        self.shares = self.results['Shares']
        self.orders = self.results['Orders']
        self.orders["market price"] = self.orders["market price"].map(lambda x: f"${x:,.4f}")
        self.orders["execution price"] = self.orders["execution price"].map(lambda x: f"${x:,.4f}")
        self.orders["transaction cost"] = self.orders["transaction cost"].map(lambda x: f"${x:,.2f}")
        self.orders["cash after transaction"] = self.orders["cash after transaction"].map(lambda x: f"${x:,.2f}")

        app = Dash(__name__)

        app.layout = html.Div([
            ## Plots + Painel Lateral
            html.Div([
            # Área principal
            html.Div([
                dcc.Graph(id="backtest-graph", figure=fig, style={"height": "1400px"})
            ],
            style={"width": "77%", "border": "1px solid #8FAAB8"}
            ),

            # Painel lateral
            html.Div([
                html.Div(id="info"),
                html.Br(),
                html.H5("Positions", style={"fontSize": "18px", "marginBottom": "10px"}),
                dash_table.DataTable(id="positions-table",
                        columns=[
                            {"name": "Asset", "id": "Asset"},
                            {"name": "Shares", "id": "Shares"},
                            {"name": "Weight", "id": "Weight"},
                            {"name": "Value", "id": "Value"}
                        ],
                        data=[],
                        style_table={"overflowY": "auto"},
                        style_header={
                            "backgroundColor": "#DCE8ED",
                            "fontWeight": "bold",
                            "border": "1px solid #B8CAD4"
                        },
                        style_cell={
                            "backgroundColor": "#F8F9FA",
                            "border": "1px solid #D6E4EA",
                            "padding": "6px",
                            "textAlign": "center",
                            "fontSize": "13px"
                        }
                    ),
                html.Br(),
                html.H5("Trades", style={"fontSize": "18px", "marginBottom": "10px"}),
                dash_table.DataTable(id="trades-table",
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
                            "backgroundColor": "#DCE8ED",
                            "fontWeight": "bold",
                            "border": "1px solid #B8CAD4"
                        },
                        style_cell={
                            "backgroundColor": "#F8F9FA",
                            "border": "1px solid #D6E4EA",
                            "padding": "6px",
                            "textAlign": "center",
                            "fontSize": "13px"
                        }
                    )
                ],
                style={
                    "width": "23%",
                    "padding": "20px",
                    "backgroundColor": "#F8F9FA",
                    "marginTop": "0px",
                    "border": "2px solid #8FAAB8",
                })
            ], style={"display": "flex", "flexDirection": "row", "gap": "0px", "border": "1px solid #8FAAB8",
                      "MarginBottom": "0px"}
            ),
            html.Br(),
            # Orders History
            html.Div([
                html.H3("Orders History", style={"marginBottom": "25px"}),
                dash_table.DataTable(id="order-history",
                    columns=[{"name": c, "id": c} for c in self.orders.columns],
                    data=self.orders.to_dict("records"),
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    page_size=1000,
                    export_format="csv",

                    style_table={"height": "500px", "overflowY": "auto"},
                    style_header={
                        "backgroundColor": "#DCE8ED",
                        "fontWeight": "bold",
                        "border": "1px solid #B8CAD4"
                    },
                    style_cell={
                        "backgroundColor": "#F8F9FA",
                        "border": "1px solid #D6E4EA",
                        "padding": "6px",
                        "textAlign": "center",
                        "fontSize": "13px"
                    })
            ], 
            style={
                "marginTop": "0px",
                "padding": "0px",
                "border": "2px solid #8FAAB8",
                "backgroundColor": "#F8F9FA",
                "borderRadius": "0px"
            })
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
                html.Div([html.Span("Selected Date", style={"fontSize": "18px", "fontWeight": "600"}),
                          html.Span(date.strftime("%d %B %Y"), style={"fontSize": "18px", "color": "#4F5B6D", "marginLeft": "10px"})],
                        style={"display": "flex", "alignItems": "baseline", "marginBottom": "20px",
                               "paddingBottom": "15px", "borderBottom": "1px solid #8FAAB8"}),
                 html.Div([
                    html.H5("Portfolio", style={"fontSize": "18px"}),
                    self.metric_row("Portfolio Value", f"${pv:,.2f}"),
                    self.metric_row("Cash", f"${cash:,.2f}"),
                    self.metric_row("Exposure", f"{100*exposure:.2f}%"),
                ],
                style={
                    "paddingBottom": "15px",
                    "borderBottom": "1px solid #8FAAB8"
                }),
                html.Div([
                html.H5("Performance", style={"fontSize": "18px"}),
                self.metric_row("Daily Return", f"{100*daily_return:.2f}%"),
                self.metric_row("Drawdown", f"{100*drawdown:.2f}%"),
            ],
            style={
                "paddingBottom": "15px",
                "borderBottom": "1px solid #8FAAB8"
            }),
            ]), 
            positions.to_dict("records"),
            orders.to_dict("records")
            )

        return app
    

    def metric_row(self, name, value):
        return html.Div([
            html.Div(name, style={"color": "#64748B", "fontSize": "14px"}),
            html.Div(value, style={"fontWeight": "600", "fontSize": "16px"})
        ],
        style={
            "display": "flex",
            "justifyContent": "space-between",
            "padding": "8px 0",
            "borderBottom": "1px solid #E2E8F0"
        })


    def plot_curves(self):
        if self.results is None:
            raise ValueError("Run the backtest before plotting.")
        
        self.portfolio_value = self.results['Portfolio Value']
        self.drawdown = self.results['Drawdown']
        self.cum_daily_returns = self.results['Cumulative Daily Returns']
        self.daily_returns = self.results['Daily Returns']
        self.rolling_volatility = self.results['Rolling Volatility']
        self.rolling_sharpe = self.results['Rolling Sharpe']
        self.exposure = self.results['Exposure']

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
        fig.add_trace(
            go.Scatter(
                x=self.portfolio_value.index.tolist(),
                y=self.portfolio_value,
                mode="lines",
                name="Portfolio Value"
            ),
            row=1, col=1
        )
        fig.update_yaxes(title_text="Value", row=1, col=1)

        # Drawdown
        fig.add_trace(
            go.Scatter(
                x=self.drawdown.index.tolist(),
                y=round(100*self.drawdown, 2),
                mode="lines",
                name="Drawdown"
            ),
            row=2, col=1
        )
        fig.update_yaxes(title_text="Drawdown (%)", row=2, col=1)

        # Cummulative Returns
        fig.add_trace(
            go.Scatter(
                x=self.cum_daily_returns.index.tolist(),
                y=round(100*self.cum_daily_returns, 2),
                mode="lines",
                name="Cumulative Returns"
            ),
            row=3, col=1
        )
        fig.update_yaxes(title_text="Cum Returns (%)", row=3, col=1)

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
                name="Exposure"
            ),
            row=7, col=1
        )
        fig.update_yaxes(title_text="Exposure", row=7, col=1)
        
        fig.update_xaxes(title_text="Date", row=7, col=1)

        # clean
        plot_bgcolor="#BDC6C9"
        paper_bgcolor="#F8F9FA"
        gridcolor="#F9FBFC"
        linecolor="#8FA6AD"

        # like Bloomberg
        """plot_bgcolor = "#0B0E11"
        paper_bgcolor = "#050607"
        gridcolor = "#252A30"
        linecolor = "#59636E"

        # less agressive
        plot_bgcolor = "#121820"
        paper_bgcolor = "#0A0F14"
        gridcolor = "#2B3540"
        linecolor = "#667585"""

        fig.update_xaxes(showgrid=True, 
                         gridcolor=gridcolor,
                         gridwidth=1, 
                         zeroline=False, 
                         showline=True, 
                         linecolor=linecolor
        )
        fig.update_yaxes(showgrid=True, 
                         gridcolor=gridcolor,
                         gridwidth=1, 
                         zeroline=False, 
                         showline=True, 
                         linecolor=linecolor
        )
        fig.update_layout(
            title="Backtest Results",
            title_x=0.5,
            title_xanchor='center',
            height=1400,
            showlegend=False,
            template="none",
            plot_bgcolor=plot_bgcolor,
            paper_bgcolor=paper_bgcolor
        )

        return fig