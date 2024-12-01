import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

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
    B = np.mean(y[y < np.median(y)])  # Lower half average as baseline
    tau_b = tau * 2  # Assume background decays slower than sine

    # Flat background offset (C) as the mean of the data
    C = np.mean(y)

    return [A, f, phi, np.abs(tau), B, np.abs(tau_b), C]


# Fit the data
def fit_sine_gaussian_decay(tt, yy):
    # Estimate initial parameters
    initial_guess = estimator_sine_gassian_decay(tt, yy)

    # Curve fitting
    params, covariance = curve_fit(
        model_sine_gaussian_decay,
        tt,
        yy,
        p0=initial_guess,
        bounds=BOUNDS_SINE_GAUSSIAN_DECAY,
    )

    return params, np.sqrt(np.diag(covariance))  # Return parameters and uncertainties


# ==============================================================================
# Lorentzian model with flat background
# ==============================================================================


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


if __name__ == "__main__":
    # Example usage
    # Assuming mw_dur and contrast are your data arrays
    mw_dur = np.linspace(0, 3500)
    contrast = (
        model_sine_gaussian_decay(
            mw_dur,
            *[
                7.31220714e-04,
                5.88768238e-04,
                2.47215447e00,
                1.54081029e03,
                1.02436466e-03,
                7.19224733e02,
                -1.47814081e-03,
            ],
        )
        + np.random.randn(len(mw_dur)) * 1e-04
    )

    params, uncertainties = fit_sine_gaussian_decay(mw_dur, contrast)

    # Extract parameters
    A, f, phi, tau, B, tau_b, C = params
    print("Fitted Parameters:")
    print(f"A (Amplitude): {A*100.0:.3f}%")
    print(f"f (Frequency): {f*1e3:.2f} MHz")
    print(f"phi (Phase): {phi:.1f} rad")
    print(f"tau (Gaussian decay for sine): {tau:.1f} ns")
    print(f"B (Background amplitude): {B*100.0:.3f} %")
    print(f"tau_b (Gaussian decay for background): {tau_b:.1f} ns")
    print(f"C (Flat background offset): {C*100.0:.3f} %")

    # Generate fitted curve
    fitted_contrast = model_sine_gaussian_decay(mw_dur, *params)

    # Plot the original data and fitted curve
    plt.figure(figsize=(8, 5))
    plt.plot(mw_dur, contrast * 100.0, "o", label="Data", markersize=4)
    plt.plot(mw_dur, fitted_contrast * 100.0, "-", label="Fitted Curve", color="red")
    plt.xlabel("MW time [ns]")
    plt.ylabel("Contrast [%]")
    plt.title("Fitted Sine with Gaussian Decay and Flat Background")
    plt.legend()
    plt.show()

    # Example usage
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
    print(f"A (Amplitude): {A*1e6:.3f} ± {u_A*1e6:.3f} µV")
    print(f"f0 (Center Frequency): {f0:.4f} ± {u_f0:.4f} GHz")
    print(f"Gamma (HWHM): {Gamma*1e3:.3f} ± {u_Gamma*1e3:.3f} MHz")
    print(f"C (Flat background): {C*1e6:.3f} ± {u_C*1e6:.3f} µV")

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
