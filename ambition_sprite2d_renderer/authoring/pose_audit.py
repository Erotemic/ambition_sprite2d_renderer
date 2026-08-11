"""Geometry-only diagnostics for rig animation poses.

The audit intentionally stops below sprite rasterization.  It evaluates a
:class:`~ambition_sprite2d_renderer.authoring.rigdoc.RigDocument` through the
same FK/IK solver used by publishing, measures the resulting skeleton, and
writes diagnostics that remain useful on machines without ``resvg_py``.

The primary design goal is to catch poses that are *structurally* wrong before
an artist has to notice them in a 100-row sheet: elbow branch inversions,
neutral/recovery arms pointing away from their authored natural pose, nearly
straight IK chains, hand orientations that detach from the forearm, large
frame-to-frame pops, excessive target reach, and joints leaving the logical
frame.

SVG-rigged characters whose source pose is marked ``geometry-layout-only`` are
expected to provide ``natural_pose.arms`` metadata.  That makes the exploded
paper-doll layout irrelevant to the gameplay anatomy and gives this auditor a
stable reference independent of where the SVG pieces happen to be parked.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import importlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from PIL import Image, ImageDraw, ImageFont

from .rigdoc import RigDocument
from .skeleton import BoneWorld


Point = tuple[float, float]

# Current fighters use character-local motion modules.  The convention is kept
# here rather than in the runtime registry because pose auditing is an authoring
# concern and can still audit any rig that has no fighter profile at all.
_FIGHTER_MOTION_MODULES: Mapping[str, str] = {
    "patent_clerk": "ambition_sprite2d_renderer.targets.characters.patent_clerk_motion",
    "carl_stargan": "ambition_sprite2d_renderer.targets.characters.carl_stargan_motion",
    "noether": "ambition_sprite2d_renderer.targets.characters.noether_motion",
    "player_robot_v3": "ambition_sprite2d_renderer.targets.characters.player_robot_v3_motion",
    "perfect_cellular_automaton": "ambition_sprite2d_renderer.targets.characters.pca_motion",
}

# Categories where a limb pointing roughly like the authored natural stance is
# expected.  Attacks, rolls, throws, launches, etc. deliberately leave this
# cone and therefore do not receive the natural-direction check.
_NATURAL_ARM_CATEGORIES = frozenset(
    {
        "idle",
        "idle_look_up",
        "walk",
        "locomotion_stop",
        "turnaround",
        "run",
        "stumble",
        "crouch_start",
        "crouch",
        "crouch_walk",
        "crouch_end",
        "land_light",
        "land_hard",
        "jump_squat",
        "fall",
        "fall_special",
        "land_special",
        "shield_raise",
        "shield_hold",
        "shield_release",
        "shield_hit",
        "prone",
        "getup",
        "dizzy",
        "sleep",
        "wake",
        "buried",
        "teeter_start",
        "teeter",
        "trip_idle",
        "trip_getup",
        "loss",
    }
)

# A smaller subset where feet should remain effectively planted.  This is not
# applied to locomotion because ankle movement is the point there.
_PLANTED_CATEGORIES = frozenset(
    {
        "idle",
        "idle_look_up",
        "crouch",
        "shield_hold",
        "prone",
        "dizzy",
        "sleep",
        "buried",
        "teeter",
        "trip_idle",
        "loss",
    }
)

# Fallback for rigs without a fighter coverage profile.  These row names are
# intentionally conservative: only obvious neutral/recovery families get the
# strict natural-arm cone.
_STRICT_ROW_TOKENS = (
    "idle",
    "walk",
    "run",
    "stop",
    "turn",
    "crouch",
    "land",
    "fall",
    "shield",
    "block",
    "hold",
    "prone",
    "getup",
    "teeter",
    "sleep",
    "buried",
)


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    subject: str | None = None
    metrics: Mapping[str, float | int | str] = field(default_factory=dict)


@dataclass
class FrameAudit:
    animation: str
    frame: int
    time: float
    categories: tuple[str, ...]
    pose_class: str
    findings: list[Finding] = field(default_factory=list)
    arms: dict[str, dict[str, float | str]] = field(default_factory=dict)
    legs: dict[str, dict[str, float | str]] = field(default_factory=dict)
    world: dict[str, BoneWorld] = field(default_factory=dict, repr=False)

    @property
    def severity(self) -> str:
        if any(item.severity == "error" for item in self.findings):
            return "error"
        if any(item.severity == "warning" for item in self.findings):
            return "warning"
        return "ok"

    def json_record(self) -> dict[str, Any]:
        return {
            "animation": self.animation,
            "frame": self.frame,
            "time": round(self.time, 6),
            "categories": list(self.categories),
            "pose_class": self.pose_class,
            "severity": self.severity,
            "findings": [asdict(item) for item in self.findings],
            "arms": self.arms,
            "legs": self.legs,
        }


@dataclass
class AuditResult:
    target: str
    rig_path: Path
    document_findings: list[Finding]
    frames: list[FrameAudit]
    output_paths: dict[str, Path] = field(default_factory=dict)
    art_preview_status: str = "not_requested"

    @property
    def error_count(self) -> int:
        return sum(
            1
            for finding in self.document_findings
            if finding.severity == "error"
        ) + sum(
            1
            for frame in self.frames
            for finding in frame.findings
            if finding.severity == "error"
        )

    @property
    def warning_count(self) -> int:
        return sum(
            1
            for finding in self.document_findings
            if finding.severity == "warning"
        ) + sum(
            1
            for frame in self.frames
            for finding in frame.findings
            if finding.severity == "warning"
        )

    @property
    def info_count(self) -> int:
        return sum(
            1
            for finding in self.document_findings
            if finding.severity == "info"
        ) + sum(
            1
            for frame in self.frames
            for finding in frame.findings
            if finding.severity == "info"
        )

    @property
    def flagged_frame_count(self) -> int:
        return sum(1 for frame in self.frames if frame.severity != "ok")

    def summary(self) -> dict[str, Any]:
        by_code: dict[str, int] = {}
        for finding in self.document_findings:
            by_code[finding.code] = by_code.get(finding.code, 0) + 1
        for frame in self.frames:
            for finding in frame.findings:
                by_code[finding.code] = by_code.get(finding.code, 0) + 1
        return {
            "animations": len({frame.animation for frame in self.frames}),
            "frames": len(self.frames),
            "flagged_frames": self.flagged_frame_count,
            "errors": self.error_count,
            "warnings": self.warning_count,
            "info": self.info_count,
            "findings_by_code": dict(sorted(by_code.items())),
        }

    def json_record(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "target": self.target,
            "rig_path": str(self.rig_path),
            "summary": self.summary(),
            "document_findings": [asdict(item) for item in self.document_findings],
            "art_preview_status": self.art_preview_status,
            "outputs": {key: str(path) for key, path in self.output_paths.items()},
            "frames": [frame.json_record() for frame in self.frames],
        }


def _signed_angle_delta(a: float, b: float) -> float:
    """Signed shortest ``b-a`` in degrees."""
    return (float(b) - float(a) + 180.0) % 360.0 - 180.0


def _angle_between(a: Point, b: Point) -> float:
    na = math.hypot(a[0], a[1])
    nb = math.hypot(b[0], b[1])
    if na <= 1e-9 or nb <= 1e-9:
        return 0.0
    cosine = max(-1.0, min(1.0, (a[0] * b[0] + a[1] * b[1]) / (na * nb)))
    return math.degrees(math.acos(cosine))


def _cross(a: Point, b: Point) -> float:
    return a[0] * b[1] - a[1] * b[0]


def _sub(a: Point, b: Point) -> Point:
    return (a[0] - b[0], a[1] - b[1])


def _distance(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _round_metrics(values: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in values.items():
        if isinstance(value, float):
            out[key] = round(value, 3)
        else:
            out[key] = value
    return out


def _load_categories_by_row(target: str) -> dict[str, tuple[str, ...]]:
    dotted = _FIGHTER_MOTION_MODULES.get(target)
    if dotted is None:
        return {}
    try:
        module = importlib.import_module(dotted)
    except (ImportError, AttributeError):
        return {}
    coverage = getattr(module, "FIGHTER_MOTION_COVERAGE", None)
    if not isinstance(coverage, Mapping):
        return {}
    by_row: dict[str, list[str]] = {}
    for category, row in coverage.items():
        by_row.setdefault(str(row), []).append(str(category))
    return {
        row: tuple(sorted(categories))
        for row, categories in by_row.items()
    }


def _pose_class(animation: str, categories: Sequence[str]) -> str:
    if any(category in _NATURAL_ARM_CATEGORIES for category in categories):
        return "natural"
    if not categories and any(token in animation for token in _STRICT_ROW_TOKENS):
        return "natural"
    if any(
        token in animation
        for token in (
            "attack",
            "smash",
            "special",
            "throw",
            "roll",
            "dodge",
            "tumble",
            "launch",
            "meteor",
            "tech",
            "jump",
        )
    ):
        return "expressive"
    return "neutral"


def _natural_arm_vectors(doc: RigDocument) -> dict[str, Point]:
    natural = doc.data.get("natural_pose")
    if not isinstance(natural, Mapping):
        return {}
    arms = natural.get("arms")
    if not isinstance(arms, Mapping):
        return {}
    result: dict[str, Point] = {}
    for side, value in arms.items():
        if not isinstance(value, Mapping):
            continue
        hand = value.get("hand")
        elbow = value.get("elbow")
        if (
            isinstance(hand, Sequence)
            and isinstance(elbow, Sequence)
            and len(hand) >= 2
            and len(elbow) >= 2
        ):
            result[str(side)] = (
                float(hand[0]) - float(elbow[0]),
                float(hand[1]) - float(elbow[1]),
            )
    return result


def _chain_side(chain: Mapping[str, Any]) -> str:
    prefix = str(chain.get("channel_prefix", ""))
    if prefix.startswith("near_"):
        return "near"
    if prefix.startswith("far_"):
        return "far"
    return prefix.removesuffix("_hand") or str(chain.get("upper", "chain"))


def _chain_points(
    world: Mapping[str, BoneWorld], chain: Mapping[str, Any]
) -> tuple[Point, Point, Point] | None:
    upper = world.get(str(chain.get("upper", "")))
    lower = world.get(str(chain.get("lower", "")))
    if upper is None or lower is None:
        return None
    end_name = chain.get("end") or chain.get("foot")
    end = world.get(str(end_name)) if end_name else None
    wrist = end.origin if end is not None else lower.tip
    return upper.origin, lower.origin, wrist


def _requested_arm_target(
    doc: RigDocument, chain: Mapping[str, Any], params: Mapping[str, float]
) -> Point:
    fr = doc.frame
    cx = float(fr.get("center_x", fr["width"] / 2.0))
    gy = float(fr.get("ground_y", fr["height"] - 2.0))
    prefix = str(chain.get("channel_prefix", "target"))
    x = params.get(f"{prefix}_x", float(chain.get("rest_x", 0.0)))
    y = params.get(f"{prefix}_y", float(chain.get("rest_y", 0.0)))
    return (cx + float(x), gy + float(y))


def _sampled_bend(chain: Mapping[str, Any], params: Mapping[str, float]) -> float:
    prefix = str(chain.get("channel_prefix", "target"))
    return float(params.get(f"{prefix}_bend", float(chain.get("bend", 1.0))))


def _reference_hand_offsets(doc: RigDocument) -> dict[str, float]:
    if "idle" not in doc.clips:
        return {}
    world, _params = doc.solve("idle", doc.frame_time("idle", 0, int(doc.clips["idle"].get("frames", 1))))
    result: dict[str, float] = {}
    for chain in doc.ik_chains:
        lower = world.get(str(chain.get("lower", "")))
        end = world.get(str(chain.get("end", "")))
        if lower is None or end is None:
            continue
        result[_chain_side(chain)] = _signed_angle_delta(lower.angle, end.angle)
    return result


def _document_findings(doc: RigDocument) -> list[Finding]:
    findings: list[Finding] = []
    features = doc.data.get("features")
    source_pose_role = features.get("source_pose_role") if isinstance(features, Mapping) else None
    if source_pose_role == "geometry-layout-only" and doc.ik_chains and not _natural_arm_vectors(doc):
        findings.append(
            Finding(
                severity="error",
                code="missing_natural_arm_pose",
                message=(
                    "canonical SVG rig declares its source pose as geometry-layout-only "
                    "but provides no natural_pose.arms authority"
                ),
            )
        )
    return findings


def _audit_chain(
    *,
    doc: RigDocument,
    frame: FrameAudit,
    chain: Mapping[str, Any],
    params: Mapping[str, float],
    natural_vectors: Mapping[str, Point],
    reference_hand_offsets: Mapping[str, float],
) -> None:
    points = _chain_points(frame.world, chain)
    if points is None:
        return
    shoulder, elbow, wrist = points
    side = _chain_side(chain)
    upper_name = str(chain.get("upper", ""))
    lower_name = str(chain.get("lower", ""))
    end_name = str(chain.get("end", ""))
    upper = frame.world.get(upper_name)
    lower = frame.world.get(lower_name)
    end = frame.world.get(end_name) if end_name else None
    if upper is None or lower is None:
        return

    root_to_target = _sub(wrist, shoulder)
    root_to_joint = _sub(elbow, shoulder)
    lower_vector = _sub(wrist, elbow)
    branch_cross = _cross(root_to_target, root_to_joint)
    sampled_bend = _sampled_bend(chain, params)
    # two_bone_ik defines positive bend on the clockwise side of the
    # root→target ray; in the cross-product convention below that is negative.
    expected_sign = -1.0 if sampled_bend >= 0.0 else 1.0
    actual_sign = 0.0 if abs(branch_cross) <= 1e-5 else (1.0 if branch_cross > 0 else -1.0)

    joint_angle = _angle_between(_sub(shoulder, elbow), _sub(wrist, elbow))
    requested = _requested_arm_target(doc, chain, params)
    requested_reach = _distance(shoulder, requested)
    chain_reach = max(1e-6, float(upper.length + lower.length))
    reach_ratio = requested_reach / chain_reach

    natural_angle = None
    natural_vector = natural_vectors.get(side)
    if natural_vector is not None:
        # Natural arm authority is authored in the neutral torso frame.  Compare
        # against that direction after carrying it with the current torso
        # rotation; otherwise a perfectly sensible arm on a prone/rolling body
        # looks 90-180 degrees "wrong" simply because the whole character
        # rotated in world space.
        torso = frame.world.get("torso")
        if torso is not None:
            angle = math.radians(float(torso.angle))
            c = math.cos(angle)
            s = math.sin(angle)
            expected_natural = (
                c * natural_vector[0] - s * natural_vector[1],
                s * natural_vector[0] + c * natural_vector[1],
            )
        else:
            expected_natural = natural_vector
        natural_angle = _angle_between(lower_vector, expected_natural)

    hand_offset = None
    hand_offset_delta = None
    if end is not None:
        hand_offset = _signed_angle_delta(lower.angle, end.angle)
        reference = reference_hand_offsets.get(side)
        if reference is not None:
            hand_offset_delta = abs(_signed_angle_delta(reference, hand_offset))

    metrics = {
        "joint_angle_deg": joint_angle,
        "branch_cross": branch_cross,
        "bend": sampled_bend,
        "reach_ratio": reach_ratio,
        "lower_angle_deg": lower.angle,
    }
    if natural_angle is not None:
        metrics["natural_direction_delta_deg"] = natural_angle
    if hand_offset is not None:
        metrics["hand_forearm_offset_deg"] = hand_offset
    if hand_offset_delta is not None:
        metrics["hand_offset_delta_from_idle_deg"] = hand_offset_delta
    frame.arms[side] = _round_metrics(metrics)

    if actual_sign and actual_sign != expected_sign:
        frame.findings.append(
            Finding(
                "error",
                "elbow_branch_inversion",
                f"{side} elbow is on the opposite side from the sampled IK bend",
                side,
                _round_metrics({"cross": branch_cross, "bend": sampled_bend}),
            )
        )

    expressive = frame.pose_class == "expressive"
    straight_warning = 179.4 if expressive else 170.0
    straight_error = 179.85 if expressive else 178.0
    if joint_angle >= straight_error:
        frame.findings.append(
            Finding(
                "error",
                "arm_hyperextension",
                f"{side} elbow is effectively ruler-straight",
                side,
                _round_metrics({"joint_angle_deg": joint_angle}),
            )
        )
    elif joint_angle >= straight_warning:
        frame.findings.append(
            Finding(
                "warning",
                "arm_near_hyperextension",
                f"{side} elbow has very little visible bend",
                side,
                _round_metrics({"joint_angle_deg": joint_angle}),
            )
        )

    if frame.pose_class == "natural" and natural_angle is not None:
        if natural_angle >= 120.0:
            frame.findings.append(
                Finding(
                    "error",
                    "arm_points_away_from_natural",
                    f"{side} forearm points opposite the authored natural arm direction",
                    side,
                    _round_metrics({"direction_delta_deg": natural_angle}),
                )
            )
        elif natural_angle >= 75.0:
            frame.findings.append(
                Finding(
                    "warning",
                    "arm_outside_natural_cone",
                    f"{side} forearm is far outside the authored natural arm cone",
                    side,
                    _round_metrics({"direction_delta_deg": natural_angle}),
                )
            )

    if hand_offset_delta is not None:
        warning_threshold = 120.0 if expressive else 70.0
        error_threshold = 165.0 if expressive else 115.0
        if hand_offset_delta >= error_threshold:
            frame.findings.append(
                Finding(
                    "error",
                    "hand_orientation_detached",
                    f"{side} hand orientation has swung far away from its idle forearm relationship",
                    side,
                    _round_metrics({"offset_delta_deg": hand_offset_delta}),
                )
            )
        elif hand_offset_delta >= warning_threshold:
            frame.findings.append(
                Finding(
                    "warning",
                    "hand_orientation_suspicious",
                    f"{side} hand orientation differs strongly from its idle forearm relationship",
                    side,
                    _round_metrics({"offset_delta_deg": hand_offset_delta}),
                )
            )

    max_reach_ratio = chain.get("max_reach_ratio")
    if max_reach_ratio is not None:
        # A soft reach clamp is explicitly protecting the anatomical bend.  A
        # distant authoring target is therefore a quality warning, not itself
        # a broken solved pose; only report meaningful overshoot so ordinary
        # locomotion swing does not flood the audit.
        if reach_ratio > (1.30 if expressive else 1.15):
            frame.findings.append(
                Finding(
                    "info",
                    "arm_target_clamped",
                    f"{side} hand trajectory substantially exceeds the soft IK reach",
                    side,
                    _round_metrics(
                        {
                            "reach_ratio": reach_ratio,
                            "max_reach_ratio": float(max_reach_ratio),
                        }
                    ),
                )
            )
    else:
        reach_error = 1.20 if expressive else 1.05
        reach_warning = 1.10 if expressive else 0.985
        if reach_ratio > reach_error:
            frame.findings.append(
                Finding(
                    "error",
                    "arm_target_beyond_reach",
                    f"{side} hand target lies far beyond the physical two-bone chain",
                    side,
                    _round_metrics({"reach_ratio": reach_ratio}),
                )
            )
        elif reach_ratio > reach_warning:
            frame.findings.append(
                Finding(
                    "warning",
                    "arm_target_near_max_reach",
                    f"{side} hand target is close enough to max reach to erase the elbow bend",
                    side,
                    _round_metrics({"reach_ratio": reach_ratio}),
                )
            )


def _audit_leg(
    *,
    doc: RigDocument,
    frame: FrameAudit,
    chain: Mapping[str, Any],
    params: Mapping[str, float],
) -> None:
    points = _chain_points(frame.world, chain)
    if points is None:
        return
    hip, knee, ankle = points
    side = _chain_side(chain).replace("foot", "").strip("_") or str(chain.get("upper", "leg"))
    root_to_target = _sub(ankle, hip)
    root_to_joint = _sub(knee, hip)
    branch_cross = _cross(root_to_target, root_to_joint)
    prefix = str(chain.get("channel_prefix", "foot"))
    bend = float(params.get(f"{prefix}_bend", float(chain.get("bend", 1.0))))
    expected_sign = -1.0 if bend >= 0 else 1.0
    actual_sign = 0.0 if abs(branch_cross) <= 1e-5 else (1.0 if branch_cross > 0 else -1.0)
    knee_angle = _angle_between(_sub(hip, knee), _sub(ankle, knee))
    frame.legs[side] = _round_metrics(
        {
            "joint_angle_deg": knee_angle,
            "branch_cross": branch_cross,
            "bend": bend,
        }
    )
    if actual_sign and actual_sign != expected_sign:
        frame.findings.append(
            Finding(
                "error",
                "knee_branch_inversion",
                f"{side} knee is on the opposite side from the sampled IK bend",
                side,
                _round_metrics({"cross": branch_cross, "bend": bend}),
            )
        )


def _audit_bounds(doc: RigDocument, frame: FrameAudit) -> None:
    width = float(doc.frame["width"])
    height = float(doc.frame["height"])
    margin = 2.0
    outside: list[str] = []
    for name, bone in frame.world.items():
        for point in (bone.origin, bone.tip):
            if (
                point[0] < -margin
                or point[1] < -margin
                or point[0] > width + margin
                or point[1] > height + margin
            ):
                outside.append(name)
                break
    if outside:
        frame.findings.append(
            Finding(
                "warning",
                "skeleton_outside_logical_frame",
                "one or more bones leave the logical rig frame; verify render overscan",
                metrics={"bones": ",".join(sorted(set(outside)))},
            )
        )


def _audit_discontinuities(doc: RigDocument, frames: list[FrameAudit]) -> None:
    by_animation: dict[str, list[FrameAudit]] = {}
    for frame in frames:
        by_animation.setdefault(frame.animation, []).append(frame)
    scale = max(1.0, float(doc.frame.get("height", 128.0)))

    for animation, row in by_animation.items():
        row.sort(key=lambda item: item.frame)
        clip = doc.clips.get(animation) or {}
        pairs = list(zip(row, row[1:]))
        if bool(clip.get("loop", True)) and len(row) > 2:
            pairs.append((row[-1], row[0]))
        for previous, current in pairs:
            expressive = current.pose_class == "expressive"
            wrist_warn = scale * (0.42 if expressive else 0.24)
            wrist_error = scale * (0.68 if expressive else 0.38)
            angle_warn = 125.0 if expressive else 80.0
            angle_error = 170.0 if expressive else 135.0
            for chain in doc.ik_chains:
                side = _chain_side(chain)
                a = _chain_points(previous.world, chain)
                b = _chain_points(current.world, chain)
                if a is None or b is None:
                    continue
                displacement = _distance(a[2], b[2])
                lower_a = previous.world.get(str(chain.get("lower", "")))
                lower_b = current.world.get(str(chain.get("lower", "")))
                angle_delta = (
                    abs(_signed_angle_delta(lower_a.angle, lower_b.angle))
                    if lower_a is not None and lower_b is not None
                    else 0.0
                )
                if displacement >= wrist_error or angle_delta >= angle_error:
                    current.findings.append(
                        Finding(
                            "error",
                            "arm_frame_pop",
                            f"{side} arm changes discontinuously from the previous sampled frame",
                            side,
                            _round_metrics(
                                {
                                    "wrist_displacement_px": displacement,
                                    "lower_angle_delta_deg": angle_delta,
                                    "previous_frame": previous.frame,
                                }
                            ),
                        )
                    )
                elif displacement >= wrist_warn or angle_delta >= angle_warn:
                    current.findings.append(
                        Finding(
                            "warning",
                            "arm_frame_jump",
                            f"{side} arm changes sharply from the previous sampled frame",
                            side,
                            _round_metrics(
                                {
                                    "wrist_displacement_px": displacement,
                                    "lower_angle_delta_deg": angle_delta,
                                    "previous_frame": previous.frame,
                                }
                            ),
                        )
                    )

            if any(category in _PLANTED_CATEGORIES for category in current.categories):
                for chain in doc.ik_legs:
                    side = _chain_side(chain)
                    a = _chain_points(previous.world, chain)
                    b = _chain_points(current.world, chain)
                    if a is None or b is None:
                        continue
                    slip = _distance(a[2], b[2])
                    if slip > 4.0:
                        current.findings.append(
                            Finding(
                                "warning",
                                "planted_foot_slip",
                                f"{side} planted foot moves between adjacent frames",
                                side,
                                _round_metrics(
                                    {
                                        "ankle_displacement_px": slip,
                                        "previous_frame": previous.frame,
                                    }
                                ),
                            )
                        )


def audit_document(doc: RigDocument, *, target: str | None = None) -> AuditResult:
    target_name = str(target or doc.name)
    categories_by_row = _load_categories_by_row(target_name)
    natural_vectors = _natural_arm_vectors(doc)
    hand_references = _reference_hand_offsets(doc)
    frames: list[FrameAudit] = []

    for animation, clip in doc.clips.items():
        nframes = max(1, int(clip.get("frames", 1)))
        categories = categories_by_row.get(str(animation), ())
        pose_class = _pose_class(str(animation), categories)
        for frame_idx in range(nframes):
            t = doc.frame_time(str(animation), frame_idx, nframes)
            world, params = doc.solve(str(animation), t)
            frame = FrameAudit(
                animation=str(animation),
                frame=frame_idx,
                time=t,
                categories=tuple(categories),
                pose_class=pose_class,
                world=dict(world),
            )
            for chain in doc.ik_chains:
                _audit_chain(
                    doc=doc,
                    frame=frame,
                    chain=chain,
                    params=params,
                    natural_vectors=natural_vectors,
                    reference_hand_offsets=hand_references,
                )
            for chain in doc.ik_legs:
                _audit_leg(doc=doc, frame=frame, chain=chain, params=params)
            _audit_bounds(doc, frame)
            frames.append(frame)

    _audit_discontinuities(doc, frames)
    rig_path = doc.source_path or Path(f"{doc.name}.rig.json")
    return AuditResult(
        target=target_name,
        rig_path=Path(rig_path),
        document_findings=_document_findings(doc),
        frames=frames,
    )


def find_rig_document(target: str, *, explicit: Path | None = None) -> Path:
    if explicit is not None:
        path = Path(explicit).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(path)
        return path

    # Canonical SVG fighters have a stronger lifecycle than loose rig JSON:
    # freshness-check (and rebuild when necessary) before auditing so an old
    # compatibility document cannot silently win by filename. The import is
    # local to keep the generic geometry auditor independent of that builder.
    try:
        from .canonical_scientist_rig import ensure_scientist_rig, svg_path

        svg_path(target)  # raises KeyError when this is not a canonical fighter
    except KeyError:
        pass
    else:
        return ensure_scientist_rig(target).resolve()

    package_root = Path(__file__).resolve().parents[1]
    rig_root = package_root / "targets" / "characters" / "rigged"
    # A target-specific rig directory is the canonical/published authoring
    # location and intentionally outranks an older loose compatibility rig of
    # the same document name. This lets characters migrate to generated SVG
    # rigs without forcing an overlay archive to delete the legacy file.
    preferred = [
        rig_root / target / f"{target}.rig.json",
        rig_root / target / f"{target}_side.rig.json",
    ]
    for path in preferred:
        if path.exists():
            return path.resolve()

    candidates = [rig_root / f"{target}.rig.json"]
    existing = [path.resolve() for path in candidates if path.exists()]
    if len(existing) == 1:
        return existing[0]

    matches: list[Path] = []
    for path in rig_root.rglob("*.rig.json"):
        try:
            data = json.loads(path.read_text(encoding="utf8"))
        except (OSError, json.JSONDecodeError):
            continue
        if str(data.get("name", "")) == target:
            matches.append(path.resolve())
    unique = sorted(set(existing + matches))
    if len(unique) == 1:
        return unique[0]
    if not unique:
        raise FileNotFoundError(
            f"no rig document found for target {target!r} under {rig_root}"
        )
    raise ValueError(
        f"multiple rig documents match {target!r}: "
        + ", ".join(str(path) for path in unique)
    )


def _severity_color(severity: str) -> tuple[int, int, int, int]:
    if severity == "error":
        return (235, 84, 84, 255)
    if severity == "warning":
        return (238, 186, 79, 255)
    return (84, 205, 130, 255)


def _draw_skeleton_cell(
    doc: RigDocument,
    frame: FrameAudit,
    *,
    size: tuple[int, int],
    label: bool = True,
) -> Image.Image:
    width, height = size
    image = Image.new("RGBA", size, (31, 27, 34, 255))
    draw = ImageDraw.Draw(image)
    fw = float(doc.frame["width"])
    fh = float(doc.frame["height"])
    pad = 5.0
    scale = min((width - 2 * pad) / max(1.0, fw), (height - 2 * pad) / max(1.0, fh))
    ox = (width - fw * scale) / 2.0
    oy = (height - fh * scale) / 2.0

    def map_point(point: Point) -> tuple[int, int]:
        return (
            int(round(ox + point[0] * scale)),
            int(round(oy + point[1] * scale)),
        )

    # Logical frame boundary.
    draw.rectangle(
        (int(ox), int(oy), int(ox + fw * scale), int(oy + fh * scale)),
        outline=(79, 70, 84, 255),
        width=1,
    )
    for name, bone in frame.world.items():
        color = (205, 210, 220, 255)
        line_width = 1
        if "arm" in name:
            color = (115, 194, 241, 255)
            line_width = 2
        elif "leg" in name or "foot" in name:
            color = (209, 179, 105, 255)
            line_width = 2
        start = map_point(bone.origin)
        end = map_point(bone.tip)
        draw.line((start, end), fill=color, width=line_width)
        r = 2 if line_width > 1 else 1
        draw.ellipse((start[0]-r, start[1]-r, start[0]+r, start[1]+r), fill=color)

    if label:
        severity = frame.severity
        draw.rectangle((0, 0, width - 1, height - 1), outline=_severity_color(severity), width=2 if severity != "ok" else 1)
        draw.text((3, 2), str(frame.frame), fill=(244, 244, 244, 255), font=ImageFont.load_default())
    return image


def write_skeleton_contact_sheet(
    doc: RigDocument,
    result: AuditResult,
    out_path: Path,
    *,
    flagged_only: bool = False,
) -> Path:
    grouped: dict[str, list[FrameAudit]] = {}
    for frame in result.frames:
        if flagged_only and frame.severity == "ok":
            continue
        grouped.setdefault(frame.animation, []).append(frame)
    if not grouped:
        image = Image.new("RGBA", (640, 80), (31, 27, 34, 255))
        draw = ImageDraw.Draw(image)
        draw.text((12, 28), "No flagged frames", fill=(220, 220, 220, 255), font=ImageFont.load_default())
        out_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(out_path)
        return out_path

    cell_w, cell_h = 88, 88
    label_w = 180
    row_h = 96
    max_frames = max(len(frames) for frames in grouped.values())
    width = label_w + max_frames * cell_w
    height = len(grouped) * row_h
    sheet = Image.new("RGBA", (width, height), (24, 21, 27, 255))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for row_index, (animation, frames) in enumerate(grouped.items()):
        y = row_index * row_h
        worst = "ok"
        if any(frame.severity == "error" for frame in frames):
            worst = "error"
        elif any(frame.severity == "warning" for frame in frames):
            worst = "warning"
        draw.rectangle((0, y, label_w - 1, y + row_h - 1), fill=(34, 30, 39, 255))
        draw.text((6, y + 7), animation, fill=(240, 240, 240, 255), font=font)
        counts: dict[str, int] = {}
        for frame in frames:
            for finding in frame.findings:
                counts[finding.code] = counts.get(finding.code, 0) + 1
        summary = ", ".join(f"{key}:{value}" for key, value in list(counts.items())[:3])
        if summary:
            draw.text((6, y + 23), summary[:28], fill=_severity_color(worst), font=font)
        categories = sorted({category for frame in frames for category in frame.categories})
        if categories:
            draw.text((6, y + 39), "/".join(categories)[:28], fill=(150, 150, 160, 255), font=font)
        for column, frame in enumerate(frames):
            cell = _draw_skeleton_cell(doc, frame, size=(cell_w, cell_h))
            sheet.alpha_composite(cell, (label_w + column * cell_w, y + 4))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, compress_level=1)
    return out_path


def write_flagged_detail_sheet(
    doc: RigDocument,
    result: AuditResult,
    out_path: Path,
    *,
    max_frames: int = 160,
) -> Path:
    """Large annotated tiles for the most suspicious individual frames."""
    flagged = [frame for frame in result.frames if frame.severity != "ok"]
    priority = {"error": 0, "warning": 1, "ok": 2}
    flagged.sort(
        key=lambda frame: (
            priority[frame.severity],
            -len(frame.findings),
            frame.animation,
            frame.frame,
        )
    )
    flagged = flagged[:max_frames]
    if not flagged:
        image = Image.new("RGBA", (640, 80), (31, 27, 34, 255))
        ImageDraw.Draw(image).text(
            (12, 28), "No flagged frames", fill=(220, 220, 220, 255), font=ImageFont.load_default()
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(out_path)
        return out_path

    tile_w, tile_h = 260, 220
    columns = 4
    rows = math.ceil(len(flagged) / columns)
    sheet = Image.new("RGBA", (columns * tile_w, rows * tile_h), (24, 21, 27, 255))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for index, frame in enumerate(flagged):
        x = (index % columns) * tile_w
        y = (index // columns) * tile_h
        cell = _draw_skeleton_cell(doc, frame, size=(150, 150), label=False)
        sheet.alpha_composite(cell, (x + 4, y + 24))
        draw.rectangle(
            (x, y, x + tile_w - 1, y + tile_h - 1),
            outline=_severity_color(frame.severity),
            width=2,
        )
        draw.text(
            (x + 5, y + 5),
            f"{frame.animation}:{frame.frame} [{frame.severity}]",
            fill=_severity_color(frame.severity),
            font=font,
        )
        for line_index, finding in enumerate(frame.findings[:5]):
            label = f"{finding.code}: {finding.subject or ''}".rstrip()
            draw.text(
                (x + 160, y + 28 + line_index * 24),
                label[:34],
                fill=(230, 230, 230, 255),
                font=font,
            )
            metric_text = ", ".join(
                f"{key}={value}" for key, value in list(finding.metrics.items())[:2]
            )
            if metric_text:
                draw.text(
                    (x + 160, y + 39 + line_index * 24),
                    metric_text[:32],
                    fill=(155, 155, 165, 255),
                    font=font,
                )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, compress_level=1)
    return out_path


def _overlay_skeleton_on_art(
    doc: RigDocument, frame: FrameAudit, art: Image.Image
) -> Image.Image:
    overlay = Image.new("RGBA", art.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    sx = art.width / float(doc.frame["width"])
    sy = art.height / float(doc.frame["height"])

    def p(point: Point) -> tuple[int, int]:
        return (int(round(point[0] * sx)), int(round(point[1] * sy)))

    for name, bone in frame.world.items():
        color = (70, 225, 255, 220) if "arm" in name else (255, 208, 84, 190) if ("leg" in name or "foot" in name) else (244, 244, 244, 160)
        a, b = p(bone.origin), p(bone.tip)
        draw.line((a, b), fill=color, width=max(1, int(round(2 * sx))))
        r = max(2, int(round(2.2 * sx)))
        draw.ellipse((a[0]-r, a[1]-r, a[0]+r, a[1]+r), fill=color)
    out = art.convert("RGBA")
    out.alpha_composite(overlay)
    return out


def write_flagged_art_sheet(
    doc: RigDocument,
    result: AuditResult,
    out_path: Path,
    *,
    max_frames: int = 120,
) -> Path | None:
    flagged = [frame for frame in result.frames if frame.severity != "ok"]
    priority = {"error": 0, "warning": 1, "ok": 2}
    flagged.sort(
        key=lambda frame: (
            priority[frame.severity],
            -len(frame.findings),
            frame.animation,
            frame.frame,
        )
    )
    flagged = flagged[:max_frames]
    if not flagged:
        return None
    # Importing the renderer package is the exact capability check we need.  If
    # unavailable, keep the geometry-only audit successful.
    try:
        importlib.import_module("resvg_py")
    except ImportError:
        return None

    cell_w, cell_h = 220, 220
    columns = 5
    rows = math.ceil(len(flagged) / columns)
    sheet = Image.new("RGBA", (columns * cell_w, rows * cell_h), (25, 22, 28, 255))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for index, frame in enumerate(flagged):
        art = doc.render_frame(
            frame.animation,
            frame.frame,
            int(doc.clips[frame.animation].get("frames", 1)),
        )
        art = _overlay_skeleton_on_art(doc, frame, art)
        art.thumbnail((cell_w - 8, cell_h - 28), Image.Resampling.LANCZOS)
        x = (index % columns) * cell_w
        y = (index // columns) * cell_h
        sheet.alpha_composite(art, (x + 4, y + 22))
        codes = ",".join(f.code for f in frame.findings[:2])
        draw.text((x + 4, y + 4), f"{frame.animation}:{frame.frame} {codes}"[:34], fill=_severity_color(frame.severity), font=font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, compress_level=1)
    return out_path


def run_pose_audit(
    *,
    target: str,
    rig_path: Path,
    out_dir: Path,
    with_art: bool = True,
) -> AuditResult:
    doc = RigDocument.load(rig_path)
    result = audit_document(doc, target=target)
    out_dir.mkdir(parents=True, exist_ok=True)

    full_sheet = write_skeleton_contact_sheet(
        doc, result, out_dir / "pose_skeletons.png"
    )
    flagged_sheet = write_skeleton_contact_sheet(
        doc, result, out_dir / "pose_flagged_skeletons.png", flagged_only=True
    )
    detail_sheet = write_flagged_detail_sheet(
        doc, result, out_dir / "pose_flagged_detail.png"
    )
    result.output_paths["skeletons"] = full_sheet
    result.output_paths["flagged_skeletons"] = flagged_sheet
    result.output_paths["flagged_detail"] = detail_sheet

    if with_art:
        art_path = write_flagged_art_sheet(
            doc, result, out_dir / "pose_flagged_art.png"
        )
        if art_path is not None:
            result.output_paths["flagged_art"] = art_path
            result.art_preview_status = "written"
        else:
            result.art_preview_status = "skipped_resvg_unavailable_or_no_flags"
    else:
        result.art_preview_status = "disabled"

    report_path = out_dir / "pose_audit.json"
    result.output_paths["report"] = report_path
    report_path.write_text(json.dumps(result.json_record(), indent=2) + "\n", encoding="utf8")
    return result


__all__ = [
    "AuditResult",
    "Finding",
    "FrameAudit",
    "audit_document",
    "find_rig_document",
    "run_pose_audit",
    "write_flagged_art_sheet",
    "write_flagged_detail_sheet",
    "write_skeleton_contact_sheet",
]
