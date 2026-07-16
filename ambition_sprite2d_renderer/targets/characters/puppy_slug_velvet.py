"""Bespoke procedural sprite for the Velvet Puppy Slug.

This is a distinct puppy-slug lineage, authored from first principles rather
than reskinning either existing puppy-slug target.  It is one coherent animal:

* a continuous low slug mantle and ventral crawling foot,
* two oversized floppy sensory ears,
* one expressive puppy face integrated into the head,
* a wagging paddle-tail grown from the mantle,
* paw-like locomotor lobes with visible pad markings.

The renderer is intentionally Python/Pillow-only.  Every visual is vector-like
geometry drawn in code.  It uses no source images, SVGs, blur, glow, ground
ellipse, or drop shadow.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from PIL import Image, ImageColor, ImageDraw

from ...authoring.sheet_build import build_sheet, write_canonical

TARGET_NAME = "puppy_slug_velvet"
FRAME_SIZE = (128, 128)
SUPER = 4
WORK_SIZE = (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER)

SHEET_FILES = [
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
]

ROWS = [
    ("idle", 8, 145),
    ("walk", 10, 88),
    ("slash", 7, 82),
    ("taunt", 8, 110),
    ("wall_walk", 8, 94),
    ("ceiling_walk", 8, 94),
    ("hurt", 4, 72),
    ("death", 9, 108),
]

# Named, explicit compositing order.  Parts that must remain readable are not
# allowed to depend on incidental call order inside a large painter.
LAYER_ORDER = {
    "motion_back": 5,
    "tail": 10,
    "far_ear": 20,
    "far_lobes": 30,
    "body": 40,
    "belly": 50,
    "dorsal": 60,
    "face": 70,
    "near_ear": 80,
    "near_lobes": 90,
    "details": 100,
    "motion_front": 110,
}

CHARACTER_LINEAGE = {
    "variant_id": "velvet_2026_07_15",
    "family": "puppy_slug",
    "created_by": "GPT-5.6 Thinking",
    "authorship_surface": "python_procedural_sprite",
    "relationship": "distinct_variant_not_derived_from_existing_art",
}

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_puppy_slug_velvet",
        "display_name": "Velvet Puppy Slug",
    },
    "body": {
        "body_plan": "Crawler",
        "body_kind": "LowProfile",
        "mass_class": "Light",
        "locomotion_hint": "Slither",
        "traits": [
            "enemy",
            "ai_era",
            "crawler",
            "no_hands",
            "wall_crawler",
            "puppy_slug_variant",
            "velvet_mantle",
        ],
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": None,
            "climb": True,
            "fly": None,
            "swim": None,
            "crawl": True,
            "use_lifts": None,
            "door_access": [],
        },
        "interactions": {
            "talk": None,
            "trade": None,
            "carry": None,
            "open_doors": [],
        },
    },
    "brain": {"default_preset": "wanderer_puppy_slug"},
    "actions": {"default_preset": "zombie_bite"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.wall_crawl": {"animation": "wall_walk", "events": []},
        "locomotion.ceiling_crawl": {
            "animation": "ceiling_walk",
            "events": [],
        },
        "action.melee.primary": {
            "animation": "slash",
            "events": [
                {
                    "t": 0.38,
                    "event": "hitbox_active_start",
                    "source": "puppy_slug_velvet.bite",
                },
                {
                    "t": 0.62,
                    "event": "hitbox_active_end",
                    "source": "puppy_slug_velvet.bite",
                },
            ],
        },
        "social.taunt": {"animation": "taunt", "events": []},
        "damage.hit": {"animation": "hurt", "events": []},
        "lifecycle.death": {"animation": "death", "events": []},
    },
    "sockets": {
        "mouth": {
            "source": "puppy_slug_velvet.geometry",
            "point": {"x": 103.0, "y": 62.0},
        },
        "head": {
            "source": "puppy_slug_velvet.geometry",
            "point": {"x": 91.0, "y": 54.0},
        },
        "belly": {
            "source": "puppy_slug_velvet.geometry",
            "point": {"x": 64.0, "y": 79.0},
        },
        "tail": {
            "source": "puppy_slug_velvet.geometry",
            "point": {"x": 25.0, "y": 68.0},
        },
        "wall_contact": {
            "source": "puppy_slug_velvet.geometry",
            "point": {"x": 64.0, "y": 84.0},
        },
    },
    "tags": ["enemy", "ai_era", "crawler", "puppy_slug_variant"],
    # Newer actor-contract writers preserve this nested field.  Older writers
    # safely ignore it; the module-level CHARACTER_LINEAGE remains canonical.
    "provenance": {"lineage": CHARACTER_LINEAGE},
}

# Palette: deliberately unrelated to the jaundiced/brown existing variants.
OUTLINE = "#241a31"
BODY_DARK = "#593d7d"
BODY_MID = "#8760b9"
BODY_LIGHT = "#c5a2eb"
BODY_GLEAM = "#eadcff"
BELLY = "#f0d3c7"
BELLY_LIGHT = "#ffe8dd"
EAR_OUTER = "#694894"
EAR_INNER = "#ee8eae"
EAR_GLEAM = "#ffc1d2"
FRILL = "#67cfbd"
FRILL_LIGHT = "#a9f1df"
MUZZLE = "#f3cfba"
MUZZLE_LIGHT = "#ffe8d6"
NOSE = "#2a1a2c"
EYE_WHITE = "#fff8ef"
EYE_IRIS = "#e39a3d"
EYE_PUPIL = "#1a1420"
TONGUE = "#e8759a"
PAD = "#cf7097"
TOOTH = "#fff7df"
MOTION = "#d8c4fa"

Point = tuple[float, float]
RGBA = tuple[int, int, int, int]


def _rgba(value: str, alpha: int = 255) -> RGBA:
    r, g, b = ImageColor.getrgb(value)
    return (r, g, b, alpha)


def _s(value: float) -> int:
    return int(round(value * SUPER))


def _pts(points: Iterable[Point]) -> list[tuple[int, int]]:
    return [(_s(x), _s(y)) for x, y in points]


def _box(cx: float, cy: float, rx: float, ry: float) -> tuple[int, int, int, int]:
    return (_s(cx - rx), _s(cy - ry), _s(cx + rx), _s(cy + ry))


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * max(0.0, min(1.0, t))


def _smooth(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _pulse(t: float, start: float, peak: float, end: float) -> float:
    if t <= start or t >= end:
        return 0.0
    if t < peak:
        return _smooth((t - start) / max(1e-6, peak - start))
    return 1.0 - _smooth((t - peak) / max(1e-6, end - peak))


def _bezier(a: Point, b: Point, c: Point, d: Point, count: int = 18) -> list[Point]:
    points: list[Point] = []
    for i in range(count):
        t = i / max(1, count - 1)
        u = 1.0 - t
        points.append(
            (
                u**3 * a[0]
                + 3 * u * u * t * b[0]
                + 3 * u * t * t * c[0]
                + t**3 * d[0],
                u**3 * a[1]
                + 3 * u * u * t * b[1]
                + 3 * u * t * t * c[1]
                + t**3 * d[1],
            )
        )
    return points


def _ellipse_points(
    center: Point, rx: float, ry: float, angle_deg: float, count: int = 30
) -> list[Point]:
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    out: list[Point] = []
    for i in range(count):
        t = math.tau * i / count
        x = math.cos(t) * rx
        y = math.sin(t) * ry
        out.append((center[0] + x * ca - y * sa, center[1] + x * sa + y * ca))
    return out


@dataclass(frozen=True)
class Pose:
    center: Point = (64.0, 70.0)
    angle: float = 0.0
    stretch: float = 1.0
    squash: float = 1.0
    wave: float = 0.0
    wave_phase: float = 0.0
    head_lift: float = 0.0
    head_reach: float = 0.0
    tail_wag: float = 0.0
    ear_droop: float = 8.0
    ear_sweep: float = 0.0
    eye_open: float = 1.0
    pupil_shift: float = 0.0
    mouth_open: float = 0.0
    tongue: float = 0.0
    near_front_lift: float = 0.0
    near_rear_lift: float = 0.0
    far_front_lift: float = 0.0
    far_rear_lift: float = 0.0
    frill_spread: float = 1.0
    death: float = 0.0
    impact: float = 0.0


def _pose_for(animation: str, frame_idx: int, nframes: int) -> Pose:
    cyc = math.tau * frame_idx / max(1, nframes)
    s = math.sin(cyc)
    c = math.cos(cyc)
    u = frame_idx / max(1, nframes - 1)

    if animation == "idle":
        # A deliberate blink in one frame, otherwise breathing + sniffing.
        eye_open = 0.12 if frame_idx == 5 else 1.0
        return Pose(
            center=(64.0 + 0.6 * c, 71.0 + 1.1 * s),
            stretch=1.0 + 0.018 * c,
            squash=1.0 - 0.025 * c,
            wave=0.7,
            wave_phase=cyc * 0.55,
            head_lift=-0.8 + 0.7 * s,
            head_reach=0.8 * c,
            tail_wag=13.0 * math.sin(cyc * 2.0),
            ear_droop=8.0 + 1.5 * s,
            ear_sweep=2.0 * c,
            eye_open=eye_open,
            pupil_shift=0.8 * s,
            mouth_open=0.0,
            frill_spread=0.95 + 0.08 * c,
        )

    if animation == "walk":
        # Alternating foot lobes + a traveling body wave.  The frame remains
        # centered; the motion is entirely anatomical so it loops in place.
        near_front = max(0.0, math.sin(cyc))
        near_rear = max(0.0, math.sin(cyc + math.pi))
        far_front = max(0.0, math.sin(cyc + math.pi))
        far_rear = max(0.0, math.sin(cyc))
        return Pose(
            center=(64.0, 70.0 + 1.8 * abs(s)),
            angle=2.0 * s,
            stretch=1.0 + 0.045 * c,
            squash=1.0 - 0.035 * c,
            wave=2.8,
            wave_phase=cyc,
            head_lift=-1.2 * abs(s),
            head_reach=1.3 * c,
            tail_wag=19.0 * math.sin(cyc + 0.45),
            ear_droop=9.5,
            ear_sweep=-5.0 * s,
            eye_open=1.0,
            pupil_shift=1.0,
            near_front_lift=near_front * 5.2,
            near_rear_lift=near_rear * 4.7,
            far_front_lift=far_front * 3.4,
            far_rear_lift=far_rear * 3.2,
            frill_spread=1.0 + 0.08 * abs(s),
        )

    if animation == "slash":
        if u < 0.24:
            q = _smooth(u / 0.24)
            return Pose(
                center=(_lerp(64.0, 57.0, q), _lerp(71.0, 75.0, q)),
                angle=_lerp(0.0, 7.0, q),
                stretch=_lerp(1.0, 0.82, q),
                squash=_lerp(1.0, 1.15, q),
                wave=1.0,
                tail_wag=_lerp(0.0, -32.0, q),
                ear_droop=_lerp(8.0, 5.0, q),
                ear_sweep=_lerp(0.0, -12.0, q),
                eye_open=1.0,
            )
        if u < 0.62:
            q = _smooth((u - 0.24) / 0.38)
            return Pose(
                center=(_lerp(55.0, 60.0, q), _lerp(75.0, 66.0, q)),
                angle=_lerp(7.0, -8.0, q),
                stretch=_lerp(0.84, 1.15, q),
                squash=_lerp(1.13, 0.91, q),
                wave=1.8,
                wave_phase=q * math.pi,
                head_lift=_lerp(0.0, -3.5, q),
                head_reach=_lerp(0.0, 4.0, q),
                tail_wag=_lerp(-32.0, 18.0, q),
                ear_droop=4.0,
                ear_sweep=_lerp(-12.0, -24.0, q),
                eye_open=1.0,
                pupil_shift=2.0,
                mouth_open=_lerp(0.0, 1.0, q),
                tongue=_lerp(0.0, 0.55, q),
                near_front_lift=5.0,
                near_rear_lift=3.0,
                far_front_lift=4.0,
                far_rear_lift=2.0,
                frill_spread=1.18,
                impact=_pulse(u, 0.34, 0.52, 0.72),
            )
        q = _smooth((u - 0.62) / 0.38)
        return Pose(
            center=(_lerp(60.0, 64.0, q), _lerp(66.0, 71.0, q)),
            angle=_lerp(-8.0, 0.0, q),
            stretch=_lerp(1.15, 1.0, q),
            squash=_lerp(0.91, 1.0, q),
            wave=1.0 * (1.0 - q),
            head_lift=_lerp(-3.5, 0.0, q),
            head_reach=_lerp(4.0, 0.0, q),
            tail_wag=_lerp(18.0, 0.0, q),
            ear_droop=_lerp(4.0, 8.0, q),
            ear_sweep=_lerp(-24.0, 0.0, q),
            eye_open=1.0,
            mouth_open=_lerp(1.0, 0.0, q),
            tongue=_lerp(0.55, 0.0, q),
            frill_spread=_lerp(1.18, 1.0, q),
            impact=_pulse(u, 0.50, 0.62, 0.78),
        )

    if animation == "taunt":
        howl = max(0.0, math.sin(cyc - 0.45))
        return Pose(
            center=(63.0, 72.0 + 1.0 * c),
            angle=-4.0 - 5.0 * howl,
            stretch=1.0 + 0.02 * c,
            squash=1.0 - 0.02 * c,
            wave=0.8,
            wave_phase=cyc,
            head_lift=-3.0 - 5.0 * howl,
            head_reach=1.0,
            tail_wag=24.0 * math.sin(cyc * 2.0),
            ear_droop=6.0 + 2.0 * c,
            ear_sweep=5.0 * s,
            eye_open=0.85 + 0.15 * c,
            pupil_shift=-0.5,
            mouth_open=0.15 + 0.72 * howl,
            tongue=0.15 * howl,
            near_front_lift=2.0 * howl,
            frill_spread=1.0 + 0.12 * howl,
        )

    if animation == "wall_walk":
        return Pose(
            center=(65.0 + 1.6 * abs(s), 64.0),
            angle=-90.0 + 2.0 * s,
            stretch=0.93 + 0.03 * c,
            squash=0.94,
            wave=2.4,
            wave_phase=cyc,
            head_lift=-0.8 * abs(s),
            tail_wag=14.0 * math.sin(cyc + 0.4),
            ear_droop=13.0,
            ear_sweep=-3.0 * s,
            eye_open=1.0,
            pupil_shift=0.8,
            near_front_lift=max(0.0, s) * 4.0,
            near_rear_lift=max(0.0, -s) * 4.0,
            far_front_lift=max(0.0, -s) * 2.6,
            far_rear_lift=max(0.0, s) * 2.6,
            frill_spread=0.92,
        )

    if animation == "ceiling_walk":
        return Pose(
            center=(64.0, 49.0 + 1.2 * abs(s)),
            angle=180.0 + 2.0 * s,
            stretch=0.96 + 0.03 * c,
            squash=0.94,
            wave=2.4,
            wave_phase=cyc,
            tail_wag=15.0 * math.sin(cyc - 0.3),
            ear_droop=17.0,
            ear_sweep=-3.0 * s,
            eye_open=1.0,
            pupil_shift=0.7,
            near_front_lift=max(0.0, s) * 3.6,
            near_rear_lift=max(0.0, -s) * 3.6,
            far_front_lift=max(0.0, -s) * 2.4,
            far_rear_lift=max(0.0, s) * 2.4,
            frill_spread=0.88,
        )

    if animation == "hurt":
        hit = math.sin(math.pi * u)
        shake = -1.0 if frame_idx % 2 else 1.0
        return Pose(
            center=(64.0 - 5.0 * hit + shake * hit, 72.0 + 1.5 * hit),
            angle=8.0 * hit * shake,
            stretch=1.0 - 0.15 * hit,
            squash=1.0 + 0.16 * hit,
            wave=0.5,
            tail_wag=-18.0 * hit,
            ear_droop=5.0,
            ear_sweep=-18.0 * hit,
            eye_open=max(0.08, 1.0 - 1.35 * hit),
            mouth_open=0.25 * hit,
            near_front_lift=2.5 * hit,
            near_rear_lift=2.0 * hit,
            frill_spread=1.0 - 0.25 * hit,
            impact=hit,
        )

    if animation == "death":
        fall = _smooth(u)
        flatten = _smooth(max(0.0, (u - 0.36) / 0.64))
        return Pose(
            center=(64.0 - 5.0 * fall, 71.0 + 18.0 * flatten),
            angle=18.0 * fall,
            stretch=1.0 + 0.18 * flatten,
            squash=1.0 - 0.52 * flatten,
            wave=(1.0 - flatten) * 0.6,
            head_lift=2.0 * flatten,
            head_reach=-2.0 * flatten,
            tail_wag=-22.0 * fall,
            ear_droop=10.0 + 10.0 * flatten,
            ear_sweep=-12.0 * fall,
            eye_open=max(0.0, 1.0 - 2.4 * fall),
            mouth_open=0.12 * (1.0 - flatten),
            near_front_lift=1.5 * fall,
            near_rear_lift=1.0 * fall,
            frill_spread=max(0.45, 1.0 - 0.55 * flatten),
            death=flatten,
        )

    raise ValueError(f"unknown animation: {animation}")


def _local_to_world(point: Point, pose: Pose) -> Point:
    x = point[0] * pose.stretch
    y = point[1] * pose.squash
    a = math.radians(pose.angle)
    ca, sa = math.cos(a), math.sin(a)
    return (
        pose.center[0] + x * ca - y * sa,
        pose.center[1] + x * sa + y * ca,
    )


def _vector_to_world(vector: Point, pose: Pose) -> Point:
    x = vector[0] * pose.stretch
    y = vector[1] * pose.squash
    a = math.radians(pose.angle)
    ca, sa = math.cos(a), math.sin(a)
    return (x * ca - y * sa, x * sa + y * ca)


def _centerline(pose: Pose, count: int = 28) -> list[Point]:
    points: list[Point] = []
    for i in range(count):
        q = i / (count - 1)
        x = _lerp(-39.0, 27.0 + pose.head_reach * 0.42, q)
        taper = math.sin(math.pi * q)
        y = (
            math.sin(q * math.tau * 1.55 + pose.wave_phase)
            * pose.wave
            * (0.30 + 0.70 * taper)
        )
        y += pose.head_lift * _smooth(max(0.0, (q - 0.67) / 0.33))
        points.append((x, y))
    return points


def _radius(q: float, pose: Pose) -> float:
    # A true slug taper: narrow tail root, broad velvet mantle, then a
    # purposeful head lobe.  The old puppy slugs are long cylinders; this
    # pear-shaped envelope is a major part of the new variant's identity.
    tail_open = _smooth(min(1.0, q / 0.30))
    mantle = 8.0 + 7.4 * (math.sin(math.pi * q) ** 0.62)
    shoulder = 3.4 * math.exp(-((q - 0.70) ** 2) / 0.055)
    head = 5.8 * math.exp(-((q - 0.94) ** 2) / 0.018)
    r = (mantle + shoulder + head) * (0.42 + 0.58 * tail_open)
    return r * (1.0 - 0.28 * pose.death)


def _body_outline(pose: Pose, inset: float = 0.0) -> list[Point]:
    line = _centerline(pose)
    upper: list[Point] = []
    lower: list[Point] = []
    for i, (x, y) in enumerate(line):
        q = i / (len(line) - 1)
        prev = line[max(0, i - 1)]
        nxt = line[min(len(line) - 1, i + 1)]
        tx, ty = nxt[0] - prev[0], nxt[1] - prev[1]
        length = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / length, tx / length
        r = max(1.0, _radius(q, pose) - inset)
        upper.append(_local_to_world((x - nx * r, y - ny * r), pose))
        lower.append(_local_to_world((x + nx * r, y + ny * r), pose))
    return upper + list(reversed(lower))


def _layer_canvas() -> dict[str, Image.Image]:
    return {
        name: Image.new("RGBA", WORK_SIZE, (0, 0, 0, 0)) for name in LAYER_ORDER
    }


def _draw_poly(
    layer: Image.Image,
    points: Sequence[Point],
    fill: str | RGBA,
    outline: str | RGBA | None = None,
    width: float = 1.0,
) -> None:
    d = ImageDraw.Draw(layer, "RGBA")
    fill_rgba = _rgba(fill) if isinstance(fill, str) else fill
    outline_rgba = _rgba(outline) if isinstance(outline, str) else outline
    p = _pts(points)
    d.polygon(p, fill=fill_rgba)
    if outline_rgba is not None:
        d.line(p + [p[0]], fill=outline_rgba, width=_s(width), joint="curve")


def _draw_line(
    layer: Image.Image,
    points: Sequence[Point],
    fill: str | RGBA,
    width: float,
) -> None:
    d = ImageDraw.Draw(layer, "RGBA")
    rgba = _rgba(fill) if isinstance(fill, str) else fill
    d.line(_pts(points), fill=rgba, width=_s(width), joint="curve")


def _draw_ellipse(
    layer: Image.Image,
    center: Point,
    rx: float,
    ry: float,
    angle: float,
    fill: str | RGBA,
    outline: str | RGBA | None = None,
    width: float = 1.0,
) -> None:
    _draw_poly(layer, _ellipse_points(center, rx, ry, angle), fill, outline, width)


def _ear_shape(pose: Pose, near: bool) -> tuple[list[Point], list[Point], Point, Point]:
    base_local = (15.5 if not near else 20.5, -12.0 if not near else -11.0)
    base = _local_to_world(base_local, pose)
    back = _vector_to_world((-13.0 - pose.ear_sweep * 0.18, -6.5), pose)
    side = _vector_to_world((-3.0, 2.0), pose)
    # Gravity remains screen-down even when the animal is on a wall/ceiling.
    tip = (
        base[0] + back[0] + side[0],
        base[1] + back[1] + side[1] + pose.ear_droop * (1.0 if near else 0.88),
    )
    width = 7.0 if near else 6.2
    dx, dy = tip[0] - base[0], tip[1] - base[1]
    length = math.hypot(dx, dy) or 1.0
    px, py = -dy / length, dx / length
    left0 = (base[0] + px * width * 0.45, base[1] + py * width * 0.45)
    right0 = (base[0] - px * width * 0.45, base[1] - py * width * 0.45)
    left1 = (tip[0] + px * width * 0.10, tip[1] + py * width * 0.10)
    right1 = (tip[0] - px * width * 0.10, tip[1] - py * width * 0.10)
    c1 = (base[0] + dx * 0.35 + px * width, base[1] + dy * 0.35 + py * width)
    c2 = (tip[0] - dx * 0.22 + px * width * 0.55, tip[1] - dy * 0.22 + py * width * 0.55)
    c3 = (tip[0] - dx * 0.22 - px * width * 0.55, tip[1] - dy * 0.22 - py * width * 0.55)
    c4 = (base[0] + dx * 0.35 - px * width, base[1] + dy * 0.35 - py * width)
    outer = _bezier(left0, c1, c2, left1, 12) + _bezier(
        right1, c3, c4, right0, 12
    )
    inner_base = (base[0] + dx * 0.16, base[1] + dy * 0.16)
    inner_tip = (tip[0] - dx * 0.13, tip[1] - dy * 0.13)
    inner = _bezier(
        (inner_base[0] + px * width * 0.22, inner_base[1] + py * width * 0.22),
        (base[0] + dx * 0.45 + px * width * 0.42, base[1] + dy * 0.45 + py * width * 0.42),
        (tip[0] - dx * 0.24 + px * width * 0.18, tip[1] - dy * 0.24 + py * width * 0.18),
        inner_tip,
        12,
    ) + _bezier(
        inner_tip,
        (tip[0] - dx * 0.24 - px * width * 0.18, tip[1] - dy * 0.24 - py * width * 0.18),
        (base[0] + dx * 0.45 - px * width * 0.42, base[1] + dy * 0.45 - py * width * 0.42),
        (inner_base[0] - px * width * 0.22, inner_base[1] - py * width * 0.22),
        12,
    )
    return outer, inner, base, tip


def _tail_shape(pose: Pose) -> list[Point]:
    root = _local_to_world((-37.0, -1.0), pose)
    back = _vector_to_world((-11.0, -1.0), pose)
    up = _vector_to_world((0.0, -7.0), pose)
    wag = math.radians(pose.tail_wag)
    vx = back[0] * math.cos(wag) - back[1] * math.sin(wag)
    vy = back[0] * math.sin(wag) + back[1] * math.cos(wag)
    tip = (root[0] + vx + up[0] * 0.45, root[1] + vy + up[1] * 0.45)
    dx, dy = tip[0] - root[0], tip[1] - root[1]
    length = math.hypot(dx, dy) or 1.0
    px, py = -dy / length, dx / length
    width = 6.4 * (1.0 - 0.35 * pose.death)
    return _bezier(
        (root[0] + px * width, root[1] + py * width),
        (root[0] + dx * 0.45 + px * width * 1.1, root[1] + dy * 0.45 + py * width * 1.1),
        (tip[0] - dx * 0.18 + px * width * 0.45, tip[1] - dy * 0.18 + py * width * 0.45),
        tip,
        12,
    ) + _bezier(
        tip,
        (tip[0] - dx * 0.18 - px * width * 0.45, tip[1] - dy * 0.18 - py * width * 0.45),
        (root[0] + dx * 0.45 - px * width * 1.1, root[1] + dy * 0.45 - py * width * 1.1),
        (root[0] - px * width, root[1] - py * width),
        12,
    )


def _lobe_shape(pose: Pose, x: float, lift: float, near: bool) -> list[Point]:
    base = _local_to_world((x, 10.0 - lift * 0.18), pose)
    down = _vector_to_world((0.0, 8.0 - lift), pose)
    fore = _vector_to_world((6.5 if x > 0 else -5.5, 1.0), pose)
    tip = (base[0] + down[0] + fore[0], base[1] + down[1] + fore[1])
    width = 5.6 if near else 4.8
    dx, dy = tip[0] - base[0], tip[1] - base[1]
    length = math.hypot(dx, dy) or 1.0
    px, py = -dy / length, dx / length
    return _bezier(
        (base[0] + px * width, base[1] + py * width),
        (base[0] + dx * 0.35 + px * width * 1.1, base[1] + dy * 0.35 + py * width * 1.1),
        (tip[0] - dx * 0.18 + px * width * 0.5, tip[1] - dy * 0.18 + py * width * 0.5),
        tip,
        10,
    ) + _bezier(
        tip,
        (tip[0] - dx * 0.18 - px * width * 0.5, tip[1] - dy * 0.18 - py * width * 0.5),
        (base[0] + dx * 0.35 - px * width * 1.1, base[1] + dy * 0.35 - py * width * 1.1),
        (base[0] - px * width, base[1] - py * width),
        10,
    )


def _draw_motion(layers: Mapping[str, Image.Image], pose: Pose, animation: str) -> None:
    if animation == "walk":
        # Small body-relative wake ticks communicate propulsion without a
        # ground shadow or detached speed cloud.
        phase = pose.wave_phase
        for i in range(3):
            alpha = 120 - i * 26
            x0 = 30.0 - i * 6.0 + math.sin(phase + i) * 1.2
            y0 = 82.0 + i * 2.0
            _draw_line(
                layers["motion_back"],
                [(x0, y0), (x0 - 4.5, y0 + 0.8)],
                _rgba(MOTION, alpha),
                1.2,
            )
    if animation == "slash" and pose.impact > 0.05:
        head = _local_to_world((43.0 + pose.head_reach * 0.45, -1.0), pose)
        for i, offset in enumerate((-8.0, 0.0, 8.0)):
            start = (head[0] + 4.0, head[1] + offset * 0.45)
            end = (head[0] + 8.0 + pose.impact * 3.0, head[1] + offset)
            _draw_line(
                layers["motion_front"],
                [start, end],
                _rgba(MOTION, int(110 + 90 * pose.impact - i * 12)),
                1.4 + 0.45 * pose.impact,
            )


def _draw_tail_and_ears(layers: Mapping[str, Image.Image], pose: Pose) -> None:
    _draw_poly(layers["tail"], _tail_shape(pose), BODY_DARK, OUTLINE, 1.5)
    far_outer, far_inner, _, _ = _ear_shape(pose, near=False)
    _draw_poly(layers["far_ear"], far_outer, EAR_OUTER, OUTLINE, 1.4)
    _draw_poly(layers["far_ear"], far_inner, _rgba(EAR_INNER, 205), None)
    near_outer, near_inner, _, _ = _ear_shape(pose, near=True)
    _draw_poly(layers["near_ear"], near_outer, EAR_OUTER, OUTLINE, 1.5)
    _draw_poly(layers["near_ear"], near_inner, EAR_INNER, None)
    if pose.death < 0.8:
        gleam = near_inner[: max(3, len(near_inner) // 3)]
        _draw_line(layers["near_ear"], gleam, _rgba(EAR_GLEAM, 180), 1.0)


def _draw_lobes(layers: Mapping[str, Image.Image], pose: Pose) -> None:
    far_specs = [(-17.0, pose.far_rear_lift), (14.0, pose.far_front_lift)]
    near_specs = [(-11.0, pose.near_rear_lift), (21.0, pose.near_front_lift)]
    for x, lift in far_specs:
        shape = _lobe_shape(pose, x, lift, near=False)
        _draw_poly(layers["far_lobes"], shape, BODY_DARK, OUTLINE, 1.2)
    for x, lift in near_specs:
        shape = _lobe_shape(pose, x, lift, near=True)
        _draw_poly(layers["near_lobes"], shape, BODY_MID, OUTLINE, 1.35)
        # Paw-pad rosette: intrinsic anatomy, not a carried decoration.
        tip = shape[len(shape) // 2 - 1]
        _draw_ellipse(
            layers["details"],
            tip,
            2.4,
            1.7,
            pose.angle,
            PAD,
            OUTLINE,
            0.75,
        )


def _draw_body(layers: Mapping[str, Image.Image], pose: Pose) -> None:
    body = _body_outline(pose)
    _draw_poly(layers["body"], body, BODY_MID, OUTLINE, 1.8)

    inset = _body_outline(pose, inset=3.0)
    _draw_poly(layers["body"], inset, BODY_LIGHT, None)

    # Dorsal gleam follows the creature's own axis and survives wall/ceiling
    # rotation without becoming a fake lighting shadow.
    gleam_local = _bezier(
        (-27.0, -7.0),
        (-10.0, -14.5),
        (11.0, -16.0 + pose.head_lift * 0.35),
        (27.0 + pose.head_reach * 0.25, -10.0 + pose.head_lift * 0.7),
        24,
    )
    _draw_line(
        layers["body"],
        [_local_to_world(p, pose) for p in gleam_local],
        _rgba(BODY_GLEAM, 175),
        2.0,
    )

    # Ventral foot / belly ribbon.  It is a solid anatomical band, never a
    # detached ground ellipse.
    lower_local = _bezier(
        (-30.0, 8.0),
        (-12.0, 16.0),
        (13.0, 16.5),
        (31.0 + pose.head_reach * 0.30, 8.0 + pose.head_lift * 0.2),
        28,
    )
    upper_local = _bezier(
        (31.0 + pose.head_reach * 0.30, 4.0 + pose.head_lift * 0.2),
        (12.0, 10.5),
        (-12.0, 10.0),
        (-30.0, 5.0),
        28,
    )
    belly = [_local_to_world(p, pose) for p in lower_local + upper_local]
    _draw_poly(layers["belly"], belly, BELLY, OUTLINE, 1.15)
    belly_gleam = _bezier((-20.0, 9.0), (-7.0, 13.0), (9.0, 13.0), (22.0, 8.5), 18)
    _draw_line(
        layers["belly"],
        [_local_to_world(p, pose) for p in belly_gleam],
        _rgba(BELLY_LIGHT, 190),
        1.2,
    )


def _draw_dorsal(layers: Mapping[str, Image.Image], pose: Pose) -> None:
    for i, x in enumerate((-18.0, -3.0, 12.0)):
        base = _local_to_world((x, -11.5), pose)
        up = _vector_to_world((0.0, -7.0 * pose.frill_spread), pose)
        side = _vector_to_world((4.2, 0.0), pose)
        tip = (base[0] + up[0], base[1] + up[1])
        leaf = _bezier(
            (base[0] - side[0], base[1] - side[1]),
            (base[0] - side[0] * 1.15 + up[0] * 0.45, base[1] - side[1] * 1.15 + up[1] * 0.45),
            (tip[0] - side[0] * 0.35, tip[1] - side[1] * 0.35),
            tip,
            8,
        ) + _bezier(
            tip,
            (tip[0] + side[0] * 0.35, tip[1] + side[1] * 0.35),
            (base[0] + side[0] * 1.15 + up[0] * 0.45, base[1] + side[1] * 1.15 + up[1] * 0.45),
            (base[0] + side[0], base[1] + side[1]),
            8,
        )
        _draw_poly(layers["dorsal"], leaf, FRILL, OUTLINE, 1.1)
        mid = (
            (base[0] + tip[0]) * 0.5,
            (base[1] + tip[1]) * 0.5,
        )
        _draw_line(
            layers["dorsal"],
            [base, mid, tip],
            _rgba(FRILL_LIGHT, 210 - i * 16),
            0.85,
        )


def _draw_face(layers: Mapping[str, Image.Image], pose: Pose) -> None:
    head_center = _local_to_world((29.0 + pose.head_reach * 0.42, -1.5 + pose.head_lift), pose)
    head_angle = pose.angle - 2.0
    # The head overlaps the continuous mantle with the same palette, so it reads
    # as one body rather than a dog-face sticker.
    _draw_ellipse(
        layers["face"],
        head_center,
        18.5 * pose.stretch,
        15.5 * pose.squash,
        head_angle,
        BODY_LIGHT,
        OUTLINE,
        1.55,
    )

    muzzle_center = _local_to_world((41.0 + pose.head_reach * 0.72, 3.0 + pose.head_lift), pose)
    if pose.mouth_open < 0.08:
        _draw_ellipse(
            layers["face"],
            muzzle_center,
            10.8,
            7.2,
            pose.angle,
            MUZZLE,
            OUTLINE,
            1.25,
        )
    else:
        jaw_gap = 5.0 * pose.mouth_open
        upper = _local_to_world((41.5 + pose.head_reach * 0.72, 0.0 + pose.head_lift), pose)
        lower = _local_to_world((40.5 + pose.head_reach * 0.68, 5.0 + jaw_gap + pose.head_lift), pose)
        _draw_ellipse(layers["face"], upper, 10.7, 5.4, pose.angle - 4.0, MUZZLE, OUTLINE, 1.2)
        _draw_ellipse(layers["face"], lower, 9.7, 4.8, pose.angle + 9.0, MUZZLE, OUTLINE, 1.2)
        mouth_center = _local_to_world((44.0 + pose.head_reach * 0.75, 5.0 + jaw_gap * 0.45 + pose.head_lift), pose)
        _draw_ellipse(
            layers["face"],
            mouth_center,
            7.2,
            3.0 + jaw_gap * 0.42,
            pose.angle,
            NOSE,
            OUTLINE,
            0.9,
        )
        if pose.tongue > 0.02:
            tongue_center = _local_to_world((46.0 + pose.head_reach * 0.75, 7.0 + jaw_gap * 0.48 + pose.head_lift), pose)
            _draw_ellipse(
                layers["details"],
                tongue_center,
                4.0,
                1.5 + 2.0 * pose.tongue,
                pose.angle + 5.0,
                TONGUE,
                OUTLINE,
                0.8,
            )
        tooth = _local_to_world((47.0 + pose.head_reach * 0.75, 2.8 + pose.head_lift), pose)
        tooth_vec = _vector_to_world((0.0, 4.1), pose)
        tooth_side = _vector_to_world((2.1, 0.0), pose)
        _draw_poly(
            layers["details"],
            [
                (tooth[0] - tooth_side[0], tooth[1] - tooth_side[1]),
                (tooth[0] + tooth_side[0], tooth[1] + tooth_side[1]),
                (tooth[0] + tooth_vec[0], tooth[1] + tooth_vec[1]),
            ],
            TOOTH,
            OUTLINE,
            0.7,
        )

    # Two eyes in a clear three-quarter face.  The far eye is smaller but never
    # omitted, preventing the frontal-cyclops failure seen in other sprites.
    far_eye = _local_to_world((29.0 + pose.head_reach * 0.45, -6.0 + pose.head_lift), pose)
    near_eye = _local_to_world((35.5 + pose.head_reach * 0.55, -5.2 + pose.head_lift), pose)
    for center, rx, ry, shift_scale in (
        (far_eye, 3.6, 4.3, 0.65),
        (near_eye, 4.5, 5.1, 1.0),
    ):
        if pose.eye_open <= 0.12:
            axis = _vector_to_world((3.0, 0.0), pose)
            _draw_line(
                layers["details"],
                [
                    (center[0] - axis[0], center[1] - axis[1]),
                    (center[0] + axis[0], center[1] + axis[1]),
                ],
                EYE_PUPIL,
                1.2,
            )
            continue
        _draw_ellipse(
            layers["details"],
            center,
            rx,
            max(0.8, ry * pose.eye_open),
            pose.angle,
            EYE_WHITE,
            OUTLINE,
            0.9,
        )
        shift = _vector_to_world((pose.pupil_shift * shift_scale, 0.2), pose)
        iris = (center[0] + shift[0], center[1] + shift[1])
        _draw_ellipse(layers["details"], iris, rx * 0.56, ry * 0.58, pose.angle, EYE_IRIS, None)
        _draw_ellipse(layers["details"], iris, rx * 0.28, ry * 0.40, pose.angle, EYE_PUPIL, None)
        catch = (iris[0] - 1.0, iris[1] - 1.3)
        _draw_ellipse(layers["details"], catch, 0.75, 0.75, 0.0, EYE_WHITE, None)

    nose = _local_to_world((50.0 + pose.head_reach * 0.78, 1.4 + pose.head_lift), pose)
    _draw_ellipse(layers["details"], nose, 3.5, 3.0, pose.angle, NOSE, OUTLINE, 0.8)
    nose_glint = _local_to_world((49.0 + pose.head_reach * 0.78, 0.2 + pose.head_lift), pose)
    _draw_ellipse(layers["details"], nose_glint, 0.8, 0.6, pose.angle, BODY_GLEAM, None)

    if pose.mouth_open < 0.08:
        mouth_a = _local_to_world((44.0 + pose.head_reach * 0.72, 6.0 + pose.head_lift), pose)
        mouth_b = _local_to_world((49.0 + pose.head_reach * 0.75, 5.0 + pose.head_lift), pose)
        _draw_line(layers["details"], [mouth_a, mouth_b], OUTLINE, 1.1)

    # Three small cheek follicles keep the muzzle organic without reading as
    # detached particles or a decorative prop.
    for i in range(3):
        follicle = _local_to_world((43.0 + i * 2.3 + pose.head_reach * 0.7, 2.0 + (i % 2) * 1.5 + pose.head_lift), pose)
        _draw_ellipse(layers["details"], follicle, 0.55, 0.55, 0.0, EAR_INNER, None)


def _compose(layers: Mapping[str, Image.Image]) -> Image.Image:
    canvas = Image.new("RGBA", WORK_SIZE, (0, 0, 0, 0))
    for name in sorted(LAYER_ORDER, key=LAYER_ORDER.__getitem__):
        canvas = Image.alpha_composite(canvas, layers[name])
    # Preserve a two-pixel sampling gutter in the logical frame.  This is a
    # uniform design-scale choice, not a per-pose shrink hack.
    art = canvas.resize((124, 124), Image.Resampling.LANCZOS)
    frame = Image.new("RGBA", FRAME_SIZE, (0, 0, 0, 0))
    frame.alpha_composite(art, (2, 2))
    return frame


def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    pose = _pose_for(animation, frame_idx, nframes)
    layers = _layer_canvas()
    _draw_motion(layers, pose, animation)
    _draw_tail_and_ears(layers, pose)
    _draw_lobes(layers, pose)
    _draw_body(layers, pose)
    _draw_dorsal(layers, pose)
    _draw_face(layers, pose)
    return _compose(layers)


def render_canonical(out_dir: str | Path, **opts) -> Path:
    del opts
    return write_canonical(
        TARGET_NAME,
        ROWS,
        render_frame,
        Path(out_dir),
        frame_size=FRAME_SIZE,
        crop_margin=4,
    )


def render(out_dir: str | Path, **opts) -> list[Path]:
    del opts
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=Path(out_dir),
        frame_size=FRAME_SIZE,
        label_width=142,
        auto_crop=True,
        crop_margin=4,
        actor_metadata=ACTOR_METADATA,
        animation_key_map={
            "idle": "rest",
            "walk": "walk",
            "slash": "side_sweep",
            "hurt": "hit",
            "death": "death",
        },
        trim=False,
        attack_hitboxes={
            "side_sweep": {
                "bbox": {"x": 73, "y": 44, "w": 47, "h": 39},
                "source": "puppy_slug_velvet.bite",
            }
        },
    )
    return [
        outputs["canonical"],
        outputs["canonical_transparent"],
        outputs["spritesheet"],
        outputs["yaml"],
        outputs["ron"],
        outputs["actor"],
        outputs["preview"],
    ]


__all__ = [
    "ACTOR_METADATA",
    "CHARACTER_LINEAGE",
    "FRAME_SIZE",
    "LAYER_ORDER",
    "ROWS",
    "SHEET_FILES",
    "TARGET_NAME",
    "render",
    "render_canonical",
    "render_frame",
]
