import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
from dash import Dash, dcc, html, Input, Output, dash_table, ALL, State, callback, ctx
from datetime import datetime
import pandas as pd
from Dashboard.helper_classes import MetricRow, SummaryCard, CollapsibleSection, DetailBlock
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
        self.risk_free_pv = self.results['Risk-free']['portfolio_value']
        self.benchmark_pv = self.results['Benchmark']['Portfolio Value']

        self.define_template()
        
        fig = make_subplots(
            rows=8, 
            cols=1, 
            subplot_titles=("Portfolio Value", "", "Drawdown", "Cumulative Returns", "Daily Returns", 
                            "Rolling Annualized Volatility", "Rolling Annualized Sharpe", "Exposure"),
            shared_xaxes=True,
            row_heights=[0.279, 0.001, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12],
            vertical_spacing=0.035
        )

        # Portfolio Value 
        y = self.portfolio_value
        x = y.index
        min_val = min(pd.concat([y, self.benchmark_pv]))
        max_val = max(pd.concat([y, self.benchmark_pv]))
        padding = 0.05 * (max_val - min_val)
        lower = min_val - padding
        upper = max_val + padding

        # risk-free portfolio
        fig.add_trace(
            go.Scatter(
                x=x,
                y=self.risk_free_pv,
                mode="lines",
                line=dict(color=self.colors['risk_free'], width=1, dash="dot"),
                name="Risk-free Portfolio",
                showlegend=True,
                visible="legendonly"
            ),
            row=1, col=1
        )

        # Benchmark portfolio
        fig.add_trace(
            go.Scatter(
                x=x,
                y=self.benchmark_pv,
                mode="lines",
                line=dict(color=self.colors['benchmark'], width=1),
                name="Benchmark",
                showlegend=True,
                #visible="legendonly"
            ),
            row=1, col=1
        )

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
                name="Portfolio Value",
                showlegend=True
            ),
            row=1, col=1
        )

        fig.update_yaxes(title_text="Value", range=[lower, upper], row=1, col=1)

        # Drawdown
        fig.add_trace(
            go.Scatter(
                x=x,
                y=round(100*self.drawdown, 2),
                mode="lines",
                line=dict(color=self.colors['drawdown'], width=1),
                fill="tozeroy",
                fillcolor=self.colors['plot_drawdown_fill'],
                name="Drawdown",
                showlegend=False,
            ),
            row=3, col=1
        )
        fig.update_yaxes(title_text="Drawdown (%)", row=3, col=1)

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
            row=4,
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
                name="Cumulative Returns",
                showlegend=False
            ),
            row=4, col=1
        )
        fig.update_yaxes(title_text="Cum Returns (%)", range=[lower, upper], row=4, col=1)

        # Daily Returns
        bar_colors = ["#00FF66" if x >= 0 else "#FF3333"
                        for x in 100*self.daily_returns]
        fig.add_trace(
            go.Bar(
                x=x,
                y=round(100*self.daily_returns, 2),
                marker_color=bar_colors,
                name="Daily Returns",
                showlegend=False
            ),
            row=5, col=1
        )
        fig.update_yaxes(title_text="Daily Returns (%)", row=5, col=1)

        # Rolling Volatility
        fig.add_trace(
            go.Scatter(
                x=x,
                y=round(100*self.rolling_volatility, 2),
                mode="lines",
                line_color=self.colors['volatility'],
                name="Rolling Volatility",
                showlegend=False
            ),
            row=6, col=1
        )
        fig.update_yaxes(title_text="Rolling Vol (%)", row=6, col=1)

        # Rolling Sharpe
        fig.add_trace(
            go.Scatter(
                x=x,
                y=round(self.rolling_sharpe, 2),
                mode="lines",
                line_color=self.colors['sharpe'],
                name="Rolling Sharpe",
                showlegend=False
            ),
            row=7, col=1
        )
        fig.update_yaxes(title_text="Rolling Sharpe", row=7, col=1)

        # Exposure
        fig.add_trace(
            go.Scatter(
                x=x,
                y=round(self.exposure, 2),
                mode="lines",
                line_color=self.colors['exposure'],
                fill="tozeroy",
                fillcolor=self.colors['plot_exposure_fill'],
                name="Exposure",
                showlegend=False
            ),
            row=8, col=1
        )
        fig.update_yaxes(title_text="Exposure", row=8, col=1)
        
        fig.update_xaxes(title_text="", row=8, col=1)

        #fig.update_traces(xaxis="x")

        fig.update_xaxes(showgrid=True, 
                         gridcolor=self.colors['gridcolor'],
                         gridwidth=1, 
                         zeroline=False, 
                         showline=True, 
                         showticklabels=True,
                         linecolor=self.colors['linecolor'],
                         tickfont={"size": 10, "color": self.colors["plot_dates_font"]},
                         title_font={"color": self.colors["plot_font"]},
                         showspikes=True,
                         spikemode="across+toaxis",
                         spikesnap="cursor",
                         spikecolor=self.colors['spike'],
                         spikethickness=0.5,
                         spikedash="dot"
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
            title=None,
            margin=dict(t=30),
            height=1800,
            #showlegend=False,
            hovermode="x unified",
            #hoversubplots="axis",
            hoverdistance=-1,
            template="alpha",
            plot_bgcolor=self.colors['plot_bgcolor'],
            paper_bgcolor=self.colors['paper_bgcolor'],
            font={"color": self.colors["plot_font"], "size": 12},
            legend=dict(orientation="h", y=0.77, x=0, xanchor="left", yanchor="middle", font=dict(size=11)),
            uirevision="constant" 
        )

        return fig
    

    def show_dashboard(self, fig):

        strategy_name = self.results['Strategy Name']
        start_date = self.results['Start Date']
        end_date = self.results['End Date']
        initial_capital = self.results['Initial Capital']
        rebalancing_frequency = self.results['Rebalancing Frequency']
        pv = self.portfolio_value.iloc[-1]
        max_pv = self.results['Metrics']['Max']
        min_pv = self.results['Metrics']['Min']
        total_return = self.cum_daily_returns.iloc[-1]
        cagr = self.results['Metrics']['CAGR']
        sharpe = self.results['Metrics']['Sharpe']
        max_drawdown = self.results['Metrics']['Max Drawdown']
        volatility = self.results['Metrics']['Volatility']
        self.cash = self.results['Cash']
        self.realized_weights = self.results['Realized Weights']
        self.shares = self.results['Shares']
        self.orders = self.results['Orders']
        self.orders["market price"] = self.orders["market price"].map(lambda x: f"${x:,.4f}")
        self.orders["execution price"] = self.orders["execution price"].map(lambda x: f"${x:,.4f}")
        self.orders["transaction cost"] = self.orders["transaction cost"].map(lambda x: f"${x:,.2f}")
        self.orders["cash after transaction"] = self.orders["cash after transaction"].map(lambda x: f"${x:,.2f}")
        trades = self.orders.shape[0]
        risk_free_name = self.results['Risk-free']['name']
        risk_free_cum_return = round(100*self.results['Risk-free']['cum_return'], 2)
        benchmark_name = self.results['Benchmark']['Strategy Name']
        benchmark_total_return = self.results['Benchmark']['Metrics']['Cumulative Return']
        excess_return_over_benchmark = self.results['Metrics']['Benchmark']['Excess Return']
        benchmark_correlation = self.results['Metrics']['Benchmark']['Correlation']
        alpha = self.results['Metrics']['Benchmark']['Alpha']
        beta = self.results['Metrics']['Benchmark']['Beta']

        app = Dash(__name__)

        stats_html = html.Div([
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
                "borderRight": "2px solid " + self.colors['border'],
                "borderLeft": "2px solid " + self.colors['border'],
                "backgroundColor": self.colors['sum_backgroundColor'],
                "marginBottom": "0px"
            }
        )

        backtest_details = [
                    {
                        "title": "General",
                        "metrics": [
                            ("Start Date", start_date),
                            ("End Date", end_date),
                            ("Strategy", strategy_name),
                            ("Initial Capital", f"${initial_capital:,.2f}"),
                            ("Rebalancing Frequency", rebalancing_frequency),
                        ]
                    },
                    {
                        "title": "Performance",
                        "metrics": [
                            ("Final Portfolio Value", f"${pv:,.2f}"),
                            ("Total Return", f"{100*total_return:.2f}%"),
                            ("CAGR", f"{100*cagr:.2f}%"),
                            ("Sharpe", f"{sharpe:.2f}"),
                            ("Risk-free Rate", risk_free_name),
                            ("Risk-free Total Return", f"{risk_free_cum_return}%")
                        ]
                    },
                    {
                        "title": "Benchmark Comparison",
                        "metrics": [
                            ("Benchmark", benchmark_name),
                            ("Benchmark Total Return", 
                             f"{100*benchmark_total_return:.2f}%" if benchmark_total_return is not None else None),
                            ("Excess Return Over Benchmark", 
                             f"{100*excess_return_over_benchmark:.2f}%" if excess_return_over_benchmark is not None else None),
                            ("Correlation", f"{100*benchmark_correlation:.2f}%" if benchmark_correlation is not None else None),
                            ("Beta", f"{beta:.3f}" if beta is not None else None),
                            ("Alpha", f"{alpha:.3f}" if alpha is not None else None)
                        ]
                    },
                    {
                        "title": "Risk",
                        "metrics": [
                            ("Volatility", f"{100*volatility:.2f}%"),
                            ("Max Drawdown", f"{100*max_drawdown:.2f}%"),
                            ("Max. Portfolio Value", f"${max_pv:,.2f}"),
                            ("Min. Portfolio Value", f"${min_pv:,.2f}"),
                            ("Var", None),
                        ]
                    },

        ]
        
        backtest_details_html = self.make_backtest_details_html(backtest_details)

        plots_html = html.Div([dcc.Graph(id="backtest-graph", figure=fig, style={"height": "1800px"})],
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
                                    "borderLeft": "1px solid " + self.colors['pannel_horizontal_border'],
                                }
        )
        
        
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

        backtest_charts_section_html = html.Div([
                                            plots_html, 
                                            pannel_html
                                            ], 
                                            style={
                                                    "display": "flex", 
                                                    "flexDirection": "row", 
                                                    "borderLeft": "2px solid " + self.colors['border'],
                                                    "borderRight": "2px solid " + self.colors['border'],
                                                    "paddingTop": "0px"
                                            }   
        )

        orders_html = html.Div([
                        orders_history_dash_table
                        ], 
                        style={
                            "marginTop": "0px",
                            "padding": "0px",
                            "borderLeft": "2px solid " + self.colors['border'],
                            "borderRight": "2px solid " + self.colors['border'],
                            "borderBottom": "2px solid " + self.colors['border'],
                            "backgroundColor": self.colors['orders_backgroundColor'],
                            "borderRadius": "0px"
                        }
        )

        app.layout = html.Div([
            # Summary statistics
            CollapsibleSection("Summary Statistics", stats_html, "summary", self.colors['sum_backgroundColor'], theme=self.theme).render(),

            # Backtest Details
            CollapsibleSection("Backtest Details", backtest_details_html, "details", self.colors['bd_backgroundColor'], default_open=False, theme=self.theme).render(),

            # Plots + Lateral Pannel
            CollapsibleSection("Backtest Charts", backtest_charts_section_html, "charts", self.colors['paper_bgcolor'], theme=self.theme).render(),
            
            # Orders History
            CollapsibleSection("Orders History", orders_html, "orders", self.colors['orders_backgroundColor'], default_open=False, theme=self.theme).render(),
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

        # Callback for collapsible sections
        @app.callback(
            Output({"type": "collapse-content", "index": ALL}, "style"),
            Output({"type": "collapse-icon", "index": ALL}, "children"),
            Input({"type": "collapse-header", "index": ALL}, "n_clicks"),
            State({"type": "collapse-content", "index": ALL}, "style"),
            State({"type": "collapse-content", "index": ALL}, "id"),
            prevent_initial_call=True,
        )
        def toggle_sections(_, styles, ids):
            trigger = ctx.triggered_id
            new_styles = []
            new_icons = []

            for style, component_id in zip(styles, ids):
                style = style or {}
                visible = style.get("display", "block") == "block"
                if component_id["index"] == trigger["index"]:
                    visible = not visible
                new_styles.append({
                    **style,
                    "display": "block" if visible else "none"
                })
                new_icons.append("▼" if visible else "▶")
            return new_styles, new_icons

        return app


    def make_backtest_details_html(self, blocks):
        backtest_details = html.Div([
                                DetailBlock(
                                    block["title"],
                                    block["metrics"],
                                    self.theme,
                                ).render()
                                for block in blocks
            ],
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(3, minmax(350px, 1fr))",
                "gap": "20px",
                "padding": "20px",
                "backgroundColor": self.colors["bd_backgroundColor"],
                "borderLeft": "2px solid " + self.colors["border"],
                "borderRight": "2px solid " + self.colors["border"]
            },
        )

        return backtest_details