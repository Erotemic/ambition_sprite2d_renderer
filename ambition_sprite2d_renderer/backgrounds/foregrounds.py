"""The foreground of a scene: a few dark things between the eye and the play.

The game draws this layer in front of the play, on a panel 2.2 views wide
that moves a little more than the room does when the camera goes along the
room. It follows the height of the camera only a little: a 16:9 view shows
`v` 0.372 to 0.628 of the panel (`REST_TOP`, `REST_BOTTOM`) at the middle of
its room, and no more than 0.04 lower at the floor of a tall room or higher
at its roof. So a thing that hangs from above is seen at the top of each
view, and a thing that stands from below at the bottom of each view.

What is here must not hide the play:

- Each thing is thin or small, and there are few of them: two or three in a
  view.
- A thing hangs from above and ends a little inside the top of the view at
  rest, or stands from below and ends a little inside the bottom. The middle
  of the view stays empty.
- Each thing is dark, a little clear, and out of focus.

A scene with no entry in `FOREGROUNDS` has no foreground: `draw` publishes an
empty picture for it.
"""

from __future__ import annotations

import math
from typing import Callable

import numpy as np

from .arenas import BOSS, ECLIPSE, HUB
from .artkit import Art, Pen, polar, scale
from .interiors import ALARM, CAVE, FOUNDRY, LAB
from .outdoors import COVE, FOREST, SKYBRIDGE, WATER
from .parts import lamps

SIZE = 1024
#: The blur of the layer in published pixels: it is nearer than the focus.
BLUR = 2.0
#: How much of what is behind a foreground thing it hides.
COVER = 0.72

REST_TOP = 0.372
REST_BOTTOM = 0.628


def _chain(pen: Pen, u: float, v0: float, v1: float, link: float = 0.006) -> None:
    v = v0
    while v < v1:
        pen.ellipse(u, v, link * 0.6, link)
        v += link * 1.7


def _lab(art: Art, pen: Pen, layer_lights: list, glow=None) -> None:
    glow = glow or LAB["glow"]
    rng = art.rand("lab foreground")
    for k in range(5):
        a = k * 0.21 + rng.uniform(-0.04, 0.04)
        pen.curve((a, 0.0), (a + rng.uniform(0.16, 0.26), 0.0), rng.uniform(0.385, 0.415), rng.choice([0.003, 0.004, 0.006]))
    # Lamps that hang on a cord from the roof, with a shade. Nothing stands
    # from below: a cabinet there was a dark box on the floor of each room
    # whose camera is low.
    for u in (0.16, 0.47, 0.80):
        end = rng.uniform(0.385, 0.40)
        pen.rect(u - 0.0012, 0.0, u + 0.0012, end)
        pen.poly([(u - 0.004, end), (u + 0.004, end), (u + 0.012, end + 0.010), (u - 0.012, end + 0.010)])
        layer_lights.append((u, end + 0.0125, 0.0034, glow))


def _alarm(art: Art, pen: Pen, layer_lights: list) -> None:
    _lab(art, pen, layer_lights, ALARM["glow"])


def _foundry(art: Art, pen: Pen, layer_lights: list) -> None:
    rng = art.rand("foundry foreground")
    for k in range(6):
        u = (k + rng.uniform(0.2, 0.8)) / 6.0
        end = rng.uniform(0.38, 0.41)
        _chain(pen, u, 0.0, end)
        if k % 2:
            pen.arc(u, end + 0.012, 0.012, 20, 270, 0.0045)
        else:
            pen.ring(u, end + 0.012, 0.012, 0.004)
    # A few heaps of slag, apart. A ridge the length of the panel was a dark
    # band on the floor of each room whose camera is low.
    for k in range(3):
        u = (k + rng.uniform(0.25, 0.75)) / 3.0
        w = rng.uniform(0.04, 0.06)
        # A heap is the top of a large round: wide and low at each height
        # of the camera.
        for du, part, top in ((0.0, 1.0, REST_BOTTOM - 0.006), (w * 0.9, 0.55, REST_BOTTOM + 0.006)):
            pen.ellipse(u + du, top + 0.07, w * part, 0.07)


def _cave(art: Art, pen: Pen, layer_lights: list) -> None:
    rng = art.rand("cave foreground")
    u = 0.0
    while u < 1.0:
        w = rng.uniform(0.012, 0.045)
        if rng.random() < 0.6:
            tip = rng.uniform(0.30, 0.415)
            pen.poly([(u, 0.0), (u + w, 0.0), (u + w * 0.55, tip)])
        u += w + rng.uniform(0.0, 0.05)
    u = 0.0
    while u < 1.0:
        w = rng.uniform(0.015, 0.05)
        if rng.random() < 0.45:
            tip = rng.uniform(0.595, 0.64)
            pen.poly([(u, 1.0), (u + w, 1.0), (u + w * 0.45, tip)])
        u += w + rng.uniform(0.0, 0.08)


def _cove(art: Art, pen: Pen, layer_lights: list) -> None:
    rng = art.rand("cove foreground")
    # Heads of palms that are over the view: only the fronds come in.
    for u in (0.08, 0.47, 0.90):
        top = (u, 0.30)
        for k in range(7):
            a = 20 + k * 23 + rng.uniform(-6, 6)
            tip = polar(*top, rng.uniform(0.09, 0.115), a)
            ctrl = polar(*top, 0.08, a - 18)
            prev = top
            for i in range(1, 13):
                t = i / 12.0
                x = (1 - t) ** 2 * top[0] + 2 * (1 - t) * t * ctrl[0] + t * t * tip[0]
                y = (1 - t) ** 2 * top[1] + 2 * (1 - t) * t * ctrl[1] + t * t * tip[1]
                pen.line([prev, (x, y)], 0.004 * (1.0 - t * 0.6))
                pen.line([(x, y), (x + 0.004, y + 0.022 * (1.0 - t * 0.5))], 0.002)
                pen.line([(x, y), (x - 0.006, y + 0.018 * (1.0 - t * 0.5))], 0.002)
                prev = (x, y)
    # Reeds and a mooring post below.
    for _ in range(26):
        u = rng.choice([rng.uniform(0.2, 0.36), rng.uniform(0.62, 0.8)])
        h = rng.uniform(0.008, 0.03)
        pen.line([(u, 1.0), (u + rng.uniform(-0.004, 0.004), REST_BOTTOM - h * 0.3), (u + rng.uniform(-0.012, 0.012), REST_BOTTOM - h)], 0.0022)
    pen.rect(0.497, REST_BOTTOM - 0.028, 0.511, 1.0)
    pen.ellipse(0.504, REST_BOTTOM - 0.028, 0.010, 0.004)


def _forest(art: Art, pen: Pen, layer_lights: list) -> None:
    rng = art.rand("forest foreground")
    # Boughs that hang into the view, with leaves.
    for k in range(5):
        u = (k + rng.uniform(0.15, 0.85)) / 5.0
        end = (u + rng.uniform(-0.05, 0.05), rng.uniform(0.385, 0.415))
        pts = [(u + (end[0] - u) * t, end[1] * t**0.8) for t in [i / 10.0 for i in range(11)]]
        pen.line(pts, 0.004)
        for x, y in pts[4:]:
            for _ in range(5):
                a = rng.uniform(20, 160)
                tip = polar(x, y, rng.uniform(0.014, 0.03), a)
                mid = ((x + tip[0]) * 0.5 + 0.006, (y + tip[1]) * 0.5)
                pen.poly([(x, y), mid, tip, ((x + tip[0]) * 0.5 - 0.006, (y + tip[1]) * 0.5)])
    # Grass and ferns below.
    for _ in range(110):
        u = rng.random()
        h = rng.uniform(0.006, 0.03) * (0.3 + 0.7 * abs(math.sin(u * 9.0)))
        lean = rng.uniform(-0.012, 0.012)
        pen.poly([(u - 0.0022, 1.0), (u + 0.0022, 1.0), (u + lean * 0.5 + 0.0012, REST_BOTTOM - h * 0.4), (u + lean, REST_BOTTOM - h)])


def _water(art: Art, pen: Pen, layer_lights: list) -> None:
    rng = art.rand("water foreground")
    for k in range(7):
        u = (k + rng.uniform(0.1, 0.9)) / 7.0
        top = rng.uniform(0.585, 0.615)
        phase, sway = rng.uniform(0, 6.28), rng.uniform(0.008, 0.016)
        pts = [(u + math.sin(v * 30.0 + phase) * sway, v) for v in np.linspace(1.0, top, 30)]
        pen.line(pts, rng.uniform(0.005, 0.008))
        for i in range(4, 30, 3):
            x, y = pts[i]
            side = 1 if i % 2 else -1
            pen.ellipse(x + side * 0.011, y - 0.006, 0.011, 0.0045)


def _skybridge(art: Art, pen: Pen, layer_lights: list) -> None:
    # A line of flags across the top of the view.
    for a, b, sag in ((-0.1, 0.42, 0.045), (0.42, 0.78, 0.035), (0.78, 1.15, 0.045)):
        base = 0.385
        pen.curve((a, base), (b, base), sag, 0.002)
        for k in range(1, 12):
            t = k / 12.0
            u = a + (b - a) * t
            v = base + sag * 4.0 * t * (1.0 - t)
            pen.poly([(u - 0.008, v), (u + 0.008, v), (u, v + 0.022)])


def _boss(art: Art, pen: Pen, layer_lights: list) -> None:
    rng = art.rand("boss foreground")
    for k in range(5):
        u = (k + rng.uniform(0.2, 0.8)) / 5.0
        end = rng.uniform(0.38, 0.41)
        if k % 2:
            _chain(pen, u, 0.0, end)
            pen.poly([(u - 0.01, end), (u + 0.01, end), (u, end + 0.03)])
        else:
            w = 0.022
            pen.rect(u - w, 0.0, u + w, end - 0.02)
            pen.poly([(u - w, end - 0.02), (u - w * 0.4, end + 0.006), (u, end - 0.012), (u + w * 0.5, end + 0.012), (u + w, end - 0.02)])
    # Teeth of rock, apart: a ridge of them the length of the panel was a
    # dark band on the floor of each room whose camera is low.
    for k in range(9):
        u = (k + rng.uniform(0.15, 0.85)) / 9.0
        w = rng.uniform(0.006, 0.012)
        tip = REST_BOTTOM - rng.uniform(0.004, 0.014)
        pen.poly([(u - w, 1.0), (u - w, REST_BOTTOM + 0.05), (u + rng.uniform(-0.3, 0.3) * w, tip), (u + w, REST_BOTTOM + 0.05), (u + w, 1.0)])


def _eclipse(art: Art, pen: Pen, layer_lights: list) -> None:
    rng = art.rand("eclipse foreground")
    for _ in range(16):
        u = rng.random()
        v = rng.choice([rng.uniform(0.34, 0.395), rng.uniform(0.605, 0.66)])
        s = rng.uniform(0.008, 0.022)
        a = rng.uniform(0, 360)
        pen.poly([polar(u, v, s * rng.uniform(0.55, 1.0), a + k * 72) for k in range(5)])


def _hub(art: Art, pen: Pen, layer_lights: list) -> None:
    # Wires with lamps on them across the top.
    for a, b, sag in ((-0.08, 0.36, 0.05), (0.36, 0.71, 0.04), (0.71, 1.1, 0.05)):
        base = 0.378
        pen.curve((a, base), (b, base), sag, 0.0018)
        for k in range(1, 9):
            t = k / 9.0
            u = a + (b - a) * t
            v = base + sag * 4.0 * t * (1.0 - t)
            pen.rect(u - 0.0012, v, u + 0.0012, v + 0.008)
            layer_lights.append((u, v + 0.012, 0.0042, HUB["warm"]))


FOREGROUNDS: dict[str, tuple[Callable[[Art, Pen, list], None], tuple[int, int, int]]] = {
    "hub": (_hub, scale(HUB["city"], 0.7)),
    "lab": (_lab, scale(LAB["steel"], 0.7)),
    "alarm": (_alarm, scale(ALARM["steel"], 0.9)),
    "basement": (_foundry, scale(FOUNDRY["iron"], 0.8)),
    "cave": (_cave, scale(CAVE["rock"], 0.8)),
    "cove": (_cove, scale(COVE["rock"], 0.8)),
    "water": (_water, scale(WATER["kelp"], 0.6)),
    "forest": (_forest, scale(FOREST["near"], 0.9)),
    "skybridge": (_skybridge, SKYBRIDGE["stone"]),
    "boss": (_boss, scale(BOSS["rock"], 0.8)),
    "eclipse": (_eclipse, scale(ECLIPSE["rock"], 0.9)),
}


def render(theme_key: str, size: int | None = None):
    """The published picture of the foreground of a scene, or `None` for a
    scene that has none."""
    if theme_key not in FOREGROUNDS:
        return None
    draw, colour = FOREGROUNDS[theme_key]
    art = Art(size or SIZE, theme_key, "foreground")
    image, pen = art.drawing()
    lights: list = []
    draw(art, pen, lights)
    mask = art.mask_of(image)
    extra = getattr(art, "extra", None)
    if extra is not None:
        mask = np.maximum(mask, extra)
    layer = art.blank()
    art.put(layer, mask, colour, COVER)
    for u, v, r, light in lights:
        lamps(art, layer, [(u, v, r)], light, halo=3.0, strength=0.8)
    return art.publish(layer, blur=BLUR * (art.size / SIZE))
