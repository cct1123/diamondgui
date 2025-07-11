if __name__ == "__main__":
    import os
    import sys

    path_project = "\\".join(os.getcwd().split("\\")[:-3])
    print(path_project)
    # caution: path[0] is reserved for script path (or '' in REPL)
    sys.path.insert(1, path_project)


import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go
from dash import Input, Output, callback, callback_context, dcc, html
from dash_bootstrap_templates import load_figure_template

from gui.components import NumericInput
from gui.config import APP_THEME, PLOT_THEME

load_figure_template([PLOT_THEME])
import atexit

# # measurement logic ================================================================================================================
# # ===============================================================================================================================
from gui.task_config import JM, TASK_THZRTRACE


def release_lock():
    return JM.stop()


atexit.register(release_lock)


# ==============================================================================================================================
# ===============================================================================================================================

# specific gui components=============================================================================================================
# begin===========================================================================================================

DATA_INTERVAL = 100
MAX_INTERVAL = 2147483647
ID = TASK_THZRTRACE.get_uiid()

GRAPH_INIT = {"data": [], "layout": go.Layout(template=PLOT_THEME)}
L_DICT = {"µm": 1e3, "nm": 1.0}

layout_buttons = dbc.Row(
    [
        dbc.ButtonGroup(
            [
                dbc.Button(
                    "Start",
                    id=ID + "-button-start",
                    outline=True,
                    color="info",
                    active=False,
                    n_clicks=0,
                ),
                dbc.Button(
                    "Pause",
                    id=ID + "-button-pause",
                    outline=True,
                    color="secondary",
                    disabled=True,
                    n_clicks=0,
                ),
                dbc.Button(
                    "Stop",
                    id=ID + "-button-stop",
                    outline=True,
                    color="secondary",
                    disabled=True,
                    n_clicks=0,
                ),
            ]
        ),
    ]
)

layout_progressbar = dbc.Row(
    [
        dbc.Col(
            id=ID + "-div-progressbar",
            children=[
                dbc.Progress(
                    value=0,
                    min=0.0,
                    max=1.0,
                    id=ID + "-progressbar",
                    animated=True,
                    striped=True,
                    label="",
                    color="info",
                    className="mt-2 mb-2",
                ),
            ],
        ),
    ]
)

layout_exppara = dbc.Row(
    [
        dbc.Col(
            [
                NumericInput(
                    "MW Freq",
                    min=380.0,
                    max=410.0,
                    step="any",
                    value=395.0,
                    unit="GHz",
                    id=ID + "-input-mwfreq",
                    persistence_type="local",
                ),
                NumericInput(
                    "MW Power",
                    min=0.0,
                    max=5.0,
                    step=1e-3,
                    value=5.0,
                    unit="V",
                    id=ID + "-input-mwpower",
                    persistence_type="local",
                ),
                NumericInput(
                    "Pulse Rate",
                    min=1e3,
                    max=1e9,
                    step="any",
                    value=0.3124e6,
                    unit="Hz",
                    id=ID + "-input-pulse_rate",
                    persistence_type="local",
                ),
                NumericInput(
                    "Volt Max",
                    min=-10e3,
                    max=10e3,
                    step=0.1,
                    value=20.0,
                    unit="mV",
                    id=ID + "-input-daq_max_mv",
                    persistence_type="local",
                ),
                NumericInput(
                    "Volt Min",
                    min=-10e3,
                    max=10e3,
                    step=0.1,
                    value=-20.0,
                    unit="mV",
                    id=ID + "-input-daq_min_mv",
                    persistence_type="local",
                ),
                NumericInput(
                    "Sampling Rate",
                    min=1e3,
                    max=500e3,
                    step="any",
                    value=500e3,
                    unit="Hz",
                    id=ID + "-input-daq_srate",
                    persistence_type="local",
                ),
                NumericInput(
                    "Refresh Rate",
                    min=1.0,
                    max=1e3,
                    step=0.1,
                    value=20.0,
                    unit="Hz",
                    id=ID + "-input-refresh",
                    persistence_type="local",
                ),
                NumericInput(
                    "History Window",
                    min=0.0,
                    max=120000,
                    step=0.1,
                    value=5.0,
                    unit="s",
                    id=ID + "-input-window",
                    persistence_type="local",
                ),
            ]
        ),
    ]
)

layout_runinfo = dbc.Row(
    [
        dbc.Col(
            [
                dbc.InputGroup(
                    [
                        dbc.InputGroupText("Priority"),
                        dbc.Select(
                            id=ID + "-input-priority",
                            options=[
                                {"label": "Critical", "value": 100},
                                {"label": "High", "value": 6},
                                {"label": "Medium", "value": 4},
                                {"label": "Low", "value": 2},
                                {"label": "Background", "value": 0},
                            ],
                            value=2,
                            persistence=True,
                            persistence_type="local",
                        ),
                    ],
                    className="mb-2",
                ),
                NumericInput(
                    "Stop Time",
                    min=0.0,
                    max=86400,
                    step="any",
                    value=10,
                    unit="s",
                    id=ID + "-input-stoptime",
                    persistence_type="local",
                ),
            ]
        ),
    ]
)

layout_para = dbc.Col(
    [layout_buttons, layout_progressbar, layout_exppara, layout_runinfo]
)

layout_graph = dbc.Row(
    [
        dbc.Container(
            [
                dcc.Graph(
                    figure=GRAPH_INIT,
                    id=ID + "graph",
                    mathjax=True,
                    animate=False,
                    responsive="auto",
                    style={"aspectRatio": "1.2/1"},
                ),
            ],
            fluid=True,
        ),
    ]
)

layout_hidden = dbc.Row(
    [
        dcc.Interval(id=ID + "interval-data", interval=MAX_INTERVAL, n_intervals=0),
        # dcc.Store(id=ID+"-store-plot", storage_type='memory', data=plotdata),
        dcc.Store(id=ID + "-store-stateset", storage_type="memory", data={}),
        dcc.Store(id=ID + "-store-paraset", storage_type="memory", data={}),
        dcc.Store(id=ID + "-store-dataset", storage_type="memory", data={}),
        dcc.Store(id=ID + "auxillary", data={}),
        dcc.Store(id=ID + "auxillary-tasksetting", data={}),
    ]
)

layout_thzrt = dbc.Col(
    [
        dbc.Card(
            [
                dbc.CardHeader(html.H4("THz Reflection Trace", className="mb-0")),
                dbc.CardBody(
                    dbc.Row(
                        [
                            dbc.Col(layout_para, width=4),
                            dbc.Col(layout_graph, width=8),
                        ],
                        className="g-2",
                    )
                ),
            ]
        ),
        layout_hidden,
    ],
    className="mt-2 mb-2",
)

dash.register_page(
    __name__,
    path="/calibration/thzr_trace",
    name="THz Reflection",
)
layout = layout_thzrt
# end=============================================================================================================
# ============================================================================================================


# handling callback events===========================================================================================
# begin=============================================================================================================


# apply experiment parameters------------------------------------------------------------------------------------------
@callback(
    Output(ID + "auxillary", "data"),
    Input(ID + "-input-mwfreq", "value"),
    Input(ID + "-input-mwpower", "value"),
    Input(ID + "-input-pulse_rate", "value"),
    Input(ID + "-input-daq_max_mv", "value"),
    Input(ID + "-input-daq_min_mv", "value"),
    Input(ID + "-input-daq_srate", "value"),
    Input(ID + "-input-refresh", "value"),
    Input(ID + "-input-window", "value"),
    Input(ID + "-input-priority", "value"),
    Input(ID + "-input-stoptime", "value"),
    prevent_initial_call=False,
)
def update_params(
    mwfreq,
    mwpower,
    pulse_rate,
    daq_max_mv,
    daq_min_mv,
    daq_srate,
    refresh,
    window,
    priority,
    stoptime,
):
    paramsdict = dict(
        mwfreq=mwfreq,
        mwpower=mwpower,
        pulse_rate=pulse_rate,
        daq_max=daq_max_mv / 1e3,
        daq_min=daq_min_mv / 1e3,
        daq_srate=daq_srate,
        refresh=refresh,
        window=window,
    )
    TASK_THZRTRACE.set_paraset(**paramsdict)
    return {}


@callback(
    Output(ID + "auxillary-tasksetting", "data"),
    Input(ID + "-input-priority", "value"),
    Input(ID + "-input-stoptime", "value"),
    prevent_initial_call=False,
)
def update_tasksetting(priority, stoptime):
    TASK_THZRTRACE.set_priority(priority)
    TASK_THZRTRACE.set_stoptime(stoptime)
    return {}


# ---------------------------------------------------------------------------------------------


# handling button events---------------------------------------------------------------------------------
@callback(
    Output(ID + "interval-data", "interval"),
    Input(ID + "-button-start", "n_clicks"),
    Input(ID + "-button-pause", "n_clicks"),
    Input(ID + "-button-stop", "n_clicks"),
    prevent_initial_call=False,
)
def check_run_stop_exp(_r, _p, _s):
    ctx = callback_context
    if ctx.triggered_id == ID + "-button-start":
        return _run_exp()
    elif ctx.triggered_id == ID + "-button-pause":
        return _pause_exp()
    elif ctx.triggered_id == ID + "-button-stop":
        return _stop_exp()
    else:
        # initial call
        # print("hello from the button store initial call")
        if TASK_THZRTRACE.state == "run":
            return DATA_INTERVAL
        else:
            return MAX_INTERVAL


def _run_exp():
    JM.start()
    JM.submit(TASK_THZRTRACE)
    # return False, True, True, DATA_INTERVAL
    return DATA_INTERVAL


def _pause_exp():
    TASK_THZRTRACE.pause()
    # return True, False, True, MAX_INTERVAL
    return MAX_INTERVAL


def _stop_exp():
    TASK_THZRTRACE.stop()
    # return True, False, False, MAX_INTERVAL
    return MAX_INTERVAL


# -----------------------------------------------------------------------------------------------
# update data, status, graph--------------------------------------------------------------------------------
@callback(
    Output(ID + "-store-stateset", "data"),
    Output(ID + "-store-paraset", "data"),
    Output(ID + "-store-dataset", "data"),
    Input(ID + "interval-data", "n_intervals"),
    prevent_initial_call=False,
)
def update_state_parameters_data(_):
    storedata = dict()
    storedata = dict(
        stateset=TASK_THZRTRACE.stateset,
        paraset=TASK_THZRTRACE.paraset,
        dataset=TASK_THZRTRACE.dataset,
    )
    return storedata["stateset"], storedata["paraset"], storedata["dataset"]


@callback(
    Output(ID + "-input-mwfreq", "disabled"),
    Output(ID + "-input-mwpower", "disabled"),
    Output(ID + "-input-pulse_rate", "disabled"),
    Output(ID + "-input-daq_max_mv", "disabled"),
    Output(ID + "-input-daq_min_mv", "disabled"),
    Output(ID + "-input-daq_srate", "disabled"),
    Output(ID + "-input-refresh", "disabled"),
    Output(ID + "-input-window", "disabled"),
    Output(ID + "-input-priority", "disabled"),
    Output(ID + "-input-stoptime", "disabled"),
    Input(ID + "-store-stateset", "data"),
    prevent_initial_call=False,
)
def disable_parameters(stateset):
    if stateset["state"] == "run":
        return [True] * 10
    elif stateset["state"] in ["idle", "wait", "done", "error"]:
        return [False] * 10


@callback(
    Output(ID + "-button-start", "disabled"),
    Output(ID + "-button-pause", "disabled"),
    Output(ID + "-button-stop", "disabled"),
    Input(ID + "-store-stateset", "data"),
    prevent_initial_call=False,
)
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


# @callback(
#     Output(ID + "-label-state", "children"),
#     Output(ID + "-label-state", "color"),
#     Input(ID+"-store-stateset", "data"),
#     )
# def update_statelabel(stateset):
#     alertcolor = "secondary"
#     if stateset["state"] == "run":
#         alertcolor = "success"
#     elif stateset["state"] == "wait":
#         alertcolor = "warning"
#     elif stateset["state"] in ["idle", "done"]:
#         alertcolor = "secondary"
#     elif stateset["state"] == "error":
#         alertcolor = "danger"
#     return stateset["state"], alertcolor


@callback(
    Output(ID + "-progressbar", "value"),
    Output(ID + "-progressbar", "label"),
    Input(ID + "-store-stateset", "data"),
)
def update_progress(stateset):
    progress_num = stateset["idx_run"] / stateset["num_run"]
    progress_time = stateset["time_run"] / stateset["time_stop"]
    progress = max(progress_num, progress_time)
    progress = min(progress, 1)
    # print(f"progress = {progress}")
    return progress, f"{(100 * progress):.0f}%"


@callback(
    Output(ID + "graph", "figure"),
    Input(ID + "-store-dataset", "data"),
    prevent_initial_call=True,
)
def update_graph(dataset):
    xx = np.array(dataset["zbd_time"])
    # print(dataset["zbd_amp"])
    yy = np.array(dataset["zbd_amp"]) * 1e3
    ymin = np.min(yy)
    ymax = np.max(yy)
    yran = 0.05 * abs(ymax - ymin)
    data = go.Scattergl(x=xx, y=yy, name="scatter", mode="lines+markers")
    return {
        "data": [data],
        "layout": go.Layout(
            xaxis=dict(range=[min(xx), max(xx)]),
            yaxis=dict(range=[ymin - yran, ymax + yran], tickformat=",.3s"),
            xaxis_title="time [s]",
            yaxis_title="Voltage [mV]",
            template=PLOT_THEME,
            font=dict(size=21),
        ),
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
        external_scripts=[],
    )
    app.layout = layout_thzrt
    app.run_server(
        # host="0.0.0.0",
        debug=DEBUG,
        port=GUI_PORT,
    )
