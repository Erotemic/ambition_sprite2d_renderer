"""Kagero's great seal: the bigger talisman spell she casts on the Inugami at
its last stand.

Jon (2026-11-11): brought to its last hit point, the Inugami bursts into its
unhurtable state again, "and then kogoro should come and cast a bigger
talasman spell tell the player he is weak and strike now, and then the next
strike cinemeatically kills the boss". Her small spell (``ninja_kagero_vfx``)
throws five talismans that seal its ward; this one throws ten, and they ring
the head and hold it until the blow.

* ``great_seal_volley`` -- her ten talismans in flight, along +X: they leave
  the left of the frame in a wide fan, turn over in the air and close in on
  its right edge, where the head is. Played as ``ofuda_volley`` is: midway
  between her and the head, turned to the head, scaled so that
  ``VOLLEY_SPAN`` of the frame is the distance.
* ``great_seal_wrap`` -- they come in from the left, go round the head and
  close into a ring about it, and her seal's vermilion ring opens behind them.
  Its last drawn frame is the first of ``great_seal_hold`` (and, as each
  effect that is not a loop, its own last frame is empty).
* ``great_seal_hold`` -- the ring holds: its talismans go slowly round the
  head, the seal's ring and its strokes pulse with her white light. A loop:
  it turns by one talisman's place each time round.
* ``great_seal_break`` -- the blow lands: the ring bursts, its talismans are
  thrown out and burn up in red fire, scraps of paper fly. It draws its own
  end.

The head is at the middle of each frame, and the ring is ``RING`` of the
frame across: the game scales the effect so the ring goes round the head.
Each talisman is ``kagero_ofuda.ofuda``. Each frame is square and drawn whole.
No shadow.
"""

from __future__ import annotations

import math
from pathlib import Path

from ._character_vfx_common import Canvas, make_spec, publish_canonical, publish_catalog, sheet_files
from .kagero_ofuda import PAPER, SUMI, VERMILION, VERMILION_DARK, _Pen, _with_alpha, ofuda

TARGET_NAME = "kagero_great_seal"
FX = {"cue_family": "ninja_kagero", "residency": "OwnedByCharacter", "fade": "InItsFrames",
      "owners": ["npc_ninja_kagero", "npc_wolfenstein_inugami"]}
SHEET_FILES = sheet_files(TARGET_NAME)
FRAME_SIZE = (320, 320)
#: The share of the frame's width her talismans cross in the volley.
VOLLEY_SPAN = 0.84
#: The ring's diameter, a share of the frame's width.
RING = 0.8
#: How many talismans the seal holds.
SLIPS = 10
#: Each talisman's length, frame pixels.
SLIP = 40.0

ROWS = [
    ("great_seal_volley", 12, 30),
    ("great_seal_wrap", 14, 45),
    ("great_seal_hold", 12, 70),
    ("great_seal_break", 12, 45),
]

FIRE_OUT = (120, 10, 14, 255)
FIRE = (230, 70, 24, 255)
FIRE_CORE = (255, 214, 120, 255)


def _smooth(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _mid() -> tuple:
    return (FRAME_SIZE[0] / 2.0, FRAME_SIZE[1] / 2.0)


def _radius() -> float:
    return FRAME_SIZE[0] * RING / 2.0


def _seal(pen: _Pen, radius: float, spin: float, alpha: float, light: float) -> None:
    """Her seal, about the middle: her white light, a vermilion ring with a
    ring in it, the brushed strokes between them, and her mark."""
    mid = _mid()
    if alpha <= 0.0:
        return
    for k, grow in enumerate((1.12, 1.04, 0.96)):
        pen.dot(mid, radius * grow, _with_alpha((255, 252, 236, 255), alpha * light * (0.03 + 0.02 * k)))

    def ring(r: float, colour, width: float) -> None:
        pts = [(mid[0] + r * math.cos(a), mid[1] + r * math.sin(a)) for a in (math.tau * i / 72 for i in range(73))]
        pen.line(pts, _with_alpha(colour, alpha), width)

    ring(radius, VERMILION, 6.0)
    ring(radius * 0.84, VERMILION_DARK, 2.4)
    for k in range(16):
        a = math.radians(spin) + math.tau * k / 16
        r0, r1 = radius * 0.87, radius * 0.97
        pen.line([(mid[0] + r0 * math.cos(a), mid[1] + r0 * math.sin(a)), (mid[0] + r1 * math.cos(a + 0.07), mid[1] + r1 * math.sin(a + 0.07))],
                 _with_alpha(SUMI, alpha), 3.0)


def _ring_slips(pen: _Pen, radius: float, turn: float, alpha: float = 1.0, glow: float = 0.5, out: float = 0.0) -> None:
    """The talismans round the ring: each points out from the middle, turned
    ``turn`` degrees round it, ``out`` (0-1) of the way thrown off it."""
    mid = _mid()
    for k in range(SLIPS):
        a = math.radians(turn) + math.tau * k / SLIPS
        r = radius + SLIP * 0.15 + out * radius * (0.18 + 0.08 * math.sin(k * 2.1))
        at = (mid[0] + r * math.cos(a), mid[1] + r * math.sin(a))
        ofuda(pen, at, math.degrees(a) - 90.0 + out * 140.0 * (1 if k % 2 else -1), SLIP * (1.0 - 0.3 * out), flutter=0.3 * math.sin(k + turn / 20.0),
              alpha=alpha, glow=glow)


def _volley(c: Canvas, p: float) -> None:
    """Her ten talismans in flight along +X, wide apart, closing on the
    right edge."""
    w, h = FRAME_SIZE
    pen = _Pen(FRAME_SIZE)
    x0 = w * (1.0 - VOLLEY_SPAN) / 2.0
    x1 = w - x0
    for k in range(SLIPS):
        lag = 0.04 * k
        if p < lag:
            continue
        u = min(1.0, (p - lag) / (1.0 - lag))
        fan = (k / (SLIPS - 1.0) - 0.5) * 0.7
        x = x0 + (x1 - x0) * u
        y = h / 2.0 + fan * h * math.sin(math.pi * u)
        turn = 90.0 + 180.0 * (1.0 + k % 3) * u * (1 if k % 2 else -1)
        for j, (dy, reach) in enumerate(((-4.0, 34.0), (4.0, 22.0))):
            pen.line([(max(x0 - 6.0, x - reach), y + dy), (x - 8.0, y + dy)], _with_alpha(PAPER, 0.45 - 0.15 * j), 2.0)
        ofuda(pen, (x, y), turn, SLIP * 0.9, flutter=0.6 * math.sin(turn / 40.0 + k), glow=0.6 * (1.0 - u * 0.4))
    c.image.alpha_composite(pen.finish())


def _wrap(c: Canvas, p: float) -> None:
    """They come in from the left and go round the head into the ring, and
    the seal opens behind them."""
    pen = _Pen(FRAME_SIZE)
    mid = _mid()
    radius = _radius()
    _seal(pen, radius * (0.4 + 0.6 * _smooth((p - 0.3) / 0.6)), 40.0 * p, _smooth((p - 0.3) / 0.4), 1.0)
    for k in range(SLIPS):
        lag = 0.04 * k
        u = _smooth((p - lag) / (0.85 - lag)) if p > lag else 0.0
        if p <= lag:
            continue
        # Each comes in from the left edge and sweeps round to its place.
        end = math.tau * k / SLIPS
        start = math.pi + (k - SLIPS / 2.0) * 0.08
        a = start + (end - start + (math.tau if end < start else 0.0)) * u
        r = radius + SLIP * 0.15 - (1.0 - u) * radius * 0.35
        at = (mid[0] + r * math.cos(a), mid[1] + r * math.sin(a))
        ofuda(pen, at, math.degrees(a) - 90.0 + (1.0 - u) * 180.0, SLIP, flutter=0.5 * (1.0 - u) * math.sin(k * 1.7 + p * 9.0), glow=0.5 + 0.5 * (1.0 - u))
    if 0.8 <= p:
        # The seal closes: a flash of her light.
        flash = 1.0 - (p - 0.8) / 0.2
        pen.dot(mid, radius * 1.05, _with_alpha((255, 252, 236, 255), 0.25 * flash))
    c.image.alpha_composite(pen.finish())


def _hold(c: Canvas, p: float) -> None:
    """The ring holds the head: a slow turn, by one talisman's place a loop,
    and her light pulsing."""
    pen = _Pen(FRAME_SIZE)
    radius = _radius()
    pulse = 0.5 + 0.5 * math.cos(math.tau * p)
    _seal(pen, radius, 40.0 + 360.0 / 16.0 * p, 1.0, 0.6 + 0.6 * pulse)
    _ring_slips(pen, radius, 360.0 / SLIPS * p, glow=0.3 + 0.5 * pulse)
    c.image.alpha_composite(pen.finish())


def _break(c: Canvas, p: float) -> None:
    """The blow lands: the ring bursts, its talismans are thrown off and burn
    up, scraps fly; nothing is left."""
    pen = _Pen(FRAME_SIZE)
    mid = _mid()
    radius = _radius()
    flash = max(0.0, 1.0 - p / 0.25)
    if flash > 0.0:
        for k, r in enumerate((1.1, 0.8, 0.5)):
            pen.dot(mid, radius * r * (0.8 + 0.3 * p), _with_alpha((255, 250, 236, 255), flash * (0.15 + 0.15 * k)))
    _seal(pen, radius * (1.0 + 0.12 * _smooth(p / 0.5)), 40.0 + 120.0 * p, 1.0 - _smooth(p / 0.45), 1.0)
    out = _smooth(p / 0.8)
    burn = _smooth((p - 0.15) / 0.6)
    gone = _smooth((p - 0.55) / 0.4)
    if gone < 1.0:
        _ring_slips(pen, radius, 0.0, alpha=(1.0 - gone) * (1.0 - 0.6 * burn), glow=0.2, out=out)
        # Each burns from its foot: a red flame where it is.
        for k in range(SLIPS):
            a = math.tau * k / SLIPS
            r = radius + SLIP * 0.15 + out * radius * (0.18 + 0.08 * math.sin(k * 2.1))
            at = (mid[0] + r * math.cos(a), mid[1] + r * math.sin(a))
            size = SLIP * 0.35 * burn * (1.0 - gone)
            if size > 1.0:
                for colour, grow in ((FIRE_OUT, 1.0), (FIRE, 0.7), (FIRE_CORE, 0.38)):
                    s = size * grow
                    pen.poly([(at[0] - s * 0.6, at[1] + s * 0.3), (at[0] + s * 0.15 * math.sin(k + p * 20.0), at[1] - s * 1.6),
                              (at[0] + s * 0.6, at[1] + s * 0.3)], _with_alpha(colour, 1.0 - gone))
                    pen.dot((at[0], at[1] + s * 0.1), s * 0.55, _with_alpha(colour, 1.0 - gone))
    scraps = 1.0 - _smooth((p - 0.4) / 0.6)
    if scraps > 0.0:
        for k in range(14):
            a = math.tau * k / 14 + 0.2
            r = radius * (0.4 + 0.6 * _smooth(p / 0.9) * (0.8 + 0.3 * math.sin(k * 2.7)))
            at = (mid[0] + r * math.cos(a), mid[1] + r * math.sin(a) + 30.0 * p * p)
            s = 5.0 + 2.0 * (k % 3)
            t = a + p * (4.0 + k % 4)
            ct, st = math.cos(t), math.sin(t)
            quad = [(at[0] + u * ct - v * st, at[1] + u * st + v * ct) for u, v in ((-s, -s * 0.6), (s, -s * 0.6), (s, s * 0.6), (-s, s * 0.6))]
            pen.poly(quad, _with_alpha(PAPER, scraps), _with_alpha(SUMI, scraps * 0.7), 1.0)
    c.image.alpha_composite(pen.finish())


DRAWERS = {"great_seal_volley": _volley, "great_seal_wrap": _wrap, "great_seal_hold": _hold, "great_seal_break": _break}

SPECS = {
    "great_seal_volley": make_spec("ofuda", "Kagero's ten paper talismans in flight along +X in a wide fan, closing on the head at the right edge; scaled to the distance by the game.",
                                   placement="world", orientation="positive_x_is_forward", relationship="release", size=300),
    "great_seal_wrap": make_spec("ofuda", "Her ten talismans sweep in from the left and close into a ring round the head, her vermilion seal opening behind them.",
                                 placement="target", relationship="impact", extra_anchor="target", size=300),
    "great_seal_hold": make_spec("ofuda", "The ring of ten talismans holds the head: it turns slowly, the vermilion seal and its strokes pulse with white light.",
                                 loop=True, placement="target", relationship="active", extra_anchor="target", size=300),
    "great_seal_break": make_spec("ofuda", "The blow lands: the ring bursts, its talismans are thrown out and burn up in red fire, paper scraps fly.",
                                  placement="target", relationship="impact", extra_anchor="target", size=300),
}

ORIGINS = {name: (FRAME_SIZE[0] / 2.0, FRAME_SIZE[1] / 2.0) for name, _, _ in ROWS}


def render(out_dir: str | Path, **opts):
    del opts
    return publish_catalog(
        fx=FX,
        target_name=TARGET_NAME,
        display_name="Kagero's great seal VFX",
        character_context_id="npc_ninja_kagero",
        character_context_display="Kagero",
        rows=ROWS,
        drawers=DRAWERS,
        specs=SPECS,
        origins=ORIGINS,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        supersample=1,
        whole_frames=True,
    )


def render_canonical(out_dir: str | Path, **opts):
    del opts
    return publish_canonical(
        target_name=TARGET_NAME,
        rows=ROWS,
        drawers=DRAWERS,
        specs=SPECS,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
    )
