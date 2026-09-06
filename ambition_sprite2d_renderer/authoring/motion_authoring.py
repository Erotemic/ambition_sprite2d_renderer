"""Agent-facing semantic motion authoring for bone-rigged characters.

The existing rig editor is deliberately low-level and precise: it exposes
channels, FK rotations, IK endpoints, transform pins, and pose keys.  This
module adds a complementary *semantic* layer for automation agents.  Agents can
say where a hand or foot should be, which side an elbow/knee should bend toward,
and which animation phase a frame represents without reconstructing the rig's
channel conventions on every character.

This is authoring tooling only.  The emitted rig document remains ordinary
``RigDocument`` JSON; no runtime schema or engine dependency is introduced.

Coordinate conventions follow :mod:`rigdoc`: frame pixels, y down, side-view
characters authored facing +X.  Endpoint goals may use absolute frame pixels,
normalized frame coordinates, root-relative offsets, or center/ground-relative
coordinates.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from .animation_keys import time_to_frame
from .rigdoc import RigDocument, sample_channel_spec
from .skeleton import two_bone_ik
from ambition_sprite2d_renderer.yaml_io import safe_dump, safe_load

Point = tuple[float, float]


@dataclass(frozen=True)
class PhaseKey:
    """One semantically named important pose within an animation template."""

    role: str
    t: float
    intent: str


PHASE_TEMPLATES: dict[str, tuple[PhaseKey, ...]] = {
    "walk": (
        PhaseKey("contact_near", 0.00, "Near foot establishes contact; far foot finishes swing."),
        PhaseKey("down_near", 0.125, "Weight settles over the near support leg."),
        PhaseKey("passing_near", 0.25, "Far foot passes the support foot; pelvis crosses midline."),
        PhaseKey("up_near", 0.375, "Body rises as the far leg prepares contact."),
        PhaseKey("contact_far", 0.50, "Far foot establishes contact; near foot finishes swing."),
        PhaseKey("down_far", 0.625, "Weight settles over the far support leg."),
        PhaseKey("passing_far", 0.75, "Near foot passes the support foot; pelvis crosses midline."),
        PhaseKey("up_far", 0.875, "Body rises as the near leg prepares contact."),
    ),
    "run": (
        PhaseKey("contact_near", 0.00, "Near foot contact under a forward-moving pelvis."),
        PhaseKey("compression_near", 0.125, "Near leg absorbs load; torso remains committed forward."),
        PhaseKey("flight_near", 0.25, "Both feet leave the ground; limbs cross through passing."),
        PhaseKey("recovery_near", 0.375, "Far leg reaches for the next contact."),
        PhaseKey("contact_far", 0.50, "Far foot contact."),
        PhaseKey("compression_far", 0.625, "Far leg absorbs load."),
        PhaseKey("flight_far", 0.75, "Second flight phase."),
        PhaseKey("recovery_far", 0.875, "Near leg reaches for the loop seam contact."),
    ),
    "melee_strike": (
        PhaseKey("ready", 0.00, "Readable neutral/guard pose."),
        PhaseKey("anticipation", 0.20, "Load away from the strike and create silhouette contrast."),
        PhaseKey("commit", 0.42, "Center of mass and striking limb accelerate into the attack."),
        PhaseKey("contact", 0.58, "Maximum readable extension at gameplay contact."),
        PhaseKey("follow_through", 0.76, "Momentum continues beyond contact rather than stopping dead."),
        PhaseKey("recovery", 1.00, "Return to a stance that can transition cleanly."),
    ),
    "smash_attack": (
        PhaseKey("ready", 0.00, "Readable neutral/guard pose."),
        PhaseKey("charge", 0.18, "Compressed held-energy pose with stable support."),
        PhaseKey("anticipation", 0.38, "Final counter-motion before release."),
        PhaseKey("commit", 0.52, "Explosive acceleration begins."),
        PhaseKey("contact", 0.62, "Gameplay-active maximum extension."),
        PhaseKey("follow_through", 0.78, "Large committed overshoot."),
        PhaseKey("endlag", 0.90, "Spent pose exposes commitment."),
        PhaseKey("recovery", 1.00, "Return toward reusable locomotion stance."),
    ),
    "jump": (
        PhaseKey("ready", 0.00, "Standing support before compression."),
        PhaseKey("crouch", 0.13, "Pelvis drops and legs compress."),
        PhaseKey("compression", 0.24, "Maximum stored energy before takeoff."),
        PhaseKey("takeoff", 0.34, "Feet release; legs begin extension."),
        PhaseKey("extension", 0.48, "Body lengthens through upward travel."),
        PhaseKey("apex", 0.66, "Vertical motion visually softens."),
        PhaseKey("fall", 0.82, "Limbs prepare for ground reacquisition."),
        PhaseKey("landing", 1.00, "Contact-ready landing shape."),
    ),
    "dash": (
        PhaseKey("ready", 0.00, "Balanced stance before movement."),
        PhaseKey("compression", 0.22, "Pelvis lowers; rear leg stores force."),
        PhaseKey("launch", 0.42, "Rear leg extends and body commits forward."),
        PhaseKey("flight", 0.62, "Maximum translation silhouette."),
        PhaseKey("catch", 0.82, "Lead foot prepares to absorb movement."),
        PhaseKey("settle", 1.00, "Stable exit pose."),
    ),
}


class PoseGoalError(ValueError):
    """Raised when a semantic goal cannot be mapped to the selected rig."""


def _clip(doc: RigDocument, clip_name: str) -> dict:
    if clip_name not in doc.clips:
        raise PoseGoalError(f"unknown clip {clip_name!r}; available: {', '.join(doc.clips)}")
    return doc.clips[clip_name]


def _frame_t(doc: RigDocument, clip_name: str, frame_idx: int) -> float:
    clip = _clip(doc, clip_name)
    frames = max(1, int(clip.get("frames", 1)))
    frame_idx = max(0, min(frames - 1, int(frame_idx)))
    return doc.frame_time(clip_name, frame_idx, frames)


def _materialize_keys(doc: RigDocument, clip_name: str, channel: str) -> dict:
    """Return a mutable key spec, preserving the channel's prior sampled motion.

    Constants/expressions are baked across authored frames before a semantic
    edit is inserted.  That mirrors the GUI editor's behavior and ensures a
    one-frame agent edit does not silently destroy the rest of the clip.
    """

    clip = _clip(doc, clip_name)
    channels = clip.setdefault("channels", {})
    spec = channels.get(channel)
    if spec is not None and "keys" in spec:
        return spec

    frames = max(1, int(clip.get("frames", 1)))
    loop = bool(clip.get("loop", True))
    if spec is None:
        spec = {"const": 0.0}
    baked = {
        "keys": [
            [
                round(doc.frame_time(clip_name, i, frames), 4),
                round(float(sample_channel_spec(spec, doc.frame_time(clip_name, i, frames), loop)), 3),
                "linear",
            ]
            for i in range(frames)
        ]
    }
    channels[channel] = baked
    return baked


def upsert_channel_key(
    doc: RigDocument,
    clip_name: str,
    frame_idx: int,
    channel: str,
    value: float,
    *,
    ease: str = "smooth",
) -> None:
    """Insert or replace one channel key at an authored frame."""

    clip = _clip(doc, clip_name)
    frames = max(1, int(clip.get("frames", 1)))
    loop = bool(clip.get("loop", True))
    spec = _materialize_keys(doc, clip_name, channel)
    t = round(_frame_t(doc, clip_name, frame_idx), 4)
    rounded = round(float(value), 3)
    for key in spec["keys"]:
        if time_to_frame(float(key[0]), frames, loop) == int(frame_idx):
            key[0] = t
            key[1] = rounded
            if len(key) >= 3:
                key[2] = ease
            else:
                key.append(ease)
            break
    else:
        spec["keys"].append([t, rounded, ease])
    spec["keys"].sort(key=lambda key: float(key[0]))


def write_pose_keys(
    doc: RigDocument,
    clip_name: str,
    frame_idx: int,
    values: Mapping[str, float],
    *,
    ease: str = "smooth",
    mark_pose_key: bool = True,
) -> None:
    """Write a coherent semantic pose edit as one set of channel keys."""

    for channel, value in values.items():
        upsert_channel_key(doc, clip_name, frame_idx, channel, value, ease=ease)
    if mark_pose_key:
        clip = _clip(doc, clip_name)
        keys = {int(frame) for frame in clip.get("pose_keys") or []}
        keys.add(int(frame_idx))
        clip["pose_keys"] = sorted(keys)


def _resolve_point(doc: RigDocument, params: Mapping[str, float], spec: Any) -> Point:
    """Resolve a goal point from one of the supported semantic coordinate spaces."""

    if isinstance(spec, Sequence) and not isinstance(spec, (str, bytes)):
        if len(spec) != 2:
            raise PoseGoalError(f"point must contain exactly two numbers, got {spec!r}")
        value = (float(spec[0]), float(spec[1]))
        space = "frame"
    elif isinstance(spec, Mapping):
        raw = spec.get("value", spec.get("target", spec.get("point")))
        if raw is None or len(raw) != 2:
            raise PoseGoalError(f"point mapping needs value/target [x, y], got {spec!r}")
        value = (float(raw[0]), float(raw[1]))
        space = str(spec.get("space", "frame"))
    else:
        raise PoseGoalError(f"unsupported point goal {spec!r}")

    frame = doc.frame
    width = float(frame["width"])
    height = float(frame["height"])
    cx = float(frame.get("center_x", width / 2))
    gy = float(frame.get("ground_y", height - 2))
    root = (cx + float(params.get("root_x", 0.0)), gy + float(params.get("root_y", 0.0)))

    if space in {"frame", "world"}:
        return value
    if space in {"normalized", "norm"}:
        return value[0] * width, value[1] * height
    if space == "root":
        return root[0] + value[0], root[1] + value[1]
    if space in {"center_ground", "stage"}:
        return cx + value[0], gy + value[1]
    raise PoseGoalError(f"unknown point space {space!r}")


def _find_chain(doc: RigDocument, semantic: str) -> tuple[str, dict]:
    aliases = {
        "near_hand": ("chain", "near_hand"),
        "far_hand": ("chain", "far_hand"),
        "near_foot": ("leg", "near_foot"),
        "far_foot": ("leg", "far_foot"),
    }
    kind, prefix = aliases.get(semantic, ("auto", semantic))
    if kind in {"chain", "auto"}:
        for chain in doc.ik_chains:
            if chain.get("channel_prefix") == prefix or chain.get("end") == semantic:
                return "chain", chain
    if kind in {"leg", "auto"}:
        for leg in doc.ik_legs:
            if leg.get("channel_prefix") == prefix or leg.get("foot") == semantic:
                return "leg", leg
    raise PoseGoalError(
        f"rig {doc.name!r} has no IK endpoint for {semantic!r}; "
        "use direct channel goals for rigs without that chain"
    )


def _joint_for_bend(
    origin: Point,
    target: Point,
    upper_len: float,
    lower_len: float,
    bend: float,
) -> Point:
    a1, _a2 = two_bone_ik(origin, target, upper_len, lower_len, bend=bend)
    radians = math.radians(a1)
    return origin[0] + math.cos(radians) * upper_len, origin[1] + math.sin(radians) * upper_len


def _choose_bend(
    doc: RigDocument,
    world: Mapping[str, Any],
    chain: Mapping[str, Any],
    target: Point,
    preference: Any,
) -> float:
    if preference is None or preference == "preserve":
        return float(chain.get("bend", 1.0))
    if isinstance(preference, (int, float)):
        return 1.0 if float(preference) >= 0 else -1.0
    text = str(preference).lower()
    if text in {"positive", "+", "+1"}:
        return 1.0
    if text in {"negative", "-", "-1"}:
        return -1.0

    upper = str(chain["upper"])
    origin = world[upper].origin
    sk = doc.build_skeleton()
    upper_len = float(sk.bones[upper].length)
    lower_len = float(sk.bones[str(chain["lower"])].length)
    candidates = {
        1.0: _joint_for_bend(origin, target, upper_len, lower_len, 1.0),
        -1.0: _joint_for_bend(origin, target, upper_len, lower_len, -1.0),
    }
    if text in {"up", "elbow_up", "knee_up"}:
        return min(candidates, key=lambda sign: candidates[sign][1])
    if text in {"down", "elbow_down", "knee_down"}:
        return max(candidates, key=lambda sign: candidates[sign][1])
    if text in {"forward", "elbow_forward", "knee_forward"}:
        return max(candidates, key=lambda sign: candidates[sign][0])
    if text in {"back", "backward", "elbow_back", "knee_back"}:
        return min(candidates, key=lambda sign: candidates[sign][0])
    raise PoseGoalError(f"unknown bend preference {preference!r}")


def _clone_with_values(
    doc: RigDocument,
    clip_name: str,
    frame_idx: int,
    values: Mapping[str, float],
) -> RigDocument:
    clone = RigDocument(deepcopy(doc.data), source_path=doc.source_path)
    write_pose_keys(clone, clip_name, frame_idx, values, mark_pose_key=False)
    return clone


def endpoint_channels(
    doc: RigDocument,
    clip_name: str,
    frame_idx: int,
    semantic: str,
    goal: Mapping[str, Any],
    *,
    base_values: Mapping[str, float] | None = None,
) -> dict[str, float]:
    """Translate a semantic endpoint target into the rig's IK channels."""

    base_values = dict(base_values or {})
    working = _clone_with_values(doc, clip_name, frame_idx, base_values) if base_values else doc
    t = _frame_t(working, clip_name, frame_idx)
    world, params = working.solve(clip_name, t)
    target = _resolve_point(working, params, goal.get("target", goal))
    kind, chain = _find_chain(working, semantic)
    prefix = str(chain.get("channel_prefix"))
    bend = _choose_bend(working, world, chain, target, goal.get("bend"))
    frame = working.frame
    cx = float(frame.get("center_x", frame["width"] / 2))
    gy = float(frame.get("ground_y", frame["height"] - 2))

    result: dict[str, float] = {f"{prefix}_bend": bend}
    if kind == "leg":
        ankle_h = float(frame.get("ankle_h", 0.0))
        result[f"{prefix}_x"] = target[0] - cx
        result[f"{prefix}_lift"] = gy - ankle_h - target[1]
        if "pitch_deg" in goal:
            result[f"{prefix}_pitch"] = float(goal["pitch_deg"])
        elif "pitch" in goal:
            result[f"{prefix}_pitch"] = float(goal["pitch"])
    else:
        result[f"{prefix}_x"] = target[0] - cx
        result[f"{prefix}_y"] = target[1] - gy
        if "pitch_deg" in goal:
            result[f"{prefix}_pitch"] = float(goal["pitch_deg"])
        elif "pitch" in goal:
            result[f"{prefix}_pitch"] = float(goal["pitch"])
    return result


def _head_look_channels(
    doc: RigDocument,
    clip_name: str,
    frame_idx: int,
    target_spec: Any,
    base_values: Mapping[str, float],
    *,
    bone_name: str = "head",
) -> dict[str, float]:
    if doc.bone(bone_name) is None:
        raise PoseGoalError(f"rig {doc.name!r} has no {bone_name!r} bone")
    working = _clone_with_values(doc, clip_name, frame_idx, base_values)
    t = _frame_t(working, clip_name, frame_idx)
    world, params = working.solve(clip_name, t)
    target = _resolve_point(working, params, target_spec)
    sk = working.build_skeleton()
    bone = sk.bones[bone_name]
    parent_angle = world[bone.parent].angle if bone.parent else 0.0
    origin = world[bone_name].origin
    desired = math.degrees(math.atan2(target[1] - origin[1], target[0] - origin[0]))
    local = desired - parent_angle - bone.rest_angle
    return {bone_name: local}


def solve_pose_goals(
    doc: RigDocument,
    clip_name: str,
    frame_idx: int,
    goals: Mapping[str, Any],
) -> dict[str, float]:
    """Resolve semantic pose goals into concrete animation channel values.

    Supported keys include ``channels`` for an explicit escape hatch,
    ``root`` (offset/shift), ``bones`` (direct local pose angles), the semantic
    endpoints ``near_hand``/``far_hand``/``near_foot``/``far_foot``, and
    ``head.look_at``.
    """

    _clip(doc, clip_name)
    t = _frame_t(doc, clip_name, frame_idx)
    sampled = doc.sample(clip_name, t)
    values: dict[str, float] = {}

    for name, value in (goals.get("channels") or {}).items():
        values[str(name)] = float(value)

    root = goals.get("root") or {}
    if "offset" in root:
        offset = root["offset"]
        values["root_x"] = float(offset[0])
        values["root_y"] = float(offset[1])
    if "shift" in root:
        shift = root["shift"]
        values["root_x"] = float(sampled.get("root_x", 0.0)) + float(shift[0])
        values["root_y"] = float(sampled.get("root_y", 0.0)) + float(shift[1])

    for bone, spec in (goals.get("bones") or {}).items():
        if doc.bone(str(bone)) is None:
            raise PoseGoalError(f"rig {doc.name!r} has no bone {bone!r}")
        if isinstance(spec, Mapping):
            value = spec.get("angle_deg", spec.get("angle"))
        else:
            value = spec
        if value is None:
            raise PoseGoalError(f"bone goal {bone!r} needs angle_deg")
        values[str(bone)] = float(value)

    for semantic in ("near_hand", "far_hand", "near_foot", "far_foot"):
        if semantic in goals:
            values.update(
                endpoint_channels(
                    doc,
                    clip_name,
                    frame_idx,
                    semantic,
                    goals[semantic],
                    base_values=values,
                )
            )

    head = goals.get("head") or {}
    if "look_at" in head:
        values.update(
            _head_look_channels(
                doc,
                clip_name,
                frame_idx,
                head["look_at"],
                values,
                bone_name=str(head.get("bone", "head")),
            )
        )
    elif "angle_deg" in head:
        values[str(head.get("bone", "head"))] = float(head["angle_deg"])

    return values


def apply_pose_goals(
    doc: RigDocument,
    clip_name: str,
    frame_idx: int,
    goals: Mapping[str, Any],
    *,
    ease: str = "smooth",
) -> dict[str, float]:
    """Resolve semantic goals, write them into the rig, and return values."""

    values = solve_pose_goals(doc, clip_name, frame_idx, goals)
    write_pose_keys(doc, clip_name, frame_idx, values, ease=ease, mark_pose_key=True)
    return values


def phase_keys_for_frames(template: str, frames: int, *, loop: bool) -> list[dict[str, Any]]:
    if template not in PHASE_TEMPLATES:
        raise PoseGoalError(
            f"unknown phase template {template!r}; available: {', '.join(sorted(PHASE_TEMPLATES))}"
        )
    frames = max(1, int(frames))
    result: list[dict[str, Any]] = []
    used: set[int] = set()
    for phase in PHASE_TEMPLATES[template]:
        if loop:
            frame = int(round((phase.t % 1.0) * frames)) % frames
        else:
            frame = int(round(phase.t * max(0, frames - 1)))
        # Tiny clips can collapse adjacent phases. Preserve order while keeping
        # one semantic record per actual frame.
        if frame in used:
            continue
        used.add(frame)
        result.append({"frame": frame, "role": phase.role, "t": phase.t, "intent": phase.intent})
    return result


def apply_phase_template(doc: RigDocument, clip_name: str, template: str) -> list[dict[str, Any]]:
    """Publish semantic phase bookmarks without changing animation motion."""

    clip = _clip(doc, clip_name)
    frames = max(1, int(clip.get("frames", 1)))
    loop = bool(clip.get("loop", True))
    keys = phase_keys_for_frames(template, frames, loop=loop)
    clip["pose_keys"] = [entry["frame"] for entry in keys]
    clip["authoring_phase_keys"] = {
        "schema": "ambition.motion_phase_keys.v1",
        "template": template,
        "keys": keys,
        "note": "Authoring metadata only; pose_keys are consumed by the editor, semantic roles are not runtime data.",
    }
    return keys


def infer_phase_template(clip_name: str) -> str | None:
    name = clip_name.lower()
    if "smash" in name:
        return "smash_attack"
    if any(token in name for token in ("jab", "attack", "strike", "punch", "kick", "slash", "pummel")):
        return "melee_strike"
    if "run" in name:
        return "run"
    if "walk" in name:
        return "walk"
    if "dash" in name:
        return "dash"
    if "jump" in name or "hop" in name:
        return "jump"
    return None


def phase_roles(doc: RigDocument, clip_name: str) -> dict[int, str]:
    clip = _clip(doc, clip_name)
    authored = clip.get("authoring_phase_keys") or {}
    result = {
        int(entry["frame"]): str(entry["role"])
        for entry in authored.get("keys") or []
        if "frame" in entry and "role" in entry
    }
    if result:
        return result
    inferred = infer_phase_template(clip_name)
    if inferred is None:
        return {}
    frames = max(1, int(clip.get("frames", 1)))
    return {
        int(entry["frame"]): str(entry["role"])
        for entry in phase_keys_for_frames(inferred, frames, loop=bool(clip.get("loop", True)))
    }


def load_goal_file(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    text = path.read_text(encoding="utf8")
    data = json.loads(text) if path.suffix.lower() == ".json" else safe_load(text)
    if not isinstance(data, Mapping):
        raise PoseGoalError(f"goal file {path} must contain a mapping")
    return dict(data)


def write_goal_scaffold(
    doc: RigDocument,
    clip_name: str,
    frame_idx: int,
    path: str | Path,
) -> Path:
    """Write an editable semantic-goal YAML scaffold seeded from the rig."""

    t = _frame_t(doc, clip_name, frame_idx)
    world, params = doc.solve(clip_name, t)
    endpoint_records: dict[str, Any] = {}
    for semantic in ("near_hand", "far_hand", "near_foot", "far_foot"):
        try:
            kind, chain = _find_chain(doc, semantic)
        except PoseGoalError:
            continue
        end_name = chain.get("end") if kind == "chain" else chain.get("foot")
        if end_name and end_name in world:
            point = world[end_name].origin
            endpoint_records[semantic] = {
                "target": {"space": "frame", "value": [round(point[0], 2), round(point[1], 2)]},
                "bend": "preserve",
            }

    scaffold = {
        "schema": "ambition.semantic_pose_goals.v1",
        "target": doc.name,
        "clip": clip_name,
        "frame": int(frame_idx),
        "notes": [
            "Frame pixels are y-down and the authored side view faces +X.",
            "Use bend: up/down for elbows or forward/back for knees when branch choice matters.",
            "The tool writes ordinary rig channels and marks this frame as a pose key.",
        ],
        "goals": {
            "root": {
                "offset": [round(float(params.get("root_x", 0.0)), 2), round(float(params.get("root_y", 0.0)), 2)]
            },
            **endpoint_records,
            "head": {"look_at": {"space": "frame", "value": [doc.frame["width"] * 0.82, doc.frame["height"] * 0.42]}},
        },
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(safe_dump(scaffold, sort_keys=False, width=110), encoding="utf8")
    return path


__all__ = [
    "PHASE_TEMPLATES",
    "PhaseKey",
    "PoseGoalError",
    "apply_phase_template",
    "apply_pose_goals",
    "endpoint_channels",
    "infer_phase_template",
    "load_goal_file",
    "phase_keys_for_frames",
    "phase_roles",
    "solve_pose_goals",
    "upsert_channel_key",
    "write_goal_scaffold",
    "write_pose_keys",
]
