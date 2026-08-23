"""Procedural full-action renderer for Richard Duckling, the Selfish Meme.

Richard Duckling is an affectionate satirical transformation of evolutionary
biologist and science communicator Richard Dawkins into an anthropomorphic
public-intellectual duck.  He is obsessed with one grievance: he helped give
"meme" its name, yet the culture has produced almost no first-rate duck memes.
His combat language makes that grievance literal.  Meme tiles reproduce,
mutate, compete for attention, and occasionally hatch into unruly ducklings.

The sprite is deliberately not a literal portrait.  It combines a white
feather crest, sharp spectacles, a tweed lecture vest, bow tie, field notebook,
and a permanently skeptical bill.  The resulting silhouette reads as a fussy
scholar-duck even without dialogue.  Everything is rendered with supersampled
Pillow geometry and publishes through Ambition's normal character target
contract, including native portraits and behind-the-scenes authoring notes.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, replace
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw

from ...authoring.portrait import PortraitClip, write_portrait_sheet
from ...authoring.sheet_build import build_sheet, write_canonical
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "richard_duckling"
FRAME_W = 128
FRAME_H = 128
SUPER = 4
PORTRAIT_SIZE = (192, 192)

AUTHORING_DESCRIPTION = {
    "parody_of": "Richard Dawkins",
    "character_name": "Richard Duckling",
    "concept": (
        "An anthropomorphic public-intellectual duck who helped popularize the word "
        "meme and now cannot understand why internet culture has failed to produce "
        "a respectable canon of duck memes. He responds by breeding, selecting, and "
        "lecturing his own memes into existence."
    ),
    "name_origin": (
        "Richard Duckling turns Richard Dawkins into a scholarly duck while the title "
        "The Selfish Meme folds together The Selfish Gene, the coined term meme, and "
        "the character's conviction that successful jokes behave like replicators."
    ),
    "visual_inspiration": [
        "A white feather crest and narrow spectacles create a recognizable skeptical-scholar silhouette without attempting a literal portrait.",
        "A green tweed vest, burgundy bow tie, notebook, and lecture pointer evoke an old-fashioned public lecturer.",
        "Small square meme cards use a simple duck-head pictogram so they remain readable at gameplay scale.",
        "Replicating cards mutate in color and expression before hatching into tiny ducklings.",
        "The bill, webbed feet, tail, and wing gestures should remain unmistakably avian even when he is posed like a professor.",
    ],
    "gameplay_inspiration": [
        "selfish_meme launches a meme card that tries to reproduce after reaching the opponent.",
        "meme_mutation creates several visibly different variants and favors the most attention-grabbing one.",
        "duckling_swarm converts successful meme replication into a low-running flock of tiny ducklings.",
        "honk_rebuttal is a broad close-range sound wave used to interrupt criticism.",
        "missing_meme is a comic search animation in which he inspects the battlefield for a good duck meme and finds none.",
    ],
    "gameplay_description": (
        "A mobile midrange summoner and disruption fighter. Richard seeds meme cards, "
        "mutates them into alternate variants, and turns surviving cards into a ground-level "
        "duckling swarm. His honk is a fast defensive cone, while his notebook block rewards "
        "timing. The intended rhythm is seed, observe, select, and replicate rather than raw damage."
    ),
    "suggested_barks": {
        "idle": [
            "I practically invented memes. Where are the ducks?",
            "No, that is a goose meme. Entirely different clade.",
            "The cultural environment remains inexplicably duck-poor.",
        ],
        "combat": [
            "Replicate this!",
            "Selection will decide!",
            "A superior template has emerged.",
            "Honk is an argument.",
        ],
        "on_hit": [
            "That criticism lacked peer review!",
            "An adverse selection event!",
        ],
        "victory": [
            "At last: a viable duck meme.",
            "The selfish meme propagates.",
        ],
    },
    "fallback_dialogue": [
        "I named the thing, you know. One might expect at least one excellent duck template by now.",
        "A meme is not merely an image with text. Unfortunately, most images with text have not heard this.",
        "That one is a goose. The distinction is elementary and apparently beyond the internet.",
        "I am applying artificial selection. Natural selection has had decades and produced nothing usable.",
        "The ducklings are not followers. They are independent replicators with suspiciously similar opinions.",
    ],
    "boundaries": [
        "Treat the character as a fictional satirical homage, not a literal likeness or claim about the real person's private behavior.",
        "Aim the joke at public ideas, argumentative style, meme history, and duck taxonomy rather than protected personal traits.",
        "Keep the character intellectually formidable even when he is pompous or exasperated.",
        "Do not confuse ducks with geese; the character would object at length.",
    ],
}

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 142),
    ("walk", 8, 102),
    ("run", 8, 80),
    ("crouch", 6, 96),
    ("jump", 6, 88),
    ("fall", 6, 92),
    ("land_hard", 6, 86),
    ("dash", 7, 64),
    ("roll", 8, 64),
    ("swim", 8, 98),
    ("block", 6, 82),
    ("hit", 5, 84),
    ("death", 8, 108),
    ("talk", 8, 104),
    ("interact", 8, 94),
    ("honk_rebuttal", 8, 70),
    ("selfish_meme", 10, 72),
    ("meme_mutation", 10, 78),
    ("duckling_swarm", 12, 68),
    ("missing_meme", 10, 92),
    ("lecture", 10, 90),
    ("celebrate", 8, 88),
    ("taunt", 8, 96),
]

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_richard_duckling",
        "display_name": "Richard Duckling, the Selfish Meme",
    },
    "authoring_description": AUTHORING_DESCRIPTION,
    "dialogue_hints": {
        "suggested_barks": [
            'That criticism lacked peer review!',
            'An adverse selection event!',
            'I practically invented memes. Where are the ducks?',
            'No, that is a goose meme. Entirely different clade.',
        ],
        "fallback_dialogue": [
            'I named the thing, you know. One might expect at least one excellent duck template by now.',
            'A meme is not merely an image with text. Unfortunately, most images with text have not heard this.',
            'I am applying artificial selection. Natural selection has had decades and produced nothing usable.',
            'The ducklings are not followers. They are independent replicators with suspiciously similar opinions.',
        ],
    },
    "body": {
        "body_plan": "AvianBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": [
            "story",
            "bird",
            "scientist",
            "science_communicator",
            "memeticist",
            "summoner",
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
                "center": {"x": 68.0, "y": 34.0},
                "size": {"w": 42.0, "h": 38.0},
                "source_size": {"w": 128.0, "h": 128.0},
            }
        },
    },
    "tags": [
        "story",
        "bird",
        "scientist",
        "science_communicator",
        "memeticist",
        "summoner",
        "playable_candidate",
    ],
    "sockets": {
        "head": {"source": "explicit.richard_duckling", "point": {"x": 68.0, "y": 34.0}},
        "chest": {"source": "explicit.richard_duckling", "point": {"x": 64.0, "y": 67.0}},
        "wing_l": {"source": "explicit.richard_duckling", "point": {"x": 48.0, "y": 68.0}},
        "wing_r": {"source": "explicit.richard_duckling", "point": {"x": 82.0, "y": 66.0}},
        "bill": {"source": "explicit.richard_duckling", "point": {"x": 91.0, "y": 41.0}},
        "speech_bubble": {"source": "explicit.richard_duckling", "point": {"x": 68.0, "y": 5.0}},
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "traversal.jump": {"animation": "jump", "events": []},
        "traversal.fall": {"animation": "fall", "events": []},
        "traversal.swim": {"animation": "swim", "events": []},
        "action.melee.primary": {"animation": "honk_rebuttal", "events": []},
        "action.ranged.primary": {"animation": "selfish_meme", "events": []},
        "action.special.primary": {"animation": "meme_mutation", "events": []},
        "action.special.secondary": {"animation": "duckling_swarm", "events": []},
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
                "revision_id": "richard_duckling_concept_direction",
                "creator_kind": "human",
                "creator": "Jon Crall",
                "contribution": "named_richard_duckling_the_selfish_meme_and_defined_the_missing_duck_meme_grievance",
            },
            {
                "revision_id": "richard_duckling_procedural_sprite_v1",
                "creator_kind": "model",
                "creator": "gpt-5.6-thinking",
                "parent_revision_id": "richard_duckling_concept_direction",
                "contribution": "procedural_full_action_sprite_native_portraits_authoring_notes_barks_and_gameplay_description",
            },
        ],
    },
}

# Palette: warm duck plumage, academic greens and burgundy, and high-chroma
# meme cards that remain readable against both light and dark stages.
OUTLINE = (24, 25, 27, 255)
OUTLINE_SOFT = (66, 61, 56, 255)
FEATHER = (236, 228, 202, 255)
FEATHER_LIGHT = (255, 250, 231, 255)
FEATHER_SHADE = (188, 177, 151, 255)
CREST = (250, 246, 224, 255)
BILL = (225, 145, 39, 255)
BILL_LIGHT = (249, 184, 63, 255)
BILL_DARK = (160, 83, 30, 255)
EYE = (29, 27, 25, 255)
VEST = (57, 86, 66, 255)
VEST_LIGHT = (88, 119, 84, 255)
VEST_DARK = (37, 58, 46, 255)
TWEED = (137, 126, 88, 255)
SHIRT = (230, 221, 195, 255)
BURGUNDY = (126, 38, 49, 255)
BURGUNDY_LIGHT = (183, 67, 76, 255)
LEATHER = (80, 55, 40, 255)
PAPER = (239, 226, 183, 255)
INK = (47, 46, 44, 255)
GLASS = (174, 226, 229, 145)
CYAN = (65, 194, 210, 255)
BLUE = (74, 118, 210, 255)
MAGENTA = (197, 72, 143, 255)
LIME = (139, 193, 74, 255)
YELLOW = (243, 202, 75, 255)
WHITE = (255, 255, 255, 255)
RED = (226, 76, 62, 255)


def _fade(color: RGBA, alpha: float) -> RGBA:
    return color[:3] + (max(0, min(255, int(round(color[3] * alpha)))),)


def _p(point: Point) -> Tuple[int, int]:
    return int(round(point[0] * SUPER)), int(round(point[1] * SUPER))


def _line(draw: ImageDraw.ImageDraw, points: Sequence[Point], fill: RGBA, width: float = 1.0) -> None:
    draw.line([_p(q) for q in points], fill=fill, width=max(1, int(round(width * SUPER))), joint="curve")


def _ellipse(
    draw: ImageDraw.ImageDraw,
    center: Point,
    rx: float,
    ry: float,
    fill: RGBA,
    outline: RGBA | None = None,
    width: float = 1.0,
) -> None:
    x, y = center
    draw.ellipse(
        _p((x - rx, y - ry)) + _p((x + rx, y + ry)),
        fill=fill,
        outline=outline,
        width=max(1, int(round(width * SUPER))) if outline else 1,
    )


def _poly(
    draw: ImageDraw.ImageDraw,
    points: Sequence[Point],
    fill: RGBA,
    outline: RGBA | None = None,
    width: float = 1.0,
) -> None:
    pts = [_p(q) for q in points]
    draw.polygon(pts, fill=fill)
    if outline:
        draw.line(pts + [pts[0]], fill=outline, width=max(1, int(round(width * SUPER))), joint="curve")


def _arc(
    draw: ImageDraw.ImageDraw,
    center: Point,
    rx: float,
    ry: float,
    start: float,
    end: float,
    fill: RGBA,
    width: float = 1.0,
) -> None:
    x, y = center
    draw.arc(
        _p((x - rx, y - ry)) + _p((x + rx, y + ry)),
        start=start,
        end=end,
        fill=fill,
        width=max(1, int(round(width * SUPER))),
    )


def _rot(point: Point, angle_deg: float) -> Point:
    r = math.radians(angle_deg)
    c, s = math.cos(r), math.sin(r)
    return point[0] * c - point[1] * s, point[0] * s + point[1] * c


def _add(a: Point, b: Point) -> Point:
    return a[0] + b[0], a[1] + b[1]


def _capsule(draw: ImageDraw.ImageDraw, a: Point, b: Point, radius: float, fill: RGBA, outline: RGBA = OUTLINE) -> None:
    _line(draw, [a, b], outline, radius * 2.0 + 1.4)
    _line(draw, [a, b], fill, radius * 2.0)
    _ellipse(draw, a, radius, radius, fill, outline, 0.7)
    _ellipse(draw, b, radius, radius, fill, outline, 0.7)


@dataclass(frozen=True)
class Pose:
    x: float = 0.0
    y: float = 0.0
    lean: float = 0.0
    squash: float = 0.0
    stride: float = 0.0
    knee: float = 0.0
    wing_l: float = 118.0
    wing_r: float = 42.0
    head_tilt: float = 0.0
    beak_open: float = 0.0
    eye_closed: bool = False
    glasses_tilt: float = 0.0
    book_front: bool = False
    book_angle: float = -8.0
    pointer: bool = False
    effect: str = ""
    effect_phase: float = 0.0
    alpha: float = 1.0


def _pose(anim: str, frame_idx: int, nframes: int) -> Pose:
    t = frame_idx / max(1, nframes)
    wave = math.sin(t * math.tau)
    wave2 = math.sin(t * math.tau * 2.0)
    pose = Pose(y=-0.7 * wave, head_tilt=1.5 * wave, glasses_tilt=0.5 * wave)

    if anim == "walk":
        pose = replace(pose, x=0.7 * wave, y=-1.0 * abs(wave), stride=8.0 * wave, knee=3.0 * abs(wave), wing_l=118 - 18 * wave, wing_r=42 + 18 * wave)
    elif anim == "run":
        pose = replace(pose, x=1.4 * wave, y=-2.2 * abs(wave), lean=13.0, stride=13.0 * wave, knee=5.0 * abs(wave), wing_l=150 - 34 * wave, wing_r=10 + 34 * wave, effect="speed_feathers", effect_phase=t)
    elif anim == "crouch":
        pose = replace(pose, y=10.0 + wave, squash=0.18, stride=3.0, knee=5.0, wing_l=140, wing_r=22, head_tilt=-4.0)
    elif anim == "jump":
        lift = math.sin(t * math.pi)
        pose = replace(pose, y=-7.0 * lift, stride=7.0 - 13.0 * t, knee=5.0, wing_l=218 - 30 * lift, wing_r=-58 + 30 * lift)
    elif anim == "fall":
        pose = replace(pose, y=-2.0 + 3.0 * t, stride=-4.0, knee=6.0, wing_l=188 + 10 * wave, wing_r=-28 - 10 * wave)
    elif anim == "land_hard":
        impact = max(0.0, 1.0 - abs(t - 0.42) * 4.0)
        pose = replace(pose, y=9.0 * impact, squash=0.20 * impact, stride=9.0, knee=6.0, wing_l=154, wing_r=8, effect="impact_feathers", effect_phase=t)
    elif anim == "dash":
        pose = replace(pose, x=5.0 * t, y=-2.0, lean=21.0, stride=11.0 * wave, wing_l=152, wing_r=6, effect="speed_feathers", effect_phase=t)
    elif anim == "roll":
        pose = replace(pose, y=7.0, lean=t * 360.0, squash=0.25, stride=0.0, wing_l=150, wing_r=12, effect="roll_memes", effect_phase=t)
    elif anim == "swim":
        pose = replace(pose, y=7.0 + 1.5 * wave, squash=0.08, stride=6.0 * wave2, wing_l=178 + 30 * wave, wing_r=-18 - 30 * wave, effect="water", effect_phase=t)
    elif anim == "block":
        pulse = math.sin(t * math.pi)
        pose = replace(pose, y=1.0, lean=-4.0, wing_l=32, wing_r=18, book_front=True, book_angle=-5.0 + 4.0 * pulse, effect="book_block", effect_phase=t)
    elif anim == "hit":
        kick = math.sin(t * math.pi)
        pose = replace(pose, x=-5.0 * kick, y=-2.0 * kick, lean=-16.0 * kick, wing_l=166, wing_r=-6, beak_open=0.7, eye_closed=True, glasses_tilt=10.0 * kick, effect="hit", effect_phase=t)
    elif anim == "death":
        ease = min(1.0, t * 1.35)
        pose = replace(pose, x=-4.0 * ease, y=15.0 * ease, lean=-84.0 * ease, wing_l=152, wing_r=4, beak_open=0.25, eye_closed=True, glasses_tilt=22.0 * ease, alpha=1.0 - max(0.0, t - 0.74) * 2.1, effect="fallen_memes", effect_phase=t)
    elif anim == "talk":
        pose = replace(pose, wing_l=112 + 10 * wave, wing_r=26 - 18 * wave, beak_open=0.25 + 0.5 * max(0.0, wave2), head_tilt=3.0 * wave)
    elif anim == "interact":
        pose = replace(pose, wing_l=118, wing_r=10 - 8 * math.sin(t * math.pi), book_front=True, book_angle=-12.0, head_tilt=-4.0)
    elif anim == "honk_rebuttal":
        blast = math.sin(t * math.pi)
        pose = replace(pose, x=-2.0 * blast, lean=-8.0 * blast, wing_l=148, wing_r=12, beak_open=1.0, eye_closed=t > 0.18, effect="honk", effect_phase=t)
    elif anim == "selfish_meme":
        cast = math.sin(t * math.pi)
        pose = replace(pose, lean=9.0 * cast, wing_l=132, wing_r=8 - 22 * cast, book_front=True, book_angle=-15.0 + 8.0 * cast, effect="selfish_meme", effect_phase=t)
    elif anim == "meme_mutation":
        bloom = math.sin(t * math.pi)
        pose = replace(pose, y=-2.0 * bloom, wing_l=210, wing_r=-50, eye_closed=t > 0.2, book_front=True, book_angle=0.0, effect="mutation", effect_phase=t)
    elif anim == "duckling_swarm":
        pose = replace(pose, y=4.0, squash=0.06, wing_l=148 - 12 * wave, wing_r=12 + 12 * wave, beak_open=0.5, effect="duckling_swarm", effect_phase=t)
    elif anim == "missing_meme":
        pose = replace(pose, wing_l=122, wing_r=28 - 16 * wave, head_tilt=-8.0 + 5.0 * wave, glasses_tilt=-4.0, effect="missing_meme", effect_phase=t)
    elif anim == "lecture":
        pose = replace(pose, wing_l=130, wing_r=5 + 12 * wave, beak_open=0.3 + 0.4 * max(0.0, wave2), pointer=True, effect="lecture", effect_phase=t)
    elif anim == "celebrate":
        hop = max(0.0, math.sin(t * math.tau))
        pose = replace(pose, y=-5.0 * hop, wing_l=222 + 7 * wave, wing_r=-62 - 7 * wave, beak_open=0.8, effect="viable_meme", effect_phase=t)
    elif anim == "taunt":
        pose = replace(pose, wing_l=118, wing_r=24, head_tilt=-7.0, beak_open=0.18, effect="goose_correction", effect_phase=t)

    return pose


def _draw_meme_card(draw: ImageDraw.ImageDraw, center: Point, scale: float = 1.0, tint: RGBA = CYAN, expression: int = 0, angle: float = 0.0) -> None:
    w, h = 13.0 * scale, 15.0 * scale
    card = Image.new("RGBA", (int((w + 8) * SUPER), int((h + 8) * SUPER)), (0, 0, 0, 0))
    cd = blending_draw(card)
    ox, oy = (w + 8) / 2.0, (h + 8) / 2.0
    _poly(cd, [(ox-w/2, oy-h/2), (ox+w/2, oy-h/2), (ox+w/2, oy+h/2), (ox-w/2, oy+h/2)], PAPER, OUTLINE, 0.9)
    _poly(cd, [(ox-w/2+1.2, oy-h/2+1.2), (ox+w/2-1.2, oy-h/2+1.2), (ox+w/2-1.2, oy-1.0), (ox-w/2+1.2, oy-1.0)], tint, None)
    # Tiny duck-head pictogram.
    _ellipse(cd, (ox-1.0, oy-3.7), 2.8, 2.5, FEATHER_LIGHT, OUTLINE, 0.45)
    _poly(cd, [(ox+1.2, oy-3.8), (ox+4.3, oy-2.8), (ox+1.2, oy-1.7)], BILL, OUTLINE, 0.35)
    if expression == 0:
        _ellipse(cd, (ox-0.2, oy-4.0), 0.45, 0.45, EYE, None)
    elif expression == 1:
        _line(cd, [(ox-1.0, oy-4.0), (ox+0.5, oy-3.6)], EYE, 0.45)
    else:
        _line(cd, [(ox-1.1, oy-4.3), (ox+0.7, oy-3.7)], EYE, 0.5)
        _line(cd, [(ox-0.6, oy-2.5), (ox+1.0, oy-2.9)], RED, 0.45)
    _line(cd, [(ox-w/2+2, oy+2), (ox+w/2-2, oy+2)], INK, 0.45)
    _line(cd, [(ox-w/2+2, oy+4.3), (ox+w/2-3.5, oy+4.3)], INK, 0.45)
    if abs(angle) > 0.01:
        card = card.rotate(-angle, resample=Image.Resampling.BICUBIC, expand=True)
    draw._image.alpha_composite(card, (int((center[0] - card.width / SUPER / 2) * SUPER), int((center[1] - card.height / SUPER / 2) * SUPER)))


def _draw_duckling(draw: ImageDraw.ImageDraw, center: Point, scale: float = 1.0, phase: float = 0.0) -> None:
    x, y = center
    bob = math.sin(phase * math.tau) * 0.7
    _ellipse(draw, (x, y + bob), 4.2 * scale, 3.2 * scale, YELLOW, OUTLINE, 0.55)
    _ellipse(draw, (x + 3.2 * scale, y - 2.2 * scale + bob), 2.7 * scale, 2.5 * scale, YELLOW, OUTLINE, 0.55)
    _poly(draw, [(x+5.3*scale, y-2.4*scale+bob), (x+8.0*scale, y-1.5*scale+bob), (x+5.2*scale, y-0.5*scale+bob)], BILL, OUTLINE, 0.4)
    _ellipse(draw, (x + 3.8 * scale, y - 2.7 * scale + bob), 0.4 * scale, 0.4 * scale, EYE, None)
    _line(draw, [(x-2.0*scale, y+3.0*scale+bob), (x-3.0*scale, y+5.0*scale+bob)], BILL_DARK, 0.65)
    _line(draw, [(x+1.5*scale, y+3.0*scale+bob), (x+2.0*scale, y+5.0*scale+bob)], BILL_DARK, 0.65)


def _draw_effects_behind(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    t = pose.effect_phase
    if pose.effect == "speed_feathers":
        for i in range(6):
            x = max(6.0, 31.0 - i * 4.0 + 2.0 * math.sin(t * math.tau + i))
            y = 47.0 + i * 9.0
            _arc(draw, (x, y), 3.0, 1.5, 185, 345, _fade(FEATHER_LIGHT, 0.65), 0.8)
    elif pose.effect == "roll_memes":
        for i in range(7):
            a = t * 360.0 + i * (360.0 / 7.0)
            q = _add((64.0, 72.0), _rot((25.0, 0.0), a))
            _draw_meme_card(draw, q, 0.38, (CYAN, BLUE, MAGENTA)[i % 3], i % 3, a)
    elif pose.effect == "water":
        for i in range(7):
            x = 24 + i * 13
            y = 98 + 2 * math.sin(t * math.tau + i)
            _arc(draw, (x, y), 8.0, 2.4, 190, 350, _fade(CYAN, 0.62), 1.0)
    elif pose.effect == "duckling_swarm":
        for i in range(7):
            u = (t * 1.35 + i / 7.0) % 1.0
            _draw_duckling(draw, (18.0 + u * 101.0, 108.0 - (i % 2) * 4.0), 0.75 + 0.08 * (i % 3), t + i * 0.13)
    elif pose.effect == "fallen_memes":
        for i in range(5):
            q = (31.0 + i * 15.0, 101.0 + (i % 2) * 5.0)
            _draw_meme_card(draw, q, 0.42, (CYAN, BLUE, MAGENTA, LIME, RED)[i], i % 3, -20 + i * 11)


def _draw_effects_front(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    t = pose.effect_phase
    if pose.effect == "impact_feathers":
        burst = math.sin(t * math.pi)
        for i in range(8):
            a = 205 + i * 18
            q = _add((64.0, 111.0), _rot((7.0 + 19.0 * burst, 0.0), a))
            _ellipse(draw, q, 1.2, 0.7, _fade(FEATHER_LIGHT, 0.75), None)
    elif pose.effect == "book_block":
        pulse = math.sin(t * math.pi)
        _arc(draw, (78.0, 66.0), 24.0 + 5.0 * pulse, 33.0 + 7.0 * pulse, 235, 118, _fade(CYAN, 0.82), 1.5)
    elif pose.effect == "hit":
        burst = math.sin(t * math.pi)
        for i in range(6):
            a = i * 60.0
            q = _add((49.0, 48.0), _rot((5.0 + 12.0 * burst, 0.0), a))
            _line(draw, [q, _add(q, _rot((3.0, 0.0), a))], RED, 1.1)
    elif pose.effect == "honk":
        reach = min(1.0, t * 1.6)
        fade = max(0.0, 1.0 - max(0.0, t - 0.55) * 2.2)
        for i in range(4):
            r = 6.0 + i * 6.5 + reach * 8.0
            _arc(draw, (87.0, 42.0), r, r * 0.62, -58, 58, _fade(YELLOW, fade * (0.9 - i * 0.15)), 1.6)
        for i in range(5):
            x = 94.0 + i * 4.0 + reach * 4.0
            _line(draw, [(x, 39.0 - i), (x + 3.0, 35.0 - i)], _fade(BURGUNDY_LIGHT, fade), 1.0)
    elif pose.effect == "selfish_meme":
        if t < 0.22:
            q = (79.0, 63.0)
        elif t < 0.68:
            u = (t - 0.22) / 0.46
            q = (79.0 + 43.0 * u, 63.0 - 18.0 * math.sin(u * math.pi))
        else:
            u = (t - 0.68) / 0.32
            q = (118.0 - 10.0 * u, 63.0 + 4.0 * u)
        _draw_meme_card(draw, q, 0.85, CYAN, 0, 10.0 * math.sin(t * math.tau))
        if t > 0.58:
            for i in range(2):
                _draw_meme_card(draw, (109.0 + i * 10.0, 75.0 + i * 8.0), 0.48, (BLUE, MAGENTA)[i], i + 1, -12 + i * 22)
    elif pose.effect == "mutation":
        bloom = math.sin(t * math.pi)
        colors = (CYAN, BLUE, MAGENTA, LIME, RED)
        for i, color in enumerate(colors):
            a = t * 140.0 + i * 72.0
            q = _add((64.0, 58.0), _rot((12.0 + 25.0 * bloom, 0.0), a))
            _draw_meme_card(draw, q, 0.55 + 0.12 * bloom, color, i % 3, a + 10)
        _line(draw, [(64.0, 81.0), (64.0, 38.0)], _fade(YELLOW, 0.5 * bloom), 1.1)
    elif pose.effect == "missing_meme":
        # Search lens, empty result card, and rotating question mark.
        sweep = math.sin(t * math.tau) * 8.0
        _ellipse(draw, (91.0 + sweep, 54.0), 10.0, 10.0, _fade(GLASS, 0.32), LEATHER, 1.8)
        _line(draw, [(84.0 + sweep, 61.0), (72.0 + sweep, 75.0)], LEATHER, 3.0)
        _draw_meme_card(draw, (106.0, 79.0), 0.58, FEATHER_SHADE, 1, -6)
        # Tiny question-mark strokes; no font dependency.
        _arc(draw, (109.0, 31.0), 6.0, 7.0, 205, 35, BURGUNDY_LIGHT, 1.5)
        _line(draw, [(112.5, 35.0), (111.0, 40.0)], BURGUNDY_LIGHT, 1.5)
        _ellipse(draw, (110.5, 44.0), 1.0, 1.0, BURGUNDY_LIGHT, None)
    elif pose.effect == "lecture":
        # A deliberately simplified gene -> meme -> duckling diagram.
        y = 28.0
        _line(draw, [(87.0, y), (115.0, y)], _fade(PAPER, 0.8), 1.0)
        _line(draw, [(87.0, y+18), (115.0, y+18)], _fade(PAPER, 0.8), 1.0)
        for i in range(5):
            x = 89.0 + i * 6.0
            _line(draw, [(x, y + 2.0), (x+3.0, y+16.0)], CYAN if i % 2 else MAGENTA, 0.8)
        _draw_meme_card(draw, (104.0, 66.0), 0.55, CYAN, 0, 0)
        _draw_duckling(draw, (104.0, 91.0), 0.72, t)
        _line(draw, [(104.0, 49.0), (104.0, 55.0)], YELLOW, 1.1)
        _line(draw, [(104.0, 76.0), (104.0, 82.0)], YELLOW, 1.1)
    elif pose.effect == "viable_meme":
        for i in range(8):
            a = t * 360.0 + i * 45.0
            q = _add((64.0, 50.0), _rot((24.0, 0.0), a))
            _draw_meme_card(draw, q, 0.38, (CYAN, BLUE, MAGENTA, LIME)[i % 4], i % 3, a)
    elif pose.effect == "goose_correction":
        # A crossed-out long-necked bird icon behind him.
        _ellipse(draw, (103.0, 59.0), 10.0, 7.0, _fade(FEATHER_SHADE, 0.8), OUTLINE_SOFT, 0.7)
        _capsule(draw, (108.0, 55.0), (109.0, 39.0), 2.2, FEATHER_SHADE, OUTLINE_SOFT)
        _ellipse(draw, (110.0, 36.0), 4.0, 3.0, FEATHER_SHADE, OUTLINE_SOFT, 0.7)
        _line(draw, [(92.0, 32.0), (116.0, 68.0)], RED, 2.2)
        _line(draw, [(115.0, 32.0), (92.0, 68.0)], RED, 2.2)


def _draw_book(draw: ImageDraw.ImageDraw, center: Point, angle: float, scale: float = 1.0) -> None:
    w, h = 16.0 * scale, 21.0 * scale
    img = Image.new("RGBA", (int((w + 8) * SUPER), int((h + 8) * SUPER)), (0, 0, 0, 0))
    d = blending_draw(img)
    ox, oy = (w + 8) / 2.0, (h + 8) / 2.0
    _poly(d, [(ox-w/2,oy-h/2),(ox+w/2,oy-h/2),(ox+w/2,oy+h/2),(ox-w/2,oy+h/2)], BURGUNDY, OUTLINE, 1.0)
    _poly(d, [(ox-w/2+2,oy-h/2+2),(ox+w/2-1.2,oy-h/2+2),(ox+w/2-1.2,oy+h/2-2),(ox-w/2+2,oy+h/2-2)], PAPER, None)
    _line(d, [(ox-2.0,oy-h/2+3.0),(ox-2.0,oy+h/2-3.0)], BURGUNDY_LIGHT, 1.0)
    _ellipse(d, (ox+3.0, oy-2.0), 2.3, 2.1, FEATHER_LIGHT, OUTLINE, 0.45)
    _poly(d, [(ox+4.5,oy-2.2),(ox+7.1,oy-1.3),(ox+4.5,oy-0.5)], BILL, OUTLINE, 0.35)
    _line(d, [(ox+0.5,oy+3.0),(ox+6.0,oy+3.0)], INK, 0.5)
    img = img.rotate(-angle, resample=Image.Resampling.BICUBIC, expand=True)
    draw._image.alpha_composite(img, (int((center[0] - img.width / SUPER / 2) * SUPER), int((center[1] - img.height / SUPER / 2) * SUPER)))


def _draw_character(draw: ImageDraw.ImageDraw, pose: Pose) -> None:
    # Render the articulated duck into its own layer so the whole body can lean
    # or roll without having to duplicate every local transform.
    layer = Image.new("RGBA", (FRAME_W * SUPER, FRAME_H * SUPER), (0, 0, 0, 0))
    d = blending_draw(layer)
    x0, y0 = 64.0 + pose.x, 70.0 + pose.y
    sy = 1.0 - pose.squash

    def q(local: Point) -> Point:
        return x0 + local[0], y0 + local[1] * sy

    # Far leg and foot.
    far_hip = q((-6.0, 20.0))
    far_knee = q((-8.0 - pose.stride * 0.30, 31.0 - pose.knee))
    far_ankle = q((-7.0 - pose.stride * 0.58, 42.0))
    _capsule(d, far_hip, far_knee, 2.1, BILL_DARK)
    _capsule(d, far_knee, far_ankle, 1.8, BILL)
    _line(d, [far_ankle, (far_ankle[0] + 7.0, far_ankle[1] + 1.2)], BILL_DARK, 2.3)
    _line(d, [far_ankle, (far_ankle[0] + 4.0, far_ankle[1] + 3.0)], BILL_DARK, 1.2)

    # Tail behind the body.
    _poly(d, [q((-16.0, 2.0)), q((-28.0, 4.0)), q((-19.0, 11.0)), q((-12.0, 8.0))], FEATHER_SHADE, OUTLINE, 1.0)

    # Torso feather mass and academic clothes.
    _ellipse(d, q((0.0, 2.0)), 18.0, 25.0 * sy, FEATHER, OUTLINE, 1.4)
    _poly(d, [q((-13.0,-9.0)),q((12.0,-10.0)),q((16.0,16.0)),q((8.0,25.0)),q((-9.0,24.0)),q((-16.0,14.0))], VEST, OUTLINE, 1.0)
    _poly(d, [q((-11.0,-7.0)),q((-2.0,0.0)),q((-4.0,23.0)),q((-10.0,23.0)),q((-15.0,13.0))], VEST_DARK, None)
    _poly(d, [q((1.0,-9.0)),q((11.0,-8.0)),q((14.0,14.0)),q((7.0,22.0)),q((1.0,21.0))], VEST_LIGHT, None)
    # Tweed crosshatch.
    for yy in (-3.0, 5.0, 13.0):
        _line(d, [q((-12.0, yy)), q((13.0, yy+1.5))], _fade(TWEED, 0.42), 0.55)
    for xx in (-7.0, 0.0, 7.0):
        _line(d, [q((xx,-7.0)), q((xx+2.0,20.0))], _fade(TWEED, 0.30), 0.5)
    _poly(d, [q((-6.0,-11.0)),q((0.0,-5.0)),q((6.0,-11.0)),q((5.0,-2.0)),q((0.0,1.0)),q((-5.0,-2.0))], SHIRT, OUTLINE_SOFT, 0.55)
    _poly(d, [q((-5.5,-5.0)),q((0.0,-1.0)),q((-5.5,3.0)),q((-8.0,-1.0)),q((-5.5,-5.0)),q((5.5,-5.0)),q((8.0,-1.0)),q((5.5,3.0)),q((0.0,-1.0))], BURGUNDY, OUTLINE, 0.6)
    for bx, by in [(-7.0, 6.0), (7.0, 6.0), (-7.0, 16.0), (7.0, 16.0)]:
        _ellipse(d, q((bx, by)), 0.8, 0.8, TWEED, None)

    # Far wing.
    far_root = q((-13.0, -3.0))
    far_tip = _add(far_root, _rot((24.0, 0.0), pose.wing_l))
    _capsule(d, far_root, far_tip, 4.5, FEATHER_SHADE)
    _poly(d, [far_tip, _add(far_tip, _rot((8.0,-2.8), pose.wing_l)), _add(far_tip, _rot((8.0,2.8), pose.wing_l))], FEATHER_SHADE, OUTLINE, 0.7)

    # Near wing.
    near_root = q((14.0, -2.0))
    near_tip = _add(near_root, _rot((25.0, 0.0), pose.wing_r))
    _capsule(d, near_root, near_tip, 5.0, FEATHER)
    _poly(d, [near_tip, _add(near_tip, _rot((8.5,-3.0), pose.wing_r)), _add(near_tip, _rot((8.5,3.0), pose.wing_r))], FEATHER_LIGHT, OUTLINE, 0.75)

    # Near leg and foot.
    near_hip = q((6.0, 20.0))
    near_knee = q((8.0 + pose.stride * 0.30, 31.0 - pose.knee))
    near_ankle = q((7.0 + pose.stride * 0.58, 42.0))
    _capsule(d, near_hip, near_knee, 2.2, BILL_DARK)
    _capsule(d, near_knee, near_ankle, 1.9, BILL)
    _line(d, [near_ankle, (near_ankle[0] + 8.0, near_ankle[1] + 1.0)], BILL_DARK, 2.5)
    _line(d, [near_ankle, (near_ankle[0] + 4.5, near_ankle[1] + 3.2)], BILL_DARK, 1.3)

    # Neck, head and crest.
    _ellipse(d, q((2.0, -18.0)), 9.0, 11.0, FEATHER, OUTLINE, 1.0)
    head = q((4.0, -31.0))
    _ellipse(d, head, 15.5, 14.0, FEATHER, OUTLINE, 1.3)
    _ellipse(d, (head[0] + 2.0, head[1] - 2.0), 12.3, 10.0, FEATHER_LIGHT, None)
    # White swept crest.
    _poly(d, [
        (head[0]-12.0, head[1]-9.0),
        (head[0]-15.0, head[1]-20.0),
        (head[0]-7.0, head[1]-14.0),
        (head[0]-5.0, head[1]-23.0),
        (head[0]+1.0, head[1]-14.0),
        (head[0]+8.0, head[1]-20.0),
        (head[0]+7.0, head[1]-9.0),
    ], CREST, OUTLINE, 1.0)

    # Bill with independent opening.
    bill_y = head[1] + 1.0
    _poly(d, [(head[0]+10.0,bill_y-3.0),(head[0]+27.0,bill_y-1.3),(head[0]+11.0,bill_y+2.0)], BILL_LIGHT, OUTLINE, 0.9)
    lower_drop = 2.0 + pose.beak_open * 5.0
    _poly(d, [(head[0]+10.0,bill_y+1.0),(head[0]+25.0,bill_y+2.0),(head[0]+11.0,bill_y+lower_drop)], BILL, OUTLINE, 0.8)
    if pose.beak_open > 0.35:
        _poly(d, [(head[0]+12.0,bill_y+1.7),(head[0]+22.0,bill_y+2.4),(head[0]+12.5,bill_y+lower_drop-0.8)], BILL_DARK, None)

    # Eyes and skeptical brows.
    eye1 = (head[0] + 1.0, head[1] - 3.0)
    eye2 = (head[0] + 8.0, head[1] - 2.5)
    if pose.eye_closed:
        _line(d, [(eye1[0]-2.0,eye1[1]),(eye1[0]+2.0,eye1[1]+0.5)], EYE, 0.9)
        _line(d, [(eye2[0]-2.0,eye2[1]),(eye2[0]+2.0,eye2[1]+0.4)], EYE, 0.9)
    else:
        for ex, ey in (eye1, eye2):
            _ellipse(d, (ex,ey), 1.3, 1.5, WHITE, EYE, 0.45)
            _ellipse(d, (ex+0.4,ey+0.1), 0.55, 0.75, EYE, None)
    _line(d, [(head[0]-1.0,head[1]-7.5),(head[0]+3.0,head[1]-8.5)], OUTLINE_SOFT, 0.9)
    _line(d, [(head[0]+5.5,head[1]-8.0),(head[0]+10.0,head[1]-6.8)], OUTLINE_SOFT, 0.9)

    # Spectacles and bridge.
    _ellipse(d, eye1, 4.2, 3.7, _fade(GLASS, 0.18), OUTLINE_SOFT, 0.75)
    _ellipse(d, eye2, 4.2, 3.7, _fade(GLASS, 0.18), OUTLINE_SOFT, 0.75)
    _line(d, [(eye1[0]+4.0,eye1[1]),(eye2[0]-4.0,eye2[1])], OUTLINE_SOFT, 0.75)
    _line(d, [(eye1[0]-4.0,eye1[1]),(head[0]-12.0,head[1]-1.0)], OUTLINE_SOFT, 0.75)

    # Notebook held in front for blocking/casting interactions.
    if pose.book_front:
        _draw_book(d, (near_tip[0] + 2.0, near_tip[1] - 1.0), pose.book_angle, 0.9)
    if pose.pointer:
        end = _add(near_tip, _rot((23.0, 0.0), -42.0))
        _line(d, [near_tip, end], TWEED, 1.3)
        _ellipse(d, end, 1.0, 1.0, BURGUNDY_LIGHT, None)

    # Rotate the composed figure around its center for leaning/rolling.
    if abs(pose.lean) > 0.01:
        layer = layer.rotate(-pose.lean, resample=Image.Resampling.BICUBIC, center=_p((64.0, 72.0)))
    draw._image.alpha_composite(layer)


def render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    pose = _pose(anim, frame_idx, nframes)
    behind = Image.new("RGBA", (FRAME_W * SUPER, FRAME_H * SUPER), (0, 0, 0, 0))
    body = Image.new("RGBA", behind.size, (0, 0, 0, 0))
    front = Image.new("RGBA", behind.size, (0, 0, 0, 0))
    _draw_effects_behind(blending_draw(behind), pose)
    _draw_character(blending_draw(body), pose)
    _draw_effects_front(blending_draw(front), pose)
    image = Image.alpha_composite(Image.alpha_composite(behind, body), front)
    if pose.alpha < 0.999:
        alpha = image.getchannel("A").point(lambda value: int(value * max(0.0, pose.alpha)))
        image.putalpha(alpha)
    return image.resize((FRAME_W, FRAME_H), Image.Resampling.LANCZOS)


def _render_native_portrait(expression: str = "default", phase: float = 0.0) -> Image.Image:
    scale = 3
    size = 256
    image = Image.new("RGBA", (size * scale, size * scale), (0, 0, 0, 0))
    draw = blending_draw(image)

    def p(point: Point) -> Tuple[int, int]:
        return int(point[0] * scale), int(point[1] * scale)

    def ell(center: Point, rx: float, ry: float, fill: RGBA, outline: RGBA | None = None, width: float = 1.0) -> None:
        x, y = center
        draw.ellipse(p((x-rx,y-ry))+p((x+rx,y+ry)), fill=fill, outline=outline, width=max(1,int(width*scale)) if outline else 1)

    def ln(points: Sequence[Point], fill: RGBA, width: float = 1.0) -> None:
        draw.line([p(q) for q in points], fill=fill, width=max(1,int(width*scale)), joint="curve")

    # Academic shoulders and vest.
    draw.polygon([p((35,256)),p((49,181)),p((88,146)),p((169,146)),p((211,181)),p((226,256))], fill=VEST, outline=OUTLINE)
    draw.polygon([p((35,256)),p((49,181)),p((112,149)),p((104,256))], fill=VEST_DARK)
    draw.polygon([p((143,149)),p((211,181)),p((226,256)),p((139,256))], fill=VEST_LIGHT)
    for yy in (177, 202, 227):
        ln([(52,yy),(205,yy+7)], _fade(TWEED,0.4), 1.0)
    draw.polygon([p((101,145)),p((127,169)),p((155,145)),p((145,195)),p((111,195))], fill=SHIRT, outline=OUTLINE)
    draw.polygon([p((108,165)),p((127,177)),p((110,191)),p((99,178)),p((108,165)),p((146,165)),p((157,178)),p((145,191)),p((127,177))], fill=BURGUNDY, outline=OUTLINE)

    # Neck, head and crest.
    ell((129,119), 28, 34, FEATHER, OUTLINE, 2.0)
    ell((130,82), 55, 48, FEATHER, OUTLINE, 2.4)
    ell((137,74), 44, 35, FEATHER_LIGHT, None)
    draw.polygon([p((82,53)),p((76,10)),p((101,31)),p((109,1)),p((127,30)),p((153,4)),p((151,40)),p((177,22)),p((166,58))], fill=CREST, outline=OUTLINE)

    # Bill.
    draw.polygon([p((167,76)),p((231,83)),p((171,96))], fill=BILL_LIGHT, outline=OUTLINE)
    open_amount = 13 if expression in {"speaking","honk","perplexed"} else 5
    draw.polygon([p((170,94)),p((228,88)),p((173,94+open_amount))], fill=BILL, outline=OUTLINE)
    if expression == "honk":
        draw.polygon([p((174,95)),p((220,91)),p((176,106))], fill=BILL_DARK)

    eye_closed = expression == "honk"
    eye_pos = ((116,69),(146,71))
    if eye_closed:
        for ex,ey in eye_pos:
            ln([(ex-8,ey),(ex+8,ey+2)], EYE, 2.5)
    else:
        for ex,ey in eye_pos:
            ell((ex,ey), 6.0, 7.0, WHITE, EYE, 1.4)
            ell((ex+2,ey+1), 2.2, 3.0, EYE, None)
    # Brows and spectacles.
    ln([(105,54),(122,50)], OUTLINE_SOFT, 2.4)
    ln([(136,51),(154,58)], OUTLINE_SOFT, 2.4)
    for ex,ey in eye_pos:
        ell((ex,ey), 15, 12, _fade(GLASS,0.15), OUTLINE_SOFT, 2.0)
    ln([(131,69),(133,70)], OUTLINE_SOFT, 2.0)
    ln([(101,68),(84,70)], OUTLINE_SOFT, 2.0)

    # Expression-specific motifs.
    if expression == "smug":
        ln([(101,111),(119,116),(139,110)], BILL_DARK, 1.4)
    elif expression == "perplexed":
        draw.arc(p((191,23))+p((224,62)), start=195, end=28, fill=BURGUNDY_LIGHT, width=max(1,int(3*scale)))
        ln([(215,52),(211,65)], BURGUNDY_LIGHT, 3.0)
        ell((210,76), 2.5, 2.5, BURGUNDY_LIGHT, None)
    elif expression == "honk":
        for i in range(4):
            r = 16 + i * 15 + phase * 8
            draw.arc(p((208-r,91-r*0.6))+p((208+r,91+r*0.6)), start=-55, end=55, fill=_fade(YELLOW,0.9-i*0.16), width=max(1,int(2.5*scale)))
    elif expression == "meme":
        # Large meme card near the shoulder.
        draw.rounded_rectangle(p((168,135))+p((236,226)), radius=8*scale, fill=PAPER, outline=OUTLINE, width=2*scale)
        draw.rectangle(p((173,141))+p((231,184)), fill=CYAN)
        ell((197,163), 13, 11, FEATHER_LIGHT, OUTLINE, 1.2)
        draw.polygon([p((206,161)),p((225,166)),p((207,172))], fill=BILL, outline=OUTLINE)
        ell((201,160), 2, 2, EYE, None)
        ln([(178,194),(226,194)], INK, 1.3)
        ln([(178,206),(218,206)], INK, 1.3)
    elif expression == "speaking":
        for i in range(3):
            _draw_meme_card(draw, (198 + i*12, 126 + i*18), 0.45, (CYAN,BLUE,MAGENTA)[i], i, -8+i*8)

    return image.resize(PORTRAIT_SIZE, Image.Resampling.LANCZOS)


def render_portraits(out_dir: Path, **opts) -> List[Path]:
    del opts
    clips = {
        "default": PortraitClip.still(_render_native_portrait("default")),
        "speaking": PortraitClip(tuple(_render_native_portrait("speaking", i / 8.0) for i in range(8)), duration_ms=108, looping=True),
        "smug": PortraitClip.still(_render_native_portrait("smug")),
        "perplexed": PortraitClip.still(_render_native_portrait("perplexed")),
        "honk": PortraitClip(tuple(_render_native_portrait("honk", i / 8.0) for i in range(8)), duration_ms=96, looping=True),
        "meme": PortraitClip.still(_render_native_portrait("meme")),
    }
    return write_portrait_sheet(TARGET_NAME, clips, Path(out_dir))


def _body_metrics_override(fw: int, fh: int):
    return {
        "body_pixel_bbox": {"x": int(fw * 0.25), "y": int(fh * 0.07), "w": int(fw * 0.57), "h": int(fh * 0.86)},
        "feet_pixel": {"x": fw * 0.5, "y": fh * 0.91},
        "feet_anchor_norm": {"x": 0.0, "y": round(0.5 - 0.91, 6)},
    }


def render(out_dir: Path, **opts) -> List[Path]:
    del opts
    outputs = build_sheet(
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
            "honk_rebuttal": {"bbox": {"x": 77, "y": 22, "w": 51, "h": 47}},
            "selfish_meme": {"bbox": {"x": 74, "y": 21, "w": 54, "h": 68}},
            "meme_mutation": {"bbox": {"x": 20, "y": 8, "w": 103, "h": 92}},
            "duckling_swarm": {"bbox": {"x": 8, "y": 86, "w": 120, "h": 39}},
        },
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    return [Path(outputs[key]) for key in keys if outputs.get(key)]


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
