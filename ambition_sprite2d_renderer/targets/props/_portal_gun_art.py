"""Shared art for the portal gun: a sleek handheld emitter.

A glossy white shell over a dark core housing; a glass tube along the top
with the mode's energy swirling inside; an angled dark grip with a trigger
guard; and at the front a dark collar from which three claw prongs reach
forward to cradle a glowing emitter core. Rendered AXIS-ALIGNED with the
muzzle facing RIGHT (+X); the game pins the ``grip`` socket to a hand and
rotates the sprite to aim.

The body is drawn as SVG in two layers, the parts behind the core and the
two claw prongs in front of it, rasterized once per colour at the
supersample (``_held_prop_common.SUPER``). Each frame paints the core, its
halo and the tube's energy between them, pulsing through the idle loop. The
mode colours (``glow`` / ``core`` / ``accent``) make ``portal_gun_blue`` and
``portal_gun_orange`` read as one gun in two modes; the game shows whichever
matches the active portal colour.

This is a ``_``-prefixed helper (no top-level ``render``) so the target
registry does not auto-register it; ``portal_gun_blue`` /
``portal_gun_orange`` call :func:`build`.
"""

from __future__ import annotations

import io
import math
from functools import lru_cache
from pathlib import Path
from typing import List, Tuple

from PIL import Image

from ...authoring.sheet_build import build_sheet
from ...authoring.svg_parts import _svg_to_png_bytes
from . import _held_prop_common as hp
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]

FRAME_SIZE = (180, 96)
ROWS: List[Tuple[str, int, int]] = [("idle", 4, 140)]

CY = FRAME_SIZE[1] * 0.5
GRIP_X = 64.0
MUZZLE_X = 158.0
#: The emitter core, cradled by the prongs just behind the muzzle.
CORE = (150.0, CY)
CORE_R = 6.5
#: The glass tube along the top: its ends and its centre line.
TUBE_X0, TUBE_X1, TUBE_Y = 60.0, 116.0, 26.0

INK = "#15171b"
SHELL = "#eef1f5"
SHELL_SHADE = "#c3cad3"
SHELL_DEEP = "#9aa3ae"
DARK = "#30353d"
DARK_MID = "#4a515b"
DARK_HI = "#6c7480"


def _hex(c: RGBA) -> str:
    return "#{:02x}{:02x}{:02x}".format(*c[:3])


def _svg(body: str) -> str:
    w, h = FRAME_SIZE
    s = hp.SUPER
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w * s}" height="{h * s}" viewBox="0 0 {w} {h}">'
            f'<g stroke-linejoin="round" stroke-linecap="round">{body}</g></svg>')


def _back_svg(accent: RGBA) -> str:
    a = _hex(accent)
    return _svg(f"""
  <!-- the glass tube's back wall and its mounts -->
  <rect x="{TUBE_X0}" y="{TUBE_Y - 5.5}" width="{TUBE_X1 - TUBE_X0}" height="11" rx="5.5"
        fill="{DARK}" stroke="{INK}" stroke-width="1.1"/>
  <rect x="{TUBE_X0 + 1.5}" y="{TUBE_Y - 3.8}" width="{TUBE_X1 - TUBE_X0 - 3}" height="7.6" rx="3.8"
        fill="{a}" fill-opacity="0.28"/>
  <path d="M72 31 L70 37 L80 37 L78 31 Z M100 31 L98 37 L108 37 L106 31 Z" fill="{DARK_MID}" stroke="{INK}"
        stroke-width="0.9"/>
  <!-- the grip, angled back, finger grooves on its front edge -->
  <path d="M55 57 L80 57 Q78 70 74 86 Q66 90 54 87 Q49 84 50 78 Z" fill="{DARK}" stroke="{INK}" stroke-width="1.3"/>
  <path d="M57 60 L76 60 L73 72 L56 70 Z" fill="{DARK_MID}"/>
  <path d="M75 64 Q71 66 74 69 M73 71 Q69 73 72 76 M71 78 Q67 80 70 83" fill="none" stroke="{INK}"
        stroke-width="1"/>
  <path d="M53 66 L52 84" stroke="{DARK_HI}" stroke-width="1.2" fill="none"/>
  <!-- the trigger and its guard -->
  <path d="M80 59 Q90 60 90 68 Q90 75 78 75" fill="none" stroke="{DARK}" stroke-width="2.6"/>
  <path d="M80 59 Q90 60 90 68 Q90 75 78 75" fill="none" stroke="{INK}" stroke-width="0.8"/>
  <path d="M81 60 Q85 64 82 70" fill="none" stroke="{DARK_HI}" stroke-width="2.2"/>
  <!-- the rear cap -->
  <path d="M46 33 Q32 34 30 46 Q31 60 46 62 Z" fill="{DARK}" stroke="{INK}" stroke-width="1.3"/>
  <path d="M36 41 L44 41 M35 46 L44 46 M36 51 L44 51" stroke="{DARK_HI}" stroke-width="1.3" fill="none"/>
  <!-- the shell: white, a dark seam along the middle -->
  <path d="M44 34 Q52 29 72 30 L118 32 Q128 34 130 44 L130 52 Q128 60 118 60 L58 61 Q46 61 44 56 Z"
        fill="{SHELL}" stroke="{INK}" stroke-width="1.4"/>
  <path d="M46 50 L130 50 L130 52 Q128 60 118 60 L58 61 Q46 61 44 56 Z" fill="{SHELL_SHADE}"/>
  <path d="M60 58 L120 58 Q126 57 128 54" stroke="{SHELL_DEEP}" stroke-width="1.6" fill="none"/>
  <path d="M50 35 Q60 32 74 33 L116 35 Q123 36 126 40" stroke="#ffffff" stroke-width="2.2" fill="none"/>
  <path d="M45 47 L130 47 L130 50 L46 50 Z" fill="{DARK}"/>
  <path d="M84 52.5 L96 52.5 M100 52.5 L112 52.5 M116 52.5 L122 52.5" stroke="{a}" stroke-width="2.2"
        fill="none"/>
  <path d="M44 34 Q52 29 72 30 L118 32 Q128 34 130 44 L130 52 Q128 60 118 60 L58 61 Q46 61 44 56 Z"
        fill="none" stroke="{INK}" stroke-width="1.4"/>
  <!-- the front collar the prongs grow from, and the short middle prong -->
  <path d="M128 37 L140 39 Q144 48 140 57 L128 59 Z" fill="{DARK}" stroke="{INK}" stroke-width="1.3"/>
  <path d="M131 41 L139 42 M131 55 L139 54" stroke="{DARK_HI}" stroke-width="1.1" fill="none"/>
  <path d="M139 45 Q146 44 147 48 Q146 52 139 51 Z" fill="{SHELL_SHADE}" stroke="{INK}" stroke-width="1.1"/>
""")


def _front_svg() -> str:
    """The top and bottom claw prongs, in front of the core."""
    prong = ("M134 38 Q140 26 152 27 Q161 29 162 39 Q159 37 155 36 Q150 34 144 36 Q140 37 138 41 Z")
    tip = "M156 31 Q161 32 162 39 Q159 37 155 36 Z"
    return _svg(f"""
  <path d="{prong}" fill="{SHELL}" stroke="{INK}" stroke-width="1.3"/>
  <path d="M138 36 Q143 30 151 30" stroke="#ffffff" stroke-width="1.8" fill="none"/>
  <path d="{tip}" fill="{DARK}" stroke="{INK}" stroke-width="0.9"/>
  <g transform="translate(0 {2 * CY}) scale(1 -1)">
    <path d="{prong}" fill="{SHELL_SHADE}" stroke="{INK}" stroke-width="1.3"/>
    <path d="{tip}" fill="{DARK}" stroke="{INK}" stroke-width="0.9"/>
  </g>
""")


@lru_cache(maxsize=8)
def _layer(svg: str) -> Image.Image:
    return Image.open(io.BytesIO(_svg_to_png_bytes(svg, 96.0))).convert("RGBA")


def _energy(canvas: Image.Image, phase: float, pulse: float, glow: RGBA, core: RGBA) -> None:
    """The emitter core and its halo, and the energy coiling in the tube."""
    p = hp.px
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = blending_draw(layer)
    cx, cy = CORE
    # Halo: soft rings of the glow colour, swelling with the pulse.
    for k, (r, alpha) in enumerate(((17, 34), (13, 54), (10.5, 80))):
        r = r * (0.9 + 0.18 * pulse)
        d.ellipse((p(cx - r), p(cy - r), p(cx + r), p(cy + r)), fill=glow[:3] + (alpha,))
    r = CORE_R * (0.92 + 0.12 * pulse)
    d.ellipse((p(cx - r), p(cy - r), p(cx + r), p(cy + r)), fill=core)
    r2 = r * (0.55 + 0.1 * pulse)
    d.ellipse((p(cx - r2), p(cy - r2), p(cx + r2), p(cy + r2)), fill=glow)
    d.ellipse((p(cx - 2.4), p(cy - 3.6), p(cx + 1.0), p(cy - 0.8)), fill=(255, 255, 255, 240))
    # The tube's energy: two strands coiling along it, drifting with the phase.
    for strand, (color, amp, width) in enumerate(((core, 2.6, 1.8), (glow, 1.6, 1.0))):
        pts = []
        steps = 40
        for i in range(steps + 1):
            u = i / steps
            x = TUBE_X0 + 3 + (TUBE_X1 - TUBE_X0 - 6) * u
            y = TUBE_Y + amp * math.sin(math.tau * (u * 3.0 - phase) + strand * math.pi)
            pts.append((p(x), p(y)))
        d.line(pts, fill=color, width=max(1, int(p(width))), joint="curve")
    canvas.alpha_composite(layer)


def _glass(canvas: Image.Image) -> None:
    """The tube's front glass: a highlight over the energy."""
    p = hp.px
    d = blending_draw(canvas)
    d.line([(p(TUBE_X0 + 4), p(TUBE_Y - 3)), (p(TUBE_X1 - 6), p(TUBE_Y - 3))], fill=(255, 255, 255, 170),
           width=max(1, int(p(1.2))))
    for x in (TUBE_X0, TUBE_X1):
        d.rounded_rectangle((p(x - 2.5), p(TUBE_Y - 6.5), p(x + 2.5), p(TUBE_Y + 6.5)), radius=p(1.5),
                            fill=(74, 81, 91, 255), outline=(21, 23, 27, 255), width=max(1, int(p(0.9))))


def _frame_meta(anim: str, frame_idx: int, nframes: int) -> dict:
    del anim, frame_idx, nframes
    return hp.anchor_meta({"grip": (GRIP_X, CY + 18), "muzzle": (MUZZLE_X, CY)})


def build(
    out_dir: str | Path,
    target_name: str,
    glow: RGBA,
    core: RGBA,
    accent: RGBA,
    actor_id: str,
    display: str,
) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    back = _layer(_back_svg(accent))
    front = _layer(_front_svg())

    def _draw_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
        if anim != "idle":
            raise ValueError(f"unknown animation: {anim}")
        phase = frame_idx / max(1, nframes)
        pulse = 0.5 - 0.5 * math.cos(math.tau * phase)
        canvas = hp.new_super(FRAME_SIZE)
        canvas.alpha_composite(back)
        _energy(canvas, phase, pulse, glow, core)
        _glass(canvas)
        canvas.alpha_composite(front)
        return hp.finalize(canvas, FRAME_SIZE)

    actor_metadata = {
        "actor": {"character_id": actor_id, "display_name": display},
        "body": {
            "body_plan": "Prop",
            "body_kind": "Device",
            "mass_class": "Light",
            "locomotion_hint": "Held",
            "traits": ["prop", "weapon", "device", "portal_gun", "sci_fi", "emitter"],
        },
        "brain": {"default_preset": "stand_still"},
        "actions": {"default_preset": "peaceful"},
        "animation_bindings": {"default": {"animation": "idle", "events": []}},
        "sockets": {
            "grip": {
                "source": f"{target_name}.geometry",
                "point": {"x": GRIP_X, "y": CY + 18},
            },
            "muzzle": {
                "source": f"{target_name}.geometry",
                "point": {"x": MUZZLE_X, "y": CY},
            },
        },
        "tags": ["prop", "weapon", "device", "portal_gun"],
    }

    outputs = build_sheet(
        target=target_name,
        rows=ROWS,
        render_fn=_draw_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        frame_meta_fn=_frame_meta,
        auto_crop=True,
        crop_margin=3,
        actor_metadata=actor_metadata,
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
