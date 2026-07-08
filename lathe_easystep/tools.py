from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Dict, List


_TOOL_KIND_BY_ORIENTATION: Dict[int, str] = {
    0: "turning",
    1: "drilling",
    2: "drilling",
    3: "drilling",
    4: "grooving",
    5: "grooving",
    6: "grooving",
    7: "grooving",
    8: "threading",
    9: "threading",
}
_ISO_PATTERN = re.compile(r"\b([A-Z]{2,}[A-Z0-9]*?)(\d{2})\b")


@dataclass(frozen=True)
class Tool:
    """Structured view of a LinuxCNC tool entry (for UI + compensation logic)."""

    t: int
    p: int
    d: float
    q: int | None
    comment: str
    iso_code: str | None
    iso_size: str | None
    radius_mm: float
    kind: str
    wear: bool = False
    radius_source: str | None = None

    @property
    def toolno(self) -> int:
        return self.t

    @property
    def orientation(self) -> int | None:
        return self.q

    def __getitem__(self, key):
        if key == "toolno":
            return self.toolno
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(f"{key!r} is not part of Tool")

    def get(self, key, default=None):
        if key == "toolno":
            return self.toolno
        if hasattr(self, key):
            return getattr(self, key)
        return default


def extract_iso_from_comment(comment: str) -> tuple[str | None, str | None, float | None]:
    if not comment:
        return None, None, None
    text = comment.upper()
    for match in _ISO_PATTERN.finditer(text):
        prefix = match.group(1)
        radius_digits = match.group(2)
        iso_candidate = prefix + radius_digits
        digits_only = re.sub(r"[^0-9]", "", iso_candidate)
        if len(digits_only) < 4:
            continue
        size_code = digits_only[:4]
        try:
            radius = int(radius_digits) / 10.0
        except Exception:
            radius = None
        return iso_candidate, size_code, radius
    return None, None, None


def tool_kind_from_orientation(orientation: int | None) -> str:
    if orientation is None:
        return "turning"
    return _TOOL_KIND_BY_ORIENTATION.get(orientation, "parting")


def parse_tool_table(
    filepath: str,
    *,
    log: Callable[[str, str], None] | None = None,
) -> tuple[Dict[int, Tool], List[int]]:
    tools: Dict[int, Tool] = {}
    missing_iso: List[int] = []
    duplicates: set[int] = set()

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for lineno, line in enumerate(f, 1):
            raw = line.strip()
            if not raw or raw.startswith(";") or raw.startswith("#"):
                continue
            left, _, comment = raw.partition(";")
            left = left.strip()
            comment = comment.strip()
            if not left:
                continue

            tokens = left.split()
            token_map: Dict[str, str] = {}
            for token in tokens:
                if len(token) < 2:
                    continue
                key = token[0].upper()
                value = token[1:]
                if not value:
                    continue
                token_map.setdefault(key, value)

            if "T" not in token_map or "P" not in token_map:
                continue
            try:
                toolno = int(float(token_map["T"]))
            except Exception:
                continue
            if toolno <= 0 or toolno >= 10000:
                continue
            if toolno in tools:
                duplicates.add(toolno)
                continue
            try:
                pocket = int(float(token_map.get("P", "0")))
            except Exception:
                pocket = 0
            try:
                diameter = float(token_map.get("D", "0"))
            except Exception:
                diameter = 0.0

            orientation = None
            q_value = token_map.get("Q")
            if q_value is not None:
                try:
                    orientation = int(float(q_value))
                except Exception:
                    orientation = None

            iso_code, iso_size, radius = extract_iso_from_comment(comment)
            if not iso_code:
                missing_iso.append(toolno)
            radius_value = float(radius or 0.0)
            radius_source = "ISO" if radius_value > 0 else None
            if radius_value <= 0 and diameter > 0 and diameter <= 5.0:
                radius_value = diameter
                radius_source = "D"
            kind = tool_kind_from_orientation(orientation)
            tool = Tool(
                t=toolno,
                p=pocket,
                d=diameter,
                q=orientation,
                comment=comment,
                iso_code=iso_code,
                iso_size=iso_size,
                radius_mm=radius_value,
                kind=kind,
                radius_source=radius_source,
            )
            tools[toolno] = tool

    if missing_iso and log:
        formatted = ", ".join(f"T{num:02d}" for num in sorted(set(missing_iso)))
        log("warning", f"[LatheEasyStep] Hinweis: ISO/Radius fehlt bei: {formatted} (optional)")
    if duplicates and log:
        log(
            "info",
            "[LatheEasyStep] Tool-Tabelle: Duplikate ignoriert für "
            + ", ".join(f"T{num:02d}" for num in sorted(duplicates)),
        )

    return tools, sorted(set(missing_iso))
