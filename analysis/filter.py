import time

import matplotlib.pyplot as plt
import numpy as np
from numba import jit
from scipy.signal import butter, lfilter, lfilter_zi


def butter_lowpass(cutoff, fs, order=5):
    """Creates a Butterworth low-pass filter using SciPy."""
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype="low", analog=False)
    return b, a


# Original function using SciPy
def apply_causal_filter_scipy(data, b, a):
    """Applies a causal low-pass filter using SciPy."""
    zi = lfilter_zi(b, a) * data[0]  # Initialize filter state
    filtered_data, _ = lfilter(b, a, data, zi=zi)
    return filtered_data


# JIT-optimized function (Numba)
@jit(nopython=True)
def apply_causal_filter_jit(data, b, a):
    """Applies a causal IIR filter using Numba with Direct Form II."""
    data -= data[0]
    filtered_data = np.empty_like(data)
    # Normalize coefficients by a[0] if a[0] is not zero
    a0 = a[0]
    # ! check the a coefficients by yuor self!
    # if a0 == 0:
    #     raise ValueError("a[0] must not be zero.")
    a_norm = a / a0
    b_norm = b / a0

    # Determine the maximum order to set state buffer size
    state_order = max(len(a_norm), len(b_norm)) - 1
    w = np.zeros(state_order)  # Filter state buffer

    for i in range(len(data)):
        # Compute the new state (using feedback coefficients)
        new_w = data[i]
        for j in range(1, len(a_norm)):
            if j - 1 < len(w):
                new_w -= a_norm[j] * w[j - 1]

        # Compute the output (using feedforward coefficients)
        y = b_norm[0] * new_w
        for j in range(1, len(b_norm)):
            if j - 1 < len(w):
                y += b_norm[j] * w[j - 1]

        filtered_data[i] = y

        # Update the state buffer by shifting old states
        for j in range(len(w) - 1, 0, -1):  # Equivalent to reversed(range(1, len(w)))
            w[j] = w[j - 1]
        if len(w) > 0:
            w[0] = new_w

    return filtered_data + data[0]


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    # Generate some sample data
    fs = 1400.0  # Sample rate (Hz)
    cutoff = 50.0  # Desired cutoff frequency (Hz)
    t = np.linspace(0, 1.0, int(fs), endpoint=False)

    # Precompute filter coefficients
    b, a = butter_lowpass(cutoff, fs, order=5)

    # Number of repetitions for averaging
    num_repeats = 10000
    # Benchmarking original method (SciPy)and JIT method
    scipy_times = []
    jit_times = []
    for _ in range(num_repeats):
        data = np.sin(2 * np.pi * 5.0 * t + np.random.randn(len(t))) + 0.5 * np.sin(
            2 * np.pi * 100.0 * t
        ) * np.random.randn(len(t))
        start = time.time()
        filtered_data_scipy = apply_causal_filter_scipy(data, b, a)
        scipy_times.append(time.time() - start)
        start = time.time()
        filtered_data_jit = apply_causal_filter_jit(data, b, a)
        jit_times.append(time.time() - start)

    avg_scipy_time = np.mean(scipy_times)
    avg_jit_time = np.mean(jit_times)

    # Print timing results
    print(f"SciPy Filtering Time: {avg_scipy_time:.6f} seconds")
    print(f"JIT Filtering Time: {avg_jit_time:.6f} seconds")
    print(
        f"JIT Filtering Speedup with {num_repeats} Repeats: {avg_scipy_time / avg_jit_time:.2f}x"
    )

    # Plot the results
    plt.figure(figsize=(24, 16))

    plt.subplot(3, 2, 1)
    # Original and SciPy filtered data
    plt.plot(t, data, label="Original Data")
    plt.plot(t, filtered_data_scipy, label="SciPy Filtered Data")
    plt.plot(t, filtered_data_jit, label="JIT Filtered Data")
    plt.title("Original Data, SciPy Filtered Data and JIT Filtered Data")
    plt.xlabel("Time [s]")
    plt.ylabel("Amplitude")
    plt.legend()
