if __name__ == "__main__":
    import os
    import sys

    path_project = "\\".join(os.getcwd().split("\\")[:-3])
    print(path_project)
    # caution: path[0] is reserved for script path (or '' in REPL)
    sys.path.insert(1, path_project)

import dash
import dash_bootstrap_components as dbc
import dash_daq as daq
import numpy as np
import plotly.graph_objs as go
from dash import Input, Output, State, callback, callback_context, dcc, html
from dash_bootstrap_templates import load_figure_template

from analysis.fitting import (
    BOUNDS_SINE_GAUSSIAN_DECAY,
    CurveFitting,
    estimator_sine_gassian_decay,
    format_param,
    model_sine_gaussian_decay,
)
from gui.components import NumericInput
from gui.config_custom import APP_THEME, PLOT_THEME
from gui.task_config import JM, TASK_RABI

load_figure_template([PLOT_THEME, PLOT_THEME + "_dark"])


class RabiCurveFitting(CurveFitting):
    def __init__(self, *args, **kwargs):
        super().__init__(
            TASK_RABI,
            model_sine_gaussian_decay,
            estimator_sine_gassian_decay,
            bounds=BOUNDS_SINE_GAUSSIAN_DECAY,
            *args,
            **kwargs,
        )

    def data_stream(self):
        dataset = self.stream.dataset
        xx = dataset["mw_dur"]
        yy = (dataset["sig_mw"] - dataset["sig_nomw"]) / dataset["sig_nomw"] * 100
        return xx, yy


curvefitting = RabiCurveFitting()
mw_dur = np.linspace(0, 3500, 100)
TASK_RABI.dataset["mw_dur"] = mw_dur

TASK_RABI.dataset["sig_nomw"] = np.ones(100)
TASK_RABI.dataset["sig_mw"] = (
    model_sine_gaussian_decay(
        mw_dur,
        *[
            7.31220714e-04,
            5.88768238e-04,
            2.47215447e00,
            1.54081029e03,
            1.02436466e-03,
            7.19224733e02,
            -1.47814081e-03,
        ],
    )
    + np.random.randn(len(mw_dur)) * 1e-04
)
# ==============================================================================================================================
# ===============================================================================================================================

# specific gui components=============================================================================================================
# begin===========================================================================================================

DATA_INTERVAL = 100
STATE_INTERVAL = 100
MAX_INTERVAL = 2147483647
IDLE_INTERVAL = 500
ID = TASK_RABI.get_uiid()

GRAPH_INIT = {"data": [], "layout": go.Layout(template=PLOT_THEME + "_dark")}
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
            dbc.Badge(
                "idle",
                color="light",
                # text_color="primary",
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
            # width=12,
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
        NumericInput(
            "Stop Time",
            min=0.0,
            max=86400,
            step=1,
            value=10,
            unit="s",
            id=ID + "-input-stoptime",
            persistence_type="local",
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Checkbox(
                            id=ID + "-input-movingaverage",
                            label="Moving Average",
                            value=False,
                            persistence_type="local",
                            className="ml-2",
                        )
                    ],
                    width="auto",
                    className="ml-2",
                ),
                dbc.Col(
                    [
                        dcc.RangeSlider(
                            id=ID + "-input-movingfactor",
                            min=0,
                            max=1,
                            value=[0.5],
                            persistence_type="local",
                            disabled=True,
                        ),
                    ],
                ),
            ]
        ),
        dbc.Col(
            [
                dbc.Checklist(
                    id=ID + "-fit-toggle",
                    options=[{"label": "Enable Curve Fitting", "value": "fit"}],
                    value=[],  # The checkbox is unchecked by default
                ),
                html.Div(
                    daq.LEDDisplay(
                        id=ID + "-fit-frequency-led-display",
                        value="0.0",
                        label="Ω [MHz]",
                        labelPosition="bottom",
                        size=30,
                        # color="info",
                        className="dbc",
                        style={"margin": "auto"},
                    ),
                    className="dbc",
                ),
                html.Div(
                    id=ID + "-fit-parameters-display", style={"whiteSpace": "pre-line"}
                ),
            ]
        ),
    ],
    className="mt-2 mb-2",
)

tab_exppara_hardware = dbc.Col(
    [
        NumericInput(
            "Laser Current",
            min=0.0,
            max=100.0,
            step=0.01,
            value=70.26,
            unit="%",
            id=ID + "-input-laser_current",
            persistence_type="local",
        ),
        NumericInput(
            "MW Frequency",
            min=96.0,
            max=480.0,
            step="any",
            value=398.548,
            unit="GHz",
            id=ID + "-input-mw_freq",
            persistence_type="local",
        ),
        NumericInput(
            "MW Power",
            min=0.0,
            max=5.0,
            step="any",
            value=5.0,
            unit="V",
            id=ID + "-input-mw_powervolt",
            persistence_type="local",
        ),
        NumericInput(
            "MW Phase",
            min=0.0,
            max=5.0,
            step="any",
            value=0.0,
            unit="V",
            id=ID + "-input-mw_phasevolt",
            persistence_type="local",
        ),
        NumericInput(
            "Min Volt",
            min=-10.0e3,
            max=10.0e3,
            step="any",
            value=-5,
            unit="mV",
            id=ID + "-input-min_volt",
            persistence_type="local",
        ),
        NumericInput(
            "Max Volt",
            min=-10.0e3,
            max=10.0e3,
            step="any",
            value=10,
            unit="mV",
            id=ID + "-input-max_volt",
            persistence_type="local",
        ),
    ],
    className="mt-2 mb-2",
)

tab_exppara_sequence = dbc.Col(
    [
        NumericInput(
            "Init Laser",
            min=0.0,
            max=10e3,
            step=1.0,
            value=40.0,
            unit="ns",
            id=ID + "-input-init_nslaser",
            persistence_type="local",
        ),
        NumericInput(
            "Init ISC",
            min=0.0,
            max=10e3,
            step=1.0,
            value=150,
            unit="ns",
            id=ID + "-input-init_isc",
            persistence_type="local",
        ),
        NumericInput(
            "Init Repeat",
            min=0.0,
            max=10e3,
            step=1.0,
            value=40,
            unit="",
            id=ID + "-input-init_repeat",
            persistence_type="local",
        ),
        NumericInput(
            "Init Wait",
            min=0.0,
            max=10e3,
            step=1.0,
            value=1001.0,
            unit="ns",
            id=ID + "-input-init_wait",
            persistence_type="local",
        ),
        NumericInput(
            "Read Wait",
            min=0.0,
            max=1e3,
            step=1.0,
            value=300.0,
            unit="ns",
            id=ID + "-input-read_wait",
            persistence_type="local",
        ),
        NumericInput(
            "Read Laser",
            min=0.0,
            max=100e3,
            step=1.0,
            value=1201.0,
            unit="ns",
            id=ID + "-input-read_laser",
            persistence_type="local",
        ),
        NumericInput(
            "MW Duration Begin",
            min=0.0,
            max=1000e3,
            step=1.0,
            value=10.0,
            unit="ns",
            id=ID + "-input-mw_dur_begin",
            persistence_type="local",
        ),
        NumericInput(
            "MW Duration End",
            min=0.0,
            max=50e6,
            step=1.0,
            value=3500.0,
            unit="ns",
            id=ID + "-input-mw_dur_end",
            persistence_type="local",
        ),
        NumericInput(
            "MW Duration Step",
            min=0.0,
            max=1e6,
            step=1.0,
            value=50.0,
            unit="ns",
            id=ID + "-input-mw_dur_step",
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
                        dbc.Tab(tab_exppara_sequence, label="Sequence"),
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
        dcc.Interval(id=ID + "-interval-fit", interval=MAX_INTERVAL, n_intervals=0),
        dcc.Interval(id=ID + "-interval-state", interval=MAX_INTERVAL, n_intervals=0),
        # dcc.Store(id=ID+"-store-plot", storage_type='memory', data=plotdata),
        dcc.Store(id=ID + "-store-stateset", storage_type="memory", data={}),
        dcc.Store(id=ID + "-store-paraset", storage_type="memory", data={}),
        dcc.Store(id=ID + "-store-dataset", storage_type="memory", data={}),
        dcc.Store(
            id=ID + "-store-fitset",
            storage_type="session",
            data={
                "params": None,
                "uncert": None,
            },
        ),
        dcc.Store(id=ID + "auxillary", data={}),
    ]
)

layout_rabi = dbc.Col(
    [
        dbc.Card(
            [
                dbc.CardHeader([html.H4("Rabi", className="mt-0 mb-0")]),
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
    path="/sensor/rabi",
    name="Rabi",
)
layout = layout_rabi
# end=============================================================================================================
# ============================================================================================================


# handling callback events===========================================================================================
# begin=============================================================================================================


# apply experiment parameters------------------------------------------------------------------------------------------
@callback(
    Output(ID + "auxillary", "data"),
    Input(ID + "-input-priority", "value"),
    Input(ID + "-input-stoptime", "value"),
    Input(ID + "-input-laser_current", "value"),
    Input(ID + "-input-mw_freq", "value"),
    Input(ID + "-input-mw_powervolt", "value"),
    Input(ID + "-input-mw_phasevolt", "value"),
    Input(ID + "-input-min_volt", "value"),
    Input(ID + "-input-max_volt", "value"),
    Input(ID + "-input-init_nslaser", "value"),
    Input(ID + "-input-init_isc", "value"),
    Input(ID + "-input-init_repeat", "value"),
    Input(ID + "-input-init_wait", "value"),
    Input(ID + "-input-read_wait", "value"),
    Input(ID + "-input-read_laser", "value"),
    Input(ID + "-input-mw_dur_begin", "value"),
    Input(ID + "-input-mw_dur_end", "value"),
    Input(ID + "-input-mw_dur_step", "value"),
    Input(ID + "-input-movingaverage", "value"),
    Input(ID + "-input-movingfactor", "value"),
    prevent_initial_call=False,
)
def update_params(
    priority,
    stoptime,
    laser_current,
    mw_freq,
    mw_powervolt,
    mw_phasevolt,
    min_volt,
    max_volt,
    init_nslaser,
    init_isc,
    init_repeat,
    init_wait,
    read_wait,
    read_laser,
    mw_dur_begin,
    mw_dur_end,
    mw_dur_step,
    moving_aveg,
    moving_factor,
):
    paramsdict = dict(
        laser_current=laser_current,  # percentage
        mw_freq=mw_freq,  # GHz
        mw_powervolt=mw_powervolt,  # voltage 0.0 to 5.0
        mw_phasevolt=mw_phasevolt,  # voltage 0.0 to 5.0
        min_volt=min_volt / 1e3,  # [V]
        max_volt=max_volt / 1e3,  # [V]
        init_nslaser=init_nslaser,  # [ns]
        init_isc=init_isc,  # [ns]
        init_repeat=init_repeat,  # []
        init_wait=init_wait,  # [ns]
        read_wait=read_wait,  # [ns]
        read_laser=read_laser,  # [ns]
        mw_dur_begin=mw_dur_begin,  # [ns]
        mw_dur_end=mw_dur_end,  # [ns]
        mw_dur_step=mw_dur_step,  # [ns]
        moving_aveg=moving_aveg,
        moving_factor=float(moving_factor[-1]),
    )
    TASK_RABI.set_paraset(**paramsdict)
    TASK_RABI.set_priority(int(priority))
    TASK_RABI.set_stoptime(stoptime)
    return {}


# ---------------------------------------------------------------------------------------------


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
        # initial call
        # print("hello from the button store initial call")
        if TASK_RABI.state == "run":
            return DATA_INTERVAL, STATE_INTERVAL
        else:
            return MAX_INTERVAL, IDLE_INTERVAL


def _run_exp():
    JM.start()
    JM.submit(TASK_RABI)
    # return False, True, True, DATA_INTERVAL
    return DATA_INTERVAL, STATE_INTERVAL


def _pause_exp():
    TASK_RABI.pause()
    # return True, False, True, MAX_INTERVAL
    return MAX_INTERVAL, IDLE_INTERVAL


def _stop_exp():
    JM.start()
    JM.remove(TASK_RABI)
    # return True, False, False, MAX_INTERVAL
    return MAX_INTERVAL, IDLE_INTERVAL


# -----------------------------------------------------------------------------------------------


# update data, status, graph--------------------------------------------------------------------------------
@callback(
    Output(ID + "-store-stateset", "data"),
    Input(ID + "-interval-state", "n_intervals"),
    prevent_initial_call=False,
)
def update_store_state(_):
    return TASK_RABI.stateset


@callback(
    Output(ID + "-store-paraset", "data"),
    Output(ID + "-store-dataset", "data"),
    Input(ID + "-interval-data", "n_intervals"),
    prevent_initial_call=False,
)
def update_store_parameters_data(_):
    return TASK_RABI.paraset, TASK_RABI.dataset


# Callback to update the fitted parameters and their uncertainties display
@callback(
    Output(ID + "-fit-parameters-display", "children"),
    Output(ID + "-fit-frequency-led-display", "value"),
    [
        Input(ID + "-store-fitset", "data"),
        Input(ID + "-fit-toggle", "value"),
    ],  # Listen for checkbox value
)
def update_fit_parameters(data, fit_enabled):
    # Only show parameters when fitting is enabled (checkbox is checked)
    if data["params"] and "fit" in fit_enabled:
        params = data["params"]
        uncert = data["uncert"]

        A = format_param(params[0], uncert[0])  # %
        freq = format_param(params[1] * 1e3, uncert[1] * 1e3)
        phi = format_param(params[2], uncert[2])
        tau = format_param(params[3], uncert[3])
        B = format_param(params[4], uncert[4])
        tau_b = format_param(params[5], uncert[5])
        C = format_param(params[6], uncert[6])
        dA = format_param(uncert[0], uncert[0])
        df = format_param(uncert[1] * 1e3, uncert[1] * 1e3)
        dphi = format_param(uncert[2], uncert[2])
        dtau = format_param(uncert[3], uncert[3])
        dB = format_param(uncert[4], uncert[4])
        dtau_b = format_param(uncert[5], uncert[5])
        dC = format_param(uncert[6], uncert[6])
        # Format fitted parameters and their uncertainties into a readable string
        param_str = (
            f"Amplitude (A): {A} ± {dA} %\n"
            f"Frequency (f): {freq} ± {df} MHz\n"
            f"Phase (phi): {phi} ± {dphi} rad\n"
            f"Decay (tau): {tau} ± {dtau} ns\n"
            f"Background (B): {B} ± {dB} %\n"
            f"Background Decay (tau_b): {tau_b} ± {dtau_b} ns\n"
            f"Offset (C): {C} ± {dC} %"
        )
        return f"Fitted Parameters:\n{param_str}", freq

    # If checkbox is not checked or no fit data is available, return nothing
    return "", "0.0"


@callback(
    Output(ID + "-interval-fit", "interval"),
    Input(ID + "-fit-toggle", "value"),
)
def update_interval_fit(fit_enabled):
    if "fit" in fit_enabled:
        if not curvefitting.is_running():
            curvefitting.start()
        return DATA_INTERVAL
    else:
        if curvefitting.is_running():
            curvefitting.stop()
        return MAX_INTERVAL


@callback(
    Output(ID + "-store-fitset", "data"),
    Input(ID + "-interval-fit", "n_intervals"),
    State(ID + "-fit-toggle", "value"),
    prevent_initial_call=True,
)
def update_store_fit(n_intervals, fit_enabled):
    fit_result = None
    if "fit" in fit_enabled:
        fit_result = curvefitting.get_last()

    if fit_result:
        return {
            "params": fit_result["params"],
            "uncert": fit_result["uncert"],
        }
    else:
        return {
            "params": None,
            "uncert": None,
        }


@callback(
    Output(ID + "-input-priority", "disabled"),
    Output(ID + "-input-stoptime", "disabled"),
    Output(ID + "-input-laser_current", "disabled"),
    Output(ID + "-input-mw_freq", "disabled"),
    Output(ID + "-input-mw_powervolt", "disabled"),
    Output(ID + "-input-mw_phasevolt", "disabled"),
    Output(ID + "-input-min_volt", "disabled"),
    Output(ID + "-input-max_volt", "disabled"),
    Output(ID + "-input-init_nslaser", "disabled"),
    Output(ID + "-input-init_isc", "disabled"),
    Output(ID + "-input-init_repeat", "disabled"),
    Output(ID + "-input-init_wait", "disabled"),
    Output(ID + "-input-read_wait", "disabled"),
    Output(ID + "-input-read_laser", "disabled"),
    Output(ID + "-input-mw_dur_begin", "disabled"),
    Output(ID + "-input-mw_dur_end", "disabled"),
    Output(ID + "-input-mw_dur_step", "disabled"),
    Output(ID + "-input-movingaverage", "disabled"),
    Output(ID + "-input-movingfactor", "disabled"),
    Input(ID + "-store-stateset", "data"),
    Input(ID + "-input-movingaverage", "value"),
    prevent_initial_call=False,
)
def disable_parameters(stateset, mavg):
    if stateset["state"] == "run":
        return [True] * 19
    elif stateset["state"] in ["idle", "wait", "done", "error"]:
        if not mavg:
            return [False] * 18 + [True]
        else:
            return [False] * 19


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
    progress_num = stateset["idx_run"] / stateset["num_run"]
    progress_time = stateset["time_run"] / stateset["time_stop"]
    progress = max(progress_num, progress_time)
    progress = min(progress, 1)
    # print(f"progress = {progress}")
    return progress, f"{(100*progress):.0f}%"


@callback(
    Output(ID + "graph", "figure"),
    Input("dark-light-switch", "value"),
    Input(ID + "-store-dataset", "data"),
    Input(ID + "-store-fitset", "data"),
    Input(ID + "-fit-toggle", "value"),
    prevent_initial_call=True,
)
def update_graph(switch_on, dataset, fitset, fit_enabled):
    template = PLOT_THEME if switch_on else PLOT_THEME + "_dark"
    xx = np.array(dataset["mw_dur"])

    sigmw_av = TASK_RABI.dataset["sig_mw"]
    signomw_av = TASK_RABI.dataset["sig_nomw"]
    yy_mw = sigmw_av * 1e3
    yy_nomw = signomw_av * 1e3
    yy_contrast = (yy_mw - yy_nomw) / yy_nomw * 100

    ymin = np.min([np.min(yy_nomw), np.min(yy_mw)])
    ymax = np.max([np.max(yy_nomw), np.max(yy_mw)])
    yran = 0.05 * abs(ymax - ymin)

    ymin_c = np.min(yy_contrast)
    ymax_c = np.max(yy_contrast)
    yran_c = 0.05 * abs(ymax_c - ymin_c)
    data_nomw = go.Scattergl(x=xx, y=yy_nomw, name="w/o MW", mode="lines+markers")
    data_mw = go.Scattergl(x=xx, y=yy_mw, name="with MW", mode="lines+markers")
    data_contrast = go.Scattergl(
        x=xx, y=yy_contrast, mode="lines+markers", name="Contrast", yaxis="y2"
    )
    fit_contrast_list = []
    if "fit" in fit_enabled and fitset["params"]:
        xx_fit_contrast = np.linspace(min(xx), max(xx), len(xx) * 4)
        yy_fit_contrast = curvefitting.model(xx_fit_contrast, *fitset["params"])
        fit_contrast_list = [
            go.Scattergl(
                x=xx_fit_contrast,
                y=yy_fit_contrast,
                mode="lines",
                name="Constrast Fit",
                yaxis="y2",
            )
        ]

    return {
        "data": [data_nomw, data_mw, data_contrast] + fit_contrast_list,
        "layout": go.Layout(
            xaxis=dict(range=[min(xx), max(xx)]),
            yaxis=dict(range=[ymin - yran, ymax + yran], tickformat=",.3s"),
            yaxis2=dict(
                range=[ymin_c - yran_c, ymax_c + yran_c],
                title="Contrast [%]",
                overlaying="y",
                side="right",
                showgrid=False,
            ),
            xaxis_title="MW time [ns]",
            yaxis_title="PL [mV]",
            template=template,
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
    app.layout = layout_rabi
    app.run_server(
        # host="0.0.0.0",
        debug=DEBUG,
        port=GUI_PORT,
    )