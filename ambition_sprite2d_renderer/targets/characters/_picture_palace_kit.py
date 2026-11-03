"""Shared drawing for the machines of the Picture Palace (the Art dimension).

The machines are drawn in the cel style of the Art dimension's cast
(`_art_cast_kit.py`). A machine is made of parts (plates, pistons, joints),
so this kit draws each part with its own ink edge: a shape of ink a little
larger than the part, and the part on it. The kit also has the legs of a
biped (two bones that bend at the knee) and the actor sidecar of a machine
that talks and does not fight.
"""

from __future__ import annotations

import math
from typing import List, Sequence, Tuple

from . import _art_cast_kit as K

Point = Tuple[float, float]

#: The studio's accent colours.
FILM_BLACK = (30, 30, 38, 255)
STUDIO_GREY = (128, 132, 146, 255)
TUNGSTEN = (255, 214, 120, 255)
REC_RED = (236, 40, 36, 255)
REC_RED_HOT = (255, 168, 120, 255)

#: The rows of a machine that walks and talks: the rows of the Curator.
ROWS: List[Tuple[str, int, int]] = [("idle", 6, 160), ("walk", 8, 110), ("talk", 6, 120), ("hit", 3, 90), ("death", 6, 130)]
LOOPS = {"idle", "walk", "talk"}


def plate(f: K.Frame, pts: Sequence[Point], fill, edge: float = 1.0, body: bool = True) -> None:
    """A part with its own ink edge."""
    f.poly(K.grow(pts, edge), K.INK, body=body)
    f.poly(pts, fill, body=False)


def rod(f: K.Frame, pts: Sequence[Point], width: float, fill, edge: float = 1.0, body: bool = True) -> None:
    """A piston, a cable or a bone with its own ink edge."""
    f.limb(pts, width + 2.0 * edge, K.INK, body=body)
    f.limb(pts, width, fill, body=False)


def disc(f: K.Frame, cx: float, cy: float, rx: float, ry: float, fill, edge: float = 1.0, body: bool = True) -> None:
    f.ellipse(cx, cy, rx + edge, ry + edge, K.INK, body=body)
    f.ellipse(cx, cy, rx, ry, fill, body=False)


def knee(hip: Point, ankle: Point, thigh: float, shin: float, forward: float = 1.0) -> Point:
    """The knee of a leg from `hip` to `ankle`; it bends toward `forward`
    (+1: the right of the frame)."""
    dx, dy = ankle[0] - hip[0], ankle[1] - hip[1]
    d = max(1e-3, math.hypot(dx, dy))
    d_c = min(d, thigh + shin - 1e-3)
    a = (thigh * thigh - shin * shin + d_c * d_c) / (2.0 * d_c)
    h = math.sqrt(max(0.0, thigh * thigh - a * a))
    ux, uy = dx / d, dy / d
    mx, my = hip[0] + ux * a, hip[1] + uy * a
    # The two normals of the line; pick the one toward `forward`.
    nx, ny = -uy, ux
    if nx * forward < 0:
        nx, ny = -nx, -ny
    return (mx + nx * h, my + ny * h)


def machine_metadata(character_id: str, display_name: str, body_plan: str, body_kind: str, traits: Sequence[str], description: str,
                     walks: bool = True) -> dict:
    """The actor sidecar of a machine of the Picture Palace: it talks, and it
    does not fight."""
    bindings = {
        "default": {"animation": "idle", "events": []},
        "dialogue.talk": {"animation": "talk", "events": []},
        "combat.hurt": {"animation": "hit", "events": []},
        "combat.death": {"animation": "death", "events": []},
    }
    if walks:
        bindings["locomotion.walk"] = {"animation": "walk", "events": []}
    return {
        "actor": {"character_id": character_id, "display_name": display_name},
        "body": {"body_plan": body_plan, "body_kind": body_kind, "mass_class": "Heavy", "traits": list(traits),
                 "locomotion_hint": "Walk" if walks else "Static"},
        "visual": {"default_pose": "idle", "portrait": {"animation": "talk", "frame": 1}},
        "tags": ["townsfolk", "art", "peaceful", "machine"],
        "authoring_description": description,
        "animation_bindings": bindings,
    }
