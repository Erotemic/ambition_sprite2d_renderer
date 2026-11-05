"""The scenes of the History dimension: Australia and Aotearoa.

The History dimension is a grid. East is later, and each floor is a region
of the world. These rooms are on the floor of Oceania. They show Lake Mungo
in the Willandra Lakes when its water was full; the coast of the North
Island of Aotearoa a few generations after the first waka came; Tongatapu
in the time of the Tuʻi Tonga; the Bay of Islands on the day of the Treaty
of Waitangi; and Warrane, Sydney Cove, when the First Fleet came. They use
the same sepia of an old textbook and the same rules as `history_eras.py`
and `history_americas_pacific.py`. The people of these places show skill,
learning and courage of their own; nothing here is a joke on them.

- ``history_willandra`` (Lake Mungo, south-west New South Wales, about
  40,000 years ago). A huge clear sky, deep blue at its top and pale at the
  horizon, and a hot high sun. The flat pale bed of the lake with round
  saltbush and bluebush in it, and emus far off. Along the far shore the
  lunette, the "Walls of China": a long crescent dune that wind and rain cut
  into fluted spires, gullies and small flat-topped mesas, in bands of grey
  clay, pink-orange, cream and white sand. At the left, on the horizon, the
  full lake of that time, with river red gums on its far shore. No building
  and no grave is shown.
- ``history_aotearoa`` (the North Island coast, about 1400). A fresh clear
  morning. At the left a coast of forest with tall kauri over it, and
  pōhutukawa red with flowers along the beach, with waka pulled up on the
  sand. At the right a headland with a pā: terraces cut into the hill,
  palisades of plain posts on their edges, and houses with steep roofs of
  thatch on the top. Islands far off and the blue-green sea. No carving
  is shown.
- ``history_tonga`` (Tongatapu, about 1200). A bright day of the trade wind
  with tall white heap clouds. A flat coral island across a calm turquoise
  lagoon: a long low line of coconut palms and pandanus, fale with domed
  roofs of thatch, and among the palms the Haʻamonga ʻa Maui, two tall
  uprights of grey coral limestone with a lintel set into their tops. A
  kalia, the great double-hulled canoe, on the lagoon, and the white line
  of surf on the reef far out.
- ``history_waitangi`` (the Bay of Islands, 6 February 1840). A summer day.
  At the right, on the lawn over the beach, the house of James Busby (white
  weatherboard, a hipped roof and a verandah), a large marquee of ship's
  sails in front of it, a crowd far off, and waka on the beach. Ships at
  anchor in the bay with their sails furled, wooded islands, and across
  the bay the houses of Kororāreka with a flagstaff on Maiki Hill over it.
- ``history_sydney_cove`` (Warrane, Sydney Cove, 1788). A sober scene: a
  quiet evening of soft overcast, muted and warm low down. A narrow cove
  between two headlands of Hawkesbury sandstone in level ledges, with gums
  and scrub on them. The ships of the First Fleet at anchor with their
  sails furled; a few small plain tents of the new camp by a stream at the
  right; the thin smoke of the fires of the Eora on the far shore, and two
  bark canoes on the water, each with its small fire.

No picture here shows a deity, a religious sign, a carved figure, a church,
a cross, a grave or rock art. No person in these pictures is harmed, and no
one carries a weapon. No flag carries a sign.

The bright detail is far off or at the edges, and the middle of each near
layer is calm, so the play in front of it reads. The things that drift in the
air are the room's motes (`terrain/motes.py`), not part of these pictures.
"""

from __future__ import annotations

import math

import numpy as np

from .artkit import Art, Pen, mix, polar, scale, smoothstep
from .history_americas_pacific import _coconut_palm, _outrigger, _pandanus, _voyaging_canoe
from .history_central_africa import _person
from .history_east_asia_coast import _bank, _grass_blades, _reflected
from .history_eras import REST_BOTTOM, _air, _heaps, _plume, _sun, _tall_ship, _textbook
from .history_origins import _arch, _gum, _land, _leaf, _tree_fern
from .parts import HORIZON, cloud_mask, fog, haze, shafts, solid

# ---------------------------------------------------------------------------
# Parts that more than one room has
# ---------------------------------------------------------------------------


def _shrub(pen: Pen, rng, u: float, v: float, w: float, h: float, lumps: int = 9) -> None:
    """A low round shrub of the dry country, as saltbush and bluebush grow:
    a mound of small round lumps of grey leaves, wider than it is high, on
    the ground at `(u, v)`."""
    pen.ellipse(u, v - h * 0.40, w * 0.80, h * 0.45)
    for _ in range(lumps):
        t = rng.uniform(-1.0, 1.0)
        top = h * (1.0 - 0.45 * t * t)
        pen.ellipse(u + t * w * 0.75, v - top * rng.uniform(0.45, 0.75), w * rng.uniform(0.22, 0.34), h * rng.uniform(0.25, 0.38))


def _emu(pen: Pen, u: float, v: float, s: float, facing: float = 1.0, graze: bool = False) -> None:
    """An emu far off: a round body of shaggy feathers that hang, a long
    thin neck, a small head, and two long legs. `(u, v)` is the feet and
    `s` the height of the back."""
    f = facing
    pen.ellipse(u, v - s * 0.78, s * 0.42, s * 0.26)
    pen.poly([(u - f * s * 0.44, v - s * 0.74), (u + f * s * 0.30, v - s * 0.70), (u + f * s * 0.20, v - s * 0.56), (u - f * s * 0.36, v - s * 0.58)])
    if graze:
        pen.line([(u + f * s * 0.30, v - s * 0.84), (u + f * s * 0.52, v - s * 0.60), (u + f * s * 0.60, v - s * 0.30)], s * 0.07)
        pen.ellipse(u + f * s * 0.62, v - s * 0.26, s * 0.07, s * 0.05)
    else:
        pen.line([(u + f * s * 0.30, v - s * 0.86), (u + f * s * 0.40, v - s * 1.20), (u + f * s * 0.38, v - s * 1.46)], s * 0.07)
        pen.ellipse(u + f * s * 0.42, v - s * 1.48, s * 0.08, s * 0.05)
    for du, lean in ((-0.06, -0.05), (0.08, 0.06)):
        pen.line([(u + f * s * du, v - s * 0.58), (u + f * s * (du + lean), v - s * 0.28), (u + f * s * du, v)], s * 0.05)


def _flax(pen: Pen, rng, u: float, v: float, h: float, blades: int = 13, stalks: int = 2) -> None:
    """A clump of harakeke, the flax of Aotearoa: long stiff blades like
    swords that fan out from one base, their tips bent over, and a few tall
    dark flower stalks over them."""
    for k in range(blades):
        ang = -90.0 + (k / (blades - 1) - 0.5) * 120.0 + rng.uniform(-6.0, 6.0)
        length = h * rng.uniform(0.6, 1.0) * (1.0 - 0.3 * abs(k / (blades - 1) - 0.5))
        tip = polar(u, v, length, ang)
        tip = (tip[0], tip[1] + length * 0.18 * abs(math.cos(math.radians(ang))))
        _leaf(pen, _arch((u + (k - blades / 2) * h * 0.004, v + 0.002), polar(u, v, length * 0.6, ang + (4.0 if ang > -90.0 else -4.0)), tip, 8), h * 0.022, 0.3)
    for j in range(stalks):
        x = u + (j - 0.5) * h * 0.18 + rng.uniform(-0.02, 0.02) * h
        top = (x + rng.uniform(-0.05, 0.05) * h, v - h * rng.uniform(1.3, 1.6))
        pen.line([(x, v), top], h * 0.012)
        for i in range(4):
            t = 0.55 + i * 0.12
            px, py = x + (top[0] - x) * t, v + (top[1] - v) * t
            side = 1.0 if i % 2 else -1.0
            pen.line([(px, py), (px + side * h * 0.05, py - h * 0.03)], h * 0.008)


def _nikau(trunk: Pen, crown: Pen, rng, u: float, v: float, h: float, lean: float = 0.0) -> None:
    """A nīkau palm: a slim grey trunk in rings, a smooth green bulge of a
    crown shaft on its top, and a tuft of stiff fronds that point up and
    out, like a feather duster."""
    w = h * 0.030
    pts = [(u + lean * t * t, v + 0.006 - (h * 0.70 + 0.006) * t) for t in np.linspace(0.0, 1.0, 9)]
    trunk.line(pts, w)
    top = pts[-1]
    crown.ellipse(top[0], top[1] - h * 0.05, w * 1.15, h * 0.07)
    head = (top[0], top[1] - h * 0.11)
    for k in range(9):
        ang = -90.0 + (k - 4) * 19.0 + rng.uniform(-5.0, 5.0)
        length = h * rng.uniform(0.28, 0.34)
        tip = polar(*head, length, ang)
        tip = (tip[0], tip[1] + length * 0.35 * abs(k - 4) / 4.0)
        rib = _arch(head, polar(*head, length * 0.6, ang), tip, 8)
        crown.line(rib, w * 0.35)
        for x, y in rib[2:]:
            side = h * 0.045
            crown.line([(x, y), (x + side * 0.7, y + side * 0.6)], w * 0.22)
            crown.line([(x, y), (x - side * 0.7, y + side * 0.6)], w * 0.22)


def _waka(hull: Pen, u: float, v: float, s: float, facing: float = 1.0) -> None:
    """A waka pulled up on the beach: one long plain dugout hull with a low
    raised bow and stern and a thin top strake. No carving."""
    f = facing
    hull.poly([(u - f * s * 0.50, v - s * 0.09), (u - f * s * 0.42, v - s * 0.06), (u + f * s * 0.40, v - s * 0.06), (u + f * s * 0.52, v - s * 0.11),
               (u + f * s * 0.42, v), (u - f * s * 0.42, v)])


# ---------------------------------------------------------------------------
# Willandra: Lake Mungo, about 40,000 years ago
# ---------------------------------------------------------------------------


WILLANDRA = {
    "top": (46, 92, 164),
    "mid": (140, 178, 212),
    "low": (238, 232, 216),
    "glow": (255, 238, 196),
    "sun": (255, 250, 232),
    "cloud": (250, 248, 240),
    "cloud_shadow": (196, 196, 196),
    "white": (246, 240, 228),
    "cream": (234, 214, 176),
    "pink": (226, 166, 128),
    "orange": (206, 130, 86),
    "clay": (152, 148, 140),
    "bed": (218, 204, 172),
    "bed_dark": (176, 160, 128),
    "saltbush": (126, 140, 112),
    "bluebush": (122, 146, 150),
    "lake": (150, 184, 198),
    "gum": (226, 218, 200),
    "leaf": (110, 126, 98),
    "emu": (74, 62, 54),
    "far": (232, 226, 212),
    "near": (48, 38, 30),
    "near_light": (210, 176, 132),
}

#: The foot of the lunette, where it meets the dry bed of the lake.
WILLANDRA_FOOT = 0.616


def _lunette_top(u: float) -> float:
    """The crest of the lunette, the long dune of the east shore: it rises
    from the bed of the lake at the left, runs high along the middle and
    the right, and falls a little at the far end of its crescent."""
    return float(np.interp(u, [0.18, 0.28, 0.40, 0.62, 0.84, 1.05], [WILLANDRA_FOOT, 0.580, 0.552, 0.544, 0.550, 0.562]))


def _lunette_bands(a: Art, foot: float, crest: np.ndarray, p: dict) -> np.ndarray:
    """The paint of the face of the lunette: level bands of grey clay at
    the foot, then pink-orange, cream and white sand to the crest, each
    band a little wavy."""
    height = np.maximum(foot - crest[None, :], 0.004)
    t = np.clip((foot - a.v) / height, 0.0, 1.5) + (a.noise("mungo band waves", cells=12.0, octaves=3, stretch=5.0) - 0.5) * 0.12
    stops = [(0.0, p["clay"]), (0.09, mix(p["clay"], p["pink"], 0.25)), (0.14, p["orange"]), (0.24, p["pink"]), (0.32, mix(p["pink"], p["cream"], 0.5)),
             (0.40, p["cream"]), (0.52, mix(p["cream"], p["white"], 0.6)), (0.66, p["white"]), (1.5, p["white"])]
    out = np.zeros((a.n, a.n, 3), dtype=np.float32)
    for channel in range(3):
        out[:, :, channel] = np.interp(t, [s[0] for s in stops], [s[1][channel] for s in stops])
    return out


def history_willandra(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = WILLANDRA
    sun_at = (0.16, 0.16)
    foot = WILLANDRA_FOOT
    if layer_key == "sky":
        # A huge clear sky of the inland: deep blue at the top, pale at the
        # horizon, a hot high sun, and a few thin streaks of cloud. Under
        # it the flat bed of the dry lake goes to the end of the world.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.86)), (0.22, p["top"]), (0.46, p["mid"]), (HORIZON - 0.006, p["low"]),
                                 (HORIZON + 0.002, mix(p["bed"], p["low"], 0.5)), (0.70, mix(p["bed"], p["low"], 0.25)), (1.0, p["bed"])]))
        a.light(layer, a.spot(*sun_at, 0.34, 2.0, squash=1.2), p["glow"], 0.40)
        _sun(a, layer, *sun_at, 0.020, p["sun"], p["glow"], 0.55)
        streaks = cloud_mask(a, "mungo streaks", 0.36, 0.06, cells=2.6, cover=0.30, soft=0.20, stretch=9.0)
        a.put(layer, streaks, p["cloud"], 0.40)
        _heaps(a, layer, "mungo heaps", ((0.66, HORIZON - 0.03, 0.05, 0.035), (0.88, HORIZON - 0.035, 0.04, 0.025)), p["cloud"], p["cloud_shadow"], 0.55)
        a.tint(layer, fog(a, "mungo heat haze", HORIZON, 0.020, 3.0), p["low"], 0.55)
        _textbook(a, layer, 0.07)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far willandra")
        cols = a.u[0]
        crest_env = np.array([_lunette_top(float(u)) for u in cols], dtype=np.float32)
        # The Walls of China: wind and rain cut the face of the lunette into
        # a row of sharp fluted spires and deep gullies, with a few small
        # flat-topped mesas between them. The low dune behind it is grey
        # with saltbush.
        spires = a.line_noise("mungo spires", cells=60.0, octaves=3)
        peaks = (1.0 - np.abs(spires * 2.0 - 1.0)) ** 2.4
        mesas = smoothstep(0.70, 0.76, a.line_noise("mungo mesas", cells=26.0, octaves=2))
        depth = foot - crest_env
        cut = depth * (0.10 + 0.70 * (1.0 - peaks))
        crest = crest_env + cut * (1.0 - mesas) + depth * 0.40 * mesas
        crest = np.minimum(crest, foot)
        back_line = crest_env + depth * 0.22 + (a.line_noise("mungo back dune", cells=5.0, octaves=3) - 0.5) * 0.006
        back_line = np.where(cols < 0.20, foot + 0.01, back_line)
        back = _land(a, back_line) * (a.v < foot + 0.002)
        face = _land(a, crest) * (a.v < foot + 0.002)
        # Fans of washed sand at the foot of the face.
        apron = np.clip((a.v - (foot - 0.010 * (0.6 + 0.4 * a.noise("mungo apron", cells=20.0, octaves=2)))) / 0.004, 0.0, 1.0) * (a.v < foot + 0.002) * smoothstep(0.20, 0.26, a.u)
        # The flat bed of the lake: saltbush and bluebush in it, emus far
        # off, and at the left, as a memory of 42,000 years ago, the full
        # lake on the horizon with river red gums on its far shore.
        bed = smoothstep(HORIZON - 0.001, HORIZON + 0.003, a.v)
        lake = a.band(HORIZON + 0.004, 0.006, 1.0) * smoothstep(0.34, 0.16, a.u) * (a.v > HORIZON - 0.001)
        gums, gum_pen = a.drawing()
        gum_crowns, gum_crown_pen = a.drawing()
        for u in (0.02, 0.06, 0.11, 0.15, 0.19):
            _gum(gum_pen, gum_crown_pen, rng, u, HORIZON + 0.0005, rng.uniform(0.020, 0.030))
        bushes, bush_pen = a.drawing()
        blues, blue_pen = a.drawing()
        for _ in range(170):
            u = rng.uniform(-0.02, 1.02)
            v = rng.uniform(foot + 0.004, 0.70) if u > 0.22 else rng.uniform(HORIZON + 0.010, 0.70)
            s = 0.0012 + (v - HORIZON) * 0.05
            _shrub(blue_pen if rng.random() < 0.4 else bush_pen, rng, u, v, s * 1.5, s, 6)
        emus, emu_pen = a.drawing()
        for eu, ev, s, f, g in ((0.30, 0.640, 0.012, 1.0, False), (0.33, 0.644, 0.011, 1.0, True), (0.36, 0.638, 0.010, -1.0, False)):
            _emu(emu_pen, eu, ev, s, f, g)
        back_mask = back * (1.0 - face)
        bush_mask = a.mask_of(bushes) * bed
        blue_mask = a.mask_of(blues) * bed
        emu_mask = a.mask_of(emus)
        gum_mask = np.maximum(a.mask_of(gums), a.mask_of(gum_crowns)) * (a.v < HORIZON + 0.001)
        mask = np.maximum.reduce([bed, back, face, gum_mask, emu_mask])
        layer = solid(a, mask, mix(p["bed"], p["far"], 0.30), p["bed"], HORIZON, 0.72, "willandra far", 0.03)
        # The bed: pale, in long faint bands of crust and sand.
        crust = smoothstep(0.55, 0.70, a.noise("mungo crust", cells=30.0, octaves=3, stretch=10.0))
        a.put(layer, bed * crust, mix(p["white"], p["far"], 0.2), 0.35)
        a.put(layer, bed * smoothstep(0.62, 0.74, a.noise("mungo bed dark", cells=24.0, octaves=3, stretch=8.0)), mix(p["bed_dark"], p["far"], 0.3), 0.30)
        a.put(layer, lake, mix(p["lake"], p["far"], 0.30), 0.85)
        a.light(layer, lake * smoothstep(0.6, 0.8, a.noise("mungo old lake", cells=60.0, octaves=2, stretch=10.0)), p["glow"], 0.35)
        a.put(layer, a.mask_of(gum_crowns) * gum_mask, mix(p["leaf"], p["far"], 0.45))
        a.put(layer, a.mask_of(gums) * gum_mask, mix(p["gum"], p["far"], 0.35))
        # The back dune, grey with its low scrub.
        a.put(layer, back_mask, mix(mix(p["cream"], p["saltbush"], 0.45), p["far"], 0.35))
        a.put(layer, back_mask * smoothstep(0.55, 0.70, a.noise("mungo back scrub", cells=120.0, octaves=2)), mix(p["saltbush"], p["far"], 0.30), 0.6)
        # The face: its bands of colour, the flutes the rain cut down it,
        # light on the sides to the sun and shade in the gullies.
        a.put(layer, face, _lunette_bands(a, foot, crest_env, p))
        flutes = a.noise("mungo flutes", cells=160.0, octaves=2, stretch=0.12)
        a.shade(layer, face * smoothstep(0.55, 0.75, flutes), 0.16)
        a.light(layer, face * smoothstep(0.30, 0.15, flutes), p["glow"], 0.20)
        gully = np.clip((crest[None, :] - crest_env[None, :]) / np.maximum(depth[None, :], 0.004), 0.0, 1.0)
        a.shade(layer, face * gully * smoothstep(0.0, 0.5, gully) * 0.8, 0.22)
        a.light(layer, a.rim(face, 0.003, 0.002, 0.3) * face, p["glow"], 0.55)
        a.shade(layer, a.rim(face, -0.003, 0.0, 0.3) * face, 0.22)
        a.put(layer, apron * face, mix(p["cream"], p["far"], 0.15), 0.75)
        a.put(layer, apron * (1.0 - face) * (a.v > crest[None, :]), mix(p["cream"], p["far"], 0.15), 0.75)
        a.put(layer, bush_mask, mix(p["saltbush"], p["far"], 0.25))
        a.put(layer, blue_mask, mix(p["bluebush"], p["far"], 0.25))
        a.light(layer, a.rim(np.maximum(bush_mask, blue_mask), 0.001, 0.001, 0.0) * np.maximum(bush_mask, blue_mask), p["glow"], 0.35)
        a.put(layer, emu_mask, mix(p["emu"], p["far"], 0.30))
        a.tint(layer, fog(a, "mungo shimmer", foot - 0.004, 0.012, 3.0) * mask, p["low"], 0.30)
        haze(a, layer, p["low"], 0.07, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near willandra")
        bank, ground, bank_at = _bank(a, "near willandra", 0.040, 0.060)
        bushes, bush_pen = a.drawing()
        blues, blue_pen = a.drawing()
        spire, spire_pen = a.drawing()
        grass, grass_pen = a.drawing()
        # A low eroded spur of the lunette at the right, with its bands;
        # saltbush and bluebush at the left. The middle is a calm bank of
        # pale sand with a few dry tufts.
        base = bank_at(0.90) + 0.006
        pts = [(0.78, base)]
        for u, top in ((0.795, base - 0.030), (0.805, base - 0.062), (0.812, base - 0.070), (0.822, base - 0.046), (0.832, base - 0.050), (0.842, base - 0.088), (0.850, base - 0.094),
                       (0.860, base - 0.060), (0.872, base - 0.072), (0.880, base - 0.104), (0.888, base - 0.108), (0.897, base - 0.070), (0.912, base - 0.074), (0.926, base - 0.074),
                       (0.936, base - 0.056), (0.948, base - 0.112), (0.958, base - 0.118), (0.968, base - 0.090), (0.985, base - 0.100), (1.02, base - 0.104)):
            pts.append((u, top))
        pts += [(1.02, 1.0), (0.78, 1.0)]
        spire_pen.poly(pts)
        for u, w, h in ((0.03, 0.050, 0.060), (0.10, 0.040, 0.044), (0.17, 0.028, 0.030), (0.73, 0.024, 0.024)):
            _shrub(bush_pen, rng, u, bank_at(u) + 0.004, w, h, 14)
        for u, w, h in ((0.065, 0.034, 0.050), (0.135, 0.022, 0.032)):
            _shrub(blue_pen, rng, u, bank_at(u) + 0.004, w, h, 12)
        for _ in range(14):
            u = rng.uniform(0.24, 0.72)
            _grass_blades(grass_pen, rng, u, bank_at(u) + 0.002, rng.uniform(0.008, 0.014), 7, 0.0012, 0.010)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        spire_mask = a.mask_of(spire) * (1.0 - bank_mask)
        bush_mask = a.mask_of(bushes)
        blue_mask = a.mask_of(blues)
        grass_mask = a.mask_of(grass)
        mask = np.maximum.reduce([bank_mask, spire_mask, bush_mask, blue_mask, grass_mask])
        layer = a.blank()
        sand = a.ramp([(0.0, mix(p["near_light"], p["near"], 0.30)), (0.66, mix(p["near_light"], p["near"], 0.30)), (0.80, mix(p["near_light"], p["near"], 0.70)), (1.0, p["near"])])
        a.put(layer, bank_mask, sand)
        a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, p["glow"], 0.30)
        crest = np.full(a.n, base - 0.12, dtype=np.float32)
        bands = _lunette_bands(a, base, crest, p)
        a.put(layer, spire_mask, bands * 0.62 + np.array(p["near"], dtype=np.float32) * 0.38)
        flutes = a.noise("mungo near flutes", cells=90.0, octaves=2, stretch=0.12)
        a.shade(layer, spire_mask * smoothstep(0.55, 0.75, flutes), 0.20)
        a.light(layer, a.rim(spire_mask, 0.004, 0.002, 0.4) * spire_mask, p["glow"], 0.45)
        a.put(layer, grass_mask, mix(p["cream"], p["near"], 0.45))
        a.put(layer, bush_mask, mix(p["saltbush"], p["near"], 0.40))
        a.put(layer, blue_mask, mix(p["bluebush"], p["near"], 0.38))
        a.light(layer, a.rim(np.maximum(bush_mask, blue_mask), 0.002, 0.003, 0.3) * np.maximum(bush_mask, blue_mask), p["glow"], 0.35)
        a.shade(layer, np.maximum(bush_mask, blue_mask) * smoothstep(0.55, 0.75, a.noise("mungo near leaves", cells=320.0, octaves=1)), 0.12)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.18)
        haze(a, layer, p["low"], 0.08, None)
        return layer
    layer = _air(a, p, "mungo heat shimmer", p["low"], 0.26, scale(p["near"], 0.9), 0.12)
    return layer


def willandra_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Twigs of saltbush, thick with small round grey leaves, stand from
    below at one place, and tufts of dry grass at two others."""
    del layer_lights
    rng = art_.rand("willandra foreground")
    u = rng.uniform(0.14, 0.26)
    top = REST_BOTTOM - 0.006
    for k in range(11):
        t = (k - 5) / 5.0
        tip = (u + t * 0.075 + rng.uniform(-0.006, 0.006), top + 0.040 * t * t + rng.uniform(0.0, 0.010))
        twig = _arch((u + t * 0.008, 1.0), (u + t * 0.030, tip[1] + 0.10), tip, 12)
        pen.line(twig, 0.0016)
        for i, (x0, y0) in enumerate(twig[5:]):
            for side in (-1.0, 1.0):
                pen.ellipse(x0 + side * 0.007, y0 + 0.003 + (i % 2) * 0.004, 0.0065, 0.0040)
    for k in range(2):
        u = 0.48 + k * 0.30 + rng.uniform(-0.04, 0.04)
        _grass_blades(pen, rng, u, 1.0, 1.0 - REST_BOTTOM + 0.006 - k * 0.012, 18, 0.0014, 0.05)


# ---------------------------------------------------------------------------
# Aotearoa: the coast of the North Island, about 1400
# ---------------------------------------------------------------------------


AOTEAROA = {
    "top": (66, 118, 172),
    "mid": (170, 204, 220),
    "low": (232, 238, 228),
    "glow": (255, 240, 204),
    "sun": (255, 250, 236),
    "cloud": (252, 252, 248),
    "cloud_shadow": (166, 182, 196),
    "sea": (60, 132, 142),
    "sea_light": (196, 228, 220),
    "sea_deep": (36, 94, 114),
    "isle": (96, 128, 128),
    "hill": (92, 126, 74),
    "hill_light": (156, 178, 102),
    "forest": (44, 78, 52),
    "forest_light": (100, 132, 78),
    "kauri": (180, 172, 156),
    "pohutukawa": (50, 84, 58),
    "flower": (200, 40, 46),
    "sand": (228, 214, 178),
    "earth": (178, 140, 88),
    "post": (104, 82, 58),
    "thatch": (150, 130, 98),
    "fern": (90, 132, 66),
    "flax": (74, 108, 58),
    "hull": (96, 66, 44),
    "smoke": (226, 226, 220),
    "far": (198, 214, 214),
    "near": (24, 38, 30),
    "near_light": (112, 144, 82),
}

#: The level of the sea at the foot of the far shore.
AOTEAROA_SEA = 0.622


def _kauri(trunk: Pen, crown: Pen, rng, u: float, v: float, h: float) -> None:
    """A kauri: a straight grey trunk like a column, with no branch for most
    of its height, a few great limbs at its top, and a high crown that is
    flat on its top, in clumps of leaves."""
    w = h * 0.05
    top = v - h * 0.62
    trunk.poly([(u - w * 1.15, v + 0.004), (u + w * 1.15, v + 0.004), (u + w * 0.85, top), (u - w * 0.85, top)])
    for k in range(6):
        ang = -160.0 + k * 28.0 + rng.uniform(-6.0, 6.0)
        end = polar(u, top, h * rng.uniform(0.18, 0.26), ang)
        trunk.line([(u, top + h * 0.02), end], w * 0.50)
        for _ in range(4):
            crown.ellipse(end[0] + rng.uniform(-0.07, 0.07) * h, end[1] - rng.uniform(-0.02, 0.05) * h, h * rng.uniform(0.07, 0.11), h * rng.uniform(0.04, 0.06))


def _pohutukawa(trunk: Pen, crown: Pen, flowers: Pen, rng, u: float, v: float, h: float, w: float, lean: float = 0.0) -> None:
    """A pōhutukawa of the coast: two or three crooked trunks that lean out
    from one foot, limbs that spread wide and low, a dense dome of dark
    leaves, and the crimson of its flowers in clusters over the crown."""
    for k in range(3):
        end = (u + lean * w + (k - 1) * w * 0.55, v - h * rng.uniform(0.50, 0.62))
        mid = ((u + end[0]) * 0.5 + (k - 1) * w * 0.12 + rng.uniform(-0.08, 0.08) * w, v - h * rng.uniform(0.22, 0.32))
        foot = (u + (k - 1) * h * 0.03, v + 0.004)
        trunk.line([foot, mid], h * 0.060 * (1.0 - abs(k - 1) * 0.3))
        trunk.line([mid, end], h * 0.040 * (1.0 - abs(k - 1) * 0.3))
        for side in (-1.0, 1.0):
            trunk.line([end, polar(*end, h * 0.12, -90.0 + side * 40.0)], h * 0.018)
    for _ in range(int(120 * w / h) + 60):
        t = rng.uniform(-1.0, 1.0)
        cu = u + lean * w + t * w
        cv = v - h * (0.44 + 0.44 * (1.0 - t * t) * rng.uniform(0.0, 1.0) ** 0.6)
        crown.ellipse(cu, cv, h * rng.uniform(0.06, 0.10), h * rng.uniform(0.04, 0.07))
    for _ in range(int(180 * w / h) + 60):
        t = rng.uniform(-0.9, 0.9)
        cu = u + lean * w + t * w
        cv = v - h * (0.46 + 0.42 * (1.0 - t * t) * rng.uniform(0.1, 1.0))
        flowers.ellipse(cu, cv, h * rng.uniform(0.010, 0.020), h * rng.uniform(0.008, 0.014))


def _pa_hill(u: float) -> float:
    """The top of the headland at the right where the pā stands: it rises
    from the sea, and its top is cut into flat terraces with steep faces
    between them."""
    smooth = float(np.interp(u, [0.56, 0.62, 0.70, 0.78, 0.86, 0.94, 1.04], [AOTEAROA_SEA + 0.004, 0.590, 0.548, 0.520, 0.514, 0.528, 0.540]))
    step = 0.016
    if smooth > 0.575:
        return smooth
    stepped = 0.514 + math.ceil((smooth - 0.514) / step - 0.25) * step
    return smooth + (stepped - smooth) * 0.75


def _whare(walls: Pen, roof: Pen, u: float, v: float, w: float, h: float) -> None:
    """A whare far off: a low wall, and a steep roof of thatch in two slopes
    that comes down almost to the ground, with a porch at its front."""
    walls.rect(u - w, v - h * 0.35, u + w, v + 0.001)
    roof.poly([(u - w * 1.25, v - h * 0.25), (u, v - h * 1.25), (u + w * 1.25, v - h * 0.25)])


def history_aotearoa(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = AOTEAROA
    sun_at = (0.80, 0.22)
    sea_v = AOTEAROA_SEA
    if layer_key == "sky":
        # A fresh clear morning: a few heap clouds, islands and headlands
        # far off, blue with distance, and the blue-green sea.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.88)), (0.24, p["top"]), (0.48, p["mid"]), (HORIZON - 0.004, p["low"]),
                                 (HORIZON + 0.002, mix(p["sea_light"], p["low"], 0.40)), (0.66, mix(p["sea"], p["sea_light"], 0.40)), (1.0, p["sea"])]))
        _sun(a, layer, *sun_at, 0.020, p["sun"], p["glow"], 0.45)
        _heaps(a, layer, "aotearoa heaps", ((0.16, 0.44, 0.06, 0.08), (0.40, 0.40, 0.08, 0.11), (0.62, 0.47, 0.05, 0.06), (0.96, 0.44, 0.06, 0.08)), p["cloud"], p["cloud_shadow"], 0.85)
        isles, _ = a.ridge("aotearoa isles", HORIZON - 0.008, 0.010, cells=5.0, octaves=4, sharp=0.3)
        isles = isles * (a.v < HORIZON + 0.001) * smoothstep(0.26, 0.34, a.u) * smoothstep(0.66, 0.56, a.u)
        a.put(layer, isles, mix(p["isle"], p["low"], 0.50))
        a.light(layer, a.rim(isles, 0.0, 0.003, 0.3) * isles, p["glow"], 0.30)
        lines = smoothstep(0.62, 0.82, a.noise("aotearoa swell lines", cells=60.0, octaves=2, stretch=14.0))
        a.light(layer, (a.v > HORIZON + 0.002) * lines, p["sea_light"], 0.30)
        glints = smoothstep(0.64, 0.84, a.noise("aotearoa glints", cells=90.0, octaves=2, stretch=8.0))
        a.light(layer, (a.v > HORIZON + 0.002) * glints * a.spot(sun_at[0], HORIZON + 0.03, 0.22, 1.0, squash=0.8), p["glow"], 0.55)
        a.tint(layer, fog(a, "aotearoa horizon haze", HORIZON, 0.012, 3.0), p["low"], 0.45)
        _textbook(a, layer, 0.06)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far aotearoa")
        cols = a.u[0]
        # The forested coast at the left: hills of forest with tall kauri
        # over it, and a beach under it with pōhutukawa along the shore.
        coast_line = np.interp(cols, [-0.05, 0.12, 0.26, 0.38, 0.46, 0.52], [0.505, 0.520, 0.548, 0.580, 0.604, sea_v + 0.01]).astype(np.float32)
        coast_line = coast_line + (a.line_noise("aotearoa coast", cells=14.0, octaves=3) - 0.5) * 0.010
        forest, forest_pen = a.drawing()
        forest_pen.poly([(-0.02, sea_v - 0.004)] + [(float(u), float(np.interp(u, cols, coast_line)) + 0.006) for u in np.linspace(-0.02, 0.52, 40)] + [(0.53, sea_v - 0.004)])
        for _ in range(170):
            u = rng.uniform(-0.02, 0.50)
            line_v = float(np.interp(u, cols, coast_line))
            forest_pen.ellipse(u, line_v + rng.uniform(-0.002, 0.006), rng.uniform(0.008, 0.016), rng.uniform(0.006, 0.012))
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        for u, h in ((0.05, 0.090), (0.13, 0.080), (0.24, 0.070), (0.31, 0.060)):
            _kauri(trunk_pen, crown_pen, rng, u, float(np.interp(u, cols, coast_line)) + h * 0.40, h)
        beach, beach_pen = a.drawing()
        beach_pen.poly([(-0.02, sea_v - 0.008), (0.56, sea_v - 0.002), (0.58, sea_v + 0.004), (-0.02, sea_v + 0.004)])
        pohu, pohu_pen = a.drawing()
        blooms, bloom_pen = a.drawing()
        for u, h, w in ((0.02, 0.040, 0.040), (0.12, 0.032, 0.030), (0.36, 0.034, 0.034), (0.44, 0.030, 0.026)):
            _pohutukawa(trunk_pen, pohu_pen, bloom_pen, rng, u, sea_v - 0.006, h, w, 0.2)
        hulls, hull_pen = a.drawing()
        for u, s, f in ((0.495, 0.034, 1.0), (0.535, 0.028, -1.0)):
            _waka(hull_pen, u, sea_v - 0.003, s, f)
        # The pā on the headland at the right: terraces cut into the hill,
        # palisades of posts on their edges, houses with steep roofs on
        # the top, and the thin smoke of a fire.
        hill_line = np.array([_pa_hill(float(u)) for u in cols], dtype=np.float32)
        hill = _land(a, hill_line) * (a.v < sea_v + 0.004) * (a.u > 0.55)
        posts, post_pen = a.drawing()
        walls, wall_pen = a.drawing()
        roofs, roof_pen = a.drawing()
        x = 0.635
        while x < 1.02:
            top = _pa_hill(x)
            if top < 0.585:
                post_pen.line([(x, top + 0.002), (x, top - 0.012 - 0.002 * (round(x * 500) % 2))], 0.0016)
            x += 0.0042
        for lv in (0.530, 0.546):
            us = [u for u in np.linspace(0.60, 1.0, 400) if abs(_pa_hill(float(u)) - lv) < 0.0030]
            if us:
                post_pen.line([(min(us), lv - 0.007), (max(us), lv - 0.007)], 0.0012)
        for u, w, h in ((0.80, 0.008, 0.016), (0.835, 0.010, 0.020), (0.87, 0.007, 0.015), (0.90, 0.009, 0.018), (0.745, 0.007, 0.014)):
            _whare(wall_pen, roof_pen, u, _pa_hill(u) - 0.001, w, h)
        storehouse = (0.92, _pa_hill(0.92))
        post_pen.line([(storehouse[0] - 0.004, storehouse[1]), (storehouse[0] - 0.004, storehouse[1] - 0.012)], 0.0014)
        post_pen.line([(storehouse[0] + 0.004, storehouse[1]), (storehouse[0] + 0.004, storehouse[1] - 0.012)], 0.0014)
        _whare(wall_pen, roof_pen, storehouse[0], storehouse[1] - 0.012, 0.006, 0.012)
        smoke = _plume(a, "aotearoa pa smoke", 0.855, _pa_hill(0.855) - 0.006, 0.12, 0.05, 0.005)
        forest_mask = a.mask_of(forest)
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        beach_mask = a.mask_of(beach)
        pohu_mask = a.mask_of(pohu)
        bloom_mask = a.mask_of(blooms) * pohu_mask
        hull_mask = a.mask_of(hulls)
        post_mask = a.mask_of(posts)
        wall_mask = a.mask_of(walls)
        roof_mask = a.mask_of(roofs)
        water = smoothstep(HORIZON + 0.006, HORIZON + 0.012, a.v)
        land = np.maximum.reduce([forest_mask, trunk_mask, crown_mask, beach_mask, pohu_mask, hull_mask, hill, post_mask, wall_mask, roof_mask])
        mask = np.maximum(land, water)
        layer = solid(a, mask, mix(p["forest"], p["far"], 0.40), mix(p["forest"], p["far"], 0.20), 0.50, 0.62, "aotearoa far", 0.04)
        a.put(layer, water, a.ramp([(0.0, mix(p["sea_light"], p["low"], 0.35)), (HORIZON + 0.012, mix(p["sea_light"], p["low"], 0.35)),
                                     (0.66, mix(p["sea"], p["sea_light"], 0.30)), (0.72, p["sea"]), (1.0, p["sea_deep"])]))
        a.put(layer, _reflected(a, land, sea_v, "aotearoa ripple", water * (a.v > sea_v)), mix(p["forest"], p["sea"], 0.55), 0.35)
        lines = smoothstep(0.64, 0.84, a.noise("aotearoa near lines", cells=60.0, octaves=2, stretch=16.0))
        a.light(layer, water * lines * smoothstep(sea_v + 0.004, sea_v + 0.05, a.v), p["sea_light"], 0.30)
        a.put(layer, a.band(sea_v + 0.001, 0.002, 1.0) * smoothstep(0.62, 0.56, a.u) * water, p["sea_light"], 0.7)
        # The forest: dark and round, a little lighter on its tops.
        a.put(layer, forest_mask, mix(p["forest"], p["far"], 0.30))
        a.light(layer, forest_mask * smoothstep(0.58, 0.78, a.noise("aotearoa crowns", cells=90.0, octaves=3)), mix(p["forest_light"], p["far"], 0.25), 0.35)
        a.light(layer, a.rim(forest_mask, -0.002, 0.003, 0.3) * forest_mask, p["glow"], 0.35)
        a.put(layer, trunk_mask, mix(mix(p["kauri"], p["post"], 0.35), p["far"], 0.20))
        a.shade(layer, trunk_mask * (a.u > 0.0) * a.rim(trunk_mask, -0.002, 0.0, 0.0), 0.25)
        a.put(layer, crown_mask, mix(p["forest"], p["far"], 0.28))
        a.light(layer, a.rim(crown_mask, -0.002, 0.003, 0.2) * crown_mask, mix(p["forest_light"], p["glow"], 0.3), 0.45)
        a.put(layer, beach_mask, mix(p["sand"], p["far"], 0.15))
        a.put(layer, pohu_mask, mix(mix(p["pohutukawa"], p["near"], 0.35), p["far"], 0.22))
        a.light(layer, a.rim(pohu_mask, -0.002, 0.002, 0.2) * pohu_mask, p["forest_light"], 0.40)
        a.put(layer, bloom_mask, mix(p["flower"], p["far"], 0.15))
        a.put(layer, hull_mask, mix(p["hull"], p["far"], 0.20))
        # The headland: green slopes, the yellow clay of the terrace faces,
        # and the grey posts of the palisades.
        a.put(layer, hill, mix(p["hill"], p["far"], 0.25))
        a.put(layer, hill * smoothstep(0.55, 0.70, a.noise("aotearoa scrub", cells=70.0, octaves=3)), mix(p["forest"], p["far"], 0.30), 0.45)
        faces = a.rim(hill, 0.0, -0.004, 0.0) * hill * (a.v < 0.585)
        a.put(layer, faces, mix(p["earth"], p["far"], 0.20), 0.85)
        a.light(layer, a.rim(hill, 0.0, 0.003, 0.2) * hill, p["glow"], 0.40)
        a.put(layer, post_mask, mix(p["post"], p["far"], 0.25))
        a.put(layer, wall_mask, mix(p["post"], p["far"], 0.15))
        a.put(layer, roof_mask, mix(p["thatch"], p["far"], 0.15))
        a.shade(layer, a.rim(roof_mask, -0.002, 0.0, 0.0) * roof_mask, 0.25)
        a.put(layer, smoke, p["smoke"], 0.50)
        mask = np.maximum(mask, smoke * 0.5)
        a.tint(layer, fog(a, "aotearoa shore haze", sea_v - 0.006, 0.012, 3.0) * mask, p["low"], 0.30)
        haze(a, layer, p["low"], 0.07, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near aotearoa")
        bank, ground, bank_at = _bank(a, "near aotearoa", 0.050, 0.040)
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        blooms, bloom_pen = a.drawing()
        palms, palm_pen = a.drawing()
        palm_crowns, palm_crown_pen = a.drawing()
        ferns, fern_pen = a.drawing()
        fern_trunks, fern_trunk_pen = a.drawing()
        flax, flax_pen = a.drawing()
        grass, grass_pen = a.drawing()
        # A pōhutukawa leans out at the left, red with flowers; a nīkau, a
        # tree fern and clumps of flax at the right. The middle is a calm
        # bank of grass and low fern.
        _pohutukawa(trunk_pen, crown_pen, bloom_pen, rng, 0.05, bank_at(0.05) + 0.006, 0.40, 0.15, 0.30)
        _nikau(palm_pen, palm_crown_pen, rng, 0.88, bank_at(0.88) + 0.006, 0.46, -0.01)
        _tree_fern(fern_trunk_pen, fern_pen, rng, 0.95, bank_at(0.95) + 0.006, 0.30, 0.01)
        for u, h in ((0.80, 0.090), (0.25, 0.060), (0.99, 0.070)):
            _flax(flax_pen, rng, u, bank_at(u) + 0.004, h, 13, 2 if h > 0.07 else 1)
        for _ in range(150):
            u = rng.uniform(0.0, 1.0)
            h = rng.uniform(0.006, 0.012) * (1.0 + 0.8 * (abs(u - 0.5) > 0.3))
            v = bank_at(u) + 0.002
            grass_pen.line([(u, v), (u + rng.uniform(-0.004, 0.004), v - h)], 0.0013)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        bloom_mask = a.mask_of(blooms) * crown_mask
        palm_mask = a.mask_of(palms)
        palm_crown_mask = a.mask_of(palm_crowns)
        fern_mask = np.maximum(a.mask_of(ferns), a.mask_of(fern_trunks))
        flax_mask = a.mask_of(flax)
        grass_mask = a.mask_of(grass)
        mask = np.maximum.reduce([bank_mask, trunk_mask, crown_mask, palm_mask, palm_crown_mask, fern_mask, flax_mask, grass_mask])
        layer = a.blank()
        earth = a.ramp([(0.0, mix(p["near_light"], p["near"], 0.40)), (0.66, mix(p["near_light"], p["near"], 0.40)), (0.78, mix(p["earth"], p["near"], 0.72)), (1.0, p["near"])])
        a.put(layer, bank_mask, earth)
        a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, p["glow"], 0.30)
        a.put(layer, grass_mask, mix(p["near_light"], p["near"], 0.35))
        a.put(layer, trunk_mask, mix(p["post"], p["near"], 0.45))
        a.light(layer, a.rim(trunk_mask, 0.003, 0.0, 0.0) * trunk_mask, p["glow"], 0.25)
        a.put(layer, crown_mask, mix(p["pohutukawa"], p["near"], 0.35))
        a.light(layer, a.rim(crown_mask, 0.002, 0.003, 0.3) * crown_mask, p["forest_light"], 0.35)
        a.put(layer, bloom_mask, mix(p["flower"], p["near"], 0.25))
        a.put(layer, palm_mask, mix(p["kauri"], p["near"], 0.50))
        a.shade(layer, palm_mask * (np.abs(((a.v * 300.0) % 1.0) - 0.5) < 0.12), 0.25)
        a.put(layer, palm_crown_mask, mix(p["fern"], p["near"], 0.35))
        a.light(layer, a.rim(palm_crown_mask, 0.002, 0.002, 0.0) * palm_crown_mask, p["near_light"], 0.35)
        a.put(layer, fern_mask, mix(p["fern"], p["near"], 0.40))
        a.put(layer, flax_mask, mix(p["flax"], p["near"], 0.35))
        a.light(layer, a.rim(flax_mask, 0.0015, 0.0, 0.0) * flax_mask, p["near_light"], 0.35)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.18)
        haze(a, layer, p["low"], 0.08, None)
        return layer
    layer = _air(a, p, "aotearoa sea haze", p["low"], 0.22, scale(p["near"], 0.9), 0.14)
    a.put(layer, shafts(a, "aotearoa shafts", 4, -0.12, 0.0, 0.85, 0.05), p["glow"], 0.06)
    return layer


def _fern_frond(pen: Pen, rib, width: float) -> None:
    """A fern frond along `rib`: a thin stem with pairs of leaflets that
    get smaller to its tip."""
    pen.line(rib, width)
    n = len(rib)
    for i in range(1, n - 1):
        (x0, y0), (x1, y1) = rib[i], rib[i + 1]
        d = math.hypot(x1 - x0, y1 - y0) or 1.0
        nx, ny = -(y1 - y0) / d, (x1 - x0) / d
        size = width * 9.0 * (1.0 - i / n) + width
        for side in (-1.0, 1.0):
            pen.line([(x0, y0), (x0 + nx * side * size + (x1 - x0) * 0.8, y0 + ny * side * size + (y1 - y0) * 0.8)], width * 0.8)


def aotearoa_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """A branch of pōhutukawa hangs into the top of the view at one place,
    with clusters of its leaves and flowers. Fern fronds arch up from below
    at one place."""
    del layer_lights
    rng = art_.rand("aotearoa foreground")
    u0 = rng.uniform(0.10, 0.28)
    branch = _arch((u0 - 0.06, 0.0), (u0 + 0.12, 0.16), (u0 + 0.30, 0.300), 16)
    for i in range(len(branch) - 1):
        pen.line([branch[i], branch[i + 1]], 0.010 * (1.0 - 0.6 * i / 16.0))
    for i in range(5, 17, 3):
        x, y = branch[i]
        for _ in range(6):
            cx, cy = x + rng.uniform(-0.025, 0.025), min(0.370, y + rng.uniform(0.0, 0.050))
            pen.ellipse(cx, cy, rng.uniform(0.008, 0.013), rng.uniform(0.005, 0.008))
        for _ in range(4):
            cx, cy = x + rng.uniform(-0.02, 0.02), min(0.374, y + rng.uniform(0.02, 0.06))
            for k in range(7):
                pen.line([(cx, cy), polar(cx, cy, 0.008, -170.0 + k * 26.0)], 0.0009)
    u = rng.uniform(0.58, 0.70)
    top = REST_BOTTOM - 0.004
    for k in range(5):
        ang = -90.0 + (k - 2) * 24.0 + rng.uniform(-5.0, 5.0)
        length = rng.uniform(0.16, 0.20)
        tip = polar(u, 1.0, length, ang)
        tip = (tip[0] + (k - 2) * 0.02, max(top + abs(k - 2) * 0.012, tip[1] - 0.20))
        _fern_frond(pen, _arch((u, 1.0), (u + (k - 2) * 0.01, tip[1] + 0.06), tip, 14), 0.0022)


# ---------------------------------------------------------------------------
# Tonga: Tongatapu, about 1200
# ---------------------------------------------------------------------------


TONGA = {
    "top": (38, 108, 180),
    "mid": (150, 200, 226),
    "low": (236, 242, 236),
    "glow": (255, 242, 210),
    "sun": (255, 252, 238),
    "cloud": (255, 255, 252),
    "cloud_shadow": (170, 186, 204),
    "ocean": (34, 88, 140),
    "lagoon": (58, 178, 176),
    "lagoon_light": (196, 238, 226),
    "reef": (250, 250, 244),
    "sand": (242, 232, 204),
    "island": (58, 104, 64),
    "island_light": (140, 172, 86),
    "palm": (54, 98, 58),
    "palm_light": (156, 180, 92),
    "trunk": (140, 122, 98),
    "stone": (196, 192, 180),
    "stone_dark": (128, 124, 116),
    "thatch": (178, 148, 96),
    "wood": (110, 82, 58),
    "sail": (226, 206, 162),
    "far": (204, 222, 224),
    "near": (30, 46, 38),
    "near_light": (204, 184, 132),
}

#: The level of the far shore across the lagoon, and of the reef far out.
TONGA_SHORE = 0.598
TONGA_REEF = HORIZON + 0.006


def _haamonga(stone: Pen, shade: Pen, u: float, v: float, h: float) -> None:
    """The Haʻamonga ʻa Maui: two uprights of grey coral limestone, each
    about five metres high, about four metres apart, and a heavy lintel
    laid across their tops in notches cut into them. `(u, v)` is the
    middle of the foot and `h` the height of an upright."""
    gap = h * 0.40
    width = h * 0.30
    for side in (-1.0, 1.0):
        x0 = u + side * gap
        x1 = u + side * (gap + width)
        lo, hi = min(x0, x1), max(x0, x1)
        stone.poly([(lo - h * 0.015, v + 0.002), (hi + h * 0.015, v + 0.002), (hi + h * 0.005, v - h * 0.55), (hi, v - h), (lo, v - h), (lo - h * 0.005, v - h * 0.55)])
        shade.poly([(x0 + side * width * 0.05, v + 0.002), (x0 + side * width * 0.30, v + 0.002), (x0 + side * width * 0.26, v - h * 0.86), (x0 + side * width * 0.05, v - h * 0.86)])
    stone.poly([(u - gap - width * 0.82, v - h * 1.03), (u + gap + width * 0.82, v - h * 1.03), (u + gap + width * 0.80, v - h * 0.86), (u - gap - width * 0.80, v - h * 0.86)])
    shade.rect(u - gap - width * 0.80, v - h * 0.90, u + gap + width * 0.80, v - h * 0.86)


def _fale(roof: Pen, posts: Pen, dark: Pen, u: float, v: float, w: float, h: float) -> None:
    """A fale far off: a roof of thatch like a long low dome, on a ring of
    short posts, open at its sides, so its inside is in shade."""
    roof.ellipse(u, v - h * 0.45, w, h * 0.55)
    dark.rect(u - w * 0.86, v - h * 0.45, u + w * 0.86, v + 0.001)
    for k in range(5):
        x = u - w * 0.80 + k * w * 0.40
        posts.line([(x, v + 0.001), (x, v - h * 0.45)], w * 0.06)


def history_tonga(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = TONGA
    sun_at = (0.66, 0.14)
    shore = TONGA_SHORE
    if layer_key == "sky":
        # A bright day of the trade wind: tall white heap clouds, the deep
        # blue ocean at the horizon, the white line of surf on the reef far
        # out, and the calm turquoise lagoon inside it.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.86)), (0.24, p["top"]), (0.50, p["mid"]), (HORIZON - 0.004, p["low"]),
                                 (HORIZON, mix(p["ocean"], p["low"], 0.35)), (TONGA_REEF, p["ocean"]), (TONGA_REEF + 0.004, mix(p["lagoon"], p["lagoon_light"], 0.45)),
                                 (0.70, p["lagoon"]), (1.0, scale(p["lagoon"], 0.85))]))
        _sun(a, layer, *sun_at, 0.018, p["sun"], p["glow"], 0.45)
        _heaps(a, layer, "tonga heaps", ((0.10, 0.52, 0.06, 0.12), (0.36, 0.53, 0.08, 0.16), (0.58, 0.55, 0.05, 0.08), (0.86, 0.52, 0.07, 0.13)), p["cloud"], p["cloud_shadow"], 0.95)
        surf = a.band(TONGA_REEF + 0.001, 0.003, 1.0) * smoothstep(0.30, 0.55, a.noise("tonga surf", cells=40.0, octaves=3, stretch=3.0))
        a.put(layer, surf, p["reef"], 0.95)
        lagoon = (a.v > TONGA_REEF + 0.004).astype(np.float32)
        ripples = smoothstep(0.55, 0.80, a.noise("tonga ripples", cells=70.0, octaves=2, stretch=9.0))
        a.light(layer, lagoon * ripples, p["lagoon_light"], 0.30)
        a.light(layer, lagoon * ripples * a.spot(sun_at[0], TONGA_REEF + 0.04, 0.24, 1.2, squash=0.8), p["glow"], 0.50)
        a.tint(layer, fog(a, "tonga horizon haze", HORIZON, 0.010, 3.0), p["low"], 0.40)
        _textbook(a, layer, 0.05)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far tonga")
        cols = a.u[0]
        # The flat island across the lagoon at the left: no hill at all,
        # only a long low line of coconut palms and pandanus. The
        # Haʻamonga stands among the palms; fale with domed roofs of thatch
        # are near the shore. At the right the lagoon is open to the reef.
        land_top = shore - 0.006 - 0.004 * a.line_noise("tonga land", cells=8.0, octaves=2)
        land_top = np.where(cols < 0.64, land_top, 1.0) - 0.0 * cols
        land_top = land_top + 0.010 * smoothstep(0.58, 0.64, cols)
        land = _land(a, land_top.astype(np.float32)) * (a.v < shore + 0.004)
        bush, bush_pen = a.drawing()
        for _ in range(120):
            u = rng.uniform(-0.02, 0.63)
            bush_pen.ellipse(u, shore - 0.008 - rng.uniform(0.0, 0.004), rng.uniform(0.006, 0.014), rng.uniform(0.004, 0.010))
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        stone, stone_pen = a.drawing()
        stone_shade, stone_shade_pen = a.drawing()
        stone_at = 0.30
        for k in range(28):
            u = -0.02 + k * 0.024 + rng.uniform(-0.008, 0.008)
            if abs(u - stone_at) < 0.028 or u > 0.64:
                continue
            _coconut_palm(trunk_pen, crown_pen, rng, u, shore - 0.004, rng.uniform(0.050, 0.085), rng.uniform(-0.012, 0.012))
        for u in (0.12, 0.42, 0.55):
            _pandanus(trunk_pen, crown_pen, rng, u, shore - 0.002, 0.030, rng.uniform(-0.01, 0.01))
        _haamonga(stone_pen, stone_shade_pen, stone_at, shore - 0.004, 0.040)
        roofs, roof_pen = a.drawing()
        posts, post_pen = a.drawing()
        dark, dark_pen = a.drawing()
        for u, w, h in ((0.46, 0.016, 0.014), (0.505, 0.012, 0.011), (0.20, 0.012, 0.011)):
            _fale(roof_pen, post_pen, dark_pen, u, shore - 0.002, w, h)
        beach, beach_pen = a.drawing()
        beach_pen.poly([(-0.02, shore - 0.004), (0.60, shore - 0.003), (0.66, shore + 0.003), (-0.02, shore + 0.004)])
        # A kalia, the great double-hulled canoe, on the lagoon, and a
        # small outrigger canoe nearer the reef.
        hulls, hull_pen = a.drawing()
        sails, sail_pen = a.drawing()
        _voyaging_canoe(hull_pen, sail_pen, 0.78, shore + 0.010, 0.066, -1.0)
        _outrigger(hull_pen, sail_pen, 0.92, shore + 0.002, 0.040, 1.0)
        land_mask = np.maximum(land, a.mask_of(bush))
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        stone_mask = a.mask_of(stone)
        shade_mask = a.mask_of(stone_shade) * stone_mask
        roof_mask = a.mask_of(roofs)
        post_mask = a.mask_of(posts)
        dark_mask = a.mask_of(dark) * (1.0 - roof_mask)
        beach_mask = a.mask_of(beach)
        boat = np.maximum(a.mask_of(hulls), a.mask_of(sails))
        water_top = (shore - 0.002) + (TONGA_REEF + 0.006 - shore + 0.002) * smoothstep(0.62, 0.70, a.u)
        water = smoothstep(water_top, water_top + 0.004, a.v)
        things = np.maximum.reduce([land_mask, trunk_mask, crown_mask, stone_mask, roof_mask, post_mask, dark_mask, beach_mask])
        mask = np.maximum.reduce([things, boat, water])
        layer = solid(a, mask, mix(p["island"], p["far"], 0.35), mix(p["island"], p["far"], 0.15), 0.54, 0.60, "tonga far", 0.04)
        a.put(layer, water, a.ramp([(0.0, mix(p["lagoon_light"], p["lagoon"], 0.35)), (HORIZON + 0.014, mix(p["lagoon_light"], p["lagoon"], 0.35)),
                                     (0.66, mix(p["lagoon"], p["lagoon_light"], 0.20)), (1.0, p["lagoon"])]))
        a.put(layer, _reflected(a, things, shore + 0.002, "tonga ripple", water * (a.v > shore + 0.002)), mix(p["island"], p["lagoon"], 0.55), 0.30)
        ripples = smoothstep(0.55, 0.80, a.noise("tonga near ripples", cells=70.0, octaves=2, stretch=9.0))
        a.light(layer, water * ripples * smoothstep(shore + 0.004, shore + 0.05, a.v), p["lagoon_light"], 0.30)
        a.put(layer, land_mask, mix(p["island"], p["far"], 0.30))
        a.light(layer, land_mask * smoothstep(0.55, 0.75, a.noise("tonga bush", cells=80.0, octaves=2)), mix(p["island_light"], p["far"], 0.3), 0.35)
        a.put(layer, beach_mask, mix(p["sand"], p["far"], 0.10))
        a.put(layer, trunk_mask, mix(p["trunk"], p["far"], 0.25))
        a.put(layer, crown_mask, mix(p["palm"], p["far"], 0.22))
        a.light(layer, a.rim(crown_mask, -0.0015, 0.0015, 0.0) * crown_mask, mix(p["palm_light"], p["far"], 0.2), 0.50)
        # The trilithon: pale grey, lit on its left, its inner faces in
        # shade, and the dark of the air between its uprights.
        a.put(layer, stone_mask, mix(p["stone"], p["far"], 0.10))
        a.put(layer, shade_mask, mix(p["stone_dark"], p["far"], 0.15))
        a.put(layer, stone_mask * smoothstep(0.6, 0.75, a.noise("tonga coral stone", cells=200.0, octaves=2)), mix(p["stone_dark"], p["far"], 0.2), 0.35)
        a.light(layer, a.rim(stone_mask, 0.002, 0.0, 0.0) * stone_mask, p["glow"], 0.5)
        a.put(layer, dark_mask, mix(p["near"], p["far"], 0.35))
        a.put(layer, post_mask, mix(p["wood"], p["far"], 0.25))
        a.put(layer, roof_mask, mix(p["thatch"], p["far"], 0.12))
        a.light(layer, a.rim(roof_mask, 0.0, 0.002, 0.0) * roof_mask, p["glow"], 0.45)
        a.shade(layer, roof_mask * smoothstep(0.0, 1.0, (a.v - shore + 0.012) / 0.012), 0.20)
        a.put(layer, a.mask_of(hulls), mix(p["wood"], p["far"], 0.25))
        a.put(layer, a.mask_of(sails), mix(p["sail"], p["far"], 0.10))
        a.shade(layer, a.mask_of(sails) * a.rim(a.mask_of(sails), 0.0, -0.002, 0.0), 0.30)
        a.put(layer, _reflected(a, boat, shore + 0.011, "tonga canoe ripple", water * (1.0 - boat) * (a.v > shore + 0.010)), mix(p["wood"], p["lagoon"], 0.55), 0.30)
        haze(a, layer, p["low"], 0.07, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near tonga")
        bank, ground, bank_at = _bank(a, "near tonga", 0.040, 0.050)
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        leaves, leaf_pen = a.drawing()
        grass, grass_pen = a.drawing()
        # A coconut palm leans out over the beach at the left; a pandanus
        # stands at the right. The middle is a calm bank of pale coral sand
        # with a few runners of beach vine.
        _coconut_palm(trunk_pen, crown_pen, rng, 0.07, bank_at(0.07) + 0.006, 0.48, 0.10)
        _coconut_palm(trunk_pen, crown_pen, rng, 0.17, bank_at(0.17) + 0.006, 0.36, 0.05)
        _pandanus(trunk_pen, leaf_pen, rng, 0.90, bank_at(0.90) + 0.006, 0.36, -0.04)
        for _ in range(16):
            u = rng.choice([rng.uniform(0.24, 0.34), rng.uniform(0.70, 0.84)])
            _grass_blades(grass_pen, rng, u, bank_at(u) + 0.002, rng.uniform(0.008, 0.016), 6, 0.0012, 0.012)
        for _ in range(5):
            u0 = rng.uniform(0.26, 0.74)
            pts = [(u0 + k * 0.012, bank_at(u0 + k * 0.012) + 0.002 + 0.0015 * math.sin(k)) for k in range(8)]
            grass_pen.line(pts, 0.0010)
            for x, y in pts[1::2]:
                grass_pen.ellipse(x, y - 0.002, 0.003, 0.002)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        leaf_mask = a.mask_of(leaves)
        grass_mask = a.mask_of(grass)
        mask = np.maximum.reduce([bank_mask, trunk_mask, crown_mask, leaf_mask, grass_mask])
        layer = a.blank()
        sand = a.ramp([(0.0, mix(p["near_light"], p["near"], 0.25)), (0.66, mix(p["near_light"], p["near"], 0.25)), (0.80, mix(p["near_light"], p["near"], 0.70)), (1.0, p["near"])])
        a.put(layer, bank_mask, sand)
        a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, p["glow"], 0.40)
        a.put(layer, grass_mask, mix(p["island_light"], p["near"], 0.40))
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
    layer = _air(a, p, "tonga sea haze", p["low"], 0.20, scale(p["near"], 0.9), 0.12)
    a.put(layer, shafts(a, "tonga shafts", 4, 0.10, 0.0, 0.85, 0.05), p["glow"], 0.07)
    return layer


def tonga_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """The fronds of a coconut palm hang into the top of the view at two
    places, seen from under the crown: each a long arched rib with its
    narrow leaflets that hang down from it."""
    del layer_lights
    rng = art_.rand("tonga foreground")
    for k in range(2):
        u0 = 0.10 + (k + rng.uniform(0.2, 0.8)) * 0.40
        for j in range(4):
            start = (u0 + (j - 1.5) * 0.03, 0.0)
            end = (start[0] + (j - 1.5) * 0.10 + rng.uniform(-0.02, 0.02), 0.330 - rng.uniform(0.0, 0.030))
            rib = _arch(start, ((start[0] + end[0]) * 0.5 + (j - 1.5) * 0.04, 0.10), end, 22)
            pen.line(rib, 0.0034)
            for i, (x, y) in enumerate(rib[1:], 1):
                side = 0.050 * (1.0 - i / 22.0 * 0.55)
                side = max(0.0, min(side, 0.378 - y))
                pen.line([(x, y), (x + side * 0.22, y + side)], 0.0018)
                pen.line([(x, y), (x - side * 0.22, y + side)], 0.0018)


# ---------------------------------------------------------------------------
# Waitangi: the Bay of Islands, 6 February 1840
# ---------------------------------------------------------------------------


WAITANGI = {
    "top": (62, 118, 176),
    "mid": (170, 202, 222),
    "low": (238, 238, 226),
    "glow": (255, 236, 196),
    "sun": (255, 250, 232),
    "cloud": (252, 250, 244),
    "cloud_shadow": (172, 182, 196),
    "sea": (50, 110, 150),
    "sea_light": (190, 220, 226),
    "sea_deep": (34, 82, 118),
    "hill": (98, 140, 74),
    "hill_light": (168, 188, 100),
    "bush": (50, 84, 56),
    "lawn": (120, 158, 76),
    "house": (240, 238, 228),
    "roof": (112, 106, 102),
    "canvas": (238, 234, 220),
    "canvas_shade": (176, 172, 162),
    "hull": (58, 48, 42),
    "sail": (226, 218, 196),
    "sand": (228, 214, 178),
    "clay": (196, 160, 92),
    "post": (96, 80, 62),
    "cloth": (200, 60, 50),
    "skin": (110, 76, 56),
    "flax": (74, 106, 58),
    "far": (204, 216, 218),
    "near": (26, 40, 30),
    "near_light": (120, 152, 84),
}

#: The level of the water of the bay at the near shore.
WAITANGI_SEA = 0.626


def _grounds(u: float) -> float:
    """The top of the grounds at Waitangi at the right: from the beach the
    lawn rises to a level top where the house stands, with bush behind."""
    return float(np.interp(u, [0.54, 0.60, 0.66, 0.74, 0.86, 1.04], [WAITANGI_SEA + 0.004, 0.614, 0.602, 0.596, 0.592, 0.590]))


def _kororareka(u: float) -> float:
    """The hills across the bay at the left: Maiki Hill high over the town
    of Kororāreka, then lower hills."""
    return float(np.interp(u, [-0.05, 0.04, 0.10, 0.17, 0.26, 0.34, 0.40], [0.574, 0.566, 0.556, 0.572, 0.582, 0.594, HORIZON + 0.004]))


def _treaty_house(walls: Pen, roof: Pen, dark: Pen, posts: Pen, u: float, v: float, w: float, h: float) -> None:
    """James Busby's house far off: a small house of white weatherboard
    under a hipped roof, a verandah along its front on thin posts, a door in
    the middle and a window at each side of it."""
    walls.rect(u - w, v - h, u + w, v + 0.001)
    roof.poly([(u - w * 1.10, v - h), (u - w * 0.55, v - h * 1.75), (u + w * 0.55, v - h * 1.75), (u + w * 1.10, v - h)])
    roof.poly([(u - w * 1.12, v - h * 0.62), (u - w * 1.06, v - h * 0.92), (u + w * 1.06, v - h * 0.92), (u + w * 1.12, v - h * 0.62)])
    for k in range(6):
        x = u - w * 1.05 + k * w * 2.10 / 5.0
        posts.line([(x, v + 0.001), (x, v - h * 0.62)], w * 0.03)
    dark.rect(u - w * 0.10, v - h * 0.50, u + w * 0.10, v + 0.001)
    for x in (u - w * 0.58, u + w * 0.58):
        dark.rect(x - w * 0.14, v - h * 0.50, x + w * 0.14, v - h * 0.18)


def _marquee(canvas: Pen, shade: Pen, rig: Pen, u: float, v: float, w: float, h: float) -> None:
    """A large marquee of ship's sails: low walls of canvas, a long roof
    that rises to three peaks on its poles, and guy ropes from the eaves to
    the ground at each side."""
    eave = v - h * 0.45
    peaks = [u - w * 0.55, u, u + w * 0.55]
    roof = [(u - w * 1.05, eave)]
    for k, x in enumerate(peaks):
        roof.append((x - w * 0.20, eave - h * 0.40))
        roof.append((x, eave - h * 0.55))
        roof.append((x + w * 0.20, eave - h * 0.40))
    roof.append((u + w * 1.05, eave))
    canvas.poly(roof)
    canvas.rect(u - w, eave, u + w, v + 0.001)
    shade.rect(u - w * 0.22, eave + h * 0.06, u + w * 0.22, v + 0.001)
    for x in peaks:
        rig.line([(x, eave - h * 0.55), (x, eave - h * 0.70)], w * 0.015)
    for side in (-1.0, 1.0):
        for k in range(3):
            x = u + side * (w * 0.98 - k * w * 0.32)
            rig.line([(x, eave), (x + side * w * 0.30, v + 0.002)], w * 0.008)


def _cabbage_tree(trunk: Pen, crown: Pen, rng, u: float, v: float, h: float) -> None:
    """A tī kōuka, a cabbage tree: a slim trunk that forks into two or
    three branches, each with a round tuft of long thin leaves at its end."""
    fork = (u + rng.uniform(-0.02, 0.02) * h, v - h * 0.55)
    trunk.line([(u, v + 0.004), fork], h * 0.035)
    for k in range(3):
        end = (fork[0] + (k - 1) * h * 0.20 + rng.uniform(-0.03, 0.03) * h, v - h * rng.uniform(0.82, 0.96))
        trunk.line([fork, ((fork[0] + end[0]) * 0.5, (fork[1] + end[1]) * 0.5 - h * 0.02), end], h * 0.020)
        for j in range(30):
            ang = -200.0 + j * 220.0 / 29.0 + rng.uniform(-3.0, 3.0)
            length = h * rng.uniform(0.13, 0.18)
            tip = polar(*end, length, ang)
            droop = length * 0.45 if abs(ang + 90.0) > 70.0 else 0.0
            crown.line([end, polar(*end, length * 0.6, ang), (tip[0], tip[1] + droop)], h * 0.011)


def history_waitangi(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = WAITANGI
    sun_at = (0.40, 0.18)
    sea_v = WAITANGI_SEA
    if layer_key == "sky":
        # A summer day over the Bay of Islands: heap clouds, low hills far
        # off round the wide bay, and its blue water.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.88)), (0.24, p["top"]), (0.48, p["mid"]), (HORIZON - 0.004, p["low"]),
                                 (HORIZON + 0.002, mix(p["sea_light"], p["low"], 0.40)), (0.66, mix(p["sea"], p["sea_light"], 0.40)), (1.0, p["sea"])]))
        _sun(a, layer, *sun_at, 0.018, p["sun"], p["glow"], 0.45)
        _heaps(a, layer, "waitangi heaps", ((0.12, 0.42, 0.07, 0.09), (0.36, 0.46, 0.06, 0.07), (0.64, 0.40, 0.09, 0.12), (0.90, 0.46, 0.05, 0.06)), p["cloud"], p["cloud_shadow"], 0.85)
        hills, _ = a.ridge("waitangi far hills", HORIZON - 0.010, 0.008, cells=4.0, octaves=4)
        hills = hills * (a.v < HORIZON + 0.002) * smoothstep(0.30, 0.40, a.u) * smoothstep(0.70, 0.60, a.u)
        a.put(layer, hills, mix(p["hill"], p["low"], 0.55))
        lines = smoothstep(0.62, 0.82, a.noise("waitangi swell lines", cells=60.0, octaves=2, stretch=14.0))
        a.light(layer, (a.v > HORIZON + 0.002) * lines, p["sea_light"], 0.28)
        a.tint(layer, fog(a, "waitangi horizon haze", HORIZON, 0.012, 3.0), p["low"], 0.45)
        _textbook(a, layer, 0.07)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far waitangi")
        cols = a.u[0]
        # Across the bay at the left: Kororāreka, its houses along the
        # shore, and the flagstaff on Maiki Hill over it. Wooded islands
        # in the bay.
        across_line = np.array([_kororareka(float(u)) for u in cols], dtype=np.float32) + (a.line_noise("waitangi across", cells=16.0, octaves=3) - 0.5) * 0.004
        across = _land(a, across_line) * (a.v < HORIZON + 0.010)
        isles, isle_pen = a.drawing()
        for u, w, h in ((0.43, 0.030, 0.010), (0.50, 0.018, 0.007), (0.36, 0.014, 0.005)):
            isle_pen.poly([(u - w, HORIZON + 0.009)] + [(u + w * t, HORIZON + 0.009 - h * (1.0 - t * t) ** 0.6) for t in np.linspace(-1.0, 1.0, 16)] + [(u + w, HORIZON + 0.009)])
        houses, house_pen = a.drawing()
        roofs, roof_pen = a.drawing()
        for k in range(11):
            u = 0.06 + k * 0.020 + rng.uniform(-0.005, 0.005)
            v = HORIZON + 0.006 - rng.uniform(0.0, 0.006)
            w = rng.uniform(0.003, 0.005)
            house_pen.rect(u - w, v - w * 0.9, u + w, v)
            roof_pen.poly([(u - w * 1.1, v - w * 0.9), (u, v - w * 1.8), (u + w * 1.1, v - w * 0.9)])
        staff, staff_pen = a.drawing()
        top = _kororareka(0.10)
        staff_pen.line([(0.10, top + 0.002), (0.10, top - 0.030)], 0.0012)
        staff_pen.line([(0.10, top - 0.030), (0.1003, top - 0.038)], 0.0007)
        # The ships at anchor, their sails furled.
        ships, ship_pen = a.drawing()
        furled, furled_pen = a.drawing()
        for u, v, s in ((0.27, 0.618, 0.060), (0.385, 0.614, 0.050), (0.50, 0.622, 0.066)):
            _tall_ship(ship_pen, furled_pen, u, v, s, furled=True)
        # The grounds at Waitangi at the right: the lawn, bush behind it,
        # the Treaty House, the marquee in front of it, a crowd far off,
        # and waka on the beach.
        ground_line = np.array([_grounds(float(u)) for u in cols], dtype=np.float32)
        grounds = _land(a, ground_line) * (a.u > 0.53) * (a.v < sea_v + 0.004)
        bush, bush_pen = a.drawing()
        for _ in range(110):
            u = rng.uniform(0.62, 1.02)
            bush_pen.ellipse(u, _grounds(u) - rng.uniform(0.004, 0.020) * smoothstep(0.62, 0.70, u), rng.uniform(0.008, 0.016), rng.uniform(0.006, 0.012))
        walls, wall_pen = a.drawing()
        house_roof, house_roof_pen = a.drawing()
        dark, dark_pen = a.drawing()
        posts, post_pen = a.drawing()
        _treaty_house(wall_pen, house_roof_pen, dark_pen, post_pen, 0.885, _grounds(0.885) + 0.002, 0.034, 0.020)
        canvas, canvas_pen = a.drawing()
        tent_shade, tent_shade_pen = a.drawing()
        rig, rig_pen = a.drawing()
        _marquee(canvas_pen, tent_shade_pen, rig_pen, 0.755, _grounds(0.755) + 0.006, 0.036, 0.034)
        bodies, body_pen = a.drawing()
        reds, red_pen = a.drawing()
        heads, head_pen = a.drawing()
        for k in range(30):
            u = rng.uniform(0.67, 0.84)
            if abs(u - 0.755) < 0.044 and rng.random() < 0.7:
                continue
            _person(red_pen if k % 5 == 0 else body_pen, head_pen, u, _grounds(u) + 0.010 + rng.uniform(0.0, 0.010), rng.uniform(0.009, 0.011))
        hulls, hull_pen = a.drawing()
        for u, s, f in ((0.585, 0.030, 1.0), (0.615, 0.026, -1.0), (0.645, 0.032, 1.0)):
            _waka(hull_pen, u, max(_grounds(u), sea_v - 0.008) + 0.003, s, f)
        beach, beach_pen = a.drawing()
        beach_pen.poly([(0.54, sea_v + 0.003), (0.60, sea_v - 0.006), (0.70, sea_v - 0.010), (1.02, sea_v - 0.010), (1.02, sea_v + 0.004)])
        across_mask = np.maximum(across, a.mask_of(isles))
        house_mask = a.mask_of(houses) * across
        roof_mask = a.mask_of(roofs)
        staff_mask = a.mask_of(staff)
        ship_mask = a.mask_of(ships)
        furled_mask = a.mask_of(furled)
        bush_mask = a.mask_of(bush) * (a.u > 0.6)
        ground_mask = np.maximum(grounds, a.mask_of(beach))
        wall_mask = a.mask_of(walls)
        hroof_mask = a.mask_of(house_roof)
        dark_mask = a.mask_of(dark) * wall_mask
        post_mask = a.mask_of(posts)
        canvas_mask = a.mask_of(canvas)
        tent_shade_mask = a.mask_of(tent_shade) * canvas_mask
        rig_mask = a.mask_of(rig)
        people = np.maximum(a.mask_of(bodies), a.mask_of(reds))
        hull_mask = a.mask_of(hulls)
        water = smoothstep(HORIZON + 0.008, HORIZON + 0.012, a.v)
        shore = np.maximum.reduce([ground_mask, bush_mask, wall_mask, hroof_mask, post_mask, canvas_mask, rig_mask, people, hull_mask])
        mask = np.maximum.reduce([across_mask, roof_mask, staff_mask, ship_mask, furled_mask, shore, water])
        layer = solid(a, mask, mix(p["hill"], p["far"], 0.45), mix(p["hill"], p["far"], 0.20), 0.56, 0.64, "waitangi far", 0.04)
        a.put(layer, water, a.ramp([(0.0, mix(p["sea_light"], p["low"], 0.35)), (HORIZON + 0.012, mix(p["sea_light"], p["low"], 0.35)),
                                     (0.66, mix(p["sea"], p["sea_light"], 0.30)), (0.72, p["sea"]), (1.0, p["sea_deep"])]))
        boats = np.maximum(ship_mask, furled_mask)
        a.put(layer, _reflected(a, boats, 0.622, "waitangi ship ripple", water * (1.0 - boats) * (a.v > 0.616)), mix(p["hull"], p["sea"], 0.55), 0.30)
        a.put(layer, _reflected(a, shore, sea_v - 0.006, "waitangi shore ripple", water * (a.v > sea_v - 0.004)), mix(p["bush"], p["sea"], 0.55), 0.30)
        lines = smoothstep(0.64, 0.84, a.noise("waitangi near lines", cells=60.0, octaves=2, stretch=16.0))
        a.light(layer, water * lines * smoothstep(HORIZON + 0.012, HORIZON + 0.06, a.v), p["sea_light"], 0.30)
        # Across the bay: pale with distance.
        a.put(layer, across_mask, mix(p["hill"], p["far"], 0.45))
        a.put(layer, across_mask * smoothstep(0.55, 0.70, a.noise("waitangi across bush", cells=60.0, octaves=3)), mix(p["bush"], p["far"], 0.50), 0.5)
        a.put(layer, house_mask, mix(p["house"], p["far"], 0.25))
        a.put(layer, roof_mask, mix(p["roof"], p["far"], 0.35))
        a.put(layer, staff_mask, mix(p["post"], p["far"], 0.35))
        a.put(layer, ship_mask, mix(p["hull"], p["far"], 0.30))
        a.put(layer, furled_mask, mix(p["sail"], p["far"], 0.20))
        # The grounds.
        a.put(layer, grounds, mix(p["lawn"], p["far"], 0.15))
        a.light(layer, grounds * smoothstep(0.55, 0.75, a.noise("waitangi lawn", cells=50.0, octaves=2, stretch=4.0)), mix(p["hill_light"], p["far"], 0.15), 0.30)
        a.put(layer, a.mask_of(beach), mix(p["sand"], p["far"], 0.10))
        a.put(layer, bush_mask, mix(p["bush"], p["far"], 0.22))
        a.light(layer, a.rim(bush_mask, 0.0, 0.003, 0.2) * bush_mask, mix(p["hill_light"], p["glow"], 0.3), 0.35)
        a.put(layer, hroof_mask, mix(p["roof"], p["far"], 0.15))
        a.put(layer, wall_mask * (1.0 - hroof_mask), mix(p["house"], p["far"], 0.05))
        a.put(layer, wall_mask * (1.0 - hroof_mask) * (np.abs(((a.v * 900.0) % 1.0) - 0.5) > 0.38), mix(p["canvas_shade"], p["far"], 0.10), 0.5)
        a.put(layer, dark_mask * (1.0 - hroof_mask), mix(p["hull"], p["far"], 0.20))
        a.put(layer, post_mask, mix(p["house"], p["far"], 0.05))
        a.put(layer, canvas_mask, mix(p["canvas"], p["far"], 0.05))
        a.put(layer, tent_shade_mask, mix(p["canvas_shade"], p["far"], 0.05))
        a.shade(layer, a.rim(canvas_mask, -0.002, 0.0, 0.0) * canvas_mask, 0.25)
        a.put(layer, rig_mask * (1.0 - canvas_mask), mix(p["post"], p["far"], 0.20))
        a.put(layer, a.mask_of(bodies), mix(p["hull"], p["far"], 0.20))
        a.put(layer, a.mask_of(reds), mix(p["cloth"], p["far"], 0.15))
        a.put(layer, a.mask_of(heads) * grounds, mix(p["skin"], p["far"], 0.20))
        a.put(layer, hull_mask, mix(p["hull"], p["far"], 0.20))
        a.light(layer, a.rim(np.maximum(shore, across_mask), 0.002, 0.002, 0.2) * np.maximum(shore, across_mask), p["glow"], 0.30)
        haze(a, layer, p["low"], 0.07, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near waitangi")
        bank, ground, bank_at = _bank(a, "near waitangi", 0.040, 0.050)
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        blooms, bloom_pen = a.drawing()
        flax, flax_pen = a.drawing()
        grass, grass_pen = a.drawing()
        # A cabbage tree and clumps of flax at the left, a pōhutukawa at the
        # right. The middle is a calm bank of lawn.
        _cabbage_tree(trunk_pen, crown_pen, rng, 0.10, bank_at(0.10) + 0.006, 0.40)
        _pohutukawa(trunk_pen, crown_pen, bloom_pen, rng, 0.93, bank_at(0.93) + 0.006, 0.34, 0.12, -0.25)
        for u, h in ((0.03, 0.10), (0.18, 0.075), (0.82, 0.06)):
            _flax(flax_pen, rng, u, bank_at(u) + 0.004, h, 14, 2 if h > 0.07 else 1)
        for _ in range(170):
            u = rng.uniform(0.0, 1.0)
            h = rng.uniform(0.005, 0.010) * (1.0 + 0.8 * (abs(u - 0.5) > 0.3))
            v = bank_at(u) + 0.002
            grass_pen.line([(u, v), (u + rng.uniform(-0.004, 0.004), v - h)], 0.0013)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        bloom_mask = a.mask_of(blooms) * crown_mask
        flax_mask = a.mask_of(flax)
        grass_mask = a.mask_of(grass)
        mask = np.maximum.reduce([bank_mask, trunk_mask, crown_mask, flax_mask, grass_mask])
        layer = a.blank()
        earth = a.ramp([(0.0, mix(p["lawn"], p["near"], 0.40)), (0.66, mix(p["lawn"], p["near"], 0.40)), (0.78, mix(p["clay"], p["near"], 0.72)), (1.0, p["near"])])
        a.put(layer, bank_mask, earth)
        a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, p["glow"], 0.30)
        a.put(layer, grass_mask, mix(p["lawn"], p["near"], 0.30))
        a.put(layer, trunk_mask, mix(p["post"], p["near"], 0.40))
        a.light(layer, a.rim(trunk_mask, 0.003, 0.0, 0.0) * trunk_mask, p["glow"], 0.25)
        a.put(layer, crown_mask, mix(p["bush"], p["near"], 0.30))
        a.light(layer, a.rim(crown_mask, 0.002, 0.003, 0.2) * crown_mask, p["hill_light"], 0.35)
        a.put(layer, bloom_mask, mix(p["cloth"], p["near"], 0.25))
        a.put(layer, flax_mask, mix(p["flax"], p["near"], 0.35))
        a.light(layer, a.rim(flax_mask, 0.0015, 0.0, 0.0) * flax_mask, p["near_light"], 0.35)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.18)
        haze(a, layer, p["low"], 0.08, None)
        return layer
    layer = _air(a, p, "waitangi summer haze", p["low"], 0.22, scale(p["near"], 0.9), 0.14)
    a.put(layer, shafts(a, "waitangi shafts", 4, 0.10, 0.0, 0.85, 0.05), p["glow"], 0.06)
    return layer


def waitangi_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Long blades of flax stand from below at one place, their tips bent
    over, and tufts of long grass at another."""
    del layer_lights
    rng = art_.rand("waitangi foreground")
    u = rng.uniform(0.18, 0.30)
    top = REST_BOTTOM - 0.004
    for k in range(9):
        lean = (k - 4) * 0.022 + rng.uniform(-0.006, 0.006)
        tip = (u + lean * 1.6, top + abs(k - 4) * 0.010 + rng.uniform(0.0, 0.008))
        rib = _arch((u + (k - 4) * 0.004, 1.0), (u + lean * 0.4, tip[1] - 0.02), tip, 12)
        _leaf(pen, rib + [(tip[0] + lean * 0.4, tip[1] + 0.03)], 0.0055, 0.3)
    u = rng.uniform(0.62, 0.74)
    _grass_blades(pen, rng, u, 1.0, 1.0 - REST_BOTTOM + 0.004, 22, 0.0016, 0.05)


# ---------------------------------------------------------------------------
# Sydney Cove: Warrane, 1788
# ---------------------------------------------------------------------------


SYDNEY_COVE = {
    "top": (118, 126, 134),
    "mid": (172, 172, 166),
    "low": (220, 210, 190),
    "glow": (236, 206, 160),
    "sun": (246, 226, 190),
    "cloud": (208, 204, 196),
    "cloud_shadow": (146, 146, 146),
    "water": (94, 112, 116),
    "water_light": (188, 186, 172),
    "water_deep": (62, 78, 84),
    "hills": (120, 128, 120),
    "sandstone": (192, 150, 96),
    "sandstone_light": (222, 192, 140),
    "sandstone_dark": (122, 88, 58),
    "gum": (204, 198, 182),
    "leaf": (108, 120, 100),
    "scrub": (94, 102, 78),
    "hull": (62, 54, 48),
    "sail": (200, 196, 182),
    "tent": (220, 214, 198),
    "tent_shade": (158, 154, 144),
    "stream": (176, 182, 174),
    "canoe": (88, 70, 54),
    "smoke": (190, 188, 182),
    "fire": (226, 150, 84),
    "banksia": (186, 160, 96),
    "grasstree": (52, 46, 38),
    "far": (194, 192, 182),
    "near": (34, 32, 28),
    "near_light": (150, 128, 94),
}

#: The level of the water of the cove at the foot of the headlands.
SYDNEY_WATER = 0.620


def _sandstone_head(u: float, side: float) -> float:
    """The top of a headland of sandstone at one side of the cove: high at
    the edge of the view, and down to the water toward the middle, in
    steps where the beds of the rock break off."""
    if side < 0:
        smooth = float(np.interp(u, [-0.05, 0.10, 0.20, 0.27, 0.33], [0.552, 0.556, 0.570, 0.592, SYDNEY_WATER + 0.004]))
    else:
        smooth = float(np.interp(u, [0.66, 0.72, 0.80, 0.90, 1.05], [SYDNEY_WATER + 0.004, 0.596, 0.574, 0.560, 0.556]))
    if smooth > SYDNEY_WATER:
        return smooth
    return smooth + (0.548 + math.ceil((smooth - 0.548) / 0.008) * 0.008 - smooth) * 0.6


def _tent(canvas: Pen, shade: Pen, u: float, v: float, w: float, h: float) -> None:
    """A small ridge tent of the camp, plain canvas, seen from its end: a
    steep triangle with the dark of its door at the middle."""
    canvas.poly([(u - w, v + 0.001), (u, v - h), (u + w, v + 0.001)])
    shade.poly([(u - w * 0.22, v + 0.001), (u, v - h * 0.55), (u + w * 0.22, v + 0.001)])


def _nawi(hull: Pen, body: Pen, fire: Pen, u: float, v: float, s: float, facing: float = 1.0) -> None:
    """A nawi, a canoe of one sheet of bark, far off on the water: a thin
    low hull with ends that rise a little, a woman who sits in it and
    fishes with a line, and a small fire on a pad of clay in the canoe."""
    f = facing
    hull.poly([(u - s * 0.50, v - s * 0.10), (u - s * 0.36, v - s * 0.02), (u + s * 0.36, v - s * 0.02), (u + s * 0.50, v - s * 0.10), (u + s * 0.38, v + s * 0.03), (u - s * 0.38, v + s * 0.03)])
    body.ellipse(u - f * s * 0.10, v - s * 0.12, s * 0.06, s * 0.10)
    body.ellipse(u - f * s * 0.10, v - s * 0.25, s * 0.04, s * 0.045)
    body.line([(u - f * s * 0.06, v - s * 0.14), (u + f * s * 0.10, v - s * 0.30), (u + f * s * 0.32, v + s * 0.04)], s * 0.008)
    fire.ellipse(u + f * s * 0.20, v - s * 0.04, s * 0.03, s * 0.02)


def _grass_tree(trunk: Pen, leaves: Pen, spike: Pen | None, rng, u: float, v: float, h: float) -> None:
    """A grass tree: a short black trunk, a round skirt of long thin leaves
    that burst from its top and droop to every side, and, on some, one tall
    straight flower spike."""
    top = (u, v - h * 0.40)
    trunk.poly([(u - h * 0.06, v + 0.004), (u + h * 0.06, v + 0.004), (u + h * 0.05, top[1]), (u - h * 0.05, top[1])])
    for k in range(40):
        ang = -180.0 + k * 180.0 / 39.0 + rng.uniform(-3.0, 3.0)
        length = h * rng.uniform(0.28, 0.36)
        tip = polar(*top, length, ang)
        droop = length * 0.55 * abs(math.cos(math.radians(ang))) ** 1.5
        leaves.line([top, polar(*top, length * 0.55, ang), (tip[0], tip[1] + droop)], h * 0.008)
    if spike is not None:
        spike.line([top, (u + rng.uniform(-0.02, 0.02) * h, top[1] - h * 0.85)], h * 0.018)
        spike.line([(u, top[1] - h * 0.30), (u + rng.uniform(-0.01, 0.01) * h, top[1] - h * 0.82)], h * 0.030)


def _banksia(stems: Pen, leaves: Pen, cones: Pen, rng, u: float, v: float, h: float) -> None:
    """A banksia shrub: a few crooked stems, clumps of long stiff leaves
    with toothed edges, and the upright cones of its flowers, dull gold."""
    for k in range(6):
        end = (u + (k - 2.5) * h * 0.18 + rng.uniform(-0.04, 0.04) * h, v - h * rng.uniform(0.50, 0.80) * (1.0 - abs(k - 2.5) * 0.12))
        stems.line([(u + (k - 2.5) * h * 0.03, v + 0.004), ((u + end[0]) * 0.5, (v + end[1]) * 0.5 + h * 0.04), end], h * 0.022)
        for j in range(14):
            ang = -180.0 + j * 180.0 / 13.0 + rng.uniform(-6.0, 6.0)
            length = h * rng.uniform(0.16, 0.24)
            base = (end[0] + rng.uniform(-0.04, 0.04) * h, end[1] + rng.uniform(0.0, 0.16) * h)
            tip = polar(*base, length, ang)
            _leaf(leaves, [base, polar(*base, length * 0.5, ang), tip], h * 0.022, 0.6)
        if k % 2 == 0:
            cones.ellipse(end[0], end[1] - h * 0.07, h * 0.04, h * 0.085)


def history_sydney_cove(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = SYDNEY_COVE
    sun_at = (0.22, HORIZON - 0.05)
    water_v = SYDNEY_WATER
    if layer_key == "sky":
        # A quiet evening of soft overcast, the light low and warm under the
        # cloud at the left, muted. Low grey hills far off round the
        # harbour, and its still water.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.88)), (0.30, p["top"]), (0.50, p["mid"]), (HORIZON - 0.004, p["low"]),
                                 (HORIZON + 0.002, mix(p["water_light"], p["low"], 0.40)), (0.68, mix(p["water"], p["water_light"], 0.40)), (1.0, p["water"])]))
        for k, (centre, half, cover, alpha) in enumerate(((0.18, 0.12, 0.60, 0.55), (0.36, 0.08, 0.55, 0.45), (0.50, 0.05, 0.48, 0.35))):
            clouds = cloud_mask(a, ("sydney cloud", k), centre, half, cells=3.0 + k, cover=cover, soft=0.35, stretch=5.0)
            a.put(layer, clouds, mix(p["cloud"], p["low"], k * 0.25), alpha)
            a.put(layer, clouds * a.band(centre + half * 0.5, half * 0.6), p["cloud_shadow"], 0.18)
        a.light(layer, a.spot(*sun_at, 0.30, 2.0, squash=2.2), p["glow"], 0.40)
        _sun(a, layer, *sun_at, 0.016, p["sun"], p["glow"], 0.30)
        hills, _ = a.ridge("sydney far hills", HORIZON - 0.016, 0.014, cells=3.0, octaves=4)
        a.put(layer, hills * (a.v < HORIZON + 0.002), mix(p["hills"], p["low"], 0.55))
        a.tint(layer, hills * smoothstep(HORIZON - 0.012, HORIZON, a.v) * (a.v < HORIZON + 0.002), p["low"], 0.35)
        lines = smoothstep(0.64, 0.84, a.noise("sydney far water", cells=60.0, octaves=2, stretch=16.0))
        a.light(layer, (a.v > HORIZON + 0.004) * lines, p["water_light"], 0.20)
        a.light(layer, (a.v > HORIZON + 0.002) * a.spot(sun_at[0], HORIZON + 0.03, 0.16, 1.0, squash=0.6) * lines, p["glow"], 0.30)
        a.tint(layer, fog(a, "sydney horizon haze", HORIZON, 0.016, 3.0), p["low"], 0.55)
        _textbook(a, layer, 0.09)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far sydney")
        cols = a.u[0]
        # The two headlands of the cove: Hawkesbury sandstone in level beds
        # with ledges and overhangs, gums and scrub on their tops.
        heads = []
        for side in (-1.0, 1.0):
            line = np.array([_sandstone_head(float(u), side) for u in cols], dtype=np.float32)
            line = line + (a.line_noise(("sydney head", side), cells=20.0, octaves=3) - 0.5) * 0.004
            heads.append(_land(a, line) * (a.v < water_v + 0.004) * ((a.u < 0.36) if side < 0 else (a.u > 0.64)))
        rock = np.maximum(heads[0], heads[1])
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        scrub, scrub_pen = a.drawing()
        for u0, u1, side in ((-0.02, 0.26, -1.0), (0.74, 1.02, 1.0)):
            for _ in range(70):
                u = rng.uniform(u0, u1)
                scrub_pen.ellipse(u, _sandstone_head(u, side) - 0.002, rng.uniform(0.006, 0.012), rng.uniform(0.004, 0.008))
            for _ in range(7):
                u = rng.uniform(u0, u1)
                _gum(trunk_pen, crown_pen, rng, u, _sandstone_head(u, side) + 0.002, rng.uniform(0.06, 0.09))
        # The First Fleet at anchor in the cove, sails furled; Sirius is
        # the largest. The tents of the new camp are small and plain on the
        # low shore at the right, by a small stream.
        ships, ship_pen = a.drawing()
        furled, furled_pen = a.drawing()
        for u, v, s in ((0.40, 0.618, 0.050), (0.49, 0.626, 0.076), (0.585, 0.616, 0.046), (0.635, 0.612, 0.036)):
            _tall_ship(ship_pen, furled_pen, u, v, s, furled=True)
        canvas, canvas_pen = a.drawing()
        tent_shade, tent_shade_pen = a.drawing()
        flat, flat_pen = a.drawing()
        flat_pen.poly([(0.66, water_v + 0.002), (0.68, water_v - 0.006), (0.80, water_v - 0.008), (0.80, water_v + 0.004)])
        for u, w, h in ((0.700, 0.007, 0.010), (0.716, 0.006, 0.009), (0.734, 0.007, 0.010), (0.752, 0.006, 0.009), (0.770, 0.007, 0.010)):
            _tent(canvas_pen, tent_shade_pen, u, water_v - 0.006 + (u - 0.7) * 0.02, w, h)
        stream, stream_pen = a.drawing()
        stream_pen.line([(0.690, water_v - 0.004), (0.694, water_v - 0.010), (0.690, water_v - 0.018), (0.697, water_v - 0.030)], 0.0016)
        # The Eora: the thin smoke of their fires along the far shore at
        # the left, and women who fish from bark canoes on the water, each
        # canoe with its small fire.
        smoke = np.maximum.reduce([_plume(a, ("sydney shore smoke", k), u, _sandstone_head(u, -1.0) + 0.004, 0.08, 0.03, 0.003) for k, u in enumerate((0.11, 0.21))])
        hulls, hull_pen = a.drawing()
        bodies, body_pen = a.drawing()
        fires, fire_pen = a.drawing()
        for u, v, s, f in ((0.32, 0.632, 0.030, 1.0), (0.27, 0.640, 0.026, -1.0)):
            _nawi(hull_pen, body_pen, fire_pen, u, v, s, f)
            smoke = np.maximum(smoke, _plume(a, ("sydney canoe smoke", u), u + f * s * 0.20, v - s * 0.06, 0.05, 0.02, 0.002))
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        scrub_mask = a.mask_of(scrub)
        ship_mask = a.mask_of(ships)
        furled_mask = a.mask_of(furled)
        canvas_mask = a.mask_of(canvas)
        tent_shade_mask = a.mask_of(tent_shade) * canvas_mask
        flat_mask = a.mask_of(flat)
        stream_mask = a.mask_of(stream) * flat_mask
        hull_mask = np.maximum(a.mask_of(hulls), a.mask_of(bodies))
        fire_mask = a.mask_of(fires)
        water = smoothstep(HORIZON + 0.008, HORIZON + 0.012, a.v)
        land = np.maximum.reduce([rock, trunk_mask, crown_mask, scrub_mask, flat_mask, canvas_mask])
        boats = np.maximum(ship_mask, furled_mask)
        mask = np.maximum.reduce([land, boats, hull_mask, water])
        layer = solid(a, mask, mix(p["sandstone"], p["far"], 0.40), mix(p["sandstone"], p["far"], 0.25), 0.55, 0.62, "sydney far", 0.04)
        a.put(layer, water, a.ramp([(0.0, mix(p["water_light"], p["low"], 0.30)), (HORIZON + 0.012, mix(p["water_light"], p["low"], 0.30)),
                                     (0.66, mix(p["water"], p["water_light"], 0.30)), (0.72, p["water"]), (1.0, p["water_deep"])]))
        a.put(layer, _reflected(a, land, water_v, "sydney shore ripple", water * (a.v > water_v)), mix(p["sandstone_dark"], p["water"], 0.50), 0.40)
        a.put(layer, _reflected(a, boats, 0.624, "sydney ship ripple", water * (1.0 - boats) * (a.v > 0.614)), mix(p["hull"], p["water"], 0.55), 0.30)
        lines = smoothstep(0.64, 0.84, a.noise("sydney near lines", cells=60.0, octaves=2, stretch=16.0))
        a.light(layer, water * lines * smoothstep(HORIZON + 0.012, HORIZON + 0.06, a.v), p["water_light"], 0.20)
        # The sandstone: yellow-ochre in level beds, a dark line of shade
        # under each ledge, darker bands of ironstone, and the hollows of
        # honeycomb weathering.
        a.put(layer, rock, mix(p["sandstone"], p["far"], 0.30))
        beds = (a.v - 0.548) / 0.008 % 1.0
        a.put(layer, rock * np.clip(1.0 - beds / 0.18, 0.0, 1.0), mix(p["sandstone_dark"], p["far"], 0.25), 0.55)
        a.light(layer, rock * np.clip((beds - 0.20) / 0.2, 0.0, 1.0) * np.clip((0.45 - beds) / 0.2, 0.0, 1.0), p["sandstone_light"], 0.25)
        a.put(layer, rock * smoothstep(0.66, 0.74, a.noise("sydney ironstone", cells=24.0, octaves=2, stretch=10.0)), mix(p["sandstone_dark"], p["far"], 0.30), 0.35)
        a.shade(layer, rock * smoothstep(0.66, 0.72, a.noise("sydney honeycomb", cells=160.0, octaves=2)), 0.20)
        a.light(layer, a.rim(rock, 0.002, 0.002, 0.2) * rock, p["glow"], 0.35)
        a.put(layer, scrub_mask, mix(p["scrub"], p["far"], 0.30))
        a.put(layer, trunk_mask, mix(p["gum"], p["far"], 0.25))
        a.put(layer, crown_mask, mix(p["leaf"], p["far"], 0.30))
        a.put(layer, flat_mask, mix(p["scrub"], p["far"], 0.35))
        a.put(layer, stream_mask, mix(p["stream"], p["far"], 0.20))
        a.put(layer, canvas_mask, mix(p["tent"], p["far"], 0.15))
        a.put(layer, tent_shade_mask, mix(p["tent_shade"], p["far"], 0.15))
        a.put(layer, ship_mask, mix(p["hull"], p["far"], 0.30))
        a.put(layer, furled_mask, mix(p["sail"], p["far"], 0.20))
        a.put(layer, hull_mask, mix(p["canoe"], p["far"], 0.25))
        a.put(layer, fire_mask, p["fire"], 0.85)
        a.put(layer, smoke, p["smoke"], 0.45)
        mask = np.maximum(mask, smoke * 0.45)
        a.tint(layer, fog(a, "sydney water haze", water_v - 0.004, 0.014, 3.0) * mask, p["low"], 0.35)
        haze(a, layer, p["low"], 0.10, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near sydney")
        bank, ground, bank_at = _bank(a, "near sydney", 0.050, 0.040)
        rock, rock_pen = a.drawing()
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        grass_trees, gt_pen = a.drawing()
        gt_leaves, gt_leaf_pen = a.drawing()
        spikes, spike_pen = a.drawing()
        stems, stem_pen = a.drawing()
        leaves, leaf_pen = a.drawing()
        cones, cone_pen = a.drawing()
        grass, grass_pen = a.drawing()
        # A low outcrop of sandstone with a ledge at the left, and a grass
        # tree on it; a gum and a banksia at the right. The middle is a
        # calm bank of sandy soil and grass.
        base = bank_at(0.10) + 0.010
        rock_pen.poly([(-0.02, 1.0), (-0.02, base - 0.110), (0.05, base - 0.118), (0.10, base - 0.108), (0.115, base - 0.100), (0.118, base - 0.070),
                       (0.150, base - 0.064), (0.170, base - 0.040), (0.200, base - 0.010), (0.22, 1.0)])
        _grass_tree(gt_pen, gt_leaf_pen, spike_pen, rng, 0.055, base - 0.112, 0.20)
        _grass_tree(gt_pen, gt_leaf_pen, None, rng, 0.255, bank_at(0.255) + 0.004, 0.10)
        _gum(trunk_pen, crown_pen, rng, 0.90, bank_at(0.90) + 0.006, 0.62)
        _banksia(stem_pen, leaf_pen, cone_pen, rng, 0.79, bank_at(0.79) + 0.004, 0.12)
        for _ in range(150):
            u = rng.uniform(0.0, 1.0)
            h = rng.uniform(0.005, 0.011) * (1.0 + 0.8 * (abs(u - 0.5) > 0.3))
            v = bank_at(u) + 0.002
            grass_pen.line([(u, v), (u + rng.uniform(-0.004, 0.004), v - h)], 0.0013)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        rock_mask = a.mask_of(rock)
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        gt_mask = a.mask_of(grass_trees)
        gt_leaf_mask = a.mask_of(gt_leaves)
        spike_mask = a.mask_of(spikes)
        stem_mask = a.mask_of(stems)
        leaf_mask = a.mask_of(leaves)
        cone_mask = a.mask_of(cones)
        grass_mask = a.mask_of(grass)
        mask = np.maximum.reduce([bank_mask, rock_mask, trunk_mask, crown_mask, gt_mask, gt_leaf_mask, spike_mask, stem_mask, leaf_mask, cone_mask, grass_mask])
        layer = a.blank()
        earth = a.ramp([(0.0, mix(p["near_light"], p["near"], 0.40)), (0.66, mix(p["near_light"], p["near"], 0.40)), (0.80, mix(p["near_light"], p["near"], 0.75)), (1.0, p["near"])])
        a.put(layer, bank_mask, earth)
        a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, p["glow"], 0.20)
        a.put(layer, rock_mask, mix(p["sandstone"], p["near"], 0.45))
        beds = (a.v * 90.0) % 1.0
        a.shade(layer, rock_mask * np.clip(1.0 - beds / 0.12, 0.0, 1.0), 0.25)
        a.shade(layer, rock_mask * smoothstep(0.70, 0.74, a.noise("sydney near honeycomb", cells=70.0, octaves=2)), 0.18)
        a.light(layer, a.rim(rock_mask, 0.004, 0.003, 0.3) * rock_mask, p["glow"], 0.30)
        a.put(layer, grass_mask, mix(p["scrub"], p["near"], 0.35))
        a.put(layer, trunk_mask, mix(p["gum"], p["near"], 0.42))
        a.light(layer, a.rim(trunk_mask, 0.003, 0.0, 0.0) * trunk_mask, p["glow"], 0.25)
        a.put(layer, crown_mask, mix(p["leaf"], p["near"], 0.38))
        a.put(layer, gt_mask, mix(p["grasstree"], p["near"], 0.30))
        a.put(layer, gt_leaf_mask, mix(p["scrub"], p["near"], 0.30))
        a.put(layer, spike_mask, mix(p["sandstone_dark"], p["near"], 0.40))
        a.put(layer, stem_mask, mix(p["sandstone_dark"], p["near"], 0.45))
        a.put(layer, leaf_mask, mix(p["leaf"], p["near"], 0.35))
        a.put(layer, cone_mask, mix(p["banksia"], p["near"], 0.35))
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.18)
        haze(a, layer, p["low"], 0.12, None)
        return layer
    layer = _air(a, p, "sydney evening haze", p["low"], 0.30, scale(p["near"], 0.8), 0.18)
    return layer


def sydney_cove_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """A branch of a gum hangs into the top of the view at one place, with
    long narrow leaves that hang down from its twigs. A few tufts of grass
    stand from below at one place."""
    del layer_lights
    rng = art_.rand("sydney foreground")
    u0 = rng.uniform(0.56, 0.72)
    branch = _arch((u0 + 0.28, 0.0), (u0 + 0.10, 0.12), (u0 - 0.10, 0.22), 16)
    for i in range(len(branch) - 1):
        pen.line([branch[i], branch[i + 1]], 0.008 * (1.0 - 0.6 * i / 16.0))
    for i in range(3, 17, 2):
        x, y = branch[i]
        twig_end = (x + rng.uniform(-0.03, 0.03), min(0.33, y + rng.uniform(0.04, 0.07)))
        pen.line([(x, y), twig_end], 0.0014)
        for _ in range(4):
            sx = x + (twig_end[0] - x) * rng.uniform(0.3, 1.0)
            sy = y + (twig_end[1] - y) * rng.uniform(0.3, 1.0)
            length = rng.uniform(0.035, 0.050)
            tip = (sx + rng.uniform(-0.012, 0.012), min(0.376, sy + length))
            _leaf(pen, _arch((sx, sy), (sx + (tip[0] - sx) * 0.2 + 0.006, (sy + tip[1]) * 0.5), tip, 8), 0.0042, 0.5)
    u = rng.uniform(0.18, 0.30)
    _grass_blades(pen, rng, u, 1.0, 1.0 - REST_BOTTOM + 0.004, 18, 0.0015, 0.05)
