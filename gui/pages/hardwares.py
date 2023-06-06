# hardware control page

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import dash_daq as ddaq

from nspyre import InstrumentGateway

dash.register_page(
    __name__, 
    path="/hardwares",
    name="Hardwares",
    icon="fa-hdd-o",
    order=6,
    ) 








from gui.pages.hardware_pages.laser_control import layout_laser_control


layout = html.Div(
    id = "hardwares", 
    children = [
        layout_laser_control
    ]
)