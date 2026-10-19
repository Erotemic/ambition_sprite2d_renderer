"""The Creator: the player's maker, a silver-haired researcher in a long navy coat and a violet scarf.

An SVG rig. The drawing is ``data/characters/creator/creator.svg``
(``scripts/svg_art/creator_art.py``), and the skeleton and the rows are
``rigged/creator/creator.rig.json`` (``scripts/build_creator_rig.py``).

Who he is (docs/storylines/cannon_expansions.md I2-I7): an independent
researcher in a basement lab, "not a grand genius - just some guy", a man of
about 50. The robed mystic with a halo and a blank geometric face he used to
be was not someone the story supports. Jon, 2026-10-18, of three redraws:
"B for creator ... keep the rest". B keeps today's navy and violet: a long
navy coat, a violet scarf, silver swept-back hair and a trimmed beard, a
glowing pendant (today's chest sigil) and a tablet (today's pale card). The
two other looks are drawn by the art script and cast nowhere.

The rows are the four he has always had: ``idle``, ``speak``, ``gesture``,
``walk``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ambition_sprite2d_renderer.authoring.part_flipbook import publish_rig_flipbook
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

TARGET_NAME = "creator"
RIG_PATH = Path(__file__).resolve().parent / "rigged" / TARGET_NAME / "creator.rig.json"

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_creator",
        "display_name": "Creator",
        "actor_id": "creator",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": ["story", "humanoid", "intro", "story", "creator"],
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
    "tags": ["story", "humanoid", "intro", "story", "creator"],
    "sockets": {
        "head": {"source": "explicit.profile.humanoid", "point": {"x": 77.2, "y": 43.9}},
        "chest": {"source": "explicit.profile.humanoid", "point": {"x": 73.0, "y": 81.0}},
        "hand_l": {"source": "explicit.profile.humanoid", "point": {"x": 65.4, "y": 114.0}},
        "hand_r": {"source": "explicit.profile.humanoid", "point": {"x": 89.8, "y": 104.1}},
        "speech_bubble": {"source": "explicit.profile.humanoid", "point": {"x": 77.2, "y": 19.2}},
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
    },
    "missing_information": [
        "Creator story-presence state is intentionally authored outside the "
        "renderer sidecar."
    ],
}


@lru_cache(maxsize=1)
def _doc() -> RigDocument:
    return RigDocument.load(RIG_PATH)


def _render_frame(animation: str, frame_idx: int, frame_count: int):
    return _doc().render_frame(animation, frame_idx, frame_count)


def render(out_dir: str | Path, **opts):
    del opts
    doc = _doc()
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME,
        rows=doc.rows(),
        render_fn=_render_frame,
        out_dir=Path(out_dir),
        frame_size=(int(doc.data["frame"]["width"]), int(doc.data["frame"]["height"])),
        auto_crop=True,
        crop_margin=4,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning=doc.sprite_tuning,
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    parts = publish_rig_flipbook(TARGET_NAME, doc.rows(), _render_frame, outputs, frame_transform, Path(out_dir))
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())


__all__ = ["ACTOR_METADATA", "render"]
