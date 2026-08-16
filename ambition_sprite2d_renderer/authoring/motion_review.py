"""Motion-quality diagnostics and visual review sheets for rig animations.

Unlike :mod:`pose_audit`, which asks whether individual poses are structurally
valid, this module evaluates *motion through time*: planted-foot slide, pelvis
travel, support/center-of-mass relationships, joint extension, endpoint speed,
loop seams, and whether a strike's speed peak aligns with its authored contact
phase.

The metrics are descriptive authoring feedback.  They intentionally avoid
turning animation principles into hard gameplay/runtime rules.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import math
from pathlib import Path
from statistics import fmean
from typing import Any, Mapping, Sequence

from PIL import Image, ImageDraw, ImageFont

from .motion_authoring import phase_roles
from .motion_rig_resolver import find_existing_rig_document
from .rigdoc import RigDocument
from .skeleton import BoneWorld

Point = tuple[float, float]


@dataclass(frozen=True)
class MotionFinding:
    severity: str
    code: str
    message: str
    frame: int | None = None
    subject: str | None = None
    metrics: Mapping[str, float | int | str] = field(default_factory=dict)


@dataclass
class MotionFrame:
    frame: int
    t: float
    world: dict[str, BoneWorld] = field(repr=False)
    params: dict[str, float] = field(repr=False)
    endpoints: dict[str, Point] = field(default_factory=dict)
    com: Point = (0.0, 0.0)
    support: tuple[float, float] | None = None
    contacts: tuple[str, ...] = ()
    phase: str | None = None


@dataclass
class MotionReview:
    target: str
    clip: str
    rig_path: Path
    frames: list[MotionFrame]
    metrics: dict[str, Any]
    findings: list[MotionFinding]
    output_paths: dict[str, Path] = field(default_factory=dict)

    def json_record(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "clip": self.clip,
            "rig_path": str(self.rig_path),
            "metrics": self.metrics,
            "findings": [asdict(item) for item in self.findings],
            "frames": [
                {
                    "frame": frame.frame,
                    "t": round(frame.t, 6),
                    "endpoints": {name: [round(p[0], 3), round(p[1], 3)] for name, p in frame.endpoints.items()},
                    "com": [round(frame.com[0], 3), round(frame.com[1], 3)],
                    "support": list(frame.support) if frame.support else None,
                    "contacts": list(frame.contacts),
                    "phase": frame.phase,
                }
                for frame in self.frames
            ],
        }


_ENDPOINT_NAMES = {
    "pelvis": ("pelvis", "origin"),
    "head": ("head", "origin"),
    "near_hand": ("near_arm_hand", "origin"),
    "far_hand": ("far_arm_hand", "origin"),
    "near_foot": ("near_leg_foot", "origin"),
    "far_foot": ("far_leg_foot", "origin"),
}

# Coarse visual mass weights are sufficient for an authoring diagnostic.  They
# are normalized at use-time over whichever named bones the rig actually has.
_MASS_WEIGHTS = {
    "pelvis": 0.16,
    "torso": 0.38,
    "head": 0.09,
    "near_arm_u": 0.035,
    "near_arm_l": 0.025,
    "far_arm_u": 0.035,
    "far_arm_l": 0.025,
    "near_leg_u": 0.075,
    "near_leg_l": 0.055,
    "far_leg_u": 0.075,
    "far_leg_l": 0.055,
}


def _distance(a: Point, b: Point) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _endpoint(world: Mapping[str, BoneWorld], name: str) -> Point | None:
    record = _ENDPOINT_NAMES.get(name)
    if record is None:
        return None
    bone_name, _kind = record
    bone = world.get(bone_name)
    return bone.origin if bone is not None else None


def _bone_midpoint(bone: BoneWorld) -> Point:
    radians = math.radians(bone.angle)
    return (
        bone.origin[0] + math.cos(radians) * bone.length * 0.5,
        bone.origin[1] + math.sin(radians) * bone.length * 0.5,
    )


def _center_of_mass(world: Mapping[str, BoneWorld]) -> Point:
    points: list[tuple[Point, float]] = []
    for name, weight in _MASS_WEIGHTS.items():
        bone = world.get(name)
        if bone is None:
            continue
        points.append((_bone_midpoint(bone), weight))
    if not points:
        origins = [bone.origin for bone in world.values()]
        return (fmean(p[0] for p in origins), fmean(p[1] for p in origins)) if origins else (0.0, 0.0)
    total = sum(weight for _point, weight in points)
    return (
        sum(point[0] * weight for point, weight in points) / total,
        sum(point[1] * weight for point, weight in points) / total,
    )


def _contact_feet(doc: RigDocument, endpoints: Mapping[str, Point], threshold: float = 2.5) -> tuple[str, ...]:
    gy = float(doc.frame.get("ground_y", doc.frame["height"] - 2))
    ankle_h = float(doc.frame.get("ankle_h", 0.0))
    ground_ankle = gy - ankle_h
    return tuple(
        name
        for name in ("near_foot", "far_foot")
        if name in endpoints and abs(endpoints[name][1] - ground_ankle) <= threshold
    )


def _support(endpoints: Mapping[str, Point], contacts: Sequence[str]) -> tuple[float, float] | None:
    xs = [endpoints[name][0] for name in contacts if name in endpoints]
    if not xs:
        return None
    if len(xs) == 1:
        return xs[0] - 3.0, xs[0] + 3.0
    return min(xs), max(xs)


def _frame_samples(doc: RigDocument, clip_name: str) -> list[MotionFrame]:
    clip = doc.clips[clip_name]
    frames = max(1, int(clip.get("frames", 1)))
    roles = phase_roles(doc, clip_name)
    result: list[MotionFrame] = []
    for idx in range(frames):
        t = doc.frame_time(clip_name, idx, frames)
        world, params = doc.solve(clip_name, t)
        endpoints = {
            name: point
            for name in _ENDPOINT_NAMES
            if (point := _endpoint(world, name)) is not None
        }
        contacts = _contact_feet(doc, endpoints)
        result.append(
            MotionFrame(
                frame=idx,
                t=t,
                world=world,
                params=params,
                endpoints=endpoints,
                com=_center_of_mass(world),
                support=_support(endpoints, contacts),
                contacts=contacts,
                phase=roles.get(idx),
            )
        )
    return result


def _speed_series(frames: Sequence[MotionFrame], endpoint: str, duration_ms: int, loop: bool) -> list[float]:
    if not frames:
        return []
    n = len(frames)
    frame_seconds = max(1e-6, (duration_ms / 1000.0) / n)
    speeds = [0.0] * n
    for i in range(1, n):
        if endpoint in frames[i - 1].endpoints and endpoint in frames[i].endpoints:
            speeds[i] = _distance(frames[i - 1].endpoints[endpoint], frames[i].endpoints[endpoint]) / frame_seconds
    if loop and n > 1 and endpoint in frames[-1].endpoints and endpoint in frames[0].endpoints:
        speeds[0] = _distance(frames[-1].endpoints[endpoint], frames[0].endpoints[endpoint]) / frame_seconds
    return speeds


def _pearson(a: Sequence[float], b: Sequence[float]) -> float | None:
    if len(a) != len(b) or len(a) < 3:
        return None
    ma, mb = fmean(a), fmean(b)
    da = [x - ma for x in a]
    db = [x - mb for x in b]
    denom = math.sqrt(sum(x * x for x in da) * sum(x * x for x in db))
    if denom <= 1e-8:
        return None
    return sum(x * y for x, y in zip(da, db)) / denom


def _joint_angle(a: Point, b: Point, c: Point) -> float:
    v0 = (a[0] - b[0], a[1] - b[1])
    v1 = (c[0] - b[0], c[1] - b[1])
    n0 = math.hypot(*v0)
    n1 = math.hypot(*v1)
    if n0 <= 1e-8 or n1 <= 1e-8:
        return 0.0
    cosv = max(-1.0, min(1.0, (v0[0] * v1[0] + v0[1] * v1[1]) / (n0 * n1)))
    return math.degrees(math.acos(cosv))


def _chain_extension(frame: MotionFrame, upper: str, lower: str, end: str) -> float | None:
    if upper not in frame.world or lower not in frame.world or end not in frame.world:
        return None
    return _joint_angle(frame.world[upper].origin, frame.world[lower].origin, frame.world[end].origin)


def _contact_segments(frames: Sequence[MotionFrame], foot: str, loop: bool) -> list[list[int]]:
    active = [foot in frame.contacts for frame in frames]
    segments: list[list[int]] = []
    current: list[int] = []
    for idx, is_active in enumerate(active):
        if is_active:
            current.append(idx)
        elif current:
            segments.append(current)
            current = []
    if current:
        segments.append(current)
    if loop and len(segments) >= 2 and active and active[0] and active[-1]:
        merged = segments[-1] + segments[0]
        segments = [merged] + segments[1:-1]
    return segments


def _unwrapped_segment(segment: Sequence[int], frame_count: int) -> list[int]:
    if not segment:
        return []
    out = [int(segment[0])]
    offset = 0
    previous = int(segment[0])
    for raw in segment[1:]:
        current = int(raw)
        if current < previous:
            offset += frame_count
        out.append(current + offset)
        previous = current
    return out


def _segment_travel_estimate(
    frames: Sequence[MotionFrame],
    foot: str,
    segment: Sequence[int],
    *,
    loop: bool,
) -> float | None:
    if len(segment) < 2:
        return None
    unwrapped = _unwrapped_segment(segment, len(frames))
    denominator = len(frames) if loop else max(1, len(frames) - 1)
    fraction = (unwrapped[-1] - unwrapped[0]) / denominator
    if fraction <= 1e-6:
        return None
    dx = frames[segment[-1]].endpoints[foot][0] - frames[segment[0]].endpoints[foot][0]
    # A body moving +X while a planted foot stays fixed in world space makes
    # the local foot move -X.  Runtime/camera travel therefore has the opposite
    # sign to local contact drift.
    return -dx / fraction


def _foot_travel_estimates(
    frames: Sequence[MotionFrame], foot: str, loop: bool
) -> list[float]:
    estimates = []
    for segment in _contact_segments(frames, foot, loop):
        estimate = _segment_travel_estimate(frames, foot, segment, loop=loop)
        if estimate is not None:
            estimates.append(estimate)
    return estimates


def _foot_slide_metrics(
    frames: Sequence[MotionFrame],
    foot: str,
    loop: bool,
    *,
    travel_px_per_cycle: float | None,
) -> dict[str, Any]:
    segments = _contact_segments(frames, foot, loop)
    records = []
    for segment in segments:
        if len(segment) <= 1:
            continue
        unwrapped = _unwrapped_segment(segment, len(frames))
        denominator = len(frames) if loop else max(1, len(frames) - 1)
        local_x = [frames[idx].endpoints[foot][0] for idx in segment]
        local_mean = fmean(local_x)
        local_rms = math.sqrt(fmean((x - local_mean) ** 2 for x in local_x))
        local_span = max(local_x) - min(local_x)
        compensated = list(local_x)
        if travel_px_per_cycle is not None:
            compensated = [
                x + travel_px_per_cycle * ((u - unwrapped[0]) / denominator)
                for x, u in zip(local_x, unwrapped)
            ]
        comp_mean = fmean(compensated)
        comp_rms = math.sqrt(fmean((x - comp_mean) ** 2 for x in compensated))
        records.append(
            {
                "frames": list(segment),
                "local_rms_px": local_rms,
                "local_span_px": local_span,
                "compensated_rms_px": comp_rms,
                "compensated_span_px": max(compensated) - min(compensated),
            }
        )
    return {
        "segments": [
            {
                "frames": item["frames"],
                "local_rms_px": round(item["local_rms_px"], 3),
                "local_span_px": round(item["local_span_px"], 3),
                "compensated_rms_px": round(item["compensated_rms_px"], 3),
                "compensated_span_px": round(item["compensated_span_px"], 3),
            }
            for item in records
        ],
        "worst_local_rms_px": round(max((item["local_rms_px"] for item in records), default=0.0), 3),
        "worst_local_span_px": round(max((item["local_span_px"] for item in records), default=0.0), 3),
        "worst_compensated_rms_px": round(max((item["compensated_rms_px"] for item in records), default=0.0), 3),
        "worst_compensated_span_px": round(max((item["compensated_span_px"] for item in records), default=0.0), 3),
    }


def review_document(
    doc: RigDocument,
    clip_name: str,
    *,
    target: str | None = None,
    focus: str | None = None,
    travel_px_per_cycle: float | None = None,
) -> MotionReview:
    if clip_name not in doc.clips:
        raise ValueError(f"unknown clip {clip_name!r}; available: {', '.join(doc.clips)}")
    clip = doc.clips[clip_name]
    frame_count = max(1, int(clip.get("frames", 1)))
    duration_ms = int(clip.get("duration_ms", 100)) * frame_count
    loop = bool(clip.get("loop", True))
    frames = _frame_samples(doc, clip_name)
    metrics: dict[str, Any] = {
        "frame_count": frame_count,
        "total_duration_ms": duration_ms,
        "loop": loop,
        "phase_roles": {str(frame.frame): frame.phase for frame in frames if frame.phase},
    }
    findings: list[MotionFinding] = []

    pelvis = [frame.endpoints.get("pelvis") for frame in frames if "pelvis" in frame.endpoints]
    if pelvis:
        metrics["pelvis"] = {
            "horizontal_excursion_px": round(max(p[0] for p in pelvis) - min(p[0] for p in pelvis), 3),
            "vertical_excursion_px": round(max(p[1] for p in pelvis) - min(p[1] for p in pelvis), 3),
        }

    travel_estimates: dict[str, list[float]] = {}
    for foot in ("near_foot", "far_foot"):
        if all(foot in frame.endpoints for frame in frames):
            travel_estimates[foot] = _foot_travel_estimates(frames, foot, loop)
    flattened_estimates = [value for values in travel_estimates.values() for value in values]
    resolved_travel = travel_px_per_cycle
    travel_source = "explicit" if travel_px_per_cycle is not None else "unavailable"
    if resolved_travel is None and flattened_estimates:
        resolved_travel = fmean(flattened_estimates)
        travel_source = "estimated_from_ground_contact"
    metrics["locomotion_travel"] = {
        "px_per_cycle": round(resolved_travel, 3) if resolved_travel is not None else None,
        "source": travel_source,
        "per_foot_estimates": {foot: [round(value, 3) for value in values] for foot, values in travel_estimates.items()},
    }
    representative = [fmean(values) for values in travel_estimates.values() if values]
    if len(representative) >= 2 and max(representative) - min(representative) > max(6.0, abs(fmean(representative)) * 0.25):
        findings.append(
            MotionFinding(
                "warning",
                "gait_travel_mismatch",
                "Near/far support phases imply materially different body travel; the two planted feet will not both read stationary at one locomotion speed.",
                metrics={"near_px_per_cycle": round(representative[0], 3), "far_px_per_cycle": round(representative[1], 3)},
            )
        )

    for foot in ("near_foot", "far_foot"):
        if all(foot in frame.endpoints for frame in frames):
            slide = _foot_slide_metrics(frames, foot, loop, travel_px_per_cycle=resolved_travel)
            metrics[f"{foot}_slide"] = slide
            if slide["worst_compensated_rms_px"] > 2.0:
                findings.append(
                    MotionFinding(
                        "warning",
                        "foot_slide",
                        f"{foot} retains {slide['worst_compensated_rms_px']:.2f}px RMS slide after compensating for {travel_source.replace('_', ' ')} body travel.",
                        subject=foot,
                        metrics={
                            "compensated_rms_px": slide["worst_compensated_rms_px"],
                            "local_rms_px": slide["worst_local_rms_px"],
                            "travel_px_per_cycle": round(resolved_travel, 3) if resolved_travel is not None else "none",
                        },
                    )
                )

    support_out = []
    for frame in frames:
        if frame.support is None:
            continue
        lo, hi = frame.support
        if frame.com[0] < lo - 4.0 or frame.com[0] > hi + 4.0:
            support_out.append(frame.frame)
    metrics["support"] = {
        "frames_with_support": sum(frame.support is not None for frame in frames),
        "com_outside_support_frames": support_out,
    }
    if support_out:
        findings.append(
            MotionFinding(
                "info",
                "com_outside_support",
                f"COM projects outside inferred support on {len(support_out)} frame(s); this reads as committed/off-balance motion.",
                metrics={"frames": ",".join(map(str, support_out))},
            )
        )

    # Joint lock diagnostics are especially useful for procedural IK walks.
    joint_specs = {
        "near_elbow": ("near_arm_u", "near_arm_l", "near_arm_hand"),
        "far_elbow": ("far_arm_u", "far_arm_l", "far_arm_hand"),
        "near_knee": ("near_leg_u", "near_leg_l", "near_leg_foot"),
        "far_knee": ("far_leg_u", "far_leg_l", "far_leg_foot"),
    }
    extension_metrics: dict[str, Any] = {}
    for label, spec in joint_specs.items():
        values = [_chain_extension(frame, *spec) for frame in frames]
        valid = [(idx, value) for idx, value in enumerate(values) if value is not None]
        if not valid:
            continue
        max_idx, max_value = max(valid, key=lambda item: item[1])
        extension_metrics[label] = {"max_deg": round(max_value, 2), "frame": max_idx}
        if max_value > 174.0:
            findings.append(
                MotionFinding(
                    "info",
                    "joint_near_lock",
                    f"{label} reaches {max_value:.1f}°; near-lock can read mechanical unless intentional.",
                    frame=max_idx,
                    subject=label,
                    metrics={"degrees": round(max_value, 2)},
                )
            )
    metrics["joint_extension"] = extension_metrics

    # Opposition: hand should generally counter the opposite foot in locomotion.
    opposition = {}
    for hand, foot in (("near_hand", "far_foot"), ("far_hand", "near_foot")):
        if all(hand in frame.endpoints and foot in frame.endpoints and "pelvis" in frame.endpoints for frame in frames):
            hand_x = [frame.endpoints[hand][0] - frame.endpoints["pelvis"][0] for frame in frames]
            foot_x = [frame.endpoints[foot][0] - frame.endpoints["pelvis"][0] for frame in frames]
            corr = _pearson(hand_x, foot_x)
            if corr is not None:
                opposition[f"{hand}_vs_{foot}"] = round(corr, 3)
    metrics["limb_opposition_correlation"] = opposition

    speed_metrics = {}
    endpoints_to_measure = [name for name in ("near_hand", "far_hand", "near_foot", "far_foot", "pelvis", "head") if all(name in frame.endpoints for frame in frames)]
    for name in endpoints_to_measure:
        speeds = _speed_series(frames, name, duration_ms, loop)
        if not speeds:
            continue
        peak_frame = max(range(len(speeds)), key=lambda idx: speeds[idx])
        speed_metrics[name] = {
            "peak_px_per_s": round(speeds[peak_frame], 2),
            "peak_frame": peak_frame,
            "series_px_per_s": [round(value, 2) for value in speeds],
        }
    metrics["endpoint_speed"] = speed_metrics

    focus_name = focus
    if focus_name is None and speed_metrics:
        # Hands win ties for attack readability; otherwise choose the endpoint
        # with the largest peak speed.
        priority = {"near_hand": 2, "far_hand": 2, "near_foot": 1, "far_foot": 1, "pelvis": 0, "head": 0}
        focus_name = max(speed_metrics, key=lambda name: (speed_metrics[name]["peak_px_per_s"], priority.get(name, 0)))
    if focus_name in speed_metrics:
        metrics["focus"] = focus_name
        contact_frames = [frame.frame for frame in frames if frame.phase in {"contact", "impact", "active"}]
        peak_frame = int(speed_metrics[focus_name]["peak_frame"])
        if contact_frames:
            nearest = min(contact_frames, key=lambda frame: abs(frame - peak_frame))
            offset = peak_frame - nearest
            metrics["focus_contact_speed_alignment"] = {
                "contact_frame": nearest,
                "peak_speed_frame": peak_frame,
                "offset_frames": offset,
            }
            if abs(offset) > 1:
                findings.append(
                    MotionFinding(
                        "warning",
                        "speed_peak_misses_contact",
                        f"{focus_name} speed peaks {abs(offset)} frame(s) {'after' if offset > 0 else 'before'} contact.",
                        frame=peak_frame,
                        subject=focus_name,
                        metrics={"offset_frames": offset, "contact_frame": nearest},
                    )
                )

    if loop and frame_count > 1:
        seam = {}
        for name in endpoints_to_measure:
            seam[name] = round(_distance(frames[-1].endpoints[name], frames[0].endpoints[name]), 3)
        seam["max_endpoint_px"] = max(seam.values(), default=0.0)
        metrics["loop_seam"] = seam
        if seam["max_endpoint_px"] > 5.0:
            findings.append(
                MotionFinding(
                    "warning",
                    "loop_seam_pop",
                    f"Loop endpoint seam reaches {seam['max_endpoint_px']:.2f}px.",
                    metrics={"max_endpoint_px": seam["max_endpoint_px"]},
                )
            )

    rig_path = Path(doc.source_path) if doc.source_path else Path("<memory>")
    return MotionReview(target=target or doc.name, clip=clip_name, rig_path=rig_path, frames=frames, metrics=metrics, findings=findings)


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()


def _draw_skeleton(draw: ImageDraw.ImageDraw, frame: MotionFrame, offset: Point, scale: float) -> None:
    world = frame.world
    for name, bone in world.items():
        end = bone.tip
        x0, y0 = offset[0] + bone.origin[0] * scale, offset[1] + bone.origin[1] * scale
        x1, y1 = offset[0] + end[0] * scale, offset[1] + end[1] * scale
        draw.line((x0, y0, x1, y1), fill=(196, 199, 205, 255), width=max(1, round(2 * scale)))
        if name in {"pelvis", "head", "near_arm_hand", "far_arm_hand", "near_leg_foot", "far_leg_foot"}:
            r = max(2, round(2.2 * scale))
            draw.ellipse((x0 - r, y0 - r, x0 + r, y0 + r), fill=(245, 209, 103, 255))
    com_x = offset[0] + frame.com[0] * scale
    com_y = offset[1] + frame.com[1] * scale
    r = max(2, round(3 * scale))
    draw.ellipse((com_x - r, com_y - r, com_x + r, com_y + r), fill=(114, 220, 231, 255))
    if frame.support:
        y = offset[1] + max((p[1] for name, p in frame.endpoints.items() if name.endswith("foot")), default=0.0) * scale + 5
        draw.line((offset[0] + frame.support[0] * scale, y, offset[0] + frame.support[1] * scale, y), fill=(125, 213, 139, 255), width=3)


def write_motion_review_image(doc: RigDocument, review: MotionReview, path: str | Path) -> Path:
    """Write skeleton/contact/trajectory review plus a focus-speed graph."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    n = len(review.frames)
    frame_w = int(doc.frame["width"])
    frame_h = int(doc.frame["height"])
    scale = min(1.0, 110 / max(frame_w, frame_h))
    cell_w = max(124, round(frame_w * scale) + 14)
    cell_h = max(142, round(frame_h * scale) + 34)
    cols = min(8, max(1, n))
    rows = math.ceil(n / cols)
    top = 58
    graph_h = 170
    width = max(760, cols * cell_w)
    height = top + rows * cell_h + graph_h + 28
    image = Image.new("RGBA", (width, height), (30, 29, 36, 255))
    draw = ImageDraw.Draw(image, "RGBA")
    title_font = _font(20, True)
    label_font = _font(12, True)
    small_font = _font(10)
    draw.text((14, 12), f"{review.target} / {review.clip} — motion review", fill=(245, 243, 238, 255), font=title_font)
    draw.text((14, 36), f"{n} frames · {review.metrics['total_duration_ms']} ms · {len(review.findings)} finding(s)", fill=(177, 173, 188, 255), font=small_font)

    trajectories: dict[str, list[Point]] = {name: [] for name in ("near_hand", "far_hand", "near_foot", "far_foot", "pelvis")}
    for frame in review.frames:
        col = frame.frame % cols
        row = frame.frame // cols
        x0, y0 = col * cell_w, top + row * cell_h
        draw.rectangle((x0 + 2, y0 + 2, x0 + cell_w - 3, y0 + cell_h - 3), fill=(38, 36, 45, 255), outline=(67, 64, 76, 255))
        offset = (x0 + 7, y0 + 23)
        _draw_skeleton(draw, frame, offset, scale)
        label = f"f{frame.frame}"
        if frame.phase:
            label += f" {frame.phase}"
        draw.text((x0 + 7, y0 + 6), label, fill=(238, 234, 226, 255), font=small_font)
        if frame.contacts:
            draw.text((x0 + 7, y0 + cell_h - 15), "contact " + ",".join(name.replace("_foot", "") for name in frame.contacts), fill=(127, 220, 144, 255), font=small_font)
        for name in trajectories:
            point = frame.endpoints.get(name)
            if point is not None:
                trajectories[name].append((offset[0] + point[0] * scale, offset[1] + point[1] * scale))

    graph_top = top + rows * cell_h + 24
    draw.text((14, graph_top), "Endpoint speed", fill=(245, 243, 238, 255), font=label_font)
    graph_box = (54, graph_top + 24, width - 24, graph_top + graph_h - 14)
    draw.rectangle(graph_box, fill=(34, 33, 41, 255), outline=(72, 69, 82, 255))
    focus = review.metrics.get("focus")
    speed = ((review.metrics.get("endpoint_speed") or {}).get(focus) or {}).get("series_px_per_s", [])
    if speed:
        max_speed = max(max(speed), 1.0)
        x0, y0, x1, y1 = graph_box
        pts = []
        for idx, value in enumerate(speed):
            x = x0 + (x1 - x0) * (idx / max(1, len(speed) - 1))
            y = y1 - (y1 - y0) * (float(value) / max_speed)
            pts.append((x, y))
        if len(pts) >= 2:
            draw.line(pts, fill=(244, 199, 87, 255), width=3)
        for frame in review.frames:
            if frame.phase:
                x = x0 + (x1 - x0) * (frame.frame / max(1, len(speed) - 1))
                draw.line((x, y0, x, y1), fill=(106, 100, 122, 150), width=1)
                draw.text((x + 2, y1 - 14 - (frame.frame % 2) * 12), frame.phase, fill=(168, 162, 183, 255), font=small_font)
        draw.text((x0 + 5, y0 + 5), f"focus: {focus} · peak {max_speed:.1f}px/s", fill=(228, 225, 218, 255), font=small_font)
    else:
        draw.text((graph_box[0] + 8, graph_box[1] + 8), "No common endpoint speed series available.", fill=(168, 162, 183, 255), font=small_font)

    image.convert("RGB").save(path, quality=94)
    return path



def write_motion_paths_image(doc: RigDocument, review: MotionReview, path: str | Path) -> Path:
    """Plot endpoint trajectories in one rig-frame coordinate system."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    width = int(doc.frame["width"])
    height = int(doc.frame["height"])
    scale = min(4.0, max(2.0, 420 / max(width, height)))
    margin = 44
    image = Image.new("RGBA", (round(width * scale) + margin * 2, round(height * scale) + margin * 2 + 40), (30, 29, 36, 255))
    draw = ImageDraw.Draw(image, "RGBA")
    title_font = _font(18, True)
    small_font = _font(10)
    draw.text((12, 10), f"{review.target} / {review.clip} — endpoint paths", fill=(245, 243, 238, 255), font=title_font)
    ox, oy = margin, margin + 28
    draw.rectangle((ox, oy, ox + width * scale, oy + height * scale), outline=(74, 70, 84, 255), fill=(35, 34, 42, 255))
    gy = float(doc.frame.get("ground_y", height - 2))
    draw.line((ox, oy + gy * scale, ox + width * scale, oy + gy * scale), fill=(94, 91, 105, 255), width=1)
    colors = {
        "near_hand": (244, 194, 84, 255),
        "far_hand": (226, 141, 102, 255),
        "near_foot": (111, 220, 137, 255),
        "far_foot": (83, 185, 129, 255),
        "pelvis": (107, 203, 232, 255),
        "head": (188, 148, 230, 255),
    }
    for name, color in colors.items():
        points = [frame.endpoints[name] for frame in review.frames if name in frame.endpoints]
        if not points:
            continue
        screen = [(ox + point[0] * scale, oy + point[1] * scale) for point in points]
        if len(screen) >= 2:
            draw.line(screen, fill=color, width=3)
        for frame, point in zip([frame for frame in review.frames if name in frame.endpoints], screen):
            r = 3
            draw.ellipse((point[0] - r, point[1] - r, point[0] + r, point[1] + r), fill=color)
            if frame.phase in {"contact", "contact_near", "contact_far", "anticipation", "follow_through", "apex"}:
                draw.text((point[0] + 4, point[1] - 5), str(frame.frame), fill=color, font=small_font)
    legend_x = 12
    legend_y = image.height - 24
    for name, color in colors.items():
        draw.rectangle((legend_x, legend_y, legend_x + 9, legend_y + 9), fill=color)
        draw.text((legend_x + 13, legend_y - 2), name, fill=(208, 204, 214, 255), font=small_font)
        legend_x += 86
    image.convert("RGB").save(path, quality=94)
    return path


def write_motion_silhouette_image(doc: RigDocument, review: MotionReview, path: str | Path) -> tuple[Path | None, dict[str, Any]]:
    """Render flat-black silhouettes and return per-frame alpha metrics.

    This product is optional because SVG-rig rasterization may be unavailable
    on minimal machines.  Geometry review remains fully functional without it.
    """

    rendered: list[Image.Image] = []
    metrics: dict[str, Any] = {"frames": []}
    clip = doc.clips[review.clip]
    frame_count = max(1, int(clip.get("frames", 1)))
    try:
        for frame in review.frames:
            image = doc.render_at(review.clip, frame.t, supersample=1)
            alpha = image.getchannel("A")
            bbox = alpha.getbbox()
            if bbox is None:
                metrics["frames"].append({"frame": frame.frame, "bbox": None, "width_px": 0, "height_px": 0, "alpha_area_px": 0})
            else:
                histogram = alpha.histogram()
                area = sum(histogram[1:])
                metrics["frames"].append(
                    {
                        "frame": frame.frame,
                        "bbox": list(bbox),
                        "width_px": bbox[2] - bbox[0],
                        "height_px": bbox[3] - bbox[1],
                        "alpha_area_px": area,
                    }
                )
            silhouette = Image.new("RGBA", image.size, (0, 0, 0, 0))
            silhouette.paste((8, 8, 10, 255), (0, 0, image.width, image.height), alpha)
            rendered.append(silhouette)
    except Exception as exc:  # Optional art dependency; geometry path must survive.
        metrics["status"] = "unavailable"
        metrics["reason"] = f"{type(exc).__name__}: {exc}"
        return None, metrics

    widths = [item["width_px"] for item in metrics["frames"] if item["width_px"]]
    metrics["status"] = "written"
    metrics["width_range_px"] = [min(widths), max(widths)] if widths else [0, 0]
    metrics["width_excursion_px"] = max(widths) - min(widths) if widths else 0
    phase_map = {frame.frame: frame.phase for frame in review.frames}
    metrics["phase_width_px"] = {
        phase_map[item["frame"]]: item["width_px"]
        for item in metrics["frames"]
        if phase_map.get(item["frame"])
    }

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    scale = 2
    cell_w = int(doc.frame["width"]) * scale + 12
    cell_h = int(doc.frame["height"]) * scale + 28
    cols = min(8, max(1, frame_count))
    rows = math.ceil(frame_count / cols)
    image = Image.new("RGBA", (cols * cell_w, rows * cell_h), (238, 236, 229, 255))
    draw = ImageDraw.Draw(image, "RGBA")
    small = _font(10)
    for idx, silhouette in enumerate(rendered):
        x0 = (idx % cols) * cell_w
        y0 = (idx // cols) * cell_h
        enlarged = silhouette.resize((silhouette.width * scale, silhouette.height * scale), Image.Resampling.NEAREST)
        image.alpha_composite(enlarged, (x0 + 6, y0 + 20))
        label = f"f{idx}"
        if phase_map.get(idx):
            label += f" {phase_map[idx]}"
        draw.text((x0 + 5, y0 + 4), label, fill=(53, 49, 56, 255), font=small)
        record = metrics["frames"][idx]
        draw.text((x0 + 5, y0 + cell_h - 14), f"w{record['width_px']} a{record['alpha_area_px']}", fill=(104, 97, 108, 255), font=small)
    image.convert("RGB").save(path, quality=94)
    return path, metrics

def _markdown(review: MotionReview) -> str:
    lines = [
        f"# Motion review: {review.target} / {review.clip}",
        "",
        f"- Frames: {review.metrics['frame_count']}",
        f"- Duration: {review.metrics['total_duration_ms']} ms",
        f"- Loop: {review.metrics['loop']}",
    ]
    pelvis = review.metrics.get("pelvis") or {}
    if pelvis:
        lines += [
            f"- Pelvis vertical excursion: {pelvis.get('vertical_excursion_px', 0)} px",
            f"- Pelvis horizontal excursion: {pelvis.get('horizontal_excursion_px', 0)} px",
        ]
    travel = review.metrics.get("locomotion_travel") or {}
    if travel.get("px_per_cycle") is not None:
        lines.append(f"- Inferred/declared travel: {travel['px_per_cycle']} px/cycle ({travel.get('source')})")
    for foot in ("near_foot", "far_foot"):
        slide = review.metrics.get(f"{foot}_slide") or {}
        if slide:
            lines.append(f"- {foot} contact drift: {slide.get('worst_local_rms_px', 0)} px RMS local; {slide.get('worst_compensated_rms_px', 0)} px RMS travel-compensated")
    seam = review.metrics.get("loop_seam")
    if seam:
        lines.append(f"- Loop endpoint seam: {seam.get('max_endpoint_px', 0)} px max")
    alignment = review.metrics.get("focus_contact_speed_alignment")
    if alignment:
        lines.append(
            f"- Focus speed/contact offset: {alignment['offset_frames']} frame(s) "
            f"({review.metrics.get('focus')})"
        )
    lines += ["", "## Findings", ""]
    if not review.findings:
        lines.append("No motion-level findings.")
    else:
        for finding in review.findings:
            where = f" frame {finding.frame}" if finding.frame is not None else ""
            lines.append(f"- **{finding.severity.upper()}** `{finding.code}`{where}: {finding.message}")
    lines += [
        "",
        "## Interpretation",
        "",
        "These are descriptive authoring diagnostics, not gameplay validation rules. A committed attack may intentionally place COM outside support, while a stylized walk may intentionally exaggerate pelvis motion. Use the report to identify what the motion reads as, then decide whether that reading matches the character and move.",
        "",
    ]
    return "\n".join(lines)


def run_motion_review(
    *,
    target: str,
    clip_name: str,
    out_dir: str | Path,
    rig_path: str | Path | None = None,
    focus: str | None = None,
    travel_px_per_cycle: float | None = None,
    with_art: bool = False,
) -> MotionReview:
    resolved = find_existing_rig_document(target, explicit=Path(rig_path) if rig_path else None)
    doc = RigDocument.load(resolved)
    review = review_document(doc, clip_name, target=target, focus=focus, travel_px_per_cycle=travel_px_per_cycle)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "motion_review.json"
    md_path = out_dir / "motion_review.md"
    image_path = out_dir / "motion_review.png"
    paths_path = out_dir / "motion_paths.png"
    json_path.write_text(json.dumps(review.json_record(), indent=2) + "\n", encoding="utf8")
    md_path.write_text(_markdown(review), encoding="utf8")
    write_motion_review_image(doc, review, image_path)
    write_motion_paths_image(doc, review, paths_path)
    review.output_paths.update({"json": json_path, "markdown": md_path, "image": image_path, "paths": paths_path})
    if with_art:
        silhouette_path = out_dir / "motion_silhouettes.png"
        written, silhouette_metrics = write_motion_silhouette_image(doc, review, silhouette_path)
        review.metrics["silhouette"] = silhouette_metrics
        # Rewrite JSON after optional raster diagnostics so machine output is complete.
        json_path.write_text(json.dumps(review.json_record(), indent=2) + "\n", encoding="utf8")
        if written is not None:
            review.output_paths["silhouette"] = written
    return review


__all__ = [
    "MotionFinding",
    "MotionFrame",
    "MotionReview",
    "review_document",
    "run_motion_review",
    "write_motion_review_image",
    "write_motion_paths_image",
    "write_motion_silhouette_image",
]
