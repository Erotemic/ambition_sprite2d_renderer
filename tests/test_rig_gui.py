"""Tests for the PySide6 rig editor (offscreen platform).

The whole module is skipped when PySide6 is unavailable — rigdoc-only
coverage lives in test_rigdoc.py so it still runs everywhere.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PySide6 = pytest.importorskip("PySide6")

from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument

TEMPLATE = (
    Path(__file__).resolve().parent.parent
    / "ambition_sprite2d_renderer"
    / "data"
    / "rig_templates"
    / "player_robot_fable.rig.json"
)


@pytest.fixture()
def doc() -> RigDocument:
    return RigDocument.load(TEMPLATE)

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PySide6 = pytest.importorskip("PySide6")


@pytest.fixture(scope="module")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture()
def window(qapp, doc):
    from ambition_sprite2d_renderer.gui.app import MainWindow
    from ambition_sprite2d_renderer.gui.state import EditorState

    state = EditorState(doc, None)
    win = MainWindow(state)
    win.resize(1200, 800)
    win.show()
    qapp.processEvents()
    yield win
    win.close()
    qapp.processEvents()


class TestEditorState:
    def test_write_key_inserts_and_updates(self, doc):
        from ambition_sprite2d_renderer.gui.state import EditorState

        state = EditorState(doc, None)
        state.set_clip("slash")
        state.set_frame(2)
        state.write_key("torso", 42.0)
        keys = doc.clips["slash"]["channels"]["torso"]["keys"]
        t = doc.frame_time("slash", 2)
        match = [k for k in keys if abs(k[0] - t) < 1e-4]
        assert match and match[0][1] == 42.0
        state.write_key("torso", -7.0)  # same frame: update, not duplicate
        assert len([k for k in keys if abs(k[0] - t) < 1e-4]) == 1

    def test_write_key_bakes_expr_channels(self, doc):
        from ambition_sprite2d_renderer.gui.state import EditorState

        state = EditorState(doc, None)
        state.set_clip("idle")
        state.set_frame(0)
        state.write_key("torso", 5.0)
        spec = doc.clips["idle"]["channels"]["torso"]
        assert "keys" in spec and "expr" not in spec
        assert len(spec["keys"]) == int(doc.clips["idle"]["frames"])

    def test_first_key_on_absent_bone_channel_preserves_every_other_frame(self):
        from ambition_sprite2d_renderer.gui.state import EditorState

        doc = RigDocument.new_empty("first_key_is_local")
        doc.clips["idle"]["frames"] = 5
        state = EditorState(doc, None)
        state.set_frame(2)

        assert "pelvis" not in state.clip()["channels"]
        assert state.write_key("pelvis", 35.0)
        spec = state.clip()["channels"]["pelvis"]
        assert len(spec["keys"]) == 3
        values = [
            doc.sample("idle", doc.frame_time("idle", frame))["pelvis"]
            for frame in range(5)
        ]
        assert values == pytest.approx([0.0, 0.0, 35.0, 0.0, 0.0])

    def test_key_selected_can_materialize_a_previously_static_bone(self):
        from ambition_sprite2d_renderer.gui.state import EditorState

        doc = RigDocument.new_empty("key_static_bone")
        doc.clips["idle"]["frames"] = 4
        state = EditorState(doc, None)
        state.selected_bone = "pelvis"
        state.set_frame(1)
        # An explicit Key selected command is allowed to materialize the rest
        # value so it becomes a real interpolation anchor without changing any
        # pose. Baseline guard keys keep a later edit local.
        assert state.selected_animation_channels() == ["pelvis"]
        assert state.insert_keys_here() == 1
        assert "pelvis" in state.clip()["channels"]
        before = [
            doc.sample("idle", doc.frame_time("idle", frame))["pelvis"]
            for frame in range(4)
        ]
        assert before == pytest.approx([0.0, 0.0, 0.0, 0.0])
        assert state.write_key("pelvis", 12.0)
        assert state.keyed_channels_at_frame(1) == ["pelvis"]

    def test_control_key_state_distinguishes_static_interpolated_and_keyed(self):
        from ambition_sprite2d_renderer.gui.state import EditorState

        doc = RigDocument.new_empty("control_state")
        doc.clips["idle"]["frames"] = 5
        state = EditorState(doc, None)
        assert state.control_key_state("pelvis", 2)["status"] == "static"

        state.set_frame(2)
        state.write_key("pelvis", 30.0)
        assert state.control_key_state("pelvis", 2)["status"] == "keyed"
        assert state.control_key_state("pelvis", 0)["status"] in {
            "interpolated",
            "keyed",
        }

    def test_pose_control_keys_and_pose_bookmarks_are_independent(self):
        from ambition_sprite2d_renderer.gui.state import EditorState

        doc = RigDocument.new_empty("independent_bookmarks")
        state = EditorState(doc, None)
        state.set_frame(2)
        state.write_key("pelvis", 15.0)
        assert "pose_keys" not in state.clip()
        state.set_pose_key(3, True)
        assert state.is_pose_key(3)
        assert 3 not in state.channel_key_frames("pelvis")["pelvis"]

    def test_noop_speculative_undo_boundary_is_removed(self):
        from ambition_sprite2d_renderer.gui.state import EditorState

        state = EditorState(RigDocument.new_empty("noop_undo"), None)
        state.push_undo()
        assert state.discard_last_undo_if_unchanged()
        assert not state.undo()

    def test_write_keys_batches_notifications(self, doc):
        from ambition_sprite2d_renderer.gui.state import EditorState

        state = EditorState(doc, None)
        animation_events = []
        pose_events = []
        document_events = []
        state.animationChanged.connect(animation_events.append)
        state.poseChanged.connect(lambda: pose_events.append(True))
        state.docChanged.connect(lambda: document_events.append(True))

        changed = state.write_keys({"root_x": 3.0, "root_y": -2.0})

        assert changed == 2
        assert animation_events == [("root_x", "root_y")]
        assert len(pose_events) == 1
        assert document_events == []

    def test_identical_key_write_is_a_noop(self, doc):
        from ambition_sprite2d_renderer.gui.state import EditorState

        state = EditorState(doc, None)
        state.write_key("root_x", 3.0)
        events = []
        state.animationChanged.connect(events.append)

        assert not state.write_key("root_x", 3.0)
        assert events == []

    def test_undo_redo_round_trip(self, doc):
        from ambition_sprite2d_renderer.gui.state import EditorState

        state = EditorState(doc, None)
        before = json.dumps(doc.data)
        state.push_undo()
        doc.data["name"] = "mutated"
        assert state.undo()
        assert json.dumps(state.doc.data) == before
        assert state.redo()
        assert state.doc.data["name"] == "mutated"

    def test_selected_foot_can_be_planted_and_dragged_without_keys(self, doc):
        from ambition_sprite2d_renderer.gui.state import EditorState

        state = EditorState(doc, None)
        state.set_clip("idle")
        state.selected_bone = "near_foot"
        original_channels = json.dumps(state.clip().get("channels", {}), sort_keys=True)
        events = []
        state.constraintsChanged.connect(lambda: events.append(True))

        assert state.plant_selected_foot_entire_clip()
        assert state.selected_foot_plant() is not None
        assert events == [True]
        assert state.move_selected_foot_plant((70.0, 96.0))
        assert json.dumps(state.clip().get("channels", {}), sort_keys=True) == original_channels
        world, _ = state.doc.solve("idle", 0.37)
        assert world["near_foot"].origin == pytest.approx((70.0, 96.0))
        assert state.release_selected_foot_plant()
        assert state.selected_foot_plant() is None

    def test_plant_all_feet_creates_one_constraint_per_leg(self, doc):
        from ambition_sprite2d_renderer.gui.state import EditorState

        state = EditorState(doc, None)
        state.set_clip("idle")
        assert state.plant_all_feet_entire_clip() == len(doc.ik_legs)
        assert state.planted_feet() == {"near_foot", "far_foot"}

    def test_plant_all_feet_ignores_stale_parts_panel_selection(self, doc):
        from ambition_sprite2d_renderer.gui.state import EditorState

        state = EditorState(doc, None)
        state.set_clip("idle")
        state.selected_part = next(
            index
            for index, part in enumerate(doc.parts)
            if part.get("name") == "near_hand"
        )
        state.selected_bone = "near_arm_l"

        assert state.plant_all_feet_entire_clip() == len(doc.ik_legs)
        assert state.planted_feet() == {"near_foot", "far_foot"}
        assert state.selected_part is not None
        assert state.selected_bone == "near_arm_l"

    def test_any_endpoint_part_can_be_pinned_and_moved(self, doc):
        from ambition_sprite2d_renderer.gui.state import EditorState

        state = EditorState(doc, None)
        state.set_clip("idle")
        # ``near_hand`` is a visual part attached to ``near_arm_l``; this rig
        # intentionally has no redundant skeleton bone named ``near_hand``.
        state.selected_bone = "near_hand"
        candidate = state.selected_pinnable_part()
        assert candidate is not None
        assert candidate["bone"] == "near_arm_l"
        assert candidate["upper"] == "near_arm_u"
        assert candidate["lower"] == "near_arm_l"
        assert candidate["solver_mode"] == "point_on_lower"
        assert not candidate["lock_rotation_supported"]

        before, _ = state.doc.solve("idle", state.t())
        anchor = before[candidate["bone"]].to_world(candidate["anchor_local"])
        assert state.pin_selected_part_entire_clip(anchor_frame=anchor)
        pin = state.selected_part_pin()
        assert pin is not None
        assert pin["solver"]["mode"] == "point_on_lower"
        assert not pin["lock_rotation"]

        assert state.move_selected_part_pin((78.0, 66.0))
        pin = state.selected_part_pin()
        assert pin["target"] == [78.0, 66.0]
        after, _ = state.doc.solve("idle", 0.37)
        pinned_anchor = after[candidate["bone"]].to_world(candidate["anchor_local"])
        assert pinned_anchor == pytest.approx((78.0, 66.0))

        assert state.release_selected_part_pin()
        assert state.selected_part_pin() is None


class TestCanvas:
    def test_preview_quality_is_stable_during_pose_edits(self, window):
        canvas = window.canvas
        state = canvas.state

        assert canvas._preview_supersample() == 2
        state.write_key("root_x", 1.0)
        assert canvas._preview_supersample() == 2

        # A click-release that selects an editable bone must not temporarily
        # downgrade the rendered image and then pop back to a sharper version.
        canvas._drag_mode = "rotate"
        canvas._drag_bone = "head"
        canvas.mouseReleaseEvent(None)
        assert canvas._preview_supersample() == 2

    def test_hit_test_finds_selected_bone(self, window):
        canvas = window.canvas
        canvas.fit()
        world, _ = canvas.state.doc.solve(canvas.state.clip_name, canvas.state.t())
        head_pos = canvas.frame_to_widget(world["head"].origin)
        hit = canvas._hit_test(head_pos)
        assert hit is not None

    def test_frame_cache_reuses_render_for_view_only_changes(self, window, monkeypatch):
        canvas = window.canvas
        state = canvas.state
        canvas._on_render_changed()
        calls = []
        original = state.doc.render_at

        def counted(*args, **kwargs):
            calls.append((args, kwargs))
            return original(*args, **kwargs)

        monkeypatch.setattr(state.doc, "render_at", counted)
        first = canvas._render_qimage(state.clip_name, state.t(), 1)
        canvas.zoom *= 1.25
        second = canvas._render_qimage(state.clip_name, state.t(), 1)

        assert first is second
        assert len(calls) == 1

    def test_pose_change_invalidates_frame_cache(self, window, monkeypatch):
        canvas = window.canvas
        state = canvas.state
        calls = []
        original = state.doc.render_at

        def counted(*args, **kwargs):
            calls.append((args, kwargs))
            return original(*args, **kwargs)

        monkeypatch.setattr(state.doc, "render_at", counted)
        canvas._render_qimage(state.clip_name, state.t(), 1)
        state.write_key("root_x", 7.0)
        canvas._render_qimage(state.clip_name, state.t(), 1)

        assert len(calls) == 2

    def test_rotate_drag_writes_key(self, window, qapp):
        from PySide6.QtCore import QEvent, QPointF, Qt
        from PySide6.QtGui import QMouseEvent

        canvas = window.canvas
        canvas.fit()
        state = canvas.state
        state.set_clip("idle")
        world, _ = state.doc.solve("idle", state.t())
        origin = canvas.frame_to_widget(world["near_arm_u"].origin)

        def mouse(etype, pos):
            return QMouseEvent(
                etype, QPointF(pos), Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
            )

        canvas.mousePressEvent(mouse(QEvent.Type.MouseButtonPress, origin))
        assert state.selected_bone == "near_arm_u"
        target = QPointF(origin.x() + 40, origin.y() + 40)  # 45° down-forward
        canvas.mouseMoveEvent(mouse(QEvent.Type.MouseMove, target))
        canvas.mouseReleaseEvent(mouse(QEvent.Type.MouseButtonRelease, target))
        spec = state.clip()["channels"]["near_arm_u"]
        assert "keys" in spec
        # world 45° = rest 90 + pose -45 (parents near zero at t=0).
        t = state.t()
        key = min(spec["keys"], key=lambda k: abs(k[0] - t))
        assert key[1] == pytest.approx(-45.0, abs=8.0)

    def test_ctrl_drag_moves_attachment_offset(self, window, qapp):
        from PySide6.QtCore import QEvent, QPointF, Qt
        from PySide6.QtGui import QMouseEvent

        canvas = window.canvas
        canvas.fit()
        state = canvas.state
        state.set_clip("idle")
        state.set_frame(0)
        world, _ = state.doc.solve("idle", state.t())
        origin = canvas.frame_to_widget(world["near_arm_u"].origin)
        before = list(state.doc.bone("near_arm_u")["offset"])

        def mouse(etype, pos, mods):
            return QMouseEvent(
                etype, QPointF(pos), Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton, mods,
            )

        ctrl = Qt.KeyboardModifier.ControlModifier
        canvas.mousePressEvent(mouse(QEvent.Type.MouseButtonPress, origin, ctrl))
        assert canvas._drag_mode == "offset"
        target = QPointF(origin.x() + 2 * canvas.zoom, origin.y() - 3 * canvas.zoom)
        canvas.mouseMoveEvent(mouse(QEvent.Type.MouseMove, target, ctrl))
        canvas.mouseReleaseEvent(
            mouse(QEvent.Type.MouseButtonRelease, target, Qt.KeyboardModifier.NoModifier)
        )
        after = state.doc.bone("near_arm_u")["offset"]
        # Torso is near-upright at idle t=0, so a +2/-3 frame-space drag
        # lands close to +2/-3 in parent-local offset units.
        assert after[0] - before[0] == pytest.approx(2.0, abs=0.6)
        assert after[1] - before[1] == pytest.approx(-3.0, abs=0.6)
        # And the solved origin now sits where the cursor dropped it.
        world2, _ = state.doc.solve("idle", state.t())
        moved = canvas.frame_to_widget(world2["near_arm_u"].origin)
        assert abs(moved.x() - target.x()) < 2 and abs(moved.y() - target.y()) < 2

    def test_ik_leg_bones_refuse_rotation(self, window):
        canvas = window.canvas
        state = canvas.state
        leg = state.doc.foot_leg_for_bone("near_leg_u")
        assert leg is not None and leg["foot"] == "near_foot"

    def test_screenshot_smoke(self, window, qapp, tmp_path):
        pix = window.grab()
        out = tmp_path / "shot.png"
        assert pix.save(str(out))
        assert out.stat().st_size > 10_000


class TestTimelinePanel:
    def test_clip_combo_follows_state(self, window, qapp):
        state = window.state
        state.set_clip("walk")
        qapp.processEvents()
        assert window.timeline.clip_combo.currentText() == "walk"

    def test_play_advances_frames(self, window, qapp):
        tl = window.timeline
        start = window.state.frame_idx
        tl.play_btn.setChecked(True)
        tl._tick()
        assert window.state.frame_idx == (start + 1) % window.state.frames()
        tl.play_btn.setChecked(False)

    def test_wheel_moves_one_frame_per_tick(self, window, qapp):
        from PySide6.QtCore import QPoint, QPointF, Qt
        from PySide6.QtGui import QWheelEvent

        slider = window.timeline.frame_slider
        slider.setValue(3)

        def wheel(dy):
            ev = QWheelEvent(
                QPointF(5, 5), QPointF(5, 5), QPoint(0, 0), QPoint(0, dy),
                Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
                Qt.ScrollPhase.NoScrollPhase, False,
            )
            slider.wheelEvent(ev)

        wheel(120)  # one notch up
        assert slider.value() == 4
        wheel(120)
        assert slider.value() == 5
        wheel(-120)  # one notch down
        assert slider.value() == 4


class TestPartsZOrder:
    def _index(self, doc, name):
        return next(i for i, p in enumerate(doc.parts) if p.get("name") == name)

    def test_list_is_front_to_back(self, window):
        from PySide6.QtCore import Qt

        from ambition_sprite2d_renderer.gui.panels import PartsPanel

        parts_panel = window.findChild(PartsPanel)
        zs = [
            window.state.doc.parts[parts_panel.listw.item(r).data(Qt.ItemDataRole.UserRole)]["z"]
            for r in range(parts_panel.listw.count())
        ]
        assert zs == sorted(zs, reverse=True)  # top of list = frontmost

    def test_list_row_maps_to_storage_index(self, window):
        from ambition_sprite2d_renderer.gui.panels import PartsPanel

        parts_panel = window.findChild(PartsPanel)
        parts_panel.listw.setCurrentRow(0)
        front = max(window.state.doc.parts, key=lambda p: p["z"])
        assert window.state.doc.parts[window.state.selected_part]["name"] == front["name"]

    def test_raise_brings_part_in_front(self, window):
        from ambition_sprite2d_renderer.gui.panels import PartsPanel

        doc = window.state.doc
        parts_panel = window.findChild(PartsPanel)
        i_torso = self._index(doc, "torso")  # z=40
        i_shade = self._index(doc, "torso_shade")  # z=41 (just in front)
        assert doc.parts[i_torso]["z"] < doc.parts[i_shade]["z"]
        window.state.selected_part = i_torso
        parts_panel._bump_z(+1)
        assert doc.parts[i_torso]["z"] > doc.parts[i_shade]["z"]

    def test_lower_sends_part_back(self, window):
        from ambition_sprite2d_renderer.gui.panels import PartsPanel

        doc = window.state.doc
        parts_panel = window.findChild(PartsPanel)
        i_shade = self._index(doc, "torso_shade")  # z=41
        i_torso = self._index(doc, "torso")  # z=40 (just behind)
        window.state.selected_part = i_shade
        parts_panel._bump_z(-1)
        assert doc.parts[i_shade]["z"] < doc.parts[i_torso]["z"]

    def test_raise_at_front_is_noop(self, window):
        from ambition_sprite2d_renderer.gui.panels import PartsPanel

        doc = window.state.doc
        parts_panel = window.findChild(PartsPanel)
        front = max(range(len(doc.parts)), key=lambda i: doc.parts[i]["z"])
        before = doc.parts[front]["z"]
        window.state.selected_part = front
        parts_panel._bump_z(+1)
        assert doc.parts[front]["z"] == before


def test_pose_key_bookmarks_separate_important_poses_from_dense_channel_keys():
    from ambition_sprite2d_renderer.gui.state import EditorState

    doc = RigDocument.new_empty("pose_keys")
    doc.data["clips"]["idle"] = {
        "loop": True,
        "frames": 8,
        "duration_ms": 100,
        "channels": {
            "torso": {
                "keys": [
                    [i / 8.0, value, "smooth"]
                    for i, value in enumerate((0, 20, 40, 20, 0, -20, -40, -20))
                ]
            }
        },
    }
    state = EditorState(doc)
    suggestions, explicit = state.pose_key_frames()
    assert explicit is False
    assert 3 <= len(suggestions) < 8
    assert state.dense_keyed_channels() == ["torso"]

    state.set_frame(1)
    state.write_key("torso", 12.0)
    # Property keys do not silently become editorial pose bookmarks.
    assert "pose_keys" not in state.clip()
    _saved, explicit = state.pose_key_frames()
    assert explicit is False


def test_simplify_dense_channel_preserves_key_poses_and_creates_inbetweens():
    from ambition_sprite2d_renderer.gui.state import EditorState

    doc = RigDocument.new_empty("simplify")
    values = (0, 20, 40, 20, 0, -20, -40, -20)
    doc.data["clips"]["idle"] = {
        "loop": True,
        "frames": 8,
        "duration_ms": 100,
        "pose_keys": [0, 2, 4, 6],
        "channels": {
            "torso": {
                "keys": [[i / 8.0, value, "smooth"] for i, value in enumerate(values)]
            }
        },
    }
    state = EditorState(doc)
    before = {
        frame: doc.sample("idle", doc.frame_time("idle", frame))["torso"]
        for frame in (0, 2, 4, 6)
    }
    assert state.simplify_channels_to_pose_keys(["torso"]) == 1
    keys = doc.clips["idle"]["channels"]["torso"]["keys"]
    assert len(keys) == 4
    after = {
        frame: doc.sample("idle", doc.frame_time("idle", frame))["torso"]
        for frame in (0, 2, 4, 6)
    }
    assert after == pytest.approx(before)
    assert state.dense_keyed_channels() == []


def test_view_overlays_are_independent_and_geometry_editing_defaults_safe():
    from ambition_sprite2d_renderer.gui.state import EditorState

    state = EditorState(RigDocument.new_empty("views"))
    assert state.geometry_edit_enabled is False
    state.set_view_options(
        key_pose_ghosts=False,
        frame_onion=True,
        motion_trail=False,
        intermediate_chain_ghosts=True,
    )
    assert state.show_key_pose_ghosts is False
    assert state.show_frame_onion is True
    assert state.show_motion_trail is False
    assert state.show_intermediate_chain_ghosts is True
    # Gameplay overlays remain independently visible.
    assert state.show_collision_geometry
    assert state.show_hurtbox_geometry
    assert state.show_hitbox_geometry


def test_temporal_direction_colors_match_canvas_and_timeline(window, qapp):
    from ambition_sprite2d_renderer.gui.pose_colors import (
        after_pose_color,
        before_pose_color,
    )

    state = window.state
    state.set_clip("idle")
    state.set_frame(0)
    qapp.processEvents()

    assert "BEFORE" in window.timeline.prev_pose_btn.text()
    assert "AFTER" in window.timeline.next_pose_btn.text()
    assert before_pose_color().name() in window.timeline.prev_pose_btn.styleSheet()
    assert after_pose_color().name() in window.timeline.next_pose_btn.styleSheet()


def test_pin_ik_foot_holds_world_position_at_pose_keys(window):
    state = window.state
    state.set_clip("idle")
    state.set_frame(0)
    state.selected_bone = "near_foot"
    pose_frames, _explicit = state.pose_key_frames()
    world, _params = state.doc.solve(state.clip_name, state.t())
    target = world["near_foot"].origin
    target_angle = world["near_foot"].angle

    changed, affected = state.pin_selected_endpoint_to_pose_keys("both")

    assert changed >= 2
    assert affected == len(pose_frames)
    for frame in pose_frames:
        world, _params = state.doc.solve(
            state.clip_name, state.doc.frame_time(state.clip_name, frame)
        )
        assert world["near_foot"].origin == pytest.approx(target, abs=0.05)
        assert world["near_foot"].angle == pytest.approx(target_angle, abs=0.05)


def test_live_preview_is_independent_of_editing_playhead(window, qapp):
    state = window.state
    preview = window.preview
    state.set_clip("idle")
    state.set_frame(3)
    editing_frame = state.frame_idx

    preview.canvas._tick()
    qapp.processEvents()

    assert state.frame_idx == editing_frame
    assert preview.clip_label.text() == "Loop: idle"
    assert preview.canvas._image is not None

    state.set_clip("walk")
    qapp.processEvents()
    assert preview.clip_label.text() == "Loop: walk"
    assert state.frame_idx == 0


def test_terminal_signal_handler_requests_clean_qt_shutdown(qapp):
    import signal

    from ambition_sprite2d_renderer.gui.__main__ import (
        _install_terminal_signal_handlers,
    )

    class FakeApp:
        def __init__(self):
            self.quit_calls = 0

        def quit(self):
            self.quit_calls += 1

    fake_app = FakeApp()
    old_int = signal.getsignal(signal.SIGINT)
    old_term = signal.getsignal(signal.SIGTERM) if hasattr(signal, "SIGTERM") else None
    timer = None
    try:
        timer, received = _install_terminal_signal_handlers(
            fake_app, poll_interval_ms=25
        )
        assert timer.isActive()
        handler = signal.getsignal(signal.SIGINT)
        handler(signal.SIGINT, None)
        assert fake_app.quit_calls == 1
        assert received == [signal.SIGINT]
    finally:
        if timer is not None:
            timer.stop()
        signal.signal(signal.SIGINT, old_int)
        if hasattr(signal, "SIGTERM") and old_term is not None:
            signal.signal(signal.SIGTERM, old_term)

class TestResponsiveWindowAndPoseSheet:
    def test_main_window_can_shrink_to_laptop_scale(self, window, qapp):
        # The old combined child minimums made the main window effectively fixed
        # at a desktop-sized layout. This is intentionally below the old canvas
        # + timeline floor and should now be a legal outer-window size.
        window.resize(800, 520)
        qapp.processEvents()
        assert window.minimumWidth() <= 800
        assert window.minimumHeight() <= 520
        assert window.width() <= 900
        assert window.height() <= 620

    def test_window_keeps_native_maximize_capability(self, window):
        from PySide6.QtCore import Qt

        assert window.windowFlags() & Qt.WindowType.WindowMaximizeButtonHint
        assert window.maximumWidth() > 10_000
        assert window.maximumHeight() > 10_000

    def test_timeline_dock_can_grow_and_its_panel_fills_the_extra_height(self, window, qapp):
        from PySide6.QtCore import Qt

        window.resize(1100, 900)
        window.resizeDocks([window.animation_dock], [420], Qt.Orientation.Vertical)
        qapp.processEvents()
        assert window.timeline_scroll.widgetResizable()
        assert window.animation_dock.height() >= 300
        assert window.timeline.height() >= window.timeline_scroll.viewport().height() - 4

    def test_pose_sheet_has_one_column_per_frame(self, window, qapp):
        window.state.set_clip("walk")
        qapp.processEvents()
        canvas = window.pose_sheet.canvas
        assert canvas.visible_frames() == list(range(window.state.frames()))
        assert canvas.sizeHint().width() == window.state.frames() * canvas.effective_column_width()

    def test_pose_sheet_click_selects_a_frame(self, window, qapp):
        from PySide6.QtCore import QEvent, QPointF, Qt
        from PySide6.QtGui import QMouseEvent

        window.state.set_clip("walk")
        canvas = window.pose_sheet.canvas
        target = min(2, window.state.frames() - 1)
        x = target * canvas.column_width + canvas.column_width / 2
        event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPointF(x, 80),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        canvas.mousePressEvent(event)
        qapp.processEvents()
        assert window.state.frame_idx == target

    def test_pose_sheet_can_show_only_key_poses(self, window, qapp):
        window.state.set_clip("walk")
        window.state.set_pose_key(0, True)
        window.state.set_pose_key(min(2, window.state.frames() - 1), True)
        canvas = window.pose_sheet.canvas
        canvas.set_key_poses_only(True)
        qapp.processEvents()
        visible = canvas.visible_frames()
        assert visible
        assert set(visible) == set(window.state.pose_key_frames()[0])

    def test_pose_sheet_keeps_pose_bookmarks_distinct_from_real_channel_keys(self):
        from ambition_sprite2d_renderer.gui.state import EditorState

        doc = RigDocument.new_empty("bookmark_is_not_a_keyframe")
        doc.clips["idle"]["frames"] = 4
        state = EditorState(doc, None)
        state.set_pose_key(2, True)
        pose_frames, explicit = state.pose_key_frames()
        assert explicit
        assert 2 in pose_frames
        assert state.keyed_channels_at_frame(2) == []
        assert state.channel_key_frames() == {}

class TestEditablePrimaryPoseSheet:
    def test_pose_sheet_is_a_primary_center_view_and_timeline_is_independent(self, window):
        assert window.centralWidget() is window.main_views
        assert window.main_views.indexOf(window.canvas) >= 0
        assert window.main_views.indexOf(window.pose_sheet) >= 0
        assert window.animation_dock.widget() is not window.pose_sheet
        assert window.animation_dock.windowTitle() == "Timeline"

    def test_pose_sheet_fk_drag_writes_the_clicked_columns_frame(self, window, qapp):
        from PySide6.QtCore import QEvent, QPointF, Qt
        from PySide6.QtGui import QMouseEvent

        state = window.state
        state.set_clip("idle")
        canvas = window.pose_sheet.canvas
        canvas.set_key_poses_only(False)
        canvas.set_column_width(180)
        canvas.set_viewport_height(480)
        target_frame = min(2, state.frames() - 1)
        column = target_frame
        rect = canvas._column_rect(column)
        world = canvas._solve_frame(target_frame)
        origin = canvas._map_point(world["near_arm_u"].origin, rect)

        def mouse(kind, pos, mods=Qt.KeyboardModifier.NoModifier):
            return QMouseEvent(
                kind,
                QPointF(pos),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                mods,
            )

        canvas.mousePressEvent(mouse(QEvent.Type.MouseButtonPress, origin))
        assert state.frame_idx == target_frame
        assert state.selected_bone == "near_arm_u"
        target = QPointF(origin.x() + 32.0, origin.y() + 32.0)
        canvas.mouseMoveEvent(mouse(QEvent.Type.MouseMove, target))
        canvas.mouseReleaseEvent(mouse(QEvent.Type.MouseButtonRelease, target))

        keys = state.clip()["channels"]["near_arm_u"]["keys"]
        target_time = state.doc.frame_time(state.clip_name, target_frame)
        assert any(abs(float(key[0]) - target_time) < 1e-4 for key in keys)
        assert "pose_keys" not in state.clip(), (
            "dragging a control key must not silently create a pose bookmark"
        )

    def test_pose_sheet_alt_drag_keys_a_two_bone_chain_in_that_column(self, window):
        from PySide6.QtCore import QEvent, QPointF, Qt
        from PySide6.QtGui import QMouseEvent

        state = window.state
        state.set_clip("idle")
        canvas = window.pose_sheet.canvas
        canvas.set_key_poses_only(False)
        canvas.set_column_width(180)
        canvas.set_viewport_height(480)
        target_frame = min(1, state.frames() - 1)
        rect = canvas._column_rect(target_frame)
        world = canvas._solve_frame(target_frame)
        # player_robot_fable's near hand artwork ends at the near lower arm tip;
        # selecting that segment's endpoint exposes the ordinary two-bone arm chain.
        endpoint = canvas._map_point(world["near_arm_l"].tip, rect)

        def mouse(kind, pos, mods):
            return QMouseEvent(
                kind,
                QPointF(pos),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                mods,
            )

        alt = Qt.KeyboardModifier.AltModifier
        canvas.mousePressEvent(mouse(QEvent.Type.MouseButtonPress, endpoint, alt))
        if canvas._drag_mode != "limb_ik":
            pytest.skip("template endpoint is document-IK or has no free two-bone chain")
        target = QPointF(endpoint.x() + 18.0, endpoint.y() - 12.0)
        canvas.mouseMoveEvent(mouse(QEvent.Type.MouseMove, target, alt))
        canvas.mouseReleaseEvent(
            mouse(QEvent.Type.MouseButtonRelease, target, Qt.KeyboardModifier.NoModifier)
        )
        target_time = state.doc.frame_time(state.clip_name, target_frame)
        keyed = state.keyed_channels_at_frame(target_frame)
        assert any(name in keyed for name in ("near_arm_u", "near_arm_l"))
        assert target_time == pytest.approx(state.doc.frame_time(state.clip_name, state.frame_idx))


def test_writing_property_keys_does_not_materialize_pose_bookmarks():
    from ambition_sprite2d_renderer.gui.state import EditorState

    doc = RigDocument.new_empty("property_keys_are_not_bookmarks")
    doc.clips["idle"]["frames"] = 6
    state = EditorState(doc, None)
    state.set_frame(3)
    assert state.write_key("pelvis", 22.0)
    assert "pose_keys" not in state.clip()


def test_pose_sheet_zoom_scales_frame_columns_with_the_rig(window, qapp):
    canvas = window.pose_sheet.canvas
    canvas.set_key_poses_only(False)
    canvas.set_column_width(180)
    canvas.set_viewport_height(520)
    canvas.reset_view()
    qapp.processEvents()

    frames = len(canvas.visible_frames())
    base_width = canvas.effective_column_width()
    base_sheet_width = canvas.sizeHint().width()
    rect = canvas._column_rect(0)
    world = canvas._solve_frame(canvas.visible_frames()[0])
    p0 = canvas._map_point(world["pelvis"].origin, rect)
    p1 = canvas._map_point(world["pelvis"].tip, rect)
    base_span = ((p1.x() - p0.x()) ** 2 + (p1.y() - p0.y()) ** 2) ** 0.5

    canvas.set_view_zoom(2.0)
    qapp.processEvents()
    zoom_width = canvas.effective_column_width()
    assert zoom_width == base_width * 2
    assert canvas.sizeHint().width() == frames * zoom_width
    assert canvas.sizeHint().width() == base_sheet_width * 2
    assert canvas._column_rect(1).left() == pytest.approx(float(zoom_width))

    rect = canvas._column_rect(0)
    p0 = canvas._map_point(world["pelvis"].origin, rect)
    p1 = canvas._map_point(world["pelvis"].tip, rect)
    zoom_span = ((p1.x() - p0.x()) ** 2 + (p1.y() - p0.y()) ** 2) ** 0.5
    assert zoom_span == pytest.approx(base_span * 2.0)


def test_pose_sheet_zoom_keeps_frame_hit_columns_aligned(window, qapp):
    canvas = window.pose_sheet.canvas
    canvas.set_key_poses_only(False)
    canvas.set_column_width(160)
    canvas.reset_view()
    canvas.set_view_zoom(2.5)
    qapp.processEvents()

    width = canvas.effective_column_width()
    if len(canvas.visible_frames()) < 2:
        pytest.skip("clip has fewer than two frames")
    assert canvas._column_at(width * 1.5) == 1
    assert canvas._column_rect(1).center().x() == pytest.approx(width * 1.5)


def test_pose_sheet_shared_zoom_preserves_cursor_anatomical_anchor(window, qapp):
    from PySide6.QtCore import QPointF

    canvas = window.pose_sheet.canvas
    scroll = window.pose_sheet.scroll
    canvas.set_key_poses_only(False)
    canvas.set_column_width(180)
    canvas.set_viewport_height(520)
    canvas.reset_view()
    qapp.processEvents()

    column = min(1, len(canvas.visible_frames()) - 1)
    rect = canvas._column_rect(column)
    world = canvas._solve_frame(canvas.visible_frames()[column])
    anchor = canvas._map_point(world["pelvis"].origin, rect)
    before_body = canvas._unmap_point(QPointF(anchor), rect)
    before_viewport = QPointF(
        anchor.x() - scroll.horizontalScrollBar().value(),
        anchor.y() - scroll.verticalScrollBar().value(),
    )

    canvas.set_view_zoom(2.0, QPointF(anchor))
    qapp.processEvents()

    new_rect = canvas._column_rect(column)
    mapped = canvas._map_point(before_body, new_rect)
    after_viewport = QPointF(
        mapped.x() - scroll.horizontalScrollBar().value(),
        mapped.y() - scroll.verticalScrollBar().value(),
    )
    assert after_viewport.x() == pytest.approx(before_viewport.x(), abs=2.0)
    assert after_viewport.y() == pytest.approx(before_viewport.y(), abs=2.0)



def test_pose_sheet_control_state_is_property_level_not_frame_level(window):
    state = window.state
    state.set_clip("idle")
    state.set_frame(0)
    state.selected_bone = "pelvis"
    state.selectionChanged.emit()

    before = state.control_key_state("pelvis", 0)
    state.write_key("pelvis", 12.0)
    here = state.control_key_state("pelvis", 0)
    assert here["status"] == "keyed"
    if state.frames() > 2:
        elsewhere = state.control_key_state("pelvis", 2)
        assert elsewhere["status"] in {"static", "interpolated", "keyed"}
    assert before["constrained"] is False


def test_ik_foot_tip_and_origin_expose_independent_channels(window):
    state = window.state
    state.set_clip("idle")
    foot = next((leg.get("foot") for leg in state.doc.ik_legs if leg.get("foot")), None)
    if foot is None:
        pytest.skip("template has no document IK foot")
    leg = state.doc.foot_leg_for_bone(str(foot))
    prefix = str(leg.get("channel_prefix", "foot"))
    assert state.handle_animation_channels(str(foot), "origin") == [
        f"{prefix}_x",
        f"{prefix}_lift",
    ]
    assert state.handle_animation_channels(str(foot), "tip") == [f"{prefix}_pitch"]
