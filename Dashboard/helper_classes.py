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
