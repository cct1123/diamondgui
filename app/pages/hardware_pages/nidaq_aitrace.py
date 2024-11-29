"""
read AI of the NI DAQ

"""

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash import dcc, html
from dash_bootstrap_templates import load_figure_template
from gui.components import NumericInput, UnitedInput
from gui.config_custom import APP_THEME, NIDAQ_AI_ID, PLOT_THEME

load_figure_template([PLOT_THEME])
DATA_INTERVAL = 1000
GRAPH_INTERVAL = 2000
MAX_INTERVAL = 2147483647
ID = NIDAQ_AI_ID
# ID = "odmr-"+random_string(8)

GRAPH_INIT = {"data": [], "layout": go.Layout(template=PLOT_THEME)}
L_DICT = {"µm": 1e3, "nm": 1.0}

layout_para = dbc.Col(
    [
        dbc.Row(
            [
                dbc.ButtonGroup(
                    [
                        dbc.Button(
                            "Run",
                            id=ID + "button-run",
                            outline=True,
                            color="success",
                            active=False,
                            n_clicks=0,
                        ),
                        # dbc.Button("Pause",  id=ID+"button-pause",outline=True, color="warning", n_clicks=0),
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
        dbc.Row(
            [
                dbc.Col(
                    [
                        # dbc.Checklist(
                        #     options=[
                        #         {"label": "AI Ch", "value": 1},
                        #     ],
                        #     value=[1],
                        #     id=ID+"input-aichannel",
                        #     inline=True,
                        #     switch=True,
                        #     persistence=True, # currently persistence fails
                        #     persistence_type='local',
                        # ),
                        dbc.Row(
                            [
                                UnitedInput(
                                    "Min Volt",
                                    -10.0,
                                    10.0,
                                    1e-7,
                                    -10.0,
                                    "V",
                                    id=ID + "input-min volt",
                                )
                            ]
                        ),
                        dbc.Row(
                            [
                                UnitedInput(
                                    "Max Volt",
                                    -10.0,
                                    10.0,
                                    1e-7,
                                    -10.0,
                                    "V",
                                    id=ID + "input-min volt",
                                )
                            ]
                        ),
                        dbc.Row(
                            [
                                NumericInput(
                                    "Number Average",
                                    1,
                                    8333,
                                    1,
                                    200,
                                    id=ID + "input-number average",
                                )
                            ]
                        ),
                        dbc.Row(
                            [
                                UnitedInput(
                                    "Sampling Rate",
                                    1.0,
                                    500e3,
                                    0.1,
                                    100e3,
                                    "Hz",
                                    id=ID + "input-sampling rate",
                                )
                            ]
                        ),
                        dbc.Row(
                            [
                                NumericInput(
                                    "Refresh Rate",
                                    1.0,
                                    60.0,
                                    0.1,
                                    30.0,
                                    id=ID + "input-refresh rate",
                                )
                            ]
                        ),
                        dbc.Row(
                            [
                                UnitedInput(
                                    "History Duration",
                                    0.0,
                                    3600,
                                    1e-6,
                                    5.0,
                                    "s",
                                    id=ID + "input-history_duration",
                                )
                            ]
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

layout_hidden = dbc.Row(
    [
        dcc.Interval(id=ID + "interval-data", interval=MAX_INTERVAL, n_intervals=0),
        dcc.Interval(id=ID + "interval-graph", interval=MAX_INTERVAL, n_intervals=0),
        # dcc.Store(id=ID+"store-plot", storage_type='memory', data=plotdata),
        # dcc.Store(id=ID+"store-select", storage_type='memory', data=selectdata)
    ]
)

layout_daqai = html.Div(
    [
        dbc.Row([dbc.Col([layout_para], width=5), dbc.Col([layout_graph], width=7)]),
        dbc.Col(
            [
                # layout_graph_info,
                layout_hidden
            ]
        ),
    ]
)


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
    gui.layout = layout_daqai
    gui.run_server(
        # host="0.0.0.0",
        debug=DEBUG,
        port=GUI_PORT,
    )
