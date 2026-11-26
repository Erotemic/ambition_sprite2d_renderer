"""The timber rampart and its east ramp in the Celtic Frontier."""

from ..characters import _history_europe_kit as colors
from ._district_props import Piece, targets
from ._town_kit import box

FLOOR = 576
OAK = colors.OAK[:3]
OAK_LIGHT = colors.OAK_LIGHT[:3]
OAK_DARK = colors.OAK_DARK[:3]
STONE = (93, 91, 82)
MOSS = (109, 124, 72)
RAMP_START = (1696, 336)
RAMP_FOOT = (2240, 512)


def post(c, x, deck):
    """Draw a post on a stone footing."""
    stone = [(x - 17, FLOOR), (x - 14, FLOOR - 13), (x + 10, FLOOR - 16), (x + 17, FLOOR)]
    c.put(c.mask(box(x - 7, deck, x + 7, FLOOR - 7)), OAK_DARK)
    c.put(c.mask(box(x - 4, deck, x - 1, FLOOR - 11)), OAK_LIGHT, 0.6)
    c.put(c.mask(lambda p: p.poly(stone)), STONE)
    c.put(c.mask(lambda p: p.line(stone[1:3], 2)), MOSS)


def deck(c, left, right, y):
    """Draw a deck and the open bays below it."""
    posts = (left + 14, (left + right) // 2, right - 14)
    for x in posts:
        post(c, x, y)
    c.put(c.mask(lambda p: [
        p.line([(start, y + 60), (end, y + 12)], 8)
        for start, end in zip(posts, posts[1:])
    ]), OAK_DARK)
    c.put(c.mask(box(left, y, right, y + 14)), OAK)
    c.put(c.mask(box(left, y, right, y + 2)), OAK_LIGHT)
    c.put(c.mask(lambda p: [
        p.line([(x, y + 4), (x + 2, y + 12)], 1.3)
        for x in range(left + 16, right - 3, 14)
    ]), OAK_DARK)
    c.put(c.mask(lambda p: [
        p.poly([(x - 4, y), (x - 4, y - 27), (x, y - 33), (x + 4, y - 27), (x + 4, y)])
        for x in range(left + 12, right - 5, 22)
    ]), OAK_DARK)
    c.put(c.mask(box(left + 6, y - 18, right - 6, y - 13)), OAK)


def east_ramp(c):
    """Draw the planks, rails, and supports of the slope."""
    start_x, start_y = RAMP_START
    end_x, end_y = RAMP_FOOT

    def height(x):
        return start_y + (end_y - start_y) * (x - start_x) / (end_x - start_x)

    posts = range(1752, end_x, 90)
    for x in posts:
        post(c, x, height(x))
    c.put(c.mask(lambda p: [
        p.line([(x, height(x) + 61), (x + 90, height(x + 90) + 10)], 8)
        for x in posts[:-1]
    ]), OAK_DARK)
    c.put(c.mask(lambda p: p.poly([
        RAMP_START, RAMP_FOOT, (end_x, end_y + 14), (start_x, start_y + 14),
    ])), OAK)
    c.put(c.mask(lambda p: p.line([RAMP_START, RAMP_FOOT], 2)), OAK_LIGHT)
    c.put(c.mask(lambda p: [
        p.line([(x, height(x) + 3), (x + 3, height(x) + 12)], 1.5)
        for x in range(start_x + 16, end_x, 14)
    ]), OAK_DARK)
    c.put(c.mask(lambda p: [
        p.line([(x, height(x)), (x, height(x) - 23)], 4)
        for x in range(start_x + 12, end_x, 25)
    ]), OAK_DARK)
    c.put(c.mask(lambda p: p.line([(start_x, start_y - 22), (end_x, end_y - 22)], 4)), OAK)


def hillfort(c, _kit):
    """Draw the stepped west side and the east ramp."""
    for left, right, y in ((1072, 1280, 496), (1296, 1504, 416), (1520, 1712, 336)):
        deck(c, left, right, y)
    east_ramp(c)
    end_x, end_y = RAMP_FOOT
    deck(c, end_x, 2320, end_y)


TARGETS = targets({"history_hillfort_walk": Piece((1072, 302, 2324, FLOOR), hillfort)}, {})
