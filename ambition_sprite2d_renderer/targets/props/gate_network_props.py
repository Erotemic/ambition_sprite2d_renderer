"""The fittings of a gate of the gate network: what a traveller uses and what
keeps a ring running.

- ``gate_dialer``: the pedestal a traveller dials from. A sloped steel desk on
  a short column, its face a half ring of eleven amber chevron keys (the
  ring's own inscription, ΛΕΓΑΛΛΥ ΔΙΣΤΙΝΧΤ, one key for each symbol) around a
  round dome. The game draws the terminal's press button over the low front
  of the column. Every dialed ring has one beside it.
- ``gate_power_cabinet``: the ring's power: a grey cabinet with a meter, a
  lever, warning stripes and the conduit that runs out of its side to the
  ring. Rings are expensive to run, and every gate hall shows it.
- ``gate_traffic_board``: the board of arrivals and departures over a public
  gate: rows of lamps, some lit, one red, under the word GATES.
- ``gate_transit_bags``: a wall dispenser of bags for the sickness organic
  travellers get in transit. A robot has no use for it.

Drawn in world units at `PX` pixels to the unit; the bottom of the frame is
the floor. No drop shadow, and no portal: a portal is the portal
presentation's, never art.

Animations:

- ``idle``: 1 frame.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Callable, Dict, List, Tuple

from PIL import Image

from ...authoring.sheet_build import build_sheet
from ._town_kit import Canvas, box
from .castle_godwin import lettering

#: Pixels of the frame to one world unit.
PX = 2

STEEL = (88, 96, 108)
STEEL_LIGHT = (150, 160, 174)
STEEL_DARK = (40, 44, 52)
BRASS = (176, 140, 78)
BRASS_DARK = (106, 80, 44)
AMBER = (255, 158, 61)
AMBER_DIM = (120, 64, 26)
RED = (210, 44, 40)
GREEN = (90, 200, 110)
CREAM = (236, 226, 200)
INK = (22, 22, 26)
HAZARD = (232, 186, 40)

#: The symbols on the keys, in the order of the ring's inscription.
INSCRIPTION = "ΛΕΓΑΥΔΙΣΤΝΧ"


def _chevron(cx: float, cy: float, s: float, angle: float) -> List[Tuple[float, float]]:
    """A chevron key `s` units across, pointing at `angle` (radians)."""
    shape = [(-0.5, -0.32), (0.5, -0.32), (0.75, 0.1), (0.0, 0.62), (-0.75, 0.1)]
    ca, sa = math.cos(angle), math.sin(angle)
    return [(cx + (x * ca - y * sa) * s, cy + (x * sa + y * ca) * s) for x, y in shape]


def _dialer(c: Canvas) -> None:
    w, h = DIALER_W, DIALER_H
    # The column and its foot.
    c.put(c.mask(box(w * 0.5 - 13, 26, w * 0.5 + 13, h - 4)), STEEL_DARK)
    c.paint(c.mask(box(w * 0.5 - 12, 26, w * 0.5 + 12, h - 4)), c.ramp([(26, STEEL), (h, STEEL_DARK)]))
    c.put(c.mask(box(w * 0.5 - 20, h - 6, w * 0.5 + 20, h)), STEEL_DARK)
    c.put(c.mask(box(w * 0.5 - 19, h - 6, w * 0.5 + 19, h - 4.5)), STEEL_LIGHT, 0.6)
    # The desk: a slab leaning toward the user.
    desk = [(2, 16), (w - 2, 16), (w - 6, 30), (6, 30)]
    c.put(c.mask(lambda p: p.poly([(x, y + 1) for x, y in desk])), INK)
    c.paint(c.mask(lambda p: p.poly(desk)), c.ramp([(16, STEEL_LIGHT), (30, STEEL)]))
    c.put(c.mask(lambda p: p.poly([(6, 30), (w - 6, 30), (w - 8, 33), (8, 33)])), STEEL_DARK)
    # The face: a half ring of the eleven keys round a dome, seen from above.
    cx, cy = w * 0.5, 23.5
    keys = []
    for i, _ in enumerate(INSCRIPTION):
        a = math.pi * (1.05 + 0.9 * i / (len(INSCRIPTION) - 1))
        x, y = cx + 25 * math.cos(a), cy + 7.5 * math.sin(a) + 1.5
        keys.append(_chevron(x, y, 4.2, a + math.pi / 2))
    c.put(c.mask(lambda p: [p.poly(k) for k in keys]), BRASS_DARK)
    c.put(c.mask(lambda p: [p.poly([(x, y - 0.6) for x, y in k]) for k in keys]), AMBER)
    c.put(c.mask(lambda p: [p.ellipse(sum(x for x, _ in k) / 5, sum(y for _, y in k) / 5 - 0.6, 0.8) for k in keys]), CREAM, 0.9)
    # The dome in the middle, red under amber glass.
    c.put(c.mask(lambda p: p.ellipse(cx, cy + 1, 7, 3.6)), BRASS_DARK)
    c.put(c.mask(lambda p: p.ellipse(cx, cy, 6, 3)), RED)
    c.put(c.mask(lambda p: p.ellipse(cx - 1.8, cy - 1, 2.2, 1.0), blur=0.3), (255, 210, 190), 0.8)
    # A brass plate on the column, where the press button sits.
    c.put(c.mask(box(w * 0.5 - 9, 34, w * 0.5 + 9, h - 9)), BRASS_DARK)
    c.put(c.mask(box(w * 0.5 - 8, 35, w * 0.5 + 8, h - 10)), BRASS, 0.55)


DIALER_W, DIALER_H = 64, 56


def _power_cabinet(c: Canvas) -> None:
    w, h = CABINET_W, CABINET_H
    body = c.mask(box(4, 10, w - 14, h))
    c.put(c.mask(box(3, 9, w - 13, h)), INK)
    c.paint(body, c.ramp([(10, STEEL_LIGHT), (h, STEEL)]))
    c.tone(body * (c.noise("cabinet", 4, 8, 2) - 0.5), 0.12)
    # The roof lip and the louvres.
    c.put(c.mask(box(1, 6, w - 11, 11)), STEEL_DARK)
    c.put(c.mask(lambda p: [p.rect(10, 16 + 4 * i, w - 22, 17.4 + 4 * i) for i in range(4)]), STEEL_DARK, 0.8)
    # The meter: a dial with its needle near the red.
    c.put(c.mask(lambda p: p.ellipse(w * 0.4, 44, 9)), INK)
    c.put(c.mask(lambda p: p.ellipse(w * 0.4, 44, 8)), CREAM)
    c.put(c.mask(lambda p: p.line([(w * 0.4, 44), (w * 0.4 + 6, 38.5)], 1.0)), RED)
    c.put(c.mask(lambda p: p.ellipse(w * 0.4, 44, 1.4)), INK)
    # The lamps: green run, amber load.
    c.put(c.mask(lambda p: p.ellipse(w * 0.4 + 16, 38, 2.4)), GREEN)
    c.put(c.mask(lambda p: p.ellipse(w * 0.4 + 16, 46, 2.4)), AMBER)
    # The lever.
    c.put(c.mask(box(10, 58, 16, 74)), STEEL_DARK)
    c.put(c.mask(lambda p: p.line([(13, 66), (24, 58)], 2.2)), INK)
    c.put(c.mask(lambda p: p.ellipse(24, 58, 2.6)), RED)
    # The warning stripes at the foot, and the word POWER.
    stripes = c.mask(lambda p: [p.poly([(6 + 8 * i, h - 4), (10 + 8 * i, h - 4), (16 + 8 * i, h - 14), (12 + 8 * i, h - 14)]) for i in range(-1, 6)])
    band = c.mask(box(6, h - 14, w - 16, h - 4))
    c.put(band, INK)
    c.put(stripes * band, HAZARD)
    lettering(c, "POWER", (w - 10) / 2, 80, 6, CREAM)
    # The conduit out of its side, bent down to the floor toward the ring.
    c.put(c.mask(lambda p: p.line([(w - 14, 30), (w - 4, 30), (w - 4, h)], 6.0)), INK)
    c.put(c.mask(lambda p: p.line([(w - 14, 30), (w - 4, 30), (w - 4, h)], 4.0)), BRASS_DARK)
    c.put(c.mask(lambda p: p.line([(w - 14, 29), (w - 5, 29), (w - 5, h)], 1.2)), BRASS, 0.7)


CABINET_W, CABINET_H = 64, 96


def _traffic_board(c: Canvas) -> None:
    w, h = BOARD_W, BOARD_H
    # Two hangers and the board.
    c.put(c.mask(lambda p: [p.line([(x, 0), (x, 10)], 1.4) for x in (24, w - 24)]), STEEL_DARK)
    c.put(c.mask(box(0, 8, w, h)), INK)
    c.put(c.mask(box(2, 10, w - 2, h - 2)), (28, 26, 30))
    lettering(c, "GATES", w / 2, 14, 8, AMBER)
    rng = c.rand("board lamps")
    for row in range(5):
        y = 30 + row * 12
        # A row: a line of dim letters (the name) and its lamp.
        c.put(c.mask(lambda p: [p.rect(10 + 6 * i, y, 14 + 6 * i, y + 5) for i in range(rng.randint(5, 9))]), AMBER_DIM)
        lamp = RED if row == 3 else (GREEN if rng.random() < 0.7 else AMBER)
        c.put(c.mask(lambda p: p.ellipse(w - 14, y + 2.5, 3)), lamp)
        c.put(c.mask(lambda p: p.ellipse(w - 15, y + 1.5, 1.0)), CREAM, 0.7)


BOARD_W, BOARD_H = 160, 96


def _transit_bags(c: Canvas) -> None:
    w, h = BAGS_W, BAGS_H
    c.put(c.mask(box(2, 4, w - 2, h - 10)), INK)
    c.paint(c.mask(box(3, 5, w - 3, h - 11)), c.ramp([(5, (210, 214, 220)), (h, (160, 166, 176))]))
    # The slot and the bags in it, paper brown.
    c.put(c.mask(box(7, h - 22, w - 7, h - 14)), INK)
    c.put(c.mask(lambda p: [p.rect(9 + 3 * i, h - 26, 11 + 3 * i, h - 15) for i in range(4)]), (190, 160, 110))
    # A green face and a cross over a gear: organics only.
    c.put(c.mask(lambda p: p.ellipse(w * 0.35, 16, 5)), GREEN)
    c.put(c.mask(lambda p: p.line([(w * 0.35 - 2.5, 18.5), (w * 0.35 + 2.5, 18.5)], 1.0)), INK)
    c.put(c.mask(lambda p: p.ellipse(w * 0.72, 16, 4.5)), STEEL_DARK)
    c.put(c.mask(lambda p: [p.line([(w * 0.72 - 5, 11), (w * 0.72 + 5, 21)], 1.2), p.line([(w * 0.72 - 5, 21), (w * 0.72 + 5, 11)], 1.2)]), RED)
    # Its bracket on the wall.
    c.put(c.mask(box(w * 0.5 - 2, h - 10, w * 0.5 + 2, h)), STEEL_DARK)


BAGS_W, BAGS_H = 32, 48


PROPS: Dict[str, Tuple[float, float, Callable[[Canvas], None], List[str]]] = {
    # name: (width, height, draw, tags)
    "gate_dialer": (DIALER_W, DIALER_H, _dialer, ["prop", "gate", "terminal"]),
    "gate_power_cabinet": (CABINET_W, CABINET_H, _power_cabinet, ["prop", "gate", "machinery"]),
    "gate_traffic_board": (BOARD_W, BOARD_H, _traffic_board, ["prop", "gate", "sign"]),
    "gate_transit_bags": (BAGS_W, BAGS_H, _transit_bags, ["prop", "gate"]),
}


def _frame_size(name: str) -> Tuple[int, int]:
    w, h, _, _ = PROPS[name]
    return (int(w * PX), int(h * PX))


def _draw(name: str) -> Image.Image:
    w, h, draw, _ = PROPS[name]
    c = Canvas(name, w, h, origin=(0.0, 0.0), ppu=PX)
    draw(c)
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
    tags = PROPS[name][3]
    return {
        "actor": {"character_id": f"prop_{name}", "display_name": name.replace("_", " ").title()},
        "body": {"body_plan": "Prop", "body_kind": "Scenery", "mass_class": "Heavy", "locomotion_hint": "Static", "traits": tags},
        "brain": {"default_preset": "stand_still"},
        "actions": {"default_preset": "peaceful"},
        "animation_bindings": {"default": {"animation": "idle", "events": []}},
        "tags": tags,
    }


TARGETS = {name: {"render": _renderer(name), "actor_metadata": _actor(name)} for name in PROPS}

__all__ = ["PROPS", "PX", "TARGETS"]
