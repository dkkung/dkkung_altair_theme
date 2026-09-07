---
title: "Utilities"
description: "Shared helpers: DataFrame handling, counts, and band geometry."
sidebar:
  order: 17
---

<!-- Generated from docstrings by website/scripts/gen_api.py - do not edit by hand. -->

Access these helpers through `ds.utils`.

## `band_geometry`

Call as `ds.utils.band_geometry(...)`.

```python
def band_geometry(
    n: int,
    span: float | None = None,
    *,
    scale: str = 'offset',
    bandPadding: float | None = None,
) -> BandGeometry: ...
```

Compute the pixel geometry of an ``n``-category band axis - the single source of
truth for dysonsphere's band-position math (violin centres, shade rects, bracket
midpoints, multilabel spans).

Vega-Lite lowers a nominal axis to a D3 band scale whose step size depends on the
padding configuration, which differs by mark type. ``scale`` picks the variant, each
resolving its inner padding from the matching theme key (outer is one shared key,
``outerPadding``, because Vega-Lite has no mark-specific outer padding):

- ``"offset"`` (default) - ``paddingInner=0``, ``paddingOuter=outerPadding``: what an
  ``xOffset`` encoding (``mark_circle``/``mark_strip``) or a ``shade`` rect sees.
- ``"band"`` - ``paddingInner=barPadding``: what ``mark_bar`` sees.
- ``"rect"`` - ``paddingInner=rectPadding`` (``0`` by default, so cells abut): what a
  ``mark_rect`` heatmap sees - and also ``mark_boxplot`` (and so ``mark_violin``'s
  embedded boxplot), since Vega-Lite routes "rect and other marks" through the one key.
- ``"point"`` - a point scale: ``step = span / n``; centre ``i`` is ``step*(0.5+i)``
  (``starts``/``ends`` equal ``centers``).

For every variant but ``"point"``, ``step = span / (n - inner + 2*outer)``, band ``i``
starts at ``step*(outer+i)`` and is ``step*(1-inner)`` wide.

**Parameters**

- **`n`** (`int`) - Number of categories.
- **`span`** (`float | None`) - Pixel extent of the axis. ``None`` (default) reads ``chartWidth`` from the active theme (pass ``chartHeight`` explicitly for a y-axis).
- **`scale`** (`str`) - ``"offset"``, ``"band"``, ``"rect"``, or ``"point"`` (see above).
- **`bandPadding`** (`float | None`) - Override for the outer padding, and for ``scale="band"`` the inner padding too (the variant where the two are equal by construction). ``None`` (default) reads the active theme.

**Returns**

- `BandGeometry` - A named tuple ``(step, centers, starts, ends)``, each position list in category-index order.

## `count_n`

Call as `ds.utils.count_n(...)`.

```python
def count_n(
    data: pl.DataFrame,
    column: str,
    categories: list[str],
) -> list[int]: ...
```

Count the number of rows in ``data`` belonging to each category.

**Parameters**

- **`data`** (`pl.DataFrame`) - A ``polars.DataFrame`` or ``pandas.DataFrame``.
- **`column`** (`str`) - Column name used for grouping (the x-axis column).
- **`categories`** (`list[str]`) - Ordered list of category labels; the returned counts follow this order. Categories with no matching rows return 0.

**Returns**

- `list[int]` - Per-category row counts in the same order as ``categories``.

**Examples**

```python
::

    counts = ds.utils.count_n(data, "group", ["Control", "Group A", "Group B"])
    # [12, 15, 11]
```

## `ensure_polars`

Call as `ds.utils.ensure_polars(...)`.

```python
def ensure_polars(data: pl.DataFrame) -> pl.DataFrame: ...
```

Convert a pandas DataFrame to Polars, or pass a Polars DataFrame through unchanged.

Accepts either a ``polars.DataFrame`` or a ``pandas.DataFrame`` without
requiring pandas as a hard dependency — the check is done via the module
name only.  If ``data`` is neither, a ``TypeError`` is raised.

**Parameters**

- **`data`** (`pl.DataFrame`) - A ``polars.DataFrame`` or ``pandas.DataFrame``.

**Returns**

- `polars.DataFrame` - The original DataFrame if already Polars, otherwise the result of ``polars.from_pandas(data)``.

**Examples**

```python
::

    import pandas as pd
    pdf = pd.DataFrame({"group": ["A", "B"], "value": [1.0, 2.0]})
    pldf = ds.utils.ensure_polars(pdf)  # returns a polars.DataFrame
```

## `resolve_palette`

Call as `ds.utils.resolve_palette(...)`.

```python
def resolve_palette(name_or_list: str | list[str]) -> list[str]: ...
```

A palette name → its hex list (via ``colors``), or a hex list passed straight through.

## `stripe_colors`

Call as `ds.utils.stripe_colors(...)`.

```python
def stripe_colors(
    palette: str | list[str],
    n: int,
    *,
    darkmode: bool,
) -> list[str]: ...
```

The ``n`` row-striping fills from *palette* - its lightest ``n`` stops, or its darkest in
darkmode, since a sequential palette runs light to dark.

Shared by ``mark_table``'s cell stripes and ``add_multilabel``'s row bands. NOT used by
``shade``, whose darkmode deliberately discards the caller's palette for greys.
