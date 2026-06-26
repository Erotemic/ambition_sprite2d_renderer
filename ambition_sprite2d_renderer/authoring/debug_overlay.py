"""Visual bone-debug overlay for rig documents.

Renders the solved skeleton on top of the (dimmed) sprite art so you can see
exactly what the FK/IK is doing: each bone as a segment from its origin to its
tip, a dot at every joint, the parent→child offset links, the IK foot *targets*
(where the solver is told to plant each ankle), and the ground line. Use it to
diagnose poses that read wrong — a flipped knee, a foot at the wrong angle, an
IK target on the wrong side.

    from ambition_sprite2d_renderer.authoring.debug_overlay import render_overlay
    render_overlay(doc, "crouch", 0.0, scale=3).save("/tmp/dbg.png")
"""

from __future__ import annotations

from typing import Dict, Tuple

from PIL import Image, ImageDraw

from .rigdoc import RigDocument

Color = Tuple[int, int, int, int]

NEAR = (90, 220, 255, 255)   # cyan  — near-side limbs (front)
FAR = (255, 120, 235, 255)   # magenta — far-side limbs (back)
SPINE = (255, 210, 90, 255)  # yellow — pelvis/torso/head
TARGET = (255, 70, 70, 255)  # red — IK ankle targets / ground


def _bone_color(name: str) -> Color:
    if name.startswith("near"):
        return NEAR
    if name.startswith("far"):
        return FAR
    return SPINE


def _dot(d: ImageDraw.ImageDraw, p: Tuple[float, float], color: Color, r: float) -> None:
    d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=color)


def _cross(d: ImageDraw.ImageDraw, p: Tuple[float, float], color: Color, r: float = 5) -> None:
    d.line([p[0] - r, p[1], p[0] + r, p[1]], fill=color, width=2)
    d.line([p[0], p[1] - r, p[0], p[1] + r], fill=color, width=2)


def render_overlay(
    doc: RigDocument,
    clip_name: str,
    t: float,
    scale: int = 3,
    art: bool = True,
) -> Image.Image:
    """Return an RGBA image of the pose with the skeleton drawn over it."""
    fr = doc.frame
    S = int(scale)
    w, h = int(fr["width"]) * S, int(fr["height"]) * S
    if art:
        base = doc.render_at(clip_name, t, supersample=2, scale=S).convert("RGBA")
        base = Image.blend(Image.new("RGBA", base.size, (38, 38, 46, 255)), base, 0.5)
    else:
        base = Image.new("RGBA", (w, h), (38, 38, 46, 255))
    d = ImageDraw.Draw(base)

    world, params = doc.solve(clip_name, t)
    sk = doc.build_skeleton()

    cx = float(fr.get("center_x", fr["width"] / 2))
    gy = float(fr.get("ground_y", fr["height"] - 2))
    ah = float(fr.get("ankle_h", 0.0))
    d.line([0, gy * S, w, gy * S], fill=(255, 80, 80, 120), width=1)

    # parent -> child offset links (thin grey), so detached/odd offsets show up
    for name, b in sk.bones.items():
        if b.parent and b.parent in world and name in world:
            po, co = world[b.parent].origin, world[name].origin
            d.line([po[0] * S, po[1] * S, co[0] * S, co[1] * S],
                   fill=(150, 150, 150, 150), width=1)

    # bone segments + joints + labels
    for name, bw in world.items():
        col = _bone_color(name)
        o = (bw.origin[0] * S, bw.origin[1] * S)
        if bw.length > 0.1:
            tip = (bw.tip[0] * S, bw.tip[1] * S)
            d.line([o, tip], fill=col, width=3)
            _dot(d, tip, col, 2.5)
        _dot(d, o, col, 4)
        d.text((o[0] + 4, o[1] - 5), name, fill=col)

    # IK ankle targets (red cross) — where the solver is told to put each foot
    for leg in doc.ik_legs:
        pre = leg.get("channel_prefix", "foot")
        x = params.get(f"{pre}_x", float(leg.get("rest_x", 0.0)))
        lift = params.get(f"{pre}_lift", float(leg.get("rest_lift", 0.0)))
        _cross(d, ((cx + x) * S, (gy - ah - lift) * S), TARGET)

    return base


def render_clip_strip(doc: RigDocument, clip_name: str, scale: int = 2) -> Image.Image:
    """A horizontal strip of every frame of a clip with the skeleton overlaid."""
    n = int(doc.clips.get(clip_name, {}).get("frames", 1))
    frames = [render_overlay(doc, clip_name, doc.frame_time(clip_name, i, n), scale)
              for i in range(n)]
    w, h = frames[0].size
    strip = Image.new("RGBA", (w * n, h), (38, 38, 46, 255))
    for i, f in enumerate(frames):
        strip.alpha_composite(f, (i * w, 0))
    return strip
