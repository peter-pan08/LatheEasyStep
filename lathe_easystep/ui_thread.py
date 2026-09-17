from __future__ import annotations

from .presets import (
    metric_thread_presets,
    thread_preset_values,
    trapezoidal_thread_presets,
    validate_thread_preset_data,
)
from .translations import TRANSLATIONS


def populate_thread_standard_options(self):
    combo = self.thread_standard
    if combo is None or self._thread_standard_populated:
        return

    def _compact(value: float) -> str:
        text = f"{value:.3f}".rstrip("0").rstrip(".")
        return text if text else "0"

    lang = self._current_language_code()
    custom_key = "combo.thread_standard.custom"

    combo.blockSignals(True)
    combo.clear()
    combo.addItem(TRANSLATIONS.tr(custom_key, lang), {"label_key": custom_key})
    # Metric threads (ISO 60 deg) -> profile "metric"
    for name, diameter, pitch in metric_thread_presets():
        pitch_text = _compact(pitch)
        technical_id = f"thread.standard.metric.{name.lower()}x{pitch_text.replace('.', '_')}"
        combo.addItem(
            TRANSLATIONS.tr(technical_id, lang),
            {
                "label": name,
                "label_key": technical_id,
                "major": diameter,
                "pitch": pitch,
                "profile": "metric",
            },
        )
    # Trapezoidal threads -> profile "tr"
    for name, diameter, pitch in trapezoidal_thread_presets():
        pitch_text = _compact(pitch)
        technical_id = f"thread.standard.tr.{name.lower()}x{pitch_text.replace('.', '_')}"
        combo.addItem(
            TRANSLATIONS.tr(technical_id, lang),
            {
                "label": name,
                "label_key": technical_id,
                "major": diameter,
                "pitch": pitch,
                "profile": "tr",
            },
        )
    combo.setCurrentIndex(0)
    combo.blockSignals(False)
    self._thread_standard_populated = True


def apply_thread_preset(self, force: bool = False):
    """Wendet das im Dropdown gewählte Preset an.

    Wenn force==False: nur Felder befüllen, die noch 0 sind (soft-fill).
    Wenn force==True: alle relevanten Felder überschreiben.
    """
    # Vermeide Rekursion
    if getattr(self, "_thread_applying_standard", False):
        return
    combo = self.thread_standard
    if combo is None:
        return
    data = combo.currentData()
    if not isinstance(data, dict):
        return
    validation_errors = validate_thread_preset_data(data)
    if validation_errors:
        try:
            self._log(
                f"[LatheEasyStep] thread preset skipped: {'; '.join(validation_errors)}",
                level="warning",
            )
        except Exception:
            pass
        return

    self._thread_applying_standard = True
    try:
        values = thread_preset_values(data)
        if values is None:
            return
        major = values["major_diameter"]
        pitch = values["pitch"]

        # Die Auswahl eines Standards setzt seine beiden Identitaetswerte
        # immer sichtbar. Nur die abgeleiteten Bearbeitungswerte bleiben beim
        # normalen Wechsel als Soft-Fill erhalten; der Button erzwingt alle.
        if self.thread_major_diameter is not None:
            self.thread_major_diameter.setValue(major)
        if self.thread_pitch is not None:
            self.thread_pitch.setValue(pitch)

        # Soft-Set / Force-Set
        changed = []
        if force:
            if self.thread_depth is not None:
                self.thread_depth.setValue(values["thread_depth"]); changed.append('depth')
            if self.thread_first_depth is not None:
                self.thread_first_depth.setValue(values["first_depth"]); changed.append('first_depth')
            if self.thread_peak_offset is not None:
                self.thread_peak_offset.setValue(values["peak_offset"]); changed.append('peak_offset')
            if self.thread_retract_r is not None:
                self.thread_retract_r.setValue(values["retract_r"]); changed.append('retract_r')
            if self.thread_infeed_q is not None:
                self.thread_infeed_q.setValue(values["infeed_q"]); changed.append('infeed_q')
            if self.thread_spring_passes is not None:
                self.thread_spring_passes.setValue(1); changed.append('spring_passes')
            if self.thread_e is not None:
                self.thread_e.setValue(0.0); changed.append('e')
            if self.thread_l is not None:
                self.thread_l.setValue(0); changed.append('l')
        else:
            if self._set_if_zero(self.thread_depth, values["thread_depth"]): changed.append('depth')
            if self._set_if_zero(self.thread_first_depth, values["first_depth"]): changed.append('first_depth')
            if self._set_if_zero(self.thread_peak_offset, values["peak_offset"]): changed.append('peak_offset')
            if self._set_if_zero(self.thread_retract_r, values["retract_r"]): changed.append('retract_r')
            if self._set_if_zero(self.thread_infeed_q, values["infeed_q"]): changed.append('infeed_q')
            # spring passes
            if self.thread_spring_passes is not None:
                try:
                    if force or int(self.thread_spring_passes.value()) == 0:
                        self.thread_spring_passes.setValue(1); changed.append('spring_passes')
                except Exception:
                    pass
            if self._set_if_zero(self.thread_e, 0.0): changed.append('e')
            if self.thread_l is not None:
                try:
                    if force or int(self.thread_l.value()) == 0:
                        self.thread_l.setValue(0); changed.append('l')
                except Exception:
                    pass
        # Debug-Ausgabe
        try:
            self._log(f"[LatheEasyStep] _apply_thread_preset: profile={data.get('profile')}, pitch={pitch}, changed={changed}", level="info")
        except Exception:
            pass
    finally:
        self._thread_applying_standard = False
