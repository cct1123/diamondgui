"""
****** Important! *******
If you run this app locally, un-comment line 113 to add the ThemeChangerAIO component to the layout
"""

import dash
from dash import html

dash.register_page(
    __name__,
    name="Analysis",
    icon="fa-area-chart",
    order=4,
)

# from app.pages.measurement_pages.confocal_page import layout_confocal
# layout = layout_confocal
from app.pages.analysis_pages.plotdata_page import layout_plotdata

layout = html.Div(id="analysis", children=[layout_plotdata])
