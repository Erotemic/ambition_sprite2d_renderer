"""Timeline panel: clip selection + transport, channel list, key editor.

Channels can be keyframes (table of t / value / ease), an expression of
``t``, or a constant — matching ``rigdoc.sample_channel_spec``.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSlider,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..authoring.rigdoc import EASE_NAMES
from .keyframe_strip import KeyframeStrip
from .pose_colors import after_pose_color, before_pose_color
from .state import EditorState

try:
    from line_profiler import profile
except ImportError:  # Optional developer dependency.
    from ..profiling import profile


class FrameSlider(QSlider):
    """Horizontal slider that advances exactly one frame per wheel notch.

    Qt's default scrolls ``wheelScrollLines`` (typically 3) per tick, which
    overshoots when scrubbing a short animation frame by frame."""

    def wheelEvent(self, event) -> None:
        delta = event.angleDelta().y()
        if delta == 0:
            event.ignore()
            return
        self.setValue(self.value() + (1 if delta > 0 else -1))
        event.accept()


class TimelinePanel(QWidget):
    def __init__(self, state: EditorState, parent=None) -> None:
        super().__init__(parent)
        self.state = state
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._refreshing = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

        root = QVBoxLayout(self)

        # ---- transport row ---------------------------------------------------
        row = QHBoxLayout()
        self.clip_combo = QComboBox()
        self.clip_combo.currentTextChanged.connect(self._on_clip_combo)
        row.addWidget(QLabel("clip"))
        row.addWidget(self.clip_combo)
        add_clip = QPushButton("+")
        add_clip.setFixedWidth(28)
        add_clip.clicked.connect(self._add_clip)
        row.addWidget(add_clip)
        dup_clip = QPushButton("⧉")
        dup_clip.setFixedWidth(28)
        dup_clip.setToolTip("Duplicate current clip")
        dup_clip.clicked.connect(self._dup_clip)
        row.addWidget(dup_clip)
        del_clip = QPushButton("−")
        del_clip.setFixedWidth(28)
        del_clip.clicked.connect(self._del_clip)
        row.addWidget(del_clip)

        self.frames_spin = QSpinBox()
        self.frames_spin.setRange(1, 64)
        self.frames_spin.valueChanged.connect(lambda v: self._apply_clip_field("frames", int(v)))
        row.addWidget(QLabel("frames"))
        row.addWidget(self.frames_spin)
        self.dur_spin = QSpinBox()
        self.dur_spin.setRange(16, 1000)
        self.dur_spin.setSuffix(" ms")
        self.dur_spin.valueChanged.connect(lambda v: self._apply_clip_field("duration_ms", int(v)))
        row.addWidget(self.dur_spin)
        self.loop_check = QCheckBox("loop")
        self.loop_check.toggled.connect(lambda v: self._apply_clip_field("loop", bool(v)))
        row.addWidget(self.loop_check)

        self.play_btn = QPushButton("▶")
        self.play_btn.setCheckable(True)
        self.play_btn.setFixedWidth(36)
        self.play_btn.toggled.connect(self._on_play)
        row.addWidget(self.play_btn)
        self.frame_slider = FrameSlider(Qt.Orientation.Horizontal)
        self.frame_slider.valueChanged.connect(self._on_slider)
        row.addWidget(self.frame_slider, stretch=1)
        self.frame_label = QLabel("0/8")
        row.addWidget(self.frame_label)
        root.addLayout(row)

        # ---- pose-key overview ------------------------------------------------
        pose_row = QHBoxLayout()
        self.pose_status = QLabel()
        self.pose_status.setWordWrap(True)
        pose_row.addWidget(self.pose_status, stretch=1)
        self.prev_pose_btn = QPushButton("◀ previous pose")
        self.prev_pose_btn.clicked.connect(self._jump_previous_pose)
        pose_row.addWidget(self.prev_pose_btn)
        self.pose_key_btn = QPushButton("Mark pose bookmark")
        self.pose_key_btn.clicked.connect(self._toggle_pose_key)
        pose_row.addWidget(self.pose_key_btn)
        self.next_pose_btn = QPushButton("next pose ▶")
        self.next_pose_btn.clicked.connect(self._jump_next_pose)
        pose_row.addWidget(self.next_pose_btn)
        root.addLayout(pose_row)

        self.key_strip = KeyframeStrip(state)
        root.addWidget(self.key_strip)

        plant_row = QHBoxLayout()
        self.plant_status = QLabel()
        self.plant_status.setWordWrap(True)
        plant_row.addWidget(self.plant_status, stretch=1)
        self.plant_selected_btn = QPushButton("Pin selected part")
        self.plant_selected_btn.setToolTip(
            "Continuously hold the selected part's complete world transform for "
            "the entire clip. Position and rotation stay fixed on in-betweens."
        )
        self.plant_selected_btn.clicked.connect(self._pin_selected_part)
        plant_row.addWidget(self.plant_selected_btn)
        self.plant_both_btn = QPushButton("Pin both foot-bone assemblies")
        self.plant_both_btn.setToolTip(
            "Best starting point for idle animations: each foot bone and the "
            "artwork attached to it stay fixed while the body bobs. Lower-leg "
            "artwork still rotates with the knee solve."
        )
        self.plant_both_btn.clicked.connect(self._pin_both_feet)
        plant_row.addWidget(self.plant_both_btn)
        self.release_plant_btn = QPushButton("Release selected")
        self.release_plant_btn.clicked.connect(self._release_selected_part)
        plant_row.addWidget(self.release_plant_btn)
        root.addLayout(plant_row)

        self.pose_help = QLabel(
            "Diamonds are POSE BOOKMARKS, not animation keyframes. Gold dots and gray "
            "bars are real per-channel keys. A first edit now preserves every other "
            "frame; sparse keys still affect the interpolated frames between them."
        )
        self.pose_help.setWordWrap(True)
        self.pose_help.setStyleSheet("color: #aaa4b2; padding: 0 4px 4px 4px;")
        root.addWidget(self.pose_help)

        key_actions = QHBoxLayout()
        self.key_selected_btn = QPushButton("Key selected")
        self.key_selected_btn.setToolTip("Insert keys only for the selected channel or selected bone")
        self.key_selected_btn.clicked.connect(self._key_selected_here)
        key_actions.addWidget(self.key_selected_btn)
        self.key_pose_btn = QPushButton("Key full pose")
        self.key_pose_btn.setToolTip("Insert sampled keys for every driven channel at this frame")
        self.key_pose_btn.clicked.connect(self._key_full_pose_here)
        key_actions.addWidget(self.key_pose_btn)
        self.reset_selected_btn = QPushButton("Return selected to interpolation")
        self.reset_selected_btn.setToolTip("Remove this frame's selected key so neighboring keys control it")
        self.reset_selected_btn.clicked.connect(self._reset_selected_to_interpolation)
        key_actions.addWidget(self.reset_selected_btn)
        self.simplify_selected_btn = QPushButton("Simplify selected")
        self.simplify_selected_btn.setToolTip(
            "Keep this channel only at important pose frames so the in-betweens interpolate"
        )
        self.simplify_selected_btn.clicked.connect(self._simplify_selected)
        key_actions.addWidget(self.simplify_selected_btn)
        self.simplify_clip_btn = QPushButton("Simplify full clip")
        self.simplify_clip_btn.setToolTip(
            "Reduce baked per-frame channel keys to the important pose frames"
        )
        self.simplify_clip_btn.clicked.connect(self._simplify_full_clip)
        key_actions.addWidget(self.simplify_clip_btn)
        key_actions.addStretch(1)
        root.addLayout(key_actions)

        # ---- channels + key editor -------------------------------------------
        self.channel_details = QGroupBox("Advanced channel editor")
        self.channel_details.setCheckable(True)
        self.channel_details.setChecked(False)
        channel_body = QWidget()
        body = QHBoxLayout(channel_body)
        left = QVBoxLayout()
        left.addWidget(QLabel("channels"))
        self.channel_list = QListWidget()
        self.channel_list.currentTextChanged.connect(self._on_channel_selected)
        left.addWidget(self.channel_list)
        chrow = QHBoxLayout()
        addch = QPushButton("Add channel")
        addch.clicked.connect(self._add_channel)
        delch = QPushButton("Delete")
        delch.clicked.connect(self._del_channel)
        chrow.addWidget(addch)
        chrow.addWidget(delch)
        left.addLayout(chrow)
        body.addLayout(left, stretch=1)

        right = QVBoxLayout()
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("type"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["keys", "expr", "const"])
        self.type_combo.currentTextChanged.connect(self._on_type_change)
        type_row.addWidget(self.type_combo)
        type_row.addStretch(1)
        right.addLayout(type_row)

        self.editor_stack = QStackedWidget()
        # keys page
        keys_page = QWidget()
        kl = QVBoxLayout(keys_page)
        self.keys_table = QTableWidget(0, 3)
        self.keys_table.setHorizontalHeaderLabels(["t", "value", "ease"])
        self.keys_table.cellChanged.connect(self._on_key_cell)
        kl.addWidget(self.keys_table)
        krow = QHBoxLayout()
        addk = QPushButton("+ key @ frame")
        addk.clicked.connect(self._add_key_here)
        delk = QPushButton("− key")
        delk.clicked.connect(self._del_key)
        krow.addWidget(addk)
        krow.addWidget(delk)
        kl.addLayout(krow)
        self.editor_stack.addWidget(keys_page)
        # expr page
        expr_page = QWidget()
        el = QVBoxLayout(expr_page)
        self.expr_edit = QLineEdit()
        self.expr_edit.setPlaceholderText("e.g. 2.8*sin(tau*t)")
        self.expr_edit.editingFinished.connect(self._on_expr_edit)
        el.addWidget(self.expr_edit)
        el.addStretch(1)
        self.editor_stack.addWidget(expr_page)
        # const page
        const_page = QWidget()
        cl = QVBoxLayout(const_page)
        self.const_spin = QDoubleSpinBox()
        self.const_spin.setRange(-4096, 4096)
        self.const_spin.setDecimals(3)
        self.const_spin.setKeyboardTracking(False)
        self.const_spin.valueChanged.connect(self._on_const_edit)
        cl.addWidget(self.const_spin)
        cl.addStretch(1)
        self.editor_stack.addWidget(const_page)
        right.addWidget(self.editor_stack)
        body.addLayout(right, stretch=2)
        details_layout = QVBoxLayout(self.channel_details)
        details_layout.addWidget(channel_body)
        channel_body.setVisible(False)
        self.channel_details.toggled.connect(channel_body.setVisible)
        self.channel_details.toggled.connect(self._on_channel_details_toggled)
        root.addWidget(self.channel_details)

        state.docChanged.connect(self.refresh)
        state.animationChanged.connect(self._refresh_animation_edit)
        state.animationChanged.connect(lambda _channels: self._refresh_pose_status())
        state.timeChanged.connect(self._refresh_transport)
        state.timeChanged.connect(self._refresh_pose_status)
        state.poseKeysChanged.connect(self._refresh_pose_status)
        state.selectionChanged.connect(self._refresh_pose_status)
        state.selectionChanged.connect(self._refresh_plant_controls)
        state.timeChanged.connect(self._refresh_plant_controls)
        state.constraintsChanged.connect(self._refresh_plant_controls)
        self.refresh()

    # ---- continuous transform pins -----------------------------------------

    def _refresh_plant_controls(self) -> None:
        candidate = self.state.selected_pinnable_part()
        selected_pin = self.state.selected_part_pin()
        pinned = sorted(self.state.pinned_parts())
        if selected_pin is not None:
            artwork = self.state.selected_pin_artwork_names()
            summary = ", ".join(artwork[:4]) or str(selected_pin.get("bone", "part"))
            adjacent = self.state.selected_pin_adjacent_artwork_names()
            if selected_pin.get("lock_rotation", False):
                detail = "Position and orientation are solved continuously"
            else:
                detail = "Position is solved continuously; rotation follows IK"
            message = (
                f"Pinned: {summary}. {detail} on every frame; drag the green pin "
                "or drag the pinned artwork itself to move it."
            )
            if adjacent:
                message += (
                    " Not controlled by this pin: "
                    f"{', '.join(adjacent[:4])}. Those parts belong to parent bones."
                )
            self.plant_status.setText(message)
        elif pinned:
            self.plant_status.setText(
                f"Pinned parts in this clip: {', '.join(pinned)}. Select one to "
                "move or release it, or pin another endpoint part."
            )
        else:
            self.plant_status.setText(
                "No continuous part pins. Select a foot, hand, or other endpoint "
                "part and pin it; for idle bobbing, pin both foot-bone assemblies."
            )
        self.plant_selected_btn.setEnabled(candidate is not None and selected_pin is None)
        self.release_plant_btn.setEnabled(selected_pin is not None)
        self.plant_both_btn.setEnabled(bool(self.state.pinnable_feet()))
        if selected_pin is not None:
            self.plant_selected_btn.setText("Selected part is pinned")
        elif candidate is not None and not candidate.get("lock_rotation_supported", True):
            self.plant_selected_btn.setText("Pin selected point")
        else:
            self.plant_selected_btn.setText("Pin selected part")

    def _pin_selected_part(self) -> None:
        self.state.push_undo()
        if not self.state.pin_selected_part_entire_clip():
            self.state.discard_last_undo()
        self._refresh_plant_controls()

    def _pin_both_feet(self) -> None:
        self.state.push_undo()
        if not self.state.pin_all_feet_entire_clip():
            self.state.discard_last_undo()
        self._refresh_plant_controls()

    def _release_selected_part(self) -> None:
        self.state.push_undo()
        if not self.state.release_selected_part_pin():
            self.state.discard_last_undo()
        self._refresh_plant_controls()

    # ---- helpers ----------------------------------------------------------------

    def _channel_name(self) -> Optional[str]:
        item = self.channel_list.currentItem()
        return item.text().split("  ")[0] if item else None

    def _spec(self) -> Optional[dict]:
        name = self._channel_name()
        if not name:
            return None
        return self.state.clip().get("channels", {}).get(name)

    def _on_channel_selected(self, _text: str) -> None:
        self.key_strip.set_selected_channel(self._channel_name())
        self._refresh_editor()
        self._refresh_pose_status()

    def _on_channel_details_toggled(self, expanded: bool) -> None:
        if not expanded:
            self.channel_list.clearSelection()
            self.channel_list.setCurrentRow(-1)
            self.key_strip.set_selected_channel(None)
            self._refresh_pose_status()

    def _selected_edit_channels(self) -> list[str]:
        channel = self._channel_name()
        if channel:
            return [channel]
        return self.state.selected_animation_channels()

    def _toggle_pose_key(self) -> None:
        self.state.push_undo()
        if not self.state.toggle_pose_key():
            self.state.discard_last_undo()
        self._refresh_pose_status()

    def _jump_previous_pose(self) -> None:
        previous, _following = self.state.neighboring_pose_keys()
        if previous is not None:
            self.state.set_frame(previous)

    def _jump_next_pose(self) -> None:
        _previous, following = self.state.neighboring_pose_keys()
        if following is not None:
            self.state.set_frame(following)

    def _key_selected_here(self) -> None:
        channels = self._selected_edit_channels()
        self.state.push_undo()
        if not self.state.insert_keys_here(channels):
            self.state.discard_last_undo()

    def _key_full_pose_here(self) -> None:
        self.state.push_undo()
        if not self.state.insert_keys_here([]):
            self.state.discard_last_undo()

    def _reset_selected_to_interpolation(self) -> None:
        channels = self._selected_edit_channels()
        if not channels:
            return
        self.state.push_undo()
        if not self.state.remove_keys_here(channels):
            self.state.discard_last_undo()

    def _simplify_selected(self) -> None:
        channels = self._selected_edit_channels()
        if not channels:
            return
        self.state.push_undo()
        if not self.state.simplify_channels_to_pose_keys(channels):
            self.state.discard_last_undo()

    def _simplify_full_clip(self) -> None:
        dense = self.state.dense_keyed_channels()
        if not dense:
            return
        answer = QMessageBox.question(
            self,
            "Simplify animation keys",
            "Keep the current important poses, remove redundant per-frame keys, "
            "and let the frames between them interpolate?\n\n"
            f"This will simplify {len(dense)} densely keyed channel(s).",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.state.push_undo()
        if not self.state.simplify_channels_to_pose_keys(dense):
            self.state.discard_last_undo()

    def _refresh_pose_status(self) -> None:
        pose_keys, explicit = self.state.pose_key_frames()
        current = self.state.frame_idx
        is_pose = current in pose_keys
        keyed = self.state.keyed_channels_at_frame(current)
        previous, following = self.state.neighboring_pose_keys()
        source = "saved" if explicit else "suggested"
        if is_pose:
            description = f"KEY POSE ({source})"
        else:
            description = "IN-BETWEEN"
        dense = self.state.dense_keyed_channels()
        dense_note = (
            f" · {len(dense)} channel(s) keyed every frame" if dense else ""
        )
        self.pose_status.setText(
            f"Frame {current + 1}/{self.state.frames()} · {description} · "
            f"{len(keyed)} channel key{'' if len(keyed) == 1 else 's'} here"
            f"{dense_note}"
        )
        self.pose_key_btn.setText("Unmark pose bookmark" if is_pose else "Mark pose bookmark")
        self.prev_pose_btn.setEnabled(previous is not None)
        self.next_pose_btn.setEnabled(following is not None)
        self.prev_pose_btn.setText(
            f"◀ BEFORE · pose {previous + 1}"
            if previous is not None
            else "◀ BEFORE pose"
        )
        self.next_pose_btn.setText(
            f"AFTER · pose {following + 1} ▶"
            if following is not None
            else "AFTER pose ▶"
        )
        self.prev_pose_btn.setStyleSheet(
            f"color: {before_pose_color().name()}; font-weight: 600;"
            if previous is not None
            else ""
        )
        self.next_pose_btn.setStyleSheet(
            f"color: {after_pose_color().name()}; font-weight: 600;"
            if following is not None
            else ""
        )
        selected = self._selected_edit_channels()
        self.key_selected_btn.setEnabled(bool(selected))
        selected_has_key = any(name in keyed for name in selected)
        self.reset_selected_btn.setEnabled(bool(selected) and selected_has_key)
        selected_dense = any(name in dense for name in selected)
        self.simplify_selected_btn.setEnabled(bool(selected) and selected_dense)
        self.simplify_clip_btn.setEnabled(bool(dense))
        self.key_strip.update()

    # ---- refresh ------------------------------------------------------------------

    def _channel_rows(self) -> list[str]:
        rows = []
        current = self.state.frame_idx
        key_map = self.state.channel_key_frames()
        for name, spec in self.state.clip().get("channels", {}).items():
            kind = "keys" if "keys" in spec else ("expr" if "expr" in spec else "const")
            marker = "●" if current in key_map.get(name, set()) else "·"
            rows.append(f"{name}  {marker} [{kind}]")
        return rows

    def _replace_channel_rows(self, rows: list[str], current: Optional[str]) -> None:
        self.channel_list.clear()
        self.channel_list.addItems(rows)
        if current:
            for index in range(self.channel_list.count()):
                if self.channel_list.item(index).text().split("  ")[0] == current:
                    self.channel_list.setCurrentRow(index)
                    break

    @profile
    def refresh(self) -> None:
        self._refreshing = True
        try:
            doc = self.state.doc
            self.clip_combo.clear()
            self.clip_combo.addItems(list(doc.clips))
            self.clip_combo.setCurrentText(self.state.clip_name)
            clip = self.state.clip()
            self.frames_spin.setValue(int(clip.get("frames", 8)))
            self.dur_spin.setValue(int(clip.get("duration_ms", 100)))
            self.loop_check.setChecked(bool(clip.get("loop", True)))
            current = self._channel_name()
            self._replace_channel_rows(self._channel_rows(), current)
            self._refresh_transport()
            self.key_strip.set_selected_channel(self._channel_name())
            self._refresh_editor()
            self._refresh_pose_status()
            self._refresh_plant_controls()
        finally:
            self._refreshing = False


    @profile
    def _refresh_animation_edit(self, changed_channels) -> None:
        """Refresh only the channel UI touched by an interactive pose edit."""
        if self._refreshing:
            return
        self._refreshing = True
        try:
            current = self._channel_name()
            desired = self._channel_rows()
            displayed = [
                self.channel_list.item(index).text()
                for index in range(self.channel_list.count())
            ]
            rows_changed = displayed != desired
            if rows_changed:
                self._replace_channel_rows(desired, current)
            selected = self._channel_name()
            if rows_changed or selected in set(changed_channels or ()):
                self._refresh_editor()
        finally:
            self._refreshing = False

    def _refresh_transport(self) -> None:
        was = self._refreshing
        self._refreshing = True
        try:
            if self.clip_combo.currentText() != self.state.clip_name:
                # Clip switched programmatically (or via undo) — resync the
                # whole panel, not just the transport row.
                self._refreshing = was
                self.refresh()
                return
            n = self.state.frames()
            self.frame_slider.setMaximum(n - 1)
            self.frame_slider.setValue(self.state.frame_idx)
            self.frame_label.setText(f"{self.state.frame_idx + 1}/{n}")
            current = self._channel_name()
            desired = self._channel_rows()
            displayed = [
                self.channel_list.item(index).text()
                for index in range(self.channel_list.count())
            ]
            if displayed != desired:
                self._replace_channel_rows(desired, current)
        finally:
            self._refreshing = was

    @profile
    def _refresh_editor(self) -> None:
        was = self._refreshing
        self._refreshing = True
        try:
            spec = self._spec()
            if spec is None:
                self.keys_table.setRowCount(0)
                self.expr_edit.clear()
                return
            if "keys" in spec:
                self.type_combo.setCurrentText("keys")
                self.editor_stack.setCurrentIndex(0)
                keys = spec.get("keys", [])
                self.keys_table.setRowCount(len(keys))
                for r, k in enumerate(keys):
                    ease = k[2] if len(k) > 2 else "smooth"
                    items = [
                        QTableWidgetItem(f"{float(k[0]):.4g}"),
                        QTableWidgetItem(f"{float(k[1]):.4g}"),
                        QTableWidgetItem(str(ease)),
                    ]
                    from ..authoring.animation_keys import time_to_frame

                    if time_to_frame(
                        float(k[0]), self.state.frames(), bool(self.state.clip().get("loop", True))
                    ) == self.state.frame_idx:
                        for item in items:
                            item.setBackground(QBrush(QColor(80, 70, 98)))
                    for col, item in enumerate(items):
                        self.keys_table.setItem(r, col, item)
            elif "expr" in spec:
                self.type_combo.setCurrentText("expr")
                self.editor_stack.setCurrentIndex(1)
                self.expr_edit.setText(str(spec["expr"]))
            else:
                self.type_combo.setCurrentText("const")
                self.editor_stack.setCurrentIndex(2)
                self.const_spin.setValue(float(spec.get("const", 0.0)))
        finally:
            self._refreshing = was

    # ---- transport edits --------------------------------------------------------------

    def _on_clip_combo(self, name: str) -> None:
        if self._refreshing or not name:
            return
        self.state.set_clip(name)
        self.refresh()

    def _on_slider(self, value: int) -> None:
        if self._refreshing:
            return
        self.state.set_frame(int(value))

    def _on_play(self, playing: bool) -> None:
        self.play_btn.setText("⏸" if playing else "▶")
        if playing:
            self.timer.start(int(self.state.clip().get("duration_ms", 100)))
        else:
            self.timer.stop()

    def _tick(self) -> None:
        self.timer.setInterval(int(self.state.clip().get("duration_ms", 100)))
        self.state.set_frame((self.state.frame_idx + 1) % self.state.frames())

    def _apply_clip_field(self, field: str, value) -> None:
        if self._refreshing:
            return
        self.state.push_undo()
        self.state.clip()[field] = value
        self.state.mark_changed()

    def _add_clip(self) -> None:
        name, ok = QInputDialog.getText(self, "Add clip", "Clip name (e.g. run, jump):")
        name = name.strip()
        if not ok or not name:
            return
        if name in self.state.doc.clips:
            QMessageBox.warning(self, "Add clip", f"Clip {name!r} already exists.")
            return
        self.state.push_undo()
        self.state.doc.clips[name] = {"loop": True, "frames": 8, "duration_ms": 100, "channels": {}}
        self.state.clip_name = name
        self.state.frame_idx = 0
        self.state.mark_changed()
        self.state.timeChanged.emit()

    def _dup_clip(self) -> None:
        import json

        src = self.state.clip_name
        name, ok = QInputDialog.getText(
            self, "Duplicate clip", "New clip name:", text=f"{src}_copy"
        )
        name = name.strip()
        if not ok or not name:
            return
        if name in self.state.doc.clips:
            QMessageBox.warning(self, "Duplicate clip", f"Clip {name!r} already exists.")
            return
        self.state.push_undo()
        self.state.doc.clips[name] = json.loads(json.dumps(self.state.doc.clips[src]))
        self.state.clip_name = name
        self.state.frame_idx = 0
        self.state.mark_changed()
        self.state.timeChanged.emit()

    def _del_clip(self) -> None:
        if len(self.state.doc.clips) <= 1:
            QMessageBox.warning(self, "Delete clip", "A document needs at least one clip.")
            return
        name = self.state.clip_name
        if QMessageBox.question(self, "Delete clip", f"Delete clip {name!r}?") != QMessageBox.StandardButton.Yes:
            return
        self.state.push_undo()
        self.state.doc.clips.pop(name, None)
        self.state.clip_name = next(iter(self.state.doc.clips))
        self.state.frame_idx = 0
        self.state.mark_changed()
        self.state.timeChanged.emit()

    # ---- channel edits ------------------------------------------------------------------

    def _add_channel(self) -> None:
        doc = self.state.doc
        options = [b["name"] for b in doc.bones] + ["root_x", "root_y"]
        for leg in doc.ik_legs:
            pre = leg.get("channel_prefix", "foot")
            options += [f"{pre}_x", f"{pre}_lift", f"{pre}_pitch"]
        options += ["(custom…)"]
        existing = set(self.state.clip().get("channels", {}))
        options = [o for o in options if o not in existing]
        name, ok = QInputDialog.getItem(self, "Add channel", "Channel:", options, 0, False)
        if not ok:
            return
        if name == "(custom…)":
            name, ok = QInputDialog.getText(self, "Add channel", "Channel name:")
            name = name.strip()
            if not ok or not name:
                return
        self.state.push_undo()
        self.state.clip().setdefault("channels", {})[name] = {"keys": [[0.0, 0.0, "smooth"]]}
        self.state.mark_changed()

    def _del_channel(self) -> None:
        name = self._channel_name()
        if not name:
            return
        self.state.push_undo()
        self.state.clip().get("channels", {}).pop(name, None)
        self.state.mark_changed()

    def _on_type_change(self, kind: str) -> None:
        if self._refreshing:
            return
        name = self._channel_name()
        spec = self._spec()
        if not name or spec is None:
            return
        current = "keys" if "keys" in spec else ("expr" if "expr" in spec else "const")
        if current == kind:
            return
        self.state.push_undo()
        channels = self.state.clip().setdefault("channels", {})
        loop = bool(self.state.clip().get("loop", True))
        from ..authoring.rigdoc import sample_channel_spec

        v0 = sample_channel_spec(spec, 0.0, loop)
        if kind == "keys":
            n = self.state.frames()
            channels[name] = {
                "keys": [
                    [
                        round(self.state.doc.frame_time(self.state.clip_name, i), 4),
                        round(sample_channel_spec(spec, self.state.doc.frame_time(self.state.clip_name, i), loop), 3),
                        "linear",
                    ]
                    for i in range(n)
                ]
            }
        elif kind == "expr":
            channels[name] = {"expr": str(round(v0, 3))}
        else:
            channels[name] = {"const": round(v0, 3)}
        self.state.mark_changed()

    def _on_expr_edit(self) -> None:
        if self._refreshing:
            return
        spec = self._spec()
        if spec is None or "expr" not in spec:
            return
        text = self.expr_edit.text().strip()
        if not text or text == spec.get("expr"):
            return
        from ..authoring.rigdoc import eval_expr

        try:
            eval_expr(text, 0.0)  # validate before committing
        except Exception as ex:  # noqa: BLE001
            QMessageBox.warning(self, "Expression", f"Bad expression:\n{ex}")
            return
        self.state.push_undo()
        spec["expr"] = text
        self.state.mark_changed()

    def _on_const_edit(self, value: float) -> None:
        if self._refreshing:
            return
        spec = self._spec()
        if spec is None or "const" not in spec:
            return
        self.state.push_undo()
        spec["const"] = float(value)
        self.state.mark_changed()

    def _on_key_cell(self, row: int, col: int) -> None:
        if self._refreshing:
            return
        spec = self._spec()
        if spec is None or "keys" not in spec:
            return
        keys = spec["keys"]
        if row >= len(keys):
            return
        item = self.keys_table.item(row, col)
        if item is None:
            return
        text = item.text().strip()
        self.state.push_undo()
        k = list(keys[row]) + (["smooth"] if len(keys[row]) < 3 else [])
        if col == 2:
            if text not in EASE_NAMES:
                return
            k[2] = text
        else:
            try:
                k[col] = float(text)
            except ValueError:
                return
        keys[row] = k
        keys.sort(key=lambda kk: float(kk[0]))
        self.state.mark_changed()

    def _add_key_here(self) -> None:
        name = self._channel_name()
        if not name:
            return
        spec = self._spec()
        loop = bool(self.state.clip().get("loop", True))
        from ..authoring.rigdoc import sample_channel_spec

        value = sample_channel_spec(spec, self.state.t(), loop) if spec else 0.0
        self.state.push_undo()
        if not self.state.write_key(name, round(value, 3)):
            self.state.discard_last_undo()

    def _del_key(self) -> None:
        spec = self._spec()
        row = self.keys_table.currentRow()
        if spec is None or "keys" not in spec or row < 0 or row >= len(spec["keys"]):
            return
        if len(spec["keys"]) <= 1:
            return
        self.state.push_undo()
        spec["keys"].pop(row)
        self.state.mark_changed()
