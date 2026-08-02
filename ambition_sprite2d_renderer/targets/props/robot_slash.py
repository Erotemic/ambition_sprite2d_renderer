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
# 5 frames x 20 ms = 100 ms, which is exactly the melee ACTIVE window
# (`SwipeSpec.active_s = 0.10`). At 24 ms the effect outlived the hitbox by a
# fifth of its own life, so the last thing a player saw of a swing was a blade
# that no longer hurt anything (Jon, 2026-08-02: "the vfx should be trimmed to
# the damage window").
ROWS: List[Tuple[str, int, int]] = [
    ("side", 5, 20),
    ("up", 5, 20),
    ("down", 5, 20),
    ("poke", 5, 20),
]

CORE = (255, 255, 255, 255)
HOT = (226, 247, 255, 255)
BODY = (174, 226, 255, 255)
EDGE = (76, 163, 239, 255)
DEEP = (29, 83, 177, 255)


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
# **The art sits INSIDE the polygon, never outside it.** Jon's rule: it is fine
# if the hitbox slightly overreaches the effect, but 100% of what is drawn must
# hit — "the player should never feel like they should have hit when they
# didn't". The polygon is the envelope scaled OUT by its own margin, so drawing
# at the same peak divided by a little more than that margin lands inside it,
# with room left for the wash's blur to feather across.
AXIS_Y = 80.0
REACH = 158.0
PEAK_HALF = 80.0 / 1.13
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

    `slash_envelope.TIP` is folded in because the frame maps to the QUAD, and
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
    if u <= 0.0 or u >= 1.0:
        return 0.0
    return slash_envelope.half_at(u * slash_envelope.TIP) * PEAK_HALF


def _half_disc(reach_scale: float = 1.0, width_scale: float = 1.0, samples: int = 48):
    """The swept half disc as a closed outline, in swing space."""
    top = []
    bottom = []
    for i in range(samples + 1):
        u = i / samples
        x = REACH * reach_scale * u
        half = _half_at(u) * width_scale
        top.append((x, AXIS_Y - half))
        bottom.append((x, AXIS_Y + half))
    return top + list(reversed(bottom))


def _band_image(size, outer_reach: float, inner_reach: float, width_scale: float,
                color, alpha: int) -> Image.Image:
    """The BLADE band: an outer half disc with an inner one punched out.

    The punch-out is what makes it read as a crescent rather than a wedge, and
    how deep it goes is the "bend". A shallow cut is the old shallow swoosh; a
    deep one is the Hollow Knight arc that curls back on itself.

    Built with a mask rather than one clever polygon: a crescent traced as a
    single closed path has to double back through itself, and PIL's even-odd
    fill of that path is not the shape anybody drew.
    """
    band = Image.new("RGBA", size, (0, 0, 0, 0))
    blending_draw(band).polygon(
        _scaled(_half_disc(outer_reach, width_scale)),
        fill=(color[0], color[1], color[2], alpha),
    )
    hole = Image.new("L", size, 0)
    ImageDraw.Draw(hole).polygon(
        _scaled(_half_disc(inner_reach, width_scale * 0.94)), fill=255
    )
    band.putalpha(ImageChops.subtract(band.getchannel("A"), hole))
    return band


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
    """One frame of the forehand slash, drawn in SWING SPACE.

    Three layers, and the middle one is the fix. Measured on the old art, the
    first 30% of the swing had ZERO pixels and the first half was under 40%
    covered, while the polygon damaged across all of it — a region that hurt and
    showed nothing (Jon, 2026-08-02: "there is a big empty part of the hitpoly
    between the arc of the slash and the player that does hurt the enemy, but
    there is no vfx to indicate to the user that it would").

      1. WASH   — the whole swept half disc at low alpha. This is the layer that
                  says "all of this hurts". It reaches the body because the
                  polygon does.
      2. BAND   — the bright blade, hugging the outer boundary, deeply cut so it
                  curls like a crescent instead of sitting flat.
      3. EDGE   — a thin hot rim on the leading arc, so the blade still has a
                  front.

    Over the five frames the wash fades first and the band retreats toward the
    tip: the swing dissipates from the handle outward, which is the direction a
    real one leaves the air.
    """
    state = _arc_state(t)
    amp = state["amp"]
    size = (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    if amp <= 0.01:
        return canvas.resize(FRAME_SIZE, Image.Resampling.LANCZOS)

    release = state["release"]
    # The blade's reach never shrinks (the hitbox does not), but the trailing
    # wash and the band's inner cut both retreat outward as the swing spends.
    wash_alpha = int(96 * amp * (1.0 - 0.72 * release))
    inner_cut = _lerp(0.42, 0.78, _smoothstep(0.0, 0.9, t))
    width_scale = _lerp(1.0, 0.86, release)

    # 1. WASH — a soft envelope over the whole swept region.
    wash = Image.new("RGBA", size, (0, 0, 0, 0))
    blending_draw(wash).polygon(
        _scaled(_half_disc(1.0, width_scale)),
        fill=(EDGE[0], EDGE[1], EDGE[2], wash_alpha),
    )
    wash = wash.filter(ImageFilter.GaussianBlur(radius=int(1.8 * SUPER)))
    canvas.alpha_composite(wash)

    # 2. BAND — the blade, brightening inward through the stack.
    for inner, color, alpha in (
        (inner_cut - 0.10, DEEP, int(215 * amp)),
        (inner_cut, BODY, int(238 * amp)),
        (inner_cut + 0.11, HOT, int(248 * amp)),
        (inner_cut + 0.19, CORE, int(255 * amp)),
    ):
        canvas.alpha_composite(
            _band_image(size, 1.0, _clamp(inner, 0.05, 0.95), width_scale, color, alpha)
        )

    # 3. EDGE — the hot leading rim.
    canvas.alpha_composite(
        _band_image(size, 1.0, 0.955, width_scale, CORE, int(255 * amp))
    )
    return canvas.resize(FRAME_SIZE, Image.Resampling.LANCZOS)


# ⚠ `up` and `down` are NOT pre-rotated any more, and that is a contract change
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
    """A straight THRUST, in swing space — the down-tilt, and only it.

    Jon keeps this one a "Marth-like" poke while every other attack becomes a
    half disc: a thrust reads by reach, not by area. So the shape is a long
    lens, full height through the middle and tapered at both ends, with the
    taper at the BODY end short — a spear does not start at a point, the hand
    is already holding something.

    Full height is right, not generous: the poke's hit volume is thin, so the
    quad the renderer stretches this into is thin, and art that left margin here
    would draw a thrust narrower than the one that hurts.
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
