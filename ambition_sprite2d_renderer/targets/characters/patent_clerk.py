"""Canonical SVG-rigged generator for Patent Clerk.

The manually traced ``assets/patent-clerk.svg`` is the character-art authority.
This module poses that paperdoll through its generated rig and adds only
animation-specific effects and review/output metadata in Python.
"""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path
from typing import List, Tuple

from PIL import Image

from ...authoring.portrait import FaceGuide, PortraitClip, render_framed_portrait, write_portrait_sheet
from ...authoring.canonical_scientist_rig import load_scientist_rig
from ...authoring.rigdoc import RigDocument
from ...authoring.sheet_build import build_sheet, write_canonical
from ._svg_fighter_effects import (
    FxCanvas,
    bone_origin,
    clock,
    compose_rig_frame,
    fade,
    orbit_point,
    pulse,
    smooth,
)

TARGET_NAME = "patent_clerk"
FRAME_SIZE = (176, 176)
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 148), ("walk", 8, 106), ("run", 8, 76),
    ("crouch", 6, 94), ("crouch_walk", 8, 90), ("jump", 6, 88),
    ("fall", 6, 92), ("land_hard", 7, 80), ("dash_startup", 4, 50),
    ("dash", 6, 58), ("slide", 6, 68), ("roll", 8, 58),
    ("wall_grab", 6, 102), ("wall_jump", 6, 80),
    ("ledge_grab", 6, 96), ("ledge_climb", 6, 92),
    ("climb", 8, 96), ("swim", 8, 102), ("block", 6, 80),
    ("known_result", 7, 62), ("hit", 5, 82), ("death", 9, 102),
    ("talk", 8, 104), ("interact", 8, 92),
    ("application_review", 6, 58), ("margin_correction", 7, 64),
    ("light_argument", 8, 66), ("reference_frame", 9, 72),
    ("elevator_thought", 9, 72), ("synchronize_clocks", 10, 78),
    ("mass_energy_conversion", 10, 80), ("annus_mirabilis", 12, 82),
    ("celebrate", 8, 88), ("taunt", 8, 92),
]

ACTOR_METADATA = {'actor': {'character_id': 'special_patent_clerk', 'display_name': 'Patent Clerk'},
 'body': {'body_plan': 'HumanoidBiped',
          'body_kind': 'Compact',
          'mass_class': 'Heavy',
          'traits': ['special_character',
                     'humanoid',
                     'patent_clerk',
                     'reference_frame_controller',
                     'classification_fighter',
                     'playable_candidate'],
          'locomotion_hint': 'Walk'},
 'capabilities': {'traversal': {'walk': True,
                                'jump': True,
                                'climb': True,
                                'fly': None,
                                'swim': True,
                                'crawl': True,
                                'use_lifts': True,
                                'door_access': ['public', 'administrative']},
                  'interactions': {'talk': True,
                                   'trade': None,
                                   'carry': None,
                                   'open_doors': ['public', 'administrative']}},
 'brain': {'default_preset': 'special_examiner'},
 'actions': {'default_preset': 'patent_clerk'},
 'visual': {'default_pose': 'idle',
            'portrait': {'face_guide': {'center': {'x': 88.0, 'y': 58.0},
                                        'size': {'w': 42.0, 'h': 45.0},
                                        'source_size': {'w': 176.0, 'h': 176.0}}}},
 'tags': ['special_character',
          'humanoid',
          'patent_clerk',
          'reference_frame_controller',
          'classification_fighter',
          'playable_candidate'],
 'sockets': {'head': {'source': 'explicit.patent_clerk', 'point': {'x': 88.0, 'y': 58.0}},
             'chest': {'source': 'explicit.patent_clerk', 'point': {'x': 87.0, 'y': 92.0}},
             'hand_l': {'source': 'explicit.patent_clerk', 'point': {'x': 67.0, 'y': 104.0}},
             'hand_r': {'source': 'explicit.patent_clerk', 'point': {'x': 108.0, 'y': 103.0}},
             'speech_bubble': {'source': 'explicit.patent_clerk', 'point': {'x': 88.0, 'y': 7.0}}},
 'animation_bindings': {'default': {'animation': 'idle', 'events': []},
                        'locomotion.walk': {'animation': 'walk', 'events': []},
                        'locomotion.run': {'animation': 'run', 'events': []},
                        'traversal.jump': {'animation': 'jump', 'events': []},
                        'traversal.fall': {'animation': 'fall', 'events': []},
                        'action.melee.primary': {'animation': 'margin_correction', 'events': []},
                        'action.ranged.primary': {'animation': 'light_argument', 'events': []},
                        'action.special.primary': {'animation': 'reference_frame', 'events': []},
                        'action.special.secondary': {'animation': 'mass_energy_conversion', 'events': []},
                        'action.special.up': {'animation': 'elevator_thought', 'events': []},
                        'action.special.down': {'animation': 'synchronize_clocks', 'events': []},
                        'action.defense.block': {'animation': 'block', 'events': []},
                        'action.defense.parry': {'animation': 'known_result', 'events': []},
                        'action.super': {'animation': 'annus_mirabilis', 'events': []},
                        'interaction.talk': {'animation': 'talk', 'events': []},
                        'interaction.use': {'animation': 'interact', 'events': []},
                        'emote.taunt': {'animation': 'taunt', 'events': []}},
 'provenance': {'variant_family': 'patent_clerk',
                'variant_id': 'gpt_5_6_thinking_bespoke_2026_08_05',
                'lineage': [{'revision_id': 'patent_clerk_character_direction',
                             'creator_kind': 'human',
                             'creator': 'Jon Crall',
                             'contribution': 'coy_identity_special_character_and_hair_first_design_direction'},
                            {'revision_id': 'patent_clerk_procedural_sprite_v1',
                             'creator_kind': 'model',
                             'creator': 'GPT-5.6 Thinking',
                             'parent_revision_id': 'patent_clerk_character_direction',
                             'contribution': 'bespoke_body_pose_effect_portrait_and_dynamic_hair_authoring'}]},
 'authoring_description': 'Patent Clerk is a coy parody of Albert Einstein, designed around his '
                          'patent-office period, iconic unruly hair, moustache, relativity thought '
                          'experiments, clock synchronization, reference frames, and mass-energy '
                          'equivalence. The public character never confirms the identity: recognition is '
                          'carried by silhouette, mechanics, and restrained bureaucratic dialogue. The '
                          'combat classifications and administrative stamps are deliberate game inventions '
                          'rather than biographical claims.',
 'gameplay_description': 'A high-mastery heavyweight controller who classifies bodies as MASS, ENERGY, '
                         'MOVING, or AT REST; manipulates relative velocity and local reference frames; and '
                         'turns careful observation into unusually strong parries and finishers. His '
                         'recovery uses an accelerating elevator frame, his stage control uses synchronized '
                         'clocks, and his super resolves several quiet office observations into one '
                         'inevitable conversion.',
 'dialogue_hints': {'barks': ['Your application has several interesting assumptions.',
                              'Please remain in your chosen frame.',
                              'The distinction is useful—for now.',
                              'Your timing was local.',
                              'Approved.',
                              'No, I am only a clerk.'],
                    'fallback_lines': ['A clock is reliable until you ask where it has been.',
                                       'Common sense is often a local regulation.',
                                       'You may call yourself stationary. Courtesy permits it.',
                                       'The office prefers inventions. I find assumptions more interesting.',
                                       'There are many patent clerks.',
                                       'Not required in this field.']}}

ACTOR_METADATA.setdefault("tags", []).append("svg_rigged")
ACTOR_METADATA.setdefault("body", {}).setdefault("traits", []).append("svg_rigged")
ACTOR_METADATA.setdefault("visual", {})["canonical_source"] = "assets/patent-clerk.svg"
ACTOR_METADATA["provenance"] = {
    "variant_family": TARGET_NAME,
    "variant_id": "manual_svg_rig_canonical_2026_08_06",
    "lineage": [
        {
            "revision_id": "patent_clerk_character_direction",
            "creator_kind": "human",
            "creator": "Jon Crall",
            "contribution": "coy_identity_special_character_and_hair_first_design_direction",
        },
        {
            "revision_id": "patent_clerk_manual_svg_paperdoll",
            "creator_kind": "human",
            "creator": "Jon Crall",
            "parent_revision_id": "patent_clerk_character_direction",
            "contribution": "canonical_manually_traced_svg_parts_and_joint_layout",
        },
        {
            "revision_id": "patent_clerk_svg_rig_generator",
            "creator_kind": "model",
            "creator": "GPT-5.6 Thinking",
            "parent_revision_id": "patent_clerk_manual_svg_paperdoll",
            "contribution": "rig_clip_effect_and_sheet_generator_authoring",
        },
    ],
}

OUTLINE = (28, 26, 30, 255)
STAMP = (181, 57, 52, 255)
STAMP_LIGHT = (242, 114, 91, 255)
FRAME_BLUE = (77, 151, 204, 255)
FRAME_LIGHT = (155, 218, 240, 255)
CLOCK_GOLD = (235, 188, 82, 255)
MASS = (196, 87, 71, 255)
ENERGY = (90, 178, 224, 255)
CONVERSION = (244, 226, 132, 255)
PAPER = (248, 242, 216, 245)
INK = (48, 43, 45, 255)


@lru_cache(maxsize=1)
def _doc() -> RigDocument:
    return load_scientist_rig("patent_clerk")


def _label(canvas: FxCanvas, center: tuple[float, float], text: str, color=STAMP, size: float = 5.0) -> None:
    padding = max(4.0, len(text) * size * 0.28)
    canvas.polygon(
        [
            (center[0] - padding, center[1] - 4.5),
            (center[0] + padding, center[1] - 4.5),
            (center[0] + padding, center[1] + 4.5),
            (center[0] - padding, center[1] + 4.5),
        ],
        fade((245, 235, 210, 255), 0.92),
        color,
        0.8,
    )
    canvas.text(center, text, color, size=size, stroke=fade(OUTLINE, 0.22))


def _behind(animation: str, canvas: FxCanvas, t: float, world, params) -> None:
    del params
    center = (88.0, 89.0)
    if animation == "reference_frame":
        q = smooth(t)
        alpha = 0.25 + 0.55 * pulse(t)
        canvas.polygon([(30, 35), (144, 35), (144, 145), (30, 145)], (22, 39, 62, int(75 * alpha)), fade(FRAME_BLUE, alpha), 1.1)
        canvas.arrow((88, 139), (88, 43), fade(FRAME_LIGHT, alpha), 1.0, 4.0)
        canvas.arrow((137, 90), (38, 90), fade(FRAME_LIGHT, alpha), 1.0, 4.0)
        for offset in (-36, -18, 18, 36):
            canvas.line([(88 + offset, 87), (88 + offset, 93)], fade(FRAME_BLUE, alpha * 0.8), 0.6)
            canvas.line([(85, 90 + offset), (91, 90 + offset)], fade(FRAME_BLUE, alpha * 0.8), 0.6)
    elif animation == "elevator_thought":
        q = smooth(t)
        canvas.polygon([(47, 29), (130, 29), (130, 150), (47, 150)], (30, 38, 54, 70), fade(FRAME_BLUE, 0.35 + q * 0.45), 1.2)
        for x in (59, 88, 117):
            canvas.arrow((x, 139), (x, 47 - 8 * pulse(t)), fade(FRAME_LIGHT, 0.4 + 0.5 * q), 1.0, 4.2)
    elif animation == "synchronize_clocks":
        for index, position in enumerate(((43, 53), (131, 53), (88, 31))):
            clock(canvas, position, 12.0, t + index * 0.21, fade(CLOCK_GOLD, 0.45 + 0.45 * pulse(t)))
    elif animation == "mass_energy_conversion":
        q = smooth(t)
        spread = 34.0 * (1.0 - q) + 7.0 * q
        canvas.ellipse((center[0] - spread, 87), 11 + 3 * q, 11 + 3 * q, fade(MASS, 0.32 + 0.32 * q), fade(MASS, 0.8), 1.0)
        canvas.ellipse((center[0] + spread, 87), 11 + 3 * q, 11 + 3 * q, fade(ENERGY, 0.32 + 0.32 * q), fade(ENERGY, 0.8), 1.0)
        if t > 0.55:
            flash = smooth((t - 0.55) / 0.45)
            for radius in (10, 18, 28, 40):
                canvas.ellipse(center, radius * flash, radius * flash, None, fade(CONVERSION, (1 - flash) * 0.72), 1.1)
    elif animation == "annus_mirabilis":
        q = smooth(t)
        for index in range(6):
            radius = 16 + index * 9 + q * 6
            canvas.ellipse(center, radius, radius * 0.62, None, fade(CONVERSION if index % 2 else FRAME_BLUE, 0.28 + 0.25 * pulse(t + index * 0.08)), 0.8)
        for index in range(8):
            angle = index * math.tau / 8.0 + t * math.tau
            point = (center[0] + math.cos(angle) * 60, center[1] + math.sin(angle) * 42)
            canvas.star(point, 2.4 + 1.2 * pulse(t + index / 8), fade(CONVERSION, 0.55), points=4)
    elif animation in {"block", "known_result"}:
        hand = bone_origin(world, "near_arm_hand", (62, 95))
        shield_center = (hand[0] - 10, hand[1] - 2)
        canvas.ellipse(shield_center, 25, 32, fade(FRAME_BLUE, 0.12), fade(FRAME_LIGHT, 0.45 + 0.35 * pulse(t)), 1.3)


def _front(animation: str, canvas: FxCanvas, t: float, world, params) -> None:
    del params
    hand = bone_origin(world, "near_arm_hand", (62, 95))
    far_hand = bone_origin(world, "far_arm_hand", (82, 97))
    if animation == "application_review":
        q = smooth(t)
        paper = (hand[0] - 10, hand[1] - 8)
        canvas.polygon([(paper[0]-13, paper[1]-9), (paper[0]+13, paper[1]-9), (paper[0]+13, paper[1]+9), (paper[0]-13, paper[1]+9)], PAPER, INK, 0.8)
        for dy in (-4, 0, 4):
            canvas.line([(paper[0]-9, paper[1]+dy), (paper[0]+7, paper[1]+dy)], fade(INK, 0.62), 0.55)
        if q > 0.58:
            _label(canvas, (paper[0], paper[1]), "APPROVED", size=3.7)
    elif animation == "margin_correction":
        q = pulse(t)
        end = (max(8.0, hand[0] - 40 - 12 * q), hand[1] - 5)
        canvas.line([hand, ((hand[0]+end[0])*0.5, hand[1]+7), end], fade(STAMP_LIGHT, 0.5 + 0.5*q), 2.0)
        canvas.line([(end[0]-4, end[1]-4), (end[0]+4, end[1]+4)], STAMP, 1.2)
        canvas.line([(end[0]-4, end[1]+4), (end[0]+4, end[1]-4)], STAMP, 1.2)
    elif animation == "light_argument":
        q = smooth(t)
        end = (13.0, hand[1] - 2)
        canvas.line([hand, end], fade(FRAME_LIGHT, 0.35 + 0.65*q), 3.0)
        canvas.line([(hand[0], hand[1]-2), (end[0], end[1]-2)], fade(CONVERSION, 0.25 + 0.55*q), 1.0)
        canvas.star(end, 3.2 + 2.8*pulse(t), fade(CONVERSION, 0.9), points=6, outline=fade(OUTLINE,0.7))
    elif animation == "known_result":
        _label(canvas, (42, 42), "KNOWN RESULT", FRAME_BLUE, 4.1)
        canvas.arrow((50, 49), (hand[0]-2, hand[1]-4), fade(FRAME_LIGHT, 0.75), 0.9, 3.5)
    elif animation == "block":
        _label(canvas, (88, 35), "AT REST", MASS, 4.4)
    elif animation == "reference_frame":
        _label(canvas, (88, 148), "LOCAL FRAME", FRAME_BLUE, 4.2)
    elif animation == "elevator_thought":
        _label(canvas, (88, 151), "ACCELERATING", FRAME_BLUE, 3.8)
    elif animation == "synchronize_clocks":
        _label(canvas, (88, 147), "SYNCHRONIZE", CLOCK_GOLD, 4.0)
    elif animation == "mass_energy_conversion":
        q = smooth(t)
        spread = 34.0 * (1.0 - q) + 7.0 * q
        _label(canvas, (88-spread, 108), "MASS", MASS, 3.6)
        _label(canvas, (88+spread, 108), "ENERGY", ENERGY, 3.6)
    elif animation == "annus_mirabilis":
        labels = (("MASS", MASS), ("ENERGY", ENERGY), ("MOVING", FRAME_BLUE), ("AT REST", CLOCK_GOLD))
        for index, (text, color) in enumerate(labels):
            angle = -2.5 + index * 1.66
            point = (88 + math.cos(angle)*56, 90 + math.sin(angle)*43)
            _label(canvas, point, text, color, 3.2)
    elif animation in {"talk", "interact", "taunt"} and t > 0.45:
        canvas.ellipse((hand[0]-4, hand[1]-3), 2.5, 2.5, fade(STAMP_LIGHT, 0.6), STAMP, 0.6)


def render_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    return compose_rig_frame(
        _doc(),
        animation,
        frame_idx,
        frame_count,
        behind=lambda canvas, t, world, params: _behind(animation, canvas, t, world, params),
        front=lambda canvas, t, world, params: _front(animation, canvas, t, world, params),
    )


def render_portraits(out_dir: str | Path, **opts):
    del opts
    doc = _doc()
    face = FaceGuide(
        center_x=72.0,
        center_y=52.0,
        width=48.0,
        height=45.0,
        source_width=float(doc.frame["width"]),
        source_height=float(doc.frame["height"]),
    )

    def frame(animation: str, index: int, count: int):
        source = doc.render_at(
            animation,
            doc.frame_time(animation, index, count),
            supersample=4,
            scale=3,
        )
        return render_framed_portrait(source, face, view_width=78.0, center_y=68.0)

    clips = {
        "default": PortraitClip.still(frame("idle", 2, 8)),
        "reviewing": PortraitClip.still(frame("application_review", 3, 6)),
        "argument": PortraitClip.still(frame("light_argument", 4, 8)),
        "breakthrough": PortraitClip.still(frame("annus_mirabilis", 7, 12)),
    }
    return write_portrait_sheet(TARGET_NAME, clips, Path(out_dir))


def render(out_dir: str | Path, **opts):
    del opts
    doc = _doc()
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=Path(out_dir),
        frame_size=FRAME_SIZE,
        auto_crop=True,
        crop_margin=4,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning=doc.sprite_tuning or {"collision_scale": 1.66},
        animation_key_map={name: name for name, _frames, _duration in ROWS},
        trim=False,
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    return [Path(outputs[key]) for key in keys if outputs.get(key)]


def render_canonical(out_dir: str | Path, **opts):
    del opts
    return write_canonical(TARGET_NAME, ROWS, render_frame, Path(out_dir), frame_size=FRAME_SIZE)


def source_uses_forbidden_raster_effects() -> bool:
    return False


__all__ = [
    "ACTOR_METADATA", "ROWS", "TARGET_NAME", "render", "render_canonical",
    "render_frame", "render_portraits", "source_uses_forbidden_raster_effects",
]
