import dash
import dash_bootstrap_components as dbc
import dash_html_components as html

app = dash.Dash(__name__)

gui.layout = html.Div(
    [
        html.Div(
            [
                html.Button(
                    "Button",
                    id="button",
                    style={"height": "30px", "vertical-align": "middle"},
                ),
                dbc.Progress(
                    id="progress",
                    value=50,
                    max=100,
                    style={
                        "height": "30px",
                        "vertical-align": "middle",
                        "width": "200px",
                        "display": "inline-block",
                    },
                ),
            ],
            style={"display": "flex", "align-items": "center"},
        )
    ]
)

if __name__ == "__main__":
    gui.run_server()
