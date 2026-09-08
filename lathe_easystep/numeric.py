"""Finite numeric values at file, geometry and generator boundaries."""
from __future__ import annotations

import math
from dataclasses import asdict, is_dataclass


_TEXT_KEYS = {"comment", "title", "name", "program_name", "label", "label_key",
              "description", "contour_name", "header_lines", "footer_lines", "helper_subs"}


def finite_float(value: object, label: str = "Wert") -> float:
    try:
        result = float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(f"{label}: ungueltige Zahl {value!r}.") from exc
    if not math.isfinite(result):
        raise ValueError(f"{label}: Zahl muss endlich sein (kein NaN/Inf).")
    return result


def whole_number(value: object, label: str = "Wert") -> int:
    result = finite_float(value, label)
    if isinstance(value, bool) or not result.is_integer():
        raise ValueError(f"{label}: ganze Zahl erforderlich.")
    return int(result)


def validate_finite_data(value: object, label: str = "Daten") -> None:
    """Reject non-finite numeric payloads before derived geometry is evaluated.

    Descriptive strings are not numbers. Numeric fields saved as strings are
    checked too; ordinary enum tokens are left to their domain validators.
    """
    if is_dataclass(value) and not isinstance(value, type):
        validate_finite_data(asdict(value), label)
    elif isinstance(value, dict):
        for key, item in value.items():
            if str(key) in _TEXT_KEYS or str(key).startswith("__"):
                continue
            validate_finite_data(item, f"{label}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            validate_finite_data(item, f"{label}[{index}]")
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        finite_float(value, label)
    elif isinstance(value, str):
        try:
            result = float(value)
        except (ValueError, OverflowError):
            return
        if not math.isfinite(result):
            raise ValueError(f"{label}: Zahl muss endlich sein (kein NaN/Inf).")
