"""Draw the low fracture that travels along the cavern floor."""
from ..props._district_props import Piece, targets
from ..props.fantasy_country_props import line, polygon


def fracture(canvas, _):
    outline = [(1, 28), (12, 25), (16, 19), (22, 23), (29, 13), (35, 19),
               (46, 6), (51, 17), (54, 22), (62, 26), (59, 30), (11, 31)]
    polygon(canvas, outline, (26, 32, 54))
    polygon(canvas, [(11, 28), (16, 20), (22, 24), (29, 14), (35, 20),
                     (46, 7), (50, 18), (56, 25), (47, 27), (30, 26), (19, 29)], (60, 145, 151))
    polygon(canvas, [(35, 24), (46, 7), (47, 17), (43, 24)], (146, 228, 192))
    polygon(canvas, [(21, 27), (29, 14), (30, 22), (26, 26)], (125, 190, 178))
    line(canvas, [(5, 28), (17, 27), (23, 29), (33, 25), (43, 27), (51, 24), (59, 26)],
         2.1, (197, 247, 211))
    polygon(canvas, [(12, 16), (15, 12), (18, 15), (15, 18)], (141, 220, 198))
    polygon(canvas, [(36, 11), (39, 5), (42, 4), (40, 10)], (174, 242, 221))


TARGETS = targets({"mine_fault_wave": Piece((0, 0, 64, 32), fracture, px=2)}, {})
