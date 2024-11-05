import dash_bootstrap_components as dbc
from dash import dcc, html, callback, clientside_callback
from dash.dependencies import Input, Output, ClientsideFunction, State
from measurement.task_base import JobManager, DummyMeasurement
import atexit
jm = JobManager()
def release_lock():
    return jm.stop()
atexit.register(release_lock)

ID = "drag_and_drop"
INTERVAL_DRAG_ORDER = 1000


class TaskCard(dbc.Card):
    def __init__(self, id="task", name="Task",style={
                        "display": "inline-block",
                        "width": "18rem",
                        "marginLeft": "0.2em",
                        "marginRight": "0.2em"
                    },
        value_args_optional={}, **group_args_optional
    ):  

        self.id = id
        self.id_card = self.id+"-card"
        self.id_closebutton = self.id+"-closebutton"
        self.id_status = self.id+f"status"
        self.id_progress = self.id+"-progressbar"
        self.id_botton = self.id+"-startpause"
        self.children = [                dbc.CardHeader(
                    dbc.Row(
                        children=[
                            dbc.Col(name, align="center"),
                            dbc.Col(
                                dbc.Button(
                                    html.I(className="fa fa-times", 
                                        #    style={"color": "#eb6864c7"}
                                           ),
                                    style={
                                        "horizontalAlign": "right",
                                        "backgroundColor": "transparent",
                                        "borderColor": "transparent",
                                    },
                                    color="danger",
                                    id=self.id_closebutton,
                                ), width="auto"
                            )
                        ]
                    )
                ),
                dbc.CardImg(src="https://cdn-icons-png.flaticon.com/512/3304/3304942.png",
                            top=True,
                            ),
                dbc.CardBody(
                    dbc.Col([
                        dbc.Row([
                            dbc.Col([
                                dbc.Button(
                                    "Pause", outline=True, color="warning",
                                    id=self.id_botton, n_clicks=0
                                ),
                            ]),
                            dbc.Col([
                                html.Div("Rung",id=self.id_status, className="mt-2 mb-2")
                            ])
                        ]),
                        dbc.Row(children=[
                            dbc.Col([dbc.Progress(
                                value=0.5, min=0.0, max=1.0, id=self.id_progress, animated=True, striped=True, label="",
                                color="info", className="mt-2 mb-2"
                            ),])
                        ]),
                    ]),
                ),]
        super().__init__(self.children, id=self.id_card, style=style, *value_args_optional, **group_args_optional)

layout_hidden = dbc.Row([
    dcc.Interval(id=ID+'-interval-uppdate', interval=INTERVAL_DRAG_ORDER, n_intervals=0), #ms
])

layout_orderlabel = dbc.Row([
    html.Div(
        id=ID+"-order",
        children=[]
    ), 
    dbc.Col([dbc.Button("Start Task Manager", id=ID+"-starttaskmanager")]),
    dbc.Col([dbc.Button("Add Task", id=ID+"-addtask")]),
    dbc.Col([dbc.Button("Remove Task", id=ID+"-removetask")]),
], style={"marginTop": "auto", "marginBottom": "auto", "marginLeft": "auto", "marginRight": "auto"})

layout_dragdrop = dbc.Row([
    html.Div(
        id=ID+"-drag_container",
        className="container",
        # className="bs container row",
        style={
            "display": "flex",
            "overflowX": "auto",
            "overflowY": "hidden",
            "marginLeft": "auto",
            "marginRight": "auto",
            "width": "100%"
        },
        children=[
            TaskCard(id=ID+f"task-{i}", name=f"Task {i}") for i in range(6)
        ],
    ),
])

layout_taskmanager = dbc.Col(
        id=ID+"-main",
        children=[
            layout_dragdrop,
            layout_hidden,
            layout_orderlabel
        ],
    )

@callback(
    Output(ID+"-order", "children"),
    [   Input(ID+"-interval-uppdate", "n_intervals"),
        Input(ID+"-drag_container", component_property="children"),
    ],
)
def watch_children(_n_intervals, children):
    """Display on screen the order of children"""
    dict_order = {}
    label_children = []
    for (ii, comp) in enumerate(children):
        comp_id = comp["props"]["id"]
        dict_order[comp["props"]["id"]] = ii
        label = f"{comp_id}: {ii}-th order!!"
        label_children.append(
             dbc.Alert(label, color="info"),
        )
    return label_children

@callback(Output(ID+"-starttaskmanager", "children"), 
          Input(ID+"-starttaskmanager", "n_clicks"),
          prevent_initial_call=True)
def start_taskmanager(n_clicks):
    print("n_clicks: ", n_clicks)
    if n_clicks%2 == 1:
        jm.start()
        print("start task manager")
        return ["Task Manager Running"]
    else:
        jm.stop()
        print("stop task manager")
        return ["Start Task Manager"]
    
@callback(
    Output(ID+"-addtask", "disabled"), 
    Input(ID+"-addtask", "n_clicks"),
    prevent_initial_call=True
)
def _add_task(n_clicks):
    if n_clicks%2 == 1:
        jobname = ["Alice", "Bob", "Cindy", "Don", "Eve"]
        jobpriority = [4, 1, 2, 10, 5]
        jobvar = [3,2,5,1,4]
        jobs = []
        for nn, pp, vv in zip(jobname, jobpriority, jobvar):
            jj = DummyMeasurement(name=nn)
            jj.set_priority(pp)
            jj.set_runnum(10)
            jj.set_paraset(epicpara1=6565, 
                        epicpara2=f"I ate {vv} appples", 
                        volt_amp=1,
                        freq=10.0*vv)
            jobs.append(jj)

        for jj in jobs:
            jm.submit(jj) 
            jm.remove(jobs[4])
        return True



clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="make_draggable"),
    Output(ID+"-drag_container", "data-drag"),
    [Input(ID+"-drag_container", "id")],
    [State(ID+"-drag_container", "children")],
)
