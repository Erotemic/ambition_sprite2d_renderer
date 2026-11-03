"""T-71: the robot of the Picture Palace that is the old model.

A heavy endoskeleton of chrome and gunmetal, bulky and square: the model
before the famous one. A square chrome skull with a heavy brow, two red
eyes in a dark band, and a jaw of teeth. A chest of slats, a spine of
blocks, pistons in its arms and legs. It stands rigid, its knees a little
bent, and it carries a leather jacket over one forearm, because it has not
worked out how to put one on.

A parody of the film robot from the future (an original drawing, no
likeness). It talks; it does not fight.

Rows: ``idle`` (the eyes glow, the head scans), ``walk`` (a heavy, even
stride), ``talk`` (the jaw opens, the eyes flare), ``hit`` and ``death``
(the knees give, it slumps, the eyes go out).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K
from . import _picture_palace_kit as M

TARGET_NAME = "art_t71"
FRAME_SIZE = (160, 224)
GROUND = 219.0
ROWS: List[Tuple[str, int, int]] = M.ROWS
LOOPS = M.LOOPS

ACTOR_METADATA = M.machine_metadata(
    "npc_art_t71", "T-71", "Biped", "Standard", ["robot", "endoskeleton", "jacket"],
    "A heavy chrome-and-gunmetal endoskeleton robot of the Picture Palace in the Art dimension: square, bulky, with red eyes and "
    "a rigid stance. It carries a leather jacket over one arm because it has not worked out how to put it on. A parody of the "
    "old-model robot from the future of the action films; an original drawing.",
)

CHROME = (206, 214, 228, 255)
CHROME_SHADE = (132, 140, 160, 255)
CHROME_LIGHT = (246, 250, 255, 255)
GUNMETAL = (78, 82, 98, 255)
GUNMETAL_DARK = (50, 52, 64, 255)
SOCKET = (26, 22, 30, 255)
LEATHER = (52, 38, 34, 255)
LEATHER_SHADE = (34, 24, 22, 255)
LEATHER_LIGHT = (98, 72, 60, 255)

THIGH, SHIN = 33.5, 34.0


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    cx = 76.0
    bob, lean, scan, jaw, eye, stride, sink, swing, spark = 0.0, 0.0, 0.0, 0.0, 0.8, 0.0, 0.0, 0.0, 0.0
    if anim == "idle":
        eye = 0.65 + 0.35 * math.sin(cyc)
        scan = 1.5 * math.sin(cyc)
    elif anim == "walk":
        stride = math.sin(cyc)
        bob = -2.0 * abs(math.cos(cyc))
        swing = -12.0 * stride
        lean = 2.0
    elif anim == "talk":
        jaw = 0.5 + 0.5 * math.sin(cyc * 2.0)
        eye = 0.8 + 0.2 * jaw
        bob = 0.5 * math.sin(cyc)
    elif anim == "hit":
        lean, eye, spark = -9.0 + 3.0 * t, (0.2 if i == 1 else 1.0), 1.0 - t
    elif anim == "death":
        sink = 34.0 * min(1.0, t * 1.3)
        lean = 22.0 * t
        eye = max(0.0, 1.0 - t * 1.25)
        swing = 14.0 * t

    hip = (cx, 136.0 + bob + sink)

    def U(dx: float, dy: float):
        return K.turn([(hip[0] + dx, hip[1] + dy)], hip[0], hip[1], lean)[0]

    def Us(points):
        return [U(x, y) for x, y in points]

    # -- legs: the far one first, darker ------------------------------------
    for side, colour, dx, phase in ((1.0, GUNMETAL_DARK, 9.0, -1.0), (-1.0, GUNMETAL, -6.0, 1.0)):
        h = (hip[0] + dx, hip[1] + 5.0)
        step = stride * phase
        ax = cx + dx * 1.2 + 13.0 * step + (14.0 * t if anim == "death" else 0.0) * (1 if side < 0 else 0.4)
        lift = 6.0 * max(0.0, math.cos(cyc)) * (1 if step > 0 else 0) if anim == "walk" else 0.0
        ankle = (ax, GROUND - 13.0 - lift)
        kn = M.knee(h, ankle, THIGH, SHIN, 1.0)
        M.rod(f, [h, kn], 12.0, colour)
        M.rod(f, [h, kn], 3.2, CHROME_SHADE if side > 0 else CHROME, edge=0.0, body=False)
        M.rod(f, [kn, ankle], 11.0, colour)
        M.rod(f, [(kn[0] - 1.0, kn[1] + 4.0), (ankle[0] - 1.0, ankle[1] - 3.0)], 3.0, CHROME_SHADE if side > 0 else CHROME, edge=0.0, body=False)
        M.disc(f, kn[0], kn[1], 6.0, 6.0, CHROME_SHADE if side > 0 else CHROME)
        fy = ankle[1]
        M.plate(f, [(ax - 9.0, fy + 1.0), (ax + 8.0, fy - 1.0), (ax + 17.0, fy + 9.0), (ax + 17.0, fy + 13.0), (ax - 9.0, fy + 13.0)],
                colour if side > 0 else GUNMETAL)
        f.ink([(ax - 7.0, fy + 9.5), (ax + 15.0, fy + 9.5)], 0.9, CHROME_SHADE)
        M.disc(f, ax, fy + 1.0, 4.0, 4.0, CHROME_SHADE)

    # -- the far arm, behind the body ---------------------------------------
    sh = U(23.0, -58.0)
    el = K.turn([U(26.0, -32.0)], sh[0], sh[1], swing)[0]
    wr = K.turn([U(28.0, -8.0)], sh[0], sh[1], swing + (-18.0 if anim == "talk" else 0.0) * (0.5 + 0.5 * math.sin(cyc)))[0]
    M.rod(f, [sh, el], 9.0, GUNMETAL_DARK)
    M.rod(f, [el, wr], 8.0, GUNMETAL_DARK)
    M.rod(f, [el, wr], 2.4, CHROME_SHADE, edge=0.0, body=False)
    M.disc(f, el[0], el[1], 4.6, 4.6, CHROME_SHADE)
    M.plate(f, [(wr[0] - 5.0, wr[1] - 1.0), (wr[0] + 5.0, wr[1] - 1.0), (wr[0] + 6.0, wr[1] + 10.0), (wr[0] - 4.0, wr[1] + 11.0)], CHROME_SHADE)

    # -- pelvis and spine -----------------------------------------------------
    M.plate(f, Us([(-20.0, -6.0), (19.0, -6.0), (16.0, 9.0), (-17.0, 9.0)]), GUNMETAL)
    f.ink(Us([(-14.0, 2.0), (12.0, 2.0)]), 1.0, GUNMETAL_DARK)
    for side in (-1.0, 1.0):
        M.rod(f, Us([(side * 13.0, -6.0), (side * 15.0, -31.0)]), 4.0, CHROME_SHADE)
    for k in range(3):
        y = -10.0 - k * 8.0
        M.plate(f, Us([(-7.0, y - 3.0), (7.0, y - 3.0), (6.0, y + 3.0), (-6.0, y + 3.0)]), CHROME)

    # -- the chest -------------------------------------------------------------
    M.plate(f, Us([(-31.0, -64.0), (29.0, -64.0), (25.0, -32.0), (-25.0, -32.0)]), GUNMETAL)
    M.plate(f, Us([(-25.0, -60.0), (23.0, -60.0), (20.0, -42.0), (-21.0, -42.0)]), CHROME, edge=0.8, body=False)
    f.poly(Us([(-25.0, -60.0), (-6.0, -60.0), (-8.0, -42.0), (-21.0, -42.0)]), CHROME_SHADE, body=False)
    for k in range(3):
        y = -56.0 + k * 5.0
        f.ink(Us([(-20.0, y), (18.0, y)]), 0.9, K.alpha(GUNMETAL_DARK, 0.9))
    for x in (-18.0, 16.0):
        f.dot(*U(x, -37.0), 1.4, CHROME_SHADE)
    f.ink(Us([(-22.0, -36.0), (20.0, -36.0)]), 0.9, GUNMETAL_DARK)

    # -- neck and head ---------------------------------------------------------
    for x in (-4.0, 5.0):
        M.rod(f, Us([(x, -63.0), (x + 0.5, -72.0)]), 3.4, CHROME_SHADE)
    hx, hy = 3.0, -88.0
    nod = -1.5 * jaw

    def H(dx: float, dy: float):
        return U(hx + dx, hy + dy + nod)

    def Hs(points):
        return [H(x, y) for x, y in points]

    skull = [(-14.0, -12.0), (-9.0, -17.0), (12.0, -17.0), (17.0, -11.0), (17.0, 4.0), (13.0, 11.0), (-6.0, 11.0), (-14.0, 4.0)]
    M.plate(f, Hs(skull), CHROME)
    f.poly(Hs([(-14.0, -12.0), (-9.0, -17.0), (-3.0, -17.0), (-6.0, 11.0), (-14.0, 4.0)]), CHROME_SHADE, body=False)
    f.ink(Hs([(-7.0, -15.0), (10.0, -15.0)]), 1.0, CHROME_LIGHT)
    # The ear: a piston cap at the side of the skull.
    M.disc(f, *H(-8.0, -1.0), 4.4, 4.4, GUNMETAL, body=False)
    f.dot(*H(-8.0, -1.0), 1.4, CHROME)
    # The band of the eyes under the heavy brow.
    f.poly(Hs([(-2.0, -8.0), (18.0, -8.5), (18.0, -2.0), (-1.0, -1.5)]), SOCKET, body=False)
    f.ink(Hs([(-3.0, -9.0), (18.0, -9.5)]), 1.6, CHROME_LIGHT)
    for ex in (5.5, 14.0):
        exx, eyy = H(ex + scan, -5.0)
        f.dot(exx, eyy, 1.9, K.alpha(M.REC_RED, 0.35 + 0.65 * eye))
        f.dot(exx + 0.4, eyy - 0.3, 0.8, K.alpha(M.REC_RED_HOT, eye))
        f.glow(exx, eyy, 2.4 + 1.6 * eye, K.alpha(M.REC_RED, 0.45 * eye))
    # The cheek, the nose hole and the jaw of teeth.
    f.ink(Hs([(4.0, 1.0), (9.0, 4.0), (17.0, 3.0)]), 0.9, CHROME_SHADE)
    f.poly(Hs([(13.0, 0.0), (16.0, 0.0), (15.0, 3.0)]), SOCKET, body=False)
    drop = 3.0 * jaw
    if drop > 0.3:
        f.poly(Hs([(1.0, 6.0), (16.0, 5.5), (15.0, 6.0 + drop), (1.0, 6.5 + drop)]), SOCKET, body=False)
    jaw_pts = [(-5.0, 6.0 + drop), (16.0, 5.5 + drop), (14.0, 12.0 + drop), (-3.0, 12.5 + drop)]
    M.plate(f, Hs(jaw_pts), CHROME, edge=0.8)
    for k in range(6):
        x = 0.0 + k * 2.6
        f.ink(Hs([(x, 6.0 + drop), (x, 9.5 + drop)]), 0.6, CHROME_SHADE)
    f.ink(Hs([(-1.0, 6.0), (16.0, 5.5)]), 0.8, SOCKET)

    # -- the shoulders ------------------------------------------------------
    M.disc(f, *U(26.0, -58.0), 8.0, 7.0, CHROME_SHADE)
    sh_n = U(-28.0, -58.0)
    M.disc(f, sh_n[0], sh_n[1], 9.0, 8.0, CHROME)
    f.ink([(sh_n[0] - 4.0, sh_n[1] - 5.0), (sh_n[0] + 3.0, sh_n[1] - 6.0)], 1.0, CHROME_LIGHT)

    # -- the near arm: the forearm held level, the jacket over it ---------------
    # The near arm holds the jacket up by its collar, out in front, as a
    # thing to study: it does not know how this goes on.
    el_n = U(-8.0, -36.0)
    hand = U(28.0, -46.0)
    M.rod(f, [sh_n, el_n], 10.0, GUNMETAL)
    M.rod(f, [sh_n, el_n], 2.8, CHROME, edge=0.0, body=False)
    M.rod(f, [el_n, hand], 8.0, GUNMETAL)
    M.rod(f, [el_n, hand], 2.4, CHROME, edge=0.0, body=False)
    M.disc(f, el_n[0], el_n[1], 5.5, 5.5, CHROME)
    hx, hy = hand
    tilt = 6.0 * stride - lean * 0.6 + (8.0 * t if anim == "death" else 0.0)

    def J(points):
        return K.turn([(hx + x * 1.12, hy + y * 1.08) for x, y in points], hx, hy, tilt)

    for side in (-1.0, 1.0):
        sleeve = [(side * 11.0, 6.0), (side * 17.0, 9.0), (side * 19.0, 40.0), (side * 13.0, 41.0), (side * 11.0, 14.0)]
        M.plate(f, J(sleeve), LEATHER_SHADE if side > 0 else LEATHER)
        f.poly(J([(side * 19.0, 36.0), (side * 13.4, 37.0), (side * 13.0, 41.0), (side * 19.0, 40.0)]), LEATHER_LIGHT, body=False)
    body = [(-12.0, 4.0), (12.0, 4.0), (14.0, 46.0), (-14.0, 46.0)]
    M.plate(f, J(body), LEATHER)
    # The lining, seen where the jacket hangs open, and the two lapels.
    f.poly(J([(-4.0, 6.0), (4.0, 6.0), (3.0, 46.0), (-3.0, 46.0)]), (122, 34, 36, 255), body=False)
    for side in (-1.0, 1.0):
        f.poly(J([(side * 3.0, 4.0), (side * 11.0, 5.0), (side * 7.0, 20.0), (side * 3.4, 18.0)]), LEATHER_LIGHT, body=False)
        f.ink(J([(side * 3.6, 18.0), (side * 3.0, 46.0)]), 1.0, (176, 178, 190, 255))
        f.ink(J([(side * 7.0, 30.0), (side * 11.0, 29.5)]), 0.9, LEATHER_SHADE)
        f.ink(J([(side * 12.6, 10.0), (side * 13.4, 44.0)]), 0.9, LEATHER_LIGHT)
    f.poly(J([(-14.0, 42.0), (14.0, 42.0), (14.0, 46.0), (-14.0, 46.0)]), LEATHER_SHADE, body=False)
    f.poly(J([(-6.0, 1.0), (6.0, 1.0), (7.0, 6.0), (-7.0, 6.0)]), LEATHER_LIGHT, body=False)
    # The chrome fist that pinches the collar.
    M.plate(f, [(hx - 4.0, hy - 6.0), (hx + 5.0, hy - 6.0), (hx + 6.0, hy + 3.0), (hx - 4.0, hy + 3.0)], CHROME)
    for k in range(3):
        f.ink([(hx - 2.0 + k * 2.6, hy - 5.0), (hx - 1.6 + k * 2.6, hy + 2.0)], 0.6, CHROME_SHADE)

    if spark > 0.0:
        sx, sy = U(10.0, -46.0)
        for a in range(5):
            ang = a * 1.25 + i
            r0, r1 = 3.0, 6.0 + 7.0 * spark
            f.glow_line([(sx + math.cos(ang) * r0, sy + math.sin(ang) * r0), (sx + math.cos(ang) * r1, sy + math.sin(ang) * r1)], 1.2,
                        K.alpha(M.TUNGSTEN, spark))
    return f.finish(width=1.6)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
