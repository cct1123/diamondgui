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

# page 2 data
df = px.data.tips()

layout = html.Div(
    [   dbc.Col( [
        dbc.Row([
            dbc.Col(
                [
                    html.Img(src='assets/smoking2.jpg')
                ], width=4
            ),
            dbc.Col(
                [
                    dcc.RadioItems(df.day.unique(), id='day-choice', value='Sat')
                ], width=6
            )
        ]),
        dbc.Row([
                    dcc.Graph(id='bar-fig',
                              figure=px.bar(df, x='smoker', y='total_bill',))

        ])
        ])
    ]
)


@callback(
    Output('bar-fig', 'figure'),
    Input('day-choice', 'value')
)
def update_graph(value):
    dff = df[df.day==value]
    fig = px.bar(dff, x='smoker', y='total_bill')
    return fig