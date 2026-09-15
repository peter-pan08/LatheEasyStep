"""Qt-free resource contract for interchangeable tool visuals.

The provider deliberately knows nothing about ``Tool``, operations, G-code or
widgets.  A caller supplies a render request and receives either a validated
resource path or an explicit instruction to use the existing procedural
fallback.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Mapping


_SUPPORTED_SUFFIXES = frozenset({".png", ".svg"})


def _key_part(value: object) -> str:
    return re.sub(r"[^a-z0-9_-]+", "-", str(value or "").strip().lower()).strip("-")


def _manifest_key(value: object) -> str:
    return ".".join(part for part in (_key_part(item) for item in str(value).split(".")) if part)


@dataclass(frozen=True)
class ToolVisualRequest:
    family: str
    handed: str = "neutral"
    shape_key: str = ""
    iso_code: str = ""

    def candidate_keys(self) -> tuple[str, ...]:
        family = _key_part(self.family) or "turning"
        handed = _key_part(self.handed) or "neutral"
        shape = _key_part(self.shape_key)
        iso = _key_part(self.iso_code)
        keys = []
        if iso:
            keys.append(f"iso.{iso}")
        if shape:
            keys.append(f"{family}.{handed}.{shape}")
        keys.extend((f"{family}.{handed}", family, "default"))
        return tuple(dict.fromkeys(keys))


@dataclass(frozen=True)
class ToolVisual:
    source: str
    matched_key: str | None = None
    resource_path: Path | None = None
    diagnostic: str | None = None

    @property
    def uses_resource(self) -> bool:
        return self.source == "resource" and self.resource_path is not None


class ToolVisualProvider:
    """Resolve a theme manifest without leaking resource paths into models."""

    def __init__(self, root: str | Path | None = None, manifest: Mapping[str, str] | None = None):
        self._root = Path(root).resolve() if root is not None else None
        self._manifest = {
            _manifest_key(key): value
            for key, value in (manifest or {}).items()
        }

    def resolve(self, request: ToolVisualRequest) -> ToolVisual:
        matched_key = next((key for key in request.candidate_keys() if key in self._manifest), None)
        if matched_key is None:
            return ToolVisual(source="procedural")

        configured = self._manifest[matched_key]
        if not isinstance(configured, str) or not configured.strip():
            return self._fallback(matched_key, "empty resource path")
        relative = Path(configured.strip())
        if relative.is_absolute() or self._root is None:
            return self._fallback(matched_key, "resource path must be relative to a theme root")
        if relative.suffix.lower() not in _SUPPORTED_SUFFIXES:
            return self._fallback(matched_key, "unsupported resource format")

        path = (self._root / relative).resolve()
        try:
            path.relative_to(self._root)
        except ValueError:
            return self._fallback(matched_key, "resource path leaves theme root")
        if not path.is_file():
            return self._fallback(matched_key, "resource file is missing")
        return ToolVisual(source="resource", matched_key=matched_key, resource_path=path)

    @staticmethod
    def _fallback(matched_key: str, reason: str) -> ToolVisual:
        return ToolVisual(
            source="procedural",
            matched_key=matched_key,
            diagnostic=f"Tool visual '{matched_key}': {reason}; using procedural fallback.",
        )
