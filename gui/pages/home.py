import logging
import os

import dash
from dash import html

# from gui.pages.home_pages.task_manager import layout_taskmanager

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

from gui.pages.home_pages.logdisplay_page import layout_logdisplay

layout = html.Div(
    id="home",
    children=[
        # Navigation Section
        layout_logdisplay
    ],
)

# @callback(
#     Output("log-messages", "children"),
#     Input("interval-component", "n_intervals")
# )
# def read_log_file(_n):
#     with open(os.path.join(MAINDIR, "temp.log"), "r") as f:
#         lines = f.readlines()[-100:]
#         log = "\n".join(lines)
#     return dcc.Markdown(log)
