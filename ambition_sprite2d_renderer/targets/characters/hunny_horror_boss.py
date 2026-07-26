"""Hunny Horror boss rig.

A large parody-horror bear boss built through the direct SVG rig pipeline:
vector parts live in ``data/characters/hunny_horror_boss/hunny_horror_boss-front.svg``
and Python assembles them into animation rows through a declarative rig doc.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Tuple

from ...authoring.portrait import (
    FaceGuide,
    PortraitClip,
    render_framed_portrait,
    write_portrait_sheet,
)
from ...authoring.rigdoc import RigDocument
from ...authoring.sheet_build import build_sheet, write_canonical

TARGET_NAME = "hunny_horror_boss"
RIG_PATH = Path(__file__).with_name("hunny_horror_boss.rig.json")
FRAME_SIZE = (320, 320)
ROWS: List[Tuple[str, int, int]] = [
    ("rest", 8, 130),
    ("walk", 8, 105),
    ("swipe", 8, 92),
    ("maul", 10, 78),
    ("slam", 10, 84),
    ("roar", 10, 104),
    ("stagger", 6, 86),
    ("death", 12, 108),
]

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_hunny_horror_boss",
        "display_name": "Hunny Horror",
    },
    "visual": {"default_pose": "rest"},
    "body": {
        "body_plan": "BossBrute",
        "body_kind": "Wide",
        "mass_class": "Heavy",
        "traits": ["boss", "bear", "horror", "honey", "monster"],
        "locomotion_hint": "Lumber",
    },
    "capabilities": {
        "traversal": {"walk": True, "jump": None, "climb": None, "fly": None},
        "interactions": {"talk": None, "trade": None, "carry": None},
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "aggressive"},
    "animation_bindings": {
        "default": {"animation": "rest", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "action.melee.primary": {
            "animation": "swipe",
            "events": [
                {"t": 0.28, "event": "telegraph_peak", "source": TARGET_NAME},
                {"t": 0.54, "event": "hitbox_active_start", "source": TARGET_NAME},
                {"t": 0.72, "event": "hitbox_active_end", "source": TARGET_NAME},
            ],
        },
        "action.melee.heavy": {
            "animation": "maul",
            "events": [
                {"t": 0.18, "event": "telegraph_peak", "source": TARGET_NAME},
                {"t": 0.34, "event": "hitbox_active_start", "source": TARGET_NAME},
                {"t": 0.46, "event": "hitbox_active_end", "source": TARGET_NAME},
                {"t": 0.60, "event": "hitbox_active_start", "source": TARGET_NAME},
                {"t": 0.74, "event": "hitbox_active_end", "source": TARGET_NAME},
            ],
        },
        "action.special.primary": {
            "animation": "slam",
            "events": [
                {"t": 0.30, "event": "telegraph_peak", "source": TARGET_NAME},
                {"t": 0.66, "event": "ground_impact", "source": TARGET_NAME},
            ],
        },
        "action.special.secondary": {
            "animation": "roar",
            "events": [
                {"t": 0.26, "event": "roar_charge_start", "source": TARGET_NAME},
                {"t": 0.58, "event": "roar_peak", "source": TARGET_NAME},
                {"t": 0.78, "event": "roar_release", "source": TARGET_NAME},
            ],
        },
        "action.special.roar": {
            "animation": "roar",
            "events": [
                {"t": 0.26, "event": "roar_charge_start", "source": TARGET_NAME},
                {"t": 0.58, "event": "roar_peak", "source": TARGET_NAME},
                {"t": 0.78, "event": "roar_release", "source": TARGET_NAME},
            ],
        },
        "damage.hit": {"animation": "stagger", "events": []},
        "interaction.talk": {"animation": "roar", "events": []},
        "death": {"animation": "death", "events": []},
    },
    "sockets": {
        "head": {"source": f"{TARGET_NAME}.geometry", "point": {"x": 80.0, "y": 58.0}},
        "mouth": {"source": f"{TARGET_NAME}.geometry", "point": {"x": 80.0, "y": 78.0}},
        "claw_l": {"source": f"{TARGET_NAME}.geometry", "point": {"x": 27.0, "y": 127.0}},
        "claw_r": {"source": f"{TARGET_NAME}.geometry", "point": {"x": 135.0, "y": 127.0}},
        "belly": {"source": f"{TARGET_NAME}.geometry", "point": {"x": 80.0, "y": 118.0}},
    },
    "tags": ["boss", "bear", "horror", "honey"],
}


ACTOR_METADATA.update(
    {
        "authoring_description": (
            "Hunny Horror is a grotesque horror inversion of Winnie-the-Pooh: the gentle "
            "honey-obsessed bear becomes an enormous, starving thing whose nursery warmth has curdled "
            "into appetite. Keep the spelling and imagery transformed rather than presenting the "
            "original character directly."
        ),
        "gameplay_description": (
            "Use as a stalking or arena boss driven by hunger. Honey pots, rumbly-tummy tells, sticky "
            "traps, reaching paws, and falsely comforting speech should make childhood familiarity "
            "work against the player."
        ),
    }
)
ACTOR_METADATA.setdefault("dialogue_hints", {}).setdefault(
    "barks",
    [
        'Have you brought any? No? Then stand a little closer.',
        'There was always a pot...',
        'First the voice. Then the paw. Then the pot.',
    ],
)


@lru_cache(maxsize=1)
def load_doc() -> RigDocument:
    return RigDocument.load(RIG_PATH)


def render_frame(animation: str, frame_idx: int, frame_count: int):
    return load_doc().render_frame(animation, frame_idx, frame_count)


def render_portraits(out_dir: str | Path, **opts):
    del opts
    doc = load_doc()
    face = FaceGuide(
        center_x=80.0,
        center_y=57.0,
        width=34.0,
        height=34.0,
        source_width=float(doc.frame["width"]),
        source_height=float(doc.frame["height"]),
    )

    def portrait_frame(animation: str, frame_idx: int, frame_count: int):
        source = doc.render_at(
            animation,
            doc.frame_time(animation, frame_idx, frame_count),
            scale=4,
        )
        return render_framed_portrait(source, face, view_width=56.0, center_y=71.0)

    def portrait_frames(animation: str, frame_indices: tuple[int, ...], frame_count: int):
        return tuple(
            portrait_frame(animation, frame_idx, frame_count)
            for frame_idx in frame_indices
        )

    clips = {
        "default": PortraitClip.still(portrait_frame("rest", 1, 8)),
        "speaking": PortraitClip(
            portrait_frames("rest", (0, 2, 4, 6), 8),
            duration_ms=130,
            looping=True,
        ),
        "evil_flash": PortraitClip(
            (
                portrait_frame("rest", 1, 8),
                portrait_frame("roar", 2, 10),
                portrait_frame("rest", 1, 8),
                portrait_frame("swipe", 4, 8),
            ),
            duration_ms=95,
            looping=True,
        ),
        "evil_hold": PortraitClip.still(portrait_frame("roar", 6, 10)),
        "roar": PortraitClip(
            portrait_frames("roar", tuple(range(10)), 10),
            duration_ms=104,
            looping=True,
        ),
        "snarl": PortraitClip.still(portrait_frame("maul", 3, 10)),
    }
    return write_portrait_sheet(TARGET_NAME, clips, Path(out_dir))


def render(out_dir: str | Path, **opts):
    del opts
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=Path(out_dir),
        frame_size=FRAME_SIZE,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning={"collision_scale": 2.15},
        animation_key_map={row[0]: row[0] for row in ROWS},
        trim=True,
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


def render_canonical(out_dir: str | Path, **opts):
    del opts
    return write_canonical(
        TARGET_NAME,
        ROWS,
        render_frame,
        Path(out_dir),
        frame_size=FRAME_SIZE,
    )


__all__ = [
    "ACTOR_METADATA",
    "FRAME_SIZE",
    "ROWS",
    "TARGET_NAME",
    "load_doc",
    "render",
    "render_canonical",
    "render_frame",
    "render_portraits",
]
