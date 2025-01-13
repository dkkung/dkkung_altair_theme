import altair as alt

"""
Defining custom themes using global and
rational configuration values. The theme
must be added to the register uniquely
for each function definition using the
@ decorator to pass the function to the
register.
"""


# alt.theme.options = {"test": "test"}
def options(
    dark_mode=False,
    dimX=300,
    dimY=300,
    font="Helvetica Neue",
    fontSize=15,
    fontStyle="UltraLight",
    grid=False,
    transparentBackground=False,
    backgroundColor="white",
):
    """
    Set global configuration options for the custom theme.
    Call this function when plotting to custom-set the
    options to override the defaults.
    """
    alt.theme.options = {}  # must reset options to remove stale keys
    alt.theme.options["grid"] = grid
    alt.theme.options["fontStyle"] = fontStyle
    alt.theme.options["dark_mode"] = dark_mode


@alt.theme.register("custom", enable=False)
def custom() -> alt.theme.ThemeConfig:
    opts = alt.theme.options
    return {
        "config": {
            "axis": {
                "grid": opts["grid"],
                "labelFontStyle": opts["fontStyle"],
                "labelFlush": True,
            },
            # "background": None if transparentBackground else backgroundColor,
            # "background": "red" if opts["dark_mode"] else backgroundColor,
            # "font": {"family": font},
            # "mark": {"color": "black", "fill": "black"},
            # "view": {
            #     "fill": backgroundColor,
            #     "continuousWidth": dimX,
            #     "continuousHeight": dimY,
            # },
            "group": {
                "strokeOpacity": 0,  # remove top and right axis borders
            },
        }
    }


"""
The functions should be consolidated into a
single function, with ternary operators
used to distinguish between configuration
values using a dark_mode global variable.
Maybe try using alt.theme.options?
"""
