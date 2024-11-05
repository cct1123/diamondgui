"""
****** Important! *******
If you run this app locally, un-comment line 113 to add the ThemeChangerAIO component to the layout
"""
import dash 
from dash import Dash, dcc, html, dash_table, Input, Output, callback
import plotly.express as px
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url

dash.register_page(
    __name__, 
    name='Analysis',
    icon="fa-area-chart",
    order=4,
    )

# from app.pages.measurement_pages.confocal_page import layout_confocal
# layout = layout_confocal

layout = html.Div(
    id = "analysis", 
    children = [
        dbc.InputGroup()
    ]
)