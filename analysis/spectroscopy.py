import numpy as np
from scipy.optimize import curve_fit, minimize


# Define a helper function for FFT calculation ---------------------------------------------------------
# -------------------------------------------------------------------------------
def calculate_fft_abs(signal_avg, tau_array, DCfilter=True):
    N = len(signal_avg)
    try:
        T = tau_array[1] - tau_array[0]  # Sample spacing
    except IndexError:
        print(
            "Warning: tau_array might not have enough points to determine sample spacing. Assuming T=1."
        )
        T = 1.0  # Default to 1 if not enough points

    # Remove DC component (mean) before FFT
    if DCfilter:
        yf = np.fft.fft(signal_avg - np.mean(signal_avg))
    else:
        yf = np.fft.fft(signal_avg)
    xf = np.fft.fftfreq(N, T)[: N // 2] * 1e9

    # Amplitude normalization
    amplitude = 2.0 / N * np.abs(yf[0 : N // 2]) * 1e3  # mV
    return xf, amplitude


def calculate_fft(signal_avg, tau_array, DCfilter=True):
    N = len(signal_avg)
    try:
        T = tau_array[1] - tau_array[0]  # Sample spacing
    except IndexError:
        print(
            "Warning: tau_array might not have enough points to determine sample spacing. Assuming T=1."
        )
        T = 1.0  # Default to 1 if not enough points

    # Remove DC component (mean) before FFT
    if DCfilter:
        yf = np.fft.fft(signal_avg - np.mean(signal_avg))
    else:
        yf = np.fft.fft(signal_avg)
    xf = np.fft.fftfreq(N, T)[: N // 2] * 1e9

    # Amplitude normalization
    yf = 2.0 / N * yf[0 : N // 2] * 1e3  # mV
    return xf, yf


# filter data in time domain ------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------
def stretched_triple_exponential(
    t, A1, tau1, beta1, A2, tau2, beta2, A3, tau3, beta3, C
):
    """
    Defines a triple stretched exponential function. This provides maximum
    flexibility for fitting complex multi-stage rise dynamics.

    Args:
        t (np.array): The time data.
        A1, A2, A3 (float): Amplitudes of the components.
        tau1, tau2, tau3 (float): Time constants of the components.
        beta1, beta2, beta3 (float): Stretch factors for each component.
        C (float): The vertical offset.

    Returns:
        np.array: The calculated values of the function.
    """
    component1 = A1 * (1 - np.exp(-((t / tau1) ** beta1)))
    component2 = A2 * (1 - np.exp(-((t / tau2) ** beta2)))
    component3 = A3 * (1 - np.exp(-((t / tau3) ** beta3)))
    return component1 + component2 + component3 + C


def filter_rising_background(time_data, signal_data):
    """
    Filters a signal by fitting a triple stretched exponential function to a
    corresponding background signal and subtracting the fit.

    Args:
        time_data (np.array): The array of time points for the signals.
        signal_data (np.array): The primary signal containing the oscillations
                                and the rising background.

    Returns:
        np.array: The filtered signal, with the rising trend removed.
        np.array: The fitted background curve.
    """
    # Initial guesses: [A1, tau1, beta1, A2, tau2, beta2, A3, tau3, beta3, C].
    total_amplitude = np.max(signal_data) - np.min(signal_data)
    initial_guesses = [
        total_amplitude * 0.53,
        1e6,
        1.0,  # Component 1 (fast)
        total_amplitude * 0.23,
        2e7,
        1.0,  # Component 2 (medium)
        total_amplitude * 0.23,
        1e8,
        1.0,  # Component 3 (slow)
        np.min(signal_data),  # C
    ]

    # Define bounds for the parameters. Constrain beta between 0 and 1.
    lower_bounds = [0, 0, 0, 0, 0, 0, 0, 0, 0, -np.inf]
    upper_bounds = [
        np.inf,
        np.inf,
        3.0,
        np.inf,
        np.inf,
        3.0,
        np.inf,
        np.inf,
        3.0,
        np.inf,
    ]
    bounds = (lower_bounds, upper_bounds)

    try:
        popt, pcov = curve_fit(
            stretched_triple_exponential,
            time_data,
            signal_data,
            p0=initial_guesses,
            bounds=bounds,
            maxfev=30000,  # Increased iterations for a very complex fit
            # method="trf"
        )

        print("Fit successful. Parameters:")
        print(f"  A1={popt[0]:.4f}, tau1={popt[1]:.2e}, beta1={popt[2]:.3f}")
        print(f"  A2={popt[3]:.4f}, tau2={popt[4]:.2e}, beta2={popt[5]:.3f}")
        print(f"  A3={popt[6]:.4f}, tau3={popt[7]:.2e}, beta3={popt[8]:.3f}")
        print(f"  C={popt[9]:.4f}")

        fitted_background = stretched_triple_exponential(time_data, *popt)
        filtered_signal = signal_data - fitted_background

        return filtered_signal, fitted_background

    except RuntimeError as e:
        print(f"Error: Curve fitting failed. {e}")
        return None, None


# ----------------------------------------------------------------------------------------------------


# Apodization functions ---------------------------------------------------------
# -------------------------------------------------------------------------------
def apply_sine_bell_window(t, fid):
    """
    Applies a sine-bell window function to an FID.

    This is ideal for FIDs that are truncated (do not decay to zero by the
    end of the acquisition), as it smoothly tapers the signal to zero at
    both ends, preventing truncation artifacts (sinc wiggles) in the spectrum.

    Args:
        t (np.ndarray): The time vector for the FID in nanoseconds.
        fid (np.ndarray): The Free Induction Decay (time-domain signal).

    Returns:
        np.ndarray: The FID after applying the sine-bell window.
    """
    print("Applying sine-bell window for truncated FID...")
    n_points = len(fid)
    # Create a sine function that goes from 0 to pi over the acquisition time
    sine_window = np.sin(np.linspace(0, np.pi, n_points))

    windowed_fid = fid * sine_window
    return windowed_fid


def apply_sigmoid_window(t, fid, transition_ratio=0.1, steepness_param=6.0):
    """
    Applies a sigmoid window to both ends of an FID.

    This provides a very smooth taper to zero, which is useful for truncated
    FIDs. The shape of the taper can be controlled.

    Args:
        t (np.ndarray): The time vector for the FID in nanoseconds.
        fid (np.ndarray): The Free Induction Decay (time-domain signal).
        transition_ratio (float): Fraction of the signal at each end to apply
                                  the window to (e.g., 0.1 for 10%).
        steepness_param (float): Controls how sharp the sigmoid transition is.
                                 A value of 12 means the transition happens
                                 over a standard range for the exp function.
                                 Higher values make the transition sharper.

    Returns:
        np.ndarray: The FID after applying the sigmoid window.
    """
    print("Applying sigmoid window for truncated FID...")
    n_points = len(fid)
    transition_points = int(n_points * transition_ratio)

    # If the signal is too short or ratio is zero, don't apply a window.
    if transition_points == 0:
        return fid

    # Create the sigmoid transition shape for one edge
    x = np.linspace(-steepness_param / 2, steepness_param / 2, transition_points)
    sigmoid_curve = 1 / (1 + np.exp(-x))

    # Create the full window shape
    window = np.ones(n_points)
    # Apply the rising edge
    window[:transition_points] = sigmoid_curve
    # Apply the falling edge (the reversed sigmoid curve)
    window[-transition_points:] = sigmoid_curve[::-1]

    windowed_fid = fid * window
    return windowed_fid


def apply_apodization(t, fid, lb):
    """
    Applies an exponential decay function (apodization) to an FID.

    Args:
        t (np.ndarray): The time vector for the FID in nanoseconds.
        fid (np.ndarray): The Free Induction Decay (time-domain signal).
        lb (float): The line broadening factor in Hz for the exponential decay.

    Returns:
        np.ndarray: The FID after apodization.
    """
    # This multiplies the FID by a decaying exponential function to improve
    # the signal-to-noise ratio, at the cost of slightly broader lines.
    # The units of lb (GHz) and t (ns) are inverse, so their product is dimensionless.
    print(f"Applying exponential decay with LB = {lb} Hz...")
    lb_ghz = lb * 1e-9
    decay_function = np.exp(-((lb_ghz * t) ** 1))
    apodized_fid = fid * decay_function
    return apodized_fid


def apply_zero_padding(t, fid, zero_padding_factor):
    """
    Applies zero padding to an FID.

    Args:
        t (np.ndarray): The time vector for the FID in nanoseconds.
        fid (np.ndarray): The FID to be padded.
        zero_padding_factor (int): The factor by which to increase the signal
                                   length (e.g., 2 for doubling).

    Returns:
        tuple: A tuple containing:
            - padded_fid (np.ndarray): The FID extended with zeros.
            - padded_t (np.ndarray): The new time vector for the padded FID in ns.
    """
    # This extends the FID with zeros to increase the number of points in the
    # resulting spectrum, making it appear smoother.
    print(f"Applying zero padding with factor x{zero_padding_factor}...")
    original_n_points = len(fid)
    new_n_points = original_n_points * zero_padding_factor

    # Create an array for the padded FID
    padded_fid = np.zeros(new_n_points, dtype=fid.dtype)
    # Copy the original FID into the beginning of the new array
    padded_fid[:original_n_points] = fid

    # Calculate the time step from the input time vector
    dt = t[1] - t[0]

    # Create the new time vector corresponding to the padded signal
    padded_t = np.arange(0, new_n_points * dt, dt)

    return padded_t, padded_fid


# -------------------------------------------------------------------------------


# Phase correction functions ----------------------------------------------------
# -------------------------------------------------------------------------------
def auto_phase(spec, fwhm_factor_signal=0.25, p1_limit=0.0):
    """
    Automatically phases a 1D NMR spectrum using a two-step optimization process.

    This function first uses a fast grid search to find an approximate solution
    for the zero-order (p0) and first-order (p1) phase corrections. It then
    refines this solution using a local minimizer (Nelder-Mead). The optimization
    aims to minimize negative components in the real part and minimize the overall
    area of the imaginary part of the spectrum, focusing on a window around the
    tallest peak.

    Args:
        spec (np.ndarray): A complex 1D numpy array representing the NMR spectrum
                           (the result of an FFT on the FID).
        p0_guess (float): Initial guess for the zero-order phase in degrees.
        p1_guess (float): Initial guess for the first-order phase in degrees.
        fwhm_factor_signal (float): Multiplier for the FWHM to define the signal region.

    Returns:
        tuple: A tuple containing:
            - np.ndarray: The phased spectrum (complex).
            - float: The optimized zero-order phase (p0) in degrees.
            - float: The optimized first-order phase (p1) in degrees.
    """

    # --- Find the region of interest around the tallest peak ---
    # This makes phasing more robust by focusing on signal, not noise/baseline.
    # Ignore the first 10% of points which might contain DC artifacts.
    dc_offset_pts = int(len(spec) * 0.10)
    spec_real_abs = np.abs(spec.real)

    # Find peak in the relevant region
    peak_index_offset = np.argmax(spec_real_abs[dc_offset_pts:])
    peak_index = peak_index_offset + dc_offset_pts
    peak_height = spec_real_abs[peak_index]

    # --- Estimate the Full Width at Half Maximum (FWHM) ---
    try:
        half_max = peak_height / 2.0

        # Find left and right points where the signal drops to half maximum
        left_hm_indices = np.where(spec_real_abs[:peak_index] < half_max)[0]
        left_hm_index = left_hm_indices[-1] if len(left_hm_indices) > 0 else 0

        right_hm_indices = np.where(spec_real_abs[peak_index:] < half_max)[0]
        right_hm_index = (
            (right_hm_indices[0] + peak_index)
            if len(right_hm_indices) > 0
            else len(spec)
        )

        fwhm = right_hm_index - left_hm_index
        if fwhm <= 0:
            fwhm = 2  # Failsafe for very sharp or noisy peaks
    except IndexError:
        fwhm = 2  # Failsafe if peak finding fails

    # --- Define signal window based on FWHM ---
    window_pts = max(2, int(fwhm * fwhm_factor_signal))
    half_window = window_pts // 2
    start_index = max(0, peak_index - half_window)
    end_index = min(len(spec), peak_index + half_window)

    # --- Helper function to apply phase correction ---
    def apply_phase(p, s):
        """Applies phase correction to a spectrum."""
        p0 = np.deg2rad(p[0])  # Zero-order phase in radians
        p1 = np.deg2rad(p[1])  # First-order phase in radians
        # p1 = 0
        # Create a linear ramp for the first-order correction, centered at the peak
        size = len(s)
        ramp = np.linspace(0, size, size)
        ramp -= ramp[peak_index]

        # Apply the phase correction using complex exponential
        phased_spec = s * np.exp(1j * (p0 + p1 * ramp))
        return phased_spec

    # --- Cost functions for the optimization ---
    def cost_function_imag(p, s):
        """
        Calculates cost based on the imaginary part of the spectrum.
        A flatter imaginary baseline (smaller derivatives) is better.
        """
        phased_spec = apply_phase(p, s)
        windowed_spec = phased_spec[start_index:end_index]
        imag_part = windowed_spec.imag
        # Penalize non-flatness in the imaginary part
        cost = -np.sum(
            (imag_part[1:] - imag_part[:-1]) ** 2
            + (imag_part[-1:] - imag_part[1:]) ** 2
        )
        return cost

    def cost_function_real(p, s):
        """
        Calculates cost based on the real part of the spectrum.
        Penalizes negative points, aiming for a positive-only spectrum.
        """
        phased_spec = apply_phase(p, s)
        windowed_spec = phased_spec[start_index:end_index]
        real_part = windowed_spec.real
        # Penalize any negative amplitude in the real part
        cost = np.sum(np.abs(real_part[real_part < 0]))
        return cost

    def cost_function(p, s):
        """
        Combined cost function for final local optimization.
        It penalizes both negative real parts and the total area of the imaginary part.
        """
        phased_spec = apply_phase(p, s)
        windowed_spec = phased_spec[start_index:end_index]
        real_part = windowed_spec.real
        imag_part = windowed_spec.imag

        # Penalty for negative points in the real part
        cost_real = np.sum(real_part[real_part < 0] ** 2)
        # Penalty for any signal in the imaginary part
        cost_imag = np.sum((imag_part) ** 2)

        return cost_imag + cost_real

    # --- Two-Step Optimization ---

    # STEP 1: Fast global search using a coarse grid
    print("Starting global grid search...")
    p0_range = np.arange(0.5, 360.5, 45)  # Search p0 from 0-360 in steps of 20

    best_score_real = float("inf")
    best_p_real = [0, 0]

    best_score_imag = float("inf")
    best_p_imag = [0, 0]

    for p0_val in p0_range:
        p_current = [p0_val, 0]

        # Evaluate real cost
        score_r = cost_function_real(p_current, spec)
        if score_r < best_score_real:
            best_score_real = score_r
            best_p_real = p_current

        # Evaluate imaginary cost
        score_i = cost_function_imag(p_current, spec)
        if score_i < best_score_imag:
            best_score_imag = score_i
            best_p_imag = p_current

    # Determine which grid search gave a better result by evaluating
    # with the combined cost function.
    score_from_real_opt = cost_function(best_p_real, spec)
    score_from_imag_opt = cost_function(best_p_imag, spec)

    p_global_best = (
        best_p_real if score_from_real_opt < score_from_imag_opt else best_p_imag
    )
    print(
        f"Global search complete. Best guess: p0={p_global_best[0]:.2f}, p1={p_global_best[1]:.2f}"
    )

    # STEP 2: Local search using the best result from the global search
    # This fine-tunes the parameters for a precise solution.
    print("Starting local optimization...")
    # Define bounds for the optimization. p0 is unbounded, p1 is limited.

    bounds = [(None, None), (-0.000, 0.000)]
    final_result = minimize(
        cost_function, p_global_best, args=(spec,), method="Nelder-Mead", bounds=bounds
    )

    bounds = [(None, None), (-p1_limit, p1_limit)]
    final_result = minimize(
        cost_function, final_result.x, args=(spec,), method="Nelder-Mead", bounds=bounds
    )

    # p0_limit = 0.001
    # p1_limit = 180.0
    # bounds = [(-p0_limit, p0_limit), (-p1_limit, p1_limit)]
    # final_result = minimize(
    #     cost_function,
    #     final_result.x,
    #     args=(spec,),
    #     method='Nelder-Mead',
    #     bounds=bounds
    # )

    p_optimized = final_result.x
    p0_opt, p1_opt = p_optimized[0], p_optimized[1]
    print(
        f"Optimization complete. Best guess: p0={p_optimized[0]:.2f}, p1={p_optimized[1]:.2f}"
    )

    # Apply the final, optimized phase correction
    final_phased_spec = apply_phase(p_optimized, spec)

    return final_phased_spec, p0_opt, p1_opt


# -------------------------------------------------------------------------------


# SNR Estimation ----------------------------------------------------------------
# -------------------------------------------------------------------------------
def calculate_snr(
    spec, dc_offset_pts=50, fwhm_factor_signal=2.0, fwhm_factor_noise=5.0
):
    """
    Calculates the Signal-to-Noise Ratio (SNR) from a phased spectrum.

    This function implements a method based on integrating the signal and the
    noise power in regions defined relative to the main peak's linewidth.

    Args:
        spec (np.ndarray): A complex 1D numpy array of the phased NMR spectrum.
        dc_offset_pts (int): Number of points at the start and end of the
                             spectrum to ignore to avoid DC/filter artifacts.
        fwhm_factor_signal (float): Multiplier for the FWHM to define the signal region.
        fwhm_factor_noise (float): Multiplier for the FWHM to define the noise window.

    Returns:
        float: The calculated Signal-to-Noise Ratio.
    """
    # 1. Work with the real, phased spectrum and remove DC/edge artifacts.
    real_spec = spec.real.copy()
    real_spec[:dc_offset_pts] = 0
    # real_spec[-dc_offset_pts:] = 0

    # 2. Find the strongest peak.
    peak_index = np.argmax(real_spec)
    peak_height = real_spec[peak_index]

    # 3. Estimate the Full Width at Half Maximum (FWHM).
    try:
        half_max = peak_height / 2.0
        left_hm_indices = np.where(real_spec[:peak_index] < half_max)[0]
        left_hm_index = left_hm_indices[-1] if len(left_hm_indices) > 0 else 0

        right_hm_indices = np.where(real_spec[peak_index:] < half_max)[0]
        right_hm_index = (
            (right_hm_indices[0] + peak_index)
            if len(right_hm_indices) > 0
            else len(real_spec)
        )

        fwhm = right_hm_index - left_hm_index
        if fwhm <= 0:
            fwhm = 2  # Failsafe for very sharp or noisy peaks
    except IndexError:
        fwhm = 2  # Failsafe if peak finding fails
    # fwhm = 2 # Failsafe if peak finding fails
    # 4. Define signal and noise regions based on FWHM.
    signal_width = max(2, int(fwhm * fwhm_factor_signal))
    signal_start = max(0, peak_index - signal_width // 2)
    signal_end = min(len(real_spec), peak_index + signal_width // 2)

    noise_width = int(fwhm * fwhm_factor_noise)
    signal_noise_start = max(0, peak_index - noise_width // 4)
    signal_noise_end = min(len(real_spec), peak_index + noise_width // 4)
    noise_window_start = max(0, peak_index - noise_width // 2)
    noise_window_end = min(len(real_spec), peak_index + noise_width // 2)

    # 5. Get signal and noise data, excluding the signal region from the noise calculation.
    signal_data = real_spec[signal_start:signal_end]
    noise_data_left = real_spec[noise_window_start:signal_noise_start]
    noise_data_right = real_spec[signal_noise_end:noise_window_end]
    noise_data = np.concatenate((noise_data_left, noise_data_right))

    if len(noise_data) < 1:
        return 0.0  # Not enough data to calculate noise

    # Perform a local baseline correction based on the median of the noise.
    # baseline_level = np.median(noise_data)
    # signal_data_corrected = signal_data - baseline_level
    # noise_data_corrected = noise_data - baseline_level

    signal_data_corrected = signal_data
    noise_data_corrected = noise_data

    # 6. Integrate signal and noise power as per the specified method.
    signal_integral = np.mean(signal_data_corrected**2)
    signal_level = np.sqrt(signal_integral)
    # "take the square first then integrate"
    noise_power_integral = np.mean(noise_data_corrected**2)

    # "if they are squared, take the square root"
    noise_level = np.sqrt(noise_power_integral)

    # 7. Calculate SNR.
    if noise_level == 0:
        return np.inf  # Avoid division by zero for noiseless data

    snr = signal_level / noise_level

    # "multiple the value by 1/sqrt(2) to reduce the overestimation"
    snr_corrected = snr / np.sqrt(2)

    return snr_corrected


# -------------------------------------------------------------------------------
