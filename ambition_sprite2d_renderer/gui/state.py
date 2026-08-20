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
import math
from collections.abc import Mapping
from typing import List, Optional

from PySide6.QtCore import QObject, Signal

from ..authoring.animation_constraints import (
    pin_for_bone,
    pinned_bones,
    remove_pin,
    update_pin_target,
    upsert_full_clip_pin,
)
from ..authoring.animation_keys import (
    channel_key_frames,
    keyed_channels_at_frame,
    neighbor_pose_keys,
    pose_key_frames,
    time_to_frame,
)
from ..authoring.rigdoc import RigDocument, sample_channel_spec
from ..authoring.skeleton import two_bone_ik

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
    # Editor-only pose-key bookmarks and composable viewport overlays.
    poseKeysChanged = Signal()
    viewOptionsChanged = Signal()
    # Persistent animation constraints such as continuous rigid-part pins.
    constraintsChanged = Signal()

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
        self.geometry_edit_enabled: bool = False
        self.show_key_pose_ghosts: bool = True
        self.show_frame_onion: bool = False
        self.show_motion_trail: bool = True
        self.show_intermediate_chain_ghosts: bool = True
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
        self.poseKeysChanged.emit()
        self.viewOptionsChanged.emit()
        self.constraintsChanged.emit()

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

    def mark_constraints_changed(self) -> None:
        """Mark continuously evaluated animation constraints as changed."""
        self._mark_render_changed()
        self.constraintsChanged.emit()

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

    def set_view_options(
        self,
        *,
        key_pose_ghosts=None,
        frame_onion=None,
        motion_trail=None,
        intermediate_chain_ghosts=None,
    ) -> None:
        """Update independent viewport overlays without hiding other layers."""
        changed = False
        for attr, value in (
            ("show_key_pose_ghosts", key_pose_ghosts),
            ("show_frame_onion", frame_onion),
            ("show_motion_trail", motion_trail),
            ("show_intermediate_chain_ghosts", intermediate_chain_ghosts),
        ):
            if value is not None and bool(value) != bool(getattr(self, attr)):
                setattr(self, attr, bool(value))
                changed = True
        if changed:
            self.viewOptionsChanged.emit()

    # ---- Pose-key authoring ------------------------------------------------

    def pose_key_frames(self) -> tuple[list[int], bool]:
        """Return the current clip's key-pose bookmarks and whether saved."""
        return pose_key_frames(self.doc, self.clip_name)

    def materialize_pose_keys(self) -> list[int]:
        """Persist the current suggestions before the user customizes them."""
        frames, explicit = self.pose_key_frames()
        if not explicit:
            self.clip()["pose_keys"] = list(frames)
        return list(frames)

    def is_pose_key(self, frame_idx: Optional[int] = None) -> bool:
        frame_idx = self.frame_idx if frame_idx is None else int(frame_idx)
        frames, _explicit = self.pose_key_frames()
        return frame_idx in frames

    def set_pose_key(self, frame_idx: int, enabled: bool = True) -> bool:
        frame_idx = max(0, min(self.frames() - 1, int(frame_idx)))
        keys = set(self.materialize_pose_keys())
        before = set(keys)
        if enabled:
            keys.add(frame_idx)
        else:
            keys.discard(frame_idx)
            # Always retain at least one reference pose.
            if not keys:
                keys.add(0)
        if keys == before:
            return False
        self.clip()["pose_keys"] = sorted(keys)
        self._set_dirty()
        self.poseKeysChanged.emit()
        return True

    def toggle_pose_key(self, frame_idx: Optional[int] = None) -> bool:
        frame_idx = self.frame_idx if frame_idx is None else int(frame_idx)
        return self.set_pose_key(frame_idx, not self.is_pose_key(frame_idx))

    def neighboring_pose_keys(self) -> tuple[Optional[int], Optional[int]]:
        keys, _explicit = self.pose_key_frames()
        return neighbor_pose_keys(
            keys, self.frame_idx, self.frames(), bool(self.clip().get("loop", True))
        )

    def keyed_channels_at_frame(self, frame_idx: Optional[int] = None) -> list[str]:
        frame_idx = self.frame_idx if frame_idx is None else int(frame_idx)
        return keyed_channels_at_frame(self.clip(), frame_idx)

    def channel_key_frames(self, channel: Optional[str] = None) -> dict[str, set[int]]:
        return channel_key_frames(self.clip(), channel)

    def selected_animation_channels(self) -> list[str]:
        """Channels most directly controlled by the selected bone/endpoint.

        Return the *authoring vocabulary* even when a channel has not been
        materialized yet. ``insert_keys_here`` can now seed an absent channel
        from the rig's pre-edit value, so a static bone and an IK endpoint are
        both legitimate targets for **Key selected**.
        """
        bone = self.selected_bone
        if not bone:
            return []
        leg = self.doc.foot_leg_for_bone(bone)
        if leg is not None and bone == leg.get("foot"):
            prefix = str(leg.get("channel_prefix", "foot"))
            return [f"{prefix}_x", f"{prefix}_lift", f"{prefix}_pitch"]
        for chain in self.doc.ik_chains:
            if bone == chain.get("end"):
                prefix = str(chain.get("channel_prefix", "target"))
                result = [f"{prefix}_x", f"{prefix}_y"]
                if chain.get("end"):
                    result.append(f"{prefix}_pitch")
                return result
        return [bone] if self.doc.bone(bone) is not None else []

    def _fk_endpoint_chain_for_bone(self, bone_name: str) -> Optional[tuple[str, str]]:
        """Two animated segments ending at ``bone_name``'s origin."""
        if not bone_name or self.doc.foot_leg_for_bone(bone_name) is not None:
            return None
        bone = self.doc.bone(bone_name)
        if bone is None:
            return None
        # This operation is intentionally endpoint-centric. Refuse interior
        # joints such as an elbow or knee, where "keep this part here" would
        # unexpectedly solve a chain through the torso/pelvis.
        if any(candidate.get("parent") == bone_name for candidate in self.doc.bones):
            return None
        lower = self.doc.bone(bone.get("parent") or "")
        if lower is None or float(lower.get("length", 0.0)) <= 0:
            return None
        upper = self.doc.bone(lower.get("parent") or "")
        if upper is None or float(upper.get("length", 0.0)) <= 0:
            return None
        return str(upper["name"]), str(lower["name"])

    def _selected_fk_endpoint_chain(self) -> Optional[tuple[str, str]]:
        bone_name = self.selected_bone
        return self._fk_endpoint_chain_for_bone(bone_name) if bone_name else None

    def _plantable_foot_for_bone(self, bone_name: str) -> Optional[dict]:
        """Describe either a document-IK or ordinary FK terminal foot."""
        if not bone_name.lower().endswith("foot"):
            return None
        leg = self.doc.foot_leg_for_bone(bone_name)
        if leg is not None and bone_name == leg.get("foot"):
            return {
                "foot": bone_name,
                "upper": str(leg.get("upper")),
                "lower": str(leg.get("lower")),
                "channel_prefix": str(leg.get("channel_prefix", "foot")),
                "document_ik": True,
            }
        chain = self._fk_endpoint_chain_for_bone(bone_name)
        if chain is None:
            return None
        return {
            "foot": bone_name,
            "upper": chain[0],
            "lower": chain[1],
            "channel_prefix": "",
            "document_ik": False,
        }

    @staticmethod
    def _bend_for_world(chain: tuple[str, str], world, skeleton) -> float:
        """Choose the IK bend that best preserves the sampled elbow/knee side."""
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
                predicted_middle[0] - middle[0],
                predicted_middle[1] - middle[1],
            )
            if distance < best_distance:
                best_bend, best_distance = bend, distance
        return best_bend

    def _replace_channel_at_pose_keys(
        self, channel: str, values: Mapping[int, float], ease: str = "smooth"
    ) -> bool:
        """Replace one channel with values at the supplied pose-key frames."""
        if not values:
            return False
        channels = self.clip().setdefault("channels", {})
        keys = [
            [
                round(self.doc.frame_time(self.clip_name, frame), 4),
                round(float(value), 3),
                ease,
            ]
            for frame, value in sorted(values.items())
        ]
        before = channels.get(channel)
        replacement = {"keys": keys}
        if before == replacement:
            return False
        channels[channel] = replacement
        return True

    def copy_selected_controls_to_pose_keys(self) -> int:
        """Use the current selected-control values at every important pose."""
        channels = self.selected_animation_channels()
        pose_frames = self.materialize_pose_keys()
        if not channels or not pose_frames:
            return 0
        sampled = self.doc.sample(self.clip_name, self.t())
        changed = [
            channel
            for channel in channels
            if self._replace_channel_at_pose_keys(
                channel, {frame: sampled.get(channel, 0.0) for frame in pose_frames}
            )
        ]
        if changed:
            self._mark_render_changed()
            self.animationChanged.emit(tuple(changed))
            self.poseKeysChanged.emit()
        return len(changed)

    def can_pin_selected_endpoint(self) -> bool:
        """Whether the selected control can be positioned across pose keys."""
        bone = self.selected_bone
        if not bone:
            return False
        leg = self.doc.foot_leg_for_bone(bone)
        if leg is not None and bone == leg.get("foot"):
            return True
        return self._selected_fk_endpoint_chain() is not None

    def pin_selected_endpoint_to_pose_keys(self, axis: str = "both") -> tuple[int, int]:
        """Keep the selected endpoint at its current position across pose keys.

        ``axis`` is ``both``, ``x``, or ``y``. Document-IK feet are pinned by
        their world-space target channels. Free two-segment limbs are solved at
        every pose key while preserving the sampled bend direction. Controlled
        channels are rewritten to pose keys, which also removes hidden baked
        in-between keys that would otherwise reintroduce a foot march.

        Returns ``(changed_channels, affected_pose_keys)``.
        """
        if axis not in {"both", "x", "y"}:
            raise ValueError(f"unknown pin axis: {axis}")
        bone_name = self.selected_bone
        pose_frames = self.materialize_pose_keys()
        if not bone_name or not pose_frames:
            return 0, 0

        current_world, _current_params = self.doc.solve(self.clip_name, self.t())
        selected_world = current_world.get(bone_name)
        if selected_world is None:
            return 0, 0
        target = selected_world.origin
        clip_channels = self.clip().get("channels") or {}
        planned: dict[str, dict[int, float]] = {}

        leg = self.doc.foot_leg_for_bone(bone_name)
        if leg is not None and bone_name == leg.get("foot"):
            prefix = str(leg.get("channel_prefix", "foot"))
            fr = self.doc.frame
            center_x = float(fr.get("center_x", fr["width"] / 2))
            ground_y = float(fr.get("ground_y", fr["height"] - 2))
            ankle_h = float(fr.get("ankle_h", 0.0))
            # Derive the authored target from the selected endpoint itself rather
            # than assuming absent channels default to zero. This remains exact
            # when a rig uses non-zero rest_x/rest_lift values.
            if axis in {"both", "x"}:
                channel = f"{prefix}_x"
                value = target[0] - center_x
                planned[channel] = {frame: value for frame in pose_frames}
            if axis in {"both", "y"}:
                channel = f"{prefix}_lift"
                value = ground_y - ankle_h - target[1]
                planned[channel] = {frame: value for frame in pose_frames}
            if axis == "both":
                channel = f"{prefix}_pitch"
                value = selected_world.angle
                planned[channel] = {frame: value for frame in pose_frames}
        else:
            chain = self._selected_fk_endpoint_chain()
            if chain is None:
                return 0, 0
            skeleton = self.doc.build_skeleton()
            upper, lower = chain
            upper_bone = skeleton.bones[upper]
            lower_bone = skeleton.bones[lower]
            upper_values: dict[int, float] = {}
            lower_values: dict[int, float] = {}
            end_values: dict[int, float] = {}
            end_bone = skeleton.bones[bone_name]
            for frame in pose_frames:
                frame_time = self.doc.frame_time(self.clip_name, frame)
                world, _params = self.doc.solve(self.clip_name, frame_time)
                sampled_endpoint = world[bone_name].origin
                frame_target = (
                    target[0] if axis in {"both", "x"} else sampled_endpoint[0],
                    target[1] if axis in {"both", "y"} else sampled_endpoint[1],
                )
                root = world[upper].origin
                bend = self._bend_for_world(chain, world, skeleton)
                world_upper, world_lower = two_bone_ik(
                    root,
                    frame_target,
                    upper_bone.length,
                    lower_bone.length,
                    bend=bend,
                )
                parent_angle = world[upper_bone.parent].angle if upper_bone.parent else 0.0
                upper_pose = world_upper - parent_angle - upper_bone.rest_angle
                lower_pose = world_lower - world_upper - lower_bone.rest_angle
                upper_values[frame] = (upper_pose + 180.0) % 360.0 - 180.0
                lower_values[frame] = (lower_pose + 180.0) % 360.0 - 180.0
                if axis == "both" and bone_name in clip_channels:
                    end_pose = selected_world.angle - world_lower - end_bone.rest_angle
                    end_values[frame] = (end_pose + 180.0) % 360.0 - 180.0
            planned[upper] = upper_values
            planned[lower] = lower_values

            # Preserve the endpoint's world orientation too. This keeps a planted
            # foot from rocking around its fixed ankle and keeps a held hand/tool
            # visually steady while the parent chain is re-solved.
            if end_values:
                planned[bone_name] = end_values

        changed = [
            channel
            for channel, values in planned.items()
            if self._replace_channel_at_pose_keys(channel, values)
        ]
        if changed:
            self._mark_render_changed()
            self.animationChanged.emit(tuple(changed))
            self.poseKeysChanged.emit()
        return len(changed), len(pose_frames)

    # ---- Continuous transform-pin constraints -----------------------------

    @staticmethod
    def _part_default_anchor(part: Mapping) -> tuple[float, float]:
        """Choose a useful local anchor for a visual part.

        Visual endpoint parts such as hands are often attached directly to the
        final forearm bone rather than receiving a dedicated hand bone.  Their
        authored center/end is therefore the point users expect to pin.
        """
        kind = str(part.get("kind", ""))
        if kind in {"circle", "ellipse"}:
            raw = part.get("center") or (0.0, 0.0)
            return (float(raw[0]), float(raw[1]))
        if kind == "capsule":
            raw = part.get("b")
            if raw is not None:
                return (float(raw[0]), float(raw[1]))
        if kind == "polygon":
            points = part.get("points") or []
            if points:
                return (
                    sum(float(point[0]) for point in points) / len(points),
                    sum(float(point[1]) for point in points) / len(points),
                )
        raw = part.get("pivot") or (0.0, 0.0)
        return (float(raw[0]), float(raw[1]))

    def _continuous_pin_candidate_for_bone(self, bone_name: str) -> Optional[dict]:
        """Describe how a selected skeleton bone can be held in frame space."""
        if not bone_name:
            return None

        # Declared IK feet/chains already name the intended two-bone solver.
        leg = self.doc.foot_leg_for_bone(bone_name)
        if leg is not None and bone_name == leg.get("foot"):
            return {
                "bone": bone_name,
                "upper": str(leg.get("upper")),
                "lower": str(leg.get("lower")),
                "channel_prefix": str(leg.get("channel_prefix", "foot")),
                "role": "foot",
                "document_ik": True,
                "solver_mode": "endpoint_bone",
                "anchor_local": (0.0, 0.0),
                "lock_rotation_supported": True,
                "selection_name": bone_name,
            }
        for chain in self.doc.ik_chains:
            if bone_name == chain.get("end"):
                return {
                    "bone": bone_name,
                    "upper": str(chain.get("upper")),
                    "lower": str(chain.get("lower")),
                    "channel_prefix": str(chain.get("channel_prefix", "target")),
                    "role": "part",
                    "document_ik": True,
                    "solver_mode": "endpoint_bone",
                    "anchor_local": (0.0, 0.0),
                    "lock_rotation_supported": True,
                    "selection_name": bone_name,
                }

        bone = self.doc.bone(bone_name)
        if bone is None:
            return None
        lower = self.doc.bone(bone.get("parent") or "")
        if lower is None or float(lower.get("length", 0.0)) <= 0:
            return None
        upper = self.doc.bone(lower.get("parent") or "")
        if upper is None or float(upper.get("length", 0.0)) <= 0:
            return None
        return {
            "bone": bone_name,
            "upper": str(upper["name"]),
            "lower": str(lower["name"]),
            "channel_prefix": "",
            "role": "foot" if bone_name.lower().endswith("foot") else "part",
            "document_ik": False,
            "solver_mode": "endpoint_bone",
            "anchor_local": (0.0, 0.0),
            "lock_rotation_supported": True,
            "selection_name": bone_name,
        }

    def _continuous_pin_candidate_for_part(self, part: Mapping) -> Optional[dict]:
        """Describe how a visual endpoint part can be pinned.

        Some rigs model a hand as artwork centered at the end of ``arm_l`` and
        do not create a separate hand bone.  In that case the pin constrains the
        authored point on the terminal lower bone.  Position is exact, while
        rotation continues to follow the IK solution because a two-joint chain
        has no spare degree of freedom for an independent orientation lock.
        """
        bone_name = str(part.get("bone") or "")
        lower = self.doc.bone(bone_name)
        if lower is None or float(lower.get("length", 0.0)) <= 0:
            return None
        upper = self.doc.bone(lower.get("parent") or "")
        if upper is None or float(upper.get("length", 0.0)) <= 0:
            return None
        return {
            "bone": bone_name,
            "upper": str(upper["name"]),
            "lower": bone_name,
            "channel_prefix": "",
            "role": "foot" if "foot" in str(part.get("name", "")).lower() else "part",
            "document_ik": False,
            "solver_mode": "point_on_lower",
            "anchor_local": self._part_default_anchor(part),
            "lock_rotation_supported": False,
            "selection_name": str(part.get("name") or bone_name),
        }

    def selected_pinnable_part(self) -> Optional[dict]:
        # The Parts panel has an explicit index; prefer it when available.
        if self.selected_part is not None and 0 <= self.selected_part < len(self.doc.parts):
            candidate = self._continuous_pin_candidate_for_part(
                self.doc.parts[self.selected_part]
            )
            if candidate is not None:
                return candidate

        selected = self.selected_bone
        if not selected:
            return None
        candidate = self._continuous_pin_candidate_for_bone(selected)
        if candidate is not None:
            return candidate

        # Canvas/tests may carry the visual part name in ``selected_bone``.
        # Resolve that alias instead of requiring every endpoint artwork group
        # to have a redundant skeleton bone with the same name.
        for part in self.doc.parts:
            if str(part.get("name") or "") == selected:
                return self._continuous_pin_candidate_for_part(part)
        return None

    def selected_part_pin(self) -> Optional[dict]:
        candidate = self.selected_pinnable_part()
        if candidate is None:
            return None
        return pin_for_bone(self.doc, self.clip_name, str(candidate["bone"]))

    def pinned_parts(self) -> set[str]:
        return pinned_bones(self.doc, self.clip_name)

    def pinnable_feet(self) -> list[dict]:
        endpoints = []
        seen = set()
        for bone in self.doc.bones:
            name = str(bone.get("name") or "")
            candidate = self._continuous_pin_candidate_for_bone(name)
            if (
                candidate is not None
                and candidate.get("role") == "foot"
                and candidate["bone"] not in seen
            ):
                endpoints.append(candidate)
                seen.add(candidate["bone"])
        return endpoints

    @staticmethod
    def _world_point_to_bone_local(world_bone, point: tuple[float, float]) -> tuple[float, float]:
        dx = float(point[0]) - world_bone.origin[0]
        dy = float(point[1]) - world_bone.origin[1]
        radians = math.radians(world_bone.angle)
        c = math.cos(radians)
        sn = math.sin(radians)
        return (dx * c + dy * sn, -dx * sn + dy * c)

    def pin_selected_part_entire_clip(
        self,
        *,
        anchor_frame: Optional[tuple[float, float]] = None,
        lock_rotation: bool = True,
    ) -> bool:
        """Pin the selected part's complete transform through the clip.

        ``anchor_frame`` may be any point clicked on the part. The point is
        stored in the selected bone's local coordinates. With rotation locked,
        the anchor plus world angle hold the complete attached artwork (and all
        descendants) rigidly rather than merely pinning a toe marker.
        """
        candidate = self.selected_pinnable_part()
        if candidate is None:
            return False
        bone_name = str(candidate["bone"])
        world, _params = self.doc.solve(self.clip_name, self.t())
        endpoint = world.get(bone_name)
        if endpoint is None:
            return False
        if anchor_frame is None:
            default_anchor = tuple(candidate.get("anchor_local", (0.0, 0.0)))
            anchor_world = endpoint.to_world(default_anchor)
            anchor_local = default_anchor
        else:
            anchor_world = anchor_frame
            anchor_local = self._world_point_to_bone_local(endpoint, anchor_world)
        skeleton = self.doc.build_skeleton()
        chain = (str(candidate["upper"]), str(candidate["lower"]))
        bend = self._bend_for_world(chain, world, skeleton)
        before = pin_for_bone(self.doc, self.clip_name, bone_name)
        before_copy = json.dumps(before, sort_keys=True) if before is not None else None
        pin = upsert_full_clip_pin(
            self.doc,
            self.clip_name,
            bone_name=bone_name,
            anchor_local=anchor_local,
            target=anchor_world,
            rotation=endpoint.angle,
            upper=chain[0],
            lower=chain[1],
            bend=bend,
            lock_rotation=(
                bool(lock_rotation)
                and bool(candidate.get("lock_rotation_supported", True))
            ),
            role=str(candidate.get("role", "part")),
            channel_prefix=str(candidate.get("channel_prefix", "")),
            solver_mode=str(candidate.get("solver_mode", "endpoint_bone")),
        )
        if before_copy == json.dumps(pin, sort_keys=True):
            return False
        self.mark_constraints_changed()
        return True

    def pin_all_feet_entire_clip(self, *, lock_rotation: bool = True) -> int:
        """Pin every foot endpoint transform at the current pose.

        A stale Parts-panel selection must not override the temporary foot-bone
        selection used by this loop.  The old implementation could therefore
        pin the same unrelated visual part twice while the UI claimed both feet
        were planted.
        """
        original_selection = self.selected_bone
        original_part = self.selected_part
        changed = 0
        try:
            self.selected_part = None
            for candidate in self.pinnable_feet():
                self.selected_bone = str(candidate["bone"])
                changed += int(
                    self.pin_selected_part_entire_clip(lock_rotation=lock_rotation)
                )
        finally:
            self.selected_bone = original_selection
            self.selected_part = original_part
        if changed:
            self.selectionChanged.emit()
        return changed

    def release_selected_part_pin(self) -> bool:
        candidate = self.selected_pinnable_part()
        if candidate is None:
            return False
        changed = remove_pin(self.doc, self.clip_name, str(candidate["bone"]))
        if changed:
            self.mark_constraints_changed()
        return changed

    def release_all_part_pins(self) -> int:
        parts = list(self.pinned_parts())
        changed = sum(remove_pin(self.doc, self.clip_name, name) for name in parts)
        if changed:
            self.mark_constraints_changed()
        return changed

    def move_selected_part_pin(self, target: tuple[float, float]) -> bool:
        """Move a persistent transform-pin target without adding pose keys."""
        candidate = self.selected_pinnable_part()
        if candidate is None:
            return False
        changed = update_pin_target(
            self.doc, self.clip_name, str(candidate["bone"]), target
        )
        if changed:
            self.mark_constraints_changed()
        return changed

    def selected_pin_artwork_names(self) -> list[str]:
        """Visual parts following the selected pin's controlled bone/subtree."""
        candidate = self.selected_pinnable_part()
        return self.pin_artwork_names(candidate)

    def pin_artwork_names(self, candidate: Optional[Mapping]) -> list[str]:
        """Visual parts rigidly controlled by ``candidate``'s selected bone.

        This deliberately does not include artwork attached to parent bones.
        For the current Player Robot, the ``*_foot`` pin controls the toes/foot
        sprite, while the SVG's ``Lower Leg / Boot`` sprite remains attached to
        ``*_leg_l`` and must rotate as part of the knee solve.
        """
        selected = str(candidate.get("bone")) if candidate is not None else ""
        if not selected:
            return []
        descendants = {selected}
        changed = True
        while changed:
            changed = False
            for bone in self.doc.bones:
                name = str(bone.get("name") or "")
                if bone.get("parent") in descendants and name not in descendants:
                    descendants.add(name)
                    changed = True
        return [
            str(part.get("name") or part.get("bone") or "part")
            for part in self.doc.parts
            if part.get("bone") in descendants
        ]

    def selected_pin_adjacent_artwork_names(self) -> list[str]:
        """Return nearby parent-bone artwork that a pin cannot hold rigidly.

        This makes visual rigging limitations explicit.  A transform pin can
        lock one endpoint bone and descendants.  It cannot simultaneously lock
        artwork on the lower-leg/forearm parent while that parent rotates to
        satisfy IK.
        """
        candidate = self.selected_pinnable_part()
        if candidate is None:
            return []
        controlled = set(self.pin_artwork_names(candidate))
        nearby_bones = {
            str(candidate.get("lower") or ""),
            str(candidate.get("upper") or ""),
        }
        nearby_bones.discard("")
        return [
            str(part.get("name") or part.get("bone") or "part")
            for part in self.doc.parts
            if str(part.get("bone") or "") in nearby_bones
            and str(part.get("name") or part.get("bone") or "part") not in controlled
        ]

    # Backward-compatible aliases retained for the foot-oriented controls and
    # older tests. They now use the same general transform-pin authority.
    def selected_plantable_foot(self) -> Optional[dict]:
        candidate = self.selected_pinnable_part()
        return candidate if candidate is not None and candidate.get("role") == "foot" else None

    def selected_foot_leg(self) -> Optional[dict]:
        return self.selected_plantable_foot()

    def selected_foot_plant(self) -> Optional[dict]:
        pin = self.selected_part_pin()
        return pin if pin is not None and pin.get("role") == "foot" else None

    def planted_feet(self) -> set[str]:
        return {
            name
            for name in self.pinned_parts()
            if (pin_for_bone(self.doc, self.clip_name, name) or {}).get("role") == "foot"
        }

    def plantable_feet(self) -> list[dict]:
        return self.pinnable_feet()

    def plant_selected_foot_entire_clip(self, *, lock_rotation: bool = True) -> bool:
        if self.selected_plantable_foot() is None:
            return False
        return self.pin_selected_part_entire_clip(lock_rotation=lock_rotation)

    def plant_all_feet_entire_clip(self, *, lock_rotation: bool = True) -> int:
        return self.pin_all_feet_entire_clip(lock_rotation=lock_rotation)

    def release_selected_foot_plant(self) -> bool:
        if self.selected_plantable_foot() is None:
            return False
        return self.release_selected_part_pin()

    def release_all_foot_plants(self) -> int:
        feet = list(self.planted_feet())
        changed = sum(remove_pin(self.doc, self.clip_name, name) for name in feet)
        if changed:
            self.mark_constraints_changed()
        return changed

    def move_selected_foot_plant(self, target: tuple[float, float]) -> bool:
        if self.selected_plantable_foot() is None:
            return False
        return self.move_selected_part_pin(target)

    def insert_keys_here(self, channels: Optional[List[str]] = None) -> int:
        """Key sampled values at the current frame.

        ``None`` means the selected bone/endpoint, while an explicit empty list
        means the complete pose.
        """
        if channels is None:
            resolved = self.selected_animation_channels()
        elif channels:
            resolved = list(channels)
        else:
            resolved = list((self.clip().get("channels") or {}).keys())
        if not resolved:
            return 0
        sampled = self.doc.sample(self.clip_name, self.t())
        values = {
            name: sampled.get(name, self._unkeyed_channel_value(name, self.frame_idx))
            for name in resolved
        }
        return self.write_keys(values, force_new_channels=True)

    def dense_keyed_channels(self) -> list[str]:
        """Channels carrying explicit keys on effectively every clip frame."""
        frames = self.frames()
        key_map = self.channel_key_frames()
        return [name for name, keyed in key_map.items() if len(keyed) >= frames]

    def simplify_channels_to_pose_keys(
        self, channels: Optional[List[str]] = None
    ) -> int:
        """Reduce baked per-frame keys to the clip's important pose frames.

        Values at retained frames are sampled before mutation, so the important
        poses stay visually fixed while frames between them become true
        interpolations that respond naturally to later edits.
        """
        clip = self.clip()
        all_channels = clip.get("channels") or {}
        names = list(channels) if channels else list(all_channels)
        pose_frames = self.materialize_pose_keys()
        if not pose_frames:
            return 0
        loop = bool(clip.get("loop", True))
        changed = []
        for name in names:
            spec = all_channels.get(name)
            if not spec or "keys" not in spec:
                continue
            existing_frames = self.channel_key_frames(name).get(name, set())
            if existing_frames.issubset(set(pose_frames)):
                continue
            retained = []
            for frame in pose_frames:
                time = self.doc.frame_time(self.clip_name, frame)
                value = sample_channel_spec(spec, time, loop)
                retained.append([round(time, 4), round(float(value), 3), "smooth"])
            spec["keys"] = retained
            changed.append(name)
        if changed:
            self._mark_render_changed()
            self.animationChanged.emit(tuple(changed))
            self.poseKeysChanged.emit()
        return len(changed)

    def remove_keys_here(self, channels: List[str]) -> int:
        """Remove current-frame keys so interpolation controls this pose again."""
        clip = self.clip()
        loop = bool(clip.get("loop", True))
        current = self.frame_idx
        changed = []
        for name in channels:
            spec = (clip.get("channels") or {}).get(name)
            if not spec or "keys" not in spec or len(spec.get("keys") or []) <= 1:
                continue
            kept = []
            removed = False
            for key in spec["keys"]:
                if time_to_frame(float(key[0]), self.frames(), loop) == current:
                    removed = True
                else:
                    kept.append(key)
            if removed and kept:
                spec["keys"] = kept
                changed.append(name)
        if changed:
            self._mark_render_changed()
            self.animationChanged.emit(tuple(changed))
            self.poseKeysChanged.emit()
        return len(changed)

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

    def discard_last_undo_if_unchanged(self) -> bool:
        """Drop the latest speculative snapshot when the document is identical.

        Mouse presses create an undo boundary before a drag begins. A simple
        click/release used only for selection must not consume an Undo step.
        """
        if self._undo and self._undo[-1] == self._snapshot():
            self._undo.pop()
            return True
        return False

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
        self.poseKeysChanged.emit()
        self.constraintsChanged.emit()

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

    def _unkeyed_channel_value(self, channel: str, frame_idx: int) -> float:
        """Value an absent channel contributes before it is first authored.

        An absent animation channel is not always numerically zero. IK targets
        inherit their rig ``rest_*`` values, body opacity defaults to one, and a
        follow-lower hand pitch is derived from the solved skeleton.  First-key
        insertion uses this helper to bake the *pre-edit* discrete frame values
        before changing the touched frame.  Without that preservation a newly
        created one-key channel is constant over the entire clip, so the first
        drag of a previously static bone unexpectedly changes every pose.
        """
        frame_idx = max(0, min(self.frames() - 1, int(frame_idx)))
        if channel in {"root_x", "root_y"} or channel.startswith("bone."):
            return 0.0
        if channel == "body_opacity":
            return 1.0
        try:
            if channel in self.doc.build_skeleton().bones:
                return 0.0
        except Exception:  # noqa: BLE001 - incomplete rigs stay editable
            pass

        for leg in self.doc.ik_legs:
            prefix = str(leg.get("channel_prefix", "foot"))
            defaults = {
                f"{prefix}_x": float(leg.get("rest_x", 0.0)),
                f"{prefix}_lift": float(leg.get("rest_lift", 0.0)),
                f"{prefix}_pitch": float(leg.get("rest_pitch", 0.0)),
                f"{prefix}_bend": float(leg.get("bend", 1.0)),
            }
            if channel in defaults:
                return defaults[channel]

        for chain in self.doc.ik_chains:
            prefix = str(chain.get("channel_prefix", "target"))
            if channel == f"{prefix}_x":
                return float(chain.get("rest_x", 0.0))
            if channel == f"{prefix}_y":
                return float(chain.get("rest_y", 0.0))
            if channel == f"{prefix}_bend":
                return float(chain.get("bend", 1.0))
            if channel == f"{prefix}_pitch":
                if str(chain.get("pitch_mode", "world")) == "world":
                    return float(chain.get("rest_pitch", 0.0))
                end = chain.get("end")
                if end:
                    try:
                        t = self.doc.frame_time(self.clip_name, frame_idx)
                        world, _params = self.doc.solve(self.clip_name, t)
                        if end in world:
                            return float(world[end].angle)
                    except Exception:  # noqa: BLE001
                        pass
                return 0.0

        # Per-part visibility channels are hidden unless explicitly driven.
        if any(part.get("opacity_channel") == channel for part in self.doc.parts):
            return 0.0
        return 0.0

    def _unkeyed_channel_varies_by_frame(self, channel: str) -> bool:
        """Whether the implicit value cannot be represented by one constant.

        Most absent channels mean a fixed rest value. The exception currently
        present in the rig format is a generic IK end using ``follow_lower``
        pitch: its implicit world pitch follows a moving parent and must be
        sampled across the clip before materializing that channel.
        """
        for chain in self.doc.ik_chains:
            prefix = str(chain.get("channel_prefix", "target"))
            if channel == f"{prefix}_pitch":
                return str(chain.get("pitch_mode", "world")) == "follow_lower"
        return False

    def _seed_unkeyed_channel(self, channel: str) -> dict:
        """Materialize baseline guards without changing other authored frames.

        A single first key would make the whole channel constant. For ordinary
        fixed rest values, the touched frame plus its immediate neighbors are
        enough to guard every other discrete pose while keeping the channel
        sparse. Frame-varying implicit values (currently follow-lower IK pitch)
        are sampled densely because there is no single baseline scalar to guard.
        """
        frames = self.frames()
        current = self.frame_idx
        if self._unkeyed_channel_varies_by_frame(channel):
            seed_frames = list(range(frames))
        elif frames <= 1:
            seed_frames = [0]
        elif bool(self.clip().get("loop", True)):
            seed_frames = sorted({(current - 1) % frames, current, (current + 1) % frames})
        else:
            seed_frames = sorted({max(0, current - 1), current, min(frames - 1, current + 1)})
        return {
            "keys": [
                [
                    round(self.doc.frame_time(self.clip_name, i), 4),
                    round(self._unkeyed_channel_value(channel, i), 3),
                    "linear",
                ]
                for i in seed_frames
            ]
        }

    @profile
    def _write_key_value(
        self,
        channel: str,
        value: float,
        ease: str,
        *,
        force_new_channel: bool = False,
    ) -> bool:
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
            rounded = round(float(value), 3)
            baseline = round(self._unkeyed_channel_value(channel, self.frame_idx), 3)
            if rounded == baseline and not force_new_channel:
                return False
            spec = self._seed_unkeyed_channel(channel)
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
        *,
        force_new_channels: bool = False,
    ) -> int:
        """Write multiple current-frame keys and notify the editor once.

        Returns the number of channels whose stored data changed. This is the
        path used by foot dragging, two-bone IK, and pose paste so one mouse
        event cannot trigger several complete render/refresh cycles.
        """
        changed = tuple(
            channel
            for channel, value in values.items()
            if self._write_key_value(
                channel,
                value,
                ease,
                force_new_channel=force_new_channels,
            )
        )
        if changed:
            pose_keys, explicit = self.pose_key_frames()
            pose_key_changed = (not explicit) or self.frame_idx not in pose_keys
            keys = set(pose_keys)
            keys.add(self.frame_idx)
            self.clip()["pose_keys"] = sorted(keys)
            self._mark_render_changed()
            self.animationChanged.emit(changed)
            if pose_key_changed:
                self.poseKeysChanged.emit()
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
