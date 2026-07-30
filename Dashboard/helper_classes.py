from dash import html
from Dashboard.themes import THEME_COLORS


class MetricRow:
    def __init__(self, name, value, theme='light'):
        self.name = name
        self.value = value
        self.theme = theme
        self.colors = THEME_COLORS[theme]

    def render(self):
        return html.Div([
            html.Div(self.name, style={"color": self.colors['pannel_names'], "fontSize": "14px"}),
            html.Div(self.value, style={"fontWeight": "600", "fontSize": "16px", "color": self.colors['pannel_values']})
        ],
        style={
            "display": "flex",
            "justifyContent": "space-between",
            "padding": "8px 0"
        })
    

class SummaryCard:
    def __init__(self, title, value, theme='light'):
        self.title = title
        self.value = value
        self.theme = theme
        self.colors = THEME_COLORS[theme]

    def render(self, color=None):
        if(color is None):
            color = self.colors['sum_values']
        return html.Div([
                        html.Div(
                            self.title,
                            style={
                                "fontSize": "13px",
                                "fontWeight": "600",
                                "color": self.colors['sum_names'],
                                "textTransform": "uppercase",
                                "marginBottom": "10px"
                            }
                        ),
                        html.Div(
                            self.value,
                            style={
                                "fontSize": "24px",
                                "fontWeight": "700",
                                "color": color
                            })
                        ],
                        style={
                            "flex": "1",
                            "padding": "18px",
                            "textAlign": "center",
                            "borderRight": "1px solid " + self.colors['sum_right_borders']
                        }
        )


class CollapsibleSection:

    def __init__(self, title, children, section_id, background_color, default_open=True, theme='light'):
        self.title = title
        self.children = children
        self.section_id = section_id
        self.background_color = background_color
        self.default_open = default_open
        self.colors = THEME_COLORS[theme]

    def render(self):
        return html.Div([
                    html.Div([
                        html.Span(
                            "▼ " if self.default_open else "▶ ",
                            id={"type": "collapse-icon", "index": self.section_id},
                            style={"marginRight": "8px"}
                        ),

                        html.Span(self.title)],

                        id={"type": "collapse-header", "index": self.section_id},
                        n_clicks=0,
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "padding": "12px 20px",
                            "backgroundColor": self.background_color,
                            "color": self.colors["titles"],
                            "fontSize": "18px",
                            "fontWeight": "600",
                            "borderTop": f"2px solid {self.colors['border']}",
                            "borderLeft": f"2px solid {self.colors['border']}",
                            "borderRight": f"2px solid {self.colors['border']}",
                            "cursor": "pointer",
                            "userSelect": "none",
                        }
                    ),   

                    html.Div(
                        self.children,
                        id={"type": "collapse-content", "index": self.section_id},
                        style={"display": "block" if self.default_open else "none"}
                    )
            ],
        )


from dash import html


class DetailBlock:
    def __init__(self, title, metrics, theme='light'):
        self.title = title
        self.metrics = metrics
        self.colors = THEME_COLORS[theme]

    def render(self):
        return html.Div([
                    html.Div(
                        self.title,
                        style={
                            "fontSize": "15px",
                            "fontWeight": "600",
                            "color": self.colors["titles"],
                            "paddingBottom": "6px",
                            "marginBottom": "10px",
                            "borderBottom": f"1px solid {self.colors['bd_border']}",
                        },
                    ),

                    *[
                        html.Div([
                                html.Span(
                                    metric,
                                    style={"color": self.colors["bd_names"], "fontSize": "13px"},
                                ),
                                html.Span(
                                    value,
                                    style={
                                        "color": self.colors["bd_values"],
                                        "fontWeight": "600",
                                        "fontSize": "13px",
                                    },
                                ),
                            ],
                            style={
                                "display": "flex",
                                "justifyContent": "space-between",
                                "padding": "4px 0px",
                            },
                        )
                        for metric, value in self.metrics
                    ]
                ],
                style={
                    "padding": "14px 18px",
                    "border": f"1px solid {self.colors['bd_border']}",
                    "borderRadius": "4px",
                    "backgroundColor": self.colors["bd_block_backgroundColor"],
                },
        )