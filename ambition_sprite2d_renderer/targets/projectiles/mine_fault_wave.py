"""Draw the low fracture that travels along the cavern floor."""
from ..props._district_props import Piece, targets
from ..props.fantasy_country_props import line, polygon


def fracture(canvas, _):
    outline = [(1, 26), (9, 25), (14, 18), (20, 22), (28, 7),
               (35, 16), (41, 10), (47, 23), (58, 27), (63, 30), (1, 30)]
    polygon(canvas, outline, (37, 71, 78))
    polygon(canvas, [(16, 25), (28, 7), (32, 18), (24, 25)], (122, 184, 163))
    polygon(canvas, [(33, 26), (41, 10), (44, 21), (40, 27)], (104, 159, 153))
    line(canvas, [(3, 27), (14, 26), (22, 28), (32, 24), (42, 27), (55, 28)], 1.8, (198, 235, 187))
    polygon(canvas, [(8, 15), (11, 12), (14, 15), (11, 17)], (129, 185, 165))
    polygon(canvas, [(49, 14), (52, 8), (55, 11), (52, 15)], (150, 204, 174))


TARGETS = targets({"mine_fault_wave": Piece((0, 0, 64, 32), fracture, px=2)}, {})
