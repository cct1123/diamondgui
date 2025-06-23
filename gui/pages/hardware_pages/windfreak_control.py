"""
Windfreak SynthHD Controller Page

last update: 2025/06/20
"""

import time

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html, no_update

from hardware.hardwaremanager import HardwareManager

# Initialize hardware manager
hm = HardwareManager()

# ---------- Layout ---------- #

layout_windfreak = dbc.Container(
    [
        dbc.Card(
            [
                dbc.CardHeader(
                    html.H4("Windfreak SynthHD Control", className="mt-0 mb-0")
                ),
                dbc.CardBody(
                    [
                        html.H5("Channel A"),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label("Frequency (MHz)"),
                                        dcc.Input(
                                            id="wf-freq-input-a",
                                            type="number",
                                            value=1000,
                                            min=50,
                                            max=13999,
                                            step=1,
                                            className="form-control",
                                        ),
                                    ],
                                    width=3,
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Power (dBm)"),
                                        dcc.Input(
                                            id="wf-power-input-a",
                                            type="number",
                                            value=0,
                                            min=-40,
                                            max=20,
                                            step=1,
                                            className="form-control",
                                        ),
                                    ],
                                    width=3,
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Phase (°)"),
                                        dcc.Input(
                                            id="wf-phase-input-a",
                                            type="number",
                                            value=0,
                                            min=0,
                                            max=360,
                                            step=1,
                                            className="form-control",
                                        ),
                                    ],
                                    width=3,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Button(
                                            "Set Output A",
                                            id="wf-set-btn-a",
                                            color="primary",
                                            className="me-2 mt-4",
                                        ),
                                        dbc.Button(
                                            "Disable A",
                                            id="wf-disable-btn-a",
                                            color="danger",
                                            className="mt-4",
                                        ),
                                    ],
                                    width=3,
                                ),
                            ],
                            className="mb-4",
                        ),
                        html.H5("Channel B"),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label("Frequency (MHz)"),
                                        dcc.Input(
                                            id="wf-freq-input-b",
                                            type="number",
                                            value=1000,
                                            min=50,
                                            max=13999,
                                            step=1,
                                            className="form-control",
                                        ),
                                    ],
                                    width=3,
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Power (dBm)"),
                                        dcc.Input(
                                            id="wf-power-input-b",
                                            type="number",
                                            value=0,
                                            min=-40,
                                            max=20,
                                            step=1,
                                            className="form-control",
                                        ),
                                    ],
                                    width=3,
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Phase (°)"),
                                        dcc.Input(
                                            id="wf-phase-input-b",
                                            type="number",
                                            value=0,
                                            min=0,
                                            max=360,
                                            step=1,
                                            className="form-control",
                                        ),
                                    ],
                                    width=3,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Button(
                                            "Set Output B",
                                            id="wf-set-btn-b",
                                            color="primary",
                                            className="me-2 mt-4",
                                        ),
                                        dbc.Button(
                                            "Disable B",
                                            id="wf-disable-btn-b",
                                            color="danger",
                                            className="mt-4",
                                        ),
                                    ],
                                    width=3,
                                ),
                            ]
                        ),
                        html.H5("Phase Lock Control"),
                        dbc.Button(
                            id="wf-phase-lock-toggle",
                            n_clicks=0,
                            color="secondary",
                            className="mb-3",
                            children="Locking: OFF",
                        ),
                        html.Div(id="wf-status", className="mt-3 text-success"),
                        html.Hr(),
                        html.H5("Current Channel Status"),
                        dcc.Interval(id="wf-interval", interval=1000, n_intervals=0),
                        dbc.Table(
                            id="wf-status-table",
                            bordered=True,
                            striped=True,
                            hover=True,
                        ),
                        html.Div(id="wf-last-updated", className="text-muted mt-2"),
                        dcc.Store(id="wf-status-store", storage_type="memory"),
                    ]
                ),
            ]
        )
    ],
    fluid=True,
)

# ---------- Callbacks ---------- #


@callback(
    Output("wf-status", "children"),
    Output("wf-freq-input-a", "disabled"),
    Output("wf-power-input-a", "disabled"),
    Output("wf-phase-input-a", "disabled"),
    Output("wf-set-btn-a", "color"),
    Output("wf-disable-btn-a", "color"),
    Input("wf-set-btn-a", "n_clicks"),
    State("wf-freq-input-a", "value"),
    State("wf-power-input-a", "value"),
    State("wf-phase-input-a", "value"),
    prevent_initial_call=True,
)
def handle_set_output_a(_, freq, power, phase):
    try:
        hm.windfreak.set_freq(freq * 1e6, channel=0)
        hm.windfreak.set_power(power, channel=0)
        hm.windfreak.set_phase(
            channel=0,
            phase_deg=phase,
            locking_status=hm.windfreak.read_channel("locking"),
        )
        hm.windfreak.enable_output(channel=0)
        return (
            f"Channel A set to {freq} MHz, {power} dBm, {phase}°",
            True,
            True,
            True,
            "success",
            "secondary",
        )
    except Exception as e:
        return f"Error (Channel A): {e}", False, False, False, "primary", "danger"


@callback(
    Output("wf-status", "children", allow_duplicate=True),
    Output("wf-freq-input-b", "disabled", allow_duplicate=True),
    Output("wf-power-input-b", "disabled", allow_duplicate=True),
    Output("wf-phase-input-b", "disabled", allow_duplicate=True),
    Output("wf-set-btn-b", "color", allow_duplicate=True),
    Output("wf-disable-btn-b", "color", allow_duplicate=True),
    Input("wf-set-btn-b", "n_clicks"),
    State("wf-freq-input-b", "value"),
    State("wf-power-input-b", "value"),
    State("wf-phase-input-b", "value"),
    prevent_initial_call=True,
)
def handle_set_output_b(_, freq, power, phase):
    try:
        hm.windfreak.set_freq(freq * 1e6, channel=1)
        hm.windfreak.set_power(power, channel=1)
        hm.windfreak.set_phase(
            channel=1,
            phase_deg=phase,
            locking_status=hm.windfreak.read_channel("locking"),
        )
        hm.windfreak.enable_output(channel=1)
        return (
            f"Channel B set to {freq} MHz, {power} dBm, {phase}°",
            True,
            True,
            True,
            "success",
            "secondary",
        )
    except Exception as e:
        return f"Error (Channel B): {e}", False, False, False, "primary", "danger"


@callback(
    Output("wf-status", "children", allow_duplicate=True),
    Output("wf-freq-input-a", "disabled", allow_duplicate=True),
    Output("wf-power-input-a", "disabled", allow_duplicate=True),
    Output("wf-phase-input-a", "disabled", allow_duplicate=True),
    Output("wf-set-btn-a", "color", allow_duplicate=True),
    Output("wf-disable-btn-a", "color", allow_duplicate=True),
    Input("wf-disable-btn-a", "n_clicks"),
    prevent_initial_call=True,
)
def handle_disable_output_a(_):
    try:
        hm.windfreak.disable(channel=0)
        return "Channel A output disabled", False, False, False, "primary", "danger"
    except Exception as e:
        return (
            f"Error disabling Channel A: {e}",
            True,
            True,
            True,
            "success",
            "secondary",
        )


@callback(
    Output("wf-status", "children", allow_duplicate=True),
    Output("wf-freq-input-b", "disabled", allow_duplicate=True),
    Output("wf-power-input-b", "disabled", allow_duplicate=True),
    Output("wf-phase-input-b", "disabled", allow_duplicate=True),
    Output("wf-set-btn-b", "color", allow_duplicate=True),
    Output("wf-disable-btn-b", "color", allow_duplicate=True),
    Input("wf-disable-btn-b", "n_clicks"),
    prevent_initial_call=True,
)
def handle_disable_output_b(_):
    try:
        hm.windfreak.disable(channel=1)
        return "", False, False, False, "primary", "danger"
    except Exception as e:
        return (
            f"Error disabling Channel B: {e}",
            True,
            True,
            True,
            "success",
            "secondary",
        )


@callback(
    Output("wf-status-table", "children"),
    Output("wf-status-store", "data"),
    Output("wf-last-updated", "children"),
    Input("wf-interval", "n_intervals"),
    State("wf-status-store", "data"),
)
def update_status_table(_, stored_data):
    try:

        def read(ch, param):
            return hm.windfreak.synth[ch].read(param)

        phase_a, phase_b, locking = hm.windfreak.read_channel("phase")
        now = time.time()
        channels = []

        for ch in [0, 1]:
            freq = round(read(ch, "frequency"), 3)
            power = round(read(ch, "power"), 2)
            enabled = "Yes" if read(ch, "rf_enable") else "No"
            phase = round(phase_a if ch == 0 else phase_b, 1)
            channels.append(
                {
                    "channel": ch,
                    "freq": freq,
                    "power": power,
                    "enabled": enabled,
                    "phase": phase,
                    "locking": locking if ch == 0 else "",
                }
            )

        table = html.Tbody(
            [
                html.Tr(
                    [
                        html.Td(f"Channel {c['channel']}"),
                        html.Td(c["freq"]),
                        html.Td(c["power"]),
                        html.Td(c["enabled"]),
                        html.Td(c["phase"]),
                        html.Td(c["locking"]),
                    ]
                )
                for c in channels
            ]
        )

        return (
            [
                html.Thead(
                    html.Tr(
                        [
                            html.Th("Channel"),
                            html.Th("Frequency (MHz)"),
                            html.Th("Power (dBm)"),
                            html.Th("Enabled"),
                            html.Th("Phase (°)"),
                            html.Th("Locking"),
                        ]
                    )
                ),
                table,
            ],
            {"timestamp": now, "channels": channels},
            "Last updated just now",
        )

    except Exception:
        if not stored_data:
            return no_update, no_update, "No valid data available"

        age = int(time.time() - stored_data["timestamp"])
        age_msg = (
            f"Last update {age} sec ago"
            if age < 60
            else f"Last update {age // 60} min ago"
        )

        table = html.Tbody(
            [
                html.Tr(
                    [
                        html.Td(f"Channel {c['channel']}"),
                        html.Td(c["freq"]),
                        html.Td(c["power"]),
                        html.Td(c["enabled"]),
                        html.Td(c["phase"]),
                        html.Td(c["locking"]),
                    ]
                )
                for c in stored_data["channels"]
            ]
        )

        return (
            [
                html.Thead(
                    html.Tr(
                        [
                            html.Th("Channel"),
                            html.Th("Frequency (MHz)"),
                            html.Th("Power (dBm)"),
                            html.Th("Enabled"),
                            html.Th("Phase (°)"),
                            html.Th("Locking"),
                        ]
                    )
                ),
                table,
            ],
            no_update,
            age_msg,
        )


@callback(
    Output("wf-phase-lock-toggle", "children"),
    Output("wf-phase-lock-toggle", "color"),
    Input("wf-phase-lock-toggle", "n_clicks"),
    State("wf-phase-lock-toggle", "children"),
    prevent_initial_call=True,
)
def toggle_phase_lock(n_clicks, current_label):
    try:
        locking_now = "ON" if "OFF" in current_label else "OFF"
        hm.windfreak.set_phase(
            channel=0, phase_deg=hm.windfreak.ch0_phase, locking_status=locking_now
        )
        label = f"Locking: {locking_now}"
        color = "success" if locking_now == "ON" else "secondary"
        return label, color
    except Exception as e:
        return f"Error: {e}", "danger"
