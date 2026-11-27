"""Draw the service walks and ladder mounts in the Castle Godwin lab."""

from ._district_props import Piece, targets


def service_tower(c, _kit):
    """Match the lab walk surfaces and leave space for the ladder rungs."""
    walks = (
        (16, 96, 704), (16, 96, 1344),
        (160, 448, 1552), (576, 864, 1376), (160, 864, 1200),
        (576, 864, 1024), (160, 448, 848), (160, 864, 672),
        (160, 448, 448), (544, 864, 400),
    )
    c.put(c.mask(lambda p: (
        p.rect(145, 427, 158, 1728),
        p.rect(864, 389, 878, 1728),
        p.rect(625, 237, 641, 419),
    )), (30, 52, 50))
    c.put(c.mask(lambda p: (
        p.rect(145, 427, 148, 1728),
        p.rect(875, 389, 878, 1728),
        p.rect(638, 237, 641, 419),
    )), (83, 117, 105))
    c.put(c.mask(lambda p: [
        p.line([(left + inset, top + 16), (left + inset + 26, top + 16), (left + inset, top + 44)], 3.4)
        for left, right, top in walks for inset in range(18, right - left - 25, 114)
    ]), (27, 47, 46))
    c.put(c.mask(lambda p: [p.rect(left, top, right, top + 16) for left, right, top in walks]), (46, 72, 65))
    c.put(c.mask(lambda p: [p.rect(left, top, right, top + 2) for left, right, top in walks]), (139, 171, 146))
    c.put(c.mask(lambda p: [
        p.rect(x, top + 4, x + 2, top + 13)
        for left, right, top in walks for x in range(left + 9, right - 5, 14)
    ]), (75, 109, 94))
    c.put(c.mask(lambda p: (
        [p.rect(134, top + 5, 158, top + 10) for top in range(432, 1728, 96)],
        [p.rect(864, top + 5, 890, top + 10) for top in range(386, 1728, 96)],
        [p.rect(616, top, 640, top + 5) for top in (248, 303, 365)],
    )), (55, 83, 73))
    c.put(c.mask(lambda p: [
        p.rect(x - 4, y - 6, x + 6, y + 29)
        for x, y in ((172, 1200), (172, 672), (852, 1200), (852, 672), (556, 400))
    ]), (35, 62, 56))
    lamps = c.mask(lambda p: [
        p.ellipse(x, y - 1, 3, 2)
        for x, y in ((172, 1200), (172, 672), (852, 1200), (852, 672), (556, 400))
    ])
    c.put(lamps, (186, 235, 161))
    c.light(c.soften(lamps, 6), (127, 226, 129), 0.38)


TARGETS = targets({
    "castle_lab_service_tower": Piece((16, 216, 919, 1728), service_tower, px=1.0),
}, {})
