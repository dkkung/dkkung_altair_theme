from vega_datasets import data

import dysonsphere as ds

ds.theme()

cars = ds.utils.ensure_polars(data.cars()).drop_nulls(["Miles_per_Gallon"])
origins = ["USA", "Europe", "Japan"]

strip = ds.mark_strip(cars, "Origin", "Miles_per_Gallon", origins, yTitle="Miles per gallon")

# Add per-category sample sizes and the category labels as annotation rows.
chart = ds.add_multilabel(
    strip,
    categories=origins,
    showSampleSize=True,
    df=cars,
    xCol="Origin",
    categoryLabel=True,
)
