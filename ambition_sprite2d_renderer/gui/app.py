"""Main window for the rig editor.

Launch with::

    python -m ambition_sprite2d_renderer.gui [path/to/file.rig.json]

File → New starts from the bundled player_robot_fable template (or an
empty biped stub); Save As suggests ``targets/characters/rigged/`` so the
character auto-registers as a sheet target; Export renders the standard
spritesheet bundle + per-clip GIFs without leaving the editor.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QFileDialog,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QTabWidget,
    QToolBar,
)

from ..authoring.rigdoc import RigDocument, render_gifs_for_doc, render_sheet_for_doc
from .animation_preview import AnimationPreviewPanel
from .canvas import CanvasWidget
from .geometry_panel import GeometryPanel
from .panels import BonesPanel, PalettePanel, PartsPanel
from .state import EditorState
from .timeline import TimelinePanel

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "data" / "rig_templates"
RIGGED_DIR = Path(__file__).resolve().parent.parent / "targets" / "characters" / "rigged"


class MainWindow(QMainWindow):
    def __init__(self, state: EditorState) -> None:
        super().__init__()
        self.state = state
        self.canvas = CanvasWidget(state)
        self.setCentralWidget(self.canvas)
        self.canvas.statusMessage.connect(lambda m: self.statusBar().showMessage(m, 4000))

        left = QDockWidget("Bones", self)
        left.setWidget(BonesPanel(state))
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, left)

        right = QDockWidget("Parts / Palette", self)
        tabs = QTabWidget()
        tabs.addTab(PartsPanel(state), "Parts")
        tabs.addTab(PalettePanel(state), "Palette")
        tabs.addTab(GeometryPanel(state), "Geometry")
        right.setWidget(tabs)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, right)

        self.preview_dock = QDockWidget("Live Loop Preview", self)
        self.preview = AnimationPreviewPanel(state)
        self.preview_dock.setWidget(self.preview)
        self.preview_dock.setMinimumWidth(250)
        self.preview_dock.setMinimumHeight(230)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.preview_dock)
        self.splitDockWidget(right, self.preview_dock, Qt.Orientation.Vertical)

        bottom = QDockWidget("Timeline", self)
        self.timeline = TimelinePanel(state)
        bottom.setWidget(self.timeline)
        bottom.setMinimumHeight(300)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, bottom)

        self._build_menus()
        state.geometryVisibilityChanged.connect(self._sync_view_actions)
        state.geometrySelectionChanged.connect(self._sync_view_actions)
        state.viewOptionsChanged.connect(self._sync_view_actions)
        self._sync_view_actions()
        state.docChanged.connect(self._refresh_title)
        state.dirtyChanged.connect(self._refresh_title)
        self._refresh_title()
        self.resize(1480, 920)

    # ---- menus ------------------------------------------------------------------

    def _build_menus(self) -> None:
        bar = self.menuBar()
        filem = bar.addMenu("&File")
        self._action(filem, "New from template…", "Ctrl+N", self.new_from_template)
        self._action(filem, "New empty", None, self.new_empty)
        self._action(filem, "Open…", "Ctrl+O", self.open_doc)
        filem.addSeparator()
        self._action(filem, "Save", "Ctrl+S", self.save)
        self._action(filem, "Save As…", "Ctrl+Shift+S", self.save_as)
        filem.addSeparator()
        self._action(filem, "Export spritesheet + GIFs…", "Ctrl+E", self.export_bundle)
        self._action(filem, "Export as Python target…", None, self.export_python)
        filem.addSeparator()
        self._action(filem, "Quit", "Ctrl+Q", self.close)

        editm = bar.addMenu("&Edit")
        self._action(editm, "Undo", QKeySequence.StandardKey.Undo, self._undo)
        self._action(editm, "Redo", QKeySequence.StandardKey.Redo, self._redo)
        editm.addSeparator()
        self._action(editm, "Copy pose", "Ctrl+Shift+C", self._copy_pose)
        self._action(editm, "Paste pose", "Ctrl+Shift+V", self._paste_pose)
        editm.addSeparator()
        self._action(editm, "Mark / unmark key pose", "P", self.timeline._toggle_pose_key)
        self._action(editm, "Key selected", "I", self.timeline._key_selected_here)
        self._action(editm, "Key full pose", "Shift+I", self.timeline._key_full_pose_here)
        self._action(editm, "Previous key pose", "[", self.timeline._jump_previous_pose)
        self._action(editm, "Next key pose", "]", self.timeline._jump_next_pose)
        editm.addSeparator()
        self._action(editm, "Rename character…", None, self.rename_character)
        self._action(editm, "Frame settings…", None, self.frame_settings)
        self._action(editm, "Edit document JSON in $VISUAL", "Ctrl+J", self.edit_doc_in_visual)

        viewm = bar.addMenu("&View")
        toolbar = QToolBar("Viewport overlays", self)
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.addToolBar(toolbar)
        self._view_actions: dict[str, QAction] = {}

        def overlay_action(key, text, shortcut, checked, callback, tooltip):
            action = self._action(viewm, text, shortcut, callback, checkable=True)
            action.setChecked(checked)
            action.setToolTip(tooltip)
            toolbar.addAction(action)
            self._view_actions[key] = action
            return action

        overlay_action(
            "bones", "Bones", "B", True, self._toggle_bones,
            "Show the current skeleton and draggable joints",
        )
        overlay_action(
            "key_ghosts", "Key ghosts", "K", True, self._toggle_key_ghosts,
            "Ghost the previous and next important poses",
        )
        overlay_action(
            "frame_onion", "Frame onion", "O", False, self._toggle_onion,
            "Also ghost the immediately adjacent frames",
        )
        overlay_action(
            "motion_trail", "Motion trail", "T", True, self._toggle_motion_trail,
            "Trace the selected bone endpoint through the complete clip",
        )
        overlay_action(
            "chain_ghosts", "In-betweens", "G", True, self._toggle_chain_ghosts,
            "Show intermediate poses for the selected bone chain",
        )
        toolbar.addSeparator()
        viewm.addSeparator()
        overlay_action(
            "collision", "Collision", None, True, self._toggle_collision,
            "Show global movement collision geometry",
        )
        overlay_action(
            "hurt", "Hurt", None, True, self._toggle_hurt,
            "Show the current clip's resolved hurtbox profile",
        )
        overlay_action(
            "hit", "Hit", None, True, self._toggle_hit,
            "Show hitboxes and their active/inactive state",
        )
        overlay_action(
            "geometry_edit", "Edit geometry", "E", False, self._toggle_geometry_edit,
            "Let gameplay geometry intercept canvas dragging; turn off to edit bones",
        )
        toolbar.addSeparator()
        viewm.addSeparator()
        self._action(viewm, "Show all overlays", None, self._show_all_overlays)
        viewm.addSeparator()
        preview_action = self.preview_dock.toggleViewAction()
        preview_action.setText("Live loop preview")
        viewm.addAction(preview_action)
        fit_action = self._action(viewm, "Fit view", "F", self.canvas.fit)
        toolbar.addAction(fit_action)

    def _action(self, menu, text, shortcut, fn, checkable=False) -> QAction:
        act = QAction(text, self)
        if shortcut:
            act.setShortcut(QKeySequence(shortcut))
        act.setCheckable(checkable)
        if checkable:
            act.toggled.connect(fn)
        else:
            act.triggered.connect(fn)
        menu.addAction(act)
        return act

    def _sync_view_actions(self) -> None:
        """Keep toolbar state synchronized with controls in other panels."""
        if not hasattr(self, "_view_actions"):
            return
        values = {
            "bones": self.canvas.show_bones,
            "key_ghosts": self.state.show_key_pose_ghosts,
            "frame_onion": self.state.show_frame_onion,
            "motion_trail": self.state.show_motion_trail,
            "chain_ghosts": self.state.show_intermediate_chain_ghosts,
            "collision": self.state.show_collision_geometry,
            "hurt": self.state.show_hurtbox_geometry,
            "hit": self.state.show_hitbox_geometry,
            "geometry_edit": self.state.geometry_edit_enabled,
        }
        for key, checked in values.items():
            action = self._view_actions.get(key)
            if action is None:
                continue
            previous = action.blockSignals(True)
            action.setChecked(bool(checked))
            action.blockSignals(previous)

    # ---- file ops -----------------------------------------------------------------

    def _confirm_discard(self) -> bool:
        if not self.state.dirty:
            return True
        ret = QMessageBox.question(
            self,
            "Unsaved changes",
            "Discard unsaved changes?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return ret == QMessageBox.StandardButton.Yes

    def new_from_template(self) -> None:
        if not self._confirm_discard():
            return
        templates = sorted(TEMPLATE_DIR.glob("*.rig.json"))
        if not templates:
            self.new_empty()
            return
        names = [p.name for p in templates]
        name, ok = QInputDialog.getItem(self, "New character", "Template:", names, 0, False)
        if not ok:
            return
        doc = RigDocument.load(TEMPLATE_DIR / name)
        new_name, ok = QInputDialog.getText(self, "New character", "Character name:", text=doc.name)
        if ok and new_name.strip():
            doc.data["name"] = new_name.strip()
        self.state.set_doc(doc, None)
        self.canvas.fit()
        self.timeline.refresh()

    def new_empty(self) -> None:
        if not self._confirm_discard():
            return
        name, ok = QInputDialog.getText(self, "New character", "Character name:", text="new_character")
        if not ok:
            return
        self.state.set_doc(RigDocument.new_empty(name.strip() or "new_character"), None)
        self.canvas.fit()
        self.timeline.refresh()

    def open_doc(self) -> None:
        if not self._confirm_discard():
            return
        start = str(RIGGED_DIR if RIGGED_DIR.is_dir() else Path.cwd())
        path, _ = QFileDialog.getOpenFileName(self, "Open rig", start, "Rig documents (*.rig.json)")
        if not path:
            return
        try:
            doc = RigDocument.load(path)
        except Exception as ex:  # noqa: BLE001
            QMessageBox.critical(self, "Open rig", f"Failed to load:\n{ex}")
            return
        self.state.set_doc(doc, path)
        self.canvas.fit()
        self.timeline.refresh()

    def save(self) -> None:
        if not self.state.path:
            self.save_as()
            return
        self.state.doc.save(self.state.path)
        self.state.dirty = False
        self._refresh_title()
        self.statusBar().showMessage(f"Saved {self.state.path}", 4000)

    def save_as(self) -> None:
        RIGGED_DIR.mkdir(parents=True, exist_ok=True)
        suggested = str(RIGGED_DIR / f"{self.state.doc.name}.rig.json")
        path, _ = QFileDialog.getSaveFileName(self, "Save rig", suggested, "Rig documents (*.rig.json)")
        if not path:
            return
        if not path.endswith(".rig.json"):
            path += ".rig.json"
        self.state.path = path
        self.save()

    def rename_character(self) -> None:
        name, ok = QInputDialog.getText(self, "Rename character", "Name:", text=self.state.doc.name)
        name = name.strip()
        if not ok or not name:
            return
        self.state.push_undo()
        self.state.doc.data["name"] = name
        self.state.mark_changed()
        self._refresh_title()

    def export_bundle(self) -> None:
        start = self.state.path and str(Path(self.state.path).parent) or str(Path.cwd())
        out = QFileDialog.getExistingDirectory(self, "Export into directory", start)
        if not out:
            return
        app = QApplication.instance()
        app.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            paths = render_sheet_for_doc(self.state.doc, Path(out))
            paths += render_gifs_for_doc(self.state.doc, Path(out) / "gifs")
        except Exception as ex:  # noqa: BLE001
            app.restoreOverrideCursor()
            QMessageBox.critical(self, "Export", f"Export failed:\n{ex}")
            return
        app.restoreOverrideCursor()
        self.statusBar().showMessage(f"Exported {len(paths)} files to {out}", 8000)

    def export_python(self) -> None:
        """Generate a readable Python target module from the document."""
        from ..authoring.rigdoc_codegen import doc_to_python

        targets_dir = RIGGED_DIR.parent
        suggested = str(targets_dir / f"{self.state.doc.name}.py")
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Python target", suggested, "Python modules (*.py)"
        )
        if not path:
            return
        Path(path).write_text(doc_to_python(self.state.doc), encoding="utf8")
        self.statusBar().showMessage(
            f"Wrote {path} — it registers as a sheet target when saved under "
            f"targets/characters/ (rename if a rigged/*.rig.json shares the name)",
            10000,
        )

    def frame_settings(self) -> None:
        """Edit canvas/output geometry, including render_scale (output
        resolution multiplier — geometry stays authored in base units)."""
        from PySide6.QtWidgets import (
            QDialog,
            QDialogButtonBox,
            QDoubleSpinBox,
            QFormLayout,
            QSpinBox,
        )

        fr = self.state.doc.frame
        dlg = QDialog(self)
        dlg.setWindowTitle("Frame settings")
        form = QFormLayout(dlg)

        def ispin(value, lo, hi):
            s = QSpinBox()
            s.setRange(lo, hi)
            s.setValue(int(value))
            return s

        def dspin(value, lo, hi):
            s = QDoubleSpinBox()
            s.setRange(lo, hi)
            s.setDecimals(2)
            s.setValue(float(value))
            return s

        width = ispin(fr.get("width", 128), 16, 2048)
        height = ispin(fr.get("height", 128), 16, 2048)
        render_scale = ispin(fr.get("render_scale", 1), 1, 8)
        supersample = ispin(fr.get("supersample", 4), 1, 8)
        ground_y = dspin(fr.get("ground_y", 101.0), 0, 2048)
        center_x = dspin(fr.get("center_x", 64.0), 0, 2048)
        ankle_h = dspin(fr.get("ankle_h", 2.6), 0, 64)
        form.addRow("width (authoring units)", width)
        form.addRow("height (authoring units)", height)
        form.addRow("render scale (output ×)", render_scale)
        form.addRow("supersample (AA ×)", supersample)
        form.addRow("ground y", ground_y)
        form.addRow("center x", center_x)
        form.addRow("ankle height", ankle_h)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        form.addRow(buttons)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        self.state.push_undo()
        fr.update(
            width=width.value(),
            height=height.value(),
            render_scale=render_scale.value(),
            supersample=supersample.value(),
            ground_y=ground_y.value(),
            center_x=center_x.value(),
            ankle_h=ankle_h.value(),
        )
        self.state.mark_changed()
        self.canvas.fit()

    def edit_doc_in_visual(self) -> None:
        import json

        from .external import edit_text_in_visual, visual_command

        if visual_command() is None:
            QMessageBox.warning(self, "$VISUAL", "Set $VISUAL (or $EDITOR) to use this.")
            return
        self.statusBar().showMessage("Waiting for $VISUAL to exit…")
        edited = edit_text_in_visual(json.dumps(self.state.doc.data, indent=1))
        self.statusBar().clearMessage()
        if edited is None:
            return
        try:
            data = json.loads(edited)
            if not isinstance(data, dict):
                raise ValueError("document must be a JSON object")
        except Exception as ex:  # noqa: BLE001
            QMessageBox.critical(self, "$VISUAL", f"Edited JSON is invalid:\n{ex}")
            return
        self.state.push_undo()
        self.state.doc.data = data
        self.state._after_history_swap()  # revalidate clip/selection, emit signals
        self.state.dirty = True

    # ---- edit ops -----------------------------------------------------------------

    def _copy_pose(self) -> None:
        n = self.state.copy_pose()
        self.statusBar().showMessage(
            f"Copied pose ({n} channels) from {self.state.clip_name}"
            f"@{self.state.frame_idx}", 4000,
        )

    def _paste_pose(self) -> None:
        n = self.state.paste_pose()
        if n:
            self.statusBar().showMessage(
                f"Pasted pose ({n} channels) at {self.state.clip_name}"
                f"@{self.state.frame_idx}", 4000,
            )
        else:
            self.statusBar().showMessage("Pose clipboard is empty", 2000)

    def _undo(self) -> None:
        if not self.state.undo():
            self.statusBar().showMessage("Nothing to undo", 2000)

    def _redo(self) -> None:
        if not self.state.redo():
            self.statusBar().showMessage("Nothing to redo", 2000)

    def _toggle_bones(self, checked: bool) -> None:
        self.canvas.show_bones = checked
        self.canvas.update()
        self._sync_view_actions()

    def _toggle_key_ghosts(self, checked: bool) -> None:
        self.state.set_view_options(key_pose_ghosts=checked)

    def _toggle_onion(self, checked: bool) -> None:
        self.canvas.onion_skin = False
        self.state.set_view_options(frame_onion=checked)

    def _toggle_motion_trail(self, checked: bool) -> None:
        self.state.set_view_options(motion_trail=checked)

    def _toggle_chain_ghosts(self, checked: bool) -> None:
        self.state.set_view_options(intermediate_chain_ghosts=checked)

    def _toggle_collision(self, checked: bool) -> None:
        self.state.set_geometry_visibility(collision=checked)

    def _toggle_hurt(self, checked: bool) -> None:
        self.state.set_geometry_visibility(hurtbox=checked)

    def _toggle_hit(self, checked: bool) -> None:
        self.state.set_geometry_visibility(hitbox=checked)

    def _toggle_geometry_edit(self, checked: bool) -> None:
        self.state.set_geometry_edit_enabled(checked)
        self.statusBar().showMessage(
            "Gameplay geometry editing enabled" if checked else "Bone animation editing enabled",
            2500,
        )

    def _show_all_overlays(self) -> None:
        for key in (
            "bones", "key_ghosts", "frame_onion", "motion_trail", "chain_ghosts",
            "collision", "hurt", "hit",
        ):
            self._view_actions[key].setChecked(True)

    def _refresh_title(self) -> None:
        star = " *" if self.state.dirty else ""
        path = self.state.path or "(unsaved)"
        self.setWindowTitle(f"{self.state.doc.name} — {path}{star} — Ambition Rig Editor")
