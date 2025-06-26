import dash
from dash import html

dash.register_page(
    __name__,
    path="/spectroscopy",
    name="Spectroscopy",
    icon="fa-flask",
    order=4,
)

layout = html.Div()
