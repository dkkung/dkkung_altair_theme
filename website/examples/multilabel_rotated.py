import numpy as np
import polars as pl

import dysonsphere as ds

ds.theme()

rng = np.random.default_rng(4)
doses = ["0", "0", "10", "6.67", "4.44", "2.96", "1.98"]
levels = [99.0, 39.0, 92.0, 80.0, 76.0, 54.0, 47.0]
conditions = [f"c{i}" for i in range(len(doses))]

df = pl.DataFrame(
    {
        "condition": [c for c in conditions for _ in range(4)],
        "viability": [float(np.clip(m + rng.normal(0, 2.5), 0, 100)) for m in levels for _ in range(4)],
    }
)

strip = ds.mark_strip(df, "condition", "viability", conditions, yTitle="% viable at 24 h")

# The dose values are far too wide for these bands, so stand them on end. The angle is given
# per cell, so the untreated controls keep their upright "-" placeholders.
chart = ds.add_multilabel(
    strip,
    {
        "Drug": [False, True, True, True, True, True, True],
        "Dose (µM)": ["-", "-", "10", "6.67", "4.44", "2.96", "1.98"],
    },
    categories=conditions,
    rowValueAngle={"Dose (µM)": [0, 0, -90, -90, -90, -90, -90]},
)
