"""Viewport for the rig editor: rendered frame + bone overlay + direct
manipulation.

Interactions:
- wheel: zoom (about the cursor); middle-drag (or space-drag): pan
- left-click near a joint: select that bone
- drag a selected FK bone: rotate it — writes a key at the current frame
- Alt+drag a bone two FK levels deep (a hand, a free foot): EDITOR-SIDE
  limb IK — the drag places the bone's origin and writes pose keys for
  its parent and grandparent (the document stays plain FK; the solver is
  only an input device). The elbow/knee keeps the side it currently bends
  toward.
- Ctrl+drag any joint: move the bone's ATTACHMENT OFFSET (rig structure,
  not animation — edits ``bone.offset`` in parent-local space)
- drag an IK foot: move its ankle target — writes ``<prefix>_x`` /
  ``<prefix>_lift`` keys (planted feet are world-anchored, so the drag is
  in world space)
- IK upper/lower leg bones refuse to rotate (the foot drives them)
"""

from __future__ import annotations

import math
from typing import Dict, Optional, Tuple

from PIL import Image
from PySide6.QtCore import QPoint, QPointF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ..authoring.skeleton import BoneWorld, two_bone_ik
from .state import EditorState

Point = Tuple[float, float]

SELECT_RADIUS_PX = 12.0


def pil_to_qimage(img: Image.Image) -> QImage:
    data = img.tobytes("raw", "RGBA")
    qimg = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)
    return qimg.copy()  # detach from the Python buffer


class CanvasWidget(QWidget):
    statusMessage = Signal(str)

    def __init__(self, state: EditorState, parent=None) -> None:
        super().__init__(parent)
        self.state = state
        self.zoom = 4.0
        self.pan = QPointF(0, 0)  # frame-space origin offset in widget px
        self.show_bones = True
        self.onion_skin = False
        self._fitted = False
        self._drag_mode: Optional[str] = None  # "rotate" | "foot" | "limb_ik" | "offset" | "pan"
        self._drag_bone: Optional[str] = None
        self._ik_bend: float = 1.0
        self._pan_anchor = QPoint()
        self.setMinimumSize(360, 360)
        self.setMouseTracking(False)
        state.docChanged.connect(self.update)
        state.timeChanged.connect(self.update)
        state.selectionChanged.connect(self.update)

    # ---- coordinate transforms ------------------------------------------------

    def frame_to_widget(self, p: Point) -> QPointF:
        return QPointF(p[0] * self.zoom + self.pan.x(), p[1] * self.zoom + self.pan.y())

    def widget_to_frame(self, pos: QPointF) -> Point:
        return ((pos.x() - self.pan.x()) / self.zoom, (pos.y() - self.pan.y()) / self.zoom)

    def fit(self) -> None:
        fr = self.state.doc.frame
        fw, fh = float(fr["width"]), float(fr["height"])
        if fw <= 0 or fh <= 0:
            return
        self.zoom = max(1.0, min(self.width() / fw, self.height() / fh) * 0.92)
        self.pan = QPointF(
            (self.width() - fw * self.zoom) / 2.0,
            (self.height() - fh * self.zoom) / 2.0,
        )
        self.update()

    def resizeEvent(self, event) -> None:
        if not self._fitted:
            self._fitted = True
            self.fit()
        super().resizeEvent(event)

    # ---- painting ------------------------------------------------------------

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(34, 30, 36))
        fr = self.state.doc.frame
        fw, fh = float(fr["width"]), float(fr["height"])
        # Frame bounds + ground line.
        tl = self.frame_to_widget((0, 0))
        painter.setPen(QPen(QColor(80, 74, 84), 1))
        painter.drawRect(int(tl.x()), int(tl.y()), int(fw * self.zoom), int(fh * self.zoom))
        gy = float(fr.get("ground_y", fh - 2))
        g0 = self.frame_to_widget((0, gy))
        g1 = self.frame_to_widget((fw, gy))
        painter.setPen(QPen(QColor(110, 96, 70), 1, Qt.PenStyle.DashLine))
        painter.drawLine(g0, g1)

        clip = self.state.clip_name
        try:
            if self.onion_skin and self.state.frames() > 1:
                for di, alpha in ((-1, 0.22), (1, 0.22)):
                    idx = (self.state.frame_idx + di) % self.state.frames()
                    ghost = self.state.doc.render_at(
                        clip, self.state.doc.frame_time(clip, idx), supersample=2
                    )
                    painter.setOpacity(alpha)
                    self._draw_frame_image(painter, ghost, fw, fh)
                painter.setOpacity(1.0)
            img = self.state.doc.render_at(clip, self.state.t())
            self._draw_frame_image(painter, img, fw, fh)
        except Exception as ex:  # noqa: BLE001 - mid-edit docs can be invalid
            painter.setOpacity(1.0)
            painter.setPen(QPen(QColor(255, 120, 120), 1))
            painter.drawText(20, 30, f"render error: {type(ex).__name__}: {ex}")

        if self.show_bones:
            try:
                world, _params = self.state.doc.solve(clip, self.state.t())
                self._draw_overlay(painter, world)
            except Exception as ex:  # noqa: BLE001
                painter.setPen(QPen(QColor(255, 120, 120), 1))
                painter.drawText(20, 50, f"solve error: {type(ex).__name__}: {ex}")
        painter.end()

    def _draw_frame_image(self, painter: QPainter, img: Image.Image, fw: float, fh: float) -> None:
        qimg = pil_to_qimage(img)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, self.zoom < 3.0)
        tl = self.frame_to_widget((0, 0))
        painter.drawImage(
            QPointF(tl.x(), tl.y()).toPoint().x(),
            QPointF(tl.x(), tl.y()).toPoint().y(),
            qimg.scaled(
                int(fw * self.zoom),
                int(fh * self.zoom),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.FastTransformation
                if self.zoom >= 3.0
                else Qt.TransformationMode.SmoothTransformation,
            ),
        )

    def _draw_overlay(self, painter: QPainter, world: Dict[str, BoneWorld]) -> None:
        sel = self.state.selected_bone
        ik_feet = {leg.get("foot") for leg in self.state.doc.ik_legs}
        for name, bw in world.items():
            is_sel = name == sel
            color = QColor(255, 170, 60) if is_sel else QColor(90, 200, 130, 200)
            if name in ik_feet:
                color = QColor(255, 170, 60) if is_sel else QColor(120, 170, 255, 220)
            painter.setPen(QPen(color, 3 if is_sel else 2))
            o = self.frame_to_widget(bw.origin)
            if bw.length > 0:
                tip = self.frame_to_widget(bw.tip)
                painter.drawLine(o, tip)
            r = 5 if is_sel else 4
            painter.drawEllipse(o, r, r)
            if name in ik_feet:
                painter.drawRect(int(o.x()) - 6, int(o.y()) - 6, 12, 12)

    # ---- interaction -----------------------------------------------------------

    def _hit_test(self, pos: QPointF) -> Optional[str]:
        try:
            world, _ = self.state.doc.solve(self.state.clip_name, self.state.t())
        except Exception:  # noqa: BLE001
            return None
        best, best_d = None, SELECT_RADIUS_PX
        for name, bw in world.items():
            for anchor in ((bw.origin, 0.0), (bw.tip, 1.0)) if bw.length > 0 else ((bw.origin, 0.0),):
                wp = self.frame_to_widget(anchor[0])
                d = math.hypot(wp.x() - pos.x(), wp.y() - pos.y())
                if d < best_d:
                    best, best_d = name, d
        return best

    def _fk_chain(self, bone_name: str) -> Optional[Tuple[str, str]]:
        """The two-bone FK chain ending at ``bone_name``'s origin, if any:
        ``(grandparent, parent)`` — both segments real (length > 0) and not
        already driven by a document IK leg."""
        doc = self.state.doc
        bone = doc.bone(bone_name)
        if bone is None or doc.foot_leg_for_bone(bone_name) is not None:
            return None
        lo = doc.bone(bone.get("parent") or "")
        if lo is None or float(lo.get("length", 0.0)) <= 0:
            return None
        up = doc.bone(lo.get("parent") or "")
        if up is None or float(up.get("length", 0.0)) <= 0:
            return None
        return up["name"], lo["name"]

    def _current_bend(self, chain: Tuple[str, str]) -> float:
        """Bend sign that keeps the middle joint on its current side: solve
        both ways for the current tip and pick the closer elbow/knee."""
        try:
            sk = self.state.doc.build_skeleton()
            world, _ = self.state.doc.solve(self.state.clip_name, self.state.t())
        except Exception:  # noqa: BLE001
            return 1.0
        up, lo = chain
        root = world[up].origin
        mid = world[lo].origin
        tip = world[lo].tip
        l1, l2 = sk.bones[up].length, sk.bones[lo].length
        best, best_d = 1.0, float("inf")
        for bend in (1.0, -1.0):
            w1, _w2 = two_bone_ik(root, tip, l1, l2, bend=bend)
            m = (root[0] + l1 * math.cos(math.radians(w1)),
                 root[1] + l1 * math.sin(math.radians(w1)))
            d = math.hypot(m[0] - mid[0], m[1] - mid[1])
            if d < best_d:
                best, best_d = bend, d
        return best

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._drag_mode = "pan"
            self._pan_anchor = event.position().toPoint()
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return
        hit = self._hit_test(event.position())
        if hit != self.state.selected_bone:
            self.state.selected_bone = hit
            self.state.selectionChanged.emit()
        if hit is None:
            self._drag_mode = None
            return
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Structural edit: move the bone's attachment offset.
            self._drag_mode = "offset"
            self._drag_bone = hit
            self.state.push_undo()
            self.statusMessage.emit(f"moving {hit} attachment (Ctrl+drag)")
            return
        if event.modifiers() & Qt.KeyboardModifier.AltModifier:
            chain = self._fk_chain(hit)
            if chain is None:
                self._drag_mode = None
                self.statusMessage.emit(
                    f"{hit} has no two-bone FK chain above it for Alt+drag IK"
                )
                return
            self._drag_mode = "limb_ik"
            self._drag_bone = hit
            self._ik_bend = self._current_bend(chain)
            self.state.push_undo()
            self.statusMessage.emit(
                f"placing {hit} via {chain[0]}+{chain[1]} IK (Alt+drag)"
            )
            return
        leg = self.state.doc.foot_leg_for_bone(hit)
        if leg is not None:
            if hit == leg.get("foot"):
                self._drag_mode = "foot"
                self._drag_bone = hit
                self.state.push_undo()
            else:
                self._drag_mode = None
                self.statusMessage.emit(
                    f"{hit} is IK-driven — drag the foot ({leg.get('foot')}) instead"
                )
        else:
            self._drag_mode = "rotate"
            self._drag_bone = hit
            self.state.push_undo()

    def mouseMoveEvent(self, event) -> None:
        if self._drag_mode == "pan":
            delta = event.position().toPoint() - self._pan_anchor
            self._pan_anchor = event.position().toPoint()
            self.pan += QPointF(delta.x(), delta.y())
            self.update()
            return
        if self._drag_mode not in ("rotate", "foot", "offset", "limb_ik") or self._drag_bone is None:
            return
        fp = self.widget_to_frame(event.position())
        if self._drag_mode == "offset":
            self._drag_offset_to(fp)
            return
        if self._drag_mode == "limb_ik":
            self._drag_limb_to(fp)
            return
        if self._drag_mode == "foot":
            leg = self.state.doc.foot_leg_for_bone(self._drag_bone)
            if leg is None:
                return
            fr = self.state.doc.frame
            pre = leg.get("channel_prefix", "foot")
            x_off = fp[0] - float(fr.get("center_x", 64.0))
            lift = (float(fr.get("ground_y", 101.0)) - float(fr.get("ankle_h", 2.6))) - fp[1]
            self.state.write_key(f"{pre}_x", round(x_off, 2))
            self.state.write_key(f"{pre}_lift", round(max(-1.0, lift), 2))
            return
        # rotate
        try:
            sk = self.state.doc.build_skeleton()
            world, _ = self.state.doc.solve(self.state.clip_name, self.state.t())
        except Exception:  # noqa: BLE001
            return
        bw = world.get(self._drag_bone)
        if bw is None:
            return
        desired = math.degrees(math.atan2(fp[1] - bw.origin[1], fp[0] - bw.origin[0]))
        pose = sk.pose_angle_for_world(self._drag_bone, desired, world)
        # Normalize the written pose into (-180, 180] so keys stay sane.
        pose = (pose + 180.0) % 360.0 - 180.0
        self.state.write_key(self._drag_bone, round(pose, 1))

    def _drag_limb_to(self, fp: Point) -> None:
        """Editor-side two-bone IK: place the dragged bone's origin at ``fp``
        by writing FK pose keys for its grandparent and parent."""
        chain = self._fk_chain(self._drag_bone)
        if chain is None:
            return
        try:
            sk = self.state.doc.build_skeleton()
            world, _ = self.state.doc.solve(self.state.clip_name, self.state.t())
        except Exception:  # noqa: BLE001
            return
        up, lo = chain
        root = world[up].origin
        w1, w2 = two_bone_ik(
            root, fp, sk.bones[up].length, sk.bones[lo].length, bend=self._ik_bend
        )
        parent = sk.bones[up].parent
        parent_angle = world[parent].angle if parent else 0.0
        pose_up = w1 - parent_angle - sk.bones[up].rest_angle
        pose_lo = w2 - w1 - sk.bones[lo].rest_angle
        for name, pose in ((up, pose_up), (lo, pose_lo)):
            pose = (pose + 180.0) % 360.0 - 180.0
            self.state.write_key(name, round(pose, 1))

    def _drag_offset_to(self, fp: Point) -> None:
        """Move the dragged bone's attachment so its origin lands at frame
        point ``fp``: new offset = R(-parent_world_angle) · (fp - parent_origin)."""
        bone = self.state.doc.bone(self._drag_bone)
        if bone is None:
            return
        try:
            world, _ = self.state.doc.solve(self.state.clip_name, self.state.t())
        except Exception:  # noqa: BLE001
            return
        bw = world.get(self._drag_bone)
        if bw is None:
            return
        parent = bone.get("parent")
        if parent and parent in world:
            po, pa = world[parent].origin, world[parent].angle
        else:
            # Root bone: parent frame is the root point at angle 0; recover
            # it from the bone's current origin minus its current offset.
            off = bone.get("offset", [0.0, 0.0])
            po, pa = (bw.origin[0] - off[0], bw.origin[1] - off[1]), 0.0
        rel = (fp[0] - po[0], fp[1] - po[1])
        a = math.radians(-pa)
        c, s = math.cos(a), math.sin(a)
        bone["offset"] = [round(rel[0] * c - rel[1] * s, 2), round(rel[0] * s + rel[1] * c, 2)]
        self.state.mark_changed()

    def mouseReleaseEvent(self, event) -> None:
        self._drag_mode = None
        self._drag_bone = None

    def wheelEvent(self, event) -> None:
        factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        old = self.widget_to_frame(event.position())
        self.zoom = max(0.5, min(24.0, self.zoom * factor))
        new_wp = self.frame_to_widget(old)
        self.pan += event.position() - new_wp
        self.update()
