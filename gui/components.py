import dash
from dash import html
import dash_bootstrap_components as dbc
from dash import callback
from dash.dependencies import Output, Input, State
from dash import dcc
import time

import string
import random


RAND_STRING_LENGTH = 8
UNIT_FREQ = {"ghz":1E9, "mhz":1E6, "khz":1E3, "hz":1.0}
UNIT_TIME = {"day":86400.0, "hr":3600.0, "min":60.0, "s":1.0, "ms":1E-3, "us":1E-6, "ns":1E-9, "ps":1E-12}
UNIT_VOLT = {"v":1.0, "mv":1E-3, "uv":1E-6, "nv":1E-9, "pv":1E-12}
UNIT_METER = {"m":1.0, "cm":1E-2, "mm":1E-3, "um":1E-6, "nm":1E-9, "pm":1E-12}
# UNIT_FREQ = {"GHz":1E9, "MHz":1E6, "kHz":1E3, "Hz":1.0}


def random_string(length):
    # using random.choices()
    # generating random strings
    return ''.join(random.choices(string.ascii_lowercase + 
                                  string.ascii_uppercase +
                                  string.digits, k=length))


class NumericInput(dbc.InputGroup):
    def __init__(self, 
        name, min, max, step, value,
        id="input", placeholder="", disabled=False, persistence=True, 
        persistence_type="local", class_name="mb-2",
        value_args_optional={}, **group_args_optional
    ):  
        # namerand = f"{name}-{random_string(RAND_STRING_LENGTH)}"
        # self.id = f"input-{namerand}"
        # id_value = self.id + "-value"
        # id_data_store = f'input-store-{namerand}' 
        self.id = id
        id_value = self.id + "-value"
        id_data_store = self.id + "-store"

        datastore = value
        self.children = [
            dbc.InputGroupText(name), 
            dbc.Input(
                    id=id_value,
                    type="number", 
                    placeholder=placeholder,
                    min=min, max=max, step=step, 
                    value=value,
                    persisted_props=["min", "max", "step", "value"],
                    persistence=persistence, 
                    persistence_type=persistence_type,
                    disabled=disabled,
                    **value_args_optional
                ),  
            dcc.Store(id=id_data_store,storage_type=persistence_type, data=datastore) # store the value for future access
        ]
        super().__init__(self.children, id=self.id, class_name=class_name, **group_args_optional)

        callback(
                Output(id_data_store, 'data'),
                Input(id_value, 'value'),
                prevent_initial_call=False,
            )(self._store_value)
    def _store_value(self, value):
        return value


class UnitedInput(dbc.InputGroup):
    id = "input-"
    def __init__(self,
        name, min, max, step, value, unit, 
        unitdict={}, id="", placeholder="", disabled=False, persistence=True, 
        persistence_type="local", class_name="mb-2", 
        value_args_optional={}, unit_args_optional={}, **group_args_optional
    ):

        # determine unit dictionary automatically ###############################################
        if unitdict == {}:
            # determine other unit automatically, 
            unit_indicate1 = unit.lower()[-1:]
            unit_indicate2 = unit.lower()[-2:]
            prefactor = 1.0
            if unit_indicate2 == "hz":
                prefactor = UNIT_FREQ[unit_indicate2]
                unitdict = {"GHz":1E9, "MHz":1E6, "kHz":1E3, "Hz":1.0}
            elif unit_indicate1 == "s":
                prefactor = UNIT_TIME[unit_indicate1]
                if prefactor > 1.0:
                    unitdict = {"Day":86400.0, "Hr":3600.0, "Min":60.0, "s":1.0}
                else:
                    unitdict = {"s":1.0, "ms":1E-3, "µs":1E-6, "ns":1E-9, "ps":1E-12}
            elif  unit_indicate1 == "v":
                prefactor = UNIT_VOLT[unit_indicate1]
                unitdict = {"V":1.0, "mV":1E-3, "µV":1E-6, "nV":1E-9, "pV":1E-12}
            elif unit_indicate1 == "m":
                prefactor = UNIT_METER[unit_indicate1]
                unitdict = {"m":1.0, "mm":1E-3, "µm":1E-6, "nm":1E-9}
            else:
                print("Your unit is not supported. Please enter unit dictionary manually.")

            for kk in unitdict.keys():
                unitdict[kk] = unitdict[kk]/prefactor

        # set arguments for InputGroup ###############################################
        for key, para in group_args_optional.items():
            setattr(self, key, para)

        if id == "":
            id = f"input-{name}-{random_string(RAND_STRING_LENGTH)}"
        self.id = id
        id_value = self.id + "-value"
        id_unit = self.id + "-unit"
        id_temp_store = self.id + "-temp"
        id_data_store = self.id + "-store"

        # # namerand = name
        # namerand = f"{name}-{random_string(RAND_STRING_LENGTH)}"
        # self.id = f"input-{namerand}"
        # id_value = self.id + "-value"
        # id_unit = self.id + "-unit"
        # id_temp_store = f'temp-store-{namerand}'
        # id_data_store = f'input-store-{namerand}' # store the value with default unit

        options = [{"label": kk, "value": vv} for kk, vv in unitdict.items()]
        tempstore = [unitdict[unit], min, max, step, value ]
        datastore = value*unitdict[unit]
        self.children = [
            dbc.InputGroupText(name),   
            dbc.Select(
                    id=id_unit,
                    options=options,
                    value=unitdict[unit],
                    persisted_props=["value", "options"],
                    # persistence=persistence, 
                    # persistence_type=persistence_type,
                    persistence=True, # currently persistence fails
                    persistence_type='local',
                    disabled=disabled,
                    size = "sm",
                    style={
                        "max-width":"30%",
                        "appearance": "none !important",
                        "-webkit-appearance": "none !important",
                        "-moz-appearance": "none !important",
                    },
                    # class_name="dropdown-container",
                    # class_name="select", 
                    **unit_args_optional
                ),                      
            dbc.Input(
                id=id_value, 
                type="number", 
                placeholder=placeholder,
                min=min, max=max, step=step, 
                value=value,
                persisted_props=["min", "max", "step", "value"],
                # persistence=persistence, 
                # persistence_type=persistence_type,
                persistence=True, # currently persistence fails
                persistence_type='local',
                disabled=disabled,
                **value_args_optional
            ),  
            dcc.Store(id=id_temp_store,storage_type=persistence_type, data=tempstore), # temporary solution to solve persistence failing problem (local persistence fails when there exists a callback that update the value)
            dcc.Store(id=id_data_store,storage_type=persistence_type, data=datastore) # store the value with default unit
        ]

        callback(
                # Output(id_unit, 'options'),
                Output(id_unit, 'value'),
                Output(id_value, 'min'), 
                Output(id_value, 'max'), 
                Output(id_value, 'step'), 
                Output(id_value, 'value'), 
                Output(id_temp_store, 'data'),
                Output(id_data_store, 'data'),
                # State(id_unit, 'options'),
                Input(id_unit, 'value'),
                State(id_value, 'min'),
                State(id_value, 'max'),
                State(id_value, 'step'),
                Input(id_value, 'value'),
                State(id_temp_store, 'data'),
                State(id_data_store, 'data'),
                prevent_initial_call=False,
            )(self._update_value_by_unit)

        super().__init__(self.children, id=self.id, class_name=class_name, **group_args_optional)

    def _update_value_by_unit(self, unitvalue, min0, max0, step0, value0, temp, data):
        ctx = dash.callback_context
        input_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if "input-" in input_id:
            # when the unit is changed, or user input a new value
            unitvalue_previous = float(temp[0])
            prefactor = float(unitvalue)/unitvalue_previous
            if value0 != None:
                temp = [unitvalue, min0/prefactor, max0/prefactor, step0 if type(step0)==str else (step0/prefactor), value0/prefactor]
                data = value0*unitvalue_previous
                print(f"value with default unit: {data}")
            else:
                temp[-1] = None
        else:
            # handle the inital callback ####################################
            if temp[-1] == None:
                print("reset the default value")
                print(value0)
                temp = [unitvalue, min0, max0, step0, value0]
                data = value0*unitvalue
        return *temp, temp, data
        


        

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
    app.layout = dbc.Container([              
            UnitedInput("Freq", 3e9, 4e9, 20, 3.5e9, "Hz", class_name="mb-2"),
        ],
        fluid=True,
        id="main"
    )

    app.run_server(debug=True, port=GUI_PORT)

