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
from ambition_sprite2d_renderer.core.draw import blending_draw

TARGET_NAME = "marie_curry"
FRAME_SIZE = (128, 128)
WORK_SIZE = (FRAME_SIZE[0] * 4, FRAME_SIZE[1] * 4)

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 140),
    ("walk", 8, 96),
    ("talk", 6, 110),
    ("interact", 6, 104),
    ("stir", 8, 82),
    ("toss", 7, 86),
    ("taunt", 8, 92),
    ("hurt", 5, 90),
    ("death", 8, 112),
]

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_marie_curry",
        "display_name": "Marie Curry",
    },
    "authoring_description": {
        "parody_of": "Marie Curie",
        "core_joke": "A culinary-radiant parody of Marie Curie: the brilliant scientist reimagined as a dangerous curry alchemist whose cookware glows with suspiciously energetic spice.",
        "visual_inspirations": [
            "Marie Curie portraiture and late-19th-century scholar silhouettes",
            "apron-over-dress chef-scientist hybrid costume",
            "a glowing curry pot carried like lab equipment",
            "green radiance cues kept stylized and playful rather than realistic or grim",
        ],
        "design_notes": [
            "The joke should read instantly as Curie becomes Curry, but the character should still feel competent, prestigious, and formidable.",
            "Blend laboratory and kitchen language: apron, stirring spoon, potion pot, notebook-minded posture.",
            "She should feel dangerous because she knows exactly what she is doing, not because she is chaotic.",
            "The glow should imply radiant chemistry and experimental cooking at once.",
        ],
        "reference_hooks": [
            "radioactivity and luminous materials",
            "scientific rigor",
            "kitchen alchemy",
            "precise, understated intensity",
        ],
    },
    "gameplay_description": {
        "role": "mid-range alchemist / area-control scientist",
        "combat_identity": [
            "stirs volatile curry compounds before releasing them",
            "controls space with splashes, fumes, or radiant puddles",
            "reads as a smart caster rather than a brawler",
        ],
        "signature_moves": [
            "Radium Roux: a glowing stir that charges her concoction",
            "Curry Burst: a lob or toss of volatile sauce",
            "Half-Life Simmer: a lingering hazard puddle or aura",
        ],
        "authoring_notes": [
            "This sheet includes a stir attack and a toss animation that can back future spell or projectile mechanics.",
            "A later expansion would benefit from a dedicated throw, splash impact, and maybe a 'measure sample' or note-taking pose.",
            "Dialog should feel calm, exacting, and a little dry, even while the food chemistry becomes absurd.",
        ],
    },
    "dialogue_hints": {
        "suggested_barks": [
            "Careful, it is still reactive.",
            "Let it simmer.",
            "A measured dose.",
            "Observe the glow.",
            "That mixture was unstable anyway.",
            "The spice is luminous today.",
        ],
        "fallback_dialogue": [
            "Precision matters in both science and cooking.",
            "People panic around invisible forces. I prefer to study them.",
            "A good experiment and a good recipe both deserve patience.",
            "The hazard is usually not the substance. It is the carelessness.",
        ],
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": [
            "story",
            "combatant",
            "scientist_parody",
            "chemist",
            "chef",
            "caster",
            "mentor",
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
            "crawl": False,
            "use_lifts": True,
            "door_access": ["public"],
        },
        "interactions": {
            "talk": True,
            "trade": None,
            "carry": True,
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
        "action.ability.primary": {
            "animation": "stir",
            "events": [
                {"t": 0.28, "event": "cast_start", "source": "marie_curry.stir"},
                {"t": 0.70, "event": "cast_release", "source": "marie_curry.stir"},
            ],
        },
        "action.ranged.primary": {
            "animation": "toss",
            "events": [
                {"t": 0.52, "event": "projectile_release", "source": "marie_curry.toss"},
            ],
        },
        "emote.taunt": {"animation": "taunt", "events": []},
        "damage.hit": {"animation": "hurt", "events": []},
        "lifecycle.death": {"animation": "death", "events": []},
    },
    "sockets": {
        "head": {"source": "marie_curry.authored", "point": {"x": 72.0, "y": 24.0}},
        "chest": {"source": "marie_curry.authored", "point": {"x": 66.0, "y": 52.0}},
        "hand_l": {"source": "marie_curry.authored", "point": {"x": 56.0, "y": 66.0}},
        "hand_r": {"source": "marie_curry.authored", "point": {"x": 88.0, "y": 64.0}},
        "speech_bubble": {"source": "marie_curry.authored", "point": {"x": 72.0, "y": 8.0}},
        "projectile_origin": {"source": "marie_curry.authored", "point": {"x": 98.0, "y": 62.0}},
        "prop_anchor": {"source": "marie_curry.authored", "point": {"x": 54.0, "y": 70.0}},
    },
    "tags": [
        "story",
        "combatant",
        "scientist_parody",
        "chemist",
        "chef",
        "caster",
        "marie_curie_parody",
    ],
}

OUTLINE = (24, 22, 30, 255)
SHADOW = (0, 0, 0, 46)
SKIN = (229, 199, 171, 255)
SKIN_SHADE = (203, 169, 138, 255)
HAIR_DARK = (71, 57, 52, 255)
HAIR = (111, 92, 84, 255)
HAIR_LIGHT = (150, 131, 124, 255)
DRESS_DARK = (79, 67, 110, 255)
DRESS = (119, 101, 161, 255)
DRESS_LIGHT = (158, 138, 199, 255)
APRON = (234, 237, 242, 255)
APRON_SHADE = (205, 211, 218, 255)
POT_DARK = (76, 84, 96, 255)
POT = (110, 121, 139, 255)
POT_LIGHT = (152, 164, 184, 255)
GLOW = (118, 250, 134, 220)
GLOW_BRIGHT = (210, 255, 190, 235)
CURRY = (222, 168, 54, 255)
CURRY_HOT = (255, 216, 93, 255)
SPOON = (122, 83, 58, 255)
SPOON_METAL = (186, 193, 203, 255)
EYE = (34, 28, 36, 255)
WHITE = (245, 247, 250, 255)
RED = (176, 64, 78, 255)
RADIUM = (94, 255, 142, 255)


def _ease(t: float) -> float:
    return t * t * (3.0 - 2.0 * t)


@dataclass
class Pose:
    root_x: float = 0.0
    root_y: float = 0.0
    bob: float = 0.0
    lean: float = 0.0
    head_tilt: float = 0.0
    mouth_open: float = 0.0
    bun_bounce: float = 0.0
    front_arm: float = 0.0
    back_arm: float = 0.0
    spoon_angle: float = 0.0
    pot_swing: float = 0.0
    front_leg: float = 0.0
    back_leg: float = 0.0
    front_foot_lift: float = 0.0
    back_foot_lift: float = 0.0
    stir_phase: float = 0.0
    toss_arc: float = 0.0
    glow_pulse: float = 0.0
    blink: bool = False
    x_eye: bool = False

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
        self.mouth_open = 0.0
        self.bun_bounce = 0.0
        self.front_arm = 0.0
        self.back_arm = 0.0
        self.spoon_angle = -18.0
        self.pot_swing = 0.0
        self.front_leg = 0.0
        self.back_leg = 0.0
        self.front_foot_lift = 0.0
        self.back_foot_lift = 0.0
        self.stir_phase = 0.0
        self.toss_arc = 0.0
        self.glow_pulse = 0.0
        self.blink = False
        self.x_eye = False

        if anim == "idle":
            self.bob = s * 1.4
            self.lean = s * 1.4
            self.head_tilt = -s * 1.2
            self.front_arm = 8.0 + s * 2.0
            self.back_arm = -10.0
            self.pot_swing = s * 3.0
            self.front_leg = c * 1.8
            self.back_leg = -c * 1.8
            self.glow_pulse = (s + 1.0) * 0.5
            self.blink = frame_idx == frame_count - 2
        elif anim == "walk":
            self.root_x = s * 2.4
            self.bob = abs(s) * 3.0 - 0.8
            self.lean = s * 2.6
            self.head_tilt = -s * 1.4
            self.front_arm = 14.0 * s + 6.0
            self.back_arm = -12.0 * s - 8.0
            self.pot_swing = -s * 8.0
            self.front_leg = 20.0 * s
            self.back_leg = -20.0 * s
            self.front_foot_lift = max(0.0, s) * 8.0
            self.back_foot_lift = max(0.0, -s) * 8.0
            self.glow_pulse = (c + 1.0) * 0.5
        elif anim == "talk":
            self.bob = s * 1.0
            self.lean = s * 1.1
            self.head_tilt = -s * 2.1
            self.front_arm = 10.0 + s * 4.0
            self.back_arm = -8.0
            self.spoon_angle = -34.0 + s * 8.0
            self.pot_swing = 3.0
            self.mouth_open = 0.12 + max(0.0, c) * 0.12
            self.glow_pulse = (s + 1.0) * 0.5
        elif anim == "interact":
            tt = _ease(t)
            self.bob = -math.sin(tt * math.pi) * 1.6
            self.lean = (tt - 0.5) * 18.0
            self.head_tilt = _ease(1.0 - t) * 6.0 - 2.0
            self.front_arm = -14.0 + tt * 42.0
            self.back_arm = -8.0
            self.spoon_angle = -70.0 + tt * 52.0
            self.pot_swing = -3.0 + tt * 10.0
            self.glow_pulse = 0.7
            self.mouth_open = 0.08
        elif anim == "stir":
            tt = frame_idx / max(1, frame_count)
            ang = math.tau * tt
            self.bob = math.sin(ang) * 1.4
            self.lean = math.sin(ang) * 2.4
            self.head_tilt = -math.cos(ang) * 2.2
            self.front_arm = 24.0 + math.sin(ang) * 18.0
            self.back_arm = -8.0
            self.spoon_angle = -20.0 + math.sin(ang) * 84.0
            self.pot_swing = math.cos(ang) * 5.0
            self.stir_phase = tt
            self.glow_pulse = (math.sin(ang * 2.0) + 1.0) * 0.5
            self.mouth_open = 0.06 + max(0.0, math.cos(ang)) * 0.08
        elif anim == "toss":
            tt = _ease(t)
            wave = math.sin(tt * math.pi)
            self.root_x = -3.0 + tt * 12.0
            self.bob = -wave * 3.0
            self.lean = -12.0 + tt * 24.0
            self.head_tilt = -8.0 + tt * 14.0
            self.front_arm = -6.0 + tt * 72.0
            self.back_arm = -10.0 + tt * 8.0
            self.spoon_angle = -84.0 + tt * 136.0
            self.pot_swing = -10.0 + tt * 18.0
            self.toss_arc = wave
            self.glow_pulse = 1.0
            self.mouth_open = 0.12 * wave
        elif anim == "taunt":
            self.bob = abs(s) * 1.5
            self.lean = s * 1.8
            self.head_tilt = -s * 2.0
            self.front_arm = 10.0 + s * 10.0
            self.back_arm = -6.0
            self.spoon_angle = -88.0
            self.pot_swing = 4.0
            self.glow_pulse = 0.9
            self.mouth_open = 0.08 + max(0.0, c) * 0.09
        elif anim == "hurt":
            hit = math.sin(t * math.pi)
            shake = math.sin(t * math.pi * 4.0) * (1.0 - t)
            self.root_x = shake * 4.0
            self.bob = -hit * 2.5
            self.lean = -16.0 * hit
            self.head_tilt = 14.0 * hit
            self.front_arm = 28.0 * hit
            self.back_arm = 18.0 * hit
            self.front_leg = 10.0 * hit
            self.back_leg = -8.0 * hit
            self.mouth_open = 0.12 * hit
            self.glow_pulse = 0.25
        elif anim == "death":
            tt = _ease(t)
            self.root_x = -tt * 14.0
            self.root_y = tt * 10.0
            self.bob = -tt * 2.0
            self.lean = -tt * 82.0
            self.head_tilt = tt * 18.0
            self.front_arm = tt * 88.0
            self.back_arm = tt * 64.0
            self.spoon_angle = -18.0 - tt * 120.0
            self.pot_swing = tt * 10.0
            self.front_leg = tt * 42.0
            self.back_leg = tt * 28.0
            self.front_foot_lift = tt * 10.0
            self.back_foot_lift = tt * 4.0
            self.glow_pulse = 0.2
            self.x_eye = tt > 0.55
            self.mouth_open = tt * 0.15


def _rot(point: tuple[float, float], origin: tuple[float, float], degrees: float) -> tuple[float, float]:
    ang = math.radians(degrees)
    px, py = point
    ox, oy = origin
    dx = px - ox
    dy = py - oy
    ca = math.cos(ang)
    sa = math.sin(ang)
    return (ox + dx * ca - dy * sa, oy + dx * sa + dy * ca)


def _ellipse(draw: ImageDraw.ImageDraw, bbox, fill, outline=OUTLINE, width=5):
    draw.ellipse(bbox, fill=fill, outline=outline, width=width)


def _poly(draw: ImageDraw.ImageDraw, points, fill, outline=OUTLINE, width=5):
    draw.polygon(points, fill=fill)
    if outline is not None:
        draw.line(list(points) + [points[0]], fill=outline, width=width)


def _line(draw: ImageDraw.ImageDraw, points, fill, width=5):
    draw.line(points, fill=fill, width=width, joint="curve")


def _circle(draw: ImageDraw.ImageDraw, center, radius, fill, outline=OUTLINE, width=4):
    x, y = center
    _ellipse(draw, (x - radius, y - radius, x + radius, y + radius), fill=fill, outline=outline, width=width)


def _piece(key: tuple, size: tuple, pivot: tuple, paint) -> tuple:
    """A piece of Marie painted once (``shape_rig``) in work pixels on a
    ``size`` canvas, its anchor at ``pivot``. ``key`` names everything
    ``paint(draw)`` reads."""
    return shape_rig.piece(("marie_curry",) + key, size, pivot, paint)


def _angle(a, b) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def _ahead(a, length: float, degrees: float):
    r = math.radians(degrees)
    return (a[0] + math.cos(r) * length, a[1] + math.sin(r) * length)


def _segment(img: Image.Image, a, b, length: float, width: int, fill, name: str, *, cap: bool = False, joints=()) -> None:
    """A thick limb segment of ``length`` from ``a`` toward ``b``, painted once
    along +x: ``cap`` rounds its first end (the polyline's curved joint), and
    ``joints`` are ``(offset, radius)`` outlined dots on it (offset 0 or the
    far end; they are round, so turning them changes nothing)."""
    pad = width // 2 + 10

    def paint(d) -> None:
        if cap:
            d.ellipse((pad - width / 2, pad - width / 2, pad + width / 2, pad + width / 2), fill=fill)
        _line(d, [(pad, pad), (pad + length, pad)], fill=fill, width=width)
        for offset, r in joints:
            _circle(d, (pad + offset, pad), r, fill, width=2)

    part = _piece(("segment", length, width, fill, cap, tuple(joints)), (length + 2 * pad, 2 * pad), (pad, pad), paint)
    shape_rig.place(img, part, a, _angle(a, b), name)


#: Leg bones (work pixels): hip to knee, knee to ankle.
THIGH = 56.0
SHIN = 48.0
#: Arm bones (work pixels): (upper, forearm) for the back and front arm.
BACK_ARM = (math.hypot(18.0, 28.0), math.hypot(8.0, 28.0))
FRONT_ARM = (math.hypot(16.0, 18.0), math.hypot(20.0, 18.0))


def _draw_leg(img: Image.Image, hip, knee, ankle, foot, *, fill, lift=0.0, side: str):
    """Thigh and shin bones of fixed length aimed at the posed knee and ankle,
    then the foot reaching the ground; joint dots ride the bones."""
    knee = _ahead(hip, THIGH, _angle(hip, (knee[0], knee[1] - lift * 0.25)))
    ankle_aim = (ankle[0], ankle[1] - lift * 0.55)
    ankle = _ahead(knee, SHIN, _angle(knee, ankle_aim))
    foot2 = (foot[0], foot[1] - lift)
    reach = float(round(math.dist(ankle, foot2) / 2.0) * 2)
    _segment(img, ankle, foot2, reach, 18, fill, f"{side}_foot", cap=True)
    _segment(img, hip, knee, THIGH, 18, fill, f"{side}_thigh", joints=((0.0, 7),))
    _segment(img, knee, ankle, SHIN, 18, fill, f"{side}_shin", cap=True, joints=((0.0, 6), (SHIN, 5)))


def _draw_arm(img: Image.Image, shoulder, elbow, hand, bones, *, fill, side: str):
    """Upper arm and forearm bones; returns where the hand landed."""
    upper, fore = bones
    elbow = _ahead(shoulder, upper, _angle(shoulder, elbow))
    hand = _ahead(elbow, fore, _angle(elbow, hand))
    _segment(img, shoulder, elbow, upper, 14, fill, f"{side}_upper_arm", joints=((0.0, 6),))
    _segment(img, elbow, hand, fore, 14, fill, f"{side}_forearm", cap=True, joints=((0.0, 5), (fore, 5)))
    return hand


def _paint_spoon(d, hand) -> None:
    """The spoon held level from ``hand``; the whole spoon turns with its angle."""
    hx, hy = hand
    end = (hx + 38.0, hy)
    bowl = (end[0] + 10.0, end[1])
    _line(d, [hand, end], fill=SPOON, width=6)
    _line(d, [hand, end], fill=OUTLINE, width=2)
    _ellipse(d, (bowl[0] - 8, bowl[1] - 5, bowl[0] + 8, bowl[1] + 5), SPOON_METAL, outline=OUTLINE, width=2)


def _draw_curry_glow(draw: ImageDraw.ImageDraw, center, radius, intensity=0.5):
    alpha = 40 + int(110 * intensity)
    alpha2 = 90 + int(110 * intensity)
    x, y = center
    _ellipse(draw, (x - radius - 16, y - radius - 12, x + radius + 16, y + radius + 18), (118, 250, 134, alpha), outline=None, width=0)
    _ellipse(draw, (x - radius - 6, y - radius - 4, x + radius + 10, y + radius + 10), (210, 255, 190, alpha2), outline=None, width=0)


def _paint_torso(d, torso) -> None:
    """Skirt, bodice, apron and the radium badge around ``torso``."""
    skirt = [
        (torso[0] - 38, torso[1] + 36),
        (torso[0] + 24, torso[1] + 32),
        (torso[0] + 42, torso[1] + 108),
        (torso[0] - 52, torso[1] + 108),
    ]
    _poly(d, skirt, DRESS_DARK, width=5)
    _ellipse(d, (torso[0] - 42, torso[1] - 52, torso[0] + 34, torso[1] + 44), DRESS, outline=OUTLINE, width=6)
    apron = [
        (torso[0] - 16, torso[1] - 8),
        (torso[0] + 18, torso[1] - 4),
        (torso[0] + 12, torso[1] + 78),
        (torso[0] - 22, torso[1] + 80),
    ]
    _poly(d, apron, APRON, width=4)
    _line(d, [(torso[0] - 10, torso[1] - 18), (torso[0] - 32, torso[1] + 8)], fill=APRON_SHADE, width=4)
    _line(d, [(torso[0] + 4, torso[1] - 18), (torso[0] + 28, torso[1] + 4)], fill=APRON_SHADE, width=4)
    _circle(d, (torso[0] + 18, torso[1] - 26), 6, RADIUM, width=2)
    _line(d, [(torso[0] + 18, torso[1] - 34), (torso[0] + 18, torso[1] - 18)], fill=OUTLINE, width=2)
    _line(d, [(torso[0] + 10, torso[1] - 26), (torso[0] + 26, torso[1] - 26)], fill=OUTLINE, width=2)


def _paint_head(d, head_center, bun_bounce: float, eyes: str, mouth_open: float) -> None:
    """Hair, face, bun, fringe, eye and mouth, untilted, around ``head_center``."""
    hair_back = (head_center[0] - 34, head_center[1] - 26, head_center[0] + 20, head_center[1] + 34)
    _ellipse(d, hair_back, HAIR_DARK, outline=OUTLINE, width=5)
    _ellipse(d, (head_center[0] - 28, head_center[1] - 24, head_center[0] + 20, head_center[1] + 26), SKIN, outline=OUTLINE, width=5)
    _circle(d, (head_center[0] - 18, head_center[1] - 30 - bun_bounce * 4), 12, HAIR, width=4)
    fringe = [(head_center[0] - 24, head_center[1] - 14), (head_center[0] + 8, head_center[1] - 22), (head_center[0] + 12, head_center[1] - 6), (head_center[0] - 18, head_center[1] + 2)]
    _poly(d, fringe, HAIR, width=3)
    _line(d, [(head_center[0] - 8, head_center[1] - 24), (head_center[0] + 10, head_center[1] - 18)], fill=HAIR_LIGHT, width=3)
    eye_center = (head_center[0] + 8, head_center[1] - 2)
    if eyes == "x":
        for sign in (-1, 1):
            _line(d, [(eye_center[0] - 6, eye_center[1] - 6 * sign), (eye_center[0] + 6, eye_center[1] + 6 * sign)], fill=EYE, width=4)
    elif eyes == "blink":
        _line(d, [(eye_center[0] - 8, eye_center[1]), (eye_center[0] + 6, eye_center[1] + 1)], fill=EYE, width=4)
    else:
        _ellipse(d, (eye_center[0] - 8, eye_center[1] - 6, eye_center[0] + 7, eye_center[1] + 6), WHITE, outline=OUTLINE, width=2)
        _circle(d, (eye_center[0] + 1, eye_center[1]), 3, EYE, width=1)
    mouth_y = head_center[1] + 14
    _line(d, [(head_center[0] - 2, mouth_y), (head_center[0] + 12, mouth_y + mouth_open * 6)], fill=OUTLINE, width=3)


def _paint_pot(d, pot_center, glow: float) -> None:
    """The glowing curry pot around ``pot_center``."""
    _draw_curry_glow(d, (pot_center[0], pot_center[1] - 14), 20, glow)
    _ellipse(d, (pot_center[0] - 26, pot_center[1] - 18, pot_center[0] + 22, pot_center[1] + 18), POT, outline=OUTLINE, width=5)
    _ellipse(d, (pot_center[0] - 22, pot_center[1] - 22, pot_center[0] + 18, pot_center[1] - 6), CURRY, outline=OUTLINE, width=3)
    _ellipse(d, (pot_center[0] - 18, pot_center[1] - 18, pot_center[0] + 14, pot_center[1] - 10), CURRY_HOT, outline=None, width=0)
    _line(d, [(pot_center[0] - 28, pot_center[1] - 6), (pot_center[0] - 38, pot_center[1] + 6)], fill=POT_DARK, width=5)
    _line(d, [(pot_center[0] + 24, pot_center[1] - 6), (pot_center[0] + 34, pot_center[1] + 4)], fill=POT_DARK, width=5)


def _draw_character(pose: Pose, anim: str, frame_idx: int, frame_count: int):
    """Marie as a rig: shadow, torso, head (turned by its tilt), pot and spoon
    are pieces painted once; legs and arms are bones of fixed length; the stir
    and toss effects change every frame and are one draw."""
    img = Image.new("RGBA", WORK_SIZE, (0, 0, 0, 0))

    ox = 216 + pose.root_x * 4
    ground_y = 388 + pose.root_y * 4
    bob = pose.bob * 4

    shadow = _piece(("shadow",), (128, 30), (64, 7), lambda d: _ellipse(d, (4, 2, 126, 25), SHADOW, outline=None, width=0))
    shape_rig.place(img, shadow, (ox, ground_y), 0.0, "shadow")

    hip_back = (ox - 18, ground_y - 120 - bob)
    hip_front = (ox + 14, ground_y - 120 - bob)
    knee_back = _rot((ox - 20, ground_y - 64 - bob), hip_back, pose.back_leg)
    knee_front = _rot((ox + 18, ground_y - 62 - bob), hip_front, pose.front_leg)
    ankle_back = (knee_back[0] - 2, knee_back[1] + 48)
    ankle_front = (knee_front[0] + 2, knee_front[1] + 48)
    foot_back = (ankle_back[0] + 18, ground_y - 2)
    foot_front = (ankle_front[0] + 20, ground_y - 2)

    _draw_leg(img, hip_back, knee_back, ankle_back, foot_back, fill=DRESS_DARK, lift=pose.back_foot_lift * 4, side="back")
    _draw_leg(img, hip_front, knee_front, ankle_front, foot_front, fill=DRESS, lift=pose.front_foot_lift * 4, side="front")

    torso = (ox, ground_y - 210 - bob)
    shape_rig.place(img, _piece(("torso",), (110, 176), (60, 60), lambda d: _paint_torso(d, (60, 60))), torso, 0.0, "torso")

    neck = (torso[0] + pose.lean * 0.6, torso[1] - 50)
    head_center = _rot((neck[0] + 8, neck[1] - 20), neck, pose.head_tilt)
    eyes = "x" if pose.x_eye else ("blink" if pose.blink else "open")
    bun = round(pose.bun_bounce * 4) / 4
    mouth = round(pose.mouth_open * 25) / 25
    head = _piece(("head", bun, eyes, mouth), (76, 96), (40, 52), lambda d: _paint_head(d, (40, 52), bun, eyes, mouth))
    shape_rig.place(img, head, head_center, pose.head_tilt, "head")

    pot_center = (torso[0] - 40, torso[1] + 34 + pose.pot_swing * 0.5)
    glow = round(pose.glow_pulse * 10) / 10
    pot = _piece(("pot", glow), (96, 96), (50, 52), lambda d: _paint_pot(d, (50, 52), glow))
    shape_rig.place(img, pot, pot_center, 0.0, "pot")

    shoulder_back = (torso[0] - 18, torso[1] - 8)
    elbow_back = _rot((shoulder_back[0] - 18, shoulder_back[1] + 28), shoulder_back, pose.back_arm)
    hand_back = _rot((elbow_back[0] - 8, elbow_back[1] + 28), elbow_back, pose.back_arm * 0.3)
    hand_back = _draw_arm(img, shoulder_back, elbow_back, hand_back, BACK_ARM, fill=DRESS_DARK, side="back")
    handle = (pot_center[0] - 18, pot_center[1] + 4)
    cord = float(round(math.dist(hand_back, handle) / 2.0) * 2)
    cord_part = _piece(("cord", cord), (cord + 8, 8), (4, 4), lambda d: _line(d, [(4, 4), (4 + cord, 4)], fill=OUTLINE, width=3))
    shape_rig.place(img, cord_part, hand_back, _angle(hand_back, handle), "cord")

    shoulder_front = (torso[0] + 18, torso[1] - 10)
    elbow_front = _rot((shoulder_front[0] + 16, shoulder_front[1] + 18), shoulder_front, pose.front_arm)
    hand_front = _rot((elbow_front[0] + 20, elbow_front[1] + 18), elbow_front, pose.front_arm * 0.35)
    hand_front = _draw_arm(img, shoulder_front, elbow_front, hand_front, FRONT_ARM, fill=APRON_SHADE, side="front")
    spoon = _piece(("spoon",), (72, 20), (6, 10), lambda d: _paint_spoon(d, (6, 10)))
    shape_rig.place(img, spoon, hand_front, pose.spoon_angle, "spoon")

    if anim in ("stir", "toss"):
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = blending_draw(layer)
        if anim == "stir":
            ang = math.tau * pose.stir_phase
            cx = pot_center[0] + math.cos(ang) * 10
            cy = pot_center[1] - 14 + math.sin(ang) * 6
            _line(draw, [(pot_center[0] - 6, pot_center[1] - 10), (cx, cy)], fill=GLOW_BRIGHT, width=3)
            for k in range(3):
                px = pot_center[0] - 4 + k * 10
                py = pot_center[1] - 34 - abs(math.sin(ang + k)) * 10
                _circle(draw, (px, py), 4 + k, GLOW_BRIGHT, outline=None, width=0)
        else:
            px = torso[0] + 58 + pose.toss_arc * 30
            py = torso[1] - 12 - pose.toss_arc * 26
            _draw_curry_glow(draw, (px, py), 10, 1.0)
            _ellipse(draw, (px - 12, py - 8, px + 12, py + 8), CURRY_HOT, outline=OUTLINE, width=2)
            splash = [(px + 10, py), (px + 28, py - 6), (px + 16, py + 14)]
            _poly(draw, splash, CURRY, width=2)
        box = layer.getbbox()
        if box is not None:
            shape_rig.place(img, (layer.crop(box), (0.0, 0.0)), (float(box[0]), float(box[1])), 0.0, "effects")

    return rigdoc.downsampled_canvas(img, FRAME_SIZE, Image.Resampling.LANCZOS)


def _render_frame(animation: str, frame_idx: int, frame_count: int):
    return _draw_character(Pose(animation, frame_idx, frame_count), animation, frame_idx, frame_count)


def render_portraits(out_dir: str | Path, **opts):
    del opts

    def portrait_frame(animation: str, frame_idx: int, frame_count: int):
        source = _draw_character(Pose(animation, frame_idx, frame_count), animation, frame_idx, frame_count)
        face = FaceGuide(
            center_x=72.0,
            center_y=26.0,
            width=40.0,
            height=40.0,
            source_width=128.0,
            source_height=128.0,
        )
        return render_framed_portrait(source, face, view_width=60.0, center_y=42.0)

    clips = {
        "default": PortraitClip.still(portrait_frame("idle", 2, 8)),
        "talking": PortraitClip(tuple(portrait_frame("talk", i, 6) for i in (0, 2, 4)), duration_ms=110, looping=True),
        "stirring": PortraitClip(tuple(portrait_frame("stir", i, 8) for i in (0, 2, 4, 6)), duration_ms=90, looping=True),
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
        sheet_tuning={"collision_scale": 1.55},
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
