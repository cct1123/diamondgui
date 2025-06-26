# hardware control page

import dash
from dash import html

dash.register_page(
    __name__,
    path="/hardwares",
    name="Hardwares",
    icon="fa-hdd-o",
    order=7,
)

from gui.pages.hardware_pages.laser_control import layout_laser_control
from gui.pages.hardware_pages.windfreak_control import layout_windfreak

layout = html.Div(id="hardwares", children=[layout_laser_control, layout_windfreak])
