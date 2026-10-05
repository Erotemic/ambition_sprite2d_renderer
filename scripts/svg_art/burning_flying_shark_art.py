#!/usr/bin/env python3
"""How the burning flying shark's SVG was first drawn (reference, not authority).

``data/characters/burning_flying_shark/burning_flying_shark.svg`` owns the art
and may have been edited since; this script reproduces the drawing as it was
first committed (less the rig catalog
``scripts/build_burning_flying_shark_rig.py`` installs). Keep it as a worked
example for drawing a legless creature with ``svgkit``: one body outline
(``TOP`` / ``BOT``) cut into overlapping segments, fins with glowing trailing
edges, and tack (a saddle, a girth, reins) riding on the body.

    uv run python scripts/svg_art/burning_flying_shark_art.py OUT.svg

Drawn in design units, shifted by (60, 60) into a 620x360 SVG.
"""
from __future__ import annotations

import sys
from pathlib import Path

import svgkit as svg
from svgkit import clipped, ellipse, ink, line, part, path, smooth, tooth

W, H = 620, 360
INK = "#15161c"
OW = 2.2  # half the silhouette ink width

C = dict(
    body="#4b5262",
    back="#353a47",
    light="#6a7385",
    belly="#cfc6b8",
    belly_sh="#a69d90",
    stripe="#2a2e38",
    magma="#ff6a1a",
    magma_hi="#ffd24a",
    fin="#3c414e",
    fin_glow="#e5581c",
    fin_glow2="#ffb03a",
    eye="#ffb52e",
    eye_rim="#ffe38a",
    pupil="#140c06",
    membrane="#b9c4cf",
    mouth="#4a161c",
    mouth2="#6b2028",
    gum="#b04d58",
    tongue="#c8707a",
    tooth="#f4ecd4",
    leather="#7a4a2a",
    leather_d="#4f2e19",
    brass="#e0aa45",
    blanket="#9e2b25",
    blanket_d="#6e1c18",
    bone="#f1eadb",
)
FAR = dict(fin="#2c303b", fin_glow="#b8461a", fin_glow2="#d98a30")

J = dict(
    body=(300.0, 150.0),
    head=(372.0, 150.0),
    snout=(476.0, 158.0),
    jaw=(400.0, 170.0),
    tail1=(222.0, 152.0),
    tail2=(156.0, 151.0),
    tail_tip=(112.0, 151.0),
    dorsal=(306.0, 106.0),
    dorsal_tip=(282.0, 44.0),
    near_pec=(350.0, 182.0),
    near_pec_tip=(284.0, 244.0),
    far_pec=(338.0, 176.0),
    far_pec_tip=(292.0, 224.0),
)

# The shark's outline, nose to tail, along the back and along the belly.
TOP = [(476, 158), (470, 146), (456, 134), (432, 123), (400, 114), (360, 107), (320, 103), (280, 104),
       (240, 112), (205, 124), (175, 136), (150, 144), (128, 148), (108, 150)]
BOT = [(476, 160), (468, 166), (452, 171), (420, 176), (380, 186), (340, 192), (300, 192), (260, 186),
       (225, 176), (195, 166), (165, 158), (140, 155), (120, 154), (108, 152)]


def edge_at(edge, x):
    """The outline's y at ``x`` (edges run nose to tail, x falling)."""
    for (x0, y0), (x1, y1) in zip(edge, edge[1:]):
        if x1 <= x <= x0:
            t = (x0 - x) / (x0 - x1) if x0 != x1 else 0.0
            return y0 + (y1 - y0) * t
    return edge[0][1] if x > edge[0][0] else edge[-1][1]


def segment_outline(x_front, x_back):
    """The body between two cuts: the back edge, then the belly edge."""
    top = [(x_front, edge_at(TOP, x_front), True)] + [p for p in TOP if x_back < p[0] < x_front] + \
          [(x_back, edge_at(TOP, x_back), True)]
    bot = [(x_back, edge_at(BOT, x_back), True)] + [p for p in BOT if x_back < p[0] < x_front][::-1] + \
          [(x_front, edge_at(BOT, x_front), True)]
    return top + bot


def shading(x_front, x_back, cid, sil, magma=()):
    """Countershading shared by every body segment so the cuts disappear: a
    dark back, a pale belly under a wavy line, a highlight along the back."""
    xs = [x for x in range(int(x_back) - 20, int(x_front) + 21, 10)]
    back = [(x, edge_at(TOP, x) - 20) for x in xs] + [(x, edge_at(TOP, x) + 0.3 * (edge_at(BOT, x) - edge_at(TOP, x)))
                                                      for x in xs[::-1]]
    hi = [(x, edge_at(TOP, x) + 0.32 * (edge_at(BOT, x) - edge_at(TOP, x))) for x in xs] + \
         [(x, edge_at(TOP, x) + 0.42 * (edge_at(BOT, x) - edge_at(TOP, x))) for x in xs[::-1]]
    belly = [(x, edge_at(TOP, x) + 0.62 * (edge_at(BOT, x) - edge_at(TOP, x))) for x in xs] + \
            [(x, edge_at(BOT, x) + 20) for x in xs[::-1]]
    items = [path(sil, C["body"]), path(smooth(back), C["back"]), path(smooth(hi), C["light"]),
             path(smooth(belly), C["belly"]),
             line([(x, edge_at(TOP, x) + 0.64 * (edge_at(BOT, x) - edge_at(TOP, x))) for x in xs], C["belly_sh"], 1.6)]
    # Magma cracks: the shark burns from inside.
    for pts in magma:
        items += crack(pts)
    return clipped(cid, sil, items)


def crack(pts):
    """A jagged magma crack: a soft glow, the molten line, a hot core."""
    d = smooth([p + (True,) for p in pts], closed=False)
    return [path(d, "none", C["magma"], 7.0, ' stroke-opacity="0.35"'), path(d, "none", C["magma"], 3.0),
            path(d, "none", C["magma_hi"], 1.2)]


def glowing_fin(name, bone, z, pts, glow_edge, col, label):
    """A fin: its fill, a glowing trailing edge, its own outline."""
    sil = smooth(pts)
    items = [path(sil, col["fin"]), line(glow_edge, col["fin_glow"], 7.0), line(glow_edge, col["fin_glow2"], 2.4)]
    part(name.replace("_", "-"), label, name, bone, z, clipped(f"clip-{name}", sil, items) + [path(sil, "none", INK, 2 * OW)])


# ---- body segments -------------------------------------------------------------
def tail_parts():
    sil = smooth(segment_outline(160, 104))
    ink("tail2", "tail2", 20.2, sil)
    body = shading(160, 104, "clip-tail2", sil)
    # second dorsal and anal finlets
    body = [path(smooth([(150, 144, True), (140, 128, True), (128, 147, True)]), C["fin"], INK, 2.0),
            path(smooth([(150, 157, True), (138, 170, True), (128, 155, True)]), C["fin"], INK, 2.0)] + body
    part("tail2", "Tail 2", "tail2", "tail2", 30.2, body)
    sil = smooth(segment_outline(232, 150))
    ink("tail1", "tail1", 20.4, sil)
    body = shading(232, 150, "clip-tail1", sil, magma=[[(226, 150), (214, 146), (204, 154), (190, 150), (178, 155)]])
    body = [path(smooth([(222, 176, True), (204, 200, True), (196, 172, True)]), C["fin"], INK, 2.0)] + body
    part("tail1", "Tail 1", "tail1", "tail1", 30.4, body)


def torso_part():
    sil = smooth(segment_outline(386, 216))
    ink("torso", "body", 24, sil)
    body = shading(386, 216, "clip-torso", sil, magma=[
        [(372, 148), (360, 145), (352, 153), (338, 149), (326, 157), (310, 152), (298, 159), (282, 154), (270, 158)],
        [(326, 157), (322, 168), (312, 172), (304, 168)],
        [(352, 153), (356, 162)],
        [(266, 138), (254, 144), (244, 139), (230, 144)],
    ])
    # Tack: a red saddle blanket with a skull, the saddle, a girth, a stirrup, reins.
    blanket = smooth([(302, 104), (328, 100), (356, 104), (360, 132, True), (300, 134, True)])
    body.append(path(blanket, C["blanket"], INK, 1.8))
    body.append(line([(302, 130), (360, 128)], C["brass"], 2.4))
    body.append(line([(308, 127), (324, 111)], C["bone"], 1.6))
    body.append(line([(308, 111), (324, 127)], C["bone"], 1.6))
    body.append(ellipse(316, 118, 4.6, 4.0, C["bone"], INK, 1.0))
    body.append(ellipse(314.5, 117.5, 1.0, 1.0, INK))
    body.append(ellipse(317.5, 117.5, 1.0, 1.0, INK))
    # the girth round the belly, its buckle, and the stirrup hanging from it
    body.append(line([(344, 110), (348, 140), (346, 170), (340, 192)], C["leather_d"], 6.0))
    body.append(line([(344, 110), (348, 140), (346, 170), (340, 192)], C["leather"], 3.6))
    body.append(path(smooth([(340, 160, True), (352, 160, True), (352, 170, True), (340, 170, True)]), "none", C["brass"], 2.0))
    seat = smooth([(308, 102), (320, 92), (338, 90), (352, 94), (360, 86, True), (364, 92), (358, 102), (336, 106),
                   (314, 108)])
    body.append(path(seat, C["leather"], INK, 1.8))
    body.append(line([(316, 102), (336, 98), (354, 98)], C["leather_d"], 1.4))
    body.append(line([(330, 108), (332, 132)], C["leather_d"], 2.4))
    body.append(path(smooth([(326, 132, True), (338, 132, True), (336, 140), (328, 140)]), "none", C["brass"], 2.2))
    # the reins, from the saddle horn forward to where the head takes them
    body.append(line([(362, 88), (372, 98), (380, 112)], C["leather_d"], 1.8))
    part("torso", "Torso", "torso", "body", 34, body)


def head_part():
    # The back edge to the gills, down the gills, the throat, then forward
    # along the mouth line (the lower jaw is its own part).
    sil_pts = [p for p in TOP if 366 < p[0] <= 476] + [
        (366, edge_at(TOP, 366), True), (366, edge_at(BOT, 366), True), (384, 185), (400, 181),
        (404, 170, True), (430, 169), (452, 167), (470, 163)]
    sil = smooth(sil_pts)
    ink("head", "head", 27, sil)
    xs = list(range(356, 487, 10))
    items = [path(sil, C["body"]),
             path(smooth([(x, edge_at(TOP, x) - 20) for x in xs] +
                         [(x, edge_at(TOP, x) + 0.3 * (edge_at(BOT, x) - edge_at(TOP, x))) for x in xs[::-1]]), C["back"]),
             path(smooth([(x, edge_at(TOP, x) + 0.32 * (edge_at(BOT, x) - edge_at(TOP, x))) for x in xs] +
                         [(x, edge_at(TOP, x) + 0.42 * (edge_at(BOT, x) - edge_at(TOP, x))) for x in xs[::-1]]),
                  C["light"]),
             path(smooth([(366, 170), (390, 172), (420, 170), (452, 165), (478, 159), (478, 200), (366, 200)]),
                  C["belly"])]
    # Gills: five slits where the head meets the body.
    for k in range(5):
        x = 372 + k * 5.5
        items.append(line([(x - 2, 132 + k * 1.5), (x + 1, 148), (x - 1, 166 - k)], C["stripe"], 2.0))
    items.append(ellipse(458, 142, 3.0, 1.8, INK, rot=-15))
    items.append(line([(404, 170), (430, 169), (452, 167), (470, 163)], INK, 2.0))
    # magma seam and scar along the snout
    items.append(line([(440, 128), (452, 136), (462, 134)], C["magma"], 3.0))
    items.append(line([(440, 128), (452, 136), (462, 134)], C["magma_hi"], 1.1))
    body = clipped("clip-head", sil, items)
    for x in (410, 418, 426, 434, 442, 450, 458, 465):
        body.append(tooth(x, 169.5 - (x - 410) * 0.1, 7 - (x - 410) * 0.04, 4.6, True, curve=0.4))
    # the bit at the corner of the mouth, and the reins running back from it
    body.append(line([(403, 166), (394, 140), (378, 110)], C["leather_d"], 1.8))
    body.append(ellipse(403, 168, 4.0, 4.0, "none", C["brass"], 2.0))
    part("head", "Head", "head", "head", 48, body)


JAW = [(396, 176), (402, 170, True), (430, 171), (452, 169), (468, 165, True), (464, 172), (446, 180), (420, 184),
       (402, 183)]


def jaw_part():
    sil = smooth(JAW)
    ink("jaw", "jaw", 26, sil)
    items = [path(sil, C["belly"]), line([(404, 174), (430, 175), (452, 172), (466, 167)], C["belly_sh"], 1.6)]
    roof = smooth([(406, 171, True), (432, 171), (454, 169), (466, 166, True), (460, 156), (436, 156), (412, 160)])
    tongue = smooth([(410, 170, True), (428, 168), (444, 167), (452, 168), (446, 171), (428, 172)])
    teeth = [tooth(x, 171 - (x - 412) * 0.12, 6 - (x - 412) * 0.04, 4.2, False, curve=0.4)
             for x in (412, 420, 428, 436, 444, 452, 460)]
    part("jaw", "Lower Jaw", "jaw", "jaw", 44,
         [path(roof, C["mouth"]), path(tongue, C["tongue"], C["mouth2"], 1.0)] + teeth + clipped("clip-jaw", sil, items))


def mouth_floor_part():
    floor = smooth([(406, 171, True), (432, 171), (454, 169), (466, 166, True), (462, 172), (446, 178), (420, 181),
                    (406, 179)])
    gum = smooth([(406, 170, True), (432, 170), (454, 168), (466, 165, True), (462, 168), (446, 171), (420, 173),
                  (406, 173)])
    part("mouth-floor", "Mouth Floor", "mouth_floor", "head", 42,
         [path(floor, C["mouth"]), path(gum, C["gum"]), line([(414, 178), (436, 178), (452, 174)], C["mouth2"], 1.6)])


EYE = (430.0, 140.0)


def eye_parts():
    x, y = EYE
    base = ellipse(x, y, 7.5, 6.0, C["stripe"])
    open_ = [base, ellipse(x, y, 5.4, 4.6, C["eye"], INK, 1.4), ellipse(x - 1, y - 1, 2.8, 2.0, C["eye_rim"]),
             ellipse(x + 0.6, y, 2.4, 3.2, C["pupil"]), ellipse(x - 2.2, y - 1.6, 0.9, 0.8, "#ffffff")]
    angry = [base, ellipse(x, y + 0.6, 5.4, 3.6, C["eye"], INK, 1.4), ellipse(x + 0.6, y + 0.8, 2.2, 2.6, C["pupil"]),
             path(smooth([(x - 9, y - 7, True), (x + 8, y - 0.5, True), (x + 8, y - 8, True)]), C["back"]),
             line([(x - 8, y - 5), (x + 8, y + 0.5)], INK, 2.2)]
    # Sharks shut a nictitating membrane over the eye as they bite.
    shut = [base, ellipse(x, y, 5.4, 4.6, C["membrane"], INK, 1.4), line([(x - 4, y + 1.5), (x + 4, y + 1.5)], "#8d99a6", 1.2)]
    dead = [base, ellipse(x, y, 5.4, 4.6, C["membrane"], INK, 1.4), line([(x - 3.5, y - 3), (x + 3.5, y + 3)], INK, 2.0),
            line([(x - 3.5, y + 3), (x + 3.5, y - 3)], INK, 2.0)]
    part("eye-open", "Eye - Open", "eye_open", "head", 50, open_, ' data-rig-opacity="eye.open" data-rig-default="1"')
    part("eye-angry", "Eye - Angry", "eye_angry", "head", 50, angry, ' data-rig-opacity="eye.angry"')
    part("eye-shut", "Eye - Shut", "eye_shut", "head", 50, shut, ' data-rig-opacity="eye.shut"')
    part("eye-dead", "Eye - Dead", "eye_dead", "head", 50, dead, ' data-rig-opacity="eye.dead"')


def fin_parts():
    far = {**C, **FAR}
    glowing_fin("far_pec", "far_pec", 16,
                [(350, 174), (330, 192), (306, 212), (290, 228, True), (302, 210), (316, 192), (326, 178)],
                [(290, 228), (302, 210), (316, 192), (326, 178)], far, "Pectoral Fin - far")
    glowing_fin("dorsal", "dorsal", 18,
                [(336, 108), (322, 82), (302, 58), (282, 44, True), (288, 66), (290, 88), (282, 110)],
                [(282, 44), (288, 66), (290, 88), (284, 108)], C, "Dorsal Fin")
    glowing_fin("fluke", "fluke", 12,
                [(124, 146), (104, 128), (82, 108), (58, 90, True), (68, 116), (84, 146), (72, 170), (64, 190, True),
                 (90, 174), (110, 160), (124, 156)],
                [(58, 90), (68, 116), (84, 146), (72, 170), (64, 190)], C, "Tail Fluke")
    glowing_fin("near_pec", "near_pec", 62,
                [(368, 176), (352, 196), (322, 224), (284, 246, True), (300, 226), (316, 208), (330, 194), (340, 184)],
                [(284, 246), (300, 226), (316, 208), (330, 194), (340, 184)], C, "Pectoral Fin - near")


def draw() -> str:
    svg.configure(dx=60.0, dy=60.0, ink=INK, ow=OW, colors=C)
    fin_parts()
    tail_parts()
    torso_part()
    mouth_floor_part()
    jaw_part()
    head_part()
    eye_parts()
    return svg.document(
        size=(W, H),
        design="burning-flying-shark-side-v2",
        layer_id="shark-side",
        label="Shark - Side Right",
        comment=[
            "  <!-- The burning flying shark: a pirate sky-mount in side view, facing right,",
            "       charred skin cracked with magma, fins glowing at their trailing edges, a",
            "       saddle, girth, stirrup and reins on its back. The rig publishes this 620x360",
            "       drawing at 0.36 px per unit; its flames are effects the target draws.",
            "       Each part is a layer with a data-rig-part name; the rig in",
            "       targets/characters/rigged/burning_flying_shark/ turns these parts about their",
            "       joints. *_ink layers are each body segment's silhouette grown by the outline",
            "       width, painted beneath every body fill so the segments read as one outlined",
            "       silhouette with no seams at their joints. The eye states sit on top of each",
            "       other: the rig shows one at a time (data-rig-opacity).",
            "       The hidden Rig Joints layer marks every joint the skeleton is built on. -->",
        ],
        joints=svg.joints_layer(J),
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    Path(sys.argv[1]).write_text(draw())
