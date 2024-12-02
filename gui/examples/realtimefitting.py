import logging
import queue
import threading
import time

import dash
import dash_bootstrap_components as dbc
import dash_daq as daq
import numpy as np
import plotly.graph_objs as go
from dash import Input, Output, State, callback, dcc, html
from scipy.optimize import curve_fit

logger = logging.getLogger(__name__)

BOUNDS_SINE_GAUSSIAN_DECAY = (
    [-np.inf, 0, -np.pi, 0, -np.inf, 0, -np.inf],
    [np.inf, np.inf, np.pi, np.inf, np.inf, np.inf, np.inf],
)


def format_param(param, uncert):
    # Check if uncertainty is a valid number (not infinity or NaN)
    if np.isinf(uncert) or np.isnan(uncert):
        return f"{param:.2f}"  # Return parameter with default formatting if uncertainty is invalid

    # Calculate the number of significant figures based on the uncertainty
    sig_figs = -int(np.floor(np.log10(abs(uncert))))  # How many decimal places to keep
    sig_figs = max(sig_figs, 1)  # Ensure at least 1 decimal place

    try:
        return f"{param:.{sig_figs}f}"
    except ValueError:
        # If there's an error in formatting, return the parameter as a string with a fallback format
        return str(param)


# Define the sine with Gaussian decay model
def model_sine_gaussian_decay(t, A, f, phi, tau, B, tau_b, C):
    return (
        A * np.sin(2 * np.pi * f * t + phi) * np.exp(-((t / tau) ** 2))
        + B * np.exp(-((t / tau_b) ** 2))
        + C
    )


# Parameter estimation method
def estimator_sine_gassian_decay(t, y):
    """
    Estimate initial parameters for the sine with Gaussian decay fit.
    :param t: Independent variable (e.g., mw_dur)
    :param y: Dependent variable (e.g., contrast)
    :return: Initial guesses for A, f, phi, tau, B, tau_b, C
    """
    # Estimate amplitude (A) as half the range of y
    A = (np.max(y) - np.min(y)) / 2

    # Estimate frequency (f) using FFT
    fft_freqs = np.fft.fftfreq(len(t), d=(t[1] - t[0]))
    fft_magnitude = np.abs(np.fft.fft(y - np.mean(y)))  # Remove DC component
    f = np.abs(fft_freqs[np.argmax(fft_magnitude[1:]) + 1])  # Dominant frequency
    # Phase (phi) can start at zero
    phi = 0
    # Estimate tau as a fraction of the total duration
    tau = (t[-1] - t[0]) / 3
    # Estimate background amplitude (B) and decay (tau_b)
    # print(type(y < np.median(y)))
    # print(y < np.median(y))
    try:
        B = np.mean(y[(y < np.median(y))])  # Lower half average as baseline
    except Exception as e:
        print(e)
        y = np.array(y)
        B = np.mean(y[(y < np.median(y))])
    tau_b = tau * 2  # Assume background decays slower than sine
    # Flat background offset (C) as the mean of the data
    C = np.mean(y)

    return [A, f, phi, np.abs(tau), B, np.abs(tau_b), C]


# Stoppable Daemon Thread class
class StoppableDaemonThread(threading.Thread):
    def __init__(
        self, group=None, target=None, name=None, args=(), kwargs=None, *, daemon=True
    ):
        self._refresh_interval = 0.1
        self.stop_event = threading.Event()
        self.result_queue = queue.Queue()
        self.args_daemon = args
        self.target_daemon = target
        super().__init__(
            group=group, target=self._run, name=name, kwargs=kwargs, daemon=daemon
        )

    def set_refresh(self, interval=0.1):
        self._refresh_interval = interval

    def _run(self):
        while not self.stop_event.is_set():
            result = self.target_daemon(*self.args_daemon)
            if result is not None:
                self.result_queue.put(result)
            time.sleep(self._refresh_interval)

    def start(self):
        super().start()

    def stop(self):
        self.stop_event.set()
        # super().join()

    def get_one(self):
        if not self.result_queue.empty():
            return self.result_queue.get_nowait()
        return None

    def get_all(self):
        return [self.result_queue.get() for _ in range(self.result_queue.qsize())]

    def get_last(self):
        all_result = [self.result_queue.get() for _ in range(self.result_queue.qsize())]
        if len(all_result) == 0:
            return None
        return all_result[-1]


# Fitting thread instance
class CurveFitting:
    def __init__(self, stream, axes, model, estimator, bonds=None, **kwargs):
        self.stream = stream
        self.axes = axes
        self.model = model
        self.estimator = estimator
        self.bounds = bonds
        self.fit_thread = None
        self.fit_results = None
        # self.fitted = False

    def fit_data(self):
        data = self.stream.get_dataset()
        tt = data[self.axes[0]]
        yy = data[self.axes[1]]
        # print(tt, yy)

        try:
            # Estimate initial parameters
            # if self.fitted:
            #     initial_guess = self.fit_results["fit_params"]
            # else:
            #     self.fit_results = None
            #     initial_guess = self.estimator(tt, yy)
            fit_results = None
            initial_guess = self.estimator(tt, yy)

            # Curve fitting
            params, covariance = curve_fit(
                self.model,
                tt,
                yy,
                p0=initial_guess,
                bounds=self.bounds,
                method="trf",
            )

            fit_results = {
                "fit_params": params.tolist(),
                "fit_uncert": np.sqrt(np.diag(covariance)).tolist(),
            }
            # self.fitted = True
        except Exception as e:
            logger.info(f"Error fitting data: {e}")
        return fit_results

    def start(self):
        # self.fitted = False
        self.fit_thread = StoppableDaemonThread(target=self.fit_data, name="FitThread")
        self.fit_thread.set_refresh(0.01)
        self.fit_thread.start()

    def is_running(self):
        return self.fit_thread is not None

    def stop(self):
        if self.fit_thread:
            self.fit_thread.stop()
            self.fit_thread = None

    def get_last(self):
        return self.fit_thread.get_last()

    def get_all(self):
        return self.fit_thread.get_all()


# Data generation function
class FakeDataGenerator:
    def __init__(self):
        self.data_buffer = None
        self.daemon_thread = StoppableDaemonThread(target=self.generate_fake_data)
        self.daemon_thread.set_refresh(0.01)

    def start(self):
        self.daemon_thread.start()

    def stop(self):
        self.daemon_thread.stop()

    def generate_fake_data(self):
        t = np.linspace(0, 6, 200)
        A, f, phi, tau, B, tau_b, C = 4, 1, 0, 3, 6.0, 3, 0.1

        noise_floor = np.random.normal(0, 0.8, size=t.shape)
        noise_freq = 1 + 0.4 * np.sin(time.time() / 4.0 * 2 * np.pi)
        y = (
            model_sine_gaussian_decay(t, A, f * noise_freq, phi, tau, B, tau_b, C)
            + noise_floor
        )
        self.data_buffer = {"time": t, "signal": y}
        time.sleep(0.05)

    def get_dataset(self):
        return self.data_buffer


# Fake Data Generator instance
fake_data_generator = FakeDataGenerator()
fake_data_generator.start()
fake_fitting = CurveFitting(
    fake_data_generator,
    ["time", "signal"],
    model_sine_gaussian_decay,
    estimator_sine_gassian_decay,
    BOUNDS_SINE_GAUSSIAN_DECAY,
)

# ===============================================================================
# GUI
# ===============================================================================
# Layout of the GUI
DATA_INTERVAL = 100
layout_realtimefitting = html.Div(
    [
        dcc.Graph(id="live-graph"),
        dcc.Interval(id="interval-component", interval=DATA_INTERVAL, n_intervals=0),
        dbc.Checklist(
            id="fit-toggle",
            options=[{"label": "Enable Curve Fitting", "value": "fit"}],
            value=[],  # The checkbox is unchecked by default
        ),
        dcc.Store(id="data-store", data={"time": [], "signal": [], "fit_signal": []}),
        html.Div(
            id="fit-parameters-display", style={"whiteSpace": "pre-line"}
        ),  # For displaying fitted parameters and uncertainties
        html.Div(
            daq.LEDDisplay(
                id="frequency-led-display",
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
    ]
)


# Callback to update the data store
@callback(
    Output("data-store", "data"),
    Input("interval-component", "n_intervals"),
    State("fit-toggle", "value"),
)
def update_data_store(n_intervals, fit_enabled):
    result = fake_data_generator.get_dataset()
    # If new data is available
    if result:
        if "fit" in fit_enabled:
            if not fake_fitting.is_running():
                logger.info("Starting fitting thread")
                fake_fitting.start()

            fit_result = fake_fitting.get_last()

            if fit_result:
                return {
                    "time": result["time"],
                    "signal": result["signal"],
                    "fit_params": fit_result["fit_params"],
                    "fit_uncert": fit_result["fit_uncert"],
                }
        else:
            # Stop the fitting thread if unchecked
            if fake_fitting.is_running():
                logger.info("Stopping fitting thread")
                fake_fitting.stop()
            return {
                "time": result["time"],
                "signal": result["signal"],
                "fit_params": None,
                "fit_uncert": None,
            }
    return dash.no_update


# Callback to update the fitted parameters and their uncertainties display
@callback(
    Output("fit-parameters-display", "children"),
    Output("frequency-led-display", "value"),
    [
        Input("data-store", "data"),
        Input("fit-toggle", "value"),
    ],  # Listen for checkbox value
)
def update_fit_parameters(data, fit_enabled):
    # Only show parameters when fitting is enabled (checkbox is checked)
    if (
        "fit_params" in data
        and data["fit_params"]
        and "fit_uncert" in data
        and "fit" in fit_enabled
    ):
        params = data["fit_params"]
        uncert = data["fit_uncert"]
        freq_formatted = format_param(params[1], uncert[1])
        # Format fitted parameters and their uncertainties into a readable string
        param_str = (
            f"Amplitude (A): {format_param(params[0], uncert[0])} ± {format_param(uncert[0], uncert[0])}\n"
            f"Frequency (f): {freq_formatted} ± {format_param(uncert[1], uncert[1])}\n"
            f"Phase (phi): {format_param(params[2], uncert[2])} ± {format_param(uncert[2], uncert[2])}\n"
            f"Decay Tau (tau): {format_param(params[3], uncert[3])} ± {format_param(uncert[3], uncert[3])}\n"
            f"Background (B): {format_param(params[4], uncert[4])} ± {format_param(uncert[4], uncert[4])}\n"
            f"Background Decay (tau_b): {format_param(params[5], uncert[5])} ± {format_param(uncert[5], uncert[5])}\n"
            f"Offset (C): {format_param(params[6], uncert[6])} ± {format_param(uncert[6], uncert[6])}"
        )
        return f"Fitted Parameters:\n{param_str}", freq_formatted

    # If checkbox is not checked or no fit data is available, return nothing
    return "", "0.0"


# Callback to update the graph
@callback(
    Output("live-graph", "figure"),
    Input("data-store", "data"),
    State("fit-toggle", "value"),
)
def update_graph(data, fit_enabled):
    traces = [
        go.Scattergl(
            x=data["time"],
            y=data["signal"],
            mode="lines+markers",
            name="Raw Data",
            # visible="legendonly",
        )
    ]
    if "fit" in fit_enabled and data["fit_params"]:
        fit_xx = np.linspace(data["time"][0], data["time"][-1], len(data["time"]) * 4)
        fit_signal = fake_fitting.model(fit_xx, *data["fit_params"])
        traces.append(
            go.Scattergl(
                x=fit_xx,
                y=fit_signal,
                mode="lines",
                name="Fit Result",
            )
        )
    return {
        "data": traces,
        "layout": go.Layout(
            title="Real-time Data with Fitting",
            xaxis=dict(title="Time"),
            yaxis=dict(title="Signal"),
        ),
    }


# Run the app
if __name__ == "__main__":
    # Initialize Dash app
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SKETCHY])
    app.layout = layout_realtimefitting
    app.run_server(debug=True)
