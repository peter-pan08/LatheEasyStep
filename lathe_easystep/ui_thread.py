from __future__ import annotations

from .presets import validate_thread_preset_data


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
        major = data.get("major")
        pitch = data.get("pitch")
        profile = data.get("profile", "metric")

        # Major & Pitch: beim Wechsel immer sichtbar setzen (oder ersetzen bei force)
        if isinstance(major, (int, float)) and self.thread_major_diameter:
            if force or abs(float(self.thread_major_diameter.value())) < 1e-9:
                self.thread_major_diameter.setValue(float(major))
        if isinstance(pitch, (int, float)) and self.thread_pitch:
            if force or abs(float(self.thread_pitch.value())) < 1e-9:
                self.thread_pitch.setValue(float(pitch))

        p = float(pitch) if isinstance(pitch, (int, float)) else 1.5

        # Profil-spezifische Default-Werte
        if profile == "tr":
            depth = p * 0.50
            q_angle = 15.0
        else:
            depth = p * 0.6134
            q_angle = 29.5

        first_depth = max(depth * 0.10, p * 0.05)
        peak_offset = -max(depth * 0.50, p * 0.25)

        # Soft-Set / Force-Set
        changed = []
        if force:
            if self.thread_depth is not None:
                self.thread_depth.setValue(float(depth)); changed.append('depth')
            if self.thread_first_depth is not None:
                self.thread_first_depth.setValue(float(first_depth)); changed.append('first_depth')
            if self.thread_peak_offset is not None:
                self.thread_peak_offset.setValue(float(peak_offset)); changed.append('peak_offset')
            if self.thread_retract_r is not None:
                self.thread_retract_r.setValue(1.5); changed.append('retract_r')
            if self.thread_infeed_q is not None:
                self.thread_infeed_q.setValue(q_angle); changed.append('infeed_q')
            if self.thread_spring_passes is not None:
                self.thread_spring_passes.setValue(1); changed.append('spring_passes')
            if self.thread_e is not None:
                self.thread_e.setValue(0.0); changed.append('e')
            if self.thread_l is not None:
                self.thread_l.setValue(0); changed.append('l')
        else:
            if self._set_if_zero(self.thread_depth, depth): changed.append('depth')
            if self._set_if_zero(self.thread_first_depth, first_depth): changed.append('first_depth')
            if self._set_if_zero(self.thread_peak_offset, peak_offset): changed.append('peak_offset')
            if self._set_if_zero(self.thread_retract_r, 1.5): changed.append('retract_r')
            if self._set_if_zero(self.thread_infeed_q, q_angle): changed.append('infeed_q')
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
            self._log(f"[LatheEasyStep] _apply_thread_preset: profile={profile}, pitch={p}, changed={changed}", level="info")
        except Exception:
            pass
    finally:
        self._thread_applying_standard = False
