"""The Officer's service round: the sidearm's shot, as its own projectile sheet.

⭐⭐ THIS EXISTS BECAUSE HIS SHOT HAD NO ART AT ALL. The Officer's side special
(`officer_the_draw`) fires `RangedActionSpec::pistol`, which authored no
`visual`, and his `CharacterDefinition` sets no `ranged_vfx` — so the shot fell
through to `ProjectileArt::generic()`, the engine's content-free orange-red
QUAD. A pistol that fires a featureless rectangle is the visual half of Jon's
*"the officer is still firing backwards"*: his sheet draws a gun and a muzzle
flare, and what leaves it is a debug placeholder.

⛔ AND THE PLACEHOLDER IS WHY THE FLIP LOOKED INNOCENT. `projectile_visuals.rs`
flips a `FlipToTravel` round with `sprite.flip_x = vel.x < 0.0`, which assumes
the art points +x. A SOLID COLOUR QUAD IS SYMMETRIC, so that flip was a no-op
and could never be seen to be right or wrong. Real directional art is what makes
the axis testable at all.

⭐ AUTHORED POINTING +X, which is this category's standing convention — the
charge shot states it in its own docstring (*"the wake trails behind on the
authored +x travel direction"*). Nose at the right edge, wake to the left.
`FlipToTravel` mirrors it for a leftward shot; a round authored the other way
would need the `authored_faces_left` declaration character sheets carry and
projectiles have no equivalent for.

**Rows.** `travel` loops — the round is in flight far longer than it takes to
draw, and a still bullet reads as a decal. The flicker is in the WAKE and the
tracer glow, never the slug's silhouette: a bullet whose outline pulses reads as
a bug, not as speed. `impact` is separate so a shot that lands says so.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageFilter

from ambition_sprite2d_renderer.core.draw import blending_draw

from ...authoring.sheet_build import build_sheet, write_canonical

TARGET_NAME = "pistol_round"

#: Small frame: this is a slug, not a fireball. Cropping trims the rest.
FRAME_W, FRAME_H = 48, 32
SUPERSAMPLE = 4

#: (name, frames, ms). Travel loops; impact does not.
ROWS: List[Tuple[str, int, int]] = [
    ("travel", 4, 60),
    ("impact", 5, 40),
]

#: Service-pistol palette: hot white tip, brass body, a cool smoke wake. Warm
#: against the Officer's blues so the round reads as HIS and not as the
#: Polygon's cyan energy ball.
CORE = (255, 251, 232)
BRASS = (247, 206, 106)
DEEP = (176, 116, 28)
WAKE = (206, 198, 186)

#: Nose sits forward of centre so the sprite's own pivot is behind the tip —
#: the round leads with its point on the +x it is authored along.
NOSE_X = FRAME_W * 0.72
MID_Y = FRAME_H * 0.5
SLUG_LEN = 13.0
SLUG_HALF_H = 3.1


def _canvas():
    img = Image.new("RGBA", (FRAME_W * SUPERSAMPLE, FRAME_H * SUPERSAMPLE), (0, 0, 0, 0))
    return img, blending_draw(img)


def _ellipse(draw, cx, cy, rx, ry, colour, alpha):
    if rx <= 0 or ry <= 0 or alpha <= 1:
        return
    s = SUPERSAMPLE
    draw.ellipse(
        [(cx - rx) * s, (cy - ry) * s, (cx + rx) * s, (cy + ry) * s],
        fill=tuple(colour) + (int(alpha),),
    )


def _slug(draw, phase: float) -> None:
    """The bullet itself — identical every frame. See the docstring: the
    silhouette must not breathe."""
    del phase
    tail_x = NOSE_X - SLUG_LEN
    # Body: a capsule from tail to just behind the nose.
    _ellipse(draw, (tail_x + NOSE_X) * 0.5, MID_Y, SLUG_LEN * 0.5, SLUG_HALF_H, BRASS, 255)
    # Ogive tip, brighter, slightly ahead — this is the "point" of the point.
    _ellipse(draw, NOSE_X - 2.2, MID_Y, 3.4, SLUG_HALF_H * 0.94, CORE, 255)
    # Base shadow so the tail does not read as a second tip.
    _ellipse(draw, tail_x + 1.6, MID_Y, 2.0, SLUG_HALF_H * 0.86, DEEP, 235)


def _wake(draw, phase: float) -> None:
    """Smoke/tracer trailing BEHIND on -x. This is where the animation lives."""
    tail_x = NOSE_X - SLUG_LEN
    for i in range(5):
        t = i / 4.0
        # Puffs drift further back and fade as the loop advances.
        x = tail_x - 2.0 - t * 16.0 - phase * 3.0
        if x < 1.5:
            continue
        r = (1.5 + t * 3.0) * (0.75 + 0.25 * phase)
        alpha = (150 - t * 128) * (1.0 - 0.35 * phase)
        _ellipse(draw, x, MID_Y, r, r * 0.8, WAKE, max(0.0, alpha))


def _travel(frame_idx: int, nframes: int) -> Image.Image:
    img, draw = _canvas()
    phase = frame_idx / float(max(1, nframes))
    _wake(draw, phase)
    _slug(draw, phase)
    return img.resize((FRAME_W, FRAME_H), Image.LANCZOS)


def _impact(frame_idx: int, nframes: int) -> Image.Image:
    img, draw = _canvas()
    t = frame_idx / float(max(1, nframes - 1)) if nframes > 1 else 1.0
    # A spatter that opens backwards from where the nose stopped.
    _ellipse(draw, NOSE_X - 4.0, MID_Y, 2.0 + t * 9.0, 2.0 + t * 7.0, BRASS, 235 * (1.0 - t))
    _ellipse(draw, NOSE_X - 4.0, MID_Y, 1.0 + t * 4.5, 1.0 + t * 3.6, CORE, 255 * (1.0 - t * 0.85))
    for i in range(4):
        sx = NOSE_X - 5.0 - t * (7.0 + i * 3.5)
        sy = MID_Y + (i - 1.5) * t * 6.0
        _ellipse(draw, sx, sy, 1.4 * (1.0 - t * 0.6), 1.4 * (1.0 - t * 0.6), DEEP, 210 * (1.0 - t))
    out = img.resize((FRAME_W, FRAME_H), Image.LANCZOS)
    return out.filter(ImageFilter.GaussianBlur(0.4))


def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    if animation == "impact":
        return _impact(frame_idx, nframes)
    return _travel(frame_idx, nframes)


# A projectile, not a character — declare a `prop_` id so the actor-contract
# emitter does not misfile it into the `npc_` catalog namespace, exactly as the
# glider does one module over.
ACTOR_METADATA = {
    "actor": {"character_id": "prop_pistol_round", "display_name": "Service Round"},
    "visual_description": {
        "intent": (
            "The Officer's sidearm round: a small brass slug with a hot tip and "
            "a short smoke wake, authored travelling +x."
        ),
        "visual_language": [
            "hot white ogive tip, brass body, deep base shadow",
            "the wake trails BEHIND on the authored +x travel direction",
            "the silhouette never pulses; only the wake and glow animate",
        ],
    },
    "gameplay_description": {
        "role": "single-shot sidearm projectile",
        "authoring_notes": [
            "Authored pointing +x so ProjectileRotation::FlipToTravel mirrors it correctly.",
            "travel loops; impact is authored apart so a landed shot is legible.",
        ],
    },
    "tags": ["projectile", "bullet", "sidearm", "officer"],
}


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=Path(out_dir),
        frame_size=(FRAME_W, FRAME_H),
        auto_crop=True,
        crop_margin=2,
        actor_metadata=ACTOR_METADATA,
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    return [Path(outputs[key]) for key in keys if outputs.get(key)]


def render_canonical(out_dir: str | Path, **opts):
    del opts
    return write_canonical(
        TARGET_NAME, ROWS, render_frame, Path(out_dir), frame_size=(FRAME_W, FRAME_H)
    )


__all__ = ["ACTOR_METADATA", "ROWS", "TARGET_NAME", "render", "render_canonical", "render_frame"]
