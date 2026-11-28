"""Draw intact props and cut their fragments from the same image."""

from functools import lru_cache
from random import Random

from PIL import Image, ImageChops, ImageDraw

from ...authoring.sheet_build import build_sheet

CRATE_SIZE = (128, 128)
SEAM_SIZE = (96, 224)

# The first frames are the large pieces. Lower quality tiers draw these first.
CRATE_CUTS = (
    [(3, 3), (85, 3), (73, 17), (95, 19), (55, 35), (23, 24), (16, 60), (3, 68)],
    [(19, 66), (57, 43), (91, 20), (125, 4), (125, 32), (93, 41),
     (104, 45), (66, 58), (41, 77)],
    [(5, 103), (24, 89), (61, 83), (57, 92), (98, 92), (83, 106),
     (109, 108), (89, 125), (4, 125)],
    [(102, 53), (125, 35), (125, 99), (114, 124), (94, 125),
     (107, 100), (97, 83), (105, 71)],
    [(6, 72), (26, 59), (31, 77), (75, 65), (39, 90), (4, 101)],
    [(75, 4), (115, 3), (100, 14), (84, 15)],
)
SEAM_CUTS = (
    [(0, 152), (23, 136), (44, 146), (55, 168), (47, 183), (67, 213),
     (51, 223), (0, 223)],
    [(96, 10), (96, 102), (75, 125), (66, 102), (41, 90), (56, 61),
     (63, 37), (80, 15)],
    [(0, 0), (79, 0), (68, 18), (47, 35), (39, 59), (14, 66), (0, 49)],
    [(96, 111), (96, 223), (70, 223), (57, 184), (69, 165), (55, 143),
     (73, 130), (81, 138)],
    [(0, 52), (16, 73), (38, 64), (34, 91), (59, 106), (70, 128),
     (49, 145), (24, 130), (0, 145)],
    [(44, 36), (61, 25), (50, 55), (40, 73), (37, 55)],
)


def crate():
    image = Image.new("RGBA", CRATE_SIZE)
    draw = ImageDraw.Draw(image)
    rng = Random(915)
    draw.polygon([(4, 5), (123, 3), (126, 122), (4, 125)], fill="#302018")
    for x, face in zip((11, 36, 62, 88), ("#8e542e", "#a36538", "#93562d", "#aa6839")):
        draw.rectangle((x, 8, x + 24, 120), fill=face)
        draw.line((x + 1, 9, x + 1, 119), fill="#d69351", width=2)
        draw.line((x + 23, 9, x + 23, 120), fill="#53301f", width=2)
        for _ in range(23):
            gx, gy = rng.randrange(x + 4, x + 22), rng.randrange(12, 105)
            length = rng.randrange(4, 24)
            draw.line([(gx, gy), (gx - 1, gy + length // 2), (gx, gy + length)],
                      fill=rng.choice(("#bf8047", "#74452a", "#cd8d50")))
    for x, y in ((47, 45), (78, 92), (95, 27)):
        draw.ellipse((x - 6, y - 11, x + 6, y + 11), outline="#724326", width=2)
        draw.ellipse((x - 2, y - 5, x + 2, y + 5), fill="#714022")
    draw.polygon([(8, 108), (99, 9), (122, 10), (111, 23), (24, 119), (7, 122)],
                 fill="#bd7b44")
    draw.line([(9, 106), (99, 9)], fill="#e3a160", width=3)
    draw.line([(23, 119), (120, 12)], fill="#603720", width=4)
    for offset in (5, 8, 12):
        draw.line([(20 + offset, 108), (96 + offset, 22)], fill="#956037")
    for top in (5, 107):
        draw.polygon([(5, top + 1), (123, top), (123, top + 13), (6, top + 15)],
                     fill="#b87945", outline="#583623", width=2)
        draw.line((8, top + 2, 119, top + 1), fill="#e1a26a", width=2)
        for x in (15, 114):
            draw.ellipse((x - 3, top + 5, x + 4, top + 12), fill="#493b33")
            draw.point((x, top + 6), fill="#d2b897")
    return image


def seam():
    image = Image.new("RGBA", SEAM_SIZE, "#3d4b52")
    draw = ImageDraw.Draw(image)
    rng = Random(624)
    for y in range(-24, 236, 17):
        points = [(x, y - x // 3 + rng.randrange(-4, 6)) for x in range(-12, 111, 12)]
        width = rng.randrange(5, 15)
        band = points + [(x, by + width) for x, by in reversed(points)]
        draw.polygon(band, fill=rng.choice(("#526469", "#495c65", "#55666a", "#534b59")))
        draw.line(points, fill=rng.choice(("#748687", "#7e717d", "#687c86")), width=2)
    for _ in range(290):
        x, y = rng.randrange(96), rng.randrange(224)
        draw.line((x, y, x + rng.randrange(1, 6), y - 1),
                  fill=rng.choice(("#3b494f", "#6d7c7d", "#617278")))
    groove = [(68, -1), (51, 22), (47, 47), (33, 64), (43, 90),
              (58, 106), (67, 132), (54, 149), (63, 172), (51, 186), (66, 223)]
    draw.line([(x + 3, y) for x, y in groove], fill="#71888a", width=5)
    draw.line(groove, fill="#202d36", width=4)
    for branch in ([(47, 47), (27, 54), (14, 73), (0, 75)],
                   [(58, 106), (74, 108), (96, 92)],
                   [(54, 149), (27, 153), (13, 172), (0, 166)]):
        draw.line(branch, fill="#26353b", width=2)
    for x, y in ((50, 42), (34, 66), (62, 121), (56, 152), (57, 199)):
        draw.polygon([(x - 3, y + 4), (x, y - 4), (x + 4, y - 5), (x + 3, y + 1)],
                     fill="#84bfc0")
        draw.point((x + 2, y - 3), fill="#d0e2cf")
    return image


def recipe(name, size, intact, cuts, edge):
    @lru_cache(maxsize=1)
    def source():
        return intact()

    def render_frame(row, index, _):
        if row == "idle":
            return source()
        cut = cuts[index]
        mask = Image.new("L", size)
        ImageDraw.Draw(mask).polygon(cut, fill=255)
        fragment = source().copy()
        ImageDraw.Draw(fragment).line(cut + cut[:1], fill=edge, width=3)
        fragment.putalpha(ImageChops.multiply(source().getchannel("A"), mask))
        return fragment

    def render(out_dir, **_):
        outputs = build_sheet(
            target=name, rows=[("idle", 1, 400), ("fracture", len(cuts), 100)],
            render_fn=render_frame, out_dir=out_dir, frame_size=size,
            auto_crop=False, trim=True,
        )
        return [outputs[key] for key in (
            "canonical", "canonical_transparent", "spritesheet", "yaml", "ron", "preview",
        )]

    return {"render": render}


TARGETS = {
    "breakable_wood_crate": recipe("breakable_wood_crate", CRATE_SIZE, crate, CRATE_CUTS, "#d4a46e"),
    "mine_seam_wall": recipe("mine_seam_wall", SEAM_SIZE, seam, SEAM_CUTS, "#8c969b"),
}
