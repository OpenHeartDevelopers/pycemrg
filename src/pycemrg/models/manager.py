# src/pycemrg/models/manager.py
#
# Deprecation shim. The implementation has moved to
# pycemrg.assets.manager.AssetManager. This module re-exports a thin
# subclass that emits a DeprecationWarning on construction so existing
# callers keep working through the deprecation window.
#
# Removal: scheduled for release N+2 (see ticket).

import warnings

from pycemrg.assets.manager import AssetManager, TqdmUpTo  # noqa: F401

__all__ = ["ModelManager", "TqdmUpTo"]


class ModelManager(AssetManager):
    """Deprecated alias for :class:`pycemrg.assets.AssetManager`."""

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "pycemrg.models.manager.ModelManager is deprecated; "
            "use pycemrg.assets.AssetManager instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
