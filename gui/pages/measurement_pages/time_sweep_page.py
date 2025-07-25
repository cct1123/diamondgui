if __name__ == "__main__":
    import os
    import sys

    # This ensures that the script can find the project's modules
    path_project = "\\".join(os.getcwd().split("\\")[:-3])
    print(path_project)
    # caution: path[0] is reserved for script path (or '' in REPL)
    sys.path.insert(1, path_project)

import logging

import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go
from dash import Input, Output, callback, callback_context, dcc, html
from dash_bootstrap_templates import load_figure_template

logger = logging.getLogger(__name__)
from gui.components import NumericInput, SelectInput, SliderInput
from gui.config import PLOT_THEME

# TASK_TSWEEPCOLL is now an instance of TimeSweepCollection
from gui.task_config import JM, TASK_TSWEEPCOLL

load_figure_template([PLOT_THEME, PLOT_THEME + "_dark"])

# ==============================================================================================================================
# UI Constants and Component Definitions
# ==============================================================================================================================

DATA_INTERVAL = 100
STATE_INTERVAL = 100
MAX_INTERVAL = 2147483647
IDLE_INTERVAL = 500
ID = TASK_TSWEEPCOLL.get_uiid()

GRAPH_INIT = {"data": [], "layout": go.Layout(template=PLOT_THEME + "_dark")}

# --- Main UI Components ---

layout_buttons = dbc.Row(
    [
        dbc.ButtonGroup(
            [
                dbc.Button(
                    "Start", id=ID + "-button-start", outline=True, color="info"
                ),
                dbc.Button(
                    "Pause",
                    id=ID + "-button-pause",
                    outline=True,
                    color="secondary",
                    disabled=True,
                ),
                dbc.Button(
                    "Stop",
                    id=ID + "-button-stop",
                    outline=True,
                    color="secondary",
                    disabled=True,
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

select_measurement = dbc.InputGroup(
    [
        dbc.InputGroupText("Measurement"),
        dbc.Select(
            id=ID + "-select-measurement",
            options=[
                {"label": "Relaxation", "value": "Relaxation"},
                {"label": "Ramsey", "value": "Ramsey"},
                {"label": "Hahn Echo", "value": "HahnEcho"},
                {"label": "CPMG", "value": "CPMG"},
                {"label": "XY4", "value": "XY4"},
                {"label": "XY8", "value": "XY8"},
                {"label": "CorrSpec", "value": "CorrSpec"},
            ],
            value="Relaxation",
            persistence=True,
            persistence_type="local",
        ),
    ],
    className="mb-2",
)

# --- Parameter Tabs ---

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
        select_measurement,
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
            name="Data Refresh",
            min=2,
            max=50,
            step=2,
            value=10,
            unit="Hz",
            id=ID + "-input-rate_refresh",
            marks={i: str(i) for i in range(0, 51, 10)},
            persistence_type="local",
            disabled=True,
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
            max=12,
            step="any",
            value=0.0,
            unit="V",
            id=ID + "-input-mw_phasevolt",
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
    ],
    className="mt-2 mb-2",
)

sequence_dynamic_controls = html.Div(
    [
        html.Div(
            id=ID + "-slope_det-wrapper",
            children=[
                SelectInput(
                    "Detect",
                    options=["Slope", "Variance"],
                    value="Slope",
                    id=ID + "-input-slope_det",
                    persistence_type="local",
                ),
            ],
        ),
        html.Div(
            id=ID + "-n_pi-wrapper",
            children=[
                NumericInput(
                    "N Pi Pulses",
                    min=1,
                    max=100,
                    step=1,
                    value=1,
                    unit="",
                    id=ID + "-input-n_pi",
                    persistence_type="local",
                )
            ],
        ),
        html.Div(
            id=ID + "-n_XY4-wrapper",
            children=[
                NumericInput(
                    "N XY4",
                    min=1,
                    max=100,
                    step=1,
                    value=1,
                    unit="",
                    id=ID + "-input-n_XY4",
                    persistence_type="local",
                )
            ],
        ),
        html.Div(
            id=ID + "-n_XY8-wrapper",
            children=[
                NumericInput(
                    "N XY8",
                    min=1,
                    max=100,
                    step=1,
                    value=1,
                    unit="",
                    id=ID + "-input-n_XY8",
                    persistence_type="local",
                )
            ],
        ),
        html.Div(
            id=ID + "-tau_dd-wrapper",
            children=[
                NumericInput(
                    "Tau DD",
                    min=1.0,
                    max=10000.0,
                    step=1.0,
                    value=50.0,
                    unit="",
                    id=ID + "-input-tau_dd",
                    persistence_type="local",
                )
            ],
        ),
    ]
)

tab_exppara_sequence = dbc.Col(
    [
        NumericInput(
            "Tau Begin",
            min=0.0,
            max=1e9,
            step=1.0,
            value=0.0,
            unit="ns",
            id=ID + "-input-tau_begin",
            persistence_type="local",
        ),
        NumericInput(
            "Tau End",
            min=0.0,
            max=5e9,
            step=1.0,
            value=1000.0,
            unit="ns",
            id=ID + "-input-tau_end",
            persistence_type="local",
        ),
        NumericInput(
            "Tau Step",
            min=1.0,
            max=1e6,
            step=1.0,
            value=50.0,
            unit="ns",
            id=ID + "-input-tau_step",
            persistence_type="local",
        ),
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
            min=0,
            max=1000,
            step=1,
            value=40,
            unit="",
            id=ID + "-input-init_repeat",
            persistence_type="local",
        ),
        NumericInput(
            "Init Wait",
            min=0.0,
            max=100e3,
            step=1.0,
            value=1001.0,
            unit="ns",
            id=ID + "-input-init_wait",
            persistence_type="local",
        ),
        NumericInput(
            "Read Wait",
            min=0.0,
            max=5e3,
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
            "Pi Pulse (mwA)",
            min=0.0,
            max=1000.0,
            step=1.0,
            value=100.0,
            unit="ns",
            id=ID + "-input-t_pi_mwa",
            persistence_type="local",
        ),
        NumericInput(
            "Pi Pulse (mwB)",
            min=0.0,
            max=1000.0,
            step=1.0,
            value=100.0,
            unit="ns",
            id=ID + "-input-t_pi_mwb",
            persistence_type="local",
        ),
        sequence_dynamic_controls,
    ],
    className="mt-2 mb-2",
)

# --- Page Layout Assembly ---

layout_para = dbc.Col(
    [
        layout_buttons,
        layout_progressbar,
        dbc.Tabs(
            [
                dbc.Tab(tab_exppara_task, label="Task"),
                dbc.Tab(tab_exppara_hardware, label="Hardware"),
                dbc.Tab(tab_exppara_sequence, label="Sequence"),
            ]
        ),
    ]
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
# layout_hidden = dbc.Col(
#     [
#         dcc.Interval(id=ID + "-interval-data", interval=MAX_INTERVAL),
#         dcc.Interval(id=ID + "-interval-state", interval=MAX_INTERVAL),
#         dcc.Store(id=ID + "-store-stateset", data={}),
#         dcc.Store(id=ID + "-store-paraset", data={}),
#         dcc.Store(id=ID + "-store-dataset", data={}),
#         dcc.Store(id=ID + "-store-measelect", data={}),
#         # dcc.Store(id=ID + "-auxillary", data={}),
#     ]
# )

layout_hidden = dbc.Row(
    [
        dcc.Interval(id=ID + "-interval-data", interval=MAX_INTERVAL, n_intervals=0),
        dcc.Interval(id=ID + "-interval-state", interval=MAX_INTERVAL, n_intervals=0),
        # dcc.Store(id=ID+"-store-plot", storage_type='memory', data=plotdata),
        dcc.Store(id=ID + "-store-stateset", storage_type="memory", data={}),
        dcc.Store(id=ID + "-store-paraset", storage_type="memory", data={}),
        dcc.Store(id=ID + "-store-dataset", storage_type="memory", data={}),
        dcc.Store(id=ID + "-store-auxillary", storage_type="memory", data={}),
    ]
)

dash.register_page(__name__, path="/sensor/timesweep", name="TimeSweep")
layout = dbc.Col(
    [
        dbc.Card(
            [
                dbc.CardHeader([html.H4("Time Sweep", className="mt-0 mb-0")]),
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


# ============================================================================================================
# Callback Definitions
# ============================================================================================================


@callback(
    Output(ID + "-slope_det-wrapper", "style"),
    Output(ID + "-n_pi-wrapper", "style"),
    Output(ID + "-n_XY4-wrapper", "style"),
    Output(ID + "-n_XY8-wrapper", "style"),
    Output(ID + "-tau_dd-wrapper", "style"),
    Input(ID + "-select-measurement", "value"),
    prevent_initial_call=False,
)
def toggle_sequence_parameters(m_type):
    """Shows or hides sequence parameters based on the selected measurement type."""
    hide, show = {"display": "none"}, {"display": "block"}
    return (
        show if m_type in ["Ramsey", "HahnEcho", "CPMG", "XY4", "XY8"] else hide,
        show if m_type == "CPMG" else hide,
        show if m_type == "XY4" else hide,
        show if m_type == "XY8" else hide,
        show if m_type == "CorrSpec" else hide,
    )


@callback(
    [Output(ID + "-store-auxillary", "data")]
    + [
        Input(f"{ID}-input-{param}", "value")
        for param in [
            "priority",
            "stoptime",
            "laser_current",
            "mw_freq",
            "mw_powervolt",
            "mw_phasevolt",
            "amp_input",
            "rate_refresh",
            "tau_begin",
            "tau_end",
            "tau_step",
            "init_nslaser",
            "init_isc",
            "init_repeat",
            "init_wait",
            "read_wait",
            "read_laser",
            "t_pi_mwa",
            "t_pi_mwb",
            # dynamic parameters input
            "slope_det",
            "n_pi",
            "n_XY4",
            "n_XY8",
            "tau_dd",
        ]
    ]
    + [Input(ID + "-select-measurement", "value")],
    prevent_initial_call=False,
)
def update_params(*args):
    """Applies all UI parameters to the active measurement task."""
    # logger.info(f"Updating parameters...{args}")
    input_values = list(args)
    m_type = input_values[-1]

    param_keys_static = [
        "priority",
        "stoptime",
        "laser_current",
        "mw_freq",
        "mw_powervolt",
        "mw_phasevolt",
        "amp_input",
        "rate_refresh",
        "tau_begin",
        "tau_end",
        "tau_step",
        "init_nslaser",
        "init_isc",
        "init_repeat",
        "init_wait",
        "read_wait",
        "read_laser",
        "t_pi_mwa",
        "t_pi_mwb",
    ]
    idx_paradyn = len(param_keys_static)
    paramsdict = dict(zip(param_keys_static[2:-1], input_values[2:idx_paradyn]))
    paramsdict["amp_input"] = int(paramsdict["amp_input"])

    if m_type in ["Ramsey", "HahnEcho", "XY4", "XY8", "CPMG"]:
        paramsdict["slope_det"] = (
            True if input_values[idx_paradyn] == "Slope" else False
        )
    if m_type == "CPMG":
        paramsdict["n_pi"] = input_values[idx_paradyn + 1]
    if m_type == "XY4":
        paramsdict["n_XY4"] = input_values[idx_paradyn + 2]
    if m_type == "XY8":
        paramsdict["n_XY8"] = input_values[idx_paradyn + 3]
    if m_type == "CorrSpec":
        paramsdict["tau_dd"] = input_values[idx_paradyn + 4]

    TASK_TSWEEPCOLL.select(m_type)
    TASK_TSWEEPCOLL.active_measurement.set_priority(int(input_values[0]))
    TASK_TSWEEPCOLL.active_measurement.set_stoptime(input_values[1])

    TASK_TSWEEPCOLL.active_measurement.set_paraset(**paramsdict)

    return [{}]


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
    if not ctx.triggered:
        if TASK_TSWEEPCOLL.active_measurement.state == "run":
            return DATA_INTERVAL, STATE_INTERVAL
        else:
            return MAX_INTERVAL, IDLE_INTERVAL

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if triggered_id == ID + "-button-start":
        return _run_exp()
    elif triggered_id == ID + "-button-pause":
        return _pause_exp()
    elif triggered_id == ID + "-button-stop":
        return _stop_exp()
    else:
        # initial call
        if TASK_TSWEEPCOLL.active_measurement.state == "run":
            return DATA_INTERVAL, STATE_INTERVAL
        else:
            return MAX_INTERVAL, IDLE_INTERVAL


def _run_exp():
    JM.start()
    JM.submit(TASK_TSWEEPCOLL.active_measurement)
    # return False, True, True, DATA_INTERVAL
    return DATA_INTERVAL, STATE_INTERVAL


def _pause_exp():
    TASK_TSWEEPCOLL.active_measurement.pause()
    # return True, False, True, MAX_INTERVAL
    return MAX_INTERVAL, IDLE_INTERVAL


def _stop_exp():
    JM.start()
    JM.remove(TASK_TSWEEPCOLL.active_measurement)
    # return True, False, False, MAX_INTERVAL
    return MAX_INTERVAL, IDLE_INTERVAL


@callback(
    Output(ID + "-store-stateset", "data"),
    Input(ID + "-interval-state", "n_intervals"),
    prevent_initial_call=False,
)
def update_store_state(_):
    return TASK_TSWEEPCOLL.active_measurement.stateset


@callback(
    Output(ID + "-store-paraset", "data"),
    Output(ID + "-store-dataset", "data"),
    Input(ID + "-interval-data", "n_intervals"),
    prevent_initial_call=False,
)
def update_store_parameters_data(_):
    return (
        TASK_TSWEEPCOLL.active_measurement.paraset,
        TASK_TSWEEPCOLL.active_measurement.dataset,
    )


@callback(
    [
        Output(f"{ID}-input-{key}", "disabled")
        for key in [
            "priority",
            "stoptime",
            "laser_current",
            "mw_freq",
            "mw_powervolt",
            "mw_phasevolt",
            "amp_input",
            "rate_refresh",
            "tau_begin",
            "tau_end",
            "tau_step",
            "init_nslaser",
            "init_isc",
            "init_repeat",
            "init_wait",
            "read_wait",
            "read_laser",
            "t_pi_mwa",
            "t_pi_mwb",
            # dynamic parameters input
            "slope_det",
            "n_pi",
            "n_XY4",
            "n_XY8",
            "tau_dd",
        ]
    ]
    + [
        Output(ID + "-select-measurement", "disabled"),
        Input(ID + "-store-stateset", "data"),
    ]
)
def disable_parameters(stateset):
    is_running = stateset.get("state") == "run"
    # return [is_running] * (len(inspect.signature(disable_parameters).parameters) - 1)
    return [is_running] * 25


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
    progress_num = (
        stateset["idx_run"] / stateset["num_run"] if stateset["num_run"] > 0 else 0
    )
    progress_time = (
        stateset["time_run"] / stateset["time_stop"] if stateset["time_stop"] > 0 else 0
    )
    progress = max(progress_num, progress_time)
    progress = min(progress, 1)
    # print(f"progress = {progress}")
    return progress, f"{(100 * progress):.0f}%"


from plotly.subplots import make_subplots


# --- Update main graph ---
@callback(
    Output(ID + "graph", "figure"),
    Input("dark-light-switch", "value"),
    Input(ID + "-store-dataset", "data"),
    prevent_initial_call=True,
)
def update_graph(dark_mode_on, dataset):
    """Updates the main data plot with four subplots including FFTs."""
    template = PLOT_THEME if dark_mode_on else PLOT_THEME + "_dark"

    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=False,  # disables global sharing
        vertical_spacing=0.05,
        row_heights=[0.3, 0.25, 0.25],
        specs=[[{}], [{}], [{}]],
    )
    if not dataset or "tau" not in dataset or len(dataset["tau"]) == 0:
        fig.update_layout(template=template, showlegend=False)
        fig.add_annotation(
            text="Waiting for data...",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        return fig

    xx = np.array(dataset["tau"])
    ref_bright = dataset.get("bright", 0) * 1e3
    ref_dark = dataset.get("dark", 0) * 1e3
    sig_p = np.array(dataset.get("sig_p", [])) * 1e3
    sig_n = np.array(dataset.get("sig_n", [])) * 1e3

    if sig_p.size == 0 or sig_n.size == 0 or xx.size == 0:
        fig.update_layout(template=template, showlegend=False)
        fig.add_annotation(
            text="Data arrays are empty.",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        return fig

    yy_diff = sig_p - sig_n

    # --- Top Plot (Difference) ---
    fig.add_trace(
        go.Scattergl(x=xx, y=yy_diff, name="Diff.", mode="lines+markers"),
        row=1,
        col=1,
    )

    # --- Middle Plot (Raw Signals) ---
    fig.add_trace(
        go.Scattergl(x=xx, y=sig_p, name="Signal (P)", mode="lines+markers"),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scattergl(x=xx, y=sig_n, name="Signal (N)", mode="lines+markers"),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scattergl(
            x=[xx[0], xx[-1]],
            y=[ref_bright, ref_bright],
            name="Bright",
            mode="lines",
            line=dict(dash="dash"),
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scattergl(
            x=[xx[0], xx[-1]],
            y=[ref_dark, ref_dark],
            name="Dark",
            mode="lines",
            line=dict(dash="dash"),
        ),
        row=2,
        col=1,
    )

    # --- Third Plot: FFT of (sig_n - sig_p) ---
    dt = (xx[1] - xx[0]) * 1e-9
    N = len(yy_diff)
    freq_diff = np.fft.rfftfreq(N, d=dt) * 1e-6
    fft_diff = np.fft.rfft(yy_diff - np.mean(yy_diff))
    fft_mag_diff = np.abs(fft_diff)

    if freq_diff.size > 0 and fft_mag_diff.size > 0:
        fig.add_trace(
            go.Scattergl(
                x=freq_diff, y=fft_mag_diff, name="FFT of Diff.", mode="lines+markers"
            ),
            row=3,
            col=1,
        )

    else:
        fig.add_annotation(
            text="FFT (Diff)",
            xref="x3",
            yref="y3",
            x=0.5,
            y=0.5,
            showarrow=False,
            row=3,
            col=1,
        )

    # FFT of sig_p and sig_n ---
    fft_p = np.fft.rfft(sig_p - np.mean(sig_p))
    fft_n = np.fft.rfft(sig_n - np.mean(sig_n))
    fft_mag_p = np.abs(fft_p)
    fft_mag_n = np.abs(fft_n)
    freq_sig = np.fft.rfftfreq(len(sig_p), d=dt) * 1e-6

    if freq_sig.size > 0 and fft_mag_p.size > 0 and fft_mag_n.size > 0:
        fig.add_trace(
            go.Scattergl(
                x=freq_sig,
                y=fft_mag_p,
                name="FFT of Sig P",
                mode="lines+markers",
            ),
            row=3,
            col=1,
        )
        fig.add_trace(
            go.Scattergl(
                x=freq_sig, y=fft_mag_n, name="FFT of Sig N", mode="lines+markers"
            ),
            row=3,
            col=1,
        )

    else:
        fig.add_annotation(
            text="FFT (P/N)",
            xref="x4",
            yref="y4",
            x=0.5,
            y=0.5,
            showarrow=False,
            row=3,
            col=1,
        )

    fig.update_layout(
        template=template,
        legend=dict(traceorder="normal"),
        margin=dict(t=20, b=20, l=20, r=20),
    )

    fig.update_xaxes(showticklabels=False, row=1, col=1)
    fig.update_xaxes(title_text="tau_eff [ns]", row=2, col=1)
    fig.update_yaxes(title_text="PL [mV]", row=1, col=1)
    fig.update_yaxes(title_text="PL [mV]", row=2, col=1)
    fig.update_xaxes(title_text="Frequency [MHz]", row=3, col=1)
    fig.update_yaxes(title_text="Magnitude [a.u.]", row=3, col=1)

    return fig


if __name__ == "__main__":
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.JOURNAL])
    app.layout = layout
    app.run_server(debug=True, port=9843)
    app.run_server(debug=True, port=9843)
    app.run_server(debug=True, port=9843)
    app.run_server(debug=True, port=9843)
