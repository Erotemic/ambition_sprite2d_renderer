"""The fittings of a gate of the gate network: what a traveller uses and what
keeps a ring running.

- ``gate_dialer``: the console a traveller dials from, in the ring's bronze.
  A pedestal with a sloped top holding a round dial, laid out as the ring
  is: the fifteen glyphs (``glyphs.legally_distinct``) lit cyan over the
  arch, Δ at the top, and in the bottom slice, where the gate has its base,
  a big solid Δ: the press that engages a dial. Seen at the slant. A small screen stands behind it. The game draws the terminal's
  press button over the brass plate on the front. Every dialed round ring
  has one beside it.
- ``gate_dialer_triangle``: the same console for the triangle gate
  (``triangle_gate``), to stand in place of ``gate_dialer`` beside it. Its
  dial is an upright triangle laid out as the gate's sides: ΛΕΓΑΛΛΥ up the
  left side, the Δ at the apex, ΙΣΤΙΝΧΤ down the right side, each foot
  toward the opening, and the press in the base, where the gate has its
  pedestal. The frame, the pedestal, the plate and the floor line are the
  round dialer's.
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
from ...glyphs.legally_distinct import ARCH_GAP_DEG, GLYPHS, Placement, arch_angle, glyphs_mask, spell
from . import triangle_gate as tri_gate
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


def _dial_glyphs(c: Canvas, cx: float, cy: float, cap: float, slant: float, pose: Callable[[int], Tuple[float, float, float]]) -> np.ndarray:
    """The coverage of the fifteen glyphs on a dial centred at (cx, cy)
    (units), seen at a slant that shortens the dial to ``slant`` of its
    height. ``pose(index)`` gives where glyph ``index`` stands in the dial's
    plane (units from the centre) and the way its head points (degrees), as
    the gate's ring or the triangle gate's sides set it."""
    px, py, k = (cx - c.o[0]) * c.k, (cy - c.o[1]) * c.k, c.k
    placements = []
    for glyph in GLYPHS:
        dx, dy, out = pose(glyph.index)
        placements.append(Placement(glyph, (px + dx * k, py + dy * k), cap * k, out + 90.0))
    squash = f"translate({px:.3f} {py:.3f}) scale(1 {slant}) translate({-px:.3f} {-py:.3f})"
    return glyphs_mask(placements, (c.W, c.H), transform=squash)


def _dial_press(c: Canvas, cx: float, top: float, foot: float, half: float) -> None:
    """The accept press: a solid Δ from ``top`` to ``foot``, ``half`` of its
    foot wide, raised on a bronze bezel."""
    press = [(cx, top), (cx + half, foot), (cx - half, foot)]
    bezel = [(cx, top - 1.6), (cx + half + 1.9, foot + 1.0), (cx - half - 1.9, foot + 1.0)]
    c.put(c.mask(lambda p: p.poly([(x, y + 0.8) for x, y in bezel])), WOOD_DARK)
    c.put(c.mask(lambda p: p.poly(bezel)), BRASS)
    c.put(c.mask(lambda p: p.poly(press), blur=0.9), CYAN_GLOW, 0.6)
    c.put(c.mask(lambda p: p.poly(press)), CYAN)
    c.put(c.mask(lambda p: p.poly([(cx, top + 1.2), (cx + half * 0.45, foot - 2.2), (cx - half * 0.45, foot - 2.2)]), blur=0.3), (225, 255, 255), 0.7)


def _round_dial(c: Canvas, cx: float) -> None:
    """The round gate's dial, seen at the slant: a bronze rim, the glyph
    band laid out as the ring (``arch_angle``), a bronze hub and its dark
    centre, and the press in the slice the glyphs leave open."""
    cy, slant = 22.5, 0.5
    c.put(c.mask(lambda p: p.ellipse(cx, cy + 0.8, 18, 18 * slant)), WOOD_DARK)
    c.put(c.mask(lambda p: p.ellipse(cx, cy, 17.5, 17.5 * slant)), BRASS)
    c.put(c.mask(lambda p: p.ellipse(cx, cy, 16, 16 * slant)), WOOD_DARK)
    c.put(c.mask(lambda p: p.ellipse(cx, cy, 9.5, 9.5 * slant)), BRASS_DARK)
    c.put(c.mask(lambda p: p.ellipse(cx, cy - 0.3, 8, 8 * slant)), (34, 30, 30))
    c.put(c.mask(lambda p: p.ellipse(cx - 2, cy - 1.2, 3, 3 * slant), blur=0.6), CYAN_GLOW, 0.25)

    def ring(index: int) -> Tuple[float, float, float]:
        ang = arch_angle(index)
        rad = math.radians(ang)
        return 12.6 * math.cos(rad), 12.6 * math.sin(rad), ang

    glyphs = _dial_glyphs(c, cx, cy, 3.6, slant, ring)
    c.put(c.soften(glyphs, 0.5), CYAN_GLOW, 0.55)
    c.put(glyphs, CYAN)
    # The press bites into the band and the hub.
    half = 12.6 * math.sin(math.radians(ARCH_GAP_DEG / 2.0)) * 0.62
    _dial_press(c, cx, cy + 3.2 * slant * 2.0 - 4.4, cy + 15.2 * slant, half)


#: The triangle dial (``gate_dialer_triangle``), in its own plane: the
#: inradius of its bronze rim, of its glyph band's outer and inner edges, and
#: of its opening (the triangle gate's).
TRI_DIAL_RIM = 12.0
TRI_DIAL_BAND_OUT = 11.0
TRI_DIAL_BAND_IN = 5.6
TRI_DIAL_OPEN = 4.6
#: The glyphs on its sides: their size, the gap from the band's apex corner
#: to the first, and the distance between neighbours.
TRI_DIAL_CAP = 3.1
TRI_DIAL_FIRST = 5.0
TRI_DIAL_PITCH = 3.7


def _triangle(cx: float, cy: float, in_r: float, slant: float) -> List[Tuple[float, float]]:
    """An upright triangle about (cx, cy), inradius ``in_r`` in the dial's
    plane, seen at ``slant``: apex, lower right, lower left (the triangle
    gate's ``_triangle``)."""
    return [(cx + 2.0 * in_r * math.cos(math.radians(a)), cy + 2.0 * in_r * math.sin(math.radians(a)) * slant) for a in tri_gate.CORNER_DEGS]


def _triangle_side(index: int) -> Tuple[float, float, float]:
    """Where glyph ``index`` stands on the triangle dial, as on the triangle
    gate (``triangle_gate._chevron_pose``): ΛΕΓΑΛΛΥ up the left side, the Δ
    at the apex, ΙΣΤΙΝΧΤ down the right side, each foot toward the
    opening."""
    mid = (TRI_DIAL_BAND_OUT + TRI_DIAL_BAND_IN) / 2.0
    if index == tri_gate.APEX_INDEX:
        rad = math.radians(tri_gate.APEX_DEG)
        out = 2.0 * mid - 1.0
        return out * math.cos(rad), out * math.sin(rad), tri_gate.APEX_DEG
    left = index < tri_gate.APEX_INDEX
    from_apex = tri_gate.PER_SIDE - 1 - index if left else index - tri_gate.APEX_INDEX - 1
    # From the side's middle toward the apex corner.
    up = math.sqrt(3.0) * mid - TRI_DIAL_FIRST - from_apex * TRI_DIAL_PITCH
    normal = tri_gate.LEFT_NORMAL_DEG if left else tri_gate.RIGHT_NORMAL_DEG
    n, t = math.radians(normal), math.radians(normal + 90.0)
    # The left side's clockwise way is up, the right side's down.
    along = up if left else -up
    return mid * math.cos(n) + along * math.cos(t), mid * math.sin(n) + along * math.sin(t), normal


def _triangle_dial(c: Canvas, cx: float) -> None:
    """The triangle gate's dial, seen at the slant: the round dial's parts
    on an upright triangle. The glyphs along the sides, the Δ at the apex,
    and the press in the base, where the gate has its pedestal."""
    cy, slant = 25.4, 0.5
    tri = lambda r: _triangle(cx, cy, r, slant)  # noqa: E731
    c.put(c.mask(lambda p: p.poly([(x, y + 0.8) for x, y in _triangle(cx, cy, TRI_DIAL_RIM + 0.4, slant)])), WOOD_DARK)
    c.put(c.mask(lambda p: p.poly(tri(TRI_DIAL_RIM))), BRASS)
    c.put(c.mask(lambda p: p.poly(tri(TRI_DIAL_BAND_OUT))), WOOD_DARK)
    c.put(c.mask(lambda p: p.poly(tri(TRI_DIAL_BAND_IN))), BRASS_DARK)
    c.put(c.mask(lambda p: p.poly([(x, y - 0.3) for x, y in tri(TRI_DIAL_OPEN)])), (34, 30, 30))
    c.put(c.mask(lambda p: p.ellipse(cx - 1.5, cy - 2.0, 2.5, 2.5 * slant), blur=0.6), CYAN_GLOW, 0.25)
    glyphs = _dial_glyphs(c, cx, cy, TRI_DIAL_CAP, slant, _triangle_side)
    c.put(c.soften(glyphs, 0.5), CYAN_GLOW, 0.55)
    c.put(glyphs, CYAN)
    # The press stands on the base and rises into the opening.
    foot = cy + TRI_DIAL_BAND_OUT * slant
    _dial_press(c, cx, cy - 2.0 * TRI_DIAL_OPEN * slant + 0.6, foot, 5.2)


def _dialer_console(c: Canvas, dial: Callable[[Canvas, float], None]) -> None:
    """A dialer: the pedestal, the screen behind and the desk, with
    ``dial`` on the desk; the brass plate on the front holds the press
    button the game draws."""
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
    dial(c, w * 0.5)
    # A brass plate on the front, where the press button sits.
    c.put(c.mask(box(w * 0.5 - 9, 37, w * 0.5 + 9, h - 9)), BRASS_DARK)
    c.put(c.mask(box(w * 0.5 - 8, 38, w * 0.5 + 8, h - 10)), BRASS, 0.55)


def _dialer(c: Canvas) -> None:
    _dialer_console(c, _round_dial)


def _dialer_triangle(c: Canvas) -> None:
    _dialer_console(c, _triangle_dial)


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
    "gate_dialer_triangle": (DIALER_W, DIALER_H, _dialer_triangle, ["prop", "gate", "terminal"]),
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
