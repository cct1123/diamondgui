import dash_bootstrap_components as dbc
from dash import dcc, html, callback
from measurement.task_base import JobManager, DummyMeasurement

jm = JobManager()
jm.start()

class TaskCard(dbc.Card):
    def __init__(self, id="task", name="Task",style={
                        "display": "inline-block",
                        "width": "18rem",
                        "margin-left": "0.2em",
                        "margin-right": "0.2em"
                    },
        value_args_optional={}, **group_args_optional
    ):  
        # namerand = f"{name}-{random_string(RAND_STRING_LENGTH)}"
        # self.id = f"input-{namerand}"
        # id_value = self.id + "-value"
        # id_data_store = f'input-store-{namerand}' 

        self.id = id
        self.id_card = self.id+"-card"
        self.id_status = self.id+f"status"
        self.id_progress = self.id+"-progressbar"
        self.id_botton = self.id+"-startpause"
        self.children = [
                        dbc.CardHeader(name),
                        dbc.CardImg(src="https://cdn-icons-png.flaticon.com/512/3304/3304942.png",
                                    top=True,
                                    ),
                        dbc.CardBody(
                            dbc.Col([
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Button(
                                            "Pause", outline=True, color="warning",
                                            id=self.id_botton , n_clicks=0
                                        ),
                                    ], width=2),
                                    dbc.Col([
                                        html.Div(id=self.id_status)
                                    ], width=8)
                                ]),
                                dbc.Row(children=[
                                    dbc.Col([dbc.Progress(
                                        value=0.5, min=0.0, max=1.0, id=self.id_progress, animated=True, striped=True, label="",
                                        color="info", className="mt-2 mb-2"
                                    ),])
                                ]),
                            ]),
                        ),
                    ]
        super().__init__(self.children, id=self.id_card, style=style, **group_args_optional)

        callback(
                Output(id_data_store, 'data'),
                Input(id_value, 'value'),
                prevent_initial_call=False,
            )(self._store_value)
        
    def _update_progress(self, value):
        # print("update progress: ", value)
        return value
    
    def _update_status(self, value):
        # print("update status: ", value)
        return value
    
    def _update_botton(self, value):
        # print("update botton: ", value)
        return value
    
    def _store_value(self, value):
        # print("store value: ", value)
        return value

layout_hidden = dbc.Row([
    dcc.Interval(id=ID+'interval-uppdate', interval=INTERVAL_DRAG_ORDER, n_intervals=0), #ms
])

layout_taskmanager = dbc.Row([
    dbc.Col([
        TaskCard(id="task-1", name="Task 1"),
        TaskCard(id="task-2", name="Task 2"),
    ], width=6),
    dbc.Col([
        TaskCard(id="task-3", name="Task 3"),
        TaskCard(id="task-4", name="Task 4"),
    ])
])

@callback()
def _add_task(name):
    print("add task: ", name)
    return 

@callback()
def _remove_task(name):
    print("remove task: ", name)
    return 

@callback()
def _update_taskschedule(_n_interval):
    
    print("update taskschedule: ")
    return 


if __name__ == "__main__":
    import dash
    app = dash.Dash(
        __name__,
        external_scripts=["https://cdnjs.cloudflare.com/ajax/libs/dragula/3.7.2/dragula.min.js"],
        external_stylesheets=[dbc.themes.BOOTSTRAP]
    )
    app.layout = dbc.Col(
        id="main",
        children=[
            layout_taskmanager,
        ],
    )
    app.run_server(debug=True)