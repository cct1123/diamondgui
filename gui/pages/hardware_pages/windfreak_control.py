"""
hardware control page

last update: 2025/01/13
"""

import dash_bootstrap_components as dbc
from dash import callback, dcc, html
from dash.dependencies import Input, Output, State

if __name__ == "__main__":
    import os
    import sys

    path_project = "\\".join(os.getcwd().split("\\")[:-3])
    print(path_project)
    sys.path.insert(1, path_project)
    from hardware.hardwaremanager import HardwareManager

    hm = HardwareManager()
    if not hm.has("windfreak"):
        from pathlib import Path

        import hardware.config as hcf

        hm.add(
            "windfreak",
            Path(path_project) / "hardware" / "mw" / "windfreak.py",
            "WindfreakSynth",
            [hcf.WINDFREAK_PORT],
        )
else:
    from hardware.hardwaremanager import HardwareManager

    hm = HardwareManager()


layout_windfreak = dbc.Container(
    [
        html.H3("Windfreak SynthHD Controller", className="mb-4"),
        # Channel A
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
        # Channel B
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
        dbc.Row(
            dbc.Col(
                dbc.Button(
                    "Set Both Channels",
                    id="wf-set-both-btn",
                    color="success",
                    className="mt-4",
                ),
                width="auto",
            ),
            className="mb-3",
        ),
        html.Div(id="wf-status", className="mt-3 text-success"),
    ],
    fluid=True,
)


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
def handle_set_output_a(n_clicks, freq, power, phase):
    try:
        hm.windfreak.set_output(freq * 1e6, power, phase=phase, channel=0)
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
def handle_set_output_b(n_clicks, freq, power, phase):
    try:
        hm.windfreak.set_output(freq * 1e6, power, phase=phase, channel=1)
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
    Input("wf-set-both-btn", "n_clicks"),
    State("wf-freq-input-a", "value"),
    State("wf-power-input-a", "value"),
    State("wf-phase-input-a", "value"),
    State("wf-freq-input-b", "value"),
    State("wf-power-input-b", "value"),
    State("wf-phase-input-b", "value"),
    prevent_initial_call=True,
)
def handle_set_both_channels(
    n_clicks, freq_a, power_a, phase_a, freq_b, power_b, phase_b
):
    try:
        hm.windfreak.set_output(freq_a * 1e6, power_a, phase=phase_a, channel=0)
        hm.windfreak.set_output(freq_b * 1e6, power_b, phase=phase_b, channel=1)
        return f"Both channels set: A ({freq_a} MHz, {power_a} dBm, {phase_a}°), B ({freq_b} MHz, {power_b} dBm, {phase_b}°)"
    except Exception as e:
        return f"Error setting both channels: {e}"


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
def handle_disable_output_a(n_clicks):
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
def handle_disable_output_b(n_clicks):
    try:
        hm.windfreak.disable(channel=1)
        return "Channel B output disabled", False, False, False, "primary", "danger"
    except Exception as e:
        return (
            f"Error disabling Channel B: {e}",
            True,
            True,
            True,
            "success",
            "secondary",
        )
