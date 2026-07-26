"""Procedural sprite target for Georg Canter.

Georg Canter is a transfinite centaur parody of Georg Cantor.  His human half
reads as a severe late-nineteenth-century professor while the equine half gives
"Canter" a literal combat silhouette.  Nested-set tack, aleph ornaments, a
Cantor-diagonal lance, and recursive constellation effects turn set theory into
visible action without requiring the audience to understand the mathematics.

Ambition's humans, animals, machines, monsters, and mixed bodies coexist as an
ordinary fact of the setting.  Georg is a centaur because that is the character;
no bark or scene should stop to explain it.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import math
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont

from ...authoring.sheet_build import build_sheet, write_canonical
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "georg_canter"
FRAME_SIZE = (320, 288)
SUPER = 3
WORK_SIZE = (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER)

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 132),
    ("walk", 8, 92),
    ("talk", 8, 104),
    ("diagonalize", 9, 76),
    ("countable_charge", 8, 74),
    ("power_set", 10, 84),
    ("aleph_rain", 8, 90),
    ("hit", 5, 84),
    ("death", 10, 112),
    ("taunt", 8, 98),
]

AUTHORING_DESCRIPTION = (
    "Georg Canter parodies Georg Cantor, the mathematician who founded modern "
    "set theory and introduced transfinite numbers for comparing different "
    "sizes of infinity. The surname becomes Canter, making him a centaur whose "
    "equine body supplies a strong silhouette and a natural high-mobility combat "
    "identity. His diagonal lance refers to Cantor's diagonal argument; nested "
    "rings, braces, and doubling constellations refer to sets, power sets, and "
    "Cantor's theorem; aleph ornaments refer to transfinite cardinal numbers. "
    "The human half draws loosely from late-nineteenth-century portraits: dark "
    "formal coat, high collar, intense eyes, swept hair, and a full beard, without "
    "reproducing one portrait exactly. He is a direct Cantor parody and is not a "
    "replacement for the separate Genghis Can and Genghis Can't pair. Ambition "
    "treats humans, animals, machines, and mixed bodies as an ordinary society, "
    "so nobody explains or comments on his being a centaur."
)

GAMEPLAY_DESCRIPTION = (
    "A mobile mid-heavy controller who turns increasing cardinality into escalating "
    "space control. His horse body gives him fast grounded acceleration and a long "
    "hurtbox, while the diagonal lance reaches through clustered opponents. "
    "Diagonalize marks one element from each nearby group and then cuts across the "
    "resulting diagonal. Countable Charge leaves a numbered procession of fading "
    "afterimages. Power Set surrounds a marked region with a strictly larger nested "
    "attack pattern, and Aleph Rain drops ordered sigils that become denser over "
    "time. He should feel commanding and inevitable rather than frantic: excellent "
    "at occupying lanes, weaker when crowded from directly above or behind. The "
    "initial catalog entry uses the existing generic swipe action set until these "
    "dedicated mechanics are authored in the unified moveset system."
)

SUGGESTED_BARKS = {
    "on_hit": [
        "You have removed one point, not the set.",
        "Finite irritation.",
        "The argument survives contact.",
    ],
    "provoked": [
        "Very well. Choose a number.",
        "You may begin counting whenever you are ready.",
    ],
    "idle": [
        "Infinity is not a number. It is a crowded neighborhood.",
        "There is always a larger collection.",
        "Count carefully. Then count what counting missed.",
    ],
    "hall": [
        "Some infinities fit inside others and still fail to be the same size.",
        "I can list your options. I can also construct the one you omitted.",
        "The diagonal is not rude. It is conclusive.",
        "Genghis Can and Genghis Can't are not my graduate students.",
    ],
}

FALLBACK_DIALOGUE = [
    "A list may continue forever and still leave something out. The interesting step is constructing the omission rather than merely asserting it.",
    "Given any collection, the collection of all its subcollections is larger. The universe is remarkably consistent about refusing a largest size.",
    "People say infinity as though it were one distant place. I have spent my career explaining that it has districts.",
    "My lance follows the diagonal: one choice from each row, changed just enough that the result cannot already be on the list.",
]

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_georg_canter",
        "display_name": "Georg Canter",
    },
    "body": {
        "body_plan": "Centauroid",
        "body_kind": "Wide",
        "mass_class": "Heavy",
        "traits": [
            "centaur",
            "mathematician",
            "set_theorist",
            "transfinite",
            "lancer",
            "playable_candidate",
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
            "crawl": None,
            "use_lifts": True,
            "door_access": ["public", "wide"],
        },
        "interactions": {
            "talk": True,
            "trade": None,
            "carry": True,
            "open_doors": ["public", "wide"],
        },
    },
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "striker_swipe"},
    "visual": {"default_pose": "idle"},
    "tags": [
        "centaur",
        "mathematician",
        "set_theorist",
        "transfinite",
        "lancer",
        "playable_candidate",
    ],
    "authoring": {
        "authoring_description": AUTHORING_DESCRIPTION,
        "gameplay_description": GAMEPLAY_DESCRIPTION,
        "suggested_barks": SUGGESTED_BARKS,
        "fallback_dialogue": FALLBACK_DIALOGUE,
    },
    "sockets": {
        "head": {
            "source": "explicit.profile.centauroid",
            "point": {"x": 202.0, "y": 57.0},
        },
        "chest": {
            "source": "explicit.profile.centauroid",
            "point": {"x": 203.0, "y": 116.0},
        },
        "hand_l": {
            "source": "explicit.profile.centauroid",
            "point": {"x": 166.0, "y": 139.0},
        },
        "hand_r": {
            "source": "explicit.profile.centauroid",
            "point": {"x": 232.0, "y": 137.0},
        },
        "speech_bubble": {
            "source": "explicit.profile.centauroid",
            "point": {"x": 200.0, "y": 8.0},
        },
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "action.melee.primary": {"animation": "diagonalize", "events": []},
        "action.melee.secondary": {"animation": "countable_charge", "events": []},
        "action.special.primary": {"animation": "power_set", "events": []},
        "action.special.secondary": {"animation": "aleph_rain", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
    },
}

# Palette: academic indigo and gold above a deep chestnut horse body.
OUTLINE = (25, 20, 32, 255)
OUTLINE_SOFT = (56, 44, 65, 255)
HORSE = (112, 61, 42, 255)
HORSE_MID = (147, 82, 53, 255)
HORSE_LIGHT = (187, 113, 70, 255)
HORSE_DARK = (69, 40, 35, 255)
HOOF = (42, 34, 39, 255)
SKIN = (221, 181, 146, 255)
SKIN_LIGHT = (242, 209, 176, 255)
SKIN_DARK = (177, 128, 100, 255)
HAIR = (54, 40, 45, 255)
HAIR_LIGHT = (91, 69, 72, 255)
COAT = (45, 48, 101, 255)
COAT_MID = (68, 73, 139, 255)
COAT_LIGHT = (103, 111, 176, 255)
SHIRT = (239, 234, 216, 255)
VEST = (92, 123, 128, 255)
GOLD = (222, 173, 66, 255)
GOLD_LIGHT = (251, 222, 135, 255)
STEEL = (174, 204, 220, 255)
STEEL_LIGHT = (235, 250, 255, 255)
TRANSFINITE = (116, 218, 232, 255)
TRANSFINITE_DARK = (65, 122, 169, 255)
POWER = (203, 119, 237, 255)
POWER_LIGHT = (237, 194, 255, 255)
EYE = (32, 29, 35, 255)
MOUTH = (118, 59, 65, 255)
TRANSPARENT = (0, 0, 0, 0)


def _s(value: float) -> int:
    return int(round(value * SUPER))


def _pt(point: Point) -> Tuple[int, int]:
    return (_s(point[0]), _s(point[1]))


def _bbox(cx: float, cy: float, rx: float, ry: float) -> Tuple[int, int, int, int]:
    return (_s(cx - rx), _s(cy - ry), _s(cx + rx), _s(cy + ry))


def _fade(color: RGBA, alpha: float) -> RGBA:
    return (color[0], color[1], color[2], max(0, min(255, int(color[3] * alpha))))


def _line(draw: ImageDraw.ImageDraw, points: Sequence[Point], fill: RGBA, width: float) -> None:
    draw.line([_pt(p) for p in points], fill=fill, width=max(1, _s(width)), joint="curve")


def _poly(draw: ImageDraw.ImageDraw, points: Sequence[Point], fill: RGBA, outline: RGBA = OUTLINE, width: float = 1.2) -> None:
    pts = [_pt(p) for p in points]
    draw.polygon(pts, fill=fill)
    if outline[3] > 0:
        draw.line([*pts, pts[0]], fill=outline, width=max(1, _s(width)), joint="curve")


def _ellipse(draw: ImageDraw.ImageDraw, center: Point, rx: float, ry: float, fill: RGBA, outline: RGBA = OUTLINE, width: float = 1.2) -> None:
    draw.ellipse(_bbox(center[0], center[1], rx, ry), fill=fill, outline=outline, width=max(1, _s(width)))


def _arc(draw: ImageDraw.ImageDraw, center: Point, rx: float, ry: float, start: float, end: float, fill: RGBA, width: float) -> None:
    draw.arc(_bbox(center[0], center[1], rx, ry), start=start, end=end, fill=fill, width=max(1, _s(width)))


def _font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", _s(size))
    except Exception:
        return ImageFont.load_default()


def _text(draw: ImageDraw.ImageDraw, xy: Point, text: str, size: int, fill: RGBA, anchor: str = "mm", stroke: RGBA = OUTLINE) -> None:
    draw.text(
        _pt(xy),
        text,
        font=_font(size),
        fill=fill,
        anchor=anchor,
        stroke_width=max(1, _s(0.7)),
        stroke_fill=stroke,
    )


def _ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _pulse(t: float, start: float, peak: float, end: float) -> float:
    if t <= start or t >= end:
        return 0.0
    if t < peak:
        return _ease((t - start) / max(0.001, peak - start))
    return 1.0 - _ease((t - peak) / max(0.001, end - peak))


def _rotate(point: Point, degrees: float) -> Point:
    radians = math.radians(degrees)
    c = math.cos(radians)
    s = math.sin(radians)
    return (point[0] * c - point[1] * s, point[0] * s + point[1] * c)


def _from(origin: Point, length: float, degrees: float) -> Point:
    dx, dy = _rotate((length, 0.0), degrees)
    return (origin[0] + dx, origin[1] + dy)


@dataclass(frozen=True)
class Pose:
    bob: float = 0.0
    stride: float = 0.0
    gallop: float = 0.0
    lean: float = 0.0
    arm_near: float = 42.0
    arm_far: float = 145.0
    lance_angle: float = -24.0
    lance_length: float = 86.0
    mouth: float = 0.0
    blink: float = 0.0
    diagonal: float = 0.0
    charge: float = 0.0
    power_set: float = 0.0
    aleph_rain: float = 0.0
    hit: float = 0.0
    collapse: float = 0.0
    taunt: float = 0.0


def _pose_for(anim: str, frame_idx: int, nframes: int) -> Pose:
    t = frame_idx / max(1, nframes - 1)
    cyc = math.tau * frame_idx / max(1, nframes)
    bob = math.sin(cyc) * 1.1
    blink = 1.0 if anim == "idle" and frame_idx == 5 else 0.0
    if anim == "idle":
        return Pose(bob=bob, arm_near=38.0 + math.sin(cyc) * 3.0, blink=blink)
    if anim == "walk":
        return Pose(
            bob=-abs(math.sin(cyc)) * 2.0,
            stride=math.sin(cyc) * 18.0,
            gallop=0.75,
            lean=-3.0,
            arm_near=32.0 - math.sin(cyc) * 8.0,
            arm_far=150.0 + math.sin(cyc) * 5.0,
            lance_angle=-18.0,
        )
    if anim == "talk":
        return Pose(
            bob=bob * 0.55,
            arm_near=15.0 + math.sin(cyc) * 18.0,
            arm_far=168.0 - math.sin(cyc) * 8.0,
            mouth=0.35 + 0.65 * abs(math.sin(cyc * 1.5)),
        )
    if anim == "diagonalize":
        swing = _pulse(t, 0.08, 0.55, 0.96)
        wind = _ease(min(1.0, t / 0.35))
        return Pose(
            bob=-swing * 2.0,
            lean=-8.0 * swing,
            arm_near=20.0 - swing * 42.0,
            arm_far=150.0,
            lance_angle=-65.0 + wind * 102.0,
            lance_length=96.0,
            diagonal=swing,
        )
    if anim == "countable_charge":
        charge = _pulse(t, 0.05, 0.52, 0.98)
        return Pose(
            bob=-abs(math.sin(cyc)) * 2.8,
            stride=math.sin(cyc * 1.5) * 23.0,
            gallop=1.0,
            lean=-13.0 * charge,
            arm_near=-8.0,
            arm_far=155.0,
            lance_angle=-3.0,
            lance_length=116.0,
            charge=charge,
        )
    if anim == "power_set":
        power = _pulse(t, 0.02, 0.62, 0.98)
        return Pose(
            bob=-power * 4.0,
            lean=2.0,
            arm_near=-78.0 + power * 18.0,
            arm_far=-116.0 - power * 18.0,
            lance_angle=-62.0,
            power_set=power,
            mouth=power * 0.7,
        )
    if anim == "aleph_rain":
        rain = _pulse(t, 0.02, 0.42, 0.98)
        return Pose(
            bob=bob * 0.4,
            arm_near=-82.0,
            arm_far=-132.0,
            lance_angle=-88.0,
            aleph_rain=rain,
            mouth=rain * 0.45,
        )
    if anim == "hit":
        impact = _pulse(t, 0.0, 0.20, 0.98)
        return Pose(
            bob=impact * 3.0,
            lean=14.0 * impact,
            arm_near=65.0,
            arm_far=125.0,
            lance_angle=-5.0,
            hit=impact,
        )
    if anim == "death":
        collapse = _ease(t)
        return Pose(
            bob=collapse * 27.0,
            lean=collapse * 66.0,
            arm_near=58.0,
            arm_far=110.0,
            lance_angle=18.0 + collapse * 35.0,
            collapse=collapse,
            blink=collapse,
        )
    if anim == "taunt":
        taunt = 0.5 + 0.5 * math.sin(cyc)
        return Pose(
            bob=bob * 0.65,
            arm_near=-38.0 + taunt * 12.0,
            arm_far=192.0 - taunt * 18.0,
            lance_angle=-42.0,
            taunt=taunt,
            mouth=0.25 + taunt * 0.4,
        )
    return Pose()


def _leg_points(hip: Point, phase: float, stride: float, collapse: float) -> Tuple[Point, Point]:
    lift = max(0.0, math.sin(phase)) * (7.0 + abs(stride) * 0.14)
    hoof_x = hip[0] + stride * math.cos(phase)
    hoof_y = 266.0 - lift + collapse * 8.0
    knee = (
        hip[0] + (hoof_x - hip[0]) * 0.45 - math.sin(phase) * 4.0,
        hip[1] + (hoof_y - hip[1]) * 0.48,
    )
    return knee, (hoof_x, hoof_y)


def _draw_leg(draw: ImageDraw.ImageDraw, hip: Point, phase: float, stride: float, near: bool, collapse: float) -> None:
    knee, hoof = _leg_points(hip, phase, stride, collapse)
    coat = HORSE_MID if near else HORSE_DARK
    _line(draw, [hip, knee, hoof], OUTLINE, 13.5 if near else 11.5)
    _line(draw, [hip, knee, hoof], coat, 9.0 if near else 7.4)
    _ellipse(draw, knee, 4.3, 4.0, coat, OUTLINE, 0.8)
    hoof_center = (hoof[0] + 1.5, hoof[1] + 1.5)
    _ellipse(draw, hoof_center, 7.2 if near else 6.2, 3.7, HOOF, OUTLINE, 0.8)


def _draw_arm(draw: ImageDraw.ImageDraw, shoulder: Point, angle: float, near: bool) -> Point:
    elbow = _from(shoulder, 26.0, angle)
    hand = _from(elbow, 24.0, angle + (-18.0 if near else 18.0))
    sleeve = COAT_MID if near else COAT
    _line(draw, [shoulder, elbow, hand], OUTLINE, 11.5)
    _line(draw, [shoulder, elbow, hand], sleeve, 7.2)
    _ellipse(draw, hand, 4.8, 4.4, SKIN, OUTLINE, 0.8)
    return hand


def _draw_lance(draw: ImageDraw.ImageDraw, hand: Point, angle: float, length: float, glow: float) -> Point:
    butt = _from(hand, -17.0, angle)
    tip = _from(hand, length, angle)
    if glow > 0.02:
        _line(draw, [butt, tip], _fade(TRANSFINITE, glow * 0.45), 8.0)
    _line(draw, [butt, tip], OUTLINE, 5.0)
    _line(draw, [butt, tip], STEEL, 2.5)
    spear_base = _from(tip, -13.0, angle)
    left = _from(spear_base, 8.0, angle - 90.0)
    right = _from(spear_base, 8.0, angle + 90.0)
    _poly(draw, [tip, left, right], STEEL_LIGHT, OUTLINE, 0.8)
    brace = _from(hand, 17.0, angle)
    _arc(draw, brace, 10.0, 10.0, angle - 150.0, angle + 150.0, GOLD, 2.2)
    return tip


def _draw_recursive_sets(layer: Image.Image, center: Point, amount: float, phase: float) -> None:
    draw = blending_draw(layer)
    for idx in range(4):
        radius = 28.0 + idx * 21.0 + amount * 10.0
        wobble = math.sin(phase + idx * 0.8) * 4.0
        color = POWER if idx % 2 else TRANSFINITE
        alpha = amount * (0.62 - idx * 0.08)
        _arc(draw, (center[0] + wobble, center[1]), radius, radius * 0.72, 190.0, 530.0, _fade(color, alpha), 2.4 + amount)
        _text(draw, (center[0] - radius * 0.88, center[1]), "{", 17, _fade(color, alpha), anchor="mm", stroke=TRANSPARENT)
        _text(draw, (center[0] + radius * 0.88, center[1]), "}", 17, _fade(color, alpha), anchor="mm", stroke=TRANSPARENT)


def _draw_diagonal_field(layer: Image.Image, amount: float, phase: float) -> None:
    draw = blending_draw(layer)
    origin = (86.0, 58.0)
    spacing = 21.0
    for row in range(6):
        for col in range(7):
            x = origin[0] + col * spacing
            y = origin[1] + row * 18.0
            alpha = amount * (0.24 + (0.23 if row == col else 0.0))
            _ellipse(draw, (x, y), 3.0, 3.0, _fade(TRANSFINITE, alpha), TRANSPARENT, 0.1)
    _line(draw, [(origin[0], origin[1]), (origin[0] + 5 * spacing, origin[1] + 5 * 18.0)], _fade(GOLD_LIGHT, amount * 0.78), 3.0)
    for idx in range(6):
        x = origin[0] + idx * spacing
        y = origin[1] + idx * 18.0
        _text(draw, (x + 7.0, y - 7.0), "¬", 8, _fade(POWER_LIGHT, amount * 0.8), stroke=TRANSPARENT)


def _draw_aleph_rain(layer: Image.Image, amount: float, phase: float) -> None:
    draw = blending_draw(layer)
    for idx in range(9):
        x = 52.0 + idx * 29.0 + math.sin(phase + idx) * 5.0
        y = 18.0 + ((idx * 31.0 + phase * 22.0) % 176.0)
        alpha = amount * (0.34 + 0.06 * (idx % 3))
        _text(draw, (x, y), "ℵ", 14 + idx % 3, _fade(TRANSFINITE, alpha), stroke=TRANSPARENT)
        if idx % 2 == 0:
            _text(draw, (x + 8.0, y + 8.0), str(idx // 2), 6, _fade(GOLD_LIGHT, alpha), stroke=TRANSPARENT)


def _render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    pose = _pose_for(anim, frame_idx, nframes)
    phase = math.tau * frame_idx / max(1, nframes)
    image = Image.new("RGBA", WORK_SIZE, TRANSPARENT)

    # Effects are drawn on independent layers so translucent forms blend cleanly.
    behind = Image.new("RGBA", WORK_SIZE, TRANSPARENT)
    if pose.diagonal > 0.01:
        _draw_diagonal_field(behind, pose.diagonal, phase)
    if pose.power_set > 0.01:
        _draw_recursive_sets(behind, (174.0, 135.0), pose.power_set, phase)
    if pose.aleph_rain > 0.01:
        _draw_aleph_rain(behind, pose.aleph_rain, phase)
    if pose.taunt > 0.01:
        draw_behind = blending_draw(behind)
        _arc(draw_behind, (196.0, 70.0), 32.0 + pose.taunt * 6.0, 16.0, 0.0, 360.0, _fade(GOLD_LIGHT, 0.35 + pose.taunt * 0.35), 2.4)
        _text(draw_behind, (196.0, 39.0), "∞", 18, _fade(TRANSFINITE, 0.45 + pose.taunt * 0.5), stroke=TRANSPARENT)
    image.alpha_composite(behind)
    draw = blending_draw(image)

    collapse = pose.collapse
    body_y = 190.0 + pose.bob + collapse * 13.0
    body_x = 162.0 - pose.charge * 8.0

    # Countable-charge afterimages sit behind the body.
    if pose.charge > 0.02:
        trail = Image.new("RGBA", WORK_SIZE, TRANSPARENT)
        trail_draw = blending_draw(trail)
        for idx in range(4):
            offset = 25.0 + idx * 25.0
            alpha = pose.charge * (0.22 - idx * 0.035)
            _ellipse(trail_draw, (body_x - offset, body_y), 58.0, 27.0, _fade(HORSE_LIGHT, alpha), TRANSPARENT, 0.1)
            _text(trail_draw, (body_x - offset, body_y - 37.0), str(idx), 9, _fade(TRANSFINITE, alpha * 2.2), stroke=TRANSPARENT)
        image.alpha_composite(trail)
        draw = blending_draw(image)

    # Tail behind the legs and torso.
    tail_root = (body_x - 64.0, body_y - 4.0)
    tail_tip = (body_x - 101.0 - math.sin(phase) * 10.0, body_y + 24.0 + math.cos(phase) * 7.0)
    tail_mid = ((tail_root[0] + tail_tip[0]) * 0.5, body_y + 4.0 - math.sin(phase) * 8.0)
    _line(draw, [tail_root, tail_mid, tail_tip], OUTLINE, 12.0)
    _line(draw, [tail_root, tail_mid, tail_tip], HORSE_DARK, 7.5)
    _ellipse(draw, tail_tip, 8.0, 10.0, HAIR, OUTLINE, 0.8)

    # Far legs.
    stride = pose.stride
    _draw_leg(draw, (body_x - 45.0, body_y + 12.0), phase + math.pi, stride * 0.76, False, collapse)
    _draw_leg(draw, (body_x + 38.0, body_y + 11.0), phase, stride * 0.76, False, collapse)

    # Horse body and nested-set tack.
    _ellipse(draw, (body_x, body_y), 76.0, 38.0, HORSE, OUTLINE, 1.7)
    _ellipse(draw, (body_x - 25.0, body_y - 10.0), 44.0, 23.0, HORSE_MID, TRANSPARENT, 0.1)
    _ellipse(draw, (body_x + 58.0, body_y - 10.0), 28.0, 31.0, HORSE_MID, OUTLINE, 1.0)
    _arc(draw, (body_x - 10.0, body_y - 1.0), 56.0, 27.0, 190.0, 345.0, GOLD, 3.0)
    for idx, radius in enumerate((12.0, 18.0, 24.0)):
        _arc(draw, (body_x - 5.0, body_y - 3.0), radius, radius * 0.7, 195.0, 525.0, GOLD_LIGHT if idx == 1 else TRANSFINITE_DARK, 1.5)

    # Near legs.
    _draw_leg(draw, (body_x - 28.0, body_y + 14.0), phase, stride, True, collapse)
    _draw_leg(draw, (body_x + 57.0, body_y + 13.0), phase + math.pi, stride, True, collapse)

    # Human torso rises from the horse withers.
    waist = (body_x + 50.0, body_y - 28.0)
    torso_center = (waist[0] + pose.lean * 0.30, waist[1] - 48.0)
    shoulder_y = torso_center[1] - 27.0
    coat_shape = [
        (waist[0] - 22.0, waist[1] + 4.0),
        (torso_center[0] - 28.0, shoulder_y + 5.0),
        (torso_center[0] - 17.0, shoulder_y - 8.0),
        (torso_center[0] + 21.0, shoulder_y - 7.0),
        (waist[0] + 28.0, waist[1] + 4.0),
    ]
    _poly(draw, coat_shape, COAT, OUTLINE, 1.5)
    _poly(
        draw,
        [
            (torso_center[0] - 7.0, shoulder_y - 3.0),
            (torso_center[0] + 10.0, shoulder_y - 3.0),
            (waist[0] + 9.0, waist[1] - 3.0),
            (waist[0] - 8.0, waist[1] - 3.0),
        ],
        VEST,
        OUTLINE_SOFT,
        0.8,
    )
    _line(draw, [(torso_center[0] + 2.0, shoulder_y), (waist[0] + 1.0, waist[1])], GOLD, 1.5)
    for yoff in (8.0, 20.0, 32.0):
        _ellipse(draw, (torso_center[0] + 4.0, shoulder_y + yoff), 1.7, 1.7, GOLD_LIGHT, OUTLINE, 0.4)
    _poly(
        draw,
        [
            (torso_center[0] - 9.0, shoulder_y - 8.0),
            (torso_center[0] + 10.0, shoulder_y - 8.0),
            (torso_center[0] + 4.0, shoulder_y + 7.0),
            (torso_center[0] - 2.0, shoulder_y + 7.0),
        ],
        SHIRT,
        OUTLINE_SOFT,
        0.6,
    )

    far_shoulder = (torso_center[0] - 18.0, shoulder_y + 2.0)
    near_shoulder = (torso_center[0] + 20.0, shoulder_y + 3.0)
    far_hand = _draw_arm(draw, far_shoulder, pose.arm_far + pose.lean * 0.35, False)
    near_hand = _draw_arm(draw, near_shoulder, pose.arm_near + pose.lean * 0.35, True)

    # Neck, face, hair, and beard.
    neck = (torso_center[0] + pose.lean * 0.20, shoulder_y - 14.0)
    _ellipse(draw, neck, 7.0, 12.0, SKIN_DARK, OUTLINE, 0.8)
    head = (neck[0] + pose.lean * 0.16, neck[1] - 28.0)
    _ellipse(draw, head, 18.0, 22.0, SKIN, OUTLINE, 1.2)
    hair_shape = [
        (head[0] - 18.0, head[1] - 6.0),
        (head[0] - 13.0, head[1] - 22.0),
        (head[0] + 3.0, head[1] - 25.0),
        (head[0] + 18.0, head[1] - 14.0),
        (head[0] + 15.0, head[1] - 2.0),
        (head[0] + 9.0, head[1] - 12.0),
        (head[0] - 8.0, head[1] - 13.0),
    ]
    _poly(draw, hair_shape, HAIR, OUTLINE, 0.9)
    _arc(draw, (head[0] - 7.0, head[1] - 8.0), 7.0, 5.0, 205.0, 345.0, HAIR_LIGHT, 1.3)
    _arc(draw, (head[0] + 6.0, head[1] - 9.0), 7.0, 5.0, 195.0, 338.0, HAIR_LIGHT, 1.3)

    eye_y = head[1] - 1.0
    eye_h = 0.6 if pose.blink > 0.4 else 2.1
    _ellipse(draw, (head[0] - 6.0, eye_y), 2.4, eye_h, EYE, EYE, 0.1)
    _ellipse(draw, (head[0] + 6.0, eye_y), 2.4, eye_h, EYE, EYE, 0.1)
    _line(draw, [(head[0] - 10.0, eye_y - 6.0), (head[0] - 3.0, eye_y - 7.5)], HAIR, 1.5)
    _line(draw, [(head[0] + 3.0, eye_y - 7.5), (head[0] + 11.0, eye_y - 6.0)], HAIR, 1.5)
    _poly(
        draw,
        [(head[0] + 1.0, head[1] + 1.0), (head[0] + 6.0, head[1] + 7.0), (head[0] + 1.0, head[1] + 9.0)],
        SKIN_DARK,
        OUTLINE_SOFT,
        0.4,
    )
    beard = [
        (head[0] - 14.0, head[1] + 7.0),
        (head[0] - 10.0, head[1] + 23.0),
        (head[0], head[1] + 35.0),
        (head[0] + 13.0, head[1] + 21.0),
        (head[0] + 15.0, head[1] + 7.0),
        (head[0] + 7.0, head[1] + 11.0),
        (head[0], head[1] + 9.0),
        (head[0] - 7.0, head[1] + 11.0),
    ]
    _poly(draw, beard, HAIR, OUTLINE, 0.8)
    if pose.mouth > 0.08:
        _ellipse(draw, (head[0] + 1.0, head[1] + 13.0), 3.2, 1.2 + pose.mouth * 2.6, MOUTH, OUTLINE, 0.4)
    else:
        _line(draw, [(head[0] - 3.0, head[1] + 13.0), (head[0] + 5.0, head[1] + 12.5)], MOUTH, 0.8)

    # Aleph brooch and lance are foreground readability anchors.
    _ellipse(draw, (torso_center[0] + 1.0, shoulder_y + 10.0), 8.0, 8.0, COAT_LIGHT, GOLD, 1.4)
    _text(draw, (torso_center[0] + 1.0, shoulder_y + 10.0), "ℵ", 8, GOLD_LIGHT, stroke=TRANSPARENT)
    lance_glow = max(pose.diagonal, pose.charge, pose.power_set, pose.aleph_rain)
    tip = _draw_lance(draw, near_hand, pose.lance_angle + pose.lean * 0.15, pose.lance_length, lance_glow)

    if pose.diagonal > 0.04:
        front = Image.new("RGBA", WORK_SIZE, TRANSPARENT)
        fd = blending_draw(front)
        slash_end = _from(tip, 60.0, pose.lance_angle + 50.0)
        _line(fd, [_from(tip, -72.0, pose.lance_angle + 50.0), slash_end], _fade(GOLD_LIGHT, pose.diagonal * 0.72), 5.5)
        _line(fd, [_from(tip, -65.0, pose.lance_angle + 50.0), slash_end], _fade(TRANSFINITE, pose.diagonal * 0.76), 2.3)
        image.alpha_composite(front)

    if pose.hit > 0.04:
        hit_layer = Image.new("RGBA", WORK_SIZE, TRANSPARENT)
        hd = blending_draw(hit_layer)
        center = (body_x + 8.0, body_y - 40.0)
        for deg in range(0, 360, 45):
            _line(hd, [_from(center, 18.0, deg), _from(center, 38.0 + pose.hit * 12.0, deg)], _fade(POWER_LIGHT, pose.hit * 0.82), 3.0)
        image.alpha_composite(hit_layer)

    return image.resize(FRAME_SIZE, Image.Resampling.LANCZOS)


def _body_metrics_override(frame_width: int, frame_height: int):
    return {
        "body_pixel_bbox": {
            "x": int(frame_width * 0.14),
            "y": int(frame_height * 0.06),
            "w": int(frame_width * 0.78),
            "h": int(frame_height * 0.88),
        },
        "feet_pixel": {"x": frame_width * 0.53, "y": frame_height * 0.93},
        "feet_anchor_norm": {"x": 0.03, "y": round(0.5 - 0.93, 6)},
    }


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=_render_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        label_width=118,
        auto_crop=False,
        trim=False,
        body_metrics_fn=_body_metrics_override,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning={"collision_scale": 1.12, "frame_sample_inset": 2},
        animation_key_map={name: name for name, _frames, _duration in ROWS},
        attack_hitboxes={
            "diagonalize": {"bbox": {"x": 126, "y": 48, "w": 184, "h": 165}},
            "countable_charge": {"bbox": {"x": 173, "y": 103, "w": 142, "h": 104}},
            "power_set": {"bbox": {"x": 58, "y": 35, "w": 238, "h": 216}},
            "aleph_rain": {"bbox": {"x": 38, "y": 18, "w": 258, "h": 232}},
        },
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


def render_canonical(out_dir: str | Path, **opts) -> Path:
    del opts
    return write_canonical(
        TARGET_NAME,
        ROWS,
        _render_frame,
        Path(out_dir),
        frame_size=FRAME_SIZE,
    )


__all__ = [
    "ACTOR_METADATA",
    "AUTHORING_DESCRIPTION",
    "FALLBACK_DIALOGUE",
    "GAMEPLAY_DESCRIPTION",
    "ROWS",
    "SUGGESTED_BARKS",
    "render",
    "render_canonical",
]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "out_dir",
        nargs="?",
        type=Path,
        default=Path("generated") / TARGET_NAME,
    )
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
