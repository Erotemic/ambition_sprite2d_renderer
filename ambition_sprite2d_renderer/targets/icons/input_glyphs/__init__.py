"""Input prompts: gamepad button glyphs, keycaps, mouse glyphs and device art.

All of it is drawn here, by code. There is no brand mark on any of it: a pad
is "a pad in that family's shape", and only the universal prompt symbols
(A/B/X/Y, the four PlayStation-like shapes, the mirrored Switch-like letters)
are printed on the buttons.

The look is the ``hud_icons`` look: a light body with a dark rim, so one glyph
reads on a bright stage and on a dark one. The one colour of "this one" (a lit
D-pad arm, stick direction, mouse button) is amber.

File names: (style, control) -> file
-------------------------------------
Every name is made by rule from the game's own vocabulary, so the Rust side
needs no hand-made table.

Gamepad glyphs, 128 x 128::

    input_glyph_{style}_{control}.png

``style`` is the ``GamepadStyle`` variant (``crates/ambition_input``):

    XboxLike -> xbox, PlayStation -> playstation, Switch -> switch,
    Generic -> generic

``control`` is the snake_case (the ``heck`` crate's rule, so ``DPadUp`` is
``d_pad_up``) of the Bevy ``GamepadButton`` variant, so the
PHYSICAL control, never the printed label (a Switch-like pad prints "B" on
``south``)::

    South -> south, East -> east, West -> west, North -> north,
    LeftTrigger -> left_trigger      (the bumper: LB / L1 / L)
    RightTrigger -> right_trigger    (RB / R1 / R)
    LeftTrigger2 -> left_trigger2    (the trigger: LT / L2 / ZL)
    RightTrigger2 -> right_trigger2  (RT / R2 / ZR)
    Select -> select, Start -> start, Mode -> mode,
    LeftThumb -> left_thumb, RightThumb -> right_thumb   (stick clicks, L3/R3)
    DPadUp -> d_pad_up, DPadDown -> d_pad_down,
    DPadLeft -> d_pad_left, DPadRight -> d_pad_right

⚠ Bevy calls the bumper ``LeftTrigger`` and the trigger ``LeftTrigger2``; the
file names keep Bevy's words so the rule stays mechanical.

Controls that are not one ``GamepadButton`` use the same pattern::

    d_pad                                the whole D-pad, no arm lit
    left_stick, right_stick              stick, "move it"
    left_stick_{up,down,left,right}      stick with one direction lit
    right_stick_{up,down,left,right}

The ``generic`` style prints neutral position dots on the face buttons (the
position is the only fact true of an unknown pad) and draws everything else
as ``xbox`` does.

Keyboard glyphs, 128 high, wider for long keys::

    input_glyph_key_{name}.png

``name`` is ``key_label(key).to_lowercase()`` from
``crates/ambition_input/src/glyphs.rs``: ``a``..``z``, ``digit0``..``digit9``,
``up``/``down``/``left``/``right``, ``space``, ``enter``, ``esc``, ``shift``,
``ctrl``, ``alt``, ``tab``, ``backspace``, and the other keys of the compact
board (``minus``, ``equal``, ``bracketleft``, ``bracketright``,
``backslash``, ``semicolon``, ``quote``, ``comma``, ``period``, ``slash``,
``capslock``, ``delete``, ``pageup``, ``pagedown``, ``end``). Left and right
Shift, Ctrl and Alt share one glyph, as ``key_label`` folds them.

Mouse glyphs, 128 x 128::

    input_glyph_mouse_{left,right,middle,wheel,wheel_up,wheel_down,move}.png

``left``/``right``/``middle`` are the snake_case Bevy ``MouseButton``.

Device illustrations and layouts
--------------------------------
::

    input_device_{xbox,playstation,switch,generic,keyboard,mouse}.png
    input_device_{...}_layout.ron

A layout RON names each control on its device::

    (
        image: "input_device_xbox.png",
        size: (800, 540),
        controls: {
            "South": (glyph: Some("input_glyph_xbox_south.png"), shape: Circle,
                      center: (x, y), radius: r, rect: (x: _, y: _, w: _, h: _)),
            ...
        },
    )

The map keys are Bevy names: ``GamepadButton`` variants plus ``DPad``,
``LeftStick`` and ``RightStick`` on a pad; ``KeyCode`` variants on the
keyboard (``ShiftRight`` has its own spot and the ``shift`` glyph); and
``MouseButton`` variants plus ``Wheel`` and ``Move`` on the mouse. ``glyph``
is ``None`` for a key that has no prompt word (``SuperLeft``, ``Fn``).

Units are pixels of the full-size image, ``size``. ⚠ The quality tiers
(half, quarter, potato) resize the PNG and do not copy the RON, so a consumer
divides by ``size`` and multiplies by the size it shows the image at. ``rect``
bounds the visible part; ``center``/``radius`` give a circle that stays on
the part (the part's own circle when ``shape`` is ``Circle``, else the circle
inscribed in ``rect``). A stick and its click (``LeftStick``/``LeftThumb``)
share a spot, as do the mouse ``Middle`` and ``Wheel``.

Why many PNG files and not one sheet
------------------------------------
The publisher builds the quality tiers of a loose PNG by resizing it whole,
which is right for a standalone glyph. A ``*_spritesheet`` is the animation
atlas contract (frames, clips, anchors) and would make every prompt a lookup
into an atlas; one file per (style, control) keeps the name rule above the
whole contract. The files install under ``sprites/input_glyphs/``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image

from . import _devices as devices
from . import _gamepad as gamepad
from . import _keys as keys
from ._paint import Box, render_box

TARGET_NAME = "input_glyphs"
INSTALL_SUBDIR = "input_glyphs"

#: A glyph's height (and a square glyph's width), in pixels of the full tier.
#: The HUD shows a prompt at about 24 to 48 px; the half tier is 64 px.
GLYPH_PX = 128

STYLES = gamepad.STYLES
GAMEPAD_CONTROLS = gamepad.gamepad_controls()
MOUSE_CONTROLS = keys.MOUSE_CONTROLS
DEVICES = (*STYLES, "keyboard", "mouse")


def gamepad_file(style: str, control: str) -> str:
    return f"input_glyph_{style}_{control}.png"


def key_file(key: keys.Key) -> str:
    return f"input_glyph_key_{key.name}.png"


def mouse_file(control: str) -> str:
    return f"input_glyph_mouse_{control}.png"


def device_files(device: str) -> Tuple[str, str]:
    return f"input_device_{device}.png", f"input_device_{device}_layout.ron"


SHEET_FILES: Tuple[str, ...] = (
    *[gamepad_file(style, control) for style in STYLES for control in GAMEPAD_CONTROLS],
    *[key_file(key) for key in keys.KEYS],
    *[mouse_file(control) for control in MOUSE_CONTROLS],
    *[name for device in DEVICES for name in device_files(device)],
)

#: A review picture of every product; not installed (not in SHEET_FILES).
CONTACT_SHEET = "input_glyphs_contact_sheet.png"


def render_gamepad_glyph(style: str, control: str, size: int = GLYPH_PX) -> Image.Image:
    def paint(canvas: Image.Image, box: Box) -> None:
        gamepad.paint_gamepad_control(canvas, box, style, control)

    return render_box(paint, (size, size))


def render_key_glyph(key: keys.Key, unit: int = GLYPH_PX) -> Image.Image:
    def paint(canvas: Image.Image, box: Box) -> None:
        keys.paint_keycap(canvas, box, key.printed)

    return render_box(paint, keys.key_glyph_size(key, unit))


def render_mouse_glyph(control: str, size: int = GLYPH_PX) -> Image.Image:
    def paint(canvas: Image.Image, box: Box) -> None:
        keys.paint_mouse(canvas, box, control)

    return render_box(paint, (size, size))


def render_devices() -> List[devices.Device]:
    out = [devices.render_pad(style, gamepad_file) for style in STYLES]
    out.append(devices.render_keyboard(key_file))
    out.append(devices.render_mouse(mouse_file))
    return out


def render_all(size: int = GLYPH_PX) -> Tuple[Dict[str, Image.Image], Dict[str, str]]:
    """Every product in memory: ``(images by file name, layout RON by file name)``."""
    images: Dict[str, Image.Image] = {}
    for style in STYLES:
        for control in GAMEPAD_CONTROLS:
            images[gamepad_file(style, control)] = render_gamepad_glyph(style, control, size)
    for key in keys.KEYS:
        images[key_file(key)] = render_key_glyph(key, size)
    for control in MOUSE_CONTROLS:
        images[mouse_file(control)] = render_mouse_glyph(control, size)
    layouts: Dict[str, str] = {}
    for device in render_devices():
        png, ron = f"{device.name}.png", f"{device.name}_layout.ron"
        images[png] = device.image
        layouts[ron] = devices.layout_ron(device)
    return images, layouts


def contact_sheet(images: Dict[str, Image.Image], *, cell: int = 64) -> Image.Image:
    """Every glyph at ``cell`` and ``cell / 2`` px on a light and a dark band,
    then the devices. For review only."""
    from ambition_sprite2d_renderer.core.draw import resize_transparent_sprite

    glyphs = [(name, img) for name, img in images.items() if name.startswith("input_glyph_")]
    device_imgs = [img for name, img in images.items() if name.startswith("input_device_")]
    small = cell // 2
    pad = 6
    width = 1600
    rows: List[Tuple[int, Image.Image, Tuple[int, int, int]]] = []
    for size in (cell, small):
        for bg in ((236, 238, 242), (34, 38, 48)):
            x, y = pad, pad
            line_h = size + pad
            placed = []
            for _, img in glyphs:
                w = max(1, round(img.width * size / img.height))
                if x + w + pad > width:
                    x, y = pad, y + line_h
                placed.append((x, y, w, img))
                x += w + pad
            band = Image.new("RGBA", (width, y + line_h + pad), bg + (255,))
            for x, y, w, img in placed:
                band.alpha_composite(resize_transparent_sprite(img, (w, size)), (x, y))
            rows.append((band.height, band, bg))
    for bg in ((236, 238, 242), (34, 38, 48)):
        x, y, line_h = pad, pad, 0
        placed = []
        for img in device_imgs:
            w, h = img.width // 2, img.height // 2
            if x + w + pad > width:
                x, y, line_h = pad, y + line_h + pad, 0
            placed.append((x, y, w, h, img))
            x += w + pad
            line_h = max(line_h, h)
        band = Image.new("RGBA", (width, y + line_h + 2 * pad), bg + (255,))
        for x, y, w, h, img in placed:
            band.alpha_composite(resize_transparent_sprite(img, (w, h)), (x, y))
        rows.append((band.height, band, bg))
    sheet = Image.new("RGBA", (width, sum(h for h, _, _ in rows)), (0, 0, 0, 255))
    y = 0
    for h, band, _ in rows:
        sheet.alpha_composite(band, (0, y))
        y += h
    return sheet


def write_input_glyphs(out_dir: str | Path, *, size: int = GLYPH_PX, review: bool = True) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    images, layouts = render_all(size)
    written: List[Path] = []
    for name, img in images.items():
        path = out_dir / name
        img.save(path)
        written.append(path)
    for name, text in layouts.items():
        path = out_dir / name
        path.write_text(text)
        written.append(path)
    if review:
        contact_sheet(images).save(out_dir / CONTACT_SHEET)
    return written


def render(out_dir: str | Path, **opts) -> List[Path]:
    """Render every input glyph, device illustration and layout into ``out_dir``."""
    return write_input_glyphs(out_dir, size=int(opts.get("size", GLYPH_PX)))
