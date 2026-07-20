"""Paradox Barber sprite target.

A polished front-view barber parody built through the SVG rig route.
The character leans into the classic barber paradox: he is sharply groomed,
slightly self-contradictory, and visually split between lathered clean-shave
and impossible self-barbering facial hair.

The silhouette is built around a tall, narrow torso, rolled sleeves, a crisp
barber apron with barber-pole stripes, a curled moustache, and asymmetrical
face treatment so he reads as The Paradox Barber even at sprite scale.
No drop shadows are used.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Tuple

from ...authoring.portrait import FaceGuide, PortraitClip, render_framed_portrait, write_portrait_sheet
from ...authoring.rigdoc import RigDocument
from ...authoring.sheet_build import build_sheet, write_canonical

TARGET_NAME = "paradox_barber"
RIG_PATH = Path(__file__).with_name("paradox_barber.rig.json")
FRAME_SIZE = (320, 320)
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 130),
    ("walk", 8, 102),
    ("talk", 8, 110),
    ("clean_cut", 8, 84),
    ("paradox_loop", 8, 96),
    ("self_shave", 8, 100),
    ("death", 8, 116),
]

ACTOR_METADATA = {
    "actor": {"character_id": "npc_paradox_barber", "display_name": "The Paradox Barber"},
    "visual": {"default_pose": "idle"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Slim",
        "mass_class": "Light",
        "traits": ["story", "humanoid", "barber", "paradox", "logic", "playable_candidate"],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {"walk": True, "jump": True, "climb": None, "fly": None, "swim": None, "crawl": False, "use_lifts": True, "door_access": ["public"]},
        "interactions": {"talk": True, "trade": None, "carry": None, "open_doors": ["public"]},
    },
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "peaceful"},
    "tags": ["story", "humanoid", "barber", "paradox", "logic", "playable_candidate"],
    "sockets": {
        "head": {"source": "explicit.profile.humanoid", "point": {"x": 80.0, "y": 34.0}},
        "chest": {"source": "explicit.profile.humanoid", "point": {"x": 80.0, "y": 86.0}},
        "hand_l": {"source": "explicit.profile.humanoid", "point": {"x": 32.0, "y": 120.0}},
        "hand_r": {"source": "explicit.profile.humanoid", "point": {"x": 128.0, "y": 120.0}},
        "speech_bubble": {"source": "explicit.profile.humanoid", "point": {"x": 80.0, "y": 6.0}},
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "self_shave", "events": []},
        "action.melee.primary": {"animation": "clean_cut", "events": []},
        "action.special.primary": {"animation": "paradox_loop", "events": []},
        "death": {"animation": "death", "events": []},
    },
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
        source = doc.render_at(animation, doc.frame_time(animation, frame_idx, frame_count), scale=4)
        face = FaceGuide(
            center_x=80.0,
            center_y=50.0,
            width=34.0,
            height=36.0,
            source_width=float(doc.frame["width"]),
            source_height=float(doc.frame["height"]),
        )
        return render_framed_portrait(source, face, view_width=58.0, center_y=68.0)

    clips = {
        "default": PortraitClip.still(portrait_frame("idle", 1, 8)),
        "talk": PortraitClip(tuple(portrait_frame("talk", i, 8) for i in range(8)), duration_ms=110, looping=True),
        "paradox": PortraitClip(tuple(portrait_frame("paradox_loop", i, 8) for i in range(8)), duration_ms=96, looping=True),
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
        sheet_tuning={"collision_scale": 1.8},
        animation_key_map={row[0]: row[0] for row in ROWS},
        trim=True,
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    return [Path(outputs[key]) for key in keys if outputs.get(key)]


def render_canonical(out_dir: str | Path, **opts):
    del opts
    return write_canonical(TARGET_NAME, ROWS, render_frame, Path(out_dir), frame_size=FRAME_SIZE)


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
