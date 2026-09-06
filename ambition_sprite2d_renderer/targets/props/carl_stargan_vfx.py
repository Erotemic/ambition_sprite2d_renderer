"""Detached cosmic VFX authored for Carl Stargan.

These marks extend Carl's existing body-integrated cosmic effects with reusable
world/target/projectile-space sprites.  The language stays observational and
astronomical: sparse stars, pale-blue scale cues, orbital geometry, warm
planetary accents, and evidence/measurement marks rather than generic magic.
"""

from __future__ import annotations

import math
from pathlib import Path

from ._character_vfx_common import (
    Canvas,
    fade,
    make_spec,
    mix,
    publish_canonical,
    publish_catalog,
    pulse,
    sheet_files,
    smooth,
    window,
)

TARGET_NAME = "carl_stargan_vfx"
SHEET_FILES = sheet_files(TARGET_NAME)
FRAME_SIZE = (144, 144)

ROWS = [
    ("pale_blue_dot_ping", 8, 58),
    ("planetary_slingshot", 9, 48),
    ("cosmic_scale_zoom", 9, 52),
    ("starstuff_burst", 10, 52),
    ("nebula_breath", 12, 78),
    ("orbit_lock", 10, 56),
    ("evidence_ping", 8, 46),
    ("cosmic_calendar_sweep", 12, 52),
    ("voyager_signal", 10, 56),
    ("perspective_shift", 10, 44),
    ("constellation_resolve", 10, 60),
    ("horizon_arc", 9, 58),
]

OUTLINE = (22, 30, 50, 255)
OUTLINE_SOFT = (38, 50, 76, 220)
STAR_WHITE = (247, 244, 222, 255)
STAR_GOLD = (241, 201, 104, 255)
PALE_BLUE = (119, 192, 218, 255)
PALE_BLUE_HI = (204, 239, 245, 255)
NEBULA_BLUE = (72, 111, 171, 255)
NEBULA_VIOLET = (110, 87, 164, 255)
PLANET_OCHRE = (196, 145, 79, 255)
PLANET_RUST = (146, 78, 58, 255)
COSMIC_DARK = (22, 30, 50, 255)


def _stars(c: Canvas, center: tuple[float, float], count: int, radius: float, phase: float, alpha: float = 1.0) -> None:
    for i in range(count):
        a = phase * math.tau + i * 2.399963229728653
        rr = radius * (0.22 + 0.78 * ((i * 0.61803398875) % 1.0))
        p = (center[0] + math.cos(a) * rr, center[1] + math.sin(a) * rr * 0.72)
        color = STAR_GOLD if i % 3 else STAR_WHITE
        c.star(p, 1.5 + (i % 3) * 0.65, fade(color, alpha * (0.46 + 0.42 * pulse(phase + i / max(1, count)))), points=4)


def _planet(c: Canvas, p: tuple[float, float], radius: float, alpha: float = 1.0) -> None:
    c.ellipse(p, radius, radius, fade(PLANET_OCHRE, 0.88 * alpha), fade(OUTLINE, alpha), 1.0)
    c.arc(p, radius * 1.28, radius * 0.42, 188, 352, fade(STAR_GOLD, 0.72 * alpha), 1.1)
    c.ellipse((p[0] - radius * 0.28, p[1] - radius * 0.32), radius * 0.22, radius * 0.18, fade(STAR_WHITE, 0.42 * alpha))


def _pale_blue_dot_ping(c: Canvas, p: float) -> None:
    center = (72.0, 72.0)
    q = window(p, 0.28)
    c.ellipse(center, 3.0 + 0.7 * pulse(p), fill=PALE_BLUE, outline=PALE_BLUE_HI, width=0.8)
    for i in range(4):
        local = max(0.0, min(1.0, p * 1.55 - i * 0.12))
        radius = 11 + 16 * smooth(local)
        c.ellipse(center, radius, radius * 0.72, outline=fade(PALE_BLUE, q * (1.0 - local) * 0.62), width=1.0)
    _stars(c, center, 9, 38 * smooth(p), p * 0.15, 0.36 * q)


def _planetary_slingshot(c: Canvas, p: float) -> None:
    center = (65.0, 75.0)
    c.arc(center, 43, 31, 205, 520, fade(NEBULA_BLUE, 0.38), 1.1)
    a = math.radians(205 + 315 * smooth(p))
    pos = (center[0] + math.cos(a) * 43, center[1] + math.sin(a) * 31)
    _planet(c, pos, 6.2, 0.45 + 0.55 * window(p, 0.62))
    # Tangent streak communicates gravity assist rather than a generic orbit.
    tx, ty = -math.sin(a), math.cos(a) * 0.72
    for i, alpha in enumerate((0.72, 0.42, 0.22)):
        length = 15 + i * 8
        c.line([pos, (pos[0] - tx * length, pos[1] - ty * length)], fade(STAR_GOLD, alpha * window(p, 0.64)), 1.4 - i * 0.25)
    c.star(center, 3.1, fade(STAR_WHITE, 0.68), points=4)


def _cosmic_scale_zoom(c: Canvas, p: float) -> None:
    center = (72.0, 72.0)
    q = window(p, 0.42)
    for i in range(6):
        phase = (p * 1.35 + i * 0.17) % 1.0
        half = 9 + 56 * (1.0 - smooth(phase))
        color = PALE_BLUE if i % 2 == 0 else NEBULA_VIOLET
        c.rect((center[0] - half, center[1] - half * 0.72, center[0] + half, center[1] + half * 0.72), outline=fade(color, q * (0.18 + 0.55 * phase)), width=0.9)
    c.ellipse(center, 2.8, fill=PALE_BLUE_HI, outline=OUTLINE, width=0.6)
    c.star((center[0] + 17, center[1] - 13), 2.5 + 1.5 * pulse(p), fade(STAR_GOLD, 0.72 * q), points=4)


def _starstuff_burst(c: Canvas, p: float) -> None:
    center = (72.0, 72.0)
    q = window(p, 0.35)
    spread = 12 + 54 * smooth(p)
    for arm in range(4):
        pts = []
        for i in range(15):
            a = arm * math.pi / 2 + i * 0.30 + p * math.tau * 0.42
            r = (i / 14) * spread
            pts.append((center[0] + math.cos(a) * r, center[1] + math.sin(a) * r * 0.66))
        c.line(pts, fade(NEBULA_BLUE if arm % 2 == 0 else NEBULA_VIOLET, 0.28 * q), 1.0)
    _stars(c, center, 30, spread, -p * 0.23, 0.72 * q)
    c.star(center, 4.5 + 3.0 * pulse(p), fade(STAR_WHITE, 0.86 * q), points=6, outline=fade(STAR_GOLD, 0.66 * q))


def _nebula_breath(c: Canvas, p: float) -> None:
    center = (72.0, 72.0)
    breathe = 0.5 + 0.5 * math.sin(math.tau * p)
    for i in range(7):
        a = i * math.tau / 7 + p * 0.38
        rr = 12 + i * 5.5
        pt = (center[0] + math.cos(a) * rr, center[1] + math.sin(a) * rr * 0.55)
        r = 13 + (i % 3) * 5 + breathe * 4
        color = NEBULA_BLUE if i % 2 == 0 else NEBULA_VIOLET
        c.ellipse(pt, r, r * 0.62, fill=fade(color, 0.055 + 0.035 * breathe), outline=fade(color, 0.15 + 0.08 * breathe), width=0.8)
    _stars(c, center, 15, 52, p * 0.07, 0.40)


def _orbit_lock(c: Canvas, p: float) -> None:
    center = (72.0, 72.0)
    q = smooth(p)
    angles = (18 * (1 - q), 54 * (1 - q), 93 * (1 - q))
    radii = ((51, 24), (39, 37), (28, 51))
    for i, ((rx, ry), tilt) in enumerate(zip(radii, angles)):
        # PIL has axis-aligned ellipses; segmented points give us tilted orbital tracks.
        pts = []
        phi = math.radians(tilt)
        for j in range(49):
            a = j * math.tau / 48
            x = math.cos(a) * rx
            y = math.sin(a) * ry
            pts.append((center[0] + x * math.cos(phi) - y * math.sin(phi), center[1] + x * math.sin(phi) + y * math.cos(phi)))
        c.line(pts, fade((PALE_BLUE, NEBULA_VIOLET, STAR_GOLD)[i], 0.28 + 0.42 * q), 1.0)
        a = p * math.tau * (1.0 + i * 0.18) + i * 2.0
        x = math.cos(a) * rx
        y = math.sin(a) * ry
        pt = (center[0] + x * math.cos(phi) - y * math.sin(phi), center[1] + x * math.sin(phi) + y * math.cos(phi))
        c.ellipse(pt, 3.0 + i, fill=fade((PALE_BLUE, PLANET_OCHRE, STAR_GOLD)[i], 0.9), outline=OUTLINE_SOFT, width=0.7)
    c.star(center, 4.2 + 1.8 * pulse(p), STAR_WHITE, points=4)


def _evidence_ping(c: Canvas, p: float) -> None:
    center = (72.0, 72.0)
    q = window(p, 0.30)
    radius = 46 - 31 * smooth(min(1.0, p * 1.3))
    c.ellipse(center, radius, radius, outline=fade(PALE_BLUE_HI, 0.72 * q), width=1.1)
    gap = radius + 6
    c.line([(center[0] - gap - 10, center[1]), (center[0] - gap, center[1])], fade(STAR_GOLD, q), 1.2)
    c.line([(center[0] + gap, center[1]), (center[0] + gap + 10, center[1])], fade(STAR_GOLD, q), 1.2)
    c.line([(center[0], center[1] - gap - 10), (center[0], center[1] - gap)], fade(STAR_GOLD, q), 1.2)
    c.line([(center[0], center[1] + gap), (center[0], center[1] + gap + 10)], fade(STAR_GOLD, q), 1.2)
    if p > 0.42:
        r = 3.2 + 4.0 * smooth((p - 0.42) / 0.58)
        c.star(center, r, fade(STAR_WHITE, q), points=4, outline=fade(PALE_BLUE, q))


def _cosmic_calendar_sweep(c: Canvas, p: float) -> None:
    center = (72.0, 72.0)
    q = window(p, 0.55)
    for i in range(12):
        start = -90 + i * 30
        reached = p * 12 - i
        alpha = 0.16 if reached < 0 else 0.76 if reached > 0.25 else 0.16 + max(0.0, reached) * 2.4
        color = NEBULA_VIOLET if i < 5 else NEBULA_BLUE if i < 9 else STAR_GOLD
        c.arc(center, 26 + i * 2.2, 26 + i * 2.2, start + 3, start + 24, fade(color, alpha * q), 2.3)
    c.ellipse(center, 15, outline=fade(PALE_BLUE, 0.42 * q), width=1.0)
    c.star((72, 72), 3.5, fade(STAR_WHITE, 0.78 * q), points=4)


def _voyager_signal(c: Canvas, p: float) -> None:
    origin = (31.0, 75.0)
    q = window(p, 0.42)
    c.star(origin, 3.3, fade(STAR_GOLD, q), points=4)
    for i in range(4):
        local = (p * 1.25 - i * 0.12)
        if local <= 0:
            continue
        radius = 11 + 18 * min(1.0, local)
        c.arc(origin, radius, radius, -55, 55, fade(PALE_BLUE_HI, q * (1.0 - 0.55 * min(1.0, local))), 1.4)
    for i, pt in enumerate(((92, 45), (105, 67), (116, 91), (94, 105))):
        c.star(pt, 1.8 + (i % 2) * 0.8, fade(STAR_WHITE, 0.35 + 0.35 * pulse(p + i * 0.17)), points=4)
    c.line([(40, 75), (121, 75)], fade(NEBULA_BLUE, 0.12 * q), 0.7)


def _perspective_shift(c: Canvas, p: float) -> None:
    center = (72.0, 72.0)
    q = window(p, 0.52)
    for i in range(22):
        a = i * 2.399963 + 0.17
        base = 6 + (i % 7) * 4.7
        r0 = base + 58 * smooth(p) * (0.3 + (i % 5) / 7)
        r1 = max(2.0, r0 - (7 + i % 4 * 4) * q)
        end = (center[0] + math.cos(a) * r0, center[1] + math.sin(a) * r0 * 0.72)
        start = (center[0] + math.cos(a) * r1, center[1] + math.sin(a) * r1 * 0.72)
        c.line([start, end], fade(PALE_BLUE if i % 3 else STAR_GOLD, 0.28 + 0.44 * q), 0.7 + (i % 3) * 0.25)
    c.ellipse(center, 4.2, fill=fade(COSMIC_DARK, 0.72), outline=fade(STAR_WHITE, 0.55 * q), width=0.8)


def _constellation_resolve(c: Canvas, p: float) -> None:
    nodes = [(28, 83), (43, 47), (67, 62), (83, 33), (103, 52), (116, 88), (91, 105), (56, 106)]
    edges = [(0, 1), (1, 2), (2, 3), (2, 4), (4, 5), (5, 6), (6, 7), (7, 2)]
    q = window(p, 0.55)
    for i, (a, b) in enumerate(edges):
        local = max(0.0, min(1.0, p * 1.7 - i * 0.09))
        if local <= 0:
            continue
        ax, ay = nodes[a]
        bx, by = nodes[b]
        end = (ax + (bx - ax) * smooth(local), ay + (by - ay) * smooth(local))
        c.line([(ax, ay), end], fade(NEBULA_BLUE, 0.52 * q), 1.0)
    for i, node in enumerate(nodes):
        appear = max(0.0, min(1.0, p * 2.2 - i * 0.055))
        c.star(node, 2.1 + (i % 3) * 0.7, fade(STAR_GOLD if i % 3 else STAR_WHITE, appear * q), points=4)


def _horizon_arc(c: Canvas, p: float) -> None:
    q = window(p, 0.48)
    center = (72.0, 109.0)
    radius = 55 + 6 * smooth(p)
    c.arc(center, radius, 37, 195, 345, fade(PALE_BLUE, 0.34 * q), 2.0)
    c.arc(center, radius - 5, 31, 203, 337, fade(PLANET_RUST, 0.38 * q), 3.0)
    x = 72 + math.cos(math.radians(250 + 40 * smooth(p))) * radius
    y = 109 + math.sin(math.radians(250 + 40 * smooth(p))) * 37
    c.star((x, y), 4.0 + 4.0 * pulse(p * 0.7), fade(STAR_GOLD, q), points=6, outline=fade(STAR_WHITE, 0.72 * q))
    _stars(c, (72, 58), 10, 52, p * 0.05, 0.32 * q)


DRAWERS = {
    "pale_blue_dot_ping": _pale_blue_dot_ping,
    "planetary_slingshot": _planetary_slingshot,
    "cosmic_scale_zoom": _cosmic_scale_zoom,
    "starstuff_burst": _starstuff_burst,
    "nebula_breath": _nebula_breath,
    "orbit_lock": _orbit_lock,
    "evidence_ping": _evidence_ping,
    "cosmic_calendar_sweep": _cosmic_calendar_sweep,
    "voyager_signal": _voyager_signal,
    "perspective_shift": _perspective_shift,
    "constellation_resolve": _constellation_resolve,
    "horizon_arc": _horizon_arc,
}

SPECS = {
    "pale_blue_dot_ping": make_spec("observation", "Tiny pale-blue world emphasized by restrained observation rings.", placement="target", relationship="active", extra_anchor="target", size=76),
    "planetary_slingshot": make_spec("orbital", "Planet sweeps a gravity-assist arc and exits on a bright tangent.", placement="world", orientation="positive_x_is_forward_after_tangent", mirror_x=True, relationship="release", size=118),
    "cosmic_scale_zoom": make_spec("scale", "Nested observation frames collapse many scales onto one marked point.", placement="target", relationship="startup", extra_anchor="target", size=122),
    "starstuff_burst": make_spec("stellar", "Loose spiral arms and star grains bloom from a shared stellar origin.", placement="world", blend="alpha_or_additive", relationship="impact", size=126),
    "nebula_breath": make_spec("ambient_cosmic", "Slow periodic nebula curls and sparse stars for sustained cosmic presence.", loop=True, placement="source", blend="alpha_or_additive", attachment="follow_source", relationship="sustain", extra_anchor="emitter", size=124),
    "orbit_lock": make_spec("orbital", "Several initially misaligned orbital tracks settle into one coherent center.", placement="target", relationship="active", extra_anchor="target", size=126),
    "evidence_ping": make_spec("observation", "Instrument-like reticle contracts onto a point and resolves as a clean glint.", placement="target", relationship="impact", extra_anchor="target", size=104),
    "cosmic_calendar_sweep": make_spec("time_scale", "Segmented radial chronology races toward a bright terminal era.", placement="world", relationship="active", size=126),
    "voyager_signal": make_spec("signal", "Sparse scientific radio arcs propagate from an authored emitter toward distant stars.", placement="source", orientation="positive_x_is_forward", mirror_x=True, relationship="release", extra_anchor="emitter", size=124),
    "perspective_shift": make_spec("scale", "Radial parallax streaks imply an enormous change of observational scale.", placement="world", relationship="release", size=132),
    "constellation_resolve": make_spec("evidence", "Independent stars connect into a legible constellation as evidence accumulates.", placement="world", relationship="aftermath", size=126),
    "horizon_arc": make_spec("planetary", "Planetary horizon and restrained sunrise glint for discovery, arrival, or recovery beats.", placement="world", relationship="aftermath", size=130),
}

ORIGINS = {name: (72.0, 72.0) for name, _, _ in ROWS}
ORIGINS["voyager_signal"] = (31.0, 75.0)
ORIGINS["horizon_arc"] = (72.0, 109.0)


def render(out_dir: str | Path, **opts):
    del opts
    return publish_catalog(
        target_name=TARGET_NAME,
        display_name="Carl Stargan Detached VFX",
        character_context_id="npc_carl_stargan",
        character_context_display="Carl Stargan",
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
