"""Gamepad control painters, one per control kind, styled per pad family.

The style decides only what is PRINTED on a control (letters, shapes, names)
and small shape habits (the separate D-pad arms of a PlayStation-like pad). The
control is always the physical one: ``south`` is the bottom face button on
every pad, so the Switch-like ``south`` glyph shows a "B".
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

from PIL import Image

from ambition_sprite2d_renderer.core.draw import blending_draw

from ._paint import (
    ACCENT,
    ACCENT_LIP,
    BODY,
    DIRECTION_VECTORS,
    DIRECTIONS,
    INK,
    LABEL,
    LIP,
    MARK,
    PRESSED,
    WELL,
    Box,
    Color,
    arrow_points,
    box_center,
    box_size,
    circle_shape,
    fit_font_px,
    label,
    outlined_polygon,
    plate,
    polygon_shape,
    rim_width,
    rotate,
    rrect_shape,
    square_in,
    stroke_line,
)

STYLES: Tuple[str, ...] = ("xbox", "playstation", "switch", "generic")

FACE = ("south", "east", "west", "north")

#: Conventional face colours, darkened enough to read on a light cap.
XBOX_FACE: Dict[str, Tuple[str, Color]] = {
    "south": ("A", (40, 160, 60, 255)),
    "east": ("B", (214, 46, 46, 255)),
    "west": ("X", (34, 104, 222, 255)),
    "north": ("Y", (240, 186, 20, 255)),
}
#: Switch-like pads print X/Y/A/B at mirrored positions: B is south.
SWITCH_FACE: Dict[str, str] = {"south": "B", "east": "A", "west": "Y", "north": "X"}
PLAYSTATION_FACE: Dict[str, Tuple[str, Color]] = {
    "south": ("cross", (70, 128, 236, 255)),
    "east": ("circle", (230, 60, 72, 255)),
    "west": ("square", (218, 100, 186, 255)),
    "north": ("triangle", (36, 176, 132, 255)),
}

SHOULDER_LABELS: Dict[str, Dict[str, str]] = {
    "xbox": {"left_trigger": "LB", "right_trigger": "RB", "left_trigger2": "LT", "right_trigger2": "RT"},
    "playstation": {"left_trigger": "L1", "right_trigger": "R1", "left_trigger2": "L2", "right_trigger2": "R2"},
    "switch": {"left_trigger": "L", "right_trigger": "R", "left_trigger2": "ZL", "right_trigger2": "ZR"},
    "generic": {"left_trigger": "LB", "right_trigger": "RB", "left_trigger2": "LT", "right_trigger2": "RT"},
}


# ---- face buttons ---------------------------------------------------------


def paint_face_button(canvas: Image.Image, box: Box, style: str, position: str) -> None:
    sq = square_in(box, 0.9)
    side = sq[2] - sq[0]
    cx, cy = box_center(sq)
    rim = rim_width(sq)
    r = side / 2.0 - rim
    plate(canvas, circle_shape(cx, cy, r), rim, bevel=side * 0.07)
    face_cy = cy - side * 0.035
    if style == "xbox":
        letter, color = XBOX_FACE[position]
        label(canvas, letter, (cx, face_cy), side * 0.56, fill=color, stroke=side * 0.035)
    elif style == "switch":
        label(canvas, SWITCH_FACE[position], (cx, face_cy), side * 0.56, fill=LABEL)
    elif style == "playstation":
        symbol, color = PLAYSTATION_FACE[position]
        _paint_ps_symbol(canvas, (cx, face_cy), side * 0.46, symbol, color, side * 0.03)
    else:
        _paint_position_dots(canvas, (cx, face_cy), side * 0.5, position)


def _paint_ps_symbol(canvas: Image.Image, center, size: float, symbol: str, color: Color, rim: float) -> None:
    cx, cy = center
    width = size * 0.16
    h = size / 2.0
    d = blending_draw(canvas)
    if symbol == "cross":
        k = h * 0.82
        stroke_line(canvas, (cx - k, cy - k), (cx + k, cy + k), width, color, rim)
        # The second bar's rim would cut the first bar; draw both colours
        # after both rims.
        stroke_line(canvas, (cx - k, cy + k), (cx + k, cy - k), width, color, rim)
        d.line([(cx - k, cy - k), (cx + k, cy + k)], fill=color, width=int(round(width)))
    elif symbol == "circle":
        r = h * 0.86
        d.ellipse((cx - r - rim, cy - r - rim, cx + r + rim, cy + r + rim), outline=INK, width=int(round(width + 2 * rim)))
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=color, width=int(round(width)))
    elif symbol == "square":
        k = h * 0.74
        d.rectangle((cx - k - rim, cy - k - rim, cx + k + rim, cy + k + rim), outline=INK, width=int(round(width + 2 * rim)))
        d.rectangle((cx - k, cy - k, cx + k, cy + k), outline=color, width=int(round(width)))
    elif symbol == "triangle":
        k = h * 0.95
        # An equilateral triangle, centred on its own centroid.
        pts = [(cx, cy - k), (cx + k * 0.866, cy + k * 0.5), (cx - k * 0.866, cy + k * 0.5)]
        loop = pts + [pts[0], pts[1]]
        d.line(loop, fill=INK, width=int(round(width + 2 * rim)), joint="curve")
        d.line(loop, fill=color, width=int(round(width)), joint="curve")
    else:  # pragma: no cover - a table typo
        raise ValueError(symbol)


def _paint_position_dots(canvas: Image.Image, center, size: float, position: str) -> None:
    """Four dots in a diamond; the pressed position is a large dark dot.

    For a pad whose labels are unknown, the position is the only fact the
    prompt can state truthfully.
    """
    cx, cy = center
    d = blending_draw(canvas)
    offset = size * 0.36
    where = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}
    for name, (dx, dy) in where.items():
        px, py = cx + dx * offset, cy + dy * offset
        if name == position:
            r = size * 0.2
            d.ellipse((px - r, py - r, px + r, py + r), fill=INK)
        else:
            r = size * 0.1
            d.ellipse((px - r, py - r, px + r, py + r), outline=INK, width=max(1, int(round(size * 0.055))))


# ---- shoulders --------------------------------------------------------------


def bumper_rect(box: Box) -> Box:
    """The bumper's own outline (rim excluded) inside its paint box."""
    w, h = box_size(box)
    rim = rim_width(box)
    bw, bh = w * 0.9 - 2 * rim, h * 0.5
    cx, cy = box_center(box)
    return (cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2)


def trigger_rect(box: Box) -> Box:
    """The trigger's own outline (rim excluded) inside its paint box."""
    w, h = box_size(box)
    rim = rim_width(box)
    tw, th = w * 0.66, h * 0.9 - 2 * rim
    cx, cy = box_center(box)
    return (cx - tw / 2, cy - th / 2, cx + tw / 2, cy + th / 2)


def paint_bumper(canvas: Image.Image, box: Box, style: str, control: str, *, highlight: bool = False) -> None:
    rim = rim_width(box)
    left = control.startswith("left")
    rect = bumper_rect(box)
    bw, bh = box_size(rect)
    cx, cy = box_center(rect)
    big, small = bh * 0.55, bh * 0.18
    radii = (big, small, small, small) if left else (small, big, small, small)
    body, lip = (ACCENT, ACCENT_LIP) if highlight else (BODY, LIP)
    plate(canvas, rrect_shape(rect, radii), rim, body=body, lip=lip, bevel=bh * 0.14)
    text = SHOULDER_LABELS[style][control]
    px = fit_font_px(text, bw * 0.8, bh * 0.62, bh * 0.62)
    label(canvas, text, (cx, cy - bh * 0.05), px)


def paint_trigger(canvas: Image.Image, box: Box, style: str, control: str, *, highlight: bool = False) -> None:
    rim = rim_width(box)
    left = control.startswith("left")
    rect = trigger_rect(box)
    tw, th = box_size(rect)
    cx, cy = box_center(rect)
    big, mid, small = tw * 0.5, tw * 0.3, tw * 0.14
    radii = (big, mid, small, small) if left else (mid, big, small, small)
    body, lip = (ACCENT, ACCENT_LIP) if highlight else (BODY, LIP)
    plate(canvas, rrect_shape(rect, radii), rim, body=body, lip=lip, bevel=tw * 0.1)
    # Grip ridges near the bottom: the trigger's "pull here" mark.
    d = blending_draw(canvas)
    for i in range(2):
        y = rect[3] - th * (0.14 + 0.08 * i)
        d.line([(rect[0] + tw * 0.22, y), (rect[2] - tw * 0.22, y)], fill=LIP, width=max(1, int(th * 0.025)))
    text = SHOULDER_LABELS[style][control]
    px = fit_font_px(text, tw * 0.78, th * 0.3, tw * 0.5)
    label(canvas, text, (cx, cy - th * 0.1), px)


# ---- system buttons ---------------------------------------------------------


def paint_system_button(canvas: Image.Image, box: Box, style: str, control: str) -> None:
    """``select``, ``start`` or ``mode``."""
    sq = square_in(box, 0.9)
    side = sq[2] - sq[0]
    cx, cy = box_center(sq)
    rim = rim_width(sq)
    if style == "playstation" and control in ("select", "start"):
        # A tall pill, as on that family of pads.
        pw, ph = side * 0.5, side - 2 * rim
        shape = rrect_shape((cx - pw / 2, cy - ph / 2, cx + pw / 2, cy + ph / 2), pw / 2)
    else:
        shape = circle_shape(cx, cy, side / 2 - rim)
    plate(canvas, shape, rim, bevel=side * 0.07)
    icon_c = (cx, cy - side * 0.035)
    if control == "mode":
        _paint_house(canvas, icon_c, side * 0.5)
    elif style == "switch":
        _paint_plus_minus(canvas, icon_c, side * 0.5, plus=(control == "start"))
    elif style == "playstation":
        if control == "select":
            _paint_share(canvas, icon_c, side * 0.42)
        else:
            _paint_menu_lines(canvas, icon_c, side * 0.36)
    else:
        if control == "select":
            _paint_view(canvas, icon_c, side * 0.5)
        else:
            _paint_menu_lines(canvas, icon_c, side * 0.46)


def _paint_house(canvas: Image.Image, center, size: float) -> None:
    cx, cy = center
    h = size / 2
    d = blending_draw(canvas)
    roof = [(cx, cy - h), (cx + h, cy - h * 0.05), (cx - h, cy - h * 0.05)]
    d.polygon(roof, fill=LABEL)
    d.rectangle((cx - h * 0.68, cy - h * 0.1, cx + h * 0.68, cy + h * 0.9), fill=LABEL)
    d.rectangle((cx - h * 0.2, cy + h * 0.3, cx + h * 0.2, cy + h * 0.9), fill=BODY)


def _paint_plus_minus(canvas: Image.Image, center, size: float, *, plus: bool) -> None:
    cx, cy = center
    h, t = size / 2, size * 0.11
    d = blending_draw(canvas)
    d.rectangle((cx - h, cy - t, cx + h, cy + t), fill=LABEL)
    if plus:
        d.rectangle((cx - t, cy - h, cx + t, cy + h), fill=LABEL)


def _paint_menu_lines(canvas: Image.Image, center, size: float) -> None:
    cx, cy = center
    h, t = size / 2, size * 0.09
    d = blending_draw(canvas)
    for k in (-1, 0, 1):
        y = cy + k * size * 0.34
        d.rectangle((cx - h, y - t, cx + h, y + t), fill=LABEL)


def _paint_view(canvas: Image.Image, center, size: float) -> None:
    """Two overlapping windows: the "view" mark."""
    cx, cy = center
    d = blending_draw(canvas)
    w, h, t = size * 0.62, size * 0.48, max(1, int(round(size * 0.1)))
    back = (cx - w / 2 + size * 0.16, cy - h / 2 - size * 0.12)
    d.rectangle((back[0], back[1], back[0] + w, back[1] + h), outline=LABEL, width=t)
    front = (cx - w / 2 - size * 0.12, cy - h / 2 + size * 0.14)
    d.rectangle((front[0], front[1], front[0] + w, front[1] + h), fill=LABEL)


def _paint_share(canvas: Image.Image, center, size: float) -> None:
    """An arrow up out of a tray: the generic "share" mark."""
    cx, cy = center
    h = size / 2
    t = max(1, int(round(size * 0.12)))
    d = blending_draw(canvas)
    d.line([(cx - h, cy), (cx - h, cy + h), (cx + h, cy + h), (cx + h, cy)], fill=LABEL, width=t, joint="curve")
    d.line([(cx, cy + h * 0.4), (cx, cy - h * 0.55)], fill=LABEL, width=t)
    d.polygon([(cx, cy - h * 1.05), (cx + h * 0.5, cy - h * 0.4), (cx - h * 0.5, cy - h * 0.4)], fill=LABEL)


# ---- D-pad ------------------------------------------------------------------


def paint_dpad(canvas: Image.Image, box: Box, style: str, highlight: Optional[str]) -> None:
    """The whole D-pad; ``highlight`` names the arm that is "this one"."""
    sq = square_in(box, 0.94)
    side = sq[2] - sq[0]
    cx, cy = box_center(sq)
    rim = rim_width(sq)
    reach = side / 2 - rim
    arm = side * 0.34
    if style == "playstation":
        # Four separate arrow keys, each pointing at the centre.
        gap = side * 0.06
        for direction in DIRECTIONS:
            pts = [
                (cx - arm / 2, cy - reach),
                (cx + arm / 2, cy - reach),
                (cx + arm / 2, cy - arm / 2 - gap),
                (cx, cy - gap * 1.2),
                (cx - arm / 2, cy - arm / 2 - gap),
            ]
            angle = {"up": 0, "right": 90, "down": 180, "left": 270}[direction]
            shape = polygon_shape(rotate(pts, (cx, cy), angle))
            lit = direction == highlight
            plate(canvas, shape, rim, body=ACCENT if lit else BODY, lip=ACCENT_LIP if lit else LIP, bevel=side * 0.035)
            _dpad_mark(canvas, cx, cy, reach, arm, direction, lit, rim)
        return
    a = arm / 2
    r = reach
    d = blending_draw(canvas)
    corner = arm * 0.18
    outer = rrect_shape((cx - a, cy - r, cx + a, cy + r), corner)
    across = rrect_shape((cx - r, cy - a, cx + r, cy + a), corner)
    d.polygon(outer(rim), fill=INK)
    d.polygon(across(rim), fill=INK)
    bevel = side * 0.035
    d.polygon(outer(0), fill=LIP)
    d.polygon(across(0), fill=LIP)
    top_v = [(x, y - bevel * 0.55) for x, y in rrect_shape((cx - a, cy - r, cx + a, cy + r), corner)(-bevel * 0.55)]
    top_h = [(x, y - bevel * 0.55) for x, y in rrect_shape((cx - r, cy - a, cx + r, cy + a), corner)(-bevel * 0.55)]
    d.polygon(top_v, fill=BODY)
    d.polygon(top_h, fill=BODY)
    if highlight is not None:
        vx, vy = DIRECTION_VECTORS[highlight]
        # The lit arm: from just past the hub to the arm's end.
        near, far = a * 0.7, r - bevel * 1.1
        inset = bevel * 0.9
        if vx == 0:
            y0, y1 = sorted((cy + vy * near, cy + vy * far))
            lit = (cx - a + inset, y0, cx + a - inset, y1)
        else:
            x0, x1 = sorted((cx + vx * near, cx + vx * far))
            lit = (x0, cy - a + inset, x1, cy + a - inset)
        lit = (lit[0], lit[1] - bevel * 0.55, lit[2], lit[3] - bevel * 0.55)
        d.rounded_rectangle(lit, radius=corner * 0.6, fill=ACCENT)
    # A shallow dish in the hub.
    hub = a * 0.5
    d.ellipse((cx - hub, cy - hub - bevel * 0.55, cx + hub, cy + hub - bevel * 0.55), fill=PRESSED)
    for direction in DIRECTIONS:
        _dpad_mark(canvas, cx, cy - bevel * 0.55, reach, arm, direction, direction == highlight, rim)


def _dpad_mark(canvas: Image.Image, cx: float, cy: float, reach: float, arm: float, direction: str, lit: bool, rim: float) -> None:
    vx, vy = DIRECTION_VECTORS[direction]
    dist = reach * 0.66
    center = (cx + vx * dist, cy + vy * dist)
    size = arm * (0.62 if lit else 0.48)
    d = blending_draw(canvas)
    d.polygon(arrow_points(center, size, direction), fill=INK if lit else LABEL)


# ---- sticks -----------------------------------------------------------------


def paint_stick(
    canvas: Image.Image,
    box: Box,
    side_label: str,
    *,
    direction: Optional[str] = None,
    pressed: bool = False,
    arrows: bool = True,
) -> None:
    """A thumbstick from above: a dark well and a light cap.

    ``direction`` draws the stick smaller, moved away from that side, with a
    large lit arrow in the space it left, and leans the cap toward the arrow.
    (An arrow inside the well hides under the leaning cap.) ``pressed`` draws
    the click (L3/R3): a lit ring round the well and a sunk cap.
    """
    sq = square_in(box, 0.96)
    side = sq[2] - sq[0]
    cx, cy = box_center(sq)
    if direction is not None:
        vx, vy = DIRECTION_VECTORS[direction]
        rim = rim_width(sq)
        arrow_c = (cx + vx * side * 0.35, cy + vy * side * 0.35)
        outlined_polygon(canvas, polygon_shape(arrow_points(arrow_c, side * 0.27, direction)), rim, ACCENT)
        k = side * 0.36
        sx, sy = cx - vx * side * 0.13, cy - vy * side * 0.13
        _paint_stick_body(canvas, (sx - k, sy - k, sx + k, sy + k), side_label, lean=direction, arrows=arrows)
        return
    _paint_stick_body(canvas, sq, side_label, pressed=pressed, arrows=arrows)


def _paint_stick_body(
    canvas: Image.Image,
    sq: Box,
    side_label: str,
    *,
    lean: Optional[str] = None,
    pressed: bool = False,
    arrows: bool = True,
) -> None:
    side = sq[2] - sq[0]
    cx, cy = box_center(sq)
    rim = rim_width(sq)
    d = blending_draw(canvas)
    well_r = side * (0.40 if pressed else 0.5) - rim
    if pressed:
        ring_r = side * 0.5 - rim
        d.ellipse((cx - ring_r - rim, cy - ring_r - rim, cx + ring_r + rim, cy + ring_r + rim), fill=INK)
        d.ellipse((cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r), fill=ACCENT)
    d.ellipse((cx - well_r - rim, cy - well_r - rim, cx + well_r + rim, cy + well_r + rim), fill=INK)
    d.ellipse((cx - well_r, cy - well_r, cx + well_r, cy + well_r), fill=WELL)
    if arrows and not pressed and lean is None:
        for name in DIRECTIONS:
            vx, vy = DIRECTION_VECTORS[name]
            center = (cx + vx * well_r * 0.82, cy + vy * well_r * 0.82)
            d.polygon(arrow_points(center, side * 0.12, name), fill=MARK)
    cap_r = side * (0.25 if pressed else 0.29)
    vx, vy = DIRECTION_VECTORS[lean] if lean else (0.0, 0.0)
    shove = side * 0.08
    ccx, ccy = cx + vx * shove, cy + vy * shove
    body, lip = (PRESSED, LIP) if pressed else (BODY, LIP)
    plate(canvas, circle_shape(ccx, ccy, cap_r), rim, body=body, lip=lip, bevel=side * 0.05)
    face_c = (ccx, ccy - side * 0.0275)
    # The concave ring of the cap top.
    ring = cap_r * 0.78
    d.ellipse((face_c[0] - ring, face_c[1] - ring, face_c[0] + ring, face_c[1] + ring), outline=LIP, width=max(1, int(round(side * 0.018))))
    text = side_label + ("3" if pressed else "")
    px = fit_font_px(text, ring * 1.5, ring * 1.2, side * 0.28)
    label(canvas, text, face_c, px)


# ---- the glyph table --------------------------------------------------------


def gamepad_controls() -> Tuple[str, ...]:
    """Every gamepad glyph control id, in file order."""
    out = list(FACE)
    out += ["left_trigger", "right_trigger", "left_trigger2", "right_trigger2"]
    out += ["select", "start", "mode", "left_thumb", "right_thumb"]
    out += ["d_pad"] + [f"d_pad_{d}" for d in DIRECTIONS]
    for stick in ("left_stick", "right_stick"):
        out += [stick] + [f"{stick}_{d}" for d in DIRECTIONS]
    return tuple(out)


def paint_gamepad_control(canvas: Image.Image, box: Box, style: str, control: str, *, highlight: bool = False) -> None:
    """Paint glyph ``control`` of pad ``style`` into ``box``."""
    if control in FACE:
        paint_face_button(canvas, box, style, control)
    elif control in ("left_trigger", "right_trigger"):
        paint_bumper(canvas, box, style, control, highlight=highlight)
    elif control in ("left_trigger2", "right_trigger2"):
        paint_trigger(canvas, box, style, control, highlight=highlight)
    elif control in ("select", "start", "mode"):
        paint_system_button(canvas, box, style, control)
    elif control == "d_pad":
        paint_dpad(canvas, box, style, None)
    elif control.startswith("d_pad_"):
        paint_dpad(canvas, box, style, control.removeprefix("d_pad_"))
    elif control in ("left_thumb", "right_thumb"):
        paint_stick(canvas, box, "L" if control.startswith("left") else "R", pressed=True)
    elif control.startswith(("left_stick", "right_stick")):
        side, _, direction = control.partition("_stick")
        paint_stick(canvas, box, "L" if side == "left" else "R", direction=direction.lstrip("_") or None)
    else:  # pragma: no cover - a table typo
        raise ValueError(control)


def is_round(control: str) -> bool:
    return control in FACE or control in ("select", "start", "mode") or "stick" in control or "thumb" in control

