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
from gui.config_custom import APP_THEME, PLOT_THEME

load_figure_template([PLOT_THEME])
import atexit

from measurement.dumdummeasurement import DummyODMR
from measurement.task_base import JobManager

dumdumodmr = DummyODMR()
jm = JobManager()


def release_lock():
    return jm.stop()


atexit.register(release_lock)


# ==============================================================================================================================
# ===============================================================================================================================

# specific gui components=============================================================================================================
# begin===========================================================================================================

DATA_INTERVAL = 100
IDLE_INTERVAL = 1000
MAX_INTERVAL = 2147483647
ID = dumdumodmr.get_uiid()

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
                dbc.Row(
                    [
                        NumericInput(
                            "B Field",
                            min=-1000.0,
                            max=1000.0,
                            step=1e-3,
                            value=5.0,
                            unit="G",
                            id=ID + "-input-bfield",
                            persistence_type="local",
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        NumericInput(
                            "MW Power",
                            min=0.0,
                            max=1000.0,
                            step=1e-3,
                            value=5.0,
                            unit="%",
                            id=ID + "-input-mwpower",
                            persistence_type="local",
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        NumericInput(
                            "Freq Begin",
                            min=0.0,
                            max=10.0,
                            step="any",
                            value=2.0,
                            unit="GHz",
                            id=ID + "-input-freq_begin",
                            persistence_type="local",
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        NumericInput(
                            "Freq End",
                            min=0.0,
                            max=10.0,
                            step="any",
                            value=4.0,
                            unit="GHz",
                            id=ID + "-input-freq_end",
                            persistence_type="local",
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        NumericInput(
                            "Freq Step",
                            min=0.0,
                            max=1.0,
                            step="any",
                            value=0.01,
                            unit="GHz",
                            id=ID + "-input-freq_step",
                            persistence_type="local",
                        ),
                    ]
                ),
            ]
        ),
    ]
)

layout_runinfo = dbc.Row(
    [
        dbc.Col(
            [
                dbc.Row(
                    [
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
    ]
)

layout_dummyODMR = html.Div(
    [
        dbc.Row([dbc.Col([layout_para], width=4), dbc.Col([layout_graph], width=8)]),
        dbc.Col(
            [
                # layout_graph_info,
                layout_hidden
            ]
        ),
    ]
)
# end=============================================================================================================
# ============================================================================================================


# handling callback events===========================================================================================
# begin=============================================================================================================


# apply experiment parameters------------------------------------------------------------------------------------------
@callback(
    Output(ID + "auxillary", "data"),
    Input(ID + "-input-mwpower", "value"),
    Input(ID + "-input-bfield", "value"),
    Input(ID + "-input-freq_begin", "value"),
    Input(ID + "-input-freq_end", "value"),
    Input(ID + "-input-freq_step", "value"),
    Input(ID + "-input-stoptime", "value"),
    prevent_initial_call=False,
)
def update_params(mwpower, bfield, freq_begin, freq_end, freq_step, stoptime):
    paramsdict = dict(
        mw_power=mwpower,
        bfield=bfield,
        freq_begin=freq_begin,
        freq_end=freq_end,
        freq_step=freq_step,
    )
    dumdumodmr.set_paraset(**paramsdict)
    dumdumodmr.set_stoptime(stoptime)
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
        if dumdumodmr.state == "run":
            return DATA_INTERVAL
        else:
            return IDLE_INTERVAL


def _run_exp():
    jm.start()
    jm.submit(dumdumodmr)
    # return False, True, True, DATA_INTERVAL
    return DATA_INTERVAL


def _pause_exp():
    dumdumodmr.pause()
    # return True, False, True, MAX_INTERVAL
    return IDLE_INTERVAL


def _stop_exp():
    dumdumodmr.stop()
    # return True, False, False, MAX_INTERVAL
    return IDLE_INTERVAL


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
        stateset=dumdumodmr.stateset,
        paraset=dumdumodmr.paraset,
        dataset=dumdumodmr.dataset,
    )
    return storedata["stateset"], storedata["paraset"], storedata["dataset"]


@callback(
    Output(ID + "-input-mwpower", "disabled"),
    Output(ID + "-input-bfield", "disabled"),
    Output(ID + "-input-freq_begin", "disabled"),
    Output(ID + "-input-freq_end", "disabled"),
    Output(ID + "-input-freq_step", "disabled"),
    Output(ID + "-input-stoptime", "disabled"),
    Input(ID + "-store-stateset", "data"),
    prevent_initial_call=False,
)
def disable_parameters(stateset):
    if stateset["state"] == "run":
        return [True] * 6
    elif stateset["state"] in ["idle", "wait", "done", "error"]:
        return [False] * 6


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


@callback(
    Output(ID + "-progressbar", "value"),
    Output(ID + "-progressbar", "label"),
    Input(ID + "-store-stateset", "data"),
)
def update_progress(stateset):
    progress_num = stateset["idx_run"] / stateset["num_run"]
    progress_time = stateset["time_run"] / stateset["time_stop"]
    progress = max(progress_num, progress_time)
    # print(f"progress = {progress}")
    return progress, f"{(100*progress):.0f}%"


@callback(
    Output(ID + "graph", "figure"),
    Input(ID + "-store-dataset", "data"),
    prevent_initial_call=True,
)
def update_graph(dataset):
    xx = np.array(dataset["freq"])
    yy = np.array(dataset["signal"]) * 1e3
    ymin = np.min(yy)
    ymax = np.max(yy)
    yran = 0.05 * abs(ymax - ymin)
    data = go.Scattergl(x=xx, y=yy, name="scatter", mode="lines+markers")
    return {
        "data": [data],
        "layout": go.Layout(
            xaxis=dict(range=[min(xx), max(xx)]),
            yaxis=dict(range=[ymin - yran, ymax + yran], tickformat=",.3s"),
            xaxis_title="Frequency [GHz]",
            yaxis_title="Signal [a.u.]",
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
    app.layout = layout_dummyODMR
    app.run_server(
        # host="0.0.0.0",
        debug=DEBUG,
        port=GUI_PORT,
    )
