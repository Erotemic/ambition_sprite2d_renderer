"""Device illustrations and their control layouts.

A device is drawn from the same painters as the glyphs, each control in a box.
Those boxes ARE the layout: :func:`render_device` returns the picture and, for
each control, the rectangle and circle a UI uses to put a callout line on it or
light it up.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from PIL import Image

from ambition_sprite2d_renderer.core.draw import blending_draw

from . import _gamepad as pad
from . import _keys as keys
from ._paint import (
    INK,
    LIP,
    Box,
    Color,
    Shape,
    box_center,
    box_size,
    ellipse_shape,
    finish,
    new_canvas,
    plate,
    rrect_shape,
    square_in,
)

#: Devices are larger than glyphs already, so a smaller supersample suffices.
DEVICE_SUPERSAMPLE = 2

PAD_SIZE = (800, 540)
KEYBOARD_UNIT = 60
KEYBOARD_MARGIN = 22
MOUSE_SIZE = (360, 400)

BODY_TOP: Color = (228, 232, 240, 255)
BODY_BOTTOM: Color = (182, 189, 204, 255)
PLATE: Color = (112, 120, 138, 255)


@dataclass(frozen=True)
class Spot:
    """One control on a device, in the device image's pixels (full tier).

    ``rect`` bounds the visible part. ``center`` and ``radius`` give a circle
    that stays on the part: for a round part its own circle, for any other
    part the circle inscribed in ``rect``.
    """

    control: str
    glyph: Optional[str]
    round: bool
    rect: Box

    @property
    def center(self) -> Tuple[float, float]:
        return box_center(self.rect)

    @property
    def radius(self) -> float:
        return min(box_size(self.rect)) / 2.0


@dataclass
class Device:
    name: str
    image: Image.Image
    spots: List[Spot]


# ---- shared body drawing ------------------------------------------------------


def _paint_body(canvas: Image.Image, shapes: Sequence[Shape], rim: float) -> None:
    """A union of shapes, rimmed once round the whole outline and filled with
    a soft top-to-bottom shade."""
    d = blending_draw(canvas)
    for shape in shapes:
        d.polygon(shape(rim), fill=INK)
    mask = Image.new("L", canvas.size, 0)
    md = blending_draw(mask)
    for shape in shapes:
        md.polygon(shape(0), fill=255)
    top, bottom = mask.getbbox()[1], mask.getbbox()[3]
    column = Image.new("RGBA", (1, canvas.height))
    for y in range(canvas.height):
        t = min(1.0, max(0.0, (y - top) / max(1, bottom - top)))
        column.putpixel((0, y), tuple(int(round(a + (b - a) * t)) for a, b in zip(BODY_TOP, BODY_BOTTOM)))
    canvas.paste(column.resize(canvas.size), (0, 0), mask)


def _scaled(box: Box, s: float) -> Box:
    return (box[0] * s, box[1] * s, box[2] * s, box[3] * s)


def _unscaled(box: Box, s: float) -> Box:
    return (box[0] / s, box[1] / s, box[2] / s, box[3] / s)


def _centered(cx: float, cy: float, w: float, h: float) -> Box:
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


# ---- gamepads -------------------------------------------------------------------


@dataclass(frozen=True)
class PadPlan:
    """Where a pad family puts things, as fractions of the image (x of the
    width, y of the height; sizes as fractions of the width)."""

    body: Callable[[float, float], List[Shape]]
    face: Tuple[float, float]
    face_spacing: float
    face_size: float
    left_stick: Tuple[float, float]
    right_stick: Tuple[float, float]
    stick_size: float
    dpad: Tuple[float, float]
    dpad_size: float
    select: Tuple[float, float]
    start: Tuple[float, float]
    system_size: float
    mode: Tuple[float, float]
    mode_size: float
    bumper_y: float
    bumper_x: float
    decorations: Callable[[Image.Image, float, float], None] = lambda canvas, w, h: None


def _xbox_body(w: float, h: float) -> List[Shape]:
    return [
        rrect_shape((0.2 * w, 0.22 * h, 0.8 * w, 0.62 * h), 0.12 * h),
        ellipse_shape(0.3 * w, 0.4 * h, 0.18 * w, 0.22 * h),
        ellipse_shape(0.7 * w, 0.4 * h, 0.18 * w, 0.22 * h),
        ellipse_shape(0.215 * w, 0.64 * h, 0.1 * w, 0.27 * h, 24),
        ellipse_shape(0.785 * w, 0.64 * h, 0.1 * w, 0.27 * h, -24),
    ]


def _playstation_body(w: float, h: float) -> List[Shape]:
    return [
        rrect_shape((0.17 * w, 0.21 * h, 0.83 * w, 0.56 * h), 0.08 * h),
        ellipse_shape(0.26 * w, 0.4 * h, 0.15 * w, 0.2 * h),
        ellipse_shape(0.74 * w, 0.4 * h, 0.15 * w, 0.2 * h),
        ellipse_shape(0.5 * w, 0.55 * h, 0.22 * w, 0.17 * h),
        ellipse_shape(0.19 * w, 0.67 * h, 0.085 * w, 0.27 * h, 16),
        ellipse_shape(0.81 * w, 0.67 * h, 0.085 * w, 0.27 * h, -16),
    ]


def _switch_body(w: float, h: float) -> List[Shape]:
    return [
        rrect_shape((0.24 * w, 0.24 * h, 0.76 * w, 0.6 * h), 0.16 * h),
        ellipse_shape(0.32 * w, 0.42 * h, 0.2 * w, 0.22 * h),
        ellipse_shape(0.68 * w, 0.42 * h, 0.2 * w, 0.22 * h),
        ellipse_shape(0.235 * w, 0.64 * h, 0.12 * w, 0.24 * h, 32),
        ellipse_shape(0.765 * w, 0.64 * h, 0.12 * w, 0.24 * h, -32),
    ]


def _playstation_decor(canvas: Image.Image, w: float, h: float) -> None:
    # The touch panel: a large flat plate between the clusters.
    rim = 0.006 * w
    plate(canvas, rrect_shape((0.37 * w, 0.23 * h, 0.63 * w, 0.44 * h), 0.03 * w), rim, body=(212, 217, 228, 255), lip=LIP, bevel=0.008 * w)


def _switch_decor(canvas: Image.Image, w: float, h: float) -> None:
    # The capture button: a small square with a dot, not a listed control.
    side = 0.034 * w
    cx, cy = 0.445 * w, 0.44 * h
    rim = 0.005 * w
    plate(canvas, rrect_shape(_centered(cx, cy, side, side), side * 0.2), rim, bevel=side * 0.08)
    r = side * 0.22
    blending_draw(canvas).ellipse((cx - r, cy - r - side * 0.04, cx + r, cy + r - side * 0.04), fill=LIP)


PAD_PLANS: Dict[str, PadPlan] = {
    "xbox": PadPlan(
        body=_xbox_body, face=(0.72, 0.38), face_spacing=0.056, face_size=0.064,
        left_stick=(0.285, 0.38), right_stick=(0.615, 0.6), stick_size=0.118,
        dpad=(0.385, 0.6), dpad_size=0.112, select=(0.435, 0.38), start=(0.565, 0.38),
        system_size=0.048, mode=(0.5, 0.27), mode_size=0.056, bumper_y=0.205, bumper_x=0.27,
    ),
    "playstation": PadPlan(
        body=_playstation_body, face=(0.745, 0.38), face_spacing=0.056, face_size=0.062,
        left_stick=(0.385, 0.62), right_stick=(0.615, 0.62), stick_size=0.112,
        dpad=(0.255, 0.38), dpad_size=0.122, select=(0.335, 0.265), start=(0.665, 0.265),
        system_size=0.058, mode=(0.5, 0.56), mode_size=0.046, bumper_y=0.195, bumper_x=0.255,
        decorations=_playstation_decor,
    ),
    "switch": PadPlan(
        body=_switch_body, face=(0.705, 0.385), face_spacing=0.054, face_size=0.06,
        left_stick=(0.3, 0.385), right_stick=(0.605, 0.6), stick_size=0.114,
        dpad=(0.395, 0.6), dpad_size=0.108, select=(0.415, 0.3), start=(0.585, 0.3),
        system_size=0.044, mode=(0.555, 0.44), mode_size=0.04, bumper_y=0.225, bumper_x=0.29,
        decorations=_switch_decor,
    ),
}
#: An unclassified pad is drawn with the Xbox-like body and neutral glyphs.
PAD_PLANS["generic"] = PAD_PLANS["xbox"]

#: Bevy `GamepadButton` names (and the two stick names) on a pad, with the
#: glyph control each one shows.
PAD_CONTROLS = {
    "South": "south", "East": "east", "West": "west", "North": "north",
    "LeftTrigger": "left_trigger", "RightTrigger": "right_trigger",
    "LeftTrigger2": "left_trigger2", "RightTrigger2": "right_trigger2",
    "Select": "select", "Start": "start", "Mode": "mode",
    "LeftThumb": "left_thumb", "RightThumb": "right_thumb",
    "DPadUp": "d_pad_up", "DPadDown": "d_pad_down", "DPadLeft": "d_pad_left", "DPadRight": "d_pad_right",
    "DPad": "d_pad", "LeftStick": "left_stick", "RightStick": "right_stick",
}


def render_pad(style: str, glyph_file: Callable[[str, str], str]) -> Device:
    plan = PAD_PLANS[style]
    s = DEVICE_SUPERSAMPLE
    canvas = new_canvas(PAD_SIZE, s)
    cw, ch = float(canvas.width), float(canvas.height)
    rects: Dict[str, Tuple[Box, bool]] = {}

    def at(fx: float, fy: float, size_w: float, size_h: Optional[float] = None) -> Box:
        """A canvas box centred at a fraction of the image; sizes are
        fractions of the width."""
        return _centered(fx * cw, fy * ch, size_w * cw, (size_h if size_h is not None else size_w) * cw)

    # Triggers sit behind the body's top edge, so they are drawn first.
    for side, sign in (("left", -1), ("right", 1)):
        bx = 0.5 + sign * (0.5 - plan.bumper_x)
        tbox = at(bx + sign * -0.015, plan.bumper_y - 0.1, 0.13, 0.15)
        control = f"{side}_trigger2"
        pad.paint_trigger(canvas, tbox, style, control)
        rects[control] = (pad.trigger_rect(tbox), False)
    body_rim = 0.009 * cw
    _paint_body(canvas, plan.body(cw, ch), body_rim)
    plan.decorations(canvas, cw, ch)
    for side, sign in (("left", -1), ("right", 1)):
        bx = 0.5 + sign * (0.5 - plan.bumper_x)
        bbox = at(bx, plan.bumper_y, 0.2, 0.09)
        control = f"{side}_trigger"
        pad.paint_bumper(canvas, bbox, style, control)
        rects[control] = (pad.bumper_rect(bbox), False)
        # The trigger shows above the bumper only; the layout names that part.
        trig, _ = rects[f"{side}_trigger2"]
        rects[f"{side}_trigger2"] = ((trig[0], trig[1], trig[2], pad.bumper_rect(bbox)[1]), False)

    sp = plan.face_spacing * cw
    fcx, fcy = plan.face[0] * cw, plan.face[1] * ch
    for control, (dx, dy) in {"south": (0, 1), "east": (1, 0), "west": (-1, 0), "north": (0, -1)}.items():
        box = _centered(fcx + dx * sp, fcy + dy * sp, plan.face_size * cw, plan.face_size * cw)
        pad.paint_face_button(canvas, box, style, control)
        rects[control] = (square_in(box, 0.9), True)

    for control, (fx, fy) in (("left_stick", plan.left_stick), ("right_stick", plan.right_stick)):
        box = at(fx, fy, plan.stick_size)
        pad.paint_stick(canvas, box, "L" if control.startswith("left") else "R", arrows=False)
        well = square_in(box, 0.96)
        rects[control] = (well, True)
        rects[control.replace("stick", "thumb")] = (well, True)

    dbox = at(plan.dpad[0], plan.dpad[1], plan.dpad_size)
    pad.paint_dpad(canvas, dbox, style, None)
    dsq = square_in(dbox, 0.94)
    rects["d_pad"] = (dsq, False)
    third = (dsq[2] - dsq[0]) / 3.0
    for name, (col, row) in {"up": (1, 0), "down": (1, 2), "left": (0, 1), "right": (2, 1)}.items():
        x0, y0 = dsq[0] + col * third, dsq[1] + row * third
        rects[f"d_pad_{name}"] = ((x0, y0, x0 + third, y0 + third), False)

    for control, (fx, fy), size in (
        ("select", plan.select, plan.system_size),
        ("start", plan.start, plan.system_size),
        ("mode", plan.mode, plan.mode_size),
    ):
        box = at(fx, fy, size)
        pad.paint_system_button(canvas, box, style, control)
        part = square_in(box, 0.9)
        if style == "playstation" and control != "mode":
            w = (part[2] - part[0]) * 0.5
            cx = (part[0] + part[2]) / 2
            part = (cx - w / 2, part[1], cx + w / 2, part[3])
        rects[control] = (part, control in ("mode",) or style != "playstation")

    image = finish(canvas, PAD_SIZE)
    spots = []
    for bevy, control in PAD_CONTROLS.items():
        rect, round_ = rects[control]
        spots.append(Spot(bevy, glyph_file(style, control), round_, _unscaled(rect, s)))
    return Device(f"input_device_{style}", image, spots)


# ---- keyboard -------------------------------------------------------------------

#: A compact 16-unit board: (Bevy `KeyCode`, width in units) per row. Two
#: keys have no glyph: they carry no prompt word in the game.
KEYBOARD_ROWS: Tuple[Tuple[Tuple[str, float], ...], ...] = (
    (("Escape", 1),) + tuple((f"Digit{n}", 1) for n in (1, 2, 3, 4, 5, 6, 7, 8, 9, 0))
    + (("Minus", 1), ("Equal", 1), ("Backspace", 2), ("Delete", 1)),
    (("Tab", 1.5),) + tuple((f"Key{c}", 1) for c in "QWERTYUIOP")
    + (("BracketLeft", 1), ("BracketRight", 1), ("Backslash", 1.5), ("PageUp", 1)),
    (("CapsLock", 1.75),) + tuple((f"Key{c}", 1) for c in "ASDFGHJKL")
    + (("Semicolon", 1), ("Quote", 1), ("Enter", 2.25), ("PageDown", 1)),
    (("ShiftLeft", 2.25),) + tuple((f"Key{c}", 1) for c in "ZXCVBNM")
    + (("Comma", 1), ("Period", 1), ("Slash", 1), ("ShiftRight", 1.75), ("ArrowUp", 1), ("End", 1)),
    (("ControlLeft", 1.25), ("SuperLeft", 1.25), ("AltLeft", 1.25), ("Space", 6.25), ("AltRight", 1),
     ("Fn", 1), ("ControlRight", 1), ("ArrowLeft", 1), ("ArrowDown", 1), ("ArrowRight", 1)),
)
#: Right-hand twins share the left key's glyph, as `key_label` folds them.
KEY_TWINS = {"ShiftRight": "ShiftLeft", "ControlRight": "ControlLeft", "AltRight": "AltLeft"}


def keyboard_size() -> Tuple[int, int]:
    units = max(sum(w for _, w in row) for row in KEYBOARD_ROWS)
    return (int(units * KEYBOARD_UNIT + 2 * KEYBOARD_MARGIN), int(len(KEYBOARD_ROWS) * KEYBOARD_UNIT + 2 * KEYBOARD_MARGIN))


def render_keyboard(key_file: Callable[[keys.Key], str]) -> Device:
    s = DEVICE_SUPERSAMPLE
    size = keyboard_size()
    canvas = new_canvas(size, s)
    u = KEYBOARD_UNIT * s
    m = KEYBOARD_MARGIN * s
    rim = 0.006 * canvas.width
    frame = (rim, rim, canvas.width - rim, canvas.height - rim)
    plate(canvas, rrect_shape(frame, m * 0.8), rim, body=PLATE, lip=(84, 91, 108, 255), bevel=m * 0.35)
    spots = []
    for r, row in enumerate(KEYBOARD_ROWS):
        x = float(m)
        y = m + r * u - m * 0.12
        for code, width in row:
            box = (x, y, x + width * u, y + u)
            key = keys.KEYS_BY_CODE.get(KEY_TWINS.get(code, code))
            if key is None:
                keys.paint_keycap(canvas, box, "", blank=True)
            else:
                keys.paint_keycap(canvas, box, key.printed)
            spots.append(Spot(code, key_file(key) if key else None, False, _unscaled(_keycap_rect(box), s)))
            x += width * u
    return Device("input_device_keyboard", finish(canvas, size), spots)


def _keycap_rect(box: Box) -> Box:
    """The visible cap inside a keycap paint box (see ``paint_keycap``)."""
    h = box[3] - box[1]
    inset = max(1.5, 0.055 * h) + h * 0.02
    return (box[0] + inset, box[1] + inset, box[2] - inset, box[3] - inset)


# ---- mouse ----------------------------------------------------------------------

MOUSE_LAYOUT = {"Left": "left", "Right": "right", "Middle": "middle", "Wheel": "wheel", "Move": "move"}


def render_mouse(mouse_file: Callable[[str], str]) -> Device:
    s = DEVICE_SUPERSAMPLE
    canvas = new_canvas(MOUSE_SIZE, s)
    box = (0.0, 0.0, float(canvas.width), float(canvas.height))
    g = keys.paint_mouse(canvas, box, None, rim_scale=0.6)
    parts = {
        "left": g.left_button,
        "right": g.right_button,
        "middle": g.wheel,
        "wheel": g.wheel,
        "move": g.body,
    }
    # The buttons' outer corners are round: keep their rectangles on the body
    # by pulling the top edge down to where the curve has filled out.
    bw = g.body[2] - g.body[0]
    for name in ("left", "right"):
        x0, y0, x1, y1 = parts[name]
        parts[name] = (x0 + bw * 0.08 if name == "left" else x0, y0 + bw * 0.22, x1 - bw * 0.08 if name == "right" else x1, y1)
    spots = [
        Spot(bevy, mouse_file(part), part in ("middle", "wheel"), _unscaled(parts[part], s))
        for bevy, part in MOUSE_LAYOUT.items()
    ]
    return Device("input_device_mouse", finish(canvas, MOUSE_SIZE), spots)


# ---- layout file ------------------------------------------------------------------


def layout_ron(device: Device) -> str:
    """The device layout as RON. See the package docstring for the schema."""
    w, h = device.image.size
    lines = [
        f"// {device.name}: control positions in `image` pixels at its full size.",
        "// Generated by the sprite renderer target `input_glyphs`; do not edit.",
        "(",
        f'    image: "{device.name}.png",',
        f"    size: ({w}, {h}),",
        "    controls: {",
    ]
    for spot in device.spots:
        x0, y0, x1, y1 = spot.rect
        cx, cy = spot.center
        glyph = f'Some("{spot.glyph}")' if spot.glyph else "None"
        shape = "Circle" if spot.round else "Rect"
        lines.append(
            f'        "{spot.control}": (glyph: {glyph}, shape: {shape}, '
            f"center: ({cx:.1f}, {cy:.1f}), radius: {spot.radius:.1f}, "
            f"rect: (x: {x0:.1f}, y: {y0:.1f}, w: {x1 - x0:.1f}, h: {y1 - y0:.1f})),"
        )
    lines += ["    },", ")", ""]
    return "\n".join(lines)

