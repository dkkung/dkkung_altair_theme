---
title: "Reading exports"
description: "Read embedded metadata, statistics, reports, and data back out of exports."
sidebar:
  order: 9
---

<!-- Generated from docstrings by website/scripts/gen_api.py - do not edit by hand. -->

## `read`

```python
def read(
    path: str,
    *,
    what: str = 'report',
    save: bool | str = False,
    output: str = 'polars',
    dataset: str | None = None,
) -> Any: ...
```

Read back the metadata (or data) embedded by :func:`save` from a PNG, SVG, or JSON.

**Parameters**

- **`path`** (`str`) - A dysonsphere-exported ``.png``, ``.svg``, or ``.json`` file.
- **`what`** (`str`) - Which artifact to return: - ``'report'`` (default) — the human-readable report **table** as a ``str``; it is printed to stdout and returned. Joins every section of the ``report`` container (``statistics`` + ``provenance``). Falls back to re-rendering the statistics from the embedded records if the prose wasn't saved (``embedReport=False``). - ``'statistics'`` — the structured **records** (list of dicts, exact floats). - ``'metadata'`` — the whole ``{provenance, statistics, theme, report}`` dict, where ``report`` is the ``{section: text}`` container. - ``'data'`` — the **original data** Altair inlined into the spec (the whole frame, including columns the chart never plotted). **JSON only** (PNG/SVG don't carry the data). The form is chosen by ``output``.
- **`save`** (`bool | str`) - Only for ``what='report'``: ``True`` writes the report to a ``.txt`` in the cwd; a string writes to that directory.
- **`output`** (`str`) - Only for ``what='data'`` — the form to return the data in: ``'polars'`` (default) → ``pl.DataFrame``; ``'pandas'`` → ``pd.DataFrame``; ``'duckdb'`` → a ``DuckDBPyRelation``; ``'records'`` → the raw ``list[dict]`` (no dataframe library needed). ``pandas`` and ``duckdb`` are imported lazily and are not package dependencies.

## `verify`

```python
def verify(path: str, df: Any = None) -> VerifyResult: ...
```

Check a saved figure against its own embedded checksums, and optionally against its data.

Two independent questions, neither of which needs the original script:

- **Is the file internally consistent?**  The spec is re-hashed and compared with the
  recorded ``vegaliteChecksum``, so an edited spec is detectable.  JSON only - SVG and PNG
  embed the metadata block but not the full spec, so ``specValid`` is ``None`` for them.
- **Did this figure come from this data?**  Pass ``df`` and each frame's checksum is
  compared with the recorded ``dataChecksum``.  This works for **all three formats**, since
  the checksums travel in the metadata block, and it is order-independent in both senses:
  row order within a frame does not matter, nor does the order frames are passed in.

Because the checksums are content-derived, a figure that has lost its metadata entirely
(screenshotted, re-saved by another tool) can still be identified: verify an intact sibling
export, or compare ``frame_checksum(df)`` against a recorded value directly.

**Parameters**

- **`path`** (`str`) - A dysonsphere-exported ``.png``, ``.svg``, or ``.json``.
- **`df`** (`Any`) - Optional dataframe, or list of dataframes, that the figure should have been built from. Polars or pandas. Omit to check only the spec.

**Returns**

- `VerifyResult` - ``.ok`` is ``True`` when every check that ran passed. ``specValid``/``dataMatches`` are ``None`` for checks that could not run.

**Examples**

```python
::

    ds.verify("fig.json").ok                 # untampered?
    ds.verify("fig.png", df=df).dataMatches  # built from this data?
    ds.verify("fig.json", df=[counts, meta]) # multi-frame chart
```
