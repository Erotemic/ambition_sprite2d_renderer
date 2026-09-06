"""Geometric special-move effects for Emmy Ethereal.

The SVG remains the character-art authority. These effects are procedural,
resolution-independent sprite-side presentation layered around the solved rig.
Their visual language is intentionally mathematical rather than magical-glow
noise: paired constructions, invariant centers, mirrored trajectories, and
conservation loops.
"""

from __future__ import annotations

import math
from typing import Mapping

from PIL import Image, ImageFilter

from ...profiling import profile

from ._svg_fighter_effects import FxCanvas, bone_origin, clamp01, fade, pulse, smooth

Color = tuple[int, int, int, int]
Point = tuple[float, float]
World = Mapping[str, object]

OUTLINE: Color = (25, 27, 38, 255)
ETHER: Color = (126, 220, 238, 255)
ETHER_LIGHT: Color = (218, 249, 250, 255)
VIOLET: Color = (150, 124, 210, 255)
VIOLET_DARK: Color = (80, 67, 126, 255)
GOLD: Color = (239, 198, 104, 255)
CORAL: Color = (219, 105, 102, 255)
INK_BLUE: Color = (57, 82, 119, 255)
FIELD_DARK: Color = (35, 45, 67, 255)

EFFECTFUL_ANIMATIONS = frozenset(
    {
        "invariant_parry",
        "symmetry_proof",
        "generator_strike",
        "conservation_law",
        "symmetry_shift",
        "ethereal_lift",
        "invariant_field",
        "symmetry_break",
        "noether_theorem",
    }
)




def _alpha_scaled(alpha: Image.Image, factor: float) -> Image.Image:
    q = max(0.0, min(1.0, float(factor)))
    return alpha.point(lambda value: int(round(value * q)))


@profile
def apply_ethereal_hum(
    frame: Image.Image,
    rig_image: Image.Image,
    t: float,
    *,
    scale: float = 1.0,
) -> Image.Image:
    """Add Emmy's prominent breathing silhouette field behind the composed frame.

    The hum is derived from the solved rig alpha rather than from screen-space
    decorations, so it follows every authored animation and pose.  It never
    changes collision/rig geometry.  The field deliberately breathes in both
    radius and intensity: a cyan body-adjacent shell anchors the silhouette
    while a much larger violet atmosphere visibly swells and recedes.

    ``scale`` is the render scale of the raster being passed in, relative to the
    rig's own canvas.  The radii below are authored in canvas pixels, and a blur
    radius does not scale itself: rendering Emmy at portrait resolution and
    applying the same numbers would give her a hairline outline instead of an
    atmosphere.  Every caller rendering above canvas scale owes this argument.
    """
    if frame.mode != "RGBA":
        frame = frame.convert("RGBA")
    if rig_image.mode != "RGBA":
        rig_image = rig_image.convert("RGBA")

    alpha = rig_image.getchannel("A")

    # One slow breath per normalized animation cycle.  Squaring the 0..1 wave
    # makes the field linger near its quiet state and then bloom decisively, so
    # the motion reads even in peripheral vision instead of looking like minor
    # antialiasing fluctuation.
    breath = 0.5 + 0.5 * math.sin(t * math.tau - math.pi * 0.5)
    bloom = breath * breath

    # Keep this to two full-frame Gaussian passes: the hum should be visually
    # large without surrendering the SVG-rig performance gains.  Both radii move
    # with the breath, making the aura expand roughly a dozen publication pixels
    # over the cycle rather than only changing alpha in place.
    close_radius = (5.5 + 3.5 * breath) * scale
    broad_radius = (18.0 + 16.0 * bloom) * scale
    close = alpha.filter(ImageFilter.GaussianBlur(close_radius))
    broad = alpha.filter(ImageFilter.GaussianBlur(broad_radius))

    aura = Image.new("RGBA", frame.size, (0, 0, 0, 0))

    # The outer violet atmosphere is intentionally conspicuous.  Its minimum is
    # still plainly visible; at full bloom it becomes a broad spectral field.
    violet = Image.new("RGBA", frame.size, VIOLET[:3] + (0,))
    violet_strength = 0.28 + 0.30 * bloom
    violet.putalpha(_alpha_scaled(broad, violet_strength))
    aura.alpha_composite(violet)

    # The close cyan shell has a smaller amplitude swing so Emmy retains a
    # luminous outline throughout the cycle while the violet field does most of
    # the breathing.
    cyan = Image.new("RGBA", frame.size, ETHER[:3] + (0,))
    cyan_strength = 0.55 + 0.30 * breath
    cyan.putalpha(_alpha_scaled(close, cyan_strength))
    aura.alpha_composite(cyan)

    aura.alpha_composite(frame)
    return aura


def _center(world: World) -> Point:
    torso = bone_origin(world, "torso", (96.0, 111.0))
    head = bone_origin(world, "head", (96.0, 76.0))
    return (torso[0], (torso[1] + head[1]) * 0.5 + 8.0)


def _hands(world: World) -> tuple[Point, Point]:
    return (
        bone_origin(world, "near_arm_hand", (128.0, 112.0)),
        bone_origin(world, "far_arm_hand", (112.0, 118.0)),
    )


def _window(t: float, attack: float = 0.5) -> float:
    """Smooth appearance envelope with a peak around *attack*."""
    t = clamp01(t)
    if t <= attack:
        return smooth(t / max(attack, 1e-6))
    return smooth((1.0 - t) / max(1.0 - attack, 1e-6))


def _diamond(
    canvas: FxCanvas,
    center: Point,
    rx: float,
    ry: float,
    color: Color,
    *,
    alpha: float,
    fill_alpha: float = 0.0,
    width: float = 1.0,
) -> None:
    points = [
        (center[0], center[1] - ry),
        (center[0] + rx, center[1]),
        (center[0], center[1] + ry),
        (center[0] - rx, center[1]),
    ]
    fill = fade(color, fill_alpha * alpha) if fill_alpha > 0 else (0, 0, 0, 0)
    canvas.polygon(points, fill, fade(color, alpha), width)


def _paired_nodes(
    canvas: FxCanvas,
    center: Point,
    *,
    rx: float,
    ry: float,
    count: int,
    phase: float,
    alpha: float,
    color_a: Color = ETHER,
    color_b: Color = VIOLET,
) -> None:
    """Draw antipodal node pairs so the construction is exactly symmetric."""
    half = max(1, count // 2)
    for index in range(half):
        angle = phase * math.tau + index * math.tau / half
        dx = math.cos(angle) * rx
        dy = math.sin(angle) * ry
        radius = 1.7 + 0.45 * (index % 3)
        for sign, color in ((1.0, color_a), (-1.0, color_b)):
            point = (center[0] + sign * dx, center[1] + sign * dy)
            canvas.ellipse(
                point,
                radius,
                radius,
                fade(color, alpha * 0.68),
                fade(ETHER_LIGHT, alpha * 0.8),
                0.55,
            )


def _opposed_arrows(
    canvas: FxCanvas,
    center: Point,
    *,
    span: float,
    y_offset: float,
    alpha: float,
    width: float = 1.0,
) -> None:
    left_y = center[1] - y_offset
    right_y = center[1] + y_offset
    canvas.arrow(
        (center[0] - span, left_y),
        (center[0] + span, left_y),
        fade(ETHER, alpha),
        width,
        4.0,
    )
    canvas.arrow(
        (center[0] + span, right_y),
        (center[0] - span, right_y),
        fade(VIOLET, alpha),
        width,
        4.0,
    )


def _conservation_behind(canvas: FxCanvas, t: float, world: World) -> None:
    center = _center(world)
    q = _window(t, 0.54)
    for index, (rx, ry) in enumerate(((31.0, 21.0), (43.0, 30.0), (55.0, 39.0))):
        alpha = q * (0.46 - 0.07 * index)
        canvas.ellipse(center, rx, ry, fade(FIELD_DARK, alpha * 0.12), fade(ETHER if index % 2 == 0 else VIOLET, alpha), 1.0)
        # Two opposing arcs make the circulation direction legible without text.
        canvas.arc(center, rx, ry, 205, 335, fade(ETHER_LIGHT, alpha * 0.92), 1.35)
        canvas.arc(center, rx, ry, 25, 155, fade(GOLD, alpha * 0.78), 1.15)
    _paired_nodes(canvas, center, rx=49.0, ry=34.0, count=8, phase=t * 0.16, alpha=0.55 * q)
    _opposed_arrows(canvas, center, span=38.0, y_offset=11.0, alpha=0.52 * q)


def _conservation_front(canvas: FxCanvas, t: float, world: World) -> None:
    center = _center(world)
    near, far = _hands(world)
    q = _window(t, 0.54)
    for hand, color in ((near, ETHER), (far, VIOLET)):
        canvas.ellipse(hand, 4.0 + 2.5 * pulse(t), 4.0 + 2.5 * pulse(t), fade(color, 0.33 * q), fade(ETHER_LIGHT, 0.8 * q), 0.8)
        canvas.line([hand, center], fade(color, 0.38 * q), 0.75)
    _diamond(canvas, center, 8.5 + 3.5 * pulse(t), 8.5 + 3.5 * pulse(t), GOLD, alpha=0.8 * q, fill_alpha=0.10, width=1.1)
    canvas.ellipse(center, 2.2, 2.2, fade(ETHER_LIGHT, 0.9 * q), fade(OUTLINE, 0.5 * q), 0.6)


def _shift_behind(canvas: FxCanvas, t: float, world: World) -> None:
    center = _center(world)
    q = _window(t, 0.48)
    split = 10.0 + 31.0 * smooth(t)
    # A mirror axis stays fixed while two congruent frames separate from it.
    canvas.line([(center[0], center[1] - 53), (center[0], center[1] + 57)], fade(ETHER_LIGHT, 0.28 + 0.42 * q), 0.85)
    for sign, color in ((-1.0, VIOLET), (1.0, ETHER)):
        c = (center[0] + sign * split, center[1])
        _diamond(canvas, c, 23.0, 38.0, color, alpha=0.45 * q, fill_alpha=0.035, width=1.15)
        canvas.line([(center[0], center[1] - 28), (c[0], center[1] - 28)], fade(color, 0.34 * q), 0.65)
        canvas.line([(center[0], center[1] + 28), (c[0], center[1] + 28)], fade(color, 0.34 * q), 0.65)
    _paired_nodes(canvas, center, rx=split + 18.0, ry=32.0, count=8, phase=0.125, alpha=0.42 * q)


def _shift_front(canvas: FxCanvas, t: float, world: World) -> None:
    center = _center(world)
    near, far = _hands(world)
    q = _window(t, 0.48)
    # The hands make the transformation feel authored by the body rather than
    # appearing as a detached generic particle system.
    canvas.arrow(far, (center[0] - 31.0, center[1]), fade(VIOLET, 0.68 * q), 1.15, 4.0)
    canvas.arrow(near, (center[0] + 31.0, center[1]), fade(ETHER, 0.68 * q), 1.15, 4.0)
    for sign, color in ((-1.0, VIOLET), (1.0, ETHER)):
        x = center[0] + sign * (34.0 + 13.0 * pulse(t))
        _diamond(canvas, (x, center[1]), 5.0, 8.0, color, alpha=0.85 * q, fill_alpha=0.28, width=0.8)


def _lift_behind(canvas: FxCanvas, t: float, world: World) -> None:
    center = _center(world)
    q = _window(t, 0.58)
    bottom = center[1] + 58.0
    top = center[1] - 73.0
    # Two parallel rails and stacked chevrons keep the recovery perfectly
    # bilaterally symmetric while giving a strong vertical read.
    for dx, color in ((-18.0, VIOLET), (18.0, ETHER)):
        canvas.line([(center[0] + dx, bottom), (center[0] + dx, top)], fade(color, 0.34 * q), 1.2)
    for index in range(5):
        y = bottom - ((t * 58.0 + index * 29.0) % (bottom - top + 20.0))
        span = 11.0 + index % 2 * 4.0
        canvas.line([(center[0] - span, y + 7.0), (center[0], y), (center[0] + span, y + 7.0)], fade(ETHER_LIGHT, 0.42 * q), 1.15)
    for radius in (18.0, 29.0, 41.0):
        canvas.ellipse((center[0], bottom - 4.0), radius, radius * 0.28, None, fade(ETHER if int(radius) % 2 else VIOLET, 0.34 * q), 0.85)


def _lift_front(canvas: FxCanvas, t: float, world: World) -> None:
    center = _center(world)
    q = _window(t, 0.58)
    for index in range(4):
        y = center[1] + 42.0 - ((t * 90.0 + index * 34.0) % 128.0)
        size = 3.5 + index * 0.7
        _diamond(canvas, (center[0], y), size, size * 1.35, ETHER_LIGHT, alpha=0.55 * q, fill_alpha=0.20, width=0.65)
    canvas.ellipse((center[0], center[1] - 25.0), 8.0 + 4.0 * pulse(t), 3.0 + 1.5 * pulse(t), fade(ETHER, 0.20 * q), fade(ETHER_LIGHT, 0.72 * q), 0.85)


def _field_behind(canvas: FxCanvas, t: float, world: World) -> None:
    center = _center(world)
    q = _window(t, 0.50)
    # Circle + square/diamond layers communicate an invariant object seen
    # through several equivalent representations.
    for index, radius in enumerate((29.0, 41.0, 53.0)):
        canvas.ellipse(center, radius, radius, fade(FIELD_DARK, 0.025 * q), fade(ETHER if index % 2 == 0 else VIOLET, (0.42 - index * 0.06) * q), 1.0)
    wobble = 5.0 * math.sin(t * math.tau)
    _diamond(canvas, center, 38.0 + wobble, 38.0 + wobble, VIOLET, alpha=0.48 * q, fill_alpha=0.035, width=1.15)
    _diamond(canvas, center, 25.0 - wobble * 0.45, 25.0 - wobble * 0.45, ETHER, alpha=0.55 * q, fill_alpha=0.045, width=1.0)
    _paired_nodes(canvas, center, rx=47.0, ry=47.0, count=8, phase=t * 0.11, alpha=0.52 * q)


def _field_front(canvas: FxCanvas, t: float, world: World) -> None:
    center = _center(world)
    near, far = _hands(world)
    q = _window(t, 0.50)
    # Opposite hand currents terminate at the same unchanging core.
    for hand, color in ((near, ETHER), (far, VIOLET)):
        canvas.line([hand, center], fade(color, 0.46 * q), 1.0)
        canvas.ellipse(hand, 3.0, 3.0, fade(color, 0.32 * q), fade(ETHER_LIGHT, 0.72 * q), 0.6)
    canvas.ellipse(center, 5.0, 5.0, fade(GOLD, 0.30 * q), fade(ETHER_LIGHT, 0.85 * q), 0.9)
    canvas.ellipse(center, 1.5, 1.5, fade(OUTLINE, 0.9 * q))


def _break_behind(canvas: FxCanvas, t: float, world: World) -> None:
    center = _center(world)
    q = _window(t, 0.61)
    # Start with a visibly symmetric lattice, then break its center line.
    half_w, half_h = 54.0, 48.0
    for xoff in (-36.0, -18.0, 0.0, 18.0, 36.0):
        canvas.line([(center[0] + xoff, center[1] - half_h), (center[0] + xoff, center[1] + half_h)], fade(INK_BLUE, 0.20 * q), 0.55)
    for yoff in (-32.0, -16.0, 0.0, 16.0, 32.0):
        canvas.line([(center[0] - half_w, center[1] + yoff), (center[0] + half_w, center[1] + yoff)], fade(INK_BLUE, 0.20 * q), 0.55)
    if t > 0.35:
        r = smooth((t - 0.35) / 0.65)
        crack = [
            (center[0], center[1] - 48),
            (center[0] - 5 * r, center[1] - 27),
            (center[0] + 7 * r, center[1] - 9),
            (center[0] - 9 * r, center[1] + 12),
            (center[0] + 6 * r, center[1] + 31),
            (center[0], center[1] + 48),
        ]
        canvas.line(crack, fade(CORAL, 0.78 * q), 2.0)
        for sign in (-1.0, 1.0):
            for index in range(3):
                x = center[0] + sign * (17.0 + index * 13.0) * r
                y = center[1] + (-23.0 + index * 22.0)
                canvas.polygon(
                    [(x, y - 5), (x + sign * 7, y), (x, y + 5)],
                    fade(CORAL if index % 2 else GOLD, 0.16 * q),
                    fade(CORAL, 0.50 * q),
                    0.75,
                )


def _break_front(canvas: FxCanvas, t: float, world: World) -> None:
    near, _far = _hands(world)
    q = _window(t, 0.61)
    radius = 5.0 + 8.0 * pulse(t)
    canvas.star(near, radius, fade(GOLD, 0.30 * q), points=4, inner=0.30, outline=fade(CORAL, 0.88 * q))
    for angle in (-0.65, -0.22, 0.22, 0.65):
        end = (near[0] + math.cos(angle) * 27.0, near[1] + math.sin(angle) * 27.0)
        canvas.line([near, end], fade(CORAL, 0.52 * q), 0.85)


def _theorem_behind(canvas: FxCanvas, t: float, world: World) -> None:
    center = _center(world)
    q = _window(t, 0.63)
    # A large finite-group-like diagram: concentric invariant rings, antipodal
    # nodes, and chords between equivalent points. It reads as one construction
    # rather than as free-floating particles.
    radii = (24.0, 39.0, 55.0, 72.0)
    for index, radius in enumerate(radii):
        squash = 0.78 + index * 0.035
        canvas.ellipse(center, radius, radius * squash, fade(FIELD_DARK, 0.018 * q), fade((ETHER, VIOLET, GOLD, ETHER_LIGHT)[index], (0.42 - 0.04 * index) * q), 1.05)
    node_count = 12
    nodes: list[Point] = []
    for index in range(node_count):
        angle = t * math.tau * 0.10 + index * math.tau / node_count
        point = (center[0] + math.cos(angle) * 67.0, center[1] + math.sin(angle) * 52.0)
        nodes.append(point)
        color = ETHER if index % 3 == 0 else VIOLET if index % 3 == 1 else GOLD
        canvas.ellipse(point, 2.4, 2.4, fade(color, 0.58 * q), fade(ETHER_LIGHT, 0.75 * q), 0.55)
    for index in range(node_count // 2):
        canvas.line([nodes[index], nodes[index + node_count // 2]], fade(ETHER_LIGHT, 0.11 * q), 0.45)
    _diamond(canvas, center, 31.0, 31.0, GOLD, alpha=0.48 * q, fill_alpha=0.028, width=1.15)
    _opposed_arrows(canvas, center, span=55.0, y_offset=17.0, alpha=0.38 * q, width=0.9)


def _theorem_front(canvas: FxCanvas, t: float, world: World) -> None:
    center = _center(world)
    near, far = _hands(world)
    q = _window(t, 0.63)
    for hand, color in ((near, ETHER), (far, VIOLET)):
        canvas.line([hand, center], fade(color, 0.52 * q), 1.15)
        _diamond(canvas, hand, 4.3, 6.0, color, alpha=0.78 * q, fill_alpha=0.22, width=0.7)
    for radius, color in ((5.0, ETHER_LIGHT), (9.0, GOLD), (14.0, VIOLET)):
        canvas.ellipse(center, radius * (0.75 + 0.25 * pulse(t)), radius * (0.75 + 0.25 * pulse(t)), None, fade(color, 0.64 * q), 0.9)
    canvas.star(center, 5.0 + 2.5 * pulse(t), fade(ETHER_LIGHT, 0.30 * q), points=4, inner=0.34, outline=fade(GOLD, 0.8 * q))


def _parry(canvas: FxCanvas, t: float, world: World) -> None:
    center = _center(world)
    q = _window(t, 0.46)
    _diamond(canvas, center, 28.0, 38.0, ETHER, alpha=0.65 * q, fill_alpha=0.055, width=1.35)
    canvas.ellipse(center, 34.0, 44.0, None, fade(VIOLET, 0.44 * q), 0.95)
    _paired_nodes(canvas, center, rx=31.0, ry=40.0, count=8, phase=0.125, alpha=0.58 * q)


def _proof(canvas: FxCanvas, t: float, world: World) -> None:
    center = _center(world)
    q = _window(t, 0.55)
    for sign in (-1.0, 1.0):
        c = (center[0] + sign * 26.0, center[1])
        _diamond(canvas, c, 15.0, 22.0, ETHER if sign > 0 else VIOLET, alpha=0.58 * q, fill_alpha=0.04, width=0.9)
    canvas.line([(center[0] - 11.0, center[1]), (center[0] + 11.0, center[1])], fade(GOLD, 0.70 * q), 1.1)
    canvas.arrow((center[0] - 5.0, center[1] - 7.0), (center[0] + 5.0, center[1] - 7.0), fade(GOLD, 0.62 * q), 0.75, 2.6)
    canvas.arrow((center[0] + 5.0, center[1] + 7.0), (center[0] - 5.0, center[1] + 7.0), fade(GOLD, 0.62 * q), 0.75, 2.6)


def _generator_strike(canvas: FxCanvas, t: float, world: World) -> None:
    near, _far = _hands(world)
    q = _window(t, 0.57)
    # A compact generator glyph rides the striking hand. This is deliberately
    # directional because the attack is; the actual authored volume remains a
    # symmetric convex lens.
    for index in range(3):
        radius = 7.0 + index * 5.0
        canvas.arc(near, radius, radius * 0.72, 210, 335, fade((ETHER, GOLD, VIOLET)[index], (0.66 - index * 0.11) * q), 1.2)
    canvas.star(near, 3.8 + 2.2 * pulse(t), fade(ETHER_LIGHT, 0.42 * q), points=4, inner=0.35, outline=fade(GOLD, 0.76 * q))


def draw_noether_behind(
    animation: str,
    canvas: FxCanvas,
    t: float,
    world: World,
    params: Mapping[str, float],
) -> None:
    del params
    if animation == "conservation_law":
        _conservation_behind(canvas, t, world)
    elif animation == "symmetry_shift":
        _shift_behind(canvas, t, world)
    elif animation == "ethereal_lift":
        _lift_behind(canvas, t, world)
    elif animation == "invariant_field":
        _field_behind(canvas, t, world)
    elif animation == "symmetry_break":
        _break_behind(canvas, t, world)
    elif animation == "noether_theorem":
        _theorem_behind(canvas, t, world)
    elif animation == "invariant_parry":
        _parry(canvas, t, world)
    elif animation == "symmetry_proof":
        _proof(canvas, t, world)


def draw_noether_front(
    animation: str,
    canvas: FxCanvas,
    t: float,
    world: World,
    params: Mapping[str, float],
) -> None:
    del params
    if animation == "conservation_law":
        _conservation_front(canvas, t, world)
    elif animation == "symmetry_shift":
        _shift_front(canvas, t, world)
    elif animation == "ethereal_lift":
        _lift_front(canvas, t, world)
    elif animation == "invariant_field":
        _field_front(canvas, t, world)
    elif animation == "symmetry_break":
        _break_front(canvas, t, world)
    elif animation == "noether_theorem":
        _theorem_front(canvas, t, world)
    elif animation == "generator_strike":
        _generator_strike(canvas, t, world)


__all__ = [
    "EFFECTFUL_ANIMATIONS",
    "apply_ethereal_hum",
    "draw_noether_behind",
    "draw_noether_front",
]
