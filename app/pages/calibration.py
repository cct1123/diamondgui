import dash
from dash import dcc, html
import dash_bootstrap_components as dbc

dash.register_page(
    __name__, 
    name="Calibration",
    icon="fa-cogs",
    order=5,
    ) 

layout = html.Div(
    id = "fdsfdsf", 
    children = [
        dbc.InputGroup()
    ]
    
    
)



from app.pages.calibration_pages.pltrace_page import layout_pltrace


layout = html.Div(
    id = "calibration", 
    children = [
        layout_pltrace
    ]
)