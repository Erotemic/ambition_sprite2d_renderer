#!/usr/bin/env python3
"""How the boss chest's SVG was first drawn (reference, not authority).

``data/props/boss_chest/boss_chest.svg`` owns the art; this script
reproduces it as first committed (less the rig catalog
``scripts/build_boss_chest_rig.py`` installs).

    uv run python scripts/svg_art/boss_chest_art.py OUT.svg

The big-item chest: a royal chest on lion-claw feet, deep blue lacquered
panels in a gold frame set with jewelled lozenges, a gold-ribbed domed lid with a
crowned medallion, a great shield lock set with a ruby, red velvet lining.
Seen from the front and a little above like the treasure chest, on a
640x640 canvas, ground y=600, centre line x=320 (published at 0.25: a
160 px frame). The lid is the same swap set hinged at the box's back edge
(``lid.closed`` / ``lid.ajar`` / ``lid.up`` / ``lid.open``); it is empty
inside, for an item placed at runtime.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import svgkit as svg
from svgkit import clipped, ellipse, line, part, path, poly, smooth

W, H = 640, 640
INK = "#140c18"
OW = 2.0

C = dict(
    blue="#2c3f8f",
    blue_light="#4b63c0",
    blue_dark="#1b275e",
    blue_deep="#101838",
    gold="#eab53e",
    gold_light="#ffe08a",
    gold_dark="#a5701c",
    velvet="#8e1c2e",
    velvet_light="#b8344a",
    velvet_dark="#5a0f1c",
    ruby="#e0263f",
    ruby_light="#ff8a98",
    ruby_dark="#8a0f22",
    sapphire="#5aa0ff",
    void="#12080e",
    shadow="#000000",
    stripe="#a5701c",
)

CX = 320.0
L, R = 136.0, 504.0  # the box's sides
RIM = 392.0  # the box's front top edge
BACK = 344.0  # the box's back top edge (the hinge line)
FLOOR = 572.0  # the box's bottom (it stands on claw feet)

J = dict(
    base=(CX, FLOOR),
    hinge=(CX, BACK),
    lid_top=(CX, 252.0),
    lock=(CX, 398.0),
    lock_end=(CX, 492.0),
)


def outlined(sil, fill, items=(), cid=None, width=None):
    body = [path(sil, fill)]
    if items:
        body = clipped(cid, sil, [path(sil, fill)] + list(items))
    return body + [path(sil, "none", INK, width or 2 * OW)]


def stud(x, y, r=5.0):
    return [ellipse(x, y, r, r, C["gold"], INK, 1.2), ellipse(x - r * 0.3, y - r * 0.3, r * 0.4, r * 0.4, C["gold_light"])]


def band(x0, y0, x1, y1, fill=None):
    return [path(poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)]), fill or C["gold"], INK, 1.4),
            line([(x0 + 2, y0 + 3), (x1 - 2, y0 + 3)], C["gold_light"], 1.6)]


def lozenge(cx, cy, s):
    """A gold lozenge set with a sapphire, studs at its points."""
    pts = [(cx, cy - 34 * s), (cx + 26 * s, cy), (cx, cy + 34 * s), (cx - 26 * s, cy)]
    out = [path(poly(pts), C["blue_dark"], C["gold"], 5.0 * s), path(poly(pts), "none", C["gold_dark"], 1.2)]
    out += [ellipse(cx, cy, 9 * s, 11 * s, C["sapphire"], INK, 1.2), ellipse(cx - 3 * s, cy - 4 * s, 3 * s, 3 * s, "#d8ecff")]
    for x, y in pts:
        out += stud(x, y, 3.6 * s)
    return out


def panel(x0, x1, y0, y1, cid, jewel=True):
    """A blue lacquered panel in a gold moulding, a jewelled lozenge on it
    (not behind the lock)."""
    sil = poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    items = [path(poly([(x0, y0), (x1, y0), (x1, y0 + 10), (x0, y0 + 10)]), C["blue_light"]),
             path(poly([(x0, y1 - 12), (x1, y1 - 12), (x1, y1), (x0, y1)]), C["blue_dark"])]
    if jewel:
        items += lozenge((x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 110.0)
    return outlined(sil, C["blue"], items, cid, 2.0) + [path(sil, "none", C["gold"], 3.0)]


def base_parts():
    # The inside: velvet back wall over a dark well (an item stands in it).
    well = poly([(L + 8, BACK), (R - 8, BACK), (R - 4, RIM), (L + 4, RIM)])
    part("interior", "Interior", "interior", "base", 10, outlined(well, C["void"], [
        path(poly([(L + 8, BACK), (R - 8, BACK), (R - 10, BACK + 20), (L + 10, BACK + 20)]), C["velvet_dark"]),
        line([(L + 10, BACK + 20), (R - 10, BACK + 20)], C["gold_dark"], 2.0),
    ], "clip-well"))
    # Lion-claw feet at the corners.
    feet = []
    for x in (L + 30, R - 30):
        foot = smooth([(x - 26, FLOOR - 8, True), (x + 26, FLOOR - 8, True), (x + 24, 588), (x + 14, 600, True),
                       (x - 14, 600, True), (x - 24, 588)])
        feet += outlined(foot, C["gold"], [
            line([(x - 9, 584), (x - 9, 599)], C["gold_dark"], 2.0), line([(x + 9, 584), (x + 9, 599)], C["gold_dark"], 2.0),
            path(poly([(x - 24, FLOOR - 8), (x + 24, FLOOR - 8), (x + 22, FLOOR + 2), (x - 22, FLOOR + 2)]), C["gold_light"]),
        ], f"clip-foot-{int(x)}")
    part("feet", "Feet", "feet", "base", 25, feet)
    # The box's front: a gold frame round three panels, the middle one
    # carrying the lock.
    front = poly([(L, RIM), (R, RIM), (R, FLOOR), (L, FLOOR)])
    items = [path(front, C["gold"]),
             path(poly([(L, RIM), (R, RIM), (R, RIM + 5), (L, RIM + 5)]), C["gold_light"])]
    items += panel(L + 16, 262, RIM + 18, FLOOR - 30, "clip-panel-l")
    items += panel(270, 370, RIM + 18, FLOOR - 30, "clip-panel-c", jewel=False)
    items += panel(378, R - 16, RIM + 18, FLOOR - 30, "clip-panel-r")
    items += band(L, FLOOR - 22, R, FLOOR, C["gold_dark"])
    for x in (L + 8, 266, 374, R - 8):
        items += stud(x, RIM + 9, 4.0) + stud(x, FLOOR - 11, 4.0)
    # corner caps
    for sx, x in ((1, L), (-1, R)):
        items.append(path(poly([(x, RIM), (x + sx * 40, RIM), (x, RIM + 40)]), C["gold_light"], INK, 1.4))
        items += stud(x + sx * 12, RIM + 12, 4.5)
    part("base", "Box", "base", "base", 30, outlined(front, C["gold"], items, "clip-front", 2 * OW))
    # The shield lock with its ruby.
    plate = smooth([(282, 398, True), (358, 398, True), (362, 446), (320, 492, True), (278, 446)])
    lock = outlined(plate, C["gold"], [
        line([(286, 404), (354, 404)], C["gold_light"], 3.0),
        path(smooth([(282, 398, True), (358, 398, True), (362, 446), (320, 492, True), (278, 446)]), "none", C["gold_dark"], 6.0),
        path(smooth([(320, 452), (328, 460), (324, 468, True), (327, 482, True), (313, 482, True), (316, 468, True),
                     (312, 460)]), C["void"]),
    ], "clip-lock")
    lock += [ellipse(CX, 426, 17, 15, C["ruby"], INK, 1.6), ellipse(CX, 430, 11, 9, C["ruby_dark"]),
             ellipse(CX - 5, 421, 6, 4, C["ruby_light"]), ellipse(CX + 6, 430, 2.4, 2.4, "#ffffff")]
    lock += stud(292, 410, 3.4) + stud(348, 410, 3.4)
    part("lock", "Lock", "lock", "lock", 40, lock)


def medallion(x, y, r):
    """A gold disc bearing a crown over a sapphire."""
    out = [ellipse(x, y, r, r, C["gold"], INK, 1.8), ellipse(x, y, r - 6, r - 6, C["blue_dark"], C["gold_dark"], 1.4)]
    crown = poly([(x - 16, y + 2), (x - 18, y - 14), (x - 8, y - 4), (x, y - 18), (x + 8, y - 4), (x + 18, y - 14),
                  (x + 16, y + 2)])
    out += [path(crown, C["gold"], INK, 1.2), ellipse(x, y + 10, 6, 5, C["sapphire"], INK, 1.0)]
    return out


def lid_closed():
    sil = smooth([(L - 6, 402, True), (L - 6, 330), (160, 292), (232, 262), (CX, 252), (408, 262), (480, 292),
                  (R + 6, 330), (R + 6, 402, True)])
    items = [
        path(smooth([(160, 296), (232, 266), (CX, 256), (408, 266), (480, 296), (480, 310), (408, 280), (CX, 270),
                     (232, 280), (160, 310)]), C["blue_light"]),
        path(poly([(L - 6, 360), (R + 6, 360), (R + 6, 402), (L - 6, 402)]), C["blue_dark"]),
    ]
    items += band(L - 6, 376, R + 6, 402)
    for x in (196, 444):
        items.append(path(poly([(x - 9, 240), (x + 9, 240), (x + 9, 378), (x - 9, 378)]), C["gold"], INK, 1.4))
        items.append(line([(x - 5, 250), (x - 5, 374)], C["gold_light"], 1.6))
        items += stud(x, 300, 4.0) + stud(x, 344, 4.0)
    for x in (156, 236, 284, 356, 404, 484):
        items += stud(x, 389, 3.6)
    body = outlined(sil, C["blue"], items, "clip-lid-closed", 2 * OW)
    body += medallion(CX, 318, 34)
    hasp = smooth([(300, 386, True), (340, 386, True), (340, 410), (CX, 420, True), (300, 410)])
    body += outlined(hasp, C["gold"], [line([(304, 390), (336, 390)], C["gold_light"], 2.4)], "clip-hasp")
    part("lid-closed", "Lid - Closed", "lid_closed", "lid", 50, body, ' data-rig-opacity="lid.closed" data-rig-default="1"')


def lid_ajar():
    sil = smooth([(L - 6, 380, True), (L - 6, 316), (160, 280), (232, 252), (CX, 242), (408, 252), (480, 280),
                  (R + 6, 316), (R + 6, 380, True)])
    items = [
        path(smooth([(160, 284), (232, 256), (CX, 246), (408, 256), (480, 284), (480, 296), (408, 268), (CX, 260),
                     (232, 268), (160, 296)]), C["blue_light"]),
        path(poly([(L - 6, 342), (R + 6, 342), (R + 6, 380), (L - 6, 380)]), C["blue_dark"]),
    ]
    items += band(L - 6, 358, R + 6, 380)
    for x in (196, 444):
        items.append(path(poly([(x - 9, 230), (x + 9, 230), (x + 9, 360), (x - 9, 360)]), C["gold"], INK, 1.4))
        items += stud(x, 286, 4.0) + stud(x, 326, 4.0)
    body = outlined(sil, C["blue"], items, "clip-lid-ajar", 2 * OW)
    body += medallion(CX, 302, 32)
    hasp = smooth([(300, 368, True), (340, 368, True), (340, 388), (CX, 396, True), (300, 388)])
    body += outlined(hasp, C["gold"], [line([(304, 372), (336, 372)], C["gold_light"], 2.4)], "clip-hasp-ajar")
    part("lid-ajar", "Lid - Ajar", "lid_ajar", "lid", 50, body, ' data-rig-opacity="lid.ajar"')


def velvet_face(x0, x1, y_top, y_bottom, cid, rows):
    """The lid's inside: red velvet in a gold frame, tufted with buttons."""
    sil = poly([(x0, y_bottom), (x1, y_bottom), (x1 + 8, y_top), (x0 - 8, y_top)])
    items = [path(poly([(x0, y_bottom - 14), (x1, y_bottom - 14), (x1, y_bottom), (x0, y_bottom)]), C["velvet_dark"])]
    h = (y_bottom - y_top)
    for r in range(rows):
        y = y_top + h * (r + 0.5) / rows
        for k in range(6):
            x = x0 + 26 + (x1 - x0 - 52) * (k + (0.5 if r % 2 else 0.0)) / 5.5
            items += [line([(x - 14, y - 6), (x, y), (x + 14, y - 6)], C["velvet_dark"], 1.6),
                      ellipse(x, y, 3.2, 3.2, C["gold"], INK, 0.8)]
    items.append(path(sil, "none", C["gold"], 9.0))
    items.append(path(sil, "none", C["gold_dark"], 2.0))
    return sil, items


def lid_up():
    sil, items = velvet_face(L + 4, R - 4, 236, BACK + 2, "clip-lid-up", 2)
    body = outlined(sil, C["velvet"], items, "clip-lid-up", 2 * OW)
    dome = smooth([(L - 8, 238, True), (L - 4, 222), (232, 206), (CX, 202), (408, 206), (R + 4, 222), (R + 8, 238, True)])
    body += outlined(dome, C["blue"], [path(poly([(L - 8, 228), (R + 8, 228), (R + 8, 238), (L - 8, 238)]), C["gold"]),
                                       line([(232, 212), (CX, 208), (408, 212)], C["blue_light"], 3.0)],
                     "clip-lid-up-dome", 2 * OW)
    part("lid-up", "Lid - Up", "lid_up", "lid", 5, body, ' data-rig-opacity="lid.up"')


def lid_open():
    sil, items = velvet_face(L + 4, R - 4, 182, BACK + 2, "clip-lid-open", 3)
    body = outlined(sil, C["velvet"], items, "clip-lid-open", 2 * OW)
    top = smooth([(L - 6, 186, True), (L - 2, 172), (232, 160), (CX, 156), (408, 160), (R + 2, 172), (R + 6, 186, True)])
    body += outlined(top, C["gold"], [line([(232, 165), (CX, 161), (408, 165)], C["gold_light"], 2.4)], "clip-lid-open-top")
    part("lid-open", "Lid - Open", "lid_open", "lid", 5, body, ' data-rig-opacity="lid.open"')


def draw() -> str:
    svg.configure(dx=0.0, dy=0.0, ink=INK, ow=OW, colors=C)
    base_parts()
    lid_closed()
    lid_ajar()
    lid_up()
    lid_open()
    return svg.document(
        size=(W, H),
        design="boss-chest",
        layer_id="boss-chest",
        label="Boss Chest - Front",
        comment=[
            "  <!-- The boss (big-item) chest seen from the front and a little above, on a",
            "       640x640 drawing whose ground is y=600 (published at 0.25). Each part is a",
            "       layer with a data-rig-part name; rigged/boss_chest/ poses them. The lid is",
            "       a swap set hinged at the box's back edge: lid.closed, lid.ajar, lid.up,",
            "       lid.open. Empty inside, for an item placed at runtime. The hidden Rig",
            "       Joints layer marks every joint. -->",
        ],
        joints=svg.joints_layer(J),
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    Path(sys.argv[1]).write_text(draw())
