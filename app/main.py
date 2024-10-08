import dash
from dash import html, dcc, Output, Input, State

import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
from app.config_custom import *

load_figure_template([PLOT_THEME])

# sidebar_css = "sidebar.css"
# nonono_css = "./gui/assets/noarrowdropdown.css"
app = dash.Dash(
    __name__, 
    use_pages=True, 
    pages_folder="pages",
    external_stylesheets=[
        
        # CSS_CYPERPUNK,
        # CSS_AUGMENTED,
        # CSS_BLACKDASH,
        # CSS_NUCLEO,
        CSS_ICON, 
        # # dbc_css, 
        CSS_SIDEBAR, 
        APP_THEME, 
        # nonono_css
        # dbc.icons.FONT_AWESOME
    ], 
    serve_locally=True,
    external_scripts=[])
# app.css.config.serve_locally = True
# app.scripts.config.serve_locally = True

# server = app.server



pages =  dash.page_registry.values()
main_pages = [page for page in pages if len(page["path"].split("/"))<=2]
# nested1_pages = [page for page in pages if 2<len(page["path"].split("/"))<=3]

sidebar = dbc.Nav(
    # [
    #     html.Img(src=LOGO_SRC, 
    #     height="30px", 
    #     )
    # ]
    # +
    [
        dbc.NavLink(
            [
                # html.Div(page["name"], className="ms-2")
                html.I(className=f"fa {page['icon']} me-2"), html.Span(page["name"]),
            ],
            href=page["path"], 
            active="exact",
        )
        for page in main_pages
    ], 
    vertical=True, 
    pills=True, 
    # dark=True,
    # className="sidebar bg-light"
    className="sidebar bg-info", 
    class_name="sidebar bg-info", 
)

app.layout = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        sidebar
                    ], 
                    width=1,
                    xs=2, sm=1.5, md=1.5, lg=1, xl=1, xxl=1,
                    # align="left"
                ),
                dbc.Col([
                    # dbc.Row(html.H1("Diamond Dashboard",  className="p-2 mb-1 text-center",)),
                    dbc.Row(
                        [
                            # dbc.Col(
                            #     [
                                    dash.page_container
                            #     ],
                            #     # # width=10,
                            #     # xs=8, sm=8, md=10, lg=10, xl=10, xxl=11,
                            #     className="content",
                            #     # align="center",
                            # ),
                        ]
                    ),
                ],
                # align="center",
                width=11,
                xs=8, sm=9, md=9, lg=10, xl=10, xxl=10, 
                # style={"resize": "horizontal", "overflow": "hidden"}
                ),
                dbc.Col([
                ],
                align="bottom",
                width=0.5,
                xs=1.5, sm=1, md=1, lg=0.5, xl=0.5, xxl=0.5,
                ),
            ], 
        )
    ],
    id="main-app"
)

# @app.callback(
#     Output("collapse", "is_open"),
#     [Input("collapse-button", "n_clicks")],
#     [State("collapse", "is_open")],
# )
# def toggle_collapse(n, is_open):
#     if n:
#         return not is_open
#     return is_open

if __name__ == "__main__":
    GUI_PORT = 9981
    DEBUG = True
    app.run(
        # host="0.0.0.0", 
        debug=DEBUG, 
        port=GUI_PORT)