"""The Mantis Lancer: a slender green conehead mantis on four legs, its blades held in the praying guard.

An SVG rig. The drawing is ``data/characters/mantis_lancer/mantis_lancer.svg``
(``scripts/svg_art/mantis_lancer_art.py``), and the skeleton and the rows are
``rigged/mantis_lancer/mantis_lancer.rig.json`` (``scripts/build_mantis_lancer_rig.py``).

Jon, 2026-10-18, called the old mantis "old bad art"; of three redraws he
chose A ("A is good for default mantis"): a slender conehead mantis standing
on four legs, its red crest the cone of its head. The old read is kept: the
red crest, the raptorial blades, a long stab, a sweeping slash and a pouncing
leap. The two other looks are drawn by the art script and cast nowhere.

The rows are the seven it has always had: ``idle``, ``walk``, ``stab``,
``slash``, ``pounce``, ``hurt``, ``death``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ambition_sprite2d_renderer.authoring.part_flipbook import publish_rig_flipbook
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

TARGET_NAME = "mantis_lancer"
RIG_PATH = Path(__file__).resolve().parent / "rigged" / TARGET_NAME / "mantis_lancer.rig.json"

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_mantis_lancer",
        "display_name": "Mantis Lancer",
    },
    "body": {
        "body_plan": "InsectoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "locomotion_hint": "Walk",
        "traits": ["enemy", "insectoid", "blade_arms", "lancer"],
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": {"height_px": None, "distance_px": None, "source": "mantis_pounce_animation"},
            "climb": True,
            "crawl": None,
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
    "actions": {"default_preset": "brute_lunge"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "action.melee.primary": {
            "animation": "stab",
            "events": [
                {"t": 0.36, "event": "hitbox_active_start", "source": "mantis_lancer.stab"},
                {"t": 0.60, "event": "hitbox_active_end", "source": "mantis_lancer.stab"},
            ],
        },
        "action.melee.sweep": {
            "animation": "slash",
            "events": [
                {"t": 0.30, "event": "hitbox_active_start", "source": "mantis_lancer.slash"},
                {"t": 0.62, "event": "hitbox_active_end", "source": "mantis_lancer.slash"},
            ],
        },
        "action.special.pounce": {"animation": "pounce", "events": [{"t": 0.40, "event": "leap_commit", "source": "mantis_lancer.pounce"}]},
        "damage.hit": {"animation": "hurt", "events": []},
        "lifecycle.death": {"animation": "death", "events": []},
    },
    "sockets": {
        "head": {"source": "mantis_lancer.geometry", "point": {"x": 158.0, "y": 100.5}},
        "thorax": {"source": "mantis_lancer.geometry", "point": {"x": 128.0, "y": 165.5}},
        "blade_l": {"source": "mantis_lancer.geometry", "point": {"x": 161.5, "y": 138.0}},
        "blade_r": {"source": "mantis_lancer.geometry", "point": {"x": 169.5, "y": 138.0}},
        "blade_tip": {"source": "mantis_lancer.geometry", "point": {"x": 182.0, "y": 120.0}},
        "pounce_origin": {"source": "mantis_lancer.geometry", "point": {"x": 128.0, "y": 203.0}},
    },
    "tags": ["enemy", "insectoid", "lancer"],
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
