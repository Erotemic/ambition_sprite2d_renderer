"""House fronts of the Math town: scenery that stands behind the play.

Each is an LDtk `Prop` (decoration, no collision) whose picture is the front
of one house: limestone and whitewash, shutters, arched windows, rose windows
drawn with a compass, hexagonal tiles, a dome, chalk proofs on the walls. A
balcony or a flat roof a body can stand on is a one-way platform the room
places where the art draws it; the light top edge of a thing is where a body
can stand. A door drawn here is the picture of a door; the room puts the
door that is walked through over it.

Drawn with `_town_kit` in world units at `PX` pixels to the unit; the bottom
of the frame is the street. Each house is its own target (its own sheet), so
a room names the house it wants by its `kind`.

The look-dev these come from is `untracked/art-candidates/town/town_vertical.py`.

Animations:

- ``idle``: 1 frame.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import numpy as np
from PIL import Image

from ...authoring.sheet_build import build_sheet
from ._town_kit import Canvas, Kit, box, mix, scale

#: Pixels of the frame to one world unit.
PX = 2
#: Room round the house in the frame, for eaves, signs and lamps.
MARGIN = 24

PAL = {
    "stone": (214, 206, 190), "stone_light": (246, 240, 226), "trim": (246, 242, 232), "dark": (40, 52, 70),
    "glass_top": (110, 170, 214), "glass_low": (50, 90, 130), "lamp": (255, 210, 140), "wood": (96, 70, 52),
    "leaf": (70, 128, 80), "iron": (36, 48, 64), "brass": (200, 150, 70), "glaze": (226, 180, 70),
}
LIMESTONE = (228, 216, 192)
WHITE = (246, 244, 238)
BLUE = (60, 110, 180)
TERRACOTTA = (184, 100, 70)
CHALK = (252, 252, 246)
OCHRE = (232, 206, 160)


def rose(c: Canvas, k: Kit, cx: float, cy: float, r: float, tag) -> None:
    """A rose window drawn with a compass: six circles through the centre."""
    k.glass(c.mask(lambda p: p.ellipse(cx, cy, r)), 0.0, cy - r, cy + r, tag)
    clip = c.mask(lambda p: p.ellipse(cx, cy, r))
    c.put(c.mask(lambda p: ([p.ring(cx + r * 0.5 * math.cos(a), cy + r * 0.5 * math.sin(a), r * 0.5, 0.8) for a in np.linspace(0, math.tau, 7)[:-1]], p.ring(cx, cy, r * 0.5, 0.8))) * clip, PAL["trim"])
    c.put(c.mask(lambda p: p.ring(cx, cy, r + 1.2, 2.6)), PAL["trim"])


def chalk_proof(c: Canvas, x: float, y: float, s: float = 1.0) -> None:
    """Pythagoras in chalk: a right triangle with a square on each side."""
    a, b = 18 * s, 24 * s
    pts = [(x, y), (x + b, y), (x, y - a)]
    c.put(c.mask(lambda p: (
        p.line(pts + [pts[0]], 0.6),
        p.line([(x, y), (x, y + b), (x + b, y + b), (x + b, y)], 0.5),
        p.line([(x, y), (x - a, y), (x - a, y - a), (x, y - a)], 0.5),
        p.line([(x, y - a), (x + a, y - a - b), (x + a + b, y - b), (x + b, y)], 0.5),
        p.line([(x + 3, y), (x + 3, y - 3), (x, y - 3)], 0.4),
    )), CHALK, 0.6)


def spiral_rail(c: Canvas, x0: float, x1: float, y: float) -> None:
    """A railing whose panels are golden spirals in iron."""
    c.put(c.mask(lambda p: (p.rect(x0, y - 14, x1, y - 12.8), p.rect(x0, y - 1.2, x1, y))), PAL["iron"])
    phi = (1 + 5 ** 0.5) / 2

    def spirals(p):
        for x in np.arange(x0 + 7, x1 - 4, 14):
            pts = []
            for i in range(60):
                th = i / 59 * 3.2 * math.pi
                r = 6.0 * phi ** (-th / (math.pi / 2))
                pts.append((x + r * math.cos(th), y - 7 + r * math.sin(th)))
            p.line(pts, 0.6)
            p.rect(x + 6.6, y - 13, x + 7.3, y)

    c.put(c.mask(spirals), PAL["iron"])


def dome(c: Canvas, x0: float, x1: float, eave: float, colour, wall) -> None:
    cx = (x0 + x1) / 2
    r = (x1 - x0) * 0.38
    m = c.mask(lambda p: p.ellipse(cx, eave, r, r * 0.9)) * (c.y < eave)
    c.put(m, colour)
    c.tone(c.mask(lambda p: p.ellipse(cx - r * 0.3, eave - r * 0.5, r * 0.5, r * 0.35), blur=r * 0.15) * m, 0.25)
    c.tone(m * np.clip((c.x - cx) / r, 0, 1), -0.2)
    c.put(c.mask(box(x0 - 4, eave - 3, x1 + 4, eave + 2)), mix(wall, (255, 255, 250), 0.3))
    c.put(c.mask(box(cx - 2, eave - r * 0.9 - 10, cx + 2, eave - r * 0.9 + 1)), PAL["brass"])


def flat_roof(c: Canvas, x0: float, x1: float, eave: float, wall) -> None:
    """A flat roof a body can stand on: a parapet whose top is the walk line."""
    c.put(c.mask(box(x0 - 3, eave - 8, x1 + 3, eave)), mix(wall, (255, 255, 250), 0.2))
    c.put(c.mask(box(x0 - 3, eave - 8, x1 + 3, eave - 6.8)), (255, 255, 252))


#: Each house: its wall's width and height (units), and how to draw it on a
#: kit whose `ground` is the street. `x0`, `x1` are the wall's sides.
House = Tuple[float, float, float, Callable[[Canvas, Kit, float, float, float], None]]


def _rose_house(c, k, x0, x1, g):
    eave = g - 330
    k.wall(x0, eave, x1, g, LIMESTONE, "limestone", tag="rose")
    k.eave_shade(x0, x1, eave, 5, 0.22)
    w = x1 - x0
    for cx in (x0 + 30, x1 - 30):
        k.window(cx, eave + 40, 14, 28, "arch", tag=("rose", cx))
    rose(c, k, x0 + w / 2, eave + 80, 22, "rosewin")
    for cx in (x0 + 50, x1 - 40):
        k.window(cx, eave + 140, 16, 30, "arch", shutters=BLUE, tag=("rose2", cx))
    k.window(x0 + 40, eave + 220, 22, 40, "arch", tag="rose3")
    k.door(x1 - 44, 30, 66, (50, 90, 120), arch=True, number=True, tag="rosedoor")
    chalk_proof(c, x0 + 76, g - 22, 0.9)
    flat_roof(c, x0, x1, eave, LIMESTONE)


def _dome_house(c, k, x0, x1, g):
    eave = g - 210
    k.wall(x0, eave, x1, g, WHITE, "plaster", tag="dome")
    k.eave_shade(x0, x1, eave, 5, 0.18)
    dome(c, x0, x1, eave, BLUE, WHITE)
    k.window(x0 + 36, eave + 24, 16, 28, "arch", shutters=BLUE, tag="d1")
    k.window(x1 - 36, eave + 24, 16, 28, "arch", shutters=BLUE, tag="d2")
    k.window(x0 + 52, eave + 122, 44, 34, "rect", lit=0.2, tag="d3")
    k.door(x1 - 40, 30, 66, BLUE, arch=True, tag="ddoor")
    k.balcony(x0 + 66, x0 + 120, eave + 82, (232, 226, 214))
    k.awning(x0 + 16, x0 + 90, eave + 110, 12, ((246, 242, 232), BLUE))


def _tower_house(c, k, x0, x1, g):
    eave = g - 420
    k.wall(x0, eave, x1, g, (236, 226, 204), "limestone", tag="tower")
    k.eave_shade(x0, x1, eave, 5, 0.22)
    w = x1 - x0
    k.window(x0 + w * 0.33, eave + 30, 14, 26, "rect", shutters=TERRACOTTA, tag="t1")
    k.window(x1 - w * 0.33, eave + 30, 14, 26, "rect", shutters=TERRACOTTA, tag="t2")
    k.window(x0 + w / 2, eave + 110, 16, 30, "arch", tag="t3")
    k.window(x0 + w / 2, eave + 200, 16, 30, "arch", flowers=(230, 80, 90), tag="t4")
    k.window(x0 + w * 0.33, eave + 290, 14, 26, "rect", tag="t5")
    k.door(x1 - w * 0.3, 28, 62, (120, 72, 50), arch=False, tag="tdoor")
    k.balcony(x0 + 16, x1 - 16, eave + 160, (232, 226, 214))
    k.hipped(x0, x1, eave, 34, (70, 120, 170), "hex", tag="troof")


def _shop_house(c, k, x0, x1, g):
    eave = g - 240
    k.wall(x0, eave, x1, g, OCHRE, "plaster", tag="shop")
    k.eave_shade(x0, x1, eave, 5, 0.22)
    w = x1 - x0
    for cx in (x0 + w * 0.22, x0 + w * 0.5, x0 + w * 0.78):
        k.window(cx, eave + 24, 16, 28, "rect", shutters=(230, 214, 180), tag=("s", cx))
    k.window(x0 + 56, eave + 150, 60, 44, "rect", lit=0.3, tag="sw")
    k.door(x1 - 44, 30, 66, (60, 90, 80), arch=True, tag="sdoor")
    k.awning(x0 + 18, x0 + 100, eave + 136, 14, ((240, 232, 210), (70, 120, 150)))
    k.ground = g
    k.sign(x1 + 2, eave + 120, 20, 15, (60, 80, 70), "cup")
    k.gable(x0, x1, eave, w * 0.3, TERRACOTTA, "clay", tag="sroof")
    k.chimney(x0 + w * 0.7, eave - w * 0.12, 10, 30, (196, 150, 110))


def _arcade_house(c, k, x0, x1, g):
    eave = g - 230
    k.wall(x0, eave, x1, g, (226, 210, 180), "stone", tag="arc")
    k.eave_shade(x0, x1, eave, 5, 0.22)
    w = x1 - x0
    n = 4
    for i in range(n):
        cx = x0 + (i + 0.5) * w / n
        k.window(cx, eave + 24, 14, 26, "rect", shutters=TERRACOTTA, tag=("a", i))
    span = w / n
    arc = c.mask(lambda p: [p.arch(x0 + i * span + 10, g - 80, x0 + (i + 1) * span - 10, g) for i in range(n)])
    c.put(arc, (70, 70, 86))
    c.tone(arc * np.clip(1 - (c.y - (g - 80)) / 60, 0, 1), -0.3)
    c.put(c.mask(lambda p: [p.ring(x0 + (i + 0.5) * span, g - 80 + (span - 20) / 2, (span - 20) / 2 + 1, 1.6) for i in range(n)]) * (c.y < g - 80 + (span - 20) / 2), (244, 236, 220))
    k.ground = g
    k.sign(x0 - 22, eave + 86, 22, 16, (40, 60, 90), "circle")
    k.gable(x0, x1, eave, w * 0.24, TERRACOTTA, "clay", tag="aroof")
    k.window(x0 + w / 2, eave - w * 0.13, 16, 16, "round", sill=False, tag="aoc")


HOUSES: Dict[str, Tuple[float, float, Callable]] = {
    # name: (wall width, height of the frame over the street, draw)
    "math_house_rose": (170, 360, _rose_house),
    "math_house_dome": (180, 300, _dome_house),
    "math_house_tower": (120, 480, _tower_house),
    "math_house_shop": (200, 320, _shop_house),
    "math_house_arcade": (210, 300, _arcade_house),
}


def _frame_size(name: str) -> Tuple[int, int]:
    w, h, _ = HOUSES[name]
    return (int((w + 2 * MARGIN) * PX), int(h * PX))


def _draw(name: str) -> Image.Image:
    w, h, draw = HOUSES[name]
    fw, fh = w + 2 * MARGIN, h
    c = Canvas(name, fw, fh, origin=(0.0, 0.0), ppu=PX)
    k = Kit(c, PAL, sun=-1)
    k.ground = fh
    draw(c, k, MARGIN, MARGIN + w, fh)
    return c.image()


def _renderer(name: str):
    def render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
        del frame_idx, nframes
        if anim != "idle":
            raise ValueError(f"unknown animation: {anim}")
        return _draw(name)

    def frame_meta(anim: str, frame_idx: int, nframes: int) -> dict:
        del anim, frame_idx, nframes
        fw, fh = _frame_size(name)
        return {"anchors": {"foot": {"x": fw / 2, "y": float(fh)}}, "forward": {"x": 0.0, "y": -1.0}, "angle_deg": 0.0}

    def render(out_dir: str | Path, **opts) -> List[Path]:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        outputs = build_sheet(
            target=name,
            rows=[("idle", 1, 400)],
            render_fn=render_frame,
            out_dir=out_dir,
            frame_size=_frame_size(name),
            frame_meta_fn=frame_meta,
            auto_crop=False,
            actor_metadata=_actor(name),
        )
        return [outputs[key] for key in ("canonical", "canonical_transparent", "spritesheet", "yaml", "ron", "actor", "preview")]

    return render


def _actor(name: str) -> dict:
    return {
        "actor": {"character_id": f"prop_{name}", "display_name": name.replace("_", " ").title()},
        "body": {"body_plan": "Prop", "body_kind": "Scenery", "mass_class": "Heavy", "locomotion_hint": "Static", "traits": ["prop", "house", "scenery"]},
        "brain": {"default_preset": "stand_still"},
        "actions": {"default_preset": "peaceful"},
        "animation_bindings": {"default": {"animation": "idle", "events": []}},
        "tags": ["prop", "house", "scenery"],
    }


TARGETS = {name: {"render": _renderer(name), "actor_metadata": _actor(name)} for name in HOUSES}

__all__ = ["HOUSES", "PX", "MARGIN", "TARGETS"]
