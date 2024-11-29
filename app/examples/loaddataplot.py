import base64
import io
import pickle

import dash
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import numpy as np
import plotly.express as px
import plotly.graph_objs as go
from dash import Input, Output, State, callback, dcc, html
from dash_bootstrap_templates import load_figure_template

# Define the ID variable at the top of the code
ID = "custom_id_"  # Prefix to dynamically generate unique IDs

# Initialize the Dash app with Sketchy theme

PLOT_THEME = "sketchy"
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
                                        html.A("Select a Pickle File"),
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
                                    dbc.Col(
                                        [  # Checkbox for FFT selection
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
                                            ),
                                        ]
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


# Callback to update the graph based on selected rows and checkbox state for FFT
@callback(
    Output(ID + "scatter-plot", "figure"),
    [
        Input(ID + "data-table", "selectedRows"),
        Input(ID + "fft-checkbox", "value"),
        Input(ID + "data-store", "data"),
    ],
    prevent_initial_call=False,
)
def update_graph(selected_rows, fft_selected, dataset):
    if not selected_rows:
        return px.scatter(title="Select data for plotting from the grid")

    # Extract the selected row IDs
    selected_ids = [row["Path"] for row in selected_rows]

    # Ensure we have at least two selected paths
    if len(selected_ids) < 2:
        return px.scatter(title="Select two paths for plotting")

    x_data = selected_ids[0]
    y_data = selected_ids[1]

    # Get the data for X and Y axes
    x_vals = get_nested_value(dataset, x_data)
    y_vals = get_nested_value(dataset, y_data)

    # If FFT is selected
    if "fft" in fft_selected:
        freqs, magnitude = perform_fft(y_vals)
        # Plot FFT result
        fig = px.line(
            x=freqs,
            y=magnitude,
            labels={"x": "Frequency", "y": "Magnitude"},
            title=f"FFT of {y_data}",
            markers=True,
        )
    else:
        # Create scatter plot if no FFT
        fig = px.line(
            x=x_vals,
            y=y_vals,
            labels={"x": x_data, "y": y_data},
            title=f"{x_data} vs {y_data}",
            markers=True,
        )

    # Apply theme directly within the update_layout
    fig.update_layout(
        template=PLOT_THEME,
        font=dict(size=21),
    )

    return fig


if __name__ == "__main__":
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SKETCHY])
    gui.layout = layout_plotdata
    gui.run_server(debug=True)
