"""SVG-rigged owl: a horned owl that flies on slow beats and strikes feet first.

A flying bird. Drawn as an SVG and posed by a rig: its body seen from the
side and its face turned to the viewer, as an owl's is, with two great amber
eyes in a pale disc under dark brows, ear tufts, a small hooked beak, a
barred buff chest, broad barred wings and feathered legs with long talons.
On the ground it stands tall, tips its head over and hoots.

The SVG ``data/characters/owl/owl.svg`` owns the art and marks every joint
(its hidden ``Rig Joints`` layer). The rig document under ``rigged/owl/`` owns
the skeleton and the clips; ``scripts/build_owl_rig.py`` derives it (through
``rigbuild.creature_rig`` with the ``bird`` anatomy) and authors the clips.
Each clip also keys the eye state (``eye.*``), the wing look
(``wing.folded`` / ``wing.open``) and the strength of each effect
(``fx.*``). This module owns only publication; ``_bird_fx`` draws the
effects.

    PYTHONPATH=tools/ambition_sprite2d_renderer python -m ambition_sprite2d_renderer publish owl
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image

from ._bird_fx import BirdFx

TARGET_NAME = "owl"
USES_DROP_SHADOW = False
USES_PROPS = False
LINEAGE = {
    "family": "owl",
    "variant": "svg_rigged",
    "parents": [],
    "method": "svg_rig",
    "revision": "initial",
}
RIG_PATH = Path(__file__).resolve().parent / "rigged" / TARGET_NAME / "owl_side.rig.json"
FRAME_W, FRAME_H = 128, 128
#: Sprite pixels per SVG unit (the rig's ``svg_source.scale``): drawn 512
#: units square, published in a 128 px frame.
ART_SCALE = 0.25
LOOPS = {"idle", "walk", "fly", "taunt"}

BROWN = (139, 94, 60, 255)
BROWN_DARK = (106, 68, 41, 255)
BUFF = (217, 178, 122, 255)
CREAM = (239, 220, 180, 255)

BIRD = BirdFx(
    target=TARGET_NAME,
    rig_path=RIG_PATH,
    art_scale=ART_SCALE,
    frame_size=(FRAME_W, FRAME_H),
    feathers=((BROWN, BROWN_DARK), (BUFF, BROWN), (CREAM, BUFF)),
    # The beak, in the head bone's frame (the bone runs from the neck to a
    # point in front of the face).
    beak_tip=(34.0, -18.0),
    flight_pitch=44.0,
)


def _px(x: float, y: float) -> Dict[str, float]:
    """A point of the drawing (SVG units) as a sprite-frame point."""
    return {"x": round(x * ART_SCALE, 1), "y": round(y * ART_SCALE, 1)}


ACTOR_METADATA = {
    "actor": {"character_id": TARGET_NAME, "display_name": "Owl"},
    "body": {
        "body_plan": "AvianBiped",
        "body_kind": "Floating",
        "mass_class": "Light",
        "locomotion_hint": "Fly",
        "traits": ["enemy", "bird", "raptor", "nocturnal", "svg_rigged"],
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": None,
            "climb": None,
            "fly": True,
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
    "brain": {"default_preset": "parrot_lively"},
    "actions": {"default_preset": "peaceful"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.fly": {"animation": "fly", "events": []},
        "action.melee.primary": {
            "animation": "slash",
            "events": [
                {"t": 0.14, "event": "telegraph_peak", "source": TARGET_NAME},
                {"t": 0.43, "event": "hitbox_active_start", "source": TARGET_NAME},
                {"t": 0.64, "event": "hitbox_active_end", "source": TARGET_NAME},
            ],
        },
        "emote.taunt": {"animation": "taunt", "events": []},
        "reaction.hurt": {"animation": "hurt", "events": []},
        "reaction.death": {"animation": "death", "events": []},
    },
    # Points on the drawn frame (before the sheet's auto-crop), perched at rest.
    "sockets": {
        "beak": {"source": "owl.geometry", "point": _px(283.0, 244.0)},
        "head": {"source": "owl.geometry", "point": _px(270.0, 214.0)},
        "talons": {"source": "owl.geometry", "point": _px(270.0, 410.0)},
        "tail": {"source": "owl.geometry", "point": _px(182.0, 406.0)},
    },
    "visual": {
        "default_pose": "idle",
        "canonical_source": "ambition_sprite2d_renderer/data/characters/owl/owl.svg",
    },
    "tags": ["enemy", "bird", "owl", "svg_rigged"],
    "authoring_description": (
        "The owl is a horned owl drawn as an SVG and posed by a rig: its body is seen from the "
        "side and its face is turned to the viewer, with two great amber eyes under dark brows. It "
        "flies on slow, deep beats, strikes feet first with its talons and, on the ground, stands "
        "tall, tips its head over and hoots."
    ),
    "gameplay_description": (
        "Use as a heavier, slower flyer than the parrot: it stalks above its target and comes "
        "down talons first. Birds are dinosaurs, so the T-rex calls it with the rest of his kin."
    ),
    "dialogue_hints": {
        "barks": [
            "Who. Not 'what comes next'. WHO.",
            "A thing is what it is. I keep the list.",
            "Hoo.",
        ]
    },
}

#: The sheet's rows are the rig's clips, in its order (the game reads them by name).
ROWS: List[Tuple[str, int, int]] = BIRD.rows()


def render_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    return BIRD.render_frame(animation, frame_idx, frame_count)


# ---- Target registration hooks ------------------------------------------------


def render(out_dir: Path, **opts) -> List[Path]:
    del opts
    return BIRD.render(Path(out_dir), ACTOR_METADATA)


def render_canonical(out_dir: Path, **opts) -> Path:
    del opts
    return BIRD.render_canonical(Path(out_dir))


__all__ = ["ACTOR_METADATA", "LINEAGE", "LOOPS", "ROWS", "TARGET_NAME", "render", "render_canonical", "render_frame"]
