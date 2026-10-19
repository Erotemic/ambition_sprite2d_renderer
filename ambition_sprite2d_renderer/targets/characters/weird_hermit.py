"""The Weird Hermit: a hunched old man with a red head rag, an absurdly long nose and long fingers.

An SVG rig. The drawing is ``data/characters/weird_hermit/weird_hermit.svg``
(``scripts/svg_art/weird_hermit_art.py``), and the skeleton and the rows are
``rigged/weird_hermit/weird_hermit.rig.json`` (``scripts/build_weird_hermit_rig.py``).

Jon, 2026-10-18, called the old hermit "old bad art"; of three redraws he
chose B ("I like B as the default. Keep the others too"): sun-baked skin, a
red rag knotted behind, wiry grey hair and moustache, patched green shorts on
a rope belt. The old read is kept: the hunch, the nose, the ribs and pot
belly, the knobby knees, the long fingers, and a curse he sneezes. The two
other looks are drawn by the art script and cast nowhere.

The rows are the seven he has always had: ``idle``, ``creep``,
``finger_jab``, ``grab``, ``curse_sneeze``, ``hurt``, ``death``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ambition_sprite2d_renderer.authoring.part_flipbook import publish_rig_flipbook
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

TARGET_NAME = "weird_hermit"
RIG_PATH = Path(__file__).resolve().parent / "rigged" / TARGET_NAME / "weird_hermit.rig.json"

ACTOR_METADATA = {
    "actor": {"character_id": "npc_weird_hermit", "display_name": "Weird Hermit"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": ["story", "humanoid", "hermit", "sideways_seer"],
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
    "tags": ["story", "humanoid", "hermit", "sideways_seer"],
    "sockets": {
        "head": {"source": "explicit.profile.humanoid", "point": {"x": 147.0, "y": 90.0}},
        "chest": {"source": "explicit.profile.humanoid", "point": {"x": 131.0, "y": 129.0}},
        "hand_l": {"source": "explicit.profile.humanoid", "point": {"x": 133.0, "y": 157.0}},
        "hand_r": {"source": "explicit.profile.humanoid", "point": {"x": 158.0, "y": 156.0}},
        "speech_bubble": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 147.0, "y": 65.0},
        },
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "creep", "events": []},
        "action.melee.primary": {"animation": "finger_jab", "events": []},
        "action.melee.secondary": {"animation": "grab", "events": []},
        "action.cast": {"animation": "curse_sneeze", "events": []},
        "interaction.talk": {"animation": "idle", "events": []},
        "interaction.use": {"animation": "grab", "events": []},
        "damage.hit": {"animation": "hurt", "events": []},
        "damage.death": {"animation": "death", "events": []},
    },
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
