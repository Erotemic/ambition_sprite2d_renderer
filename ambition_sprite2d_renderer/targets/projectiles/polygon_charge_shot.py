"""The Projectile Polygon's charge shot: a standalone projectile sprite.

His neutral special is the classic held-and-released charge ball. That cannot be
an effect composited into his character sheet, because the shot OUTLIVES the
animation that fired it — it crosses the stage under its own entity, at whatever
tier it was released, and it has to be legible at every one of them. So it is
its own target, with its own rows.

**Five tiers, told apart by shape, not just size.** A shot the player has held
for two seconds has to be readable as different from a tap the instant it leaves
the barrel, and scale alone does not survive being small on a busy stage:

* tier 1 is a bare pellet — a core and nothing else,
* tier 2 adds a rim,
* tier 3 adds the first orbiting arc,
* tier 4 doubles the arcs and starts throwing sparks,
* tier 5 gains a compression ring and a lens flare, so full charge reads as a
  different OBJECT rather than a bigger dot.

Each travel row loops, and the pulse is deliberately not in phase with the orbit
so the ball never looks like a spinning still.

Impacts are separate rows rather than a scaled copy of one: a light hit puffs and
a heavy hit throws a shockwave ring, which is what tells a player whether the
thing they just ate was worth the shield.
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageFilter

from ambition_sprite2d_renderer.core.draw import blending_draw

from ...authoring.sheet_build import build_sheet, write_canonical

TARGET_NAME = "polygon_charge_shot"
FRAME_W, FRAME_H = 96, 96
SUPERSAMPLE = 4

#: His cannon's palette, so the shot reads as HIS. White core through cyan to a
#: deep rim; the rim is what keeps it visible against a pale stage.
CORE = (250, 254, 255)
HOT = (186, 246, 255)
BODY = (96, 214, 252)
RIM = (26, 108, 178)
SPARK = (214, 250, 255)

#: (name, frames, ms). Travel rows loop; impacts and the spawn flash do not.
ROWS: list[tuple[str, int, int]] = [
    ("travel_tier1", 4, 70),
    ("travel_tier2", 6, 66),
    ("travel_tier3", 6, 62),
    ("travel_tier4", 8, 58),
    ("travel_tier5", 8, 54),
    ("spawn", 5, 38),
    ("impact_light", 6, 44),
    ("impact_heavy", 9, 46),
]

#: Radius of the ball at each tier, in logical px. Tier 5 is deliberately more
#: than double tier 1 — the reward for holding has to be visible at a glance.
TIER_RADIUS = {1: 5.0, 2: 7.5, 3: 10.5, 4: 14.0, 5: 18.5}


def _canvas() -> tuple[Image.Image, object]:
    image = Image.new(
        "RGBA", (FRAME_W * SUPERSAMPLE, FRAME_H * SUPERSAMPLE), (0, 0, 0, 0)
    )
    return image, blending_draw(image)


def _disc(draw, centre, radius: float, colour, alpha: int) -> None:
    if radius <= 0 or alpha <= 1:
        return
    x, y = centre[0] * SUPERSAMPLE, centre[1] * SUPERSAMPLE
    r = radius * SUPERSAMPLE
    draw.ellipse([x - r, y - r, x + r, y + r], fill=tuple(colour) + (alpha,))


def _ring(draw, centre, radius: float, width: float, colour, alpha: int) -> None:
    if radius <= 0 or alpha <= 1:
        return
    x, y = centre[0] * SUPERSAMPLE, centre[1] * SUPERSAMPLE
    r = radius * SUPERSAMPLE
    draw.ellipse(
        [x - r, y - r, x + r, y + r],
        outline=tuple(colour) + (alpha,),
        width=max(1, round(width * SUPERSAMPLE)),
    )


def _arc(draw, centre, radius: float, start: float, extent: float, width: float,
         colour, alpha: int) -> None:
    if radius <= 0 or alpha <= 1:
        return
    x, y = centre[0] * SUPERSAMPLE, centre[1] * SUPERSAMPLE
    r = radius * SUPERSAMPLE
    draw.arc(
        [x - r, y - r, x + r, y + r],
        start=start,
        end=start + extent,
        fill=tuple(colour) + (alpha,),
        width=max(1, round(width * SUPERSAMPLE)),
    )


def _ball(draw, centre, radius: float, tier: int, phase: float, alpha: float = 1.0) -> None:
    """One charge ball. Layers are added by TIER, not merely scaled."""
    # Pulse and orbit run at different rates on purpose: matched, the ball reads
    # as one rigid object being spun rather than something under pressure.
    pulse = 1.0 + 0.09 * math.sin(phase * math.tau)
    swell = radius * pulse
    _disc(draw, centre, swell * 1.28, RIM, int(70 * alpha))
    _disc(draw, centre, swell, BODY, int(190 * alpha))
    _disc(draw, centre, swell * 0.62, HOT, int(225 * alpha))
    _disc(draw, centre, swell * 0.30, CORE, int(250 * alpha))
    if tier >= 2:
        _ring(draw, centre, swell * 1.12, max(0.6, radius * 0.10), HOT, int(150 * alpha))
    if tier >= 3:
        spin = phase * 360.0 * 1.7
        _arc(draw, centre, swell * 1.42, spin, 96, max(0.7, radius * 0.13), BODY, int(190 * alpha))
    if tier >= 4:
        spin = phase * 360.0 * 1.7
        _arc(draw, centre, swell * 1.42, spin + 180, 96, max(0.7, radius * 0.13), BODY, int(190 * alpha))
        _arc(draw, centre, swell * 1.72, -spin * 0.7, 62, max(0.6, radius * 0.09), HOT, int(150 * alpha))
        for index in range(5):
            angle = phase * math.tau * 1.3 + index * math.tau / 5
            reach = swell * (1.6 + 0.35 * ((index * 0.618) % 1.0))
            point = (centre[0] + math.cos(angle) * reach, centre[1] + math.sin(angle) * reach)
            _disc(draw, point, max(0.5, radius * 0.11), SPARK, int(210 * alpha))
    if tier >= 5:
        # A compression ring standing off the surface: full charge is a shot
        # that is visibly holding something in.
        _ring(draw, centre, swell * 1.95, max(0.7, radius * 0.08), CORE, int(120 * alpha))
        for index in range(4):
            angle = index * math.pi / 2 + phase * math.tau * 0.4
            reach = swell * 2.25
            tip = (centre[0] + math.cos(angle) * reach, centre[1] + math.sin(angle) * reach)
            draw.line(
                [
                    (centre[0] * SUPERSAMPLE, centre[1] * SUPERSAMPLE),
                    (tip[0] * SUPERSAMPLE, tip[1] * SUPERSAMPLE),
                ],
                fill=HOT + (int(90 * alpha),),
                width=max(1, round(radius * 0.09 * SUPERSAMPLE)),
            )


def _travel(tier: int, frame_idx: int, frame_count: int) -> Image.Image:
    image, draw = _canvas()
    phase = frame_idx / frame_count
    centre = (FRAME_W * 0.5, FRAME_H * 0.5)
    radius = TIER_RADIUS[tier]
    # The wake trails BEHIND (-x): the sheet is authored travelling +x and the
    # runtime mirrors it, so a trail drawn symmetrically would read as a comet
    # flying tail-first the moment he turns around.
    for step in range(1, 4 if tier >= 3 else 2):
        back = (centre[0] - radius * 0.85 * step, centre[1])
        _disc(draw, back, radius * (0.72 - 0.16 * step), BODY, int(96 / step))
    _ball(draw, centre, radius, tier, phase)
    return _finish(image, blur=0.9 + 0.12 * tier)


def _spawn(frame_idx: int, frame_count: int) -> Image.Image:
    """Muzzle exit: the ball snaps out of a flat flash."""
    image, draw = _canvas()
    t = frame_idx / max(1, frame_count - 1)
    centre = (FRAME_W * 0.5, FRAME_H * 0.5)
    flare = (1.0 - t) ** 1.6
    _disc(draw, centre, 26.0 * flare + 3.0, CORE, int(230 * flare))
    _ring(draw, centre, 10.0 + 30.0 * t, 2.4 * (1.0 - t) + 0.4, HOT, int(200 * (1.0 - t)))
    _ball(draw, centre, TIER_RADIUS[5] * (0.35 + 0.65 * t), 5, t, alpha=min(1.0, t * 1.8))
    return _finish(image, blur=1.4)


def _impact(heavy: bool, frame_idx: int, frame_count: int) -> Image.Image:
    image, draw = _canvas()
    t = frame_idx / max(1, frame_count - 1)
    centre = (FRAME_W * 0.5, FRAME_H * 0.5)
    fade = (1.0 - t) ** 1.5
    peak = 34.0 if heavy else 17.0
    _disc(draw, centre, peak * (0.25 + 0.75 * t) * 0.5, CORE, int(220 * fade))
    _disc(draw, centre, peak * (0.3 + 0.7 * t) * 0.8, HOT, int(170 * fade))
    _ring(draw, centre, peak * (0.2 + t), 3.0 * fade + 0.5, BODY, int(220 * fade))
    if heavy:
        # A second, faster ring: the shockwave outrunning the flash is what
        # separates a heavy hit from a bright one.
        _ring(draw, centre, peak * (0.2 + t * 1.7), 2.0 * fade + 0.4, CORE, int(150 * fade))
        for index in range(9):
            angle = index * math.tau / 9 + 0.2
            reach = peak * (0.4 + t * 1.5)
            tip = (centre[0] + math.cos(angle) * reach, centre[1] + math.sin(angle) * reach)
            _disc(draw, tip, 2.6 * fade + 0.4, SPARK, int(220 * fade))
    return _finish(image, blur=1.6)


def _finish(image: Image.Image, blur: float) -> Image.Image:
    glow = image.filter(ImageFilter.GaussianBlur(blur * SUPERSAMPLE))
    out = Image.new("RGBA", image.size, (0, 0, 0, 0))
    out.alpha_composite(glow)
    out.alpha_composite(image)
    return out.resize((FRAME_W, FRAME_H), Image.LANCZOS)


def render_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    if animation.startswith("travel_tier"):
        return _travel(int(animation[-1]), frame_idx, frame_count)
    if animation == "spawn":
        return _spawn(frame_idx, frame_count)
    if animation == "impact_light":
        return _impact(False, frame_idx, frame_count)
    if animation == "impact_heavy":
        return _impact(True, frame_idx, frame_count)
    raise ValueError(f"{TARGET_NAME}: no drawer for {animation!r}")


ACTOR_METADATA = {
    "actor": {
        "character_id": TARGET_NAME,
        "display_name": "Polygon Charge Shot",
    },
    "authoring_description": {
        "concept": (
            "The held-and-released charge shot fired from the Projectile "
            "Polygon's head cannon. Five tiers, each a different object rather "
            "than a different size."
        ),
        "visual_language": [
            "white core through cyan body to a deep blue rim, the cannon's own palette",
            "layers added by tier: rim, then orbiting arcs, then sparks, then a compression ring",
            "pulse and orbit deliberately out of phase so it never reads as a spinning still",
            "the wake trails behind on the authored +x travel direction",
        ],
    },
    "gameplay_description": {
        "role": "chargeable neutral-special projectile",
        "authoring_notes": [
            "Tier rows are separate animations, not a scale parameter: the runtime picks the row for the release tier.",
            "impact_light and impact_heavy are authored apart so a player can tell what hit them.",
        ],
    },
    "tags": ["projectile", "charge_shot", "energy", "projectile_polygon"],
}


def render(out_dir: str | Path, **opts):
    del opts
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=Path(out_dir),
        frame_size=(FRAME_W, FRAME_H),
        auto_crop=True,
        crop_margin=3,
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
