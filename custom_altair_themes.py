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
    angledX=False,
    axisWidth=0.50,
    darkmode=False,
    dashedLine=False,
    dashedRule=True,
    font="Helvetica Neue",
    fontStyle="Regular",
    fontWeight=300,  # only multiples of 100
    grid=False,
    gridColor="darkGray",
    legend=True,
    legendStroke=False,
    markFillColor="black",
    markFillOpacity=0.9,
    markSize=10,
    markStrokeColor="black",
    markStrokeOpacity=1,
    markStrokeWidth=0.50,
    chartBackgroundColor="white",
    ticks=True,
    topAndRightBorder=False,
    transparentBackground=False,
    verticalY=False,
    viewBackgroundColor="white",
    xTicks=True,
    yTicks=True,
):
    """
    Set global configuration options for the custom theme.
    Call this function when plotting to custom-set the
    options to override the defaults.
    """
    alt.theme.options = {}  # must reset options to remove stale keys
    alt.theme.options["angledX"] = angledX
    alt.theme.options["axisWidth"] = axisWidth
    alt.theme.options["chartBackgroundColor"] = chartBackgroundColor
    alt.theme.options["darkmode"] = darkmode
    alt.theme.options["dashedLine"] = dashedLine
    alt.theme.options["dashedRule"] = dashedRule
    alt.theme.options["font"] = font
    alt.theme.options["grid"] = grid
    alt.theme.options["gridColor"] = gridColor
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
    alt.theme.options["ticks"] = ticks
    alt.theme.options["tickWidth"] = axisWidth
    alt.theme.options["topAndRightBorder"] = topAndRightBorder
    alt.theme.options["transparentBackground"] = transparentBackground
    alt.theme.options["verticalY"] = verticalY
    alt.theme.options["viewBackgroundColor"] = viewBackgroundColor
    alt.theme.options["xTicks"] = xTicks
    alt.theme.options["yTicks"] = yTicks
    # alt.theme.options["colors"] = {
    #     "nature": ["#4BA69F", "#C6A639", "#53A157", "#4A8A95", "#FCF6D1"],
    #     "categoricalSequential": ["#C4EFEC", "#4BA69F"]
    # }


@alt.theme.register("custom", enable=False)
def custom() -> alt.theme.ThemeConfig:
    colors = {
        "DKolors": ["#4BA69F", "#C6A639", "#75954A", "#4A8A95", "#FCF6D1"],
        "ordinal": ["#585D5E", "#4BA69F"],
        "diverging": ["#D6E2E9", "#4BA69F"]
    }
    opts = alt.theme.options
    return {
        "background": None
        if opts["transparentBackground"] or opts["darkmode"]
        else opts["chartBackgroundColor"],  # background of the entire view
        "config": {
            "area": {
                "fill": opts["markFillColor"],
                "fillOpacity": opts["markFillOpacity"],
                "stroke": "white" if opts["darkmode"] else opts["markStrokeColor"],
                "strokeOpacity": opts["markStrokeOpacity"],
                "strokeWidth": opts["markStrokeWidth"],
            },
            "axis": {
                "domain": True,
                "domainColor": "white" if opts["darkmode"] else "black",
                "domainWidth": opts["axisWidth"],
                "grid": opts["grid"],
                "gridColor": opts["gridColor"]
                if opts["darkmode"]
                else opts["gridColor"],
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
                "translate": 0,  # default is 0.5, which causes x and y axes to be misaligned / shifted. Required for top and right border alignment.
            },
            "axisX": {
                "labelAlign": "right"
                if opts["angledX"]
                else "center",  # keep label alignment distinct between X & Y
                "labelAngle": 315 if opts["angledX"] else 0,
                "ticks": True if opts["xTicks"] and opts["ticks"] else False,
            },
            "axisY": {
                "labelAlign": "center"
                if opts["verticalY"]
                else "right",  # keep label alignment distinct between X & Y
                "labelAngle": 270 if opts["verticalY"] else 0,
                "ticks": True if opts["yTicks"] and opts["ticks"] else False,
            },
            "bar": {
                "fill": opts["markFillColor"],
                "fillOpacity": opts["markFillOpacity"],
                "stroke": "white" if opts["darkmode"] else opts["markStrokeColor"],
                "strokeOpacity": opts["markStrokeOpacity"],
                "strokeWidth": opts["markStrokeWidth"],
            },
            "boxplot": {
                "box": {
                    # 'fill': opts['markFillColor'],
                    "fillOpacity": opts["markFillOpacity"],
                    "stroke": "white" if opts["darkmode"] else opts["markStrokeColor"],
                    "strokeOpacity": opts["markStrokeOpacity"],
                    "strokeWidth": opts["markStrokeWidth"],
                },
                "median": {
                    "fill": "black"
                    if opts["darkmode"]
                    else opts["viewBackgroundColor"],
                    "fillOpacity": opts["markFillOpacity"],
                    "size": opts["markSize"],
                    "stroke": "white" if opts["darkmode"] else opts["markStrokeColor"],
                    "strokeOpacity": opts["markStrokeOpacity"],
                    "strokeWidth": opts["markStrokeWidth"],
                },
                "rule": {  # may inherit undeclared fields from top-level rule config
                    "fill": "white" if opts["darkmode"] else "black",
                    "fillOpacity": opts["markFillOpacity"],
                    "size": opts["markSize"],
                    "stroke": "white" if opts["darkmode"] else opts["markStrokeColor"],
                    "strokeDash": [0, 0],
                    "strokeOpacity": opts["markStrokeOpacity"],
                    "strokeWidth": opts["markStrokeWidth"],
                },
                "outliers": {
                    "color": "white" if opts["darkmode"] else "black",
                    "fill": "white" if opts["darkmode"] else "black",
                    "fillOpacity": opts["markFillOpacity"],
                    "size": 0,
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
            "header": {
                "labelColor": "white" if opts["darkmode"] else "black",
                "labelFont": opts["font"],
                "labelFontStyle": opts["fontStyle"],
                "labelFontWeight": opts["fontWeight"],
                "titleColor": "white" if opts["darkmode"] else "black",
                "titleFont": opts["font"],
                "titleFontStyle": opts["fontStyle"],
                "titleFontWeight": opts["fontWeight"],
                "titlePadding": 0,
            },
            "legend": {
                "disable": not opts["legend"],
                "gradientOpacity": opts["markFillOpacity"],
                "gradientStrokeColor": "white" if opts["darkmode"] else "black",
                "gradientStrokeWidth": opts["markStrokeWidth"],
                "labelColor": "white" if opts["darkmode"] else "black",
                "labelFont": opts["font"],
                "labelFontStyle": opts["fontStyle"],
                "labelFontWeight": opts["fontWeight"],
                "strokeColor": "white" if opts["darkmode"] else "black",
                "strokeWidth": opts["axisWidth"] if opts["legendStroke"] else 0,
                "symbolStrokeColor": "white" if opts["darkmode"] else "black",
                "titleColor": "white" if opts["darkmode"] else "black",
                "titleFont": opts["font"],
                "titleFontStyle": opts["fontStyle"],
                "titleFontWeight": opts["fontWeight"],
            },
            "line": {
                "color": "white" if opts["darkmode"] else "black",
                "stroke": "white" if opts["darkmode"] else "black",
                "strokeDash": [4, 4] if opts["dashedLine"] else [0, 0],
                "strokeOpacity": 1,
                "strokeWidth": opts["axisWidth"],
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
                # pass in a list outside of a dict to AVOID interpolations; define as {scheme: _} to USE interpolation, which will NOT use the maximum range of colors
                "category": colors["DKolors"],
                "diverging": {
                    "scheme": colors["diverging"],
                },
                "heatmap": {
                    "scheme": "plasma" if opts["darkmode"] else "viridis",
                },
                "ordinal": {
                    "scheme": colors["ordinal"],
                },
                "ramp": {
                    "scheme": "plasma" if opts["darkmode"] else "viridis",
                },
            },
            "rule": {
                "color": "white" if opts["darkmode"] else "black",
                "stroke": "white" if opts["darkmode"] else "black",
                "strokeDash": [4, 4] if opts["dashedRule"] else [0, 0],
                "strokeOpacity": 1,
                "strokeWidth": opts["axisWidth"],
            },
            "rect": {
                "fill": opts["markFillColor"],
                "fillOpacity": opts["markFillOpacity"],
                "stroke": "white" if opts["darkmode"] else opts["markStrokeColor"],
                "strokeOpacity": opts["markStrokeOpacity"],
                "strokeWidth": opts["markStrokeWidth"],
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
                "fill": None
                if opts["transparentBackground"] or opts["darkmode"]
                else opts["viewBackgroundColor"],
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
- Try to add default paddingOutter and paddingInner values for all types of charts/marks.
- Add support for area marks.
    - Add support for gradients - linear and maybe radial.
- Figure out why opacity decreases (or does color change?) for area marks when line = True.
- Figure out why the Y axis and X axis have dissimilar domain widths on large plots.
- Maybe change legend scale size?
- Add custom color palettes for both light and dark modes.
"""
