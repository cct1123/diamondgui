import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, html


class NumericInput(dbc.InputGroup):
    def __init__(
        self,
        name,
        min,
        max,
        step,
        value,
        unit="",
        id="input",
        placeholder="",
        disabled=False,
        persistence=True,
        persistence_type="local",
        class_name="mb-2",
        group_args_optional={},
        **value_args_optional,
    ):
        self.id = id
        id_input = f"{id}-value"

        self.input = dbc.Input(
            id=id_input,
            type="number",
            placeholder=placeholder,
            min=min,
            max=max,
            step=step,
            value=value,
            persisted_props=["min", "max", "step", "value"],
            persistence=persistence,
            persistence_type=persistence_type,
            disabled=disabled,
            className="form-control",
            **value_args_optional,
        )

        self.children = [
            dbc.InputGroupText(name),
            self.input,
            dbc.InputGroupText(unit),
        ]

        super().__init__(
            self.children,
            id=f"{id}-base",
            class_name=class_name,
            **group_args_optional,
        )

    @staticmethod
    def register_callbacks(app, input_id: str, min_val: float, max_val: float):
        """Registers a validation callback for the input."""

        @app.callback(
            Output(f"{input_id}-value", "invalid"),
            Input(f"{input_id}-value", "value"),
        )
        def validate_input(value):
            if value is None or value < min_val or value > max_val:
                return True  # Red border when invalid
            return False  # No red border


# Create Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Instantiate custom numeric input
numeric_input = NumericInput(
    name="Voltage",
    min=0,
    max=5,
    step=0.1,
    value=1.2,
    unit="V",
    id="voltage-input",
)

# Define app layout
app.layout = dbc.Container(
    [
        html.H4("Numeric Input with Red Border on Invalid"),
        numeric_input,
    ]
)

# Register validation callback
numeric_input.register_callbacks(app, "voltage-input", min_val=0, max_val=5)

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
