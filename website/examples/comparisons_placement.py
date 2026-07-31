import dysonsphere as ds
from vega_datasets import data

ds.theme()

cars = ds.ensure_polars(data.cars()).drop_nulls(["Horsepower"])
origins = ["Europe", "Japan", "USA"]

# Left alone each bracket hugs the data it spans, so they sit at uneven heights when the
# groups do. yStart + yStep overrides that with an even ladder in data units.
chart = ds.mark_strip(
    cars, "Origin", "Horsepower", origins,
) + ds.add_comparisons(
    cars, "Origin", "Horsepower",
    pairs="all",
    categories=origins, labelStyle="asterisks",
    yStart=250.0, yStep=28.0,
)
