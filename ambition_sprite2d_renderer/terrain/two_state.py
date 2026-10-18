"""The terrain skin of the two-state hub: one architecture in two states.

The hub of the game shows its architecture clean (pale stone with gold lines)
or corrupted (the same construction rebuilt in dark voxels, its gold lines lit
as cyan and magenta circuits). The state of a point is decided in the game by
a moving front: the game lays both skins on the same blocks and shows each one
on its own side of the front. With every shader off the game shows the skin of
the room's state alone, so the room keeps its look.

The corrupted state is DERIVED from the clean one, not a second drawing: each
voxel keeps the value of the stone it was, the cap's gold fillet becomes a
circuit, and the top of a block stays one bright line where a body stands.

The pictures follow the parts of `skins.py` (sizes, the surface and edge
offsets, which way each repeats). Each is drawn one texel at a time from the
world position of the texel, so two pieces of the same part laid side by side
meet with no seam. A texel is half a world unit; nothing is supersampled, so
the voxel edges and the one-unit lines stay sharp.

Two rules keep the corrupted state honest about collision:

- The top of a block has one bright line (the walking line), and nothing of
  the corrupted mass stands above it.
- What is not a place to stand (blocks that grew past the box, below a block)
  is dim and lets the sky through.
"""

from __future__ import annotations

import numpy as np
from PIL import Image

from . import skins

KEYS = ("hub_clean", "hub_corrupt")

PX = skins.PX_PER_UNIT

STONE = np.array((0.890, 0.862, 0.800))
STONE_LIT = np.array((0.965, 0.945, 0.898))
STONE_SHADE = np.array((0.775, 0.745, 0.686))
MORTAR = np.array((0.715, 0.682, 0.620))
GOLD = np.array((0.788, 0.635, 0.290))
GOLD_LIT = np.array((0.940, 0.820, 0.500))
INK_LO = np.array((0.020, 0.018, 0.055))
INK_HI = np.array((0.120, 0.104, 0.240))
MAGENTA = np.array((1.00, 0.16, 0.66))
CYAN = np.array((0.13, 0.88, 1.00))
#: The walking line of a corrupted block.
WALK_LINE = np.array((0.780, 0.720, 1.000))
#: The rim on the sides and the underside of a corrupted block.
RIM = np.array((0.300, 0.520, 0.900))
#: The corrupted sky about the architecture: what grown blocks fade toward.
CORRUPT_AIR = np.array((0.300, 0.150, 0.430))

#: The voxel edge of the corrupted architecture, in world units. Four to a
#: picture of 64, so a picture repeats on the voxel lattice.
VOXEL = 16.0
#: The period every part repeats with, in world units.
PERIOD = 64.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def rand_cell(cx: np.ndarray, cy: np.ndarray, salt: int) -> np.ndarray:
    """A value in [0, 1) for each integer cell: the hash the room look of the
    game used (`rand_cell` of `room_look_common.wgsl`), so a voxel here is the
    voxel that was drawn there."""
    x = np.floor(cx).astype(np.int64).astype(np.uint32)
    y = np.floor(cy).astype(np.int64).astype(np.uint32)
    with np.errstate(over="ignore"):
        h = (x * np.uint32(1_597_334_677)) ^ (y * np.uint32(3_812_015_801)) ^ np.uint32((salt * 668_265_263) & 0xFFFFFFFF)
        h ^= h >> np.uint32(16)
        h = h * np.uint32(0x7FEB352D)
        h ^= h >> np.uint32(15)
        h = h * np.uint32(0x846CA68B)
        h ^= h >> np.uint32(16)
    return (h >> np.uint32(8)).astype(np.float64) / 16_777_216.0


def wrapped(cell: np.ndarray, period: float, size: float) -> np.ndarray:
    """A cell index that repeats with the picture: `period` units over cells
    of `size`."""
    return np.mod(cell, round(period / size))


def smoothstep(a: float, b: float, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def mix(a, b, t) -> np.ndarray:
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    t = np.asarray(t, dtype=np.float64)
    if t.ndim and t.shape[-1] != 3:
        t = t[..., None]
    return a + (b - a) * t


def luma(c: np.ndarray) -> np.ndarray:
    return c @ np.array((0.2126, 0.7152, 0.0722))


class Picture:
    """A picture of `size` world units, one texel per half unit. `x` and `y`
    are the world position of each texel, from the corner of the picture."""

    def __init__(self, size: tuple[int, int]) -> None:
        w, h = size[0] * PX, size[1] * PX
        ys, xs = np.mgrid[0:h, 0:w]
        self.x = (xs + 0.5) / PX
        self.y = (ys + 0.5) / PX
        self.rgb = np.zeros((h, w, 3))
        self.alpha = np.zeros((h, w))

    def put(self, where: np.ndarray, colour: np.ndarray, alpha: float | np.ndarray = 1.0) -> None:
        """Paint `colour` (one colour or one for each texel) over the picture
        where `where` is true, with `alpha` cover."""
        cover = where * np.asarray(alpha, dtype=np.float64)
        colour = np.broadcast_to(np.asarray(colour, dtype=np.float64), self.rgb.shape)
        out = cover + self.alpha * (1.0 - cover)
        weight = np.where(out > 1e-6, cover / np.maximum(out, 1e-6), 0.0)[..., None]
        self.rgb = self.rgb * (1.0 - weight) + colour * weight
        self.alpha = out

    def publish(self) -> Image.Image:
        rgb = np.clip(self.rgb, 0.0, 1.0)
        # An empty texel has the mean colour of the picture, so a sampler that
        # mixes it in adds no dark line.
        full = self.alpha > 0.5
        if full.any():
            rgb = np.where(self.alpha[..., None] > 1e-3, rgb, rgb[full].mean(axis=0))
        out = np.dstack([rgb * 255.0, self.alpha * 255.0])
        return Image.fromarray(np.rint(np.clip(out, 0, 255)).astype(np.uint8), "RGBA")


# ---------------------------------------------------------------------------
# The clean state
# ---------------------------------------------------------------------------


def masonry(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Coursed stone, half bond: courses of 16, stones of 32. Each stone has
    a tone of its own, and the mortar is a line one unit wide."""
    course, brick = 16.0, 32.0
    row = np.floor(y / course)
    shift = np.mod(row, 2.0) * brick * 0.5
    bx = np.floor((x + shift) / brick)
    fy = y - row * course
    fx = x + shift - bx * brick
    tone = 1.0 + (rand_cell(wrapped(bx, PERIOD, brick), wrapped(row, PERIOD, course), 12) - 0.5) * 0.06
    col = STONE * tone[..., None]
    col = np.where(((fy < 1.0) | (fx < 1.0))[..., None], mix(col, MORTAR, 0.75), col)
    col = np.where(((fy >= 1.0) & (fy < 2.0) & (fx >= 1.0))[..., None], col * 1.03, col)
    return col


def gilded(col: np.ndarray, distance: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Gold on the lines `distance` is the distance to: a bright core, a
    darker edge, and a glint that runs along it."""
    gold = smoothstep(1.5, 0.5, distance)
    glint = 0.5 + 0.5 * np.sin(x * 2.0 * np.pi / PERIOD)
    return mix(col, mix(GOLD, GOLD_LIT, glint * glint), gold)


def cap_bands(l: np.ndarray, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The cap of a block, `l` units below its top: a lit top, a shaded
    fascia, a lit band, and dentils. With the distance to its gold fillet."""
    dentil = np.mod(x, PERIOD / 5.0) < PERIOD / 10.0
    col = np.where(
        (l < 5.0)[..., None],
        STONE_LIT,
        np.where(
            (l < 8.0)[..., None],
            STONE_SHADE,
            np.where((l < 11.0)[..., None], STONE_LIT * 0.97, np.where(dentil[..., None], STONE_LIT, STONE_SHADE * 0.94)),
        ),
    )
    return col, np.abs(l - 9.0) + 0.4


def clean_fill() -> Picture:
    pic = Picture(skins.FILL)
    pic.put(np.ones_like(pic.alpha), masonry(pic.x, pic.y))
    return pic


def clean_cap() -> Picture:
    pic = Picture(skins.CAP)
    l = pic.y - skins.CAP_SURFACE
    col, fillet = cap_bands(l, pic.x)
    pic.put(l >= 0.0, gilded(col, fillet, pic.x))
    return pic


def clean_under() -> Picture:
    pic = Picture(skins.UNDER)
    up = skins.UNDER_EDGE - pic.y
    # The lower edge of the stone is in shade, as the light is from above.
    pic.put((up > 0.0) & (up < 2.0), STONE_SHADE, 0.8)
    return pic


def clean_side() -> Picture:
    pic = Picture(skins.SIDE)
    # The light is from the upper left: the edge of the stone is lit.
    pic.put(pic.x < 2.0, STONE_LIT, 0.8)
    pic.put((pic.x >= 2.0) & (pic.x < 3.0), STONE_SHADE, 0.25)
    return pic


#: The height of one course of a platform. A platform repeats its picture
#: down each 16 units (`fill` of the one-way part), so a platform taller than
#: one course is a stack of courses, and a course is opaque to its foot.
SLAB = float(skins.ONEWAY[1])


def clean_oneway() -> Picture:
    """A course of a platform: one dressed stone with a cap, a groove and a
    gold stud in each stone."""
    pic = Picture(skins.ONEWAY)
    x, l = pic.x, pic.y
    col = STONE * (1.0 - 0.05 * (l / SLAB))[..., None]
    joint = np.mod(x + 24.0, PERIOD) < 1.0
    col = np.where((joint & (l > 10.0))[..., None], MORTAR, col)
    cap, fillet = cap_bands(l, x)
    col = np.where((l < 11.0)[..., None], cap, col)
    mid = 12.5
    sx = np.mod(x + 24.0, PERIOD) - PERIOD * 0.5
    stud = np.maximum(np.abs(sx) * 1.6 + np.abs(l - mid) - 2.2, 0.0) + 0.45
    col = np.where((l > SLAB - 2.0)[..., None], mix(col, STONE_SHADE, 0.8), col)
    pic.put(l < SLAB, gilded(col, np.minimum(fillet, stud), x))
    return pic


# ---------------------------------------------------------------------------
# The corrupted state
# ---------------------------------------------------------------------------


def voxel_ink(x: np.ndarray, y: np.ndarray, stone: np.ndarray, lit_top: np.ndarray, vox: float = VOXEL) -> np.ndarray:
    """The ink of the voxels of the mass at `x, y`: the value of the stone it
    was, voxel faces lit where nothing is above, seams (some voxels are 2x2,
    with no seam inside), cracks of magenta light along some seams, and
    scanlines."""
    cx, cy = np.floor(x / vox), np.floor(y / vox)
    wx, wy = wrapped(cx, PERIOD, vox), wrapped(cy, PERIOD, vox)
    r = rand_cell(wx, wy, 601)
    r2 = rand_cell(wx, wy, 602)
    u = np.stack([x - cx * vox, y - cy * vox], axis=-1)
    v = np.clip((luma(stone) - 0.55) / 0.40, 0.0, 1.0)
    v = 0.22 + 0.42 * v + 0.36 * r
    ink = mix(INK_LO, INK_HI, v) + np.array((0.030, -0.010, -0.030)) * (r2 - 0.5)[..., None]
    ink = np.where((lit_top & (u[..., 1] < 5.0))[..., None], ink * 1.25 + np.array((0.150, 0.130, 0.280)), ink)
    big = rand_cell(np.mod(np.floor(cx * 0.5), round(PERIOD / vox / 2)), np.mod(np.floor(cy * 0.5), round(PERIOD / vox / 2)), 610) < 0.4
    u2x, u2y = np.mod(x, vox * 2.0), np.mod(y, vox * 2.0)
    seam = ((u[..., 0] >= vox - 1.0) | (u[..., 1] >= vox - 1.0)) & ~(big & (u2x < vox * 2.0 - 1.0) & (u2y < vox * 2.0 - 1.0))
    ink = np.where(seam[..., None], ink * 0.5, ink)
    # A crack runs along the seam below some voxels and lights the stone.
    crack = rand_cell(wx, wy, 620) < 0.10
    d = np.abs(vox - 0.5 - u[..., 1])
    light = smoothstep(1.2, 0.2, d) + np.exp(-d / 3.0) * 0.30
    ink = np.maximum(ink, MAGENTA * (crack * light * 0.86)[..., None])
    ink = ink * (0.93 + 0.07 * np.mod(np.floor(y), 2.0))[..., None]
    return ink


def circuit(col: np.ndarray, distance: np.ndarray, x: np.ndarray) -> np.ndarray:
    """The gold lines of the clean state, lit: cyan in some stretches,
    magenta in others."""
    which = rand_cell(wrapped(np.floor(x / 32.0), PERIOD, 32.0), np.zeros_like(x), 640) >= 0.5
    colour = np.where(which[..., None], CYAN, MAGENTA)
    lit = smoothstep(1.3, 0.4, distance) + np.exp(-distance / 4.0) * 0.18
    return np.maximum(col, colour * (lit * 0.94)[..., None])


def corrupt_fill() -> Picture:
    pic = Picture(skins.FILL)
    stone = masonry(pic.x, pic.y)
    pic.put(np.ones_like(pic.alpha), voxel_ink(pic.x, pic.y, stone, np.zeros_like(pic.alpha, dtype=bool)))
    return pic


def corrupt_cap() -> Picture:
    """The top row of voxels: lit faces, the fillet as a circuit, and the
    walking line where the body stands. Nothing stands above the top."""
    pic = Picture(skins.CAP)
    l = pic.y - skins.CAP_SURFACE
    stone, fillet = cap_bands(l, pic.x)
    col = voxel_ink(pic.x, l, stone, np.ones_like(pic.alpha, dtype=bool))
    col = circuit(col, fillet, pic.x)
    col = np.where((l < 2.0)[..., None], WALK_LINE, col)
    pic.put(l >= 0.0, col)
    return pic


def corrupt_under() -> Picture:
    """The rim of the box on its lower edge, and a few half-size blocks that
    grew below it: dim, and the sky shows through them."""
    pic = Picture(skins.UNDER)
    up = skins.UNDER_EDGE - pic.y
    pic.put((up > 0.0) & (up < 1.5), RIM, 0.8)
    vox = VOXEL * 0.5
    cx = np.floor(pic.x / vox)
    below = -up
    grown = (below > 0.0) & (below < vox) & (rand_cell(wrapped(cx, PERIOD, vox), np.ones_like(cx), 600) < 0.16)
    r = rand_cell(wrapped(cx, PERIOD, vox), np.full_like(cx, 2.0), 601)
    ink = mix(mix(INK_LO, INK_HI, 0.35 + 0.4 * r), CORRUPT_AIR, 0.45)
    seam = (np.mod(pic.x, vox) >= vox - 1.0) | (below >= vox - 1.0)
    ink = np.where(seam[..., None], ink * 0.7, ink)
    pic.put(grown, ink, 0.55)
    return pic


def corrupt_side() -> Picture:
    """The rim of the box on a side, and the voxels of the edge column the
    mass lost: dark hollows, as the box is whole there."""
    pic = Picture(skins.SIDE)
    cy = np.floor(pic.y / VOXEL)
    r = rand_cell(np.zeros_like(cy), wrapped(cy, PERIOD, VOXEL), 600)
    lost = (pic.x < VOXEL) & (r <= 0.20)
    hollow = mix(INK_LO, INK_HI, 0.08 + 0.06 * rand_cell(np.zeros_like(cy), wrapped(cy, PERIOD, VOXEL), 601))
    pic.put(lost, hollow)
    # The edge of a hollow that is lit, as the voxel faces are.
    u = pic.y - cy * VOXEL
    pic.put(lost & (u < 1.0), CYAN, 0.55)
    pic.put(pic.x < 1.5, RIM, 0.8)
    return pic


def corrupt_oneway() -> Picture:
    """A platform in half-size voxels: the walking line on top, the fillet as
    a circuit, and the rim below."""
    pic = Picture(skins.ONEWAY)
    x, l = pic.x, pic.y
    stone, fillet = cap_bands(l, x)
    col = voxel_ink(x, l, stone, np.ones_like(pic.alpha, dtype=bool), vox=VOXEL * 0.5)
    col = circuit(col, fillet, x)
    col = np.where((l < 2.0)[..., None], WALK_LINE, col)
    col = np.where((l > SLAB - 1.5)[..., None], mix(col, RIM, 0.8), col)
    pic.put(l < SLAB, col)
    return pic


PAINTERS = {
    ("hub_clean", "fill"): clean_fill,
    ("hub_clean", "cap"): clean_cap,
    ("hub_clean", "under"): clean_under,
    ("hub_clean", "side"): clean_side,
    ("hub_clean", "oneway"): clean_oneway,
    ("hub_corrupt", "fill"): corrupt_fill,
    ("hub_corrupt", "cap"): corrupt_cap,
    ("hub_corrupt", "under"): corrupt_under,
    ("hub_corrupt", "side"): corrupt_side,
    ("hub_corrupt", "oneway"): corrupt_oneway,
}


def paint(key: str, part: str) -> Image.Image | None:
    """The picture of `part` of the skin `key`, if this module draws it."""
    painter = PAINTERS.get((key, part))
    return painter().publish() if painter else None
