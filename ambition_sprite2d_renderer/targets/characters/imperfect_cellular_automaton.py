"""Imperfect Cellular Automaton — procedural skeletal character target.

This character is not a damaged copy of the Perfect Cellular Automaton.  Its
visual rule is asymmetry: one side still tries to preserve a clean cellular
lattice while the other continuously mutates into a violet fault-growth.  The
body, face, tail, attack hand, and animation timing all expose that disagreement.
The chest runs a deliberately faulty cellular automaton whose state changes in
every rendered frame.

The entire sprite remains Python-authored through the repository's Skeleton /
Clip / Rig pipeline.  No generated image source is required.

Publish:

    PYTHONPATH=tools/ambition_sprite2d_renderer \
      python -m ambition_sprite2d_renderer publish imperfect_cellular_automaton
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Mapping, Tuple

from PIL import Image, ImageColor, ImageDraw

from ...authoring import rigdoc
from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.rig import clamp, lerp, smoothstep, vec
from ...authoring.skeleton import (
    BoneWorld,
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
from ambition_sprite2d_renderer.core.draw import blending_draw
from ...authoring.sheet_build import build_sheet, write_canonical
from . import _solo_shape_rig as SR

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
        "traits": ["bio_android", "cellular_automaton", "aerial_melee", "mutable"],
    },
    "visual": {
        "default_pose": "idle",
        "facing_policy": "three_quarter_front_right",
    },
    "provenance": {
        "variant_family": "imperfect_cellular_automaton",
        "variant_id": "gpt_5_6_zorder_polish_2026_07_15",
        "lineage": [
            {
                "revision_id": "legacy_unattributed",
                "creator_kind": "unknown",
                "creator": "unattributed",
                "contribution": "predecessor_design",
                "derived_from": "player_robot_fable",
                "certainty": "partial",
            },
            {
                "revision_id": "gpt_5_6_redesign_2026_07_15",
                "creator_kind": "model",
                "creator": "gpt-5.6-thinking",
                "contribution": "complete_visual_redesign_and_animation_polish",
                "parent_revision_id": "legacy_unattributed",
                "date": "2026-07-15",
            },
            {
                "revision_id": "gpt_5_6_zorder_polish_2026_07_15",
                "creator_kind": "model",
                "creator": "gpt-5.6-thinking",
                "contribution": "arm_visibility_zorder_contract_and_shadow_removal",
                "parent_revision_id": "gpt_5_6_redesign_2026_07_15",
                "date": "2026-07-15",
            },
        ],
    },
    "tags": ["aerial", "enemy", "custom", "cellular", "mutable"],
}


ACTOR_METADATA.update(
    {
        "authoring_description": (
            """
            Parody of Imperfect Cell from DBZ. Combined with CS fun.

            "The Imperfect Cellular Automaton personifies cellular-automaton mathematics as a "
            "character who sometimes violates its own local rule. It is a philosophical foil to the "
            "Perfect Cellular Automaton: asymmetry, mutation, accumulated exceptions, and emergent "
            "evolution are treated as identity rather than damage."
            """
        ),
        "gameplay_description": (
            "Use as an adaptive enemy, unstable ally, mutation mechanic, or playable rule-breaker. "
            "Its state should visibly propagate across cells while occasional exceptions create "
            "abilities or futures that a flawless deterministic counterpart cannot reach."
        ),
    }
)
ACTOR_METADATA.setdefault("dialogue_hints", {}).setdefault(
    "barks",
    [
        'I follow my rule MOSTLY.',
        'The exceptions become the new rule.',
        "I'm the written-down noise.",
    ],
)


def _rgba(hex_color: str, alpha: int = 255) -> Color:
    r, g, b = ImageColor.getrgb(hex_color)
    return (r, g, b, alpha)


PAL: Dict[str, Color] = {
    "outline": _rgba("#08100F"),
    "void": _rgba("#0B1517"),
    "void_hi": _rgba("#17262A"),
    "emerald_dark": _rgba("#0D3B31"),
    "emerald": _rgba("#137A5A"),
    "emerald_hi": _rgba("#42C47E"),
    "acid": _rgba("#B6F34A"),
    "acid_white": _rgba("#E8FFAF"),
    "ceramic": _rgba("#EFE8CF"),
    "ceramic_shadow": _rgba("#C9C1A6"),
    "ceramic_hi": _rgba("#FFF9E5"),
    "violet_dark": _rgba("#352253"),
    "violet": _rgba("#7046A8"),
    "violet_hi": _rgba("#B66CE3"),
    "magenta": _rgba("#F05CB8"),
    "cyan": _rgba("#54D8E8"),
}


# ---- Skeleton -----------------------------------------------------------------


def _build_skeleton() -> Skeleton:
    sk = Skeleton()
    sk.bone("pelvis", offset=(0.0, -78.0))
    sk.bone("torso", parent="pelvis", offset=(4.0, -43.0))
    sk.bone("head", parent="torso", offset=(5.0, -47.0))

    sk.bone("tail_a", parent="pelvis", offset=(-18.0, 7.0), length=37.0, rest_angle=156.0)
    sk.bone("tail_b", parent="tail_a", offset=(37.0, 0.0), length=31.0, rest_angle=12.0)
    sk.bone("tail_c", parent="tail_b", offset=(31.0, 0.0), length=24.0, rest_angle=18.0)

    sk.bone("far_arm_u", parent="torso", offset=(-28.0, -18.0), length=ARM_U, rest_angle=105.0)
    sk.bone("far_arm_l", parent="far_arm_u", offset=(ARM_U, 0.0), length=ARM_L, rest_angle=-4.0)
    sk.bone("near_arm_u", parent="torso", offset=(32.0, -15.0), length=ARM_U + 2.0, rest_angle=72.0)
    sk.bone("near_arm_l", parent="near_arm_u", offset=(ARM_U + 2.0, 0.0), length=ARM_L + 3.0, rest_angle=-4.0)

    sk.bone("far_leg_u", parent="pelvis", offset=(-15.0, 3.0), length=LEG_U, rest_angle=96.0)
    sk.bone("far_leg_l", parent="far_leg_u", offset=(LEG_U, 0.0), length=LEG_L, rest_angle=-2.0)
    sk.bone("far_foot", parent="far_leg_l", offset=(LEG_L, 0.0), length=20.0, rest_angle=-94.0)
    sk.bone("near_leg_u", parent="pelvis", offset=(17.0, 3.0), length=LEG_U + 2.0, rest_angle=84.0)
    sk.bone("near_leg_l", parent="near_leg_u", offset=(LEG_U + 2.0, 0.0), length=LEG_L + 1.0, rest_angle=2.0)
    sk.bone("near_foot", parent="near_leg_l", offset=(LEG_L + 1.0, 0.0), length=22.0, rest_angle=-86.0)
    return sk


_SKEL = _build_skeleton()


# ---- Drawing helpers -----------------------------------------------------------


def _local_poly(ctx: PartCtx, pts, fill, outline=True, ow=OUTLINE_W, radius=0.0, steps=8):
    poly = ctx.pts(pts)
    if radius:
        poly = rounded_polygon(poly, radius=ctx.L(radius), steps=steps)
    draw_polygon(ctx.draw, poly, fill, PAL["outline"] if outline else None, ctx.L(ow))


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


# ---- Part painters -------------------------------------------------------------
#
# Each rig part places PIECES (``_solo_shape_rig``): a rigid group is painted
# once in its bone's own frame (a stand-in bone at rest on a small canvas) and
# turned into place by the posed bone, so a part flipbook stores it once. A
# cell (an axis-aligned square) rides its point unturned, as it was drawn.


def _rest_ctx(d, origin: Point, length: float, params: Mapping) -> PartCtx:
    """A paint context whose bone lies at rest at ``origin`` (design units) on
    the piece canvas ``d`` paints."""
    return PartCtx(d._img, d, BoneWorld(origin, 0.0, length), {}, SS, params)


def _piece(key, extent, paint):
    return SR.local_piece(key, extent, paint, SS)


def _on_bone(ctx: PartCtx, part, bone: BoneWorld, name: str) -> None:
    SR.place(ctx.img, part, ctx.cw(bone.origin), bone.angle, name)


def _draw_cell(ctx: PartCtx, local: Point, half: float, fill: Color, *, outline: Color | None = None) -> None:
    cx, cy = ctx.pt(local)
    rr = ctx.L(half)
    ctx.draw.rectangle(
        (cx - rr, cy - rr, cx + rr, cy + rr),
        fill=fill,
        outline=outline,
        width=max(1, int(ctx.L(0.55))) if outline is not None else 1,
    )


def _place_cell(ctx: PartCtx, at_canvas: Point, half: float, fill: Color, outline: Color | None, name: str) -> None:
    """A state cell as a piece, its centre at canvas pixel ``at_canvas``."""
    r = half + 1.5
    part = _piece(("ica_cell", half, fill, outline), (r, r, r, r), lambda d, o: _draw_cell(_rest_ctx(d, o, 0.0, {}), (0.0, 0.0), half, fill, outline=outline))
    SR.place(ctx.img, part, at_canvas, 0.0, name)


def _draw_node(ctx: PartCtx, center: Point, radius: float, fill: Color) -> None:
    cx, cy = ctx.cw(center)
    rr = ctx.L(radius)
    ctx.draw.ellipse(
        (cx - rr, cy - rr, cx + rr, cy + rr),
        fill=fill,
        outline=PAL["outline"],
        width=max(1, int(ctx.L(0.7))),
    )


def _draw_tapered_prong(
    ctx: PartCtx,
    origin: Point,
    angle: float,
    length: float,
    base_half: float,
    fill: Color,
) -> None:
    tx, ty = vec(length, angle)
    nx, ny = vec(base_half, angle + 90.0)
    pts = [
        (origin[0] - nx, origin[1] - ny),
        (origin[0] + nx, origin[1] + ny),
        (origin[0] + tx, origin[1] + ty),
    ]
    draw_polygon(
        ctx.draw,
        rounded_polygon([ctx.cw(p) for p in pts], radius=ctx.L(0.9), steps=4),
        fill,
        PAL["outline"],
        ctx.L(0.75),
    )


TAIL_CHAIN = (
    ("tail_a", 9.0, 7.4, "emerald_dark", "acid"),
    ("tail_b", 7.7, 6.0, "emerald", "acid"),
    ("tail_c", 6.2, 3.8, "violet", "magenta"),
)


def _tail_chain_painter(ctx: PartCtx) -> None:
    for idx, (bone, r0, r1, fill, node) in enumerate(TAIL_CHAIN):
        bw = ctx.world[bone]

        def paint(d, o, idx=idx, length=bw.length, r0=r0, r1=r1, fill=fill, node=node) -> None:
            c = _rest_ctx(d, o, length, {})
            a, b = o, (o[0] + length, o[1])
            _draw_segment_shape(c, a, b, r0, r1, PAL[fill], radius=2.8)
            # Mechanical cell seams make the tail read as a linked computation,
            # rather than as an organic tentacle.
            for u in (0.28, 0.60):
                _draw_node(c, (lerp(a[0], b[0], u), o[1]), 3.1 - idx * 0.35, PAL[node])

        r = r0 + 3.0
        _on_bone(ctx, _piece(("ica_tail", bone, bw.length), (r, r, bw.length + r, r), paint), bw, bone)

    # Broken output fork: the last state has no single successor.
    wc = ctx.world["tail_c"]

    def fork(d, o) -> None:
        c = _rest_ctx(d, o, 0.0, {})
        _draw_tapered_prong(c, o, -24.0, 11.0, 3.2, PAL["violet_hi"])
        _draw_tapered_prong(c, o, 13.0, 13.0, 3.0, PAL["acid"])
        _draw_tapered_prong(c, o, 42.0, 8.0, 2.4, PAL["magenta"])

    SR.place(ctx.img, _piece(("ica_tail_fork",), (5.0, 9.0, 16.0, 16.0), fork), ctx.cw(wc.tip), wc.angle, "tail_fork")

    tip = wc.tip
    frame = int(ctx.params.get("frame_idx", 0))
    for idx, (ox, oy, fill) in enumerate(((8, -14, PAL["acid"]), (20, 8, PAL["magenta"]))):
        wobble = 2.2 * math.sin((frame + idx) * 1.7)
        _place_cell(ctx, ctx.pt((tip[0] - wc.origin[0] + ox, tip[1] - wc.origin[1] + oy + wobble)), 2.0, fill, None, f"tail_cell{idx}")


def _paint_body_shell(ctx: PartCtx, shell_open: float) -> None:
    """Back plates, vanes, torso shell and chest (torso frame)."""
    # Back plates. The ordered half is compact; the mutating half fans outward.
    ordered_back = [(-35, -31), (-52, -13), (-49, 18), (-31, 46), (-18, 39), (-15, -20)]
    fault_back = [(27, -28), (49 + 8 * shell_open, -5), (47 + 12 * shell_open, 24), (30, 50), (13, 40), (13, -22)]
    _local_poly(ctx, ordered_back, PAL["emerald_dark"], ow=1.15, radius=4.5)
    _local_poly(ctx, fault_back, PAL["violet_dark"], ow=1.15, radius=3.4)

    if shell_open > 0.05:
        # Hover vanes reveal that the two body halves do not agree on symmetry.
        vane_l = [(-38, -8), (-70 - 6 * shell_open, -23), (-53, 10)]
        vane_r1 = [(35, -11), (72 + 8 * shell_open, -31), (50, 4)]
        vane_r2 = [(37, 13), (70 + 4 * shell_open, 25), (48, 29)]
        _local_poly(ctx, vane_l, PAL["emerald"], ow=0.9, radius=1.2)
        _local_poly(ctx, vane_r1, PAL["violet"], ow=0.9, radius=1.2)
        _local_poly(ctx, vane_r2, PAL["magenta"], ow=0.8, radius=1.0)

    torso = [(-25, -38), (13, -42), (31, -31), (37, -3), (30, 31), (15, 58), (-2, 69), (-20, 55), (-33, 23), (-36, -11)]
    _local_poly(ctx, torso, PAL["emerald"], ow=1.45, radius=7.0)

    # Corrupted overlay tears diagonally across the otherwise clean shell.
    fault_overlay = [(4, -38), (20, -38), (32, -26), (37, -3), (31, 20), (17, 8), (14, -10)]
    _local_poly(ctx, fault_overlay, PAL["violet"], ow=0.75, radius=2.0)
    crack = [ctx.pt((4, -31)), ctx.pt((14, -17)), ctx.pt((8, -1)), ctx.pt((21, 13)), ctx.pt((15, 30))]
    ctx.draw.line(crack, fill=PAL["outline"], width=max(1, int(ctx.L(1.0))), joint="curve")

    # Shoulder armor belongs to the arm painters. Keeping the socket and limb
    # in one z-layer prevents a pose from leaving a visible shoulder attached
    # to an arm that was accidentally painted behind the torso.

    chest = [(-19, -21), (9, -24), (21, -13), (20, 19), (12, 44), (-2, 55), (-16, 42), (-24, 16), (-25, -9)]
    _local_poly(ctx, chest, PAL["ceramic"], ow=1.0, radius=6.0)


def _paint_life_grid(ctx: PartCtx, life_cells, fault_cell, glitch: float) -> None:
    grid_x, grid_y = -16.0, -12.0
    step = 7.3
    for gy in range(5):
        for gx in range(5):
            live = bool(life_cells[gy][gx])
            local = (grid_x + gx * step, grid_y + gy * step)
            if (gx, gy) == fault_cell:
                fill = PAL["magenta"]
                half = 2.55 + 0.6 * glitch
            elif live:
                fill = PAL["acid"] if (gx + gy) % 3 else PAL["cyan"]
                half = 2.25
            else:
                fill = PAL["ceramic_shadow"]
                half = 1.75
            _draw_cell(ctx, local, half, fill)


def _paint_body_waist(ctx: PartCtx) -> None:
    # A black register strip records cells that escaped the main grid.
    register = [(6, 19), (18, 18), (20, 47), (8, 49)]
    _local_poly(ctx, register, PAL["void"], ow=0.75, radius=1.8)
    for idx, fill in enumerate((PAL["acid"], PAL["violet_hi"], PAL["magenta"])):
        _draw_cell(ctx, (12.5 + (idx % 2) * 5.5, 25 + idx * 8.0), 1.9, fill)

    waist = [(-27, 43), (-7, 47), (2, 60), (-8, 74), (-27, 65), (-35, 53)]
    _local_poly(ctx, waist, PAL["emerald_dark"], ow=1.0, radius=4.0)
    fault_waist = [(0, 48), (25, 40), (34, 54), (20, 72), (2, 61)]
    _local_poly(ctx, fault_waist, PAL["violet_dark"], ow=1.0, radius=3.0)
    _draw_cell(ctx, (24, 54), 4.2, PAL["magenta"], outline=PAL["outline"])


BODY_EXTENT = (84.0, 48.0, 86.0, 80.0)


def _body_painter(ctx: PartCtx) -> None:
    p = ctx.params
    bw = ctx.bw
    hover = clamp(float(p.get("hover", 0.0)), 0.0, 1.0)
    shell_open = round(clamp(float(p.get("shell_open", hover)), 0.0, 1.0), 2)
    glitch = clamp(float(p.get("glitch_pulse", 0.0)), 0.0, 1.0)

    shell = _piece(("ica_body_shell", shell_open), BODY_EXTENT, lambda d, o: _paint_body_shell(_rest_ctx(d, o, bw.length, p), shell_open))
    _on_bone(ctx, shell, bw, "body_shell")

    # The live grid changes every frame (it IS the automaton): one small piece.
    life_cells = p.get("life_cells", [[0] * 5 for _ in range(5)])
    fault_cell = tuple(p.get("fault_cell", (-1, -1)))
    cells = tuple(tuple(int(bool(v)) for v in row) for row in life_cells)
    grid = _piece(("ica_life_grid", cells, fault_cell, glitch), BODY_EXTENT, lambda d, o: _paint_life_grid(_rest_ctx(d, o, bw.length, p), cells, fault_cell, glitch))
    _on_bone(ctx, grid, bw, "life_grid")

    waist = _piece(("ica_body_waist",), BODY_EXTENT, lambda d, o: _paint_body_waist(_rest_ctx(d, o, bw.length, p)))
    _on_bone(ctx, waist, bw, "body_waist")

    # Detached state cells. They move with the body but refuse to join it.
    frame = int(p.get("frame_idx", 0))
    animation = str(p.get("animation", "idle"))
    orbit = 1.0 + 0.45 * hover
    particles = [
        (48 + 3 * math.sin(frame * 1.3), -42 + 4 * math.cos(frame * 0.9), PAL["acid"]),
        (57 + 5 * math.cos(frame * 1.1), 8 + 5 * math.sin(frame * 0.8), PAL["violet_hi"]),
        (42 + 4 * math.sin(frame * 0.7), 43 + 3 * math.cos(frame * 1.4), PAL["magenta"]),
    ]
    if animation == "slash":
        particles.append((64 + 10 * glitch, -2, PAL["cyan"]))
    for idx, (x, y, fill) in enumerate(particles):
        _place_cell(ctx, ctx.pt((x * orbit, y)), 2.6 - idx * 0.25, fill, PAL["outline"], f"particle{idx}")


def _paint_head(ctx: PartCtx, blink: bool, squint: float, glitch: float) -> None:
    # Back antenna: regular and measured.
    mast_a = ctx.pt((-14, -18))
    mast_b = ctx.pt((-25, -53))
    ctx.draw.line((mast_a, mast_b), fill=PAL["outline"], width=max(1, int(ctx.L(4.2))))
    ctx.draw.line((mast_a, mast_b), fill=PAL["emerald_hi"], width=max(1, int(ctx.L(2.2))))
    for local in ((-18, -31), (-22, -43)):
        _draw_cell(ctx, local, 3.0, PAL["acid"], outline=PAL["outline"])
    _draw_cell(ctx, (-26, -55), 4.1, PAL["acid_white"], outline=PAL["outline"])

    # Front antenna: a broken, branching successor.
    _local_poly(ctx, [(10, -20), (25, -49), (24, -13)], PAL["violet"], ow=0.9, radius=1.0)
    _local_poly(ctx, [(22, -35), (39, -48), (28, -27)], PAL["magenta"], ow=0.75, radius=0.8)
    _draw_cell(ctx, (39, -49), 3.0, PAL["magenta"], outline=PAL["outline"])

    helmet = [(-26, -22), (4, -31), (28, -20), (34, -1), (28, 18), (6, 25), (-20, 18), (-31, 3)]
    _local_poly(ctx, helmet, PAL["void"], ow=1.45, radius=6.5)
    ordered_cap = [(-24, -18), (-4, -27), (-5, 10), (-23, 14), (-28, 1)]
    _local_poly(ctx, ordered_cap, PAL["emerald_dark"], ow=0.65, radius=3.0)
    fault_cap = [(4, -27), (27, -18), (32, -1), (25, 9), (9, 2)]
    _local_poly(ctx, fault_cap, PAL["violet_dark"], ow=0.65, radius=2.0)

    face = [(-15, -8), (17, -10), (25, -1), (23, 20), (10, 36), (-7, 34), (-20, 19), (-22, 1)]
    _local_poly(ctx, face, PAL["ceramic"], ow=1.0, radius=5.5)
    face_hi = [(-13, -5), (2, -7), (0, 29), (-9, 29), (-17, 17), (-18, 2)]
    _local_poly(ctx, face_hi, PAL["ceramic_hi"], outline=False, radius=3.0)

    visor = [(-13, -2), (18, -4), (23, 2), (21, 12), (-12, 14), (-17, 8)]
    _local_poly(ctx, visor, PAL["void_hi"], ow=0.65, radius=2.8)

    eye_h = 0.8 if blink else max(1.4, 4.0 * (1.0 - 0.55 * squint))
    # Ordered eye is a stable rectangular state.
    c = ctx.pt((-4, 5))
    ctx.draw.rounded_rectangle(
        (c[0] - ctx.L(5.5), c[1] - ctx.L(eye_h), c[0] + ctx.L(5.5), c[1] + ctx.L(eye_h)),
        radius=max(1, int(ctx.L(1.3))), fill=PAL["acid"],
    )
    # Fault eye is two cells that periodically disagree on where the face is.
    shift = 3.0 * glitch
    for ex, ey, fill in ((10 + shift, 2, PAL["magenta"]), (15 - shift, 8, PAL["violet_hi"])):
        _draw_cell(ctx, (ex, ey), eye_h * 0.85 + 1.2, fill)

    jaw = [(-8, 19), (15, 17), (16, 29), (6, 38), (-5, 33)]
    _local_poly(ctx, jaw, PAL["ceramic_shadow"], ow=0.65, radius=2.5)
    mouth_a, mouth_b = ctx.pt((-1, 27)), ctx.pt((10, 26))
    ctx.draw.line((mouth_a, mouth_b), fill=PAL["outline"], width=max(1, int(ctx.L(0.8))))
    _draw_cell(ctx, (5, 34), 2.6, PAL["void"], outline=PAL["outline"])

    # A one-frame echo makes the glitch read without smearing the entire sprite.
    if glitch > 0.5:
        echo = [ctx.pt((28, -11)), ctx.pt((35, -7)), ctx.pt((34, 11)), ctx.pt((28, 15))]
        composite_polygon(ctx.img, echo, (*PAL["cyan"][:3], 105))


def _head_painter(ctx: PartCtx) -> None:
    """The head, one piece per expression (blink, squint step, glitch)."""
    p = ctx.params
    blink = float(p.get("blink", 0.0)) > 0.5
    squint = SR.q(clamp(float(p.get("eye_squint", 0.0)), 0.0, 1.0), 0.1)
    glitch = clamp(float(p.get("glitch_pulse", 0.0)), 0.0, 1.0)
    bw = ctx.bw
    head = _piece(("ica_head", blink, squint, glitch), (36.0, 62.0, 46.0, 42.0), lambda d, o: _paint_head(_rest_ctx(d, o, bw.length, p), blink, squint, glitch))
    _on_bone(ctx, head, bw, "head")


def _shoulder_piece(key, poly_offsets, fill, radius: float, node_r: float, node_fill):
    def paint(d, o) -> None:
        c = _rest_ctx(d, o, 0.0, {})
        poly = [(o[0] + x, o[1] + y) for x, y in poly_offsets]
        draw_polygon(c.draw, rounded_polygon([c.cw(q) for q in poly], radius=c.L(radius), steps=6), fill, PAL["outline"], c.L(0.95))
        _draw_node(c, o, node_r, node_fill)

    return _piece(key, (16.0, 14.0, 16.0, 14.0), paint)


def _far_arm_painter(ctx: PartCtx) -> None:
    """The character-left arm as one foreground assembly: shoulder plate
    (unturned, as drawn), upper arm, and forearm with elbow, cells, palm and
    fingers riding it."""
    upper, lower = ctx.world["far_arm_u"], ctx.world["far_arm_l"]

    # Broad asymmetric shoulder plate. It deliberately projects left of the
    # torso, preserving a readable arm root even in foreshortened poses.
    plate = ((-14.0, -9.0), (5.0, -8.0), (10.0, 1.0), (4.0, 10.0), (-13.0, 8.0))
    SR.place(ctx.img, _shoulder_piece(("ica_far_shoulder",), plate, PAL["emerald_hi"], 3.2, 4.1, PAL["acid"]), ctx.cw(upper.origin), 0.0, "far_shoulder")

    def upper_paint(d, o) -> None:
        c = _rest_ctx(d, o, upper.length, {})
        _draw_segment_shape(c, o, (o[0] + upper.length, o[1]), 9.0, 7.0, PAL["emerald_dark"], radius=2.7)

    _on_bone(ctx, _piece(("ica_far_upper", upper.length), (11.0, 11.0, upper.length + 11.0, 11.0), upper_paint), upper, "far_upper_arm")

    def lower_paint(d, o) -> None:
        c = _rest_ctx(d, o, lower.length, {})
        palm = (o[0] + lower.length, o[1])
        _draw_segment_shape(c, o, palm, 7.5, 5.4, PAL["emerald"], radius=2.2)
        _draw_node(c, o, 5.1, PAL["acid"])
        # A bright edge and two state cells keep the arm from collapsing into the
        # dark torso palette at final sprite scale.
        for frac, radius, fill in ((0.34, 2.5, PAL["emerald_hi"]), (0.70, 2.35, PAL["acid"])):
            _draw_node(c, (o[0] + lower.length * frac, o[1]), radius, fill)
        hand_poly = [(palm[0] - 4.0, palm[1] - 6.0), (palm[0] + 8.0, palm[1] - 5.0), (palm[0] + 9.0, palm[1] + 5.0), (palm[0] - 4.0, palm[1] + 6.0)]
        draw_polygon(c.draw, rounded_polygon([c.cw(q) for q in hand_poly], radius=c.L(2.0), steps=6), PAL["ceramic"], PAL["outline"], c.L(0.85))
        _draw_node(c, (palm[0] + 3.0, palm[1]), 2.2, PAL["acid"])
        # Two compact fingers are more legible than the previous detached square.
        for offset, delta, fill in ((-2.6, -8.0, PAL["acid_white"]), (2.6, 7.0, PAL["emerald_hi"])):
            _draw_tapered_prong(c, (palm[0] + 7.0, palm[1] + offset), delta, 8.0, 2.0, fill)

    _on_bone(ctx, _piece(("ica_far_lower", lower.length), (9.0, 10.0, lower.length + 18.0, 10.0), lower_paint), lower, "far_forearm")


def _near_arm_painter(ctx: PartCtx) -> None:
    u, low = ctx.world["near_arm_u"], ctx.world["near_arm_l"]

    plate = ((-8.0, -10.0), (10.0, -8.0), (14.0, 4.0), (4.0, 12.0), (-9.0, 7.0))
    SR.place(ctx.img, _shoulder_piece(("ica_near_shoulder",), plate, PAL["violet_hi"], 3.0, 5.0, PAL["magenta"]), ctx.cw(u.origin), 0.0, "near_shoulder")

    def upper_paint(d, o) -> None:
        c = _rest_ctx(d, o, u.length, {})
        _draw_segment_shape(c, o, (o[0] + u.length, o[1]), 9.2, 7.0, PAL["violet"], radius=2.6)

    _on_bone(ctx, _piece(("ica_near_upper", u.length), (11.0, 11.0, u.length + 11.0, 11.0), upper_paint), u, "near_upper_arm")

    extension = SR.q(clamp(float(ctx.params.get("claw_extension", 0.0)), 0.0, 1.0), 0.05)
    claw_open = SR.q(float(ctx.params.get("claw_open", 0.0)), 0.05)

    def lower_paint(d, o) -> None:
        c = _rest_ctx(d, o, low.length, {})
        palm = (o[0] + low.length, o[1])
        _draw_segment_shape(c, o, palm, 8.0, 5.8, PAL["violet_dark"], radius=2.0)
        _draw_node(c, o, 4.8, PAL["acid"])
        # Mismatched armor cells crawl down the weapon arm.
        for ufrac, fill in ((0.25, PAL["violet_hi"]), (0.56, PAL["magenta"]), (0.80, PAL["acid"])):
            _draw_node(c, (o[0] + low.length * ufrac, o[1]), 2.4, fill)
        hand_poly = [(palm[0] - 5, palm[1] - 7), (palm[0] + 8, palm[1] - 7), (palm[0] + 10, palm[1] + 7), (palm[0] - 5, palm[1] + 7)]
        draw_polygon(c.draw, rounded_polygon([c.cw(q) for q in hand_poly], radius=c.L(2.0)), PAL["void"], PAL["outline"], c.L(0.9))
        spread = 11.0 + 8.0 * claw_open
        base_len = 10.0 + extension * 18.0
        for idx, (delta, fill) in enumerate(((-spread, PAL["violet_hi"]), (0.0, PAL["acid"]), (spread, PAL["magenta"]))):
            _draw_tapered_prong(c, (palm[0] + 6, palm[1] + (idx - 1) * 3.2), delta, base_len + idx * 2.0, 3.3, fill)

    reach = 6.0 + 10.0 + 18.0 + 4.0 + 4.0
    _on_bone(ctx, _piece(("ica_near_lower", low.length, extension, claw_open), (9.0, reach, low.length + reach, reach), lower_paint), low, "near_forearm")


def _leg_painter(side: str):
    upper_key = f"{side}_leg_u"
    lower_key = f"{side}_leg_l"
    near = side == "near"

    def fn(ctx: PartCtx) -> None:
        u, low = ctx.world[upper_key], ctx.world[lower_key]
        upper_fill = PAL["violet"] if near else PAL["emerald_dark"]
        lower_fill = PAL["violet_dark"] if near else PAL["void_hi"]

        def upper_paint(d, o) -> None:
            c = _rest_ctx(d, o, u.length, {})
            _draw_segment_shape(c, o, (o[0] + u.length, o[1]), 9.0 if near else 7.8, 7.0 if near else 6.0, upper_fill, radius=2.5)

        def lower_paint(d, o) -> None:
            c = _rest_ctx(d, o, low.length, {})
            _draw_segment_shape(c, o, (o[0] + low.length, o[1]), 7.7 if near else 6.8, 5.5, lower_fill, radius=2.2)
            _draw_node(c, o, 6.8 if near else 5.8, PAL["magenta"] if near else PAL["acid"])
            if near:
                _draw_node(c, (o[0] + low.length * 0.55, o[1]), 2.7, PAL["violet_hi"])

        _on_bone(ctx, _piece(("ica_leg_upper", side, u.length), (11.0, 11.0, u.length + 11.0, 11.0), upper_paint), u, f"{side}_thigh")
        _on_bone(ctx, _piece(("ica_leg_lower", side, low.length), (9.0, 9.0, low.length + 9.0, 9.0), lower_paint), low, f"{side}_shin")

    return fn


def _foot_painter(side: str):
    near = side == "near"

    def fn(ctx: PartCtx) -> None:
        bw = ctx.bw

        def paint(d, o) -> None:
            c = _rest_ctx(d, o, bw.length, {})
            pts = [(-5.5, -4.0), (6.5, -5.0), (19.0, -1.0), (22.0, 5.0), (16.0, 9.0), (-5.0, 8.0)]
            fill = PAL["violet_dark"] if near else PAL["emerald_dark"]
            draw_polygon(c.draw, rounded_polygon(c.pts(pts), radius=c.L(1.8)), fill, PAL["outline"], c.L(0.9))
            toe = [(7, -2), (18, 0), (19, 5), (8, 5)]
            draw_polygon(c.draw, rounded_polygon(c.pts(toe), radius=c.L(1.2)), PAL["ceramic"], PAL["outline"], c.L(0.65))
            _draw_cell(c, (1.0, 1.0), 3.1, PAL["magenta"] if near else PAL["acid"], outline=PAL["outline"])
            if near:
                _draw_tapered_prong(c, c.bw.tip, -15.0, 8.0, 2.6, PAL["violet_hi"])

        _on_bone(ctx, _piece(("ica_foot", side, bw.length), (8.0, 8.0, max(24.0, bw.length + 10.0), 11.0), paint), bw, f"{side}_foot")

    return fn


# Named layers are an executable contract, not informal magic numbers. Arms
# intentionally occupy the two highest bands in every animation. This is a
# stylized three-quarter sprite, not a physically sorted 3D mesh: preserving
# readable hands and attack silhouettes is more important than allowing the
# torso to erase an anatomically "far" limb.
PART_Z = {
    "tail": 10,
    "far_leg": 20,
    "far_foot": 21,
    "body": 40,
    "head": 50,
    "near_leg": 60,
    "near_foot": 61,
    "far_arm": 80,
    "near_arm": 90,
}
ARM_PARTS = frozenset({"far_arm", "near_arm"})
NON_ARM_PARTS = frozenset(PART_Z) - ARM_PARTS


def _validate_part_z(part_z: Dict[str, int]) -> None:
    """Reject z-order regressions at import time and in tests."""
    missing = (ARM_PARTS | NON_ARM_PARTS) - set(part_z)
    if missing:
        raise ValueError(f"missing z-order entries: {sorted(missing)}")
    highest_non_arm = max(part_z[name] for name in NON_ARM_PARTS)
    lowest_arm = min(part_z[name] for name in ARM_PARTS)
    if lowest_arm <= highest_non_arm:
        raise ValueError(
            "arm visibility contract violated: every arm must render above "
            f"every non-arm part ({lowest_arm=} <= {highest_non_arm=})"
        )
    if part_z["near_arm"] <= part_z["far_arm"]:
        raise ValueError("near arm must resolve arm-on-arm overlaps")


def _build_rig() -> Rig:
    _validate_part_z(PART_Z)
    rig = Rig(_SKEL)
    rig.part("tail", "tail_a", PART_Z["tail"], _tail_chain_painter)
    rig.part("far_leg", "far_leg_u", PART_Z["far_leg"], _leg_painter("far"))
    rig.part("far_foot", "far_foot", PART_Z["far_foot"], _foot_painter("far"))
    rig.part("body", "torso", PART_Z["body"], _body_painter)
    rig.part("head", "head", PART_Z["head"], _head_painter)
    rig.part("near_leg", "near_leg_u", PART_Z["near_leg"], _leg_painter("near"))
    rig.part("near_foot", "near_foot", PART_Z["near_foot"], _foot_painter("near"))
    rig.part("far_arm", "far_arm_u", PART_Z["far_arm"], _far_arm_painter)
    rig.part("near_arm", "near_arm_u", PART_Z["near_arm"], _near_arm_painter)
    return rig


_RIG = _build_rig()


# ---- Clips --------------------------------------------------------------------

_TAU = math.tau


def _stride(phase_off: float, hip_off: float, duty: float = 0.58, half: float = 17.0, lift_h: float = 13.0):
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
            return lerp(-7.0, 9.0, ph / duty)
        u = (ph - duty) / (1.0 - duty)
        return lerp(9.0, -10.0, smoothstep(u))

    return x, lift, pitch


_NEAR_X, _NEAR_LIFT, _NEAR_PITCH = _stride(0.0, 43.0)
_FAR_X, _FAR_LIFT, _FAR_PITCH = _stride(0.5, -39.0)
_DEFAULT_FOOT_X = {"near": 43.0, "far": -39.0}

CLIP_IDLE = Clip(
    loop=True,
    channels={
        "root_y": lambda t: 0.9 * math.sin(_TAU * t),
        "root_x": lambda t: 0.45 * math.sin(_TAU * (t + 0.12)),
        "pelvis": lambda t: -1.0 + 1.2 * math.sin(_TAU * t),
        "torso": lambda t: 1.8 + 1.8 * math.sin(_TAU * (t - 0.05)),
        "head": lambda t: -2.0 - 1.6 * math.sin(_TAU * (t - 0.12)),
        "tail_a": lambda t: -7.0 + 5.0 * math.sin(_TAU * (t - 0.16)),
        "tail_b": lambda t: -8.0 + 8.0 * math.sin(_TAU * (t - 0.10)),
        "tail_c": lambda t: 5.0 + 11.0 * math.sin(_TAU * (t - 0.03)),
        "near_arm_u": lambda t: -5.0 + 2.0 * math.sin(_TAU * t),
        "near_arm_l": lambda t: -12.0 + 2.0 * math.sin(_TAU * (t - 0.08)),
        "far_arm_u": lambda t: 4.0 - 1.2 * math.sin(_TAU * t),
        "far_arm_l": lambda t: -8.0 + 1.5 * math.sin(_TAU * (t - 0.04)),
        "near_foot_x": _DEFAULT_FOOT_X["near"],
        "far_foot_x": _DEFAULT_FOOT_X["far"],
        "blink": Channel((0.0, 0), (0.43, 0), (0.47, 1, "linear"), (0.53, 1), (0.58, 0, "linear")),
        "eye_squint": 0.02,
        "claw_open": lambda t: 0.10 + 0.08 * math.sin(_TAU * t),
    },
)

CLIP_WALK = Clip(
    loop=True,
    channels={
        "root_y": lambda t: 2.4 * math.cos(2.0 * _TAU * t) - 0.8,
        "root_x": lambda t: 1.2 * math.sin(_TAU * t),
        "pelvis": lambda t: 3.8 * math.sin(_TAU * t),
        "torso": lambda t: 5.0 - 5.5 * math.sin(_TAU * t),
        "head": lambda t: -4.0 + 3.0 * math.sin(_TAU * (t - 0.08)),
        "tail_a": lambda t: -12.0 - 13.0 * math.sin(_TAU * t),
        "tail_b": lambda t: -10.0 - 18.0 * math.sin(_TAU * (t - 0.02)),
        "tail_c": lambda t: 7.0 + 18.0 * math.sin(_TAU * (t + 0.05)),
        "near_arm_u": lambda t: -4.0 + 22.0 * math.cos(_TAU * t),
        "near_arm_l": lambda t: -18.0 - 11.0 * math.cos(_TAU * t),
        "far_arm_u": lambda t: 5.0 - 18.0 * math.cos(_TAU * t),
        "far_arm_l": lambda t: -12.0 + 9.0 * math.cos(_TAU * t),
        "near_foot_x": _NEAR_X,
        "near_foot_lift": _NEAR_LIFT,
        "near_foot_pitch": _NEAR_PITCH,
        "far_foot_x": _FAR_X,
        "far_foot_lift": _FAR_LIFT,
        "far_foot_pitch": _FAR_PITCH,
        "eye_squint": 0.18,
        "claw_open": 0.28,
    },
)

CLIP_SLASH = Clip(
    loop=False,
    channels={
        "root_x": Channel((0, 0), (0.18, -8.0), (0.46, -20.0, "out"), (0.72, -8.0), (1, 0)),
        "root_y": Channel((0, 0), (0.18, -4.0), (0.46, -5.0, "out"), (0.72, 0), (1, 0)),
        "pelvis": Channel((0, -1), (0.18, -10), (0.46, 11, "out"), (0.75, 4), (1, -1)),
        "torso": Channel((0, 2), (0.18, -18), (0.46, 20, "out"), (0.74, 7), (1, 2)),
        "head": Channel((0, -2), (0.18, 7), (0.46, -9, "out"), (1, -2)),
        "tail_a": Channel((0, -7), (0.18, -28), (0.46, 20, "out"), (0.78, 7), (1, -7)),
        "tail_b": Channel((0, -8), (0.18, -34), (0.46, 30, "out"), (1, -8)),
        "tail_c": Channel((0, 5), (0.18, -22), (0.46, 36, "out"), (1, 5)),
        # Wind up behind the body, then rake hard through +X.
        "near_arm_u": Channel((0, -5), (0.18, 92), (0.32, 105), (0.46, -83, "out"), (0.70, -42), (1, -5)),
        "near_arm_l": Channel((0, -12), (0.18, -66), (0.32, -74), (0.46, 5, "out"), (0.70, -4), (1, -12)),
        # The emerald left arm counterbalances outside the torso instead of
        # folding across the face during the weapon-arm windup. It still sits
        # in the foreground layer, but its pose protects the facial read.
        "far_arm_u": Channel((0, 8), (0.18, 24), (0.46, 42, "out"), (0.72, 20), (1, 8)),
        "far_arm_l": Channel((0, -10), (0.18, -18), (0.46, 8, "out"), (0.72, -4), (1, -10)),
        "near_foot_x": 42.0,
        "far_foot_x": -41.0,
        "far_foot_lift": Channel((0, 0), (0.30, 0), (0.46, 5.0, "out"), (0.76, 0), (1, 0)),
        "far_foot_pitch": Channel((0, 0), (0.30, 0), (0.46, 12.0, "out"), (0.76, 0), (1, 0)),
        "eye_squint": Channel((0, 0.1), (0.18, 0.4), (0.46, 0.72), (0.78, 0.28), (1, 0.08)),
        "claw_open": Channel((0, 0.15), (0.18, 0.5), (0.32, 0.35), (0.46, 1.0, "out"), (0.72, 0.45), (1, 0.15)),
        "claw_extension": Channel((0, 0.0), (0.18, 0.2), (0.32, 0.6), (0.46, 1.0, "out"), (0.70, 0.55), (1, 0.0)),
    },
)

CLIP_FLY = Clip(
    loop=True,
    channels={
        "root_y": lambda t: -2.0 + 1.6 * math.sin(_TAU * t),
        "root_x": lambda t: 1.4 * math.sin(_TAU * (t + 0.15)),
        "pelvis": lambda t: 2.6 * math.sin(_TAU * t),
        "torso": lambda t: 7.0 + 4.0 * math.sin(_TAU * t),
        "head": lambda t: -5.0 - 2.5 * math.sin(_TAU * (t - 0.10)),
        "tail_a": lambda t: -14.0 + 12.0 * math.sin(_TAU * (t - 0.18)),
        "tail_b": lambda t: -8.0 + 19.0 * math.sin(_TAU * (t - 0.12)),
        "tail_c": lambda t: 12.0 + 17.0 * math.sin(_TAU * (t - 0.07)),
        "near_arm_u": lambda t: -52.0 - 7.0 * math.sin(_TAU * t),
        "near_arm_l": lambda t: -4.0 + 6.0 * math.sin(_TAU * (t - 0.04)),
        "far_arm_u": lambda t: 47.0 + 6.0 * math.sin(_TAU * t),
        "far_arm_l": lambda t: -18.0 - 5.0 * math.sin(_TAU * (t - 0.04)),
        "near_foot_x": 20.0,
        "far_foot_x": -18.0,
        "near_foot_lift": 29.0,
        "far_foot_lift": 25.0,
        "near_foot_pitch": 12.0,
        "far_foot_pitch": -8.0,
        "hover": 1.0,
        "shell_open": lambda t: 0.72 + 0.18 * math.sin(_TAU * t),
        "eye_squint": 0.08,
        "claw_open": 0.55,
    },
)

CLIPS: Dict[str, Clip] = {"idle": CLIP_IDLE, "walk": CLIP_WALK, "slash": CLIP_SLASH, "fly": CLIP_FLY}


_LIFE_SEED = [
    [0, 1, 0, 0, 0],
    [0, 0, 1, 1, 0],
    [1, 1, 1, 0, 0],
    [0, 0, 0, 1, 0],
    [0, 1, 0, 1, 1],
]


def _life_step(board: List[List[int]], fault_index: int) -> Tuple[List[List[int]], Tuple[int, int]]:
    h = len(board)
    w = len(board[0]) if h else 0
    nxt = [[0 for _ in range(w)] for _ in range(h)]
    for y in range(h):
        for x in range(w):
            n = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    n += board[(y + dy) % h][(x + dx) % w]
            nxt[y][x] = int(n == 3 or (board[y][x] and n == 2))

    # The machine almost follows the rule. A deterministic fault flips exactly
    # one result, giving every frame a traceable but non-perfect successor.
    fault_x = (fault_index * 3 + 1) % w
    fault_y = (fault_index * 2 + fault_index // 3) % h
    nxt[fault_y][fault_x] ^= 1
    return nxt, (fault_x, fault_y)


def _life_sequence(max_steps: int = 64) -> Tuple[List[List[List[int]]], List[Tuple[int, int]]]:
    seq: List[List[List[int]]] = []
    faults: List[Tuple[int, int]] = []
    board = [row[:] for row in _LIFE_SEED]
    for step in range(max_steps):
        seq.append([row[:] for row in board])
        board, fault = _life_step(board, step)
        faults.append(fault)
    return seq, faults


_LIFE_SEQUENCE, _FAULT_SEQUENCE = _life_sequence()
_ANIM_FRAME_OFFSETS = {}
_acc = 0
for _anim_name, _nframes, _ms in ROWS:
    _ANIM_FRAME_OFFSETS[_anim_name] = _acc
    _acc += _nframes


def _life_state_for_frame(animation: str, frame_idx: int) -> Tuple[List[List[int]], Tuple[int, int]]:
    step = (_ANIM_FRAME_OFFSETS.get(animation, 0) + frame_idx) % len(_LIFE_SEQUENCE)
    return [row[:] for row in _LIFE_SEQUENCE[step]], _FAULT_SEQUENCE[step]


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
    draw = blending_draw(img)
    world, params = _solve(animation, t)
    params = dict(params)
    params["animation"] = animation
    params["frame_idx"] = frame_idx
    params["life_cells"], params["fault_cell"] = _life_state_for_frame(animation, frame_idx)
    params["glitch_pulse"] = 1.0 if (frame_idx + _ANIM_FRAME_OFFSETS.get(animation, 0)) % 5 == 3 else 0.0

    _RIG.draw(img, draw, world, SS, params)
    return rigdoc.downsampled_canvas(img, (FRAME_W, FRAME_H), Image.Resampling.LANCZOS)


# ---- Target hooks --------------------------------------------------------------


def _body_metrics_override(fw: int, fh: int):
    return {
        "body_pixel_bbox": {"x": int(fw * 0.12), "y": int(fh * 0.03), "w": int(fw * 0.78), "h": int(fh * 0.91)},
        "feet_pixel": {"x": fw * 0.50, "y": fh * 0.92},
        "feet_anchor_norm": {"x": 0.0, "y": round(0.5 - 0.92, 6)},
    }


def render(out_dir: Path, **opts) -> List[Path]:
    del opts
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
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
        attack_hitboxes={"slash": {"bbox": {"x": 126, "y": 48, "w": 112, "h": 128}}},
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    parts = publish_rig_flipbook(TARGET_NAME, ROWS, render_frame, outputs, frame_transform, Path(out_dir))
    return [Path(outputs[k]) for k in keys if outputs.get(k)] + list(parts.values())


def render_canonical(out_dir: Path, **opts) -> Path:
    del opts
    return write_canonical(TARGET_NAME, ROWS, render_frame, Path(out_dir), frame_size=(FRAME_W, FRAME_H))
