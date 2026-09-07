from vega_datasets import data

import dysonsphere as ds

# categorical(members=n) returns the CVD-robust qualitative palette sized to
# your group count (blue / pink / yellow / green).
ds.theme()

cars = ds.utils.ensure_polars(data.cars()).drop_nulls(["Miles_per_Gallon"])
origins = ["USA", "Europe", "Japan"]

chart = ds.mark_strip(
    cars,
    "Origin",
    "Miles_per_Gallon",
    origins,
    palette=ds.palettes.categorical(3),
    yTitle="Miles per gallon",
)
