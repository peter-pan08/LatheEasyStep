"""Contract checks between the extracted UI lifecycle and its handler."""

import ast
import inspect

import lathe_easystep.ui_lifecycle as ui_lifecycle
from lathe_easystep_handler import HandlerClass


def test_direct_private_handler_calls_exist_on_handler_class():
    """Catch stale lifecycle calls when handler methods are moved or removed."""
    tree = ast.parse(inspect.getsource(ui_lifecycle))
    called_methods = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "handler"
        and node.func.attr.startswith("_")
    }

    missing = sorted(name for name in called_methods if not hasattr(HandlerClass, name))
    assert missing == []
