import logging
import os
import queue
import re
import threading
import time
from pathlib import Path

import dash_bootstrap_components as dbc
from dash import Dash, callback, dcc, html
from dash.dependencies import Input, Output, State

from logmodule import LogQueue

# Step 1: Logging Setup
formatted_logs_queue = queue.Queue()

raw_logs_queue = LogQueue()
INTERVAL_FORMATLOG = 500  # ms
INTERVAL_STORELOG = 500  # ms
INTERVAL_DISPLAYLOG = 1000  # ms
LEN_LOGS_TO_DISPLAY = 100  # Limit logs to display

HERE = Path(__file__).parent
LOG_TEMP_FILE = os.path.join(
    HERE, f"{time.strftime('%Y%m%d', time.localtime())}_temp.log"
)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s %(levelname)s %(module)s PID %(process)d %(threadName)s %(thread)d: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "%(asctime)s %(levelname)s %(module)s %(threadName)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console_handler": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file_handler": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": LOG_TEMP_FILE,
            "formatter": "verbose",
        },
        "stream_handler": {
            "level": "INFO",
            "class": "log_module.StreamToVariableHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console_handler", "file_handler", "stream_handler"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)
# Step 2: Dash Application Setup

layout_logmessage = html.Div(
    [
        html.H3("Real-Time Log Display", className="text-center"),
        html.Div(
            [
                html.Div(
                    id="log-output",
                    style={
                        "overflowY": "scroll",
                        "height": "400px",
                        "whiteSpace": "pre-wrap",
                    },
                ),
                dcc.Store(id="store-logs", storage_type="session", data=[]),
            ]
        ),
        dcc.Interval(
            id="store-log-interval", interval=INTERVAL_STORELOG, n_intervals=0
        ),  # Log processing interval
        dcc.Interval(
            id="display-log-interval", interval=INTERVAL_DISPLAYLOG, n_intervals=0
        ),  # Display update interval
    ]
)


# Function to apply color based on log level
def get_log_color(level):
    colors = {
        "DEBUG": "gray",
        "INFO": "blue",
        "WARNING": "orange",
        "ERROR": "red",
        "CRITICAL": "purple",
    }
    return colors.get(level, "black")


# Function to extract log level from a log message using regex
def extract_log_level(log):
    pattern = r"\b(DEBUG|INFO|WARNING|ERROR|CRITICAL)\b"
    match = re.search(pattern, log)
    if match:
        return match.group(0)
    return "INFO"


# Processing function to color logs
def process_logs():
    while True:
        if not raw_logs_queue.empty():
            log = raw_logs_queue.get()
            level = extract_log_level(log)
            color = get_log_color(level)
            parts = re.split(
                r"(\bDEBUG\b|\bINFO\b|\bWARNING\b|\bERROR\b|\bCRITICAL\b)", log
            )
            formatted_parts = []
            for part in parts:
                if part in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                    formatted_parts.append(html.Span(part, style={"color": color}))
                else:
                    split_numbers = re.split(r"(\d+)", part)
                    for sub_part in split_numbers:
                        if sub_part.isdigit():
                            formatted_parts.append(
                                html.Span(sub_part, style={"color": "green"})
                            )
                        else:
                            formatted_parts.append(html.Span(sub_part))
            formatted_logs_queue.put(html.P(formatted_parts))
        time.sleep(INTERVAL_FORMATLOG / 1e3)


# Callback to process logs and store them
@callback(
    Output("store-logs", "data"),
    Input("store-log-interval", "n_intervals"),
    State("store-logs", "data"),
)
def process_and_store_logs(n, stored_logs):
    new_logs = list(stored_logs)  # Copy existing logs
    while not formatted_logs_queue.empty():
        fromatted_log = formatted_logs_queue.get()
        new_logs.append(fromatted_log)
    # Keep only the last N logs
    return new_logs[-LEN_LOGS_TO_DISPLAY:]


# Callback to display logs from the stored data
@callback(
    Output("log-output", "children"),
    Input("display-log-interval", "n_intervals"),
    State("store-logs", "data"),
)
def display_logs(n, stored_logs):
    return stored_logs  # Return the stored logs for display


# Step 3: Simulate log generation in a separate thread
def generate_logs():
    for i in range(100000):
        logger.debug(f"Debug message {i}")
        if i % 5 == 0:
            logger.info(f"Info message {i}")
        if i % 10 == 0:
            logger.warning(f"Warning message {i}")
        if i % 15 == 0:
            logger.error(f"Error message {i}")
        if i % 20 == 0:
            logger.critical(f"Critical message {i}")
        time.sleep(0.5)


# Start log processing and generation threads
threading.Thread(target=process_logs, daemon=True).start()
threading.Thread(target=generate_logs, daemon=True).start()

# Run the Dash app
if __name__ == "__main__":
    app = Dash(__name__, external_stylesheets=[dbc.themes.SKETCHY])
    app.layout = layout_logmessage
    app.run_server(debug=True)
