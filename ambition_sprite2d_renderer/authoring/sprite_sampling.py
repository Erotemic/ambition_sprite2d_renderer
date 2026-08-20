"""Sprite-bake sampling policies for continuous Ambition motion.

Animation authoring is intentionally independent from sprite publication.  This
module chooses economical sample times from an already-evaluable clip.  The
primary plan is non-uniform and therefore suitable for previews and a future
runtime that accepts per-frame durations.  ``uniform_compatibility_plan`` keeps
the same quality metric while choosing a single cadence for the current sheet
runtime.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

from .motion_evaluation import sample_clip_state
from .motion_ir import ClipDefinition, PreparedCharacterMotion, PoseState, Transform2D

_EPS = 1e-8


@dataclass(frozen=True)
class SpriteBakeProfile:
    """Quality/budget policy for converting continuous motion to held sprites."""

    max_joint_error_px: float = 3.0
    max_rotation_error_deg: float = 7.5
    max_hold_ms: float = 250.0
    max_frames: int = 16
    probe_fractions: tuple[float, ...] = (0.25, 0.5, 0.75)
    include_named_pose_anchors: bool = True
    include_markers: bool = True

    def validate(self) -> None:
        if self.max_joint_error_px <= 0.0:
            raise ValueError("max_joint_error_px must be positive")
        if self.max_rotation_error_deg <= 0.0:
            raise ValueError("max_rotation_error_deg must be positive")
        if self.max_hold_ms <= 0.0:
            raise ValueError("max_hold_ms must be positive")
        if self.max_frames < 1:
            raise ValueError("max_frames must be at least one")
        if not self.probe_fractions or any(not (0.0 < f < 1.0) for f in self.probe_fractions):
            raise ValueError("probe_fractions must lie strictly inside (0, 1)")


@dataclass(frozen=True)
class SpriteSample:
    at_s: float
    duration_s: float


@dataclass(frozen=True)
class SpriteSamplePlan:
    clip_id: str
    samples: tuple[SpriteSample, ...]
    max_error_ratio: float
    max_joint_error_px: float
    max_rotation_error_deg: float
    budget_exhausted: bool
    mode: str

    @property
    def frame_count(self) -> int:
        return len(self.samples)

    @property
    def sample_times(self) -> tuple[float, ...]:
        return tuple(sample.at_s for sample in self.samples)

    def to_dict(self) -> dict[str, object]:
        return {
            "clip": self.clip_id,
            "mode": self.mode,
            "frame_count": self.frame_count,
            "budget_exhausted": self.budget_exhausted,
            "max_error_ratio": round(self.max_error_ratio, 6),
            "max_joint_error_px": round(self.max_joint_error_px, 6),
            "max_rotation_error_deg": round(self.max_rotation_error_deg, 6),
            "samples": [
                {
                    "at_s": round(sample.at_s, 6),
                    "duration_ms": round(sample.duration_s * 1000.0, 3),
                }
                for sample in self.samples
            ],
        }


@dataclass(frozen=True)
class _WorldBone:
    origin: tuple[float, float]
    tip: tuple[float, float]
    rotation_deg: float
    scale: tuple[float, float]


def _rotate(point: tuple[float, float], degrees: float) -> tuple[float, float]:
    radians = math.radians(degrees)
    c = math.cos(radians)
    s = math.sin(radians)
    return (point[0] * c - point[1] * s, point[0] * s + point[1] * c)


def _mul(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    return (a[0] * b[0], a[1] * b[1])


def _add(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    return (a[0] + b[0], a[1] + b[1])


def _world_bones(prepared: PreparedCharacterMotion, state: PoseState) -> dict[str, _WorldBone]:
    root_position = state.root.position
    root_rotation = state.root.rotation_deg
    root_scale = state.root.scale
    world: dict[str, _WorldBone] = {}
    for bone in prepared.rig.bones:
        delta = state.bones.get(bone.id, Transform2D())
        local_position = (
            bone.rest.position[0] + delta.position[0],
            bone.rest.position[1] + delta.position[1],
        )
        local_rotation = bone.rest.rotation_deg + delta.rotation_deg
        local_scale = (
            bone.rest.scale[0] * delta.scale[0],
            bone.rest.scale[1] * delta.scale[1],
        )
        if bone.parent is None:
            origin = _add(root_position, _rotate(_mul(local_position, root_scale), root_rotation))
            rotation = root_rotation + local_rotation
            scale = _mul(root_scale, local_scale)
        else:
            parent = world[bone.parent]
            origin = _add(parent.origin, _rotate(_mul(local_position, parent.scale), parent.rotation_deg))
            rotation = parent.rotation_deg + local_rotation
            scale = _mul(parent.scale, local_scale)
        tip = _add(origin, _rotate((bone.length * scale[0], 0.0), rotation))
        world[bone.id] = _WorldBone(origin=origin, tip=tip, rotation_deg=rotation, scale=scale)
    return world


def _angle_error(a: float, b: float) -> float:
    # Winding matters while authoring, but a held raster only cares about the
    # visual orientation at a sample.  Compare the nearest equivalent angle.
    delta = (float(a) - float(b) + 180.0) % 360.0 - 180.0
    return abs(delta)


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def pose_visual_error(
    prepared: PreparedCharacterMotion,
    held: PoseState,
    actual: PoseState,
    profile: SpriteBakeProfile,
) -> tuple[float, float, float]:
    """Return ``(ratio, max_joint_px, max_rotation_deg)`` between two poses."""

    px_per_unit = prepared.binding.render.frame_px_per_rig_unit
    joint_error = _distance(held.root.position, actual.root.position) * px_per_unit
    rotation_error = _angle_error(held.root.rotation_deg, actual.root.rotation_deg)
    held_world = _world_bones(prepared, held)
    actual_world = _world_bones(prepared, actual)
    for bone_id in held_world:
        a = held_world[bone_id]
        b = actual_world[bone_id]
        joint_error = max(
            joint_error,
            _distance(a.origin, b.origin) * px_per_unit,
            _distance(a.tip, b.tip) * px_per_unit,
        )
        rotation_error = max(rotation_error, _angle_error(a.rotation_deg, b.rotation_deg))
    ratio = max(
        joint_error / profile.max_joint_error_px,
        rotation_error / profile.max_rotation_error_deg,
    )
    return ratio, joint_error, rotation_error


def _state(prepared: PreparedCharacterMotion, clip: ClipDefinition, at_s: float) -> PoseState:
    return sample_clip_state(
        prepared.library,
        clip,
        at_s,
        bone_ids=prepared.rig.bone_by_id,
    )


def _probe_times(
    clip: ClipDefinition,
    start: float,
    end: float,
    profile: SpriteBakeProfile,
) -> tuple[float, ...]:
    if end - start <= _EPS:
        return ()
    probes = {start + (end - start) * fraction for fraction in profile.probe_fractions}
    # Authored keys are high-information places to inspect, but they are not
    # mandatory sprite frames.  If the held image already approximates them,
    # the sampler is free to omit them.
    for key in clip.pose_keys:
        if start + _EPS < key.at_s < end - _EPS:
            probes.add(key.at_s)
    for track in clip.tracks:
        for key in track.keys:
            if start + _EPS < key.at_s < end - _EPS:
                probes.add(key.at_s)
    return tuple(sorted(probes))


def _lerp_transform(a: Transform2D, b: Transform2D, u: float) -> Transform2D:
    return Transform2D(
        position=(
            a.position[0] + (b.position[0] - a.position[0]) * u,
            a.position[1] + (b.position[1] - a.position[1]) * u,
        ),
        # Keep authored winding literal here.  The comparison below reduces the
        # final visual orientation modulo 360, but the approximating motion
        # itself follows the same unwrapped scalar convention as the IR.
        rotation_deg=a.rotation_deg + (b.rotation_deg - a.rotation_deg) * u,
        scale=(
            a.scale[0] + (b.scale[0] - a.scale[0]) * u,
            a.scale[1] + (b.scale[1] - a.scale[1]) * u,
        ),
    )


def _lerp_state(a: PoseState, b: PoseState, u: float) -> PoseState:
    bone_ids = set(a.bones) | set(b.bones)
    parameter_ids = set(a.parameters) | set(b.parameters)
    return PoseState(
        root=_lerp_transform(a.root, b.root, u),
        bones={
            bone_id: _lerp_transform(
                a.bones.get(bone_id, Transform2D()),
                b.bones.get(bone_id, Transform2D()),
                u,
            )
            for bone_id in bone_ids
        },
        parameters={
            name: a.parameters.get(name, 0.0)
            + (b.parameters.get(name, 0.0) - a.parameters.get(name, 0.0)) * u
            for name in parameter_ids
        },
    )


def _interval_error(
    prepared: PreparedCharacterMotion,
    clip: ClipDefinition,
    start: float,
    end: float,
    profile: SpriteBakeProfile,
) -> tuple[float, float, float, float]:
    start_state = _state(prepared, clip, start)
    end_state = _state(prepared, clip, end)
    worst_ratio = 0.0
    worst_joint = 0.0
    worst_rotation = 0.0
    split = (start + end) * 0.5
    span = max(end - start, _EPS)
    for at_s in _probe_times(clip, start, end, profile):
        u = (at_s - start) / span
        approximation = _lerp_state(start_state, end_state, u)
        ratio, joint, rotation = pose_visual_error(
            prepared, approximation, _state(prepared, clip, at_s), profile
        )
        if ratio > worst_ratio:
            worst_ratio = ratio
            worst_joint = joint
            worst_rotation = rotation
            split = at_s
    # Even perfectly linear motion needs a temporal density cap once it is baked
    # to held bitmaps.  This is deliberately separate from the curve error.
    hold_ratio = (end - start) * 1000.0 / profile.max_hold_ms
    if hold_ratio > worst_ratio:
        worst_ratio = hold_ratio
        # Split at the hold cap rather than the midpoint.  That reaches the
        # minimum number of held frames for long nearly-linear intervals (for
        # example a 1.2 s quiet idle at 250 ms needs five samples, not the eight
        # produced by recursive binary subdivision).
        split = min(end, start + profile.max_hold_ms / 1000.0)
    return worst_ratio, worst_joint, worst_rotation, split


def _mandatory_times(clip: ClipDefinition, profile: SpriteBakeProfile) -> list[float]:
    times = {0.0}
    if profile.include_named_pose_anchors:
        times.update(key.at_s for key in clip.pose_keys if key.pose is not None)
    if profile.include_markers:
        times.update(marker.at_s for marker in clip.markers)
    return sorted(t for t in times if -_EPS <= t < clip.duration_s - _EPS)


def _make_plan(
    clip: ClipDefinition,
    times: Sequence[float],
    *,
    max_error_ratio: float,
    max_joint_error_px: float,
    max_rotation_error_deg: float,
    budget_exhausted: bool,
    mode: str,
) -> SpriteSamplePlan:
    ordered = tuple(sorted(set(max(0.0, min(float(t), clip.duration_s)) for t in times)))
    samples: list[SpriteSample] = []
    for index, at_s in enumerate(ordered):
        end = ordered[index + 1] if index + 1 < len(ordered) else clip.duration_s
        samples.append(SpriteSample(at_s=at_s, duration_s=max(0.0, end - at_s)))
    return SpriteSamplePlan(
        clip_id=clip.id,
        samples=tuple(samples),
        max_error_ratio=max_error_ratio,
        max_joint_error_px=max_joint_error_px,
        max_rotation_error_deg=max_rotation_error_deg,
        budget_exhausted=budget_exhausted,
        mode=mode,
    )


def adaptive_sample_plan(
    prepared: PreparedCharacterMotion,
    clip_id: str,
    profile: SpriteBakeProfile = SpriteBakeProfile(),
) -> SpriteSamplePlan:
    """Choose non-uniform sprite times under curve-error and hold-duration budgets."""

    profile.validate()
    clip = prepared.library.clips[clip_id]
    times = _mandatory_times(clip, profile)
    if not times:
        times = [0.0]
    budget_exhausted = len(times) > profile.max_frames
    if budget_exhausted:
        times = times[: profile.max_frames]

    while len(times) < profile.max_frames:
        boundaries = sorted(times) + [clip.duration_s]
        worst: tuple[float, float, float, float] | None = None
        for index in range(len(boundaries) - 1):
            start, end = boundaries[index], boundaries[index + 1]
            result = _interval_error(prepared, clip, start, end, profile)
            if worst is None or result[0] > worst[0]:
                worst = result
        if worst is None or worst[0] <= 1.0 + 1e-6:
            break
        split = worst[3]
        if any(abs(split - existing) <= _EPS for existing in times):
            break
        times.append(split)
        times.sort()

    max_ratio = 0.0
    max_joint = 0.0
    max_rotation = 0.0
    boundaries = sorted(times) + [clip.duration_s]
    for index in range(len(boundaries) - 1):
        ratio, joint, rotation, _split = _interval_error(
            prepared, clip, boundaries[index], boundaries[index + 1], profile
        )
        max_ratio = max(max_ratio, ratio)
        max_joint = max(max_joint, joint)
        max_rotation = max(max_rotation, rotation)
    budget_exhausted = budget_exhausted or max_ratio > 1.0 + 1e-6
    return _make_plan(
        clip,
        times,
        max_error_ratio=max_ratio,
        max_joint_error_px=max_joint,
        max_rotation_error_deg=max_rotation,
        budget_exhausted=budget_exhausted,
        mode="adaptive",
    )


def uniform_compatibility_plan(
    prepared: PreparedCharacterMotion,
    clip_id: str,
    profile: SpriteBakeProfile = SpriteBakeProfile(),
) -> SpriteSamplePlan:
    """Choose the smallest uniform frame count satisfying the same quality metric.

    The current game-facing sheet format has one duration per animation row.
    This adapter therefore preserves the continuous-motion architecture while
    selecting an economical *uniform* cadence until per-frame durations are a
    runtime feature.
    """

    profile.validate()
    clip = prepared.library.clips[clip_id]
    best: SpriteSamplePlan | None = None
    for frame_count in range(1, profile.max_frames + 1):
        step = clip.duration_s / frame_count
        times = [index * step for index in range(frame_count)]
        max_ratio = 0.0
        max_joint = 0.0
        max_rotation = 0.0
        for index, start in enumerate(times):
            end = times[index + 1] if index + 1 < frame_count else clip.duration_s
            ratio, joint, rotation, _split = _interval_error(prepared, clip, start, end, profile)
            max_ratio = max(max_ratio, ratio)
            max_joint = max(max_joint, joint)
            max_rotation = max(max_rotation, rotation)
        best = _make_plan(
            clip,
            times,
            max_error_ratio=max_ratio,
            max_joint_error_px=max_joint,
            max_rotation_error_deg=max_rotation,
            budget_exhausted=max_ratio > 1.0 + 1e-6,
            mode="uniform-compatibility",
        )
        if max_ratio <= 1.0 + 1e-6:
            return best
    assert best is not None
    return best


__all__ = [
    "SpriteBakeProfile",
    "SpriteSample",
    "SpriteSamplePlan",
    "adaptive_sample_plan",
    "pose_visual_error",
    "uniform_compatibility_plan",
]
