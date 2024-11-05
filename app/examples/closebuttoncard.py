
import json

import dash
import dash_bootstrap_components as dbc
from dash import html
from dash.dependencies import ALL, Input, Output, State
from dash.exceptions import PreventUpdate

# FONT_AWESOME = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css"
app = dash.Dash(external_stylesheets=[dbc.themes.JOURNAL, dbc.icons.FONT_AWESOME])

app.layout = dbc.Container(
    [
        dbc.InputGroup(
            [
                dbc.Input(id="input"),
                dbc.Row(
                    dbc.Button("Add card", id="add-button"),
                ),
            ],
            className="mb-4",
        ),
        html.Div([], id="output"),
    ],
    className="p-5",
)


def make_card(n_add, content):
    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row(
                    children=[
                        dbc.Col("Card header", align="center"),
                        dbc.Col(
                            dbc.Button(
                                html.I(className="fa fa-times", style={"color": "#eb6864c7"}),
                                style={
                                    "horizontalAlign": "right",
                                    "backgroundColor": "transparent",
                                    "borderColor": "transparent",
                                },
                                color="danger",
                                id={"type": "close-button", "index": n_add},
                            ), width="auto"
                        )
                    ]
                )
            ),
            dbc.CardBody(html.P(content, className="card-text")),
        ],
        id={"type": "card", "index": n_add},
        style={"width": "400px"},
        className="mb-3 mx-auto",
    )


@app.callback(
    Output("output", "children"),
    [
        Input("add-button", "n_clicks"),
        Input({"type": "close-button", "index": ALL}, "n_clicks"),
    ],
    [
        State("input", "value"),
        State("output", "children"),
        State({"type": "close-button", "index": ALL}, "id"),
    ],
)
def manage_cards(n_add, n_close, content, children, close_id):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate
    else:
        button_id, _ = ctx.triggered[0]["prop_id"].split(".")

    if button_id == "add-button":
        if n_add:
            if children is None:
                children = []
            children.append(make_card(n_add, content))
    else:
        button_id = json.loads(button_id)
        index_to_remove = button_id["index"]
        children = [
            child
            for child in children
            if child["props"]["id"]["index"] != index_to_remove
        ]

    return children


if __name__ == "__main__":
    app.run_server(debug=True)