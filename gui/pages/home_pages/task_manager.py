import atexit

import dash_bootstrap_components as dbc
import numpy as np
from dash import callback, clientside_callback, dcc, html
from dash.dependencies import ClientsideFunction, Input, Output, State
from gui.pages.measurement_pages.dummeasurement_page import dumdumodmr
from gui.pages.measurement_pages.dummeasurement_page_copy import dumdumodmr_copy

from measurement.dumdummeasurement import DummyODMR
from measurement.task_base import JobManager

jm = JobManager()


def release_lock():
    return jm.stop()


atexit.register(release_lock)

ID = "drag_and_drop"
INTERVAL_DRAG_ORDER = 1000


class TaskCard(dbc.Card):
    INTERVAL_CARD_STATUS = 500

    def __init__(
        self,
        id: str = "task",
        name: str = "Task",
        task=None,
        task_uiid=None,
        style: dict = {
            "display": "inline-block",
            "width": "18rem",
            "marginLeft": "0.2em",
            "marginRight": "0.2em",
        },
        value_args_optional={},
        **group_args_optional,
    ):
        self.id = id
        self.id_card = self.id + "-card"
        self.id_closebutton = self.id + "-card" + "-closebutton"
        self.id_status = self.id + "-card" + "status"
        self.id_progress = self.id + "-card" + "-progressbar"
        self.id_botton = self.id + "-card" + "-startpause"
        self.id_store = self.id + "-card" + "-store"
        self.id_interval = self.id + "-card" + "-interval"

        self.task = task
        self.task_uiid = task_uiid

        layout_hidden = dbc.Row(
            [
                dcc.Interval(
                    id=self.id_interval,
                    interval=self.INTERVAL_CARD_STATUS,
                    n_intervals=0,
                ),
                dcc.Store(id=self.id_store, storage_type="memory", data={}),
            ]
        )
        self.children = [
            layout_hidden,
            dbc.CardHeader(
                dbc.Row(
                    children=[
                        dbc.Col(name, align="center"),
                        dbc.Col(
                            dbc.Button(
                                html.I(
                                    className="fa fa-times",
                                    #    style={"color": "#eb6864c7"}
                                ),
                                style={
                                    "horizontalAlign": "right",
                                    "backgroundColor": "transparent",
                                    "borderColor": "transparent",
                                },
                                color="danger",
                                id=self.id_closebutton,
                            ),
                            width="auto",
                        ),
                    ]
                )
            ),
            dbc.CardImg(
                src="https://cdn-icons-png.flaticon.com/512/3304/3304942.png",
                top=True,
            ),
            dbc.CardBody(
                dbc.Col(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Button(
                                            "Pause",
                                            outline=True,
                                            color="warning",
                                            id=self.id_botton,
                                            n_clicks=0,
                                        ),
                                    ],
                                    width="auto",
                                ),
                                dbc.Col([html.Div(id=self.id_status)], width="auto"),
                            ]
                        ),
                        dbc.Row(
                            children=[
                                dbc.Col(
                                    [
                                        dbc.Progress(
                                            value=0.0,
                                            min=0.0,
                                            max=1.0,
                                            id=self.id_progress,
                                            animated=True,
                                            striped=True,
                                            label="",
                                            color="info",
                                            className="mt-2 mb-2",
                                        ),
                                    ]
                                )
                            ]
                        ),
                    ]
                ),
            ),
        ]
        super().__init__(
            self.children,
            id=self.id_card,
            style=style,
            *value_args_optional,
            **group_args_optional,
        )

        if task_uiid is not None:
            print("hi i have a task_uiid")
            callback(
                Output(self.id_progress, "value"),
                Output(self.id_progress, "label"),
                Input(self.id_store, "data"),
                prevent_initial_call=True,
            )(self._update_progress)

            callback(
                Output(self.id_store, "data"),
                Input(self.id_interval, "n_intervals"),
                prevent_initial_call=True,
            )(self._update_storestate)

            callback(
                Output(self.id_card, "className"),
                # Input(ID+"-interval-uppdate", "n_intervals"),
                Input(self.id_store, "data"),
                prevent_initial_call=True,
            )(self._update_cardfade)

    def _update_progress(self, stateset):
        progress_num = stateset["idx_run"] / stateset["num_run"]
        progress_time = stateset["time_run"] / stateset["time_stop"]
        progress = max(progress_num, progress_time)
        print(f"progress = {progress}")
        # print(f"progress = {progress}")
        return progress, f"{(100*progress):.0f}%"

    def _update_storestate(self, _n_interval):
        return self.task.stateset

    def _update_cardfade(self, stateset):
        print(stateset["state"])
        if stateset["state"] == "run" or stateset["state"] == "wait":
            print("show the task!!!")
            return "fade show"
        else:
            print("hide the task!!!")
            return "fade"


layout_hidden = dbc.Row(
    [
        dcc.Interval(
            id=ID + "-interval-uppdate", interval=INTERVAL_DRAG_ORDER, n_intervals=0
        ),  # ms
    ]
)

layout_orderlabel = dbc.Row(
    [
        html.Div(id=ID + "-order", children=[]),
        dbc.Col([dbc.Button("Start Task Manager", id=ID + "-starttaskmanager")]),
        dbc.Col([dbc.Button("Appear Tasks", id=ID + "-appeartasks")]),
        dbc.Col([dbc.Button("Get Task List", id=ID + "-maketasklist")]),
        dbc.Col([dbc.Button("Add Task", id=ID + "-addtask")]),
        dbc.Col([dbc.Button("Remove Task", id=ID + "-removetask")]),
    ],
    style={
        "marginTop": "auto",
        "marginBottom": "auto",
        "marginLeft": "auto",
        "marginRight": "auto",
    },
)

layout_dragdrop = dbc.Row(
    [
        html.Div(
            id=ID + "-drag_container",
            className="container",
            # className="bs container row",
            style={
                "display": "flex",
                "overflowX": "auto",
                "overflowY": "hidden",
                "marginLeft": "auto",
                "marginRight": "auto",
                "width": "100%",
            },
            children=[
                # dbc.Fade(TaskCard(id=f"task-{i}", name=f"Task {i}"),
                # id=f"task-fade-{i}",
                # is_in=False,
                # appear=False, style={
                #             "display": "inline-block",
                #             "width": "18rem",
                #             "marginLeft": "0.2em",
                #             "marginRight": "0.2em"
                #         })
                TaskCard(
                    id=dumdumodmr.get_name(),
                    name=dumdumodmr.get_classname(),
                    task=dumdumodmr,
                    task_uiid=dumdumodmr.get_uiid(),
                ),
                TaskCard(
                    id=dumdumodmr_copy.get_name(),
                    name=dumdumodmr_copy.get_classname() + "COPY",
                    task=dumdumodmr_copy,
                    task_uiid=dumdumodmr.get_uiid(),
                ),
                # TaskCard(id=f"{ID}-task-{i}", name=f"Task {i}", className="fade")
                # TaskCard(id=f"{ID}-task-{i}", name=f"Task {i}")
                # for i in range(6)
            ],
        ),
    ]
)

layout_taskmanager = dbc.Col(
    id=ID + "-main",
    children=[layout_dragdrop, layout_hidden, layout_orderlabel],
)
# @callback(
#     Output(ID+"-drag_container", "children"),
#     # Input(ID+"-interval-uppdate", "n_intervals"),
#     Input(ID+"-maketasklist", "n_clicks"),
#     prevent_initial_call=True
# )
# def update_dragdroplist(_n_intervals):
#     """Display on screen the order of children"""
#     tasks = [jm.running] + jm.queue if jm.running is not None else jm.queue
#     print(jm.running)
#     print(jm.queue)
#     tasks.sort(key=lambda job: job.priority, reverse=True)
#     print(tasks)
#     return [
#         TaskCard(id=job.get_name(), name=job.get_classname(), task=job, task_uiid=job.get_uiid()) for job in tasks
#     ]

# @callback(
#     Output("task-fade-0", "is_in"),
#     Output("task-fade-3", "is_in"),
#     Output("task-fade-2", "is_in"),
#     # Input(ID+"-interval-uppdate", "n_intervals"),
#     Input(ID+"-appeartasks", "n_clicks"),
#     prevent_initial_call=True
# )
# def update_dragdroplist(n_clicks):
#     """Display on screen the order of children"""
#     if n_clicks%2 == 1:
#         return True, True, True
#     else:
#         return False,False,False


@callback(
    Output(ID + "-starttaskmanager", "children"),
    Input(ID + "-starttaskmanager", "n_clicks"),
    prevent_initial_call=True,
)
def start_taskmanager(n_clicks):
    print("n_clicks: ", n_clicks)
    if n_clicks % 2 == 1:
        jm.start()
        print("start task manager")
        return ["Task Manager Running"]
    else:
        jm.stop()
        print("stop task manager")
        return ["Start Task Manager"]


@callback(
    Output(ID + "-addtask", "disabled"),
    Input(ID + "-addtask", "n_clicks"),
    prevent_initial_call=True,
)
def _add_task(_nclicks):
    randomidx = np.random.randint(0, 100)
    jj = DummyODMR(name=f"Fake Task {randomidx}")
    # jj.set_priority(0)
    jj.set_runnum(10)
    jj.set_paraset(
        epicpara1=6565,
        epicpara2=f"I ate {randomidx} appples",
        volt_amp=1,
        freq=10.0 * randomidx,
    )
    jm.submit(jj)
    return False


clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="make_draggable"),
    Output(ID + "-drag_container", "data-drag"),
    [Input(ID + "-drag_container", "id")],
    [State(ID + "-drag_container", "children")],
)


# srfsdfsd23432454353


# @callback()
# def _remove_task(name):
#     print("remove task: ", name)
#     return

# @callback()
# def _update_taskschedule(_n_interval):

#     print("update taskschedule: ")
#     return
(
    (
        "props",
        {
            "children": [
                {
                    "props": {
                        "children": {
                            "props": {
                                "children": [
                                    {
                                        "props": {
                                            "children": "Task 5",
                                            "align": "center",
                                        },
                                        "type": "Col",
                                        "namespace": "dash_bootstrap_components",
                                    },
                                    {
                                        "props": {
                                            "children": {
                                                "props": {
                                                    "children": {
                                                        "props": {
                                                            "children": None,
                                                            "className": "fa fa-times",
                                                        },
                                                        "type": "I",
                                                        "namespace": "dash_html_components",
                                                    },
                                                    "id": "drag_and_drop-task-5-card-closebutton",
                                                    "color": "danger",
                                                    "style": {
                                                        "horizontalAlign": "right",
                                                        "backgroundColor": "transparent",
                                                        "borderColor": "transparent",
                                                    },
                                                },
                                                "type": "Button",
                                                "namespace": "dash_bootstrap_components",
                                            },
                                            "width": "auto",
                                        },
                                        "type": "Col",
                                        "namespace": "dash_bootstrap_components",
                                    },
                                ]
                            },
                            "type": "Row",
                            "namespace": "dash_bootstrap_components",
                        }
                    },
                    "type": "CardHeader",
                    "namespace": "dash_bootstrap_components",
                },
                {
                    "props": {
                        "children": None,
                        "src": "https://cdn-icons-png.flaticon.com/512/3304/3304942.png",
                        "top": True,
                    },
                    "type": "CardImg",
                    "namespace": "dash_bootstrap_components",
                },
                {
                    "props": {
                        "children": {
                            "props": {
                                "children": [
                                    {
                                        "props": {
                                            "children": [
                                                {
                                                    "props": {
                                                        "children": [
                                                            {
                                                                "props": {
                                                                    "children": "Pause",
                                                                    "id": "drag_and_drop-task-5-card-startpause",
                                                                    "color": "warning",
                                                                    "n_clicks": 0,
                                                                    "outline": True,
                                                                },
                                                                "type": "Button",
                                                                "namespace": "dash_bootstrap_components",
                                                            }
                                                        ],
                                                        "width": "auto",
                                                    },
                                                    "type": "Col",
                                                    "namespace": "dash_bootstrap_components",
                                                },
                                                {
                                                    "props": {
                                                        "children": [
                                                            {
                                                                "props": {
                                                                    "children": None,
                                                                    "id": "drag_and_drop-task-5-cardstatus",
                                                                },
                                                                "type": "Div",
                                                                "namespace": "dash_html_components",
                                                            }
                                                        ],
                                                        "width": "auto",
                                                    },
                                                    "type": "Col",
                                                    "namespace": "dash_bootstrap_components",
                                                },
                                            ]
                                        },
                                        "type": "Row",
                                        "namespace": "dash_bootstrap_components",
                                    },
                                    {
                                        "props": {
                                            "children": [
                                                {
                                                    "props": {
                                                        "children": [
                                                            {
                                                                "props": {
                                                                    "children": None,
                                                                    "id": "drag_and_drop-task-5-card-progressbar",
                                                                    "animated": True,
                                                                    "className": "mt-2 mb-2",
                                                                    "color": "info",
                                                                    "label": "",
                                                                    "max": 1,
                                                                    "min": 0,
                                                                    "striped": True,
                                                                    "value": 0.5,
                                                                },
                                                                "type": "Progress",
                                                                "namespace": "dash_bootstrap_components",
                                                            }
                                                        ]
                                                    },
                                                    "type": "Col",
                                                    "namespace": "dash_bootstrap_components",
                                                }
                                            ]
                                        },
                                        "type": "Row",
                                        "namespace": "dash_bootstrap_components",
                                    },
                                ]
                            },
                            "type": "Col",
                            "namespace": "dash_bootstrap_components",
                        }
                    },
                    "type": "CardBody",
                    "namespace": "dash_bootstrap_components",
                },
            ],
            "id": "drag_and_drop-task-5-card",
            "className": "fade",
            "style": {
                "display": "inline-block",
                "width": "18rem",
                "marginLeft": "0.2em",
                "marginRight": "0.2em",
            },
        },
    ),
    ("type", "Card"),
    ("namespace", "dash_bootstrap_components"),
)
(
    (
        "props",
        {
            "children": [
                {
                    "props": {
                        "children": {
                            "props": {
                                "children": [
                                    {
                                        "props": {
                                            "children": "Task 5",
                                            "align": "center",
                                        },
                                        "type": "Col",
                                        "namespace": "dash_bootstrap_components",
                                    },
                                    {
                                        "props": {
                                            "children": {
                                                "props": {
                                                    "children": {
                                                        "props": {
                                                            "children": None,
                                                            "className": "fa fa-times",
                                                        },
                                                        "type": "I",
                                                        "namespace": "dash_html_components",
                                                    },
                                                    "id": "drag_and_drop-task-5-card-closebutton",
                                                    "color": "danger",
                                                    "style": {
                                                        "horizontalAlign": "right",
                                                        "backgroundColor": "transparent",
                                                        "borderColor": "transparent",
                                                    },
                                                },
                                                "type": "Button",
                                                "namespace": "dash_bootstrap_components",
                                            },
                                            "width": "auto",
                                        },
                                        "type": "Col",
                                        "namespace": "dash_bootstrap_components",
                                    },
                                ]
                            },
                            "type": "Row",
                            "namespace": "dash_bootstrap_components",
                        }
                    },
                    "type": "CardHeader",
                    "namespace": "dash_bootstrap_components",
                },
                {
                    "props": {
                        "children": None,
                        "src": "https://cdn-icons-png.flaticon.com/512/3304/3304942.png",
                        "top": True,
                    },
                    "type": "CardImg",
                    "namespace": "dash_bootstrap_components",
                },
                {
                    "props": {
                        "children": {
                            "props": {
                                "children": [
                                    {
                                        "props": {
                                            "children": [
                                                {
                                                    "props": {
                                                        "children": [
                                                            {
                                                                "props": {
                                                                    "children": "Pause",
                                                                    "id": "drag_and_drop-task-5-card-startpause",
                                                                    "color": "warning",
                                                                    "n_clicks": 0,
                                                                    "outline": True,
                                                                },
                                                                "type": "Button",
                                                                "namespace": "dash_bootstrap_components",
                                                            }
                                                        ],
                                                        "width": "auto",
                                                    },
                                                    "type": "Col",
                                                    "namespace": "dash_bootstrap_components",
                                                },
                                                {
                                                    "props": {
                                                        "children": [
                                                            {
                                                                "props": {
                                                                    "children": None,
                                                                    "id": "drag_and_drop-task-5-cardstatus",
                                                                },
                                                                "type": "Div",
                                                                "namespace": "dash_html_components",
                                                            }
                                                        ],
                                                        "width": "auto",
                                                    },
                                                    "type": "Col",
                                                    "namespace": "dash_bootstrap_components",
                                                },
                                            ]
                                        },
                                        "type": "Row",
                                        "namespace": "dash_bootstrap_components",
                                    },
                                    {
                                        "props": {
                                            "children": [
                                                {
                                                    "props": {
                                                        "children": [
                                                            {
                                                                "props": {
                                                                    "children": None,
                                                                    "id": "drag_and_drop-task-5-card-progressbar",
                                                                    "animated": True,
                                                                    "className": "mt-2 mb-2",
                                                                    "color": "info",
                                                                    "label": "",
                                                                    "max": 1,
                                                                    "min": 0,
                                                                    "striped": True,
                                                                    "value": 0.5,
                                                                },
                                                                "type": "Progress",
                                                                "namespace": "dash_bootstrap_components",
                                                            }
                                                        ]
                                                    },
                                                    "type": "Col",
                                                    "namespace": "dash_bootstrap_components",
                                                }
                                            ]
                                        },
                                        "type": "Row",
                                        "namespace": "dash_bootstrap_components",
                                    },
                                ]
                            },
                            "type": "Col",
                            "namespace": "dash_bootstrap_components",
                        }
                    },
                    "type": "CardBody",
                    "namespace": "dash_bootstrap_components",
                },
            ],
            "id": "drag_and_drop-task-5-card",
            "className": "fade show",
            "style": {
                "display": "inline-block",
                "width": "18rem",
                "marginLeft": "0.2em",
                "marginRight": "0.2em",
            },
        },
    ),
    ("type", "Card"),
    ("namespace", "dash_bootstrap_components"),
)
