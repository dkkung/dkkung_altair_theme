import altair as alt

"""
Global configuration values.
"""
dimX = 300
dimY = 300
font = "Helvetica Neue"
fontSize = dimX / 30
fontStyle = "UtlraLight"
transparentBackground = False
backgroundColor = "white"

"""
Defining custom themes using global and
rational configuration values. The theme
must be added to the register uniquely
for each function definition using the
@ decorator to pass the function to the
register.
"""


# alt.theme.options = {"test": "test"}
def options(dark_mode: bool, grid: bool):
    alt.theme.options = {} # must reset options to remove stale keys
    alt.theme.options["grid"] = grid
    alt.theme.options["dark_mode"] = dark_mode

# @alt.theme.register('custom_light', enable = False)
# def custom_light() -> alt.theme.ThemeConfig:
#     return {
#         "config": {
#             "view": {"continuousWidth": dimX, "continuousHeight": dimY},
#             "mark": {"color": "black", "fill": "black"},
#         }
#     }


@alt.theme.register("custom_dark", enable=False)
def custom_dark() -> alt.theme.ThemeConfig:
    alt.theme.enable("custom_dark")
    return {
        "config": {
            "axis": {
                "grid": False,
                "labelFontStyle": fontStyle,
                "labelFlush": True,
            },
            # "background": None if transparentBackground else backgroundColor,
            "background": "red" if alt.theme.options["dark_mode"] else backgroundColor,
            "font": {"family": font},
            "mark": {"color": "black", "fill": "black"},
            "view": {
                "fill": backgroundColor,
                "continuousWidth": dimX,
                "continuousHeight": dimY,
            },
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
