#!/usr/bin/env python3
"""How the treasure chest's SVG was first drawn (reference, not authority).

``data/props/treasure_chest/treasure_chest.svg`` owns the art; this script
reproduces it as first committed (less the rig catalog
``scripts/build_treasure_chest_rig.py`` installs).

    uv run python scripts/svg_art/treasure_chest_art.py OUT.svg

A banded pirate chest seen from the front and a little above, on a 512x512
canvas, ground y=440, centre line x=256 (published at 0.25: a 128 px frame).
The lid is a swap set of four drawings hinged at the box's back edge
(``lid.closed`` / ``lid.ajar`` / ``lid.up`` / ``lid.open``): the classic way
a sprite lid swings toward the viewer. Inside, a heap of coins and gems
sits behind the box's front, shown only in the treasure rows
(``treasure.shown``): the plain chest is empty, for an item placed at
runtime.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import svgkit as svg
from svgkit import clipped, ellipse, line, part, path, poly, smooth

W, H = 512, 512
INK = "#1f1410"
OW = 1.8

C = dict(
    wood="#9a5427",
    wood_light="#bd7038",
    wood_dark="#6e3517",
    wood_deep="#4a220e",
    inner="#5a2c14",
    inner_dark="#3a1a0a",
    iron="#3d4049",
    iron_light="#717887",
    iron_dark="#24262d",
    gold="#e9a93a",
    gold_light="#ffd86a",
    gold_dark="#a8681a",
    gold_hot="#fff1b0",
    void="#1c0e08",
    ruby="#e0334a",
    sapphire="#3f7ae8",
    emerald="#34c26f",
    pearl="#f4ecdc",
    shadow="#000000",
    stripe="#a8681a",
)

#: Joints: the box's bottom centre (the root), the hinge on the back edge
#: of the box's top, the lock, and the treasure heap's crown.
J = dict(
    base=(256.0, 432.0),
    hinge=(256.0, 262.0),
    lid_top=(256.0, 198.0),
    lock=(256.0, 306.0),
    lock_end=(256.0, 352.0),
    treasure=(256.0, 290.0),
    treasure_top=(256.0, 228.0),
)

L, R = 114.0, 398.0  # the box's sides
RIM = 300.0  # the box's front top edge
BACK = 262.0  # the box's back top edge (the hinge line)
FLOOR = 432.0


def outlined(sil, fill, items=(), cid=None, width=None):
    body = [path(sil, fill)]
    if items:
        body = clipped(cid, sil, [path(sil, fill)] + list(items))
    return body + [path(sil, "none", INK, width or 2 * OW)]


def rivet(x, y, r=4.0):
    return [ellipse(x, y, r, r, C["iron_light"], INK, 1.0), ellipse(x - r * 0.3, y - r * 0.3, r * 0.35, r * 0.35, "#c9ced8")]


def strap(x0, x1, y0, y1, rivets=()):
    """A vertical iron band from y0 to y1 with rivets at the given heights."""
    out = [path(poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)]), C["iron"], INK, 1.4),
           line([(x0 + 3, y0 + 2), (x0 + 3, y1 - 2)], C["iron_light"], 1.6)]
    for y in rivets:
        out += rivet((x0 + x1) / 2, y)
    return out


def coin(x, y, r=9.0, tilt=0.55):
    return [ellipse(x, y, r, r * tilt, C["gold"], INK, 1.2), ellipse(x - r * 0.2, y - r * 0.12, r * 0.55, r * 0.3, C["gold_light"])]


def gem(x, y, r, color):
    pts = [(x, y - r), (x + r * 0.9, y - r * 0.15), (x + r * 0.5, y + r * 0.9), (x - r * 0.5, y + r * 0.9),
           (x - r * 0.9, y - r * 0.15)]
    return [path(poly(pts), color, INK, 1.2),
            path(poly([(x, y - r), (x + r * 0.9, y - r * 0.15), (x, y + r * 0.1), (x - r * 0.9, y - r * 0.15)]),
                 "#ffffff", extra=' opacity="0.35"')]


def base_parts():
    shade = smooth([(256 + 168 * math.cos(a), 436 + 18 * math.sin(a)) for a in (k * math.tau / 16 for k in range(16))])
    part("shadow", "Shadow", "shadow", "base", 0, [path(shade, C["shadow"], extra=' opacity="0.28"')])
    # The box's inside (seen once the lid is up): a dark well, lighter at
    # the back wall.
    well = poly([(L + 6, BACK), (R - 6, BACK), (R - 4, RIM), (L + 4, RIM)])
    part("interior", "Interior", "interior", "base", 10, outlined(well, C["void"], [
        path(poly([(L + 6, BACK), (R - 6, BACK), (R - 8, BACK + 14), (L + 8, BACK + 14)]), C["inner"]),
        line([(L + 40, BACK + 2), (L + 40, BACK + 13)], C["inner_dark"], 1.4),
        line([(R - 40, BACK + 2), (R - 40, BACK + 13)], C["inner_dark"], 1.4),
    ], "clip-well"))
    # The treasure heap: a mound of coins with gems, a pearl string, a
    # goblet; its foot is hidden behind the box's front.
    mound = smooth([(L + 10, RIM + 6), (L + 26, 270), (170, 248), (220, 236), (262, 230), (306, 238), (350, 252),
                    (R - 24, 272), (R - 10, RIM + 6)])
    heap = []
    for k, (x, y) in enumerate(((150, 262), (182, 250), (214, 242), (246, 236), (282, 240), (314, 246), (346, 256),
                                (378, 270), (166, 276), (200, 266), (232, 258), (300, 262), (334, 270), (264, 254),
                                (136, 284), (366, 286), (226, 280), (290, 282))):
        heap += coin(x, y, 9.0 + (k % 3), 0.5 + 0.08 * (k % 2))
    heap += gem(208, 252, 11, C["ruby"]) + gem(318, 256, 10, C["sapphire"]) + gem(270, 244, 9, C["emerald"])
    heap += [line([(150, 270), (176, 280), (204, 276), (226, 284)], C["pearl"], 4.0)]
    for x, y in ((150, 270), (164, 276), (178, 280), (192, 278), (206, 276), (220, 282)):
        heap.append(ellipse(x, y, 3.0, 3.0, C["pearl"], INK, 0.7))
    # a goblet leaning in the heap
    heap += outlined(smooth([(338, 222, True), (366, 222, True), (362, 238), (354, 246), (356, 258, True),
                             (366, 264, True), (334, 264, True), (346, 258, True), (348, 246), (340, 238)]),
                     C["gold"], [line([(344, 226), (344, 238)], C["gold_light"], 2.4)], "clip-goblet", 2.4)
    part("treasure", "Treasure", "treasure", "treasure", 20,
         outlined(mound, C["gold_dark"], [path(mound, C["gold"], extra=' opacity="0.45"')], "clip-mound") + heap,
         ' data-rig-opacity="treasure.shown"')
    # The box's front: planks, iron corners and straps, a gold trim along
    # the rim and a lock plate.
    front = smooth([(L, RIM, True), (R, RIM, True), (R + 2, FLOOR - 10), (R - 8, FLOOR, True), (L + 8, FLOOR, True),
                    (L - 2, FLOOR - 10)])
    items = [path(poly([(L, RIM), (R, RIM), (R, RIM + 18), (L, RIM + 18)]), C["wood_light"])]
    for y in (334.0, 366.0, 398.0):
        items += [line([(L, y), (R, y)], C["wood_deep"], 2.2), line([(L, y + 3), (R, y + 3)], C["wood_light"], 1.2)]
    for x, y0, y1 in ((176, 304, 330), (300, 340, 362), (204, 370, 394), (330, 404, 428), (140, 404, 426)):
        items.append(line([(x, y0), (x + 6, (y0 + y1) / 2), (x, y1)], C["wood_dark"], 1.3))
    items += [path(poly([(L, FLOOR - 16), (R, FLOOR - 16), (R, FLOOR), (L, FLOOR)]), C["wood_dark"])]
    # corner brackets
    for sx, x in ((1, L), (-1, R)):
        items.append(path(poly([(x, RIM), (x + sx * 28, RIM), (x + sx * 28, RIM + 10), (x + sx * 10, RIM + 10),
                                (x + sx * 10, FLOOR - 10), (x + sx * 28, FLOOR - 10), (x + sx * 28, FLOOR), (x, FLOOR)]),
                           C["iron"]))
        items += rivet(x + sx * 18, RIM + 6, 3.2) + rivet(x + sx * 18, FLOOR - 5, 3.2)
    items += strap(160, 182, RIM, FLOOR, (RIM + 22, 384, FLOOR - 16))
    items += strap(330, 352, RIM, FLOOR, (RIM + 22, 384, FLOOR - 16))
    items.append(path(poly([(L, RIM), (R, RIM), (R, RIM + 7), (L, RIM + 7)]), C["gold"]))
    items.append(line([(L, RIM + 2), (R, RIM + 2)], C["gold_light"], 1.6))
    part("base", "Box", "base", "base", 30, outlined(front, C["wood"], items, "clip-front", 2 * OW))
    # The lock plate with its keyhole.
    plate = smooth([(234, 304, True), (278, 304, True), (280, 334), (256, 354, True), (232, 334)])
    part("lock", "Lock", "lock", "lock", 40, outlined(plate, C["gold"], [
        line([(238, 308), (274, 308)], C["gold_light"], 2.4),
        path(smooth([(256, 316), (262, 322), (259, 328, True), (261, 340, True), (251, 340, True), (253, 328, True),
                     (250, 322)]), C["void"]),
    ], "clip-lock") + rivet(240, 312, 2.6) + rivet(272, 312, 2.6))


def lid_closed():
    sil = smooth([(L - 4, 308, True), (L - 4, 252), (132, 224), (184, 206), (256, 198), (328, 206), (380, 224),
                  (R + 4, 252), (R + 4, 308, True)])
    items = [
        path(smooth([(132, 228), (184, 210), (256, 202), (328, 210), (380, 228), (380, 240), (328, 222), (256, 214),
                     (184, 222), (132, 240)]), C["wood_light"]),
        line([(L, 246), (184, 226), (256, 220), (328, 226), (R, 246)], C["wood_deep"], 2.0),
        line([(L, 270), (R, 270)], C["wood_deep"], 2.0),
        path(poly([(L - 4, 290), (R + 4, 290), (R + 4, 308), (L - 4, 308)]), C["gold"]),
        line([(L - 4, 293), (R + 4, 293)], C["gold_light"], 1.8),
    ]
    items += strap(160, 182, 196, 292, (226, 262)) + strap(330, 352, 196, 292, (226, 262))
    body = outlined(sil, C["wood"], items, "clip-lid-closed", 2 * OW)
    # the hasp hanging over the lock
    hasp = smooth([(242, 286, True), (270, 286, True), (270, 312), (256, 322, True), (242, 312)])
    body += outlined(hasp, C["gold"], [line([(246, 290), (266, 290)], C["gold_light"], 2.0)], "clip-hasp")
    part("lid-closed", "Lid - Closed", "lid_closed", "lid", 50, body, ' data-rig-opacity="lid.closed" data-rig-default="1"')


def lid_ajar():
    """Lifted a hand's breadth: the face tilted back (shorter), a lit gap
    under its edge."""
    sil = smooth([(L - 4, 286, True), (L - 4, 240), (132, 214), (184, 198), (256, 190), (328, 198), (380, 214),
                  (R + 4, 240), (R + 4, 286, True)])
    items = [
        path(smooth([(132, 218), (184, 202), (256, 194), (328, 202), (380, 218), (380, 228), (328, 212), (256, 206),
                     (184, 212), (132, 228)]), C["wood_light"]),
        line([(L, 234), (184, 216), (256, 210), (328, 216), (R, 234)], C["wood_deep"], 2.0),
        line([(L, 254), (R, 254)], C["wood_deep"], 2.0),
        path(poly([(L - 4, 272), (R + 4, 272), (R + 4, 286), (L - 4, 286)]), C["gold"]),
        line([(L - 4, 275), (R + 4, 275)], C["gold_light"], 1.8),
    ]
    items += strap(160, 182, 188, 274, (216, 248)) + strap(330, 352, 188, 274, (216, 248))
    body = outlined(sil, C["wood"], items, "clip-lid-ajar", 2 * OW)
    hasp = smooth([(242, 270, True), (270, 270, True), (270, 292), (256, 300, True), (242, 292)])
    body += outlined(hasp, C["gold"], [line([(246, 274), (266, 274)], C["gold_light"], 2.0)], "clip-hasp-ajar")
    part("lid-ajar", "Lid - Ajar", "lid_ajar", "lid", 50, body, ' data-rig-opacity="lid.ajar"')


def lid_up():
    """Swung up past the vertical: the underside faces us, foreshortened,
    the dome's top showing as a strip along its upper edge."""
    inner = poly([(L + 2, BACK + 2), (R - 2, BACK + 2), (R + 6, 168), (L - 6, 168)])
    items = [line([(L + 4, 226), (R - 4, 226)], C["inner_dark"], 2.0),
             line([(L + 2, 196), (R - 2, 196)], C["inner_dark"], 2.0)]
    items += strap(160, 182, 168, BACK, (184, 244)) + strap(330, 352, 168, BACK, (184, 244))
    body = outlined(inner, C["inner"], items, "clip-lid-up", 2 * OW)
    dome = smooth([(L - 6, 170, True), (L - 2, 154), (184, 140), (256, 136), (328, 140), (R + 2, 154),
                   (R + 6, 170, True)])
    body += outlined(dome, C["wood"], [path(poly([(L - 6, 160), (R + 6, 160), (R + 6, 170), (L - 6, 170)]), C["gold"]),
                                       line([(184, 146), (256, 142), (328, 146)], C["wood_light"], 3.0)],
                     "clip-lid-up-dome", 2 * OW)
    part("lid-up", "Lid - Up", "lid_up", "lid", 5, body, ' data-rig-opacity="lid.up"')


def lid_open():
    """Thrown back: the lid's inside face toward us, standing behind the box."""
    inner = smooth([(L + 2, BACK + 2, True), (R - 2, BACK + 2, True), (R + 8, 128, True), (330, 112), (256, 108),
                    (182, 112), (L - 8, 128, True)])
    items = [line([(L + 2, 226), (R - 2, 226)], C["inner_dark"], 2.0),
             line([(L - 2, 190), (R + 2, 190)], C["inner_dark"], 2.0),
             line([(L - 6, 154), (R + 6, 154)], C["inner_dark"], 2.0),
             path(poly([(L - 8, 116), (R + 8, 116), (R + 8, 132), (L - 8, 132)]), C["gold"]),
             line([(L - 8, 119), (R + 8, 119)], C["gold_light"], 1.8),
             path(poly([(L + 2, BACK - 10), (R - 2, BACK - 10), (R - 2, BACK + 2), (L + 2, BACK + 2)]), C["inner_dark"])]
    items += strap(160, 182, 108, BACK, (150, 214)) + strap(330, 352, 108, BACK, (150, 214))
    for x in (L + 2, R - 2):
        items += rivet(x + (12 if x < 256 else -12), 140, 3.4)
    part("lid-open", "Lid - Open", "lid_open", "lid", 5, outlined(inner, C["inner"], items, "clip-lid-open", 2 * OW),
         ' data-rig-opacity="lid.open"')


def draw() -> str:
    svg.configure(dx=0.0, dy=0.0, ink=INK, ow=OW, colors=C)
    base_parts()
    lid_closed()
    lid_ajar()
    lid_up()
    lid_open()
    return svg.document(
        size=(W, H),
        design="treasure-chest",
        layer_id="treasure-chest",
        label="Treasure Chest - Front",
        comment=[
            "  <!-- A banded pirate treasure chest seen from the front and a little above, on",
            "       a 512x512 drawing whose ground is y=440 (published at 0.25). Each part is a",
            "       layer with a data-rig-part name; rigged/treasure_chest/ poses them. The lid",
            "       is a swap set hinged at the box's back edge: lid.closed, lid.ajar, lid.up,",
            "       lid.open. The treasure heap shows only where a clip keys treasure.shown",
            "       (an empty chest otherwise). The hidden Rig Joints layer marks every joint. -->",
        ],
        joints=svg.joints_layer(J),
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    Path(sys.argv[1]).write_text(draw())
