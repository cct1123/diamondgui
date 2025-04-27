import random
import string

import dash
import dash_bootstrap_components as dbc
from dash import callback, dcc, html
from dash.dependencies import Input, Output, State

# Constants for Unit Conversion
UNIT_FREQ = {"GHz": 1e9, "MHz": 1e6, "kHz": 1e3, "Hz": 1.0}
UNIT_TIME = {"Day": 86400.0, "Hr": 3600.0, "Min": 60.0, "s": 1.0, "ms": 1e-3}
UNIT_VOLT = {"V": 1.0, "mV": 1e-3, "µV": 1e-6, "nV": 1e-9}
UNIT_METER = {"m": 1.0, "mm": 1e-3, "µm": 1e-6, "nm": 1e-9}

RAND_STRING_LENGTH = 8


def random_string(length):
    return "".join(
        random.choices(
            string.ascii_lowercase + string.ascii_uppercase + string.digits, k=length
        )
    )


class UnitInput(dbc.InputGroup):
    def __init__(
        self,
        name,
        min,
        max,
        step,
        value,
        unit,
        unitdict={},
        id="",
        placeholder="",
        disabled=False,
        persistence=True,
        persistence_type="local",
        class_name="mb-2",
        value_args_optional={},
        unit_args_optional={},
        **group_args_optional,
    ):
        # Determine unit dictionary automatically if not provided
        if unitdict == {}:
            unit_indicate1 = unit.lower()[-1:]
            unit_indicate2 = unit.lower()[-2:]
            prefactor = 1.0
            if unit_indicate2 == "hz":
                prefactor = UNIT_FREQ[unit_indicate2]
                unitdict = {"GHz": 1e9, "MHz": 1e6, "kHz": 1e3, "Hz": 1.0}
            elif unit_indicate1 == "s":
                prefactor = UNIT_TIME[unit_indicate1]
                unitdict = {"Day": 86400.0, "Hr": 3600.0, "Min": 60.0, "s": 1.0}
            elif unit_indicate1 == "v":
                prefactor = UNIT_VOLT[unit_indicate1]
                unitdict = {"V": 1.0, "mV": 1e-3, "µV": 1e-6, "nV": 1e-9}
            elif unit_indicate1 == "m":
                prefactor = UNIT_METER[unit_indicate1]
                unitdict = {"m": 1.0, "mm": 1e-3, "µm": 1e-6, "nm": 1e-9}
            else:
                print(
                    "Your unit is not supported. Please enter unit dictionary manually."
                )

            # Scale all units in the dictionary
            for kk in unitdict.keys():
                unitdict[kk] = unitdict[kk] / prefactor

        # Set arguments for InputGroup
        if id == "":
            id = f"input-{name}-{random_string(RAND_STRING_LENGTH)}"
        self.id = id
        id_value = self.id + "-value"
        id_unit = self.id + "-unit"
        id_data_store = self.id + "-store"

        options = [{"label": kk, "value": vv} for kk, vv in unitdict.items()]
        datastore = value * unitdict[unit]
        self.children = [
            dbc.InputGroupText(name),
            dbc.Select(
                id=id_unit,
                options=options,
                value=unitdict[unit],
                persistence=True,
                persistence_type="local",
                disabled=disabled,
                size="sm",
                **unit_args_optional,
            ),
            dbc.Input(
                id=id_value,
                type="number",
                placeholder=placeholder,
                min=min,
                max=max,
                step=step,
                value=value,
                persistence=True,
                persistence_type="local",
                disabled=disabled,
                **value_args_optional,
            ),
            dcc.Store(id=id_data_store, storage_type=persistence_type, data=datastore),
        ]

        # Callback to update value when unit changes
        @callback(
            Output(id_value, "value"),
            Output(id_data_store, "data"),
            Output(id_unit, "value"),
            Input(id_unit, "value"),
            Input(id_value, "value"),
            State(id_data_store, "data"),
            prevent_initial_call=False,
        )
        def update_value_by_unit(unit, value, prev_data):
            prev_unit = prev_data / value if value != 0 else 1.0
            new_value = value * (unit / prev_unit) if value is not None else None
            return new_value, new_value, unit

        super().__init__(
            self.children, id=self.id, class_name=class_name, **group_args_optional
        )


# === Example Dash App ===
if __name__ == "__main__":
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    app.layout = dbc.Container(
        [
            html.H1("Unit Input Example"),
            UnitInput(
                name="Frequency",
                min=0,
                max=1000,
                step=1,
                value=100,
                unit="Hz",
                unitdict=UNIT_FREQ,
                placeholder="Enter frequency",
                class_name="mb-3",
            ),
            html.Div(id="output-value"),
        ],
        fluid=True,
    )

    # Display the value in real-time
    @app.callback(
        Output("output-value", "children"),
        Input("input-Frequency", "value"),
    )
    def display_value(value):
        return f"Current value: {value}"

    app.run_server(debug=True, port=8050)
