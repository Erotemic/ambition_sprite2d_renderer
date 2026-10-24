"""One view of a figure, as rig parts of SVG paint.

``draw_view`` returns the parts of one view in the humanoid rig's vocabulary
(``humanoid_svg_rig``): the body's own parts (skin), then each worn
component (``wear``) and the head's (``headdraw``) as separate parts, each
tagged with the feature that swaps it. Every part is drawn by projecting the
figure's 3D primitives through the view, so all five views agree.

The paint order depends on the view: in the front and back views both arms are
over the body and long hair hangs behind it (front) or over it (back); in the
turned views the far arm and leg are behind the body and the near ones in
front. The near side is always the character's RIGHT (``l < 0``).

The hands are held-item ready: the part ``near_hand`` (``far_hand``) rides a
grip bone whose pivot is the middle of the fist, and the fist is drawn so
that, unturned, an item through it points forward and 24 degrees up: the
contract of the game's posed hand (``posed_hand.rs``, ``ITEM_REST_ANGLE``).
"""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Dict, List, Tuple

from .body import Figure
from .drawkit import SIDES, Ctx, Part, make_ctx, shaded_region, tube3
from .geometry import Point, Vec3, View, add3, capsule_band, hull, loft_region, norm3, scale3, sub3, wrap180
from .svgout import FINE, Canvas

#: The angle (degrees above forward) an item takes in an unturned hand.
ITEM_REST_ANGLE = 24.0

#: How far down the neck (a fraction of its length) the head carries the
#: neck's upper part, and the depth that part is drawn at: over the torso and
#: its clothes, under hair hanging behind the head and under the head.
NECK_SLEEVE = 0.4
NECK_UPPER_Z = 34.5
#: The colour of the layer under the clothes at the hips.
UNDERWEAR = "#d8d0c2"


def zmap_for(view: View, tucked: bool) -> Dict[str, float]:
    turned = abs(view.s) > 0.5
    z: Dict[str, float] = {}
    for depth, _side, _sgn in SIDES:
        far = depth == "far"
        arm = (2.0 if turned else 40.0) if far else 43.0
        leg = (6.0 if turned else 10.0) if far else 13.0
        # The upper limb paints over the lower one: its round end is the
        # elbow (the knee), and the lower limb's end hides under it.
        z.update({f"{depth}_arm_u": arm + 0.5, f"{depth}_arm_l": arm, f"{depth}_arm_hand": arm + 1.0,
                  f"{depth}_leg_u": leg + 0.5, f"{depth}_leg_l": leg, f"{depth}_leg_foot": leg + 1.0})
    z.update({"pelvis": 31.0 if tucked else 20.0, "neck": 26.0, "torso": 30.0})
    return z


# ---- the body's own parts ----------------------------------------------------------------------


def _hand_frame(fig: Figure, side: str) -> Tuple[Vec3, Vec3, Vec3, Vec3, float]:
    """The hand's frame at rest: wrist, down the hand, forward (the grip
    axis), the palm's normal; and its length. The hand is turned so the grip
    axis rises ``ITEM_REST_ANGLE`` above forward."""
    j = fig.joints
    W, HT = j[f"{side}_wrist"], j[f"{side}_handtip"]
    sgn = -1.0 if side == "right" else 1.0
    u = norm3(sub3(HT, W))
    w = (-sgn, 0.0, 0.0)
    v = norm3((0.0, -u[2], u[1]))
    th = math.radians(ITEM_REST_ANGLE)
    # Turn about the palm's normal: the grip axis tips up, the fingers forward.
    v2 = norm3(sub3(scale3(v, math.cos(th)), scale3(u, math.sin(th))))
    u2 = norm3(add3(scale3(u, math.cos(th)), scale3(v, math.sin(th))))
    return W, u2, v2, w, math.dist(W, HT)


def grip_point(fig: Figure, side: str) -> Vec3:
    """The middle of the fist: where a held item's grip goes."""
    W, u, v, w, L = _hand_frame(fig, side)
    k = fig.k
    return add3(add3(W, scale3(u, 0.46 * L)), add3(scale3(v, 0.3 * k), scale3(w, 0.5 * k)))


def draw_hand(ctx: Ctx, side: str) -> List:
    fig = ctx.fig
    pt = ctx.new()
    W, u, v, w, L = _hand_frame(fig, side)
    k = fig.k * (0.94 if fig.female else 1.0) * (0.9 + 0.1 * fig.spec.body.limbs)
    pts3: List[Vec3] = []
    # A loose fist: the palm, the knuckles, the fingers curled back under.
    for t, half_v, half_w, curl in ((0.0, 2.6, 1.7, 0.0), (0.25, 4.1, 2.0, 0.0), (0.5, 4.5, 2.1, 0.2), (0.66, 4.2, 1.9, 1.0),
                                    (0.72, 3.4, 1.6, 2.0)):
        c = add3(W, scale3(u, L * t))
        c = add3(c, scale3(w, curl * k))
        for ang in range(0, 360, 45):
            r = math.radians(ang)
            pts3.append(add3(c, add3(scale3(v, half_v * k * math.cos(r)), scale3(w, half_w * k * math.sin(r)))))
    # In this view the fist's grip axis must lie exactly ITEM_REST_ANGLE above
    # forward on screen (the game's contract); turn the drawing about the
    # grip to make it so.
    g = grip_point(fig, side)
    gp = ctx.p(g)
    ax = ctx.p(add3(g, v))
    ax = (ax[0] - gp[0], ax[1] - gp[1])
    turn = 0.0
    if math.hypot(*ax) > 0.3:
        turn = -ITEM_REST_ANGLE - math.degrees(math.atan2(ax[1], ax[0]))
        turn = (turn + 180.0) % 360.0 - 180.0
    cs, sn = math.cos(math.radians(turn)), math.sin(math.radians(turn))

    def P(q: Vec3) -> Point:
        x, y = ctx.p(q)
        dx, dy = x - gp[0], y - gp[1]
        return (gp[0] + dx * cs - dy * sn, gp[1] + dx * sn + dy * cs)

    poly = hull(P(q) for q in pts3)
    thumb_a = add3(add3(W, scale3(u, L * 0.16)), add3(scale3(v, 2.8 * k), scale3(w, 0.6 * k)))
    thumb_b = add3(add3(W, scale3(u, L * 0.46)), add3(scale3(v, 3.4 * k), scale3(w, 2.0 * k)))
    thumb_front = ctx.view.depth(thumb_b) > ctx.view.depth(add3(W, scale3(u, L * 0.4)))
    from .geometry import tube

    def thumb() -> None:
        pt.region([tube(P(thumb_a), P(thumb_b), 1.3 * k, 1.05 * k)], ctx.skin)

    if not thumb_front:
        thumb()
    pt.region([poly], ctx.skin, smooth=True)
    pt.flat([capsule_band(P(W), P(add3(W, scale3(u, 0.68 * L))), 3.0 * k, 2.6 * k, 1.0 * k)], ctx.skin_sh)
    if thumb_front:
        thumb()
    if abs(ctx.view.s) > 0.5:
        for off in (-1.5, 0.0, 1.5):
            a = add3(add3(W, scale3(u, L * 0.52)), add3(scale3(v, off * k), scale3(w, 0.4 * k)))
            b = add3(add3(W, scale3(u, L * 0.68)), add3(scale3(v, off * 0.9 * k), scale3(w, 1.2 * k)))
            pt.line([P(a), P(b)], ctx.skin_dk, FINE * 0.8, smooth=False)
    return pt.els


def body_parts(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    fig = ctx.fig
    out: List[Part] = []
    T = fig.T
    # The trunk is skin from the neck to just below the waist; the pelvis
    # (underwear, then legwear) carries on from the waist, so a top that is
    # not tucked lies over the trousers instead of skin showing under it.
    pt = ctx.new()
    shaded_region(ctx, pt, fig.torso, fig.torso.top, fig.y_waist + 0.06 * T, ctx.skin, shade_cap=2.5)
    out.append(Part("torso", "torso", zmap["torso"], pt.els, "Torso"))
    pt = ctx.new()

    def crotch(a: float, y: float) -> float:
        al = abs(wrap180(a))
        return (fig.y_crotch - 0.07 * T * abs(math.sin(math.radians(al))) ** 0.8) - y

    shaded_region(ctx, pt, fig.torso.shell(0.15), fig.y_waist - 0.02 * T, fig.y_crotch, UNDERWEAR, crotch)
    out.append(Part("pelvis", "pelvis", zmap["pelvis"], pt.els, "Pelvis"))
    pt = ctx.new()
    nk = fig.neck
    shaded_region(ctx, pt, nk, nk.top, nk.bottom, ctx.skin, shade_frac=0.25)
    pt.flat(loft_region(ctx.view, nk, nk.top, nk.top + (nk.bottom - nk.top) * 0.55), ctx.skin_sh)
    out.append(Part("neck", "torso", zmap["neck"], pt.els, "Neck"))
    # The neck's upper half again, on the HEAD: when the head turns about the
    # top of the neck it carries this with it over the neck below, so a tilt
    # opens no gap and leaves no step. It is inked down its sides only (its
    # fill runs past its inked end), so the two read as one neck.
    pt = ctx.new()
    y_s = nk.top + (nk.bottom - nk.top) * NECK_SLEEVE
    pt.region(loft_region(ctx.view, nk, nk.top, y_s), ctx.skin)
    shaded_region(ctx, pt, nk, nk.top, y_s + 0.9, ctx.skin, ink=False, shade_frac=0.25)
    pt.flat(loft_region(ctx.view, nk, nk.top, nk.top + (nk.bottom - nk.top) * 0.55), ctx.skin_sh)
    out.append(Part("neck_upper", "head", NECK_UPPER_Z, pt.els, "Neck - Upper (turns with the head)"))
    j = fig.joints
    rs, re, rw = fig.arm_r
    rt, rk, rc, ra = fig.leg_r
    for depth, side, _sgn in SIDES:
        S, E, W = j[f"{side}_shoulder"], j[f"{side}_elbow"], j[f"{side}_wrist"]
        pu = ctx.new()
        tube3(ctx, pu, S, E, rs * 0.86, re, ctx.skin, joint_b=True)
        out.append(Part(f"{depth}_arm_u", f"{depth}_arm_u", zmap[f"{depth}_arm_u"], pu.els, f"Upper Arm - {depth.title()}"))
        pl = ctx.new()
        tube3(ctx, pl, E, W, re * 0.97, rw, ctx.skin)
        out.append(Part(f"{depth}_arm_l", f"{depth}_arm_l", zmap[f"{depth}_arm_l"], pl.els, f"Lower Arm - {depth.title()}"))
        out.append(Part(f"{depth}_hand", f"{depth}_grip", zmap[f"{depth}_arm_hand"], draw_hand(ctx, side), f"Hand - {depth.title()}"))
        Hp, K, A = j[f"{side}_hip"], j[f"{side}_knee"], j[f"{side}_ankle"]
        tu = ctx.new()
        tube3(ctx, tu, Hp, K, rt, rk * 1.05, ctx.skin, joint_b=True)
        out.append(Part(f"{depth}_leg_u", f"{depth}_leg_u", zmap[f"{depth}_leg_u"], tu.els, f"Thigh - {depth.title()}"))
        tl = ctx.new()
        tube3(ctx, tl, K, A, rc, ra, ctx.skin)
        out.append(Part(f"{depth}_leg_l", f"{depth}_leg_l", zmap[f"{depth}_leg_l"], tl.els, f"Shin - {depth.title()}"))
        from .wear import foot_points

        ft = ctx.new()
        sole, top, collar = foot_points(fig, side, 0.9)
        ft.region([hull(ctx.p(q) for q in sole + top + collar)], ctx.skin, smooth=True)
        out.append(Part(f"{depth}_foot", f"{depth}_leg_foot", zmap[f"{depth}_leg_foot"], ft.els, f"Foot - {depth.title()}"))
    return out


# ---- assembly ------------------------------------------------------------------------------------


def _component_parts(ctx: Ctx, zmap: Dict[str, float], slots) -> List[Part]:
    from . import headdraw, wear

    fig = ctx.fig
    o = fig.spec.outfit
    out: List[Part] = []
    if "legwear" in slots:
        out += wear.legwear_parts(ctx, zmap)
    if "top" in slots:
        out += wear.top_parts(ctx, zmap)
    if "outer" in slots:
        out += wear.outer_parts(ctx, zmap)
    if "footwear" in slots:
        out += wear.footwear_parts(ctx, zmap)
    if "hair" in slots:
        out += headdraw.hair_parts(ctx, fig.spec.hair.style, f"hair:{fig.spec.hair.style}")
    if "hat" in slots and o.hat != "none":
        out += headdraw.hat_parts(ctx, o.hat, o.hat_color, f"hat:{o.hat}")
    return out


def draw_view(fig: Figure, view: View, canvas: Canvas) -> List[Part]:
    """The rig parts of one view, in paint order, with the spec's wardrobe
    alternates drawn hidden (``rig`` sets their features off)."""
    from . import headdraw, wear
    from .body import build

    ctx = make_ctx(fig, view, canvas)
    zmap = zmap_for(view, ctx.plan["tucked"])
    parts: List[Part] = []
    parts += body_parts(ctx, zmap)
    parts += headdraw.head_parts(ctx)
    parts += headdraw.face_parts(ctx)
    parts += headdraw.facial_hair_parts(ctx)
    parts += headdraw.glasses_parts(ctx)
    parts += wear.accessory_parts(ctx, zmap)
    parts += _component_parts(ctx, zmap, ("legwear", "top", "outer", "footwear", "hair", "hat"))
    for item in fig.spec.outfit.wardrobe:
        slot, _, kind = item.partition(":")
        alt_spec = _with_slot(fig.spec, slot, kind)
        alt = make_ctx(build(alt_spec), view, canvas)
        for p in _component_parts(alt, zmap, (slot,)):
            parts.append(replace(p, name=f"{p.name}@{kind}", label=f"{p.label} ({kind})"))
    parts = [p for p in parts if p.els]
    names = [p.name for p in parts]
    assert len(names) == len(set(names)), sorted(n for n in names if names.count(n) > 1)
    parts.sort(key=lambda p: p.z)
    return parts


def _with_slot(spec, slot: str, kind: str):
    import copy

    alt = copy.deepcopy(spec)
    o = alt.outfit
    if slot == "hat":
        o.hat = kind
    elif slot == "outer":
        o.outer = kind
        # An alternate is worn at its kind's own length.
        if kind == "robe":
            o.outer_length, o.outer_open = "ankle", False
        elif kind == "coat":
            o.outer_length = "knee"
    elif slot == "top":
        o.top = kind
    elif slot == "legwear":
        o.bottom = kind
    elif slot == "footwear":
        o.shoes = kind
    elif slot == "hair":
        alt.hair.style = kind
    o.wardrobe = []
    return alt


def view_joints(fig: Figure, view: View) -> Dict[str, Point]:
    """The rig joints of one view in screen cm, by the humanoid binder's names
    (and each hand's grip, the pivot of its hand part)."""
    j = fig.joints
    out = {"waist": view.project(j["waist"]), "neck": view.project(j["neck"])}
    for depth, side, _sgn in SIDES:
        for name in ("shoulder", "elbow", "wrist", "handtip", "hip", "knee", "ankle", "toe"):
            out[f"{depth}_{name}"] = view.project(j[f"{side}_{name}"])
        out[f"{depth}_grip"] = view.project(grip_point(fig, side))
    return out


__all__ = ["ITEM_REST_ANGLE", "Part", "draw_view", "grip_point", "view_joints", "zmap_for"]
