"""Detached bureaucratic/relativity VFX authored for the Patent Clerk.

The Clerk's effects should feel like office instruments and thought-experiment
diagrams brought to life: stamps, ruled frames, clocks, labels, light rays, and
measurement ticks.  They are intentionally diagrammatic rather than wizardly.
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

TARGET_NAME = "patent_clerk_vfx"
SHEET_FILES = sheet_files(TARGET_NAME)
FRAME_SIZE = (144, 144)

ROWS = [
    ("stamp_mass", 8, 48),
    ("stamp_energy", 8, 48),
    ("stamp_moving", 8, 48),
    ("stamp_at_rest", 8, 48),
    ("reference_frame_grid", 12, 70),
    ("relative_velocity_arrows", 10, 56),
    ("clock_sync", 10, 62),
    ("clock_desync", 10, 62),
    ("proper_time_tick", 12, 66),
    ("mass_energy_exchange", 11, 58),
    ("light_cone", 9, 52),
    ("simultaneity_slice", 12, 62),
    ("elevator_frame", 10, 60),
    ("known_result_stamp", 9, 54),
]

OUTLINE = (31, 31, 38, 255)
INK = (44, 48, 58, 255)
PAPER = (244, 236, 211, 255)
PAPER_DIM = (207, 199, 180, 255)
STAMP = (160, 56, 59, 255)
STAMP_LIGHT = (224, 119, 103, 255)
MASS = (196, 87, 71, 255)
ENERGY = (90, 178, 224, 255)
FRAME_BLUE = (92, 132, 178, 255)
FRAME_LIGHT = (191, 222, 236, 255)
CLOCK_GOLD = (221, 181, 98, 255)
CONVERSION = (242, 211, 115, 255)


def _stamp(c: Canvas, p: float, text: str, color) -> None:
    q = window(p, 0.28)
    impact = smooth(min(1.0, p / 0.30))
    settle = max(0.0, (p - 0.30) / 0.70)
    # The imprint enters vertically, squashes slightly on contact, then fades as ink.
    cy = 49 + 24 * impact + 2 * math.sin(min(1.0, settle) * math.pi)
    scale_y = 0.76 + 0.24 * impact
    half_w = 47.0
    half_h = 17.0 * scale_y
    c.rect((72 - half_w, cy - half_h, 72 + half_w, cy + half_h), fill=fade(PAPER, 0.08 * q), outline=fade(color, 0.88 * q), width=2.0)
    c.rect((72 - half_w + 4, cy - half_h + 4, 72 + half_w - 4, cy + half_h - 4), outline=fade(color, 0.44 * q), width=0.8)
    c.pixel_text((72, cy), text, fade(color, 0.96 * q), scale=2.15 if len(text) <= 6 else 1.65, shadow=fade(OUTLINE, 0.25 * q))
    if p > 0.22:
        splash = min(1.0, (p - 0.22) / 0.30)
        for i in range(8):
            a = i * math.tau / 8 + 0.2
            rr = 54 + 8 * splash
            pt = (72 + math.cos(a) * rr, cy + math.sin(a) * rr * 0.32)
            c.ellipse(pt, 1.2 + (i % 2), fill=fade(color, q * (1.0 - splash) * 0.55))


def _stamp_mass(c: Canvas, p: float) -> None:
    _stamp(c, p, "MASS", MASS)


def _stamp_energy(c: Canvas, p: float) -> None:
    _stamp(c, p, "ENERGY", ENERGY)


def _stamp_moving(c: Canvas, p: float) -> None:
    _stamp(c, p, "MOVING", FRAME_BLUE)


def _stamp_at_rest(c: Canvas, p: float) -> None:
    _stamp(c, p, "AT REST", CLOCK_GOLD)


def _reference_frame_grid(c: Canvas, p: float) -> None:
    phase = p * 18.0
    c.rect((22, 24, 122, 120), fill=fade(PAPER, 0.035), outline=fade(FRAME_LIGHT, 0.26), width=0.8)
    for i in range(-6, 8):
        x = 72 + i * 12 + (phase % 12)
        c.line([(x, 28), (x, 116)], fade(FRAME_BLUE, 0.20), 0.6)
    for i in range(-5, 7):
        y = 72 + i * 12
        c.line([(26, y), (118, y)], fade(FRAME_BLUE, 0.16), 0.6)
    c.arrow((34, 104), (110, 104), fade(FRAME_LIGHT, 0.74), 1.1, 4.2)
    c.arrow((34, 104), (34, 42), fade(FRAME_LIGHT, 0.74), 1.1, 4.2)
    c.ellipse((72, 72), 4.0, fill=ENERGY, outline=OUTLINE, width=0.7)
    c.pixel_text((72, 18), "LOCAL FRAME", fade(FRAME_LIGHT, 0.78), scale=1.15)


def _relative_velocity_arrows(c: Canvas, p: float) -> None:
    q = window(p, 0.52)
    center_y = 72.0
    left_len = 22 + 35 * smooth(p)
    right_len = 57 - 35 * smooth(p)
    c.arrow((72, center_y - 17), (72 + left_len, center_y - 17), fade(ENERGY, 0.86 * q), 2.0, 6.0)
    c.arrow((72, center_y + 17), (72 - right_len, center_y + 17), fade(MASS, 0.86 * q), 2.0, 6.0)
    c.line([(72, 42), (72, 102)], fade(FRAME_LIGHT, 0.28 * q), 0.8)
    c.pixel_text((72, 120), "RELATIVE", fade(FRAME_LIGHT, 0.62 * q), scale=1.25)


def _clock(c: Canvas, center: tuple[float, float], radius: float, angle: float, alpha: float, accent) -> None:
    c.ellipse(center, radius, fill=fade(PAPER, 0.10 * alpha), outline=fade(accent, 0.80 * alpha), width=1.2)
    for i in range(12):
        a = i * math.tau / 12 - math.pi / 2
        r0 = radius * (0.77 if i % 3 == 0 else 0.84)
        r1 = radius * 0.94
        c.line([(center[0] + math.cos(a) * r0, center[1] + math.sin(a) * r0), (center[0] + math.cos(a) * r1, center[1] + math.sin(a) * r1)], fade(INK, 0.42 * alpha), 0.6)
    c.line([center, (center[0] + math.cos(angle) * radius * 0.62, center[1] + math.sin(angle) * radius * 0.62)], fade(INK, 0.88 * alpha), 1.0)
    c.line([center, (center[0] + math.cos(angle * 0.37 - 0.7) * radius * 0.42, center[1] + math.sin(angle * 0.37 - 0.7) * radius * 0.42)], fade(INK, 0.74 * alpha), 1.2)
    c.ellipse(center, 1.5, fill=accent)


def _clock_sync(c: Canvas, p: float) -> None:
    q = window(p, 0.58)
    target = -math.pi / 2 + p * math.pi * 0.4
    delta = (1.0 - smooth(p)) * 1.25
    _clock(c, (44, 72), 23, target - delta, q, CLOCK_GOLD)
    _clock(c, (100, 72), 23, target + delta, q, CLOCK_GOLD)
    c.line([(67, 72), (77, 72)], fade(FRAME_BLUE, 0.52 * q), 1.0)
    if p > 0.68:
        s = smooth((p - 0.68) / 0.32)
        c.star((72, 72), 3.5 + 5 * s, fade(CONVERSION, q * (1 - s * 0.35)), points=4)


def _clock_desync(c: Canvas, p: float) -> None:
    q = window(p, 0.48)
    base = -math.pi / 2 + p * math.pi * 0.35
    delta = smooth(p) * 1.35
    _clock(c, (44, 72), 23, base - delta, q, CLOCK_GOLD)
    _clock(c, (100, 72), 23, base + delta, q, ENERGY)
    c.line([(67, 72), (77, 72)], fade(STAMP_LIGHT, 0.38 * q), 1.0)
    c.line([(69, 67), (75, 77)], fade(STAMP, 0.62 * q), 1.2)
    c.line([(75, 67), (69, 77)], fade(STAMP, 0.62 * q), 1.2)


def _proper_time_tick(c: Canvas, p: float) -> None:
    center = (72.0, 72.0)
    phase = p * math.tau
    _clock(c, center, 29, phase - math.pi / 2, 1.0, CLOCK_GOLD)
    # Outer ticks slip at different rates while the proper-time clock remains the reference.
    for i in range(16):
        a = i * math.tau / 16 + phase * (0.15 if i % 2 == 0 else -0.08)
        r0 = 39 + (i % 3) * 2
        r1 = r0 + (8 if i % 4 == 0 else 4)
        color = ENERGY if i % 2 == 0 else FRAME_BLUE
        c.line([(72 + math.cos(a) * r0, 72 + math.sin(a) * r0), (72 + math.cos(a) * r1, 72 + math.sin(a) * r1)], fade(color, 0.42), 0.8)
    c.pixel_text((72, 121), "PROPER TIME", fade(CLOCK_GOLD, 0.66), scale=1.0)


def _mass_energy_exchange(c: Canvas, p: float) -> None:
    q = window(p, 0.55)
    amount = smooth(p)
    # Matter block contracts as energy radiance expands.
    half = 18 * (1 - amount) + 4
    c.rect((39 - half, 72 - half, 39 + half, 72 + half), fill=fade(MASS, 0.42 * q), outline=fade(MASS, 0.90 * q), width=1.2)
    c.pixel_text((39, 72), "M", fade(PAPER, 0.88 * q), scale=2.0)
    radius = 6 + amount * 25
    c.ellipse((103, 72), radius, outline=fade(ENERGY, 0.82 * q), width=2.0)
    c.star((103, 72), 4 + amount * 8, fade(CONVERSION, 0.84 * q), points=6, outline=fade(ENERGY, q))
    c.arrow((61, 72), (83, 72), fade(CONVERSION, 0.72 * q), 1.4, 5)
    for i in range(5):
        a = i * math.tau / 5 + p
        c.star((103 + math.cos(a) * (radius + 7), 72 + math.sin(a) * (radius + 7)), 1.8 + i % 2, fade(ENERGY, 0.44 * q), points=4)


def _light_cone(c: Canvas, p: float) -> None:
    q = window(p, 0.48)
    event = (72.0, 74.0)
    length = 12 + 53 * smooth(p)
    c.line([event, (72 - length, 74 - length)], fade(FRAME_LIGHT, 0.86 * q), 2.0)
    c.line([event, (72 + length, 74 - length)], fade(FRAME_LIGHT, 0.86 * q), 2.0)
    c.line([event, (72 - length, 74 + length)], fade(FRAME_BLUE, 0.42 * q), 1.0)
    c.line([event, (72 + length, 74 + length)], fade(FRAME_BLUE, 0.42 * q), 1.0)
    c.line([(16, 74), (128, 74)], fade(PAPER_DIM, 0.22 * q), 0.7)
    c.line([(72, 13), (72, 131)], fade(PAPER_DIM, 0.22 * q), 0.7)
    c.star(event, 3.6, fade(CONVERSION, q), points=4)


def _simultaneity_slice(c: Canvas, p: float) -> None:
    center = (72.0, 72.0)
    for x in (36, 54, 72, 90, 108):
        c.line([(x, 30), (x, 113)], fade(FRAME_BLUE, 0.18), 0.7)
        c.ellipse((x, 50 + (x % 3) * 8), 2.6, fill=fade(ENERGY, 0.72))
        c.ellipse((x, 92 - (x % 4) * 5), 2.6, fill=fade(MASS, 0.72))
    angle = -0.72 + 1.44 * (0.5 + 0.5 * math.sin(math.tau * p))
    dx = math.cos(angle) * 62
    dy = math.sin(angle) * 62
    c.line([(center[0] - dx, center[1] - dy), (center[0] + dx, center[1] + dy)], fade(CLOCK_GOLD, 0.88), 2.0)
    c.pixel_text((72, 123), "SIMULTANEOUS", fade(CLOCK_GOLD, 0.62), scale=0.85)


def _elevator_frame(c: Canvas, p: float) -> None:
    q = window(p, 0.55)
    shift = 8 * smooth(p)
    c.rect((39, 26 + shift, 105, 116 + shift), fill=fade(PAPER, 0.035 * q), outline=fade(FRAME_BLUE, 0.68 * q), width=1.5)
    c.line([(39, 96 + shift), (105, 96 + shift)], fade(FRAME_BLUE, 0.52 * q), 1.2)
    # Apparent downward frame acceleration with a free marker inside.
    for x in (29, 115):
        c.arrow((x, 46), (x, 84 + 10 * smooth(p)), fade(MASS, 0.70 * q), 1.4, 5)
    c.ellipse((72, 68), 4.5, fill=fade(ENERGY, q), outline=OUTLINE, width=0.8)
    c.pixel_text((72, 19), "FRAME", fade(FRAME_LIGHT, 0.68 * q), scale=1.3)


def _known_result_stamp(c: Canvas, p: float) -> None:
    q = window(p, 0.38)
    c.rect((29, 35, 115, 109), fill=fade(PAPER, 0.12 * q), outline=fade(INK, 0.54 * q), width=1.0)
    for y in (49, 60, 71, 82):
        c.line([(39, y), (103, y)], fade(INK, 0.20 * q), 0.7)
    c.pixel_text((72, 45), "KNOWN RESULT", fade(FRAME_BLUE, 0.86 * q), scale=1.25)
    # The check arrives only after the document is visually established.
    if p > 0.32:
        local = smooth((p - 0.32) / 0.68)
        start = (50, 85)
        mid = (65, 98)
        end = (98, 66)
        if local < 0.45:
            u = local / 0.45
            point = (start[0] + (mid[0] - start[0]) * u, start[1] + (mid[1] - start[1]) * u)
            c.line([start, point], fade(STAMP, 0.92 * q), 4.0)
        else:
            c.line([start, mid], fade(STAMP, 0.92 * q), 4.0)
            u = (local - 0.45) / 0.55
            point = (mid[0] + (end[0] - mid[0]) * u, mid[1] + (end[1] - mid[1]) * u)
            c.line([mid, point], fade(STAMP, 0.92 * q), 4.0)


DRAWERS = {
    "stamp_mass": _stamp_mass,
    "stamp_energy": _stamp_energy,
    "stamp_moving": _stamp_moving,
    "stamp_at_rest": _stamp_at_rest,
    "reference_frame_grid": _reference_frame_grid,
    "relative_velocity_arrows": _relative_velocity_arrows,
    "clock_sync": _clock_sync,
    "clock_desync": _clock_desync,
    "proper_time_tick": _proper_time_tick,
    "mass_energy_exchange": _mass_energy_exchange,
    "light_cone": _light_cone,
    "simultaneity_slice": _simultaneity_slice,
    "elevator_frame": _elevator_frame,
    "known_result_stamp": _known_result_stamp,
}

SPECS = {
    "stamp_mass": make_spec("classification_stamp", "Bureaucratic MASS classification imprint with a physical ink-slam read.", placement="target", relationship="impact", extra_anchor="target", rotate_safe=False, size=112),
    "stamp_energy": make_spec("classification_stamp", "Bureaucratic ENERGY classification imprint in the Clerk's cool energy color.", placement="target", relationship="impact", extra_anchor="target", rotate_safe=False, size=112),
    "stamp_moving": make_spec("classification_stamp", "MOVING classification imprint; deliberately administrative rather than magical.", placement="target", relationship="impact", extra_anchor="target", rotate_safe=False, size=112),
    "stamp_at_rest": make_spec("classification_stamp", "AT REST classification imprint with clock-gold ink.", placement="target", relationship="impact", extra_anchor="target", rotate_safe=False, size=112),
    "reference_frame_grid": make_spec("reference_frame", "A moving local coordinate grid gives the target an explicit observational frame.", loop=True, placement="source", attachment="follow_source", relationship="sustain", extra_anchor="emitter", rotate_safe=False, size=122),
    "relative_velocity_arrows": make_spec("reference_frame", "Complementary velocity arrows change length to express frame-dependent motion.", placement="world", orientation="positive_x_is_reference_forward", mirror_x=True, relationship="active", size=118),
    "clock_sync": make_spec("time", "Two initially disagreeing clocks converge to a synchronized indication.", placement="world", relationship="active", size=118),
    "clock_desync": make_spec("time", "Two clocks diverge from a previously shared indication.", placement="target", relationship="active", extra_anchor="target", size=118),
    "proper_time_tick": make_spec("time", "A central proper-time clock remains the reference while exterior ticks slip around it.", loop=True, placement="source", attachment="follow_source", relationship="sustain", extra_anchor="emitter", rotate_safe=False, size=116),
    "mass_energy_exchange": make_spec("mass_energy", "Dense matter contracts while an energy packet expands, linked by a measured conversion arrow.", placement="world", orientation="positive_x_is_conversion_direction", mirror_x=True, relationship="release", size=126),
    "light_cone": make_spec("spacetime_diagram", "A clean event and light cone expand over restrained spacetime axes.", placement="target", relationship="active", extra_anchor="target", rotate_safe=False, size=132),
    "simultaneity_slice": make_spec("spacetime_diagram", "A simultaneity slice tilts through fixed event markers as reference-frame interpretation changes.", loop=True, placement="source", attachment="follow_source", relationship="sustain", extra_anchor="emitter", rotate_safe=False, size=128),
    "elevator_frame": make_spec("thought_experiment", "A compact elevator/reference cabin accelerates around a free marker.", placement="world", relationship="active", rotate_safe=False, size=126),
    "known_result_stamp": make_spec("bureaucratic_resolution", "Document-like known result receives a decisive authored check mark.", placement="target", relationship="aftermath", extra_anchor="target", rotate_safe=False, size=116),
}

ORIGINS = {name: (72.0, 72.0) for name, _, _ in ROWS}


def render(out_dir: str | Path, **opts):
    del opts
    return publish_catalog(
        target_name=TARGET_NAME,
        display_name="Patent Clerk Detached VFX",
        character_context_id="special_patent_clerk",
        character_context_display="Patent Clerk",
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
