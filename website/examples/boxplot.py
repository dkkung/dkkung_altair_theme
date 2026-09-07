import altair as alt
from vega_datasets import data

import dysonsphere as ds

# Plain Altair marks inherit the theme too: grey boxes, single-stroke median,
# rounded whisker caps. boxplotOutliers=False hides outlier points.
ds.theme()

cars = ds.utils.ensure_polars(data.cars()).drop_nulls(["Miles_per_Gallon"])

chart = (
    alt.Chart(cars)
    .mark_boxplot()
    .encode(
        x=alt.X("Origin:N", title=None),
        y=alt.Y("Miles_per_Gallon:Q", title="Miles per gallon"),
    )
)
