"""Willson — a pelican and bicycle authored as one composite actor.

The target is fully procedural Python.  Rider and bicycle have independent
pose transforms inside one sprite entity, allowing Willson to step off, carry
the bicycle while flying, and separate from it during the death fall without
creating a second gameplay actor.  Wheel rotation uses deliberately asymmetric
geometry so motion remains visible from frame to frame.

Publish:

    PYTHONPATH=tools/ambition_sprite2d_renderer \
      python -m ambition_sprite2d_renderer publish willson
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Mapping, Sequence, Tuple

from PIL import Image, ImageColor, ImageDraw

from ...authoring.sheet_build import build_sheet, write_canonical
from ambition_sprite2d_renderer.core.draw import blending_draw

Color = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "willson"
FRAME_W, FRAME_H = 256, 256
SS = 4
TAU = math.tau

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 140),
    ("walk", 8, 78),
    ("slash", 8, 72),
    ("fly", 8, 86),
    ("taunt", 6, 108),
    ("hurt", 4, 94),
    ("death", 10, 92),
]
LOOPS = {"idle", "walk", "fly"}

ACTOR_METADATA = {
    "actor": {
        "character_id": TARGET_NAME,
        "display_name": "Willson",
    },
    "body": {
        "body_plan": "AvianCyclist",
        "body_kind": "Grounded",
        "traits": [
            "pelican",
            "bicycle_bound",
            "inseparable_composite_actor",
            "dismount_animation",
            "aerial_bicycle_carry",
            "pedal_locomotion",
            "beak_melee",
            "expressive",
        ],
    },
    "visual": {
        "default_pose": "idle",
        "facing_policy": "side_right",
    },
    "provenance": {
        "variant_family": TARGET_NAME,
        "variant_id": "gpt_5_6_composite_motion_polish_2026_07_15",
        "lineage": [
            {
                "revision_id": "human_concept_2026_07_15",
                "creator_kind": "human",
                "creator": "project_author",
                "contribution": "character_name_and_pelican_riding_a_bicycle_concept",
                "date": "2026-07-15",
            },
            {
                "revision_id": "gpt_5_6_initial_sprite_2026_07_15",
                "creator_kind": "model",
                "creator": "gpt-5.6-thinking",
                "contribution": "procedural_sprite_design_animation_and_python_implementation",
                "parent_revision_id": "human_concept_2026_07_15",
                "date": "2026-07-15",
            },
            {
                "revision_id": "gpt_5_6_composite_motion_polish_2026_07_15",
                "creator_kind": "model",
                "creator": "gpt-5.6-thinking",
                "contribution": "dismounted_idle_readable_wheel_motion_violent_attack_flight_and_rider_bicycle_separation",
                "parent_revision_id": "gpt_5_6_initial_sprite_2026_07_15",
                "date": "2026-07-15",
            },
        ],
    },
    "tags": ["npc", "avian", "cyclist", "custom", "beak_melee"],
}


def _rgba(value: str, alpha: int = 255) -> Color:
    r, g, b = ImageColor.getrgb(value)
    return (r, g, b, alpha)


PAL: Dict[str, Color] = {
    "outline": _rgba("#101921"),
    "tire": _rgba("#18212A"),
    "tire_hi": _rgba("#394753"),
    "rim": _rgba("#B9CDD1"),
    "spoke": _rgba("#789098"),
    "bike_dark": _rgba("#12505A"),
    "bike": _rgba("#168A91"),
    "bike_hi": _rgba("#49C7BE"),
    "brass": _rgba("#D9A52E"),
    "brass_hi": _rgba("#FFE27A"),
    "leather": _rgba("#6F3F28"),
    "leather_hi": _rgba("#B56D3E"),
    "feather_dark": _rgba("#A8B0AD"),
    "feather": _rgba("#E9E6D8"),
    "feather_hi": _rgba("#FFFDF0"),
    "wing": _rgba("#D4D4C8"),
    "wing_hi": _rgba("#F4F1E2"),
    "bill_dark": _rgba("#C34D22"),
    "bill": _rgba("#F0782C"),
    "bill_hi": _rgba("#FFB04A"),
    "pouch": _rgba("#F6A548"),
    "pouch_hi": _rgba("#FFD37A"),
    "leg": _rgba("#D95E2C"),
    "leg_hi": _rgba("#FF9A4B"),
    "eye": _rgba("#14202A"),
    "eye_hi": _rgba("#EAF9FF"),
    "scarf": _rgba("#B53A3F"),
    "scarf_hi": _rgba("#F06C62"),
    "satchel": _rgba("#8B5533"),
    "satchel_hi": _rgba("#D18A4D"),
}


# Stable painter ordering.  The bicycle lives behind the rider; the near foot
# and wing live in front; the hand-grip and facial marks close the stack.
LAYER_Z: Dict[str, int] = {
    "wheels": 10,
    "far_crank": 20,
    "bike_frame": 30,
    "tail": 40,
    "far_wing": 45,
    "far_leg": 48,
    "body": 50,
    "satchel": 54,
    "neck": 58,
    "head": 62,
    "beak": 66,
    "near_leg": 72,
    "near_wing": 78,
    "handle_details": 82,
    "face_details": 86,
    "accents": 90,
}

LAYER_RELATIONS: Tuple[Tuple[str, str], ...] = (
    ("bike_frame", "wheels"),
    ("body", "far_wing"),
    ("body", "bike_frame"),
    ("near_leg", "body"),
    ("near_wing", "body"),
    ("near_wing", "bike_frame"),
    ("handle_details", "near_wing"),
    ("face_details", "head"),
    ("accents", "near_wing"),
)


def _validate_layer_z(layer_z: Mapping[str, int]) -> None:
    if set(layer_z) != set(LAYER_Z):
        raise ValueError(f"layer set changed: expected={sorted(LAYER_Z)}, got={sorted(layer_z)}")
    values = list(layer_z.values())
    if len(values) != len(set(values)):
        raise ValueError("every Willson layer must have a unique z value")
    for upper, lower in LAYER_RELATIONS:
        if layer_z[upper] <= layer_z[lower]:
            raise ValueError(f"layer contract requires {upper!r} above {lower!r}")


_validate_layer_z(LAYER_Z)


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _ease(t: float) -> float:
    t = _clamp(t)
    return t * t * (3.0 - 2.0 * t)


def _pulse(t: float, start: float, peak: float, end: float) -> float:
    if t <= start or t >= end:
        return 0.0
    if t <= peak:
        return _ease((t - start) / max(1e-6, peak - start))
    return 1.0 - _ease((t - peak) / max(1e-6, end - peak))


def _rot(point: Point, degrees: float) -> Point:
    x, y = point
    r = math.radians(degrees)
    c, s = math.cos(r), math.sin(r)
    return (x * c - y * s, x * s + y * c)


def _around(point: Point, pivot: Point, degrees: float) -> Point:
    q = _rot((point[0] - pivot[0], point[1] - pivot[1]), degrees)
    return (q[0] + pivot[0], q[1] + pivot[1])


def _add(a: Point, b: Point) -> Point:
    return (a[0] + b[0], a[1] + b[1])


def _sub(a: Point, b: Point) -> Point:
    return (a[0] - b[0], a[1] - b[1])


def _mul(a: Point, value: float) -> Point:
    return (a[0] * value, a[1] * value)


def _norm(a: Point) -> Point:
    length = math.hypot(a[0], a[1]) or 1.0
    return (a[0] / length, a[1] / length)


def _perp(a: Point) -> Point:
    return (-a[1], a[0])


def _ellipse_points(center: Point, rx: float, ry: float, angle: float = 0.0, steps: int = 40) -> List[Point]:
    out: List[Point] = []
    for idx in range(steps):
        theta = TAU * idx / steps
        q = (rx * math.cos(theta), ry * math.sin(theta))
        out.append(_add(center, _rot(q, angle)))
    return out


class VDraw:
    def __init__(self, image: Image.Image, scale: int) -> None:
        self.image = image
        self.draw = blending_draw(image)
        self.scale = scale

    def point(self, point: Point) -> Point:
        return (point[0] * self.scale, point[1] * self.scale)

    def points(self, points: Iterable[Point]) -> List[Point]:
        return [self.point(p) for p in points]

    def line(self, points: Sequence[Point], fill: Color, width: float, joint: str = "curve") -> None:
        self.draw.line(
            self.points(points),
            fill=fill,
            width=max(1, int(round(width * self.scale))),
            joint=joint,
        )

    def polygon(
        self,
        points: Sequence[Point],
        fill: Color,
        outline: Color | None = None,
        width: float = 1.0,
    ) -> None:
        pts = self.points(points)
        self.draw.polygon(pts, fill=fill)
        if outline is not None:
            self.draw.line(
                pts + [pts[0]],
                fill=outline,
                width=max(1, int(round(width * self.scale))),
                joint="curve",
            )

    def ellipse(
        self,
        center: Point,
        rx: float,
        ry: float,
        fill: Color,
        outline: Color | None = None,
        width: float = 1.0,
        angle: float = 0.0,
    ) -> None:
        self.polygon(_ellipse_points(center, rx, ry, angle), fill, outline, width)

    def circle(
        self,
        center: Point,
        radius: float,
        fill: Color,
        outline: Color | None = None,
        width: float = 1.0,
    ) -> None:
        x, y = self.point(center)
        r = radius * self.scale
        self.draw.ellipse(
            (x - r, y - r, x + r, y + r),
            fill=fill,
            outline=outline,
            width=max(1, int(round(width * self.scale))),
        )

    def ring(self, center: Point, radius: float, fill: Color, width: float) -> None:
        x, y = self.point(center)
        r = radius * self.scale
        self.draw.ellipse(
            (x - r, y - r, x + r, y + r),
            outline=fill,
            width=max(1, int(round(width * self.scale))),
        )


BASE = {
    "rear_hub": (65.0, 201.0),
    "front_hub": (190.0, 201.0),
    "crank": (126.0, 187.0),
    "seat_post": (108.0, 151.0),
    "head_top": (168.0, 153.0),
    "head_bottom": (176.0, 178.0),
    "handle_left": (160.0, 132.0),
    "handle_right": (184.0, 130.0),
    "body_center": (112.0, 108.0),
    "rider_pivot": (114.0, 137.0),
    "head_center": (151.0, 63.0),
    "far_shoulder": (99.0, 99.0),
    "near_shoulder": (127.0, 101.0),
    "far_hip": (105.0, 134.0),
    "near_hip": (120.0, 136.0),
}


def _pose(animation: str, frame_idx: int, nframes: int) -> Dict[str, float]:
    loop = animation in LOOPS
    t = frame_idx / max(1, nframes) if loop else frame_idx / max(1, nframes - 1)
    phase = TAU * t
    pose: Dict[str, float] = {
        "t": t,
        "phase": phase,
        "wheel_angle": 0.0,
        "wheel_motion": 0.0,
        "pedal_angle": -52.0,
        "bike_angle": 0.0,
        "bike_dx": 0.0,
        "bike_dy": 0.0,
        "body_bob": 0.0,
        "body_lean": 0.0,
        "body_dx": 0.0,
        "head_bob": 0.0,
        "head_dx": 0.0,
        "head_dy": 0.0,
        "beak_extend": 0.0,
        "beak_open": 0.0,
        "near_wing_raise": 0.0,
        "far_wing_raise": 0.0,
        "blink": 0.0,
        "scarf_lift": 0.0,
        "slump": 0.0,
        "bell_ring": 0.0,
        "dismount": 0.0,
        "flight": 0.0,
        "flight_flap": 0.0,
        "attack_force": 0.0,
        "death_fall": 0.0,
        "rider_bike_inherit": 1.0,
        "rider_dx": 0.0,
        "rider_dy": 0.0,
        "rider_angle": 0.0,
    }

    if animation == "idle":
        # One continuous mount/dismount cycle.  The midpoint is a stable
        # dismounted pose: both feet are grounded and one wing holds the
        # tilted bicycle ready to launch.
        dismount = 0.5 - 0.5 * math.cos(phase)
        settling = math.sin(phase * 2.0)
        pose.update(
            dismount=dismount,
            rider_bike_inherit=1.0 - dismount,
            rider_dx=-27.0 * dismount,
            rider_dy=27.0 * dismount,
            rider_angle=3.5 * dismount,
            wheel_angle=18.0 * math.sin(phase * 0.5),
            wheel_motion=0.18 * (1.0 - dismount),
            pedal_angle=-52.0 + 26.0 * dismount + 3.0 * settling,
            bike_angle=-5.5 * dismount,
            bike_dx=8.0 * dismount,
            body_bob=0.7 * settling,
            body_lean=2.5 * dismount,
            head_bob=0.8 * math.sin(phase + 0.4),
            near_wing_raise=0.10 + 0.18 * dismount,
            far_wing_raise=0.10 * dismount,
            blink=1.0 if frame_idx == 5 else 0.0,
            scarf_lift=0.08 * (1.0 + math.sin(phase)),
        )
    elif animation == "walk":
        # Five spokes make 72 degrees the symmetry interval.  Deliberately
        # advance by 58.5 degrees per frame so no adjacent frame aliases.
        pose.update(
            wheel_angle=468.0 * t,
            wheel_motion=1.0,
            pedal_angle=360.0 * t - 42.0,
            body_bob=1.9 * math.sin(phase * 2.0),
            body_lean=-6.0 + 1.8 * math.sin(phase),
            head_bob=1.4 * math.sin(phase * 2.0 + 0.5),
            scarf_lift=0.70 + 0.20 * math.sin(phase + 0.7),
        )
    elif animation == "slash":
        windup = _pulse(t, 0.00, 0.20, 0.43)
        strike = _pulse(t, 0.16, 0.51, 0.88)
        impact = _pulse(t, 0.38, 0.55, 0.72)
        pose.update(
            wheel_angle=95.0 * t + 38.0 * strike,
            wheel_motion=0.35 + 0.85 * strike,
            pedal_angle=-36.0 + 72.0 * t,
            bike_angle=6.0 * windup - 14.0 * strike + 4.0 * impact,
            bike_dx=-7.0 * windup + 8.0 * strike,
            bike_dy=2.0 * windup + 4.0 * strike,
            body_dx=-6.0 * windup + 5.0 * strike,
            body_lean=10.0 * windup - 12.0 * strike,
            body_bob=3.0 * windup + 2.0 * strike,
            head_dx=-4.0 * windup + 8.0 * strike,
            head_dy=2.0 * windup + 1.0 * strike,
            head_bob=-3.0 * strike,
            beak_extend=25.0 * strike,
            beak_open=0.82 * windup + 0.28 * strike,
            near_wing_raise=0.72 * windup + 0.28 * strike,
            far_wing_raise=0.45 * windup + 0.16 * strike,
            scarf_lift=0.25 * windup + 0.95 * strike,
            attack_force=impact,
        )
    elif animation == "fly":
        flap = math.sin(phase)
        pose.update(
            flight=1.0,
            flight_flap=flap,
            rider_bike_inherit=0.0,
            rider_dx=-4.0,
            rider_dy=-20.0 + 3.0 * math.sin(phase * 2.0),
            rider_angle=-13.0 + 2.5 * math.sin(phase),
            bike_dx=-4.0,
            bike_dy=5.0 + 1.8 * math.sin(phase * 2.0 + 0.8),
            bike_angle=-4.0 + 1.5 * math.sin(phase + 0.5),
            wheel_angle=540.0 * t,
            wheel_motion=0.85,
            pedal_angle=180.0 * t - 20.0,
            body_bob=-2.0 * flap,
            head_bob=-1.2 * flap,
            beak_open=0.08 + 0.05 * max(0.0, flap),
            scarf_lift=0.95 + 0.18 * flap,
        )
    elif animation == "taunt":
        call = math.sin(math.pi * t) ** 2
        pose.update(
            wheel_angle=3.0 * math.sin(phase),
            pedal_angle=-48.0,
            body_bob=-1.2 * call,
            body_lean=3.0 * call,
            head_bob=-5.0 * call,
            beak_open=0.85 * call,
            near_wing_raise=0.72 * call,
            bell_ring=math.sin(phase * 3.0) * call,
            scarf_lift=0.25 * call,
        )
    elif animation == "hurt":
        envelope = math.sin(math.pi * t)
        wobble = math.sin(TAU * t * 1.5)
        pose.update(
            wheel_angle=24.0 * t,
            wheel_motion=0.25 * envelope,
            pedal_angle=-20.0 + 14.0 * t,
            bike_angle=5.5 * wobble * envelope,
            bike_dx=-5.0 * envelope,
            body_lean=12.0 * wobble * envelope,
            body_bob=-3.0 * envelope,
            head_bob=3.0 * envelope,
            beak_open=0.22 * envelope,
            near_wing_raise=0.35 * envelope,
            far_wing_raise=0.25 * envelope,
            scarf_lift=0.35 * envelope,
            blink=0.7 * envelope,
        )
    elif animation == "death":
        fall = _ease(_clamp((t - 0.10) / 0.90))
        kick = _pulse(t, 0.05, 0.22, 0.50)
        pose.update(
            death_fall=fall,
            rider_bike_inherit=1.0 - fall,
            rider_dx=-28.0 * fall,
            rider_dy=57.0 * fall,
            rider_angle=-70.0 * fall,
            wheel_angle=170.0 * t + 30.0 * kick,
            wheel_motion=0.70 * (1.0 - fall),
            pedal_angle=-34.0 + 80.0 * t,
            bike_angle=-4.0 * kick - 14.0 * fall,
            bike_dx=23.0 * fall,
            bike_dy=8.0 * fall,
            body_dx=-4.0 * kick,
            body_bob=-4.0 * kick,
            body_lean=-10.0 * kick,
            head_bob=3.0 * fall,
            beak_open=0.42 * kick + 0.18 * fall,
            near_wing_raise=0.30 * kick + 0.90 * fall,
            far_wing_raise=0.25 * kick + 0.75 * fall,
            scarf_lift=0.55 * kick + 0.65 * fall,
            slump=fall,
            blink=fall,
        )
    else:
        raise KeyError(animation)
    return pose


def _bike_xf(pose: Mapping[str, float], point: Point) -> Point:
    pivot = BASE["rear_hub"]
    p = _around(point, pivot, pose["bike_angle"])
    return (p[0] + pose["bike_dx"], p[1] + pose["bike_dy"])


def _rider_xf(pose: Mapping[str, float], point: Point) -> Point:
    pivot = BASE["rider_pivot"]
    p = _around(point, pivot, pose["body_lean"])
    p = (p[0] + pose["body_dx"], p[1] + pose["body_bob"])
    p = _around(p, pivot, pose["rider_angle"])
    independent = (p[0] + pose["rider_dx"], p[1] + pose["rider_dy"])
    attached = _bike_xf(pose, independent)
    inherit = _clamp(pose["rider_bike_inherit"])
    return (
        _lerp(independent[0], attached[0], inherit),
        _lerp(independent[1], attached[1], inherit),
    )


def _rider_shape(pose: Mapping[str, float], points: Iterable[Point]) -> List[Point]:
    return [_rider_xf(pose, p) for p in points]


def _bike_shape(pose: Mapping[str, float], points: Iterable[Point]) -> List[Point]:
    return [_bike_xf(pose, p) for p in points]


def _pedal_points(pose: Mapping[str, float]) -> Tuple[Point, Point]:
    center = BASE["crank"]
    angle = math.radians(pose["pedal_angle"])
    radius = 16.0
    near = (center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle))
    far = (center[0] - radius * math.cos(angle), center[1] - radius * math.sin(angle))
    return _bike_xf(pose, near), _bike_xf(pose, far)


def _knee(hip: Point, foot: Point, bend: float) -> Point:
    delta = _sub(foot, hip)
    direction = _norm(delta)
    normal = _perp(direction)
    mid = _add(hip, _mul(delta, 0.52))
    reach = math.hypot(delta[0], delta[1])
    bulge = max(8.0, 22.0 - reach * 0.12)
    return _add(mid, _mul(normal, bend * bulge))


def _draw_wheel(v: VDraw, center: Point, spin_deg: float, motion: float) -> None:
    radius = 32.5
    # Five spokes deliberately break the old 45-degree visual aliasing.
    for idx in range(5):
        angle = math.radians(spin_deg + idx * 72.0)
        p = (center[0] + 27.5 * math.cos(angle), center[1] + 27.5 * math.sin(angle))
        v.line([center, p], PAL["spoke"], 1.35)

    # A brass valve and paired teal rim marks make rotation readable even when
    # the wheel silhouette itself remains fixed in screen space.
    valve_angle = math.radians(spin_deg + 17.0)
    valve = (center[0] + 29.1 * math.cos(valve_angle), center[1] + 29.1 * math.sin(valve_angle))
    v.circle(valve, 1.8, PAL["brass_hi"], PAL["outline"], 0.55)
    for offset_deg in (116.0, 132.0):
        angle = math.radians(spin_deg + offset_deg)
        tangent = (-math.sin(angle), math.cos(angle))
        p = (center[0] + 28.4 * math.cos(angle), center[1] + 28.4 * math.sin(angle))
        v.line([_add(p, _mul(tangent, -4.5)), _add(p, _mul(tangent, 4.5))], PAL["bike_hi"], 1.6)

    v.ring(center, 28.2, PAL["rim"], 2.1)
    v.ring(center, radius, PAL["tire"], 5.3)
    v.ring(center, radius - 2.1, PAL["tire_hi"], 0.9)
    v.circle(center, 3.3, PAL["brass"], PAL["outline"], 0.9)

    # Geometric streaks, never raster blur.  Their tangent direction changes
    # with wheel phase, so they reinforce rather than obscure rotation.
    if motion > 0.05:
        alpha = int(100 + 110 * _clamp(motion))
        streak_color = (*PAL["rim"][:3], alpha)
        for idx in range(3):
            angle = math.radians(spin_deg + 28.0 + idx * 118.0)
            tangent = (-math.sin(angle), math.cos(angle))
            p = (center[0] + 35.5 * math.cos(angle), center[1] + 35.5 * math.sin(angle))
            length = 4.0 + 5.0 * motion
            v.line([_add(p, _mul(tangent, -length)), _add(p, _mul(tangent, length))], streak_color, 1.15)


def _paint_wheels(v: VDraw, pose: Mapping[str, float]) -> None:
    motion = pose["wheel_motion"]
    _draw_wheel(v, _bike_xf(pose, BASE["rear_hub"]), pose["wheel_angle"], motion)
    _draw_wheel(v, _bike_xf(pose, BASE["front_hub"]), pose["wheel_angle"] + 13.0, motion)


def _paint_far_crank(v: VDraw, pose: Mapping[str, float]) -> None:
    crank = _bike_xf(pose, BASE["crank"])
    _, far = _pedal_points(pose)
    v.line([crank, far], PAL["bike_dark"], 3.2)
    tangent = _norm(_perp(_sub(far, crank)))
    v.line([_add(far, _mul(tangent, -6.0)), _add(far, _mul(tangent, 6.0))], PAL["outline"], 2.6)


def _tube(v: VDraw, pose: Mapping[str, float], a: Point, b: Point, width: float = 5.0, highlight: bool = True) -> None:
    aa, bb = _bike_xf(pose, a), _bike_xf(pose, b)
    v.line([aa, bb], PAL["outline"], width + 2.2)
    v.line([aa, bb], PAL["bike"], width)
    if highlight:
        offset = _mul(_norm(_perp(_sub(bb, aa))), -1.2)
        v.line([_add(aa, offset), _add(bb, offset)], PAL["bike_hi"], 1.1)


def _paint_bike_frame(v: VDraw, pose: Mapping[str, float]) -> None:
    rear = BASE["rear_hub"]
    front = BASE["front_hub"]
    crank = BASE["crank"]
    seat = BASE["seat_post"]
    ht = BASE["head_top"]
    hb = BASE["head_bottom"]
    _tube(v, pose, rear, crank)
    _tube(v, pose, crank, hb)
    _tube(v, pose, hb, rear)
    _tube(v, pose, crank, seat, 4.6)
    _tube(v, pose, seat, ht, 4.6)
    _tube(v, pose, ht, hb, 5.0)
    _tube(v, pose, ht, front, 4.2, highlight=False)
    _tube(v, pose, hb, front, 3.5, highlight=False)

    # Saddle, chain ring, and handlebar are all structural bike layers.
    saddle = _bike_shape(pose, [(98, 148), (119, 147), (123, 151), (100, 153)])
    v.polygon(saddle, PAL["leather"], PAL["outline"], 1.2)
    v.line([_bike_xf(pose, (109, 151)), _bike_xf(pose, (109, 145))], PAL["outline"], 3.5)
    v.circle(_bike_xf(pose, crank), 10.0, PAL["bike_dark"], PAL["outline"], 1.2)
    v.ring(_bike_xf(pose, crank), 7.1, PAL["brass"], 1.6)

    stem = _bike_xf(pose, (170, 132))
    v.line([_bike_xf(pose, ht), stem], PAL["outline"], 5.4)
    v.line([_bike_xf(pose, ht), stem], PAL["bike_hi"], 3.0)
    v.line(
        [_bike_xf(pose, BASE["handle_left"]), _bike_xf(pose, BASE["handle_right"])],
        PAL["outline"],
        4.6,
    )
    v.line(
        [_bike_xf(pose, BASE["handle_left"]), _bike_xf(pose, BASE["handle_right"])],
        PAL["bike_dark"],
        2.5,
    )


def _paint_tail(v: VDraw, pose: Mapping[str, float]) -> None:
    lift = pose["scarf_lift"]
    feathers = [
        [(90, 119), (65, 126 - 4 * lift), (81, 136), (102, 127)],
        [(92, 114), (71, 111 - 6 * lift), (83, 127), (104, 124)],
        [(94, 122), (74, 140 - 2 * lift), (96, 136), (108, 126)],
    ]
    for idx, feather in enumerate(feathers):
        fill = PAL["feather_dark"] if idx != 1 else PAL["wing"]
        v.polygon(_rider_shape(pose, feather), fill, PAL["outline"], 1.0)

    # A short scarf gives the ride animation a readable speed cue.
    scarf = [(93, 78), (76, 77 - 6 * lift), (62, 84 - 9 * lift), (81, 88), (96, 86)]
    v.polygon(_rider_shape(pose, scarf), PAL["scarf"], PAL["outline"], 1.1)
    stripe = _rider_shape(pose, [(78, 80), (71, 82), (77, 86), (84, 84)])
    v.polygon(stripe, PAL["scarf_hi"], None)


def _wing_poly(shoulder: Point, hand: Point, lift: float, side: str) -> List[Point]:
    delta = _sub(hand, shoulder)
    direction = _norm(delta)
    normal = _perp(direction)
    sign = -1.0 if side == "far" else 1.0
    elbow = _add(_add(shoulder, _mul(delta, 0.48)), _mul(normal, sign * (11.0 + 7.0 * lift)))
    return [
        _add(shoulder, _mul(normal, -6.0)),
        _add(elbow, _mul(normal, -8.0)),
        _add(hand, _mul(normal, -4.0)),
        _add(hand, _mul(normal, 4.2)),
        _add(elbow, _mul(normal, 7.0)),
        _add(shoulder, _mul(normal, 6.5)),
    ]


def _flight_wing_local(side: str, flap: float) -> List[Point]:
    if side == "far":
        shoulder = (99.0, 99.0)
        tip = (47.0, 78.0 - 33.0 * flap)
        elbow = (74.0, 84.0 - 21.0 * flap)
        return [
            shoulder,
            (88.0, 91.0),
            (elbow[0] + 3.0, elbow[1] - 11.0),
            (tip[0], tip[1]),
            (56.0, tip[1] + 14.0),
            (70.0, elbow[1] + 17.0),
            (93.0, 108.0),
        ]
    shoulder = (127.0, 101.0)
    tip = (63.0, 63.0 - 39.0 * flap)
    elbow = (94.0, 77.0 - 25.0 * flap)
    return [
        shoulder,
        (116.0, 91.0),
        (elbow[0] + 6.0, elbow[1] - 14.0),
        (tip[0], tip[1]),
        (70.0, tip[1] + 17.0),
        (82.0, elbow[1] + 21.0),
        (113.0, 113.0),
    ]


def _paint_far_wing(v: VDraw, pose: Mapping[str, float]) -> None:
    if pose["flight"] > 0.5:
        points = _rider_shape(pose, _flight_wing_local("far", pose["flight_flap"]))
        v.polygon(points, PAL["feather_dark"], PAL["outline"], 1.4)
        v.line(points[1:5], PAL["wing"], 1.6)
        return

    shoulder = _rider_xf(pose, BASE["far_shoulder"])
    death = pose["death_fall"]
    dismount = pose["dismount"]
    handle = _bike_xf(pose, (162.0, 132.0 - 7.0 * pose["far_wing_raise"]))
    rest = _rider_xf(pose, (88.0, 125.0))
    tumble = _rider_xf(pose, (73.0, 85.0))
    target = (
        _lerp(_lerp(handle[0], rest[0], dismount), tumble[0], death),
        _lerp(_lerp(handle[1], rest[1], dismount), tumble[1], death),
    )
    poly = _wing_poly(shoulder, target, pose["far_wing_raise"], "far")
    v.polygon(poly, PAL["feather_dark"], PAL["outline"], 1.2)
    v.line([shoulder, target], PAL["wing"], 2.2)


def _draw_leg(v: VDraw, pose: Mapping[str, float], side: str) -> None:
    near_pedal, far_pedal = _pedal_points(pose)
    if side == "near":
        hip = _rider_xf(pose, BASE["near_hip"])
        pedal = near_pedal
        ground = (102.0, 221.0)
        flight_grip = _bike_xf(pose, (132.0, 158.0))
        tumble = _rider_xf(pose, (138.0, 170.0))
        bend = -1.0
    else:
        hip = _rider_xf(pose, BASE["far_hip"])
        pedal = far_pedal
        ground = (82.0, 221.0)
        flight_grip = _bike_xf(pose, (109.0, 155.0))
        tumble = _rider_xf(pose, (91.0, 174.0))
        bend = 1.0

    dismount = pose["dismount"]
    flight = pose["flight"]
    death = pose["death_fall"]
    foot = (
        _lerp(pedal[0], ground[0], dismount),
        _lerp(pedal[1], ground[1], dismount),
    )
    foot = (
        _lerp(foot[0], flight_grip[0], flight),
        _lerp(foot[1], flight_grip[1], flight),
    )
    foot = (
        _lerp(foot[0], tumble[0], death),
        _lerp(foot[1], tumble[1], death),
    )

    knee = _knee(hip, foot, bend)
    outer = PAL["outline"]
    inner = PAL["leg"] if side == "far" else PAL["leg_hi"]
    v.line([hip, knee, foot], outer, 7.2)
    v.line([hip, knee, foot], inner, 4.4)

    # The webbing remains readable whether it is on a pedal, on the ground,
    # wrapped around the airborne bicycle frame, or flung free in the fall.
    if dismount > 0.55:
        tangent = (1.0, 0.0)
    elif flight > 0.5:
        tangent = _norm(_sub(_bike_xf(pose, (145.0, 150.0)), _bike_xf(pose, (98.0, 150.0))))
    elif death > 0.45:
        tangent = _norm(_sub(foot, knee))
    else:
        crank = _bike_xf(pose, BASE["crank"])
        tangent = _norm(_perp(_sub(foot, crank)))
    normal = _perp(tangent)
    web = [
        _add(foot, _mul(tangent, -5.0)),
        _add(_add(foot, _mul(tangent, 7.5)), _mul(normal, -4.0)),
        _add(_add(foot, _mul(tangent, 8.5)), _mul(normal, 0.0)),
        _add(_add(foot, _mul(tangent, 7.0)), _mul(normal, 4.2)),
        _add(foot, _mul(tangent, -4.0)),
    ]
    v.polygon(web, inner, PAL["outline"], 1.0)


def _paint_far_leg(v: VDraw, pose: Mapping[str, float]) -> None:
    _draw_leg(v, pose, "far")


def _paint_body(v: VDraw, pose: Mapping[str, float]) -> None:
    body = _rider_shape(pose, _ellipse_points(BASE["body_center"], 29.0, 37.0, -6.0))
    v.polygon(body, PAL["feather"], PAL["outline"], 1.6)
    belly = _rider_shape(pose, _ellipse_points((119.0, 116.0), 17.0, 24.0, -7.0))
    v.polygon(belly, PAL["feather_hi"], None)
    breast_mark = _rider_shape(pose, [(125, 88), (139, 101), (135, 117), (128, 108)])
    v.polygon(breast_mark, PAL["wing"], None)


def _paint_satchel(v: VDraw, pose: Mapping[str, float]) -> None:
    strap = _rider_shape(pose, [(96, 82), (101, 80), (130, 136), (124, 138)])
    v.polygon(strap, PAL["leather"], PAL["outline"], 0.8)
    bag = _rider_shape(pose, [(84, 113), (105, 109), (114, 131), (91, 137), (82, 128)])
    v.polygon(bag, PAL["satchel"], PAL["outline"], 1.2)
    flap = _rider_shape(pose, [(84, 113), (104, 110), (108, 120), (87, 124)])
    v.polygon(flap, PAL["satchel_hi"], PAL["outline"], 0.8)
    # W badge makes the name legible without writing text into the sprite.
    badge = _rider_shape(pose, [(90, 119), (93, 129), (97, 123), (101, 128), (104, 116)])
    v.line(badge, PAL["brass_hi"], 1.7)


def _paint_neck(v: VDraw, pose: Mapping[str, float]) -> None:
    head_shift = pose["head_bob"]
    hx, hdy = pose["head_dx"], pose["head_dy"]
    points = [
        (126, 91),
        (139 + hx * 0.30, 84 + hdy * 0.30),
        (140 + hx * 0.70, 72 + head_shift * 0.35 + hdy * 0.70),
        (149 + hx, 68 + head_shift + hdy),
    ]
    world = _rider_shape(pose, points)
    v.line(world, PAL["outline"], 22.0)
    v.line(world, PAL["feather"], 18.2)
    hi = _rider_shape(
        pose,
        [(130, 88), (141 + hx * 0.35, 81 + hdy * 0.35), (143 + hx * 0.72, 72 + head_shift * 0.4 + hdy * 0.72)],
    )
    v.line(hi, PAL["feather_hi"], 5.2)


def _paint_head(v: VDraw, pose: Mapping[str, float]) -> None:
    center = (
        BASE["head_center"][0] + pose["head_dx"],
        BASE["head_center"][1] + pose["head_bob"] + pose["head_dy"],
    )
    head = _rider_shape(pose, _ellipse_points(center, 17.0, 16.0, -5.0))
    v.polygon(head, PAL["feather"], PAL["outline"], 1.4)
    hx = pose["head_dx"]
    hy = pose["head_bob"] + pose["head_dy"]
    crown = _rider_shape(
        pose,
        [(137 + hx, 54 + hy), (145 + hx, 45 + hy), (149 + hx, 54 + hy), (157 + hx, 47 + hy), (158 + hx, 58 + hy)],
    )
    v.polygon(crown, PAL["feather_hi"], PAL["outline"], 0.8)


def _beak_shapes(pose: Mapping[str, float]) -> Tuple[List[Point], List[Point]]:
    ext = pose["beak_extend"]
    opening = 8.0 * pose["beak_open"]
    hx = pose["head_dx"]
    hy = pose["head_bob"] + pose["head_dy"]
    upper = [
        (158 + hx, 62 + hy - opening * 0.45),
        (215 + hx + ext, 65 + hy - opening * 0.35),
        (222 + hx + ext, 70 + hy),
        (160 + hx, 75 + hy),
    ]
    pouch = [
        (159 + hx, 73 + hy),
        (221 + hx + ext, 71 + hy + opening * 0.25),
        (205 + hx + ext * 0.72, 95 + hy + opening),
        (172 + hx, 91 + hy + opening * 0.55),
        (160 + hx, 81 + hy),
    ]
    return _rider_shape(pose, upper), _rider_shape(pose, pouch)


def _paint_beak(v: VDraw, pose: Mapping[str, float]) -> None:
    upper, pouch = _beak_shapes(pose)
    v.polygon(pouch, PAL["pouch"], PAL["outline"], 1.3)
    v.polygon(upper, PAL["bill"], PAL["outline"], 1.3)
    # Bill ridge and pouch fold clarify the two masses at game scale.
    v.line([upper[0], upper[1], upper[2]], PAL["bill_hi"], 1.5)
    v.line([pouch[0], pouch[1], pouch[2]], PAL["pouch_hi"], 1.2)


def _paint_near_leg(v: VDraw, pose: Mapping[str, float]) -> None:
    _draw_leg(v, pose, "near")
    crank = _bike_xf(pose, BASE["crank"])
    near, _ = _pedal_points(pose)
    v.line([crank, near], PAL["outline"], 3.7)
    v.line([crank, near], PAL["brass"], 2.2)


def _paint_near_wing(v: VDraw, pose: Mapping[str, float]) -> None:
    if pose["flight"] > 0.5:
        points = _rider_shape(pose, _flight_wing_local("near", pose["flight_flap"]))
        v.polygon(points, PAL["wing"], PAL["outline"], 1.5)
        v.line(points[1:5], PAL["wing_hi"], 2.0)
        # Long primary-feather seams make the flap readable after downsample.
        shoulder = _rider_xf(pose, BASE["near_shoulder"])
        for local_tip in _flight_wing_local("near", pose["flight_flap"])[3:6]:
            tip = _rider_xf(pose, local_tip)
            v.line([shoulder, _add(shoulder, _mul(_norm(_sub(tip, shoulder)), 36.0))], PAL["feather_dark"], 0.8)
        return

    shoulder = _rider_xf(pose, BASE["near_shoulder"])
    lift = pose["near_wing_raise"]
    handle = _bike_xf(pose, (181.0 - 5.0 * lift, 130.0 - 17.0 * lift))
    # Dismounted Willson still owns the bicycle: his near wing stays on the
    # handle while his body and feet move off the saddle.
    dismounted_handle = _bike_xf(pose, (178.0, 130.0))
    tumble = _rider_xf(pose, (151.0, 74.0))
    death = pose["death_fall"]
    target = (
        _lerp(_lerp(handle[0], dismounted_handle[0], pose["dismount"]), tumble[0], death),
        _lerp(_lerp(handle[1], dismounted_handle[1], pose["dismount"]), tumble[1], death),
    )
    poly = _wing_poly(shoulder, target, lift, "near")
    v.polygon(poly, PAL["wing"], PAL["outline"], 1.4)
    inner = [
        shoulder,
        _add(shoulder, _mul(_norm(_sub(target, shoulder)), 18.0)),
        _add(target, (-5.0, 2.0)),
    ]
    v.line(inner, PAL["wing_hi"], 2.3)
    v.circle(target, 4.2, PAL["wing_hi"], PAL["outline"], 1.0)


def _paint_handle_details(v: VDraw, pose: Mapping[str, float]) -> None:
    left = _bike_xf(pose, BASE["handle_left"])
    right = _bike_xf(pose, BASE["handle_right"])
    v.line([left, _add(left, (-5.0, 0.8))], PAL["leather"], 4.2)
    v.line([right, _add(right, (5.0, -0.5))], PAL["leather"], 4.2)
    bell_center = _bike_xf(pose, (170.0, 127.0 + pose["bell_ring"]))
    v.circle(bell_center, 4.5, PAL["brass"], PAL["outline"], 1.0)
    v.circle(_add(bell_center, (-1.0, -1.0)), 1.2, PAL["brass_hi"], None)
    v.line([_add(bell_center, (3.8, 1.5)), _add(bell_center, (7.0, 4.0))], PAL["outline"], 1.1)


def _paint_face_details(v: VDraw, pose: Mapping[str, float]) -> None:
    hx = pose["head_dx"]
    hy = pose["head_bob"] + pose["head_dy"]
    eye = _rider_xf(pose, (156.0 + hx, 59.0 + hy))
    blink = _clamp(pose["blink"])
    if blink > 0.55:
        v.line([_add(eye, (-3.2, 0.5)), _add(eye, (3.0, -0.2))], PAL["eye"], 1.8)
    else:
        v.circle(eye, 3.3, PAL["eye"], PAL["outline"], 0.7)
        v.circle(_add(eye, (1.0, -1.2)), 0.9, PAL["eye_hi"], None)
    brow = _rider_shape(pose, [(151 + hx, 54 + hy), (160 + hx, 53 + hy)])
    v.line(brow, PAL["feather_dark"], 1.4)


def _paint_accents(v: VDraw, pose: Mapping[str, float]) -> None:
    seams = [
        [(111, 89), (116, 103)],
        [(103, 93), (106, 109)],
        [(119, 96), (126, 112)],
    ]
    for seam in seams:
        v.line(_rider_shape(pose, seam), PAL["feather_dark"], 0.8)

    attack = pose["attack_force"]
    if attack > 0.05:
        hx = pose["head_dx"]
        hy = pose["head_bob"] + pose["head_dy"]
        tip = _rider_xf(pose, (222.0 + hx + pose["beak_extend"], 70.0 + hy))
        for idx, dy in enumerate((-13.0, 0.0, 13.0)):
            length = 15.0 + idx * 4.0
            end = _add(tip, (-length, dy * 0.34))
            start = _add(end, (-15.0 - 8.0 * attack, -dy * 0.10))
            v.line([start, end], PAL["bill_hi"] if idx == 1 else PAL["pouch_hi"], 2.2 - idx * 0.25)
        rear = _bike_xf(pose, BASE["rear_hub"])
        for dx, dy in ((-9, -3), (-13, 2), (-7, 6)):
            v.line([_add(rear, (dx, dy)), _add(rear, (dx - 7.0 * attack, dy + 3.0))], PAL["brass_hi"], 1.5)

    if pose["flight"] > 0.5:
        # Thin horizontal air cuts are geometric motion cues, not shadows or
        # blur effects.  They stay behind the beak and bicycle silhouette.
        for idx, (x, y) in enumerate(((33, 88), (25, 114), (43, 145))):
            wobble = 4.0 * math.sin(pose["phase"] + idx)
            v.line([(x, y + wobble), (x + 21 + 5 * idx, y + wobble)], PAL["rim"], 1.0)

    if pose["death_fall"] > 0.20:
        # Loose feathers emphasize that the rider has actually separated from
        # the bike.  They follow the rider, not the bicycle transform.
        fall = pose["death_fall"]
        for local in ((108, 76), (91, 96), (123, 119)):
            center = _rider_xf(pose, local)
            v.ellipse(_add(center, (-8.0 * fall, -5.0 * fall)), 4.5, 1.8, PAL["wing_hi"], PAL["outline"], 0.6, -20.0)


PAINTERS: Dict[str, Callable[[VDraw, Mapping[str, float]], None]] = {
    "wheels": _paint_wheels,
    "far_crank": _paint_far_crank,
    "bike_frame": _paint_bike_frame,
    "tail": _paint_tail,
    "far_wing": _paint_far_wing,
    "far_leg": _paint_far_leg,
    "body": _paint_body,
    "satchel": _paint_satchel,
    "neck": _paint_neck,
    "head": _paint_head,
    "beak": _paint_beak,
    "near_leg": _paint_near_leg,
    "near_wing": _paint_near_wing,
    "handle_details": _paint_handle_details,
    "face_details": _paint_face_details,
    "accents": _paint_accents,
}


def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    pose = _pose(animation, frame_idx, nframes)
    image = Image.new("RGBA", (FRAME_W * SS, FRAME_H * SS), (0, 0, 0, 0))
    vector = VDraw(image, SS)
    for name in sorted(PAINTERS, key=LAYER_Z.__getitem__):
        PAINTERS[name](vector, pose)
    return image.resize((FRAME_W, FRAME_H), Image.Resampling.LANCZOS)


def _body_metrics_override(fw: int, fh: int):
    return {
        "body_pixel_bbox": {
            "x": int(fw * 0.11),
            "y": int(fh * 0.15),
            "w": int(fw * 0.82),
            "h": int(fh * 0.78),
        },
        "feet_pixel": {"x": fw * 0.50, "y": fh * 0.925},
        "feet_anchor_norm": {"x": 0.0, "y": round(0.5 - 0.925, 6)},
    }


def render(out_dir: Path, **opts) -> List[Path]:
    del opts
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=Path(out_dir),
        frame_size=(FRAME_W, FRAME_H),
        label_width=100,
        auto_crop=False,
        body_metrics_fn=_body_metrics_override,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning={"collision_scale": 1.0, "frame_sample_inset": 1},
        animation_key_map={name: name for name, _frames, _duration in ROWS},
        attack_hitboxes={"slash": {"bbox": {"x": 142, "y": 30, "w": 112, "h": 96}}},
    )
    keys = (
        "spritesheet",
        "yaml",
        "ron",
        "actor",
        "canonical",
        "canonical_transparent",
        "preview",
    )
    return [Path(outputs[key]) for key in keys if outputs.get(key)]


def render_canonical(out_dir: Path, **opts) -> Path:
    del opts
    return write_canonical(
        TARGET_NAME,
        ROWS,
        render_frame,
        Path(out_dir),
        frame_size=(FRAME_W, FRAME_H),
    )


def _source_uses_forbidden_raster_effects() -> bool:
    forbidden_globals = ("ImageFilter", "GaussianBlur", "BoxBlur")
    return any(name in globals() for name in forbidden_globals)
