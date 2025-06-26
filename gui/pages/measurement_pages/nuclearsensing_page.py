if __name__ == "__main__":
    import logging
    import os

    # Add the project root to the Python path
    path_project = "\\".join(os.getcwd().split("\\")[:-3])
    print(path_project)
    # In a real scenario, the following line would be uncommented
    # sys.path.insert(1, path_project)

    # Setup basic logging for testing
    logging.basicConfig(level=logging.DEBUG)


import logging

import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go
from dash import Input, Output, callback, callback_context, dcc, html
from dash_bootstrap_templates import load_figure_template

from gui.components import NumericInput, SelectInput, SliderInput

logger = logging.getLogger(__name__)
# Assuming these would be imported from the project structure
# from gui.components import NumericInput, SelectInput, SliderInput
# from gui.config import PLOT_THEME
# To make this script runnable standalone, we will define dummy versions
# and then the actual GUI code will use them.
from gui.config import APP_THEME, PLOT_THEME
from gui.task_config import JM, TASK_NQST

load_figure_template([PLOT_THEME, PLOT_THEME + "_dark"])

# =================================================================================================
# GUI Page Components
# =================================================================================================

DATA_INTERVAL = 200
STATE_INTERVAL = 200
MAX_INTERVAL = 2147483647
IDLE_INTERVAL = 500
ID = TASK_NQST.get_uiid()

GRAPH_INIT = {"data": [], "layout": go.Layout(template=PLOT_THEME + "_dark")}

layout_buttons = dbc.Row(
    dbc.ButtonGroup(
        [
            dbc.Button("Start", id=ID + "-button-start", outline=True, color="info"),
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
    )
)

layout_progressbar = dbc.Row(
    [
        dbc.Col(
            dbc.Badge(
                "idle",
                color="light",
                className="border mt-2 mb-2",
                id=ID + "-badge-status",
            ),
            width="auto",
        ),
        dbc.Col(
            dbc.Progress(
                value=0,
                id=ID + "-progressbar",
                animated=True,
                striped=True,
                label="",
                color="info",
                style={"width": "100%"},
            ),
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
        NumericInput(
            "Stop Time",
            min=0.0,
            max=86400,
            step=1,
            value=60,
            unit="s",
            id=ID + "-input-stoptime",
            persistence_type="local",
        ),
        SliderInput(
            "Refresh Rate",
            min=1,
            max=20,
            step=1,
            value=10,
            unit="Hz",
            id=ID + "-input-rate_refresh",
            marks={ii: f"{ii}" for ii in range(0, 21, 5)},
            persistence_type="local",
        ),
        NumericInput(
            "Number of Tracks",
            min=2,
            max=10000,
            step=2,
            value=100,
            unit="",
            id=ID + "-input-n_track",
            persistence_type="local",
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
            value=30.0,
            unit="%",
            id=ID + "-input-laser_current",
            persistence_type="local",
        ),
        NumericInput(
            "MW Freq",
            min=96.0,
            max=480.0,
            step=1e-3,
            value=398.550,
            unit="GHz",
            id=ID + "-input-mw_freq",
            persistence_type="local",
        ),
        NumericInput(
            "MW Power",
            min=0.0,
            max=5.0,
            step=0.1,
            value=5.0,
            unit="V",
            id=ID + "-input-mw_powervolt",
            persistence_type="local",
        ),
        NumericInput(
            "MW Phase",
            min=0.0,
            max=5.0,
            step=0.1,
            value=0.0,
            unit="V",
            id=ID + "-input-mw_phasevolt",
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
        dbc.InputGroup(
            [
                dbc.InputGroupText("⚠️RF All Set?⚠️"),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Checkbox(
                                    id=ID + "-input-rf_set",
                                    label="YES",
                                    value=False,
                                    persistence_type="local",
                                    className="mt-2",
                                ),
                            ]
                        )
                    ]
                ),
            ]
        ),
    ],
    className="mt-2 mb-2",
)

accordion_sequence = dbc.Accordion(
    [
        dbc.AccordionItem(
            [
                NumericInput(
                    "Laser Time",
                    min=0,
                    max=1e6,
                    step=1.0,
                    value=300.0,
                    unit="ns",
                    id=ID + "-input-t_prep_laser",
                    persistence_type="local",
                ),
                NumericInput(
                    "ISC Wait",
                    min=0,
                    max=1e6,
                    step=1.0,
                    value=200.0,
                    unit="ns",
                    id=ID + "-input-t_prep_isc",
                    persistence_type="local",
                ),
                NumericInput(
                    "Laser Pulses",
                    min=1,
                    max=1000,
                    step=1,
                    value=30,
                    unit="",
                    id=ID + "-input-n_prep_lpul",
                    persistence_type="local",
                ),
            ],
            title="Sensor Preparation",
        ),
        dbc.AccordionItem(
            [
                NumericInput(
                    "Init Wait",
                    min=0,
                    max=1e6,
                    step=1.0,
                    value=300.0,
                    unit="ns",
                    id=ID + "-input-t_prob_init_wait",
                    persistence_type="local",
                ),
                NumericInput(
                    "MW Pi/2",
                    min=0,
                    max=1e6,
                    step=1.0,
                    value=30.0,
                    unit="ns",
                    id=ID + "-input-t_prob_mw_a_pio2",
                    persistence_type="local",
                ),
                NumericInput(
                    "Phase Acc.",
                    min=0,
                    max=1e6,
                    step=1.0,
                    value=600.0,
                    unit="ns",
                    id=ID + "-input-t_prob_phacc",
                    persistence_type="local",
                ),
                NumericInput(
                    "Read Wait",
                    min=0,
                    max=1e6,
                    step=1.0,
                    value=300.0,
                    unit="ns",
                    id=ID + "-input-t_prob_read_wait",
                    persistence_type="local",
                ),
                NumericInput(
                    "Read Laser",
                    min=0,
                    max=1e6,
                    step=1.0,
                    value=600.0,
                    unit="ns",
                    id=ID + "-input-t_prob_laser",
                    persistence_type="local",
                ),
                NumericInput(
                    "Fwd Blocks",
                    min=1,
                    max=100,
                    step=1,
                    value=6,
                    unit="",
                    id=ID + "-input-n_dbloc_fwd",
                    persistence_type="local",
                ),
                NumericInput(
                    "Bwd Blocks",
                    min=1,
                    max=100,
                    step=1,
                    value=6,
                    unit="",
                    id=ID + "-input-n_dbloc_bwd",
                    persistence_type="local",
                ),
            ],
            title="Sensor Probing",
        ),
        dbc.AccordionItem(
            [
                NumericInput(
                    "RF Pi/2",
                    min=0,
                    max=1e6,
                    step=1.0,
                    value=16666,
                    unit="ns",
                    id=ID + "-input-t_rf_pio2",
                    persistence_type="local",
                ),
                NumericInput(
                    "Pre-Lock",
                    min=0,
                    max=1e6,
                    step=1.0,
                    value=20000,
                    unit="ns",
                    id=ID + "-input-t_prlo",
                    persistence_type="local",
                ),
                NumericInput(
                    "Fwd Lock",
                    min=0,
                    max=1e6,
                    step=1.0,
                    value=17000,
                    unit="ns",
                    id=ID + "-input-t_lock_fwd",
                    persistence_type="local",
                ),
                NumericInput(
                    "Bwd Lock",
                    min=0,
                    max=1e6,
                    step=1.0,
                    value=17000,
                    unit="ns",
                    id=ID + "-input-t_lock_bwd",
                    persistence_type="local",
                ),
            ],
            title="Target Control",
        ),
    ],
    always_open=True,
    className="mt-2 mb-2",
)

layout_exppara = dbc.Row(
    dbc.Col(
        dbc.Tabs(
            [
                dbc.Tab(tab_exppara_task, label="Task"),
                dbc.Tab(tab_exppara_hardware, label="Hardware"),
                dbc.Tab(accordion_sequence, label="Sequence"),
            ]
        )
    )
)

layout_para = dbc.Col([layout_buttons, layout_progressbar, layout_exppara])
layout_graph = dbc.Row(
    dbc.Container(
        dcc.Graph(
            figure=GRAPH_INIT,
            id=ID + "-graph",
            mathjax=True,
            animate=False,
            responsive="auto",
            style={"aspectRatio": "1.2/1"},
        ),
        fluid=True,
    )
)
layout_hidden = dbc.Row(
    [
        dcc.Interval(id=ID + "-interval-data", interval=MAX_INTERVAL),
        dcc.Interval(id=ID + "-interval-state", interval=MAX_INTERVAL),
        dcc.Store(
            id=ID + "-store-stateset", storage_type="memory", data=TASK_NQST.stateset
        ),
        dcc.Store(
            id=ID + "-store-paraset", storage_type="memory", data=TASK_NQST.paraset
        ),
        dcc.Store(
            id=ID + "-store-dataset", storage_type="memory", data=TASK_NQST.dataset
        ),
        dcc.Store(id=ID + "-auxillary", data={}),
    ]
)

layout_nuclear_quasi_static_track = dbc.Col(
    [
        dbc.Card(
            [
                dbc.CardHeader(
                    [html.H4("Nuclear Quasi-Static Track", className="mt-0 mb-0")]
                ),
                dbc.CardBody(
                    dbc.Row(
                        [
                            dbc.Col([layout_para], width=4),
                            dbc.Col([layout_graph], width=8),
                        ]
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
    path="/spectroscopy/nqst",
    name="Nuclear Quasi-Static Track",
)
layout = layout_nuclear_quasi_static_track
# =================================================================================================
# Callbacks
# =================================================================================================


@callback(
    Output(ID + "-auxillary", "data"),
    [
        Input(f"{ID}-input-{key}", "value")
        for key in [
            "priority",
            "stoptime",
            "rate_refresh",
            "n_track",
            "laser_current",
            "mw_freq",
            "mw_powervolt",
            "mw_phasevolt",
            "amp_input",
            "rf_set",
            "t_prep_laser",
            "t_prep_isc",
            "n_prep_lpul",
            "t_prob_init_wait",
            "t_prob_mw_a_pio2",
            "t_prob_phacc",
            "t_prob_read_wait",
            "t_prob_laser",
            "n_dbloc_fwd",
            "n_dbloc_bwd",
            "t_rf_pio2",
            "t_prlo",
            "t_lock_fwd",
            "t_lock_bwd",
        ]
    ],
    prevent_initial_call=False,
)
def update_params(*args):
    param_keys = [
        "priority",
        "stoptime",
        "rate_refresh",
        "n_track",
        "laser_current",
        "mw_freq",
        "mw_powervolt",
        "mw_phasevolt",
        "amp_input",
        "rf_set",
        "t_prep_laser",
        "t_prep_isc",
        "n_prep_lpul",
        "t_prob_init_wait",
        "t_prob_mw_a_pio2",
        "t_prob_phacc",
        "t_prob_read_wait",
        "t_prob_laser",
        "n_dbloc_fwd",
        "n_dbloc_bwd",
        "t_rf_pio2",
        "t_prlo",
        "t_lock_fwd",
        "t_lock_bwd",
    ]
    input_values = list(args)
    TASK_NQST.set_priority(int(input_values[0]))
    TASK_NQST.set_stoptime(input_values[1])
    paramsdict = dict(zip(param_keys[2:], input_values[2:]))
    TASK_NQST.set_paraset(**paramsdict)

    return {}


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
    logger.info(f"check_run_stop_exp {ctx}")
    if ctx.triggered_id == ID + "-button-start":
        logger.info("hello from the button store")
        return _run_exp()
    elif ctx.triggered_id == ID + "-button-pause":
        return _pause_exp()
    elif ctx.triggered_id == ID + "-button-stop":
        return _stop_exp()
    else:
        # initial call
        # print("hello from the button store initial call")
        if TASK_NQST.state == "run":
            return DATA_INTERVAL, STATE_INTERVAL
        else:
            return MAX_INTERVAL, IDLE_INTERVAL


def _run_exp():
    JM.start()
    JM.submit(TASK_NQST)
    # return False, True, True, DATA_INTERVAL
    return DATA_INTERVAL, STATE_INTERVAL


def _pause_exp():
    TASK_NQST.pause()
    # return True, False, True, MAX_INTERVAL
    return MAX_INTERVAL, IDLE_INTERVAL


def _stop_exp():
    JM.start()
    JM.remove(TASK_NQST)
    # return True, False, False, MAX_INTERVAL
    return MAX_INTERVAL, IDLE_INTERVAL


@callback(
    Output(ID + "-store-stateset", "data"),
    Input(ID + "-interval-state", "n_intervals"),
    prevent_initial_call=False,
)
def update_store_state(_):
    return TASK_NQST.stateset


@callback(
    Output(ID + "-store-paraset", "data"),
    Output(ID + "-store-dataset", "data"),
    Input(ID + "-interval-data", "n_intervals"),
    prevent_initial_call=False,
)
def update_store_parameters_data(_):
    return TASK_NQST.paraset, TASK_NQST.dataset


@callback(
    [
        Output(f"{ID}-input-{key}", "disabled")
        for key in [
            "priority",
            "stoptime",
            "rate_refresh",
            "n_track",
            "laser_current",
            "mw_freq",
            "mw_powervolt",
            "mw_phasevolt",
            "amp_input",
            # "rf_set",
            "t_prep_laser",
            "t_prep_isc",
            "n_prep_lpul",
            "t_prob_init_wait",
            "t_prob_mw_a_pio2",
            "t_prob_phacc",
            "t_prob_read_wait",
            "t_prob_laser",
            "n_dbloc_fwd",
            "n_dbloc_bwd",
            "t_rf_pio2",
            "t_prlo",
            "t_lock_fwd",
            "t_lock_bwd",
        ]
    ],
    Input(ID + "-store-stateset", "data"),
)
def disable_parameters(stateset):
    is_running = stateset.get("state") == "run"
    # return [is_running] * (len(inspect.signature(disable_parameters).parameters) - 1)
    return [is_running] * 23


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
    Output(ID + "-graph", "figure"),
    Input("dark-light-switch", "value"),
    Input(ID + "-store-dataset", "data"),
    prevent_initial_call=True,
)
def update_graph(switch_on, dataset):
    template = PLOT_THEME if switch_on else PLOT_THEME + "_dark"
    traces = []

    for prefix in ["AB", "BA"]:
        tau = np.array(dataset.get(f"tau_{prefix}", []))
        sig = np.array(dataset.get(f"sig_{prefix}", []))
        bg = np.array(dataset.get(f"sig_{prefix}_bg", []))

        if tau.size > 0 and sig.size > 0 and bg.size > 0:
            traces.append(
                go.Scattergl(
                    x=tau,
                    y=sig - bg,
                    mode="lines+markers",
                    name=f"Signal ({prefix[0]}->{prefix[1]})",
                )
            )
            traces.append(
                go.Scattergl(
                    x=tau,
                    y=sig,
                    mode="lines",
                    name=f"Raw {prefix[0]}->{prefix[1]}",
                    visible="legendonly",
                )
            )
            traces.append(
                go.Scattergl(
                    x=tau,
                    y=bg,
                    mode="lines",
                    name=f"BG {prefix[0]}->{prefix[1]}",
                    visible="legendonly",
                )
            )

    layout = go.Layout(
        xaxis_title="Evolution Time [ns]",
        yaxis_title="Signal [a.u.]",
        template=template,
        font=dict(size=16),
        legend=dict(bgcolor="rgba(0,0,0,0)", x=0.01, y=0.99),
        title=None,
        margin=dict(t=10, b=10, l=10, r=10),
    )
    return {"data": traces, "layout": layout}


if __name__ == "__main__":
    from dash_bootstrap_components import themes

    APP_THEME = themes.JOURNAL
    DEBUG = True
    GUI_PORT = 9844
    app = dash.Dash(__name__, external_stylesheets=[APP_THEME])
    app.layout = html.Div(
        [
            # Add a dummy dark-light-switch for standalone testing
            dcc.Store(id="dark-light-switch", data=True),
            layout_nuclear_quasi_static_track,
        ]
    )
    app.run_server(debug=DEBUG, port=GUI_PORT)
