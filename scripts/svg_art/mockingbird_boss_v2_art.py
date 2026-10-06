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
two reviews: a lean black skull with a great domed forehead, a brow low over
a glowing slit eye tilted hard toward a slender, sharp beak lined with long
narrow fangs over a slim jaw, on a segmented steel neck; a cage of steel ribs
round a glowing red engine-heart; two rigid swept jet wings, the near one
reaching toward the camera, a missile on each wingtip; two rotors on masts tall enough to clear the back spikes; a heavy
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
    snout=(960.0, 244.0),
    jaw=(704.0, 222.0),
    jaw_tip=(914.0, 234.0),
    engine=(300.0, 232.0),
    engine_tip=(118.0, 236.0),
    near_rotor=(574.0, 132.0),
    near_hub=(574.0, -16.0),
    far_rotor=(318.0, 124.0),
    far_hub=(318.0, -6.0),
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


#: The swept jet wings in design units, as (root leading edge, root trailing
#: edge, tip trailing edge, tip leading edge). Seen from a little above, the
#: near wing reaches down and back toward the camera from the flank and the
#: far wing up and back behind the hull, foreshortened.
WINGS = {
    "near": ((548.0, 186.0), (372.0, 192.0), (238.0, 318.0), (302.0, 318.0)),
    "far": ((532.0, 128.0), (384.0, 126.0), (296.0, 58.0), (334.0, 54.0)),
}


def wing_parts(side):
    """A rigid swept jet wing on the hull (it rides the ``body`` bone): its
    skin with a sheen behind the steel leading edge, flap segments along the
    trailing edge, panel lines and rivets, a hazard stripe and a red chevron,
    a nav light at the tip, and a missile on a rail along the tip."""
    far = side == "far"
    c = col(far)
    z0 = 3.5 if far else 55
    r_le, r_te, t_te, t_le = WINGS[side]

    def at(a, b, t):
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

    def chord(u, v):
        """The point ``v`` of the way from leading to trailing edge, ``u``
        of the way from root to tip."""
        return at(at(r_le, t_le, u), at(r_te, t_te, u), v)

    sil = poly([r_le, t_le, t_te, r_te])
    items = [path(sil, c["armor"])]
    items.append(path(poly([chord(0, 0.04), chord(1, 0.04), chord(1, 0.3), chord(0, 0.3)]), c["armor_hi"]))
    items.append(path(poly([chord(0, 0.62), chord(1, 0.62), chord(1, 0.78), chord(0, 0.78)]), c["armor_lo"]))
    for k in range(3):
        u0, u1 = 0.08 + k * 0.3, 0.08 + (k + 1) * 0.3 - 0.02
        items.append(path(poly([chord(u0, 0.8), chord(u1, 0.8), chord(u1, 1.02), chord(u0, 1.02)]), c["armor_lo"],
                          C["seam"], 1.4))
    for u in (0.36, 0.68):
        items.append(line([chord(u, 0.05), chord(u, 0.78)], C["seam"], 1.2))
    items.append(line([chord(0, 0.45), chord(1, 0.45)], C["seam"], 1.2))
    items += rivets([chord(u, 0.45) for u in (0.12, 0.3, 0.5, 0.7, 0.88)], 1.5, c["steel"])
    items.append(path(poly([chord(0.1, 0.5), chord(0.22, 0.5), chord(0.22, 0.66), chord(0.1, 0.66)]), C["hazard"], INK, 0.8))
    items.append(path(poly([chord(0.62, 0.12), chord(0.8, 0.22), chord(0.62, 0.32), chord(0.68, 0.22)]), c["hydraulic"],
                      INK, 0.8))
    body = clipped(f"clip-{side}-wing", sil, items) + [path(sil, "none", INK, LW)]
    # the steel leading edge and a root fairing into the hull
    body += [line([r_le, t_le], INK, 8.0), line([r_le, t_le], c["steel"], 4.6),
             line([at(r_le, t_le, 0.03), at(r_le, t_le, 0.97)], c["steel_hi"], 1.4)]
    fair = smooth([at(r_le, r_te, -0.04) + (True,), at(r_le, r_te, 1.02) + (True,), chord(0.1, 0.9), chord(0.1, 0.1)])
    body.append(path(fair, c["armor_hi"], INK, LW))
    body.append(ellipse(*t_le, 4.5, 4.5, "#3fd16a" if not far else "#2a8a48", INK, 1.0))
    ink(f"{side}_wing", "body", 19.5 if not far else 2.5, sil)
    part(f"{side}-wing", f"Wing - {side}", f"{side}_wing", "body", z0, body)

    # the missile on a rail along the wingtip, pointing forward
    r = 10.0 if far else 13.0
    y = t_le[1] + (r + 3 if not far else -r - 3)
    tail, nose = (t_te[0] - 26, y + 3), (t_le[0] + 150 if not far else t_le[0] + 110, y - 4)
    rail = [line([(t_te[0] + 4, t_te[1]), (t_le[0] + 2, t_le[1])], INK, 9.0),
            line([(t_te[0] + 4, t_te[1]), (t_le[0] + 2, t_le[1])], c["steel_lo"], 5.0)]
    part(f"{side}-missile", f"Missile - {side}", f"{side}_missile", "body", z0 + 0.6,
         rail + missile(f"{side}-missile", tail, nose, r, c))


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
SKULL = [(648, 212), (638, 172), (640, 126), (656, 86), (686, 58), (728, 42), (774, 42), (812, 58), (836, 86),
         (846, 118), (848, 148, True), (870, 168), (900, 190), (928, 212), (950, 232), (964, 246, True), (940, 236),
         (918, 228, True), (870, 224), (820, 222), (776, 222), (740, 222), (716, 226, True), (686, 230), (660, 226)]
JAW = [(696, 216), (712, 228, True), (760, 230), (820, 228), (870, 228), (916, 232, True), (906, 238), (866, 243),
       (820, 248), (770, 252), (732, 252), (708, 245), (696, 233)]
EYE = (806.0, 176.0)


def mouth_part():
    c = C
    inside = smooth([(712, 226, True), (780, 222), (860, 222), (918, 230, True), (896, 244), (820, 250), (760, 252),
                     (724, 246)])
    part("mouth", "Mouth", "mouth", "head", 40,
         [path(inside, c["mouth"]), line([(730, 240), (800, 244), (870, 238)], c["mouth2"], 4.0)])


def tooth(x, y, h, w, down=True, fill=None):
    s = 1 if down else -1
    pts = [(x - w / 2, y, True), (x - w * 0.12, y + s * h * 0.6), (x + w * 0.1, y + s * h, True),
           (x + w * 0.4, y + s * h * 0.45), (x + w / 2, y, True)]
    return path(smooth(pts), fill or C["tooth"], INK, 1.1)


def jaw_part():
    """A slim lower mandible with a row of long, narrow fangs along its top."""
    c = C
    sil = smooth(JAW)
    ink("jaw", "jaw", 23, sil)
    lo = [(700, 242), (760, 244), (830, 240), (916, 236), (916, 270), (700, 270)]
    hi = [(714, 232), (770, 233), (840, 232), (906, 234), (896, 238), (840, 237), (770, 238), (716, 238)]
    extra = [line([(722, 244), (780, 246), (850, 241), (896, 238)], C["seam"], 1.4)]
    teeth = [tooth(x, 230 + (x - 730) * 0.01, 20 - abs(x - 800) * 0.05, 5.0, down=False) for x in range(735, 904, 14)]
    body = teeth + shaded("clip-jaw", sil, c["armor"], c["armor_lo"], c["armor_hi"], lo, hi, extra)
    part("jaw", "Lower Jaw", "jaw", "jaw", 42, body)


def head_part():
    """A lean skull: a great domed forehead, an armour brow low over the eye,
    and a slender beak tapering to a sharp hooked point, lined with long fangs."""
    c = C
    sil = smooth(SKULL)
    ink("head", "head", 24, sil)
    lo = [(650, 208), (720, 206), (800, 204), (880, 210), (970, 226), (970, 260), (630, 260)]
    hi = [(656, 120), (676, 82), (716, 54), (764, 48), (806, 64), (826, 90), (804, 78), (764, 64), (720, 70), (688, 92),
          (668, 124)]
    extra = [
        # the cranium's plate seams and rivets
        line([(656, 196), (654, 140), (676, 94), (720, 64)], C["seam"], 1.8),
        line([(700, 120), (760, 104), (810, 112)], C["seam"], 1.4),
        line([(860, 192), (900, 206), (940, 230)], C["seam"], 1.4),
        ellipse(912, 212, 4.0, 2.0, C["seam"], rot=30),
        # a cheek vent: three slots
        *[line([(712 + 10 * k, 194), (720 + 10 * k, 210)], c["armor_lo"], 3.0) for k in range(3)],
    ]
    extra += rivets([(672, 170), (676, 146), (690, 122)], 2.0, C["steel"])
    teeth = [tooth(x, 222 + (x - 720) * 0.012, 26 - abs(x - 800) * 0.06, 5.5, down=True) for x in range(728, 918, 14)]
    # The brow: an armour plate jutting low over the eye, angled down to the front.
    brow = path(smooth([(752, 146, True), (812, 156), (856, 178, True), (818, 172), (762, 160)]), c["armor_lo"], INK, 1.2)
    body = shaded("clip-head", sil, c["armor"], c["armor_lo"], c["armor_hi"], lo, hi, extra) + teeth + [brow]
    part("head", "Head", "head", "head", 44, body)


def eye_parts():
    """A narrow slit tilted hard down toward the beak, under the brow."""
    x, y = EYE
    socket = path(smooth([(x - 26, y - 14, True), (x + 4, y - 4), (x + 32, y + 12, True), (x + 6, y + 12), (x - 20, y - 2)]),
                  C["armor_lo"], INK, 1.2)

    def slit(w, h, fill, rim=None):
        pts = [(x - 22 * w, y - 11 * h - 1, True), (x + 2 * w, y - 3 * h), (x + 28 * w, y + 10 * h, True),
               (x + 4 * w, y + 5 * h), (x - 16 * w, y - 4 * h)]
        return path(smooth(pts), fill, rim or INK, 1.0)

    open_ = [socket, slit(1.0, 1.0, C["eye"]), slit(0.6, 0.55, C["eye_hi"], C["eye"]), ellipse(x + 6, y + 3, 2.4, 1.6, "#fff6dc")]
    angry = [socket, slit(1.05, 0.75, C["eye"]), slit(0.7, 0.4, C["eye_hi"], C["eye"]),
             path(smooth([(x - 30, y - 20, True), (x + 36, y + 8, True), (x + 36, y - 6, True)]), C["armor"], INK, 1.0)]
    shut = [socket, line([(x - 22, y - 10), (x + 4, y + 1), (x + 28, y + 10)], C["eye_off"], 3.6),
            line([(x - 20, y - 9), (x + 26, y + 9)], C["eye"], 1.0)]
    dead = [socket, slit(1.0, 1.0, C["eye_off"]), line([(x - 8, y - 6), (x + 8, y + 8)], C["steel_lo"], 2.0),
            line([(x - 8, y + 8), (x + 8, y - 6)], C["steel_lo"], 2.0)]
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
            "       right. A lean black skull with a great forehead, a slanted slit eye and a",
            "       slender beak of fangs on a segmented steel neck; a cage of steel ribs round",
            "       a glowing red engine-heart; hooked spines on an armoured back; two swept",
            "       jet wings, a missile on each tip; two rotors on tall masts; a thruster at the",
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
