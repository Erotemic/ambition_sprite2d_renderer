"""Robot melee slash effect — a broad, readable Hollow-Knight-style sweep.

The game sizes this effect to the resolved melee hitbox and selects a row for
the attack pose. The runtime rotates rows only with the gravity frame and uses
a local horizontal mirror for left-facing side attacks, so facing never turns
the asymmetric accent layers upside down.

The five-frame, 100 ms rows match the melee ACTIVE window exactly, and begin in
the fully active state for Hollow-Knight-like responsiveness:

- impact: a broad white cut is already out on frame 0,
- follow-through: the same readable footprint starts to contract,
- dissipate: the sweep shrinks and feathers,
- release: the remaining energy thins quickly,
- clear: transparent.

``side`` is the broad forward/back swoop, ``up`` and ``down`` are the same
attack language above or below the body, and ``poke`` is the intentionally odd
grounded down-tilt thrust.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from ...authoring.sheet_build import build_sheet
from ...core import slash_envelope
from ambition_sprite2d_renderer.core.draw import blending_draw

TARGET_NAME = "robot_slash"
SHEET_FILES = (
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
)

FRAME_SIZE = (160, 160)
SUPER = 4
# 5 frames x 20 ms = 100 ms, matching `SwipeSpec.active_s = 0.10` so the
# visible effect and damaging window end together.
ROWS: List[Tuple[str, int, int]] = [
    ("side", 5, 20),
    ("up", 5, 20),
    ("down", 5, 20),
    ("poke", 5, 20),
]

# Pale blue ramp: keep even the deepest stop in mid blue so the effect reads as
# motion rather than a solid dark object.
CORE = (255, 255, 255, 255)
HOT = (240, 251, 255, 255)
BODY = (206, 238, 255, 255)
EDGE = (150, 205, 245, 255)
DEEP = (96, 158, 214, 255)


def _px(value: float) -> float:
    return value * SUPER


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _smoothstep(edge0: float, edge1: float, value: float) -> float:
    if edge0 == edge1:
        return 1.0 if value >= edge1 else 0.0
    t = _clamp((value - edge0) / (edge1 - edge0))
    return t * t * (3.0 - 2.0 * t)


def _phase(t: float) -> str:
    if t < 0.18:
        return "impact"
    if t < 0.44:
        return "follow_through"
    if t < 0.72:
        return "dissipate"
    if t < 0.95:
        return "release"
    return "clear"


def _amplitude(t: float) -> float:
    if t <= 0.56:
        return _lerp(1.0, 0.82, _smoothstep(0.0, 0.56, t))
    return 0.82 * (1.0 - _smoothstep(0.62, 1.0, t))


# ── The swept region, in SWING SPACE ─────────────────────────────────────────
#
# The frame IS the swing: `x = 0` is the body, `x = REACH` the tip, and `y` runs
# across the arc about `AXIS_Y`. `SwingShape` hands the renderer a quad with
# exactly those axes, so art authored here lands ON the hit polygon rather than
# near it.
#
# Keep all visible art inside the hit polygon. The polygon expands the shared
# envelope by its margin, leaving room for the visual blur without drawing a
# non-damaging edge.
#  THE FRAME IS THE SWING, and its size is DERIVED, not restated.
#
# The runtime stretches this frame into the quad it computes from the hit
# POLYGON, so the frame's width is the polygon's extent and its half-height is
# the polygon's widest station. Naming pixel sizes here was therefore naming the
# polygon's numbers a second time in different units, and they had already
# drifted: the polygon stopped its swing at 0.96 of reach while this file drew
# to 1.0.
#
# `SwingDescriptor` is the one spelling both read. When a second character gets
# its own sheet this becomes a parameter rather than a module constant, which is
# what makes sharing an effect mean sharing the RECIPE — the same generator run
# against another character's descriptor, drawing for ITS volume.
SWING = slash_envelope.PLAYER_ROBOT_SWING
AXIS_Y = FRAME_SIZE[1] / 2.0
REACH = float(FRAME_SIZE[0])
PEAK_HALF = SWING.art_peak_half(FRAME_SIZE[1])
# The art's own margin at the two ENDS, where the envelope narrows and no
# perpendicular inset can help: the polygon closes to a point there, so the
# effect starts and stops slightly inside it.
T_INSET_NEAR = 0.05
T_INSET_FAR = 0.06


def _scaled(points):
    return [(_px(x), _px(y)) for x, y in points]


def _half_at(t: float) -> float:
    """Half-height of the swept region a fraction `t` along the swing.

    ⚠ THIS WAS A MEASURED TABLE and the table is why the effect wobbled. It
    sampled the polygon's profile off a rasterised scan, which imported the
    scan's 1-pixel quantisation as ripple, and then ran a spline through the
    noise — a wobble with extra steps. The analytic envelope cannot ripple:
    there is nothing between the samples to disagree with.

    The descriptor's `tip` is folded in because the frame maps to the QUAD, and
    the quad spans the polygon's extent — which stops at the blunt tip, not at
    t=1.
    """
    # SHORTENED at both ends, not remapped. The envelope goes to zero at the
    # body and at the tip, so the polygon comes to a point there and no amount
    # of perpendicular margin can contain a blurred pixel drawn past it —
    # widening the container from 1.07 to 1.16 moved the leak by 0.03%. The art
    # instead occupies a slightly shorter span of the frame and reaches zero
    # width INSIDE the volume's points.
    u = (t - T_INSET_NEAR) / max(1e-6, 1.0 - T_INSET_NEAR - T_INSET_FAR)
    if u < 0.0 or u > 1.0:
        return 0.0
    return slash_envelope.half_at(u * SWING.tip) * PEAK_HALF


def _envelope_outline(width_scale: float = 1.0, samples: int = 96):
    """The swept region's outline, in swing space. Dense: this is ART."""
    top = []
    bottom = []
    for i in range(samples + 1):
        u = i / samples
        x = REACH * u
        half = _half_at(u) * width_scale
        top.append((x, AXIS_Y - half))
        bottom.append((x, AXIS_Y + half))
    return top + list(reversed(bottom))


# How far back the blade's horns sit from its point, as a fraction of reach. The
# leading edge is a curve between them.
HORN_PULL = SWING.horn_pull


def _far_edge_x(dy: float, width_scale: float) -> float:
    """The BLADE's leading edge at height `dy` off the axis — a smooth curve.

    ⚠ NOT the polygon's front. The polygon ends in a blunt vertical chord,
    because it is a coarse convex container and a chord is the cheapest honest
    way to close one. Following that chord with the bright edge drew a straight
    vertical line down the middle of the swing with curves only at the top and
    bottom — the "weird tip" and the jaggedness, in a shape whose every
    definition is smooth.
    
    So the art gets its own front: a parabola from the point back to the horns.
    It is inside the chord everywhere except its single tangent point, so
    containment is unaffected and nothing drawn is straight.
    """
    half = max(1e-6, PEAK_HALF * width_scale)
    k = _clamp(abs(dy) / half)
    # A hair short of the polygon's blunt chord, so the bright edge never lands
    # exactly on it — a tangent there shows as a small flat tick at the point.
    tip_x = REACH * SWING.tip * 0.98
    return tip_x - (tip_x * HORN_PULL) * k * k


def _blade_gradient(size, width_scale: float, trail: float) -> Image.Image:
    """A RIBBON behind the leading edge: constant width, smooth everywhere.

    The blade is the front of the swing, and what follows it is the air it came
    through. So brightness is a function of one thing — how far a pixel sits
    BEHIND the analytic leading edge — and `trail` is how long the wake is.

    ⚠ This is the third fill this effect has had, and the reason each previous
    one failed is worth keeping. Nested polygons in stepped colours gave a solid
    lens with hard edges between the layers ("angles in the vfx"). A per-row
    normalised ramp gave smooth colour but stepped between rows ("still feels
    like the arc is jagged"). A closed-form distance behind a closed-form edge
    has neither: no layer boundaries and no rows.
    """
    w, h = size
    grad = Image.new("L", size, 0)
    px = grad.load()
    sx = w / FRAME_SIZE[0]
    sy = h / FRAME_SIZE[1]
    trail_px = trail * sx
    for row in range(h):
        dy = row / sy - AXIS_Y
        fx = _far_edge_x(dy, width_scale)
        if fx < 0.0:
            continue
        fx *= sx
        lo = max(0, int(fx - trail_px))
        hi = min(w - 1, int(fx))
        for col in range(lo, hi + 1):
            # 1 at the blade, 0 a full trail behind it. Squared so the bright
            # core hugs the edge and the wake stays a wash.
            k = 1.0 - (fx - col) / max(1e-6, trail_px)
            # A FLOOR under the wake. Falling to zero left the near half of the
            # swing invisible again at a glance, which is the original
            # complaint; a fifth of full alpha keeps the whole swept region
            # faintly lit and blue, and reads as air the blade came through.
            px[col, row] = int(255 * (0.20 + 0.80 * _clamp(k) ** 1.7))
    return grad


def _arc_state(t: float) -> dict:
    shrink = _smoothstep(0.0, 0.82, t)
    release = _smoothstep(0.62, 1.0, t)
    return {
        "progress": _lerp(1.0, 0.58, shrink),
        "width": _lerp(60.0, 16.0, shrink) * _lerp(1.0, 0.74, release),
        "amp": _amplitude(t),
        "release": release,
    }


def _draw_sweep_frame(t: float) -> Image.Image:
    """One frame of the slash: a blade edge with a trail behind it.

    The whole swept region carries ink — that is the fix for "a big empty part
    of the hitpoly ... there is no vfx to indicate to the user that it would"
    hit — but its brightness is a smooth ramp toward the leading edge rather
    than a stack of filled shapes, so it reads as a swing and not as an object.
    """
    state = _arc_state(t)
    amp = state["amp"]
    size = (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    if amp <= 0.01:
        return canvas.resize(FRAME_SIZE, Image.Resampling.LANCZOS)

    release = state["release"]
    width_scale = _lerp(1.0, 0.88, release)
    # The trail retreats toward the blade as the swing spends: early frames are
    # a full sweep, late ones a thin leading line.
    # How far the wake reaches back from the blade, in frame units. It starts
    # long enough to cover the swept region — the whole point is that the part
    # of the polygon nearest the player visibly hurts — and shortens to a thin
    # leading line as the swing spends.
    trail = _lerp(REACH * 0.92, REACH * 0.30, _smoothstep(0.0, 0.9, t))

    mask = Image.new("L", size, 0)
    # raw-draw-ok: `mask` is mode "L". The gnu_ton rule is about ImageDraw
    # REPLACING a destination's alpha; a single-channel mask has no alpha
    # channel, and replacing its coverage value is exactly what a mask wants.
    ImageDraw.Draw(mask).polygon(_scaled(_envelope_outline(width_scale)), fill=255)  # raw-draw-ok
    grad = _blade_gradient(size, width_scale, trail)
    grad = grad.filter(ImageFilter.GaussianBlur(radius=int(1.2 * SUPER)))
    grad = ImageChops.multiply(grad, mask)

    # Colour by the same ramp: the deep stop far from the edge, white at it.
    # Alpha carries the fade independently of hue. Keep the wake in visible
    # mid blues and reserve near-white for the final edge.
    stops = ((0.00, DEEP), (0.35, EDGE), (0.72, BODY), (0.90, HOT), (1.00, CORE))
    ramp = []
    for i in range(256):
        k = i / 255.0
        lo, hi = stops[0], stops[-1]
        for a, b in zip(stops, stops[1:]):
            if a[0] <= k <= b[0]:
                lo, hi = a, b
                break
        f = (k - lo[0]) / max(1e-6, hi[0] - lo[0])
        ramp.append(tuple(int(_lerp(lo[1][c], hi[1][c], f)) for c in range(3)))

    gpx = grad.load()
    cpx = canvas.load()
    for y in range(size[1]):
        for x in range(size[0]):
            v = gpx[x, y]
            if v == 0:
                continue
            r, g, b = ramp[v]
            cpx[x, y] = (r, g, b, int(v * amp))
    return canvas.resize(FRAME_SIZE, Image.Resampling.LANCZOS)


#  `up` and `down` are NOT pre-rotated any more, and that is a contract change
# shared with `slash_visuals.rs`.
#
# The rows used to be drawn turned a quarter turn because the renderer added a
# per-pose rotation offset on top of the swing direction — an up-swing came out
# at rotation zero, so its artwork had to be drawn already pointing up. That was
# coherent when the sprite was a SQUARE: rotating a square changes nothing about
# which side is long.
#
# It stopped being coherent when the quad became the swing's own extent. The
# renderer sizes the sprite (length along the swing, width across it) on the
# sprite's LOCAL axes, so a row drawn a quarter turn out has its long dimension
# across the swing instead of along it — measured at 8.8% of the drawn ink
# landing outside the volume for the up attacks and 9.2% for the down.
#
# So: every row is drawn in swing space, and orientation is the swing axis
# alone. `pose` now selects WHICH artwork, never how it is turned.
def _draw_up_frame_raw(t: float) -> Image.Image:
    return _draw_sweep_frame(t)


def _draw_down_frame_raw(t: float) -> Image.Image:
    return _draw_sweep_frame(t)


def _poke_polygon(progress: float, width_scale: float = 1.0):
    """Draw the down-tilt as a straight thrust in swing space.

    The long lens emphasizes reach rather than area. It fills the thin hit-volume
    quad vertically so the visible thrust is not narrower than the damaging one.
    """
    # Inside the volume, like every other row: the thrust's polygon is
    # parallel-sided at the quad's own half-height, so art drawn at the frame
    # edge leaks the moment the halo blurs. 0.86 leaves the blur somewhere to go.
    x0 = 0.06 * REACH
    x1 = x0 + (REACH * 0.90 - x0) * _clamp(progress, 0.30, 1.0)
    half = 69.0 * width_scale
    return [
        (x0, AXIS_Y - half * 0.62),
        (x0 + (x1 - x0) * 0.22, AXIS_Y - half),
        (x0 + (x1 - x0) * 0.82, AXIS_Y - half * 0.78),
        (x1, AXIS_Y),
        (x0 + (x1 - x0) * 0.82, AXIS_Y + half * 0.78),
        (x0 + (x1 - x0) * 0.22, AXIS_Y + half),
        (x0, AXIS_Y + half * 0.62),
    ]


def _draw_poke_frame_raw(t: float) -> Image.Image:
    shrink = _smoothstep(0.0, 0.82, t)
    release = _smoothstep(0.62, 1.0, t)
    progress = _lerp(1.0, 0.62, shrink)
    amp = _amplitude(t)

    size = (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    if amp <= 0.01:
        return canvas.resize(FRAME_SIZE, Image.Resampling.LANCZOS)

    halo = Image.new("RGBA", size, (0, 0, 0, 0))
    blending_draw(halo).polygon(
        _scaled(_poke_polygon(progress, 1.0)),
        fill=(EDGE[0], EDGE[1], EDGE[2], int(120 * amp)),
    )
    halo = halo.filter(ImageFilter.GaussianBlur(radius=int(3.0 * SUPER)))
    canvas.alpha_composite(halo)

    draw = blending_draw(canvas)
    for width_scale, color, alpha in (
        (0.94, DEEP, 220),
        (0.74, BODY, 238),
        (0.48, HOT, 250),
        (0.20, CORE, 255),
    ):
        draw.polygon(
            _scaled(_poke_polygon(progress, width_scale * _lerp(1.0, 0.82, release))),
            fill=(color[0], color[1], color[2], int(alpha * amp)),
        )
    return canvas.resize(FRAME_SIZE, Image.Resampling.LANCZOS)


def _draw_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    t = frame_idx / max(1, frame_count - 1)
    if animation == "up":
        image = _draw_up_frame_raw(t)
    elif animation == "down":
        image = _draw_down_frame_raw(t)
    elif animation == "poke":
        image = _draw_poke_frame_raw(t)
    else:
        image = _draw_sweep_frame(t)
    # NO global rotation. Every row above is drawn in SWING SPACE — x is the
    # swing axis, which is the axis `SwingShape` hands the renderer — so a
    # blanket 90-degree turn here would put the art across its own hitbox.
    return image


def _frame_meta(animation: str, frame_idx: int, frame_count: int) -> dict:
    t = frame_idx / max(1, frame_count - 1)
    # Swing space: every row runs body -> tip along +x about the axis. `up` and
    # `down` are the side sweep turned a quarter turn by `_draw_*_frame_raw`,
    # so their anchors turn with them.
    anchors = {
        "side": ((0.0, AXIS_Y), (REACH, AXIS_Y)),
        "up": ((AXIS_Y, FRAME_SIZE[1] - 2.0), (AXIS_Y, FRAME_SIZE[1] - REACH)),
        "down": ((AXIS_Y, 2.0), (AXIS_Y, REACH)),
        "poke": ((0.0, AXIS_Y), (REACH, AXIS_Y)),
    }
    origin, tip = anchors[animation]
    return {
        "anchors": {
            "origin": {"x": origin[0], "y": origin[1]},
            "tip": {"x": tip[0], "y": tip[1]},
        },
        "effect": {
            "kind": animation,
            "progress": round(t, 4),
            "phase": _phase(t),
            "intensity": round(_amplitude(t), 4),
        },
    }


ACTOR_METADATA = {
    "actor": {"character_id": "fx_robot_slash", "display_name": "Robot Slash"},
    "body": {
        "body_plan": "Effect",
        "body_kind": "Slash",
        "locomotion_hint": "Stationary",
        "traits": ["fx", "slash", "melee", "overlay"],
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "animation_bindings": {
        "default": {"animation": "side", "events": []},
        "action.melee.side": {"animation": "side", "events": []},
        "action.melee.up": {"animation": "up", "events": []},
        "action.melee.down_air": {"animation": "down", "events": []},
        "action.melee.down_tilt": {"animation": "poke", "events": []},
    },
    "sockets": {
        "origin": {
            "source": f"{TARGET_NAME}.geometry",
            "point": {"x": 78.0, "y": 12.0},
        },
    },
    "tags": ["fx", "slash", "melee", "overlay"],
}


def render(out_dir: str | Path, **opts) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=_draw_frame,
        out_dir=out_dir,
        frame_size=opts.get("frame_size") or FRAME_SIZE,
        frame_meta_fn=_frame_meta,
        auto_crop=False,
        actor_metadata=ACTOR_METADATA,
    )
    return [
        outputs["canonical"],
        outputs["canonical_transparent"],
        outputs["spritesheet"],
        outputs["yaml"],
        outputs["ron"],
        outputs["actor"],
        outputs["preview"],
    ]
