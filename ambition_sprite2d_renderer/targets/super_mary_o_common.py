from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Tuple

from PIL import Image, ImageColor, ImageDraw, ImageFont
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

OUTLINE = (28, 22, 19, 255)
WHITE = (255, 255, 255, 255)
TRANSPARENT = (0, 0, 0, 0)
SHADOW = (0, 0, 0, 70)


@dataclass(frozen=True)
class MaryPalette:
    cap: RGBA
    shirt: RGBA
    overalls: RGBA
    buttons: RGBA
    gloves: RGBA
    hair: RGBA
    skin: RGBA
    shoes: RGBA
    accent: RGBA


NORMAL_MARY = MaryPalette(
    cap=(184, 36, 34, 255),
    shirt=(194, 48, 40, 255),
    overalls=(48, 94, 208, 255),
    buttons=(254, 214, 75, 255),
    gloves=(247, 243, 236, 255),
    hair=(101, 65, 35, 255),
    skin=(251, 193, 146, 255),
    shoes=(118, 80, 43, 255),
    accent=(238, 170, 64, 255),
)

FIRE_MARY = MaryPalette(
    cap=(201, 66, 38, 255),
    shirt=(214, 73, 42, 255),
    overalls=(242, 240, 235, 255),
    buttons=(248, 178, 66, 255),
    gloves=(250, 248, 246, 255),
    hair=(112, 72, 41, 255),
    skin=(251, 197, 150, 255),
    shoes=(121, 83, 46, 255),
    accent=(248, 157, 52, 255),
)

PIPE_GREEN = (29, 159, 75, 255)
PIPE_GREEN_DARK = (20, 102, 49, 255)
PIPE_GREEN_LIGHT = (94, 214, 137, 255)
COIN_GOLD = (240, 189, 44, 255)
COIN_GOLD_LIGHT = (255, 235, 129, 255)
BRICK = (171, 101, 54, 255)
BRICK_DARK = (118, 64, 35, 255)
BRICK_LIGHT = (208, 148, 96, 255)
GROUND_BROWN = (176, 118, 64, 255)
GROUND_BROWN_DARK = (121, 80, 40, 255)
GROUND_BROWN_LIGHT = (217, 165, 99, 255)
SKY_BLUE = (120, 195, 255, 255)
MILK_WHITE = (248, 246, 238, 255)
MILK_BLUE = (86, 136, 218, 255)
GAS_RED = (210, 72, 62, 255)
GAS_RED_DARK = (143, 42, 34, 255)
STEEL = (140, 149, 158, 255)
STEEL_DARK = (79, 89, 99, 255)


def rgba(color: str, alpha: int = 255) -> RGBA:
    r, g, b = ImageColor.getrgb(color)
    return (r, g, b, alpha)


class PixelCanvas:
    def __init__(self, draw: ImageDraw.ImageDraw, scale: int):
        self.draw = draw
        self.scale = scale

    def _box(self, x1: float, y1: float, x2: float, y2: float) -> tuple[int, int, int, int]:
        s = self.scale
        return (
            int(round(x1 * s)),
            int(round(y1 * s)),
            int(round(x2 * s)),
            int(round(y2 * s)),
        )

    def _pt(self, x: float, y: float) -> tuple[int, int]:
        s = self.scale
        return (int(round(x * s)), int(round(y * s)))

    def rect(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        *,
        fill: RGBA,
        outline: RGBA | None = None,
        width: float = 1.0,
    ) -> None:
        self.draw.rectangle(
            self._box(x1, y1, x2, y2),
            fill=fill,
            outline=outline,
            width=max(1, int(round(width * self.scale))),
        )

    def rounded_rect(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        *,
        radius: float,
        fill: RGBA,
        outline: RGBA | None = None,
        width: float = 1.0,
    ) -> None:
        self.draw.rounded_rectangle(
            self._box(x1, y1, x2, y2),
            radius=max(1, int(round(radius * self.scale))),
            fill=fill,
            outline=outline,
            width=max(1, int(round(width * self.scale))),
        )

    def ellipse(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        *,
        fill: RGBA,
        outline: RGBA | None = None,
        width: float = 1.0,
    ) -> None:
        self.draw.ellipse(
            self._box(x1, y1, x2, y2),
            fill=fill,
            outline=outline,
            width=max(1, int(round(width * self.scale))),
        )

    def polygon(
        self,
        pts: Iterable[Point],
        *,
        fill: RGBA,
        outline: RGBA | None = None,
        width: float = 1.0,
    ) -> None:
        points = [self._pt(x, y) for x, y in pts]
        self.draw.polygon(points, fill=fill)
        if outline is not None:
            self.draw.line(
                points + [points[0]],
                fill=outline,
                width=max(1, int(round(width * self.scale))),
            )

    def line(self, pts: Iterable[Point], *, fill: RGBA, width: float = 1.0) -> None:
        self.draw.line(
            [self._pt(x, y) for x, y in pts],
            fill=fill,
            width=max(1, int(round(width * self.scale))),
            joint="curve",
        )

    def text(self, x: float, y: float, text: str, *, fill: RGBA, font: ImageFont.ImageFont) -> None:
        self.draw.text(self._pt(x, y), text, fill=fill, font=font)



def rasterize_logical(
    logical_size: tuple[int, int],
    scale: int,
    painter: Callable[[PixelCanvas], None],
) -> Image.Image:
    img = Image.new(
        "RGBA",
        (logical_size[0] * scale, logical_size[1] * scale),
        TRANSPARENT,
    )
    px = PixelCanvas(blending_draw(img), scale)
    painter(px)
    return img



def bottom_center_canvas(
    sprite: Image.Image,
    frame_size: tuple[int, int],
    *,
    offset_x: int = 0,
    offset_y: int = 0,
) -> Image.Image:
    frame = Image.new("RGBA", frame_size, TRANSPARENT)
    x = (frame.width - sprite.width) // 2 + offset_x
    y = frame.height - sprite.height + offset_y
    frame.alpha_composite(sprite, (x, y))
    return frame



def sprite_shadow(
    frame_size: tuple[int, int],
    *,
    width: int,
    height: int,
    y: int,
    x: int | None = None,
    color: RGBA = SHADOW,
) -> Image.Image:
    img = Image.new("RGBA", frame_size, TRANSPARENT)
    draw = blending_draw(img)
    if x is None:
        x = frame_size[0] // 2
    draw.ellipse((x - width // 2, y - height // 2, x + width // 2, y + height // 2), fill=color)
    return img



def label_font(size: int = 9) -> ImageFont.ImageFont:
    for name in ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            pass
    return ImageFont.load_default()
