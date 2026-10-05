"""Procedural "puppy slug" enemy sprite sheet.

A late-2010s deep-dream homage: an elongated slug-like body with a
chain of half-formed dog faces budding out of its dorsal ridge.
The hitbox / hurtbox is the whole body. The creature crawls along
floors and (in later animations) clings to walls and ceilings.

The sprite is intentionally a base "shape and weirdness" pass —
fur fractals and full dream-feedback texture are expected to come
from a shader fed this sheet as input. We commit to:

- a readable side silhouette (slug body + segmented dog-head bumps),
- enough internal palette variation that a fractal/noise shader has
  a useful base to perturb,
- jaundiced fur tones + glassy puppy eyes so the creature reads as
  "wrong dog" even before any post-processing.

Animations:
- `idle`:        breathing wobble while stationary.
- `crawl`:       full undulation cycle, body translates left→right
                 within the frame so the loop feels propulsive.
- `wall_crawl`:  same locomotion but the creature has rotated 90°
                 so its belly is against a vertical surface on its
                 LEFT. Used for climbing up a wall on the right
                 side of a room. (Game flips the sprite for the
                 other wall / ceiling — we don't bake those.)
- `ceiling_crawl`: belly up against a ceiling — full 180° flip
                 from `crawl`, but we still render it so the
                 dog-head bumps droop down toward the floor under
                 gravity, which a simple sprite flip wouldn't do.
- `hurt`:        recoil ripple. Body squashes, fur darkens.
- `death`:       deflating melt. The creature loses structure and
                 the dog faces dissolve back into the slug ridge.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageColor, ImageFilter

from ...authoring import rigdoc, shape_rig
from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "puppy_slug"
SHEET_FILES = [
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
]

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_puppy_slug",
        "display_name": "Puppy Slug",
    },
    "body": {
        "body_plan": "Crawler",
        "body_kind": "Crawler",
        "mass_class": "Light",
        "locomotion_hint": "Slither",
        "traits": ["enemy", "ai_era", "crawler", "no_hands", "wall_crawler"],
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": None,
            "climb": True,
            "fly": None,
            "swim": None,
            "crawl": True,
            "use_lifts": None,
            "door_access": [],
        },
        "interactions": {
            "talk": None,
            "trade": None,
            "carry": None,
            "open_doors": [],
        },
    },
    "brain": {"default_preset": "wanderer_puppy_slug"},
    "actions": {"default_preset": "peaceful_slither"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.wall_crawl": {"animation": "wall_walk", "events": []},
        "locomotion.ceiling_crawl": {"animation": "ceiling_walk", "events": []},
        "damage.hit": {"animation": "hurt", "events": []},
        "lifecycle.death": {"animation": "death", "events": []},
    },
    "sockets": {
        "mouth": {"source": "puppy_slug.geometry", "point": {"x": 96.0, "y": 48.0}},
        "head": {"source": "puppy_slug.geometry", "point": {"x": 96.0, "y": 40.0}},
        "belly": {"source": "puppy_slug.geometry", "point": {"x": 64.0, "y": 66.0}},
        "tail": {"source": "puppy_slug.geometry", "point": {"x": 28.0, "y": 58.0}},
        "wall_contact": {
            "source": "puppy_slug.geometry",
            "point": {"x": 64.0, "y": 72.0},
        },
    },
    "tags": ["enemy", "ai_era", "crawler"],
}

# Frame size: roomy enough that the dog-face bumps are legible
# (Crawlid-from-Hollow-Knight role: a small ground grunt with
# obvious silhouette readability). The creature still occupies
# only the central ~60% of the frame so wall/ceiling rotations
# fit comfortably. Auto-crop trims to silhouette so callers don't
# pay for the empty margin.
FRAME_SIZE = (128, 96)
SUPER = 4
W, H = FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER

# Row names match what the engine's `CharacterAnim::from_name` table
# accepts: `walk` → `CharacterAnim::Walk` is the locomotion slot the
# enemy animator picks whenever vel.x is non-zero. The `wall_walk`
# and `ceiling_walk` rows are kept in the sheet for a future surface-
# wrapping brain (they'd map to new `CharacterAnim::WallWalk` /
# `CeilingWalk` variants); the runtime currently drops them silently.
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 140),
    ("walk", 10, 90),
    ("wall_walk", 10, 95),
    ("ceiling_walk", 10, 95),
    ("hurt", 4, 70),
    ("death", 8, 110),
]

# ---- Palette -----------------------------------------------------------------
# Jaundiced fur with a hint of green-blue in the shadows — picked so a
# deep-dream feedback shader has hue room in both directions without
# washing out. Pup faces use a warmer, pinker tone so the bumps read as
# "faces" against the body even at small sizes.
PAL_BODY_DARK = "#3a2a1d"
PAL_BODY_MID = "#7a5a32"
PAL_BODY_LIGHT = "#c79a55"
PAL_BODY_HIGHLIGHT = "#f0d088"
PAL_BELLY = "#d8b58a"
PAL_PUP_FACE = "#b07845"
PAL_PUP_FACE_LIGHT = "#dca87a"
PAL_PUP_SNOUT = "#3e2218"
PAL_PUP_NOSE = "#1a0e08"
PAL_EYE_WHITE = "#f6efd9"
PAL_EYE_IRIS = "#6a3a14"
PAL_EYE_PUPIL = "#0c0604"
PAL_SLIME = "#a8c46a"
PAL_OUTLINE = "#1a0f08"


def _rgba(color: str, alpha: int = 255) -> RGBA:
    r, g, b = ImageColor.getrgb(color)
    return (r, g, b, alpha)


def _s(v: float) -> int:
    return int(round(v * SUPER))


def _pt(x: float, y: float) -> Tuple[int, int]:
    return (_s(x), _s(y))


def _box(x1: float, y1: float, x2: float, y2: float) -> Tuple[int, int, int, int]:
    return (_s(x1), _s(y1), _s(x2), _s(y2))


def _downsample(img: Image.Image) -> Image.Image:
    return rigdoc.downsampled_canvas(img, FRAME_SIZE, Image.Resampling.LANCZOS)


# ---- Geometry helpers --------------------------------------------------------


def _body_centerline(
    cx: float,
    cy: float,
    length: float,
    n: int,
    phase: float,
    wave_amp: float,
    wave_freq: float,
    pitch: float = 0.0,
) -> List[Point]:
    """Sample (x, y) along the slug centerline.

    The body is laid out left→right around `cx, cy`. `phase` shifts
    the wave so successive frames feel like the same body has moved
    along itself (propulsive undulation rather than a wobble in
    place). `pitch` tilts the whole line — used to make wall-crawl
    angle into the wall.
    """
    points: List[Point] = []
    half = length / 2.0
    cos_p = math.cos(pitch)
    sin_p = math.sin(pitch)
    for i in range(n):
        t = i / (n - 1)
        # Local (un-pitched) coords: x runs head→tail, y waves.
        lx = (t - 0.5) * length
        wave = math.sin(t * wave_freq * math.tau + phase) * wave_amp
        # Taper the wave at head + tail so the ends still feel anchored.
        edge_taper = math.sin(t * math.pi)
        ly = wave * (0.35 + 0.65 * edge_taper)
        # Apply pitch rotation around the body center.
        rx = lx * cos_p - ly * sin_p
        ry = lx * sin_p + ly * cos_p
        points.append((cx + rx, cy + ry))
    _ = half  # `length/2` is implicit in the parameterisation; keep symbol for readability.
    return points


def _segment_radius(t: float, base: float) -> float:
    """Body radius profile along the slug (t in [0, 1] head→tail)."""
    # Bulbous head, thicker mid, tapered tail. Three-lobed envelope
    # so a feedback shader has visible thickness gradients to chew on.
    head_lobe = math.exp(-((t - 0.06) ** 2) / 0.012)
    mid_lobe = math.exp(-((t - 0.55) ** 2) / 0.08)
    tail_taper = max(0.05, 1.0 - max(0.0, (t - 0.85) / 0.15) ** 2)
    return base * (0.65 + 0.55 * head_lobe + 0.40 * mid_lobe) * tail_taper


def _ring_points(
    center: Point, radius: float, normal: Point, n: int = 14
) -> List[Point]:
    """Approximate an ellipse perpendicular to `normal` for body shading."""
    nx, ny = normal
    # Tangent perpendicular to normal in 2D.
    tx, ty = -ny, nx
    pts = []
    for k in range(n):
        a = k / n * math.tau
        # Squashed perpendicular to the body — long axis along tangent,
        # short axis pinched along normal so it reads as a rim, not a circle.
        rx = math.cos(a) * radius * 1.0
        ry = math.sin(a) * radius * 0.55
        pts.append((center[0] + rx * tx + ry * nx, center[1] + rx * ty + ry * ny))
    return pts


# ---- Body drawing ------------------------------------------------------------
#
# The body is drawn as a rig: ``BODY_SEGMENTS`` bones along the waving
# centreline, each a tapered capsule painted once in its own frame and turned
# to its bone, as ``shape_rig.capsule`` draws a limb. Every bone's outline
# (and the slime trail under it) is placed first, then every bone's fill
# (mid tone, highlight band, belly band and fur tufts), so the bones join
# without a seam: a bone's fill starts square at its joint and covers the end
# of the bone before. A part flipbook stores each bone once and turns it.

BODY_SEGMENTS = 12
BODY_BASE_R = 10.0


def _tapered_capsule(d, length: float, r0: float, r1: float, fill: RGBA, start_cap: bool = True) -> None:
    """A capsule along +x from (0, 0) to (length, 0) (super pixels), radius
    ``r0`` at its start and ``r1`` at its end. Without ``start_cap`` the
    start is cut square at the joint."""
    if r0 <= 0 and r1 <= 0:
        return
    d.polygon([(0, -r0), (length, -r1), (length, r1), (0, r0)], fill=fill)
    if start_cap:
        d.ellipse((-r0, -r0, r0, r0), fill=fill)
    d.ellipse((length - r1, -r1, length + r1, r1), fill=fill)


class _Shifted:
    """A draw that adds ``(dx, dy)`` to every point it is given."""

    def __init__(self, d, dx: float, dy: float) -> None:
        self._d, self._dx, self._dy = d, dx, dy

    def polygon(self, pts, **kw):
        self._d.polygon([(x + self._dx, y + self._dy) for x, y in pts], **kw)

    def line(self, pts, **kw):
        self._d.line([(x + self._dx, y + self._dy) for x, y in pts], **kw)

    def ellipse(self, box, **kw):
        x0, y0, x1, y1 = box
        self._d.ellipse((x0 + self._dx, y0 + self._dy, x1 + self._dx, y1 + self._dy), **kw)


def _paint_segment(d, pad: float, k: int, length: float, layer: str, down_local: float, death_progress: float, trail_strength: float) -> None:
    """Bone ``k`` of the body (``layer`` "outline" or "fill"), its start at
    ``(pad, pad)`` of its raster and its axis along +x (super pixels)."""
    S = SUPER
    t0, t1 = k / BODY_SEGMENTS, (k + 1) / BODY_SEGMENTS
    shrink = 1.0 - 0.35 * death_progress
    r0 = _segment_radius(t0, BODY_BASE_R) * shrink * S
    r1 = _segment_radius(t1, BODY_BASE_R) * shrink * S
    L = length * S
    sd = _Shifted(d, pad, pad)
    if layer == "outline":
        if trail_strength > 0.01:
            img = d._img
            trail = Image.new("RGBA", img.size, (0, 0, 0, 0))
            td = _Shifted(blending_draw(trail), pad, pad)
            ya = down_local * (_segment_radius(t0, 9.0) - 1.0) * S
            yb = down_local * (_segment_radius(t1, 9.0) - 1.0) * S
            td.line([(0, ya), (L, yb)], fill=_rgba(PAL_SLIME, int(150 * trail_strength)), width=_s(2.4))
            img.alpha_composite(trail.filter(ImageFilter.GaussianBlur(radius=_s(0.9))))
        # Square at its start too: two bones' edges laid over each other
        # reduce apart and stack darker than the one edge they make.
        _tapered_capsule(sd, L, r0 + 0.8 * S, r1 + 0.8 * S, _rgba(PAL_OUTLINE), start_cap=k == 0)
        return
    # The mid tone starts square (but for the first bone): the bone before
    # ends its highlight band under it, and this bone's band starts round.
    _tapered_capsule(sd, L, r0, r1, _rgba(PAL_BODY_MID), start_cap=k == 0)
    _tapered_capsule(sd, L, r0 * 0.385, r1 * 0.385, _rgba(PAL_BODY_LIGHT))
    _tapered_capsule(sd, L, r0 * 0.22, r1 * 0.22, _rgba(PAL_BELLY, 230))
    # Fur tufts: short strokes along the ridge, at the old 28 samples. Each
    # keeps one length (the old per-frame wobble made every frame a new
    # picture).
    n = 28
    for i in range(2, n - 2):
        t = i / (n - 1)
        if not (t0 <= t < t1):
            continue
        x = (t - t0) * BODY_SEGMENTS * L
        r = _segment_radius(t, BODY_BASE_R) * S
        tuft = r * 0.7 * (0.6 + 0.4 * math.sin(i * 0.9)) * (1.0 - death_progress * 0.8)
        sd.line([(x - tuft / 2, 0), (x + tuft / 2, 0)], fill=_rgba(PAL_BODY_DARK), width=_s(1.1))


def _axis_point(p: dict, t: float) -> Point:
    """The centreline point at ``t`` (0 head, 1 tail) in frame pixels: the old
    ``_body_centerline`` with the old sag (which moved the outline along the
    axis) folded in."""
    pitch = p["pitch"]
    lx = (t - 0.5) * p["length"] + math.cos(2 * pitch) * p["sag"] * 0.45 * math.sin(t * math.pi)
    wave = math.sin(t * p["wave_freq"] * math.tau + p["phase"]) * p["wave_amp"]
    ly = wave * (0.35 + 0.65 * math.sin(t * math.pi))
    c, s = math.cos(pitch), math.sin(pitch)
    return (p["cx"] + lx * c - ly * s, p["cy"] + lx * s + ly * c)


def _centerline(p: dict, n: int = 28) -> List[Point]:
    return [_axis_point(p, i / (n - 1)) for i in range(n)]


def _place_body(img: Image.Image, p: dict) -> None:
    """The body (and its slime trail) as ``BODY_SEGMENTS`` turned bones of a
    fixed length: a squash (hurt, death) moves the bones closer together."""
    pitch = p["pitch"]
    # The belly side across the axis, in the bone's own frame.
    down_local = 1.0 if math.cos(2 * pitch) >= 0 else -1.0
    length = round(p["base_length"] / BODY_SEGMENTS, 2)
    # The bones change with the melt in four steps, and the trail is there or
    # not: each step is one set of pieces.
    dp = round(p["death_progress"] * 4) / 4
    trail = 0.45 if p["trail_strength"] > 0.2 else 0.0
    pad = (BODY_BASE_R * 1.6 + 4.0) * SUPER
    joints = [_axis_point(p, k / BODY_SEGMENTS) for k in range(BODY_SEGMENTS + 1)]
    for layer in ("outline", "fill"):
        for k in range(BODY_SEGMENTS):
            key = ("puppy_slug_bone", k, length, layer, down_local, dp, trail if layer == "outline" else 0)
            part = shape_rig.piece(
                key,
                (length * SUPER + 2 * pad, 2 * pad),
                (pad, pad),
                lambda d, k=k, layer=layer: _paint_segment(d, pad, k, length, layer, down_local, dp, trail),
            )
            a, b = joints[k], joints[k + 1]
            degrees = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
            shape_rig.place(img, part, (a[0] * SUPER, a[1] * SUPER), degrees, f"body_{layer}_{k}")


# ---- Puppy heads -------------------------------------------------------------


def _draw_pup_head(
    img: Image.Image,
    center: Point,
    radius: float,
    facing: float,
    eye_open: float,
    pitch: float,
    melt: float = 0.0,
    name: str = "pup_head",
) -> None:
    """One of the dog faces budding out of the dorsal ridge, as one piece.

    The face is painted once with its snout along the body's forward
    direction and turned to ``facing``. ``melt`` collapses the head back
    into the body for the death animation."""
    if melt >= 0.98:
        return
    radius = round(radius, 2)
    eye_open = round(eye_open, 2)
    melt = round(melt, 2)
    grav_x = math.sin(pitch + math.pi / 2.0)
    grav_y = math.cos(pitch + math.pi / 2.0)
    forward = math.atan2(-grav_y, -grav_x) - math.pi / 2.0
    half = radius * 2.4 * SUPER
    key = ("puppy_slug_head", radius, eye_open, melt, round(pitch, 4))
    part = shape_rig.piece(
        key,
        (2 * half, 2 * half),
        (half, half),
        lambda d: _paint_pup_head(d, (half / SUPER, half / SUPER), radius, forward, eye_open, pitch, melt),
    )
    shape_rig.place(img, part, (center[0] * SUPER, center[1] * SUPER), math.degrees(facing - forward), name)


def _paint_pup_head(
    d,
    center: Point,
    radius: float,
    facing: float,
    eye_open: float,
    pitch: float,
    melt: float,
) -> None:
    """The dog face centred on ``center`` (frame pixels of its own raster)."""
    cx, cy = center

    head_w = radius * 2.4 * (1.0 - 0.6 * melt)
    head_h = radius * 2.1 * (1.0 - 0.6 * melt)

    # Snout direction.
    sx = math.cos(facing)
    sy = math.sin(facing)
    # Perpendicular for ears.
    px = -sy
    py = sx

    # Skull base.
    d.ellipse(
        _box(
            cx - head_w / 2 - 0.5,
            cy - head_h / 2 - 0.5,
            cx + head_w / 2 + 0.5,
            cy + head_h / 2 + 0.5,
        ),
        fill=_rgba(PAL_OUTLINE),
    )
    d.ellipse(
        _box(cx - head_w / 2, cy - head_h / 2, cx + head_w / 2, cy + head_h / 2),
        fill=_rgba(PAL_PUP_FACE),
    )

    # Cheek highlight.
    d.ellipse(
        _box(
            cx - head_w * 0.3,
            cy - head_h * 0.10,
            cx + head_w * 0.18,
            cy + head_h * 0.32,
        ),
        fill=_rgba(PAL_PUP_FACE_LIGHT, 200),
    )

    if melt < 0.5:
        # Ears: two angled drops above the head. They use the
        # "up" direction (opposite gravity, modulated by snout).
        up_x = -math.sin(pitch)
        up_y = -math.cos(pitch)
        ear_base_left = (
            cx + (px * 0.55 - up_x * 0.05) * head_w * 0.30,
            cy + (py * 0.55 - up_y * 0.05) * head_h * 0.30,
        )
        ear_tip_left = (
            ear_base_left[0] + up_x * head_h * 0.55 + px * head_w * 0.15,
            ear_base_left[1] + up_y * head_h * 0.55 + py * head_h * 0.15,
        )
        ear_base_right = (
            cx + (-px * 0.55 - up_x * 0.05) * head_w * 0.30,
            cy + (-py * 0.55 - up_y * 0.05) * head_h * 0.30,
        )
        ear_tip_right = (
            ear_base_right[0] + up_x * head_h * 0.55 - px * head_w * 0.15,
            ear_base_right[1] + up_y * head_h * 0.55 - py * head_h * 0.15,
        )
        for base, tip in (
            (ear_base_left, ear_tip_left),
            (ear_base_right, ear_tip_right),
        ):
            tri = [
                (base[0] - px * head_w * 0.08, base[1] - py * head_w * 0.08),
                (base[0] + px * head_w * 0.08, base[1] + py * head_w * 0.08),
                tip,
            ]
            d.polygon(
                [_pt(*p) for p in tri],
                fill=_rgba(PAL_BODY_DARK),
                outline=_rgba(PAL_OUTLINE),
            )

    # Snout — fat oval extending from the face center along `facing`.
    if melt < 0.7:
        snout_cx = cx + sx * head_w * 0.40
        snout_cy = cy + sy * head_w * 0.40
        snout_r = head_w * 0.32 * (1.0 - melt)
        d.ellipse(
            _box(
                snout_cx - snout_r,
                snout_cy - snout_r * 0.75,
                snout_cx + snout_r,
                snout_cy + snout_r * 0.75,
            ),
            fill=_rgba(PAL_PUP_SNOUT),
            outline=_rgba(PAL_OUTLINE),
        )
        # Wet nose tip.
        nose_cx = snout_cx + sx * snout_r * 0.55
        nose_cy = snout_cy + sy * snout_r * 0.55
        nr = snout_r * 0.30
        d.ellipse(
            _box(nose_cx - nr, nose_cy - nr * 0.85, nose_cx + nr, nose_cy + nr * 0.85),
            fill=_rgba(PAL_PUP_NOSE),
        )
        # Mouth seam.
        m_a = (snout_cx - sx * snout_r * 0.05, snout_cy - sy * snout_r * 0.05)
        m_b = (
            snout_cx + sx * snout_r * 0.55 + px * snout_r * 0.10,
            snout_cy + sy * snout_r * 0.55 + py * snout_r * 0.10,
        )
        d.line([_pt(*m_a), _pt(*m_b)], fill=_rgba(PAL_OUTLINE), width=_s(0.8))

    # Eyes — two glassy beads. Eye-open lerps the pupil to a slit.
    if melt < 0.4:
        # Eye centers offset perpendicular to facing (sides of the muzzle).
        for sign in (-1.0, 1.0):
            ex = cx + sx * head_w * 0.05 + px * sign * head_w * 0.22
            ey = cy + sy * head_w * 0.05 + py * sign * head_w * 0.22
            er = head_w * 0.13
            d.ellipse(
                _box(ex - er, ey - er, ex + er, ey + er), fill=_rgba(PAL_EYE_WHITE)
            )
            ir = er * 0.65 * eye_open
            if ir > 0.01:
                # Iris drifts slightly toward snout direction.
                ix = ex + sx * er * 0.20
                iy = ey + sy * er * 0.20
                d.ellipse(
                    _box(ix - ir, iy - ir, ix + ir, iy + ir), fill=_rgba(PAL_EYE_IRIS)
                )
                pr = ir * 0.55
                d.ellipse(
                    _box(ix - pr, iy - pr, ix + pr, iy + pr), fill=_rgba(PAL_EYE_PUPIL)
                )
            else:
                # Closed-eye slit.
                d.line(
                    [_pt(ex - er * 0.8, ey), _pt(ex + er * 0.8, ey)],
                    fill=_rgba(PAL_EYE_PUPIL),
                    width=_s(0.8),
                )


def _pup_heads_along(
    centerline: List[Point],
    pitch: float,
    count: int,
    phase: float,
    head_scale: float = 1.0,
) -> List[Tuple[Point, float, float]]:
    """Pick mounting points on the dorsal ridge for pup heads.

    Returns a list of (center, radius, facing_angle) tuples.
    Heads are spaced evenly along the body but skip the very tail.
    """
    n = len(centerline)
    grav_x = math.sin(pitch + math.pi / 2.0)
    grav_y = math.cos(pitch + math.pi / 2.0)
    heads: List[Tuple[Point, float, float]] = []
    # Mount fractions along the body — keep heads out of the tail
    # and spread them across the front 75% so they overlap and feel
    # crowded (deep-dream "more faces than makes sense").
    fracs = [0.08 + i * (0.72 / max(1, count - 1)) for i in range(count)]
    for j, frac in enumerate(fracs):
        idx = int(frac * (n - 1))
        cx, cy = centerline[idx]
        t = idx / (n - 1)
        r = _segment_radius(t, base=10.0)
        # Each head bumps OPPOSITE gravity so they ride the dorsal ridge.
        # Plus a small wobble so they don't sit in a dead straight line.
        wobble = math.sin(phase * 2.0 + j * 1.2) * 1.2
        # Heads only lift ~half the body radius so they sit IN the
        # ridge, not on stalks. With the bigger head radius below,
        # this lets the heads visually merge with the body — the
        # whole dorsal line reads as a chain of fused faces.
        bump = r * 0.45 + wobble
        hx = cx - grav_x * bump
        hy = cy - grav_y * bump
        # Facing: lean slightly toward the head end of the slug (i.e. left),
        # blended with phase so heads turn as the body undulates. Wall-crawl
        # rotates this naturally through `pitch`.
        forward = math.atan2(-grav_y, -grav_x) - math.pi / 2.0  # along body, head-ward
        facing = forward + math.sin(phase + j * 0.8) * 0.35
        # Heads are MEANT to dominate — the silhouette of a puppy
        # slug is "row of dog faces on a tube," not "tube with
        # decorations." So head_r is comparable to body radius.
        head_r = (6.5 + 1.0 * math.sin(j * 1.3)) * head_scale
        heads.append(((hx, hy), head_r, facing))
    return heads


# ---- Per-animation params ----------------------------------------------------


def _params_for(anim: str, frame_idx: int, nframes: int):
    """Drive every per-frame variable from anim + frame."""
    t = frame_idx / max(1, nframes)
    tau = math.tau

    # Defaults: body sits horizontally, head end at left.
    cx = FRAME_SIZE[0] / 2.0
    cy = FRAME_SIZE[1] * 0.62
    # Shorter aspect ratio than a long slug — fat caterpillar feel.
    length = FRAME_SIZE[0] * 0.80
    base_length = length
    pitch = 0.0
    wave_amp = 0.7
    wave_freq = 1.6
    phase = t * tau
    fur_phase = t * tau * 0.6
    sag = 0.0
    eye_open = 1.0
    trail_strength = 0.35
    head_count = 2
    head_phase = phase
    head_scale = 1.0
    death_progress = 0.0
    body_translate = 0.0  # extra X translation applied to whole creature

    if anim == "idle":
        wave_amp = 0.6
        wave_freq = 1.2
        phase = math.sin(t * tau) * 0.7
        head_phase = math.sin(t * tau) * 0.5
        trail_strength = 0.25
        eye_open = 1.0
        sag = 0.6 + 0.4 * math.sin(t * tau)
    elif anim == "walk":
        wave_amp = 2.2
        wave_freq = 2.0
        # The body stays put in the frame: the game moves it. A crawl
        # across the frame (it was 14 px a loop, for a sheet previewed
        # end to end) is drawn on top of the game's own motion, and every
        # loop snapped the slug back by it.
        trail_strength = 0.55
        head_phase = phase
    elif anim == "wall_walk":
        # Belly on a vertical wall to the LEFT of the creature.
        # Rotate the entire body so head is up (-Y) and tail down (+Y).
        pitch = -math.pi / 2.0
        cx = FRAME_SIZE[0] * 0.62
        cy = FRAME_SIZE[1] / 2.0
        length = FRAME_SIZE[1] * 0.85
        base_length = length
        wave_amp = 1.8
        wave_freq = 2.0
        # Translate the creature up the wall over the loop.
        body_translate = 0.0
        trail_strength = 0.45
    elif anim == "ceiling_walk":
        # Upside-down. Gravity now sags the heads downward (toward floor).
        pitch = math.pi
        wave_amp = 2.0
        wave_freq = 2.0
        trail_strength = 0.40
        sag = 1.3  # heads droop visibly
    elif anim == "hurt":
        # Sharp squash + fur darkens.
        squash = math.sin(t * math.pi)
        wave_amp = 0.4
        wave_freq = 1.0
        length *= 1.0 - 0.18 * squash
        sag = 1.8 * squash
        trail_strength = 0.15
        eye_open = max(0.1, 1.0 - 1.5 * squash)
        head_count = 2
    elif anim == "death":
        # Deflating melt — body flattens, heads dissolve.
        death_progress = min(1.0, t * 1.15)
        wave_amp = 0.6 * (1.0 - death_progress)
        wave_freq = 1.4
        length *= 1.0 - 0.10 * death_progress
        sag = 2.6 + 3.5 * death_progress
        trail_strength = 0.6 * (1.0 - death_progress)
        eye_open = max(0.0, 1.0 - 2.2 * death_progress)
        head_count = max(1, int(round(2 * (1.0 - death_progress))))
        head_scale = max(0.2, 1.0 - 0.6 * death_progress)
    else:
        raise ValueError(f"unknown animation: {anim}")

    return {
        "cx": cx + body_translate * math.cos(pitch),
        "cy": cy + body_translate * math.sin(pitch),
        "length": length,
        "base_length": base_length,
        "pitch": pitch,
        "wave_amp": wave_amp,
        "wave_freq": wave_freq,
        "phase": phase,
        "fur_phase": fur_phase,
        "sag": sag,
        "eye_open": eye_open,
        "trail_strength": trail_strength,
        "head_count": head_count,
        "head_phase": head_phase,
        "head_scale": head_scale,
        "death_progress": death_progress,
    }


# ---- Renderer ----------------------------------------------------------------


def _render_internal(p: dict) -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    _place_body(img, p)
    heads = _pup_heads_along(
        _centerline(p),
        pitch=p["pitch"],
        count=p["head_count"],
        phase=p["head_phase"],
        head_scale=p["head_scale"],
    )
    for j, (center, radius, facing) in enumerate(heads):
        _draw_pup_head(
            img,
            center=center,
            radius=radius,
            facing=facing,
            eye_open=p["eye_open"],
            pitch=p["pitch"],
            melt=p["death_progress"],
            name=f"pup_head_{j}",
        )

    return _downsample(img)


def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    p = _params_for(animation, frame_idx, nframes)
    return _render_internal(p)


def render(out_dir: str | Path, **opts) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        label_width=120,
        actor_metadata=ACTOR_METADATA,
    )
    parts = publish_rig_flipbook(TARGET_NAME, ROWS, render_frame, outputs, frame_transform, Path(out_dir))
    return [
        outputs["canonical"],
        outputs["canonical_transparent"],
        outputs["spritesheet"],
        outputs["yaml"],
        outputs["ron"],
        outputs["actor"],
        outputs["preview"],
    ] + list(parts.values())
