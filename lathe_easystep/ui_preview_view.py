from __future__ import annotations

"""Schmale Ausgabeschnittstelle fuer Seiten-, Schnitt- und Konturvorschau."""

from .ui_helpers import current_language


class PreviewView:
    """Kapselt die konkreten Preview-Widgets hinter fachlichen Operationen."""

    def __init__(self, handler):
        self._handler = handler

    def is_bound(self) -> bool:
        return self._handler.preview is not None or self._handler.contour_preview is not None

    @staticmethod
    def _set_paths(widget, paths, active_index) -> None:
        try:
            widget.set_paths(paths, active_index)
        except TypeError:
            widget.set_paths(paths)

    @staticmethod
    def _set_context(widget, program_context, active_operation) -> None:
        try:
            widget.set_front_context(program_context, active_operation)
        except Exception:
            pass

    @staticmethod
    def _set_messages(widget, messages) -> None:
        if hasattr(widget, "set_status_messages"):
            widget.set_status_messages(messages)

    @staticmethod
    def _set_language(widget, lang) -> None:
        # ID-only-Vollaudit 2026-09-21: die Canvas-Beschriftung (Legende,
        # Warnungsbox, Schnitt-/Vorderansicht-Labels) braucht die aktuelle
        # Sprache bei jedem Neuzeichnen, siehe ViewState.language.
        if hasattr(widget, "language"):
            try:
                widget.language = lang
            except Exception:
                pass

    def apply_paths(
        self,
        paths,
        *,
        active_index=None,
        include_contour_preview=True,
        program_context=None,
        active_operation=None,
        collision=False,
    ) -> None:
        handler = self._handler
        context = program_context or {}
        messages = context.get("__warnings", []) if context.get("preview_warnings") else []
        lang = current_language(handler)
        preview = handler.preview

        if preview is not None:
            if hasattr(preview, "set_collision"):
                preview.set_collision(collision)
            self._set_language(preview, lang)
            self._set_messages(preview, messages)
            self._set_paths(preview, paths, active_index)
            self._set_context(preview, program_context, active_operation)
            try:
                if getattr(preview, "slice_enabled", False):
                    handler._ensure_slice_z_matches_operation(active_operation)
            except Exception:
                pass

        preview_slice = handler.preview_slice
        if preview_slice is not None and getattr(preview_slice, "isVisible", lambda: False)():
            try:
                preview_slice.set_view_mode("front")
            except Exception:
                pass
            try:
                preview_slice.set_slice_z(getattr(preview, "slice_z", 0.0) if preview is not None else 0.0)
            except Exception:
                pass
            self._set_language(preview_slice, lang)
            self._set_messages(preview_slice, messages)
            self._set_paths(preview_slice, paths, active_index)
            self._set_context(preview_slice, program_context, active_operation)

        contour_preview = handler.contour_preview
        if include_contour_preview and contour_preview is not None:
            self._set_language(contour_preview, lang)
            self._set_paths(contour_preview, paths, active_index)

    def apply_scene(
        self,
        scene,
        *,
        include_contour_preview=True,
        program_context=None,
        active_operation=None,
        collision=False,
    ) -> None:
        """Publish layer metadata where supported, with legacy fallback."""
        for widget in (
            self._handler.preview,
            self._handler.preview_slice,
            self._handler.contour_preview if include_contour_preview else None,
        ):
            if widget is None:
                continue
            if hasattr(widget, "set_preview_scene"):
                widget.set_preview_scene(scene)
            elif hasattr(widget, "preview_scene"):
                widget.preview_scene = scene
        # Existing widgets continue to consume the stable flattened view.
        self.apply_paths(
            scene.paths,
            active_index=scene.active_index,
            include_contour_preview=include_contour_preview,
            program_context=program_context,
            active_operation=active_operation,
            collision=collision,
        )
