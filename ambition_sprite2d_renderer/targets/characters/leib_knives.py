"""Procedural sprite target for Gottfried Leib-Knives.

Leib-Knives is a human courtly duelist parody of Gottfried Wilhelm Leibniz.
His two narrow blades turn the calculus notation associated with Leibniz into a
combat silhouette: one blade draws differentials and the other completes broad
integral sweeps.  The large dark peruke, lace cravat, burgundy court coat, and
measured fencing posture are inspired by late-seventeenth-century portraits,
without attempting to reproduce any one portrait.

Ambition's people, animals, machines, monsters, and stranger bodies coexist as
an ordinary fact of the setting.  Leib-Knives is human because that silhouette
serves this design; neither his dialogue nor anyone else's should treat that as
noteworthy.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont

from ...authoring import rigdoc
from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.sheet_build import build_sheet, write_canonical
from ambition_sprite2d_renderer.core.draw import blending_draw
from . import _colonial_statesman_rig
from . import _solo_shape_rig as SR

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "leib_knives"
FRAME_SIZE = (256, 288)
WORK_FRAME_SIZE = (512, 576)
SUPER = 3

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 132),
    ("walk", 8, 96),
    ("talk", 8, 106),
    ("slash", 7, 70),
    ("crosscut", 8, 66),
    ("integral_sweep", 9, 72),
    ("notation", 8, 92),
    ("block", 6, 82),
    ("hit", 5, 86),
    ("death", 8, 110),
    ("taunt", 8, 96),
]

AUTHORING_DESCRIPTION = (
    "Gottfried Leib-Knives parodies Gottfried Wilhelm Leibniz, the German "
    "mathematician, philosopher, and polymath associated with the development "
    "of differential and integral calculus and with the d/dx and integral "
    "notation that became standard. The name turns Leibniz into Leib-Knives: "
    "a courtly dual-blade duelist whose paired weapons draw differentials and "
    "integral curves. His long dark curled peruke, lace cravat, formal coat, "
    "and diplomatic bearing are inspired by late-seventeenth-century portraits. "
    "The recurring priority-dispute jokes refer to Leibniz and Isaac Newton "
    "developing calculus independently and later partisans arguing over credit. "
    "The design should remain affectionate rather than depicting him as merely "
    "a plagiarist. Ambition treats humans, animals, machines, and fantastic "
    "figures as an ordinary mixed society, so his being human is never itself "
    "a joke or a subject of dialogue."
)

GAMEPLAY_DESCRIPTION = (
    "A light precision duelist built around two complementary blades. Fast "
    "differential cuts apply short-lived marks that represent local change; a "
    "wide integral sweep cashes accumulated marks into displacement and damage. "
    "Crosscut is a compact anti-rush tool, while notation creates a brief "
    "calculus glyph that alters the trajectory or timing of the next attack. "
    "He should reward spacing, sequencing, and exact timing rather than raw "
    "durability. The initial catalog entry uses the existing generic swipe kit "
    "until those mechanics receive dedicated runtime actions."
)

SUGGESTED_BARKS = {
    "on_hit": [
        "An infinitesimal cut still counts.",
        "You have mistaken notation for weakness.",
        "That was neither necessary nor sufficient.",
    ],
    "provoked": ["Very well. Let us differentiate."],
    "idle": [
        "A small difference, correctly placed, decides everything.",
        "I developed this stance independently.",
        "Good notation is a weapon against confusion.",
    ],
    "hall": [
        "Two blades, one calculus. The priority dispute is ongoing.",
        "My notation survived. I consider that a point.",
        "The best of all possible move sets is still being balanced.",
    ],
}

FALLBACK_DIALOGUE = [
    "I prefer notation that reveals the operation instead of concealing it. A symbol should do useful work.",
    "GNU Ton and I reached similar techniques by different roads. Posterity then paved the roads with arguments.",
    "A derivative tells you how quickly the present is becoming the future. In a duel, that is practical information.",
    "An integral gathers countless small changes into one result. Do not stand inside the result.",
]

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_leib_knives",
        "display_name": "Gottfried Leib-Knives",
    },
    "dialogue_hints": {
        "suggested_barks": [
            'An infinitesimal cut still counts.',
            'You have mistaken notation for weakness.',
            'That was neither necessary nor sufficient.',
            'Very well. Let us differentiate.',
        ],
        "fallback_dialogue": [
            'I prefer notation that reveals the operation instead of concealing it. A symbol should do useful work.',
            'GNU Ton and I reached similar techniques by different roads. Posterity then paved the roads with arguments.',
            'A derivative tells you how quickly the present is becoming the future. In a duel, that is practical information.',
            'An integral gathers countless small changes into one result. Do not stand inside the result.',
        ],
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": [
            "human",
            "mathematician",
            "polymath",
            "courtly_duelist",
            "dual_blades",
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
            "door_access": ["public"],
        },
        "interactions": {
            "talk": True,
            "trade": None,
            "carry": None,
            "open_doors": ["public"],
        },
    },
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "striker_swipe"},
    "visual": {"default_pose": "idle"},
    "tags": [
        "human",
        "mathematician",
        "polymath",
        "courtly_duelist",
        "dual_blades",
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
            "source": "explicit.profile.humanoid",
            "point": {"x": 127.0, "y": 58.0},
        },
        "chest": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 126.0, "y": 132.0},
        },
        "hand_l": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 92.0, "y": 162.0},
        },
        "hand_r": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 160.0, "y": 160.0},
        },
        "speech_bubble": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 127.0, "y": 12.0},
        },
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "action.melee.primary": {"animation": "slash", "events": []},
        "action.melee.secondary": {"animation": "crosscut", "events": []},
        "action.special.primary": {"animation": "integral_sweep", "events": []},
        "action.special.secondary": {"animation": "notation", "events": []},
        "action.defense.block": {"animation": "block", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
    },
}

OUTLINE = (29, 20, 25, 255)
OUTLINE_SOFT = (62, 42, 48, 255)
SKIN = (222, 184, 151, 255)
SKIN_LIGHT = (241, 207, 176, 255)
SKIN_SHADE = (181, 137, 112, 255)
BLUSH = (201, 133, 124, 110)
WIG = (58, 38, 35, 255)
WIG_MID = (88, 59, 52, 255)
WIG_LIGHT = (127, 88, 73, 255)
COAT = (92, 31, 48, 255)
COAT_DARK = (54, 22, 36, 255)
COAT_LIGHT = (138, 47, 69, 255)
WAISTCOAT = (42, 105, 110, 255)
WAISTCOAT_LIGHT = (71, 145, 146, 255)
CRAVAT = (245, 239, 221, 255)
BREECH = (215, 196, 161, 255)
BREECH_FAR = (183, 165, 137, 255)
STOCKING = (236, 228, 205, 255)
BOOT = (48, 31, 31, 255)
GOLD = (226, 181, 77, 255)
GOLD_LIGHT = (249, 222, 139, 255)
STEEL = (191, 214, 226, 255)
STEEL_LIGHT = (239, 250, 255, 255)
STEEL_DARK = (91, 120, 139, 255)
CALCULUS_BLUE = (101, 207, 224, 255)
CALCULUS_GOLD = (245, 197, 90, 255)
MOUTH = (115, 62, 67, 255)
EYE = (39, 31, 30, 255)


def _s(value: float) -> int:
    return int(round(value * SUPER))


def _pt(point: Point) -> Tuple[int, int]:
    return (_s(point[0]), _s(point[1]))


def _box(cx: float, cy: float, rx: float, ry: float) -> Tuple[int, int, int, int]:
    return (_s(cx - rx), _s(cy - ry), _s(cx + rx), _s(cy + ry))


def _rot(x: float, y: float, degrees: float) -> Point:
    radians = math.radians(degrees)
    c = math.cos(radians)
    s = math.sin(radians)
    return (x * c - y * s, x * s + y * c)


def _lerp(a: float, b: float, amount: float) -> float:
    return a + (b - a) * amount


def _ease(amount: float) -> float:
    amount = max(0.0, min(1.0, amount))
    return amount * amount * (3.0 - 2.0 * amount)


def _pulse(amount: float) -> float:
    return math.sin(max(0.0, min(1.0, amount)) * math.pi)


def _fade(color: RGBA, alpha: float) -> RGBA:
    return (color[0], color[1], color[2], int(color[3] * max(0.0, min(1.0, alpha))))


def _poly(
    draw: ImageDraw.ImageDraw,
    points: Sequence[Point],
    fill: RGBA,
    outline: RGBA | None = OUTLINE,
    width: float = 1.0,
) -> None:
    pts = [_pt(point) for point in points]
    draw.polygon(pts, fill=fill)
    if outline is not None and width > 0:
        draw.line(pts + [pts[0]], fill=outline, width=max(1, _s(width)), joint="curve")


def _line(
    draw: ImageDraw.ImageDraw,
    points: Sequence[Point],
    fill: RGBA,
    width: float = 1.0,
) -> None:
    draw.line([_pt(point) for point in points], fill=fill, width=max(1, _s(width)), joint="curve")


def _ellipse(
    draw: ImageDraw.ImageDraw,
    center: Point,
    rx: float,
    ry: float,
    fill: RGBA,
    outline: RGBA | None = OUTLINE,
    width: float = 1.0,
) -> None:
    draw.ellipse(
        _box(center[0], center[1], rx, ry),
        fill=fill,
        outline=outline,
        width=max(1, _s(width)) if outline is not None else 1,
    )


def _arc(
    draw: ImageDraw.ImageDraw,
    center: Point,
    rx: float,
    ry: float,
    start: float,
    end: float,
    fill: RGBA,
    width: float,
) -> None:
    draw.arc(_box(center[0], center[1], rx, ry), start, end, fill=fill, width=max(1, _s(width)))


def _font(size: float) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", _s(size))
    except Exception:
        return ImageFont.load_default()


class Pose:
    def __init__(self, animation: str, frame_idx: int, nframes: int) -> None:
        t = frame_idx / max(1, nframes - 1)
        cycle = math.tau * frame_idx / max(1, nframes)
        s = math.sin(cycle)
        c = math.cos(cycle)

        self.root_x = 0.0
        self.root_y = 0.0
        self.bob = 0.0
        self.tilt = 0.0
        self.head = 0.0
        self.left_arm = -3.0
        self.right_arm = 3.0
        self.left_leg = 0.0
        self.right_leg = 0.0
        self.left_lift = 0.0
        self.right_lift = 0.0
        self.coat_sway = 0.0
        self.cravat = 0.0
        self.mouth = 0.0
        self.blink = False
        self.x_eye = False
        self.near_blade = 1.0
        self.far_blade = 1.0
        self.near_angle = -12.0
        self.far_angle = 18.0
        self.slash = 0.0
        self.crosscut = 0.0
        self.integral = 0.0
        self.notation = 0.0
        self.block = 0.0
        self.taunt = 0.0

        if animation == "idle":
            self.bob = s * 1.3
            self.tilt = s * 1.0
            self.head = -1.5 + s * 0.8
            self.left_arm = -4.0 + s * 2.0
            self.right_arm = 4.0 - s * 1.8
            self.left_leg = -2.0 + c
            self.right_leg = 2.0 - c
            self.coat_sway = s * 2.2
            self.cravat = max(0.0, s) * 1.5
            self.near_angle = -16.0 + s * 2.0
            self.far_angle = 20.0 - s * 2.0
            self.blink = frame_idx in {nframes - 2}
        elif animation == "walk":
            self.root_x = s * 1.8
            self.bob = abs(s) * 2.4 - 0.4
            self.tilt = s * 2.0
            self.head = -1.0 - s * 0.8
            self.left_leg = -23.0 * s
            self.right_leg = 21.0 * s
            self.left_lift = max(0.0, -s) * 7.0
            self.right_lift = max(0.0, s) * 7.0
            self.left_arm = 10.0 * s - 5.0
            self.right_arm = -10.0 * s + 5.0
            self.coat_sway = -s * 7.0
            self.near_angle = -18.0 - s * 12.0
            self.far_angle = 22.0 + s * 10.0
        elif animation == "talk":
            self.bob = s * 0.8
            self.tilt = -1.0 + s * 0.5
            self.head = -2.0 + s * 1.0
            self.left_arm = _lerp(-5.0, 26.0, _pulse(t))
            self.right_arm = -2.0
            self.mouth = 0.35 + 0.45 * max(0.0, s)
            self.coat_sway = s * 1.0
            self.near_blade = 0.0
            self.near_angle = -30.0
        elif animation == "slash":
            attack = _pulse(t)
            advance = _ease(min(1.0, t * 1.45))
            self.root_x = -7.0 + advance * 25.0
            self.bob = -attack * 2.5
            self.tilt = -8.0 + attack * 17.0
            self.head = -4.0 + attack * 6.0
            self.left_arm = -18.0 + attack * 78.0
            self.right_arm = 8.0 - attack * 24.0
            self.left_leg = -10.0 + attack * 18.0
            self.right_leg = 8.0 - attack * 8.0
            self.coat_sway = 8.0 - attack * 20.0
            self.near_angle = -62.0 + attack * 128.0
            self.far_angle = 24.0
            self.slash = attack
        elif animation == "crosscut":
            attack = _pulse(t)
            self.root_x = -4.0 + attack * 10.0
            self.bob = -attack * 2.0
            self.tilt = -4.0 + attack * 6.0
            self.left_arm = -24.0 + attack * 70.0
            self.right_arm = 24.0 - attack * 70.0
            self.left_leg = -6.0 + attack * 8.0
            self.right_leg = 6.0 - attack * 8.0
            self.coat_sway = -attack * 9.0
            self.near_angle = -76.0 + attack * 110.0
            self.far_angle = 78.0 - attack * 110.0
            self.crosscut = attack
        elif animation == "integral_sweep":
            attack = _pulse(t)
            progress = _ease(t)
            self.root_x = -8.0 + progress * 20.0
            self.bob = -attack * 3.0
            self.tilt = -11.0 + progress * 22.0
            self.head = -6.0 + progress * 8.0
            self.left_arm = -28.0 + progress * 88.0
            self.right_arm = 12.0 - progress * 34.0
            self.left_leg = -12.0 + progress * 22.0
            self.right_leg = 10.0 - progress * 12.0
            self.coat_sway = 11.0 - progress * 24.0
            self.near_angle = -88.0 + progress * 175.0
            self.far_angle = 40.0 - progress * 48.0
            self.integral = attack
        elif animation == "notation":
            rise = _pulse(t)
            self.bob = -rise * 1.5
            self.tilt = -2.0 + rise * 3.0
            self.head = -3.0 + rise * 3.0
            self.left_arm = -8.0 + rise * 54.0
            self.right_arm = 8.0 - rise * 18.0
            self.near_angle = -40.0 + rise * 32.0
            self.far_angle = 30.0
            self.notation = rise
            self.mouth = 0.18 * rise
        elif animation == "block":
            guard = _ease(min(1.0, t * 2.5))
            self.root_x = -3.0
            self.bob = 2.0
            self.tilt = -5.0
            self.head = 3.0
            self.left_arm = -12.0 + guard * 48.0
            self.right_arm = 12.0 - guard * 48.0
            self.left_leg = -8.0
            self.right_leg = 9.0
            self.near_angle = -44.0 + guard * 82.0
            self.far_angle = 48.0 - guard * 82.0
            self.block = guard
        elif animation == "hit":
            impact = _pulse(t)
            shake = math.sin(t * math.pi * 5.0) * (1.0 - t)
            self.root_x = shake * 3.0 - impact * 4.0
            self.bob = -impact * 2.0
            self.tilt = -10.0 * impact
            self.head = 7.0 * impact
            self.left_arm = 18.0 * impact
            self.right_arm = 22.0 * impact
            self.left_leg = -8.0 * impact
            self.right_leg = 8.0 * impact
            self.coat_sway = -8.0 * impact
            self.mouth = 0.7 * impact
            self.near_angle = -12.0 - impact * 28.0
            self.far_angle = 18.0 + impact * 24.0
        elif animation == "death":
            fall = _ease(t)
            self.root_x = fall * 15.0
            self.root_y = fall * 9.0
            self.bob = -fall * 4.0
            self.tilt = -79.0 * fall
            self.head = -16.0 * fall
            self.left_arm = _lerp(-4.0, 52.0, fall)
            self.right_arm = _lerp(4.0, -54.0, fall)
            self.left_leg = _lerp(-2.0, 18.0, fall)
            self.right_leg = _lerp(2.0, -18.0, fall)
            self.coat_sway = -20.0 * fall
            self.near_angle = -16.0 - fall * 28.0
            self.far_angle = 20.0 + fall * 30.0
            self.x_eye = fall > 0.58
        elif animation == "taunt":
            flourish = _pulse(t)
            self.bob = -flourish * 1.0
            self.tilt = -3.0 + flourish * 4.0
            self.head = -5.0 + flourish * 5.0
            self.left_arm = -8.0 + flourish * 38.0
            self.right_arm = 8.0 - flourish * 26.0
            self.near_angle = -50.0 + flourish * 122.0
            self.far_angle = 54.0 - flourish * 108.0
            self.taunt = flourish
            self.mouth = 0.25 * flourish


def _blade_geometry(hand: Point, angle: float, length: float = 80.0) -> Tuple[Point, Point]:
    radians = math.radians(angle)
    guard = (hand[0] + 4.0 * math.cos(radians), hand[1] + 4.0 * math.sin(radians))
    tip = (guard[0] + length * math.cos(radians), guard[1] + length * math.sin(radians))
    return guard, tip


# -- the rig: each rigid piece painted once in its own frame, turned into place --

LENGTH_STEP = 2.0


def _S(p: Point) -> Point:
    """A work-space point in supersampled canvas pixels, unrounded."""
    return (p[0] * SUPER, p[1] * SUPER)


def _piece(key, extent, paint):
    return SR.local_piece(key, extent, paint, SUPER)


def _place(image: Image.Image, part, at: Point, deg: float, name: str, opacity: float = 1.0) -> None:
    SR.place(image, part, _S(at), deg, name, opacity)


def _heading(a: Point, b: Point) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def _stepped(a: Point, b: Point) -> float:
    return max(LENGTH_STEP, round(math.hypot(b[0] - a[0], b[1] - a[1]) / LENGTH_STEP) * LENGTH_STEP)


def _local(origin: Point):
    """``P`` (or ``H``) of an unturned frame whose root is at ``origin``."""

    def P(x: float, y: float) -> Point:
        return (origin[0] + x, origin[1] + y)

    return P


def _bar_piece(length: float, width: float, color: RGBA, stripe: float):
    """One bone of the old polyline along +x: a band ``width`` wide, round at
    both ends, with its thin outline stripe down the middle."""

    def paint(d, o) -> None:
        a, b = o, (o[0] + length, o[1])
        _line(d, [a, b], color, width)
        _ellipse(d, a, width / 2.0, width / 2.0, color, None)
        _ellipse(d, b, width / 2.0, width / 2.0, color, None)
        _line(d, [a, b], OUTLINE, stripe)

    r = width / 2.0 + 1.0
    return _piece(("leib_bar", length, width, color, stripe), (r, r, length + r, r), paint)


def _place_bar(image: Image.Image, a: Point, b: Point, width: float, color: RGBA, name: str) -> None:
    _place(image, _bar_piece(_stepped(a, b), width, color, 1.0), a, _heading(a, b), name)


def _boot_piece():
    def paint(d, ankle) -> None:
        boot = [
            (ankle[0] - 7.0, ankle[1] - 5.0),
            (ankle[0] + 9.0, ankle[1] - 5.0),
            (ankle[0] + 15.0, ankle[1] + 3.0),
            (ankle[0] + 7.0, ankle[1] + 9.0),
            (ankle[0] - 8.0, ankle[1] + 7.0),
        ]
        _poly(d, boot, BOOT, OUTLINE, 0.8)

    return _piece(("leib_boot",), (10.0, 7.0, 17.0, 11.0), paint)


def _draw_leg(image: Image.Image, hip: Point, thigh_angle: float, lift: float, front: bool) -> Point:
    thigh_length = 45.0
    shin_length = 43.0
    knee = (hip[0] + thigh_length * math.cos(math.radians(thigh_angle)), hip[1] + thigh_length * math.sin(math.radians(thigh_angle)))
    ankle = (
        knee[0] + shin_length * math.cos(math.radians(thigh_angle + 9.0)),
        knee[1] + shin_length * math.sin(math.radians(thigh_angle + 9.0)) - lift,
    )
    side = "near" if front else "far"
    breech = BREECH if front else BREECH_FAR
    _place_bar(image, hip, knee, 8.4 if front else 7.3, breech, f"{side}_thigh")
    _place_bar(image, knee, ankle, 7.2 if front else 6.4, STOCKING, f"{side}_shin")
    knee_part = _piece(("leib_knee", front), (6.0, 6.0, 6.0, 6.0), lambda d, o: _ellipse(d, o, 5.0, 5.2, breech, OUTLINE, 0.5))
    _place(image, knee_part, knee, 0.0, f"{side}_knee")
    _place(image, _boot_piece(), ankle, 0.0, f"{side}_boot")
    return ankle


def _draw_arm(image: Image.Image, shoulder: Point, elbow: Point, hand: Point, width: float, color: RGBA, radius: float, side: str) -> None:
    _place_bar(image, shoulder, elbow, width, color, f"{side}_upper_arm")
    _place_bar(image, elbow, hand, width, color, f"{side}_forearm")
    hand_part = _piece(("leib_hand", radius), (radius + 1.0, radius + 1.0, radius + 1.0, radius + 1.0), lambda d, o: _ellipse(d, o, radius, radius * 0.88, SKIN, OUTLINE, 0.5))
    _place(image, hand_part, hand, 0.0, f"{side}_hand")


def _blade_piece(near: bool):
    """A small-sword along +x from the hand: blade, guard and pommel."""
    length = 84.0 if near else 75.0

    def paint(d, hand) -> None:
        guard = (hand[0] + 4.0, hand[1])
        tip = (guard[0] + length, guard[1])
        base = (guard[0], guard[1] + 1.8)
        blade = [(base[0], base[1] + 2.0), (tip[0], tip[1] + 1.3), (tip[0], tip[1] - 1.0), (base[0], base[1] - 2.4)]
        _poly(d, blade, STEEL if near else STEEL_DARK, OUTLINE, 0.55)
        _line(d, [base, tip], STEEL_LIGHT, 0.55)
        _line(d, [(guard[0], guard[1] + 7.0), (guard[0], guard[1] - 7.0)], GOLD, 2.3)
        _ellipse(d, hand, 3.1, 3.1, GOLD_LIGHT, OUTLINE, 0.45)

    return _piece(("leib_blade", near), (5.0, 9.0, length + 7.0, 9.0), paint)


def _blade_glow_piece(near: bool):
    length = 84.0 if near else 75.0
    color = CALCULUS_BLUE if near else CALCULUS_GOLD
    return _piece(("leib_blade_glow", near), (-2.0, 3.0, length + 7.0, 3.0), lambda d, hand: _line(d, [(hand[0] + 4.0, hand[1]), (hand[0] + 4.0 + length, hand[1])], color, 3.0))


def _draw_blade(image: Image.Image, hand: Point, angle: float, *, near: bool, glow: float = 0.0) -> Point:
    side = "near" if near else "far"
    _place(image, _blade_piece(near), hand, angle, f"{side}_blade")
    if glow > 0.01:
        _place(image, _blade_glow_piece(near), hand, angle, f"{side}_blade_glow", glow)
    _guard, tip = _blade_geometry(hand, angle, 84.0 if near else 75.0)
    return tip


def _paint_tails(d, o, sway: float) -> None:
    P = _local(o)
    tail_left = [P(-22.0, -108.0), P(-8.0, -38.0), P(-25.0 + sway * 0.45, 22.0), P(-3.0, 18.0), P(8.0, -24.0), P(1.0, -108.0)]
    tail_right = [P(7.0, -108.0), P(12.0, -34.0), P(29.0 + sway * 0.58, 16.0), P(45.0, 10.0), P(32.0, -42.0), P(25.0, -108.0)]
    _poly(d, tail_left, COAT_DARK, OUTLINE, 1.0)
    _poly(d, tail_right, COAT, OUTLINE, 1.0)
    _line(d, [tail_left[0], tail_left[2]], GOLD, 1.0)
    _line(d, [tail_right[0], tail_right[2]], GOLD, 1.0)


def _paint_coat(d, o, cravat_lift: float) -> None:
    P = _local(o)
    torso = [P(-35.0, -202.0), P(4.0, -218.0), P(38.0, -201.0), P(49.0, -151.0), P(43.0, -103.0), P(22.0, -76.0), P(-12.0, -73.0), P(-38.0, -96.0), P(-43.0, -151.0)]
    _poly(d, torso, COAT, OUTLINE, 1.2)
    lapel_left = [P(-16.0, -192.0), P(-1.0, -199.0), P(-5.0, -119.0), P(-19.0, -101.0), P(-29.0, -129.0)]
    lapel_right = [P(9.0, -196.0), P(25.0, -190.0), P(36.0, -126.0), P(18.0, -98.0), P(6.0, -120.0)]
    _poly(d, lapel_left, COAT_LIGHT, OUTLINE, 0.6)
    _poly(d, lapel_right, COAT_LIGHT, OUTLINE, 0.6)
    waistcoat = [P(-9.0, -197.0), P(14.0, -195.0), P(20.0, -107.0), P(-1.0, -92.0), P(-20.0, -111.0), P(-19.0, -177.0)]
    _poly(d, waistcoat, WAISTCOAT, OUTLINE, 0.8)
    _poly(d, [P(-7.0, -193.0), P(6.0, -194.0), P(8.0, -111.0), P(-3.0, -99.0)], WAISTCOAT_LIGHT, None, 0.0)
    cravat = [P(-4.0, -207.0), P(12.0, -205.0), P(17.0, -175.0 + cravat_lift * 0.3), P(6.0, -143.0), P(-6.0, -170.0), P(-12.0, -185.0)]
    _poly(d, cravat, CRAVAT, OUTLINE, 0.7)
    for y in (-174.0, -151.0, -128.0):
        _ellipse(d, P(5.0, y), 2.0, 2.0, GOLD, OUTLINE, 0.3)


def _paint_head(d, o, x_eye: bool, blink: bool, mouth: float) -> None:
    H = _local(o)
    wig_back = [H(-33.0, -12.0), H(-26.0, -42.0), H(-4.0, -57.0), H(20.0, -50.0), H(34.0, -25.0), H(34.0, 12.0), H(27.0, 35.0), H(15.0, 45.0), H(7.0, 20.0), H(-18.0, 18.0), H(-27.0, 39.0), H(-39.0, 29.0)]
    _poly(d, wig_back, WIG, OUTLINE, 1.0)
    for cx, cy, r in [(-35, 4, 10), (-38, 22, 10), (-30, 38, 9), (34, 3, 10), (39, 20, 10), (31, 38, 9)]:
        _ellipse(d, H(cx, cy), r, r * 0.88, WIG_MID, OUTLINE_SOFT, 0.5)
        _arc(d, H(cx, cy), r * 0.65, r * 0.58, 210, 500, WIG_LIGHT, 0.7)
    head = [H(-19.0, -20.0), H(-9.0, -38.0), H(12.0, -42.0), H(28.0, -28.0), H(30.0, -4.0), H(18.0, 21.0), H(-5.0, 25.0), H(-24.0, 10.0)]
    _poly(d, head, SKIN, OUTLINE, 1.0)
    _ellipse(d, H(7.0, 1.0), 9.0, 6.5, BLUSH, None, 0.0)
    if x_eye:
        for x in (-4.0, 14.0):
            _line(d, [H(x - 4.0, -5.0), H(x + 3.0, 1.0)], OUTLINE, 0.8)
            _line(d, [H(x - 4.0, 1.0), H(x + 3.0, -5.0)], OUTLINE, 0.8)
    elif blink:
        _line(d, [H(-9.0, -4.0), H(-1.0, -4.0)], OUTLINE, 0.8)
        _line(d, [H(9.0, -5.0), H(18.0, -5.0)], OUTLINE, 0.8)
    else:
        for x in (-5.0, 14.0):
            _ellipse(d, H(x, -4.0), 3.6, 2.8, (245, 244, 234, 255), OUTLINE, 0.4)
            _ellipse(d, H(x + 0.7, -4.0), 1.0, 1.1, EYE, EYE, 0.1)
        _line(d, [H(-10.0, -10.0), H(-1.0, -11.0)], OUTLINE, 0.6)
        _line(d, [H(9.0, -11.0), H(18.0, -10.0)], OUTLINE, 0.6)
    nose = [H(5.0, -2.0), H(10.0, 7.0), H(5.0, 11.0), H(2.0, 4.0)]
    _poly(d, nose, SKIN_SHADE, OUTLINE, 0.3)
    _poly(d, [H(1.0, 13.0), H(-5.0, 12.0), H(-10.0, 16.0), H(0.0, 17.0)], WIG_MID, OUTLINE_SOFT, 0.3)
    _poly(d, [H(7.0, 13.0), H(13.0, 11.0), H(18.0, 15.0), H(8.0, 17.0)], WIG_MID, OUTLINE_SOFT, 0.3)
    if mouth > 0.05:
        _ellipse(d, H(4.0, 19.0), 4.5, 1.8 + mouth * 4.0, MOUTH, OUTLINE, 0.4)
    else:
        _line(d, [H(-1.0, 19.0), H(4.0, 20.0), H(10.0, 18.8)], MOUTH, 0.7)


def _render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    """Leib as a rig: coat tails (per sway step), coat, head (per
    expression), blades and limb bones are pieces painted once and turned
    into place at the statesman skeleton's anchors; the calculus effects stay
    shapes."""
    image = Image.new("RGBA", (WORK_FRAME_SIZE[0] * SUPER, WORK_FRAME_SIZE[1] * SUPER), (0, 0, 0, 0))
    draw = blending_draw(image)
    pose = Pose(animation, frame_idx, nframes)
    joints = _colonial_statesman_rig.evaluate(pose, WORK_FRAME_SIZE[0], WORK_FRAME_SIZE[1])
    root = joints.root
    body_angle = joints.body_ang

    def P(x: float, y: float) -> Point:
        rx, ry = _rot(x, y, body_angle)
        return (root[0] + rx, root[1] + ry)

    if pose.integral > 0.02:
        center = P(26.0, -128.0)
        _arc(draw, center, 95.0, 116.0, 122.0, 315.0, _fade(CALCULUS_BLUE, pose.integral * 0.75), 5.0)
        _arc(draw, center, 84.0, 105.0, 130.0, 305.0, _fade(CALCULUS_GOLD, pose.integral * 0.45), 2.0)
    if pose.notation > 0.02:
        alpha = pose.notation
        glyphs = [
            ("d", P(66.0, -224.0), CALCULUS_BLUE, 20.0),
            ("∫", P(90.0, -170.0), CALCULUS_GOLD, 28.0),
            ("dx", P(76.0, -112.0), CALCULUS_BLUE, 14.0),
        ]
        for text, point, color, size in glyphs:
            draw.text(_pt(point), text, font=_font(size), fill=_fade(color, alpha), anchor="mm")
    if pose.taunt > 0.02:
        center = P(0.0, -230.0)
        _arc(draw, center, 54.0, 30.0, 195.0, 345.0, _fade(GOLD_LIGHT, pose.taunt * 0.7), 2.0)

    _draw_leg(image, joints.far_hip, 92.0 + pose.right_leg, pose.right_lift, False)

    sway = SR.q(pose.coat_sway, 2.0)
    _place(image, _piece(("leib_tails", sway), (40.0, 112.0, 62.0, 30.0), lambda d, o: _paint_tails(d, o, sway)), root, body_angle, "coat_tails")
    cravat = SR.q(pose.cravat, 0.75)
    _place(image, _piece(("leib_coat", cravat), (46.0, 222.0, 52.0, -68.0), lambda d, o: _paint_coat(d, o, cravat)), root, body_angle, "coat")

    _draw_arm(image, joints.far_shoulder, joints.far_elbow, joints.far_hand, 7.4, COAT_DARK, 4.2, "far")
    if pose.far_blade > 0.0:
        _draw_blade(image, joints.far_hand, pose.far_angle + body_angle, near=False, glow=max(pose.crosscut, pose.block) * 0.45)

    mouth = SR.q(pose.mouth, 0.1)
    head = _piece(("leib_head", pose.x_eye, pose.blink, mouth), (52.0, 60.0, 52.0, 48.0), lambda d, o: _paint_head(d, o, pose.x_eye, pose.blink, mouth))
    _place(image, head, joints.head_root, joints.head_ang, "head")

    _draw_leg(image, joints.near_hip, 92.0 + pose.left_leg, pose.left_lift, True)

    _draw_arm(image, joints.near_shoulder, joints.near_elbow, joints.near_hand, 7.8, COAT, 4.5, "near")
    if pose.near_blade > 0.0:
        near_tip = _draw_blade(
            image,
            joints.near_hand,
            pose.near_angle + body_angle,
            near=True,
            glow=max(pose.slash, pose.crosscut, pose.integral, pose.block),
        )
        if pose.slash > 0.04:
            _arc(draw, near_tip, 54.0, 40.0, 145.0, 325.0, _fade(CALCULUS_BLUE, pose.slash * 0.72), 4.0)
        if pose.crosscut > 0.04:
            _arc(draw, P(5.0, -145.0), 72.0, 58.0, 185.0, 350.0, _fade(CALCULUS_GOLD, pose.crosscut * 0.65), 3.0)

    if pose.block > 0.35:
        center = P(4.0, -153.0)
        _ellipse(draw, center, 43.0, 50.0, _fade(CALCULUS_BLUE, (pose.block - 0.35) * 0.18), _fade(CALCULUS_BLUE, pose.block * 0.55), 2.0)

    return rigdoc.downsampled_canvas(image, FRAME_SIZE, Image.Resampling.LANCZOS)


def _body_metrics_override(frame_width: int, frame_height: int):
    return {
        "body_pixel_bbox": {
            "x": int(frame_width * 0.20),
            "y": int(frame_height * 0.08),
            "w": int(frame_width * 0.62),
            "h": int(frame_height * 0.86),
        },
        "feet_pixel": {"x": frame_width * 0.50, "y": frame_height * 0.93},
        "feet_anchor_norm": {"x": 0.0, "y": round(0.5 - 0.93, 6)},
    }


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=_render_frame,
        out_dir=Path(out_dir),
        frame_size=FRAME_SIZE,
        label_width=112,
        auto_crop=False,
        body_metrics_fn=_body_metrics_override,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning={"collision_scale": 1.08, "frame_sample_inset": 1},
        animation_key_map={name: name for name, _frames, _duration in ROWS},
        attack_hitboxes={
            "slash": {"bbox": {"x": 117, "y": 82, "w": 132, "h": 116}},
            "crosscut": {"bbox": {"x": 35, "y": 72, "w": 187, "h": 136}},
            "integral_sweep": {"bbox": {"x": 36, "y": 48, "w": 210, "h": 188}},
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
    parts = publish_rig_flipbook(TARGET_NAME, ROWS, _render_frame, outputs, frame_transform, Path(out_dir))
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())


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
