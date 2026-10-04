"""Shared procedural sprite builder for the Runge/Kutta parody duo.

The duo are tougher, denser, and slower than Oiler.  Their silhouettes push
that idea through broad coats, reinforced aprons, heavy gloves, and thick
boots.  They are not generic professors; they are scheme-running numerical
operators trying to seize Oiler's Kernel.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw

from ...authoring import rigdoc
from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.portrait import FaceGuide, PortraitClip, render_framed_portrait, write_portrait_sheet
from ...authoring.sheet_build import build_sheet, write_canonical
from ambition_sprite2d_renderer.core.draw import blending_draw
from . import _fx_piece
from . import _solo_shape_rig as _rig

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

FRAME_W = 144
FRAME_H = 144
SUPER = 4

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 152),
    ("walk", 8, 122),
    ("run", 8, 104),
    ("crouch", 6, 108),
    ("jump", 6, 92),
    ("fall", 6, 92),
    ("land_hard", 6, 90),
    ("talk", 8, 112),
    ("interact", 8, 100),
    ("jab", 5, 82),
    ("attack_up", 6, 84),
    ("attack_down", 6, 84),
    ("air_forward", 6, 82),
    ("block", 8, 92),
    ("hit", 5, 96),
    ("death", 10, 114),
    ("taunt", 8, 106),
    ("celebrate", 8, 96),
    ("stage_smash", 8, 86),
    ("slope_lock", 8, 94),
    ("kernel_seize", 10, 92),
    ("converge_crush", 10, 96),
]

OUTLINE = (15, 18, 24, 255)
OUTLINE_SOFT = (36, 42, 53, 255)
SKIN_BASE = (194, 153, 118, 255)
SKIN_LIGHT = (223, 183, 148, 255)
SKIN_SHADE = (151, 111, 84, 255)
SKIN_DEEP = (110, 76, 56, 255)
EYE = (28, 24, 24, 255)
EYE_WHITE = (242, 238, 233, 255)
MOUTH = (110, 61, 55, 255)
METAL = (138, 149, 163, 255)
METAL_LIGHT = (191, 200, 214, 255)
METAL_DEEP = (90, 98, 112, 255)
GLOW_TEAL = (85, 210, 201, 255)
GLOW_TEAL_SOFT = (85, 210, 201, 86)
GLOW_AMBER = (241, 194, 81, 255)
GLOW_AMBER_SOFT = (241, 194, 81, 80)
GLOW_RED = (230, 96, 88, 255)
GLOW_RED_SOFT = (230, 96, 88, 88)
GLOW_VIOLET = (169, 112, 221, 255)
GLOW_VIOLET_SOFT = (169, 112, 221, 86)


@dataclass(frozen=True)
class DuoStyle:
    target_name: str
    display_name: str
    character_id: str
    coat: RGBA
    coat_light: RGBA
    coat_deep: RGBA
    shirt: RGBA
    shirt_shade: RGBA
    apron: RGBA
    apron_shade: RGBA
    strap: RGBA
    glove: RGBA
    glove_light: RGBA
    pants: RGBA
    pants_shade: RGBA
    boot: RGBA
    boot_light: RGBA
    accent: RGBA
    accent_light: RGBA
    accent_deep: RGBA
    hair: RGBA
    hair_light: RGBA
    hair_deep: RGBA
    head_kind: str
    beard: bool
    moustache: bool
    body_kind: str
    trim: str
    face_center_x: float = 72.0
    face_center_y: float = 28.5
    face_w: float = 30.0
    face_h: float = 31.0


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
    coat_swing: float = 0.0
    apron_swing: float = 0.0
    mouth: float = 0.0
    brow: float = 0.0
    blink: float = 0.0
    eye_narrow: float = 0.0
    beard_sway: float = 0.0
    stage: float = 0.0
    slope: float = 0.0
    kernel: float = 0.0
    converge: float = 0.0
    block: float = 0.0
    hurt: float = 0.0
    defeat: float = 0.0
    taunt: float = 0.0
    cheer: float = 0.0
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


def _make_actor_metadata(style: DuoStyle) -> dict:
    return {
        "actor": {"character_id": style.character_id, "display_name": style.display_name},
        "body": {
            "body_plan": "HumanoidBiped",
            "body_kind": "Standard",
            "mass_class": "Medium",
            "traits": [
                "npc",
                "humanoid",
                "mathematician",
                "kernel_raider",
                "numerical_duelist",
                "slow_heavy",
            ],
            "locomotion_hint": "Walk",
        },
        "capabilities": {
            "traversal": {"walk": True, "jump": True, "crawl": True, "use_lifts": True, "door_access": ["public"]},
            "interactions": {"talk": True, "open_doors": ["public"]},
        },
        "brain": {"default_preset": "guard"},
        "actions": {"default_preset": "heavy_combat"},
        "visual": {
            "default_pose": "idle",
            "portrait": {
                "face_guide": {
                    "center": {"x": style.face_center_x, "y": style.face_center_y},
                    "size": {"width": style.face_w, "height": style.face_h},
                    "source_size": {"width": FRAME_W, "height": FRAME_H},
                }
            },
        },
        "tags": ["npc", "humanoid", "mathematician", "kernel_raider", "numerical_duelist", "slow_heavy"],
        "sockets": {
            "head": {"source": "explicit.profile.humanoid", "point": {"x": 72.0, "y": 28.0}},
            "chest": {"source": "explicit.profile.humanoid", "point": {"x": 72.0, "y": 70.0}},
            "hand_l": {"source": "explicit.profile.humanoid", "point": {"x": 48.0, "y": 84.0}},
            "hand_r": {"source": "explicit.profile.humanoid", "point": {"x": 98.0, "y": 84.0}},
            "speech_bubble": {"source": "explicit.profile.humanoid", "point": {"x": 72.0, "y": 8.0}},
        },
        "animation_bindings": {
            "default": {"animation": "idle", "events": []},
            "locomotion.walk": {"animation": "walk", "events": []},
            "locomotion.run": {"animation": "run", "events": []},
            "traversal.jump": {"animation": "jump", "events": []},
            "traversal.fall": {"animation": "fall", "events": []},
            "interaction.talk": {"animation": "talk", "events": []},
            "interaction.use": {"animation": "interact", "events": []},
            "action.melee.primary": {"animation": "stage_smash", "events": []},
            "action.ranged.primary": {"animation": "slope_lock", "events": []},
            "action.special.primary": {"animation": "kernel_seize", "events": []},
            "action.special.secondary": {"animation": "converge_crush", "events": []},
            "action.defense.block": {"animation": "block", "events": []},
            "emote.taunt": {"animation": "taunt", "events": []},
        },
    }


def _make_base_pose(style: DuoStyle) -> Pose:
    if style.body_kind == "broad":
        return Pose(
            head=(72.0, 29.5), neck=(72.0, 44.0),
            near_shoulder=(86.0, 56.0), far_shoulder=(56.0, 57.0),
            near_elbow=(94.0, 76.0), far_elbow=(48.0, 76.0),
            near_hand=(97.0, 95.0), far_hand=(44.0, 94.0),
            near_hip=(82.0, 85.0), far_hip=(63.0, 86.0),
            near_knee=(83.0, 103.0), far_knee=(61.0, 104.0),
            near_ankle=(84.0, 126.0), far_ankle=(60.0, 126.0),
            mouth=0.05, brow=0.16, eye_narrow=0.15,
        )
    return Pose(
        head=(72.0, 28.5), neck=(72.0, 43.0),
        near_shoulder=(84.0, 54.0), far_shoulder=(58.0, 55.0),
        near_elbow=(92.0, 73.0), far_elbow=(50.0, 74.0),
        near_hand=(95.0, 90.0), far_hand=(45.0, 90.0),
        near_hip=(80.0, 84.0), far_hip=(64.0, 84.5),
        near_knee=(82.0, 102.0), far_knee=(63.0, 103.0),
        near_ankle=(84.0, 126.0), far_ankle=(61.0, 126.0),
        mouth=0.04, brow=0.14, eye_narrow=0.12,
    )


def _pose(style: DuoStyle, animation: str, frame_idx: int, frame_count: int) -> Pose:
    base = _make_base_pose(style)
    t = frame_idx / max(1, frame_count)
    cyc = math.sin(t * math.tau)
    cyc2 = math.sin(t * math.tau + math.pi / 2.0)
    pose = replace(
        base,
        vertical=0.55 * cyc2,
        coat_swing=0.12 * cyc,
        apron_swing=0.08 * cyc,
        beard_sway=0.08 * cyc if style.beard else 0.0,
    )

    def change(delta: dict[str, object]) -> None:
        nonlocal pose
        values = {name: getattr(pose, name) for name in pose.__dataclass_fields__}
        for key, value in delta.items():
            values[key] = value
        pose = Pose(**values)

    v = pose.vertical
    change({
        "head": _offset(pose.head, 0.0, v), "neck": _offset(pose.neck, 0.0, v),
        "near_shoulder": _offset(pose.near_shoulder, 0.0, v), "far_shoulder": _offset(pose.far_shoulder, 0.0, v),
        "near_elbow": _offset(pose.near_elbow, 0.0, v), "far_elbow": _offset(pose.far_elbow, 0.0, v),
        "near_hand": _offset(pose.near_hand, 0.0, v), "far_hand": _offset(pose.far_hand, 0.0, v),
        "near_hip": _offset(pose.near_hip, 0.0, v), "far_hip": _offset(pose.far_hip, 0.0, v),
        "near_knee": _offset(pose.near_knee, 0.0, v), "far_knee": _offset(pose.far_knee, 0.0, v),
        "near_ankle": _offset(pose.near_ankle, 0.0, v), "far_ankle": _offset(pose.far_ankle, 0.0, v),
    })

    if animation in {"walk", "run"}:
        stride = 5.4 if animation == "walk" else 7.6
        lift = 2.6 if animation == "walk" else 4.1
        arm = 4.0 if animation == "walk" else 6.0
        change({
            "near_knee": _offset(pose.near_knee, cyc * stride * 0.35, -abs(cyc) * lift),
            "far_knee": _offset(pose.far_knee, -cyc * stride * 0.35, -abs(-cyc) * lift),
            "near_ankle": _offset(pose.near_ankle, cyc * stride, -max(0.0, cyc) * lift),
            "far_ankle": _offset(pose.far_ankle, -cyc * stride, -max(0.0, -cyc) * lift),
            "near_elbow": _offset(pose.near_elbow, -cyc * arm * 0.6, 0.5),
            "far_elbow": _offset(pose.far_elbow, cyc * arm * 0.6, 0.5),
            "near_hand": _offset(pose.near_hand, -cyc * arm, abs(cyc) * 0.7),
            "far_hand": _offset(pose.far_hand, cyc * arm, abs(cyc) * 0.7),
            "coat_swing": 0.18 * cyc,
            "apron_swing": 0.16 * cyc,
        })
        if animation == "run":
            change({
                "head": _offset(pose.head, 1.5, -0.2), "neck": _offset(pose.neck, 1.5, -0.2),
                "near_hip": _offset(pose.near_hip, 1.0, 0.0), "far_hip": _offset(pose.far_hip, 1.0, 0.0),
                "brow": 0.24,
            })
    elif animation == "crouch":
        s = _smooth(frame_idx / max(1, frame_count - 1))
        change({
            "head": _offset(pose.head, 0.0, 6.5 * s), "neck": _offset(pose.neck, 0.0, 7.0 * s),
            "near_shoulder": _offset(pose.near_shoulder, 0.5, 6.2 * s), "far_shoulder": _offset(pose.far_shoulder, -0.5, 6.2 * s),
            "near_hip": _offset(pose.near_hip, 0.0, 7.5 * s), "far_hip": _offset(pose.far_hip, 0.0, 7.5 * s),
            "near_knee": _offset(pose.near_knee, -2.5, 3.5 * s), "far_knee": _offset(pose.far_knee, -1.5, 3.5 * s),
            "near_ankle": _offset(pose.near_ankle, -4.8, 0.0), "far_ankle": _offset(pose.far_ankle, -3.4, 0.0),
            "near_elbow": _offset(pose.near_elbow, -3.5, 4.2 * s), "far_elbow": _offset(pose.far_elbow, 2.0, 4.1 * s),
            "near_hand": _offset(pose.near_hand, -5.8, 4.0 * s), "far_hand": _offset(pose.far_hand, -2.5, 4.8 * s),
            "mouth": 0.0,
        })
    elif animation == "jump":
        p = _pulse(t)
        change({
            "head": _offset(pose.head, 0.0, -10.5 * p), "neck": _offset(pose.neck, 0.0, -10.5 * p),
            "near_shoulder": _offset(pose.near_shoulder, 0.0, -10.2 * p), "far_shoulder": _offset(pose.far_shoulder, 0.0, -10.2 * p),
            "near_elbow": _offset(pose.near_elbow, -2.0, -9.0 * p), "far_elbow": _offset(pose.far_elbow, 2.0, -8.8 * p),
            "near_hand": _offset(pose.near_hand, -3.0, -15.0 * p), "far_hand": _offset(pose.far_hand, 2.0, -14.0 * p),
            "near_hip": _offset(pose.near_hip, 0.0, -9.8 * p), "far_hip": _offset(pose.far_hip, 0.0, -9.8 * p),
            "near_knee": _offset(pose.near_knee, 3.0, -6.6 * p), "far_knee": _offset(pose.far_knee, -1.8, -6.0 * p),
            "near_ankle": _offset(pose.near_ankle, 7.2, -10.5 * p), "far_ankle": _offset(pose.far_ankle, -5.0, -9.2 * p),
            "mouth": 0.11,
        })
    elif animation == "fall":
        change({
            "near_elbow": _offset(pose.near_elbow, -2.2, -1.0), "far_elbow": _offset(pose.far_elbow, 3.5, -1.0),
            "near_hand": _offset(pose.near_hand, -3.5, -2.5), "far_hand": _offset(pose.far_hand, 4.5, -2.0),
            "near_knee": _offset(pose.near_knee, 3.0, -4.0), "far_knee": _offset(pose.far_knee, -2.5, -3.0),
            "near_ankle": _offset(pose.near_ankle, 6.0, -2.0), "far_ankle": _offset(pose.far_ankle, -5.0, -1.0),
            "mouth": 0.12, "brow": 0.24,
        })
    elif animation == "land_hard":
        p = _pulse(t)
        change({
            "head": _offset(pose.head, 0.0, 7.8 * p), "neck": _offset(pose.neck, 0.0, 7.8 * p),
            "near_shoulder": _offset(pose.near_shoulder, 0.5, 7.0 * p), "far_shoulder": _offset(pose.far_shoulder, -0.5, 7.0 * p),
            "near_hip": _offset(pose.near_hip, 0.0, 8.8 * p), "far_hip": _offset(pose.far_hip, 0.0, 8.8 * p),
            "near_knee": _offset(pose.near_knee, -4.0, 2.2 * p), "far_knee": _offset(pose.far_knee, -3.0, 2.2 * p),
            "near_ankle": _offset(pose.near_ankle, -5.5, 0.0), "far_ankle": _offset(pose.far_ankle, -4.0, 0.0),
            "near_hand": _offset(pose.near_hand, -5.5, 6.0 * p), "far_hand": _offset(pose.far_hand, -3.5, 6.0 * p),
        })
    elif animation == "talk":
        g = cyc
        change({
            "near_elbow": _offset(pose.near_elbow, 3.2 * g, -2.3 * abs(g)),
            "near_hand": _offset(pose.near_hand, 7.0 * g, -5.0 * abs(g)),
            "mouth": 0.18 + 0.12 * abs(g), "brow": 0.18, "glyphs": 0.28 + 0.16 * abs(g),
            "near_hand_mode": "lecture",
        })
    elif animation == "interact":
        s = _smooth(t)
        change({
            "near_elbow": _lerp_point(pose.near_elbow, (96.0, 68.0), s),
            "near_hand": _lerp_point(pose.near_hand, (110.0, 61.0), s),
            "mouth": 0.06, "brow": 0.18, "glyphs": 0.36, "near_hand_mode": "point",
        })
    elif animation in {"jab", "attack_up", "attack_down", "air_forward"}:
        target = {
            "jab": ((111.0, 79.0), (99.0, 73.0)),
            "attack_up": ((100.0, 55.0), (90.0, 63.0)),
            "attack_down": ((106.0, 97.0), (95.0, 83.0)),
            "air_forward": ((113.0, 70.0), (100.0, 66.0)),
        }[animation]
        p = _pulse(t)
        hand, elbow = target
        change({
            "near_elbow": _lerp_point(pose.near_elbow, elbow, p),
            "near_hand": _lerp_point(pose.near_hand, hand, p),
            "far_hand": _offset(pose.far_hand, -3.0 * p, 1.5), "far_elbow": _offset(pose.far_elbow, -2.0 * p, 1.0),
            "stage": 0.65 * p if animation != "attack_up" else 0.4 * p,
            "near_hand_mode": "fist", "brow": 0.30,
        })
    elif animation == "block":
        p = _pulse(t)
        change({
            "near_elbow": _lerp_point(pose.near_elbow, (87.0, 67.0), p),
            "near_hand": _lerp_point(pose.near_hand, (99.0, 61.0), p),
            "far_elbow": _lerp_point(pose.far_elbow, (56.0, 73.0), p),
            "far_hand": _lerp_point(pose.far_hand, (56.0, 61.0), p),
            "block": 0.45 + 0.4 * p, "near_hand_mode": "block", "far_hand_mode": "block", "brow": 0.26,
        })
    elif animation == "hit":
        p = _pulse(t)
        change({
            "head": _offset(pose.head, -4.0 * p, -0.5 * p), "neck": _offset(pose.neck, -4.0 * p, -0.5 * p),
            "near_shoulder": _offset(pose.near_shoulder, -3.0 * p, 1.0), "far_shoulder": _offset(pose.far_shoulder, -3.0 * p, 1.0),
            "near_elbow": _offset(pose.near_elbow, -6.5 * p, 2.0 * p), "far_elbow": _offset(pose.far_elbow, -4.0 * p, 2.0 * p),
            "near_hand": _offset(pose.near_hand, -10.0 * p, 4.0 * p), "far_hand": _offset(pose.far_hand, -6.0 * p, 4.0 * p),
            "hurt": p, "mouth": 0.15, "brow": 0.4,
        })
    elif animation == "death":
        s = _smooth(t)
        change({
            "head": _lerp_point(pose.head, (54.0, 110.0), s), "neck": _lerp_point(pose.neck, (61.0, 101.0), s),
            "near_shoulder": _lerp_point(pose.near_shoulder, (74.0, 100.0), s), "far_shoulder": _lerp_point(pose.far_shoulder, (56.0, 103.0), s),
            "near_elbow": _lerp_point(pose.near_elbow, (88.0, 109.0), s), "far_elbow": _lerp_point(pose.far_elbow, (43.0, 116.0), s),
            "near_hand": _lerp_point(pose.near_hand, (101.0, 118.0), s), "far_hand": _lerp_point(pose.far_hand, (30.0, 123.0), s),
            "near_hip": _lerp_point(pose.near_hip, (83.0, 104.0), s), "far_hip": _lerp_point(pose.far_hip, (66.0, 107.0), s),
            "near_knee": _lerp_point(pose.near_knee, (96.0, 119.0), s), "far_knee": _lerp_point(pose.far_knee, (70.0, 124.0), s),
            "near_ankle": _lerp_point(pose.near_ankle, (117.0, 129.0), s), "far_ankle": _lerp_point(pose.far_ankle, (77.0, 131.0), s),
            "defeat": s, "hurt": 0.35 + 0.5 * s, "blink": s,
        })
    elif animation == "taunt":
        c = cyc
        change({
            "near_elbow": _offset(pose.near_elbow, 4.0 * c, -4.0 * abs(c)),
            "near_hand": _offset(pose.near_hand, 8.0 * c, -8.0 * abs(c)),
            "mouth": 0.02, "brow": 0.34, "taunt": 0.42 + 0.33 * abs(c), "near_hand_mode": "dismiss", "glyphs": 0.22,
        })
    elif animation == "celebrate":
        c = cyc2
        change({
            "near_elbow": _lerp_point(pose.near_elbow, (94.0, 60.0), abs(c)), "far_elbow": _lerp_point(pose.far_elbow, (50.0, 61.0), abs(c)),
            "near_hand": _lerp_point(pose.near_hand, (101.0, 44.0), abs(c)), "far_hand": _lerp_point(pose.far_hand, (42.0, 46.0), abs(c)),
            "cheer": 0.5 + 0.28 * abs(c), "mouth": 0.16,
        })
    elif animation == "stage_smash":
        p = _pulse(t)
        change({
            "near_elbow": _lerp_point(pose.near_elbow, (100.0, 75.0), p), "near_hand": _lerp_point(pose.near_hand, (117.0, 82.0), p),
            "stage": 0.4 + 0.6 * p, "near_hand_mode": "fist", "brow": 0.34,
        })
    elif animation == "slope_lock":
        p = _pulse(t)
        change({
            "near_elbow": _lerp_point(pose.near_elbow, (91.0, 69.0), p), "near_hand": _lerp_point(pose.near_hand, (107.0, 70.0), p),
            "far_elbow": _lerp_point(pose.far_elbow, (54.0, 68.0), p), "far_hand": _lerp_point(pose.far_hand, (39.0, 72.0), p),
            "slope": 0.35 + 0.65 * p, "near_hand_mode": "push", "far_hand_mode": "push", "brow": 0.28,
        })
    elif animation == "kernel_seize":
        p = _pulse(t)
        change({
            "near_elbow": _lerp_point(pose.near_elbow, (95.0, 64.0), p), "near_hand": _lerp_point(pose.near_hand, (108.0, 55.0), p),
            "far_elbow": _lerp_point(pose.far_elbow, (55.0, 72.0), p * 0.35), "far_hand": _lerp_point(pose.far_hand, (46.0, 86.0), p * 0.35),
            "kernel": 0.35 + 0.65 * p, "near_hand_mode": "grip", "brow": 0.32, "glyphs": 0.26 + 0.18 * p,
        })
    elif animation == "converge_crush":
        p = _pulse(t)
        change({
            "near_elbow": _lerp_point(pose.near_elbow, (90.0, 63.0), p * 0.6), "near_hand": _lerp_point(pose.near_hand, (98.0, 55.0), p * 0.6),
            "far_elbow": _lerp_point(pose.far_elbow, (53.0, 65.0), p * 0.6), "far_hand": _lerp_point(pose.far_hand, (45.0, 57.0), p * 0.6),
            "converge": 0.4 + 0.6 * p, "cheer": 0.08 + 0.1 * p, "brow": 0.2,
        })
    return pose


def _draw_hand(draw: ImageDraw.ImageDraw, style: DuoStyle, center: Point, mode: str, far: bool) -> None:
    fill = style.glove_light if not far else style.glove
    outline = OUTLINE_SOFT if far else OUTLINE
    if mode == "point":
        palm = [_offset(center, -3.0, -2.0), _offset(center, 1.2, -2.2), _offset(center, 2.6, 1.2), _offset(center, -1.2, 2.4)]
        _poly(draw, palm, fill=fill, outline=outline, width=0.7)
        _line(draw, [_offset(center, 1.0, -1.4), _offset(center, 8.2, -4.2)], outline, 1.1)
    elif mode in {"push", "block"}:
        _ellipse(draw, center, 3.8, 3.1, fill=fill, outline=outline, width=0.7)
        for dx in (-1.8, 0.0, 1.8):
            _line(draw, [_offset(center, dx, -1.4), _offset(center, dx + 0.5, -5.8)], outline, 0.9)
    elif mode in {"fist", "grip"}:
        _ellipse(draw, _offset(center, 0.2, 0.4), 3.6, 3.3, fill=fill, outline=outline, width=0.7)
        _line(draw, [_offset(center, -2.8, -0.8), _offset(center, 2.8, -0.8)], style.accent_deep, 0.8)
    elif mode == "dismiss":
        _ellipse(draw, center, 3.4, 2.9, fill=fill, outline=outline, width=0.7)
        _line(draw, [_offset(center, -0.4, -1.8), _offset(center, 4.8, -6.0)], outline, 0.9)
    elif mode == "lecture":
        _ellipse(draw, center, 3.5, 2.9, fill=fill, outline=outline, width=0.7)
        for tip in ((4.8, -4.9), (1.8, -5.2), (-0.5, -4.6)):
            _line(draw, [_offset(center, 0.0, -1.0), _offset(center, *tip)], outline, 0.8)
    else:
        _ellipse(draw, center, 3.3, 3.0, fill=fill, outline=outline, width=0.7)


# --- Drawn as a rig: each rigid piece is painted ONCE at its rest place and
# carried into the frame (moved, turned, mirrored). The coat and the eyes are
# symmetric about ``_AXIS``: their left half is painted and the right half is
# the same raster mirrored. Effects are pieces painted at full strength and
# placed with their strength as the draw's opacity. ---

_CANVAS = (FRAME_W * SUPER, FRAME_H * SUPER)
#: Pieces are cut on a grid of this many canvas pixels, so a mirrored copy
#: reduces to the exact mirror of the reduced piece.
_GRID = 8
#: The mirror axis of the coat and the face (frame pixels, on the grid).
_AXIS = 72.0
#: The coat's upper half is cut at ``_WAIST_CUT`` (it rides the neck); the
#: skirt starts at ``_SKIRT_TOP`` (it rides the hem). They overlap between.
_WAIST_CUT = 88.0
_SKIRT_TOP = 80.0
#: Where a bone piece's root sits on its rest canvas (frame pixels).
_BONE_O: Point = (20.0, 20.0)
_MID_O: Point = (FRAME_W / 2.0, FRAME_H / 2.0)
#: How far the body turns (counter-clockwise, degrees) when it falls dead.
_DEATH_TURN = 84.0
_PIECES: dict = {}


def _sp(p: Point) -> Point:
    return (p[0] * SUPER, p[1] * SUPER)


def _piece(style: DuoStyle, key, paint, pivot: Point, keep: Tuple[float, float, float, float] | None = None):
    """``paint(draw)`` on a frame-sized canvas (the group at its rest place),
    cut to what it covers on a ``_GRID`` of canvas pixels; ``pivot`` in frame
    pixels. ``keep`` = (x0, y0, x1, y1) frame pixels keeps only that region (a
    half or a band of a symmetric group). Cached under ``key``, which must
    name everything ``paint`` reads."""
    full = (style.target_name,) + tuple(key)
    cached = _PIECES.get(full)
    if cached is None:
        image = Image.new("RGBA", _CANVAS, (0, 0, 0, 0))
        paint(blending_draw(image))
        if keep is not None:
            mask = Image.new("L", _CANVAS, 0)
            x0, y0, x1, y1 = (int(round(v * SUPER)) for v in keep)
            ImageDraw.Draw(mask).rectangle((max(0, x0), max(0, y0), min(_CANVAS[0], x1) - 1, min(_CANVAS[1], y1) - 1), fill=255)
            image = Image.composite(image, Image.new("RGBA", _CANVAS, (0, 0, 0, 0)), mask)
        box = image.getchannel("A").getbbox() or (0, 0, _GRID, _GRID)
        x0, y0 = box[0] - box[0] % _GRID, box[1] - box[1] % _GRID
        x1, y1 = box[2] + (-box[2]) % _GRID, box[3] + (-box[3]) % _GRID
        cached = (image.crop((x0, y0, x1, y1)), (pivot[0] * SUPER - x0, pivot[1] * SUPER - y0))
        _PIECES[full] = cached
    return cached


def _put(img: Image.Image, part, at: Point, deg: float, name: str, opacity: float = 1.0) -> None:
    _rig.place(img, part, _sp(at), deg, name, opacity)


def _put_pair(img: Image.Image, part, xf, rest: Point, name: str, opacity: float = 1.0) -> None:
    """The left half ``part`` (its pivot ``rest`` on the axis) and its mirror,
    carried by ``xf``."""
    at, deg = xf.pt(rest), xf.deg
    _put(img, part, at, deg, f"{name}_l", opacity)
    _put(img, _fx_piece.mirrored(part), at, deg, f"{name}_r", opacity)


def _deg(a: Point, b: Point) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def _two_bone(root: Point, target: Point, l1: float, l2: float, hint: Point) -> Tuple[Point, Point]:
    """Joint and end of a two-bone limb of lengths ``l1``, ``l2`` from ``root``
    reaching toward ``target``, bent to the side nearer ``hint``."""
    dx, dy = target[0] - root[0], target[1] - root[1]
    reach = min(max(math.hypot(dx, dy), abs(l1 - l2) + 1e-3), l1 + l2 - 1e-3)
    base = math.atan2(dy, dx)
    bend = math.acos(max(-1.0, min(1.0, (l1 * l1 + reach * reach - l2 * l2) / (2 * l1 * reach))))
    joints = [(root[0] + l1 * math.cos(base + k * bend), root[1] + l1 * math.sin(base + k * bend)) for k in (1.0, -1.0)]
    joint = min(joints, key=lambda j: math.dist(j, hint))
    ex, ey = target[0] - joint[0], target[1] - joint[1]
    norm = max(1e-6, math.hypot(ex, ey))
    return joint, (joint[0] + ex / norm * l2, joint[1] + ey / norm * l2)


def _bone(style: DuoStyle, img: Image.Image, a: Point, b: Point, length: float, radius_a: float, radius_b: float, fill: RGBA, outline: RGBA, width: float, name: str) -> None:
    """The painter's tapered capsule as a bone of fixed ``length``, turned from ``a`` toward ``b``."""
    O = _BONE_O
    part = _piece(
        style,
        ("bone", length, radius_a, radius_b, fill, outline, width),
        lambda d: _capsule(d, O, (O[0] + length, O[1]), radius_a, radius_b, fill=fill, outline=outline, width=width),
        O,
    )
    _put(img, part, a, _deg(a, b), name)


def _rest_length(base: Pose, a: str, b: str) -> float:
    return float(round(math.dist(getattr(base, a), getattr(base, b))))


def _draw_leg(img: Image.Image, style: DuoStyle, base: Pose, pose: Pose, *, far: bool) -> None:
    side = "far" if far else "near"
    l1, l2 = _rest_length(base, f"{side}_hip", f"{side}_knee"), _rest_length(base, f"{side}_knee", f"{side}_ankle")
    hip = getattr(pose, f"{side}_hip")
    knee, ankle = _two_bone(hip, getattr(pose, f"{side}_ankle"), l1, l2, getattr(pose, f"{side}_knee"))
    thigh_fill = style.pants_shade if far else style.pants
    outline = OUTLINE_SOFT if far else OUTLINE
    _bone(style, img, hip, knee, l1, 4.8 if far else 5.2, 4.2 if far else 4.6, thigh_fill, outline, 0.9, f"{side}_thigh")
    _bone(style, img, knee, ankle, l2, 4.0 if far else 4.3, 3.4 if far else 3.6, style.pants_shade, outline, 0.8, f"{side}_shin")

    def boot(draw) -> None:
        a = _BONE_O
        pts = [_offset(a, -4.0, 0.0), _offset(a, 4.0, 0.0), _offset(a, 8.6, 2.0), _offset(a, 5.0, 5.4), _offset(a, -4.8, 4.8)]
        _poly(draw, pts, fill=style.boot if not far else style.boot_light, outline=OUTLINE, width=0.9)
        _line(draw, [_offset(a, -2.0, 3.0), _offset(a, 5.0, 3.0)], METAL_DEEP, 0.8)

    _put(img, _piece(style, ("boot", far), boot, _BONE_O), ankle, 0.0, f"{side}_boot")


def _draw_arm(img: Image.Image, style: DuoStyle, base: Pose, pose: Pose, hand_deg: float, *, far: bool) -> Point:
    """An arm of fixed bone lengths reaching the painter's hand; returns where its hand is."""
    side = "far" if far else "near"
    l1, l2 = _rest_length(base, f"{side}_shoulder", f"{side}_elbow"), _rest_length(base, f"{side}_elbow", f"{side}_hand")
    shoulder = getattr(pose, f"{side}_shoulder")
    elbow, hand = _two_bone(shoulder, getattr(pose, f"{side}_hand"), l1, l2, getattr(pose, f"{side}_elbow"))
    sleeve = style.coat_deep if far else style.coat_light
    outline = OUTLINE_SOFT if far else OUTLINE
    _bone(style, img, shoulder, elbow, l1, 5.5 if far else 6.0, 4.8 if far else 5.2, sleeve, outline, 0.9, f"{side}_upper_arm")
    O = _BONE_O

    def fore(draw) -> None:
        end = (O[0] + l2, O[1])
        _capsule(draw, O, end, 4.4 if far else 4.8, 3.8 if far else 4.0, fill=sleeve, outline=outline, width=0.8)
        _ellipse(draw, _lerp_point(O, end, 0.72), 4.0, 2.2, style.accent, outline=outline, width=0.6)

    _put(img, _piece(style, ("forearm", far, l2), fore, O), elbow, _deg(elbow, hand), f"{side}_forearm")
    mode = pose.far_hand_mode if far else pose.near_hand_mode
    hand_part = _piece(style, ("hand", far, mode), lambda d: _draw_hand(d, style, _MID_O, mode, far), _MID_O)
    _put(img, hand_part, hand, hand_deg, f"{side}_hand")
    return hand


def _hem(pose: Pose) -> float:
    return max(pose.near_ankle[1], pose.far_ankle[1]) - 1.5


def _paint_coat(draw: ImageDraw.ImageDraw, style: DuoStyle, base: Pose) -> None:
    """The coat, shirt, lapels, straps and collar at rest, symmetric about ``_AXIS``."""
    n = base.neck[1]
    hem = _hem(base)

    def m(points):
        return points + [(2 * _AXIS - x, y) for x, y in reversed(points)]

    left = 54.0 if style.body_kind == "broad" else 56.0
    coat = m([(_AXIS, 92.0), (69.0, hem), (57.0, hem), (49.0, 88.0), (left, n + 5.0), (63.0, n + 1.5)])
    _poly(draw, coat, fill=style.coat, outline=OUTLINE, width=1.1)
    shirt = m([(_AXIS, 88.0), (68.5, 88.0), (61.5, 73.0), (64.5, n + 3.0)])
    _poly(draw, shirt, fill=style.shirt, outline=OUTLINE_SOFT, width=0.7)
    for lapel in ([(59.5, n + 4.0), (69.5, n + 4.0), (67.2, 75.0), (59.2, 82.0)],):
        _poly(draw, lapel, fill=style.coat_light, outline=OUTLINE_SOFT, width=0.7)
        _poly(draw, [(2 * _AXIS - x, y) for x, y in lapel], fill=style.coat_light, outline=OUTLINE_SOFT, width=0.7)
    strap = [(66.8, 78.0), (58.5, 58.0)] if style.trim == "strapped" else [(68.0, 78.0), (61.0, 61.0)]
    width = 1.4 if style.trim == "strapped" else 1.3
    _line(draw, strap, style.strap, width)
    _line(draw, [(2 * _AXIS - x, y) for x, y in strap], style.strap, width)
    collar = m([(_AXIS, n + 6.0), (65.0, n + 1.0), (70.0, n - 0.6)])
    _poly(draw, collar, fill=style.accent_light, outline=OUTLINE_SOFT, width=0.6)


def _paint_apron(draw: ImageDraw.ImageDraw, style: DuoStyle, base: Pose) -> None:
    hem = _hem(base)
    apron = [(66.0, 77.0), (82.0, 77.0), (86.0, hem - 2.0), (62.0, hem - 1.0)]
    if style.trim == "angled":
        apron = [(67.0, 77.0), (81.0, 77.0), (84.0, hem - 4.0), (62.0, hem - 1.5), (64.0, 98.0)]
    _poly(draw, apron, fill=style.apron, outline=OUTLINE, width=0.85)
    _line(draw, [(72.0, 78.0), (74.5, hem - 1.0)], style.apron_shade, 1.0)
    _disc(draw, (74.0, 90.0), 2.6, style.accent, outline=OUTLINE_SOFT, width=0.5)


def _paint_head_base(draw: ImageDraw.ImageDraw, style: DuoStyle, y: float) -> None:
    """The head without its eyes, brows, mouth and beard: face, hair, nose, moustache and ear."""
    if style.head_kind == "square":
        face = [(60.5, y - 4.0), (66.0, y - 8.6), (78.0, y - 8.8), (84.0, y - 4.2), (84.2, y + 7.5), (79.2, y + 13.0), (65.2, y + 13.0), (59.8, y + 7.8)]
    else:
        face = [(61.0, y - 4.5), (66.2, y - 8.8), (77.6, y - 8.4), (82.8, y - 4.2), (84.2, y + 6.2), (81.4, y + 12.0), (72.0, y + 14.0), (63.2, y + 12.0), (59.8, y + 6.4)]
    _poly(draw, face, fill=SKIN_BASE, outline=OUTLINE, width=1.0)
    if style.head_kind == "swept":
        hair = [(60.2, y + 0.0), (61.2, y - 7.0), (69.0, y - 11.4), (79.0, y - 10.4), (84.5, y - 4.2), (84.0, y + 2.6), (80.0, y + 1.0), (73.0, y - 0.6), (67.0, y - 1.2), (62.0, y + 1.5)]
        _poly(draw, hair, fill=style.hair, outline=OUTLINE, width=1.0)
        _line(draw, [(65.0, y - 5.2), (76.0, y - 8.0), (82.0, y - 1.5)], style.hair_light, 1.0)
    else:
        hair = [(60.0, y + 0.0), (61.5, y - 6.8), (68.0, y - 10.6), (77.5, y - 10.2), (83.5, y - 5.2), (84.0, y + 1.5), (79.0, y - 0.8), (69.0, y - 1.8), (62.0, y + 1.6)]
        _poly(draw, hair, fill=style.hair, outline=OUTLINE, width=1.0)
        for x in (64.5, 69.0, 73.5, 78.0):
            _line(draw, [(x, y - 9.0), (x + 1.2, y - 2.0)], style.hair_light, 0.8)
    _line(draw, [(72.5, y + 0.6), (71.0, y + 5.0), (72.8, y + 6.2)], SKIN_DEEP, 0.7)
    if style.moustache:
        mustache = [(66.0, y + 7.8), (71.0, y + 6.8), (78.0, y + 7.8), (77.0, y + 9.4), (67.0, y + 9.4)]
        _poly(draw, mustache, fill=style.hair, outline=OUTLINE_SOFT, width=0.5)
    _ellipse(draw, (83.2, y + 4.0), 1.7, 2.8, SKIN_SHADE, outline=OUTLINE_SOFT, width=0.4)


def _paint_eye(draw: ImageDraw.ImageDraw, style: DuoStyle, y: float, brow: float, narrow: float, blink: float) -> None:
    """The left brow and eye (the right ones are their mirror)."""
    b = brow * 1.5
    _line(draw, [(65.5, y - 0.5 - b), (70.5, y - 1.8 - b * 0.3)], style.hair_deep, 1.2)
    _ellipse(draw, (68.0, y + 1.8), 3.0, max(0.4, 2.0 - narrow), EYE_WHITE, outline=OUTLINE_SOFT, width=0.4)
    if blink < 0.9:
        _disc(draw, (68.2, y + 1.9), 0.82, EYE, outline=None)
    else:
        _line(draw, [(65.2, y + 1.8), (71.0, y + 1.8)], EYE, 0.7)


def _head_pieces(img: Image.Image, style: DuoStyle, base: Pose, pose: Pose, neck_xf, head_xf) -> None:
    """The neck, the head base, the eyes (a left one and its mirror), the
    mouth and the beard, carried by the neck's and the head's transforms."""
    n, y = base.neck[1], base.head[1]
    neck = _piece(
        style,
        ("neck",),
        lambda d: _poly(d, [(67.2, n - 1.0), (77.0, n - 1.0), (78.0, n + 8.0), (66.0, n + 8.0)], fill=SKIN_SHADE, outline=OUTLINE_SOFT, width=0.7),
        (_AXIS, n),
    )
    _put(img, neck, neck_xf.pt((_AXIS, n)), neck_xf.deg, "neck")
    head_at, deg = head_xf.pt((_AXIS, y)), head_xf.deg
    _put(img, _piece(style, ("head_base",), lambda d: _paint_head_base(d, style, y), (_AXIS, y)), head_at, deg, "head")
    brow = _rig.q(pose.brow, 0.04)
    blink = min(_rig.q(pose.blink, 0.1), 1.0)
    narrow = 0.8 + base.eye_narrow * 1.8 + blink * 2.6
    if blink < 0.9:
        narrow = min(narrow, 1.6)
    eye = _piece(style, ("eye", brow, round(narrow, 3), blink >= 0.9), lambda d: _paint_eye(d, style, y, brow, narrow, blink), (_AXIS, y), keep=(0.0, 0.0, _AXIS, FRAME_H))
    _put_pair(img, eye, head_xf, (_AXIS, y), "eye")
    mouth = _rig.q(pose.mouth, 0.1)
    mouth_y = y + (10.0 if style.moustache else 8.5)
    part = _piece(style, ("mouth", mouth), lambda d: _arc(d, (_AXIS, mouth_y), 4.0, 2.2 + mouth * 2.4, 20, 160, MOUTH, 1.0), (_AXIS, y))
    _put(img, part, head_at, deg, "mouth")
    if style.beard:
        beard = [(63.2, y + 8.4), (72.0, y + 15.2), (81.2, y + 8.8), (78.0, y + 11.0), (66.5, y + 11.0)]
        _put(img, _piece(style, ("beard",), lambda d: _poly(d, beard, fill=style.hair, outline=OUTLINE, width=0.8), (_AXIS, y)), head_at, deg, "beard")


def _fx(img: Image.Image, style: DuoStyle, key, paint, at: Point, opacity: float, name: str, deg: float = 0.0, pivot: Point = _MID_O) -> None:
    """An effect piece painted at full strength around ``pivot`` (frame
    pixels), placed at ``at`` with its strength as the opacity."""
    _put(img, _piece(style, ("fx",) + tuple(key), paint, pivot), at, deg, name, _clamp01(opacity))


def _effects_back(img: Image.Image, style: DuoStyle, pose: Pose) -> None:
    if pose.converge > 0.02:
        c = (72.0, 69.0)
        _fx(img, style, ("converge_outer",), lambda d: _arc(d, c, 23.0, 28.0, 160, 355, style.accent_light, 1.8), c, pose.converge, "fx_converge_outer", pivot=c)
        _fx(img, style, ("converge_inner",), lambda d: _arc(d, c, 15.0, 20.0, 190, 28, GLOW_VIOLET, 1.2), c, pose.converge * 0.8, "fx_converge_inner", pivot=c)
        for rad, phase, col, nm in ((23.0, 0.0, GLOW_AMBER, "amber"), (18.0, 120.0, style.accent, "accent"), (14.5, 240.0, GLOW_TEAL, "teal")):
            ang = math.radians(pose.converge * 240.0 + phase)
            p = (c[0] + math.cos(ang) * rad, c[1] + math.sin(ang) * rad * 0.8)
            _fx(img, style, ("dot", col), lambda d, col=col: _disc(d, _MID_O, 1.8, col, outline=OUTLINE_SOFT, width=0.4), p, pose.converge, f"fx_dot_{nm}")
    if pose.kernel > 0.02:
        c = (112.0, 52.0)

        def kernel(draw) -> None:
            _poly(draw, [_offset(c, -12.0, -12.0), _offset(c, 12.0, -12.0), _offset(c, 12.0, 12.0), _offset(c, -12.0, 12.0)], fill=None, outline=style.accent_light, width=1.4)
            _poly(draw, [_offset(c, -7.0, -7.0), _offset(c, 7.0, -7.0), _offset(c, 7.0, 7.0), _offset(c, -7.0, 7.0)], fill=None, outline=_fade(GLOW_AMBER, 0.8), width=1.0)
            _line(draw, [_offset(c, -16.0, 0.0), _offset(c, -12.0, 0.0)], GLOW_TEAL, 1.0)
            _line(draw, [_offset(c, 12.0, 0.0), _offset(c, 16.0, 0.0)], GLOW_TEAL, 1.0)

        _fx(img, style, ("kernel",), kernel, c, pose.kernel, "fx_kernel", pivot=c)
    if pose.slope > 0.02:
        x0, y0 = 40.0, 108.0
        step = [(x0, y0), (x0 + 6.0, y0), (x0 + 6.0, y0 - 6.0), (x0 + 12.0, y0 - 6.0), (x0 + 12.0, y0 - 12.0), (x0 + 18.0, y0 - 12.0)]
        _fx(img, style, ("slope_floor",), lambda d: _line(d, step, style.accent_light, 1.5), (x0, y0), pose.slope, "fx_slope_floor", pivot=(x0, y0))


def _effects_front(img: Image.Image, style: DuoStyle, pose: Pose, hand: Point) -> None:
    O = _MID_O
    if pose.stage > 0.02:
        # The streak grows in four lengths; its strength is the opacity.
        sq = max(0.25, _rig.q(pose.stage, 0.25))
        dx, dy = 14.0 + 18.0 * sq, 2.0 + 2.0 * sq
        length = math.hypot(dx, dy)
        start = _offset(hand, 0.0, -1.0)

        def streak(draw) -> None:
            _line(draw, [O, _offset(O, length, 0.0)], GLOW_AMBER, 3.2)
            _line(draw, [O, _offset(O, length, 0.0)], _fade(style.accent_deep, 0.8), 1.0)

        _fx(img, style, ("streak", sq), streak, start, pose.stage, "fx_streak", deg=math.degrees(math.atan2(dy, dx)))

        def impact(draw) -> None:
            _line(draw, [_offset(O, -4.0, 0.0), _offset(O, 4.0, 0.0)], GLOW_RED, 1.0)
            _line(draw, [_offset(O, 0.0, -4.0), _offset(O, 0.0, 4.0)], GLOW_RED, 1.0)

        _fx(img, style, ("impact",), impact, _offset(start, dx + 4.0, dy + 2.0), pose.stage, "fx_impact")
    if pose.slope > 0.02:
        for idx, yoff in enumerate((-7.0, 0.0, 7.0)):
            mid = idx == 1
            pts = [O, _offset(O, 8.0, 0.0), _offset(O, 8.0, -5.0), _offset(O, 16.0, -5.0), _offset(O, 16.0, -10.0), _offset(O, 24.0, -10.0)]
            col, width = (style.accent_light, 1.7) if mid else (GLOW_TEAL, 1.2)
            _fx(img, style, ("slope_step", mid), lambda d, col=col, width=width: _line(d, pts, col, width), _offset(hand, -1.0, yoff), pose.slope, f"fx_slope_{idx}")
    if pose.block > 0.02:
        def block(draw) -> None:
            _arc(draw, O, 13.0, 15.0, 250, 110, style.accent_light, 2.0)
            _arc(draw, O, 9.0, 11.0, 250, 110, _fade(GLOW_TEAL, 0.75), 1.0)

        _fx(img, style, ("block",), block, _offset(hand, 8.0, -1.0), pose.block, "fx_block")
    if pose.taunt > 0.02:
        _fx(img, style, ("taunt",), lambda d: _line(d, [_offset(O, -4.0, 0.0), O, _offset(O, -4.0, 3.0)], GLOW_RED, 1.2), _offset(pose.head, 16.0, -1.5), pose.taunt, "fx_taunt")
    if pose.cheer > 0.02:
        c = (72.0, 22.0)
        _fx(img, style, ("cheer",), lambda d: _arc(d, c, 18.0, 5.0, 0, 359, GLOW_AMBER, 1.4), c, pose.cheer, "fx_cheer", pivot=c)


def _paint_glyphs(draw: ImageDraw.ImageDraw, style: DuoStyle) -> None:
    _line(draw, [(97.0, 63.0), (101.0, 59.0), (106.0, 59.0)], style.accent_light, 1.0)
    _line(draw, [(98.0, 68.0), (101.0, 66.0), (104.0, 68.0)], GLOW_AMBER, 0.9)


def _mid(a: Point, b: Point) -> Point:
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def _carriers(style: DuoStyle, base: Pose, pose: Pose):
    """Where the rest pieces are carried: (pose, upper, skirt, neck, head).
    Standing, the coat's upper half rides the neck's height, the skirt and
    apron the hem's, the neck and head their own. Falling dead, the whole
    body turns over about the hips as one rigid group; its limbs reach the
    painter's ankles and the turned rest hands."""
    if pose.defeat <= 0.0:
        def lift(dy: float):
            return _rig.IDENTITY.translate(0.0, dy)

        return pose, lift(pose.neck[1] - base.neck[1]), lift(_hem(pose) - _hem(base)), lift(pose.neck[1] - base.neck[1]), lift(pose.head[1] - base.head[1])
    rest = _mid(base.near_hip, base.far_hip)
    now = _mid(pose.near_hip, pose.far_hip)
    body = _rig.IDENTITY.rotate_ccw(rest, _DEATH_TURN * pose.defeat).translate(now[0] - rest[0], now[1] - rest[1])
    names = ("head", "neck", "near_shoulder", "far_shoulder", "near_elbow", "far_elbow", "near_hand", "far_hand", "near_hip", "far_hip")
    turned = replace(pose, **{name: body.pt(getattr(base, name)) for name in names})
    return turned, body, body, body, body


def _render_native_frame(style: DuoStyle, animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    base = _make_base_pose(style)
    pose, upper, skirt, neck_xf, head_xf = _carriers(style, base, _pose(style, animation, frame_idx, frame_count))
    image = Image.new("RGBA", _CANVAS, (0, 0, 0, 0))
    _effects_back(image, style, pose)
    _draw_leg(image, style, base, pose, far=True)
    _draw_leg(image, style, base, pose, far=False)
    waist = (_AXIS, _WAIST_CUT)
    skirt_half = _piece(style, ("skirt",), lambda d: _paint_coat(d, style, base), waist, keep=(0.0, _SKIRT_TOP, _AXIS, FRAME_H))
    swing = _rig.IDENTITY.rotate_ccw(waist, 8.0 * pose.coat_swing)
    _put_pair(image, skirt_half, swing._then(skirt.m, skirt.deg), waist, "skirt")
    upper_half = _piece(style, ("coat",), lambda d: _paint_coat(d, style, base), waist, keep=(0.0, 0.0, _AXIS, _WAIST_CUT))
    _put_pair(image, upper_half, upper, waist, "coat")
    apron = _piece(style, ("apron",), lambda d: _paint_apron(d, style, base), waist)
    _put(image, apron, skirt.pt(waist), skirt.deg, "apron")
    if pose.glyphs > 0.02:
        _fx(image, style, ("glyphs",), lambda d: _paint_glyphs(d, style), (100.0, 64.0), pose.glyphs, "fx_glyphs", pivot=(100.0, 64.0))
    hand_deg = upper.deg
    _draw_arm(image, style, base, pose, hand_deg, far=True)
    hand = _draw_arm(image, style, base, pose, hand_deg, far=False)
    _effects_front(image, style, pose, hand)
    _head_pieces(image, style, base, pose, neck_xf, head_xf)
    return image


def render_frame(style: DuoStyle, animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    return rigdoc.downsampled_canvas(
        _render_native_frame(style, animation, frame_idx, frame_count), (FRAME_W, FRAME_H), Image.Resampling.LANCZOS
    )


def _body_metrics_override(fw: int, fh: int):
    return {
        "body_pixel_bbox": {"x": int(fw * 0.22), "y": int(fh * 0.08), "w": int(fw * 0.60), "h": int(fh * 0.84)},
        "feet_pixel": {"x": fw * 0.52, "y": fh * 0.92},
        "feet_anchor_norm": {"x": 0.01, "y": round(0.5 - 0.92, 6)},
    }


def render_target(style: DuoStyle, out_dir: Path) -> List[Path]:
    def render_fn(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
        return render_frame(style, animation, frame_idx, frame_count)

    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=style.target_name,
        rows=ROWS,
        render_fn=render_fn,
        out_dir=Path(out_dir),
        frame_size=(FRAME_W, FRAME_H),
        label_width=112,
        auto_crop=False,
        body_metrics_fn=_body_metrics_override,
        actor_metadata=_make_actor_metadata(style),
        sheet_tuning={"collision_scale": 1.0, "frame_sample_inset": 1},
        animation_key_map={name: name for name, _frames, _duration in ROWS},
        attack_hitboxes={
            "stage_smash": {"bbox": {"x": 84, "y": 60, "w": 54, "h": 36}},
            "slope_lock": {"bbox": {"x": 85, "y": 46, "w": 48, "h": 34}},
            "kernel_seize": {"bbox": {"x": 92, "y": 28, "w": 40, "h": 45}},
            "converge_crush": {"bbox": {"x": 44, "y": 30, "w": 60, "h": 58}},
        },
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    parts = publish_rig_flipbook(style.target_name, ROWS, render_fn, outputs, frame_transform, Path(out_dir))
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())


def render_target_canonical(style: DuoStyle, out_dir: Path) -> Path:
    return write_canonical(
        style.target_name,
        ROWS,
        lambda animation, frame_idx, frame_count: render_frame(style, animation, frame_idx, frame_count),
        Path(out_dir),
        frame_size=(FRAME_W, FRAME_H),
    )


def render_target_portraits(style: DuoStyle, out_dir: Path) -> List[Path]:
    face = FaceGuide(
        center_x=style.face_center_x,
        center_y=style.face_center_y,
        width=style.face_w,
        height=style.face_h,
        source_width=FRAME_W,
        source_height=FRAME_H,
    )

    def portrait_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
        return render_framed_portrait(
            _render_native_frame(style, animation, frame_idx, frame_count),
            face,
            view_width=62.0,
            center_y=43.5,
        )

    clips = {
        "default": PortraitClip.still(portrait_frame("idle", 1, 8)),
        "talking": PortraitClip(tuple(portrait_frame("talk", i, 8) for i in range(8)), duration_ms=112, looping=True),
        "scheming": PortraitClip(tuple(portrait_frame("taunt", i, 8) for i in (1, 3, 5, 7)), duration_ms=112, looping=True),
        "seizing": PortraitClip(tuple(portrait_frame("kernel_seize", i, 10) for i in (2, 4, 6, 8)), duration_ms=94, looping=True),
    }
    return write_portrait_sheet(style.target_name, clips, Path(out_dir))


__all__ = [
    "DuoStyle",
    "ROWS",
    "render_target",
    "render_target_canonical",
    "render_target_portraits",
]
