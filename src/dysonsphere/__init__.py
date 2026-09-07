# Support modules are namespaced surfaces; their contents are deliberately NOT star-imported
# into the top namespace.
from . import ext, metadata, palettes, stats, transforms, utils  # noqa: F401
from .annotations import *  # noqa: F403
from .assembly import *  # noqa: F403
from .discovery import *  # noqa: F403
from .display_labels import *  # noqa: F403
from .export import *  # noqa: F403
from .marks import *  # noqa: F403
from .multilabel import *  # noqa: F403
from .nonlinear import *  # noqa: F403
from .palettes import palette
from .table import *  # noqa: F403
from .theme import *  # noqa: F403

# The public API - star-imported names, palette, and public namespaces, written out so the
# surface is documented in one place and guarded by tests (test_package_namespace). Every
# module defines its own __all__, so the star-imports above bind exactly these names and
# nothing else (no leaked stdlib/third-party imports on the dysonsphere namespace).
__all__ = [
    "add_log_ticks",
    "add_multilabel",
    "add_pow_ticks",
    "assemble",
    "create_config",
    "extensions",
    "label_expr",
    "labels",
    "load",
    "load_extension",
    "log_label_expr",
    "mark_strip",
    "mark_table",
    "mark_violin",
    "metadata",
    "palette",
    "palettes",
    "rule",
    "save",
    "shade",
    "show",
    "stats",
    "text",
    "theme",
    "transforms",
    "utils",
]


def __getattr__(name: str):
    """Lazily resolve installed extensions as attributes (PEP 562).

    ``dysonsphere.biology`` imports and returns the ``dysonsphere-biology`` extension when it
    is installed (registered under the ``dysonsphere.extensions`` entry-point group); the
    resolved module is cached in the package namespace so later access skips discovery. Any
    other missing attribute raises ``AttributeError`` as usual (a plain typo and an
    uninstalled extension are indistinguishable here - use ``extensions()`` to list what is
    installed, or ``load_extension(name)`` for an ImportError that names them).
    """
    from .discovery import _extension_entry_points

    ep = _extension_entry_points().get(name)
    if ep is not None:
        module = ep.load()
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
