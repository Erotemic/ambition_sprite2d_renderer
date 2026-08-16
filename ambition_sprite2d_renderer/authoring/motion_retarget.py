"""Retarget authored motion between humanoid rig documents.

The transfer operates on semantic anatomy rather than copying raw bone angles.
For each source frame it samples the pelvis/root plus available hand and foot
endpoints, expresses those endpoint offsets in source body-scale units, and
reconstructs equivalent targets on the destination rig through its own IK
chains.  Torso/head local angles are carried as secondary pose cues when the
bones exist on both rigs.

This is intentionally a starting-point generator, not a promise of automatic
character animation.  The destination should still be reviewed and adjusted to
its personality, costume silhouette, proportions, and combat intent.
"""

from __future__ import annotations

from typing import Any, Mapping

from .motion_authoring import (
    apply_phase_template,
    infer_phase_template,
    write_pose_keys,
)
from .rigdoc import RigDocument


class MotionRetargetError(ValueError):
    pass


def _body_scale(doc: RigDocument) -> float:
    sk = doc.build_skeleton()
    totals = []
    for side in ("near", "far"):
        upper = sk.bones.get(f"{side}_leg_u")
        lower = sk.bones.get(f"{side}_leg_l")
        if upper is not None and lower is not None:
            totals.append(float(upper.length + lower.length))
    if totals:
        return sum(totals) / len(totals)
    return float(doc.frame["height"]) * 0.36


def _endpoint_bindings(doc: RigDocument) -> dict[str, tuple[str, dict]]:
    result: dict[str, tuple[str, dict]] = {}
    for chain in doc.ik_chains:
        prefix = str(chain.get("channel_prefix") or "")
        if prefix in {"near_hand", "far_hand"}:
            result[prefix] = ("chain", chain)
    for leg in doc.ik_legs:
        prefix = str(leg.get("channel_prefix") or "")
        if prefix in {"near_foot", "far_foot"}:
            result[prefix] = ("leg", leg)
    return result


def _endpoint_position(world: Mapping[str, Any], kind: str, binding: Mapping[str, Any]) -> tuple[float, float] | None:
    name = binding.get("end") if kind == "chain" else binding.get("foot")
    if not name or name not in world:
        return None
    return tuple(world[str(name)].origin)


def _source_bend(params: Mapping[str, float], binding: Mapping[str, Any]) -> float:
    prefix = str(binding.get("channel_prefix") or "")
    return float(params.get(f"{prefix}_bend", binding.get("bend", 1.0)))


def retarget_clip(
    source: RigDocument,
    source_clip: str,
    target: RigDocument,
    *,
    target_clip: str | None = None,
    scale: float | None = None,
    copy_phase_template: bool = True,
) -> dict[str, Any]:
    """Retarget one source clip into ``target`` and return transfer metadata."""

    if source_clip not in source.clips:
        raise MotionRetargetError(f"source rig has no clip {source_clip!r}")
    target_clip = target_clip or source_clip
    src_clip = source.clips[source_clip]
    frames = max(1, int(src_clip.get("frames", 1)))
    duration_ms = int(src_clip.get("duration_ms", 100))
    loop = bool(src_clip.get("loop", True))
    src_scale = _body_scale(source)
    dst_scale = _body_scale(target)
    transfer_scale = float(scale) if scale is not None else dst_scale / max(src_scale, 1e-6)

    target.data.setdefault("clips", {})[target_clip] = {
        "loop": loop,
        "frames": frames,
        "duration_ms": duration_ms,
        "channels": {},
        "authoring_retarget": {
            "schema": "ambition.motion_retarget.v1",
            "source_rig": source.name,
            "source_clip": source_clip,
            "source_body_scale_px": round(src_scale, 3),
            "target_body_scale_px": round(dst_scale, 3),
            "endpoint_scale": round(transfer_scale, 5),
            "note": "Starting-point transfer by normalized anatomical endpoints; review and personalize before publication.",
        },
    }

    source_bindings = _endpoint_bindings(source)
    target_bindings = _endpoint_bindings(target)
    common = sorted(set(source_bindings) & set(target_bindings))
    src_frame = source.frame
    dst_frame = target.frame
    src_cx = float(src_frame.get("center_x", src_frame["width"] / 2))
    src_gy = float(src_frame.get("ground_y", src_frame["height"] - 2))
    dst_cx = float(dst_frame.get("center_x", dst_frame["width"] / 2))
    dst_gy = float(dst_frame.get("ground_y", dst_frame["height"] - 2))

    for frame_idx in range(frames):
        t = source.frame_time(source_clip, frame_idx, frames)
        src_world, src_params = source.solve(source_clip, t)
        src_root = (
            src_cx + float(src_params.get("root_x", 0.0)),
            src_gy + float(src_params.get("root_y", 0.0)),
        )
        target_values: dict[str, float] = {
            "root_x": float(src_params.get("root_x", 0.0)) * transfer_scale,
            "root_y": float(src_params.get("root_y", 0.0)) * transfer_scale,
        }
        dst_root = (dst_cx + target_values["root_x"], dst_gy + target_values["root_y"])

        # Local torso/head pose is a useful secondary cue, but endpoints remain
        # authoritative so proportion differences do not distort reach.
        for bone_name in ("pelvis", "torso", "head"):
            if source.bone(bone_name) is not None and target.bone(bone_name) is not None and bone_name in src_params:
                target_values[bone_name] = float(src_params[bone_name])

        for semantic in common:
            src_kind, src_binding = source_bindings[semantic]
            dst_kind, dst_binding = target_bindings[semantic]
            src_point = _endpoint_position(src_world, src_kind, src_binding)
            if src_point is None:
                continue
            local = ((src_point[0] - src_root[0]) * transfer_scale, (src_point[1] - src_root[1]) * transfer_scale)
            target_point = (dst_root[0] + local[0], dst_root[1] + local[1])
            prefix = str(dst_binding.get("channel_prefix"))
            target_values[f"{prefix}_bend"] = _source_bend(src_params, src_binding)
            if dst_kind == "leg":
                ankle_h = float(dst_frame.get("ankle_h", 0.0))
                target_values[f"{prefix}_x"] = target_point[0] - dst_cx
                target_values[f"{prefix}_lift"] = dst_gy - ankle_h - target_point[1]
                src_prefix = str(src_binding.get("channel_prefix"))
                if f"{src_prefix}_pitch" in src_params:
                    target_values[f"{prefix}_pitch"] = float(src_params[f"{src_prefix}_pitch"])
            else:
                target_values[f"{prefix}_x"] = target_point[0] - dst_cx
                target_values[f"{prefix}_y"] = target_point[1] - dst_gy
                src_prefix = str(src_binding.get("channel_prefix"))
                if f"{src_prefix}_pitch" in src_params:
                    target_values[f"{prefix}_pitch"] = float(src_params[f"{src_prefix}_pitch"])

        write_pose_keys(target, target_clip, frame_idx, target_values, ease="smooth", mark_pose_key=False)

    if copy_phase_template:
        source_phase = (src_clip.get("authoring_phase_keys") or {}).get("template")
        template = source_phase or infer_phase_template(source_clip)
        if template is not None:
            apply_phase_template(target, target_clip, template)

    return {
        "source": source.name,
        "source_clip": source_clip,
        "target": target.name,
        "target_clip": target_clip,
        "frames": frames,
        "duration_ms_per_frame": duration_ms,
        "loop": loop,
        "endpoint_scale": round(transfer_scale, 5),
        "transferred_endpoints": common,
    }


__all__ = ["MotionRetargetError", "retarget_clip"]
