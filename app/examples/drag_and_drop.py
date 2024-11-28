import dash
import dash_bootstrap_components as dbc
from dash import callback, clientside_callback, dcc, html
from dash.dependencies import ClientsideFunction, Input, Output, State

ID = "drag_and_drop"
INTERVAL_DRAG_ORDER = 100000


layout_hidden = dbc.Row(
    [
        dcc.Interval(
            id=ID + "interval-uppdate", interval=INTERVAL_DRAG_ORDER, n_intervals=0
        ),  # ms
    ]
)

layout_orderlabel = dbc.Row(
    [html.Div(id=ID + "order", children=[])],
    style={
        "marginTop": "auto",
        "marginBottom": "auto",
        "marginLeft": "auto",
        "marginRight": "auto",
    },
)

layout_draggablecontainer = dbc.Row(
    [
        html.Div(
            id=ID + "drag_container",
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
                dbc.Card(
                    [
                        dbc.CardHeader(f"Card {i}"),
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
                                                        id=ID + f"button-pause-{i}",
                                                        n_clicks=0,
                                                    ),
                                                ]
                                            ),
                                            dbc.Col(
                                                [
                                                    html.Div(
                                                        "Rung",
                                                        id=ID + f"status-{i}",
                                                        className="mt-2 mb-2",
                                                    )
                                                ]
                                            ),
                                        ]
                                    ),
                                    dbc.Row(
                                        children=[
                                            dbc.Col(
                                                [
                                                    dbc.Progress(
                                                        value=0.5,
                                                        min=0.0,
                                                        max=1.0,
                                                        id=ID + f"-progressbar-{i}",
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
                    ],
                    id=ID + f"child-{i}",
                    style={
                        "display": "inline-block",
                        "width": "18rem",
                        "marginLeft": "0.2em",
                        "marginRight": "0.2em",
                    },
                )
                for i in range(6)
            ],
        ),
    ]
)


@callback(
    Output(ID + "order", "children"),
    [
        Input(ID + "interval-uppdate", "n_intervals"),
        Input(ID + "drag_container", component_property="children"),
    ],
)
def watch_children(_n_intervals, children):
    """Display on screen the order of children"""
    dict_order = {}
    label_children = []
    for ii, comp in enumerate(children):
        comp_id = comp["props"]["id"]
        dict_order[comp["props"]["id"]] = ii
        label = f"{comp_id}: {ii}-th order!!"
        label_children.append(
            dbc.Alert(label, color="info"),
        )
    return label_children


clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="make_draggable"),
    Output(ID + "drag_container", "data-drag"),
    [Input(ID + "drag_container", "id")],
    [State(ID + "drag_container", "children")],
)

if __name__ == "__main__":
    app = dash.Dash(
        __name__,
        external_scripts=[
            "https://cdnjs.cloudflare.com/ajax/libs/dragula/3.7.2/dragula.min.js"
        ],
        external_stylesheets=[dbc.themes.BOOTSTRAP],
    )
    app.layout = dbc.Col(
        id="main",
        children=[
            layout_hidden,
            layout_draggablecontainer,
            layout_orderlabel,
        ],
    )
    app.run_server(debug=True)
