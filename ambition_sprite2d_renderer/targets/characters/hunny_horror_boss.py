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
    ("roar", 8, 104),
    ("death", 8, 118),
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
        "action.special.roar": {
            "animation": "roar",
            "events": [
                {"t": 0.26, "event": "roar_charge_start", "source": TARGET_NAME},
                {"t": 0.58, "event": "roar_peak", "source": TARGET_NAME},
                {"t": 0.78, "event": "roar_release", "source": TARGET_NAME},
            ],
        },
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


@lru_cache(maxsize=1)
def load_doc() -> RigDocument:
    return RigDocument.load(RIG_PATH)


def render_frame(animation: str, frame_idx: int, frame_count: int):
    return load_doc().render_frame(animation, frame_idx, frame_count)


def render_portraits(out_dir: str | Path, **opts):
    del opts
    doc = load_doc()

    def portrait_frame(animation: str, frame_idx: int, frame_count: int):
        source = doc.render_at(
            animation,
            doc.frame_time(animation, frame_idx, frame_count),
            scale=4,
        )
        face = FaceGuide(
            center_x=80.0,
            center_y=57.0,
            width=34.0,
            height=34.0,
            source_width=float(doc.frame["width"]),
            source_height=float(doc.frame["height"]),
        )
        return render_framed_portrait(source, face, view_width=56.0, center_y=71.0)

    clips = {
        "default": PortraitClip.still(portrait_frame("rest", 1, 8)),
        "roar": PortraitClip(tuple(portrait_frame("roar", i, 8) for i in range(8)), duration_ms=104, looping=True),
        "snarl": PortraitClip.still(portrait_frame("swipe", 4, 8)),
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
