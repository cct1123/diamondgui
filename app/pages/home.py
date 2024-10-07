import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import dash_daq as ddaq

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

layout = html.Div(
    id = "home", 
    children = [
        dbc.ButtonGroup([
            # ddaq.PowerButton(id="button-shutdown", className="me-1", on=True, color="rgba(223, 221, 221, 0.4)"),
            ddaq.PowerButton(id="button-shutdown", className="me-1", on=True),
            dcc.Store(id="shutdown-dummy", data=[]),
            ],
        )
    ]
    
    
)