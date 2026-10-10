from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageDraw

from ...authoring import rigdoc, shape_rig
from ...authoring.part_flipbook import publish_rig_flipbook
from ambition_sprite2d_renderer.authoring.portrait import (
    FaceGuide,
    PortraitClip,
    render_framed_portrait,
    write_portrait_sheet,
)
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

TARGET_NAME = "admiral_grass_hopper"
FRAME_SIZE = (128, 128)
WORK_SIZE = (FRAME_SIZE[0] * 4, FRAME_SIZE[1] * 4)
SUPER = 4

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 140),
    ("walk", 8, 96),
    ("talk", 6, 112),
    ("interact", 6, 108),
    ("slash", 7, 84),
    ("taunt", 8, 92),
    ("hurt", 5, 92),
    ("death", 8, 112),
]

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_admiral_grass_hopper",
        "display_name": "Admiral Grass Hopper",
    },
    "authoring_description": {
        "parody_of": "Rear Admiral Grace Hopper",
        "core_joke": "A grasshopper admiral who literalizes the Hopper name while keeping Grace Hopper's naval-computing legacy at the center.",
        "visual_inspirations": [
            "Grace Hopper portraiture and U.S. Navy officer presentation",
            "storybook grasshopper silhouettes with long hind legs and antennae",
            "a compact metroidvania-friendly side profile rather than a realistic insect",
            "gold-trimmed admiral coat, cap badge, and a command baton that can also read as a debugging pointer",
        ],
        "design_notes": [
            "Keep the character likable and readable first, then let the entomology sell the pun.",
            "The coat, epaulettes, and hat should do most of the 'admiral' work; the abdomen, antennae, and hind legs should do most of the 'grasshopper' work.",
            "The baton can double as a compiler pointer, classroom stick, or melee flourish.",
            "The tone should celebrate Grace Hopper rather than mocking her: this is a tribute-parody character.",
        ],
        "reference_hooks": [
            "COBOL / compiler pioneer",
            "debugging lore and the famous moth anecdote",
            "naval command presence",
            "fast hopping movement and crisp lecture-energy dialog",
        ],
    },
    "gameplay_description": {
        "role": "mobile support-skirmisher / brilliant officer",
        "combat_identity": [
            "quick side-hops and sharp baton strikes",
            "commanding bark-based support fantasy",
            "can read as a mentor NPC, miniboss, or playable light fighter",
        ],
        "signature_moves": [
            "Bug Report: a precise baton jab or slash that 'flags' an enemy",
            "Compiler Directive: a command gesture that could buff allies or alter battlefield behavior",
            "Debug Hop: a springy reposition with exaggerated grasshopper leg compression",
        ],
        "authoring_notes": [
            "This sheet only includes a general-purpose slash, not a full projectile or support kit yet.",
            "Future expansion should probably add a pronounced hop / leap attack row and a dedicated command-point emote.",
            "Because Grace Hopper is a foundational computing figure, dialog should lean clever, direct, and impatient with sloppy thinking.",
        ],
    },
    "dialogue_hints": {
        "suggested_barks": [
            "Debug it at the source!",
            "Hop to it!",
            "Compiler says no!",
            "Mind your logic!",
            "That bug is now documented!",
            "Order from disorder!",
        ],
        "fallback_dialogue": [
            "I prefer clear thinking, clean systems, and decisive action.",
            "A bug ignored is a bug promoted.",
            "You can waste time arguing with reality, or you can measure it and move.",
            "The trick is to make complex work look disciplined.",
        ],
    },
    "body": {
        "body_plan": "InsectoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "locomotion_hint": "Walk",
        "traits": [
            "story",
            "combatant",
            "scientist_parody",
            "insectoid",
            "naval_officer",
            "computer_science",
            "mentor",
            "hopper",
        ],
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": {"height_px": None, "distance_px": None, "source": "grasshopper_hind_legs"},
            "climb": None,
            "crawl": None,
            "fly": None,
            "swim": None,
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
    "actions": {"default_preset": "peaceful"},
    "visual": {
        "default_pose": "idle",
        "portrait_style": "dialog_closeup",
        "portrait_source": TARGET_NAME,
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "action.melee.primary": {
            "animation": "slash",
            "events": [
                {"t": 0.34, "event": "hitbox_active_start", "source": "admiral_grass_hopper.slash"},
                {"t": 0.60, "event": "hitbox_active_end", "source": "admiral_grass_hopper.slash"},
            ],
        },
        "emote.taunt": {"animation": "taunt", "events": []},
        "damage.hit": {"animation": "hurt", "events": []},
        "lifecycle.death": {"animation": "death", "events": []},
    },
    "sockets": {
        "head": {"source": "admiral_grass_hopper.authored", "point": {"x": 72.0, "y": 26.0}},
        "chest": {"source": "admiral_grass_hopper.authored", "point": {"x": 64.0, "y": 54.0}},
        "hand_l": {"source": "admiral_grass_hopper.authored", "point": {"x": 58.0, "y": 64.0}},
        "hand_r": {"source": "admiral_grass_hopper.authored", "point": {"x": 84.0, "y": 62.0}},
        "weapon_grip": {"source": "admiral_grass_hopper.authored", "point": {"x": 86.0, "y": 60.0}},
        "weapon_tip": {"source": "admiral_grass_hopper.authored", "point": {"x": 106.0, "y": 54.0}},
        "speech_bubble": {"source": "admiral_grass_hopper.authored", "point": {"x": 72.0, "y": 8.0}},
    },
    "tags": [
        "story",
        "combatant",
        "scientist_parody",
        "insectoid",
        "naval_officer",
        "computer_science",
        "grace_hopper_parody",
        "mentor",
    ],
}

OUTLINE = (18, 22, 22, 255)
GREEN_DARK = (41, 92, 54, 255)
GREEN = (89, 163, 93, 255)
GREEN_LIGHT = (140, 211, 123, 255)
GREEN_PALE = (182, 235, 156, 255)
COAT_DARK = (32, 45, 92, 255)
COAT = (56, 84, 150, 255)
COAT_LIGHT = (92, 130, 210, 255)
GOLD = (234, 197, 84, 255)
GOLD_LIGHT = (248, 224, 136, 255)
WHITE = (237, 240, 246, 255)
RED = (173, 54, 53, 255)
RED_LIGHT = (214, 90, 88, 255)
WOOD = (123, 84, 56, 255)
WOOD_LIGHT = (165, 118, 74, 255)
EYE = (32, 24, 24, 255)
EYE_HL = (255, 252, 244, 255)
CHEEK = (208, 166, 132, 90)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _ease(t: float) -> float:
    return t * t * (3.0 - 2.0 * t)


@dataclass
class Pose:
    root_x: float = 0.0
    root_y: float = 0.0
    bob: float = 0.0
    lean: float = 0.0
    head_tilt: float = 0.0
    antenna_sway: float = 0.0
    abdomen_lift: float = 0.0
    coat_flare: float = 0.0
    mouth_open: float = 0.0
    arm_front: float = 0.0
    arm_back: float = 0.0
    baton_angle: float = -12.0
    baton_extend: float = 0.0
    front_leg: float = 0.0
    rear_leg: float = 0.0
    front_foot_lift: float = 0.0
    rear_foot_lift: float = 0.0
    salute: float = 0.0
    blink: bool = False
    x_eye: bool = False
    dead: bool = False

    def __init__(self, anim: str, frame_idx: int, frame_count: int):
        t = frame_idx / max(1, frame_count - 1)
        cyc = math.tau * frame_idx / max(1, frame_count)
        s = math.sin(cyc)
        c = math.cos(cyc)

        self.root_x = 0.0
        self.root_y = 0.0
        self.bob = 0.0
        self.lean = 0.0
        self.head_tilt = 0.0
        self.antenna_sway = 0.0
        self.abdomen_lift = 0.0
        self.coat_flare = 0.0
        self.mouth_open = 0.0
        self.arm_front = 0.0
        self.arm_back = 0.0
        self.baton_angle = -14.0
        self.baton_extend = 0.0
        self.front_leg = 0.0
        self.rear_leg = 0.0
        self.front_foot_lift = 0.0
        self.rear_foot_lift = 0.0
        self.salute = 0.0
        self.blink = False
        self.x_eye = False
        self.dead = False

        if anim == "idle":
            self.bob = s * 1.5
            self.lean = s * 1.8
            self.head_tilt = -s * 1.4
            self.antenna_sway = s * 6.0
            self.abdomen_lift = abs(s) * 1.8
            self.coat_flare = abs(s) * 1.4
            self.arm_front = 8.0 + s * 3.0
            self.arm_back = -10.0 - s * 2.0
            self.front_leg = c * 2.0
            self.rear_leg = -c * 2.0
            self.blink = frame_idx == frame_count - 2
        elif anim == "walk":
            self.root_x = s * 2.4
            self.bob = abs(s) * 3.2 - 0.8
            self.lean = s * 3.4
            self.head_tilt = -s * 1.6
            self.antenna_sway = -s * 10.0
            self.abdomen_lift = abs(s) * 2.4
            self.coat_flare = abs(s) * 5.0
            self.arm_front = 14.0 * s + 8.0
            self.arm_back = -12.0 * s - 10.0
            self.front_leg = 22.0 * s
            self.rear_leg = -24.0 * s
            self.front_foot_lift = max(0.0, s) * 8.0
            self.rear_foot_lift = max(0.0, -s) * 8.0
        elif anim == "talk":
            self.bob = s * 1.0
            self.lean = s * 1.2
            self.head_tilt = -s * 2.0
            self.antenna_sway = s * 8.0
            self.arm_front = _lerp(8.0, 28.0, (s + 1.0) * 0.5)
            self.arm_back = -8.0
            self.baton_angle = -38.0
            self.baton_extend = 8.0
            self.salute = (s + 1.0) * 0.28
            self.mouth_open = 0.18 + (c + 1.0) * 0.08
            self.coat_flare = 1.5
        elif anim == "interact":
            tt = _ease(t)
            self.bob = -math.sin(tt * math.pi) * 2.0
            self.lean = _lerp(-8.0, 10.0, tt)
            self.head_tilt = _lerp(-6.0, 4.0, tt)
            self.antenna_sway = _lerp(10.0, -6.0, tt)
            self.arm_front = _lerp(-12.0, 42.0, tt)
            self.arm_back = -6.0
            self.baton_angle = _lerp(-72.0, -10.0, tt)
            self.baton_extend = _lerp(4.0, 18.0, tt)
            self.salute = _lerp(0.0, 0.18, tt)
            self.mouth_open = 0.10
            self.coat_flare = 2.2
        elif anim == "slash":
            tt = _ease(t)
            wave = math.sin(tt * math.pi)
            self.root_x = _lerp(-4.0, 8.0, tt)
            self.bob = -wave * 3.5
            self.lean = _lerp(12.0, -18.0, tt)
            self.head_tilt = _lerp(8.0, -10.0, tt)
            self.antenna_sway = _lerp(-8.0, 18.0, tt)
            self.abdomen_lift = 2.0 + wave * 1.8
            self.coat_flare = 4.0 + wave * 5.0
            self.arm_front = _lerp(78.0, -112.0, tt)
            self.arm_back = _lerp(10.0, -18.0, tt)
            self.baton_angle = _lerp(60.0, -120.0, tt)
            self.baton_extend = _lerp(0.0, 26.0, tt)
            self.front_leg = 8.0 - wave * 5.0
            self.rear_leg = -10.0 + wave * 5.0
            self.mouth_open = 0.12 * wave
        elif anim == "taunt":
            self.bob = abs(s) * 1.6
            self.lean = s * 2.2
            self.head_tilt = -s * 3.0
            self.antenna_sway = s * 12.0
            self.arm_front = 16.0 + s * 8.0
            self.arm_back = -10.0
            self.baton_angle = -84.0
            self.baton_extend = 14.0
            self.salute = 0.20 + max(0.0, s) * 0.25
            self.mouth_open = 0.1 + max(0.0, c) * 0.12
            self.coat_flare = 3.0
        elif anim == "hurt":
            hit = math.sin(t * math.pi)
            shake = math.sin(t * math.pi * 4.0) * (1.0 - t)
            self.root_x = shake * 4.0
            self.bob = -hit * 2.5
            self.lean = -18.0 * hit
            self.head_tilt = 16.0 * hit
            self.antenna_sway = 22.0 * hit
            self.arm_front = 28.0 * hit
            self.arm_back = 18.0 * hit
            self.front_leg = 12.0 * hit
            self.rear_leg = -10.0 * hit
            self.mouth_open = 0.14 * hit
        elif anim == "death":
            tt = _ease(t)
            self.root_x = _lerp(0.0, -16.0, tt)
            self.root_y = _lerp(0.0, 12.0, tt)
            self.bob = -tt * 2.0
            self.lean = _lerp(0.0, -88.0, tt)
            self.head_tilt = _lerp(0.0, 28.0, tt)
            self.antenna_sway = _lerp(0.0, 26.0, tt)
            self.abdomen_lift = _lerp(0.0, 6.0, tt)
            self.coat_flare = _lerp(1.0, 7.0, tt)
            self.arm_front = _lerp(8.0, 92.0, tt)
            self.arm_back = _lerp(-10.0, 62.0, tt)
            self.baton_angle = _lerp(-14.0, -136.0, tt)
            self.front_leg = _lerp(0.0, 48.0, tt)
            self.rear_leg = _lerp(0.0, 24.0, tt)
            self.front_foot_lift = _lerp(0.0, 8.0, tt)
            self.rear_foot_lift = _lerp(0.0, 4.0, tt)
            self.mouth_open = _lerp(0.0, 0.18, tt)
            self.x_eye = tt > 0.55
            self.dead = tt > 0.84


def _rot(point: tuple[float, float], origin: tuple[float, float], degrees: float) -> tuple[float, float]:
    ang = math.radians(degrees)
    px, py = point
    ox, oy = origin
    dx = px - ox
    dy = py - oy
    ca = math.cos(ang)
    sa = math.sin(ang)
    return (ox + dx * ca - dy * sa, oy + dx * sa + dy * ca)


def _poly(draw: ImageDraw.ImageDraw, points, fill, outline=OUTLINE, width=5):
    draw.polygon(points, fill=fill)
    if outline is not None:
        draw.line(list(points) + [points[0]], fill=outline, width=width)


def _ellipse(draw: ImageDraw.ImageDraw, bbox, fill, outline=OUTLINE, width=5):
    draw.ellipse(bbox, fill=fill, outline=outline, width=width)


def _line(draw: ImageDraw.ImageDraw, pts, fill, width=5):
    draw.line(pts, fill=fill, width=width, joint="curve")


def _circle(draw: ImageDraw.ImageDraw, center, radius, fill, outline=OUTLINE, width=4):
    x, y = center
    _ellipse(draw, (x - radius, y - radius, x + radius, y + radius), fill=fill, outline=outline, width=width)


def _draw_hat(draw: ImageDraw.ImageDraw, center, head_tilt=0.0):
    cx, cy = center
    brim = [(cx - 34, cy - 26), (cx + 20, cy - 32), (cx + 34, cy - 18), (cx - 22, cy - 12)]
    crown = [(cx - 22, cy - 40), (cx + 8, cy - 44), (cx + 24, cy - 34), (cx - 8, cy - 30)]
    brim = [_rot(p, center, head_tilt) for p in brim]
    crown = [_rot(p, center, head_tilt) for p in crown]
    _poly(draw, brim, COAT_DARK, width=4)
    _poly(draw, crown, COAT, width=4)
    badge_center = _rot((cx + 8, cy - 32), center, head_tilt)
    _circle(draw, badge_center, 6, GOLD_LIGHT, width=2)
    _line(draw, [
        _rot((cx - 16, cy - 28), center, head_tilt),
        _rot((cx + 22, cy - 34), center, head_tilt),
    ], fill=GOLD, width=4)


# --- Rig construction -------------------------------------------------------
#
# The admiral is drawn as a rig (``shape_rig``): every rigid piece is painted
# once in its own raster (supersampled pixels) and placed, turned where it
# turns. Limb segments are round-capped strokes turned from joint to joint
# (one piece per whole-pixel length) carrying the joint disc at their root;
# the abdomen, coat skirt and antennae are keyed by the (rounded) lift, flare
# and sway they read; the thorax rides the chest; the head's face, eye, mouth,
# antennae and hat turn together by the head's tilt; the baton is painted
# level and turned about the hand.


def _piece(key, half: float, paint):
    """A piece ``2 * half`` supersampled pixels square, pivot at the centre:
    ``paint(draw, o)`` paints it with the local origin at ``(o, o)``."""
    size = 2 * int(math.ceil(half))
    return shape_rig.piece((TARGET_NAME,) + tuple(key), (size, size), (size / 2, size / 2), lambda d: paint(d, size / 2))


def _length(a, b) -> float:
    """A segment's length to the whole frame pixel (in supersampled px)."""
    return float(max(1, round(math.hypot(b[0] - a[0], b[1] - a[1]) / SUPER)) * SUPER)


def _angle(a, b) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def _place_segment(img, a, b, fill, width: int, root_disc, name: str, end_disc=None) -> None:
    """A limb segment from ``a`` to ``b``: a stroke of ``width`` with round
    ends (the polyline's curve joints), then the joint disc ``(radius,
    outline width)`` at its root, and ``end_disc`` at its end."""
    span = _length(a, b)
    half = span + width + 4

    def paint(draw, o: float) -> None:
        r = width / 2
        _line(draw, [(o, o), (o + span, o)], fill=fill, width=width)
        draw.ellipse((o - r, o - r, o + r, o + r), fill=fill)
        draw.ellipse((o + span - r, o - r, o + span + r, o + r), fill=fill)
        if root_disc is not None:
            _circle(draw, (o, o), root_disc[0], fill, width=root_disc[1])
        if end_disc is not None:
            _circle(draw, (o + span, o), end_disc[0], fill, width=end_disc[1])

    part = _piece(("segment", span, fill, width, root_disc, end_disc), half, paint)
    shape_rig.place(img, part, a, _angle(a, b), name)


def _place_leg(img, side: str, hip, knee, ankle, foot, *, fill, lift=0.0) -> None:
    ax, ay = ankle
    ankle = (ax, ay - lift * 0.35)
    foot = (foot[0], foot[1] - lift)
    _place_segment(img, hip, knee, fill, 18, (8, 3), f"{side}_thigh")
    _place_segment(img, knee, ankle, fill, 18, (7, 3), f"{side}_shin")
    _place_segment(img, ankle, foot, fill, 18, (6, 3), f"{side}_foot")


def _paint_baton(draw, o: float, extend: float) -> None:
    """The baton level from the hand at ``(o, o)``."""
    hx, hy = o, o
    end = (hx + 38.0 + extend, hy - 2.0)
    tip = (end[0] + 8.0, end[1])
    _line(draw, [(hx, hy), end], fill=WOOD, width=8)
    _line(draw, [(hx, hy), end], fill=OUTLINE, width=2)
    _line(draw, [end, tip], fill=GOLD, width=5)
    _line(draw, [end, tip], fill=OUTLINE, width=2)
    _circle(draw, (hx + 10.0, hy), 3, GOLD_LIGHT, width=2)


def _paint_thorax(draw, chest) -> None:
    thorax_box = (chest[0] - 56, chest[1] - 62, chest[0] + 54, chest[1] + 44)
    _ellipse(draw, thorax_box, COAT, outline=OUTLINE, width=6)
    left_lapel = [(chest[0] - 18, chest[1] - 38), (chest[0] + 2, chest[1] - 6), (chest[0] - 8, chest[1] + 30), (chest[0] - 28, chest[1] + 8)]
    right_lapel = [(chest[0] + 4, chest[1] - 42), (chest[0] + 24, chest[1] - 12), (chest[0] + 20, chest[1] + 20), (chest[0] - 2, chest[1] - 10)]
    _poly(draw, left_lapel, COAT_LIGHT, width=3)
    _poly(draw, right_lapel, COAT_LIGHT, width=3)
    for dx, dy in ((-30, -46), (-30, -28), (-26, -10), (10, -36), (8, -18), (6, 0)):
        _circle(draw, (chest[0] + dx, chest[1] + dy), 4, GOLD_LIGHT, width=2)
    epaulet_back = [(chest[0] - 48, chest[1] - 54), (chest[0] - 12, chest[1] - 64), (chest[0] - 10, chest[1] - 46), (chest[0] - 44, chest[1] - 36)]
    epaulet_front = [(chest[0] + 8, chest[1] - 58), (chest[0] + 42, chest[1] - 60), (chest[0] + 46, chest[1] - 42), (chest[0] + 12, chest[1] - 42)]
    _poly(draw, epaulet_back, GOLD, width=3)
    _poly(draw, epaulet_front, GOLD, width=3)


def _paint_head(draw, head_center) -> None:
    head_box = (head_center[0] - 42, head_center[1] - 36, head_center[0] + 36, head_center[1] + 30)
    _ellipse(draw, head_box, GREEN_LIGHT, outline=OUTLINE, width=6)
    _ellipse(draw, (head_box[0] + 8, head_box[1] + 10, head_box[2] - 10, head_box[3] - 10), GREEN_PALE, outline=None)
    _ellipse(draw, (head_center[0] - 8, head_center[1] + 8, head_center[0] + 20, head_center[1] + 24), CHEEK, outline=None)


def _paint_eye(draw, head_center, x_eye: bool, blink: bool) -> None:
    eye_center = (head_center[0] + 14, head_center[1] - 2)
    if x_eye:
        for sign in (-1, 1):
            _line(draw, [(eye_center[0] - 7, eye_center[1] - 7 * sign), (eye_center[0] + 7, eye_center[1] + 7 * sign)], fill=EYE, width=4)
    elif blink:
        _line(draw, [(eye_center[0] - 10, eye_center[1]), (eye_center[0] + 8, eye_center[1] + 2)], fill=EYE, width=4)
    else:
        _ellipse(draw, (eye_center[0] - 10, eye_center[1] - 8, eye_center[0] + 8, eye_center[1] + 8), WHITE, outline=OUTLINE, width=3)
        pupil = (eye_center[0] + 2, eye_center[1] + 1)
        _circle(draw, pupil, 4, EYE, width=1)
        _circle(draw, (pupil[0] - 1, pupil[1] - 1), 1, EYE_HL, outline=None, width=0)


def _paint_mouth(draw, head_center, mouth_open: float) -> None:
    mouth_y = head_center[1] + 16
    mouth_w = 16
    mouth_h = 3 + mouth_open * 26
    _line(draw, [(head_center[0] - 2, mouth_y), (head_center[0] + mouth_w, mouth_y + mouth_h * 0.15)], fill=OUTLINE, width=4)
    if mouth_open > 0.04:
        tongue = [
            (head_center[0] + 4, mouth_y + 2),
            (head_center[0] + 15, mouth_y + 2),
            (head_center[0] + 12, mouth_y + mouth_h),
            (head_center[0] + 5, mouth_y + mouth_h),
        ]
        _poly(draw, tongue, RED_LIGHT, outline=None, width=0)


def _paint_antennae(draw, head_center, sway: float) -> None:
    for side, lift in ((-1, -8), (1, 10)):
        ant_base = (head_center[0] - 4, head_center[1] - 20)
        ant_mid = (head_center[0] + side * 8, head_center[1] - 62 + side * 4 + sway)
        ant_tip = (head_center[0] + side * 22, head_center[1] - 96 + sway * 1.2 + lift)
        _line(draw, [ant_base, ant_mid, ant_tip], fill=GREEN_DARK, width=6)
        _circle(draw, ant_tip, 4, GOLD_LIGHT, width=2)


def _draw_admiral(pose: Pose, anim: str, frame_idx: int, frame_count: int):
    img = Image.new("RGBA", WORK_SIZE, (0, 0, 0, 0))

    ox = 210 + pose.root_x * SUPER
    ground_y = 386 + pose.root_y * SUPER
    bob = pose.bob * SUPER

    hip_back = (ox - 42, ground_y - 112 - bob)
    hip_front = (ox - 4, ground_y - 114 - bob)
    knee_back = _rot((ox - 74, ground_y - 54 - bob), hip_back, pose.rear_leg)
    knee_front = _rot((ox + 16, ground_y - 48 - bob), hip_front, pose.front_leg)
    ankle_back = (knee_back[0] + 22, knee_back[1] + 48)
    ankle_front = (knee_front[0] + 24, knee_front[1] + 44)
    foot_back = (ankle_back[0] + 34, ground_y - 6)
    foot_front = (ankle_front[0] + 34, ground_y - 6)

    _place_leg(img, "back", hip_back, knee_back, ankle_back, foot_back, fill=GREEN_DARK, lift=pose.rear_foot_lift * SUPER)

    # Wing and abdomen about the body point, keyed by the abdomen's lift.
    body_at = (ox, ground_y - bob)
    lift = round(pose.abdomen_lift * SUPER)

    def paint_abdomen(draw, o: float) -> None:
        abdomen_box = (o - 122, o - 190 - lift, o - 10, o - 104)
        wing_box = (o - 84, o - 214, o + 10, o - 128)
        _ellipse(draw, wing_box, (184, 235, 226, 160), outline=(86, 120, 120, 150), width=3)
        _ellipse(draw, abdomen_box, GREEN, outline=OUTLINE, width=6)
        _ellipse(draw, (abdomen_box[0] + 14, abdomen_box[1] + 10, abdomen_box[2] - 12, abdomen_box[3] - 10), GREEN_LIGHT, outline=None)

    shape_rig.place(img, _piece(("abdomen", lift), 220, paint_abdomen), body_at, 0.0, "abdomen")

    chest = (ox + pose.lean * 0.5, ground_y - 212 - bob)
    _place_leg(img, "front", hip_front, knee_front, ankle_front, foot_front, fill=GREEN, lift=pose.front_foot_lift * SUPER)

    flare = round(pose.coat_flare * SUPER / 2) * 2

    def paint_skirt(draw, o: float) -> None:
        coat_skirt = [
            (o - 44, o + 18),
            (o + 28, o + 10),
            (o + 44 + flare, o + 76),
            (o - 12, o + 82),
            (o - 48 - flare * 0.3, o + 74),
        ]
        _poly(draw, coat_skirt, COAT_DARK, width=5)

    shape_rig.place(img, _piece(("skirt", flare), 96, paint_skirt), chest, 0.0, "coat_skirt")
    shape_rig.place(img, _piece(("thorax",), 72, lambda d, o: _paint_thorax(d, (o, o))), chest, 0.0, "thorax")

    # The head turns by its tilt about its centre: face, eye, mouth, antennae, hat.
    neck = (chest[0] + 18, chest[1] - 66)
    head_center = _rot((neck[0] + 20, neck[1] - 18), neck, pose.head_tilt)
    tilt = pose.head_tilt
    shape_rig.place(img, _piece(("head",), 48, lambda d, o: _paint_head(d, (o, o))), head_center, tilt, "head")
    eye = (pose.x_eye, pose.blink and not pose.x_eye)
    shape_rig.place(img, _piece(("eye",) + eye, 48, lambda d, o: _paint_eye(d, (o, o), *eye)), head_center, tilt, "eye")
    mouth_open = round(pose.mouth_open * 50) / 50
    shape_rig.place(img, _piece(("mouth", mouth_open), 48, lambda d, o: _paint_mouth(d, (o, o), mouth_open)), head_center, tilt, "mouth")
    sway = round(pose.antenna_sway / 2) * 2
    shape_rig.place(img, _piece(("antennae", sway), 132, lambda d, o: _paint_antennae(d, (o, o), sway)), head_center, tilt, "antennae")
    shape_rig.place(img, _piece(("hat",), 52, lambda d, o: _draw_hat(d, (o, o))), head_center, tilt, "hat")

    shoulder_back = (chest[0] - 28, chest[1] - 20)
    elbow_back = _rot((shoulder_back[0] - 18, shoulder_back[1] + 28), shoulder_back, pose.arm_back)
    hand_back = _rot((elbow_back[0] + 2, elbow_back[1] + 26), elbow_back, pose.arm_back * 0.3)
    _place_segment(img, shoulder_back, elbow_back, GREEN_DARK, 14, (6, 3), "back_upper_arm")
    _place_segment(img, elbow_back, hand_back, GREEN_DARK, 14, (5, 3), "back_forearm", end_disc=(5, 3))

    shoulder_front = (chest[0] + 22, chest[1] - 18)
    elbow_front = _rot((shoulder_front[0] + 20, shoulder_front[1] + 18), shoulder_front, pose.arm_front)
    hand_front = _rot((elbow_front[0] + 22, elbow_front[1] + 20), elbow_front, pose.arm_front * 0.35)
    _place_segment(img, shoulder_front, elbow_front, GREEN, 14, (6, 3), "front_upper_arm")
    _place_segment(img, elbow_front, hand_front, GREEN, 14, (5, 3), "front_forearm", end_disc=(5, 3))
    extend = round(pose.baton_extend / 2) * 2
    baton = _piece(("baton", extend), 80, lambda d, o: _paint_baton(d, o, extend))
    shape_rig.place(img, baton, hand_front, pose.baton_angle, "baton")

    if pose.salute > 0.01:
        salute_hand = _rot((head_center[0] + 4, head_center[1] - 36), head_center, pose.head_tilt)

        def paint_salute(draw, o: float) -> None:
            _line(draw, [(o - 10, o + 10), (o, o), (o + 16, o - 2)], fill=GOLD_LIGHT, width=5)

        shape_rig.place(img, _piece(("salute",), 24, paint_salute), salute_hand, 0.0, "salute")

    return rigdoc.downsampled_canvas(img, FRAME_SIZE, Image.Resampling.LANCZOS)


def _render_frame(animation: str, frame_idx: int, frame_count: int):
    pose = Pose(animation, frame_idx, frame_count)
    return _draw_admiral(pose, animation, frame_idx, frame_count)


def render_portraits(out_dir: str | Path, **opts):
    del opts

    def portrait_frame(animation: str, frame_idx: int, frame_count: int):
        source = _draw_admiral(Pose(animation, frame_idx, frame_count), animation, frame_idx, frame_count)
        face = FaceGuide(
            center_x=74.0,
            center_y=28.0,
            width=46.0,
            height=42.0,
            source_width=128.0,
            source_height=128.0,
        )
        return render_framed_portrait(source, face, view_width=62.0, center_y=42.0)

    clips = {
        "default": PortraitClip.still(portrait_frame("idle", 2, 8)),
        "talking": PortraitClip(tuple(portrait_frame("talk", i, 6) for i in (0, 2, 4)), duration_ms=110, looping=True),
        "command": PortraitClip(tuple(portrait_frame("interact", i, 6) for i in (1, 3, 5)), duration_ms=108, looping=True),
        "taunt": PortraitClip.still(portrait_frame("taunt", 3, 8)),
    }
    return write_portrait_sheet(TARGET_NAME, clips, Path(out_dir))


def render(out_dir: str | Path, **opts):
    del opts
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=_render_frame,
        out_dir=Path(out_dir),
        frame_size=FRAME_SIZE,
        auto_crop=True,
        crop_margin=4,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning={"collision_scale": 1.5},
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


__all__ = ["ACTOR_METADATA", "render", "render_portraits"]
