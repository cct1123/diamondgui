


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

from gui.config_custom import APP_THEME, PLOT_THEME
from gui.pages.measurement_pages.odmr_page import layout_odmr
from gui.pages.measurement_pages.confocal_page import layout_confocal

SINK_TIMEOUT = 0.2 # second
GUI_PORT = 9981

icon_css =  "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css"
load_figure_template([PLOT_THEME])

dash.register_page(
    __name__, 
    path="/sensor",
    name="Sensor",
    icon="fa-diamond",
    order=2,
    title="Sensor Properties"
    ) 

layout =  html.Div([
    dbc.Col([
        dbc.Col([
            html.H1("ODMR", className="p-2 mb-1 text-center"),
            layout_odmr
        ]),
        dbc.Col([
            html.H1("Confocal Scan", className="p-2 mb-1 text-center"),
            layout_confocal
        ]),
    ])

])
