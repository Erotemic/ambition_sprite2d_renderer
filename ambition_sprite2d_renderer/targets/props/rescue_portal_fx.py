"""The gate network's rescue (the game's PLAYER-DEATH, Q174: "just before the
blow lands, a portal opens and yoinks the body away"): two one-shot effects
drawn as one of the interdimensional gate's triangle doors.

- ``take``: three rays draw the door round the body, it opens on the gate's
  tunnel of whirling triangles, a dark wave falls inward as the body is
  pulled in, and the door turns a third and falls into its centre.
- ``give``: the door opens where the body comes back, a bright wave and the
  light the body steps out of, and it folds away.

Its own sheet because the rows draw their own start and end (each ends on a
clear frame): the game draws each frame at full strength (``InItsFrames``),
where the generic catalogs fade an effect over its clip and would wash out
the swallow and the snap shut.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image

from ...authoring.sheet_build import build_sheet, write_canonical
from .generic_exotic_fx import (
    SUPER,
    WHITE,
    _clamp,
    _ease_out,
    _ellipse,
    _lerp,
    _line,
    _mul_alpha,
    _polygon,
    _smooth,
)

Point = Tuple[float, float]

TARGET_NAME = "rescue_portal_fx"
# An effect sheet (`SheetRecord::fx`): decoded at boot and kept, so a first
# death draws its door; its frames draw their own start and end.
FX = {"cue_family": "rescue_portal", "residency": "Core", "fade": "InItsFrames"}
FRAME_SIZE = (192, 192)
W, H = FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER
ROWS: List[Tuple[str, int, int]] = [
    ("rescue_portal_take", 16, 42),
    ("rescue_portal_give", 14, 42),
]
ORIGIN = (96.0, 100.0)

ACTOR_METADATA = {
    "actor": {"character_id": f"fx_{TARGET_NAME}", "display_name": "Rescue Portal FX"},
    "body": {
        "body_plan": "Effect",
        "body_kind": "Overlay",
        "mass_class": "Light",
        "locomotion_hint": "Stationary",
        "traits": ["fx", "overlay", "presentation"],
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "sockets": {"origin": {"source": f"{TARGET_NAME}.geometry", "point": {"x": ORIGIN[0], "y": ORIGIN[1]}}},
    "tags": ["fx", "overlay", "presentation"],
}


# The interdimensional gate's light (``interdimensional_gate.GLYPH_CORE`` and
# ``GLYPH_GLOW``) and its tunnel's depth (``_gate_wormhole_triangles``): the
# rescue is the gate network's, so it is drawn as one of its doors.
GATE_CORE = (143, 246, 255, 255)
GATE_GLOW = (57, 212, 255, 255)
GATE_FAR = (168, 96, 255, 255)
VOID_DEEP = (6, 4, 26, 255)
VOID_MID = (30, 22, 92, 255)


def _triangle(cx: float, cy: float, r: float, turn: float) -> List[Point]:
    return [
        (cx + math.cos(turn - math.pi / 2 + math.tau * i / 3) * r,
         cy + math.sin(turn - math.pi / 2 + math.tau * i / 3) * r)
        for i in range(3)
    ]


def _inscribed(tri: Sequence[Point], f: float) -> List[Point]:
    """Each corner `f` of the way along the outer triangle's edge: the gate's
    whirling tunnel step."""
    return [(_lerp(tri[i][0], tri[(i + 1) % 3][0], f), _lerp(tri[i][1], tri[(i + 1) % 3][1], f)) for i in range(3)]


def _gate_door(img: Image.Image, cx: float, cy: float, r: float, turn: float, open_: float,
               spin: float, depth: float, edge: float) -> None:
    """A triangle door of the gate network: its void, the tunnel of whirling
    triangles in it, and its lit edge. `open_` scales the door from its
    centre; `depth` darkens the tunnel (a body going in) and `edge` the
    rim's light."""
    if open_ <= 0.02:
        return
    outer = _triangle(cx, cy, r * open_, turn)
    _polygon(img, _triangle(cx, cy, r * open_ * 1.12, turn), fill=_mul_alpha(GATE_GLOW, 0.22 * edge))
    _polygon(img, outer, fill=_mul_alpha(VOID_MID, 0.92))
    level = outer
    for k in range(6):
        level = _inscribed(level, 0.2 + 0.06 * math.sin(spin + k * 0.7))
        shade = VOID_DEEP if k >= 3 else VOID_MID
        _polygon(img, level, fill=_mul_alpha(shade, 0.55 + 0.08 * k * depth),
                 outline=_mul_alpha(GATE_FAR if k % 2 else GATE_GLOW, (0.70 - 0.09 * k) * edge), width=1.0)
    _polygon(img, outer, outline=_mul_alpha(GATE_CORE, 0.95 * edge), width=2.2)
    # Three sparks run round the rim, one edge each.
    for i in range(3):
        t = (spin / math.tau * 1.5 + i / 3.0) % 1.0
        a, b = outer[i], outer[(i + 1) % 3]
        x, y = _lerp(a[0], b[0], t), _lerp(a[1], b[1], t)
        _ellipse(img, (x - 2.2 * r / 46.0, y - 2.2 * r / 46.0, x + 2.2 * r / 46.0, y + 2.2 * r / 46.0), fill=_mul_alpha(WHITE, 0.9 * edge))


def _draw_rescue_portal(img: Image.Image, p: float, give: bool) -> None:
    cx, cy, r = 96.0, 100.0, 72.0
    k = r / 46.0
    # The door is drawn by three rays from its corners, as the gate's is.
    draw = _smooth(_clamp(p / 0.22))
    if draw < 1.0:
        corners = _triangle(cx, cy, r, 0.0)
        for i in range(3):
            a, b = corners[i], corners[(i + 1) % 3]
            end = (_lerp(a[0], b[0], draw), _lerp(a[1], b[1], draw))
            _line(img, [a, end], fill=_mul_alpha(GATE_CORE, 0.95), width=2.0)
            _ellipse(img, (a[0] - 3 * k, a[1] - 3 * k, a[0] + 3 * k, a[1] + 3 * k), fill=_mul_alpha(WHITE, 0.9))
    spin = math.tau * p * 1.4
    if give:
        # Opens wide, flashes white as the body comes out, folds away.
        open_ = _ease_out(_clamp((p - 0.12) / 0.25)) * (1.0 - _smooth(_clamp((p - 0.70) / 0.24)))
        _gate_door(img, cx, cy, r, 0.0, open_, spin, 0.4, 1.0)
        swell = math.sin(math.pi * _clamp((p - 0.32) / 0.36))
        if swell > 0.0:
            # The emit wave: a bright triangle from the centre to the lip,
            # and the light the body steps out of.
            _polygon(img, _triangle(cx, cy, r * open_ * (0.2 + 0.8 * _clamp((p - 0.32) / 0.36)), 0.0),
                     outline=_mul_alpha(WHITE, 0.9 * swell), width=3.0)
            _ellipse(img, (cx - 20 * k * swell, cy - 28 * k * swell, cx + 20 * k * swell, cy + 28 * k * swell),
                     fill=_mul_alpha(GATE_CORE, 0.75 * swell))
            _ellipse(img, (cx - 10 * k * swell, cy - 16 * k * swell, cx + 10 * k * swell, cy + 16 * k * swell),
                     fill=_mul_alpha(WHITE, 0.85 * swell))
        return
    # Takes: opens round the body, a dark wave falls inward as it is pulled
    # in, then the door turns a third and falls into its centre.
    open_ = _ease_out(_clamp((p - 0.12) / 0.22))
    close = _smooth(_clamp((p - 0.66) / 0.24))
    turn = close * math.tau / 3
    _gate_door(img, cx, cy, r, turn, open_ * (1.0 - close), spin, 1.0 + close, 1.0 - 0.3 * close)
    pull = _clamp((p - 0.34) / 0.34)
    if 0.0 < pull < 1.0:
        _polygon(img, _triangle(cx, cy, r * open_ * (1.0 - pull), turn),
                 outline=_mul_alpha(VOID_DEEP, 0.9), width=3.0)
        # Strands of the body drawn in toward the centre.
        for i in range(9):
            a = math.tau * i / 9 + p * 3.0
            d0 = r * 0.75 * (1.0 - pull) + 6 * k
            d1 = d0 * 0.45
            _line(img, [(cx + math.cos(a) * d0, cy + math.sin(a) * d0),
                        (cx + math.cos(a) * d1, cy + math.sin(a) * d1)],
                  fill=_mul_alpha(GATE_CORE if i % 2 else GATE_FAR, 0.75 * (1.0 - pull)), width=1.2)
    flash = math.sin(math.pi * _clamp((p - 0.86) / 0.12))
    if flash > 0.0:
        _ellipse(img, (cx - 9 * k * flash, cy - 9 * k * flash, cx + 9 * k * flash, cy + 9 * k * flash), fill=_mul_alpha(WHITE, 0.95 * flash))
        for i in range(3):
            a = -math.pi / 2 + math.tau * i / 3
            _line(img, [(cx, cy), (cx + math.cos(a) * 22 * k * flash, cy + math.sin(a) * 22 * k * flash)],
                  fill=_mul_alpha(GATE_CORE, 0.9 * flash), width=1.6)


def _draw_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    if frame_idx == nframes - 1:
        return Image.new("RGBA", FRAME_SIZE, (0, 0, 0, 0))
    p = frame_idx / max(1, nframes - 1)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    _draw_rescue_portal(img, p, anim == "rescue_portal_give")
    return img.resize(FRAME_SIZE, Image.Resampling.NEAREST)


def _frame_meta(anim: str, frame_idx: int, nframes: int) -> dict:
    return {
        "anchors": {"origin": {"x": ORIGIN[0], "y": ORIGIN[1]}},
        "effect": {
            "family": "phase_magic",
            "progress": round(frame_idx / max(1, nframes - 1), 4),
            "clear_frame": frame_idx == nframes - 1,
        },
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
        crop_margin=5,
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
    return write_canonical(TARGET_NAME, ROWS, _draw_frame, Path(out_dir), frame_size=FRAME_SIZE, crop_margin=5)
