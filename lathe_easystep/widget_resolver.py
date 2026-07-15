"""Robuste Widget-Suche fuer QtVCP-Embedding (Standalone vs. eingebettetes Panel).

Reine Qt-Baumsuche ohne fachliche Logik: findet den Panel-Root unter mehreren
moeglichen Host-Fenstern und loest Widgetnamen tolerant auf (exakte Treffer,
Suffix-Varianten, Typ-Praeferenz). Vom Handler nur ueber `WidgetResolver`
instanziiert, siehe `HandlerClass._setup_resolver()`.
"""

from __future__ import annotations

from qtpy import QtCore, QtWidgets

from .ui_registry import PANEL_WIDGET_NAMES


class WidgetResolveError(RuntimeError):
    pass


def _qname(obj):
    try:
        return obj.metaObject().className()
    except Exception:
        return type(obj).__name__


def _path_to_root(w, max_up=25):
    """Debug helper: show parent chain up to root."""
    parts = []
    cur = w
    for _ in range(max_up):
        if cur is None:
            break
        on = getattr(cur, "objectName", lambda: "")()
        parts.append(f"{_qname(cur)}('{on}')")
        cur = cur.parent()
    return " <- ".join(parts)


def _pick_best_root(widgets):
    """
    Try to select a usable root from widgets/handler context.
    Priority:
      1) nearest panel/root marker in parent tree
      2) first QMainWindow/QDialog in parent tree
      3) the first passed widget
    """
    for w in widgets:
        cur = w
        for _ in range(30):
            if cur is None:
                break
            try:
                if cur.objectName() in PANEL_WIDGET_NAMES:
                    if cur.objectName() in ("MainWindow", "VCPWindow") and not _looks_like_panel_widget(cur):
                        pass
                    else:
                        return cur
            except Exception:
                pass
            try:
                if _looks_like_panel_widget(cur):
                    return cur
            except Exception:
                pass
            if isinstance(cur, QtWidgets.QMainWindow):
                return cur
            if isinstance(cur, QtWidgets.QDialog):
                return cur
            cur = cur.parent()

    for w in widgets:
        if w is not None:
            return w

    return None


class WidgetResolver:
    """
    Central widget resolver:
      - resolve(): strict, type-safe, collision-aware
      - try_resolve(): returns None instead of exception
      - resolve_later(): retry via QTimer (embed/timing robust)
    """

    def __init__(self, *, root=None, widgets=None, logger=None):
        self.logger = logger
        self.root = root
        self.widgets = list(widgets) if widgets else []

        if self.root is None:
            self.root = _pick_best_root(self.widgets)

    def _log(self, level, msg):
        if self.logger:
            fn = getattr(self.logger, level, None)
            if callable(fn):
                fn(msg)
                return

        # Reduce noisy warnings when the resolver root is a generic MainWindow/VCPWindow
        # but the actual embedded panel is present in the widget list. In that case
        # many early lookups will naturally fail against the host window; degrade
        # warnings to debug to avoid flooding the startup log.
        try:
            root_name = getattr(self.root, "objectName", lambda: "")()
            if level == "warning" and root_name in ("MainWindow", "VCPWindow"):
                for w in (self.widgets or []):
                    try:
                        if getattr(w, "objectName", lambda: "")() in PANEL_WIDGET_NAMES:
                            level = "debug"
                            break
                    except Exception:
                        continue
        except Exception:
            pass

        # If any of the known roots/widgets is the panel and it has not yet been
        # marked as `ui_ready`, demote warnings to debug to avoid spurious
        # "not found" messages during early startup when the embedded UI
        # is still being constructed.
        try:
            for candidate in ([self.root] + (self.widgets or [])):
                if candidate is None:
                    continue
                ui_ready = getattr(candidate, "ui_ready", None)
                if ui_ready is False and level in ("warning", "debug"):
                    # completely suppress non-error logs until UI is ready
                    return
        except Exception:
            pass

        # Prefer explicit logger if provided, otherwise use module logger.
        logger = self.logger if self.logger is not None else _LOGGER

        # Resolve to a callable logging function (debug/info/warning/error).
        log_fn = getattr(logger, level, None)
        if not callable(log_fn):
            log_fn = getattr(logger, "debug", None)

        # Emit log via logger; swallow any logging errors to avoid startup failures.
        try:
            if callable(log_fn):
                log_fn(f"[WidgetResolver][{level.upper()}] {msg}")
        except Exception:
            # Best-effort fallback: do nothing to avoid noisy prints during startup.
            pass

    def _candidates(self, cls, name=None, *, root=None):
        roots = []
        if root is not None:
            roots.append(root)
        if self.root is not None and self.root not in roots:
            roots.append(self.root)

        for w in self.widgets:
            if w is not None and w not in roots:
                roots.append(w)

        found = []
        # If name is an idx lookup (id:NN or digits), search by dynamic property 'idx'
        maybe_id = None
        try:
            if isinstance(name, str):
                if name.startswith("id:"):
                    maybe_id = name.split(":", 1)[1]
                elif name.isdigit():
                    maybe_id = name
        except Exception:
            maybe_id = None
        if maybe_id is not None:
            try:
                iid = int(maybe_id)
                for r in roots:
                    try:
                        for w in r.findChildren(cls, options=QtCore.Qt.FindChildrenRecursively):
                            try:
                                val = w.property("idx")
                                if val is None:
                                    continue
                                if (isinstance(val, int) and val == iid) or (isinstance(val, str) and val.isdigit() and int(val) == iid):
                                    found.append(w)
                            except Exception:
                                continue
                    except Exception:
                        continue
            except Exception:
                pass

        for r in roots:
            if r is None:
                continue
            if name:
                c = r.findChildren(cls, name, QtCore.Qt.FindChildrenRecursively)
            else:
                c = r.findChildren(cls, options=QtCore.Qt.FindChildrenRecursively)
            found.extend(c)

        for w in self.widgets:
            if w is None:
                continue
            if name:
                c = w.findChildren(cls, name, QtCore.Qt.FindChildrenRecursively)
            else:
                c = w.findChildren(cls, options=QtCore.Qt.FindChildrenRecursively)
            found.extend(c)

        uniq = []
        seen = set()
        for x in found:
            key = int(x.winId()) if hasattr(x, "winId") else id(x)
            if key in seen:
                continue
            seen.add(key)
            uniq.append(x)
        return uniq

    def resolve(
        self,
        cls,
        name,
        *,
        root=None,
        required=True,
        allow_multiple=False,
        prefer_visible=True,
        debug_context=False,
    ):
        if not issubclass(cls, QtCore.QObject):
            raise ValueError("cls must be a Qt QObject subclass")

        cands = self._candidates(cls, name=name, root=root)

        if len(cands) == 0:
            msg = f"Widget '{name}' ({cls.__name__}) not found."
            if debug_context:
                msg += f" root={_qname(self.root) if self.root else None}"
            if required:
                raise WidgetResolveError(msg)
            self._log("warning", msg)
            return None

        if len(cands) > 1 and not allow_multiple:
            details = []
            for i, w in enumerate(cands[:10]):
                details.append(
                    f"  [{i}] {_qname(w)} name='{w.objectName()}' visible={getattr(w,'isVisible',lambda:None)()} "
                    f"enabled={getattr(w,'isEnabled',lambda:None)()} path={_path_to_root(w)}"
                )
            msg = (
                f"objectName collision for '{name}' ({cls.__name__}): {len(cands)} matches.\n"
                + "\n".join(details)
            )
            raise WidgetResolveError(msg)

        if len(cands) == 1:
            return cands[0]

        if prefer_visible:
            vis = [w for w in cands if getattr(w, "isVisible", lambda: False)()]
            if len(vis) == 1:
                return vis[0]
            en = [w for w in cands if getattr(w, "isEnabled", lambda: False)()]
            if len(en) == 1:
                return en[0]
            self._log("warning", f"Multiple matches for '{name}', selecting first after visibility heuristic.")
            return (vis or en or cands)[0]

        self._log("warning", f"Multiple matches for '{name}', selecting first (no heuristic).")
        return cands[0]

    def try_resolve(self, cls, name, **kwargs):
        try:
            return self.resolve(cls, name, required=False, **kwargs)
        except WidgetResolveError as e:
            self._log("warning", str(e))
            return None

    def resolve_later(
        self,
        cls,
        name,
        callback,
        *,
        root=None,
        interval_ms=100,
        timeout_ms=3000,
        allow_multiple=False,
        prefer_visible=True,
        debug_context=False,
    ):
        start = QtCore.QElapsedTimer()
        start.start()

        def _tick():
            try:
                w = self.resolve(
                    cls,
                    name,
                    root=root,
                    required=True,
                    allow_multiple=allow_multiple,
                    prefer_visible=prefer_visible,
                    debug_context=debug_context,
                )
                callback(w, None)
            except WidgetResolveError as e:
                if start.elapsed() >= timeout_ms:
                    callback(None, e)
                else:
                    QtCore.QTimer.singleShot(interval_ms, _tick)

        _tick()

