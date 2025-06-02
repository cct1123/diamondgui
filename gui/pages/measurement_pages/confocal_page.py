import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go
from dash import Input, Output, State, callback, callback_context, dcc, html
from dash_bootstrap_templates import load_figure_template

from gui.components import NumericInput, UnitedInput
from gui.config import APP_THEME, COLORSCALE, CONFOCAL_ID, PLOT_THEME

load_figure_template([PLOT_THEME])
import json
import random

DATA_INTERVAL = 200
GRAPH_INTERVAL = 300
MAX_INTERVAL = 2147483647
ID = CONFOCAL_ID
L_DICT = {"µm": 1e3, "nm": 1.0}

styles = {"pre": {"border": "thin lightgrey solid", "overflowX": "scroll"}}

GRAPH_INIT = {"data": [], "layout": go.Layout(template=PLOT_THEME)}
# storedata = {"plot":{"x":[], "y":[], "z":[]}, "selec":{"x":[], "y":[]}}
plotdata = dict(plot=dict(x=[], y=[], z=[]))
selectdata = dict(select=dict(x=[], y=[]))

layout_para = dbc.Col(
    [
        dbc.Row(
            [
                dbc.ButtonGroup(
                    [
                        dbc.Button(
                            "Scan",
                            id=ID + "button-run",
                            outline=True,
                            color="success",
                            active=False,
                            n_clicks=0,
                        ),
                        dbc.Button(
                            "Pause",
                            id=ID + "button-pause",
                            outline=True,
                            color="warning",
                            n_clicks=0,
                        ),
                        dbc.Button(
                            "Stop",
                            id=ID + "button-stop",
                            outline=True,
                            color="danger",
                            n_clicks=0,
                        ),
                    ],
                ),
                # dbc.Col([html.Div(id="div-status", children=[]),]),
                dbc.Progress(
                    value=0,
                    id="progress-bar",
                    animated=True,
                    striped=False,
                    label="",
                    className="mt-2 mb-2",
                ),
            ],
            align="center",
        ),
        dbc.Col(
            [
                dbc.Row(
                    [
                        # dbc.Col([UnitedInput("X Begin", -1E9, 1E9, 1, 50, "nm", L_DICT, id=ID+"input-X Begin")]),
                        # dbc.Col([UnitedInput("X End", -1E9, 1E9, 1, 50, "nm", L_DICT, id=ID+"input-X End")]),
                        # dbc.Col([UnitedInput("X Step", -1E9, 1E9, 1, 50, "nm", L_DICT, id=ID+"input-X Step")]),
                        dbc.Col(
                            [
                                NumericInput(
                                    "X Begin [nm]",
                                    -1e9,
                                    1e9,
                                    1,
                                    50,
                                    id=ID + "input-X Begin",
                                )
                            ]
                        ),
                        dbc.Col(
                            [
                                NumericInput(
                                    "X End [nm]",
                                    -1e9,
                                    1e9,
                                    1,
                                    50,
                                    id=ID + "input-X End",
                                )
                            ]
                        ),
                        dbc.Col(
                            [
                                NumericInput(
                                    "X Step [nm]",
                                    -1e9,
                                    1e9,
                                    1,
                                    50,
                                    id=ID + "input-X Step",
                                )
                            ]
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        # dbc.Col([UnitedInput("Y Begin", -1E9, 1E9, 1, 50, "nm", L_DICT, id=ID+"input-Y Begin")]),
                        # dbc.Col([UnitedInput("Y End", -1E9, 1E9, 1, 50, "nm", L_DICT, id=ID+"input-Y End")]),
                        # dbc.Col([UnitedInput("Y Step", -1E9, 1E9, 1, 50, "nm", L_DICT, id=ID+"input-Y Step")]),
                        dbc.Col(
                            [
                                NumericInput(
                                    "Y Begin [nm]",
                                    -1e9,
                                    1e9,
                                    1,
                                    50,
                                    id=ID + "input-Y Begin",
                                )
                            ]
                        ),
                        dbc.Col(
                            [
                                NumericInput(
                                    "Y End [nm]",
                                    -1e9,
                                    1e9,
                                    1,
                                    50,
                                    id=ID + "input-Y End",
                                )
                            ]
                        ),
                        dbc.Col(
                            [
                                NumericInput(
                                    "Y Step [nm]",
                                    -1e9,
                                    1e9,
                                    1,
                                    50,
                                    id=ID + "input-Y Step",
                                )
                            ]
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.InputGroup(
                                    [
                                        dbc.InputGroupText("Fix Axis"),
                                        dbc.Select(
                                            id=ID + "select-fixaxis",
                                            options=[
                                                {"label": "1", "value": 1},
                                                {"label": "2", "value": 2},
                                                {
                                                    "label": "3",
                                                    "value": 3,
                                                },  # refering to axis of the posiitioners
                                            ],
                                            value=3,
                                            persisted_props=["value"],
                                            persistence=True,
                                            persistence_type="local",
                                            size="sm",
                                            disabled=False,
                                        ),
                                    ]
                                )
                            ],
                            width=4,
                        ),
                        dbc.Col(
                            [
                                UnitedInput(
                                    "Z Point",
                                    -1e9,
                                    1e9,
                                    1,
                                    1000,
                                    "nm",
                                    L_DICT,
                                    id=ID + "input-Z Point",
                                ),
                            ],
                            width=8,
                        ),
                    ]
                ),
            ]
        ),
    ]
)

layout_graph = dbc.Col(
    [
        dbc.Container(
            [
                dcc.Graph(
                    figure=GRAPH_INIT,
                    id=ID + "graph",
                    mathjax=True,
                    animate=False,
                    responsive="auto",
                    style={"aspectRatio": "1.2/1"},
                )
            ],
            fluid=True,
        )
    ],
)

layout_graph_info = dbc.Row(
    [
        dbc.Col(
            [
                dcc.Markdown("""
            **Hover Data**

            Mouse over values in the graph.
        """),
                html.Pre(id="hover-data", style=styles["pre"]),
            ],
            className="three columns",
        ),
        dbc.Col(
            [
                dcc.Markdown("""
            **Click Data**

            Click on points in the graph.
        """),
                html.Pre(id="click-data", style=styles["pre"]),
            ],
            className="three columns",
        ),
        dbc.Col(
            [
                dcc.Markdown("""
            **Selection Data**

            Choose the lasso or rectangle tool in the graph's menu
            bar and then select points in the graph.

            Note that if `layout.clickmode = 'event+select'`, selection data also
            accumulates (or un-accumulates) selected data if you hold down the shift
            button while clicking.
        """),
                html.Pre(id="selected-data", style=styles["pre"]),
            ],
            className="three columns",
        ),
        dbc.Col(
            [
                dcc.Markdown("""
            **Zoom and Relayout Data**

            Click and drag on the graph to zoom or click on the zoom
            buttons in the graph's menu bar.
            Clicking on legend items will also fire
            this event.
        """),
                html.Pre(id="relayout-data", style=styles["pre"]),
            ],
            className="three columns",
        ),
    ]
)

layout_hidden = dbc.Row(
    [
        dcc.Interval(id=ID + "interval-data", interval=MAX_INTERVAL, n_intervals=0),
        dcc.Interval(id=ID + "interval-graph", interval=MAX_INTERVAL, n_intervals=0),
        dcc.Store(id=ID + "store-plot", storage_type="memory", data=plotdata),
        dcc.Store(id=ID + "store-select", storage_type="memory", data=selectdata),
    ]
)

layout_confocal = html.Div(
    [
        dbc.Row([dbc.Col([layout_para], width=5), dbc.Col([layout_graph], width=7)]),
        dbc.Col([layout_graph_info, layout_hidden]),
    ]
)


# test interactive-----------------------------------------------
@callback(Output("hover-data", "children"), Input(ID + "graph", "hoverData"))
def display_hover_data(hoverData):
    return json.dumps(hoverData, indent=2)


@callback(Output("click-data", "children"), Input(ID + "graph", "clickData"))
def display_click_data(clickData):
    return json.dumps(clickData, indent=2)


@callback(Output("selected-data", "children"), Input(ID + "graph", "selectedData"))
def display_selected_data(selectedData):
    return json.dumps(selectedData, indent=2)


@callback(Output("relayout-data", "children"), Input(ID + "graph", "relayoutData"))
def display_relayout_data(relayoutData):
    return json.dumps(relayoutData, indent=2)


# ----------------------------------------------------------------------

# @callback(
#     Output(ID+'click-data', 'children'),
#     Output(ID+"store-select", 'data'),
#     Input(ID+'graph', 'clickData'),

#     prevent_initial_call=True,
# )
# def _display_click_data(clickData):
#     # {'points': [{'x': 128.5789673961222, 'y': 185.3020134228188, 'curveNumber': 0}]}
#     storedata = dict(select=dict(x=[], y=[]))
#     storedata["select"]["x"] = [pp["x"] for pp in clickData["points"]]
#     storedata["select"]["y"] = [pp["y"] for pp in clickData["points"]]
#     print(storedata)
#     return [str(clickData)], storedata


@callback(
    Output(ID + "interval-data", "interval"),
    Output(ID + "interval-graph", "interval"),
    Input(ID + "button-run", "n_clicks"),
    Input(ID + "button-pause", "n_clicks"),
    Input(ID + "button-stop", "n_clicks"),
    prevent_initial_call=True,
)
def _update_intervals(_n_clicks1, _n_clicks2, _n_clicks3):
    ctx = callback_context
    if ctx.triggered_id == ID + "button-run":
        return DATA_INTERVAL, GRAPH_INTERVAL
    return MAX_INTERVAL, MAX_INTERVAL


@callback(
    Output(ID + "store-plot", "data"),
    Input(ID + "interval-data", "n_intervals"),
    # State(ID+'store-plot', "data"),
    prevent_initial_call=True,
)
def _update_storedata(_):
    x = np.linspace(0.0, 200.0 + 80 * random.random(), 50 + int(50 * random.random()))
    y = np.linspace(50.0, 260.0, 150)
    xx, yy = np.meshgrid(x, y)
    zz = np.sin(xx * random.random()) + np.cos(yy * random.random()) + random.random()
    storedata = {}
    storedata["plot"] = dict(x=np.ravel(xx), y=np.ravel(yy), z=np.ravel(zz))
    return storedata


@callback(
    Output(ID + "input-X Begin", "value"),
    Output(ID + "input-X End", "value"),
    Output(ID + "input-Y Begin", "value"),
    Output(ID + "input-Y End", "value"),
    # Output(ID+"input-X Begin"+"-unit", 'value'),
    # Output(ID+"input-X End"+"-unit", 'value'),
    # Output(ID+"input-Y Begin"+"-unit", 'value'),
    # Output(ID+"input-Y End"+"-unit", 'value'),
    Input(ID + "graph", "relayoutData"),
    State(ID + "input-X Begin", "value"),
    State(ID + "input-X End", "value"),
    State(ID + "input-Y Begin", "value"),
    State(ID + "input-Y End", "value"),
    prevent_initial_call=True,
)
def _set_scan_range(relayout, x0, x1, y0, y1):
    relayoutkeys = relayout.keys()
    if "xaxis.range[0]" in relayoutkeys:
        x0 = round(relayout["xaxis.range[0]"])
        x1 = round(relayout["xaxis.range[1]"])
        y0 = round(relayout["yaxis.range[0]"])
        y1 = round(relayout["yaxis.range[1]"])

    return x0, x1, y0, y1


@callback(
    Output(ID + "graph", "figure"),
    Input(ID + "interval-graph", "n_intervals"),
    Input(ID + "store-select", "data"),
    State(ID + "store-plot", "data"),
    prevent_initial_call=True,
)
def _update_graph(_, select, data):
    if data["plot"]["x"] != []:
        xmin = min(data["plot"]["x"])
        xmax = max(data["plot"]["x"])
        ymin = min(data["plot"]["y"])
        ymax = max(data["plot"]["y"])
        ratio = (ymax - ymin) / (xmax - xmin)
    else:
        ratio = 1.0
    # width = 1200
    # data = go.Heatmapgl(
    data = go.Heatmap(
        x=data["plot"]["x"],
        y=data["plot"]["y"],
        z=data["plot"]["z"],
        colorscale=COLORSCALE,
        showscale=True,
        colorbar=dict(len=0.8),
        # hoverinfo='confocal scan',
        # name='scan',
    )
    # select = go.Scatter(x=select["select"]["x"], y=select["select"]["y"], mode="markers", showlegend = False,)
    return {
        # 'data':[data, select],
        "data": [data],
        "layout": go.Layout(
            clickmode="event+select",
            autosize=True,
            # width=width,
            # height=ratio*width,
            xaxis=dict(title="x [mm]"),
            yaxis=dict(scaleanchor="x", title="y [mm]"),
            # yaxis = dict(scaleanchor = 'x', scaleratio=ratio, title="y [mm]"),
            # xaxis2 = dict(scaleanchor = 'x', title="", visible=False),
            # yaxis2 = dict(scaleanchor = 'x', title="", visible=False),
            template=PLOT_THEME,
        ),
    }


if __name__ == "__main__":
    from dash_bootstrap_components import themes

    # APP_THEME = themes.JOURNAL
    # APP_THEME = themes.SKETCHY
    # APP_THEME = themes.QUARTZ
    # APP_THEME = themes.DARKLY
    # APP_THEME = themes.VAPOR
    APP_THEME = themes.SUPERHERO
    DEBUG = True
    GUI_PORT = 9843
    app = dash.Dash(
        __name__,
        external_stylesheets=[
            APP_THEME,
        ],
        external_scripts=[],
    )
    app.layout = layout_confocal
    app.run_server(
        # host="0.0.0.0",
        debug=DEBUG,
        port=GUI_PORT,
    )
