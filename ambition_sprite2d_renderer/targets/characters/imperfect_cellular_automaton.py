"""Imperfect Cellular Automaton — skeletal tack-on target.

Uses the repo's Python skeleton / Clip / Rig pipeline (not the GUI) and keeps
all customization local to this target.  The pose language is driven by a
single canonical idle frame based on the user's approved concept art: tall Cell-
inspired horns, black helmet, cream face/chest, cellular automaton chest glyphs,
green shell armor, purple limbs, and a segmented tail.

Publish:

    PYTHONPATH=tools/ambition_sprite2d_renderer \
      python -m ambition_sprite2d_renderer publish imperfect_cellular_automaton
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

TARGET_NAME = "imperfect_cellular_automaton"
FRAME_W, FRAME_H = 256, 256
SS = 4

CENTER_X = 128.0
GROUND_Y = 236.0
ANKLE_H = 2.8

LEG_U, LEG_L = 46.0, 44.0
ARM_U, ARM_L = 31.0, 29.0
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
        "character_id": "imperfect_cellular_automaton",
        "display_name": "Imperfect Cellular Automaton",
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
    sk.bone("pelvis", offset=(0.0, -82.0))
    sk.bone("torso", parent="pelvis", offset=(0.0, -47.0))
    sk.bone("head", parent="torso", offset=(0.0, -46.0))
    sk.bone("tail_a", parent="pelvis", offset=(-18.0, 7.0), length=41.0, rest_angle=154.0)
    sk.bone("tail_b", parent="tail_a", offset=(41.0, 0.0), length=37.0, rest_angle=18.0)
    sk.bone("tail_c", parent="tail_b", offset=(37.0, 0.0), length=31.0, rest_angle=18.0)

    sk.bone("far_arm_u", parent="torso", offset=(-36.0, -16.0), length=ARM_U, rest_angle=90.0)
    sk.bone("far_arm_l", parent="far_arm_u", offset=(ARM_U, 0.0), length=ARM_L)
    sk.bone("near_arm_u", parent="torso", offset=(36.0, -16.0), length=ARM_U, rest_angle=90.0)
    sk.bone("near_arm_l", parent="near_arm_u", offset=(ARM_U, 0.0), length=ARM_L)

    sk.bone("far_leg_u", parent="pelvis", offset=(-20.0, 2.0), length=LEG_U, rest_angle=90.0)
    sk.bone("far_leg_l", parent="far_leg_u", offset=(LEG_U, 0.0), length=LEG_L)
    sk.bone("far_foot", parent="far_leg_l", offset=(LEG_L, 0.0), length=21.0, rest_angle=-90.0)
    sk.bone("near_leg_u", parent="pelvis", offset=(20.0, 2.0), length=LEG_U, rest_angle=90.0)
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
    # stronger V-shaped torso, less round and less heavy.
    side_left = [(-37, -29), (-50, -2), (-44, 24), (-30, 47), (-18, 43), (-17, -16)]
    side_right = [(37, -29), (50, -2), (44, 24), (30, 47), (18, 43), (17, -16)]
    _local_poly(ctx, side_left, PAL["green_dark"], ow=1.1, radius=5.0)
    _local_poly(ctx, side_right, PAL["green_dark"], ow=1.1, radius=5.0)

    front_shell = [(-30, -37), (-12, -44), (12, -44), (30, -37), (42, -15), (38, 9), (28, 36), (14, 63), (0, 74), (-14, 63), (-28, 36), (-38, 9), (-42, -15)]
    _local_poly(ctx, front_shell, PAL["green"], ow=1.35, radius=7.0)

    for ox in (-40, 40):
        c = ctx.pt((ox, -22))
        r = ctx.L(15.2)
        ctx.draw.ellipse((c[0]-r, c[1]-r*0.76, c[0]+r, c[1]+r*0.76), fill=PAL["green2"], outline=PAL["outline"], width=max(1, int(ctx.L(0.8))))
        accent = ctx.pt((ox + (8 if ox < 0 else -8), -16))
        _draw_square(ctx.draw, accent[0], accent[1], ctx.L(2.6), PAL["green_hi"])

    chest = [(-18, -20), (18, -20), (25, -12), (26, 8), (23, 34), (12, 60), (0, 70), (-12, 60), (-23, 34), (-26, 8), (-25, -12)]
    _local_poly(ctx, chest, PAL["cream"], ow=1.0, radius=8.0)

    life_cells = ctx.params.get("life_cells", [[0] * 4 for _ in range(4)])
    grid_origin_x, grid_origin_y = -13.5, -2.0
    cell_step = 9.0
    cell_size = 2.6
    for gy in range(4):
        for gx in range(4):
            c = ctx.pt((grid_origin_x + gx * cell_step, grid_origin_y + gy * cell_step))
            live = bool(life_cells[gy][gx])
            if live:
                fill = PAL["cyan"] if (gx + gy) % 2 == 0 else PAL["gold"]
            else:
                fill = PAL["cream_shadow"]
            _draw_square(ctx.draw, c[0], c[1], ctx.L(cell_size), fill)

    panel = [(9, 24), (23, 24), (23, 53), (9, 53)]
    _local_poly(ctx, panel, PAL["black"], ow=0.9, radius=2.0)
    for ox, oy, live in [(13, 29, 1), (13, 41, 1), (13, 52, 1), (21, 29, 0), (21, 41, 1), (21, 52, 0)]:
        c = ctx.pt((ox, oy))
        _draw_square(ctx.draw, c[0], c[1], ctx.L(2.8), PAL["lime"] if live else PAL["green_dark"])

    belt_left = [(-34, 43), (-15, 47), (-17, 61), (-38, 57)]
    belt_right = [(34, 43), (15, 47), (17, 61), (38, 57)]
    _local_poly(ctx, belt_left, PAL["green2"], ow=1.0, radius=3.0)
    _local_poly(ctx, belt_right, PAL["green2"], ow=1.0, radius=3.0)
    for ox in (-25, 25):
        c = ctx.pt((ox, 53))
        _draw_square(ctx.draw, c[0], c[1], ctx.L(3.4), PAL["green_hi"])

    codpiece = [(-13, 46), (13, 46), (18, 61), (16, 78), (0, 83), (-16, 78), (-18, 61)]
    _local_poly(ctx, codpiece, PAL["green"], ow=1.0, radius=5.5)


def _head_painter(ctx: PartCtx) -> None:
    p = ctx.params
    helmet = [(-25, -13), (-14, -26), (0, -31), (14, -26), (25, -13), (25, 8), (16, 15), (-16, 15), (-25, 8)]
    _local_poly(ctx, helmet, PAL["black"], ow=1.35, radius=7.0)

    left_horn = [(-14, -20), (-35, -48), (-26, -8)]
    right_horn = [(14, -20), (35, -48), (26, -8)]
    _local_poly(ctx, left_horn, PAL["green"], ow=1.0, radius=1.0)
    _local_poly(ctx, right_horn, PAL["green"], ow=1.0, radius=1.0)
    for ox in (-35, 35):
        c = ctx.pt((ox, -48))
        rr = ctx.L(4.0)
        ctx.draw.ellipse((c[0]-rr, c[1]-rr, c[0]+rr, c[1]+rr), fill=PAL["lime"], outline=PAL["outline"], width=max(1, int(ctx.L(0.5))))

    gem = ctx.pt((0, -18))
    _draw_square(ctx.draw, gem[0], gem[1], ctx.L(4.0), PAL["green_hi"])
    for ox in (-15, 15):
        c = ctx.pt((ox, -1))
        s = ctx.L(4.8)
        ctx.draw.rectangle((c[0]-s, c[1]-s, c[0]+s, c[1]+s), outline=PAL["green"], width=max(1, int(ctx.L(1.0))))
    for ox, oy in [(-22, 4), (22, 4)]:
        c = ctx.pt((ox, oy))
        _draw_square(ctx.draw, c[0], c[1], ctx.L(3.0), PAL["green_hi"])

    face = [(-16, 8), (16, 8), (21, 14), (20, 30), (10, 43), (-10, 43), (-20, 30), (-21, 14)]
    _local_poly(ctx, face, PAL["cream"], ow=1.0, radius=6.5)
    snout = ctx.pt((0, 16))
    nx, ny = snout
    ctx.draw.ellipse((nx-ctx.L(5.2), ny-ctx.L(2.6), nx+ctx.L(5.2), ny+ctx.L(2.6)), fill=PAL["black"])
    a, b = ctx.pt((0, 18)), ctx.pt((0, 28))
    ctx.draw.line((a, b), fill=PAL["outline"], width=max(1, int(ctx.L(0.8))))
    ml, mc, mr = ctx.pt((-10, 26)), ctx.pt((0, 29)), ctx.pt((10, 26))
    ctx.draw.line((ml, mc), fill=PAL["outline"], width=max(1, int(ctx.L(0.8))))
    ctx.draw.line((mc, mr), fill=PAL["outline"], width=max(1, int(ctx.L(0.8))))
    chin = ctx.pt((0, 36))
    ctx.draw.rounded_rectangle((chin[0]-ctx.L(4.0), chin[1]-ctx.L(1.0), chin[0]+ctx.L(4.0), chin[1]+ctx.L(8.0)), radius=max(1, int(ctx.L(1.4))), fill=PAL["black"])


def _far_arm_painter(ctx: PartCtx) -> None:
    u, low = ctx.world["far_arm_u"], ctx.world["far_arm_l"]
    _draw_segment_shape(ctx, u.origin, u.tip, 8.4, 6.6, PAL["green2"], radius=2.0)
    sx, sy = ctx.cw(u.origin)
    rr = ctx.L(4.8)
    ctx.draw.ellipse((sx-rr, sy-rr, sx+rr, sy+rr), fill=PAL["green_hi"], outline=PAL["outline"], width=max(1, int(ctx.L(0.65))))
    _draw_segment_shape(ctx, low.origin, low.tip, 8.6, 7.0, PAL["purple"], radius=2.0)
    _draw_forearm_stripe(ctx, low.origin, low.tip, 4.5, 3.8, 1.35)
    ex, ey = ctx.cw(low.origin)
    er = ctx.L(3.5)
    ctx.draw.ellipse((ex-er, ey-er, ex+er, ey+er), fill=PAL["green_hi"], outline=PAL["outline"], width=max(1, int(ctx.L(0.5))))
    wrist = (low.tip[0] - math.cos(math.radians(low.angle)) * 3.2, low.tip[1] - math.sin(math.radians(low.angle)) * 3.2)
    _draw_arm_cuff(ctx, wrist, low.angle, 4.2, 3.4, PAL["green_dark"])
    cuff_node = ctx.cw((wrist[0], wrist[1]))
    _draw_square(ctx.draw, cuff_node[0], cuff_node[1], ctx.L(2.6), PAL["green_hi"])
    _draw_fist(ctx, (low.tip[0] + math.cos(math.radians(low.angle)) * 2.4, low.tip[1] + math.sin(math.radians(low.angle)) * 2.4), low.angle + 6.0, scale=0.95)


def _near_arm_painter(ctx: PartCtx) -> None:
    u, low = ctx.world["near_arm_u"], ctx.world["near_arm_l"]
    _draw_segment_shape(ctx, u.origin, u.tip, 8.8, 6.8, PAL["green2"], radius=2.0)
    sx, sy = ctx.cw(u.origin)
    rr = ctx.L(5.0)
    ctx.draw.ellipse((sx-rr, sy-rr, sx+rr, sy+rr), fill=PAL["green_hi"], outline=PAL["outline"], width=max(1, int(ctx.L(0.65))))
    _draw_segment_shape(ctx, low.origin, low.tip, 8.9, 7.3, PAL["purple"], radius=2.0)
    _draw_forearm_stripe(ctx, low.origin, low.tip, 4.7, 4.0, 1.45)
    ex, ey = ctx.cw(low.origin)
    er = ctx.L(3.5)
    ctx.draw.ellipse((ex-er, ey-er, ex+er, ey+er), fill=PAL["green_hi"], outline=PAL["outline"], width=max(1, int(ctx.L(0.5))))
    wrist = (low.tip[0] - math.cos(math.radians(low.angle)) * 3.2, low.tip[1] - math.sin(math.radians(low.angle)) * 3.2)
    _draw_arm_cuff(ctx, wrist, low.angle, 4.4, 3.5, PAL["green_dark"])
    cuff_node = ctx.cw((wrist[0], wrist[1]))
    _draw_square(ctx.draw, cuff_node[0], cuff_node[1], ctx.L(2.7), PAL["green_hi"])
    _draw_fist(ctx, (low.tip[0] + math.cos(math.radians(low.angle)) * 2.5, low.tip[1] + math.sin(math.radians(low.angle)) * 2.5), low.angle - 2.0, scale=1.0)


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


_NEAR_X, _NEAR_LIFT, _NEAR_PITCH = _stride(0.0, 46.0)
_FAR_X, _FAR_LIFT, _FAR_PITCH = _stride(0.5, -46.0)
_DEFAULT_FOOT_X = {"near": 46.0, "far": -46.0}

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
        "near_arm_u": lambda t: 0.0 + 0.5 * math.sin(_TAU * t),
        "near_arm_l": lambda t: -10.0 + 0.5 * math.sin(_TAU * (t - 0.08)),
        "far_arm_u": lambda t: -15.0 - 0.5 * math.sin(_TAU * t),
        "far_arm_l": lambda t: -10.0 + 0.5 * math.sin(_TAU * (t - 0.05)),
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
        "near_arm_u": lambda t: 8.0 + 10.0 * math.cos(_TAU * t),
        "near_arm_l": lambda t: -24.0 - 6.0 * math.cos(_TAU * t),
        "far_arm_u": lambda t: -4.0 - 10.0 * math.cos(_TAU * t),
        "far_arm_l": lambda t: -18.0 + 6.0 * math.cos(_TAU * t),
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
        "near_arm_u": Channel((0, 0), (0.16, -58), (0.32, -84), (0.52, 10, "out"), (0.78, 8), (1, 0)),
        "near_arm_l": Channel((0, -10), (0.16, -46), (0.32, -58), (0.52, 2, "out"), (0.78, -12), (1, -10)),
        "far_arm_u": Channel((0, -15), (0.20, 10), (0.50, -8, "out"), (1, -15)),
        "far_arm_l": Channel((0, -10), (0.20, -8), (0.50, -20, "out"), (1, -10)),
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
        "near_arm_u": lambda t: -60.0 - 5.0 * math.sin(_TAU * t),
        "near_arm_l": lambda t: 0.0 + 5.0 * math.sin(_TAU * (t - 0.04)),
        "far_arm_u": lambda t: 60.0 + 5.0 * math.sin(_TAU * t),
        "far_arm_l": lambda t: -24.0 - 5.0 * math.sin(_TAU * (t - 0.04)),
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


_LIFE_SEED = [
    [1, 1, 0, 0],
    [1, 0, 0, 0],
    [0, 0, 0, 1],
    [0, 0, 1, 1],
]


def _life_step(board: List[List[int]]) -> List[List[int]]:
    h = len(board)
    w = len(board[0]) if h else 0
    nxt = [[0 for _ in range(w)] for _ in range(h)]
    for y in range(h):
        for x in range(w):
            n = 0
            for yy in range(max(0, y - 1), min(h, y + 2)):
                for xx in range(max(0, x - 1), min(w, x + 2)):
                    if xx == x and yy == y:
                        continue
                    n += board[yy][xx]
            if board[y][x]:
                nxt[y][x] = 1 if n in (2, 3) else 0
            else:
                nxt[y][x] = 1 if n == 3 else 0
    return nxt


def _life_sequence(max_steps: int = 32) -> List[List[List[int]]]:
    seen = set()
    seq = []
    board = [row[:] for row in _LIFE_SEED]
    for _ in range(max_steps):
        key = tuple(tuple(r) for r in board)
        if key in seen:
            break
        seen.add(key)
        seq.append([row[:] for row in board])
        board = _life_step(board)
    return seq or [[row[:] for row in _LIFE_SEED]]


_LIFE_SEQUENCE = _life_sequence()
_ANIM_FRAME_OFFSETS = {}
_acc = 0
for _anim_name, _nframes, _ms in ROWS:
    _ANIM_FRAME_OFFSETS[_anim_name] = _acc
    _acc += _nframes


def _life_cells_for_frame(animation: str, frame_idx: int) -> List[List[int]]:
    step = (_ANIM_FRAME_OFFSETS.get(animation, 0) + frame_idx) % len(_LIFE_SEQUENCE)
    return [row[:] for row in _LIFE_SEQUENCE[step]]


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
    params = dict(params)
    params["animation"] = animation
    params["frame_idx"] = frame_idx
    params["life_cells"] = _life_cells_for_frame(animation, frame_idx)
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
