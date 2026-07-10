from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict

from .ui_registry import COMBO_ITEM_REGISTRY, TAB_TITLE_KEYS, UI_TEXT_KEYS, UI_TOOLTIP_KEYS
from .ui_static import ui_required_keys


DEFAULT_LANGUAGE = "de"
_LOGGER = logging.getLogger(__name__)


class TranslationStore:
    def __init__(self) -> None:
        self._catalogs: Dict[str, Dict[str, str]] = {}
        self._missing_keys: set[tuple[str, str]] = set()
        self._duplicate_keys: set[tuple[str, str]] = set()
        self._load_catalogs()

    def _load_catalogs(self) -> None:
        base_dir = Path(__file__).resolve().parent / "languages"
        ordered = ["de", "en", "es"]
        discovered = []
        try:
            discovered = sorted(path.stem for path in base_dir.glob("*.lng"))
        except Exception:
            discovered = []
        for lang in list(dict.fromkeys(ordered + discovered)):
            path = base_dir / f"{lang}.lng"
            try:
                self._catalogs[lang] = self._parse_lng(path, lang)
            except Exception as exc:
                _LOGGER.warning("Failed to load translation catalog %s: %s", path, exc)
                self._catalogs[lang] = {}

    def _parse_lng(self, path: Path, lang: str) -> Dict[str, str]:
        catalog: Dict[str, str] = {}
        for line_no, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = raw_line.strip()
            if not line or line.startswith("#") or line.startswith(";"):
                continue
            if "=" not in line:
                _LOGGER.warning("[LatheEasyStep][i18n] invalid line in %s:%s -> %s", path, line_no, raw_line)
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if not key:
                _LOGGER.warning("[LatheEasyStep][i18n] empty key in %s:%s", path, line_no)
                continue
            if key in catalog:
                self._duplicate_keys.add((lang, key))
            catalog[key] = value
        return catalog

    def tr(self, key: str, lang: str) -> str:
        if not key:
            return ""
        catalog = self._catalogs.get(lang) or {}
        if key in catalog:
            return str(catalog[key])
        self._missing_keys.add((lang, key))
        return key

    def available_languages(self) -> list[str]:
        return [lang for lang, catalog in self._catalogs.items() if catalog]

    def text(self, object_name: str, lang: str) -> str:
        key = UI_TEXT_KEYS.get(object_name)
        return self.tr(key, lang) if key else object_name

    def tooltip(self, object_name: str, lang: str) -> str:
        key = UI_TOOLTIP_KEYS.get(object_name)
        return self.tr(key, lang) if key else object_name

    def tab_title(self, object_name: str, lang: str) -> str:
        key = TAB_TITLE_KEYS.get(object_name)
        return self.tr(key, lang) if key else object_name

    def combo_items(self, object_name: str, lang: str):
        items = COMBO_ITEM_REGISTRY.get(object_name, [])
        return [(self.tr(text_key, lang), value) for value, text_key in items]

    def required_keys(self) -> set[str]:
        keys = set(UI_TEXT_KEYS.values()) | set(TAB_TITLE_KEYS.values()) | set(UI_TOOLTIP_KEYS.values())
        for items in COMBO_ITEM_REGISTRY.values():
            for _value, text_key in items:
                keys.add(text_key)
        keys.update(ui_required_keys())
        return keys

    def log_missing(self, logger=None) -> None:
        target = logger or _LOGGER
        for lang, key in sorted(self._duplicate_keys):
            try:
                target.warning("[LatheEasyStep][i18n] duplicate translation key '%s' for language '%s'", key, lang)
            except Exception:
                pass
        self._duplicate_keys.clear()
        if not self._missing_keys:
            return
        for lang, key in sorted(self._missing_keys):
            try:
                target.warning("[LatheEasyStep][i18n] missing translation key '%s' for language '%s'", key, lang)
            except Exception:
                pass
        self._missing_keys.clear()

    def validate_language(self, lang: str, logger=None) -> None:
        target = logger or _LOGGER
        catalog = self._catalogs.get(lang) or {}
        for key in sorted(self.required_keys()):
            if key not in catalog:
                self._missing_keys.add((lang, key))
        self.log_missing(target)


TRANSLATIONS = TranslationStore()
