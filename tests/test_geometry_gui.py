from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

PySide6 = pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication

from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
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
    assert panel.collision_summary.text() == "present"
    assert state.doc.data["gameplay_geometry"]["collision"]["shape"]["w"] > 0
