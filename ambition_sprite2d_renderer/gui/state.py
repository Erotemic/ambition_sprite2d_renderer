"""Shared editor state for the rig editor.

One ``EditorState`` instance is owned by the main window and handed to
every panel. Panels mutate ``state.doc.data`` directly, then emit the
matching signal. High-frequency pose edits deliberately use narrower
signals than structural document edits so dragging a joint does not rebuild
every editor panel on every mouse-move event.

Undo is snapshot-based: callers ``push_undo()`` once before a mutation (or
before a drag begins), and undo/redo swap whole-document JSON snapshots.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import List, Optional

from PySide6.QtCore import QObject, Signal

from ..authoring.rigdoc import RigDocument, sample_channel_spec

try:
    from line_profiler import profile
except ImportError:  # Optional developer dependency.
    from ..profiling import profile

MAX_UNDO = 200


class EditorState(QObject):
    # Broad document/schema mutation. Expensive panels refresh from this.
    docChanged = Signal()
    # Any mutation that changes the rendered frame. The canvas refreshes from this.
    poseChanged = Signal()
    # Animation-channel edits, carrying the tuple of channels that changed.
    animationChanged = Signal(object)
    selectionChanged = Signal()
    timeChanged = Signal()
    dirtyChanged = Signal()
    # Authoring-only gameplay geometry changed; does not invalidate sprite pixels.
    geometryChanged = Signal()
    geometryVisibilityChanged = Signal()
    geometrySelectionChanged = Signal()

    def __init__(self, doc: RigDocument, path: Optional[str] = None) -> None:
        super().__init__()
        self.doc = doc
        self.path: Optional[str] = path
        self.clip_name: str = next(iter(doc.clips), "idle")
        self.frame_idx: int = 0
        self.selected_bone: Optional[str] = None
        self.selected_part: Optional[int] = None  # index into doc.parts
        self.dirty: bool = False
        self.pose_clipboard: Optional[dict] = None  # {channel: value}
        self.render_revision: int = 0
        self.show_collision_geometry: bool = True
        self.show_hurtbox_geometry: bool = True
        self.show_hitbox_geometry: bool = True
        self.geometry_layer: str = "hurtbox"
        self.geometry_shape_index: int = 0
        self.geometry_edit_enabled: bool = True
        self._undo: List[str] = []
        self._redo: List[str] = []

    # ---- Document lifecycle ------------------------------------------------

    def set_doc(self, doc: RigDocument, path: Optional[str]) -> None:
        self.doc = doc
        self.path = path
        self.clip_name = next(iter(doc.clips), "idle")
        self.frame_idx = 0
        self.selected_bone = None
        self.selected_part = None
        self.dirty = False
        self.render_revision += 1
        self._undo.clear()
        self._redo.clear()
        self.docChanged.emit()
        self.poseChanged.emit()
        self.timeChanged.emit()
        self.selectionChanged.emit()
        self.dirtyChanged.emit()
        self.geometryChanged.emit()
        self.geometrySelectionChanged.emit()

    def _set_dirty(self) -> None:
        if not self.dirty:
            self.dirty = True
            self.dirtyChanged.emit()

    def _mark_render_changed(self) -> None:
        self._set_dirty()
        self.render_revision += 1
        self.poseChanged.emit()

    def mark_changed(self) -> None:
        """Mark a broad structural/content edit.

        Use this for bone/part/palette/clip structure edits. Interactive pose
        edits should use :meth:`write_keys` or :meth:`mark_pose_changed` so the
        expensive side panels are not rebuilt continuously.
        """
        self._mark_render_changed()
        self.docChanged.emit()

    def mark_pose_changed(self) -> None:
        """Mark a render-affecting edit without rebuilding structural panels."""
        self._mark_render_changed()

    def mark_geometry_changed(self) -> None:
        """Mark authoring geometry dirty without invalidating rendered sprites."""
        self._set_dirty()
        self.geometryChanged.emit()

    def set_geometry_visibility(
        self, *, collision=None, hurtbox=None, hitbox=None
    ) -> None:
        changed = False
        for attr, value in (
            ("show_collision_geometry", collision),
            ("show_hurtbox_geometry", hurtbox),
            ("show_hitbox_geometry", hitbox),
        ):
            if value is not None and bool(value) != bool(getattr(self, attr)):
                setattr(self, attr, bool(value))
                changed = True
        if changed:
            self.geometryVisibilityChanged.emit()

    def set_geometry_selection(
        self, layer: str, shape_index: int = 0
    ) -> None:
        if layer not in {"collision", "hurtbox", "hitbox"}:
            raise ValueError(layer)
        shape_index = max(0, int(shape_index))
        if layer == self.geometry_layer and shape_index == self.geometry_shape_index:
            return
        self.geometry_layer = layer
        self.geometry_shape_index = shape_index
        self.geometrySelectionChanged.emit()

    def set_geometry_edit_enabled(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if enabled != self.geometry_edit_enabled:
            self.geometry_edit_enabled = enabled
            self.geometrySelectionChanged.emit()

    # ---- Undo ----------------------------------------------------------------

    @profile
    def _snapshot(self) -> str:
        # Compact snapshots reduce both serialization time and undo memory.
        return json.dumps(self.doc.data, separators=(",", ":"), ensure_ascii=False)

    def push_undo(self) -> None:
        self._undo.append(self._snapshot())
        if len(self._undo) > MAX_UNDO:
            self._undo.pop(0)
        self._redo.clear()

    def discard_last_undo(self) -> None:
        """Drop a speculative undo snapshot after a cancelled/no-op edit."""
        if self._undo:
            self._undo.pop()

    def undo(self) -> bool:
        if not self._undo:
            return False
        self._redo.append(self._snapshot())
        self.doc.data = json.loads(self._undo.pop())
        self._after_history_swap()
        return True

    def redo(self) -> bool:
        if not self._redo:
            return False
        self._undo.append(self._snapshot())
        self.doc.data = json.loads(self._redo.pop())
        self._after_history_swap()
        return True

    def _after_history_swap(self) -> None:
        if self.clip_name not in self.doc.clips:
            self.clip_name = next(iter(self.doc.clips), "idle")
        if self.selected_part is not None and self.selected_part >= len(self.doc.parts):
            self.selected_part = None
        if self.selected_bone and self.doc.bone(self.selected_bone) is None:
            self.selected_bone = None
        self._mark_render_changed()
        self.docChanged.emit()
        self.timeChanged.emit()
        self.selectionChanged.emit()
        self.geometryChanged.emit()
        self.geometrySelectionChanged.emit()

    # ---- Time cursor -------------------------------------------------------

    def clip(self) -> dict:
        return self.doc.clips.setdefault(
            self.clip_name, {"loop": True, "frames": 8, "duration_ms": 100, "channels": {}}
        )

    def frames(self) -> int:
        return max(1, int(self.clip().get("frames", 8)))

    def t(self) -> float:
        return self.doc.frame_time(self.clip_name, self.frame_idx)

    def set_frame(self, idx: int) -> None:
        idx = max(0, min(self.frames() - 1, idx))
        if idx != self.frame_idx:
            self.frame_idx = idx
            self.timeChanged.emit()

    def set_clip(self, name: str) -> None:
        if name in self.doc.clips and name != self.clip_name:
            self.clip_name = name
            self.frame_idx = 0
            self.timeChanged.emit()

    # ---- Key authoring (canvas drags + timeline edits) ---------------------

    @profile
    def _write_key_value(self, channel: str, value: float, ease: str) -> bool:
        """Write one key without emitting signals. Return whether data changed."""
        clip = self.clip()
        channels = clip.setdefault("channels", {})
        spec = channels.get(channel)
        loop = bool(clip.get("loop", True))
        changed = False
        if spec is not None and "keys" not in spec:
            n = self.frames()
            spec = {
                "keys": [
                    [
                        round(self.doc.frame_time(self.clip_name, i), 4),
                        round(
                            sample_channel_spec(
                                spec, self.doc.frame_time(self.clip_name, i), loop
                            ),
                            3,
                        ),
                        "linear",
                    ]
                    for i in range(n)
                ]
            }
            channels[channel] = spec
            changed = True
        elif spec is None:
            spec = {"keys": []}
            channels[channel] = spec
            changed = True

        keys = spec["keys"]
        t = round(self.t(), 4)
        rounded = round(float(value), 3)
        for key in keys:
            if abs(float(key[0]) - t) < 1e-4:
                if float(key[1]) != rounded:
                    key[1] = rounded
                    changed = True
                break
        else:
            keys.append([t, rounded, ease])
            keys.sort(key=lambda key: float(key[0]))
            changed = True
        return changed

    @profile
    def write_keys(
        self,
        values: Mapping[str, float],
        ease: str = "smooth",
    ) -> int:
        """Write multiple current-frame keys and notify the editor once.

        Returns the number of channels whose stored data changed. This is the
        path used by foot dragging, two-bone IK, and pose paste so one mouse
        event cannot trigger several complete render/refresh cycles.
        """
        changed = tuple(
            channel
            for channel, value in values.items()
            if self._write_key_value(channel, value, ease)
        )
        if changed:
            self._mark_render_changed()
            self.animationChanged.emit(changed)
        return len(changed)

    def write_key(self, channel: str, value: float, ease: str = "smooth") -> bool:
        """Set one channel at the current frame, baking expr/const channels."""
        return bool(self.write_keys({channel: value}, ease=ease))

    # ---- Pose clipboard ----------------------------------------------------

    def copy_pose(self) -> int:
        """Sample every driven channel into the pose clipboard."""
        self.pose_clipboard = {
            name: round(value, 3)
            for name, value in self.doc.sample(self.clip_name, self.t()).items()
        }
        return len(self.pose_clipboard)

    @profile
    def paste_pose(self) -> int:
        """Write the clipboard pose as one batched current-frame edit."""
        if not self.pose_clipboard:
            return 0
        self.push_undo()
        changed = self.write_keys(self.pose_clipboard)
        if not changed:
            # Avoid retaining a useless undo point when the pose was identical.
            self._undo.pop()
        return changed
