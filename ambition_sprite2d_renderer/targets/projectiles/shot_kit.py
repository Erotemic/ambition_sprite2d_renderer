"""The plain shots of the game, as one sheet: one row for each shot.

These are the shots that had no art of their own. The robot's fireball and
Hadouken were one blob texture with a tint (`projectile_energy.png`). A thrown
rock, a magic bolt and the dilophosaurus's spit had no look at all, so the game
drew the engine's plain orange box (`ProjectileArt::generic`).

Each row is one look, registered by `game/ambition_content/src/projectiles.rs`:

* ``fireball``: the robot's fireball. A comet of fire: a white-hot nose, an
  orange body, tongues of flame behind it.
* ``coldfire``: the same comet in blue (the Mockingbird, once its fire is cold).
* ``hadouken``: the robot's Hadouken. A ball of blue force behind a bright
  crescent front, with streamers behind.
* ``hadouken_super``: the same, larger, with a second crescent and sparks.
* ``spit``: a glob of venom with drops behind it (the dilophosaurus).
* ``rock``: a thrown rock, which tumbles.
* ``bolt``: a bolt of magic: a violet diamond with a pale core and motes behind.

AUTHORED POINTING +X, as every projectile sheet is: the nose is at the right
and the tail is at the left. Flat shapes, in the colours of who fires them; a
dark rim in the shot's own hue and no black ink line, because these are light
(the rock has an ink line: it is a thing).

Each row loops. What moves is the tail and the core, never the outline of the
nose: a shot whose front edge beats reads as a fault.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Callable, Dict, List, Sequence, Tuple

from PIL import Image

from ambition_sprite2d_renderer.core.draw import blending_draw

from ...authoring.sheet_build import build_sheet, write_canonical

TARGET_NAME = "shot_kit"
#: The middle of the frame is the middle of the HEAD of each shot (the ball of
#: a comet, not the middle of its length): the game puts the middle of the
#: frame on the middle of the shot's body, so the tail is behind the body.
FRAME_W, FRAME_H = 128, 64
SUPERSAMPLE = 4

#: (name, frames, ms).
ROWS: List[Tuple[str, int, int]] = [
    ("fireball", 6, 55),
    ("coldfire", 6, 55),
    ("hadouken", 6, 55),
    ("hadouken_super", 6, 50),
    ("spit", 4, 70),
    ("rock", 4, 80),
    ("bolt", 4, 60),
]

Point = Tuple[float, float]
RGBA = Tuple[int, int, int, int]

CX, CY = FRAME_W / 2, FRAME_H / 2


def _canvas():
    img = Image.new("RGBA", (FRAME_W * SUPERSAMPLE, FRAME_H * SUPERSAMPLE), (0, 0, 0, 0))
    return img, blending_draw(img)


def _s(points: Sequence[Point]) -> List[Point]:
    return [(x * SUPERSAMPLE, y * SUPERSAMPLE) for x, y in points]


def _poly(draw, points: Sequence[Point], fill: RGBA) -> None:
    draw.polygon(_s(points), fill=fill)


def _ellipse(draw, cx: float, cy: float, rx: float, ry: float, fill: RGBA) -> None:
    draw.ellipse(
        ((cx - rx) * SUPERSAMPLE, (cy - ry) * SUPERSAMPLE, (cx + rx) * SUPERSAMPLE, (cy + ry) * SUPERSAMPLE), fill=fill
    )


def _comet(nose: float, tail: float, half: float, wave: float, tongues: int, phase: float) -> List[Point]:
    """A round nose at the right and a tail of tongues to the left. ``phase``
    moves the tongues; the nose does not move."""
    top: List[Point] = []
    steps = 10
    for i in range(steps + 1):
        a = -math.pi / 2 + math.pi * i / steps
        top.append((nose - half + half * math.cos(a), CY + half * math.sin(a)))
    # top is the nose from its top to its bottom; then the lower edge to the tail, then back along the upper edge
    body = nose - half
    lower: List[Point] = []
    upper: List[Point] = []
    n = tongues * 2
    for i in range(1, n + 1):
        t = i / n
        x = body - (body - tail) * t
        # the tail narrows, and each second point is a tongue that goes out and back
        width = half * (1.0 - 0.72 * t)
        if i % 2 == 1:
            # the tongue next to the head is small: it must not stand out past the head
            flare = wave * (0.25 if i == 1 else 1.0)
            width *= 1.0 + flare * (0.55 + 0.45 * math.sin(phase * math.tau + i * 1.9))
        else:
            width *= 0.55
        lower.append((x, CY + width))
        upper.append((x, CY - width))
    tip = [(tail - 4.0 - 3.0 * math.sin(phase * math.tau), CY)]
    return top + lower + tip + upper[::-1]


#: The colours of a comet of fire, from its rim to its core, then its sparks.
_HOT = ((150, 32, 20, 235), (240, 92, 26, 255), (255, 176, 46, 255), (255, 236, 150, 255), (255, 255, 240, 255), (255, 190, 70))
_COLD = ((20, 44, 132, 235), (40, 110, 232, 255), (96, 184, 255, 255), (190, 236, 255, 255), (244, 252, 255, 255), (150, 214, 255))


def _fireball(phase: float, colours=_HOT) -> Image.Image:
    img, d = _canvas()
    nose = CX + 21.0
    _poly(d, _comet(nose, 10.0, 21.0, 0.55, 4, phase), colours[0])
    _poly(d, _comet(nose - 1.5, 16.0, 18.0, 0.5, 4, phase + 0.2), colours[1])
    _poly(d, _comet(nose - 3.0, 31.0, 13.5, 0.42, 3, phase + 0.45), colours[2])
    _poly(d, _comet(nose - 4.5, 49.0, 8.5, 0.3, 2, phase + 0.7), colours[3])
    _ellipse(d, nose - 12.0, CY - 1.0, 5.2, 4.6, colours[4])
    # sparks that the tail leaves
    for k in range(4):
        t = (phase + k * 0.27) % 1.0
        x = 27.0 - 22.0 * t
        y = CY + (-1) ** k * (9.0 + 9.0 * t) + 2.0 * math.sin(k * 2.1)
        r = 2.4 * (1.0 - t)
        _poly(d, [(x + r, y), (x, y - r), (x - r * 1.6, y), (x, y + r)], (*colours[5], int(255 * (1.0 - t))))
    return img


def _crescent(cx: float, radius: float, thick: float, spread: float, fill: RGBA, d) -> None:
    """A crescent that opens to the left: the front of the wave."""
    outer: List[Point] = []
    inner: List[Point] = []
    steps = 14
    for i in range(steps + 1):
        a = -spread + 2 * spread * i / steps
        outer.append((cx + radius * math.cos(a), CY + radius * math.sin(a)))
        inner.append((cx - thick + (radius - thick * 0.35) * math.cos(a), CY + (radius - thick * 0.2) * math.sin(a) * 0.96))
    _poly(d, outer + inner[::-1], fill)


def _hadouken(phase: float, big: bool) -> Image.Image:
    img, d = _canvas()
    scale = 1.0 if not big else 1.22
    cx = CX
    r = 17.0 * scale
    # streamers behind the ball
    for k, (dy, length) in enumerate([(-0.62, 44.0), (0.0, 54.0), (0.62, 44.0)]):
        wob = 2.5 * math.sin(phase * math.tau + k * 2.1)
        y = CY + dy * r
        width = (5.5 if dy else 7.0) * scale
        _poly(d, [(cx, y - width), (cx - length * 0.55, y - width * 0.45 + wob), (cx - length - wob, y + wob * 0.6),
                  (cx - length * 0.55, y + width * 0.45 + wob), (cx, y + width)], (40, 92, 214, 170))
    _ellipse(d, cx, CY, r + 3.0, r + 3.0, (24, 60, 170, 235))
    _ellipse(d, cx, CY, r, r, (62, 140, 255, 255))
    # the ball turns: two lobes of pale blue go round its middle
    for k in range(2):
        a = phase * math.tau + k * math.pi
        _ellipse(d, cx + 0.45 * r * math.cos(a), CY + 0.45 * r * math.sin(a), r * 0.42, r * 0.34, (132, 204, 255, 255))
    _ellipse(d, cx + 2.0, CY, r * 0.36, r * 0.36, (236, 250, 255, 255))
    _crescent(cx + 6.0, r + 7.0, 7.0 * scale, 1.05, (232, 248, 255, 255), d)
    if big:
        _crescent(cx - 6.0, r + 9.0, 5.0, 0.9, (150, 214, 255, 230), d)
        for k in range(5):
            t = (phase * 1.0 + k * 0.2) % 1.0
            a = k * 1.4 + 0.6
            x = cx - 8.0 - 40.0 * t
            y = CY + (r + 6.0) * math.sin(a) * (1.0 - 0.3 * t)
            q = 2.8 * (1.0 - t)
            _poly(d, [(x + q, y), (x, y - q), (x - q, y), (x, y + q)], (214, 240, 255, int(255 * (1.0 - t))))
    return img


def _blob(cx: float, cy: float, r: float, phase: float, lumps: int, amount: float) -> List[Point]:
    pts: List[Point] = []
    steps = 28
    for i in range(steps):
        a = math.tau * i / steps
        k = 1.0 + amount * math.sin(a * lumps + phase * math.tau) + amount * 0.5 * math.sin(a * 2 - phase * math.tau)
        # longer along the way it flies
        pts.append((cx + r * 1.18 * k * math.cos(a), cy + r * 0.9 * k * math.sin(a)))
    return pts


def _spit(phase: float) -> Image.Image:
    img, d = _canvas()
    # the drops behind, smaller as they are farther back
    for k, (x, dy, r) in enumerate([(38.0, -5.0, 6.0), (25.0, 4.0, 4.4), (14.0, -2.0, 3.0)]):
        y = CY + dy + 1.6 * math.sin(phase * math.tau + k * 1.7)
        d_pts = _blob(x, y, r + 1.4, phase + k * 0.3, 3, 0.1)
        _poly(d, d_pts, (58, 96, 22, 240))
        _poly(d, _blob(x, y, r, phase + k * 0.3, 3, 0.1), (170, 214, 52, 255))
    _poly(d, _blob(CX, CY, 17.0, phase, 3, 0.085), (58, 96, 22, 245))
    _poly(d, _blob(CX, CY, 14.8, phase, 3, 0.085), (150, 200, 44, 255))
    _poly(d, _blob(CX + 2.5, CY - 1.5, 10.0, phase + 0.25, 3, 0.07), (204, 236, 84, 255))
    _ellipse(d, CX + 7.0, CY - 5.0, 4.2, 2.8, (246, 255, 200, 255))
    # a bubble in it
    _ellipse(d, CX - 6.0, CY + 5.0, 2.6, 2.6, (116, 164, 34, 255))
    return img


#: The rock, about its middle: a lump of five sides, and its facets.
_ROCK = [(-15.0, -4.0), (-6.0, -14.0), (9.0, -12.0), (16.0, 1.0), (7.0, 13.0), (-9.0, 11.0)]
_ROCK_LIGHT = [(-6.0, -14.0), (9.0, -12.0), (6.0, -2.0), (-7.0, -3.0)]
_ROCK_DARK = [(16.0, 1.0), (7.0, 13.0), (-9.0, 11.0), (-2.0, 3.0), (6.0, -2.0)]


def _turn(points: Sequence[Point], deg: float, at: Point) -> List[Point]:
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return [(at[0] + x * c - y * s, at[1] + x * s + y * c) for x, y in points]


def _rock(frame: int) -> Image.Image:
    img, d = _canvas()
    at = (CX, CY)
    deg = 90.0 * frame
    grown = [(x * 1.12, y * 1.12) for x, y in _ROCK]
    _poly(d, _turn(grown, deg, at), (38, 32, 30, 255))
    _poly(d, _turn(_ROCK, deg, at), (134, 122, 110, 255))
    # The light is from above: the facets that face up are light in each frame.
    _poly(d, _turn(_ROCK_DARK, deg, at), (96, 86, 80, 255))
    _poly(d, _turn(_ROCK_LIGHT, deg, at), (178, 168, 152, 255))
    # two short lines of dust behind it
    for dy, length in ((-9.0, 16.0), (8.0, 12.0)):
        _poly(d, [(40.0, CY + dy - 1.2), (40.0 - length, CY + dy), (40.0, CY + dy + 1.2)], (190, 180, 166, 170))
    return img


def _bolt(phase: float) -> Image.Image:
    img, d = _canvas()
    beat = 1.0 + 0.1 * math.sin(phase * math.tau)
    nose, mid, tail = CX + 26.0, CX, CX - 48.0
    for half, back, fill in (
        (15.0 * beat, tail, (74, 30, 120, 235)),
        (11.5 * beat, tail + 14.0, (146, 70, 214, 255)),
        (7.0 * beat, tail + 30.0, (226, 150, 255, 255)),
        (3.2, tail + 44.0, (255, 240, 255, 255)),
    ):
        _poly(d, [(nose, CY), (mid, CY - half), (back, CY), (mid, CY + half)], fill)
    # motes that fall behind
    for k in range(4):
        t = (phase + k * 0.25) % 1.0
        x = 42.0 - 30.0 * t
        y = CY + (-1) ** k * (10.0 + 5.0 * t)
        q = 3.0 * (1.0 - t)
        _poly(d, [(x + q, y), (x, y - q), (x - q, y), (x, y + q)], (236, 170, 255, int(255 * (1.0 - t))))
    return img


def _phase(frame_idx: int, nframes: int) -> float:
    return frame_idx / max(1, nframes)


_DRAW: Dict[str, Callable[[int, int], Image.Image]] = {
    "fireball": lambda i, n: _fireball(_phase(i, n)),
    "coldfire": lambda i, n: _fireball(_phase(i, n), _COLD),
    "hadouken": lambda i, n: _hadouken(_phase(i, n), False),
    "hadouken_super": lambda i, n: _hadouken(_phase(i, n), True),
    "spit": lambda i, n: _spit(_phase(i, n)),
    "rock": lambda i, n: _rock(i),
    "bolt": lambda i, n: _bolt(_phase(i, n)),
}


def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    return _DRAW[animation](frame_idx, nframes).resize((FRAME_W, FRAME_H), Image.LANCZOS)


# Projectiles, not a character: a `prop_` id keeps the actor-contract emitter
# from filing the sheet under the `npc_` names, as the other projectile sheets do.
ACTOR_METADATA = {
    "actor": {"character_id": "prop_shot_kit", "display_name": "Plain Shots"},
    "visual_description": {
        "intent": "The plain shots of the game, one row each, authored travelling +x.",
        "visual_language": [
            "flat shapes, a dark rim in the shot's own hue, no black ink line on light",
            "the tail and the core move; the outline of the nose does not",
        ],
    },
    "gameplay_description": {
        "role": "the looks of shots that have no art of their own",
        "authoring_notes": [
            "Authored pointing +x.",
            "Every row loops.",
        ],
    },
    "tags": ["projectile", "fireball", "hadouken", "spit", "rock", "bolt"],
}


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=Path(out_dir),
        frame_size=(FRAME_W, FRAME_H),
        auto_crop=True,
        crop_margin=2,
        actor_metadata=ACTOR_METADATA,
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    return [Path(outputs[key]) for key in keys if outputs.get(key)]


def render_canonical(out_dir: str | Path, **opts):
    del opts
    return write_canonical(TARGET_NAME, ROWS, render_frame, Path(out_dir), frame_size=(FRAME_W, FRAME_H))


__all__ = ["ACTOR_METADATA", "ROWS", "TARGET_NAME", "render", "render_canonical", "render_frame"]
