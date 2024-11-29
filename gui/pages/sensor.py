import dash
import dash_bootstrap_components as dbc
from dash import html
from dash_bootstrap_templates import load_figure_template
from gui.config_custom import PLOT_THEME

# from gui.pages.measurement_pages.dummeasurement_page import layout_dummyODMR
# from gui.pages.measurement_pages.dummeasurement_page_copy import layout_dummyODMR_copy
from gui.pages.measurement_pages.odmr_page import layout_pODMR
from gui.pages.measurement_pages.rabi_page import layout_rabi

SINK_TIMEOUT = 0.2  # second
GUI_PORT = 9981

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
                dbc.Col(
                    [
                        html.H1("ODMR", className="p-2 mb-1 text-center"),
                        layout_pODMR,
                    ]
                ),
                dbc.Col(
                    [
                        html.H1("Rabi", className="p-2 mb-1 text-center"),
                        layout_rabi,
                    ]
                ),
            ]
        )
    ]
)
