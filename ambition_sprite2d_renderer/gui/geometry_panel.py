"""Authoring-only collision, hurtbox, hitbox, and cue-binding panel."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..authoring.gameplay_geometry import (
    ExistingGeometryError,
    SHAPE_KINDS,
    assign_hurtbox_profile,
    attack_like_clips,
    collision_entry,
    convert_shape,
    create_hurtbox_profile,
    default_shape,
    entry_shapes,
    generate_collision,
    generate_hitbox,
    generate_hurtboxes,
    geometry_root,
    hitbox_entry,
    hurtbox_clip_binding,
    hurtbox_entry,
    hurtbox_profile_users,
    hurtbox_profiles,
    hurtbox_source,
    layer_entry,
    layer_shapes,
    make_hurtbox_override,
    mark_entry_edited,
    polygon_is_convex,
    remove_hurtbox_override,
)
from .state import EditorState

_LAYER_LABELS = {
    "collision": "Collision",
    "hurtbox": "Hurtboxes: current clip",
    "hitbox": "Hitboxes: current clip",
}


def _dspin() -> QDoubleSpinBox:
    widget = QDoubleSpinBox()
    widget.setRange(-4096.0, 4096.0)
    widget.setDecimals(2)
    widget.setSingleStep(0.5)
    widget.setKeyboardTracking(False)
    return widget


class PreciseShapeEditor(QGroupBox):
    """Exact numeric editor for the currently selected canvas shape."""

    def __init__(self, changed, convert_requested, parent=None) -> None:
        super().__init__("Selected shape: precise values", parent)
        self._changed = changed
        self._convert_requested = convert_requested
        self._refreshing = False
        self._shape: dict | None = None
        outer = QVBoxLayout(self)

        form = QFormLayout()
        self.name = QLineEdit()
        self.kind = QComboBox()
        self.kind.addItems(list(SHAPE_KINDS))
        self.status = QLabel("No shape selected")
        self.status.setWordWrap(True)
        form.addRow("name", self.name)
        form.addRow("kind", self.kind)
        form.addRow("status", self.status)
        outer.addLayout(form)

        self.stack = QStackedWidget()
        self.pages: dict[str, QWidget] = {}
        self.spins: dict[str, QDoubleSpinBox] = {}
        for kind, fields in (
            ("rect", ("x", "y", "w", "h")),
            ("circle", ("cx", "cy", "r")),
            ("capsule", ("ax", "ay", "bx", "by", "r")),
        ):
            page = QWidget()
            page_form = QFormLayout(page)
            for field in fields:
                spin = _dspin()
                spin.valueChanged.connect(
                    lambda _value, field=field: self._on_scalar_change(field)
                )
                self.spins[field] = spin
                page_form.addRow(field, spin)
            self.pages[kind] = page
            self.stack.addWidget(page)

        polygon_page = QWidget()
        polygon_layout = QVBoxLayout(polygon_page)
        self.points = QTableWidget(0, 2)
        self.points.setHorizontalHeaderLabels(["x", "y"])
        self.points.horizontalHeader().setStretchLastSection(True)
        self.points.cellChanged.connect(self._on_points_change)
        polygon_layout.addWidget(self.points)
        point_buttons = QHBoxLayout()
        self.add_point = QPushButton("Add vertex")
        self.delete_point = QPushButton("Delete vertex")
        self.add_point.clicked.connect(self._add_point)
        self.delete_point.clicked.connect(self._delete_point)
        point_buttons.addWidget(self.add_point)
        point_buttons.addWidget(self.delete_point)
        polygon_layout.addLayout(point_buttons)
        self.pages["polygon"] = polygon_page
        self.stack.addWidget(polygon_page)
        outer.addWidget(self.stack)

        self.name.editingFinished.connect(self._on_name_change)
        self.kind.currentTextChanged.connect(self._on_kind_change)
        self.set_shape(None)

    def set_shape(self, shape: dict | None) -> None:
        self._refreshing = True
        try:
            self._shape = shape
            enabled = shape is not None
            self.setEnabled(enabled)
            if not enabled:
                self.status.setText("No shape selected")
                self.name.clear()
                return
            kind = str(shape.get("kind", "rect"))
            self.name.setText(str(shape.get("name", "")))
            self.kind.setCurrentText(kind)
            self.stack.setCurrentWidget(self.pages[kind])
            for field, spin in self.spins.items():
                spin.setValue(float(shape.get(field, 0.0)))
            self.points.setRowCount(0)
            if kind == "polygon":
                points = shape.get("points") or []
                self.points.setRowCount(len(points))
                for row, point in enumerate(points):
                    self.points.setItem(row, 0, QTableWidgetItem(f"{float(point[0]):.2f}"))
                    self.points.setItem(row, 1, QTableWidgetItem(f"{float(point[1]):.2f}"))
                convex = polygon_is_convex(points)
                self.status.setText(
                    f"{len(points)} vertices; " + ("convex" if convex else "not convex — future runtime export may reject it")
                )
            else:
                self.status.setText("Drag the filled shape to move it; drag its handles to reshape it.")
        finally:
            self._refreshing = False

    def _on_name_change(self) -> None:
        if not self._refreshing and self._shape is not None:
            self._changed({"name": self.name.text().strip()})

    def _on_kind_change(self, kind: str) -> None:
        if self._refreshing or self._shape is None:
            return
        self._convert_requested(kind)

    def _on_scalar_change(self, field: str) -> None:
        if self._refreshing or self._shape is None:
            return
        self._changed({field: self.spins[field].value()})

    def _read_points(self) -> list[list[float]] | None:
        points = []
        try:
            for row in range(self.points.rowCount()):
                x_item = self.points.item(row, 0)
                y_item = self.points.item(row, 1)
                points.append([float(x_item.text()), float(y_item.text())])
        except (AttributeError, ValueError):
            return None
        return points

    def _on_points_change(self, _row: int, _column: int) -> None:
        if self._refreshing or self._shape is None:
            return
        points = self._read_points()
        if points is not None:
            self._changed({"points": points})

    def _add_point(self) -> None:
        if self._shape is None:
            return
        points = [list(point) for point in self._shape.get("points") or []]
        if len(points) >= 2:
            a, b = points[-2], points[-1]
            points.append([b[0] + (b[0] - a[0]), b[1] + (b[1] - a[1])])
        elif points:
            points.append([points[-1][0] + 10.0, points[-1][1]])
        else:
            points.append([0.0, 0.0])
        self._changed({"points": points})

    def _delete_point(self) -> None:
        if self._shape is None:
            return
        points = [list(point) for point in self._shape.get("points") or []]
        if len(points) <= 3:
            return
        row = self.points.currentRow()
        if row < 0:
            row = len(points) - 1
        del points[row]
        self._changed({"points": points})


class GeometryPanel(QWidget):
    """Gameplay-geometry authoring UI, intentionally ignored by publication."""

    def __init__(self, state: EditorState, parent=None) -> None:
        super().__init__(parent)
        self.state = state
        self._refreshing = False
        top = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        layout = QVBoxLayout(body)
        scroll.setWidget(body)
        top.addWidget(scroll)

        note = QLabel(
            "Authoring-only: current sheet and game publication do not consume this data. "
            "Collision is global. Hurtbox clips normally share named profiles and may opt "
            "into local overrides. Hitboxes remain animation-specific."
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
        self.show_collision.toggled.connect(lambda value: state.set_geometry_visibility(collision=value))
        self.show_hurt.toggled.connect(lambda value: state.set_geometry_visibility(hurtbox=value))
        self.show_hit.toggled.connect(lambda value: state.set_geometry_visibility(hitbox=value))
        layout.addWidget(vis)

        summary = QGroupBox("Coverage")
        summary_form = QFormLayout(summary)
        self.collision_summary = QLabel()
        self.hurt_summary = QLabel()
        self.hit_summary = QLabel()
        self.hurt_summary.setWordWrap(True)
        self.hit_summary.setWordWrap(True)
        summary_form.addRow("collision", self.collision_summary)
        summary_form.addRow("hurtboxes", self.hurt_summary)
        summary_form.addRow("current hitbox", self.hit_summary)
        layout.addWidget(summary)

        buttons = QGridLayout()
        self.gen_collision = QPushButton("Generate collision")
        self.gen_hurt = QPushButton("Generate shared hurtbox profiles")
        self.gen_hit = QPushButton("Generate hitbox for current clip")
        self.gen_collision.clicked.connect(self._generate_collision)
        self.gen_hurt.clicked.connect(self._generate_hurt)
        self.gen_hit.clicked.connect(self._generate_hit)
        buttons.addWidget(self.gen_collision, 0, 0)
        buttons.addWidget(self.gen_hurt, 0, 1)
        buttons.addWidget(self.gen_hit, 1, 0, 1, 2)
        layout.addLayout(buttons)

        sharing = QGroupBox("Hurtbox sharing for current animation")
        sharing_form = QFormLayout(sharing)
        self.hurt_source = QLabel()
        self.hurt_source.setWordWrap(True)
        self.hurt_used_by = QLabel()
        self.hurt_used_by.setWordWrap(True)
        self.hurt_profile = QComboBox()
        self.hurt_profile.currentIndexChanged.connect(self._assign_selected_profile)
        profile_buttons = QWidget()
        profile_buttons_layout = QGridLayout(profile_buttons)
        profile_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.new_profile = QPushButton("Create new shared hurtbox")
        self.duplicate_profile = QPushButton("Copy as new shared hurtbox")
        self.make_override = QPushButton("Make unique for this animation")
        self.remove_override = QPushButton("Rejoin shared hurtbox")
        self.new_profile.clicked.connect(self._new_hurtbox_profile)
        self.duplicate_profile.clicked.connect(self._duplicate_hurtbox_profile)
        self.make_override.clicked.connect(self._make_hurtbox_override)
        self.remove_override.clicked.connect(self._remove_hurtbox_override)
        profile_buttons_layout.addWidget(self.new_profile, 0, 0)
        profile_buttons_layout.addWidget(self.duplicate_profile, 0, 1)
        profile_buttons_layout.addWidget(self.make_override, 1, 0)
        profile_buttons_layout.addWidget(self.remove_override, 1, 1)
        sharing_form.addRow("current geometry", self.hurt_source)
        sharing_form.addRow("shared hurtbox", self.hurt_profile)
        sharing_form.addRow("animations affected", self.hurt_used_by)
        sharing_form.addRow("actions", profile_buttons)
        layout.addWidget(sharing)

        selection = QGroupBox("Direct geometry editing")
        selection_form = QFormLayout(selection)
        self.layer = QComboBox()
        for key, label in _LAYER_LABELS.items():
            self.layer.addItem(label, key)
        self.shape = QComboBox()
        self.edit_canvas = QCheckBox("Drag geometry on canvas (turn off to edit bones)")
        self.edit_canvas.setChecked(state.geometry_edit_enabled)
        self.edit_canvas.toggled.connect(state.set_geometry_edit_enabled)
        add_row = QWidget()
        add_layout = QHBoxLayout(add_row)
        add_layout.setContentsMargins(0, 0, 0, 0)
        self.add_kind = QComboBox()
        self.add_kind.addItems(list(SHAPE_KINDS))
        self.add_shape = QPushButton("Add shape")
        self.delete_shape = QPushButton("Delete selected")
        add_layout.addWidget(self.add_kind)
        add_layout.addWidget(self.add_shape)
        add_layout.addWidget(self.delete_shape)
        selection_form.addRow("layer", self.layer)
        selection_form.addRow("shape", self.shape)
        selection_form.addRow("canvas", self.edit_canvas)
        selection_form.addRow("edit", add_row)
        layout.addWidget(selection)

        self.precise = PreciseShapeEditor(self._edit_selected_shape, self._convert_selected_shape)
        layout.addWidget(self.precise)

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

        self.layer.currentIndexChanged.connect(self._layer_changed)
        self.shape.currentIndexChanged.connect(self._shape_changed)
        self.add_shape.clicked.connect(self._add_shape)
        self.delete_shape.clicked.connect(self._delete_shape)
        state.docChanged.connect(self.refresh)
        state.geometryChanged.connect(self.refresh)
        state.geometrySelectionChanged.connect(self.refresh)
        state.geometryVisibilityChanged.connect(self.refresh)
        state.timeChanged.connect(self.refresh)
        self.refresh()

    def _selected_layer(self) -> str:
        return str(self.layer.currentData() or "hurtbox")

    def _selected_shapes(self, *, create: bool = False) -> list[dict]:
        return layer_shapes(
            self.state.doc,
            self.state.geometry_layer,
            self.state.clip_name,
            create=create,
        )

    def _selected_shape(self) -> dict | None:
        shapes = self._selected_shapes()
        index = self.state.geometry_shape_index
        return shapes[index] if 0 <= index < len(shapes) else None

    def _layer_changed(self) -> None:
        if self._refreshing:
            return
        self.state.set_geometry_selection(self._selected_layer(), 0)

    def _shape_changed(self, index: int) -> None:
        if self._refreshing or index < 0:
            return
        self.state.set_geometry_selection(self.state.geometry_layer, index)

    def _add_shape(self) -> None:
        layer = self.state.geometry_layer
        self.state.push_undo()
        entry = layer_entry(self.state.doc, layer, self.state.clip_name, create=True)
        shapes = entry_shapes(entry, create=True)
        shape = default_shape(
            self.add_kind.currentText(),
            self.state.doc.frame,
            name=f"{layer}_{len(shapes) + 1}",
        )
        shapes.append(shape)
        mark_entry_edited(entry)
        self.state.geometry_shape_index = len(shapes) - 1
        self.state.mark_geometry_changed()
        self.state.geometrySelectionChanged.emit()

    def _delete_shape(self) -> None:
        shapes = self._selected_shapes(create=True)
        index = self.state.geometry_shape_index
        if not 0 <= index < len(shapes):
            return
        self.state.push_undo()
        del shapes[index]
        entry = layer_entry(self.state.doc, self.state.geometry_layer, self.state.clip_name)
        mark_entry_edited(entry)
        self.state.geometry_shape_index = max(0, min(index, len(shapes) - 1))
        self.state.mark_geometry_changed()
        self.state.geometrySelectionChanged.emit()

    def _edit_selected_shape(self, changes: dict) -> None:
        shape = self._selected_shape()
        if shape is None:
            return
        if all(shape.get(key) == value for key, value in changes.items()):
            return
        self.state.push_undo()
        for key, value in changes.items():
            if key == "points":
                shape[key] = [[round(float(x), 2), round(float(y), 2)] for x, y in value]
            elif key == "name":
                shape[key] = str(value)
            else:
                shape[key] = round(float(value), 2)
        mark_entry_edited(layer_entry(self.state.doc, self.state.geometry_layer, self.state.clip_name))
        self.state.mark_geometry_changed()

    def _convert_selected_shape(self, kind: str) -> None:
        shapes = self._selected_shapes(create=True)
        index = self.state.geometry_shape_index
        if not 0 <= index < len(shapes):
            return
        if shapes[index].get("kind", "rect") == kind:
            return
        self.state.push_undo()
        shapes[index] = convert_shape(shapes[index], kind)
        mark_entry_edited(layer_entry(self.state.doc, self.state.geometry_layer, self.state.clip_name))
        self.state.mark_geometry_changed()

    def _assign_selected_profile(self, _index: int) -> None:
        if self._refreshing:
            return
        profile_name = self.hurt_profile.currentData()
        if not profile_name:
            return
        source = hurtbox_source(self.state.doc, self.state.clip_name)
        if source.profile_name == profile_name and not source.is_override:
            return
        self.state.push_undo()
        assign_hurtbox_profile(self.state.doc, self.state.clip_name, str(profile_name))
        self.state.geometry_shape_index = 0
        self.state.mark_geometry_changed()
        self.state.geometrySelectionChanged.emit()

    def _profile_name_prompt(self, title: str, default: str) -> str | None:
        text, accepted = QInputDialog.getText(self, title, "Profile name", text=default)
        if not accepted or not text.strip():
            return None
        return text.strip()

    def _new_hurtbox_profile(self) -> None:
        name = self._profile_name_prompt("Create hurtbox profile", self.state.clip_name)
        if name is None:
            return
        self.state.push_undo()
        profile_name = create_hurtbox_profile(self.state.doc, name)
        assign_hurtbox_profile(self.state.doc, self.state.clip_name, profile_name)
        self.state.geometry_layer = "hurtbox"
        self.state.geometry_shape_index = 0
        self.state.mark_geometry_changed()
        self.state.geometrySelectionChanged.emit()

    def _duplicate_hurtbox_profile(self) -> None:
        source = hurtbox_source(self.state.doc, self.state.clip_name)
        if source.entry is None:
            return
        base = f"{source.profile_name or self.state.clip_name}_copy"
        name = self._profile_name_prompt("Duplicate hurtbox geometry", base)
        if name is None:
            return
        self.state.push_undo()
        profile_name = create_hurtbox_profile(self.state.doc, name, source_entry=source.entry)
        assign_hurtbox_profile(self.state.doc, self.state.clip_name, profile_name)
        self.state.geometry_layer = "hurtbox"
        self.state.geometry_shape_index = 0
        self.state.mark_geometry_changed()
        self.state.geometrySelectionChanged.emit()

    def _make_hurtbox_override(self) -> None:
        source = hurtbox_source(self.state.doc, self.state.clip_name)
        if source.is_override:
            return
        self.state.push_undo()
        make_hurtbox_override(self.state.doc, self.state.clip_name)
        self.state.geometry_layer = "hurtbox"
        self.state.geometry_shape_index = 0
        self.state.mark_geometry_changed()
        self.state.geometrySelectionChanged.emit()

    def _remove_hurtbox_override(self) -> None:
        source = hurtbox_source(self.state.doc, self.state.clip_name)
        if not source.is_override or not source.profile_name:
            return
        self.state.push_undo()
        if not remove_hurtbox_override(self.state.doc, self.state.clip_name):
            self.state.discard_last_undo()
            return
        self.state.geometry_shape_index = 0
        self.state.mark_geometry_changed()
        self.state.geometrySelectionChanged.emit()

    def _confirm_replace(self, noun: str) -> bool:
        return QMessageBox.question(
            self,
            f"Replace {noun}?",
            f"{noun.capitalize()} already exists. Replace it with newly generated authoring data?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes

    def _run_generator(self, fn, noun: str, layer: str) -> None:
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
            self.state.discard_last_undo()
            QMessageBox.critical(self, f"Generate {noun}", str(ex))
            return
        finally:
            if app is not None:
                app.restoreOverrideCursor()
        self.state.geometry_layer = layer
        self.state.geometry_shape_index = 0
        self.state.mark_geometry_changed()
        self.state.geometrySelectionChanged.emit()
        window = self.window()
        if hasattr(window, "statusBar"):
            window.statusBar().showMessage(result.message, 5000)

    def _generate_collision(self) -> None:
        self._run_generator(
            lambda replace: generate_collision(self.state.doc, replace=replace),
            "collision",
            "collision",
        )

    def _generate_hurt(self) -> None:
        self._run_generator(
            lambda replace: generate_hurtboxes(self.state.doc, replace=replace),
            "hurtbox profiles",
            "hurtbox",
        )

    def _generate_hit(self) -> None:
        clip = self.state.clip_name
        self._run_generator(
            lambda replace: generate_hitbox(self.state.doc, clip, replace=replace),
            f"hitbox for {clip}",
            "hitbox",
        )

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
        mark_entry_edited(entry)
        self.state.mark_geometry_changed()

    def _refresh_hurtbox_source(self, doc) -> None:
        source = hurtbox_source(doc, self.state.clip_name)
        profiles = hurtbox_profiles(doc)
        binding = hurtbox_clip_binding(doc, self.state.clip_name) or {}

        self.hurt_profile.clear()
        self.hurt_profile.addItem("No profile assigned", None)
        for profile_name in sorted(profiles):
            self.hurt_profile.addItem(profile_name, profile_name)
        assigned = binding.get("profile") if isinstance(binding, dict) else None
        index = self.hurt_profile.findData(assigned)
        self.hurt_profile.setCurrentIndex(max(0, index))

        if source.kind == "profile":
            self.hurt_source.setText(
                f"Shared profile '{source.profile_name}'. Editing it changes every linked clip."
            )
        elif source.kind == "override":
            self.hurt_source.setText(
                f"Local override of '{source.profile_name}'. Editing affects only {self.state.clip_name}."
            )
        elif source.kind == "legacy_override":
            self.hurt_source.setText(
                "Legacy per-clip geometry. Assign or duplicate it into a named profile to share it."
            )
        else:
            self.hurt_source.setText("Missing. Generate profiles or assign a profile.")

        users = hurtbox_profile_users(doc, str(assigned)) if assigned else ()
        if users:
            preview = ", ".join(users[:12])
            if len(users) > 12:
                preview += f", … (+{len(users) - 12})"
            self.hurt_used_by.setText(f"{len(users)} clip(s): {preview}")
        else:
            self.hurt_used_by.setText("No clips use a shared profile.")

        self.duplicate_profile.setEnabled(source.entry is not None)
        self.make_override.setEnabled(source.entry is not None and not source.is_override)
        self.remove_override.setEnabled(source.is_override and bool(source.profile_name))

    def refresh(self) -> None:
        self._refreshing = True
        try:
            doc = self.state.doc
            self.show_collision.setChecked(self.state.show_collision_geometry)
            self.show_hurt.setChecked(self.state.show_hurtbox_geometry)
            self.show_hit.setChecked(self.state.show_hitbox_geometry)
            self.edit_canvas.setChecked(self.state.geometry_edit_enabled)

            root = geometry_root(doc, create=False)
            collision = collision_entry(doc)
            profiles = hurtbox_profiles(doc)
            hit_clips = root.get("hitboxes", {}).get("clips", {})
            attack_count = len(attack_like_clips(doc))
            current_hit = hitbox_entry(doc, self.state.clip_name)

            collision_count = len(entry_shapes(collision))
            hurt_count = sum(
                bool(entry_shapes(hurtbox_entry(doc, clip_name)))
                for clip_name in doc.clips
            )
            overrides = sum(
                hurtbox_source(doc, clip_name).is_override for clip_name in doc.clips
            )
            hit_count = sum(bool(entry_shapes(entry)) for entry in hit_clips.values())
            self.collision_summary.setText(
                f"{collision_count} global shape(s)" if collision_count else "missing"
            )
            self.hurt_summary.setText(
                f"{hurt_count} / {len(doc.clips)} clips via {len(profiles)} shared profile(s)"
                + (f" and {overrides} local override(s)" if overrides else "")
            )
            current_status = f"{len(entry_shapes(current_hit))} shape(s)" if current_hit else "missing"
            self.hit_summary.setText(
                f"{hit_count} / {attack_count} attack-like clips; "
                f"{self.state.clip_name}: {current_status}"
            )
            self._refresh_hurtbox_source(doc)

            layer_index = self.layer.findData(self.state.geometry_layer)
            self.layer.setCurrentIndex(max(0, layer_index))
            shapes = self._selected_shapes()
            self.state.geometry_shape_index = max(
                0, min(self.state.geometry_shape_index, len(shapes) - 1)
            )
            self.shape.clear()
            for index, shape in enumerate(shapes):
                label = shape.get("name") or f"{shape.get('kind', 'rect')} {index + 1}"
                self.shape.addItem(
                    f"{index + 1}: {label} [{shape.get('kind', 'rect')}]"
                )
            if shapes:
                self.shape.setCurrentIndex(self.state.geometry_shape_index)
            self.shape.setEnabled(bool(shapes))
            self.delete_shape.setEnabled(bool(shapes))
            self.precise.set_shape(self._selected_shape())

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
