# from gui.pages.measurement_pages.confocal_page import *
from gui.pages.measurement_pages.pltrace_page import *
# from gui.pages.hardware_pages.nidaq_ai import *


from dash_bootstrap_components import themes

DEBUG = True
GUI_PORT = 9843
app = dash.Dash(
__name__, 
external_stylesheets=[
        APP_THEME, 
], 
external_scripts=[])

# Serve files locally
app.css.config.serve_locally = True
app.scripts.config.serve_locally = True

app.layout = layout_pltrace
app.run_server(
# host="0.0.0.0", 
debug=DEBUG,
port=GUI_PORT)