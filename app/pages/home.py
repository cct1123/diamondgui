import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash import dcc, html, callback, callback_context
from dash.dependencies import Output, Input, State
import os
from app.pages.home_pages.task_manager import layout_taskmanager

import logging
logger = logging.getLogger(__name__)

MAINDIR = os.getcwd()

dash.register_page(
    __name__, 
    path="/",
    name="Home",
    icon="fa-home",
    order=1,
    # # meta tag
    # title="Diamond Dashboard", 
    # image="icons8-sparkling-diamond-64.ico", 
    # description="The home page for diamond dashboard."
    ) 

layout = html.Div(
    id = "home", 
    children = [
        # Navigation Section
        dbc.Row([
            dbc.Col([
                # dbc.Navbar(
                #     children=[
                #         dbc.NavItem(dbc.NavLink(dbc.Row([
                #             dbc.Col(html.Img(src="assets/hardware.png", height="200px")),
                #             # dbc.Col("Hardwares", className="ms-2")
                #         ], align="center", className="g-0"), href="/hardwares", external_link=True, style={"backgroundColor": "transparent"})),
                #         dbc.NavItem(dbc.NavLink(dbc.Row([
                #             dbc.Col(html.Img(src="assets/spectrometer.png", height="200px")),
                #             # dbc.Col("Spectrometry", className="ms-2")
                #         ], align="center", className="g-0"), href="/spectrometry", external_link=True, style={"backgroundColor": "transparent"})),
                #         dbc.NavItem(dbc.NavLink(dbc.Row([
                #             dbc.Col(html.Img(src="assets/analysis.png", height="200px")),
                #             # dbc.Col("Analysis", className="ms-2")
                #         ], align="center", className="g-0"), href="/analysis", external_link=True, style={"backgroundColor": "transparent"})),
                #         dbc.NavItem(dbc.NavLink(dbc.Row([
                #             dbc.Col(html.Img(src="assets/calibration.png", height="200px")),
                #             # dbc.Col("Calibration", className="ms-2")
                #         ], align="center", className="g-0"), href="/calibration", external_link=True, style={"backgroundColor": "transparent"})),                    ],
                #     # color="info",
                #     # dark=True,
                #     style={"border": "none"},
                #     className="mb-5"
                # )
            ], width=12),
        ]),
        # Task Manager Section
        dbc.Row([
            dbc.Col([
                html.H4("Task Manager", className="card-title"),
                layout_taskmanager,
            ]),
        ]),
        # Log Section
        dbc.Row([
            dbc.Col([
                dbc.CardBody([
                    html.H4("Log", className="card-title"),
                    # html.P("Log messages", className="card-text"),
                    html.Div(id="log-messages", style={"height": "200px", "overflowY": "scroll"})
                ])
            ]),
        ]),
        dcc.Interval(
            id='interval-component',
            interval = 1000 * 1, # 1 second in milliseconds
            n_intervals=0
        )
    ]
)

@callback(
    Output("log-messages", "children"),
    Input("interval-component", "n_intervals")
)
def read_log_file(_n):
    with open(os.path.join(MAINDIR, "temp.log"), "r") as f:
        lines = f.readlines()[-100:]
        log = "\n".join(lines)
    return dcc.Markdown(log)
