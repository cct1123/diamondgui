
# [Beta] Dashboard for NMR Experiments based on Quantum Sensors

**DiamondGUI** is a high-performance, web-based control system designed for managing diamond quantum sensor experiments. It focuses on speed, modularity, and user accessibility.
![Demo Screenshot](gui/assets/demo.png)
## Features
- **Singleton Hardware Management**: Ensures efficient control over hardware instruments, preventing redundant access.
- **Concurrent Measurements**: Run multiple measurement tasks in parallel with multiton task management.
- **In-Memory Data Handling**: Rapid data storage and retrieval directly in RAM.
- **User-Friendly Web Interface**: Built with Plotly Dash, featuring intuitive navigation for experiment control and analysis.

## Architecture Overview

### Hardware Management
- **Singleton Design**: Prevents duplicate hardware instances.
- **Centralized Control**: Instruments managed through individual controller classes.
- **Blocking Communication**: Hardware communication operates on a single-thread main process.

### Measurement Logic
- **Multiton Pattern**: Supports multiple concurrent instances of similar measurements (e.g., ODMR).
- **Task Queue**: Managed by a singleton task manager, enabling task submission, pausing, and stopping.

### Data Management
- **RAM Storage**: Data stored in memory for speed (requires significant RAM for large datasets).
- **Future-Proof**: Flexible architecture for potential database integration.

## WebUI Design
### Demo Screenshot


Developed with Dash for cross-platform, multi-user accessibility. Main sections include:

- **Home**: View task queue, logs, and navigation.
- **Sensor**: Conduct sensor characterization (e.g., ODMR, Rabi oscillations, T1/T2 measurements).
- **Spectrometry**: Perform NMR spectroscopy and quantitative analysis.
- **Calibration**: Tools for hardware and measurement calibration.
- **Hardware**: Direct control over connected instruments.

## Getting Started
1. Clone this repository:
   ```bash
   git clone https://github.com/cct1123/diamondgui.git
   cd diamondgui
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements_pip.txt
   ```
3. Run the server:
   ```bash
   python main.py
   ```
4. Access the dashboard at `http://localhost:9982`.

## Contributions
Contributions are welcome! Please open an issue to discuss improvements or submit a pull request.

---

For more details on Dash, visit the [Dash Tutorial](https://dash.plotly.com/tutorial).
