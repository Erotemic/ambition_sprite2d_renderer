"""Kagero's spell: her talismans thrown at the Inugami, and their seal on it.

Jon (2026-10-29): "I also need a talisman Sprite for the ninja to be able to
use against inugami Wolfenstein, so it's visually clear when they cast the
spell, the ghost will get pasted with a few talismans".

* ``ofuda_volley`` -- her five talismans in flight, along +X: they leave the
  left of the frame together, fan apart, turn over in the air and close in on
  its right edge, where the head is. The game plays it midway between her and
  the head, turned toward the head and scaled to the distance (its talismans
  cross ``VOLLEY_SPAN`` of the frame), for her spell's flight (``kagero.rs``
  ``FLY_S``: the row is as long).
* ``ofuda_seal`` -- they strike the head: a flash of white paper light, the
  red ring of her seal opening out with its brushed strokes, and scraps of
  paper thrown off. Then the talismans stay on the head (the worn gear
  ``kagero_ofuda``).

Each talisman is ``kagero_ofuda.ofuda``, the one she wears at her sash and
pastes on the head. Each frame is square (the game draws an effect into a
square, turned by the pose it is given), and each draws its own end. No
shadow.

The sheet is OWNED by Kagero and by the Inugami (``owners``): it is decoded
with either, so it is resident before she throws.
"""

from __future__ import annotations

import math
from pathlib import Path

from ._character_vfx_common import Canvas, make_spec, publish_canonical, publish_catalog, sheet_files
from .kagero_ofuda import PAPER, VERMILION, VERMILION_DARK, SUMI, _Pen, _with_alpha, ofuda

TARGET_NAME = "ninja_kagero_vfx"
FX = {"cue_family": "ninja_kagero", "residency": "OwnedByCharacter", "fade": "InItsFrames",
      "owners": ["npc_ninja_kagero", "npc_wolfenstein_inugami"]}
SHEET_FILES = sheet_files(TARGET_NAME)
FRAME_SIZE = (192, 192)
#: The share of the frame's width her talismans cross in ``ofuda_volley``:
#: the game scales the effect so this is the distance to the head.
VOLLEY_SPAN = 0.84

ROWS = [
    # As long as her spell's flight (`kagero.rs` FLY_S, 0.3 s), and one
    # clear frame.
    ("ofuda_volley", 11, 30),
    ("ofuda_seal", 12, 45),
]

#: Her five talismans: how far each is behind the first (a share of the
#: flight), how far it fans out of the line (a share of the frame), and how
#: many half turns it makes in the air.
VOLLEY = ((0.0, 0.0, 1.0), (0.06, -0.16, -1.0), (0.1, 0.17, 1.5), (0.16, -0.08, -1.5), (0.2, 0.09, 2.0))


def _smooth(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _volley(c: Canvas, p: float) -> None:
    """Her talismans in flight, along +X from the left of the frame to its
    right; ``p`` is the share of the flight done (0-1)."""
    w, h = FRAME_SIZE
    pen = _Pen(FRAME_SIZE)
    x0 = w * (1.0 - VOLLEY_SPAN) / 2.0
    x1 = w - x0
    for k, (lag, fan, turns) in enumerate(VOLLEY):
        u = max(0.0, min(1.0, (p - lag) / (1.0 - lag)))
        if p < lag:
            continue
        # Out of her hand together, apart in the air, together on the head.
        x = x0 + (x1 - x0) * u
        y = h / 2.0 + fan * h * math.sin(math.pi * u)
        turn = 90.0 + 180.0 * turns * u
        length = 30.0
        # Lines of speed behind it.
        for j, (dy, reach) in enumerate(((-3.0, 26.0), (3.0, 18.0))):
            pen.line([(max(x0 - 6.0, x - reach), y + dy), (x - 6.0, y + dy)], _with_alpha(PAPER, 0.45 - 0.15 * j), 1.6)
        ofuda(pen, (x, y), turn, length, flutter=0.6 * math.sin(turn / 40.0 + k), glow=0.55 * (1.0 - u * 0.5))
    c.image.alpha_composite(pen.finish())


def _seal(c: Canvas, p: float) -> None:
    """They strike: a flash of paper light, her seal's red ring opening out
    with its strokes, and scraps of paper thrown off; it all draws its own end."""
    w, h = FRAME_SIZE
    mid = (w / 2.0, h / 2.0)
    pen = _Pen(FRAME_SIZE)
    # The flash: white, at once, gone by a third of the row.
    flash = max(0.0, 1.0 - p / 0.33)
    if flash > 0.0:
        for k, r in enumerate((44.0, 30.0, 16.0)):
            pen.dot(mid, r * (0.7 + 0.5 * p), _with_alpha(PAPER, flash * (0.3 + 0.25 * k)))
    # The seal: a red ring opening out, its strokes round it, fading out.
    ring = 22.0 + 58.0 * _smooth(p / 0.7)
    fade = 1.0 - _smooth((p - 0.45) / 0.55)
    if fade > 0.0:
        pts = [(mid[0] + ring * math.cos(a), mid[1] + ring * math.sin(a)) for a in (math.tau * i / 48 for i in range(49))]
        pen.line(pts, _with_alpha(VERMILION, fade), 5.0 * (1.0 - 0.5 * p))
        inner = [(mid[0] + ring * 0.78 * math.cos(a), mid[1] + ring * 0.78 * math.sin(a)) for a in (math.tau * i / 48 for i in range(49))]
        pen.line(inner, _with_alpha(VERMILION_DARK, fade * 0.8), 1.6)
        # The brushed strokes of the seal, between the rings, turning a little.
        for k in range(8):
            a = math.tau * k / 8 + 0.6 * p
            r0, r1 = ring * 0.82, ring * 0.96
            q0 = (mid[0] + r0 * math.cos(a), mid[1] + r0 * math.sin(a))
            q1 = (mid[0] + r1 * math.cos(a + 0.12), mid[1] + r1 * math.sin(a + 0.12))
            pen.line([q0, q1], _with_alpha(SUMI, fade), 2.2)
    # Scraps of paper thrown off, turning, falling a little.
    scraps = 1.0 - _smooth((p - 0.35) / 0.65)
    if scraps > 0.0:
        for k in range(9):
            a = math.tau * k / 9 + 0.3
            r = 18.0 + 70.0 * _smooth(p / 0.8) * (0.8 + 0.25 * math.sin(k * 2.1))
            at = (mid[0] + r * math.cos(a), mid[1] + r * math.sin(a) + 14.0 * p * p)
            s = 4.0 + 1.5 * (k % 3)
            t = a + p * (3.0 + k % 4)
            ct, st = math.cos(t), math.sin(t)
            quad = [(at[0] + u * ct - v * st, at[1] + u * st + v * ct) for u, v in ((-s, -s * 0.6), (s, -s * 0.6), (s, s * 0.6), (-s, s * 0.6))]
            pen.poly(quad, _with_alpha(PAPER, scraps), _with_alpha(SUMI, scraps * 0.7), 0.8)
    c.image.alpha_composite(pen.finish())


DRAWERS = {"ofuda_volley": _volley, "ofuda_seal": _seal}

SPECS = {
    "ofuda_volley": make_spec("ofuda", "Kagero's five paper talismans in flight along +X, fanning apart and closing on the head at the right edge; scaled to the distance by the game.",
                              placement="world", orientation="positive_x_is_forward", relationship="release", size=180),
    "ofuda_seal": make_spec("ofuda", "Her talismans strike the head: a paper-white flash, the red ring of her seal opening with brushed strokes, paper scraps thrown off.",
                            placement="target", relationship="impact", extra_anchor="target", size=180),
}

ORIGINS = {name: (FRAME_SIZE[0] / 2.0, FRAME_SIZE[1] / 2.0) for name, _, _ in ROWS}


def render(out_dir: str | Path, **opts):
    del opts
    return publish_catalog(
        fx=FX,
        target_name=TARGET_NAME,
        display_name="Kagero's spell VFX",
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
