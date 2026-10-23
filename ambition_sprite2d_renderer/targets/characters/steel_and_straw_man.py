"""The Steel Man and the Straw Man: two SVG rigs, one set of rows.

Jon asked (2026-10-23) for two new characters for the philosophical positions
of the game: the Steel Man (the opposing argument at its strongest, to respect
while disagreeing) and the Straw Man (comic relief, the misrepresentation that
is easy to knock down). They are NOT the Tin Man and the Scarecrow:

* ``steel_man``: the girder: blued plate riveted over red-lead I-beam limbs,
  pin-bolted joints, footings bolted down like a column's, a brass builder's
  plate on his chest, a calm face. 196 cm.
* ``straw_man``: the sheaf: wheat bound in jute at the neck, the waist, the
  knees and the ankles, an ear-of-wheat quiff, the blue first-prize rosette
  he gave himself, straws working loose. 185 cm.

Each drawing is ``data/characters/<id>/<id>.svg`` (the side view in the left
cell, the front view in the right cell) and each rig
``rigged/<id>/<id>.rig.json``; ``scripts/build_steel_and_straw_man_rigs.py``
writes both from ``scripts/svg_art/steel_and_straw_man_art.py``, which also
keeps the uncast looks. The rows are ``idle``, ``walk``, ``talk``,
``interact`` and ``hurt``. Nothing in the game draws them yet (no catalog row).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict

from ambition_sprite2d_renderer.authoring.part_flipbook import publish_rig_flipbook
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

RIGGED = Path(__file__).resolve().parent / "rigged"

#: target id -> (catalog id, display name, traits)
CAST: Dict[str, tuple] = {
    "steel_man": ("npc_steel_man", "The Steel Man", ["humanoid", "construct", "philosophy", "steady"]),
    "straw_man": ("npc_straw_man", "The Straw Man", ["humanoid", "construct", "philosophy", "comic"]),
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
    character_id, display, traits = CAST[target]
    J = _joints(_doc(target))
    hx, hy = J["head"]

    def pt(p):
        return {"source": "explicit.profile.humanoid", "point": {"x": round(p[0], 1), "y": round(p[1], 1)}}

    return {
        "actor": {"character_id": character_id, "display_name": display},
        "body": {"body_plan": "HumanoidBiped", "body_kind": "Standard", "mass_class": "Heavy" if target == "steel_man" else "Light",
                 "traits": traits, "locomotion_hint": "Walk"},
        "capabilities": {
            "traversal": {"walk": True, "jump": None, "climb": None, "fly": None, "swim": None, "crawl": None, "use_lifts": True,
                          "door_access": ["public"]},
            "interactions": {"talk": True, "trade": None, "carry": None, "open_doors": ["public"]},
        },
        "brain": {"default_preset": "patrol_peaceful"},
        "actions": {"default_preset": "peaceful"},
        "visual": {"default_pose": "idle"},
        "tags": traits + ["svg_rigged"],
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
