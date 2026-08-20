"""Editable all-poses sheet for the rig editor.

The ordinary single-pose canvas remains the detailed art/geometry surface and
Timeline remains the channel/time surface.  This module is a *second primary
pose-authoring viewport*: every frame is drawn as a skeleton column and the
bones in every column are directly draggable.

Interactions intentionally mirror the main canvas where they are pose-centric:

- click a joint/tip: select that bone and that frame
- drag an FK bone: rotate it and write a key into that column's frame
- Alt+drag a free limb endpoint: solve its two-bone FK chain and write both keys
- drag an IK foot: move the per-frame document IK target
- Ctrl+drag a joint: edit the structural attachment offset (global rig edit)
- double-click the column header: mark/unmark the frame as a key pose

Gameplay geometry and persistent full-clip pins remain on the single-pose
canvas: they are not frame-column pose operations and making them look local in
a sheet would be misleading.
"""

from __future__ import annotations

import math
from typing import Optional, Tuple

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ..authoring.skeleton import two_bone_ik
from .pose_colors import current_pose_color, other_pose_color
from .state import EditorState

Point = Tuple[float, float]
SELECT_RADIUS_PX = 13.0


class PoseSheetCanvas(QWidget):
    """Draw and directly edit one complete resolved skeleton per frame column."""

    statusMessage = Signal(str)

    TOP = 32
    BOTTOM = 26
    GUTTER = 10

    def __init__(self, state: EditorState, parent=None) -> None:
        super().__init__(parent)
        self.state = state
        # Editing, not thumbnail density, is the default. The slider can still
        # compress this to an overview when judging arcs and silhouettes.
        self.column_width = 164
        self.key_poses_only = False
        self.viewport_height = 480
        self._drag_mode: Optional[str] = None  # rotate | foot | limb_ik | offset
        self._drag_bone: Optional[str] = None
        self._drag_frame: Optional[int] = None
        self._drag_column: Optional[int] = None
        self._ik_bend: float = 1.0
        self.setMinimumSize(1, 1)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)
        self.setToolTip(
            "Editable pose sheet. Dragging writes real animation-channel keys. "
            "Header diamonds are pose bookmarks (not interpolation keys); the "
            "gray header bar shows actual channel-key density and a gold dot "
            "means the selected bone/control is explicitly keyed on that frame."
        )
        state.docChanged.connect(self.refresh_geometry)
        state.timeChanged.connect(self.update)
        state.poseChanged.connect(self.update)
        state.poseKeysChanged.connect(self.refresh_geometry)
        state.selectionChanged.connect(self.update)

    # ---- sheet geometry ----------------------------------------------------

    def visible_frames(self) -> list[int]:
        if self.key_poses_only:
            keys, _explicit = self.state.pose_key_frames()
            return list(keys) or [0]
        return list(range(self.state.frames()))

    def set_column_width(self, width: int) -> None:
        width = max(88, min(280, int(width)))
        if width == self.column_width:
            return
        self.column_width = width
        self.refresh_geometry()

    def set_key_poses_only(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if enabled == self.key_poses_only:
            return
        self.key_poses_only = enabled
        self.refresh_geometry()

    def set_viewport_height(self, height: int) -> None:
        height = max(260, int(height))
        if height == self.viewport_height:
            return
        self.viewport_height = height
        self.refresh_geometry()

    def sizeHint(self) -> QSize:  # noqa: N802 - Qt API
        count = max(1, len(self.visible_frames()))
        return QSize(count * self.column_width, self.viewport_height)

    def minimumSizeHint(self) -> QSize:  # noqa: N802 - Qt API
        return QSize(1, 1)

    def refresh_geometry(self) -> None:
        hint = self.sizeHint()
        self.resize(hint.width(), hint.height())
        self.updateGeometry()
        self.update()

    @staticmethod
    def _diamond(center: QPointF, radius: float) -> QPainterPath:
        path = QPainterPath()
        path.moveTo(center.x(), center.y() - radius)
        path.lineTo(center.x() + radius, center.y())
        path.lineTo(center.x(), center.y() + radius)
        path.lineTo(center.x() - radius, center.y())
        path.closeSubpath()
        return path

    def _column_rect(self, column: int) -> QRectF:
        x = column * self.column_width
        return QRectF(float(x), 0.0, float(self.column_width), float(self.height()))

    def _column_at(self, x: float) -> Optional[int]:
        frames = self.visible_frames()
        if not frames:
            return None
        column = int(x // self.column_width)
        return column if 0 <= column < len(frames) else None

    def _frame_transform(self, rect: QRectF) -> tuple[float, float, float]:
        frame = self.state.doc.frame
        fw = max(1.0, float(frame.get("width", 128.0)))
        fh = max(1.0, float(frame.get("height", 128.0)))
        draw_w = max(1.0, rect.width() - 2 * self.GUTTER)
        draw_h = max(1.0, rect.height() - self.TOP - self.BOTTOM)
        scale = min(draw_w / fw, draw_h / fh)
        used_w = fw * scale
        used_h = fh * scale
        ox = rect.left() + (rect.width() - used_w) / 2.0
        oy = rect.top() + self.TOP + (draw_h - used_h) / 2.0
        return scale, ox, oy

    def _map_point(self, point: Point, rect: QRectF) -> QPointF:
        scale, ox, oy = self._frame_transform(rect)
        return QPointF(ox + point[0] * scale, oy + point[1] * scale)

    def _unmap_point(self, point: QPointF, rect: QRectF) -> Point:
        scale, ox, oy = self._frame_transform(rect)
        return ((point.x() - ox) / scale, (point.y() - oy) / scale)

    # ---- skeleton queries --------------------------------------------------

    def _solve_frame(self, frame_idx: int):
        t = self.state.doc.frame_time(self.state.clip_name, frame_idx)
        return self.state.doc.solve(self.state.clip_name, t)[0]

    def _hit_test(self, pos: QPointF, column: int) -> Optional[str]:
        frames = self.visible_frames()
        if not 0 <= column < len(frames):
            return None
        frame_idx = frames[column]
        rect = self._column_rect(column)
        try:
            world = self._solve_frame(frame_idx)
        except Exception:  # noqa: BLE001 - incomplete rigs must stay editable
            return None
        best: Optional[str] = None
        best_score = (SELECT_RADIUS_PX, 2)
        # Origins and tips are both handles. On coincident joints prefer an
        # ORIGIN over its parent's TIP so terminal controls such as an IK foot
        # remain selectable instead of being shadowed by the lower-leg endpoint.
        for name, bone in world.items():
            anchors = [(bone.origin, 0)]
            if bone.length > 0:
                anchors.append((bone.tip, 1))
            for anchor, endpoint_rank in anchors:
                wp = self._map_point(anchor, rect)
                distance = math.hypot(wp.x() - pos.x(), wp.y() - pos.y())
                score = (distance, endpoint_rank)
                if distance < SELECT_RADIUS_PX and score < best_score:
                    best, best_score = name, score
        return best

    def _fk_chain(self, bone_name: str) -> Optional[Tuple[str, str]]:
        doc = self.state.doc
        bone = doc.bone(bone_name)
        if bone is None or doc.foot_leg_for_bone(bone_name) is not None:
            return None
        lower = doc.bone(bone.get("parent") or "")
        if lower is None or float(lower.get("length", 0.0)) <= 0:
            return None
        upper = doc.bone(lower.get("parent") or "")
        if upper is None or float(upper.get("length", 0.0)) <= 0:
            return None
        return str(upper["name"]), str(lower["name"])

    def _current_bend(self, chain: Tuple[str, str]) -> float:
        try:
            skeleton = self.state.doc.build_skeleton()
            world = self._solve_frame(self.state.frame_idx)
        except Exception:  # noqa: BLE001
            return 1.0
        upper, lower = chain
        root = world[upper].origin
        middle = world[lower].origin
        tip = world[lower].tip
        len1 = skeleton.bones[upper].length
        len2 = skeleton.bones[lower].length
        best_bend, best_distance = 1.0, float("inf")
        for bend in (1.0, -1.0):
            world_upper, _world_lower = two_bone_ik(root, tip, len1, len2, bend=bend)
            predicted_middle = (
                root[0] + len1 * math.cos(math.radians(world_upper)),
                root[1] + len1 * math.sin(math.radians(world_upper)),
            )
            distance = math.hypot(
                predicted_middle[0] - middle[0], predicted_middle[1] - middle[1]
            )
            if distance < best_distance:
                best_bend, best_distance = bend, distance
        return best_bend

    # ---- paint -------------------------------------------------------------

    def _draw_skeleton(self, painter: QPainter, frame_idx: int, rect: QRectF) -> None:
        try:
            world = self._solve_frame(frame_idx)
        except Exception as ex:  # noqa: BLE001 - mid-edit rigs can be incomplete
            painter.setPen(QPen(QColor(255, 120, 120), 1))
            painter.drawText(
                rect.adjusted(8, self.TOP, -8, -8),
                Qt.AlignmentFlag.AlignCenter,
                f"solve error\n{type(ex).__name__}",
            )
            return

        selected = self.state.selected_bone
        current = frame_idx == self.state.frame_idx
        for name, bone in world.items():
            active = current and name == selected
            color = QColor(255, 177, 78) if active else QColor(100, 214, 154, 220)
            painter.setPen(QPen(color, 3.0 if active else 1.8))
            origin = self._map_point(bone.origin, rect)
            if bone.length > 0:
                painter.drawLine(origin, self._map_point(bone.tip, rect))
            radius = 4.8 if active else 3.2
            painter.setBrush(QBrush(color))
            painter.drawEllipse(origin, radius, radius)
            # Tips are handles too. A tiny ring makes endpoint IK discoverable.
            if bone.length > 0:
                tip = self._map_point(bone.tip, rect)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(tip, 2.5, 2.5)
                painter.setBrush(QBrush(color))

        frame = self.state.doc.frame
        ground_y = float(frame.get("ground_y", frame.get("height", 128.0)))
        start = self._map_point((0.0, ground_y), rect)
        end = self._map_point((float(frame.get("width", 128.0)), ground_y), rect)
        painter.setPen(QPen(QColor(108, 96, 72, 125), 1, Qt.PenStyle.DashLine))
        painter.drawLine(start, end)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(31, 29, 35))

        frames = self.visible_frames()
        pose_keys, explicit = self.state.pose_key_frames()
        pose_key_set = set(pose_keys)
        current = self.state.frame_idx
        key_map = self.state.channel_key_frames()
        selected_channels = set(self.state.selected_animation_channels())
        channel_count = max(1, len(key_map))

        for column, frame_idx in enumerate(frames):
            rect = self._column_rect(column)
            if frame_idx == current:
                painter.fillRect(rect.adjusted(2, 2, -2, -2), QColor(76, 68, 93, 170))
            elif frame_idx in pose_key_set:
                painter.fillRect(rect.adjusted(2, 2, -2, -2), QColor(50, 46, 58, 150))

            painter.setPen(QPen(QColor(74, 70, 80), 1))
            painter.drawLine(rect.topRight(), rect.bottomRight())

            label_color = current_pose_color() if frame_idx == current else QColor(205, 201, 211)
            painter.setPen(QPen(label_color, 1))
            painter.drawText(
                QRectF(rect.left(), 5.0, rect.width(), 20.0),
                Qt.AlignmentFlag.AlignCenter,
                f"frame {frame_idx + 1}",
            )

            if frame_idx in pose_key_set:
                pose_color = current_pose_color() if frame_idx == current else other_pose_color()
                painter.setPen(QPen(pose_color, 1.5))
                painter.setBrush(QBrush(pose_color if explicit else QColor(31, 29, 35)))
                painter.drawPath(
                    self._diamond(QPointF(rect.left() + rect.width() - 13.0, 14.0), 4.5)
                )

            # Raw channel keys are deliberately a DIFFERENT visual language from
            # pose bookmarks. A short gray bar shows how much of this frame is
            # explicitly keyed; a gold dot says the currently selected bone or
            # endpoint control has a key here. This makes sparse interpolation
            # visible without pretending bookmarks drive the animation.
            keyed_count = sum(frame_idx in keyed_frames for keyed_frames in key_map.values())
            if keyed_count:
                density = min(1.0, keyed_count / channel_count)
                bar_w = max(4.0, (rect.width() - 16.0) * density)
                painter.fillRect(
                    QRectF(rect.left() + 8.0, 27.0, bar_w, 3.0),
                    QColor(134, 129, 150, 220),
                )
            if selected_channels and any(
                frame_idx in key_map.get(channel, set()) for channel in selected_channels
            ):
                painter.setPen(QPen(QColor(255, 205, 95), 1.0))
                painter.setBrush(QBrush(QColor(255, 205, 95)))
                painter.drawEllipse(QPointF(rect.left() + 11.0, 14.0), 3.2, 3.2)

            self._draw_skeleton(painter, frame_idx, rect)

        if not frames:
            painter.setPen(QPen(QColor(190, 185, 198), 1))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No frames")
        painter.end()

    # ---- direct pose editing ----------------------------------------------

    def _select_column_frame(self, column: int) -> int:
        frame_idx = self.visible_frames()[column]
        self.state.set_frame(frame_idx)
        return frame_idx

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt API
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return
        column = self._column_at(event.position().x())
        if column is None:
            return
        frame_idx = self._select_column_frame(column)
        hit = self._hit_test(event.position(), column)
        if hit != self.state.selected_bone:
            self.state.selected_bone = hit
            self.state.selected_part = None
            self.state.selectionChanged.emit()
        if hit is None:
            self._drag_mode = None
            event.accept()
            return

        self._drag_bone = hit
        self._drag_frame = frame_idx
        self._drag_column = column
        self.state.push_undo()

        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self._drag_mode = "offset"
            self.statusMessage.emit(
                f"frame {frame_idx + 1}: moving {hit} attachment (Ctrl+drag; structural)"
            )
            event.accept()
            return

        if event.modifiers() & Qt.KeyboardModifier.AltModifier:
            chain = self._fk_chain(hit)
            if chain is None:
                self._drag_mode = None
                self.state.discard_last_undo()
                self.statusMessage.emit(
                    f"{hit} has no free two-bone FK chain for Alt+drag IK"
                )
                event.accept()
                return
            self._drag_mode = "limb_ik"
            self._ik_bend = self._current_bend(chain)
            self.statusMessage.emit(
                f"frame {frame_idx + 1}: placing {hit} via {chain[0]}+{chain[1]} IK"
            )
            event.accept()
            return

        leg = self.state.doc.foot_leg_for_bone(hit)
        plantable = self.state.selected_plantable_foot()
        if plantable is not None:
            self._drag_mode = "foot"
            if not plantable.get("document_ik", False):
                chain = (str(plantable["upper"]), str(plantable["lower"]))
                self._ik_bend = self._current_bend(chain)
            self.statusMessage.emit(f"frame {frame_idx + 1}: placing {hit} with IK")
        elif leg is not None:
            self._drag_mode = None
            self.state.discard_last_undo()
            self.statusMessage.emit(
                f"{hit} is document-IK driven; drag its foot ({leg.get('foot')})"
            )
        else:
            self._drag_mode = "rotate"
            self.statusMessage.emit(f"frame {frame_idx + 1}: rotating {hit}")
        event.accept()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 - Qt API
        if (
            self._drag_mode not in {"rotate", "foot", "limb_ik", "offset"}
            or self._drag_bone is None
            or self._drag_column is None
            or self._drag_frame is None
        ):
            return
        # The shared state should remain on the edited column for the complete
        # drag even if another panel receives a time change meanwhile.
        if self.state.frame_idx != self._drag_frame:
            self.state.set_frame(self._drag_frame)
        frame_point = self._unmap_point(event.position(), self._column_rect(self._drag_column))

        if self._drag_mode == "offset":
            self._drag_offset_to(frame_point)
            return
        if self._drag_mode == "limb_ik":
            self._drag_limb_to(frame_point)
            return
        if self._drag_mode == "foot":
            endpoint = self.state.selected_plantable_foot()
            if endpoint is None:
                return
            if not endpoint.get("document_ik", False):
                self._drag_limb_to(frame_point)
                return
            leg = self.state.doc.foot_leg_for_bone(self._drag_bone)
            if leg is None:
                return
            frame = self.state.doc.frame
            prefix = str(leg.get("channel_prefix", "foot"))
            x_off = frame_point[0] - float(frame.get("center_x", 64.0))
            lift = (
                float(frame.get("ground_y", 101.0))
                - float(frame.get("ankle_h", 2.6))
                - frame_point[1]
            )
            self.state.write_keys(
                {
                    f"{prefix}_x": round(x_off, 2),
                    f"{prefix}_lift": round(max(-1.0, lift), 2),
                }
            )
            return

        # Ordinary FK rotation.
        try:
            skeleton = self.state.doc.build_skeleton()
            world = self._solve_frame(self._drag_frame)
        except Exception:  # noqa: BLE001
            return
        bone = world.get(self._drag_bone)
        if bone is None:
            return
        desired = math.degrees(
            math.atan2(frame_point[1] - bone.origin[1], frame_point[0] - bone.origin[0])
        )
        pose = skeleton.pose_angle_for_world(self._drag_bone, desired, world)
        pose = (pose + 180.0) % 360.0 - 180.0
        self.state.write_key(self._drag_bone, round(pose, 1))

    def _drag_limb_to(self, target: Point) -> None:
        if self._drag_bone is None or self._drag_frame is None:
            return
        chain = self._fk_chain(self._drag_bone)
        if chain is None:
            # An ordinary FK terminal foot is described through the state's
            # plantable endpoint even though the foot itself may be in an IK map.
            endpoint = self.state.selected_plantable_foot()
            if endpoint is None or endpoint.get("document_ik", False):
                return
            chain = (str(endpoint["upper"]), str(endpoint["lower"]))
        try:
            skeleton = self.state.doc.build_skeleton()
            world = self._solve_frame(self._drag_frame)
        except Exception:  # noqa: BLE001
            return
        upper, lower = chain
        root = world[upper].origin
        world_upper, world_lower = two_bone_ik(
            root,
            target,
            skeleton.bones[upper].length,
            skeleton.bones[lower].length,
            bend=self._ik_bend,
        )
        parent = skeleton.bones[upper].parent
        parent_angle = world[parent].angle if parent else 0.0
        upper_pose = world_upper - parent_angle - skeleton.bones[upper].rest_angle
        lower_pose = world_lower - world_upper - skeleton.bones[lower].rest_angle
        values = {}
        for name, pose in ((upper, upper_pose), (lower, lower_pose)):
            pose = (pose + 180.0) % 360.0 - 180.0
            values[name] = round(pose, 1)
        self.state.write_keys(values)

    def _drag_offset_to(self, target: Point) -> None:
        if self._drag_bone is None or self._drag_frame is None:
            return
        bone = self.state.doc.bone(self._drag_bone)
        if bone is None:
            return
        try:
            world = self._solve_frame(self._drag_frame)
        except Exception:  # noqa: BLE001
            return
        bone_world = world.get(self._drag_bone)
        if bone_world is None:
            return
        parent = bone.get("parent")
        if parent and parent in world:
            parent_origin, parent_angle = world[parent].origin, world[parent].angle
        else:
            offset = bone.get("offset", [0.0, 0.0])
            parent_origin = (
                bone_world.origin[0] - float(offset[0]),
                bone_world.origin[1] - float(offset[1]),
            )
            parent_angle = 0.0
        relative = (target[0] - parent_origin[0], target[1] - parent_origin[1])
        angle = math.radians(-parent_angle)
        cosine, sine = math.cos(angle), math.sin(angle)
        bone["offset"] = [
            round(relative[0] * cosine - relative[1] * sine, 2),
            round(relative[0] * sine + relative[1] * cosine, 2),
        ]
        self.state.mark_pose_changed()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 - Qt API
        drag_mode = self._drag_mode
        self._drag_mode = None
        self._drag_bone = None
        self._drag_frame = None
        self._drag_column = None
        if drag_mode == "offset":
            # Structural edits refresh the bone property panel once, not on every
            # motion event.
            self.state.docChanged.emit()
        if drag_mode in {"rotate", "foot", "limb_ik", "offset"}:
            self.state.discard_last_undo_if_unchanged()
        if event is not None:
            event.accept()

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802 - Qt API
        if event.button() == Qt.MouseButton.LeftButton:
            column = self._column_at(event.position().x())
            # Reserve double-click for the header so a fast double-click on an
            # editable joint cannot unexpectedly toggle a pose bookmark.
            if column is not None and event.position().y() <= self.TOP:
                frame_idx = self.visible_frames()[column]
                self.state.push_undo()
                if not self.state.toggle_pose_key(frame_idx):
                    self.state.discard_last_undo()
                self.state.set_frame(frame_idx)
                event.accept()
                return
        super().mouseDoubleClickEvent(event)


class PoseSheetPanel(QWidget):
    """Scrollable primary all-frames pose-authoring surface."""

    def __init__(self, state: EditorState, parent=None) -> None:
        super().__init__(parent)
        self.state = state
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)

        controls = QHBoxLayout()
        description = QLabel(
            "Edit the whole clip directly. ◆ = pose bookmark (hollow = suggested); "
            "gray header bar = real channel-key density; gold dot = selected control keyed. "
            "Alt+drag = limb IK; Ctrl+drag = rig-wide structural edit."
        )
        description.setWordWrap(True)
        controls.addWidget(description, stretch=1)

        self.keys_only = QCheckBox("pose bookmarks only")
        controls.addWidget(self.keys_only)
        controls.addWidget(QLabel("column width"))
        self.column_width = QSlider(Qt.Orientation.Horizontal)
        self.column_width.setRange(88, 280)
        self.column_width.setValue(164)
        self.column_width.setMaximumWidth(220)
        controls.addWidget(self.column_width)
        root.addLayout(controls)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(False)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setMinimumSize(1, 1)
        self.canvas = PoseSheetCanvas(state)
        self.scroll.setWidget(self.canvas)
        root.addWidget(self.scroll, stretch=1)

        self.keys_only.toggled.connect(self.canvas.set_key_poses_only)
        self.column_width.valueChanged.connect(self.canvas.set_column_width)
        state.docChanged.connect(self.canvas.refresh_geometry)
        state.timeChanged.connect(self._ensure_current_visible)
        self.canvas.refresh_geometry()

    def minimumSizeHint(self) -> QSize:  # noqa: N802 - Qt API
        return QSize(1, 1)

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().resizeEvent(event)
        # Width belongs to the frame columns; height belongs to the main-view
        # viewport. This makes the sheet fill the center of the editor instead of
        # looking like a short strip embedded in a dock.
        self.canvas.set_viewport_height(max(260, self.scroll.viewport().height()))

    def _ensure_current_visible(self) -> None:
        frames = self.canvas.visible_frames()
        try:
            column = frames.index(self.state.frame_idx)
        except ValueError:
            self.canvas.update()
            return
        x = column * self.canvas.column_width + self.canvas.column_width // 2
        self.scroll.ensureVisible(x, self.canvas.height() // 2, 32, 24)
        self.canvas.update()
