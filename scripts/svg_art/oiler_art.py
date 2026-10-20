#!/usr/bin/env python3
"""Oiler, redesigned: Euler as a scholar-mechanic in a head wrap and a silk banyan.

    uv run python scripts/svg_art/oiler_art.py --all DIR   # every view of every look, to DIR

Jon, 2026-10-20, after the first candidate round: "it's not actually supposed
to be a turban. it's a head wrap in combination with a silk banyan. the
workshop version is better. and the smile shouldn't be so much a happy smile
as much as a knowing smile. he should give off a wise vibe. we're also going
to need the side view the three quarters view in the front view." And: "he's
also probably going to be an asymmetric character, due to his eye".

CANDIDATES, NOT CAST: nothing registers these drawings yet. Oiler's game art is
still ``data/characters/oiler/oiler-multiview.svg``; once Jon approves this
turnaround it is redrawn there, in place, with a design_history lineage entry.

THE DESIGN.  The workshop round's clothes (a linen shirt, an ochre waistcoat, a
long leather apron with its pouch, dark breeches, boots) under an open silk
banyan, the loose gown a gentleman of his day wore at home and at work, its
sleeves pushed up to the elbow so the forearms and the hands are bare; a
lining of pale straw silk shows at the shawl collar, the front edges and the
turned-back cuffs.  On his head a soft linen wrap, close to the skull, its
end tucked at the left and hanging to the nape.  A long straight nose, a full
closed mouth lifted at one corner (his left): a knowing smile, not a happy
one, under eyes that sit a little narrowed.

ASYMMETRY IS THE CHARACTER.  His RIGHT eye is the failing one in every view:
a heavier, lower lid over a clouded iris, a swollen bag, a lower brow.  The
side view faces right and so shows his right side; the three-quarter view
turns toward screen-right with his right side near; the front view has it on
screen-left.  Mirroring a sheet moves the bad eye to the other side, so a
left-facing Oiler needs its own drawing rather than a flip.

House style: the Colonial Statesman's (flat cel shading, thin warm ink, the
shade below-left and the light above-right), adult proportions.
"""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path
from typing import Callable, Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import svgkit as svg  # noqa: E402
from svgkit import capsule, ellipse, line, part, path, smooth  # noqa: E402

W = H = 560
INK = "#1d1714"
OW = 1.5
GROUND_Y = 502.0
#: Shade down-left, light up-right.
SD, LD = (-1.0, 0.6), (1.0, -0.8)

BASE = dict(
    skin="#e7bf9c", skin_sh="#c99a78", skin_lt="#f4d6bc", skin_dk="#9c6a52", lip="#bd8070", lip_dk="#8a4e42",
    wrap="#e6e4e0", wrap_sh="#b4b3b4", wrap_lt="#fbfaf7", wrap_dk="#8c8b8f", blush="#eab69c",
    hair="#a59684", hair_sh="#7f7264", hair_lt="#c0b4a4", brow="#a8927c",
    shirt="#ece6da", shirt_sh="#c9c0ae", shirt_lt="#faf7f0",
    vest="#b07a2a", vest_sh="#87591a", vest_lt="#c9933f", button="#c9a24a",
    apron="#6b4a33", apron_sh="#4a3220", apron_lt="#8a6347",
    breech="#3b3f4a", breech_sh="#272a33", breech_lt="#50566a",
    boot="#3a2a20", boot_sh="#1e150f", boot_lt="#5a4434",
    lining="#e2d3a4", lining_sh="#bfae7c", lining_lt="#f2e8c6",
    iris="#6f93b8", cloud="#9a968e",
)
LOOKS = {
    "teal": dict(label="teal silk banyan", gown="#2c6a78", gown_sh="#1c4954", gown_lt="#4c92a0", sheen="#86c3c6"),
    # the 1753 pastel's banyan: blue silk with dark stripes, faced in dark silk
    "teal_portrait": dict(label="teal striped banyan, dark facings (the 1753 pastel)", gown="#2f7286", gown_sh="#1e4f5e", gown_lt="#4c95a8",
                          sheen="#8cc8d0", pattern="stripes", stripe="#25343c",
                          lining="#3b4048", lining_sh="#272a30", lining_lt="#5d636e"),
    "wine": dict(label="wine silk banyan", gown="#6c2a36", gown_sh="#4a1a24", gown_lt="#8e4250", sheen="#c27a84"),
    "slate": dict(label="slate-violet silk banyan", gown="#4a4a6e", gown_sh="#33334e", gown_lt="#66688e", sheen="#9a9cc0"),
}
O: Dict = {}

#: Every design point passes through svgkit's ``P``; this wraps it with a
#: front-to-back squeeze (``sq``: about ``x = cx`` by ``k``) and a mirror for
#: the left-facing views, which are drawn as his other side facing right and
#: then flipped -- so the light stays above-right in both.
_P0 = svg.P
_MAP: Dict = {"sq": None, "mirror": False}


def _P(x, y):
    if _MAP["sq"]:
        cx, k = _MAP["sq"]
        x = cx + (x - cx) * k
    X, Y = _P0(x, y)
    X += _MAP.get("dx") or 0.0
    return (W - X if _MAP["mirror"] else X), Y


svg.P = _P


def left() -> bool:
    """True while drawing a left-facing view: his LEFT side is the one shown."""
    return O.get("facing") == "left"


def use(look: str) -> None:
    O.clear()
    O.update(BASE)
    O.update(LOOKS[look])


_N = [0]


def uid(tag="c"):
    _N[0] += 1
    return f"oil{tag}{_N[0]}"


def cel(d, base, shade, light=None, items=(), sdir=SD, ldir=LD, s=5.0, l=3.0, sw=None, ink=None, edges=None):
    """A shape: its fill, a ``shade`` band along the edges facing ``sdir`` and a
    ``light`` band along those facing ``ldir`` (clipped inside), the detail
    ``items``, then the thin ink outline -- or, given ``edges`` (open runs of
    points), ink on those runs only, so a seam hidden under cloth stays clean."""
    cid = uid()
    sx, sy = -sdir[0] * s, -sdir[1] * s
    out = [f'<clipPath id="{cid}"><path d="{d}" /></clipPath>',
           f'<clipPath id="{cid}s"><path d="{d}" transform="translate({sx:.2f} {sy:.2f})" /></clipPath>',
           f'<g clip-path="url(#{cid})">', path(d, shade), f'<g clip-path="url(#{cid}s)">']
    if light:
        lx, ly = -ldir[0] * l, -ldir[1] * l
        out += [path(d, light), path(d, base, extra=f' transform="translate({lx:.2f} {ly:.2f})"')]
    else:
        out.append(path(d, base))
    out.append("</g>")
    out += list(items)
    out.append("</g>")
    if edges is None:
        out.append(path(d, "none", ink or INK, sw or 2 * OW))
    else:
        out += [line(run, ink or INK, sw or 2 * OW) for run in edges]
    return out


def C(d, key, items=(), **kw):
    return cel(d, O[key], O[key + "_sh"], O.get(key + "_lt"), items, **kw)


def far(d, key, items=(), **kw):
    """A shape on the far side of the body: its colour in shade, no light band."""
    return cel(d, O[key + "_sh"], O[key + "_sh"], None, items, s=1, **kw)


def frame(origin, u_ang):
    ux, uy = math.cos(u_ang), math.sin(u_ang)
    nx, ny = -uy, ux
    return lambda t, s: (origin[0] + ux * t + nx * s, origin[1] + uy * t + ny * s)


def ang(a, b):
    return math.atan2(b[1] - a[1], b[0] - a[0])


def mx(pts, cx=280.0):
    """Mirror points across ``x = cx`` (the front view's left half from its right)."""
    return [(2 * cx - p[0], p[1]) + tuple(p[2:]) for p in pts]


def sheen(pts, w=1.3):
    return line(pts, O["sheen"], w)


def damask(x0, y0, x1, y1, step=17.0):
    """The silk's woven figure: a small four-petal sprig on a diamond grid --
    or, for the portrait's banyan, its dark stripes."""
    out = []
    if O.get("pattern") == "stripes":
        return [line([(x, y0 - 4), (x, y1 + 4)], O["stripe"], 4.4) for x in range(int(x0) + 4, int(x1), 14)]
    for j, y in enumerate(range(int(y0), int(y1), int(step))):
        for x in range(int(x0 + (step / 2 if j % 2 else 0)), int(x1), int(step)):
            for dx, dy in ((0, -1.6), (0, 1.6), (-1.6, 0), (1.6, 0)):
                out.append(ellipse(x + dx, y + dy, 1.0, 1.0, O["gown_lt"]))
    return out


#: Hands are drawn this much larger than their first sketch: they matter.
HAND = 1.2


# ---- shared pieces: hands, forearms, boots ---------------------------------------------------

def finger(b, m, e, w0, w1, w2):
    """One finger as a single tapered outline through its base ``b``, middle
    knuckle ``m`` and tip ``e``, half-widths ``w0``, ``w1``, ``w2``."""
    def nrm(p0, p1):
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(dx, dy) or 1.0
        return -dy / L, dx / L, dx / L, dy / L
    n0x, n0y, _, _ = nrm(b, m)
    n1x, n1y, ux, uy = nrm(m, e)
    side_a = [(b[0] + n0x * w0, b[1] + n0y * w0), (m[0] + (n0x + n1x) / 2 * w1, m[1] + (n0y + n1y) / 2 * w1), (e[0] + n1x * w2, e[1] + n1y * w2)]
    side_b = [(e[0] - n1x * w2, e[1] - n1y * w2), (m[0] - (n0x + n1x) / 2 * w1, m[1] - (n0y + n1y) / 2 * w1), (b[0] - n0x * w0, b[1] - n0y * w0)]
    tip = (e[0] + ux * w2 * 1.1, e[1] + uy * w2 * 1.1)
    return smooth(side_a + [tip] + side_b)


def hand_side(wrist, a, near=True):
    """A relaxed hand hanging from ``wrist`` along ``a`` (radians), seen from its
    back: the thumb, four fingers side by side (the index at the front, toward
    +x) curling a little forward, each in a finer ink so it reads, then the
    back of the hand, inked only where it is not joined to the wrist.  ``t``
    runs down the hand, ``f`` toward the front."""
    q = frame(wrist, a)
    p = lambda t, f: q(HAND * t, -HAND * f)  # the frame's +s is the back while the hand hangs down
    sk, sh, lt, dk = (O["skin"], O["skin_sh"], O["skin_lt"], O["skin_dk"]) if near else (O["skin_sh"], O["skin_dk"], None, O["skin_dk"])
    fine = 1.3
    out = []
    thumb = finger(p(4, 5.0), p(11, 8.6), p(16.5, 9.6), 3.4 * HAND, 2.8 * HAND, 2.2 * HAND)
    out += cel(thumb, sk, sh, lt, [line([p(14.6, 8.0), p(15.4, 10.8)], dk, 0.7)], s=1.6, sw=fine)
    for f0, length, curl in ((-5.0, 12.5, 2.0), (-1.7, 15.0, 2.8), (1.6, 16.0, 3.4), (4.8, 14.5, 3.6)):
        fing = finger(p(10, f0), p(10 + length * 0.55, f0 + curl * 0.3), p(10 + length, f0 + curl), 2.1 * HAND, 1.95 * HAND, 1.7 * HAND)
        out += cel(fing, sk, sh, lt if f0 > 4 else None, [line([p(10 + length * 0.55, f0 + curl * 0.3 - 1.2), p(10 + length * 0.55, f0 + curl * 0.3 + 1.2)],
                                                              sh, 0.7)], s=1.0, sw=fine)
    run = [p(-1, -6.8), p(6, -7.4), p(11, -7.0), p(13.5, -3), p(14, 2), p(13, 6.6), p(7, 7.2), p(-1, 6.8)]
    palm = smooth([p(-3, -6.6)] + run + [p(-3, 6.6)])
    items = [line([p(4, -2.5), p(9.5, -3.2)], sh, 0.8), line([p(4, 1.5), p(9.5, 1.5)], sh, 0.8)]
    out += cel(palm, sk, sh, lt, items, s=2.5, edges=[run])
    return out


def hand_front(wrist, a, inward):
    """A relaxed hand hanging at his side, seen from the front: the palm faces
    his thigh (``inward`` is +1 when the body is toward +x), so the camera sees
    the back of the hand edge-on, the index finger curling in toward the thigh
    with the tips of the others just behind it, and the thumb lying down the
    front of the hand."""
    q = frame(wrist, a)
    p = lambda t, i: q(HAND * t, -HAND * i * inward)  # i > 0 runs toward his body
    sk, sh, lt, dk = O["skin"], O["skin_sh"], O["skin_lt"], O["skin_dk"]
    fine = 1.3
    out = []
    for i0, length, curl in ((3.2, 13.0, 3.0), (1.4, 14.5, 3.4)):  # ring and middle, behind
        out += cel(finger(p(9, i0), p(9 + length * 0.6, i0 + curl * 0.4), p(9 + length, i0 + curl), 2.1 * HAND, 2.0 * HAND, 1.7 * HAND),
                   sh, dk, None, [], s=1.0, sw=fine)
    run = [p(-1, -5.4), p(7, -6.0), p(12, -5.0), p(13.5, 0), p(12.5, 5.0), p(6, 5.6), p(-1, 5.4)]
    out += cel(smooth([p(-3, -5.2)] + run + [p(-3, 5.2)]), sk, sh, lt, [], s=2.0, edges=[run])
    idx = finger(p(10, -1.0), p(18.5, 0.6), p(24, 4.0), 2.4 * HAND, 2.2 * HAND, 1.9 * HAND)
    out += cel(idx, sk, sh, lt, [line([p(18.4, -1.4), p(18.8, 2.4)], sh, 0.7)], s=1.2, sw=fine)
    thumb = finger(p(3, -4.4), p(11, -6.0), p(17.5, -4.2), 3.0 * HAND, 2.6 * HAND, 2.1 * HAND)
    out += cel(thumb, sk, sh, lt, [line([p(15.2, -6.2), p(15.8, -2.6)], dk, 0.7)], s=1.6, sw=fine)
    return out


def forearm(e, w, near=True, r=(9.0, 7.8)):
    """A bare forearm (the banyan and the shirt pushed up to the elbow), with
    the roll of the linen shirt sleeve at its top."""
    a = ang(e, w)
    p = frame(e, a)
    if near:
        out = cel(capsule(e, w, *r), O["skin"], O["skin_sh"], O["skin_lt"], [line([p(12, -3), p(24, -3.5)], O["skin_sh"], 0.8)], s=3)
        return out + C(capsule(p(-2, 0), p(7, 0), r[0] + 3.5, r[0] + 3.2), "shirt", [line([p(2, -11), p(3, 11)], O["shirt_sh"], 1.0)], s=3)
    out = cel(capsule(e, w, r[0] - 0.8, r[1] - 0.6), O["skin_sh"], O["skin_dk"], None, [], s=1)
    return out + far(capsule(p(-2, 0), p(7, 0), r[0] + 2.6, r[0] + 2.3), "shirt")


def sleeve(s, e, near=True, r=(12.5, 13.0)):
    """The banyan's wide sleeve from the shoulder to the elbow, its lining of
    straw silk turned back in a deep cuff where it was pushed up."""
    a = ang(s, e)
    p = frame(e, a)
    body = capsule(s, e, *r)
    cuff = smooth([p(-7, -r[1] - 0.8), p(1.5, -r[1] - 1.4), p(3, 0), p(1.5, r[1] + 1.4), p(-7, r[1] + 0.8)])
    if near:
        bx = sorted([s[0], e[0]])
        out = C(body, "gown", damask(bx[0] - 16, s[1] - 14, bx[1] + 16, e[1] + 14) + [sheen([frame(s, a)(4, -r[0] * 0.45), frame(s, a)(20, -r[0] * 0.5)]),
                                                                                    line([frame(s, a)(6, 4), frame(s, a)(24, 5)], O["gown_sh"], 1.1)], s=5)
        return out + C(cuff, "lining", [line([p(-4, -r[1]), p(-3, r[1])], O["lining_sh"], 1.0)], s=3)
    return far(body, "gown") + far(cuff, "lining")


def leg_piece(hip, knee, ankle, toe_dx, piece, near=True, front=False):
    """One rigid piece of a leg: the breeched ``thigh``; the ``shin`` (the
    breeches below the knee and the boot's shaft over them); the booted
    ``foot``, its toe ``toe_dx`` ahead of the ankle (0 seen from the front)."""
    (kx, ky), (ax, ay) = knee, ankle
    if piece == "thigh":
        d = capsule(hip, knee, 13, 11)
        return C(d, "breech", [], s=4) if near else far(d, "breech")
    sg = 1 if toe_dx >= 0 else -1
    if piece == "shin":
        out = C(capsule(knee, (ax, ay - 10), 10, 8), "breech", [], s=4) if near else far(capsule(knee, (ax, ay - 10), 10, 8), "breech")
        if front:
            d = smooth([(kx - 10, ky + 12), (kx + 10, ky + 12), (ax + 9, ay - 8), (ax + 9.6, ay + 4, True), (ax - 9.6, ay + 4, True), (ax - 9, ay - 8)])
        else:
            d = smooth([(kx - 11 * sg, ky + 12), (kx + 10 * sg, ky + 10), (ax + 8 * sg, ay - 8), (ax + 9 * sg, ay + 4, True), (ax - 10 * sg, ay + 4, True),
                        (ax - 10 * sg, ay - 14)])
        top = [line([(kx - 11, ky + 20), (kx + 10, ky + 19)], O["boot_sh"], 1.3)]
        return out + (C(d, "boot", top, s=4) if near else cel(d, O["boot_sh"], "#120c08", None, [], s=1))
    if front:
        d = smooth([(ax - 9.6, ay - 4), (ax + 9.6, ay - 4), (ax + 11, ay + 6), (ax + 8, ay + 14, True), (ax - 8, ay + 14, True), (ax - 11, ay + 6)])
        items = [line([(ax - 9, ay + 6), (ax + 9, ay + 6)], O["boot_sh"], 1.0)]
    else:
        d = smooth([(ax - 10 * sg, ay - 6), (ax + 6 * sg, ay - 6), (ax + toe_dx, ay + 8), (ax + toe_dx + 2 * sg, ay + 14, True), (ax - 10 * sg, ay + 16, True)])
        items = [line([(ax - 9 * sg, ay + 8), (ax + 10 * sg, ay + 8)], O["boot_sh"], 1.0)]
    return C(d, "boot", items, s=4) if near else cel(d, O["boot_sh"], "#120c08", None, [], s=1)


def pelvis_block(pts):
    """The seat of the breeches across the hips, under the coat: it hides the
    roots of the thighs however the legs swing."""
    return C(smooth(pts), "breech", [], s=3)


# ============================================================================================
# SIDE VIEW (facing right; his right side toward the camera)
# ============================================================================================

S_LEGS = {"near": ((278, 348), (284, 416), (279, 484)), "far": ((262, 348), (260, 416), (252, 484))}
S_FAR_ARM = ((262, 262), (256, 314), (266, 356))
S_NEAR_ARM = ((272, 262), (266, 314), (280, 354))
S_EYE = (292.0, 203.0)
#: The side cap was drawn in first-sketch units: it is scaled about the throat
#: and carried back by ``S_HEAD_DX`` to sit on the head, drawn at its final measure.
S_HEAD_XF = (286.0, 246.0, 0.88)
S_HEAD_DX = -6.0


def s_joints():
    ns, ne, nw = S_NEAR_ARM
    fs, fe, fw = S_FAR_ARM
    J = {"body": ("", 270.0, 348.0), "torso": ("body", 270.0, 348.0), "head": ("torso", 284.0 + S_HEAD_DX, 238.0),
         "near_arm_u": ("torso", *ns), "near_arm_l": ("near_arm_u", *ne), "near_hand": ("near_arm_l", *nw),
         "far_arm_u": ("torso", *fs), "far_arm_l": ("far_arm_u", *fe), "far_hand": ("far_arm_l", *fw)}
    for side in ("near", "far"):
        hip, knee, ankle = S_LEGS[side]
        J[f"{side}_leg_u"] = ("body", *hip)
        J[f"{side}_leg_l"] = (f"{side}_leg_u", *knee)
        J[f"{side}_foot"] = (f"{side}_leg_l", *ankle)
    return J


def s_leg(side, piece):
    hip, knee, ankle = S_LEGS[side]
    return leg_piece(hip, knee, ankle, 26, piece, side == "near")


def s_skirt(side):
    """The banyan below the waist, in two panels so a stride swings it: the near
    one over the near thigh, its front edge lined, the far one behind."""
    if side == "far":
        d = smooth([(246, 330), (270, 332), (272, 380), (274, 436, True), (232, 437, True), (236, 396), (242, 360)])
        return far(d, "gown")
    d = smooth([(246, 330), (290, 334), (293, 380), (296, 438, True), (236, 440, True), (240, 400), (244, 362)])
    items = damask(228, 336, 300, 440) + [line([(254, 352), (250, 400), (248, 436)], O["gown_sh"], 1.3), line([(272, 356), (274, 436)], O["gown_sh"], 1.1),
                                          sheen([(262, 360), (260, 400)]), sheen([(282, 372), (284, 420)], 1.1)]
    out = C(d, "gown", items, s=6, edges=[[(290, 334), (293, 380), (296, 438)], [(296, 438), (236, 440)], [(236, 440), (240, 400), (244, 362), (246, 340)]])
    edge = smooth([(287, 330), (292, 330), (295, 380), (297, 438, True), (290, 438, True), (288, 380)])
    out += C(edge, "lining", [], s=2, edges=[[(292, 330), (295, 380), (297, 438)], [(290, 438), (288, 380), (287, 330)]])
    hem = smooth([(236, 435), (296, 434), (296, 440, True), (236, 441, True)])
    return out + C(hem, "lining", [], s=1.5)


def s_vest():
    shirt = smooth([(288, 240), (268, 238), (254, 248), (246, 270), (244, 300), (248, 330), (262, 346), (290, 348), (300, 320), (300, 280), (296, 252)])
    out = C(shirt, "shirt", [], s=4)
    vest = smooth([(292, 244), (300, 252), (305, 280), (308, 314), (305, 342), (296, 354, True), (252, 350, True), (246, 320), (246, 284), (254, 256),
                   (270, 246)])
    items = [ellipse(px, py, 1.7, 1.7, O["button"], INK, 0.6) for px, py in [(302, 266), (305, 282), (306, 298), (306, 314)]]
    items.append(line([(272, 250), (280, 300), (286, 350)], O["vest_sh"], 1.1))
    return out + C(vest, "vest", items, s=5)


def s_gown():
    """The banyan from the shoulders to the waist, hanging open at the front."""
    back = [(291, 356), (292, 320), (294, 290), (293, 262), (288, 246), (276, 238), (264, 238), (254, 244), (249, 260), (247, 290), (246, 324),
            (246, 356)]
    d = smooth([p if i not in (0, len(back) - 1) else p + (True,) for i, p in enumerate(back)])
    items = damask(234, 246, 292, 360) + [line([(256, 262), (252, 300), (252, 344)], O["gown_sh"], 1.3), sheen([(262, 258), (260, 292)]),
                                          sheen([(268, 300), (266, 340)], 1.1)]
    out = C(d, "gown", items, s=6, edges=[back[:6], back[5:]])
    edge = smooth([(284, 244), (291, 248), (295, 262), (297, 290), (295, 320), (293, 354, True), (287, 354, True), (289, 320), (290, 290),
                   (289, 264), (281, 252)])
    return out + C(edge, "lining", [], s=2)


def s_apron():
    bottom = 408  # mid-thigh: bound to the torso, a longer apron juts out like a board when he bends
    d = smooth([(282, 300), (302, 302), (309, 320), (309, 350), (306, bottom - 30), (304, bottom, True), (278, bottom + 2, True), (278, bottom - 30),
                (282, 350)])
    items = [line([(294, 318), (294, bottom - 6)], O["apron_sh"], 1.1)]
    pouch = smooth([(288, 340, True), (307, 340, True), (307, 362, True), (288, 362, True)])
    items += [path(pouch, O["apron_sh"], INK, 1.0), path(smooth([(288, 340, True), (307, 340, True), (305, 348), (290, 348)]), O["apron_lt"], INK, 0.9),
              ellipse(297.5, 346, 1.8, 1.8, O["button"], INK, 0.6)]
    out = C(d, "apron", items, s=4)
    strap = smooth([(286, 302), (304, 302), (304, 309), (286, 310)])
    return out + cel(strap, O["apron_sh"], "#2e2014", None, [], s=1)


def s_neck():
    out = C(smooth([(262, 228), (290, 230), (296, 250), (284, 256), (264, 254)]), "skin", [], s=4)
    # the banyan's shawl collar, rolled round the back of the neck
    collar = smooth([(262, 236), (276, 234), (288, 240), (292, 250), (284, 250), (272, 244), (260, 246)])
    out += C(collar, "lining", [], s=2.5)
    stock = smooth([(271, 236), (293, 238), (298, 250), (274, 252)])
    out += C(stock, "shirt", [line([(275, 244), (295, 245)], O["shirt_sh"], 0.9)], s=3)
    tie = smooth([(292, 244), (301, 246), (305, 256), (300, 262), (304, 272), (298, 280), (294, 268), (291, 256)])
    return out + C(tie, "shirt", [line([(296, 250), (299, 260), (297, 272)], O["shirt_sh"], 1.0)], s=3)


def s_face_points():
    """Euler in profile, drawn to the front view's measure -- the eye at 203,
    the round nose tip at 221, the mouth at 233, the chin at 249, a skull as
    round behind as the front is broad: a short upright forehead under the
    cap, the long upper lip, a small mouth set back, a round chin and a soft
    second chin, the back of the head one curve down to the nape."""
    return [(262, 170), (282, 168.6), (293, 173), (298, 182), (299.8, 190), (299.4, 196), (301.4, 202), (304.6, 209), (307.8, 215), (309.8, 219.4),
            (309.0, 222.8), (305.8, 224.4), (302.6, 224.8), (301.6, 227.0), (302.2, 230.6), (300.4, 233.2, True), (301.8, 235.4), (300.4, 238.4, True),
            (301.4, 242.0), (300.6, 246.4), (296.4, 249.6), (288, 251.2), (278, 250.4), (268, 246.4), (258.6, 238.6), (250.6, 227), (246.4, 212),
            (246.8, 196), (251.6, 181)]


def s_head():
    sk, dk = O["skin_sh"], O["skin_dk"]
    ex, ey = S_EYE
    out = []
    items = [
        # the line of the jaw, back from the chin to under the ear; its shade;
        # the fold of the second chin
        line([(296, 249.4), (284, 247.6), (273, 240), (266, 229), (265, 220)], sk, 1.3),
        path(smooth([(254, 214), (262, 230), (274, 242), (288, 248), (298, 248), (288, 251), (272, 247), (258, 234)]), sk),
        line([(278, 248), (288, 250.6), (297, 249)], sk, 1.2),
        ellipse(285, 222, 8, 5.2, O["blush"]),
        line([(279, 212), (287, 214.6), (294, 213.6)], sk, 1.1),
        # the nose: the round tip's light, the wing and the nostril, the fold
        # from the wing round the full cheek to the corner of the mouth
        ellipse(306.4, 217.0, 2.2, 1.6, O["skin_lt"]),
        path(smooth([(299.4, 216.4), (304, 215.2), (306.6, 219.6), (302.6, 222.2), (299.6, 221)]), sk),
        line([(299.4, 216), (298.8, 219.6), (300.6, 222.4)], dk, 1.0),
        line([(304, 222.4), (306.6, 222.8)], dk, 1.3),
        line([(301, 201), (306, 212)], O["skin_lt"], 1.4),
        # the crease at the root of the nose
        line([(298.4, 193.6), (299.0, 198.0)], dk, 0.8),
    ]
    out += C(smooth(s_face_points()), "skin", items, s=6)
    # the grey-brown hair round the back of the skull under the cap, inked only
    # where it meets the skin, so the head's outline stays one round curve
    hair = [(247.4, 190), (257, 188), (259.6, 202), (257, 218), (252, 227)]
    out += cel(smooth(hair + [(249, 220), (246.6, 206)]), O["hair"], O["hair_sh"], O["hair_lt"], [line([(251.6, 196), (252.6, 212)], O["hair_sh"], 0.9)],
               s=2, edges=[hair])
    if left():  # the cap's long end, hanging behind his left ear down the side of the neck
        out += C(smooth([(250, 186), (259, 190), (261, 210), (258, 236), (255, 262, True), (247, 260, True), (247, 234), (246, 206)]), "wrap",
                 [line([(253, 196), (254, 222), (252, 250)], O["wrap_sh"], 1.1), line([(257, 200), (257, 220)], O["wrap_lt"], 1.2)], s=3)
    out += C(smooth([(258.6, 198), (265.6, 196.6), (268.2, 206), (266, 216.4), (259.6, 215.6)]), "skin",
             [line([(262.4, 201), (265.4, 206), (262.6, 211.4)], dk, 1.0)], s=3)
    # the cap keeps the measure it was drawn in: its first-sketch units, scaled about the throat
    svg.transform(S_HEAD_XF)
    _MAP["dx"] = S_HEAD_DX
    cap = s_wrap()
    svg.transform(None)
    _MAP["dx"] = 0.0
    return out + cap


def s_wrap():
    """The cap in profile: the band round the head above the bare forehead,
    running back over the ear, and the loose cloth above it in rumpled layers
    climbing from the brow toward the back of the head, higher on his left."""
    out = []
    lift = 4.0 if left() else 0.0
    out += layer([(298, 166), (294, 158 - lift), (286, 154 - lift, True), (278, 151 - lift), (268, 149 - lift, True), (260, 148 - lift),
                  (252, 149 - lift, True), (246, 152 - lift), (244, 158, True), (248, 163), (256, 165, True), (268, 166), (280, 169), (292, 172)],
                 [(290, 156 - lift), (268, 150 - lift), (248, 153 - lift)], [[(260, 153), (256, 160)]],
                 [[(270, 150 - lift), (276, 166), (264, 165)], [(254, 150 - lift), (258, 164), (248, 162)]])
    out += layer([(305, 175), (303, 167), (296, 163, True), (286, 160), (274, 158, True), (264, 157), (254, 158, True), (246, 161), (242, 168), (242, 178),
                  (246, 186, True), (252, 192), (260, 192), (268, 184, True), (286, 179)],
                 [(298, 166), (272, 159), (246, 162)], [[(264, 168), (258, 178)], [(246, 170), (248, 182)]],
                 [[(284, 160), (290, 178), (276, 179)], [(256, 158), (260, 190), (250, 190)], [(244, 164), (246, 182), (242, 174)]])
    band = smooth([(250, 186), (266, 179), (286, 174), (303, 173), (308, 177, True), (306, 184, True), (288, 182), (268, 188), (253, 197, True)])
    out += C(band, "wrap", [line([(258, 188), (280, 181), (302, 179)], O["wrap_sh"], 1.0), line([(262, 184), (290, 177)], O["wrap_lt"], 1.2)],
             s=3, sdir=(0.0, 1.0))
    return out


def s_mouth_open():
    return [path(smooth([(295.0, 228.6), (303.4, 229.0), (303.6, 238.6), (296.0, 238.8)]), O["skin"]),
            path(smooth([(297.2, 231.0), (302.6, 230.8), (302.4, 236.8), (298.2, 237.0)]), "#4a2424", INK, 1.2),
            path(smooth([(297.6, 231.2), (302.2, 231.0), (301.8, 232.4), (297.8, 232.6)]), "#efe8dc"),
            path(smooth([(298.0, 235.6), (302.2, 235.4), (301.8, 237.2), (298.2, 237.4)]), O["lip"])]


def s_far_upper():
    s, e, _w = S_FAR_ARM
    return sleeve(s, e, near=False, r=(11.5, 12.0))


def s_far_lower():
    _s, e, w = S_FAR_ARM
    return forearm(e, w, near=False)


def s_far_hand():
    _s, e, w = S_FAR_ARM
    return hand_side(w, ang(e, w), near=False)


def s_near_upper():
    s, e, _w = S_NEAR_ARM
    return sleeve(s, e)


def s_near_lower():
    _s, e, w = S_NEAR_ARM
    return forearm(e, w)


def s_near_hand():
    _s, e, w = S_NEAR_ARM
    return hand_side(w, ang(e, w))


def side_layers():
    return [
        ("far-arm-lower", "Far Arm - Lower", "far_arm_l", "far_arm_l", 6, "", s_far_lower),
        ("far-arm-upper", "Far Arm - Upper", "far_arm_u", "far_arm_u", 7, "", s_far_upper),
        ("far-hand", "Far Hand", "far_hand", "far_arm_hand", 8, "", s_far_hand),
        ("far-skirt", "Far Skirt", "far_skirt", "far_leg_u", 9, "", lambda: s_skirt("far")),
        ("far-thigh", "Far Thigh", "far_leg_u", "far_leg_u", 10, "", lambda: s_leg("far", "thigh")),
        ("far-shin", "Far Shin", "far_leg_l", "far_leg_l", 11, "", lambda: s_leg("far", "shin")),
        ("far-foot", "Far Foot", "far_leg_foot", "far_leg_foot", 12, "", lambda: s_leg("far", "foot")),
        ("pelvis", "Pelvis", "pelvis_yoke", "pelvis", 19, "", lambda: pelvis_block([(252, 332), (290, 334), (292, 362), (252, 362)])),
        ("near-thigh", "Near Thigh", "near_leg_u", "near_leg_u", 20, "", lambda: s_leg("near", "thigh")),
        ("near-shin", "Near Shin", "near_leg_l", "near_leg_l", 21, "", lambda: s_leg("near", "shin")),
        ("near-foot", "Near Foot", "near_leg_foot", "near_leg_foot", 22, "", lambda: s_leg("near", "foot")),
        ("vest", "Shirt and Waistcoat", "vest", "torso", 30, "", s_vest),
        ("gown", "Banyan", "gown", "torso", 36, "", s_gown),
        ("near-skirt", "Near Skirt", "near_skirt", "near_leg_u", 40, "", lambda: s_skirt("near")),
        ("apron", "Apron", "apron", "torso", 44, "", s_apron),
        ("neck", "Neck, Collar and Neckcloth", "neck", "torso", 50, "", s_neck),
        ("head", "Head", "head", "head", 60, "", s_head),
        *face_layers(s_face_features, lambda: [S_EYE], (0.85,), s_mouth_open),
        ("near-arm-lower", "Near Arm - Lower", "near_arm_l", "near_arm_l", 77, "", s_near_lower),
        ("near-arm-upper", "Near Arm - Upper", "near_arm_u", "near_arm_u", 78, "", s_near_upper),
        ("near-hand", "Near Hand", "near_hand", "near_arm_hand", 82, "", s_near_hand),
    ]


# ============================================================================================
# FRONT VIEW (his right on screen-left)
# ============================================================================================

F_CX = 280.0
F_ARM_R = ((246, 264), (240, 312), (238, 356))  # his right, screen-left
F_ARM_L = tuple((2 * F_CX - x, y) for x, y in F_ARM_R)
F_LEG_R = ((268, 350), (267, 416), (266, 484))
F_LEG_L = tuple((2 * F_CX - x, y) for x, y in F_LEG_R)
F_EYE_R, F_EYE_L = (267.5, 203.0), (292.5, 203.0)


def f_joints():
    J = {"body": ("", 280.0, 350.0), "torso": ("body", 280.0, 350.0), "head": ("torso", 280.0, 244.0)}
    for side, (s, e, w) in (("right", F_ARM_R), ("left", F_ARM_L)):
        J[f"{side}_arm_u"] = ("torso", *s)
        J[f"{side}_arm_l"] = (f"{side}_arm_u", *e)
        J[f"{side}_hand"] = (f"{side}_arm_l", *w)
    for side, (h, k, a) in (("right", F_LEG_R), ("left", F_LEG_L)):
        J[f"{side}_leg_u"] = ("body", *h)
        J[f"{side}_leg_l"] = (f"{side}_leg_u", *k)
        J[f"{side}_foot"] = (f"{side}_leg_l", *a)
    return J


def f_wrap_back():
    """The cap's long end, hanging behind his left ear to the collar."""
    d = smooth([(309, 180), (318, 184), (321, 200), (319, 222), (316, 242), (310, 248, True), (308, 234), (310, 212), (307, 194)])
    return C(d, "wrap", [line([(314, 192), (315, 214), (313, 236)], O["wrap_sh"], 1.1), line([(317, 190), (318, 206)], O["wrap_lt"], 1.2)], s=3)


def f_face(cx=280.0, k=1.0):
    """The front face outline: broad and round, full at the cheeks, the jaw
    soft, his left cheek a little fuller where the smile lifts it."""
    pts = [(255, 178), (253, 192), (252, 206), (253, 220), (257, 232), (264, 241), (272, 246.5), (280, 248.5), (288, 246.5), (296, 241), (303.5, 232),
           (307.5, 220), (308.5, 206), (307.5, 192), (305, 178), (296, 171), (280, 169), (264, 171)]
    return smooth([(cx + (x - 280) * k, y) for x, y in pts])


def f_head():
    sk, dk = O["skin_sh"], O["skin_dk"]
    (rx, ry), (lx, ly) = F_EYE_R, F_EYE_L
    out = []
    for sgn in (-1, 1):  # the ears, the grey-brown hair over them
        ex = 280 + sgn * 27.5
        ear = smooth([(ex - sgn * 1, 197), (ex + sgn * 4.5, 195), (ex + sgn * 6.5, 205), (ex + sgn * 4.5, 217), (ex - sgn * 0.5, 217)])
        out += C(ear, "skin", [line([(ex + sgn * 2, 200), (ex + sgn * 4.2, 206), (ex + sgn * 2.4, 212)], dk, 1.0)], s=2)
    for pts in ([(251, 180), (260, 178), (259, 196), (252, 200)], mx([(251, 180), (260, 178), (259, 196), (252, 200)])):
        out += C(smooth(pts), "hair", [], s=2)
    out += C(smooth([(266, 242), (280, 250), (294, 242), (292, 254), (280, 257), (268, 254)]), "skin", [], s=2)  # the second chin
    items = [
        path(smooth([(252, 208), (255, 226), (264, 240), (276, 247), (264, 236), (257, 222)]), sk),
        ellipse(263, 223, 5.5, 3.6, O["blush"]), ellipse(297.5, 222.5, 5.5, 3.6, O["blush"]),
        # the crease between the brows, a line across the forehead
        line([(279.4, 189.4), (280, 196.4)], dk, 0.9), line([(268, 184), (279, 182.4)], sk, 1.0),
        # the nose: a broad bridge, shaded on his right, and a round fleshy tip
        line([(276.6, 203), (275.2, 215)], sk, 1.6), line([(283.4, 203), (284.4, 214)], O["skin_lt"], 1.4),
        path(smooth([(273.2, 218.4), (276.6, 216.4), (280, 217.4), (283.4, 216.4), (286.8, 218.4), (286.2, 223.4), (280, 225.2), (273.8, 223.4)]), sk),
        ellipse(280.6, 219.2, 3.6, 3.0, O["skin"]), ellipse(281.4, 218.4, 1.8, 1.4, O["skin_lt"]),
        line([(272.6, 218.6), (273.6, 223.2), (277, 224.6), (280, 225.6), (283, 224.6), (286.4, 223.2), (287.4, 218.6)], INK, 1.1),
        ellipse(276.8, 223.0, 1.4, 0.8, dk), ellipse(283.2, 223.0, 1.4, 0.8, dk),
    ]
    out += C(f_face(), "skin", items, s=5)
    return out + f_wrap()


def tight(pts):
    """The cap held close: as wide as before over the head, but its loose upper
    layers a little lower and the overhang past his left temple drawn in."""
    out = []
    for p in pts:
        x, y = p[0], p[1]
        if x > 312:
            x = 312 + (x - 312) * 0.6
        if y < 180:
            y = 180 + (y - 180) * 0.92
        out.append((x, y) + tuple(p[2:]))
    return out


def f_wrap():
    return cap_front(tight)


def layer(pts, ridge, folds=(), pockets=(), m=lambda q: q):
    """One loose layer of the cap's silk, rumpled: pinched corners along its
    edges, its shade along the lower edge, deep fold pockets, a bright ridge
    along the top and a few crisp creases."""
    items = [path(smooth(m([tuple(v) + (True,) for v in q])), O["wrap_sh"]) for q in pockets]
    items += [line(m(ridge), O["wrap_lt"], 1.8)] + [line(m(f), O["wrap_dk"], 1.0) for f in folds]
    return C(smooth(m(pts)), "wrap", items, s=5, sdir=(-0.3, 1.0))


def cap_front(m=lambda pts: pts):
    """The cap after the 1753 pastel, from the front (``m`` turns the points
    for the three-quarter view): a band of silk wound round the head above the
    bare forehead, and above it the loose cloth heaped in rumpled layers --
    wider than the head, low on his right and climbing to his left, where it
    overhangs and droops past the temple."""
    out = []
    out += layer([(256, 162), (260, 153), (268, 149, True), (276, 147), (286, 144, True), (294, 143), (304, 141, True), (312, 141), (318, 141, True),
                  (325, 146), (327, 153), (323, 159, True), (314, 160), (304, 162, True), (294, 162), (280, 165, True), (266, 167), (258, 169)],
                 [(264, 152), (284, 146), (310, 142), (322, 144)], [[(300, 150), (310, 158)], [(276, 154), (280, 163)]],
                 [[(287, 145), (296, 161), (283, 164)], [(316, 142), (324, 158), (312, 160)], [(268, 150), (272, 166), (262, 167)]], m)
    out += layer([(249, 178), (250, 168), (258, 162, True), (268, 160), (280, 157, True), (292, 155), (304, 153, True), (316, 153), (325, 157), (330, 166),
                  (328, 176), (322, 186, True), (318, 180), (314, 175, True), (304, 172), (292, 173, True), (278, 173), (264, 177, True), (256, 178)],
                 [(256, 166), (280, 159), (312, 156), (326, 160)], [[(270, 166), (284, 171)], [(318, 164), (324, 180)]],
                 [[(296, 155), (304, 172), (291, 173)], [(318, 155), (330, 170), (323, 185), (318, 178)], [(262, 162), (264, 177), (254, 178)],
                  [(280, 158), (284, 173), (276, 173)]], m)
    band = smooth(m([(251, 184), (264, 178), (284, 175), (304, 175), (314, 180, True), (311, 188, True), (290, 183), (268, 186), (253, 192, True)]))
    return out + C(band, "wrap", [line(m([(260, 182), (284, 178.6), (306, 179)]), O["wrap_sh"], 1.0), line(m([(262, 179), (288, 176.4)]), O["wrap_lt"], 1.2)],
                   s=3, sdir=(0.0, 1.0))


def f_mouth_open():
    return [path(smooth([(270.6, 230.2), (291.4, 229.4), (290, 239.6), (271, 239.6)]), O["skin"]),
            path(smooth([(272.4, 233.0), (280, 232.6), (289.2, 231.2), (286.4, 236.8), (280, 238.2), (274.4, 236.8)]), "#4a2424", INK, 1.3),
            path(smooth([(273.4, 233.2), (280, 232.8), (288.2, 231.6), (286.8, 233.6), (280, 234.2), (274.2, 234.2)]), "#efe8dc"),
            path(smooth([(275.0, 236.6), (280, 237.2), (285.4, 236.0), (283.6, 238.8), (280, 239.4), (276.4, 238.8)]), O["lip"])]


def f_neck():
    out = C(capsule((280, 234), (280, 256), 13, 13), "skin", [], s=4)
    # the banyan's shawl collar, rolled round the back of the neck
    out += C(smooth([(258, 252), (270, 244), (290, 244), (302, 252), (296, 256), (280, 251), (264, 256)]), "lining", [], s=2.5)
    stock = smooth([(267, 248), (293, 248), (294, 258), (266, 258)])
    out += C(stock, "shirt", [line([(268, 253), (292, 253)], O["shirt_sh"], 0.9)], s=2.5)
    tie = smooth([(276, 256), (284, 256), (287, 266), (283, 280), (280, 284), (277, 280), (273, 266)])
    return out + C(tie, "shirt", [line([(280, 260), (280, 280)], O["shirt_sh"], 1.0)], s=2.5)


def f_vest():
    out = C(smooth([(266, 250), (294, 250), (298, 270), (280, 284), (262, 270)]), "shirt", [], s=2)
    vest = smooth([(268, 256), (276, 270), (280, 276), (284, 270), (292, 256), (306, 268), (308, 300), (306, 334), (298, 348, True), (280, 342),
                   (262, 348, True), (254, 334), (252, 300), (254, 268)])
    items = [ellipse(281, y, 1.8, 1.8, O["button"], INK, 0.6) for y in (284, 296, 308, 320, 332)]
    items += [line([(280, 278), (280, 342)], O["vest_sh"], 1.1), line([(262, 300), (258, 336)], O["vest_sh"], 1.1)]
    return out + C(vest, "vest", items, s=5)


def f_apron():
    d = smooth([(256, 304), (304, 304), (306, 360), (307, 392), (308, 410, True), (252, 410, True), (253, 392), (254, 360)])
    items = [line([(280, 362), (280, 404)], O["apron_sh"], 1.1)]
    pouch = smooth([(266, 326, True), (294, 326, True), (294, 352, True), (266, 352, True)])
    items += [path(pouch, O["apron_sh"], INK, 1.0), path(smooth([(266, 326, True), (294, 326, True), (292, 335), (268, 335)]), O["apron_lt"], INK, 0.9),
              ellipse(280, 332, 2.0, 2.0, O["button"], INK, 0.6)]
    out = C(d, "apron", items, s=4)
    return out + cel(smooth([(250, 300), (310, 300), (310, 308), (250, 308)]), O["apron_sh"], "#2e2014", None, [], s=1)


def f_gown():
    """The open banyan: a panel down each side, the shawl collar of straw silk
    running round the neck and down both front edges to the hem."""
    d = smooth([(250, 252), (238, 264), (234, 290), (234, 330), (232, 380), (230, 438, True), (260, 440, True), (259, 380), (259, 320), (262, 284),
                (270, 258), (280, 254), (290, 258), (298, 284), (301, 320), (301, 380), (300, 440, True), (330, 438, True), (328, 380), (326, 330),
                (326, 290), (322, 264), (310, 252), (296, 245), (280, 243), (264, 245)])
    items = damask(228, 250, 334, 442) + [line([(244, 300), (240, 380), (238, 434)], O["gown_sh"], 1.3), line([(316, 300), (320, 380), (322, 434)], O["gown_sh"], 1.3),
             sheen([(250, 290), (248, 340)]), sheen([(312, 286), (314, 330)]), sheen([(252, 380), (251, 420)], 1.1)]
    out = C(d, "gown", items, s=6)
    for pts in ([(270, 248), (276, 254), (266, 282), (263, 320), (263, 440, True), (257.5, 440, True), (257.5, 320), (259, 282), (264, 254)],):
        out += C(smooth(pts), "lining", [], s=2)
        out += C(smooth(mx(pts)), "lining", [], s=2)
    hem = smooth([(230, 436), (262, 438), (262, 443, True), (230, 441, True)])
    out += C(hem, "lining", [], s=1.5) + C(smooth(mx([(230, 436), (262, 438), (262, 443, True), (230, 441, True)])), "lining", [], s=1.5)
    return out


def f_arm(side, piece):
    s, e, w = F_ARM_R if side == "right" else F_ARM_L
    inward = 1 if side == "right" else -1
    if piece == "upper":
        return sleeve(s, e)
    if piece == "lower":
        return forearm(e, w, r=(8.0, 7.0))
    return hand_front(w, ang(e, w), inward)


def f_leg(side, piece):
    h, k, a = F_LEG_R if side == "right" else F_LEG_L
    return leg_piece(h, k, a, 0, piece, front=True)


def front_layers():
    L = [("wrap-back", "Wrap - Ends", "wrap_back", "head", 4, "", f_wrap_back)]
    z = 10
    for side, label in (("left", "Left"), ("right", "Right")):
        L += [(f"{side}-thigh", f"Thigh - {label}", f"{side}_leg_u", f"{side}_leg_u", z, "", lambda s=side: f_leg(s, "thigh")),
              (f"{side}-shin", f"Shin - {label}", f"{side}_leg_l", f"{side}_leg_l", z + 1, "", lambda s=side: f_leg(s, "shin")),
              (f"{side}-foot", f"Foot - {label}", f"{side}_leg_foot", f"{side}_leg_foot", z + 2, "", lambda s=side: f_leg(s, "foot"))]
        z += 10
    L.insert(4, ("pelvis", "Pelvis", "pelvis_yoke", "pelvis", 19, "", lambda: pelvis_block([(256, 332), (304, 332), (306, 364), (254, 364)])))
    L += [("vest", "Shirt and Waistcoat", "vest", "torso", 30, "", f_vest),
          ("apron", "Apron", "apron", "torso", 34, "", f_apron),
          ("gown", "Banyan", "gown", "torso", 36, "", f_gown),
          ("neck", "Neck, Collar and Neckcloth", "neck", "torso", 50, "", f_neck),
          ("head", "Head", "head", "head", 60, "", f_head),
          ]
    L += face_layers(f_face_features, lambda: [F_EYE_R, F_EYE_L], (1.0, 1.0), f_mouth_open)
    z = 70
    for side, label in (("left", "Left"), ("right", "Right")):
        L += [(f"{side}-arm-lower", f"Arm - {label} - Lower", f"{side}_arm_l", f"{side}_arm_l", z, "", lambda s=side: f_arm(s, "lower")),
              (f"{side}-arm-upper", f"Arm - {label} - Upper", f"{side}_arm_u", f"{side}_arm_u", z + 1, "", lambda s=side: f_arm(s, "upper")),
              (f"{side}-hand", f"Arm - {label} - Hand", f"{side}_hand", f"{side}_arm_hand", z + 2, "", lambda s=side: f_arm(s, "hand"))]
        z += 5
    return L


# ============================================================================================
# THREE-QUARTER VIEW (turned toward screen-right; his right side near)
# ============================================================================================

def tq(pts, c=290.0, near=1.0, far_k=0.56):
    """Turn front-view torso points into the three-quarter view: the front's
    centre line moves to ``x = c``, his right half keeps its width (the side
    of the body comes into view there), his left half foreshortens."""
    out = []
    for p in pts:
        u = p[0] - F_CX
        out.append((c + (u * near if u < 0 else u * far_k), p[1]) + tuple(p[2:]))
    return out



def hq(pts):
    """Front-view head points turned into the three-quarter head."""
    return tq(pts, c=284.0, near=0.95, far_k=0.85)


Q_ARM_N = ((254, 264), (247, 312), (250, 356))  # his right
Q_ARM_F = ((310, 262), (318, 310), (321, 352))  # his left, mostly behind him
Q_LEG_N = ((276, 350), (274, 416), (270, 484))
Q_LEG_F = ((298, 348), (300, 414), (300, 482))
Q_EYE_N, Q_EYE_F = (280.0, 203.0), (304.0, 202.6)


def q_joints():
    J = {"body": ("", 288.0, 350.0), "torso": ("body", 288.0, 350.0), "head": ("torso", 288.0, 244.0)}
    for side, (s, e, w) in (("near", Q_ARM_N), ("far", Q_ARM_F)):
        J[f"{side}_arm_u"] = ("torso", *s)
        J[f"{side}_arm_l"] = (f"{side}_arm_u", *e)
        J[f"{side}_hand"] = (f"{side}_arm_l", *w)
    for side, (h, k, a) in (("near", Q_LEG_N), ("far", Q_LEG_F)):
        J[f"{side}_leg_u"] = ("body", *h)
        J[f"{side}_leg_l"] = (f"{side}_leg_u", *k)
        J[f"{side}_foot"] = (f"{side}_leg_l", *a)
    return J


def q_wrap_back():
    """The cap's long end hangs behind his left ear: facing right that ear is
    the far one and only the end's tip shows behind the neck; facing left it
    is the near one and the whole fall shows behind it."""
    if left():
        return C(smooth([(252, 186), (262, 188), (264, 206), (262, 228), (258, 252, True), (250, 250, True), (250, 228), (248, 204)]), "wrap",
                 [line([(256, 196), (257, 222), (254, 244)], O["wrap_sh"], 1.1), line([(260, 198), (260, 216)], O["wrap_lt"], 1.2)], s=3)
    return C(smooth([(306, 236), (314, 238), (316, 252), (311, 262, True), (306, 256, True), (307, 246)]), "wrap", [], s=2)


def q_head():
    """The head turned toward the screen's right, his right side near: the
    broad face foreshortened on the far side, the nose crossing in front of
    the far cheek with its round tip, the far cheek's curve the silhouette."""
    sk, dk = O["skin_sh"], O["skin_dk"]
    (nx, ny), (fx, fy) = Q_EYE_N, Q_EYE_F
    out = []
    out += C(smooth([(256, 180), (266, 178), (266, 196), (258, 202)]), "hair", [], s=2)
    out += C(smooth([(276, 244), (292, 252), (306, 244), (302, 256), (288, 259), (278, 253)]), "skin", [], s=2)
    face = smooth([(264, 178), (260, 192), (259, 206), (261, 220), (266, 232), (274, 242), (284, 248.4), (295, 250), (303, 247.6), (309, 240),
                   (313, 229), (314.6, 216), (314, 204), (311, 192), (308, 180), (296, 172), (280, 171)])
    items = [
        path(smooth([(259, 208), (262, 224), (272, 240), (284, 247), (272, 238), (264, 224)]), sk),
        ellipse(275.5, 223, 6, 3.8, O["blush"]), ellipse(309.8, 222, 3.0, 3.2, O["blush"]),
        line([(292.4, 189.6), (293, 196.4)], dk, 0.9), line([(280, 184.4), (292, 182.8)], sk, 1.0),
        # the near plane of the nose in shade, its ridge, the round tip and its
        # light, the wings and the nostrils
        path(smooth([(292, 203), (295.6, 204), (298.6, 215), (296, 220), (292, 215)]), sk),
        line([(296.4, 201.6), (299.4, 210.4), (302.4, 215.4)], O["skin_lt"], 1.4),
        ellipse(302.6, 219.6, 4.2, 3.6, O["skin"]), ellipse(303.8, 218.2, 1.9, 1.4, O["skin_lt"]),
        line([(298.2, 212.4), (301.4, 215.6)], sk, 0.9),
        line([(294.6, 218.4), (294.0, 222.2), (296.6, 224.0), (300, 224.8), (303.6, 225.0), (306.6, 223.0), (307.0, 219.4), (305.6, 216.4)], INK, 1.1),
        ellipse(299.2, 223.2, 1.4, 0.8, dk), ellipse(304.6, 223.2, 0.9, 0.7, dk),
    ]
    out += C(face, "skin", items, s=5)
    ear = smooth([(262, 197), (256.5, 196), (254, 206), (256, 217), (262, 219)])
    out += C(ear, "skin", [line([(258.6, 200), (256.8, 206.4), (258.8, 213)], dk, 1.0)], s=2)
    return out + q_wrap()


def hcap(pts):
    """Front-view cap points turned into the three-quarter view, centred over
    the turned head: lower like the front's, its far side foreshortened."""
    # facing left the cap is mirrored first, so its low, close side is the far one
    return tq(tight(pts), c=283.0, near=0.98, far_k=0.9 if left() else 0.72)


def q_wrap():
    return cap_front((lambda pts: hcap(mx(pts))) if left() else hcap)


def q_mouth_open():
    return [path(smooth([(286.4, 231.0), (306.4, 230.0), (304.4, 240.6), (288.4, 240.6)]), O["skin"]),
            path(smooth([(288.4, 234.0), (296, 233.6), (304.4, 232.0), (301.6, 237.8), (296, 239.2), (290.8, 237.8)]), "#4a2424", INK, 1.3),
            path(smooth([(289.4, 234.2), (296, 233.8), (303.4, 232.4), (302.0, 234.4), (296, 235.0), (290.2, 235.2)]), "#efe8dc"),
            path(smooth([(291.4, 237.6), (296, 238.2), (300.8, 237.0), (299.2, 239.8), (296, 240.4), (292.8, 239.8)]), O["lip"])]


def q_neck():
    out = C(capsule((287, 234), (288, 256), 12.5, 12.5), "skin", [], s=4)
    out += C(smooth(tq([(258, 252), (270, 244), (290, 244), (302, 252), (296, 256), (280, 251), (264, 256)])), "lining", [], s=2.5)
    out += C(smooth(tq([(267, 248), (293, 248), (294, 258), (266, 258)])), "shirt", [line(tq([(268, 253), (292, 253)]), O["shirt_sh"], 0.9)], s=2.5)
    tie = smooth(tq([(276, 256), (284, 256), (287, 266), (283, 280), (280, 284), (277, 280), (273, 266)]))
    return out + C(tie, "shirt", [line(tq([(280, 260), (280, 280)]), O["shirt_sh"], 1.0)], s=2.5)


def q_vest():
    out = C(smooth(tq([(266, 250), (294, 250), (298, 270), (280, 284), (262, 270)])), "shirt", [], s=2)
    vest = smooth(tq([(268, 256), (276, 270), (280, 276), (284, 270), (292, 256), (306, 268), (309, 300), (307, 334), (298, 348, True), (280, 342),
                      (262, 348, True), (252, 334), (249, 300), (252, 268)]))
    items = [ellipse(*tq([(282, y)])[0], 1.8, 1.8, O["button"], INK, 0.6) for y in (284, 296, 308, 320, 332)]
    items += [line(tq([(280, 278), (280, 342)]), O["vest_sh"], 1.1), line(tq([(262, 300), (258, 336)]), O["vest_sh"], 1.1)]
    return out + C(vest, "vest", items, s=5)


def q_apron():
    d = smooth(tq([(254, 304), (306, 304), (308, 360), (309, 392), (310, 410, True), (250, 410, True), (251, 392), (252, 360)]))
    items = [line(tq([(280, 362), (280, 404)]), O["apron_sh"], 1.1)]
    pouch = smooth(tq([(266, 326, True), (294, 326, True), (294, 352, True), (266, 352, True)]))
    items += [path(pouch, O["apron_sh"], INK, 1.0), path(smooth(tq([(266, 326, True), (294, 326, True), (292, 335), (268, 335)])), O["apron_lt"], INK, 0.9),
              ellipse(*tq([(280, 332)])[0], 2.0, 2.0, O["button"], INK, 0.6)]
    out = C(d, "apron", items, s=4)
    return out + cel(smooth(tq([(246, 300), (312, 300), (312, 308), (246, 308)])), O["apron_sh"], "#2e2014", None, [], s=1)


def q_gown():
    """The banyan turned: the near panel shows the side of the gown as well."""
    near = [(256, 250), (244, 256), (236, 270), (232, 300), (232, 340), (230, 390), (228, 440, True), (264, 442, True), (263, 380), (263, 320),
            (266, 284), (272, 258), (280, 254)]
    farp = [(280, 254), (290, 258), (298, 284), (301, 320), (301, 380), (300, 440, True), (332, 438, True), (330, 380), (328, 330), (328, 290),
            (324, 264), (310, 252), (296, 245), (280, 243), (264, 245)]
    d = smooth(tq(near + farp))
    items = damask(226, 250, 312, 444) + [line(tq([(246, 300), (241, 380), (238, 434)]), O["gown_sh"], 1.3), line(tq([(318, 300), (322, 380), (324, 434)]), O["gown_sh"], 1.2),
             sheen(tq([(250, 290), (248, 340)])), sheen(tq([(254, 380), (253, 420)]), 1.1), line(tq([(258, 268), (252, 300)]), O["gown_sh"], 1.0)]
    out = C(d, "gown", items, s=6)
    lap = [(270, 248), (276, 254), (266, 282), (263, 320), (263, 442, True), (257.5, 442, True), (257.5, 320), (259, 282), (264, 254)]
    out += C(smooth(tq(lap)), "lining", [], s=2)
    out += C(smooth(tq(mx(lap))), "lining", [], s=1.5)
    out += C(smooth(tq([(228, 437), (264, 439), (264, 444, True), (228, 442, True)])), "lining", [], s=1.5)
    out += C(smooth(tq(mx([(228, 437), (262, 439), (262, 444, True), (228, 442, True)]))), "lining", [], s=1.5)
    return out


def q_arm(side, piece):
    s, e, w = Q_ARM_N if side == "near" else Q_ARM_F
    near = side == "near"
    if piece == "upper":
        return sleeve(s, e, near=near, r=(12.5, 13.0) if near else (11.0, 11.5))
    if piece == "lower":
        return forearm(e, w, near=near)
    return hand_side(w, ang(e, w), near=near)


def q_leg(side, piece):
    h, k, a = Q_LEG_N if side == "near" else Q_LEG_F
    return leg_piece(h, k, a, 16, piece, side == "near")


def tq_layers():
    return [
        ("wrap-back", "Wrap - End", "wrap_back", "head", 4, "", q_wrap_back),
        ("far-arm-lower", "Far Arm - Lower", "far_arm_l", "far_arm_l", 6, "", lambda: q_arm("far", "lower")),
        ("far-arm-upper", "Far Arm - Upper", "far_arm_u", "far_arm_u", 7, "", lambda: q_arm("far", "upper")),
        ("far-hand", "Far Hand", "far_hand", "far_arm_hand", 8, "", lambda: q_arm("far", "hand")),
        ("far-thigh", "Far Thigh", "far_leg_u", "far_leg_u", 10, "", lambda: q_leg("far", "thigh")),
        ("far-shin", "Far Shin", "far_leg_l", "far_leg_l", 11, "", lambda: q_leg("far", "shin")),
        ("far-foot", "Far Foot", "far_leg_foot", "far_leg_foot", 12, "", lambda: q_leg("far", "foot")),
        ("pelvis", "Pelvis", "pelvis_yoke", "pelvis", 19, "", lambda: pelvis_block(tq([(256, 332), (304, 332), (306, 364), (254, 364)]))),
        ("near-thigh", "Near Thigh", "near_leg_u", "near_leg_u", 20, "", lambda: q_leg("near", "thigh")),
        ("near-shin", "Near Shin", "near_leg_l", "near_leg_l", 21, "", lambda: q_leg("near", "shin")),
        ("near-foot", "Near Foot", "near_leg_foot", "near_leg_foot", 22, "", lambda: q_leg("near", "foot")),
        ("vest", "Shirt and Waistcoat", "vest", "torso", 30, "", q_vest),
        ("apron", "Apron", "apron", "torso", 34, "", q_apron),
        ("gown", "Banyan", "gown", "torso", 36, "", q_gown),
        ("neck", "Neck, Collar and Neckcloth", "neck", "torso", 50, "", q_neck),
        ("head", "Head", "head", "head", 60, "", q_head),
        *face_layers(q_face_features, lambda: [Q_EYE_N, Q_EYE_F], (1.0, 0.72), q_mouth_open),
        ("near-arm-lower", "Near Arm - Lower", "near_arm_l", "near_arm_l", 77, "", lambda: q_arm("near", "lower")),
        ("near-arm-upper", "Near Arm - Upper", "near_arm_u", "near_arm_u", 78, "", lambda: q_arm("near", "upper")),
        ("near-hand", "Near Hand", "near_hand", "near_arm_hand", 82, "", lambda: q_arm("near", "hand")),
    ]


# ============================================================================================

# ============================================================================================
# THE FACE: expressions
# ============================================================================================
#
# The head layers draw everything that never moves (the skull, the cap, the
# ears, the nose, the cheeks).  The eyes, the brows, the mouth and the folds
# round it are drawn per EXPRESSION, each in its own layer behind an opacity
# channel (``face_<name>``), so a clip or a portrait picks one.  ``knowing`` is
# shown by default.  Two overlays sit on top of any of them: ``blink`` (skin
# over the eyes, the lids closed) and ``talk_mouth`` (an open, speaking mouth).
#
# His RIGHT eye fails in every expression: at rest it is screwed into a squint,
# it opens only to a heavy-lidded half when he is startled, and it closes with
# the other when he laughs or winces.

#: name -> the good eye, the failing eye, the gaze of the good eye (dx, dy), the
#: brows over the good and the failing eye as (inner, outer) lifts (negative is
#: up), the mouth, and the folds beside it.
EXPRESSIONS = {
    "knowing": dict(good="knowing", bad="squint", gaze=(1.8, -0.6), brow_good=(0.0, 0.0), brow_bad=(0.0, 0.0), mouth="knowing"),
    "pleased": dict(good="smiling", bad="squint", gaze=(1.0, -0.2), brow_good=(-0.8, -0.6), brow_bad=(-0.4, -0.2), mouth="smile"),
    "delighted": dict(good="happy", bad="happy", gaze=(0, 0), brow_good=(-1.6, -1.0), brow_bad=(-1.2, -0.8), mouth="laugh"),
    "surprised": dict(good="wide", bad="half", gaze=(0.4, 0.0), brow_good=(-3.2, -2.6), brow_bad=(-2.4, -2.0), mouth="o"),
    "thinking": dict(good="open", bad="squint", gaze=(-1.6, -1.6), brow_good=(-2.4, -1.6), brow_bad=(0.8, 0.2), mouth="pursed"),
    "stern": dict(good="knowing", bad="squint", gaze=(0.6, 0.2), brow_good=(2.0, -0.4), brow_bad=(2.0, 0.0), mouth="flat"),
    "worried": dict(good="open", bad="squint", gaze=(0.2, 0.6), brow_good=(-2.6, 0.8), brow_bad=(-2.0, 0.6), mouth="frown"),
    "hurt": dict(good="shut", bad="shut", gaze=(0, 0), brow_good=(2.4, 0.4), brow_bad=(2.4, 0.4), mouth="grit"),
}
EXPRESSION_ORDER = tuple(EXPRESSIONS)
WHITE, PUPIL, SLIT = "#f4efe6", "#141414", "#5e5248"


def eye_frontal(cx, cy, state, gaze=(0.0, 0.0), k=1.0, good=True):
    """One eye seen from the front, ``k`` its foreshortening (1 near, less far)."""
    X = lambda dx: cx + dx * k
    sk, dk = O["skin_sh"], O["skin_dk"]
    gx, gy = gaze[0] * k, gaze[1]
    if state in ("knowing", "smiling", "open", "wide"):
        top = {"knowing": -2.6, "smiling": -2.0, "open": -3.0, "wide": -3.8}[state]
        low = {"knowing": 2.8, "smiling": 1.8, "open": 3.0, "wide": 3.4}[state]
        out = [path(smooth([(X(-5.6), cy + 0.8), (X(-2.4), cy + top + 0.6), (X(1.6), cy + top), (X(5.6), cy - 0.8), (X(3.4), cy + low - 0.4),
                            (X(-1.6), cy + low)]), WHITE)]
        ir = 2.5 if state != "wide" else 2.3
        out += [ellipse(cx + gx, cy - 0.2 + gy, ir * k, ir + 0.1, O["iris"]), ellipse(cx + gx + 0.2 * k, cy - 0.2 + gy, 1.1 * k, 1.1, PUPIL),
                ellipse(cx + gx + 1.0 * k, cy - 1.0 + gy, 0.5, 0.5, "#ffffff")]
        if state != "wide":  # the lid sits over the top of the iris
            out.append(path(smooth([(X(-6.2), cy + 0.6), (X(-2.4), cy + top - 1.8), (X(1.6), cy + top - 2.4), (X(6.2), cy - 1.2),
                                    (X(1.6), cy + top + 0.6), (X(-2.4), cy + top + 1.2)]), O["skin"]))
        out += [line([(X(-5.8), cy + 0.8), (X(-2.4), cy + top + 0.4), (X(1.6), cy + top - 0.2), (X(6.0), cy - 0.8)], INK, 1.6),
                line([(X(-5.0), cy + top - 1.6), (X(0.6), cy + top - 3.2), (X(5.6), cy + top - 1.4)], sk, 1.0),
                line([(X(-3.6), cy + low), (X(1), cy + low + 0.4), (X(4.4), cy + low - 0.8)], INK, 0.7)]
        if state == "smiling":
            out += [line([(X(-4.0), cy + low + 2.0), (X(1), cy + low + 2.8), (X(4.6), cy + low + 1.4)], sk, 1.0)]
        return out
    if state == "squint":
        return [path(smooth([(X(-4.2), cy + 0.9), (cx, cy + 0.3), (X(4.2), cy + 0.8), (cx, cy + 1.5)]), SLIT),
                line([(X(-5.6), cy + 1.0), (X(-2.4), cy - 0.6), (X(2.0), cy - 0.8), (X(5.6), cy + 0.6)], INK, 1.7),
                line([(X(-4.4), cy + 1.8), (cx, cy + 2.8), (X(4.4), cy + 1.6)], INK, 0.9),
                line([(X(-5.0), cy - 2.8), (cx, cy - 4.2), (X(5.0), cy - 2.8)], sk, 1.0),
                line([(X(-4.4), cy + 4.4), (cx, cy + 5.4), (X(4.2), cy + 4.4)], sk, 1.0),
                line([(X(-6.2), cy + 0.6), (X(-9.0), cy - 1.0)], dk, 0.8), line([(X(-6.0), cy + 2.2), (X(-8.8), cy + 3.4)], dk, 0.8)]
    if state == "half":  # the failing eye startled open: a heavy lid half over a clouded iris
        return [path(smooth([(X(-5.4), cy + 0.8), (X(-1), cy - 1.2), (X(5.0), cy + 0.2), (X(1.4), cy + 2.8), (X(-3), cy + 2.6)]), WHITE),
                ellipse(cx + 0.6 * k, cy + 0.8, 2.2 * k, 1.8, O["cloud"]), ellipse(cx + 0.6 * k, cy + 0.8, 0.9 * k, 0.9, "#3a3632"),
                path(smooth([(X(-6.2), cy + 0.2), (X(-1.0), cy - 3.6), (X(6.0), cy - 1.0), (X(5.4), cy + 0.6), (X(-1.0), cy + 0.0), (X(-5.8), cy + 1.0)]),
                     sk, INK, 0.8),
                line([(X(-5.8), cy + 0.8), (X(-1.0), cy + 0.0), (X(5.4), cy + 0.6)], INK, 1.7),
                line([(X(-3.4), cy + 2.8), (X(2.4), cy + 2.8)], INK, 0.8)]
    if state == "happy":  # shut in a laugh: the lids an arch, the cheek pushed up under it
        return [line([(X(-5.6), cy + 1.4), (X(-2.0), cy - 1.2), (X(2.0), cy - 1.4), (X(5.6), cy + 1.0)], INK, 1.7),
                line([(X(-4.2), cy + 3.6), (cx, cy + 4.6), (X(4.2), cy + 3.4)], sk, 1.0),
                line([(X(-6.4), cy + 1.0) if not good else (X(6.4), cy + 0.6), (X(-9.0), cy + 0.0) if not good else (X(9.0), cy - 0.4)], dk, 0.8)]
    if state == "shut":  # screwed shut: a hard line, creases fanning from both corners
        return [line([(X(-5.6), cy + 0.4), (X(-1.6), cy + 1.6), (X(2.0), cy + 1.4), (X(5.6), cy + 0.2)], INK, 1.8),
                line([(X(-4.4), cy - 2.0), (cx, cy - 1.0), (X(4.4), cy - 2.2)], dk, 0.9),
                line([(X(-4.0), cy + 3.4), (cx, cy + 4.2), (X(4.0), cy + 3.2)], dk, 0.9),
                line([(X(-6.4), cy + 0.6), (X(-9.0), cy - 0.8)], dk, 0.8), line([(X(6.4), cy + 0.4), (X(9.0), cy - 1.0)], dk, 0.8)]
    raise KeyError(state)


def brow_line(pts, inner_end, lift):
    """A thin light brow through ``pts`` (left to right), its inner end (the one
    nearer the nose: index 0 or -1) and outer end lifted by ``lift``."""
    inner, outer = lift
    a, m, b = pts
    if inner_end == 0:
        a, b = (a[0], a[1] + inner), (b[0], b[1] + outer)
    else:
        a, b = (a[0], a[1] + outer), (b[0], b[1] + inner)
    m = (m[0], m[1] + (inner + outer) / 2 - (0.6 if inner < -1.5 and outer > 0 else 0.0))
    out = [line([a, m, b], O["brow"], 2.2)]
    if inner > 1.0:  # knit: the crease the brows push up between them
        x = a[0] if inner_end == 0 else b[0]
        y = a[1] if inner_end == 0 else b[1]
        out.append(line([(x + (-1.6 if inner_end == 0 else 1.6), y - 2.0), (x + (-1.0 if inner_end == 0 else 1.0), y + 2.4)], O["skin_dk"], 0.9))
    return out


def mouth_frontal(cx, cy, hw_l, hw_r, lift, kind):
    """The mouth seen from the front or turned, ``hw_l``/``hw_r`` its half
    widths to the screen's left and right, ``lift`` the screen side (+1 right,
    -1 left) of his LEFT corner, the one his smile pulls up."""
    sk, dk = O["skin_sh"], O["skin_dk"]
    L, R = cx - hw_l, cx + hw_r
    lift_l = 1.0 if lift < 0 else 0.0
    lift_r = 1.0 if lift > 0 else 0.0
    if kind == "knowing":
        yl, yr = cy - 1.8 * lift_l, cy - 1.8 * lift_r
        up = [(L + 0.4, cy - 0.2 - 1.2 * lift_l), (cx - hw_l * 0.45, cy - 1.6), (cx, cy - 1.0), (cx + hw_r * 0.45, cy - 1.8), (R - 0.4, cy - 2.0 * lift_r - 0.2),
              (cx + hw_r * 0.6, cy - 0.2), (cx, cy + 0.2), (cx - hw_l * 0.6, cy)]
        lo = [(L + hw_l * 0.25, cy + 1.2), (cx, cy + 1.6), (R - hw_r * 0.25, cy + 0.8), (cx + hw_r * 0.5, cy + 4.2), (cx, cy + 4.8), (cx - hw_l * 0.5, cy + 3.8)]
        out = [path(smooth(up), O["lip"]), path(smooth(lo), O["lip"]),
               line([(L, yl), (cx - hw_l * 0.5, cy + 0.6), (cx, cy + 0.8), (cx + hw_r * 0.5, cy + 0.2), (R, yr)], INK, 1.5),
               line([(cx - 3.4, cy + 7.0), (cx + 3.4, cy + 6.8)], dk, 0.9)]
        cx_c = R if lift > 0 else L
        out.append(line([(cx_c + 0.6 * lift, cy - 2.6), (cx_c + 1.6 * lift, cy + 0.2)], dk, 0.9))
        return out
    if kind == "smile":
        y_end = cy - 2.4
        out = [path(smooth([(L + 1, y_end + 0.6), (cx, cy - 0.6), (R - 1, y_end + 0.2 - lift_r * 0.8), (cx + hw_r * 0.4, cy + 0.4), (cx - hw_l * 0.4, cy + 0.4)]), O["lip"]),
               path(smooth([(L + 2, cy + 0.6), (cx, cy + 1.6), (R - 2, cy + 0.4), (cx + hw_r * 0.4, cy + 4.6), (cx, cy + 5.2), (cx - hw_l * 0.4, cy + 4.4)]), O["lip"]),
               line([(L - 0.6, y_end - lift_l * 0.8), (cx - hw_l * 0.5, cy + 0.8), (cx, cy + 1.2), (cx + hw_r * 0.5, cy + 0.8), (R + 0.6, y_end - lift_r * 0.8)], INK, 1.6),
               line([(L - 1.2, y_end - 2.2), (L - 0.2, y_end + 1.2)], dk, 0.9), line([(R + 1.2, y_end - 2.2), (R + 0.2, y_end + 1.2)], dk, 0.9),
               line([(cx - 3.4, cy + 7.4), (cx + 3.4, cy + 7.2)], dk, 0.9)]
        return out
    if kind == "laugh":
        top = [(L - 0.6, cy - 2.4), (cx - hw_l * 0.5, cy - 1.0), (cx, cy - 0.8), (cx + hw_r * 0.5, cy - 1.0), (R + 0.6, cy - 2.8)]
        bot = [(cx + hw_r * 0.6, cy + 5.6), (cx, cy + 7.4), (cx - hw_l * 0.6, cy + 5.6)]
        return [path(smooth([(L - 2.4, cy - 4.0), (R + 2.4, cy - 4.4), (R + 1.6, cy + 6.0), (cx, cy + 10.4), (L - 1.6, cy + 6.0)]), O["skin"]),
                path(smooth([top[0] + (True,)] + top[1:4] + [top[4] + (True,)] + bot), "#4a2424", INK, 1.3),
                path(smooth([(L + 0.6, cy - 2.0), (cx, cy - 0.4), (R - 0.6, cy - 2.4), (cx + hw_r * 0.4, cy + 0.8), (cx - hw_l * 0.4, cy + 0.8)]), "#efe8dc"),
                path(smooth([(cx - hw_l * 0.45, cy + 4.6), (cx, cy + 3.4), (cx + hw_r * 0.45, cy + 4.6), (cx, cy + 7.0)]), "#b4545a"),
                path(smooth([(cx - hw_l * 0.55, cy + 6.2), (cx, cy + 7.6), (cx + hw_r * 0.55, cy + 6.2), (cx, cy + 9.4)]), O["lip"]),
                line([(L - 2.0, cy - 5.2), (L - 0.8, cy - 1.6)], dk, 0.9), line([(R + 2.0, cy - 5.4), (R + 0.8, cy - 1.8)], dk, 0.9)]
    if kind == "o":
        ox = cx + (hw_r - hw_l) * 0.25
        return [path(smooth([(L - 1, cy - 2.4), (R + 1, cy - 2.4), (R + 1, cy + 7.0), (L - 1, cy + 7.0)]), O["skin"]),
                ellipse(ox, cy + 2.2, 3.6 * (hw_l + hw_r) / 18, 4.4, O["lip"]),
                ellipse(ox, cy + 2.2, 2.4 * (hw_l + hw_r) / 18, 3.0, "#4a2424", INK, 1.1),
                line([(ox - 2.6, cy + 9.2), (ox + 2.6, cy + 9.0)], dk, 0.9)]
    if kind == "pursed":  # pushed together and drawn aside, toward his left
        px = cx + lift * 2.4
        return [path(smooth([(px - 5.0, cy + 0.2), (px - 1.0, cy - 1.6), (px + 3.0, cy - 1.4), (px + 5.2, cy + 0.4), (px + 2.4, cy + 3.8), (px - 2.8, cy + 3.6)]), O["lip"]),
                line([(px - 5.4, cy + 0.8), (px - 1.0, cy + 0.6), (px + 2.0, cy + 1.0), (px + 5.4, cy + 0.2)], INK, 1.4),
                line([(px - 1.2, cy + 0.2), (px - 0.8, cy + 1.6)], dk, 0.8), line([(px + 2.4, cy + 0.4), (px + 2.8, cy + 1.8)], dk, 0.8),
                line([(cx - 3.0, cy + 7.0), (cx + 3.0, cy + 6.8)], dk, 0.9)]
    if kind == "flat":
        return [path(smooth([(L + 1, cy), (cx, cy - 1.2), (R - 1, cy), (cx, cy + 0.6)]), O["lip"]),
                path(smooth([(L + 2.4, cy + 1.2), (cx, cy + 1.4), (R - 2.4, cy + 1.2), (cx, cy + 3.8)]), O["lip"]),
                line([(L - 0.4, cy + 1.6), (cx - hw_l * 0.4, cy + 0.8), (cx, cy + 0.8), (cx + hw_r * 0.4, cy + 0.8), (R + 0.4, cy + 1.6)], INK, 1.6),
                line([(L - 0.8, cy + 2.4), (L - 1.6, cy + 5.0)], dk, 0.9), line([(R + 0.8, cy + 2.4), (R + 1.6, cy + 5.0)], dk, 0.9),
                line([(cx - 3.0, cy + 6.6), (cx + 3.0, cy + 6.4)], dk, 0.9)]
    if kind == "frown":
        return [path(smooth([(L + 1, cy + 1.6), (cx, cy - 1.0), (R - 1, cy + 1.6), (cx, cy + 0.4)]), O["lip"]),
                path(smooth([(L + 2.4, cy + 2.4), (cx, cy + 1.6), (R - 2.4, cy + 2.4), (cx, cy + 4.6)]), O["lip"]),
                line([(L - 0.4, cy + 3.0), (cx - hw_l * 0.5, cy + 0.8), (cx, cy + 0.4), (cx + hw_r * 0.5, cy + 0.8), (R + 0.4, cy + 3.0)], INK, 1.5),
                line([(L - 1.0, cy + 3.8), (L - 1.8, cy + 6.8)], dk, 0.9), line([(R + 1.0, cy + 3.8), (R + 1.8, cy + 6.8)], dk, 0.9),
                line([(cx - 3.0, cy + 7.2), (cx + 3.0, cy + 7.0)], dk, 0.9)]
    if kind == "grit":  # lips pulled back from clenched teeth
        return [path(smooth([(L - 2.0, cy - 3.0), (R + 2.0, cy - 3.0), (R + 2.0, cy + 7.0), (L - 2.0, cy + 7.0)]), O["skin"]),
                path(smooth([(L - 0.4, cy - 0.6, True), (R + 0.4, cy - 0.8, True), (R - 0.6, cy + 4.0, True), (L + 0.6, cy + 4.0, True)]), "#efe8dc", INK, 1.4),
                line([(L + 0.4, cy + 1.6), (R - 0.4, cy + 1.4)], O["skin_sh"], 0.9),
                *[line([(cx + d * (hw_l if d < 0 else hw_r), cy - 0.4), (cx + d * (hw_l if d < 0 else hw_r), cy + 3.6)], O["skin_sh"], 0.7) for d in (-0.6, -0.2, 0.2, 0.6)],
                line([(L - 1.4, cy - 2.6), (L - 2.4, cy + 2.6)], dk, 0.9), line([(R + 1.4, cy - 2.6), (R + 2.4, cy + 2.6)], dk, 0.9),
                line([(cx - 3.0, cy + 7.6), (cx + 3.0, cy + 7.4)], dk, 0.9)]
    raise KeyError(kind)


def folds_frontal(near_fold, far_fold, lift_side_is_far, kind):
    """The folds from the nose to the mouth: deep on the side the smile lifts,
    deep on both in a smile or a laugh, faint in a frown."""
    sk, dk = O["skin_sh"], O["skin_dk"]
    deep_both = kind in ("smile", "laugh", "grit")
    faint = kind in ("frown", "o")
    out = []
    for pts, lifted in ((near_fold, not lift_side_is_far), (far_fold, lift_side_is_far)):
        if faint:
            out.append(line(pts[:2], sk, 1.0))
        elif deep_both or lifted:
            out.append(line(pts, dk, 1.0))
        else:
            out.append(line(pts[:2], sk, 1.1))
    return out


def f_face_features(expr):
    """The front face's features in one expression."""
    e = EXPRESSIONS[expr]
    (rx, ry), (lx, ly) = F_EYE_R, F_EYE_L
    out = folds_frontal([(271.8, 224.0), (269.8, 230.4), (269.4, 235.0)], [(288.2, 223.4), (291.2, 228.6), (292.0, 234.6)], True, e["mouth"])
    out += eye_frontal(lx, ly, e["good"], e["gaze"], good=True)
    out += eye_frontal(rx, ry, e["bad"], good=False)
    out += brow_line([(260.6, 196.0), (266, 194.6), (273.4, 196.2)], -1, e["brow_bad"])
    out += brow_line([(286.6, 194.4), (292.6, 192.2), (299.4, 193.4)], 0, e["brow_good"])
    if e["good"] in ("knowing", "open"):
        out.append(line([(lx - 4.4, ly + 5.0), (lx + 4.4, ly + 4.8)], O["skin_sh"], 0.9))
    out += mouth_frontal(280.6, 233.4, 9.0, 9.0, +1, e["mouth"])
    return out


def q_face_features(expr):
    """The turned face's features: the near eye bigger, the far one
    foreshortened beside the nose; the mouth's far half shorter."""
    e = EXPRESSIONS[expr]
    (nx, ny), (fx, fy) = Q_EYE_N, Q_EYE_F
    lift = -1 if left() else +1
    out = folds_frontal([(291.4, 224.4), (288.8, 230.6), (288.0, 235.0)], [(307.2, 223.6), (309.0, 228.4), (308.6, 234.4)], not left(), e["mouth"])
    if left():  # his left side near: the good eye near, the failing one far
        out += eye_frontal(nx, ny, e["good"], e["gaze"], good=True)
        out += eye_frontal(fx, fy, e["bad"], k=0.72, good=False)
        out += brow_line([(272.2, 196.2), (278.6, 194.6), (286.6, 196.0)], -1, e["brow_good"])
        out += brow_line([(299.0, 194.6), (304.6, 192.6), (310.2, 193.8)], 0, e["brow_bad"])
        if e["good"] in ("knowing", "open"):
            out.append(line([(nx - 4.4, ny + 5.0), (nx + 4.4, ny + 4.8)], O["skin_sh"], 0.9))
    else:
        out += eye_frontal(fx, fy, e["good"], e["gaze"], k=0.72, good=True)
        out += eye_frontal(nx, ny, e["bad"], good=False)
        out += brow_line([(272.2, 196.2), (278.6, 194.6), (286.6, 196.0)], -1, e["brow_bad"])
        out += brow_line([(299.0, 194.6), (304.6, 192.6), (310.2, 193.8)], 0, e["brow_good"])
        if e["good"] in ("knowing", "open"):
            out.append(line([(fx - 3.2, fy + 4.6), (fx + 3.4, fy + 4.4)], O["skin_sh"], 0.9))
    out += mouth_frontal(296.0, 233.6, 8.6, 8.0, lift, e["mouth"])
    return out


def eye_profile(ex, ey, state, gaze=(0.0, 0.0)):
    """The one eye a profile shows, facing right."""
    sk, dk = O["skin_sh"], O["skin_dk"]
    if state in ("knowing", "smiling", "open", "wide"):
        top = {"knowing": -2.2, "smiling": -1.6, "open": -2.6, "wide": -3.4}[state]
        out = [path(smooth([(ex - 4.2, ey + 0.6), (ex + 0.4, ey + top), (ex + 4.4, ey - 1.0), (ex + 3.8, ey + 1.8), (ex - 0.6, ey + 2.4)]), WHITE),
               ellipse(ex + 2.6 + max(gaze[0], -1) * 0.4, ey - 0.4 + gaze[1] * 0.6, 1.4, 2.3, O["iris"]),
               ellipse(ex + 3.0 + max(gaze[0], -1) * 0.4, ey - 0.4 + gaze[1] * 0.6, 0.7, 1.1, PUPIL)]
        if state != "wide":
            out.append(path(smooth([(ex - 4.8, ey + 0.4), (ex + 0.4, ey + top - 2.0), (ex + 5.0, ey - 1.6), (ex + 0.4, ey + top + 0.6)]), O["skin"]))
        out += [line([(ex - 4.6, ey + 0.6), (ex + 0.4, ey + top - 0.2), (ex + 4.8, ey - 1.0)], INK, 1.6),
                line([(ex - 3.6, ey + top - 1.8), (ex + 0.8, ey + top - 3.2), (ex + 4.4, ey + top - 1.6)], sk, 1.0),
                line([(ex - 2.4, ey + 2.6), (ex + 3.4, ey + 2.0)], INK, 0.7)]
        if state == "smiling":
            out.append(line([(ex - 2.4, ey + 4.6), (ex + 3.4, ey + 4.0)], sk, 1.0))
        return out
    if state == "squint":
        return [path(smooth([(ex - 3.8, ey + 0.9), (ex, ey + 0.2), (ex + 3.6, ey + 0.6), (ex, ey + 1.5)]), SLIT),
                line([(ex - 5.4, ey + 1.0), (ex - 1.0, ey - 1.0), (ex + 4.8, ey + 0.2)], INK, 1.9),
                line([(ex - 3.8, ey + 1.8), (ex + 0.4, ey + 2.6), (ex + 3.6, ey + 1.4)], INK, 0.9),
                line([(ex - 4.6, ey - 3.0), (ex + 0.4, ey - 4.4), (ex + 4.6, ey - 2.8)], sk, 1.0),
                line([(ex - 5.4, ey + 1.0), (ex - 8.4, ey - 0.6)], dk, 0.8), line([(ex - 5.2, ey + 2.4), (ex - 8.2, ey + 3.6)], dk, 0.8)]
    if state == "half":
        return [path(smooth([(ex - 4.2, ey + 0.8), (ex + 0.4, ey - 1.4), (ex + 4.4, ey - 0.4), (ex + 3.8, ey + 1.8), (ex - 0.6, ey + 2.4)]), WHITE),
                ellipse(ex + 2.4, ey + 0.4, 1.3, 1.6, O["cloud"]),
                path(smooth([(ex - 4.8, ey + 0.6), (ex + 0.4, ey - 3.4), (ex + 5.0, ey - 1.6), (ex + 4.6, ey + 0.2), (ex + 0.4, ey - 0.4)]), sk, INK, 0.8),
                line([(ex - 4.6, ey + 0.8), (ex + 0.4, ey - 0.4), (ex + 4.8, ey + 0.2)], INK, 1.7),
                line([(ex - 2.4, ey + 2.6), (ex + 3.4, ey + 2.0)], INK, 0.7)]
    if state == "happy":
        return [line([(ex - 4.8, ey + 1.0), (ex + 0.4, ey - 1.4), (ex + 4.6, ey + 0.4)], INK, 1.7),
                line([(ex - 3.4, ey + 3.4), (ex + 3.4, ey + 3.0)], sk, 1.0),
                line([(ex - 5.4, ey + 0.8), (ex - 8.2, ey - 0.2)], dk, 0.8)]
    if state == "shut":
        return [line([(ex - 4.8, ey + 0.4), (ex, ey + 1.6), (ex + 4.6, ey + 0.2)], INK, 1.8),
                line([(ex - 3.6, ey - 2.0), (ex + 3.6, ey - 2.2)], dk, 0.9), line([(ex - 3.4, ey + 3.4), (ex + 3.4, ey + 3.0)], dk, 0.9),
                line([(ex - 5.4, ey + 0.6), (ex - 8.2, ey - 0.8)], dk, 0.8)]
    raise KeyError(state)


def mouth_profile(kind, lifted):
    """The mouth in profile (facing right): its corner set back in the cheek,
    lifted when it is his left corner and he smiles knowingly."""
    sk, dk = O["skin_sh"], O["skin_dk"]
    lips = [path(smooth([(297.8, 230.4), (301.0, 229.8), (302.2, 230.8), (300.6, 232.2), (297.6, 232.0)]), O["lip"]),
            path(smooth([(297.6, 233.8), (301.2, 233.6), (301.8, 235.4), (300.0, 236.8), (297.8, 236.2)]), O["lip"])]
    groove = line([(297.6, 239.0), (300.4, 238.8)], dk, 0.9)
    fold = line([(297.6, 222.6), (295.4, 227.4), (295.6, 231.4), (296.8, 234)], dk, 1.0)
    faint_fold = line([(297.6, 222.6), (295.6, 227.4)], sk, 1.0)
    if kind == "knowing":
        c = (295.8, 229.6) if lifted else (296.2, 231.0)
        return lips + [fold if lifted else faint_fold, line([c, (297.8, 232.6), (299.8, 233.0), (300.8, 232.8)], INK, 1.5),
                       line([(294.8, 228.0), (295.8, 229.8)] if lifted else [(295.2, 230.0), (296.2, 231.2)], dk, 0.9), groove]
    if kind == "smile":
        return lips + [fold, line([(294.8, 228.6), (296.6, 231.8), (299.8, 233.0), (300.8, 232.8)], INK, 1.6),
                       line([(293.6, 226.4), (294.8, 229.0)], dk, 0.9), groove]
    if kind == "laugh":
        return [path(smooth([(293.6, 227.0), (303.4, 228.0), (303.6, 241.0), (295.0, 240.6)]), O["skin"]), fold,
                path(smooth([(295.0, 229.2, True), (301.8, 229.6), (302.2, 238.0), (297.0, 238.4)]), "#4a2424", INK, 1.3),
                path(smooth([(296.0, 229.6), (301.4, 229.8), (301.0, 231.4), (296.4, 231.2)]), "#efe8dc"),
                path(smooth([(297.4, 237.0), (302.2, 237.0), (301.8, 239.4), (297.6, 239.6)]), O["lip"]),
                line([(293.4, 226.0), (294.6, 228.8)], dk, 0.9)]
    if kind == "o":
        return [path(smooth([(295.0, 228.0), (303.4, 228.6), (303.4, 239.0), (296.0, 239.0)]), O["skin"]), faint_fold,
                path(smooth([(298.4, 229.8), (302.6, 230.2), (302.8, 237.4), (298.8, 237.2)]), O["lip"]),
                ellipse(301.0, 233.6, 1.4, 2.6, "#4a2424", INK, 1.0), groove]
    if kind == "pursed":  # pressed together and drawn in: a short line, the corner tucked
        return lips + [faint_fold, line([(298.2, 232.6), (299.8, 233.0), (300.8, 232.8)], INK, 1.4),
                       line([(297.4, 231.4), (297.8, 233.6)], dk, 0.9), line([(298.4, 239.4), (300.2, 239.0)], dk, 1.0)]
    if kind == "flat":
        return lips + [faint_fold, line([(296.0, 232.6), (298.0, 232.8), (300.8, 232.8)], INK, 1.6), line([(295.6, 233.4), (295.0, 236.4)], dk, 0.9), groove]
    if kind == "frown":
        return lips + [faint_fold, line([(296.0, 234.4), (298.0, 233.2), (300.8, 232.8)], INK, 1.5), line([(295.6, 235.0), (294.8, 238.4)], dk, 0.9), groove]
    if kind == "grit":
        return [path(smooth([(294.0, 227.6), (303.4, 228.4), (303.4, 240.4), (295.0, 240.2)]), O["skin"]), fold,
                path(smooth([(296.6, 230.4, True), (302.0, 230.6, True), (301.8, 235.2, True), (296.8, 235.0, True)]), "#efe8dc", INK, 1.3),
                line([(297.0, 232.8), (301.8, 232.8)], sk, 0.8), line([(299.4, 230.8), (299.4, 234.8)], sk, 0.7),
                line([(294.4, 228.6), (295.4, 233.4)], dk, 0.9), groove]
    raise KeyError(kind)


def s_face_features(expr):
    """The profile's features: facing right he shows his right eye (the failing
    one) and the level corner of his mouth; facing left, his good eye and the
    corner his smile lifts."""
    e = EXPRESSIONS[expr]
    ex, ey = S_EYE
    state = e["good"] if left() else e["bad"]
    brow = e["brow_good"] if left() else e["brow_bad"]
    base_brow = [(ex - 8, ey - 8.2), (ex - 1, ey - 10.0), (ex + 6.2, ey - 8.4)] if left() else [(ex - 8, ey - 6.6), (ex - 1, ey - 7.8), (ex + 6.2, ey - 6.2)]
    out = eye_profile(ex, ey, state, e["gaze"])
    out += brow_line(base_brow, -1, brow)
    out += mouth_profile(e["mouth"], lifted=left())
    return out


def blink_patch(eyes, k_of):
    """Skin over the open eyes, then the lids closed: the blink overlay."""
    out = []
    for (cx, cy), k in zip(eyes, k_of):
        out.append(ellipse(cx, cy + 0.6, 7.0 * k, 3.8, O["skin"]))
        out.append(line([(cx - 5.4 * k, cy + 0.4), (cx, cy + 2.0), (cx + 5.4 * k, cy + 0.4)], INK, 1.6))
    return out


def face_layers(features, eyes, ks, talk):
    """The expression layers, then the blink and the talking mouth over them."""
    L = []
    for i, name in enumerate(EXPRESSION_ORDER):
        L.append((f"face-{name}", f"Face - {name.title()}", f"face_{name}", "head", 61 + i * 0.01, f"face_{name}_vis", lambda n=name: features(n)))
    L.append(("blink", "Blink", "blink", "head", 61.5, "blink_vis", lambda: blink_patch(eyes(), ks)))
    L.append(("talk-mouth", "Talk Mouth", "talk_mouth", "head", 61.6, "talk_vis", talk))
    return L


VIEWS: Dict[str, Tuple[str, Callable[[], List], Callable[[], Dict]]] = {
    "side": ("Oiler - Side Right", side_layers, s_joints),
    "tq": ("Oiler - Three Quarter", tq_layers, q_joints),
    "front": ("Oiler - Front", front_layers, f_joints),
    "tq_left": ("Oiler - Three Quarter Left", tq_layers, q_joints),
    "side_left": ("Oiler - Side Left", side_layers, s_joints),
}
#: The side view's torso pieces, drawn narrower front to back than first sketched.
SIDE_TORSO = {"vest", "gown", "near-skirt", "far-skirt", "apron", "neck"}
SIDE_SQUEEZE = (270.0, 0.84)
SHOWN = {"face_knowing_vis"}


def svg_text(look: str, view: str) -> str:
    use(look)
    _N[0] = 0
    svg.configure(dx=0, dy=0, ink=INK, ow=OW, colors={})
    label, layers, joints = VIEWS[view]
    side = view.startswith("side")
    O["facing"] = "left" if view.endswith("_left") else "right"
    _MAP["mirror"] = left()
    for group, plabel, name, bone, z, channel, painter in layers():
        extra = (f' data-rig-opacity="{channel}"' + (' data-rig-default="1"' if channel in SHOWN else "")) if channel else ""
        _MAP["dx"] = S_HEAD_DX / 2 if (side and group == "neck") else 0.0
        _MAP["sq"] = SIDE_SQUEEZE if (side and group in SIDE_TORSO) else None
        body = painter()
        _MAP["sq"] = None
        _MAP["dx"] = 0.0
        svg.transform(None)
        part(group, plabel, name, bone, z, body, extra)
    return svg.document(
        size=(W, H), design=f"oiler-banyan-{look}", layer_id="oiler", label=label,
        comment=[f"  <!-- CANDIDATE, NOT CAST: Oiler, {O['label']}, {label} (2026-10-20); the ground at y={GROUND_Y:g}.",
                 "       Drawn by scripts/svg_art/oiler_art.py. -->"],
        joints=_joints_then_reset(joints),
    )


def _joints_then_reset(joints):
    out = svg.joints_layer({k: (v[1], v[2]) for k, v in joints().items()})
    _MAP["mirror"] = False
    return out


# ============================================================================================
# THE MULTIVIEW SOURCE: every view in one rig-ready SVG
# ============================================================================================

#: (view key, layer label, rig side map) in the order the multiview lays them out.
#: The two LEFT views are stored as drawn: his left side turned to face right.
#: The target mirrors their frames into the sheet's ``~mirrored`` rows, so a
#: left-facing Oiler keeps his failing eye on his right.
MULTIVIEW = (
    ("tq", "Oiler - Three Quarter", None),
    ("front", "Oiler - Front", "left=far,right=near"),
    ("side", "Oiler - Side Right", None),
    ("tq_left", "Oiler - Three Quarter Left", None),
    ("side_left", "Oiler - Side Left", None),
)
DESIGN_ID = "euler-banyan-v2"


def _tip(a, b, length):
    d = math.hypot(b[0] - a[0], b[1] - a[1])
    return (b[0] + (b[0] - a[0]) / d * length, b[1] + (b[1] - a[1]) / d * length)


def rig_joints(view: str) -> Dict[str, Tuple[float, float]]:
    """The rig's joints for one view, by the names the humanoid builder reads."""
    J: Dict[str, Tuple[float, float]] = {}
    if view == "front":
        J["waist"], J["neck"] = (280.0, 300.0), (280.0, 248.0)
        for side, (sh, el, wr), (hp, kn, an) in (("right", F_ARM_R, F_LEG_R), ("left", F_ARM_L, F_LEG_L)):
            J.update({f"{side}_shoulder": sh, f"{side}_elbow": el, f"{side}_wrist": wr, f"{side}_handtip": _tip(el, wr, 30.0),
                      f"{side}_hip": hp, f"{side}_knee": kn, f"{side}_ankle": an, f"{side}_toe": (an[0], an[1] + 12.0)})
        return J
    if view.startswith("side"):
        J["waist"], J["neck"] = (270.0, 300.0), (279.0, 244.0)
        arms, legs, toe = {"near": S_NEAR_ARM, "far": S_FAR_ARM}, S_LEGS, 24.0
    else:
        J["waist"], J["neck"] = (288.0, 300.0), (288.0, 246.0)
        arms, legs, toe = {"near": Q_ARM_N, "far": Q_ARM_F}, {"near": Q_LEG_N, "far": Q_LEG_F}, 14.0
    for side in ("near", "far"):
        sh, el, wr = arms[side]
        hp, kn, an = legs[side]
        J.update({f"{side}_shoulder": sh, f"{side}_elbow": el, f"{side}_wrist": wr, f"{side}_handtip": _tip(el, wr, 30.0),
                  f"{side}_hip": hp, f"{side}_knee": kn, f"{side}_ankle": an, f"{side}_toe": (an[0] + toe, an[1] + 12.0)})
    return J


def _with_ids(items: List[str], prefix: str) -> List[str]:
    """Give every drawable a stable id: the rig builder binds parts by id."""
    n = [0]

    def tag(m):
        n[0] += 1
        return f'<{m.group(1)} id="{prefix}-{n[0]}"'
    return [re.sub(r"<(path|ellipse|circle)\b", tag, item) for item in items]


def multiview_text(look: str = "teal") -> str:
    """Oiler's rig source: the five views side by side, each a layer of rig
    parts (``data-rig-part``/``-bone``/``-z``, opacity channels for the faces)
    and its joint markers."""
    use(look)
    _N[0] = 0
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"',
           f'     width="{W * len(MULTIVIEW)}mm" height="{H}mm" viewBox="0 0 {W * len(MULTIVIEW)} {H}"',
           f'     data-character-design="{DESIGN_ID}">',
           "  <!-- GENERATED by scripts/svg_art/oiler_art.py (multiview mode): edit the script, not this file.",
           f"       Oiler, {O['label']}: five views, the ground at y={GROUND_Y:g}. The two LEFT views show his left side",
           "       turned to face right; the sprite target mirrors their frames into the ~mirrored rows. -->"]
    for i, (view, label, side_map) in enumerate(MULTIVIEW):
        svg.configure(dx=W * i, dy=0, ink=INK, ow=OW, colors={})
        _, layers, _ = VIEWS[view]
        side = view.startswith("side")
        O["facing"] = "left" if view.endswith("_left") else "right"
        _MAP["mirror"] = False
        attrs = f' data-view-key="{view}"' + (f' data-rig-side-map="{side_map}"' if side_map else "")
        attrs += ' data-view-mirror="x"' if view.endswith("_left") else ""
        out.append(f'  <g id="view-{view}" inkscape:groupmode="layer" inkscape:label="{label}"{attrs}>')
        parts = []
        for group, plabel, name, bone, z, channel, painter in layers():
            _MAP["sq"] = SIDE_SQUEEZE if (side and group in SIDE_TORSO) else None
            _MAP["dx"] = S_HEAD_DX / 2 if (side and group == "neck") else 0.0
            body = painter()
            _MAP["sq"], _MAP["dx"] = None, 0.0
            extra = ""
            if channel:
                extra = f' data-rig-opacity="{channel}"' + (' data-rig-opacity-default="1"' if channel in SHOWN else "")
            parts.append((z, group, plabel, name, bone, extra, _with_ids(body, f"{view}-{group}")))
        for z, group, plabel, name, bone, extra, body in sorted(parts, key=lambda q: q[0]):
            out.append(f'    <g id="{view}-{group}" inkscape:groupmode="layer" inkscape:label="{plabel}" data-rig-part="{name}" '
                       f'data-rig-bone="{bone}" data-rig-z="{svg.f(z)}"{extra}>')
            out += ["      " + item for item in body]
            out.append("    </g>")
        out.append(f'    <g id="{view}-joints" inkscape:groupmode="layer" inkscape:label="Joints">')
        for jn, (x, y) in rig_joints(view).items():
            X, Y = svg.P(x, y)
            out.append(f'      <circle id="{view}-joint-{jn}" data-rig-joint="{jn}" cx="{svg.f(X)}" cy="{svg.f(Y)}" r="1.2" fill="#ff00ff" />')
        out.append("    </g>")
        out.append("  </g>")
    out.append("</svg>")
    O["facing"] = "right"
    return "\n".join(out) + "\n"


def main() -> None:
    if len(sys.argv) > 2 and sys.argv[1] == "--multiview":
        Path(sys.argv[2]).write_text(multiview_text(), encoding="utf8")
        print(sys.argv[2])
        return
    if len(sys.argv) > 2 and sys.argv[1] == "--all":
        out = Path(sys.argv[2])
        out.mkdir(parents=True, exist_ok=True)
        for look in LOOKS:
            for view in VIEWS:
                p = out / f"oiler_{look}_{view}.svg"
                p.write_text(svg_text(look, view), encoding="utf8")
                print(p)
        return
    raise SystemExit("usage: oiler_art.py --all DIR   (candidates only; nothing is cast yet)")


if __name__ == "__main__":
    main()
