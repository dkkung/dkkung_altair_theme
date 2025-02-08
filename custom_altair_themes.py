import altair as alt

"""
Defining custom themes using global and
rational configuration values. The theme
must be added to the register uniquely
for each function definition using the
@ decorator to pass the function to the
register.
"""


def options(
    axisWidth = 0.5,
    backgroundColor="white",
    darkmode=False,
    font="Helvetica Neue",
    fontStyle="Regular",
    fontWeight=200, # only multiples of 100
    grid=False,
    markFillColor="black",
    markFillOpacity=0.9,
    markStrokeColor="black",
    markStrokeOpacity=1,
    markStrokeWidth=0.25,
    markSize=40,
    ticks = True,
    topAndRightBorder=False,
    transparentBackground=False,
):
    """
    Set global configuration options for the custom theme.
    Call this function when plotting to custom-set the
    options to override the defaults.
    """
    alt.theme.options = {}  # must reset options to remove stale keys
    alt.theme.options["axisWidth"] = axisWidth
    alt.theme.options["backgroundColor"]=backgroundColor,
    alt.theme.options["darkmode"] = darkmode
    alt.theme.options["grid"] = grid
    alt.theme.options["font"] = font
    alt.theme.options["fontStyle"] = fontStyle
    alt.theme.options["fontWeight"] = fontWeight
    alt.theme.options["markFillColor"] = markFillColor
    alt.theme.options["markFillOpacity"] = markFillOpacity
    alt.theme.options["markStrokeColor"] = markStrokeColor
    alt.theme.options["markStrokeOpacity"] = markStrokeOpacity
    alt.theme.options["markStrokeWidth"] = markStrokeWidth
    alt.theme.options["markSize"] = markSize
    alt.theme.options["ticks"] = ticks
    alt.theme.options["tickWidth"] = axisWidth
    alt.theme.options["topAndRightBorder"] = topAndRightBorder
    alt.theme.options["transparentBackground"]=transparentBackground,


@alt.theme.register("custom", enable=False)
def custom() -> alt.theme.ThemeConfig:
    opts = alt.theme.options
    return {
        "background": None if opts["darkmode"] else "white", # background of the entire view
        "config": {
            "axis": {
                "domain": True,
                "domainColor": "white" if opts["darkmode"] else "black",
                "domainWidth": opts["axisWidth"],
                "grid": opts["grid"],
                "gridColor": "lightGray" if opts["darkmode"] else "lightGray",
                "gridOpacity": 0.5,
                "gridWidth": opts["axisWidth"],
                "labelColor": "white" if opts["darkmode"] else "black",
                "labelFont": opts["font"],
                "labelFontStyle": opts["fontStyle"],
                "labelFontWeight": opts["fontWeight"],
                "ticks": opts["ticks"],
                "tickColor": "white" if opts["darkmode"] else "black",
                "tickWidth": opts["axisWidth"],
                "titleColor": "white" if opts["darkmode"] else "black",
                "titleFont": opts["font"],
                "titleFontStyle": opts["fontStyle"],
                "titleFontWeight": opts["fontWeight"],
            },
            "background": None if opts["transparentBackground"] else opts["backgroundColor"],
            "boxplot": {
                "box": {
                    "fill": opts["markFillColor"],
                    "fillOpacity": opts["markFillOpacity"],
                    "size": opts["markSize"],
                    "stroke": opts["markStrokeColor"],
                    "strokeOpacity": opts["markStrokeOpacity"],
                    "strokeWidth": opts["markStrokeWidth"],
                },
                "median": {
                    "fill": "white" if opts["darkmode"] else "black",
                    "fillOpacity": 0,
                    "size": opts["markSize"],
                    "stroke": opts["markStrokeColor"],
                    "strokeOpacity": opts["markStrokeOpacity"],
                    "strokeWidth": opts["markStrokeWidth"],
                },
                "rule": {
                    "fill": opts["markFillColor"],
                    "fillOpacity": opts["markFillOpacity"],
                    "size": opts["markSize"],
                    "stroke": opts["markStrokeColor"],
                    "strokeOpacity": opts["markStrokeOpacity"],
                    "strokeWidth": opts["markStrokeWidth"],
                },
                "outliers": {
                    "size": 50,
                    "color": "red"
                }
            },
            "font": opts["font"],
            "legend": {
                "labelColor": "white" if opts["darkmode"] else "black",
                "labelFont": opts["font"],
                "labelFontStyle": opts["fontStyle"],
                "labelFontWeight": opts["fontWeight"],
                "gradientStrokeColor": "white" if opts["darkmode"] else "black",
                "gradientStrokeWidth": opts["axisWidth"],
                "titleColor": "white" if opts["darkmode"] else "black",
                "titleFont": opts["font"],
                "titleFontStyle": opts["fontStyle"],
                "titleFontWeight": opts["fontWeight"],
            },
            "point": {
                "fill": opts["markFillColor"],
                "fillOpacity": opts["markFillOpacity"],
                "size": opts["markSize"],
                "stroke": opts["markStrokeColor"],
                "strokeOpacity": opts["markStrokeOpacity"],
                "strokeWidth": opts["markStrokeWidth"],
            },
            "range": {
                "category": {
                    "scheme": "pastel1",
                },
                "diverging": {
                    "scheme": "pinkyellowgreen",
                },
                "heatmap": {
                    "scheme": "pinkyellowgreen",
                },
                "ordinal": {
                    "scheme": "pastel1",
                },
                "ramp": {
                    "scheme": "plasma" if opts["darkmode"] else "viridis",
                },
            },
            "rect": {
                # "fill": opts["markFillColor"],
                # "fillOpacity": opts["markFillOpacity"],
                # "size": opts["markSize"],
                # "stroke": opts["markStrokeColor"],
                # "strokeOpacity": opts["markStrokeOpacity"],
                # "strokeWidth": opts["markStrokeWidth"],
            },
            "square": {
                "fill": opts["markFillColor"],
                "fillOpacity": opts["markFillOpacity"],
                "size": opts["markSize"],
                "stroke": opts["markStrokeColor"],
                "strokeOpacity": opts["markStrokeOpacity"],
                "strokeWidth": opts["markStrokeWidth"],
            },
            "title": {
                "color": "white" if opts["darkmode"] else "black",
                "font": opts["font"],
                "fontStyle": opts["fontStyle"],
                "fontWeight": opts["fontWeight"],
                "subtitleColor": "white" if opts["darkmode"] else "black",
                "subtitleFont": opts["font"], 
                "subtitleFontStyle": opts["fontStyle"],
                "subtitleFontWeight": opts["fontWeight"],
            },
            "view": {
                # "fill": None,
                # "fill": backgroundColor,
                # "continuousWidth": 300,
                # "continuousHeight": 300,
                "stroke": "white" if opts["darkmode"] else "black",
                "strokeOpacity": 1 if opts["topAndRightBorder"] else 0,  # remove top and right axis borders
                "strokeWidth": opts["axisWidth"],
            },
        }
    }