"""Authoring-only gameplay geometry stored inside rig documents.

This module deliberately has no connection to sheet publication or the game
runtime yet. It gives the rig editor a place to seed, inspect, and edit
collision, hurtbox, and hitbox shapes before the runtime contract is changed.
Generated geometry is ordinary JSON data and becomes authoritative for the
authoring tool as soon as it is accepted into the document.

All coordinates are in logical rig-frame pixels. Shape dictionaries use one of
four intentionally small primitives:

``rect``
    ``x``, ``y``, ``w``, ``h``
``circle``
    ``cx``, ``cy``, ``r``
``capsule``
    segment endpoints ``ax``, ``ay``, ``bx``, ``by`` and radius ``r``
``polygon``
    ``points`` as ``[[x, y], ...]``. Runtime-facing export can later require
    convexity; the authoring tool reports concavity but does not destroy work.

Version 1 initially wrote a singular ``shape`` field for collision and
hurtboxes. :func:`entry_shapes` reads that representation and migrates it to a
``shapes`` list only when a caller explicitly requests mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
import copy
import math
from statistics import median
from typing import Iterable, Optional, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .rigdoc import RigDocument

GEOMETRY_VERSION = 2
SHAPE_KINDS = ("rect", "circle", "capsule", "polygon")
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


@dataclass(frozen=True)
class HurtboxSource:
    """Resolved hurtbox source for one animation clip."""

    kind: str
    profile_name: Optional[str]
    entry: Optional[dict]
    used_by: tuple[str, ...] = ()

    @property
    def is_override(self) -> bool:
        return self.kind in {"override", "legacy_override"}

    @property
    def is_shared(self) -> bool:
        return self.kind == "profile"


def geometry_root(doc: "RigDocument", *, create: bool = True) -> dict:
    """Return the authoring-only geometry block.

    Merely inspecting a document should not make it dirty, so callers may use
    ``create=False`` to receive an empty mapping when the block is absent.
    """
    if create:
        root = doc.data.setdefault("gameplay_geometry", {})
        root["version"] = max(int(root.get("version", 1)), GEOMETRY_VERSION)
        root.setdefault("space", "rig_frame_pixels")
        hurtboxes = root.setdefault("hurtboxes", {})
        hurtboxes.setdefault("profiles", {})
        hurtboxes.setdefault("clips", {})
        root.setdefault("hitboxes", {"clips": {}})
        return root
    return doc.data.get("gameplay_geometry") or {}


def rect_from_bbox(bbox: tuple[float, float, float, float]) -> dict:
    x0, y0, x1, y1 = bbox
    return {
        "kind": RECT_KIND,
        "x": float(x0),
        "y": float(y0),
        "w": float(max(0.0, x1 - x0)),
        "h": float(max(0.0, y1 - y0)),
    }


def rect_bbox(rect: dict) -> tuple[float, float, float, float]:
    x = float(rect.get("x", 0.0))
    y = float(rect.get("y", 0.0))
    return x, y, x + float(rect.get("w", 0.0)), y + float(rect.get("h", 0.0))


def shape_bbox(shape: dict) -> tuple[float, float, float, float]:
    """Return an axis-aligned frame-space bbox for any supported shape."""
    kind = shape.get("kind", RECT_KIND)
    if kind == "rect":
        return rect_bbox(shape)
    if kind == "circle":
        cx = float(shape.get("cx", 0.0))
        cy = float(shape.get("cy", 0.0))
        r = max(0.0, float(shape.get("r", 0.0)))
        return cx - r, cy - r, cx + r, cy + r
    if kind == "capsule":
        ax = float(shape.get("ax", 0.0))
        ay = float(shape.get("ay", 0.0))
        bx = float(shape.get("bx", ax))
        by = float(shape.get("by", ay))
        r = max(0.0, float(shape.get("r", 0.0)))
        return min(ax, bx) - r, min(ay, by) - r, max(ax, bx) + r, max(ay, by) + r
    points = shape.get("points") or []
    if not points:
        return 0.0, 0.0, 0.0, 0.0
    xs = [float(point[0]) for point in points]
    ys = [float(point[1]) for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def default_shape(kind: str, frame: dict, *, name: str = "shape") -> dict:
    """Create a useful centered primitive for the Add Shape action."""
    if kind not in SHAPE_KINDS:
        raise ValueError(f"unsupported gameplay geometry shape kind: {kind!r}")
    fw = float(frame.get("width", 128.0))
    fh = float(frame.get("height", 128.0))
    cx = float(frame.get("center_x", fw / 2.0))
    cy = min(float(frame.get("ground_y", fh * 0.8)) - fh * 0.20, fh * 0.55)
    if kind == "rect":
        return {"name": name, "kind": kind, "x": cx - 12.0, "y": cy - 18.0, "w": 24.0, "h": 36.0}
    if kind == "circle":
        return {"name": name, "kind": kind, "cx": cx, "cy": cy, "r": 14.0}
    if kind == "capsule":
        return {
            "name": name,
            "kind": kind,
            "ax": cx,
            "ay": cy - 14.0,
            "bx": cx,
            "by": cy + 14.0,
            "r": 10.0,
        }
    return {
        "name": name,
        "kind": kind,
        "points": [
            [cx - 14.0, cy - 12.0],
            [cx + 14.0, cy - 12.0],
            [cx + 18.0, cy + 10.0],
            [cx - 18.0, cy + 10.0],
        ],
    }


def convert_shape(shape: dict, kind: str) -> dict:
    """Convert a shape while preserving its name and visible bounds."""
    if kind not in SHAPE_KINDS:
        raise ValueError(kind)
    if shape.get("kind", RECT_KIND) == kind:
        return shape
    x0, y0, x1, y1 = shape_bbox(shape)
    name = str(shape.get("name", "shape"))
    cx = (x0 + x1) / 2.0
    cy = (y0 + y1) / 2.0
    w = max(1.0, x1 - x0)
    h = max(1.0, y1 - y0)
    if kind == "rect":
        return {"name": name, "kind": kind, "x": x0, "y": y0, "w": w, "h": h}
    if kind == "circle":
        return {"name": name, "kind": kind, "cx": cx, "cy": cy, "r": max(w, h) / 2.0}
    if kind == "capsule":
        radius = min(w, h) / 2.0
        if h >= w:
            return {
                "name": name,
                "kind": kind,
                "ax": cx,
                "ay": y0 + radius,
                "bx": cx,
                "by": y1 - radius,
                "r": radius,
            }
        return {
            "name": name,
            "kind": kind,
            "ax": x0 + radius,
            "ay": cy,
            "bx": x1 - radius,
            "by": cy,
            "r": radius,
        }
    return {
        "name": name,
        "kind": kind,
        "points": [[x0, y0], [x1, y0], [x1, y1], [x0, y1]],
    }


def translate_shape(shape: dict, dx: float, dy: float) -> None:
    """Translate a shape in place."""
    kind = shape.get("kind", RECT_KIND)
    if kind == "rect":
        shape["x"] = float(shape.get("x", 0.0)) + dx
        shape["y"] = float(shape.get("y", 0.0)) + dy
    elif kind == "circle":
        shape["cx"] = float(shape.get("cx", 0.0)) + dx
        shape["cy"] = float(shape.get("cy", 0.0)) + dy
    elif kind == "capsule":
        for key in ("ax", "bx"):
            shape[key] = float(shape.get(key, 0.0)) + dx
        for key in ("ay", "by"):
            shape[key] = float(shape.get(key, 0.0)) + dy
    else:
        shape["points"] = [
            [float(point[0]) + dx, float(point[1]) + dy]
            for point in shape.get("points") or []
        ]


def point_segment_distance(point, a, b) -> float:
    px, py = point
    ax, ay = a
    bx, by = b
    vx, vy = bx - ax, by - ay
    denom = vx * vx + vy * vy
    if denom <= 1e-12:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / denom))
    qx, qy = ax + t * vx, ay + t * vy
    return math.hypot(px - qx, py - qy)


def point_in_polygon(point, points) -> bool:
    """Even-odd point-in-polygon test, including edge-adjacent points."""
    if len(points) < 3:
        return False
    x, y = point
    inside = False
    j = len(points) - 1
    for i in range(len(points)):
        xi, yi = float(points[i][0]), float(points[i][1])
        xj, yj = float(points[j][0]), float(points[j][1])
        if point_segment_distance((x, y), (xi, yi), (xj, yj)) <= 1e-6:
            return True
        crosses = (yi > y) != (yj > y)
        if crosses:
            x_at_y = (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi
            if x < x_at_y:
                inside = not inside
        j = i
    return inside


def point_in_shape(shape: dict, point) -> bool:
    kind = shape.get("kind", RECT_KIND)
    x, y = point
    if kind == "rect":
        x0, y0, x1, y1 = shape_bbox(shape)
        return x0 <= x <= x1 and y0 <= y <= y1
    if kind == "circle":
        return math.hypot(x - float(shape.get("cx", 0.0)), y - float(shape.get("cy", 0.0))) <= float(shape.get("r", 0.0))
    if kind == "capsule":
        return point_segment_distance(
            point,
            (float(shape.get("ax", 0.0)), float(shape.get("ay", 0.0))),
            (float(shape.get("bx", 0.0)), float(shape.get("by", 0.0))),
        ) <= float(shape.get("r", 0.0))
    return point_in_polygon(point, shape.get("points") or [])


def polygon_is_convex(points) -> bool:
    """Return true for a consistently wound polygon with at least 3 points."""
    if len(points) < 3:
        return False
    sign = 0
    for i in range(len(points)):
        a = points[i - 1]
        b = points[i]
        c = points[(i + 1) % len(points)]
        cross = (float(b[0]) - float(a[0])) * (float(c[1]) - float(b[1])) - (
            float(b[1]) - float(a[1])
        ) * (float(c[0]) - float(b[0]))
        if abs(cross) < 1e-8:
            continue
        current = 1 if cross > 0 else -1
        if sign and current != sign:
            return False
        sign = current
    return sign != 0


def entry_shapes(entry: Optional[dict], *, create: bool = False) -> list[dict]:
    """Return an entry's shapes, optionally migrating the old singular field."""
    if entry is None:
        return []
    shapes = entry.get("shapes")
    if isinstance(shapes, list):
        return shapes
    legacy = entry.get("shape")
    if not isinstance(legacy, dict):
        if create:
            entry["shapes"] = []
            return entry["shapes"]
        return []
    if create:
        entry.pop("shape", None)
        entry["shapes"] = [legacy]
        return entry["shapes"]
    return [legacy]


def mark_entry_edited(entry: Optional[dict]) -> None:
    if entry is not None:
        entry.setdefault("provenance", {})["edited"] = True


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
    return {"generated": True, "edited": False, "method": method, **extra}


def generate_collision(doc: "RigDocument", *, replace: bool = False) -> GenerationResult:
    """Seed one global collision rectangle from the reference visual pose."""
    existing = collision_entry(doc)
    if existing and entry_shapes(existing) and not replace:
        raise ExistingGeometryError("collision geometry already exists")
    clip = "idle" if "idle" in doc.clips else next(iter(doc.clips), "")
    if not clip:
        raise ValueError("document has no animation clips")
    bbox = _alpha_bbox(doc, clip, 0)
    if bbox is None:
        raise ValueError(f"reference pose {clip!r} has no visible pixels")
    root = geometry_root(doc)
    shape = rect_from_bbox(bbox)
    shape["name"] = "body_collision"
    root["collision"] = {
        "shapes": [shape],
        "provenance": _provenance("reference_alpha_bbox_v1", clip=clip, frame=0),
    }
    return GenerationResult("collision", 1, f"Generated collision from {clip} frame 0")


def _pose_family(clip_name: str) -> str:
    """Choose a human-readable starting profile family from a clip name."""
    name = clip_name.lower()
    families = (
        ("rolling", ("roll", "tumble", "spin")),
        ("crouching", ("crouch", "duck", "crawl")),
        ("ledge", ("ledge", "hang", "climb")),
        ("airborne", ("air", "jump", "fall", "fly", "hover", "float")),
        ("damaged", ("hurt", "damage", "death", "dead", "stun", "knock", "downed")),
        ("special", ("transform", "teleport", "blink_out", "blink_in")),
    )
    for family, hints in families:
        if any(hint in name for hint in hints):
            return family
    return "standing"


def _bbox_iou(a, b) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    intersection = max(0.0, ix1 - ix0) * max(0.0, iy1 - iy0)
    area_a = max(0.0, ax1 - ax0) * max(0.0, ay1 - ay0)
    area_b = max(0.0, bx1 - bx0) * max(0.0, by1 - by0)
    union = area_a + area_b - intersection
    return intersection / union if union > 1e-9 else 0.0


def _representative_bbox(items: list[tuple[str, tuple[int, int, int, int]]]):
    return tuple(float(median([bbox[index] for _clip, bbox in items])) for index in range(4))


def _similar_hurtbox(doc: "RigDocument", bbox, representative) -> bool:
    fw = max(1.0, float(doc.frame.get("width", 1.0)))
    fh = max(1.0, float(doc.frame.get("height", 1.0)))
    edge_delta = max(
        abs(bbox[0] - representative[0]) / fw,
        abs(bbox[2] - representative[2]) / fw,
        abs(bbox[1] - representative[1]) / fh,
        abs(bbox[3] - representative[3]) / fh,
    )
    return _bbox_iou(bbox, representative) >= 0.68 or edge_delta <= 0.055


def _unique_profile_name(profiles: dict, base: str) -> str:
    base = base.strip().lower().replace(" ", "_") or "profile"
    if base not in profiles:
        return base
    suffix = 2
    while f"{base}_{suffix}" in profiles:
        suffix += 1
    return f"{base}_{suffix}"


def generate_hurtboxes(doc: "RigDocument", *, replace: bool = False) -> GenerationResult:
    """Generate shared hurtbox profiles and assign every visible clip.

    Each clip is measured using the existing animation-union alpha bounds. Similar
    measurements are clustered within broad pose families, then represented by a
    median rectangle. The result is intentionally editable authoring data, not a
    runtime contract.
    """
    hurt = geometry_root(doc, create=False).get("hurtboxes", {})
    existing_profiles = hurt.get("profiles", {})
    existing_clips = hurt.get("clips", {})
    has_existing = any(entry_shapes(entry) for entry in existing_profiles.values())
    if not has_existing:
        for binding in existing_clips.values():
            if entry_shapes(binding) or entry_shapes((binding or {}).get("override")):
                has_existing = True
                break
    if has_existing and not replace:
        raise ExistingGeometryError("hurtbox geometry already exists")

    measured: dict[str, tuple[int, int, int, int]] = {}
    for clip_name, clip in doc.clips.items():
        nframes = max(1, int(clip.get("frames", 1)))
        bbox = _union_bboxes(_alpha_bbox(doc, clip_name, i) for i in range(nframes))
        if bbox is not None:
            measured[clip_name] = bbox

    families: dict[str, list[tuple[str, tuple[int, int, int, int]]]] = {}
    for clip_name, bbox in measured.items():
        families.setdefault(_pose_family(clip_name), []).append((clip_name, bbox))

    root = geometry_root(doc)
    hurt_out = root.setdefault("hurtboxes", {})
    profiles_out = hurt_out.setdefault("profiles", {})
    clips_out = hurt_out.setdefault("clips", {})
    profiles_out.clear()
    clips_out.clear()

    profile_count = 0
    for family in sorted(families):
        clusters: list[list[tuple[str, tuple[int, int, int, int]]]] = []
        for item in sorted(families[family]):
            for cluster in clusters:
                if _similar_hurtbox(doc, item[1], _representative_bbox(cluster)):
                    cluster.append(item)
                    break
            else:
                clusters.append([item])

        for cluster_index, cluster in enumerate(clusters, start=1):
            base = family if cluster_index == 1 else f"{family}_{cluster_index}"
            profile_name = _unique_profile_name(profiles_out, base)
            representative = _representative_bbox(cluster)
            shape = rect_from_bbox(representative)
            shape["name"] = "body_hurt"
            clip_names = [clip_name for clip_name, _bbox in cluster]
            profiles_out[profile_name] = {
                "shapes": [shape],
                "provenance": _provenance(
                    "clustered_animation_union_alpha_bbox_v2",
                    family=family,
                    clips=clip_names,
                ),
            }
            for clip_name in clip_names:
                clips_out[clip_name] = {"profile": profile_name}
            profile_count += 1

    return GenerationResult(
        "hurtboxes",
        profile_count,
        f"Generated {profile_count} shared hurtbox profiles for {len(clips_out)} clips",
    )

def _active_frames(doc: "RigDocument", clip_name: str) -> list[int]:
    clip = doc.clips[clip_name]
    nframes = max(1, int(clip.get("frames", 1)))
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
        motion = max(p[0] for p in points) - min(p[0] for p in points) + max(p[1] for p in points) - min(p[1] for p in points)
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
    """Seed a conservative attack rectangle for one clip."""
    if clip_name not in doc.clips:
        raise KeyError(clip_name)
    existing = geometry_root(doc, create=False).get("hitboxes", {}).get("clips", {})
    if clip_name in existing and entry_shapes(existing[clip_name]) and not replace:
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

    shape["name"] = "attack"
    root = geometry_root(doc)
    clips_out = root.setdefault("hitboxes", {}).setdefault("clips", {})
    clips_out[clip_name] = {
        "active_frames": [min(frames), max(frames)],
        "shapes": [shape],
        "bindings": {"vfx": [], "sfx": []},
        "provenance": _provenance(
            method, clip=clip_name, terminal=terminal_name, warning=warning
        ),
    }
    return GenerationResult("hitbox", 1, f"Generated hitbox seed for {clip_name}")


def collision_entry(doc: "RigDocument", *, create: bool = False) -> Optional[dict]:
    root = geometry_root(doc, create=create)
    entry = root.get("collision")
    if entry is None and create:
        entry = {"shapes": [], "provenance": {"generated": False, "edited": True, "method": "manual"}}
        root["collision"] = entry
    return entry


def hurtbox_profiles(doc: "RigDocument", *, create: bool = False) -> dict:
    root = geometry_root(doc, create=create)
    hurtboxes = root.get("hurtboxes", {})
    if create:
        return hurtboxes.setdefault("profiles", {})
    return hurtboxes.get("profiles", {})


def hurtbox_clip_binding(
    doc: "RigDocument", clip_name: str, *, create: bool = False
) -> Optional[dict]:
    root = geometry_root(doc, create=create)
    hurtboxes = root.get("hurtboxes", {})
    clips = hurtboxes.get("clips", {})
    binding = clips.get(clip_name)
    if binding is None and create:
        clips = hurtboxes.setdefault("clips", {})
        binding = {}
        clips[clip_name] = binding
    return binding


def hurtbox_profile_users(doc: "RigDocument", profile_name: str) -> tuple[str, ...]:
    clips = geometry_root(doc, create=False).get("hurtboxes", {}).get("clips", {})
    return tuple(sorted(
        clip_name
        for clip_name, binding in clips.items()
        if (
            isinstance(binding, dict)
            and binding.get("profile") == profile_name
            and not isinstance(binding.get("override"), dict)
        )
    ))


def hurtbox_source(doc: "RigDocument", clip_name: str) -> HurtboxSource:
    binding = hurtbox_clip_binding(doc, clip_name)
    if not isinstance(binding, dict):
        return HurtboxSource("missing", None, None)

    # Version-1 files stored a complete entry directly under clips.<name>.
    if entry_shapes(binding):
        return HurtboxSource("legacy_override", None, binding, (clip_name,))

    profile_name = binding.get("profile")
    override = binding.get("override")
    if isinstance(override, dict):
        return HurtboxSource("override", profile_name, override, (clip_name,))

    profile = hurtbox_profiles(doc).get(profile_name) if profile_name else None
    if isinstance(profile, dict):
        return HurtboxSource(
            "profile",
            str(profile_name),
            profile,
            hurtbox_profile_users(doc, str(profile_name)),
        )
    return HurtboxSource("missing", str(profile_name) if profile_name else None, None)


def create_hurtbox_profile(
    doc: "RigDocument", name: str, *, source_entry: Optional[dict] = None
) -> str:
    profiles = hurtbox_profiles(doc, create=True)
    profile_name = _unique_profile_name(profiles, name)
    if source_entry is None:
        entry = {
            "shapes": [],
            "provenance": {"generated": False, "edited": True, "method": "manual"},
        }
    else:
        entry = copy.deepcopy(source_entry)
        provenance = entry.setdefault("provenance", {})
        provenance.update({"generated": False, "edited": True, "method": "duplicated_profile"})
    profiles[profile_name] = entry
    return profile_name


def assign_hurtbox_profile(doc: "RigDocument", clip_name: str, profile_name: str) -> None:
    if profile_name not in hurtbox_profiles(doc):
        raise KeyError(profile_name)
    binding = hurtbox_clip_binding(doc, clip_name, create=True)
    binding.clear()
    binding["profile"] = profile_name


def make_hurtbox_override(doc: "RigDocument", clip_name: str) -> dict:
    source = hurtbox_source(doc, clip_name)
    if source.is_override and source.entry is not None:
        return source.entry
    binding = hurtbox_clip_binding(doc, clip_name, create=True)
    if source.profile_name:
        binding["profile"] = source.profile_name
    entry = copy.deepcopy(source.entry) if source.entry is not None else {
        "shapes": [],
        "provenance": {},
    }
    provenance = entry.setdefault("provenance", {})
    provenance.update({"generated": False, "edited": True, "method": "local_override"})
    binding["override"] = entry
    return entry


def remove_hurtbox_override(doc: "RigDocument", clip_name: str) -> bool:
    binding = hurtbox_clip_binding(doc, clip_name)
    if not isinstance(binding, dict) or "override" not in binding:
        return False
    binding.pop("override", None)
    return True


def hurtbox_entry(doc: "RigDocument", clip_name: str, *, create: bool = False) -> Optional[dict]:
    source = hurtbox_source(doc, clip_name)
    if source.entry is not None:
        return source.entry
    if not create:
        return None

    profiles = hurtbox_profiles(doc, create=True)
    profile_name = create_hurtbox_profile(doc, "default") if not profiles else sorted(profiles)[0]
    assign_hurtbox_profile(doc, clip_name, profile_name)
    return hurtbox_profiles(doc)[profile_name]

def hitbox_entry(doc: "RigDocument", clip_name: str, *, create: bool = False) -> Optional[dict]:
    root = geometry_root(doc, create=create)
    clips = root.get("hitboxes", {}).get("clips", {})
    entry = clips.get(clip_name)
    if entry is None and create:
        clips = root.setdefault("hitboxes", {}).setdefault("clips", {})
        entry = {
            "active_frames": [0, max(0, int(doc.clips.get(clip_name, {}).get("frames", 1)) - 1)],
            "shapes": [],
            "bindings": {"vfx": [], "sfx": []},
            "provenance": {"generated": False, "edited": True, "method": "manual"},
        }
        clips[clip_name] = entry
    return entry


def layer_entry(doc: "RigDocument", layer: str, clip_name: str, *, create: bool = False) -> Optional[dict]:
    if layer == "collision":
        return collision_entry(doc, create=create)
    if layer == "hurtbox":
        return hurtbox_entry(doc, clip_name, create=create)
    if layer == "hitbox":
        return hitbox_entry(doc, clip_name, create=create)
    raise ValueError(layer)


def layer_shapes(doc: "RigDocument", layer: str, clip_name: str, *, create: bool = False) -> list[dict]:
    return entry_shapes(layer_entry(doc, layer, clip_name, create=create), create=create)


def attack_like_clips(doc: "RigDocument") -> list[str]:
    return [name for name in doc.clips if any(token in name.lower() for token in ATTACK_NAME_HINTS)]
