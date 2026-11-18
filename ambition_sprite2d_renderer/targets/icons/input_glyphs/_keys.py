"""Keyboard keycap and mouse painters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from PIL import Image

from ambition_sprite2d_renderer.core.draw import blending_draw

from ._paint import (
    ACCENT,
    ACCENT_LIP,
    BODY,
    DIRECTIONS,
    INK,
    LABEL,
    WELL,
    LIP,
    Box,
    arrow_points,
    box_center,
    box_size,
    fit_font_px,
    label,
    layer_masked,
    outlined_polygon,
    plate,
    polygon_shape,
    rect_mask,
    rim_width,
    rrect_shape,
)


@dataclass(frozen=True)
class Key:
    """One key: its glyph name, the Bevy ``KeyCode`` it stands for, what is
    printed on it, and its width in key units (1 u is a letter key)."""

    name: str
    keycode: str
    printed: str
    width_u: float = 1.0


def _letters() -> Tuple[Key, ...]:
    return tuple(Key(c.lower(), f"Key{c}", c) for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ")


def _digits() -> Tuple[Key, ...]:
    return tuple(Key(f"digit{n}", f"Digit{n}", str(n)) for n in range(10))


#: ``name`` is ``key_label(keycode).to_lowercase()`` from
#: ``crates/ambition_input/src/glyphs.rs``: the game's own prompt word.
KEYS: Tuple[Key, ...] = (
    *_letters(),
    *_digits(),
    Key("up", "ArrowUp", "@up"),
    Key("down", "ArrowDown", "@down"),
    Key("left", "ArrowLeft", "@left"),
    Key("right", "ArrowRight", "@right"),
    Key("space", "Space", "Space", 3.5),
    Key("enter", "Enter", "Enter", 2.25),
    Key("esc", "Escape", "Esc", 1.25),
    Key("shift", "ShiftLeft", "Shift", 2.25),
    Key("ctrl", "ControlLeft", "Ctrl", 1.5),
    Key("alt", "AltLeft", "Alt", 1.25),
    Key("tab", "Tab", "Tab", 1.5),
    Key("backspace", "Backspace", "@backspace", 2.0),
    # The rest of a compact board, so the keyboard illustration has no
    # unnamed key.
    Key("minus", "Minus", "-"),
    Key("equal", "Equal", "="),
    Key("bracketleft", "BracketLeft", "["),
    Key("bracketright", "BracketRight", "]"),
    Key("backslash", "Backslash", "\\"),
    Key("semicolon", "Semicolon", ";"),
    Key("quote", "Quote", "'"),
    Key("comma", "Comma", ","),
    Key("period", "Period", "."),
    Key("slash", "Slash", "/"),
    Key("capslock", "CapsLock", "Caps", 1.75),
    Key("delete", "Delete", "Del"),
    Key("pageup", "PageUp", "PgUp"),
    Key("pagedown", "PageDown", "PgDn"),
    Key("end", "End", "End"),
)
KEYS_BY_CODE = {key.keycode: key for key in KEYS}


def key_glyph_size(key: Key, unit: int) -> Tuple[int, int]:
    return int(round(unit * key.width_u)), unit


def paint_keycap(canvas: Image.Image, box: Box, printed: str, *, highlight: bool = False, blank: bool = False) -> None:
    """A keycap filling ``box``. ``printed`` is text, or ``@name`` for a
    drawn symbol (arrows, backspace)."""
    w, h = box_size(box)
    rim = rim_width((0, 0, h, h))
    inset = rim + h * 0.02
    rect = (box[0] + inset, box[1] + inset, box[2] - inset, box[3] - inset)
    bevel = h * 0.11
    body, lip = (ACCENT, ACCENT_LIP) if highlight else (BODY, LIP)
    plate(canvas, rrect_shape(rect, h * 0.14), rim, body=body, lip=lip, bevel=bevel)
    if blank:
        return
    face = (rect[0] + bevel * 0.6, rect[1] + bevel * 0.1, rect[2] - bevel * 0.6, rect[3] - bevel * 1.2)
    fw, fh = box_size(face)
    fc = box_center(face)
    if printed.startswith("@"):
        _paint_key_symbol(canvas, face, printed[1:])
        return
    single = len(printed) == 1
    start = fh * (0.62 if single else 0.4)
    px = fit_font_px(printed, fw * 0.82, fh * 0.7, start)
    label(canvas, printed, fc, px)


def _paint_key_symbol(canvas: Image.Image, face: Box, name: str) -> None:
    fw, fh = box_size(face)
    cx, cy = box_center(face)
    d = blending_draw(canvas)
    if name in DIRECTIONS:
        d.polygon(arrow_points((cx, cy), fh * 0.5, name), fill=LABEL)
        return
    if name == "backspace":
        # A left-pointing tag with a cross in it.
        h = fh * 0.3
        w = h * 2.6
        x0 = cx - w / 2
        tag = [(x0, cy), (x0 + h, cy - h), (x0 + w, cy - h), (x0 + w, cy + h), (x0 + h, cy + h)]
        d.polygon(tag, fill=LABEL)
        k = h * 0.45
        mx = x0 + h + (w - h) / 2
        t = max(1, int(round(h * 0.28)))
        d.line([(mx - k, cy - k), (mx + k, cy + k)], fill=BODY, width=t)
        d.line([(mx - k, cy + k), (mx + k, cy - k)], fill=BODY, width=t)
        return
    raise ValueError(name)  # pragma: no cover - a table typo


# ---- mouse ------------------------------------------------------------------

MOUSE_CONTROLS = ("left", "right", "middle", "wheel", "wheel_up", "wheel_down", "move")


@dataclass(frozen=True)
class MouseGeometry:
    """Where the mouse parts are, in canvas pixels."""

    body: Box
    split_y: float
    wheel: Box
    rim: float

    @property
    def left_button(self) -> Box:
        return (self.body[0], self.body[1], (self.body[0] + self.body[2]) / 2, self.split_y)

    @property
    def right_button(self) -> Box:
        return ((self.body[0] + self.body[2]) / 2, self.body[1], self.body[2], self.split_y)


def mouse_geometry(box: Box, scale: float = 1.0, rim_scale: float = 1.0) -> MouseGeometry:
    w, h = box_size(box)
    cx, cy = box_center(box)
    side = min(w, h) * scale
    bw, bh = side * 0.56, side * 0.88
    rim = rim_width((0, 0, side, side)) * rim_scale
    body = (cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2)
    split_y = body[1] + bh * 0.44
    ww, wh = bw * 0.26, bh * 0.24
    wheel = (cx - ww / 2, body[1] + bh * 0.1, cx + ww / 2, body[1] + bh * 0.1 + wh)
    return MouseGeometry(body, split_y, wheel, rim)


def paint_mouse(canvas: Image.Image, box: Box, highlight: Optional[str] = None, *, rim_scale: float = 1.0) -> MouseGeometry:
    """A mouse from above; ``highlight`` is one of :data:`MOUSE_CONTROLS`.

    ``rim_scale`` thins the rim of a mouse drawn large (the device picture),
    where a glyph's rim would look heavy."""
    scale = 0.62 if highlight == "move" else 1.0
    if highlight in ("wheel", "wheel_up", "wheel_down"):
        # Room on the right for the roll arrows.
        w = box[2] - box[0]
        box_m = (box[0] - w * 0.08, box[1], box[2] - w * 0.08, box[3])
        g = mouse_geometry(box_m, scale, rim_scale)
    else:
        g = mouse_geometry(box, scale, rim_scale)
    bw, bh = box_size(g.body)
    radii = (bw * 0.5, bw * 0.5, bw * 0.42, bw * 0.42)
    shape = rrect_shape(g.body, radii, n=20)
    plate(canvas, shape, g.rim, bevel=bh * 0.04)
    if highlight in ("left", "right", "middle"):
        # The button you press is a lit zone of the top: a half for left and
        # right, the strip round the wheel for middle.
        if highlight == "middle":
            mid = (g.body[0] + g.body[2]) / 2
            region = (mid - bw * 0.24, g.body[1], mid + bw * 0.24, g.split_y)
        else:
            region = g.left_button if highlight == "left" else g.right_button

        def paint(layer: Image.Image) -> None:
            blending_draw(layer).polygon(shape(-g.rim * 0.2), fill=ACCENT)

        layer_masked(canvas, paint, rect_mask(canvas.size, region))
    d = blending_draw(canvas)
    t = max(1, int(round(g.rim * 0.8)))
    cx = (g.body[0] + g.body[2]) / 2
    d.line([(g.body[0], g.split_y), (g.body[2], g.split_y)], fill=INK, width=t)
    d.line([(cx, g.body[1]), (cx, g.wheel[1])], fill=INK, width=t)
    d.line([(cx, g.wheel[3]), (cx, g.split_y)], fill=INK, width=t)
    lit_wheel = highlight in ("wheel", "wheel_up", "wheel_down")
    ww, wh = box_size(g.wheel)
    wheel_shape = rrect_shape(g.wheel, ww * 0.5)
    # Unlit, the wheel is dark: a light wheel in a dark rim reads as a "0".
    plate(canvas, wheel_shape, g.rim * 0.8, body=ACCENT if lit_wheel else WELL, lip=ACCENT_LIP if lit_wheel else INK, bevel=wh * 0.1)
    side_x = g.body[2] + (box[2] - g.body[2]) / 2
    arrow = (box[2] - g.body[2]) * 0.7
    wy = (g.wheel[1] + g.wheel[3]) / 2
    if highlight in ("wheel", "wheel_up"):
        outlined_polygon(canvas, polygon_shape(arrow_points((side_x, wy - arrow * 0.6), arrow, "up")), g.rim * 0.8, ACCENT)
    if highlight in ("wheel", "wheel_down"):
        outlined_polygon(canvas, polygon_shape(arrow_points((side_x, wy + arrow * 0.6), arrow, "down")), g.rim * 0.8, ACCENT)
    if highlight == "move":
        bx, by = box_center(box)
        reach = min(box_size(box)) * 0.42
        size = min(box_size(box)) * 0.16
        for name, (vx, vy) in (("up", (0, -1)), ("down", (0, 1)), ("left", (-1, 0)), ("right", (1, 0))):
            c = (bx + vx * reach, by + vy * reach)
            outlined_polygon(canvas, polygon_shape(arrow_points(c, size, name)), g.rim * 0.8, ACCENT)
    return g
