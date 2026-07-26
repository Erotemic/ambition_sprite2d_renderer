"""Authoring-only gameplay geometry stored inside rig documents.

This module deliberately has no connection to sheet publication or the game
runtime yet.  It gives the rig editor a place to seed, inspect, and edit
collision, hurtbox, and hitbox rectangles before the runtime contract is
changed.  Generated geometry is ordinary JSON data and becomes authoritative
for the authoring tool as soon as it is accepted into the document.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Optional, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .rigdoc import RigDocument

GEOMETRY_VERSION = 1
RECT_KIND = "rect"

ATTACK_NAME_HINTS = (
    "attack",
    "slash",
    "air_",
    "ledge_getup_attack",
    "shoot",
)
TERMINAL_NAME_HINTS = ("hand", "foot", "fist", "weapon", "blade")


class ExistingGeometryError(RuntimeError):
    """Raised when a non-destructive generator would replace authored data."""


@dataclass(frozen=True)
class GenerationResult:
    layer: str
    count: int
    message: str


def geometry_root(doc: "RigDocument", *, create: bool = True) -> dict:
    """Return the authoring-only geometry block.

    Merely inspecting a document should not make it dirty, so callers may use
    ``create=False`` to receive an empty mapping when the block is absent.
    """
    if create:
        root = doc.data.setdefault("gameplay_geometry", {})
        root.setdefault("version", GEOMETRY_VERSION)
        root.setdefault("space", "rig_frame_pixels")
        root.setdefault("hurtboxes", {"clips": {}})
        root.setdefault("hitboxes", {"clips": {}})
        return root
    return doc.data.get("gameplay_geometry") or {}


def rect_from_bbox(bbox: tuple[int, int, int, int]) -> dict:
    x0, y0, x1, y1 = bbox
    return {
        "kind": RECT_KIND,
        "x": float(x0),
        "y": float(y0),
        "w": float(max(0, x1 - x0)),
        "h": float(max(0, y1 - y0)),
    }


def rect_bbox(rect: dict) -> tuple[float, float, float, float]:
    x = float(rect.get("x", 0.0))
    y = float(rect.get("y", 0.0))
    return x, y, x + float(rect.get("w", 0.0)), y + float(rect.get("h", 0.0))


def _alpha_bbox(doc: "RigDocument", clip: str, frame_idx: int) -> Optional[tuple[int, int, int, int]]:
    t = doc.frame_time(clip, frame_idx)
    image = doc.render_at(clip, t, supersample=1, scale=1)
    return image.getchannel("A").getbbox()


def _union_bboxes(boxes: Iterable[Optional[tuple[int, int, int, int]]]) -> Optional[tuple[int, int, int, int]]:
    union = None
    for bbox in boxes:
        if bbox is None:
            continue
        if union is None:
            union = list(bbox)
        else:
            union[0] = min(union[0], bbox[0])
            union[1] = min(union[1], bbox[1])
            union[2] = max(union[2], bbox[2])
            union[3] = max(union[3], bbox[3])
    return tuple(union) if union is not None else None


def _provenance(method: str, **extra) -> dict:
    return {
        "generated": True,
        "edited": False,
        "method": method,
        **extra,
    }


def generate_collision(doc: "RigDocument", *, replace: bool = False) -> GenerationResult:
    """Seed one global collision rectangle from the reference visual pose.

    The current sheet pipeline derives body metrics from its first frame.  To
    remain migration-friendly, this authoring seed uses frame zero of ``idle``
    when available, otherwise frame zero of the first clip.
    """
    existing = geometry_root(doc, create=False).get("collision")
    if existing and not replace:
        raise ExistingGeometryError("collision geometry already exists")
    clip = "idle" if "idle" in doc.clips else next(iter(doc.clips), "")
    if not clip:
        raise ValueError("document has no animation clips")
    bbox = _alpha_bbox(doc, clip, 0)
    if bbox is None:
        raise ValueError(f"reference pose {clip!r} has no visible pixels")
    root = geometry_root(doc)
    root["collision"] = {
        "shape": rect_from_bbox(bbox),
        "provenance": _provenance("reference_alpha_bbox_v1", clip=clip, frame=0),
    }
    return GenerationResult("collision", 1, f"Generated collision from {clip} frame 0")


def generate_hurtboxes(doc: "RigDocument", *, replace: bool = False) -> GenerationResult:
    """Seed one union-alpha hurtbox rectangle for every animation clip."""
    existing = (
        geometry_root(doc, create=False).get("hurtboxes", {}).get("clips", {})
    )
    if existing and not replace:
        raise ExistingGeometryError("hurtbox geometry already exists")
    generated = {}
    for clip_name, clip in doc.clips.items():
        nframes = max(1, int(clip.get("frames", 1)))
        bbox = _union_bboxes(_alpha_bbox(doc, clip_name, i) for i in range(nframes))
        if bbox is None:
            continue
        generated[clip_name] = {
            "shape": rect_from_bbox(bbox),
            "provenance": _provenance(
                "animation_union_alpha_bbox_v1",
                clip=clip_name,
                frames=nframes,
            ),
        }
    root = geometry_root(doc)
    clips_out = root.setdefault("hurtboxes", {}).setdefault("clips", {})
    clips_out.clear()
    clips_out.update(generated)
    return GenerationResult(
        "hurtboxes",
        len(clips_out),
        f"Generated visual-union hurtboxes for {len(clips_out)} clips",
    )


def _active_frames(doc: "RigDocument", clip_name: str) -> list[int]:
    clip = doc.clips[clip_name]
    nframes = max(1, int(clip.get("frames", 1)))
    # The Player Robot and several paper-doll targets already expose a scalar
    # slash channel.  Prefer its nonzero frames when available.
    if "slash" in clip.get("channels", {}):
        active = [
            i
            for i in range(nframes)
            if float(doc.sample(clip_name, doc.frame_time(clip_name, i)).get("slash", 0.0)) > 0.05
        ]
        if active:
            return active
    if nframes == 1:
        return [0]
    start = max(0, int(math.floor(nframes * 0.25)))
    end = min(nframes - 1, int(math.ceil(nframes * 0.70)))
    return list(range(start, end + 1))


def _direction_hint(clip_name: str) -> tuple[float, float]:
    name = clip_name.lower()
    if "up" in name:
        return (0.0, -1.0)
    if "down" in name:
        return (0.0, 1.0)
    if "back" in name:
        return (-1.0, 0.0)
    return (1.0, 0.0)


def _terminal_candidates(world: dict) -> list[tuple[str, tuple[float, float]]]:
    out = []
    for name, bone in world.items():
        lname = name.lower()
        if any(token in lname for token in TERMINAL_NAME_HINTS):
            point = bone.tip if float(getattr(bone, "length", 0.0)) > 0 else bone.origin
            out.append((name, point))
    return out


def _choose_terminal(doc: "RigDocument", clip_name: str, frames: list[int]) -> tuple[Optional[str], list[tuple[float, float]]]:
    dx, dy = _direction_hint(clip_name)
    cx = float(doc.frame.get("center_x", float(doc.frame["width"]) / 2.0))
    cy = float(doc.frame.get("ground_y", float(doc.frame["height"]) * 0.75))
    tracks: dict[str, list[tuple[float, float]]] = {}
    for frame in frames:
        world, _ = doc.solve(clip_name, doc.frame_time(clip_name, frame))
        for name, point in _terminal_candidates(world):
            tracks.setdefault(name, []).append(point)
    if not tracks:
        return None, []

    def score(item):
        _name, points = item
        directional = max((p[0] - cx) * dx + (p[1] - cy) * dy for p in points)
        motion = (
            max(p[0] for p in points) - min(p[0] for p in points)
            + max(p[1] for p in points) - min(p[1] for p in points)
        )
        return directional + 0.5 * motion

    name, points = max(tracks.items(), key=score)
    return name, points


def _clamped_rect(doc: "RigDocument", points: list[tuple[float, float]], *, pad: float) -> dict:
    fw = float(doc.frame["width"])
    fh = float(doc.frame["height"])
    x0 = max(0.0, min(p[0] for p in points) - pad)
    y0 = max(0.0, min(p[1] for p in points) - pad)
    x1 = min(fw, max(p[0] for p in points) + pad)
    y1 = min(fh, max(p[1] for p in points) + pad)
    return {
        "kind": RECT_KIND,
        "x": round(x0, 2),
        "y": round(y0, 2),
        "w": round(max(1.0, x1 - x0), 2),
        "h": round(max(1.0, y1 - y0), 2),
    }


def generate_hitbox(doc: "RigDocument", clip_name: str, *, replace: bool = False) -> GenerationResult:
    """Seed a conservative attack rectangle for one clip.

    This is intentionally a suggestion, not semantic inference.  It chooses the
    hand/foot terminal that travels furthest in the direction implied by the
    clip name, follows it through the active frames, and extends the track by a
    short weapon/reach allowance.  The GUI exposes the result for correction.
    """
    if clip_name not in doc.clips:
        raise KeyError(clip_name)
    existing = (
        geometry_root(doc, create=False).get("hitboxes", {}).get("clips", {})
    )
    if clip_name in existing and not replace:
        raise ExistingGeometryError(f"hitbox for {clip_name!r} already exists")

    frames = _active_frames(doc, clip_name)
    terminal_name, points = _choose_terminal(doc, clip_name, frames)
    method = "terminal_motion_reach_v1"
    warning = "Generated from terminal-bone motion; review before use."
    if points:
        dx, dy = _direction_hint(clip_name)
        reach = 24.0
        points = points + [(x + dx * reach, y + dy * reach) for x, y in points]
        shape = _clamped_rect(doc, points, pad=7.0)
    else:
        bbox = _union_bboxes(_alpha_bbox(doc, clip_name, i) for i in frames)
        if bbox is None:
            raise ValueError(f"clip {clip_name!r} has no visible attack frames")
        shape = rect_from_bbox(bbox)
        method = "active_frame_alpha_bbox_fallback_v1"
        warning = "No hand/foot terminal found; generated from the whole visible pose."

    root = geometry_root(doc)
    clips_out = root.setdefault("hitboxes", {}).setdefault("clips", {})
    clips_out[clip_name] = {
        "active_frames": [min(frames), max(frames)],
        "shapes": [shape],
        "bindings": {
            "vfx": [],
            "sfx": [],
        },
        "provenance": _provenance(
            method,
            clip=clip_name,
            terminal=terminal_name,
            warning=warning,
        ),
    }
    return GenerationResult("hitbox", 1, f"Generated hitbox seed for {clip_name}")


def collision_entry(doc: "RigDocument") -> Optional[dict]:
    return geometry_root(doc, create=False).get("collision")


def hurtbox_entry(doc: "RigDocument", clip_name: str) -> Optional[dict]:
    return (
        geometry_root(doc, create=False)
        .get("hurtboxes", {})
        .get("clips", {})
        .get(clip_name)
    )


def hitbox_entry(doc: "RigDocument", clip_name: str) -> Optional[dict]:
    return (
        geometry_root(doc, create=False)
        .get("hitboxes", {})
        .get("clips", {})
        .get(clip_name)
    )


def attack_like_clips(doc: "RigDocument") -> list[str]:
    return [
        name
        for name in doc.clips
        if any(token in name.lower() for token in ATTACK_NAME_HINTS)
    ]
