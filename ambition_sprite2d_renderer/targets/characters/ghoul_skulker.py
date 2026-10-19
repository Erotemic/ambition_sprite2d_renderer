"""The Ghoul Skulker: a stitched corpse in a burial shroud, hunched, its long arms hanging to its shins.

An SVG rig. The drawing is ``data/characters/ghoul_skulker/ghoul_skulker.svg``
(``scripts/svg_art/ghoul_skulker_art.py``), and the skeleton and the rows are
``rigged/ghoul_skulker/ghoul_skulker.rig.json`` (``scripts/build_ghoul_skulker_rig.py``).

Jon, 2026-10-18, of three redraws of the ghoul: "B for default skulker". B
is a stitched corpse in a burial shroud: blue-grey skin, a stitched seam
across the chest and round the shoulder, the shroud as a hood and a wrap at
the hips. The old read is kept: a crouched creeping wretch, a hooked nose,
moustache tendrils, a loincloth, bony limbs and clawed hands. The two other
looks are drawn by the art script and cast nowhere.

The rows are the seven it has always had: ``idle``, ``skulk``, ``claw``,
``pounce``, ``cackle``, ``hurt``, ``death``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ambition_sprite2d_renderer.authoring.part_flipbook import publish_rig_flipbook
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

TARGET_NAME = "ghoul_skulker"
RIG_PATH = Path(__file__).resolve().parent / "rigged" / TARGET_NAME / "ghoul_skulker.rig.json"

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_ghoul_skulker",
        "display_name": "Ghoul Skulker",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "LowProfile",
        "mass_class": "Light",
        "locomotion_hint": "Skulk",
        "traits": ["enemy", "undead", "skulker", "clawed", "low_profile"],
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": {
                "height_px": None,
                "distance_px": None,
                "source": "ghoul_pounce_animation",
            },
            "climb": None,
            "crawl": True,
            "fly": None,
            "swim": None,
            "use_lifts": None,
            "door_access": [],
        },
        "interactions": {
            "talk": None,
            "trade": None,
            "carry": None,
            "open_doors": [],
        },
    },
    "brain": {"default_preset": "melee_brute_striker"},
    "actions": {"default_preset": "striker_swipe"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.skulk": {"animation": "skulk", "events": []},
        "action.melee.primary": {
            "animation": "claw",
            "events": [
                {
                    "t": 0.34,
                    "event": "hitbox_active_start",
                    "source": "ghoul_skulker.claw",
                },
                {
                    "t": 0.58,
                    "event": "hitbox_active_end",
                    "source": "ghoul_skulker.claw",
                },
            ],
        },
        "action.special.pounce": {
            "animation": "pounce",
            "events": [
                {"t": 0.25, "event": "leap_commit", "source": "ghoul_skulker.pounce"},
                {
                    "t": 0.54,
                    "event": "hitbox_active_start",
                    "source": "ghoul_skulker.pounce",
                },
                {
                    "t": 0.70,
                    "event": "hitbox_active_end",
                    "source": "ghoul_skulker.pounce",
                },
            ],
        },
        "interaction.cackle": {"animation": "cackle", "events": []},
        "damage.hit": {"animation": "hurt", "events": []},
        "lifecycle.death": {"animation": "death", "events": []},
    },
    "sockets": {
        "head": {"source": "ghoul_skulker.geometry", "point": {"x": 150.0, "y": 102.0}},
        "mouth": {
            "source": "ghoul_skulker.geometry",
            "point": {"x": 158.0, "y": 113.0},
        },
        "hand_l": {
            "source": "ghoul_skulker.geometry",
            "point": {"x": 125.0, "y": 189.0},
        },
        "hand_r": {
            "source": "ghoul_skulker.geometry",
            "point": {"x": 140.0, "y": 190.0},
        },
        "claw_tip": {
            "source": "ghoul_skulker.geometry",
            "point": {"x": 142.0, "y": 195.0},
        },
        "pounce_origin": {
            "source": "ghoul_skulker.geometry",
            "point": {"x": 112.0, "y": 179.0},
        },
    },
    "tags": ["enemy", "undead", "skulker"],
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
