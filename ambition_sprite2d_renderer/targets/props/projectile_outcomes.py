"""What happened to a shot, at a glance: it hit, a guard turned it, or it went
out. And the tell of a guard that turns shots.

Each outcome has its own colour and its own shape, so the player can tell the
three apart in the 0.3 s each is on screen:

* ``fireball_hit`` — WARM and ROUND: a white-hot core opens into a ring of
  flame petals, and embers fly out in all ways. The shot landed.
* ``fireball_deflect`` — COLD and SHARP: a white-blue cross flare, a thin arc
  of the ricochet, and needle sparks that glance off up and back. No flame: a
  hull turned the shot.
* ``fireball_fizzle`` — SMALL and GREY: a puff of smoke that rises and thins,
  with two embers that drop and go out. No flash: the shot ran out (its
  range, a wall, its last bounce).
* ``boss_guard_glint`` — the tell of a guard that is up: a shield emblem in
  white and blue light shows over the hull and a sheen runs over it. The game
  draws it over a boss each beat while its hull turns blows.

The game draws each where the outcome happens (`ProjectileArt::hit_vfx`,
`deflect_vfx`, `expiry_vfx`; `boss_guard_tell`). No row has a shadow, and none
draws a projectile: the shot is the game's. Each row fades out in its own
frames.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from PIL import Image

from ...authoring.sheet_build import build_sheet, write_canonical
from ...core.draw import blending_draw

RGBA = Tuple[int, int, int, int]

TARGET_NAME = "projectile_outcomes"
# An effect sheet: its rows sound `vfx.projectile_outcome.<row>` (no cue ships
# until one is auditioned); decoded at boot (any shot may end so); each row
# fades in its own frames.
FX = {"cue_family": "projectile_outcome", "residency": "Core", "fade": "InItsFrames"}
SHEET_FILES = [
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
]

ACTOR_METADATA = {
    "actor": {"character_id": "fx_projectile_outcomes", "display_name": "Projectile Outcomes"},
    "body": {
        "body_plan": "Effect",
        "body_kind": "Burst",
        "mass_class": "Light",
        "locomotion_hint": "Stationary",
        "traits": ["fx", "overlay"],
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "animation_bindings": {"default": {"animation": "fireball_hit", "events": []}},
    "sockets": {"origin": {"source": f"{TARGET_NAME}.geometry", "point": {"x": 64.0, "y": 64.0}}},
    "tags": ["fx", "overlay"],
}

ROWS: List[Tuple[str, int, int]] = [
    ("fireball_hit", 7, 40),
    ("fireball_deflect", 6, 40),
    ("fireball_fizzle", 8, 50),
    ("boss_guard_glint", 9, 45),
]

FRAME_SIZE = (128, 128)
SUPER = 4
C = 64.0  # the centre of a frame, in frame pixels

INK = (40, 20, 28, 255)
WHITE = (255, 252, 240, 255)
HOT_YELLOW = (255, 222, 110, 255)
FLAME = (255, 150, 60, 255)
FLAME_DEEP = (226, 84, 46, 255)
EMBER = (255, 214, 120, 255)
STEEL_WHITE = (240, 250, 255, 255)
STEEL_BLUE = (140, 210, 255, 255)
STEEL_DEEP = (70, 130, 220, 255)
SMOKE = (150, 136, 146, 255)
SMOKE_LIGHT = (200, 192, 198, 255)


def _alpha(color: RGBA, a: float) -> RGBA:
    return (color[0], color[1], color[2], max(0, min(255, int(round(color[3] * a)))))


def _s(v: float) -> float:
    return v * SUPER


def _ease_out(t: float) -> float:
    t = min(1.0, max(0.0, t))
    return 1.0 - (1.0 - t) ** 3


def _fade_after(t: float, start: float) -> float:
    """1 until `start`, then down to 0 at the end of the row."""
    if t <= start:
        return 1.0
    return max(0.0, 1.0 - (t - start) / (1.0 - start))


def _circle(d, cx, cy, r, fill, outline=None, width=0):
    d.ellipse((_s(cx - r), _s(cy - r), _s(cx + r), _s(cy + r)), fill=fill, outline=outline, width=int(width))


def _poly(d, pts, fill, outline=None, width=0):
    pts = [(_s(x), _s(y)) for x, y in pts]
    d.polygon(pts, fill=fill)
    if outline is not None and width:
        d.line(pts + [pts[0]], fill=outline, width=int(width), joint="curve")


def _line(d, a, b, fill, width):
    d.line((_s(a[0]), _s(a[1]), _s(b[0]), _s(b[1])), fill=fill, width=int(round(_s(width))))


def _hit(img: Image.Image, t: float) -> None:
    """A white-hot core opens into a ring of flame petals; embers fly out."""
    d = blending_draw(img)
    fade = _fade_after(t, 0.45)
    grow = _ease_out(t / 0.55)
    # Flame petals: eight, round-tipped, around the core.
    petals = 8
    outer = 10.0 + 24.0 * grow
    for k in range(petals):
        a = math.tau * k / petals + 0.2
        tip = (C + math.cos(a) * outer, C + math.sin(a) * outer)
        left = (C + math.cos(a - 0.34) * outer * 0.45, C + math.sin(a - 0.34) * outer * 0.45)
        right = (C + math.cos(a + 0.34) * outer * 0.45, C + math.sin(a + 0.34) * outer * 0.45)
        _poly(d, [left, tip, right], _alpha(FLAME if k % 2 else FLAME_DEEP, fade), _alpha(INK, fade), 1.6 * SUPER)
    # The core: white in the first frames, yellow as it cools.
    core = max(0.0, 9.0 + 6.0 * grow - 14.0 * max(0.0, t - 0.35))
    if core > 0.5:
        _circle(d, C, C, core, _alpha(HOT_YELLOW, fade), _alpha(INK, fade), 1.6 * SUPER)
        _circle(d, C, C, core * 0.6, _alpha(WHITE, fade))
    # Embers fly out past the petals.
    for k in range(10):
        a = math.tau * k / 10 + 0.5
        r0 = outer * 0.8
        r1 = outer * (1.0 + 0.6 * _ease_out(t))
        head = (C + math.cos(a) * r1, C + math.sin(a) * r1)
        tail = (C + math.cos(a) * max(r0, r1 - 6.0), C + math.sin(a) * max(r0, r1 - 6.0))
        if t > 0.1:
            _line(d, tail, head, _alpha(EMBER, fade), 1.4)


def _deflect(img: Image.Image, t: float) -> None:
    """A cold cross flare, the arc of a ricochet, needle sparks glancing off."""
    d = blending_draw(img)
    fade = _fade_after(t, 0.35)
    flare = math.sin(math.pi * min(1.0, t / 0.6))
    # The cross flare: a long thin four-point star, cold white.
    if flare > 0.03:
        long_r, short_r = 30.0 * flare, 3.0 * flare
        for turn in (0.0, math.pi / 2.0):
            pts = []
            for k in range(4):
                a = turn + math.pi * k / 2.0
                r = long_r if k % 2 == 0 else short_r
                pts.append((C + math.cos(a) * r, C + math.sin(a) * r))
            _poly(d, pts, _alpha(STEEL_WHITE, fade), _alpha(STEEL_DEEP, fade), 1.2 * SUPER)
        _circle(d, C, C, 5.0 * flare, _alpha(STEEL_WHITE, fade), _alpha(STEEL_DEEP, fade), 1.2 * SUPER)
    # The ricochet: a thin arc that opens up and back from the contact.
    sweep = _ease_out(t / 0.7)
    r = 18.0 + 10.0 * sweep
    d.arc(
        (_s(C - r), _s(C - r), _s(C + r), _s(C + r)),
        start=200.0,
        end=200.0 + 110.0 * sweep,
        fill=_alpha(STEEL_BLUE, fade),
        width=int(_s(2.2)),
    )
    # Needle sparks glance off up and back: straight, thin, fast.
    for k, angle in enumerate((-150.0, -125.0, -100.0, -70.0, -40.0)):
        a = math.radians(angle)
        travel = 10.0 + 36.0 * _ease_out(t * (1.1 - 0.08 * k))
        head = (C + math.cos(a) * travel, C + math.sin(a) * travel)
        tail = (C + math.cos(a) * max(4.0, travel - 9.0), C + math.sin(a) * max(4.0, travel - 9.0))
        _line(d, tail, head, _alpha(STEEL_WHITE if k % 2 else STEEL_BLUE, fade), 1.3)


def _fizzle(img: Image.Image, t: float) -> None:
    """The fire shrinks to a dull ember and goes out in a puff that rises and
    thins; two embers drop and go out."""
    d = blending_draw(img)
    fade = _fade_after(t, 0.25)
    # The flame going out: a dull orange core that shrinks in the first part.
    dying = max(0.0, 1.0 - t / 0.4)
    if dying > 0.0:
        _circle(d, C, C, 9.0 * dying, _alpha(FLAME, 0.8 * dying), _alpha(INK, 0.8 * dying), 1.2 * SUPER)
    rise = 14.0 * _ease_out(t)
    grow = 0.8 + 0.6 * _ease_out(t / 0.6)
    for k, (dx, dy, r) in enumerate(((-9.0, 0.0, 10.0), (8.0, -3.0, 9.0), (0.0, -10.0, 9.5), (-3.0, 6.0, 7.0))):
        rr = r * grow * (1.0 - 0.3 * t)
        _circle(d, C + dx, C + dy - rise, rr, _alpha(SMOKE if k % 2 else SMOKE_LIGHT, 0.85 * fade),
                _alpha(INK, 0.6 * fade), 1.0 * SUPER)
    # Two embers drop and go out by mid-row.
    ember = max(0.0, 1.0 - t / 0.55)
    if ember > 0.0:
        for dx, fall in ((-7.0, 18.0), (8.0, 13.0)):
            y = C + 6.0 + fall * t
            _circle(d, C + dx, y, 2.0 + 1.0 * ember, _alpha(EMBER, ember), _alpha(FLAME_DEEP, ember), 0.6 * SUPER)


def _guard_glint(img: Image.Image, t: float) -> None:
    """A shield emblem in cold light, and a sheen that runs over it."""
    d = blending_draw(img)
    show = math.sin(math.pi * t)
    if show <= 0.02:
        return
    # The emblem: a pointed shield outline, white with a blue edge.
    w, h = 22.0, 27.0
    shield = [
        (C - w, C - h * 0.62),
        (C, C - h * 0.82),
        (C + w, C - h * 0.62),
        (C + w * 0.92, C + h * 0.1),
        (C, C + h),
        (C - w * 0.92, C + h * 0.1),
    ]
    _poly(d, shield, _alpha(STEEL_BLUE, 0.28 * show), _alpha(STEEL_DEEP, show), 2.0 * SUPER)
    inner = [(C + (x - C) * 0.72, C + (y - C) * 0.72) for x, y in shield]
    _poly(d, inner, _alpha(STEEL_WHITE, 0.18 * show), _alpha(STEEL_WHITE, show), 1.2 * SUPER)
    # The sheen: a bright diagonal band that runs across the shield, inside it.
    x = C - 26.0 + 52.0 * t
    band = [(x - 4.0, C - 30.0), (x + 4.0, C - 30.0), (x - 10.0, C + 30.0), (x - 18.0, C + 30.0)]
    sheen = Image.new("RGBA", img.size, (0, 0, 0, 0))
    _poly(blending_draw(sheen), band, _alpha(STEEL_WHITE, 0.75 * show))
    mask = Image.new("L", img.size, 0)
    _poly(blending_draw(mask), inner, 255)
    img.alpha_composite(Image.composite(sheen, Image.new("RGBA", img.size, (0, 0, 0, 0)), mask))
    # A star where the sheen meets the top edge.
    star = 7.0 * show
    for turn in (0.0, math.pi / 2.0):
        pts = []
        for k in range(4):
            a = turn + math.pi * k / 2.0
            r = star if k % 2 == 0 else star * 0.18
            pts.append((x + math.cos(a) * r, C - 22.0 + math.sin(a) * r))
        _poly(d, pts, _alpha(STEEL_WHITE, show))


DRAWERS = {
    "fireball_hit": _hit,
    "fireball_deflect": _deflect,
    "fireball_fizzle": _fizzle,
    "boss_guard_glint": _guard_glint,
}


def _draw_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    img = Image.new("RGBA", (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER), (0, 0, 0, 0))
    # A frame stands for the middle of its part of the row.
    DRAWERS[anim](img, (frame_idx + 0.5) / nframes)
    return img.resize(FRAME_SIZE, Image.Resampling.LANCZOS)


def _frame_meta(anim: str, frame_idx: int, nframes: int) -> dict:
    return {
        "anchors": {"origin": {"x": C, "y": C}},
        "effect": {"kind": anim, "progress": round((frame_idx + 0.5) / nframes, 4)},
    }


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_sheet(
        fx=FX,
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=_draw_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        frame_meta_fn=_frame_meta,
        auto_crop=True,
        crop_margin=6,
        actor_metadata=ACTOR_METADATA,
    )
    return [
        outputs["spritesheet"],
        outputs["yaml"],
        outputs["ron"],
        outputs["actor"],
        outputs["preview"],
        outputs["canonical"],
        outputs["canonical_transparent"],
    ]


def render_canonical(out_dir: str | Path, **opts) -> Path:
    del opts
    return write_canonical(TARGET_NAME, ROWS, _draw_frame, Path(out_dir), frame_size=FRAME_SIZE, crop_margin=6)


__all__ = ["ACTOR_METADATA", "FX", "ROWS", "TARGET_NAME", "render", "render_canonical"]
