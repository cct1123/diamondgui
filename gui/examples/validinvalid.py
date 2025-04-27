import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

# External CSS (using the Bootstrap theme)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.JOURNAL])

app.layout = html.Div(
    [
        html.H1("Bootstrap Input Validation Example"),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Label("Enter a number between 1 and 10"),
                        dcc.Input(
                            id="number-input",
                            type="number",
                            min=1,
                            max=10,
                            step=1,
                            className="form-control",  # Bootstrap form-control for styling
                        ),
                        html.Div(
                            id="input-feedback"
                        ),  # To provide feedback if necessary
                    ]
                )
            ]
        ),
    ]
)


@app.callback(Output("input-feedback", "children"), [Input("number-input", "value")])
def validate_input(value):
    # Check if the value is None or outside the valid range
    if value is None or value < 1 or value > 10:
        return "Input is invalid. Please enter a number between 1 and 10."
    return f"Valid input: {value}"


if __name__ == "__main__":
    app.run_server(debug=True)
