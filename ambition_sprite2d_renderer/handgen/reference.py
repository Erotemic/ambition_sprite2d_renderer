"""Reference sheets: the bare 3D model as a turnaround (each digit its own
colour, so a piece can be followed across every cell), and the drawn hand
over poses x rolls in a style."""

from __future__ import annotations

from typing import Dict, Sequence, Tuple

import numpy as np
from PIL import Image, ImageDraw

from .draw import STYLES, HandStyle, draw_hand
from .model import Camera, HandPose, HandSpec, digits, palm_outline, thumb_web
from .poses import POSES

DIGIT_COLOURS = {"index": (232, 92, 92), "middle": (92, 200, 110), "ring": (90, 130, 236), "little": (232, 200, 70), "thumb": (236, 140, 60)}
ROLLS = (0, 45, 90, 135, 180)
BACKGROUND = (40, 34, 60, 255)


def render_model(spec: HandSpec, pose: HandPose, cam: Camera, size: Tuple[int, int], ss: int = 4) -> Image.Image:
    """The bare model: the palm a plate (lighter on its palm side), each
    phalanx a capsule in its digit's colour (darker where its back faces
    us), joints dark pivots, a white dot where a pad faces us; painter's
    order by depth."""
    img = Image.new("RGBA", (size[0] * ss, size[1] * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    S = lambda p: (p[0] * ss, p[1] * ss)  # noqa: E731
    palm_col = (236, 226, 214) if cam.palm_faces_us() else (170, 160, 150)
    outline = palm_outline(spec)
    depth = float(np.mean([cam.depth(p) for p in outline]))
    parts = [(depth, "plate", outline, palm_col), (depth - 0.01, "plate", thumb_web(spec, pose), palm_col)]
    for name, dg in digits(spec, pose).items():
        for i in range(len(dg.joints) - 1):
            a, b = dg.joints[i], dg.joints[i + 1]
            facing = cam.depth(dg.pads[i])
            parts.append(((cam.depth(a) + cam.depth(b)) / 2, "bone", (a, b, dg.widths[i] * cam.scale, facing), DIGIT_COLOURS[name]))
    ink = (30, 24, 40, 255)
    for _depth, kind, data, colour in sorted(parts, key=lambda p: p[0]):
        if kind == "plate":
            d.polygon([S(cam.project(p)) for p in data], fill=colour + (255,), outline=ink, width=ss)
            continue
        a, b, w, facing = data
        pa, pb = S(cam.project(a)), S(cam.project(b))
        k = 0.55 + 0.45 * max(0.0, facing)
        for col, ww in ((ink, w + 1.2 * cam.scale), (tuple(int(c * k) for c in colour) + (255,), w)):
            r = ww * ss / 2
            d.line([pa, pb], fill=col, width=int(ww * ss))
            for p in (pa, pb):
                d.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=col)
        r = 0.9 * ss * cam.scale
        d.ellipse((pa[0] - r, pa[1] - r, pa[0] + r, pa[1] + r), fill=ink)
        if facing > 0.2:
            m = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
            d.ellipse((m[0] - r, m[1] - r, m[0] + r, m[1] + r), fill=(255, 255, 255, 255))
    return img.resize(size, Image.Resampling.LANCZOS)


def _grid(cells, rows: Sequence[str], cols: Sequence[str], cell: Tuple[int, int]) -> Image.Image:
    label_w, label_h = 70, 18
    sheet = Image.new("RGBA", (label_w + cell[0] * len(cols), label_h + (cell[1] + 4) * len(rows)), BACKGROUND)
    d = ImageDraw.Draw(sheet)
    for c, name in enumerate(cols):
        d.text((label_w + c * cell[0] + 6, 4), name, fill=(230, 230, 240, 255))
    for r, name in enumerate(rows):
        y = label_h + r * (cell[1] + 4)
        d.text((6, y + cell[1] // 2), name, fill=(230, 230, 240, 255))
        for c in range(len(cols)):
            sheet.alpha_composite(cells(r, c), (label_w + c * cell[0], y))
    return sheet


def _roll_label(roll: float) -> str:
    return f"roll {roll:g}" + (" (palm)" if roll == 0 else " (back)" if roll == 180 else "")


def _camera(cell: Tuple[int, int], roll: float, spec: HandSpec) -> Camera:
    scale = cell[1] / 85.0
    return Camera((cell[0] * (0.3 if spec.handedness == "right" else 0.3), cell[1] * 0.72), -40.0, float(roll), scale)


def model_sheet(spec: HandSpec = HandSpec(), poses: Dict[str, HandPose] = None, rolls: Sequence[float] = ROLLS, cell: Tuple[int, int] = (240, 220)) -> Image.Image:
    """The bare model, poses (rows) x rolls (columns)."""
    poses = poses or {k: POSES[k] for k in ("open", "grasp", "fist")}
    names = list(poses)
    return _grid(lambda r, c: render_model(spec, poses[names[r]], _camera(cell, rolls[c], spec), cell), names, [_roll_label(r) for r in rolls], cell)


def drawn_sheet(spec: HandSpec = HandSpec(), style: HandStyle = STYLES["skin"], poses: Dict[str, HandPose] = None, rolls: Sequence[float] = (0, 180), cell: Tuple[int, int] = (240, 220)) -> Image.Image:
    """The drawn hand, poses (rows) x rolls (columns)."""
    poses = poses or POSES
    names = list(poses)
    return _grid(lambda r, c: draw_hand(spec, poses[names[r]], _camera(cell, rolls[c], spec), cell, style).frame(), names, [_roll_label(r) for r in rolls], cell)
