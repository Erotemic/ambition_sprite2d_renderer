"""The scenes of the History dimension: the Atlantic world.

The History dimension is a grid. East is later, and each floor is a region
of the world. These rooms show the peoples and the cities round the
Atlantic in the centuries when its coasts came into contact: their courts,
their crafts and their trade. They use the same sepia of an old textbook and
the same rules as `history_eras.py` and `history_origins.py`. The people of
these places show skill, invention and a long history of their own; nothing
here is a joke on them.

- ``history_benin`` (Benin City, the capital of the kingdom of Benin, in
  the 1600s). A humid morning. The long, wide, straight main street of the
  city goes away to the edge of the rainforest. Walls of red laterite earth
  with horizontal ridges are on its two sides. On the right is the palace
  compound of the Oba: steep roofs of wooden shingles and tall pointed
  turrets, each with a brass bird with spread wings on its point. On the
  left, thin smoke goes up from the furnaces of the guild of brass casters.
  Oil palms and plantains stand at the sides, on a bank of red earth.
- ``history_saint_domingue`` (the north plain of Saint-Domingue, 1791).
  A late afternoon. Behind the plain, range after range of steep green
  mornes go back into the haze (Ayiti, the Taino name that Haiti took back
  in 1804, means "land of mountains"). The sea is a strip at the left,
  under the low sun. On the plain are blocks of cane fields, a plantation
  house at the end of an alley of royal palms, and a sugar works with a
  tall chimney and a round cattle mill. Far off, a few thin columns of
  smoke go up from the plain: in August 1791 the enslaved people of the
  north rose, and the cane fields burned. The smoke is far and quiet.
  Royal palms and banana plants stand at the sides, on a bank of red earth.

The bright detail is far off or at the edges, and the middle of each near
layer is calm, so the play in front of it reads. The things that drift in the
air are the room's motes (`terrain/motes.py`), not part of these pictures.
"""

from __future__ import annotations

import numpy as np

from .artkit import Art, Pen, mix, scale, smoothstep
from .history_americas_pacific import _canopy, _fronds, _royal_palm
from .history_eras import REST_BOTTOM, _air, _at, _heaps, _plume, _sun, _textbook
from .history_origins import _arch, _banana, _cane, _land, _leaf
from .parts import HORIZON, fog, haze, shafts, solid

BENIN = {
    "top": (92, 126, 146),
    "mid": (180, 192, 180),
    "low": (240, 226, 194),
    "glow": (255, 232, 186),
    "sun": (255, 246, 222),
    "cloud": (244, 240, 230),
    "cloud_shadow": (172, 178, 172),
    "forest": (54, 86, 56),
    "forest_light": (104, 136, 78),
    "street": (214, 168, 118),
    "street_light": (240, 204, 156),
    "laterite": (168, 74, 46),
    "laterite_light": (206, 112, 72),
    "laterite_dark": (112, 46, 30),
    "shingle": (96, 64, 44),
    "shingle_light": (160, 116, 80),
    "brass": (226, 176, 72),
    "brass_light": (255, 226, 140),
    "cloth": (246, 242, 230),
    "smoke": (214, 210, 204),
    "far": (176, 172, 160),
    "near": (44, 30, 22),
    "near_light": (150, 84, 52),
    "palm": (40, 62, 36),
    "palm_light": (110, 140, 70),
}

#: The point where the main street goes out of sight, at the edge of the
#: forest.
VANISH = (0.44, HORIZON - 0.004)
#: The street at the foot of the far panel: its half width, and how far down.
STREET_FOOT_V = 0.80
STREET_HALF = 0.20
#: The height of the walls of the street at the foot of the panel: the wall
#: of the town on the left, and the higher wall of the palace on the right.
WALL_H = 0.09
PALACE_H = 0.12


def _street_point(side: float, t: float, lift: float = 0.0, out: float = 0.0) -> tuple[float, float]:
    """A point on the edge of the main street in perspective. `t` is 0 at
    the vanishing point and 1 at the foot of the panel; `side` is -1 for the
    left and 1 for the right. `lift` raises the point (a height at the foot
    of the panel), and `out` moves it away from the street (a width at the
    foot of the panel). The two shrink to the vanishing point."""
    u = VANISH[0] + side * (STREET_HALF + out) * t
    v = VANISH[1] + (STREET_FOOT_V - VANISH[1]) * t - lift * t
    return (u, v)


def _benin_bird(pen: Pen, u: float, v: float, s: float) -> None:
    """A brass bird that stands on the point of a turret with its wings
    spread: a round body, a long beak and two wide wings that lift."""
    pen.ellipse(u, v - s * 0.35, s * 0.30, s * 0.26)
    pen.poly([(u + s * 0.22, v - s * 0.48), (u + s * 0.80, v - s * 0.36), (u + s * 0.22, v - s * 0.30)])
    for side in (-1.0, 1.0):
        pen.poly([(u, v - s * 0.42), (u + side * s * 0.55, v - s * 0.95), (u + side * s * 1.10, v - s * 1.05), (u + side * s * 0.70, v - s * 0.55),
                  (u + side * s * 0.25, v - s * 0.22)])
    pen.poly([(u - s * 0.25, v - s * 0.30), (u - s * 0.60, v - s * 0.10), (u - s * 0.20, v - s * 0.15)])
    pen.line([(u, v - s * 0.10), (u, v)], s * 0.12)


def _turret(pen: Pen, shade: Pen, rings: Pen, bird: Pen, u: float, v: float, w: float, h: float) -> None:
    """A tall pointed turret of the palace: a steep cone of wooden shingles
    that curves in a little near its point, rings of shingle courses, and a
    brass bird on the point."""
    pts = []
    for k in range(11):
        t = k / 10.0
        half = w * (1.0 - t) ** 1.25
        pts.append((t, half))
    left = [(u - half, v - h * t) for t, half in pts]
    right = [(u + half, v - h * t) for t, half in reversed(pts)]
    pen.poly(left + right)
    shade.poly([(u + w * 0.15, v)] + [(u + half, v - h * t) for t, half in pts])
    for k in range(1, 7):
        t = k / 7.0
        half = w * (1.0 - t) ** 1.25
        rings.line([(u - half, v - h * t + h * 0.012), (u + half, v - h * t)], max(0.0008, w * 0.06))
    _benin_bird(bird, u, v - h, w * 0.75)


def _roof_run(pen: Pen, gable: Pen, side: float, t0: float, t1: float, base: float, rise: float, out: float, reach: float) -> None:
    """A long steep roof of wooden shingles on a building along the street,
    from depth `t0` to depth `t1`: the slope that looks onto the street, from
    its eaves (`base` high, `out` from the street) up to its ridge (`rise`
    higher and `reach` further out), and the gable at its near end."""
    eave0, eave1 = _street_point(side, t0, base, out), _street_point(side, t1, base, out)
    ridge0, ridge1 = _street_point(side, t0, base + rise, out + reach), _street_point(side, t1, base + rise, out + reach)
    pen.poly([eave0, eave1, ridge1, ridge0])
    back = _street_point(side, t1, base, out + 2.0 * reach)
    pen.poly([eave1, ridge1, back])
    gable.poly([eave1, ridge1, back])


def _oil_palm(trunk: Pen, crown: Pen, nuts: Pen, rng, u: float, v: float, h: float, lean: float) -> None:
    """An oil palm: a thick rough trunk with the stubs of old fronds on it, a
    dense head of long fronds, and a bunch of red fruit under them."""
    w = h * 0.045
    pts = [(u + lean * t**1.3, v + 0.01 - (h + 0.01) * t) for t in np.linspace(0.0, 1.0, 12)]
    trunk.line(pts, w)
    for k in range(3, 11):
        x, y = pts[k]
        for side in (-1.0, 1.0):
            trunk.line([(x, y), (x + side * w * 0.75, y - w * 0.7)], w * 0.28)
    top = pts[-1]
    _fronds(crown, rng, top, h, 18, 0.40, 0.30, w * 0.40, 0.050)
    for du in (-0.6, 0.0, 0.6):
        nuts.ellipse(top[0] + du * w * 0.9, top[1] + h * 0.045, w * 0.55, w * 0.50)


def history_benin(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = BENIN
    sun_at = (0.30, 0.34)
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.85)), (0.24, p["top"]), (0.44, p["mid"]), (HORIZON - 0.02, p["low"]),
                                 (HORIZON + 0.05, mix(p["low"], p["forest"], 0.5)), (1.0, p["forest"])]))
        # The sun is pale in the wet air of the morning.
        _sun(a, layer, *sun_at, 0.028, p["sun"], p["glow"], 0.65)
        a.put(layer, shafts(a, "benin sky shafts", 4, 0.18, 0.28, 0.75, 0.04) * (a.v > sun_at[1]), p["glow"], 0.10)
        _heaps(a, layer, "benin heaps", ((0.66, 0.36, 0.09, 0.08), (0.92, 0.32, 0.06, 0.05), (0.12, 0.40, 0.05, 0.04)), p["cloud"], p["cloud_shadow"], 0.75)
        # The edge of the rainforest far off: a line of crowns with tall
        # trees over it, blue in the haze.
        trees, tree_pen = a.drawing()
        rng = a.rand("benin far forest")
        _, line = a.ridge("benin far forest line", HORIZON - 0.010, 0.004, cells=12.0, octaves=2)
        _canopy(tree_pen, rng, line, 0.0, 1.0, 0.012, 0.006, 0.014, 160)
        for _ in range(9):
            u = rng.uniform(0.02, 0.98)
            top = _at(line, u) - rng.uniform(0.03, 0.05)
            tree_pen.line([(u, _at(line, u)), (u, top)], 0.0016)
            tree_pen.ellipse(u, top, rng.uniform(0.012, 0.020), rng.uniform(0.005, 0.008))
        a.tint(layer, a.mask_of(trees, blur=0.6), mix(p["forest"], p["mid"], 0.60), 0.60)
        a.tint(layer, a.band(HORIZON - 0.02, 0.10, 1.4), p["low"], 0.30)
        _textbook(a, layer, 0.08)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far benin")
        forest, forest_pen = a.drawing()
        yards, yard_pen = a.drawing()
        street, street_pen = a.drawing()
        faces, face_pen = a.drawing()
        caps, cap_pen = a.drawing()
        roofs, roof_pen = a.drawing()
        roof_shade, roof_shade_pen = a.drawing()
        gables, gable_pen = a.drawing()
        rings, ring_pen = a.drawing()
        birds, bird_pen = a.drawing()
        people, people_pen = a.drawing()
        heads, head_pen = a.drawing()
        # The forest at the end of the street and at the two sides.
        _, line = a.ridge("benin forest line", HORIZON + 0.002, 0.004, cells=6.0, octaves=3)
        _canopy(forest_pen, rng, line, 0.0, 1.0, 0.014, 0.008, 0.016, 320)
        _canopy(forest_pen, rng, line, 0.0, 0.14, 0.05, 0.016, 0.030, 30)
        _canopy(forest_pen, rng, line, 0.88, 1.0, 0.05, 0.016, 0.030, 30)
        ground = smoothstep(HORIZON - 0.002, HORIZON + 0.004, a.v)
        # The main street: wide and straight, and it goes to the forest.
        street_pen.poly([VANISH, _street_point(1.0, 6.0), _street_point(-1.0, 6.0)])
        # The roofs of the compounds behind the two walls, from far to near;
        # on the right, the long roofs of the palace and its turrets.
        t = 0.05
        while t < 4.0:
            dt = 0.04 + 0.12 * t
            _roof_run(roof_pen, gable_pen, -1.0, t, t + dt * 0.86, WALL_H * 0.85, rng.uniform(0.06, 0.09), 0.01 + 0.02 * rng.random(), 0.035)
            t += dt
        for t0, t1 in ((0.03, 0.28), (0.30, 0.62), (0.64, 1.10), (1.12, 6.0)):
            _roof_run(roof_pen, gable_pen, 1.0, t0, t1, PALACE_H * 0.9, 0.075, 0.012, 0.05)
        for t, h in ((0.24, 0.17), (0.50, 0.21), (0.84, 0.25)):
            u, v = _street_point(1.0, t, PALACE_H * 0.9 + 0.075, 0.062)
            _turret(roof_pen, roof_shade_pen, ring_pen, bird_pen, u, v, 0.020 * t + 0.004, h * t + 0.02)
        # The yards and the land beyond the walls.
        for side, height in ((-1.0, WALL_H), (1.0, PALACE_H)):
            yard_pen.poly([VANISH, _street_point(side, 6.0, height), _street_point(side, 6.0, height, 1.0)])
        # The two walls of red earth along the street: the face that looks
        # onto the street, and the top of the wall.
        for side, height in ((-1.0, WALL_H), (1.0, PALACE_H)):
            face_pen.poly([VANISH, _street_point(side, 6.0), _street_point(side, 6.0, height)])
            cap_pen.poly([VANISH, _street_point(side, 6.0, height), _street_point(side, 6.0, height + 0.006, 0.014)])
        # People on the street, in white cloth, small with the distance.
        for k in range(10):
            t = rng.uniform(0.18, 0.95)
            u, v = _street_point(rng.uniform(-0.8, 0.8), t)
            s = 0.026 * t
            people_pen.poly([(u - s * 0.18, v), (u + s * 0.18, v), (u + s * 0.14, v - s * 0.75), (u - s * 0.14, v - s * 0.75)])
            head_pen.ellipse(u, v - s * 0.88, s * 0.11, s * 0.13)
        street_mask = a.mask_of(street) * ground
        face_mask = a.mask_of(faces)
        cap_mask = np.clip(a.mask_of(caps) - face_mask, 0.0, 1.0)
        wall_mask = np.maximum(face_mask, cap_mask)
        roof_mask = np.clip(a.mask_of(roofs) - wall_mask, 0.0, 1.0)
        forest_mask = a.mask_of(forest)
        mask = np.maximum.reduce([ground, forest_mask, roof_mask, wall_mask, a.mask_of(birds)])
        layer = a.blank()
        # The forest, and the yards beyond the walls: red earth and green.
        a.put(layer, mask, mix(p["forest"], p["far"], 0.18))
        a.light(layer, forest_mask * a.rim(forest_mask, -0.002, 0.004, 0.5), p["forest_light"], 0.45)
        yard_mask = a.mask_of(yards) * ground
        patches = smoothstep(0.45, 0.60, a.noise("benin yards", cells=18.0, octaves=3))
        a.put(layer, yard_mask * patches, mix(p["laterite"], p["far"], 0.40), 0.5)
        # The street: swept, sun-baked earth, paler than the walls, with the
        # lines of wheel-less feet and carts along it to the far end.
        a.put(layer, street_mask, a.ramp([(0.0, mix(p["street"], p["far"], 0.40)), (HORIZON, mix(p["street"], p["far"], 0.40)),
                                          (STREET_FOOT_V, p["street"]), (1.0, p["street"])]))
        du, dv = a.u - VANISH[0], a.v - VANISH[1]
        along = du / np.maximum(dv, 1e-3)
        ruts = np.clip(1.0 - np.abs(((along * 9.0) % 1.0) - 0.5) / 0.06, 0.0, 1.0)
        a.shade(layer, street_mask * ruts * smoothstep(0.004, 0.04, dv), 0.08)
        a.light(layer, street_mask * smoothstep(0.55, 0.75, a.noise("benin street light", cells=20.0, octaves=2)), p["street_light"], 0.25)
        # The walls: red laterite in horizontal ridges. The left face looks
        # away from the sun and is in shade; the right face is lit.
        a.put(layer, face_mask, mix(p["laterite"], p["far"], 0.08))
        a.shade(layer, face_mask * (a.u < VANISH[0]), 0.22)
        slope = dv / np.maximum(np.abs(du), 1e-4)
        ridges = np.clip(1.0 - np.abs(((slope * 7.0) % 1.0) - 0.5) / 0.10, 0.0, 1.0)
        a.shade(layer, face_mask * ridges * smoothstep(0.01, 0.05, np.abs(du)), 0.35)
        lips = np.clip(1.0 - np.abs(((slope * 7.0 + 0.3) % 1.0) - 0.5) / 0.08, 0.0, 1.0)
        a.light(layer, face_mask * lips * smoothstep(0.01, 0.05, np.abs(du)), p["laterite_light"], 0.30)
        a.put(layer, cap_mask, mix(p["laterite_dark"], p["far"], 0.10))
        # The roofs of shingles, and the courses of shingles on the turrets.
        a.put(layer, roof_mask, mix(p["shingle"], p["far"], 0.04))
        shingle_rows = np.clip(1.0 - np.abs(((slope * 40.0) % 1.0) - 0.5) / 0.14, 0.0, 1.0)
        a.shade(layer, roof_mask * shingle_rows * smoothstep(0.01, 0.04, np.abs(du)), 0.20)
        a.shade(layer, a.mask_of(roof_shade) * roof_mask, 0.32)
        a.light(layer, roof_mask * a.rim(roof_mask, 0.002, 0.003, 0.4), p["shingle_light"], 0.50)
        a.shade(layer, a.mask_of(rings) * roof_mask, 0.30)
        # The gable at the near end of each roof is a wall of red earth under
        # the edges of the shingles.
        gable_mask = a.mask_of(gables) * roof_mask
        a.put(layer, gable_mask * (1.0 - a.rim(gable_mask, 0.0, 0.004, 0.0)), mix(p["laterite"], p["far"], 0.15))
        a.shade(layer, gable_mask * (a.u < VANISH[0]), 0.15)
        # The brass birds on the turrets catch the morning sun.
        bird_mask = a.mask_of(birds)
        a.put(layer, bird_mask, p["brass"])
        a.glow(layer, a.blur(bird_mask, 3.0), p["brass_light"], 0.45)
        # The people in white cloth.
        a.put(layer, a.mask_of(people) * street_mask, p["cloth"])
        a.put(layer, a.mask_of(heads) * ground, mix(p["laterite_dark"], p["near"], 0.40))
        # Thin smoke from the furnaces of the casters' guild, behind the
        # roofs on the left.
        for k, (t, out) in enumerate(((0.45, 0.07), (0.72, 0.12), (0.26, 0.05))):
            base = _street_point(-1.0, t, WALL_H * 1.4, out)
            smoke = _plume(a, ("benin smoke", k), base[0], base[1], 0.20, 0.07, 0.009)
            a.put(layer, smoke, p["smoke"], 0.60)
            mask = np.maximum(mask, smoke * 0.60)
        # The damp air of the morning: thick at the far end of the street and
        # thinner nearer, so the near walls keep their colour.
        a.tint(layer, fog(a, "benin street haze", HORIZON - 0.004, 0.012, 3.0), p["low"], 0.35)
        a.tint(layer, smoothstep(0.70, HORIZON, a.v) * ground, p["low"], 0.30)
        haze(a, layer, p["low"], 0.06, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near benin")
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        nuts, nut_pen = a.drawing()
        stems, stem_pen = a.drawing()
        leaves, leaf_pen = a.drawing()
        bank, bank_pen = a.drawing()
        ground, line = a.ridge("near benin", 0.70, 0.006, cells=4.0, octaves=3)
        # A low bank of red earth along the foot, higher at the two sides.
        pts = [(u, _at(line, u) - 0.05 * smoothstep(0.30, 0.02, u) - 0.04 * smoothstep(0.72, 0.98, u)) for u in np.linspace(0.0, 1.0, 60)]
        bank_pen.poly([(0.0, 1.0)] + pts + [(1.0, 1.0)])
        # Oil palms and plantains at the two sides; the middle stays calm.
        _oil_palm(trunk_pen, crown_pen, nut_pen, rng, 0.08, 0.66, 0.30, 0.02)
        _oil_palm(trunk_pen, crown_pen, nut_pen, rng, 0.92, 0.68, 0.27, -0.03)
        _banana(stem_pen, leaf_pen, rng, 0.17, 0.665, 0.15)
        _banana(stem_pen, leaf_pen, rng, 0.83, 0.685, 0.14)
        _banana(stem_pen, leaf_pen, rng, 0.02, 0.66, 0.13)
        bank_mask = a.mask_of(bank)
        plants = np.maximum.reduce([a.mask_of(trunks), a.mask_of(crowns), a.mask_of(stems), a.mask_of(leaves)])
        mask = np.maximum.reduce([ground, bank_mask, plants, a.mask_of(nuts)])
        layer = a.blank()
        a.put(layer, mask, mix(p["palm"], p["near"], 0.35))
        a.put(layer, a.mask_of(crowns), mix(p["palm_light"], p["near"], 0.55))
        a.put(layer, a.mask_of(leaves), mix(p["palm_light"], p["near"], 0.40))
        a.put(layer, a.mask_of(trunks), mix((110, 84, 60), p["near"], 0.55))
        a.put(layer, a.mask_of(nuts), mix((196, 70, 40), p["near"], 0.35))
        # The bank of red earth, in ridges, lit along its top.
        earth = a.ramp([(0.0, mix(p["near_light"], p["near"], 0.25)), (0.62, mix(p["near_light"], p["near"], 0.25)), (0.80, mix(p["near_light"], p["near"], 0.70)), (1.0, p["near"])])
        a.put(layer, np.maximum(bank_mask, ground), earth)
        ridges = np.clip(1.0 - np.abs(((a.v * 110.0 + 0.6 * np.sin(a.u * 9.0)) % 1.0) - 0.5) / 0.14, 0.0, 1.0)
        a.shade(layer, np.maximum(bank_mask, ground) * ridges, 0.28)
        a.light(layer, a.rim(np.maximum(bank_mask, ground), 0.0, 0.003, 0.4) * np.maximum(bank_mask, ground), p["glow"], 0.40)
        a.light(layer, a.rim(plants, 0.003, 0.002, 0.4) * plants, p["glow"], 0.30)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.22)
        haze(a, layer, p["low"], 0.08, None)
        return layer
    layer = _air(a, p, "benin humid morning", p["low"], 0.30, p["near"], 0.22)
    a.put(layer, shafts(a, "benin shafts", 4, 0.16, 0.0, 0.85, 0.05), p["glow"], 0.08)
    return layer


def benin_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """The tips of oil palm fronds that hang into the top of the view at two
    places, and a clump of grass that stands from below at one place."""
    del layer_lights
    rng = art_.rand("benin foreground")
    for k in range(2):
        u0 = (k + rng.uniform(0.15, 0.85)) / 2.0
        for j in range(2):
            start = (u0 + (j - 0.5) * 0.05, 0.0)
            end = (start[0] + (0.07 if j else -0.07) + rng.uniform(-0.02, 0.02), 0.386 - rng.uniform(0.0, 0.01))
            ctrl = ((start[0] + end[0]) * 0.5 + (0.03 if j else -0.03), 0.22)
            rib = _arch(start, ctrl, end, 20)
            pen.line(rib, 0.0026)
            for i, (x, y) in enumerate(rib[1:], 1):
                t = i / 20.0
                side = 0.030 * (1.0 - t * 0.6)
                if y + side > 0.392:
                    side = max(0.0, 0.392 - y)
                pen.line([(x, y), (x + side * 0.30, y + side)], 0.0014)
                pen.line([(x, y), (x - side * 0.30, y + side)], 0.0014)
    u0 = rng.uniform(0.35, 0.65)
    for _ in range(8):
        u = u0 + rng.uniform(-0.02, 0.02)
        top = REST_BOTTOM - rng.uniform(-0.004, 0.012)
        bend = rng.uniform(-0.02, 0.02)
        pen.line(_arch((u, 1.0), (u + bend * 0.2, top + 0.05), (u + bend, top), 8), 0.0018)


# ---------------------------------------------------------------------------
# Saint-Domingue: the north plain in 1791, under the mornes
# ---------------------------------------------------------------------------


SAINT_DOMINGUE = {
    "top": (98, 128, 160),
    "mid": (212, 196, 168),
    "low": (250, 220, 168),
    "glow": (255, 212, 148),
    "sun": (255, 240, 206),
    "cloud": (250, 236, 214),
    "cloud_shadow": (200, 170, 156),
    "sea": (64, 122, 152),
    "sea_light": (236, 222, 184),
    "morne": (30, 88, 58),
    "morne_light": (120, 156, 78),
    "cane": (112, 156, 62),
    "cane_light": (168, 192, 92),
    "cane_young": (142, 176, 74),
    "earth": (154, 74, 44),
    "earth_light": (198, 112, 68),
    "wall": (238, 230, 210),
    "roof": (150, 72, 50),
    "stone": (184, 166, 134),
    "brick": (160, 82, 56),
    "thatch": (176, 146, 92),
    "trunk": (196, 186, 166),
    "smoke": (150, 140, 134),
    "far": (196, 186, 166),
    "near": (46, 30, 22),
    "near_light": (156, 82, 50),
    "palm": (40, 66, 38),
    "palm_light": (112, 148, 70),
}

#: The coast: the plain ends at this `u` on the horizon, and the sea is to
#: the left of it.
COAST_U = 0.28


def _house(walls: Pen, roof: Pen, holes: Pen, u: float, v: float, w: float, h: float) -> None:
    """A plantation house of the plain: a long low house of one floor on a
    base, with a gallery of posts along its front and a high hipped roof of
    tiles."""
    walls.rect(u - w, v - h, u + w, v)
    roof.poly([(u - w * 1.12, v - h * 0.92), (u - w * 0.60, v - h * 2.3), (u + w * 0.60, v - h * 2.3), (u + w * 1.12, v - h * 0.92)])
    for k in range(7):
        x = u - w * 0.80 + k * w * 1.6 / 6.0
        holes.rect(x - w * 0.06, v - h * 0.72, x + w * 0.06, v - h * 0.08)


def _sugar_works(walls: Pen, roof: Pen, brick: Pen, mill: Pen, u: float, v: float, s: float) -> None:
    """A sugar works of a plantation: a long low boiling house of stone with
    a tile roof, a tall square chimney of brick at its end, and a round
    cattle mill beside it: a cone roof on posts over the rollers."""
    walls.rect(u - s, v - s * 0.22, u + s, v)
    roof.poly([(u - s * 1.04, v - s * 0.20), (u - s * 0.90, v - s * 0.42), (u + s * 0.90, v - s * 0.42), (u + s * 1.04, v - s * 0.20)])
    brick.poly([(u + s * 0.70, v - s * 0.30), (u + s * 0.84, v - s * 0.30), (u + s * 0.82, v - s * 1.30), (u + s * 0.72, v - s * 1.30)])
    brick.rect(u + s * 0.70, v - s * 1.36, u + s * 0.84, v - s * 1.28)
    mu = u - s * 1.42
    mill.poly([(mu - s * 0.40, v - s * 0.26), (mu, v - s * 0.56), (mu + s * 0.40, v - s * 0.26)])
    for k in (-0.32, 0.0, 0.32):
        mill.line([(mu + s * k, v - s * 0.27), (mu + s * k, v)], s * 0.035)


def _cabins(walls: Pen, roof: Pen, u: float, v: float, s: float, count: int) -> None:
    """A row of small cabins with thatched roofs: the quarters where the
    enslaved people of the plantation lived."""
    for k in range(count):
        x = u + k * s * 2.6
        walls.rect(x - s, v - s * 0.7, x + s, v)
        roof.poly([(x - s * 1.25, v - s * 0.62), (x, v - s * 1.6), (x + s * 1.25, v - s * 0.62)])


def history_saint_domingue(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = SAINT_DOMINGUE
    sun_at = (0.13, 0.40)
    sea_v = HORIZON - 0.002
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.88)), (0.20, p["top"]), (0.42, p["mid"]), (sea_v, p["low"]),
                                 (sea_v + 0.003, p["sea"]), (HORIZON + 0.06, mix(p["sea"], p["low"], 0.25)), (1.0, p["sea"])]))
        _sun(a, layer, *sun_at, 0.026, p["sun"], p["glow"], 0.70)
        _heaps(a, layer, "saint domingue heaps", ((0.42, 0.30, 0.07, 0.06), (0.62, 0.24, 0.09, 0.07), (0.88, 0.33, 0.06, 0.05)), p["cloud"],
               p["cloud_shadow"], 0.80)
        # The sea at the left: a road of light under the low sun.
        glints = smoothstep(0.60, 0.80, a.noise("saint domingue glints", cells=70.0, octaves=2, stretch=7.0))
        a.light(layer, (a.v > sea_v + 0.002) * glints * a.spot(sun_at[0], HORIZON + 0.03, 0.26, 1.0, squash=0.9), p["sea_light"], 0.60)
        a.light(layer, a.band(sea_v + 0.003, 0.004, 1.5) * smoothstep(0.40, 0.05, a.u), p["sea_light"], 0.50)
        # The mornes: range after range of steep green mountains that go back
        # into the haze. Each nearer range is darker and greener. At the left
        # they come down to the sea. The slopes that face the low sun at the
        # left catch its light.
        ranges = ((HORIZON - 0.150, 0.050, 4.0, 0.70, 0.66), (HORIZON - 0.115, 0.045, 5.0, 0.65, 0.50), (HORIZON - 0.080, 0.040, 6.0, 0.60, 0.33),
                  (HORIZON - 0.048, 0.034, 7.0, 0.55, 0.14))
        for k, (base, amp, cells, sharp, pale) in enumerate(ranges):
            _, line = a.ridge(("saint domingue morne", k), base, amp, cells=cells, octaves=5, sharp=sharp)
            line = line + (sea_v + 0.004 - line) * smoothstep(0.34 - 0.03 * k, 0.10 + 0.02 * k, a.u[0])
            # The foot of each range: the sea at the left, and behind the
            # plain (which covers it) at the right.
            foot = sea_v + 0.004 + 0.03 * smoothstep(COAST_U - 0.06, COAST_U + 0.06, a.u)
            mask = _land(a, line) * smoothstep(foot + 0.002, foot - 0.001, a.v)
            colour = mix(p["morne"], p["low"], pale)
            a.put(layer, mask, a.ramp([(0.0, colour), (base, colour), (HORIZON, mix(colour, p["low"], 0.45)), (1.0, mix(colour, p["low"], 0.45))]))
            lit = a.rim(mask, 0.010, 0.004, 2.0) * mask
            a.light(layer, lit, mix(p["morne_light"], p["glow"], 0.35), 0.55 * (1.0 - pale * 0.6))
            # Mist in the valley at the foot of each range.
            a.tint(layer, mask * fog(a, ("saint domingue valley mist", k), line.max() - 0.004, 0.020, 3.0), p["low"], 0.55)
        _textbook(a, layer, 0.08)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far saint domingue")
        # The nearest morne rises steep from the plain at the right; the
        # plain runs from it to the coast at the left.
        _, hill = a.ridge("saint domingue foothill", HORIZON - 0.06, 0.030, cells=5.0, octaves=5, sharp=0.6)
        _, plain = a.ridge("saint domingue plain", HORIZON + 0.010, 0.002, cells=4.0, octaves=2)
        rise = smoothstep(0.66, 0.92, a.u[0])
        top = plain + (hill - plain) * rise
        coast = COAST_U - (a.v - HORIZON) * 1.5
        land = _land(a, top) * smoothstep(coast - 0.01, coast + 0.01, a.u)
        hill_mask = _land(a, top) * smoothstep(0.62, 0.70, a.u) * (a.v < plain[None, :] + 0.02)
        forest, forest_pen = a.drawing()
        fields = {key: a.drawing() for key in ("cane", "cane_light", "cane_young", "earth")}
        roads, road_pen = a.drawing()
        trees, tree_pen = a.drawing()
        walls, wall_pen = a.drawing()
        roofs, roof_pen = a.drawing()
        holes, hole_pen = a.drawing()
        stone, stone_pen = a.drawing()
        bricks, brick_pen = a.drawing()
        mill, mill_pen = a.drawing()
        thatch, thatch_pen = a.drawing()
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        # The forest on the foothill: crowns of trees in a dense cover.
        _canopy(forest_pen, rng, top, 0.62, 1.0, 0.010, 0.010, 0.018, 160)
        # The cane fields: rows of blocks that get deeper toward the eye,
        # with roads of red earth between them. Most are cane, tall or
        # young; a few are bare red earth, ready to plant.
        v, gap = HORIZON + 0.014, 0.006
        while v < 1.0:
            x = rng.uniform(-0.08, 0.0)
            while x < 1.0:
                length = rng.uniform(0.05, 0.16) * (1.0 + (v - HORIZON) * 3.0)
                key = rng.choices(("cane", "cane_light", "cane_young", "earth"), (5, 3, 3, 1))[0]
                fields[key][1].rect(x, v, x + length, v + gap)
                road_pen.line([(x + length, v), (x + length, v + gap)], 0.0008 + (v - HORIZON) * 0.006)
                x += length
            road_pen.line([(0.0, v), (1.0, v)], 0.0008 + (v - HORIZON) * 0.006)
            # A hedge of trees along some of the roads.
            if rng.random() < 0.35:
                for _ in range(int(16 + (v - HORIZON) * 60)):
                    r = min(0.008, gap * rng.uniform(0.25, 0.45))
                    tree_pen.ellipse(rng.uniform(0.0, 1.0), v - r * 0.5, r * 1.2, r)
            v += gap
            gap *= 1.30
        # The plantation: the house at the end of its alley of royal palms,
        # the sugar works and its mill, and the rows of cabins.
        house_u, house_v = 0.50, HORIZON + 0.026
        _house(wall_pen, roof_pen, hole_pen, house_u, house_v, 0.026, 0.008)
        for k in range(4):
            t = k / 3.0
            v_k = house_v + 0.004 + t * 0.022
            for side in (-1.0, 1.0):
                u_k = house_u + side * (0.010 + t * 0.012)
                _royal_palm(trunk_pen, crown_pen, rng, u_k, v_k, 0.020 + t * 0.014, 0.0)
        _sugar_works(stone_pen, roof_pen, brick_pen, mill_pen, 0.34, HORIZON + 0.030, 0.040)
        _cabins(wall_pen, thatch_pen, 0.385, HORIZON + 0.046, 0.0065, 5)
        for u in (0.26, 0.58, 0.63, 0.44):
            tree_pen.ellipse(u, HORIZON + 0.020, 0.012, 0.008)
        # Far smoke over the plain, thin and quiet: the fields that burned in
        # August 1791.
        smoke = np.zeros((a.n, a.n), dtype=np.float32)
        for k, (u, rise_v, drift) in enumerate(((0.72, 0.16, 0.035), (0.81, 0.12, 0.030), (0.24, 0.10, 0.025))):
            smoke = np.maximum(smoke, _plume(a, ("saint domingue smoke", k), u, HORIZON + 0.012, rise_v, drift, 0.008))
        ground = land * (a.v > plain[None, :] - 0.002)
        field_masks = {key: a.mask_of(img) * ground for key, (img, _) in fields.items()}
        building = np.maximum.reduce([a.mask_of(walls), a.mask_of(roofs), a.mask_of(stone), a.mask_of(bricks), a.mask_of(mill), a.mask_of(thatch)])
        palms = np.maximum(a.mask_of(trunks), a.mask_of(crowns))
        mask = np.maximum.reduce([land, a.mask_of(forest) * smoothstep(0.60, 0.66, a.u), building, palms])
        layer = solid(a, mask, mix(p["morne"], p["far"], 0.30), mix(p["cane"], p["morne"], 0.45), HORIZON - 0.08, HORIZON + 0.06, "saint domingue far", 0.05)
        # The foothill: forest, lit on the side to the sun.
        forest_mask = a.mask_of(forest) * smoothstep(0.60, 0.66, a.u)
        a.light(layer, forest_mask * smoothstep(0.40, 0.70, a.noise("saint domingue forest", cells=30.0, octaves=3)), p["morne_light"], 0.35)
        a.light(layer, a.rim(np.maximum(hill_mask, forest_mask), 0.003, 0.002, 0.5) * mask, p["glow"], 0.35)
        # A beach of pale sand along the coast.
        a.put(layer, a.rim(land, 0.006, 0.0, 0.5) * land, mix(p["sea_light"], p["far"], 0.2), 0.8)
        # The fields: the cane, and the bare red earth, and the fine rows
        # of the cane in the near fields.
        for key, colour in (("cane", p["cane"]), ("cane_light", p["cane_light"]), ("cane_young", p["cane_young"]), ("earth", p["earth"])):
            a.put(layer, field_masks[key], mix(colour, p["far"], 0.25))
        rows = np.clip(1.0 - np.abs(((a.u * 900.0 + a.v * 40.0) % 1.0) - 0.5) / 0.18, 0.0, 1.0) * smoothstep(0.68, 0.80, a.v)
        a.shade(layer, rows * np.maximum.reduce([field_masks["cane"], field_masks["cane_light"], field_masks["cane_young"]]), 0.12)
        a.put(layer, a.mask_of(roads) * ground, mix(p["earth_light"], p["far"], 0.30), 0.8)
        a.put(layer, a.mask_of(trees) * land, mix(p["palm"], p["far"], 0.30))
        a.light(layer, a.rim(a.mask_of(trees), 0.002, 0.001, 0.3) * land, p["glow"], 0.25)
        # The buildings: whitewashed walls, tile roofs, grey stone and the
        # brick of the chimney.
        a.put(layer, a.mask_of(walls), mix(p["wall"], p["far"], 0.12))
        a.put(layer, a.mask_of(holes) * a.mask_of(walls), mix(p["near"], p["far"], 0.35))
        a.put(layer, a.mask_of(stone), mix(p["stone"], p["far"], 0.15))
        a.put(layer, a.mask_of(roofs), mix(p["roof"], p["far"], 0.15))
        a.put(layer, a.mask_of(thatch), mix(p["thatch"], p["far"], 0.20))
        a.put(layer, a.mask_of(mill), mix(p["thatch"], p["far"], 0.15))
        a.put(layer, a.mask_of(bricks), mix(p["brick"], p["far"], 0.12))
        a.light(layer, a.rim(building, 0.002, 0.0, 0.2) * building, p["glow"], 0.45)
        a.put(layer, a.mask_of(trunks), mix(p["trunk"], p["far"], 0.20))
        a.put(layer, a.mask_of(crowns), mix(p["palm"], p["far"], 0.20))
        a.light(layer, a.rim(a.mask_of(crowns), 0.002, 0.001, 0.3) * a.mask_of(crowns), p["palm_light"], 0.4)
        a.put(layer, smoke, p["smoke"], 0.70)
        mask = np.maximum(mask, smoke * 0.70)
        # The warm haze of the late afternoon over the plain.
        a.tint(layer, fog(a, "saint domingue plain haze", HORIZON + 0.006, 0.020, 3.0), p["low"], 0.45)
        a.tint(layer, smoothstep(0.80, HORIZON, a.v) * land, p["low"], 0.20)
        haze(a, layer, p["low"], 0.06, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near saint domingue")
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        stems, stem_pen = a.drawing()
        leaves, leaf_pen = a.drawing()
        cane, cane_pen = a.drawing()
        grass, grass_pen = a.drawing()
        bank, bank_pen = a.drawing()
        ground, line = a.ridge("near saint domingue", 0.70, 0.006, cells=4.0, octaves=3)
        # A bank of red earth along the foot, higher at the two sides, with
        # grass on its top.
        pts = [(u, _at(line, u) - 0.05 * smoothstep(0.30, 0.02, u) - 0.045 * smoothstep(0.70, 0.98, u)) for u in np.linspace(0.0, 1.0, 60)]
        bank_pen.poly([(0.0, 1.0)] + pts + [(1.0, 1.0)])
        for _ in range(260):
            u = rng.uniform(0.0, 1.0)
            v = float(np.interp(u, [q[0] for q in pts], [q[1] for q in pts])) + 0.002
            h = rng.uniform(0.006, 0.016) * (1.0 + 0.8 * (abs(u - 0.5) > 0.3))
            grass_pen.line([(u, v), (u + rng.uniform(-0.005, 0.005), v - h)], 0.0014)
        # Royal palms at the left; banana plants and a clump of cane at the
        # right. The middle stays calm.
        _royal_palm(trunk_pen, crown_pen, rng, 0.06, 0.665, 0.62, 0.01)
        _royal_palm(trunk_pen, crown_pen, rng, 0.16, 0.672, 0.46, -0.008)
        _banana(stem_pen, leaf_pen, rng, 0.86, 0.68, 0.15)
        _banana(stem_pen, leaf_pen, rng, 0.96, 0.67, 0.18)
        _cane(cane_pen, rng, 0.79, 0.685, 0.13)
        _cane(cane_pen, rng, 0.25, 0.68, 0.10)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        plants = np.maximum.reduce([a.mask_of(trunks), a.mask_of(crowns), a.mask_of(stems), a.mask_of(leaves), a.mask_of(cane)])
        mask = np.maximum.reduce([bank_mask, plants, a.mask_of(grass)])
        layer = a.blank()
        a.put(layer, mask, mix(p["palm"], p["near"], 0.35))
        a.put(layer, a.mask_of(crowns), mix(p["palm_light"], p["near"], 0.50))
        a.put(layer, a.mask_of(leaves), mix(p["palm_light"], p["near"], 0.38))
        a.put(layer, a.mask_of(cane), mix(p["cane"], p["near"], 0.40))
        a.put(layer, a.mask_of(trunks) * (1.0 - a.mask_of(crowns)), mix(p["trunk"], p["near"], 0.50))
        # The bank of red earth, in beds, lit along its top, and its grass.
        earth = a.ramp([(0.0, mix(p["near_light"], p["near"], 0.20)), (0.62, mix(p["near_light"], p["near"], 0.20)), (0.80, mix(p["near_light"], p["near"], 0.68)),
                        (1.0, p["near"])])
        a.put(layer, bank_mask, earth)
        beds = np.clip(1.0 - np.abs(((a.v * 90.0 + 0.8 * np.sin(a.u * 11.0)) % 1.0) - 0.5) / 0.12, 0.0, 1.0)
        a.shade(layer, bank_mask * beds * a.noise("saint domingue beds", cells=8.0, octaves=2), 0.30)
        a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, p["glow"], 0.40)
        a.put(layer, a.mask_of(grass), mix(p["cane_young"], p["near"], 0.45))
        a.light(layer, a.rim(plants, 0.003, 0.002, 0.4) * plants, p["glow"], 0.30)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.22)
        haze(a, layer, p["low"], 0.08, None)
        return layer
    layer = _air(a, p, "saint domingue warm haze", p["low"], 0.28, p["near"], 0.22)
    a.put(layer, shafts(a, "saint domingue shafts", 4, 0.20, 0.0, 0.85, 0.05), p["glow"], 0.08)
    return layer


def saint_domingue_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """The tips of royal palm fronds that hang into the top of the view at
    two places, and a few long leaves of cane that stand from below at one
    place."""
    del layer_lights
    rng = art_.rand("saint domingue foreground")
    for k in range(2):
        u0 = (k + rng.uniform(0.15, 0.85)) / 2.0
        for j in range(2):
            start = (u0 + (j - 0.5) * 0.05, 0.0)
            end = (start[0] + (0.08 if j else -0.08) + rng.uniform(-0.02, 0.02), 0.384 - rng.uniform(0.0, 0.01))
            ctrl = ((start[0] + end[0]) * 0.5 + (0.03 if j else -0.03), 0.20)
            rib = _arch(start, ctrl, end, 20)
            pen.line(rib, 0.0026)
            for i, (x, y) in enumerate(rib[1:], 1):
                t = i / 20.0
                side = 0.032 * (1.0 - t * 0.6)
                if y + side > 0.392:
                    side = max(0.0, 0.392 - y)
                pen.line([(x, y), (x + side * 0.25, y + side)], 0.0013)
                pen.line([(x, y), (x - side * 0.25, y + side)], 0.0013)
    u0 = rng.uniform(0.35, 0.65)
    for _ in range(6):
        u = u0 + rng.uniform(-0.015, 0.015)
        top = REST_BOTTOM - rng.uniform(-0.004, 0.010)
        bend = rng.uniform(-0.05, 0.05)
        _leaf(pen, _arch((u, 1.0), (u + bend * 0.2, top + 0.08), (u + bend, top), 10), 0.004, 0.6)
