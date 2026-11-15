"""Interface language (English / European Portuguese).

The language is chosen in ``config.yaml`` (``language: en`` or ``language: pt``) or with the
environment variable ``GREYZONE_LANG``. Texts are written in English in the code and wrapped in
``tr("...")``; the Portuguese versions live in ``i18n_pt.py``. Column names, codes and the model
itself do not change with the language, so files and models work in both languages.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml

SUPPORTED = ("en", "pt")
_CONFIG = Path(__file__).resolve().parent.parent / "config.yaml"


def _detect() -> str:
    env = os.environ.get("GREYZONE_LANG", "").strip().lower()
    if env:
        return env if env in SUPPORTED else "en"
    try:
        with open(_CONFIG, encoding="utf-8") as handle:
            value = str((yaml.safe_load(handle) or {}).get("language", "en")).strip().lower()
    except (OSError, yaml.YAMLError):
        return "en"
    return value if value in SUPPORTED else "en"


LANG = _detect()


def tr(text: str, /, **values) -> str:
    """Translate an English text (and fill its {placeholders})."""
    if LANG == "pt":
        from .i18n_pt import PT

        text = PT.get(text, text)
    return text.format(**values) if values else text


def column_name(name: str) -> str:
    """Name of a variable/column as shown to the user (Portuguese names in Portuguese mode)."""
    if LANG == "pt":
        from .i18n_pt import COLUMN_NAMES

        return COLUMN_NAMES.get(name, name)
    return name


def column_description(name: str, english: str) -> str:
    if LANG == "pt":
        from .i18n_pt import COLUMN_DESCRIPTIONS

        return COLUMN_DESCRIPTIONS.get(name, english)
    return english


def column_unit(unit: str) -> str:
    if LANG == "pt":
        from .i18n_pt import UNITS

        return UNITS.get(unit, unit)
    return unit


def pt_aliases(name: str) -> list[str]:
    """Portuguese column names are always accepted when reading a file (both languages)."""
    from .i18n_pt import COLUMN_NAMES

    return [COLUMN_NAMES[name]] if name in COLUMN_NAMES else []

