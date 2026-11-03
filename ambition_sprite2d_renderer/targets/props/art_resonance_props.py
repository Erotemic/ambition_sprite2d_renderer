"""The props of the Resonant Reach, the music quarter of the Art dimension.

They are drawn in the cel style of the dimension's cast
(`targets/characters/_art_cast_kit.py`), in the colours of the Reach: night
blue, brass, ivory and ebony, with cyan for sound.

- ``art_chime``: scenery (a `Prop`), and the look of each of the three
  chimes of the Reach (levers). A tall tube of brass that hangs from an
  ebony stand, with a striker that hangs on a hook by it.
- ``art_chord_bar_<syllable>``: a door (the look of a `LockWall` of 32 by
  128 world units, drawn at 3 to 1). A golden organ pipe in a rack of
  ebony. On the pipe is a plaque with its note: the note on a staff, its
  letter (C, E or G) and its syllable (do, mi or sol). The chime of the
  same syllable opens it.
- ``art_grand_piano``: scenery. A grand piano with its lid up on its stick.
- ``art_metronome``: scenery. A tall metronome; its ``idle`` row is the
  tick and the tock of its rod.

Animations: ``idle``. No drop shadows: the game draws them.
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

from ..characters import _art_cast_kit as K
from .art_props import _publisher

Point = Tuple[float, float]

#: The colours of the Reach.
NIGHT = (36, 44, 104, 255)
NIGHT_LIGHT = (70, 84, 168, 255)
EBONY = (30, 26, 44, 255)
EBONY_LIGHT = (66, 64, 104, 255)
IVORY = (250, 242, 220, 255)
IVORY_SHADE = (214, 202, 176, 255)
BRASS = K.GOLD
BRASS_LIGHT = (255, 226, 140, 255)
BRASS_DARK = K.GOLD_DARK
SOUND = K.CYAN

STILL: List[Tuple[str, int, int]] = [("idle", 1, 1000)]

# ---------------------------------------------------------------------------
# Letters, as strokes in a box of 1 by 1 (y down).
# ---------------------------------------------------------------------------


def _arc(cx: float, cy: float, rx: float, ry: float, a0: float, a1: float, count: int = 16) -> List[Point]:
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * k / (count - 1))), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * k / (count - 1)))) for k in range(count)]


GLYPHS: Dict[str, List[List[Point]]] = {
    "C": [_arc(0.55, 0.5, 0.45, 0.5, -45.0, -315.0, 20)],
    "E": [[(0.85, 0.0), (0.2, 0.0), (0.2, 1.0), (0.85, 1.0)], [(0.2, 0.5), (0.7, 0.5)]],
    "G": [_arc(0.55, 0.5, 0.45, 0.5, -45.0, -340.0, 20) + [(0.98, 0.58)], [(0.98, 0.58), (0.98, 0.95)], [(0.62, 0.58), (0.98, 0.58)]],
    "d": [_arc(0.4, 0.68, 0.32, 0.32, 0.0, 360.0, 18), [(0.72, 0.0), (0.72, 1.0)]],
    "o": [_arc(0.5, 0.68, 0.36, 0.32, 0.0, 360.0, 18)],
    "m": [[(0.05, 1.0), (0.05, 0.36)], _arc(0.27, 0.56, 0.22, 0.2, 180.0, 360.0, 8) + [(0.49, 1.0)], _arc(0.71, 0.56, 0.22, 0.2, 180.0, 360.0, 8) + [(0.93, 1.0)]],
    "i": [[(0.5, 0.4), (0.5, 1.0)]],
    "s": [[(0.85, 0.42), (0.6, 0.36), (0.25, 0.4), (0.18, 0.55), (0.5, 0.67), (0.82, 0.8), (0.75, 0.96), (0.45, 1.0), (0.12, 0.94)]],
    "l": [[(0.5, 0.0), (0.5, 1.0)]],
}
#: Letters with a dot over them: the dot, in the same box.
DOTS = {"i": (0.5, 0.18)}


def _write(f: K.Frame, text: str, x: float, y: float, h: float, width: float, colour, glow=None) -> None:
    """`text` in strokes, its box `h` tall, its left edge at `x`."""
    advance = {"m": 0.95, "i": 0.35, "l": 0.35}
    for ch in text:
        w = h * 0.62
        for stroke in GLYPHS[ch]:
            pts = [(x + px * w, y + py * h) for px, py in stroke]
            if glow:
                f.glow_line(pts, width * 2.2, glow)
            f.ink(pts, width, colour)
        if ch in DOTS:
            dx, dy = DOTS[ch]
            f.dot(x + dx * w, y + dy * h, width * 0.75, colour)
        x += w * advance.get(ch, 0.8) + h * 0.22


def _text_width(text: str, h: float) -> float:
    advance = {"m": 0.95, "i": 0.35, "l": 0.35}
    return sum(h * 0.62 * advance.get(ch, 0.8) + h * 0.22 for ch in text) - h * 0.22


# ---------------------------------------------------------------------------
# The chime.
# ---------------------------------------------------------------------------

CHIME_FRAME = (96, 256)


def _draw_chime():
    w, h = CHIME_FRAME
    f = K.Frame(CHIME_FRAME)
    foot = h - 3.0
    post_x, arm_y = 22.0, 16.0
    tube_x, tube_w, tube_top, tube_foot = 58.0, 19.0, 40.0, 214.0
    # The stand: a heavy foot, a post, and an arm across the top.
    f.poly([(8.0, foot), (88.0, foot), (84.0, foot - 12.0), (12.0, foot - 12.0)], EBONY)
    f.poly([(8.0, foot), (88.0, foot), (87.0, foot - 4.0), (9.0, foot - 4.0)], EBONY_LIGHT, body=False)
    f.ink([(13.0, foot - 11.0), (83.0, foot - 11.0)], 1.0, BRASS)
    f.poly([(post_x - 5.0, foot - 12.0), (post_x + 5.0, foot - 12.0), (post_x + 4.0, arm_y), (post_x - 4.0, arm_y)], EBONY)
    f.ink([(post_x - 2.0, foot - 14.0), (post_x - 1.5, arm_y + 4.0)], 1.0, EBONY_LIGHT)
    f.poly([(post_x - 6.0, arm_y - 6.0), (tube_x + 14.0, arm_y - 6.0), (tube_x + 16.0, arm_y), (tube_x + 14.0, arm_y + 4.0), (post_x - 6.0, arm_y + 4.0)], EBONY)
    f.ellipse(post_x, arm_y - 8.0, 4.0, 4.0, BRASS)
    f.ellipse(tube_x + 16.0, arm_y - 1.0, 3.2, 3.2, BRASS)
    # The cords from the arm to the cap of the tube.
    for dx in (-4.0, 4.0):
        f.ink([(tube_x + dx * 0.5, arm_y + 4.0), (tube_x + dx, tube_top - 2.0)], 1.0, K.shade(IVORY_SHADE, 0.8))
    # The tube of brass, a cap at its top and a ring near its foot.
    f.poly([(tube_x - tube_w / 2.0, tube_top), (tube_x + tube_w / 2.0, tube_top), (tube_x + tube_w / 2.0, tube_foot), (tube_x - tube_w / 2.0, tube_foot)], BRASS)
    f.poly([(tube_x + tube_w * 0.18, tube_top), (tube_x + tube_w / 2.0, tube_top), (tube_x + tube_w / 2.0, tube_foot), (tube_x + tube_w * 0.18, tube_foot)], BRASS_DARK, body=False)
    f.limb([(tube_x - tube_w * 0.28, tube_top + 6.0), (tube_x - tube_w * 0.28, tube_foot - 6.0)], 2.4, BRASS_LIGHT, body=False)
    f.poly([(tube_x - tube_w / 2.0 - 1.5, tube_top - 5.0), (tube_x + tube_w / 2.0 + 1.5, tube_top - 5.0), (tube_x + tube_w / 2.0 + 1.5, tube_top + 4.0), (tube_x - tube_w / 2.0 - 1.5, tube_top + 4.0)], BRASS_DARK)
    f.ellipse(tube_x, tube_foot, tube_w / 2.0, 2.4, K.shade(BRASS_DARK, 0.7))
    f.ink([(tube_x - tube_w / 2.0, tube_foot - 22.0), (tube_x + tube_w / 2.0, tube_foot - 22.0)], 1.2, BRASS_DARK)
    # The striker on its hook: a handle of ebony and a head of leather.
    hook_y = 108.0
    f.limb([(post_x + 4.0, hook_y), (post_x + 9.0, hook_y), (post_x + 9.0, hook_y + 4.0)], 1.6, BRASS)
    f.ink([(post_x + 9.0, hook_y + 4.0), (post_x + 9.0, hook_y + 12.0)], 1.0, K.shade(IVORY_SHADE, 0.8))
    f.limb([(post_x + 9.0, hook_y + 12.0), (post_x + 9.0, hook_y + 42.0)], 3.0, EBONY_LIGHT)
    f.poly([(post_x + 2.0, hook_y + 42.0), (post_x + 16.0, hook_y + 42.0), (post_x + 16.0, hook_y + 54.0), (post_x + 2.0, hook_y + 54.0)], K.WOOD_DARK)
    f.ink([(post_x + 3.0, hook_y + 44.0), (post_x + 15.0, hook_y + 44.0)], 0.8, K.WOOD)
    # A ring of sound that has not quite died away.
    for k, r in enumerate((14.0, 22.0)):
        f.glow_line(_arc(tube_x, 130.0, r, r * 1.8, -40.0, 40.0, 10), 1.2, K.alpha(SOUND, 0.45 - 0.15 * k))
    return f.finish(width=1.6, glow_blur=2.0)


# ---------------------------------------------------------------------------
# The chord bars: the doors of the Concert Hall's stage.
# ---------------------------------------------------------------------------

BAR_FRAME = (96, 384)
#: Each bar: its letter, its step on the staff (0 is the bottom line; C is
#: one ledger line under it), and the colour of its note.
CHORD_NOTES = {
    "do": ("C", -2, K.MAGENTA),
    "mi": ("E", 0, SOUND),
    "sol": ("G", 2, K.YELLOW),
}


def _draw_bar(syllable: str):
    letter, step, colour = CHORD_NOTES[syllable]
    w, h = BAR_FRAME
    f = K.Frame(BAR_FRAME)
    m = 3.0
    left, right = 18.0, w - 18.0
    mouth_y, rack_y = 268.0, 318.0
    # The rack of ebony that holds the foot of the pipe: it fills the foot of
    # the wall.
    f.poly([(m + 2.0, rack_y), (w - m - 2.0, rack_y), (w - m - 2.0, h - m), (m + 2.0, h - m)], EBONY)
    f.poly([(m + 2.0, rack_y), (w - m - 2.0, rack_y), (w - m - 2.0, rack_y + 7.0), (m + 2.0, rack_y + 7.0)], BRASS, body=False)
    for k in range(3):
        y = rack_y + 20.0 + k * 16.0
        f.ink([(m + 8.0, y), (w - m - 8.0, y)], 0.8, EBONY_LIGHT)
    # The foot of the pipe: a cone that narrows into the rack.
    f.poly([(left, mouth_y + 22.0), (right, mouth_y + 22.0), (w / 2.0 + 9.0, rack_y + 2.0), (w / 2.0 - 9.0, rack_y + 2.0)], BRASS)
    f.poly([(w / 2.0 + 8.0, mouth_y + 22.0), (right, mouth_y + 22.0), (w / 2.0 + 9.0, rack_y + 2.0), (w / 2.0 + 3.0, rack_y + 2.0)], BRASS_DARK, body=False)
    # The body of the pipe, from the top of the wall to the mouth.
    f.poly([(left, m + 6.0), (right, m + 6.0), (right, mouth_y + 22.0), (left, mouth_y + 22.0)], BRASS)
    f.poly([(right - 16.0, m + 6.0), (right, m + 6.0), (right, mouth_y + 22.0), (right - 16.0, mouth_y + 22.0)], BRASS_DARK, body=False)
    f.limb([(left + 9.0, m + 16.0), (left + 9.0, mouth_y + 14.0)], 4.0, BRASS_LIGHT, body=False)
    # Its open top: a rim, and the dark inside of the pipe.
    f.poly([(left - 3.0, m), (right + 3.0, m), (right + 3.0, m + 8.0), (left - 3.0, m + 8.0)], BRASS_DARK)
    f.ellipse(w / 2.0, m + 4.0, (right - left) / 2.0 - 2.0, 2.4, EBONY, body=False)
    # The mouth: a flat lip with a dark slot, under a pointed upper lip.
    f.poly([(left + 8.0, mouth_y - 22.0), (w / 2.0, mouth_y - 38.0), (right - 8.0, mouth_y - 22.0), (right - 8.0, mouth_y), (left + 8.0, mouth_y)], K.shade(BRASS, 1.15), body=False)
    f.ink([(left + 8.0, mouth_y - 22.0), (w / 2.0, mouth_y - 38.0), (right - 8.0, mouth_y - 22.0)], 1.2, BRASS_DARK)
    f.poly([(left + 9.0, mouth_y - 2.0), (right - 9.0, mouth_y - 2.0), (right - 11.0, mouth_y + 6.0), (left + 11.0, mouth_y + 6.0)], EBONY, body=False)
    f.glow_poly([(left + 13.0, mouth_y), (right - 13.0, mouth_y), (right - 14.0, mouth_y + 4.0), (left + 14.0, mouth_y + 4.0)], K.alpha(colour, 0.7))
    # Bands of brass round the pipe.
    for y in (34.0, 214.0):
        f.limb([(left, y), (right, y)], 3.0, BRASS_DARK, body=False)
    # The plaque with the note.
    px0, px1, py0, py1 = left + 5.0, right - 5.0, 52.0, 200.0
    f.poly([(px0, py0), (px1, py0), (px1, py1), (px0, py1)], NIGHT, body=False)
    f.poly([(px0, py0), (px1, py0), (px1, py0 + 3.0), (px0, py0 + 3.0)], NIGHT_LIGHT, body=False)
    f.ink([(px0, py0), (px1, py0), (px1, py1), (px0, py1), (px0, py0)], 1.4, BRASS_DARK)
    # The staff: five lines, and the note on its step.
    sx0, sx1, gap, bottom = px0 + 6.0, px1 - 6.0, 5.0, 96.0
    for k in range(5):
        y = bottom - k * gap
        f.ink([(sx0, y), (sx1, y)], 0.8, IVORY)
    nx, ny = (sx0 + sx1) / 2.0 + 2.0, bottom - step * gap / 2.0
    if step <= -2:
        f.ink([(nx - 8.0, bottom + gap), (nx + 8.0, bottom + gap)], 0.9, IVORY)
    head = K.turn(K.ellipse_points(nx, ny, 4.6, 3.4, 16), nx, ny, -20.0)
    f.glow_poly(K.grow(head, 1.5), K.alpha(colour, 0.6))
    f.poly(head, colour, body=False)
    f.ink([(nx + 4.0, ny - 1.0), (nx + 4.0, ny - 24.0)], 1.2, colour)
    # Its letter, large and lit, and its syllable under it.
    lh = 40.0
    _write(f, letter, w / 2.0 - lh * 0.34, 112.0, lh, 3.6, colour, glow=K.alpha(colour, 0.35))
    sh = 18.0
    _write(f, syllable, w / 2.0 - _text_width(syllable, sh) / 2.0, 168.0, sh, 1.8, IVORY)
    return f.finish(width=1.6, glow_blur=2.0)


# ---------------------------------------------------------------------------
# The grand piano.
# ---------------------------------------------------------------------------

PIANO_FRAME = (384, 224)


def _draw_piano():
    w, h = PIANO_FRAME
    f = K.Frame(PIANO_FRAME)
    foot = h - 3.0
    # The plan of the case: x along the piano from the keys, z across from
    # the straight side (far) to the curved side (near).
    length, width = 300.0, 112.0
    plan = [(0.0, 0.0), (length * 0.86, 0.0)]
    plan += [(length * 0.86 + 28.0 * math.sin(math.radians(a)), 22.0 - 22.0 * math.cos(math.radians(a))) for a in range(20, 181, 20)]
    plan += [(length * 0.70, width * 0.42), (length * 0.52, width * 0.62), (length * 0.34, width * 0.86), (length * 0.18, width), (0.0, width)]
    x0, rim = 58.0, 112.0
    depth = 26.0

    def flat(x: float, z: float, up: float = 0.0) -> Point:
        """A point of the plan, seen from the front and a little above."""
        return (x0 + x + z * 0.18, rim - 30.0 + z * 0.30 - up)

    # The lid, up on its stick: it turns about the straight side.
    lift = math.radians(48.0)

    def lid(x: float, z: float) -> Point:
        return (x0 + x + z * math.cos(lift) * 0.18, rim - 34.0 + z * math.cos(lift) * 0.30 - z * math.sin(lift))

    # The legs, the far ones first.
    for lx, lz, colour in ((length * 0.82, 6.0, EBONY), (20.0, width - 8.0, EBONY_LIGHT), (length * 0.52, width * 0.6, EBONY_LIGHT)):
        top_x, top_y = flat(lx, lz)
        top_y += depth - 2.0
        base_y = foot - 6.0 if colour is EBONY else foot - 4.0
        f.poly([(top_x - 6.0, top_y), (top_x + 6.0, top_y), (top_x + 4.0, base_y), (top_x - 4.0, base_y)], colour)
        f.ellipse(top_x, base_y + 1.0, 4.4, 3.0, BRASS)
    # The lid and its stick.
    lid_pts = [lid(x, z) for x, z in plan]
    f.poly(lid_pts, EBONY)
    f.poly([lid(x, z * 0.92) for x, z in plan], EBONY_LIGHT, body=False)
    f.poly([lid(x, z * 0.84) for x, z in plan], EBONY, body=False)
    stick_base = flat(length * 0.42, width * 0.66)
    stick_top = lid(length * 0.42, width * 0.66)
    f.limb([stick_base, stick_top], 2.2, EBONY_LIGHT)
    # The case: its side below the near edge, and its top.
    near = [p for p in plan if p[1] > 1.0]
    side = [flat(x, z) for x, z in near] + [(flat(x, z)[0], flat(x, z)[1] + depth) for x, z in reversed(near)]
    f.poly(side, EBONY)
    f.poly([(flat(x, z)[0], flat(x, z)[1] + depth - 6.0) for x, z in near] + [(flat(x, z)[0], flat(x, z)[1] + depth) for x, z in reversed(near)], K.shade(EBONY, 0.7), body=False)
    f.ink([(flat(x, z)[0], flat(x, z)[1] + 4.0) for x, z in near], 1.4, NIGHT_LIGHT)
    top = [flat(x, z) for x, z in plan]
    f.poly(top, EBONY)
    # Inside the open case: the gold of the iron frame and the strings.
    inner = [flat(x * 0.94 + 8.0, z * 0.84 + 6.0) for x, z in plan]
    f.poly(inner, BRASS, body=False)
    f.poly([flat(x * 0.94 + 8.0, z * 0.84 + 6.0) for x, z in plan if x > length * 0.4] + [flat(length * 0.4, 6.0)], BRASS_DARK, body=False)
    for k in range(10):
        z = 12.0 + k * 8.0
        f.ink([flat(24.0, z), flat(length * (0.86 - k * 0.05), z * 0.6 + 4.0)], 0.6, K.alpha(IVORY_SHADE, 0.8))
    # The keys: a strip of ivory at the front, with the black keys on it.
    kx0, kx1 = -24.0, 6.0
    keybed = [flat(kx0, width * 0.06), flat(kx1, width * 0.06), flat(kx1, width), flat(kx0, width)]
    f.poly([(x, y + 6.0) for x, y in keybed], EBONY)
    f.poly(keybed, IVORY)
    for k in range(1, 18):
        z = width * 0.06 + k * (width * 0.94) / 18.0
        f.ink([flat(kx0, z), flat(kx1, z)], 0.6, IVORY_SHADE)
        if k % 7 not in (0, 3):
            a, b = flat(kx0 + 8.0, z - 1.6), flat(kx1, z + 1.6)
            f.poly([a, (b[0], a[1] + 0.6), b, (a[0], b[1] - 0.6)], EBONY, body=False)
    f.poly([flat(kx0 - 6.0, width * 0.04), flat(kx0, width * 0.04), flat(kx0, width + 2.0), flat(kx0 - 6.0, width + 2.0)], EBONY)
    # The music stand, with a page of music on it.
    sa, sb = flat(14.0, width * 0.30), flat(14.0, width * 0.80)
    stand = [sa, sb, (sb[0] - 6.0, sb[1] - 34.0), (sa[0] - 6.0, sa[1] - 34.0)]
    f.poly(stand, EBONY)
    page = [(sa[0] + 1.0, sa[1] - 6.0), (sb[0] - 1.0, sb[1] - 6.0), (sb[0] - 6.0, sb[1] - 30.0), (sa[0] - 4.0, sa[1] - 30.0)]
    f.poly(page, IVORY, body=False)
    for k in range(4):
        u = 0.25 + k * 0.17
        y0 = page[0][1] + (page[3][1] - page[0][1]) * u
        y1 = page[1][1] + (page[2][1] - page[1][1]) * u
        f.ink([(page[0][0] + (page[3][0] - page[0][0]) * u + 1.0, y0), (page[1][0] + (page[2][0] - page[1][0]) * u - 1.0, y1)], 0.6, K.alpha(EBONY, 0.7))
    # The lyre under the keys, and its three brass pedals.
    lx, ly = flat(4.0, width * 0.6)
    ly += depth
    f.poly([(lx - 7.0, ly), (lx + 7.0, ly), (lx + 5.0, foot - 14.0), (lx - 5.0, foot - 14.0)], EBONY_LIGHT)
    for k in (-1, 0, 1):
        f.limb([(lx + k * 5.0, foot - 14.0), (lx + k * 5.0 + 6.0, foot - 11.0)], 2.0, BRASS)
    # The sheen of the lacquer along the case.
    f.ink([flat(length * 0.3, width * 0.9 + 4.0), flat(length * 0.55, width * 0.58 + 4.0)], 1.4, K.alpha(NIGHT_LIGHT, 0.9))
    # Two little notes rise from the open case.
    for k, (nx, ny) in enumerate(((250.0, 52.0), (282.0, 34.0))):
        f.glow(nx, ny, 3.0, K.alpha(SOUND, 0.8))
        f.glow_line([(nx + 2.4, ny), (nx + 2.4, ny - 11.0), (nx + 7.0, ny - 7.0)], 1.0, K.alpha(SOUND, 0.8))
    return f.finish(width=1.6, glow_blur=2.0)


# ---------------------------------------------------------------------------
# The metronome.
# ---------------------------------------------------------------------------

METRONOME_FRAME = (128, 256)
METRONOME_ROWS: List[Tuple[str, int, int]] = [("idle", 8, 125)]


def _draw_metronome(i: int, n: int):
    w, h = METRONOME_FRAME
    f = K.Frame(METRONOME_FRAME)
    foot = h - 3.0
    cx = w / 2.0
    base_top, apex = foot - 30.0, 22.0
    # The plinth, and the pyramid of the case on it.
    f.poly([(cx - 52.0, foot), (cx + 52.0, foot), (cx + 48.0, base_top), (cx - 48.0, base_top)], EBONY)
    f.poly([(cx - 52.0, foot), (cx + 52.0, foot), (cx + 51.0, foot - 5.0), (cx - 51.0, foot - 5.0)], EBONY_LIGHT, body=False)
    f.ink([(cx - 47.0, base_top + 3.0), (cx + 47.0, base_top + 3.0)], 1.2, BRASS)
    case = [(cx - 40.0, base_top), (cx + 40.0, base_top), (cx + 12.0, apex), (cx - 12.0, apex)]
    f.poly(case, K.WOOD_DARK)
    f.poly([(cx + 14.0, base_top), (cx + 40.0, base_top), (cx + 12.0, apex), (cx + 5.0, apex)], K.shade(K.WOOD_DARK, 0.75), body=False)
    f.poly([(cx - 16.0, apex - 2.0), (cx + 16.0, apex - 2.0), (cx + 12.0, apex - 10.0), (cx - 12.0, apex - 10.0)], BRASS)
    f.ellipse(cx, apex - 12.0, 5.0, 3.6, BRASS)
    # The front: a window of ivory with the marks of the tempo on it.
    win = [(cx - 14.0, base_top - 18.0), (cx + 14.0, base_top - 18.0), (cx + 8.0, apex + 18.0), (cx - 8.0, apex + 18.0)]
    f.poly(K.grow(win, 2.4), BRASS, body=False)
    f.poly(win, IVORY, body=False)
    for k in range(14):
        y = apex + 24.0 + k * 11.0
        half = 3.0 if k % 3 else 6.0
        f.ink([(cx - half, y), (cx + half, y)], 0.7, K.alpha(EBONY, 0.7))
    # The winding key at its side.
    f.limb([(cx + 34.0, base_top - 30.0), (cx + 44.0, base_top - 30.0)], 2.4, BRASS)
    f.poly([(cx + 44.0, base_top - 38.0), (cx + 50.0, base_top - 38.0), (cx + 50.0, base_top - 22.0), (cx + 44.0, base_top - 22.0)], BRASS)
    # The rod on its pivot, and its weight; it swings, tick and tock.
    pivot = (cx, base_top - 10.0)
    swing = 16.0 * math.sin(math.tau * i / float(n))
    rod = K.turn([pivot, (cx, apex + 8.0)], pivot[0], pivot[1], swing)
    f.limb(rod, 2.4, K.STEEL)
    wy = apex + 74.0
    weight = K.turn([(cx - 8.0, wy - 7.0), (cx + 8.0, wy - 7.0), (cx + 6.0, wy + 7.0), (cx - 6.0, wy + 7.0)], pivot[0], pivot[1], swing)
    f.poly(weight, BRASS)
    f.ink(K.turn([(cx - 7.0, wy - 2.0), (cx + 7.0, wy - 2.0)], pivot[0], pivot[1], swing), 0.8, BRASS_DARK)
    f.ellipse(pivot[0], pivot[1], 4.0, 4.0, BRASS)
    # The tick: a ring of sound at each end of its swing.
    edge = abs(math.sin(math.tau * i / float(n)))
    if edge > 0.9:
        tip = rod[1]
        f.glow_line(_arc(tip[0], tip[1], 8.0, 8.0, 0.0, 360.0, 20), 1.2, K.alpha(SOUND, 0.8))
    return f.finish(width=1.6, glow_blur=2.0)


# ---------------------------------------------------------------------------
# Publication.
# ---------------------------------------------------------------------------

SCENERY = ["prop", "scenery", "art", "music"]

TARGETS: Dict[str, dict] = {}
TARGETS["art_chime"] = _publisher("art_chime", "Chime", STILL, CHIME_FRAME, lambda anim, i, n: _draw_chime(), {"foot": (48.0, 256.0)}, "Scenery", SCENERY)
for _syllable in CHORD_NOTES:
    TARGETS[f"art_chord_bar_{_syllable}"] = _publisher(
        f"art_chord_bar_{_syllable}", f"Chord Bar {_syllable.title()}", STILL, BAR_FRAME,
        (lambda s: lambda anim, i, n: _draw_bar(s))(_syllable), {"foot": (48.0, 384.0)}, "Door", ["prop", "door", "lock", "art", "music"], forward=(0.0, -1.0))
TARGETS["art_grand_piano"] = _publisher("art_grand_piano", "Grand Piano", STILL, PIANO_FRAME, lambda anim, i, n: _draw_piano(), {"foot": (192.0, 224.0)}, "Scenery", SCENERY)
TARGETS["art_metronome"] = _publisher("art_metronome", "Metronome", METRONOME_ROWS, METRONOME_FRAME, lambda anim, i, n: _draw_metronome(i, n), {"foot": (64.0, 256.0)}, "Scenery", SCENERY)
