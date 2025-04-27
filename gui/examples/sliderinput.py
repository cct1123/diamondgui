import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, callback, dcc, html


# === SelectInput Class ===
class SelectInput(dbc.InputGroup):
    def __init__(
        self,
        name,
        options,
        value,
        unit="",
        id="select",
        placeholder="",
        disabled=False,
        persistence=True,
        persistence_type="local",
        class_name="mb-2",
        value_args_optional={},
        **group_args_optional,
    ):
        self.id = id
        id_value = self.id
        id_data_store = self.id + "-store"

        datastore = value
        self.children = [
            dbc.InputGroupText(name),
            dbc.Select(
                id=id_value,
                options=[{"label": opt, "value": opt} for opt in options],
                value=value,
                placeholder=placeholder,
                persistence=persistence,
                persistence_type=persistence_type,
                disabled=disabled,
                **value_args_optional,
            ),
            dbc.InputGroupText(unit),
            dcc.Store(
                id=id_data_store,
                storage_type=persistence_type,
                data=datastore,
            ),
        ]

        super().__init__(
            self.children,
            id=self.id + "-base",
            class_name=class_name,
            **group_args_optional,
        )

        callback(
            Output(id_data_store, "data"),
            Input(id_value, "value"),
            prevent_initial_call=False,
        )(self._store_value)

    def _store_value(self, value):
        return value


# === SliderInput Class ===
class SliderInput(dbc.InputGroup):
    def __init__(
        self,
        name,
        min,
        max,
        step,
        value,
        unit="",
        id="slider",
        disabled=False,
        tooltip=True,
        marks=None,
        persistence=True,
        persistence_type="local",
        class_name="mb-4",
        value_args_optional={},
        **group_args_optional,
    ):
        self.id = id
        id_slider = self.id
        id_data_store = self.id + "-store"

        if marks is None:
            marks = {
                int(min): str(min),
                int(max): str(max),
            }

        datastore = value
        self.children = [
            dbc.InputGroupText(name),
            html.Div(
                dcc.Slider(
                    id=id_slider,
                    min=min,
                    max=max,
                    step=step,
                    value=value,
                    marks=marks,
                    tooltip={"always_visible": tooltip, "placement": "bottom"},
                    persistence=persistence,
                    persistence_type=persistence_type,
                    disabled=disabled,
                    **value_args_optional,
                ),
                style={"flexGrow": 1, "padding": "0 10px"},
            ),
            dbc.InputGroupText(unit),
            dcc.Store(
                id=id_data_store,
                storage_type=persistence_type,
                data=datastore,
            ),
        ]

        super().__init__(
            self.children,
            id=self.id + "-base",
            class_name=class_name,
            style={"alignItems": "center"},
            **group_args_optional,
        )

        callback(
            Output(id_data_store, "data"),
            Input(id_slider, "value"),
            prevent_initial_call=False,
        )(self._store_and_label_value)

    def _store_and_label_value(self, value):
        return value, f"{value}"


# === Demo App ===
if __name__ == "__main__":
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    # Instantiate components
    select_component = SelectInput(
        name="Mode",
        options=["Auto", "Manual", "Off"],
        value="Auto",
        id="mode-select",
        unit="",
    )

    slider_component = SliderInput(
        name="Power",
        min=0,
        max=100,
        marks={ii: "{}".format(ii) for ii in range(0, 100, 10)},
        step=1,
        value=50,
        unit="%",
        id="power-slider",
    )

    app.layout = dbc.Container(
        [
            html.H2("Custom Component Demo"),
            select_component,
            html.Div(id="select-output", className="mb-4"),
            slider_component,
            html.Div(id="slider-output", className="mb-4"),
        ],
        fluid=True,
    )

    @callback(
        Output("select-output", "children"),
        Input("mode-select-store", "data"),
    )
    def update_select_output(value):
        return f"Selected mode: {value}"

    @callback(
        Output("slider-output", "children"),
        Input("power-slider-store", "data"),
    )
    def update_slider_output(value):
        return f"Power level: {value}%"

    app.run_server(debug=True)
    app.run_server(debug=True)
