"""Perfect Cellular Automaton — skeletal tack-on target.

Uses the repo's Python skeleton / Clip / Rig pipeline (not the GUI) and keeps
all customization local to this target.  The pose language is driven by a
single canonical idle frame based on the user's approved concept art: tall Cell-
inspired horns, black helmet, cream face/chest, cellular automaton chest glyphs,
green shell armor, purple limbs, and a segmented tail.

Publish:

    PYTHONPATH=tools/ambition_sprite2d_renderer \
      python -m ambition_sprite2d_renderer publish perfect_cellular_automaton
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image, ImageColor, ImageDraw

from ...authoring.common_draw import draw_capsule
from ...authoring.rig import clamp, lerp, smoothstep, vec
from ...authoring.skeleton import (
    Channel,
    Clip,
    PartCtx,
    Rig,
    Skeleton,
    composite_polygon,
    draw_polygon,
    rounded_polygon,
    two_bone_ik,
)
from ...authoring.tackon_sheet import build_sheet, write_canonical

Color = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "perfect_cellular_automaton"
FRAME_W, FRAME_H = 256, 256
SS = 4

CENTER_X = 128.0
GROUND_Y = 236.0
ANKLE_H = 2.8

LEG_U, LEG_L = 43.0, 42.0
ARM_U, ARM_L = 33.0, 31.0
OUTLINE_W = 1.45

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 150),
    ("walk", 8, 95),
    ("slash", 6, 82),
    ("fly", 6, 96),
]
LOOPS = {"idle", "walk", "fly"}

ACTOR_METADATA = {
    "actor": {
        "character_id": "perfect_cellular_automaton",
        "display_name": "Perfect Cellular Automaton",
    },
    "body": {
        "body_plan": "HumanoidBipedWithTail",
        "body_kind": "Floating",
        "traits": ["bio_android", "cellular_automaton", "aerial_melee"],
    },
    "visual": {"default_pose": "idle", "source_style": "player_robot_fable_extension"},
    "tags": ["aerial", "enemy", "custom", "cellular"],
}


def _rgba(hex_color: str, alpha: int = 255) -> Color:
    r, g, b = ImageColor.getrgb(hex_color)
    return (r, g, b, alpha)


PAL: Dict[str, Color] = {
    "outline": _rgba("#08110C"),
    "black": _rgba("#0B110F"),
    "green_dark": _rgba("#0F4425"),
    "green": _rgba("#1E733C"),
    "green2": _rgba("#379251"),
    "green_hi": _rgba("#8FEA41"),
    "lime": _rgba("#B8FF5D"),
    "cream": _rgba("#EFE7C5"),
    "cream_shadow": _rgba("#DCD1A6"),
    "cream_hi": _rgba("#FFF8DA"),
    "purple": _rgba("#694DAA"),
    "purple_dark": _rgba("#402B72"),
    "cyan": _rgba("#59BCFF"),
    "gold": _rgba("#F1C948"),
    "shadow": (0, 0, 0, 52),
}


# ---- Skeleton -----------------------------------------------------------------


def _build_skeleton() -> Skeleton:
    sk = Skeleton()
    sk.bone("pelvis", offset=(0.0, -81.0))
    sk.bone("torso", parent="pelvis", offset=(0.0, -42.0))
    sk.bone("head", parent="torso", offset=(0.0, -50.0))
    sk.bone("tail_a", parent="pelvis", offset=(-18.0, 7.0), length=41.0, rest_angle=154.0)
    sk.bone("tail_b", parent="tail_a", offset=(41.0, 0.0), length=37.0, rest_angle=18.0)
    sk.bone("tail_c", parent="tail_b", offset=(37.0, 0.0), length=31.0, rest_angle=18.0)

    sk.bone("far_arm_u", parent="torso", offset=(-31.0, -19.0), length=ARM_U, rest_angle=90.0)
    sk.bone("far_arm_l", parent="far_arm_u", offset=(ARM_U, 0.0), length=ARM_L)
    sk.bone("near_arm_u", parent="torso", offset=(31.0, -19.0), length=ARM_U, rest_angle=90.0)
    sk.bone("near_arm_l", parent="near_arm_u", offset=(ARM_U, 0.0), length=ARM_L)

    sk.bone("far_leg_u", parent="pelvis", offset=(-18.0, 2.0), length=LEG_U, rest_angle=90.0)
    sk.bone("far_leg_l", parent="far_leg_u", offset=(LEG_U, 0.0), length=LEG_L)
    sk.bone("far_foot", parent="far_leg_l", offset=(LEG_L, 0.0), length=21.0, rest_angle=-90.0)
    sk.bone("near_leg_u", parent="pelvis", offset=(18.0, 2.0), length=LEG_U, rest_angle=90.0)
    sk.bone("near_leg_l", parent="near_leg_u", offset=(LEG_U, 0.0), length=LEG_L)
    sk.bone("near_foot", parent="near_leg_l", offset=(LEG_L, 0.0), length=21.0, rest_angle=-90.0)
    return sk


_SKEL = _build_skeleton()


# ---- Drawing helpers -----------------------------------------------------------


def _local_poly(ctx: PartCtx, pts, fill, outline=True, ow=OUTLINE_W, radius=0.0, steps=8):
    poly = ctx.pts(pts)
    if radius:
        poly = rounded_polygon(poly, radius=ctx.L(radius), steps=steps)
    draw_polygon(ctx.draw, poly, fill, PAL["outline"] if outline else None, ctx.L(ow))


def _draw_square(draw: ImageDraw.ImageDraw, x: float, y: float, size: float, fill: Color) -> None:
    draw.rounded_rectangle(
        (x - size, y - size, x + size, y + size),
        radius=max(1, int(size * 0.35)),
        fill=fill,
    )


def _draw_soft_shadow(draw: ImageDraw.ImageDraw, center: Point, sx: float, sy: float, scale: float) -> None:
    cx, cy = center[0] * scale, center[1] * scale
    draw.ellipse((cx - sx * scale, cy - sy * scale, cx + sx * scale, cy + sy * scale), fill=PAL["shadow"])


def _segment_points(a: Point, b: Point, r0: float, r1: float):
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    nx = -dy / L
    ny = dx / L
    return [
        (a[0] + nx * r0, a[1] + ny * r0),
        (b[0] + nx * r1, b[1] + ny * r1),
        (b[0] - nx * r1, b[1] - ny * r1),
        (a[0] - nx * r0, a[1] - ny * r0),
    ]


def _draw_segment_shape(ctx: PartCtx, a: Point, b: Point, r0: float, r1: float, fill: Color, radius: float = 2.0):
    poly = [ctx.cw(p) for p in _segment_points(a, b, r0, r1)]
    poly = rounded_polygon(poly, radius=ctx.L(radius), steps=6)
    draw_polygon(ctx.draw, poly, fill, PAL["outline"], ctx.L(0.8))


def _draw_forearm_stripe(ctx: PartCtx, a: Point, b: Point, inset0: float, inset1: float, w: float = 1.4):
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    tx = dx / L
    ty = dy / L
    nx = -ty
    ny = tx
    # place stripe on the top/outside edge like the diffusion reference.
    p0 = (a[0] + nx * inset0 + tx * 2.4, a[1] + ny * inset0 + ty * 2.4)
    p1 = (b[0] + nx * inset1 - tx * 3.0, b[1] + ny * inset1 - ty * 3.0)
    stripe = [
        (p0[0] + nx * w, p0[1] + ny * w),
        (p1[0] + nx * (w * 0.8), p1[1] + ny * (w * 0.8)),
        (p1[0] - nx * (w * 0.55), p1[1] - ny * (w * 0.55)),
        (p0[0] - nx * (w * 0.7), p0[1] - ny * (w * 0.7)),
    ]
    draw_polygon(ctx.draw, rounded_polygon([ctx.cw(p) for p in stripe], radius=ctx.L(0.8), steps=5), PAL["green_hi"], None, 0)


def _draw_arm_cuff(ctx: PartCtx, center: Point, angle: float, half_len: float, half_w: float, fill: Color):
    vx, vy = vec(half_len, angle)
    nx, ny = vec(half_w, angle + 90)
    cuff = [
        (center[0] - vx - nx, center[1] - vy - ny),
        (center[0] + vx - nx, center[1] + vy - ny),
        (center[0] + vx + nx, center[1] + vy + ny),
        (center[0] - vx + nx, center[1] - vy + ny),
    ]
    draw_polygon(ctx.draw, rounded_polygon([ctx.cw(p) for p in cuff], radius=ctx.L(0.8), steps=4), fill, PAL["outline"], ctx.L(0.55))


def _draw_fist(ctx: PartCtx, center: Point, angle: float, scale: float = 1.0):
    # Slightly chunky clenched fist, closer to the diffusion concept.
    hx, hy = center
    pts = [
        (-4.8, -4.8), (2.4, -5.0), (6.2, -3.6), (8.0, -0.8),
        (8.2, 4.2), (4.8, 7.4), (-1.8, 7.0), (-5.8, 3.2), (-6.0, -1.8),
    ]
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    out = []
    for x, y in pts:
        x *= scale
        y *= scale
        rx = hx + x * ca - y * sa
        ry = hy + x * sa + y * ca
        out.append((rx, ry))
    draw_polygon(ctx.draw, rounded_polygon([ctx.cw(p) for p in out], radius=ctx.L(1.4), steps=5), PAL["cream"], PAL["outline"], ctx.L(0.8))
    # three finger separation lines
    for fx in (0.5, 2.8, 5.1):
        a = (hx + (fx * ca - (-3.4) * sa) * scale, hy + (fx * sa + (-3.4) * ca) * scale)
        b = (hx + ((fx + 0.8) * ca - 3.8 * sa) * scale, hy + ((fx + 0.8) * sa + 3.8 * ca) * scale)
        ctx.draw.line((ctx.cw(a), ctx.cw(b)), fill=PAL["cream_shadow"], width=max(1, int(ctx.L(0.45))))


# ---- Part painters -------------------------------------------------------------


def _tail_chain_painter(ctx: PartCtx) -> None:
    wa = ctx.world["tail_a"]
    wb = ctx.world["tail_b"]
    wc = ctx.world["tail_c"]
    pts = [wa.origin, wa.tip, wb.tip, wc.tip]
    radii = [9.2, 8.0, 6.8, 5.4]

    def ring(poly_pts, fill, width_mul=1.0):
        poly = rounded_polygon(poly_pts, radius=ctx.L(4.0), steps=6)
        draw_polygon(ctx.draw, poly, fill, PAL["outline"], ctx.L(1.1 * width_mul))

    top, bot = [], []
    for i, p in enumerate(pts):
        nxt = pts[i + 1] if i + 1 < len(pts) else (p[0] + math.cos(math.radians(wc.angle)) * 3.0, p[1] + math.sin(math.radians(wc.angle)) * 3.0)
        if i == 0:
            ang = math.degrees(math.atan2(nxt[1] - p[1], nxt[0] - p[0]))
        else:
            prv = pts[i - 1]
            ang = math.degrees(math.atan2(nxt[1] - prv[1], nxt[0] - prv[0]))
        nx = -math.sin(math.radians(ang))
        ny = math.cos(math.radians(ang))
        r = radii[i]
        top.append((p[0] + nx * r, p[1] + ny * r))
        bot.append((p[0] - nx * r, p[1] - ny * r))
    tail_poly = [ctx.cw(p) for p in (top + bot[::-1])]
    ring(tail_poly, PAL["green_dark"])
    inner_top = []
    inner_bot = []
    for i, p in enumerate(pts[:-1]):
        nxt = pts[i + 1]
        ang = math.degrees(math.atan2(nxt[1] - p[1], nxt[0] - p[0]))
        nx = -math.sin(math.radians(ang))
        ny = math.cos(math.radians(ang))
        r = radii[i] * 0.62
        inner_top.append((p[0] + nx * r, p[1] + ny * r))
        inner_bot.append((p[0] - nx * r, p[1] - ny * r))
    inner_tip = pts[-1]
    inner_poly = [ctx.cw(p) for p in (inner_top + [inner_tip] + inner_bot[::-1])]
    composite_polygon(ctx.img, rounded_polygon(inner_poly, radius=ctx.L(3.0), steps=6), (*PAL["green2"][:3], 210), PAL["outline"], ctx.L(0.45))

    # Cell squares along the upper surface.
    markers = [lerp(0.18, 0.92, i / 5.0) for i in range(6)]
    polyline = [wa.origin, wa.tip, wb.tip, wc.tip]
    lengths = [0.0]
    total = 0.0
    for a, b in zip(polyline, polyline[1:]):
        total += math.hypot(b[0] - a[0], b[1] - a[1])
        lengths.append(total)
    for j, t in enumerate(markers):
        dist = total * t
        seg = 0
        while seg + 1 < len(lengths) and lengths[seg + 1] < dist:
            seg += 1
        a, b = polyline[seg], polyline[min(seg + 1, len(polyline) - 1)]
        span = max(1e-5, lengths[min(seg + 1, len(lengths) - 1)] - lengths[seg])
        u = (dist - lengths[seg]) / span
        px = lerp(a[0], b[0], u)
        py = lerp(a[1], b[1], u)
        cx, cy = ctx.cw((px, py - 1.2))
        _draw_square(ctx.draw, cx, cy, ctx.L(2.8 + 0.15 * math.sin(j)), PAL["lime"])

    tx, ty = ctx.cw(wc.tip)
    tr = ctx.L(6.4)
    ctx.draw.ellipse((tx - tr, ty - tr, tx + tr, ty + tr), fill=PAL["lime"], outline=PAL["outline"], width=max(1, int(ctx.L(0.7))))



def _body_painter(ctx: PartCtx) -> None:
    # Symmetric torso aimed at the simplified diffusion target.
    side_left = [(-33, -24), (-46, -4), (-43, 33), (-28, 55), (-18, 49), (-18, -14)]
    side_right = [(33, -24), (46, -4), (43, 33), (28, 55), (18, 49), (18, -14)]
    _local_poly(ctx, side_left, PAL["green_dark"], ow=1.1, radius=6.0)
    _local_poly(ctx, side_right, PAL["green_dark"], ow=1.1, radius=6.0)
    front_shell = [(-28, -33), (-10, -41), (10, -41), (28, -33), (39, -11), (37, 20), (28, 51), (12, 74), (-12, 74), (-28, 51), (-37, 20), (-39, -11)]
    _local_poly(ctx, front_shell, PAL["green"], ow=1.35, radius=9.0)

    # shoulder pads
    for ox in (-36, 36):
        c = ctx.pt((ox, -18))
        r = ctx.L(16.0)
        ctx.draw.ellipse((c[0]-r, c[1]-r*0.82, c[0]+r, c[1]+r*0.82), fill=PAL["green2"], outline=PAL["outline"], width=max(1, int(ctx.L(0.8))))
        accent = ctx.pt((ox + (7 if ox < 0 else -7), -11))
        _draw_square(ctx.draw, accent[0], accent[1], ctx.L(2.9), PAL["green_hi"])

    chest = [(-17, -18), (17, -18), (26, -9), (29, 20), (24, 49), (10, 72), (-10, 72), (-24, 49), (-29, 20), (-26, -9)]
    _local_poly(ctx, chest, PAL["cream"], ow=1.0, radius=10.0)

    for ox, oy in [(-10, 0), (0, 0), (-10, 10), (0, 10)]:
        c = ctx.pt((ox, oy))
        _draw_square(ctx.draw, c[0], c[1], ctx.L(3.2), PAL["cyan"])
    for ox, oy in [(15, 0), (15, 10), (5, 10), (15, 20), (5, 20)]:
        c = ctx.pt((ox, oy))
        _draw_square(ctx.draw, c[0], c[1], ctx.L(3.2), PAL["gold"])

    panel = [(10, 26), (25, 26), (25, 55), (10, 55)]
    _local_poly(ctx, panel, PAL["black"], ow=0.9, radius=2.0)
    for ox, oy, live in [(14, 31, 1), (14, 43, 1), (14, 55, 1), (23, 31, 0), (23, 43, 1), (23, 55, 0)]:
        c = ctx.pt((ox, oy))
        _draw_square(ctx.draw, c[0], c[1], ctx.L(3.2), PAL["lime"] if live else PAL["green_dark"])

    belt_left = [(-36, 46), (-16, 50), (-18, 68), (-40, 62)]
    belt_right = [(36, 46), (16, 50), (18, 68), (40, 62)]
    _local_poly(ctx, belt_left, PAL["green2"], ow=1.0, radius=3.0)
    _local_poly(ctx, belt_right, PAL["green2"], ow=1.0, radius=3.0)
    for ox in (-27, 27):
        c = ctx.pt((ox, 56))
        _draw_square(ctx.draw, c[0], c[1], ctx.L(3.6), PAL["green_hi"])

    codpiece = [(-15, 48), (15, 48), (23, 62), (20, 79), (0, 82), (-20, 79), (-23, 62)]
    _local_poly(ctx, codpiece, PAL["green"], ow=1.0, radius=6.0)


def _head_painter(ctx: PartCtx) -> None:
    p = ctx.params
    helmet = [(-31, -16), (-18, -31), (0, -37), (18, -31), (31, -16), (31, 11), (20, 20), (-20, 20), (-31, 11)]
    _local_poly(ctx, helmet, PAL["black"], ow=1.45, radius=9.0)

    left_horn = [(-18, -25), (-44, -58), (-33, -11)]
    right_horn = [(18, -25), (44, -58), (33, -11)]
    _local_poly(ctx, left_horn, PAL["green"], ow=1.0, radius=1.0)
    _local_poly(ctx, right_horn, PAL["green"], ow=1.0, radius=1.0)
    for ox in (-44, 44):
        c = ctx.pt((ox, -58))
        rr = ctx.L(4.8)
        ctx.draw.ellipse((c[0]-rr, c[1]-rr, c[0]+rr, c[1]+rr), fill=PAL["lime"], outline=PAL["outline"], width=max(1, int(ctx.L(0.55))))

    gem = ctx.pt((0, -22))
    _draw_square(ctx.draw, gem[0], gem[1], ctx.L(4.6), PAL["green_hi"])
    for ox in (-18, 18):
        c = ctx.pt((ox, -1))
        s = ctx.L(5.6)
        ctx.draw.rectangle((c[0]-s, c[1]-s, c[0]+s, c[1]+s), outline=PAL["green"], width=max(1, int(ctx.L(1.1))))
    for ox, oy in [(-26, 6), (26, 6)]:
        c = ctx.pt((ox, oy))
        _draw_square(ctx.draw, c[0], c[1], ctx.L(3.6), PAL["green_hi"])

    face = [(-19, 10), (19, 10), (25, 16), (23, 34), (11, 49), (-11, 49), (-23, 34), (-25, 16)]
    _local_poly(ctx, face, PAL["cream"], ow=1.1, radius=8.0)
    snout = ctx.pt((0, 19))
    nx, ny = snout
    ctx.draw.ellipse((nx-ctx.L(5.8), ny-ctx.L(3.0), nx+ctx.L(5.8), ny+ctx.L(3.0)), fill=PAL["black"])
    a, b = ctx.pt((0, 22)), ctx.pt((0, 33))
    ctx.draw.line((a, b), fill=PAL["outline"], width=max(1, int(ctx.L(0.9))))
    ml, mc, mr = ctx.pt((-12, 31)), ctx.pt((0, 34)), ctx.pt((12, 31))
    ctx.draw.line((ml, mc), fill=PAL["outline"], width=max(1, int(ctx.L(0.9))))
    ctx.draw.line((mc, mr), fill=PAL["outline"], width=max(1, int(ctx.L(0.9))))
    chin = ctx.pt((0, 42))
    ctx.draw.rounded_rectangle((chin[0]-ctx.L(4.5), chin[1]-ctx.L(1.0), chin[0]+ctx.L(4.5), chin[1]+ctx.L(9.5)), radius=max(1, int(ctx.L(1.6))), fill=PAL["black"])


def _far_arm_painter(ctx: PartCtx) -> None:
    u, low = ctx.world["far_arm_u"], ctx.world["far_arm_l"]
    _draw_segment_shape(ctx, u.origin, u.tip, 10.0, 8.0, PAL["green2"], radius=2.4)
    sx, sy = ctx.cw(u.origin)
    rr = ctx.L(5.3)
    ctx.draw.ellipse((sx-rr, sy-rr, sx+rr, sy+rr), fill=PAL["green_hi"], outline=PAL["outline"], width=max(1, int(ctx.L(0.7))))
    _draw_segment_shape(ctx, low.origin, low.tip, 10.2, 9.0, PAL["purple"], radius=2.2)
    _draw_forearm_stripe(ctx, low.origin, low.tip, 5.5, 5.0, 1.55)
    ex, ey = ctx.cw(low.origin)
    er = ctx.L(4.0)
    ctx.draw.ellipse((ex-er, ey-er, ex+er, ey+er), fill=PAL["green_hi"], outline=PAL["outline"], width=max(1, int(ctx.L(0.55))))
    wrist = (low.tip[0] - math.cos(math.radians(low.angle)) * 3.8, low.tip[1] - math.sin(math.radians(low.angle)) * 3.8)
    _draw_arm_cuff(ctx, wrist, low.angle, 5.0, 4.1, PAL["green_dark"])
    cuff_node = ctx.cw((wrist[0], wrist[1]))
    _draw_square(ctx.draw, cuff_node[0], cuff_node[1], ctx.L(3.0), PAL["green_hi"])
    _draw_fist(ctx, (low.tip[0] + math.cos(math.radians(low.angle)) * 2.6, low.tip[1] + math.sin(math.radians(low.angle)) * 2.6), low.angle + 10.0, scale=1.05)


def _near_arm_painter(ctx: PartCtx) -> None:
    u, low = ctx.world["near_arm_u"], ctx.world["near_arm_l"]
    _draw_segment_shape(ctx, u.origin, u.tip, 10.2, 8.2, PAL["green2"], radius=2.5)
    sx, sy = ctx.cw(u.origin)
    rr = ctx.L(5.5)
    ctx.draw.ellipse((sx-rr, sy-rr, sx+rr, sy+rr), fill=PAL["green_hi"], outline=PAL["outline"], width=max(1, int(ctx.L(0.7))))
    _draw_segment_shape(ctx, low.origin, low.tip, 10.5, 9.2, PAL["purple"], radius=2.2)
    _draw_forearm_stripe(ctx, low.origin, low.tip, 5.6, 5.1, 1.7)
    ex, ey = ctx.cw(low.origin)
    er = ctx.L(4.0)
    ctx.draw.ellipse((ex-er, ey-er, ex+er, ey+er), fill=PAL["green_hi"], outline=PAL["outline"], width=max(1, int(ctx.L(0.55))))
    wrist = (low.tip[0] - math.cos(math.radians(low.angle)) * 3.8, low.tip[1] - math.sin(math.radians(low.angle)) * 3.8)
    _draw_arm_cuff(ctx, wrist, low.angle, 5.2, 4.3, PAL["green_dark"])
    cuff_node = ctx.cw((wrist[0], wrist[1]))
    _draw_square(ctx.draw, cuff_node[0], cuff_node[1], ctx.L(3.1), PAL["green_hi"])
    _draw_fist(ctx, (low.tip[0] + math.cos(math.radians(low.angle)) * 2.8, low.tip[1] + math.sin(math.radians(low.angle)) * 2.8), low.angle - 6.0, scale=1.1)


def _leg_painter(side: str):
    upper_key = f"{side}_leg_u"
    lower_key = f"{side}_leg_l"
    upper_fill = PAL["purple"]
    lower_fill = PAL["purple_dark"]
    radius_u0 = 9.6 if side == "near" else 8.6
    radius_u1 = 7.9 if side == "near" else 7.0
    radius_l0 = 8.8 if side == "near" else 7.8
    radius_l1 = 7.0 if side == "near" else 6.4

    def fn(ctx: PartCtx) -> None:
        u, low = ctx.world[upper_key], ctx.world[lower_key]
        _draw_segment_shape(ctx, u.origin, u.tip, radius_u0, radius_u1, upper_fill, radius=2.4)
        _draw_segment_shape(ctx, low.origin, low.tip, radius_l0, radius_l1, lower_fill, radius=2.2)
        # knee shield, larger like the target.
        kx, ky = ctx.cw(low.origin)
        rr = ctx.L(8.0 if side == "near" else 7.2)
        ctx.draw.ellipse((kx - rr, ky - rr, kx + rr, ky + rr), fill=PAL["green_hi"], outline=PAL["outline"], width=max(1, int(ctx.L(0.75))))
    return fn



def _foot_painter(side: str):
    pts = [(-5.0, -2.0), (7.5, -2.2), (17.0, -0.8), (22.0, 3.2), (20.0, 9.4), (-2.2, 9.0)]

    def fn(ctx: PartCtx) -> None:
        poly = rounded_polygon(ctx.pts(pts), radius=ctx.L(1.5), steps=5)
        draw_polygon(ctx.draw, poly, PAL["cream"], PAL["outline"], ctx.L(0.9))
        heel = [(-7.0, -4.5), (2.4, -4.5), (2.4, 5.2), (-7.0, 5.2)]
        draw_polygon(ctx.draw, rounded_polygon(ctx.pts(heel), radius=ctx.L(1.0)), PAL["black"], PAL["outline"], ctx.L(0.6))
        cuff = [(-2.5, -5.0), (8.5, -5.0), (8.5, 4.2), (-2.5, 4.2)]
        draw_polygon(ctx.draw, rounded_polygon(ctx.pts(cuff), radius=ctx.L(1.0)), PAL["green"], PAL["outline"], ctx.L(0.7))
        node = ctx.pt((2.0, -0.2))
        _draw_square(ctx.draw, node[0], node[1], ctx.L(3.2), PAL["green_hi"])
    return fn


def _build_rig() -> Rig:
    rig = Rig(_SKEL)
    rig.part("tail", "tail_a", 5, _tail_chain_painter)
    rig.part("far_leg", "far_leg_u", 10, _leg_painter("far"))
    rig.part("far_foot", "far_foot", 11, _foot_painter("far"))
    rig.part("body", "torso", 40, _body_painter)
    rig.part("far_arm", "far_arm_u", 44, _far_arm_painter)
    rig.part("head", "head", 50, _head_painter)
    rig.part("near_leg", "near_leg_u", 60, _leg_painter("near"))
    rig.part("near_foot", "near_foot", 61, _foot_painter("near"))
    rig.part("near_arm", "near_arm_u", 70, _near_arm_painter)
    return rig


_RIG = _build_rig()


# ---- Clips --------------------------------------------------------------------

_TAU = math.tau


def _stride(phase_off: float, hip_off: float, duty: float = 0.58, half: float = 16.0, lift_h: float = 12.0):
    def x(t: float) -> float:
        ph = (t + phase_off) % 1.0
        if ph < duty:
            return hip_off + lerp(half, -half, ph / duty)
        u = (ph - duty) / (1.0 - duty)
        return hip_off + lerp(-half, half, smoothstep(u))

    def lift(t: float) -> float:
        ph = (t + phase_off) % 1.0
        if ph < duty:
            return 0.0
        u = (ph - duty) / (1.0 - duty)
        return lift_h * math.sin(math.pi * u)

    def pitch(t: float) -> float:
        ph = (t + phase_off) % 1.0
        if ph < duty:
            return lerp(-6.0, 8.0, ph / duty)
        u = (ph - duty) / (1.0 - duty)
        return lerp(8.0, -8.0, smoothstep(u))

    return x, lift, pitch


_NEAR_X, _NEAR_LIFT, _NEAR_PITCH = _stride(0.0, 44.0)
_FAR_X, _FAR_LIFT, _FAR_PITCH = _stride(0.5, -44.0)
_DEFAULT_FOOT_X = {"near": 44.0, "far": -44.0}

# Canonical pose closely matching the approved reference image.
CLIP_IDLE = Clip(
    loop=True,
    channels={
        "root_y": lambda t: 0.35 * math.sin(_TAU * t),
        "root_x": lambda t: 0.22 * math.sin(_TAU * t),
        "pelvis": lambda t: 0.4 * math.sin(_TAU * t),
        "torso": lambda t: 0.7 * math.sin(_TAU * (t - 0.05)),
        "head": lambda t: -0.6 * math.sin(_TAU * (t - 0.10)),
        "tail_a": lambda t: -5.0 + 2.0 * math.sin(_TAU * (t - 0.14)),
        "tail_b": lambda t: -5.0 + 2.6 * math.sin(_TAU * (t - 0.10)),
        "tail_c": lambda t: 2.0 + 3.0 * math.sin(_TAU * (t - 0.06)),
        "near_arm_u": lambda t: 28.0 + 1.0 * math.sin(_TAU * t),
        "near_arm_l": lambda t: -12.0 + 1.0 * math.sin(_TAU * (t - 0.08)),
        "far_arm_u": lambda t: 18.0 - 1.0 * math.sin(_TAU * t),
        "far_arm_l": lambda t: -10.0 + 1.0 * math.sin(_TAU * (t - 0.05)),
        "near_foot_x": _DEFAULT_FOOT_X["near"],
        "far_foot_x": _DEFAULT_FOOT_X["far"],
        "blink": Channel((0.0, 0), (0.47, 0, "linear"), (0.50, 1, "linear"), (0.55, 1, "linear"), (0.60, 0, "linear")),
        "eye_squint": 0.02,
    },
)

CLIP_WALK = Clip(
    loop=True,
    channels={
        "root_y": lambda t: 1.8 * math.cos(2.0 * _TAU * t) - 0.3,
        "pelvis": lambda t: 2.5 * math.sin(_TAU * t),
        "torso": lambda t: 2.0 - 4.0 * math.sin(_TAU * t),
        "head": lambda t: -1.8 + 2.4 * math.sin(_TAU * (t - 0.10)),
        "tail_a": lambda t: -12.0 - 9.0 * math.sin(_TAU * t),
        "tail_b": lambda t: -10.0 - 14.0 * math.sin(_TAU * t),
        "tail_c": lambda t: 4.0 + 10.0 * math.sin(_TAU * (t + 0.05)),
        "near_arm_u": lambda t: 8.0 + 16.0 * math.cos(_TAU * t),
        "near_arm_l": lambda t: -52.0 - 7.0 * math.cos(_TAU * t),
        "far_arm_u": lambda t: 18.0 - 18.0 * math.cos(_TAU * t),
        "far_arm_l": lambda t: -18.0 + 8.0 * math.cos(_TAU * t),
        "near_foot_x": _NEAR_X,
        "near_foot_lift": _NEAR_LIFT,
        "near_foot_pitch": _NEAR_PITCH,
        "far_foot_x": _FAR_X,
        "far_foot_lift": _FAR_LIFT,
        "far_foot_pitch": _FAR_PITCH,
        "eye_squint": 0.16,
    },
)

CLIP_SLASH = Clip(
    loop=False,
    channels={
        "root_x": Channel((0, 0), (0.20, -4.0), (0.48, 10.0, "out"), (0.76, 3.0), (1, 0)),
        "pelvis": Channel((0, 0), (0.20, -5.0), (0.48, 8.0, "out"), (1, 0)),
        "torso": Channel((0, 0), (0.20, -12.0), (0.50, 14.0, "out"), (0.80, 4.0), (1, 0)),
        "head": Channel((0, 0), (0.20, -5.0), (0.50, 4.0, "out"), (1, 0)),
        "tail_a": Channel((0, -7), (0.20, -18), (0.50, 10, "out"), (1, -6)),
        "tail_b": Channel((0, -8), (0.20, -22), (0.50, 16, "out"), (1, -8)),
        "tail_c": Channel((0, 6), (0.20, -4), (0.50, 20, "out"), (1, 4)),
        "near_arm_u": Channel((0, 8), (0.16, -76), (0.32, -90), (0.52, 0, "out"), (0.78, 10), (1, 8)),
        "near_arm_l": Channel((0, -52), (0.16, -50), (0.32, -60), (0.52, 12, "out"), (0.78, -6), (1, -52)),
        "far_arm_u": Channel((0, 18), (0.20, 26), (0.50, -6, "out"), (1, 18)),
        "far_arm_l": Channel((0, -18), (0.20, -6), (0.50, -16, "out"), (1, -18)),
        "near_foot_x": 44.0,
        "far_foot_x": -44.0,
        "far_foot_lift": Channel((0, 0), (0.35, 0), (0.50, 4.0, "out"), (0.82, 0), (1, 0)),
        "far_foot_pitch": Channel((0, 0), (0.35, 0), (0.50, 12.0, "out"), (0.82, 0), (1, 0)),
        "eye_squint": Channel((0, 0.1), (0.24, 0.35), (0.50, 0.55), (1, 0.08)),
    },
)

CLIP_FLY = Clip(
    loop=True,
    channels={
        "root_y": lambda t: -18.0 + 2.8 * math.sin(_TAU * t),
        "root_x": lambda t: 0.9 * math.sin(_TAU * (t + 0.15)),
        "pelvis": lambda t: 1.8 * math.sin(_TAU * t),
        "torso": lambda t: 3.8 * math.sin(_TAU * t),
        "head": lambda t: -2.0 * math.sin(_TAU * (t - 0.10)),
        "tail_a": lambda t: -9.0 + 10.0 * math.sin(_TAU * (t - 0.18)),
        "tail_b": lambda t: -6.0 + 14.0 * math.sin(_TAU * (t - 0.12)),
        "tail_c": lambda t: 8.0 + 10.0 * math.sin(_TAU * (t - 0.08)),
        "near_arm_u": lambda t: -68.0 - 6.0 * math.sin(_TAU * t),
        "near_arm_l": lambda t: 10.0 + 5.0 * math.sin(_TAU * (t - 0.04)),
        "far_arm_u": lambda t: 66.0 + 6.0 * math.sin(_TAU * t),
        "far_arm_l": lambda t: -20.0 - 5.0 * math.sin(_TAU * (t - 0.04)),
        "near_foot_x": 22.0,
        "far_foot_x": -22.0,
        "near_foot_lift": 18.0,
        "far_foot_lift": 14.0,
        "near_foot_pitch": 8.0,
        "far_foot_pitch": 8.0,
        "hover": 1.0,
        "eye_squint": 0.05,
    },
)

CLIPS: Dict[str, Clip] = {"idle": CLIP_IDLE, "walk": CLIP_WALK, "slash": CLIP_SLASH, "fly": CLIP_FLY}


def _foot_target(sampled: Dict[str, float], side: str) -> Point:
    ax = CENTER_X + sampled.get(f"{side}_foot_x", _DEFAULT_FOOT_X[side])
    ay = GROUND_Y - ANKLE_H - sampled.get(f"{side}_foot_lift", 0.0)
    return (ax, ay)


def _solve(animation: str, t: float):
    sampled = CLIPS[animation].sample(t)
    root = (CENTER_X + sampled.get("root_x", 0.0), GROUND_Y + sampled.get("root_y", 0.0))
    angles = {name: val for name, val in sampled.items() if name in _SKEL.bones}
    w0 = _SKEL.world(angles, root=root)
    for side in ("far", "near"):
        hip = w0[f"{side}_leg_u"].origin
        ankle = _foot_target(sampled, side)
        a1, a2 = two_bone_ik(hip, ankle, LEG_U, LEG_L, bend=1.0)
        pelvis_angle = w0["pelvis"].angle
        angles[f"{side}_leg_u"] = a1 - pelvis_angle - 90.0
        angles[f"{side}_leg_l"] = a2 - a1
        pitch = sampled.get(f"{side}_foot_pitch", 0.0)
        angles[f"{side}_foot"] = pitch - a2 + 90.0
    world = _SKEL.world(angles, root=root)
    return world, sampled


def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    if animation in LOOPS:
        t = frame_idx / max(1, nframes)
    else:
        t = frame_idx / max(1, nframes - 1)
    img = Image.new("RGBA", (FRAME_W * SS, FRAME_H * SS), (0, 0, 0, 0))
    world, params = _solve(animation, t)
    _RIG.draw(img, ImageDraw.Draw(img), world, SS, params)
    return img.resize((FRAME_W, FRAME_H), Image.Resampling.LANCZOS)


# ---- Target hooks --------------------------------------------------------------


def _body_metrics_override(fw: int, fh: int):
    return {
        "body_pixel_bbox": {"x": int(fw * 0.16), "y": int(fh * 0.03), "w": int(fw * 0.68), "h": int(fh * 0.91)},
        "feet_pixel": {"x": fw * 0.50, "y": fh * 0.92},
        "feet_anchor_norm": {"x": 0.0, "y": round(0.5 - 0.92, 6)},
    }


def render(out_dir: Path, **opts) -> List[Path]:
    del opts
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=Path(out_dir),
        frame_size=(FRAME_W, FRAME_H),
        label_width=100,
        auto_crop=False,
        body_metrics_fn=_body_metrics_override,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning={"collision_scale": 1.12, "frame_sample_inset": 1},
        animation_key_map={"idle": "idle", "walk": "walk", "slash": "slash", "fly": "fly"},
        attack_hitboxes={"slash": {"bbox": {"x": 122, "y": 72, "w": 46, "h": 74}}},
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    return [Path(outputs[k]) for k in keys if outputs.get(k)]


def render_canonical(out_dir: Path, **opts) -> Path:
    del opts
    return write_canonical(TARGET_NAME, ROWS, render_frame, Path(out_dir), frame_size=(FRAME_W, FRAME_H))
