import dash
from dash import dcc, html
from dash import callback, callback_context, Output, Input, State 
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

import plotly
import plotly.graph_objs as go

import numpy as np
from gui.components import random_string
from gui.config_custom import APP_THEME, PLOT_THEME, COLORSCALE, ODMR_ID
from gui.components import UnitedInput, NumericInput
load_figure_template([PLOT_THEME])
import json
import random
import string
DATA_INTERVAL = 1000
GRAPH_INTERVAL = 2000
MAX_INTERVAL = 2147483647
ID = ODMR_ID
ID = "odmr-"+random_string(8)

GRAPH_INIT = {'data':[], 'layout':go.Layout(template=PLOT_THEME)}
L_DICT = {"µm":1E3, "nm":1.0}

layout_para = dbc.Col([
    dbc.Row([
            dbc.ButtonGroup([
                dbc.Button("Scan", id=ID+"button-run", outline=True, color="success", active=False, n_clicks=0), 
                dbc.Button("Pause",  id=ID+"button-pause",outline=True, color="warning", n_clicks=0), 
                dbc.Button("Stop",  id=ID+"button-stop", outline=True, color="danger", n_clicks=0),
            ],),
            # dbc.Col([html.Div(id="div-status", children=[]),]),
            dbc.Progress(
                value=0, id="progress-bar", animated=True, striped=False, label="", className="mt-2 mb-2"
            ),
            ],
            align="center",
        ),
    dbc.Row([
        dbc.Col([
            dbc.Checklist(
                options=[
                    {"label": "Pulsed?", "value": 1},
                ],
                value=[1],
                id="input-Pulsed?",
                inline=True,
                switch=True,
                persistence=True, # currently persistence fails
                persistence_type='local',
            ),
            dbc.Row([UnitedInput("Pi Pulse", 0, 1E6, 2, 1000.0, "ns", id=ID+"input-Pi Pulse")]),
            dbc.Row([UnitedInput("Power", -100, 100, 0.1, 0.0, "dBm", unitdict={"dBm":1},  id=ID+"input-Power")]),
        ]),
        dbc.Col([
            dbc.Row([UnitedInput("Freq Begin", 0, 500E9, 1, 2.85E9, "Hz",  id=ID+"input-Freq Begin")]),
            dbc.Row([UnitedInput("Freq End", 0, 500E9, 1, 2.9E9, "Hz", id=ID+"input-Freq End")]),
            dbc.Row([UnitedInput("Freq Step", 0, 500E9, 1, 0.05E9, "Hz", id=ID+"input-Freq Step")]),
        ]),
    ]),
])

layout_graph = dbc.Col([
    dbc.Container([
        dcc.Graph(
            figure=GRAPH_INIT,
            id=ID+'graph', mathjax=True, animate=False,
            responsive="auto", 
            style={"aspectRatio":"1.2/1"}
            )],
    fluid=True)
],)

layout_hidden = dbc.Row([
    dcc.Interval(id=ID+"interval-data", interval=MAX_INTERVAL, n_intervals=0),
    dcc.Interval(id=ID+"interval-graph", interval=MAX_INTERVAL, n_intervals=0),
    # dcc.Store(id=ID+"store-plot", storage_type='memory', data=plotdata),
    # dcc.Store(id=ID+"store-select", storage_type='memory', data=selectdata)
])

layout_odmr = html.Div([
    dbc.Row([
        dbc.Col([layout_para], width=5),
        dbc.Col([layout_graph], width=7)
    ]), 
    dbc.Col([
        # layout_graph_info, 
        layout_hidden
    ])
])



if __name__ == "__main__":
    from dash_bootstrap_components import themes
    # APP_THEME = themes.JOURNAL
    # APP_THEME = themes.SKETCHY
    # APP_THEME = themes.QUARTZ
    # APP_THEME = themes.DARKLY
    # APP_THEME = themes.VAPOR
    APP_THEME = themes.SUPERHERO
    DEBUG = True
    GUI_PORT = 9843
    app = dash.Dash(
        __name__, 
        external_stylesheets=[
            APP_THEME, 
        ], 
        external_scripts=[])
    app.layout = layout_odmr
    app.run_server(
        # host="0.0.0.0", 
        debug=DEBUG, 
        port=GUI_PORT)
