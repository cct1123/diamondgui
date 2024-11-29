import base64
import io
import pickle
import threading

import dash
import dash_ace
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import numpy as np
import plotly.express as px
import plotly.graph_objs as go
from dash import Input, Output, State, callback, callback_context, dcc, html
from dash_bootstrap_templates import load_figure_template
from gui.config_custom import APP_THEME, PLOT_THEME, PLOTDATA_ID
from scipy.optimize import curve_fit

# Define the ID variable at the top of the code
ID = PLOTDATA_ID  # Prefix to dynamically generate unique IDs

# Initialize the Dash app with Sketchy theme

load_figure_template([PLOT_THEME])
GRAPH_INIT = {"data": [], "layout": go.Layout(template=PLOT_THEME)}


# Function to flatten nested dictionary and keep track of paths
def flatten_dict(d, parent_key=""):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}.{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key).items())
        else:
            # Convert np.ndarray to list for display
            if isinstance(v, np.ndarray):
                v = v.tolist()  # Only call tolist() on np.ndarray
            items.append((new_key, v))
    return dict(items)


# Function to generate the tree-like structure for AG Grid
def generate_ag_grid_data(flattened):
    grid_data = []
    for key, value in flattened.items():
        grid_data.append({"Path": key, "Value": value})
    return grid_data


# Access the nested data using the flattened keys
def get_nested_value(data, key):
    keys = key.split(".")
    for k in keys:
        data = data[k]
    return data


# Function to perform FFT
def perform_fft(data):
    # Apply FFT and get frequency spectrum
    fft_result = np.fft.fft(data)
    freqs = np.fft.fftfreq(len(data))

    # Select only the positive frequencies
    pos_freqs = freqs[: len(freqs) // 2]
    pos_magnitude = np.abs(fft_result)[
        : len(fft_result) // 2
    ]  # Magnitude of the FFT result

    return pos_freqs, pos_magnitude


layout_plotdata = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        [
                            # Upload section
                            dcc.Upload(
                                id=ID + "upload-data",
                                children=html.Div(
                                    [
                                        "Drag and Drop or ",
                                        "Select a Pickle File",
                                    ]
                                ),
                                style={
                                    "width": "100%",
                                    "height": "80px",
                                    "lineHeight": "80px",
                                    "borderWidth": "2px",
                                    "borderStyle": "dashed",
                                    "borderRadius": "10px",
                                    "textAlign": "center",
                                    "backgroundColor": "#f8f9fa",
                                },
                                multiple=False,
                            ),
                            # Displaying the file name of the uploaded file
                            dbc.Row(
                                [
                                    dbc.Col(
                                        html.Div(
                                            children="Loaded file: ",
                                            id=ID + "file-name",
                                        )
                                    ),
                                ]
                            ),
                            # Displaying the entire data structure in AG Grid
                            dag.AgGrid(
                                id=ID + "data-table",
                                style={"height": "400px", "width": "100%"},
                                columnDefs=[
                                    {
                                        "headerName": "Path",
                                        "field": "Path",
                                        "width": 250,
                                    },
                                    {
                                        "headerName": "Value",
                                        "field": "Value",
                                        "width": 400,
                                    },
                                ],
                                rowData=[],
                                enableEnterpriseModules=True,
                                columnSize="sizeToFit",
                                dashGridOptions={
                                    "rowSelection": "multiple",  # Enable multi-row selection by default
                                    "rowMultiSelectWithClick": True,  # Enable multi-row selection on click
                                },
                                selectedRows=[],  # Start with no rows selected
                            ),
                        ]
                    ),
                    width=6,  # Left column with the table
                ),
                dbc.Col(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        dbc.Button(
                                                            "Fit Curve",
                                                            id=ID + "fit-button",
                                                            color="primary",
                                                            outline=True,
                                                            className=" mt-2 mb-2",
                                                        )
                                                    ]
                                                ),
                                                dbc.Col(
                                                    [  # Checkbox for FFT selection
                                                        dbc.Row(
                                                            dbc.Checklist(
                                                                id=ID + "fft-checkbox",
                                                                options=[
                                                                    {
                                                                        "label": "Show FFT",
                                                                        "value": "fft",
                                                                    }
                                                                ],
                                                                value=[],
                                                                inline=True,
                                                                className="mt-3 mb-2",
                                                            ),
                                                        )
                                                    ]
                                                ),
                                            ]
                                        ),
                                        dash_ace.DashAceEditor(
                                            id=ID + "code-editor",
                                            value="def model(x, a, b, c, d):\n    return a*np.sin(b*x+c)+d",  # Example function
                                            theme="tomorrow",  # Choose from many themes
                                            mode="python",  # Set mode to Python
                                            tabSize=4,
                                            style={"height": "100px", "width": "90%"},
                                        ),
                                    ]
                                ),
                            ]
                        ),
                        html.Div(
                            [
                                # Graph section
                                dcc.Graph(figure=GRAPH_INIT, id=ID + "scatter-plot"),
                            ]
                        ),
                    ],
                    width=6,  # Right column with the graph
                ),
            ]
        ),
        # Store component to cache the dataset in front-end state
        dcc.Store(id=ID + "data-store", storage_type="session"),
        dcc.Store(id=ID + "fit-results"),
    ]
)


# Callback to handle file upload and store the dataset in the data-store
@callback(
    [
        Output(ID + "data-store", "data"),
        Output(ID + "file-name", "children"),
    ],  # Update file name in UI
    Input(ID + "upload-data", "contents"),  # Listen to the file upload component
    State(ID + "upload-data", "filename"),
    prevent_initial_call=True,
)
def load_data(file_contents, filename):
    if file_contents:
        # Load data from uploaded file
        content_type, content_string = file_contents.split(",")
        decoded = base64.b64decode(content_string)
        dataset = pickle.load(io.BytesIO(decoded))

        # Return the dataset to the data-store and display file name
        return dataset, f"Loaded file: {filename}"
    return {}, "No file loaded"  # Return empty dict if no file is uploaded


# Callback to update the table based on the data in the data-store
@callback(
    Output(ID + "data-table", "rowData"),  # Update the table with row data
    Input(ID + "data-store", "data"),  # Listen to changes in the data-store
    prevent_initial_call=False,
)
def update_table(dataset):
    if dataset:
        # Flatten the dataset and filter only arrays or lists
        flattened = flatten_dict(dataset)

        # Generate AG Grid data with the flattened structure
        grid_data = generate_ag_grid_data(flattened)
        return grid_data
    return []  # Return empty table if no data in the store


# Callback to perform fitting in a separate thread
@callback(
    Output(ID + "fit-results", "data"),  # Store fitted curve data
    Input(ID + "fit-button", "n_clicks"),
    Input(ID + "upload-data", "contents"),
    State(ID + "data-table", "selectedRows"),
    State(ID + "code-editor", "value"),
    State(ID + "data-store", "data"),
    prevent_initial_call=True,
)
def run_fitting_thread(_n_clicks, _file_contents, selected_rows, func_str, dataset):
    ctx = callback_context
    if ctx.triggered_id != ID + "fit-button":
        return {}
    if not selected_rows:
        return {}
    elif len(selected_rows) < 2:
        return {}
    result_container = {}
    # Extract raw data from selected rows
    x_data = get_nested_value(dataset, selected_rows[0]["Path"])
    y_data = get_nested_value(dataset, selected_rows[1]["Path"])

    # Function to perform fitting in the background
    def fit_curve():
        try:
            # Create local environment and inject preloaded libraries
            local_env = {"np": np}
            exec(func_str, local_env)  # Execute user code with injected environment
            # Extract the user-defined function
            curve_function = local_env.get("model")
            if curve_function is None:
                raise ValueError("The code must define a function named 'model'")
            params, _ = curve_fit(curve_function, x_data, y_data)
            y_fit = curve_function(np.array(x_data), *params)
            result_container["params"] = params
            result_container["x_fit"] = x_data
            result_container["y_fit"] = y_fit
            # print(result_container)
        except Exception as e:
            result_container["error"] = str(e)

    thread = threading.Thread(target=fit_curve)
    thread.start()
    thread.join()  # Ensure fitting finishes before returning
    return result_container  # Return the fitted data or errors


# Callback to update the graph with raw and fitted data
@callback(
    Output(ID + "scatter-plot", "figure"),
    [
        Input(ID + "data-table", "selectedRows"),
        Input(ID + "fit-results", "data"),  # Fitted data
        Input(ID + "fft-checkbox", "value"),
        State(ID + "data-store", "data"),
    ],
    prevent_initial_call=True,
)
def update_graph(selected_rows, fit_results, fft_selected, dataset):
    if not selected_rows:
        return px.scatter(title="Select data for plotting from the grid")
    elif len(selected_rows) < 2:
        return px.scatter(title="Select two paths for plotting")

    # Extract raw data from selected rows
    x_name = selected_rows[0]["Path"]
    x_data = get_nested_value(dataset, x_name)
    y_name = selected_rows[1]["Path"]
    y_data = get_nested_value(dataset, y_name)
    if type(x_data) != type(y_data):
        return px.scatter(title="X and Y data must be of the same type")
    elif len(x_data) != len(y_data):
        return px.scatter(title="X and Y data must have the same length")

    # Create figure with raw data
    fig = go.Figure()

    # Plot FFT of raw data if FFT checkbox is selected
    if fft_selected:
        # Perform FFT on raw y_data
        y_freqs, y_magnitude = perform_fft(y_data)
        fig.add_trace(
            go.Scatter(
                x=y_freqs,
                y=y_magnitude,
                mode="lines",
                name="FFT of Raw Data",
                line=dict(dash="dot"),
            )
        )
        fig.update_layout(
            title=f"FFT of {y_name}",
        )
    else:
        fig.add_trace(
            go.Scatter(
                x=x_data,
                y=y_data,
                mode="lines+markers",
                name="Raw Data",
            )
        )
        # Plot fitted curve if available
        if fit_results and "x_fit" in fit_results and "y_fit" in fit_results:
            fig.add_trace(
                go.Scatter(
                    x=fit_results["x_fit"],
                    y=fit_results["y_fit"],
                    mode="lines",
                    name="Fitted Curve",
                )
            )

            # Display fitted parameters with rounded values (assuming fit_results contains them)
            fit_params_text = f"Fitted parameters: {[round(param, 3) for param in fit_results['params']]}"
            fig.update_layout(title=fit_params_text)

        # If there was an error in fitting, show it
        if fit_results and "error" in fit_results:
            fig.update_layout(title=f"Curve fitting error: {fit_results['error']}")

    # Update layout with proper axis labels and title
    fig.update_layout(
        template=PLOT_THEME,
        xaxis_title=selected_rows[0]["Path"],
        yaxis_title=selected_rows[1]["Path"],
        font=dict(size=18),
    )

    return fig


if __name__ == "__main__":
    app = dash.Dash(__name__, external_stylesheets=[APP_THEME])
    gui.layout = layout_plotdata
    gui.run_server(debug=True)
