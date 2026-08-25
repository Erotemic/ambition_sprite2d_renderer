"""Detached charge VFX for the Projectile Polygon's neutral special.

The shot itself is a projectile target (`projectiles/polygon_charge_shot.py`) —
it leaves and lives on its own. This is the other half: what happens AT the
muzzle while the button is held, and it has to be a separate sprite for the same
reason the shot does. It is anchored to his cannon and follows it as he aims,
so it cannot be baked into a character row that already assumes a fixed pose.

What a charge has to communicate, in order:

* **that it started** — an intake, so the player knows the button took,
* **what tier it is at** — the reason `charge_build` is one long row rather than
  a loop: the ring count climbs as it fills, and a player glancing at the muzzle
  should be able to read "nearly there" without a meter,
* **that it is full** — a hard flash and a changed loop, because a held charge
  that looks the same at 60% and 100% wastes the whole mechanic,
* **that it went away** — release and cancel differ, so a shield-drop mistake
  reads differently from a shot.

Colours are the cannon's own, so a charging muzzle and the shot that comes out of
it are visibly the same energy.
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
)

TARGET_NAME = "projectile_polygon_vfx"
SHEET_FILES = sheet_files(TARGET_NAME)
FRAME_SIZE = (144, 144)

CORE = (250, 254, 255, 255)
HOT = (186, 246, 255, 255)
BODY = (96, 214, 252, 255)
RIM = (26, 108, 178, 255)

CENTRE = (72.0, 72.0)

ROWS = [
    ("charge_intake", 6, 46),
    ("charge_build", 14, 62),
    ("charge_ready", 6, 40),
    ("charge_hold_full", 10, 58),
    ("charge_release", 7, 40),
    ("charge_cancel", 8, 52),
]


def _ball(canvas: Canvas, radius: float, alpha: float, phase: float, tier: float) -> None:
    """The core sphere. `tier` (0..1) adds structure, not just size."""
    swell = radius * (1.0 + 0.08 * math.sin(phase * math.tau))
    canvas.ellipse(CENTRE, swell * 1.30, fill=fade(RIM, 0.30 * alpha))
    canvas.ellipse(CENTRE, swell, fill=fade(BODY, 0.78 * alpha))
    canvas.ellipse(CENTRE, swell * 0.60, fill=fade(HOT, 0.90 * alpha))
    canvas.ellipse(CENTRE, swell * 0.28, fill=fade(CORE, 0.98 * alpha))
    if tier > 0.25:
        spin = phase * 360.0 * 1.6
        canvas.arc(CENTRE, swell * 1.45, swell * 1.45, spin, spin + 100,
                   fade(BODY, 0.75 * alpha), width=max(0.7, radius * 0.12))
    if tier > 0.55:
        spin = phase * 360.0 * 1.6
        canvas.arc(CENTRE, swell * 1.45, swell * 1.45, spin + 180, spin + 280,
                   fade(BODY, 0.75 * alpha), width=max(0.7, radius * 0.12))
        canvas.arc(CENTRE, swell * 1.78, swell * 1.78, -spin * 0.7, -spin * 0.7 + 70,
                   fade(HOT, 0.6 * alpha), width=max(0.6, radius * 0.09))
    if tier > 0.85:
        canvas.ellipse(CENTRE, swell * 2.05, outline=fade(CORE, 0.5 * alpha),
                       width=max(0.7, radius * 0.08))


def _intake(canvas: Canvas, t: float) -> None:
    """Loose energy pulled inward: the button registered."""
    ease = smooth(t)
    for index in range(7):
        angle = index * math.tau / 7 + t * 1.2
        reach = 44.0 * (1.0 - ease) + 9.0
        point = (CENTRE[0] + math.cos(angle) * reach, CENTRE[1] + math.sin(angle) * reach)
        canvas.line([point, CENTRE], fade(BODY, 0.16 + 0.34 * ease), width=1.0)
        canvas.ellipse(point, 1.6 + 1.4 * ease, fill=fade(HOT, 0.5 + 0.4 * ease))
    _ball(canvas, 3.0 + 4.0 * ease, 0.35 + 0.6 * ease, t, 0.0)


def _build(canvas: Canvas, t: float) -> None:
    """The long fill. Ring count and radius both climb, so the tier is legible."""
    tier = smooth(t)
    radius = 5.0 + 13.5 * tier
    # Intake keeps arriving the whole time — a charge that stops drawing energy
    # in reads as finished long before it is.
    for index in range(5):
        angle = index * math.tau / 5 - t * 3.1
        arrive = (t * 2.4 + index / 5.0) % 1.0
        reach = 46.0 * (1.0 - arrive) + radius
        point = (CENTRE[0] + math.cos(angle) * reach, CENTRE[1] + math.sin(angle) * reach)
        canvas.ellipse(point, 1.2 + 1.6 * arrive, fill=fade(HOT, 0.30 + 0.5 * arrive))
    # One standing ring per completed tier: countable at a glance.
    for step in range(1, 6):
        if tier < step / 5.0:
            break
        canvas.ellipse(
            CENTRE, radius * (1.35 + 0.24 * step),
            outline=fade(BODY, 0.22 + 0.10 * step),
            width=0.8,
        )
    _ball(canvas, radius, 1.0, t * 2.0, tier)


def _ready(canvas: Canvas, t: float) -> None:
    """It filled. A hard flash, so full charge is never a guess."""
    flare = (1.0 - smooth(t)) ** 1.5
    canvas.ellipse(CENTRE, 20.0 + 46.0 * smooth(t), outline=fade(CORE, 0.85 * flare), width=2.6 * flare + 0.4)
    canvas.ellipse(CENTRE, 12.0 + 26.0 * smooth(t), outline=fade(HOT, 0.7 * flare), width=1.8 * flare + 0.3)
    canvas.ellipse(CENTRE, 30.0 * flare + 6.0, fill=fade(CORE, 0.75 * flare))
    _ball(canvas, 18.5, 1.0, t, 1.0)


def _hold_full(canvas: Canvas, t: float) -> None:
    """Held at full: it stays big and gets ANGRY rather than just sitting."""
    _ball(canvas, 18.5, 1.0, t, 1.0)
    for index in range(6):
        angle = index * math.tau / 6 + t * math.tau * 0.5
        crackle = pulse(t * 2.0 + index / 6.0)
        inner = 21.0
        outer = inner + 5.0 + 7.0 * crackle
        a = (CENTRE[0] + math.cos(angle) * inner, CENTRE[1] + math.sin(angle) * inner)
        b = (CENTRE[0] + math.cos(angle + 0.16) * outer, CENTRE[1] + math.sin(angle + 0.16) * outer)
        canvas.line([a, b], fade(CORE, 0.25 + 0.55 * crackle), width=0.9)


def _release(canvas: Canvas, t: float) -> None:
    """It leaves: the ball goes with the shot and the muzzle keeps the flash."""
    ease = smooth(t)
    canvas.ellipse(CENTRE, 10.0 + 52.0 * ease, outline=fade(HOT, 0.8 * (1.0 - ease)), width=2.4 * (1.0 - ease) + 0.3)
    canvas.ellipse(CENTRE, 26.0 * (1.0 - ease) + 4.0, fill=fade(CORE, 0.9 * (1.0 - ease)))
    # The ball itself moving off along +x, which the runtime mirrors with facing.
    travel = (CENTRE[0] + 58.0 * ease, CENTRE[1])
    canvas.ellipse(travel, 18.5 * (1.0 - 0.35 * ease), fill=fade(BODY, 0.85 * (1.0 - ease * 0.5)))
    canvas.ellipse(travel, 8.0 * (1.0 - 0.35 * ease), fill=fade(CORE, 0.95 * (1.0 - ease * 0.5)))


def _cancel(canvas: Canvas, t: float) -> None:
    """It was dropped: the energy falls apart outward instead of leaving."""
    ease = smooth(t)
    _ball(canvas, 18.5 * (1.0 - ease * 0.8), (1.0 - ease) ** 1.4, t, 1.0 - ease)
    for index in range(8):
        angle = index * math.tau / 8 + 0.3
        reach = 20.0 + 34.0 * ease
        point = (CENTRE[0] + math.cos(angle) * reach, CENTRE[1] + math.sin(angle) * reach)
        canvas.ellipse(point, 2.4 * (1.0 - ease), fill=fade(BODY, 0.6 * (1.0 - ease)))


DRAWERS = {
    "charge_intake": _intake,
    "charge_build": _build,
    "charge_ready": _ready,
    "charge_hold_full": _hold_full,
    "charge_release": _release,
    "charge_cancel": _cancel,
}

SPECS = {
    "charge_intake": make_spec(
        "charge", "Loose energy drawn into the muzzle as the charge begins.",
        placement="source", attachment="follow_source", relationship="startup",
        extra_anchor="emitter", size=80,
    ),
    "charge_build": make_spec(
        "charge", "The fill: ball and standing ring count both climb with tier.",
        placement="source", attachment="follow_source", relationship="sustain",
        extra_anchor="emitter", blend="alpha_or_additive", size=104,
    ),
    "charge_ready": make_spec(
        "charge", "Hard flash the instant the charge tops out.",
        placement="source", attachment="follow_source", relationship="active",
        extra_anchor="emitter", blend="alpha_or_additive", size=128,
    ),
    "charge_hold_full": make_spec(
        "charge", "Held at full charge, crackling rather than sitting still.",
        loop=True, placement="source", attachment="follow_source", relationship="sustain",
        extra_anchor="emitter", blend="alpha_or_additive", size=112,
    ),
    "charge_release": make_spec(
        "charge", "The ball departs along +x and the muzzle keeps the flash.",
        placement="source", orientation="positive_x_is_forward", mirror_x=True,
        attachment="follow_source", relationship="release", extra_anchor="emitter", size=132,
    ),
    "charge_cancel": make_spec(
        "charge", "Dropped charge falling apart outward instead of leaving.",
        placement="source", attachment="follow_source", relationship="recovery",
        extra_anchor="emitter", size=104,
    ),
}

ORIGINS = {name: CENTRE for name, _frames, _ms in ROWS}


def render(out_dir: str | Path, **opts):
    del opts
    return publish_catalog(
        target_name=TARGET_NAME,
        display_name="Projectile Polygon Charge VFX",
        character_context_id="projectile_polygon",
        character_context_display="Projectile Polygon",
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


__all__ = ["DRAWERS", "ORIGINS", "ROWS", "SPECS", "TARGET_NAME", "render", "render_canonical"]
