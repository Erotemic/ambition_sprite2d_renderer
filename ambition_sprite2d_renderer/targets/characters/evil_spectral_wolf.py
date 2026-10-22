"""The spectral wolf of Castle Godwin: a dog of the regime, dead and risen.

Jon, 2026-10-22: "I want you to create spectral wolf enemies", its fire "Red,
like the Inugami". Between its attacks it fades (faint, and the game makes it
intangible); it comes solid to lunge; when it dies it bursts into wisps.

The drawing is ``data/characters/evil_spectral_wolf/evil_spectral_wolf_side.svg``
(``scripts/svg_art/evil_spectral_wolf_art.py``): the attack hound's body made a
wolf, in the Inugami's spirit ink. The bones and the shared clips are the
hound's (``scripts/build_evil_spectral_wolf_rig.py``).

How faint each frame is (``opacity``) is authored here and drawn into the
frame: ``faded`` is faint, ``fade_out`` and ``fade_in`` go between, and the
spirit leaves it in ``death``. ``slash`` is the snapping bite, ``attack_side``
the leaping lunge, ``taunt`` the howl.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ambition_sprite2d_renderer.authoring.part_flipbook import publish_rig_flipbook
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument, faded_canvas
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

TARGET_NAME = "evil_spectral_wolf"
RIG_PATH = Path(__file__).resolve().parent / "rigged" / TARGET_NAME / f"{TARGET_NAME}_side.rig.json"

#: The body, in frame pixels (x0, y0, x1, y1): the hound's (the bones are
#: the same), in the wolf's taller frame. The bottom edge is the ground line
#: of the paws.
BODY_BOX = (68.0, 57.0, 178.0, 158.0)

ACTOR_METADATA = {
    "actor": {"character_id": "npc_evil_spectral_wolf", "display_name": "Spectral Wolf"},
    "authoring_description": {
        "visual_inspirations": [
            "The attack hound's body made a wolf: a heavy ruff, a bushy tail, a longer muzzle.",
            "The Inugami's spirit ink: rose fur, a maroon outline, pale gold eyes, a mouth lit from inside.",
            "Red ghost fire off its hackles, its back and its tail; its collar snapped, the regime's tag still on it.",
        ],
        "rigging_notes": [
            "The SVG owns the part shapes. The bones and the shared clips are the attack hound's.",
            "faded, fade_out and fade_in are drawn faint; death ends with the spirit gone.",
        ],
    },
    "body": {
        "body_plan": "Quadruped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": ["animal", "wolf", "quadruped", "no_hands", "enemy", "evil", "spirit"],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": True,
            "climb": None,
            "crawl": None,
            "fly": None,
            "swim": None,
            "use_lifts": None,
            "door_access": [],
        },
        "interactions": {"talk": None, "trade": None, "carry": None, "open_doors": []},
    },
    "brain": {"default_preset": "melee_brute_striker"},
    "actions": {"default_preset": "striker_swipe"},
    "visual": {"default_pose": "idle"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "locomotion.jump": {"animation": "jump", "events": []},
        "locomotion.fall": {"animation": "fall", "events": []},
        "attack.bite": {"animation": "slash", "events": []},
        "attack.lunge": {"animation": "attack_side", "events": []},
        "vocalization.howl": {"animation": "taunt", "events": []},
        "state.faded": {"animation": "faded", "events": []},
        "reaction.hit": {"animation": "hit", "events": []},
        "life.death": {"animation": "death", "events": []},
    },
    "tags": ["animal", "wolf", "quadruped", "enemy", "evil", "spirit", "svg_rigged"],
}


@lru_cache(maxsize=1)
def _doc() -> RigDocument:
    return RigDocument.load(RIG_PATH)


#: How solid it is when it is not faded: a spirit is a little transparent,
#: as the Inugami is.
SOLID = 0.9
#: How faint it is when it is faded.
FAINT = 0.3
#: The frame of ``death`` from which the spirit leaves it.
LEAVES_FROM = 3


def opacity(animation: str, frame_idx: int, frame_count: int) -> float:
    """How solid the frame is (0 to 1)."""
    u = frame_idx / max(1, frame_count - 1)
    if animation == "faded":
        return FAINT
    if animation == "fade_out":
        return SOLID + (FAINT - SOLID) * u
    if animation == "fade_in":
        return FAINT + (SOLID - FAINT) * u
    if animation == "death" and frame_idx >= LEAVES_FROM:
        return SOLID * (1.0 - (frame_idx - LEAVES_FROM + 1) / (frame_count - LEAVES_FROM))
    return SOLID


def _render_frame(animation: str, frame_idx: int, frame_count: int):
    return faded_canvas(_doc().render_frame(animation, frame_idx, frame_count), opacity(animation, frame_idx, frame_count))


def _body_metrics(fw: int, fh: int) -> dict:
    x0, y0, x1, y1 = BODY_BOX
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


__all__ = ["ACTOR_METADATA", "BODY_BOX", "opacity", "render"]
