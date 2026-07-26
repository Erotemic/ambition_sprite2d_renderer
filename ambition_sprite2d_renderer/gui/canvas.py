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

import copy
import math
from collections import OrderedDict
from typing import Dict, Optional, Tuple

from PIL import Image
from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QImage, QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from ..authoring.gameplay_geometry import (
    collision_entry,
    entry_shapes,
    hitbox_entry,
    hurtbox_entry,
    layer_entry,
    layer_shapes,
    mark_entry_edited,
    point_in_shape,
)
from ..authoring.skeleton import BoneWorld, two_bone_ik
from .state import EditorState

try:
    from line_profiler import profile
except ImportError:  # Optional developer dependency.
    from ..profiling import profile

Point = Tuple[float, float]

SELECT_RADIUS_PX = 12.0
PREVIEW_SUPERSAMPLE = 2
ONION_SUPERSAMPLE = 1
FRAME_CACHE_SIZE = 12
SOLVE_CACHE_SIZE = 24


@profile
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
        self._geometry_drag: Optional[dict] = None
        self._frame_cache: OrderedDict[tuple, QImage] = OrderedDict()
        self._solve_cache: OrderedDict[tuple, tuple] = OrderedDict()
        self.setMinimumSize(360, 360)
        self.setMouseTracking(False)
        state.poseChanged.connect(self._on_render_changed)
        state.timeChanged.connect(self._on_time_changed)
        state.selectionChanged.connect(self.update)
        state.geometryChanged.connect(self.update)
        state.geometryVisibilityChanged.connect(self.update)
        state.geometrySelectionChanged.connect(self.update)

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

    def _on_render_changed(self) -> None:
        self._frame_cache.clear()
        self._solve_cache.clear()
        self.update()

    def _on_time_changed(self) -> None:
        self.update()

    def _preview_supersample(self) -> int:
        """Return one stable preview quality for all editor interactions.

        Switching between 1x during a click/drag and 2x after a short timer made
        the sprite visibly pop even when the user merely selected a bone. The
        optimized part compositor is fast enough to keep the high-resolution
        preview active continuously.
        """
        return PREVIEW_SUPERSAMPLE

    def _cache_key(self, clip: str, t: float, quality: int) -> tuple:
        return (
            id(self.state.doc),
            self.state.render_revision,
            clip,
            round(float(t), 8),
            int(quality),
        )

    @profile
    def _solve_at(self, clip: str, t: float):
        key = self._cache_key(clip, t, -1)
        cached = self._solve_cache.get(key)
        if cached is not None:
            self._solve_cache.move_to_end(key)
            return cached
        solved = self.state.doc.solve(clip, t)
        self._solve_cache[key] = solved
        if len(self._solve_cache) > SOLVE_CACHE_SIZE:
            self._solve_cache.popitem(last=False)
        return solved

    @profile
    def _render_qimage(self, clip: str, t: float, supersample: int) -> QImage:
        key = self._cache_key(clip, t, supersample)
        cached = self._frame_cache.get(key)
        if cached is not None:
            self._frame_cache.move_to_end(key)
            return cached
        solved = self._solve_at(clip, t)
        image = self.state.doc.render_at(
            clip, t, supersample=supersample, solved=solved
        )
        qimage = pil_to_qimage(image)
        self._frame_cache[key] = qimage
        if len(self._frame_cache) > FRAME_CACHE_SIZE:
            self._frame_cache.popitem(last=False)
        return qimage

    @profile
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
        t = self.state.t()
        try:
            if self.onion_skin and self.state.frames() > 1:
                for di, alpha in ((-1, 0.22), (1, 0.22)):
                    idx = (self.state.frame_idx + di) % self.state.frames()
                    ghost_t = self.state.doc.frame_time(clip, idx)
                    ghost = self._render_qimage(clip, ghost_t, ONION_SUPERSAMPLE)
                    painter.setOpacity(alpha)
                    self._draw_frame_image(painter, ghost, fw, fh)
                painter.setOpacity(1.0)
            image = self._render_qimage(clip, t, self._preview_supersample())
            self._draw_frame_image(painter, image, fw, fh)
        except Exception as ex:  # noqa: BLE001 - mid-edit docs can be invalid
            painter.setOpacity(1.0)
            painter.setPen(QPen(QColor(255, 120, 120), 1))
            painter.drawText(20, 30, f"render error: {type(ex).__name__}: {ex}")

        self._draw_gameplay_geometry(painter, clip, self.state.frame_idx)

        if self.show_bones:
            try:
                world, _params = self._solve_at(clip, t)
                self._draw_overlay(painter, world)
            except Exception as ex:  # noqa: BLE001
                painter.setPen(QPen(QColor(255, 120, 120), 1))
                painter.drawText(20, 50, f"solve error: {type(ex).__name__}: {ex}")
        painter.end()

    @profile
    def _draw_frame_image(self, painter: QPainter, image: QImage, fw: float, fh: float) -> None:
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, self.zoom < 3.0)
        tl = self.frame_to_widget((0, 0))
        target = QRectF(tl.x(), tl.y(), fw * self.zoom, fh * self.zoom)
        # Let QPainter scale the cached image directly. Avoid allocating another
        # full-size QImage on every pan, zoom, selection change, or expose event.
        painter.drawImage(target, image, QRectF(image.rect()))

    def _geometry_color(self, layer: str, *, live: bool = True) -> QColor:
        if layer == "collision":
            return QColor(255, 210, 70, 230)
        if layer == "hurtbox":
            return QColor(60, 220, 235, 230)
        return QColor(255, 70, 70, 235 if live else 110)

    def _shape_handle_points(self, shape: dict) -> list[tuple[str, Point]]:
        kind = shape.get("kind", "rect")
        if kind == "rect":
            x = float(shape.get("x", 0.0))
            y = float(shape.get("y", 0.0))
            w = float(shape.get("w", 0.0))
            h = float(shape.get("h", 0.0))
            return [
                ("nw", (x, y)),
                ("ne", (x + w, y)),
                ("se", (x + w, y + h)),
                ("sw", (x, y + h)),
            ]
        if kind == "circle":
            cx = float(shape.get("cx", 0.0))
            cy = float(shape.get("cy", 0.0))
            r = float(shape.get("r", 0.0))
            return [("center", (cx, cy)), ("radius", (cx + r, cy))]
        if kind == "capsule":
            ax = float(shape.get("ax", 0.0))
            ay = float(shape.get("ay", 0.0))
            bx = float(shape.get("bx", ax))
            by = float(shape.get("by", ay))
            r = float(shape.get("r", 0.0))
            mx, my = (ax + bx) / 2.0, (ay + by) / 2.0
            dx, dy = bx - ax, by - ay
            length = math.hypot(dx, dy)
            if length <= 1e-8:
                nx, ny = 1.0, 0.0
            else:
                nx, ny = -dy / length, dx / length
            return [
                ("a", (ax, ay)),
                ("b", (bx, by)),
                ("radius", (mx + nx * r, my + ny * r)),
            ]
        return [
            (f"vertex:{index}", (float(point[0]), float(point[1])))
            for index, point in enumerate(shape.get("points") or [])
        ]

    def _draw_gameplay_shape(
        self,
        painter: QPainter,
        shape: dict,
        color: QColor,
        *,
        dashed: bool = False,
        selected: bool = False,
    ) -> None:
        kind = shape.get("kind", "rect")
        fill = QColor(color)
        fill.setAlpha(32 if selected else 24)
        style = Qt.PenStyle.DashLine if dashed else Qt.PenStyle.SolidLine
        painter.setBrush(QBrush(fill))
        painter.setPen(QPen(color, 3 if selected else 2, style))

        if kind == "rect":
            x = float(shape.get("x", 0.0))
            y = float(shape.get("y", 0.0))
            w = float(shape.get("w", 0.0))
            h = float(shape.get("h", 0.0))
            if w > 0 and h > 0:
                tl = self.frame_to_widget((x, y))
                painter.drawRect(QRectF(tl.x(), tl.y(), w * self.zoom, h * self.zoom))
        elif kind == "circle":
            cx = float(shape.get("cx", 0.0))
            cy = float(shape.get("cy", 0.0))
            r = max(0.0, float(shape.get("r", 0.0)))
            center = self.frame_to_widget((cx, cy))
            painter.drawEllipse(center, r * self.zoom, r * self.zoom)
        elif kind == "capsule":
            ax = float(shape.get("ax", 0.0))
            ay = float(shape.get("ay", 0.0))
            bx = float(shape.get("bx", ax))
            by = float(shape.get("by", ay))
            r = max(0.0, float(shape.get("r", 0.0)))
            a = self.frame_to_widget((ax, ay))
            b = self.frame_to_widget((bx, by))
            # A round-capped thick line is exactly a capsule. Draw its translucent
            # body first, then a narrow outline so it remains legible over the art.
            body_pen = QPen(fill, max(1.0, 2.0 * r * self.zoom), style)
            body_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(body_pen)
            painter.drawLine(a, b)
            edge_pen = QPen(color, 2 if not selected else 3, style)
            edge_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(edge_pen)
            painter.drawLine(a, b)
            painter.drawEllipse(a, r * self.zoom, r * self.zoom)
            painter.drawEllipse(b, r * self.zoom, r * self.zoom)
        elif kind == "polygon":
            points = [self.frame_to_widget((float(p[0]), float(p[1]))) for p in shape.get("points") or []]
            if len(points) >= 3:
                painter.drawPolygon(QPolygonF(points))

        painter.setBrush(Qt.BrushStyle.NoBrush)
        if selected and self.state.geometry_edit_enabled:
            painter.setPen(QPen(QColor(255, 255, 255, 235), 1))
            painter.setBrush(QBrush(color))
            for _handle, point in self._shape_handle_points(shape):
                wp = self.frame_to_widget(point)
                painter.drawRect(QRectF(wp.x() - 4, wp.y() - 4, 8, 8))
            painter.setBrush(Qt.BrushStyle.NoBrush)

    def _draw_layer_shapes(
        self,
        painter: QPainter,
        layer: str,
        shapes: list[dict],
        *,
        live: bool = True,
    ) -> None:
        color = self._geometry_color(layer, live=live)
        for index, shape in enumerate(shapes):
            selected = layer == self.state.geometry_layer and index == self.state.geometry_shape_index
            self._draw_gameplay_shape(
                painter,
                shape,
                color,
                dashed=(layer == "hitbox" and not live),
                selected=selected,
            )

    def _draw_gameplay_geometry(
        self, painter: QPainter, clip: str, frame_idx: int
    ) -> None:
        collision = collision_entry(self.state.doc)
        if self.state.show_collision_geometry and collision:
            self._draw_layer_shapes(painter, "collision", entry_shapes(collision))

        hurt = hurtbox_entry(self.state.doc, clip)
        if self.state.show_hurtbox_geometry and hurt:
            self._draw_layer_shapes(painter, "hurtbox", entry_shapes(hurt))

        hit = hitbox_entry(self.state.doc, clip)
        if self.state.show_hitbox_geometry and hit:
            active = hit.get("active_frames") or [0, self.state.frames() - 1]
            live = int(active[0]) <= frame_idx <= int(active[-1])
            self._draw_layer_shapes(painter, "hitbox", entry_shapes(hit), live=live)

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

    def _geometry_layer_visible(self, layer: str) -> bool:
        return {
            "collision": self.state.show_collision_geometry,
            "hurtbox": self.state.show_hurtbox_geometry,
            "hitbox": self.state.show_hitbox_geometry,
        }[layer]

    def _geometry_hit_test(self, pos: QPointF) -> Optional[tuple[int, str]]:
        if not self.state.geometry_edit_enabled:
            return None
        layer = self.state.geometry_layer
        if not self._geometry_layer_visible(layer):
            return None
        shapes = layer_shapes(self.state.doc, layer, self.state.clip_name)
        if not shapes:
            return None
        handle_radius = 10.0
        # Prefer handles, selected shape first, then later-drawn shapes.
        order = list(range(len(shapes) - 1, -1, -1))
        selected = self.state.geometry_shape_index
        if selected in order:
            order.remove(selected)
            order.insert(0, selected)
        for index in order:
            for handle, point in self._shape_handle_points(shapes[index]):
                wp = self.frame_to_widget(point)
                if math.hypot(wp.x() - pos.x(), wp.y() - pos.y()) <= handle_radius:
                    return index, handle
        fp = self.widget_to_frame(pos)
        for index in order:
            if point_in_shape(shapes[index], fp):
                return index, "body"
        return None

    def _begin_geometry_drag(self, index: int, handle: str, pos: QPointF) -> None:
        shapes = layer_shapes(self.state.doc, self.state.geometry_layer, self.state.clip_name, create=True)
        if not 0 <= index < len(shapes):
            return
        self.state.set_geometry_selection(self.state.geometry_layer, index)
        self.state.push_undo()
        self._drag_mode = "geometry"
        self._geometry_drag = {
            "layer": self.state.geometry_layer,
            "index": index,
            "handle": handle,
            "start": self.widget_to_frame(pos),
            "shape": copy.deepcopy(shapes[index]),
        }
        self.statusMessage.emit(f"editing {self.state.geometry_layer} shape {index + 1}: {handle}")

    @staticmethod
    def _round_shape(shape: dict) -> None:
        for key, value in tuple(shape.items()):
            if isinstance(value, float):
                shape[key] = round(value, 2)
            elif key == "points":
                shape[key] = [[round(float(x), 2), round(float(y), 2)] for x, y in value]

    def _drag_geometry_to(self, fp: Point) -> None:
        drag = self._geometry_drag
        if not drag:
            return
        shapes = layer_shapes(self.state.doc, drag["layer"], self.state.clip_name, create=True)
        index = int(drag["index"])
        if not 0 <= index < len(shapes):
            return
        original = copy.deepcopy(drag["shape"])
        start_x, start_y = drag["start"]
        dx, dy = fp[0] - start_x, fp[1] - start_y
        handle = drag["handle"]
        kind = original.get("kind", "rect")

        if handle == "body":
            from ..authoring.gameplay_geometry import translate_shape
            translate_shape(original, dx, dy)
        elif kind == "rect":
            x0 = float(original.get("x", 0.0))
            y0 = float(original.get("y", 0.0))
            x1 = x0 + float(original.get("w", 0.0))
            y1 = y0 + float(original.get("h", 0.0))
            if "w" in handle:
                x0 = fp[0]
            if "e" in handle:
                x1 = fp[0]
            if "n" in handle:
                y0 = fp[1]
            if "s" in handle:
                y1 = fp[1]
            original.update({
                "x": min(x0, x1),
                "y": min(y0, y1),
                "w": max(0.5, abs(x1 - x0)),
                "h": max(0.5, abs(y1 - y0)),
            })
        elif kind == "circle":
            if handle == "center":
                original["cx"], original["cy"] = fp
            else:
                original["r"] = max(0.5, math.hypot(
                    fp[0] - float(original.get("cx", 0.0)),
                    fp[1] - float(original.get("cy", 0.0)),
                ))
        elif kind == "capsule":
            if handle == "a":
                original["ax"], original["ay"] = fp
            elif handle == "b":
                original["bx"], original["by"] = fp
            else:
                ax = float(original.get("ax", 0.0))
                ay = float(original.get("ay", 0.0))
                bx = float(original.get("bx", ax))
                by = float(original.get("by", ay))
                from ..authoring.gameplay_geometry import point_segment_distance
                original["r"] = max(0.5, point_segment_distance(fp, (ax, ay), (bx, by)))
        elif kind == "polygon" and handle.startswith("vertex:"):
            vertex = int(handle.split(":", 1)[1])
            points = [list(point) for point in original.get("points") or []]
            if 0 <= vertex < len(points):
                points[vertex] = [fp[0], fp[1]]
                original["points"] = points

        self._round_shape(original)
        shapes[index] = original
        mark_entry_edited(layer_entry(self.state.doc, drag["layer"], self.state.clip_name))
        self.state.mark_geometry_changed()

    def _hit_test(self, pos: QPointF) -> Optional[str]:
        try:
            world, _ = self._solve_at(self.state.clip_name, self.state.t())
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
            world, _ = self._solve_at(self.state.clip_name, self.state.t())
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
        geometry_hit = self._geometry_hit_test(event.position())
        if geometry_hit is not None:
            self._begin_geometry_drag(geometry_hit[0], geometry_hit[1], event.position())
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

    @profile
    def mouseMoveEvent(self, event) -> None:
        if self._drag_mode == "pan":
            delta = event.position().toPoint() - self._pan_anchor
            self._pan_anchor = event.position().toPoint()
            self.pan += QPointF(delta.x(), delta.y())
            self.update()
            return
        if self._drag_mode == "geometry":
            self._drag_geometry_to(self.widget_to_frame(event.position()))
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
            self.state.write_keys(
                {
                    f"{pre}_x": round(x_off, 2),
                    f"{pre}_lift": round(max(-1.0, lift), 2),
                }
            )
            return
        # rotate
        try:
            sk = self.state.doc.build_skeleton()
            world, _ = self._solve_at(self.state.clip_name, self.state.t())
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

    @profile
    def _drag_limb_to(self, fp: Point) -> None:
        """Editor-side two-bone IK: place the dragged bone's origin at ``fp``
        by writing FK pose keys for its grandparent and parent."""
        chain = self._fk_chain(self._drag_bone)
        if chain is None:
            return
        try:
            sk = self.state.doc.build_skeleton()
            world, _ = self._solve_at(self.state.clip_name, self.state.t())
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
        values = {}
        for name, pose in ((up, pose_up), (lo, pose_lo)):
            pose = (pose + 180.0) % 360.0 - 180.0
            values[name] = round(pose, 1)
        self.state.write_keys(values)

    @profile
    def _drag_offset_to(self, fp: Point) -> None:
        """Move the dragged bone's attachment so its origin lands at frame
        point ``fp``: new offset = R(-parent_world_angle) · (fp - parent_origin)."""
        bone = self.state.doc.bone(self._drag_bone)
        if bone is None:
            return
        try:
            world, _ = self._solve_at(self.state.clip_name, self.state.t())
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
        self.state.mark_pose_changed()

    def mouseReleaseEvent(self, event) -> None:
        drag_mode = self._drag_mode
        self._drag_mode = None
        self._drag_bone = None
        self._geometry_drag = None
        if drag_mode == "offset":
            # Refresh the bone property form once after the interactive drag,
            # rather than rebuilding every side panel per mouse event.
            self.state.docChanged.emit()

    def wheelEvent(self, event) -> None:
        factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        old = self.widget_to_frame(event.position())
        self.zoom = max(0.5, min(24.0, self.zoom * factor))
        new_wp = self.frame_to_widget(old)
        self.pan += event.position() - new_wp
        self.update()
