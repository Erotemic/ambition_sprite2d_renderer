"""The ornaments of the two-state hub: what its architecture has once for each
block, and not in a pattern that repeats.

The skin of a block (`two_state.py`) repeats each 64 units, so it has no
place for a thing that is one for each block: the arcade below a platform and
its banners, the ivy on a corner, the emblem on a large wall, a fluted
pillar. Each of those is a picture here, in each state, and the game places
it by the shape of the block (`lay_block_skin` in the terrain skin of the
renderer):

| part | size (units) | where the game lays it |
| --- | --- | --- |
| `pillar` | 48 x 224 | the fill of a block 48 wide or less and over 96 high; it repeats down from the top of the block, and its right `PILLAR_EDGE` stays at the right of a narrower block |
| `arch` | 150 x 48 | one bay below a platform (a block 40 high or less and 96 wide or more): the platform is cut in bays near 150 wide; the brackets (`ARCH_BRACKET` at each end) keep their size and the span between them is stretched |
| `banner` | 28 x 80 | in the middle of some bays, from the bottom of the platform |
| `ivy` | 3 x 64 x 52 | a clump on a top corner of a block; the corner is at (`IVY_CORNER`) of the square, and the square is mirrored for a right corner |
| `ivy_strands` | 3 x 40 x 120 | what hangs below the end of a platform whose corner has ivy; x goes into the platform from its end |
| `emblem` | 76 x 108 | a gold sigil in the middle of a large wall face (150 x 150 or more), one each 320 units |

The corrupted state of each one is the clean one in voxels, as in the skin:
the same silhouette, the gold lines lit as cyan and magenta, and what is not a
place to stand dim, with the sky through it. Nothing here is drawn above the
walking line of the top of a block.
"""

from __future__ import annotations

import numpy as np
from PIL import Image

from .two_state import (
    CORRUPT_AIR,
    CYAN,
    GOLD,
    GOLD_LIT,
    INK_HI,
    INK_LO,
    MAGENTA,
    MORTAR,
    RIM,
    STONE,
    STONE_LIT,
    STONE_SHADE,
    VOXEL,
    WALK_LINE,
    Picture,
    circuit,
    gilded,
    luma,
    mix,
    rand_cell,
    smoothstep,
    voxel_ink,
)

KEYS = ("hub_clean", "hub_corrupt")

PILLAR = (48, 224)
#: The right part of the pillar picture that a narrower pillar keeps at its
#: right side: the shaded edge.
PILLAR_EDGE = 8.0
ARCH = (150, 48)
#: The width of the bracket at each end of a bay. It is not stretched.
ARCH_BRACKET = 18.0
BANNER = (28, 80)
IVY_VARIANTS = 3
IVY = (64, 52)
#: The top corner of the block in an ivy square: the clump reaches 11 past
#: the end of the block and 8 over its top.
IVY_CORNER = (11.0, 8.0)
STRANDS = (40, 120)
EMBLEM = (76, 108)

LEAF_DARK = np.array((0.205, 0.345, 0.225))
LEAF_MID = np.array((0.305, 0.470, 0.270))
LEAF_LIT = np.array((0.470, 0.625, 0.340))
LEAVES = (LEAF_DARK, LEAF_MID, LEAF_LIT)
CLOTH = np.array((0.300, 0.395, 0.585))
CLOTH_CORRUPT = np.array((0.260, 0.060, 0.270))
#: Below a platform the stone is in its own shade.
SOFFIT_STONE = mix(STONE, STONE_SHADE, 0.62)
GOLD_LINE = mix(GOLD, GOLD_LIT, 0.35)


def blocks(pic: Picture, size: float) -> tuple[np.ndarray, np.ndarray]:
    """The middle of the block of `size` each texel is in."""
    return (np.floor(pic.x / size) + 0.5) * size, (np.floor(pic.y / size) + 0.5) * size


def covered(part, x0: np.ndarray, y0: np.ndarray, vox: float) -> np.ndarray:
    """How much of the block of `vox` from `x0, y0` `part` covers, from 0 to
    1: a thin line (the curve of an arch, the border of a banner) is in the
    blocks it crosses, and not only in those whose middle it is on."""
    steps = (np.arange(4) + 0.5) / 4.0 * vox
    hits = sum(part(x0 + dx, y0 + dy).astype(float) for dx in steps for dy in steps)
    return hits / 16.0


def in_voxels(pic: Picture, part, vox: float, salt: int, alpha: float, gold: np.ndarray, gold_light: np.ndarray, cloth=None, cloth_gold=None) -> None:
    """Paint the corrupted state of what `part(x, y)` says is there, in blocks
    of `vox`: dim ink with the sky through it, a lit top face, and the gold
    lines (`gold`, exact, not in blocks) lit."""
    x0, y0 = np.floor(pic.x / vox) * vox, np.floor(pic.y / vox) * vox
    r = rand_cell(np.floor(pic.x / vox), np.floor(pic.y / vox), salt)
    keep = (covered(part, x0, y0, vox) >= 0.25) & (r > 0.14)
    col = mix(INK_LO, INK_HI, 0.45 + 0.4 * r)
    if cloth is not None:
        on_cloth = covered(cloth, x0, y0, vox) >= 0.25
        col = np.where(on_cloth[..., None], CLOTH_CORRUPT * (0.8 + 0.4 * r)[..., None], col)
    col = mix(col, CORRUPT_AIR, 0.20)
    # The top face of a block is lit, as in the mass of the architecture.
    above = covered(part, x0, y0 - vox, vox) >= 0.25
    col = np.where((~above & (pic.y - y0 < 2.0))[..., None], col * 1.3 + np.array((0.08, 0.07, 0.16)), col)
    seam = (pic.x - x0 >= vox - 1.0) | (pic.y - y0 >= vox - 1.0)
    col = np.where(seam[..., None], col * 0.85, col)
    pic.put(keep, col, alpha)
    # The lines stay thin and whole: they are the circuit of the mass.
    pic.put(gold, mix(INK_HI, gold_light, 0.85))
    if cloth_gold is not None:
        pic.put(cloth_gold, mix(INK_HI, MAGENTA, 0.85))


# ---------------------------------------------------------------- pillar --


def pillar_stone(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """A fluted shaft with gold bands: the stone, and the distance to the gold."""
    width = float(PILLAR[0])
    flute = np.mod(x, 8.0)
    col = STONE * (1.0 - 0.07 * smoothstep(0.0, 3.0, np.abs(flute - 4.0)) + 0.035)[..., None]
    col = np.where((flute < 1.0)[..., None], MORTAR, col)
    band = np.mod(y + 60.0, float(PILLAR[1]))
    in_band = band < 22.0
    col = np.where(in_band[..., None], np.where((band > 15.0)[..., None], STONE_SHADE, STONE_LIT), col)
    gold = np.where(in_band, np.minimum(np.abs(band - 3.0), np.abs(band - 13.0)), 1.0e4)
    # The light is from the upper left.
    col = np.where((x < 2.0)[..., None], mix(col, STONE_LIT, 0.8), col)
    col = np.where((x > width - 3.0)[..., None], mix(col, STONE_SHADE, 0.8), col)
    return col, gold


def clean_pillar() -> Picture:
    pic = Picture(PILLAR)
    col, gold = pillar_stone(pic.x, pic.y)
    pic.put(np.ones_like(pic.alpha, dtype=bool), gilded(col, gold, pic.x + pic.y))
    return pic


def corrupt_pillar() -> Picture:
    pic = Picture(PILLAR)
    stone, gold = pillar_stone(pic.x, pic.y)
    col = voxel_ink(pic.x, pic.y, stone, np.zeros_like(pic.alpha, dtype=bool))
    col = circuit(col, gold, pic.y)
    # The rim of the box on each side: the pillar is where a body stops.
    edge = (pic.x < 1.5) | (pic.x >= PILLAR[0] - 1.5)
    col = np.where(edge[..., None], mix(col, RIM, 0.8), col)
    pic.put(np.ones_like(pic.alpha, dtype=bool), col)
    return pic


# ------------------------------------------------------------------ arch --


def arch_part(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Where one bay of the arcade is stone, and where its gold line is. `x`
    is from the left end of the bay, `y` down from the bottom of the
    platform."""
    half = ARCH[0] * 0.5
    cx = x - half
    soffit = y < 6.0
    # A stepped bracket at each end of the bay.
    from_end = half - np.abs(cx)
    step = np.floor(y / 8.0)
    bracket = (from_end < ARCH_BRACKET - 1.0 - step * 3.0) & (y < ARCH[1])
    # A shallow arch between the brackets: thin at the crown.
    span = half - 15.0
    rise = min(span * 0.55, 38.0)
    k = np.clip(np.abs(cx) / span, 0.0, 1.0)
    curve = 6.0 + rise * (1.0 - np.sqrt(np.maximum(1.0 - k * k, 0.0)))
    under_curve = (np.abs(cx) < span) & (y < curve)
    gold = under_curve & (y > curve - 1.8) & ~bracket
    return (soffit | bracket | under_curve), gold


def clean_arch() -> Picture:
    pic = Picture(ARCH)
    stone, gold = arch_part(pic.x, pic.y)
    col = SOFFIT_STONE * (1.0 - 0.10 * np.clip(pic.y / 46.0, 0.0, 1.0))[..., None]
    col = np.where(gold[..., None], GOLD_LINE, col)
    pic.put(stone, col)
    return pic


def corrupt_arch() -> Picture:
    pic = Picture(ARCH)
    _, gold = arch_part(pic.x, pic.y)
    in_voxels(pic, lambda x, y: arch_part(x, y)[0], VOXEL * 0.5, 670, 0.88, gold, CYAN)
    return pic


# ---------------------------------------------------------------- banner --


def banner_part(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Where the banner is cloth, and where it is gold (its border, its hem,
    the emblem on it). `x` is from its left edge, `y` down from the bottom of
    the platform."""
    ax = np.abs(x - BANNER[0] * 0.5)
    hem = 66.0 + ax * 0.9
    cloth = (ax < 14.0) & (y < hem) & (y >= 0.0)
    emblem = np.abs(ax + np.abs(y - 36.0) - 6.5)
    gold = cloth & ((ax > 11.8) | (y > hem - 2.2) | (emblem < 1.0))
    return cloth, gold


def clean_banner() -> Picture:
    pic = Picture(BANNER)
    cloth, gold = banner_part(pic.x, pic.y)
    fold = 0.92 + 0.08 * np.sin(pic.x * 0.9)
    col = np.where(gold[..., None], GOLD_LINE, CLOTH * fold[..., None])
    pic.put(cloth, col)
    return pic


def corrupt_banner() -> Picture:
    pic = Picture(BANNER)
    _, gold = banner_part(pic.x, pic.y)
    in_voxels(
        pic,
        lambda x, y: banner_part(x, y)[0],
        VOXEL * 0.5,
        671,
        0.88,
        np.zeros_like(gold),
        CYAN,
        cloth=lambda x, y: banner_part(x, y)[0],
        cloth_gold=gold,
    )
    return pic


# ------------------------------------------------------------------- ivy --


def ivy_clump(qx: np.ndarray, qy: np.ndarray, key: int) -> np.ndarray:
    """Which leaf is at `q` (from the top corner of the block: x into the
    block from its end, y down): 0 for none, 1..3 dark to lit. The ivy is
    thick on the corner and thin away from it, and thins to nothing at the
    edge of its square."""
    from_corner = np.hypot(qx - 6.0, (qy - 5.0) * 0.75)
    fringe = smoothstep(-8.0, -1.0, qy) * smoothstep(-11.0, -4.0, qx) * smoothstep(52.0, 45.0, qx) * smoothstep(44.0, 37.0, qy)
    density = np.exp(-np.maximum(from_corner - 9.0, 0.0) / 12.0) * 0.95 * fringe
    cx, cy = np.floor(qx / 6.0), np.floor(qy / 6.0)
    ix, iy = cx + key * 37.0, cy
    present = rand_cell(ix, iy, 710) <= density
    jx = rand_cell(ix, iy, 711) - 0.5
    jy = rand_cell(ix, iy, 712) - 0.5
    ox = qx - (cx + 0.5) * 6.0 - jx * 2.4
    oy = qy - (cy + 0.5) * 6.0 - jy * 2.4
    angle = rand_cell(ix, iy, 713) * np.pi
    s, c = np.sin(angle), np.cos(angle)
    ex = (ox * c + oy * s) / 3.9
    ey = (oy * c - ox * s) / 2.4
    leaf = present & (ex * ex + ey * ey <= 1.0)
    shade = 1 + np.floor(rand_cell(ix, iy, 714) * 2.99).astype(int)
    return np.where(leaf, shade, 0)


def dead_leaf(pic: Picture, where: np.ndarray, cell: float = 4.0) -> None:
    """Leaves after the rewrite: dead blocks, and a few are lit. They are not
    black: black blocks beside a platform read as pieces of the platform."""
    r = rand_cell(np.floor(pic.x / cell), np.floor(pic.y / cell), 740)
    col = mix(np.array((0.060, 0.130, 0.150)) * (0.7 + 0.6 * r)[..., None], CORRUPT_AIR, 0.30)
    lit = r > 0.95
    pic.put(where & ~lit, col, 0.80)
    pic.put(where & lit, CYAN * 0.75, 0.90)


def ivy_square(variant: int, corrupt: bool) -> Picture:
    pic = Picture(IVY)
    qx, qy = pic.x - IVY_CORNER[0], pic.y - IVY_CORNER[1]
    if not corrupt:
        leaf = ivy_clump(qx, qy, variant)
        for shade, colour in enumerate(LEAVES, start=1):
            pic.put(leaf == shade, colour)
        return pic
    bx, by = blocks(pic, 4.0)
    leaf = ivy_clump(bx - IVY_CORNER[0], by - IVY_CORNER[1], variant) > 0
    # The walking line is over the ivy: it is where the body stands.
    walk = (qx >= 0.0) & (qy >= 0.0) & (qy < 2.0)
    dead_leaf(pic, leaf & ~walk)
    return pic


def strands(qx: np.ndarray, qy: np.ndarray, key: int) -> np.ndarray:
    """Which leaf of the three strands that hang from the end of a platform
    is at `q` (x into the platform from its end, y down from its bottom): 0
    for none, 1 for a stem, 2..3 for a leaf. The strands do not move: a line
    one pixel wide that moved in the wind read as a flicker."""
    out = np.zeros(qx.shape, dtype=int)
    row = np.floor(qy / 7.0)
    for k in range(3):
        sid = key * 11 + k
        length = 34.0 + 84.0 * float(rand_cell(np.array(sid), np.array(0), 730))
        sx = 4.0 + k * 9.0 + (float(rand_cell(np.array(sid), np.array(0), 731)) - 0.5) * 5.0
        dx = qx - sx
        on = (qy >= 0.0) & (qy <= length)
        stem = on & (np.abs(dx) < 0.7)
        # A leaf on each side in turn, every 7, with some left out.
        side = np.where(np.mod(row + k, 2.0) == 0.0, 1.0, -1.0)
        ox = dx - side * 3.4
        oy = qy - (row + 0.5) * 7.0
        ex = (ox + oy * 0.35 * side) / 3.6
        ey = oy / 2.2
        leaf = on & (rand_cell(np.full_like(row, sid), row, 732) < 0.78) & (ex * ex + ey * ey < 1.0)
        shade = 2 + np.floor(rand_cell(np.full_like(row, sid + 1000), row, 733) * 1.99).astype(int)
        out = np.where((out == 0) & stem, 1, out)
        out = np.where((out == 0) & leaf, shade, out)
    return out


def strand_square(variant: int, corrupt: bool) -> Picture:
    pic = Picture(STRANDS)
    if not corrupt:
        leaf = strands(pic.x, pic.y, variant)
        for shade, colour in enumerate(LEAVES, start=1):
            pic.put(leaf == shade, colour)
        return pic
    bx, by = blocks(pic, 4.0)
    dead_leaf(pic, strands(bx, by, variant) > 0)
    return pic


def strip(squares: list[Picture]) -> Image.Image:
    images = [square.publish() for square in squares]
    w, h = images[0].size
    out = Image.new("RGBA", (w * len(images), h))
    for index, image in enumerate(images):
        out.paste(image, (index * w, 0))
    return out


# ---------------------------------------------------------------- emblem --


def sigil_distance(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """The distance to the lines of the sigil: two rings, a square on its
    corner, an upright line through it, and a small ring in the middle."""
    dx, dy = x - EMBLEM[0] * 0.5, y - EMBLEM[1] * 0.5
    radius = 34.0
    length = np.hypot(dx, dy)
    d = np.abs(length - radius)
    d = np.minimum(d, np.abs(length - radius * 0.62))
    d = np.minimum(d, np.abs(np.abs(dx) + np.abs(dy) - radius * 0.62) * 0.7071)
    d = np.minimum(d, np.where(np.abs(dy) < radius * 1.5, np.abs(dx), 1.0e4))
    return np.minimum(d, np.abs(length - radius * 0.15))


def clean_emblem() -> Picture:
    pic = Picture(EMBLEM)
    d = sigil_distance(pic.x, pic.y)
    gold = smoothstep(1.5, 0.5, d)
    glint = 0.5 + 0.5 * np.sin((pic.x + pic.y) * 0.06)
    pic.put(gold > 0.0, mix(GOLD, GOLD_LIT, glint * glint), gold)
    return pic


def corrupt_emblem() -> Picture:
    pic = Picture(EMBLEM)
    d = sigil_distance(pic.x, pic.y)
    lit = np.clip((smoothstep(1.3, 0.4, d) + np.exp(-d / 4.0) * 0.18) * 0.94, 0.0, 1.0)
    pic.put(lit > 0.02, CYAN, lit)
    return pic


PAINTERS = {
    ("hub_clean", "pillar"): lambda: clean_pillar().publish(),
    ("hub_corrupt", "pillar"): lambda: corrupt_pillar().publish(),
    ("hub_clean", "arch"): lambda: clean_arch().publish(),
    ("hub_corrupt", "arch"): lambda: corrupt_arch().publish(),
    ("hub_clean", "banner"): lambda: clean_banner().publish(),
    ("hub_corrupt", "banner"): lambda: corrupt_banner().publish(),
    ("hub_clean", "ivy"): lambda: strip([ivy_square(v, False) for v in range(IVY_VARIANTS)]),
    ("hub_corrupt", "ivy"): lambda: strip([ivy_square(v, True) for v in range(IVY_VARIANTS)]),
    ("hub_clean", "ivy_strands"): lambda: strip([strand_square(v, False) for v in range(IVY_VARIANTS)]),
    ("hub_corrupt", "ivy_strands"): lambda: strip([strand_square(v, True) for v in range(IVY_VARIANTS)]),
    ("hub_clean", "emblem"): lambda: clean_emblem().publish(),
    ("hub_corrupt", "emblem"): lambda: corrupt_emblem().publish(),
}

#: The size each part is laid at, in world units: a strip is its squares side
#: by side.
SIZES = {
    "pillar": PILLAR,
    "arch": ARCH,
    "banner": BANNER,
    "ivy": (IVY[0] * IVY_VARIANTS, IVY[1]),
    "ivy_strands": (STRANDS[0] * IVY_VARIANTS, STRANDS[1]),
    "emblem": EMBLEM,
}


def parts(key: str) -> dict[str, Image.Image]:
    """Each ornament of the skin `key`, by part: none for a skin with none."""
    return {part: paint() for (owner, part), paint in PAINTERS.items() if owner == key}
