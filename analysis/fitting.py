import queue
import threading
import time

import numpy as np
from scipy.optimize import curve_fit


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
    # for real time curve fitting using data stream
    def __init__(
        self, stream, model, estimator, axes=["xx", "yy"], bonds=None, **kwargs
    ):
        self.stream = stream
        self.axes = axes
        self.model = model
        self.estimator = estimator
        self.bounds = bonds
        self.fit_thread = None
        self.fit_results = None
        self.buffer_last = None
        # self.fitted = False

    def data_stream(self):
        data = self.stream.get_dataset()
        return data[self.axes[0]], data[self.axes[1]]

    def fit_data(self):
        tt, yy = self.data_stream()

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
                bounds=self.bounds if self.bounds else (-np.inf, np.inf),
                method="trf",
            )

            fit_results = {
                "params": params.tolist(),
                "uncert": np.sqrt(np.diag(covariance)).tolist(),
            }
            # self.fitted = True
        except Exception as e:
            print(f"Error fitting data: {e}")
        return fit_results

    def start(self):
        # self.fitted = False
        self.buffer_last = None
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
        last = self.fit_thread.get_last()
        if last:
            self.buffer_last = last
        return self.buffer_last

    def get_all(self):
        return self.fit_thread.get_all()


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


# ==============================================================================
# Sine with Gaussian decays and flat background
# ==============================================================================
BOUNDS_SINE_GAUSSIAN_DECAY = (
    [-np.inf, 0, -np.pi, 0, -np.inf, 0, -np.inf],
    [np.inf, np.inf, np.pi, np.inf, np.inf, np.inf, np.inf],
)


# Define the model: Sine with Gaussian decay and flat background
def model_sine_gaussian_decay(t, A, f, phi, tau, B, tau_b, C):
    """
    Sine with Gaussian decay and a flat background.
    :param t: Time (mw_dur)
    :param A: Amplitude of the sine wave
    :param f: Frequency of the sine wave
    :param phi: Phase of the sine wave
    :param tau: Gaussian decay constant for the sine wave
    :param B: Background amplitude
    :param tau_b: Gaussian decay constant for the background
    :param C: Flat background offset
    """
    return (
        A * np.sin(2 * np.pi * f * t + phi) * np.exp(-(t / tau))
        + B * np.exp(-(t / tau_b))
        + C
    )


# Parameter estimation method
def estimator_sine_gaussian_decay(t, y):
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
    B = np.mean(y[y < np.median(y)])  # Lower half average as baseline
    tau_b = tau * 2  # Assume background decays slower than sine

    # Flat background offset (C) as the mean of the data
    C = np.mean(y)

    return [A, f, phi, np.abs(tau), B, np.abs(tau_b), C]


# Fit the data
def fit_sine_gaussian_decay(tt, yy):
    # Estimate initial parameters
    initial_guess = estimator_sine_gaussian_decay(tt, yy)

    # Curve fitting
    params, covariance = curve_fit(
        model_sine_gaussian_decay,
        tt,
        yy,
        p0=initial_guess,
        bounds=BOUNDS_SINE_GAUSSIAN_DECAY,
    )

    return params, np.sqrt(np.diag(covariance))  # Return parameters and uncertainties


BOUNDS_COS_GAUSSIAN_DECAY = (
    [-np.inf, 0, 0, -np.inf, 0, -np.inf],
    [np.inf, np.inf, np.inf, np.inf, np.inf, np.inf],
)


def model_cos_gaussian_decay(t, A, f, tau, B, tau_b, C):
    return model_sine_gaussian_decay(t, A, f, np.pi / 2.0, tau, B, tau_b, C)


def estimator_cos_gaussian_decay(tt, yy):
    guess = estimator_sine_gaussian_decay(tt, yy)
    guess.pop(2)  # remove the phase
    return guess


def fit_cos_gaussian_decay(tt, yy):
    # Estimate initial parameters
    initial_guess = estimator_cos_gaussian_decay(tt, yy)

    # Curve fitting
    params, covariance = curve_fit(
        model_cos_gaussian_decay,
        tt,
        yy,
        p0=initial_guess,
    )

    return params, np.sqrt(np.diag(covariance))  # Return parameters and uncertainties


# ==============================================================================
# Lorentzian model with flat background
# ==============================================================================
BOUNDS_LORENTZIAN = (
    [-np.inf, 0, 0, -np.inf],
    [np.inf, np.inf, np.inf, np.inf],
)


# Define the Lorentzian model with a flat background
def model_lorentzian(freq, A, f0, Gamma, C):
    """
    Lorentzian model with a flat background.
    :param freq: Frequency array
    :param A: Amplitude of the Lorentzian (can be positive or negative)
    :param f0: Center frequency
    :param Gamma: Half-width at half-maximum (HWHM)
    :param C: Flat background offset
    """
    return A * (Gamma**2 / ((freq - f0) ** 2 + Gamma**2)) + C


# Estimator for initial parameters
def estimator_lorentzian(freq, sig):
    """
    Estimate initial parameters for the Lorentzian model.
    :param freq: Frequency array
    :param sig: Signal array
    :return: Initial guesses for A, f0, Gamma, and C
    """
    # Estimate flat background (C) as the median of the signal
    C = np.median(sig)

    # Estimate amplitude (A) as the difference between the max and min signal
    A = np.max(sig) - np.min(sig)

    # Estimate center frequency (f0) as the frequency corresponding to the maximum absolute deviation
    f0 = freq[np.argmax(np.abs(sig - C))]

    # Estimate Gamma as the range where the signal drops to half the peak
    half_max = np.abs(A) / 2
    near_peak = np.abs(sig - C) > half_max
    if np.sum(near_peak) > 1:
        Gamma = (freq[near_peak][-1] - freq[near_peak][0]) / 2
    else:
        Gamma = (freq[-1] - freq[0]) / 10  # Default guess for Gamma

    return [A, f0, np.abs(Gamma), C]


# Fit the Lorentzian model
def fit_lorentzian(xx, yy):
    # Estimate initial parameters
    initial_guess = estimator_lorentzian(xx, yy)

    # Curve fitting
    params, covariance = curve_fit(model_lorentzian, xx, yy, p0=initial_guess)

    return params, np.sqrt(np.diag(covariance))  # Return parameters and uncertainties


# ==============================================================================
# Gaussian model with flat background
# ==============================================================================
# Define bounds for the Gaussian fit
BOUNDS_GAUSSIAN = (
    [-np.inf, 0, 0, -np.inf],
    [np.inf, np.inf, np.inf, np.inf],
)


# Define the Gaussian model with a flat background
def model_gaussian(freq, A, f0, sigma, C):
    """
    Gaussian model with a flat background.
    :param freq: Frequency array
    :param A: Amplitude of the Gaussian (can be positive or negative)
    :param f0: Center frequency
    :param sigma: Standard deviation (related to width)
    :param C: Flat background offset
    """
    return A * np.exp(-0.5 * ((freq - f0) / sigma) ** 2) + C


# Estimator for initial parameters
def estimator_gaussian(freq, sig):
    """
    Estimate initial parameters for the Gaussian model.
    :param freq: Frequency array
    :param sig: Signal array
    :return: Initial guesses for A, f0, sigma, and C
    """
    # Estimate flat background (C) as the median of the signal
    C = np.median(sig)

    # Estimate amplitude (A) as the difference between the max and min signal
    A = np.max(sig) - np.min(sig)

    # Estimate center frequency (f0) as the frequency corresponding to the maximum absolute deviation
    f0 = freq[np.argmax(np.abs(sig - C))]

    # Estimate sigma as the range where the signal drops to ~37% (1/e) of the peak
    peak_index = np.argmax(np.abs(sig - C))
    half_max = np.abs(A) / np.exp(1)
    near_peak = np.abs(sig - C) > half_max
    if np.sum(near_peak) > 1:
        sigma = (freq[near_peak][-1] - freq[near_peak][0]) / (
            2 * np.sqrt(2 * np.log(2))
        )  # Convert FWHM to sigma
    else:
        sigma = (freq[-1] - freq[0]) / 10  # Default guess for sigma

    return [A, f0, np.abs(sigma), C]


# Fit the Gaussian model
def fit_gaussian(xx, yy):
    """
    Fit the Gaussian model to the data.
    :param xx: Frequency array
    :param yy: Signal array
    :return: Fitted parameters and uncertainties
    """
    # Estimate initial parameters
    initial_guess = estimator_gaussian(xx, yy)

    # Curve fitting
    params, covariance = curve_fit(
        model_gaussian, xx, yy, p0=initial_guess, bounds=BOUNDS_GAUSSIAN
    )

    return params, np.sqrt(np.diag(covariance))  # Return parameters and uncertainties


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    # Example usage for cosine Gaussian decay==============================================================
    # Assuming mw_dur and contrast are your data arrays
    mw_dur = np.linspace(0, 3500, 100)
    contrast = (
        model_cos_gaussian_decay(
            mw_dur,
            *[
                7.31220714e-04,
                5.88768238e-04,
                # 2.47215447e00,
                1.54081029e03,
                1.02436466e-03,
                7.19224733e02,
                -1.47814081e-03,
            ],
        )
        + np.random.randn(len(mw_dur)) * 1e-04
    )

    params, uncertainties = fit_cos_gaussian_decay(mw_dur, contrast)

    # Extract parameters
    A, f, tau, B, tau_b, C = params
    print("Fitted Parameters:")
    print(f"A (Amplitude): {A * 100.0:.3f}%")
    print(f"f (Frequency): {f * 1e3:.2f} MHz")
    # print(f"phi (Phase): {phi:.1f} rad")
    print(f"tau (Gaussian decay for sine): {tau:.1f} ns")
    print(f"B (Background amplitude): {B * 100.0:.3f} %")
    print(f"tau_b (Gaussian decay for background): {tau_b:.1f} ns")
    print(f"C (Flat background offset): {C * 100.0:.3f} %")

    # Generate fitted curve
    fitted_contrast = model_cos_gaussian_decay(mw_dur, *params)

    # Plot the original data and fitted curve
    plt.figure(figsize=(8, 5))
    plt.plot(mw_dur, contrast * 100.0, "o", label="Data", markersize=4)
    plt.plot(mw_dur, fitted_contrast * 100.0, "-", label="Fitted Curve", color="red")
    plt.xlabel("MW time [ns]")
    plt.ylabel("Contrast [%]")
    plt.title("Fitted Cosine with Gaussian Decay and Flat Background")
    plt.legend()
    plt.show()
    # =========================================================================================================

    # Example usage for Lorentzian=============================================================================

    # Assuming freq and sig_diff are your data arrays
    freq = np.linspace(398.5, 398.6, 100)
    sig_diff = (
        model_lorentzian(
            freq, -1.15234127e-04, 3.98556462e02, 4.02208642e-03, 0.026600881e-04
        )
        + np.random.randn(len(freq)) * 1e-05
    )
    params, uncertainties = fit_lorentzian(freq, sig_diff)

    # Extract parameters
    A, f0, Gamma, C = params
    u_A, u_f0, u_Gamma, u_C = uncertainties

    # Print fitted parameters with uncertainties
    print("Fitted Parameters and Uncertainties:")
    print(f"A (Amplitude): {A * 1e6:.3f} ± {u_A * 1e6:.3f} µV")
    print(f"f0 (Center Frequency): {f0:.4f} ± {u_f0:.4f} GHz")
    print(f"Gamma (HWHM): {Gamma * 1e3:.3f} ± {u_Gamma * 1e3:.3f} MHz")
    print(f"C (Flat background): {C * 1e6:.3f} ± {u_C * 1e6:.3f} µV")

    # Generate fitted curve
    fitted_signal = model_lorentzian(freq, *params)

    # Plot the original data and fitted curve
    plt.figure(figsize=(8, 5))
    plt.plot(freq, sig_diff * 1e6, "o", label="Data", markersize=4)
    plt.plot(freq, fitted_signal * 1e6, "-", label="Fitted Curve", color="red")
    plt.xlabel("Frequency [GHz]")
    plt.ylabel("Differential Signal [uV]")
    plt.title("Fitted Lorentzian Model with Flat Background")
    plt.legend()
    plt.show()

    # =========================================================================================================

    # Example usage for Gaussian===============================================================================
    # Generate synthetic Gaussian data
    freq = np.linspace(0, 100, 500)
    true_params = [10, 50, 5, 2]  # A, f0, sigma, C
    signal = -model_gaussian(freq, *true_params) + np.random.normal(0, 0.5, freq.size)

    # Fit the synthetic data
    fitted_params, uncertainties = fit_gaussian(freq, signal)

    print("Fitted parameters:", fitted_params)
    print("Uncertainties:", uncertainties)

    # Plot the results
    import matplotlib.pyplot as plt

    plt.plot(freq, signal, label="Data", linestyle="dotted")
    plt.plot(freq, model_gaussian(freq, *fitted_params), label="Fit", color="red")
    plt.legend()
    plt.xlabel("Frequency")
    plt.ylabel("Signal")
    plt.title("Gaussian Fit")
    plt.show()
    # =========================================================================================================
