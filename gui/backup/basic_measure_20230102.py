


import dash
from dash.dependencies import Output, Input
from dash import dcc, html, callback_context, callback
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
import dash_daq as ddaq

import plotly
import plotly.graph_objs as go
import plotly.io as pio
from collections import deque


from nspyre import DataSink
from measurement.odmr_dummy import SpinMeasurements
import threading
import random
import numpy as np
import time

SINK_TIMEOUT = 0.2 # second
GUI_PORT = 9981
app_theme = dbc.themes.SKETCHY
# app_theme = dbc.themes.DARKLY
# app_theme = dbc.themes.QUARTZ
# app_theme = dbc.themes.DARKLY
# app_theme = dbc.themes.VAPOR
# plot_template = 'vapor'
plot_template = 'sketchy'
# plot_template = 'darkly'
# plot_template = 'quartz'
# plot_template = 'darkly'
icon_css =  "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css"
load_figure_template([plot_template])

dash.register_page(
    __name__, 
    path="/basic",
    name="Basic Measure",
    icon="fa-diamond",
    order=2,
    title="Basic Measurement"
    ) 






class DashBoard():
    
    fig = go.Figure()
    datasink = DataSink('odmr', '127.0.0.1', auto_reconnect=True)
    exp = SpinMeasurements()

    X = np.array([0])
    Y = np.array([0])
    status = "run" # idle, pause
    parameters = dict(freq_start=2.7e9, freq_end=3.0e9, num_pt=100, num_iter=2)
    thread_job = threading.Thread()
    progress = 0.0
    def __init__(self):
        self.create_applayout()
        callback(Output('live-graph', 'figure'), 
                          Input('graph-update', 'n_intervals'),
                          prevent_initial_call=False)(self._update_graph)
        callback(Output('local-data-dumdum', 'data'), 
                          Input('data-update', 'n_intervals'),
                          prevent_initial_call=True)(self._update_data)
        callback(Output('animated-progress', 'label'), 
                          Output('animated-progress', 'value'), 
                          Input('check-exp', 'n_intervals'),
                          prevent_initial_call=True)(self.update_progress_bar)
        callback(Output('button-run', 'active'), 
                          Output('button-pause', 'active'),
                          Output('button-stop', 'active'), 
                          Output('div-status', 'children'), 
                          Output('graph-update', 'interval'),
                          Input('button-run', 'n_clicks'), 
                          Input('button-pause', 'n_clicks'), 
                          Input('button-stop', 'n_clicks'), 
                          Input('check-exp', 'n_intervals'))(self.update_status)
        callback(Output('store-para', 'data'), 
                          Input('input-start-freq', 'value'), 
                          Input('input-end-freq', 'value'), 
                          Input('input-num-points', 'value'), 
                          Input('input-iterations', 'value'))(self.update_para)
        callback(Output('local-data', 'data'), 
                          Input('button-run', 'n_clicks'), 
                          prevent_initial_call=True)(self.run_exp)
        self.datasink.start()

    def run_exp(self, _):
        print("trigggg runnnnnnnnnnnnnn")
        
        para = self.parameters
        self.thread_job = threading.Thread(target=self.exp.odmr_sweep, args=('odmr', para["freq_start"], para["freq_end"], para["num_pt"], para["num_iter"]))
        self.thread_job.start()
        while not self.thread_job.is_alive():
            time.sleep(0.1)
            print("not started")
        else:
            self.status = "run"
            self.progress = 0.0
        # self.X = deque(maxlen=para["num_pt"])
        # self.Y = deque(maxlen=para["num_pt"])
        return []

    def update_status(self, _1, _2, _3, _4):
        print("trigggg")
        ctx = callback_context
        # print(callback_context.triggered_id)
        if ctx.triggered_id == "button-run":
            return True, False, False, [dbc.Spinner(color="success")], 200
        elif ctx.triggered_id == "button-pause":
            if self.status == "run":
                self.status = "paused"
                return False, True, False, [dbc.Spinner(color="warning")], 2147483647
        elif ctx.triggered_id == "button-stop":
            self.progress = 0.0
            self.status = "idle"
            return False, False, False, [], 2147483647
        elif ctx.triggered_id == "check-exp":
            # self.thread_job.join()
            # the following code is blocked until the thread_job is done
            if self.status == "run":
                if not self.thread_job.is_alive():
                    self.status = "idle"
                    # self.thread_job.join()
                    self.progress = 0.0
                    return False, False, False, [], 2147483647    
                else:
                    self.status = "run"
                    return True, False, False, [dbc.Spinner(color="success")], 200
            elif self.status == "paused":
                return False, True, False, [dbc.Spinner(color="warning")], 2147483647

        return False, False, False, [], 2147483647

    def update_progress_bar(self, _):
        print("update progress bar!!")
        print(self.status)
        if self.status == "run":
            print("progress running!!!!")
            return f"{round(self.progress)}%", self.progress
        else:
            self.progress = 0.0
            return "", self.progress

    def update_para(self, startfreq, stopfreq, numpt, numiter):
        print("update parametes")
        self.parameters["freq_start"] = startfreq
        self.parameters["freq_end"] = stopfreq
        self.parameters["num_pt"] = numpt
        self.parameters["num_iter"] = numiter
        return []

    def read_para(self):
        if self.datasink.pop(timeout=SINK_TIMEOUT):
            self.xlabel = self.datasink.xlabel
            self.ylabel = self.datasink.ylabel
            self.title = self.datasink.title
        
    def read_data(self):
        if self.datasink.pop(timeout=SINK_TIMEOUT):
            data = self.datasink.data['datasets']['mydata'][-1]
            self.progress = len(self.datasink.data['datasets']['mydata'])/self.parameters["num_iter"]*100
            self.X = data[0]
            self.Y = data[1]

    def _update_data(self, _):
        if self.status == "run":
            self.read_data()
        return []

    def _update_graph(self, _):
        data = go.Scattergl(x = list(self.X), y=list(self.Y), name='scatter', mode='lines+markers')
        return {'data':[data], 
        'layout':go.Layout(
            xaxis = dict(range=[min(self.X), max(self.X)]), 
            yaxis = dict(range=[min(self.Y), 1.05*max(self.Y)]), 
            xaxis_title="Frequency [GHz]",
            yaxis_title="Spint State",
            template=plot_template)
        }

    def start_gui(self, debug=True):
        app = dash.Dash(__name__, external_stylesheets=[app_theme, icon_css], external_scripts=[])
        self.app.run_server(debug=debug, port=GUI_PORT)

    def create_applayout(self):
        children = [html.H1("ODMR Apppppppppppppppppppp", className="p-2 mb-1 text-center"),
                    dbc.Row(
                            [dbc.Col([dbc.ButtonGroup(
                                [dbc.Button("Run", id="button-run", outline=True, color="success", active=False, n_clicks=0), 
                                dbc.Button("Pause",  id="button-pause",outline=True, color="warning", n_clicks=0), 
                                dbc.Button("Stop",  id="button-stop", outline=True, color="danger", n_clicks=0),
                                dbc.Button("A FKIN' Button",  id="button-fking", outline=True, color="primary", className="me-1"),

                                ],
                            ),]),
                            dbc.Col([
                            html.Div(id="div-status", children=[]),]),
                            dbc.Col([
                            ddaq.PowerButton(
                                                id='our-power-button-1',
                                                className="me-1", 
                                                on=False,
                                                color="secondary"
                                            ),],),
                            dbc.Progress(
                                            value=100, id="animated-progress", animated=True, striped=True, label="",
                                        ),
                            ],
                            align="center",
                            ), 
                            
                    dbc.Row(
                            [
                            dbc.Col([html.Div(id="parameters-input", children=
                                        [dcc.Store(id='store-para', storage_type='local'),
                                            dbc.InputGroup([
                                                

                                                            dbc.InputGroupText("Start"),   
                                                            dbc.Select(
                                                                    id="select-unit-freq2",
                                                                    options=[
                                                                        {"label": "GHz", "value": 1E9},
                                                                        {"label": "MHz", "value": 1E6},
                                                                        {"label": "kHz", "value": 1E3},
                                                                        {"label": "Hz", "value": 1, "disabled": False},
                                                                    ],
                                                                    value=1,
                                                                    persisted_props=["value"],
                                                                    persistence=True, 
                                                                    persistence_type="local",
                                                                    size = "sm",
                                                                    style={"max-width":"20%",
                                                                    "appearance": "none !important",
                                                                    "-webkit-appearance": "none !important",
                                                                     "-moz-appearance": "none !important",
                                                                    },
                                                                    disabled =False,
                                                                    # class_name="dropdown-container"
                                                                    # class_name="select"
                                                                ),                      
                                                            dbc.Input(
                                                                id="input-start-freq", 
                                                                type="number", placeholder="Start Frequency",
                                                                min=100e3, max=10e9, step=20, 
                                                                value=3.0e9,
                                                                persistence=True, 
                                                                persistence_type="local",
                                                                disabled =False,
                                                            ),
    
                                                            ],
                                                            className="mb-3",
                                                            ),
                                            dbc.InputGroup([

                                                            dbc.InputGroupText(children=["End", 
                                                                                        dbc.Select(
                                                                                            id="select-unit-freq",
                                                                                            options=[
                                                                                                {"label": "GHz", "value": 1E9},
                                                                                                {"label": "MHz", "value": 1E6},
                                                                                                {"label": "kHz", "value": 1E3},
                                                                                                {"label": "Hz", "value": 1, "disabled": False},
                                                                                            ],
                                                                                            value=1,
                                                                                            persisted_props=["value"],
                                                                                            persistence=True, 
                                                                                            persistence_type="local", 
                                                                                            required=True, 
                                                                                            # color="primary", 
                                                                                            class_name="m-1",
                                                                                            # html_size="1",
                                                                                            size='sm'
                                                                                        )
                                                                                        ],
                                                                                ), 
                                                            dbc.Input(
                                                                id="input-end-freq", 
                                                                type="number", placeholder="End Frequency",
                                                                min=100e3, max=10e9, step=20, 
                                                                value=4.0e9,
                                                                persistence=True, 
                                                                persistence_type="local",
                                                                required=True,
                                                            ),
                                                            
                                                            ],
                                                            class_name="mb-3",
                                                            ),
                                            dbc.InputGroup([
                                                            dbc.InputGroupText("Point Number"), 
                                                            dbc.Input(
                                                                id="input-num-points", type="number", placeholder="Number of Scan Points",
                                                                min=2, max=1000000, step=1,
                                                                value=300, 
                                                            )],
                                                            className="mb-3",
                                                            ),
                                            dbc.InputGroup([
                                                            dbc.InputGroupText("Iteration"), 
                                                            dbc.Input(
                                                                id="input-iterations", type="number", placeholder="Number of Iterations",
                                                                min=1, max=1000000, step=1,
                                                                value=10,
                                                            )],
                                                            className="mb-3",
                                                            ),
                                            
                                        ],
                                    ),], width=4), 
                    dbc.Col([dcc.Graph(id='live-graph', mathjax=True, animate=False), ], width=8),
                    ],
                    align="center"),# slow when animate=True 

                    dcc.Store(id='local-data', storage_type='local'),
                    dcc.Store(id='local-data-dumdum', storage_type='local'),
                    dcc.Store(id='local-data-dumdumdum', storage_type='local'),
                    dcc.Interval(id='check-exp', interval=2000, n_intervals=0), #ms
                    dcc.Interval(id='data-update', interval=100, n_intervals=0), #ms
                    dcc.Interval(id='graph-update', interval=100, n_intervals=0), #ms
                    
                ]
        self.layout = html.Div(id="main",children=children)


dbb = DashBoard()
dbb.create_applayout
layout = dbb.layout
