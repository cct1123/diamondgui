if __name__ == "__main__":
    import os
    import sys

    path_project = "\\".join(os.getcwd().split("\\")[:-1])
    print(path_project)
    # caution: path[0] is reserved for script path (or '' in REPL)
    sys.path.insert(1, path_project)

    import dash
    import dash_bootstrap_components as dbc

    from gui.pages.home_pages.task_manager import layout_taskmanager

    app = dash.Dash(
        __name__,
        external_scripts=[
            "https://cdnjs.cloudflare.com/ajax/libs/dragula/3.7.2/dragula.min.js",
        ],
        external_stylesheets=[dbc.themes.BOOTSTRAP],
    )
    app.layout = dbc.Col(
        id="main",
        children=[layout_taskmanager],
    )
    GUI_PORT = 9981
    app.run_server(port=GUI_PORT, debug=True, threaded=True)
