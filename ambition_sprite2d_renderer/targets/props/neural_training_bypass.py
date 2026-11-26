"""The maintenance tunnel below the Weights' training deck."""

from ._district_props import Piece, targets
from ._town_kit import box
from .castle_godwin import lettering
from .neural_props import PANEL, PANEL_LIGHT, TRACE, NODE, glow_bulb

WALL = (18, 23, 48)
RIB = (41, 49, 91)
AMBER = (248, 189, 108)


def entrance(c, x, side):
    """Mark the ladder opening with a light and a down arrow."""
    sign = x + side * 38
    c.put(c.mask(box(sign - 52, 963, sign + 52, 986)), RIB)
    c.put(c.mask(box(sign - 50, 965, sign + 50, 984)), WALL)
    c.put(c.mask(box(sign - 50, 982, sign + 50, 984)), AMBER)
    lettering(c, "BYPASS", sign, 969, 10, NODE)
    c.put(c.mask(lambda p: p.poly([
        (x - 2, 993), (x + 2, 993), (x + 2, 1003), (x + 8, 1003),
        (x, 1012), (x - 8, 1003), (x - 2, 1003),
    ])), AMBER)
    c.put(c.mask(lambda p: [p.rect(x + offset, 1016, x + offset + 6, 1119) for offset in (-32, 26)]), PANEL_LIGHT)
    for offset in (-27, 27):
        glow_bulb(c, x + offset, 1013, 3, AMBER, 0.45)


def bypass(c, _kit):
    c.put(c.mask(lambda p: p.poly([
        (960, 1015), (1024, 1015), (1024, 1040), (1408, 1040),
        (1408, 1015), (1472, 1015), (1472, 1120), (960, 1120),
    ])), WALL)
    c.put(c.mask(box(966, 1111, 1466, 1120)), PANEL)
    c.put(c.mask(lambda p: [p.rect(x, 1044, x + 12, 1111) for x in (1044, 1132, 1220, 1308, 1396)]), RIB)
    trace = [(1019, 1076), (1042, 1054), (1144, 1054), (1166, 1072),
             (1272, 1072), (1292, 1054), (1393, 1054), (1414, 1076)]
    c.put(c.mask(lambda p: p.line(trace, 2)), TRACE, 0.65)
    for x, y in (trace[1], trace[3], trace[5], trace[7]):
        glow_bulb(c, x, y, 3.5, NODE, 0.5)
    c.put(c.mask(lambda p: [
        p.rect(x, 1094, x + 24, 1100) for x in (1076, 1164, 1252, 1340)
    ]), PANEL_LIGHT)
    entrance(c, 992, -1)
    entrance(c, 1440, 1)


TARGETS = targets({"neural_training_bypass": Piece((866, 934, 1544, 1120), bypass)}, {})
