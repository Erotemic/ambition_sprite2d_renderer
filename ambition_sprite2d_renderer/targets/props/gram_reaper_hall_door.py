"""Draw the Gram Reaper entrance in the Hall of Bosses."""

from ._district_props import Piece, targets
from ._town_kit import box
from .castle_godwin import lettering

PLUM = (42, 25, 53)
STONE = (110, 87, 125)
ASH = (183, 163, 195)
LIGHT = (214, 228, 211)
GLOW = (123, 178, 153)


def entrance(c, _kit):
    c.put(c.mask(lambda p: p.arch(1661, 238, 1715, 336)), ASH)
    c.put(c.mask(lambda p: p.arch(1664, 241, 1712, 334)), STONE)
    c.put(c.mask(lambda p: p.arch(1668, 245, 1708, 332)), PLUM)
    c.put(c.mask(lambda p: p.arch(1672, 249, 1704, 319)), (59, 40, 80))
    c.put(c.mask(lambda p: p.ellipse(1688, 271, 10)), GLOW)
    c.put(c.mask(lambda p: p.ellipse(1693, 267, 8)), (59, 40, 80))
    c.put(c.mask(lambda p: p.poly([(1683, 288), (1689, 279), (1694, 289), (1689, 302)])), ASH)
    c.put(c.mask(lambda p: p.line([(1689, 302), (1689, 318)], 1.4)), ASH)
    c.put(c.mask(lambda p: p.ring(1701, 310, 2.3, 1.1)), LIGHT)
    c.put(c.mask(box(1661, 330, 1715, 336)), STONE)
    c.put(c.mask(box(1642, 208, 1734, 227)), ASH)
    c.put(c.mask(box(1644, 210, 1732, 225)), PLUM)
    lettering(c, "GRAM REAPER", 1688, 213, 8, LIGHT)


TARGETS = targets({"gram_reaper_hall_door": Piece((1638, 204, 1738, 340), entrance)}, {})
