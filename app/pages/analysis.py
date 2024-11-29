"""
****** Important! *******
If you run this app locally, un-comment line 113 to add the ThemeChangerAIO component to the layout
"""

import dash
import dash_bootstrap_components as dbc

dash.register_page(
    __name__,
    name="Analysis",
    icon="fa-area-chart",
    order=4,
)

# from app.pages.measurement_pages.confocal_page import layout_confocal
# layout = layout_confocal
from app.pages.analysis_pages.plotdata_page import layout_plotdata

layout = dbc.Col(id="analysis", children=[layout_plotdata], className="mt-2 mb-2")
