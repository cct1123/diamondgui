if __name__ == "__main__":
    import os
    import sys

    path_project = "\\".join(os.getcwd().split("\\")[:-3])
    print(path_project)
    # caution: path[0] is reserved for script path (or '' in REPL)
    sys.path.insert(1, path_project)

import logging

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash import Input, Output, callback, callback_context, dcc, html
from dash_bootstrap_templates import load_figure_template

logger = logging.getLogger(__name__)
from gui.components import (
    NumericInput,  # Add any other needed components
    SelectInput,
)
from gui.config import APP_THEME, PLOT_THEME
from gui.task_config import JM, TASK_PL_TRACE

load_figure_template([PLOT_THEME, PLOT_THEME + "_dark"])

# ==============================================================================================================================
# ===============================================================================================================================

# specific gui components=============================================================================================================
# begin===========================================================================================================

DATA_INTERVAL = 100
STATE_INTERVAL = 100
MAX_INTERVAL = 2147483647
IDLE_INTERVAL = 500
ID = TASK_PL_TRACE.get_uiid()

GRAPH_INIT = {"data": [], "layout": go.Layout(template=PLOT_THEME + "_dark")}

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
            dbc.Badge(
                "idle",
                color="light",
                className="mt-2 mb-2",
                id=ID + "-badge-status",
            ),
            width="auto",
        ),
        dbc.Col(
            [
                dbc.Progress(
                    value=0,
                    min=0.0,
                    max=1.0,
                    id=ID + "-progressbar",
                    animated=True,
                    striped=True,
                    label="",
                    color="info",
                    style={"width": "100%"},
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
            },
        ),
    ]
)

tab_exppara_task = dbc.Col(
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
                    value=6,
                    persistence=True,
                    persistence_type="local",
                ),
            ],
            className="mb-2",
        ),
        # NumericInput(
        #     "Run Time",
        #     min=1,
        #     max=86400,
        #     step=1,
        #     value=3600,
        #     unit="s",
        #     id=ID + "-input-runtime",
        #     persistence_type="local",
        # ),
        # SliderInput(
        #     name="Window Size",
        #     min=1,
        #     max=60,
        #     step=1,
        #     value=20,
        #     unit="s",
        #     id=ID + "-input-window_size",
        #     marks={ii: "{}".format(ii) for ii in range(0, 61, 10)},
        #     persistence_type="local",
        #     class_name="mb-2",
        # ),
        # SliderInput(
        #     name="Scale Window",
        #     min=1,
        #     max=20,
        #     step=1,
        #     value=5,
        #     unit="s",
        #     id=ID + "-input-scale_window",
        #     marks={ii: "{}".format(ii) for ii in range(0, 21, 5)},
        #     persistence_type="local",
        #     class_name="mb-2",
        # ),
    ],
    className="mt-2 mb-2",
)

tab_exppara_hardware = dbc.Col(
    [
        NumericInput(
            "Laser Current",
            min=0.0,
            max=100.0,
            step=0.1,
            value=80.0,
            unit="%",
            id=ID + "-input-laser_current",
            persistence_type="local",
        ),
        SelectInput(
            "Signal Amp",
            options=[200, 500, 1000, 2000, 5000, 10000],
            value=1000,
            unit="mV",
            id=ID + "-input-amp_input",
            persistence_type="local",
        ),
        NumericInput(
            "Segment Size",
            min=256,
            max=65536,
            step=256,
            value=8192,
            unit="samples",
            id=ID + "-input-segment_size",
            persistence_type="local",
        ),
        NumericInput(
            "Pre-trigger Size",
            min=16,
            max=4096,
            step=16,
            value=256,
            unit="samples",
            id=ID + "-input-pre_trig_size",
            persistence_type="local",
        ),
        NumericInput(
            "Number of Segments",
            min=1,
            max=1024,
            step=1,
            value=64,
            unit="",
            id=ID + "-input-num_segment",
            persistence_type="local",
        ),
        NumericInput(
            "Sampling Rate",
            min=1e6,
            max=100e6,
            step=1e6,
            value=10e6,
            unit="Hz",
            id=ID + "-input-sampling_rate",
            persistence_type="local",
        ),
    ],
    className="mt-2 mb-2",
)

layout_exppara = dbc.Row(
    [
        dbc.Col(
            [
                dbc.Tabs(
                    [
                        dbc.Tab(tab_exppara_task, label="Task"),
                        dbc.Tab(tab_exppara_hardware, label="Hardware"),
                    ]
                )
            ]
        )
    ]
)

layout_para = dbc.Col([layout_buttons, layout_progressbar, layout_exppara])

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
        dcc.Interval(id=ID + "-interval-data", interval=MAX_INTERVAL, n_intervals=0),
        dcc.Interval(id=ID + "-interval-state", interval=MAX_INTERVAL, n_intervals=0),
        dcc.Store(id=ID + "-store-stateset", storage_type="memory", data={}),
        dcc.Store(id=ID + "-store-paraset", storage_type="memory", data={}),
        dcc.Store(id=ID + "-store-dataset", storage_type="memory", data={}),
        dcc.Store(id=ID + "auxillary", data={}),
    ]
)

layout_pl_trace = dbc.Col(
    [
        dbc.Card(
            [
                dbc.CardHeader([html.H4("PL Trace", className="mt-0 mb-0")]),
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col([layout_para], width=4),
                                dbc.Col([layout_graph], width=8),
                            ]
                        )
                    ]
                ),
            ]
        ),
        layout_hidden,
    ],
    className="mt-2 mb-2",
)

dash.register_page(
    __name__,
    path="/calibration/pl_trace",
    name="PL Trace",
)
layout = layout_pl_trace
# end=============================================================================================================
# ============================================================================================================


# handling callback events===========================================================================================
# begin=============================================================================================================


# apply experiment parameters------------------------------------------------------------------------------------------
@callback(
    Output(ID + "auxillary", "data"),
    Input(ID + "-input-priority", "value"),
    Input(ID + "-input-runtime", "value"),
    Input(ID + "-input-window_size", "value"),
    Input(ID + "-input-scale_window", "value"),
    Input(ID + "-input-laser_current", "value"),
    Input(ID + "-input-amp_input", "value"),
    Input(ID + "-input-segment_size", "value"),
    Input(ID + "-input-pre_trig_size", "value"),
    Input(ID + "-input-num_segment", "value"),
    Input(ID + "-input-sampling_rate", "value"),
    prevent_initial_call=False,
)
def update_params(
    priority,
    runtime,
    window_size,
    scale_window,
    laser_current,
    amp_input,
    segment_size,
    pre_trig_size,
    num_segment,
    sampling_rate,
):
    paramsdict = dict(
        laser_current=laser_current,
        amp_input=int(amp_input),
        segment_size=int(segment_size),
        pre_trig_size=int(pre_trig_size),
        num_segment=int(num_segment),
        sampling_rate=float(sampling_rate),
        window_size=float(window_size),
        scale_window=float(scale_window),
    )
    logger.debug(f"Update Parameters : {paramsdict}")
    TASK_PL_TRACE.set_paraset(**paramsdict)
    TASK_PL_TRACE.set_priority(int(priority))
    # TASK_PL_TRACE.set_stoptime(runtime)
    return {}


# handling button events---------------------------------------------------------------------------------
@callback(
    Output(ID + "-interval-data", "interval"),
    Output(ID + "-interval-state", "interval"),
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
        if TASK_PL_TRACE.state == "run":
            return DATA_INTERVAL, STATE_INTERVAL
        else:
            return MAX_INTERVAL, IDLE_INTERVAL


def _run_exp():
    JM.start()
    JM.submit(TASK_PL_TRACE)
    return DATA_INTERVAL, STATE_INTERVAL


def _pause_exp():
    TASK_PL_TRACE.pause()
    return MAX_INTERVAL, IDLE_INTERVAL


def _stop_exp():
    JM.start()
    JM.remove(TASK_PL_TRACE)
    return MAX_INTERVAL, IDLE_INTERVAL


# update data, status, graph--------------------------------------------------------------------------------
@callback(
    Output(ID + "-store-stateset", "data"),
    Input(ID + "-interval-state", "n_intervals"),
    prevent_initial_call=False,
)
def update_store_state(_):
    return TASK_PL_TRACE.stateset


@callback(
    Output(ID + "-store-paraset", "data"),
    Output(ID + "-store-dataset", "data"),
    Input(ID + "-interval-data", "n_intervals"),
    prevent_initial_call=False,
)
def update_store_parameters_data(_):
    # logger.info(f"Update Stateset: {TASK_PL_TRACE.stateset}")
    # logger.info(f"Update paraset: {TASK_PL_TRACE.paraset}")
    # logger.info(f"Update Data: {TASK_PL_TRACE.dataset}")
    return TASK_PL_TRACE.paraset, TASK_PL_TRACE.dataset


@callback(
    Output(ID + "-input-priority", "disabled"),
    # Output(ID + "-input-runtime", "disabled"),
    # Output(ID + "-input-window_size", "disabled"),
    # Output(ID + "-input-scale_window", "disabled"),
    Output(ID + "-input-laser_current", "disabled"),
    Output(ID + "-input-amp_input", "disabled"),
    Output(ID + "-input-segment_size", "disabled"),
    Output(ID + "-input-pre_trig_size", "disabled"),
    Output(ID + "-input-num_segment", "disabled"),
    Output(ID + "-input-sampling_rate", "disabled"),
    Input(ID + "-store-stateset", "data"),
    prevent_initial_call=False,
)
def disable_parameters(stateset):
    if stateset["state"] == "run":
        return [True] * 7
    elif stateset["state"] in ["idle", "wait", "done", "error"]:
        return [False] * 7


@callback(
    Output(ID + "-button-start", "disabled"),
    Output(ID + "-button-pause", "disabled"),
    Output(ID + "-button-stop", "disabled"),
    Input(ID + "-store-stateset", "data"),
    prevent_initial_call=False,
)
def disable_buttons(stateset):
    if stateset["state"] == "run":
        return True, False, False
    elif stateset["state"] in ["done", "wait"]:
        return False, True, False
    elif stateset["state"] == "idle":
        return False, True, True
    elif stateset["state"] == "error":
        return False, False, False


@callback(
    Output(ID + "-badge-status", "children"),
    Output(ID + "-badge-status", "color"),
    Input(ID + "-store-stateset", "data"),
)
def update_status(stateset):
    if stateset["state"] == "run":
        return "Run", "success"
    elif stateset["state"] == "wait":
        return "Wait", "warning"
    elif stateset["state"] in ["done"]:
        return "Done", "secondary"
    elif stateset["state"] == "error":
        return "Error", "danger"
    elif stateset["state"] == "idle":
        return "Idle", "light"


@callback(
    Output(ID + "-progressbar", "value"),
    Output(ID + "-progressbar", "label"),
    Input(ID + "-store-stateset", "data"),
)
def update_progress(stateset):
    progress = stateset["time_run"] / stateset["time_stop"]
    progress = min(progress, 1)
    return progress, f"{(100 * progress):.0f}%"


@callback(
    Output(ID + "graph", "figure"),
    Input("dark-light-switch", "value"),
    Input(ID + "-store-dataset", "data"),
    prevent_initial_call=True,
)
def update_graph(switch_on, dataset):
    template = PLOT_THEME if switch_on else PLOT_THEME + "_dark"

    if not dataset["x_data"] or not dataset["y_data"]:
        return {"data": [], "layout": go.Layout(template=template)}

    data_trace = go.Scattergl(
        x=dataset["x_data"],
        y=dataset["y_data"],
        mode="lines",
        name="PL Signal",
    )

    return {
        "data": [data_trace],
        "layout": go.Layout(
            xaxis_title="Time (s)",
            yaxis_title="PL Signal (mV)",
            template=template,
            font=dict(size=21),
            margin=dict(t=0),
        ),
    }


if __name__ == "__main__":
    from dash_bootstrap_components import themes

    APP_THEME = themes.JOURNAL
    DEBUG = True
    GUI_PORT = 9843
    app = dash.Dash(
        __name__,
        external_stylesheets=[APP_THEME],
        external_scripts=[],
    )
    app.layout = layout_pl_trace
    app.run_server(debug=DEBUG, port=GUI_PORT)
