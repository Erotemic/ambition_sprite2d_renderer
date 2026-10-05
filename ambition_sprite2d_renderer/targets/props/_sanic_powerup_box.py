"""Shared art for Sanic's power-up boxes: a chunky item monitor with an icon on its screen.

A steel monitor on a squat base, bolted at the corners, its dark glass screen
showing the power-up's icon behind rolling scanlines and a glint. Break it and
it squashes, flashes, bursts into shards, and the icon pops up out of it and
hangs there glowing while the power-up takes; what is left is the smashed
lower shell.

Rows (every box the same, the icon is what differs):

- ``idle``: the scanlines roll, a glint sweeps the glass (loops);
- ``break``: hit, flash, shards, the icon rising (once);
- ``broken``: the empty smashed shell (one frame).

The case, the icon and the broken shell are SVG layers rasterized once at the
supersample; each frame composes them and paints the scanlines, the glint, the
flash and the shards. The frame is a full 128 px square (no auto-crop, so the
flying shards never resize it), standing on the ground at y=116.

Private module: discovery ignores ``targets/props/_*.py``. The public targets
(``sanic_powerup_speed``, ``sanic_powerup_rings``,
``sanic_powerup_invincibility``) call :func:`build` with their icon.
"""

from __future__ import annotations

import io
import math
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image

from ...authoring.sheet_build import build_sheet, write_canonical
from ...authoring.svg_parts import _svg_to_png_bytes
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

SUPER = 4
FRAME_SIZE = (128, 128)
GROUND_Y = 116.0
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 110),
    ("break", 9, 55),
    ("broken", 1, 100),
]
SHEET_FILES_SUFFIXES = ("_spritesheet.png", "_spritesheet.yaml", "_spritesheet.ron", "_actor.ron")

#: The case and its screen, in frame pixels.
CASE = (34.0, 36.0, 94.0, 106.0)
SCREEN = (42.0, 44.0, 86.0, 84.0)
SCREEN_CENTER = (64.0, 64.0)

INK = "#14161c"
STEEL = "#b9c2cf"
STEEL_LIGHT = "#e6ebf2"
STEEL_DARK = "#7d8796"
STEEL_DEEP = "#525b69"
GLASS = "#1a2d4a"
GLASS_DEEP = "#0d1a2e"


def _svg(body: str) -> str:
    w, h = FRAME_SIZE
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w * SUPER}" height="{h * SUPER}" '
            f'viewBox="0 0 {w} {h}"><g stroke-linejoin="round" stroke-linecap="round">{body}</g></svg>')


@lru_cache(maxsize=16)
def _layer(svg: str) -> Image.Image:
    return Image.open(io.BytesIO(_svg_to_png_bytes(svg, 96.0))).convert("RGBA")


def _bolts(points) -> str:
    out = []
    for x, y in points:
        out.append(f'<circle cx="{x}" cy="{y}" r="2.1" fill="{STEEL_DARK}" stroke="{INK}" stroke-width="0.7"/>'
                   f'<circle cx="{x - 0.6}" cy="{y - 0.6}" r="0.7" fill="{STEEL_LIGHT}"/>')
    return "".join(out)


CASE_SVG = _svg(f"""
  <ellipse cx="64" cy="{GROUND_Y - 0.5}" rx="40" ry="4" fill="#000000" fill-opacity="0.3"/>
  <!-- the base -->
  <path d="M30 104 L98 104 L100 113 Q100 116 96 116 L32 116 Q28 116 28 113 Z" fill="{STEEL_DARK}"
        stroke="{INK}" stroke-width="1.4"/>
  <path d="M31 106 L97 106" stroke="{STEEL}" stroke-width="1.2" fill="none"/>
  <!-- the case -->
  <rect x="34" y="36" width="60" height="70" rx="7" fill="{STEEL}" stroke="{INK}" stroke-width="1.6"/>
  <path d="M37 40 Q38 38 42 38 L86 38 Q90 38 91 40" stroke="{STEEL_LIGHT}" stroke-width="2" fill="none"/>
  <path d="M35 92 L93 92 L93 99 Q93 105 87 105 L41 105 Q35 105 35 99 Z" fill="{STEEL_DARK}"/>
  <path d="M90 42 L90 90" stroke="{STEEL_DARK}" stroke-width="2" fill="none"/>
  <rect x="34" y="36" width="60" height="70" rx="7" fill="none" stroke="{INK}" stroke-width="1.6"/>
  <!-- the speaker grille and a status light under the screen -->
  <path d="M44 95 L56 95 M44 98.5 L56 98.5 M44 102 L56 102" stroke="{STEEL_DEEP}" stroke-width="1.3" fill="none"/>
  <circle cx="82" cy="98.5" r="2.6" fill="#38e07a" stroke="{INK}" stroke-width="0.8"/>
  <circle cx="81.3" cy="97.8" r="0.9" fill="#d8ffe6"/>
  {_bolts([(39, 41), (89, 41), (39, 88), (89, 88)])}
  <!-- the screen: a dark bezel, the glass -->
  <rect x="40" y="42" width="48" height="44" rx="5" fill="{STEEL_DEEP}" stroke="{INK}" stroke-width="1.2"/>
  <rect x="42" y="44" width="44" height="40" rx="4" fill="{GLASS}"/>
  <path d="M42 70 Q64 76 86 70 L86 80 Q86 84 82 84 L46 84 Q42 84 42 80 Z" fill="{GLASS_DEEP}"/>
""")

BROKEN_SVG = _svg(f"""
  <ellipse cx="64" cy="{GROUND_Y - 0.5}" rx="40" ry="4" fill="#000000" fill-opacity="0.3"/>
  <path d="M30 104 L98 104 L100 113 Q100 116 96 116 L32 116 Q28 116 28 113 Z" fill="{STEEL_DARK}"
        stroke="{INK}" stroke-width="1.4"/>
  <!-- the lower shell, torn open along a jagged edge -->
  <path d="M34 106 L34 80 L40 74 L45 82 L52 72 L58 80 L64 70 L71 79 L77 73 L83 81 L89 74 L94 80 L94 106 Z"
        fill="{STEEL}" stroke="{INK}" stroke-width="1.6"/>
  <path d="M40 76 L45 84 L52 74 L58 82 L64 72 L71 81 L77 75 L83 83 L88 77 L88 86 L40 86 Z" fill="{GLASS_DEEP}"/>
  <path d="M35 92 L93 92 L93 99 Q93 105 87 105 L41 105 Q35 105 35 99 Z" fill="{STEEL_DARK}"/>
  <path d="M44 95 L56 95 M44 98.5 L56 98.5 M44 102 L56 102" stroke="{STEEL_DEEP}" stroke-width="1.3" fill="none"/>
  <circle cx="82" cy="98.5" r="2.6" fill="#5a2a2a" stroke="{INK}" stroke-width="0.8"/>
  <path d="M46 86 L50 90 M70 86 L66 91 M78 86 L81 90" stroke="{INK}" stroke-width="0.9" fill="none"/>
  {_bolts([(39, 88), (89, 88)])}
  <path d="M34 106 L34 80 L40 74 L45 82 L52 72 L58 80 L64 70 L71 79 L77 73 L83 81 L89 74 L94 80 L94 106 Z"
        fill="none" stroke="{INK}" stroke-width="1.6"/>
""")

# ---- icons (SVG fragments centred on the screen) ---------------------------------


def icon_svg(fragment: str) -> str:
    """A full-frame layer with ``fragment`` (drawn about (0, 0), about 34 px
    across) centred on the screen."""
    x, y = SCREEN_CENTER
    return _svg(f'<g transform="translate({x} {y})">{fragment}</g>')


SPEED_ICON = f"""
  <!-- speed lines streaming behind -->
  <path d="M-19 -6 L-9 -6 M-21 0 L-10 0 M-19 6 L-11 6" stroke="#9fd8ff" stroke-width="2" fill="none"/>
  <!-- a red sneaker: sole, toe cap, a white strap with a gold buckle -->
  <path d="M-12 -9 Q-10 -14 -4 -13 L1 -11 Q6 -5 12 -3 Q18 -1 18 5 L18 7 L-12 7 Z" fill="#e3263a" stroke="{INK}"
        stroke-width="1.2"/>
  <path d="M-12 -9 Q-14 -2 -12 7" fill="none" stroke="{INK}" stroke-width="1.2"/>
  <path d="M10 -3.6 Q17 -1.5 18 5 L13 5 Q12 0 8 -2 Z" fill="#ffffff"/>
  <path d="M-2 -11 L4 -5 L1 -3 L-5 -9 Z" fill="#ffffff" stroke="{INK}" stroke-width="0.8"/>
  <rect x="-1.4" y="-9.4" width="3.4" height="3.4" rx="0.6" fill="#ffd34d" stroke="{INK}" stroke-width="0.6"
        transform="rotate(42 0.3 -7.7)"/>
  <path d="M-14 6 L20 6 Q21 11 17 12 L-13 12 Q-15 11 -14 6 Z" fill="#f4f6fa" stroke="{INK}" stroke-width="1.2"/>
  <path d="M-12 10 L18 10" stroke="#b9c2cf" stroke-width="1" fill="none"/>
  <path d="M-8 -11 Q-5 -12 -1 -10" stroke="#ff8a96" stroke-width="1.4" fill="none"/>
"""

RING_ICON = f"""
  <circle cx="0" cy="0" r="12" fill="none" stroke="{INK}" stroke-width="8"/>
  <circle cx="0" cy="0" r="12" fill="none" stroke="#e9a91c" stroke-width="6"/>
  <circle cx="0" cy="0" r="12" fill="none" stroke="#ffd24a" stroke-width="3.2"/>
  <path d="M-9 -7 A12 12 0 0 1 4 -11.4" stroke="#fff6c2" stroke-width="1.8" fill="none"/>
  <path d="M10 -14 L11.2 -10.8 L14.4 -9.6 L11.2 -8.4 L10 -5.2 L8.8 -8.4 L5.6 -9.6 L8.8 -10.8 Z" fill="#ffffff"/>
"""


def _star(r: float, inner: float, rot: float = -90.0) -> str:
    pts = []
    for k in range(10):
        rr = r if k % 2 == 0 else r * inner
        a = math.radians(rot + 36.0 * k)
        pts.append(f"{rr * math.cos(a):.2f},{rr * math.sin(a):.2f}")
    return "M" + " L".join(pts) + " Z"


INVINCIBLE_ICON = f"""
  <circle cx="0" cy="1" r="17" fill="#ffffff" fill-opacity="0.14"/>
  <path d="{_star(16, 0.46)}" fill="#ff9d1c" stroke="{INK}" stroke-width="1.3"/>
  <path d="{_star(12.5, 0.46)}" fill="#ffd93a" transform="translate(-0.6 -0.6)"/>
  <path d="{_star(6, 0.46)}" fill="#fff6c8" transform="translate(-1.8 -2.2)"/>
  <circle cx="-3.5" cy="-1" r="1.4" fill="{INK}"/>
  <circle cx="3.5" cy="-1" r="1.4" fill="{INK}"/>
  <path d="M-12 -14 L-11.2 -12 L-9.2 -11.2 L-11.2 -10.4 L-12 -8.4 L-12.8 -10.4 L-14.8 -11.2 L-12.8 -12 Z"
        fill="#9fe8ff"/>
  <path d="M14 8 L14.8 10 L16.8 10.8 L14.8 11.6 L14 13.6 L13.2 11.6 L11.2 10.8 L13.2 10 Z" fill="#ff9ff0"/>
"""

#: The icons' glow on the glass, by icon.
ICON_GLOW: Dict[str, RGBA] = {
    "speed": (120, 200, 255, 255),
    "rings": (255, 214, 80, 255),
    "invincibility": (255, 236, 140, 255),
}

# ---- per-frame painting -----------------------------------------------------------


def _p(v: float) -> float:
    return v * SUPER


def _screen_effects(canvas: Image.Image, phase: float, glow: RGBA) -> None:
    """Scanlines rolling down the glass, a soft glow, a glint sweeping across."""
    x0, y0, x1, y1 = SCREEN
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = blending_draw(layer)
    cx, cy = SCREEN_CENTER
    d.ellipse((_p(cx - 20), _p(cy - 17), _p(cx + 20), _p(cy + 17)), fill=glow[:3] + (34,))
    offset = (phase * 4.0) % 4.0
    y = y0 + offset
    while y < y1:
        d.line([(_p(x0 + 1), _p(y)), (_p(x1 - 1), _p(y))], fill=(0, 0, 0, 52), width=SUPER)
        y += 4.0
    # The glint: a slanted band crossing the glass once a loop.
    gx = x0 - 16 + (x1 - x0 + 32) * phase
    band = [(_p(gx), _p(y0)), (_p(gx + 8), _p(y0)), (_p(gx - 6), _p(y1)), (_p(gx - 14), _p(y1))]
    d.polygon(band, fill=(255, 255, 255, 60))
    # Clip to the glass.
    mask = Image.new("L", canvas.size, 0)
    blending_draw(mask).rounded_rectangle((_p(x0), _p(y0), _p(x1), _p(y1)), radius=_p(4), fill=255)
    layer.putalpha(Image.composite(layer.getchannel("A"), Image.new("L", canvas.size, 0), mask))
    canvas.alpha_composite(layer)
    d = blending_draw(canvas)
    d.line([(_p(x0 + 3), _p(y0 + 3)), (_p(x0 + 14), _p(y0 + 3))], fill=(255, 255, 255, 120), width=int(_p(1.4)))


def _squash(img: Image.Image, scale_y: float, scale_x: float) -> Image.Image:
    """``img`` squashed about the ground line's centre."""
    w, h = img.size
    nw, nh = int(round(w * scale_x)), int(round(h * scale_y))
    small = img.resize((nw, nh), Image.Resampling.LANCZOS)
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gx, gy = _p(64.0), _p(GROUND_Y)
    out.alpha_composite(small, (int(round(gx - gx * scale_x)), int(round(gy - gy * scale_y))))
    return out


def _flash(img: Image.Image, amount: float) -> Image.Image:
    """``img`` washed toward white, keeping its alpha."""
    white = Image.new("RGBA", img.size, (255, 255, 255, 255))
    white.putalpha(img.getchannel("A"))
    return Image.blend(img, white, amount)


#: Shards of case and glass: (direction degrees, speed, spin, size, colour).
SHARDS = (
    (-150, 1.0, 1.0, 5.0, (185, 194, 207, 255)),
    (-120, 1.2, -1.0, 4.0, (26, 45, 74, 255)),
    (-95, 1.1, 1.0, 4.5, (230, 235, 242, 255)),
    (-70, 1.25, -1.0, 4.0, (26, 45, 74, 255)),
    (-40, 1.0, 1.0, 5.0, (185, 194, 207, 255)),
    (-20, 0.8, -1.0, 3.5, (125, 135, 150, 255)),
    (-165, 0.75, 1.0, 3.5, (125, 135, 150, 255)),
    (-55, 0.9, 1.0, 3.0, (140, 210, 255, 255)),
)


def _shards(canvas: Image.Image, s: float) -> None:
    """Shards flung up and out of the case at ``s`` (0..1 of their flight),
    falling under gravity and fading."""
    d = blending_draw(canvas)
    cx, cy = 64.0, 66.0
    for k, (deg, speed, spin, size, color) in enumerate(SHARDS):
        a = math.radians(deg)
        dist = 46.0 * speed * s
        x = cx + math.cos(a) * dist
        y = min(cy + math.sin(a) * dist + 60.0 * s * s, GROUND_Y - 2.0)
        rot = math.radians(spin * 400.0 * s + 40 * k)
        pts = [(x + size * math.cos(rot + q), y + size * 0.7 * math.sin(rot + q)) for q in (0.0, 2.3, 4.1)]
        alpha = int(255 * max(0.0, 1.0 - max(0.0, s - 0.55) / 0.45))
        d.polygon([(_p(px), _p(py)) for px, py in pts], fill=color[:3] + (alpha,),
                  outline=(20, 22, 28, alpha), width=SUPER)


def _burst(canvas: Image.Image, amount: float) -> None:
    """The bang: a white star over the case."""
    if amount <= 0.02:
        return
    d = blending_draw(canvas)
    cx, cy = SCREEN_CENTER
    pts = []
    for k in range(16):
        r = (34.0 if k % 2 == 0 else 13.0) * (0.7 + 0.3 * amount)
        a = math.radians(-90 + 22.5 * k)
        pts.append((_p(cx + r * math.cos(a)), _p(cy + r * math.sin(a))))
    d.polygon(pts, fill=(255, 255, 240, int(220 * amount)))


def _icon_glow(canvas: Image.Image, at: Point, glow: RGBA, amount: float) -> None:
    if amount <= 0.02:
        return
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = blending_draw(layer)
    for r, alpha in ((26, 40), (20, 60), (15, 80)):
        d.ellipse((_p(at[0] - r), _p(at[1] - r), _p(at[0] + r), _p(at[1] + r)), fill=glow[:3] + (int(alpha * amount),))
    canvas.alpha_composite(layer)


#: The break, frame by frame: (squash y, squash x, flash, burst, shell shown
#: as "intact"/"broken", shard flight, icon rise in px, icon glow, icon opacity).
BREAK_KEYS = (
    (0.86, 1.08, 0.0, 0.0, "intact", 0.0, 0.0, 0.0, 1.0),
    (1.05, 0.97, 0.75, 0.6, "intact", 0.0, 0.0, 0.3, 1.0),
    (1.0, 1.0, 0.0, 1.0, "broken", 0.12, -8.0, 0.8, 1.0),
    (1.0, 1.0, 0.0, 0.4, "broken", 0.3, -18.0, 1.0, 1.0),
    (1.0, 1.0, 0.0, 0.0, "broken", 0.48, -26.0, 1.0, 1.0),
    (1.0, 1.0, 0.0, 0.0, "broken", 0.64, -30.0, 0.9, 1.0),
    (1.0, 1.0, 0.0, 0.0, "broken", 0.8, -32.0, 1.0, 1.0),
    (1.0, 1.0, 0.0, 0.0, "broken", 0.92, -33.0, 0.7, 0.7),
    (1.0, 1.0, 0.0, 0.0, "broken", 1.0, -34.0, 0.4, 0.35),
)


def frame_painter(icon: str, icon_kind: str):
    """The ``render_fn`` for one box: ``icon`` is an SVG fragment drawn about
    (0, 0); ``icon_kind`` picks its glow (``ICON_GLOW``)."""
    glow = ICON_GLOW[icon_kind]

    def intact(phase: float) -> Image.Image:
        canvas = Image.new("RGBA", (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER), (0, 0, 0, 0))
        canvas.alpha_composite(_layer(CASE_SVG))
        canvas.alpha_composite(_layer(icon_svg(icon)))
        _screen_effects(canvas, phase, glow)
        return canvas

    def draw_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
        if anim == "idle":
            canvas = intact(frame_idx / max(1, nframes))
        elif anim == "broken":
            canvas = Image.new("RGBA", (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER), (0, 0, 0, 0))
            canvas.alpha_composite(_layer(BROKEN_SVG))
        elif anim == "break":
            sy, sx, flash, burst, shell, shard, rise, glow_amt, icon_alpha = BREAK_KEYS[frame_idx]
            if shell == "intact":
                canvas = _squash(intact(0.0), sy, sx)
                if flash > 0.0:
                    canvas = _flash(canvas, flash)
            else:
                canvas = Image.new("RGBA", (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER), (0, 0, 0, 0))
                canvas.alpha_composite(_layer(BROKEN_SVG))
                at = (SCREEN_CENTER[0], SCREEN_CENTER[1] + rise)
                _icon_glow(canvas, at, glow, glow_amt)
                icon_layer = _layer(icon_svg(icon))
                if icon_alpha < 1.0:
                    icon_layer = icon_layer.copy()
                    icon_layer.putalpha(icon_layer.getchannel("A").point(lambda v: int(v * icon_alpha)))
                canvas.alpha_composite(icon_layer, (0, int(round(_p(rise)))) if rise >= 0 else (0, 0),
                                       (0, int(round(_p(-rise)))) if rise < 0 else (0, 0))
                _shards(canvas, shard)
            _burst(canvas, burst)
        else:
            raise ValueError(f"unknown animation: {anim}")
        return canvas.resize(FRAME_SIZE, Image.Resampling.LANCZOS)

    return draw_frame


def build(out_dir: str | Path, *, target_name: str, icon: str, icon_kind: str, display: str,
          effect: str) -> List[Path]:
    """Render one power-up box's sheet. ``effect`` names the power-up the
    ``break`` row's ``grant_powerup`` event grants (in the frame metadata and
    the tags)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    draw_frame = frame_painter(icon, icon_kind)

    def frame_meta(anim: str, frame_idx: int, nframes: int) -> dict:
        rise = BREAK_KEYS[frame_idx][6] if anim == "break" else 0.0
        x, y = SCREEN_CENTER
        return {"anchors": {"center": {"x": x, "y": 71.0}, "icon": {"x": x, "y": y + rise}},
                "prop": {"kind": "powerup_box", "state": anim, "powerup": effect}}

    def body_metrics(fw: int, fh: int) -> dict:
        # The intact case is the solid body (it can be stood on); the shards
        # and the rising icon never widen it.
        x0, y0, x1, _y1 = CASE
        return {
            "body_pixel_bbox": {"x": int(x0) - 4, "y": int(y0), "w": int(x1 - x0) + 8, "h": int(GROUND_Y - y0)},
            "feet_pixel": {"x": fw / 2.0, "y": GROUND_Y},
            "feet_anchor_norm": {"x": 0.0, "y": -0.5},
        }

    actor_metadata = {
        "actor": {"character_id": target_name, "display_name": display},
        "body": {
            "body_plan": "Prop",
            "body_kind": "Device",
            "locomotion_hint": "Stationary",
            "traits": ["prop", "pickup", "powerup", "item_box", "breakable", "surface_locomotion_demo"],
        },
        "brain": {"default_preset": "stand_still"},
        "actions": {"default_preset": "peaceful"},
        "animation_bindings": {
            "default": {"animation": "idle", "events": []},
            "pickup.break": {
                "animation": "break",
                "events": [
                    {"t": 0.25, "event": "box_break", "source": target_name},
                    {"t": 0.75, "event": "grant_powerup", "source": target_name},
                ],
            },
            "state.broken": {"animation": "broken", "events": []},
        },
        "sockets": {
            "center": {"source": f"{target_name}.geometry", "point": {"x": 64.0, "y": 71.0}},
            "icon": {"source": f"{target_name}.geometry", "point": {"x": SCREEN_CENTER[0], "y": SCREEN_CENTER[1]}},
        },
        "tags": ["prop", "pickup", "powerup", "item_box", "animated", f"powerup_{effect}"],
    }

    outputs = build_sheet(
        target=target_name,
        rows=ROWS,
        render_fn=draw_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        frame_meta_fn=frame_meta,
        auto_crop=False,
        body_metrics_fn=body_metrics,
        actor_metadata=actor_metadata,
    )
    return [outputs[k] for k in ("spritesheet", "yaml", "ron", "actor", "preview", "canonical",
                                 "canonical_transparent") if outputs.get(k)]


def canonical(out_dir: str | Path, *, target_name: str, icon: str, icon_kind: str) -> Path:
    """The box's canonical image (its idle)."""
    return write_canonical(target_name, ROWS, frame_painter(icon, icon_kind), Path(out_dir), frame_size=FRAME_SIZE)


__all__ = ["FRAME_SIZE", "INVINCIBLE_ICON", "RING_ICON", "ROWS", "SHEET_FILES_SUFFIXES", "SPEED_ICON", "build",
           "canonical", "frame_painter"]
