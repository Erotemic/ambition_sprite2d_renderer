"""SVG-rigged chicken: a white cockerel that struts, runs at you and pecks.

A ground bird. It walks with its head thrust at each step, runs with its
wings out, flutters when it is off the ground and pecks. Drawn as an SVG and
posed by a rig: a white body with a dark tail (the Columbian pattern), a red
comb and wattle, a short yellow beak, a striped hackle, yellow legs, and a
wing that folds on the body and spreads.

The SVG ``data/characters/chicken/chicken.svg`` owns the art and marks every
joint (its hidden ``Rig Joints`` layer). The rig document under
``rigged/chicken/`` owns the skeleton and the clips;
``scripts/build_chicken_rig.py`` derives it (through ``rigbuild.creature_rig``
with the ``bird`` anatomy) and authors the clips. Each clip also keys the eye
state (``eye.*``), the wing look (``wing.folded`` / ``wing.open``) and the
strength of each effect (``fx.*``). This module owns only publication;
``_bird_fx`` draws the effects.

    PYTHONPATH=tools/ambition_sprite2d_renderer python -m ambition_sprite2d_renderer publish chicken
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image

from ._bird_fx import BirdFx

TARGET_NAME = "chicken"
USES_DROP_SHADOW = False
USES_PROPS = False
LINEAGE = {
    "family": "chicken",
    "variant": "svg_rigged",
    "parents": [],
    "method": "svg_rig",
    "revision": "initial",
}
RIG_PATH = Path(__file__).resolve().parent / "rigged" / TARGET_NAME / "chicken_side.rig.json"
FRAME_W, FRAME_H = 128, 128
#: Sprite pixels per SVG unit (the rig's ``svg_source.scale``): drawn 512
#: units square, published in a 128 px frame.
ART_SCALE = 0.25
LOOPS = {"idle", "walk", "run", "jump", "fall", "taunt"}

WHITE = (246, 241, 231, 255)
SHADE = (214, 205, 192, 255)
DARK = (44, 59, 70, 255)
SHEEN = (95, 154, 138, 255)

BIRD = BirdFx(
    target=TARGET_NAME,
    rig_path=RIG_PATH,
    art_scale=ART_SCALE,
    frame_size=(FRAME_W, FRAME_H),
    feathers=((WHITE, SHADE), (WHITE, DARK), (DARK, SHEEN)),
    # The head bone runs from the neck's base to the beak tip, 92 units.
    beak_tip=(94.0, 0.0),
)


def _px(x: float, y: float) -> Dict[str, float]:
    """A point of the drawing (SVG units) as a sprite-frame point."""
    return {"x": round(x * ART_SCALE, 1), "y": round(y * ART_SCALE, 1)}


ACTOR_METADATA = {
    "actor": {"character_id": "chicken", "display_name": "Chicken"},
    "body": {
        "body_plan": "AvianBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "locomotion_hint": "Run",
        "traits": ["enemy", "bird", "ground_bird", "svg_rigged"],
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": True,
            "climb": None,
            "fly": None,
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
    "brain": {"default_preset": "melee_brute_striker"},
    "actions": {"default_preset": "striker_swipe"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "locomotion.jump": {"animation": "jump", "events": []},
        "locomotion.fall": {"animation": "fall", "events": []},
        "action.melee.primary": {
            "animation": "slash",
            "events": [
                {"t": 0.17, "event": "telegraph_peak", "source": TARGET_NAME},
                {"t": 0.42, "event": "hitbox_active_start", "source": TARGET_NAME},
                {"t": 0.67, "event": "hitbox_active_end", "source": TARGET_NAME},
            ],
        },
        "emote.taunt": {"animation": "taunt", "events": []},
        "reaction.hurt": {"animation": "hurt", "events": []},
        "reaction.death": {"animation": "death", "events": []},
    },
    # Points on the drawn frame (before the sheet's auto-crop), standing at rest.
    "sockets": {
        "beak": {"source": "chicken.geometry", "point": _px(348.0, 218.0)},
        "head": {"source": "chicken.geometry", "point": _px(306.0, 212.0)},
        "feet": {"source": "chicken.geometry", "point": _px(256.0, 416.0)},
        "tail": {"source": "chicken.geometry", "point": _px(142.0, 196.0)},
    },
    "visual": {
        "default_pose": "idle",
        "canonical_source": "ambition_sprite2d_renderer/data/characters/chicken/chicken.svg",
    },
    "tags": ["enemy", "bird", "chicken", "svg_rigged"],
    "authoring_description": (
        "The chicken is a white cockerel with a dark tail, a red comb and wattle and yellow legs, "
        "drawn as an SVG and posed by a rig. It is a ground bird: it struts with its head thrust at "
        "each step, runs with its wings out, flutters off the ground and pecks."
    ),
    "gameplay_description": (
        "Use as a small, fast ground bird: an enemy that runs straight at its target and pecks, or "
        "a yard animal. Birds are dinosaurs, so the T-rex calls it with the rest of his kin."
    ),
    "dialogue_hints": {
        "barks": [
            "Bawk. I do not swerve.",
            "You go first. No, you.",
            "BA-GAWK!",
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
