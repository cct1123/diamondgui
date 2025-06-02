import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, clientside_callback, html

from gui.config import *

# load_figure_template([PLOT_THEME])

# sidebar_css = "sidebar.css"
# nonono_css = "./gui/assets/noarrowdropdown.css"
app = dash.Dash(
    __name__,
    use_pages=True,
    pages_folder="pages",
    external_stylesheets=[
        APP_THEME,
    ],
    serve_locally=True,
    external_scripts=[
        # "https://cdnjs.cloudflare.com/ajax/libs/dragula/3.7.2/dragula.min.js"
    ],
)
# app.css.config.serve_locally = True
# app.scripts.config.serve_locally = True

# server = app.server
# print(APP_THEME)


# Add color mode switch
color_mode_switch = dbc.Col(
    [
        dbc.Label(className="fa fa-moon-o", html_for="switch"),
        dbc.Switch(
            id="dark-light-switch",
            value=True,
            className="d-inline-block ms-1",
            persistence=True,
            persistence_type="session",
        ),
        dbc.Label(className="fa fa-sun-o", html_for="switch"),
    ],
    style={"position": "absolute", "top": 0, "right": 0},
    # className="mt-2 ml-2 mr-2 mb-2",
)

# Build navigation links

# Separate main and nested pages
pages = dash.page_registry.values()
main_pages = [page for page in pages if len(page["path"].split("/")) <= 2]
nested_pages = [page for page in pages if len(page["path"].split("/")) > 2]
for np in nested_pages:
    print(np["name"])
nav_links = []
for main_page in main_pages:
    print(main_page["name"])
    # Find nested pages for this main page
    sub_pages = [
        page
        for page in nested_pages
        if page["path"].startswith(main_page["path"] + "/")
    ]

    if sub_pages:
        print(f"creating sub pages for {main_page['name']}")
        # Create a dropdown for nested pages
        dropdown = dbc.DropdownMenu(
            label=[
                html.I(className=f"fa {main_page['icon']} me-2"),
                html.A(
                    html.Span(main_page["name"]),
                    href=main_page["path"],
                    style={"color": "inherit", "text-decoration": "none"},
                ),
            ],
            nav=True,
            caret=False,
            direction="end",
            children=[
                dbc.DropdownMenuItem(main_page["name"], href=main_page["path"]),
                dbc.DropdownMenuItem(divider=True),
            ]
            + [
                dbc.DropdownMenuItem(page["name"], href=page["path"])
                for page in sub_pages
            ],
        )
        nav_links.append(dropdown)
    else:
        # Add main page link directly
        nav_links.append(
            dbc.NavLink(
                [
                    html.I(className=f"fa {main_page['icon']} me-2"),
                    html.Span(main_page["name"]),
                ],
                href=main_page["path"],
                active="exact",
            )
        )
# Combine all links
sidebar = dbc.Nav(
    nav_links,
    vertical=True,
    pills=True,
    class_name="sidebar bg-info",
)


# Custom CSS for hover-triggered dropdowns
app.layout = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    [sidebar],
                    width=1,
                    xs=2,
                    sm=1.5,
                    md=1.5,
                    lg=1,
                    xl=1,
                    xxl=1,
                    class_name="sidebar-wrapper ps",
                    # align="left"
                ),
                dbc.Col(
                    [
                        color_mode_switch,
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
                    xs=8,
                    sm=9,
                    md=9,
                    lg=10,
                    xl=10,
                    xxl=10,
                    class_name="main-panel ps",
                    # style={"resize": "horizontal", "overflow": "hidden"}
                ),
                dbc.Col(
                    [],
                    align="bottom",
                    width=0.5,
                    xs=1.5,
                    sm=1,
                    md=1,
                    lg=0.5,
                    xl=0.5,
                    xxl=0.5,
                ),
            ],
        )
    ],
    id="main-app",
)


clientside_callback(
    """ 
    (switchOn) => {
       document.documentElement.setAttribute('data-bs-theme', switchOn ? 'light' : 'dark');  
       return window.dash_clientside.no_update
    }
    """,
    Output("dark-light-switch", "id"),
    Input("dark-light-switch", "value"),
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
        port=GUI_PORT,
    )
