"""The scenes of the History dimension: the coasts of East Asia.

The History dimension is a grid. East is later, and each floor is a region
of the world. These rooms show three peoples of the coasts of East Asia: the
Jomon villagers of north Japan, the first farmers and seafarers of Taiwan
(the homeland of the Austronesian languages), and Silla, the kingdom of
Korea that built its capital at Gyeongju. Three later rooms show the
capitals of the same coasts: Hangzhou of the Southern Song, Heian-kyo, and
Hanyang of Joseon. They use the same sepia of an old textbook and the same
rules as `history_eras.py` and `history_southeast_asia.py`. The people of
these places show skill, invention and wealth of their own; nothing here is
a joke on them.

- ``history_jomon`` (Sannai-Maruyama, north Japan, about 3000 BCE). A clear
  afternoon of early autumn. A forest of chestnut and beech covers a low
  terrace; its warm greens are just turning gold and rust. The calm blue
  water of Mutsu Bay is below the terrace at the left, and the snowy peaks
  of the Hakkoda are far off at the right. In a clearing stands a village of
  pit houses: steep cones of thatch that come down to the ground, smoke
  from a few of them, and one long house. Above the trees stand the six
  great chestnut posts of the village's tall structure: two rows of three
  posts with three open floors and no roof. Ferns and the burrs of
  chestnuts are near.
- ``history_taiwan`` (the east coast of Taiwan, about 2500 BCE). A clear
  morning. Steep green mountains of the Central Range fall straight into
  the deep blue Pacific, one headland behind the next, with white surf on
  the rocks at their feet. On a fan of land at the foot of the near
  mountain are small terraces of millet, houses of wood and thatch on
  stilts, and a plank canoe pulled up on the beach. Pandanus with its prop
  roots and silvergrass with pale plumes are near.
- ``history_gyeongju`` (Gyeongju, the capital of Silla, about 640 CE). An
  afternoon of autumn. Smooth green mounds of the royal tombs, of many
  sizes, stand on the plain among red pines with orange-red bark and flat
  dark crowns. The tiled roofs of the palace, with eaves that turn up at
  their ends, stand on its low hill. Cheomseongdae, a tower of granite in
  the shape of a bottle, stands small in the middle distance. The low
  mountain Namsan is behind. Red pines and the scarlet leaves of maples
  are near.

- ``history_hangzhou`` (Hangzhou, the Southern Song capital, about 1200 CE).
  A soft morning of spring on West Lake. The water is still and shows each
  thing on it upside down. The Su causeway crosses the lake with willows,
  peach trees in blossom and three arched stone bridges. Leifeng Pagoda,
  octagonal with five eaved storeys, stands on its wooded hill at the left.
  Rows of tea bushes cover the hills behind, and the grey tile roofs of the
  city line the shore at the right. A pleasure boat and small boats are on
  the water. Willow fronds and lotus are near.
- ``history_heian`` (Heian-kyo, about 1000 CE). An afternoon of autumn in
  the garden of a mansion. Low, wide halls in the shinden style, with
  vermilion pillars, black lattice, pale blinds and roofs of cypress bark,
  are joined by covered corridors; one corridor goes out to a pavilion over
  the pond. A red arched bridge goes to an island of pines. An ox carriage
  stands in the court of white gravel. Maples are red and gold, and the
  soft hills of Higashiyama are behind. A maple and pampas grass are near.
- ``history_hanyang`` (Hanyang, the capital of Joseon, 1446 CE). A clear
  morning of early summer at Gyeongbokgung. Geunjeongjeon stands on its two
  terraces of granite in a paved court, with two storeys of tiled roof whose
  eaves sweep up, and painted brackets in green, blue and red. Bugaksan
  rises behind it, a dome of pale granite over slopes of pine, and the wall
  of the city follows the ridges. Red pines and peonies are near.

No picture here shows a god, a Buddha or a temple with images. The pagoda
is architecture far off.

The bright detail is far off or at the edges, and the middle of each near
layer is calm, so the play in front of it reads. The things that drift in the
air are the room's motes (`terrain/motes.py`), not part of these pictures.
"""

from __future__ import annotations

import math

import numpy as np

from .artkit import Art, Pen, mix, polar, scale, smoothstep
from .history_americas_pacific import _canopy, _pandanus
from .history_eras import REST_BOTTOM, _air, _at, _heaps, _plume, _sun, _textbook
from .history_origins import _arch, _land, _leaf
from .history_southeast_asia import _fern, _reflect, _ripple
from .parts import HORIZON, fog, haze, shafts, solid

# ---------------------------------------------------------------------------
# Parts that more than one room has
# ---------------------------------------------------------------------------


def _column_line(a: Art, us, vs) -> np.ndarray:
    """A line with one `v` for each column of the panel, from points
    `(us, vs)`. Columns outside the points get the `v` of the end points."""
    return np.interp(np.linspace(0.0, 1.0, a.n), us, vs).astype(np.float32)


def _bank(a: Art, tag: str, left_rise: float, right_rise: float, base: float = 0.705):
    """The ground of a near layer: a low bank that rises a little at the two
    sides, so the near things stand at the sides and the middle is calm.
    Returns `(pen image, ground mask, bank_at)`."""
    bank, bank_pen = a.drawing()
    ground, line = a.ridge(tag, base, 0.005, cells=4.0, octaves=3)
    pts = [(u, _at(line, u) - left_rise * smoothstep(0.26, 0.02, u) - right_rise * smoothstep(0.74, 0.98, u)) for u in np.linspace(0.0, 1.0, 60)]
    bank_pen.poly([(0.0, 1.0)] + pts + [(1.0, 1.0)])

    def bank_at(u: float) -> float:
        return float(np.interp(u, [q[0] for q in pts], [q[1] for q in pts]))

    return bank, ground, bank_at


def _autumn(a: Art, layer: np.ndarray, mask: np.ndarray, p: dict, tag: str, far: float, turn: float = 0.5) -> None:
    """Paint the crowns of a broadleaf forest over `mask` in early autumn:
    warm green, with patches that turn gold and fewer that turn rust. `turn`
    is how far the autumn has gone. The lit side faces the sun at the left."""
    a.put(layer, mask, mix(p["forest"], p["far"], far))
    lumps = a.noise((tag, "lumps"), cells=60.0, octaves=3)
    gold = smoothstep(0.62 - turn * 0.18, 0.74 - turn * 0.18, a.noise((tag, "gold"), cells=26.0, octaves=3))
    rust = smoothstep(0.70 - turn * 0.10, 0.80 - turn * 0.10, a.noise((tag, "rust"), cells=34.0, octaves=3))
    a.put(layer, mask * gold, mix(p["gold"], p["far"], far), 0.75)
    a.put(layer, mask * rust, mix(p["rust"], p["far"], far), 0.70)
    a.light(layer, mask * smoothstep(0.55, 0.75, lumps), mix(p["forest_light"], p["far"], far), 0.35)
    a.shade(layer, mask * smoothstep(0.45, 0.25, lumps), 0.20 * (1.0 - far))
    a.light(layer, a.rim(mask, 0.003, 0.003, 0.5) * mask, mix(p["forest_light"], p["glow"], 0.4), 0.45)
    a.shade(layer, a.rim(mask, -0.003, -0.003, 0.5) * mask, 0.22 * (1.0 - far))


def _lumpy_crown(pen: Pen, rng, u: float, v: float, rx: float, ry: float, count: int) -> None:
    """The crown of a broadleaf tree: many round lumps in an oval round
    `(u, v)`, more of them near the middle."""
    for _ in range(count):
        ang = rng.uniform(0.0, math.tau)
        r = rng.uniform(0.0, 1.0) ** 0.7
        pen.ellipse(u + math.cos(ang) * r * rx, v + math.sin(ang) * r * ry, rx * rng.uniform(0.07, 0.15), ry * rng.uniform(0.08, 0.18))


def _limbs(pen: Pen, rng, u: float, v_foot: float, v_top: float, w: float, lean: float, limbs: int) -> list[tuple[float, float]]:
    """A trunk that tapers from `w` at its foot to its top, and `limbs`
    limbs that go up and out from its upper part. Returns the ends of the
    limbs, where the lumps of the crown go."""
    pts = [(u + lean * t**1.5, v_foot + 0.01 - (v_foot + 0.01 - v_top) * t) for t in np.linspace(0.0, 1.0, 10)]
    for i in range(len(pts) - 1):
        t = i / (len(pts) - 1)
        pen.line([pts[i], pts[i + 1]], w * (1.0 - 0.55 * t))
    # The root flare at the foot.
    pen.poly([(u - w * 1.1, v_foot + 0.012), (u + w * 1.1, v_foot + 0.012), (u + w * 0.5, v_foot - w * 1.2), (u - w * 0.5, v_foot - w * 1.2)])
    ends = []
    height = v_foot - v_top
    for k in range(limbs):
        t = 0.55 + 0.40 * k / max(limbs - 1, 1)
        start = (u + lean * t**1.5, v_foot - height * t)
        side = -1.0 if k % 2 else 1.0
        end = (start[0] + side * height * rng.uniform(0.18, 0.30), start[1] - height * rng.uniform(0.10, 0.22))
        pen.line(_arch(start, (start[0] + side * height * 0.08, start[1] - height * 0.10), end, 6), w * 0.45)
        ends.append(end)
    ends.append(pts[-1])
    return ends


def _grass_blades(pen: Pen, rng, u: float, v: float, h: float, count: int, width: float, spread: float = 0.04) -> None:
    """A tuft of long grass blades that arch up and out from one base."""
    for _ in range(count):
        lean = rng.uniform(-spread, spread)
        top = (u + lean, v - h * rng.uniform(0.6, 1.0))
        tip = (top[0] + lean * 0.5, top[1] + h * 0.15 * abs(lean) / max(spread, 1e-6))
        pen.line(_arch((u + rng.uniform(-0.004, 0.004), v + 0.004), (u + lean * 0.2, top[1] + h * 0.3), tip, 8), width)


# ---------------------------------------------------------------------------
# Jomon: Sannai-Maruyama in early autumn
# ---------------------------------------------------------------------------


JOMON = {
    "top": (92, 134, 176),
    "mid": (174, 198, 210),
    "low": (240, 228, 200),
    "glow": (255, 224, 168),
    "sun": (255, 246, 222),
    "cloud": (250, 244, 230),
    "cloud_shadow": (178, 180, 184),
    "bay": (62, 112, 156),
    "bay_light": (196, 220, 226),
    "far_hills": (126, 146, 164),
    "hakkoda": (112, 128, 152),
    "hakkoda_light": (206, 206, 210),
    "snow": (248, 248, 246),
    "forest": (82, 112, 58),
    "forest_light": (160, 170, 88),
    "gold": (212, 168, 64),
    "rust": (176, 88, 44),
    "grass": (150, 152, 82),
    "grass_light": (204, 192, 118),
    "path": (170, 140, 98),
    "thatch": (178, 142, 86),
    "door": (46, 34, 28),
    "post": (112, 80, 54),
    "post_light": (196, 156, 106),
    "deck": (146, 108, 72),
    "smoke": (226, 222, 216),
    "trunk": (96, 72, 52),
    "beech": (152, 148, 138),
    "burr": (176, 162, 72),
    "far": (206, 210, 208),
    "near": (42, 34, 26),
    "near_light": (156, 124, 74),
    "fern": (104, 120, 58),
    "fern_light": (180, 170, 90),
    "moss": (74, 82, 44),
}


def _pit_house(roof: Pen, door: Pen, u: float, v: float, w: float, h: float) -> None:
    """A Jomon pit house: the floor is dug down into the ground, so only a
    steep cone of thatch shows, and it comes down to the ground on all
    sides. Its sides bulge out a little. A small vent under a tiny gable is
    at its top, and a low door is at its foot."""
    left = [(u - w * (1.0 - t**1.4), v + 0.002 - h * t) for t in np.linspace(0.0, 1.0, 10)]
    right = [(u + w * (1.0 - t**1.4), v + 0.002 - h * t) for t in np.linspace(0.0, 1.0, 10)]
    roof.poly(left + right[::-1])
    # The vent: a small gable that stands over the top of the cone.
    roof.poly([(u - w * 0.16, v - h * 0.94), (u + w * 0.16, v - h * 0.94), (u + w * 0.06, v - h * 1.08), (u - w * 0.06, v - h * 1.08)])
    door.ellipse(u + w * 0.18, v - h * 0.13, w * 0.14, h * 0.10)
    door.rect(u + w * 0.04, v - h * 0.13, u + w * 0.32, v + 0.001)


def _long_house(roof: Pen, door: Pen, u: float, v: float, w: float, h: float) -> None:
    """The long house of the village: a long, low roof of thatch with round
    ends that comes down to the ground, and a door in its long side."""
    pts = [(u + w * math.cos(t), v + 0.002 - h * math.sin(t) ** 0.45) for t in np.linspace(math.pi, 0.0, 30)]
    roof.poly(pts)
    for s in (-1.0, 1.0):
        roof.poly([(u + s * w * 0.55, v - h * 0.92), (u + s * w * 0.55 + w * 0.05, v - h * 0.92), (u + s * w * 0.55 + w * 0.025, v - h * 1.10)])
    door.ellipse(u - w * 0.10, v - h * 0.16, w * 0.06, h * 0.14)
    door.rect(u - w * 0.16, v - h * 0.16, u - w * 0.04, v + 0.001)


def _six_posts(back: Pen, top: Pen, edge: Pen, front: Pen, u: float, v: float, h: float) -> None:
    """The great structure of Sannai-Maruyama as it is rebuilt: six posts of
    chestnut, each a whole trunk about 1 m thick and 15 m tall, in two rows
    of three about 4 m apart. Three open floors span between the posts at
    three heights; there is no floor and no roof at the top. It is seen a
    little from the side and from above, so the back row stands to the right
    of the front row and higher, and the top of each floor shows. `h` is the
    height of the posts. The pens are the back posts, the tops of the
    floors, the front edges of the floors and the front posts."""
    w = h * 0.28
    pw = h * 0.075
    dx, dy = w * 0.45, -h * 0.07
    for k in range(3):
        x = u + (k - 1) * w + dx
        back.rect(x - pw * 0.5, v + dy - h, x + pw * 0.5, v + dy + 0.002)
    thick = h * 0.030
    for f in (0.28, 0.50, 0.72):
        y = v - h * f
        x0, x1 = u - w - pw * 0.3, u + w + pw * 0.3
        top.poly([(x0, y), (x1, y), (x1 + dx, y + dy), (x0 + dx, y + dy)])
        edge.rect(x0, y, x1, y + thick)
    for k in range(3):
        x = u + (k - 1) * w
        front.rect(x - pw * 0.5, v - h, x + pw * 0.5, v + 0.002)


def history_jomon(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = JOMON
    sun_at = (0.20, 0.33)

    def coast(v):
        # The edge of the terrace over the bay: it comes toward the eye and
        # to the left.
        return 0.40 - (v - HORIZON) * 2.6

    if layer_key == "sky":
        # A clear sky of autumn, deep blue high up and warm low down, with
        # a few small clouds. Under the horizon is the bay.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.85)), (0.24, p["top"]), (0.46, p["mid"]), (HORIZON - 0.01, p["low"]),
                                 (HORIZON + 0.002, mix(p["bay"], p["low"], 0.35)), (HORIZON + 0.04, p["bay"]), (1.0, p["bay"])]))
        _sun(a, layer, *sun_at, 0.022, p["sun"], p["glow"], 0.60)
        _heaps(a, layer, "jomon heaps", ((0.42, 0.45, 0.05, 0.035), (0.56, 0.41, 0.035, 0.022), (0.90, 0.44, 0.04, 0.026)), p["cloud"], p["cloud_shadow"], 0.80)
        # The far shore across the bay at the left: low blue hills.
        hills, line = a.ridge("jomon far shore", HORIZON - 0.006, 0.006, cells=5.0, octaves=4)
        above = smoothstep(HORIZON + 0.003, HORIZON, a.v)
        hills = hills * smoothstep(0.50, 0.38, a.u) * above
        a.put(layer, hills, a.ramp([(0.0, mix(p["far_hills"], p["mid"], 0.45)), (HORIZON - 0.012, mix(p["far_hills"], p["mid"], 0.45)), (HORIZON, mix(p["far_hills"], p["low"], 0.6)), (1.0, p["low"])]))
        # The Hakkoda: a group of old volcanoes with round tops, far off at
        # the right, with the first snow on their tops.
        us = np.linspace(0.50, 1.06, 90)
        bumps = ((0.60, 0.030, 0.040), (0.68, 0.050, 0.035), (0.76, 0.068, 0.040), (0.835, 0.056, 0.032), (0.91, 0.046, 0.040), (0.99, 0.036, 0.045))
        rise = np.array([0.010 + sum(hgt * math.exp(-(((x - c) / wd) ** 2)) for c, hgt, wd in bumps) for x in us])
        rise *= smoothstep(0.50, 0.58, us)
        top = _column_line(a, us, HORIZON + 0.002 - rise)
        massif = _land(a, top) * smoothstep(0.50, 0.53, a.u) * above
        colour = mix(p["hakkoda"], p["mid"], 0.30)
        a.put(layer, massif, a.ramp([(0.0, colour), (HORIZON - 0.07, colour), (HORIZON - 0.005, mix(colour, p["low"], 0.55)), (1.0, p["low"])]))
        gullies = smoothstep(0.58, 0.80, a.noise("jomon hakkoda gullies", cells=40.0, octaves=2, stretch=0.25))
        a.shade(layer, massif * gullies * smoothstep(HORIZON, HORIZON - 0.04, a.v), 0.10)
        a.light(layer, a.rim(massif, 0.008, 0.0, 1.5) * massif, mix(p["hakkoda_light"], p["glow"], 0.4), 0.45)
        depth = a.v - top[None, :]
        snow = massif * smoothstep(0.016, 0.006, depth + (a.noise("jomon snow line", cells=50.0, octaves=3) - 0.5) * 0.012)
        snow = snow * smoothstep(HORIZON - 0.030, HORIZON - 0.040, a.v)
        streaks = massif * gullies * smoothstep(0.035, 0.012, depth) * smoothstep(HORIZON - 0.025, HORIZON - 0.035, a.v)
        a.put(layer, np.maximum(snow, streaks * 0.8), mix(p["snow"], p["mid"], 0.12), 0.95)
        a.shade(layer, snow * a.rim(massif, -0.010, 0.0, 2.0), 0.10)
        a.tint(layer, fog(a, "jomon low haze", HORIZON - 0.006, 0.016, 3.0), p["low"], 0.55)
        sea = (a.v > HORIZON + 0.002).astype(np.float32)
        a.light(layer, sea * smoothstep(0.62, 0.82, a.noise("jomon bay lines", cells=50.0, octaves=2, stretch=12.0)), p["bay_light"], 0.35)
        _textbook(a, layer, 0.08)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far jomon")
        # The terrace: land at the right and in front, and the bay at the
        # left under it.
        _, tline = a.ridge("jomon terrace", HORIZON + 0.014, 0.003, cells=4.0, octaves=2)
        land = _land(a, tline) * smoothstep(coast(a.v) - 0.008, coast(a.v) + 0.008, a.u)
        bay = smoothstep(HORIZON + 0.001, HORIZON + 0.004, a.v) * (1.0 - land)
        # The forest: a wall of crowns behind the village, and trees down
        # the slope to the bay at the left.
        forest, forest_pen = a.drawing()
        crown_line = tline - 0.004
        _canopy(forest_pen, rng, crown_line, 0.34, 1.02, 0.010, 0.005, 0.011, 420)
        for _ in range(200):
            v = rng.uniform(HORIZON + 0.012, 0.74)
            u = coast(v) + rng.uniform(-0.004, 0.05)
            r = rng.uniform(0.005, 0.011) * (1.0 + (v - HORIZON) * 4.0)
            forest_pen.ellipse(u, v - r * 0.5, r, r * 0.8)
        # Single chestnuts that stand in the clearing.
        for u, v, r in ((0.50, 0.672, 0.016), (0.63, 0.676, 0.013), (0.99, 0.664, 0.018), (0.86, 0.684, 0.020)):
            forest_pen.ellipse(u, v - r * 1.4, r, r * 0.85)
            forest_pen.ellipse(u + r * 0.7, v - r * 1.1, r * 0.7, r * 0.6)
            forest_pen.ellipse(u - r * 0.7, v - r * 1.0, r * 0.7, r * 0.6)
        stems, stem_pen = a.drawing()
        for u, v, r in ((0.50, 0.672, 0.016), (0.63, 0.676, 0.013), (0.99, 0.664, 0.018), (0.86, 0.684, 0.020)):
            stem_pen.line([(u, v + 0.002), (u, v - r)], r * 0.25)
        # The village in its clearing: pit houses, the long house and the
        # six posts. The tall posts stand above the trees.
        roofs, roof_pen = a.drawing()
        doors, door_pen = a.drawing()
        houses = ((0.455, 0.654, 0.015), (0.52, 0.643, 0.012), (0.585, 0.660, 0.017), (0.645, 0.640, 0.011), (0.785, 0.652, 0.016),
                  (0.835, 0.640, 0.012), (0.905, 0.658, 0.018), (0.955, 0.643, 0.013))
        for u, v, w in houses:
            _pit_house(roof_pen, door_pen, u, v, w * 1.15, w * 1.85)
        _long_house(roof_pen, door_pen, 0.70, 0.672, 0.046, 0.024)
        posts = {key: a.drawing() for key in ("back", "top", "edge", "front")}
        tu, tv = 0.705, 0.644
        _six_posts(posts["back"][1], posts["top"][1], posts["edge"][1], posts["front"][1], tu, tv, 0.100)
        land_mask = np.maximum(land, a.mask_of(forest) * (a.v > HORIZON - 0.04))
        forest_mask = a.mask_of(forest)
        roof_mask = a.mask_of(roofs)
        door_mask = a.mask_of(doors) * roof_mask
        pm = {key: a.mask_of(img) for key, (img, _) in posts.items()}
        post_mask = np.maximum.reduce(list(pm.values()))
        stem_mask = a.mask_of(stems)
        mask = np.maximum.reduce([land_mask, bay, roof_mask, post_mask])
        layer = solid(a, mask, mix(p["grass"], p["far"], 0.35), p["grass"], HORIZON, 0.70, "jomon far", 0.05)
        # The bay: calm blue water with long lines of light, and a pale edge
        # where it meets the shore.
        a.put(layer, bay, a.ramp([(0.0, mix(p["bay"], p["far"], 0.45)), (HORIZON, mix(p["bay"], p["far"], 0.45)), (0.70, mix(p["bay"], p["far"], 0.15)), (1.0, p["bay"])]))
        a.light(layer, bay * smoothstep(0.58, 0.80, a.noise("jomon bay ripples", cells=60.0, octaves=2, stretch=12.0)), p["bay_light"], 0.45)
        a.light(layer, bay * a.spot(sun_at[0], HORIZON + 0.03, 0.20, 1.5, squash=2.5), p["glow"], 0.35)
        a.light(layer, a.rim(bay, -0.006, 0.0, 0.6) * bay, p["bay_light"], 0.5)
        # The clearing: dry grass of autumn in patches, and worn paths of
        # bare earth between the houses.
        a.light(layer, land * smoothstep(0.55, 0.75, a.noise("jomon grass", cells=30.0, octaves=3, stretch=4.0)), p["grass_light"], 0.40)
        paths = smoothstep(0.0035, 0.0010, np.abs(a.v - (0.664 + 0.006 * np.sin(a.u * 14.0)))) * smoothstep(0.42, 0.46, a.u)
        a.put(layer, land * paths * (1.0 - forest_mask), mix(p["path"], p["far"], 0.15), 0.6)
        a.put(layer, stem_mask, mix(p["trunk"], p["far"], 0.2))
        _autumn(a, layer, forest_mask, p, "jomon far forest", 0.22, 0.45)
        # The houses: thatch lit on the side to the sun, dark at the foot,
        # with the stalks of the thatch in long lines.
        a.put(layer, roof_mask, a.ramp([(0.0, mix(p["thatch"], p["far"], 0.15)), (0.63, mix(p["thatch"], p["far"], 0.15)), (0.67, p["thatch"]), (1.0, p["thatch"])]))
        a.shade(layer, roof_mask * smoothstep(0.3, 0.9, a.noise("jomon thatch", cells=220.0, octaves=1, stretch=0.10)), 0.16)
        a.light(layer, a.rim(roof_mask, 0.004, 0.0, 0.3) * roof_mask, p["glow"], 0.50)
        a.shade(layer, a.rim(roof_mask, -0.005, 0.0, 0.5) * roof_mask, 0.25)
        a.put(layer, door_mask, p["door"], 0.9)
        # The six posts: the back row in shade, the floors lit on their
        # tops, and the front row lit on the side to the sun.
        # The six posts: the back row darker, in the shade of the floors; the
        # tops of the floors pale with the sky on them, their front edges lit
        # with a dark line of shade under each; the front row lit on the
        # side to the sun and dark on the other side, so each post is round.
        a.put(layer, pm["back"], scale(p["post"], 0.62))
        a.put(layer, pm["top"], mix(p["deck"], p["post_light"], 0.35))
        under = np.clip(a.shift(pm["edge"], 0.0, 0.003) - pm["edge"] - pm["top"], 0.0, 1.0)
        a.put(layer, under * (1.0 - pm["front"]), scale(p["post"], 0.45), 0.8)
        a.put(layer, pm["edge"], p["deck"])
        a.light(layer, a.rim(pm["edge"], 0.0, 0.0015, 0.0) * pm["edge"], p["post_light"], 0.70)
        a.put(layer, pm["front"], p["post"])
        a.light(layer, a.rim(pm["front"], 0.0025, 0.0, 0.0) * pm["front"], p["post_light"], 0.70)
        a.shade(layer, a.rim(pm["front"], -0.0025, 0.0, 0.0) * pm["front"], 0.35)
        # Smoke from three of the houses goes up and drifts to the right.
        for k, (u, v, w) in enumerate((houses[1], houses[4], houses[6])):
            smoke = _plume(a, ("jomon smoke", k), u, v - w * 1.6, 0.06, 0.03, 0.004)
            a.put(layer, smoke, p["smoke"], 0.55)
            mask = np.maximum(mask, smoke * 0.55)
        a.tint(layer, fog(a, "jomon terrace haze", HORIZON + 0.006, 0.014, 3.0) * mask, p["low"], 0.40)
        haze(a, layer, p["low"], 0.07, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near jomon")
        bank, ground, bank_at = _bank(a, "near jomon", 0.040, 0.034)
        trunks, trunk_pen = a.drawing()
        beech, beech_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        burrs, burr_pen = a.drawing()
        ferns, fern_pen = a.drawing()
        # A big chestnut at the left with burrs at the ends of its twigs; a
        # beech with a smooth grey trunk at the right; bracken at their
        # feet. The middle is calm.
        for end in _limbs(trunk_pen, rng, 0.085, bank_at(0.085) + 0.006, 0.40, 0.020, 0.03, 4):
            _lumpy_crown(crown_pen, rng, end[0], end[1] - 0.02, 0.065, 0.045, 90)
            for _ in range(3):
                bu = end[0] + rng.uniform(-0.05, 0.05)
                bv = end[1] - 0.01 + rng.uniform(0.0, 0.04)
                burr_pen.ellipse(bu, bv, 0.0042)
                for j in range(12):
                    burr_pen.line([(bu, bv), polar(bu, bv, 0.0068, j * 30.0 + rng.uniform(-8.0, 8.0))], 0.0008)
        for end in _limbs(beech_pen, rng, 0.915, bank_at(0.915) + 0.006, 0.36, 0.014, -0.02, 3):
            _lumpy_crown(crown_pen, rng, end[0], end[1] - 0.02, 0.055, 0.040, 80)
        for u, h in ((0.17, 0.065), (0.23, 0.045), (0.80, 0.055), (0.86, 0.07), (0.99, 0.05)):
            _fern(fern_pen, rng, u, bank_at(u) + 0.004, h, 9)
        for _ in range(10):
            u = rng.uniform(0.30, 0.70)
            _fern(fern_pen, rng, u, bank_at(u) + 0.002, rng.uniform(0.010, 0.016), 5)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        trunk_mask = a.mask_of(trunks)
        beech_mask = a.mask_of(beech)
        crown_mask = a.mask_of(crowns)
        burr_mask = a.mask_of(burrs)
        fern_mask = a.mask_of(ferns)
        mask = np.maximum.reduce([bank_mask, trunk_mask, beech_mask, crown_mask, burr_mask, fern_mask])
        layer = a.blank()
        earth = a.ramp([(0.0, mix(p["moss"], p["near"], 0.30)), (0.66, mix(p["moss"], p["near"], 0.30)), (0.80, mix(p["moss"], p["near"], 0.75)), (1.0, p["near"])])
        a.put(layer, bank_mask, earth)
        leaves = bank_mask * smoothstep(0.62, 0.80, a.noise("jomon leaf litter", cells=110.0, octaves=1)) * smoothstep(0.76, 0.70, a.v)
        a.put(layer, leaves, mix(p["rust"], p["near"], 0.45), 0.6)
        a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, p["glow"], 0.30)
        # The chestnut's bark is dark and cut in long ridges; the beech's
        # bark is smooth and grey.
        a.put(layer, trunk_mask, mix(p["trunk"], p["near"], 0.40))
        ridges = smoothstep(0.45, 0.75, a.noise("jomon chestnut bark", cells=220.0, octaves=1, stretch=0.08))
        a.shade(layer, trunk_mask * ridges, 0.30)
        a.put(layer, beech_mask, mix(p["beech"], p["near"], 0.35))
        for m in (trunk_mask, beech_mask):
            a.light(layer, a.rim(m, 0.004, 0.0, 0.4) * m, p["glow"], 0.40)
        near = {**p, "forest": mix(p["forest"], p["near"], 0.50), "gold": mix(p["gold"], p["near"], 0.40), "rust": mix(p["rust"], p["near"], 0.40),
                "forest_light": mix(p["forest_light"], p["near"], 0.30), "far": p["near"]}
        _autumn(a, layer, crown_mask, near, "jomon near crowns", 0.0, 0.40)
        a.put(layer, burr_mask, mix(p["burr"], p["near"], 0.25))
        a.light(layer, a.rim(burr_mask, 0.002, 0.002, 0.2) * burr_mask, p["glow"], 0.35)
        a.put(layer, fern_mask, mix(p["fern"], p["near"], 0.30))
        a.put(layer, fern_mask * smoothstep(0.60, 0.75, a.noise("jomon fern rust", cells=30.0, octaves=2)), mix(p["rust"], p["near"], 0.35), 0.7)
        a.light(layer, a.rim(fern_mask, 0.002, 0.002, 0.3) * fern_mask, mix(p["fern_light"], p["glow"], 0.2), 0.40)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.20)
        haze(a, layer, p["low"], 0.07, None)
        return layer
    layer = _air(a, p, "jomon autumn air", p["low"], 0.20, scale(p["near"], 0.8), 0.20)
    a.put(layer, shafts(a, "jomon shafts", 4, 0.14, 0.0, 0.85, 0.05), p["glow"], 0.08)
    return layer


def jomon_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Bracken stands from below at two places, and a twig of chestnut with
    long toothed leaves and two spiny burrs hangs from above at one place."""
    del layer_lights
    rng = art_.rand("jomon foreground")
    for k in range(2):
        u0 = 0.12 + (k + rng.uniform(0.2, 0.8)) * 0.38
        for j in range(5):
            t = j / 4.0 - 0.5
            ang = -90.0 + t * 80.0
            length = rng.uniform(0.10, 0.13) * (1.0 - abs(t) * 0.4)
            base = (u0 + t * 0.01, REST_BOTTOM + 0.10)
            tip = polar(*base, length, ang)
            tip = (tip[0] + t * 0.04, max(tip[1] + length * 0.18, REST_BOTTOM - 0.012))
            rib = _arch(base, polar(*base, length * 0.7, ang), tip, 12)
            pen.line([(base[0], 1.0)] + rib, 0.0022)
            for i in range(1, len(rib) - 1):
                x, y = rib[i]
                side = 0.012 * (1.0 - i / len(rib))
                for s in (-1.0, 1.0):
                    pen.line([(x, y), (x + s * side, max(y - side * 0.3, REST_BOTTOM - 0.010))], 0.0014)
    u = rng.uniform(0.40, 0.60)
    twig = _arch((u - 0.06, 0.0), (u - 0.01, 0.22), (u + 0.09, 0.33), 14)
    pen.line(twig, 0.0028)
    for i, (x, y) in enumerate(twig[4:], 4):
        s = 1.0 if i % 2 else -1.0
        length = rng.uniform(0.040, 0.055)
        tip = (x + s * length * 0.35, min(0.386, y + length))
        rib = [(x, y), ((x + tip[0]) * 0.5 + s * 0.004, (y + tip[1]) * 0.5), tip]
        _leaf(pen, rib, 0.0045, 0.8)
    for bx, by in (twig[9], twig[13]):
        cy = min(by + 0.020, 0.372)
        pen.line([(bx, by), (bx, cy)], 0.0016)
        pen.ellipse(bx, cy, 0.0075)
        for j in range(14):
            end = polar(bx, cy, 0.0120, j * (360.0 / 14.0))
            pen.line([(bx, cy), (end[0], min(end[1], 0.388))], 0.0010)


# ---------------------------------------------------------------------------
# Taiwan: the east coast in the morning
# ---------------------------------------------------------------------------


TAIWAN = {
    "top": (42, 102, 170),
    "mid": (138, 184, 214),
    "low": (232, 236, 222),
    "glow": (255, 236, 194),
    "sun": (255, 250, 228),
    "cloud": (250, 250, 246),
    "cloud_shadow": (170, 184, 198),
    "ocean": (22, 70, 130),
    "ocean_light": (150, 196, 220),
    "surf": (248, 250, 248),
    "range": (70, 112, 118),
    "mountain": (46, 104, 62),
    "mountain_light": (128, 172, 88),
    "mountain_dark": (26, 68, 50),
    "cliff": (118, 114, 100),
    "cliff_light": (198, 190, 166),
    "sand": (170, 162, 146),
    "sand_light": (218, 210, 190),
    "millet": (204, 170, 78),
    "millet_light": (236, 208, 122),
    "terrace": (104, 118, 60),
    "thatch": (186, 154, 98),
    "wood": (110, 80, 56),
    "canoe": (104, 72, 50),
    "pandanus": (74, 114, 64),
    "pandanus_light": (156, 182, 98),
    "trunk": (128, 106, 80),
    "grass": (116, 136, 68),
    "grass_light": (176, 180, 100),
    "plume": (234, 226, 206),
    "far": (196, 214, 222),
    "near": (30, 42, 34),
    "near_light": (130, 140, 96),
    "rock": (92, 92, 86),
}


def _stilt_house(posts: Pen, walls: Pen, roof: Pen, u: float, v: float, w: float, h: float) -> None:
    """A house of wood and thatch on low stilts: a floor on posts, walls of
    planks, a ladder, and a steep roof of thatch with long eaves."""
    floor = v - h * 0.30
    for k in range(4):
        x = u - w * 0.80 + k * w * 0.533
        posts.line([(x, v + 0.002), (x, floor)], w * 0.08)
    posts.rect(u - w * 0.96, floor - h * 0.04, u + w * 0.96, floor)
    posts.line([(u + w * 1.20, v + 0.001), (u + w * 0.82, floor)], w * 0.06)
    walls.rect(u - w * 0.80, floor - h * 0.30, u + w * 0.80, floor - h * 0.04)
    eave = floor - h * 0.24
    roof.poly([(u - w * 1.22, eave), (u + w * 1.22, eave), (u + w * 0.55, floor - h * 1.05), (u - w * 0.55, floor - h * 1.05)])


def _plank_canoe(hull: Pen, strake: Pen, u: float, v: float, s: float, facing: float = 1.0) -> None:
    """A canoe pulled up on the beach, with no outrigger: a dugout base
    with a plank sewn along each side to make it deeper, and ends that rise.
    `s` is its length."""
    f = facing
    hull.poly([(u - f * s * 0.52, v - s * 0.17), (u - f * s * 0.40, v - s * 0.10), (u + f * s * 0.40, v - s * 0.10), (u + f * s * 0.55, v - s * 0.20),
               (u + f * s * 0.42, v), (u - f * s * 0.40, v)])
    strake.line([(u - f * s * 0.44, v - s * 0.11), (u + f * s * 0.46, v - s * 0.12)], s * 0.022)


def _silvergrass(blades: Pen, plumes: Pen, rng, u: float, v: float, h: float, count: int = 14, heads: int = 5) -> None:
    """A clump of silvergrass (Miscanthus): long narrow blades that arch out
    from one base, and tall stems with pale feathery plumes that bend in
    the wind."""
    _grass_blades(blades, rng, u, v, h * 0.7, count, h * 0.010, h * 0.35)
    for _ in range(heads):
        lean = rng.uniform(-0.10, 0.25) * h
        top = (u + lean, v - h * rng.uniform(0.85, 1.05))
        stem = _arch((u + rng.uniform(-0.01, 0.01) * h, v + 0.004), (u + lean * 0.2, top[1] + h * 0.3), top, 10)
        blades.line(stem, h * 0.007)
        # The plume: many thin spikes from the top of the stem that hang
        # out to the side the wind blows.
        x, y = top
        for j in range(7):
            length = h * rng.uniform(0.14, 0.22)
            ang = -70.0 + j * 9.0 + rng.uniform(-4.0, 4.0)
            end = polar(x, y, length, ang)
            end = (end[0], end[1] + length * 0.45)
            plumes.line(_arch((x, y), polar(x, y, length * 0.5, ang), end, 6), h * 0.012)


def history_taiwan(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = TAIWAN
    sun_at = (0.16, 0.40)
    beach_v = 0.672
    if layer_key == "sky":
        # A clear morning over the Pacific: the sun low over the sea at the
        # left, the far headlands of the coast at the right, each one paler
        # than the one in front, with clouds caught on their tops.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.85)), (0.24, p["top"]), (0.46, p["mid"]), (HORIZON - 0.01, p["low"]),
                                 (HORIZON, mix(p["low"], p["ocean"], 0.5)), (HORIZON + 0.012, p["ocean"]), (1.0, scale(p["ocean"], 0.85))]))
        _sun(a, layer, *sun_at, 0.024, p["sun"], p["glow"], 0.70)
        _heaps(a, layer, "taiwan heaps", ((0.36, 0.44, 0.05, 0.035), (0.08, 0.47, 0.035, 0.02)), p["cloud"], p["cloud_shadow"], 0.85)
        sea = (a.v > HORIZON + 0.002).astype(np.float32)
        a.light(layer, sea * smoothstep(0.60, 0.82, a.noise("taiwan sea lines", cells=50.0, octaves=2, stretch=12.0)), p["ocean_light"], 0.35)
        glitter = sea * a.spot(sun_at[0], HORIZON + 0.06, 0.12, 1.2, squash=0.55) * smoothstep(0.45, 0.70, a.noise("taiwan glitter", cells=90.0, octaves=2, stretch=10.0))
        a.light(layer, glitter, p["glow"], 0.75)
        above = smoothstep(HORIZON + 0.004, HORIZON + 0.001, a.v)
        cols = np.linspace(0.0, 1.0, a.n)
        for k, (u0, peak, pale) in enumerate(((0.38, 0.045, 0.52), (0.47, 0.068, 0.36), (0.56, 0.092, 0.20))):
            # Each headland: a cliff out of the sea at its left end, then a
            # ridge with sharp peaks that goes on to the right.
            fine = a.line_noise(("taiwan ridge peaks", k), cells=14.0, octaves=3)
            broad = a.line_noise(("taiwan ridge", k), cells=4.0, octaves=2)
            peaks = 1.0 - np.abs(fine * 2.0 - 1.0)
            rise = peak * np.clip((cols - u0) / 0.10, 0.0, 1.0) ** 0.40 * (0.50 + 0.30 * broad + 0.35 * peaks)
            top = np.where(cols >= u0, HORIZON + 0.003 - rise, 2.0).astype(np.float32)
            mask = _land(a, top) * above
            colour = mix(p["range"], p["mid"], pale)
            a.put(layer, mask, a.ramp([(0.0, colour), (HORIZON - peak, colour), (HORIZON - 0.004, mix(colour, p["low"], 0.40)), (1.0, colour)]))
            spurs = smoothstep(0.50, 0.80, a.noise(("taiwan far spurs", k), cells=60.0, octaves=2, stretch=0.5))
            a.shade(layer, mask * spurs, 0.10 * (1.0 - pale))
            a.light(layer, a.rim(mask, 0.005, 0.002, 1.0) * mask, mix(p["mountain_light"], p["glow"], 0.5), 0.45 * (1.0 - pale * 0.5))
            # The surf at the foot of the cliff where the headland meets the
            # sea.
            surf = a.band(HORIZON + 0.003, 0.003, 1.0) * smoothstep(u0 - 0.012, u0, a.u) * smoothstep(u0 + 0.05, u0 + 0.01, a.u)
            a.put(layer, surf * smoothstep(0.35, 0.60, a.noise(("taiwan far surf", k), cells=60.0, octaves=2, stretch=3.0)), p["surf"], 0.8 * (1.0 - pale * 0.5))
            a.tint(layer, mask * fog(a, ("taiwan peak cloud", k), HORIZON - peak * 0.70, 0.010, 3.0) * smoothstep(u0 + 0.08, u0 + 0.16, a.u), p["cloud"], 0.65)
        a.tint(layer, fog(a, "taiwan sea haze", HORIZON - 0.002, 0.010, 3.0), p["low"], 0.45)
        _textbook(a, layer, 0.06)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far taiwan")
        # The near mountain at the right: a high ridge with sharp tops that
        # comes down in a steep cliff to the sea at its left. Spurs come down
        # from the ridge toward the eye, one in front of the next, with deep
        # gullies between them.
        ridge_us = [0.600, 0.625, 0.660, 0.700, 0.750, 0.800, 0.850, 0.900, 0.950, 1.020]
        ridge_vs = [0.606, 0.560, 0.520, 0.500, 0.478, 0.452, 0.432, 0.446, 0.428, 0.440]
        fine = a.line_noise("taiwan mountain crest", cells=26.0, octaves=2)
        crest = _column_line(a, ridge_us, ridge_vs) - (1.0 - np.abs(fine * 2.0 - 1.0)) * 0.008
        crest = np.where(np.linspace(0.0, 1.0, a.n) >= 0.600, crest, 2.0).astype(np.float32)
        mountain = _land(a, crest)
        spurs = []
        for k, (top, ctrl, foot) in enumerate((((0.78, 0.462), (0.70, 0.470), (0.640, 0.612)), ((0.95, 0.455), (0.84, 0.500), (0.730, 0.634)),
                                              ((1.04, 0.520), (0.92, 0.540), (0.860, 0.638)))):
            img, pen = a.drawing()
            line = _arch(top, ctrl, foot, 24)
            jag = a.line_noise(("taiwan spur", k), cells=8.0, octaves=3)
            line = [(x, y - (float(jag[int(i / 24 * (a.n - 1))]) - 0.5) * 0.010 * math.sin(math.pi * i / 24)) for i, (x, y) in enumerate(line)]
            pen.poly(line + [(foot[0], 0.72), (1.05, 0.72), (1.05, top[1])])
            spurs.append(a.mask_of(img) * mountain)
        # The fan of land at the foot of the mountain, where the village is.
        fan_us = [0.56, 0.62, 0.70, 0.80, 0.92, 1.02]
        fan_vs = [0.668, 0.656, 0.646, 0.640, 0.632, 0.628]
        fan = _land(a, _column_line(a, fan_us, fan_vs)) * smoothstep(0.55, 0.58, a.u)

        def fan_at(u: float) -> float:
            return float(np.interp(u, fan_us, fan_vs))

        beach_line = _column_line(a, [0.20, 0.40, 0.70, 1.0], [beach_v + 0.012, beach_v + 0.004, beach_v - 0.002, beach_v - 0.004])
        beach = _land(a, beach_line) * smoothstep(0.18, 0.24, a.u + (a.v - beach_v) * 2.0)
        sea = smoothstep(HORIZON + 0.001, HORIZON + 0.004, a.v)
        # Rocks at the foot of the cliff with surf round them.
        rocks, rock_pen = a.drawing()
        for _ in range(9):
            u = rng.uniform(0.585, 0.635)
            v = HORIZON + 0.010 + (u - 0.585) * 0.6 + rng.uniform(0.0, 0.008)
            r = rng.uniform(0.003, 0.006)
            rock_pen.poly([(u - r * 1.3, v), (u - r * 0.6, v - r * 0.9), (u + r * 0.4, v - r * 1.1), (u + r * 1.3, v)])
        # Small terraces of millet climb the lower slope of the near spur:
        # long level strips, each held by a low wall of stones.
        fields, field_pen = a.drawing()
        walls, wall_pen = a.drawing()
        for row in range(5):
            v = 0.630 - row * 0.008
            x = 0.745 + row * 0.020 + rng.uniform(-0.006, 0.006)
            while x < 0.90 - row * 0.008:
                length = rng.uniform(0.020, 0.045)
                field_pen.poly([(x, v), (x + length, v), (x + length - 0.003, v - 0.005), (x + 0.003, v - 0.005)])
                wall_pen.line([(x, v), (x + length, v)], 0.0012)
                x += length + rng.uniform(0.008, 0.020)
        trees, tree_pen = a.drawing()
        for _ in range(60):
            u = rng.uniform(0.57, 1.02)
            if 0.74 < u < 0.90 and rng.random() < 0.7:
                continue
            v = fan_at(u) + rng.uniform(0.0, 0.006)
            r = rng.uniform(0.004, 0.008)
            tree_pen.ellipse(u, v - r * 0.6, r, r * 0.8)
        houses = {key: a.drawing() for key in ("posts", "walls", "roof")}
        for u, w in ((0.645, 0.012), (0.70, 0.014), (0.755, 0.011), (0.90, 0.013)):
            _stilt_house(houses["posts"][1], houses["walls"][1], houses["roof"][1], u, fan_at(u) + 0.012, w, w * 1.8)
        boats, boat_pen = a.drawing()
        strakes, strake_pen = a.drawing()
        _plank_canoe(boat_pen, strake_pen, 0.47, float(_at(beach_line, 0.47)) + 0.012, 0.070, 1.0)
        _plank_canoe(boat_pen, strake_pen, 0.56, float(_at(beach_line, 0.56)) + 0.013, 0.052, -1.0)
        rock_mask = a.mask_of(rocks)
        slope = spurs[1] * (1.0 - spurs[2])
        field_mask = a.mask_of(fields) * slope
        wall_mask = a.mask_of(walls) * slope
        tree_mask = a.mask_of(trees)
        hm = {key: a.mask_of(img) for key, (img, _) in houses.items()}
        boat_mask = np.maximum(a.mask_of(boats), a.mask_of(strakes))
        land = np.maximum.reduce([mountain, fan, beach, rock_mask, tree_mask, *hm.values(), boat_mask])
        mask = np.maximum(land, sea)
        layer = solid(a, mask, mix(p["ocean"], p["far"], 0.25), p["ocean"], HORIZON, 0.70, "taiwan far", 0.03)
        # The sea: deep blue, lit in long lines, with the glitter of the
        # sun and lines of surf that run in to the beach.
        a.light(layer, sea * smoothstep(0.58, 0.82, a.noise("taiwan swells", cells=60.0, octaves=2, stretch=12.0)), p["ocean_light"], 0.40)
        glitter = sea * a.spot(sun_at[0], 0.64, 0.16, 1.3, squash=0.6) * smoothstep(0.45, 0.72, a.noise("taiwan far glitter", cells=110.0, octaves=2, stretch=10.0))
        a.light(layer, glitter, p["glow"], 0.65)
        for k, dv in enumerate((0.004, 0.011, 0.020)):
            line = beach_line[None, :] - dv - 0.002 * k
            surf = smoothstep(0.0020, 0.0, np.abs(a.v - line)) * smoothstep(0.30, 0.55, a.noise(("taiwan surf", k), cells=40.0, octaves=3, stretch=4.0))
            a.put(layer, surf * sea * (1.0 - beach) * smoothstep(0.20, 0.30, a.u), p["surf"], 0.85 - k * 0.2)
        # The mountain: the far mass blue with the air; each spur in front
        # greener, lit along its crest, with a dark gully at its far side.
        a.put(layer, mountain, a.ramp([(0.0, mix(p["mountain_dark"], p["far"], 0.45)), (0.44, mix(p["mountain_dark"], p["far"], 0.40)), (HORIZON, mix(p["mountain_dark"], p["far"], 0.20)), (1.0, p["mountain_dark"])]))
        for k, spur in enumerate(spurs):
            depth = 0.30 - k * 0.12
            a.shade(layer, a.blur(np.clip(a.shift(spur, -0.005, 0.0) - spur, 0.0, 1.0), 4.0) * mountain, 0.18)
            a.put(layer, spur, a.ramp([(0.0, mix(p["mountain"], p["far"], depth + 0.10)), (0.46, mix(p["mountain"], p["far"], depth)), (HORIZON + 0.03, mix(p["mountain"], p["far"], depth * 0.5)), (1.0, p["mountain"])]))
            broken = smoothstep(0.30, 0.70, a.noise(("taiwan spur crest", k), cells=30.0, octaves=2))
            a.light(layer, a.rim(spur, 0.004, 0.004, 0.6) * spur * broken, mix(p["mountain_light"], p["glow"], 0.35), 0.40)
        canopy = smoothstep(0.55, 0.78, a.noise("taiwan canopy", cells=140.0, octaves=2))
        a.light(layer, mountain * canopy, p["mountain_light"], 0.18)
        a.shade(layer, mountain * smoothstep(0.62, 0.85, a.noise("taiwan ravines", cells=40.0, octaves=2, stretch=0.25)), 0.14)
        a.light(layer, a.rim(mountain, 0.007, 0.0, 1.0) * mountain, mix(p["mountain_light"], p["glow"], 0.4), 0.50)
        # Bare rock on the cliff where the mountain meets the sea.
        cliff = mountain * smoothstep(0.66, 0.61, a.u) * smoothstep(0.40, 0.60, a.noise("taiwan cliff rock", cells=40.0, octaves=3, stretch=0.4))
        a.put(layer, cliff, mix(p["cliff"], p["far"], 0.20), 0.75)
        a.light(layer, cliff * a.rim(mountain, 0.006, 0.0, 1.0), p["cliff_light"], 0.5)
        a.put(layer, field_mask, mix(p["millet"], p["terrace"], 0.25))
        a.light(layer, field_mask * smoothstep(0.5, 0.8, a.noise("taiwan millet", cells=90.0, octaves=2)), p["millet_light"], 0.35)
        a.put(layer, wall_mask, mix(p["cliff"], p["mountain_dark"], 0.3), 0.85)
        a.put(layer, fan, a.ramp([(0.0, p["grass"]), (0.62, mix(p["grass"], p["far"], 0.2)), (0.68, p["grass"]), (1.0, p["grass"])]))
        a.light(layer, fan * smoothstep(0.55, 0.75, a.noise("taiwan fan grass", cells=40.0, octaves=3, stretch=3.0)), p["grass_light"], 0.35)
        a.light(layer, a.rim(fan, 0.0, 0.003, 0.4) * fan, p["grass_light"], 0.40)
        a.put(layer, tree_mask, mix(p["mountain_dark"], p["mountain"], 0.4))
        a.light(layer, a.rim(tree_mask, 0.002, 0.002, 0.3) * tree_mask, p["mountain_light"], 0.45)
        # The beach of grey sand and small pebbles, wet and dark at the
        # water.
        a.put(layer, beach, a.ramp([(0.0, p["sand_light"]), (beach_v, p["sand_light"]), (beach_v + 0.03, p["sand"]), (1.0, p["sand"])]))
        a.shade(layer, beach * smoothstep(0.55, 0.80, a.noise("taiwan pebbles", cells=40.0, octaves=2, stretch=4.0)), 0.08)
        a.put(layer, a.rim(beach, 0.0, 0.003, 0.0) * beach, mix(p["sand"], p["ocean"], 0.35), 0.6)
        a.put(layer, rock_mask, p["rock"])
        a.light(layer, a.rim(rock_mask, 0.002, 0.002, 0.0) * rock_mask, p["cliff_light"], 0.5)
        foam = np.clip(a.blur(rock_mask, 3.0) * 2.0 - rock_mask, 0.0, 1.0) * sea * (1.0 - mountain)
        a.put(layer, foam * smoothstep(0.40, 0.65, a.noise("taiwan rock foam", cells=80.0, octaves=2)), p["surf"], 0.85)
        # The houses: posts and planks of wood and steep roofs of thatch lit
        # on the side to the sun.
        a.put(layer, hm["posts"], p["wood"])
        a.put(layer, hm["walls"], mix(p["wood"], p["thatch"], 0.35))
        roof = hm["roof"]
        a.put(layer, roof, p["thatch"])
        a.shade(layer, roof * smoothstep(0.3, 0.9, a.noise("taiwan thatch", cells=220.0, octaves=1, stretch=0.12)), 0.16)
        a.light(layer, a.rim(roof, 0.003, 0.0, 0.2) * roof, p["glow"], 0.55)
        a.shade(layer, a.rim(roof, -0.003, 0.0, 0.2) * roof, 0.25)
        bm = a.mask_of(boats)
        a.put(layer, bm, p["canoe"])
        a.light(layer, a.rim(bm, 0.0, 0.002, 0.0) * bm, p["sand_light"], 0.45)
        a.put(layer, a.mask_of(strakes) * bm, mix(p["canoe"], p["sand_light"], 0.35))
        a.tint(layer, fog(a, "taiwan sea mist", HORIZON + 0.004, 0.012, 3.0) * mask * (1.0 - mountain), p["low"], 0.35)
        haze(a, layer, p["low"], 0.06, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near taiwan")
        bank, ground, bank_at = _bank(a, "near taiwan", 0.030, 0.040)
        trunks, trunk_pen = a.drawing()
        leaves, leaf_pen = a.drawing()
        blades, blade_pen = a.drawing()
        plumes, plume_pen = a.drawing()
        rocks, rock_pen = a.drawing()
        # A pandanus on its prop roots at the left, with dark rocks at its
        # foot; silvergrass with pale plumes at the right. The middle is a
        # calm bank of grass over the beach.
        _pandanus(trunk_pen, leaf_pen, rng, 0.09, bank_at(0.09) + 0.004, 0.40, 0.06)
        for u, w in ((0.17, 0.028), (0.21, 0.018), (0.02, 0.030)):
            rock_pen.ellipse(u, bank_at(u) - w * 0.25, w, w * 0.55)
        for u, h in ((0.80, 0.14), (0.87, 0.19), (0.95, 0.16)):
            _silvergrass(blade_pen, plume_pen, rng, u, bank_at(u) + 0.004, h, 16, 5)
        for _ in range(14):
            u = rng.uniform(0.28, 0.72)
            _grass_blades(blade_pen, rng, u, bank_at(u) + 0.002, rng.uniform(0.012, 0.020), 5, 0.0012, 0.008)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        trunk_mask = a.mask_of(trunks)
        leaf_mask = a.mask_of(leaves)
        blade_mask = a.mask_of(blades)
        plume_mask = a.mask_of(plumes)
        rock_mask = a.mask_of(rocks)
        mask = np.maximum.reduce([bank_mask, trunk_mask, leaf_mask, blade_mask, plume_mask, rock_mask])
        layer = a.blank()
        earth = a.ramp([(0.0, mix(p["grass"], p["near"], 0.45)), (0.66, mix(p["grass"], p["near"], 0.45)), (0.80, mix(p["grass"], p["near"], 0.78)), (1.0, p["near"])])
        a.put(layer, bank_mask, earth)
        a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, p["glow"], 0.30)
        a.put(layer, rock_mask, mix(p["rock"], p["near"], 0.35))
        a.light(layer, a.rim(rock_mask, 0.004, 0.004, 0.4) * rock_mask, p["cliff_light"], 0.35)
        a.put(layer, trunk_mask, mix(p["trunk"], p["near"], 0.40))
        a.light(layer, a.rim(trunk_mask, 0.003, 0.0, 0.3) * trunk_mask, p["glow"], 0.35)
        a.put(layer, leaf_mask, mix(p["pandanus"], p["near"], 0.35))
        a.light(layer, a.rim(leaf_mask, 0.002, 0.002, 0.3) * leaf_mask, mix(p["pandanus_light"], p["glow"], 0.2), 0.40)
        a.put(layer, blade_mask, mix(p["grass"], p["near"], 0.35))
        a.light(layer, a.rim(blade_mask, 0.0015, 0.0, 0.2) * blade_mask, p["grass_light"], 0.35)
        a.put(layer, plume_mask, mix(p["plume"], p["near"], 0.15))
        a.shade(layer, a.rim(plume_mask, -0.002, -0.002, 0.3) * plume_mask, 0.25)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.20)
        haze(a, layer, p["low"], 0.06, None)
        return layer
    layer = _air(a, p, "taiwan sea air", p["low"], 0.16, scale(p["top"], 0.4), 0.18)
    a.put(layer, shafts(a, "taiwan shafts", 3, 0.16, 0.0, 0.80, 0.04), p["glow"], 0.07)
    return layer


def taiwan_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Silvergrass with plumes stands from below at two places, and the
    long strap leaves of a pandanus hang from above at one place."""
    del layer_lights
    rng = art_.rand("taiwan foreground")
    for k in range(2):
        u0 = 0.12 + (k + rng.uniform(0.2, 0.8)) * 0.38
        for _ in range(10):
            u = u0 + rng.uniform(-0.012, 0.012)
            top = REST_BOTTOM - rng.uniform(-0.004, 0.010)
            lean = rng.uniform(-0.04, 0.04)
            pen.line(_arch((u, 1.0), (u + lean * 0.3, top + 0.10), (u + lean, top), 10), 0.0015)
        for j in range(2):
            u = u0 + (j - 0.5) * 0.016
            top = (u + 0.006, REST_BOTTOM - 0.014)
            pen.line(_arch((u, 1.0), (u, top[1] + 0.12), top, 10), 0.0014)
            for i in range(6):
                end = polar(*top, rng.uniform(0.014, 0.020), -60.0 + i * 10.0)
                pen.line([top, (end[0], end[1] + 0.008)], 0.0016)
    u = rng.uniform(0.40, 0.60)
    stem = _arch((u - 0.03, 0.0), (u, 0.16), (u + 0.02, 0.26), 10)
    pen.line(stem, 0.0040)
    cx, cy = stem[-1]
    for j in range(9):
        ang = 15.0 + j * 150.0 / 8.0 + rng.uniform(-5.0, 5.0)
        length = rng.uniform(0.09, 0.13)
        tip = polar(cx, cy, length, ang)
        tip = (tip[0], min(0.386, tip[1] + length * 0.25))
        _leaf(pen, _arch((cx, cy), polar(cx, cy, length * 0.5, ang - 15.0), tip, 8), 0.0042, 0.4)


# ---------------------------------------------------------------------------
# Gyeongju: the capital of Silla in autumn
# ---------------------------------------------------------------------------


GYEONGJU = {
    "top": (96, 130, 172),
    "mid": (204, 198, 176),
    "low": (250, 226, 180),
    "glow": (255, 214, 142),
    "sun": (255, 242, 206),
    "cloud": (252, 236, 206),
    "cloud_shadow": (200, 172, 144),
    "namsan": (96, 106, 120),
    "namsan_forest": (70, 90, 76),
    "namsan_light": (204, 184, 156),
    "hills": (134, 140, 150),
    "grass": (106, 140, 62),
    "grass_light": (184, 188, 94),
    "grass_dark": (62, 94, 48),
    "field": (196, 172, 98),
    "bark": (200, 94, 56),
    "bark_dark": (118, 72, 52),
    "pine": (40, 66, 48),
    "pine_light": (100, 122, 70),
    "maple": (208, 56, 38),
    "maple_light": (242, 142, 62),
    "tile": (88, 90, 98),
    "tile_light": (168, 166, 162),
    "wall": (234, 224, 200),
    "column": (164, 62, 44),
    "stone": (182, 170, 146),
    "stone_light": (236, 220, 186),
    "stone_dark": (112, 100, 86),
    "far": (224, 210, 184),
    "near": (40, 32, 26),
    "near_light": (164, 122, 70),
}


def _red_pine(trunk: Pen, crown: Pen, rng, u: float, v: float, h: float, lean: float) -> None:
    """A Korean red pine: a slim trunk that bends and leans, bare to high
    up, and a crown of three or four flat dark layers like clouds over its
    top part, each layer on its own short limb, the widest at the bottom."""
    pts = []
    for t in np.linspace(0.0, 1.0, 10):
        wob = math.sin(t * 5.0 + u * 30.0) * h * 0.03 * t
        pts.append((u + lean * h * t**1.3 + wob, v + 0.004 - (h + 0.004) * t))
    trunk.line(pts, h * 0.030)
    layers = rng.randint(2, 3)
    for k in range(layers):
        t = 0.72 + 0.28 * k / (layers - 1)
        x0, y0 = pts[min(9, int(round(t * 9)))]
        side = (-1.0 if k % 2 else 1.0) * rng.uniform(0.3, 1.0)
        rx = h * (0.40 - 0.16 * k / (layers - 1)) * rng.uniform(0.85, 1.15)
        cx, cy = x0 + side * rx * 0.35, y0 - h * 0.02
        trunk.line([(x0, y0 + h * 0.04), (cx, cy + h * 0.01)], h * 0.016)
        for _ in range(12):
            s = rng.uniform(-1.0, 1.0)
            crown.ellipse(cx + s * rx * 0.8, cy - h * 0.035 * (1.0 - abs(s)) + rng.uniform(-0.012, 0.012) * h, rx * rng.uniform(0.22, 0.36), h * rng.uniform(0.040, 0.060))


def _mound(pen: Pen, u: float, v: float, w: float, h: float) -> None:
    """A royal tomb of Silla: a smooth round mound of earth under grass,
    wide and a little flat on the top."""
    pen.poly([(u + w * math.cos(t), v + 0.002 - h * math.sin(t) ** 0.75) for t in np.linspace(math.pi, 0.0, 40)])


def _hall(walls: Pen, columns: Pen, roof: Pen, ridge: Pen, base: Pen, u: float, v: float, w: float, h: float) -> None:
    """A hall of the palace on a platform of stone: white walls between red
    columns, and a roof of grey tiles. The eaves reach far out and turn up
    at the corners, and a ridge of tiles runs along its top with its two
    ends turned up."""
    base.rect(u - w * 1.10, v - h * 0.14, u + w * 1.10, v + 0.002)
    wall_top = v - h * 0.55
    walls.rect(u - w * 0.88, wall_top, u + w * 0.88, v - h * 0.14)
    for k in range(7):
        x = u - w * 0.88 + k * w * 1.76 / 6.0
        columns.line([(x, v - h * 0.14), (x, wall_top)], w * 0.05)
    # The roof: the eave line sags in the middle and sweeps up at the ends.
    eave = _arch((u - w * 1.38, wall_top - h * 0.22), (u, wall_top + h * 0.10), (u + w * 1.38, wall_top - h * 0.22), 14)
    top = v - h * 1.05
    roof.poly(eave + [(u + w * 0.78, top), (u - w * 0.78, top)])
    ridge.line([(u - w * 0.86, top - h * 0.08), (u - w * 0.74, top), (u + w * 0.74, top), (u + w * 0.86, top - h * 0.08)], h * 0.07)


def _cheomseongdae(stone: Pen, window: Pen, u: float, v: float, h: float) -> None:
    """Cheomseongdae, the tower of granite where the sky was watched: a
    square base of two steps, a body like a bottle that is wide at the
    bottom and slim at the top, a small square window half up its side, and
    a square frame of long stones on its top."""
    stone.rect(u - h * 0.31, v - h * 0.04, u + h * 0.31, v + 0.001)
    stone.rect(u - h * 0.29, v - h * 0.08, u + h * 0.29, v - h * 0.04)
    body = []
    for t in np.linspace(0.0, 1.0, 16):
        half = h * (0.27 - 0.13 * t**0.8)
        body.append((half, v - h * 0.08 - h * 0.80 * t))
    stone.poly([(u - x, y) for x, y in body] + [(u + x, y) for x, y in body[::-1]])
    # The frame on the top: two layers of long stones laid in a square.
    stone.rect(u - h * 0.17, v - h * 0.94, u + h * 0.17, v - h * 0.88)
    stone.rect(u - h * 0.17, v - h * 1.00, u + h * 0.17, v - h * 0.95)
    window.rect(u - h * 0.11, v - h * 0.945, u + h * 0.11, v - h * 0.935)
    window.rect(u - h * 0.055, v - h * 0.56, u + h * 0.055, v - h * 0.45)


def _maple_leaf(pen: Pen, u: float, v: float, s: float, turn: float) -> None:
    """A maple leaf: five pointed lobes from one point, the middle one the
    longest, and a short stalk."""
    pts = []
    for k in range(5):
        ang = turn - 90.0 + (k - 2) * 52.0
        reach = s * (1.0 if k == 2 else 0.85 if k in (1, 3) else 0.6)
        pts.append(polar(u, v, reach, ang))
        pts.append(polar(u, v, s * 0.35, ang + 26.0))
    pen.poly([pts[-1]] + pts[:-1])
    pen.line([(u, v), polar(u, v, s * 0.5, turn + 90.0)], s * 0.08)


def _maple_tier(pen: Pen, rng, u: float, v: float, rx: float, ry: float) -> None:
    """A tier of maple foliage: a wide, a little flat mass, with a ragged
    edge of small pointed leaves that stand out from it."""
    pen.ellipse(u, v, rx * 0.90, ry * 0.80)
    for _ in range(int(rx * 1000.0)):
        ang = rng.uniform(0.0, math.tau)
        r = rng.uniform(0.80, 1.02)
        x, y = u + math.cos(ang) * rx * r, v + math.sin(ang) * ry * r
        _maple_leaf(pen, x, y, rng.uniform(0.008, 0.013), math.degrees(ang) + 90.0 + rng.uniform(-25.0, 25.0))


def history_gyeongju(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = GYEONGJU
    sun_at = (0.80, 0.36)
    if layer_key == "sky":
        # A gold afternoon of autumn. Namsan, the low mountain of granite
        # and pine, lies long behind the city; lower hills are far off at
        # the right.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.85)), (0.24, p["top"]), (0.46, p["mid"]), (HORIZON - 0.01, p["low"]),
                                 (HORIZON + 0.002, mix(p["grass"], p["far"], 0.55)), (1.0, mix(p["grass"], p["far"], 0.40))]))
        _sun(a, layer, *sun_at, 0.022, p["sun"], p["glow"], 0.70)
        streaks = smoothstep(0.55, 0.80, a.noise("gyeongju streaks", cells=6.0, octaves=3, stretch=14.0)) * a.band(0.42, 0.08, 1.2)
        a.light(layer, streaks, p["cloud"], 0.40)
        hills, _ = a.ridge("gyeongju east hills", HORIZON - 0.016, 0.010, cells=4.0, octaves=4)
        above = smoothstep(HORIZON + 0.004, HORIZON + 0.001, a.v)
        hills = hills * smoothstep(0.52, 0.62, a.u) * above
        colour = mix(p["hills"], p["mid"], 0.50)
        a.put(layer, hills, a.ramp([(0.0, colour), (HORIZON - 0.03, colour), (HORIZON, mix(colour, p["low"], 0.55)), (1.0, p["low"])]))
        a.light(layer, a.rim(hills, -0.006, 0.0, 1.5) * hills, p["glow"], 0.35)
        # Namsan: a long ridge with a few rounded tops and knobs of bare
        # granite, forest on its slopes. The light is from the right.
        us = np.linspace(-0.04, 0.70, 80)
        bumps = ((0.10, 0.040, 0.07), (0.22, 0.070, 0.06), (0.30, 0.080, 0.05), (0.40, 0.064, 0.06), (0.52, 0.040, 0.06))
        rise = np.array([0.008 + sum(hgt * math.exp(-(((x - c) / wd) ** 2)) for c, hgt, wd in bumps) for x in us])
        rise *= smoothstep(0.70, 0.58, us)
        ln = a.line_noise("namsan crags", cells=24.0, octaves=2)
        top = _column_line(a, us, HORIZON + 0.003 - rise) - (ln - 0.5) * 0.004
        namsan = _land(a, top) * smoothstep(0.70, 0.67, a.u) * above
        colour = mix(p["namsan"], p["mid"], 0.30)
        a.put(layer, namsan, a.ramp([(0.0, colour), (HORIZON - 0.08, colour), (HORIZON - 0.004, mix(colour, p["low"], 0.50)), (1.0, p["low"])]))
        forest = namsan * smoothstep(0.40, 0.70, a.noise("namsan forest", cells=120.0, octaves=2))
        a.put(layer, forest, mix(p["namsan_forest"], p["mid"], 0.35), 0.35)
        crags = namsan * smoothstep(0.76, 0.86, a.noise("namsan granite", cells=90.0, octaves=2, stretch=0.6)) * smoothstep(HORIZON - 0.02, HORIZON - 0.05, a.v)
        a.light(layer, crags, p["namsan_light"], 0.30)
        a.light(layer, a.rim(namsan, -0.007, 0.0, 1.5) * namsan, mix(p["namsan_light"], p["glow"], 0.4), 0.45)
        a.tint(layer, fog(a, "gyeongju low haze", HORIZON - 0.006, 0.018, 3.0), p["low"], 0.60)
        _textbook(a, layer, 0.09)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far gyeongju")
        _, pline = a.ridge("gyeongju plain", HORIZON + 0.006, 0.002, cells=4.0, octaves=2)
        plain = _land(a, pline)
        # The low hill of the palace at the left: a long, low crescent with
        # trees along its edge and halls on its top.
        hill, hill_pen = a.drawing()
        hill_pen.poly([(0.06, HORIZON + 0.022)] + [(0.24 + 0.17 * math.cos(t), HORIZON + 0.008 - 0.012 * math.sin(t) ** 0.6) for t in np.linspace(math.pi, 0.0, 24)] + [(0.42, HORIZON + 0.022)])
        hall = {key: a.drawing() for key in ("walls", "columns", "roof", "ridge", "base")}
        for u, v, w, h in ((0.24, HORIZON - 0.002, 0.040, 0.034), (0.14, HORIZON + 0.002, 0.024, 0.024), (0.33, HORIZON + 0.001, 0.026, 0.026)):
            _hall(*(hall[k][1] for k in ("walls", "columns", "roof", "ridge", "base")), u, v, w, h)
        # The tomb mounds: big ones near, smaller ones far, and one of two
        # mounds joined, as the tombs of a king and a queen are.
        mounds, mound_pen = a.drawing()
        for u, v, w, h in ((0.47, 0.618, 0.022, 0.012), (0.60, 0.622, 0.030, 0.016), (0.08, 0.640, 0.040, 0.020), (0.68, 0.652, 0.072, 0.038),
                           (0.85, 0.640, 0.048, 0.030), (0.92, 0.643, 0.046, 0.026), (0.97, 0.622, 0.024, 0.012), (0.36, 0.662, 0.036, 0.018),
                           (0.53, 0.610, 0.014, 0.007), (0.78, 0.612, 0.018, 0.009), (0.17, 0.694, 0.060, 0.030), (0.52, 0.700, 0.050, 0.024)):
            _mound(mound_pen, u, v, w, h)
        tower, tower_pen = a.drawing()
        window, window_pen = a.drawing()
        _cheomseongdae(tower_pen, window_pen, 0.545, 0.628, 0.050)
        # Red pines in groves among the mounds, and a few maples in red.
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        maples, maple_pen = a.drawing()
        for gu, gv, gh, count in ((0.44, 0.640, 0.055, 3), (0.60, 0.646, 0.050, 2), (0.79, 0.664, 0.075, 4), (0.995, 0.660, 0.070, 2),
                                  (0.03, 0.664, 0.065, 3), (0.17, 0.670, 0.060, 2), (0.29, 0.678, 0.075, 3), (0.64, 0.618, 0.035, 3), (0.50, 0.622, 0.030, 2)):
            for _ in range(count):
                u = gu + rng.uniform(-0.025, 0.025)
                v = gv + rng.uniform(-0.004, 0.006)
                _red_pine(trunk_pen, crown_pen, rng, u, v, gh * rng.uniform(0.75, 1.15), rng.uniform(-0.15, 0.15))
        # Far groves along the foot of the plain: pines, and maples and
        # zelkovas that the autumn turns red and gold.
        _canopy(maple_pen, rng, pline, 0.40, 1.02, 0.004, 0.004, 0.009, 140)
        _canopy(maple_pen, rng, np.full(a.n, HORIZON + 0.010, dtype=np.float32), 0.04, 0.44, 0.003, 0.004, 0.008, 80)
        plain_mask = plain
        hill_mask = a.mask_of(hill)
        hm = {key: a.mask_of(img) for key, (img, _) in hall.items()}
        mound_mask = a.mask_of(mounds)
        tower_mask = a.mask_of(tower)
        window_mask = a.mask_of(window) * tower_mask
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        maple_mask = a.mask_of(maples)
        mask = np.maximum.reduce([plain_mask, hill_mask, *hm.values(), mound_mask, tower_mask, trunk_mask, crown_mask, maple_mask])
        layer = solid(a, mask, mix(p["grass"], p["far"], 0.40), p["grass"], HORIZON, 0.70, "gyeongju far", 0.05)
        # The plain: grass that the autumn turns gold in patches, and
        # harvested fields far off.
        a.put(layer, plain * smoothstep(0.50, 0.80, a.noise("gyeongju fields", cells=16.0, octaves=2, stretch=6.0)), mix(p["field"], p["far"], 0.25), 0.40)
        a.light(layer, plain * smoothstep(0.50, 0.80, a.noise("gyeongju grass", cells=30.0, octaves=2, stretch=5.0)), p["grass_light"], 0.20)
        a.put(layer, hill_mask, mix(p["grass_dark"], p["far"], 0.35))
        a.light(layer, a.rim(hill_mask, -0.004, 0.003, 0.5) * hill_mask, p["grass_light"], 0.35)
        # The mounds: smooth green, lit on the side to the sun and in shade
        # on the other side, with a dark line at their feet.
        a.put(layer, mound_mask, a.ramp([(0.0, mix(p["grass"], p["far"], 0.25)), (0.61, mix(p["grass"], p["far"], 0.25)), (0.66, p["grass"]), (1.0, p["grass"])]))
        lit = a.blur(np.clip(mound_mask - a.shift(mound_mask, -0.012, 0.004), 0.0, 1.0), 6.0) * mound_mask
        a.light(layer, lit, mix(p["grass_light"], p["glow"], 0.35), 0.65)
        dark = a.blur(np.clip(mound_mask - a.shift(mound_mask, 0.012, 0.0), 0.0, 1.0), 6.0) * mound_mask
        a.shade(layer, dark, 0.25)
        a.shade(layer, a.rim(mound_mask, 0.0, -0.002, 0.3) * mound_mask, 0.0)
        # The palace: a platform of grey stone, white walls between red
        # columns, and dark tile roofs with lit ridges.
        a.put(layer, hm["base"], mix(p["stone"], p["far"], 0.20))
        a.put(layer, hm["walls"], mix(p["wall"], p["far"], 0.10))
        a.put(layer, hm["columns"] * hm["walls"], p["column"], 0.85)
        a.put(layer, hm["roof"], mix(p["tile"], p["far"], 0.15))
        a.shade(layer, hm["roof"] * np.clip(1.0 - np.abs(((a.u * 700.0) % 1.0) - 0.5) / 0.2, 0.0, 1.0), 0.18)
        a.light(layer, a.rim(hm["roof"], -0.002, 0.0, 0.0) * hm["roof"], p["tile_light"], 0.55)
        a.put(layer, a.shift(hm["roof"], 0.0, 0.004) * hm["walls"] * (1.0 - hm["roof"]), p["tile"], 0.5)
        a.put(layer, hm["ridge"], mix(p["tile"], p["stone_dark"], 0.4))
        a.light(layer, a.rim(hm["ridge"], 0.0, 0.001, 0.0) * hm["ridge"], p["tile_light"], 0.5)
        # Cheomseongdae: pale granite, lit on the right, the window dark.
        a.put(layer, tower_mask, p["stone"])
        courses = np.clip(1.0 - np.abs(((a.v * 900.0) % 1.0) - 0.5) / 0.12, 0.0, 1.0)
        a.shade(layer, tower_mask * courses, 0.14)
        a.light(layer, a.rim(tower_mask, -0.003, 0.0, 0.0) * tower_mask, p["stone_light"], 0.65)
        a.shade(layer, a.rim(tower_mask, 0.003, 0.0, 0.0) * tower_mask, 0.25)
        a.put(layer, window_mask, p["stone_dark"], 0.9)
        # The red pines: orange-red trunks and flat dark crowns lit at their
        # tops; the maples scarlet.
        a.put(layer, trunk_mask, mix(p["bark"], p["far"], 0.15))
        a.put(layer, crown_mask, a.ramp([(0.0, mix(p["pine"], p["far"], 0.40)), (HORIZON, mix(p["pine"], p["far"], 0.30)), (0.70, p["pine"]), (1.0, p["pine"])]))
        a.light(layer, a.rim(crown_mask, -0.002, 0.003, 0.3) * crown_mask, mix(p["pine_light"], p["glow"], 0.3), 0.50)
        a.put(layer, maple_mask, mix(p["pine"], p["far"], 0.35))
        reds = maple_mask * smoothstep(0.66, 0.76, a.noise("gyeongju far maples", cells=40.0, octaves=2))
        golds = maple_mask * smoothstep(0.70, 0.80, a.noise("gyeongju far zelkovas", cells=36.0, octaves=2))
        a.put(layer, reds, mix(p["maple"], p["far"], 0.30), 0.85)
        a.put(layer, golds, mix(p["field"], p["far"], 0.20), 0.75)
        a.light(layer, a.rim(maple_mask, -0.002, 0.002, 0.3) * maple_mask, mix(p["pine_light"], p["glow"], 0.4), 0.45)
        a.tint(layer, fog(a, "gyeongju plain haze", HORIZON + 0.004, 0.012, 3.0) * mask, p["low"], 0.45)
        haze(a, layer, p["low"], 0.06, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near gyeongju")
        bank, ground, bank_at = _bank(a, "near gyeongju", 0.030, 0.034)
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        limbs, limb_pen = a.drawing()
        maples, maple_pen = a.drawing()
        fallen, fallen_pen = a.drawing()
        grass, grass_pen = a.drawing()
        # Two red pines that lean at the left; a maple in full red at the
        # right; red leaves fallen in the grass. The middle is calm.
        for u, h, lean in ((0.06, 0.40, 0.10), (0.15, 0.32, -0.18)):
            _red_pine(trunk_pen, crown_pen, rng, u, bank_at(u) + 0.006, h, lean)
        # The maple: three wide, flat tiers of leaves, the widest at the
        # bottom, on limbs that show dark in the gaps between them.
        _limbs(limb_pen, rng, 0.90, bank_at(0.90) + 0.006, 0.31, 0.012, -0.01, 4)
        tiers = []
        for cu, cv, rx, ry in ((0.905, 0.300, 0.070, 0.020), (0.890, 0.338, 0.100, 0.024), (0.905, 0.378, 0.115, 0.024)):
            img, pen = a.drawing()
            _maple_tier(pen, rng, cu, cv, rx, ry)
            tiers.append(a.mask_of(img))
            for _ in range(5):
                gu = cu + rng.uniform(-0.7, 0.7) * rx
                maple_pen.ellipse(gu, cv + ry * rng.uniform(0.2, 0.6), rng.uniform(0.004, 0.008), rng.uniform(0.002, 0.004))
        for _ in range(24):
            u = rng.uniform(0.70, 1.0) if rng.random() < 0.7 else rng.uniform(0.25, 0.70)
            _maple_leaf(fallen_pen, u, bank_at(u) + rng.uniform(0.004, 0.030), rng.uniform(0.005, 0.008), rng.uniform(-90.0, 90.0))
        for _ in range(16):
            u = rng.uniform(0.26, 0.74)
            _grass_blades(grass_pen, rng, u, bank_at(u) + 0.002, rng.uniform(0.010, 0.018), 6, 0.0011, 0.008)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        limb_mask = a.mask_of(limbs)
        maple_mask = np.maximum.reduce(tiers)
        gap_mask = a.mask_of(maples) * maple_mask
        fallen_mask = a.mask_of(fallen) * bank_mask
        grass_mask = a.mask_of(grass)
        mask = np.maximum.reduce([bank_mask, trunk_mask, crown_mask, limb_mask, maple_mask, grass_mask])
        layer = a.blank()
        earth = a.ramp([(0.0, mix(p["grass_dark"], p["near"], 0.35)), (0.66, mix(p["grass_dark"], p["near"], 0.35)), (0.80, mix(p["grass_dark"], p["near"], 0.75)), (1.0, p["near"])])
        a.put(layer, bank_mask, earth)
        a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, p["glow"], 0.30)
        a.put(layer, grass_mask, mix(p["grass"], p["near"], 0.40))
        a.light(layer, a.rim(grass_mask, -0.0015, 0.0, 0.2) * grass_mask, p["grass_light"], 0.30)
        a.put(layer, fallen_mask, mix(p["maple"], p["near"], 0.35), 0.85)
        # The pines: the bark is orange-red and in plates high up, and grey
        # and dark low down. The crowns are dark, lit on their tops.
        bark = a.ramp([(0.0, mix(p["bark"], p["near"], 0.15)), (0.50, mix(p["bark"], p["near"], 0.20)), (0.66, mix(p["bark_dark"], p["near"], 0.35)), (1.0, p["near"])])
        a.put(layer, trunk_mask, bark)
        plates = smoothstep(0.50, 0.78, a.noise("gyeongju pine plates", cells=160.0, octaves=1, stretch=0.4))
        a.shade(layer, trunk_mask * plates, 0.25)
        a.light(layer, a.rim(trunk_mask, -0.003, 0.0, 0.3) * trunk_mask, p["glow"], 0.45)
        a.put(layer, crown_mask, mix(p["pine"], p["near"], 0.40))
        a.light(layer, crown_mask * smoothstep(0.55, 0.80, a.noise("gyeongju needles", cells=420.0, octaves=1, stretch=3.0)), p["pine_light"], 0.14)
        a.light(layer, a.rim(crown_mask, -0.002, 0.004, 0.4) * crown_mask, mix(p["pine_light"], p["glow"], 0.3), 0.45)
        a.put(layer, limb_mask, mix(p["bark_dark"], p["near"], 0.45))
        # The maple: scarlet, with orange where the light comes through.
        # The maple: scarlet, with patches of orange and a little gold. Each
        # tier is lit on its top and dark under it; the top tier is painted
        # first, so the tier under it covers its shaded underside.
        orange = smoothstep(0.50, 0.66, a.noise("gyeongju maple orange", cells=30.0, octaves=2))
        gold = smoothstep(0.72, 0.82, a.noise("gyeongju maple gold", cells=36.0, octaves=2))
        for k, tier in enumerate(tiers):
            a.put(layer, tier, mix(p["maple"], p["near"], 0.30 - k * 0.04))
            a.put(layer, tier * orange, mix(p["maple_light"], p["near"], 0.30), 0.75)
            a.put(layer, tier * gold, mix(p["field"], p["near"], 0.20), 0.70)
            a.shade(layer, a.rim(tier, 0.0, -0.010, 1.0) * tier, 0.40)
            a.light(layer, a.rim(tier, -0.002, 0.005, 0.5) * tier, p["maple_light"], 0.40)
        branch_gaps = np.maximum(gap_mask, limb_mask * maple_mask * smoothstep(0.55, 0.70, a.noise("gyeongju maple gaps", cells=40.0, octaves=2)))
        a.put(layer, branch_gaps, mix(p["bark_dark"], p["near"], 0.55), 0.85)
        a.shade(layer, a.rim(mask, 0.004, -0.003, 1.0) * mask, 0.20)
        haze(a, layer, p["low"], 0.07, None)
        return layer
    layer = _air(a, p, "gyeongju autumn air", p["low"], 0.22, scale(p["near"], 0.8), 0.20)
    a.put(layer, shafts(a, "gyeongju shafts", 4, -0.16, 0.0, 0.85, 0.05), p["glow"], 0.09)
    return layer


def gyeongju_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Grass stands from below at two places. A spray of pine needles hangs
    from above at one place, and a twig of maple at another."""
    del layer_lights
    rng = art_.rand("gyeongju foreground")
    for k in range(2):
        u0 = 0.12 + (k + rng.uniform(0.2, 0.8)) * 0.38
        for _ in range(11):
            u = u0 + rng.uniform(-0.012, 0.012)
            top = REST_BOTTOM - rng.uniform(-0.004, 0.010)
            lean = rng.uniform(-0.04, 0.04)
            pen.line(_arch((u, 1.0), (u + lean * 0.3, top + 0.10), (u + lean, top), 10), 0.0015)
    # The pine: a bough that comes down from above, with tufts of long
    # needles along it.
    u = rng.uniform(0.22, 0.34)
    bough = _arch((u - 0.05, 0.0), (u, 0.20), (u + 0.10, 0.31), 12)
    pen.line(bough, 0.0032)
    for x, y in bough[4::2]:
        for j in range(9):
            end = polar(x, y, 0.028, 40.0 + j * 12.0 + rng.uniform(-4.0, 4.0))
            pen.line([(x, y), (end[0], min(end[1], 0.384))], 0.0011)
    # The maple: a thin twig with five leaves that hang from it.
    u = rng.uniform(0.66, 0.78)
    twig = _arch((u + 0.03, 0.0), (u, 0.20), (u - 0.05, 0.30), 10)
    pen.line(twig, 0.0020)
    for i in (5, 7, 8, 9, 10):
        x, y = twig[i]
        s = 0.016
        cy = min(y + s * 0.9, 0.384 - s)
        pen.line([(x, y), (x, cy + s * 0.5)], 0.0010)
        _maple_leaf(pen, x, cy, s, 180.0 + rng.uniform(-25.0, 25.0))


# ---------------------------------------------------------------------------
# Parts of the three rooms of the capitals: Hangzhou, Heian-kyo and Hanyang
# ---------------------------------------------------------------------------


def _upturned(pen: Pen, u0: float, u1: float, v: float, lift: float, thick: float, sag: float = 0.0, power: float = 3.0) -> None:
    """The edge of a tiled roof from `u0` to `u1` at `v`: its ends turn up by
    `lift`, and its middle sags by `sag`. `thick` is the depth of the edge."""
    n = 24
    top = []
    for i in range(n + 1):
        t = i / n
        x = u0 + (u1 - u0) * t
        top.append((x, v - lift * abs(2.0 * t - 1.0) ** power + sag * math.sin(math.pi * t)))
    pen.poly(top + [(x, y + thick) for x, y in reversed(top)])


def _hip_gable_roof(roof: Pen, u: float, v: float, half: float, h: float, lift: float, sag: float = 0.0) -> None:
    """A hipped-and-gabled roof seen from the front: an upturned eave from
    `u - half` to `u + half` at `v`, a slope up to a ridge `h` higher, and a
    small gable under each end of the ridge."""
    _upturned(roof, u - half, u + half, v, lift, h * 0.16, sag)
    roof.poly([(u - half * 0.97, v + h * 0.02 - lift * 0.8), (u - half * 0.80, v + h * 0.06), (u + half * 0.80, v + h * 0.06), (u + half * 0.97, v + h * 0.02 - lift * 0.8),
               (u + half * 0.60, v - h * 0.62), (u + half * 0.56, v - h), (u - half * 0.56, v - h), (u - half * 0.60, v - h * 0.62)])


def _reflected(a: Art, mask: np.ndarray, water_v: float, tag: str, water: np.ndarray) -> np.ndarray:
    """The picture of `mask` in still water under the level `water_v`,
    broken a little by the wind and kept to the `water`."""
    return _ripple(a, tag, _reflect(a, mask, water_v)) * water


# ---------------------------------------------------------------------------
# Hangzhou: West Lake on a morning of spring
# ---------------------------------------------------------------------------


HANGZHOU = {
    "top": (118, 158, 186),
    "mid": (196, 212, 208),
    "low": (238, 236, 220),
    "glow": (255, 240, 204),
    "sun": (255, 250, 234),
    "cloud": (250, 250, 244),
    "hills": (110, 140, 132),
    "water": (84, 148, 132),
    "water_light": (196, 226, 212),
    "water_deep": (52, 108, 98),
    "forest": (62, 104, 64),
    "forest_light": (138, 176, 94),
    "tea": (96, 150, 64),
    "tea_light": (172, 206, 108),
    "tea_row": (52, 92, 52),
    "willow": (132, 174, 72),
    "willow_light": (204, 222, 124),
    "willow_dark": (70, 108, 52),
    "peach": (236, 170, 172),
    "trunk": (86, 70, 56),
    "stone": (172, 168, 156),
    "stone_light": (230, 226, 212),
    "stone_dark": (104, 102, 98),
    "tile": (84, 88, 96),
    "tile_light": (158, 162, 166),
    "wall": (232, 226, 210),
    "brick": (190, 140, 96),
    "brick_light": (232, 196, 146),
    "eave": (66, 62, 64),
    "red": (180, 52, 40),
    "hull": (108, 76, 52),
    "mat": (178, 150, 100),
    "lotus": (66, 116, 68),
    "lotus_light": (152, 188, 108),
    "lotus_pink": (236, 152, 164),
    "far": (214, 224, 218),
    "near": (28, 42, 36),
    "near_light": (120, 140, 96),
}

#: The level of the far shore of West Lake, and of the causeway across it.
HANGZHOU_SHORE = 0.610
HANGZHOU_CAUSEWAY = 0.633
#: The level of the quay of the city at the right, near the eye.
HANGZHOU_QUAY = 0.664


def _leifeng(body: Pen, eaves: Pen, doors: Pen, u: float, v: float, w: float, h: float, storeys: int = 5) -> None:
    """Leifeng Pagoda as the Song knew it: an octagonal tower of brick on a
    low base, with eaves of wood and tile at each of its five storeys, each
    storey a little narrower than the one under it, and a short spire with
    rings on its top. `w` is the width of the lowest storey, and `h` the
    height to the top of the spire."""
    base = h * 0.05
    body.rect(u - w * 0.72, v - base, u + w * 0.72, v + 0.004)
    y = v - base
    s = h * 0.74 / storeys
    for k in range(storeys):
        half = w * 0.5 * (1.0 - 0.085 * k)
        wall_top = y - s * 0.70
        body.rect(u - half, wall_top, u + half, y + 0.001)
        doors.ellipse(u, y - s * 0.40, half * 0.17, s * 0.10)
        doors.rect(u - half * 0.17, y - s * 0.40, u + half * 0.17, y - s * 0.06)
        reach = half * 1.60
        eave_v = wall_top + s * 0.08
        eaves.poly([(u - reach * 0.96, eave_v), (u + reach * 0.96, eave_v), (u + half * 0.86, y - s), (u - half * 0.86, y - s)])
        _upturned(eaves, u - reach, u + reach, eave_v, s * 0.20, s * 0.10)
        y -= s
    # The top: a low roof of eight sides, and a spire with rings.
    half = w * 0.5 * (1.0 - 0.085 * storeys)
    eaves.poly([(u - half * 1.25, y + 0.001), (u + half * 1.25, y + 0.001), (u + half * 0.20, y - h * 0.065), (u - half * 0.20, y - h * 0.065)])
    body.line([(u, y - h * 0.05), (u, v - h)], w * 0.05)
    for j in range(4):
        body.ellipse(u, y - h * (0.085 + j * 0.034), w * (0.085 - j * 0.010), w * 0.022)


def _willow(trunk: Pen, crown: Pen, rng, u: float, v: float, h: float, w: float) -> None:
    """A weeping willow far off: a short trunk, a round head, and a curtain
    of long fronds that hangs from it almost to the ground, ragged at its
    foot."""
    lean = rng.uniform(-0.2, 0.2) * w
    top = (u + lean, v - h * 0.70)
    trunk.line([(u, v + 0.002), top], w * 0.10)
    cu, cv = top[0], v - h * 0.84
    crown.ellipse(cu, cv, w * 0.36, h * 0.16)
    # The curtain: it spreads out and down from the head like a fountain.
    left = [(cu - w * 0.36 * (1.0 - t) - w * 0.50 * t**0.7, cv + (v - h * 0.12 - cv) * t) for t in np.linspace(0.0, 1.0, 8)]
    right = [(cu + w * 0.36 * (1.0 - t) + w * 0.50 * t**0.7, cv + (v - h * 0.12 - cv) * t) for t in np.linspace(0.0, 1.0, 8)]
    hem = []
    for i in range(11):
        t = i / 10.0
        hem.append((cu + (t - 0.5) * w * 1.7, v - h * (0.06 + 0.16 * rng.random()) + h * 0.06 * abs(t - 0.5)))
    crown.poly(left + hem[1:-1] + right[::-1])
    for x, y in hem[1:-1]:
        crown.line([(x, y - h * 0.10), (x + rng.uniform(-0.05, 0.05) * w, y + h * rng.uniform(0.0, 0.06))], w * 0.06)


def _hump_bridge(stone: Pen, hole: Pen, u: float, v: float, w: float, h: float) -> None:
    """An arched stone bridge of the causeway: a deck that rises in a hump
    over one round arch. The water fills the lower half of the arch, so the
    arch and its picture in the water make a ring."""
    top = _arch((u - w, v - h * 0.20), (u, v - h * 1.85), (u + w, v - h * 0.20), 14)
    stone.poly([(u - w * 1.20, v + 0.001)] + top + [(u + w * 1.20, v + 0.001)])
    hole.ellipse(u, v + 0.0005, w * 0.40, h * 0.60)


def _pleasure_boat(hull: Pen, cabin: Pen, roof: Pen, posts: Pen, u: float, v: float, s: float, facing: float = 1.0) -> None:
    """A pleasure boat of West Lake: a long low hull, a cabin with open sides
    between red posts, and a roof of dark tiles whose ends turn up. `s` is
    its length and `(u, v)` the middle of its waterline."""
    f = facing

    def at(x: float, y: float) -> tuple[float, float]:
        return (u + f * x * s, v - y * s)

    hull.poly([at(-0.54, 0.11), at(-0.44, 0.03), at(-0.34, -0.006), at(0.36, -0.006), at(0.47, 0.03), at(0.55, 0.12), at(0.44, 0.075), at(-0.42, 0.070)])
    cabin.poly([at(-0.30, 0.07), at(0.26, 0.07), at(0.26, 0.23), at(-0.30, 0.23)])
    for x in (-0.30, -0.12, 0.08, 0.26):
        posts.line([at(x, 0.07), at(x, 0.245)], s * 0.020)
    x0, x1 = sorted((at(-0.40, 0.0)[0], at(0.36, 0.0)[0]))
    _upturned(roof, x0, x1, v - s * 0.245, s * 0.06, s * 0.035)
    xa, xb = sorted((at(-0.30, 0.0)[0], at(0.26, 0.0)[0]))
    roof.poly([(x0 + s * 0.03, v - s * 0.245), (x1 - s * 0.03, v - s * 0.245), (xb - s * 0.02, v - s * 0.32), (xa + s * 0.02, v - s * 0.32)])


def _sampan(hull: Pen, mat: Pen, man: Pen, u: float, v: float, s: float, facing: float = 1.0) -> None:
    """A small boat of the lake: a narrow hull with raised ends, an arched
    roof of matting over its middle, and a boatman with a hat who stands at
    the stern and pushes a long pole."""
    f = facing

    def at(x: float, y: float) -> tuple[float, float]:
        return (u + f * x * s, v - y * s)

    hull.poly([at(-0.52, 0.09), at(-0.40, 0.0), at(0.40, 0.0), at(0.54, 0.10), at(0.40, 0.05), at(-0.40, 0.05)])
    mat.poly([at(-0.18, 0.05)] + [at(-0.18 + 0.36 * t, 0.05 + 0.15 * math.sin(math.pi * t) ** 0.6) for t in np.linspace(0.0, 1.0, 12)] + [at(0.18, 0.05)])
    man.line([at(-0.38, 0.05), at(-0.37, 0.26)], s * 0.035)
    man.poly([at(-0.45, 0.25), at(-0.29, 0.25), at(-0.37, 0.32)])
    man.line([at(-0.30, 0.20), at(-0.62, -0.12)], s * 0.012)


def _town_house(wall: Pen, roof: Pen, u: float, v: float, w: float, h: float) -> None:
    """A house of the city far off: a white wall and a roof of grey tiles
    whose ends turn up a little."""
    wall.rect(u - w * 0.48, v - h * 0.55, u + w * 0.48, v + 0.002)
    roof.poly([(u - w * 0.62, v - h * 0.50), (u + w * 0.62, v - h * 0.50), (u + w * 0.36, v - h), (u - w * 0.36, v - h)])
    _upturned(roof, u - w * 0.66, u + w * 0.66, v - h * 0.50, h * 0.10, h * 0.08)


def history_hangzhou(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = HANGZHOU
    sun_at = (0.30, 0.30)
    shore = HANGZHOU_SHORE
    cause_v = HANGZHOU_CAUSEWAY

    def city_edge(v):
        # The east shore, where the city is: it comes toward the eye and to
        # the left.
        return 0.80 - (v - shore) * 1.3

    if layer_key == "sky":
        # A soft morning of spring: a pale sky, thin cloud, and the hills
        # round the lake in two soft ranges, each paler than the one in
        # front, with mist in the valleys and on the water.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.90)), (0.26, p["top"]), (0.48, p["mid"]), (HORIZON - 0.01, p["low"]),
                                 (HORIZON + 0.002, mix(p["water"], p["low"], 0.55)), (1.0, mix(p["water"], p["low"], 0.30))]))
        _sun(a, layer, *sun_at, 0.020, p["sun"], p["glow"], 0.45)
        streaks = smoothstep(0.55, 0.80, a.noise("hangzhou streaks", cells=5.0, octaves=3, stretch=10.0)) * a.band(0.40, 0.10, 1.2)
        a.light(layer, streaks, p["cloud"], 0.35)
        above = smoothstep(HORIZON + 0.004, HORIZON + 0.001, a.v)
        for k, (base, amp, cells, pale) in enumerate(((HORIZON - 0.050, 0.026, 3.0, 0.62), (HORIZON - 0.022, 0.018, 5.0, 0.42))):
            mask, _ = a.ridge(("hangzhou hills", k), base, amp, cells=cells, octaves=4)
            mask = mask * above
            colour = mix(p["hills"], p["mid"], pale)
            a.put(layer, mask, a.ramp([(0.0, colour), (base - amp, colour), (HORIZON - 0.004, mix(colour, p["low"], 0.55)), (1.0, p["low"])]))
            a.light(layer, a.rim(mask, 0.006, 0.002, 1.5) * mask, p["glow"], 0.25)
            a.tint(layer, fog(a, ("hangzhou valley mist", k), base + amp * 0.8, 0.010, 3.0) * mask, p["low"], 0.50)
        a.tint(layer, fog(a, "hangzhou lake mist", HORIZON - 0.004, 0.014, 3.0), p["low"], 0.60)
        _textbook(a, layer, 0.07)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far hangzhou")
        cols = np.linspace(0.0, 1.0, a.n)
        on_land = smoothstep(shore + 0.0015, shore - 0.0005, a.v)
        # The tea hills behind, at the middle: two round tops with rows of
        # tea bushes that follow the slope.
        bumps = ((0.50, 0.034, 0.08), (0.63, 0.056, 0.07), (0.75, 0.044, 0.06), (0.86, 0.030, 0.06))
        rise = np.array([0.006 + sum(hh * math.exp(-(((x - c) / wd) ** 2)) for c, hh, wd in bumps) for x in cols], dtype=np.float32)
        tea_top = (shore - rise - (a.line_noise("hangzhou tea crest", cells=30.0, octaves=2) - 0.5) * 0.003).astype(np.float32)
        tea = _land(a, tea_top) * on_land * smoothstep(0.38, 0.44, a.u)
        # Woods on the tops of the tea hills and in the folds between them.
        tea_woods, tea_wood_pen = a.drawing()
        _canopy(tea_wood_pen, rng, tea_top, 0.58, 0.68, 0.002, 0.004, 0.008, 40)
        _canopy(tea_wood_pen, rng, tea_top, 0.71, 0.80, 0.002, 0.004, 0.007, 30)
        _canopy(tea_wood_pen, rng, tea_top, 0.84, 0.92, 0.002, 0.003, 0.006, 20)
        for fold in (0.565, 0.695, 0.81):
            for _ in range(10):
                fv = rng.uniform(_at(tea_top, fold) + 0.004, shore - 0.002)
                tea_wood_pen.ellipse(fold + rng.uniform(-0.006, 0.006) + (fv - shore) * 0.2, fv, rng.uniform(0.003, 0.006), rng.uniform(0.003, 0.005))
        # Sunset Hill at the left, wooded, with Leifeng Pagoda on its top.
        bumps = ((0.25, 0.058, 0.10), (0.10, 0.034, 0.07), (0.36, 0.018, 0.05))
        rise = np.array([0.004 + sum(hh * math.exp(-(((x - c) / wd) ** 2)) for c, hh, wd in bumps) for x in cols], dtype=np.float32)
        hill_top = (shore - rise * smoothstep(0.46, 0.38, cols)).astype(np.float32)
        hill, hill_pen = a.drawing()
        _canopy(hill_pen, rng, hill_top, -0.02, 0.44, 0.003, 0.006, 0.012, 280)
        hill_mask = np.maximum(_land(a, hill_top + 0.004), a.mask_of(hill)) * on_land * smoothstep(0.46, 0.42, a.u)
        pag = {key: a.drawing() for key in ("body", "eaves", "doors")}
        pag_u = 0.255
        _leifeng(pag["body"][1], pag["eaves"][1], pag["doors"][1], pag_u, _at(hill_top, pag_u) + 0.004, 0.040, 0.140)
        # The city on the east shore at the right: rows of grey roofs that
        # go back to the foot of the hills, and a few trees between them.
        city_img, city_pen = a.drawing()
        city_pen.poly([(0.80, shore - 0.03), (0.80, shore), (city_edge(HANGZHOU_QUAY), HANGZHOU_QUAY), (1.05, HANGZHOU_QUAY), (1.05, shore - 0.03)])
        city_land = a.mask_of(city_img)
        quay = city_land * smoothstep(HANGZHOU_QUAY - 0.0045, HANGZHOU_QUAY - 0.0035, a.v)
        walls, wall_pen = a.drawing()
        roofs, roof_pen = a.drawing()
        town_trees, town_tree_pen = a.drawing()
        rows = [shore - 0.010, shore - 0.004, shore + 0.004, shore + 0.013, shore + 0.024, shore + 0.036, HANGZHOU_QUAY - 0.004]
        for r, v in enumerate(rows):
            x = max(city_edge(v) + 0.012, 0.79) if v < shore else city_edge(v) + 0.010
            size = 0.010 + 0.0020 * r
            while x < 1.03:
                w = size * rng.uniform(1.0, 1.8)
                if r == len(rows) - 1:
                    # Willows along the quay.
                    if rng.random() < 0.6:
                        _willow(town_tree_pen, town_tree_pen, rng, x + w * 0.5, v, size * 1.5, size * 1.0)
                    x += size * rng.uniform(2.0, 3.2)
                    continue
                if rng.random() < 0.14:
                    town_tree_pen.ellipse(x, v - size * 0.9, size * 0.9, size * 0.8)
                else:
                    _town_house(wall_pen, roof_pen, x + w * 0.5, v, w, size * rng.uniform(0.9, 1.2))
                x += w + size * rng.uniform(0.1, 0.4)
        # The Su causeway: a long low bank across the lake with willows and
        # peach trees on it, and three arched bridges.
        cause, cause_pen = a.drawing()
        cause_pen.rect(-0.02, cause_v - 0.003, city_edge(cause_v) + 0.02, cause_v + 0.001)
        bridges, bridge_pen = a.drawing()
        holes, hole_pen = a.drawing()
        spans = (0.14, 0.40, 0.62)
        for u in spans:
            _hump_bridge(bridge_pen, hole_pen, u, cause_v - 0.001, 0.020, 0.011)
        willows, willow_pen = a.drawing()
        peaches, peach_pen = a.drawing()
        stems, stem_pen = a.drawing()
        u = -0.01
        while u < city_edge(cause_v):
            if min(abs(u - s) for s in spans) > 0.030:
                h = rng.uniform(0.026, 0.036)
                if rng.random() < 0.30:
                    stem_pen.line([(u, cause_v), (u, cause_v - h * 0.45)], 0.0018)
                    _lumpy_crown(peach_pen, rng, u, cause_v - h * 0.62, h * 0.42, h * 0.30, 18)
                else:
                    _willow(stem_pen, willow_pen, rng, u, cause_v - 0.001, h, h * rng.uniform(0.55, 0.72))
            u += rng.uniform(0.020, 0.030)
        # Boats on the lake: a pleasure boat with a cabin, and small boats
        # with a roof of matting.
        boats = []
        for kind, bu, bv, s, f in (("pleasure", 0.43, 0.672, 0.075, 1.0), ("sampan", 0.60, 0.651, 0.040, -1.0), ("sampan", 0.25, 0.694, 0.048, 1.0), ("sampan", 0.08, 0.650, 0.032, 1.0)):
            pens = {key: a.drawing() for key in ("hull", "cabin", "roof", "posts")}
            if kind == "pleasure":
                _pleasure_boat(pens["hull"][1], pens["cabin"][1], pens["roof"][1], pens["posts"][1], bu, bv, s, f)
            else:
                _sampan(pens["hull"][1], pens["roof"][1], pens["posts"][1], bu, bv, s, f)
            boats.append((kind, bv, {key: a.mask_of(img) for key, (img, _) in pens.items()}))
        tea_wood_mask = a.mask_of(tea_woods) * on_land
        tea = np.maximum(tea, tea_wood_mask)
        tea_mask = tea * (1.0 - hill_mask)
        pm = {key: a.mask_of(img) for key, (img, _) in pag.items()}
        pag_mask = np.maximum(pm["body"], pm["eaves"])
        wall_mask = a.mask_of(walls)
        roof_mask = a.mask_of(roofs)
        town_tree_mask = a.mask_of(town_trees)
        town_mask = np.maximum.reduce([wall_mask, roof_mask, town_tree_mask])
        city_ground = city_land
        hole_mask = a.mask_of(holes)
        bridge_mask = a.mask_of(bridges) * (1.0 - hole_mask)
        cause_mask = np.maximum(a.mask_of(cause), bridge_mask)
        willow_mask = a.mask_of(willows)
        peach_mask = a.mask_of(peaches)
        stem_mask = a.mask_of(stems)
        on_cause = np.maximum.reduce([cause_mask, willow_mask, peach_mask, stem_mask])
        boat_mask = np.maximum.reduce([np.maximum.reduce(list(bm.values())) for _, _, bm in boats])
        land = np.maximum.reduce([tea, hill_mask, pag_mask, city_ground, town_mask])
        water = smoothstep(shore - 0.002, shore + 0.001, a.v) * (1.0 - city_ground)
        mask = np.maximum.reduce([land, water, on_cause, boat_mask])
        layer = solid(a, mask, mix(p["forest"], p["far"], 0.45), p["forest"], HORIZON, 0.70, "hangzhou far", 0.03)
        # The lake: it shows the pale sky near the far shore and goes to jade
        # toward the eye. Each thing on it shows upside down under it.
        a.put(layer, water, a.ramp([(0.0, mix(p["water_light"], p["low"], 0.40)), (shore, mix(p["water_light"], p["low"], 0.40)),
                                     (0.65, mix(p["water"], p["water_light"], 0.45)), (0.74, p["water"]), (1.0, p["water_deep"])]))
        above_shore = land * (a.v < shore + 0.001)
        hill_flip = _reflected(a, np.maximum(tea, hill_mask) * (a.v < shore + 0.001), shore, "hangzhou hill ripple", water)
        a.put(layer, hill_flip, mix(p["forest"], p["water"], 0.55), 0.50)
        pag_flip = _reflected(a, pag_mask, shore, "hangzhou pagoda ripple", water)
        a.put(layer, pag_flip, mix(p["brick"], p["water"], 0.40), 0.60)
        town_flip = _reflected(a, town_mask * above_shore, shore, "hangzhou town ripple", water)
        a.put(layer, town_flip, mix(p["tile"], p["water_light"], 0.45), 0.45)
        quay_flip = _reflected(a, np.maximum(town_mask, city_land) * (a.u > city_edge(HANGZHOU_QUAY) + 0.01) * (a.v > shore + 0.008), HANGZHOU_QUAY, "hangzhou quay ripple", water)
        a.put(layer, quay_flip, mix(p["tile"], p["water"], 0.55), 0.50)
        cause_flip = _reflected(a, on_cause, cause_v + 0.001, "hangzhou causeway ripple", water * (1.0 - on_cause))
        a.put(layer, cause_flip, mix(p["willow_dark"], p["water"], 0.40), 0.55)
        a.put(layer, _reflected(a, bridge_mask, cause_v - 0.001, "hangzhou bridge ripple", water * (1.0 - on_cause)), mix(p["stone"], p["water_light"], 0.30), 0.70)
        for k, (_, bv, bm) in enumerate(boats):
            body = np.maximum.reduce(list(bm.values()))
            a.put(layer, _reflected(a, body, bv + 0.0005, f"hangzhou boat ripple {k}", water * (1.0 - boat_mask)), mix(p["hull"], p["water"], 0.45), 0.55)
        lines = smoothstep(0.62, 0.84, a.noise("hangzhou lake lines", cells=60.0, octaves=2, stretch=14.0))
        a.light(layer, water * lines * smoothstep(shore + 0.01, shore + 0.05, a.v), p["water_light"], 0.30)
        glitter = water * a.spot(sun_at[0], 0.66, 0.16, 1.2, squash=0.6) * smoothstep(0.50, 0.75, a.noise("hangzhou glitter", cells=110.0, octaves=2, stretch=10.0))
        a.light(layer, glitter, p["glow"], 0.55)
        # The tea hills: green rows of bushes that follow the slope, with dark
        # lines between them, lit on the side to the sun.
        a.put(layer, tea_mask, mix(p["tea"], p["far"], 0.35))
        depth = a.v - tea_top[None, :] + (a.noise("hangzhou tea wobble", cells=40.0, octaves=2) - 0.5) * 0.004
        rows = np.clip(1.0 - np.abs(((depth / 0.0050) % 1.0) - 0.5) / 0.20, 0.0, 1.0)
        a.put(layer, tea_mask * rows * smoothstep(0.0015, 0.004, depth), mix(p["tea_row"], p["far"], 0.25), 0.85)
        a.light(layer, tea_mask * (1.0 - rows) * smoothstep(0.55, 0.80, a.noise("hangzhou tea light", cells=20.0, octaves=2)), p["tea_light"], 0.25)
        a.light(layer, a.rim(tea_mask, 0.005, 0.0, 0.8) * tea_mask, mix(p["tea_light"], p["glow"], 0.4), 0.50)
        a.shade(layer, a.rim(tea_mask, -0.006, 0.0, 1.5) * tea_mask, 0.12)
        woods = tea_wood_mask * (1.0 - hill_mask)
        a.put(layer, woods, mix(p["forest"], p["far"], 0.35))
        a.light(layer, a.rim(woods, 0.002, 0.002, 0.3) * woods, mix(p["forest_light"], p["far"], 0.3), 0.45)
        # Sunset Hill: the crowns of spring trees, dark under and lit on
        # their tops.
        a.put(layer, hill_mask, mix(p["forest"], p["far"], 0.28))
        lumps = a.noise("hangzhou hill lumps", cells=90.0, octaves=2)
        a.light(layer, hill_mask * smoothstep(0.55, 0.78, lumps), mix(p["forest_light"], p["far"], 0.2), 0.40)
        a.light(layer, a.rim(hill_mask, 0.003, 0.003, 0.4) * hill_mask, mix(p["forest_light"], p["glow"], 0.4), 0.55)
        a.shade(layer, hill_mask * smoothstep(0.62, 0.85, a.noise("hangzhou hill shade", cells=30.0, octaves=2)), 0.12)
        # Leifeng Pagoda: warm brick lit on the face to the sun, in shade on
        # its far face; dark eaves with pale lit edges; dark doors.
        a.put(layer, pm["body"], p["brick"])
        face = (a.u - pag_u) / 0.020
        a.light(layer, pm["body"] * smoothstep(-0.25, -0.40, face), p["brick_light"], 0.55)
        a.shade(layer, pm["body"] * smoothstep(0.25, 0.40, face), 0.28)
        a.put(layer, pm["eaves"], p["eave"])
        a.light(layer, a.rim(pm["eaves"], 0.0, 0.0025, 0.0) * pm["eaves"], p["tile_light"], 0.55)
        a.put(layer, pm["doors"] * pm["body"] * (1.0 - pm["eaves"]), scale(p["eave"], 0.7), 0.9)
        # The city: white walls and grey roofs with pale ridges; trees
        # between them.
        a.put(layer, city_ground, mix(p["stone"], p["forest"], 0.35))
        a.put(layer, quay, p["stone"])
        a.light(layer, a.rim(quay, 0.0, 0.0015, 0.0) * quay, p["stone_light"], 0.7)
        a.shade(layer, quay * np.clip(1.0 - np.abs(((a.u * 260.0) % 1.0) - 0.5) / 0.08, 0.0, 1.0), 0.25)
        a.put(layer, wall_mask, mix(p["wall"], p["far"], 0.15))
        a.put(layer, town_tree_mask, mix(p["willow"], p["forest"], 0.35))
        a.light(layer, a.rim(town_tree_mask, 0.002, 0.002, 0.2) * town_tree_mask, p["willow_light"], 0.45)
        a.put(layer, roof_mask, mix(p["tile"], p["far"], 0.20))
        a.light(layer, a.rim(roof_mask, 0.0, 0.002, 0.0) * roof_mask, p["tile_light"], 0.65)
        a.shade(layer, a.rim(roof_mask, 0.0, -0.0015, 0.0) * roof_mask, 0.30)
        # The causeway: pale stone and grass, the bridges lit on their tops,
        # the willows a fresh green with fronds in a darker green, and peach
        # trees in pink blossom.
        a.put(layer, a.mask_of(cause), mix(p["willow_dark"], p["stone"], 0.40))
        a.put(layer, bridge_mask, p["stone"])
        a.light(layer, a.rim(bridge_mask, 0.0, 0.002, 0.0) * bridge_mask, p["stone_light"], 0.75)
        a.put(layer, stem_mask, p["trunk"])
        a.put(layer, willow_mask, p["willow"])
        a.put(layer, willow_mask * smoothstep(0.45, 0.75, a.noise("hangzhou fronds", cells=500.0, octaves=1, stretch=0.06)), p["willow_dark"], 0.55)
        a.light(layer, a.rim(willow_mask, 0.002, 0.003, 0.2) * willow_mask, p["willow_light"], 0.60)
        a.put(layer, peach_mask, p["peach"])
        a.light(layer, a.rim(peach_mask, 0.002, 0.002, 0.2) * peach_mask, (255, 236, 236), 0.55)
        # The boats: dark hulls; the pleasure boat with a pale cabin, red
        # posts and a dark tile roof; the small boats with a roof of matting
        # and a dark boatman.
        for kind, bv, bm in boats:
            a.put(layer, bm["cabin"], mix(p["wall"], p["mat"], 0.3))
            a.put(layer, bm["roof"], p["eave"] if kind == "pleasure" else p["mat"])
            a.put(layer, bm["posts"], p["red"] if kind == "pleasure" else p["near"], 1.0 if kind == "pleasure" else 0.8)
            a.put(layer, bm["hull"], p["hull"])
            a.light(layer, a.rim(bm["hull"], 0.0, 0.0015, 0.0) * bm["hull"], p["brick_light"], 0.55)
        a.tint(layer, fog(a, "hangzhou shore mist", shore - 0.004, 0.014, 3.0) * mask, p["low"], 0.45)
        haze(a, layer, p["low"], 0.07, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near hangzhou")
        bank, ground, bank_at = _bank(a, "near hangzhou", 0.034, 0.024)
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        fronds, frond_pen = a.drawing()
        pond, pond_pen = a.drawing()
        stalks, stalk_pen = a.drawing()
        pads, pad_pen = a.drawing()
        flowers, flower_pen = a.drawing()
        grass, grass_pen = a.drawing()
        # A big willow at the left, its fronds hanging in long curtains; a
        # pool of lotus at the right. The middle is a calm bank of grass.
        ends = _limbs(trunk_pen, rng, 0.075, bank_at(0.075) + 0.006, 0.36, 0.020, 0.05, 4)
        for ex, ey in ends:
            # Thin twigs arch up and over from the end of each limb, and the
            # fronds hang from them in long thin strands with small leaves.
            for _ in range(5):
                side = rng.uniform(-1.0, 1.0)
                tip = (ex + side * 0.055, ey + rng.uniform(0.000, 0.020))
                if tip[0] > 0.26:
                    tip = (0.26 - rng.uniform(0.0, 0.02), tip[1])
                twig = _arch((ex, ey), ((ex + tip[0]) * 0.5, ey - rng.uniform(0.020, 0.035)), tip, 10)
                crown_pen.line(twig, 0.0016)
                for x, y in twig[2:]:
                    if rng.random() < 0.35:
                        continue
                    length = rng.uniform(0.07, 0.20)
                    drift = rng.uniform(-0.004, 0.008)
                    strand = _arch((x, y), (x + drift * 0.2, y + length * 0.5), (x + drift, y + length), 10)
                    frond_pen.line(strand, rng.uniform(0.0010, 0.0016))
                    for sx, sy in strand[1::2]:
                        frond_pen.ellipse(sx + 0.0012, sy + 0.003, 0.0016, 0.0040)
        pond_pen.ellipse(0.87, bank_at(0.87) + 0.016, 0.15, 0.018)
        lotus = []
        for u, h, kind in ((0.76, 0.050, "pad"), (0.80, 0.095, "up"), (0.84, 0.070, "pad"), (0.875, 0.125, "bud"), (0.90, 0.060, "pad"), (0.93, 0.105, "up"),
                           (0.965, 0.080, "flower"), (0.99, 0.050, "pad"), (0.83, 0.030, "float"), (0.92, 0.028, "float"), (0.73, 0.026, "float")):
            foot = bank_at(u) + 0.014
            top = (u + rng.uniform(-0.010, 0.010), foot - h)
            if kind != "float":
                stalk_pen.line(_arch((u, foot), (u, foot - h * 0.5), top, 8), 0.0026)
            lotus.append((kind, top, h))
            if kind in ("pad", "float"):
                r = 0.022 + h * 0.15
                pad_pen.ellipse(top[0], top[1], r, r * 0.30)
            elif kind == "up":
                # A young leaf that stands up like a cup, its edge curled.
                r = 0.020
                pad_pen.poly([(top[0] - r, top[1] - r * 0.6), (top[0] - r * 0.3, top[1] - r * 0.15), (top[0], top[1] + 0.002), (top[0] + r * 0.3, top[1] - r * 0.15), (top[0] + r, top[1] - r * 0.7),
                              (top[0] + r * 0.4, top[1] - r * 0.55), (top[0], top[1] - r * 0.62), (top[0] - r * 0.4, top[1] - r * 0.50)])
            elif kind == "bud":
                flower_pen.poly([(top[0], top[1] - 0.026), (top[0] + 0.009, top[1] - 0.010), (top[0] + 0.006, top[1]), (top[0] - 0.006, top[1]), (top[0] - 0.009, top[1] - 0.010)])
            else:
                for ang in (-60.0, -30.0, 0.0, 30.0, 60.0):
                    tip = polar(top[0], top[1], 0.022, ang - 90.0)
                    _leaf(flower_pen, [(top[0], top[1] + 0.002), ((top[0] + tip[0]) * 0.5 + 0.002 * math.sin(math.radians(ang)), (top[1] + tip[1]) * 0.5), tip], 0.0065, 0.6)
        for _ in range(14):
            u = rng.uniform(0.28, 0.70)
            _grass_blades(grass_pen, rng, u, bank_at(u) + 0.002, rng.uniform(0.010, 0.018), 5, 0.0012, 0.008)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        frond_mask = a.mask_of(fronds)
        pond_mask = a.mask_of(pond) * bank_mask
        stalk_mask = a.mask_of(stalks)
        pad_mask = a.mask_of(pads)
        flower_mask = a.mask_of(flowers)
        grass_mask = a.mask_of(grass)
        mask = np.maximum.reduce([bank_mask, trunk_mask, crown_mask, frond_mask, stalk_mask, pad_mask, flower_mask, grass_mask])
        layer = a.blank()
        earth = a.ramp([(0.0, mix(p["forest"], p["near"], 0.40)), (0.66, mix(p["forest"], p["near"], 0.40)), (0.80, mix(p["forest"], p["near"], 0.78)), (1.0, p["near"])])
        a.put(layer, bank_mask, earth)
        a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, p["glow"], 0.28)
        a.put(layer, pond_mask, mix(p["water"], p["near"], 0.35))
        a.light(layer, pond_mask * smoothstep(0.55, 0.80, a.noise("hangzhou pond lines", cells=60.0, octaves=2, stretch=10.0)), p["water_light"], 0.35)
        a.light(layer, a.rim(pond_mask, 0.0, 0.003, 0.2) * pond_mask, p["water_light"], 0.45)
        a.put(layer, grass_mask, mix(p["willow_dark"], p["near"], 0.35))
        a.light(layer, a.rim(grass_mask, 0.0015, 0.0, 0.2) * grass_mask, p["willow_light"], 0.30)
        # The willow: dark furrowed bark; its head and fronds a fresh green,
        # lit where the morning light comes from the left.
        a.put(layer, trunk_mask, mix(p["trunk"], p["near"], 0.40))
        a.shade(layer, trunk_mask * smoothstep(0.45, 0.75, a.noise("hangzhou willow bark", cells=220.0, octaves=1, stretch=0.08)), 0.30)
        a.light(layer, a.rim(trunk_mask, 0.004, 0.0, 0.4) * trunk_mask, p["glow"], 0.35)
        a.put(layer, crown_mask, mix(p["trunk"], p["near"], 0.40))
        a.put(layer, frond_mask, mix(p["willow"], p["near"], 0.25))
        a.put(layer, frond_mask * smoothstep(0.45, 0.70, a.noise("hangzhou frond shade", cells=24.0, octaves=2)), mix(p["willow_dark"], p["near"], 0.30), 0.6)
        a.light(layer, a.rim(frond_mask, 0.0015, 0.0, 0.0) * frond_mask, p["willow_light"], 0.50)
        # The lotus: blue-green leaves lit on their rims, pink flowers.
        a.put(layer, stalk_mask, mix(p["lotus"], p["near"], 0.40))
        a.put(layer, pad_mask, mix(p["lotus"], p["near"], 0.20))
        a.light(layer, a.rim(pad_mask, 0.0, 0.003, 0.0) * pad_mask, p["lotus_light"], 0.60)
        a.shade(layer, a.rim(pad_mask, 0.0, -0.002, 0.0) * pad_mask, 0.30)
        a.put(layer, flower_mask, p["lotus_pink"])
        a.light(layer, a.rim(flower_mask, 0.002, 0.002, 0.0) * flower_mask, (255, 236, 236), 0.55)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.18)
        haze(a, layer, p["low"], 0.08, None)
        return layer
    layer = _air(a, p, "hangzhou morning mist", p["low"], 0.28, scale(p["near"], 0.8), 0.16)
    a.put(layer, shafts(a, "hangzhou shafts", 4, 0.14, 0.0, 0.85, 0.05), p["glow"], 0.07)
    return layer


def hangzhou_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Willow fronds hang from above at two places, each a twig with long
    thin strands. Lotus leaves on tall stalks stand from below at one place."""
    del layer_lights
    rng = art_.rand("hangzhou foreground")
    for k in range(2):
        u0 = 0.14 + (k + rng.uniform(0.2, 0.8)) * 0.36
        twig = _arch((u0 - 0.04, 0.0), (u0, 0.20), (u0 + 0.05, 0.26), 10)
        pen.line(twig, 0.0024)
        for x, y in twig[3:]:
            for _ in range(2):
                x0 = x + rng.uniform(-0.006, 0.006)
                end = min(0.388, y + rng.uniform(0.06, 0.14))
                drift = rng.uniform(-0.006, 0.006)
                strand = _arch((x0, y), (x0 + drift * 0.3, (y + end) * 0.5), (x0 + drift, end), 8)
                pen.line(strand, 0.0010)
                for sx, sy in strand[2::2]:
                    _leaf(pen, [(sx, sy), (sx + 0.002, sy + 0.005), (sx + 0.001, sy + 0.010)], 0.0016, 0.6)
    u = rng.uniform(0.50, 0.62)
    for j, (du, h, r) in enumerate(((-0.015, 0.012, 0.020), (0.012, 0.004, 0.026), (0.032, 0.016, 0.016))):
        x = u + du
        top = (x + rng.uniform(-0.006, 0.006), REST_BOTTOM - h + 0.010)
        pen.line(_arch((x, 1.0), (x, top[1] + 0.12), top, 10), 0.0022)
        pen.ellipse(top[0], top[1] + 0.003, r, r * 0.28)


# ---------------------------------------------------------------------------
# Heian-kyo: the garden of a mansion in autumn
# ---------------------------------------------------------------------------


HEIAN = {
    "top": (88, 124, 172),
    "mid": (206, 196, 180),
    "low": (250, 224, 182),
    "glow": (255, 212, 140),
    "sun": (255, 240, 204),
    "cloud": (252, 236, 210),
    "hills": (110, 112, 112),
    "hills_forest": (82, 96, 72),
    "maple": (200, 54, 36),
    "maple_light": (238, 124, 58),
    "gold": (224, 172, 62),
    "pine": (42, 68, 52),
    "pine_light": (104, 128, 80),
    "bark": (92, 70, 56),
    "vermilion": (204, 72, 44),
    "vermilion_light": (242, 140, 96),
    "roof": (122, 82, 58),
    "roof_light": (180, 138, 98),
    "roof_dark": (74, 50, 40),
    "lattice": (48, 38, 34),
    "blind": (214, 192, 132),
    "wood": (138, 110, 82),
    "gravel": (220, 212, 192),
    "gravel_shade": (186, 178, 162),
    "water": (64, 100, 112),
    "water_light": (190, 206, 198),
    "stone": (150, 144, 132),
    "stone_light": (214, 206, 186),
    "moss": (92, 112, 64),
    "ox": (64, 46, 38),
    "carriage": (44, 34, 32),
    "carriage_light": (150, 118, 82),
    "grass": (148, 136, 76),
    "grass_light": (210, 190, 112),
    "plume": (238, 226, 204),
    "far": (224, 210, 188),
    "near": (40, 28, 24),
    "near_light": (164, 118, 70),
}

#: The level of the far edge of the pond, where the court of white gravel
#: ends, and of the island and the bridge in the pond.
HEIAN_POND = 0.650
HEIAN_ISLAND = 0.677


def _shinden(under: Pen, floor: Pen, pillars: Pen, lattice: Pen, blinds: Pen, roof: Pen, edge: Pen, u: float, v: float, half: float, h: float) -> None:
    """A hall of a mansion in the shinden style: long and low, raised on
    short posts over the ground, with a veranda and its rail all round.
    Vermilion pillars stand between black lattice shutters and pale blinds
    of split bamboo. A wide hipped-and-gabled roof of cypress bark, smooth
    and brown with a thick cut edge, reaches far out over the veranda. `h`
    is the height from the ground to the ridge."""
    floor_v = v - h * 0.20
    for k in range(11):
        x = u - half * 0.96 + k * half * 1.92 / 10.0
        under.line([(x, v + 0.002), (x, floor_v)], max(half * 0.020, 0.0012))
    floor.rect(u - half * 1.00, floor_v - h * 0.040, u + half * 1.00, floor_v)
    floor.rect(u - half * 1.00, floor_v - h * 0.130, u + half * 1.00, floor_v - h * 0.105)
    for k in range(21):
        x = u - half + k * half / 10.0
        floor.line([(x, floor_v - h * 0.13), (x, floor_v)], max(half * 0.008, 0.0010))
    eave_v = v - h * 0.58
    wall_l, wall_r = u - half * 0.86, u + half * 0.86
    lattice.rect(wall_l, eave_v, wall_r, floor_v - h * 0.04)
    bays = 7
    for k in range(bays):
        x0 = wall_l + (wall_r - wall_l) * k / bays
        x1 = x0 + (wall_r - wall_l) / bays
        if k % 2 == 1:
            blinds.rect(x0, eave_v, x1, floor_v - h * 0.13)
    for k in range(bays + 1):
        x = wall_l + (wall_r - wall_l) * k / bays
        pillars.line([(x, floor_v), (x, eave_v)], max(half * 0.040, 0.0016))
    # The roof: the lower slopes are hipped and sweep up a little to a short
    # gable under each end of the ridge.
    edge_v = eave_v + h * 0.03
    reach = half * 1.16
    thick = h * 0.07
    edge.poly([(u - reach, edge_v - thick), (u + reach, edge_v - thick), (u + reach + h * 0.01, edge_v), (u - reach - h * 0.01, edge_v)])
    ridge_v = v - h
    left = _arch((u - reach, edge_v - thick), (u - reach * 0.80, edge_v - thick - h * 0.10), (u - half * 0.60, ridge_v + h * 0.06), 10)
    right = _arch((u + half * 0.60, ridge_v + h * 0.06), (u + reach * 0.80, edge_v - thick - h * 0.10), (u + reach, edge_v - thick), 10)
    roof.poly(left + [(u - half * 0.58, ridge_v), (u + half * 0.58, ridge_v)] + right)
    roof.rect(u - half * 0.62, ridge_v - h * 0.04, u + half * 0.62, ridge_v + h * 0.015)


def _corridor(posts: Pen, roof: Pen, floor: Pen, a0: tuple[float, float], a1: tuple[float, float], h: float, bays: int) -> None:
    """A covered corridor that joins two halls: slim posts, a floor of
    boards with a rail, and a low roof of bark over it, from the foot `a0`
    to the foot `a1`."""
    for k in range(bays + 1):
        t = k / bays
        x, y = a0[0] + (a1[0] - a0[0]) * t, a0[1] + (a1[1] - a0[1]) * t
        posts.line([(x, y + 0.002), (x, y - h * 0.82)], max(h * 0.05, 0.0012))
    floor.poly([(a0[0], a0[1] - h * 0.24), (a1[0], a1[1] - h * 0.24), (a1[0], a1[1] - h * 0.18), (a0[0], a0[1] - h * 0.18)])
    floor.poly([(a0[0], a0[1] - h * 0.44), (a1[0], a1[1] - h * 0.44), (a1[0], a1[1] - h * 0.40), (a0[0], a0[1] - h * 0.40)])
    roof.poly([(a0[0] - h * 0.2, a0[1] - h * 0.78), (a1[0] + h * 0.2, a1[1] - h * 0.78), (a1[0] + h * 0.1, a1[1] - h * 1.12), (a0[0] - h * 0.1, a0[1] - h * 1.12)])


def _sorihashi(deck: Pen, rail: Pen, u0: float, u1: float, v: float, rise: float) -> None:
    """A red arched bridge of a garden (a sorihashi): a deck that rises in a
    high curve from bank to bank, with a red rail on posts along it."""
    curve = _arch((u0, v), ((u0 + u1) * 0.5, v - rise * 2.0), (u1, v), 20)
    deck.poly(curve + [(x, y + rise * 0.18) for x, y in reversed(curve)])
    top = [(x, y - rise * 0.42) for x, y in curve]
    rail.line(top[1:-1], rise * 0.10)
    for x, y in curve[1:-1:2]:
        rail.line([(x, y), (x, y - rise * 0.44)], rise * 0.07)
    for x, y in (curve[1], curve[-2]):
        rail.line([(x, y), (x, y - rise * 0.62)], rise * 0.13)


def _ox_carriage(box: Pen, wheel: Pen, beast: Pen, u: float, v: float, s: float, facing: float = 1.0) -> None:
    """An ox carriage of the court (a gissha) far off: a box of black lacquer
    with a roof that curves up at its front and back, one tall pair of
    wheels, long shafts to the yoke, a black ox, and a man who leads it. `s`
    is its length and `(u, v)` the foot of its wheel."""
    f = facing

    def at(x: float, y: float) -> tuple[float, float]:
        return (u + f * x * s, v - y * s)

    r = s * 0.20
    box.poly([at(-0.30, 0.24), at(0.16, 0.24), at(0.16, 0.56), at(-0.30, 0.56)])
    box.poly([at(-0.36, 0.55), at(-0.30, 0.60), at(0.16, 0.60), at(0.24, 0.64), at(0.22, 0.56), at(-0.34, 0.53)])
    box.line([at(0.10, 0.28), at(0.62, 0.20)], s * 0.020)
    wheel.ring(u - f * s * 0.08, v - r, r, s * 0.035)
    for k in range(6):
        ang = k * 30.0
        x0, y0 = polar(u - f * s * 0.08, v - r, r, ang)
        x1, y1 = polar(u - f * s * 0.08, v - r, r, ang + 180.0)
        wheel.line([(x0, y0), (x1, y1)], s * 0.012)
    # The ox, its head down a little to the yoke.
    beast.ellipse(*at(0.70, 0.22), s * 0.13, s * 0.08)
    beast.ellipse(*at(0.84, 0.20), s * 0.05, s * 0.045)
    for x in (0.62, 0.66, 0.76, 0.80):
        beast.line([at(x, 0.18), at(x, 0.0)], s * 0.025)
    beast.line([at(0.85, 0.24), at(0.89, 0.29)], s * 0.012)
    # The man who leads it.
    beast.line([at(0.98, 0.0), at(0.98, 0.26)], s * 0.035)
    beast.ellipse(*at(0.98, 0.30), s * 0.025, s * 0.030)
    beast.line([at(0.97, 0.20), at(0.87, 0.18)], s * 0.010)


def _maple_grove(pen: Pen, rng, u: float, v: float, w: float, h: float, count: int) -> None:
    """A grove of maples far off: low trunks under wide crowns of small
    round lumps, the crowns joined into one ragged mass."""
    for _ in range(count):
        x = u + rng.uniform(-w, w)
        y = v - h * rng.uniform(0.55, 0.85)
        pen.line([(x, v + 0.002), (x, y)], h * 0.05)
        _lumpy_crown(pen, rng, x, y, h * rng.uniform(0.40, 0.60), h * rng.uniform(0.28, 0.36), 18)


def history_heian(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = HEIAN
    sun_at = (0.80, 0.34)
    pond_v = HEIAN_POND
    isle_v = HEIAN_ISLAND
    if layer_key == "sky":
        # A clear afternoon of autumn. The soft round hills of Higashiyama
        # lie in a long line behind the city, with the colour of the maples
        # in patches on their slopes and mist at their feet.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.88)), (0.24, p["top"]), (0.46, p["mid"]), (HORIZON - 0.01, p["low"]),
                                 (HORIZON + 0.002, mix(p["hills_forest"], p["low"], 0.45)), (1.0, mix(p["hills_forest"], p["low"], 0.30))]))
        _sun(a, layer, *sun_at, 0.022, p["sun"], p["glow"], 0.65)
        streaks = smoothstep(0.55, 0.80, a.noise("heian streaks", cells=6.0, octaves=3, stretch=12.0)) * a.band(0.40, 0.09, 1.2)
        a.light(layer, streaks, p["cloud"], 0.40)
        above = smoothstep(HORIZON + 0.004, HORIZON + 0.001, a.v)
        cols = np.linspace(0.0, 1.0, a.n)
        for k, (bumps, pale) in enumerate((
            (((0.04, 0.046, 0.09), (0.19, 0.058, 0.06), (0.29, 0.050, 0.10), (0.47, 0.070, 0.07), (0.58, 0.056, 0.11), (0.76, 0.068, 0.08), (0.93, 0.052, 0.10)), 0.50),
            (((0.00, 0.030, 0.08), (0.12, 0.024, 0.05), (0.33, 0.034, 0.12), (0.52, 0.022, 0.06), (0.66, 0.040, 0.09), (0.86, 0.028, 0.07), (1.00, 0.036, 0.05)), 0.24),
        )):
            # The bumps add like the shoulders of soft hills, not like a row of
            # cones: each hill is the highest of them at its place.
            rise = np.array([0.008 + max(hh * math.exp(-(((x - c) / wd) ** 2)) for c, hh, wd in bumps) for x in cols], dtype=np.float32)
            rise += (a.line_noise(("heian hill shoulders", k), cells=10.0, octaves=3) - 0.5) * 0.010
            top = (HORIZON + 0.003 - rise - (a.line_noise(("heian hill trees", k), cells=90.0, octaves=1) - 0.5) * 0.0025).astype(np.float32)
            mask = _land(a, top) * above
            colour = mix(p["hills"], p["mid"], pale)
            a.put(layer, mask, a.ramp([(0.0, colour), (HORIZON - 0.08, colour), (HORIZON - 0.004, mix(colour, p["low"], 0.50)), (1.0, p["low"])]))
            woods = mask * smoothstep(0.35, 0.70, a.noise(("heian hill woods", k), cells=220.0, octaves=2))
            a.put(layer, woods, mix(p["hills_forest"], p["mid"], pale), 0.40)
            red = mask * smoothstep(0.62, 0.78, a.noise(("heian hill maples", k), cells=120.0, octaves=2))
            a.put(layer, red, mix(p["maple"], p["mid"], pale + 0.20), 0.45)
            gold = mask * smoothstep(0.66, 0.80, a.noise(("heian hill gold", k), cells=110.0, octaves=2))
            a.put(layer, gold, mix(p["gold"], p["mid"], pale + 0.15), 0.40)
            a.light(layer, a.rim(mask, -0.006, 0.002, 1.5) * mask, p["glow"], 0.35)
            a.tint(layer, fog(a, ("heian hill mist", k), HORIZON - 0.008, 0.012, 3.0) * mask, p["low"], 0.45)
        a.tint(layer, fog(a, "heian low haze", HORIZON - 0.004, 0.014, 3.0), p["low"], 0.55)
        _textbook(a, layer, 0.09)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far heian")
        # The trees of the city behind the mansion, along the horizon.
        city_trees, city_pen = a.drawing()
        _canopy(city_pen, rng, np.full(a.n, HORIZON + 0.022, dtype=np.float32), -0.02, 1.02, 0.012, 0.006, 0.013, 340)
        ground = smoothstep(HORIZON + 0.016, HORIZON + 0.020, a.v)
        # Maples round the halls, in red and gold.
        maples, maple_pen = a.drawing()
        for gu, gv, gw, gh, count in ((0.02, 0.640, 0.04, 0.050, 4), (0.255, 0.628, 0.035, 0.050, 4), (0.62, 0.626, 0.05, 0.044, 5),
                                      (0.985, 0.640, 0.03, 0.055, 4), (0.53, 0.616, 0.06, 0.040, 4), (0.36, 0.612, 0.06, 0.036, 4)):
            _maple_grove(maple_pen, rng, gu, gv, gw, gh, count)
        # The halls: the main hall in the middle, a hall at each side, and
        # the covered corridors that join them. A corridor runs from the
        # east hall to a pavilion over the pond.
        names = ("under", "floor", "pillars", "lattice", "blinds", "roof", "edge")
        hall = {key: a.drawing() for key in names}
        pens = [hall[k][1] for k in names]
        _corridor(hall["under"][1], hall["roof"][1], hall["floor"][1], (0.13, 0.633), (0.31, 0.633), 0.020, 9)
        _corridor(hall["under"][1], hall["roof"][1], hall["floor"][1], (0.53, 0.633), (0.72, 0.633), 0.020, 9)
        _corridor(hall["under"][1], hall["roof"][1], hall["floor"][1], (0.82, 0.634), (0.885, 0.664), 0.020, 4)
        _shinden(*pens, 0.10, 0.633, 0.062, 0.042)
        _shinden(*pens, 0.77, 0.634, 0.066, 0.044)
        _shinden(*pens, 0.42, 0.637, 0.125, 0.062)
        _shinden(*pens, 0.915, 0.667, 0.036, 0.034)
        # The court of white gravel, a spit of the bank into the pond with
        # rocks on it, and an island with pines and a maple. A red bridge
        # goes from the spit to the island.
        spit, spit_pen = a.drawing()
        spit_pen.poly([(0.42, pond_v - 0.001)] + [(0.505 + 0.045 * math.cos(t), pond_v + (isle_v + 0.001 - pond_v) * math.sin(t) ** 0.8) for t in np.linspace(math.pi, 0.0, 24)] + [(0.60, pond_v - 0.001)])
        isle, isle_pen = a.drawing()
        isle_pen.poly([(0.14 + 0.09 * (1 - math.cos(t)), isle_v + 0.001 - 0.022 * math.sin(t) ** 0.6) for t in np.linspace(0.0, math.pi, 30)])
        rocks, rock_pen = a.drawing()
        for u, v, r in ((0.475, isle_v, 0.007), (0.545, isle_v - 0.002, 0.006), (0.16, isle_v, 0.008), (0.30, isle_v, 0.006), (0.40, pond_v + 0.002, 0.006), (0.70, pond_v + 0.002, 0.007),
                        (0.64, pond_v + 0.001, 0.004), (0.25, isle_v + 0.001, 0.005)):
            rock_pen.poly([(u - r * 1.3, v + 0.001), (u - r * 0.7, v - r * 0.9), (u + r * 0.3, v - r * 1.1), (u + r * 1.3, v + 0.001)])
        trunks, trunk_pen = a.drawing()
        pines, pine_pen = a.drawing()
        for u, h, lean in ((0.19, 0.060, 0.30), (0.235, 0.050, -0.22), (0.165, 0.040, -0.10)):
            _red_pine(trunk_pen, pine_pen, rng, u, isle_v - 0.014, h, lean)
        _maple_grove(maple_pen, rng, 0.28, isle_v - 0.008, 0.012, 0.036, 3)
        _red_pine(trunk_pen, pine_pen, rng, 0.53, isle_v - 0.010, 0.040, 0.25)
        deck, deck_pen = a.drawing()
        rail, rail_pen = a.drawing()
        _sorihashi(deck_pen, rail_pen, 0.310, 0.470, isle_v, 0.016)
        carriage = {key: a.drawing() for key in ("box", "wheel", "beast")}
        _ox_carriage(carriage["box"][1], carriage["wheel"][1], carriage["beast"][1], 0.625, 0.647, 0.046, 1.0)
        hm = {key: a.mask_of(img) for key, (img, _) in hall.items()}
        hall_mask = np.maximum.reduce(list(hm.values()))
        cm = {key: a.mask_of(img) for key, (img, _) in carriage.items()}
        carriage_mask = np.maximum.reduce(list(cm.values()))
        city_mask = a.mask_of(city_trees)
        maple_mask = a.mask_of(maples)
        court = ground * smoothstep(pond_v + 0.0015, pond_v - 0.0005, a.v)
        spit_mask = a.mask_of(spit)
        isle_mask = a.mask_of(isle)
        rock_mask = a.mask_of(rocks)
        trunk_mask = a.mask_of(trunks)
        pine_mask = a.mask_of(pines)
        deck_mask = a.mask_of(deck)
        rail_mask = a.mask_of(rail)
        bridge_mask = np.maximum(deck_mask, rail_mask)
        land = np.maximum.reduce([court, spit_mask, isle_mask, rock_mask])
        water = smoothstep(pond_v - 0.001, pond_v + 0.001, a.v) * (1.0 - np.maximum(spit_mask, isle_mask))
        mask = np.maximum.reduce([city_mask, ground, maple_mask, hall_mask, land, trunk_mask, pine_mask, bridge_mask, carriage_mask])
        layer = solid(a, mask, mix(p["pine"], p["far"], 0.45), p["pine"], HORIZON, 0.70, "heian far", 0.03)
        # The trees of the city: dark and blue with the air, a few in red.
        a.put(layer, city_mask, mix(p["hills_forest"], p["far"], 0.22))
        a.put(layer, city_mask * smoothstep(0.58, 0.72, a.noise("heian city maples", cells=70.0, octaves=2)), mix(p["maple"], p["far"], 0.25), 0.85)
        a.put(layer, city_mask * smoothstep(0.64, 0.78, a.noise("heian city gold", cells=60.0, octaves=2)), mix(p["gold"], p["far"], 0.20), 0.85)
        a.shade(layer, city_mask * smoothstep(0.55, 0.80, a.noise("heian city lumps", cells=160.0, octaves=2)), 0.15)
        a.light(layer, a.rim(city_mask, -0.002, 0.003, 0.3) * city_mask, mix(p["pine_light"], p["glow"], 0.5), 0.55)
        # The court: white gravel raked in long lines.
        a.put(layer, court, p["gravel"])
        a.shade(layer, court * np.clip(1.0 - np.abs(((a.v * 520.0) % 1.0) - 0.5) / 0.18, 0.0, 1.0), 0.12)
        a.shade(layer, court * smoothstep(pond_v - 0.012, pond_v, a.v), 0.10)
        a.shade(layer, court * a.blur(np.clip(a.shift(hall_mask, 0.004, 0.003) - hall_mask, 0.0, 1.0), 2.0), 0.25)
        a.put(layer, spit_mask, p["moss"])
        a.light(layer, a.rim(spit_mask, -0.003, 0.003, 0.3) * spit_mask, p["grass_light"], 0.45)
        a.put(layer, isle_mask, p["moss"])
        a.light(layer, a.rim(isle_mask, -0.003, 0.003, 0.3) * isle_mask, p["grass_light"], 0.45)
        # The pond: it shows the gold sky, the red of the maples, the halls
        # and the bridge upside down.
        a.put(layer, water, a.ramp([(0.0, mix(p["water_light"], p["low"], 0.35)), (pond_v, mix(p["water_light"], p["low"], 0.35)),
                                     (0.69, mix(p["water"], p["water_light"], 0.35)), (0.76, p["water"]), (1.0, scale(p["water"], 0.8))]))
        flip_hall = _reflected(a, hall_mask * (a.v < pond_v), pond_v, "heian hall ripple", water)
        a.put(layer, flip_hall, mix(p["roof_dark"], p["water"], 0.40), 0.55)
        flip_maple = _reflected(a, maple_mask * (a.v < pond_v) * (1.0 - hall_mask), pond_v, "heian maple ripple", water * (1.0 - flip_hall))
        a.put(layer, flip_maple, mix(p["maple"], p["water"], 0.35), 0.55)
        flip_isle = _reflected(a, np.maximum.reduce([isle_mask, pine_mask, trunk_mask, bridge_mask, rock_mask]) * (a.v < isle_v + 0.001), isle_v, "heian isle ripple", water)
        a.put(layer, flip_isle, mix(p["pine"], p["water"], 0.40), 0.55)
        a.put(layer, _reflected(a, bridge_mask, isle_v, "heian bridge ripple", water), mix(p["vermilion"], p["water"], 0.30), 0.75)
        a.put(layer, _reflected(a, hall_mask * (a.u > 0.86) * (a.v < 0.668), 0.668, "heian pavilion ripple", water), mix(p["roof_dark"], p["water"], 0.40), 0.55)
        lines = smoothstep(0.62, 0.84, a.noise("heian pond lines", cells=60.0, octaves=2, stretch=14.0))
        a.light(layer, water * lines * smoothstep(pond_v + 0.01, pond_v + 0.05, a.v), p["water_light"], 0.30)
        glitter = water * a.spot(sun_at[0], 0.68, 0.16, 1.2, squash=0.6) * smoothstep(0.50, 0.75, a.noise("heian glitter", cells=110.0, octaves=2, stretch=10.0))
        a.light(layer, glitter, p["glow"], 0.55)
        a.light(layer, a.rim(water, 0.0, -0.002, 0.0) * water, p["gravel"], 0.35)
        # The maples: scarlet with patches of orange and gold, lit at their
        # tops from the sun at the right.
        a.put(layer, maple_mask, mix(p["maple"], p["far"], 0.12))
        a.put(layer, maple_mask * smoothstep(0.50, 0.68, a.noise("heian far orange", cells=40.0, octaves=2)), mix(p["maple_light"], p["far"], 0.12), 0.75)
        a.put(layer, maple_mask * smoothstep(0.66, 0.78, a.noise("heian far gold", cells=36.0, octaves=2)), mix(p["gold"], p["far"], 0.10), 0.80)
        a.shade(layer, maple_mask * smoothstep(0.60, 0.80, a.noise("heian far maple shade", cells=90.0, octaves=2)), 0.18)
        a.light(layer, a.rim(maple_mask, -0.002, 0.003, 0.3) * maple_mask, p["glow"], 0.50)
        # The halls: dark under the floor, pale boards, vermilion pillars,
        # black lattice and pale blinds; the roofs of bark lit on the slope
        # to the sun, with a pale cut edge and a dark ridge.
        a.put(layer, hm["under"], scale(p["lattice"], 1.2))
        a.put(layer, hm["lattice"], p["lattice"])
        grid = np.maximum(np.clip(1.0 - np.abs(((a.u * 700.0) % 1.0) - 0.5) / 0.10, 0.0, 1.0), np.clip(1.0 - np.abs(((a.v * 700.0) % 1.0) - 0.5) / 0.10, 0.0, 1.0))
        a.light(layer, hm["lattice"] * grid, p["wood"], 0.25)
        a.put(layer, hm["blinds"] * hm["lattice"], p["blind"])
        a.shade(layer, hm["blinds"] * hm["lattice"] * np.clip(1.0 - np.abs(((a.v * 1400.0) % 1.0) - 0.5) / 0.15, 0.0, 1.0), 0.15)
        a.put(layer, hm["pillars"], p["vermilion"])
        a.light(layer, a.rim(hm["pillars"], 0.0012, 0.0, 0.0) * hm["pillars"], p["vermilion_light"], 0.40)
        a.put(layer, hm["floor"], p["wood"])
        a.light(layer, a.rim(hm["floor"], 0.0, 0.0012, 0.0) * hm["floor"], p["gravel"], 0.45)
        roof = hm["roof"] * (1.0 - hm["edge"])
        a.put(layer, roof, p["roof"])
        a.light(layer, a.rim(roof, -0.003, 0.0, 0.5) * roof, p["roof_light"], 0.55)
        a.shade(layer, a.rim(roof, 0.003, 0.0, 0.5) * roof, 0.20)
        a.shade(layer, roof * np.clip(1.0 - np.abs(((a.u * 600.0) % 1.0) - 0.5) / 0.15, 0.0, 1.0), 0.06)
        a.put(layer, hm["edge"], p["roof_light"])
        a.shade(layer, hm["edge"] * np.clip(1.0 - np.abs(((a.v * 1100.0) % 1.0) - 0.5) / 0.20, 0.0, 1.0), 0.20)
        # The island, the rocks, the pines and the bridge.
        a.put(layer, rock_mask, p["stone"])
        a.light(layer, a.rim(rock_mask, -0.002, 0.002, 0.0) * rock_mask, p["stone_light"], 0.55)
        a.put(layer, trunk_mask, p["bark"])
        a.put(layer, pine_mask, p["pine"])
        a.light(layer, a.rim(pine_mask, -0.002, 0.003, 0.2) * pine_mask, mix(p["pine_light"], p["glow"], 0.3), 0.55)
        a.put(layer, deck_mask, p["vermilion"])
        a.light(layer, a.rim(deck_mask, 0.0, 0.0015, 0.0) * deck_mask, p["vermilion_light"], 0.6)
        a.shade(layer, a.rim(deck_mask, 0.0, -0.0015, 0.0) * deck_mask, 0.30)
        a.put(layer, rail_mask, mix(p["vermilion"], p["vermilion_light"], 0.25))
        # The ox carriage: black lacquer with a pale roof edge; the ox dark.
        a.put(layer, cm["box"], p["carriage"])
        a.light(layer, a.rim(cm["box"], 0.0, 0.0015, 0.0) * cm["box"], p["carriage_light"], 0.7)
        a.put(layer, cm["wheel"], p["carriage"])
        a.put(layer, cm["beast"], p["ox"])
        a.tint(layer, fog(a, "heian court haze", HORIZON + 0.006, 0.010, 3.0) * mask * (a.v < 0.62), p["low"], 0.25)
        haze(a, layer, p["low"], 0.07, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near heian")
        bank, ground, bank_at = _bank(a, "near heian", 0.032, 0.030)
        limbs, limb_pen = a.drawing()
        gaps, gap_pen = a.drawing()
        fallen, fallen_pen = a.drawing()
        blades, blade_pen = a.drawing()
        plumes, plume_pen = a.drawing()
        rocks, rock_pen = a.drawing()
        # A maple in full red at the left, its tiers of leaves over a dark
        # trunk; pampas grass with pale plumes at the right, and a garden
        # stone at its foot. The middle is calm.
        _limbs(limb_pen, rng, 0.09, bank_at(0.09) + 0.006, 0.30, 0.013, 0.02, 4)
        tiers = []
        for cu, cv, rx, ry in ((0.085, 0.292, 0.075, 0.022), (0.10, 0.330, 0.105, 0.024), (0.085, 0.372, 0.120, 0.026), (0.12, 0.414, 0.090, 0.020)):
            img, pen = a.drawing()
            _maple_tier(pen, rng, cu, cv, rx, ry)
            tiers.append(a.mask_of(img))
            for _ in range(5):
                gu = cu + rng.uniform(-0.7, 0.7) * rx
                gap_pen.ellipse(gu, cv + ry * rng.uniform(0.2, 0.6), rng.uniform(0.004, 0.008), rng.uniform(0.002, 0.004))
        for u, h in ((0.80, 0.15), (0.87, 0.20), (0.95, 0.16), (0.74, 0.10)):
            _silvergrass(blade_pen, plume_pen, rng, u, bank_at(u) + 0.004, h, 16, 6)
        for u, w in ((0.90, 0.030), (0.84, 0.016)):
            rock_pen.ellipse(u, bank_at(u) - w * 0.20, w, w * 0.55)
        for _ in range(26):
            u = rng.uniform(0.0, 0.32) if rng.random() < 0.7 else rng.uniform(0.32, 0.70)
            _maple_leaf(fallen_pen, u, bank_at(u) + rng.uniform(0.004, 0.030), rng.uniform(0.005, 0.008), rng.uniform(-90.0, 90.0))
        for _ in range(14):
            u = rng.uniform(0.28, 0.72)
            _grass_blades(blade_pen, rng, u, bank_at(u) + 0.002, rng.uniform(0.010, 0.018), 5, 0.0011, 0.008)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        limb_mask = a.mask_of(limbs)
        maple_mask = np.maximum.reduce(tiers)
        gap_mask = a.mask_of(gaps) * maple_mask
        fallen_mask = a.mask_of(fallen) * bank_mask
        blade_mask = a.mask_of(blades)
        plume_mask = a.mask_of(plumes)
        rock_mask = a.mask_of(rocks)
        mask = np.maximum.reduce([bank_mask, limb_mask, maple_mask, blade_mask, plume_mask, rock_mask])
        layer = a.blank()
        earth = a.ramp([(0.0, mix(p["moss"], p["near"], 0.40)), (0.66, mix(p["moss"], p["near"], 0.40)), (0.80, mix(p["moss"], p["near"], 0.78)), (1.0, p["near"])])
        a.put(layer, bank_mask, earth)
        a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, p["glow"], 0.30)
        a.put(layer, fallen_mask, mix(p["maple"], p["near"], 0.30), 0.85)
        a.put(layer, rock_mask, mix(p["stone"], p["near"], 0.40))
        a.light(layer, a.rim(rock_mask, -0.004, 0.004, 0.4) * rock_mask, p["stone_light"], 0.35)
        a.put(layer, limb_mask, mix(p["bark"], p["near"], 0.40))
        a.light(layer, a.rim(limb_mask, -0.003, 0.0, 0.3) * limb_mask, p["glow"], 0.30)
        orange = smoothstep(0.50, 0.66, a.noise("heian maple orange", cells=30.0, octaves=2))
        gold = smoothstep(0.74, 0.84, a.noise("heian maple gold", cells=36.0, octaves=2))
        for k, tier in enumerate(tiers):
            a.put(layer, tier, mix(p["maple"], p["near"], 0.28 - k * 0.04))
            a.put(layer, tier * orange, mix(p["maple_light"], p["near"], 0.28), 0.75)
            a.put(layer, tier * gold, mix(p["gold"], p["near"], 0.20), 0.70)
            a.shade(layer, a.rim(tier, 0.0, -0.010, 1.0) * tier, 0.40)
            a.light(layer, a.rim(tier, -0.002, 0.005, 0.5) * tier, p["maple_light"], 0.40)
        branch_gaps = np.maximum(gap_mask, limb_mask * maple_mask * smoothstep(0.55, 0.70, a.noise("heian maple gaps", cells=40.0, octaves=2)))
        a.put(layer, branch_gaps, mix(p["bark"], p["near"], 0.55), 0.85)
        a.put(layer, blade_mask, mix(p["grass"], p["near"], 0.40))
        a.light(layer, a.rim(blade_mask, -0.0015, 0.0, 0.2) * blade_mask, p["grass_light"], 0.35)
        a.put(layer, plume_mask, mix(p["plume"], p["near"], 0.12))
        a.shade(layer, a.rim(plume_mask, 0.002, -0.002, 0.3) * plume_mask, 0.25)
        a.shade(layer, a.rim(mask, 0.004, -0.003, 1.0) * mask, 0.20)
        haze(a, layer, p["low"], 0.07, None)
        return layer
    layer = _air(a, p, "heian autumn air", p["low"], 0.20, scale(p["near"], 0.8), 0.20)
    a.put(layer, shafts(a, "heian shafts", 4, -0.16, 0.0, 0.85, 0.05), p["glow"], 0.09)
    return layer


def heian_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Pampas grass with plumes stands from below at two places, and a branch
    of maple with leaves hangs from above at one place."""
    del layer_lights
    rng = art_.rand("heian foreground")
    for k in range(2):
        u0 = 0.12 + (k + rng.uniform(0.2, 0.8)) * 0.38
        for _ in range(9):
            u = u0 + rng.uniform(-0.012, 0.012)
            top = REST_BOTTOM - rng.uniform(-0.004, 0.008)
            lean = rng.uniform(-0.04, 0.04)
            pen.line(_arch((u, 1.0), (u + lean * 0.3, top + 0.10), (u + lean, top), 10), 0.0015)
        for j in range(3):
            u = u0 + (j - 1) * 0.012
            top = (u + 0.008, REST_BOTTOM - 0.014 + j % 2 * 0.004)
            pen.line(_arch((u, 1.0), (u, top[1] + 0.12), top, 10), 0.0014)
            for i in range(7):
                end = polar(*top, rng.uniform(0.014, 0.022), -50.0 + i * 9.0)
                pen.line(_arch(top, polar(*top, 0.008, -50.0 + i * 9.0), (end[0], end[1] + 0.010), 5), 0.0015)
    u = rng.uniform(0.40, 0.60)
    branch = _arch((u - 0.07, 0.0), (u - 0.01, 0.24), (u + 0.08, 0.345), 14)
    pen.line(branch, 0.0030)
    for i in range(6, 15):
        x, y = branch[i]
        s = rng.uniform(0.012, 0.016)
        cy = min(y + s * 1.2, 0.384 - s * 0.7)
        pen.line([(x, y), (x + rng.uniform(-0.004, 0.004), cy + s * 0.5)], 0.0010)
        _maple_leaf(pen, x, cy, s, 180.0 + rng.uniform(-30.0, 30.0))


# ---------------------------------------------------------------------------
# Hanyang: Gyeongbokgung under Bugaksan in early summer
# ---------------------------------------------------------------------------


HANYANG = {
    "top": (60, 116, 184),
    "mid": (156, 196, 224),
    "low": (236, 236, 220),
    "glow": (255, 240, 200),
    "sun": (255, 250, 230),
    "cloud": (252, 252, 248),
    "cloud_shadow": (186, 198, 212),
    "granite": (198, 194, 186),
    "granite_light": (240, 238, 230),
    "granite_dark": (130, 128, 126),
    "slope": (66, 108, 64),
    "ridges": (104, 128, 112),
    "pine": (42, 80, 50),
    "pine_light": (110, 150, 80),
    "bark": (196, 96, 58),
    "bark_dark": (110, 70, 52),
    "city_wall": (228, 224, 212),
    "tile": (76, 80, 90),
    "tile_light": (150, 156, 166),
    "ridge_white": (232, 230, 222),
    "column": (178, 54, 40),
    "column_light": (224, 112, 82),
    "door": (118, 58, 46),
    "green": (54, 140, 108),
    "blue": (62, 120, 152),
    "red": (192, 62, 48),
    "stone": (206, 200, 186),
    "stone_light": (242, 236, 222),
    "stone_dark": (140, 134, 122),
    "paving": (178, 172, 158),
    "grass": (92, 126, 60),
    "grass_light": (164, 186, 96),
    "peony": (226, 98, 138),
    "peony_light": (250, 178, 198),
    "peony_white": (246, 238, 234),
    "leaf": (58, 104, 56),
    "leaf_light": (128, 168, 88),
    "far": (214, 222, 226),
    "near": (30, 40, 32),
    "near_light": (130, 140, 96),
}

#: The foot of the lower stone terrace of the great hall, in the court.
HANYANG_TERRACE = 0.666


def _paljak_roof(roof: Pen, ridge: Pen, u: float, eave_v: float, half: float, h: float, lift: float) -> None:
    """A hipped-and-gabled roof of Korea (a paljak roof) seen from the
    front: a long eave that sags a little in the middle and sweeps up hard
    at its corners, a curved slope of grey tiles up to the ridge, and a
    white ridge whose ends turn up. `h` is the height from the eave to the
    ridge."""
    sag = h * 0.05
    _upturned(roof, u - half, u + half, eave_v, lift, h * 0.13, sag, 4.0)
    eave = [(u - half * 0.97 + half * 1.94 * t, eave_v - lift * 0.9 * abs(2.0 * t - 1.0) ** 4.0 + sag * math.sin(math.pi * t)) for t in np.linspace(0.0, 1.0, 24)]
    ridge_v = eave_v - h
    left = _arch(eave[0], (u - half * 0.80, eave_v - h * 0.15), (u - half * 0.60, ridge_v), 10)
    right = _arch((u + half * 0.60, ridge_v), (u + half * 0.80, eave_v - h * 0.15), eave[-1], 10)
    roof.poly(left + right + eave[::-1])
    ridge.line([(u - half * 0.66, ridge_v - h * 0.13), (u - half * 0.60, ridge_v), (u + half * 0.60, ridge_v), (u + half * 0.66, ridge_v - h * 0.13)], h * 0.09)


def _geunjeongjeon(stone: Pen, rail: Pen, columns: Pen, doors: Pen, bands: Pen, roof: Pen, ridge: Pen, u: float, v: float, s: float) -> None:
    """Geunjeongjeon, the throne hall of Gyeongbokgung: it stands on two
    terraces of granite, each with a stone rail, and a stair in the middle.
    Red columns hold two storeys of grey tile roof, each a hipped-and-gabled
    roof with eaves that sweep up at the corners. Under each eave is a band
    of painted brackets (dancheong). `(u, v)` is the foot of the lower
    terrace and `s` the scale."""
    stone.rect(u - s * 0.78, v - s * 0.045, u + s * 0.78, v + 0.002)
    stone.rect(u - s * 0.64, v - s * 0.090, u + s * 0.64, v - s * 0.045)
    for top, half in ((v - s * 0.045, 0.78), (v - s * 0.090, 0.64)):
        rail.rect(u - s * half, top - s * 0.020, u + s * half, top - s * 0.015)
        for k in range(int(half * 40) + 1):
            x = u - s * half + k * s * half * 2.0 / int(half * 40)
            if abs(x - u) > s * 0.07:
                rail.line([(x, top), (x, top - s * 0.022)], s * 0.006)
    stone.rect(u - s * 0.07, v - s * 0.092, u + s * 0.07, v + 0.002)
    floor_v = v - s * 0.090
    body_top = floor_v - s * 0.19
    doors.rect(u - s * 0.44, body_top, u + s * 0.44, floor_v)
    for k in range(9):
        x = u - s * 0.44 + k * s * 0.11
        columns.line([(x, floor_v), (x, body_top)], s * 0.020)
    bands.rect(u - s * 0.46, body_top - s * 0.035, u + s * 0.46, body_top + 0.001)
    _paljak_roof(roof, ridge, u, body_top - s * 0.025, s * 0.64, s * 0.12, s * 0.065)
    # The upper storey: a short wall of columns and painted brackets over
    # the lower roof, and the upper roof.
    up_floor = body_top - s * 0.135
    up_top = up_floor - s * 0.060
    doors.rect(u - s * 0.32, up_top, u + s * 0.32, up_floor)
    for k in range(7):
        x = u - s * 0.32 + k * s * 0.64 / 6.0
        columns.line([(x, up_floor), (x, up_top)], s * 0.016)
    bands.rect(u - s * 0.34, up_top - s * 0.030, u + s * 0.34, up_top + 0.001)
    _paljak_roof(roof, ridge, u, up_top - s * 0.020, s * 0.56, s * 0.17, s * 0.07)


def history_hanyang(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = HANYANG
    sun_at = (0.18, 0.30)
    terrace_v = HANYANG_TERRACE
    if layer_key == "sky":
        # A clear morning of early summer with a few white clouds. Bugaksan
        # rises behind the palace: a dome of pale granite over slopes of
        # pine. Lower ridges go off to each side, and the wall of the city
        # follows their crests.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.88)), (0.24, p["top"]), (0.46, p["mid"]), (HORIZON - 0.01, p["low"]),
                                 (HORIZON + 0.002, mix(p["slope"], p["low"], 0.45)), (1.0, mix(p["slope"], p["low"], 0.30))]))
        _sun(a, layer, *sun_at, 0.022, p["sun"], p["glow"], 0.55)
        _heaps(a, layer, "hanyang heaps", ((0.32, 0.40, 0.05, 0.032), (0.86, 0.36, 0.06, 0.040), (0.98, 0.44, 0.03, 0.020)), p["cloud"], p["cloud_shadow"], 0.85)
        above = smoothstep(HORIZON + 0.004, HORIZON + 0.001, a.v)
        cols = np.linspace(0.0, 1.0, a.n)
        # The far ridges first, pale; then the near ridges and Bugaksan.
        far_mask, _ = a.ridge("hanyang far ridges", HORIZON - 0.030, 0.016, cells=4.0, octaves=4, sharp=0.3)
        far_mask = far_mask * above
        colour = mix(p["ridges"], p["mid"], 0.55)
        a.put(layer, far_mask, a.ramp([(0.0, colour), (HORIZON - 0.05, colour), (HORIZON - 0.004, mix(colour, p["low"], 0.50)), (1.0, p["low"])]))
        # Bugaksan: a steep dome in the middle. Inwangsan, rocky and lower, at
        # the left; the low ridges of the city between and at the right.
        _, ridge_line = a.ridge("hanyang ridges", HORIZON - 0.060, 0.030, cells=3.0, octaves=4, sharp=0.15)
        rise = HORIZON - ridge_line
        rise = rise * (0.75 + 0.25 * smoothstep(0.2, 0.0, np.abs(cols - 0.5)))
        # Each dome has a round top and long flanks that curve in; the
        # flank to the right is the longer one.
        for c, hh, left, right in ((0.59, 0.185, 0.16, 0.24), (0.19, 0.112, 0.12, 0.16)):
            x = np.clip(np.where(cols < c, (c - cols) / left, (cols - c) / right), 0.0, 1.0)
            dome = hh * (1.0 - x**1.8) ** 2.2
            rise = np.maximum(rise, dome)
        rise += 0.012 * np.exp(-(((cols - 0.70) / 0.025) ** 2))
        crags = (a.line_noise("hanyang crags", cells=40.0, octaves=2) - 0.5) * 0.005
        top = (HORIZON + 0.003 - rise - crags).astype(np.float32)
        mount = _land(a, top) * above
        a.put(layer, mount, a.ramp([(0.0, mix(p["slope"], p["mid"], 0.25)), (0.48, mix(p["slope"], p["mid"], 0.22)), (HORIZON - 0.004, mix(p["slope"], p["low"], 0.40)), (1.0, p["low"])]))
        trees = mount * smoothstep(0.45, 0.70, a.noise("hanyang pines", cells=200.0, octaves=2))
        a.shade(layer, trees, 0.14)
        a.light(layer, mount * smoothstep(0.60, 0.80, a.noise("hanyang pine light", cells=140.0, octaves=2)), mix(p["pine_light"], p["mid"], 0.3), 0.25)
        # The granite: bare rock on the dome of Bugaksan and on the high
        # crags, in long smooth faces, and in knobs on the ridges.
        depth = a.v - top[None, :]
        peak = np.maximum(a.spot(0.59, HORIZON - 0.16, 0.12, 1.0, squash=0.8), 0.6 * a.spot(0.19, HORIZON - 0.10, 0.08, 1.0, squash=0.8))
        rock_faces = smoothstep(0.40, 0.62, a.noise("hanyang rock faces", cells=30.0, octaves=3, stretch=0.35))
        rock = mount * np.clip(smoothstep(0.050, 0.020, depth) * smoothstep(0.2, 0.5, peak) + rock_faces * smoothstep(0.3, 0.6, peak) * smoothstep(0.11, 0.05, depth), 0.0, 1.0)
        knobs = mount * smoothstep(0.012, 0.004, depth) * smoothstep(0.62, 0.78, a.noise("hanyang knobs", cells=36.0, octaves=2)) * (1.0 - peak)
        rock = np.maximum(rock, knobs)
        a.put(layer, rock, mix(p["granite"], p["mid"], 0.15))
        a.light(layer, rock * smoothstep(0.55, 0.80, a.noise("hanyang rock light", cells=90.0, octaves=2, stretch=0.3)), p["granite_light"], 0.45)
        a.shade(layer, rock * smoothstep(0.60, 0.85, a.noise("hanyang rock seams", cells=160.0, octaves=1, stretch=0.15)), 0.18)
        a.light(layer, a.rim(mount, 0.006, 0.0, 1.0) * mount, mix(p["granite_light"], p["glow"], 0.4), 0.35)
        a.shade(layer, a.rim(mount, -0.008, 0.0, 2.0) * mount, 0.10)
        # Pines that stand on the crest line, in small dark tufts.
        tufts = mount * smoothstep(0.006, 0.0, depth) * smoothstep(0.55, 0.70, a.noise("hanyang crest pines", cells=200.0, octaves=1)) * (1.0 - smoothstep(0.3, 0.6, peak))
        a.put(layer, tufts, mix(p["pine"], p["mid"], 0.20), 0.6)
        # The wall of the city: a pale line of stone with a parapet that
        # follows the crests a little under them, and climbs over the
        # shoulder of Bugaksan.
        # Where a ridge is lower than `cap`, the wall runs along its crest;
        # on the high domes it goes across the face, and climbs as it goes.
        cap = np.interp(cols, [0.0, 0.10, 0.19, 0.30, 0.45, 0.59, 0.72, 1.0], [0.050, 0.060, 0.072, 0.050, 0.060, 0.115, 0.080, 0.050])
        wall_line = (HORIZON + 0.012 - np.minimum(rise, cap)).astype(np.float32)
        wall = mount * smoothstep(0.0022, 0.0010, np.abs(a.v - wall_line[None, :])) * smoothstep(HORIZON - 0.012, HORIZON - 0.020, a.v)
        battlements = np.clip(1.0 - np.abs(((a.u * 420.0) % 1.0) - 0.5) / 0.22, 0.0, 1.0)
        crenel = mount * smoothstep(0.0012, 0.0004, np.abs(a.v - wall_line[None, :] + 0.0026)) * battlements * smoothstep(HORIZON - 0.012, HORIZON - 0.020, a.v)
        a.put(layer, np.maximum(wall, crenel), p["city_wall"], 0.95)
        a.shade(layer, smoothstep(0.0016, 0.0004, np.abs(a.v - wall_line[None, :] - 0.0026)) * mount * smoothstep(HORIZON - 0.012, HORIZON - 0.020, a.v), 0.30)
        a.tint(layer, fog(a, "hanyang low haze", HORIZON - 0.006, 0.016, 3.0), p["low"], 0.55)
        _textbook(a, layer, 0.07)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far hanyang")
        # The pine woods at the foot of the mountain, behind the palace.
        woods, wood_pen = a.drawing()
        _canopy(wood_pen, rng, np.full(a.n, HORIZON + 0.022, dtype=np.float32), -0.02, 1.02, 0.010, 0.006, 0.012, 300)
        # Pines that stand over the roofs at the sides.
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        for gu, gv, gh, count in ((0.05, 0.640, 0.085, 3), (0.17, 0.636, 0.065, 2), (0.83, 0.636, 0.070, 2), (0.95, 0.640, 0.090, 3)):
            for _ in range(count):
                _red_pine(trunk_pen, crown_pen, rng, gu + rng.uniform(-0.03, 0.03), gv + rng.uniform(-0.003, 0.003), gh * rng.uniform(0.8, 1.15), rng.uniform(-0.15, 0.15))
        # The halls behind the throne hall, and the long cloister round the
        # court, with red posts under a low roof of tiles.
        back = {key: a.drawing() for key in ("roof", "ridge", "walls")}
        for bu, bv, half in ((0.30, 0.622, 0.060), (0.71, 0.622, 0.066), (0.40, 0.614, 0.040), (0.60, 0.612, 0.046)):
            back["walls"][1].rect(bu - half * 0.70, bv - 0.012, bu + half * 0.70, bv + 0.002)
            _paljak_roof(back["roof"][1], back["ridge"][1], bu, bv - 0.011, half, 0.016, 0.006)
        cloister = {key: a.drawing() for key in ("roof", "ridge", "posts", "wall")}
        cv = 0.646
        cloister["wall"][1].rect(-0.02, cv - 0.010, 1.02, cv + 0.002)
        for k in range(52):
            x = -0.01 + k * 0.02
            cloister["posts"][1].line([(x, cv + 0.002), (x, cv - 0.016)], 0.0022)
        _upturned(cloister["roof"][1], -0.03, 1.03, cv - 0.017, 0.0, 0.003)
        cloister["roof"][1].poly([(-0.03, cv - 0.016), (1.03, cv - 0.016), (1.03, cv - 0.027), (-0.03, cv - 0.027)])
        cloister["ridge"][1].rect(-0.03, cv - 0.029, 1.03, cv - 0.026)
        # Geunjeongjeon on its terraces in the middle.
        names = ("stone", "rail", "columns", "doors", "bands", "roof", "ridge")
        hall = {key: a.drawing() for key in names}
        _geunjeongjeon(*(hall[k][1] for k in names), 0.50, terrace_v, 0.190)
        # The court: rough slabs of granite, the raised royal path from the
        # stair toward the eye, and the rows of rank stones beside it.
        court = smoothstep(cv - 0.001, cv + 0.001, a.v)
        path, path_pen = a.drawing()
        path_pen.poly([(0.488, terrace_v), (0.512, terrace_v), (0.56, 1.0), (0.44, 1.0)])
        ranks, rank_pen = a.drawing()
        for j in range(8):
            v = terrace_v + 0.008 + j * (0.010 + j * 0.002)
            off = 0.055 + (v - terrace_v) * 0.9
            hgt = 0.004 + (v - terrace_v) * 0.08
            for side in (-1.0, 1.0):
                x = 0.5 + side * off
                rank_pen.poly([(x - hgt * 0.30, v), (x + hgt * 0.30, v), (x + hgt * 0.24, v - hgt), (x - hgt * 0.24, v - hgt)])
        wood_mask = a.mask_of(woods)
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        bm = {key: a.mask_of(img) for key, (img, _) in back.items()}
        cm = {key: a.mask_of(img) for key, (img, _) in cloister.items()}
        hm = {key: a.mask_of(img) for key, (img, _) in hall.items()}
        hall_mask = np.maximum.reduce(list(hm.values()))
        path_mask = a.mask_of(path) * court
        rank_mask = a.mask_of(ranks)
        ground = smoothstep(HORIZON + 0.014, HORIZON + 0.018, a.v)
        mask = np.maximum.reduce([wood_mask, ground, trunk_mask, crown_mask, *bm.values(), *cm.values(), hall_mask, court, rank_mask])
        layer = solid(a, mask, mix(p["pine"], p["far"], 0.40), p["pine"], HORIZON, 0.70, "hanyang far", 0.03)
        a.put(layer, wood_mask, mix(p["pine"], p["far"], 0.30))
        a.shade(layer, wood_mask * smoothstep(0.55, 0.80, a.noise("hanyang wood lumps", cells=160.0, octaves=2)), 0.15)
        a.light(layer, a.rim(wood_mask, 0.002, 0.003, 0.3) * wood_mask, mix(p["pine_light"], p["glow"], 0.4), 0.45)
        # The halls behind: dark tile roofs with white ridges.
        a.put(layer, bm["walls"], mix(p["column"], p["far"], 0.30))
        a.put(layer, bm["roof"], mix(p["tile"], p["far"], 0.25))
        a.light(layer, a.rim(bm["roof"], 0.0, 0.002, 0.0) * bm["roof"], p["tile_light"], 0.5)
        a.put(layer, bm["ridge"], mix(p["ridge_white"], p["far"], 0.2))
        # The pines over the cloister: orange-red trunks, flat dark crowns.
        a.put(layer, trunk_mask, mix(p["bark"], p["far"], 0.15))
        a.put(layer, crown_mask, mix(p["pine"], p["far"], 0.15))
        a.light(layer, a.rim(crown_mask, 0.002, 0.003, 0.3) * crown_mask, mix(p["pine_light"], p["glow"], 0.3), 0.50)
        # The cloister: a white wall under red posts and a dark roof.
        a.put(layer, cm["wall"], mix(p["stone_light"], p["far"], 0.10))
        a.put(layer, cm["wall"] * smoothstep(cv - 0.005, cv - 0.004, a.v), mix(p["stone"], p["far"], 0.10))
        a.put(layer, cm["posts"], p["column"])
        a.put(layer, cm["roof"], p["tile"])
        a.light(layer, cm["roof"] * smoothstep(cv - 0.020, cv - 0.027, a.v), p["tile_light"], 0.35)
        a.put(layer, a.rim(cm["roof"], 0.0, -0.002, 0.0) * cm["roof"], mix(p["green"], p["tile"], 0.3), 0.8)
        a.put(layer, cm["ridge"], p["ridge_white"])
        # The court: pale granite slabs with dark joints, the royal path a
        # little paler, and the rank stones.
        slabs = np.maximum(np.clip(1.0 - np.abs((((a.u - 0.5) / (0.2 + (a.v - cv) * 6.0) * 30.0) % 1.0) - 0.5) / 0.05, 0.0, 1.0) * smoothstep(0.3, 0.6, a.noise("hanyang slab gaps", cells=50.0, octaves=1)),
                           np.clip(1.0 - np.abs((((np.clip(a.v - cv, 0.0, None) * 30.0) ** 0.6 * 9.0) % 1.0) - 0.5) / 0.06, 0.0, 1.0))
        a.put(layer, court, a.ramp([(0.0, mix(p["paving"], p["far"], 0.3)), (cv, mix(p["paving"], p["far"], 0.3)), (0.72, p["paving"]), (1.0, p["paving"])]))
        a.light(layer, court * smoothstep(0.50, 0.80, a.noise("hanyang paving", cells=30.0, octaves=2, stretch=3.0)), p["stone_light"], 0.15)
        a.shade(layer, court * slabs * smoothstep(cv + 0.003, cv + 0.02, a.v), 0.10)
        a.put(layer, path_mask, mix(p["stone"], p["stone_light"], 0.3))
        a.shade(layer, a.rim(path_mask, -0.002, 0.0, 0.0) * path_mask, 0.25)
        a.put(layer, rank_mask, p["stone"])
        a.shade(layer, a.rim(rank_mask, -0.0015, 0.0, 0.0) * rank_mask, 0.30)
        a.shade(layer, court * a.blur(np.clip(a.shift(rank_mask, -0.004, 0.0) - rank_mask, 0.0, 1.0), 1.0), 0.25)
        # The throne hall: granite terraces lit on their tops, a pale rail,
        # red columns, red-brown lattice doors, a band of green and blue
        # painted brackets with red under each eave, and grey roofs with
        # white ridges.
        a.put(layer, hm["stone"], p["stone"])
        a.light(layer, hm["stone"] * smoothstep(0.55, 0.85, a.noise("hanyang terrace light", cells=40.0, octaves=2)), p["stone_light"], 0.25)
        a.light(layer, a.rim(hm["stone"], 0.0, 0.003, 0.0) * hm["stone"], p["stone_light"], 0.85)
        a.shade(layer, a.blur(np.clip(a.shift(np.maximum(hm["stone"], hm["rail"]), 0.0, 0.004) - hm["stone"] - hm["rail"], 0.0, 1.0), 1.0) * court, 0.45)
        a.shade(layer, hm["stone"] * np.clip(1.0 - np.abs(((a.v * 1300.0) % 1.0) - 0.5) / 0.10, 0.0, 1.0) * (np.abs(a.u - 0.5) < 0.012), 0.25)
        a.shade(layer, hm["stone"] * smoothstep(0.55, 0.85, a.noise("hanyang terrace blocks", cells=260.0, octaves=1, stretch=3.0)), 0.10)
        a.put(layer, hm["rail"], p["stone_light"])
        a.shade(layer, a.rim(hm["rail"], 0.0, -0.0012, 0.0) * hm["rail"], 0.25)
        a.put(layer, hm["doors"], p["door"])
        grid = np.maximum(np.clip(1.0 - np.abs(((a.u * 900.0) % 1.0) - 0.5) / 0.10, 0.0, 1.0), np.clip(1.0 - np.abs(((a.v * 900.0) % 1.0) - 0.5) / 0.10, 0.0, 1.0))
        a.shade(layer, hm["doors"] * grid, 0.25)
        a.put(layer, hm["columns"], p["column"])
        a.light(layer, a.rim(hm["columns"], 0.0015, 0.0, 0.0) * hm["columns"], p["column_light"], 0.45)
        a.put(layer, hm["bands"], p["green"])
        blocks = (a.u * 260.0) % 1.0
        a.put(layer, hm["bands"] * (blocks < 0.35), p["blue"])
        a.put(layer, hm["bands"] * (np.abs(blocks - 0.62) < 0.08), p["red"])
        a.light(layer, hm["bands"] * np.clip(1.0 - np.abs(((a.v * 700.0) % 1.0) - 0.5) / 0.12, 0.0, 1.0), p["stone_light"], 0.35)
        a.put(layer, hm["roof"], p["tile"])
        a.shade(layer, hm["roof"] * np.clip(1.0 - np.abs(((a.u * 520.0) % 1.0) - 0.5) / 0.18, 0.0, 1.0), 0.18)
        a.light(layer, a.rim(hm["roof"], 0.003, 0.0, 0.4) * hm["roof"], p["tile_light"], 0.50)
        a.light(layer, a.rim(hm["roof"], 0.0, -0.0025, 0.0) * hm["roof"], p["tile_light"], 0.45)
        a.put(layer, hm["ridge"], p["ridge_white"])
        a.tint(layer, fog(a, "hanyang court haze", HORIZON + 0.012, 0.012, 3.0) * mask * (1.0 - hall_mask), p["low"], 0.30)
        haze(a, layer, p["low"], 0.06, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near hanyang")
        bank, ground, bank_at = _bank(a, "near hanyang", 0.034, 0.030)
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        leaves, leaf_pen = a.drawing()
        flowers, flower_pen = a.drawing()
        whites, white_pen = a.drawing()
        grass, grass_pen = a.drawing()
        rocks, rock_pen = a.drawing()
        # Two red pines that lean at the left; a bed of peonies in flower at
        # the right, with a garden stone. The middle is calm.
        for u, h, lean in ((0.07, 0.40, 0.12), (0.16, 0.30, -0.16)):
            _red_pine(trunk_pen, crown_pen, rng, u, bank_at(u) + 0.006, h, lean)
        rock_pen.ellipse(0.76, bank_at(0.76) - 0.006, 0.030, 0.018)
        for _ in range(22):
            u = rng.uniform(0.78, 1.0)
            base = bank_at(u) + 0.004
            h = rng.uniform(0.030, 0.075)
            top = (u + rng.uniform(-0.012, 0.012), base - h)
            leaf_pen.line(_arch((u, base), (u, base - h * 0.5), top, 6), 0.0022)
            for _ in range(3):
                # The leaves of the peony: cut into three pointed lobes.
                lu, lv = top[0] + rng.uniform(-0.02, 0.02), top[1] + rng.uniform(0.008, h * 0.7)
                for ang in (-40.0, 0.0, 40.0):
                    tip = polar(lu, lv, rng.uniform(0.014, 0.020), ang - 90.0 + rng.uniform(-60.0, 60.0))
                    _leaf(leaf_pen, [(lu, lv), ((lu + tip[0]) * 0.5, (lv + tip[1]) * 0.5 - 0.002), tip], 0.0045, 0.6)
            if rng.random() < 0.55:
                r = rng.uniform(0.010, 0.016)
                pen = white_pen if rng.random() < 0.25 else flower_pen
                # The flower: a cup of round petals, wider than it is high.
                for k in range(7):
                    ang = -90.0 + (k - 3) * 28.0
                    pu, pv = polar(top[0], top[1], r * 0.55, ang)
                    pen.ellipse(pu, pv, r * 0.52, r * 0.42)
                pen.ellipse(top[0], top[1] + r * 0.15, r * 0.70, r * 0.45)
        for _ in range(14):
            u = rng.uniform(0.26, 0.72)
            _grass_blades(grass_pen, rng, u, bank_at(u) + 0.002, rng.uniform(0.010, 0.018), 5, 0.0011, 0.008)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        leaf_mask = a.mask_of(leaves)
        flower_mask = a.mask_of(flowers)
        white_mask = a.mask_of(whites)
        grass_mask = a.mask_of(grass)
        rock_mask = a.mask_of(rocks)
        mask = np.maximum.reduce([bank_mask, trunk_mask, crown_mask, leaf_mask, flower_mask, white_mask, grass_mask, rock_mask])
        layer = a.blank()
        earth = a.ramp([(0.0, mix(p["grass"], p["near"], 0.40)), (0.66, mix(p["grass"], p["near"], 0.40)), (0.80, mix(p["grass"], p["near"], 0.78)), (1.0, p["near"])])
        a.put(layer, bank_mask, earth)
        a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, p["glow"], 0.30)
        a.put(layer, grass_mask, mix(p["grass"], p["near"], 0.35))
        a.light(layer, a.rim(grass_mask, 0.0015, 0.0, 0.2) * grass_mask, p["grass_light"], 0.30)
        a.put(layer, rock_mask, mix(p["stone"], p["near"], 0.40))
        a.light(layer, a.rim(rock_mask, 0.004, 0.004, 0.4) * rock_mask, p["stone_light"], 0.40)
        # The pines: orange-red bark in plates high up, grey low down; dark
        # crowns lit on their tops.
        bark = a.ramp([(0.0, mix(p["bark"], p["near"], 0.15)), (0.50, mix(p["bark"], p["near"], 0.20)), (0.66, mix(p["bark_dark"], p["near"], 0.35)), (1.0, p["near"])])
        a.put(layer, trunk_mask, bark)
        a.shade(layer, trunk_mask * smoothstep(0.50, 0.78, a.noise("hanyang pine plates", cells=160.0, octaves=1, stretch=0.4)), 0.25)
        a.light(layer, a.rim(trunk_mask, 0.003, 0.0, 0.3) * trunk_mask, p["glow"], 0.45)
        a.put(layer, crown_mask, mix(p["pine"], p["near"], 0.35))
        a.light(layer, crown_mask * smoothstep(0.55, 0.80, a.noise("hanyang needles", cells=420.0, octaves=1, stretch=3.0)), p["pine_light"], 0.14)
        a.light(layer, a.rim(crown_mask, 0.002, 0.004, 0.4) * crown_mask, mix(p["pine_light"], p["glow"], 0.3), 0.45)
        # The peonies: deep green leaves, pink and white flowers lit on the
        # side to the sun.
        a.put(layer, leaf_mask, mix(p["leaf"], p["near"], 0.30))
        a.light(layer, a.rim(leaf_mask, 0.002, 0.002, 0.2) * leaf_mask, p["leaf_light"], 0.40)
        a.put(layer, flower_mask, p["peony"])
        a.light(layer, a.rim(flower_mask, 0.003, 0.003, 0.3) * flower_mask, p["peony_light"], 0.60)
        a.shade(layer, a.rim(flower_mask, -0.003, -0.002, 0.3) * flower_mask, 0.25)
        a.put(layer, white_mask, p["peony_white"])
        a.shade(layer, a.rim(white_mask, -0.003, -0.002, 0.3) * white_mask, 0.20)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.18)
        haze(a, layer, p["low"], 0.07, None)
        return layer
    layer = _air(a, p, "hanyang summer air", p["low"], 0.18, scale(p["near"], 0.8), 0.18)
    a.put(layer, shafts(a, "hanyang shafts", 4, 0.14, 0.0, 0.85, 0.05), p["glow"], 0.07)
    return layer


def hanyang_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Peonies on tall stalks stand from below at two places, each a few
    round flowers and cut leaves. A bough of pine with tufts of long
    needles hangs from above at one place."""
    del layer_lights
    rng = art_.rand("hanyang foreground")
    for k in range(2):
        u0 = 0.12 + (k + rng.uniform(0.2, 0.8)) * 0.38
        for j in range(3):
            u = u0 + (j - 1) * 0.016
            top = (u + rng.uniform(-0.006, 0.006), REST_BOTTOM - 0.004 - (j % 2) * 0.006)
            pen.line(_arch((u, 1.0), (u, top[1] + 0.10), top, 10), 0.0018)
            r = 0.008 + (j % 2) * 0.002
            for i in range(5):
                pu, pv = polar(top[0], top[1], r * 0.55, -90.0 + (i - 2) * 34.0)
                pen.ellipse(pu, pv, r * 0.50, r * 0.40)
            pen.ellipse(top[0], top[1] + r * 0.2, r * 0.70, r * 0.45)
            lv = top[1] + 0.030
            for s in (-1.0, 1.0):
                tip = (u + s * 0.018, lv - 0.004)
                _leaf(pen, [(u, lv + 0.004), (u + s * 0.010, lv - 0.006), tip], 0.0040, 0.6)
    u = rng.uniform(0.40, 0.60)
    bough = _arch((u - 0.05, 0.0), (u, 0.22), (u + 0.10, 0.345), 12)
    pen.line(bough, 0.0032)
    for x, y in bough[4::2]:
        for j in range(9):
            end = polar(x, y, 0.028, 40.0 + j * 12.0 + rng.uniform(-4.0, 4.0))
            pen.line([(x, y), (end[0], min(end[1], 0.384))], 0.0011)
