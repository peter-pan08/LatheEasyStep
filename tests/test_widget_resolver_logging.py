from lathe_easystep.widget_resolver import WidgetResolver


def test_resolver_logging_without_injected_logger_uses_module_fallback():
    """Realer Embedded-Fund: _log() referenzierte einen undefinierten
    Modul-Logger, sobald ein Lookup nach abgeschlossenem UI-Start warnte."""
    resolver = WidgetResolver(root=None, widgets=None, logger=None)
    resolver._log("warning", "absichtlich fehlendes Testwidget")
