"""Continuous evaluation for the Ambition motion IR.

The motion JSON describes animation in time.  Sprite publication is one backend
that samples that motion; Godot is another frontend that edits it.  Keeping the
evaluator here prevents either backend from turning its own frame/key layout into
the meaning of a clip.
"""
from __future__ import annotations

from dataclasses import replace
import math
import re
from typing import Iterable, Sequence

from .motion_ir import (
    ClipDefinition,
    MotionLibrary,
    PoseState,
    ScalarKey,
    ScalarTrack,
    Transform2D,
)

_EPS = 1e-9


def _ease(name: str, u: float) -> float:
    u = max(0.0, min(1.0, float(u)))
    if name == "linear":
        return u
    if name == "smooth":
        return u * u * (3.0 - 2.0 * u)
    if name == "in":
        return u * u * u
    if name == "out":
        return 1.0 - (1.0 - u) ** 3
    if name == "sine":
        return 0.5 - 0.5 * math.cos(math.pi * u)
    if name == "hold":
        return 1.0 if u >= 1.0 - _EPS else 0.0
    raise ValueError(f"unsupported motion interpolation {name!r}")


def _lerp(a: float, b: float, u: float) -> float:
    return float(a) + (float(b) - float(a)) * float(u)


def _segment_sample(
    keys: Sequence[tuple[float, float, str]],
    at_s: float,
    *,
    duration_s: float,
    loop: bool,
) -> float:
    """Sample scalar keys whose interpolation labels the segment into each key."""

    if not keys:
        raise ValueError("cannot sample an empty key sequence")
    if len(keys) == 1:
        return float(keys[0][1])

    if loop:
        t = float(at_s) % duration_s
        first_t, first_v, first_interp = keys[0]
        last_t, last_v, _last_interp = keys[-1]
        if t < first_t or t >= last_t:
            span = (duration_s - last_t) + first_t
            if span <= _EPS:
                return float(first_v)
            u = ((t - last_t) % duration_s) / span
            return _lerp(last_v, first_v, _ease(first_interp, u))
    else:
        t = max(0.0, min(float(at_s), duration_s))
        if t <= keys[0][0] + _EPS:
            return float(keys[0][1])
        if t >= keys[-1][0] - _EPS:
            return float(keys[-1][1])

    for index in range(len(keys) - 1):
        ta, va, _ia = keys[index]
        tb, vb, ib = keys[index + 1]
        if ta - _EPS <= t <= tb + _EPS:
            span = tb - ta
            if span <= _EPS:
                return float(vb)
            u = (t - ta) / span
            return _lerp(va, vb, _ease(ib, u))
    return float(keys[-1][1])


def _transform_component(transform: Transform2D, component: str) -> float:
    if component == "position.x":
        return transform.position[0]
    if component == "position.y":
        return transform.position[1]
    if component == "rotation_deg":
        return transform.rotation_deg
    if component == "scale.x":
        return transform.scale[0]
    if component == "scale.y":
        return transform.scale[1]
    raise ValueError(f"unknown transform component {component!r}")


def _replace_transform_component(transform: Transform2D, component: str, value: float) -> Transform2D:
    if component == "position.x":
        return replace(transform, position=(value, transform.position[1]))
    if component == "position.y":
        return replace(transform, position=(transform.position[0], value))
    if component == "rotation_deg":
        return replace(transform, rotation_deg=value)
    if component == "scale.x":
        return replace(transform, scale=(value, transform.scale[1]))
    if component == "scale.y":
        return replace(transform, scale=(transform.scale[0], value))
    raise ValueError(f"unknown transform component {component!r}")


def state_target_value(state: PoseState, target: str) -> float:
    """Read one backend-neutral scalar target from a pose state."""

    if target.startswith("root."):
        return _transform_component(state.root, target[len("root.") :])
    match = re.fullmatch(r"bone\.([^.]+)\.(position\.[xy]|rotation_deg|scale\.[xy])", target)
    if match:
        transform = state.bones.get(match.group(1), Transform2D())
        return _transform_component(transform, match.group(2))
    if target.startswith("parameter."):
        return float(state.parameters.get(target[len("parameter.") :], 0.0))
    raise ValueError(f"unknown motion track target {target!r}")


def state_with_target_value(state: PoseState, target: str, value: float) -> PoseState:
    """Return *state* with one backend-neutral scalar target replaced."""

    if target.startswith("root."):
        return replace(state, root=_replace_transform_component(state.root, target[len("root.") :], value))
    match = re.fullmatch(r"bone\.([^.]+)\.(position\.[xy]|rotation_deg|scale\.[xy])", target)
    if match:
        bones = dict(state.bones)
        bone_id = match.group(1)
        bones[bone_id] = _replace_transform_component(
            bones.get(bone_id, Transform2D()), match.group(2), value
        )
        return replace(state, bones=bones)
    if target.startswith("parameter."):
        parameters = dict(state.parameters)
        parameters[target[len("parameter.") :]] = float(value)
        return replace(state, parameters=parameters)
    raise ValueError(f"unknown motion track target {target!r}")


def sample_scalar_track(track: ScalarTrack, at_s: float, *, duration_s: float, loop: bool) -> float:
    keys = [(key.at_s, key.value, key.interpolation) for key in track.keys]
    return _segment_sample(keys, at_s, duration_s=duration_s, loop=loop)


def _pose_value_keys(
    library: MotionLibrary,
    clip: ClipDefinition,
    target: str,
) -> list[tuple[float, float, str]]:
    return [
        (
            key.at_s,
            state_target_value(library.resolve_pose_key(key), target),
            key.interpolation,
        )
        for key in clip.pose_keys
    ]


def sample_pose_backbone(
    library: MotionLibrary,
    clip: ClipDefinition,
    at_s: float,
    *,
    bone_ids: Iterable[str] | None = None,
) -> PoseState:
    """Evaluate just the whole-body pose-key backbone of a clip."""

    if not clip.pose_keys:
        return PoseState()
    states = [library.resolve_pose_key(key) for key in clip.pose_keys]
    bones = set(bone_ids or ())
    for state in states:
        bones.update(state.bones)
    parameters: set[str] = set()
    for state in states:
        parameters.update(state.parameters)

    def sample(target: str) -> float:
        return _segment_sample(
            _pose_value_keys(library, clip, target),
            at_s,
            duration_s=clip.duration_s,
            loop=clip.loop,
        )

    root = Transform2D(
        position=(sample("root.position.x"), sample("root.position.y")),
        rotation_deg=sample("root.rotation_deg"),
        scale=(sample("root.scale.x"), sample("root.scale.y")),
    )
    bone_states = {
        bone_id: Transform2D(
            position=(
                sample(f"bone.{bone_id}.position.x"),
                sample(f"bone.{bone_id}.position.y"),
            ),
            rotation_deg=sample(f"bone.{bone_id}.rotation_deg"),
            scale=(
                sample(f"bone.{bone_id}.scale.x"),
                sample(f"bone.{bone_id}.scale.y"),
            ),
        )
        for bone_id in sorted(bones)
    }
    parameter_values = {
        name: sample(f"parameter.{name}") for name in sorted(parameters)
    }
    return PoseState(root=root, bones=bone_states, parameters=parameter_values)


def sample_clip_state(
    library: MotionLibrary,
    clip: ClipDefinition,
    at_s: float,
    *,
    bone_ids: Iterable[str] | None = None,
) -> PoseState:
    """Evaluate an Ambition clip at an arbitrary time in seconds.

    Pose keys form the whole-body backbone.  Independent scalar tracks are
    absolute property curves and replace the corresponding backbone property.
    This is the same composition used by the compatibility renderer projection,
    but it is expressed directly in IR time rather than sprite frame indices.
    """

    state = sample_pose_backbone(library, clip, at_s, bone_ids=bone_ids)
    for track in clip.tracks:
        value = sample_scalar_track(track, at_s, duration_s=clip.duration_s, loop=clip.loop)
        state = state_with_target_value(state, track.target, value)
    return state


def semantic_scalar_targets(bone_ids: Iterable[str]) -> tuple[str, ...]:
    targets = ["root.position.x", "root.position.y"]
    for bone_id in bone_ids:
        targets.extend(
            (
                f"bone.{bone_id}.position.x",
                f"bone.{bone_id}.position.y",
                f"bone.{bone_id}.rotation_deg",
            )
        )
    return tuple(targets)


def pose_backbone_track(
    library: MotionLibrary,
    clip: ClipDefinition,
    target: str,
) -> ScalarTrack:
    return ScalarTrack(
        target=target,
        keys=tuple(
            ScalarKey(
                at_s=key.at_s,
                value=state_target_value(library.resolve_pose_key(key), target),
                interpolation=key.interpolation,
            )
            for key in clip.pose_keys
        ),
    )


def effective_scalar_track(
    library: MotionLibrary,
    clip: ClipDefinition,
    target: str,
) -> ScalarTrack:
    for track in clip.tracks:
        if track.target == target:
            return track
    return pose_backbone_track(library, clip, target)


__all__ = [
    "effective_scalar_track",
    "pose_backbone_track",
    "sample_clip_state",
    "sample_pose_backbone",
    "sample_scalar_track",
    "semantic_scalar_targets",
    "state_target_value",
    "state_with_target_value",
]
