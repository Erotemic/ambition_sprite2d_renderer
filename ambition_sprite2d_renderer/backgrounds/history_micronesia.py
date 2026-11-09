"""The scenes of the History dimension: Micronesia.

The History dimension is a grid. East is later, and each floor is a region
of the world. These rooms are on the floor of Oceania, in the row of
Micronesia. They show a coast of Guåhan in the time of the latte houses; a
low coral atoll of the Marshall Islands; Nan Madol off Pohnpei at dusk; a
village path of Yap with its stone money; Nauru when its phosphate was dug
out; and Bikini Atoll in 1946, after its people were moved away. They use
the same sepia of an old textbook and the same rules as `history_eras.py`
and `history_oceania.py`. The people of these places show skill, learning
and courage of their own; nothing here is a joke on them.

- ``history_marianas`` (Guåhan, the Marianas, about 1000-1670). A bright
  day of the trade wind with heap clouds. At the left a high headland of
  pale grey-cream limestone with dark green jungle on its top. Along the
  coast under it, coconut palms and breadfruit trees, and among them two
  houses of the Chamorro on latte: two rows of stone pillars, each with its
  capstone flat face up, under a steep roof of thatch. A sakman, the fast
  proa with one hull, an outrigger and a big triangular sail, on the
  lagoon, and small canoes. The white line of surf on the reef far out,
  and fruit bats (fanihi) that fly far off and hang in a breadfruit tree.
- ``history_marshalls`` (an atoll of the Marshall Islands, about
  1500-1900). A big sky with tall white heap clouds over the ocean. A long
  low islet with no hill at all: coconut palms, pandanus and a few low
  houses with steep roofs of thatch, a canoe pulled up on the beach. At the
  right the islet ends; past the white line of the reef the dark blue open
  ocean shows long, regular swells, the swells that the navigators read.
  A proa with its sail up on the calm pale lagoon.
- ``history_nan_madol`` (Nan Madol, off Pohnpei, about 1180-1628). Dusk:
  a low warm sun, long shadows and mist on the water. The islets of black
  basalt on the reef: high walls of columns laid crosswise like a log
  cabin, one course along the wall and the next across it with the ends
  out, and the corners lifted higher like the prow of a ship. Canals of
  dark green water between the islets, mangroves at the edge of the water,
  and behind them the steep green mountains of Pohnpei with cloud on their
  tops. No tomb is shown.
- ``history_yap`` (Yap, about 1500-1900). Warm green light. A path paved
  with flat stones under betel palms and coconut palms, with rai, the stone
  money (white-grey discs of limestone with a hole in the middle), on edge
  in a row along it. Far off, a faluw, the men's house, on a platform of
  stones, with a tall steep roof and high pointed gables. A shore of
  mangroves and the lagoon past it.
- ``history_nauru`` (Nauru, about 1920-1968). Half sober. Clear light. At
  the left the "topside": a pale, bare field of grey-white limestone
  pinnacles, with the brown phosphate dug out from between them. At the
  right the narrow green belt of the coast with coconut palms and a few
  plain sheds; a steel cantilever stands on the edge of the reef, its long
  arm out over the water to a steamship at anchor. Frigatebirds high in the
  sky. Nobody is shown.
- ``history_bikini`` (Bikini Atoll, 1946). Sober, still and muted, in
  greys and grey-greens. A long low islet of coconut palms and pandanus, a
  few empty houses of thatch and of planks with their doors open, the calm
  wide lagoon, and far off in it the grey ships of a fleet at anchor, small
  and side on. A quiet grey-blue sky with flat high cloud.

No picture here shows a deity, a religious sign, a carved figure, a church,
a cross, a grave, a tattoo or a weapon. No cloud of an explosion, no blast
and nothing that falls from the sky is shown at Bikini.

The bright detail is far off or at the edges, and the middle of each near
layer is calm, so the play in front of it reads. The things that drift in the
air are the room's motes (`terrain/motes.py`), not part of these pictures.
"""

from __future__ import annotations

import math

import numpy as np

from .artkit import Art, Pen, mix, polar, scale, smoothstep
from .history_americas_pacific import _coconut_palm, _frigatebird, _mangrove, _pandanus
from .history_east_asia_coast import _bank, _grass_blades, _reflected
from .history_eras import REST_BOTTOM, _air, _heaps, _sun, _textbook
from .history_origins import _arch, _land, _leaf
from .history_southeast_asia import _canoe_ashore
from .parts import HORIZON, cloud_mask, fog, haze, shafts, solid

#: The top of the band of the foreground that a view at rest shows, as
#: `foregrounds.REST_TOP` (that module imports this one, so the number is
#: here too).
REST_TOP = 0.372

# ---------------------------------------------------------------------------
# Parts that more than one room has
# ---------------------------------------------------------------------------


def _sakman(hull: Pen, sail: Pen, u: float, v: float, s: float, facing: float = 1.0) -> None:
    """A proa of Micronesia, as the Chamorro sakman and the canoes of the
    Marshalls: one long narrow hull with ends that rise a little, the float
    of the outrigger on two booms at one side (seen behind the hull, so a
    little higher), a short mast, and a big triangular sail. The sail is
    held between a long yard and a boom that meet at its tack at one end of
    the hull. `(u, v)` is the middle of the waterline, `s` the length."""
    f = facing
    hull.poly([(u - s * 0.50, v - s * 0.08), (u - s * 0.36, v - s * 0.035), (u + s * 0.36, v - s * 0.035), (u + s * 0.50, v - s * 0.08),
               (u + s * 0.40, v + s * 0.012), (u - s * 0.40, v + s * 0.012)])
    hull.poly([(u - s * 0.24, v - s * 0.11), (u + s * 0.24, v - s * 0.11), (u + s * 0.27, v - s * 0.095), (u - s * 0.27, v - s * 0.095)])
    for du in (-0.11, 0.11):
        hull.line([(u + du * s, v - s * 0.03), (u + du * s, v - s * 0.105)], s * 0.012)
    tack = (u + f * s * 0.40, v - s * 0.06)
    peak = (u - f * s * 0.12, v - s * 0.86)
    clew = (u - f * s * 0.40, v - s * 0.14)
    hull.line([(u, v - s * 0.03), (u + f * s * 0.02, v - s * 0.44)], s * 0.014)
    leech = _arch(peak, ((peak[0] + clew[0]) * 0.5 - f * s * 0.10, (peak[1] + clew[1]) * 0.5), clew, 8)
    sail.poly([tack] + leech)
    hull.line([tack, peak], s * 0.012)
    hull.line([tack, clew], s * 0.010)


def _house(roof: Pen, dark: Pen, posts: Pen, u: float, v: float, w: float, h: float, wall: Pen | None = None, door: Pen | None = None) -> None:
    """A low house of an atoll far off: a steep roof of thatch with a ridge
    on short posts, open at its sides, so its inside is in shade. With a
    `wall` pen it has a low wall (of plaited leaf or of planks) in place of
    the open sides, and with a `door` pen a dark doorway that stands open in
    the wall."""
    eave = v - h * 0.32
    if wall is None:
        dark.rect(u - w * 0.80, eave, u + w * 0.80, v + 0.001)
        for k in range(4):
            x = u - w * 0.72 + k * w * 0.48
            posts.line([(x, v + 0.001), (x, eave)], w * 0.06)
    else:
        wall.rect(u - w * 0.80, eave, u + w * 0.80, v + 0.001)
    if door is not None:
        door.rect(u - w * 0.16, eave + h * 0.05, u + w * 0.16, v + 0.001)
    roof.poly([(u - w * 1.05, eave + h * 0.02), (u + w * 1.05, eave + h * 0.02), (u + w * 0.42, v - h), (u - w * 0.42, v - h)])


def _lobed_leaf(pen: Pen, base: tuple[float, float], ang: float, length: float) -> None:
    """A leaf of the breadfruit: big, with deep lobes like fingers that point
    to its tip, three at each side, along a stout rib."""
    tip = polar(*base, length, ang)
    rib = [base, polar(*base, length * 0.5, ang), tip]
    _leaf(pen, _arch(rib[0], rib[1], rib[2], 8), length * 0.12, 0.6)
    for t in (0.30, 0.52, 0.74):
        at = polar(*base, length * t, ang)
        reach = length * 0.30 * (1.0 - 0.35 * t)
        for side in (-1.0, 1.0):
            end = polar(*at, reach, ang + side * 48.0)
            _leaf(pen, [at, polar(*at, reach * 0.5, ang + side * 52.0), end], length * 0.055, 0.5)


def _breadfruit(trunk: Pen, crown: Pen, fruit: Pen, rng, u: float, v: float, h: float) -> list[tuple[float, float]]:
    """A breadfruit tree: a stout grey trunk that forks, a broad round crown
    of big glossy leaves with deep lobes at its edge, and round green fruit
    under the leaves. Returns points under the crown where a thing can
    hang."""
    w = h * 0.05
    trunk.line([(u, v + 0.004), (u + rng.uniform(-0.01, 0.01) * h, v - h * 0.48)], w)
    trunk.poly([(u - w * 1.2, v + 0.004), (u + w * 1.2, v + 0.004), (u + w * 0.5, v - w * 1.5), (u - w * 0.5, v - w * 1.5)])
    for side in (-1.0, 1.0):
        trunk.line([(u, v - h * 0.38), (u + side * h * 0.20, v - h * 0.62)], w * 0.6)
    cv = v - h * 0.70
    for _ in range(16):
        crown.ellipse(u + rng.uniform(-0.30, 0.30) * h, cv + rng.uniform(-0.14, 0.10) * h, h * rng.uniform(0.12, 0.18), h * rng.uniform(0.09, 0.13))
    for k in range(13):
        ang = -190.0 + k * 200.0 / 12.0 + rng.uniform(-6.0, 6.0)
        base = (u + math.cos(math.radians(ang)) * h * 0.30, cv + math.sin(math.radians(ang)) * h * 0.16)
        _lobed_leaf(crown, base, ang, h * rng.uniform(0.15, 0.20))
    for _ in range(6):
        fruit.ellipse(u + rng.uniform(-0.24, 0.24) * h, cv + h * rng.uniform(0.10, 0.17), h * 0.032, h * 0.036)
    return [(u + rng.uniform(-0.26, 0.26) * h, cv + h * 0.16) for _ in range(5)]


def _fanihi(pen: Pen, u: float, v: float, s: float, beat: float = 0.0) -> None:
    """A fruit bat far off in flight: a small dark body and two broad wings,
    each with the scallops of its fingers along its trailing edge."""
    lift = s * 0.25 * beat
    for side in (-1.0, 1.0):
        pen.poly([(u, v - s * 0.10), (u + side * s * 0.45, v - s * 0.32 - lift), (u + side * s * 1.0, v - s * 0.12 - lift * 0.6),
                  (u + side * s * 0.78, v + s * 0.06), (u + side * s * 0.62, v - s * 0.02), (u + side * s * 0.42, v + s * 0.12),
                  (u + side * s * 0.24, v + s * 0.04), (u, v + s * 0.10)])
    pen.ellipse(u, v, s * 0.11, s * 0.16)


def _hanging_bat(pen: Pen, u: float, v: float, s: float) -> None:
    """A fruit bat that hangs from a branch by its feet, its wings wrapped
    round it: a dark drop, narrow at its top, with its small head at the
    bottom."""
    pen.line([(u, v), (u, v + s * 0.20)], s * 0.08)
    pen.ellipse(u, v + s * 0.55, s * 0.20, s * 0.40)
    pen.ellipse(u, v + s * 0.98, s * 0.11, s * 0.10)


def _frond_from_above(pen: Pen, rng, u0: float, count: int, low: float) -> None:
    """The fronds of a coconut palm that hang into the top of the view, seen
    from under the crown: each a long arched rib with narrow leaflets that
    hang down from it. Nothing comes lower than `low`."""
    for j in range(count):
        start = (u0 + (j - (count - 1) * 0.5) * 0.03, 0.0)
        end = (start[0] + (j - (count - 1) * 0.5) * 0.10 + rng.uniform(-0.02, 0.02), low - 0.050 - rng.uniform(0.0, 0.030))
        rib = _arch(start, ((start[0] + end[0]) * 0.5 + (j - (count - 1) * 0.5) * 0.04, 0.10), end, 22)
        pen.line(rib, 0.0034)
        for i, (x, y) in enumerate(rib[1:], 1):
            side = 0.050 * (1.0 - i / 22.0 * 0.55)
            side = max(0.0, min(side, low - y))
            pen.line([(x, y), (x + side * 0.22, y + side)], 0.0018)
            pen.line([(x, y), (x - side * 0.22, y + side)], 0.0018)


def _near_paint(a: Art, layer: np.ndarray, bank_mask: np.ndarray, earth: np.ndarray, glow, strength: float) -> None:
    """Paint the bank of a near layer: its earth, and a soft lit edge on its
    top."""
    a.put(layer, bank_mask, earth)
    a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, glow, strength)


# ---------------------------------------------------------------------------
# The Marianas: Guåhan, about 1000-1670
# ---------------------------------------------------------------------------


MARIANAS = {
    "top": (40, 112, 182),
    "mid": (150, 200, 228),
    "low": (238, 242, 234),
    "glow": (255, 240, 206),
    "sun": (255, 252, 238),
    "cloud": (255, 255, 250),
    "cloud_shadow": (170, 184, 204),
    "ocean": (30, 84, 140),
    "lagoon": (52, 166, 168),
    "lagoon_light": (192, 236, 222),
    "reef": (250, 250, 244),
    "sand": (240, 230, 202),
    "cliff": (214, 206, 184),
    "cliff_shade": (150, 142, 124),
    "clay": (156, 84, 56),
    "jungle": (40, 86, 50),
    "jungle_light": (108, 148, 68),
    "palm": (52, 98, 56),
    "palm_light": (150, 178, 88),
    "trunk": (140, 122, 98),
    "breadfruit": (38, 92, 50),
    "breadfruit_light": (120, 168, 76),
    "fruit": (150, 186, 80),
    "latte": (206, 200, 182),
    "latte_shade": (140, 134, 120),
    "thatch": (178, 146, 94),
    "wood": (110, 82, 58),
    "sail": (230, 214, 172),
    "bat": (44, 34, 30),
    "far": (204, 220, 222),
    "near": (32, 40, 30),
    "near_light": (150, 112, 74),
}

#: The level of the far shore across the lagoon, and of the reef far out.
MARIANAS_SHORE = 0.604
MARIANAS_REEF = HORIZON + 0.007


def _latte_house(stone: Pen, roof: Pen, dark: Pen, u: float, v: float, w: float, h: float) -> None:
    """A house of the Chamorro on latte, far off and seen from its side: a row
    of latte stones, each a haligi (a pillar that gets narrower to its top)
    under a tasa (a capstone like half a ball, its flat face up), a floor on
    the capstones, and a steep roof of thatch on the floor. `w` is half the
    length and `h` the height to the ridge."""
    pillar = h * 0.36
    for k in range(4):
        x = u - w * 0.78 + k * w * 0.52
        stone.poly([(x - w * 0.085, v + 0.001), (x + w * 0.085, v + 0.001), (x + w * 0.05, v - pillar * 0.78), (x - w * 0.05, v - pillar * 0.78)])
        r = w * 0.13
        stone.poly([(x + r * math.cos(t), v - pillar + pillar * 0.26 * math.sin(t)) for t in np.linspace(0.0, math.pi, 10)])
    dark.rect(u - w * 0.98, v - pillar - h * 0.07, u + w * 0.98, v - pillar)
    roof.poly([(u - w * 1.06, v - pillar - h * 0.05), (u + w * 1.06, v - pillar - h * 0.05), (u + w * 0.30, v - h), (u - w * 0.30, v - h)])


def _marianas_cliff(u: float) -> float:
    """The top of the headland of limestone at the left: a high flat top
    under its jungle, and a steep cliff that falls to the sea."""
    return float(np.interp(u, [-0.05, 0.10, 0.22, 0.29, 0.305, 0.325, 0.345], [0.498, 0.492, 0.500, 0.508, 0.540, 0.586, MARIANAS_SHORE + 0.002]))


def history_marianas(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = MARIANAS
    sun_at = (0.70, 0.13)
    shore = MARIANAS_SHORE
    if layer_key == "sky":
        # A bright day of the trade wind: tall white heap clouds, the deep
        # blue ocean at the horizon, the white line of surf on the reef far
        # out, and the calm lagoon inside it.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.86)), (0.24, p["top"]), (0.50, p["mid"]), (HORIZON - 0.004, p["low"]),
                                 (HORIZON, mix(p["ocean"], p["low"], 0.35)), (MARIANAS_REEF, p["ocean"]), (MARIANAS_REEF + 0.004, mix(p["lagoon"], p["lagoon_light"], 0.45)),
                                 (0.70, p["lagoon"]), (1.0, scale(p["lagoon"], 0.85))]))
        _sun(a, layer, *sun_at, 0.018, p["sun"], p["glow"], 0.45)
        _heaps(a, layer, "marianas heaps", ((0.16, 0.53, 0.07, 0.13), (0.44, 0.55, 0.06, 0.10), (0.66, 0.52, 0.08, 0.15), (0.90, 0.54, 0.05, 0.09)), p["cloud"], p["cloud_shadow"], 0.95)
        surf = a.band(MARIANAS_REEF + 0.001, 0.003, 1.0) * smoothstep(0.30, 0.55, a.noise("marianas surf", cells=40.0, octaves=3, stretch=3.0))
        a.put(layer, surf, p["reef"], 0.95)
        lagoon = (a.v > MARIANAS_REEF + 0.004).astype(np.float32)
        ripples = smoothstep(0.55, 0.80, a.noise("marianas ripples", cells=70.0, octaves=2, stretch=9.0))
        a.light(layer, lagoon * ripples, p["lagoon_light"], 0.30)
        a.light(layer, lagoon * ripples * a.spot(sun_at[0], MARIANAS_REEF + 0.04, 0.24, 1.2, squash=0.8), p["glow"], 0.50)
        a.tint(layer, fog(a, "marianas horizon haze", HORIZON, 0.010, 3.0), p["low"], 0.40)
        _textbook(a, layer, 0.05)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far marianas")
        cols = a.u[0]
        # The headland of limestone at the left: a high flat top under dark
        # jungle, a pale cliff that falls to the sea, with upright streaks
        # and a dark notch that the sea cut at its foot.
        cliff_line = np.array([_marianas_cliff(float(u)) for u in cols], dtype=np.float32)
        cliff_line = cliff_line + (a.line_noise("marianas jungle", cells=60.0, octaves=2) - 0.5) * 0.006 * (cols < 0.31)
        cliff = _land(a, cliff_line) * (a.v < shore + 0.004)
        jungle = cliff * (a.v < cliff_line[None, :] + 0.012 + 0.006 * a.noise("marianas jungle edge", cells=30.0, octaves=2)) * (a.u < 0.318)
        # The coast under the headland: a low strip of land with coconut
        # palms and breadfruit trees, and the latte houses among them.
        flat_top = shore - 0.007 - 0.003 * a.line_noise("marianas coast", cells=10.0, octaves=2)
        flat = _land(a, flat_top.astype(np.float32)) * (a.v < shore + 0.004) * (a.u > 0.18) * (a.u < 0.68)
        bush, bush_pen = a.drawing()
        for _ in range(110):
            u = rng.uniform(0.18, 0.67)
            bush_pen.ellipse(u, shore - 0.008 - rng.uniform(0.0, 0.004), rng.uniform(0.006, 0.013), rng.uniform(0.004, 0.009))
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        breads, bread_pen = a.drawing()
        fruits, fruit_pen = a.drawing()
        for k in range(20):
            u = 0.31 + k * 0.019 + rng.uniform(-0.006, 0.006)
            if 0.40 < u < 0.47 or 0.52 < u < 0.57 or u > 0.67:
                continue
            _coconut_palm(trunk_pen, crown_pen, rng, u, shore - 0.004, rng.uniform(0.045, 0.078), rng.uniform(-0.012, 0.012))
        for u, h in ((0.37, 0.046), (0.49, 0.050), (0.61, 0.042), (0.25, 0.040)):
            _breadfruit(trunk_pen, bread_pen, fruit_pen, rng, u, shore - 0.003, h)
        stones, stone_pen = a.drawing()
        roofs, roof_pen = a.drawing()
        floors, floor_pen = a.drawing()
        for u, w, h in ((0.435, 0.020, 0.040), (0.545, 0.016, 0.032)):
            _latte_house(stone_pen, roof_pen, floor_pen, u, shore - 0.002, w, h)
        beach, beach_pen = a.drawing()
        beach_pen.poly([(0.30, shore - 0.003), (0.66, shore - 0.003), (0.70, shore + 0.003), (0.32, shore + 0.004)])
        # A sakman on the lagoon with its big sail, and two small canoes.
        hulls, hull_pen = a.drawing()
        sails, sail_pen = a.drawing()
        _sakman(hull_pen, sail_pen, 0.79, shore + 0.016, 0.075, -1.0)
        _sakman(hull_pen, sail_pen, 0.66, shore + 0.006, 0.030, 1.0)
        _sakman(hull_pen, sail_pen, 0.93, shore + 0.004, 0.026, -1.0)
        # Fruit bats that fly far off over the trees.
        bats, bat_pen = a.drawing()
        for u, v, s, beat in ((0.47, 0.520, 0.0050, 0.6), (0.50, 0.508, 0.0042, -0.4), (0.53, 0.526, 0.0046, 0.2), (0.40, 0.540, 0.0036, 1.0)):
            _fanihi(bat_pen, u, v, s, beat)
        cliff_mask = cliff * (1.0 - jungle)
        land_mask = np.maximum.reduce([flat, a.mask_of(bush)])
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        bread_mask = a.mask_of(breads)
        fruit_mask = a.mask_of(fruits) * bread_mask
        stone_mask = a.mask_of(stones)
        roof_mask = a.mask_of(roofs)
        floor_mask = a.mask_of(floors)
        beach_mask = a.mask_of(beach)
        boat = np.maximum(a.mask_of(hulls), a.mask_of(sails))
        bat_mask = a.mask_of(bats)
        water_top = (shore - 0.002) + (MARIANAS_REEF + 0.006 - shore + 0.002) * smoothstep(0.68, 0.76, a.u)
        water = smoothstep(water_top, water_top + 0.004, a.v)
        things = np.maximum.reduce([cliff, land_mask, trunk_mask, crown_mask, bread_mask, stone_mask, roof_mask, floor_mask, beach_mask])
        mask = np.maximum.reduce([things, boat, water, bat_mask])
        layer = solid(a, mask, mix(p["jungle"], p["far"], 0.35), mix(p["jungle"], p["far"], 0.15), 0.54, 0.60, "marianas far", 0.04)
        a.put(layer, water, a.ramp([(0.0, mix(p["lagoon_light"], p["lagoon"], 0.35)), (HORIZON + 0.014, mix(p["lagoon_light"], p["lagoon"], 0.35)),
                                     (0.66, mix(p["lagoon"], p["lagoon_light"], 0.20)), (1.0, p["lagoon"])]))
        a.put(layer, _reflected(a, things, shore + 0.002, "marianas ripple", water * (a.v > shore + 0.002)), mix(p["jungle"], p["lagoon"], 0.55), 0.30)
        ripples = smoothstep(0.55, 0.80, a.noise("marianas near ripples", cells=70.0, octaves=2, stretch=9.0))
        a.light(layer, water * ripples * smoothstep(shore + 0.004, shore + 0.05, a.v), p["lagoon_light"], 0.30)
        # The cliff: pale cream, lit on its face to the sun, with upright
        # streaks of grey, small dark holes, red clay low in its cracks and
        # the dark notch of the sea at its foot.
        a.put(layer, cliff_mask, mix(p["cliff"], p["far"], 0.10))
        streaks = a.noise("marianas cliff streaks", cells=90.0, octaves=2, stretch=0.12)
        a.put(layer, cliff_mask * smoothstep(0.55, 0.75, streaks), mix(p["cliff_shade"], p["far"], 0.15), 0.55)
        a.light(layer, cliff_mask * smoothstep(0.42, 0.25, streaks), p["glow"], 0.25)
        a.put(layer, cliff_mask * smoothstep(0.80, 0.86, a.noise("marianas cliff holes", cells=260.0, octaves=1)), mix(p["cliff_shade"], p["near"], 0.30), 0.6)
        a.put(layer, cliff_mask * smoothstep(0.68, 0.78, a.noise("marianas cliff clay", cells=60.0, octaves=2, stretch=0.3)) * smoothstep(0.55, 0.59, a.v), mix(p["clay"], p["far"], 0.25), 0.45)
        a.shade(layer, cliff_mask * a.band(shore - 0.004, 0.006, 1.0) * (a.u > 0.12), 0.35)
        a.shade(layer, cliff_mask * smoothstep(0.24, 0.31, a.u) * (a.v > 0.52), 0.18)
        a.put(layer, jungle, mix(p["jungle"], p["far"], 0.30))
        a.light(layer, jungle * smoothstep(0.55, 0.75, a.noise("marianas jungle lumps", cells=140.0, octaves=2)), mix(p["jungle_light"], p["far"], 0.3), 0.40)
        a.light(layer, a.rim(jungle, 0.0, 0.002, 0.0) * jungle, p["glow"], 0.35)
        a.put(layer, land_mask, mix(p["jungle"], p["far"], 0.28))
        a.light(layer, land_mask * smoothstep(0.55, 0.75, a.noise("marianas bush", cells=80.0, octaves=2)), mix(p["jungle_light"], p["far"], 0.3), 0.35)
        a.put(layer, beach_mask, mix(p["sand"], p["far"], 0.10))
        a.put(layer, trunk_mask, mix(p["trunk"], p["far"], 0.25))
        a.put(layer, crown_mask, mix(p["palm"], p["far"], 0.22))
        a.light(layer, a.rim(crown_mask, -0.0015, 0.0015, 0.0) * crown_mask, mix(p["palm_light"], p["far"], 0.2), 0.50)
        a.put(layer, bread_mask, mix(p["breadfruit"], p["far"], 0.20))
        a.light(layer, a.rim(bread_mask, -0.0015, 0.0020, 0.0) * bread_mask, mix(p["breadfruit_light"], p["far"], 0.2), 0.55)
        a.put(layer, fruit_mask, mix(p["fruit"], p["far"], 0.15), 0.9)
        # The latte houses: pale stones with their shade side, a dark floor
        # and a roof of thatch lit on its top.
        a.put(layer, stone_mask, mix(p["latte"], p["far"], 0.08))
        a.shade(layer, stone_mask * a.rim(stone_mask, -0.0012, 0.0, 0.0), 0.30)
        a.put(layer, floor_mask, mix(p["wood"], p["far"], 0.20))
        a.put(layer, roof_mask, mix(p["thatch"], p["far"], 0.10))
        a.light(layer, a.rim(roof_mask, 0.0, 0.002, 0.0) * roof_mask, p["glow"], 0.45)
        a.shade(layer, roof_mask * a.rim(roof_mask, -0.002, 0.0, 0.0), 0.25)
        a.put(layer, a.mask_of(hulls), mix(p["wood"], p["far"], 0.25))
        a.put(layer, a.mask_of(sails), mix(p["sail"], p["far"], 0.08))
        a.shade(layer, a.mask_of(sails) * a.rim(a.mask_of(sails), 0.002, 0.0, 0.0), 0.25)
        a.put(layer, _reflected(a, boat, shore + 0.017, "marianas canoe ripple", water * (1.0 - boat) * (a.v > shore + 0.016)), mix(p["wood"], p["lagoon"], 0.55), 0.30)
        a.put(layer, bat_mask, mix(p["bat"], p["far"], 0.25))
        haze(a, layer, p["low"], 0.07, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near marianas")
        bank, ground, bank_at = _bank(a, "near marianas", 0.046, 0.044)
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        fruits, fruit_pen = a.drawing()
        palms, palm_pen = a.drawing()
        bats, bat_pen = a.drawing()
        grass, grass_pen = a.drawing()
        stones, stone_pen = a.drawing()
        # A big breadfruit tree at the left, with fanihi that hang asleep
        # under its crown; a coconut palm leans in at the right, over a
        # block of limestone. The middle is a calm bank of red clay under
        # grass.
        hangs = _breadfruit(trunk_pen, crown_pen, fruit_pen, rng, 0.09, bank_at(0.09) + 0.006, 0.46)
        for x, y in hangs[:3]:
            _hanging_bat(bat_pen, x, y + 0.004, rng.uniform(0.020, 0.026))
        _coconut_palm(trunk_pen, palm_pen, rng, 0.90, bank_at(0.90) + 0.006, 0.44, -0.08)
        stone_pen.poly([(0.80, bank_at(0.80) + 0.010), (0.805, bank_at(0.80) - 0.020), (0.83, bank_at(0.83) - 0.034), (0.88, bank_at(0.88) - 0.030), (0.90, bank_at(0.90) - 0.010), (0.91, bank_at(0.91) + 0.010)])
        for _ in range(18):
            u = rng.choice([rng.uniform(0.20, 0.30), rng.uniform(0.70, 0.80)])
            _grass_blades(grass_pen, rng, u, bank_at(u) + 0.002, rng.uniform(0.010, 0.020), 7, 0.0013, 0.014)
        for _ in range(40):
            u = rng.uniform(0.30, 0.70)
            v = bank_at(u) + 0.002
            grass_pen.line([(u, v), (u + rng.uniform(-0.003, 0.003), v - rng.uniform(0.004, 0.008))], 0.0012)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        fruit_mask = a.mask_of(fruits)
        palm_mask = a.mask_of(palms)
        bat_mask = a.mask_of(bats)
        grass_mask = a.mask_of(grass)
        stone_mask = a.mask_of(stones)
        mask = np.maximum.reduce([bank_mask, trunk_mask, crown_mask, fruit_mask, palm_mask, bat_mask, grass_mask, stone_mask])
        layer = a.blank()
        earth = a.ramp([(0.0, mix(p["near_light"], p["near"], 0.30)), (0.66, mix(p["near_light"], p["near"], 0.30)), (0.80, mix(p["near_light"], p["near"], 0.72)), (1.0, p["near"])])
        _near_paint(a, layer, bank_mask, earth, p["glow"], 0.25)
        turf = a.rim(bank_mask, 0.0, 0.007, 0.6) * bank_mask
        a.put(layer, turf, mix(p["jungle_light"], p["near"], 0.40), 0.85)
        a.put(layer, stone_mask, mix(p["cliff"], p["near"], 0.35))
        a.put(layer, stone_mask * smoothstep(0.70, 0.80, a.noise("marianas near pits", cells=200.0, octaves=1)), mix(p["cliff_shade"], p["near"], 0.55), 0.7)
        a.light(layer, a.rim(stone_mask, 0.004, 0.004, 0.3) * stone_mask, p["glow"], 0.30)
        a.shade(layer, a.rim(stone_mask, -0.004, -0.004, 0.3) * stone_mask, 0.30)
        a.put(layer, grass_mask, mix(p["jungle_light"], p["near"], 0.35))
        a.put(layer, trunk_mask, mix(p["trunk"], p["near"], 0.45))
        a.light(layer, a.rim(trunk_mask, 0.003, 0.0, 0.0) * trunk_mask, p["glow"], 0.25)
        a.shade(layer, trunk_mask * (np.abs(((a.v * 260.0) % 1.0) - 0.5) < 0.10) * (a.u > 0.5), 0.25)
        a.put(layer, crown_mask, mix(p["breadfruit"], p["near"], 0.30))
        a.light(layer, a.rim(crown_mask, 0.003, 0.003, 0.0) * crown_mask, p["breadfruit_light"], 0.45)
        a.shade(layer, crown_mask * smoothstep(0.45, 0.25, a.noise("marianas near crown", cells=50.0, octaves=2)), 0.20)
        a.put(layer, fruit_mask, mix(p["fruit"], p["near"], 0.30))
        a.light(layer, a.rim(fruit_mask, 0.002, 0.002, 0.0) * fruit_mask, p["glow"], 0.35)
        a.put(layer, palm_mask, mix(p["palm"], p["near"], 0.30))
        a.light(layer, a.rim(palm_mask, 0.002, 0.002, 0.0) * palm_mask, p["palm_light"], 0.40)
        a.put(layer, bat_mask, mix(p["bat"], p["near"], 0.20))
        a.light(layer, a.rim(bat_mask, 0.002, 0.0, 0.0) * bat_mask, (150, 100, 70), 0.30)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.18)
        haze(a, layer, p["low"], 0.07, None)
        return layer
    layer = _air(a, p, "marianas sea haze", p["low"], 0.20, scale(p["near"], 0.9), 0.12)
    a.put(layer, shafts(a, "marianas shafts", 4, 0.10, 0.0, 0.85, 0.05), p["glow"], 0.07)
    return layer


def marianas_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Big lobed leaves of a breadfruit hang into the top of the view at one
    place from a branch, and the fronds of a coconut palm hang at another."""
    del layer_lights
    rng = art_.rand("marianas foreground")
    u0 = rng.uniform(0.08, 0.22)
    branch = _arch((u0 - 0.08, 0.0), (u0 + 0.06, 0.10), (u0 + 0.20, 0.17), 12)
    for i in range(len(branch) - 1):
        pen.line([branch[i], branch[i + 1]], 0.010 * (1.0 - 0.5 * i / 12.0))
    for i in range(3, 13, 2):
        x, y = branch[i]
        ang = rng.uniform(60.0, 120.0)
        length = rng.uniform(0.12, 0.16)
        length = min(length, (REST_TOP - 0.004 - y) / max(math.sin(math.radians(ang)), 0.3))
        _lobed_leaf(pen, (x, y), ang, length)
    _frond_from_above(pen, rng, rng.uniform(0.64, 0.80), 4, REST_TOP + 0.004)


# ---------------------------------------------------------------------------
# The Marshalls: an atoll, about 1500-1900
# ---------------------------------------------------------------------------


MARSHALLS = {
    "top": (34, 104, 184),
    "mid": (146, 196, 230),
    "low": (236, 242, 240),
    "glow": (255, 244, 214),
    "sun": (255, 252, 240),
    "cloud": (255, 255, 252),
    "cloud_shadow": (164, 180, 204),
    "ocean": (22, 62, 124),
    "swell": (70, 120, 176),
    "lagoon": (88, 196, 190),
    "lagoon_light": (212, 244, 232),
    "reef": (252, 252, 246),
    "sand": (244, 236, 210),
    "island": (60, 104, 62),
    "island_light": (146, 176, 88),
    "palm": (52, 98, 56),
    "palm_light": (158, 182, 92),
    "trunk": (144, 126, 100),
    "thatch": (180, 150, 98),
    "wood": (112, 84, 58),
    "sail": (232, 218, 178),
    "far": (206, 224, 228),
    "near": (36, 48, 40),
    "near_light": (210, 192, 146),
}

#: The level of the shore of the islet, and of the reef at the right.
MARSHALLS_SHORE = 0.630
MARSHALLS_REEF = 0.626


def history_marshalls(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = MARSHALLS
    sun_at = (0.30, 0.12)
    shore = MARSHALLS_SHORE
    if layer_key == "sky":
        # A big sky with tall heap clouds over the ocean. Under the horizon
        # the dark blue open ocean with its long regular swells, in lines of
        # light and shade that get closer to the horizon; the white line of
        # the reef; and the calm pale lagoon inside it.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.84)), (0.26, p["top"]), (0.52, p["mid"]), (HORIZON - 0.004, p["low"]),
                                 (HORIZON, mix(p["ocean"], p["low"], 0.40)), (HORIZON + 0.006, p["ocean"]), (MARSHALLS_REEF, mix(p["ocean"], p["swell"], 0.3)),
                                 (MARSHALLS_REEF + 0.004, mix(p["lagoon"], p["lagoon_light"], 0.45)), (0.72, p["lagoon"]), (1.0, scale(p["lagoon"], 0.86))]))
        _sun(a, layer, *sun_at, 0.018, p["sun"], p["glow"], 0.40)
        _heaps(a, layer, "marshalls heaps", ((0.12, 0.555, 0.06, 0.10), (0.38, 0.56, 0.05, 0.08), (0.62, 0.55, 0.09, 0.20), (0.86, 0.56, 0.07, 0.14)), p["cloud"], p["cloud_shadow"], 0.95)
        ocean = (a.v > HORIZON) * (a.v < MARSHALLS_REEF)
        t = np.clip((a.v - HORIZON) / (MARSHALLS_REEF - HORIZON), 0.0, 1.0)
        phase = (t ** 0.55) * 9.0 * 2.0 * math.pi + a.u * 2.2 + (a.noise("marshalls swell bend", cells=3.0, octaves=2) - 0.5) * 1.2
        wave = np.sin(phase)
        a.light(layer, ocean * smoothstep(0.55, 0.95, wave), p["swell"], 0.70)
        a.light(layer, ocean * smoothstep(0.85, 1.0, wave) * smoothstep(0.3, 0.7, a.noise("marshalls swell caps", cells=30.0, octaves=2, stretch=6.0)), p["low"], 0.25)
        a.shade(layer, ocean * smoothstep(-0.55, -0.95, wave), 0.30)
        surf = a.band(MARSHALLS_REEF + 0.001, 0.0035, 1.0) * smoothstep(0.25, 0.50, a.noise("marshalls surf", cells=40.0, octaves=3, stretch=3.0))
        a.put(layer, surf, p["reef"], 0.95)
        lagoon = (a.v > MARSHALLS_REEF + 0.004).astype(np.float32)
        ripples = smoothstep(0.58, 0.82, a.noise("marshalls ripples", cells=70.0, octaves=2, stretch=9.0))
        a.light(layer, lagoon * ripples, p["lagoon_light"], 0.30)
        a.tint(layer, fog(a, "marshalls horizon haze", HORIZON, 0.008, 3.0), p["low"], 0.35)
        _textbook(a, layer, 0.05)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far marshalls")
        cols = a.u[0]
        # The islet: a long low strip of land with no hill at all, coconut
        # palms and pandanus on it, low houses near its beach and a canoe
        # pulled up on the sand. It ends at the right, where the reef runs
        # on with its surf.
        land_top = shore - 0.007 - 0.004 * a.line_noise("marshalls land", cells=8.0, octaves=2)
        land_top = np.where(cols < 0.60, land_top, 1.0) + 0.012 * smoothstep(0.54, 0.60, cols)
        land = _land(a, land_top.astype(np.float32)) * (a.v < shore + 0.004)
        bush, bush_pen = a.drawing()
        for _ in range(130):
            u = rng.uniform(-0.02, 0.60)
            bush_pen.ellipse(u, shore - 0.009 - rng.uniform(0.0, 0.004), rng.uniform(0.006, 0.014), rng.uniform(0.004, 0.009))
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        for k in range(30):
            u = -0.02 + k * 0.021 + rng.uniform(-0.007, 0.007)
            if u > 0.59:
                continue
            _coconut_palm(trunk_pen, crown_pen, rng, u, shore - 0.005, rng.uniform(0.045, 0.082), rng.uniform(-0.014, 0.014))
        for u in (0.08, 0.27, 0.44, 0.53):
            _pandanus(trunk_pen, crown_pen, rng, u, shore - 0.003, 0.028, rng.uniform(-0.01, 0.01))
        roofs, roof_pen = a.drawing()
        dark, dark_pen = a.drawing()
        posts, post_pen = a.drawing()
        for u, w, h in ((0.19, 0.012, 0.016), (0.225, 0.010, 0.014), (0.38, 0.013, 0.017)):
            _house(roof_pen, dark_pen, post_pen, u, shore - 0.002, w, h)
        beach, beach_pen = a.drawing()
        beach_pen.poly([(-0.02, shore - 0.004), (0.57, shore - 0.003), (0.62, shore + 0.003), (-0.02, shore + 0.004)])
        hulls, hull_pen = a.drawing()
        sails, sail_pen = a.drawing()
        _canoe_ashore(hull_pen, hull_pen, 0.31, shore + 0.002, 0.040, 1.0)
        _sakman(hull_pen, sail_pen, 0.75, shore + 0.022, 0.080, 1.0)
        _sakman(hull_pen, sail_pen, 0.91, shore + 0.008, 0.034, -1.0)
        land_mask = np.maximum(land, a.mask_of(bush))
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        roof_mask = a.mask_of(roofs)
        post_mask = a.mask_of(posts)
        dark_mask = a.mask_of(dark) * (1.0 - roof_mask)
        beach_mask = a.mask_of(beach)
        hull_mask = a.mask_of(hulls)
        sail_mask = a.mask_of(sails)
        boat = np.maximum(hull_mask, sail_mask)
        water_top = (shore - 0.002) + (MARSHALLS_REEF + 0.006 - shore + 0.002) * smoothstep(0.58, 0.66, a.u)
        water = smoothstep(water_top, water_top + 0.004, a.v)
        things = np.maximum.reduce([land_mask, trunk_mask, crown_mask, roof_mask, post_mask, dark_mask, beach_mask])
        mask = np.maximum.reduce([things, boat, water])
        layer = solid(a, mask, mix(p["island"], p["far"], 0.35), mix(p["island"], p["far"], 0.15), 0.56, 0.62, "marshalls far", 0.04)
        a.put(layer, water, a.ramp([(0.0, mix(p["lagoon_light"], p["lagoon"], 0.35)), (shore + 0.006, mix(p["lagoon_light"], p["lagoon"], 0.35)),
                                     (0.68, mix(p["lagoon"], p["lagoon_light"], 0.20)), (1.0, p["lagoon"])]))
        a.put(layer, _reflected(a, things, shore + 0.002, "marshalls ripple", water * (a.v > shore + 0.002)), mix(p["island"], p["lagoon"], 0.55), 0.28)
        ripples = smoothstep(0.55, 0.80, a.noise("marshalls near ripples", cells=70.0, octaves=2, stretch=9.0))
        a.light(layer, water * ripples * smoothstep(shore + 0.004, shore + 0.05, a.v), p["lagoon_light"], 0.30)
        a.put(layer, land_mask, mix(p["island"], p["far"], 0.30))
        a.light(layer, land_mask * smoothstep(0.55, 0.75, a.noise("marshalls bush", cells=80.0, octaves=2)), mix(p["island_light"], p["far"], 0.3), 0.35)
        a.put(layer, beach_mask, mix(p["sand"], p["far"], 0.08))
        a.put(layer, trunk_mask, mix(p["trunk"], p["far"], 0.25))
        a.put(layer, crown_mask, mix(p["palm"], p["far"], 0.22))
        a.light(layer, a.rim(crown_mask, 0.0015, 0.0015, 0.0) * crown_mask, mix(p["palm_light"], p["far"], 0.2), 0.50)
        a.put(layer, dark_mask, mix(p["near"], p["far"], 0.35))
        a.put(layer, post_mask, mix(p["wood"], p["far"], 0.25))
        a.put(layer, roof_mask, mix(p["thatch"], p["far"], 0.12))
        a.light(layer, a.rim(roof_mask, 0.0015, 0.002, 0.0) * roof_mask, p["glow"], 0.45)
        a.shade(layer, roof_mask * a.rim(roof_mask, -0.002, 0.0, 0.0), 0.25)
        a.put(layer, hull_mask, mix(p["wood"], p["far"], 0.25))
        a.put(layer, sail_mask, mix(p["sail"], p["far"], 0.08))
        a.shade(layer, sail_mask * a.rim(sail_mask, -0.002, 0.0, 0.0), 0.25)
        a.put(layer, _reflected(a, boat, shore + 0.023, "marshalls canoe ripple", water * (1.0 - boat) * (a.v > shore + 0.022)), mix(p["wood"], p["lagoon"], 0.55), 0.28)
        haze(a, layer, p["low"], 0.06, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near marshalls")
        bank, ground, bank_at = _bank(a, "near marshalls", 0.036, 0.042)
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        leaves, leaf_pen = a.drawing()
        shrubs, shrub_pen = a.drawing()
        hulls, hull_pen = a.drawing()
        grass, grass_pen = a.drawing()
        # A coconut palm leans out over the beach at the left; a pandanus
        # stands at the right, and a canoe lies on the sand under it. Low
        # round shrubs of naupaka at the two sides. The middle is a calm
        # bank of pale coral sand.
        _coconut_palm(trunk_pen, crown_pen, rng, 0.06, bank_at(0.06) + 0.006, 0.50, 0.12)
        _coconut_palm(trunk_pen, crown_pen, rng, 0.15, bank_at(0.15) + 0.006, 0.30, 0.04)
        _pandanus(trunk_pen, leaf_pen, rng, 0.91, bank_at(0.91) + 0.006, 0.34, -0.03)
        _canoe_ashore(hull_pen, hull_pen, 0.80, bank_at(0.80) + 0.004, 0.13, -1.0)
        for u, w in ((0.22, 0.030), (0.27, 0.022), (0.72, 0.026)):
            for _ in range(10):
                shrub_pen.ellipse(u + rng.uniform(-w, w), bank_at(u) - rng.uniform(0.002, 0.016), rng.uniform(0.008, 0.013), rng.uniform(0.006, 0.010))
        for _ in range(5):
            u0 = rng.uniform(0.30, 0.68)
            pts = [(u0 + k * 0.012, bank_at(u0 + k * 0.012) + 0.002 + 0.0015 * math.sin(k)) for k in range(7)]
            grass_pen.line(pts, 0.0010)
            for x, y in pts[1::2]:
                grass_pen.ellipse(x, y - 0.002, 0.003, 0.002)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        leaf_mask = a.mask_of(leaves)
        shrub_mask = a.mask_of(shrubs)
        hull_mask = a.mask_of(hulls)
        grass_mask = a.mask_of(grass)
        mask = np.maximum.reduce([bank_mask, trunk_mask, crown_mask, leaf_mask, shrub_mask, hull_mask, grass_mask])
        layer = a.blank()
        sand = a.ramp([(0.0, mix(p["near_light"], p["near"], 0.22)), (0.66, mix(p["near_light"], p["near"], 0.22)), (0.80, mix(p["near_light"], p["near"], 0.70)), (1.0, p["near"])])
        _near_paint(a, layer, bank_mask, sand, p["glow"], 0.40)
        a.put(layer, grass_mask, mix(p["island_light"], p["near"], 0.40))
        a.put(layer, shrub_mask, mix(p["island_light"], p["near"], 0.45))
        a.light(layer, a.rim(shrub_mask, 0.002, 0.003, 0.0) * shrub_mask, p["palm_light"], 0.40)
        a.put(layer, hull_mask, mix(p["wood"], p["near"], 0.35))
        a.light(layer, a.rim(hull_mask, 0.0, 0.003, 0.0) * hull_mask, p["glow"], 0.30)
        a.put(layer, trunk_mask, mix(p["trunk"], p["near"], 0.40))
        a.shade(layer, trunk_mask * (np.abs(((a.v * 260.0) % 1.0) - 0.5) < 0.10), 0.25)
        a.light(layer, a.rim(trunk_mask, 0.003, 0.0, 0.0) * trunk_mask, p["glow"], 0.30)
        a.put(layer, crown_mask, mix(p["palm"], p["near"], 0.30))
        a.light(layer, a.rim(crown_mask, 0.002, 0.002, 0.0) * crown_mask, p["palm_light"], 0.40)
        a.put(layer, leaf_mask, mix(p["palm"], p["near"], 0.25))
        a.light(layer, a.rim(leaf_mask, 0.002, 0.002, 0.0) * leaf_mask, p["palm_light"], 0.35)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.18)
        haze(a, layer, p["low"], 0.07, None)
        return layer
    layer = _air(a, p, "marshalls sea haze", p["low"], 0.18, scale(p["near"], 0.9), 0.10)
    a.put(layer, shafts(a, "marshalls shafts", 4, -0.08, 0.0, 0.85, 0.05), p["glow"], 0.06)
    return layer


def marshalls_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """The long leaves of a pandanus hang into the top of the view at one
    place, like straps that bend down from a tuft; the fronds of a coconut
    palm hang at another place."""
    del layer_lights
    rng = art_.rand("marshalls foreground")
    u0 = rng.uniform(0.10, 0.24)
    stem = (u0, 0.06)
    pen.line([(u0 - 0.05, 0.0), stem], 0.012)
    for k in range(13):
        ang = 10.0 + k * 12.5 + rng.uniform(-4.0, 4.0)
        length = rng.uniform(0.18, 0.26)
        tip = polar(*stem, length, ang)
        tip = (tip[0], min(REST_TOP - 0.004, tip[1] + length * 0.25))
        _leaf(pen, _arch(stem, polar(*stem, length * 0.55, ang - 25.0), tip, 12), 0.0050, 0.35)
    _frond_from_above(pen, rng, rng.uniform(0.62, 0.78), 4, REST_TOP + 0.004)


# ---------------------------------------------------------------------------
# Nan Madol: off Pohnpei, about 1180-1628, at dusk
# ---------------------------------------------------------------------------


NAN_MADOL = {
    "top": (58, 66, 108),
    "mid": (164, 128, 134),
    "low": (244, 192, 140),
    "glow": (255, 190, 118),
    "sun": (255, 230, 176),
    "cloud": (226, 160, 140),
    "cloud_shadow": (98, 84, 108),
    "mountain": (56, 78, 66),
    "mountain_far": (118, 116, 126),
    "water": (40, 66, 62),
    "water_light": (206, 150, 116),
    "basalt": (42, 40, 44),
    "basalt_light": (128, 108, 100),
    "basalt_end": (70, 66, 70),
    "coral": (150, 138, 120),
    "mangrove": (38, 60, 44),
    "mangrove_light": (100, 112, 70),
    "fern": (64, 92, 58),
    "mist": (226, 196, 176),
    "far": (150, 140, 152),
    "near": (24, 24, 28),
    "near_light": (92, 84, 80),
}

#: The level of the water at the foot of the islets.
NAN_MADOL_WATER = 0.616


def _crib_wall(stones: tuple[Pen, Pen], body: Pen, u0: float, u1: float, v: float, h: float, lift: float, course: float) -> None:
    """A wall of Nan Madol from `u0` to `u1`, its foot at `v`, `h` high: black
    basalt columns laid crosswise like a log cabin. In one course the
    columns lie along the wall; in the next they lie across it, so their
    ends of five or six sides show. The corners rise higher by `lift` and
    lean out, like the prow of a ship. `body` takes the outline of the wall
    (the dark of the joints); `stones` take the long columns and the ends."""
    longs, ends = stones
    span = u1 - u0

    def top(x: float) -> float:
        d = min(x - u0, u1 - x) / max(span * 0.28, 1e-6)
        return v - h - lift * max(0.0, 1.0 - d) ** 2

    xs = np.linspace(u0, u1, 24)
    outline = [(u0 + h * 0.03, v + 0.001), (u1 - h * 0.03, v + 0.001), (u1 + h * 0.10, top(u1))] + [(float(x), top(float(x))) for x in xs[::-1]] + [(u0 - h * 0.10, top(u0))]
    body.poly(outline)
    k = 0
    y = v
    while y > v - h - lift:
        y0 = y - course
        if k % 2 == 0:
            x = u0 - h * 0.12 + (course * 1.4 if k % 4 else 0.0)
            while x < u1 + h * 0.12:
                length = course * (4.0 + (k * 7 + int(x * 997)) % 5)
                longs.rect(x + course * 0.08, y0 + course * 0.10, x + length - course * 0.08, y - course * 0.08)
                x += length
        else:
            r = course * 0.50
            x = u0 - h * 0.12 + r
            while x < u1 + h * 0.12:
                ends.poly([polar(x, y - course * 0.5, r * 0.96, 30.0 + 60.0 * j) for j in range(6)])
                x += r * 1.95
        y = y0
        k += 1


def history_nan_madol(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = NAN_MADOL
    sun_at = (0.80, HORIZON - 0.040)
    water_v = NAN_MADOL_WATER
    if layer_key == "sky":
        # Dusk: deep blue-violet over warm rose and the gold of the low sun,
        # long thin clouds lit pink from below. The steep green mountains of
        # Pohnpei far off, with cloud on their tops, and the still water,
        # with the light of the sun in a long path on it.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.85)), (0.22, p["top"]), (0.46, p["mid"]), (HORIZON - 0.004, p["low"]),
                                 (HORIZON + 0.002, mix(p["water_light"], p["low"], 0.40)), (0.66, mix(p["water"], p["water_light"], 0.35)), (1.0, p["water"])]))
        for k, (centre, half, cover, alpha) in enumerate(((0.30, 0.05, 0.40, 0.55), (0.44, 0.04, 0.42, 0.60), (0.52, 0.025, 0.38, 0.55))):
            clouds = cloud_mask(a, ("nan madol cloud", k), centre, half, cells=3.0 + k, cover=cover, soft=0.25, stretch=7.0)
            a.put(layer, clouds, mix(p["cloud"], p["cloud_shadow"], 0.55 - k * 0.2), alpha)
            a.light(layer, clouds * a.band(centre + half * 0.6, half * 0.6) * a.spot(*sun_at, 0.7, 1.0, squash=1.8), p["glow"], 0.55)
        a.light(layer, a.spot(*sun_at, 0.34, 2.0, squash=1.6), p["glow"], 0.55)
        _sun(a, layer, *sun_at, 0.020, p["sun"], p["glow"], 0.45)
        far_hills, far_line = a.ridge("nan madol far mountains", HORIZON - 0.030, 0.026, cells=3.0, octaves=4, sharp=0.6)
        a.put(layer, far_hills * (a.v < HORIZON + 0.002), mix(p["mountain_far"], p["low"], 0.35))
        hills, hill_line = a.ridge("nan madol mountains", HORIZON - 0.012, 0.036, cells=2.4, octaves=5, sharp=0.7)
        hills = hills * (a.u < 0.70)
        a.put(layer, hills * (a.v < HORIZON + 0.002), mix(p["mountain"], p["mountain_far"], 0.45))
        a.light(layer, hills * (a.v < HORIZON + 0.002) * smoothstep(0.55, 0.75, a.noise("nan madol forest lumps", cells=90.0, octaves=2)), p["glow"], 0.12)
        a.tint(layer, hills * smoothstep(HORIZON - 0.020, HORIZON, a.v) * (a.v < HORIZON + 0.002), p["mist"], 0.40)
        for k, line in enumerate((far_line, hill_line)):
            tops = np.clip(1.0 - np.abs(a.v - (line[None, :] - 0.004)) / 0.012, 0.0, 1.0) * smoothstep(0.50, 0.75, a.noise(("nan madol cap", k), cells=6.0, octaves=3, stretch=2.0))
            tops = tops * smoothstep(HORIZON - 0.010, HORIZON - 0.050, line[None, :] + 0.0 * a.v)
            a.put(layer, tops, mix(p["cloud"], p["low"], 0.55), 0.70)
        water = (a.v > HORIZON + 0.002).astype(np.float32)
        lines = smoothstep(0.62, 0.84, a.noise("nan madol far water", cells=60.0, octaves=2, stretch=16.0))
        a.light(layer, water * lines, p["water_light"], 0.20)
        path = np.clip(1.0 - np.abs(a.u - sun_at[0]) / (0.02 + (a.v - HORIZON) * 0.25), 0.0, 1.0)
        a.light(layer, water * path * lines, p["glow"], 0.60)
        a.tint(layer, fog(a, "nan madol horizon mist", HORIZON, 0.014, 3.0), p["mist"], 0.50)
        _textbook(a, layer, 0.08)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far nan madol")
        # The islets of basalt on the reef: a great walled islet at the
        # left of the middle (as Nandauwas), smaller ones at its sides, and
        # canals of dark water between them. Mangroves at the edge of the
        # water, and a few trees that grow behind the walls.
        bodies, body_pen = a.drawing()
        longs, long_pen = a.drawing()
        ends, end_pen = a.drawing()
        for u0, u1, h, lift in ((0.24, 0.47, 0.044, 0.012), (0.53, 0.62, 0.022, 0.006), (0.70, 0.77, 0.016, 0.004), (0.08, 0.17, 0.018, 0.005), (0.62, 0.66, 0.010, 0.003)):
            v = water_v + (0.004 if h < 0.02 else 0.0)
            _crib_wall((long_pen, end_pen), body_pen, u0, u1, v, h, lift, 0.0050 if h > 0.03 else 0.0036)
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        for u, h in ((0.30, 0.050), (0.36, 0.060), (0.42, 0.046), (0.57, 0.040), (0.12, 0.036)):
            crown_pen.ellipse(u, water_v - h, h * 0.30, h * 0.22)
            crown_pen.ellipse(u + h * 0.18, water_v - h * 0.92, h * 0.22, h * 0.18)
        mangroves, mangrove_pen = a.drawing()
        for u, h in ((0.00, 0.060), (0.04, 0.050), (0.19, 0.040), (0.50, 0.046), (0.67, 0.036), (0.80, 0.050), (0.86, 0.042), (0.94, 0.056)):
            _mangrove(trunk_pen, mangrove_pen, rng, u, water_v + 0.004, h)
        body_mask = a.mask_of(bodies)
        long_mask = a.mask_of(longs) * body_mask
        end_mask = a.mask_of(ends) * body_mask
        crown_mask = a.mask_of(crowns) * (1.0 - body_mask)
        trunk_mask = a.mask_of(trunks)
        mangrove_mask = a.mask_of(mangroves)
        water = smoothstep(water_v - 0.002, water_v + 0.002, a.v)
        things = np.maximum.reduce([body_mask, crown_mask, trunk_mask, mangrove_mask])
        mask = np.maximum(things, water)
        layer = solid(a, mask, mix(p["mangrove"], p["far"], 0.35), mix(p["mangrove"], p["far"], 0.15), 0.56, 0.62, "nan madol far", 0.04)
        a.put(layer, water, a.ramp([(0.0, mix(p["water_light"], p["water"], 0.40)), (water_v, mix(p["water_light"], p["water"], 0.40)),
                                     (0.68, mix(p["water"], p["water_light"], 0.18)), (1.0, p["water"])]))
        lines = smoothstep(0.60, 0.84, a.noise("nan madol water lines", cells=60.0, octaves=2, stretch=16.0))
        a.light(layer, water * lines * a.spot(sun_at[0], water_v + 0.03, 0.30, 1.2, squash=0.6), p["glow"], 0.45)
        a.put(layer, _reflected(a, things, water_v + 0.002, "nan madol ripple", water * (a.v > water_v + 0.001)), mix(p["basalt"], p["water"], 0.40), 0.45)
        # The long shadows of the walls lie on the water away from the low
        # sun at the right.
        a.shade(layer, a.blur(a.shift(body_mask, -0.030, 0.006), 3.0) * water * (1.0 - body_mask), 0.30)
        a.put(layer, crown_mask, mix(p["mangrove"], p["far"], 0.30))
        a.light(layer, a.rim(crown_mask, -0.002, 0.0, 0.0) * crown_mask, p["glow"], 0.30)
        # The walls: black basalt, the joints darker, the long columns and
        # the ends a little lit, more on the side to the sun.
        a.put(layer, body_mask, mix(p["basalt"], p["far"], 0.12))
        a.put(layer, long_mask, mix(p["basalt_end"], p["far"], 0.15))
        a.put(layer, end_mask, mix(p["basalt_end"], p["far"], 0.10))
        a.light(layer, a.rim(long_mask, 0.0, 0.0012, 0.0) * long_mask, p["basalt_light"], 0.55)
        a.light(layer, a.rim(end_mask, -0.0010, 0.0010, 0.0) * end_mask, p["basalt_light"], 0.55)
        a.light(layer, body_mask * smoothstep(0.0, 1.0, (a.u - 0.2) / 0.7), p["glow"], 0.12)
        a.light(layer, a.rim(body_mask, -0.002, 0.0, 0.0) * body_mask, p["glow"], 0.35)
        a.put(layer, trunk_mask, mix(p["basalt"], p["far"], 0.30))
        a.put(layer, mangrove_mask, mix(p["mangrove"], p["far"], 0.22))
        a.light(layer, a.rim(mangrove_mask, -0.002, 0.001, 0.0) * mangrove_mask, mix(p["mangrove_light"], p["glow"], 0.4), 0.35)
        mist = fog(a, "nan madol water mist", water_v + 0.002, 0.012, 3.0)
        a.tint(layer, mist * mask, p["mist"], 0.45)
        haze(a, layer, p["low"], 0.08, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near nan madol")
        bank, ground, bank_at = _bank(a, "near nan madol", 0.050, 0.046)
        # At the left the corner of a wall of basalt, lifted like a prow,
        # with its columns laid crosswise; at the right mangroves in the
        # shallow water, their roots arched. The middle is a calm low bank
        # of coral rubble and moss.
        bodies, body_pen = a.drawing()
        longs, long_pen = a.drawing()
        ends, end_pen = a.drawing()
        foot = bank_at(0.10) + 0.010
        _crib_wall((long_pen, end_pen), body_pen, -0.30, 0.20, foot, 0.17, 0.05, 0.018)
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        ferns, fern_pen = a.drawing()
        _mangrove(trunk_pen, crown_pen, rng, 0.88, bank_at(0.88) + 0.010, 0.40)
        _mangrove(trunk_pen, crown_pen, rng, 0.98, bank_at(0.98) + 0.010, 0.48)
        for u in (0.24, 0.27, 0.76):
            base = (u, bank_at(u) + 0.002)
            for k in range(6):
                ang = -160.0 + k * 28.0 + rng.uniform(-6.0, 6.0)
                length = rng.uniform(0.030, 0.045)
                tip = polar(*base, length, ang)
                tip = (tip[0], tip[1] + length * 0.35)
                _leaf(fern_pen, _arch(base, polar(*base, length * 0.6, ang - 8.0), tip, 8), 0.004, 0.5)
        rubble, rubble_pen = a.drawing()
        for _ in range(26):
            u = rng.uniform(0.20, 0.84)
            rubble_pen.ellipse(u, bank_at(u) + rng.uniform(0.004, 0.016), rng.uniform(0.003, 0.007), rng.uniform(0.002, 0.004))
        bank_mask = np.maximum(a.mask_of(bank), ground)
        body_mask = a.mask_of(bodies)
        long_mask = a.mask_of(longs) * body_mask
        end_mask = a.mask_of(ends) * body_mask
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        fern_mask = a.mask_of(ferns)
        rubble_mask = a.mask_of(rubble) * bank_mask
        mask = np.maximum.reduce([bank_mask, body_mask, trunk_mask, crown_mask, fern_mask])
        layer = a.blank()
        earth = a.ramp([(0.0, mix(p["near_light"], p["near"], 0.35)), (0.66, mix(p["near_light"], p["near"], 0.35)), (0.80, mix(p["near_light"], p["near"], 0.75)), (1.0, p["near"])])
        _near_paint(a, layer, bank_mask, earth, p["glow"], 0.25)
        a.put(layer, rubble_mask, mix(p["coral"], p["near"], 0.45), 0.8)
        a.put(layer, a.rim(bank_mask, 0.0, 0.006, 0.6) * bank_mask * smoothstep(0.4, 0.6, a.noise("nan madol near moss", cells=40.0, octaves=2)), mix(p["fern"], p["near"], 0.35), 0.8)
        a.put(layer, body_mask, mix(p["basalt"], p["near"], 0.40))
        a.put(layer, long_mask, mix(p["basalt_end"], p["near"], 0.30))
        a.put(layer, end_mask, mix(p["basalt_end"], p["near"], 0.25))
        a.light(layer, a.rim(long_mask, 0.0, 0.003, 0.2) * long_mask, p["basalt_light"], 0.45)
        a.light(layer, a.rim(end_mask, -0.002, 0.002, 0.2) * end_mask, p["basalt_light"], 0.45)
        a.shade(layer, a.rim(end_mask, 0.002, -0.002, 0.2) * end_mask, 0.30)
        a.put(layer, body_mask * a.rim(body_mask, 0.0, 0.012, 0.5) * smoothstep(0.45, 0.6, a.noise("nan madol wall moss", cells=30.0, octaves=2)), mix(p["fern"], p["near"], 0.35), 0.7)
        a.light(layer, a.rim(body_mask, -0.004, 0.0, 0.2) * body_mask, p["glow"], 0.35)
        a.put(layer, fern_mask, mix(p["fern"], p["near"], 0.30))
        a.put(layer, trunk_mask, mix(p["basalt_light"], p["near"], 0.55))
        a.put(layer, crown_mask, mix(p["mangrove"], p["near"], 0.30))
        a.light(layer, a.rim(crown_mask, -0.003, 0.002, 0.0) * crown_mask, mix(p["mangrove_light"], p["glow"], 0.4), 0.40)
        a.shade(layer, a.rim(mask, 0.004, -0.003, 1.0) * mask, 0.18)
        haze(a, layer, p["low"], 0.10, None)
        return layer
    layer = _air(a, p, "nan madol dusk mist", p["mist"], 0.34, scale(p["near"], 0.8), 0.20)
    return layer


def nan_madol_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """A branch of a mangrove hangs into the top of the view at one place,
    with its thick oval leaves in pairs; the fronds of a tree fern stand
    from below at another place."""
    del layer_lights
    rng = art_.rand("nan madol foreground")
    u0 = rng.uniform(0.60, 0.76)
    branch = _arch((u0 + 0.30, 0.0), (u0 + 0.12, 0.12), (u0 - 0.06, 0.20), 14)
    for i in range(len(branch) - 1):
        pen.line([branch[i], branch[i + 1]], 0.008 * (1.0 - 0.5 * i / 14.0))
    for i in range(2, 15, 2):
        x, y = branch[i]
        for side in (-1.0, 1.0):
            ang = 90.0 + side * rng.uniform(30.0, 60.0)
            length = rng.uniform(0.040, 0.055)
            tip = polar(x, y, length, ang)
            tip = (tip[0], min(REST_TOP - 0.004, tip[1]))
            _leaf(pen, [(x, y), ((x + tip[0]) * 0.5, (y + tip[1]) * 0.5), tip], 0.010, 0.8)
    u = rng.uniform(0.16, 0.28)
    top = REST_BOTTOM + 0.006
    for k in range(5):
        ang = -90.0 + (k - 2) * 26.0 + rng.uniform(-5.0, 5.0)
        length = rng.uniform(0.16, 0.20)
        tip = polar(u, 1.0, length, ang)
        tip = (tip[0] + (k - 2) * 0.02, max(top + abs(k - 2) * 0.012, tip[1] - 0.20))
        rib = _arch((u, 1.0), (u + (k - 2) * 0.01, tip[1] + 0.06), tip, 14)
        pen.line(rib, 0.0024)
        for i in range(1, len(rib) - 1):
            x, y = rib[i]
            size = 0.020 * (1.0 - i / len(rib) * 0.7)
            for side in (-1.0, 1.0):
                pen.line([(x, y), (x + side * size, y + size * 0.25)], 0.0020)


# ---------------------------------------------------------------------------
# Yap: a village path, about 1500-1900
# ---------------------------------------------------------------------------


YAP = {
    "top": (66, 128, 170),
    "mid": (176, 208, 210),
    "low": (240, 236, 214),
    "glow": (255, 236, 186),
    "sun": (255, 248, 226),
    "cloud": (250, 250, 240),
    "cloud_shadow": (176, 190, 190),
    "water": (70, 150, 150),
    "water_light": (200, 232, 214),
    "mangrove": (40, 78, 50),
    "forest": (54, 96, 56),
    "forest_light": (130, 166, 80),
    "palm": (50, 96, 54),
    "palm_light": (150, 178, 88),
    "trunk": (150, 146, 132),
    "betel": (64, 116, 60),
    "rai": (212, 208, 194),
    "rai_shade": (150, 146, 136),
    "paving": (128, 124, 112),
    "paving_light": (176, 172, 156),
    "platform": (96, 92, 86),
    "thatch": (172, 140, 90),
    "wood": (104, 78, 54),
    "croton": (196, 90, 48),
    "croton_gold": (220, 186, 70),
    "far": (198, 214, 204),
    "near": (30, 38, 30),
    "near_light": (128, 120, 100),
}

#: The level of the shore and of the path far off.
YAP_SHORE = 0.612


def _betel_palm(trunk: Pen, crown: Pen, rng, u: float, v: float, h: float, lean: float = 0.0) -> None:
    """An areca palm, the betel palm: a slim, straight grey trunk, a smooth
    green crown shaft on its top, and a small neat crown of a few fronds
    that arch out and hang."""
    w = h * 0.018
    pts = [(u + lean * t * t, v + 0.004 - (h * 0.80 + 0.004) * t) for t in np.linspace(0.0, 1.0, 9)]
    trunk.line(pts, w)
    top = pts[-1]
    crown.ellipse(top[0], top[1] - h * 0.045, w * 1.25, h * 0.060)
    head = (top[0], top[1] - h * 0.10)
    for k in range(8):
        ang = -90.0 + (k - 3.5) * 26.0 + rng.uniform(-5.0, 5.0)
        length = h * rng.uniform(0.17, 0.22)
        tip = polar(*head, length, ang)
        tip = (tip[0], tip[1] + length * 0.70 * abs(math.cos(math.radians(ang))))
        _leaf(crown, _arch(head, polar(*head, length * 0.65, ang), tip, 8), h * 0.014, 0.5)


def _rai(pen: Pen, hole: Pen, u: float, v: float, r: float, lean: float = 0.0) -> None:
    """A rai, a disc of stone money, that stands on edge on the ground at
    `(u, v)`: a thick round disc a little narrower than it is high (it is
    seen a little from the side), with a round hole in its middle. `lean`
    tilts its top to one side."""
    cx, cy = u + lean * r, v - r * 0.98
    pen.poly([(cx + r * 0.92 * math.cos(t), cy + r * math.sin(t)) for t in np.linspace(0.0, math.tau, 32)])
    hole.ellipse(cx + lean * r * 0.05, cy, r * 0.17, r * 0.19)


def _faluw(roof: Pen, base: Pen, dark: Pen, u: float, v: float, w: float, h: float) -> None:
    """A faluw, a men's house of Yap, far off and seen from its long side: a
    wide platform of stones; on it a big house with a tall, steep roof of
    thatch. Its ridge sags a little to the middle, and its two gables rise
    to high points that lean out over the ends; the eaves come low over the
    walls."""
    base.rect(u - w * 1.20, v - h * 0.12, u + w * 1.20, v + 0.001)
    eave = v - h * 0.30
    dark.rect(u - w * 0.86, eave, u + w * 0.86, v - h * 0.11)
    roof.poly([(u - w * 1.00, eave), (u + w * 1.00, eave), (u + w * 0.86, v - h * 0.90), (u + w * 1.02, v - h * 1.12), (u + w * 0.60, v - h * 0.92),
               (u, v - h * 0.84), (u - w * 0.60, v - h * 0.92), (u - w * 1.02, v - h * 1.12), (u - w * 0.86, v - h * 0.90)])


def history_yap(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = YAP
    sun_at = (0.24, 0.20)
    shore = YAP_SHORE
    if layer_key == "sky":
        # A warm, soft day: high light clouds, and under the horizon the
        # lagoon, calm and green-blue.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.88)), (0.28, p["top"]), (0.50, p["mid"]), (HORIZON - 0.004, p["low"]),
                                 (HORIZON + 0.002, mix(p["water_light"], p["low"], 0.40)), (0.68, mix(p["water"], p["water_light"], 0.40)), (1.0, p["water"])]))
        for k, (centre, half, cover, alpha) in enumerate(((0.20, 0.08, 0.50, 0.55), (0.38, 0.07, 0.48, 0.50), (0.52, 0.04, 0.44, 0.45))):
            clouds = cloud_mask(a, ("yap cloud", k), centre, half, cells=3.0 + k, cover=cover, soft=0.30, stretch=3.5)
            a.put(layer, clouds, mix(p["cloud"], p["low"], k * 0.2), alpha)
            a.put(layer, clouds * a.band(centre + half * 0.5, half * 0.6), p["cloud_shadow"], 0.20)
        _sun(a, layer, *sun_at, 0.016, p["sun"], p["glow"], 0.40)
        lines = smoothstep(0.64, 0.84, a.noise("yap far water", cells=60.0, octaves=2, stretch=16.0))
        a.light(layer, (a.v > HORIZON + 0.004) * lines, p["water_light"], 0.22)
        a.tint(layer, fog(a, "yap horizon haze", HORIZON, 0.012, 3.0), p["low"], 0.45)
        _textbook(a, layer, 0.07)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far yap")
        cols = a.u[0]
        # A low green island: forest and palms over the village. At the
        # left of the middle the faluw on its platform; the paved path runs
        # along the front with rai on edge beside it. At the right the
        # mangroves of the shore and the lagoon.
        land_top = shore - 0.030 - 0.012 * a.line_noise("yap hills", cells=4.0, octaves=3)
        land_top = land_top + (shore + 0.004 - land_top) * smoothstep(0.62, 0.74, cols)
        land = _land(a, land_top.astype(np.float32)) * (a.v < shore + 0.006)
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        betels, betel_pen = a.drawing()
        for k in range(16):
            u = 0.02 + k * 0.040 + rng.uniform(-0.01, 0.01)
            if 0.30 < u < 0.42 or u > 0.66:
                continue
            if k % 2:
                _coconut_palm(trunk_pen, crown_pen, rng, u, shore - 0.002, rng.uniform(0.055, 0.075), rng.uniform(-0.010, 0.010))
            else:
                _betel_palm(trunk_pen, betel_pen, rng, u, shore - 0.002, rng.uniform(0.050, 0.065))
        roofs, roof_pen = a.drawing()
        bases, base_pen = a.drawing()
        dark, dark_pen = a.drawing()
        _faluw(roof_pen, base_pen, dark_pen, 0.36, shore - 0.003, 0.034, 0.052)
        _faluw(roof_pen, base_pen, dark_pen, 0.58, shore - 0.002, 0.014, 0.022)
        path, path_pen = a.drawing()
        path_pen.poly([(-0.02, shore - 0.002), (0.66, shore - 0.002), (0.66, shore + 0.006), (-0.02, shore + 0.006)])
        rais, rai_pen = a.drawing()
        holes, hole_pen = a.drawing()
        for u, r, lean in ((0.12, 0.010, 0.10), (0.135, 0.007, 0.15), (0.20, 0.012, -0.05), (0.46, 0.011, 0.08), (0.475, 0.008, 0.12), (0.49, 0.006, 0.15), (0.26, 0.006, 0.0)):
            _rai(rai_pen, hole_pen, u, shore + 0.002, r, lean)
        mangroves, mangrove_pen = a.drawing()
        for u, h in ((0.64, 0.036), (0.68, 0.044), (0.72, 0.030), (0.75, 0.034), (0.79, 0.026)):
            _mangrove(trunk_pen, mangrove_pen, rng, u, shore + 0.004, h)
        land_mask = land
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        betel_mask = a.mask_of(betels)
        roof_mask = a.mask_of(roofs)
        base_mask = a.mask_of(bases)
        dark_mask = a.mask_of(dark) * (1.0 - roof_mask)
        path_mask = a.mask_of(path)
        rai_mask = a.mask_of(rais) * (1.0 - a.mask_of(holes))
        mangrove_mask = a.mask_of(mangroves)
        water = smoothstep(shore + 0.002, shore + 0.006, a.v) * (1.0 - path_mask)
        things = np.maximum.reduce([land_mask, trunk_mask, crown_mask, betel_mask, roof_mask, base_mask, dark_mask, path_mask, rai_mask, mangrove_mask])
        mask = np.maximum(things, water)
        layer = solid(a, mask, mix(p["forest"], p["far"], 0.35), mix(p["forest"], p["far"], 0.15), 0.56, 0.62, "yap far", 0.05)
        a.put(layer, water, a.ramp([(0.0, mix(p["water_light"], p["water"], 0.35)), (shore + 0.004, mix(p["water_light"], p["water"], 0.35)), (0.68, mix(p["water"], p["water_light"], 0.20)), (1.0, p["water"])]))
        a.put(layer, _reflected(a, np.maximum(land_mask, mangrove_mask), shore + 0.004, "yap ripple", water), mix(p["forest"], p["water"], 0.55), 0.30)
        a.put(layer, land_mask, mix(p["forest"], p["far"], 0.32))
        lumps = a.noise("yap forest lumps", cells=110.0, octaves=2)
        a.light(layer, land_mask * smoothstep(0.55, 0.75, lumps), mix(p["forest_light"], p["far"], 0.3), 0.35)
        a.light(layer, a.rim(land_mask, 0.002, 0.002, 0.0) * land_mask, p["glow"], 0.25)
        a.put(layer, path_mask, mix(p["paving_light"], p["far"], 0.20))
        a.put(layer, path_mask * smoothstep(0.55, 0.70, a.noise("yap far stones", cells=300.0, octaves=1)), mix(p["paving"], p["far"], 0.20), 0.6)
        a.put(layer, base_mask, mix(p["platform"], p["far"], 0.20))
        a.light(layer, base_mask * smoothstep(0.55, 0.75, a.noise("yap far platform", cells=400.0, octaves=1)), p["paving_light"], 0.30)
        a.put(layer, dark_mask, mix(p["near"], p["far"], 0.35))
        a.put(layer, roof_mask, mix(p["thatch"], p["far"], 0.12))
        a.light(layer, a.rim(roof_mask, 0.002, 0.002, 0.0) * roof_mask, p["glow"], 0.45)
        a.shade(layer, roof_mask * a.rim(roof_mask, -0.002, 0.0, 0.0), 0.25)
        a.put(layer, trunk_mask, mix(p["trunk"], p["far"], 0.20))
        a.put(layer, crown_mask, mix(p["palm"], p["far"], 0.22))
        a.light(layer, a.rim(crown_mask, 0.0015, 0.0015, 0.0) * crown_mask, mix(p["palm_light"], p["far"], 0.2), 0.45)
        a.put(layer, betel_mask, mix(p["betel"], p["far"], 0.20))
        a.light(layer, a.rim(betel_mask, 0.0015, 0.0015, 0.0) * betel_mask, mix(p["palm_light"], p["far"], 0.2), 0.45)
        a.put(layer, rai_mask, mix(p["rai"], p["far"], 0.08))
        a.shade(layer, rai_mask * a.rim(rai_mask, -0.0012, -0.0008, 0.0), 0.30)
        a.put(layer, mangrove_mask, mix(p["mangrove"], p["far"], 0.22))
        a.light(layer, a.rim(mangrove_mask, 0.002, 0.001, 0.0) * mangrove_mask, p["forest_light"], 0.30)
        haze(a, layer, p["low"], 0.07, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near yap")
        bank, ground, bank_at = _bank(a, "near yap", 0.030, 0.040)
        # The path: a broad bank of flat stones fitted together. At the left
        # a big rai stands on edge and leans on a smaller one, with a third
        # by it; at the right betel palms and a croton bush. The middle is
        # the calm grey paving.
        rai_masks = []
        for u, r, lean in ((0.035, 0.110, 0.10), (0.135, 0.068, 0.20), (0.205, 0.040, -0.05)):
            disc, disc_pen = a.drawing()
            hole, hole_pen = a.drawing()
            _rai(disc_pen, hole_pen, u, bank_at(u) + 0.010, r, lean)
            rai_masks.append(a.mask_of(disc) * (1.0 - a.mask_of(hole)))
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        crotons, croton_pen = a.drawing()
        golds, gold_pen = a.drawing()
        _betel_palm(trunk_pen, crown_pen, rng, 0.86, bank_at(0.86) + 0.006, 0.56, -0.01)
        _betel_palm(trunk_pen, crown_pen, rng, 0.95, bank_at(0.95) + 0.006, 0.66, 0.02)
        for _ in range(26):
            cx = 0.78 + rng.uniform(-0.035, 0.035)
            base = (cx, bank_at(cx) + 0.002)
            ang = rng.uniform(-150.0, -30.0)
            length = rng.uniform(0.020, 0.032)
            _leaf(croton_pen if rng.random() < 0.55 else gold_pen, [base, polar(*base, length * 0.5, ang), polar(*base, length, ang)], 0.0045, 0.6)
        stones, stone_pen = a.drawing()
        x = 0.0
        while x < 1.0:
            w = rng.uniform(0.030, 0.060)
            y = bank_at(x + w * 0.5)
            stone_pen.poly([(x + 0.002, y + 0.0015), (x + w - 0.002, y + 0.0015 + rng.uniform(-0.001, 0.001)), (x + w - 0.004, y + 0.010), (x + 0.004, y + 0.010)])
            x += w
        grass, grass_pen = a.drawing()
        for _ in range(16):
            u = rng.choice([rng.uniform(0.18, 0.30), rng.uniform(0.66, 0.80)])
            _grass_blades(grass_pen, rng, u, bank_at(u) + 0.002, rng.uniform(0.008, 0.016), 6, 0.0012, 0.012)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        rai_mask = np.maximum.reduce(rai_masks)
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        croton_mask = a.mask_of(crotons)
        gold_mask = a.mask_of(golds)
        stone_mask = a.mask_of(stones) * bank_mask
        grass_mask = a.mask_of(grass)
        mask = np.maximum.reduce([bank_mask, rai_mask, trunk_mask, crown_mask, croton_mask, gold_mask, grass_mask])
        layer = a.blank()
        earth = a.ramp([(0.0, mix(p["near_light"], p["near"], 0.30)), (0.66, mix(p["near_light"], p["near"], 0.30)), (0.80, mix(p["near_light"], p["near"], 0.75)), (1.0, p["near"])])
        _near_paint(a, layer, bank_mask, earth, p["glow"], 0.20)
        a.put(layer, stone_mask, mix(p["paving"], p["near"], 0.30))
        a.light(layer, a.rim(stone_mask, 0.0, 0.002, 0.0) * stone_mask, p["paving_light"], 0.45)
        a.shade(layer, a.rim(stone_mask, 0.002, 0.0, 0.0) * stone_mask, 0.35)
        a.put(layer, grass_mask, mix(p["forest_light"], p["near"], 0.35))
        # The rai: pale grey-white limestone, rough, lit on the side to the
        # sun at the left and dark on the other, the hole dark round its
        # lower rim.
        pits = smoothstep(0.62, 0.78, a.noise("yap rai pits", cells=120.0, octaves=2))
        for disc in rai_masks:
            a.put(layer, disc, mix(p["rai"], p["near"], 0.18))
            a.put(layer, disc * pits, mix(p["rai_shade"], p["near"], 0.25), 0.6)
            a.light(layer, a.rim(disc, 0.006, 0.004, 0.4) * disc, p["glow"], 0.35)
            a.shade(layer, a.rim(disc, -0.008, -0.004, 0.6) * disc, 0.35)
            a.shade(layer, a.rim(disc, -0.002, 0.0, 0.0) * disc, 0.45)
        a.put(layer, trunk_mask, mix(p["trunk"], p["near"], 0.40))
        a.shade(layer, trunk_mask * (np.abs(((a.v * 300.0) % 1.0) - 0.5) < 0.08), 0.20)
        a.light(layer, a.rim(trunk_mask, 0.003, 0.0, 0.0) * trunk_mask, p["glow"], 0.25)
        a.put(layer, crown_mask, mix(p["betel"], p["near"], 0.30))
        a.light(layer, a.rim(crown_mask, 0.002, 0.002, 0.0) * crown_mask, p["palm_light"], 0.40)
        a.put(layer, croton_mask, mix(p["croton"], p["near"], 0.30))
        a.put(layer, gold_mask, mix(p["croton_gold"], p["near"], 0.30))
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.18)
        haze(a, layer, p["low"], 0.08, None)
        return layer
    layer = _air(a, p, "yap warm haze", p["low"], 0.22, scale(p["near"], 0.85), 0.14)
    a.put(layer, shafts(a, "yap shafts", 4, 0.12, 0.0, 0.85, 0.05), p["glow"], 0.08)
    return layer


def yap_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """The fronds of a betel palm hang into the top of the view at one place;
    the broad leaves of a croton stand from below at another place."""
    del layer_lights
    rng = art_.rand("yap foreground")
    _frond_from_above(pen, rng, rng.uniform(0.14, 0.28), 3, REST_TOP + 0.004)
    u = rng.uniform(0.66, 0.78)
    for k in range(11):
        base = (u + rng.uniform(-0.02, 0.02), 1.0)
        ang = -90.0 + (k - 5) * 13.0 + rng.uniform(-5.0, 5.0)
        length = rng.uniform(0.18, 0.30)
        tip = polar(*base, length, ang)
        tip = (tip[0], max(REST_BOTTOM + 0.006 + abs(k - 5) * 0.008, tip[1]))
        _leaf(pen, _arch(base, polar(*base, length * 0.5, ang + rng.uniform(-6.0, 6.0)), tip, 10), 0.012, 0.55)


# ---------------------------------------------------------------------------
# Nauru: the phosphate works, about 1920-1968
# ---------------------------------------------------------------------------


NAURU = {
    "top": (82, 132, 184),
    "mid": (176, 202, 220),
    "low": (238, 238, 230),
    "glow": (255, 244, 220),
    "sun": (255, 252, 240),
    "cloud": (250, 250, 248),
    "cloud_shadow": (180, 188, 198),
    "ocean": (40, 92, 140),
    "ocean_light": (170, 206, 214),
    "reef": (246, 246, 240),
    "pinnacle": (212, 208, 196),
    "pinnacle_shade": (148, 144, 136),
    "phosphate": (128, 98, 70),
    "pit": (96, 80, 64),
    "belt": (70, 112, 64),
    "belt_light": (150, 176, 94),
    "palm": (60, 102, 60),
    "palm_light": (156, 178, 96),
    "trunk": (140, 126, 106),
    "shed": (196, 192, 180),
    "tin": (150, 152, 152),
    "steel": (70, 70, 74),
    "hull": (44, 44, 48),
    "deck": (216, 212, 200),
    "bird": (36, 34, 38),
    "scrub": (128, 136, 92),
    "far": (206, 212, 212),
    "near": (40, 38, 36),
    "near_light": (196, 190, 176),
}

#: The level of the land of the coast and of the sea at the foot of it.
NAURU_SHORE = 0.612


def _pinnacles(pen: Pen, rng, u0: float, u1: float, v: float, h: float, step: float) -> None:
    """A field of limestone pinnacles from `u0` to `u1`, their feet at `v`:
    sharp spires close together, each with jagged sides, some high and some
    low, as they stand where the phosphate was dug out from between them."""
    x = u0
    while x < u1:
        w = step * rng.uniform(0.6, 1.1)
        top = h * rng.uniform(0.35, 1.0)
        apex = (x + w * rng.uniform(-0.3, 0.3), v - top)
        left = [(x - w + (apex[0] - x + w) * t + rng.uniform(-0.12, 0.12) * w, v - top * t) for t in (0.0, 0.3, 0.55, 0.8)]
        right = [(x + w + (apex[0] - x - w) * t + rng.uniform(-0.12, 0.12) * w, v - top * t) for t in (0.8, 0.55, 0.3, 0.0)]
        pen.poly(left + [apex] + right)
        x += step * rng.uniform(0.7, 1.2)


def _cantilever(steel: Pen, u: float, v: float, h: float, reach: float, facing: float = 1.0) -> None:
    """A cantilever loader of the phosphate works: a tall tower of steel
    lattice on the edge of the reef, a long arm of lattice that reaches from
    its top out over the water, a chute that hangs from the end of the arm,
    and the long sloped belt of the conveyor that comes up to it from the
    land. `(u, v)` is the foot of the tower, `h` its height."""
    f = facing
    w = h * 0.008
    legs = ((u - h * 0.12, v), (u - h * 0.05, v - h)), ((u + h * 0.12, v), (u + h * 0.05, v - h))
    for a_, b_ in legs:
        steel.line([a_, b_], w * 1.6)
    for k in range(7):
        t0, t1 = k / 7.0, (k + 1) / 7.0
        la = (legs[0][0][0] + (legs[0][1][0] - legs[0][0][0]) * t0, v - h * t0)
        rb = (legs[1][0][0] + (legs[1][1][0] - legs[1][0][0]) * t1, v - h * t1)
        steel.line([la, rb], w)
        steel.line([(la[0], la[1]), (legs[1][0][0] + (legs[1][1][0] - legs[1][0][0]) * t0, v - h * t0)], w * 0.8)
    top_a = (u - f * h * 0.20, v - h * 1.02)
    top_b = (u + f * reach, v - h * 0.94)
    low_a = (u, v - h * 0.84)
    low_b = (u + f * reach, v - h * 0.88)
    steel.line([top_a, top_b], w * 1.4)
    steel.line([low_a, low_b], w * 1.4)
    n = 10
    for k in range(n):
        t0, t1 = k / n, (k + 1) / n
        p0 = (top_a[0] + (top_b[0] - top_a[0]) * t0, top_a[1] + (top_b[1] - top_a[1]) * t0)
        p1 = (low_a[0] + (low_b[0] - low_a[0]) * t1, low_a[1] + (low_b[1] - low_a[1]) * t1)
        steel.line([p0, p1], w)
    steel.line([(u + f * reach, v - h * 0.88), (u + f * reach * 0.98, v - h * 0.22)], w * 2.0)
    belt_low = (u - f * h * 1.6, v - h * 0.04)
    steel.line([belt_low, (u - f * h * 0.10, v - h * 0.96)], w * 2.0)
    for k in range(1, 5):
        t = k / 5.0
        x = belt_low[0] + (u - f * h * 0.10 - belt_low[0]) * t
        y = belt_low[1] + (v - h * 0.96 - belt_low[1]) * t
        steel.line([(x, y), (x, v + 0.001)], w * 1.2)


def _steamer(hull: Pen, deck: Pen, u: float, v: float, s: float, facing: float = 1.0) -> None:
    """A cargo steamer at anchor, side on: a long dark hull with a raised
    bow and stern, a pale block of bridge and cabins in its middle, one tall
    funnel, and two masts. `(u, v)` is the middle of the waterline and `s`
    the length."""
    f = facing
    hull.poly([(u - f * s * 0.50, v - s * 0.10), (u - f * s * 0.30, v - s * 0.08), (u + f * s * 0.36, v - s * 0.08), (u + f * s * 0.52, v - s * 0.13),
               (u + f * s * 0.46, v + s * 0.01), (u - f * s * 0.46, v + s * 0.01)])
    deck.rect(u - s * 0.08, v - s * 0.17, u + s * 0.10, v - s * 0.08)
    deck.rect(u - s * 0.04, v - s * 0.22, u + s * 0.07, v - s * 0.17)
    hull.rect(u - f * s * 0.03 - s * 0.022, v - s * 0.34, u - f * s * 0.03 + s * 0.022, v - s * 0.20)
    for du in (-0.30, 0.30):
        hull.line([(u + f * du * s, v - s * 0.08), (u + f * du * s, v - s * 0.42)], s * 0.008)
        hull.line([(u + f * du * s, v - s * 0.30), (u + f * (du + (0.12 if du < 0 else -0.12)) * s, v - s * 0.10)], s * 0.005)


def _shed(wall: Pen, roof: Pen, dark: Pen, u: float, v: float, w: float, h: float) -> None:
    """A plain shed of the works far off: a low wall of boards, a low
    pitched roof of corrugated iron, and a dark door."""
    wall.rect(u - w, v - h * 0.60, u + w, v + 0.001)
    roof.poly([(u - w * 1.08, v - h * 0.58), (u + w * 1.08, v - h * 0.58), (u + w * 0.70, v - h), (u - w * 0.70, v - h)])
    dark.rect(u - w * 0.18, v - h * 0.42, u + w * 0.02, v + 0.001)


def history_nauru(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = NAURU
    sun_at = (0.62, 0.16)
    shore = NAURU_SHORE
    if layer_key == "sky":
        # Clear light, a little pale and hazy with dust; a few flat clouds.
        # Under the horizon the open sea, the reef close in with its line
        # of surf.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.90)), (0.26, p["top"]), (0.50, p["mid"]), (HORIZON - 0.004, p["low"]),
                                 (HORIZON + 0.002, mix(p["ocean"], p["low"], 0.40)), (0.64, p["ocean"]), (1.0, scale(p["ocean"], 0.85))]))
        for k, (centre, half, cover, alpha) in enumerate(((0.26, 0.06, 0.42, 0.45), (0.46, 0.05, 0.44, 0.40))):
            clouds = cloud_mask(a, ("nauru cloud", k), centre, half, cells=3.0 + k, cover=cover, soft=0.30, stretch=5.0)
            a.put(layer, clouds, p["cloud"], alpha)
            a.put(layer, clouds * a.band(centre + half * 0.5, half * 0.6), p["cloud_shadow"], 0.20)
        _sun(a, layer, *sun_at, 0.016, p["sun"], p["glow"], 0.40)
        lines = smoothstep(0.64, 0.84, a.noise("nauru far water", cells=60.0, octaves=2, stretch=16.0))
        a.light(layer, (a.v > HORIZON + 0.004) * lines, p["ocean_light"], 0.25)
        a.tint(layer, fog(a, "nauru horizon haze", HORIZON, 0.016, 3.0), p["low"], 0.50)
        _textbook(a, layer, 0.07)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far nauru")
        cols = a.u[0]
        # The topside at the left: the plateau, its phosphate dug out, so
        # only a field of pale limestone pinnacles stands, with the bare
        # brown floor of the pits between them. It steps down at the right
        # to the narrow green belt of the coast, with palms and sheds. On
        # the edge of the reef the cantilever reaches out to the steamer.
        plateau_top = shore - 0.034 + 0.034 * smoothstep(0.50, 0.58, cols) + (a.line_noise("nauru plateau", cells=10.0, octaves=2) - 0.5) * 0.004
        plateau = _land(a, plateau_top.astype(np.float32)) * (a.v < shore + 0.004)
        spires, spire_pen = a.drawing()
        rng_s = a.rand("far nauru spires")
        _pinnacles(spire_pen, rng_s, -0.02, 0.54, shore - 0.030, 0.026, 0.008)
        _pinnacles(spire_pen, rng_s, -0.02, 0.52, shore - 0.026, 0.020, 0.011)
        belt = _land(a, (shore - 0.008 - 0.003 * a.line_noise("nauru belt", cells=10.0, octaves=2)).astype(np.float32)) * (a.v < shore + 0.004) * (a.u > 0.46) * (a.u < 0.80)
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        for k in range(14):
            u = 0.50 + k * 0.021 + rng.uniform(-0.006, 0.006)
            if 0.60 < u < 0.66 or u > 0.79:
                continue
            _coconut_palm(trunk_pen, crown_pen, rng, u, shore - 0.004, rng.uniform(0.040, 0.066), rng.uniform(-0.012, 0.012))
        walls, wall_pen = a.drawing()
        roofs, roof_pen = a.drawing()
        doors, door_pen = a.drawing()
        for u, w, h in ((0.61, 0.014, 0.014), (0.645, 0.010, 0.012), (0.70, 0.012, 0.012)):
            _shed(wall_pen, roof_pen, door_pen, u, shore - 0.003, w, h)
        steel, steel_pen = a.drawing()
        _cantilever(steel_pen, 0.80, shore + 0.002, 0.080, 0.090, 1.0)
        hulls, hull_pen = a.drawing()
        decks, deck_pen = a.drawing()
        _steamer(hull_pen, deck_pen, 0.91, shore + 0.014, 0.110, -1.0)
        birds, bird_pen = a.drawing()
        for u, v, s, beat in ((0.34, 0.36, 0.014, 0.0), (0.42, 0.33, 0.011, 0.5), (0.58, 0.39, 0.012, -0.3), (0.72, 0.31, 0.010, 0.2)):
            _frigatebird(bird_pen, u, v, s, beat)
        reef = smoothstep(shore - 0.002, shore + 0.002, a.v) * (a.v < shore + 0.008) * (a.u > 0.44)
        plateau_mask = plateau * (a.u < 0.60)
        spire_mask = a.mask_of(spires)
        belt_mask = belt
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        wall_mask = a.mask_of(walls)
        roof_mask = a.mask_of(roofs)
        door_mask = a.mask_of(doors) * wall_mask
        steel_mask = a.mask_of(steel)
        hull_mask = a.mask_of(hulls)
        deck_mask = a.mask_of(decks)
        bird_mask = a.mask_of(birds)
        things = np.maximum.reduce([plateau_mask, spire_mask, belt_mask, trunk_mask, crown_mask, wall_mask, roof_mask, steel_mask, hull_mask, deck_mask, reef])
        mask = np.maximum(things, bird_mask)
        layer = solid(a, mask, mix(p["pinnacle"], p["far"], 0.30), mix(p["pit"], p["far"], 0.15), 0.56, 0.62, "nauru far", 0.04)
        # The pits: bare brown floor, darker low down; the spires pale grey
        # white, lit on their left, with dark grooves.
        a.put(layer, plateau_mask, a.ramp([(0.0, mix(p["phosphate"], p["far"], 0.30)), (shore - 0.034, mix(p["phosphate"], p["far"], 0.30)), (shore, mix(p["pit"], p["far"], 0.15)), (1.0, p["pit"])]))
        a.put(layer, spire_mask, mix(p["pinnacle"], p["far"], 0.10))
        a.shade(layer, spire_mask * a.rim(spire_mask, -0.0015, 0.0, 0.2), 0.30)
        a.light(layer, spire_mask * a.rim(spire_mask, 0.0012, 0.0, 0.0), p["glow"], 0.45)
        grooves = smoothstep(0.60, 0.80, a.noise("nauru spire grooves", cells=200.0, octaves=1, stretch=0.15))
        a.shade(layer, spire_mask * grooves, 0.18)
        a.shade(layer, spire_mask * smoothstep(shore - 0.040, shore - 0.020, a.v), 0.20)
        a.put(layer, reef, mix(p["reef"], p["far"], 0.10), 0.85)
        a.put(layer, belt_mask, mix(p["belt"], p["far"], 0.28))
        a.light(layer, belt_mask * smoothstep(0.55, 0.75, a.noise("nauru belt bush", cells=80.0, octaves=2)), mix(p["belt_light"], p["far"], 0.3), 0.35)
        a.put(layer, trunk_mask, mix(p["trunk"], p["far"], 0.25))
        a.put(layer, crown_mask, mix(p["palm"], p["far"], 0.22))
        a.light(layer, a.rim(crown_mask, 0.0015, 0.0015, 0.0) * crown_mask, mix(p["palm_light"], p["far"], 0.2), 0.45)
        a.put(layer, wall_mask, mix(p["shed"], p["far"], 0.12))
        a.put(layer, roof_mask, mix(p["tin"], p["far"], 0.12))
        a.light(layer, a.rim(roof_mask, 0.0, 0.0015, 0.0) * roof_mask, p["glow"], 0.45)
        a.put(layer, door_mask, mix(p["near"], p["far"], 0.30))
        a.put(layer, steel_mask, mix(p["steel"], p["far"], 0.22))
        a.put(layer, hull_mask, mix(p["hull"], p["far"], 0.20))
        a.put(layer, deck_mask, mix(p["deck"], p["far"], 0.10))
        a.put(layer, bird_mask, mix(p["bird"], p["far"], 0.25))
        haze(a, layer, p["low"], 0.08, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near nauru")
        bank, ground, bank_at = _bank(a, "near nauru", 0.050, 0.036)
        # At the left a few big pinnacles of the topside, pale and sharp,
        # with the brown phosphate earth low between them; at the right a
        # coconut palm of the coast and dry scrub. The middle is a calm bank
        # of pale crushed stone.
        spires, spire_pen = a.drawing()
        rng_s = a.rand("near nauru spires")
        _pinnacles(spire_pen, rng_s, -0.04, 0.17, bank_at(0.06) + 0.012, 0.20, 0.040)
        _pinnacles(spire_pen, rng_s, 0.14, 0.24, bank_at(0.20) + 0.008, 0.07, 0.024)
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        scrub, scrub_pen = a.drawing()
        _coconut_palm(trunk_pen, crown_pen, rng, 0.92, bank_at(0.92) + 0.006, 0.42, -0.06)
        for u in (0.74, 0.79, 0.84):
            for _ in range(10):
                scrub_pen.ellipse(u + rng.uniform(-0.02, 0.02), bank_at(u) - rng.uniform(0.002, 0.014), rng.uniform(0.006, 0.010), rng.uniform(0.004, 0.008))
            _grass_blades(scrub_pen, rng, u, bank_at(u) + 0.002, 0.024, 8, 0.0012, 0.02)
        pebbles, pebble_pen = a.drawing()
        for _ in range(30):
            u = rng.uniform(0.24, 0.74)
            pebble_pen.ellipse(u, bank_at(u) + rng.uniform(0.003, 0.016), rng.uniform(0.002, 0.004), rng.uniform(0.0015, 0.0025))
        bank_mask = np.maximum(a.mask_of(bank), ground)
        spire_mask = a.mask_of(spires)
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        scrub_mask = a.mask_of(scrub)
        pebble_mask = a.mask_of(pebbles) * bank_mask
        mask = np.maximum.reduce([bank_mask, spire_mask, trunk_mask, crown_mask, scrub_mask])
        layer = a.blank()
        earth = a.ramp([(0.0, mix(p["near_light"], p["near"], 0.30)), (0.66, mix(p["near_light"], p["near"], 0.30)), (0.80, mix(p["near_light"], p["near"], 0.72)), (1.0, p["near"])])
        _near_paint(a, layer, bank_mask, earth, p["glow"], 0.30)
        a.put(layer, bank_mask * (a.u < 0.26) * smoothstep(0.4, 0.6, a.noise("nauru near phosphate", cells=20.0, octaves=2)), mix(p["phosphate"], p["near"], 0.35), 0.8)
        a.put(layer, pebble_mask, mix(p["pinnacle"], p["near"], 0.25), 0.7)
        a.put(layer, spire_mask, mix(p["pinnacle"], p["near"], 0.22))
        grooves = smoothstep(0.58, 0.80, a.noise("nauru near grooves", cells=120.0, octaves=2, stretch=0.12))
        a.shade(layer, spire_mask * grooves, 0.25)
        a.put(layer, spire_mask * smoothstep(0.80, 0.86, a.noise("nauru near holes", cells=160.0, octaves=1)), mix(p["pinnacle_shade"], p["near"], 0.40), 0.6)
        a.light(layer, a.rim(spire_mask, 0.005, 0.0, 0.3) * spire_mask, p["glow"], 0.35)
        a.shade(layer, a.rim(spire_mask, -0.006, 0.0, 0.4) * spire_mask, 0.30)
        a.put(layer, spire_mask * smoothstep(bank_at(0.1) - 0.04, bank_at(0.1) + 0.01, a.v), mix(p["phosphate"], p["near"], 0.40), 0.55)
        a.put(layer, scrub_mask, mix(p["scrub"], p["near"], 0.40))
        a.put(layer, trunk_mask, mix(p["trunk"], p["near"], 0.40))
        a.shade(layer, trunk_mask * (np.abs(((a.v * 260.0) % 1.0) - 0.5) < 0.10), 0.25)
        a.light(layer, a.rim(trunk_mask, 0.003, 0.0, 0.0) * trunk_mask, p["glow"], 0.30)
        a.put(layer, crown_mask, mix(p["palm"], p["near"], 0.30))
        a.light(layer, a.rim(crown_mask, 0.002, 0.002, 0.0) * crown_mask, p["palm_light"], 0.40)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.18)
        haze(a, layer, p["low"], 0.09, None)
        return layer
    layer = _air(a, p, "nauru dust haze", p["low"], 0.24, scale(p["near"], 0.85), 0.12)
    return layer


def nauru_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Dry scrub stands from below at one place, thin twigs with small
    leaves; the fronds of a coconut palm hang into the top of the view at
    another place."""
    del layer_lights
    rng = art_.rand("nauru foreground")
    u = rng.uniform(0.16, 0.30)
    top = REST_BOTTOM + 0.004
    for k in range(9):
        base = (u + rng.uniform(-0.01, 0.01), 1.0)
        ang = -90.0 + (k - 4) * 14.0 + rng.uniform(-6.0, 6.0)
        length = rng.uniform(0.20, 0.32)
        tip = polar(*base, length, ang)
        tip = (tip[0], max(top + abs(k - 4) * 0.010, tip[1]))
        twig = _arch(base, polar(*base, length * 0.5, ang + rng.uniform(-10.0, 10.0)), tip, 8)
        pen.line(twig, 0.0022)
        for x, y in twig[3::2]:
            pen.ellipse(x + rng.uniform(-0.006, 0.006), y, 0.0050, 0.0030)
    _frond_from_above(pen, rng, rng.uniform(0.66, 0.80), 3, REST_TOP + 0.004)


# ---------------------------------------------------------------------------
# Bikini: the atoll in 1946, sober
# ---------------------------------------------------------------------------


BIKINI = {
    "top": (112, 128, 142),
    "mid": (170, 178, 184),
    "low": (214, 214, 206),
    "glow": (226, 222, 206),
    "sun": (236, 234, 224),
    "cloud": (206, 208, 206),
    "cloud_shadow": (150, 156, 162),
    "lagoon": (118, 146, 146),
    "lagoon_light": (186, 198, 192),
    "reef": (222, 224, 220),
    "sand": (204, 200, 186),
    "island": (92, 108, 92),
    "island_light": (140, 150, 124),
    "palm": (90, 106, 90),
    "palm_light": (148, 158, 132),
    "trunk": (140, 134, 122),
    "thatch": (158, 146, 120),
    "plank": (150, 144, 132),
    "wood": (104, 96, 86),
    "ship": (118, 122, 128),
    "ship_dark": (88, 92, 98),
    "far": (194, 198, 196),
    "near": (40, 44, 42),
    "near_light": (176, 172, 158),
}

#: The level of the shore of the islet.
BIKINI_SHORE = 0.610


def _warship(pen: Pen, u: float, v: float, s: float, kind: str) -> None:
    """A grey warship far off at anchor, side on and whole. `kind` is
    "battleship" (a long low hull, turrets at the bow and the stern, a tall
    tower of bridges and a funnel in the middle), "carrier" (a flat deck the
    length of the hull, with a small island at one side), "cruiser" (a lower
    hull, two funnels) or "transport" (a high hull, a block of bridge and
    cabins, one funnel and two masts). `(u, v)` is the middle of the
    waterline and `s` the length."""
    if kind == "carrier":
        pen.poly([(u - s * 0.46, v - s * 0.07), (u + s * 0.46, v - s * 0.07), (u + s * 0.42, v + s * 0.01), (u - s * 0.42, v + s * 0.01)])
        pen.rect(u - s * 0.52, v - s * 0.10, u + s * 0.52, v - s * 0.08)
        pen.rect(u + s * 0.10, v - s * 0.19, u + s * 0.22, v - s * 0.10)
        pen.line([(u + s * 0.16, v - s * 0.19), (u + s * 0.16, v - s * 0.27)], s * 0.008)
        return
    high = {"battleship": 0.06, "cruiser": 0.05, "transport": 0.09}[kind]
    pen.poly([(u - s * 0.50, v - s * high), (u + s * 0.40, v - s * high), (u + s * 0.52, v - s * (high + 0.02)), (u + s * 0.44, v + s * 0.01), (u - s * 0.44, v + s * 0.01)])
    if kind == "battleship":
        pen.rect(u - s * 0.10, v - s * 0.13, u + s * 0.12, v - s * high)
        pen.rect(u + s * 0.02, v - s * 0.24, u + s * 0.08, v - s * 0.13)
        pen.rect(u - s * 0.06, v - s * 0.19, u - s * 0.01, v - s * 0.13)
        for x in (0.22, 0.31, -0.24, -0.33):
            pen.rect(u + s * x - s * 0.035, v - s * 0.10, u + s * x + s * 0.035, v - s * high)
        pen.line([(u + s * 0.05, v - s * 0.24), (u + s * 0.05, v - s * 0.32)], s * 0.006)
    elif kind == "cruiser":
        pen.rect(u - s * 0.12, v - s * 0.11, u + s * 0.14, v - s * high)
        pen.rect(u + s * 0.06, v - s * 0.18, u + s * 0.11, v - s * 0.11)
        for x in (-0.06, 0.0):
            pen.rect(u + s * x - s * 0.018, v - s * 0.17, u + s * x + s * 0.018, v - s * 0.11)
        for x in (0.25, -0.27):
            pen.rect(u + s * x - s * 0.03, v - s * 0.085, u + s * x + s * 0.03, v - s * high)
    else:
        pen.rect(u - s * 0.06, v - s * 0.17, u + s * 0.12, v - s * high)
        pen.rect(u - s * 0.02, v - s * 0.25, u + s * 0.02, v - s * 0.17)
        for x in (-0.30, 0.30):
            pen.line([(u + s * x, v - s * high), (u + s * x, v - s * 0.32)], s * 0.007)


def history_bikini(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = BIKINI
    shore = BIKINI_SHORE
    if layer_key == "sky":
        # A quiet grey-blue sky with flat high cloud in long even bands, and
        # under the horizon the calm wide lagoon, grey-green. No sun shows.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.92)), (0.30, p["top"]), (0.52, p["mid"]), (HORIZON - 0.004, p["low"]),
                                 (HORIZON + 0.002, mix(p["lagoon_light"], p["low"], 0.40)), (0.68, mix(p["lagoon"], p["lagoon_light"], 0.40)), (1.0, p["lagoon"])]))
        for k, (centre, half, cover, alpha) in enumerate(((0.16, 0.08, 0.55, 0.45), (0.30, 0.06, 0.50, 0.40), (0.44, 0.04, 0.46, 0.35))):
            clouds = cloud_mask(a, ("bikini cloud", k), centre, half, cells=2.5 + k, cover=cover, soft=0.40, stretch=9.0)
            a.put(layer, clouds, mix(p["cloud"], p["low"], k * 0.25), alpha)
            a.put(layer, clouds * a.band(centre + half * 0.5, half * 0.6), p["cloud_shadow"], 0.15)
        a.put(layer, (a.v > HORIZON) * a.band(HORIZON + 0.003, 0.0035, 1.0) * smoothstep(0.35, 0.60, a.noise("bikini reef", cells=30.0, octaves=3, stretch=3.0)), p["reef"], 0.45)
        lines = smoothstep(0.66, 0.86, a.noise("bikini far water", cells=60.0, octaves=2, stretch=18.0))
        a.light(layer, (a.v > HORIZON + 0.004) * lines, p["lagoon_light"], 0.15)
        a.tint(layer, fog(a, "bikini horizon haze", HORIZON, 0.016, 3.0), p["low"], 0.50)
        _textbook(a, layer, 0.06)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far bikini")
        cols = a.u[0]
        # The islet: a long low line of palms and pandanus at the left, a
        # few empty houses near its beach with their doors open. At the
        # right, far off in the lagoon, the grey ships at anchor, small and
        # still.
        land_top = shore - 0.006 - 0.004 * a.line_noise("bikini land", cells=8.0, octaves=2)
        land_top = np.where(cols < 0.58, land_top, 1.0) + 0.012 * smoothstep(0.52, 0.58, cols)
        land = _land(a, land_top.astype(np.float32)) * (a.v < shore + 0.004)
        bush, bush_pen = a.drawing()
        for _ in range(110):
            u = rng.uniform(-0.02, 0.57)
            bush_pen.ellipse(u, shore - 0.008 - rng.uniform(0.0, 0.004), rng.uniform(0.006, 0.013), rng.uniform(0.004, 0.009))
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        for k in range(26):
            u = -0.02 + k * 0.023 + rng.uniform(-0.007, 0.007)
            if u > 0.56 or 0.24 < u < 0.30:
                continue
            _coconut_palm(trunk_pen, crown_pen, rng, u, shore - 0.004, rng.uniform(0.045, 0.080), rng.uniform(-0.012, 0.012))
        for u in (0.10, 0.36, 0.50):
            _pandanus(trunk_pen, crown_pen, rng, u, shore - 0.002, 0.028, rng.uniform(-0.01, 0.01))
        roofs, roof_pen = a.drawing()
        dark, dark_pen = a.drawing()
        posts, post_pen = a.drawing()
        planks, plank_pen = a.drawing()
        _house(roof_pen, dark_pen, post_pen, 0.25, shore - 0.002, 0.012, 0.016, wall=post_pen, door=dark_pen)
        _house(roof_pen, dark_pen, post_pen, 0.285, shore - 0.002, 0.010, 0.014, wall=plank_pen, door=dark_pen)
        _house(roof_pen, dark_pen, post_pen, 0.43, shore - 0.002, 0.011, 0.015, wall=post_pen, door=dark_pen)
        beach, beach_pen = a.drawing()
        beach_pen.poly([(-0.02, shore - 0.004), (0.55, shore - 0.003), (0.60, shore + 0.003), (-0.02, shore + 0.004)])
        ships, ship_pen = a.drawing()
        for u, v, s, kind in ((0.66, HORIZON + 0.010, 0.050, "transport"), (0.73, HORIZON + 0.012, 0.070, "battleship"), (0.81, HORIZON + 0.009, 0.064, "carrier"),
                              (0.88, HORIZON + 0.011, 0.048, "cruiser"), (0.94, HORIZON + 0.008, 0.040, "transport"), (0.77, HORIZON + 0.005, 0.034, "cruiser")):
            _warship(ship_pen, u, v, s, kind)
        land_mask = np.maximum(land, a.mask_of(bush))
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        roof_mask = a.mask_of(roofs)
        post_mask = a.mask_of(posts)
        plank_mask = a.mask_of(planks)
        dark_mask = a.mask_of(dark) * (1.0 - roof_mask)
        beach_mask = a.mask_of(beach)
        ship_mask = a.mask_of(ships)
        water_top = (shore - 0.002) + (HORIZON + 0.004 - shore + 0.002) * smoothstep(0.56, 0.62, a.u)
        water = smoothstep(water_top, water_top + 0.004, a.v)
        things = np.maximum.reduce([land_mask, trunk_mask, crown_mask, roof_mask, post_mask, plank_mask, dark_mask, beach_mask])
        mask = np.maximum.reduce([things, ship_mask, water])
        layer = solid(a, mask, mix(p["island"], p["far"], 0.35), mix(p["island"], p["far"], 0.15), 0.56, 0.62, "bikini far", 0.03)
        a.put(layer, water, a.ramp([(0.0, mix(p["lagoon_light"], p["lagoon"], 0.40)), (HORIZON + 0.014, mix(p["lagoon_light"], p["lagoon"], 0.40)),
                                     (0.68, mix(p["lagoon"], p["lagoon_light"], 0.20)), (1.0, p["lagoon"])]))
        a.put(layer, _reflected(a, things, shore + 0.002, "bikini ripple", water * (a.v > shore + 0.002)), mix(p["island"], p["lagoon"], 0.55), 0.25)
        a.put(layer, ship_mask, mix(p["ship"], p["far"], 0.35))
        a.shade(layer, ship_mask * (a.v > HORIZON + 0.004), 0.12)
        a.put(layer, _reflected(a, ship_mask, HORIZON + 0.011, "bikini ship ripple", water * (1.0 - ship_mask) * (a.v > HORIZON + 0.010)), mix(p["ship_dark"], p["lagoon"], 0.55), 0.20)
        a.put(layer, land_mask, mix(p["island"], p["far"], 0.30))
        a.light(layer, land_mask * smoothstep(0.55, 0.75, a.noise("bikini bush", cells=80.0, octaves=2)), mix(p["island_light"], p["far"], 0.3), 0.25)
        a.put(layer, beach_mask, mix(p["sand"], p["far"], 0.10))
        a.put(layer, trunk_mask, mix(p["trunk"], p["far"], 0.25))
        a.put(layer, crown_mask, mix(p["palm"], p["far"], 0.22))
        a.light(layer, a.rim(crown_mask, 0.0, 0.0015, 0.0) * crown_mask, mix(p["palm_light"], p["far"], 0.2), 0.35)
        a.put(layer, post_mask, mix(p["thatch"], p["far"], 0.25))
        a.put(layer, plank_mask, mix(p["plank"], p["far"], 0.20))
        a.put(layer, dark_mask, mix(p["near"], p["far"], 0.35))
        a.put(layer, roof_mask, mix(p["thatch"], p["far"], 0.15))
        a.light(layer, a.rim(roof_mask, 0.0, 0.002, 0.0) * roof_mask, p["glow"], 0.25)
        haze(a, layer, p["low"], 0.08, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near bikini")
        bank, ground, bank_at = _bank(a, "near bikini", 0.040, 0.044)
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        leaves, leaf_pen = a.drawing()
        grass, grass_pen = a.drawing()
        # A coconut palm leans over the beach at the left and a pandanus
        # stands at the right, with low grey-green beach plants at their
        # feet. The middle is a calm, empty bank of pale sand.
        _coconut_palm(trunk_pen, crown_pen, rng, 0.07, bank_at(0.07) + 0.006, 0.48, 0.09)
        _coconut_palm(trunk_pen, crown_pen, rng, 0.17, bank_at(0.17) + 0.006, 0.34, 0.03)
        _pandanus(trunk_pen, leaf_pen, rng, 0.89, bank_at(0.89) + 0.006, 0.36, -0.04)
        for _ in range(14):
            u = rng.choice([rng.uniform(0.22, 0.32), rng.uniform(0.70, 0.82)])
            _grass_blades(grass_pen, rng, u, bank_at(u) + 0.002, rng.uniform(0.008, 0.014), 6, 0.0012, 0.012)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        leaf_mask = a.mask_of(leaves)
        grass_mask = a.mask_of(grass)
        mask = np.maximum.reduce([bank_mask, trunk_mask, crown_mask, leaf_mask, grass_mask])
        layer = a.blank()
        sand = a.ramp([(0.0, mix(p["near_light"], p["near"], 0.25)), (0.66, mix(p["near_light"], p["near"], 0.25)), (0.80, mix(p["near_light"], p["near"], 0.70)), (1.0, p["near"])])
        _near_paint(a, layer, bank_mask, sand, p["glow"], 0.25)
        a.put(layer, grass_mask, mix(p["island_light"], p["near"], 0.40))
        a.put(layer, trunk_mask, mix(p["trunk"], p["near"], 0.40))
        a.shade(layer, trunk_mask * (np.abs(((a.v * 260.0) % 1.0) - 0.5) < 0.10), 0.20)
        a.put(layer, crown_mask, mix(p["palm"], p["near"], 0.30))
        a.light(layer, a.rim(crown_mask, 0.0, 0.002, 0.0) * crown_mask, p["palm_light"], 0.30)
        a.put(layer, leaf_mask, mix(p["palm"], p["near"], 0.25))
        a.light(layer, a.rim(leaf_mask, 0.0, 0.002, 0.0) * leaf_mask, p["palm_light"], 0.28)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.15)
        haze(a, layer, p["low"], 0.10, None)
        return layer
    layer = _air(a, p, "bikini still haze", p["low"], 0.24, scale(p["near"], 0.85), 0.12)
    return layer


def bikini_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """The fronds of coconut palms hang into the top of the view at two
    places, still, in muted grey-green."""
    del layer_lights
    rng = art_.rand("bikini foreground")
    for k in range(2):
        _frond_from_above(pen, rng, 0.10 + (k + rng.uniform(0.2, 0.8)) * 0.40, 4, REST_TOP + 0.004)

