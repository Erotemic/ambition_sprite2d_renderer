"""Compact dope-sheet style pose/key overview for the rig editor."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from ..authoring.animation_constraints import transform_pins
from ..authoring.gameplay_geometry import hitbox_entry
from .pose_colors import (
    after_pose_color,
    before_pose_color,
    current_pose_color,
    other_pose_color,
)
from .state import EditorState


class KeyframeStrip(QWidget):
    """Show pose bookmarks, per-frame property density, and selected-control keys.

    Single-click changes frame. Double-click marks/unmarks an editorial pose bookmark.
    Pose bookmarks are intentionally separate from raw property keys: generated rigs
    often key every channel on every frame, while artists still need a handful
    of important poses to orient their work.
    """

    def __init__(self, state: EditorState, parent=None) -> None:
        super().__init__(parent)
        self.state = state
        self.selected_channel: Optional[str] = None
        self.setMinimumHeight(116)
        self.setMaximumHeight(132)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)
        self.setToolTip(
            "Click a frame to select it. Double-click a diamond row to mark or "
            "unmark an important pose. Filled diamonds are saved pose bookmarks; "
            "hollow diamonds are automatic suggestions. Blue is the pose before "
            "the current frame; purple is the pose after it. Green bars are "
            "continuous rigid-part pins."
        )
        state.timeChanged.connect(self.update)
        state.poseKeysChanged.connect(self.update)
        state.animationChanged.connect(lambda _channels: self.update())
        state.docChanged.connect(self.update)
        state.geometryChanged.connect(self.update)
        state.constraintsChanged.connect(self.update)

    def set_selected_channel(self, name: Optional[str]) -> None:
        if name != self.selected_channel:
            self.selected_channel = name
            self.update()

    def _frame_x(self, frame: int) -> float:
        frames = max(1, self.state.frames())
        left, right = 24.0, max(25.0, float(self.width()) - 16.0)
        if frames == 1:
            return (left + right) / 2.0
        return left + (right - left) * frame / (frames - 1)

    def _frame_at(self, x: float) -> int:
        frames = max(1, self.state.frames())
        if frames == 1:
            return 0
        left, right = 24.0, max(25.0, float(self.width()) - 16.0)
        ratio = (x - left) / max(1.0, right - left)
        return max(0, min(frames - 1, int(round(ratio * (frames - 1)))))

    @staticmethod
    def _diamond(center: QPointF, radius: float) -> QPainterPath:
        path = QPainterPath()
        path.moveTo(center.x(), center.y() - radius)
        path.lineTo(center.x() + radius, center.y())
        path.lineTo(center.x(), center.y() + radius)
        path.lineTo(center.x() - radius, center.y())
        path.closeSubpath()
        return path

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(31, 29, 35))

        frames = max(1, self.state.frames())
        pose_keys, explicit = self.state.pose_key_frames()
        previous_pose, following_pose = self.state.neighboring_pose_keys()
        pose_key_set = set(pose_keys)
        key_map = self.state.channel_key_frames()
        selected_keys = key_map.get(self.selected_channel, set()) if self.selected_channel else set()
        channel_count = max(1, len(key_map))

        current = self.state.frame_idx
        if frames > 1:
            x0 = self._frame_x(current - 0.5)
            x1 = self._frame_x(current + 0.5)
        else:
            x0, x1 = 8.0, float(self.width()) - 8.0
        painter.fillRect(QRectF(x0, 4.0, max(1.0, x1 - x0), float(self.height()) - 8.0), QColor(74, 67, 91, 110))

        baseline_y = 58.0
        painter.setPen(QPen(QColor(82, 78, 88), 1))
        painter.drawLine(QPointF(20, baseline_y), QPointF(self.width() - 12, baseline_y))

        hit = hitbox_entry(self.state.doc, self.state.clip_name)
        if hit:
            active = hit.get("active_frames") or [0, frames - 1]
            start = max(0, min(frames - 1, int(active[0])))
            end = max(start, min(frames - 1, int(active[-1])))
            if frames > 1:
                half = (self._frame_x(1) - self._frame_x(0)) * 0.42
            else:
                half = 12.0
            painter.setPen(QPen(Qt.PenStyle.NoPen))
            painter.setBrush(QBrush(QColor(255, 75, 75, 145)))
            painter.drawRoundedRect(
                QRectF(
                    self._frame_x(start) - half,
                    54.0,
                    max(5.0, self._frame_x(end) - self._frame_x(start) + 2 * half),
                    5.0,
                ),
                2.5,
                2.5,
            )
            bindings = hit.get("bindings") or {}
            marker_x = self._frame_x(start)
            if bindings.get("vfx"):
                painter.setPen(QPen(QColor(225, 135, 255), 1))
                painter.setBrush(QBrush(QColor(225, 135, 255)))
                painter.drawPath(self._diamond(QPointF(marker_x, 56.5), 3.5))
            if bindings.get("sfx"):
                painter.setPen(QPen(QColor(110, 235, 170), 1))
                painter.setBrush(QBrush(QColor(110, 235, 170)))
                painter.drawEllipse(QPointF(marker_x + 7.0, 56.5), 3.0, 3.0)

        plants = transform_pins(self.state.doc, self.state.clip_name, create=False)
        if frames > 1:
            half = (self._frame_x(1) - self._frame_x(0)) * 0.42
        else:
            half = 12.0
        for plant_index, plant in enumerate(plants[:3]):
            if plant.get("scope") == "clip":
                start, end = 0, frames - 1
            else:
                start = max(0, min(frames - 1, int(plant.get("start_frame", 0))))
                end = max(0, min(frames - 1, int(plant.get("end_frame", frames - 1))))
            y = 70.0 + 10.0 * plant_index
            color = QColor(88, 235, 157, 190 if plant.get("enabled", True) else 70)
            painter.setPen(QPen(color, 1))
            painter.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), 105)))
            segments = [(start, end)] if start <= end else [(start, frames - 1), (0, end)]
            for seg_start, seg_end in segments:
                painter.drawRoundedRect(
                    QRectF(
                        self._frame_x(seg_start) - half,
                        y,
                        max(5.0, self._frame_x(seg_end) - self._frame_x(seg_start) + 2 * half),
                        6.0,
                    ),
                    3.0,
                    3.0,
                )
            bone_name = str(plant.get("bone", "part"))
            short = bone_name.replace("near_", "N:").replace("far_", "F:")
            painter.setPen(QPen(color, 1))
            painter.drawText(QRectF(2.0, y - 4.0, 21.0, 14.0), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, short[:3])

        for frame in range(frames):
            x = self._frame_x(frame)
            keyed_count = sum(frame in values for values in key_map.values())
            density = keyed_count / channel_count

            painter.setPen(QPen(QColor(76, 72, 82), 1))
            painter.drawLine(QPointF(x, 24), QPointF(x, 101))

            if keyed_count:
                bar_h = 3.0 + 9.0 * density
                painter.fillRect(QRectF(x - 2.5, baseline_y - bar_h, 5.0, bar_h), QColor(134, 129, 150, 210))

            if frame in selected_keys:
                painter.setPen(QPen(QColor(255, 205, 95), 1.5))
                painter.setBrush(QBrush(QColor(255, 205, 95)))
                painter.drawEllipse(QPointF(x, 47), 3.5, 3.5)

            if frame in pose_key_set:
                if frame == current:
                    color = current_pose_color()
                    label = "NOW"
                elif frame == previous_pose:
                    color = before_pose_color()
                    label = "BEFORE"
                elif frame == following_pose:
                    color = after_pose_color()
                    label = "AFTER"
                else:
                    color = other_pose_color() if explicit else QColor(149, 189, 205)
                    label = ""
                painter.setPen(QPen(color, 2))
                painter.setBrush(QBrush(color if explicit else QColor(31, 29, 35)))
                painter.drawPath(self._diamond(QPointF(x, 30), 5.0))
                if label:
                    painter.setPen(QPen(color, 1))
                    painter.drawText(
                        QRectF(x - 28, 4, 56, 13),
                        Qt.AlignmentFlag.AlignCenter,
                        label,
                    )

            painter.setPen(QPen(QColor(220, 216, 226) if frame == current else QColor(132, 128, 140), 1))
            painter.drawText(QRectF(x - 10, 101, 20, 14), Qt.AlignmentFlag.AlignCenter, str(frame + 1))

        painter.setPen(QPen(current_pose_color(), 1))
        painter.drawLine(QPointF(self._frame_x(current), 19), QPointF(self._frame_x(current), 104))
        painter.end()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.state.set_frame(self._frame_at(event.position().x()))
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            frame = self._frame_at(event.position().x())
            self.state.push_undo()
            if not self.state.toggle_pose_key(frame):
                self.state.discard_last_undo()
            self.state.set_frame(frame)
            event.accept()
            return
        super().mouseDoubleClickEvent(event)
