import dash
from dash import dcc, html, callback, Output, Input
import plotly.express as px
import dash_bootstrap_components as dbc

dash.register_page(
    __name__, 
    name='Spectrometry',
    icon="fa-flask",
    order=3,
    )

layout = html.Div()
