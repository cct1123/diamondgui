import random
import string

import dash
import dash_bootstrap_components as dbc
from dash import callback, dcc
from dash.dependencies import Input, Output, State

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
    id = "input-"

    def __init__(
        self,
        name,
        min,
        max,
        step,
        value,
        placeholder="",
        disabled=False,
        persistence=True,
        persistence_type="local",
        class_name="mb-3",
        value_args_optional={},
        **group_args_optional,
    ):
        self.id = f"input-{name}-{random_string(RAND_STRING_LENGTH)}"
        self.children = [
            dbc.InputGroupText(name),
            dbc.Input(
                id=self.id + "-value",
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
                **value_args_optional,
            ),
        ]
        super().__init__(
            self.children, id=self.id, class_name=class_name, **group_args_optional
        )


class UnitedInput(dbc.InputGroup):
    id = "input-"

    def __init__(
        self,
        name,
        min,
        max,
        step,
        value,
        unit,
        unitdict={},
        placeholder="",
        disabled=False,
        persistence=True,
        persistence_type="local",
        class_name="mb-3",
        value_args_optional={},
        unit_args_optional={},
        **group_args_optional,
    ):
        # determine unit dictionary automatically ###############################################
        if unitdict == {}:
            # determine other unit automatically,
            unit_indicate1 = unit.lower()[-1:]
            unit_indicate2 = unit.lower()[-2:]
            prefactor = 1.0
            if unit_indicate2 == "hz":
                prefactor = UNIT_FREQ[unit_indicate2]
                unitdict = {"GHz": 1e9, "MHz": 1e6, "kHz": 1e3, "Hz": 1.0}
            elif unit_indicate1 == "s":
                prefactor = UNIT_TIME[unit_indicate1]
                if prefactor > 1.0:
                    unitdict = {"Day": 86400.0, "Hr": 3600.0, "Min": 60.0, "s": 1.0}
                else:
                    unitdict = {
                        "s": 1.0,
                        "ms": 1e-3,
                        "µs": 1e-6,
                        "ns": 1e-9,
                        "ps": 1e-12,
                    }
            elif unit_indicate1 == "v":
                prefactor = UNIT_VOLT[unit_indicate1]
                unitdict = {"V": 1.0, "mV": 1e-3, "µV": 1e-6, "nV": 1e-9, "pV": 1e-12}
            elif unit_indicate1 == "m":
                prefactor = UNIT_METER[unit_indicate1]
                unitdict = {"m": 1.0, "mm": 1e-3, "µm": 1e-6, "nm": 1e-9}
            else:
                print(
                    "Your unit is not supported. Please enter unit dictionary manually."
                )

            for kk in unitdict.keys():
                unitdict[kk] = unitdict[kk] / prefactor

        # set arguments for InputGroup ###############################################
        for key, para in group_args_optional.items():
            setattr(self, key, para)
        namerand = f"{name}-{random_string(RAND_STRING_LENGTH)}"
        self.id = f"input-{namerand}"
        id_value = self.id + "-value"
        id_unit = self.id + "-unit"
        id_store = f"temp-store-{namerand}"

        options = [{"label": kk, "value": vv} for kk, vv in unitdict.items()]
        temp_data = [options, unitdict[unit], min, max, step, value]
        self.children = [
            dbc.InputGroupText(name),
            dbc.Select(
                id=id_unit,
                options=[{"label": kk, "value": vv} for kk, vv in unitdict.items()],
                value=unitdict[unit],
                persisted_props=["value", "options"],
                # persistence=persistence,
                # persistence_type=persistence_type,
                persistence=True,  # currently persistence fails
                persistence_type="local",
                disabled=disabled,
                size="sm",
                style={
                    "max-width": "20%",
                    "appearance": "none !important",
                    "-webkit-appearance": "none !important",
                    "-moz-appearance": "none !important",
                },
                # class_name="dropdown-container",
                # class_name="select",
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
                persisted_props=["min", "max", "step", "value"],
                # persistence=persistence,
                # persistence_type=persistence_type,
                persistence=True,  # currently persistence fails
                persistence_type="local",
                disabled=disabled,
                **value_args_optional,
            ),
            dcc.Store(
                id=id_store, storage_type="local", data=temp_data
            ),  # temporary solution to solve persistence failing problem (local persistence fails when there exists a callback that update the value)
        ]

        callback(
            Output(id_unit, "options"),
            Output(id_unit, "value"),
            Output(id_value, "min"),
            Output(id_value, "max"),
            Output(id_value, "step"),
            Output(id_value, "value"),
            Output(id_store, "data"),
            State(id_unit, "options"),
            Input(id_unit, "value"),
            State(id_value, "min"),
            State(id_value, "max"),
            State(id_value, "step"),
            Input(id_value, "value"),
            State(id_store, "data"),
            prevent_initial_call=False,
        )(self._update_value_by_unit)

        super().__init__(
            self.children, id=self.id, class_name=class_name, **group_args_optional
        )

    def _update_value_by_unit(
        self, unitoptions, unitvalue, min0, max0, step0, value0, datastore
    ):
        ctx = dash.callback_context
        input_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if "input-" in input_id:
            # when the unit is changed, or user input a new value
            prefactor = float(unitvalue)
            for ii, unitlv in enumerate(unitoptions):
                unitoptions[ii]["value"] = float(f'{(unitlv["value"]/prefactor):.4e}')
            if value0 != None:
                datastore = [
                    unitoptions,
                    1.0,
                    min0 / prefactor,
                    max0 / prefactor,
                    step0 / prefactor,
                    value0 / prefactor,
                ]
            else:
                datastore[-1] = None
        else:
            # handle the inital callback ####################################
            if datastore[-1] == None:
                print("reset the default value")
                print(value0)
                datastore = [unitoptions, unitvalue, min0, max0, step0, value0]
        return *datastore, datastore


# class CustomComponents():


#     def __init__(self):
#         pass

#     def UnitedInput(self,
#         name, min, max, step, value, unit,
#         unitdict={}, placeholder="", disabled=False, persistence=True, persistence_type="local",
#         value_args_optional={}, unit_args_optional={}, **group_args_optional
#     ):
#         id = f"input-{name}"
#         id_value = id + "-value"
#         id_unit = id + "-unit"


#         # determine unit dictionary automatically ###############################################
#         if unitdict == {}:
#             # determine other unit automatically,
#             unit_indicate1 = unit.lower()[-1:]
#             unit_indicate2 = unit.lower()[-2:]
#             prefactor = 1.0
#             if unit_indicate2 == "hz":
#                 prefactor = UNIT_FREQ[unit_indicate2]
#                 unitdict = {"GHz":1E9, "MHz":1E6, "kHz":1E3, "Hz":1.0}
#             elif unit_indicate1 == "s":
#                 prefactor = UNIT_TIME[unit_indicate1]
#                 if prefactor > 1.0:
#                     unitdict = {"Day":86400.0, "Hr":3600.0, "Min":60.0, "s":1.0}
#                 else:
#                     unitdict = {"s":1.0, "ms":1E-3, "µs":1E-6, "ns":1E-9, "ps":1E-12}
#             elif  unit_indicate1 == "v":
#                 prefactor = UNIT_VOLT[unit_indicate1]
#                 unitdict = {"V":1.0, "mV":1E-3, "µV":1E-6, "nV":1E-9, "pV":1E-12}
#             elif unit_indicate1 == "m":
#                 prefactor = UNIT_METER[unit_indicate1]
#                 unitdict = {"m":1.0, "mm":1E-3, "µm":1E-6, "nm":1E-9}
#             else:
#                 print("Your unit is not supported. Please enter unit dictionary manually.")

#             for kk in unitdict.keys():
#                 unitdict[kk] = unitdict[kk]/prefactor


#         children = [
#             dbc.InputGroupText(name),
#             dbc.Select(
#                     id=id_unit,
#                     options=[{"label": kk, "value": vv} for kk, vv in unitdict.items()],
#                     value=unitdict[unit],
#                     persisted_props=["value"],
#                     persistence=persistence,
#                     persistence_type=persistence_type,
#                     disabled = disabled,
#                     size = "sm",
#                     style={
#                         "max-width":"20%",
#                         "appearance": "none !important",
#                         "-webkit-appearance": "none !important",
#                         "-moz-appearance": "none !important",
#                     },
#                     # class_name="dropdown-container",
#                     # class_name="select",
#                     **unit_args_optional
#                 ),
#             dbc.Input(
#                 id=id_value,
#                 type="number",
#                 placeholder=placeholder,
#                 min=min, max=max, step=step,
#                 value=value,
#                 persisted_props=["value"],
#                 persistence=persistence,
#                 persistence_type=persistence_type,
#                 disabled = disabled,
#                 **value_args_optional
#             ),
#         ]
#         callback(
#                 Output(id_unit, 'options'),
#                 Output(id_unit, 'value'),
#                 Output(id_value, 'min'),
#                 Output(id_value, 'max'),
#                 Output(id_value, 'step'),
#                 Output(id_value, 'value'),
#                 # Output(self.id_unit, 'value'),
#                 Input(id_unit, 'options'),
#                 Input(id_unit, 'value'),
#                 State(id_value, 'min'),
#                 State(id_value, 'max'),
#                 State(id_value, 'step'),
#                 State(id_value, 'value'),
#             )(self._update_value_by_unit)

#         return dbc.InputGroup(
#             children,
#             id=id,
#             # persistence=persistence,
#             # persistence_type=persistence_type,
#             **group_args_optional
#             )


#     def _update_value_by_unit(self, unitdict, unitvalue, min0, max0, step0, value0):
#         print("HI!!! I am called!")
#         prefactor = float(unitvalue)
#         print(f"{unitvalue}, {min0}, {max0}, {step0}, {value0}")
#         for ii, unitlv in enumerate(unitdict):
#             unitdict[ii]["value"] = float(f'{(unitlv["value"]/prefactor):.4e}')
#         options = unitdict
#         print(options)
#         return options, 1.0, min0/prefactor, max0/prefactor, step0/prefactor, value0/prefactor


if __name__ == "__main__":
    GUI_PORT = 9881
    app_theme = dbc.themes.JOURNAL
    app = dash.Dash(
        __name__,
        external_stylesheets=[
            app_theme,
        ],
    )
    # cc = CustomComponents()
    app.layout = dbc.Container(
        [
            UnitedInput("Freq", 3e9, 4e9, 20, 3.5e9, "Hz", class_name="mb-3"),
            # dbc.Input(
            #     id="trtgeswgfsdfgds",
            #     type="number",
            #     placeholder="fdsfdsfsdfsdfsdf",
            #     min=0, max=5000000, step=0.1,
            #     value=454,
            #     persisted_props=["value"],
            #     # persistence=persistence,
            #     # persistence_type=persistence_type,
            #     persistence=True,
            #     persistence_type='local',
            # ),
        ],
        fluid=True,
        id="main",
    )

    app.run_server(debug=True, port=GUI_PORT)
