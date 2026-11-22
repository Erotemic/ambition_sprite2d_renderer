"""The Supreme Leader's shots (`docs/planning/game/bosses.md`, "The Supreme
Leader"). Each is a projectile look (`projectile_visuals.ron`).

- `supreme_leader_bolt`: the shot of his sceptre's orb, a crimson spark in a
  gold ring that leaves a short trail behind it. Its look turns it with its
  flight (`VelocityAligned`), so it is drawn travelling +x.
- `supreme_leader_shell`: a decree's shell, falling from the ceiling: an
  iron shell with a crimson band and a gold fuse cap, nose down, its fins
  rocking as it falls. Drawn falling +y; its look keeps it upright.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import List

from PIL import Image, ImageDraw, ImageFilter

from ...authoring.sheet_build import build_sheet

SS = 4


def _canvas(w, h):
    img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)  # raw-draw-ok: opaque strokes on a clear canvas


def _poly(d, pts, fill):
    d.polygon([(x * SS, y * SS) for x, y in pts], fill=fill)


def _dot(d, x, y, r, fill):
    d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], fill=fill)


BOLT_W, BOLT_H = 48, 24


def _bolt(frame_idx: int, nframes: int) -> Image.Image:
    glow, d_glow = _canvas(BOLT_W, BOLT_H)
    cx, cy = 34.0, 12.0
    k = 1.0 + 0.12 * math.sin(frame_idx / nframes * math.tau * 2)
    # The trail: crimson fading back along its flight.
    for i in range(10):
        u = i / 9
        _dot(d_glow, cx - 4 - 24 * u, cy, (5.5 - 3.5 * u) * k, (220, 40, 40, int(150 * (1 - u))))
    _dot(d_glow, cx, cy, 9 * k, (255, 70, 50, 120))
    glow = glow.filter(ImageFilter.GaussianBlur(2.5 * SS))
    img, d = _canvas(BOLT_W, BOLT_H)
    img.alpha_composite(glow)
    d = ImageDraw.Draw(img)  # raw-draw-ok: opaque strokes on a clear canvas
    # The gold ring, turning.
    a = frame_idx / nframes * math.tau
    rx = 6.0 * abs(math.cos(a)) + 1.5
    d.ellipse([(cx - rx) * SS, (cy - 6.5) * SS, (cx + rx) * SS, (cy + 6.5) * SS], outline=(232, 186, 74, 255), width=int(1.4 * SS))
    _dot(d, cx, cy, 4.2 * k, (200, 28, 36, 255))
    _dot(d, cx + 0.8, cy - 0.8, 2.2, (255, 214, 190, 255))
    return img.resize((BOLT_W, BOLT_H), Image.LANCZOS)


SHELL_W, SHELL_H = 28, 44


def _shell(frame_idx: int, nframes: int) -> Image.Image:
    img, d = _canvas(SHELL_W, SHELL_H)
    rock = 2.0 * math.sin(frame_idx / nframes * math.tau)
    cx = 14.0
    # Fins at the top (it falls nose down), rocking.
    _poly(d, [(cx - 3, 6), (cx - 10 + rock, 1), (cx - 9 + rock, 10), (cx - 3, 12)], (48, 44, 52, 255))
    _poly(d, [(cx + 3, 6), (cx + 10 + rock, 1), (cx + 9 + rock, 10), (cx + 3, 12)], (48, 44, 52, 255))
    # The body.
    _poly(d, [(cx - 7, 8), (cx + 7, 8), (cx + 7, 30), (cx, 41), (cx - 7, 30)], (78, 74, 86, 255))
    _poly(d, [(cx - 7, 8), (cx - 3, 8), (cx - 3, 31), (cx - 7, 30)], (112, 108, 122, 255))
    # The crimson band and the gold fuse cap at the nose.
    _poly(d, [(cx - 7, 17), (cx + 7, 17), (cx + 7, 22), (cx - 7, 22)], (178, 30, 40, 255))
    _poly(d, [(cx - 3.5, 36), (cx + 3.5, 36), (cx, 42)], (226, 178, 70, 255))
    return img.resize((SHELL_W, SHELL_H), Image.LANCZOS)


def _target(name, draw, size, frames, ms, intent):
    rows = [("travel", frames, ms)]
    meta = {
        "actor": {"character_id": f"prop_{name}", "display_name": name.replace("_", " ").title()},
        "visual_description": {"intent": intent},
        "tags": ["projectile", "regime", "supreme_leader"],
    }

    def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
        del animation
        return draw(frame_idx, nframes)

    def render(out_dir: str | Path, **opts) -> List[Path]:
        del opts
        outputs = build_sheet(target=name, rows=rows, render_fn=render_frame, out_dir=Path(out_dir), frame_size=size,
                              auto_crop=False, actor_metadata=meta)
        keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
        return [Path(outputs[key]) for key in keys if outputs.get(key)]

    return {"render": render, "actor_metadata": meta}


TARGETS = {
    "supreme_leader_bolt": _target("supreme_leader_bolt", _bolt, (BOLT_W, BOLT_H), 6, 60,
                                   "A crimson spark in a turning gold ring, trailing red."),
    "supreme_leader_shell": _target("supreme_leader_shell", _shell, (SHELL_W, SHELL_H), 6, 70,
                                    "An iron artillery shell with a crimson band, falling nose down."),
}

__all__ = ["TARGETS"]
