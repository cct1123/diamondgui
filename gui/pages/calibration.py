import dash
import dash_bootstrap_components as dbc
from dash import html

dash.register_page(
    __name__,
    path="/calibration",
    name="Calibration",
    icon="fa-cogs",
    order=5,
)

layout = html.Div(id="fdsfdsf", children=[dbc.InputGroup()])


# from gui.pages.calibration_pages.pltrace_page import layout_pltrace

# from gui.pages.calibration_pages.thzrtrace_page import layout_thzrt

layout = html.Div(
    id="calibration",
    children=[
        # layout_pltrace,
        # layout_thzrt
    ],
)
