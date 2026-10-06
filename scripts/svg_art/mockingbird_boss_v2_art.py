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
Mockingbird Flash animation (Jon's reference, 2026-10-06): a black skull with a
glowing slit eye and a gaping jaw of white saw teeth on a segmented steel neck,
a cage of steel ribs round a glowing red engine-heart, hooked black spines and
swept fins along an armoured back, two rotor masts, a missile pod over the
head, a heavy thruster at the tail and two grappling claws hanging beneath.
Drawn facing right in a 1140x720 SVG (design units shifted by ``DX``, ``DY``).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import svgkit as svg
from svgkit import capsule, clipped, ellipse, ink, line, part, path, poly, smooth

W, H = 1140, 720
#: The design is drawn at x 100-925, y 30-440; shifted to leave room behind
#: it for the thruster's plume and above it to rear.
DX, DY = 120.0, 90.0
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
    snout=(904.0, 222.0),
    jaw=(694.0, 222.0),
    jaw_tip=(890.0, 240.0),
    engine=(300.0, 232.0),
    engine_tip=(118.0, 236.0),
    pod=(560.0, 118.0),
    pod_tip=(820.0, 96.0),
    near_rotor=(498.0, 128.0),
    near_hub=(498.0, 58.0),
    far_rotor=(332.0, 126.0),
    far_hub=(332.0, 70.0),
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
    sil, body = cylinder("clip-far-mast", (hx, J["far_rotor"][1] + 4), (hx, hy + 8), 9.0, c, rings=(0.3, 0.62), cap=False)
    body.append(ellipse(hx, hy + 8, 14, 6, c["steel_lo"], INK, LW))
    body.append(ellipse(hx, hy + 5, 10, 4, c["steel"], INK, 1.0))
    part("far-rotor-mast", "Far Rotor Mast", "far_rotor_mast", "far_rotor", 6, body)
    blades("far_rotor", "far_rotor", 7, (hx, hy), 150.0, True, "Far Rotor Blades")


def pod_part():
    """The missile pod on the far shoulder, its warhead over the head."""
    c = col(True)
    a, b = J["pod"], J["pod_tip"]
    # the mount
    mount = smooth([(540, 140, True), (552, 112), (584, 104), (600, 128, True)])
    items = [path(mount, c["armor"], INK, LW)]
    sil, body = cylinder("clip-pod", a, (b[0] - 40, b[1] + 3.4), 15.0, c, rings=(0.1, 0.45, 0.8), cap=False)
    items += body
    # the warhead: a teal ogive with a pale tip
    wx, wy = b[0] - 40, b[1] + 3.4
    head = smooth([(wx, wy - 15, True), (wx + 22, wy - 12), (b[0], b[1], True), (wx + 22, wy + 12), (wx, wy + 15, True)])
    items.append(path(head, C["teal"], INK, LW))
    items.append(path(smooth([(wx + 2, wy - 11, True), (wx + 22, wy - 8), (b[0] - 4, b[1] - 1, True), (wx + 18, wy - 3),
                              (wx + 2, wy - 4, True)]), C["teal_hi"]))
    items.append(line([(wx + 1, wy - 15), (wx + 1, wy + 15)], c["steel_dk"], 3.0))
    # fins at the tail end
    for s in (-1, 1):
        items.append(path(smooth([(a[0] + 18, a[1] + s * 12, True), (a[0] - 6, a[1] + s * 30, True),
                                  (a[0] - 2, a[1] + s * 12, True)]), c["steel_lo"], INK, 1.2))
    # a hazard band
    for k in range(4):
        x = a[0] + 140 + k * 7
        items.append(line([(x, a[1] - 26 + k * -0.6 + 10), (x + 4, a[1] - 26 + 28)], C["hazard"] if k % 2 else C["armor_lo"], 3.4))
    part("pod", "Missile Pod", "pod", "pod", 12, items)


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
    # Swept fins at the back, behind the hull.
    fins = []
    for (bx, by, h, k) in ((296, 126, 96, 1.0), (258, 140, 74, 0.86)):
        pts = [(bx + 26 * k, by + 6, True), (bx + 4 * k, by - h * 0.55), (bx - 30 * k, by - h, True),
               (bx - 18 * k, by - h * 0.62), (bx - 22 * k, by + 8, True)]
        sil = smooth(pts)
        fins += [path(sil, c["armor"], INK, LW), line([(bx + 10 * k, by), (bx - 20 * k, by - h * 0.9)], c["sheen"], 1.8),
                 path(smooth([(bx + 14 * k, by + 2), (bx - 2 * k, by - h * 0.45), (bx - 26 * k, by - h * 0.92, True),
                              (bx - 14 * k, by - h * 0.5), (bx - 14 * k, by + 4)]), c["armor_lo"])]
    part("fins", "Back Fins", "fins", "body", 14, fins)

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
    for i, (x, s) in enumerate(((556, 0.9), (514, 1.2), (466, 1.4), (418, 1.5), (370, 1.4), (330, 1.25))):
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
SKULL = [(646, 196), (650, 166), (672, 136), (712, 118), (762, 114), (810, 124), (852, 144), (886, 172), (910, 204),
         (922, 232), (918, 254, True), (906, 238), (890, 228, True), (850, 222), (810, 220), (770, 220), (734, 224),
         (704, 230, True), (676, 230), (656, 216)]
JAW = [(686, 216), (700, 228, True), (740, 234), (790, 236), (840, 236), (884, 234, True), (892, 244), (880, 270),
       (848, 294), (800, 308), (750, 310), (712, 298), (690, 272), (680, 240)]
EYE = (812.0, 160.0)


def mouth_part():
    c = C
    inside = smooth([(700, 226, True), (760, 222), (830, 220), (896, 222, True), (884, 252), (820, 262), (760, 262),
                     (712, 250)])
    part("mouth", "Mouth", "mouth", "head", 40,
         [path(inside, c["mouth"]), line([(716, 244), (780, 252), (850, 248)], c["mouth2"], 5.0)])


def tooth(x, y, h, w, down=True, fill=None):
    s = 1 if down else -1
    pts = [(x - w / 2, y, True), (x - w * 0.12, y + s * h * 0.6), (x + w * 0.1, y + s * h, True),
           (x + w * 0.4, y + s * h * 0.45), (x + w / 2, y, True)]
    return path(smooth(pts), fill or C["tooth"], INK, 1.1)


def jaw_part():
    c = C
    sil = smooth(JAW)
    ink("jaw", "jaw", 23, sil)
    lo = [(680, 262), (740, 280), (820, 276), (900, 250), (900, 320), (680, 320)]
    hi = [(700, 236), (760, 240), (840, 242), (896, 240), (890, 248), (840, 250), (760, 250), (706, 246)]
    extra = [line([(712, 270), (770, 284), (840, 276), (880, 258)], C["seam"], 1.8)]
    extra += rivets([(730, 262), (770, 272), (812, 270)], 2.0, C["steel"])
    teeth = [tooth(x, 236 - (x - 720) * -0.02, 18 - abs(x - 800) * 0.04, 10, down=False) for x in range(724, 884, 13)]
    # The beard: a comb of saw teeth rooted along the chin, raking down and forward.
    beard = []
    chin = [(888, 250), (878, 272), (848, 296), (800, 310), (752, 312), (716, 300)]
    segs = list(zip(chin, chin[1:]))
    for k in range(11):
        u = k / 10 * len(segs)
        i = min(len(segs) - 1, int(u))
        (x0, y0), (x1, y1) = segs[i]
        t = u - i
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        h = 24 - 12 * (k / 10)
        tx, ty = x1 - x0, y1 - y0
        d = math.hypot(tx, ty)
        tx, ty = tx / d, ty / d
        nx, ny = -ty, tx  # outward (down) normal of a chin running nose to throat
        if ny < 0:
            nx, ny = -nx, -ny
        w = 7.0
        tip = (x + nx * h + 8, y + ny * h)
        beard.append(path(smooth([(x - tx * w - nx * 4, y - ty * w - ny * 4, True), tip + (True,),
                                  (x + tx * w - nx * 4, y + ty * w - ny * 4, True)]), C["tooth"], INK, 1.1))
        beard.append(line([(x + nx * 2, y + ny * 2), (x + nx * h * 0.7 + 5, y + ny * h * 0.7)], C["tooth_sh"], 1.3))
    body = teeth + shaded("clip-jaw", sil, c["armor"], c["armor_lo"], c["armor_hi"], lo, hi, extra) + beard
    part("jaw", "Lower Jaw", "jaw", "jaw", 42, body)


def head_part():
    c = C
    sil = smooth(SKULL)
    ink("head", "head", 24, sil)
    lo = [(650, 200), (720, 196), (800, 192), (880, 196), (920, 204), (920, 240), (640, 240)]
    hi = [(684, 146), (720, 130), (770, 126), (820, 136), (856, 154), (836, 152), (790, 140), (740, 140), (700, 152)]
    extra = [
        # a brow ridge over the eye socket, and seams back from it
        path(smooth([(772, 150), (812, 140), (854, 152), (858, 162), (812, 154), (774, 162)]), c["armor_lo"]),
        line([(700, 160), (760, 170), (794, 172)], C["seam"], 2.0),
        line([(690, 196), (740, 204), (790, 202)], C["seam"], 1.6),
        line([(872, 196), (900, 222), (912, 244)], C["seam"], 1.6),
        ellipse(890, 192, 3.6, 2.4, C["seam"], rot=30),
    ]
    extra += rivets([(690, 178), (716, 186), (742, 190)], 2.0, C["steel"])
    teeth = [tooth(x, 224 - (x - 720) * 0.012, 22 - abs(x - 800) * 0.05, 11, down=True) for x in range(718, 892, 14)]
    body = shaded("clip-head", sil, c["armor"], c["armor_lo"], c["armor_hi"], lo, hi, extra) + teeth
    part("head", "Head", "head", "head", 44, body)


def eye_parts():
    x, y = EYE
    socket = path(smooth([(x - 30, y + 8, True), (x - 6, y - 6), (x + 26, y - 6, True), (x + 18, y + 6), (x - 6, y + 12)]),
                  C["armor_lo"], INK, 1.2)

    def slit(w, h, fill, rim=None):
        pts = [(x - 26 * w, y + 7, True), (x - 4 * w, y - 3 * h), (x + 22 * w, y - 4 * h, True), (x + 12 * w, y + 4 * h),
               (x - 6 * w, y + 8 * h)]
        return path(smooth(pts), fill, rim or INK, 1.0)

    open_ = [socket, slit(1.0, 1.0, C["eye"]), slit(0.62, 0.55, C["eye_hi"], C["eye"]), ellipse(x + 4, y + 1, 3.4, 2.4, "#fff6dc")]
    angry = [socket, slit(1.05, 0.7, C["eye"]), slit(0.7, 0.35, C["eye_hi"], C["eye"]),
             path(smooth([(x - 34, y - 14, True), (x + 30, y - 2, True), (x + 32, y - 18, True)]), C["armor"], INK, 1.0)]
    shut = [socket, line([(x - 26, y + 7), (x - 4, y + 2), (x + 22, y - 2)], C["eye_off"], 4.0),
            line([(x - 24, y + 6), (x + 20, y - 2)], C["eye"], 1.0)]
    dead = [socket, slit(1.0, 1.0, C["eye_off"]), line([(x - 10, y - 4), (x + 8, y + 8)], C["steel_lo"], 2.0),
            line([(x - 10, y + 8), (x + 8, y - 4)], C["steel_lo"], 2.0)]
    part("eye-open", "Eye - Open", "eye_open", "head", 46, open_, ' data-rig-opacity="eye.open" data-rig-default="1"')
    part("eye-angry", "Eye - Angry", "eye_angry", "head", 46, angry, ' data-rig-opacity="eye.angry"')
    part("eye-shut", "Eye - Shut", "eye_shut", "head", 46, shut, ' data-rig-opacity="eye.shut"')
    part("eye-dead", "Eye - Dead", "eye_dead", "head", 46, dead, ' data-rig-opacity="eye.dead"')


def near_rotor_parts():
    c = C
    hx, hy = J["near_hub"]
    # The nacelle on the flank: a tall pod from the keel to the rotor's collar.
    nac = smooth([(476, 262, True), (472, 200), (474, 140), (486, 126, True), (510, 126, True), (522, 140), (524, 200),
                  (520, 262, True), (498, 274)])
    items = [path(nac, c["steel"])]
    items.append(path(smooth([(506, 128), (520, 140), (524, 200), (520, 262), (498, 274), (500, 200), (502, 140)]), c["steel_lo"]))
    items.append(path(smooth([(480, 140), (486, 132), (492, 140), (490, 250), (482, 252)]), c["steel_hi"]))
    for y in (150, 196, 242):
        items.append(line([(472, y), (498, y + 4), (524, y)], c["steel_dk"], 3.0))
    items.append(ellipse(498, 220, 8, 8, C["armor_lo"], INK, 1.0))
    items.append(ellipse(498, 220, 4, 4, C["eye"]))
    ink("nacelle", "body", 21.5, nac)
    part("nacelle", "Rotor Nacelle", "nacelle", "body", 50, clipped("clip-nacelle", nac, items) + [path(nac, "none", INK, LW)])
    sil, body = cylinder("clip-near-mast", (hx, J["near_rotor"][1] + 2), (hx, hy + 10), 10.0, c, rings=(0.35, 0.7), cap=False)
    body.append(ellipse(hx, hy + 10, 18, 7, c["steel_lo"], INK, LW))
    body.append(ellipse(hx, hy + 6, 12, 4.5, c["steel"], INK, 1.0))
    part("near-rotor-mast", "Near Rotor Mast", "near_rotor_mast", "near_rotor", 48, body)
    blades("near_rotor", "near_rotor", 52, (hx, hy), 196.0, False, "Near Rotor Blades")


def draw() -> str:
    svg.configure(dx=DX, dy=DY, ink=INK, ow=OW, colors=C)
    far_rotor_parts()
    claw_parts("far")
    pod_part()
    body_parts()
    engine_part()
    neck_parts()
    mouth_part()
    jaw_part()
    head_part()
    eye_parts()
    near_rotor_parts()
    claw_parts("near")
    return svg.document(
        size=(W, H),
        design="mockingbird-boss-side-v2",
        layer_id="mockingbird-side",
        label="Mockingbird - Side Right",
        comment=[
            "  <!-- The Mockingbird v2: a mechanical predator-gunship in side view, facing",
            "       right. A black skull with a glowing slit eye and a jaw of white saw teeth",
            "       on a segmented steel neck; a cage of steel ribs round a glowing red",
            "       engine-heart; hooked spines and swept fins on an armoured back; two",
            "       rotors; a missile pod over the head; a thruster at the tail; two",
            "       grappling claws beneath. Each part is a layer with a data-rig-part name.",
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
