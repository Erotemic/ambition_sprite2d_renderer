"""The News Board v2: the Drain Market's talking notice board.

An SVG rig. The drawing is ``data/characters/news_board_v2/news_board_v2.svg``
(``scripts/svg_art/news_board_art.py``, look A, seen from the front), and the
skeleton and the rows are ``rigged/news_board_v2/news_board_v2.rig.json``
(``scripts/build_news_board_v2_rig.py``).

Jon, 2026-10-22: redesigned art for the news board; on 2026-10-23 he asked to
see it in the game. Look A is cast because the board stands on the street of
the Drain Market (``drain_alley``): planks on two old drain pipes under a
pitched tin roof, a cork field of pinned notices, and a PA horn wired to the
roof, which is its voice. Its news is pictures, never words: the lab wall with
a hole in it, a smoke cloud with a halo, a researcher in crosshairs, a red
rubber stamp.

The rows: ``idle`` (the loose slip lifts in a draught) and ``talk`` (the horn
kicks on each word, its rings of sound show in turn). The old procedural board
(``targets/props/news_board.py``) stays renderable.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ambition_sprite2d_renderer.authoring.part_flipbook import publish_rig_flipbook
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

TARGET_NAME = "news_board_v2"
RIG_PATH = Path(__file__).resolve().parent / "rigged" / TARGET_NAME / f"{TARGET_NAME}.rig.json"

ACTOR_METADATA = {
    "actor": {"character_id": "npc_news_board", "display_name": "News Board"},
    "body": {
        "body_plan": "PropActor",
        "body_kind": "PropLike",
        "mass_class": "Static",
        "traits": ["prop_like", "talks"],
    },
    "capabilities": {
        "traversal": {"walk": None, "jump": None, "climb": None, "fly": None, "swim": None, "crawl": None, "use_lifts": None},
        "interactions": {"talk": True, "trade": None, "carry": None},
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "visual": {"default_pose": "idle"},
    "tags": ["intro", "prop_like"],
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
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
