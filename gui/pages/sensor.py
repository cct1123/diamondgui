import dash
import dash_bootstrap_components as dbc
from dash import html
from dash_bootstrap_templates import load_figure_template

from gui.config import PLOT_THEME

icon_css = (
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css"
)
load_figure_template([PLOT_THEME])

dash.register_page(
    __name__,
    path="/sensor",
    name="Sensor",
    icon="fa-diamond",
    order=2,
    title="Sensor Properties",
)

layout = html.Div(
    [
        dbc.Col(
            [
                # layout_pODMR,
                # layout_rabi,
            ]
        )
    ]
)
