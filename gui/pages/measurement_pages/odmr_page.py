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

from analysis.fitting import (  # estimator_lorentzian,; model_lorentzian,
    BOUNDS_GAUSSIAN,
    CurveFitting,
    estimator_gaussian,
    format_param,
    model_gaussian,
)
from gui.components import NumericInput, SelectInput, SliderInput
from gui.config import APP_THEME, PLOT_THEME
from gui.task_config import JM, TASK_ODMR

load_figure_template([PLOT_THEME, PLOT_THEME + "_dark"])


class ODMRCurveFitting(CurveFitting):
    def __init__(self, *args, **kwargs):
        super().__init__(
            TASK_ODMR,
            model_gaussian,
            estimator_gaussian,
            bounds=BOUNDS_GAUSSIAN,
            *args,
            **kwargs,
        )

    def data_stream(self):
        dataset = self.stream.dataset
        xx = dataset["freq"]
        signal = dataset["signal"]
        background = dataset["background"]

        # sigmw_rise = dataset["sig_mw_rise"]
        # sigmw_fall = dataset["sig_mw_fall"]
        # sigmw_av = (sigmw_rise + sigmw_fall) / 2
        # signomw_rise = dataset["sig_nomw_rise"]
        # signomw_fall = dataset["sig_nomw_fall"]
        # signomw_av = (signomw_rise + signomw_fall) / 2
        # yy_mw = sigmw_av * 1e3  # in mV
        # yy_nomw = signomw_av * 1e3  # in mV
        # yy_diff = yy_mw - yy_nomw
        return xx, (signal - background)


curvefitting = ODMRCurveFitting()

# # put fake data for testing--------------------
# freq = np.linspace(398.5, 398.6, 100)
# sig_diff = (
#     model_lorentzian(
#         freq, -1.15234127e-04, 3.98556462e02, 4.02208642e-03, 0.026600881e-04
#     )
#     + np.random.randn(len(freq)) * 1e-05
# )
# TASK_ODMR.dataset["freq"] = freq
# TASK_ODMR.dataset["sig_mw_rise"] = sig_diff
# TASK_ODMR.dataset["sig_mw_fall"] = sig_diff
# TASK_ODMR.dataset["sig_nomw_rise"] = np.ones(len(freq))
# TASK_ODMR.dataset["sig_nomw_fall"] = np.ones(len(freq))
# # -----------------------------------------

# ==============================================================================================================================
# ===============================================================================================================================

# specific gui components=============================================================================================================
# begin===========================================================================================================

DATA_INTERVAL = 100
STATE_INTERVAL = 100
MAX_INTERVAL = 2147483647
IDLE_INTERVAL = 500
ID = TASK_ODMR.get_uiid()

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
                className="border mt-2 mb-2",
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
        dbc.Row(
            [
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
                SliderInput(
                    name="Refresh",
                    min=2,
                    max=40,
                    step=2,
                    value=20,
                    unit="Hz",
                    id=ID + "-input-rate_refresh",
                    marks={ii: "{}".format(ii) for ii in range(0, 40, 10)},
                    persistence_type="local",
                    disabled=True,
                    class_name="mb-2",
                ),
            ]
        ),
        dbc.Col(
            [
                dbc.Checklist(
                    id=ID + "-fit-toggle",
                    options=[{"label": "Enable Curve Fitting", "value": "fit"}],
                    value=[],  # The checkbox is unchecked by default
                    # persistence_type="local",
                ),
                html.Div(
                    daq.LEDDisplay(
                        id=ID + "-fit-frequency-led-display",
                        value="0.0",
                        label="f [GHz]",
                        labelPosition="bottom",
                        size=30,
                        # color="info",
                        className="dbc",
                        style={"margin": "auto"},
                    ),
                    className="dbc",
                ),
                html.Div(
                    id=ID + "-fit-parameters-display",
                    style={"whiteSpace": "pre-line"},
                    className="dbc",
                ),
            ]
        ),
    ],
    className="mt-2 mb-2",
)

tab_exppara_hardware = dbc.Col(
    [
        NumericInput(
            "Freq Begin",
            min=96,
            max=480,
            step="any",
            value=398.5,
            unit="GHz",
            id=ID + "-input-freq_begin",
            persistence_type="local",
        ),
        NumericInput(
            "Freq End",
            min=96,
            max=480,
            step="any",
            value=398.6,
            unit="GHz",
            id=ID + "-input-freq_end",
            persistence_type="local",
        ),
        NumericInput(
            "Freq Step",
            min=0,
            max=10.0e3,
            step="any",
            value=5.0,
            unit="MHz",
            id=ID + "-input-freq_step",
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
            "Laser Current",
            min=0.0,
            max=100.0,
            step=0.01,
            value=81.26,
            unit="%",
            id=ID + "-input-laser_current",
            persistence_type="local",
        ),
        SelectInput(
            "Signal Amp",
            options=[200, 500, 1000, 2000, 5000, 10000],
            value=5000,
            unit="mV",
            id=ID + "-input-amp_input",
            persistence_type="local",
        ),
        NumericInput(
            "Bz Volt",
            min=-1.0,
            max=1.0,
            step="any",
            value=0,
            unit="V",
            id=ID + "-input-bz_bias_vol",
            persistence_type="local",
        ),
    ],
    className="mt-2 mb-2",
)

tab_exppara_sequence = dbc.Col(
    [
        dbc.Row(
            [
                NumericInput(
                    "Init Laser",
                    min=0.0,
                    max=10e3,
                    step=1.0,
                    value=4.0,
                    unit="ns",
                    id=ID + "-input-init_nslaser",
                    persistence_type="local",
                ),
            ]
        ),
        dbc.Row(
            [
                NumericInput(
                    "Init ISC",
                    min=0.0,
                    max=10e3,
                    step=1.0,
                    value=200,
                    unit="ns",
                    id=ID + "-input-init_isc",
                    persistence_type="local",
                ),
            ]
        ),
        dbc.Row(
            [
                NumericInput(
                    "Init Repeat",
                    min=0.0,
                    max=10e3,
                    step=1.0,
                    value=20,
                    unit="",
                    id=ID + "-input-init_repeat",
                    persistence_type="local",
                ),
            ]
        ),
        dbc.Row(
            [
                NumericInput(
                    "Init Wait",
                    min=0.0,
                    max=10e3,
                    step=1.0,
                    value=401.0,
                    unit="ns",
                    id=ID + "-input-init_wait",
                    persistence_type="local",
                ),
            ]
        ),
        dbc.Row(
            [
                NumericInput(
                    "MW Time",
                    min=0.0,
                    max=16e7,
                    step=1.0,
                    value=2000.0,
                    unit="ns",
                    id=ID + "-input-mw_time",
                    persistence_type="local",
                ),
            ]
        ),
        dbc.Row(
            [
                NumericInput(
                    "Read Wait",
                    min=0.0,
                    max=1e3,
                    step=1.0,
                    value=500.0,
                    unit="ns",
                    id=ID + "-input-read_wait",
                    persistence_type="local",
                ),
            ]
        ),
        dbc.Row(
            [
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
            ]
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
        dcc.Interval(id=ID + "interval-data", interval=MAX_INTERVAL, n_intervals=0),
        dcc.Interval(id=ID + "-interval-fit", interval=MAX_INTERVAL, n_intervals=0),
        dcc.Interval(id=ID + "interval-state", interval=MAX_INTERVAL, n_intervals=0),
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


layout_pODMR = dbc.Col(
    [
        dbc.Card(
            [
                dbc.CardHeader([html.H4("Pulsed ODMR", className="mt-0 mb-0")]),
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
    path="/sensor/podmr",
    name="pulsed ODMR",
)
layout = layout_pODMR

# end=============================================================================================================
# ============================================================================================================


# handling callback events===========================================================================================
# begin=============================================================================================================


# apply experiment parameters------------------------------------------------------------------------------------------
@callback(
    Output(ID + "auxillary", "data"),
    Input(ID + "-input-priority", "value"),
    Input(ID + "-input-stoptime", "value"),
    Input(ID + "-input-freq_begin", "value"),
    Input(ID + "-input-freq_end", "value"),
    Input(ID + "-input-freq_step", "value"),
    Input(ID + "-input-mw_powervolt", "value"),
    Input(ID + "-input-laser_current", "value"),
    Input(ID + "-input-amp_input", "value"),
    Input(ID + "-input-init_nslaser", "value"),
    Input(ID + "-input-init_isc", "value"),
    Input(ID + "-input-init_repeat", "value"),
    Input(ID + "-input-init_wait", "value"),
    Input(ID + "-input-mw_time", "value"),
    Input(ID + "-input-read_wait", "value"),
    Input(ID + "-input-read_laser", "value"),
    Input(ID + "-input-rate_refresh", "value"),
    Input(ID + "-input-bz_bias_vol", "value"),
    prevent_initial_call=False,
)
def update_params(
    priority,
    stoptime,
    freq_begin,
    freq_end,
    freq_step,
    mw_powervolt,
    laser_current,
    amp_input,
    init_nslaser,
    init_isc,
    init_repeat,
    init_wait,
    mw_time,
    read_wait,
    read_laser,
    rate_refresh,
    bz_bias_vol,
):
    paramsdict = dict(
        freq_start=freq_begin,  # [GHz]
        freq_stop=freq_end,  # [GHz]
        freq_step=freq_step / 1e3,  # [GHz]
        init_wait=init_wait,
        init_nslaser=init_nslaser,
        init_isc=init_isc,
        init_repeat=init_repeat,
        mw_time=mw_time,
        read_wait=read_wait,
        read_laser=read_laser,
        mw_powervolt=mw_powervolt,
        laser_current=laser_current,  # 0 to 100%
        amp_input=int(amp_input),  # [mV]
        rate_refresh=rate_refresh,
        bz_bias_vol=bz_bias_vol,
    )
    TASK_ODMR.set_paraset(**paramsdict)
    TASK_ODMR.set_priority(int(priority))
    TASK_ODMR.set_stoptime(stoptime)
    return {}


# ---------------------------------------------------------------------------------------------


# handling button events---------------------------------------------------------------------------------
@callback(
    Output(ID + "interval-data", "interval"),
    Output(ID + "interval-state", "interval"),
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
        if TASK_ODMR.state == "run":
            return DATA_INTERVAL, STATE_INTERVAL
        else:
            return MAX_INTERVAL, IDLE_INTERVAL


def _run_exp():
    # JM.start()
    JM.submit(TASK_ODMR)
    # return False, True, True, DATA_INTERVAL
    return DATA_INTERVAL, STATE_INTERVAL


def _pause_exp():
    TASK_ODMR.pause()
    # return True, False, True, MAX_INTERVAL
    return MAX_INTERVAL, IDLE_INTERVAL


def _stop_exp():
    # JM.start()
    JM.remove(TASK_ODMR)
    # return True, False, False, MAX_INTERVAL
    return MAX_INTERVAL, IDLE_INTERVAL


# -----------------------------------------------------------------------------------------------


# update data, status, graph--------------------------------------------------------------------------------
@callback(
    Output(ID + "-store-stateset", "data"),
    Input(ID + "interval-state", "n_intervals"),
    prevent_initial_call=False,
)
def update_store_state(_):
    return TASK_ODMR.stateset


@callback(
    Output(ID + "-store-paraset", "data"),
    Output(ID + "-store-dataset", "data"),
    Input(ID + "interval-data", "n_intervals"),
    prevent_initial_call=False,
)
def update_store_parameters_data(_):
    return TASK_ODMR.paraset, TASK_ODMR.dataset


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

        A = format_param(params[0], uncert[0])  # mV
        freq = format_param(params[1], uncert[1])  # GHz
        gamma = format_param(params[2] * 1e3, uncert[2] * 1e3)  # MHz
        C = format_param(params[3] * 1e3, uncert[3] * 1e3)  # uV

        dA = format_param(uncert[0], uncert[0])
        df = format_param(uncert[1], uncert[1])
        dgamma = format_param(uncert[2] * 1e3, uncert[2] * 1e3)
        dC = format_param(uncert[3] * 1e3, uncert[3] * 1e3)  # uV

        # Format fitted parameters and their uncertainties into a readable string
        param_str = (
            f"Amplitude (A): {A} ± {dA} mV\n"
            f"Frequency (f0): {freq} ± {df} GHz\n"
            f"Linewidth (HWHM): {gamma} ± {dgamma} MHz\n"
            f"Background (C): {C} ± {dC} uV\n"
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
    Output(ID + "-input-freq_begin", "disabled"),
    Output(ID + "-input-freq_end", "disabled"),
    Output(ID + "-input-freq_step", "disabled"),
    Output(ID + "-input-mw_powervolt", "disabled"),
    Output(ID + "-input-laser_current", "disabled"),
    Output(ID + "-input-amp_input", "disabled"),
    Output(ID + "-input-init_nslaser", "disabled"),
    Output(ID + "-input-init_isc", "disabled"),
    Output(ID + "-input-init_repeat", "disabled"),
    Output(ID + "-input-init_wait", "disabled"),
    Output(ID + "-input-mw_time", "disabled"),
    Output(ID + "-input-read_wait", "disabled"),
    Output(ID + "-input-read_laser", "disabled"),
    Output(ID + "-input-rate_refresh", "disabled"),
    Output(ID + "-input-bz_bias_vol", "disabled"),
    Input(ID + "-store-stateset", "data"),
    prevent_initial_call=False,
)
def disable_parameters(stateset):
    if stateset["state"] == "run":
        return [True] * 17
    elif stateset["state"] in ["idle", "wait", "done", "error"]:
        return [False] * 17


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
    Input("dark-light-switch", "value"),
    Input(ID + "-store-dataset", "data"),
    Input(ID + "-store-fitset", "data"),
    Input(ID + "-fit-toggle", "value"),
    prevent_initial_call=True,
)
def update_graph(switch_on, dataset, fitset, fit_enabled):
    template = PLOT_THEME if switch_on else PLOT_THEME + "_dark"
    xx = np.array(dataset["freq"])
    signal = np.array(dataset["signal"]) * 1e3  # in mV
    background = np.array(dataset["background"]) * 1e3  # in mV

    data_signal = go.Scattergl(
        x=xx, y=signal, name="with MW", mode="lines+markers", visible="legendonly"
    )
    data_background = go.Scattergl(
        x=xx, y=background, name="w/o MW", mode="lines+markers", visible="legendonly"
    )
    data_df = go.Scattergl(
        x=xx, y=signal - background, name="diff", mode="lines+markers"
    )

    fit_df_list = []
    if "fit" in fit_enabled and fitset["params"]:
        xx_fit_contrast = np.linspace(min(xx), max(xx), len(xx) * 4)
        yy_fit_contrast = (
            curvefitting.model(xx_fit_contrast, *fitset["params"]) * 1e3
        )  # in mV
        fit_df_list = [
            go.Scattergl(
                x=xx_fit_contrast,
                y=yy_fit_contrast,
                mode="lines",
                name="Fit",
            )
        ]

    return {
        "data": [data_background, data_signal, data_df] + fit_df_list,
        "layout": go.Layout(
            xaxis_title="Frequency [GHz]",
            yaxis_title="Signal [mV]",
            template=template,
            font=dict(size=21),
            legend={
                "bgcolor": "rgba(0, 0, 0, 0)",  # Set background color to transparent
                "x": 0.8,  # Position legend on the left
                "y": 0.9,  # Position legend on the top
            },
            title=None,
            margin=dict(t=0),  # Remove the top margin where the title usually sits
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
    app.layout = layout_pODMR
    app.run_server(
        # host="0.0.0.0",
        debug=DEBUG,
        port=GUI_PORT,
    )
