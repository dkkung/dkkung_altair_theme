import altair as alt

'''
Global configuration values.
'''
font = "Helvetica Neue"
dimX = 300
dimY = 300
fontSize = dimX / 30

'''
Defining custom themes using global and
rational configuration values. The theme
must be added to the register uniquely
for each function definition using the
@ decorator to pass the function to the
register.
'''
@alt.theme.register('custom_light', enable = False)
def custom_light() -> alt.theme.ThemeConfig:
    return {
        "config": {
            "view": {"continuousWidth": dimX, "continuousHeight": dimY},
            "mark": {"color": "black", "fill": "black"},
        }
    }
    
@alt.theme.register('custom_dark', enable = False)
def custom_dark() -> alt.theme.ThemeConfig:
    return {
        "config": {
            "view": {"continuousWidth": dimX, "continuousHeight": dimY},
            "mark": {"color": "black", "fill": "black"},
        }
    }