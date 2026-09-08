from __future__ import annotations

from typing import Dict


def collect_program_header(self) -> Dict[str, object]:
    """Sammelt alle Programmkopf-Parameter für Kommentare/G-Code."""
    def _ensure_checkbox(attr_name: str):
        widget = getattr(self, attr_name, None)
        if widget is not None and hasattr(widget, "isChecked"):
            return widget
        candidate = self._get_widget_by_name(attr_name)
        if candidate is not None and hasattr(candidate, "isChecked"):
            setattr(self, attr_name, candidate)
            return candidate
        setattr(self, attr_name, None)
        return None

    def _combo_data(widget):
        if widget is None:
            return None
        if hasattr(widget, "currentData"):
            try:
                data = widget.currentData()
            except Exception:
                data = None
            if data is not None:
                return data
        try:
            name = str(widget.objectName() or "").strip()
        except Exception:
            name = ""
        if name == "program_unit":
            try:
                return "mm" if int(widget.currentIndex()) == 0 else "inch"
            except Exception:
                return None
        if name == "program_npv" and hasattr(widget, "currentText"):
            try:
                token = str(widget.currentText() or "").strip().upper()
            except Exception:
                token = ""
            if token.startswith("G"):
                return token
        return None

    # Fehlende Widgets nachladen, falls sie zum Zeitpunkt der Initialisierung
    # noch nicht gefunden wurden (z. B. wegen verzögertem UI-Aufbau).
    if self.program_npv is None:
        self.program_npv = self._get_widget_by_name("program_npv")
    if self.program_unit is None:
        self.program_unit = self._find_unit_combo()
    if self.program_shape is None:
        self.program_shape = self._find_shape_combo()
    if self.program_retract_mode is None:
        self.program_retract_mode = self._get_widget_by_name("program_retract_mode")
    if self.program_s1 is None:
        self.program_s1 = self._get_widget_by_name("program_s1")
    if self.program_s3 is None:
        self.program_s3 = self._get_widget_by_name("program_s3")
    if self.program_has_subspindle is None:
        self.program_has_subspindle = self._get_widget_by_name("program_has_subspindle")
    if self.program_xt is None:
        self.program_xt = self._get_widget_by_name("program_xt")
    if self.program_zt is None:
        self.program_zt = self._get_widget_by_name("program_zt")
    if self.program_sc is None:
        self.program_sc = self._get_widget_by_name("program_sc")
    if getattr(self, "program_machine_profile", None) is None:
        self.program_machine_profile = self._get_widget_by_name("program_machine_profile")
    if getattr(self, "program_chuck_size", None) is None:
        self.program_chuck_size = self._get_widget_by_name("program_chuck_size")
    if getattr(self, "program_chuck_part_type", None) is None:
        self.program_chuck_part_type = self._get_widget_by_name("program_chuck_part_type")
    if getattr(self, "program_chuck_grip_mode", None) is None:
        self.program_chuck_grip_mode = self._get_widget_by_name("program_chuck_grip_mode")
    if getattr(self, "program_chuck_profile", None) is None:
        self.program_chuck_profile = self._get_widget_by_name("program_chuck_profile")
    if getattr(self, "program_chuck_x_min", None) is None:
        self.program_chuck_x_min = self._get_widget_by_name("program_chuck_x_min")
    if getattr(self, "program_chuck_x_max", None) is None:
        self.program_chuck_x_max = self._get_widget_by_name("program_chuck_x_max")
    if getattr(self, "program_chuck_z_limit", None) is None:
        self.program_chuck_z_limit = self._get_widget_by_name("program_chuck_z_limit")
    if self.program_name is None:
        self.program_name = self._get_widget_by_name("program_name")
    for attr in (
        "program_spindle_mode",
        "program_spindle_max_rpm",
        "program_park_mode",
        "program_toolchange_coords",
        "program_park_coords",
        "program_park_x",
        "program_park_z",
        "program_park_sequential",
        "program_optional_stop_toolchange",
        "program_preview_warnings",
    ):
        if getattr(self, attr, None) is None:
            setattr(self, attr, self._get_widget_by_name(attr))
    if self.program_xa is None:
        self.program_xa = self._get_widget_by_name("program_xa")
    if self.program_xi is None:
        self.program_xi = self._get_widget_by_name("program_xi")
    if self.program_za is None:
        self.program_za = self._get_widget_by_name("program_za")
    if self.program_zi is None:
        self.program_zi = self._get_widget_by_name("program_zi")
    if self.program_zb is None:
        self.program_zb = self._get_widget_by_name("program_zb")
    if self.program_w is None:
        self.program_w = self._get_widget_by_name("program_w")
    if self.program_l is None:
        self.program_l = self._get_widget_by_name("program_l")
    if self.program_n is None:
        self.program_n = self._get_widget_by_name("program_n")
    if self.program_sw is None:
        self.program_sw = self._get_widget_by_name("program_sw")
    if self.program_xra is None:
        self.program_xra = self._get_widget_by_name("program_xra")
    if self.program_xri is None:
        self.program_xri = self._get_widget_by_name("program_xri")
    if self.program_zra is None:
        self.program_zra = self._get_widget_by_name("program_zra")
    if self.program_zri is None:
        self.program_zri = self._get_widget_by_name("program_zri")
    if self.program_xra_absolute is None:
        self.program_xra_absolute = self._get_widget_by_name("program_xra_absolute")
    if self.program_xri_absolute is None:
        self.program_xri_absolute = self._get_widget_by_name("program_xri_absolute")
    if self.program_zra_absolute is None:
        self.program_zra_absolute = self._get_widget_by_name("program_zra_absolute")
    if self.program_zri_absolute is None:
        self.program_zri_absolute = self._get_widget_by_name("program_zri_absolute")
    self.program_xra_absolute = _ensure_checkbox("program_xra_absolute")
    self.program_xri_absolute = _ensure_checkbox("program_xri_absolute")
    self.program_zra_absolute = _ensure_checkbox("program_zra_absolute")
    self.program_zri_absolute = _ensure_checkbox("program_zri_absolute")
    self.program_xt_absolute = _ensure_checkbox("program_xt_absolute")
    self.program_zt_absolute = _ensure_checkbox("program_zt_absolute")
    self.program_has_subspindle = _ensure_checkbox("program_has_subspindle")
    self.program_park_sequential = _ensure_checkbox("program_park_sequential")
    self.program_optional_stop_toolchange = _ensure_checkbox("program_optional_stop_toolchange")
    self.program_preview_warnings = _ensure_checkbox("program_preview_warnings")

    header: Dict[str, object] = {}
    if self.program_npv:
        header["npv"] = _combo_data(self.program_npv)
    if self.program_unit:
        header["unit"] = _combo_data(self.program_unit)
    if self.program_shape:
        header["shape"] = _combo_data(self.program_shape)

    def _val(widget):
        if widget is None:
            return None
        if hasattr(widget, "value") and callable(getattr(widget, "value")):
            try:
                return float(widget.value())
            except Exception:
                return None
        if hasattr(widget, "text") and callable(getattr(widget, "text")):
            t = widget.text().strip()
            if not t:
                return None
            try:
                return float(t.replace(",", "."))
            except Exception:
                return None
        return None

    # Rohteilabmessungen / Spannmaße
    header["xa"] = _val(self.program_xa)
    header["xi"] = _val(self.program_xi)
    header["za"] = _val(self.program_za)
    header["zi"] = _val(self.program_zi)
    header["zb"] = _val(self.program_zb)
    header["w"] = _val(self.program_w)
    header["l"] = _val(self.program_l)
    header["n_edges"] = _val(self.program_n)
    header["sw"] = _val(self.program_sw)

    # Rückzug/Ebenen
    header["retract_mode"] = (
        str(_combo_data(self.program_retract_mode) or "").strip()
        if self.program_retract_mode
        else ""
    )
    header["xra"] = _val(self.program_xra)
    header["xri"] = _val(self.program_xri)
    header["zra"] = _val(self.program_zra)
    header["zri"] = _val(self.program_zri)

    # Absolute flags for retract planes stay available because roughing and
    # safety moves still distinguish between work and machine references.
    header["xra_absolute"] = bool(self.program_xra_absolute.isChecked()) if self.program_xra_absolute else False
    header["xri_absolute"] = bool(self.program_xri_absolute.isChecked()) if self.program_xri_absolute else False
    header["zra_absolute"] = bool(self.program_zra_absolute.isChecked()) if self.program_zra_absolute else False
    header["zri_absolute"] = bool(self.program_zri_absolute.isChecked()) if self.program_zri_absolute else False
    header["xt_absolute"] = bool(self.program_xt_absolute.isChecked()) if self.program_xt_absolute else False
    header["zt_absolute"] = bool(self.program_zt_absolute.isChecked()) if self.program_zt_absolute else False

    # Werkzeugwechsel-/Sicherheitspositionen
    header["xt"] = _val(self.program_xt)
    header["zt"] = _val(self.program_zt)
    header["sc"] = _val(self.program_sc)
    if getattr(self, "program_machine_profile", None):
        header["machine_profile"] = _combo_data(self.program_machine_profile)
    if getattr(self, "program_chuck_size", None):
        header["chuck_size"] = _combo_data(self.program_chuck_size)
    if getattr(self, "program_chuck_part_type", None):
        header["chuck_part_type"] = _combo_data(self.program_chuck_part_type)
    if getattr(self, "program_chuck_grip_mode", None):
        header["chuck_grip_mode"] = _combo_data(self.program_chuck_grip_mode)
    if getattr(self, "program_chuck_profile", None):
        header["chuck_profile"] = _combo_data(self.program_chuck_profile)
    header["chuck_no_go_x_min"] = _val(getattr(self, "program_chuck_x_min", None))
    header["chuck_no_go_x_max"] = _val(getattr(self, "program_chuck_x_max", None))
    header["chuck_no_go_z_limit"] = _val(getattr(self, "program_chuck_z_limit", None))
    if getattr(self, "program_spindle_mode", None):
        header["spindle_mode"] = _combo_data(self.program_spindle_mode)
    header["spindle_max_rpm"] = _val(getattr(self, "program_spindle_max_rpm", None))
    if getattr(self, "program_park_mode", None):
        header["park_mode"] = _combo_data(self.program_park_mode)
    if getattr(self, "program_toolchange_coords", None):
        header["toolchange_coords"] = _combo_data(self.program_toolchange_coords)
        toolchange_coords = str(header.get("toolchange_coords", "work") or "work").strip().lower()
        header["xt_absolute"] = toolchange_coords != "machine"
        header["zt_absolute"] = toolchange_coords != "machine"
    if getattr(self, "program_park_coords", None):
        header["park_coords"] = _combo_data(self.program_park_coords)
    else:
        xt_abs = bool(header.get("xt_absolute", True))
        zt_abs = bool(header.get("zt_absolute", True))
        header["toolchange_coords"] = "work" if xt_abs and zt_abs else "machine"
        header["park_coords"] = header.get("toolchange_coords", "work")
    header["park_x"] = _val(getattr(self, "program_park_x", None))
    header["park_z"] = _val(getattr(self, "program_park_z", None))
    header["park_sequential"] = bool(self.program_park_sequential.isChecked()) if self.program_park_sequential else False
    header["optional_stop_toolchange"] = bool(self.program_optional_stop_toolchange.isChecked()) if self.program_optional_stop_toolchange else False
    header["preview_warnings"] = bool(self.program_preview_warnings.isChecked()) if self.program_preview_warnings else False

    if self.program_name:
        header["program_name"] = self.program_name.text().strip()

    # Drehzahlbegrenzung (S3 nur, wenn Gegenspindel aktiv)
    header["has_subspindle"] = bool(self.program_has_subspindle.isChecked()) if self.program_has_subspindle else False
    header["s1_max"] = float(self.program_s1.value()) if self.program_s1 else 0.0
    if header["has_subspindle"]:
        header["s3_max"] = float(self.program_s3.value()) if self.program_s3 else 0.0
    else:
        header["s3_max"] = 0.0

    cached = getattr(self, "_program_header_cache", None)
    if isinstance(cached, dict):
        merged = dict(cached)
        for key, value in header.items():
            if value is None:
                continue
            if isinstance(value, str) and value == "":
                continue
            merged[key] = value
        header = merged

    self._program_header_cache = dict(header)
    return header
