"""The rescue's parcel: the coins a death's fee took, sealed by the gate
network where the body was taken (the game's PLAYER-DEATH, Q174: "the fee is
left at the spot as a recoverable cache, a sealed parcel at the rescue
portal's mouth").

A small parcel in the gate's colours (violet depth, cyan light), bound with
two bands and sealed with the gate's triangle. ``idle`` bobs and the seal
breathes; ``collect`` breaks the seal and the coins spring out.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from PIL import Image

from ...authoring.sheet_build import build_sheet, write_canonical
from ._sanic_support_prop_common import (
    FRAME_SIZE,
    SHEET_FILES_SUFFIXES,
    alpha,
    clamp01,
    downsample,
    new_frame,
    rgba,
    star,
)
from ambition_sprite2d_renderer.core.draw import blending_draw

TARGET_NAME = "rescue_parcel_prop"
SHEET_FILES = tuple(f"{TARGET_NAME}{suffix}" for suffix in SHEET_FILES_SUFFIXES)
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 130),
    ("collect", 7, 54),
]

# The interdimensional gate's light and its tunnel's depth.
OUTLINE = rgba("#120c2a")
BOX_DARK = rgba("#1e1650")
BOX = rgba("#33268a")
BOX_HI = rgba("#4d3cb8")
BAND = rgba("#39d4ff")
BAND_HI = rgba("#8ff6ff")
SEAL_CORE = rgba("#ecffff")
COIN = rgba("#f5b11e")
COIN_HI = rgba("#ffe88a")
COIN_DARK = rgba("#a65f08")

ACTOR_METADATA = {
    "actor": {"character_id": TARGET_NAME, "display_name": "Rescue Parcel"},
    "body": {
        "body_plan": "Prop",
        "body_kind": "Collectible",
        "locomotion_hint": "Stationary",
        "traits": ["prop", "pickup", "currency", "gate_network"],
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "pickup.collect": {"animation": "collect", "events": []},
    },
    "sockets": {
        "center": {"source": f"{TARGET_NAME}.geometry", "point": {"x": 64.0, "y": 62.0}},
        "pickup": {"source": f"{TARGET_NAME}.geometry", "point": {"x": 64.0, "y": 62.0}},
    },
    "tags": ["prop", "pickup", "currency", "animated"],
}


def _s(v: float) -> float:
    return v * 4


def _w(v: float) -> int:
    return max(1, int(round(v * 4)))


def _poly(points):
    return [(_s(x), _s(y)) for x, y in points]


def _geometry(anim: str, frame_idx: int, nframes: int) -> dict:
    if anim == "collect":
        p = clamp01(frame_idx / max(1, nframes - 1))
        return {"t": p, "cy": 62.0 - 4.0 * p, "glow": 1.0, "open": p, "alpha": 1.0 - 0.85 * max(0.0, p - 0.45) / 0.55}
    t = frame_idx / max(1, nframes)
    return {
        "t": t,
        "cy": 62.0 + 2.0 * math.sin(t * math.tau),
        "glow": 0.55 + 0.45 * (0.5 + 0.5 * math.sin(t * math.tau)),
        "open": 0.0,
        "alpha": 1.0,
    }


def _draw(img: Image.Image, g: dict) -> None:
    d = blending_draw(img)
    a, cx, cy, op = g["alpha"], 64.0, g["cy"], g["open"]
    hw, hh = 26.0, 20.0
    lid_lift = 14.0 * op
    # The box.
    body = [(cx - hw, cy - hh + 6), (cx + hw, cy - hh + 6), (cx + hw, cy + hh), (cx - hw, cy + hh)]
    d.polygon(_poly(body), fill=alpha(BOX, a), outline=alpha(OUTLINE, a), width=_w(1.2))
    d.polygon(_poly([(cx - hw, cy + hh - 7), (cx + hw, cy + hh - 7), (cx + hw, cy + hh), (cx - hw, cy + hh)]),
              fill=alpha(BOX_DARK, a))
    # Coins springing out of the opened parcel.
    if op > 0.0:
        for i in range(6):
            ang = -math.pi / 2 + (i - 2.5) * 0.42
            r = 8.0 + 46.0 * op
            x = cx + math.cos(ang) * r * 0.9
            y = cy - hh + 4 + math.sin(ang) * r + 30.0 * op * op
            d.ellipse((_s(x - 5), _s(y - 5), _s(x + 5), _s(y + 5)), fill=alpha(COIN, a), outline=alpha(COIN_DARK, a), width=_w(1.0))
            d.ellipse((_s(x - 2.2), _s(y - 3), _s(x + 0.8), _s(y + 0.5)), fill=alpha(COIN_HI, a))
    # The lid.
    ly = cy - hh - lid_lift
    tilt = 6.0 * op
    lid = [(cx - hw - 3, ly + tilt), (cx + hw + 3, ly - tilt), (cx + hw + 3, ly + 8 - tilt), (cx - hw - 3, ly + 8 + tilt)]
    d.polygon(_poly(lid), fill=alpha(BOX_HI, a), outline=alpha(OUTLINE, a), width=_w(1.2))
    # The bands, across the box and the lid.
    band_a = a * (1.0 - 0.6 * op)
    d.rectangle((_s(cx - 4), _s(cy - hh + 6), _s(cx + 4), _s(cy + hh)), fill=alpha(BAND, band_a))
    d.rectangle((_s(cx - 1.5), _s(cy - hh + 6), _s(cx - 0.2), _s(cy + hh)), fill=alpha(BAND_HI, band_a))
    d.rectangle((_s(cx - hw), _s(cy + 2), _s(cx + hw), _s(cy + 8)), fill=alpha(BAND, band_a))
    # The seal: the gate's triangle, glowing; it breaks as the parcel opens.
    glow = g["glow"] * (1.0 - op)
    sr = 11.0
    tri = [(cx + math.cos(-math.pi / 2 + math.tau * i / 3) * sr, cy + 4 + math.sin(-math.pi / 2 + math.tau * i / 3) * sr) for i in range(3)]
    halo = [(cx + (x - cx) * 1.45, cy + 4 + (y - cy - 4) * 1.45) for x, y in tri]
    d.polygon(_poly(halo), fill=alpha(BAND, 0.35 * glow * a))
    d.polygon(_poly(tri), fill=alpha(BOX_DARK, a * (1.0 - op)), outline=alpha(BAND_HI, (0.6 + 0.4 * glow) * a * (1.0 - op)), width=_w(2.0))
    inner = [(cx + (x - cx) * 0.45, cy + 4 + (y - cy - 4) * 0.45) for x, y in tri]
    d.polygon(_poly(inner), fill=alpha(SEAL_CORE, glow * a))
    if g["open"] == 0.0:
        t = g["t"]
        sx = cx + math.cos(t * math.tau) * hw * 0.8
        star(d, sx, cy - hh - 2, 3.0 + 2.0 * g["glow"], color=alpha(BAND_HI, 0.8 * g["glow"]), width=1.2)
    else:
        for i in range(5):
            ang = op * 2.0 + i * math.tau / 5
            r = 10.0 + 34.0 * op
            star(d, cx + math.cos(ang) * r, cy + 4 + math.sin(ang) * r, 3.0 + 3.0 * (1.0 - op),
                 color=alpha(BAND_HI, 0.9 * (1.0 - op)), width=1.2)


def _draw_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    img = new_frame()
    _draw(img, _geometry(anim, frame_idx, nframes))
    return downsample(img)


def _frame_meta(anim: str, frame_idx: int, nframes: int) -> dict:
    g = _geometry(anim, frame_idx, nframes)
    return {
        "anchors": {
            "center": {"x": 64.0, "y": round(g["cy"], 2)},
            "pickup": {"x": 64.0, "y": round(g["cy"], 2)},
        },
        "prop": {"kind": "parcel", "state": anim, "progress": round(g["t"], 4)},
    }


def _body_metrics(fw: int, fh: int) -> dict:
    # The collect row's coins must not grow the pickup's collision.
    return {
        "body_pixel_bbox": {"x": int(fw * 0.27), "y": int(fh * 0.28), "w": int(fw * 0.46), "h": int(fh * 0.40)},
        "feet_pixel": {"x": fw / 2.0, "y": fh * 0.66},
        "feet_anchor_norm": {"x": 0.0, "y": -0.5},
    }


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=_draw_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        frame_meta_fn=_frame_meta,
        auto_crop=True,
        crop_margin=6,
        body_metrics_fn=_body_metrics,
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
