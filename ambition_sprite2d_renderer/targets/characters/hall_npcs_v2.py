"""Five hall NPCs redrawn as SVG rigs: one skeleton, one set of rows.

Jon asked (2026-10-22) for new art for the Architect, the Manifest Clerk, the
Vault Keeper, the Merchant Prototype and the General Hero, and the looks were
decided 2026-10-23. A major redesign is a new target, so the old toon targets
(``architect``, ``vault_keeper``, ``merchant_prototype``, ``general_hero``)
stay renderable beside these:

* ``architect_v2``: the modernist: a dark suit, round glasses, a violet bow
  tie, the roll of drawings under his arm;
* ``manifest_clerk``: the old registrar in a long cardigan coat, half-moon
  glasses, the fanfold manifest from his fist to a heap on the floor (before
  this he wore the Architect's sheet);
* ``vault_keeper_v2``: the keeper of the vault: a wine-red robe, bald, a black
  beard, a gold earring, the key-headed vault staff, the combination dial;
* ``merchant_prototype_v2``: the travelling pedlar, the whole shop on her back
  (an axe, a bomb, a health cell), a polka-dot headscarf, an apron, a blue skirt;
* ``general_hero_v2``: the knight who came back: a breastplate, a blue cape, a
  blond beard, standing watch with both hands on his planted sword.

Each drawing is ``data/characters/<id>/<id>.svg`` and each rig
``rigged/<id>/<id>.rig.json``; ``scripts/build_hall_npc_v2_rigs.py`` writes
both (from ``scripts/svg_art/architect_and_clerk_art.py`` and
``scripts/svg_art/vault_merchant_hero_art.py``). The rows are ``idle``,
``walk``, ``talk``, ``interact`` and ``hurt``; the General Hero also has
``slash`` and ``celebrate``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict

from ambition_sprite2d_renderer.authoring.part_flipbook import publish_rig_flipbook
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

RIGGED = Path(__file__).resolve().parent / "rigged"

#: target id -> (display name, traits)
CAST: Dict[str, tuple] = {
    "architect_v2": ("Architect", ["hub", "guide", "humanoid", "builder"]),
    "manifest_clerk": ("Manifest Clerk", ["intro", "utility", "humanoid", "clerk"]),
    "vault_keeper_v2": ("Vault Keeper", ["hub", "guide", "humanoid", "keeper"]),
    "merchant_prototype_v2": ("Merchant Prototype", ["hub", "guide", "humanoid", "merchant"]),
    "general_hero_v2": ("General Hero", ["hub", "peaceful", "humanoid", "hero"]),
}

# The catalog row each target draws.
CATALOG_IDS: Dict[str, str] = {
    "architect_v2": "npc_architect",
    "manifest_clerk": "npc_manifest_clerk",
    "vault_keeper_v2": "npc_vault_keeper",
    "merchant_prototype_v2": "npc_merchant_prototype",
    "general_hero_v2": "npc_general_hero",
}


def _rig_path(target: str) -> Path:
    return RIGGED / target / f"{target}.rig.json"


@lru_cache(maxsize=None)
def _doc(target: str) -> RigDocument:
    return RigDocument.load(_rig_path(target))


def _joints(doc: RigDocument) -> Dict[str, tuple]:
    """Each bone's rest point in frame pixels (the bones' offsets summed)."""
    frame = doc.data["frame"]
    by_name = {b["name"]: b for b in doc.data["bones"]}
    out: Dict[str, tuple] = {}

    def at(name: str) -> tuple:
        if name not in out:
            b = by_name[name]
            px, py = at(b["parent"]) if b["parent"] else (frame["center_x"], frame["ground_y"])
            out[name] = (px + b["offset"][0], py + b["offset"][1])
        return out[name]

    for name in by_name:
        at(name)
    return out


def actor_metadata(target: str) -> dict:
    display, traits = CAST[target]
    J = _joints(_doc(target))
    hx, hy = J["head"]

    def pt(p):
        return {"source": "explicit.profile.humanoid", "point": {"x": round(p[0], 1), "y": round(p[1], 1)}}

    return {
        # The catalog row this art draws, as every other target names it.
        "actor": {"character_id": CATALOG_IDS[target], "display_name": display},
        "body": {"body_plan": "HumanoidBiped", "body_kind": "Standard", "mass_class": "Medium", "traits": traits, "locomotion_hint": "Walk"},
        "capabilities": {
            "traversal": {"walk": True, "jump": None, "climb": None, "fly": None, "swim": None, "crawl": None, "use_lifts": True,
                          "door_access": ["public"]},
            "interactions": {"talk": True, "trade": None, "carry": None, "open_doors": ["public"]},
        },
        "brain": {"default_preset": "patrol_peaceful"},
        "actions": {"default_preset": "peaceful"},
        "visual": {"default_pose": "idle"},
        "tags": traits + ["svg_rigged", "versioned_variant"],
        # Frame pixels, from the drawing's joints at rest.
        "sockets": {
            "head": pt((hx, hy - 20)),
            "chest": pt(((hx + J["torso"][0]) / 2, (hy + J["torso"][1]) / 2)),
            "hand_l": pt(J["far_hand"]),
            "hand_r": pt(J["near_hand"]),
            "speech_bubble": pt((hx, hy - 52)),
        },
        "animation_bindings": {
            "default": {"animation": "idle", "events": []},
            "locomotion.walk": {"animation": "walk", "events": []},
            "interaction.talk": {"animation": "talk", "events": []},
            "interaction.use": {"animation": "interact", "events": []},
        },
    }


def _make(target: str):
    def render_frame(animation: str, frame_idx: int, frame_count: int):
        return _doc(target).render_frame(animation, frame_idx, frame_count)

    def render(out_dir: str | Path, **opts):
        del opts
        doc = _doc(target)
        frame_transform: dict = {}
        outputs = build_sheet(
            frame_transform_out=frame_transform,
            target=target,
            rows=doc.rows(),
            render_fn=render_frame,
            out_dir=Path(out_dir),
            frame_size=(int(doc.data["frame"]["width"]), int(doc.data["frame"]["height"])),
            auto_crop=True,
            crop_margin=4,
            actor_metadata=actor_metadata(target),
            sheet_tuning=doc.sprite_tuning,
        )
        keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
        parts = publish_rig_flipbook(target, doc.rows(), render_frame, outputs, frame_transform, Path(out_dir))
        return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())

    return render


#: Only a target whose rig document is built registers.
TARGETS = {
    target: {"render": _make(target), "actor_metadata": actor_metadata(target)}
    for target in CAST
    if _rig_path(target).exists()
}

__all__ = ["CAST", "TARGETS", "actor_metadata"]
