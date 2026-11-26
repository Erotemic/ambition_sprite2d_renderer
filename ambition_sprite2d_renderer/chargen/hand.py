"""The hand: handgen's skeleton (the Dealer's hand) drawn in chargen's paint.

``handgen`` models a hand as a palm slab and five jointed digits posed by
joint angles (``HandSpec``, ``HandPose``). Here that model is placed in the
figure's 3D hand frame (``draw._hand_frame``), projected through the view,
and painted as SVG regions in the house style:

* ONE outline round the whole hand (every piece's ink, then every fill);
* a finger that crosses the palm (a fist seen from its palm side) gets a
  thin seam, not ink, so the fist reads as fingers over a palm;
* the WRIST STUB joins the forearm: it starts at the wrist with the
  forearm's own width and screen direction and runs into the heel of the
  palm, inked along its sides only, so no line crosses the wrist. It never
  reaches back past the wrist, so it cannot paint skin over a cuff.

The hand is still turned on screen about the grip so an item through the
fist points ``ITEM_REST_ANGLE`` above forward (the game's contract); the
stub bends to meet it, as a wrist does.

At sprite size a finger is two or three pixels wide: what the model buys is
the silhouette (knuckles, a thumb, a heel that flares out of the wrist) and
the right order of fingers and palm in every view, not finger detail.
"""

from __future__ import annotations

import math
from typing import List, Optional, Sequence

import numpy as np

from ..handgen.model import FINGER_NAMES, HandPose, HandSpec, SPECS, digits, knuckle_edge, palm_face, thumb_web
from ..handgen.poses import POSES
from .drawkit import Ctx
from .geometry import Point, Vec3, add3, capsule, capsule_band, hull, norm3, scale3, sub3
from .svgout import FINE, El, shade, style

#: The hand shapes a chargen hand can be drawn in (``handgen.poses``). The
#: rest shape (a loose fist, ready for an item) is ``grasp``.
SHAPES = {
    "grasp": POSES["grasp"],
    "fist": POSES["fist"],
    "open": HandPose((0.08, 0.05, 0.1, 0.15), 0.1, spread=0.35),
    "relaxed": POSES["relaxed"],
}
REST_SHAPE = "grasp"

#: How much wider than handgen's default hand a chargen hand is (the house
#: style's hands are a little chunky, so they read at sprite size).
WIDTH = 1.22


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def draw_hand_model(ctx: Ctx, side: str, frame, grip: Vec3, k: float, shape: str = REST_SHAPE, *, turn_to: Optional[float]) -> List[El]:
    """The hand of ``side`` in ``shape``, as paint elements.

    ``frame``: (wrist, along the hand, the grip axis, the palm's normal,
    the hand's length) from ``draw._hand_frame``; ``grip``: the grip point
    the drawing turns about; ``k``: the hand's width scale (1 the default
    chargen hand); ``turn_to``: the screen angle (degrees above forward)
    the grip axis is turned to, or None for a hand that holds nothing and
    is not turned (an open hand: its palm is turned to the camera, as a
    wave or a shrug shows it)."""
    fig = ctx.fig
    W, u, v, w, L = frame
    pose = SHAPES[shape]
    if turn_to is None:
        # The palm to the camera: the camera's direction off the hand's
        # length. Seen down its length (a hand pointing at us) the palm
        # keeps its own normal.
        cam = (-ctx.view.s, 0.0, ctx.view.c)
        off = sub3(cam, scale3(u, _dot(cam, u)))
        if math.sqrt(_dot(off, off)) > 0.2:
            w = norm3(off)
            # The thumb on the hand's own side: a right hand seen palm on has
            # its thumb toward the figure's right (-l). (The figure's space,
            # l left, y down, z forward, is left handed: this cross product
            # is the mirror of the physical one.)
            v = _cross(w, u)
            if side == "left":
                v = scale3(v, -1.0)
    # The model's hand frame: u along the fingers, V across with the index
    # on its negative side for a right hand (positive for a left), N out of
    # the palm. The thumb and index lie along +v (toward the grip axis).
    if side == "right":
        spec, V = SPECS["default"], scale3(v, -1.0)
    else:
        spec, V = SPECS["default"].mirrored(), v
    spec = spec.scaled(1.0, WIDTH * k)
    mid = spec.finger("middle")
    s = L / (spec.palm_length + sum(mid.bones))
    st = style()
    ol = st.outline
    # The hand starts where the heel's outline ends at the wrist.
    O = add3(W, scale3(u, 2.2 * s + ol * 0.5))

    def world(p: Sequence[float]) -> Vec3:
        return add3(O, add3(scale3(u, float(p[0]) * s), add3(scale3(V, float(p[1]) * s), scale3(w, float(p[2]) * s))))

    # Match the side-view held-item angle only in turned views, as in
    # ``draw.draw_hand``. In axial views the grip points into or out of
    # the screen; rotating that foreshortened axis twists the fist sideways.
    gp = ctx.p(grip)
    ax = ctx.p(add3(grip, v))
    ax = (ax[0] - gp[0], ax[1] - gp[1])
    turn = 0.0
    if turn_to is not None and abs(ctx.view.s) > 0.5 and math.hypot(*ax) > 0.3:
        turn = -turn_to - math.degrees(math.atan2(ax[1], ax[0]))
        turn = (turn + 180.0) % 360.0 - 180.0
    cs, sn = math.cos(math.radians(turn)), math.sin(math.radians(turn))

    def P(q: Vec3) -> Point:
        x, y = ctx.p(q)
        dx, dy = x - gp[0], y - gp[1]
        return (gp[0] + dx * cs - dy * sn, gp[1] + dx * sn + dy * cs)

    def Pl(p: Sequence[float]) -> Point:
        return P(world(p))

    def depth(p: Sequence[float]) -> float:
        return ctx.view.depth(world(p))

    palm_front = depth((0.0, 0.0, 1.0)) - depth((0.0, 0.0, 0.0)) > 0.0
    ds = digits(spec, pose)
    # The draw order (``handgen.draw.paint_order``): a phalanx on our side
    # of the palm's plane is in front of it, the rest behind; each group far
    # to near.
    sgn = 1.0 if palm_front else -1.0
    front, behind = [], []
    for name, dg in ds.items():
        for i in range(len(dg.joints) - 1):
            m = (dg.joints[i] + dg.joints[i + 1]) / 2
            (front if m[2] * sgn >= -0.25 * spec.palm_depth else behind).append((depth(m), name, i))
    behind.sort()
    front.sort()

    def phalanx(name: str, i: int) -> List[Point]:
        dg = ds[name]
        n = len(dg.widths)
        r0 = dg.widths[i] / 2 * s
        r1 = (dg.widths[i + 1] if i + 1 < n else dg.widths[-1] * 0.88) / 2 * s
        return capsule(Pl(dg.joints[i]), Pl(dg.joints[i + 1]), r0, r1, 6)

    near, far = palm_face(spec, palm_front), palm_face(spec, not palm_front)
    palm = hull(Pl(p) for p in near + far)
    web = [Pl(p) for p in thumb_web(spec, pose)]

    # The wrist stub: from the wrist (unturned, the forearm's width and
    # direction) into the heel (turned with the hand).
    rs, re, rw = fig.arm_r
    Ws = ctx.p(W)
    E = fig.joints[f"{side}_elbow"]
    fx, fy = Ws[0] - ctx.p(E)[0], Ws[1] - ctx.p(E)[1]
    fl = math.hypot(fx, fy)
    if fl < 1e-6:
        fx, fy, fl = 0.0, 1.0, 1.0
    nx, ny = -fy / fl, fx / fl
    heel = Pl((spec.palm_length * 0.3, 0.0, 0.0))
    rh = min(rw, spec.palm_half_width * s * 0.9)
    o = fig.spec.outfit
    gloved = o.gloves != "none"
    glove = o.glove_color or o.shoe_color
    if gloved:
        # A glove's cuff: over the wrist and a little up the forearm (a
        # glove is worn over a sleeve's end), its edge inked.
        cuff = 0.06 * math.dist(W, E)
        Ws = (Ws[0] - fx / fl * cuff, Ws[1] - fy / fl * cuff)
        rw = rw + 0.45
        rh = rh + 0.3
    back = [(Ws[0] + nx * rw, Ws[1] + ny * rw), (Ws[0] - nx * rw, Ws[1] - ny * rw)]
    ring = [(heel[0] + rh * math.cos(t), heel[1] + rh * math.sin(t)) for t in np.linspace(0, math.tau, 16, endpoint=False)]
    stub = hull(back + ring)
    # Its ink: the hull without the edge across the wrist.
    ib = [min(range(len(stub)), key=lambda j: math.dist(stub[j], b)) for b in back]
    stub_ink: List[List[Point]] = []
    a_, b_ = ib
    if gloved:
        stub_ink.append(stub + [stub[0]])
    elif (a_ + 1) % len(stub) == b_:
        stub_ink.append([stub[(b_ + j) % len(stub)] for j in range(len(stub) - 1)])
    elif (b_ + 1) % len(stub) == a_:
        stub_ink.append([stub[(a_ + j) % len(stub)] for j in range(len(stub) - 1)])
    else:
        stub_ink.append(stub + [stub[0]])

    def color(name: str, i: int) -> str:
        """The colour of a piece (``i`` a phalanx, -1 the palm and its web):
        skin, or the glove's (a fingerless glove leaves a finger's last two
        joints and the thumb's last bare)."""
        if not gloved:
            return ctx.skin
        if o.gloves == "fingerless" and i >= (2 if name == "thumb" else 1):
            return ctx.skin
        return glove

    cv = ctx.cv
    ink_w = cv.w(2 * ol)
    seam_w = cv.w(FINE * 0.75 * st.fine)
    pieces = [phalanx(n, i) for _d, n, i in behind] + [palm, web] + [phalanx(n, i) for _d, n, i in front]
    els: List[El] = []
    # 1. One outline round everything.
    for poly in pieces:
        els.append(El(cv.smooth_d(poly) if len(poly) > 8 else cv.poly_d(poly), fill=st.ink, stroke=st.ink, width=ink_w))
    for line in stub_ink:
        els.append(El(cv.poly_d(line, closed=False), stroke=st.ink, width=ink_w))
    # 2. The fills, far to near: the stub, the digits behind the palm, the
    # palm with its web, the digits in front (each with its seam).
    pc = color("palm", -1)
    els.append(El(cv.poly_d(stub), fill=pc, stroke=pc, width=cv.w(0.12)))
    for _d, n, i in behind:
        c = color(n, i)
        els.append(El(cv.smooth_d(phalanx(n, i)), fill=c, stroke=c, width=cv.w(0.12)))
    els.append(El(cv.poly_d(palm), fill=pc, stroke=pc, width=cv.w(0.12)))
    els.append(El(cv.poly_d(web), fill=pc, stroke=pc, width=cv.w(0.12)))
    # The palm's shade, on its left edge (the house light comes from the right).
    a = Pl((0.0, 0.0, 0.0))
    b = Pl((spec.palm_length * 0.85, 0.0, 0.0))
    hw = spec.palm_half_width * s
    els.append(El(cv.poly_d(capsule_band(a, b, hw * 0.75, hw, 0.35 * hw * st.shade_band)), fill=ctx.skin_sh if not gloved else shade(glove, 0.16)))
    if gloved:
        # The cuff's turned edge.
        d = 0.9
        c0, c1 = ((q[0] + fx / fl * d, q[1] + fy / fl * d) for q in back)
        els.append(El(cv.poly_d([c0, c1], closed=False), stroke=shade(glove, 0.4), width=seam_w * 1.4))
    if not palm_front:
        # From the back, the knuckle ridge over the tucked fingers.
        edge = [Pl(p) for p in knuckle_edge(spec, False)]
        els.append(El(cv.smooth_d(edge, closed=False), stroke=shade(pc, 0.32), width=seam_w))
    for _d, n, i in front:
        c = color(n, i)
        els.append(El(cv.smooth_d(phalanx(n, i)), fill=c, stroke=shade(c, 0.32), width=seam_w))
    # A digit is one piece of flesh: patch over the seam where two of its
    # phalanges meet (the joint's own crease stays at sprite size).
    for _d, n, i in front:
        if i > 0 and (n, i - 1) in {(nn, ii) for _dd, nn, ii in front}:
            dg = ds[n]
            r = dg.widths[i] / 2 * s * 0.85
            c = Pl(dg.joints[i])
            els.append(El(cv.smooth_d([(c[0] + r * math.cos(t), c[1] + r * math.sin(t)) for t in np.linspace(0, math.tau, 8, endpoint=False)]),
                          fill=color(n, i)))
    return els


__all__ = ["REST_SHAPE", "SHAPES", "draw_hand_model"]
