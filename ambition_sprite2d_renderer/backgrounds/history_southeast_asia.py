"""The scenes of the History dimension: Southeast Asia.

The History dimension is a grid. East is later, and each floor is a region
of the world. These rooms show the peoples of Southeast Asia: the first
painters of the karst caves of Sulawesi, the Austronesian seafarers who
came to the islands, and the bronze age of the Red River delta. They use
the same sepia of an old textbook and the same rules as `history_eras.py`
and `history_origins.py`. The people of these places show skill,
invention and a long history of their own; nothing here is a joke on them.

- ``history_wallacea`` (the karst of Maros-Pangkep, Sulawesi, about 51,000
  years ago). A warm, humid morning. Steep towers of grey-white limestone
  stand up from a green river plain. Rainforest grows on their tops and on
  every ledge, so each tower is furred with green. At the foot of the
  largest tower is the dark mouth of a cave. A slow river goes across the
  plain between palms to the sea, and a glimpse of the sea shows far off at
  the left. Far towers go back into a warm haze. Ferns and pandanus stand
  at the sides. People crossed these islands by sea on their way to Sahul.
- ``history_austronesia`` (the coasts of the Philippines and Indonesia,
  about 2000 BCE). A bright day. A turquoise lagoon lies inside a reef, and
  a white beach is in front of it. On the beach stand houses on posts, of
  bamboo and thatch, with high peaked roofs; outrigger canoes are pulled
  up on the sand. Coconut palms and banana plants grow along the shore.
  Behind the lagoon a green volcano rises, with a little cloud at its top.
- ``history_red_river`` (the Red River delta of northern Vietnam, 200 BCE
  to 43 CE). A soft, misty morning. Towers and humps of limestone stand in
  layers of blue mist. A wide brown river goes across the plain. Near it
  stand houses on posts with saddle roofs that curve up at the two ends
  like a boat. In front, flooded rice paddies are like mirrors of the sky,
  between raised green dikes. White egrets stand in the water and fly over
  it.

The bright detail is far off or at the edges, and the middle of each near
layer is calm, so the play in front of it reads. The things that drift in the
air are the room's motes (`terrain/motes.py`), not part of these pictures.
"""

from __future__ import annotations

import numpy as np

from .artkit import Art, Pen, mix, polar, scale, smoothstep
from .history_americas_pacific import _canopy, _coconut_palm, _fronds, _pandanus
from .history_eras import REST_BOTTOM, _air, _at, _heaps, _sun, _textbook
from .history_origins import _arch, _banana, _land, _leaf
from .parts import HORIZON, fog, haze, shafts, solid

# ---------------------------------------------------------------------------
# Parts that more than one room has
# ---------------------------------------------------------------------------


def _karst(pen: Pen, rng, u: float, v: float, w: float, h: float, lean: float = 0.0) -> None:
    """A tower of karst: a steep tower of limestone that the rain dissolved
    out of a plateau. Its sides are almost vertical, with ledges and steps
    in them. Its top is a crown of two to four knobs, and the forest on it
    makes its edge lumpy. `lean` moves the top to one side, in parts of
    `w`."""
    left, right = [], []
    walk = [0.0, 0.0]
    for k in range(11):
        t = k / 10.0
        y = v - h * 0.74 * t
        width = w * (1.0 - 0.12 * t + 0.06 * np.sin(np.pi * t))
        for side in range(2):
            walk[side] = float(np.clip(walk[side] + rng.uniform(-0.12, 0.12) * w, -0.18 * w, 0.18 * w))
        left.append((u - width + walk[0] + lean * w * t, y))
        right.append((u + width + walk[1] + lean * w * t, y))
    # The crown: knobs of different heights across the top.
    knobs = [(rng.uniform(0.15, 0.85), rng.uniform(0.4, 1.0), rng.uniform(0.08, 0.18)) for _ in range(rng.randint(2, 4))]
    x0, x1 = left[-1][0], right[-1][0]
    y0 = v - h * 0.74
    top = []
    for k in range(1, 18):
        s = k / 18.0
        rise = sum(amp * np.exp(-(((s - c) / wk) ** 2)) for c, amp, wk in knobs)
        rise = min(1.0, 0.15 + rise) * np.sin(np.pi * s) ** 0.4
        top.append((x0 + (x1 - x0) * s, y0 - h * 0.26 * rise))
    pen.poly([(left[0][0], v + 0.01)] + left + top + right[::-1] + [(right[0][0], v + 0.01)])
    # The crowns of the trees on the top make its edge lumpy.
    for x, y in top[::2]:
        pen.ellipse(x, y + w * 0.04, w * rng.uniform(0.10, 0.16), w * rng.uniform(0.07, 0.11))


def _paint_karst(a: Art, layer: np.ndarray, p: dict, mask: np.ndarray, tag: str, far: float, green: float = 1.0) -> np.ndarray:
    """Paint towers of karst over `mask`: grey-white rock with dark streaks
    where the rain runs down, lit on the side to the sun at the left, and a
    fur of green forest on the top and on the ledges. `far` mixes all of it
    into the haze. Returns the mask of the green."""
    a.put(layer, mask, mix(p["karst"], p["far"], far))
    faces = smoothstep(0.35, 0.65, a.noise((tag, "faces"), cells=24.0, octaves=2, stretch=0.4))
    a.light(layer, mask * faces, mix(p["karst_light"], p["far"], far), 0.30)
    streaks = smoothstep(0.50, 0.80, a.noise((tag, "streaks"), cells=90.0, octaves=2, stretch=0.08))
    a.shade(layer, mask * streaks, 0.32 * (1.0 - far))
    lit = a.rim(mask, 0.010, 0.0, 2.0) * mask
    a.light(layer, lit, mix(p["karst_light"], p["far"], far * 0.6), 0.55)
    a.shade(layer, a.rim(mask, -0.010, 0.0, 2.0) * mask, 0.28 * (1.0 - far * 0.5))
    # The forest: a thick cap on the top of each tower, and green on the
    # ledges of its sides that hangs down in tongues.
    cap = a.blur(a.rim(mask, 0.0, 0.034), 5.0)
    lumps = a.noise((tag, "forest"), cells=70.0, octaves=3)
    ledges = a.noise((tag, "ledges"), cells=40.0, octaves=3, stretch=2.5)
    tongues = a.noise((tag, "tongues"), cells=50.0, octaves=2, stretch=0.2)
    forest = mask * smoothstep(0.42, 0.56, cap * 1.6 + (lumps - 0.5) * 0.5) * green
    forest = np.maximum(forest, mask * smoothstep(0.65, 0.76, ledges * 0.65 + tongues * 0.35 + (lumps - 0.5) * 0.3) * green)
    a.put(layer, forest, mix(p["forest"], p["far"], far))
    a.light(layer, forest * smoothstep(0.55, 0.75, lumps), mix(p["forest_light"], p["far"], far), 0.50)
    a.light(layer, a.rim(forest, 0.003, 0.004, 0.6) * forest, mix(p["forest_light"], p["glow"], 0.3), 0.40)
    a.shade(layer, a.rim(forest, 0.0, -0.004, 0.6) * forest, 0.25 * (1.0 - far))
    return forest


def _fern(pen: Pen, rng, u: float, v: float, h: float, count: int = 7) -> None:
    """A clump of ferns: fronds that arch up and out from one base and bend
    over at their tips. Each frond has a row of small leaflets on each side
    of its rib, short near the tip."""
    for k in range(count):
        t = (k + 0.5) / count - 0.5
        ang = -90.0 + t * 150.0 + rng.uniform(-8.0, 8.0)
        length = h * rng.uniform(0.75, 1.0) * (1.0 - abs(t) * 0.3)
        tip = polar(u, v, length, ang)
        tip = (tip[0] + t * h * 0.3, tip[1] + length * 0.25)
        ctrl = polar(u, v, length * 0.7, ang - t * 20.0)
        rib = _arch((u, v), ctrl, tip, 14)
        pen.line(rib, h * 0.016)
        for i in range(2, len(rib) - 1):
            x, y = rib[i]
            nx, ny = rib[i + 1][0] - rib[i - 1][0], rib[i + 1][1] - rib[i - 1][1]
            d = max(float(np.hypot(nx, ny)), 1e-9)
            nx, ny = nx / d, ny / d
            side = h * 0.12 * (1.0 - i / len(rib)) ** 0.8
            for s in (-1.0, 1.0):
                end = (x - ny * side * s + nx * side * 0.35, y + nx * side * s + ny * side * 0.35 + side * 0.25)
                _leaf(pen, [(x, y), ((x + end[0]) * 0.5, (y + end[1]) * 0.5), end], h * 0.014, 0.6)


def _house_on_posts(posts: Pen, walls: Pen, roof: Pen, u: float, v: float, w: float, h: float, saddle: bool) -> None:
    """A house of bamboo and thatch raised on posts over the wet ground. The
    floor is high, a ladder goes up to it, and the walls are low under a big
    roof. With `saddle` the ridge of the roof sags in the middle and its two
    ends sweep up and out past the walls like the ends of a boat (the houses
    of the Dong Son drums). Without it the roof is a tall peak with short
    crossed horns at the two ends of its ridge."""
    floor = v - h * 0.38
    for k in range(4):
        x = u - w * 0.80 + k * w * 0.533
        posts.line([(x, v + 0.002), (x, floor)], w * 0.09)
    posts.rect(u - w * 0.98, floor - h * 0.035, u + w * 0.98, floor)
    posts.line([(u + w * 1.30, v + 0.001), (u + w * 0.80, floor)], w * 0.07)
    for k in range(4):
        y = v - (v - floor) * (k + 0.5) / 4.0
        posts.line([(u + w * 1.30 - (w * 0.5) * (k + 0.5) / 4.0 - w * 0.08, y), (u + w * 1.30 - (w * 0.5) * (k + 0.5) / 4.0 + w * 0.08, y)], w * 0.05)
    walls.rect(u - w * 0.78, floor - h * 0.30, u + w * 0.78, floor - h * 0.035)
    eave = floor - h * 0.20
    if saddle:
        # The ridge sags in the middle, and the ridge and the eaves both
        # sweep up at the two ends and reach out past the walls, like the
        # ends of a boat. The eaves stay above the floor, so the walls show
        # under them and the roof does not read as a bowl.
        ridge = _arch((u - w * 2.05, floor - h * 1.30), (u, floor - h * 0.60), (u + w * 2.05, floor - h * 1.30), 16)
        eaves = _arch((u - w * 1.75, floor - h * 0.50), (u, floor - h * 0.02), (u + w * 1.75, floor - h * 0.50), 16)
        roof.poly(eaves + ridge[::-1])
        # The ridge beam on top, in the colour of the posts. Its two ends
        # stand out past the thatch and curl up.
        beam = [(x, y - h * 0.03) for x, y in ridge]
        posts.line(beam, w * 0.07)
        for end, s in ((beam[0], -1.0), (beam[-1], 1.0)):
            posts.line([end, (end[0] + s * w * 0.20, end[1] - h * 0.08), (end[0] + s * w * 0.16, end[1] - h * 0.16)], w * 0.06)
    else:
        apex = floor - h * 1.10
        roof.poly([(u - w * 1.25, eave), (u + w * 1.25, eave), (u + w * 0.12, apex), (u - w * 0.12, apex)])
        for s in (-1.0, 1.0):
            roof.line([(u + s * w * 0.05, apex + h * 0.06), (u + s * w * 0.32, apex - h * 0.12)], w * 0.07)


def _egret(pen: Pen, u: float, v: float, s: float, facing: float = 1.0) -> None:
    """A white egret that stands in the water: a slim body, a long neck in
    an S, a long thin bill and long dark legs (the legs are drawn by the
    caller in its own colour)."""
    f = facing
    pen.ellipse(u, v - s * 0.55, s * 0.32, s * 0.14)
    pen.poly([(u - f * s * 0.30, v - s * 0.58), (u - f * s * 0.55, v - s * 0.50), (u - f * s * 0.28, v - s * 0.48)])
    neck = _arch((u + f * s * 0.22, v - s * 0.62), (u + f * s * 0.02, v - s * 0.95), (u + f * s * 0.24, v - s * 1.15), 8)
    pen.line(neck, s * 0.09)
    pen.ellipse(neck[-1][0], neck[-1][1], s * 0.08, s * 0.06)
    pen.line([neck[-1], (neck[-1][0] + f * s * 0.30, neck[-1][1] + s * 0.03)], s * 0.035)


def _egret_flying(pen: Pen, u: float, v: float, s: float, beat: float, facing: float = 1.0) -> None:
    """A white egret in flight: broad wings, the neck drawn back, and the
    legs that trail behind."""
    f = facing
    lift = s * 0.35 * beat
    pen.ellipse(u, v, s * 0.30, s * 0.08)
    pen.poly([(u - s * 0.10, v - s * 0.02), (u + s * 0.12, v - s * 0.02), (u + s * 0.02 - f * s * 0.10, v - s * 0.55 - lift), (u - s * 0.28, v - s * 0.40 - lift)])
    pen.poly([(u - s * 0.06, v + s * 0.02), (u + s * 0.14, v + s * 0.02), (u + s * 0.26, v + s * 0.30 + lift * 0.4), (u - s * 0.02, v + s * 0.22 + lift * 0.4)])
    pen.ellipse(u + f * s * 0.36, v - s * 0.04, s * 0.09, s * 0.07)
    pen.line([(u + f * s * 0.42, v - s * 0.04), (u + f * s * 0.62, v - s * 0.02)], s * 0.035)
    pen.line([(u - f * s * 0.28, v + s * 0.02), (u - f * s * 0.72, v + s * 0.05)], s * 0.035)


def _far_palm(trunk: Pen, crown: Pen, rng, u: float, v: float, h: float, lean: float) -> None:
    """A coconut palm far off: the same shape as a near one, with thicker
    fronds, so that its crown still reads when it is small and soft."""
    w = h * 0.035
    pts = [(u + lean * t**1.6, v + 0.004 - (h + 0.004) * t) for t in np.linspace(0.0, 1.0, 10)]
    trunk.line(pts, w)
    _fronds(crown, rng, pts[-1], h, 9, 0.34, 0.50, w * 1.1, 0.07)


def _bamboo(culms: Pen, leaves: Pen, rng, u: float, v: float, h: float, count: int = 9) -> None:
    """A clump of bamboo: many tall thin culms from one base that lean out
    and bend over at their tops, with joints, and sprays of narrow leaves
    along their upper parts."""
    for k in range(count):
        t = (k + 0.5) / count - 0.5
        lean = t * h * 0.55 + rng.uniform(-0.04, 0.04) * h
        top = (u + lean * 1.4, v - h * rng.uniform(0.85, 1.0) * (1.0 - abs(t) * 0.25))
        culm = _arch((u + t * h * 0.06, v + 0.004), (u + lean * 0.3, v - h * 0.6), top, 14)
        culms.line(culm, h * 0.010)
        for i in range(5, len(culm), 2):
            x, y = culm[i]
            for s in (-1.0, 1.0):
                for j in range(3):
                    ang = (180.0 if s < 0 else 0.0) + s * (20.0 + j * 18.0) + rng.uniform(-10.0, 10.0)
                    length = h * rng.uniform(0.05, 0.08)
                    tip = polar(x, y, length, ang)
                    tip = (tip[0], tip[1] + length * 0.5)
                    _leaf(leaves, [(x, y), polar(x, y, length * 0.5, ang), tip], h * 0.008, 0.5)


def _hanging_vine(pen: Pen, rng, u: float, v_top: float, v_end: float, width: float) -> None:
    """A liana that hangs from above and sways a little, with small leaves
    along it."""
    pts = [(u + 0.006 * np.sin(k * 0.8 + rng.uniform(0.0, 1.0)) * k / 10.0, v_top + (v_end - v_top) * k / 10.0) for k in range(11)]
    pen.line(pts, width)
    for i, (x, y) in enumerate(pts[2:], 2):
        side = 1.0 if i % 2 else -1.0
        tip = (x + side * 0.010, y + 0.008)
        _leaf(pen, [(x, y), (x + side * 0.005, y + 0.002), tip], 0.0028, 0.6)


# ---------------------------------------------------------------------------
# Wallacea: the karst of Maros-Pangkep
# ---------------------------------------------------------------------------


WALLACEA = {
    "top": (110, 146, 156),
    "mid": (180, 200, 194),
    "low": (236, 228, 204),
    "glow": (255, 236, 198),
    "sun": (255, 246, 224),
    "cloud": (246, 242, 232),
    "cloud_shadow": (180, 186, 178),
    "sea": (92, 140, 150),
    "sea_light": (206, 226, 220),
    "karst": (184, 182, 170),
    "karst_light": (236, 232, 218),
    "forest": (52, 102, 60),
    "forest_light": (112, 156, 82),
    "plain": (94, 128, 66),
    "plain_light": (150, 170, 92),
    "river": (156, 176, 160),
    "cave": (30, 24, 22),
    "palm": (62, 104, 58),
    "trunk": (120, 98, 72),
    "far": (198, 206, 194),
    "near": (28, 40, 30),
    "near_light": (98, 130, 80),
    "fern": (70, 118, 62),
    "fern_light": (146, 178, 98),
    "rock": (176, 172, 160),
    "moss": (58, 96, 52),
}


def history_wallacea(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = WALLACEA
    sun_at = (0.24, 0.30)
    coast_u = 0.16
    if layer_key == "sky":
        # A warm, humid sky: grey-green blue at the top and warm white low
        # down, with the sun a soft disc in the haze.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.85)), (0.24, p["top"]), (0.46, p["mid"]), (HORIZON - 0.01, p["low"]),
                                 (HORIZON + 0.002, p["sea"]), (1.0, p["sea"])]))
        _sun(a, layer, *sun_at, 0.022, p["sun"], p["glow"], 0.55)
        _heaps(a, layer, "wallacea heaps", ((0.58, 0.40, 0.06, 0.05), (0.86, 0.43, 0.05, 0.035)), p["cloud"], p["cloud_shadow"], 0.75)
        a.tint(layer, fog(a, "wallacea high haze", 0.36, 0.10, 2.0), p["low"], 0.30)
        # Far towers of karst in rows that go back into the haze, and the
        # sea far off at the left, with a few lines of light on it.
        rng = a.rand("wallacea far towers")
        for k, (count, base, hmin, hmax, pale) in enumerate(((16, HORIZON + 0.004, 0.05, 0.10, 0.62), (12, HORIZON + 0.006, 0.07, 0.14, 0.42))):
            towers, pen = a.drawing()
            for _ in range(count):
                u = rng.uniform(coast_u + 0.06, 1.04)
                w = rng.uniform(0.012, 0.026)
                _karst(pen, rng, u, base, w, rng.uniform(hmin, hmax), rng.uniform(-0.3, 0.3))
            mask = a.mask_of(towers, blur=0.6)
            _paint_karst(a, layer, p, mask, f"wallacea sky towers {k}", pale, 0.8)
            a.tint(layer, mask * fog(a, ("wallacea tower mist", k), HORIZON - 0.01, 0.03, 3.0), p["low"], 0.6)
        sea = (a.v > HORIZON + 0.002).astype(np.float32)
        a.light(layer, sea * smoothstep(0.62, 0.80, a.noise("wallacea sea lines", cells=50.0, octaves=2, stretch=12.0)), p["sea_light"], 0.35)
        a.tint(layer, fog(a, "wallacea sea haze", HORIZON - 0.002, 0.012, 3.0), p["low"], 0.6)
        _textbook(a, layer, 0.08)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far wallacea")
        # The plain: green, from the coast at the left to the feet of the
        # towers. At the left it ends at the sea.
        _, plain = a.ridge("wallacea plain", HORIZON + 0.010, 0.003, cells=4.0, octaves=2)
        coast = coast_u - (a.v - HORIZON) * 1.6
        land = _land(a, plain) * smoothstep(coast - 0.01, coast + 0.01, a.u)
        towers, tower_pen = a.drawing()
        mouths, mouth_pen = a.drawing()
        for u, w, h, lean in ((0.24, 0.030, 0.13, 0.2), (0.31, 0.022, 0.09, -0.2), (0.66, 0.034, 0.18, -0.1), (0.78, 0.046, 0.26, 0.1),
                              (0.90, 0.036, 0.15, 0.25), (0.98, 0.030, 0.19, -0.2)):
            _karst(tower_pen, rng, u, _at(plain, u) + 0.012, w, h, lean)
        # The cave mouth at the foot of the big tower: a dark arch, low and
        # wide, a little above the plain.
        cu, cv = 0.775, _at(plain, 0.78) + 0.004
        mouth_pen.ellipse(cu, cv - 0.020, 0.020, 0.020)
        mouth_pen.rect(cu - 0.020, cv - 0.020, cu + 0.020, cv)
        mouth_pen.poly([(cu - 0.026, cv), (cu - 0.020, cv - 0.012), (cu + 0.020, cv - 0.012), (cu + 0.028, cv)])
        # The rainforest along the feet of the towers, the river, and palms
        # on the plain.
        trees, tree_pen = a.drawing()
        _canopy(tree_pen, rng, plain, 0.20, 1.0, 0.006, 0.006, 0.014, 120)
        mid = HORIZON + 0.030 + 0.008 * np.sin(a.u * 7.0 + 1.0) + 0.004 * np.sin(a.u * 19.0)
        river = smoothstep(0.0040, 0.0020, np.abs(a.v - mid)) * land * smoothstep(0.0, 0.05, a.u - coast_u)
        palms, palm_pen = a.drawing()
        trunks, trunk_pen = a.drawing()
        for u, v, h in ((0.20, 0.632, 0.040), (0.23, 0.636, 0.050), (0.38, 0.640, 0.045), (0.43, 0.646, 0.060), (0.47, 0.642, 0.040),
                        (0.56, 0.652, 0.050), (0.62, 0.660, 0.064), (0.88, 0.648, 0.052), (0.93, 0.656, 0.062)):
            _far_palm(trunk_pen, palm_pen, rng, u, v, h * 1.5, rng.uniform(-0.012, 0.012))
        tower_mask = a.mask_of(towers)
        mouth_mask = a.mask_of(mouths) * tower_mask
        tree_mask = a.mask_of(trees) * smoothstep(0.18, 0.22, a.u)
        palm_mask = np.maximum(a.mask_of(palms), a.mask_of(trunks))
        mask = np.maximum.reduce([land, tower_mask, tree_mask, palm_mask])
        layer = solid(a, mask, mix(p["plain"], p["far"], 0.35), p["plain"], HORIZON, HORIZON + 0.10, "wallacea far", 0.06)
        # Grass and swamp in patches, and dark groves of trees on the plain.
        a.light(layer, land * smoothstep(0.55, 0.75, a.noise("wallacea fields", cells=30.0, octaves=3, stretch=4.0)), p["plain_light"], 0.35)
        a.put(layer, land * smoothstep(0.68, 0.74, a.noise("wallacea groves", cells=80.0, octaves=3, stretch=2.0)), p["forest"], 0.75)
        a.put(layer, river, mix(p["river"], p["sea_light"], 0.3), 0.85)
        _paint_karst(a, layer, p, tower_mask, "wallacea far towers", 0.12)
        # The cave: dark inside, its lip lit, and a few roots that hang over
        # its top.
        a.put(layer, mouth_mask, p["cave"])
        a.light(layer, a.rim(mouth_mask, 0.0, -0.003, 0.5) * tower_mask * (1.0 - mouth_mask), p["karst_light"], 0.5)
        a.shade(layer, a.rim(mouth_mask, 0.0, 0.004, 0.6) * mouth_mask, 0.0)
        a.put(layer, tree_mask, mix(p["forest"], p["far"], 0.25))
        a.light(layer, a.rim(tree_mask, 0.003, 0.004, 0.5) * tree_mask, p["forest_light"], 0.45)
        a.put(layer, a.mask_of(trunks), mix(p["trunk"], p["far"], 0.2))
        a.put(layer, a.mask_of(palms), mix(p["palm"], p["far"], 0.2))
        a.light(layer, a.rim(a.mask_of(palms), 0.002, 0.002, 0.3) * a.mask_of(palms), p["forest_light"], 0.4)
        # The humid haze: thick far off, and on the feet of the towers.
        a.tint(layer, fog(a, "wallacea plain haze", HORIZON + 0.004, 0.018, 3.0) * mask, p["low"], 0.45)
        haze(a, layer, p["low"], 0.08, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near wallacea")
        bank, bank_pen = a.drawing()
        rocks, rock_pen = a.drawing()
        ferns, fern_pen = a.drawing()
        trunks, trunk_pen = a.drawing()
        leaves, leaf_pen = a.drawing()
        ground, line = a.ridge("near wallacea", 0.705, 0.006, cells=4.0, octaves=3)
        pts = [(u, _at(line, u) - 0.045 * smoothstep(0.28, 0.02, u) - 0.030 * smoothstep(0.72, 0.98, u)) for u in np.linspace(0.0, 1.0, 60)]
        bank_pen.poly([(0.0, 1.0)] + pts + [(1.0, 1.0)])

        def bank_at(u: float) -> float:
            return float(np.interp(u, [q[0] for q in pts], [q[1] for q in pts]))

        # A block of limestone at the left, fallen from a tower, with moss
        # on its top; ferns at its foot and a pandanus at the right.
        _karst(rock_pen, rng, 0.04, bank_at(0.04) + 0.012, 0.055, 0.19, 0.25)
        _karst(rock_pen, rng, 0.13, bank_at(0.13) + 0.010, 0.030, 0.045, -0.2)
        for u, h in ((0.17, 0.060), (0.22, 0.040), (0.78, 0.045), (0.97, 0.050)):
            _fern(fern_pen, rng, u, bank_at(u) + 0.004, h, 9)
        for _ in range(10):
            u = rng.uniform(0.30, 0.70)
            _fern(fern_pen, rng, u, bank_at(u) + 0.002, rng.uniform(0.010, 0.016), 5)
        _pandanus(trunk_pen, leaf_pen, rng, 0.88, bank_at(0.88) + 0.004, 0.38, -0.05)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        rock_mask = a.mask_of(rocks)
        fern_mask = a.mask_of(ferns)
        leaf_mask = a.mask_of(leaves)
        trunk_mask = a.mask_of(trunks)
        mask = np.maximum.reduce([bank_mask, rock_mask, fern_mask, leaf_mask, trunk_mask])
        layer = a.blank()
        earth = a.ramp([(0.0, mix(p["moss"], p["near"], 0.35)), (0.66, mix(p["moss"], p["near"], 0.35)), (0.80, mix(p["moss"], p["near"], 0.75)), (1.0, p["near"])])
        a.put(layer, bank_mask, earth)
        a.light(layer, bank_mask * smoothstep(0.6, 0.8, a.noise("wallacea litter", cells=120.0, octaves=1)) * smoothstep(0.74, 0.70, a.v), p["near_light"], 0.25)
        a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, p["glow"], 0.30)
        near_karst = {**p, "karst": mix(p["rock"], p["near"], 0.30), "karst_light": mix(p["karst_light"], p["near"], 0.15),
                      "forest": mix(p["moss"], p["near"], 0.20), "forest_light": mix(p["fern_light"], p["near"], 0.25), "far": p["near"]}
        _paint_karst(a, layer, near_karst, rock_mask, "wallacea near rock", 0.0, 0.9)
        a.put(layer, trunk_mask, mix(p["trunk"], p["near"], 0.45))
        a.put(layer, leaf_mask, mix(p["fern"], p["near"], 0.40))
        a.light(layer, a.rim(leaf_mask, 0.002, 0.002, 0.3) * leaf_mask, p["fern_light"], 0.35)
        a.put(layer, fern_mask, mix(p["fern"], p["near"], 0.30))
        a.light(layer, a.rim(fern_mask, 0.002, 0.002, 0.3) * fern_mask, mix(p["fern_light"], p["glow"], 0.2), 0.40)
        a.shade(layer, a.rim(mask, 0.004, -0.003, 1.0) * mask, 0.20)
        haze(a, layer, p["low"], 0.08, None)
        return layer
    layer = _air(a, p, "wallacea humid air", p["low"], 0.24, scale(p["near"], 0.8), 0.22)
    a.put(layer, shafts(a, "wallacea shafts", 4, 0.14, 0.0, 0.85, 0.05), p["glow"], 0.08)
    return layer


def wallacea_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Ferns that stand from below at two places, and a liana that hangs
    from above at one place."""
    del layer_lights
    rng = art_.rand("wallacea foreground")
    for k in range(2):
        u0 = (k + rng.uniform(0.2, 0.8)) / 2.0
        for j in range(5):
            t = j / 4.0 - 0.5
            ang = -90.0 + t * 70.0
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
                    end = (x + s * side, max(y - side * 0.3, REST_BOTTOM - 0.010))
                    pen.line([(x, y), end], 0.0014)
    u = rng.uniform(0.35, 0.65)
    _hanging_vine(pen, rng, u, 0.0, 0.378, 0.0022)


# ---------------------------------------------------------------------------
# Austronesia: a lagoon of the islands, about 2000 BCE
# ---------------------------------------------------------------------------


AUSTRONESIA = {
    "top": (40, 108, 178),
    "mid": (128, 186, 222),
    "low": (232, 238, 228),
    "glow": (255, 240, 206),
    "sun": (255, 250, 232),
    "cloud": (250, 250, 246),
    "cloud_shadow": (160, 178, 196),
    "ocean": (34, 94, 150),
    "lagoon": (64, 190, 186),
    "lagoon_light": (200, 244, 230),
    "reef": (246, 250, 246),
    "volcano": (78, 128, 70),
    "volcano_light": (150, 184, 100),
    "volcano_dark": (44, 84, 54),
    "sand": (232, 214, 170),
    "sand_light": (250, 240, 210),
    "sand_dark": (186, 160, 116),
    "thatch": (196, 160, 98),
    "bamboo": (176, 150, 96),
    "wood": (120, 86, 58),
    "palm": (70, 120, 62),
    "palm_light": (140, 180, 90),
    "trunk": (134, 108, 80),
    "banana": (96, 150, 66),
    "far": (200, 216, 214),
    "near": (62, 50, 36),
    "near_light": (188, 164, 116),
}


def _canoe_ashore(hull: Pen, boom: Pen, u: float, v: float, s: float, facing: float = 1.0) -> None:
    """An outrigger canoe pulled up on the sand: a long, narrow hull with
    ends that rise a little, two booms across it, and the float of the
    outrigger beside it (seen behind the hull, so a little higher)."""
    f = facing
    hull.poly([(u - s * 0.50, v - s * 0.07), (u - s * 0.38, v - s * 0.05), (u + s * 0.38, v - s * 0.05), (u + f * s * 0.54, v - s * 0.11),
               (u + s * 0.40, v), (u - s * 0.40, v), (u - f * s * 0.54, v - s * 0.10)])
    for du in (-0.18, 0.16):
        boom.line([(u + du * s, v - s * 0.05), (u + du * s + s * 0.03, v - s * 0.16)], s * 0.018)
    boom.poly([(u - s * 0.32, v - s * 0.15), (u + s * 0.34, v - s * 0.15), (u + s * 0.38, v - s * 0.17), (u + s * 0.32, v - s * 0.19), (u - s * 0.30, v - s * 0.19),
               (u - s * 0.36, v - s * 0.17)])


def history_austronesia(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = AUSTRONESIA
    sun_at = (0.18, 0.28)
    reef_v = HORIZON + 0.012
    beach_v = 0.664
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.85)), (0.24, p["top"]), (0.46, p["mid"]), (HORIZON - 0.01, p["low"]),
                                 (HORIZON, mix(p["low"], p["ocean"], 0.5)), (HORIZON + 0.01, p["ocean"]), (1.0, p["ocean"])]))
        _sun(a, layer, *sun_at, 0.024, p["sun"], p["glow"], 0.65)
        _heaps(a, layer, "austronesia heaps", ((0.34, 0.47, 0.06, 0.05), (0.96, 0.45, 0.04, 0.03)), p["cloud"], p["cloud_shadow"], 0.85)
        # The volcano: a wide green cone behind the lagoon, its slopes cut
        # by gullies, and a little cloud at its top.
        cone, cone_pen = a.drawing()
        top_u, top_v = 0.70, 0.43
        rng = a.rand("austronesia cone")
        # The sides of a volcano are concave: steep near the top and long
        # and low at the foot.
        left = [(top_u - 0.025 - 0.30 * (1.0 - t) ** 2.2 + rng.uniform(-0.003, 0.003), HORIZON + 0.004 - (HORIZON + 0.004 - top_v) * t) for t in np.linspace(0.0, 1.0, 16)]
        right = [(top_u + 0.025 + 0.34 * (1.0 - t) ** 2.0 + rng.uniform(-0.003, 0.003), HORIZON + 0.004 - (HORIZON + 0.004 - top_v) * t) for t in np.linspace(0.0, 1.0, 16)]
        cone_pen.poly(left + [(top_u - 0.012, top_v + 0.004), (top_u, top_v + 0.008), (top_u + 0.014, top_v + 0.002)] + right[::-1])
        mask = a.mask_of(cone, blur=0.4)
        paint = a.ramp([(0.0, p["volcano"]), (top_v, mix(p["volcano"], p["far"], 0.25)), (HORIZON, mix(p["volcano"], p["low"], 0.45)), (1.0, p["volcano"])])
        a.put(layer, mask, paint)
        gullies = smoothstep(0.62, 0.82, a.noise("austronesia gullies", cells=36.0, octaves=2, stretch=0.30))
        a.shade(layer, mask * gullies * smoothstep(top_v, top_v + 0.05, a.v), 0.12)
        forest = smoothstep(0.50, 0.70, a.noise("austronesia cone forest", cells=50.0, octaves=3)) * smoothstep(top_v + 0.06, top_v + 0.12, a.v)
        a.put(layer, mask * forest, mix(p["volcano_dark"], p["far"], 0.25), 0.6)
        a.light(layer, a.rim(mask, 0.016, 0.0, 2.5) * mask, mix(p["volcano_light"], p["glow"], 0.3), 0.50)
        a.light(layer, mask * smoothstep(0.55, 0.75, a.noise("austronesia slopes", cells=40.0, octaves=3)) * (a.u < top_u), p["volcano_light"], 0.25)
        _heaps(a, layer, "austronesia summit", ((top_u + 0.035, top_v - 0.004, 0.040, 0.026),), p["cloud"], p["cloud_shadow"], 0.92)
        a.tint(layer, fog(a, "austronesia low haze", HORIZON - 0.008, 0.016, 3.0), p["low"], 0.55)
        sea = (a.v > HORIZON + 0.002).astype(np.float32)
        a.light(layer, sea * smoothstep(0.62, 0.82, a.noise("austronesia sea lines", cells=50.0, octaves=2, stretch=12.0)), p["lagoon_light"], 0.35)
        _textbook(a, layer, 0.06)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far austronesia")
        # The far shore at the foot of the volcano: a low green strip with
        # trees. The reef, the lagoon and the beach come toward the eye.
        far_shore, shore_pen = a.drawing()
        _, sline = a.ridge("austronesia far shore", reef_v - 0.003, 0.002, cells=5.0, octaves=2)
        shore_pen.poly([(0.36, reef_v + 0.004)] + [(u, _at(sline, u) - 0.006 * smoothstep(0.36, 0.5, u)) for u in np.linspace(0.36, 1.0, 20)] + [(1.0, reef_v + 0.004)])
        _canopy(shore_pen, rng, sline, 0.42, 1.0, 0.002, 0.002, 0.005, 80)
        lagoon = smoothstep(reef_v - 0.002, reef_v + 0.002, a.v)
        _, bline = a.ridge("austronesia beach", beach_v, 0.002, cells=3.0, octaves=2)
        beach = _land(a, bline)
        houses = {key: a.drawing() for key in ("posts", "walls", "roof")}
        boats, boat_pen = a.drawing()
        booms, boom_pen = a.drawing()
        palms, palm_pen = a.drawing()
        trunks, trunk_pen = a.drawing()
        bananas, banana_pen = a.drawing()
        # The village on the beach at the right; canoes pulled up on the
        # sand at the left; palms and bananas along the shore.
        for u, w in ((0.62, 0.026), (0.735, 0.032), (0.86, 0.028)):
            _house_on_posts(houses["posts"][1], houses["walls"][1], houses["roof"][1], u, _at(bline, u) + 0.004, w, w * 2.2, saddle=False)
        for u, s, f in ((0.21, 0.10, 1.0), (0.33, 0.085, -1.0), (0.44, 0.11, 1.0)):
            _canoe_ashore(boat_pen, boom_pen, u, _at(bline, u) + 0.014, s, f)
        for u, h, lean in ((0.08, 0.11, 0.014), (0.13, 0.085, -0.010), (0.54, 0.12, 0.016), (0.685, 0.10, -0.012), (0.80, 0.13, 0.018), (0.93, 0.115, -0.014)):
            _far_palm(trunk_pen, palm_pen, rng, u, _at(bline, u) + 0.002, h, lean)
        for u, h in ((0.57, 0.030), (0.665, 0.026), (0.91, 0.032), (0.98, 0.028)):
            _banana(banana_pen, banana_pen, rng, u, _at(bline, u) + 0.003, h)
        shore_mask = a.mask_of(far_shore)
        house_masks = {key: a.mask_of(img) for key, (img, _) in houses.items()}
        things = np.maximum.reduce([*house_masks.values(), a.mask_of(boats), a.mask_of(booms), a.mask_of(palms), a.mask_of(trunks), a.mask_of(bananas)])
        mask = np.maximum.reduce([lagoon, shore_mask, beach, things])
        layer = solid(a, mask, mix(p["lagoon"], p["far"], 0.20), mix(p["lagoon"], p["lagoon_light"], 0.25), reef_v, beach_v, "austronesia far", 0.03)
        # The reef: a line of white surf; the lagoon inside it is turquoise
        # over the white sand, with ripples and the light of the sun.
        surf = a.band(reef_v + 0.002, 0.003, 1.0) * smoothstep(0.30, 0.55, a.noise("austronesia surf", cells=40.0, octaves=3, stretch=3.0))
        a.put(layer, surf * (1.0 - shore_mask), p["reef"], 0.95)
        ripples = smoothstep(0.55, 0.80, a.noise("austronesia ripples", cells=70.0, octaves=2, stretch=9.0))
        a.light(layer, lagoon * ripples * (1.0 - beach), p["lagoon_light"], 0.45)
        a.light(layer, lagoon * a.band(beach_v - 0.004, 0.010, 1.0) * (1.0 - beach), p["lagoon_light"], 0.55)
        a.put(layer, shore_mask, mix(p["volcano_dark"], p["far"], 0.35))
        a.light(layer, a.rim(shore_mask, 0.002, 0.002, 0.3) * shore_mask, p["volcano_light"], 0.4)
        # The beach: white sand, lit, with a wet edge at the water.
        a.put(layer, beach, a.ramp([(0.0, p["sand_light"]), (beach_v, p["sand_light"]), (beach_v + 0.03, p["sand"]), (1.0, p["sand"])]))
        a.put(layer, beach * a.band(beach_v + 0.002, 0.003, 1.0), p["sand_dark"], 0.45)
        a.light(layer, beach * smoothstep(0.6, 0.8, a.noise("austronesia sand", cells=40.0, octaves=2, stretch=5.0)), p["sand_light"], 0.35)
        # The houses: posts of wood, walls of bamboo, roofs of thatch lit at
        # the left.
        a.put(layer, house_masks["posts"], mix(p["wood"], p["far"], 0.15))
        a.put(layer, house_masks["walls"], mix(p["bamboo"], p["far"], 0.10))
        canes = np.clip(1.0 - np.abs(((a.u * 900.0) % 1.0) - 0.5) / 0.18, 0.0, 1.0)
        a.shade(layer, house_masks["walls"] * canes, 0.18)
        roof = house_masks["roof"]
        a.put(layer, roof, mix(p["thatch"], p["far"], 0.08))
        a.shade(layer, roof * smoothstep(0.3, 0.9, a.noise("austronesia thatch", cells=200.0, octaves=1, stretch=0.12)), 0.16)
        a.light(layer, a.rim(roof, 0.004, 0.0, 0.3) * roof, p["glow"], 0.45)
        a.shade(layer, a.rim(roof, 0.0, -0.003, 0.0) * roof, 0.30)
        a.put(layer, a.mask_of(boats), p["wood"])
        a.light(layer, a.rim(a.mask_of(boats), 0.0, 0.002, 0.0) * a.mask_of(boats), p["sand_light"], 0.4)
        a.put(layer, a.mask_of(booms), mix(p["wood"], p["sand_dark"], 0.30))
        a.put(layer, a.mask_of(trunks), mix(p["trunk"], p["far"], 0.10))
        a.put(layer, a.mask_of(palms), mix(p["palm"], p["far"], 0.10))
        a.put(layer, a.mask_of(bananas), mix(p["banana"], p["far"], 0.10))
        greens = np.maximum(a.mask_of(palms), a.mask_of(bananas))
        a.light(layer, a.rim(greens, 0.003, 0.003, 0.4) * greens, p["palm_light"], 0.5)
        haze(a, layer, p["low"], 0.06, reef_v + 0.01)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near austronesia")
        bank, bank_pen = a.drawing()
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        bananas, banana_pen = a.drawing()
        ground, line = a.ridge("near austronesia", 0.705, 0.005, cells=4.0, octaves=3)
        pts = [(u, _at(line, u) - 0.030 * smoothstep(0.26, 0.02, u) - 0.040 * smoothstep(0.74, 0.98, u)) for u in np.linspace(0.0, 1.0, 60)]
        bank_pen.poly([(0.0, 1.0)] + pts + [(1.0, 1.0)])

        def bank_at(u: float) -> float:
            return float(np.interp(u, [q[0] for q in pts], [q[1] for q in pts]))

        # A coconut palm that leans out over the beach at the left, and
        # banana plants at the right. The middle is open sand.
        _coconut_palm(trunk_pen, crown_pen, rng, 0.07, bank_at(0.07) + 0.006, 0.34, 0.10)
        _coconut_palm(trunk_pen, crown_pen, rng, 0.17, bank_at(0.17) + 0.004, 0.22, -0.04)
        for u, h in ((0.83, 0.16), (0.93, 0.22), (0.99, 0.14)):
            _banana(banana_pen, banana_pen, rng, u, bank_at(u) + 0.004, h)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        banana_mask = a.mask_of(bananas)
        mask = np.maximum.reduce([bank_mask, trunk_mask, crown_mask, banana_mask])
        layer = a.blank()
        sand = a.ramp([(0.0, mix(p["sand"], p["near"], 0.12)), (0.68, mix(p["sand"], p["near"], 0.12)), (0.82, mix(p["near_light"], p["near"], 0.55)), (1.0, p["near"])])
        a.put(layer, bank_mask, sand)
        a.light(layer, bank_mask * smoothstep(0.55, 0.75, a.noise("austronesia near drifts", cells=16.0, octaves=2, stretch=4.0)), p["sand_light"], 0.15)
        a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, p["glow"], 0.40)
        a.put(layer, trunk_mask, mix(p["trunk"], p["near"], 0.40))
        rings = np.clip(1.0 - np.abs(((a.v * 300.0) % 1.0) - 0.5) / 0.15, 0.0, 1.0)
        a.shade(layer, trunk_mask * rings, 0.20)
        a.put(layer, crown_mask, mix(p["palm"], p["near"], 0.35))
        a.put(layer, banana_mask, mix(p["banana"], p["near"], 0.30))
        greens = np.maximum(crown_mask, banana_mask)
        a.light(layer, a.rim(greens, 0.003, 0.003, 0.4) * greens, mix(p["palm_light"], p["glow"], 0.2), 0.45)
        a.light(layer, a.rim(trunk_mask, 0.003, 0.0, 0.3) * trunk_mask, p["glow"], 0.35)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.20)
        haze(a, layer, p["low"], 0.06, None)
        return layer
    layer = _air(a, p, "austronesia sea air", p["low"], 0.16, scale(p["top"], 0.4), 0.18)
    a.put(layer, shafts(a, "austronesia shafts", 3, 0.16, 0.0, 0.80, 0.04), p["glow"], 0.07)
    return layer


def austronesia_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """The fronds of a coconut palm that hang into the top of the view at
    one place, and blades of beach grass that stand from below at two
    places."""
    del layer_lights
    rng = art_.rand("austronesia foreground")
    u0 = rng.uniform(0.15, 0.35)
    for j in range(3):
        start = (u0 + (j - 1) * 0.03, 0.0)
        end = (start[0] + (j - 1) * 0.09 + rng.uniform(-0.02, 0.02), 0.386 - rng.uniform(0.0, 0.01))
        ctrl = ((start[0] + end[0]) * 0.5 + (j - 1) * 0.04, 0.20)
        rib = _arch(start, ctrl, end, 20)
        pen.line(rib, 0.0026)
        for i, (x, y) in enumerate(rib[1:], 1):
            t = i / 20.0
            side = 0.026 * (1.0 - t * 0.5)
            if y + side * 0.9 > 0.392:
                side = max(0.0, (0.392 - y) / 0.9)
            pen.line([(x, y), (x + side * 0.45, y + side * 0.9)], 0.0015)
            pen.line([(x, y), (x - side * 0.45, y + side * 0.9)], 0.0015)
    for k in range(2):
        u1 = rng.uniform(0.55, 0.95) if k else rng.uniform(0.40, 0.50)
        for _ in range(9):
            u = u1 + rng.uniform(-0.012, 0.012)
            top = REST_BOTTOM - rng.uniform(-0.004, 0.010)
            lean = rng.uniform(-0.05, 0.05)
            pen.line(_arch((u, 1.0), (u + lean * 0.3, top + 0.10), (u + lean, top), 10), 0.0016)


# ---------------------------------------------------------------------------
# The Red River: the delta of Dong Son
# ---------------------------------------------------------------------------


RED_RIVER = {
    "top": (120, 146, 168),
    "mid": (186, 200, 206),
    "low": (232, 230, 220),
    "glow": (255, 238, 210),
    "sun": (255, 248, 230),
    "mist": (206, 216, 222),
    "hills": (86, 112, 128),
    "hills_green": (78, 112, 86),
    "karst": (170, 178, 180),
    "karst_light": (220, 226, 226),
    "forest": (70, 104, 80),
    "forest_light": (122, 152, 104),
    "river": (150, 112, 74),
    "river_light": (204, 170, 128),
    "water": (176, 194, 204),
    "water_light": (236, 238, 232),
    "dike": (102, 140, 64),
    "dike_light": (164, 186, 96),
    "rice": (126, 166, 72),
    "thatch": (166, 132, 82),
    "bamboo": (150, 140, 88),
    "bamboo_leaf": (92, 128, 70),
    "wood": (110, 80, 56),
    "egret": (250, 250, 246),
    "egret_legs": (60, 54, 50),
    "far": (196, 206, 210),
    "near": (36, 42, 32),
    "near_light": (130, 120, 90),
    "clay": (150, 112, 80),
    "reed": (150, 150, 92),
}


def history_red_river(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = RED_RIVER
    sun_at = (0.64, 0.32)
    bank_v = HORIZON + 0.004
    paddy_v = HORIZON + 0.036
    if layer_key == "sky":
        # A soft, misty sky, and the limestone hills of the delta in layers
        # of blue mist: each row paler and bluer than the row in front.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.9)), (0.26, p["top"]), (0.46, p["mid"]), (HORIZON - 0.01, p["low"]),
                                 (HORIZON + 0.002, p["mist"]), (1.0, p["mist"])]))
        _sun(a, layer, *sun_at, 0.022, p["sun"], p["glow"], 0.45)
        a.tint(layer, fog(a, "red river high haze", 0.30, 0.10, 2.0), p["mid"], 0.30)
        rng = a.rand("red river hills")
        rows = ((22, HORIZON + 0.004, 0.06, 0.12, 0.016, 0.030, 0.72), (16, HORIZON + 0.006, 0.07, 0.16, 0.018, 0.036, 0.52),
                (10, HORIZON + 0.008, 0.06, 0.18, 0.020, 0.040, 0.32))
        for k, (count, base, hmin, hmax, wmin, wmax, pale) in enumerate(rows):
            towers, pen = a.drawing()
            for _ in range(count):
                u = rng.uniform(-0.04, 1.04)
                # The tall towers stand at the two sides; the middle has low
                # humps, so the sky over the river stays open.
                side = 0.4 + 0.6 * abs(u - 0.45) / 0.55
                _karst(pen, rng, u, base, rng.uniform(wmin, wmax), rng.uniform(hmin, hmax) * side, rng.uniform(-0.3, 0.3))
            mask = a.mask_of(towers, blur=0.8)
            colour = mix(p["hills"], p["mist"], pale)
            a.put(layer, mask, a.ramp([(0.0, colour), (base - 0.12, colour), (base, mix(colour, p["mist"], 0.7)), (1.0, colour)]))
            a.light(layer, a.rim(mask, -0.010, 0.0, 2.0) * mask, mix(p["karst_light"], p["glow"], 0.3), 0.30 * (1.0 - pale))
            green = mask * smoothstep(0.42, 0.58, a.blur(a.rim(mask, 0.0, 0.02), 6.0) * 1.6 + (a.noise(("red river hill green", k), cells=50.0, octaves=3) - 0.5) * 0.5)
            a.put(layer, green, mix(p["hills_green"], p["mist"], pale), 0.6)
            a.tint(layer, mask * fog(a, ("red river mist", k), base - 0.03 + k * 0.01, 0.025, 3.0), p["mist"], 0.75)
        # Two egrets in flight over the plain.
        birds, bird_pen = a.drawing()
        for u, v, s, beat in ((0.30, 0.44, 0.012, 0.6), (0.34, 0.455, 0.010, -0.4), (0.82, 0.48, 0.009, 0.2)):
            _egret_flying(bird_pen, u, v, s, beat, 1.0)
        a.put(layer, a.mask_of(birds, blur=0.3), p["egret"], 0.95)
        _textbook(a, layer, 0.08)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far red river")
        # The far bank and the wide brown river, then the near bank and the
        # paddies down to the eye.
        _, far_line = a.ridge("red river far bank", bank_v, 0.002, cells=4.0, octaves=2)
        far_bank = _land(a, far_line)
        river = smoothstep(bank_v + 0.004, bank_v + 0.006, a.v) * smoothstep(paddy_v + 0.0005, paddy_v - 0.0015, a.v)
        groves, grove_pen = a.drawing()
        leaves, leaf_pen = a.drawing()
        houses = {key: a.drawing() for key in ("posts", "walls", "roof")}
        # Bamboo groves and the stilt houses of a village on the far bank.
        for u in (0.05, 0.12, 0.40, 0.48, 0.70, 0.78, 0.92):
            _bamboo(grove_pen, leaf_pen, rng, u, bank_v + 0.006, rng.uniform(0.020, 0.032), 7)
        for u, w in ((0.09, 0.008), (0.44, 0.007), (0.74, 0.009), (0.86, 0.007)):
            _house_on_posts(houses["posts"][1], houses["walls"][1], houses["roof"][1], u, bank_v + 0.006, w, w * 1.7, saddle=True)
        # Larger houses on a raised mound by the near bank at the left, with
        # bamboo behind them.
        mound, mound_pen = a.drawing()
        mound_pen.poly([(-0.01, paddy_v + 0.014)] + [(x, paddy_v - 0.003 - 0.002 * np.sin(np.pi * x / 0.30)) for x in np.linspace(0.0, 0.28, 12)]
                       + [(0.31, paddy_v + 0.004), (0.30, paddy_v + 0.012), (0.20, paddy_v + 0.015)])
        for u, h in ((0.03, 0.06), (0.25, 0.05)):
            _bamboo(grove_pen, leaf_pen, rng, u, paddy_v + 0.004, h, 9)
        for u, w in ((0.09, 0.022), (0.18, 0.018)):
            _house_on_posts(houses["posts"][1], houses["walls"][1], houses["roof"][1], u, paddy_v + 0.010, w, w * 1.7, saddle=True)
        # The paddies: rows of flat water, each row deeper toward the eye,
        # split by dikes. The dikes across go to a point far off, as lines in
        # perspective do.
        dikes, dike_pen = a.drawing()
        young, young_pen = a.drawing()
        deep, deep_pen = a.drawing()
        vp = (0.55, HORIZON - 0.12)
        v, gap = paddy_v + 0.003, 0.004
        while v < 1.0:
            width = 0.0012 + (v - HORIZON) * 0.016
            dike_pen.line([(-0.02, v), (1.02, v)], width)
            x = rng.uniform(-0.10, 0.0)
            while x < 1.05:
                y0, y1 = v, v + gap

                def at(y: float, x0: float = x) -> float:
                    return vp[0] + (x0 - vp[0]) * (y - vp[1]) / (v - vp[1])

                dike_pen.line([(x, y0), (at(y1), y1)], width * 0.8)
                length = rng.uniform(0.05, 0.12) * (1.0 + (v - HORIZON) * 5.0)
                # Some paddies are green with young rice; some are deep water
                # that shows the blue of the high sky; the rest are bright.
                quad = [(x, y0), (x + length, y0), (at(y1, x + length), y1), (at(y1), y1)]
                roll = rng.random()
                if roll < 0.30:
                    young_pen.poly(quad)
                elif roll < 0.55:
                    deep_pen.poly(quad)
                x += length
            v += gap
            gap *= 1.30
        egrets, egret_pen = a.drawing()
        legs, leg_pen = a.drawing()
        for _ in range(12):
            u = rng.uniform(0.30, 0.98)
            v = rng.uniform(paddy_v + 0.010, 0.70)
            s = 0.010 + (v - HORIZON) * 0.14
            _egret(egret_pen, u, v, s, rng.choice((-1.0, 1.0)))
            leg_pen.line([(u, v - s * 0.45), (u + s * 0.04, v)], s * 0.04)
        # Two long dugout boats on the river, each with a low cover of
        # woven bamboo over its middle.
        boats, boat_pen = a.drawing()
        for u, v, s in ((0.36, bank_v + 0.020, 0.040), (0.66, bank_v + 0.014, 0.030)):
            boat_pen.poly([(u - s * 0.55, v - s * 0.08), (u - s * 0.40, v), (u + s * 0.40, v), (u + s * 0.55, v - s * 0.09), (u + s * 0.40, v - s * 0.05), (u - s * 0.40, v - s * 0.05)])
            boat_pen.ellipse(u, v - s * 0.06, s * 0.16, s * 0.09)
        paddies = smoothstep(paddy_v - 0.0005, paddy_v + 0.0015, a.v)
        mound_mask = a.mask_of(mound)
        house_masks = {key: a.mask_of(img) for key, (img, _) in houses.items()}
        grove_mask = np.maximum(a.mask_of(groves), a.mask_of(leaves))
        mask = np.maximum.reduce([far_bank, grove_mask, *house_masks.values()])
        layer = solid(a, mask, mix(p["dike"], p["far"], 0.45), mix(p["dike"], p["far"], 0.15), HORIZON, 0.70, "red river far", 0.04)
        # The river: wide and brown with silt, lit in long lines.
        a.put(layer, river, a.ramp([(0.0, mix(p["river"], p["mist"], 0.45)), (bank_v + 0.006, mix(p["river"], p["mist"], 0.45)), (paddy_v, p["river"]), (1.0, p["river"])]))
        a.light(layer, river * smoothstep(0.50, 0.72, a.noise("red river current", cells=50.0, octaves=2, stretch=20.0)), p["river_light"], 0.70)
        a.light(layer, river * smoothstep(0.70, 0.85, a.noise("red river ripples", cells=120.0, octaves=1, stretch=8.0)), p["water_light"], 0.45)
        a.shade(layer, river * a.band(paddy_v - 0.002, 0.004, 1.0), 0.25)
        boat_mask = a.mask_of(boats)
        a.put(layer, a.shift(boat_mask, 0.0, 0.004) * river * (1.0 - boat_mask), mix(p["wood"], p["river"], 0.5), 0.5)
        a.put(layer, boat_mask, mix(p["wood"], p["far"], 0.20))
        a.light(layer, river * a.spot(sun_at[0], bank_v + 0.012, 0.25, 1.0, squash=3.0), p["glow"], 0.35)
        # The paddies: water like a mirror of the sky. The far water shows
        # the low pale sky, the near water the higher blue.
        mirror = a.ramp([(0.0, p["water_light"]), (paddy_v, mix(p["water_light"], p["water"], 0.5)), (0.68, p["water"]), (1.0, mix(p["water"], p["top"], 0.5))])
        a.put(layer, paddies, mirror)
        a.put(layer, a.mask_of(deep) * paddies, mix(p["water"], p["top"], 0.55), 0.8)
        a.light(layer, paddies * smoothstep(0.62, 0.82, a.noise("red river paddy glints", cells=70.0, octaves=2, stretch=10.0)), p["water_light"], 0.5)
        shoots = 0.75 + 0.25 * smoothstep(0.3, 0.7, a.noise("red river shoots", cells=300.0, octaves=1, stretch=0.2))
        a.put(layer, a.mask_of(young) * paddies * shoots, mix(p["rice"], p["water"], 0.25), 0.80)
        dike_mask = a.mask_of(dikes) * paddies
        a.put(layer, dike_mask, p["dike"])
        a.light(layer, a.rim(dike_mask, 0.0, 0.0015, 0.0) * dike_mask, p["dike_light"], 0.6)
        a.put(layer, mound_mask, mix(p["dike"], p["far"], 0.25))
        a.light(layer, a.rim(mound_mask, 0.0, 0.002, 0.3) * mound_mask, p["dike_light"], 0.5)
        # The groves and the houses.
        a.put(layer, a.mask_of(groves), mix(p["bamboo"], p["far"], 0.30))
        a.put(layer, a.mask_of(leaves), mix(p["bamboo_leaf"], p["far"], 0.30))
        a.light(layer, a.rim(a.mask_of(leaves), 0.002, 0.002, 0.3) * a.mask_of(leaves), p["forest_light"], 0.35)
        a.put(layer, house_masks["walls"], mix(p["bamboo"], p["wood"], 0.45))
        roof = house_masks["roof"]
        # The roof: thatch lit at its top and dark at the eaves, and its
        # shade on the wall under it.
        a.put(layer, a.shift(roof, 0.0, 0.003) * house_masks["walls"] * (1.0 - roof), p["wood"], 0.6)
        a.put(layer, roof, a.ramp([(0.0, mix(p["thatch"], p["glow"], 0.25)), (paddy_v - 0.03, mix(p["thatch"], p["glow"], 0.25)), (paddy_v, p["thatch"]), (1.0, p["thatch"])]))
        a.shade(layer, roof * smoothstep(0.3, 0.9, a.noise("red river thatch", cells=220.0, octaves=1, stretch=0.12)), 0.14)
        a.shade(layer, a.rim(roof, 0.0, -0.004, 0.2) * roof, 0.45)
        a.put(layer, house_masks["posts"], p["wood"])
        # The egrets in the water, each with its reflection under it.
        egret_mask = a.mask_of(egrets)
        a.put(layer, a.shift(egret_mask, 0.0, 0.010) * paddies * (1.0 - egret_mask), p["water_light"], 0.5)
        a.put(layer, a.mask_of(legs) * paddies, p["egret_legs"], 0.8)
        a.put(layer, egret_mask, p["egret"])
        a.tint(layer, fog(a, "red river bank mist", bank_v + 0.002, 0.012, 3.0), p["mist"], 0.45)
        haze(a, layer, p["low"], 0.06, None)
        mask = np.maximum.reduce([mask, river, paddies, mound_mask, boat_mask])
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near red river")
        bank, bank_pen = a.drawing()
        culms, culm_pen = a.drawing()
        leaves, leaf_pen = a.drawing()
        reeds, reed_pen = a.drawing()
        ground, line = a.ridge("near red river", 0.705, 0.004, cells=4.0, octaves=3)
        pts = [(u, _at(line, u) - 0.030 * smoothstep(0.26, 0.02, u) - 0.028 * smoothstep(0.76, 0.98, u)) for u in np.linspace(0.0, 1.0, 60)]
        bank_pen.poly([(0.0, 1.0)] + pts + [(1.0, 1.0)])

        def bank_at(u: float) -> float:
            return float(np.interp(u, [q[0] for q in pts], [q[1] for q in pts]))

        # A clump of bamboo at the left; reeds and tufts of young rice at
        # the right. The top of the dike in the middle is calm.
        _bamboo(culm_pen, leaf_pen, rng, 0.07, bank_at(0.07) + 0.006, 0.40, 13)
        for u, h in ((0.80, 0.060), (0.88, 0.080), (0.96, 0.070)):
            for _ in range(14):
                x = u + rng.uniform(-0.015, 0.015)
                lean = rng.uniform(-0.03, 0.03)
                top = (x + lean, bank_at(u) - h * rng.uniform(0.7, 1.0))
                reed_pen.line(_arch((x, bank_at(u) + 0.004), (x + lean * 0.2, top[1] + h * 0.5), top, 8), 0.0016)
                reed_pen.ellipse(top[0], top[1] - 0.004, 0.0022, 0.007)
        for _ in range(26):
            u = rng.uniform(0.22, 0.76)
            base = bank_at(u) + 0.002
            for j in range(5):
                lean = (j - 2) * 0.004 + rng.uniform(-0.002, 0.002)
                reed_pen.line([(u, base), (u + lean * 0.4, base - 0.006), (u + lean, base - rng.uniform(0.010, 0.016))], 0.0010)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        culm_mask = a.mask_of(culms)
        leaf_mask = a.mask_of(leaves)
        reed_mask = a.mask_of(reeds)
        mask = np.maximum.reduce([bank_mask, culm_mask, leaf_mask, reed_mask])
        layer = a.blank()
        earth = a.ramp([(0.0, mix(p["clay"], p["near"], 0.30)), (0.66, mix(p["clay"], p["near"], 0.30)), (0.80, mix(p["clay"], p["near"], 0.72)), (1.0, p["near"])])
        a.put(layer, bank_mask, earth)
        a.put(layer, bank_mask * a.band(_at(line, 0.5) + 0.004, 0.006, 1.0), mix(p["dike"], p["near"], 0.35), 0.8)
        a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, p["glow"], 0.30)
        a.put(layer, culm_mask, mix(p["bamboo"], p["near"], 0.35))
        joints = np.clip(1.0 - np.abs(((a.v * 160.0) % 1.0) - 0.5) / 0.06, 0.0, 1.0)
        a.shade(layer, culm_mask * joints, 0.35)
        a.put(layer, leaf_mask, mix(p["bamboo_leaf"], p["near"], 0.30))
        a.light(layer, a.rim(leaf_mask, 0.002, 0.002, 0.3) * leaf_mask, p["forest_light"], 0.35)
        a.put(layer, reed_mask, mix(p["reed"], p["near"], 0.35))
        a.light(layer, a.rim(reed_mask, 0.0015, 0.0, 0.2) * reed_mask, p["glow"], 0.30)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.20)
        haze(a, layer, p["mist"], 0.10, None)
        return layer
    layer = _air(a, p, "red river mist", p["mist"], 0.30, p["near"], 0.18)
    a.put(layer, shafts(a, "red river shafts", 3, -0.12, 0.0, 0.85, 0.06), p["glow"], 0.06)
    return layer


def red_river_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Stalks of rice with heavy heads that bend over stand from below at
    two places, and a spray of bamboo leaves hangs from above at one place."""
    del layer_lights
    rng = art_.rand("red river foreground")
    for k in range(2):
        u0 = (k + rng.uniform(0.2, 0.8)) / 2.0
        for _ in range(12):
            u = u0 + rng.uniform(-0.014, 0.014)
            top = REST_BOTTOM - rng.uniform(-0.004, 0.010)
            lean = rng.uniform(-0.03, 0.03)
            stalk = _arch((u, 1.0), (u + lean * 0.3, top + 0.10), (u + lean, top), 10)
            pen.line(stalk, 0.0014)
            x, y = stalk[-1]
            droop = 1.0 if lean >= 0 else -1.0
            head = _arch((x, y), (x + droop * 0.012, y - 0.004), (x + droop * 0.020, y + 0.012), 6)
            pen.line(head, 0.0018)
            for hx, hy in head[1:]:
                pen.ellipse(hx, hy, 0.0016, 0.0024)
    u = rng.uniform(0.30, 0.60)
    culm = _arch((u - 0.05, 0.0), (u, 0.18), (u + 0.08, 0.30), 12)
    pen.line(culm, 0.0028)
    for i, (x, y) in enumerate(culm[3:], 3):
        for s in (-1.0, 1.0):
            length = rng.uniform(0.030, 0.045)
            tip = (x + s * length * 0.6, min(0.384, y + length))
            _leaf(pen, [(x, y), ((x + tip[0]) * 0.5 + s * 0.004, (y + tip[1]) * 0.5), tip], 0.0035, 0.5)
