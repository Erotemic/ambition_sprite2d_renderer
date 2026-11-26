"""The three gallery entrances in the central hub."""

from ._district_props import Piece, targets
from ._town_kit import box
from .castle_godwin import lettering

STONE = (213, 204, 181)
CREAM = (248, 238, 211)
BRASS = (205, 166, 84)
INK = (32, 43, 70)


def doorway(c, x, name, panel, accent):
    """Draw a door with a nameplate above the frame."""
    c.put(c.mask(lambda p: p.arch(x - 27, 830, x + 27, 928)), CREAM)
    c.put(c.mask(lambda p: p.arch(x - 24, 833, x + 24, 925)), BRASS)
    c.put(c.mask(lambda p: p.arch(x - 21, 835, x + 21, 923)), panel)
    c.put(c.mask(box(x - 21, 900, x + 21, 923)), INK, 0.6)
    c.put(c.mask(box(x - 25, 923, x + 25, 928)), STONE)
    c.put(c.mask(box(x - 17, 903, x + 17, 905)), accent)
    c.put(c.mask(lambda p: p.ring(x + 14, 898, 2.7, 1.1)), BRASS)
    c.put(c.mask(box(x - 48, 801, x + 48, 823)), STONE)
    c.put(c.mask(box(x - 46, 803, x + 46, 821)), panel)
    lettering(c, name, x, 807, 9, CREAM)


def portraits(c, x):
    """Draw the silhouettes on the Characters door."""
    c.put(c.mask(lambda p: [
        p.ellipse(x + offset, 867 - abs(offset) / 3, 4.5, 5)
        for offset in (-10, 0, 10)
    ]), CREAM)
    c.put(c.mask(lambda p: [
        p.arch(x + offset - 6, 873 - abs(offset) / 4, x + offset + 6, 883)
        for offset in (-10, 0, 10)
    ]), CREAM)


def landscape(c, x):
    """Draw the mountains on the Biomes door."""
    c.put(c.mask(lambda p: p.ellipse(x + 9, 859, 4, 4)), BRASS)
    c.put(c.mask(lambda p: p.poly([
        (x - 16, 881), (x - 6, 861), (x + 2, 873),
        (x + 9, 866), (x + 16, 881),
    ])), CREAM)
    c.put(c.mask(lambda p: p.line([(x - 15, 886), (x + 16, 886)], 1.8)), BRASS)


def shield(c, x):
    """Draw the shield on the Bosses door."""
    c.put(c.mask(lambda p: p.poly([
        (x - 13, 859), (x + 13, 859), (x + 11, 875),
        (x, 885), (x - 11, 875),
    ])), BRASS)
    c.put(c.mask(lambda p: p.poly([
        (x - 8, 863), (x + 8, 863), (x + 6, 873),
        (x, 879), (x - 6, 873),
    ])), INK)


def gallery_doors(c, _kit):
    doorway(c, 805, "CHARACTERS", INK, (126, 155, 203))
    portraits(c, 805)
    doorway(c, 968, "BIOMES", (38, 78, 69), (137, 190, 154))
    landscape(c, 968)
    doorway(c, 1084, "BOSSES", (94, 44, 56), (204, 137, 122))
    shield(c, 1084)


TARGETS = targets({"hub_gallery_doors": Piece((752, 798, 1136, 928), gallery_doors)}, {})
