#!/usr/bin/env python3
"""How the small dinosaurs' SVGs were first drawn (reference, not authority).

``data/characters/<name>/<name>.svg`` for the ``compsognathus``, the
``dilophosaurus`` and the ``pachycephalosaurus`` own the art; this script
reproduces them as first committed (less the rig catalog
``scripts/build_ratite_rigs.py`` installs).

    uv run python scripts/svg_art/dinosaurs_art.py OUT_DIR

Three dinosaurs that walk on two legs, each a side view facing right on a
512x512 canvas, ground y=416. They are drawn by one function from a few
measures and a head, on the joints of ``rigbuild.ratite`` (a body carried
level, a neck in its own bone, a head with a hinged jaw, a long tail, an arm
per side on the ``<side>_wing`` bone, and a leg per side that folds at the
hock).

- compsognathus: tiny and slender (the whole drawing is the dilophosaurus's
  build at 0.62, published at 0.25).
- dilophosaurus: olive, with two thin crests on its skull. It spits.
- pachycephalosaurus: sand and rust, with a dome of bone on its skull and
  knobs behind it. It runs at things head first.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

import svgkit as svg
from birdkit import along, ellipse, eye_states, legs, line, outlined, part, path, smooth, tube

W, H = 512, 512
INK = "#1d1418"
OW = 1.6
Point = Tuple[float, float]

#: The joints of the build, before a dinosaur's own scale.
BUILD = dict(
    body=(236.0, 262.0), neck=(296.0, 246.0), head=(350.0, 178.0), beak_tip=(416.0, 190.0), jaw=(364.0, 196.0),
    tail=(190.0, 260.0), tail_tip=(44.0, 284.0),
    near_shoulder=(290.0, 268.0), near_wingtip=(322.0, 314.0), far_shoulder=(280.0, 264.0), far_wingtip=(310.0, 308.0),
    near_hip=(234.0, 284.0), near_knee=(208.0, 344.0), near_ankle=(238.0, 404.0),
    far_hip=(216.0, 282.0), far_knee=(192.0, 342.0), far_ankle=(220.0, 404.0),
)
#: A lower head, for a dinosaur that carries its skull out in front to ram.
LOW_HEAD = dict(BUILD, head=(346.0, 206.0), beak_tip=(408.0, 226.0), jaw=(358.0, 226.0))


def eyes(ex: float, ey: float, r: float, iris: str, lid: str) -> Dict[str, list]:
    pupil = "#120d0f"
    return {
        "open": [ellipse(ex, ey, r, r, iris, INK, 1.3), ellipse(ex + 0.8, ey, r * 0.28, r * 0.62, pupil),
                 ellipse(ex - r * 0.3, ey - r * 0.35, r * 0.2, r * 0.2, "#ffffff")],
        "angry": [ellipse(ex, ey, r, r, iris, INK, 1.3), ellipse(ex + 1.0, ey + 0.4, r * 0.2, r * 0.5, pupil),
                  path(smooth([(ex - r - 3, ey - r - 3, True), (ex + r + 3, ey - r * 0.2, True),
                               (ex + r + 3, ey - r - 3, True)]), lid, INK, 1.0)],
        "shut": [line([(ex - r, ey), (ex, ey + r * 0.5), (ex + r, ey)], INK, 2.0)],
        "dead": [line([(ex - r * 0.8, ey - r * 0.8), (ex + r * 0.8, ey + r * 0.8)], INK, 2.0),
                 line([(ex - r * 0.8, ey + r * 0.8), (ex + r * 0.8, ey - r * 0.8)], INK, 2.0)],
    }


def draw(name: str, label: str, C: Dict[str, str], *, head: str, scale: Optional[Tuple[float, float, float]] = None,
         stripes: bool = True) -> str:
    """One two-legged dinosaur. ``head`` is ``crests``, ``dome`` or ``plain``;
    ``scale`` is ``(cx, cy, k)``: the whole drawing made smaller about a point
    on the ground."""
    J = LOW_HEAD if head == "dome" else BUILD
    svg.configure(dx=0.0, dy=0.0, ink=INK, ow=OW, colors=C)
    svg.transform(scale)
    # The tail: long, level and stiff, to a thin end.
    tail_c = [(198, 262), (150, 266), (100, 274), (44, 284)]
    items = [line([along(tail_c, 0.05), along(tail_c, 0.5), along(tail_c, 0.95)], C["dark"], 5.0)]
    if stripes:
        for u in (0.2, 0.35, 0.5, 0.65, 0.8):
            x, y = along(tail_c, u)
            items.append(line([(x - 3, y - 20 * (1 - u)), (x + 3, y + 2)], C["deep"], 3.0))
    part("tail", "Tail", "tail", "tail", 10, outlined(smooth(tube(tail_c, 24.0, 3.0)), C["skin"], items, "clip-tail"))
    # The arms: small, held in front, two claws each.
    for side, z in (("far", 16), ("near", 52)):
        sh, tip = J[f"{side}_shoulder"], J[f"{side}_wingtip"]
        fill = C["dark"] if side == "far" else C["skin"]
        arm = outlined(svg.capsule(sh, tip, 7.0, 4.5), fill)
        for dx, dy in ((6, 8), (-1, 10)):
            arm.append(path(smooth([(tip[0], tip[1] - 2), (tip[0] + dx, tip[1] + dy)], closed=False), "none", C["claw"], 2.2))
        part(f"{side}-arm", f"Arm - {side}", f"{side}_arm", f"{side}_wing", z, arm)
    for side, z in (("far", 18), ("near", 40)):
        far = side == "far"
        legs(J, side, z, thigh=C["dark"] if far else C["skin"], thigh_shade=C["deep"],
             shank=C["dark"] if far else C["skin"], shank_dark=C["deep"], claw=C["claw"],
             toes=((-8, 9), (16, 12), (30, 9)), thigh_r=(25.0, 11.0), shank_r=(8.0, 6.0), toe_r=(5.0, 3.4), claw_len=6.0)
    sil = smooth([(304, 246), (310, 268), (296, 290), (260, 302), (222, 300), (192, 286), (182, 262), (194, 240),
                  (226, 228), (266, 228), (292, 234)])
    items = [
        path(smooth([(200, 240), (232, 230), (270, 230), (296, 240), (262, 244), (224, 244)]), C["dark"]),
        path(smooth([(196, 284), (226, 298), (262, 300), (294, 290), (264, 288), (226, 286)]), C["belly"]),
    ]
    if stripes:
        for k in range(5):
            x = 208 + 20 * k
            items.append(line([(x, 230), (x - 4, 250), (x - 10, 264)], C["deep"], 3.0))
    part("body", "Body", "body", "body", 30, outlined(sil, C["skin"], items, "clip-body"))
    # The neck, forward and up to the head.
    hx, hy = J["head"]
    neck_c = [(292, 250), (314, 228), (332, 204), (hx - 4, hy + 6)]
    items = [line([along(neck_c, 0.1), along(neck_c, 0.9)], C["belly"], 6.0)]
    sil = smooth(tube(neck_c, 17.0, 12.0))
    part("neck", "Neck", "neck", "neck", 60, outlined(sil, C["skin"], [
        path(smooth([(neck_c[0][0] - 14, neck_c[0][1] - 8), (neck_c[2][0] - 12, neck_c[2][1] - 8),
                     (neck_c[3][0] - 8, neck_c[3][1] - 6), (neck_c[3][0], neck_c[3][1]), (neck_c[1][0], neck_c[1][1])]),
             C["dark"])] + items, "clip-neck"))
    # The head: a long skull with teeth, and what it wears on top.
    bx, by = J["beak_tip"]
    jx, jy = J["jaw"]
    body = []
    if head == "crests":
        for dx, fill in ((-6.0, C["crest_dark"]), (4.0, C["crest"])):
            crest = smooth([(hx - 4 + dx, hy - 10, True), (hx + 14 + dx, hy - 40), (hx + 40 + dx, hy - 38),
                            (hx + 50 + dx, hy - 14, True)])
            body += outlined(crest, fill, [line([(hx + 6 + dx, hy - 16), (hx + 20 + dx, hy - 34), (hx + 40 + dx, hy - 24)],
                                                C["crest_dark"], 1.4)], f"clip-crest-{int(dx)}")
    skull = smooth([(hx - 14, hy + 2), (hx - 10, hy - 14), (hx + 10, hy - 20), (hx + 40, hy - 14), (bx - 4, by - 14),
                    (bx, by), (bx - 18, by + 6), (jx + 2, jy), (hx - 6, hy + 16)])
    items = [path(smooth([(hx - 10, hy - 12), (hx + 10, hy - 18), (hx + 38, hy - 12), (hx + 14, hy - 8)]), C["dark"]),
             ellipse(bx - 10, by - 8, 2.0, 1.6, C["deep"])]
    body += outlined(skull, C["skin"], items, "clip-skull")
    # the teeth of the upper jaw
    for k in range(5):
        tx = jx + 8 + k * (bx - jx - 14) / 5.0
        body.append(path(svg.poly([(tx, by + 2 - 0.2 * k), (tx + 5, by + 2 - 0.2 * k), (tx + 2.5, by + 9 - 0.2 * k)]), "#fbf6e6", INK, 0.7))
    if head == "dome":
        # the dome of bone, and the knobs behind it
        for kx, ky in ((hx - 16, hy - 6), (hx - 12, hy + 4), (hx - 18, hy + 12)):
            body += outlined(svg.poly([(kx + 6, ky - 4), (kx - 8, ky), (kx + 6, ky + 4)]), C["dome_dark"])
        dome = smooth([(hx - 14, hy - 4), (hx - 8, hy - 30), (hx + 16, hy - 40), (hx + 40, hy - 30), (hx + 46, hy - 8),
                       (hx + 20, hy - 4)])
        body += outlined(dome, C["dome"], [path(smooth([(hx - 4, hy - 28), (hx + 14, hy - 36), (hx + 34, hy - 30),
                                                         (hx + 16, hy - 26)]), "#fffaf0"),
                                           line([(hx - 8, hy - 8), (hx + 20, hy - 10), (hx + 42, hy - 10)], C["dome_dark"], 1.6)],
                         "clip-dome")
    part("head", "Head", "head", "head", 70, body)
    lower = smooth([(jx - 4, jy, True), (bx - 16, by + 6, True), (bx - 24, by + 16), (jx + 4, jy + 12), (jx - 6, jy + 8, True)])
    part("jaw", "Lower Jaw", "jaw", "jaw", 69, outlined(lower, C["belly"], [
        line([(jx, jy + 6), (bx - 24, by + 12)], C["dark"], 1.2)], "clip-jaw"))
    ex, ey = (hx + 20, hy - 6) if head != "dome" else (hx + 24, hy + 2)
    eye_states("eye", "head", 72, eyes(ex, ey, 6.0, C["iris"], C["deep"]))
    xf = {k: scale for k in J} if scale else None
    svg.transform(None)
    return svg.document(
        size=(W, H), design=f"{name}-side", layer_id=f"{name}-side", label=f"{label} - Side Right",
        comment=[
            f"  <!-- The {label.lower()}, side view facing right, on a 512x512 drawing whose",
            "       ground is y=416. Each part is a layer with a data-rig-part name;",
            f"       rigged/{name}/ turns them about their joints. The eye has open / angry /",
            "       shut / dead. The hidden Rig Joints layer marks every joint. -->",
        ],
        joints=svg.joints_layer(J, xf),
    )


DILO = dict(skin="#7a9450", dark="#536b36", deep="#34461f", belly="#d6cf96", claw="#2a2418", iris="#f2c230",
            crest="#e0602c", crest_dark="#a23a18")
PACHY = dict(skin="#b88d58", dark="#8a5e34", deep="#5e3c1e", belly="#e6d6a8", claw="#3a2a18", iris="#e8a02c",
             dome="#eadcb4", dome_dark="#b39c68")
COMPY = dict(skin="#6fa06a", dark="#467a4c", deep="#2c5232", belly="#e2dfa6", claw="#22301e", iris="#f2c230")
#: The compsognathus is the build at this scale, about a point on the ground under it.
COMPY_SCALE = (236.0, 416.0, 0.62)

DRAW = {
    "dilophosaurus": lambda: draw("dilophosaurus", "Dilophosaurus", DILO, head="crests"),
    "pachycephalosaurus": lambda: draw("pachycephalosaurus", "Pachycephalosaurus", PACHY, head="dome", stripes=False),
    "compsognathus": lambda: draw("compsognathus", "Compsognathus", COMPY, head="plain", scale=COMPY_SCALE),
}

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for name, fn in DRAW.items():
        (out / f"{name}.svg").write_text(fn())
