from copy import deepcopy
from types import SimpleNamespace
import json

import pytest

from lathe_easystep.examples import example_programs, make_program_settings
from lathe_easystep.gcode_program import generate_program_gcode
from lathe_easystep.gcode_safety import emit_approach, append_tool_and_spindle, validate_chuck_segment
from lathe_easystep.gcode_utils import require_positive, get_tool_number
from lathe_easystep.model import OpType, Operation, ProgramModel
from lathe_easystep.persistence import step_data_to_operation
from lathe_easystep.storage import parse_program_payload
from lathe_easystep import ui_persistence


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), "NaN", "inf", "-Infinity", "1e999"])
def test_nonfinite_values_rejected_before_geometry_and_export(value):
    with pytest.raises(ValueError):
        require_positive({"feed": value}, ["feed"], "face")
    with pytest.raises(ValueError):
        step_data_to_operation({"op_type": "face", "params": {"feed": value}})
    with pytest.raises(ValueError):
        parse_program_payload({"version": 1, "header": {"xt": value}}, "test.lse")
    model = ProgramModel(geometry_builders={"face": lambda p: pytest.fail("geometry must not run")})
    with pytest.raises(ValueError):
        model.update_geometry(Operation("face", {"start_x": value}))
    ops, settings = example_programs()["Planen.ngc"]
    ops[-1].params["start_x"] = value
    with pytest.raises(ValueError):
        generate_program_gcode(ops, settings)


@pytest.mark.parametrize("value", [1.5, "2.9", -1, True, "nan", "bad"])
def test_invalid_tool_numbers_are_not_truncated(value):
    with pytest.raises(ValueError):
        get_tool_number({"tool": value})


@pytest.mark.parametrize("filename", list(example_programs()))
def test_generation_is_repeatable_and_leaves_input_unchanged(filename):
    ops, settings = example_programs()[filename]
    before = deepcopy((ops, settings))
    first = generate_program_gcode(ops, settings)
    assert generate_program_gcode(ops, settings) == first
    assert (ops, settings) == before


def test_removed_contour_never_reuses_cached_geometry_and_failure_is_immutable():
    ops, settings = example_programs()["Abdrehen.ngc"]
    ops[-1].params["_primitives"] = [{"type": "line", "p1": (900, 0), "p2": (900, -5)}]
    ops[-1].params["_contour_params"] = {"start_x": 900, "start_z": 0, "segments": [{"x": 900, "z": -5}]}
    # Named contour is the authoritative source, not cached operation geometry.
    assert "X900" not in "\n".join(generate_program_gcode(ops, settings))
    ops.pop(1)
    before = deepcopy((ops, settings))
    with pytest.raises(ValueError):
        generate_program_gcode(ops, settings)
    assert (ops, settings) == before


def _chuck_settings():
    return dict(make_program_settings(), xa=50, xi=0, za=0, zi=-50, xra=5, zra=5,
                chuck_no_go_x_min=0, chuck_no_go_x_max=100, chuck_no_go_z_limit=-40)


def test_chuck_collision_blocks_approach_and_keeps_existing_export(tmp_path):
    settings = _chuck_settings()
    lines = []
    with pytest.raises(ValueError, match="Futter-Sperrzone"):
        emit_approach(lines, 30, -45, settings)
    assert lines == []
    ops, _ = example_programs()["Planen.ngc"]
    ops[-1].params.update(start_x=30, start_z=-45, end_z=-45)
    target = tmp_path / "program.ngc"
    target.write_text("old program")
    handler = SimpleNamespace(_normalized_file_path=str, _build_gcode_lines=lambda: generate_program_gcode(ops, settings))
    with pytest.raises(ValueError, match="Futter-Sperrzone"):
        ui_persistence.write_gcode_file(handler, str(target))
    assert target.read_text() == "old program"


@pytest.mark.parametrize("direction", [1, -1])
def test_chuck_segment_crossing_with_both_endpoints_outside(direction):
    settings = _chuck_settings()
    settings["chuck_no_go_z_limit"] = -40 * direction
    with pytest.raises(ValueError, match="Futter-Sperrzone"):
        validate_chuck_segment(settings, (-10, -45 * direction), (110, -45 * direction))
    validate_chuck_segment(settings, (-10, 5 * direction), (110, 5 * direction))


def test_external_approach_uses_safe_x_until_target_z():
    settings = dict(make_program_settings(), _is_at_safe=True)
    lines = []
    emit_approach(lines, 45, -20, settings)
    assert lines == ["G0 Z-20.000", "G0 X45.000"]


@pytest.mark.parametrize("missing", ["xt", "zt"])
def test_single_tool_requires_complete_toolchange_position(missing):
    ops, settings = example_programs()["Planen.ngc"]
    settings.pop(missing)
    lines = []
    with pytest.raises(ValueError, match="XT/ZT"):
        append_tool_and_spindle(lines, 1, 1000, settings)
    assert lines == []
    with pytest.raises(ValueError, match="XT/ZT"):
        generate_program_gcode(ops, settings)


def _save_handler(path, payload, link=True):
    return SimpleNamespace(
        _normalized_file_path=str, _current_program_path="previous.lse", root_widget=None,
        _find_root_widget=lambda: None, model=SimpleNamespace(operations=[Operation("face", {})]),
        _ensure_step_file_link=lambda *a, **k: link, _build_program_data=lambda: payload,
    )


@pytest.mark.parametrize("failure", ["link", "serialize", "replace"])
def test_failed_program_save_preserves_existing_file_path_and_cleans_temporary(tmp_path, monkeypatch, failure):
    monkeypatch.setattr(ui_persistence.QtCore, "QSettings", lambda: None, raising=False)
    target = tmp_path / "program.lse"
    target.write_text("old program")
    payload = {"version": 1}
    if failure == "serialize":
        payload["cycle"] = payload
    handler = _save_handler(target, payload, link=failure != "link")
    if failure == "replace":
        def fail_replace(*a):
            raise OSError("write error")
        monkeypatch.setattr(ui_persistence.os, "replace", fail_replace)
    with pytest.raises((ValueError, OSError)):
        ui_persistence.write_program_file(handler, str(target))
    assert target.read_text() == "old program"
    assert handler._current_program_path == "previous.lse"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["program.lse"]


def test_successful_program_save_commits_path_and_json(tmp_path, monkeypatch):
    monkeypatch.setattr(ui_persistence.QtCore, "QSettings", lambda: None, raising=False)
    target = tmp_path / "program.lse"
    handler = _save_handler(target, {"version": 1})
    ui_persistence.write_program_file(handler, str(target))
    assert json.loads(target.read_text()) == {"version": 1}
    assert handler._current_program_path == str(target)


@pytest.mark.parametrize("path", [[[1, "bad"]], [[1]], [None], "bad"])
def test_malformed_path_is_not_silently_shortened(path):
    with pytest.raises(ValueError):
        step_data_to_operation({"op_type": "contour", "path": path})


def test_duplicate_contour_names_and_unknown_operations_abort():
    ops, settings = example_programs()["Abdrehen.ngc"]
    ops.insert(1, deepcopy(ops[1]))
    with pytest.raises(ValueError, match="nicht eindeutig"):
        generate_program_gcode(ops, settings)
    with pytest.raises(ValueError, match="Unbekannter Operationstyp"):
        generate_program_gcode([Operation("unsupported", {})], settings)


def test_changed_contour_matches_fresh_save_load_after_previous_export():
    from lathe_easystep.persistence import operation_to_step_data
    ops, settings = example_programs()["Abdrehen.ngc"]
    old = generate_program_gcode(ops, settings)
    ops[1].path[2] = (26., -5.)
    fresh = [step_data_to_operation(operation_to_step_data(op)) for op in ops]
    changed = generate_program_gcode(ops, settings)
    assert changed != old
    assert changed == generate_program_gcode(fresh, settings)


@pytest.mark.parametrize("failure", ["serialize", "replace"])
def test_failed_step_save_preserves_file_and_link(tmp_path, monkeypatch, failure):
    from lathe_easystep.storage import set_step_file_path
    from lathe_easystep.persistence import operation_to_step_data
    target = tmp_path / "new.step.json"
    target.write_text("old")
    op = Operation("face", {"__step_file_path": "previous.step.json"})
    handler = SimpleNamespace(_normalized_file_path=str, _set_step_file_path=set_step_file_path,
                              _operation_to_step_data=operation_to_step_data)
    if failure == "serialize":
        op.params["bad"] = object()
    else:
        monkeypatch.setattr(ui_persistence.os, "replace", lambda *a: (_ for _ in ()).throw(OSError("disk error")))
    with pytest.raises((TypeError, OSError)):
        ui_persistence.write_step_file(handler, op, str(target))
    assert target.read_text() == "old"
    assert op.params["__step_file_path"] == "previous.step.json"
    assert list(tmp_path.iterdir()) == [target]


@pytest.mark.parametrize("case", ["second_write_failure", "unlinked_step"])
def test_save_changes_preserves_dirty_state_when_not_all_steps_saved(tmp_path, monkeypatch, case):
    from lathe_easystep.persistence import operation_to_step_data
    a, b = tmp_path / "a.step.json", tmp_path / "b.step.json"
    b.write_text("old b")
    ops = [Operation("face", {"__step_file_path": str(a)}),
           Operation("face", {"__step_file_path": str(b)})]
    if case == "second_write_failure":
        ops[1].params["bad"] = object()
    else:
        ops[1].params.pop("__step_file_path")
    cleared, errors = [], []
    handler = SimpleNamespace(
        _saving_changes=False, root_widget=None, _find_root_widget=lambda: None,
        _update_selected_operation=lambda **k: None, _log=lambda *a, **k: None,
        model=SimpleNamespace(operations=ops), _dirty_operation_indices={0, 1},
        _current_program_path=None, _current_gcode_path=None, _program_dirty=False,
        _step_file_path=lambda op: op.params.get("__step_file_path"),
        _operation_to_step_data=operation_to_step_data, _remember_dialog_path=lambda *a, **k: None,
        _normalized_file_path=lambda path: path, _clear_dirty_state=lambda: cleared.append(True),
    )
    monkeypatch.setattr(ui_persistence, "_tr",
                        lambda handler, key, **kw: f"{key} {kw}")
    monkeypatch.setattr(ui_persistence.QtWidgets.QMessageBox, "information", lambda *a: None)
    monkeypatch.setattr(ui_persistence.QtWidgets.QMessageBox, "critical", lambda *args: errors.append(args[-1]))
    ui_persistence.handle_save_changes(handler)
    assert a.exists() and b.read_text() == "old b"
    assert handler._dirty_operation_indices == {0, 1} and not cleared
    assert not handler._saving_changes
    if case == "second_write_failure":
        assert len(errors) == 1 and "steps_updated" in errors[0] and "1" in errors[0]
    else:
        assert not errors
