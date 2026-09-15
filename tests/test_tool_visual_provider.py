from dataclasses import asdict

from lathe_easystep.tool_visuals import ToolVisualProvider, ToolVisualRequest
from lathe_easystep.tools import Tool


def _request():
    return ToolVisualRequest(
        family="turning", handed="external", shape_key="C", iso_code="CNMG120408"
    )


def _tool():
    return Tool(
        t=1, p=1, d=8.0, q=3, comment="CNMG 120408", iso_code="CNMG120408",
        iso_size="1204", radius_mm=0.8, kind="turning",
    )


def test_provider_prefers_iso_resource_without_knowing_tool_model(tmp_path):
    image = tmp_path / "cnmg.svg"
    image.write_text("<svg/>", encoding="utf-8")
    provider = ToolVisualProvider(tmp_path, {
        "turning": "generic.png",
        "iso.cnmg120408": "cnmg.svg",
    })

    visual = provider.resolve(_request())

    assert visual.uses_resource is True
    assert visual.matched_key == "iso.cnmg120408"
    assert visual.resource_path == image.resolve()
    assert visual.diagnostic is None


def test_provider_without_matching_resource_selects_existing_procedural_visual():
    visual = ToolVisualProvider().resolve(_request())

    assert visual.source == "procedural"
    assert visual.resource_path is None
    assert visual.diagnostic is None


def test_missing_resource_has_visible_diagnostic_and_safe_fallback(tmp_path):
    visual = ToolVisualProvider(tmp_path, {"turning.external.c": "missing.png"}).resolve(_request())

    assert visual.source == "procedural"
    assert visual.matched_key == "turning.external.c"
    assert "missing" in visual.diagnostic


def test_unsafe_or_unsupported_resource_never_leaves_theme_root(tmp_path):
    unsafe = ToolVisualProvider(tmp_path, {"turning": "../outside.svg"}).resolve(_request())
    unsupported = ToolVisualProvider(tmp_path, {"turning": "tool.exe"}).resolve(_request())

    assert unsafe.source == unsupported.source == "procedural"
    assert "leaves theme root" in unsafe.diagnostic
    assert "unsupported" in unsupported.diagnostic


def test_changing_visual_set_cannot_mutate_tool_data(tmp_path):
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    tool = _tool()
    before = asdict(tool)

    visual_a = ToolVisualProvider(tmp_path, {"turning": first.name}).resolve(_request())
    visual_b = ToolVisualProvider(tmp_path, {"turning": second.name}).resolve(_request())

    assert visual_a.resource_path != visual_b.resource_path
    assert asdict(tool) == before
