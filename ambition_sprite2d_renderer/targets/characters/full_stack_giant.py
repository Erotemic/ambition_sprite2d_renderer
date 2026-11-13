"""Full Stack: the giant square robot built like a guitar amplifier stack, with an electric guitar.

An SVG rig. The drawing is ``data/characters/full_stack/full_stack.svg``
(``scripts/svg_art/full_stack_art.py``), and the skeleton and the rows are
``rigged/full_stack/full_stack.rig.json`` (``scripts/build_full_stack_rig.py``).

The game's design: ``docs/planning/game/final-boss.md``. It is the
bossofthegame's agent and the giant whose shoulders he stands on: a mount of
the class ``giant`` (``npc_full_stack``). THE ART IS THE BODY: the body box
is the amp head, the cabinet and the legs (``BODY_BOX`` of the art script),
at 1.25 world units to a pixel, and the top of the head and the guitar's edge
are the ground the catalog row states.
"""

from __future__ import annotations

import importlib.util
from functools import lru_cache
from pathlib import Path

from ambition_sprite2d_renderer.authoring.part_flipbook import publish_rig_flipbook
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

TARGET_NAME = "full_stack_giant"
RIG_PATH = Path(__file__).resolve().parent / "rigged" / "full_stack" / "full_stack.rig.json"
_ART = Path(__file__).resolve().parents[3] / "scripts" / "svg_art" / "full_stack_art.py"

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_full_stack",
        "display_name": "Full Stack",
        "actor_id": "full_stack",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Wide",
        "mass_class": "Heavy",
        "traits": ["mount", "giant", "robot", "agent", "final_boss"],
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
            "use_lifts": None,
            "door_access": [],
        },
        "interactions": {
            "talk": None,
            "trade": None,
            "carry": True,
            "open_doors": [],
        },
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "visual": {"default_pose": "idle"},
    "tags": ["mount", "giant", "robot", "agent", "final_boss"],
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
    },
    "missing_information": [
        "Its mount surfaces (the top, the guitar's edge) are stated by the game's catalog row, not published per frame."
    ],
}


@lru_cache(maxsize=1)
def _art():
    spec = importlib.util.spec_from_file_location("full_stack_art", _ART)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def _doc() -> RigDocument:
    return RigDocument.load(RIG_PATH)


def _render_frame(animation: str, frame_idx: int, frame_count: int):
    return _doc().render_frame(animation, frame_idx, frame_count)


def _body_metrics(fw: int, fh: int) -> dict:
    x0, y0, x1, y1 = _art().BODY_BOX
    x, y, w, h = int(x0), int(y0), int(x1 - x0), int(y1 - y0)
    feet = (x + w / 2.0, float(y + h))
    return {
        "body_pixel_bbox": {"x": x, "y": y, "w": w, "h": h},
        "feet_pixel": {"x": feet[0], "y": feet[1]},
        "feet_anchor_norm": {"x": round((feet[0] - fw / 2.0) / fw, 6), "y": round((fh / 2.0 - feet[1]) / fh, 6)},
    }


def render(out_dir: str | Path, **opts):
    del opts
    doc = _doc()
    frame = doc.data["frame"]
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME,
        rows=doc.rows(),
        render_fn=_render_frame,
        out_dir=Path(out_dir),
        frame_size=(int(frame["width"]), int(frame["height"])),
        # The frame is authored, so the body box is in its pixels.
        auto_crop=False,
        actor_metadata=ACTOR_METADATA,
        body_metrics_fn=_body_metrics,
        sheet_tuning=doc.sprite_tuning,
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    parts = publish_rig_flipbook(TARGET_NAME, doc.rows(), _render_frame, outputs, frame_transform, Path(out_dir))
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())


__all__ = ["ACTOR_METADATA", "render"]
