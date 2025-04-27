import random
import string

import dash
import dash_bootstrap_components as dbc
from dash import callback, dcc, html
from dash.dependencies import Input, Output

RAND_STRING_LENGTH = 8
UNIT_FREQ = {"ghz": 1e9, "mhz": 1e6, "khz": 1e3, "hz": 1.0}
UNIT_TIME = {
    "day": 86400.0,
    "hr": 3600.0,
    "min": 60.0,
    "s": 1.0,
    "ms": 1e-3,
    "us": 1e-6,
    "ns": 1e-9,
    "ps": 1e-12,
}
UNIT_VOLT = {"v": 1.0, "mv": 1e-3, "uv": 1e-6, "nv": 1e-9, "pv": 1e-12}
UNIT_METER = {"m": 1.0, "cm": 1e-2, "mm": 1e-3, "um": 1e-6, "nm": 1e-9, "pm": 1e-12}
# UNIT_FREQ = {"GHz":1E9, "MHz":1E6, "kHz":1E3, "Hz":1.0}


def random_string(length):
    # using random.choices()
    # generating random strings
    return "".join(
        random.choices(
            string.ascii_lowercase + string.ascii_uppercase + string.digits, k=length
        )
    )


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
        # namerand = f"{name}-{random_string(RAND_STRING_LENGTH)}"
        # self.id = f"input-{namerand}"
        # id_value = self.id + "-value"
        # id_data_store = f'input-store-{namerand}'
        self.id = id
        id_value = self.id
        # id_data_store = self.id + "-store"

        # datastore = value
        self.children = [
            dbc.InputGroupText(name),
            dbc.Input(
                id=id_value,
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
            ),
            dbc.InputGroupText(unit),
            # dcc.Store(
            #     id=id_data_store, storage_type=persistence_type, data=datastore
            # ),  # store the value for future access
        ]
        super().__init__(
            self.children,
            id=self.id + "-base",
            class_name=class_name,
            **group_args_optional,
        )

        callback(
            Output(f"{id_value}", "invalid"),
            Input(f"{id_value}", "value"),
            Input(f"{id_value}", "min"),
            Input(f"{id_value}", "max"),
        )(self._validate_input)

    def _validate_input(self, value, min_val, max_val):
        if value is None or value < min_val or value > max_val:
            return True  # Red border when invalid
        return False  # No red border


# class UnitedInput(dbc.InputGroup):
#     # not fully verified
#     id = "input-"

#     def __init__(
#         self,
#         name,
#         min,
#         max,
#         step,
#         value,
#         unit,
#         unitdict={},
#         id="",
#         placeholder="",
#         disabled=False,
#         persistence=True,
#         persistence_type="local",
#         class_name="mb-2",
#         value_args_optional={},
#         unit_args_optional={},
#         **group_args_optional,
#     ):
#         # determine unit dictionary automatically ###############################################
#         if unitdict == {}:
#             # determine other unit automatically,
#             unit_indicate1 = unit.lower()[-1:]
#             unit_indicate2 = unit.lower()[-2:]
#             prefactor = 1.0
#             if unit_indicate2 == "hz":
#                 prefactor = UNIT_FREQ[unit_indicate2]
#                 unitdict = {"GHz": 1e9, "MHz": 1e6, "kHz": 1e3, "Hz": 1.0}
#             elif unit_indicate1 == "s":
#                 prefactor = UNIT_TIME[unit_indicate1]
#                 if prefactor > 1.0:
#                     unitdict = {"Day": 86400.0, "Hr": 3600.0, "Min": 60.0, "s": 1.0}
#                 else:
#                     unitdict = {
#                         "s": 1.0,
#                         "ms": 1e-3,
#                         "µs": 1e-6,
#                         "ns": 1e-9,
#                         "ps": 1e-12,
#                     }
#             elif unit_indicate1 == "v":
#                 prefactor = UNIT_VOLT[unit_indicate1]
#                 unitdict = {"V": 1.0, "mV": 1e-3, "µV": 1e-6, "nV": 1e-9, "pV": 1e-12}
#             elif unit_indicate1 == "m":
#                 prefactor = UNIT_METER[unit_indicate1]
#                 unitdict = {"m": 1.0, "mm": 1e-3, "µm": 1e-6, "nm": 1e-9}
#             else:
#                 print(
#                     "Your unit is not supported. Please enter unit dictionary manually."
#                 )

#             for kk in unitdict.keys():
#                 unitdict[kk] = unitdict[kk] / prefactor

#         # set arguments for InputGroup ###############################################
#         for key, para in group_args_optional.items():
#             setattr(self, key, para)

#         if id == "":
#             id = f"input-{name}-{random_string(RAND_STRING_LENGTH)}"
#         self.id = id
#         id_value = self.id + "-value"
#         id_unit = self.id + "-unit"
#         id_temp_store = self.id + "-temp"
#         id_data_store = self.id + "-store"

#         options = [{"label": kk, "value": vv} for kk, vv in unitdict.items()]
#         tempstore = [unitdict[unit], min, max, step, value]
#         datastore = value * unitdict[unit]
#         self.children = [
#             dbc.InputGroupText(name),
#             dbc.Select(
#                 id=id_unit,
#                 options=options,
#                 value=unitdict[unit],
#                 persisted_props=["value", "options"],
#                 persistence=True,  # currently persistence fails
#                 persistence_type="local",
#                 disabled=disabled,
#                 size="sm",
#                 style={
#                     "max-width": "30%",
#                     "appearance": "none !important",
#                     "-webkit-appearance": "none !important",
#                     "-moz-appearance": "none !important",
#                 },
#                 **unit_args_optional,
#             ),
#             dbc.Input(
#                 id=id_value,
#                 type="number",
#                 placeholder=placeholder,
#                 min=min,
#                 max=max,
#                 step=step,
#                 value=value,
#                 persisted_props=["min", "max", "step", "value"],
#                 persistence=True,
#                 persistence_type="local",
#                 disabled=disabled,
#                 **value_args_optional,
#             ),
#             dcc.Store(
#                 id=id_temp_store, storage_type=persistence_type, data=tempstore
#             ),  # temporary solution to solve persistence failing problem (local persistence fails when there exists a callback that update the value)
#             dcc.Store(
#                 id=id_data_store, storage_type=persistence_type, data=datastore
#             ),  # store the value with default unit
#         ]

#         callback(
#             Output(id_unit, "value"),
#             Output(id_value, "min"),
#             Output(id_value, "max"),
#             Output(id_value, "step"),
#             Output(id_value, "value"),
#             Output(id_temp_store, "data"),
#             Output(id_data_store, "data"),
#             Input(id_unit, "value"),
#             State(id_value, "min"),
#             State(id_value, "max"),
#             State(id_value, "step"),
#             Input(id_value, "value"),
#             State(id_temp_store, "data"),
#             State(id_data_store, "data"),
#             prevent_initial_call=False,
#         )(self._update_value_by_unit)

#         super().__init__(
#             self.children, id=self.id, class_name=class_name, **group_args_optional
#         )

#     def _update_value_by_unit(self, unitval, min0, max0, step0, val0, temp, store):
#         ctx = dash.callback_context
#         changed_id = ctx.triggered_id or ""

#         try:
#             unitval = float(unitval)
#         except (ValueError, TypeError):
#             return dash.no_update

#         prev = float(temp[0])

#         # If unit changed, recalculate everything
#         if "unit" in changed_id:
#             factor = unitval / prev
#             new_min = min0 / factor
#             new_max = max0 / factor
#             new_step = step0 / factor if isinstance(step0, (int, float)) else step0
#             new_val = val0 / factor if val0 is not None else None
#             temp = [unitval, new_min, new_max, new_step, new_val]
#             store = new_val * unitval if new_val is not None else None
#             return unitval, new_min, new_max, new_step, new_val, temp, store

#         # If value changed, only update store
#         elif "value" in changed_id:
#             store = val0 * unitval if val0 is not None else None
#             return (
#                 dash.no_update,
#                 dash.no_update,
#                 dash.no_update,
#                 dash.no_update,
#                 dash.no_update,
#                 temp,
#                 store,
#             )

#         return (
#             dash.no_update,
#             dash.no_update,
#             dash.no_update,
#             dash.no_update,
#             dash.no_update,
#             dash.no_update,
#             store,
#         )


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


if __name__ == "__main__":
    GUI_PORT = 9881
    app_theme = dbc.themes.BOOTSTRAP
    app = dash.Dash(__name__, external_stylesheets=[app_theme])

    # freq_input = UnitedInput(
    #     "Freq", 3e9, 4e9, 1e6, 3.5e9, "Hz", persistence=True, id="freq"
    # )
    amp_input = NumericInput("Amp", 0, 10, 0.1, 5, unit="V", id="amp")
    sel_input = SelectInput("Mode", ["Auto", "Manual", "Test"], "Auto", id="mode")

    app.layout = dbc.Container(
        [
            html.H2("Component Demo"),
            # freq_input,
            amp_input,
            sel_input,
            html.Hr(),
            html.Div(id="output-values", className="mt-3"),
        ],
        fluid=True,
    )

    @app.callback(
        Output("output-values", "children"),
        # Input("freq-store", "data"),
        Input("amp", "value"),
        Input("mode", "value"),
    )
    # def display_values(freq, amp, mode):
    def display_values(amp, mode):
        return html.Div(
            [
                # html.P(f"Frequency: {freq:.3e} Hz" if freq else "Frequency: None"),
                html.P(f"Amplitude: {amp} V" if amp else "Amplitude: None"),
                html.P(f"Mode: {mode}"),
            ]
        )

    app.run_server(debug=True, port=GUI_PORT)
