#!/usr/bin/env python3
"""Redesign candidates, round 1: the Vault Keeper, the Merchant Prototype and the General Hero.

    uv run python scripts/svg_art/vault_merchant_hero_art.py --all DIR          # every look, side + front SVGs
    uv run python scripts/svg_art/vault_merchant_hero_art.py --sheets DIR       # SVGs + one contact sheet per character
    uv run python scripts/svg_art/vault_merchant_hero_art.py --look keeper_a DIR

CANDIDATES, NOT CAST: nothing registers these drawings. The three hall NPCs
(``npc_vault_keeper``, ``npc_merchant_prototype``, ``npc_general_hero``) still
draw their old toon sheets; once Jon picks a look it is redrawn as the
character's SVG with a rig builder, as Oiler was.

WHO THEY ARE (character_catalog.ron + sandbox/hall.yarn + sandbox/kernel.yarn):

* VAULT KEEPER (178 cm): keeps the hall's vault room ("People pay me to keep
  things here"), prices everything ("I know what everything here costs. I
  haven't priced you"), keeps the ledger of where every upgrade's funding came
  from ("Close the ledger"), wears a silver buckle the pirate raider covets,
  and holds a combination the Mockingbird cannot copy. Barks: "Hands off the
  vault staff", "That debt has interest", "A secret spoken is a secret spent".
* MERCHANT PROTOTYPE (168 cm, round): the draft shop ("Shop's open. Anything
  you can't afford is greyed out"): axes, health cells, bombs, the gun-sword,
  the puppy-slug gun; refunds until a purchase changes the story. "I am still
  setting prices"; "Terms still pending. The price never is"; "No refunds for
  violence".
* GENERAL HERO (185 cm, the tallest of the three): a decorated veteran, NOT the
  General (``absurd_general``, the cartoon brass in olive with the bulb nose).
  "We won. I lost people. I don't like being asked which part the medals are
  for"; "I am resting. If the alarm goes, I stop resting"; "CHARGE!". His old
  toon preset was the generic sword hero (a blade and a scarf), so every look
  keeps a sword and a scarf, and adds the medals and the tiredness.

House style (oiler_art.py, colonial_statesman_art.py): thick warm ink, flat
cel fills with one shade band down-back and a thin light band up-front, adult
proportions, small eyes, NO drop shadows. Side view faces right (the primary
view); the front view is the second. Each look is a dict in ``LOOKS``; its
costume is drawn by the ``dress_<look>`` functions over the shared body.
"""
from __future__ import annotations

import colorsys
import io
import math
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import svgkit as svg  # noqa: E402
from svgkit import capsule, ellipse, line, path, smooth  # noqa: E402

W = H = 560
GROUND = 502.0
INK = "#1d1714"
OUT = 3.4      # silhouette ink
FINE = 1.6     # inner ink
CX = 280.0

# ============================================================================================
# colour and cel shading
# ============================================================================================


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _hex(r, g, b):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(v * 255))) for v in (r, g, b))


def shade(c, k=0.74):
    """The colour in shadow: darker, a touch more saturated, cooled toward violet."""
    hh, ll, ss = colorsys.rgb_to_hls(*_rgb(c))
    if hh < 0.17:  # warm (skin, leather, gold): toward red, no hotter
        hh, ss = (hh - 0.012) % 1.0, ss * 0.92
    elif hh > 0.45:  # cool: toward violet
        hh, ss = (hh + 0.012) % 1.0, min(1.0, ss * 1.05)
    return _hex(*colorsys.hls_to_rgb(hh, ll * k, ss))


def light(c, k=0.16):
    r, g, b = _rgb(c)
    return _hex(r + (1 - r) * k, g + (1 - g) * k, b + (1 - b) * k)


_NUM = re.compile(r"(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)")


def shifted(d, dx, dy):
    return _NUM.sub(lambda m: f"{float(m.group(1)) + dx:.2f},{float(m.group(2)) + dy:.2f}", d)


_N = [0]


def cel(d, base, items=(), s=5.0, l=2.4, sh=None, lt=None, sw=None, ink=True, sdir=(-1.0, 0.65)):
    """A shape in flat cel: its fill, a shade band hugging the down-back edges
    (``s`` wide), a thin light band on the up-front edges, the clipped
    ``items``, then the ink outline. No drop shadows: the shade is IN the shape."""
    _N[0] += 1
    cid = f"vmh{_N[0]}"
    sh = sh or shade(base)
    lt = lt if lt is not None else light(base)
    sx, sy = -sdir[0] * s, -sdir[1] * s
    inner = [path(d, base), path(d + " " + shifted(d, sx, sy), sh, extra=' fill-rule="evenodd"')]
    if lt and l:
        inner.append(path(d + " " + shifted(d, sdir[0] * l, sdir[1] * l), lt, extra=' fill-rule="evenodd"'))
    inner += list(items)
    out = [f'<clipPath id="{cid}"><path d="{d}" /></clipPath>', f'<g clip-path="url(#{cid})">'] + inner + ["</g>"]
    if ink:
        out.append(path(d, "none", INK, sw or OUT))
    return out


def flat(d, fill, sw=None):
    return [path(d, fill, INK, sw or OUT)]


def frame(o, a):
    ux, uy = math.cos(a), math.sin(a)
    return lambda t, s, *c: (o[0] + ux * t - uy * s, o[1] + uy * t + ux * s) + c


def ang(a, b):
    return math.atan2(b[1] - a[1], b[0] - a[0])


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def mx(pts, cx=CX):
    return [(2 * cx - p[0], p[1]) + tuple(p[2:]) for p in pts]


def rect(x0, y0, x1, y1, r=0.0):
    if r <= 0:
        return smooth([(x0, y0, True), (x1, y0, True), (x1, y1, True), (x0, y1, True)])
    return smooth([(x0 + r, y0, True), (x1 - r, y0, True), (x1, y0 + r, True), (x1, y1 - r, True), (x1 - r, y1, True), (x0 + r, y1, True),
                   (x0, y1 - r, True), (x0, y0 + r, True)])


# ============================================================================================
# the figure: landmarks from a height and a build
# ============================================================================================

class Geo:
    """Where a figure's joints and planes sit, from its look's height ``H`` (SVG
    units, sole to crown), head ratio ``hr`` and build. Side view: facing +x,
    the body's axis at ``x = CX``."""

    def __init__(self, L):
        self.L = L
        H = self.H = L["H"]
        b = L.get("build", {})
        self.crown = GROUND - H
        self.hh = H * L["hr"]
        self.chin = self.crown + self.hh
        self.sh_y = self.chin + H * b.get("neck", 0.058)
        self.chest_y = self.sh_y + H * 0.075
        self.waist_y = GROUND - H * 0.595
        self.hip_y = GROUND - H * 0.50
        self.crotch_y = GROUND - H * 0.462
        self.knee_y = GROUND - H * 0.272
        self.ankle_y = GROUND - H * 0.052
        # side depths
        self.dback = H * b.get("back", 0.072)
        self.dchest = H * b.get("chest", 0.072)
        self.belly = H * b.get("belly", 0.0)
        self.bust = H * b.get("bust", 0.0)
        self.seat = H * b.get("seat", 0.0)
        # front half-widths
        self.sw = H * b.get("shoulder", 0.122)
        self.ww = H * b.get("waist", 0.082)
        self.hw = H * b.get("hip", 0.094)
        self.limb = b.get("limb", 1.0)
        # the head: face plane x in the side view (head centred a touch ahead of the neck)
        self.xf = CX + H * 0.016 + self.hh * 0.47
        # side arms and legs (near = the viewer's side)
        Hh = H
        self.s_arm = {
            "near": ((CX + Hh * 0.004, self.sh_y + Hh * 0.026), (CX - Hh * 0.008, self.waist_y + Hh * 0.004), (CX + Hh * 0.018, self.crotch_y - Hh * 0.004)),
            "far": ((CX - Hh * 0.016, self.sh_y + Hh * 0.024), (CX - Hh * 0.034, self.waist_y), (CX - Hh * 0.014, self.crotch_y - Hh * 0.01)),
        }
        self.s_leg = {
            "near": ((CX + Hh * 0.012, self.hip_y), (CX + Hh * 0.02, self.knee_y), (CX + Hh * 0.014, self.ankle_y)),
            "far": ((CX - Hh * 0.022, self.hip_y), (CX - Hh * 0.04, self.knee_y), (CX - Hh * 0.058, self.ankle_y)),
        }
        sx = self.sw - H * 0.022
        self.f_arm = {
            "right": ((CX - sx, self.sh_y + H * 0.03), (CX - self.sw - H * 0.004, self.waist_y + H * 0.004), (CX - self.sw - H * 0.008, self.crotch_y - H * 0.006)),
        }
        self.f_arm["left"] = tuple((2 * CX - x, y) for x, y in self.f_arm["right"])
        lx = H * b.get("stance", 0.05)
        self.f_leg = {"right": ((CX - H * 0.048, self.hip_y), (CX - lx, self.knee_y), (CX - lx, self.ankle_y))}
        self.f_leg["left"] = tuple((2 * CX - x, y) for x, y in self.f_leg["right"])

    # head-local points: u from the face plane (+ forward), v from the crown, in head heights
    def Q(self, u, v, *rest):
        return (self.xf + u * self.hh, self.crown + v * self.hh) + tuple(rest)

    def F(self, u, v, *rest):
        """Front head-local: u across from the centre (+ screen right), v down from the crown."""
        return (CX + u * self.hh, self.crown + v * self.hh) + tuple(rest)


# ============================================================================================
# heads
# ============================================================================================

#: The cranium in head-local units (side view): centre and radii.
CRAN = (-0.46, 0.47, 0.47, 0.47)


def cran(g, th, t=0.0):
    uc, vc, rx, ry = CRAN
    a = math.radians(th)
    return g.Q(uc + (rx + t) * math.cos(a), vc + (ry + t) * math.sin(a))


def face_profile(g, f):
    """The profile from the brow to under the chin, facing +x."""
    n, hook, droop = f.get("nose", 0.13), f.get("hook", 0.0), f.get("droop", 0.0)
    br, lip, chin = f.get("brow", 0.02), f.get("lip", 0.02), f.get("chin", 0.02)
    jaw = f.get("jaw_drop", 0.0)
    pts = [
        (0.0 + br * 0.4, 0.27), (0.012 + br, 0.365), (-0.008, 0.43),
        (n * 0.45 + hook, 0.51), (n, 0.595 + droop, True), (n - 0.035, 0.645 + droop * 0.6), (0.024, 0.655),
        (0.034 + lip, 0.715), (0.016 + lip * 0.4, 0.752), (0.028 + lip * 0.8, 0.79), (0.002, 0.836),
        (0.024 + chin, 0.905 + jaw * 0.5), (-0.03, 0.985 + jaw), (-0.16, 1.0 + jaw * 0.8),
    ]
    return [g.Q(*p) for p in pts]


def head_side_outline(g, f):
    back = [cran(g, th) for th in (128, 150, 175, 200, 228, 255, 280)]
    fore = [cran(g, th) for th in (305, 325)]
    under = [g.Q(-0.36, 0.94 + f.get("jaw_drop", 0.0) * 0.5), g.Q(-0.6, 0.87)]
    return back + fore + face_profile(g, f) + under


def eye_side(g, f, u=-0.105, v=0.47):
    ex, ey = g.Q(u, v)
    k = g.hh / 70.0 * f.get("eye", 1.0)
    iris = f.get("iris", "#3c3328")
    out = [path(smooth([(ex - 4.2 * k, ey - 0.4 * k), (ex - 0.5 * k, ey - 2.2 * k), (ex + 3.0 * k, ey - 1.2 * k), (ex + 3.4 * k, ey + 0.6 * k),
                        (ex - 0.5 * k, ey + 1.8 * k)]), "#f1ebe2"),
           ellipse(ex + 1.6 * k, ey - 0.2 * k, 1.5 * k, 1.9 * k, iris),
           line([(ex - 4.6 * k, ey - 0.6 * k), (ex - 0.6 * k, ey - 2.6 * k), (ex + 3.6 * k, ey - 1.4 * k)], INK, 1.9 * k),
           line([(ex - 2.6 * k, ey + 2.0 * k), (ex + 2.6 * k, ey + 1.4 * k)], shade(f["skin"], 0.7), 0.8 * k)]
    if f.get("lids", 0):  # a heavy upper lid fold
        out.append(line([(ex - 4.0 * k, ey - 3.6 * k), (ex + 0.0 * k, ey - 4.8 * k), (ex + 3.4 * k, ey - 3.2 * k)], shade(f["skin"], 0.75), 0.9 * k))
    if f.get("lashes"):
        out.append(line([(ex + 3.0 * k, ey - 1.6 * k), (ex + 5.0 * k, ey - 2.8 * k)], INK, 1.2 * k))
    return out


def brow_side(g, f, u=-0.11, v=0.405):
    bx, by = g.Q(u, v)
    k = g.hh / 70.0
    th = f.get("brow_th", 2.6) * k
    tilt = f.get("brow_tilt", 0.0) * k
    return [line([(bx - 5.6 * k, by + 0.4 * k - tilt), (bx - 0.5 * k, by - 1.4 * k), (bx + 5.2 * k, by - 0.2 * k + tilt)], f.get("brow_c", INK), th)]


def ear_side(g, f, u=-0.52, v=0.56):
    c = g.Q(u, v)
    k = g.hh / 70.0
    q = frame(c, math.radians(-98))
    d = smooth([q(-8.5 * k, -1.5 * k), q(-6 * k, 5.2 * k), q(3 * k, 6 * k), q(8 * k, 3.4 * k), q(9.4 * k, -1.6 * k), q(6.8 * k, -4.6 * k), q(-2 * k, -4.2 * k)])
    sk = f["skin"]
    return cel(d, sk, [line([q(5.6 * k, 2.6 * k), q(5.8 * k, -1.6 * k), q(1.0 * k, -1.8 * k), q(-3.4 * k, 1.2 * k)], shade(sk, 0.66), 1.1 * k)],
               s=2.2, sw=2.4)


def head_side(g, f, hair_back=(), hair_front=(), extra=(), hair_mid=()):
    """The whole side head: hair behind, the skull and face, the ear, the
    features, hair in front."""
    sk = f["skin"]
    skd = shade(sk, 0.78)
    skdd = shade(sk, 0.6)
    out = list(hair_back)
    outline = head_side_outline(g, f)
    d = smooth(outline)
    n = f.get("nose", 0.13)
    droop = f.get("droop", 0.0)
    items = [
        # the jaw: from the chin back to under the ear, the cheek's shade below it
        line([g.Q(-0.08, 0.975 + f.get("jaw_drop", 0) * 0.8), g.Q(-0.3, 0.92), g.Q(-0.44, 0.84), g.Q(-0.47, 0.72)], skd, 1.3),
        path(smooth([g.Q(-0.47, 0.70), g.Q(-0.44, 0.84), g.Q(-0.30, 0.93), g.Q(-0.10, 0.99), g.Q(-0.32, 1.02), g.Q(-0.55, 0.96), g.Q(-0.6, 0.76)]), skd),
        # the eye socket's shade and the cheekbone
        path(smooth([g.Q(-0.17, 0.43), g.Q(-0.04, 0.415), g.Q(-0.01, 0.48), g.Q(-0.08, 0.5), g.Q(-0.16, 0.49)]), light(skd, 0.35)),
        line([g.Q(-0.27, 0.58), g.Q(-0.16, 0.6), g.Q(-0.08, 0.62)], skd, 1.0),
        # the nostril wing, the fold to the mouth
        path(smooth([g.Q(n - 0.075, 0.6 + droop), g.Q(n - 0.03, 0.592 + droop), g.Q(n - 0.03, 0.64 + droop * 0.6), g.Q(n - 0.08, 0.645 + droop * 0.6)]), skd),
        line([g.Q(n - 0.08, 0.605 + droop), g.Q(n - 0.095, 0.632 + droop), g.Q(n - 0.07, 0.65 + droop * 0.6)], skdd, 1.1),
        line([g.Q(n - 0.1, 0.655), g.Q(n - 0.13, 0.7), g.Q(n - 0.12, 0.76)], skd, 1.1),
        # the mouth's line, its corner set back in the cheek
        line([g.Q(-0.045, 0.757), g.Q(0.0, 0.752), g.Q(0.018 + f.get("lip", 0.02) * 0.4, 0.752)], INK, 1.5),
        ellipse(*g.Q(0.012, 0.785), 0.022 * g.hh, 0.012 * g.hh, f.get("lipc", shade(sk, 0.86))),
        # the light down the ridge of the nose
        line([g.Q(0.004, 0.45), g.Q(n * 0.55, 0.53), g.Q(n - 0.012, 0.585 + droop)], light(sk, 0.35), 1.4),
    ]
    for age in range(f.get("age", 0)):  # lines across the forehead, crow's feet
        items.append(line([g.Q(-0.2, 0.22 + age * 0.05), g.Q(-0.03, 0.21 + age * 0.05)], skd, 0.9))
    if f.get("age", 0) >= 2:
        items += [line([g.Q(-0.2, 0.465), g.Q(-0.25, 0.45)], skd, 0.8), line([g.Q(-0.2, 0.49), g.Q(-0.245, 0.5)], skd, 0.8)]
    if f.get("stubble"):
        items.append(path(smooth([g.Q(0.03, 0.8), g.Q(0.05, 0.9), g.Q(-0.03, 0.99), g.Q(-0.3, 0.93), g.Q(-0.44, 0.8), g.Q(-0.4, 0.68),
                                  g.Q(-0.2, 0.72), g.Q(-0.06, 0.66), g.Q(0.03, 0.66)]), f["stubble"], extra=' opacity="0.55"'))
    out += cel(d, sk, items, s=0.07 * g.hh, sdir=(-1.0, 0.35))
    out += list(hair_mid)
    out += ear_side(g, f)
    out += eye_side(g, f)
    out += brow_side(g, f)
    out += list(hair_front)
    out += list(extra)
    return out


def head_front_outline(g, f):
    w = f.get("w", 0.37)
    jaw, chinw, cheek = f.get("jaw", 0.82), f.get("chinw", 0.38), f.get("cheek", 1.0)
    jd = f.get("jaw_drop", 0.0)
    pts = [(0.0, 0.0), (w * 0.62, 0.035), (w * 0.93, 0.17), (w, 0.36), (w * cheek, 0.55), (w * jaw, 0.76), (w * chinw * 1.35, 0.9 + jd * 0.6), (w * chinw, 0.97 + jd),
           (0.0, 1.0 + jd)]
    right = [g.F(-u, v) for u, v in pts]  # screen-left half (his right)
    left = [g.F(u, v) for u, v in reversed(pts[1:-1])]
    return right + left


def head_front(g, f, hair_back=(), hair_front=(), extra=(), hair_mid=()):
    sk = f["skin"]
    skd = shade(sk, 0.78)
    skdd = shade(sk, 0.6)
    w = f.get("w", 0.37)
    k = g.hh / 70.0
    out = list(hair_back)
    n = f.get("nose_w", 0.075)
    ny = 0.6 + f.get("droop", 0.0)
    ey, ex = 0.47, f.get("eye_x", 0.165)
    items = [
        # the shade down his right side of the face and under the jaw
        path(smooth([g.F(-w, 0.3), g.F(-w + 0.06, 0.55), g.F(-w * 0.7, 0.8), g.F(-0.12, 0.96), g.F(-w * 0.92, 0.95), g.F(-w - 0.02, 0.6)]), skd),
        # the nose: the shaded flank, the tip, the nostrils
        path(smooth([g.F(-0.028, 0.46), g.F(-0.01, 0.46), g.F(-0.02, 0.56), g.F(-n * 0.8, ny), g.F(-n * 0.9, ny - 0.02)]), skd),
        line([g.F(-n, ny - 0.01), g.F(-n * 0.9, ny + 0.03), g.F(-0.03, ny + 0.035), g.F(0.0, ny + 0.03)], skdd, 1.3 * k),
        line([g.F(n, ny - 0.01), g.F(n * 0.9, ny + 0.03), g.F(0.03, ny + 0.035)], skdd, 1.1 * k),
        ellipse(*g.F(0.012, ny - 0.005), 0.018 * g.hh, 0.014 * g.hh, light(sk, 0.35)),
        # the eye sockets
        ellipse(*g.F(-ex, ey - 0.012), 0.072 * g.hh, 0.032 * g.hh, light(skd, 0.6)),
        ellipse(*g.F(ex, ey - 0.012), 0.072 * g.hh, 0.032 * g.hh, light(skd, 0.72)),
        # the mouth
        line([g.F(-f.get("mouth_w", 0.1), 0.75), g.F(-0.03, 0.745), g.F(0.03, 0.745), g.F(f.get("mouth_w", 0.1), 0.75)], INK, 1.6 * k),
        path(smooth([g.F(-0.06, 0.765), g.F(0.06, 0.765), g.F(0.04, 0.79), g.F(-0.04, 0.79)]), f.get("lipc", shade(sk, 0.86))),
        line([g.F(-0.04, 0.84), g.F(0.04, 0.84)], skd, 1.0 * k),
        line([g.F(-0.11, 0.66), g.F(-0.135, 0.72)], skd, 1.0 * k), line([g.F(0.11, 0.66), g.F(0.135, 0.72)], skd, 1.0 * k),
    ]
    for age in range(f.get("age", 0)):
        items.append(line([g.F(-0.13, 0.22 + age * 0.05), g.F(0.13, 0.215 + age * 0.05)], skd, 0.9 * k))
    if f.get("stubble"):
        items.append(path(smooth([g.F(-w * 0.95, 0.62), g.F(-0.12, 0.7), g.F(0.0, 0.69), g.F(0.12, 0.7), g.F(w * 0.95, 0.62), g.F(w * 0.8, 0.82),
                                  g.F(0.1, 1.0), g.F(-0.1, 1.0), g.F(-w * 0.8, 0.82)]), f["stubble"], extra=' opacity="0.55"'))
    out += cel(smooth(head_front_outline(g, f)), sk, items, s=0.05 * g.hh, sdir=(-1.0, 0.3))
    out += list(hair_mid)
    # the ears, over the hair at the temples, inked only where they stand off the face
    for sgn in (-1, 1):
        ux = sgn * (w - 0.025)
        run = [g.F(ux, 0.43), g.F(ux + sgn * 0.07, 0.415), g.F(ux + sgn * 0.09, 0.52), g.F(ux + sgn * 0.062, 0.645), g.F(ux - sgn * 0.005, 0.67)]
        e = smooth(run + [g.F(ux - sgn * 0.03, 0.55)])
        out += cel(e, sk if sgn > 0 else shade(sk, 0.86), [line([g.F(ux + sgn * 0.035, 0.46), g.F(ux + sgn * 0.055, 0.53), g.F(ux + sgn * 0.03, 0.6)], skdd, 1.1 * k)],
                   s=2.2, ink=False)
        out.append(line(run, INK, 2.4))
    iris = f.get("iris", "#3c3328")
    for sgn in (-1, 1):
        cx, cy = g.F(sgn * ex, ey)
        out += [path(smooth([(cx - 4.4 * k, cy + 0.2 * k), (cx, cy - 2.2 * k), (cx + 4.4 * k, cy + 0.2 * k), (cx, cy + 1.8 * k)]), "#f1ebe2"),
                ellipse(cx, cy - 0.1 * k, 1.7 * k, 1.9 * k, iris),
                line([(cx - 4.8 * k, cy + 0.2 * k), (cx - 1.2 * k, cy - 2.4 * k), (cx + 2.0 * k, cy - 2.3 * k), (cx + 4.8 * k, cy + 0.0 * k)], INK, 1.9 * k),
                line([(cx - 2.8 * k, cy + 2.2 * k), (cx + 2.8 * k, cy + 2.2 * k)], skd, 0.8 * k)]
        if f.get("lids", 0):
            out.append(line([(cx - 4.0 * k, cy - 3.8 * k), (cx + 4.0 * k, cy - 3.8 * k)], skd, 0.9 * k))
        if f.get("lashes"):
            out.append(line([(cx + sgn * 4.6 * k, cy - 0.2 * k), (cx + sgn * 6.4 * k, cy - 1.6 * k)], INK, 1.2 * k))
        th = f.get("brow_th", 2.6) * k
        tilt = f.get("brow_tilt", 0.0) * k
        bx, by = g.F(sgn * (ex + 0.005), 0.405)
        out.append(line([(bx - sgn * 5.8 * k, by + 0.8 * k + tilt), (bx - sgn * 0.5 * k, by - 1.0 * k), (bx + sgn * 5.8 * k, by + 0.2 * k - tilt)],
                        f.get("brow_c", INK), th))
    out += list(hair_front)
    out += list(extra)
    return out


# ---- hair helpers --------------------------------------------------------------------------

def cap_hair_side(g, th0, th1, t, inner, n=10):
    """Hair hugging the skull: the cranium arc from ``th0`` to ``th1`` (degrees,
    back to front through the top) pushed out by ``t``, closed back along
    ``inner`` (head-local points from the front hairline to the nape)."""
    arc = [cran(g, th0 + (th1 - th0) * i / n, t) for i in range(n + 1)]
    return smooth(arc + [g.Q(*p) for p in inner])


def front_cap(g, f, t, line_pts, top=-0.035):
    """Hair over the top of the head, seen from the front: the outline pushed
    out by ``t``, the hairline ``line_pts`` (screen-left to right, front-local)."""
    w = f.get("w", 0.37) + t
    arc = [g.F(-w * 1.0, 0.42), g.F(-w * 0.98, 0.2), g.F(-w * 0.66, 0.02), g.F(0, top), g.F(w * 0.66, 0.02), g.F(w * 0.98, 0.2), g.F(w, 0.42)]
    return smooth(arc + [g.F(*p) for p in reversed(line_pts)])


# ============================================================================================
# the body: limbs, hands, feet
# ============================================================================================

def limb(a, b, r0, r1, base, s=4.0, items=(), sw=None):
    return cel(capsule(a, b, r0, r1), base, items, s=s, sw=sw)


def hand_side(w, a, L, skin, near=True, grip=False):
    """A hand from wrist ``w`` along ``a``: a relaxed hand seen from its back,
    the thumb toward the front (+s), the fingers together and curled a little;
    ``grip``: a fist round something held across it."""
    q = frame(w, a)
    k = L / 30.0
    sk = skin if near else shade(skin, 0.86)
    if grip:
        d = smooth([q(-2 * k, -6 * k), q(8 * k, -8.6 * k), q(17 * k, -8.2 * k), q(21 * k, -4 * k), q(21 * k, 4 * k), q(16 * k, 8.6 * k), q(6 * k, 8.4 * k),
                    q(-2 * k, 6 * k)])
        items = [line([q(14 * k, -6 * k), q(15 * k, 6 * k)], shade(sk, 0.7), 1.1), line([q(18.6 * k, -3 * k), q(19 * k, 3.4 * k)], shade(sk, 0.7), 0.9)]
        out = cel(d, sk, items, s=2.5, sw=2.8)
        thumb = smooth([q(3 * k, 5 * k), q(10 * k, 9.4 * k), q(16 * k, 9 * k), q(16.6 * k, 5.6 * k), q(9 * k, 4 * k)])
        return out + cel(thumb, sk, [], s=1.5, sw=2.2)
    thumb = smooth([q(2 * k, 4.8 * k), q(9 * k, 8.8 * k), q(15.4 * k, 9.2 * k), q(17.2 * k, 7.4 * k), q(12 * k, 4.4 * k), q(6 * k, 2.4 * k)])
    out = cel(thumb, sk, [], s=1.5, sw=2.2)
    d = smooth([q(-2 * k, -6.4 * k), q(8 * k, -7.4 * k), q(18 * k, -6.6 * k), q(26 * k, -4.4 * k), q(30 * k, -0.6 * k), q(29 * k, 3.6 * k),
                q(24 * k, 5.6 * k), q(15 * k, 5.8 * k), q(6 * k, 6.2 * k), q(-2 * k, 6.2 * k)])
    items = [line([q(14 * k, -2.0 * k), q(26 * k, -1.6 * k)], shade(sk, 0.7), 0.9), line([q(15 * k, 1.8 * k), q(26.5 * k, 2.2 * k)], shade(sk, 0.7), 0.9),
             line([q(11 * k, -5.8 * k), q(13 * k, 4.6 * k)], shade(sk, 0.8), 0.8)]
    return out + cel(d, sk, items, s=2.6, sw=2.8)


def hand_front(w, a, L, skin, inward):
    """A relaxed hand hanging at the side, seen from the front: edge-on, the
    thumb lying down the front of it, the index curled toward the thigh."""
    q = frame(w, a)
    k = L / 30.0
    p = lambda t, i: q(t * k, -i * k * inward)  # noqa: E731
    d = smooth([p(-2, -5.6), p(10, -6.4), p(22, -5.0), p(28, -1.2), p(27, 3.4), p(20, 6.0), p(8, 6.2), p(-2, 5.6)])
    out = cel(d, skin, [line([p(15, 2.0), p(25, 1.4)], shade(skin, 0.7), 0.9), line([p(17, -2), p(25, -2.6)], shade(skin, 0.7), 0.9)], s=2.4, sw=2.8)
    thumb = smooth([p(2, -4), p(12, -7.4), p(19, -6.4), p(19, -3.6), p(10, -2.4)])
    return out + cel(thumb, skin, [], s=1.5, sw=2.2)


def shoe_side(ankle, L, base, kind="shoe", near=True, top=None):
    """A shoe or boot in profile, the toe toward +x, its sole on the ground."""
    ax, ay = ankle
    k = L / 50.0
    c = base if near else shade(base, 0.82)
    if kind == "boot":
        top = top if top is not None else ay - 46 * k
        d = smooth([(ax - 9 * k, top, True), (ax + 9 * k, top, True), (ax + 9 * k, ay - 4 * k), (ax + 20 * k, ay + 2 * k), (ax + 36 * k, GROUND - 7 * k),
                    (ax + 38 * k, GROUND, True), (ax - 12 * k, GROUND, True), (ax - 12 * k, ay - 6 * k), (ax - 10 * k, ay - 20 * k)])
        items = [line([(ax - 13 * k, GROUND - 4 * k), (ax + 38 * k, GROUND - 4 * k)], shade(c, 0.6), 2.4 * k),
                 line([(ax - 10 * k, top + 6 * k), (ax + 10 * k, top + 6 * k)], shade(c, 0.7), 1.4)]
    else:
        d = smooth([(ax - 9 * k, ay - 6 * k), (ax + 6 * k, ay - 5 * k), (ax + 20 * k, ay + 1 * k), (ax + 34 * k, GROUND - 7 * k), (ax + 37 * k, GROUND, True),
                    (ax - 12 * k, GROUND, True), (ax - 12 * k, ay + 2 * k)])
        items = [line([(ax - 13 * k, GROUND - 3.5 * k), (ax + 37 * k, GROUND - 3.5 * k)], shade(c, 0.6), 2.2 * k)]
    return cel(d, c, items, s=3, l=1.6)


def shoe_front(ankle, L, base, kind="shoe", top=None, sgn=1):
    ax, ay = ankle
    k = L / 50.0
    if kind == "boot":
        top = top if top is not None else ay - 46 * k
        d = smooth([(ax - 10 * k, top, True), (ax + 10 * k, top, True), (ax + 10.5 * k, ay), (ax + 12 * k + sgn * 2 * k, GROUND - 6 * k),
                    (ax + 11 * k + sgn * 2 * k, GROUND, True), (ax - 11 * k + sgn * 2 * k, GROUND, True), (ax - 12 * k + sgn * 2 * k, GROUND - 6 * k), (ax - 10.5 * k, ay)])
        items = [line([(ax - 11 * k, top + 6 * k), (ax + 11 * k, top + 6 * k)], shade(base, 0.7), 1.4)]
    else:
        d = smooth([(ax - 9 * k, ay - 3 * k), (ax + 9 * k, ay - 3 * k), (ax + 12 * k + sgn * 2 * k, GROUND - 7 * k), (ax + 11 * k + sgn * 2 * k, GROUND, True),
                    (ax - 11 * k + sgn * 2 * k, GROUND, True), (ax - 12 * k + sgn * 2 * k, GROUND - 7 * k)])
        items = []
    items.append(line([(ax - 12 * k, GROUND - 3.5 * k), (ax + 13 * k, GROUND - 3.5 * k)], shade(base, 0.6), 2.2 * k))
    return cel(d, base, items, s=3, l=1.6)


# ============================================================================================
# drawing a look
# ============================================================================================

class Fig:
    """One view being drawn: ``add(z, items)`` collects layers; ``svg()`` writes them in z order."""

    def __init__(self, look, view):
        self.L = look
        self.view = view
        self.g = Geo(look)
        self.layers: List[Tuple[float, str, List[str]]] = []

    def add(self, z, name, items):
        self.layers.append((z, name, list(items)))

    def svg(self, title):
        self.layers.sort(key=lambda q: q[0])
        out = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"',
               f'     width="{W}" height="{H}" viewBox="0 0 {W} {H}" data-character-design="{self.L["id"]}-r1">',
               f'  <!-- CANDIDATE, NOT CAST: {title}, {self.view} view (2026-10-22); the ground at y={GROUND:g}.',
               '       Drawn by scripts/svg_art/vault_merchant_hero_art.py. -->',
               f'  <g id="{self.L["id"]}" inkscape:groupmode="layer" inkscape:label="{title} - {self.view}">']
        for z, name, items in self.layers:
            out.append(f'    <g id="{self.view}-{name}" inkscape:groupmode="layer" inkscape:label="{name}" data-rig-z="{svg.f(z)}">')
            out += ["      " + it for it in items]
            out.append("    </g>")
        out += ["  </g>", "</svg>"]
        return "\n".join(out) + "\n"


# z bands
Z_BACK, Z_FARARM, Z_FARLEG, Z_FARSKIRT, Z_LEG, Z_TORSO, Z_VEST, Z_COAT, Z_APRON, Z_BELT, Z_NECK, Z_HEAD, Z_HAT, Z_HELD, Z_ARM, Z_HAND = (
    0, 10, 20, 25, 30, 40, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95)


def side_torso_pts(g, top_off=0.0):
    """The torso in profile, from the throat down the front, round the seat, up the back."""
    H = g.H
    return [
        (CX + H * 0.03, g.chin + H * 0.012 + top_off), (CX + g.dchest * 0.75, g.sh_y + H * 0.02), (CX + g.dchest + g.bust, g.chest_y + H * 0.012),
        (CX + g.dchest * 0.92 + g.bust * 0.3, g.waist_y - H * 0.035), (CX + g.dchest * 0.86 + g.belly, g.waist_y + H * 0.03),
        (CX + g.dchest * 0.82 + g.belly * 0.75, g.hip_y), (CX + H * 0.05, g.crotch_y + H * 0.006),
        (CX - H * 0.035, g.crotch_y + H * 0.01), (CX - g.dback - g.seat, g.hip_y + H * 0.012), (CX - g.dback * 0.86, g.waist_y),
        (CX - g.dback, g.sh_y + H * 0.05), (CX - g.dback * 0.7, g.sh_y + H * 0.005), (CX - H * 0.032, g.chin + H * 0.004 + top_off),
    ]


def front_torso_pts(g):
    H = g.H
    nk = H * 0.032
    return [
        (CX - nk, g.chin + H * 0.008), (CX - g.sw * 0.72, g.sh_y + H * 0.004), (CX - g.sw, g.sh_y + H * 0.03), (CX - g.sw + H * 0.012, g.chest_y + H * 0.02),
        (CX - g.ww - g.belly * 0.5, g.waist_y), (CX - g.hw, g.hip_y), (CX - g.hw * 0.98, g.crotch_y + H * 0.012),
        (CX + g.hw * 0.98, g.crotch_y + H * 0.012), (CX + g.hw, g.hip_y), (CX + g.ww + g.belly * 0.5, g.waist_y), (CX + g.sw - H * 0.012, g.chest_y + H * 0.02),
        (CX + g.sw, g.sh_y + H * 0.03), (CX + g.sw * 0.72, g.sh_y + H * 0.004), (CX + nk, g.chin + H * 0.008),
    ]


def neck_side(g, skin):
    H = g.H
    d = smooth([g.Q(-0.3, 0.7), g.Q(-0.1, 0.86), (CX + H * 0.035, g.chin + H * 0.02), (CX + H * 0.03, g.sh_y + H * 0.01),
                (CX - H * 0.035, g.sh_y + H * 0.01), (CX - H * 0.04, g.chin), g.Q(-0.62, 0.8)])
    return cel(d, skin, [], s=5)


def neck_front(g, skin):
    H = g.H
    d = smooth([(CX - H * 0.032, g.chin - H * 0.03), (CX + H * 0.032, g.chin - H * 0.03), (CX + H * 0.036, g.sh_y + H * 0.012),
                (CX - H * 0.036, g.sh_y + H * 0.012)])
    return cel(d, skin, [path(smooth([(CX - H * 0.034, g.chin), (CX + H * 0.034, g.chin), (CX + H * 0.03, g.chin + H * 0.022),
                                      (CX - H * 0.03, g.chin + H * 0.022)]), shade(skin, 0.78))], s=5)


def body_side(fig, P):
    """The dressed body in profile, from the palette ``P``: legs in ``legs``
    (trousers), shoes or boots, the torso in ``shirt``, the arms in ``sleeve``
    to the wrist (or to ``P['cuff_at']`` with bare forearms), the hands."""
    g = fig.g
    H = g.H
    lr = g.limb
    for side, zl, za in (("far", Z_FARLEG, Z_FARARM), ("near", Z_LEG, Z_ARM)):
        near = side == "near"
        hip, knee, ankle = g.s_leg[side]
        c = P["legs"] if near else shade(P["legs"], 0.84)
        if not P.get("no_legs"):
            fig.add(zl, f"{side}-thigh", cel(capsule(hip, knee, H * 0.052 * lr, H * 0.036 * lr), c, s=4))
            fig.add(zl + 0.1, f"{side}-shin", cel(capsule(knee, (ankle[0], ankle[1] - H * 0.01), H * 0.036 * lr, H * 0.028 * lr), c, s=4))
        fig.add(zl + 0.2, f"{side}-foot", shoe_side(ankle, H * 0.13, P["shoe"], P.get("shoe_kind", "shoe"), near, top=P.get("boot_top")))
        s, e, w = g.s_arm[side]
        sc = P["sleeve"] if near else shade(P["sleeve"], 0.84)
        if not P.get("no_arms"):
            fig.add(za, f"{side}-arm-upper", cel(capsule(s, e, H * 0.032 * lr, H * 0.028 * lr), sc, s=4))
            fc = sc if not P.get("bare_forearm") else (P["face"]["skin"] if near else shade(P["face"]["skin"], 0.86))
            fig.add(za + 0.1, f"{side}-arm-lower", cel(capsule(e, w, H * 0.026 * lr, H * 0.02 * lr) if P.get("bare_forearm") else
                                                       capsule(e, w, H * 0.028 * lr, H * 0.022 * lr), fc, s=4))
            if P.get("bare_forearm"):
                q = frame(e, ang(e, w))
                fig.add(za + 0.15, f"{side}-roll", cel(smooth([q(-H * 0.012, -H * 0.036), q(H * 0.022, -H * 0.034), q(H * 0.024, H * 0.034), q(-H * 0.012, H * 0.036)]),
                                                       sc, [line([q(H * 0.005, -H * 0.03), q(H * 0.006, H * 0.03)], shade(sc, 0.75), 1.2)], s=3))
        if not P.get("hand_held", {}).get(side):
            fig.add(za + 0.3, f"{side}-hand", hand_side(w, ang(e, w) - 0.08, H * 0.088, P["face"]["skin"], near))
    if not P.get("no_torso"):
        fig.add(Z_TORSO, "torso", cel(smooth(side_torso_pts(g)), P["shirt"], s=6))
    fig.add(Z_NECK - 2, "neck", neck_side(g, P["face"]["skin"]))


def body_front(fig, P):
    g = fig.g
    H = g.H
    lr = g.limb
    for side, sgn in (("right", -1), ("left", 1)):
        hip, knee, ankle = g.f_leg[side]
        if not P.get("no_legs"):
            fig.add(Z_LEG, f"{side}-thigh", cel(capsule(hip, knee, H * 0.05 * lr, H * 0.037 * lr), P["legs"], s=4))
            fig.add(Z_LEG + 0.1, f"{side}-shin", cel(capsule(knee, (ankle[0], ankle[1] - H * 0.01), H * 0.037 * lr, H * 0.029 * lr), P["legs"], s=4))
        fig.add(Z_LEG + 0.2, f"{side}-foot", shoe_front(ankle, H * 0.13, P["shoe"], P.get("shoe_kind", "shoe"), top=P.get("boot_top"), sgn=sgn))
        s, e, w = g.f_arm[side]
        if not P.get("no_arms"):
            fig.add(Z_ARM, f"{side}-arm-upper", cel(capsule(s, e, H * 0.032 * lr, H * 0.028 * lr), P["sleeve"], s=4))
            fc = P["sleeve"] if not P.get("bare_forearm") else P["face"]["skin"]
            fig.add(Z_ARM + 0.1, f"{side}-arm-lower", cel(capsule(e, w, H * 0.026 * lr, H * 0.02 * lr) if P.get("bare_forearm") else
                                                          capsule(e, w, H * 0.028 * lr, H * 0.022 * lr), fc, s=4))
            if P.get("bare_forearm"):
                q = frame(e, ang(e, w))
                fig.add(Z_ARM + 0.15, f"{side}-roll", cel(smooth([q(-H * 0.012, -H * 0.036), q(H * 0.022, -H * 0.034), q(H * 0.024, H * 0.034), q(-H * 0.012, H * 0.036)]),
                                                          P["sleeve"], [line([q(H * 0.005, -H * 0.03), q(H * 0.006, H * 0.03)], shade(P["sleeve"], 0.75), 1.2)], s=3))
        if not P.get("hand_held", {}).get(side):
            fig.add(Z_HAND, f"{side}-hand", hand_front(w, ang(e, w), H * 0.088, P["face"]["skin"], -sgn))
    if not P.get("no_torso"):
        fig.add(Z_TORSO, "torso", cel(smooth(front_torso_pts(g)), P["shirt"], s=6))
    fig.add(Z_NECK - 2, "neck", neck_front(g, P["face"]["skin"]))


# ============================================================================================
# LOOKS (filled in below by the character sections)
# ============================================================================================

#: look id -> dict(id, char, letter, label, H, hr, build, palette P, side(fig), front(fig))
LOOKS: Dict[str, Dict] = {}
CHARS = {
    "vault_keeper": "Vault Keeper",
    "merchant_prototype": "Merchant Prototype",
    "general_hero": "General Hero",
}
#: 1 cm in SVG units: the General Hero (185 cm) stands 370 units.
CM = 2.0


def look(**kw):
    LOOKS[kw["id"]] = kw
    return kw


def draw(look_id: str, view: str) -> str:
    L = LOOKS[look_id]
    fig = Fig(L, view)
    if L.get("pose"):
        L["pose"](fig.g)
    _N[0] = 0
    svg.configure(dx=0, dy=0, ink=INK, ow=OUT / 2, colors={})
    (L["side"] if view == "side" else L["front"])(fig)
    return fig.svg(f"{CHARS[L['char']]} {L['letter']}: {L['label']}")


# ============================================================================================
# shared costume pieces
# ============================================================================================

def coat_side(g, top_y, front_dx, hem_y, hem_front, hem_back, flare=0.0):
    """A coat's body in profile, collar to hem, a little proud of the torso."""
    H = g.H
    return [
        (CX + H * 0.034, top_y), (CX + g.dchest * 0.8 + front_dx, g.sh_y + H * 0.02), (CX + g.dchest + g.bust + front_dx, g.chest_y + H * 0.01),
        (CX + g.dchest * 0.94 + g.belly + front_dx, g.waist_y + H * 0.02), (CX + g.dchest * 0.86 + g.belly * 0.8 + front_dx, g.hip_y),
        (CX + hem_front, hem_y - H * 0.004, True), (CX - hem_back - flare, hem_y, True), (CX - g.dback - g.seat - front_dx * 0.8 - flare * 0.5, g.hip_y + H * 0.02),
        (CX - g.dback * 0.88 - front_dx * 0.6, g.waist_y), (CX - g.dback - front_dx * 0.7, g.sh_y + H * 0.05), (CX - g.dback * 0.72, g.sh_y),
        (CX - H * 0.03, top_y + H * 0.002),
    ]


def coat_front(g, top_y, out_dx, hem_y, hem_w, open_w=0.0):
    """A coat's body from the front (closed when ``open_w`` is 0)."""
    H = g.H
    half = [(CX, top_y + H * 0.02), (CX - H * 0.034, top_y), (CX - g.sw * 0.74, g.sh_y + H * 0.002), (CX - g.sw - out_dx * 0.5, g.sh_y + H * 0.03),
            (CX - g.sw + H * 0.012 - out_dx, g.chest_y + H * 0.02), (CX - g.ww - g.belly * 0.5 - out_dx, g.waist_y), (CX - g.hw - out_dx, g.hip_y),
            (CX - hem_w, hem_y, True), (CX - open_w, hem_y + H * 0.004, True)]
    return half + mx(list(reversed(half)))[1:-1] if not open_w else half


def buttons(pts, r, fill, ring=None):
    return [ellipse(x, y, r, r, fill, INK, 1.0) for x, y in pts]


def key_ring(c, r, iron, n=5, a0=60.0, a1=125.0, big=1.0):
    """An iron ring of big old keys hanging from ``c``."""
    out = [ellipse(c[0], c[1] + r, r, r, "none", INK, 4.4), ellipse(c[0], c[1] + r, r, r, "none", iron, 2.2)]
    for i in range(n):
        a = math.radians(a0 + (a1 - a0) * i / max(1, n - 1))
        b = (c[0] + math.cos(a) * r, c[1] + r + math.sin(a) * r)
        q = frame(b, a)
        L = (22 + 5 * ((i * 7) % 3)) * big
        d = smooth([q(-3, -3.6), q(5, -4.4), q(8, 0), q(5, 4.4), q(-3, 3.6), q(-5, 0)])
        out += cel(d, iron, [ellipse(*q(1.6, 0), 1.6, 1.6, shade(iron, 0.5))], s=1.5, sw=2.2)
        out += cel(smooth([q(6, -1.8, ), q(L, -1.6, ), q(L, 1.6), q(6, 1.8)]), iron, [], s=1.0, sw=2.2)
        out += cel(smooth([q(L - 8, 1.4, True), q(L - 0.5, 1.4, True), q(L - 0.5, 6, True), q(L - 4, 6, True), q(L - 4, 4.2, True), q(L - 8, 4.2, True)]),
                   iron, [], s=1.0, sw=2.0)
    return out


def ledger_book(x0, y0, x1, y1, leather, page="#efe6cf", corner="#c9a24a", strap=None, face=True):
    """A thick ledger: its board, gilt corners, a strap; ``face`` False shows
    the spine/edge (seen from the front, under the arm)."""
    if face:
        out = cel(rect(x0, y0, x1, y1, 3), leather, [line([(x0 + 5, y0 + 5), (x1 - 5, y0 + 5)], light(leather, 0.25), 1.2)], s=4)
        for cx, cy, sx, sy in ((x1, y0, -1, 1), (x1, y1, -1, -1), (x0, y0, 1, 1), (x0, y1, 1, -1)):
            out += flat(smooth([(cx, cy, True), (cx + sx * 10, cy, True), (cx, cy + sy * 10, True)]), corner, 1.6)
        lx = x0 + (x1 - x0) * 0.32
        out += flat(rect(lx, (y0 + y1) / 2 - 7, x0 + (x1 - x0) * 0.68, (y0 + y1) / 2 + 7, 2), page, 1.6)
        out.append(line([(lx + 4, (y0 + y1) / 2 - 1.5), (x0 + (x1 - x0) * 0.68 - 4, (y0 + y1) / 2 - 1.5)], "#8a7c66", 1.0))
        out.append(line([(lx + 4, (y0 + y1) / 2 + 2.5), (x0 + (x1 - x0) * 0.6, (y0 + y1) / 2 + 2.5)], "#8a7c66", 1.0))
        if strap:
            sx = x0 + (x1 - x0) * 0.82
            out += cel(rect(sx - 4, y0 - 2, sx + 4, y1 + 2, 1), strap, [], s=1.5, sw=2.2)
            out += flat(rect(sx - 5, (y0 + y1) / 2 - 4, sx + 5, (y0 + y1) / 2 + 4, 1), corner, 1.6)
        return out
    out = cel(rect(x0, y0, x1, y1, 2.5), page, [line([(x0 + 2, y), (x1 - 2, y)], "#c9bb9c", 0.8) for y in range(int(y0) + 5, int(y1) - 2, 3)], s=2)
    out += cel(rect(x0 - 2, y0 - 3, x1 + 2, y0 + 3, 1.5), leather, [], s=1.5, sw=2.4) + cel(rect(x0 - 2, y1 - 3, x1 + 2, y1 + 3, 1.5), leather, [], s=1.5, sw=2.4)
    return out


def spectacles_side(g, rim="#c9cdd3"):
    """Small round spectacles seen edge-on: the lens just ahead of the eye, the
    temple arm running back to the top of the ear."""
    ex, ey = g.Q(-0.03, 0.475)
    r = g.hh * 0.052
    arm = [(ex - 1, ey - r * 0.4), g.Q(-0.3, 0.45), g.Q(-0.45, 0.46)]
    return [line(arm, INK, 2.6), line(arm, rim, 1.0),
            ellipse(ex, ey, r * 0.28, r, "#dfe9ee", INK, 2.2), ellipse(ex, ey, r * 0.28, r, "none", rim, 1.0)]


def spectacles_front(g, f, rim="#c9cdd3"):
    out = []
    r = g.hh * 0.06
    ex = f.get("eye_x", 0.165)
    for sgn in (-1, 1):
        c = g.F(sgn * ex, 0.47)
        out += [ellipse(c[0], c[1], r, r * 0.86, "none", INK, 2.6), ellipse(c[0], c[1], r, r * 0.86, "none", rim, 1.2)]
    a, b = g.F(-ex + r / g.hh, 0.465), g.F(ex - r / g.hh, 0.465)
    out += [line([a, ((a[0] + b[0]) / 2, a[1] - 2), b], INK, 2.4), line([a, ((a[0] + b[0]) / 2, a[1] - 2), b], rim, 1.0)]
    return out


# ============================================================================================
# VAULT KEEPER
# ============================================================================================

def keeper_a_face():
    return dict(skin="#e3b18f", nose=0.15, hook=0.025, droop=0.012, brow=0.035, lip=0.012, chin=0.03, jaw_drop=0.02, w=0.4, jaw=0.92, chinw=0.46, cheek=1.02,
                brow_th=3.6, brow_c="#9c968e", age=2, lids=1, iris="#3e4a52", nose_w=0.085, mouth_w=0.11)


def keeper_a_hair_side(g, hair):
    """Bald on top; the grey fringe round the back of the head over the ears
    (``mid``: under the ear); short grey mutton-chop whiskers down the cheek
    in front of the ear to the jaw (``front``)."""
    fringe = cap_hair_side(g, 134, 200, 0.022, [(-0.78, 0.36), (-0.72, 0.38), (-0.66, 0.36, True), (-0.58, 0.4), (-0.5, 0.39, True), (-0.42, 0.42),
                                                (-0.41, 0.47), (-0.52, 0.47), (-0.63, 0.53), (-0.67, 0.7), (-0.67, 0.85)])
    mid = cel(fringe, hair, [line([g.Q(-0.82, 0.42), g.Q(-0.8, 0.6)], shade(hair, 0.8), 1.0)], s=3, sw=2.8)
    chop = smooth([g.Q(-0.43, 0.43), g.Q(-0.37, 0.45), g.Q(-0.34, 0.6), g.Q(-0.29, 0.72), g.Q(-0.25, 0.81, True), g.Q(-0.31, 0.84), g.Q(-0.38, 0.78),
                   g.Q(-0.42, 0.64)])
    front = cel(chop, hair, [line([g.Q(-0.385, 0.56), g.Q(-0.33, 0.74)], shade(hair, 0.8), 1.0)], s=2.5, sw=2.6)
    return mid, front


def keeper_a_hair_front(g, f, hair):
    """From the front: the fringe a tuft over each ear, the chops down each cheek."""
    out = []
    w = f["w"]
    for sgn in (-1, 1):
        tuft = smooth([g.F(sgn * (w - 0.04), 0.3), g.F(sgn * (w + 0.035), 0.28), g.F(sgn * (w + 0.06), 0.38), g.F(sgn * (w + 0.03), 0.46),
                       g.F(sgn * (w - 0.03), 0.46)])
        out += cel(tuft, hair, [], s=2.5, sw=2.6)
        chop = smooth([g.F(sgn * (w - 0.02), 0.46), g.F(sgn * (w + 0.005), 0.6), g.F(sgn * (w * 0.92), 0.76), g.F(sgn * (w * 0.8), 0.86, True),
                       g.F(sgn * (w * 0.72), 0.78), g.F(sgn * (w * 0.8), 0.6), g.F(sgn * (w - 0.075), 0.47)])
        out += cel(chop, hair, [line([g.F(sgn * (w * 0.88), 0.6), g.F(sgn * (w * 0.84), 0.76)], shade(hair, 0.8), 1.0)], s=2.5, sw=2.6)
    return out


def keeper_a_side(fig):
    L, g = fig.L, fig.g
    P = L["P"]
    H = g.H
    body_side(fig, P)
    # the frock coat, buttoned to the throat, to the knee
    hem = g.knee_y - H * 0.012
    d = smooth(coat_side(g, g.chin + H * 0.022, H * 0.012, hem, H * 0.07, H * 0.098, flare=H * 0.006))
    items = [line([(CX - H * 0.005, g.waist_y + H * 0.03), (CX - H * 0.02, hem - 4)], shade(P["coat"], 0.75), 1.4),
             line([(CX + H * 0.045, g.hip_y + H * 0.01), (CX + H * 0.052, hem - 4)], shade(P["coat"], 0.75), 1.2)]
    fx = CX + g.dchest * 0.86 + g.belly * 0.8
    items += buttons([(fx - 3, g.sh_y + H * 0.04), (fx + 1, g.chest_y), (fx + 2, g.chest_y + H * 0.04), (fx, g.waist_y - H * 0.005)], 2.4, P["silver"])
    fig.add(Z_COAT, "coat", cel(d, P["coat"], items, s=7))
    # the standing collar and the white stock above it
    fig.add(Z_NECK + 1, "collar", cel(smooth([(CX - H * 0.045, g.chin + H * 0.0), (CX + H * 0.03, g.chin + H * 0.014), (CX + H * 0.042, g.chin + H * 0.04),
                                              (CX - H * 0.04, g.sh_y + H * 0.006)]), P["coat"], [], s=3))
    fig.add(Z_NECK + 0.5, "stock", cel(smooth([(CX + H * 0.02, g.chin + H * 0.004), (CX + H * 0.04, g.chin + H * 0.012), (CX + H * 0.036, g.chin + H * 0.028),
                                               (CX + H * 0.02, g.chin + H * 0.03)]), P["linen"], [], s=2))
    # the belt and its silver buckle, worn over the coat
    by = g.waist_y + H * 0.012
    bf = CX + g.dchest * 0.94 + g.belly + H * 0.014
    belt = smooth([(CX - g.dback * 0.9 - H * 0.008, by - H * 0.016), (bf, by - H * 0.016, True), (bf, by + H * 0.016, True), (CX - g.dback * 0.9 - H * 0.008, by + H * 0.016)])
    fig.add(Z_BELT, "belt", cel(belt, P["belt"], [], s=2))
    fig.add(Z_BELT + 0.1, "buckle", cel(rect(bf - H * 0.012, by - H * 0.024, bf + H * 0.006, by + H * 0.024, 2), P["silver"],
                                       [line([(bf - H * 0.004, by - H * 0.016), (bf - H * 0.004, by + H * 0.016)], shade(P["silver"], 0.7), 1.2)], s=2))
    fig.add(Z_BELT + 0.2, "keys", key_ring((CX - H * 0.045, by + H * 0.012), H * 0.024, P["iron"], n=5, a0=50, a1=130))
    # the ledger, under his near arm
    fig.add(Z_HELD, "ledger", ledger_book(CX - H * 0.075, g.chest_y + H * 0.005, CX + H * 0.07, g.waist_y + H * 0.04, P["ledger"], strap=P["belt"]))
    f = P["face"]
    fig.add(Z_HEAD, "head", head_side(g, f, hair_mid=keeper_a_hair_side(g, P["hair"])[0], hair_front=keeper_a_hair_side(g, P["hair"])[1],
                                      extra=spectacles_side(g, P["silver"])))
    # the coat sleeves' deep cuffs
    for side in ("near", "far"):
        s, e, w = g.s_arm[side]
        q = frame(w, ang(e, w))
        c = P["coat"] if side == "near" else shade(P["coat"], 0.84)
        fig.add((Z_ARM if side == "near" else Z_FARARM) + 0.2, f"{side}-cuff",
                cel(smooth([q(-H * 0.05, -H * 0.03), q(0, -H * 0.031), q(0, H * 0.031), q(-H * 0.05, H * 0.03)]), c,
                    [buttons([q(-H * 0.02, -H * 0.018)], 1.8, P["silver"])[0]], s=3))


def keeper_a_front(fig):
    L, g = fig.L, fig.g
    P = L["P"]
    H = g.H
    body_front(fig, P)
    hem = g.knee_y - H * 0.012
    d = smooth(coat_front(g, g.chin + H * 0.02, H * 0.012, hem, g.hw + H * 0.04))
    items = []
    for sgn in (-1, 1):
        items += buttons([(CX + sgn * H * 0.03, y) for y in (g.sh_y + H * 0.03, g.chest_y + H * 0.01, g.chest_y + H * 0.05, g.waist_y - H * 0.0)], 2.4, P["silver"])
    items += [line([(CX, g.chin + H * 0.03), (CX + H * 0.004, hem)], shade(P["coat"], 0.6), 1.6),
              line([(CX - g.hw * 0.6, g.hip_y), (CX - g.hw * 0.8, hem - 3)], shade(P["coat"], 0.75), 1.2),
              line([(CX + g.hw * 0.6, g.hip_y), (CX + g.hw * 0.8, hem - 3)], shade(P["coat"], 0.75), 1.2)]
    fig.add(Z_COAT, "coat", cel(d, P["coat"], items, s=7))
    fig.add(Z_NECK + 1, "collar", cel(smooth([(CX - H * 0.042, g.chin - H * 0.004), (CX - H * 0.012, g.chin + H * 0.026), (CX + H * 0.012, g.chin + H * 0.026),
                                              (CX + H * 0.042, g.chin - H * 0.004), (CX + H * 0.05, g.sh_y + H * 0.004), (CX - H * 0.05, g.sh_y + H * 0.004)]), P["coat"], [], s=3))
    fig.add(Z_NECK + 0.5, "stock", cel(smooth([(CX - H * 0.014, g.chin + H * 0.006), (CX + H * 0.014, g.chin + H * 0.006), (CX + H * 0.01, g.chin + H * 0.03),
                                               (CX - H * 0.01, g.chin + H * 0.03)]), P["linen"], [], s=2))
    by = g.waist_y + H * 0.012
    bw = g.ww + g.belly * 0.5 + H * 0.016
    fig.add(Z_BELT, "belt", cel(rect(CX - bw, by - H * 0.016, CX + bw, by + H * 0.016), P["belt"], [], s=2))
    fig.add(Z_BELT + 0.1, "buckle", cel(rect(CX - H * 0.03, by - H * 0.026, CX + H * 0.03, by + H * 0.026, 3), P["silver"],
                                       [path(rect(CX - H * 0.016, by - H * 0.012, CX + H * 0.016, by + H * 0.012, 1.5), P["belt"], INK, 1.4),
                                        line([(CX - H * 0.024, by - H * 0.02), (CX + H * 0.022, by - H * 0.02)], light(P["silver"], 0.5), 1.0)], s=2))
    fig.add(Z_BELT + 0.2, "keys", key_ring((CX + g.ww + H * 0.006, by + H * 0.012), H * 0.024, P["iron"], n=5, a0=50, a1=130))
    # the ledger under his right arm, seen by its fore-edge
    x = CX - g.sw + H * 0.002
    fig.add(Z_ARM - 1, "ledger", ledger_book(x - H * 0.02, g.chest_y + H * 0.0, x + H * 0.012, g.waist_y + H * 0.04, P["ledger"], face=False))
    f = P["face"]
    fig.add(Z_HEAD, "head", head_front(g, f, hair_mid=keeper_a_hair_front(g, f, P["hair"]), extra=spectacles_front(g, f, P["silver"])))
    for side in ("right", "left"):
        s, e, w = g.f_arm[side]
        q = frame(w, ang(e, w))
        fig.add(Z_ARM + 0.2, f"{side}-cuff", cel(smooth([q(-H * 0.05, -H * 0.031), q(0, -H * 0.032), q(0, H * 0.032), q(-H * 0.05, H * 0.031)]), P["coat"], [], s=3))


look(id="keeper_a", char="vault_keeper", letter="A", label="strongroom warden (frock coat, silver buckle, keys, ledger)",
     H=178 * CM, hr=0.19, build=dict(shoulder=0.135, waist=0.105, hip=0.104, chest=0.08, back=0.078, belly=0.022, limb=1.12),
     P=dict(face=keeper_a_face(), hair="#bdb7ae", coat="#3c3a46", sleeve="#3c3a46", shirt="#3c3a46", legs="#4a4650", shoe="#26201e",
            silver="#cdd2d8", belt="#2a2220", iron="#6b6662", ledger="#7c2f2b", linen="#ece6da"),
     side=keeper_a_side, front=keeper_a_front)


# ---- more shared pieces ----------------------------------------------------------------------

def vest_side(g, out=0.006, bottom=0.035, front_point=0.015):
    H = g.H
    o = H * out
    return [(CX + g.dchest * 0.55, g.sh_y + H * 0.008), (CX + g.dchest + g.bust + o, g.chest_y + H * 0.01), (CX + g.dchest * 0.92 + g.bust * 0.3 + g.belly * 0.6 + o, g.waist_y - H * 0.02),
            (CX + g.dchest * 0.88 + g.belly + o, g.waist_y + H * (bottom + front_point), True), (CX - g.dback * 0.9 - o, g.waist_y + H * bottom, True),
            (CX - g.dback * 0.88 - o, g.waist_y), (CX - g.dback - o, g.sh_y + H * 0.05), (CX - g.dback * 0.55, g.sh_y + H * 0.004)]


def vest_front(g, neck_v=0.08, bottom=0.035, out=0.004):
    """A waistcoat from the front: a V to ``neck_v`` below the shoulders, its
    fronts ending in points."""
    H = g.H
    o = H * out
    half = [(CX, g.sh_y + H * neck_v), (CX - H * 0.034, g.sh_y - H * 0.004), (CX - g.sw * 0.66, g.sh_y + H * 0.004), (CX - g.sw + H * 0.02, g.chest_y),
            (CX - g.ww - g.belly * 0.5 - o, g.waist_y), (CX - g.ww - g.belly * 0.5 - o, g.waist_y + H * bottom, True), (CX - H * 0.012, g.waist_y + H * (bottom + 0.022), True),
            (CX, g.waist_y + H * (bottom + 0.012), True)]
    return half + mx(list(reversed(half)))[1:-1]


def skirt_side(g, top_y, hem_y, front, back):
    H = g.H
    return [(CX + g.dchest * 0.88 + g.belly + H * 0.004, top_y), (CX + g.dchest * 0.86 + g.belly * 0.8 + H * 0.012, g.hip_y), (CX + front, hem_y - H * 0.004, True),
            (CX - back, hem_y, True), (CX - g.dback - g.seat - H * 0.016, g.hip_y + H * 0.02), (CX - g.dback * 0.9 - H * 0.004, top_y)]


def skirt_front(g, top_y, hem_y, top_w, hem_w):
    return [(CX - top_w, top_y), (CX - top_w - (hem_w - top_w) * 0.35, (top_y + hem_y) / 2), (CX - hem_w, hem_y, True), (CX + hem_w, hem_y, True),
            (CX + top_w + (hem_w - top_w) * 0.35, (top_y + hem_y) / 2), (CX + top_w, top_y)]


def belt_side(g, y, h, color, buckle, front_x, back_x, buckle_w=None):
    H = g.H
    out = cel(smooth([(back_x, y - h, True), (front_x, y - h, True), (front_x, y + h, True), (back_x, y + h, True)]), color, [], s=2)
    bw = buckle_w or H * 0.018
    out += cel(rect(front_x - bw * 0.66, y - h * 1.5, front_x + bw * 0.34, y + h * 1.5, 2), buckle,
               [line([(front_x - bw * 0.2, y - h), (front_x - bw * 0.2, y + h)], shade(buckle, 0.7), 1.2)], s=2)
    return out


def belt_front(g, y, h, half_w, color, buckle, bw=None):
    H = g.H
    bw = bw or H * 0.03
    out = cel(rect(CX - half_w, y - h, CX + half_w, y + h), color, [], s=2)
    out += cel(rect(CX - bw, y - h * 1.6, CX + bw, y + h * 1.6, 3), buckle,
               [path(rect(CX - bw * 0.5, y - h * 0.7, CX + bw * 0.5, y + h * 0.7, 1.5), color, INK, 1.4),
                line([(CX - bw * 0.8, y - h * 1.25), (CX + bw * 0.7, y - h * 1.25)], light(buckle, 0.5), 1.0)], s=2)
    return out


def chain(pts, metal):
    return [line(pts, INK, 3.2), line(pts, metal, 1.4)]


def small_key(top, a, L, metal):
    q = frame(top, a)
    out = cel(smooth([q(-2, -3.6), q(4, -4.2), q(7, 0), q(4, 4.2), q(-2, 3.6), q(-4, 0)]), metal, [ellipse(*q(1.4, 0), 1.4, 1.4, shade(metal, 0.5))], s=1.5, sw=2.0)
    out += cel(smooth([q(6, -1.5), q(L, -1.4), q(L, 1.4), q(6, 1.5)]), metal, [], s=1.0, sw=2.0)
    out += cel(smooth([q(L - 7, 1.2, True), q(L - 0.5, 1.2, True), q(L - 0.5, 5, True), q(L - 3.5, 5, True), q(L - 3.5, 3.4, True), q(L - 7, 3.4, True)]),
               metal, [], s=1.0, sw=1.8)
    return out


def padlock(c, s, metal, body):
    x, y = c
    out = [path(smooth([(x - s * 0.5, y), (x - s * 0.5, y - s * 0.6), (x, y - s * 1.0), (x + s * 0.5, y - s * 0.6), (x + s * 0.5, y)], closed=False), "none", INK, 4.2),
           path(smooth([(x - s * 0.5, y), (x - s * 0.5, y - s * 0.6), (x, y - s * 1.0), (x + s * 0.5, y - s * 0.6), (x + s * 0.5, y)], closed=False), "none", metal, 2.0)]
    out += cel(rect(x - s * 0.8, y - s * 0.1, x + s * 0.8, y + s * 1.1, 2), body, [ellipse(x, y + s * 0.4, s * 0.16, s * 0.2, INK)], s=2)
    return out


def bun_hair_side(g, hair, bun=(-0.86, 0.2, 0.15)):
    """Hair drawn back tight from the forehead to a bun high at the back."""
    cap = cap_hair_side(g, 128, 322, 0.018, [(-0.06, 0.16), (-0.2, 0.22), (-0.32, 0.33), (-0.4, 0.44), (-0.44, 0.52), (-0.54, 0.44), (-0.64, 0.6),
                                              (-0.68, 0.84)], n=16)
    sh = shade(hair, 0.78)
    items = [line([g.Q(-0.12, 0.08), g.Q(-0.4, 0.06), g.Q(-0.7, 0.18)], sh, 1.2), line([g.Q(-0.2, 0.2), g.Q(-0.5, 0.2), g.Q(-0.74, 0.3)], sh, 1.2),
             line([g.Q(-0.4, 0.36), g.Q(-0.62, 0.38), g.Q(-0.8, 0.46)], sh, 1.2), line([g.Q(-0.04, 0.03), g.Q(-0.3, -0.0)], light(hair, 0.3), 1.6)]
    out_back = cel(smooth([g.Q(bun[0] - bun[2], bun[1]), g.Q(bun[0], bun[1] - bun[2] * 1.05), g.Q(bun[0] + bun[2], bun[1]), g.Q(bun[0], bun[1] + bun[2])]),
                   hair, [line([g.Q(bun[0] - bun[2] * 0.6, bun[1] - bun[2] * 0.5), g.Q(bun[0] + bun[2] * 0.2, bun[1] + bun[2] * 0.4)], sh, 1.2)], s=4)
    return out_back, cel(cap, hair, items, s=4, sw=2.8)


def bun_hair_front(g, f, hair, bun=0.15):
    w = f.get("w", 0.37)
    sh = shade(hair, 0.78)
    back = cel(smooth([g.F(-bun, -0.02), g.F(0, -0.02 - bun * 0.9), g.F(bun, -0.02), g.F(0, 0.06)]), hair, [], s=3)
    cap = front_cap(g, f, 0.022, [(-w - 0.01, 0.46), (-w + 0.03, 0.34), (-w * 0.7, 0.18), (-0.1, 0.12), (0, 0.13), (0.1, 0.12), (w * 0.7, 0.18), (w - 0.03, 0.34),
                                  (w + 0.01, 0.46)], top=-0.03)
    items = [line([g.F(-0.05, 0.12), g.F(-0.2, 0.04), g.F(-0.3, 0.1)], sh, 1.2), line([g.F(0.05, 0.12), g.F(0.2, 0.04), g.F(0.3, 0.1)], sh, 1.2)]
    return back, cel(cap, hair, items, s=3, sw=2.8)


def beard_side(g, hair, bottom=1.12, mus=True):
    """A full beard trimmed square, ear to chin, and a moustache over the lip."""
    sh = shade(hair, 0.75)
    d = smooth([g.Q(-0.42, 0.42), g.Q(-0.34, 0.5), g.Q(-0.26, 0.64), g.Q(-0.08, 0.7), g.Q(0.02, 0.8), g.Q(0.07, 0.9), g.Q(0.06, bottom - 0.04, True),
                g.Q(-0.04, bottom, True), g.Q(-0.26, bottom - 0.08), g.Q(-0.42, 0.95), g.Q(-0.5, 0.8), g.Q(-0.46, 0.6)])
    items = [line([g.Q(-0.12, 0.82), g.Q(-0.08, 1.02)], sh, 1.1), line([g.Q(-0.28, 0.78), g.Q(-0.22, 0.98)], sh, 1.1), line([g.Q(-0.04, 0.78), g.Q(0.0, 0.96)], sh, 1.0)]
    out = cel(d, hair, items, s=4, sw=2.8)
    out.append(line([g.Q(-0.04, 0.765), g.Q(0.03, 0.765)], INK, 1.6))
    if mus:
        out += cel(smooth([g.Q(-0.1, 0.69), g.Q(0.0, 0.67), g.Q(0.06, 0.69), g.Q(0.06, 0.74), g.Q(0.0, 0.76), g.Q(-0.12, 0.76)]), hair, [], s=2, sw=2.2)
    return out


def beard_front(g, f, hair, bottom=1.12, mus=True):
    w = f.get("w", 0.37)
    sh = shade(hair, 0.75)
    d = smooth([g.F(-w + 0.02, 0.44), g.F(-w + 0.03, 0.62), g.F(-0.16, 0.7), g.F(-0.06, 0.8), g.F(0.06, 0.8), g.F(0.16, 0.7), g.F(w - 0.03, 0.62),
                g.F(w - 0.02, 0.44), g.F(w + 0.01, 0.62), g.F(w * 0.86, 0.9), g.F(w * 0.5, bottom - 0.02, True), g.F(-w * 0.5, bottom - 0.02, True), g.F(-w * 0.86, 0.9),
                g.F(-w - 0.01, 0.62)])
    items = [line([g.F(-0.12, 0.86), g.F(-0.1, 1.04)], sh, 1.1), line([g.F(0.12, 0.86), g.F(0.1, 1.04)], sh, 1.1), line([g.F(0.0, 0.88), g.F(0.0, 1.06)], sh, 1.0)]
    out = cel(d, hair, items, s=4, sw=2.8)
    if mus:
        out += cel(smooth([g.F(-0.15, 0.73), g.F(-0.06, 0.67), g.F(0, 0.69), g.F(0.06, 0.67), g.F(0.15, 0.73), g.F(0.1, 0.76), g.F(0, 0.735), g.F(-0.1, 0.76)]),
                   hair, [], s=2, sw=2.2)
    out += [path(smooth([g.F(-0.07, 0.765), g.F(0.07, 0.765), g.F(0.05, 0.8), g.F(-0.05, 0.8)]), f.get("lipc", shade(f["skin"], 0.86)), INK, 1.3)]
    return out


def visor_side(g, color="#3f8f5a"):
    """A clerk's green eyeshade: the band round the head, the brim jutting from the forehead."""
    band = [line([g.Q(-0.02, 0.24), g.Q(-0.4, 0.18), g.Q(-0.75, 0.24), g.Q(-0.92, 0.36)], INK, 5.2),
            line([g.Q(-0.02, 0.24), g.Q(-0.4, 0.18), g.Q(-0.75, 0.24), g.Q(-0.92, 0.36)], shade(color, 0.6), 2.6)]
    brim = smooth([g.Q(-0.08, 0.2, True), g.Q(0.12, 0.25), g.Q(0.3, 0.33, True), g.Q(0.27, 0.36, True), g.Q(0.04, 0.33), g.Q(-0.1, 0.3, True)])
    return band + [path(brim, color, extra=' opacity="0.82"'), path(brim, "none", INK, 2.6),
                   line([g.Q(-0.06, 0.255), g.Q(0.12, 0.29), g.Q(0.26, 0.335)], light(color, 0.45), 1.2)]


def visor_front(g, f, color="#3f8f5a"):
    w = f.get("w", 0.37)
    d = smooth([g.F(-w - 0.01, 0.24, True), g.F(0, 0.2), g.F(w + 0.01, 0.24, True), g.F(w + 0.1, 0.36, True), g.F(0, 0.345), g.F(-w - 0.1, 0.36, True)])
    return [path(d, color, extra=' opacity="0.82"'), path(d, "none", INK, 2.6), line([g.F(-w + 0.02, 0.255), g.F(0, 0.225), g.F(w - 0.02, 0.255)], light(color, 0.45), 1.2)]


def pencil(a, b, wood="#e7b84a"):
    q = frame(a, ang(a, b))
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    out = cel(smooth([q(0, -2.2, True), q(L - 6, -2.2, True), q(L, 0, True), q(L - 6, 2.2, True), q(0, 2.2, True)]), wood, [], s=1, sw=2.0)
    out += [path(smooth([q(L - 6, -2.2, True), q(L, 0, True), q(L - 6, 2.2, True)]), "#e8cfa4", INK, 1.2), ellipse(*q(L - 1.2, 0), 1.0, 0.9, INK)]
    return out


def staff(x, y_top, y_bot, wood, metal, head="key", w=3.4):
    """A tall staff; ``head`` 'key': its top a key's bow (a ring) and the bit a
    little below it, so the staff is a giant vault key."""
    out = cel(rect(x - w, y_top + 22, x + w, y_bot), wood, [line([(x + 1, y_top + 40), (x + 1, y_bot - 4)], light(wood, 0.3), 1.0)], s=2)
    if head == "key":
        out += [ellipse(x, y_top + 10, 13, 13, INK), ellipse(x, y_top + 10, 9.6, 9.6, metal), ellipse(x, y_top + 10, 5.2, 5.2, INK),
                ellipse(x, y_top + 10, 2.6, 2.6, light(metal, 0.4))]
        out += cel(rect(x - 6, y_top + 21, x + 6, y_top + 30, 2), metal, [], s=1.5)
        bit = smooth([(x + 4, y_top + 36, True), (x + 20, y_top + 36, True), (x + 20, y_top + 46, True), (x + 14, y_top + 46, True), (x + 14, y_top + 51, True),
                      (x + 20, y_top + 51, True), (x + 20, y_top + 60, True), (x + 4, y_top + 60, True)])
        out += cel(bit, metal, [], s=2)
        out += cel(rect(x - 4.4, y_top + 30, x + 4.4, y_top + 64, 1.5), metal, [], s=1.5)
    return out


def dial(c, r, metal, face="#2b2a30"):
    """A combination dial: a silver ring of ticks round a dark face, a knob."""
    x, y = c
    out = cel(smooth([(x + r * math.cos(a), y + r * math.sin(a)) for a in [i * math.pi / 8 for i in range(16)]]), metal, [], s=2.5)
    out.append(ellipse(x, y, r * 0.66, r * 0.66, face, INK, 1.4))
    for i in range(12):
        a = i * math.pi / 6
        out.append(line([(x + r * 0.72 * math.cos(a), y + r * 0.72 * math.sin(a)), (x + r * 0.9 * math.cos(a), y + r * 0.9 * math.sin(a))], INK, 1.2))
    out += [ellipse(x, y, r * 0.3, r * 0.3, metal, INK, 1.4), line([(x, y - r * 0.3), (x, y - r * 0.6)], light(metal, 0.3), 1.6)]
    return out


# ---- the Vault Keeper, B: the clerk ----------------------------------------------------------

def keeper_b_face():
    return dict(skin="#b47b5c", nose=0.125, hook=0.006, droop=0.0, brow=0.015, lip=0.028, chin=0.02, w=0.35, jaw=0.76, chinw=0.34, cheek=1.0,
                brow_th=2.2, brow_c="#2a1f1c", brow_tilt=-0.6, age=1, lashes=1, iris="#3a2a20", nose_w=0.068, mouth_w=0.095, lipc="#8e5048")


def keeper_b_side(fig):
    L, g = fig.L, fig.g
    P = L["P"]
    H = g.H
    body_side(fig, P)
    # the skirt, waist to ankle
    hem = g.ankle_y - H * 0.002
    fig.add(Z_COAT, "skirt", cel(smooth(skirt_side(g, g.waist_y - H * 0.012, hem, H * 0.086, H * 0.104)), P["skirt"],
                                 [line([(CX + H * 0.01, g.hip_y), (CX + H * 0.03, hem - 3)], shade(P["skirt"], 0.7), 1.4),
                                  line([(CX - H * 0.04, g.hip_y + H * 0.02), (CX - H * 0.06, hem - 3)], shade(P["skirt"], 0.7), 1.4)], s=7))
    fig.add(Z_VEST, "waistcoat", cel(smooth(vest_side(g, bottom=0.02, front_point=0.012)), P["vest"],
                                     buttons([(CX + g.dchest + g.bust - H * 0.004, g.chest_y + H * 0.03), (CX + g.dchest * 0.92 + H * 0.002, g.waist_y - H * 0.012)], 2.0, P["silver"]),
                                     s=6))
    # the high collar of the blouse, a cameo at the throat
    fig.add(Z_NECK + 1, "collar", cel(smooth([(CX - H * 0.036, g.chin - H * 0.004), (CX + H * 0.032, g.chin + H * 0.006), (CX + H * 0.036, g.chin + H * 0.034),
                                              (CX - H * 0.036, g.sh_y + H * 0.004)]), P["shirt"], [line([(CX - H * 0.03, g.chin + H * 0.012), (CX + H * 0.03, g.chin + H * 0.02)], shade(P["shirt"], 0.8), 1.0)], s=3))
    by = g.waist_y - H * 0.004
    fig.add(Z_BELT, "belt", belt_side(g, by, H * 0.011, P["belt"], P["silver"], CX + g.dchest * 0.9 + H * 0.016, CX - g.dback * 0.9 - H * 0.008))
    # the chatelaine: chains from the belt to her keys and a padlock
    cx0 = CX + H * 0.02
    for dx, L2, kind in ((-6, 0.06, "key"), (0, 0.085, "lock"), (6, 0.07, "key")):
        end = (cx0 + dx * 1.4, by + H * L2)
        fig.add(Z_BELT + 0.1, "chatelaine", chain([(cx0 + dx * 0.3, by + 4), end], P["silver"]))
        if kind == "key":
            fig.add(Z_BELT + 0.2, "chatelaine-key", small_key(end, math.pi / 2, H * 0.06, P["silver"]))
        else:
            fig.add(Z_BELT + 0.2, "padlock", padlock((end[0], end[1] + 7), 9, P["silver"], P["brass"]))
    # sleeve garters round the upper arms
    for side in ("near", "far"):
        s, e, w = g.s_arm[side]
        m = lerp(s, e, 0.55)
        q = frame(m, ang(s, e))
        c = P["garter"] if side == "near" else shade(P["garter"], 0.84)
        fig.add((Z_ARM if side == "near" else Z_FARARM) + 0.05, f"{side}-garter", cel(smooth([q(-3.5, -H * 0.033), q(3.5, -H * 0.033), q(3.5, H * 0.033), q(-3.5, H * 0.033)]), c, [], s=1.5, sw=2.4))
        qc = frame(w, ang(e, w))
        c = P["shirt"] if side == "near" else shade(P["shirt"], 0.86)
        fig.add((Z_ARM if side == "near" else Z_FARARM) + 0.2, f"{side}-cuff", cel(smooth([qc(-H * 0.03, -H * 0.026), qc(0, -H * 0.026), qc(0, H * 0.026), qc(-H * 0.03, H * 0.026)]),
                                                                                  c, [], s=2))
    # the ledger, carried by its top edge in her near hand
    s, e, w = g.s_arm["near"]
    bx0, by0 = w[0] - H * 0.06, w[1] + H * 0.035
    fig.add(Z_ARM + 0.25, "ledger", ledger_book(bx0, by0, bx0 + H * 0.13, by0 + H * 0.165, P["ledger"], strap=P["belt"]))
    fig.add(Z_ARM + 0.3, "near-hand", hand_side((w[0] + 2, w[1] - 2), math.pi / 2 - 0.05, H * 0.085, P["face"]["skin"], grip=True))
    f = P["face"]
    back, cap = bun_hair_side(g, P["hair"])
    extra = visor_side(g, P["visor"]) + [ellipse(*g.Q(-0.52, 0.72), 2.4, 2.4, P["silver"], INK, 1.2)]
    extra += pencil(g.Q(-0.66, 0.36), g.Q(-0.36, 0.53))
    fig.add(Z_HEAD, "head", head_side(g, f, hair_back=back, hair_mid=cap, extra=extra))


def keeper_b_front(fig):
    L, g = fig.L, fig.g
    P = L["P"]
    H = g.H
    body_front(fig, P)
    hem = g.ankle_y - H * 0.002
    fig.add(Z_COAT, "skirt", cel(smooth(skirt_front(g, g.waist_y - H * 0.012, hem, g.ww + H * 0.012, g.hw + H * 0.06)), P["skirt"],
                                 [line([(CX - H * 0.03, g.hip_y), (CX - H * 0.05, hem - 3)], shade(P["skirt"], 0.7), 1.4),
                                  line([(CX + H * 0.03, g.hip_y), (CX + H * 0.05, hem - 3)], shade(P["skirt"], 0.7), 1.4)], s=7))
    fig.add(Z_VEST, "waistcoat", cel(smooth(vest_front(g, neck_v=0.07, bottom=0.02)), P["vest"],
                                     buttons([(CX - H * 0.008, y) for y in (g.chest_y + H * 0.012, g.chest_y + H * 0.04, g.waist_y)], 2.0, P["silver"]), s=6))
    fig.add(Z_VEST - 0.5, "blouse-front", [line([(CX, g.sh_y + H * 0.01), (CX, g.sh_y + H * 0.07)], shade(P["shirt"], 0.8), 1.2)])
    fig.add(Z_NECK + 1, "collar", cel(smooth([(CX - H * 0.036, g.chin - H * 0.01), (CX + H * 0.036, g.chin - H * 0.01), (CX + H * 0.04, g.sh_y + H * 0.004),
                                              (CX - H * 0.04, g.sh_y + H * 0.004)]), P["shirt"], [], s=3) + cel(rect(CX - 4, g.chin + H * 0.012, CX + 4, g.chin + H * 0.03, 3), P["brass"], [], s=1, sw=1.8))
    by = g.waist_y - H * 0.004
    fig.add(Z_BELT, "belt", belt_front(g, by, H * 0.011, g.ww + H * 0.014, P["belt"], P["silver"], bw=H * 0.022))
    cx0 = CX + g.ww * 0.6
    for dx, L2, kind in ((-7, 0.06, "key"), (0, 0.085, "lock"), (7, 0.07, "key")):
        end = (cx0 + dx * 1.4, by + H * L2)
        fig.add(Z_BELT + 0.1, "chatelaine", chain([(cx0 + dx * 0.3, by + 4), end], P["silver"]))
        if kind == "key":
            fig.add(Z_BELT + 0.2, "chatelaine-key", small_key(end, math.pi / 2, H * 0.06, P["silver"]))
        else:
            fig.add(Z_BELT + 0.2, "padlock", padlock((end[0], end[1] + 7), 9, P["silver"], P["brass"]))
    for side in ("right", "left"):
        s, e, w = g.f_arm[side]
        m = lerp(s, e, 0.55)
        q = frame(m, ang(s, e))
        fig.add(Z_ARM + 0.05, f"{side}-garter", cel(smooth([q(-3.5, -H * 0.033), q(3.5, -H * 0.033), q(3.5, H * 0.033), q(-3.5, H * 0.033)]), P["garter"], [], s=1.5, sw=2.4))
        qc = frame(w, ang(e, w))
        fig.add(Z_ARM + 0.2, f"{side}-cuff", cel(smooth([qc(-H * 0.03, -H * 0.026), qc(0, -H * 0.026), qc(0, H * 0.026), qc(-H * 0.03, H * 0.026)]), P["shirt"], [], s=2))
    # the ledger in her right hand, seen by its spine
    s, e, w = g.f_arm["right"]
    fig.add(Z_HAND - 0.1, "ledger", ledger_book(w[0] - H * 0.022, w[1] + H * 0.03, w[0] + H * 0.022, w[1] + H * 0.195, P["ledger"], face=False))
    f = P["face"]
    back, cap = bun_hair_front(g, f, P["hair"])
    extra = visor_front(g, f, P["visor"]) + [ellipse(*g.F(-f["w"] - 0.06, 0.68), 2.4, 2.4, P["silver"], INK, 1.2), ellipse(*g.F(f["w"] + 0.06, 0.68), 2.4, 2.4, P["silver"], INK, 1.2)]
    extra += pencil(g.F(f["w"] + 0.02, 0.3), g.F(f["w"] + 0.1, 0.56))
    fig.add(Z_HEAD, "head", head_front(g, f, hair_back=back, hair_mid=cap, extra=extra))


look(id="keeper_b", char="vault_keeper", letter="B", label="ledger clerk (eyeshade, chatelaine of keys, ledger in hand)",
     H=178 * CM, hr=0.185, build=dict(shoulder=0.11, waist=0.07, hip=0.096, chest=0.062, back=0.064, bust=0.012, seat=0.008, limb=0.9, neck=0.062),
     P=dict(face=keeper_b_face(), hair="#2b201d", shirt="#ebe5d8", sleeve="#ebe5d8", legs="#2e2b33", shoe="#2a201c", shoe_kind="boot", no_legs=True,
            skirt="#2f3340", vest="#5b2f45", silver="#cdd2d8", brass="#c9a24a", belt="#231c1c", garter="#6e2240", ledger="#2f5a52", visor="#3f8f5a",
            hand_held={"near": True}),
     side=keeper_b_side, front=keeper_b_front)


# ---- the Vault Keeper, C: the keeper of the vault, robed, with the vault staff ----------------

def keeper_c_face():
    return dict(skin="#c3916a", nose=0.15, hook=0.03, droop=0.006, brow=0.04, lip=0.016, chin=0.02, w=0.385, jaw=0.88, chinw=0.44, cheek=1.0,
                brow_th=3.8, brow_c="#2a211d", brow_tilt=0.8, age=1, lids=1, iris="#2e2620", nose_w=0.08, mouth_w=0.1)


def keeper_c_pose(g):
    H = g.H
    s, e, w = g.s_arm["near"]
    g.s_arm["near"] = (s, (CX + H * 0.004, g.waist_y - H * 0.012), (CX + H * 0.1, g.waist_y - H * 0.03))
    s, e, w = g.f_arm["right"]
    g.f_arm["right"] = (s, (CX - g.sw - H * 0.014, g.waist_y - H * 0.0), (CX - g.sw - H * 0.03, g.waist_y + H * 0.06))


def robe_trim(pts, color, w=4.0):
    return [line(pts, INK, w + 3.4), line(pts, color, w)]


def keeper_c_side(fig):
    L, g = fig.L, fig.g
    P = L["P"]
    H = g.H
    body_side(fig, P)
    hem = g.ankle_y + H * 0.006
    # the robe: one long garment from the throat to the ankle, a little flared
    d = smooth(coat_side(g, g.chin + H * 0.02, H * 0.012, hem, H * 0.088, H * 0.11, flare=H * 0.01))
    items = [line([(CX - H * 0.01, g.waist_y + H * 0.03), (CX - H * 0.03, hem - 4)], shade(P["robe"], 0.72), 1.5),
             line([(CX + H * 0.04, g.hip_y), (CX + H * 0.06, hem - 4)], shade(P["robe"], 0.72), 1.3)]
    items += robe_trim([(CX - H * 0.12, hem - 6), (CX + H * 0.1, hem - 7)], P["gold"], 5)
    fig.add(Z_COAT, "robe", cel(d, P["robe"], items, s=8))
    # the stole hanging down the front, a key worked in gold near its end
    fx = CX + g.dchest * 0.86
    stole = smooth([(CX + H * 0.03, g.chin + H * 0.03), (fx + H * 0.018, g.chest_y), (fx + g.belly + H * 0.02, g.waist_y + H * 0.03),
                    (CX + H * 0.092, g.knee_y + H * 0.03, True), (CX + H * 0.05, g.knee_y + H * 0.034, True), (fx - H * 0.02 + g.belly, g.waist_y + H * 0.03),
                    (fx - H * 0.03, g.chest_y), (CX + H * 0.0, g.chin + H * 0.03)])
    fig.add(Z_APRON, "stole", cel(stole, P["stole"], [line([(CX + H * 0.06, g.knee_y - H * 0.02), (CX + H * 0.08, g.knee_y + H * 0.02)], P["gold"], 2.6),
                                                     ellipse(CX + H * 0.058, g.knee_y - H * 0.028, 3.2, 3.2, "none", P["gold"], 1.8)], s=4))
    # the hood, down, lying in folds over the back of the shoulders
    hood = smooth([(CX - H * 0.03, g.chin - H * 0.01), (CX - H * 0.075, g.chin - H * 0.005), (CX - H * 0.105, g.sh_y + H * 0.02), (CX - H * 0.1, g.sh_y + H * 0.065),
                   (CX - H * 0.07, g.sh_y + H * 0.08), (CX - H * 0.05, g.sh_y + H * 0.04), (CX - H * 0.01, g.sh_y + H * 0.01)])
    fig.add(Z_NECK + 0.6, "hood", cel(hood, P["robe"], [line([(CX - H * 0.08, g.sh_y), (CX - H * 0.07, g.sh_y + H * 0.05)], shade(P["robe"], 0.7), 1.4)], s=5))
    by = g.waist_y + H * 0.01
    fig.add(Z_BELT, "sash", belt_side(g, by, H * 0.014, P["sash"], P["silver"], CX + g.dchest * 0.94 + g.belly + H * 0.016, CX - g.dback * 0.9 - H * 0.012, buckle_w=H * 0.022))
    # the combination dial on a chain, on his chest
    fig.add(Z_BELT + 0.5, "dial", chain([(CX + H * 0.03, g.chin + H * 0.03), (CX + g.dchest + H * 0.012, g.chest_y + H * 0.004)], P["silver"])
            + dial((CX + g.dchest + H * 0.012, g.chest_y + H * 0.02), H * 0.024, P["silver"]))
    # the vault staff in his near hand
    s, e, w = g.s_arm["near"]
    sx = w[0] + H * 0.06
    fig.add(Z_ARM - 0.5, "staff", staff(sx, g.crown - H * 0.07, GROUND - 1, P["wood"], P["silver"]))
    fig.add(Z_HAND, "near-hand", hand_side(w, ang(e, w), H * 0.085, P["face"]["skin"], grip=True))
    for side in ("near", "far"):
        s, e, w = g.s_arm[side]
        q = frame(w, ang(e, w))
        c = P["robe"] if side == "near" else shade(P["robe"], 0.84)
        sleeve = smooth([q(-H * 0.07, -H * 0.034), q(H * 0.004, -H * 0.044), q(H * 0.008, H * 0.05), q(-H * 0.07, H * 0.036)])
        fig.add((Z_ARM if side == "near" else Z_FARARM) + 0.2, f"{side}-cuff", cel(sleeve, c, robe_trim([q(0, -H * 0.04), q(H * 0.004, H * 0.046)], P["gold"], 3), s=3))
    f = P["face"]
    fig.add(Z_HEAD, "head", head_side(g, f, hair_front=beard_side(g, P["hair"]), extra=[ellipse(*g.Q(-0.5, 0.72), 3.0, 3.0, "none", P["gold"], 2.0)]))


def keeper_c_front(fig):
    L, g = fig.L, fig.g
    P = L["P"]
    H = g.H
    body_front(fig, P)
    hem = g.ankle_y + H * 0.006
    d = smooth(coat_front(g, g.chin + H * 0.02, H * 0.014, hem, g.hw + H * 0.06))
    items = [line([(CX - g.hw * 0.6, g.hip_y), (CX - g.hw * 0.8, hem - 3)], shade(P["robe"], 0.72), 1.4),
             line([(CX + g.hw * 0.6, g.hip_y), (CX + g.hw * 0.8, hem - 3)], shade(P["robe"], 0.72), 1.4)]
    items += robe_trim([(CX - g.hw - H * 0.07, hem - 6), (CX + g.hw + H * 0.07, hem - 6)], P["gold"], 5)
    fig.add(Z_COAT, "robe", cel(d, P["robe"], items, s=8))
    stole = smooth([(CX - H * 0.04, g.chin + H * 0.02), (CX - H * 0.026, g.waist_y), (CX - H * 0.03, g.knee_y + H * 0.03, True), (CX + H * 0.03, g.knee_y + H * 0.03, True),
                    (CX + H * 0.026, g.waist_y), (CX + H * 0.04, g.chin + H * 0.02), (CX, g.chin + H * 0.05)])
    fig.add(Z_APRON, "stole", cel(stole, P["stole"], small_key((CX, g.knee_y - H * 0.05), math.pi / 2, H * 0.06, P["gold"]), s=4))
    by = g.waist_y + H * 0.01
    fig.add(Z_BELT, "sash", belt_front(g, by, H * 0.014, g.ww + g.belly * 0.5 + H * 0.02, P["sash"], P["silver"], bw=H * 0.03))
    fig.add(Z_BELT + 0.5, "dial", chain([(CX - H * 0.04, g.chin + H * 0.02), (CX, g.chest_y), (CX + H * 0.04, g.chin + H * 0.02)], P["silver"])
            + dial((CX, g.chest_y + H * 0.02), H * 0.026, P["silver"]))
    hood = smooth([(CX - H * 0.05, g.chin + H * 0.0), (CX - H * 0.075, g.chin - H * 0.03), (CX, g.chin - H * 0.05), (CX + H * 0.075, g.chin - H * 0.03),
                   (CX + H * 0.05, g.chin + H * 0.0)])
    fig.add(Z_NECK - 3, "hood", cel(hood, shade(P["robe"], 0.8), [], s=3))
    s, e, w = g.f_arm["right"]
    fig.add(Z_ARM - 0.5, "staff", staff(w[0], g.crown - H * 0.07, GROUND - 1, P["wood"], P["silver"]))
    fig.add(Z_HAND + 0.1, "right-fist", hand_side((w[0] + 6, w[1] - 4), math.pi / 2 + 0.3, H * 0.075, P["face"]["skin"], grip=True))
    for side in ("right", "left"):
        s, e, w = g.f_arm[side]
        q = frame(w, ang(e, w))
        sleeve = smooth([q(-H * 0.07, -H * 0.034), q(H * 0.004, -H * 0.046), q(H * 0.008, H * 0.046), q(-H * 0.07, H * 0.034)])
        fig.add(Z_ARM + 0.2, f"{side}-cuff", cel(sleeve, P["robe"], robe_trim([q(0, -H * 0.042), q(H * 0.004, H * 0.042)], P["gold"], 3), s=3))
    f = P["face"]
    fig.add(Z_HEAD, "head", head_front(g, f, hair_front=beard_front(g, f, P["hair"]), extra=[ellipse(*g.F(f["w"] + 0.06, 0.7), 3.0, 3.0, "none", P["gold"], 2.0)]))


look(id="keeper_c", char="vault_keeper", letter="C", label="keeper of the vault (robe, the vault staff, a combination dial)",
     H=178 * CM, hr=0.19, build=dict(shoulder=0.13, waist=0.098, hip=0.1, chest=0.078, back=0.074, belly=0.016, limb=1.1),
     P=dict(face=keeper_c_face(), hair="#2a221e", robe="#6a2733", sleeve="#6a2733", shirt="#6a2733", legs="#3a2a2a", shoe="#2a201c", no_legs=True,
            stole="#2c2a35", gold="#d4a944", silver="#cdd2d8", sash="#2c2a35", wood="#6b4a33",
            hand_held={"near": True, "right": True}),
     pose=keeper_c_pose, side=keeper_c_side, front=keeper_c_front)


# ============================================================================================
# MERCHANT PROTOTYPE
# ============================================================================================

def stripes_v(x0, y0, x1, y1, step, color, w):
    return [line([(x, y0 - 4), (x, y1 + 4)], color, w) for x in [x0 + i * step for i in range(int((x1 - x0) / step) + 2)]]


def price_tag(top, color="#efe6cf", mark="?", s=1.0, string="#7a6a55"):
    """A paper price tag on a string, its price not yet written (a '?')."""
    x, y = top
    out = [line([(x, y), (x + 2 * s, y + 8 * s)], INK, 2.6), line([(x, y), (x + 2 * s, y + 8 * s)], string, 1.0)]
    d = smooth([(x - 3 * s, y + 8 * s, True), (x + 7 * s, y + 8 * s, True), (x + 9 * s, y + 13 * s, True), (x + 9 * s, y + 24 * s, True), (x - 5 * s, y + 24 * s, True),
                (x - 5 * s, y + 13 * s, True)])
    out += cel(d, color, [], s=1.5, sw=2.0)
    out.append(ellipse(x + 2 * s, y + 11 * s, 1.2 * s, 1.2 * s, INK))
    if mark:
        out.append(f'<text x="{svg.f(x + 2 * s)}" y="{svg.f(y + 22.5 * s)}" font-family="DejaVu Sans, sans-serif" font-weight="bold" font-size="{svg.f(9 * s)}" '
                   f'text-anchor="middle" fill="{INK}">{mark}</text>')
    return out


def pouch(c, s, leather, tie="#c9a24a"):
    x, y = c
    d = smooth([(x - s * 0.5, y), (x + s * 0.5, y), (x + s * 0.75, y + s * 0.7), (x + s * 0.5, y + s * 1.15), (x - s * 0.5, y + s * 1.15), (x - s * 0.75, y + s * 0.7)])
    out = cel(d, leather, [line([(x - s * 0.55, y + s * 0.2), (x + s * 0.55, y + s * 0.2)], shade(leather, 0.65), 1.4)], s=3)
    out += [ellipse(x + s * 0.15, y + s * 0.2, s * 0.12, s * 0.12, tie, INK, 1.2)]
    out += [line([(x + s * 0.15, y + s * 0.25), (x + s * 0.05, y + s * 0.55)], INK, 2.6), line([(x + s * 0.15, y + s * 0.25), (x + s * 0.05, y + s * 0.55)], tie, 1.2)]
    return out


def coin(c, r, gold="#e0b84a"):
    return [ellipse(c[0], c[1], r, r, gold, INK, 1.6), ellipse(c[0], c[1], r * 0.55, r * 0.55, "none", shade(gold, 0.7), 1.0)]


def mustache_side(g, hair, big=1.0):
    return cel(smooth([g.Q(-0.12, 0.665), g.Q(0.0, 0.655), g.Q(0.07 * big, 0.68), g.Q(0.08 * big, 0.74), g.Q(0.03, 0.76), g.Q(-0.04, 0.745), g.Q(-0.13, 0.73)]),
               hair, [line([g.Q(-0.06, 0.68), g.Q(0.03, 0.73)], shade(hair, 0.7), 1.0)], s=2, sw=2.4)


def mustache_front(g, hair, big=1.0, thin=False):
    if thin:
        return [line([g.F(-0.1, 0.725), g.F(-0.03, 0.705), g.F(0.03, 0.705), g.F(0.1, 0.725)], INK, 4.2), line([g.F(-0.095, 0.723), g.F(-0.03, 0.705), g.F(0.03, 0.705),
                                                                                                                    g.F(0.095, 0.723)], hair, 2.0)]
    d = smooth([g.F(-0.16 * big, 0.75), g.F(-0.1, 0.67), g.F(0, 0.665), g.F(0.1, 0.67), g.F(0.16 * big, 0.75), g.F(0.1, 0.745), g.F(0.0, 0.725), g.F(-0.1, 0.745)])
    return cel(d, hair, [line([g.F(-0.06, 0.69), g.F(-0.1, 0.73)], shade(hair, 0.7), 1.0), line([g.F(0.06, 0.69), g.F(0.1, 0.73)], shade(hair, 0.7), 1.0)], s=2, sw=2.4)


# ---- A: the market trader ----------------------------------------------------------------

def merchant_a_face():
    return dict(skin="#dba887", nose=0.15, hook=0.0, droop=0.025, brow=0.025, lip=0.02, chin=0.0, jaw_drop=0.04, w=0.4, jaw=0.95, chinw=0.5, cheek=1.04,
                brow_th=3.4, brow_c="#2a201c", brow_tilt=0.4, age=1, iris="#3a2a20", nose_w=0.09, mouth_w=0.1, stubble="#7a6458")


def flat_cap_side(g, cloth, t=0.05):
    sh = shade(cloth, 0.75)
    crown = smooth([cran(g, 160, t), cran(g, 200, t + 0.02), cran(g, 240, t + 0.04), cran(g, 275, t + 0.05), cran(g, 305, t + 0.03), g.Q(0.03, 0.17),
                    g.Q(0.05, 0.22, True), g.Q(-0.2, 0.27), g.Q(-0.5, 0.33), g.Q(-0.76, 0.42), g.Q(-0.92, 0.46, True)])
    out = cel(crown, cloth, [line([g.Q(-0.4, 0.04), g.Q(-0.1, 0.16)], sh, 1.2), line([g.Q(-0.72, 0.2), g.Q(-0.5, 0.26)], sh, 1.0)], s=5)
    out += [ellipse(*g.Q(-0.2, -0.02), 2.6, 1.6, sh, INK, 1.2)]
    brim = smooth([g.Q(-0.02, 0.2, True), g.Q(0.12, 0.23), g.Q(0.2, 0.27, True), g.Q(0.12, 0.29), g.Q(-0.02, 0.28, True)])
    return out + cel(brim, sh, [], s=2)


def flat_cap_front(g, f, cloth):
    w = f.get("w", 0.37)
    sh = shade(cloth, 0.75)
    crown = smooth([g.F(-w - 0.06, 0.28, True), g.F(-w - 0.04, 0.14), g.F(-w * 0.6, 0.0), g.F(0, -0.05), g.F(w * 0.6, 0.0), g.F(w + 0.06, 0.12), g.F(w + 0.08, 0.26, True),
                    g.F(0, 0.22)])
    out = cel(crown, cloth, [line([g.F(-0.05, 0.0), g.F(-0.02, 0.2)], sh, 1.2)], s=5)
    brim = smooth([g.F(-w + 0.02, 0.24, True), g.F(0, 0.2), g.F(w - 0.02, 0.24, True), g.F(w - 0.06, 0.3), g.F(0, 0.31), g.F(-w + 0.06, 0.3)])
    return out + cel(brim, sh, [], s=2)


def merchant_a_side(fig):
    L, g = fig.L, fig.g
    P = L["P"]
    H = g.H
    body_side(fig, P)
    # the striped shirt: re-draw the torso with its stripes
    fig.layers = [ly for ly in fig.layers if ly[1] != "torso"]
    fig.add(Z_TORSO, "torso", cel(smooth(side_torso_pts(g)), P["shirt"], stripes_v(CX - H * 0.12, g.chin, CX + H * 0.16, g.crotch_y, 7, P["stripe"], 1.6), s=6))
    # the waistcoat, open over the belly
    fig.add(Z_VEST, "waistcoat", cel(smooth(vest_side(g, bottom=0.03, front_point=0.0)), P["vest"], [], s=6))
    # the long canvas apron, chest to knee, over the belly
    fx = CX + g.dchest * 0.86 + g.belly
    ap = smooth([(CX + g.dchest * 0.7, g.chest_y - H * 0.03), (CX + g.dchest + H * 0.012, g.chest_y), (fx + H * 0.016, g.waist_y + H * 0.03),
                 (CX + g.dchest * 0.86 + g.belly * 0.8 + H * 0.014, g.hip_y), (CX + H * 0.09, g.knee_y + H * 0.02, True), (CX + H * 0.0, g.knee_y + H * 0.02, True),
                 (CX + H * 0.03, g.hip_y), (CX + H * 0.05, g.waist_y), (CX + g.dchest * 0.5, g.chest_y - H * 0.024)])
    pocket = smooth([(CX + H * 0.04, g.hip_y - H * 0.01, True), (fx + H * 0.012, g.hip_y - H * 0.012, True), (CX + H * 0.098, g.hip_y + H * 0.05, True),
                     (CX + H * 0.04, g.hip_y + H * 0.05, True)])
    items = [path(pocket, shade(P["apron"], 0.88), INK, 1.6), line([(CX + H * 0.06, g.hip_y + H * 0.06), (CX + H * 0.07, g.knee_y + H * 0.01)], shade(P["apron"], 0.75), 1.3)]
    fig.add(Z_APRON, "apron", cel(ap, P["apron"], items, s=5))
    fig.add(Z_APRON + 0.2, "pocket-coins", coin((CX + H * 0.075, g.hip_y - H * 0.016), 4.0) + pencil((CX + H * 0.05, g.hip_y + H * 0.004), (CX + H * 0.064, g.hip_y - H * 0.05)))
    fig.add(Z_APRON + 0.3, "apron-strings", [line([(CX + g.dchest * 0.6, g.chest_y - H * 0.028), (CX + H * 0.01, g.chin + H * 0.03)], INK, 4.4),
                                             line([(CX + g.dchest * 0.6, g.chest_y - H * 0.028), (CX + H * 0.01, g.chin + H * 0.03)], P["apron"], 2.0),
                                             line([(CX + H * 0.04, g.waist_y + H * 0.005), (CX - g.dback - H * 0.004, g.waist_y + H * 0.01)], INK, 4.4),
                                             line([(CX + H * 0.04, g.waist_y + H * 0.005), (CX - g.dback - H * 0.004, g.waist_y + H * 0.01)], P["apron"], 2.0)])
    fig.add(Z_APRON + 0.4, "tag", price_tag((CX + H * 0.03, g.waist_y + H * 0.01), s=1.15))
    fig.add(Z_BELT, "purse", pouch((CX - H * 0.06, g.waist_y + H * 0.02), H * 0.05, P["leather"]))
    f = P["face"]
    hair = cel(cap_hair_side(g, 120, 175, 0.03, [(-0.86, 0.42), (-0.7, 0.42), (-0.6, 0.47), (-0.64, 0.66), (-0.66, 0.84)]), P["hair"], [], s=3, sw=2.6)
    fig.add(Z_HEAD, "head", head_side(g, f, hair_mid=hair, hair_front=mustache_side(g, P["hair"], 1.1) + flat_cap_side(g, P["cap"])
                                      + pencil(g.Q(-0.64, 0.38), g.Q(-0.34, 0.5))))


def merchant_a_front(fig):
    L, g = fig.L, fig.g
    P = L["P"]
    H = g.H
    body_front(fig, P)
    fig.layers = [ly for ly in fig.layers if ly[1] != "torso"]
    fig.add(Z_TORSO, "torso", cel(smooth(front_torso_pts(g)), P["shirt"], stripes_v(CX - g.sw - 6, g.chin, CX + g.sw + 6, g.crotch_y, 7, P["stripe"], 1.6), s=6))
    # the waistcoat hangs open either side of the apron
    for sgn in (-1, 1):
        half = [(CX + sgn * H * 0.034, g.sh_y - H * 0.004), (CX + sgn * g.sw * 0.66, g.sh_y + H * 0.004), (CX + sgn * (g.sw - H * 0.02), g.chest_y),
                (CX + sgn * (g.ww + g.belly * 0.5 + H * 0.006), g.waist_y), (CX + sgn * (g.ww + g.belly * 0.5 + H * 0.004), g.waist_y + H * 0.034, True),
                (CX + sgn * (g.ww * 0.6), g.waist_y + H * 0.036, True), (CX + sgn * H * 0.05, g.chest_y)]
        fig.add(Z_VEST, "waistcoat", cel(smooth(half), P["vest"], [], s=5))
    bib = smooth([(CX - H * 0.05, g.chest_y - H * 0.03, True), (CX + H * 0.05, g.chest_y - H * 0.03, True), (CX + H * 0.056, g.waist_y - H * 0.0),
                  (CX + g.ww + g.belly * 0.5 + H * 0.004, g.waist_y + H * 0.008), (CX + g.hw + H * 0.006, g.knee_y + H * 0.02, True),
                  (CX - g.hw - H * 0.006, g.knee_y + H * 0.02, True), (CX - g.ww - g.belly * 0.5 - H * 0.004, g.waist_y + H * 0.008), (CX - H * 0.056, g.waist_y)])
    pocket = smooth([(CX - H * 0.07, g.hip_y - H * 0.012, True), (CX + H * 0.07, g.hip_y - H * 0.012, True), (CX + H * 0.068, g.hip_y + H * 0.05, True),
                     (CX - H * 0.068, g.hip_y + H * 0.05, True)])
    items = [path(pocket, shade(P["apron"], 0.88), INK, 1.6), line([(CX, g.hip_y - H * 0.012), (CX, g.hip_y + H * 0.05)], INK, 1.4),
             line([(CX - H * 0.05, g.hip_y + H * 0.06), (CX - H * 0.06, g.knee_y + H * 0.01)], shade(P["apron"], 0.75), 1.3),
             line([(CX + H * 0.05, g.hip_y + H * 0.06), (CX + H * 0.06, g.knee_y + H * 0.01)], shade(P["apron"], 0.75), 1.3)]
    fig.add(Z_APRON, "apron", cel(bib, P["apron"], items, s=5))
    fig.add(Z_APRON + 0.2, "pocket-coins", coin((CX - H * 0.04, g.hip_y - H * 0.016), 4.0) + coin((CX - H * 0.026, g.hip_y - H * 0.02), 4.0)
            + pencil((CX + H * 0.03, g.hip_y + H * 0.004), (CX + H * 0.045, g.hip_y - H * 0.05)))
    for sgn in (-1, 1):
        fig.add(Z_APRON + 0.3, "apron-strings", [line([(CX + sgn * H * 0.045, g.chest_y - H * 0.028), (CX + sgn * H * 0.034, g.chin + H * 0.012)], INK, 4.4),
                                                 line([(CX + sgn * H * 0.045, g.chest_y - H * 0.028), (CX + sgn * H * 0.034, g.chin + H * 0.012)], P["apron"], 2.0)])
    fig.add(Z_APRON + 0.4, "tag", price_tag((CX + g.ww + g.belly * 0.5 - H * 0.004, g.waist_y + H * 0.01), s=1.15))
    fig.add(Z_ARM - 0.3, "purse", pouch((CX - g.ww - g.belly * 0.5 - H * 0.03, g.waist_y + H * 0.02), H * 0.05, P["leather"]))
    f = P["face"]
    w = f["w"]
    hair = []
    for sgn in (-1, 1):
        hair += cel(smooth([g.F(sgn * (w - 0.02), 0.24), g.F(sgn * (w + 0.04), 0.3), g.F(sgn * (w + 0.03), 0.44), g.F(sgn * (w - 0.04), 0.44)]), P["hair"], [], s=2, sw=2.4)
    fig.add(Z_HEAD, "head", head_front(g, f, hair_mid=hair, hair_front=mustache_front(g, P["hair"], 1.15) + flat_cap_front(g, f, P["cap"])
                                       + pencil(g.F(w + 0.02, 0.3), g.F(w + 0.1, 0.56))))


look(id="merchant_a", char="merchant_prototype", letter="A", label="market trader (flat cap, canvas apron, coin purse, blank price tag)",
     H=168 * CM, hr=0.2, build=dict(shoulder=0.12, waist=0.112, hip=0.112, chest=0.078, back=0.072, belly=0.075, limb=1.14, stance=0.056),
     P=dict(face=merchant_a_face(), hair="#2b221e", cap="#6a5e52", shirt="#e8e4da", stripe="#7d93b4", sleeve="#e8e4da", bare_forearm=True, vest="#4b4a55",
            apron="#c9b48a", legs="#5d4636", shoe="#2e231d", shoe_kind="boot", boot_top=None, leather="#7a5236"),
     side=merchant_a_side, front=merchant_a_front)


# ---- B: the travelling pedlar, her whole shop on her back ------------------------------------

def merchant_b_face():
    return dict(skin="#8c5a3e", nose=0.14, hook=0.012, droop=0.01, brow=0.02, lip=0.03, chin=0.02, w=0.38, jaw=0.86, chinw=0.42, cheek=1.04,
                brow_th=2.6, brow_c="#1f1714", brow_tilt=-0.4, age=2, lids=1, lashes=1, iris="#2a1e18", nose_w=0.088, mouth_w=0.1, lipc="#6e3b30")


def merchant_b_pose(g):
    H = g.H
    s, e, w = g.s_arm["near"]
    g.s_arm["near"] = (s, (CX - H * 0.02, g.waist_y - H * 0.004), (CX + g.dchest - H * 0.004, g.chest_y + H * 0.03))


def headscarf_side(g, cloth, dot="#efe6cf"):
    d = smooth([cran(g, 122, 0.035), cran(g, 160, 0.04), cran(g, 200, 0.045), cran(g, 240, 0.05), cran(g, 280, 0.045), cran(g, 312, 0.035), g.Q(0.0, 0.2),
                g.Q(-0.12, 0.22), g.Q(-0.34, 0.32), g.Q(-0.46, 0.4), g.Q(-0.62, 0.56), g.Q(-0.68, 0.76)])
    dots = [ellipse(*g.Q(u, v), 1.6, 1.6, dot) for u, v in ((-0.2, 0.05), (-0.4, 0.02), (-0.6, 0.08), (-0.3, 0.16), (-0.5, 0.15), (-0.72, 0.18), (-0.8, 0.32),
                                                            (-0.62, 0.3), (-0.84, 0.5), (-0.72, 0.45))]
    out = cel(d, cloth, dots + [line([g.Q(-0.1, 0.15), g.Q(-0.5, 0.25), g.Q(-0.8, 0.55)], shade(cloth, 0.75), 1.2)], s=5)
    knot = smooth([g.Q(-0.82, 0.72), g.Q(-0.7, 0.7), g.Q(-0.7, 0.82), g.Q(-0.82, 0.84)])
    tails = smooth([g.Q(-0.8, 0.78), g.Q(-0.92, 0.88), g.Q(-1.02, 1.1, True), g.Q(-0.9, 1.06), g.Q(-0.84, 1.18, True), g.Q(-0.74, 0.86)])
    return cel(tails, shade(cloth, 0.9), [], s=2.5) + out + cel(knot, cloth, [], s=2)


def headscarf_front(g, f, cloth, dot="#efe6cf"):
    w = f.get("w", 0.37)
    d = smooth([g.F(-w - 0.05, 0.52), g.F(-w - 0.06, 0.24), g.F(-w * 0.6, -0.01), g.F(0, -0.05), g.F(w * 0.6, -0.01), g.F(w + 0.06, 0.24), g.F(w + 0.05, 0.52),
                g.F(w - 0.02, 0.5), g.F(w - 0.04, 0.3), g.F(w * 0.5, 0.18), g.F(0, 0.17), g.F(-w * 0.5, 0.18), g.F(-w + 0.04, 0.3), g.F(-w + 0.02, 0.5)])
    dots = [ellipse(*g.F(u, v), 1.6, 1.6, dot) for u, v in ((-0.25, 0.05), (0.0, 0.02), (0.25, 0.05), (-0.12, 0.12), (0.12, 0.12), (-0.37, 0.2), (0.37, 0.2),
                                                            (-0.4, 0.38), (0.4, 0.38))]
    return cel(d, cloth, dots, s=5)


def pack_side(g, P):
    """The pedlar's pack frame on her back and what hangs off it: the bedroll on
    top, a pot, a lantern, the shop's wares (an axe, a bomb, a health cell)."""
    H = g.H
    x0, x1 = CX - g.dback - H * 0.17, CX - g.dback + H * 0.01
    y0, y1 = g.crown + H * 0.03, g.hip_y + H * 0.02
    out = []
    # the axe, slung through the frame, its head above the bedroll
    out += cel(rect(x0 + H * 0.02, y0 - H * 0.1, x0 + H * 0.034, y1 - H * 0.02, 2), P["wood"], [], s=1.5, sw=2.6)
    axe = smooth([(x0 + H * 0.03, y0 - H * 0.1, True), (x0 - H * 0.02, y0 - H * 0.12), (x0 - H * 0.04, y0 - H * 0.08, True), (x0 - H * 0.02, y0 - H * 0.04, True),
                  (x0 + H * 0.03, y0 - H * 0.06, True)])
    out += cel(axe, P["steel"], [line([(x0 - H * 0.036, y0 - H * 0.08), (x0 - H * 0.024, y0 - H * 0.048)], light(P["steel"], 0.6), 1.6)], s=2)
    # the frame and the pack
    out += cel(rect(x0, y0 + H * 0.04, x1, y1, 8), P["pack"], [line([(x0 + 8, y0 + H * 0.12), (x1 - 4, y0 + H * 0.12)], shade(P["pack"], 0.7), 1.4),
                                                                line([(x0 + 8, y0 + H * 0.24), (x1 - 4, y0 + H * 0.24)], shade(P["pack"], 0.7), 1.4)], s=6)
    out += cel(rect(x0 - H * 0.02, y0 + H * 0.14, x0 + H * 0.04, y0 + H * 0.24, 4), shade(P["pack"], 0.92), [ellipse(x0 + H * 0.01, y0 + H * 0.16, 2.2, 2.2, P["brass"], INK, 1)], s=3)
    # the bedroll on top, seen end-on
    rx, ry = (x0 + x1) / 2, y0 + H * 0.02
    out += cel(smooth([(x0 - H * 0.01, ry - H * 0.04), (x1 + H * 0.0, ry - H * 0.045), (x1 + H * 0.01, ry + H * 0.03), (x0 - H * 0.01, ry + H * 0.035)]), P["roll"],
               [line([(rx - H * 0.04, ry - H * 0.04), (rx - H * 0.05, ry + H * 0.03)], shade(P["roll"], 0.65), 2.2), line([(rx + H * 0.04, ry - H * 0.042), (rx + H * 0.035, ry + H * 0.03)], shade(P["roll"], 0.65), 2.2)], s=4)
    # the health cell in a side pocket: a red jar with a white cross
    hx, hy = x0 + H * 0.06, y1 - H * 0.07
    out += cel(rect(hx - H * 0.026, hy - H * 0.035, hx + H * 0.026, hy + H * 0.04, 5), P["cell"], [path(smooth([(hx - 3, hy - 9, True), (hx + 3, hy - 9, True), (hx + 3, hy - 3, True),
                (hx + 9, hy - 3, True), (hx + 9, hy + 3, True), (hx + 3, hy + 3, True), (hx + 3, hy + 9, True), (hx - 3, hy + 9, True), (hx - 3, hy + 3, True), (hx - 9, hy + 3, True),
                (hx - 9, hy - 3, True), (hx - 3, hy - 3, True)]), "#f4efe6", INK, 1.2)], s=3)
    out += cel(rect(hx - H * 0.02, hy - H * 0.048, hx + H * 0.02, hy - H * 0.034, 2), P["brass"], [], s=1)
    # the bomb in a net, hanging from the frame's foot
    bx, by = x0 + H * 0.0, y1 + H * 0.02
    out += cel(smooth([(bx - H * 0.03, by), (bx, by - H * 0.03), (bx + H * 0.03, by), (bx, by + H * 0.03)]), "#2a2a30", [ellipse(bx + H * 0.01, by - H * 0.012, 3, 2.2, "#55555e")], s=3)
    out += [line([(bx, by - H * 0.03), (bx + 3, by - H * 0.045), (bx + 7, by - H * 0.05)], INK, 2.6), line([(bx, by - H * 0.03), (bx + 3, by - H * 0.045), (bx + 7, by - H * 0.05)], "#c9a24a", 1.2)]
    # the pot hanging at the back
    px, py = x0 - H * 0.005, y0 + H * 0.3
    out += cel(smooth([(px - H * 0.03, py - H * 0.02, True), (px + H * 0.01, py - H * 0.02, True), (px + H * 0.012, py + H * 0.02), (px - H * 0.01, py + H * 0.04),
                       (px - H * 0.04, py + H * 0.02)]), P["pot"], [line([(px - H * 0.032, py - H * 0.012), (px + H * 0.008, py - H * 0.012)], light(P["pot"], 0.4), 1.2)], s=3)
    return out


def merchant_b_side(fig):
    L, g = fig.L, fig.g
    P = L["P"]
    H = g.H
    body_side(fig, P)
    fig.add(Z_BACK, "pack", pack_side(g, P))
    hem = g.ankle_y + H * 0.002
    fig.add(Z_COAT, "skirt", cel(smooth(skirt_side(g, g.waist_y - H * 0.012, hem, H * 0.088, H * 0.11)), P["skirt"],
                                 [line([(CX + H * 0.01, g.hip_y), (CX + H * 0.03, hem - 3)], shade(P["skirt"], 0.7), 1.4),
                                  line([(CX - H * 0.05, g.hip_y + H * 0.02), (CX - H * 0.07, hem - 3)], shade(P["skirt"], 0.7), 1.4),
                                  line([(CX - H * 0.12, hem - 6), (CX + H * 0.1, hem - 6)], P["trim"], 3.0)], s=7))
    fx = CX + g.dchest * 0.86 + g.belly
    ap = smooth([(CX + H * 0.03, g.waist_y - H * 0.008), (fx + H * 0.018, g.waist_y), (CX + g.dchest * 0.86 + g.belly * 0.8 + H * 0.024, g.hip_y),
                 (CX + H * 0.094, g.knee_y + H * 0.06, True), (CX + H * 0.03, g.knee_y + H * 0.066, True), (CX + H * 0.02, g.hip_y)])
    fig.add(Z_APRON, "apron", cel(ap, P["apron"], [line([(CX + H * 0.06, g.hip_y + H * 0.02), (CX + H * 0.07, g.knee_y + H * 0.05)], shade(P["apron"], 0.75), 1.3)], s=5))
    # the shawl round her shoulders
    shawl = smooth([(CX - H * 0.04, g.chin + H * 0.004), (CX + H * 0.04, g.chin + H * 0.014), (CX + g.dchest + g.bust + H * 0.014, g.chest_y - H * 0.004),
                    (CX + g.dchest * 0.7, g.chest_y + H * 0.05, True), (CX - g.dback * 0.4, g.chest_y + H * 0.07, True), (CX - g.dback - H * 0.016, g.sh_y + H * 0.05)])
    fig.add(Z_NECK + 0.5, "shawl", cel(shawl, P["shawl"], [line([(CX - H * 0.02, g.sh_y), (CX + H * 0.03, g.chest_y + H * 0.04)], shade(P["shawl"], 0.75), 1.3)], s=5)
            + [line([(CX + g.dchest * 0.7 - 2 * i, g.chest_y + H * 0.05 + 0.6 * i), (CX + g.dchest * 0.7 - 2 * i - 1, g.chest_y + H * 0.05 + 0.6 * i + 6)], shade(P["shawl"], 0.6), 1.4)
               for i in range(0, 34, 4)])
    # the pack straps over her shoulder, her near hand on one
    strap = [(CX - g.dback * 0.6, g.sh_y + H * 0.004), (CX + g.dchest * 0.6, g.sh_y + H * 0.02), (CX + g.dchest + g.bust + H * 0.004, g.chest_y + H * 0.03),
             (CX + g.dchest * 0.6, g.waist_y - H * 0.01), (CX - g.dback * 0.6, g.waist_y + H * 0.01)]
    fig.add(Z_NECK + 0.8, "strap", [line(strap, INK, 9.0), line(strap, P["leather"], 5.6)])
    s, e, w = g.s_arm["near"]
    fig.add(Z_HAND, "near-hand", hand_side(w, ang(e, w) - 0.6, H * 0.08, P["face"]["skin"], grip=True))
    f = P["face"]
    hair = cel(smooth([g.Q(-0.04, 0.2), g.Q(-0.02, 0.26), g.Q(-0.16, 0.26), g.Q(-0.32, 0.36), g.Q(-0.4, 0.46), g.Q(-0.44, 0.38), g.Q(-0.34, 0.28)]), P["hair"], [], s=2, sw=2.4)
    hoop = [ellipse(*g.Q(-0.52, 0.8), 5.0, 6.4, "none", INK, 3.6), ellipse(*g.Q(-0.52, 0.8), 5.0, 6.4, "none", P["brass"], 1.8)]
    fig.add(Z_HEAD, "head", head_side(g, f, hair_mid=hair + headscarf_side(g, P["scarf"]), extra=hoop))


def merchant_b_front(fig):
    L, g = fig.L, fig.g
    P = L["P"]
    H = g.H
    body_front(fig, P)
    # the pack behind her: its frame wider than her shoulders, the bedroll across the top, the axe head
    x0, x1 = CX - g.sw - H * 0.02, CX + g.sw + H * 0.02
    y0 = g.crown + H * 0.07
    back = cel(rect(x0, y0, x1, g.hip_y + H * 0.0, 8), P["pack"], [], s=6)
    back += cel(rect(x0 - H * 0.02, y0 - H * 0.03, x1 + H * 0.02, y0 + H * 0.04, 10), P["roll"], [line([(x0 + H * 0.03, y0 - H * 0.03), (x0 + H * 0.03, y0 + H * 0.04)], shade(P["roll"], 0.65), 2.2),
                                                                                         line([(x1 - H * 0.03, y0 - H * 0.03), (x1 - H * 0.03, y0 + H * 0.04)], shade(P["roll"], 0.65), 2.2)], s=4)
    back += cel(rect(x1 - H * 0.02, y0 - H * 0.12, x1 - H * 0.006, y0, 2), P["wood"], [], s=1.5, sw=2.6)
    back += cel(smooth([(x1 - H * 0.014, y0 - H * 0.12, True), (x1 + H * 0.04, y0 - H * 0.135), (x1 + H * 0.05, y0 - H * 0.09, True), (x1 - H * 0.014, y0 - H * 0.08, True)]),
                P["steel"], [], s=2)
    back += cel(rect(x0 - H * 0.03, g.chest_y, x0 + H * 0.01, g.waist_y, 4), P["cell"], [], s=2)
    fig.add(Z_BACK, "pack", back)
    hem = g.ankle_y + H * 0.002
    fig.add(Z_COAT, "skirt", cel(smooth(skirt_front(g, g.waist_y - H * 0.012, hem, g.ww + g.belly * 0.5 + H * 0.012, g.hw + H * 0.065)), P["skirt"],
                                 [line([(CX - H * 0.03, g.hip_y), (CX - H * 0.05, hem - 3)], shade(P["skirt"], 0.7), 1.4),
                                  line([(CX + H * 0.03, g.hip_y), (CX + H * 0.05, hem - 3)], shade(P["skirt"], 0.7), 1.4),
                                  line([(CX - g.hw - H * 0.07, hem - 6), (CX + g.hw + H * 0.07, hem - 6)], P["trim"], 3.0)], s=7))
    ap = smooth([(CX - g.ww - H * 0.0, g.waist_y - H * 0.006), (CX + g.ww + H * 0.0, g.waist_y - H * 0.006), (CX + g.hw + H * 0.01, g.knee_y + H * 0.06, True),
                 (CX - g.hw - H * 0.01, g.knee_y + H * 0.06, True)])
    fig.add(Z_APRON, "apron", cel(ap, P["apron"], [], s=5))
    shawl = smooth([(CX - H * 0.05, g.chin - H * 0.004), (CX + H * 0.05, g.chin - H * 0.004), (CX + g.sw + H * 0.012, g.sh_y + H * 0.03), (CX + g.sw - H * 0.01, g.chest_y + H * 0.03),
                    (CX, g.chest_y + H * 0.07, True), (CX - g.sw + H * 0.01, g.chest_y + H * 0.03), (CX - g.sw - H * 0.012, g.sh_y + H * 0.03)])
    fig.add(Z_NECK + 0.5, "shawl", cel(shawl, P["shawl"], [line([(CX - H * 0.05, g.sh_y + H * 0.01), (CX, g.chest_y + H * 0.06)], shade(P["shawl"], 0.75), 1.3)], s=5))
    for sgn in (-1, 1):
        st = [(CX + sgn * g.sw * 0.6, g.sh_y - H * 0.002), (CX + sgn * g.sw * 0.66, g.chest_y + H * 0.02), (CX + sgn * g.sw * 0.7, g.waist_y)]
        fig.add(Z_NECK + 0.8, "strap", [line(st, INK, 9.0), line(st, P["leather"], 5.6)])
    f = P["face"]
    hair = cel(smooth([g.F(-f["w"] + 0.04, 0.3), g.F(-0.1, 0.17), g.F(0.0, 0.2), g.F(0.12, 0.17), g.F(f["w"] - 0.04, 0.3), g.F(f["w"] - 0.06, 0.24), g.F(0, 0.24),
                       g.F(-f["w"] + 0.06, 0.24)]), P["hair"], [], s=2, sw=2.2)
    hoops = []
    for sgn in (-1, 1):
        c = g.F(sgn * (f["w"] + 0.05), 0.76)
        hoops += [ellipse(c[0], c[1], 4.0, 6.0, "none", INK, 3.6), ellipse(c[0], c[1], 4.0, 6.0, "none", P["brass"], 1.8)]
    fig.add(Z_HEAD, "head", head_front(g, f, hair_mid=hair + headscarf_front(g, f, P["scarf"]), extra=hoops))


look(id="merchant_b", char="merchant_prototype", letter="B", label="travelling pedlar (the whole shop on her back: axe, bomb, health cell)",
     H=168 * CM, hr=0.195, build=dict(shoulder=0.114, waist=0.09, hip=0.106, chest=0.066, back=0.066, bust=0.014, belly=0.02, seat=0.01, limb=1.0),
     P=dict(face=merchant_b_face(), hair="#1e1714", scarf="#a8322e", shirt="#d9c9a4", sleeve="#d9c9a4", legs="#3a2a2a", shoe="#3a2a20", shoe_kind="boot", no_legs=True,
            skirt="#3f5a6e", trim="#d4a944", apron="#c9b48a", shawl="#c27a3a", leather="#6b4430", pack="#8a6a48", roll="#7d8a5a", wood="#8a6440", steel="#b9c0c8",
            cell="#c83a3a", brass="#d4a944", pot="#4a4a52", hand_held={"near": True}),
     pose=merchant_b_pose, side=merchant_b_side, front=merchant_b_front)


# ---- C: the showroom salesman, terms still pending ------------------------------------------

def merchant_c_face():
    return dict(skin="#efc4a2", nose=0.12, hook=-0.01, droop=0.0, brow=0.015, lip=0.018, chin=0.035, jaw_drop=0.03, w=0.39, jaw=0.94, chinw=0.48, cheek=1.06,
                brow_th=2.6, brow_c="#5a3220", brow_tilt=-1.0, age=0, iris="#4a6a3a", nose_w=0.075, mouth_w=0.12)


def merchant_c_pose(g):
    H = g.H
    s, e, w = g.s_arm["near"]
    g.s_arm["near"] = (s, (CX - H * 0.006, g.waist_y + H * 0.002), (CX + H * 0.07, g.waist_y + H * 0.03))
    s, e, w = g.f_arm["left"]
    g.f_arm["left"] = (s, (CX + g.sw + H * 0.014, g.waist_y), (CX + g.sw - H * 0.01, g.waist_y + H * 0.06))


def slick_hair_side(g, hair):
    d = cap_hair_side(g, 128, 318, 0.03, [(-0.02, 0.17), (-0.14, 0.2), (-0.3, 0.28), (-0.4, 0.4), (-0.43, 0.5), (-0.52, 0.42), (-0.62, 0.5), (-0.66, 0.8)], n=16)
    items = [line([g.Q(-0.06, 0.05), g.Q(-0.4, -0.02), g.Q(-0.8, 0.16)], light(hair, 0.45), 2.4), line([g.Q(-0.1, 0.12), g.Q(-0.5, 0.1), g.Q(-0.84, 0.3)], shade(hair, 0.7), 1.2),
             line([g.Q(-0.3, 0.24), g.Q(-0.62, 0.3), g.Q(-0.86, 0.46)], shade(hair, 0.7), 1.2)]
    return cel(d, hair, items, s=4, sw=2.8)


def slick_hair_front(g, f, hair):
    w = f.get("w", 0.37)
    d = front_cap(g, f, 0.03, [(-w - 0.01, 0.42), (-w + 0.02, 0.3), (-w * 0.6, 0.2), (-0.12, 0.17), (-0.1, 0.06, True), (-0.02, 0.2), (w * 0.6, 0.2), (w - 0.02, 0.3),
                               (w + 0.01, 0.42)], top=-0.05)
    items = [line([g.F(-0.08, 0.02), g.F(0.2, 0.0), g.F(0.36, 0.14)], light(hair, 0.45), 2.4), line([g.F(-0.1, 0.06), g.F(-0.3, 0.1)], shade(hair, 0.7), 1.2)]
    return cel(d, hair, items, s=4, sw=2.8)


def check(x0, y0, x1, y1, step, c1, c2):
    out = [line([(x, y0 - 4), (x, y1 + 4)], c1, 2.2) for x in [x0 + i * step for i in range(int((x1 - x0) / step) + 2)]]
    out += [line([(x0 - 4, y), (x1 + 4, y)], c1, 2.2) for y in [y0 + i * step for i in range(int((y1 - y0) / step) + 2)]]
    out += [line([(x + step / 2, y0 - 4), (x + step / 2, y1 + 4)], c2, 0.8) for x in [x0 + i * step for i in range(int((x1 - x0) / step) + 2)]]
    return out


def clipboard(c, wd, ht, a, board="#a87a4a", paper="#f2ede2"):
    q = frame(c, a)
    d = smooth([q(-wd / 2, -ht / 2, True), q(wd / 2, -ht / 2, True), q(wd / 2, ht / 2, True), q(-wd / 2, ht / 2, True)])
    out = cel(d, board, [], s=2)
    pd = smooth([q(-wd / 2 + 4, -ht / 2 + 7, True), q(wd / 2 - 4, -ht / 2 + 7, True), q(wd / 2 - 4, ht / 2 - 4, True), q(-wd / 2 + 4, ht / 2 - 4, True)])
    out += cel(pd, paper, [line([q(-wd / 2 + 8, -ht / 2 + 14 + i * 7), q(wd / 2 - 16 - (i % 2) * 6, -ht / 2 + 14 + i * 7)], "#8a8478", 1.1) for i in range(int((ht - 24) / 7))]
               + [line([q(wd / 2 - 13, -ht / 2 + 13 + i * 7), q(wd / 2 - 7, -ht / 2 + 13 + i * 7)], "#b03a3a", 1.4) for i in range(int((ht - 24) / 7))], s=1.5, sw=1.8)
    clip = smooth([q(-wd / 4, -ht / 2 - 3, True), q(wd / 4, -ht / 2 - 3, True), q(wd / 4, -ht / 2 + 8, True), q(-wd / 4, -ht / 2 + 8, True)])
    return out + cel(clip, "#cdd2d8", [], s=1.5, sw=2.0)


def bowtie(c, s, color):
    x, y = c
    d = smooth([(x, y, True), (x - s, y - s * 0.6, True), (x - s * 1.05, y + s * 0.6, True), (x, y, True), (x + s * 1.05, y - s * 0.6, True), (x + s, y + s * 0.6, True)])
    return cel(d, color, [], s=1.5, sw=2.2) + [ellipse(x, y, s * 0.3, s * 0.4, shade(color, 0.8), INK, 1.4)]


def merchant_c_side(fig):
    L, g = fig.L, fig.g
    P = L["P"]
    H = g.H
    body_side(fig, P)
    hem = g.crotch_y + H * 0.03
    d = smooth(coat_side(g, g.chin + H * 0.026, H * 0.012, hem, H * 0.07 + g.belly * 0.6, H * 0.09))
    fig.add(Z_COAT, "jacket", cel(d, P["jacket"], check(CX - H * 0.16, g.chin, CX + H * 0.16, hem + 10, 11, P["check"], P["check2"])
                                  + [line([(CX + H * 0.03, g.waist_y + H * 0.04), (CX + H * 0.064, g.waist_y + H * 0.05)], INK, 1.6)], s=7))
    # the lapel, the shirt and bow tie at the throat
    fx = CX + g.dchest + g.bust
    fig.add(Z_NECK + 0.5, "shirt-front", cel(smooth([(CX + H * 0.02, g.chin + H * 0.012), (CX + H * 0.044, g.chin + H * 0.018), (fx - H * 0.0, g.sh_y + H * 0.04),
                                                     (fx - H * 0.012, g.chest_y), (CX + H * 0.04, g.sh_y + H * 0.02)]), P["shirt"], [], s=2))
    fig.add(Z_NECK + 0.6, "lapel", cel(smooth([(CX + H * 0.03, g.chin + H * 0.02), (fx - H * 0.006, g.chest_y - H * 0.0), (fx + H * 0.002, g.chest_y + H * 0.04, True),
                                               (fx - H * 0.02, g.chest_y + H * 0.02), (CX + H * 0.03, g.sh_y + H * 0.02)]), shade(P["jacket"], 0.85), [], s=2))
    fig.add(Z_NECK + 0.7, "bowtie", bowtie((CX + H * 0.046, g.chin + H * 0.024), H * 0.018, P["tie"]))
    # the tape measure round his neck
    tape = [(CX - H * 0.035, g.chin + H * 0.012), (CX + H * 0.04, g.chin + H * 0.034), (fx + H * 0.004, g.chest_y + H * 0.01), (fx + g.belly * 0.6, g.waist_y + H * 0.02)]
    fig.add(Z_NECK + 0.8, "tape", [line(tape, INK, 6.6), line(tape, P["tape"], 3.6)] + [line([lerp(tape[2], tape[3], t), (lerp(tape[2], tape[3], t)[0] - 2.4, lerp(tape[2], tape[3], t)[1] + 0.4)], INK, 0.9) for t in (0.2, 0.4, 0.6, 0.8)])
    # the price tags dangling from his breast pocket
    fig.add(Z_NECK + 0.9, "tags", price_tag((fx - H * 0.02, g.chest_y + H * 0.02), s=0.9) + price_tag((fx - H * 0.034, g.chest_y + H * 0.024), s=0.8, mark=""))
    # the clipboard at his hip, the near hand holding it
    s, e, w = g.s_arm["near"]
    fig.add(Z_ARM + 0.25, "clipboard", clipboard((w[0] + H * 0.04, w[1] - H * 0.01), H * 0.11, H * 0.15, -0.35))
    fig.add(Z_HAND, "near-hand", hand_side(w, ang(e, w) + 0.3, H * 0.085, P["face"]["skin"], grip=True))
    for side in ("near", "far"):
        s, e, w = g.s_arm[side]
        q = frame(w, ang(e, w))
        c = P["shirt"] if side == "near" else shade(P["shirt"], 0.86)
        fig.add((Z_ARM if side == "near" else Z_FARARM) + 0.2, f"{side}-cuff", cel(smooth([q(-H * 0.012, -H * 0.024), q(H * 0.002, -H * 0.024), q(H * 0.002, H * 0.024), q(-H * 0.012, H * 0.024)]), c, [], s=1.5))
    fig.layers = [(z, n, it) if n not in ("near-arm-upper", "near-arm-lower", "far-arm-upper", "far-arm-lower") else
                  (z, n, cel(it_path(it), P["jacket"] if n.startswith("near") else shade(P["jacket"], 0.84), check(CX - 120, 150, CX + 160, 420, 11, P["check"], P["check2"]), s=4))
                  for z, n, it in fig.layers]
    f = P["face"]
    fig.add(Z_HEAD, "head", head_side(g, f, hair_mid=slick_hair_side(g, P["hair"]), hair_front=[line([g.Q(-0.06, 0.705), g.Q(0.05, 0.7)], INK, 4.0),
                                                                                                 line([g.Q(-0.05, 0.704), g.Q(0.045, 0.7)], P["hair"], 1.8)]))


def it_path(items):
    """The outline path of a cel shape (its clip path's ``d``)."""
    m = re.search(r'<clipPath id="[^"]+"><path d="([^"]+)"', items[0])
    return m.group(1)


def merchant_c_front(fig):
    L, g = fig.L, fig.g
    P = L["P"]
    H = g.H
    body_front(fig, P)
    hem = g.crotch_y + H * 0.03
    d = smooth(coat_front(g, g.chin + H * 0.026, H * 0.014, hem, g.hw + H * 0.02))
    items = check(CX - g.sw - 10, g.chin, CX + g.sw + 10, hem + 10, 11, P["check"], P["check2"])
    items += [line([(CX, g.waist_y - H * 0.02), (CX - H * 0.004, hem)], INK, 1.6), path(smooth([(CX, g.waist_y - H * 0.02), (CX - H * 0.04, hem, True), (CX + H * 0.04, hem, True)]), light(P["shirt"], 0.0), INK, 1.6)]
    items += buttons([(CX - H * 0.008, g.waist_y - H * 0.004), (CX - H * 0.008, g.waist_y + H * 0.03)], 2.2, P["button"])
    items += [line([(CX - g.ww - H * 0.02, g.waist_y + H * 0.05), (CX - g.ww * 0.3, g.waist_y + H * 0.05)], INK, 1.6), line([(CX + g.ww * 0.3, g.waist_y + H * 0.05), (CX + g.ww + H * 0.02, g.waist_y + H * 0.05)], INK, 1.6)]
    fig.add(Z_COAT, "jacket", cel(d, P["jacket"], items, s=7))
    fig.add(Z_NECK + 0.5, "shirt-front", cel(smooth([(CX - H * 0.034, g.chin + H * 0.004), (CX + H * 0.034, g.chin + H * 0.004), (CX + H * 0.03, g.chest_y), (CX, g.waist_y - H * 0.02, True),
                                                     (CX - H * 0.03, g.chest_y)]), P["shirt"], [], s=2))
    for sgn in (-1, 1):
        lap = smooth([(CX + sgn * H * 0.036, g.chin + H * 0.006), (CX + sgn * H * 0.07, g.sh_y + H * 0.03), (CX + sgn * H * 0.06, g.chest_y - H * 0.0, True),
                      (CX + sgn * H * 0.074, g.chest_y + H * 0.01, True), (CX + sgn * H * 0.004, g.waist_y - H * 0.02, True), (CX + sgn * H * 0.03, g.chest_y)])
        fig.add(Z_NECK + 0.6, "lapel", cel(lap, shade(P["jacket"], 0.85), [], s=2))
    fig.add(Z_NECK + 0.7, "bowtie", bowtie((CX, g.chin + H * 0.022), H * 0.022, P["tie"]))
    for sgn in (-1, 1):
        tape = [(CX + sgn * H * 0.03, g.chin + H * 0.004), (CX + sgn * H * 0.05, g.sh_y + H * 0.02), (CX + sgn * H * 0.044, g.waist_y + H * 0.02)]
        fig.add(Z_NECK + 0.8, "tape", [line(tape, INK, 7.0), line(tape, P["tape"], 4.0)] + [line([lerp(tape[1], tape[2], t), (lerp(tape[1], tape[2], t)[0] - sgn * 2.4, lerp(tape[1], tape[2], t)[1])], INK, 0.9) for t in (0.2, 0.4, 0.6, 0.8)])
    fig.add(Z_NECK + 0.9, "tags", price_tag((CX + g.sw * 0.6, g.chest_y + H * 0.004), s=0.9) + price_tag((CX + g.sw * 0.48, g.chest_y + H * 0.008), s=0.8, mark=""))
    s, e, w = g.f_arm["left"]
    fig.add(Z_ARM + 0.25, "clipboard", clipboard((w[0] + H * 0.01, w[1] + H * 0.03), H * 0.03, H * 0.15, 0.0, paper="#a87a4a"))
    fig.add(Z_HAND, "left-hand", hand_side((w[0] - 4, w[1] - 4), math.pi / 2 - 0.3, H * 0.078, P["face"]["skin"], grip=True))
    fig.layers = [(z, n, it) if n not in ("right-arm-upper", "right-arm-lower", "left-arm-upper", "left-arm-lower") else
                  (z, n, cel(it_path(it), P["jacket"], check(CX - 200, 150, CX + 200, 420, 11, P["check"], P["check2"]), s=4)) for z, n, it in fig.layers]
    for side in ("right", "left"):
        s, e, w = g.f_arm[side]
        q = frame(w, ang(e, w))
        fig.add(Z_ARM + 0.2, f"{side}-cuff", cel(smooth([q(-H * 0.012, -H * 0.024), q(H * 0.002, -H * 0.024), q(H * 0.002, H * 0.024), q(-H * 0.012, H * 0.024)]), P["shirt"], [], s=1.5))
    f = P["face"]
    fig.add(Z_HEAD, "head", head_front(g, f, hair_mid=slick_hair_front(g, f, P["hair"]), hair_front=mustache_front(g, P["hair"], thin=True)))


look(id="merchant_c", char="merchant_prototype", letter="C", label="showroom salesman (check suit, tape measure, clipboard of pending prices)",
     H=168 * CM, hr=0.2, build=dict(shoulder=0.116, waist=0.108, hip=0.106, chest=0.072, back=0.068, belly=0.068, limb=1.08),
     P=dict(face=merchant_c_face(), hair="#7a3e22", shirt="#f1ede4", sleeve="#b8893c", jacket="#b8893c", check="#8a5a2a", check2="#d8b46a", tie="#b0302e",
            legs="#5a4030", shoe="#2e231d", tape="#e7c43a", button="#3a2a20", hand_held={"near": True, "left": True}),
     pose=merchant_c_pose, side=merchant_c_side, front=merchant_c_front)


# ============================================================================================
# GENERAL HERO
# ============================================================================================

MEDAL_RIBBONS = (("#2f4f8f", "#e6d28a"), ("#a8322e", "#efe6cf"), ("#3a6a4a", "#e6d28a"), ("#5b2f6e", "#efe6cf"))


def medal(x, y, s, ribbon, kind, gold="#d4a944"):
    """A medal on its ribbon, the ribbon's top at ``(x, y)``."""
    r1, r2 = ribbon
    rib = smooth([(x - 3.4 * s, y, True), (x + 3.4 * s, y, True), (x + 3.4 * s, y + 7 * s, True), (x, y + 9 * s, True), (x - 3.4 * s, y + 7 * s, True)])
    out = [path(rib, r1, INK, 1.6), line([(x, y + 0.6), (x, y + 8 * s)], r2, 1.4 * s)]
    cy = y + 12.4 * s
    if kind == "star":
        pts = []
        for i in range(10):
            rr = 5.2 * s if i % 2 == 0 else 2.4 * s
            a = math.radians(-90 + 36 * i)
            pts.append((x + rr * math.cos(a), cy + rr * math.sin(a), True))
        out.append(path(smooth(pts), gold, INK, 1.4))
    elif kind == "cross":
        out.append(path(smooth([(x - 1.6 * s, cy - 4.6 * s, True), (x + 1.6 * s, cy - 4.6 * s, True), (x + 1.6 * s, cy - 1.6 * s, True), (x + 4.6 * s, cy - 1.6 * s, True),
                                (x + 4.6 * s, cy + 1.6 * s, True), (x + 1.6 * s, cy + 1.6 * s, True), (x + 1.6 * s, cy + 4.6 * s, True), (x - 1.6 * s, cy + 4.6 * s, True),
                                (x - 1.6 * s, cy + 1.6 * s, True), (x - 4.6 * s, cy + 1.6 * s, True), (x - 4.6 * s, cy - 1.6 * s, True), (x - 1.6 * s, cy - 1.6 * s, True)]), gold, INK, 1.4))
    else:
        out += [ellipse(x, cy, 4.0 * s, 4.0 * s, gold, INK, 1.4), ellipse(x, cy, 2.0 * s, 2.0 * s, "none", shade(gold, 0.7), 0.9)]
    return out


def medal_row(x0, y, n, s, dx, kinds=("disc", "star", "cross", "disc")):
    out = []
    for i in range(n):
        out += medal(x0 + i * dx, y, s, MEDAL_RIBBONS[i % len(MEDAL_RIBBONS)], kinds[i % len(kinds)])
    return out


def sword_hilt(p, a, grip, guard, metal, wrap, pommel=True):
    """A sword's hilt from the guard at ``p`` along ``a`` (toward the pommel)."""
    q = frame(p, a)
    out = cel(smooth([q(0, -2.8), q(grip, -2.6), q(grip, 2.6), q(0, 2.8)]), wrap, [line([q(grip * f, -2.6), q(grip * f + 2, 2.6)], shade(wrap, 0.6), 0.9) for f in (0.25, 0.5, 0.75)],
              s=1.2, sw=2.2)
    out += cel(smooth([q(-2.6, -guard, True), q(2.6, -guard, True), q(2.6, guard, True), q(-2.6, guard, True)]), metal, [], s=1.2, sw=2.4)
    if pommel:
        c = q(grip + 3.6, 0)
        out += [ellipse(c[0], c[1], 4.6, 4.6, metal, INK, 2.2), ellipse(c[0] + 1.2, c[1] - 1.2, 1.4, 1.4, light(metal, 0.6))]
    return out


def scabbard(a, b, r, leather, metal):
    q = frame(b, ang(a, b))
    out = cel(capsule(a, b, r, r * 0.8), leather, [], s=2, sw=2.6)
    out += cel(smooth([q(-14, -r * 0.95), q(0, -r * 0.85), q(4, 0), q(0, r * 0.85), q(-14, r * 0.95)]), metal, [], s=1.5, sw=2.2)
    qa = frame(a, ang(a, b))
    out += cel(smooth([qa(0, -r * 1.05, True), qa(8, -r * 1.05, True), qa(8, r * 1.05, True), qa(0, r * 1.05, True)]), metal, [], s=1.5, sw=2.2)
    return out


def scarf_band_side(g, color):
    H = g.H
    return cel(smooth([(CX - H * 0.048, g.chin - H * 0.008), (CX + H * 0.034, g.chin + H * 0.0), (CX + H * 0.05, g.chin + H * 0.026), (CX + H * 0.03, g.sh_y + H * 0.012),
                       (CX - H * 0.05, g.sh_y + H * 0.0)]), color, [line([(CX - H * 0.04, g.chin + H * 0.014), (CX + H * 0.04, g.chin + H * 0.02)], shade(color, 0.7), 1.3)], s=4)


def scarf_tail_side(g, color, to_y, x_end):
    H = g.H
    return cel(smooth([(CX + H * 0.02, g.chin + H * 0.02), (CX + H * 0.05, g.chin + H * 0.03), (x_end + H * 0.012, (g.chin + to_y) / 2), (x_end + H * 0.008, to_y, True),
                       (x_end - H * 0.022, to_y + H * 0.008, True), (x_end - H * 0.02, (g.chin + to_y) / 2)]), color,
               [line([(x_end - H * 0.016, to_y - 1), (x_end + H * 0.006, to_y - 2)], light(color, 0.4), 1.4)], s=3)


def scarf_front(g, color, tail_x, tail_y):
    H = g.H
    band = cel(smooth([(CX - H * 0.05, g.chin - H * 0.012), (CX + H * 0.05, g.chin - H * 0.012), (CX + H * 0.056, g.sh_y + H * 0.004), (CX, g.sh_y + H * 0.018),
                       (CX - H * 0.056, g.sh_y + H * 0.004)]), color, [line([(CX - H * 0.04, g.chin + H * 0.01), (CX + H * 0.04, g.chin + H * 0.01)], shade(color, 0.7), 1.3)], s=4)
    tail = cel(smooth([(CX + tail_x * 0.4 - H * 0.02, g.sh_y), (CX + tail_x * 0.4 + H * 0.02, g.sh_y), (CX + tail_x + H * 0.022, tail_y, True),
                       (CX + tail_x - H * 0.022, tail_y + H * 0.006, True)]), color, [], s=3)
    return tail + band


def short_hair_side(g, hair, grey=None, length=0.0):
    d = cap_hair_side(g, 128, 316, 0.026, [(-0.02, 0.15), (-0.12, 0.17), (-0.26, 0.24), (-0.36, 0.34), (-0.4, 0.5), (-0.47, 0.5), (-0.5, 0.42), (-0.62, 0.48),
                                           (-0.66, 0.66 + length), (-0.62, 0.86 + length)], n=16)
    items = [line([g.Q(-0.1, 0.06), g.Q(-0.4, 0.0), g.Q(-0.76, 0.16)], light(hair, 0.35), 2.0), line([g.Q(-0.2, 0.16), g.Q(-0.5, 0.16), g.Q(-0.8, 0.34)], shade(hair, 0.7), 1.2)]
    if grey:
        items.append(path(smooth([g.Q(-0.3, 0.27), g.Q(-0.4, 0.3), g.Q(-0.44, 0.5), g.Q(-0.36, 0.5), g.Q(-0.34, 0.36)]), grey))
    return cel(d, hair, items, s=4, sw=2.8)


def short_hair_front(g, f, hair, grey=None, part=-0.12):
    w = f.get("w", 0.37)
    d = front_cap(g, f, 0.026, [(-w - 0.005, 0.46), (-w + 0.02, 0.3), (-w * 0.62, 0.17), (part, 0.14), (part + 0.06, 0.16), (w * 0.62, 0.17), (w - 0.02, 0.3),
                                (w + 0.005, 0.46)], top=-0.04)
    items = [line([g.F(part, 0.12), g.F(part - 0.02, 0.0)], shade(hair, 0.65), 1.3), line([g.F(part + 0.04, 0.02), g.F(0.26, 0.04)], light(hair, 0.35), 2.0)]
    if grey:
        for sgn in (-1, 1):
            items.append(path(smooth([g.F(sgn * (w + 0.02), 0.26), g.F(sgn * (w - 0.03), 0.26), g.F(sgn * (w - 0.02), 0.46), g.F(sgn * (w + 0.03), 0.46)]), grey))
    return cel(d, hair, items, s=4, sw=2.8)


# ---- A: the war hero, home, in his greatcoat -------------------------------------------------

def hero_a_face():
    return dict(skin="#d39f7b", nose=0.145, hook=0.008, droop=0.0, brow=0.035, lip=0.012, chin=0.04, jaw_drop=0.01, w=0.37, jaw=0.94, chinw=0.5, cheek=1.0,
                brow_th=3.2, brow_c="#2e221c", brow_tilt=0.2, age=1, lids=1, iris="#4a6478", nose_w=0.075, mouth_w=0.1, stubble="#8a7464")


def hero_a_side(fig):
    L, g = fig.L, fig.g
    P = L["P"]
    H = g.H
    body_side(fig, P)
    # the tunic's skirt to the hip, the belt
    fig.add(Z_VEST, "tunic", cel(smooth(vest_side(g, out=0.004, bottom=0.075, front_point=0.0)), P["shirt"],
                                 buttons([(CX + g.dchest + H * 0.002, g.sh_y + H * 0.03), (CX + g.dchest + H * 0.006, g.chest_y + H * 0.01), (CX + g.dchest * 0.96, g.waist_y - H * 0.014)],
                                         2.1, P["brass"]), s=6))
    fig.add(Z_VEST + 1, "belt", belt_side(g, g.waist_y + H * 0.006, H * 0.011, P["belt"], P["brass"], CX + g.dchest * 0.92 + H * 0.01, CX - g.dback * 0.9 - H * 0.008))
    fig.add(Z_VEST + 2, "medals", medal_row(CX + g.dchest - H * 0.02, g.chest_y - H * 0.022, 2, 0.95, 7.0))
    # the sword on his far hip: the hilt forward of the belt, the scabbard's tip behind the coat
    hilt_p = (CX + g.dchest + H * 0.006, g.waist_y + H * 0.024)
    tip = (CX - H * 0.2, g.knee_y + H * 0.02)
    a = ang(tip, hilt_p)
    fig.add(Z_FARSKIRT, "scabbard", scabbard(hilt_p, tip, 4.6, P["belt"], P["brass"]))
    fig.add(Z_FARSKIRT + 0.1, "hilt", sword_hilt(hilt_p, a, H * 0.05, 9, P["brass"], P["grip"]))
    # the greatcoat, open, to mid-calf: its back and its near front panel
    hem = g.knee_y + H * 0.1
    coat = [(CX - H * 0.03, g.chin + H * 0.006), (CX - g.dback * 0.8, g.sh_y + H * 0.004), (CX - g.dback - H * 0.014, g.sh_y + H * 0.05), (CX - g.dback * 0.9 - H * 0.016, g.waist_y),
            (CX - g.dback - H * 0.03, g.hip_y + H * 0.02), (CX - H * 0.13, hem, True), (CX + H * 0.05, hem + H * 0.004, True), (CX + H * 0.045, g.knee_y), (CX + H * 0.04, g.hip_y),
            (CX + H * 0.046, g.waist_y), (CX + g.dchest * 0.66, g.chest_y), (CX + g.dchest * 0.5, g.sh_y + H * 0.01), (CX + H * 0.02, g.chin + H * 0.016)]
    items = [line([(CX - H * 0.04, g.waist_y + H * 0.04), (CX - H * 0.08, hem - 4)], shade(P["coat"], 0.72), 1.5),
             line([(CX + H * 0.0, g.hip_y), (CX - H * 0.01, hem - 4)], shade(P["coat"], 0.72), 1.3),
             line([(CX - g.dback - H * 0.03, g.waist_y + H * 0.004), (CX - g.dback + H * 0.03, g.waist_y + H * 0.004)], INK, 1.6)]
    items += buttons([(CX - g.dback + H * 0.016, g.waist_y + H * 0.004)], 2.2, P["brass"])
    fig.add(Z_COAT, "greatcoat", cel(smooth(coat), P["coat"], items, s=8))
    facing = smooth([(CX + H * 0.03, g.sh_y + H * 0.004), (CX + g.dchest * 0.66 + H * 0.002, g.chest_y), (CX + H * 0.048, g.waist_y), (CX + H * 0.042, g.hip_y),
                     (CX + H * 0.047, g.knee_y), (CX + H * 0.052, hem + H * 0.002, True), (CX + H * 0.034, hem, True), (CX + H * 0.03, g.knee_y), (CX + H * 0.026, g.hip_y),
                     (CX + H * 0.03, g.waist_y), (CX + g.dchest * 0.5, g.chest_y)])
    fig.add(Z_COAT + 0.5, "facing", cel(facing, shade(P["coat"], 0.84), [], s=2))
    # the turned-up collar
    fig.add(Z_NECK + 1.5, "collar", cel(smooth([(CX - H * 0.062, g.chin - H * 0.008), (CX - H * 0.034, g.chin - H * 0.01), (CX - H * 0.004, g.chin + H * 0.014), (CX + H * 0.02, g.sh_y + H * 0.01),
                                                (CX - g.dback * 0.8, g.sh_y + H * 0.006), (CX - H * 0.07, g.chin + H * 0.02)]), P["coat"],
                                        [line([(CX - H * 0.05, g.chin - H * 0.0), (CX - H * 0.035, g.chin + H * 0.026)], shade(P["coat"], 0.7), 1.3)], s=4))
    fig.add(Z_NECK + 1, "scarf", scarf_band_side(g, P["scarf"]) + scarf_tail_side(g, P["scarf"], g.waist_y - H * 0.02, CX + g.dchest + H * 0.008))
    for side in ("near", "far"):
        s, e, w = g.s_arm[side]
        q = frame(w, ang(e, w))
        c = P["coat"] if side == "near" else shade(P["coat"], 0.84)
        fig.add((Z_ARM if side == "near" else Z_FARARM) + 0.2, f"{side}-cuff",
                cel(smooth([q(-H * 0.045, -H * 0.032), q(0, -H * 0.034), q(0, H * 0.034), q(-H * 0.045, H * 0.032)]), shade(c, 0.9), [], s=3))
    f = P["face"]
    fig.add(Z_HEAD, "head", head_side(g, f, hair_mid=short_hair_side(g, P["hair"], P["grey"])))


def hero_a_front(fig):
    L, g = fig.L, fig.g
    P = L["P"]
    H = g.H
    body_front(fig, P)
    fig.add(Z_VEST, "tunic", cel(smooth(coat_front(g, g.chin + H * 0.02, H * 0.006, g.crotch_y + H * 0.01, g.hw + H * 0.008)), P["shirt"],
                                 buttons([(CX, y) for y in (g.sh_y + H * 0.03, g.chest_y + H * 0.01, g.chest_y + H * 0.045)], 2.1, P["brass"])
                                 + [line([(CX, g.sh_y + H * 0.02), (CX, g.crotch_y)], shade(P["shirt"], 0.7), 1.3)], s=6))
    fig.add(Z_VEST + 1, "belt", belt_front(g, g.waist_y + H * 0.006, H * 0.011, g.ww + H * 0.01, P["belt"], P["brass"], bw=H * 0.02))
    fig.add(Z_VEST + 2, "medals", medal_row(CX + H * 0.03, g.chest_y - H * 0.03, 3, 0.95, 8.0))
    # the hilt at his left hip
    hilt_p = (CX + g.ww - H * 0.004, g.waist_y + H * 0.035)
    fig.add(Z_VEST + 3, "hilt", sword_hilt(hilt_p, math.radians(-120), H * 0.05, 9, P["brass"], P["grip"]))
    hem = g.knee_y + H * 0.1
    for sgn in (-1, 1):
        panel = [(CX + sgn * H * 0.034, g.chin + H * 0.004), (CX + sgn * g.sw * 0.74, g.sh_y + H * 0.0), (CX + sgn * (g.sw + H * 0.008), g.sh_y + H * 0.03),
                 (CX + sgn * (g.sw - H * 0.002), g.chest_y + H * 0.02), (CX + sgn * (g.ww + H * 0.016), g.waist_y), (CX + sgn * (g.hw + H * 0.03), g.hip_y),
                 (CX + sgn * (g.hw + H * 0.06), hem, True), (CX + sgn * H * 0.06, hem + H * 0.004, True), (CX + sgn * H * 0.054, g.hip_y), (CX + sgn * H * 0.05, g.waist_y),
                 (CX + sgn * H * 0.07, g.chest_y), (CX + sgn * H * 0.05, g.sh_y + H * 0.02)]
        items = [line([(CX + sgn * (g.hw + H * 0.0), g.hip_y + H * 0.02), (CX + sgn * (g.hw + H * 0.02), hem - 4)], shade(P["coat"], 0.72), 1.4)]
        items += buttons([(CX + sgn * H * 0.08, g.chest_y + H * 0.02), (CX + sgn * H * 0.074, g.waist_y - H * 0.01)], 2.2, P["brass"])
        fig.add(Z_COAT, "greatcoat", cel(smooth(panel), P["coat"], items, s=8))
        lap = smooth([(CX + sgn * H * 0.036, g.chin + H * 0.006), (CX + sgn * H * 0.075, g.sh_y + H * 0.025), (CX + sgn * H * 0.082, g.chest_y + H * 0.03, True),
                      (CX + sgn * H * 0.05, g.waist_y, True), (CX + sgn * H * 0.07, g.chest_y), (CX + sgn * H * 0.05, g.sh_y + H * 0.02)])
        fig.add(Z_COAT + 0.5, "lapel", cel(lap, shade(P["coat"], 0.84), [], s=2))
        fig.add(Z_NECK + 1.5, "collar", cel(smooth([(CX + sgn * H * 0.034, g.chin - H * 0.006), (CX + sgn * H * 0.066, g.chin - H * 0.016), (CX + sgn * H * 0.085, g.sh_y + H * 0.01),
                                                    (CX + sgn * H * 0.04, g.sh_y + H * 0.01)]), P["coat"], [], s=3))
    fig.add(Z_NECK + 1, "scarf", scarf_front(g, P["scarf"], -H * 0.03, g.waist_y - H * 0.02))
    for side in ("right", "left"):
        s, e, w = g.f_arm[side]
        q = frame(w, ang(e, w))
        fig.add(Z_ARM + 0.2, f"{side}-cuff", cel(smooth([q(-H * 0.045, -H * 0.032), q(0, -H * 0.034), q(0, H * 0.034), q(-H * 0.045, H * 0.032)]), shade(P["coat"], 0.9), [], s=3))
    f = P["face"]
    fig.add(Z_HEAD, "head", head_front(g, f, hair_mid=short_hair_front(g, f, P["hair"], P["grey"])))


look(id="hero_a", char="general_hero", letter="A", label="the war hero, home (greatcoat, red scarf, sword at the hip, medals)",
     H=185 * CM, hr=0.178, build=dict(shoulder=0.13, waist=0.08, hip=0.088, chest=0.074, back=0.07, limb=1.0, stance=0.048),
     P=dict(face=hero_a_face(), hair="#3a2a22", grey="#a8a29a", coat="#56677a", sleeve="#56677a", shirt="#2c3850", legs="#2c2d36", shoe="#4a3022", shoe_kind="boot",
            boot_top=None, brass="#d4a944", belt="#5a3a26", grip="#3a2a22", scarf="#a8322e"),
     side=hero_a_side, front=hero_a_front)


# ---- B: the knight who came back: breastplate, cape, standing watch on his sword ---------------

def hero_b_face():
    return dict(skin="#c88f66", nose=0.155, hook=0.03, droop=0.004, brow=0.035, lip=0.014, chin=0.03, w=0.37, jaw=0.9, chinw=0.46, cheek=1.0,
                brow_th=3.0, brow_c="#6a4a2a", brow_tilt=0.4, age=2, lids=1, iris="#4a5a3a", nose_w=0.078, mouth_w=0.1)


def hero_b_pose(g):
    H = g.H
    s, e, w = g.s_arm["near"]
    g.s_arm["near"] = (s, (CX - H * 0.002, g.waist_y + H * 0.004), (CX + H * 0.105, g.waist_y + H * 0.02))
    s, e, w = g.s_arm["far"]
    g.s_arm["far"] = (s, (CX - H * 0.026, g.waist_y), (CX + H * 0.09, g.waist_y + H * 0.016))
    for side, sgn in (("right", -1), ("left", 1)):
        s, e, w = g.f_arm[side]
        g.f_arm[side] = (s, (CX + sgn * (g.sw + H * 0.006), g.waist_y + H * 0.004), (CX + sgn * H * 0.03, g.waist_y + H * 0.03))


def pauldron(c, r, a, steel):
    q = frame(c, a)
    out = []
    for k, (rr, dy) in enumerate(((r, 0.0), (r * 0.86, r * 0.42), (r * 0.72, r * 0.8))):
        d = smooth([q(-rr, dy - r * 0.1), q(-rr * 0.7, dy - r * 0.62), q(0, dy - r * 0.8), q(rr * 0.7, dy - r * 0.62), q(rr, dy - r * 0.1), q(rr * 0.8, dy + r * 0.25),
                    q(0, dy + r * 0.32), q(-rr * 0.8, dy + r * 0.25)])
        out = cel(d, steel, [line([q(-rr * 0.5, dy - r * 0.5), q(rr * 0.2, dy - r * 0.66)], light(steel, 0.6), 1.6)], s=3) + out
    return out


def hero_b_side(fig):
    L, g = fig.L, fig.g
    P = L["P"]
    H = g.H
    body_side(fig, P)
    # the cape hanging behind him
    cape = smooth([(CX - H * 0.02, g.sh_y - H * 0.012), (CX - g.dback - H * 0.03, g.sh_y + H * 0.04), (CX - g.dback - H * 0.05, g.waist_y), (CX - H * 0.15, g.knee_y),
                   (CX - H * 0.17, g.knee_y + H * 0.13, True), (CX - H * 0.13, g.knee_y + H * 0.115), (CX - H * 0.09, g.knee_y + H * 0.13), (CX - H * 0.04, g.knee_y + H * 0.12, True),
                   (CX - H * 0.02, g.hip_y), (CX + H * 0.0, g.sh_y + H * 0.04)])
    fig.add(Z_BACK, "cape", cel(cape, P["cape"], [line([(CX - g.dback - H * 0.02, g.waist_y), (CX - H * 0.12, g.knee_y + H * 0.11)], shade(P["cape"], 0.7), 1.6),
                                                  line([(CX - H * 0.05, g.waist_y + H * 0.02), (CX - H * 0.07, g.knee_y + H * 0.11)], shade(P["cape"], 0.7), 1.4)], s=8))
    # the gambeson's skirt to mid-thigh
    skirt = smooth([(CX + g.dchest * 0.9, g.waist_y), (CX + g.dchest * 0.9 + H * 0.012, g.hip_y), (CX + H * 0.085, g.hip_y + H * 0.1, True), (CX - H * 0.1, g.hip_y + H * 0.1, True),
                    (CX - g.dback - H * 0.014, g.hip_y), (CX - g.dback * 0.9, g.waist_y)])
    fig.add(Z_VEST - 1, "gambeson-skirt", cel(skirt, P["shirt"], [line([(x, g.hip_y - H * 0.01), (x - 2, g.hip_y + H * 0.096)], shade(P["shirt"], 0.7), 1.2)
                                                                  for x in (CX - H * 0.06, CX - H * 0.02, CX + H * 0.02, CX + H * 0.055)], s=6))
    # the breastplate
    bp = smooth([(CX + H * 0.024, g.sh_y + H * 0.006), (CX + g.dchest + H * 0.016, g.chest_y + H * 0.004), (CX + g.dchest + H * 0.01, g.waist_y - H * 0.01),
                 (CX + g.dchest * 0.9 + H * 0.01, g.waist_y + H * 0.03, True), (CX - g.dback * 0.9 - H * 0.008, g.waist_y + H * 0.03, True), (CX - g.dback - H * 0.008, g.sh_y + H * 0.05),
                 (CX - g.dback * 0.7, g.sh_y + H * 0.004)])
    fig.add(Z_VEST, "breastplate", cel(bp, P["steel"], [line([(CX + g.dchest - H * 0.004, g.sh_y + H * 0.04), (CX + g.dchest + H * 0.006, g.chest_y + H * 0.02)], light(P["steel"], 0.7), 2.6),
                                                       line([(CX - g.dback, g.waist_y + H * 0.02), (CX + g.dchest + H * 0.004, g.waist_y + H * 0.02)], shade(P["steel"], 0.7), 1.4)]
                                       + [ellipse(CX + g.dchest * 0.2, g.waist_y + H * 0.022, 1.6, 1.6, P["brass"], INK, 0.8)], s=6))
    fig.add(Z_NECK + 0.8, "clasp", [ellipse(CX + H * 0.02, g.sh_y + H * 0.002, 4.4, 4.4, P["brass"], INK, 1.6)]
            + medal_row(CX + H * 0.034, g.sh_y + H * 0.01, 2, 0.95, 7.0, kinds=("star", "cross")))
    fig.add(Z_NECK - 1, "gorget", cel(smooth([(CX - H * 0.04, g.chin + H * 0.004), (CX + H * 0.036, g.chin + H * 0.012), (CX + H * 0.044, g.sh_y + H * 0.008), (CX - H * 0.045, g.sh_y)]),
                                      P["shirt"], [], s=3))
    fig.add(Z_ARM + 0.05, "near-pauldron", pauldron((CX - H * 0.004, g.sh_y + H * 0.012), H * 0.044, math.radians(-8), P["steel"]))
    # the sword planted point-down before him, both hands on the pommel
    s, e, w = g.s_arm["near"]
    sx = w[0] + H * 0.04
    guard_y = w[1] + H * 0.075
    blade = smooth([(sx - 4.2, guard_y, True), (sx + 4.2, guard_y, True), (sx + 3.6, GROUND - 14), (sx, GROUND - 1, True), (sx - 3.6, GROUND - 14)])
    fig.add(Z_ARM - 0.6, "blade", cel(blade, P["blade"], [line([(sx + 0.6, guard_y + 6), (sx + 0.6, GROUND - 18)], shade(P["blade"], 0.75), 1.0)], s=2, sw=2.6))
    fig.add(Z_ARM - 0.5, "hilt", sword_hilt((sx, guard_y), -math.pi / 2, H * 0.06, 12, P["brass"], P["grip"]))
    fs, fe, fw = g.s_arm["far"]
    fig.add(Z_ARM - 0.4, "far-hand", hand_side(fw, ang(fe, fw), H * 0.085, shade(P["face"]["skin"], 0.86), grip=True))
    fig.add(Z_HAND, "near-hand", hand_side(w, ang(e, w), H * 0.085, P["face"]["skin"], grip=True))
    for side in ("near", "far"):
        s, e, w = g.s_arm[side]
        q = frame(w, ang(e, w))
        c = P["bracer"] if side == "near" else shade(P["bracer"], 0.84)
        fig.add((Z_ARM if side == "near" else Z_FARARM) + 0.2, f"{side}-bracer", cel(smooth([q(-H * 0.06, -H * 0.03), q(0, -H * 0.028), q(0, H * 0.028), q(-H * 0.06, H * 0.03)]), c,
                                                                                   [line([q(-H * 0.03, -H * 0.028), q(-H * 0.03, H * 0.028)], shade(c, 0.7), 1.2)], s=2))
    f = P["face"]
    hair = cap_hair_side(g, 128, 318, 0.035, [(-0.02, 0.16), (-0.14, 0.18), (-0.3, 0.26), (-0.42, 0.38), (-0.46, 0.46), (-0.58, 0.42), (-0.68, 0.6), (-0.7, 0.84),
                                               (-0.76, 0.96, True), (-0.84, 0.88)], n=16)
    items = [line([g.Q(-0.08, 0.08), g.Q(-0.4, 0.02), g.Q(-0.8, 0.2)], light(P["hair"], 0.35), 2.0), line([g.Q(-0.2, 0.18), g.Q(-0.6, 0.22), g.Q(-0.86, 0.6)], shade(P["hair"], 0.7), 1.3),
             line([g.Q(-0.3, 0.3), g.Q(-0.7, 0.4), g.Q(-0.9, 0.84)], shade(P["hair"], 0.7), 1.3)]
    fig.add(Z_HEAD, "head", head_side(g, f, hair_mid=cel(hair, P["hair"], items, s=4, sw=2.8), hair_front=beard_side(g, P["hair"], bottom=1.04)))


def hero_b_front(fig):
    L, g = fig.L, fig.g
    P = L["P"]
    H = g.H
    body_front(fig, P)
    cape = smooth([(CX - g.sw * 0.6, g.sh_y - H * 0.01), (CX + g.sw * 0.6, g.sh_y - H * 0.01), (CX + g.sw + H * 0.03, g.sh_y + H * 0.04), (CX + g.hw + H * 0.07, g.knee_y + H * 0.12, True),
                   (CX - g.hw - H * 0.07, g.knee_y + H * 0.12, True), (CX - g.sw - H * 0.03, g.sh_y + H * 0.04)])
    fig.add(Z_BACK, "cape", cel(cape, P["lining"], [], s=8))
    skirt = smooth([(CX - g.ww - H * 0.006, g.waist_y), (CX + g.ww + H * 0.006, g.waist_y), (CX + g.hw + H * 0.03, g.hip_y + H * 0.1, True), (CX - g.hw - H * 0.03, g.hip_y + H * 0.1, True)])
    fig.add(Z_VEST - 1, "gambeson-skirt", cel(skirt, P["shirt"], [line([(x, g.hip_y - H * 0.01), (x * 1.0 + (x - CX) * 0.2, g.hip_y + H * 0.096)], shade(P["shirt"], 0.7), 1.2)
                                                                  for x in (CX - H * 0.06, CX - H * 0.02, CX + H * 0.02, CX + H * 0.06)], s=6))
    bp = smooth([(CX - H * 0.04, g.sh_y + H * 0.004), (CX - g.sw + H * 0.03, g.sh_y + H * 0.02), (CX - g.sw + H * 0.03, g.chest_y + H * 0.02), (CX - g.ww - H * 0.008, g.waist_y),
                 (CX - g.ww - H * 0.004, g.waist_y + H * 0.03, True), (CX, g.waist_y + H * 0.045, True), (CX + g.ww + H * 0.004, g.waist_y + H * 0.03, True), (CX + g.ww + H * 0.008, g.waist_y),
                 (CX + g.sw - H * 0.03, g.chest_y + H * 0.02), (CX + g.sw - H * 0.03, g.sh_y + H * 0.02), (CX + H * 0.04, g.sh_y + H * 0.004), (CX, g.sh_y + H * 0.02)])
    fig.add(Z_VEST, "breastplate", cel(bp, P["steel"], [line([(CX, g.sh_y + H * 0.03), (CX, g.waist_y + H * 0.04)], shade(P["steel"], 0.7), 1.6),
                                                       line([(CX + H * 0.03, g.sh_y + H * 0.04), (CX + H * 0.05, g.chest_y + H * 0.03)], light(P["steel"], 0.7), 3.0)], s=7))
    fig.add(Z_NECK - 1, "gorget", cel(smooth([(CX - H * 0.042, g.chin - H * 0.004), (CX + H * 0.042, g.chin - H * 0.004), (CX + H * 0.05, g.sh_y + H * 0.012), (CX - H * 0.05, g.sh_y + H * 0.012)]),
                                      P["shirt"], [], s=3))
    for sgn in (-1, 1):
        fig.add(Z_ARM + 0.05, "pauldron", pauldron((CX + sgn * (g.sw - H * 0.012), g.sh_y + H * 0.014), H * 0.044, math.radians(sgn * 18), P["steel"]))
        fig.add(Z_NECK + 0.8, "clasp", [ellipse(CX + sgn * H * 0.05, g.sh_y + H * 0.006, 4.4, 4.4, P["brass"], INK, 1.6)])
    fig.add(Z_NECK + 0.8, "chain", chain([(CX - H * 0.05, g.sh_y + H * 0.006), (CX, g.sh_y + H * 0.02), (CX + H * 0.05, g.sh_y + H * 0.006)], P["brass"])
            + medal_row(CX + H * 0.05, g.sh_y + H * 0.012, 2, 0.95, 8.0, kinds=("star", "cross")))
    # the sword before him, point down, both hands on the pommel
    guard_y = g.waist_y + H * 0.105
    blade = smooth([(CX - 4.6, guard_y, True), (CX + 4.6, guard_y, True), (CX + 4.0, GROUND - 14), (CX, GROUND - 1, True), (CX - 4.0, GROUND - 14)])
    fig.add(Z_ARM - 0.6, "blade", cel(blade, P["blade"], [line([(CX, guard_y + 6), (CX, GROUND - 18)], shade(P["blade"], 0.75), 1.0)], s=2, sw=2.6))
    fig.add(Z_ARM - 0.5, "hilt", sword_hilt((CX, guard_y), -math.pi / 2, H * 0.06, 14, P["brass"], P["grip"]))
    for side, sgn in (("right", -1), ("left", 1)):
        s, e, w = g.f_arm[side]
        q = frame(w, ang(e, w))
        fig.add(Z_ARM + 0.2, f"{side}-bracer", cel(smooth([q(-H * 0.06, -H * 0.03), q(0, -H * 0.028), q(0, H * 0.028), q(-H * 0.06, H * 0.03)]), P["bracer"], [], s=2))
        fig.add(Z_HAND + (0.1 if sgn > 0 else 0), f"{side}-fist", hand_side((w[0] - sgn * 2, w[1] + 2), ang(e, w), H * 0.075, P["face"]["skin"], grip=True))
    f = P["face"]
    w = f["w"]
    back = cel(smooth([g.F(-w - 0.03, 0.4), g.F(-w - 0.07, 0.66), g.F(-w - 0.04, 0.86), g.F(w + 0.04, 0.86), g.F(w + 0.07, 0.66), g.F(w + 0.03, 0.4)]), shade(P["hair"], 0.8), [], s=3)
    top = front_cap(g, f, 0.04, [(-w - 0.01, 0.44), (-w + 0.03, 0.3), (-w * 0.6, 0.17), (0, 0.14), (w * 0.6, 0.17), (w - 0.03, 0.3), (w + 0.01, 0.44)], top=-0.06)
    hair = cel(top, P["hair"], [line([g.F(-0.05, 0.02), g.F(-0.2, 0.2)], shade(P["hair"], 0.7), 1.3), line([g.F(0.05, 0.02), g.F(0.2, 0.2)], shade(P["hair"], 0.7), 1.3),
                                line([g.F(0.06, -0.02), g.F(0.28, 0.06)], light(P["hair"], 0.35), 2.0)], s=4, sw=2.8)
    fig.add(Z_HEAD, "head", head_front(g, f, hair_back=back, hair_mid=hair, hair_front=beard_front(g, f, P["hair"], bottom=1.04)))


look(id="hero_b", char="general_hero", letter="B", label="the knight who came back (breastplate, cape, standing watch on his sword)",
     H=185 * CM, hr=0.178, build=dict(shoulder=0.132, waist=0.084, hip=0.09, chest=0.076, back=0.072, limb=1.04, stance=0.05),
     P=dict(face=hero_b_face(), hair="#a87a44", cape="#2f4f8f", lining="#3a5a9a", shirt="#3a5a8f", sleeve="#3a5a8f", legs="#3a3640", shoe="#4a3022", shoe_kind="boot",
            steel="#aeb8c4", brass="#d4a944", grip="#4a2e22", blade="#d6dde4", bracer="#6b4430", hand_held={"near": True, "far": True, "right": True, "left": True}),
     pose=hero_b_pose, side=hero_b_side, front=hero_b_front)


# ---- C: the veteran ranger: field jacket, scarf, a sword on her back ------------------------

def hero_c_face():
    return dict(skin="#a8714e", nose=0.135, hook=0.014, droop=0.0, brow=0.025, lip=0.022, chin=0.03, w=0.35, jaw=0.82, chinw=0.4, cheek=1.0,
                brow_th=2.8, brow_c="#1f1714", brow_tilt=0.3, age=1, lids=1, lashes=1, iris="#3a2a20", nose_w=0.07, mouth_w=0.095, lipc="#7e4436")


def braid_side(g, hair, to_y):
    H = g.H
    out = []
    x0, y0 = g.Q(-0.82, 0.8)
    n = 7
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        ya, yb = y0 + (to_y - y0) * t0, y0 + (to_y - y0) * t1
        xa, xb = x0 - H * 0.01 * t0 * 3, x0 - H * 0.01 * t1 * 3
        r = 8.0 - 3.0 * t0
        out += cel(smooth([(xa - r, ya), (xa + r, ya + 2), (xb + r * 0.8, yb), (xb, yb + 3), (xb - r * 0.8, yb)]), hair, [], s=2, sw=2.4)
    out += cel(smooth([(x0 - H * 0.03 - 4, to_y + 2, True), (x0 - H * 0.03 + 4, to_y + 2, True), (x0 - H * 0.03 + 5, to_y + 16), (x0 - H * 0.03 - 5, to_y + 16)]), hair, [], s=2, sw=2.2)
    out += cel(rect(x0 - H * 0.03 - 5, to_y - 2, x0 - H * 0.03 + 5, to_y + 4, 1.5), "#2f7f86", [], s=1, sw=2.0)
    return out


def hero_c_side(fig):
    L, g = fig.L, fig.g
    P = L["P"]
    H = g.H
    body_side(fig, P)
    # the sword across her back: the scabbard behind her, the hilt up behind her near shoulder
    tip = (CX + H * 0.0, g.hip_y + H * 0.02)
    throat = (CX - H * 0.1, g.sh_y - H * 0.004)
    fig.add(Z_BACK, "scabbard", scabbard(throat, tip, 5.0, P["belt"], P["brass"]))
    fig.add(Z_BACK + 0.1, "hilt", sword_hilt(throat, ang(tip, throat), H * 0.06, 10, P["steel"], P["grip"]))
    fig.add(Z_BACK + 0.5, "braid", braid_side(g, P["hair"], g.waist_y - H * 0.02))
    # the field jacket to the hip, its belt, pockets and epaulette
    hem = g.crotch_y + H * 0.01
    d = smooth(coat_side(g, g.chin + H * 0.024, H * 0.01, hem, H * 0.078, H * 0.086))
    items = [path(smooth([(CX + H * 0.02, g.chest_y - H * 0.014, True), (CX + g.dchest + g.bust - H * 0.0, g.chest_y - H * 0.014, True), (CX + g.dchest + g.bust - H * 0.004, g.chest_y + H * 0.03, True),
                          (CX + H * 0.024, g.chest_y + H * 0.03, True)]), shade(P["jacket"], 0.9), INK, 1.4),
             path(smooth([(CX + H * 0.018, g.hip_y - H * 0.01, True), (CX + H * 0.074, g.hip_y - H * 0.01, True), (CX + H * 0.076, g.hip_y + H * 0.035, True), (CX + H * 0.02, g.hip_y + H * 0.035, True)]),
                  shade(P["jacket"], 0.9), INK, 1.4)]
    fig.add(Z_COAT, "jacket", cel(d, P["jacket"], items, s=7))
    fig.add(Z_COAT + 0.2, "medals", medal_row(CX + g.dchest - H * 0.024, g.chest_y - H * 0.04, 2, 0.9, 6.5, kinds=("disc", "cross")))
    fig.add(Z_BELT, "belt", belt_side(g, g.waist_y + H * 0.008, H * 0.012, P["belt"], P["brass"], CX + g.dchest * 0.92 + g.bust * 0.3 + H * 0.014, CX - g.dback * 0.9 - H * 0.012))
    # the baldric across her chest, a pouch on it
    bal = [(CX - g.dback * 0.6, g.sh_y + H * 0.004), (CX + g.dchest * 0.5, g.sh_y + H * 0.01), (CX + g.dchest + g.bust + H * 0.008, g.chest_y + H * 0.02), (CX + g.dchest * 0.8, g.waist_y - H * 0.006)]
    fig.add(Z_BELT + 0.3, "baldric", [line(bal, INK, 9.4), line(bal, P["belt"], 6.0)] + cel(rect(CX + g.dchest - H * 0.01, g.chest_y + H * 0.014, CX + g.dchest + g.bust + H * 0.016,
                                                                                                  g.chest_y + H * 0.05, 2), P["belt"], [], s=2))
    fig.add(Z_ARM + 0.05, "epaulette", cel(smooth([(CX - H * 0.03, g.sh_y + H * 0.002), (CX + H * 0.03, g.sh_y + H * 0.008), (CX + H * 0.03, g.sh_y + H * 0.02), (CX - H * 0.03, g.sh_y + H * 0.016)]),
                                           shade(P["jacket"], 0.85), [ellipse(CX + H * 0.022, g.sh_y + H * 0.012, 1.8, 1.8, P["brass"], INK, 0.8)], s=1.5, sw=2.4))
    fig.add(Z_NECK + 1, "scarf", scarf_band_side(g, P["scarf"]) + scarf_tail_side(g, P["scarf"], g.chest_y + H * 0.03, CX + g.dchest + H * 0.016))
    for side in ("near", "far"):
        s, e, w = g.s_arm[side]
        q = frame(w, ang(e, w))
        c = P["jacket"] if side == "near" else shade(P["jacket"], 0.84)
        fig.add((Z_ARM if side == "near" else Z_FARARM) + 0.2, f"{side}-cuff", cel(smooth([q(-H * 0.03, -H * 0.03), q(0, -H * 0.03), q(0, H * 0.03), q(-H * 0.03, H * 0.03)]), shade(c, 0.9), [], s=2))
    f = P["face"]
    hair = cap_hair_side(g, 124, 318, 0.03, [(-0.02, 0.15), (-0.1, 0.2), (-0.24, 0.24), (-0.36, 0.36), (-0.42, 0.5), (-0.5, 0.44), (-0.62, 0.5), (-0.7, 0.72), (-0.76, 0.86)], n=16)
    items = [line([g.Q(-0.06, 0.07), g.Q(-0.4, 0.0), g.Q(-0.78, 0.2)], light(P["hair"], 0.35), 2.0), line([g.Q(-0.14, 0.18), g.Q(-0.5, 0.2), g.Q(-0.8, 0.5)], shade(P["hair"], 0.7), 1.3)]
    fig.add(Z_HEAD, "head", head_side(g, f, hair_mid=cel(hair, P["hair"], items, s=4, sw=2.8), extra=[ellipse(*g.Q(-0.52, 0.72), 2.2, 2.2, P["brass"], INK, 1.0)]))


def hero_c_front(fig):
    L, g = fig.L, fig.g
    P = L["P"]
    H = g.H
    body_front(fig, P)
    # the hilt over her right shoulder, behind her
    fig.add(Z_BACK, "hilt", sword_hilt((CX - g.sw * 0.62, g.sh_y - H * 0.0), math.radians(-112), H * 0.06, 10, P["steel"], P["grip"]))
    hem = g.crotch_y + H * 0.01
    d = smooth(coat_front(g, g.chin + H * 0.024, H * 0.01, hem, g.hw + H * 0.016))
    items = [line([(CX + H * 0.004, g.sh_y + H * 0.02), (CX + H * 0.004, hem)], shade(P["jacket"], 0.6), 1.5)]
    for sgn in (-1, 1):
        items.append(path(smooth([(CX + sgn * H * 0.025, g.chest_y - H * 0.016, True), (CX + sgn * H * 0.075, g.chest_y - H * 0.016, True), (CX + sgn * H * 0.074, g.chest_y + H * 0.03, True),
                                  (CX + sgn * H * 0.026, g.chest_y + H * 0.03, True)]), shade(P["jacket"], 0.9), INK, 1.4))
        items.append(path(smooth([(CX + sgn * H * 0.03, g.hip_y - H * 0.012, True), (CX + sgn * H * 0.08, g.hip_y - H * 0.012, True), (CX + sgn * H * 0.08, g.hip_y + H * 0.035, True),
                                  (CX + sgn * H * 0.03, g.hip_y + H * 0.035, True)]), shade(P["jacket"], 0.9), INK, 1.4))
    items += buttons([(CX + H * 0.004, y) for y in (g.sh_y + H * 0.03, g.chest_y + H * 0.04)], 2.0, P["brass"])
    fig.add(Z_COAT, "jacket", cel(d, P["jacket"], items, s=7))
    fig.add(Z_COAT + 0.2, "medals", medal_row(CX + H * 0.034, g.chest_y - H * 0.048, 3, 0.85, 7.0, kinds=("disc", "cross", "star")))
    fig.add(Z_BELT, "belt", belt_front(g, g.waist_y + H * 0.008, H * 0.012, g.ww + H * 0.012, P["belt"], P["brass"], bw=H * 0.02))
    bal = [(CX - g.sw * 0.62, g.sh_y - H * 0.002), (CX - H * 0.01, g.chest_y + H * 0.01), (CX + g.ww + H * 0.006, g.waist_y - H * 0.004)]
    fig.add(Z_BELT + 0.3, "baldric", [line(bal, INK, 9.4), line(bal, P["belt"], 6.0)] + cel(rect(CX - H * 0.04, g.chest_y - H * 0.012, CX - H * 0.008, g.chest_y + H * 0.022, 2), P["belt"],
                                                                                            [ellipse(CX - H * 0.024, g.chest_y - H * 0.002, 1.6, 1.6, P["brass"], INK, 0.8)], s=2))
    for sgn in (-1, 1):
        fig.add(Z_ARM + 0.05, "epaulette", cel(smooth([(CX + sgn * H * 0.06, g.sh_y - H * 0.0), (CX + sgn * (g.sw - H * 0.004), g.sh_y + H * 0.012), (CX + sgn * (g.sw - H * 0.006), g.sh_y + H * 0.026),
                                                       (CX + sgn * H * 0.06, g.sh_y + H * 0.014)]), shade(P["jacket"], 0.85), [], s=1.5, sw=2.4))
        fig.add(Z_NECK + 0.5, "collar", cel(smooth([(CX + sgn * H * 0.03, g.chin - H * 0.006), (CX + sgn * H * 0.06, g.sh_y + H * 0.004), (CX + sgn * H * 0.03, g.sh_y + H * 0.03),
                                                    (CX + sgn * H * 0.004, g.sh_y + H * 0.01)]), P["jacket"], [], s=2))
    fig.add(Z_NECK + 1, "scarf", scarf_front(g, P["scarf"], H * 0.03, g.chest_y + H * 0.03))
    for side in ("right", "left"):
        s, e, w = g.f_arm[side]
        q = frame(w, ang(e, w))
        fig.add(Z_ARM + 0.2, f"{side}-cuff", cel(smooth([q(-H * 0.03, -H * 0.03), q(0, -H * 0.03), q(0, H * 0.03), q(-H * 0.03, H * 0.03)]), shade(P["jacket"], 0.9), [], s=2))
    f = P["face"]
    w = f["w"]
    top = front_cap(g, f, 0.03, [(-w - 0.01, 0.5), (-w + 0.02, 0.3), (-w * 0.6, 0.2), (-0.1, 0.16), (0.08, 0.12, True), (w * 0.5, 0.2), (w - 0.02, 0.3), (w + 0.01, 0.48)], top=-0.04)
    hair = cel(top, P["hair"], [line([g.F(0.08, 0.1), g.F(0.07, -0.02)], shade(P["hair"], 0.6), 1.3), line([g.F(-0.06, 0.02), g.F(-0.3, 0.1)], light(P["hair"], 0.35), 2.0)], s=4, sw=2.8)
    studs = [ellipse(*g.F(-w - 0.05, 0.68), 2.2, 2.2, P["brass"], INK, 1.0), ellipse(*g.F(w + 0.05, 0.68), 2.2, 2.2, P["brass"], INK, 1.0)]
    fig.add(Z_HEAD, "head", head_front(g, f, hair_mid=hair, extra=studs))


look(id="hero_c", char="general_hero", letter="C", label="the veteran ranger (field jacket, scarf, a sword across her back, medals)",
     H=185 * CM, hr=0.176, build=dict(shoulder=0.118, waist=0.074, hip=0.094, chest=0.064, back=0.064, bust=0.012, seat=0.006, limb=0.94, stance=0.046),
     P=dict(face=hero_c_face(), hair="#2a1d18", jacket="#7d4a32", sleeve="#7d4a32", shirt="#3a3c46", legs="#3a3c46", shoe="#3a2a20", shoe_kind="boot", boot_top=None,
            brass="#d4a944", belt="#4a3022", grip="#2a2220", steel="#b9c0c8", scarf="#2f7f86"),
     side=hero_c_side, front=hero_c_front)


# ============================================================================================
# the cast looks as rig parts
# ============================================================================================

#: The look Jon's cast wears, by character (2026-10-23).
CAST = {"vault_keeper": "keeper_c", "merchant_prototype": "merchant_b", "general_hero": "hero_b"}

#: A side-view layer's bone, by its name; any other layer is dress on the torso.
_BONES = {
    "thigh": "leg_u", "shin": "leg_l", "foot": "foot",
    "arm-upper": "arm_u", "pauldron": "arm_u", "arm-lower": "arm_l", "roll": "arm_l", "cuff": "arm_l", "bracer": "arm_l", "hand": "hand",
}
#: What the near hand holds turns with it.
_HELD = {"staff", "blade", "hilt"}


def layer_bone(name: str) -> str:
    if name in _HELD:
        return "near_hand"
    if name == "head":
        return "head"
    side, _, rest = name.partition("-")
    if side in ("near", "far") and rest in _BONES:
        return f"{side}_{_BONES[rest]}"
    return "torso"


def rig_joints(g: Geo) -> Dict[str, Tuple[str, float, float]]:
    """Where each bone of a posed figure turns: ``bone: (parent, x, y)``, parents first."""
    J = {
        "body": ("", CX, g.hip_y),
        "torso": ("body", CX, g.hip_y),
        "head": ("torso", CX + g.H * 0.006, g.chin + g.H * 0.012),
    }
    for side in ("near", "far"):
        s, e, w = g.s_arm[side]
        J[f"{side}_arm_u"] = ("torso", *s)
        J[f"{side}_arm_l"] = (f"{side}_arm_u", *e)
        J[f"{side}_hand"] = (f"{side}_arm_l", *w)
    for side in ("near", "far"):
        hip, knee, ankle = g.s_leg[side]
        J[f"{side}_leg_u"] = ("body", *hip)
        J[f"{side}_leg_l"] = (f"{side}_leg_u", *knee)
        J[f"{side}_foot"] = (f"{side}_leg_l", *ankle)
    return J


def rig_drawing(char: str) -> Dict:
    """The cast look's side view as rig parts: ``parts`` is ``(part, bone, z,
    body)`` back to front, ``joints`` the bones; ``svgkit`` is configured for
    ``svgkit.document``."""
    L = dict(LOOKS[CAST[char]])
    if char == "merchant_prototype":
        # Only her feet show under the skirt, and they swing in the walk: a
        # boot top at the ankle, so no shaft pokes out behind the hem.
        L["P"] = dict(L["P"], boot_top=GROUND - L["H"] * 0.075)
    fig = Fig(L, "side")
    if L.get("pose"):
        L["pose"](fig.g)
    _N[0] = 0
    svg.configure(dx=0, dy=0, ink=INK, ow=OUT / 2, colors={})
    L["side"](fig)
    fig.layers.sort(key=lambda q: q[0])
    parts = [(name.replace("-", "_"), layer_bone(name), z, items) for z, name, items in fig.layers]
    return {"parts": parts, "joints": rig_joints(fig.g), "label": L["label"], "height": L["H"]}


# ============================================================================================
# output: SVGs and the contact sheets
# ============================================================================================

SHEET_BG = (214, 219, 226, 255)
#: The game draws the General Hero (185 cm) about this many pixels tall.
GAME_PX = 96


def _font(size, bold=True):
    from PIL import ImageFont
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            pass
    return ImageFont.load_default()


def render(svg_text: str, zoom: float):
    """The SVG as an RGBA image (resvg, as the tool's other candidate sheets)."""
    import resvg_py
    from PIL import Image
    return Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_string=svg_text, zoom=zoom)))).convert("RGBA")


def _crop(im, zoom, box):
    x0, y0, x1, y1 = box
    return im.crop((int(x0 * zoom), int(y0 * zoom), int(x1 * zoom), int(y1 * zoom)))


def contact_sheet(char: str, out_png: Path, svgs: Dict[Tuple[str, str], str]) -> None:
    """One row per look: its label, the side figure, the front figure, the head
    close-up (side over front), the game-size previews (1x and 2x pixels)."""
    from PIL import Image, ImageDraw
    looks = [lid for lid, L in LOOKS.items() if L["char"] == char]
    fz, hz = 1.4, 2.4
    fig_box = (125, 92, 435, 508)
    rows = []
    for lid in looks:
        L = LOOKS[lid]
        g = Geo(L)
        side, front = svgs[(lid, "side")], svgs[(lid, "front")]
        a = _crop(render(side, fz), fz, fig_box)
        b = _crop(render(front, fz), fz, fig_box)
        hx = g.xf - g.hh * 0.42
        hy = g.crown - g.hh * 0.3
        hs = _crop(render(side, hz), hz, (hx - 60, hy, hx + 60, hy + 120))
        hf = _crop(render(front, hz), hz, (CX - 60, hy, CX + 60, hy + 120))
        gz = GAME_PX / (185 * CM)
        gs = _crop(render(side, gz), gz, fig_box)
        gf = _crop(render(front, gz), gz, fig_box)
        rows.append((L, a, b, hs, hf, gs, gf))
    lab_h, pad = 34, 18
    fw, fh = rows[0][1].size
    hw, hh = rows[0][3].size
    gw, gh = rows[0][5].size
    width = pad + fw + pad + fw + pad + hw + pad + (gw * 2 + 8) + pad + (gw * 4 + 12) + pad
    height = sum(lab_h + max(fh, hh * 2 + 8) + pad for _ in rows) + 46
    sheet = Image.new("RGBA", (width, height), SHEET_BG)
    dr = ImageDraw.Draw(sheet)
    dr.text((pad, 12), f"{CHARS[char]} - redesign candidates, round 1 (2026-10-22)   |   side (facing right) / front / heads / game size 1x + 2x", fill=(40, 36, 34), font=_font(18))
    y = 46
    for L, a, b, hs, hf, gs, gf in rows:
        dr.text((pad, y + 6), f"{L['letter']}: {L['label']}", fill=(29, 23, 20), font=_font(20))
        y += lab_h
        x = pad
        for im in (a, b):
            sheet.alpha_composite(im, (x, y))
            x += fw + pad
        sheet.alpha_composite(hs, (x, y))
        sheet.alpha_composite(hf, (x, y + hh + 8))
        x += hw + pad
        gy = y + max(fh, hh * 2 + 8) - gh
        sheet.alpha_composite(gs, (x, gy))
        sheet.alpha_composite(gf, (x + gw + 8, gy))
        x += gw * 2 + 8 + pad
        big = [im.resize((im.width * 2, im.height * 2), Image.NEAREST) for im in (gs, gf)]
        gy2 = y + max(fh, hh * 2 + 8) - big[0].height
        sheet.alpha_composite(big[0], (x, gy2))
        sheet.alpha_composite(big[1], (x + big[0].width + 12, gy2))
        y += max(fh, hh * 2 + 8) + pad
    out_png.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out_png)
    print(out_png)


def write_svgs(out: Path, ids) -> Dict[Tuple[str, str], str]:
    out.mkdir(parents=True, exist_ok=True)
    texts = {}
    for lid in ids:
        for view in ("side", "front"):
            t = draw(lid, view)
            texts[(lid, view)] = t
            p = out / f"{lid}_{view}.svg"
            p.write_text(t, encoding="utf8")
    return texts


def main() -> None:
    a = sys.argv[1:]
    if len(a) == 2 and a[0] == "--all":
        for (lid, view) in write_svgs(Path(a[1]), LOOKS):
            print(Path(a[1]) / f"{lid}_{view}.svg")
        return
    if len(a) == 2 and a[0] == "--sheets":
        out = Path(a[1])
        texts = write_svgs(out / "svg", LOOKS)
        for char in CHARS:
            contact_sheet(char, out / f"{char}_r1.png", texts)
        return
    if len(a) == 3 and a[0] == "--look":
        write_svgs(Path(a[2]), [a[1]])
        return
    raise SystemExit("usage: vault_merchant_hero_art.py --all DIR | --sheets DIR | --look ID DIR   (candidates only; nothing is cast)\n"
                     f"looks: {', '.join(LOOKS)}")


if __name__ == "__main__":
    main()
