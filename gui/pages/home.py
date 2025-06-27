import logging
import os

import dash
from dash import html

# from gui.pages.home_pages.task_manager import layout_taskmanager

logger = logging.getLogger(__name__)

MAINDIR = os.getcwd()

dash.register_page(
    __name__,
    path="/",
    name="Home",
    icon="fa-home",
    order=1,
    # # meta tag
    # title="Diamond Dashboard",
    # image="icons8-sparkling-diamond-64.ico",
    # description="The home page for diamond dashboard."
)


from gui.pages.home_pages.camera_page import layout_camera
from gui.pages.home_pages.logdisplay_page import layout_logdisplay
from gui.pages.home_pages.windfreak_status import layout_windfreak_status

layout = html.Div(
    id="home",
    children=[
        # Navigation Section
        layout_camera,
        layout_logdisplay,
        layout_windfreak_status,
    ],
)
