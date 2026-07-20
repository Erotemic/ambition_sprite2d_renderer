from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Tuple

from ambition_sprite2d_renderer.authoring.portrait import (
    FaceGuide,
    PortraitClip,
    render_framed_portrait,
    write_portrait_sheet,
)
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

TARGET_NAME = "neil_ongras_turfson"
FRAME_SIZE = (128, 128)

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 145),
    ("walk", 8, 104),
    ("run", 8, 76),
    ("crouch", 6, 92),
    ("jump", 6, 84),
    ("fall", 6, 92),
    ("land", 6, 76),
    ("talk", 8, 104),
    ("interact", 8, 90),
    ("point_sky", 8, 80),
    ("cosmic_lecture", 10, 82),
    ("kneel", 8, 88),
    ("touch_grass", 10, 84),
    ("grass_sweep", 8, 76),
    ("block", 6, 82),
    ("hit", 5, 88),
    ("celebrate", 8, 88),
    ("taunt", 8, 94),
]

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_neil_ongras_turfson",
        "display_name": "Neil onGras Turfson",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": [
            "story",
            "humanoid",
            "scientist",
            "cosmic_naturalist",
            "touch_grass",
        ],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": True,
            "climb": None,
            "fly": None,
            "swim": None,
            "crawl": False,
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
        "portrait_style": "dialog_closeup",
        "portrait_source": TARGET_NAME,
        "animation_bindings": {
            "default": {"animation": "idle", "events": []},
            "locomotion.walk": {"animation": "walk", "events": []},
            "locomotion.run": {"animation": "run", "events": []},
            "traversal.jump": {"animation": "jump", "events": []},
            "traversal.fall": {"animation": "fall", "events": []},
            "interaction.talk": {"animation": "talk", "events": []},
            "interaction.use": {"animation": "interact", "events": []},
            "emote.point": {"animation": "point_sky", "events": []},
            "ability.cosmic_lecture": {"animation": "cosmic_lecture", "events": []},
            "ability.touch_grass": {"animation": "touch_grass", "events": []},
            "ability.grass_sweep": {"animation": "grass_sweep", "events": []},
            "action.defense.block": {"animation": "block", "events": []},
            "emote.taunt": {"animation": "taunt", "events": []},
        },
    },
}

RIG_DIR = Path(__file__).resolve().parent / "rigged" / TARGET_NAME
DOC_FILE = RIG_DIR / "neil_ongras_turfson_three_quarter.rig.json"


@lru_cache(maxsize=1)
def _doc() -> RigDocument:
    return RigDocument.load(DOC_FILE)


def _render_frame(animation: str, frame_idx: int, frame_count: int):
    return _doc().render_frame(animation, frame_idx, frame_count)


def render_portraits(out_dir: str | Path, **opts):
    del opts
    doc = _doc()

    def portrait_frame(animation: str, frame_idx: int, frame_count: int):
        source = doc.render_at(
            animation,
            doc.frame_time(animation, frame_idx, frame_count),
            supersample=2,
            scale=3,
        )
        face = FaceGuide(
            center_x=64.0,
            center_y=23.0,
            width=40.0,
            height=38.0,
            source_width=float(doc.frame["width"]),
            source_height=float(doc.frame["height"]),
        )
        return render_framed_portrait(
            source,
            face,
            view_width=58.0,
            center_y=42.0,
        )

    clips = {
        "default": PortraitClip.still(portrait_frame("idle", 2, 8)),
        "talking": PortraitClip(
            tuple(portrait_frame("talk", frame, 8) for frame in (0, 2, 4, 6)),
            duration_ms=100,
            looping=True,
        ),
        "lecture": PortraitClip(
            tuple(
                portrait_frame("cosmic_lecture", frame, 10)
                for frame in (0, 2, 5, 7)
            ),
            duration_ms=90,
            looping=True,
        ),
        "inspecting": PortraitClip.still(portrait_frame("interact", 4, 8)),
    }
    return write_portrait_sheet(TARGET_NAME, clips, Path(out_dir))


def render(out_dir: str | Path, **opts):
    del opts
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=_render_frame,
        out_dir=Path(out_dir),
        frame_size=FRAME_SIZE,
        auto_crop=True,
        crop_margin=4,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning={"collision_scale": 1.65},
        trim=False,
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


__all__ = ["ACTOR_METADATA", "render", "render_portraits"]
