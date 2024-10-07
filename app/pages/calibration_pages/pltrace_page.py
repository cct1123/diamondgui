"""ODMR_ID
read the PL trace with NI DAQ

"""
import dash
from dash import dcc, html
from dash import callback, callback_context, Output, Input, State 
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

import plotly
import plotly.graph_objs as go

import numpy as np
from app.components import random_string
from app.config_custom import APP_THEME, PLOT_THEME, COLORSCALE, ODMR_ID, PLTRACE_ID
from app.components import UnitedInput, NumericInput
load_figure_template([PLOT_THEME])
import json
import random
import string

from calibration.pl_trace import PLTrace

# measurement logic -----------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------
pltrace = PLTrace()

# gui -------------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------
DATA_INTERVAL = 100
GRAPH_INTERVAL = 100
MAX_INTERVAL = 2147483647
ID = PLTRACE_ID

GRAPH_INIT = {'data':[], 'layout':go.Layout(template=PLOT_THEME)}
L_DICT = {"µm":1E3, "nm":1.0}

layout_para = dbc.Col([
    dbc.Row([
            dbc.ButtonGroup([
                dbc.Button("Run", id=ID+"button-run", outline=True, color="success", active=False, n_clicks=0), 
                # dbc.Button("Pause",  id=ID+"button-pause",outline=True, color="warning", n_clicks=0), 
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
            dbc.Row([NumericInput("Min Volt", min=-10.0E3, max=10.0E3, step="any", value=-5.0, unit="mV", id=ID+"input-min volt", persistence_type="local")]),
            dbc.Row([NumericInput("Max Volt", min=-10.0E3, max=10.0E3, step="any", value=5.0, unit="mV", id=ID+"input-max volt", persistence_type="local")]),
            dbc.Row([NumericInput("Number Average", min=1, max=40000, step=1, value=200, id=ID+"input-number average", persistence_type="local")]),
            # dbc.Row([UnitedInput("Sampling Rate", 1.0, 500E3, 0.1, 100E3, "Hz", id=ID+"input-sampling rate")]),
            dbc.Row([NumericInput("Refresh Rate", min=1.0, max=60.0, step=0.1, value=30.0, id=ID+"input-refresh rate", persistence_type="local")]),
            dbc.Row([NumericInput("History Window", min=0.0, max=3600, step="any", value=5.0, unit="s", id=ID+"input-history window", persistence_type="local")]),
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
    dcc.Store(id=ID+"store-params", storage_type='memory', data={}),
    dcc.Store(id=ID+"auxillary", data={})
])

layout_pltrace= html.Div([
    dbc.Row([
        dbc.Col([layout_para], width=4),
        dbc.Col([layout_graph], width=8)
    ]), 
    dbc.Col([
        # layout_graph_info, 
        layout_hidden
    ])
])
# ---------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------

# handling callback events-------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------

@callback(
    Output(ID+"store-params", "data"),
    Input(ID+"input-min volt"+"-store", "data"),
    Input(ID+"input-max volt"+"-store", "data"), 
    Input(ID+"input-number average"+"-store", "data"), 
    Input(ID+"input-refresh rate"+"-store", "data"), 
    Input(ID+"input-history window"+"-store", "data"), 
    # State(ID+"input-max volt", "value"), 
    # State(ID+"input-min volt", "value"), 
    # State(ID+"input-number average", "value"), 
    # State(ID+"input-refresh rate", "value"), 
    # State(ID+"input-history window", "value"), 
    prevent_initial_call=True,
)
def _update_params(min_volt, max_volt, n_average, refresh_rate, history_window):
    print(min_volt, max_volt, n_average, refresh_rate, history_window)
    # print(*minv, *maxv, *num, *refreshrate, *hist_window)
    sampling_rate = refresh_rate*n_average
    num_trace = refresh_rate*history_window
    paramsdict = dict(
            min_volt = min_volt*1E3, # in [V]
            max_volt = max_volt*1E3, # in [V]
            n_average = n_average,
            refresh_rate = refresh_rate, # [Hz]
            sampling_rate = sampling_rate, 
            history_window = history_window,
            num_trace = num_trace
        )
    pltrace.set_params(**paramsdict)
    return paramsdict



@callback(
    Output(ID+"button-run", "outline"),
    Output(ID+"button-stop", "outline"),
    Output(ID+"interval-data", "interval"),
    Output(ID+"interval-graph", "interval"),
    Input(ID+"button-run", "n_clicks"),
    Input(ID+"button-stop", "n_clicks"),
    prevent_initial_call=True,)
def check_run_stop_exp(rn, sn):
    ctx = callback_context
    if ctx.triggered_id == ID+"button-run":
        return run_exp()
    elif ctx.triggered_id == ID+"button-stop":
        return stop_exp()
def run_exp():
    print("trigggg runnnnnnnnnnnnnn")
    pltrace.start()
    return False, True, DATA_INTERVAL, GRAPH_INTERVAL

def stop_exp():
    print("trigggg stop")
    pltrace.stop()
    return True, False, MAX_INTERVAL, MAX_INTERVAL

@callback(
    Output(ID+"auxillary", "data"),
    Input(ID+"interval-data", "n_intervals"),
    prevent_initial_call=True,)
def _update_data(_):
    return {}

@callback(
    Output(ID+'graph', 'figure'),
    Input(ID+"interval-graph", "n_intervals"),
    prevent_initial_call=True,)
def _update_graph(_):
    temptemp = pltrace.dataset["timestamp"]
    xx = temptemp[~np.isnan(temptemp)]
    temptemp = pltrace.dataset["data"]
    yy = temptemp[~np.isnan(temptemp)]
    if len(xx) == 0:
        xx = np.array([0.0])
        yy = np.array([0.0])
    xx -= np.max(xx)
    ymin = np.min(yy)
    ymax = np.max(yy)
    yran = 0.05*abs(ymax-ymin)
    # print(f"xx:{xx}")
    # print(f"yy:{yy}")
    # data = go.Scatter(x = xx, y=yy, name='scatter', mode='lines+markers')
    data = go.Scattergl(x = xx, y=yy, name='scatter', mode='lines+markers')
    return {'data':[data], 
        'layout':go.Layout(
            # xaxis = dict(range=[min(xx), max(xx)], exponentformat="power"), 
            xaxis = dict(range=[min(xx), max(xx)]), 
            # https://stackoverflow.com/questions/71830854/how-to-change-the-y-axis-in-plotly-to-go-from-scientific-to-exponential-or-plain
            yaxis = dict(range=[ymin-yran, ymax+yran], tickformat=",.3s"), 
            xaxis_title="time [s]",
            yaxis_title="Voltage [V]",
            template=PLOT_THEME, 
            font=dict(size=21)
            )
        }


# ---------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------

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
    app.layout = layout_pltrace
    app.run_server(
        # host="0.0.0.0", 
        debug=DEBUG, 
        port=GUI_PORT)