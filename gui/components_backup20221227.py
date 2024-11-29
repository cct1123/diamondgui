import dash_bootstrap_components as dbc



import string
import random


RAND_STRING_LENGTH = 4
UNIT_FREQ = {"ghz":1E9, "mhz":1E6, "khz":1E3, "hz":1.0}
UNIT_TIME = {"day":86400.0, "hr":3600.0, "min":60.0, "s":1.0, "ms":1E-3, "us":1E-6, "ns":1E-9, "ps":1E-12}
UNIT_VOLT = {"v":1.0, "mv":1E-3, "uv":1E-6, "nv":1E-9, "pv":1E-12}
UNIT_METER = {"m":1.0, "cm":1E-2, "mm":1E-3, "um":1E-6, "nm":1E-9, "pm":1E-12}
# UNIT_FREQ = {"GHz":1E9, "MHz":1E6, "kHz":1E3, "Hz":1.0}


def random_string(length):
    # using random.choices()
    # generating random strings
    return ''.join(random.choices(string.ascii_lowercase +
                                string.digits, k=length))

class UnitedInput(dbc.InputGroup):

    id = "input"
    id_value = "input-value"
    id_unit = "input-unit"

    _prop_names = [
        'children', 'id', 'className', 'class_name', 'key', 'loading_state', 'size', 'style', # props of dbc InputGroup
        'disabled', 'placeholder', 'persistence_type', 'persistence', 'min', 'max', 'step', 'value',  # some props of dbc Input
        'unit', 'name' # some custom props
        ]

    available_properties = [
        'children', 'id', 'className', 'class_name', 'key', 'loading_state', 'size', 'style', 
        'disabled', 'placeholder', 'persistence_type', 'persistence', 'min', 'max', 'step', 'value', 
        'unit', 'name'
        ]

    # ['autoComplete', 'autoFocus', 'autocomplete', 'autofocus', 'className', 'class_name', 
    # 'debounce', 'disabled', 'html_size', 'inputMode', 'inputmode', 'invalid', 'key', 'list', 
    # 'loading_state', 'max', 'maxLength', 'maxlength', 'min', 'minLength', 'minlength', 'n_blur', 
    # 'n_blur_timestamp', 'n_submit', 'n_submit_timestamp', 'name', 'pattern', 'persisted_props', 
    # 'persistence', 'persistence_type', 'placeholder', 'plaintext', 'readonly', 'required', 'size', 
    # 'step', 'style', 'tabIndex', 'tabindex', 'type', 'valid', 'value'] 

    # def __init__(self, name):
    def __init__(
        self, name, min, max, step, value, unit, 
        unitdict={}, placeholder="", disabled=False, persistence=True, persistence_type="local", 
        value_args_optional={}, unit_args_optional={}, **group_args_optional
    ):


        self.name = name
        self.min = min
        self.max = max
        self.step = step
        self.value = value
        self.unit = unit
        self.unitdict = unitdict
        self.placeholder = placeholder
        self.disabled = disabled
        self.persistence = persistence
        self.persistence_type = persistence_type

        self.id = f"input-{name}"
        self.id_value = self.id + "-value"
        self.id_unit = self.id + "-unit"
        # self.className="mb-3"
        # self.class_name = self.className

        if self.unitdict == {}:
            # determine other unit automatically, 
            unit_indicate1 = self.unit.lower()[-1:]
            unit_indicate2 = self.unit.lower()[-2:]
            prefactor = 1.0
            if unit_indicate2 == "hz":
                prefactor = UNIT_FREQ[unit_indicate2]
                self.unitdict = {"GHz":1E9, "MHz":1E6, "kHz":1E3, "Hz":1.0}
            elif unit_indicate1 == "s":
                prefactor = UNIT_TIME[unit_indicate1]
                if prefactor > 1.0:
                    self.unitdict = {"Day":86400.0, "Hr":3600.0, "Min":60.0, "s":1.0}
                else:
                    self.unitdict = {"s":1.0, "ms":1E-3, "µs":1E-6, "ns":1E-9, "ps":1E-12}
            elif  unit_indicate1 == "v":
                prefactor = UNIT_VOLT[unit_indicate1]
                self.unitdict = {"V":1.0, "mV":1E-3, "µV":1E-6, "nV":1E-9, "pV":1E-12}
            elif unit_indicate1 == "m":
                prefactor = UNIT_METER[unit_indicate1]
                self.unitdict = {"m":1.0, "mm":1E-3, "µm":1E-6, "nm":1E-9}
            else:
                print("Your unit is not supported. Please enter unit dictionary manually.")

            for kk in self.unitdict.keys():
                    self.unitdict[kk]/prefactor

        for name, para in group_args_optional.items():
            if name in self._prop_names:
                setattr(self, name, para)
            else:
                raise TypeError(f"The '{self.__class__}' component  with the ID '{self.id}' received an unexpected keyword argument: '{name}'\nAllowed arguments: {self.available_properties}")

        self.children = [
                dbc.InputGroupText(self.name),   
                dbc.Select(
                        id=self.id_value,
                        options=[{"label": kk, "value": vv} for kk, vv in self.unitdict.items()],
                        value=self.unitdict[self.unit],
                        # persisted_props=["value"],
                        persistence=self.persistence, 
                        persistence_type=self.persistence_type,
                        disabled = self.disabled,
                        size = "sm",
                        style={
                            "max-width":"20%",
                            "appearance": "none !important",
                            "-webkit-appearance": "none !important",
                            "-moz-appearance": "none !important",
                        },
                        # class_name="dropdown-container",
                        # class_name="select", 
                        **unit_args_optional
                    ),                      
                dbc.Input(
                    id=self.id_unit, 
                    type="number", 
                    placeholder=self.placeholder,
                    min=min, max=max, step=step, 
                    value=self.value,
                    persistence=self.persistence, 
                    persistence_type=self.persistence_type,
                    disabled = self.disabled,
                    **value_args_optional
                ),            
            ],
            


if __name__ == "__main__":
    aaa = UnitedInput("Freq", 3e9, 4e9, 20, 3.5e9, "Hz", class_name="fdsfds")
    # ggg = dbc.InputGroup([dbc.InputGroupText("Start"), dbc.Select(), dbc.Input(
    #                             id="input-start-freq", 
    #                             type="number", placeholder="Start Frequency",
    #                             min=100e3, max=10e9, step=20, 
    #                             value=3.0e9,
    #                             persistence=True, 
    #                             persistence_type="local",
    #                             disabled =False,
    #                         )], className="fdwfsd")
    # # print(ggg.__dict__.keys())
    # print(type(ggg))
    # print(aaa.layout.__dict__)

    # iii = dbc.Input(id="input-start-freq", type="number", placeholder="Start Frequency",min=1, max=11111, step=1, value=22,persistence=True, persistence_type="local",disabled =False)
    # print(iii.__dict__)





