from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageDraw

from ambition_sprite2d_renderer.authoring.portrait import (
    FaceGuide,
    PortraitClip,
    render_framed_portrait,
    write_portrait_sheet,
)
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

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
SHADOW = (0, 0, 0, 44)
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


def _draw_leg(draw: ImageDraw.ImageDraw, hip, knee, ankle, foot, *, fill, lift=0.0):
    ax, ay = ankle
    foot = (foot[0], foot[1] - lift)
    _line(draw, [hip, knee, (ax, ay - lift * 0.35), foot], fill=fill, width=18)
    for point, r in ((hip, 8), (knee, 7), ((ax, ay - lift * 0.35), 6)):
        _circle(draw, point, r, fill, width=3)


def _draw_arm(draw: ImageDraw.ImageDraw, shoulder, elbow, hand, *, fill, baton=False, baton_angle=-20.0, baton_extend=0.0):
    _line(draw, [shoulder, elbow, hand], fill=fill, width=14)
    _circle(draw, shoulder, 6, fill, width=3)
    _circle(draw, elbow, 5, fill, width=3)
    _circle(draw, hand, 5, fill, width=3)
    if baton:
        hx, hy = hand
        end = (hx + 38.0 + baton_extend, hy - 2.0)
        end = _rot(end, hand, baton_angle)
        tip = _rot((end[0] + 8.0, end[1]), end, baton_angle * 0.08)
        _line(draw, [hand, end], fill=WOOD, width=8)
        _line(draw, [hand, end], fill=OUTLINE, width=2)
        _line(draw, [end, tip], fill=GOLD, width=5)
        _line(draw, [end, tip], fill=OUTLINE, width=2)
        ring = _rot((hx + 10.0, hy), hand, baton_angle)
        _circle(draw, ring, 3, GOLD_LIGHT, width=2)


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


def _draw_admiral(pose: Pose, anim: str, frame_idx: int, frame_count: int):
    img = Image.new("RGBA", WORK_SIZE, (0, 0, 0, 0))
    draw = blending_draw(img)

    ox = 210 + pose.root_x * SUPER
    ground_y = 386 + pose.root_y * SUPER
    bob = pose.bob * SUPER

    shadow_w = 138 + abs(pose.lean) * 0.6
    shadow_h = 22 + abs(pose.bob) * 0.3
    _ellipse(draw, (ox - shadow_w / 2, ground_y - 6, ox + shadow_w / 2, ground_y - 6 + shadow_h), SHADOW, outline=None)

    hip_back = (ox - 42, ground_y - 112 - bob)
    hip_front = (ox - 4, ground_y - 114 - bob)
    knee_back = _rot((ox - 74, ground_y - 54 - bob), hip_back, pose.rear_leg)
    knee_front = _rot((ox + 16, ground_y - 48 - bob), hip_front, pose.front_leg)
    ankle_back = (knee_back[0] + 22, knee_back[1] + 48)
    ankle_front = (knee_front[0] + 24, knee_front[1] + 44)
    foot_back = (ankle_back[0] + 34, ground_y - 6)
    foot_front = (ankle_front[0] + 34, ground_y - 6)

    _draw_leg(draw, hip_back, knee_back, ankle_back, foot_back, fill=GREEN_DARK, lift=pose.rear_foot_lift * SUPER)

    abdomen_box = (ox - 122, ground_y - 190 - bob - pose.abdomen_lift * SUPER, ox - 10, ground_y - 104 - bob)
    wing_box = (ox - 84, ground_y - 214 - bob, ox + 10, ground_y - 128 - bob)
    _ellipse(draw, wing_box, (184, 235, 226, 160), outline=(86, 120, 120, 150), width=3)
    _ellipse(draw, abdomen_box, GREEN, outline=OUTLINE, width=6)
    _ellipse(draw, (abdomen_box[0] + 14, abdomen_box[1] + 10, abdomen_box[2] - 12, abdomen_box[3] - 10), GREEN_LIGHT, outline=None)

    chest = (ox + pose.lean * 0.5, ground_y - 212 - bob)
    thorax_box = (chest[0] - 56, chest[1] - 62, chest[0] + 54, chest[1] + 44)
    coat_skirt = [
        (chest[0] - 44, chest[1] + 18),
        (chest[0] + 28, chest[1] + 10),
        (chest[0] + 44 + pose.coat_flare * SUPER, chest[1] + 76),
        (chest[0] - 12, chest[1] + 82),
        (chest[0] - 48 - pose.coat_flare * SUPER * 0.3, chest[1] + 74),
    ]

    _draw_leg(draw, hip_front, knee_front, ankle_front, foot_front, fill=GREEN, lift=pose.front_foot_lift * SUPER)
    _poly(draw, coat_skirt, COAT_DARK, width=5)
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

    neck = (chest[0] + 18, chest[1] - 66)
    head_center = _rot((neck[0] + 20, neck[1] - 18), neck, pose.head_tilt)
    head_box = (head_center[0] - 42, head_center[1] - 36, head_center[0] + 36, head_center[1] + 30)
    _ellipse(draw, head_box, GREEN_LIGHT, outline=OUTLINE, width=6)
    _ellipse(draw, (head_box[0] + 8, head_box[1] + 10, head_box[2] - 10, head_box[3] - 10), GREEN_PALE, outline=None)
    _ellipse(draw, (head_center[0] - 8, head_center[1] + 8, head_center[0] + 20, head_center[1] + 24), CHEEK, outline=None)

    eye_center = _rot((head_center[0] + 14, head_center[1] - 2), head_center, pose.head_tilt)
    if pose.x_eye:
        for sign in (-1, 1):
            _line(draw, [(eye_center[0] - 7, eye_center[1] - 7 * sign), (eye_center[0] + 7, eye_center[1] + 7 * sign)], fill=EYE, width=4)
    elif pose.blink:
        _line(draw, [(eye_center[0] - 10, eye_center[1]), (eye_center[0] + 8, eye_center[1] + 2)], fill=EYE, width=4)
    else:
        _ellipse(draw, (eye_center[0] - 10, eye_center[1] - 8, eye_center[0] + 8, eye_center[1] + 8), WHITE, outline=OUTLINE, width=3)
        pupil = (eye_center[0] + 2, eye_center[1] + 1)
        _circle(draw, pupil, 4, EYE, width=1)
        _circle(draw, (pupil[0] - 1, pupil[1] - 1), 1, EYE_HL, outline=None, width=0)

    mouth_y = head_center[1] + 16
    mouth_w = 16
    mouth_h = 3 + pose.mouth_open * 26
    _line(draw, [
        _rot((head_center[0] - 2, mouth_y), head_center, pose.head_tilt),
        _rot((head_center[0] + mouth_w, mouth_y + mouth_h * 0.15), head_center, pose.head_tilt),
    ], fill=OUTLINE, width=4)
    if pose.mouth_open > 0.04:
        tongue = [
            _rot((head_center[0] + 4, mouth_y + 2), head_center, pose.head_tilt),
            _rot((head_center[0] + 15, mouth_y + 2), head_center, pose.head_tilt),
            _rot((head_center[0] + 12, mouth_y + mouth_h), head_center, pose.head_tilt),
            _rot((head_center[0] + 5, mouth_y + mouth_h), head_center, pose.head_tilt),
        ]
        _poly(draw, tongue, RED_LIGHT, outline=None, width=0)

    for side, lift in ((-1, -8), (1, 10)):
        ant_base = _rot((head_center[0] - 4, head_center[1] - 20), head_center, pose.head_tilt)
        ant_mid = _rot((head_center[0] + side * 8, head_center[1] - 62 + side * 4 + pose.antenna_sway), head_center, pose.head_tilt)
        ant_tip = _rot((head_center[0] + side * 22, head_center[1] - 96 + pose.antenna_sway * 1.2 + lift), head_center, pose.head_tilt)
        _line(draw, [ant_base, ant_mid, ant_tip], fill=GREEN_DARK, width=6)
        _circle(draw, ant_tip, 4, GOLD_LIGHT, width=2)

    _draw_hat(draw, head_center, pose.head_tilt)

    shoulder_back = (chest[0] - 28, chest[1] - 20)
    elbow_back = _rot((shoulder_back[0] - 18, shoulder_back[1] + 28), shoulder_back, pose.arm_back)
    hand_back = _rot((elbow_back[0] + 2, elbow_back[1] + 26), elbow_back, pose.arm_back * 0.3)
    _draw_arm(draw, shoulder_back, elbow_back, hand_back, fill=GREEN_DARK, baton=False)

    shoulder_front = (chest[0] + 22, chest[1] - 18)
    elbow_front = _rot((shoulder_front[0] + 20, shoulder_front[1] + 18), shoulder_front, pose.arm_front)
    hand_front = _rot((elbow_front[0] + 22, elbow_front[1] + 20), elbow_front, pose.arm_front * 0.35)
    _draw_arm(draw, shoulder_front, elbow_front, hand_front, fill=GREEN, baton=True, baton_angle=pose.baton_angle, baton_extend=pose.baton_extend)

    if pose.salute > 0.01:
        salute_hand = _rot((head_center[0] + 4, head_center[1] - 36), head_center, pose.head_tilt)
        _line(draw, [
            (salute_hand[0] - 10, salute_hand[1] + 10),
            salute_hand,
            (salute_hand[0] + 16, salute_hand[1] - 2),
        ], fill=GOLD_LIGHT, width=5)

    return img.resize(FRAME_SIZE, Image.Resampling.LANCZOS)


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
    outputs = build_sheet(
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
    return [Path(outputs[key]) for key in keys if outputs.get(key)]


__all__ = ["ACTOR_METADATA", "render", "render_portraits"]
