"""Kagero's paper talismans (ofuda), pasted on the Inugami: a worn gear.

Jon (2026-10-29): "I also need a talisman Sprite for the ninja to be able to
use against inugami Wolfenstein, so it's visually clear when they cast the
spell, the ghost will get pasted with a few talismans, and that will be an
additional visual cue that the boss is vulnerable again."

Kagero hunts spirits. Her talisman is a long slip of white paper: a vermilion
band at its head, a brushed seal down its middle, a round red stamp at its
foot. ``ofuda`` draws one, anywhere and at any turn; her effects
(``ninja_kagero_vfx``) throw them, and this target pastes them on the head.

When her spell breaks its ward, the Inugami wears ``kagero_ofuda`` (the game's
``worn_gear.ron``) until it dies: the talismans stay on its brow, its cheek and
its muzzle, so a player sees at a glance that it can be hurt. Gear is drawn
over the anchor part, turns and squashes with it and mirrors with the body, so
the talismans stay on the head in every row it is drawn in. This target
publishes one picture and no sheet:

* ``kagero_ofuda_front.png`` -- the talismans on the head, in the head's own
  frame: the head's pivot (the middle of the head, ``wolfenstein_inugami``'s
  head pixels (0, 0)) is at ``SOCKET``; it faces right.

No shadow.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image

from ambition_sprite2d_renderer.core.draw import blending_draw

TARGET_NAME = "kagero_ofuda"
OUTPUTS = ("kagero_ofuda_front.png",)
#: What the publish installs: the picture, in `sprites/`.
SHEET_FILES = OUTPUTS

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

PAPER: RGBA = (248, 243, 226, 255)
PAPER_SHADE: RGBA = (214, 204, 182, 255)
PAPER_BACK: RGBA = (226, 216, 192, 255)
VERMILION: RGBA = (204, 40, 36, 255)
VERMILION_DARK: RGBA = (150, 22, 26, 255)
SUMI: RGBA = (30, 24, 28, 255)
INK: RGBA = (52, 30, 34, 255)

#: A talisman's width against its length.
ASPECT = 0.3

# ---- One talisman ----------------------------------------------------------------


class _Pen:
    """Draws on a supersampled RGBA image in logical pixels."""

    def __init__(self, size: Tuple[int, int], supersample: int = 4) -> None:
        self.size = size
        self.k = supersample
        self.image = Image.new("RGBA", (size[0] * supersample, size[1] * supersample), (0, 0, 0, 0))
        self.draw = blending_draw(self.image)

    def poly(self, pts: Sequence[Point], fill: RGBA, outline: RGBA | None = None, width: float = 1.0) -> None:
        s = [(x * self.k, y * self.k) for x, y in pts]
        self.draw.polygon(s, fill=fill)
        if outline is not None:
            self.draw.line(s + [s[0]], fill=outline, width=max(1, round(width * self.k)), joint="curve")

    def line(self, pts: Sequence[Point], color: RGBA, width: float) -> None:
        self.draw.line([(x * self.k, y * self.k) for x, y in pts], fill=color, width=max(1, round(width * self.k)), joint="curve")

    def dot(self, c: Point, r: float, fill: RGBA) -> None:
        x, y = c
        self.draw.ellipse(((x - r) * self.k, (y - r) * self.k, (x + r) * self.k, (y + r) * self.k), fill=fill)

    def finish(self) -> Image.Image:
        return self.image.resize(self.size, Image.Resampling.LANCZOS)


def _with_alpha(c: RGBA, a: float) -> RGBA:
    return (c[0], c[1], c[2], max(0, min(255, round(c[3] * a))))


def ofuda(pen, at: Point, turn: float, length: float, *, curl: float = 0.0, flutter: float = 0.0, alpha: float = 1.0,
          glow: float = 0.0) -> None:
    """One talisman on ``pen`` (anything with ``poly``, ``line`` and ``dot``
    in its own pixels): its middle at ``at``, its length along +y turned by
    ``turn`` degrees (clockwise), ``length`` long.

    ``curl`` (0-1) lifts its lower near corner off what it is pasted on (the
    paper's back shows); ``flutter`` (-1 to 1) bends its foot sideways, as in
    flight; ``glow`` (0-1) is the white light of her spell round it."""
    w = length * ASPECT
    h = length
    t = math.radians(turn)
    ct, st = math.cos(t), math.sin(t)

    def P(u: float, v: float) -> Point:
        # (u across, v along) from the middle; the foot bends with flutter.
        v01 = (v + h / 2) / h
        u = u + flutter * w * 0.45 * v01 * v01
        return (at[0] + u * ct - v * st, at[1] + u * st + v * ct)

    def quad(u0: float, v0: float, u1: float, v1: float) -> List[Point]:
        return [P(u0, v0), P(u1, v0), P(u1, v1), P(u0, v1)]

    a = alpha
    lw = max(0.6, length * 0.035)
    if glow > 0.0:
        for k, grow in enumerate((0.5, 0.3, 0.16)):
            g = grow * length * glow
            pen.poly(quad(-w / 2 - g, -h / 2 - g, w / 2 + g, h / 2 + g), _with_alpha((255, 252, 236, 255), a * (0.18 + 0.12 * k) * glow))
    # The slip: its outline, with the curled corner cut away.
    c = curl * w * 0.6
    body = [P(-w / 2, -h / 2), P(w / 2, -h / 2), P(w / 2, h / 2), P(-w / 2 + c, h / 2)]
    if c > 0.0:
        body.append(P(-w / 2, h / 2 - c))
    pen.poly(body, _with_alpha(PAPER, a), _with_alpha(INK, a), lw)
    # A little shade down its far edge: paper, not a card.
    pen.poly(quad(w / 2 - w * 0.16, -h / 2 + lw, w / 2 - lw * 0.5, h / 2 - lw), _with_alpha(PAPER_SHADE, a * 0.6))
    # The vermilion band at its head, and the white sun in it.
    pen.poly(quad(-w / 2 + lw * 0.6, -h / 2 + lw * 0.6, w / 2 - lw * 0.6, -h / 2 + h * 0.17), _with_alpha(VERMILION, a))
    pen.dot(P(0.0, -h / 2 + h * 0.09), w * 0.13, _with_alpha(PAPER, a))
    # The seal, brushed down its middle: a spine with its strokes.
    sw = max(0.7, w * 0.11)
    pen.line([P(0.0, -h * 0.28), P(w * 0.03, h * 0.18)], _with_alpha(SUMI, a), sw)
    for v, reach, slant in ((-0.24, 0.3, -0.04), (-0.12, 0.34, 0.05), (0.0, 0.26, -0.06), (0.1, 0.3, 0.04)):
        pen.line([P(-w * reach, h * (v + slant)), P(w * reach, h * (v - slant))], _with_alpha(SUMI, a), sw * 0.8)
    pen.line([P(-w * 0.22, h * 0.14), P(-w * 0.08, h * 0.2)], _with_alpha(SUMI, a), sw * 0.7)
    pen.line([P(w * 0.24, h * 0.13), P(w * 0.1, h * 0.21)], _with_alpha(SUMI, a), sw * 0.7)
    # The red stamp at its foot.
    pen.dot(P(0.0, h * 0.34), w * 0.2, _with_alpha(VERMILION, a))
    pen.dot(P(0.0, h * 0.34), w * 0.09, _with_alpha(VERMILION_DARK, a))
    if c > 0.0:
        # The lifted corner: the paper's back, folded over.
        pen.poly([P(-w / 2 + c, h / 2), P(-w / 2, h / 2 - c), P(-w / 2 + c * 1.05, h / 2 - c * 1.05)], _with_alpha(PAPER_BACK, a),
                 _with_alpha(INK, a), lw * 0.8)


# ---- Pasted on the head --------------------------------------------------------

#: The Inugami's head pixels (``wolfenstein_inugami``) to world units: its
#: body box is 55 head pixels tall and stands 212 world units.
WORLD_PER_HEAD_PX = 212.0 / 55.0
#: The picture: this many head pixels across, at this many picture pixels to
#: a head pixel, with the head's middle at its middle.
SPAN_HEAD_PX = 72.0
PX_PER_HEAD_PX = 8.0
SIZE = round(SPAN_HEAD_PX * PX_PER_HEAD_PX)
SOCKET = (0.5, 0.5)
#: Its size in the world (``worn_gear.ron``), at a fit scale of 1.
WORLD_SIZE = round(SPAN_HEAD_PX * WORLD_PER_HEAD_PX, 1)

#: Where they are pasted, in head pixels from its middle (facing right): the
#: middle of each talisman, its turn, its length and how far its corner lifts.
#: One seals the brain jar; one is across the back of the skull, its corner
#: lifting; one is under the eye; one is on the bridge of the muzzle. None is
#: over an eye.
PASTED: Sequence[Tuple[Point, float, float, float]] = (
    ((-10.0, -26.0), -24.0, 15.0, 0.0),
    ((-14.0, -2.0), 12.0, 16.0, 0.8),
    ((-2.0, 7.0), -10.0, 13.0, 0.3),
    ((21.0, -3.0), 70.0, 12.0, 0.0),
)


def pasted() -> Image.Image:
    """The talismans on the head, in the picture of the gear."""
    pen = _Pen((SIZE, SIZE))
    mid = SIZE / 2.0
    for (x, y), turn, length, curl in PASTED:
        ofuda(pen, (mid + x * PX_PER_HEAD_PX, mid + y * PX_PER_HEAD_PX), turn, length * PX_PER_HEAD_PX, curl=curl)
    return pen.finish()


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / OUTPUTS[0]
    pasted().save(path)
    return [path]


__all__ = ["OUTPUTS", "SHEET_FILES", "SOCKET", "TARGET_NAME", "WORLD_SIZE", "ofuda", "render"]
