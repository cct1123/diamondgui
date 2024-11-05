"""
hardware control page

To do/solve (2023/01/09):
○ Synchronize the Laser input parameters when the page is loaded
○ Allows command input

"""
import time
import dash
from dash import dcc, html, callback, callback_context
from dash.dependencies import Output, Input, State
import dash_bootstrap_components as dbc
import dash_daq as ddaq
from hardware.hardwaremanager import HardwareManager
import logging
logger = logging.getLogger(__name__)

try:
    from hardware.hardwaremanager import HardwareManager
    hm = HardwareManager()
    logger.info(f"Calling Hardware Manager from '{__name__}': {hm}")
    max_laser_power = hm.laser.get_max_laser_power()
    max_laser_current = hm.laser.get_max_laser_current()
except:
    max_laser_power = 150.0
    max_laser_current = 363.6


import random
import string
ID = "lasercontrol-"+''.join(
    random.choices(
        string.ascii_lowercase +
        string.ascii_uppercase +
        string.digits, k=8
    ))+"-"
COLOR_INDICATOR = "rgba(var(--bs-info-rgb),var(--bs-bg-opacity))!important"
COLOR_BG = "rgba(var(--bs-body-bg-rgb),var(--bs-bg-opacity))!important"
COLOR_TEXT = "rgba(var(--bs-body-color-rgb)"

# input layout and callback -------------------------------------------------

layout_input = dbc.Col([
    html.H3("Input", className="p-2 mb-1 text-center",),
    dbc.ButtonGroup([
        dbc.Button(
            children=["Fire"], 
            id=ID+"button-fire", 
            outline=True, 
            color="info", 
            className="me-1", 
        ),
        # dbc.Button("Connect", color="success", className="me-1"),
    ], 
    className="mb-3",
    ),
    dbc.InputGroup([
        dbc.InputGroupText("Constant Mode"),
        dbc.Row([dbc.RadioItems(
            options=[
                {"label": "Power", "value": "power"},
                {"label": "Current", "value": "current"},
            ],
            value="power",
            id=ID+"radioitems-constant-mode",
            inline=True,
            persistence=True,
        ),], align="center", className="border"),
        dbc.InputGroupText(""),
    ],
    className="mb-3",
    ),
    dbc.InputGroup([
        dbc.InputGroupText("Analog Modulation"),
        dbc.Row([dbc.RadioItems(
            options=[
                {"label": "External", "value": "ext"},
                {"label": "Internal", "value": "int"},
            ],
            value="ext",
            id=ID+"radioitems-analog-modulation",
            inline=True,
            persistence=True,
        ),], align="center", className="border"),
        # dbc.InputGroupText(""),
    ],
    className="mb-3",
    ),
    dbc.InputGroup([
        dbc.InputGroupText("modmodmod Type"),
        dbc.Row([dbc.RadioItems(
            options=[
                {"label": "CW", "value": "cw"},
                {"label": "Modulated", "value": "modulated"},
            ],
            value="cw",
            id=ID+"radioitems-modulation-type",
            inline=True,
            persistence=True,
        ),], align="center", className="border"),
        # dbc.InputGroupText(""),
    ],
    className="mb-3",
    ),
    dbc.InputGroup([
        dbc.InputGroupText("Digital Modulation"),
        dbc.Row([dbc.RadioItems(
            options=[
                {"label": "External", "value": "ext"},
                {"label": "Internal", "value": "int"},
            ],
            value="ext",
            id=ID+"radioitems-digital-modulation",
            inline=True,
            persistence=True,
        ),], align="center", className="border"),
        # dbc.InputGroupText(""),
    ],
    className="mb-3",
    ),
    dbc.InputGroup([
        dbc.InputGroupText("Power"),
        dbc.Input(
            id=ID+"input-power",
            type="number",
            min=0.0,
            max=max_laser_power,
            step=0.1, 
            value=50.0,
            persistence=True,
            disabled=False,
        ),
        dbc.InputGroupText("mW"),
    ],
    className="mb-3",
    ),
    dbc.InputGroup([
        dbc.InputGroupText("Current"),
        dbc.Input(
            id=ID+"input-current",
            type="number",
            min=0.0,
            max=max_laser_current,
            step=0.1, 
            value=50.0,
            persistence=True,
            disabled=False,
        ),
        dbc.InputGroupText("mA"),
    ],
    className="mb-3",
    ),
    dbc.InputGroup([
        dbc.InputGroupText("Command"),
        dbc.Input(
            id=ID+"input-command",
            placeholder="Input command and press 'enter' ", 
            type="text",
            persistence=True,
            disabled=False,
        ),
    ],
    className="mb-3",
    ),
],
)


@callback(
    Output(ID+"button-fire", "outline"), 
    Output(ID+"button-fire", "color"), 
    Output(ID+"button-fire", "children"), 
    Input(ID+"button-fire", "n_clicks"),
    State(ID+"button-fire", "children"),
    State(ID+"alert-status", "children"),
    prevent_initial_call=False
)
def _update_fire(n_clicks, fire_children, status_children):
    ctx = callback_context
    if ctx.triggered_id == ID+"button-fire":
        if fire_children == ["Fire"]:
            if status_children[-1] == "Standby" or "Laser ON":
                hm.laser.laser_on()
                return False, "success", ["Fired"]
            else:
                return True, "warning", ["Fire"]
        elif fire_children == ["Fired"]:
            hm.laser.laser_off()
            return True, "info",  ["Fire"]
    else:
        iii = 1
        for i in range(iii):
            try:
                if hm.laser.is_laser_on():
                    return False, "success", ["Fired"]
                else:
                    return True, "info",  ["Fire"]
            except:
                iii+=1
                time.sleep(0.5)

@callback(
    Output(ID+"radioitems-constant-mode", "options"), 
    Output(ID+"radioitems-analog-modulation", "options"), 
    Output(ID+"radioitems-modulation-type", "options"), 
    Output(ID+"radioitems-digital-modulation", "options"), 
    Input(ID+"alert-status", "children"),
    State(ID+"radioitems-constant-mode", "options"), 
    State(ID+"radioitems-analog-modulation", "options"), 
    State(ID+"radioitems-modulation-type", "options"), 
    State(ID+"radioitems-digital-modulation", "options"), 
    prevent_initial_call=False
)
def _disable_input_items(status_children, inoptions1, inoptions2, inoptions3, inoptions4):
    disabled  = True
    inoptions1, inoptions2, inoptions3, inoptions4
    if status_children[-1] == "Laser ON":
        disabled  = True
    else:
        disabled  = False

    for ino in inoptions1:
        ino["disabled"] = disabled
    for ino in inoptions2:
        ino["disabled"] = disabled
    for ino in inoptions3:
        ino["disabled"] = disabled
    for ino in inoptions4:
        ino["disabled"] = disabled
    return inoptions1, inoptions2, inoptions3, inoptions4


@callback(
    Output(ID+'store-local-data', "data"),
    Input(ID+"input-power", "n_blur"), 
    Input(ID+"input-current", "n_blur"), 
    Input(ID+"radioitems-constant-mode", "value"), 
    Input(ID+"radioitems-analog-modulation", "value"), 
    Input(ID+"radioitems-modulation-type", "value"), 
    Input(ID+"radioitems-digital-modulation", "value"), 
    State(ID+"input-power", "value"), 
    State(ID+"input-current", "value"), 
    prevent_initial_call=False
)
def _update_input(
    _5, _6,
    arg1, arg2, arg3, arg4, arg5, arg6, 
    ):
    # hm.connect()
    ctx = callback_context
    if ctx.triggered_id == ID+"radioitems-constant-mode":
        # print(arg1)
        if arg1 != None:
            hm.laser.set_analog_control_mode(arg1)
            time.sleep(0.1)
            # print(hm.laser.get_analog_control_mode())
    elif ctx.triggered_id == ID+"radioitems-analog-modulation":
        # print(arg2)
        if arg2 != None:
            hm.laser.set_analog_modulation(arg2)
            time.sleep(0.1)
            # print(hm.laser.get_analog_modulation())
    elif ctx.triggered_id == ID+"radioitems-modulation-type":
        # print(arg3)
        if arg3 != None:
            hm.laser.set_modulation_state(arg3)
            time.sleep(0.1)
            # print(hm.laser.get_modulation_state())
    elif ctx.triggered_id == ID+"radioitems-digital-modulation":
        # print(arg4)
        if arg4 != None:
            hm.laser.set_digital_modulation(arg4)
            time.sleep(0.1)
            # print(hm.laser.get_digital_modulation())
    elif ctx.triggered_id == ID+"input-power":
        # print(arg5)
        if arg5 != None:
            hm.laser.set_laser_power(arg5)
            time.sleep(0.1)
            # print(hm.laser.get_laser_power())
    elif ctx.triggered_id == ID+"input-current":
        # print(arg6)
        if arg6 != None:
            hm.laser.set_diode_current(100.0*arg6/max_laser_current)
            time.sleep(0.1)
            # print(hm.laser.get_diode_current())
    return []


@callback(
    Output(ID+"input-command-response", "children"), 
    Input(ID+"input-command", "n_submit"),
    State(ID+"input-command", "value"),
    prevent_initial_call=True
)
def _update_input_command(_, command):
    response = str(hm.laser.send_query(command))
    return ["Response: ", response]

layout_status = dbc.Row([
    dbc.Alert(id=ID+"input-command-response", children=["Response: ", "...."], color="info"),
    dbc.Alert(id=ID+"alert-status", children=["Status", ""], color="info"),
    # dbc.Alert(id=ID+"alert-status", children=["Status", ""]),
]
)

# -------------------------------------------------------------------------

# layout and callback for monitoring device's states-----------------------
layout_hidden = dbc.Col([
    dcc.Store(id=ID+'store-local-data', storage_type="local", data=[]), 
    dcc.Interval(id=ID+'interval-uppdate', interval=500, n_intervals=0), #ms
]
)

layout_output = dbc.Col([
    html.H3("Output", className="p-2 text-center",), 
    dbc.Row([
        dbc.Col([
            ddaq.Gauge(   
                id=ID+"gauge-power",  
                min=0.0,
                max=max_laser_power,
                value=00.0,
                # label='Power',
                # units="mW",
                label="mW",
                color={"gradient":True,
                        "ranges":{
                            COLOR_BG:[0,0.6*max_laser_power],
                            COLOR_INDICATOR:[0.6*max_laser_power, max_laser_power]
                            }
                        },
                showCurrentValue=True,
                labelPosition="bottom", 
                className="bg-transparent",
                style={
                    'marginBottom': -50, #Or whatever number suits your needs
                    "circle.stroke-width": "40px"
                },
            ),
        ]),
        dbc.Col([
            ddaq.Gauge( 
                id=ID+"gauge-current",        
                min=0.0,
                max=max_laser_current,
                value=00.0,
                # label='Current',
                # units="mA",
                label="mA",
                color={"gradient":True,
                        "ranges":{
                            COLOR_BG:[0,0.6*max_laser_current],
                            COLOR_INDICATOR:[0.6*max_laser_current, max_laser_current]
                            }
                        },
                showCurrentValue=True,
                labelPosition="bottom", 
                className="bg-transparent",
                style={
                    'marginBottom': -50 #Or whatever number suits your needs
                }
            ),
        ]),
        ], 
        # width=10,
        align='center',
    ),
],)

layout_temperature = dbc.Col([
    html.H3("Temperature", className="p-2 text-center",), 
    dbc.Row([
        dbc.Col([
            ddaq.Thermometer(
                id=ID+"thermometer-baseplate",
                min=0,
                max=60,
                value=60,
                showCurrentValue=True,
                units="°C",
                label="Base",
                color=COLOR_INDICATOR,
                className="bg-transparent label:input-group-text",
                # scale={"custom":{
                #     0:{"label":"fuckyou", "style":".input-group-text"},
                #     30:{"label":"fuckyou"}
                #     }}
            ), 
        ]),
        dbc.Col([
            ddaq.Thermometer(
                id=ID+"thermometer-diode",
                min=0,
                max=60,
                value=60,
                showCurrentValue=True,
                units="°C", 
                label="Diode",
                color=COLOR_INDICATOR,
                className="bg-transparent", 
            )
        ]), 
    ], 
    id="laser-temperautre", 
    
    )
    ],
)

@callback(
    Output(ID+"gauge-power", "value"), 
    Output(ID+"gauge-current", "value"),
    Output(ID+"thermometer-baseplate", "value"), 
    Output(ID+"thermometer-diode", "value"), 
    Output(ID+"alert-status", "children"), 
    Input(ID+'interval-uppdate', "n_intervals"),
    prevent_initial_call=True,
    # manager=long_callback_manager,
)
def _update_device_states(_):
    power = hm.laser.get_laser_power()
    current = hm.laser.get_diode_current()
    temp_base = hm.laser.get_baseplate_temp()
    temp_diode = hm.laser.get_diode_temp()
    status = hm.laser.get_status()
    # power = random.choices(range(0, max_laser_power))[0]
    # current = random.choices(range(0, max_laser_current))[0]
    # temp_base = random.choices(range(0, 50))[0]
    # temp_diode = random.choices(range(0, 50))[0]
    # status = random.choices(["Warm Up", "Standby", "Laser ON", "Error", "Alarm", "Sleep", "Searching SLM point"])[0]
    return power,current, temp_base, temp_diode, ["Status: ", status]



# --------------------------------------------------------------------------
layout_laser_control = html.Div([
    dbc.Row([
        dbc.Col([
            layout_input, 
            layout_hidden,
            layout_status,
        ],
        # align="center", 
        width="5", className="mt-3 border"
        ), 
        dbc.Col([
            layout_output,
            layout_temperature
        ],
        align="center", 
        width="7", 
        className="mt-3 border"
        ),
    ],
    align="top")
])

if __name__ == "__main__":
    from dash_bootstrap_components import themes
    # APP_THEME = themes.JOURNAL
    APP_THEME = themes.SKETCHY
    # APP_THEME = themes.QUARTZ
    # APP_THEME = themes.DARKLY
    # APP_THEME = themes.VAPOR
    # APP_THEME = themes.SUPERHERO
    DEBUG = True
    GUI_PORT = 9843
    app = dash.Dash(
        __name__, 
        external_stylesheets=[
            APP_THEME, 
        ], 
        external_scripts=[])
    app.layout = layout_laser_control
    app.run_server(
        # host="0.0.0.0", 
        debug=DEBUG, 
        port=GUI_PORT)

