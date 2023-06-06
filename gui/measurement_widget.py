
from dash import Dash, html, callback, dcc
from dash.dependencies import Output, Input, State
import dash_bootstrap_components as dbc

from components import UnitedInput, NumericInput

import string
import random
RAND_STRING_LENGTH = 8
def random_string(length):
    # using random.choices()
    # generating random strings
    return ''.join(random.choices(string.ascii_lowercase + 
                                  string.ascii_uppercase +
                                  string.digits, k=length))

mea_name = "epicmeasurement"
randname = random_string(RAND_STRING_LENGTH)
iidd = mea_name + randname
id_temp_store = f"temp-store-{iidd}"
id_para_form = f"para-form-{iidd}"
persistence_type = "local"
paramform = dbc.Container([
    dbc.Col([
            UnitedInput("Freq Begin", 3e9, 4e9, 20, 3.5e9, "Hz"),
            UnitedInput("Freq End", 3e9, 4e9, 20, 3.5e9, "Hz"),
            UnitedInput("Freq Step", 3e9, 4e9, 20, 3.5e9, "Hz"),
            NumericInput("Iteration", 0, 100, 1, 5),
            UnitedInput("Freq54353", 3e9, 4e9, 20, 3.5e9, "Hz"),
            UnitedInput("Freq", 3e9, 4e9, 20, 3.5e9, "Hz"),
        ], 
        id=id_para_form,
        width=12
    ), 
    dcc.Store(id=id_temp_store,storage_type=persistence_type, data=[]), # store the parameters for future access
    ], 
)


button_group = dbc.Container([
    dbc.Row([
        dbc.ButtonGroup([
            dbc.Button("Run", id=f"button-{iidd}-run", outline=True, color="success", active=False, n_clicks=0), 
            dbc.Button("Pause",  id=f"button-{iidd}-pause",outline=True, color="warning", n_clicks=0), 
            dbc.Button("Stop",  id=f"button-{iidd}-stop", outline=True, color="danger", n_clicks=0),
        ],),
        # dbc.Col([html.Div(id="div-status", children=[]),]),
        dbc.Progress(
            value=0, id="progress-bar", animated=True, striped=False, label="",
        ),
        ],
        align="center",
    )
    ], 
)

if __name__ == "__main__":
    GUI_PORT = 9871
    app_theme = dbc.themes.JOURNAL
    app = Dash(
        __name__, 
        external_stylesheets=[
            app_theme, 
        ], 
    )
    # cc = CustomComponents()
    app.layout = dbc.Container([ 
        dbc.Row([
            dbc.Col([
                    paramform
                ], 
                width=4
            ),
            dbc.Col([
                    button_group,
                    dcc.Graph(id='live-graph', mathjax=True, animate=False), 
                ], 
                width=8
            ),
        ]),            
        dbc.Button(id="fkbutton"),
        dcc.Store(id="temperstore"),
        dbc.Alert(id="alert-display", children=["This is a primary alert"], color="primary"),
        dbc.Input(
            id="trtgeswgfsdfgds", 
            type="number", 
            placeholder="fdsfdsfsdfsdfsdf",
            min=0, max=5000000, step=0.1, 
            value=454,
            persisted_props=["value"],
            # persistence=persistence, 
            # persistence_type=persistence_type,
            persistence=True, 
            persistence_type='local',
        ),          
        ],
        fluid=True,
        id="main"
    )


    @app.callback(
        Output("alert-display", "children"),
        Output(id_temp_store, "data"),
        Input("fkbutton", "n_clicks"),
        State(id_para_form, "children"),
        prevent_initial_call=True,
        )
    def _submit_para(_, wearetheworld):
        para_dict = dict()
        for comp in wearetheworld:
            # print(comp['props']['id'])
            for ccc in comp['props']['children']:
                if 'id' in ccc['props'].keys():
                    if 'input-store' in ccc['props']['id']:
                        para_name = ccc['props']['id'].split("-")[2]
                        para_dict[para_name] = ccc['props']['data'][-1]
        return [f"Parameter '{kk}': {vv}\n" for kk, vv in para_dict.items()], para_dict
    app.run_server(debug=True, port=GUI_PORT)
