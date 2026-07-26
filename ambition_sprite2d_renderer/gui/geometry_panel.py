"""Authoring-only collision, hurtbox, hitbox, and cue-binding panel."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..authoring.gameplay_geometry import (
    ExistingGeometryError,
    attack_like_clips,
    collision_entry,
    generate_collision,
    generate_hitbox,
    generate_hurtboxes,
    geometry_root,
    hitbox_entry,
    hurtbox_entry,
)
from .state import EditorState


def _dspin() -> QDoubleSpinBox:
    widget = QDoubleSpinBox()
    widget.setRange(-4096.0, 4096.0)
    widget.setDecimals(2)
    widget.setSingleStep(0.5)
    widget.setKeyboardTracking(False)
    return widget


class RectEditor(QGroupBox):
    """Compact numeric editor for one generated rectangle."""

    def __init__(self, title: str, changed, parent=None) -> None:
        super().__init__(title, parent)
        self._changed = changed
        self._refreshing = False
        form = QFormLayout(self)
        self.status = QLabel("Missing")
        self.status.setWordWrap(True)
        form.addRow("status", self.status)
        self.spins = {name: _dspin() for name in ("x", "y", "w", "h")}
        for name, spin in self.spins.items():
            spin.valueChanged.connect(lambda _value, name=name: self._on_change(name))
            form.addRow(name, spin)
        self.set_rect(None)

    def set_rect(self, rect: dict | None, status: str | None = None) -> None:
        self._refreshing = True
        try:
            self.status.setText(status or ("Present" if rect else "Missing"))
            self.setEnabled(rect is not None)
            for name, spin in self.spins.items():
                spin.setValue(float((rect or {}).get(name, 0.0)))
        finally:
            self._refreshing = False

    def _on_change(self, _name: str) -> None:
        if self._refreshing:
            return
        self._changed({name: spin.value() for name, spin in self.spins.items()})


class GeometryPanel(QWidget):
    """First-stage gameplay geometry authoring UI.

    Data written here is intentionally ignored by publication and runtime code.
    It exists so artists can establish and revise the authoring contract before
    the game begins consuming it.
    """

    def __init__(self, state: EditorState, parent=None) -> None:
        super().__init__(parent)
        self.state = state
        self._refreshing = False
        layout = QVBoxLayout(self)

        note = QLabel(
            "Authoring-only: saved in gameplay_geometry; current sheet and game "
            "publication do not consume it. Generators never overwrite existing "
            "geometry without confirmation."
        )
        note.setWordWrap(True)
        layout.addWidget(note)

        vis = QGroupBox("Overlay visibility")
        vis_layout = QHBoxLayout(vis)
        self.show_collision = QCheckBox("Collision")
        self.show_hurt = QCheckBox("Hurt")
        self.show_hit = QCheckBox("Hit")
        for check in (self.show_collision, self.show_hurt, self.show_hit):
            check.setChecked(True)
            vis_layout.addWidget(check)
        self.show_collision.toggled.connect(
            lambda value: state.set_geometry_visibility(collision=value)
        )
        self.show_hurt.toggled.connect(
            lambda value: state.set_geometry_visibility(hurtbox=value)
        )
        self.show_hit.toggled.connect(
            lambda value: state.set_geometry_visibility(hitbox=value)
        )
        layout.addWidget(vis)

        summary = QGroupBox("Coverage")
        summary_form = QFormLayout(summary)
        self.collision_summary = QLabel()
        self.hurt_summary = QLabel()
        self.hit_summary = QLabel()
        summary_form.addRow("collision", self.collision_summary)
        summary_form.addRow("hurtboxes", self.hurt_summary)
        summary_form.addRow("current hitbox", self.hit_summary)
        layout.addWidget(summary)

        buttons = QGridLayout()
        self.gen_collision = QPushButton("Generate collision")
        self.gen_hurt = QPushButton("Generate hurtboxes")
        self.gen_hit = QPushButton("Generate hitbox for current clip")
        self.gen_collision.clicked.connect(self._generate_collision)
        self.gen_hurt.clicked.connect(self._generate_hurt)
        self.gen_hit.clicked.connect(self._generate_hit)
        buttons.addWidget(self.gen_collision, 0, 0)
        buttons.addWidget(self.gen_hurt, 0, 1)
        buttons.addWidget(self.gen_hit, 1, 0, 1, 2)
        layout.addLayout(buttons)

        self.collision_rect = RectEditor("Collision rectangle", self._edit_collision)
        self.hurt_rect = RectEditor("Current clip hurtbox", self._edit_hurt)
        self.hit_rect = RectEditor("Current clip hitbox", self._edit_hit)
        layout.addWidget(self.collision_rect)
        layout.addWidget(self.hurt_rect)
        layout.addWidget(self.hit_rect)

        attack = QGroupBox("Current hitbox window and presentation bindings")
        attack_form = QFormLayout(attack)
        self.active_start = QSpinBox()
        self.active_end = QSpinBox()
        self.active_start.setRange(0, 4096)
        self.active_end.setRange(0, 4096)
        self.vfx = QLineEdit()
        self.sfx = QLineEdit()
        self.vfx.setPlaceholderText("comma-separated VFX cue ids")
        self.sfx.setPlaceholderText("comma-separated SFX cue ids")
        self.active_start.valueChanged.connect(lambda _value: self._edit_attack_meta())
        self.active_end.valueChanged.connect(lambda _value: self._edit_attack_meta())
        self.vfx.editingFinished.connect(self._edit_attack_meta)
        self.sfx.editingFinished.connect(self._edit_attack_meta)
        attack_form.addRow("active start frame", self.active_start)
        attack_form.addRow("active end frame", self.active_end)
        attack_form.addRow("VFX bindings", self.vfx)
        attack_form.addRow("SFX bindings", self.sfx)
        layout.addWidget(attack)
        layout.addStretch(1)

        state.docChanged.connect(self.refresh)
        state.geometryChanged.connect(self.refresh)
        state.timeChanged.connect(self.refresh)
        self.refresh()

    def _confirm_replace(self, noun: str) -> bool:
        return QMessageBox.question(
            self,
            f"Replace {noun}?",
            f"{noun.capitalize()} already exists. Replace it with a newly generated seed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes

    def _run_generator(self, fn, noun: str) -> None:
        self.state.push_undo()
        app = QApplication.instance()
        if app is not None:
            app.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            try:
                result = fn(False)
            except ExistingGeometryError:
                if not self._confirm_replace(noun):
                    self.state.discard_last_undo()
                    return
                result = fn(True)
        except Exception as ex:  # noqa: BLE001
            if self.state._undo:
                self.state.discard_last_undo()
            QMessageBox.critical(self, f"Generate {noun}", str(ex))
            return
        finally:
            if app is not None:
                app.restoreOverrideCursor()
        self.state.mark_geometry_changed()
        window = self.window()
        if hasattr(window, "statusBar"):
            window.statusBar().showMessage(result.message, 5000)

    def _generate_collision(self) -> None:
        self._run_generator(
            lambda replace: generate_collision(self.state.doc, replace=replace),
            "collision",
        )

    def _generate_hurt(self) -> None:
        self._run_generator(
            lambda replace: generate_hurtboxes(self.state.doc, replace=replace),
            "hurtboxes",
        )

    def _generate_hit(self) -> None:
        clip = self.state.clip_name
        self._run_generator(
            lambda replace: generate_hitbox(self.state.doc, clip, replace=replace),
            f"hitbox for {clip}",
        )

    def _mutate_rect(self, entry: dict | None, shape_key: str, values: dict) -> None:
        if entry is None:
            return
        shape = entry.get(shape_key)
        if shape_key == "shapes":
            shapes = entry.setdefault("shapes", [])
            if not shapes:
                return
            shape = shapes[0]
        if not isinstance(shape, dict):
            return
        self.state.push_undo()
        shape.update({name: round(float(value), 2) for name, value in values.items()})
        provenance = entry.setdefault("provenance", {})
        provenance["edited"] = True
        self.state.mark_geometry_changed()

    def _edit_collision(self, values: dict) -> None:
        self._mutate_rect(collision_entry(self.state.doc), "shape", values)

    def _edit_hurt(self, values: dict) -> None:
        self._mutate_rect(hurtbox_entry(self.state.doc, self.state.clip_name), "shape", values)

    def _edit_hit(self, values: dict) -> None:
        self._mutate_rect(hitbox_entry(self.state.doc, self.state.clip_name), "shapes", values)

    @staticmethod
    def _split_bindings(text: str) -> list[str]:
        return [item.strip() for item in text.split(",") if item.strip()]

    def _edit_attack_meta(self) -> None:
        if self._refreshing:
            return
        entry = hitbox_entry(self.state.doc, self.state.clip_name)
        if entry is None:
            return
        values = [self.active_start.value(), self.active_end.value()]
        if values[1] < values[0]:
            values[1] = values[0]
        bindings = {
            "vfx": self._split_bindings(self.vfx.text()),
            "sfx": self._split_bindings(self.sfx.text()),
        }
        if entry.get("active_frames") == values and entry.get("bindings") == bindings:
            return
        self.state.push_undo()
        entry["active_frames"] = values
        entry["bindings"] = bindings
        entry.setdefault("provenance", {})["edited"] = True
        self.state.mark_geometry_changed()

    def refresh(self) -> None:
        self._refreshing = True
        try:
            doc = self.state.doc
            root = geometry_root(doc, create=False)
            collision = collision_entry(doc)
            hurt_clips = root.get("hurtboxes", {}).get("clips", {})
            hit_clips = root.get("hitboxes", {}).get("clips", {})
            attack_count = len(attack_like_clips(doc))
            current_hurt = hurtbox_entry(doc, self.state.clip_name)
            current_hit = hitbox_entry(doc, self.state.clip_name)

            self.collision_summary.setText("present" if collision else "missing")
            self.hurt_summary.setText(f"{len(hurt_clips)} / {len(doc.clips)} clips")
            current_status = "present" if current_hit else "missing"
            self.hit_summary.setText(
                f"{len(hit_clips)} / {attack_count} attack-like clips; "
                f"{self.state.clip_name}: {current_status}"
            )
            self.gen_hit.setToolTip(
                f"Detected {attack_count} attack-like clips; generation applies only to the selected clip."
            )

            collision_shape = collision.get("shape") if collision else None
            hurt_shape = current_hurt.get("shape") if current_hurt else None
            hit_shape = None
            if current_hit and current_hit.get("shapes"):
                hit_shape = current_hit["shapes"][0]
            self.collision_rect.set_rect(collision_shape)
            self.hurt_rect.set_rect(hurt_shape)
            self.hit_rect.set_rect(hit_shape)

            enabled = current_hit is not None
            for widget in (self.active_start, self.active_end, self.vfx, self.sfx):
                widget.setEnabled(enabled)
            if current_hit:
                active = current_hit.get("active_frames") or [0, 0]
                self.active_start.setMaximum(max(0, self.state.frames() - 1))
                self.active_end.setMaximum(max(0, self.state.frames() - 1))
                self.active_start.setValue(int(active[0]))
                self.active_end.setValue(int(active[-1]))
                bindings = current_hit.get("bindings") or {}
                self.vfx.setText(", ".join(bindings.get("vfx") or []))
                self.sfx.setText(", ".join(bindings.get("sfx") or []))
            else:
                self.active_start.setValue(0)
                self.active_end.setValue(0)
                self.vfx.clear()
                self.sfx.clear()
        finally:
            self._refreshing = False
