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
    axisWidth=0.5,
    backgroundColor="white",
    darkmode=False,
    font="Helvetica Neue",
    fontStyle="Regular",
    fontWeight=200,  # only multiples of 100
    grid=False,
    legend=True,
    legendStroke=False,
    markFillColor="black",
    markFillOpacity=0.9,
    markSize=10,
    markStrokeColor="black",
    markStrokeOpacity=1,
    markStrokeWidth=0.50,
    ticks=True,
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
    alt.theme.options["backgroundColor"] = (backgroundColor,)
    alt.theme.options["darkmode"] = darkmode
    alt.theme.options["font"] = font
    alt.theme.options["grid"] = grid
    alt.theme.options["legend"] = legend
    alt.theme.options["legendStroke"] = legendStroke
    alt.theme.options["fontStyle"] = fontStyle
    alt.theme.options["fontWeight"] = fontWeight
    alt.theme.options["markFillColor"] = markFillColor
    alt.theme.options["markFillOpacity"] = markFillOpacity
    alt.theme.options["markSize"] = markSize
    alt.theme.options["markStrokeColor"] = markStrokeColor
    alt.theme.options["markStrokeOpacity"] = markStrokeOpacity
    alt.theme.options["markStrokeWidth"] = markStrokeWidth
    # alt.theme.options['plotScale'] = plotScale
    alt.theme.options["ticks"] = ticks
    alt.theme.options["tickWidth"] = axisWidth
    alt.theme.options["topAndRightBorder"] = topAndRightBorder
    alt.theme.options["transparentBackground"] = (transparentBackground,)


@alt.theme.register("custom", enable=False)
def custom() -> alt.theme.ThemeConfig:
    opts = alt.theme.options
    return {
        "background": None
        if opts["darkmode"]
        else "white",  # background of the entire view
        "config": {
            "axis": {
                "domain": True,
                "domainColor": "white" if opts["darkmode"] else "black",
                "domainWidth": opts["axisWidth"],
                "grid": opts["grid"],
                "gridColor": "lightGray" if opts["darkmode"] else "lightGray",
                "gridOpacity": 0.5,
                "gridWidth": opts["axisWidth"],
                "labelAlign": "center",
                "labelAngle": 0,
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
            "background": None
            if opts["transparentBackground"]
            else opts["backgroundColor"],
            "boxplot": {
                "box": {
                    # 'fill': opts['markFillColor'],
                    "fillOpacity": opts["markFillOpacity"],
                    "stroke": "white" if opts["darkmode"] else opts["markStrokeColor"],
                    "strokeOpacity": opts["markStrokeOpacity"],
                    "strokeWidth": opts["markStrokeWidth"],
                },
                "median": {
                    "fill": "black" if opts["darkmode"] else opts["backgroundColor"],
                    "fillOpacity": opts["markFillOpacity"],
                    "size": opts["markSize"],
                    "stroke": "white" if opts["darkmode"] else opts["markStrokeColor"],
                    "strokeOpacity": opts["markStrokeOpacity"],
                    "strokeWidth": opts["markStrokeWidth"],
                },
                "rule": {
                    "fill": "white" if opts["darkmode"] else "black",
                    "fillOpacity": opts["markFillOpacity"],
                    "size": opts["markSize"],
                    "stroke": "white" if opts["darkmode"] else opts["markStrokeColor"],
                    "strokeOpacity": opts["markStrokeOpacity"],
                    "strokeWidth": opts["markStrokeWidth"],
                },
                "outliers": {
                    "color": "white" if opts["darkmode"] else "black",
                    "fill": "white" if opts["darkmode"] else "black",
                    "fillOpacity": opts["markFillOpacity"],
                    "size": opts["markSize"],
                    "stroke": "white" if opts["darkmode"] else opts["markStrokeColor"],
                    "strokeOpacity": opts["markStrokeOpacity"],
                    "strokeWidth": opts["markStrokeWidth"],
                },
            },
            "circle": {
                "fill": opts["markFillColor"],
                "fillOpacity": opts["markFillOpacity"],
                "size": opts["markSize"],
                "stroke": opts["markStrokeColor"],
                "strokeOpacity": opts["markStrokeOpacity"],
                "strokeWidth": opts["markStrokeWidth"],
            },
            "font": opts["font"],
            "legend": {
                "disable": not opts["legend"],
                "labelColor": "white" if opts["darkmode"] else "black",
                "labelFont": opts["font"],
                "labelFontStyle": opts["fontStyle"],
                "labelFontWeight": opts["fontWeight"],
                "gradientStrokeColor": "white" if opts["darkmode"] else "black",
                "gradientStrokeWidth": opts["axisWidth"],
                "strokeColor": "white" if opts["darkmode"] else "black",
                "strokeWidth": opts["axisWidth"] if opts["legendStroke"] else 0,
                "symbolStrokeColor": "white" if opts["darkmode"] else "black",
                "padding": 8,
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
                    "scheme": "greys",
                },
                "diverging": {
                    "scheme": "pinkyellowgreen",
                },
                "heatmap": {
                    "scheme": "plasma" if opts["darkmode"] else "viridis",
                },
                "ordinal": {
                    "scheme": "greys",
                },
                "ramp": {
                    "scheme": "plasma" if opts["darkmode"] else "viridis",
                },
            },
            "rule": {
                "color": "white" if opts["darkmode"] else "black",
                "stroke": "white" if opts["darkmode"] else "black",
                "strokeDash": [4, 4],
                "strokeOpacity": 1,
                "strokeWidth": opts["axisWidth"],
            },
            "rect": {
                'fill': opts['markFillColor'],
                'fillOpacity': opts['markFillOpacity'],
                'size': opts['markSize'],
                'stroke': opts['markStrokeColor'],
                'strokeOpacity': opts['markStrokeOpacity'],
                'strokeWidth': opts['markStrokeWidth'],
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
                # 'fill': None,
                # 'fill': backgroundColor,
                # 'continuousWidth': 300,
                # 'continuousHeight': 300,
                # 'discreteWidth': 20,
                "stroke": "white" if opts["darkmode"] else "black",
                "strokeOpacity": 1
                if opts["topAndRightBorder"]
                else 0,  # remove top and right axis borders
                "strokeWidth": opts["axisWidth"],
            },
        },
    }


"""
TO-DO LIST:
- Change font, fontSize, fontWeight, and fontStyle for faceted labels and title. HEADER CONFIG IS BROKEN.
    - Add a padding to X-axis labels - maybe around 10 px. The padding will push the title away as well (which is good, I think).
- Add a stroke to legend icons.
- Add dark mode support for boxplots, but DO NOT change the stroke color of individual POINTS (at least with greys) to white (changing rect strokes to white is good).
- Make 'greys' the default ordinal and sequential color scheme; it's usable for both light- and dark-mode.
"""
