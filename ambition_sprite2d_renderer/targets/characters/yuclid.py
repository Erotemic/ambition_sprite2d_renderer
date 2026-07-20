"""Procedural sprite target for Yuclid, the Euclid parody boss.

Yuclid is a severe geometer who regards portals as an affront: they skip the
clean path, they bend the plane, and worst of all they let people arrive
without proving how they got there.  He presents as a high-status boss rather
than a generic professor: laurel-bound curls, a squared philosopher's beard,
a white marble robe layered with a cobalt mantle, geometric gold trim, and an
imposing lecture-hall posture.

The combat kit turns Euclidean preferences into movement and attacks instead of
held props:

* ``straightedge_slam`` cleaves the space with a flawless golden line;
* ``parallel_banish`` drives out distortions using rigid line-barrages;
* ``postulate_burst`` erupts as triangles, squares, and proof marks;
* ``compass_orbit`` cages foes inside pure circles and arcs;
* ``portal_denial`` condemns a portal inside a barred forbidden diagram.

Everything is authored directly in Python/Pillow.  There are no generated-image
inputs, no drop shadows, and no floor ellipses.  The painter order is legs,
robe, arms, then head, keeping the face and silhouette authoritative.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, replace
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw

from ...authoring.portrait import (
    FaceGuide,
    PortraitClip,
    render_framed_portrait,
    write_portrait_sheet,
)
from ...authoring.sheet_build import build_sheet, write_canonical

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "yuclid"
FRAME_W = 144
FRAME_H = 144
SUPER = 4

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 148),
    ("walk", 8, 104),
    ("run", 8, 76),
    ("crouch", 6, 92),
    ("jump", 6, 84),
    ("fall", 6, 84),
    ("land_hard", 6, 72),
    ("talk", 8, 104),
    ("interact", 8, 92),
    ("jab", 5, 58),
    ("attack_up", 6, 64),
    ("attack_down", 6, 64),
    ("air_forward", 6, 60),
    ("block", 8, 82),
    ("hit", 5, 86),
    ("death", 10, 108),
    ("taunt", 8, 96),
    ("celebrate", 8, 90),
    ("straightedge_slam", 8, 70),
    ("parallel_banish", 8, 76),
    ("postulate_burst", 10, 74),
    ("compass_orbit", 10, 78),
    ("portal_denial", 12, 76),
]

ACTOR_METADATA = {
    "actor": {"character_id": "npc_yuclid", "display_name": "Yuclid"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": [
            "boss",
            "story",
            "humanoid",
            "mathematician",
            "geometer",
            "anti_portal",
            "lecture_duelist",
        ],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": True,
            "climb": None,
            "fly": None,
            "swim": None,
            "crawl": True,
            "use_lifts": True,
            "door_access": ["boss", "public"],
        },
        "interactions": {
            "talk": True,
            "trade": None,
            "carry": None,
            "open_doors": ["boss", "public"],
        },
    },
    "brain": {"default_preset": "boss_guard"},
    "actions": {"default_preset": "boss_combat"},
    "visual": {
        "default_pose": "idle",
        "portrait": {
            "face_guide": {
                "center": {"x": 72.0, "y": 28.5},
                "size": {"width": 28.0, "height": 31.0},
                "source_size": {"width": FRAME_W, "height": FRAME_H},
            }
        },
    },
    "tags": [
        "boss",
        "story",
        "humanoid",
        "mathematician",
        "geometer",
        "anti_portal",
        "lecture_duelist",
    ],
    "sockets": {
        "head": {"source": "explicit.profile.humanoid", "point": {"x": 72.0, "y": 29.0}},
        "chest": {"source": "explicit.profile.humanoid", "point": {"x": 72.0, "y": 69.0}},
        "hand_l": {"source": "explicit.profile.humanoid", "point": {"x": 48.0, "y": 84.0}},
        "hand_r": {"source": "explicit.profile.humanoid", "point": {"x": 95.0, "y": 82.0}},
        "speech_bubble": {"source": "explicit.profile.humanoid", "point": {"x": 72.0, "y": 7.0}},
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "traversal.jump": {"animation": "jump", "events": []},
        "traversal.fall": {"animation": "fall", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "action.melee.primary": {"animation": "straightedge_slam", "events": []},
        "action.ranged.primary": {"animation": "parallel_banish", "events": []},
        "action.special.primary": {"animation": "portal_denial", "events": []},
        "action.special.secondary": {"animation": "compass_orbit", "events": []},
        "action.defense.block": {"animation": "block", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
    },
}

OUTLINE = (15, 19, 24, 255)
OUTLINE_SOFT = (39, 47, 55, 255)
SKIN = (189, 151, 118, 255)
SKIN_LIGHT = (223, 184, 148, 255)
SKIN_SHADE = (149, 109, 82, 255)
SKIN_DEEP = (112, 77, 57, 255)
HAIR = (42, 44, 54, 255)
HAIR_LIGHT = (76, 81, 95, 255)
HAIR_SHADE = (27, 28, 34, 255)
LAUREL = (140, 175, 92, 255)
LAUREL_LIGHT = (193, 216, 136, 255)
ROBE = (244, 239, 226, 255)
ROBE_SHADE = (212, 205, 191, 255)
ROBE_DEEP = (175, 166, 152, 255)
MANTLE = (50, 74, 133, 255)
MANTLE_LIGHT = (91, 119, 189, 255)
MANTLE_DEEP = (31, 46, 95, 255)
BELT = (152, 97, 65, 255)
BELT_LIGHT = (188, 132, 86, 255)
GOLD = (239, 191, 78, 255)
GOLD_LIGHT = (255, 225, 130, 255)
GOLD_DEEP = (172, 115, 36, 255)
SANDAL = (121, 86, 61, 255)
SANDAL_LIGHT = (160, 121, 91, 255)
EYE = (29, 25, 24, 255)
EYE_WHITE = (244, 239, 232, 255)
MOUTH = (112, 59, 51, 255)
GEO_CYAN = (97, 216, 224, 255)
GEO_CYAN_SOFT = (97, 216, 224, 92)
GEO_VIOLET = (174, 112, 226, 235)
GEO_VIOLET_SOFT = (174, 112, 226, 80)
GEO_RED = (224, 100, 96, 255)
GEO_RED_SOFT = (224, 100, 96, 84)
MARBLE = (225, 220, 213, 255)


@dataclass(frozen=True)
class Pose:
    head: Point
    neck: Point
    near_shoulder: Point
    far_shoulder: Point
    near_elbow: Point
    far_elbow: Point
    near_hand: Point
    far_hand: Point
    near_hip: Point
    far_hip: Point
    near_knee: Point
    far_knee: Point
    near_ankle: Point
    far_ankle: Point
    near_hand_mode: str = "open"
    far_hand_mode: str = "open"
    vertical: float = 0.0
    lean: float = 0.0
    robe_spread: float = 0.0
    cloak_sweep: float = 0.0
    mouth: float = 0.0
    brow: float = 0.0
    blink: float = 0.0
    eye_narrow: float = 0.0
    beard_sway: float = 0.0
    aura: float = 0.0
    straightedge: float = 0.0
    parallel: float = 0.0
    burst: float = 0.0
    orbit: float = 0.0
    denial: float = 0.0
    disdain: float = 0.0
    block: float = 0.0
    hurt: float = 0.0
    defeat: float = 0.0
    halo: float = 0.0
    glyphs: float = 0.0


def _s(value: float) -> int:
    return max(1, int(round(value * SUPER)))


def _pt(point: Point) -> Tuple[int, int]:
    return (int(round(point[0] * SUPER)), int(round(point[1] * SUPER)))


def _bbox(center: Point, rx: float, ry: float) -> Tuple[int, int, int, int]:
    return (
        int(round((center[0] - rx) * SUPER)),
        int(round((center[1] - ry) * SUPER)),
        int(round((center[0] + rx) * SUPER)),
        int(round((center[1] + ry) * SUPER)),
    )


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _smooth(value: float) -> float:
    value = _clamp01(value)
    return value * value * (3.0 - 2.0 * value)


def _pulse(value: float) -> float:
    return math.sin(_clamp01(value) * math.pi)


def _lerp(a: float, b: float, amount: float) -> float:
    return a + (b - a) * amount


def _lerp_point(a: Point, b: Point, amount: float) -> Point:
    return (_lerp(a[0], b[0], amount), _lerp(a[1], b[1], amount))


def _offset(point: Point, dx: float, dy: float) -> Point:
    return (point[0] + dx, point[1] + dy)


def _rotate(point: Point, origin: Point, degrees: float) -> Point:
    r = math.radians(degrees)
    c = math.cos(r)
    s = math.sin(r)
    x = point[0] - origin[0]
    y = point[1] - origin[1]
    return (origin[0] + x * c - y * s, origin[1] + x * s + y * c)


def _fade(color: RGBA, strength: float, alpha_scale: float = 1.0) -> RGBA:
    alpha = int(round(color[3] * _clamp01(strength) * alpha_scale))
    return (color[0], color[1], color[2], max(0, min(255, alpha)))


def _segment_quad(a: Point, b: Point, radius_a: float, radius_b: float) -> list[Point]:
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    length = math.hypot(dx, dy) or 1.0
    nx = -dy / length
    ny = dx / length
    return [
        (a[0] + nx * radius_a, a[1] + ny * radius_a),
        (b[0] + nx * radius_b, b[1] + ny * radius_b),
        (b[0] - nx * radius_b, b[1] - ny * radius_b),
        (a[0] - nx * radius_a, a[1] - ny * radius_a),
    ]


def _poly(draw: ImageDraw.ImageDraw, points: Sequence[Point], fill: RGBA | None, outline: RGBA | None = OUTLINE, width: float = 1.0) -> None:
    scaled = [_pt(point) for point in points]
    draw.polygon(scaled, fill=fill)
    if outline is not None and width > 0:
        draw.line(scaled + [scaled[0]], fill=outline, width=max(1, _s(width)), joint="curve")


def _line(draw: ImageDraw.ImageDraw, points: Sequence[Point], fill: RGBA, width: float) -> None:
    draw.line([_pt(point) for point in points], fill=fill, width=max(1, _s(width)), joint="curve")


def _disc(draw: ImageDraw.ImageDraw, center: Point, radius: float, fill: RGBA, outline: RGBA | None = OUTLINE, width: float = 1.0) -> None:
    draw.ellipse(_bbox(center, radius, radius), fill=fill, outline=outline, width=max(1, _s(width)) if outline else 0)


def _ellipse(draw: ImageDraw.ImageDraw, center: Point, rx: float, ry: float, fill: RGBA, outline: RGBA | None = OUTLINE, width: float = 1.0) -> None:
    draw.ellipse(_bbox(center, rx, ry), fill=fill, outline=outline, width=max(1, _s(width)) if outline else 0)


def _arc(draw: ImageDraw.ImageDraw, center: Point, rx: float, ry: float, start: float, end: float, fill: RGBA, width: float) -> None:
    draw.arc(_bbox(center, rx, ry), start=start, end=end, fill=fill, width=max(1, _s(width)))


def _capsule(draw: ImageDraw.ImageDraw, a: Point, b: Point, radius_a: float, radius_b: float, fill: RGBA, outline: RGBA = OUTLINE, width: float = 1.0) -> None:
    quad = _segment_quad(a, b, radius_a, radius_b)
    _poly(draw, quad, fill=fill, outline=outline, width=width)
    _disc(draw, a, radius_a, fill=fill, outline=outline, width=width)
    _disc(draw, b, radius_b, fill=fill, outline=outline, width=width)


def _leaf(draw: ImageDraw.ImageDraw, center: Point, angle: float, length: float, width: float, fill: RGBA) -> None:
    tip = _rotate((center[0], center[1] - length), center, angle)
    left = _rotate((center[0] - width, center[1] - length * 0.45), center, angle)
    right = _rotate((center[0] + width, center[1] - length * 0.45), center, angle)
    _poly(draw, [center, left, tip, right], fill=fill, outline=OUTLINE_SOFT, width=0.6)


def _make_base_pose() -> Pose:
    return Pose(
        head=(72.0, 29.0),
        neck=(72.0, 43.0),
        near_shoulder=(84.0, 55.0),
        far_shoulder=(59.0, 56.0),
        near_elbow=(92.0, 72.0),
        far_elbow=(50.0, 74.0),
        near_hand=(95.0, 89.0),
        far_hand=(45.0, 90.0),
        near_hip=(81.0, 84.0),
        far_hip=(64.0, 85.0),
        near_knee=(84.0, 103.0),
        far_knee=(63.0, 104.0),
        near_ankle=(86.0, 126.0),
        far_ankle=(61.0, 126.0),
        mouth=0.08,
        brow=0.15,
        eye_narrow=0.15,
    )


def _pose(animation: str, frame_idx: int, frame_count: int) -> Pose:
    base = _make_base_pose()
    t = frame_idx / max(1, frame_count)
    cyc = math.sin(t * math.tau)
    cyc2 = math.sin(t * math.tau + math.pi / 2.0)
    hop = max(0.0, cyc)

    pose = replace(
        base,
        vertical=cyc2 * 0.6,
        robe_spread=0.15 + 0.12 * abs(cyc),
        cloak_sweep=0.1 * cyc,
        beard_sway=0.08 * cyc,
        mouth=0.06,
    )

    def move_points(delta: dict[str, Point | float]):
        nonlocal pose
        values = {name: getattr(pose, name) for name in pose.__dataclass_fields__}
        for key, value in delta.items():
            if isinstance(value, tuple):
                values[key] = value
            elif isinstance(value, (int, float)):
                values[key] = float(value)
            else:
                values[key] = value
        pose = Pose(**values)

    # Baseline small vertical shift.
    v = pose.vertical
    move_points(
        {
            "head": _offset(pose.head, 0.0, v),
            "neck": _offset(pose.neck, 0.0, v),
            "near_shoulder": _offset(pose.near_shoulder, 0.0, v),
            "far_shoulder": _offset(pose.far_shoulder, 0.0, v),
            "near_elbow": _offset(pose.near_elbow, 0.0, v),
            "far_elbow": _offset(pose.far_elbow, 0.0, v),
            "near_hand": _offset(pose.near_hand, 0.0, v),
            "far_hand": _offset(pose.far_hand, 0.0, v),
            "near_hip": _offset(pose.near_hip, 0.0, v),
            "far_hip": _offset(pose.far_hip, 0.0, v),
            "near_knee": _offset(pose.near_knee, 0.0, v),
            "far_knee": _offset(pose.far_knee, 0.0, v),
            "near_ankle": _offset(pose.near_ankle, 0.0, v),
            "far_ankle": _offset(pose.far_ankle, 0.0, v),
        }
    )

    if animation in {"walk", "run"}:
        stride = 7.0 if animation == "walk" else 10.5
        lift = 3.5 if animation == "walk" else 6.0
        arm = 5.0 if animation == "walk" else 8.0
        forward = cyc
        move_points(
            {
                "near_knee": _offset(pose.near_knee, forward * stride * 0.42, -abs(forward) * lift),
                "far_knee": _offset(pose.far_knee, -forward * stride * 0.42, -abs(-forward) * lift),
                "near_ankle": _offset(pose.near_ankle, forward * stride, -max(0.0, forward) * lift),
                "far_ankle": _offset(pose.far_ankle, -forward * stride, -max(0.0, -forward) * lift),
                "near_elbow": _offset(pose.near_elbow, -forward * arm * 0.65, 0.6),
                "far_elbow": _offset(pose.far_elbow, forward * arm * 0.65, 0.6),
                "near_hand": _offset(pose.near_hand, -forward * arm, abs(forward) * 0.8),
                "far_hand": _offset(pose.far_hand, forward * arm, abs(forward) * 0.8),
                "robe_spread": 0.25 + 0.20 * abs(forward),
                "cloak_sweep": 0.25 * forward,
                "mouth": 0.02,
            }
        )
        if animation == "run":
            move_points(
                {
                    "head": _offset(pose.head, 2.0, 0.0),
                    "neck": _offset(pose.neck, 2.0, 0.0),
                    "near_shoulder": _offset(pose.near_shoulder, 1.8, 0.0),
                    "far_shoulder": _offset(pose.far_shoulder, 1.8, 0.0),
                    "near_hip": _offset(pose.near_hip, 1.2, 0.0),
                    "far_hip": _offset(pose.far_hip, 1.2, 0.0),
                    "brow": 0.28,
                }
            )
    elif animation == "crouch":
        squish = _smooth(frame_idx / max(1, frame_count - 1))
        move_points(
            {
                "head": _offset(pose.head, 0.0, 6.0 * squish),
                "neck": _offset(pose.neck, 0.0, 7.0 * squish),
                "near_shoulder": _offset(pose.near_shoulder, 0.5, 6.0 * squish),
                "far_shoulder": _offset(pose.far_shoulder, -0.5, 6.0 * squish),
                "near_hip": _offset(pose.near_hip, 0.0, 7.0 * squish),
                "far_hip": _offset(pose.far_hip, 0.0, 7.0 * squish),
                "near_knee": _offset(pose.near_knee, -2.0, 3.0 * squish),
                "far_knee": _offset(pose.far_knee, -1.0, 3.0 * squish),
                "near_ankle": _offset(pose.near_ankle, -5.0, 0.0),
                "far_ankle": _offset(pose.far_ankle, -3.0, 0.0),
                "near_elbow": _offset(pose.near_elbow, -3.0, 4.0 * squish),
                "far_elbow": _offset(pose.far_elbow, 2.0, 4.0 * squish),
                "near_hand": _offset(pose.near_hand, -6.0, 4.0 * squish),
                "far_hand": _offset(pose.far_hand, -2.0, 5.0 * squish),
                "robe_spread": 0.32,
                "mouth": 0.0,
            }
        )
    elif animation == "jump":
        phase = _pulse(t)
        move_points(
            {
                "head": _offset(pose.head, 0.0, -12.0 * phase),
                "neck": _offset(pose.neck, 0.0, -12.0 * phase),
                "near_shoulder": _offset(pose.near_shoulder, 0.0, -12.0 * phase),
                "far_shoulder": _offset(pose.far_shoulder, 0.0, -12.0 * phase),
                "near_elbow": _offset(pose.near_elbow, -2.0, -10.0 * phase),
                "far_elbow": _offset(pose.far_elbow, 1.5, -10.0 * phase),
                "near_hand": _offset(pose.near_hand, -2.0, -16.0 * phase),
                "far_hand": _offset(pose.far_hand, 1.0, -15.0 * phase),
                "near_hip": _offset(pose.near_hip, 0.0, -11.0 * phase),
                "far_hip": _offset(pose.far_hip, 0.0, -11.0 * phase),
                "near_knee": _offset(pose.near_knee, 3.0, -8.0 * phase),
                "far_knee": _offset(pose.far_knee, -1.0, -7.0 * phase),
                "near_ankle": _offset(pose.near_ankle, 8.0, -12.0 * phase),
                "far_ankle": _offset(pose.far_ankle, -5.0, -10.0 * phase),
                "robe_spread": 0.30 + 0.18 * phase,
                "cloak_sweep": 0.18,
                "mouth": 0.12,
            }
        )
    elif animation == "fall":
        s = frame_idx / max(1, frame_count - 1)
        move_points(
            {
                "head": _offset(pose.head, 1.0, 1.0),
                "neck": _offset(pose.neck, 1.0, 1.0),
                "near_elbow": _offset(pose.near_elbow, -3.0, -2.0),
                "far_elbow": _offset(pose.far_elbow, 4.0, -1.0),
                "near_hand": _offset(pose.near_hand, -4.0, -4.0 + s * 2.0),
                "far_hand": _offset(pose.far_hand, 5.0, -3.0 + s * 1.5),
                "near_knee": _offset(pose.near_knee, 4.0, -5.0),
                "far_knee": _offset(pose.far_knee, -3.0, -3.0),
                "near_ankle": _offset(pose.near_ankle, 7.0, -2.0),
                "far_ankle": _offset(pose.far_ankle, -6.0, -1.0),
                "robe_spread": 0.34,
                "mouth": 0.14,
                "brow": 0.26,
            }
        )
    elif animation == "land_hard":
        shock = _pulse(t)
        move_points(
            {
                "head": _offset(pose.head, 0.0, 7.0 * shock),
                "neck": _offset(pose.neck, 0.0, 7.0 * shock),
                "near_shoulder": _offset(pose.near_shoulder, 1.0, 7.5 * shock),
                "far_shoulder": _offset(pose.far_shoulder, -1.0, 7.5 * shock),
                "near_hip": _offset(pose.near_hip, 0.0, 9.0 * shock),
                "far_hip": _offset(pose.far_hip, 0.0, 9.0 * shock),
                "near_knee": _offset(pose.near_knee, -4.0, 2.0 * shock),
                "far_knee": _offset(pose.far_knee, -3.0, 2.0 * shock),
                "near_ankle": _offset(pose.near_ankle, -6.0, 0.0),
                "far_ankle": _offset(pose.far_ankle, -4.0, 0.0),
                "near_hand": _offset(pose.near_hand, -6.0, 7.0 * shock),
                "far_hand": _offset(pose.far_hand, -4.0, 7.0 * shock),
                "robe_spread": 0.38,
                "mouth": 0.06,
            }
        )
    elif animation == "talk":
        gesture = cyc
        move_points(
            {
                "near_elbow": _offset(pose.near_elbow, 3.0 * gesture, -2.5 * abs(gesture)),
                "near_hand": _offset(pose.near_hand, 6.0 * gesture, -5.0 * abs(gesture)),
                "far_elbow": _offset(pose.far_elbow, -1.0, -1.2),
                "far_hand": _offset(pose.far_hand, -1.0, -2.0),
                "mouth": 0.18 + 0.12 * abs(gesture),
                "brow": 0.22,
                "glyphs": 0.28 + 0.16 * abs(gesture),
                "near_hand_mode": "lecture",
            }
        )
    elif animation == "interact":
        sweep = _smooth(t)
        move_points(
            {
                "near_elbow": _lerp_point(pose.near_elbow, (97.0, 66.0), sweep),
                "near_hand": _lerp_point(pose.near_hand, (108.0, 57.0), sweep),
                "far_hand": _lerp_point(pose.far_hand, (52.0, 94.0), sweep),
                "mouth": 0.04,
                "brow": 0.18,
                "glyphs": 0.38,
                "near_hand_mode": "point",
            }
        )
    elif animation in {"jab", "attack_up", "attack_down", "air_forward"}:
        target = {
            "jab": ((112.0, 75.0), (100.0, 70.0)),
            "attack_up": ((100.0, 51.0), (91.0, 61.0)),
            "attack_down": ((106.0, 96.0), (94.0, 82.0)),
            "air_forward": ((113.0, 67.0), (100.0, 64.0)),
        }[animation]
        rush = _pulse(t)
        hand, elbow = target
        move_points(
            {
                "near_elbow": _lerp_point(pose.near_elbow, elbow, rush),
                "near_hand": _lerp_point(pose.near_hand, hand, rush),
                "far_elbow": _offset(pose.far_elbow, -3.0 * rush, 1.0),
                "far_hand": _offset(pose.far_hand, -4.0 * rush, 1.5),
                "straightedge": 0.7 * rush if animation != "attack_up" else 0.45 * rush,
                "robe_spread": 0.20 + 0.22 * rush,
                "brow": 0.34,
                "mouth": 0.04,
                "near_hand_mode": "blade",
            }
        )
        if animation == "air_forward":
            move_points(
                {
                    "head": _offset(pose.head, 2.0, -4.0),
                    "neck": _offset(pose.neck, 2.0, -4.0),
                    "near_ankle": _offset(pose.near_ankle, 3.0, -7.0),
                    "far_ankle": _offset(pose.far_ankle, -6.0, -5.0),
                }
            )
    elif animation == "block":
        phase = _pulse(t)
        move_points(
            {
                "near_elbow": _lerp_point(pose.near_elbow, (88.0, 67.0), phase),
                "near_hand": _lerp_point(pose.near_hand, (101.0, 62.0), phase),
                "far_elbow": _lerp_point(pose.far_elbow, (55.0, 73.0), phase),
                "far_hand": _lerp_point(pose.far_hand, (56.0, 60.0), phase),
                "block": 0.45 + 0.40 * phase,
                "brow": 0.30,
                "mouth": 0.0,
                "near_hand_mode": "block",
                "far_hand_mode": "block",
            }
        )
    elif animation == "hit":
        shock = _pulse(t)
        move_points(
            {
                "head": _offset(pose.head, -4.0 * shock, -1.0 * shock),
                "neck": _offset(pose.neck, -4.0 * shock, -1.0 * shock),
                "near_shoulder": _offset(pose.near_shoulder, -3.0 * shock, 1.0),
                "far_shoulder": _offset(pose.far_shoulder, -3.0 * shock, 1.0),
                "near_elbow": _offset(pose.near_elbow, -7.0 * shock, 2.0 * shock),
                "far_elbow": _offset(pose.far_elbow, -4.0 * shock, 2.0 * shock),
                "near_hand": _offset(pose.near_hand, -11.0 * shock, 4.0 * shock),
                "far_hand": _offset(pose.far_hand, -6.0 * shock, 4.0 * shock),
                "hurt": shock,
                "mouth": 0.16,
                "brow": 0.45,
            }
        )
    elif animation == "death":
        s = _smooth(t)
        move_points(
            {
                "head": _lerp_point(pose.head, (54.0, 109.0), s),
                "neck": _lerp_point(pose.neck, (61.0, 101.0), s),
                "near_shoulder": _lerp_point(pose.near_shoulder, (73.0, 100.0), s),
                "far_shoulder": _lerp_point(pose.far_shoulder, (56.0, 103.0), s),
                "near_elbow": _lerp_point(pose.near_elbow, (88.0, 109.0), s),
                "far_elbow": _lerp_point(pose.far_elbow, (43.0, 116.0), s),
                "near_hand": _lerp_point(pose.near_hand, (101.0, 118.0), s),
                "far_hand": _lerp_point(pose.far_hand, (30.0, 124.0), s),
                "near_hip": _lerp_point(pose.near_hip, (83.0, 104.0), s),
                "far_hip": _lerp_point(pose.far_hip, (66.0, 107.0), s),
                "near_knee": _lerp_point(pose.near_knee, (96.0, 119.0), s),
                "far_knee": _lerp_point(pose.far_knee, (70.0, 124.0), s),
                "near_ankle": _lerp_point(pose.near_ankle, (117.0, 129.0), s),
                "far_ankle": _lerp_point(pose.far_ankle, (77.0, 131.0), s),
                "defeat": s,
                "hurt": 0.35 + 0.5 * s,
                "robe_spread": 0.46,
                "mouth": 0.04,
                "blink": s,
            }
        )
    elif animation == "taunt":
        curl = cyc
        move_points(
            {
                "near_elbow": _offset(pose.near_elbow, 4.0 * curl, -4.0 * abs(curl)),
                "near_hand": _offset(pose.near_hand, 8.0 * curl, -8.0 * abs(curl)),
                "far_hand": _offset(pose.far_hand, -2.0, -2.0),
                "disdain": 0.40 + 0.35 * abs(curl),
                "brow": 0.38,
                "mouth": 0.03,
                "near_hand_mode": "dismiss",
                "glyphs": 0.24,
            }
        )
    elif animation == "celebrate":
        phase = cyc2
        move_points(
            {
                "near_elbow": _lerp_point(pose.near_elbow, (93.0, 58.0), abs(phase)),
                "far_elbow": _lerp_point(pose.far_elbow, (50.0, 59.0), abs(phase)),
                "near_hand": _lerp_point(pose.near_hand, (101.0, 42.0), abs(phase)),
                "far_hand": _lerp_point(pose.far_hand, (42.0, 44.0), abs(phase)),
                "halo": 0.55 + 0.28 * abs(phase),
                "mouth": 0.17,
                "brow": 0.08,
            }
        )
    elif animation == "straightedge_slam":
        rush = _pulse(t)
        move_points(
            {
                "near_elbow": _lerp_point(pose.near_elbow, (100.0, 71.0), rush),
                "near_hand": _lerp_point(pose.near_hand, (117.0, 72.0), rush),
                "far_hand": _lerp_point(pose.far_hand, (52.0, 95.0), rush * 0.5),
                "straightedge": 0.35 + 0.65 * rush,
                "brow": 0.42,
                "mouth": 0.04,
                "near_hand_mode": "blade",
                "robe_spread": 0.26 + 0.22 * rush,
                "cloak_sweep": 0.35 * rush,
            }
        )
    elif animation == "parallel_banish":
        press = _pulse(t)
        move_points(
            {
                "near_elbow": _lerp_point(pose.near_elbow, (92.0, 68.0), press),
                "near_hand": _lerp_point(pose.near_hand, (107.0, 70.0), press),
                "far_elbow": _lerp_point(pose.far_elbow, (54.0, 67.0), press),
                "far_hand": _lerp_point(pose.far_hand, (39.0, 71.0), press),
                "parallel": 0.30 + 0.70 * press,
                "brow": 0.36,
                "mouth": 0.02,
                "near_hand_mode": "push",
                "far_hand_mode": "push",
            }
        )
    elif animation == "postulate_burst":
        charge = _pulse(t)
        move_points(
            {
                "near_elbow": _lerp_point(pose.near_elbow, (94.0, 66.0), charge * 0.65),
                "near_hand": _lerp_point(pose.near_hand, (101.0, 56.0), charge),
                "far_elbow": _lerp_point(pose.far_elbow, (56.0, 75.0), charge * 0.25),
                "far_hand": _lerp_point(pose.far_hand, (45.0, 92.0), charge * 0.15),
                "burst": 0.25 + 0.75 * charge,
                "brow": 0.35,
                "mouth": 0.10,
                "near_hand_mode": "point",
                "glyphs": 0.35 + 0.25 * charge,
            }
        )
    elif animation == "compass_orbit":
        whirl = _pulse(t)
        move_points(
            {
                "near_elbow": _lerp_point(pose.near_elbow, (91.0, 62.0), whirl * 0.5),
                "near_hand": _lerp_point(pose.near_hand, (99.0, 52.0), whirl * 0.5),
                "far_elbow": _lerp_point(pose.far_elbow, (53.0, 65.0), whirl * 0.45),
                "far_hand": _lerp_point(pose.far_hand, (46.0, 54.0), whirl * 0.45),
                "orbit": 0.40 + 0.60 * whirl,
                "aura": 0.25 + 0.4 * whirl,
                "brow": 0.22,
                "mouth": 0.08,
                "halo": 0.10 + 0.15 * whirl,
            }
        )
    elif animation == "portal_denial":
        deny = _pulse(t)
        move_points(
            {
                "near_elbow": _lerp_point(pose.near_elbow, (93.0, 64.0), deny),
                "near_hand": _lerp_point(pose.near_hand, (110.0, 56.0), deny),
                "far_elbow": _lerp_point(pose.far_elbow, (52.0, 79.0), deny * 0.3),
                "far_hand": _lerp_point(pose.far_hand, (39.0, 93.0), deny * 0.25),
                "denial": 0.35 + 0.65 * deny,
                "parallel": 0.18 + 0.14 * deny,
                "straightedge": 0.08 + 0.10 * deny,
                "disdain": 0.18 + 0.25 * deny,
                "brow": 0.48,
                "mouth": 0.02,
                "near_hand_mode": "condemn",
            }
        )

    return pose


def _draw_leg(draw: ImageDraw.ImageDraw, hip: Point, knee: Point, ankle: Point, *, far: bool, pose: Pose) -> None:
    thigh_fill = ROBE_SHADE if far else ROBE
    shin_fill = ROBE_DEEP if far else ROBE_SHADE
    _capsule(draw, hip, knee, 4.6 if far else 5.0, 4.0 if far else 4.5, fill=thigh_fill)
    _capsule(draw, knee, ankle, 3.6 if far else 4.0, 3.0 if far else 3.3, fill=shin_fill)
    foot = [
        _offset(ankle, -3.0, 0.0),
        _offset(ankle, 4.5, 0.0),
        _offset(ankle, 8.0, 2.4),
        _offset(ankle, 3.0, 5.0),
        _offset(ankle, -4.0, 4.2),
    ]
    _poly(draw, foot, fill=SANDAL if not far else SANDAL_LIGHT, outline=OUTLINE, width=0.9)


def _draw_torso(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    chest = _lerp_point(pose.neck, ((pose.near_hip[0] + pose.far_hip[0]) * 0.5, 66.0 + pose.vertical), 0.50)
    hem_y = max(pose.near_ankle[1], pose.far_ankle[1]) - 1.5
    spread = 12.0 + pose.robe_spread * 18.0
    left_hem = (59.0 - spread * 0.42, hem_y)
    right_hem = (88.0 + spread * 0.58, hem_y)
    underrobe = [
        (63.0, pose.neck[1] + 8.0),
        (81.0, pose.neck[1] + 7.0),
        (92.0, 91.0),
        right_hem,
        left_hem,
        (55.0, 89.0),
    ]
    _poly(draw, underrobe, fill=ROBE, outline=OUTLINE, width=1.1)
    fold = [
        (71.0, pose.neck[1] + 6.0),
        (76.0, 75.0),
        (73.0, hem_y),
        (67.0, hem_y),
        (69.0, 77.0),
    ]
    _poly(draw, fold, fill=ROBE_SHADE, outline=OUTLINE_SOFT, width=0.7)
    right_fold = [
        (79.5, pose.neck[1] + 7.0),
        (86.0, 78.0),
        (91.0, hem_y - 1.0),
        (83.0, hem_y - 0.4),
        (79.0, 79.0),
    ]
    _poly(draw, right_fold, fill=ROBE_SHADE, outline=OUTLINE_SOFT, width=0.7)

    mantle = [
        (57.0, 49.0),
        (77.0, 46.0),
        (94.0, 55.0),
        (101.0 + pose.cloak_sweep * 10.0, 86.0),
        (92.0 + pose.cloak_sweep * 6.0, 122.0),
        (72.0, 113.0),
        (69.0, 72.0),
        (58.0, 73.0),
        (50.0, 58.0),
    ]
    _poly(draw, mantle, fill=MANTLE, outline=OUTLINE, width=1.15)
    mantle_trim = [
        (59.0, 50.0),
        (77.0, 48.5),
        (91.0, 56.5),
        (96.0 + pose.cloak_sweep * 5.5, 84.0),
        (88.0 + pose.cloak_sweep * 4.0, 117.0),
    ]
    _line(draw, mantle_trim, GOLD_LIGHT, 1.8)
    _line(draw, [(_lerp_point(mantle[0], mantle[-1], 0.6)), (82.0, 109.0)], GOLD, 1.3)

    belt = [
        (61.0, 83.0),
        (86.0, 81.0),
        (91.0, 90.0),
        (62.0, 92.0),
    ]
    _poly(draw, belt, fill=BELT, outline=OUTLINE, width=0.9)
    clasp = [(72.0, 83.0), (77.5, 83.0), (80.0, 87.0), (74.7, 90.0), (70.5, 87.0)]
    _poly(draw, clasp, fill=GOLD, outline=OUTLINE_SOFT, width=0.7)

    if pose.aura > 0.01:
        _arc(draw, (72.0, 69.0), 19.0, 26.0, 196, 352, _fade(GEO_CYAN, pose.aura), 1.8)


def _draw_hand(draw: ImageDraw.ImageDraw, center: Point, mode: str, far: bool = False) -> None:
    fill = SKIN_SHADE if far else SKIN
    outline = OUTLINE_SOFT if far else OUTLINE
    if mode == "point":
        palm = [
            _offset(center, -2.8, -1.8),
            _offset(center, 1.0, -2.0),
            _offset(center, 2.4, 1.0),
            _offset(center, -1.2, 2.2),
        ]
        finger = [_offset(center, 1.0, -1.5), _offset(center, 7.5, -4.2)]
        _poly(draw, palm, fill=fill, outline=outline, width=0.7)
        _line(draw, finger, outline, 1.8)
        _line(draw, [_offset(center, 0.4, -1.2), _offset(center, 6.8, -3.7)], GOLD_LIGHT, 0.9)
    elif mode in {"push", "condemn", "block"}:
        _ellipse(draw, _offset(center, 0.3, 0.4), 3.8, 3.0, fill=fill, outline=outline, width=0.7)
        for dx in (-1.8, 0.2, 2.0):
            _line(draw, [_offset(center, dx, -1.8), _offset(center, dx + 0.6, -5.8)], outline, 1.0)
    elif mode == "blade":
        blade = [
            _offset(center, -2.5, -2.0),
            _offset(center, 2.0, -0.8),
            _offset(center, 1.0, 2.2),
            _offset(center, -3.2, 1.2),
        ]
        _poly(draw, blade, fill=fill, outline=outline, width=0.7)
    elif mode == "dismiss":
        _ellipse(draw, _offset(center, 0.6, 0.4), 3.5, 2.8, fill=fill, outline=outline, width=0.7)
        _line(draw, [_offset(center, 0.4, -2.0), _offset(center, 5.4, -6.2)], outline, 1.0)
        _line(draw, [_offset(center, -0.6, -1.6), _offset(center, 4.6, -4.9)], outline, 0.9)
    elif mode == "lecture":
        _ellipse(draw, _offset(center, 0.2, 0.3), 3.3, 2.8, fill=fill, outline=outline, width=0.7)
        for tip in ((4.6, -4.9), (1.8, -5.2), (-0.5, -4.5)):
            _line(draw, [_offset(center, 0.0, -1.0), _offset(center, *tip)], outline, 0.9)
    else:
        _ellipse(draw, _offset(center, 0.0, 0.3), 3.2, 2.8, fill=fill, outline=outline, width=0.7)


def _draw_arm(draw: ImageDraw.ImageDraw, shoulder: Point, elbow: Point, hand: Point, mode: str, *, far: bool, pose: Pose) -> None:
    sleeve = MANTLE_DEEP if far else MANTLE_LIGHT
    cuff = GOLD_DEEP if far else GOLD
    _capsule(draw, shoulder, elbow, 5.1 if far else 5.5, 4.4 if far else 4.8, fill=sleeve, outline=OUTLINE_SOFT if far else OUTLINE, width=0.9)
    _capsule(draw, elbow, hand, 4.2 if far else 4.5, 3.4 if far else 3.6, fill=sleeve, outline=OUTLINE_SOFT if far else OUTLINE, width=0.8)
    cuff_center = _lerp_point(elbow, hand, 0.72)
    _ellipse(draw, cuff_center, 4.2, 2.1, cuff, outline=OUTLINE_SOFT if far else OUTLINE, width=0.6)
    _draw_hand(draw, hand, mode, far=far)


def _draw_head(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    neck_box = [
        (67.0, 40.0 + pose.vertical),
        (77.0, 40.0 + pose.vertical),
        (78.2, 49.0 + pose.vertical),
        (66.0, 49.0 + pose.vertical),
    ]
    _poly(draw, neck_box, fill=SKIN_SHADE, outline=OUTLINE_SOFT, width=0.8)

    jaw_y = pose.head[1] + 13.0
    face = [
        (61.5, pose.head[1] - 4.5),
        (67.0, pose.head[1] - 9.0),
        (77.0, pose.head[1] - 8.5),
        (82.5, pose.head[1] - 3.5),
        (84.0, pose.head[1] + 5.0),
        (82.0, jaw_y),
        (72.0, jaw_y + 3.0),
        (62.0, jaw_y),
        (59.5, pose.head[1] + 4.5),
    ]
    _poly(draw, face, fill=SKIN, outline=OUTLINE, width=1.0)
    _poly(draw, [(62.0, jaw_y - 0.5), (72.0, jaw_y + 4.4 + pose.beard_sway), (81.5, jaw_y - 0.8), (78.0, pose.head[1] + 8.0), (66.0, pose.head[1] + 8.0)], fill=HAIR, outline=OUTLINE, width=0.9)
    _line(draw, [(65.0, pose.head[1] + 10.0), (72.0, jaw_y + 3.3), (79.0, pose.head[1] + 10.2)], HAIR_LIGHT, 0.9)

    # Hair and laurel.
    hair = [
        (59.5, pose.head[1] + 0.0),
        (61.5, pose.head[1] - 7.2),
        (68.5, pose.head[1] - 11.0),
        (77.5, pose.head[1] - 10.2),
        (83.5, pose.head[1] - 5.8),
        (85.0, pose.head[1] + 2.8),
        (81.0, pose.head[1] + 0.8),
        (77.0, pose.head[1] - 1.7),
        (68.0, pose.head[1] - 2.5),
        (61.0, pose.head[1] + 1.0),
    ]
    _poly(draw, hair, fill=HAIR, outline=OUTLINE, width=1.0)
    for cx, ang in ((65.5, -24), (69.0, -8), (72.5, 4), (76.0, 18), (79.0, 28)):
        _leaf(draw, (cx, pose.head[1] - 8.4), ang, 4.5, 1.6, fill=LAUREL)
        _line(draw, [(cx - 0.3, pose.head[1] - 6.9), (cx + 0.5, pose.head[1] - 9.6)], LAUREL_LIGHT, 0.5)

    # Brows and eyes.
    brow_l = pose.brow * 1.5
    narrow = 0.8 + pose.eye_narrow * 1.8 + pose.blink * 2.6
    _line(draw, [(65.5, pose.head[1] - 0.2 - brow_l), (70.5, pose.head[1] - 1.8 - brow_l * 0.25)], HAIR_SHADE, 1.3)
    _line(draw, [(73.6, pose.head[1] - 1.6 - brow_l * 0.25), (79.2, pose.head[1] - 0.4 - brow_l)], HAIR_SHADE, 1.3)
    _ellipse(draw, (68.0, pose.head[1] + 1.8), 3.2, max(0.4, 2.0 - narrow), EYE_WHITE, outline=OUTLINE_SOFT, width=0.4)
    _ellipse(draw, (76.5, pose.head[1] + 1.7), 3.2, max(0.4, 2.0 - narrow), EYE_WHITE, outline=OUTLINE_SOFT, width=0.4)
    if pose.blink < 0.9:
        _disc(draw, (68.2, pose.head[1] + 1.9), 0.85, EYE, outline=None)
        _disc(draw, (76.4, pose.head[1] + 1.8), 0.85, EYE, outline=None)
    else:
        _line(draw, [(65.0, pose.head[1] + 1.8), (71.0, pose.head[1] + 1.8)], EYE, 0.7)
        _line(draw, [(73.5, pose.head[1] + 1.7), (79.5, pose.head[1] + 1.7)], EYE, 0.7)
    # Nose and mouth.
    _line(draw, [(72.7, pose.head[1] + 0.8), (71.2, pose.head[1] + 4.8), (73.0, pose.head[1] + 6.4)], SKIN_DEEP, 0.8)
    mouth_y = pose.head[1] + 8.0
    _arc(draw, (72.0, mouth_y), 4.2, 2.4 + pose.mouth * 2.5, 15, 165, MOUTH, 1.0)
    if pose.mouth > 0.14:
        _line(draw, [(69.2, mouth_y + 0.2), (74.8, mouth_y + 0.2)], EYE_WHITE, 0.7)
    # Ear.
    _ellipse(draw, (83.4, pose.head[1] + 4.2), 1.7, 2.8, SKIN_SHADE, outline=OUTLINE_SOFT, width=0.4)


def _draw_effects_back(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    if pose.orbit > 0.02:
        center = (72.0, 70.0)
        _arc(draw, center, 23.0, 30.0, 130, 320, _fade(GEO_CYAN, pose.orbit), 1.9)
        _arc(draw, center, 15.0, 21.0, 305, 100, _fade(GOLD_LIGHT, pose.orbit * 0.75), 1.1)
        angle = pose.orbit * 280.0
        for radius, col, phase in ((23.0, GOLD, 0.0), (18.0, GEO_CYAN, 110.0), (15.5, GEO_VIOLET, 220.0)):
            rad = math.radians(angle + phase)
            p = (center[0] + math.cos(rad) * radius, center[1] + math.sin(rad) * radius * 0.78)
            _disc(draw, p, 1.8, _fade(col, pose.orbit), outline=OUTLINE_SOFT, width=0.4)
    if pose.denial > 0.02:
        c = (112.0, 52.0)
        _arc(draw, c, 15.0, 17.0, 0, 359, _fade(GEO_VIOLET, pose.denial), 2.0)
        _arc(draw, c, 11.0, 13.0, 0, 359, _fade(GEO_CYAN, pose.denial * 0.55), 0.9)
        for xoff in (-8.0, 0.0, 8.0):
            _line(draw, [(_offset(c, xoff, -12.0)), (_offset(c, xoff, 12.0))], _fade(GOLD, pose.denial * 0.9), 0.9)
        _line(draw, [(_offset(c, -13.0, 11.0)), (_offset(c, 13.0, -11.0))], _fade(GEO_RED, pose.denial), 2.3)
    if pose.burst > 0.02:
        p = _offset(pose.near_hand, 14.0, -8.0)
        tri = [_offset(p, 0.0, -11.0), _offset(p, -10.0, 6.0), _offset(p, 10.0, 6.0)]
        sq = [_offset(p, -7.5, -7.5), _offset(p, 7.5, -7.5), _offset(p, 7.5, 7.5), _offset(p, -7.5, 7.5)]
        _poly(draw, tri, fill=None, outline=_fade(GEO_CYAN, pose.burst * 0.85), width=1.4)
        _poly(draw, sq, fill=None, outline=_fade(GOLD_LIGHT, pose.burst * 0.65), width=1.0)


def _draw_effects_front(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    if pose.straightedge > 0.02:
        a = _offset(pose.near_hand, 0.0, -1.5)
        b = _offset(pose.near_hand, 14.0 + 19.0 * pose.straightedge, -1.8 - 3.0 * pose.straightedge)
        _line(draw, [a, b], _fade(GOLD_LIGHT, pose.straightedge), 3.0)
        _line(draw, [a, b], _fade(GOLD_DEEP, pose.straightedge * 0.75), 1.0)
    if pose.parallel > 0.02:
        hand_y = pose.near_hand[1]
        for idx, yoff in enumerate((-7.0, 0.0, 7.0)):
            start = _offset(pose.near_hand, -1.0, yoff)
            end = _offset(start, 16.0 + pose.parallel * 20.0, 0.0)
            _line(draw, [start, end], _fade(GEO_CYAN if idx != 1 else GOLD_LIGHT, pose.parallel), 1.8 if idx == 1 else 1.2)
        if pose.denial > 0.01:
            _line(draw, [(_offset(pose.near_hand, 9.0, -13.0)), (_offset(pose.near_hand, 9.0, 13.0))], _fade(GEO_RED, pose.denial), 1.2)
    if pose.block > 0.02:
        center = _offset(pose.near_hand, 8.0, -1.0)
        _arc(draw, center, 13.0, 15.0, 250, 110, _fade(GEO_CYAN, pose.block), 2.2)
        _arc(draw, center, 9.0, 11.0, 250, 110, _fade(GOLD_LIGHT, pose.block * 0.8), 1.0)
    if pose.disdain > 0.02:
        tip = _offset(pose.head, 17.0, -2.0)
        _line(draw, [_offset(tip, -4.0, 0.0), tip, _offset(tip, -4.0, 3.0)], _fade(GEO_RED, pose.disdain), 1.4)
    if pose.glyphs > 0.02:
        c = _offset(pose.near_hand, 11.0, -17.0)
        _poly(draw, [_offset(c, -4.0, 3.0), _offset(c, 0.0, -4.0), _offset(c, 4.0, 3.0)], fill=None, outline=_fade(GOLD, pose.glyphs), width=0.9)
        _line(draw, [_offset(c, 8.0, -2.0), _offset(c, 13.0, -2.0)], _fade(GEO_CYAN, pose.glyphs), 0.9)
        _line(draw, [_offset(c, 10.5, -4.5), _offset(c, 10.5, 0.5)], _fade(GEO_CYAN, pose.glyphs), 0.9)
    if pose.halo > 0.02:
        _arc(draw, (72.0, 22.0), 17.0, 5.5, 0, 359, _fade(GOLD_LIGHT, pose.halo), 1.5)


def _render_native_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    pose = _pose(animation, frame_idx, frame_count)
    image = Image.new("RGBA", (FRAME_W * SUPER, FRAME_H * SUPER), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image, "RGBA")

    _draw_effects_back(draw, pose)
    _draw_leg(draw, pose.far_hip, pose.far_knee, pose.far_ankle, far=True, pose=pose)
    _draw_leg(draw, pose.near_hip, pose.near_knee, pose.near_ankle, far=False, pose=pose)
    _draw_torso(draw, pose)
    _draw_arm(draw, pose.far_shoulder, pose.far_elbow, pose.far_hand, pose.far_hand_mode, far=True, pose=pose)
    _draw_arm(draw, pose.near_shoulder, pose.near_elbow, pose.near_hand, pose.near_hand_mode, far=False, pose=pose)
    _draw_effects_front(draw, pose)
    _draw_head(draw, pose)
    return image


def render_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    return _render_native_frame(animation, frame_idx, frame_count).resize((FRAME_W, FRAME_H), Image.Resampling.LANCZOS)


def render_portraits(out_dir: Path, **opts) -> List[Path]:
    del opts
    face = FaceGuide(
        center_x=72.0,
        center_y=28.5,
        width=28.0,
        height=31.0,
        source_width=FRAME_W,
        source_height=FRAME_H,
    )

    def portrait_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
        return render_framed_portrait(
            _render_native_frame(animation, frame_idx, frame_count),
            face,
            view_width=60.0,
            center_y=43.0,
        )

    clips = {
        "default": PortraitClip.still(portrait_frame("idle", 1, 8)),
        "lecturing": PortraitClip(
            tuple(portrait_frame("talk", frame, 8) for frame in range(8)),
            duration_ms=104,
            looping=True,
        ),
        "disdain": PortraitClip(
            tuple(portrait_frame("taunt", frame, 8) for frame in (1, 3, 5, 7)),
            duration_ms=118,
            looping=True,
        ),
        "condemning": PortraitClip(
            tuple(portrait_frame("portal_denial", frame, 12) for frame in (2, 4, 6, 8, 10)),
            duration_ms=88,
            looping=True,
        ),
    }
    return write_portrait_sheet(TARGET_NAME, clips, Path(out_dir))


def _body_metrics_override(fw: int, fh: int):
    return {
        "body_pixel_bbox": {"x": int(fw * 0.24), "y": int(fh * 0.09), "w": int(fw * 0.57), "h": int(fh * 0.84)},
        "feet_pixel": {"x": fw * 0.52, "y": fh * 0.92},
        "feet_anchor_norm": {"x": 0.01, "y": round(0.5 - 0.92, 6)},
    }


def render(out_dir: Path, **opts) -> List[Path]:
    del opts
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=Path(out_dir),
        frame_size=(FRAME_W, FRAME_H),
        label_width=112,
        auto_crop=False,
        body_metrics_fn=_body_metrics_override,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning={"collision_scale": 1.0, "frame_sample_inset": 1},
        animation_key_map={name: name for name, _frames, _duration in ROWS},
        trim=False,
        attack_hitboxes={
            "straightedge_slam": {"bbox": {"x": 86, "y": 50, "w": 52, "h": 32}},
            "parallel_banish": {"bbox": {"x": 84, "y": 42, "w": 48, "h": 38}},
            "portal_denial": {"bbox": {"x": 90, "y": 26, "w": 44, "h": 45}},
            "postulate_burst": {"bbox": {"x": 83, "y": 37, "w": 40, "h": 35}},
            "compass_orbit": {"bbox": {"x": 44, "y": 31, "w": 62, "h": 62}},
        },
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    return [Path(outputs[key]) for key in keys if outputs.get(key)]


def render_canonical(out_dir: Path, **opts) -> Path:
    del opts
    return write_canonical(TARGET_NAME, ROWS, render_frame, Path(out_dir), frame_size=(FRAME_W, FRAME_H))


__all__ = ["ACTOR_METADATA", "render", "render_canonical", "render_portraits"]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out_dir", nargs="?", type=Path, default=Path("generated") / TARGET_NAME)
    args = parser.parse_args(argv)
    outputs = render(args.out_dir)
    for path in outputs:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
