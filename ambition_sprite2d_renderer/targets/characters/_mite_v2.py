"""The mites, v2: what the two SVG-rig mite targets share.

The drawings are ``data/characters/<name>/<name>_side.svg``
(``scripts/svg_art/mites_art.py``, the cast mode), and the skeletons and rows
are ``rigged/<name>/<name>_side.rig.json`` (``scripts/build_mite_v2_rigs.py``).
A target module names its mite and its actor contract; this module renders
the sheet. The game draws the rows ``idle``, ``walk``, ``run``, ``slash``,
``hit``, ``death`` and ``dash``, as it did for the first mites (robot-toon
configs ``configs/dividing_mite.yaml`` and ``configs/exploding_mite.yaml``,
which stay renderable).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict

from ambition_sprite2d_renderer.authoring.part_flipbook import publish_rig_flipbook
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

RIGGED = Path(__file__).resolve().parent / "rigged"


@lru_cache(maxsize=4)
def doc(name: str) -> RigDocument:
    return RigDocument.load(RIGGED / name / f"{name}_side.rig.json")


def frame_point(name: str, x: float, y: float) -> Dict[str, float]:
    """A point of the drawing (SVG units) in the rig frame's pixels."""
    d = doc(name)
    fr, scale = d.data["frame"], float(d.data["svg_source"]["scale"])
    return {"x": round(fr["center_x"] + (x - 200.0) * scale, 1), "y": round(fr["ground_y"] + (y - 354.0) * scale, 1)}


def actor_metadata(name: str, *, character_id: str, display_name: str, mass_class: str, trait: str,
                   live: tuple, head: tuple, chest: tuple, jaws: tuple, notes: list) -> dict:
    """The actor contract of a mite: the old config's, its body a crawler."""
    traits = ["robot", "enemy", "combatant", "mite", trait, "crawler", "no_hands"]
    return {
        "actor": {"character_id": character_id, "display_name": display_name},
        "authoring_description": {"rigging_notes": notes},
        "body": {"body_plan": "Crawler", "body_kind": "Crawler", "mass_class": mass_class, "traits": traits, "locomotion_hint": "Walk"},
        "capabilities": {
            "traversal": {"walk": True, "jump": None, "climb": None, "fly": None, "swim": None, "crawl": None,
                          "use_lifts": True, "door_access": ["public"]},
            "interactions": {"talk": None, "trade": None, "carry": None, "open_doors": ["public"]},
        },
        "brain": {"default_preset": "melee_brute_striker"},
        "actions": {"default_preset": "striker_swipe"},
        "visual": {"default_pose": "idle"},
        "animation_bindings": {
            "default": {"animation": "idle", "events": []},
            "locomotion.walk": {"animation": "walk", "events": []},
            "action.melee.primary": {"animation": "slash", "events": [
                {"t": live[0], "event": "hitbox_active_start", "source": "explicit.profile.mite_mandibles"},
                {"t": live[1], "event": "hitbox_active_end", "source": "explicit.profile.mite_mandibles"},
            ]},
        },
        "sockets": {
            "head": {"source": "explicit.profile.mite", "point": frame_point(name, *head)},
            "chest": {"source": "explicit.profile.mite", "point": frame_point(name, *chest)},
            "weapon_grip": {"source": "explicit.profile.mite", "point": frame_point(name, *jaws)},
        },
        "tags": traits + ["svg_rigged"],
    }


def body_box(name: str, x0: float, y0: float, x1: float, y1: float) -> tuple:
    """The body (the shell or the lobes and the legs; not a feeler or the fuse)
    from a box of the drawing (SVG units) to frame pixels."""
    a, b = frame_point(name, x0, y0), frame_point(name, x1, y1)
    return (a["x"], a["y"], b["x"], b["y"])


def render(name: str, actor: dict, box: tuple, out_dir: str | Path):
    """The sheet. The body is the authored ``box`` in every row: the game
    sizes a mite by it (the catalog's ``standing_height``), so a feeler or the
    fuse does not make the mite taller or its body larger."""
    d = doc(name)

    def body_metrics(fw: int, fh: int) -> dict:
        x0, y0, x1, y1 = box
        x, y, w, h = int(round(x0)), int(round(y0)), int(round(x1 - x0)), int(round(y1 - y0))
        feet = (x + w / 2.0, float(y + h))
        return {
            "body_pixel_bbox": {"x": x, "y": y, "w": w, "h": h},
            "feet_pixel": {"x": feet[0], "y": feet[1]},
            "feet_anchor_norm": {"x": round((feet[0] - fw / 2.0) / fw, 6), "y": round((fh / 2.0 - feet[1]) / fh, 6)},
        }

    def frame(animation: str, frame_idx: int, frame_count: int):
        return d.render_frame(animation, frame_idx, frame_count)

    rows = d.rows()
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=name,
        rows=rows,
        render_fn=frame,
        out_dir=Path(out_dir),
        frame_size=(int(d.data["frame"]["width"]), int(d.data["frame"]["height"])),
        # The frame is authored, so the body box is in its pixels.
        auto_crop=False,
        actor_metadata=actor,
        body_metrics_fn=body_metrics,
        sheet_tuning=d.sprite_tuning,
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    parts = publish_rig_flipbook(name, rows, frame, outputs, frame_transform, Path(out_dir))
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())
