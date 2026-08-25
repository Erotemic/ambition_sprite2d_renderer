"""Canonical SVG-rigged full-action generator for Carl Stargan.

The manually traced ``assets/carl-stargan.svg`` is the visual authority. Python
owns the rig clips, cosmic effects, portraits, and sheet publication—not the
character's anatomy or clothing geometry.
"""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

from PIL import Image

import json

from ...authoring import strike_axis, swing_effects
from ...authoring.portrait import FaceGuide, PortraitClip, render_framed_portrait, write_portrait_sheet
from ...authoring.canonical_scientist_rig import ensure_scientist_rig
from ...authoring.rigdoc import RigDocument
from ...authoring.sheet_build import build_sheet, write_canonical
from ._svg_fighter_effects import (
    FxCanvas,
    bone_origin,
    compose_rig_frame,
    fade,
    orbit_point,
    pulse,
    smooth,
)
from .carl_stargan_motion import CARL_ROWS, EFFECT_ALIASES

TARGET_NAME = "carl_stargan"
FRAME_SIZE = (160, 160)
ROWS = list(CARL_ROWS)

ACTOR_METADATA = {'actor': {'character_id': 'npc_carl_stargan', 'display_name': 'Carl Stargan'},
 'body': {'body_plan': 'HumanoidBiped',
          'body_kind': 'Standard',
          'mass_class': 'Medium',
          'traits': ['story',
                     'humanoid',
                     'science_communicator',
                     'cosmic_storyteller',
                     'skeptic',
                     'playable_candidate'],
          'locomotion_hint': 'Walk'},
 'capabilities': {'traversal': {'walk': True,
                                'jump': True,
                                'climb': True,
                                'fly': None,
                                'swim': True,
                                'crawl': True,
                                'use_lifts': True,
                                'door_access': ['public']},
                  'interactions': {'talk': True, 'trade': None, 'carry': None, 'open_doors': ['public']}},
 'brain': {'default_preset': 'patrol_peaceful'},
 'actions': {'default_preset': 'peaceful'},
 'visual': {'default_pose': 'idle',
            'face_guide': {'center': {'x': 64.0, 'y': 29.0},
                           'size': {'w': 31.0, 'h': 36.0},
                           'source_size': {'w': 128.0, 'h': 128.0}}},
 'tags': ['story', 'humanoid', 'science_communicator', 'cosmic_storyteller', 'skeptic', 'playable_candidate'],
 'sockets': {'head': {'source': 'explicit.profile.humanoid', 'point': {'x': 64.0, 'y': 29.0}},
             'chest': {'source': 'explicit.profile.humanoid', 'point': {'x': 64.0, 'y': 64.0}},
             'hand_l': {'source': 'explicit.profile.humanoid', 'point': {'x': 44.0, 'y': 79.0}},
             'hand_r': {'source': 'explicit.profile.humanoid', 'point': {'x': 86.0, 'y': 79.0}},
             'speech_bubble': {'source': 'explicit.profile.humanoid', 'point': {'x': 64.0, 'y': 3.0}}},
 'animation_bindings': {'default': {'animation': 'idle', 'events': []},
                        'locomotion.walk': {'animation': 'walk', 'events': []},
                        'locomotion.run': {'animation': 'run', 'events': []},
                        'traversal.jump': {'animation': 'jump', 'events': []},
                        'traversal.fall': {'animation': 'fall', 'events': []},
                        'action.melee.primary': {'animation': 'planetary_orbit', 'events': []},
                        'action.ranged.primary': {'animation': 'pale_blue_dot', 'events': []},
                        'action.special.primary': {'animation': 'cosmic_calendar', 'events': []},
                        'action.special.secondary': {'animation': 'billions_and_billions', 'events': []},
                        'action.special.up': {'animation': 'cosmic_drift', 'events': []},
                        'action.special.down': {'animation': 'billions_and_billions', 'events': []},
                        'action.super': {'animation': 'starstuff', 'events': []},
                        'action.defense.block': {'animation': 'block', 'events': []},
                        'action.defense.roll': {'animation': 'roll', 'events': []},
                        'interaction.talk': {'animation': 'talk', 'events': []},
                        'interaction.use': {'animation': 'use_telescope', 'events': []},
                        'emote.think': {'animation': 'think', 'events': []},
                        'emote.inspire': {'animation': 'stargaze', 'events': []},
                        'emote.taunt': {'animation': 'taunt', 'events': []}},
 'authoring_description': 'Carl Stargan is a warm, theatrically cosmic parody of science communicator Carl '
                          'Sagan. The name bends Sagan toward stars while the character pairs wonder, scale, '
                          'skepticism, and an inability to discuss a room without locating it in the '
                          'universe. The visual target is a warmly caricatured 1970s science presenter: soft '
                          'brown jacket, black turtleneck, dark trousers, expressive hands, swept wavy hair, '
                          'and a pocket telescope used as a recurring prop. Cosmic effects are gameplay '
                          "inventions inspired by Sagan's public language about starstuff, the pale blue "
                          'dot, planetary scale, and evidence-led wonder.',
 'gameplay_description': 'Use as a science guide, narrator, lecturer, or playable explorer whose hints '
                         'reframe local obstacles at cosmic scale. He should inspire curiosity but '
                         'ultimately defer to evidence rather than vibes.',
 'dialogue_hints': {'barks': ['Billions and billions of pedestals in this hall...',
                              'Scale is not decoration, it is the point.',
                              'Wonder gets me to the question. Evidence decides who leaves with it.']}}

ACTOR_METADATA.setdefault("tags", []).append("svg_rigged")
ACTOR_METADATA.setdefault("body", {}).setdefault("traits", []).append("svg_rigged")
ACTOR_METADATA.setdefault("visual", {})["canonical_source"] = "assets/carl-stargan.svg"
ACTOR_METADATA["actions"] = {"default_preset": "carl_stargan"}
ACTOR_METADATA["provenance"] = {
    "variant_family": TARGET_NAME,
    "variant_id": "manual_svg_rig_canonical_2026_08_06",
    "lineage": [
        {
            "revision_id": "carl_stargan_character_direction",
            "creator_kind": "human",
            "creator": "Jon Crall",
            "contribution": "cosmic_storyteller_smash_fighter_direction",
        },
        {
            "revision_id": "carl_stargan_manual_svg_paperdoll",
            "creator_kind": "human",
            "creator": "Jon Crall",
            "parent_revision_id": "carl_stargan_character_direction",
            "contribution": "canonical_manually_traced_svg_parts_and_joint_layout",
        },
        {
            "revision_id": "carl_stargan_svg_rig_generator",
            "creator_kind": "model",
            "creator": "GPT-5.6 Thinking",
            "parent_revision_id": "carl_stargan_manual_svg_paperdoll",
            "contribution": "rig_clip_cosmic_effect_and_sheet_generator_authoring",
        },
    ],
}

OUTLINE = (27, 22, 26, 255)
STAR_GOLD = (248, 203, 112, 255)
STAR_WHITE = (251, 244, 214, 255)
NEBULA_BLUE = (91, 164, 220, 255)
NEBULA_VIOLET = (148, 101, 186, 255)
PALE_BLUE = (104, 190, 225, 255)
PLANET_OCHRE = (208, 139, 66, 255)
PLANET_RUST = (150, 71, 50, 255)
COSMIC_DARK = (22, 30, 50, 255)
TELESCOPE = (72, 72, 82, 255)
TELESCOPE_LIGHT = (151, 151, 162, 255)


@lru_cache(maxsize=4)
def _load_doc_cached(path_text: str, mtime_ns: int, size: int) -> RigDocument:
    del mtime_ns, size
    return RigDocument.load(path_text)


def _doc() -> RigDocument:
    path = ensure_scientist_rig("carl_stargan")
    stat = path.stat()
    return _load_doc_cached(str(path), stat.st_mtime_ns, stat.st_size)


def _stars(canvas: FxCanvas, center: tuple[float, float], count: int, radius: float, phase: float, alpha: float = 1.0) -> None:
    for index in range(count):
        angle = phase * math.tau + index * 2.399963
        r = radius * (0.25 + 0.75 * ((index * 0.6180339887) % 1.0))
        point = (center[0] + math.cos(angle) * r, center[1] + math.sin(angle) * r * 0.68)
        color = STAR_GOLD if index % 3 else STAR_WHITE
        canvas.star(point, 1.2 + (index % 4) * 0.45, fade(color, alpha * (0.45 + 0.45 * pulse(phase + index / max(1, count)))), points=4)


def _behind(animation: str, canvas: FxCanvas, t: float, world, params) -> None:
    del params
    center = (80.0, 82.0)
    if animation in {"cosmic_drift", "float_glide"}:
        for index in range(9):
            x = 150 - ((t * 70 + index * 17) % 72)
            y = 43 + (index * 13) % 78
            canvas.star((x, y), 1.4 + index % 3, fade(STAR_GOLD if index % 2 else PALE_BLUE, 0.32 + 0.25 * pulse(t + index / 9)), points=4)
        canvas.line([(150, 85), (118, 85), (98, 89)], fade(NEBULA_BLUE, 0.22), 4.0)
    elif animation == "block":
        hand = bone_origin(world, "near_arm_hand", (55, 90))
        shield = (hand[0] - 8, hand[1] - 1)
        for radius in (18, 25, 32):
            canvas.ellipse(shield, radius, radius * 0.78, fade(COSMIC_DARK, 0.09), fade(PALE_BLUE, 0.28 + 0.18 * pulse(t + radius / 50)), 0.9)
        _stars(canvas, shield, 7, 27, t, 0.45)
    elif animation == "stargaze":
        q = smooth(t)
        canvas.arc(center, 67, 51, 205, 340, fade(NEBULA_BLUE, 0.25 + 0.45 * q), 1.4)
        canvas.arc(center, 72, 57, 205, 340, fade(NEBULA_VIOLET, 0.18 + 0.35 * q), 2.5)
        _stars(canvas, (80, 70), 17, 68, t * 0.18, 0.4 + 0.4 * q)
    elif animation == "planetary_orbit":
        q = smooth(t)
        canvas.ellipse(center, 61, 31, None, fade(NEBULA_BLUE, 0.3 + 0.4 * pulse(t)), 1.1)
        planet = orbit_point(center, 61, 31, t + 0.15)
        canvas.ellipse(planet, 8 + 2 * q, 8 + 2 * q, fade(PLANET_OCHRE, 0.48), fade(PLANET_RUST, 0.9), 1.0)
        canvas.arc(planet, 10, 3.5, 180, 360, fade(STAR_GOLD, 0.65), 0.8)
    elif animation == "pale_blue_dot":
        q = smooth(t)
        hand = bone_origin(world, "near_arm_hand", (43, 80))
        dot = (max(34.0, hand[0] - 12), hand[1] - 2)
        for radius in (8, 16, 24, 31):
            canvas.ellipse(dot, radius * q, radius * q, None, fade(PALE_BLUE, (1 - q) * 0.42 + 0.08), 0.8)
        _stars(canvas, dot, 13, 29 * q, t * 0.2, 0.22 + 0.3 * q)
    elif animation == "cosmic_calendar":
        q = smooth(t)
        for index in range(12):
            start = -165 + index * 20
            end = start + 14
            color = STAR_GOLD if index > 8 else NEBULA_BLUE if index > 4 else NEBULA_VIOLET
            canvas.arc(center, 30 + index * 2.5 * q, 22 + index * 1.7 * q, start, end, fade(color, 0.25 + 0.45 * q), 2.2)
        _stars(canvas, center, 10, 45 * q, -t * 0.16, 0.35)
    elif animation == "billions_and_billions":
        q = smooth(t)
        _stars(canvas, center, 34, 12 + 62 * q, t * 0.25, 0.28 + 0.5 * q)
        canvas.ellipse(center, 20 + 34 * q, 12 + 23 * q, fade(NEBULA_VIOLET, 0.05 + 0.08 * q), None)
    elif animation == "starstuff":
        q = smooth(t)
        for arm in range(4):
            points = []
            for index in range(22):
                a = arm * math.pi / 2 + index * 0.27 + t * math.tau
                r = 2.2 * index * q
                points.append((center[0] + math.cos(a) * r, center[1] + math.sin(a) * r * 0.62))
            canvas.line(points, fade(NEBULA_VIOLET if arm % 2 else NEBULA_BLUE, 0.22 + 0.35 * q), 1.0)
        _stars(canvas, center, 30, 64 * q, -t * 0.33, 0.35 + 0.35 * q)
    elif animation in {"attack_up", "attack_down", "air_neutral", "air_forward", "air_back", "air_down", "air_up", "jab", "punch"}:
        hand = bone_origin(world, "near_arm_hand", (48, 82))
        q = pulse(t)
        for radius in (12, 19, 27):
            canvas.arc(hand, radius, radius * 0.72, 130, 310, fade(STAR_GOLD, q * (0.68 - radius / 70)), 1.3)


def _telescope(canvas: FxCanvas, a: tuple[float, float], b: tuple[float, float], alpha: float) -> None:
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = max(1.0, math.hypot(dx, dy))
    nx, ny = -dy / length, dx / length
    p1 = (a[0] + nx * 3, a[1] + ny * 3)
    p2 = (b[0] + nx * 5, b[1] + ny * 5)
    p3 = (b[0] - nx * 5, b[1] - ny * 5)
    p4 = (a[0] - nx * 3, a[1] - ny * 3)
    canvas.polygon([p1, p2, p3, p4], fade(TELESCOPE, alpha), fade(OUTLINE, alpha), 1.0)
    canvas.line([a, b], fade(TELESCOPE_LIGHT, alpha), 1.1)
    canvas.ellipse(b, 5.5, 5.5, fade(TELESCOPE_LIGHT, alpha), fade(OUTLINE, alpha), 0.9)


def _front(animation: str, canvas: FxCanvas, t: float, world, params) -> None:
    del params
    near = bone_origin(world, "near_arm_hand", (50, 90))
    far = bone_origin(world, "far_arm_hand", (78, 92))
    if animation == "use_telescope":
        q = smooth(min(1.0, t * 2.0)) * smooth(min(1.0, (1.0 - t) * 3.0))
        _telescope(canvas, far, near, 0.45 + 0.55 * q)
        canvas.star((near[0] - 10, near[1] - 4), 2.8 + 2.5 * pulse(t), fade(PALE_BLUE, q), points=4)
    elif animation == "planetary_orbit":
        planet = orbit_point((80, 82), 61, 31, t + 0.15)
        canvas.ellipse(planet, 5.5, 5.5, PLANET_OCHRE, PLANET_RUST, 1.0)
        canvas.ellipse((planet[0]-2, planet[1]-2), 1.5, 1.5, fade(STAR_WHITE, 0.65))
    elif animation == "pale_blue_dot":
        dot = (max(34.0, near[0] - 12), near[1] - 2)
        canvas.ellipse(dot, 2.2 + 1.5 * pulse(t), 2.2 + 1.5 * pulse(t), PALE_BLUE, STAR_WHITE, 0.8)
    elif animation == "billions_and_billions":
        for hand in (near, far):
            canvas.star((hand[0], hand[1]-2), 3.0 + 2.0 * pulse(t), fade(STAR_GOLD, 0.75), points=6, outline=fade(OUTLINE,0.55))
    elif animation == "starstuff":
        _stars(canvas, (80, 82), 12, 44 * smooth(t), t * 0.6, 0.55)
    elif animation in {"stargaze", "celebrate"}:
        canvas.star((near[0]-5, near[1]-7), 3.2 + 1.4*pulse(t), fade(STAR_GOLD,0.75), points=5)
        canvas.star((far[0]+5, far[1]-6), 2.6 + 1.2*pulse(t+0.2), fade(PALE_BLUE,0.65), points=4)
    elif animation == "think":
        for index, radius in enumerate((2.0, 3.0, 4.0)):
            canvas.ellipse((112 + index*8, 42-index*7), radius, radius, fade(PALE_BLUE,0.35+0.12*index), fade(OUTLINE,0.35), 0.5)
    elif animation == "taunt":
        canvas.text((30, 31), "EVIDENCE?", STAR_GOLD, size=4.1, stroke=fade(OUTLINE,0.6))


SPEC_DIR = Path(__file__).resolve().parent / "rigged" / TARGET_NAME / "specs"


def _spec_for(animation: str) -> dict | None:
    """The authored swing spec for one clip, or `None` for a clip with no swing."""
    path = SPEC_DIR / f"{animation}.spec.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _swing_axes(animation: str, frame_count: int):
    """Where the telescope is on each frame, measured on the sword part alone.

    ⛔ NOT the luminance inference `swing_effects` falls back to. That one holds
    for a dark fighter carrying bright steel; Carl is the other way round — a
    pale jacket and a dark brass barrel — so it would find his coat and miss the
    weapon. The rig knows which part is the sword, so it says so.
    """
    doc = _doc()
    samples = [doc.frame_time(animation, i, frame_count) for i in range(frame_count)]
    return strike_axis.from_part(doc, animation, samples, "sword")


def _raw_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    effect_animation = EFFECT_ALIASES.get(animation, animation)
    return compose_rig_frame(
        _doc(),
        animation,
        frame_idx,
        frame_count,
        behind=lambda canvas, t, world, params: _behind(effect_animation, canvas, t, world, params),
        front=lambda canvas, t, world, params: _front(effect_animation, canvas, t, world, params),
    )


@lru_cache(maxsize=None)
def _clip_frames(animation: str, frame_count: int) -> tuple:
    """Every frame of one clip, with its authored swing composited on.

    Cached per CLIP, not per frame: the trail on frame 4 is drawn from where the
    barrel was on frames 1-3, so a `render_fn` that only ever sees one frame
    cannot draw it — which is how a sheet ships with none of it.
    """
    raw = [_raw_frame(animation, i, frame_count) for i in range(frame_count)]
    spec = _spec_for(animation)
    if not spec:
        return tuple(raw)
    axes = _swing_axes(animation, frame_count)
    return tuple(swing_effects.composite_authored_effect(raw, spec, axes=axes))


@lru_cache(maxsize=1)
def _attack_hitboxes() -> dict:
    """The authored hit volume for every telescope swing that has a spec.

    Derived from the same axes and spec as the trail, so the arc a player is
    shown is the arc that hits them.
    """
    out = {}
    for animation, frame_count, _duration in ROWS:
        spec = _spec_for(animation)
        if not spec:
            continue
        raw = [_raw_frame(animation, i, frame_count) for i in range(frame_count)]
        poly = swing_effects.authored_hit_volume(
            raw, spec, axes=_swing_axes(animation, frame_count)
        )
        if poly:
            out[animation] = {"poly": poly}
    return out


def render_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    return _clip_frames(animation, frame_count)[frame_idx]


def render_portraits(out_dir: str | Path, **opts):
    del opts
    doc = _doc()
    face = FaceGuide(
        center_x=66.0,
        center_y=41.0,
        width=40.0,
        height=43.0,
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
        return render_framed_portrait(source, face, view_width=70.0, center_y=59.0)

    clips = {
        "default": PortraitClip.loop(
            tuple(frame("idle", index, 8) for index in range(8)),
            duration_ms=148,
        ),
        # The pose a UI BOX draws. Frame 2 of the same idle — the still
        # this target published before its default began to move.
        "portrait": PortraitClip.still(frame("idle", 2, 8)),
        "curious": PortraitClip.still(frame("think", 4, 8)),
        "observing": PortraitClip.still(frame("use_telescope", 5, 10)),
        "cosmic": PortraitClip.still(frame("starstuff", 6, 10)),
    }
    return write_portrait_sheet(
        TARGET_NAME, clips, Path(out_dir), still_clip="portrait"
    )


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
        sheet_tuning=doc.sprite_tuning or {"collision_scale": 1.58},
        attack_hitboxes=_attack_hitboxes(),
        pose_bodies="authored",
        # His paperdoll view is `Carl Stargan - Side Left` and both his rig
        # (`features.facing: "west"`) and his SVG (`data-rig-facing="west"`)
        # declare it. Publishing it is what makes the declaration real: without
        # this line the fact is authored at every layer and read by none, and he
        # renders facing away from his own movement exactly as the Patent Clerk
        # did.
        authored_faces_left=doc.authored_faces_left,
        animation_key_map={name: name for name, _frames, _duration in ROWS},
        # trim: NOT passed, deliberately. `registry/pack_groups.py` is the single
        # authority — "all build paths ask `policy_for(target)` instead of
        # carrying independent defaults" — and its default packs, because Carl
        # draws through the trim-aware CharacterAnimator like every character.
        # He carried `trim=False` with no reason beside it, which is what left a
        # 155x156 frame around a 58x114 body: 3.7x the area, all of it
        # transparent margin that the height contract would scale.
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    return [Path(outputs[key]) for key in keys if outputs.get(key)]


def render_canonical(out_dir: str | Path, **opts):
    del opts
    return write_canonical(TARGET_NAME, ROWS, render_frame, Path(out_dir), frame_size=FRAME_SIZE)


__all__ = [
    "ACTOR_METADATA", "ROWS", "TARGET_NAME", "render", "render_canonical",
    "render_frame", "render_portraits",
]
