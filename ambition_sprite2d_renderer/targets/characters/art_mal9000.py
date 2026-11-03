"""MAL-9000: the ship's computer of the Picture Palace's space set.

A tall dark panel in the wall (about 48 by 128 world units; the frame is
twice that). In its upper half, a round red eye in a silver ring: a dark
lens with a red light deep in it that glows and dims. Under the eye, a
little silver name plate, MAL 9000. Lower down, the slits of its speaker,
and a row of small status lights. It does not walk: its rows are the eye.

A parody of the calm ship's computer of the space odyssey film (an original
drawing, no likeness). It talks, politely; it does not open the door.

Rows: ``idle`` (the eye glows and dims, slowly), ``talk`` (the eye pulses
as it speaks, and its speaker lights), ``hit`` (the eye flickers) and
``death`` (its memory is pulled: the eye pulses slower and slower, and
goes out, as it sings).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K
from . import _picture_palace_kit as M

TARGET_NAME = "art_mal9000"
FRAME_SIZE = (96, 256)
ROWS: List[Tuple[str, int, int]] = [("idle", 8, 160), ("talk", 6, 100), ("hit", 3, 90), ("death", 8, 220)]
LOOPS = {"idle", "talk"}

ACTOR_METADATA = M.machine_metadata(
    "npc_art_mal9000", "MAL-9000", "PropActor", "PropLike", ["computer", "wall_panel", "speaker", "red_eye"],
    "The ship's computer of the Picture Palace's space set, in the Art dimension: a tall dark wall panel with one round red eye "
    "in a silver ring and a little name plate, MAL 9000. Calm and polite; it is sorry, but it cannot open the pod bay door. "
    "A parody of the ship's computer of the space odyssey film; an original drawing.",
    walks=False,
)

PANEL = M.FILM_BLACK
BEZEL = (96, 100, 114, 255)
BEZEL_LIGHT = (150, 154, 170, 255)
RING = (214, 218, 230, 255)
RING_SHADE = (140, 146, 164, 255)
LENS = (14, 12, 20, 255)
DEEP_RED = (120, 10, 14, 255)

#: Strokes of the letters of the name plate on a grid 2 wide and 4 tall.
GLYPHS = {
    "M": [[(0, 4), (0, 0), (1, 2), (2, 0), (2, 4)]],
    "A": [[(0, 4), (0, 1), (1, 0), (2, 1), (2, 4)], [(0, 2.4), (2, 2.4)]],
    "L": [[(0, 0), (0, 4), (2, 4)]],
    "9": [[(2, 2), (0, 2), (0, 0), (2, 0), (2, 4), (0, 4)]],
    "0": [[(0, 0), (2, 0), (2, 4), (0, 4), (0, 0)]],
    "-": [[(0.2, 2), (1.8, 2)]],
    " ": [],
}


def _text(f: K.Frame, text: str, x: float, y: float, h: float, colour, width: float = 0.7) -> None:
    s = h / 4.0
    for ch in text:
        for stroke in GLYPHS[ch]:
            f.ink([(x + px * s, y + py * s) for px, py in stroke], width, colour)
        x += 3.0 * s


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    w, h = FRAME_SIZE
    glow, speak, flicker = 0.75 + 0.25 * math.sin(cyc), 0.0, 0.0
    if anim == "talk":
        glow = 0.75 + 0.25 * math.sin(cyc * 2.0)
        speak = 0.5 + 0.5 * math.sin(cyc * 2.0)
    elif anim == "hit":
        glow = (1.0, 0.25, 0.8)[i]
        flicker = 1.0 - t
    elif anim == "death":
        # The song slows: each pulse is longer than the last, and fainter.
        fade = 1.0 - t
        glow = fade * (0.6 + 0.4 * math.cos(math.tau * 3.0 * math.sqrt(t)))

    x0, y0, x1, y1 = 7.0, 7.0, w - 7.0, h - 7.0
    # The bezel and the black panel in it.
    M.plate(f, [(x0 + 4.0, y0), (x1 - 4.0, y0), (x1, y0 + 4.0), (x1, y1 - 4.0), (x1 - 4.0, y1), (x0 + 4.0, y1), (x0, y1 - 4.0), (x0, y0 + 4.0)], BEZEL)
    f.poly([(x1 - 6.0, y0 + 2.0), (x1 - 1.0, y0 + 4.0), (x1 - 1.0, y1 - 4.0), (x1 - 6.0, y1 - 2.0)], K.shade(BEZEL, 0.75), body=False)
    f.ink([(x0 + 2.0, y0 + 5.0), (x0 + 2.0, y1 - 5.0)], 1.0, BEZEL_LIGHT)
    px0, py0, px1, py1 = x0 + 7.0, y0 + 8.0, x1 - 7.0, y1 - 8.0
    M.plate(f, [(px0, py0), (px1, py0), (px1, py1), (px0, py1)], PANEL, edge=0.8, body=False)
    f.ink([(px0 + 2.0, py0 + 2.0), (px1 - 2.0, py0 + 2.0)], 0.8, K.alpha(BEZEL_LIGHT, 0.5))
    # Two screws at the top and two at the foot of the bezel.
    for sx, sy in ((x0 + 4.0, y0 + 4.0), (x1 - 4.0, y0 + 4.0), (x0 + 4.0, y1 - 4.0), (x1 - 4.0, y1 - 4.0)):
        f.dot(sx, sy, 1.4, K.shade(BEZEL, 0.6))

    # The eye: a silver ring, a dark lens, a red light deep in it.
    ex, ey = w / 2.0, 82.0
    if flicker:
        ex += (1.5 if i == 1 else -1.0)
    M.disc(f, ex, ey, 26.0, 26.0, RING_SHADE, body=False)
    f.ellipse(ex - 1.0, ey - 1.0, 24.0, 24.0, RING, body=False)
    f.ellipse(ex + 1.0, ey + 1.0, 19.5, 19.5, RING_SHADE, body=False)
    f.ellipse(ex, ey, 18.0, 18.0, LENS, body=False)
    f.ellipse(ex, ey, 13.0, 13.0, K.alpha(DEEP_RED, 0.5 + 0.5 * glow), body=False)
    f.ellipse(ex, ey, 8.5, 8.5, K.alpha(M.REC_RED, 0.25 + 0.75 * glow), body=False)
    f.ellipse(ex, ey, 3.6, 3.6, K.alpha(M.TUNGSTEN, glow), body=False)
    f.dot(ex, ey, 1.4, K.alpha(K.WHITE, glow))
    f.glow(ex, ey, 6.0 + 9.0 * glow, K.alpha(M.REC_RED, 0.55 * glow))
    if anim == "talk":
        f.glow(ex, ey, 12.0 + 8.0 * speak, K.alpha(M.REC_RED, 0.25 * speak))
    # The glass of the lens catches the light of the room: one curved glint.
    f.ink([(ex - 12.0, ey - 5.0), (ex - 10.0, ey - 10.0), (ex - 5.0, ey - 13.0)], 1.5, K.alpha(K.WHITE, 0.7))
    f.dot(ex + 9.0, ey + 9.0, 1.0, K.alpha(K.WHITE, 0.35))

    # The name plate under the eye.
    nx0, nx1, ny0, ny1 = ex - 26.0, ex + 26.0, 122.0, 136.0
    M.plate(f, [(nx0, ny0), (nx1, ny0), (nx1, ny1), (nx0, ny1)], RING, edge=0.8, body=False)
    f.poly([(nx0, ny1 - 3.0), (nx1, ny1 - 3.0), (nx1, ny1), (nx0, ny1)], RING_SHADE, body=False)
    _text(f, "MAL 9000", nx0 + 4.0, ny0 + 3.5, 6.0, PANEL, 0.75)

    # The speaker: rows of slits that light a little when it talks.
    for k in range(9):
        y = 156.0 + k * 6.0
        f.limb([(ex - 20.0, y), (ex + 20.0, y)], 2.6, (8, 8, 12, 255), body=False)
        if speak:
            lit = max(0.0, speak - abs(k - 4) * 0.18)
            f.ink([(ex - 18.0, y), (ex + 18.0, y)], 1.0, K.alpha(M.REC_RED, 0.6 * lit))
    # The row of status lights at the foot: tungsten, and one red when it records.
    for k in range(5):
        lx = ex - 16.0 + k * 8.0
        on = (k + i) % 3 != 0 if anim != "death" else (t < 0.3 and k == 0)
        colour = M.REC_RED if k == 4 else M.TUNGSTEN
        f.ellipse(lx, 222.0, 2.2, 2.2, K.alpha(colour, 0.9 if on else 0.25), body=False)
        if on:
            f.glow(lx, 222.0, 3.4, K.alpha(colour, 0.35))
    return f.finish(width=1.6, glow_blur=2.2)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
