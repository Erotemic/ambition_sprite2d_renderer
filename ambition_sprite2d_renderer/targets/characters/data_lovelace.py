"""Data Lovelace sprite target.

A bespoke robot parody of Ada Lovelace built through the SVG rig route.
She reads as an elegant Victorian automaton rather than a generic sci-fi robot:
brass bodywork, teal analytical-engine trim, punch-card halos, and a dress-like
mechanical silhouette. No drop shadows are used.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Tuple

from ...authoring.portrait import FaceGuide, PortraitClip, render_framed_portrait, write_portrait_sheet
from ...authoring.rigdoc import RigDocument
from ...authoring.sheet_build import build_sheet, write_canonical

TARGET_NAME = "data_lovelace"
RIG_PATH = Path(__file__).with_name("data_lovelace.rig.json")
FRAME_SIZE = (320, 320)
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 130),
    ("walk", 8, 102),
    ("talk", 8, 110),
    ("compute", 8, 92),
    ("analytical_burst", 8, 88),
    ("self_repair", 8, 96),
    ("death", 8, 116),
]

ACTOR_METADATA = {
    "actor": {"character_id": "npc_data_lovelace", "display_name": "Data Lovelace"},
    "visual": {"default_pose": "idle"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Slim",
        "mass_class": "Light",
        "traits": ["robot", "automaton", "computing", "victorian", "playable_candidate"],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {"walk": True, "jump": True, "climb": None, "fly": None, "swim": None, "crawl": False, "use_lifts": True, "door_access": ["public"]},
        "interactions": {"talk": True, "trade": None, "carry": None, "open_doors": ["public"]},
    },
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "peaceful"},
    "tags": ["robot", "automaton", "computing", "victorian", "playable_candidate"],
    "sockets": {
        "head": {"source": "explicit.profile.humanoid", "point": {"x": 80.0, "y": 30.0}},
        "chest": {"source": "explicit.profile.humanoid", "point": {"x": 80.0, "y": 86.0}},
        "hand_l": {"source": "explicit.profile.humanoid", "point": {"x": 31.0, "y": 122.0}},
        "hand_r": {"source": "explicit.profile.humanoid", "point": {"x": 129.0, "y": 122.0}},
        "speech_bubble": {"source": "explicit.profile.humanoid", "point": {"x": 80.0, "y": 6.0}},
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "self_repair", "events": []},
        "action.special.primary": {"animation": "compute", "events": []},
        "action.special.secondary": {"animation": "analytical_burst", "events": []},
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
            center_y=51.0,
            width=36.0,
            height=38.0,
            source_width=float(doc.frame["width"]),
            source_height=float(doc.frame["height"]),
        )
        return render_framed_portrait(source, face, view_width=60.0, center_y=69.0)

    clips = {
        "default": PortraitClip.still(portrait_frame("idle", 1, 8)),
        "talk": PortraitClip(tuple(portrait_frame("talk", i, 8) for i in range(8)), duration_ms=110, looping=True),
        "compute": PortraitClip(tuple(portrait_frame("compute", i, 8) for i in range(8)), duration_ms=92, looping=True),
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
        sheet_tuning={"collision_scale": 1.85},
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
