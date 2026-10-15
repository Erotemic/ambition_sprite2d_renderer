"""The terraces of the Math town: what a body climbs, and what is built in the rock.

Scenery (LDtk `Prop`s, decoration, no collision) for the street room
(`math_town_street`), which climbs from the street to two terraces and the
summit, under an aqueduct whose deck runs across the whole town:

- ``math_aqueduct_span_street`` / ``_t1`` / ``_t2``: one span of the aqueduct,
  its deck at the top of the frame and its pier at the left edge, down to the
  street, the first terrace or the second. The room sets one beside the next;
  the deck is walked on a still platform the room places.
- ``math_switchback_stair``: the stair from the street to the first terrace,
  two flights and a landing on a pier. The room puts a still one-way platform
  under each tread (``STEP_RISE`` by ``FLIGHT_1_RUN`` or ``FLIGHT_2_RUN``).
- ``math_tunnel_bay``, ``math_tunnel_mouth``, ``math_tunnel_gate``: the street
  goes on under the first terrace in a vaulted passage with lamps in its
  vault, to a shut gate (the long way round, for later).
- ``math_cliff_home_wide`` / ``_narrow``: homes cut in the face of the rock.
- ``math_cypress``, ``math_olive``: trees.

Each frame is drawn in world units at ``PX`` pixels to the unit, and the art
fills its frame to every edge, so a room places the prop's box on the frame.
The light top edge of a thing is where a body can stand. The look-dev these
come from is ``untracked/art-candidates/town/town_vertical.py``.

Animations:

- ``idle``: 1 frame.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import numpy as np
from PIL import Image

from ...authoring.sheet_build import build_sheet
from ._town_kit import Canvas, Kit, box, mix, scale

#: Pixels of the frame to one world unit.
PX = 2

PAL = {
    "stone": (214, 206, 190), "stone_light": (246, 240, 226), "trim": (246, 242, 232), "dark": (40, 52, 70),
    "glass_top": (110, 170, 214), "glass_low": (50, 90, 130), "lamp": (255, 210, 140), "wood": (96, 70, 52),
    "leaf": (70, 128, 80), "iron": (36, 48, 64), "brass": (200, 150, 70), "glaze": (226, 180, 70),
}
LIMESTONE = (228, 216, 192)
WHITE = (246, 244, 238)
BLUE = (60, 110, 180)
TERRACOTTA = (184, 100, 70)
AIR = (214, 226, 240)
WALK = (255, 255, 252)

#: The aqueduct: a span's width, its deck, the band of its arches, and the
#: height of each kind of span (deck top to the foot of its pier).
SPAN_W = 160
PIER_W = 16
DECK_H = 16
BAND_H = 32
SPAN_HEIGHTS = {"street": 720, "t1": 464, "t2": 224}

#: The stair: the rise of every tread, the run of a tread of each flight, the
#: landing, and the frame (the street is its bottom, the terrace its top).
STEP_RISE = 4
FLIGHT_1_RUN = 8
FLIGHT_2_RUN = 9
FLIGHT_RISE = 128
STEPS = FLIGHT_RISE // STEP_RISE
LANDING_W = 64
STAIR_W = LANDING_W + STEPS * FLIGHT_1_RUN
STAIR_H = 2 * FLIGHT_RISE
#: Where flight 2 leaves the landing: the landing goes on past it, to the
#: left, so a body can turn there.
FLIGHT_2_X0 = STAIR_W - STEPS * FLIGHT_2_RUN

#: The passage under the first terrace: a bay of it, its mouth, its gate.
TUNNEL_H = 96
BAY_W = 160
MOUTH_W = 32
MOUTH_H = TUNNEL_H + 16
GATE_W = 48


# ---------------------------------------------------------------------------
# Stone
# ---------------------------------------------------------------------------


def _hash(a: np.ndarray, b: np.ndarray, salt: int) -> np.ndarray:
    v = (a.astype(np.int64) * 73856093) ^ (b.astype(np.int64) * 19349663) ^ salt
    return ((v * 2654435761) % 4096) / 4096.0


def ashlar(c: Canvas, m: np.ndarray, colour, course=12.0, length=24.0, salt=7) -> None:
    """Courses of cut stone where `m` is: each stone its own tone, the joints
    dark, a light line on each stone's top edge."""
    row = np.floor(c.y / course)
    off = (row % 2) * length * 0.5 + _hash(row, row * 0, salt) * 6
    col = np.floor((c.x + off) / length)
    tone = _hash(row, col, salt) - 0.5
    fy = (c.y / course) % 1.0
    fx = ((c.x + off) / length) % 1.0
    joint = np.maximum(np.clip(1 - fy * course / 0.9, 0, 1), np.clip(1 - fx * length / 0.9, 0, 1))
    top = np.clip(1 - (fy * course - 0.9) / 1.4, 0, 1) * (fy * course > 0.9)
    c.put(m, colour)
    c.tone(m * tone, 0.16)
    c.tone(m * (c.noise(("ash", salt), 8, 8, 3) - 0.5), 0.08)
    c.put(m * top, mix(colour, WALK, 0.5), 0.35)
    c.put(m * joint, scale(colour, 0.66), 0.7)


def walk_line(c: Canvas, x0: float, x1: float, y: float, colour) -> None:
    """The one light, hard line of a place to stand."""
    c.put(c.mask(box(x0, y, x1, y + 3.0)), mix(colour, WALK, 0.35))
    c.put(c.mask(box(x0, y, x1, y + 1.2)), WALK)


def vines(c: Canvas, x: float, y_top: float, length: float, tag) -> None:
    rng = c.rand("vine", tag)
    leaves = c.mask(lambda p: [p.ellipse(x + rng.uniform(-6, 6) * (t / length + 0.3), y_top + t, rng.uniform(1.6, 3.2), rng.uniform(1.2, 2.2)) for t in np.arange(0, length, 1.6)])
    c.put(leaves, (70, 120, 70))
    c.tone(leaves * (c.noise(("vn", tag), 20, 60, 1) - 0.5), 0.4)
    blooms = c.mask(lambda p: [p.ellipse(x + rng.uniform(-6, 6) * (t / length + 0.3), y_top + t, 1.2) for t in np.arange(0, length * 0.7, 7)])
    c.put(blooms, (214, 90, 140))


# ---------------------------------------------------------------------------
# The aqueduct
# ---------------------------------------------------------------------------


def _arch_band(c: Canvas, y0: float, h: float) -> np.ndarray:
    """A band from the pier to the next one, with the arch cut out under it:
    the opening's crown is a little under the band's top."""
    rx = (SPAN_W - PIER_W) / 2
    cx = PIER_W + rx
    band = c.mask(box(0, y0, SPAN_W, y0 + h))
    arch = c.mask(lambda p: p.ellipse(cx, y0 + h, rx, h - 5)) * (c.y > y0 + 4)
    return np.clip(band - arch, 0, 1)


def _aqueduct_span(height: int, tag: str) -> Callable[[], Image.Image]:
    def draw() -> Image.Image:
        c = Canvas(f"aqueduct_{tag}", SPAN_W, height, origin=(0.0, 0.0), ppu=PX)
        stone = (232, 226, 210)
        deck = c.mask(box(0, 0, SPAN_W, DECK_H))
        pier = c.mask(box(0, DECK_H, PIER_W, height))
        parts = [deck, pier, _arch_band(c, DECK_H, BAND_H)]
        # A tall span has a second tier of arches half way down, as the
        # aqueducts that cross a valley do.
        mid = None
        if height > 600:
            mid = DECK_H + (height - DECK_H) * 0.46
            parts.append(_arch_band(c, mid, 24))
        via = np.clip(sum(parts), 0, 1)
        ashlar(c, via, stone, course=12, length=22, salt=50)
        # The capital where each band meets the pier, and the pier's base.
        for y in [DECK_H + BAND_H] + ([mid + 24] if mid else []):
            c.put(c.mask(box(0, y - 2, PIER_W + 3, y + 2)), mix(stone, WALK, 0.3))
            c.tone(c.mask(box(0, y + 2, PIER_W + 3, y + 4)), -0.15)
        c.put(c.mask(box(0, height - 10, PIER_W + 4, height)), scale(stone, 0.95))
        c.put(c.mask(box(0, height - 10, PIER_W + 4, height - 8.8)), mix(stone, WALK, 0.4))
        # The deck's coping: the walk line, and the drip edge under it.
        walk_line(c, 0, SPAN_W, 0, stone)
        c.put(c.mask(box(0, DECK_H - 2, SPAN_W, DECK_H)), scale(stone, 0.82))
        # Lit from the left; the side of the pier away from the sun in shade.
        c.tone(pier * np.clip((c.x - PIER_W * 0.55) / (PIER_W * 0.45), 0, 1), -0.16)
        c.tone(pier * np.clip((c.y - DECK_H - 200) / 600, 0, 1), -0.12)
        # A little of the air on it: it stands behind the houses.
        c.tint(via, AIR, 0.08)
        if tag == "street":
            vines(c, PIER_W * 0.5, DECK_H + BAND_H, 110, "aq_street")
        elif tag == "t1":
            vines(c, PIER_W * 0.5, DECK_H + BAND_H, 70, "aq_t1")
        return c.image()

    return draw


# ---------------------------------------------------------------------------
# The stair
# ---------------------------------------------------------------------------


def stair_treads() -> List[Tuple[float, float, float]]:
    """Each tread as (x0, x1, top) in the stair's frame: flight 1 climbs left
    from the foot of the cliff (the frame's right) to the landing, flight 2
    climbs right from the landing to the top of the cliff. The room puts a
    still platform under each one; this is its one statement of them."""
    out = []
    for j in range(1, STEPS + 1):
        x1 = STAIR_W - FLIGHT_1_RUN * (j - 1)
        out.append((x1 - FLIGHT_1_RUN, x1, STAIR_H - STEP_RISE * j))
    for j in range(1, STEPS + 1):
        x0 = FLIGHT_2_X0 + FLIGHT_2_RUN * (j - 1)
        out.append((x0, x0 + FLIGHT_2_RUN, FLIGHT_RISE - STEP_RISE * j))
    return out


def _stair() -> Image.Image:
    c = Canvas("switchback_stair", STAIR_W, STAIR_H, origin=(0.0, 0.0), ppu=PX)
    treads = stair_treads()
    f1, f2 = treads[:STEPS], treads[STEPS:]
    land = FLIGHT_RISE
    stone = (226, 214, 190)
    # The landing on its pier, down to the street.
    pier = c.mask(lambda p: (p.rect(0, land, LANDING_W - 16, STAIR_H), p.rect(0, land, LANDING_W, land + 12)))
    ashlar(c, pier, scale(stone, 0.94), course=10, length=20, salt=61)
    c.put(c.mask(box(0, STAIR_H - 8, LANDING_W - 12, STAIR_H)), scale(stone, 0.9))
    # Flight 1 rides a stringer, open under it so the street goes under.
    lo, hi = (STAIR_W, STAIR_H), (LANDING_W, land)
    stringer1 = c.mask(lambda p: p.poly([(LANDING_W, land), (STAIR_W, STAIR_H), (STAIR_W, STAIR_H + 1), (LANDING_W, land + 14)]))
    steps1 = c.mask(lambda p: [p.rect(x0, top, x1 + 0.4, top + STEP_RISE + 6) for x0, x1, top in f1])
    ashlar(c, np.clip(stringer1 + steps1, 0, 1), stone, course=STEP_RISE * 2, length=18, salt=62)
    # Flight 2, over it, on its own stringer from the landing to the cliff.
    stringer2 = c.mask(lambda p: p.poly([(FLIGHT_2_X0, land), (STAIR_W, 0), (STAIR_W, 14), (FLIGHT_2_X0, land + 14)]))
    steps2 = c.mask(lambda p: [p.rect(x0, top, x1 + 0.4, top + STEP_RISE + 2) for x0, x1, top in f2])
    m2 = np.clip(stringer2 + steps2, 0, 1)
    ashlar(c, m2, mix(stone, WALK, 0.12), course=STEP_RISE * 2, length=18, salt=63)
    c.tone(stringer2 * c.mask(lambda p: p.poly([(FLIGHT_2_X0, land + 8), (STAIR_W, 8), (STAIR_W, 14), (FLIGHT_2_X0, land + 14)])), -0.22)
    # Each tread's top is a walk line.
    c.put(c.mask(lambda p: [p.rect(x0, top, x1, top + 1.2) for x0, x1, top in treads]), WALK)
    c.put(c.mask(box(0, land, LANDING_W, land + 1.2)), WALK)
    # Iron rails on the open side of each flight.
    iron = PAL["iron"]
    off = 26

    def rail(p, a, b, n):
        p.line([(a[0], a[1] - off), (b[0], b[1] - off)], 1.1)
        for t in np.linspace(0.04, 0.96, n):
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            p.rect(x - 0.5, y - off, x + 0.5, y)

    c.put(c.mask(lambda p: (rail(p, lo, hi, 11), rail(p, (FLIGHT_2_X0 + 2, land), (STAIR_W - 2, 2), 13))), iron)
    return c.image()


# ---------------------------------------------------------------------------
# The passage under the terrace
# ---------------------------------------------------------------------------


def _tunnel_bay() -> Image.Image:
    c = Canvas("tunnel_bay", BAY_W, TUNNEL_H, origin=(0.0, 0.0), ppu=PX)
    back = c.mask(box(0, 0, BAY_W, TUNNEL_H))
    ashlar(c, back, (92, 96, 112), course=10, length=20, salt=70)
    # The vault: two arches of the bay, the ribs light, the web dark.
    for x0 in (0, BAY_W / 2):
        web = c.mask(lambda p: p.ellipse(x0 + BAY_W / 4, 0, BAY_W / 4, 22))
        c.tone(web, -0.35)
        c.put(c.mask(lambda p: p.ring(x0 + BAY_W / 4, 0, BAY_W / 4, 1.6)) * (c.y < 24), (168, 170, 180))
    # A doorway and a window in the back wall: the passage is lived in.
    k = Kit(c, PAL, sun=-1)
    k.ground = TUNNEL_H
    k.door(46, 22, 44, (90, 70, 56), arch=True, step=False, tag="bay_door")
    k.window(114, TUNNEL_H - 52, 14, 20, "arch", lit=0.7, tag="bay_win")
    # The lamp in the vault and its light on the wall.
    lx = BAY_W / 2
    c.put(c.mask(box(lx - 0.5, 0, lx + 0.5, 12)), PAL["iron"])
    c.put(c.mask(lambda p: p.ellipse(lx, 15, 3.2)), mix(PAL["lamp"], WALK, 0.4))
    c.light(c.mask(lambda p: p.ellipse(lx, 30, 46, 34), blur=10), PAL["lamp"], 0.38)
    # The floor's edge under the wall.
    c.tone(c.mask(box(0, TUNNEL_H - 4, BAY_W, TUNNEL_H)), -0.25)
    return c.image()


def _tunnel_mouth() -> Image.Image:
    c = Canvas("tunnel_mouth", MOUTH_W, MOUTH_H, origin=(0.0, 0.0), ppu=PX)
    jamb = c.mask(box(0, 0, MOUTH_W, MOUTH_H))
    ashlar(c, jamb, WHITE, course=10, length=16, salt=41)
    c.put(c.mask(box(0, 0, MOUTH_W, 3)), mix(WHITE, WALK, 0.5))
    c.tone(c.mask(box(MOUTH_W - 6, 6, MOUTH_W, MOUTH_H)), -0.2)
    return c.image()


def _tunnel_gate() -> Image.Image:
    c = Canvas("tunnel_gate", GATE_W, TUNNEL_H, origin=(0.0, 0.0), ppu=PX)
    c.put(c.mask(box(0, 0, GATE_W, TUNNEL_H)), (40, 44, 58))
    iron = PAL["iron"]
    bars = c.mask(lambda p: ([p.rect(x, 0, x + 2.2, TUNNEL_H) for x in np.arange(3, GATE_W, 7)], [p.rect(0, y, GATE_W, y + 2.2) for y in (14, 50, 84)]))
    c.put(bars, mix(iron, (90, 100, 120), 0.4))
    # Spikes along the bottom, and the plaque: the long way round.
    c.put(c.mask(lambda p: [p.poly([(x, TUNNEL_H - 6), (x + 2.2, TUNNEL_H - 6), (x + 1.1, TUNNEL_H)]) for x in np.arange(3, GATE_W, 7)]), iron)
    c.put(c.mask(box(GATE_W / 2 - 10, 26, GATE_W / 2 + 10, 40)), PAL["brass"])
    c.put(c.mask(lambda p: p.line([(GATE_W / 2 + 6 * math.cos(t) / (1 + math.sin(t) ** 2), 33 + 6 * math.sin(t) * math.cos(t) / (1 + math.sin(t) ** 2)) for t in np.linspace(0, math.tau, 60)], 0.9)), PAL["iron"])
    return c.image()


# ---------------------------------------------------------------------------
# Homes in the rock
# ---------------------------------------------------------------------------

CLIFF_HOMES = {"wide": (150, 92), "narrow": (76, 104)}


def _cliff_home(kind: str) -> Callable[[], Image.Image]:
    w, h = CLIFF_HOMES[kind]

    def draw() -> Image.Image:
        c = Canvas(f"cliff_home_{kind}", w, h, origin=(0.0, 0.0), ppu=PX)
        k = Kit(c, PAL, sun=-1)
        x0, x1, eave = 6.0, w - 6.0, 10.0
        if kind == "wide":
            k.wall(x0, eave, x1, h, (238, 222, 196), "plaster", tag="cliff_wide")
            for cx in (32, 75, 118):
                k.window(cx, eave + 16, 14, 24, "arch", shutters=BLUE if cx != 75 else None, lit=0.5 if cx == 75 else 0.0, tag=("cw", cx))
            k.flowerbox(24, 52, eave + 42, (230, 80, 90), "cw_flowers")
            k.window(75, eave + 52, 18, 26, "rect", tag="cw_low")
        else:
            k.wall(x0, eave, x1, h, (246, 244, 238), "plaster", tag="cliff_narrow")
            k.window(w / 2, eave + 14, 14, 26, "arch", shutters=TERRACOTTA, tag="cn_top")
            k.balcony(x0 + 8, x1 - 8, eave + 58, (232, 226, 214))
            k.window(w / 2, eave + 62, 16, 28, "arch", lit=0.6, tag="cn_low")
        # A face built into the rock: a cornice over it, and the rock's
        # reveal at each side.
        wall = (238, 222, 196) if kind == "wide" else (246, 244, 238)
        c.put(c.mask(box(0, eave - 6, w, eave + 1)), mix(wall, WALK, 0.25))
        c.put(c.mask(box(0, eave - 6, w, eave - 4.8)), WALK)
        c.tone(c.mask(box(0, eave + 1, w, eave + 5)), -0.18)
        c.put(c.mask(lambda p: (p.rect(0, eave, x0, h), p.rect(x1, eave, w, h))), scale(wall, 0.78))
        return c.image()

    return draw


# ---------------------------------------------------------------------------
# Trees
# ---------------------------------------------------------------------------

CYPRESS = (24, 128)
OLIVE = (64, 52)


def _cypress() -> Image.Image:
    w, h = CYPRESS
    c = Canvas("cypress", w, h, origin=(0.0, 0.0), ppu=PX)
    x, ground = w / 2, h
    c.put(c.mask(box(x - 1.5, ground - 10, x + 1.5, ground)), (90, 70, 50))
    tall = h - 8

    def outline(p):
        pts = []
        for t in np.linspace(0, 1, 24):
            pts.append((x + 11.5 * math.sin(math.pi * t) ** 0.7 * (1 - t * 0.25), ground - 6 - tall * t))
        for t in np.linspace(1, 0, 24):
            pts.append((x - 11.5 * math.sin(math.pi * t) ** 0.7 * (1 - t * 0.25), ground - 6 - tall * t))
        p.poly(pts)

    body = c.mask(outline)
    c.put(body, (54, 92, 62))
    c.tone(body * np.clip((c.x - x) / 9, 0, 1), -0.22)
    c.tone(body * (c.noise("cyp", 6, 30, 2) - 0.5), 0.35)
    c.light(body * np.clip((x - c.x) / 9, 0, 1), (255, 240, 200), 0.18)
    return c.image()


def _olive() -> Image.Image:
    w, h = OLIVE
    c = Canvas("olive", w, h, origin=(0.0, 0.0), ppu=PX)
    x, ground = w / 2, h
    rng = c.rand("olive")
    c.put(c.mask(lambda p: (p.line([(x, ground), (x - 2, ground - 16), (x + 3, ground - 28)], 3.0), p.line([(x - 1, ground - 18), (x - 12, ground - 28)], 1.6))), (110, 92, 72))
    crown = c.mask(lambda p: [p.ellipse(x + rng.uniform(-20, 20), ground - 36 + rng.uniform(-8, 6), rng.uniform(8, 12), rng.uniform(5, 8)) for _ in range(14)])
    c.put(crown, (110, 138, 96))
    c.tone(crown * (c.noise("olv", 16, 12, 2) - 0.5), 0.4)
    c.light(crown * np.clip((x - c.x) / 30 + 0.3, 0, 1) * np.clip((ground - 30 - c.y) / 14, 0, 1), (255, 246, 214), 0.25)
    return c.image()


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------

#: Each target: its frame in world units, and how to draw it.
PIECES: Dict[str, Tuple[Tuple[int, int], Callable[[], Image.Image]]] = {
    **{f"math_aqueduct_span_{tag}": ((SPAN_W, h), _aqueduct_span(h, tag)) for tag, h in SPAN_HEIGHTS.items()},
    "math_switchback_stair": ((STAIR_W, STAIR_H), _stair),
    "math_tunnel_bay": ((BAY_W, TUNNEL_H), _tunnel_bay),
    "math_tunnel_mouth": ((MOUTH_W, MOUTH_H), _tunnel_mouth),
    "math_tunnel_gate": ((GATE_W, TUNNEL_H), _tunnel_gate),
    **{f"math_cliff_home_{kind}": (size, _cliff_home(kind)) for kind, size in CLIFF_HOMES.items()},
    "math_cypress": (CYPRESS, _cypress),
    "math_olive": (OLIVE, _olive),
}


def _frame_size(name: str) -> Tuple[int, int]:
    (w, h), _ = PIECES[name]
    return (int(w * PX), int(h * PX))


def _actor(name: str) -> dict:
    return {
        "actor": {"character_id": f"prop_{name}", "display_name": name.replace("_", " ").title()},
        "body": {"body_plan": "Prop", "body_kind": "Scenery", "mass_class": "Heavy", "locomotion_hint": "Static", "traits": ["prop", "scenery"]},
        "brain": {"default_preset": "stand_still"},
        "actions": {"default_preset": "peaceful"},
        "animation_bindings": {"default": {"animation": "idle", "events": []}},
        "tags": ["prop", "scenery"],
    }


def _renderer(name: str):
    _, draw = PIECES[name]

    def render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
        del frame_idx, nframes
        if anim != "idle":
            raise ValueError(f"unknown animation: {anim}")
        return draw()

    def frame_meta(anim: str, frame_idx: int, nframes: int) -> dict:
        del anim, frame_idx, nframes
        fw, fh = _frame_size(name)
        return {"anchors": {"foot": {"x": fw / 2, "y": float(fh)}}, "forward": {"x": 0.0, "y": -1.0}, "angle_deg": 0.0}

    def render(out_dir: str | Path, **opts) -> List[Path]:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        outputs = build_sheet(
            target=name,
            rows=[("idle", 1, 400)],
            render_fn=render_frame,
            out_dir=out_dir,
            frame_size=_frame_size(name),
            frame_meta_fn=frame_meta,
            auto_crop=False,
            actor_metadata=_actor(name),
        )
        return [outputs[key] for key in ("canonical", "canonical_transparent", "spritesheet", "yaml", "ron", "actor", "preview")]

    return render


TARGETS = {name: {"render": _renderer(name), "actor_metadata": _actor(name)} for name in PIECES}

__all__ = ["PIECES", "PX", "TARGETS", "stair_treads", "STEP_RISE", "STAIR_W", "STAIR_H", "LANDING_W", "FLIGHT_RISE"]
