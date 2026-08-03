---
title: "Multicharts"
description: "Compose several charts into one figure, each at its own size."
sidebar:
  order: 6
---

<!-- Generated from docstrings by website/scripts/gen_api.py - do not edit by hand. -->

## `multichart`

```python
def multichart(
    members: list[_Member],
    *,
    spacing: _Spacing = None,
) -> _AltairChart: ...
```

Compose several charts into one figure, each built at its own size.

Charts in one figure share a single ``config.view``, so :func:`theme` alone cannot give
them different sizes - the last call wins. Sizing with ``.properties()`` instead leaves
``markSize``, the corner and arc radii, and the pixel geometry of every annotation
(``add_shade`` spans, comparison brackets, ``add_labels`` placement) computed for the
theme's size rather than the one the chart renders at. ``multichart`` builds each member
while the theme genuinely says its size, so those all land correctly, then stamps the
size on the chart so the shared config cannot override it.

Size only: Vega-Lite's ``config`` is spec-level, so palettes, fonts and axis styling
cannot differ between charts in one figure. Set those on the encoding instead - e.g.
``alt.Color(..., scale=alt.Scale(range=ds.palette("ds_cat_2", 3)))`` - which is per-view
and survives. Scales are not shared: concat resolves them independently already.

**Parameters**

- **`members`** (`list[_Member]`) - The charts, in layout order. Each is a ``(builder, width, height)`` tuple, a bare zero-argument builder (built at the theme's current size), or an already-built chart (used as-is, so a ``multichart`` result can nest inside another). Nest lists to make rows: ``[[a, b], [c, d]]`` is two rows of two, a flat list is a single row.
- **`spacing`** (`_Spacing`) - Gap between charts in pixels - a number for both directions, or ``{"row": 40, "column": 10}`` to set them independently. ``None`` uses Vega-Lite's default.

**Returns**

- `An Altair concat chart, so ``.resolve_scale()``, ``.properties()`` and further nesting` - 
- `all work on the result.` - 

**Examples**

```python
A wide time course beside a narrow endpoint comparison::

    figure = ds.multichart(
        [(time_course, 210, 130), (endpoint_quant, 95, 130)],
        spacing=34,
    )

Two rows, with more room between the rows than within them::

    figure = ds.multichart(
        [
            [(time_course, 190, 110), (endpoint_quant, 90, 110)],
            [(heatmap, 130, 110), (activity_fit, 150, 110)],
        ],
        spacing={"row": 40, "column": 10},
    )
```
