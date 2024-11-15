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
from app.config_custom import APP_THEME, PLOT_THEME, COLORSCALE, THZRTRACE_ID
from app.components import NumericInput
load_figure_template([PLOT_THEME])
import json
import random
import string
import atexit

from measurement.odmr import pODMR
from measurement.task_base import INT_INF
from measurement.task_base import JobManager

podmr = pODMR()
jm = JobManager()
def release_lock():
    return jm.stop()
atexit.register(release_lock)
#==============================================================================================================================
#===============================================================================================================================

# specific gui components=============================================================================================================
# begin===========================================================================================================

DATA_INTERVAL = 100
IDLE_INTERVAL = 1000
MAX_INTERVAL = 2147483647
ID = podmr.get_uiid()

GRAPH_INIT = {'data':[], 'layout':go.Layout(template=PLOT_THEME)}
L_DICT = {"µm":1E3, "nm":1.0}

layout_buttons = dbc.Row([
    dbc.ButtonGroup([
        dbc.Button("Start", id=ID + "-button-start", outline=True, color="info", active=False, n_clicks=0),
        dbc.Button("Pause", id=ID + "-button-pause", outline=True, color="secondary", disabled=True, n_clicks=0),
        dbc.Button("Stop", id=ID + "-button-stop", outline=True, color="secondary", disabled=True, n_clicks=0),
    ]),
])

layout_progressbar = dbc.Row([
    dbc.Col(
        id=ID + "-div-progressbar",
        children=[
            dbc.Progress(
                value=0, min=0.0, max=1.0, id=ID + "-progressbar", animated=True, striped=True, label="",
                color="info", className="mt-2 mb-2"
            ),
        ]
    ),
])

# freq_start = 398.50,
# freq_stop = 398.6,
# freq_step = 0.2E-3,
# mw_powervolt = 5.0,
# laser_current = 81.26, #0 to 100%
# min_volt = -0.002, # [V]
# max_volt = 0.010,

# init_laser = 1500.0,

# init_nslaser = 4.0,
# init_isc = 200,
# init_repeat = 20,
# init_wait = 401.0,
# mw_time = 2000.0,
# read_wait = 500.0,
# read_laser = 1201.0,
tab_exppara_task = dbc.Col(
    [
        dbc.Row(
            [
                NumericInput(
                    "Priority", min=0, max=10, step=1, value=10, unit="",
                    id=ID + "-input-priority", persistence_type="local"
                ),
            ]
        ),
        dbc.Row(
            [
                NumericInput(
                    "Stop Time", min=0.0, max=86400, step=1, value=10, unit="s",
                    id=ID + "-input-stoptime", persistence_type="local"
                ),
            ]
        ),
    ],
    className="mt-2 mb-2",
)

tab_exppara_hardware = dbc.Col([
    NumericInput(
        "Freq Begin", min=96, max=480, step="any", value=398.5, unit="GHz",
        id=ID + "-input-freq_begin", persistence_type="local"
    ),
    NumericInput(
        "Freq End", min=96, max=480, step="any", value=398.6, unit="GHz",
        id=ID + "-input-freq_end", persistence_type="local"
    ),
    NumericInput(
        "Freq Step", min=0, max=10.0E3, step="any", value=5.0, unit="MHz",
        id=ID + "-input-freq_step", persistence_type="local"
    ),
    NumericInput(
        "MW Power", min=0.0, max=5.0, step="any", value=5.0, unit="V",
        id=ID + "-input-mw_powervolt", persistence_type="local"
    ),
    NumericInput(
        "Laser Current", min=0.0, max=100.0, step=0.01, value=81.26, unit="%",
        id=ID + "-input-laser_current", persistence_type="local"
    ),
    NumericInput(
        "Min Volt", min=-10.0E3, max=10.0E3, step="any", value=-2, unit="mV",
        id=ID + "-input-min_volt", persistence_type="local"
    ),
    NumericInput(
        "Max Volt", min=-10.0E3, max=10.0E3, step="any", value=10, unit="mV",
        id=ID + "-input-max_volt", persistence_type="local"
    ),
        
        
        ],
    className="mt-2 mb-2",
)

tab_exppara_sequence = dbc.Col([
    dbc.Row([
        NumericInput(
            "Init Laser", min=0.0, max=10E3, step=1.0, value=4.0, unit="ns",
            id=ID + "-input-init_nslaser", persistence_type="local"
        ),
    ]),
    dbc.Row([
        NumericInput(
            "Init ISC", min=0.0, max=10E3, step=1.0, value=200, unit="ns",
            id=ID + "-input-init_isc", persistence_type="local"
        ),
    ]),
    dbc.Row([
        NumericInput(
            "Init Repeat", min=0.0, max=10E3, step=1.0, value=20, unit="",
            id=ID + "-input-init_repeat", persistence_type="local"
        ),
    ]),
    dbc.Row([
        NumericInput(
            "Init Wait", min=0.0, max=10E3, step=1.0, value=401.0, unit="ns",
            id=ID + "-input-init_wait", persistence_type="local"
        ),
    ]),
    dbc.Row([
        NumericInput(
            "MW Time", min=0.0, max=100E3, step=1.0, value=2000.0, unit="ns",
            id=ID + "-input-mw_time", persistence_type="local"
        ),
    ]),
    dbc.Row([
        NumericInput(
            "Read Wait", min=0.0, max=1E3, step=1.0, value=500.0, unit="ns",
            id=ID + "-input-read_wait", persistence_type="local"
        ),
    ]),
    dbc.Row([
        NumericInput(
            "Read Laser", min=0.0, max=100E3, step=1.0, value=1201.0, unit="ns",
            id=ID + "-input-read_laser", persistence_type="local"
        ),
    ]),
],
    className="mt-2 mb-2",)

layout_exppara = dbc.Row([
    dbc.Col([
            dbc.Tabs(
    [   dbc.Tab(tab_exppara_task, label="Task"),
        dbc.Tab(tab_exppara_hardware, label="Hardware"),
        dbc.Tab(tab_exppara_sequence, label="Sequence"),
    ]
)
    ])

])

layout_para = dbc.Col([
    layout_buttons,
    layout_progressbar,
    layout_exppara
])

layout_graph = dbc.Row([
    dbc.Container([
        dcc.Graph(
            figure=GRAPH_INIT,
            id=ID+'graph', mathjax=True, animate=False,
            responsive="auto", 
            style={"aspectRatio":"1.2/1"}
        ),
    ], fluid=True),
])

layout_hidden = dbc.Row([
    dcc.Interval(id=ID+"interval-data", interval=MAX_INTERVAL, n_intervals=0),
    # dcc.Store(id=ID+"-store-plot", storage_type='memory', data=plotdata),
    dcc.Store(id=ID+"-store-stateset", storage_type='memory', data={}),
    dcc.Store(id=ID+"-store-paraset", storage_type='memory', data={}),
    dcc.Store(id=ID+"-store-dataset", storage_type='memory', data={}),
    dcc.Store(id=ID+"auxillary", data={})
])

layout_pODMR = html.Div([
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
    Input(ID + "-input-priority", "value"),
    Input(ID + "-input-stoptime", "value"),
    Input(ID + "-input-freq_begin", "value"),
    Input(ID + "-input-freq_end", "value"),
    Input(ID + "-input-freq_step", "value"),
    Input(ID + "-input-mw_powervolt", "value"),
    Input(ID + "-input-laser_current", "value"),
    Input(ID + "-input-min_volt", "value"),
    Input(ID + "-input-max_volt", "value"),
    Input(ID + "-input-init_nslaser", "value"),
    Input(ID + "-input-init_isc", "value"),
    Input(ID + "-input-init_repeat", "value"),
    Input(ID + "-input-init_wait", "value"),
    Input(ID + "-input-mw_time", "value"),
    Input(ID + "-input-read_wait", "value"),
    Input(ID + "-input-read_laser", "value"),
    prevent_initial_call=False,
)
def update_params(priority, stoptime, 
                  freq_begin, freq_end, freq_step, 
                  mw_powervolt, laser_current, 
                  min_volt, max_volt, 
                  init_nslaser, init_isc, init_repeat, init_wait, 
                  mw_time, read_wait, read_laser):
    paramsdict = dict(
        freq_start=freq_begin,  # [GHz]
        freq_stop=freq_end,  # [GHz]
        freq_step=freq_step/1E3,  # [GHz]
        init_wait=init_wait,
        init_nslaser=init_nslaser,
        init_isc=init_isc,
        init_repeat=init_repeat,
        mw_time=mw_time,
        read_wait=read_wait,
        read_laser=read_laser,
        mw_powervolt=mw_powervolt,
        laser_current=laser_current,  # 0 to 100%
        min_volt=min_volt/1E3,# [V]
        max_volt=max_volt/1E3,# [V]
    )
    podmr.set_paraset(**paramsdict)
    podmr.set_priority(priority)
    podmr.set_stoptime(stoptime)
    return {}
# ---------------------------------------------------------------------------------------------

# handling button events---------------------------------------------------------------------------------
@callback(
    Output(ID+"interval-data", "interval"),
    Input(ID+"-button-start", "n_clicks"),
    Input(ID+"-button-pause", "n_clicks"),
    Input(ID+"-button-stop", "n_clicks"),
    prevent_initial_call=False,)
def check_run_stop_exp(_r, _p, _s):
    ctx = callback_context
    if ctx.triggered_id == ID+"-button-start":
        return _run_exp()
    elif ctx.triggered_id == ID+"-button-pause":
        return _pause_exp()
    elif ctx.triggered_id == ID+"-button-stop":
        return _stop_exp()
    else:
        # initial call
        # print("hello from the button store initial call")
        if podmr.state == "run":
            return DATA_INTERVAL
        else:
            return IDLE_INTERVAL

def _run_exp():
    jm.start()
    jm.submit(podmr)
    # return False, True, True, DATA_INTERVAL
    return DATA_INTERVAL

def _pause_exp():
    podmr.pause()
    # return True, False, True, MAX_INTERVAL
    return IDLE_INTERVAL

def _stop_exp():
    podmr.stop()
    # return True, False, False, MAX_INTERVAL
    return IDLE_INTERVAL
# -----------------------------------------------------------------------------------------------


# update data, status, graph--------------------------------------------------------------------------------
@callback(
    Output(ID+"-store-stateset", "data"),
    Output(ID+"-store-paraset", "data"),
    Output(ID+"-store-dataset", "data"),
    Input(ID+"interval-data", "n_intervals"),
    prevent_initial_call=False,)
def update_state_parameters_data(_):
    storedata = dict()
    storedata = dict(stateset=podmr.stateset, paraset=podmr.paraset, dataset=podmr.dataset)
    return storedata["stateset"], storedata["paraset"], storedata["dataset"]


@callback(
    Output(ID + "-input-priority", "disabled"),
    Output(ID + "-input-stoptime", "disabled"),
    Output(ID + "-input-freq_begin", "disabled"),
    Output(ID + "-input-freq_end", "disabled"),
    Output(ID + "-input-freq_step", "disabled"),
    Output(ID + "-input-mw_powervolt", "disabled"),
    Output(ID + "-input-laser_current", "disabled"),
    Output(ID + "-input-min_volt", "disabled"),
    Output(ID + "-input-max_volt", "disabled"),
    Output(ID + "-input-init_nslaser", "disabled"),
    Output(ID + "-input-init_isc", "disabled"),
    Output(ID + "-input-init_repeat", "disabled"),
    Output(ID + "-input-init_wait", "disabled"),
    Output(ID + "-input-mw_time", "disabled"),
    Output(ID + "-input-read_wait", "disabled"),
    Output(ID + "-input-read_laser", "disabled"),
    Input(ID+"-store-stateset", "data"),
    prevent_initial_call=False,)

def disable_parameters(stateset):
    if stateset["state"] == "run":
        return [True]*16
    elif stateset["state"] in ["idle", "wait", "done", "error"]:
        return [False]*16

@callback(
    Output(ID+"-button-start", "disabled"),
    Output(ID+"-button-pause", "disabled"),
    Output(ID+"-button-stop", "disabled"),
    Input(ID+"-store-stateset", "data"),
    prevent_initial_call=False,)
def disable_buttons(stateset):
    # print(stateset["state"])
    if stateset["state"] == "run":
        return True, False, False
    elif stateset["state"] == "wait":
        return False, True, False
    elif stateset["state"] in ["idle", "done"]:
        return False, True, True
    elif stateset["state"] == "error":
        return False, False, False

@callback(
    Output(ID+"-progressbar", 'value'),
    Output(ID+"-progressbar", 'label'),
    Input(ID+"-store-stateset", "data"),
)
def update_progress(stateset):
    progress_num = stateset["idx_run"]/stateset["num_run"]
    progress_time = stateset["time_run"]/stateset["time_stop"]
    progress = max(progress_num, progress_time)
    # print(f"progress = {progress}")
    return progress, f"{round(100*progress)}%"

@callback(
    Output(ID+'graph', 'figure'),
    Input(ID+"-store-dataset", "data"),
    prevent_initial_call=True,)
def update_graph(dataset):
    xx = np.array(dataset["freq"])
    sigmw_rise = podmr.dataset["sig_mw_rise"]
    sigmw_fall = podmr.dataset["sig_mw_fall"]
    sigmw_av = (sigmw_rise+sigmw_fall)/2

    signomw_rise = podmr.dataset["sig_nomw_rise"]
    signomw_fall = podmr.dataset["sig_nomw_fall"]
    signomw_av = (signomw_rise+signomw_fall)/2
    yy_mw = np.array(sigmw_av*1E3)
    yy_nomw = np.array(signomw_av*1E3)

    ymin = np.min([np.min(yy_nomw), np.min(yy_mw)])
    ymax = np.max([np.max(yy_nomw), np.max(yy_mw)])
    yran = 0.05*abs(ymax-ymin)

    data_mw = go.Scattergl(x = xx, y=yy_mw, name='with MW', mode='lines+markers')
    data_nomw = go.Scattergl(x = xx, y=yy_nomw, name='w/o MW', mode='lines+markers')
    return {'data':[data_nomw, data_mw], 
        'layout':go.Layout(
            xaxis = dict(range=[min(xx), max(xx)]), 
            yaxis = dict(range=[ymin-yran, ymax+yran], tickformat=",.3s"), 
            xaxis_title="Frequency [GHz]",
            yaxis_title="Signal [mV]",
            template=PLOT_THEME, 
            font=dict(size=21)
            )
        }
# -----------------------------------------------------------------------------------------------


# end=============================================================================================================
# ============================================================================================================


if __name__ == "__main__":
    
    from dash_bootstrap_components import themes
    APP_THEME = themes.JOURNAL
    # APP_THEME = themes.SKETCHY
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
    app.layout = layout_pODMR
    app.run_server(
        # host="0.0.0.0", 
        debug=DEBUG, 
        port=GUI_PORT)