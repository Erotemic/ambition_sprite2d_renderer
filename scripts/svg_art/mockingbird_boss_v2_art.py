#!/usr/bin/env python3
"""How the Mockingbird v2's SVG was first drawn (reference, not authority).

``data/characters/mockingbird_boss_v2/mockingbird_boss_v2.svg`` owns the art
and may have been edited since; this script reproduces the drawing as it was
first committed (less the rig catalog ``scripts/build_mockingbird_boss_v2_rig.py``
installs). Keep it as a worked example for drawing a MACHINE with ``svgkit``:
armour panels shaded inside their silhouettes, cylinders with rings and a
sheen, rotor blades as a swap set of spin states, and a glowing core seen
through a cage of ribs.

    uv run python scripts/svg_art/mockingbird_boss_v2_art.py OUT.svg

The design follows the mechanical "mockingbird" of the How to Kill a
Mockingbird Flash animation (Jon's reference, 2026-10-06), revised after his
first review: a lean black skull with a tall forehead, an overhanging brow, a
glowing slit eye and a long hooked beak of fangs over a slim jaw, on a
segmented steel neck; a cage of steel ribs round a glowing red engine-heart;
two armoured wings of blade feathers swept back over the hull, a missile slung
under each; two rotors on masts tall enough to clear the back spikes; a heavy
thruster at the tail and two grappling claws beneath.
Drawn facing right in a 1140x760 SVG (design units shifted by ``DX``, ``DY``).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import svgkit as svg
from svgkit import capsule, clipped, ellipse, ink, line, part, path, poly, smooth

W, H = 1140, 760
#: The design is drawn at x 100-925, y 30-440; shifted to leave room behind
#: it for the thruster's plume and above it to rear.
DX, DY = 120.0, 130.0
INK = "#0b0c10"
OW = 2.4  # half the silhouette ink width
LW = 1.6  # detail outline width

C = dict(
    armor="#262931",
    armor_hi="#3d424e",
    armor_lo="#17181d",
    sheen="#6b7383",
    seam="#101116",
    steel="#8e949e",
    steel_hi="#cfd4da",
    steel_lo="#5c616b",
    steel_dk="#41454d",
    core="#d8381a",
    core_hi="#ff8a3d",
    core_lo="#8f1f0e",
    core_hot="#ffd98a",
    eye="#ff5a14",
    eye_hi="#ffd27a",
    eye_glow="#ff7a2a",
    eye_off="#3a2c2a",
    tooth="#eeeae0",
    tooth_sh="#b8b2a3",
    mouth="#2c0b0b",
    mouth2="#561410",
    teal="#4f8f8a",
    teal_hi="#9fd8cf",
    hazard="#e2b630",
    hydraulic="#c2321c",
    stripe="#c9ced4",
    blade="#9aa1ab",
    blade_hi="#dde2e7",
)
FAR = dict(
    armor="#1d1f25",
    armor_hi="#2e323b",
    steel="#6f747d",
    steel_hi="#a3a8b0",
    steel_lo="#4a4e56",
    steel_dk="#34373e",
    hydraulic="#94261a",
    blade="#7d838c",
    blade_hi="#b9bec5",
)

# ---- joints ----------------------------------------------------------------
J = dict(
    body=(430.0, 200.0),
    neck1=(572.0, 182.0),
    neck2=(616.0, 190.0),
    head=(660.0, 196.0),
    snout=(936.0, 234.0),
    jaw=(704.0, 222.0),
    jaw_tip=(904.0, 232.0),
    engine=(300.0, 232.0),
    engine_tip=(118.0, 236.0),
    near_rotor=(574.0, 132.0),
    near_hub=(574.0, -16.0),
    far_rotor=(318.0, 124.0),
    far_hub=(318.0, 4.0),
    near_wing=(516.0, 146.0),
    near_wing_wrist=(410.0, 74.0),
    near_wing_tip=(150.0, 30.0),
    far_wing=(500.0, 130.0),
    far_wing_wrist=(402.0, 56.0),
    far_wing_tip=(170.0, 6.0),
    near_shoulder=(486.0, 276.0),
    near_elbow=(528.0, 334.0),
    near_wrist=(578.0, 364.0),
    near_tip=(612.0, 404.0),
    far_shoulder=(420.0, 272.0),
    far_elbow=(458.0, 326.0),
    far_wrist=(506.0, 356.0),
    far_tip=(540.0, 394.0),
)


def col(far):
    return {**C, **FAR} if far else C


def shaded(cid, sil, base, lo, hi, lo_pts=None, hi_pts=None, extra=()):
    """A panel: its fill, a shadow band and a highlight band clipped inside
    the silhouette, then any extra detail, then its own outline."""
    items = [path(sil, base)]
    if lo_pts:
        items.append(path(smooth(lo_pts), lo))
    if hi_pts:
        items.append(path(smooth(hi_pts), hi))
    items += list(extra)
    return clipped(cid, sil, items) + [path(sil, "none", INK, LW)]


def rivets(pts, r=2.2, fill=None):
    return [ellipse(x, y, r, r, fill or C["steel_hi"], INK, 0.8) for x, y in pts]


def cylinder(cid, a, b, r, c, rings=(), cap=True):
    """A steel cylinder from a to b (radius r): a sheen along its upper third,
    a shadow along its lower edge, rings across it and an end cap at b."""
    ax, ay = a
    bx, by = b
    d = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / d, (by - ay) / d
    nx, ny = -uy, ux
    sil = poly([(ax + nx * r, ay + ny * r), (bx + nx * r, by + ny * r), (bx - nx * r, by - ny * r),
                (ax - nx * r, ay - ny * r)])

    def off(t, k):
        return (ax + ux * d * t + nx * r * k, ay + uy * d * t + ny * r * k)

    # The top of a cylinder is on its -n side when it points right (y down).
    items = [path(sil, c["steel"]),
             path(poly([off(0, 1.1), off(1, 1.1), off(1, 0.45), off(0, 0.45)]), c["steel_lo"]),
             path(poly([off(0, -0.75), off(1, -0.75), off(1, -0.35), off(0, -0.35)]), c["steel_hi"])]
    for t in rings:
        p0, p1 = off(t, -1.1), off(t, 1.1)
        items.append(line([p0, p1], c["steel_dk"], 3.2))
        items.append(line([off(t + 0.012, -1.1), off(t + 0.012, 1.1)], c["steel_hi"], 1.0))
    body = clipped(cid, sil, items) + [path(sil, "none", INK, LW)]
    if cap:
        ang = math.degrees(math.atan2(uy, ux))
        body.append(ellipse(bx, by, r * 0.32, r, c["steel_lo"], INK, LW, rot=ang))
    return sil, body


# ---- the far side (behind the body) -------------------------------------------
def blades(name, bone, z, hub, span, far, extra_label):
    """A rotor's blades as a swap set: seen from the side a spinning pair
    reads as full length, then foreshortened with its tips swinging round."""
    c = col(far)
    hx, hy = hub
    states = (
        ("a", [(-span, 3.0, 7.0), (span, -3.0, 7.0)]),
        ("b", [(-span * 0.62, 12.0, 8.0), (span * 0.62, -12.0, 8.0)]),
        ("c", [(-span * 0.62, -12.0, 8.0), (span * 0.62, 12.0, 8.0)]),
    )
    for key, tips in states:
        items = []
        for tx, ty, w in tips:
            tip = (hx + tx, hy + ty)
            s = 1 if tx > 0 else -1
            pts = [(hx, hy - 3, True), (hx + tx * 0.5, hy + ty * 0.5 - w * 0.6), (tip[0] - s * 6, tip[1] - w * 0.5),
                   (tip[0], tip[1], True), (tip[0] - s * 6, tip[1] + w * 0.5), (hx + tx * 0.5, hy + ty * 0.5 + w * 0.5),
                   (hx, hy + 3, True)]
            items.append(path(smooth(pts), c["blade"], INK, 1.2))
            items.append(line([(hx + tx * 0.15, hy + ty * 0.15 - 1), (hx + tx * 0.92, hy + ty * 0.92 - 1)], c["blade_hi"], 1.1))
            items.append(line([(tip[0] - s * 14, tip[1] - w * 0.4), (tip[0] - s * 8, tip[1] + w * 0.4)], c["hazard"], 2.2))
        items.append(ellipse(hx, hy, 14, 8, c["steel_lo"], INK, 1.4))
        items.append(ellipse(hx, hy - 2, 8, 3.6, c["steel_hi"]))
        default = ' data-rig-default="1"' if key == "a" else ""
        part(f"{name.replace('_', '-')}-{key}", f"{extra_label} - {key}", f"{name}_{key}", bone, z,
             items, f' data-rig-opacity="{name}.{key}"{default}')


def far_rotor_parts():
    c = col(True)
    hx, hy = J["far_hub"]
    sil, body = cylinder("clip-far-mast", (hx, J["far_rotor"][1] + 4), (hx, hy + 8), 10.0, c, rings=(0.25, 0.5, 0.75), cap=False)
    body.append(ellipse(hx, hy + 8, 14, 6, c["steel_lo"], INK, LW))
    body.append(ellipse(hx, hy + 5, 10, 4, c["steel"], INK, 1.0))
    part("far-rotor-mast", "Far Rotor Mast", "far_rotor_mast", "far_rotor", 6, body)
    blades("far_rotor", "far_rotor", 7, (hx, hy), 150.0, True, "Far Rotor Blades")


def missile(name, a, b, r, c):
    """A missile from its tail ``a`` to its nose ``b``: a steel body with
    rings, a hazard band, tail fins and a teal warhead with a pale tip."""
    ax, ay = a
    bx, by = b
    d = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / d, (by - ay) / d
    nx, ny = -uy, ux

    def L(t, k):
        return (ax + ux * t + nx * k, ay + uy * t + ny * k)

    items = []
    for s_ in (-1, 1):
        items.append(path(smooth([L(30, s_ * r * 0.7) + (True,), L(-4, s_ * r * 2.0) + (True,), L(4, s_ * r * 0.7) + (True,)]),
                          c["steel_lo"], INK, 1.2))
    wh = d - 2.6 * r
    _, body = cylinder(f"clip-{name}", a, L(wh, 0), r, c, rings=(0.12, 0.7), cap=False)
    items += body
    band = poly([L(wh * 0.38, -r), L(wh * 0.5, -r), L(wh * 0.5, r), L(wh * 0.38, r)])
    items.append(path(band, C["hazard"], INK, 0.8))
    for k in range(3):
        t0 = wh * (0.38 + 0.04 * k)
        items.append(line([L(t0 + 2, -r), L(t0 - 2, r)], C["armor_lo"], 2.0))
    head = smooth([L(wh, -r) + (True,), L(wh + r * 1.4, -r * 0.8), L(d, 0) + (True,), L(wh + r * 1.4, r * 0.8),
                   L(wh, r) + (True,)])
    items.append(path(head, C["teal"], INK, LW))
    items.append(path(smooth([L(wh + 2, -r * 0.7) + (True,), L(wh + r * 1.4, -r * 0.55), L(d - 4, -1) + (True,),
                              L(wh + r * 1.2, -r * 0.15), L(wh + 2, -r * 0.2) + (True,)]), C["teal_hi"]))
    items.append(line([L(wh, -r), L(wh, r)], c["steel_dk"], 2.6))
    return items


def wing_parts(side):
    """A mechanical wing swept back over the hull: a steel spar in two bones
    (``<side>_wing`` to the wrist, ``<side>_wing_tip`` beyond it), blade
    feathers hanging off it whose tips make a stepped trailing edge (the
    primaries off the outer bone, the secondaries off the inner), an armour
    covert strip over their roots, and a missile slung under the inner wing."""
    far = side == "far"
    c = col(far)
    z0 = 3.5 if far else 54
    R, Wr, T = J[f"{side}_wing"], J[f"{side}_wing_wrist"], J[f"{side}_wing_tip"]

    def at(a, b, t):
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

    def blade(base, tip, width, fill, cid):
        bx, by = base
        tx, ty = tip
        d = math.hypot(tx - bx, ty - by)
        ux, uy = (tx - bx) / d, (ty - by) / d
        nx, ny = -uy, ux
        w = width / 2

        def L(t, k):
            return (bx + ux * d * t + nx * w * k, by + uy * d * t + ny * w * k)

        pts = [L(0, -1) + (True,), L(0.55, -1.05), L(0.86, -0.7), tip + (True,), L(0.8, 0.85), L(0.4, 1.0),
               L(0, 1) + (True,)]
        sil = smooth(pts)
        items = [path(sil, fill), path(smooth([L(0, 0.15), L(0.6, 0.2), L(0.92, 0.05), L(0.75, 1.0), L(0, 1.2)]),
                                       c["armor_lo"]),
                 line([L(0.05, -0.55), L(0.8, -0.4)], c["steel"], 1.6)]
        return clipped(cid, sil, items) + [path(sil, "none", INK, LW)]

    def feathers(name, a, b, n, ang0, ang1, len0, len1, width, t0=0.0, t1=1.0):
        out = []
        for k in range(n):
            u = k / max(1, n - 1)
            base = at(a, b, t0 + (t1 - t0) * u)
            ang = math.radians(ang0 + (ang1 - ang0) * u)
            L = len0 + (len1 - len0) * u
            tip = (base[0] + math.cos(ang) * L, base[1] + math.sin(ang) * L)
            fill = c["armor_hi"] if k % 2 else c["armor"]
            out.append(blade(base, tip, width, fill, f"clip-{side}-{name}-{k}"))
        return out

    # -- the outer wing: primaries, the outermost (longest, most swept) first.
    prim = feathers("primary", Wr, T, 7, 140, 172, 96, 150, 32, t0=0.04, t1=0.96)
    outer = [x for f in reversed(prim) for x in f]
    spar = capsule(Wr, T, 9.0, 4.5)
    outer.append(path(spar, c["steel"], INK, LW))
    outer.append(line([at(Wr, T, 0.02), at(T, Wr, 0.04)], c["steel_hi"], 2.0))
    for t in (0.3, 0.6):
        p0 = at(Wr, T, t)
        outer.append(line([(p0[0], p0[1] - 7), (p0[0] + 1, p0[1] + 7)], c["steel_dk"], 2.6))
    part(f"{side}-wing-tip", f"Wing Tip - {side}", f"{side}_wing_tip", f"{side}_wing_tip", z0 - 0.4, outer)

    # -- the inner wing: secondaries, a covert strip over their roots, the spar.
    sec = feathers("secondary", Wr, R, 5, 142, 124, 112, 70, 34, t0=0.0, t1=0.85)
    inner = [x for f in sec for x in f]
    cov = smooth([at(R, Wr, -0.05) + (True,), at(R, Wr, 1.05) + (True,), (Wr[0] + 6, Wr[1] + 30),
                  (R[0] - 30, R[1] + 26), (R[0] + 8, R[1] + 16, True)])
    cov_items = [path(cov, c["armor"]), line([(Wr[0] + 10, Wr[1] + 22), (R[0] - 24, R[1] + 20)], c["armor_lo"], 8.0),
                 line([(Wr[0] + 8, Wr[1] + 6), (R[0] - 4, R[1] + 2)], c["armor_hi"], 4.0)]
    cov_items += rivets([at(R, Wr, t) for t in (0.25, 0.5, 0.75)], 1.8, c["steel"])
    inner += clipped(f"clip-{side}-coverts", cov, cov_items) + [path(cov, "none", INK, LW)]
    _, sp = cylinder(f"clip-{side}-wing-spar", R, Wr, 9.0, c, rings=(0.35, 0.7), cap=False)
    inner += sp
    inner.append(line([(R[0] - 4, R[1] + 8), at(R, Wr, 0.5)], c["hydraulic"], 3.4))
    # a hooked thumb spike at the wrist
    inner.append(path(smooth([(Wr[0] + 10, Wr[1] - 6, True), (Wr[0] + 24, Wr[1] - 30), (Wr[0] + 38, Wr[1] - 40, True),
                              (Wr[0] + 16, Wr[1] - 24), (Wr[0] - 4, Wr[1] - 8, True)]), c["armor"], INK, LW))
    inner.append(ellipse(Wr[0], Wr[1], 11, 11, c["steel_lo"], INK, LW))
    inner.append(ellipse(Wr[0], Wr[1], 4, 4, c["hydraulic"], INK, 0.8))
    inner.append(ellipse(R[0], R[1], 15, 15, c["steel_lo"], INK, LW))
    inner.append(ellipse(R[0], R[1], 6, 6, c["steel_hi"], INK, 0.8))
    part(f"{side}-wing", f"Wing - {side}", f"{side}_wing", f"{side}_wing", z0, inner)

    # -- the missile, slung under the inner wing on a pylon.
    pyl = at(R, Wr, 0.3)
    m_tail, m_nose = (R[0] - 150, R[1] + 52), (R[0] + 100, R[1] + 38)
    drop = (pyl[0] - 4, R[1] + 32)
    mis = [line([pyl, drop], INK, 11.0), line([pyl, drop], c["steel_lo"], 6.4)]
    mis += missile(f"{side}-missile", m_tail, m_nose, 13.0, c)
    part(f"{side}-missile", f"Missile - {side}", f"{side}_missile", f"{side}_wing", z0 + 0.6, mis)


def claw_parts(side):
    far = side == "far"
    c = col(far)
    z0 = 9 if far else 60
    sh, el, wr, tip = (J[f"{side}_{k}"] for k in ("shoulder", "elbow", "wrist", "tip"))
    # The upper arm: a steel strut with a red hydraulic ram along it.
    _, upper = cylinder(f"clip-{side}-arm", sh, el, 8.5, c, rings=(0.5,), cap=False)
    upper.append(line([(sh[0] + 8, sh[1] - 2), (el[0] + 6, el[1] - 12)], c["hydraulic"], 4.0))
    upper.append(line([(sh[0] + 8, sh[1] - 2), ((sh[0] + el[0]) / 2 + 8, (sh[1] + el[1]) / 2 - 6)], c["steel_hi"], 2.0))
    upper.append(ellipse(sh[0], sh[1], 12, 12, c["steel_lo"], INK, LW))
    upper.append(ellipse(sh[0], sh[1], 5, 5, c["steel_hi"], INK, 0.8))
    part(f"{side}-arm", f"Claw Arm - {side}", f"{side}_arm", f"{side}_arm", z0, upper)
    _, fore = cylinder(f"clip-{side}-fore", el, wr, 7.0, c, rings=(0.35, 0.7), cap=False)
    fore.append(ellipse(el[0], el[1], 10, 10, c["steel_lo"], INK, LW))
    fore.append(ellipse(el[0], el[1], 4, 4, c["hydraulic"], INK, 0.8))
    part(f"{side}-fore", f"Claw Forearm - {side}", f"{side}_fore", f"{side}_fore", z0 + 0.5, fore)
    # The grapple: a palm and three hooked talons, open or shut.
    wx, wy = wr
    dx, dy = tip[0] - wx, tip[1] - wy
    d = math.hypot(dx, dy)
    ux, uy = dx / d, dy / d
    nx, ny = -uy, ux

    def L(a, b):
        return (wx + ux * a + nx * b, wy + uy * a + ny * b)

    for state, spread in (("open", 1.0), ("shut", 0.0)):
        items = []
        palm = smooth([L(-8, -14), L(16, -18), L(26, 0), L(16, 18), L(-8, 14)])
        for k, side_off in enumerate((-1, 0, 1)):
            # each talon: out from the palm, then hooked back inward
            fan = side_off * (34 * spread + 5)
            reach = 68 - abs(side_off) * 8
            base = L(16, side_off * 7)
            mid = L(16 + reach * 0.55, side_off * 7 + fan * 0.9)
            end = L(16 + reach * (0.8 + 0.1 * (1 - spread)), side_off * 7 + fan * 0.55 - side_off * 14 * (1 - spread) * 0.6
                    - (8 if side_off == 0 else 0) * spread)
            hook = L(16 + reach * (0.66 + 0.1 * (1 - spread)), side_off * 7 + fan * 0.2 - side_off * 6 - (12 if side_off == 0 else 0))
            pts = [base + (True,), mid, end + (True,), hook + (True,), L(16 + reach * 0.5, side_off * 7 + fan * 0.6 - side_off * 3),
                   L(16, side_off * 7 - 4 * (1 if side_off >= 0 else -1)) + (True,)]
            items.append(path(smooth(pts), c["steel"], INK, 1.6))
            items.append(line([L(18, side_off * 7), mid], c["steel_hi"], 1.4))
            items.append(ellipse(*L(16 + reach * 0.55, side_off * 7 + fan * 0.9), 2.4, 2.4, c["hydraulic"], INK, 0.6))
        items.append(path(palm, c["steel_lo"], INK, LW))
        items.append(ellipse(wx, wy, 8, 8, c["steel_dk"], INK, LW))
        items.append(ellipse(wx, wy, 3, 3, c["steel_hi"]))
        default = ' data-rig-default="1"' if state == "open" else ""
        part(f"{side}-claw-{state}", f"Claw - {side} {state}", f"{side}_claw_{state}", f"{side}_claw", z0 + 1, items,
             f' data-rig-opacity="{side}_claw.{state}"{default}')


# ---- the body ------------------------------------------------------------------
# The armoured back, nose (at the neck) to tail, along the top and then the
# underside (the ribs and the core hang beneath it).
BACK = [(596, 176), (590, 152), (566, 130), (520, 114), (460, 106), (400, 106), (340, 112), (290, 124), (246, 140),
        (210, 160, True), (190, 196, True), (240, 204), (300, 202), (360, 196), (420, 192), (480, 192), (540, 194),
        (586, 196, True)]
CORE_C = (432.0, 238.0)


def hook(base, lean, size, c):
    """A hooked black spine curving back off the armour."""
    bx, by = base
    pts = [(bx + 10 * size, by + 4, True), (bx + 6 * size, by - 18 * size), (bx - 4 * size, by - 34 * size),
           (bx - 18 * size + lean, by - 40 * size, True), (bx - 8 * size, by - 26 * size), (bx - 4 * size, by - 12 * size),
           (bx - 10 * size, by + 4, True)]
    return [path(smooth(pts), c["armor"], INK, LW),
            line([(bx + 3 * size, by - 6 * size), (bx - 2 * size, by - 26 * size), (bx - 12 * size + lean * 0.6, by - 36 * size)],
                 c["sheen"], 1.6)]


def body_parts():
    c = C
    # The cage: ribs round the glowing core, the core beneath them.
    cx, cy = CORE_C
    core_sil = smooth([(cx - 120, cy - 22), (cx - 92, cy - 50), (cx - 30, cy - 62), (cx + 40, cy - 60), (cx + 104, cy - 44),
                       (cx + 132, cy - 10), (cx + 118, cy + 30), (cx + 70, cy + 54), (cx, cy + 62), (cx - 70, cy + 54),
                       (cx - 112, cy + 24)])
    core_items = [path(core_sil, c["core"])]
    # the glow: hot in the middle, darker toward the rim
    core_items.append(path(smooth([(cx - 120, cy + 30), (cx - 60, cy + 62), (cx + 60, cy + 62), (cx + 130, cy + 20),
                                   (cx + 140, cy + 80), (cx - 130, cy + 80)]), c["core_lo"]))
    core_items.append(ellipse(cx + 6, cy - 4, 74, 30, c["core_hi"]))
    core_items.append(ellipse(cx + 12, cy - 10, 40, 14, c["core_hot"]))
    # turbine bands: the core is a ribbed bladder
    for k in range(-4, 5):
        x = cx + k * 26
        core_items.append(line([(x - 6, cy - 70), (x + 4, cy), (x - 6, cy + 70)], c["core_lo"], 3.2))
        core_items.append(line([(x - 1, cy - 50), (x + 7, cy - 4)], c["core_hi"], 1.4))
    core = clipped("clip-core", core_sil, core_items) + [path(core_sil, "none", INK, LW)]
    ink("core", "body", 20, core_sil)
    part("core", "Core", "core", "body", 28, core)

    # The ribs: steel, curving out of the hull, round under the core and in.
    ribs = []
    for k in range(6):
        x0 = 330 + k * 42
        lean = (k - 2.5) * 6
        depth = 68 - abs(k - 2.6) * 7
        pts = [(x0, 194), (x0 + 14 + lean * 0.4, cy - 14), (x0 + 8 + lean, cy + depth * 0.62), (x0 - 12 + lean, cy + depth * 0.88),
               (x0 - 30 + lean * 0.8, cy + depth * 0.7)]
        ribs.append(line(pts, INK, 12.0))
        ribs.append(line(pts, c["steel"], 7.4))
        ribs.append(line(pts[:3], c["steel_hi"], 2.4))
        ribs.append(ellipse(pts[-1][0], pts[-1][1], 4.2, 4.2, c["steel_lo"], INK, 1.0))
    # a keel under the ribs, nose to tail, that the claws hang from
    keel = [(310, 262), (380, 284), (450, 290), (520, 280), (580, 248)]
    ribs.append(line(keel, INK, 11))
    ribs.append(line(keel, c["steel_lo"], 6.4))
    ribs.append(line(keel[:4], c["steel"], 2.0))
    part("ribs", "Ribs", "ribs", "body", 36, ribs)

    # The hull: armoured back with panel seams, rivets and hooked spines.
    sil = smooth(BACK)
    ink("hull", "body", 21, sil)
    spines = []
    for i, (x, s) in enumerate(((548, 1.0), (522, 1.15))):
        y = 116 if 360 < x < 540 else 122
        if x > 540:
            y = 128
        spines += hook((x, y + 4), 2.0 * i, s, c)
    part("spines", "Back Spines", "spines", "body", 16, spines)
    lo = [(600, 160), (520, 160), (440, 154), (360, 158), (280, 168), (200, 182), (190, 240), (600, 240)]
    hi = [(560, 124), (500, 112), (430, 108), (360, 112), (300, 122), (270, 132), (300, 132), (360, 124), (430, 120),
          (500, 124), (556, 136)]
    seams = [line([(512, 116), (500, 154), (506, 192)], C["seam"], 2.0),
             line([(404, 108), (398, 150), (404, 192)], C["seam"], 2.0),
             line([(300, 124), (296, 160), (304, 200)], C["seam"], 2.0),
             line([(216, 162), (300, 166), (420, 160), (540, 164), (594, 170)], C["seam"], 1.6)]
    seams += rivets([(520, 178), (480, 176), (440, 176), (400, 176), (360, 178), (320, 180), (280, 182), (240, 186)], 2.0,
                    C["steel"])
    # a hazard chevron and a red marker light on the flank
    seams.append(path(poly([(232, 172), (262, 172), (252, 186), (222, 186)]), C["hazard"], INK, 1.0))
    seams.append(path(poly([(240, 172), (248, 172), (238, 186), (230, 186)]), C["armor_lo"]))
    seams.append(ellipse(560, 168, 5, 5, C["eye"], INK, 1.0))
    seams.append(ellipse(559, 166.5, 2, 2, C["eye_hi"]))
    part("hull", "Hull", "hull", "body", 34,
         shaded("clip-hull", sil, c["armor"], c["armor_lo"], c["armor_hi"], lo, hi, seams))


def engine_part():
    c = C
    a, b = J["engine"], J["engine_tip"]
    # A strut from the hull, then a fat cylinder with a nozzle at the back.
    strut = smooth([(300, 196, True), (316, 226), (300, 252, True), (262, 250), (244, 214, True)])
    items = [path(strut, c["armor"], INK, LW)]
    sil, body = cylinder("clip-engine", (a[0] + 6, a[1]), (b[0] + 34, b[1]), 32.0, c, rings=(0.12, 0.42, 0.72, 0.8), cap=False)
    items += body
    # intake at the front
    items.append(ellipse(a[0] + 6, a[1], 11, 32, c["steel_lo"], INK, LW))
    items.append(ellipse(a[0] + 8, a[1], 6, 24, c["armor_lo"]))
    # hazard band
    hb = poly([(196, 202), (214, 202), (214, 268), (196, 268)])
    band = poly([(194, 196), (218, 196), (218, 274), (194, 274)])
    items += clipped("clip-engine-band", sil, clipped("clip-engine-band-box", band, [path(hb, C["hazard"])] +
                     [line([(186 + k * 9, 270), (200 + k * 9, 198)], C["armor_lo"], 3.4) for k in range(0, 5)]))
    items.append(path(sil, "none", INK, LW))
    # nozzle: a flared bell with a dark throat
    nx0 = b[0] + 34
    bell = smooth([(nx0, b[1] - 30, True), (b[0] + 6, b[1] - 38), (b[0] - 4, b[1] - 40, True), (b[0] - 4, b[1] + 40, True),
                   (b[0] + 6, b[1] + 38), (nx0, b[1] + 30, True)])
    items.append(path(bell, c["steel_lo"], INK, LW))
    items.append(line([(nx0 - 2, b[1] - 28), (b[0] + 2, b[1] - 36)], c["steel_hi"], 2.0))
    items.append(ellipse(b[0] - 4, b[1], 11, 40, c["steel_dk"], INK, LW))
    items.append(ellipse(b[0] - 5, b[1], 7, 30, c["core_lo"]))
    items.append(ellipse(b[0] - 5, b[1], 3.6, 18, c["core_hi"]))
    ink("engine", "engine", 19, sil)
    part("engine", "Thruster", "engine", "engine", 26, items)


def neck_parts():
    c = C
    for name, a, b, z in (("neck1", J["neck1"], J["neck2"], 30), ("neck2", J["neck2"], J["head"], 31)):
        sil, body = cylinder(f"clip-{name}", (a[0] - 18, a[1] - 1), (b[0] + 8, b[1]), 15.0, c, rings=(), cap=False)
        # vertebra collars: steel discs standing proud of the core
        for t in (0.15, 0.55, 0.95):
            x = a[0] - 18 + (b[0] + 26 - a[0]) * t
            y = a[1] + (b[1] - a[1]) * t
            body.append(ellipse(x, y, 7.5, 22, c["steel_lo"], INK, LW, rot=10))
            body.append(ellipse(x - 1.5, y - 2, 3.2, 17, c["steel_hi"], rot=10))
        ink(name, name, 22, sil)
        part(name, f"Neck {name[-1]}", name, name, z, body)


# The skull: back of the dome, over the brow, down the snout to its tip,
# then back along the mouth line (the jaw is its own part).
SKULL = [(648, 208), (648, 172), (660, 136), (684, 106), (718, 88), (758, 84), (792, 94), (812, 112), (818, 132, True),
         (846, 154), (880, 176), (912, 200), (934, 224), (940, 246, True), (926, 234), (906, 226, True), (866, 222),
         (826, 220), (786, 220), (746, 222), (718, 226, True), (688, 228), (662, 222)]
JAW = [(696, 216), (712, 228, True), (760, 230), (820, 228), (870, 228), (906, 232, True), (900, 240), (868, 246),
       (820, 252), (770, 256), (732, 256), (708, 248), (696, 234)]
EYE = (798.0, 150.0)


def mouth_part():
    c = C
    inside = smooth([(712, 226, True), (780, 222), (860, 222), (912, 230, True), (892, 244), (820, 250), (760, 252),
                     (724, 246)])
    part("mouth", "Mouth", "mouth", "head", 40,
         [path(inside, c["mouth"]), line([(730, 240), (800, 244), (870, 238)], c["mouth2"], 4.0)])


def tooth(x, y, h, w, down=True, fill=None):
    s = 1 if down else -1
    pts = [(x - w / 2, y, True), (x - w * 0.12, y + s * h * 0.6), (x + w * 0.1, y + s * h, True),
           (x + w * 0.4, y + s * h * 0.45), (x + w / 2, y, True)]
    return path(smooth(pts), fill or C["tooth"], INK, 1.1)


def jaw_part():
    """A slim lower mandible: a row of fangs along its top and a short comb of
    saw teeth raking off the chin."""
    c = C
    sil = smooth(JAW)
    ink("jaw", "jaw", 23, sil)
    lo = [(700, 244), (760, 246), (830, 242), (906, 236), (906, 270), (700, 270)]
    hi = [(714, 232), (770, 233), (840, 232), (900, 234), (890, 238), (840, 237), (770, 238), (716, 238)]
    extra = [line([(722, 246), (780, 248), (850, 242), (890, 238)], C["seam"], 1.4)]
    teeth = [tooth(x, 230 + (x - 730) * 0.01, 12 - abs(x - 810) * 0.03, 7, down=False) for x in range(732, 896, 12)]
    beard = []
    chin = [(898, 240), (868, 247), (820, 253), (772, 257)]
    segs = list(zip(chin, chin[1:]))
    for k in range(7):
        u = k / 6 * len(segs)
        i = min(len(segs) - 1, int(u))
        (x0, y0), (x1, y1) = segs[i]
        t = u - i
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        h = 13 - 5 * (k / 6)
        beard.append(path(smooth([(x - 5, y - 3, True), (x + 6, y + h, True), (x + 6, y - 3, True)]), C["tooth"], INK, 1.0))
    body = teeth + shaded("clip-jaw", sil, c["armor"], c["armor_lo"], c["armor_hi"], lo, hi, extra) + beard
    part("jaw", "Lower Jaw", "jaw", "jaw", 42, body)


def head_part():
    """A lean skull: a tall domed forehead, an overhanging brow, and a long
    snout tapering to a hooked beak lined with fangs."""
    c = C
    sil = smooth(SKULL)
    ink("head", "head", 24, sil)
    lo = [(650, 206), (720, 204), (800, 200), (880, 206), (944, 216), (944, 252), (640, 252)]
    hi = [(668, 132), (696, 102), (736, 90), (776, 94), (804, 112), (788, 110), (752, 104), (716, 110), (688, 134)]
    extra = [
        # the cranium's plate seam and rivets
        line([(664, 186), (676, 140), (704, 112), (740, 100)], C["seam"], 1.8),
        line([(700, 176), (760, 182), (806, 180)], C["seam"], 1.6),
        line([(836, 186), (880, 200), (918, 224)], C["seam"], 1.6),
        ellipse(900, 206, 4.0, 2.2, C["seam"], rot=30),
        # a cheek vent: three slots
        *[line([(712 + 10 * k, 196), (720 + 10 * k, 212)], c["armor_lo"], 3.0) for k in range(3)],
    ]
    extra += rivets([(684, 168), (694, 146), (712, 128)], 2.0, C["steel"])
    teeth = [tooth(x, 222 + (x - 720) * 0.006, 15 - abs(x - 810) * 0.03, 8, down=True) for x in range(724, 904, 12)]
    # The brow: an armour plate jutting over the eye, angled down at the front.
    brow = path(smooth([(752, 128, True), (812, 130), (838, 146, True), (812, 144), (764, 142)]), c["armor_lo"], INK, 1.2)
    body = shaded("clip-head", sil, c["armor"], c["armor_lo"], c["armor_hi"], lo, hi, extra) + teeth + [brow]
    part("head", "Head", "head", "head", 44, body)


def eye_parts():
    x, y = EYE
    socket = path(smooth([(x - 26, y - 6, True), (x + 4, y - 2), (x + 30, y + 6, True), (x + 6, y + 10), (x - 20, y + 4)]),
                  C["armor_lo"], INK, 1.2)

    def slit(w, h, fill, rim=None):
        pts = [(x - 22 * w, y - 4 * h, True), (x + 4 * w, y - 1 * h), (x + 26 * w, y + 6 * h, True),
               (x + 4 * w, y + 5 * h), (x - 16 * w, y + 2 * h)]
        return path(smooth(pts), fill, rim or INK, 1.0)

    open_ = [socket, slit(1.0, 1.0, C["eye"]), slit(0.6, 0.5, C["eye_hi"], C["eye"]), ellipse(x + 6, y + 3, 2.6, 1.8, "#fff6dc")]
    angry = [socket, slit(1.05, 0.6, C["eye"]), slit(0.7, 0.3, C["eye_hi"], C["eye"]),
             path(smooth([(x - 30, y - 12, True), (x + 34, y + 2, True), (x + 34, y - 10, True)]), C["armor"], INK, 1.0)]
    shut = [socket, line([(x - 22, y - 2), (x + 4, y + 2), (x + 26, y + 6)], C["eye_off"], 3.6),
            line([(x - 20, y - 1), (x + 24, y + 6)], C["eye"], 1.0)]
    dead = [socket, slit(1.0, 1.0, C["eye_off"]), line([(x - 8, y - 4), (x + 8, y + 8)], C["steel_lo"], 2.0),
            line([(x - 8, y + 8), (x + 8, y - 4)], C["steel_lo"], 2.0)]
    part("eye-open", "Eye - Open", "eye_open", "head", 46, open_, ' data-rig-opacity="eye.open" data-rig-default="1"')
    part("eye-angry", "Eye - Angry", "eye_angry", "head", 46, angry, ' data-rig-opacity="eye.angry"')
    part("eye-shut", "Eye - Shut", "eye_shut", "head", 46, shut, ' data-rig-opacity="eye.shut"')
    part("eye-dead", "Eye - Dead", "eye_dead", "head", 46, dead, ' data-rig-opacity="eye.dead"')


def near_rotor_parts():
    c = C
    hx, hy = J["near_hub"]
    base = J["near_rotor"][1]
    # A gearbox on the forward hull, the tall mast rising out of it.
    box = smooth([(hx - 26, base + 14, True), (hx - 22, base - 14), (hx - 10, base - 22, True), (hx + 10, base - 22, True),
                  (hx + 22, base - 14), (hx + 26, base + 14, True)])
    gear = [path(box, c["armor"], INK, LW), line([(hx - 20, base - 6), (hx + 20, base - 6)], c["steel"], 3.0),
            line([(hx - 14, base - 16), (hx + 6, base - 18)], c["armor_hi"], 2.4)]
    gear += rivets([(hx - 16, base + 4), (hx + 16, base + 4)], 1.8, c["steel"])
    part("gearbox", "Rotor Gearbox", "gearbox", "body", 38, gear)
    sil, body = cylinder("clip-near-mast", (hx, base - 10), (hx, hy + 10), 11.0, c, rings=(0.25, 0.5, 0.75), cap=False)
    body.append(ellipse(hx, hy + 10, 20, 7.5, c["steel_lo"], INK, LW))
    body.append(ellipse(hx, hy + 6, 13, 4.8, c["steel"], INK, 1.0))
    part("near-rotor-mast", "Near Rotor Mast", "near_rotor_mast", "near_rotor", 37, body)
    blades("near_rotor", "near_rotor", 52, (hx, hy), 196.0, False, "Near Rotor Blades")


def draw() -> str:
    svg.configure(dx=DX, dy=DY, ink=INK, ow=OW, colors=C)
    wing_parts("far")
    far_rotor_parts()
    claw_parts("far")
    body_parts()
    engine_part()
    neck_parts()
    mouth_part()
    jaw_part()
    head_part()
    eye_parts()
    near_rotor_parts()
    wing_parts("near")
    claw_parts("near")
    return svg.document(
        size=(W, H),
        design="mockingbird-boss-side-v2",
        layer_id="mockingbird-side",
        label="Mockingbird - Side Right",
        comment=[
            "  <!-- The Mockingbird v2: a mechanical predator-gunship in side view, facing",
            "       right. A lean black skull with a tall forehead, a glowing slit eye and a",
            "       beak of fangs on a segmented steel neck; a cage of steel ribs round a",
            "       glowing red engine-heart; hooked spines on an armoured back; two armoured",
            "       wings, a missile under each; two rotors on tall masts; a thruster at the",
            "       tail; two grappling claws beneath. Each part is a layer with a data-rig-part name.",
            "       *_ink layers are silhouettes grown by the outline width, painted beneath",
            "       every fill so the body reads as one outlined silhouette. Swap sets (the",
            "       eye, each rotor's spin state, each claw open or shut) sit on top of each",
            "       other and the rig shows one at a time (data-rig-opacity).",
            "       The hidden Rig Joints layer marks every joint the skeleton is built on. -->",
        ],
        joints=svg.joints_layer(J),
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    Path(sys.argv[1]).write_text(draw())
