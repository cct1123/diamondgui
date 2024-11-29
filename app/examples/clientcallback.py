import json

import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, callback, clientside_callback, dcc, html

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = Dash(__name__, external_stylesheets=external_stylesheets)

df = pd.read_csv(
    "https://raw.githubusercontent.com/plotly/datasets/master/gapminderDataFiveYear.csv"
)

available_countries = df["country"].unique()


graph_layout = html.Div(
    [
        dcc.Graph(id="clientside-graph-px"),
        dcc.Store(id="clientside-figure-store-px"),
        "Indicator",
        dcc.Dropdown(
            {
                "pop": "Population",
                "lifeExp": "Life Expectancy",
                "gdpPercap": "GDP per Capita",
            },
            "pop",
            id="clientside-graph-indicator-px",
        ),
        "Country",
        dcc.Dropdown(available_countries, "Canada", id="clientside-graph-country-px"),
        "Graph scale",
        dcc.RadioItems(["linear", "log"], "linear", id="clientside-graph-scale-px"),
        html.Hr(),
        html.Details(
            [
                html.Summary("Contents of figure storage"),
                dcc.Markdown(id="clientside-figure-json-px"),
            ]
        ),
    ]
)

app = Dash(__name__)

gui.layout = html.Div(
    [
        dcc.Store(id="notification-permission"),
        html.Button("Notify", id="notify-btn"),
        html.Div(id="notification-output"),
        graph_layout,
    ]
)


@callback(
    Output("clientside-figure-store-px", "data"),
    Input("clientside-graph-indicator-px", "value"),
    Input("clientside-graph-country-px", "value"),
)
def update_store_data(indicator, country):
    dff = df[df["country"] == country]
    return px.scatter(dff, x="year", y=str(indicator))


clientside_callback(
    """
    function(figure, scale) {
        if(figure === undefined) {
            return {'data': [], 'layout': {}};
        }
        const fig = Object.assign({}, figure, {
            'layout': {
                ...figure.layout,
                'yaxis': {
                    ...figure.layout.yaxis, type: scale
                }
             }
        });
        return fig;
    }
    """,
    Output("clientside-graph-px", "figure"),
    Input("clientside-figure-store-px", "data"),
    Input("clientside-graph-scale-px", "value"),
)


@callback(
    Output("clientside-figure-json-px", "children"),
    Input("clientside-figure-store-px", "data"),
)
def generated_px_figure_json(data):
    return "```\n" + json.dumps(data, indent=2) + "\n```"


clientside_callback(
    """
    function() {
        return navigator.permissions.query({name:'notifications'})
    }
    """,
    Output("notification-permission", "data"),
    Input("notify-btn", "n_clicks"),
    prevent_initial_call=True,
)

clientside_callback(
    """
    function(result) {
        if (result.state == 'granted') {
            new Notification("Dash notification", { body: "Notification already granted!"});
            return null;
        } else if (result.state == 'prompt') {
            return new Promise((resolve, reject) => {
                Notification.requestPermission().then(res => {
                    if (res == 'granted') {
                        new Notification("Dash notification", { body: "Notification granted!"});
                        resolve();
                    } else {
                        reject(`Permission not granted: ${res}`)
                    }
                })
            });
        } else {
            return result.state;
        }
    }
    """,
    Output("notification-output", "children"),
    Input("notification-permission", "data"),
    prevent_initial_call=True,
)

if __name__ == "__main__":
    gui.run(debug=True)
