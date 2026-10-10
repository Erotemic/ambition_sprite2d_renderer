"""The cart of the intro: a wooden wagon in the lab of the Creator.

The joke is the place: a horse cart of planks and iron, the cart a prisoner
comes to in at the start of an old adventure, in a lab of steel and glass.
The cart is not made to fit the lab.

The game does not draw the cart as a prop on a platform. The cart IS the
platform: its bed is the surface a body stands on. The sheet has four rows,
and each is one picture of the same frame:

    idle    the cart with no near side, no wheels and no back end: the far
            rail, the front board, the bench, the bed and the shafts (tipped
            up, as on a cart that is parked). The game draws it behind each
            body.
    front   the near side: its beam, its posts, its two rails, and the two
            wheels. The game draws it in front of each body, so a body that
            stands on the bed is in the cart, not on it. The wheels are in
            this row so that they are not behind the load of the cart.
    ramp    the back end let down as a ramp from the bed to the floor. The
            game draws it when the ramp is down (a row of steps under it is
            the collision).
    gate    the back end shut: a board. For a cart that rolls (not in the
            game yet): the game draws `ramp` or `gate`, not the two.

The frame is not cropped (`auto_crop=False`), so the game can name the bed in
frame pixels: see `BED_SPAN_PX`, `BED_TOP_PX` and `RAMP_*`. The platform looks
of the game (`game/ambition_content/src/intro/sprites.rs`) have the same
numbers, and a test of the game reads them from the published sheet.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from PIL import Image

from ...authoring.sheet_build import build_sheet
from ...core.draw import blending_draw

RGBA = Tuple[int, int, int, int]

TARGET_NAME = "intro_cart"
SHEET_FILES = [f"{TARGET_NAME}_spritesheet.png", f"{TARGET_NAME}_spritesheet.yaml"]

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 1, 200),
    ("front", 1, 200),
    ("ramp", 1, 200),
    ("gate", 1, 200),
]

#: Frame pixels to one world unit of the game.
PX = 3
#: The frame in world units. The floor the wheels stand on is `FLOOR` units
#: below the top, and the middle of the bed is `MID` units from the left.
UNITS = (320, 104)
FLOOR = 100.0
MID = 124.0
FRAME_SIZE = (UNITS[0] * PX, UNITS[1] * PX)
SUPER = 3
K = PX * SUPER

#: The bed: half its length, and how far its surface is over the floor.
BED_HALF = 88.0
BED_HEIGHT = 58.0
#: The bed in frame pixels: the span of its length, and the row of its surface.
BED_SPAN_PX = ((MID - BED_HALF) * PX, (MID + BED_HALF) * PX)
BED_TOP_PX = (FLOOR - BED_HEIGHT) * PX

#: How far the top of the rail is over the bed. The player is 46 high: the
#: rail is at its middle, so the legs are behind the rail and the body shows.
RAIL_HEIGHT = 19.0
#: The two rails of a side: the lower edge of each, and how thick a rail is.
RAILS = (BED_HEIGHT + 4.6, BED_HEIGHT + 12.4)
RAIL_THICK = 4.8
WHEEL_R = 27.0
WHEELS = (-50.0, 52.0)
#: The ramp: from the back end of the bed down to the floor. The collision of
#: the game is a row of steps: `RAMP_STEPS` of them, each `RAMP_RUN` long and
#: `RAMP_RISE` under the one before. The first is `RAMP_RISE` under the bed.
RAMP_STEPS = 14
RAMP_RUN = 7.0
RAMP_RISE = 4.0
#: The first step in frame pixels: the span of its length, and the row of its
#: surface. The game lays the row `ramp` on the platform that is this step.
RAMP_STEP_SPAN_PX = ((MID + BED_HALF) * PX, (MID + BED_HALF + RAMP_RUN) * PX)
RAMP_STEP_TOP_PX = (FLOOR - (BED_HEIGHT - RAMP_RISE)) * PX

INK = (30, 20, 16, 255)
WOOD = (150, 104, 62, 255)
WOOD_LIGHT = (190, 142, 88, 255)
WOOD_DARK = (104, 68, 42, 255)
WOOD_FAR = (92, 62, 42, 255)
WOOD_FAR_DARK = (66, 44, 32, 255)
IRON = (86, 90, 100, 255)
IRON_LIGHT = (140, 146, 158, 255)
IRON_DARK = (44, 46, 54, 255)
STRAW = (224, 190, 96, 255)
STRAW_DARK = (176, 140, 62, 255)
SACK = (176, 158, 124, 255)
SACK_DARK = (128, 110, 84, 255)
ROPE = (196, 170, 120, 255)


def _mix(a: RGBA, b: RGBA, t: float) -> RGBA:
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))  # type: ignore[return-value]


def _xy(x: float, y: float) -> Tuple[float, float]:
    """A point of the cart in working pixels. `x` is to the right of the
    middle of the bed, `y` is up from the floor."""
    return ((MID + x) * K, (FLOOR - y) * K)


class _Pen:
    def __init__(self) -> None:
        self.image = Image.new("RGBA", (UNITS[0] * K, UNITS[1] * K), (0, 0, 0, 0))
        self.draw = blending_draw(self.image)

    def poly(self, pts, fill: RGBA, ink: float = 0.9) -> None:
        pts = [_xy(x, y) for x, y in pts]
        self.draw.polygon(pts, fill=fill)
        if ink > 0.0:
            self.draw.line(pts + [pts[0]], fill=INK, width=max(1, int(round(ink * K))), joint="curve")

    def box(self, x0: float, y0: float, x1: float, y1: float, fill: RGBA, ink: float = 0.9) -> None:
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill, ink)

    def line(self, pts, fill: RGBA, width: float) -> None:
        self.draw.line([_xy(x, y) for x, y in pts], fill=fill, width=max(1, int(round(width * K))), joint="curve")

    def disc(self, x: float, y: float, r: float, fill: RGBA, ink: float = 0.9) -> None:
        cx, cy = _xy(x, y)
        box = [cx - r * K, cy - r * K, cx + r * K, cy + r * K]
        self.draw.ellipse(box, fill=fill, outline=INK if ink > 0.0 else None, width=max(1, int(round(ink * K))))

    def publish(self) -> Image.Image:
        return self.image.resize(FRAME_SIZE, Image.Resampling.LANCZOS)


def _plank(pen: _Pen, x0: float, y0: float, x1: float, y1: float, wood: RGBA, dark: RGBA, light: RGBA, seed: int) -> None:
    """One plank that lies flat: a body, a light upper edge, a dark lower
    edge, two lines of grain and a nail at each end."""
    pen.box(x0, y0, x1, y1, wood)
    h = y1 - y0
    pen.line([(x0 + 0.9, y1 - 0.9), (x1 - 0.9, y1 - 0.9)], light, 0.7)
    pen.line([(x0 + 0.9, y0 + 0.9), (x1 - 0.9, y0 + 0.9)], dark, 0.7)
    length = x1 - x0
    for k in range(2):
        a = x0 + length * (0.16 + 0.42 * k + 0.07 * ((seed + k) % 3))
        b = min(x1 - 3.0, a + length * (0.16 + 0.05 * ((seed * 3 + k) % 4)))
        y = y0 + h * (0.36 + 0.3 * k)
        pen.line([(a, y), ((a + b) * 0.5, y + 0.5), (b, y)], dark, 0.45)
    for x in (x0 + 2.4, x1 - 2.4):
        pen.disc(x, (y0 + y1) * 0.5, 0.75, IRON_DARK, 0.0)


def _post(pen: _Pen, x: float, y0: float, y1: float, wood: RGBA, dark: RGBA, light: RGBA, width: float = 5.0) -> None:
    """A post that stands, with a round head."""
    pen.box(x - width * 0.5, y0, x + width * 0.5, y1, wood)
    pen.line([(x - width * 0.5 + 0.9, y0 + 1.0), (x - width * 0.5 + 0.9, y1 - 1.0)], light, 0.7)
    pen.line([(x + width * 0.5 - 0.9, y0 + 1.0), (x + width * 0.5 - 0.9, y1 - 1.0)], dark, 0.7)
    pen.box(x - width * 0.5 - 0.8, y1 - 0.4, x + width * 0.5 + 0.8, y1 + 2.0, light)


def _wheel(pen: _Pen, x: float, turn: float) -> None:
    """A wheel of wood with a tyre of iron: twelve spokes and a hub."""
    y, r = WHEEL_R, WHEEL_R
    pen.disc(x, y, r, IRON_DARK)
    pen.disc(x, y, r - 1.9, IRON, 0.0)
    pen.disc(x, y, r - 3.2, WOOD_DARK, 0.6)
    # Between the spokes: the dark of what is behind the wheel.
    pen.disc(x, y, r - 8.4, _mix(WOOD_FAR_DARK, INK, 0.45), 0.6)
    for k in range(12):
        a = turn + k * math.tau / 12.0
        dx, dy = math.cos(a), math.sin(a)
        pen.line([(x + dx * 4.0, y + dy * 4.0), (x + dx * (r - 7.6), y + dy * (r - 7.6))], INK, 3.3)
        pen.line([(x + dx * 4.0, y + dy * 4.0), (x + dx * (r - 7.8), y + dy * (r - 7.8))], WOOD, 1.9)
    # Felloes: the lines where the pieces of the rim meet.
    for k in range(6):
        a = turn + (k + 0.5) * math.tau / 6.0
        dx, dy = math.cos(a), math.sin(a)
        pen.line([(x + dx * (r - 8.2), y + dy * (r - 8.2)), (x + dx * (r - 3.4), y + dy * (r - 3.4))], INK, 0.6)
    pen.disc(x, y, 6.2, WOOD_LIGHT)
    pen.disc(x, y, 3.2, IRON)
    pen.disc(x - 0.8, y + 0.8, 1.0, IRON_LIGHT, 0.0)
    # The light on the tyre, from above and to the left.
    cx, cy = _xy(x, y)
    box = [cx - (r - 0.9) * K, cy - (r - 0.9) * K, cx + (r - 0.9) * K, cy + (r - 0.9) * K]
    pen.draw.arc(box, 200, 290, fill=IRON_LIGHT, width=max(1, int(round(0.9 * K))))


def _far_side(pen: _Pen) -> None:
    """The far rail: the same as the near one, darker, and seen over the bed."""
    top = BED_HEIGHT + RAIL_HEIGHT
    for x in (-84.0, -42.0, 0.0, 42.0, 84.0):
        _post(pen, x + 3.0, BED_HEIGHT, top + 1.0, WOOD_FAR, WOOD_FAR_DARK, _mix(WOOD_FAR, WOOD, 0.5), 4.4)
    for y in RAILS:
        _plank(pen, -86.0, y, 90.0, y + RAIL_THICK, WOOD_FAR, WOOD_FAR_DARK, _mix(WOOD_FAR, WOOD, 0.5), int(y))


def _back(pen: _Pen) -> None:
    under = BED_HEIGHT - 9.0
    # The shafts: two poles at the front of the cart, tipped up, as on a cart
    # that is parked. There is no horse.
    for lift, wood in ((2.6, WOOD_FAR), (0.0, WOOD)):
        shaft = [(-84.0, under + 2.0 + lift), (-100.0, under + 14.0 + lift), (-117.0, 93.0 + lift * 0.4)]
        pen.line(shaft, INK, 4.6)
        pen.line(shaft, wood, 2.8)
    pen.box(-120.6, 88.0, -113.4, 92.4, IRON)
    # A rope left on the shaft.
    rope = [(-103.0, under + 17.0), (-108.0, under + 9.0), (-104.0, under + 3.0), (-99.0, under + 12.0)]
    pen.line(rope, INK, 2.2)
    pen.line(rope, ROPE, 1.1)

    # Under the bed: the beam of each axle, and the long beam between them.
    pen.box(-74.0, under - 7.0, 78.0, under, WOOD_FAR_DARK)
    for x in WHEELS:
        pen.box(x - 7.0, WHEEL_R - 4.5, x + 7.0, under - 6.0, WOOD_DARK)
        pen.box(x - 9.0, WHEEL_R - 4.0, x + 9.0, WHEEL_R + 4.0, IRON_DARK)
        # The far wheel: a dark shape that the near wheel is in front of.
        pen.disc(x + 3.0, WHEEL_R + 1.0, WHEEL_R - 1.0, _mix(WOOD_FAR_DARK, INK, 0.45))

    _far_side(pen)

    # The straw and the sack at the front of the bed.
    straw = [(-84.0, BED_HEIGHT), (-82.0, BED_HEIGHT + 9.0), (-72.0, BED_HEIGHT + 14.0), (-58.0, BED_HEIGHT + 12.0), (-46.0, BED_HEIGHT + 7.0), (-38.0, BED_HEIGHT)]
    pen.poly(straw, STRAW)
    for k in range(11):
        x = -80.0 + k * 3.8
        pen.line([(x, BED_HEIGHT + 1.0), (x + 2.0 - (k % 3), BED_HEIGHT + 5.0 + (k * 5 % 7))], STRAW_DARK, 0.5)
    pen.poly([(-34.0, BED_HEIGHT), (-36.0, BED_HEIGHT + 11.0), (-30.0, BED_HEIGHT + 16.0), (-26.0, BED_HEIGHT + 19.0), (-22.0, BED_HEIGHT + 16.0), (-15.0, BED_HEIGHT + 12.0), (-13.0, BED_HEIGHT)], SACK)
    pen.line([(-30.0, BED_HEIGHT + 15.6), (-22.0, BED_HEIGHT + 15.6)], ROPE, 1.0)
    pen.line([(-29.0, BED_HEIGHT + 3.0), (-27.0, BED_HEIGHT + 11.0)], SACK_DARK, 0.6)
    pen.line([(-20.0, BED_HEIGHT + 2.0), (-19.0, BED_HEIGHT + 9.0)], SACK_DARK, 0.6)

    # The front of the cart: its board, and the bench of the driver with its
    # foot board.
    for k in range(3):
        y = BED_HEIGHT + 1.0 + k * 10.6
        _plank(pen, -93.0, y, -86.0, y + 10.0, WOOD, WOOD_DARK, WOOD_LIGHT, k + 5)
    _post(pen, -89.5, BED_HEIGHT - 6.0, BED_HEIGHT + 34.0, WOOD_DARK, _mix(WOOD_DARK, INK, 0.4), WOOD, 3.6)
    pen.box(-110.0, BED_HEIGHT + 12.0, -92.0, BED_HEIGHT + 16.0, WOOD_LIGHT)
    pen.poly([(-96.0, BED_HEIGHT + 12.0), (-107.0, BED_HEIGHT + 12.0), (-103.0, BED_HEIGHT - 2.0), (-96.0, BED_HEIGHT - 2.0)], WOOD_DARK)
    pen.poly([(-92.0, BED_HEIGHT - 2.0), (-114.0, BED_HEIGHT - 6.0), (-114.0, BED_HEIGHT - 9.0), (-92.0, BED_HEIGHT - 6.0)], WOOD)
    # A lamp on a hook over the bench.
    pen.line([(-89.5, BED_HEIGHT + 33.0), (-97.0, BED_HEIGHT + 36.0), (-99.0, BED_HEIGHT + 31.0)], IRON_DARK, 1.0)
    pen.box(-102.0, BED_HEIGHT + 21.0, -96.0, BED_HEIGHT + 31.0, IRON_DARK)
    pen.box(-100.8, BED_HEIGHT + 22.6, -97.2, BED_HEIGHT + 29.4, (255, 206, 120, 255), 0.0)
    pen.box(-99.8, BED_HEIGHT + 23.6, -98.2, BED_HEIGHT + 27.6, (255, 244, 204, 255), 0.0)
    # The post at the back end: the ramp or the gate is at it.
    _post(pen, 89.5, BED_HEIGHT - 6.0, BED_HEIGHT + RAIL_HEIGHT + 3.0, WOOD_DARK, _mix(WOOD_DARK, INK, 0.4), WOOD, 3.6)

    # The bed: its planks, seen from a little above, then its near edge.
    pen.box(-88.0, BED_HEIGHT - 2.0, 88.0, BED_HEIGHT + 3.4, WOOD_DARK)
    for k in range(8):
        x = -88.0 + k * 22.0
        pen.line([(x + 0.4, BED_HEIGHT + 0.4), (x + 3.0, BED_HEIGHT + 3.0)], INK, 0.5)
    pen.line([(-87.0, BED_HEIGHT + 2.6), (87.0, BED_HEIGHT + 2.6)], _mix(WOOD_DARK, WOOD, 0.6), 0.6)


def _ramp(pen: _Pen) -> None:
    """The back end of the cart, let down: a ramp of planks with cleats, from
    the bed to the floor. Its surface goes through the front corner of each
    step of the collision."""
    x0, y0 = BED_HALF, BED_HEIGHT
    x1 = BED_HALF + RAMP_RUN * (RAMP_STEPS + 0.5)
    slope = (RAMP_RISE / RAMP_RUN)
    surface = lambda x: y0 - (x - x0) * slope  # noqa: E731
    thick = 5.0
    pen.poly([(x0 - 2.0, y0), (x1, max(0.0, surface(x1))), (x1, 0.0), (x1 - 8.0, 0.0), (x0 - 2.0, y0 - thick)], WOOD)
    pen.line([(x0 - 1.0, y0 - 0.9), (x1 - 1.0, surface(x1) + 0.2)], WOOD_LIGHT, 0.8)
    pen.line([(x0 - 1.0, y0 - thick + 0.9), (x1 - 9.0, 0.9)], WOOD_DARK, 0.8)
    # Cleats: a body does not slide on them.
    for k in range(1, 9):
        x = x0 + k * 10.6
        y = surface(x)
        pen.poly([(x - 1.6, y + 0.9 + 1.6 * slope), (x + 1.6, y + 0.9 - 1.6 * slope), (x + 1.6, y + 2.6 - 1.6 * slope), (x - 1.6, y + 2.6 + 1.6 * slope)], WOOD_LIGHT, 0.6)
    # The two irons that hold it to the bed.
    pen.box(x0 - 4.0, y0 - 6.5, x0 + 4.5, y0 + 0.8, IRON)
    pen.disc(x0, y0 - 2.8, 1.1, IRON_LIGHT, 0.0)


def _gate(pen: _Pen) -> None:
    """The back end of the cart, shut: a board as high as the rail."""
    for k in range(2):
        y = BED_HEIGHT + 1.0 + k * 10.6
        _plank(pen, 86.0, y, 93.0, y + 10.0, WOOD, WOOD_DARK, WOOD_LIGHT, k)
    pen.box(85.0, BED_HEIGHT - 6.5, 93.5, BED_HEIGHT + 0.8, IRON)


def _front(pen: _Pen) -> None:
    """The near side of the cart: the beam of the bed, five posts, two rails
    and the two wheels. The space between the rails is open: a body in the
    cart shows through it."""
    top = BED_HEIGHT + RAIL_HEIGHT
    # The beam is the edge of the bed. Its top is a little over the surface,
    # so the feet of a body are behind it.
    _plank(pen, -91.0, BED_HEIGHT - 9.0, 91.0, BED_HEIGHT + 1.6, WOOD, WOOD_DARK, WOOD_LIGHT, 2)
    for x in (-84.0, -42.0, 0.0, 42.0, 84.0):
        pen.box(x - 3.4, BED_HEIGHT - 8.0, x + 3.4, BED_HEIGHT + 0.6, IRON)
        pen.disc(x, BED_HEIGHT - 3.6, 1.1, IRON_LIGHT, 0.0)
    for y, seed in zip(RAILS, (1, 4)):
        _plank(pen, -90.0, y, 90.0, y + RAIL_THICK, WOOD, WOOD_DARK, WOOD_LIGHT, seed)
    for x in (-84.0, -42.0, 0.0, 42.0, 84.0):
        _post(pen, x, BED_HEIGHT + 1.0, top, WOOD_LIGHT, WOOD, _mix(WOOD_LIGHT, (255, 240, 210, 255), 0.4))
        for y in RAILS:
            pen.disc(x, y + RAIL_THICK * 0.5, 0.85, IRON_DARK, 0.0)
    # The wheels are in front of the cart and of what is in it.
    for x in WHEELS:
        _wheel(pen, x, 0.26 + x * 0.01)


def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
    pen = _Pen()
    {"front": _front, "ramp": _ramp, "gate": _gate}.get(animation, _back)(pen)
    return pen.publish()


def render(out_dir: str | Path, **opts) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        label_width=112,
        # The game names the bed in frame pixels: the frame stays as drawn.
        auto_crop=False,
    )
    return [
        outputs["canonical"],
        outputs["canonical_transparent"],
        outputs["spritesheet"],
        outputs["yaml"],
        outputs["preview"],
    ]
