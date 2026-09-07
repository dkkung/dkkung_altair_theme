"""Guards the package's public namespace - the per-module __all__ contract (v3.0).

Before v3.0 the star-imports in __init__.py ran without per-module __all__ lists, leaking
every top-level import (ds.np, ds.math, ds.json, even ds.field from dataclasses) onto the
public namespace. These tests pin the intended API surface so a new module-level import
can never silently become public again.
"""

import importlib
import importlib.util
from types import ModuleType

import dysonsphere as ds

# importlib (not `from dysonsphere import ...`): the theme FUNCTION shadows its module on
# the package namespace, so attribute access would hand back the wrong object.
_MODULE_NAMES = [
    "annotations",
    "discovery",
    "export",
    "labels",
    "marks",
    "metadata",
    "assembly",
    "multilabel",
    "nonlinear",
    "palettes",
    "table",
    "theme",
    "transforms",
    "utils",
]
_MODULES = [importlib.import_module(f"dysonsphere.{name}") for name in _MODULE_NAMES]


class TestPackageNamespace:
    def test_every_public_name_resolves(self):
        for name in ds.__all__:
            assert getattr(ds, name, None) is not None, f"ds.{name} in __all__ but missing"

    def test_package_all_is_union_of_module_alls(self):
        # __init__.__all__ is written out explicitly (self-documenting); this keeps it in
        # sync with star-imported modules plus the stats namespace, not its functions.
        union = {name for mod in _MODULES for name in mod.__all__}
        assert sorted(ds.__all__) == sorted(union | {"stats"})

    def test_stats_surface_is_namespaced_only(self):
        assert isinstance(ds.stats, ModuleType)
        assert ds.stats is importlib.import_module("dysonsphere.stats")
        assert sorted(ds.stats.__all__) == ["clear_stats", "comparisons", "correlation"]
        for name in ds.stats.__all__:
            assert callable(getattr(ds.stats, name))
            assert name not in ds.__all__
            assert not hasattr(ds, name), f"stats.{name} leaked onto the top namespace"
        for name in ("add_comparisons", "add_correlation"):
            assert not hasattr(ds.stats, name)
            assert not hasattr(ds, name)
            assert name not in ds.__all__
        for name in ("inference", "statistics"):
            assert importlib.util.find_spec(f"dysonsphere.{name}") is None
            assert not hasattr(ds, name)
            assert name not in ds.__all__

    def test_every_module_defines_all(self):
        for mod in _MODULES:
            assert hasattr(mod, "__all__"), f"{mod.__name__} lacks __all__ (would leak its imports)"

    def test_no_leaked_stdlib_or_thirdparty_names(self):
        # the exact names that leaked before v3.0
        for leaked in ("alt", "np", "pl", "math", "json", "os", "sys", "re", "Path", "Any", "cast", "field"):
            assert leaked not in ds.__all__, f"ds.__all__ leaks {leaked!r}"

    def test_ext_surface_is_namespaced_only(self):
        # dysonsphere.ext (the extension-author primitive surface) is bound as ds.ext but its
        # contents stay OFF the top namespace - `ext` is deliberately absent from _MODULE_NAMES
        # above because it is not star-imported (its __all__ must not join ds.__all__).
        from dysonsphere import ext

        assert callable(ext.opt) and callable(ext.internal_data)
        for name in ext.__all__:
            assert name not in ds.__all__, f"ext.{name} leaked onto the top namespace"
