"""Procedural full-action renderer for Ramen-nujan.

Ramen-nujan is a respectful visual parody of Srinivasa Ramanujan: a young
early-twentieth-century mathematician with a broad low forehead, lucid large
eyes, and a dense side-swept black hair wave. He belongs to the Flying
Spaghetti Monster faction, but remains a person rather than a food mascot.

His silhouette is deliberately unlike Girdle's: distinctly heavier through the
coat and cheeks, with a fuller scholar belly, a long asymmetrical coat, narrow
sloping shoulders, short widely planted legs, and an attached cross-body
academic stole. The stole carries noodle-gold stitching and tiny
vegetable-color embroidery. There is no bowl, fork, chopstick, ingredient, or
other held prop; the runtime held-item system remains authoritative.

The ramen references are explicitly vegetarian: mushroom cream, scallion green,
carrot orange, toasted sesame, and vegetable-broth gold. No meat, fish, egg,
or animal-broth motif appears anywhere in the design. His magic vocabulary is
mathematical and dreamlike: summation sweeps, factorial bursts, and a
playfully impossible ``-1/12`` theorem sigil. His charge / cast language reads
as power arriving in dreams, with tethered aura glyphs that stay connected to
his body instead of becoming detached props or particles. The dream charge is
purposefully sleepy and inward, as though the theorem came to him overnight and
he is waking up with it already formed.

This character-specific Python/Pillow renderer uses no generated-image inputs,
particles, floor ellipses, props, or drop shadows. Painter order is
``legs -> torso -> both arms -> ability auras -> head`` so both arms stay in
front of the torso, the dream/math effects remain integrated, and the head
stays in front of the complete body.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from PIL import Image, ImageDraw
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

ACTOR_METADATA = {
    "actor": {"character_id": "npc_ramen_nujan", "display_name": "Ramen-nujan"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": [
            "story",
            "humanoid",
            "mathematician",
            "number_theorist",
            "fsm_faction",
            "vegetarian",
            "playable_candidate",
            "dream_math",
        ],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": True,
            "climb": True,
            "fly": None,
            "swim": True,
            "crawl": True,
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
    "visual": {"default_pose": "idle"},
    "tags": [
        "story",
        "humanoid",
        "mathematician",
        "number_theorist",
        "fsm_faction",
        "vegetarian",
        "playable_candidate",
        "dream_math",
    ],
    "sockets": {
        "head": {"source": "explicit.profile.humanoid", "point": {"x": 65.0, "y": 28.0}},
        "chest": {"source": "explicit.profile.humanoid", "point": {"x": 65.0, "y": 65.0}},
        "hand_l": {"source": "explicit.profile.humanoid", "point": {"x": 48.0, "y": 87.0}},
        "hand_r": {"source": "explicit.profile.humanoid", "point": {"x": 84.0, "y": 86.0}},
        "speech_bubble": {"source": "explicit.profile.humanoid", "point": {"x": 65.0, "y": 5.0}},
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "traversal.jump": {"animation": "jump", "events": []},
        "traversal.fall": {"animation": "fall", "events": []},
        "action.melee.primary": {"animation": "slash", "events": []},
        "action.defense.block": {"animation": "block", "events": []},
        "action.defense.roll": {"animation": "roll", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
    },
}

TARGET_BASENAME = "ramen_nujan"
FRAME_SIZE = (128, 128)
SUPER = 4
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 145),
    ("walk", 8, 104),
    ("run", 8, 78),
    ("crouch", 6, 95),
    ("crouch_walk", 8, 88),
    ("jump", 6, 95),
    ("fall", 6, 95),
    ("land_hard", 8, 95),
    ("land_recovery", 6, 75),
    ("dash_startup", 4, 50),
    ("dash", 6, 65),
    ("slide", 6, 70),
    ("roll", 8, 58),
    ("wall_grab", 6, 110),
    ("wall_jump", 6, 85),
    ("ledge_grab", 6, 100),
    ("ledge_climb", 6, 100),
    ("ledge_getup", 6, 40),
    ("ledge_roll", 8, 37),
    ("ledge_getup_attack", 8, 37),
    ("climb", 8, 100),
    ("swim", 8, 105),
    ("float_glide", 8, 110),
    ("block", 6, 85),
    ("hit", 5, 90),
    ("death", 8, 110),
    ("talk", 8, 108),
    ("interact", 8, 92),
    ("jab", 5, 58),
    ("punch", 7, 72),
    ("slash", 8, 75),
    ("attack_side", 8, 65),
    ("attack_up", 8, 65),
    ("attack_down", 8, 65),
    ("air_neutral", 8, 60),
    ("air_forward", 7, 62),
    ("air_back", 7, 62),
    ("air_down", 7, 70),
    ("air_up", 7, 62),
    ("charge", 8, 76),
    ("cast", 8, 80),
    ("celebrate", 8, 92),
    ("taunt", 8, 95),
]

# Historical tailoring, warm South Indian skin tones, and restrained
# vegetarian-FSM accents.  The food joke is garment language, never a prop.
OUTLINE = (13, 16, 18, 255)
OUTLINE_SOFT = (33, 39, 40, 255)
SKIN = (157, 105, 72, 255)
SKIN_LIGHT = (196, 145, 101, 255)
SKIN_SHADE = (121, 76, 52, 255)
SKIN_DEEP = (78, 47, 36, 255)
HAIR = (23, 24, 25, 255)
HAIR_MID = (42, 44, 45, 255)
HAIR_GLEAM = (72, 74, 72, 255)
GLASS_TINT = (220, 230, 220, 40)  # retained for shared helper; no glasses are drawn
SUIT = (64, 43, 59, 255)          # deep aubergine scholar coat
SUIT_MID = (91, 58, 76, 255)
SUIT_LIGHT = (113, 75, 91, 255)
SUIT_DARK = (39, 28, 40, 255)
VEST = (47, 94, 66, 255)          # seaweed / scallion academic stole
SHIRT = (235, 224, 198, 255)      # mushroom cream
SHIRT_SHADE = (196, 181, 151, 255)
TIE = (116, 53, 37, 255)
NOODLE_GOLD = (220, 174, 75, 255) # vegetable-broth / toasted-noodle piping
SESAME = (239, 211, 139, 255)
SCALLION = (82, 132, 67, 255)
CARROT = (202, 91, 42, 255)
TROUSER = (38, 37, 47, 255)
TROUSER_LIGHT = (58, 55, 66, 255)
SHOE = (50, 37, 31, 255)
SHOE_LIGHT = (79, 57, 44, 255)
EYE_WHITE = (236, 225, 202, 255)
EYE = (24, 20, 18, 255)
MOUTH = (91, 44, 38, 255)
DREAM_AURA = (185, 231, 159, 255)
DREAM_GOLD = (248, 213, 115, 255)
DREAM_ORANGE = (234, 132, 75, 255)
SIGMA_WHITE = (255, 245, 219, 255)

@dataclass
class Pose:
    body_x: float = 0.0
    body_y: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    rotation: float = 0.0
    rotation_pivot: Point = (64.5, 84.0)
    head_x: float = 0.0
    head_y: float = 0.0
    head_tilt: float = 0.0
    blink: bool = False
    mouth_open: float = 0.0
    mouth_smile: float = 0.0
    brow_lift: float = 0.0
    near_shoulder: Point = (79.0, 56.0)
    near_elbow: Point = (84.0, 74.0)
    near_hand: Point = (83.0, 89.0)
    far_shoulder: Point = (50.0, 57.0)
    far_elbow: Point = (46.0, 75.0)
    far_hand: Point = (48.0, 90.0)
    near_hip: Point = (70.0, 91.0)
    near_knee: Point = (72.0, 104.0)
    near_ankle: Point = (73.0, 117.0)
    far_hip: Point = (59.0, 91.0)
    far_knee: Point = (58.0, 104.0)
    far_ankle: Point = (57.0, 117.0)
    near_hand_mode: str = "relaxed"
    far_hand_mode: str = "relaxed"

    def __init__(self, animation: str, frame_idx: int, nframes: int) -> None:
        phase = frame_idx / max(1, nframes)
        t = frame_idx / max(1, nframes - 1)
        wave = math.sin(phase * math.tau)
        cosine = math.cos(phase * math.tau)

        self.body_x = 0.0
        self.body_y = 0.0
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.rotation = 0.0
        self.rotation_pivot = (64.5, 84.0)
        self.head_x = 0.0
        self.head_y = 0.0
        self.head_tilt = -1.0
        self.blink = False
        self.mouth_open = 0.0
        self.mouth_smile = 0.0
        self.brow_lift = 0.0
        self.near_shoulder = (79.0, 56.0)
        self.near_elbow = (84.0, 74.0)
        self.near_hand = (83.0, 89.0)
        self.far_shoulder = (50.0, 57.0)
        self.far_elbow = (46.0, 75.0)
        self.far_hand = (48.0, 90.0)
        self.near_hip = (70.0, 91.0)
        self.near_knee = (72.0, 104.0)
        self.near_ankle = (73.0, 117.0)
        self.far_hip = (59.0, 91.0)
        self.far_knee = (58.0, 104.0)
        self.far_ankle = (57.0, 117.0)
        self.near_hand_mode = "relaxed"
        self.far_hand_mode = "relaxed"

        if animation == "idle":
            breath = 0.5 - 0.5 * cosine
            self.body_y = -0.45 * breath
            self.head_y = -0.25 * breath
            self.head_x = 0.25 * wave
            self.head_tilt = -1.3 + 0.55 * wave
            self.near_elbow = (84.0 + 0.6 * wave, 74.0)
            self.near_hand = (83.0 + 0.45 * wave, 89.0 + 0.35 * cosine)
            self.far_elbow = (46.0 - 0.45 * wave, 75.0)
            self.far_hand = (48.0 - 0.35 * wave, 90.0)
            self.blink = frame_idx == 6

        elif animation in {"walk", "run"}:
            running = animation == "run"
            gait = 1.0 if not running else 1.55
            stride = 8.5 * wave * gait
            near_lift = max(0.0, wave) * (5.0 if not running else 8.0)
            far_lift = max(0.0, -wave) * (5.0 if not running else 8.0)
            self.body_x = (0.8 if not running else 1.2) * wave
            self.body_y = -(1.2 if not running else 2.0) * abs(wave)
            self.head_x = 0.5 * wave
            self.head_y = -0.35 * abs(wave)
            self.head_tilt = (-2.0 if not running else -4.0) - 0.5 * wave
            self.near_knee = (72.0 + stride * 0.50, 104.0 - near_lift * 0.25)
            self.near_ankle = (73.0 + stride, 117.0 - near_lift)
            self.far_knee = (58.0 - stride * 0.48, 104.0 - far_lift * 0.25)
            self.far_ankle = (57.0 - stride * 0.92, 117.0 - far_lift)
            self.near_elbow = (84.0 - stride * 0.45, 74.0)
            self.near_hand = (83.0 - stride * 0.62, 89.0)
            self.far_elbow = (46.0 + stride * 0.38, 75.0)
            self.far_hand = (48.0 + stride * 0.54, 90.0)
            if running:
                self.near_hand_mode = self.far_hand_mode = "closed"

        elif animation in {"crouch", "crouch_walk"}:
            moving = animation == "crouch_walk"
            stride = wave if moving else 0.0
            self.scale_y = 0.79
            self.rotation_pivot = (64.5, 117.0)
            self.body_y = 1.0
            self.head_tilt = -3.0 + 0.7 * stride
            self.near_shoulder = (79.0, 60.0)
            self.far_shoulder = (50.0, 61.0)
            self.near_elbow = (87.0 + 3.0 * stride, 78.0)
            self.near_hand = (92.0 + 5.0 * stride, 91.0)
            self.far_elbow = (44.0 - 3.0 * stride, 79.0)
            self.far_hand = (39.0 - 5.0 * stride, 92.0)
            self.near_hip = (70.0, 95.0)
            self.far_hip = (59.0, 95.0)
            self.near_knee = (79.0 + 5.0 * stride, 105.0)
            self.near_ankle = (85.0 + 8.0 * stride, 117.0)
            self.far_knee = (51.0 - 5.0 * stride, 105.0)
            self.far_ankle = (45.0 - 8.0 * stride, 117.0)

        elif animation == "jump":
            preload = 1.0 - _smoothstep(t / 0.28)
            rise = _smoothstep((t - 0.08) / 0.58)
            self.body_y = 4.0 * preload - 7.0 * rise
            self.scale_y = 1.0 - 0.13 * preload
            self.rotation_pivot = (64.5, 117.0)
            self.head_tilt = -2.5 - 1.5 * rise
            self.near_elbow = (86.0, 69.0 - 6.0 * rise)
            self.near_hand = (93.0, 83.0 - 14.0 * rise)
            self.far_elbow = (44.0, 70.0 - 4.0 * rise)
            self.far_hand = (37.0, 86.0 - 10.0 * rise)
            self.near_knee = (78.0, 100.0)
            self.near_ankle = (82.0, 111.0)
            self.far_knee = (53.0, 101.0)
            self.far_ankle = (49.0, 112.0)
            self.near_hand_mode = self.far_hand_mode = "open"

        elif animation == "fall":
            self.body_y = -7.0 + 4.0 * t
            self.head_tilt = 2.0 + 2.0 * t
            self.mouth_open = 0.12
            self.near_elbow = (90.0, 66.0)
            self.near_hand = (101.0, 76.0)
            self.far_elbow = (40.0, 67.0)
            self.far_hand = (29.0, 78.0)
            self.near_knee = (77.0, 100.0)
            self.near_ankle = (82.0, 112.0)
            self.far_knee = (52.0, 101.0)
            self.far_ankle = (47.0, 113.0)
            self.near_hand_mode = self.far_hand_mode = "open"

        elif animation in {"land_hard", "land_recovery"}:
            impact = math.sin(math.pi * _clamp01(t / 0.78)) if animation == "land_hard" else 1.0 - _smoothstep(t)
            self.body_y = 3.0 * impact
            self.scale_y = 1.0 - 0.25 * impact
            self.rotation_pivot = (64.5, 117.0)
            self.head_tilt = -5.0 * impact
            self.near_shoulder = (79.0, 58.0 + 6.0 * impact)
            self.far_shoulder = (50.0, 59.0 + 6.0 * impact)
            self.near_elbow = (88.0, 76.0 + 3.0 * impact)
            self.near_hand = (95.0, 92.0 + 2.0 * impact)
            self.far_elbow = (43.0, 77.0 + 3.0 * impact)
            self.far_hand = (36.0, 93.0 + 2.0 * impact)
            self.near_knee = (79.0, 104.0)
            self.near_ankle = (84.0, 117.0)
            self.far_knee = (51.0, 104.0)
            self.far_ankle = (46.0, 117.0)

        elif animation in {"dash_startup", "dash"}:
            startup = animation == "dash_startup"
            charge = _smoothstep(t) if startup else 1.0
            self.rotation = -7.0 - 4.0 * charge
            self.rotation_pivot = (64.5, 93.0)
            self.body_x = (-2.0 * charge if startup else -2.0 + 6.0 * t)
            self.body_y = 2.5 * charge
            self.head_tilt = -3.0
            self.near_elbow = (70.0, 72.0)
            self.near_hand = (60.0, 85.0)
            self.far_elbow = (42.0, 70.0)
            self.far_hand = (31.0, 82.0)
            self.near_knee = (81.0 + 5.0 * charge, 102.0)
            self.near_ankle = (92.0 + 7.0 * charge, 117.0)
            self.far_knee = (51.0 - 5.0 * charge, 103.0)
            self.far_ankle = (41.0 - 7.0 * charge, 117.0)
            self.near_hand_mode = self.far_hand_mode = "closed"

        elif animation == "slide":
            self.scale_y = 0.65
            self.rotation = -12.0
            self.rotation_pivot = (64.5, 117.0)
            self.body_y = 2.0
            self.body_x = -2.0 + 6.0 * t
            self.head_tilt = -4.0
            self.near_shoulder = (79.0, 62.0)
            self.far_shoulder = (50.0, 63.0)
            self.near_elbow = (72.0, 80.0)
            self.near_hand = (62.0, 91.0)
            self.far_elbow = (43.0, 80.0)
            self.far_hand = (34.0, 93.0)
            self.near_hip = (71.0, 97.0)
            self.far_hip = (58.0, 97.0)
            self.near_knee = (86.0, 105.0)
            self.near_ankle = (101.0, 116.0)
            self.far_knee = (49.0, 105.0)
            self.far_ankle = (35.0, 117.0)

        elif animation == "roll":
            self.scale_x = 0.78
            self.scale_y = 0.72
            self.rotation = -360.0 * t
            self.rotation_pivot = (64.5, 80.0)
            self.body_x = -5.0 + 10.0 * t
            self.body_y = 6.0 - 2.5 * math.sin(math.pi * t)
            self.head_tilt = -2.0
            self.near_shoulder = (76.0, 66.0)
            self.far_shoulder = (53.0, 67.0)
            self.near_elbow = (77.0, 80.0)
            self.near_hand = (71.0, 91.0)
            self.far_elbow = (52.0, 81.0)
            self.far_hand = (58.0, 92.0)
            self.near_hip = (70.0, 94.0)
            self.far_hip = (59.0, 94.0)
            self.near_knee = (77.0, 102.0)
            self.near_ankle = (78.0, 110.0)
            self.far_knee = (52.0, 102.0)
            self.far_ankle = (51.0, 110.0)
            self.near_hand_mode = self.far_hand_mode = "closed"

        elif animation == "wall_grab":
            self.body_x = 8.0
            self.body_y = -4.0 + 0.7 * wave
            self.rotation = 4.0
            self.rotation_pivot = (65.0, 82.0)
            self.head_tilt = 1.5
            self.near_elbow = (94.0, 48.0)
            self.near_hand = (104.0, 36.0)
            self.far_elbow = (78.0, 50.0)
            self.far_hand = (96.0, 42.0)
            self.near_knee = (83.0, 98.0)
            self.near_ankle = (98.0, 106.0)
            self.far_knee = (68.0, 101.0)
            self.far_ankle = (91.0, 114.0)
            self.near_hand_mode = self.far_hand_mode = "grip"

        elif animation == "wall_jump":
            spring = _smoothstep(t)
            self.body_x = 8.0 - 18.0 * spring
            self.body_y = -4.0 - 5.0 * math.sin(math.pi * spring)
            self.rotation = 4.0 - 22.0 * spring
            self.rotation_pivot = (65.0, 82.0)
            self.head_tilt = 2.0 - 3.0 * spring
            self.near_elbow = _lerp_point((94.0, 48.0), (51.0, 67.0), spring)
            self.near_hand = _lerp_point((104.0, 36.0), (36.0, 77.0), spring)
            self.far_elbow = _lerp_point((78.0, 50.0), (45.0, 69.0), spring)
            self.far_hand = _lerp_point((96.0, 42.0), (31.0, 82.0), spring)
            self.near_knee = (83.0 - 9.0 * spring, 99.0)
            self.near_ankle = (98.0 - 19.0 * spring, 108.0)
            self.far_knee = (68.0 - 7.0 * spring, 101.0)
            self.far_ankle = (91.0 - 20.0 * spring, 114.0)
            self.near_hand_mode = self.far_hand_mode = "open"

        elif animation == "ledge_grab":
            self.body_y = 8.0 + 0.7 * wave
            self.head_y = 1.0
            self.head_tilt = -1.0 + 0.5 * wave
            self.near_shoulder = (78.0, 58.0)
            self.far_shoulder = (51.0, 59.0)
            self.near_elbow = (79.0, 38.0)
            self.near_hand = (73.0, 18.0)
            self.far_elbow = (55.0, 39.0)
            self.far_hand = (58.0, 18.0)
            self.near_knee = (77.0, 103.0)
            self.near_ankle = (83.0, 110.0)
            self.far_knee = (53.0, 102.0)
            self.far_ankle = (47.0, 109.0)
            self.near_hand_mode = self.far_hand_mode = "grip"

        elif animation in {"ledge_climb", "ledge_getup"}:
            climb = _smoothstep(t)
            self.body_y = 8.0 - 11.0 * climb
            self.scale_y = 0.88 + 0.12 * climb
            self.rotation_pivot = (64.5, 117.0)
            self.head_y = 3.0 * (1.0 - climb)
            self.head_tilt = -3.0 + 2.0 * climb
            self.near_elbow = _lerp_point((79.0, 38.0), (88.0, 74.0), climb)
            self.near_hand = _lerp_point((73.0, 18.0), (94.0, 90.0), climb)
            self.far_elbow = _lerp_point((55.0, 39.0), (43.0, 75.0), climb)
            self.far_hand = _lerp_point((58.0, 18.0), (37.0, 90.0), climb)
            self.near_hip = _lerp_point((70.0, 95.0), (70.0, 91.0), climb)
            self.far_hip = _lerp_point((59.0, 95.0), (59.0, 91.0), climb)
            self.near_knee = _lerp_point((77.0, 105.0), (72.0, 104.0), climb)
            self.near_ankle = _lerp_point((83.0, 110.0), (73.0, 117.0), climb)
            self.far_knee = _lerp_point((53.0, 104.0), (58.0, 104.0), climb)
            self.far_ankle = _lerp_point((47.0, 109.0), (57.0, 117.0), climb)
            self.near_hand_mode = self.far_hand_mode = "grip" if climb < 0.65 else "relaxed"

        elif animation == "ledge_roll":
            roll = _smoothstep((t - 0.12) / 0.88)
            self.scale_x = _lerp(1.0, 0.78, roll)
            self.scale_y = _lerp(0.88, 0.72, roll)
            self.rotation = -360.0 * roll
            self.rotation_pivot = (64.5, 77.0)
            self.body_x = -4.0 + 9.0 * roll
            self.body_y = 8.0 * (1.0 - roll) + 4.0 * roll - 2.0 * math.sin(math.pi * roll)
            self.head_tilt = -2.0
            self.near_elbow = _lerp_point((79.0, 38.0), (77.0, 80.0), roll)
            self.near_hand = _lerp_point((73.0, 18.0), (71.0, 91.0), roll)
            self.far_elbow = _lerp_point((55.0, 39.0), (52.0, 81.0), roll)
            self.far_hand = _lerp_point((58.0, 18.0), (58.0, 92.0), roll)
            self.near_hip = (70.0, 95.0)
            self.far_hip = (59.0, 95.0)
            self.near_knee = (77.0, 103.0)
            self.near_ankle = (79.0, 111.0)
            self.far_knee = (52.0, 103.0)
            self.far_ankle = (50.0, 111.0)
            self.near_hand_mode = self.far_hand_mode = "grip" if roll < 0.35 else "closed"

        elif animation == "ledge_getup_attack":
            rise = _smoothstep(_clamp01(t / 0.48))
            strike = _smoothstep(_clamp01((t - 0.32) / 0.52))
            self.body_y = 8.0 - 10.0 * rise
            self.rotation_pivot = (64.5, 117.0)
            self.scale_y = 0.88 + 0.12 * rise
            self.head_tilt = -3.0 + 3.0 * rise
            self.near_elbow = _lerp_point((79.0, 38.0), (96.0, 64.0), rise)
            self.near_hand = _lerp_point((73.0, 18.0), (112.0 + 4.0 * strike, 57.0 - 9.0 * strike), rise)
            self.far_elbow = _lerp_point((55.0, 39.0), (58.0, 68.0), rise)
            self.far_hand = _lerp_point((58.0, 18.0), (68.0, 73.0), rise)
            self.near_knee = _lerp_point((77.0, 105.0), (76.0, 103.0), rise)
            self.near_ankle = _lerp_point((83.0, 110.0), (82.0, 117.0), rise)
            self.far_knee = _lerp_point((53.0, 104.0), (54.0, 104.0), rise)
            self.far_ankle = _lerp_point((47.0, 109.0), (48.0, 117.0), rise)
            self.near_hand_mode = "chop" if rise > 0.55 else "grip"
            self.far_hand_mode = "closed"

        elif animation == "climb":
            alternate = wave
            self.body_y = -4.0 + 1.2 * cosine
            self.head_tilt = 1.5 * alternate
            self.near_elbow = (81.0, 46.0 + 9.0 * alternate)
            self.near_hand = (80.0, 29.0 + 12.0 * alternate)
            self.far_elbow = (50.0, 47.0 - 9.0 * alternate)
            self.far_hand = (51.0, 31.0 - 12.0 * alternate)
            self.near_knee = (76.0, 99.0 - 5.0 * alternate)
            self.near_ankle = (82.0, 112.0 - 9.0 * alternate)
            self.far_knee = (53.0, 100.0 + 5.0 * alternate)
            self.far_ankle = (47.0, 113.0 + 6.0 * alternate)
            self.near_hand_mode = self.far_hand_mode = "grip"

        elif animation == "swim":
            stroke = wave
            self.body_y = -4.0 + 1.1 * cosine
            self.rotation = -53.0 + 3.0 * wave
            self.rotation_pivot = (64.5, 77.0)
            self.head_tilt = 1.0
            self.near_elbow = (86.0 + 5.0 * stroke, 67.0)
            self.near_hand = (97.0 + 6.0 * stroke, 75.0)
            self.far_elbow = (43.0 - 5.0 * stroke, 68.0)
            self.far_hand = (32.0 - 6.0 * stroke, 76.0)
            self.near_knee = (77.0 - 4.0 * stroke, 100.0)
            self.near_ankle = (82.0 - 6.0 * stroke, 111.0)
            self.far_knee = (52.0 + 4.0 * stroke, 101.0)
            self.far_ankle = (47.0 + 6.0 * stroke, 112.0)
            self.near_hand_mode = self.far_hand_mode = "open"

        elif animation == "float_glide":
            self.body_y = -8.0 + 1.3 * cosine
            self.rotation = -12.0 + 2.0 * wave
            self.rotation_pivot = (64.5, 78.0)
            self.head_tilt = 0.5
            self.near_elbow = (92.0, 61.0 + 2.0 * wave)
            self.near_hand = (108.0, 64.0 + 3.0 * wave)
            self.far_elbow = (38.0, 62.0 - 2.0 * wave)
            self.far_hand = (23.0, 67.0 - 3.0 * wave)
            self.near_knee = (78.0, 101.0)
            self.near_ankle = (86.0, 110.0)
            self.far_knee = (52.0, 101.0)
            self.far_ankle = (44.0, 111.0)
            self.near_hand_mode = self.far_hand_mode = "open"

        elif animation == "block":
            brace = 0.25 + 0.75 * math.sin(math.pi * t)
            self.body_y = 2.5 * brace
            self.scale_y = 1.0 - 0.08 * brace
            self.rotation_pivot = (64.5, 117.0)
            self.head_tilt = -2.0 * brace
            self.near_elbow = (83.0, 65.0)
            self.near_hand = (62.0, 70.0)
            self.far_elbow = (46.0, 66.0)
            self.far_hand = (67.0, 79.0)
            self.near_knee = (75.0, 102.0)
            self.near_ankle = (79.0, 117.0)
            self.far_knee = (55.0, 103.0)
            self.far_ankle = (51.0, 117.0)
            self.near_hand_mode = self.far_hand_mode = "closed"

        elif animation == "hit":
            recoil = math.sin(math.pi * t)
            self.body_x = -5.0 * recoil
            self.body_y = -2.0 * recoil
            self.rotation = -9.0 * recoil
            self.rotation_pivot = (64.5, 86.0)
            self.head_tilt = 12.0 * recoil
            self.mouth_open = 0.75 * recoil
            self.brow_lift = 0.8 * recoil
            self.near_elbow = (73.0, 69.0)
            self.near_hand = (63.0, 79.0)
            self.far_elbow = (42.0, 70.0)
            self.far_hand = (31.0, 81.0)
            self.near_knee = (76.0, 102.0)
            self.near_ankle = (81.0, 117.0)
            self.far_knee = (54.0, 103.0)
            self.far_ankle = (49.0, 117.0)
            self.near_hand_mode = self.far_hand_mode = "open"

        elif animation == "death":
            collapse = _smoothstep(t)
            self.body_x = 4.0 * collapse
            self.body_y = -4.0 * collapse
            self.scale_y = 1.0 - 0.12 * collapse
            self.rotation = 86.0 * collapse
            self.rotation_pivot = (64.5, 88.0)
            self.head_tilt = 6.0 * collapse
            self.mouth_open = 0.15 * collapse
            self.near_elbow = (78.0, 78.0)
            self.near_hand = (70.0, 94.0)
            self.far_elbow = (49.0, 78.0)
            self.far_hand = (55.0, 95.0)
            self.near_knee = (76.0, 103.0)
            self.near_ankle = (79.0, 116.0)
            self.far_knee = (53.0, 103.0)
            self.far_ankle = (50.0, 116.0)
            self.near_hand_mode = self.far_hand_mode = "relaxed"

        elif animation == "talk":
            gesture = 0.5 - 0.5 * math.cos(phase * math.tau)
            counter = 0.5 + 0.5 * math.sin((phase + 0.23) * math.tau)
            self.body_y = -0.35 * gesture
            self.head_x = 0.7 * gesture
            self.head_y = -0.2 * gesture
            self.head_tilt = -1.8 + 2.0 * gesture
            self.mouth_open = 0.22 + 0.68 * max(0.0, math.sin((phase + 0.08) * math.tau))
            self.brow_lift = 0.75 * counter
            self.blink = frame_idx == 6
            self.near_elbow = (85.0 + 4.5 * gesture, 73.0 - 4.5 * gesture)
            self.near_hand = (89.0 + 10.0 * gesture, 83.0 - 15.0 * gesture)
            self.near_hand_mode = "pinch" if frame_idx in {2, 3, 4} else "open"
            self.far_elbow = (45.0 - 2.5 * counter, 74.0 - 3.0 * counter)
            self.far_hand = (43.0 - 5.0 * counter, 86.0 - 11.0 * counter)
            self.far_hand_mode = "open"

        elif animation == "interact":
            reach = math.sin(t * math.pi) ** 1.2
            settle = math.sin(phase * math.tau)
            self.body_x = 1.8 * reach
            self.body_y = -0.5 * reach
            self.head_x = 1.5 * reach
            self.head_y = -0.2 * reach
            self.head_tilt = -2.8 + 1.0 * reach
            self.mouth_open = 0.10 + 0.18 * reach
            self.brow_lift = 0.35 + 0.55 * reach
            self.near_elbow = (88.0 + 6.0 * reach, 72.0 - 2.0 * reach)
            self.near_hand = (91.0 + 18.0 * reach, 78.0 - 9.0 * reach)
            self.near_hand_mode = "point"
            self.far_elbow = (48.0 + 2.0 * reach, 72.0)
            self.far_hand = (58.0 + 2.0 * reach, 68.0 - 2.0 * reach)
            self.far_hand_mode = "closed"
            self.near_knee = (72.0 + 1.2 * reach, 104.0)
            self.near_ankle = (73.0 + 2.2 * reach, 117.0)
            self.far_knee = (58.0 + 0.4 * settle, 104.0)

        elif animation == "jab":
            strike = math.sin(math.pi * t) ** 1.6
            self.body_x = 2.5 * strike
            self.rotation = -3.0 * strike
            self.rotation_pivot = (64.5, 91.0)
            self.head_tilt = -2.0
            self.near_elbow = (88.0 + 7.0 * strike, 70.0)
            self.near_hand = (92.0 + 23.0 * strike, 68.0 - 2.0 * strike)
            self.near_hand_mode = "point"
            self.far_elbow = (53.0, 66.0)
            self.far_hand = (64.0, 68.0)
            self.far_hand_mode = "closed"
            self.near_knee = (75.0 + 2.0 * strike, 103.0)
            self.near_ankle = (79.0 + 5.0 * strike, 117.0)
            self.far_knee = (55.0 - 2.0 * strike, 104.0)
            self.far_ankle = (50.0 - 4.0 * strike, 117.0)

        elif animation == "punch":
            windup = _smoothstep(_clamp01(t / 0.35))
            release = _smoothstep(_clamp01((t - 0.28) / 0.45))
            recover = _smoothstep(_clamp01((t - 0.72) / 0.28))
            strike = release * (1.0 - recover)
            self.body_x = -2.0 * windup + 6.0 * strike
            self.rotation = 5.0 * windup - 11.0 * strike
            self.rotation_pivot = (64.5, 91.0)
            self.head_tilt = -3.0 * strike
            self.near_elbow = (77.0 + 18.0 * strike, 68.0)
            self.near_hand = (67.0 - 8.0 * windup + 45.0 * strike, 72.0)
            self.near_hand_mode = "closed"
            self.far_elbow = (54.0 + 5.0 * strike, 66.0)
            self.far_hand = (64.0 + 8.0 * strike, 71.0)
            self.far_hand_mode = "closed"
            self.near_knee = (77.0 + 4.0 * strike, 103.0)
            self.near_ankle = (83.0 + 7.0 * strike, 117.0)
            self.far_knee = (53.0 - 3.0 * strike, 104.0)
            self.far_ankle = (47.0 - 6.0 * strike, 117.0)

        elif animation in {"slash", "attack_side"}:
            arc = _smoothstep(t)
            swing = math.sin(math.pi * arc)
            wide = animation == "slash"
            self.body_x = (3.0 if wide else 4.5) * swing
            self.rotation = (-5.0 if wide else -8.0) * swing
            self.rotation_pivot = (64.5, 91.0)
            self.head_tilt = -1.5 - 2.0 * swing
            start = (69.0, 55.0) if wide else (72.0, 64.0)
            end = (111.0, 81.0) if wide else (116.0, 68.0)
            self.near_elbow = _lerp_point((75.0, 59.0), (96.0, 68.0), arc)
            self.near_hand = _lerp_point(start, end, arc)
            self.near_hand_mode = "chop" if wide else "point"
            self.far_elbow = (53.0, 68.0)
            self.far_hand = (64.0, 72.0)
            self.far_hand_mode = "closed"
            self.near_knee = (76.0 + 4.0 * swing, 103.0)
            self.near_ankle = (82.0 + 7.0 * swing, 117.0)
            self.far_knee = (54.0 - 3.0 * swing, 104.0)
            self.far_ankle = (48.0 - 5.0 * swing, 117.0)

        elif animation == "attack_up":
            strike = math.sin(math.pi * t)
            self.body_y = 2.0 * (1.0 - strike)
            self.scale_y = 0.92 + 0.08 * strike
            self.rotation_pivot = (64.5, 117.0)
            self.head_tilt = -4.0 * strike
            self.near_elbow = (84.0, 64.0 - 18.0 * strike)
            self.near_hand = (88.0, 76.0 - 52.0 * strike)
            self.near_hand_mode = "chop"
            self.far_elbow = (50.0, 66.0 - 12.0 * strike)
            self.far_hand = (58.0, 75.0 - 38.0 * strike)
            self.far_hand_mode = "open"
            self.near_knee = (77.0, 103.0)
            self.near_ankle = (82.0, 117.0)
            self.far_knee = (53.0, 104.0)
            self.far_ankle = (48.0, 117.0)

        elif animation == "attack_down":
            strike = math.sin(math.pi * t)
            self.body_y = 3.0 * strike
            self.scale_y = 1.0 - 0.12 * strike
            self.rotation_pivot = (64.5, 117.0)
            self.head_tilt = 4.0 * strike
            self.near_elbow = (91.0, 76.0 + 9.0 * strike)
            self.near_hand = (104.0, 88.0 + 21.0 * strike)
            self.near_hand_mode = "chop"
            self.far_elbow = (52.0, 69.0)
            self.far_hand = (63.0, 76.0)
            self.far_hand_mode = "closed"
            self.near_knee = (78.0, 104.0)
            self.near_ankle = (84.0, 117.0)
            self.far_knee = (52.0, 104.0)
            self.far_ankle = (46.0, 117.0)

        elif animation == "air_neutral":
            self.body_y = -7.0
            self.rotation = -360.0 * t
            self.rotation_pivot = (64.5, 78.0)
            self.head_tilt = -1.0
            self.near_elbow = (91.0, 65.0)
            self.near_hand = (105.0, 72.0)
            self.far_elbow = (39.0, 66.0)
            self.far_hand = (25.0, 74.0)
            self.near_knee = (79.0, 100.0)
            self.near_ankle = (88.0, 108.0)
            self.far_knee = (50.0, 100.0)
            self.far_ankle = (41.0, 109.0)
            self.near_hand_mode = self.far_hand_mode = "chop"

        elif animation == "air_forward":
            strike = math.sin(math.pi * t)
            self.body_y = -7.0
            self.rotation = -8.0 * strike
            self.rotation_pivot = (64.5, 78.0)
            self.near_elbow = (93.0, 66.0)
            self.near_hand = (110.0 + 5.0 * strike, 63.0)
            self.near_hand_mode = "point"
            self.far_elbow = (50.0, 69.0)
            self.far_hand = (62.0, 72.0)
            self.far_hand_mode = "closed"
            self.near_knee = (83.0, 98.0)
            self.near_ankle = (103.0 + 5.0 * strike, 101.0)
            self.far_knee = (51.0, 101.0)
            self.far_ankle = (43.0, 111.0)

        elif animation == "air_back":
            strike = math.sin(math.pi * t)
            self.body_y = -7.0
            self.rotation = 8.0 * strike
            self.rotation_pivot = (64.5, 78.0)
            self.near_elbow = (82.0, 70.0)
            self.near_hand = (74.0, 78.0)
            self.near_hand_mode = "closed"
            self.far_elbow = (38.0, 66.0)
            self.far_hand = (19.0 - 4.0 * strike, 63.0)
            self.far_hand_mode = "chop"
            self.near_knee = (76.0, 101.0)
            self.near_ankle = (83.0, 111.0)
            self.far_knee = (46.0, 98.0)
            self.far_ankle = (25.0 - 5.0 * strike, 101.0)

        elif animation == "air_down":
            strike = math.sin(math.pi * t)
            self.body_y = -8.0 + 2.0 * strike
            self.head_tilt = 3.0 * strike
            self.near_elbow = (90.0, 62.0)
            self.near_hand = (101.0, 52.0)
            self.far_elbow = (42.0, 63.0)
            self.far_hand = (31.0, 54.0)
            self.near_knee = (72.0, 101.0)
            self.near_ankle = (73.0, 121.0 + 2.0 * strike)
            self.far_knee = (58.0, 101.0)
            self.far_ankle = (57.0, 114.0)
            self.near_hand_mode = self.far_hand_mode = "open"

        elif animation == "air_up":
            strike = math.sin(math.pi * t)
            self.body_y = -8.0
            self.head_tilt = -4.0 * strike
            self.near_elbow = (83.0, 55.0 - 15.0 * strike)
            self.near_hand = (88.0, 62.0 - 42.0 * strike)
            self.far_elbow = (48.0, 56.0 - 14.0 * strike)
            self.far_hand = (52.0, 63.0 - 40.0 * strike)
            self.near_knee = (77.0, 101.0)
            self.near_ankle = (82.0, 111.0)
            self.far_knee = (52.0, 101.0)
            self.far_ankle = (47.0, 112.0)
            self.near_hand_mode = self.far_hand_mode = "chop"

        elif animation == "charge":
            pulse = 0.5 - 0.5 * cosine
            self.body_y = 2.0 * pulse
            self.scale_y = 1.0 - 0.08 * pulse
            self.rotation_pivot = (64.5, 117.0)
            self.head_tilt = -3.0 - 2.0 * pulse
            self.brow_lift = -0.2
            self.near_elbow = (81.0, 66.0)
            self.near_hand = (66.0, 72.0)
            self.far_elbow = (48.0, 67.0)
            self.far_hand = (63.0, 76.0)
            self.near_hand_mode = self.far_hand_mode = "pinch"
            self.near_knee = (76.0, 103.0)
            self.near_ankle = (81.0, 117.0)
            self.far_knee = (54.0, 104.0)
            self.far_ankle = (49.0, 117.0)

        elif animation == "cast":
            unfold = _smoothstep(t)
            self.body_y = -1.0 * unfold
            self.head_tilt = -2.0 + 3.0 * unfold
            self.mouth_open = 0.1 + 0.25 * unfold
            self.brow_lift = 0.4 + 0.4 * unfold
            self.near_elbow = _lerp_point((81.0, 66.0), (96.0, 54.0), unfold)
            self.near_hand = _lerp_point((66.0, 72.0), (113.0, 46.0), unfold)
            self.far_elbow = _lerp_point((48.0, 67.0), (36.0, 57.0), unfold)
            self.far_hand = _lerp_point((63.0, 76.0), (20.0, 51.0), unfold)
            self.near_hand_mode = self.far_hand_mode = "open"

        elif animation == "celebrate":
            lift = 0.5 - 0.5 * cosine
            self.body_y = -2.0 * lift
            self.head_tilt = 1.5 * wave
            self.mouth_smile = 1.0
            self.brow_lift = 0.7
            self.near_elbow = (87.0, 58.0 - 9.0 * lift)
            self.near_hand = (91.0, 65.0 - 28.0 * lift)
            self.far_elbow = (43.0, 59.0 - 9.0 * lift)
            self.far_hand = (39.0, 66.0 - 28.0 * lift)
            self.near_hand_mode = self.far_hand_mode = "open"
            self.near_knee = (75.0, 103.0 - 2.0 * lift)
            self.near_ankle = (79.0, 117.0 - 4.0 * lift)
            self.far_knee = (55.0, 104.0)
            self.far_ankle = (51.0, 117.0)

        elif animation == "taunt":
            question = 0.5 - 0.5 * cosine
            self.head_tilt = -4.0 + 8.0 * question
            self.brow_lift = 0.5
            self.mouth_smile = -0.35
            self.near_elbow = (87.0, 67.0 - 3.0 * question)
            self.near_hand = (96.0, 55.0 - 7.0 * question)
            self.near_hand_mode = "pinch"
            self.far_elbow = (43.0, 69.0)
            self.far_hand = (31.0, 77.0)
            self.far_hand_mode = "open"

        else:  # pragma: no cover - ROWS is the public animation contract.
            raise KeyError(animation)


def _s(value: float) -> int:
    return int(round(value * SUPER))


def _pt(point: Point) -> Tuple[int, int]:
    return (_s(point[0]), _s(point[1]))


def _box(center: Point, rx: float, ry: float) -> Tuple[int, int, int, int]:
    cx, cy = center
    return (_s(cx - rx), _s(cy - ry), _s(cx + rx), _s(cy + ry))


def _poly(
    draw: ImageDraw.ImageDraw,
    points: Iterable[Point],
    fill: RGBA,
    outline: RGBA | None = OUTLINE,
    width: float = 1.0,
) -> None:
    ipoints = [_pt(point) for point in points]
    draw.polygon(ipoints, fill=fill)
    if outline is not None and width > 0:
        draw.line(ipoints + [ipoints[0]], fill=outline, width=max(1, _s(width)), joint="curve")


def _line(draw: ImageDraw.ImageDraw, points: Sequence[Point], fill: RGBA, width: float) -> None:
    draw.line([_pt(point) for point in points], fill=fill, width=max(1, _s(width)), joint="curve")


def _ellipse(
    draw: ImageDraw.ImageDraw,
    center: Point,
    rx: float,
    ry: float,
    fill: RGBA | None,
    outline: RGBA | None = OUTLINE,
    width: float = 1.0,
) -> None:
    draw.ellipse(
        _box(center, rx, ry),
        fill=fill,
        outline=outline,
        width=max(1, _s(width)) if outline is not None and width > 0 else 1,
    )


def _circle(
    draw: ImageDraw.ImageDraw,
    center: Point,
    radius: float,
    fill: RGBA | None,
    outline: RGBA | None = OUTLINE,
    width: float = 1.0,
) -> None:
    _ellipse(draw, center, radius, radius, fill, outline, width)


def _lerp(a: float, b: float, amount: float) -> float:
    return a + (b - a) * amount


def _lerp_point(a: Point, b: Point, amount: float) -> Point:
    return (_lerp(a[0], b[0], amount), _lerp(a[1], b[1], amount))


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _smoothstep(value: float) -> float:
    value = _clamp01(value)
    return value * value * (3.0 - 2.0 * value)


def _unit_segment(a: Point, b: Point) -> Tuple[Point, Point, float]:
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    length = max(1.0e-6, math.hypot(dx, dy))
    along = (dx / length, dy / length)
    normal = (-along[1], along[0])
    return along, normal, length


def _bent_tube(
    draw: ImageDraw.ImageDraw,
    start: Point,
    bend: Point,
    end: Point,
    radii: Tuple[float, float, float],
    *,
    fill: RGBA,
    outline: RGBA = OUTLINE,
    width: float = 1.15,
) -> None:
    """Draw one connected six-sided bent limb, not separate capsules."""
    _, n1, _ = _unit_segment(start, bend)
    _, n2, _ = _unit_segment(bend, end)
    avg = (n1[0] + n2[0], n1[1] + n2[1])
    avg_len = max(1.0e-6, math.hypot(*avg))
    nm = (avg[0] / avg_len, avg[1] / avg_len)
    r0, r1, r2 = radii
    points = [
        (start[0] + n1[0] * r0, start[1] + n1[1] * r0),
        (bend[0] + nm[0] * r1, bend[1] + nm[1] * r1),
        (end[0] + n2[0] * r2, end[1] + n2[1] * r2),
        (end[0] - n2[0] * r2, end[1] - n2[1] * r2),
        (bend[0] - nm[0] * r1, bend[1] - nm[1] * r1),
        (start[0] - n1[0] * r0, start[1] - n1[1] * r0),
    ]
    _poly(draw, points, fill, outline, width)
    _ellipse(draw, start, r0, r0, fill, outline, width)
    _ellipse(draw, end, r2, r2, fill, outline, width)


def _lens_tint(image: Image.Image, center: Point, rx: float, ry: float) -> None:
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = blending_draw(overlay)
    _ellipse(draw, center, rx, ry, GLASS_TINT, outline=None, width=0)
    image.alpha_composite(overlay)


def _rotate(point: Point, origin: Point, degrees: float) -> Point:
    radians = math.radians(degrees)
    c = math.cos(radians)
    s = math.sin(radians)
    x = point[0] - origin[0]
    y = point[1] - origin[1]
    return (origin[0] + x * c - y * s, origin[1] + x * s + y * c)


def _downsample(image: Image.Image) -> Image.Image:
    return image.resize(FRAME_SIZE, Image.Resampling.LANCZOS)


def _ensure_canvas_inset(image: Image.Image, margin: int = 2) -> Image.Image:
    """Keep expressive poses fully visible without changing their authored shape.

    Most frames only need a one- or two-pixel translation after Lanczos
    downsampling.  Extremely wide rotations may receive a small uniform scale
    reduction, capped by the available inset.  The operation is applied to the
    complete composited character, so body connectivity and painter order are
    preserved.
    """
    bbox = image.getbbox()
    if bbox is None:
        return image
    left, top, right, bottom = bbox
    available_w = image.width - 2 * margin
    available_h = image.height - 2 * margin
    width = right - left
    height = bottom - top
    scale = min(1.0, available_w / max(1, width), available_h / max(1, height))
    crop = image.crop(bbox)
    if scale < 0.999:
        crop = crop.resize(
            (max(1, round(crop.width * scale)), max(1, round(crop.height * scale))),
            Image.Resampling.LANCZOS,
        )
    new_w, new_h = crop.size
    target_x = min(max(left, margin), image.width - margin - new_w)
    target_y = min(max(top, margin), image.height - margin - new_h)
    canvas = Image.new("RGBA", image.size, (0, 0, 0, 0))
    canvas.alpha_composite(crop, (int(target_x), int(target_y)))
    return canvas


class RamenNujanRenderer:
    """Draw a distinctive, connected, empty-handed Ramen-nujan.

    His silhouette is intentionally unlike Girdle's compact three-piece-suit
    outline.  Ramen-nujan has a broad low hair mass, a short wedge-shaped face,
    a visibly fuller scholar belly and cheek line, a long asymmetrical scholar
    coat, an attached cross-body academic stole, slim sleeves, and short widely
    planted legs.  The stole is clothing, not a
    held prop; its stitched noodle lines and vegetable-color details are the
    restrained FSM reference.
    """

    USES_PROPS = False
    USES_DROP_SHADOW = False

    @staticmethod
    def _remap_joint(point: Point, *, scale_x: float, dy: float) -> Point:
        return (64.5 + (point[0] - 64.5) * scale_x, point[1] + dy)

    def _reproportion_pose(self, pose: Pose, animation: str, frame_idx: int, nframes: int) -> None:
        """Move the inherited action vocabulary onto Ramen-nujan's own body plan."""
        pose.near_shoulder = self._remap_joint(pose.near_shoulder, scale_x=0.90, dy=4.4)
        pose.far_shoulder = self._remap_joint(pose.far_shoulder, scale_x=0.90, dy=4.4)
        pose.near_elbow = self._remap_joint(pose.near_elbow, scale_x=1.01, dy=3.3)
        pose.far_elbow = self._remap_joint(pose.far_elbow, scale_x=1.01, dy=3.3)
        pose.near_hand = self._remap_joint(pose.near_hand, scale_x=1.05, dy=2.0)
        pose.far_hand = self._remap_joint(pose.far_hand, scale_x=1.05, dy=2.0)
        pose.near_hip = self._remap_joint(pose.near_hip, scale_x=0.80, dy=6.3)
        pose.far_hip = self._remap_joint(pose.far_hip, scale_x=0.80, dy=6.3)
        pose.near_knee = self._remap_joint(pose.near_knee, scale_x=0.96, dy=4.1)
        pose.far_knee = self._remap_joint(pose.far_knee, scale_x=0.96, dy=4.1)
        pose.near_ankle = self._remap_joint(pose.near_ankle, scale_x=0.96, dy=1.2)
        pose.far_ankle = self._remap_joint(pose.far_ankle, scale_x=0.96, dy=1.2)

        # A thoughtful forward set and asymmetric hands make even the neutral
        # outline unlike Girdle's square, arms-at-the-sides stance.
        if animation == "idle":
            phase = frame_idx / max(1, nframes)
            drift = math.sin(phase * math.tau)
            pose.body_x -= 0.7
            pose.head_x -= 1.1
            pose.head_tilt += 1.1
            pose.far_elbow = (50.8 - 0.5 * drift, 82.5)
            pose.far_hand = (57.6 - 0.4 * drift, 92.6)
            pose.far_hand_mode = "relaxed"
            pose.near_elbow = (80.6 + 0.5 * drift, 81.0)
            pose.near_hand = (79.6 + 0.4 * drift, 95.2)
            pose.near_hand_mode = "open"
        elif animation == "talk":
            # Flowing two-sided explanation rather than Girdle's single precise jab.
            phase = frame_idx / max(1, nframes)
            sweep = math.sin(phase * math.tau)
            pose.body_x -= 0.5
            pose.far_hand = (pose.far_hand[0] - 2.5, pose.far_hand[1] + 1.0)
            pose.near_hand = (pose.near_hand[0] + 1.5, pose.near_hand[1] - 1.0)
            pose.head_tilt += 1.8 * sweep
        elif animation == "charge":
            # He draws power inward as though it arrived through a theorem-dream.
            pose.near_hand_mode = "open"
            pose.far_hand_mode = "open"
            pose.head_tilt += 0.6
            pose.blink = True
            pose.mouth_smile = 0.32
            pose.body_y += 0.6
            pose.near_hand = (73.5, 86.8)
            pose.far_hand = (55.5, 85.5)
        elif animation == "cast":
            # Release the dream insight outward into visible mathematics.
            pose.near_hand_mode = "open"
            pose.far_hand_mode = "open"
            pose.head_tilt += 2.0
            pose.brow_lift += 0.2
            pose.near_hand = (88.5, 76.5)
            pose.far_hand = (50.8, 79.0)

    def render_frame(self, animation: str, frame_idx: int, nframes: int) -> Image.Image:
        image = Image.new("RGBA", (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER), (0, 0, 0, 0))
        draw = blending_draw(image)
        pose = Pose(animation, frame_idx, nframes)
        self._reproportion_pose(pose, animation, frame_idx, nframes)

        def P(point: Point) -> Point:
            px, py = point
            pivot_x, pivot_y = pose.rotation_pivot
            px = pivot_x + (px - pivot_x) * pose.scale_x
            py = pivot_y + (py - pivot_y) * pose.scale_y
            if abs(pose.rotation) > 1.0e-7:
                px, py = _rotate((px, py), pose.rotation_pivot, pose.rotation)
            return (px + pose.body_x, py + pose.body_y)

        self._draw_far_leg(draw, P, pose)
        self._draw_near_leg(draw, P, pose)
        self._draw_torso(draw, P)
        self._draw_far_arm(draw, P, pose)
        self._draw_near_arm(draw, P, pose)
        self._draw_ability_effects(draw, P, pose, animation, frame_idx, nframes)
        pose.head_tilt += pose.rotation
        self._draw_head(
            image,
            draw,
            P((63.2 + pose.head_x, 36.5 + pose.head_y)),
            pose,
        )
        return _ensure_canvas_inset(_downsample(image))

    def _draw_far_leg(self, draw: ImageDraw.ImageDraw, P, pose: Pose) -> None:
        self._draw_leg(draw, P(pose.far_hip), P(pose.far_knee), P(pose.far_ankle), near=False)

    def _draw_near_leg(self, draw: ImageDraw.ImageDraw, P, pose: Pose) -> None:
        self._draw_leg(draw, P(pose.near_hip), P(pose.near_knee), P(pose.near_ankle), near=True)

    def _draw_leg(self, draw: ImageDraw.ImageDraw, hip: Point, knee: Point, ankle: Point, *, near: bool) -> None:
        cloth = TROUSER_LIGHT if near else TROUSER
        shade = TROUSER if near else SUIT_DARK
        _bent_tube(draw, hip, knee, ankle, (4.65, 3.95, 2.95), fill=cloth, width=1.10)
        _line(draw, [(knee[0] - 1.4, knee[1]), (knee[0] + 1.2, knee[1] + 0.5)], shade, 0.55)
        _ellipse(draw, (ankle[0], ankle[1] - 0.5), 2.85, 2.55, shade, OUTLINE, 0.80)
        along, normal, _ = _unit_segment(knee, ankle)
        foot_dir = (-normal[0], -normal[1])
        shoe_center = (
            ankle[0] + along[0] * 1.5 + foot_dir[0] * (1.15 if near else 0.7),
            ankle[1] + along[1] * 1.5 + foot_dir[1] * (1.15 if near else 0.7),
        )
        half_len = 5.4
        half_w = 2.65
        shoe_points = [
            (shoe_center[0] - foot_dir[0] * half_len + along[0] * half_w, shoe_center[1] - foot_dir[1] * half_len + along[1] * half_w),
            (shoe_center[0] + foot_dir[0] * half_len + along[0] * half_w, shoe_center[1] + foot_dir[1] * half_len + along[1] * half_w),
            (shoe_center[0] + foot_dir[0] * (half_len + 1.0), shoe_center[1] + foot_dir[1] * (half_len + 1.0)),
            (shoe_center[0] + foot_dir[0] * half_len - along[0] * half_w, shoe_center[1] + foot_dir[1] * half_len - along[1] * half_w),
            (shoe_center[0] - foot_dir[0] * half_len - along[0] * half_w, shoe_center[1] - foot_dir[1] * half_len - along[1] * half_w),
        ]
        _poly(draw, shoe_points, SHOE_LIGHT if near else SHOE, OUTLINE, 0.95)
        _line(
            draw,
            [
                (shoe_center[0] - foot_dir[0] * 2.8 - along[0] * 0.6, shoe_center[1] - foot_dir[1] * 2.8 - along[1] * 0.6),
                (shoe_center[0] + foot_dir[0] * 2.5 - along[0] * 0.6, shoe_center[1] + foot_dir[1] * 2.5 - along[1] * 0.6),
            ],
            SHOE_LIGHT,
            0.45,
        )

    def _draw_torso(self, draw: ImageDraw.ImageDraw, P) -> None:
        # Long, asymmetrical scholar coat: narrow at the shoulders, fuller at
        # the belly, and flared / offset at the hem.  This remains the primary
        # silhouette break from Girdle.
        draw.rounded_rectangle(
            _box(P((64.0, 98.7)), 11.2, 5.2),
            radius=max(1, _s(2.2)),
            fill=TROUSER,
            outline=OUTLINE,
            width=max(1, _s(1.05)),
        )
        coat = [
            P((48.8, 57.7)),
            P((54.2, 51.8)),
            P((64.0, 50.4)),
            P((75.2, 52.6)),
            P((81.6, 59.0)),
            P((84.1, 78.8)),
            P((83.0, 88.8)),
            P((80.2, 97.0)),
            P((73.4, 102.4)),
            P((61.8, 103.6)),
            P((48.4, 106.0)),
            P((40.2, 101.8)),
            P((42.2, 84.0)),
            P((44.4, 67.0)),
        ]
        _poly(draw, coat, SUIT, OUTLINE, 1.35)
        # Lit right plane and dark rear flare keep the long coat dimensional.
        _poly(
            draw,
            [P((65.0, 52.2)), P((74.6, 54.6)), P((80.4, 61.6)), P((81.8, 79.8)), P((80.2, 89.8)), P((76.6, 99.6)), P((67.2, 102.0))],
            SUIT_MID,
            outline=None,
            width=0,
        )
        _poly(
            draw,
            [P((49.0, 58.8)), P((54.4, 54.0)), P((56.2, 74.0)), P((55.6, 93.8)), P((48.0, 104.0)), P((42.0, 100.2)), P((44.4, 69.0))],
            SUIT_DARK,
            outline=None,
            width=0,
        )
        belly = [
            P((56.4, 66.8)),
            P((63.6, 63.8)),
            P((72.2, 66.2)),
            P((75.4, 74.6)),
            P((73.0, 84.8)),
            P((66.2, 89.4)),
            P((58.4, 88.0)),
            P((54.0, 79.0)),
        ]
        _poly(draw, belly, SUIT_LIGHT, outline=None, width=0)

        # High collar and wrap-front remove the familiar tie-and-lapel outline.
        _poly(draw, [P((57.0, 52.8)), P((64.0, 59.0)), P((59.5, 67.2)), P((52.5, 56.8))], SHIRT, OUTLINE, 0.75)
        _poly(draw, [P((71.8, 53.3)), P((64.0, 59.0)), P((67.8, 67.2)), P((77.8, 58.5))], SHIRT_SHADE, OUTLINE, 0.75)
        _poly(draw, [P((59.0, 54.8)), P((64.0, 59.2)), P((69.0, 55.0)), P((69.5, 66.5)), P((58.5, 66.5))], SHIRT, OUTLINE_SOFT, 0.65)
        _line(draw, [P((64.0, 59.0)), P((64.0, 67.0))], NOODLE_GOLD, 0.65)
        _circle(draw, P((64.0, 64.0)), 0.85, CARROT, OUTLINE_SOFT, 0.20)
        _line(draw, [P((59.8, 73.5)), P((64.2, 76.0)), P((68.6, 73.8))], SUIT_DARK, 0.55)

        # Attached academic stole crosses the body, then becomes a broad
        # asymmetrical front panel.  Parallel stitched lines evoke noodles but
        # remain intrinsic garment decoration.
        stole = [
            P((71.2, 54.2)),
            P((78.8, 58.6)),
            P((67.5, 74.0)),
            P((60.5, 85.0)),
            P((55.5, 103.0)),
            P((44.0, 104.0)),
            P((49.0, 87.5)),
            P((58.5, 72.8)),
        ]
        _poly(draw, stole, VEST, OUTLINE, 0.95)
        _line(draw, [P((72.0, 56.0)), P((62.0, 72.0)), P((54.0, 86.0)), P((50.0, 100.0))], NOODLE_GOLD, 0.75)
        _line(draw, [P((75.0, 58.5)), P((65.0, 74.0)), P((57.0, 88.0)), P((54.0, 99.0))], SESAME, 0.45)
        # Vegetarian stitch cluster: mushroom cap, scallion leaves, carrot dot.
        _ellipse(draw, P((56.5, 83.0)), 2.0, 1.15, SHIRT_SHADE, OUTLINE_SOFT, 0.35)
        _line(draw, [P((56.5, 83.8)), P((56.5, 86.2))], SHIRT_SHADE, 0.65)
        _poly(draw, [P((51.5, 91.0)), P((55.0, 88.5)), P((54.0, 93.0))], SCALLION, OUTLINE_SOFT, 0.30)
        _poly(draw, [P((52.2, 91.5)), P((49.0, 89.0)), P((49.5, 93.5))], SCALLION, OUTLINE_SOFT, 0.30)
        _circle(draw, P((52.5, 96.5)), 0.85, CARROT, OUTLINE_SOFT, 0.20)

        # Curved partition-series seam on the unobstructed coat front.
        _line(
            draw,
            [P((66.0, 72.0)), P((69.0, 69.5)), P((71.5, 74.0)), P((73.5, 68.0)), P((76.0, 71.0))],
            NOODLE_GOLD,
            0.55,
        )
        for y, color in ((79.0, SESAME), (86.0, CARROT), (93.0, SCALLION)):
            _circle(draw, P((69.0, y)), 0.85, color, OUTLINE_SOFT, 0.18)

        # Neck is absorbed by the final head layer.
        draw.rounded_rectangle(
            _box(P((63.5, 52.2)), 5.3, 6.5),
            radius=max(1, _s(2.0)),
            fill=SKIN_SHADE,
            outline=OUTLINE,
            width=max(1, _s(0.85)),
        )

    def _draw_far_arm(self, draw: ImageDraw.ImageDraw, P, pose: Pose) -> None:
        self._draw_arm(draw, P(pose.far_shoulder), P(pose.far_elbow), P(pose.far_hand), pose.far_hand_mode, near=False)

    def _draw_near_arm(self, draw: ImageDraw.ImageDraw, P, pose: Pose) -> None:
        self._draw_arm(draw, P(pose.near_shoulder), P(pose.near_elbow), P(pose.near_hand), pose.near_hand_mode, near=True)

    def _draw_arm(
        self,
        draw: ImageDraw.ImageDraw,
        shoulder: Point,
        elbow: Point,
        hand: Point,
        hand_mode: str,
        *,
        near: bool,
    ) -> None:
        sleeve = SUIT_LIGHT if near else SUIT_DARK
        seam = NOODLE_GOLD if near else OUTLINE_SOFT
        along, normal, length = _unit_segment(elbow, hand)
        wrist = (hand[0] - along[0] * min(3.0, length * 0.30), hand[1] - along[1] * min(3.0, length * 0.30))
        _bent_tube(draw, shoulder, elbow, wrist, (5.35, 4.2, 3.05), fill=sleeve, width=1.10)
        seam_start = (shoulder[0] - normal[0] * 1.25, shoulder[1] - normal[1] * 1.25)
        seam_end = (wrist[0] - normal[0] * 0.7, wrist[1] - normal[1] * 0.7)
        _line(draw, [seam_start, elbow, seam_end], seam, 0.55)
        _ellipse(draw, shoulder, 4.9, 4.5, sleeve, OUTLINE, 0.95)
        _ellipse(draw, wrist, 3.1, 2.7, SHIRT if near else SHIRT_SHADE, OUTLINE, 0.78)
        self._draw_hand(draw, wrist, hand, hand_mode, near=near)

    def _draw_hand(self, draw: ImageDraw.ImageDraw, wrist: Point, center: Point, mode: str, *, near: bool) -> None:
        skin = SKIN_LIGHT if near else SKIN
        along, normal, _ = _unit_segment(wrist, center)
        palm_rx = 3.65 if mode in {"open", "point"} else 3.15
        _ellipse(draw, center, palm_rx, 2.95, skin, OUTLINE, 0.85)

        def finger(start: Point, end: Point, width: float = 1.0) -> None:
            _line(draw, [start, end], OUTLINE, width + 0.70)
            _line(draw, [start, end], skin, width)

        if mode == "open":
            base = (center[0] + along[0] * 1.0, center[1] + along[1] * 1.0)
            for offset in (-1.35, -0.4, 0.5, 1.35):
                start = (base[0] + normal[0] * offset, base[1] + normal[1] * offset)
                length = 3.1 - abs(offset) * 0.25
                end = (start[0] + along[0] * length, start[1] + along[1] * length)
                finger(start, end, 0.82)
        elif mode == "pinch":
            for sign in (-1.0, 1.0):
                start = (center[0] + along[0] * 0.9 + normal[0] * sign * 0.65, center[1] + along[1] * 0.9 + normal[1] * sign * 0.65)
                end = (center[0] + along[0] * 3.5 + normal[0] * sign * 0.12, center[1] + along[1] * 3.5 + normal[1] * sign * 0.12)
                finger(start, end, 0.88)
        elif mode == "point":
            start = (center[0] + along[0] * 1.1, center[1] + along[1] * 1.1)
            end = (center[0] + along[0] * 6.0, center[1] + along[1] * 6.0)
            finger(start, end, 1.0)
        elif mode in {"closed", "grip"}:
            _line(draw, [(center[0] - 1.5, center[1] - 0.5), (center[0] + 1.7, center[1] + 0.9)], SKIN_DEEP, 0.42)
            if mode == "grip":
                _line(draw, [(center[0] - normal[0] * 1.7, center[1] - normal[1] * 1.7), (center[0] + normal[0] * 1.7, center[1] + normal[1] * 1.7)], SKIN_DEEP, 0.38)
        elif mode == "chop":
            start = (center[0] + along[0] * 0.8, center[1] + along[1] * 0.8)
            end = (center[0] + along[0] * 5.0, center[1] + along[1] * 5.0)
            _line(draw, [start, end], OUTLINE, 2.3)
            _line(draw, [start, end], skin, 1.45)
        else:
            thumb_start = (center[0] + normal[0] * 1.1, center[1] + normal[1] * 1.1)
            thumb_end = (thumb_start[0] + along[0] * 2.0, thumb_start[1] + along[1] * 2.0)
            finger(thumb_start, thumb_end, 0.78)

    def _draw_ability_effects(self, draw: ImageDraw.ImageDraw, P, pose: Pose, animation: str, frame_idx: int, nframes: int) -> None:
        if animation == "charge":
            self._draw_dream_invocation(draw, P, pose, frame_idx, nframes)
        elif animation == "cast":
            self._draw_dream_cast(draw, P, pose, frame_idx, nframes)
        elif animation in {"jab", "slash"}:
            self._draw_sigma_effect(draw, P, pose, wide=(animation == "slash"))
        elif animation in {"attack_side", "punch", "attack_up"}:
            self._draw_factorial_effect(draw, P, pose, upward=(animation == "attack_up"))
        elif animation in {"attack_down", "air_down"}:
            self._draw_negative_twelfth_effect(draw, P, pose, aerial=(animation == "air_down"))

    def _draw_dream_invocation(self, draw: ImageDraw.ImageDraw, P, pose: Pose, frame_idx: int, nframes: int) -> None:
        phase = frame_idx / max(1, nframes)
        sway = math.sin(phase * math.tau)
        drowse = 0.5 - 0.5 * math.cos(phase * math.tau)
        tether = [
            P((61.5, 61.0)),
            P((59.0, 53.0 - 0.8 * drowse)),
            P((58.0, 43.5 - 1.2 * drowse)),
            P((60.8, 33.8 - 0.8 * drowse)),
        ]
        _line(draw, tether, OUTLINE, 2.2)
        _line(draw, tether, DREAM_AURA, 1.15)
        path = [
            P((69.0, 27.5)),
            P((72.0 + 1.0 * sway, 20.5)),
            P((71.0 + 1.2 * sway, 12.0)),
            P((64.0, 7.5)),
            P((56.0 - 1.0 * sway, 10.5)),
            P((54.0 - 0.8 * sway, 18.0)),
            P((59.5, 22.0)),
            P((67.0 + 0.6 * sway, 19.0)),
        ]
        _line(draw, path, OUTLINE, 2.8)
        _line(draw, path, DREAM_AURA, 1.65)
        inner = [P((63.5, 24.0)), P((62.0, 17.0)), P((66.0, 13.6)), P((70.0, 16.6))]
        _line(draw, inner, OUTLINE_SOFT, 1.6)
        _line(draw, inner, DREAM_GOLD, 0.9)
        _circle(draw, P((56.0 - 1.0 * sway, 10.7)), 2.35, DREAM_GOLD, OUTLINE_SOFT, 0.30)
        _circle(draw, P((64.0, 7.5)), 1.8, SESAME, OUTLINE_SOFT, 0.22)
        _line(draw, [P((56.0 - 1.0 * sway, 10.7)), P((52.5 - 0.8 * sway, 8.2)), P((50.2 - 0.4 * sway, 11.2))], DREAM_ORANGE, 0.72)
        self._draw_sigma_glyph(
            draw,
            [P((55.5, 26.0)), P((59.0, 22.4)), P((65.0, 22.4)), P((61.5, 26.2)), P((65.0, 29.6)), P((58.8, 29.6))],
            DREAM_GOLD,
        )
        _line(draw, [P((72.5, 26.0)), P((72.5, 18.6))], OUTLINE, 1.8)
        _line(draw, [P((72.5, 26.0)), P((72.5, 18.6))], DREAM_ORANGE, 0.95)
        _circle(draw, P((72.5, 16.4)), 1.15, DREAM_GOLD, OUTLINE_SOFT, 0.20)

    def _draw_dream_cast(self, draw: ImageDraw.ImageDraw, P, pose: Pose, frame_idx: int, nframes: int) -> None:
        phase = frame_idx / max(1, nframes)
        pulse = 0.5 - 0.5 * math.cos(phase * math.tau)
        ribbon = [P((56.0, 72.5)), P((62.0, 63.0 - 1.5 * pulse)), P((71.0, 58.8)), P((82.0, 57.2 - 1.0 * pulse)), P((94.0, 53.5))]
        _line(draw, ribbon, OUTLINE, 2.6)
        _line(draw, ribbon, DREAM_AURA, 1.5)
        self._draw_sigma_glyph(draw, [P((94.0, 53.5)), P((100.0, 48.5)), P((112.0, 48.5)), P((104.0, 55.2)), P((112.0, 63.0)), P((99.0, 63.0))], DREAM_GOLD)
        stem = [P((57.0, 72.0)), P((49.5, 65.0)), P((45.0, 55.0))]
        _line(draw, stem, OUTLINE, 2.1)
        _line(draw, stem, DREAM_ORANGE, 1.2)
        _line(draw, [P((45.0, 55.0)), P((44.8, 45.2))], OUTLINE, 2.2)
        _line(draw, [P((45.0, 55.0)), P((44.8, 45.2))], DREAM_ORANGE, 1.25)
        _circle(draw, P((44.8, 41.8)), 1.55, DREAM_GOLD, OUTLINE_SOFT, 0.28)
        twelfth = [P((72.2, 60.0)), P((77.2, 55.2)), P((84.5, 55.2)), P((80.0, 60.2)), P((84.6, 66.3)), P((90.4, 66.3))]
        _line(draw, twelfth, DREAM_GOLD, 0.9)
        self._draw_sigma_glyph(
            draw,
            [P((70.5, 66.8)), P((76.8, 71.2)), P((84.6, 71.2)), P((80.5, 76.5)), P((86.2, 82.2)), P((78.5, 82.2))],
            DREAM_AURA,
        )

    def _draw_sigma_glyph(self, draw: ImageDraw.ImageDraw, points: Sequence[Point], color: RGBA) -> None:
        _line(draw, points, OUTLINE, 2.6)
        _line(draw, points, color, 1.55)
        _line(draw, [points[1], points[4]], SIGMA_WHITE, 0.5)

    def _draw_sigma_effect(self, draw: ImageDraw.ImageDraw, P, pose: Pose, *, wide: bool) -> None:
        ax, ay = pose.near_hand
        if wide:
            pts = [
                P((ax, ay)),
                P((ax + 5.0, ay - 5.5)),
                P((ax + 16.0, ay - 5.5)),
                P((ax + 9.0, ay + 0.5)),
                P((ax + 16.0, ay + 7.0)),
                P((ax + 5.0, ay + 7.0)),
            ]
        else:
            pts = [
                P((ax, ay)),
                P((ax + 3.5, ay - 3.8)),
                P((ax + 11.5, ay - 3.8)),
                P((ax + 6.8, ay + 0.3)),
                P((ax + 11.5, ay + 5.0)),
                P((ax + 4.5, ay + 5.0)),
            ]
        self._draw_sigma_glyph(draw, pts, DREAM_GOLD if wide else DREAM_AURA)

    def _draw_factorial_effect(self, draw: ImageDraw.ImageDraw, P, pose: Pose, *, upward: bool) -> None:
        ax, ay = pose.near_hand
        if upward:
            path = [P((ax, ay)), P((ax + 1.5, ay - 6.0)), P((ax + 1.5, ay - 16.5))]
            _line(draw, path, OUTLINE, 2.4)
            _line(draw, path, DREAM_ORANGE, 1.35)
            _circle(draw, P((ax + 1.5, ay - 19.2)), 1.75, DREAM_GOLD, OUTLINE_SOFT, 0.28)
            _line(draw, [P((ax - 1.5, ay - 8.0)), P((ax + 4.5, ay - 10.5))], SESAME, 0.6)
        else:
            path = [P((ax, ay)), P((ax + 7.0, ay - 1.0)), P((ax + 12.5, ay - 5.0)), P((ax + 12.5, ay - 16.0))]
            _line(draw, path, OUTLINE, 2.4)
            _line(draw, path, DREAM_ORANGE, 1.35)
            _circle(draw, P((ax + 12.5, ay - 18.8)), 1.75, DREAM_GOLD, OUTLINE_SOFT, 0.28)

    def _draw_negative_twelfth_effect(self, draw: ImageDraw.ImageDraw, P, pose: Pose, *, aerial: bool) -> None:
        ax, ay = pose.near_hand
        if aerial:
            ay += 1.0
        minus = [P((ax, ay)), P((ax + 5.0, ay - 1.5)), P((ax + 11.0, ay - 1.5))]
        _line(draw, minus, OUTLINE, 2.2)
        _line(draw, minus, DREAM_GOLD, 1.25)
        top_one = [P((ax + 9.0, ay - 8.5)), P((ax + 9.0, ay - 1.5))]
        slash = [P((ax + 11.0, ay - 1.5)), P((ax + 6.0, ay + 8.0))]
        lower_one = [P((ax + 8.2, ay + 2.5)), P((ax + 8.2, ay + 9.5))]
        lower_two = [P((ax + 9.2, ay + 3.5)), P((ax + 14.2, ay + 3.5)), P((ax + 14.2, ay + 6.0)), P((ax + 9.5, ay + 9.2)), P((ax + 15.2, ay + 9.2))]
        for pts, color, width in ((top_one, DREAM_AURA, 1.1), (slash, DREAM_ORANGE, 1.2), (lower_one, DREAM_AURA, 1.0), (lower_two, DREAM_ORANGE, 1.0)):
            _line(draw, pts, OUTLINE, width + 1.0)
            _line(draw, pts, color, width)

    def _draw_head(self, image: Image.Image, draw: ImageDraw.ImageDraw, center: Point, pose: Pose) -> None:
        cx, cy = center

        def R(point: Point) -> Point:
            return _rotate(point, center, pose.head_tilt)

        # Broad temples, fuller cheeks, and a low side-swept hair wave. The
        # head is wider and slightly heavier than either the old Ramen-nujan
        # or Girdle.
        far_ear = R((cx - 16.4, cy + 1.9))
        near_ear = R((cx + 17.0, cy + 1.7))
        _ellipse(draw, far_ear, 4.2, 6.2, SKIN_SHADE, OUTLINE, 0.82)
        _ellipse(draw, near_ear, 4.6, 6.4, SKIN, OUTLINE, 0.86)
        _line(draw, [R((cx - 15.8, cy)), R((cx - 13.8, cy + 2.5)), R((cx - 15.0, cy + 4.8))], SKIN_DEEP, 0.42)
        _line(draw, [R((cx + 16.4, cy)), R((cx + 14.3, cy + 2.5)), R((cx + 15.7, cy + 4.8))], SKIN_DEEP, 0.42)

        face = [
            R((cx - 14.8, cy - 15.8)),
            R((cx - 5.8, cy - 20.8)),
            R((cx + 8.0, cy - 19.8)),
            R((cx + 15.8, cy - 13.0)),
            R((cx + 18.6, cy - 2.0)),
            R((cx + 17.6, cy + 9.2)),
            R((cx + 11.6, cy + 17.0)),
            R((cx + 2.0, cy + 21.0)),
            R((cx - 7.8, cy + 19.4)),
            R((cx - 14.3, cy + 12.4)),
            R((cx - 17.8, cy + 2.8)),
            R((cx - 16.8, cy - 7.0)),
        ]
        _poly(draw, face, SKIN, OUTLINE, 1.12)
        _poly(
            draw,
            [R((cx - 11.6, cy - 13.8)), R((cx - 3.6, cy - 18.4)), R((cx + 3.4, cy - 15.6)), R((cx + 1.2, cy - 5.5)), R((cx - 9.4, cy - 5.0))],
            SKIN_LIGHT,
            outline=None,
            width=0,
        )
        _poly(
            draw,
            [R((cx + 8.8, cy + 2.0)), R((cx + 15.6, cy + 4.8)), R((cx + 10.2, cy + 14.6)), R((cx + 2.8, cy + 17.8)), R((cx + 2.0, cy + 9.2))],
            SKIN_SHADE,
            outline=None,
            width=0,
        )

        hair = [
            R((cx - 15.4, cy - 5.0)),
            R((cx - 17.6, cy - 13.4)),
            R((cx - 13.6, cy - 21.4)),
            R((cx - 5.0, cy - 26.4)),
            R((cx + 4.2, cy - 27.2)),
            R((cx + 13.6, cy - 23.4)),
            R((cx + 18.6, cy - 16.2)),
            R((cx + 17.6, cy - 7.0)),
            R((cx + 11.8, cy - 12.8)),
            R((cx + 6.5, cy - 16.0)),
            R((cx + 1.0, cy - 16.8)),
            R((cx - 4.5, cy - 14.0)),
            R((cx - 10.5, cy - 10.5)),
        ]
        _poly(draw, hair, HAIR, OUTLINE, 1.0)
        # Strong off-center part and broad combed wave, not Girdle's pointed crest.
        _line(draw, [R((cx + 4.0, cy - 25.5)), R((cx + 2.0, cy - 18.0)), R((cx - 1.5, cy - 14.5))], SKIN_DEEP, 0.62)
        _line(draw, [R((cx + 5.0, cy - 25.0)), R((cx + 11.0, cy - 22.5)), R((cx + 15.0, cy - 17.0))], HAIR_GLEAM, 0.72)
        _line(draw, [R((cx + 1.0, cy - 25.5)), R((cx - 6.5, cy - 23.5)), R((cx - 12.5, cy - 18.0))], HAIR_GLEAM, 0.72)
        _poly(
            draw,
            [R((cx - 7.0, cy - 17.0)), R((cx + 2.0, cy - 19.0)), R((cx + 6.5, cy - 14.0)), R((cx - 1.5, cy - 11.5))],
            HAIR_MID,
            outline=None,
            width=0,
        )
        _line(draw, [R((cx - 14.5, cy - 13.0)), R((cx - 13.5, cy - 4.0))], HAIR_MID, 0.60)
        _line(draw, [R((cx + 16.0, cy - 14.0)), R((cx + 15.0, cy - 5.0))], HAIR_MID, 0.60)

        far_eye = R((cx - 5.0, cy - 2.5))
        near_eye = R((cx + 5.8, cy - 2.2))
        for is_near, eye in ((False, far_eye), (True, near_eye)):
            if pose.blink:
                _line(draw, [(eye[0] - 2.4, eye[1]), (eye[0] + 2.4, eye[1])], EYE, 0.72)
            else:
                _ellipse(draw, eye, 2.55 if is_near else 2.35, 1.85, EYE_WHITE, OUTLINE, 0.42)
                _circle(draw, (eye[0] + 0.15, eye[1] + 0.10), 1.02 if is_near else 0.92, EYE, EYE, 0.12)
                _circle(draw, (eye[0] + 0.48, eye[1] - 0.35), 0.23, SKIN_LIGHT, None, 0)
        brow_raise = pose.brow_lift
        _line(draw, [R((cx - 9.2, cy - 8.2 - brow_raise * 0.7)), R((cx - 1.0, cy - 8.8 - brow_raise * 0.7))], HAIR, 1.05)
        _line(draw, [R((cx + 1.3, cy - 8.8 - brow_raise)), R((cx + 10.2, cy - 8.0 - brow_raise))], HAIR, 1.08)

        # Broad, slightly downturned nose and compressed lower face.
        _line(draw, [R((cx + 0.8, cy - 0.5)), R((cx + 1.8, cy + 5.2))], SKIN_SHADE, 0.62)
        _line(draw, [R((cx - 1.0, cy + 6.0)), R((cx + 2.0, cy + 7.0)), R((cx + 5.5, cy + 5.8))], SKIN_DEEP, 0.52)
        _line(draw, [R((cx - 9.5, cy + 4.5)), R((cx - 6.5, cy + 6.0))], SKIN_SHADE, 0.34)
        _line(draw, [R((cx + 8.0, cy + 4.0)), R((cx + 11.0, cy + 5.8))], SKIN_DEEP, 0.34)

        mouth_center = R((cx + 0.8, cy + 12.0))
        if pose.mouth_open > 0.22:
            _ellipse(draw, mouth_center, 3.7, 0.95 + pose.mouth_open * 1.25, MOUTH, OUTLINE, 0.52)
            _line(draw, [(mouth_center[0] - 2.0, mouth_center[1]), (mouth_center[0] + 2.0, mouth_center[1])], SHIRT, 0.32)
        else:
            curve = pose.mouth_smile * 1.6
            _line(
                draw,
                [R((cx - 3.5, cy + 11.8)), R((cx + 0.8, cy + 12.2 + curve)), R((cx + 5.5, cy + 11.5))],
                MOUTH,
                0.76,
            )
def render(out_dir: str | Path, **opts) -> List[Path]:
    from ...authoring.sheet_build import build_sheet

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    renderer = RamenNujanRenderer()
    outputs = build_sheet(
        target=TARGET_BASENAME,
        rows=ROWS,
        render_fn=renderer.render_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        auto_crop=True,
    )
    return [
        outputs["spritesheet"],
        outputs["yaml"],
        outputs["ron"],
        outputs["preview"],
        outputs["canonical"],
        outputs["canonical_transparent"],
    ]


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render the polished, empty-handed Ramen-nujan character spritesheet.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "generated" / TARGET_BASENAME,
    )
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
