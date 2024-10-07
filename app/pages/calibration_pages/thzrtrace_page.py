"""ODMR_ID
read the PL trace with NI DAQ

"""
if __name__ == "__main__":
    import sys
    import os
    path_project = "\\".join(os.getcwd().split("\\")[:-3])
    print(path_project)
    # caution: path[0] is reserved for script path (or '' in REPL)
    sys.path.insert(1, path_project)


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

from calibration.thzreflection_trace import THzReflectionTrace
from measurement.task_base import INT_INF
from nspyre import DataSink

# # measurement logic ================================================================================================================
# # ===============================================================================================================================
thzrt = THzReflectionTrace()

#==============================================================================================================================
#===============================================================================================================================

# specific gui components=============================================================================================================
# begin===========================================================================================================

DATA_INTERVAL = 100
GRAPH_INTERVAL = 100
MAX_INTERVAL = 2147483647
ID = PLTRACE_ID

GRAPH_INIT = {'data':[], 'layout':go.Layout(template=PLOT_THEME)}
L_DICT = {"µm":1E3, "nm":1.0}

layout_para = dbc.Col([
    dbc.Row([
            dbc.ButtonGroup([
                dbc.Button("Start", id=ID+"button-start", outline=True, color="success", active=False, n_clicks=0), 
                dbc.Button("Pause",  id=ID+"button-pause",outline=True, color="warning", disabled=True, n_clicks=0), 
                dbc.Button("Stop",  id=ID+"button-stop", outline=True, color="danger", disabled=True, n_clicks=0),
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
            dbc.Row([NumericInput("MW Freq", min=380.0, max=410.0, step="any", value=395.0, unit="GHz", id=ID+"input-mwfreq", persistence_type="local")]),
            dbc.Row([NumericInput("MW Power", min=0.0, max=5.0, step=1E-3, value=5.0, unit="V", id=ID+"input-mwpower", persistence_type="local")]),
            dbc.Row([NumericInput("Pulse Rate", min=1E3, max=1E9, step="any", value=0.3124E6, unit="Hz", id=ID+"input-pulse_rate", persistence_type="local")]),
            dbc.Row([NumericInput("Volt Max", min=-10E3, max=10E3, step=0.1, value=20.0, unit="mV", id=ID+"input-daq_max_mv", persistence_type="local")]),
            dbc.Row([NumericInput("Volt Min", min=-10E3, max=10E3, step=0.1, value=-20.0, unit="mV", id=ID+"input-daq_min_mv", persistence_type="local")]),
            dbc.Row([NumericInput("Sampling Rate", min=1E3, max=500E3, step="any", value=500E3, unit="Hz", id=ID+"input-daq_srate", persistence_type="local")]),
            dbc.Row([NumericInput("Refresh Rate", min=1.0, max=1E3, step=0.1, value=20.0, unit="Hz",id=ID+"input-refresh", persistence_type="local")]),
            dbc.Row([NumericInput("History Window", min=0.0, max=120000, step=0.1, value=5.0, unit="s", id=ID+"input-window", persistence_type="local")]),
        ]),
    ]),

    dbc.Row([
        dbc.Col([
            dbc.Row([NumericInput("Stop Time", min=0.0, max=86400, step="any", value=10, unit="s", id=ID+"input-timestop", persistence_type="local")]),
            dbc.Row([NumericInput("Runs", min=0, max=INT_INF, step=1, value=INT_INF, unit="", id=ID+"input-runs", persistence_type="local")]),
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
    dcc.Store(id=ID+"store-stateset", storage_type='memory', data={}),
    dcc.Store(id=ID+"store-paraset", storage_type='memory', data={}),
    dcc.Store(id=ID+"store-dataset", storage_type='memory', data={}),
    dcc.Store(id=ID+"auxillary", data={})
])

layout_thzrt= html.Div([
    dbc.Row([
        dbc.Col([layout_para], width=4),
        dbc.Col([layout_graph], width=8)
    ]), 
    dbc.Col([
        # layout_graph_info, 
        layout_hidden
    ])
])
# end=============================================================================================================
# ============================================================================================================



# handling callback events===========================================================================================
# begin=============================================================================================================

# apply experiment parameters------------------------------------------------------------------------------------------
@callback(
    Output(ID+"auxillary", "data"),
    Input(ID+"input-mwfreq", "value"), 
    Input(ID+"input-mwpower", "value"),
    Input(ID+"input-pulse_rate", "value"),
    Input(ID+"input-daq_max_mv", "value"),
    Input(ID+"input-daq_min_mv", "value"),
    Input(ID+"input-daq_srate", "value"),
    Input(ID+"input-refresh", "value"),
    Input(ID+"input-window", "value"),
    prevent_initial_call=False,
)
def update_params(mwfreq, mwpower, pulse_rate, daq_max_mv, daq_min_mv, daq_srate, refresh, window):
    paramsdict = dict(
            mwfreq=mwfreq, 
            mwpower=mwpower, 
            pulse_rate=pulse_rate, 
            daq_max=daq_max_mv/1E3, 
            daq_min=daq_min_mv/1E3, 
            daq_srate=daq_srate, 
            refresh=refresh, 
            window=window
        )
    print(paramsdict)
    thzrt.set_paraset(**paramsdict)
    return {}
# ---------------------------------------------------------------------------------------------

# handling button events---------------------------------------------------------------------------------
@callback(
    Output(ID+"button-start", "disabled"),
    Output(ID+"button-pause", "disabled"),
    Output(ID+"button-stop", "disabled"),
    Output(ID+"interval-data", "interval"),
    Output(ID+"interval-graph", "interval"),
    Input(ID+"button-start", "n_clicks"),
    Input(ID+"button-pause", "n_clicks"),
    Input(ID+"button-stop", "n_clicks"),
    prevent_initial_call=True,)
def check_run_stop_exp(_r, _p, _s):
    ctx = callback_context
    if ctx.triggered_id == ID+"button-start":
        return _run_exp()
    elif ctx.triggered_id == ID+"button-pause":
        return _pause_exp()
    elif ctx.triggered_id == ID+"button-stop":
        return _stop_exp()
def _run_exp():
    print("trigggg runnnnnnnnnnnnnn")
    thzrt.start()
    # return False, True, True, DATA_INTERVAL, GRAPH_INTERVAL
    return True, False, False, DATA_INTERVAL, GRAPH_INTERVAL

def _pause_exp():
    print("trigggg pause")
    thzrt.pause()
    # return True, False, True, MAX_INTERVAL, MAX_INTERVAL
    return False, True, False, MAX_INTERVAL, MAX_INTERVAL

def _stop_exp():
    print("trigggg stop")
    thzrt.stop()
    # return True, False, False, MAX_INTERVAL, MAX_INTERVAL
    return False, True, True, MAX_INTERVAL, MAX_INTERVAL

@callback(
    Output(ID+"input-mwfreq", "disabled"),
    Output(ID+"input-mwpower", "disabled"),
    Output(ID+"input-pulse_rate", "disabled"),
    Output(ID+"input-daq_max_mv", "disabled"),
    Output(ID+"input-daq_min_mv", "disabled"),
    Output(ID+"input-daq_srate", "disabled"),
    Output(ID+"input-refresh", "disabled"),
    Output(ID+"input-window", "disabled"),
    Input(ID+"store-stateset", "data"),
    prevent_initial_call=True,)
def disable_parameters(stateset):
    print(stateset["state"])
    if stateset["state"] == "run":
        print("here is run status")
        return True, True, True, True, True, True, True, True
    elif stateset["state"] in ["idle", "wait", "done", "error"]:
        print("here is not run status")
        return False, False, False, False, False, False, False, False
# -----------------------------------------------------------------------------------------------


# update data and graph--------------------------------------------------------------------------------
@callback(
    Output(ID+"store-stateset", "data"),
    Output(ID+"store-paraset", "data"),
    Output(ID+"store-dataset", "data"),
    Input(ID+"interval-data", "n_intervals"),
    prevent_initial_call=False,)
def update_state_parameters_data(_):
    # datasink.start()
    # data = datasink.pop()
    # datasink.stop()
    storedata = dict()
    storedata = dict(stateset=thzrt.stateset, paraset=thzrt.paraset, dataset=thzrt.dataset)
    # with DataSink(thzrt._name) as dss:
    #     dss.pop()
        # storedata = dict(stateset=dss.stateset, paraset=dss.paraset, dataset=dss.dataset)
    # print(f"Data Here!!!!!!!!!!!!!!!!{storedata}")
    # return storedata.stateset, storedata.paraset, storedata.dataset
    return storedata["stateset"], storedata["paraset"], storedata["dataset"]
    # return thzrt.stateset, thzrt.paraset, thzrt.dataset
    # return {}, {}, {}

@callback(
    Output(ID+'graph', 'figure'),
    # Input(ID+"interval-graph", "n_intervals"),
    Input(ID+"store-dataset", "data"),
    prevent_initial_call=True,)
def update_graph(dataset):
    xx = np.array(dataset["zbd_time"])
    # print(dataset["zbd_amp"])
    yy = np.array(dataset["zbd_amp"])*1E3
    ymin = np.min(yy)
    ymax = np.max(yy)
    yran = 0.05*abs(ymax-ymin)
    data = go.Scattergl(x = xx, y=yy, name='scatter', mode='lines+markers')
    return {'data':[data], 
        'layout':go.Layout(
            # xaxis = dict(range=[min(xx), max(xx)], exponentformat="power"), 
            xaxis = dict(range=[min(xx), max(xx)]), 
            # https://stackoverflow.com/questions/71830854/how-to-change-the-y-axis-in-plotly-to-go-from-scientific-to-exponential-or-plain
            yaxis = dict(range=[ymin-yran, ymax+yran], tickformat=",.3s"), 
            xaxis_title="time [s]",
            yaxis_title="Voltage [mV]",
            template=PLOT_THEME, 
            font=dict(size=21)
            )
        }
# -----------------------------------------------------------------------------------------------


# end=============================================================================================================
# ============================================================================================================


if __name__ == "__main__":
    
    from dash_bootstrap_components import themes
    # APP_THEME = themes.JOURNAL
    APP_THEME = themes.SKETCHY
    # APP_THEME = themes.QUARTZ
    # APP_THEME = themes.DARKLY
    # APP_THEME = themes.VAPOR
    # APP_THEME = themes.SUPERHERO
    DEBUG = True
    GUI_PORT = 9843
    app = dash.Dash(
        __name__, 
        external_stylesheets=[
            APP_THEME, 
        ], 
        external_scripts=[])
    app.layout = layout_thzrt
    app.run_server(
        # host="0.0.0.0", 
        debug=DEBUG, 
        port=GUI_PORT)