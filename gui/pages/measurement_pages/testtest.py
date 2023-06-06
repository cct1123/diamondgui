

import dash
from dash.dependencies import Output, Input
from dash import dcc, html, callback_context, callback
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
import dash_daq as ddaq

import plotly
import plotly.graph_objs as go
import plotly.io as pio
from collections import deque


from nspyre import DataSink
from measurement.odmr_dummy import SpinMeasurements
import threading
import random
import numpy as np
import time

SINK_TIMEOUT = 0.2 # second
GUI_PORT = 9981
app_theme = dbc.themes.SKETCHY
# app_theme = dbc.themes.DARKLY
# app_theme = dbc.themes.QUARTZ
# app_theme = dbc.themes.DARKLY
# app_theme = dbc.themes.VAPOR
# plot_template = 'vapor'
plot_template = 'sketchy'
# plot_template = 'darkly'
# plot_template = 'quartz'
# plot_template = 'darkly'
icon_css =  "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css"
load_figure_template([plot_template])

dash.register_page(
    __name__, 
    name="Measure",
    path="/measurement/fdfdsf",
    # icon="fa-diamond",
    # order=2,
    title="testtest Measurement"
    ) 

layout = html.Div(
    id = "ertertert", 
    children = [
        dbc.ButtonGroup(
                                [dbc.Button("Run", id="button-run454", outline=True, color="success", active=False, n_clicks=0), 
                                dbc.Button("Pause",  id="button-pause45",outline=True, color="warning", n_clicks=0), 
                                dbc.Button("Stop",  id="button-stop454", outline=True, color="danger", n_clicks=0),
                                ],
                            ),

    ]
    
    
)
