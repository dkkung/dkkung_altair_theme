import altair as alt
from vega_datasets import data

import dysonsphere as ds

ds.theme()

cars = ds.utils.ensure_polars(data.cars()).drop_nulls(["Miles_per_Gallon"])

# ds.transforms.jitter() adds a Gaussian x-offset column; pass it to Altair's xOffset.
cars = ds.transforms.jitter(cars)

chart = (
    alt.Chart(cars)
    .mark_circle()
    .encode(
        x=alt.X("Origin:N", title=None),
        y=alt.Y("Miles_per_Gallon:Q", title="Miles per gallon"),
        xOffset=alt.XOffset("jitter_x:Q"),
    )
)
