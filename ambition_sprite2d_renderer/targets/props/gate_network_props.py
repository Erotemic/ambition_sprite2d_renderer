"""The fittings of a gate of the gate network: what a traveller uses and what
keeps a ring running.

- ``gate_dialer``: the console a traveller dials from, in the ring's bronze.
  A pedestal with a sloped top holding a round dial: the ring's fifteen
  glyphs (``glyphs.legally_distinct``) lit cyan round a dark centre with a
  solid Δ in it, seen at the slant. A small screen stands behind it. The game draws the terminal's
  press button over the brass plate on the front. Every dialed ring has one
  beside it.
- ``gate_power_cabinet``: the ring's power: a grey cabinet with a meter, a
  lever, warning stripes and the conduit that runs out of its side to the
  ring. Rings are expensive to run, and every gate hall shows it.
- ``gate_traffic_board``: the board of arrivals and departures over a public
  gate: addresses in the gate's glyphs, each with its lamp (one red), under
  the word GATES.
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

import numpy as np
from PIL import Image

from ...authoring.sheet_build import build_sheet
from ...glyphs.legally_distinct import BY_ID, GLYPHS, Placement, glyphs_mask, spell
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

WOOD = (86, 64, 44)
WOOD_DARK = (48, 35, 24)
WOOD_LIGHT = (140, 108, 72)
CYAN = (127, 243, 255)
CYAN_GLOW = (57, 212, 255)
SCREEN = (16, 42, 52)


def _dial_glyphs(c: Canvas, cx: float, cy: float, radius: float, cap: float, slant: float) -> np.ndarray:
    """The coverage of the fifteen glyphs round a dial centred at (cx, cy)
    (units): Λ at the top, each foot toward the centre, and a solid Δ in the
    middle (the press that engages a dial), all seen at a slant that shortens
    the dial to ``slant`` of its height."""
    px, py, k = (cx - c.o[0]) * c.k, (cy - c.o[1]) * c.k, c.k
    placements = [Placement(BY_ID["delta"], (px, py), 1.6 * cap * k)]
    for glyph in GLYPHS:
        ang = -90.0 + glyph.index * 360.0 / len(GLYPHS)
        rad = math.radians(ang)
        placements.append(Placement(glyph, (px + radius * k * math.cos(rad), py + radius * k * math.sin(rad)), cap * k, ang + 90.0))
    squash = f"translate({px:.3f} {py:.3f}) scale(1 {slant}) translate({-px:.3f} {-py:.3f})"
    return glyphs_mask(placements, (c.W, c.H), transform=squash)


def _dialer(c: Canvas) -> None:
    w, h = DIALER_W, DIALER_H
    # The plinth on the floor.
    c.put(c.mask(box(5, h - 6, w - 5, h)), WOOD_DARK)
    c.put(c.mask(box(6, h - 6, w - 6, h - 5)), WOOD_LIGHT, 0.6)
    # The pedestal: its front, and a sliver of its right side for depth.
    c.put(c.mask(box(9, 30, w - 7, h - 6)), WOOD_DARK)
    c.paint(c.mask(box(10, 31, w - 10, h - 6)), c.ramp([(31, WOOD), (h, WOOD_DARK)]))
    c.tone(c.mask(box(10, 31, w - 10, h - 6)) * (c.noise("pedestal", 3, 4, 2) - 0.5), 0.14)
    c.put(c.mask(lambda p: p.poly([(w - 10, 31), (w - 7, 29), (w - 7, h - 6), (w - 10, h - 6)])), WOOD_DARK)
    # The screen behind the desk, on a stem: three lines of cyan text.
    c.put(c.mask(box(30, 11, 34, 16)), WOOD_DARK)
    c.put(c.mask(box(18, 1, 46, 13)), WOOD_DARK)
    c.put(c.mask(box(19, 2, 45, 12)), WOOD)
    c.put(c.mask(box(20.5, 3.5, 43.5, 10.5)), SCREEN)
    c.put(c.mask(lambda p: [p.rect(22.5, 5 + 2 * i, 22.5 + (17, 13, 9)[i], 6 + 2 * i) for i in range(3)], blur=0.15), CYAN, 0.85)
    c.put(c.mask(box(20.5, 3.5, 43.5, 10.5), blur=1.2), CYAN_GLOW, 0.18)
    # The desk: a slab leaning toward the user, with its front edge.
    desk = [(5, 14), (w - 5, 14), (w - 7, 31), (7, 31)]
    c.paint(c.mask(lambda p: p.poly(desk)), c.ramp([(14, WOOD_LIGHT), (31, WOOD)]))
    c.put(c.mask(lambda p: p.poly([(7, 31), (w - 7, 31), (w - 8, 34), (8, 34)])), WOOD_DARK)
    c.put(c.mask(lambda p: p.line(desk[:2], 0.8)), WOOD_LIGHT, 0.9)
    # The dial, seen at the slant: a bronze rim, the glyph band, a bronze
    # hub and its dark centre.
    cx, cy, slant = w * 0.5, 22.5, 0.5
    c.put(c.mask(lambda p: p.ellipse(cx, cy + 0.8, 18, 18 * slant)), WOOD_DARK)
    c.put(c.mask(lambda p: p.ellipse(cx, cy, 17.5, 17.5 * slant)), BRASS)
    c.put(c.mask(lambda p: p.ellipse(cx, cy, 16, 16 * slant)), WOOD_DARK)
    c.put(c.mask(lambda p: p.ellipse(cx, cy, 9.5, 9.5 * slant)), BRASS_DARK)
    c.put(c.mask(lambda p: p.ellipse(cx, cy - 0.3, 8, 8 * slant)), (34, 30, 30))
    c.put(c.mask(lambda p: p.ellipse(cx - 2, cy - 1.2, 3, 3 * slant), blur=0.6), CYAN_GLOW, 0.25)
    glyphs = _dial_glyphs(c, cx, cy, 12.6, 3.6, slant)
    c.put(c.soften(glyphs, 0.5), CYAN_GLOW, 0.55)
    c.put(glyphs, CYAN)
    # A brass plate on the front, where the press button sits.
    c.put(c.mask(box(w * 0.5 - 9, 37, w * 0.5 + 9, h - 9)), BRASS_DARK)
    c.put(c.mask(box(w * 0.5 - 8, 38, w * 0.5 + 8, h - 10)), BRASS, 0.55)


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
    placements = []
    for row, address in enumerate(BOARD_ADDRESSES):
        y = 30 + row * 12
        # A row: the address in glyphs, and its lamp.
        for i, glyph in enumerate(spell(address)):
            placements.append(Placement(glyph, ((12 + 6.5 * i) * c.k, (y + 2.5) * c.k), 5.0 * c.k))
    letters = glyphs_mask(placements, (c.W, c.H))
    c.put(c.soften(letters, 0.6), AMBER, 0.3)
    c.put(letters, AMBER)
    for row in range(len(BOARD_ADDRESSES)):
        y = 30 + row * 12
        lamp = RED if row == 3 else (GREEN if rng.random() < 0.7 else AMBER)
        c.put(c.mask(lambda p: p.ellipse(w - 14, y + 2.5, 3)), lamp)
        c.put(c.mask(lambda p: p.ellipse(w - 15, y + 1.5, 1.0)), CREAM, 0.7)


BOARD_W, BOARD_H = 160, 96
#: The rows of the board: the public network's busiest addresses.
BOARD_ADDRESSES = ("TANGENT", "GENESIS", "SAILING", "CITADEL", "SILENT")


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
