"""Detached mathematical VFX authored for Emmy Ethereal.

The visual rule is structural: symmetry, conservation, generators, equivalence,
and invariant objects must be visible in the geometry itself.  These sprites are
not decorative equations or generic magic particles; each one communicates a
relationship that survives the animation.
"""

from __future__ import annotations

import math
from pathlib import Path

from ._character_vfx_common import (
    Canvas,
    fade,
    make_spec,
    publish_canonical,
    publish_catalog,
    pulse,
    sheet_files,
    smooth,
    window,
)

TARGET_NAME = "noether_vfx"
SHEET_FILES = sheet_files(TARGET_NAME)
FRAME_SIZE = (144, 144)

ROWS = [
    ("symmetry_axis_snap", 9, 50),
    ("invariant_core", 12, 70),
    ("conserved_pair_exchange", 12, 66),
    ("group_orbit", 12, 68),
    ("generator_steps", 10, 54),
    ("broken_symmetry_shards", 10, 50),
    ("ether_cancel", 9, 54),
    ("equivalence_bridge", 10, 58),
    ("conservation_transfer", 12, 64),
    ("proof_complete", 11, 58),
    ("paired_trajectory", 12, 62),
    ("conserved_current", 12, 66),
]

OUTLINE = (25, 27, 38, 255)
ETHER = (126, 220, 238, 255)
ETHER_LIGHT = (218, 249, 250, 255)
VIOLET = (150, 124, 210, 255)
VIOLET_DARK = (80, 67, 126, 255)
GOLD = (239, 198, 104, 255)
CORAL = (219, 105, 102, 255)
INK_BLUE = (57, 82, 119, 255)
FIELD_DARK = (35, 45, 67, 255)


def _node(c: Canvas, point: tuple[float, float], radius: float, color, alpha: float = 1.0) -> None:
    c.ellipse(point, radius, fill=fade(color, 0.28 * alpha), outline=fade(ETHER_LIGHT, 0.84 * alpha), width=0.8)


def _axis(c: Canvas, x: float, alpha: float = 1.0) -> None:
    c.line([(x, 18), (x, 126)], fade(GOLD, 0.66 * alpha), 1.0)
    for y in range(28, 121, 16):
        c.line([(x - 3, y), (x + 3, y)], fade(GOLD, 0.42 * alpha), 0.7)


def _symmetry_axis_snap(c: Canvas, p: float) -> None:
    q = window(p, 0.45)
    axis_x = 72.0
    _axis(c, axis_x, q)
    left = [(42, 42), (31, 69), (48, 94), (56, 116)]
    for i, (x, y) in enumerate(left):
        _node(c, (x, y), 4.0 + (i % 2), ETHER, q)
        target_x = axis_x + (axis_x - x)
        start_x = 118 + (i % 2) * 8
        local = smooth(max(0.0, min(1.0, p * 1.55 - i * 0.08)))
        right_x = start_x + (target_x - start_x) * local
        _node(c, (right_x, y), 4.0 + (i % 2), VIOLET, q)
        if local > 0.25:
            c.line([(x + 4, y), (axis_x - 4, y)], fade(ETHER, 0.22 * q), 0.8)
            c.line([(axis_x + 4, y), (right_x - 4, y)], fade(VIOLET, 0.22 * q), 0.8)
    c.diamond((72, 72), 6, 6, fade(GOLD, 0.20 * q), fade(GOLD, 0.82 * q), 1.0)


def _invariant_core(c: Canvas, p: float) -> None:
    center = (72.0, 72.0)
    phase = p * math.tau
    c.ellipse(center, 46, 46, outline=fade(ETHER, 0.28), width=1.0)
    # Square and diamond trade prominence while the center remains unchanged.
    square_alpha = 0.35 + 0.45 * (0.5 + 0.5 * math.cos(phase))
    diamond_alpha = 0.35 + 0.45 * (0.5 + 0.5 * math.sin(phase))
    r = 25 + 7 * math.sin(phase)
    c.rect((72 - r, 72 - r, 72 + r, 72 + r), outline=fade(ETHER, square_alpha), width=1.4)
    c.diamond(center, 31 - 5 * math.sin(phase), 31 - 5 * math.sin(phase), None, fade(VIOLET, diamond_alpha), 1.4)
    for i in range(8):
        a = phase * 0.25 + i * math.tau / 8
        _node(c, (72 + math.cos(a) * 45, 72 + math.sin(a) * 45), 2.5, ETHER if i % 2 == 0 else VIOLET, 0.72)
    c.ellipse(center, 4.0, fill=GOLD, outline=ETHER_LIGHT, width=0.8)


def _conserved_pair_exchange(c: Canvas, p: float) -> None:
    center = (72.0, 72.0)
    c.ellipse(center, 43, 28, outline=fade(INK_BLUE, 0.38), width=1.0)
    a = p * math.tau
    a_pt = (72 + math.cos(a) * 43, 72 + math.sin(a) * 28)
    b_pt = (72 - math.cos(a) * 43, 72 - math.sin(a) * 28)
    _node(c, a_pt, 7, ETHER, 0.95)
    _node(c, b_pt, 7, VIOLET, 0.95)
    c.line([a_pt, b_pt], fade(GOLD, 0.26), 0.9)
    c.ellipse(center, 4.0, fill=GOLD, outline=ETHER_LIGHT, width=0.7)
    # Equal-size auxiliary bars reinforce that quantity is transferred, not created.
    c.rect((30, 118, 68, 123), fill=fade(ETHER, 0.34), outline=fade(ETHER, 0.72), width=0.6)
    c.rect((76, 118, 114, 123), fill=fade(VIOLET, 0.34), outline=fade(VIOLET, 0.72), width=0.6)


def _group_orbit(c: Canvas, p: float) -> None:
    center = (72.0, 72.0)
    c.ellipse(center, 44, 44, outline=fade(ETHER, 0.26), width=1.0)
    for i in range(6):
        a = p * math.tau / 6 + i * math.tau / 6
        pt = (72 + math.cos(a) * 44, 72 + math.sin(a) * 44)
        c.diamond(pt, 5, 5, fade(ETHER if i % 2 == 0 else VIOLET, 0.18), fade(ETHER_LIGHT, 0.8), 0.8)
        c.line([center, pt], fade(GOLD, 0.12 + 0.10 * (i % 2)), 0.7)
    # Two reflection axes make the finite transformation group legible.
    c.line([(31, 72), (113, 72)], fade(GOLD, 0.28), 0.7)
    c.line([(72, 31), (72, 113)], fade(GOLD, 0.28), 0.7)
    c.ellipse(center, 3.8, fill=GOLD)


def _generator_steps(c: Canvas, p: float) -> None:
    center = (72.0, 72.0)
    q = window(p, 0.58)
    steps = 8
    built = min(steps, int(p * (steps + 1)))
    for i in range(steps):
        a0 = -math.pi / 2 + i * math.tau / steps
        a1 = -math.pi / 2 + (i + 1) * math.tau / steps
        p0 = (72 + math.cos(a0) * 40, 72 + math.sin(a0) * 40)
        p1 = (72 + math.cos(a1) * 40, 72 + math.sin(a1) * 40)
        color = ETHER if i % 2 == 0 else VIOLET
        _node(c, p0, 3.5, color, 0.82 * q if i <= built else 0.18 * q)
        if i < built:
            c.arrow(p0, p1, fade(color, 0.74 * q), 1.1, 4.0)
    c.diamond(center, 6, 6, fade(GOLD, 0.22 * q), fade(GOLD, 0.92 * q), 1.0)


def _broken_symmetry_shards(c: Canvas, p: float) -> None:
    q = window(p, 0.35)
    center = (72.0, 72.0)
    _axis(c, 72, 0.42 * q)
    shards = [(-35, -28), (-24, 7), (-39, 33), (35, -28), (24, 7), (39, 33)]
    for i, (dx, dy) in enumerate(shards):
        side = -1 if dx < 0 else 1
        fracture = max(0.0, p - 0.34)
        asym = (i % 3 - 1) * 7.0 * fracture * side
        drift = (10 + (i % 3) * 7) * fracture
        x = center[0] + dx + side * drift
        y = center[1] + dy + asym + (i % 2) * fracture * 8
        c.diamond((x, y), 6 + i % 2 * 2, 5 + (i + 1) % 2 * 2, fade(ETHER if side < 0 else VIOLET, 0.14 * q), fade(ETHER_LIGHT, 0.66 * q), 0.8)
    # The invariant survives the broken exterior symmetry.
    c.ellipse(center, 4.6, fill=fade(GOLD, q), outline=fade(ETHER_LIGHT, q), width=0.7)


def _ether_cancel(c: Canvas, p: float) -> None:
    q = window(p, 0.48)
    center = (72.0, 72.0)
    for side, color in ((-1, ETHER), (1, VIOLET)):
        pts = []
        for i in range(15):
            u = i / 14
            x = center[0] + side * (52 * (1 - u) * (1 - smooth(p)) + 22 * (1 - u))
            y = center[1] + math.sin(u * math.pi * 2 + side * p * 1.8) * 12 * (1 - u)
            pts.append((x, y))
        c.line(pts, fade(color, 0.54 * q), 2.0)
    collapse = max(0.0, (p - 0.45) / 0.55)
    c.ellipse(center, 16 * (1 - collapse) + 2, outline=fade(GOLD, q * (1 - collapse)), width=1.1)
    if collapse > 0.3:
        c.star(center, 4.5 + 3 * collapse, fade(ETHER_LIGHT, q * (1 - collapse * 0.5)), points=4)


def _equivalence_bridge(c: Canvas, p: float) -> None:
    q = window(p, 0.52)
    left = (38.0, 72.0)
    right = (106.0, 72.0)
    center = (72.0, 72.0)
    tri = [(38, 50), (20, 88), (56, 88)]
    c.polygon(tri, fade(ETHER, 0.07 * q), fade(ETHER, 0.72 * q), 1.3)
    c.rect((88, 54, 124, 90), fill=fade(VIOLET, 0.07 * q), outline=fade(VIOLET, 0.72 * q), width=1.3)
    local = smooth(min(1.0, p * 1.45))
    c.line([(56, 72), (56 + 16 * local, 72)], fade(GOLD, 0.68 * q), 1.5)
    c.line([(88 - 16 * local, 72), (88, 72)], fade(GOLD, 0.68 * q), 1.5)
    c.diamond(center, 8, 8, fade(GOLD, 0.18 * q), fade(ETHER_LIGHT, 0.88 * q), 1.0)
    _node(c, left, 3.0, ETHER, q)
    _node(c, right, 3.0, VIOLET, q)


def _conservation_transfer(c: Canvas, p: float) -> None:
    q = window(p, 0.62)
    left = (45.0, 72.0)
    right = (99.0, 72.0)
    c.ellipse(left, 24, 24, outline=fade(ETHER, 0.36 * q), width=1.0)
    c.ellipse(right, 24, 24, outline=fade(VIOLET, 0.36 * q), width=1.0)
    # Arc lengths complement one another: total authored quantity stays constant.
    amount = smooth(p)
    c.arc(left, 19, 19, -90, -90 + 300 * (1 - amount), fade(ETHER, 0.88 * q), 3.0)
    c.arc(right, 19, 19, -90, -90 + 300 * amount, fade(VIOLET, 0.88 * q), 3.0)
    c.arrow((65, 72), (79, 72), fade(GOLD, 0.72 * q), 1.2, 4)
    c.ellipse((72, 72), 3.2, fill=GOLD)


def _proof_complete(c: Canvas, p: float) -> None:
    q = window(p, 0.62)
    nodes = [(30, 74), (45, 39), (72, 28), (99, 39), (114, 74), (95, 108), (49, 108), (72, 72)]
    edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 0), (1, 7), (3, 7), (5, 7), (6, 7)]
    for i, (a, b) in enumerate(edges):
        local = max(0.0, min(1.0, p * 1.75 - i * 0.055))
        if local <= 0:
            continue
        ax, ay = nodes[a]
        bx, by = nodes[b]
        c.line([(ax, ay), (ax + (bx - ax) * smooth(local), ay + (by - ay) * smooth(local))], fade(INK_BLUE if i < 7 else GOLD, 0.62 * q), 1.0)
    for i, point in enumerate(nodes):
        _node(c, point, 3.5 if i != 7 else 5.0, ETHER if i % 2 == 0 else VIOLET, q)
    if p > 0.65:
        c.star((72, 72), 4.0 + 3.0 * smooth((p - 0.65) / 0.35), fade(GOLD, q), points=4)


def _paired_trajectory(c: Canvas, p: float) -> None:
    q = window(p, 0.56)
    center = (72.0, 72.0)
    _axis(c, 72, 0.28 * q)
    for side, color in ((-1, ETHER), (1, VIOLET)):
        pts = []
        for i in range(22):
            u = i / 21
            x = center[0] + side * (14 + 42 * u)
            y = 112 - 72 * u + 24 * (u - 0.5) ** 2
            pts.append((x, y))
        c.line(pts, fade(color, 0.42 * q), 1.1)
        u = p
        x = center[0] + side * (14 + 42 * u)
        y = 112 - 72 * u + 24 * (u - 0.5) ** 2
        _node(c, (x, y), 4.5, color, q)
    c.ellipse(center, 3.5, fill=GOLD)


def _conserved_current(c: Canvas, p: float) -> None:
    center = (72.0, 72.0)
    phase = p * math.tau
    c.ellipse(center, 45, 31, outline=fade(FIELD_DARK, 0.65), width=1.0)
    for i in range(10):
        a = phase + i * math.tau / 10
        pt = (72 + math.cos(a) * 45, 72 + math.sin(a) * 31)
        tangent = (-math.sin(a), math.cos(a))
        end = (pt[0] + tangent[0] * 7, pt[1] + tangent[1] * 7)
        c.arrow(pt, end, fade(ETHER if i < 5 else VIOLET, 0.62), 0.9, 2.8)
    c.diamond(center, 7, 7, fade(GOLD, 0.18), fade(GOLD, 0.88), 1.0)
    c.ellipse(center, 2.4, fill=ETHER_LIGHT)


DRAWERS = {
    "symmetry_axis_snap": _symmetry_axis_snap,
    "invariant_core": _invariant_core,
    "conserved_pair_exchange": _conserved_pair_exchange,
    "group_orbit": _group_orbit,
    "generator_steps": _generator_steps,
    "broken_symmetry_shards": _broken_symmetry_shards,
    "ether_cancel": _ether_cancel,
    "equivalence_bridge": _equivalence_bridge,
    "conservation_transfer": _conservation_transfer,
    "proof_complete": _proof_complete,
    "paired_trajectory": _paired_trajectory,
    "conserved_current": _conserved_current,
}

SPECS = {
    "symmetry_axis_snap": make_spec("symmetry", "Independent geometry snaps into exact bilateral symmetry around a persistent axis.", placement="target", relationship="active", extra_anchor="target", size=118),
    "invariant_core": make_spec("invariant", "Exterior square/diamond descriptions transform periodically while a gold central invariant never moves.", loop=True, placement="source", attachment="follow_source", relationship="sustain", extra_anchor="emitter", size=112),
    "conserved_pair_exchange": make_spec("conservation", "Antipodal quantities exchange positions while equal authored measures remain visible.", loop=True, placement="source", attachment="follow_source", relationship="sustain", extra_anchor="emitter", size=118),
    "group_orbit": make_spec("transformation_group", "A finite orbit of repeated rotations/reflections around one invariant center.", loop=True, placement="source", attachment="follow_source", relationship="sustain", extra_anchor="emitter", size=116),
    "generator_steps": make_spec("generator", "One elementary transformation is repeatedly composed around a closed cycle.", placement="world", relationship="startup", size=112),
    "broken_symmetry_shards": make_spec("symmetry_break", "Paired exterior geometry fractures asymmetrically while the invariant center survives.", placement="target", relationship="impact", extra_anchor="target", size=126),
    "ether_cancel": make_spec("cancellation", "Opposed field-like constructions approach pairwise and cancel at the invariant center.", placement="target", relationship="release", extra_anchor="target", size=122),
    "equivalence_bridge": make_spec("equivalence", "Different exterior constructions meet at the same invariant intermediate.", placement="world", relationship="active", size=124),
    "conservation_transfer": make_spec("conservation", "Complementary arc measures transfer from one reservoir to another with fixed total quantity.", placement="world", relationship="active", size=112),
    "proof_complete": make_spec("proof", "Apparently separate nodes acquire edges until one coherent symmetric construction resolves.", placement="world", relationship="aftermath", size=126),
    "paired_trajectory": make_spec("symmetry", "Two trajectories remain exact mirror images while advancing through the same parameter.", loop=True, placement="source", attachment="follow_source", relationship="sustain", extra_anchor="emitter", size=124),
    "conserved_current": make_spec("conservation", "A periodic directed current circulates around a fixed invariant core.", loop=True, placement="source", attachment="follow_source", relationship="sustain", extra_anchor="emitter", size=118),
}

ORIGINS = {name: (72.0, 72.0) for name, _, _ in ROWS}


def render(out_dir: str | Path, **opts):
    del opts
    return publish_catalog(
        target_name=TARGET_NAME,
        display_name="Emmy Ethereal Detached VFX",
        character_context_id="npc_noether",
        character_context_display="Emmy Ethereal",
        rows=ROWS,
        drawers=DRAWERS,
        specs=SPECS,
        origins=ORIGINS,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
    )


def render_canonical(out_dir: str | Path, **opts):
    del opts
    return publish_canonical(
        target_name=TARGET_NAME,
        rows=ROWS,
        drawers=DRAWERS,
        specs=SPECS,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
    )
