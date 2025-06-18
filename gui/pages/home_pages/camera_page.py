import time

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, callback, ctx, dcc, html

from hardware.hardwaremanager import HardwareManager

ID = "cameraviewer-"
hw = HardwareManager()

layout_camera = dbc.Container(
    [
        dbc.Card(
            [
                dbc.CardHeader("Camera Viewer"),
                dbc.CardBody(
                    [
                        html.Div(
                            html.Img(
                                id=ID + "live-camera-feed",
                                style={
                                    "width": "100%",
                                    "border": "1px solid #ccc",
                                    "borderRadius": "8px",
                                    "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
                                },
                            ),
                            style={"overflow": "hidden"},
                        ),
                        dcc.Interval(
                            id=ID + "interval-camera", interval=100, n_intervals=0
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Button(
                                        "Start Camera",
                                        id=ID + "btn-start-camera",
                                        color="success",
                                        className="me-2",
                                        size="sm",
                                    ),
                                    width="auto",
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "Stop Camera",
                                        id=ID + "btn-stop-camera",
                                        color="danger",
                                        size="sm",
                                    ),
                                    width="auto",
                                ),
                                dbc.Col(
                                    html.Div(
                                        id=ID + "camera-status",
                                        className="text-muted",
                                    ),
                                    width="auto",
                                ),
                                dbc.Col(
                                    html.Div(
                                        id=ID + "fps-counter",
                                        className="text-muted",
                                    ),
                                    width="auto",
                                ),
                            ],
                            className="mt-3",
                            justify="start",
                            align="center",
                        ),
                        html.Hr(),
                        html.H6("Brightness Control", className="mt-3"),
                        dcc.Slider(
                            id=ID + "voltage-slider",
                            min=0.0,
                            max=5.0,
                            step=0.01,
                            value=0.0,
                            marks={i: f"{i}V" for i in range(6)},
                            tooltip={"placement": "bottom", "always_visible": True},
                        ),
                        html.Div(id=ID + "voltage-output", className="mt-2"),
                        dcc.Store(id=ID + "stored-voltage", storage_type="memory"),
                    ]
                ),
            ],
            className="mt-4 mb-4",
        )
    ],
    fluid=True,
)


# ---------------- Callback Definitions ---------------- #


@callback(
    Output(ID + "live-camera-feed", "src"),
    Output(ID + "camera-status", "children"),
    Output(ID + "fps-counter", "children"),
    Input(ID + "interval-camera", "n_intervals"),
)
def update_image(_):
    frame_data = hw.camera.get_frame()
    if frame_data:
        last_time = hw.camera.last_frame_time
        fps = 1.0 / (time.time() - last_time) if (time.time() - last_time) > 0 else 0
        return (
            f"data:image/jpg;base64,{frame_data}",
            "Camera is streaming",
            f"FPS: {fps:.1f}",
        )
    return dash.no_update, dash.no_update, dash.no_update


@callback(
    Output(ID + "btn-start-camera", "disabled"),
    Output(ID + "btn-stop-camera", "disabled"),
    Input(ID + "btn-start-camera", "n_clicks"),
    Input(ID + "btn-stop-camera", "n_clicks"),
    prevent_initial_call=True,
)
def control_camera(start_clicks, stop_clicks):
    triggered = ctx.triggered_id
    if triggered == ID + "btn-start-camera":
        hw.camera.start()
        return True, False
    elif triggered == ID + "btn-stop-camera":
        hw.camera.stop()
        return False, True
    return dash.no_update, dash.no_update


@callback(
    Output(ID + "voltage-slider", "value"),
    Output(ID + "voltage-output", "children"),
    Output(ID + "stored-voltage", "data"),
    Input(ID + "voltage-slider", "value"),
    Input(ID + "stored-voltage", "data"),
    prevent_initial_call=False,
)
def sync_and_set_voltage(slider_value, stored_voltage):
    triggered = ctx.triggered_id

    # First page load or reload
    if triggered is None or triggered == ID + "stored-voltage":
        voltage = stored_voltage if stored_voltage is not None else 0.0
        # restore device state
        hw.whitelight.set_voltage(voltage)
        return voltage, f"Restored voltage: {voltage:.2f} V", voltage

    # User moved slider
    voltage = slider_value if slider_value is not None else 0.0

    try:
        hw.whitelight.set_voltage(voltage)
        return voltage, f"Voltage set to {voltage:.2f} V", voltage
    except Exception as e:
        return dash.no_update, f"Error: {e}", stored_voltage
