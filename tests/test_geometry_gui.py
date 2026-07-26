from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

PySide6 = pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication

from ambition_sprite2d_renderer.authoring.gameplay_geometry import (
    entry_shapes,
    hurtbox_clip_binding,
    hurtbox_entry,
    hurtbox_source,
)
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.gui.canvas import CanvasWidget
from ambition_sprite2d_renderer.gui.geometry_panel import GeometryPanel
from ambition_sprite2d_renderer.gui.state import EditorState


def _app():
    return QApplication.instance() or QApplication([])


def test_geometry_panel_starts_missing_and_generates_collision():
    _app()
    state = EditorState(RigDocument.new_empty("gui_geometry"))
    panel = GeometryPanel(state)
    assert panel.collision_summary.text() == "missing"
    assert "0 /" in panel.hit_summary.text()
    panel._generate_collision()
    assert "global shape" in panel.collision_summary.text()
    assert state.doc.data["gameplay_geometry"]["collision"]["shapes"][0]["w"] > 0


def test_panel_can_add_and_convert_non_rectangular_shapes():
    _app()
    state = EditorState(RigDocument.new_empty("gui_geometry_shapes"))
    panel = GeometryPanel(state)
    state.set_geometry_selection("hurtbox", 0)
    panel.add_kind.setCurrentText("capsule")
    panel._add_shape()
    shapes = entry_shapes(hurtbox_entry(state.doc, state.clip_name))
    assert shapes[0]["kind"] == "capsule"
    assert hurtbox_clip_binding(state.doc, state.clip_name)["profile"] == "default"
    panel._convert_selected_shape("polygon")
    assert shapes[0]["kind"] == "polygon"
    assert len(shapes[0]["points"]) == 4


def test_canvas_drag_moves_shape_and_polygon_vertex():
    _app()
    state = EditorState(RigDocument.new_empty("gui_geometry_drag"))
    panel = GeometryPanel(state)
    state.set_geometry_selection("hurtbox", 0)
    panel.add_kind.setCurrentText("polygon")
    panel._add_shape()
    canvas = CanvasWidget(state)
    shape = entry_shapes(hurtbox_entry(state.doc, state.clip_name))[0]
    original = [list(point) for point in shape["points"]]
    canvas._geometry_drag = {
        "layer": "hurtbox",
        "index": 0,
        "handle": "body",
        "start": (0.0, 0.0),
        "shape": __import__("copy").deepcopy(shape),
    }
    canvas._drag_geometry_to((5.0, 7.0))
    assert shape["points"][0] == [original[0][0] + 5.0, original[0][1] + 7.0]

    canvas._geometry_drag = {
        "layer": "hurtbox",
        "index": 0,
        "handle": "vertex:0",
        "start": (0.0, 0.0),
        "shape": __import__("copy").deepcopy(shape),
    }
    canvas._drag_geometry_to((11.0, 13.0))
    assert shape["points"][0] == [11.0, 13.0]


def test_panel_local_override_detaches_current_clip_from_profile():
    _app()
    doc = RigDocument.new_empty("gui_geometry_profiles")
    # Add another clip so the generated/shared profile has more than one user.
    doc.data["clips"]["walk"] = dict(doc.data["clips"]["idle"])
    state = EditorState(doc)
    panel = GeometryPanel(state)
    panel._generate_hurt()
    idle_profile = hurtbox_clip_binding(doc, "idle")["profile"]
    walk_profile = hurtbox_clip_binding(doc, "walk")["profile"]
    assert idle_profile == walk_profile
    assert "Shared profile" in panel.hurt_source.text()

    panel._make_hurtbox_override()
    assert hurtbox_source(doc, "idle").kind == "override"
    assert "Local override" in panel.hurt_source.text()
    assert hurtbox_source(doc, "walk").kind == "profile"

    panel._remove_hurtbox_override()
    assert hurtbox_source(doc, "idle").kind == "profile"
