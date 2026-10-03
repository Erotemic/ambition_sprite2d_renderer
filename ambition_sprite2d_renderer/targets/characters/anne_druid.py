"""Procedural full-action renderer for Anne Druid.

Anne Druid is an affectionate science-fantasy parody inspired by Ann Druyan's
work as a writer, producer, science communicator, and creative director of the
Voyager Golden Record.  The character is not intended as a literal portrait.
She is a cosmic naturalist: part forest druid, part interstellar archivist, and
part keeper of messages sent toward civilizations humanity may never meet.

The silhouette is built around a crescent of dark silver-streaked hair, a long
teal travelling robe, leaf-shaped shoulder panels, and the Golden Record worn
as a luminous round shield.  Her effects translate ideas associated with the
Voyager record and ``Cosmos`` into readable game actions: whale-song rings,
pulsar maps, orbiting seeds, constellation vines, and a record cast that leaves
an etched interstellar-message trail.

Everything is drawn with supersampled Pillow geometry.  The target has no floor
ellipse or drop shadow, and the record is part of the character design rather
than a separately published held prop.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, replace
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw

from ...authoring.portrait import PortraitClip, write_portrait_sheet
from ...authoring import rigdoc, shape_rig
from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.sheet_build import build_sheet, write_canonical
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "anne_druid"
FRAME_W = 128
FRAME_H = 128
SUPER = 4
PORTRAIT_SIZE = (192, 192)

AUTHORING_DESCRIPTION = {
    "parody_of": "Ann Druyan",
    "concept": (
        "An affectionate science-fantasy transformation of the writer, producer, "
        "science communicator, and Voyager Golden Record creative director into "
        "a cosmic druid who preserves messages for distant life."
    ),
    "name_origin": (
        "Anne Druid turns Ann Druyan's surname into a fantasy class while keeping "
        "the character centered on communication, wonder, skepticism, and cosmic scale."
    ),
    "visual_inspiration": [
        "The Voyager Golden Record becomes a luminous circular shield and spell focus.",
        "The pulsar map becomes branching silver-gold line work around major casts.",
        "Whale song and natural sounds become expanding cyan waveform rings.",
        "A teal travelling robe and constellation vines merge naturalist and cosmic imagery.",
        "Dark hair with silver star-like streaks creates a mature, specific silhouette without copying a photograph.",
    ],
    "gameplay_inspiration": [
        "golden_record_guard blocks and reflects with the record's engraved surface.",
        "whale_song converts recorded natural sound into a broad resonant wave.",
        "pulsar_beacon marks space with a rotating astronomical navigation diagram.",
        "cosmic_garden grows orbiting seeds and constellation vines from the floor.",
        "voyager_cast sends the record outward and recalls it like an interstellar boomerang."
    ],
    "boundaries": [
        "Treat the character as a warm fictional homage, not a literal likeness or biographical claim.",
        "Preserve agency and scientific curiosity; do not reduce her to somebody else's companion.",
        "Keep the Golden Record, natural sound, and cosmic communication as the central design language.",
        "Avoid generic witch iconography when a scientific or naturalist visual metaphor can do the same job.",
    ],
}

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 148),
    ("walk", 8, 104),
    ("run", 8, 80),
    ("crouch", 6, 96),
    ("crouch_walk", 8, 92),
    ("jump", 6, 90),
    ("fall", 6, 92),
    ("land_hard", 7, 84),
    ("dash_startup", 4, 54),
    ("dash", 6, 60),
    ("slide", 6, 68),
    ("roll", 8, 62),
    ("wall_grab", 6, 104),
    ("wall_jump", 6, 82),
    ("ledge_grab", 6, 98),
    ("ledge_climb", 6, 94),
    ("climb", 8, 98),
    ("swim", 8, 104),
    ("block", 6, 82),
    ("hit", 5, 84),
    ("death", 8, 108),
    ("talk", 8, 106),
    ("interact", 8, 94),
    ("golden_record_guard", 8, 68),
    ("whale_song", 10, 74),
    ("pulsar_beacon", 10, 76),
    ("cosmic_garden", 10, 78),
    ("voyager_cast", 10, 66),
    ("celebrate", 8, 90),
    ("taunt", 8, 96),
]

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_anne_druid",
        "display_name": "Anne Druid",
    },
    "authoring_description": AUTHORING_DESCRIPTION,
    "dialogue_hints": {
        "suggested_barks": [
            'The record is not a time capsule. It is an introduction.',
            'Listen long enough and the universe stops sounding empty.',
            'Wonder without skepticism is fog.',
            'The map points home. If you can read a pulsar.',
        ],
        "fallback_dialogue": [
            'We sent music, greetings, a heartbeat, and the sound of a kiss. Optimism is sometimes an engineering decision.',
            'A message for strangers begins with the hope that strangers can understand.',
            'Skepticism without wonder is a locked door.',
            'I do not know who finds it. That was never the point of sending it.',
        ],
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": [
            "story",
            "humanoid",
            "scientist",
            "science_communicator",
            "cosmic_druid",
            "golden_record_keeper",
            "playable_candidate",
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
    "visual": {
        "default_pose": "idle",
        "portrait": {
            "face_guide": {
                "center": {"x": 65.0, "y": 31.0},
                "size": {"w": 31.0, "h": 35.0},
                "source_size": {"w": 128.0, "h": 128.0},
            }
        },
    },
    "tags": [
        "story",
        "humanoid",
        "scientist",
        "science_communicator",
        "cosmic_druid",
        "golden_record_keeper",
        "playable_candidate",
    ],
    "sockets": {
        "head": {"source": "explicit.anne_druid", "point": {"x": 65.0, "y": 30.0}},
        "chest": {"source": "explicit.anne_druid", "point": {"x": 64.0, "y": 62.0}},
        "hand_l": {"source": "explicit.anne_druid", "point": {"x": 46.0, "y": 73.0}},
        "hand_r": {"source": "explicit.anne_druid", "point": {"x": 84.0, "y": 70.0}},
        "record_center": {"source": "explicit.anne_druid", "point": {"x": 48.0, "y": 62.0}},
        "speech_bubble": {"source": "explicit.anne_druid", "point": {"x": 65.0, "y": 4.0}},
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "traversal.jump": {"animation": "jump", "events": []},
        "traversal.fall": {"animation": "fall", "events": []},
        "action.melee.primary": {"animation": "golden_record_guard", "events": []},
        "action.ranged.primary": {"animation": "voyager_cast", "events": []},
        "action.special.primary": {"animation": "whale_song", "events": []},
        "action.special.secondary": {"animation": "pulsar_beacon", "events": []},
        "action.special.tertiary": {"animation": "cosmic_garden", "events": []},
        "action.defense.block": {"animation": "block", "events": []},
        "action.defense.roll": {"animation": "roll", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
    },
    "provenance": {
        "variant_family": TARGET_NAME,
        "variant_id": "gpt_5_6_thinking_original_2026_07_26",
        "lineage": [
            {
                "revision_id": "anne_druid_concept_direction",
                "creator_kind": "human",
                "creator": "Jon Crall",
                "contribution": "selected_anne_druid_and_required_authoring_description_for_new_characters",
            },
            {
                "revision_id": "anne_druid_procedural_sprite_v1",
                "creator_kind": "model",
                "creator": "gpt-5.6-thinking",
                "parent_revision_id": "anne_druid_concept_direction",
                "contribution": "procedural_full_action_sprite_native_portraits_and_actor_authoring_notes",
            },
        ],
    },
}

# Palette: deep space and forest colors, with the record acting as the single
# high-value metallic focal point.
OUTLINE = (18, 21, 29, 255)
OUTLINE_SOFT = (43, 48, 61, 255)
SKIN = (174, 118, 88, 255)
SKIN_LIGHT = (224, 164, 121, 255)
SKIN_SHADE = (124, 76, 66, 255)
HAIR_DEEP = (25, 25, 34, 255)
HAIR = (43, 40, 51, 255)
HAIR_MID = (72, 66, 78, 255)
HAIR_SILVER = (159, 157, 166, 255)
TEAL_DEEP = (18, 55, 62, 255)
TEAL = (28, 88, 91, 255)
TEAL_LIGHT = (50, 128, 122, 255)
MOSS = (58, 102, 72, 255)
MOSS_LIGHT = (98, 144, 91, 255)
ROBE_DARK = (30, 39, 53, 255)
ROBE = (43, 60, 75, 255)
ROBE_LIGHT = (70, 89, 101, 255)
BOOT = (44, 39, 43, 255)
GOLD_DEEP = (113, 75, 24, 255)
GOLD = (205, 153, 53, 255)
GOLD_LIGHT = (250, 218, 111, 255)
COPPER = (173, 98, 45, 255)
STAR = (249, 241, 202, 255)
CYAN = (90, 209, 215, 255)
CYAN_LIGHT = (184, 245, 244, 255)
VIOLET = (155, 110, 205, 255)
VIOLET_LIGHT = (222, 190, 243, 255)
LEAF = (80, 151, 99, 255)
LEAF_LIGHT = (145, 202, 125, 255)
EYE = (35, 26, 26, 255)
MOUTH = (111, 55, 59, 255)


def _fade(color: RGBA, alpha: float) -> RGBA:
    return color[:3] + (max(0, min(255, int(round(color[3] * alpha)))),)


def _s(value: float) -> int:
    return max(1, int(round(value * SUPER)))


def _pt(point: Point) -> Tuple[int, int]:
    return int(round(point[0] * SUPER)), int(round(point[1] * SUPER))


def _pts(points: Sequence[Point]) -> List[Tuple[int, int]]:
    return [_pt(p) for p in points]


def _ellipse(draw: ImageDraw.ImageDraw, center: Point, rx: float, ry: float, fill: RGBA, outline: RGBA | None = None, width: float = 1.0) -> None:
    x, y = center
    box = _pt((x - rx, y - ry)) + _pt((x + rx, y + ry))
    draw.ellipse(box, fill=fill, outline=outline, width=_s(width) if outline else 1)


def _line(draw: ImageDraw.ImageDraw, points: Sequence[Point], fill: RGBA, width: float = 1.0) -> None:
    draw.line(_pts(points), fill=fill, width=_s(width), joint="curve")


def _poly(draw: ImageDraw.ImageDraw, points: Sequence[Point], fill: RGBA, outline: RGBA | None = None, width: float = 1.0) -> None:
    pp = _pts(points)
    draw.polygon(pp, fill=fill)
    if outline:
        draw.line(pp + [pp[0]], fill=outline, width=_s(width), joint="curve")


def _arc(draw: ImageDraw.ImageDraw, center: Point, rx: float, ry: float, start: float, end: float, fill: RGBA, width: float = 1.0) -> None:
    x, y = center
    box = _pt((x - rx, y - ry)) + _pt((x + rx, y + ry))
    draw.arc(box, start=start, end=end, fill=fill, width=_s(width))


def _rot(point: Point, degrees: float) -> Point:
    rad = math.radians(degrees)
    c, s = math.cos(rad), math.sin(rad)
    return point[0] * c - point[1] * s, point[0] * s + point[1] * c


def _add(a: Point, b: Point) -> Point:
    return a[0] + b[0], a[1] + b[1]


def _limb(origin: Point, length: float, degrees: float) -> Point:
    return _add(origin, _rot((length, 0.0), degrees))


def _capsule(draw: ImageDraw.ImageDraw, a: Point, b: Point, radius: float, fill: RGBA, outline: RGBA = OUTLINE, width: float = 1.0) -> None:
    _line(draw, [a, b], outline, radius * 2.0 + width * 2.0)
    _line(draw, [a, b], fill, radius * 2.0)
    _ellipse(draw, a, radius, radius, fill, outline, width)
    _ellipse(draw, b, radius, radius, fill, outline, width)


def _leaf(draw: ImageDraw.ImageDraw, center: Point, length: float, width: float, degrees: float, fill: RGBA, outline: RGBA = OUTLINE_SOFT) -> None:
    ux = _rot((length / 2.0, 0.0), degrees)
    uy = _rot((0.0, width / 2.0), degrees)
    a = (center[0] - ux[0], center[1] - ux[1])
    b = (center[0] + uy[0], center[1] + uy[1])
    c = (center[0] + ux[0], center[1] + ux[1])
    d = (center[0] - uy[0], center[1] - uy[1])
    _poly(draw, [a, b, c, d], fill, outline, 0.8)
    _line(draw, [a, c], _fade(outline, 0.75), 0.65)


@dataclass(frozen=True)
class Pose:
    x: float = 0.0
    y: float = 0.0
    lean: float = 0.0
    squash: float = 0.0
    stride: float = 0.0
    knee: float = 0.0
    arm_l: float = 104.0
    fore_l: float = 76.0
    arm_r: float = 58.0
    fore_r: float = 20.0
    head_tilt: float = 0.0
    record_x: float = 47.0
    record_y: float = 61.0
    record_scale: float = 1.0
    record_front: bool = False
    eye_closed: bool = False
    mouth_open: float = 0.0
    robe_flare: float = 0.0
    effect: str = ""
    effect_phase: float = 0.0
    alpha: float = 1.0


def _phase(frame_idx: int, nframes: int) -> float:
    return frame_idx / max(1, nframes)


def _pose(anim: str, frame_idx: int, nframes: int) -> Pose:
    t = _phase(frame_idx, nframes)
    wave = math.sin(t * math.tau)
    wave2 = math.sin(t * math.tau * 2.0)
    pose = Pose(y=-0.7 * wave, head_tilt=1.2 * wave, robe_flare=0.8 * wave)

    if anim == "walk":
        pose = replace(pose, x=0.8 * wave, y=-1.1 * abs(wave), stride=7.5 * wave, knee=2.8 * abs(wave), arm_l=104 - 18 * wave, arm_r=58 + 18 * wave, fore_l=74 + 6 * wave, fore_r=22 - 6 * wave, robe_flare=4.5 * wave)
    elif anim == "run":
        pose = replace(pose, x=1.5 * wave, y=-2.4 * abs(wave), lean=10.0, stride=12.0 * wave, knee=5.0 * abs(wave), arm_l=124 - 34 * wave, arm_r=24 + 34 * wave, fore_l=42, fore_r=142, robe_flare=-8.0 - 5.0 * wave)
    elif anim == "crouch":
        pose = replace(pose, y=11.0 + 1.0 * wave, squash=0.12, stride=3.0, arm_l=128, fore_l=72, arm_r=36, fore_r=80, robe_flare=5.0)
    elif anim == "crouch_walk":
        pose = replace(pose, y=10.0 - abs(wave), squash=0.12, stride=5.5 * wave, knee=4.0, arm_l=120 - 10 * wave, arm_r=42 + 10 * wave, robe_flare=5.0 * wave)
    elif anim == "jump":
        lift = math.sin(min(1.0, t) * math.pi)
        pose = replace(pose, y=0.5 - 7.0 * lift, stride=5.0 - 10.0 * t, knee=5.0, arm_l=224 - 28 * lift, fore_l=252, arm_r=-44 + 28 * lift, fore_r=-72, robe_flare=-9.0)
    elif anim == "fall":
        pose = replace(pose, y=-3.0 + 3.0 * t, stride=-3.0, knee=6.0, arm_l=178 + 10 * wave, fore_l=222, arm_r=2 - 10 * wave, fore_r=-42, robe_flare=-12.0 + 3.0 * wave)
    elif anim == "land_hard":
        impact = max(0.0, 1.0 - abs(t - 0.42) * 4.0)
        pose = replace(pose, y=10.0 * impact, squash=0.16 * impact, stride=8.0, knee=6.0, arm_l=140, fore_l=86, arm_r=22, fore_r=78, robe_flare=10.0 * impact)
    elif anim == "dash_startup":
        pose = replace(pose, lean=18.0 * t, y=5.0 * t, arm_l=122, fore_l=52, arm_r=32, fore_r=144, robe_flare=-8.0 * t)
    elif anim == "dash":
        pose = replace(pose, x=6.0 * t, y=-2.0, lean=22.0, stride=10.0 * wave, arm_l=146, fore_l=82, arm_r=18, fore_r=166, robe_flare=-14.0 - 4.0 * wave, effect="stardust", effect_phase=t)
    elif anim == "slide":
        pose = replace(pose, x=3.0, y=10.0, lean=24.0, squash=0.14, stride=11.0, arm_l=158, fore_l=100, arm_r=8, fore_r=166, robe_flare=-18.0, effect="stardust", effect_phase=t)
    elif anim == "roll":
        angle = t * 360.0
        pose = replace(pose, y=7.0 + 2.0 * math.sin(t * math.tau), squash=0.25, lean=angle, stride=0.0, arm_l=140, fore_l=205, arm_r=40, fore_r=-25, robe_flare=12.0, record_x=64.0, record_y=74.0, record_scale=1.12, effect="roll_stars", effect_phase=t)
    elif anim == "wall_grab":
        pose = replace(pose, x=10.0, y=-2.0, lean=-6.0, stride=-5.0, knee=5.0, arm_l=188, fore_l=180, arm_r=192, fore_r=180, robe_flare=-7.0)
    elif anim == "wall_jump":
        pose = replace(pose, x=7.0 - 13.0 * t, y=-4.0 * math.sin(t * math.pi), lean=-16.0, stride=-8.0, knee=5.0, arm_l=204, fore_l=230, arm_r=-18, fore_r=-48, robe_flare=12.0)
    elif anim == "ledge_grab":
        pose = replace(pose, y=4.0 + wave, arm_l=204, fore_l=178, arm_r=-24, fore_r=2, stride=-4.0, knee=5.0)
    elif anim == "ledge_climb":
        pose = replace(pose, x=5.0 * t, y=7.0 - 13.0 * t, arm_l=214 - 70 * t, fore_l=176 - 55 * t, arm_r=-34 + 65 * t, fore_r=2 + 80 * t, stride=5.0, robe_flare=7.0)
    elif anim == "climb":
        pose = replace(pose, y=1.5 * wave2, arm_l=210 - 36 * wave, fore_l=178, arm_r=-30 + 36 * wave, fore_r=2, stride=5.0 * wave, knee=5.0)
    elif anim == "swim":
        pose = replace(pose, y=-3.0 + 2.0 * wave, lean=78.0, arm_l=178 + 34 * wave, fore_l=200, arm_r=2 - 34 * wave, fore_r=-20, stride=6.0 * wave2, robe_flare=-12.0, effect="bubbles", effect_phase=t)
    elif anim in {"block", "golden_record_guard"}:
        pulse = math.sin(t * math.pi)
        pose = replace(pose, y=1.0, lean=-3.0, arm_l=30, fore_l=4, arm_r=24, fore_r=7, record_x=84.0 + 2.0 * pulse, record_y=65.0, record_scale=1.12 + 0.08 * pulse, record_front=True, effect="record_guard", effect_phase=t)
    elif anim == "hit":
        kick = math.sin(t * math.pi)
        pose = replace(pose, x=-5.0 * kick, lean=-15.0 * kick, y=-2.0 * kick, arm_l=154, fore_l=118, arm_r=12, fore_r=74, eye_closed=True, mouth_open=0.5, robe_flare=9.0 * kick, effect="hit_sparks", effect_phase=t)
    elif anim == "death":
        ease = min(1.0, t * 1.35)
        pose = replace(pose, x=-5.0 * ease, y=15.0 * ease, lean=-82.0 * ease, squash=0.08 * ease, arm_l=136, fore_l=96, arm_r=26, fore_r=82, eye_closed=True, robe_flare=15.0 * ease, alpha=1.0 - max(0.0, t - 0.72) * 2.2, effect="falling_stars", effect_phase=t)
    elif anim == "talk":
        pose = replace(pose, arm_r=34 - 12 * wave, fore_r=4 + 12 * wave, arm_l=112 + 8 * wave, fore_l=76, mouth_open=0.5 + 0.5 * max(0.0, wave2), head_tilt=3.0 * wave)
    elif anim == "interact":
        pose = replace(pose, arm_r=16 - 10 * math.sin(t * math.pi), fore_r=0, arm_l=112, fore_l=76, head_tilt=-3.0, effect="tiny_constellation", effect_phase=t)
    elif anim == "whale_song":
        bloom = math.sin(t * math.pi)
        pose = replace(pose, y=-1.5 * bloom, arm_l=150 - 25 * bloom, fore_l=118, arm_r=30 - 20 * bloom, fore_r=0, eye_closed=t > 0.18, mouth_open=0.75, record_x=48.0, record_y=63.0, effect="whale_song", effect_phase=t)
    elif anim == "pulsar_beacon":
        bloom = math.sin(t * math.pi)
        pose = replace(pose, y=-2.5 * bloom, arm_l=232, fore_l=258, arm_r=-52, fore_r=-78, eye_closed=t > 0.2, record_x=64.0, record_y=67.0, record_scale=1.02, effect="pulsar", effect_phase=t)
    elif anim == "cosmic_garden":
        pose = replace(pose, y=6.0, squash=0.06, arm_l=142 - 12 * wave, fore_l=96, arm_r=18 + 12 * wave, fore_r=84, head_tilt=4.0, effect="cosmic_garden", effect_phase=t)
    elif anim == "voyager_cast":
        cast = math.sin(min(1.0, t * 1.25) * math.pi)
        returning = t > 0.62
        rx = 48.0 + 59.0 * min(1.0, t / 0.55) if not returning else 107.0 - 59.0 * ((t - 0.62) / 0.38)
        pose = replace(pose, lean=12.0 * cast, arm_l=124, fore_l=72, arm_r=12 - 26 * cast, fore_r=-18, record_x=rx, record_y=51.0 - 12.0 * math.sin(t * math.pi), record_scale=0.92, record_front=True, effect="voyager_cast", effect_phase=t)
    elif anim == "celebrate":
        jump = max(0.0, math.sin(t * math.tau))
        pose = replace(pose, y=-5.0 * jump, arm_l=226 + 8 * wave, fore_l=252, arm_r=-46 - 8 * wave, fore_r=-72, mouth_open=0.65, record_x=47.0, record_y=61.0, effect="celebrate", effect_phase=t)
    elif anim == "taunt":
        pose = replace(pose, arm_l=112, fore_l=76, arm_r=18, fore_r=-8, head_tilt=-5.0, mouth_open=0.25, record_front=False, effect="pale_blue_dot", effect_phase=t)

    return pose


def _draw_record(draw: ImageDraw.ImageDraw, center: Point, scale: float, phase: float = 0.0, front: bool = False) -> None:
    r = 16.0 * scale
    _ellipse(draw, center, r + 1.5, r + 1.5, OUTLINE, None)
    _ellipse(draw, center, r, r, GOLD_DEEP, GOLD_LIGHT if front else GOLD, 1.1)
    _ellipse(draw, center, r - 2.0, r - 2.0, GOLD, _fade(GOLD_LIGHT, 0.8), 0.75)
    # Grooves and center label.
    for rr in (5.0, 8.0, 11.0, 13.5):
        _arc(draw, center, rr * scale, rr * scale, 15 + phase * 22, 330 + phase * 22, _fade(GOLD_LIGHT, 0.65), 0.55)
    _ellipse(draw, center, 3.4 * scale, 3.4 * scale, COPPER, GOLD_LIGHT, 0.65)
    _ellipse(draw, center, 0.9 * scale, 0.9 * scale, OUTLINE_SOFT, None)
    # Small radial inscription marks evoke the cover diagrams without trying to
    # reproduce the artifact literally at sprite scale.
    for idx in range(6):
        angle = idx * 60.0 + phase * 18.0
        a = _add(center, _rot((6.0 * scale, 0.0), angle))
        b = _add(center, _rot((12.2 * scale, 0.0), angle))
        _line(draw, [a, b], _fade(STAR, 0.72), 0.55)


def _draw_effects_behind(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    t = pose.effect_phase
    if pose.effect == "stardust":
        for i in range(7):
            # Leave enough source-space margin for the Lanczos halo after the
            # supersampled layer is reduced to the published 128px frame.
            x = max(7.0, 29.0 - i * 4.0 + 4.0 * math.sin(t * math.tau + i))
            y = 64.0 + ((i * 17) % 37) + 3.0 * math.cos(t * math.tau * 2 + i)
            _ellipse(draw, (x, y), 1.2 + 0.2 * (i % 2), 1.2 + 0.2 * (i % 2), _fade(STAR, 0.55 + 0.05 * i), None)
    elif pose.effect == "roll_stars":
        for i in range(9):
            a = t * 360.0 + i * 40.0
            p = _add((64.0, 73.0), _rot((24.0, 0.0), a))
            _ellipse(draw, p, 1.2, 1.2, _fade(STAR, 0.75), None)
    elif pose.effect == "bubbles":
        for i in range(6):
            p = (28.0 + i * 11.0, 89.0 - ((t * 30.0 + i * 7.0) % 30.0))
            _ellipse(draw, p, 1.6 + 0.3 * (i % 2), 1.6 + 0.3 * (i % 2), _fade(CYAN, 0.12), _fade(CYAN_LIGHT, 0.7), 0.7)
    elif pose.effect == "cosmic_garden":
        growth = min(1.0, t * 1.8)
        for side, sx in ((-1, 48.0), (1, 78.0)):
            points = []
            for i in range(7):
                u = i / 6.0
                points.append((sx + side * 11.0 * math.sin(u * 2.7 + side) * growth, 115.0 - u * 55.0 * growth))
            _line(draw, points, _fade(LEAF_LIGHT, 0.88), 1.3)
            for i in range(2, 7, 2):
                if i / 6.0 <= growth + 0.05:
                    _leaf(draw, points[i], 7.0, 3.4, -35.0 * side + i * 8.0, LEAF, _fade(STAR, 0.65))
        for i in range(5):
            angle = t * 120.0 + i * 72.0
            p = _add((64.0, 73.0), _rot((24.0 + 3.0 * (i % 2), 0.0), angle))
            _ellipse(draw, p, 1.8 + 0.4 * (i % 3), 1.8 + 0.4 * (i % 3), (GOLD_LIGHT if i % 2 else CYAN_LIGHT), OUTLINE_SOFT, 0.5)
    elif pose.effect == "falling_stars":
        for i in range(5):
            p = (40.0 + i * 11.0, 24.0 + ((t * 42.0 + i * 9.0) % 60.0))
            _line(draw, [(p[0] - 4.0, p[1] - 7.0), p], _fade(STAR, 0.45), 0.8)
            _ellipse(draw, p, 1.0, 1.0, _fade(STAR, 0.75), None)


def _draw_effects_front(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    t = pose.effect_phase
    if pose.effect == "record_guard":
        pulse = math.sin(t * math.pi)
        for i in range(3):
            r = 20.0 + i * 7.0 + pulse * 4.0
            _arc(draw, (pose.record_x, pose.record_y), r, r, -82, 82, _fade(CYAN_LIGHT, 0.7 - i * 0.16), 1.25)
        for i in range(5):
            a = -56.0 + i * 28.0
            p1 = _add((pose.record_x, pose.record_y), _rot((19.0, 0.0), a))
            p2 = _add((pose.record_x, pose.record_y), _rot((29.0 + 5.0 * pulse, 0.0), a))
            _line(draw, [p1, p2], _fade(GOLD_LIGHT, 0.8), 0.8)
    elif pose.effect == "hit_sparks":
        strength = math.sin(t * math.pi)
        for i in range(5):
            a = -60 + i * 30
            p1 = (91.0, 52.0)
            p2 = _add(p1, _rot((9.0 + 7.0 * strength, 0.0), a))
            _line(draw, [p1, p2], _fade(GOLD_LIGHT, 0.8), 1.0)
    elif pose.effect == "tiny_constellation":
        reveal = math.sin(t * math.pi)
        points = [(91, 53), (100, 46), (110, 55), (104, 66), (114, 72)]
        for a, b in zip(points, points[1:]):
            _line(draw, [a, b], _fade(CYAN_LIGHT, 0.65 * reveal), 0.8)
        for p in points:
            _ellipse(draw, p, 1.3, 1.3, _fade(STAR, reveal), None)
    elif pose.effect == "whale_song":
        bloom = math.sin(t * math.pi)
        origin = (77.0, 46.0)
        for i in range(5):
            r = 8.0 + i * 8.0 + t * 9.0
            _arc(draw, origin, r, r * 0.72, -58, 58, _fade(CYAN_LIGHT, max(0.0, 0.85 - i * 0.12) * bloom), 1.5)
        # A tiny abstract whale contour embedded in the waveform.
        whale = [(85, 44), (91, 40), (99, 41), (105, 38), (103, 44), (108, 48), (99, 47), (93, 50), (86, 48)]
        _line(draw, whale, _fade(CYAN_LIGHT, 0.72 * bloom), 1.0)
    elif pose.effect == "pulsar":
        bloom = math.sin(t * math.pi)
        center = (64.0, 41.0 - 4.0 * bloom)
        _ellipse(draw, center, 4.0 + 3.0 * bloom, 4.0 + 3.0 * bloom, _fade(STAR, 0.28), _fade(STAR, 0.9), 0.8)
        for i in range(12):
            a = i * 30.0 + t * 90.0
            length = 13.0 + (i % 4) * 3.2 + 8.0 * bloom
            _line(draw, [_add(center, _rot((5.0, 0.0), a)), _add(center, _rot((length, 0.0), a))], _fade(GOLD_LIGHT if i % 2 else CYAN_LIGHT, 0.75 * bloom), 0.8)
        # Branching pulsar-map lines.
        for i in range(7):
            a = 205.0 + i * 18.0
            elbow = _add(center, _rot((19.0, 0.0), a))
            end = _add(elbow, _rot((8.0 + i * 1.2, 0.0), a + (-16 if i % 2 else 13)))
            _line(draw, [center, elbow, end], _fade(STAR, 0.55 * bloom), 0.65)
    elif pose.effect == "voyager_cast":
        alpha = math.sin(t * math.pi)
        for i in range(9):
            u = i / 8.0
            x = 48.0 + (pose.record_x - 48.0) * u
            y = 62.0 + (pose.record_y - 62.0) * u - math.sin(u * math.pi) * 8.0
            _ellipse(draw, (x, y), 0.8 + u * 0.6, 0.8 + u * 0.6, _fade(GOLD_LIGHT, alpha * (0.2 + u * 0.55)), None)
        # Long interstellar message line behind the thrown disc.
        _line(draw, [(49.0, 62.0), (pose.record_x, pose.record_y)], _fade(CYAN_LIGHT, 0.32 * alpha), 0.8)
    elif pose.effect == "celebrate":
        for i in range(9):
            a = i * 40.0 + t * 70.0
            p = _add((64.0, 49.0), _rot((24.0 + 5.0 * math.sin(t * math.tau + i), 0.0), a))
            _ellipse(draw, p, 1.2, 1.2, GOLD_LIGHT if i % 2 else CYAN_LIGHT, None)
    elif pose.effect == "pale_blue_dot":
        dot = (107.0, 52.0 + 2.0 * math.sin(t * math.tau))
        _line(draw, [(86.0, 61.0), dot], _fade(STAR, 0.46), 0.7)
        _ellipse(draw, dot, 2.0, 2.0, CYAN, CYAN_LIGHT, 0.6)
        _ellipse(draw, dot, 7.0, 7.0, _fade(CYAN, 0.09), None)


def _rig_piece(key: tuple, size: Tuple[float, float], origin: Point, paint) -> tuple:
    """A piece of Anne Druid painted once (``shape_rig``): ``paint(draw)`` draws
    in frame units with its anchor at ``origin`` (frame units) on a ``size``
    (frame units) canvas. ``key`` names everything ``paint`` reads."""
    return shape_rig.piece(("anne_druid",) + key, (size[0] * SUPER, size[1] * SUPER), (origin[0] * SUPER, origin[1] * SUPER), paint)


def _put(img: Image.Image, part: tuple, at: Point, name: str, degrees: float = 0.0) -> None:
    """``part`` with its anchor at the frame point ``at``, turned ``degrees``."""
    shape_rig.place(img, part, (at[0] * SUPER, at[1] * SUPER), degrees, name)


def _bone(img: Image.Image, a: Point, b: Point, length: float, radius: float, fill: RGBA, name: str) -> None:
    """``_capsule`` from ``a`` toward ``b`` as a bone of fixed ``length``."""
    pad = radius + 2.5
    part = _rig_piece(
        ("bone", length, radius, fill), (length + 2 * pad, 2 * pad), (pad, pad),
        lambda d: _capsule(d, (pad, pad), (pad + length, pad), radius, fill),
    )
    _put(img, part, a, name, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])))


def _frame_layer(img: Image.Image, paint, name: str) -> None:
    """A per-frame effect (it changes every frame) as ONE draw: ``paint(draw)``
    paints frame-unit coordinates into a fresh canvas, placed cropped."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    paint(blending_draw(layer))
    box = layer.getbbox()
    if box is not None:
        shape_rig.place(img, (layer.crop(box), (0.0, 0.0)), (float(box[0]), float(box[1])), 0.0, name)


#: The leg bones' fixed lengths (hip to knee, knee to boot).
THIGH = 14.0
SHIN = 17.0
#: The neck bone's fixed length (neck to chest).
NECK = 16.0


def _leg_chain(hip: Point, foot: Point) -> Tuple[Point, Point]:
    """Knee and foot of a two-bone leg of fixed lengths reaching from ``hip``
    toward ``foot``, the knee bent forward (+x when upright). Out of reach, the
    leg straightens and its foot is the chain's end."""
    dx, dy = foot[0] - hip[0], foot[1] - hip[1]
    d = max(1e-6, math.hypot(dx, dy))
    base = math.atan2(dy, dx)
    if d >= THIGH + SHIN:
        return _limb(hip, THIGH, math.degrees(base)), _limb(hip, THIGH + SHIN, math.degrees(base))
    a = math.acos(max(-1.0, min(1.0, (THIGH * THIGH + d * d - SHIN * SHIN) / (2 * THIGH * d))))
    return _limb(hip, THIGH, math.degrees(base - a)), foot


def _record_piece(scale: float, front: bool) -> tuple:
    """The golden record, painted once per size at phase 0 and turned for its spin."""
    half = 16.0 * scale + 3.0
    return _rig_piece(("record", scale, front), (2 * half, 2 * half), (half, half), lambda d: _draw_record(d, (half, half), scale, 0.0, front))


#: The body piece's anchor in its own canvas (the root at ``(64, 66)``).
ROBE_ORIGIN = (40.0, 24.0)


def _paint_robe(draw: ImageDraw.ImageDraw, flare: float, sy: float) -> None:
    """Robe, mantle, leaf shoulder panels and constellation embroidery in the
    unleaned body frame (``ROBE_ORIGIN`` is the root; ``sy`` squashes)."""

    def tx(local: Point) -> Point:
        return ROBE_ORIGIN[0] + local[0], ROBE_ORIGIN[1] + local[1] * sy

    robe = [
        tx((-13.0, -15.0)),
        tx((11.0, -15.0)),
        tx((15.0 + flare * 0.18, 21.0)),
        tx((18.0 + flare, 43.0)),
        tx((3.0 + flare * 0.2, 39.0)),
        tx((-4.0 - flare * 0.1, 44.0)),
        tx((-19.0 - flare, 39.0)),
        tx((-15.0 - flare * 0.2, 18.0)),
    ]
    _poly(draw, robe, ROBE, OUTLINE, 1.15)
    _poly(draw, [tx((-13, -15)), tx((-2, -19)), tx((2, 13)), tx((-8, 42)), tx((-19 - flare, 39)), tx((-15, 15))], TEAL_DEEP, OUTLINE_SOFT, 0.8)
    _poly(draw, [tx((0, -18)), tx((11, -15)), tx((15 + flare * 0.18, 21)), tx((18 + flare, 43)), tx((5, 39)), tx((3, 8))], TEAL, OUTLINE_SOFT, 0.8)
    _line(draw, [tx((0.0, -17.0)), tx((2.0, 37.0))], GOLD, 1.1)
    _line(draw, [tx((-10.0, 34.0)), tx((3.0, 38.0)), tx((14.0 + flare * 0.5, 35.0))], _fade(TEAL_LIGHT, 0.8), 0.8)
    # Small constellation embroidery on the robe.
    stars = [tx((-5, 4)), tx((1, 10)), tx((-2, 18)), tx((6, 24))]
    for a, b in zip(stars, stars[1:]):
        _line(draw, [a, b], _fade(STAR, 0.45), 0.5)
    for p in stars:
        _ellipse(draw, p, 0.9, 0.9, _fade(STAR, 0.78), None)
    # Leaf-shaped shoulder panels.
    _leaf(draw, tx((-11.5, -16.0)), 12.0, 5.6, 116.0, MOSS, OUTLINE)
    _leaf(draw, tx((10.0, -16.0)), 12.0, 5.6, 62.0, MOSS_LIGHT, OUTLINE)


def _paint_hand(draw: ImageDraw.ImageDraw, hand: Point) -> None:
    _ellipse(draw, hand, 3.5, 3.0, SKIN_LIGHT, OUTLINE, 0.8)
    for fi in range(3):
        _line(draw, [(hand[0] + 1.5, hand[1] - 1.1 + fi * 1.0), (hand[0] + 4.2, hand[1] - 1.7 + fi * 1.15)], SKIN_SHADE, 0.55)


def _paint_head(draw: ImageDraw.ImageDraw, head: Point, eye_closed: bool, mouth_open: float) -> None:
    """Hair crescent, three-quarter face and silver streaks around ``head``."""
    # Hair back mass creates the crescent silhouette.
    _ellipse(draw, (head[0] - 2.5, head[1] + 1.5), 17.5, 19.0, HAIR_DEEP, OUTLINE, 1.0)
    for offx, offy, rr, col in [
        (-13, 2, 7.5, HAIR), (-10, -9, 7.0, HAIR_MID), (-2, -14, 7.5, HAIR),
        (8, -11, 7.0, HAIR_MID), (13, -1, 7.5, HAIR), (10, 9, 7.0, HAIR_DEEP),
        (-9, 11, 7.5, HAIR_MID),
    ]:
        _ellipse(draw, (head[0] + offx, head[1] + offy), rr, rr * 1.08, col, OUTLINE_SOFT, 0.45)
    # Face is three-quarter-facing right.
    _ellipse(draw, (head[0] + 2.5, head[1]), 10.8, 13.2, SKIN, OUTLINE, 1.0)
    _ellipse(draw, (head[0] + 4.0, head[1] - 2.2), 9.5, 10.5, SKIN_LIGHT, None)
    nose = (head[0] + 12.2, head[1] + 0.2)
    _poly(draw, [(head[0] + 8.5, head[1] - 2.0), nose, (head[0] + 8.8, head[1] + 2.4)], SKIN, OUTLINE_SOFT, 0.6)
    eye_y = head[1] - 3.4
    if eye_closed:
        _line(draw, [(head[0] + 3.4, eye_y), (head[0] + 7.4, eye_y + 0.5)], EYE, 0.9)
    else:
        _ellipse(draw, (head[0] + 5.5, eye_y), 1.3, 1.0, STAR, EYE, 0.55)
        _ellipse(draw, (head[0] + 5.9, eye_y), 0.48, 0.6, EYE, None)
    _line(draw, [(head[0] + 2.8, eye_y - 2.5), (head[0] + 7.6, eye_y - 2.9)], HAIR_DEEP, 0.9)
    mouth_y = head[1] + 6.2
    if mouth_open > 0.05:
        _ellipse(draw, (head[0] + 7.0, mouth_y), 2.3, 0.9 + mouth_open * 1.3, MOUTH, OUTLINE_SOFT, 0.45)
    else:
        _arc(draw, (head[0] + 7.0, mouth_y - 0.5), 3.2, 2.0, 15, 150, MOUTH, 0.85)

    # Silver star streaks keep the hair readable at gameplay scale.
    for idx, (a, b) in enumerate([
        ((head[0] - 12.0, head[1] - 8.0), (head[0] - 8.0, head[1] + 9.0)),
        ((head[0] - 4.0, head[1] - 14.0), (head[0] - 1.0, head[1] + 8.0)),
        ((head[0] + 8.0, head[1] - 11.0), (head[0] + 11.0, head[1] + 5.0)),
    ]):
        _line(draw, [a, b], _fade(HAIR_SILVER, 0.72 - idx * 0.08), 1.0)


def _draw_character(img: Image.Image, pose: Pose) -> None:
    """Anne Druid as a rig. Body coordinates are authored in local character
    space and transformed by a small whole-body lean (``tx``); the robe, strap
    and record are pieces turned with it, limbs are fixed-length bones, and the
    head, hands and boots are pieces that stay upright."""
    root = (64.0 + pose.x, 66.0 + pose.y)
    scale_y = round(1.0 - pose.squash, 2)

    def tx(local: Point) -> Point:
        rotated = _rot((local[0], local[1] * scale_y), pose.lean)
        return root[0] + rotated[0], root[1] + rotated[1]

    hip = tx((0.0, 19.0))
    chest = tx((0.0, -5.0))
    neck = tx((1.0, -21.0))
    head = tx((2.0, -34.0))

    # Legs and boots, behind robe.
    stride = pose.stride
    for side, foot, fills in (
        ("left", tx((-7.0 - stride, 47.0)), (ROBE_DARK, ROBE)),
        ("right", tx((7.0 + stride, 47.0)), (ROBE_DARK, ROBE_LIGHT)),
    ):
        knee, foot = _leg_chain(hip, foot)
        _bone(img, hip, knee, THIGH, 3.6, fills[0], f"{side}_thigh")
        _bone(img, knee, foot, SHIN, 3.3, fills[1], f"{side}_shin")
        if side == "left":
            left_foot = foot
        else:
            right_foot = foot
    for side, foot, flip in (("left", left_foot, -1), ("right", right_foot, 1)):
        boot = _rig_piece(("boot", flip), (22, 10), (11, 4.5), lambda d, flip=flip: _capsule(d, (11, 4.5), (11 + 6.0 * flip, 5.0), 3.0, BOOT))
        _put(img, boot, foot, f"{side}_boot")

    # Record behind body unless an action brings it forward.
    if not pose.record_front:
        record_scale = round(pose.record_scale * 50) / 50
        record_local = (pose.record_x - 64.0, pose.record_y - 66.0)
        _put(img, _record_piece(record_scale, False), tx(record_local), "record", pose.effect_phase * 20.0)
        strap = _rig_piece(("strap", scale_y), (30, 50), (20, 24), lambda d: _line(d, [(13.0, 24.0 - 15.0 * scale_y), (7.0, 24.0 + 8.0 * scale_y)], COPPER, 1.3))
        _put(img, strap, root, "strap", pose.lean)

    # Robe, asymmetric mantle, shoulder leaves and embroidery: one piece per flare.
    flare = round(pose.robe_flare)
    robe = _rig_piece(("robe", flare, scale_y), (80, 72), ROBE_ORIGIN, lambda d: _paint_robe(d, flare, scale_y))
    _put(img, robe, root, "robe", pose.lean)

    # Arms.
    shoulder_l = tx((-10.0, -13.0))
    shoulder_r = tx((10.0, -13.0))
    elbow_l = _limb(shoulder_l, 15.0, pose.arm_l + pose.lean)
    elbow_r = _limb(shoulder_r, 15.0, pose.arm_r + pose.lean)
    hand_l = _limb(elbow_l, 14.0, pose.fore_l + pose.lean)
    hand_r = _limb(elbow_r, 14.0, pose.fore_r + pose.lean)
    _bone(img, shoulder_l, elbow_l, 15.0, 3.8, TEAL_DEEP, "left_upper_arm")
    _bone(img, elbow_l, hand_l, 14.0, 3.1, SKIN, "left_forearm")
    _bone(img, shoulder_r, elbow_r, 15.0, 3.8, TEAL_LIGHT, "right_upper_arm")
    _bone(img, elbow_r, hand_r, 14.0, 3.1, SKIN_LIGHT, "right_forearm")
    hand_part = _rig_piece(("hand",), (12, 9), (5, 4.5), lambda d: _paint_hand(d, (5, 4.5)))
    _put(img, hand_part, hand_l, "left_hand")
    _put(img, hand_part, hand_r, "right_hand")

    # Neck and face.
    _bone(img, neck, chest, NECK, 4.0, SKIN, "neck")
    mouth = round(pose.mouth_open * 10) / 10
    head_part = _rig_piece(("head", pose.eye_closed, mouth), (48, 48), (24, 25), lambda d: _paint_head(d, (24, 25), pose.eye_closed, mouth))
    _put(img, head_part, head, "head")

    if pose.record_front:
        # The thrown-record action uses absolute frame coordinates so its arc
        # can travel independently of the body transform.
        center = (pose.record_x, pose.record_y) if pose.effect == "voyager_cast" else tx((pose.record_x - 64.0, pose.record_y - 66.0))
        record_scale = round(pose.record_scale * 50) / 50
        _put(img, _record_piece(record_scale, True), center, "record_front", pose.effect_phase * 20.0)


def render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    pose = _pose(anim, frame_idx, nframes)
    image = Image.new("RGBA", (FRAME_W * SUPER, FRAME_H * SUPER), (0, 0, 0, 0))
    # The effects change every frame: each layer is one draw.
    _frame_layer(image, lambda d: _draw_effects_behind(d, pose), "effects_behind")
    _draw_character(image, pose)
    _frame_layer(image, lambda d: _draw_effects_front(d, pose), "effects_front")
    if pose.alpha < 0.999:
        image = rigdoc.faded_canvas(image, max(0.0, pose.alpha))
    return rigdoc.downsampled_canvas(image, (FRAME_W, FRAME_H), Image.Resampling.LANCZOS)


def _render_native_portrait(expression: str = "default", phase: float = 0.0) -> Image.Image:
    scale = 3
    size = 256
    image = Image.new("RGBA", (size * scale, size * scale), (0, 0, 0, 0))
    draw = blending_draw(image)

    # Native portrait geometry deliberately reuses the palette and motifs but
    # not a scaled gameplay frame.
    cx, cy = 127.0, 103.0
    def p(point: Point) -> Tuple[int, int]:
        return int(point[0] * scale), int(point[1] * scale)
    def ell(center: Point, rx: float, ry: float, fill: RGBA, outline: RGBA | None = None, width: float = 1.0) -> None:
        x, y = center
        draw.ellipse(p((x-rx, y-ry)) + p((x+rx, y+ry)), fill=fill, outline=outline, width=max(1, int(width*scale)))
    def ln(points: Sequence[Point], fill: RGBA, width: float = 1.0) -> None:
        draw.line([p(q) for q in points], fill=fill, width=max(1, int(width*scale)), joint="curve")

    # Robe shoulders and record.
    draw.polygon([p((38, 256)), p((53, 173)), p((92, 145)), p((160, 145)), p((205, 178)), p((224, 256))], fill=ROBE)
    draw.polygon([p((38, 256)), p((53, 173)), p((101, 146)), p((111, 256))], fill=TEAL_DEEP)
    draw.polygon([p((142, 147)), p((205, 178)), p((224, 256)), p((139, 256))], fill=TEAL)
    ell((65, 193), 38, 38, GOLD_DEEP, GOLD_LIGHT, 2.2)
    for rr in (12, 20, 28, 34):
        draw.arc(p((65-rr,193-rr))+p((65+rr,193+rr)), start=10+phase*20, end=335+phase*20, fill=GOLD_LIGHT, width=max(1,int(0.9*scale)))
    ell((65, 193), 8, 8, COPPER, GOLD_LIGHT, 1.2)

    # Hair mass and face.
    ell((cx-8, cy+5), 66, 77, HAIR_DEEP, OUTLINE, 2.0)
    for ox, oy, rx, ry, col in [
        (-48, 3, 29, 38, HAIR), (-39, -39, 28, 34, HAIR_MID), (-5, -58, 34, 28, HAIR),
        (35, -46, 29, 34, HAIR_MID), (51, -5, 27, 38, HAIR), (38, 39, 31, 39, HAIR_DEEP),
        (-38, 43, 32, 38, HAIR_MID),
    ]:
        ell((cx+ox, cy+oy), rx, ry, col, OUTLINE_SOFT, 1.0)
    ell((cx+11, cy), 39, 49, SKIN, OUTLINE, 2.0)
    ell((cx+15, cy-7), 34, 38, SKIN_LIGHT, None)
    draw.polygon([p((cx+31, cy-9)), p((cx+48, cy+2)), p((cx+33, cy+9))], fill=SKIN, outline=OUTLINE_SOFT)

    eye_closed = expression in {"listening", "whale_song"}
    mouth_open = expression in {"speaking", "wonder", "whale_song"}
    if eye_closed:
        ln([(cx+11, cy-15), (cx+27, cy-13)], EYE, 2.0)
    else:
        ell((cx+20, cy-15), 4.4, 3.2, STAR, EYE, 1.1)
        ell((cx+22, cy-15), 1.4, 2.0, EYE, None)
    ln([(cx+9, cy-24), (cx+29, cy-25)], HAIR_DEEP, 2.0)
    if mouth_open:
        ell((cx+28, cy+25), 7.2, 4.0 if expression != "wonder" else 6.5, MOUTH, OUTLINE_SOFT, 1.0)
    else:
        draw.arc(p((cx+18,cy+16))+p((cx+38,cy+30)), start=10, end=145, fill=MOUTH, width=max(1,int(1.8*scale)))

    # Silver streaks and collar.
    for a, b in [((cx-39, cy-39), (cx-28, cy+32)), ((cx-8, cy-58), (cx-2, cy+29)), ((cx+37, cy-40), (cx+43, cy+19))]:
        ln([a, b], _fade(HAIR_SILVER, 0.78), 2.4)
    draw.polygon([p((99, 148)), p((126, 164)), p((153, 147)), p((142, 184)), p((112, 184))], fill=MOSS, outline=OUTLINE)
    ln([(126, 164), (126, 230)], GOLD, 2.4)

    # Expression-specific cosmic accents.
    if expression == "wonder":
        for i in range(8):
            a = i * 45.0 + phase * 50.0
            q = _add((182.0, 57.0), _rot((28.0, 0.0), a))
            ell(q, 2.2, 2.2, GOLD_LIGHT if i % 2 else CYAN_LIGHT, None)
    elif expression == "whale_song":
        for i in range(4):
            r = 13 + i * 14 + phase * 9
            draw.arc(p((168-r,85-r*0.7))+p((168+r,85+r*0.7)), start=-55, end=55, fill=_fade(CYAN_LIGHT, 0.85-i*0.14), width=max(1,int(2.2*scale)))
    elif expression == "pale_blue_dot":
        ell((202, 65), 4.0, 4.0, CYAN, CYAN_LIGHT, 1.2)
        ell((202, 65), 18.0, 18.0, _fade(CYAN, 0.08), None)
        ln([(165, 105), (202, 65)], _fade(STAR, 0.58), 1.1)
    elif expression == "speaking":
        points = [(176, 60), (190, 51), (207, 62), (199, 78), (216, 87)]
        for a, b in zip(points, points[1:]):
            ln([a, b], _fade(CYAN_LIGHT, 0.56), 1.2)
        for q in points:
            ell(q, 2.1, 2.1, STAR, None)

    return image.resize(PORTRAIT_SIZE, Image.Resampling.LANCZOS)


def render_portraits(out_dir: Path, **opts) -> List[Path]:
    del opts
    clips = {
        "default": PortraitClip.still(_render_native_portrait("default")),
        "speaking": PortraitClip(tuple(_render_native_portrait("speaking", i / 8.0) for i in range(8)), duration_ms=108, looping=True),
        "wonder": PortraitClip(tuple(_render_native_portrait("wonder", i / 8.0) for i in range(8)), duration_ms=118, looping=True),
        "listening": PortraitClip.still(_render_native_portrait("listening")),
        "whale_song": PortraitClip(tuple(_render_native_portrait("whale_song", i / 8.0) for i in range(8)), duration_ms=112, looping=True),
        "pale_blue_dot": PortraitClip.still(_render_native_portrait("pale_blue_dot")),
    }
    return write_portrait_sheet(TARGET_NAME, clips, Path(out_dir))


def _body_metrics_override(fw: int, fh: int):
    return {
        "body_pixel_bbox": {"x": int(fw * 0.25), "y": int(fh * 0.08), "w": int(fw * 0.55), "h": int(fh * 0.84)},
        "feet_pixel": {"x": fw * 0.5, "y": fh * 0.92},
        "feet_anchor_norm": {"x": 0.0, "y": round(0.5 - 0.92, 6)},
    }


def render(out_dir: Path, **opts) -> List[Path]:
    del opts
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
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
        attack_hitboxes={
            "golden_record_guard": {"bbox": {"x": 69, "y": 38, "w": 55, "h": 59}},
            "whale_song": {"bbox": {"x": 76, "y": 26, "w": 51, "h": 53}},
            "pulsar_beacon": {"bbox": {"x": 28, "y": 2, "w": 72, "h": 70}},
            "cosmic_garden": {"bbox": {"x": 25, "y": 49, "w": 79, "h": 73}},
            "voyager_cast": {"bbox": {"x": 75, "y": 20, "w": 53, "h": 71}},
        },
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    parts = publish_rig_flipbook(TARGET_NAME, ROWS, render_frame, outputs, frame_transform, Path(out_dir))
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())


def render_canonical(out_dir: Path, **opts) -> Path:
    del opts
    return write_canonical(TARGET_NAME, ROWS, render_frame, Path(out_dir), frame_size=(FRAME_W, FRAME_H))


__all__ = [
    "ACTOR_METADATA",
    "AUTHORING_DESCRIPTION",
    "TARGET_NAME",
    "render",
    "render_canonical",
    "render_frame",
    "render_portraits",
]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out_dir", nargs="?", type=Path, default=Path("generated") / TARGET_NAME)
    args = parser.parse_args()
    for path in render(args.out_dir):
        print(path)
    for path in render_portraits(args.out_dir):
        print(path)
