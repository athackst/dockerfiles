"""Shared templates.yml interface for generation and workflows."""

from .api import (
    Templates,
    canonical_platform,
    eol_is_past,
    filter_targets_by_platform,
    parse_platform,
    platforms_support,
)

__version__ = "0.1.0"

__all__ = [
    "Templates",
    "canonical_platform",
    "eol_is_past",
    "filter_targets_by_platform",
    "parse_platform",
    "platforms_support",
    "__version__",
]
