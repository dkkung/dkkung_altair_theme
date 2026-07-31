import dysonsphere as ds
from vega_datasets import data

ds.theme()

cars = ds.ensure_polars(data.cars()).drop_nulls(["Miles_per_Gallon"])
origins = ["Europe", "Japan", "USA"]
pairs = [("Europe", "Japan"), ("Europe", "USA")]

# reverse= hangs those brackets BELOW their groups with the ticks pointing up, and they
# stack downward. Useful when the space above the data is already spoken for.
chart = ds.mark_strip(
    cars, "Origin", "Miles_per_Gallon", origins, yTitle="Miles per gallon",
) + ds.add_comparisons(
    cars, "Origin", "Miles_per_Gallon", pairs,
    reverse=pairs, labelStyle="asterisks", categories=origins,
)
