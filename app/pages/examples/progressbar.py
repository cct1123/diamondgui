import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import time
from dash_bootstrap_components import themes
APP_THEME = themes.JOURNAL
# APP_THEME = themes.SKETCHY
# APP_THEME = themes.QUARTZ
# APP_THEME = themes.DARKLY
# APP_THEME = themes.VAPOR
# APP_THEME = themes.SUPERHERO

app = dash.Dash(
    __name__, 
    external_stylesheets=[
        APP_THEME, 
    ], 
    external_scripts=[])

app.layout = html.Div([
    html.H1('Progress Bar Example'),
    dcc.Interval(id='interval', interval=1000),  # update every 1 second
    dbc.Progress(id='progress', value=0, max=100, animated=True, striped=False, label="", className="mt-2 mb-2"),
    html.Div(id='progress-text')
])

@app.callback(
    Output('progress', 'value'),
    [Input('interval', 'n_intervals')]
)
def update_progress(n):
    if n is None:
        return 0
    progress = n % 100  # simulate progress from 0 to 100
    return progress

@app.callback(
    Output('progress-text', 'children'),
    [Input('progress', 'value')]
)
def update_progress_text(value):
    return f'Progress: {value}%'

if __name__ == '__main__':
    DEBUG = True
    GUI_PORT = 9833
    app.run_server(
        # host="0.0.0.0", 
        debug=DEBUG, 
        port=GUI_PORT)