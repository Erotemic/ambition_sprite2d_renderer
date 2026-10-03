"""Procedural sprite target for Jeff Hinter in his shrinkwrap-converged armor.

This sibling target keeps the same caricature, proportions, and broad acting
vocabulary as the base Jeff Hinter sheet, but assumes the manifold optimization
has already converged into his body-conforming segmented armor. The ordinary
rows therefore render Jeff fully plated while preserving his recognizable
glasses, swept silver hair, and academic silhouette.

It also includes a dedicated transformation row that begins as ordinary Jeff,
deploys the manifold field, and settles into the armored form. The coordinate
plane, optimization mesh, and typography remain transient effects rather than
props. As with the base target, there is no drop shadow and no baked held
object; painter order stays legs -> torso -> both arms -> head.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from ...authoring.part_flipbook import publish_rig_flipbook
from .jeff_hinter import JeffHinterRenderer as _BaseJeffHinterRenderer
from .jeff_hinter import _lerp, _lerp_point, _pulse01, _smoothstep

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_BASENAME = "jeff_hinter_armored"
FRAME_SIZE = (160, 160)
SUPER = 4
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 145),
    ("walk", 8, 105),
    ("talk", 8, 108),
    ("interact", 10, 92),
    ("hint", 10, 92),
    ("visualize_2d", 12, 92),
    ("shout_14", 12, 78),
    ("shout_3", 12, 78),
    ("manifold_shrinkwrap", 16, 82),
    ("transform_armor", 18, 82),
    # Runtime-recognized defensive alias. On the armored sheet it uses the
    # plated brace directly rather than re-running the full transformation.
    ("block", 10, 82),
    # Runtime-recognized expressive alias for scripted uses that only know the
    # common CharacterAnim vocabulary. It intentionally reuses the outburst.
    ("taunt", 12, 78),
]

ACTOR_METADATA = {
    "actor": {"character_id": "npc_jeff_hinter_armored", "display_name": "Jeff Hinter (Armored)"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": ["story", "humanoid", "scholar", "hint_npc", "ai_history", "manifold_armor", "armored_variant"],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": None,
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
    "actions": {"default_preset": "peaceful"},
    "visual": {"default_pose": "idle"},
    "tags": ["story", "humanoid", "scholar", "hint_npc", "ai_history", "manifold_armor", "armored_variant"],
    "sockets": {
        "head": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 70.0, "y": 43.0},
        },
        "chest": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 72.0, "y": 91.0},
        },
        "hand_l": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 52.0, "y": 105.0},
        },
        "hand_r": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 94.0, "y": 101.0},
        },
        "speech_bubble": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 72.0, "y": 10.0},
        },
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "interaction.hint": {"animation": "hint", "events": []},
        "emote.visualize_2d": {"animation": "visualize_2d", "events": []},
        "emote.shout_14": {"animation": "shout_14", "events": []},
        "emote.shout_3": {"animation": "shout_3", "events": []},
        "ability.manifold_shrinkwrap": {"animation": "manifold_shrinkwrap", "events": []},
        "ability.transform_armor": {"animation": "transform_armor", "events": []},
        "defense.block": {"animation": "block", "events": []},
    },
}


ACTOR_METADATA.update(
    {
        "authoring_description": (
            "Armored Jeff Hinter is the converged combat form of the Geoffrey Hinton parody. His "
            "abstract manifold has shrink-wrapped into literal segmented armor, preserving the "
            "glasses, hair, academic posture, and dimensional jokes beneath a body-sized optimization "
            "result."
        ),
        "gameplay_description": (
            "Use as a transformed ally, miniboss, or defensive playable form. The armor should feel "
            "mathematically fitted rather than forged: deploy it through convergence, let attacks "
            "follow learned surfaces, and retain Jeff's tendency to explain the representation while "
            "under fire."
        ),
    }
)
ACTOR_METADATA.setdefault("dialogue_hints", {}).setdefault(
    "barks",
    [
        'THREE! The armor has depth...',
        'Please attack conventionally.',
        'When everything glows, leave.',
    ],
)

ARMORED_DEFAULT_ANIMATIONS = {
    "idle",
    "walk",
    "talk",
    "interact",
    "hint",
    "visualize_2d",
    "shout_14",
    "shout_3",
    "taunt",
}

# The palette and drawing are the base sheet's (``jeff_hinter``): this sheet
# only poses Jeff differently.


@dataclass
class Pose:
    body_x: float = 0.0
    body_y: float = 0.0
    lean: float = 0.0
    head_x: float = 0.0
    head_y: float = 0.0
    head_tilt: float = 0.0
    blink: bool = False
    mouth_open: float = 0.0
    mouth_round: float = 0.0
    mouth_smile: float = 0.0
    brow_lift: float = 0.0
    gaze_x: float = 0.0
    gaze_y: float = 0.0
    near_shoulder: Point = (86.0, 78.0)
    near_elbow: Point = (94.0, 96.0)
    near_hand: Point = (93.0, 113.0)
    far_shoulder: Point = (59.0, 80.0)
    far_elbow: Point = (50.0, 98.0)
    far_hand: Point = (52.0, 114.0)
    near_hand_mode: str = "relaxed"
    far_hand_mode: str = "relaxed"
    near_hip: Point = (80.0, 116.0)
    near_knee: Point = (82.0, 133.0)
    near_ankle: Point = (83.0, 149.0)
    far_hip: Point = (66.0, 116.0)
    far_knee: Point = (64.0, 133.0)
    far_ankle: Point = (63.0, 149.0)
    plane_strength: float = 0.0
    plane_phase: float = 0.0
    hint_strength: float = 0.0
    shout_strength: float = 0.0
    shout_phase: float = 0.0
    shout_text: str = "14"
    manifold_strength: float = 0.0
    manifold_progress: float = 0.0
    manifold_phase: float = 0.0
    armor_strength: float = 0.0
    armor_lock: float = 0.0

    def __init__(self, animation: str, frame_idx: int, nframes: int) -> None:
        t = frame_idx / max(1, nframes - 1)
        phase = frame_idx / max(1, nframes)
        wave = math.sin(phase * math.tau)
        cosine = math.cos(phase * math.tau)

        self.body_x = 0.0
        self.body_y = 0.0
        self.lean = -1.5
        self.head_x = 0.0
        self.head_y = 0.0
        self.head_tilt = -2.0
        self.blink = False
        self.mouth_open = 0.0
        self.mouth_round = 0.0
        self.mouth_smile = 0.0
        self.brow_lift = 0.0
        self.gaze_x = 0.4
        self.gaze_y = 0.0
        self.near_shoulder = (86.0, 78.0)
        self.near_elbow = (94.0, 96.0)
        self.near_hand = (93.0, 113.0)
        self.far_shoulder = (59.0, 80.0)
        self.far_elbow = (50.0, 98.0)
        self.far_hand = (52.0, 114.0)
        self.near_hand_mode = "relaxed"
        self.far_hand_mode = "relaxed"
        self.near_hip = (80.0, 116.0)
        self.near_knee = (82.0, 133.0)
        self.near_ankle = (83.0, 149.0)
        self.far_hip = (66.0, 116.0)
        self.far_knee = (64.0, 133.0)
        self.far_ankle = (63.0, 149.0)
        self.plane_strength = 0.0
        self.plane_phase = phase
        self.hint_strength = 0.0
        self.shout_strength = 0.0
        self.shout_phase = t
        self.shout_text = "14"
        self.manifold_strength = 0.0
        self.manifold_progress = 0.0
        self.manifold_phase = phase
        self.armor_strength = 0.0
        self.armor_lock = 0.0

        if animation == "idle":
            breath = 0.5 - 0.5 * cosine
            self.body_y = -0.55 * breath
            self.head_y = -0.35 * breath
            self.head_x = 0.25 * wave
            self.head_tilt = -2.5 + 0.8 * wave
            self.near_elbow = (94.0 + 0.4 * wave, 96.0)
            self.near_hand = (93.0 + 0.35 * wave, 113.0 + 0.35 * cosine)
            self.far_elbow = (50.0 - 0.35 * wave, 98.0)
            self.far_hand = (52.0 - 0.25 * wave, 114.0)
            self.gaze_x = 0.55 + 0.22 * wave
            self.blink = frame_idx == 6
            self.mouth_smile = 0.08

        elif animation == "walk":
            stride = 8.5 * wave
            near_lift = max(0.0, wave) * 4.5
            far_lift = max(0.0, -wave) * 4.5
            self.body_x = 0.5 * wave
            self.body_y = -1.25 * abs(wave)
            self.lean = -3.5
            self.head_x = 0.35 * wave
            self.head_y = -0.25 * abs(wave)
            self.head_tilt = -3.6 - 0.45 * wave
            self.near_knee = (82.0 + stride * 0.50, 133.0 - near_lift * 0.2)
            self.near_ankle = (83.0 + stride, 149.0 - near_lift)
            self.far_knee = (64.0 - stride * 0.48, 133.0 - far_lift * 0.2)
            self.far_ankle = (63.0 - stride * 0.92, 149.0 - far_lift)
            self.near_elbow = (94.0 - stride * 0.34, 96.0)
            self.near_hand = (93.0 - stride * 0.48, 113.0)
            self.far_elbow = (50.0 + stride * 0.28, 98.0)
            self.far_hand = (52.0 + stride * 0.40, 114.0)
            self.blink = frame_idx == 7

        elif animation == "talk":
            gesture = 0.5 - 0.5 * math.cos(phase * math.tau)
            alternate = math.sin(phase * math.tau)
            self.body_y = -0.45 * gesture
            self.head_tilt = -4.0 + 3.5 * alternate
            self.head_x = 0.6 * alternate
            self.mouth_open = 0.25 + 0.65 * max(0.0, math.sin(phase * math.tau * 2.0))
            self.mouth_smile = 0.18
            self.brow_lift = 0.35 + 0.5 * gesture
            self.near_elbow = (101.0 + 2.0 * alternate, 90.0 - 4.0 * gesture)
            self.near_hand = (110.0 + 3.0 * alternate, 82.0 - 2.0 * gesture)
            self.near_hand_mode = "open"
            self.far_elbow = (48.0, 96.0 - 2.0 * gesture)
            self.far_hand = (57.0, 101.0 - 3.0 * gesture)
            self.far_hand_mode = "open"
            self.gaze_x = 0.8
            self.blink = frame_idx == 6

        elif animation in {"interact", "hint"}:
            # Tap temple -> realize -> point outward.  The explicit point is an
            # empty-hand gesture, not a baked held item.
            gather = _smoothstep(min(1.0, t / 0.32))
            reveal = _smoothstep((t - 0.28) / 0.42)
            settle = _smoothstep((t - 0.72) / 0.28)
            self.hint_strength = _pulse01((t - 0.12) / 0.88)
            self.body_x = 1.6 * reveal - 0.7 * settle
            self.body_y = -1.2 * self.hint_strength
            self.lean = -4.0 + 5.0 * reveal
            self.head_tilt = -10.0 * gather + 13.0 * reveal - 4.0 * settle
            self.head_x = 1.1 * reveal
            self.brow_lift = 0.4 + 1.2 * reveal
            self.mouth_smile = 0.15 + 0.45 * reveal
            self.mouth_open = 0.15 + 0.35 * math.sin(t * math.pi * 3.0) ** 2
            self.gaze_x = _lerp(-0.45, 1.0, reveal)
            self.gaze_y = _lerp(-0.25, 0.0, reveal)
            temple_hand = (88.0, 47.0)
            point_hand = (126.0, 73.0)
            self.near_elbow = _lerp_point((94.0, 96.0), (102.0, 76.0), gather)
            self.near_elbow = _lerp_point(self.near_elbow, (108.0, 78.0), reveal)
            self.near_hand = _lerp_point((93.0, 113.0), temple_hand, gather)
            self.near_hand = _lerp_point(self.near_hand, point_hand, reveal)
            self.near_hand = _lerp_point(self.near_hand, (112.0, 91.0), settle)
            self.near_hand_mode = "temple" if reveal < 0.48 else "point"
            self.far_elbow = _lerp_point((50.0, 98.0), (51.0, 90.0), reveal)
            self.far_hand = _lerp_point((52.0, 114.0), (61.0, 90.0), reveal)
            self.far_hand_mode = "open"
            self.blink = frame_idx == 2

        elif animation == "visualize_2d":
            emerge = _smoothstep(t / 0.24)
            focus = _smoothstep((t - 0.18) / 0.25)
            release = _smoothstep((t - 0.82) / 0.18)
            strength = emerge * (1.0 - 0.55 * release)
            self.plane_strength = strength
            self.plane_phase = phase
            self.body_x = -1.5 * focus + 0.8 * release
            self.body_y = -0.7 * strength
            self.lean = -4.0 - 3.5 * focus
            self.head_x = 0.8 * focus
            self.head_y = -0.8 * focus
            self.head_tilt = -8.0 + 2.0 * wave
            self.brow_lift = 0.75
            self.mouth_open = 0.12 + 0.18 * abs(wave)
            self.gaze_x = 1.15
            self.gaze_y = -0.15 + 0.2 * wave
            self.far_elbow = _lerp_point((50.0, 98.0), (45.0, 82.0), focus)
            self.far_hand = _lerp_point((52.0, 114.0), (53.0, 70.0), focus)
            self.far_hand_mode = "frame"
            self.near_elbow = _lerp_point((94.0, 96.0), (101.0, 91.0), focus)
            self.near_hand = _lerp_point((93.0, 113.0), (120.0, 104.0), focus)
            self.near_hand_mode = "frame"
            self.blink = frame_idx == 10

        elif animation == "manifold_shrinkwrap":
            # Three nested contours iteratively contract onto Jeff's silhouette.
            # The residual vectors shorten as the fit improves; at convergence the
            # manifold hardens into segmented armor rather than becoming a bubble.
            deploy = _smoothstep(t / 0.18)
            optimize = _smoothstep((t - 0.10) / 0.48)
            lock = _smoothstep((t - 0.50) / 0.22)
            field_fade = _smoothstep((t - 0.68) / 0.27)
            self.manifold_strength = deploy * (1.0 - 0.82 * field_fade)
            self.manifold_progress = optimize
            self.manifold_phase = phase
            self.armor_strength = _smoothstep((t - 0.30) / 0.40)
            self.armor_lock = _pulse01((t - 0.48) / 0.40)

            # Open calibration stance -> compressed fit -> broad armored brace.
            self.body_y = 2.4 * deploy - 2.0 * lock
            self.body_x = -0.7 * optimize + 1.1 * lock
            self.lean = -5.0 - 2.5 * optimize + 8.5 * lock
            self.head_x = -0.8 * optimize + 0.7 * lock
            self.head_y = 1.0 * deploy - 1.2 * lock
            self.head_tilt = -8.0 - 3.0 * optimize + 10.0 * lock
            self.brow_lift = 0.5 + 0.8 * optimize
            self.mouth_open = 0.08 + 0.28 * (1.0 - lock) * abs(wave)
            self.mouth_smile = 0.10 + 0.18 * lock
            self.gaze_x = -0.15 + 0.55 * lock
            self.gaze_y = 0.45 - 0.35 * lock

            near_open_elbow = (104.0, 91.0)
            near_open_hand = (119.0, 87.0)
            far_open_elbow = (43.0, 92.0)
            far_open_hand = (29.0, 88.0)
            self.near_elbow = _lerp_point((94.0, 96.0), near_open_elbow, deploy)
            self.near_hand = _lerp_point((93.0, 113.0), near_open_hand, deploy)
            self.far_elbow = _lerp_point((50.0, 98.0), far_open_elbow, deploy)
            self.far_hand = _lerp_point((52.0, 114.0), far_open_hand, deploy)
            self.near_elbow = _lerp_point(self.near_elbow, (100.0, 103.0), lock)
            self.near_hand = _lerp_point(self.near_hand, (101.0, 117.0), lock)
            self.far_elbow = _lerp_point(self.far_elbow, (47.0, 103.0), lock)
            self.far_hand = _lerp_point(self.far_hand, (47.0, 117.0), lock)
            self.near_hand_mode = "open" if lock < 0.58 else "relaxed"
            self.far_hand_mode = "open" if lock < 0.58 else "relaxed"

            self.near_knee = _lerp_point((82.0, 133.0), (86.0, 133.0), lock)
            self.near_ankle = _lerp_point((83.0, 149.0), (92.0, 149.0), lock)
            self.far_knee = _lerp_point((64.0, 133.0), (60.0, 133.0), lock)
            self.far_ankle = _lerp_point((63.0, 149.0), (53.0, 149.0), lock)

            # A crisp one-frame settling vibration makes the lock-in read as a
            # mechanical optimization result rather than a costume dissolve.
            if self.armor_lock > 0.35:
                settle_shake = math.sin(t * math.pi * 18.0) * 0.65 * self.armor_lock
                self.body_x += settle_shake
                self.head_x -= settle_shake * 0.45
            self.blink = 0.34 < t < 0.46

        elif animation == "transform_armor":
            # Base Jeff -> manifold field deploy -> converged armor -> calm plated
            # settle. This ends close to the armored idle pose so it chains cleanly.
            deploy = _smoothstep(t / 0.16)
            optimize = _smoothstep((t - 0.08) / 0.28)
            lock = _smoothstep((t - 0.34) / 0.18)
            settle = _smoothstep((t - 0.64) / 0.20)
            field_fade = _smoothstep((t - 0.54) / 0.24)
            self.manifold_strength = deploy * (1.0 - 0.90 * field_fade)
            self.manifold_progress = optimize
            self.manifold_phase = phase
            self.armor_strength = _smoothstep((t - 0.18) / 0.26)
            self.armor_lock = _smoothstep((t - 0.40) / 0.16)

            self.body_y = 1.3 * deploy - 1.6 * lock - 0.8 * settle
            self.body_x = -0.4 * optimize + 0.6 * lock
            self.lean = -3.5 - 1.8 * optimize + 7.2 * lock - 1.6 * settle
            self.head_x = -0.5 * optimize + 0.55 * lock
            self.head_y = 0.5 * deploy - 0.9 * lock - 0.2 * settle
            self.head_tilt = -5.0 - 2.0 * optimize + 8.5 * lock - 2.0 * settle
            self.brow_lift = 0.25 + 0.75 * optimize
            self.mouth_open = 0.06 + 0.24 * (1.0 - lock) * abs(wave)
            self.mouth_smile = 0.05 + 0.15 * lock + 0.06 * settle
            self.gaze_x = 0.10 + 0.42 * lock
            self.gaze_y = 0.20 - 0.20 * lock

            self.near_elbow = _lerp_point((94.0, 96.0), (101.0, 90.0), deploy)
            self.near_hand = _lerp_point((93.0, 113.0), (117.0, 86.0), deploy)
            self.far_elbow = _lerp_point((50.0, 98.0), (44.0, 92.0), deploy)
            self.far_hand = _lerp_point((52.0, 114.0), (30.0, 88.0), deploy)
            self.near_elbow = _lerp_point(self.near_elbow, (100.0, 103.0), lock)
            self.near_hand = _lerp_point(self.near_hand, (98.0, 115.0), lock)
            self.far_elbow = _lerp_point(self.far_elbow, (48.0, 103.0), lock)
            self.far_hand = _lerp_point(self.far_hand, (49.0, 116.0), lock)
            self.near_elbow = _lerp_point(self.near_elbow, (95.0, 97.0), settle)
            self.near_hand = _lerp_point(self.near_hand, (94.0, 113.0), settle)
            self.far_elbow = _lerp_point(self.far_elbow, (51.0, 98.0), settle)
            self.far_hand = _lerp_point(self.far_hand, (53.0, 114.0), settle)
            self.near_hand_mode = "open" if lock < 0.50 else "relaxed"
            self.far_hand_mode = "open" if lock < 0.50 else "relaxed"

            self.near_knee = _lerp_point((82.0, 133.0), (85.0, 133.0), lock)
            self.near_ankle = _lerp_point((83.0, 149.0), (88.0, 149.0), lock)
            self.far_knee = _lerp_point((64.0, 133.0), (61.0, 133.0), lock)
            self.far_ankle = _lerp_point((63.0, 149.0), (58.0, 149.0), lock)

            if self.armor_lock > 0.2 and settle < 0.75:
                settle_shake = math.sin(t * math.pi * 18.0) * 0.58 * self.armor_lock * (1.0 - settle)
                self.body_x += settle_shake
                self.head_x -= settle_shake * 0.42
            self.blink = 0.28 < t < 0.42

        elif animation == "block":
            # Already-armored defensive brace.
            brace = _smoothstep(t / 0.22)
            pulse = 0.5 - 0.5 * math.cos(phase * math.tau)
            self.armor_strength = 1.0
            self.armor_lock = 1.0
            self.body_y = -1.3 * brace - 0.35 * pulse
            self.body_x = 0.45 * brace
            self.lean = 4.0 + 1.8 * brace
            self.head_x = 0.35 * brace
            self.head_y = -0.45 * brace
            self.head_tilt = 4.5 + 1.2 * brace
            self.brow_lift = 0.55 + 0.15 * pulse
            self.mouth_open = 0.05 + 0.08 * pulse
            self.mouth_smile = 0.08
            self.gaze_x = 0.55
            self.gaze_y = -0.05
            self.near_elbow = (98.0, 101.0)
            self.near_hand = (98.0, 116.0)
            self.far_elbow = (48.0, 101.0)
            self.far_hand = (49.0, 117.0)
            self.near_hand_mode = "relaxed"
            self.far_hand_mode = "relaxed"
            self.near_knee = (85.0, 133.0)
            self.near_ankle = (90.0, 149.0)
            self.far_knee = (61.0, 133.0)
            self.far_ankle = (56.0, 149.0)
            self.blink = frame_idx == nframes - 2

        elif animation in {"shout_14", "shout_3", "taunt"}:
            # ``14`` parodies the classic high-dimensional visualization
            # trick; ``3`` is Jeff trying to recover the missing depth axis
            # of this deliberately two-dimensional game.
            self.shout_text = "3" if animation == "shout_3" else "14"
            inhale = _smoothstep(min(1.0, t / 0.26))
            blast = _smoothstep((t - 0.22) / 0.18)
            decay = _smoothstep((t - 0.66) / 0.34)
            strength = blast * (1.0 - 0.65 * decay)
            self.shout_strength = strength
            self.shout_phase = t
            self.body_x = -2.0 * inhale + 4.2 * strength - 2.0 * decay
            self.body_y = 1.2 * inhale - 3.0 * strength + 2.2 * decay
            self.lean = -8.0 * inhale + 15.0 * strength - 7.0 * decay
            self.head_x = -1.4 * inhale + 2.6 * strength
            self.head_y = 0.7 * inhale - 2.5 * strength
            self.head_tilt = -13.0 * inhale + 21.0 * strength - 7.0 * decay
            self.brow_lift = 1.4 * strength
            self.mouth_open = 0.1 + 1.35 * strength
            self.mouth_round = 0.95 * strength
            self.gaze_x = 0.95
            self.gaze_y = -0.25
            self.near_elbow = _lerp_point((94.0, 96.0), (102.0, 75.0), inhale)
            self.near_hand = _lerp_point((93.0, 113.0), (101.0, 64.0), inhale)
            self.far_elbow = _lerp_point((50.0, 98.0), (54.0, 76.0), inhale)
            self.far_hand = _lerp_point((52.0, 114.0), (57.0, 65.0), inhale)
            self.near_hand_mode = "cup_mouth"
            self.far_hand_mode = "cup_mouth"
            # The body rattles slightly at peak volume.
            if strength > 0.55:
                shake = math.sin(t * math.pi * 12.0) * 0.9 * strength
                self.body_x += shake
                self.head_x -= shake * 0.7
            self.blink = strength > 0.5

        if animation in ARMORED_DEFAULT_ANIMATIONS:
            # The alternate sheet assumes Jeff has already completed the shrinkwrap
            # optimization. Ordinary actions therefore keep the acting vocabulary
            # but render with the converged segmented armor at all times.
            self.armor_strength = 1.0
            self.armor_lock = 1.0
            self.body_y -= 0.8
            self.head_y -= 0.2
            self.lean += 0.7
            self.brow_lift += 0.08


class JeffHinterRenderer(_BaseJeffHinterRenderer):
    """The base Jeff rig (``jeff_hinter``) drawn from this sheet's poses."""

    pose_cls = Pose


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    from ...authoring.sheet_build import build_sheet

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    renderer = JeffHinterRenderer()
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_BASENAME,
        rows=ROWS,
        render_fn=renderer.render_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        auto_crop=False,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning={"collision_scale": 1.05},
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
    parts = publish_rig_flipbook(TARGET_BASENAME, ROWS, renderer.render_frame, outputs, frame_transform, Path(out_dir))
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())


__all__ = ["ACTOR_METADATA", "render"]
