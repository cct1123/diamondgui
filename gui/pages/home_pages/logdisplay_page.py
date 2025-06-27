import queue
import re
import threading
import time

import dash_bootstrap_components as dbc
from dash import Dash, callback, dcc, html
from dash.dependencies import Input, Output, State

from logmodule import LogQueue

INTERVAL_FORMATLOG = 300  # ms
INTERVAL_STORELOG = 500  # ms
INTERVAL_DISPLAYLOG = 1000  # ms
LEN_LOGS_TO_DISPLAY = 100  # Limit logs to display
ID = "logmessage-"

# Logging Setup
formatted_logs_queue = queue.Queue()
raw_logs_queue = LogQueue()


layout_logdisplay = dbc.Container(
    [
        dbc.Card(
            [
                dbc.CardHeader("Log Messages"),
                dbc.CardBody(
                    [
                        html.Div(
                            id=ID + "log-output",
                            style={
                                "overflowY": "scroll",
                                "height": "300px",
                                "whiteSpace": "pre-wrap",
                            },
                            className="mt-2 mb-2",
                        ),
                    ]
                ),
            ]
        ),
        dcc.Store(
            id=ID + "store-logs",
            storage_type="local",
            data=[],
        ),
        dcc.Interval(
            id=ID + "store-log-interval",
            interval=INTERVAL_STORELOG,
            n_intervals=0,
        ),  # Log processing interval
        dcc.Interval(
            id=ID + "display-log-interval",
            interval=INTERVAL_DISPLAYLOG,
            n_intervals=0,
        ),  # Display update interval
    ],
    className="mt-4 mb-4",
    fluid=True,
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
            log_record = raw_logs_queue.get()  # This is a LogRecord, not a string
            log_message = log_record.getMessage()  # Extract the log message (string)
            level = extract_log_level(log_message)
            color = get_log_color(level)
            parts = re.split(
                r"(\bDEBUG\b|\bINFO\b|\bWARNING\b|\bERROR\b|\bCRITICAL\b)", log_message
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
    Output(ID + "store-logs", "data"),
    Input(ID + "store-log-interval", "n_intervals"),
    State(ID + "store-logs", "data"),
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
    Output(ID + "log-output", "children"),
    Input(ID + "display-log-interval", "n_intervals"),
    State(ID + "store-logs", "data"),
)
def display_logs(n, stored_logs):
    return stored_logs  # Return the stored logs for display


threading.Thread(target=process_logs, daemon=True).start()

# Run the Dash app
if __name__ == "__main__":
    app = Dash(__name__, external_stylesheets=[dbc.themes.SKETCHY])
    app.layout = layout_logdisplay
    app.run_server(debug=True)

# Log Section
