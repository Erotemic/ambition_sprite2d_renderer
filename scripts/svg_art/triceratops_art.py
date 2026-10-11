#!/usr/bin/env python3
"""How the triceratops's SVG was first drawn (reference, not authority).

``data/characters/triceratops/triceratops.svg`` owns the art; this script
reproduces it as first committed (less the rig catalog
``scripts/build_triceratops_rig.py`` installs).

    uv run python scripts/svg_art/triceratops_art.py SIDE.svg

A triceratops on a 512x512 canvas, ground y=416, centre line x=256 (published
at 0.5: a 256 px frame), on the joints of ``rigbuild.quadruped`` and a
``tail`` / ``tail_tip`` pair for its tail bone. Slate blue with a pale belly:
a barrel of a body on four thick legs, a heavy tail, and a great head that
is one part (the frill with its ochre blotches and its rim of knobs, the two
long brow horns, the nose horn, the hooked beak).
"""
from __future__ import annotations

import sys
from pathlib import Path

import svgkit as svg
from birdkit import ellipse, eye_states, line, outlined, part, path, smooth, tube

W, H = 512, 512
INK = "#1d1418"
OW = 1.6

C = dict(
    skin="#6f8796",
    light="#8aa2b0",
    dark="#4f6474",
    deep="#34444f",
    belly="#c9c3a4",
    horn="#efe6cc",
    horn_dark="#b8a987",
    frill="#d98a3a",
    frill_dark="#a8521f",
    beak="#8a7a5c",
    beak_dark="#5e5240",
    nail="#e6dcc0",
    iris="#f2c230",
)

J = dict(
    pelvis=(176.0, 292.0),
    neck_base=(306.0, 294.0),
    head=(338.0, 296.0),
    snout=(446.0, 342.0),
    jaw=(376.0, 338.0),
    tail=(150.0, 290.0),
    tail_tip=(40.0, 356.0),
    near_hip=(186.0, 308.0),
    near_knee=(206.0, 356.0),
    near_ankle=(188.0, 400.0),
    far_hip=(164.0, 304.0),
    far_knee=(184.0, 354.0),
    far_ankle=(166.0, 400.0),
    near_shoulder=(298.0, 322.0),
    near_elbow=(286.0, 362.0),
    near_wrist=(298.0, 400.0),
    far_shoulder=(278.0, 318.0),
    far_elbow=(266.0, 360.0),
    far_wrist=(278.0, 400.0),
)

JOINTS = {"hind": ("hip", "knee", "ankle"), "fore": ("shoulder", "elbow", "wrist")}


def leg(side: str, kind: str, z: float) -> None:
    """A thick leg: an upper and a lower column, and a round foot with nails."""
    far = side == "far"
    skin, shade = (C["dark"], C["deep"]) if far else (C["skin"], C["dark"])
    top, mid, end = (J[f"{side}_{name}"] for name in JOINTS[kind])
    r = (27.0, 20.0, 17.0, 15.0) if kind == "hind" else (22.0, 17.0, 15.0, 14.0)
    name = f"{side}_{kind}"
    sil = svg.capsule(top, mid, r[0], r[1])
    part(f"{side}-{kind}-upper", f"{kind.title()} Upper - {side}", f"{name}_upper", f"{name}_upper", z + 4,
         outlined(sil, skin, [line([(top[0] - 12, top[1] + 8), (mid[0] - 10, mid[1] - 4)], shade, 1.4),
                              line([(mid[0] - 12, mid[1] - 2), (mid[0], mid[1] + 3), (mid[0] + 12, mid[1] - 2)], shade, 1.2)],
                  f"clip-{side}-{kind}-u"))
    sil = svg.capsule(mid, end, r[2], r[3])
    part(f"{side}-{kind}-lower", f"{kind.title()} Lower - {side}", f"{name}_lower", f"{name}_lower", z + 2,
         outlined(sil, skin, [line([(end[0] - 10, end[1] - 12), (end[0], end[1] - 9), (end[0] + 10, end[1] - 12)], shade,
                                   1.2)], f"clip-{side}-{kind}-l"))
    ax, ay = end
    foot = smooth([(ax - 17, ay - 8), (ax + 14, ay - 10), (ax + 25, ay + 4), (ax + 25, ay + 16, True), (ax - 19, ay + 16, True),
                   (ax - 20, ay + 4)])
    items = [path(smooth([(ax - 18, ay + 10), (ax + 22, ay + 10), (ax + 22, ay + 16), (ax - 17, ay + 16)]), shade)]
    nails = []
    for dx in (5.0, 14.0, 22.0):
        nails.append(path(smooth([(ax + dx - 4, ay + 16, True), (ax + dx - 3, ay + 8), (ax + dx + 2, ay + 7),
                                  (ax + dx + 4, ay + 16, True)]), C["nail"], INK, 1.0))
    part(f"{side}-{kind}-paw", f"{kind.title()} Foot - {side}", f"{name}_paw", f"{name}_paw", z,
         outlined(foot, skin, items, f"clip-{side}-{kind}-p") + nails)


def parts():
    for kind in ("hind", "fore"):
        leg("far", kind, 10)

    tail_c = [(158, 290), (112, 312), (72, 340), (40, 356)]
    items = [path(smooth(tube([(150, 300), (110, 322), (72, 346), (42, 358)], 14.0, 2.0)), C["belly"]),
             line([(140, 280), (100, 302), (62, 332)], C["dark"], 2.0)]
    part("tail", "Tail", "tail", "tail", 20, outlined(smooth(tube(tail_c, 32.0, 3.0)), C["skin"], items, "clip-tail"))

    sil = smooth([(136, 292), (148, 252), (186, 234), (238, 232), (288, 244), (324, 268), (334, 304), (320, 336),
                  (284, 354), (232, 358), (184, 350), (148, 326)])
    items = [
        path(smooth([(142, 318), (186, 336), (236, 342), (288, 338), (326, 318), (322, 344), (284, 362), (230, 364),
                     (182, 358), (146, 334)]), C["belly"]),
        path(smooth([(150, 252), (186, 234), (238, 232), (288, 244), (322, 266), (286, 256), (238, 246), (188, 248)]),
             C["light"]),
        line([(196, 262), (206, 300), (198, 334)], C["dark"], 1.6),
        line([(276, 266), (268, 300), (276, 332)], C["dark"], 1.6),
    ]
    for x, y, r in ((170, 268, 7), (192, 282, 5), (222, 262, 8), (246, 284, 6), (262, 262, 5), (300, 282, 6),
                    (226, 300, 4)):
        items.append(ellipse(x, y, r, r * 0.8, C["dark"]))
    part("torso", "Torso", "torso", "torso", 34, outlined(sil, C["skin"], items, "clip-torso"))

    part("neck", "Neck", "neck", "neck", 35,
         outlined(svg.capsule((300, 296), (346, 300), 30.0, 26.0), C["skin"],
                  [line([(318, 276), (322, 300), (318, 322)], C["dark"], 1.4)], "clip-neck"))

    for kind in ("hind", "fore"):
        leg("near", kind, 40)

    head_parts()


def horn(cid, base, tip, width, bend, fill, shade):
    """A horn from ``base`` to ``tip``, bowed by ``bend`` across its length."""
    (bx, by), (tx, ty) = base, tip
    dx, dy = tx - bx, ty - by
    d = (dx * dx + dy * dy) ** 0.5
    nx, ny = -dy / d, dx / d
    mx, my = bx + dx * 0.5 + nx * bend, by + dy * 0.5 + ny * bend
    sil = smooth([(bx + nx * width, by + ny * width, True), (mx + nx * width * 0.6, my + ny * width * 0.6), (tx, ty, True),
                  (mx - nx * width * 0.6, my - ny * width * 0.6), (bx - nx * width, by - ny * width, True)])
    rib = line([(bx + dx * 0.1 - nx * width * 0.4, by + dy * 0.1 - ny * width * 0.4),
                (mx - nx * width * 0.3, my - ny * width * 0.3), (tx - dx * 0.08, ty - dy * 0.08)], shade, 1.6)
    return outlined(sil, fill, [rib], cid)


def head_parts():
    body = []
    # The far brow horn, behind the skull.
    body += horn("clip-horn-far", (364, 270), (428, 198), 11.0, -8.0, C["horn_dark"], C["beak"])
    # The frill: a shield of bone behind the skull, its rim set with knobs.
    rim = [(358, 280), (352, 234), (330, 198), (298, 188), (272, 206), (264, 242), (278, 278), (308, 302), (342, 306)]
    for (x, y), (ox, oy) in zip(rim[1:7], ((8, -4), (4, -9), (-2, -10), (-8, -6), (-10, 0), (-8, 6))):
        body += outlined(smooth([(x - oy * 0.6, y + ox * 0.6, True), (x + ox, y + oy), (x + oy * 0.6, y - ox * 0.6, True)]),
                         C["horn"], width=2.0)
    frill = smooth(rim)
    items = [
        path(smooth([(346, 238), (328, 208), (300, 200), (280, 214), (274, 242), (286, 270), (310, 288), (336, 290),
                     (318, 262), (312, 236), (326, 226)]), C["dark"]),
        ellipse(304, 232, 15, 19, C["frill"], rot=-20.0),
        ellipse(304, 232, 7, 10, C["frill_dark"], rot=-20.0),
        ellipse(322, 272, 11, 9, C["frill"], rot=30.0),
        ellipse(322, 272, 5, 4, C["frill_dark"], rot=30.0),
        line([(340, 292), (322, 248), (300, 204)], C["deep"], 1.4),
    ]
    body += outlined(frill, C["skin"], items, "clip-frill")
    # The skull, from the brow down to the beak.
    skull = smooth([(338, 300), (346, 270), (376, 262), (408, 284), (424, 300), (430, 316), (392, 340), (372, 340),
                    (352, 330)])
    items = [path(smooth([(348, 272), (376, 264), (406, 284), (378, 276)]), C["light"]),
             path(smooth([(340, 306), (352, 330), (374, 340), (392, 340), (368, 326)]), C["dark"]),
             line([(352, 310), (362, 318), (374, 318)], C["deep"], 1.3)]
    body += outlined(skull, C["skin"], items, "clip-skull")
    # The beak: a hooked bill of horn at the end of the snout.
    beak = smooth([(418, 296, True), (436, 308), (446, 326), (446, 344, True), (436, 336), (420, 332), (408, 334, True),
                   (410, 312)])
    body += outlined(beak, C["beak"], [path(smooth([(436, 320), (446, 328), (446, 344), (438, 336)]), C["beak_dark"]),
                                       ellipse(424, 312, 2.4, 1.8, C["beak_dark"])], "clip-beak")
    # The nose horn and the near brow horn.
    body += horn("clip-horn-nose", (416, 300), (432, 264), 9.0, -3.0, C["horn"], C["horn_dark"])
    body += horn("clip-horn-near", (378, 270), (446, 204), 12.0, -9.0, C["horn"], C["horn_dark"])
    part("head", "Head", "head", "head", 60, body)
    lower = smooth([(370, 336, True), (410, 334), (436, 338, True), (432, 350), (404, 358), (374, 352), (366, 344)])
    part("jaw", "Lower Jaw", "jaw", "jaw", 58, outlined(lower, C["belly"], [
        path(smooth([(412, 334), (436, 338), (432, 350), (414, 354)]), C["beak"]),
        line([(374, 346), (404, 350)], C["dark"], 1.2)], "clip-jaw"))
    ex, ey, r = 384.0, 292.0, 6.0
    pupil = "#120d0f"
    eye_states("eye", "head", 72, {
        "open": [ellipse(ex, ey, r, r, C["iris"], INK, 1.3), ellipse(ex + 0.8, ey, r * 0.4, r * 0.6, pupil),
                 ellipse(ex - r * 0.3, ey - r * 0.35, r * 0.2, r * 0.2, "#ffffff")],
        "angry": [ellipse(ex, ey, r, r, C["iris"], INK, 1.3), ellipse(ex + 1.0, ey + 0.4, r * 0.3, r * 0.5, pupil),
                  path(smooth([(ex - r - 3, ey - r - 3, True), (ex + r + 3, ey - r * 0.2, True),
                               (ex + r + 3, ey - r - 3, True)]), C["deep"], INK, 1.0)],
        "shut": [line([(ex - r, ey), (ex, ey + r * 0.5), (ex + r, ey)], INK, 2.0)],
        "dead": [line([(ex - r * 0.8, ey - r * 0.8), (ex + r * 0.8, ey + r * 0.8)], INK, 2.0),
                 line([(ex - r * 0.8, ey + r * 0.8), (ex + r * 0.8, ey - r * 0.8)], INK, 2.0)],
    })


def draw_side() -> str:
    svg.configure(dx=0.0, dy=0.0, ink=INK, ow=OW, colors=C)
    parts()
    return svg.document(
        size=(W, H),
        design="triceratops-side",
        layer_id="triceratops-side",
        label="Triceratops - Side Right",
        comment=[
            "  <!-- The triceratops, side view facing right, on a 512x512 drawing whose ground",
            "       is y=416 (published at 0.5). Each part is a layer with a data-rig-part name;",
            "       rigged/triceratops/ turns them about their joints. The eye has open / angry",
            "       / shut / dead. The hidden Rig Joints layer marks every joint. -->",
        ],
        joints=svg.joints_layer(J),
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    Path(sys.argv[1]).write_text(draw_side())
