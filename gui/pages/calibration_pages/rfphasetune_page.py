import os
import sys

# Auto insert project root to sys.path
path_project = os.path.abspath(os.path.join(os.getcwd(), "..", ".."))
sys.path.insert(1, path_project)

import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go
from dash import Input, Output, callback, callback_context, dcc, html
from dash_bootstrap_templates import load_figure_template

from gui.components import NumericInput
from gui.config import PLOT_THEME
from gui.task_config import JM, TASK_PHASETUNE

# Load Plotly template
load_figure_template([PLOT_THEME])

# ---------- Identifiers & Constants ----------
ID = TASK_PHASETUNE.get_uiid()
DATA_INTERVAL = 100
MAX_INTERVAL = 2147483647

# ---------- UI Layout Components ----------
layout_buttons = dbc.Row(
    [
        dbc.ButtonGroup(
            [
                dbc.Button(
                    "Start", id=ID + "-button-start", color="info", outline=True
                ),
                dbc.Button(
                    "Pause",
                    id=ID + "-button-pause",
                    color="secondary",
                    outline=True,
                    disabled=True,
                ),
                dbc.Button(
                    "Stop",
                    id=ID + "-button-stop",
                    color="secondary",
                    outline=True,
                    disabled=True,
                ),
            ]
        )
    ],
    className="mb-2",
)

layout_progress = dbc.Row(
    [
        dbc.Col(
            dbc.Progress(
                id=ID + "-progressbar",
                value=0,
                min=0.0,
                max=1.0,
                animated=True,
                striped=True,
                label="",
                color="info",
                className="mb-2",
            )
        )
    ]
)

layout_exppara = dbc.Col(
    [
        NumericInput(
            "MW Freq",
            1.0,
            2000.0,
            step=1.0,
            value=600.0,
            unit="MHz",
            id=ID + "-input-freq",
        ),
        NumericInput(
            "MW Power",
            -30.0,
            10.0,
            step=0.1,
            value=0.0,
            unit="dBm",
            id=ID + "-input-power",
        ),
        NumericInput(
            "Initial Phase",
            0.0,
            360.0,
            step=1.0,
            value=0.0,
            unit="°",
            id=ID + "-input-init_phase",
        ),
        NumericInput(
            "Initial Step",
            0.01,
            60.0,
            step=0.01,
            value=10.0,
            unit="°",
            id=ID + "-input-init_step",
        ),
        NumericInput(
            "Min Step",
            0.01,
            10.0,
            step=0.01,
            value=0.05,
            unit="°",
            id=ID + "-input-min_step",
        ),
        NumericInput(
            "Max Step",
            1.0,
            90.0,
            step=0.1,
            value=20.0,
            unit="°",
            id=ID + "-input-max_step",
        ),
        NumericInput(
            "Refresh Rate",
            1.0,
            100.0,
            step=0.1,
            value=10.0,
            unit="Hz",
            id=ID + "-input-refresh",
        ),
        NumericInput(
            "Stop Time",
            1.0,
            3600.0,
            step=1.0,
            value=20.0,
            unit="s",
            id=ID + "-input-stoptime",
        ),
    ],
    className="mb-2",
)

layout_left = dbc.Col(
    [
        layout_buttons,
        layout_progress,
        layout_exppara,
    ],
    width=4,
)

layout_graph = dbc.Col(
    dcc.Graph(
        id=ID + "-graph",
        figure={"data": [], "layout": go.Layout(template=PLOT_THEME)},
        style={"aspectRatio": "2/1"},
    ),
    width=8,
)

layout_hidden = html.Div(
    [
        dcc.Interval(id=ID + "-interval-data", interval=MAX_INTERVAL, n_intervals=0),
        dcc.Store(id=ID + "-store-stateset", storage_type="memory"),
        dcc.Store(id=ID + "-store-paraset", storage_type="memory"),
        dcc.Store(id=ID + "-store-dataset", storage_type="memory"),
    ]
)

layout_phase = dbc.Col(
    [
        dbc.Card(
            [
                dbc.CardHeader(html.H4("RF Relative Phase Tuning", className="mb-0")),
                dbc.CardBody(
                    dbc.Row(
                        [
                            layout_left,
                            layout_graph,
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

# ---------- Register Page ----------
dash.register_page(
    __name__,
    path="/calibration/rf_phase_tune",
    name="RF Phase Tuning",
)
layout = layout_phase


# ---------- Callbacks ----------
@callback(
    Output(ID + "-store-paraset", "data"),
    Input(ID + "-input-freq", "value"),
    Input(ID + "-input-power", "value"),
    Input(ID + "-input-init_phase", "value"),
    Input(ID + "-input-init_step", "value"),
    Input(ID + "-input-min_step", "value"),
    Input(ID + "-input-max_step", "value"),
    Input(ID + "-input-refresh", "value"),
    Input(ID + "-input-stoptime", "value"),
    prevent_initial_call=False,
)
def update_paraset(
    freq, power, init_phase, init_step, min_step, max_step, refresh, stoptime
):
    paras = dict(
        freq_mhz=freq,
        power_dbm=power,
        phaseA_deg=init_phase,
        initial_step_deg=init_step,
        min_step_deg=min_step,
        max_step_deg=max_step,
        rate_refresh=refresh,
    )
    TASK_PHASETUNE.set_paraset(**paras)
    TASK_PHASETUNE.set_stoptime(stoptime)
    return TASK_PHASETUNE.paraset


@callback(
    Output(ID + "-interval-data", "interval"),
    Input(ID + "-button-start", "n_clicks"),
    Input(ID + "-button-pause", "n_clicks"),
    Input(ID + "-button-stop", "n_clicks"),
    prevent_initial_call=False,
)
def handle_buttons(n_start, n_pause, n_stop):
    ctx = callback_context
    if ctx.triggered_id == ID + "-button-start":
        JM.start()
        JM.submit(TASK_PHASETUNE)
        return DATA_INTERVAL
    elif ctx.triggered_id == ID + "-button-pause":
        TASK_PHASETUNE.pause()
        return MAX_INTERVAL
    elif ctx.triggered_id == ID + "-button-stop":
        TASK_PHASETUNE.stop()
        return MAX_INTERVAL
    return MAX_INTERVAL


@callback(
    Output(ID + "-store-stateset", "data"),
    Output(ID + "-store-dataset", "data"),
    Input(ID + "-interval-data", "n_intervals"),
    prevent_initial_call=False,
)
def update_state_and_dataset(_):
    return TASK_PHASETUNE.stateset, TASK_PHASETUNE.dataset


@callback(
    Output(ID + "-progressbar", "value"),
    Output(ID + "-progressbar", "label"),
    Input(ID + "-store-stateset", "data"),
)
def update_progressbar(stateset):
    p_num = stateset["idx_run"] / max(stateset["num_run"], 1)
    p_time = stateset["time_run"] / max(stateset["time_stop"], 1)
    progress = min(1.0, max(p_num, p_time))
    return progress, f"{progress * 100:.0f}%"


@callback(
    Output(ID + "-graph", "figure"),
    Input(ID + "-store-dataset", "data"),
    prevent_initial_call=True,
)
def update_plot(dataset):
    phase = np.array(dataset["phase_history"])
    power = np.array(dataset["power_history"])
    x = np.arange(len(phase))

    trace_phase = go.Scattergl(
        x=x, y=phase, name="Phase B", mode="lines+markers", yaxis="y"
    )
    trace_power = go.Scattergl(
        x=x, y=power, name="Power B", mode="lines+markers", yaxis="y2"
    )

    layout = go.Layout(
        xaxis=dict(title="Iteration"),
        yaxis=dict(title="Phase [deg]"),
        yaxis2=dict(title="Power [µW]", overlaying="y", side="right"),
        template=PLOT_THEME,
        font=dict(size=21),
        margin=dict(t=30, b=40, l=50, r=50),
    )
    return {"data": [trace_phase, trace_power], "layout": layout}
