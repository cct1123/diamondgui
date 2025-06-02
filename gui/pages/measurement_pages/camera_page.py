import base64
import threading
import time

import cv2
import dash
import dash_bootstrap_components as dbc
import nidaqmx
import numpy as np
from dash import Input, Output, callback, ctx, dcc, html
from thorlabs_tsi_sdk.tl_camera import TLCameraSDK

dash.register_page(__name__, path="/camera", name="Camera Viewer", icon="fa-camera")


# Shared state with thread-safe access
class CameraState:
    def __init__(self):
        self.frame_data = None
        self.running = False
        self.lock = threading.Lock()
        self.last_frame_time = 0

    def update_frame(self, data):
        with self.lock:
            self.frame_data = data
            self.last_frame_time = time.time()

    def get_frame(self):
        with self.lock:
            return self.frame_data

    def is_running(self):
        with self.lock:
            return self.running

    def set_running(self, running):
        with self.lock:
            self.running = running


camera_state = CameraState()
camera_thread = None


def get_camera_frame():
    global camera_thread
    print("Starting camera thread")
    try:
        with TLCameraSDK() as sdk:
            available_cameras = sdk.discover_available_cameras()
            if not available_cameras:
                print("No cameras found")
                return

            print(f"Found camera: {available_cameras[0]}")
            with sdk.open_camera(available_cameras[0]) as camera:
                print("Camera opened")
                # Configure camera
                camera.roi = (
                    0,
                    0,
                    camera.sensor_width_pixels,
                    camera.sensor_height_pixels,
                )
                camera.exposure_time_us = 10000  # Adjust based on your needs
                camera.frames_per_trigger_zero_for_unlimited = 0
                camera.image_poll_timeout_ms = 1000
                camera.arm(2)
                camera.issue_software_trigger()
                print("Camera armed")

                # Pre-allocate buffers for better performance
                while camera_state.is_running():
                    frame = camera.get_pending_frame_or_null()
                    if frame is None:
                        time.sleep(0.005)  # Small sleep to prevent busy waiting
                        continue

                    # Process frame
                    image_buffer = np.copy(frame.image_buffer)
                    grayscale_img = image_buffer.reshape(
                        camera.image_height_pixels, camera.image_width_pixels
                    )

                    # Optimized conversion
                    if grayscale_img.max() > 0:
                        gray_8bit = cv2.convertScaleAbs(
                            grayscale_img, alpha=(255.0 / grayscale_img.max())
                        )
                    else:
                        gray_8bit = np.zeros_like(grayscale_img, dtype=np.uint8)

                    # Convert to JPEG instead of PNG for smaller size
                    rgb_image = cv2.cvtColor(gray_8bit, cv2.COLOR_GRAY2RGB)
                    _, buffer = cv2.imencode(
                        ".jpg", rgb_image, [int(cv2.IMWRITE_JPEG_QUALITY), 85]
                    )
                    jpg_as_text = base64.b64encode(buffer).decode("utf-8")

                    camera_state.update_frame(jpg_as_text)

    except Exception as e:
        print(f"Camera thread error: {e}")
    finally:
        camera_thread = None


def start_camera():
    global camera_thread
    if not camera_state.is_running():
        camera_state.set_running(True)
        camera_thread = threading.Thread(target=get_camera_frame, daemon=True)
        camera_thread.start()


def stop_camera():
    camera_state.set_running(False)
    if camera_thread:
        camera_thread.join(timeout=1.0)


layout = dbc.Container(
    [
        html.H3("Live Camera Viewer", className="mb-3"),
        html.Div(
            [
                html.Img(
                    id="live-camera-feed",
                    style={"width": "100%", "border": "1px solid #ccc"},
                ),
                dcc.Interval(id="interval-camera", interval=100, n_intervals=0),
            ],
            className="mb-3",
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Button(
                            "Start Camera",
                            id="btn-start-camera",
                            color="success",
                            className="me-2",
                        ),
                        dbc.Button("Stop Camera", id="btn-stop-camera", color="danger"),
                    ]
                ),
                dbc.Col(
                    [
                        html.Div(id="camera-status", className="text-muted"),
                        html.Div(id="fps-counter", className="text-muted"),
                    ],
                    width="auto",
                ),
            ]
        ),
        html.Hr(),
        html.Div(
            [
                html.H5("Voltage Control (NI-DAQmx)", className="mb-2"),
                dcc.Slider(
                    id="voltage-slider",
                    min=0.0,
                    max=5.0,
                    step=0.01,
                    value=0.0,
                    marks={i: f"{i}V" for i in range(6)},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
                html.Div(id="voltage-output", className="mt-2"),
                dbc.Button(
                    "Set to 0V",
                    id="btn-zero-voltage",
                    color="warning",
                    className="mt-2",
                ),
            ],
            className="mb-4",
        ),
    ],
    fluid=True,
)


@callback(
    Output("live-camera-feed", "src"),
    Output("camera-status", "children"),
    Output("fps-counter", "children"),
    Input("interval-camera", "n_intervals"),
)
def update_image(_):
    frame_data = camera_state.get_frame()
    if frame_data:
        fps_text = ""
        if camera_state.last_frame_time > 0:
            fps = (
                1.0 / (time.time() - camera_state.last_frame_time)
                if (time.time() - camera_state.last_frame_time) > 0
                else 0
            )
            fps_text = f"FPS: {fps:.1f}"
        return f"data:image/jpg;base64,{frame_data}", "Camera is streaming", fps_text
    return dash.no_update, dash.no_update, dash.no_update


@callback(
    Output("btn-start-camera", "disabled"),
    Output("btn-stop-camera", "disabled"),
    Input("btn-start-camera", "n_clicks"),
    Input("btn-stop-camera", "n_clicks"),
    prevent_initial_call=True,
)
def control_camera(start_clicks, stop_clicks):
    triggered = ctx.triggered_id
    if triggered == "btn-start-camera":
        start_camera()
        return True, False
    elif triggered == "btn-stop-camera":
        stop_camera()
        return False, True
    return dash.no_update, dash.no_update


# @callback(
#     Output("voltage-output", "children"),
#     Input("voltage-slider", "value"),
#     Input("btn-zero-voltage", "n_clicks"),
#     prevent_initial_call=True,
# )
# def set_voltage(slider_value, zero_clicks):
#     triggered = ctx.triggered_id
#     voltage = 0.0 if triggered == "btn-zero-voltage" else slider_value


#     try:
#         with nidaqmx.Task() as task:
#             task.ao_channels.add_ao_voltage_chan("Dev1/ao0", min_val=0.0, max_val=5.0)
#             task.write(voltage)
#         return f"Voltage set to {voltage:.2f} V"
#     except Exception as e:
#         return f"Error: {str(e)}"
@callback(
    Output("voltage-output", "children"),
    Output("voltage-slider", "value"),
    Input("voltage-slider", "value"),
    Input("btn-zero-voltage", "n_clicks"),
    prevent_initial_call=True,
)
def set_voltage(slider_value, zero_clicks):
    triggered = ctx.triggered_id
    voltage = 0.0 if triggered == "btn-zero-voltage" else slider_value

    try:
        with nidaqmx.Task() as task:
            task.ao_channels.add_ao_voltage_chan("Dev1/ao0", min_val=0.0, max_val=5.0)
            task.write(voltage)
        return f"Voltage set to {voltage:.2f} V", voltage
    except Exception as e:
        return f"Error: {str(e)}", dash.no_update
