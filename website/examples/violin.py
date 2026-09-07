from vega_datasets import data

import dysonsphere as ds

ds.theme()

cars = ds.utils.ensure_polars(data.cars()).drop_nulls(["Horsepower"])
origins = ["USA", "Europe", "Japan"]

chart = ds.mark_violin(cars, "Origin", "Horsepower", origins, yTitle="Horsepower")
