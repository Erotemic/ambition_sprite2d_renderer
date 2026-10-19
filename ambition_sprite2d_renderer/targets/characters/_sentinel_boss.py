"""The three sentinel bosses: one skeleton, one set of rows, three drawings.

Each look is an SVG rig: its drawing is ``data/characters/<target>/<target>.svg``
(``scripts/svg_art/sentinel_boss_art.py``) and its skeleton and rows are
``rigged/<target>/<target>.rig.json`` (``scripts/build_sentinel_boss_rigs.py``).
The target modules (``gradient_sentinel_boss``, ``clockwork_warden_boss``,
``hooded_sentinel_boss``) each call :func:`render` with their own name.

They replace the generic v1 boss (``boss``, ``boss_side.py``), whose rows,
attacks and hurtbox split they keep: the arms sweep and slam, so the
hurtbox is the head and the cloak and never the arms.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, List

from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.rigdoc import RigDocument
from ...authoring.sheet_build import build_sheet

RIGGED = Path(__file__).resolve().parent / "rigged"

# Authored in the pixels of the 288 x 272 frame every look is drawn on (the
# rig's ``frame``), before the sheet crops it.

#: The hood, and the cloak below it: both inside the arms' reach.
HEAD = {"name": "head", "x": 116, "y": 47, "w": 66, "h": 74,
        "poly": [(123.0, 52.0), (160.0, 47.0), (180.0, 64.0), (182.0, 100.0), (168.0, 118.0), (132.0, 121.0), (118.0, 100.0), (116.0, 74.0)]}
BODY = {"name": "body", "x": 94, "y": 112, "w": 82, "h": 98,
        "poly": [(124.0, 112.0), (168.0, 112.0), (176.0, 140.0), (176.0, 195.0), (144.0, 210.0), (94.0, 200.0), (102.0, 160.0), (110.0, 128.0)]}

ATTACK_HITBOXES = {
    # The claws strike the floor in front of and behind him.
    "floor_slam": {"bbox": (54, 200, 180, 56)},
    # Both arms flung out level, one to each side.
    "side_sweep": {"parts": [{"name": "left", "x": 36, "y": 104, "w": 64, "h": 52},
                             {"name": "right", "x": 196, "y": 104, "w": 68, "h": 52}]},
    # The ring he throws out, as four boxes so its corners are not damaging.
    "spike_halo": {"parts": [{"name": "top", "x": 56, "y": 30, "w": 176, "h": 40},
                             {"name": "bottom", "x": 56, "y": 200, "w": 176, "h": 40},
                             {"name": "left", "x": 42, "y": 60, "w": 40, "h": 150},
                             {"name": "right", "x": 206, "y": 60, "w": 40, "h": 150}]},
    # A lane along his dash, low enough to jump.
    "dash_echo": {"bbox": (0, 110, 288, 64)},
}

#: ``hit`` keeps the rest pair, so the stunned boss can still be struck;
#: ``death`` has none.
HURTBOX_PARTS = {anim: {"parts": [dict(HEAD), dict(BODY)]}
                 for anim in ("rest", "floor_slam", "side_sweep", "spike_halo", "dash_echo", "hit")}


def actor_metadata(target: str, display_name: str, inspirations: List[str]) -> Dict:
    return {
        "actor": {"character_id": target, "display_name": display_name},
        "authoring_description": {
            "visual_inspirations": inspirations,
            "rigging_notes": ["The SVG owns the part shapes. The rig owns the joints and motion."],
        },
        "body": {"body_plan": "BossMultipart", "body_kind": "Wide", "mass_class": "Boss", "traits": ["boss"],
                 "locomotion_hint": "BossKinematic"},
        "brain": {"default_preset": "stand_still"},
        "actions": {"default_preset": "peaceful"},
        "visual": {"default_pose": "rest"},
        "animation_bindings": {
            "default": {"animation": "rest", "events": []},
            "action.melee.primary": {"animation": "floor_slam", "events": [
                {"t": 0.38, "event": "hitbox_active_start", "source": "explicit.profile.boss"},
                {"t": 0.64, "event": "hitbox_active_end", "source": "explicit.profile.boss"}]},
            "action.ranged.primary": {"animation": "spike_halo", "events": [
                {"t": 0.5, "event": "projectile_release", "source": "explicit.profile.boss"}]},
        },
        "sockets": {
            "center": {"source": "sentinel_boss.geometry", "point": {"x": 144.0, "y": 146.0}},
            "projectile_origin": {"source": "sentinel_boss.geometry", "point": {"x": 164.0, "y": 83.0}},
        },
        "tags": ["boss", "svg_rigged"],
    }


@lru_cache(maxsize=None)
def _doc(target: str) -> RigDocument:
    return RigDocument.load(RIGGED / target / f"{target}.rig.json")


def render(target: str, metadata: Dict, out_dir: str | Path):
    doc = _doc(target)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    def render_frame(animation: str, frame_idx: int, frame_count: int):
        return doc.render_frame(animation, frame_idx, frame_count)

    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=target,
        rows=doc.rows(),
        render_fn=render_frame,
        out_dir=out_dir,
        frame_size=(int(doc.data["frame"]["width"]), int(doc.data["frame"]["height"])),
        label_width=100,
        auto_crop=True,
        crop_margin=4,
        actor_metadata=metadata,
        sheet_tuning=doc.sprite_tuning,
        attack_hitboxes=ATTACK_HITBOXES,
        hurtbox_parts=HURTBOX_PARTS,
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    parts = publish_rig_flipbook(target, doc.rows(), render_frame, outputs, frame_transform, out_dir)
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())
