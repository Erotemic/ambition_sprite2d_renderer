"""Standalone generator for a Flying Spaghetti Monster boss sprite sheet.

Large floating boss for the side scroller, rendered procedurally with PIL.
The silhouette leans into the iconic two meatballs, looping noodles, and
stalk-eyes, with bossy attack animations:
- hover / drift
- noodle whip lash
- meatball volley spit
- eye beam glare
- hurt / death feedback

Generator only. No registration or GUI wiring.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from contextlib import contextmanager
from typing import List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw

from ...authoring import rigdoc
from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw
from . import _solo_shape_rig as SR

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "flying_spaghetti_monster_boss"
# Output (post-downsample) frame resolution. This is a BOSS that renders much
# larger on screen than a normal character, so its texture needs proportionally
# more native pixels to stay crisp — a normal character (the player) ships at a
# 256 native frame and reads sharp at its small on-screen size; a boss displayed
# 2-3x larger needs ~2-3x the native pixels for the same crispness. The body
# fills ~half the frame, so a (800,640) frame yields a ~400px body. Geometry is
# authored in WORK_FRAME_SIZE units and supersampled by SUPER, so raising the
# downsample target just preserves more of that detail (no redraw, no gameplay
# change — display size is collision-driven).
WORK_FRAME_SIZE = (860, 800)
# The same aspect as the work frame, so the downsample never squashes: the
# frame is a uniform 0.87 of the work units.
FRAME_SIZE = (748, 696)
SUPER = 4
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 132),
    ("drift", 8, 98),
    ("noodle_whip", 7, 86),
    ("meatball_volley", 7, 88),
    ("eye_beam", 7, 90),
    ("hurt", 4, 96),
    ("death", 8, 112),
    # Rows past the engine's seven `BossAnim` kinds. The fight's conductor
    # pins them by name; they come AFTER the seven because the engine's sheet
    # spec indexes those by position in the PNG.
    ("pulse", 8, 84),
    ("dive", 8, 84),
    ("grasp", 8, 90),
    ("summon", 8, 96),
]

# Publish authoritative per-animation hurtboxes keyed by the GENERIC gameplay
# keys the boss combat looks animations up by (NOT these row names) — mirrors the
# Rust `FLYING_SPAGHETTI_MONSTER_SHEET` BossAnim mapping (idle→Rest,
# drift→DashEcho, noodle_whip→SideSweep, meatball_volley→FloorSlam,
# eye_beam→SpikeHalo, hurt→Hit, death→Death). Without this the boss falls back to
# the coarse idle alpha bbox (the whole noodle spread) for every pose; with it,
# the player's attacks register on the per-pose body.
# Rows that loop sample a whole cycle; the rest play once, first to last.
LOOPING_ROWS = {"idle", "drift"}

ANIMATION_KEY_MAP = {
    "idle": "rest",
    "drift": "dash_echo",
    "noodle_whip": "side_sweep",
    "meatball_volley": "floor_slam",
    "eye_beam": "spike_halo",
    "hurt": "hit",
    "death": "death",
    "pulse": "pulse",
    "dive": "dive",
    "grasp": "grasp",
    "summon": "summon",
}

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_flying_spaghetti_monster_boss",
        "display_name": "Flying Spaghetti Monster Boss",
    },
    "body": {
        "body_plan": "BossMultipart",
        "body_kind": "Wide",
        "mass_class": "Boss",
        "locomotion_hint": "BossFloat",
        "traits": ["boss", "floating", "multipart", "no_hands", "noodle", "ranged"],
    },
    "capabilities": {
        "traversal": {
            "walk": False,
            "jump": None,
            "climb": None,
            "crawl": None,
            "fly": True,
            "swim": None,
            "use_lifts": None,
            "door_access": [],
        },
        "interactions": {
            "talk": None,
            "trade": None,
            "carry": None,
            "open_doors": [],
        },
    },
    "brain": {"default_preset": "boss_pattern"},
    "actions": {"default_preset": "fsm_boss_specials"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.hover": {"animation": "drift", "events": []},
        "action.melee.primary": {
            "animation": "noodle_whip",
            "events": [
                {
                    "t": 0.34,
                    "event": "hitbox_active_start",
                    "source": "flying_spaghetti_monster_boss.noodle_whip",
                },
                {
                    "t": 0.62,
                    "event": "hitbox_active_end",
                    "source": "flying_spaghetti_monster_boss.noodle_whip",
                },
            ],
        },
        "action.ranged.primary": {
            "animation": "meatball_volley",
            "events": [
                {
                    "t": 0.48,
                    "event": "projectile_release",
                    "source": "flying_spaghetti_monster_boss.meatball_volley",
                }
            ],
        },
        "action.special.eye_beam": {
            "animation": "eye_beam",
            "events": [
                {
                    "t": 0.44,
                    "event": "beam_active_start",
                    "source": "flying_spaghetti_monster_boss.eye_beam",
                },
                {
                    "t": 0.72,
                    "event": "beam_active_end",
                    "source": "flying_spaghetti_monster_boss.eye_beam",
                },
            ],
        },
        "damage.hit": {"animation": "hurt", "events": []},
        "lifecycle.death": {"animation": "death", "events": []},
    },
    "sockets": {
        "core": {
            "source": "flying_spaghetti_monster_boss.geometry",
            "point": {"x": 160.0, "y": 136.0},
        },
        "meatball_l": {
            "source": "flying_spaghetti_monster_boss.geometry",
            "point": {"x": 126.0, "y": 140.0},
        },
        "meatball_r": {
            "source": "flying_spaghetti_monster_boss.geometry",
            "point": {"x": 192.0, "y": 138.0},
        },
        "eye_l": {
            "source": "flying_spaghetti_monster_boss.geometry",
            "point": {"x": 116.0, "y": 40.0},
        },
        "eye_r": {
            "source": "flying_spaghetti_monster_boss.geometry",
            "point": {"x": 220.0, "y": 42.0},
        },
        "beam_l": {
            "source": "flying_spaghetti_monster_boss.geometry",
            "point": {"x": 116.0, "y": 40.0},
        },
        "beam_r": {
            "source": "flying_spaghetti_monster_boss.geometry",
            "point": {"x": 220.0, "y": 42.0},
        },
        "noodle_tip": {
            "source": "flying_spaghetti_monster_boss.geometry",
            "point": {"x": 252.0, "y": 150.0},
        },
        "projectile_origin": {
            "source": "flying_spaghetti_monster_boss.geometry",
            "point": {"x": 190.0, "y": 132.0},
        },
    },
    "tags": ["boss", "floating", "multipart"],
}


ACTOR_METADATA.update(
    {
        "authoring_description": (
            "The Flying Spaghetti Monster Boss turns the Flying Spaghetti Monster satire into a "
            "sincere, oversized noodle deity. It should preserve the affectionate absurdity of the "
            "original parody religion: noodly appendages, marinara grace, and mock-theological "
            "confidence rather than generic pasta jokes."
        ),
        "gameplay_description": (
            "Use as a floating boss, strange benefactor, faction deity, or comic source of blessings. "
            "Attacks should extend through noodles, meatballs, sauce, and improbable grace; speech "
            "should sound doctrinal while remaining knowingly ridiculous."
        ),
    }
)
ACTOR_METADATA.setdefault("dialogue_hints", {}).setdefault(
    "barks",
    [
        'You came within range of My noodly appendage, and so you are blessed.',
        'Everything is sacred if you season it correctly.',
        'You have been touched by marinara. Ramen.',
    ],
)

OUTLINE = (58, 40, 30, 255)
NOODLE = (240, 222, 172, 255)
NOODLE_BACK = (206, 184, 134, 255)
NOODLE_DEEP = (170, 146, 102, 255)
NOODLE_SHADE = (212, 190, 140, 255)
NOODLE_HI = (253, 244, 214, 255)
MEATBALL = (140, 78, 50, 255)
MEATBALL_SHADE = (96, 50, 32, 255)
MEATBALL_HI = (184, 116, 78, 255)
MEATBALL_CRUMB = (78, 40, 26, 255)
SAUCE = (196, 52, 34, 245)
SAUCE_DARK = (138, 30, 22, 245)
SAUCE_HI = (240, 118, 88, 230)
EYE = (250, 246, 238, 255)
EYE_GLOW = (255, 236, 150, 255)
IRIS = (84, 58, 40, 255)
PUPIL = (26, 18, 16, 255)
BEAM = (255, 250, 222, 205)
BEAM2 = (255, 226, 140, 120)
IMPACT = (255, 244, 200, 170)

# The geometry frame is the socket frame (`ACTOR_METADATA["sockets"]`): the
# body's root sits at (160, 152), and the bell's centre at (160, 131). The
# canvas puts the BELL'S CENTRE AT THE FRAME'S CENTRE, so the drawn body, the
# boss's position and its collision box coincide with no offset for the
# engine to derive; the noodles hang into the lower half and the lash reaches
# into the right, and the packer trims the empty space either way.
ROOT = (160.0, 152.0)
BELL_CENTRE = (160.0, 131.0)
CANVAS_MARGIN = (WORK_FRAME_SIZE[0] / 2 - BELL_CENTRE[0], WORK_FRAME_SIZE[1] / 2 - BELL_CENTRE[1])


#: Canvas pixels per geometry unit. The canvas is the FRAME supersampled by
#: SUPER (a whole factor, so a part flipbook reduces each piece on the frame's
#: own grid and can place turned pieces): the work frame's geometry drawn at
#: SUPER * 748 / 860.
SCALE = SUPER * FRAME_SIZE[0] / WORK_FRAME_SIZE[0]
CANVAS_SIZE = (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER)
#: Canvas pixels subtracted from every point: a piece painted on its own small
#: canvas (``_piece``) shifts the geometry onto it.
_SHIFT = (0, 0)


def _s(v: float) -> int:
    return int(round(v * SCALE))


def _pt(p: Point) -> Tuple[int, int]:
    return (_s(p[0] + CANVAS_MARGIN[0]) - _SHIFT[0], _s(p[1] + CANVAS_MARGIN[1]) - _SHIFT[1])


def _cv(p: Point) -> Point:
    """A geometry point in canvas pixels, unrounded (where a piece lands)."""
    return ((p[0] + CANVAS_MARGIN[0]) * SCALE, (p[1] + CANVAS_MARGIN[1]) * SCALE)


def _piece(key: tuple, centre: Point, half: Point, paint):
    """A piece painted once by ``paint(draw)`` in GEOMETRY coordinates on its
    own canvas covering ``centre`` +- ``half``, its pivot at ``centre``."""
    global _SHIFT
    cx, cy = _s(centre[0] + CANVAS_MARGIN[0]), _s(centre[1] + CANVAS_MARGIN[1])
    hw, hh = _s(half[0]), _s(half[1])
    shift = (cx - hw, cy - hh)
    exact = _cv(centre)

    def local(draw) -> None:
        global _SHIFT
        prev, _SHIFT = _SHIFT, shift
        try:
            paint(draw)
        finally:
            _SHIFT = prev

    return SR.rest_piece(("fsm",) + key, (2 * hw, 2 * hh), (exact[0] - shift[0], exact[1] - shift[1]), local)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _rot(x: float, y: float, deg: float) -> Point:
    r = math.radians(deg)
    c = math.cos(r)
    s = math.sin(r)
    return (x * c - y * s, x * s + y * c)


def _mix(a: RGBA, b: RGBA, t: float) -> RGBA:
    t = max(0.0, min(1.0, t))
    return tuple(int(round(_lerp(a[i], b[i], t))) for i in range(4))  # type: ignore[return-value]


def _poly(
    draw: ImageDraw.ImageDraw,
    pts: Sequence[Point],
    fill: RGBA,
    outline: RGBA | None = OUTLINE,
    width: float = 1.0,
) -> None:
    draw.polygon([_pt(p) for p in pts], fill=fill)
    if outline is not None and len(pts) >= 2:
        draw.line(
            [_pt(p) for p in list(pts) + [pts[0]]],
            fill=outline,
            width=max(1, _s(width)),
            joint="curve",
        )


def _line(
    draw: ImageDraw.ImageDraw, pts: Sequence[Point], fill: RGBA, width: float
) -> None:
    if len(pts) >= 2:
        draw.line(
            [_pt(p) for p in pts], fill=fill, width=max(1, _s(width)), joint="curve"
        )
        # Round caps: PIL's wide lines end square, which reads as a cut stick.
        r = width * 0.5
        for end in (pts[0], pts[-1]):
            _ellipse(draw, end[0], end[1], r, r, fill, None, 0)


def _ellipse(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    fill: RGBA | None,
    outline: RGBA | None = OUTLINE,
    width: float = 0.8,
) -> None:
    x0, y0 = _pt((cx - rx, cy - ry))
    x1, y1 = _pt((cx + rx, cy + ry))
    draw.ellipse(
        (x0, y0, x1, y1),
        fill=fill,
        outline=outline,
        width=max(1, _s(width)) if outline is not None else 0,
    )


def _circle(
    draw: ImageDraw.ImageDraw,
    center: Point,
    r: float,
    fill: RGBA | None,
    outline: RGBA | None = OUTLINE,
    width: float = 0.8,
) -> None:
    _ellipse(draw, center[0], center[1], r, r, fill, outline, width)


def _downsample(img: Image.Image) -> Image.Image:
    return rigdoc.downsampled_canvas(img, FRAME_SIZE, Image.Resampling.LANCZOS)


def _hash(i: int, salt: int = 0) -> float:
    """A fixed pseudo-random value in [0, 1): the same noodle every frame."""
    v = math.sin(i * 12.9898 + salt * 78.233) * 43758.5453
    return v - math.floor(v)


# The damage fractions the reveal map is painted at, heaviest first: a pixel
# keeps the LOWEST level that covers it, because each lighter pass overwrites.
SAUCE_LEVELS = [k / 8.0 for k in range(8, 0, -1)]


class _Paint:
    """Draws the clean art and the sauce reveal map in one pass.

    Ordinary drawing goes to the art and ERASES the reveal map beneath it, so
    sauce is only ever where it would be seen: a noodle drawn over a splat
    hides it. Inside `with paint.sauce(level)` drawing goes to the reveal map
    only, stamped with that level's threshold as its alpha."""

    def __init__(self, art, reveal) -> None:
        self._art = art
        self._reveal = reveal
        self._level: Optional[float] = None

    @contextmanager
    def sauce(self, level: float):
        prev, self._level = self._level, level
        try:
            yield self
        finally:
            self._level = prev

    def __getattr__(self, name: str):
        def call(*args, **kwargs):
            if self._level is None:
                getattr(self._art, name)(*args, **kwargs)
                erase = dict(kwargs)
                for key in ("fill", "outline"):
                    if erase.get(key) is not None:
                        erase[key] = (0, 0, 0, 0)
                getattr(self._reveal, name)(*args, **erase)
            else:
                alpha = max(1, int(round(255 * (1.0 - self._level))))
                stamp = dict(kwargs)
                for key in ("fill", "outline"):
                    c = stamp.get(key)
                    if c is not None:
                        stamp[key] = (c[0], c[1], c[2], alpha)
                getattr(self._reveal, name)(*args, **stamp)

        return call


class _Nothing:
    """Swallows draws: with it as the art, a ``_Paint`` only erases the reveal
    map under a piece placed on the art by ``shape_rig``."""

    def __getattr__(self, name: str):
        return lambda *args, **kwargs: None


#: The bell's churn, keyed in steps of its phase (a piece per step).
BELL_PHASE_STEP = math.tau / 16


def _bell_piece(first: int, last: int, rise: float, phase: float):
    """Bell strands ``first..last`` at ``phase``, untilted, about ROOT: the
    strands are not squashed (``_swirl`` cancels the squash), only turned."""
    width = {0: 9.0, 22: 9.2}[first]

    def paint(draw) -> None:
        for i in range(first, last):
            col = (NOODLE_DEEP if i < 8 else NOODLE_BACK) if first == 0 else NOODLE
            _draw_noodle(draw, _swirl((ROOT[0], ROOT[1] - rise), i, phase), width, col, highlight=first != 0)

    return _piece(("bell", first, phase), ROOT, (BELL_RX + 46, BELL_TOP + 36), paint)


def _noodle(canvas: Image.Image, erase: Optional["_Paint"], pts: Sequence[Point], width: float, fill: RGBA, highlight: bool, name: str) -> None:
    """A noodle that bends every frame (a tentacle, a stalk, a drape): painted
    on its own canvas and placed as ONE raster, so a part flipbook stores one
    picture of it per frame, not its strokes. The canvas lies along the
    noodle's chord (it is painted turned back by the chord's angle and placed
    turned by it), so a slanted noodle is not stored in a mostly empty box.
    It still hides the sauce beneath it (``erase``)."""
    global _SHIFT
    pad = width + 4.0
    (ax, ay), (bx, by) = pts[0], pts[-1]
    degrees = math.degrees(math.atan2(by - ay, bx - ax)) if math.hypot(bx - ax, by - ay) > 1e-3 else 0.0
    local_pts = [(ax + q[0], ay + q[1]) for q in (_rot(x - ax, y - ay, -degrees) for x, y in pts)]
    # The highlight is offset up-left on screen: turned back with the noodle.
    x0, y0 = _s(min(x for x, _ in local_pts) - pad + CANVAS_MARGIN[0]), _s(min(y for _, y in local_pts) - pad + CANVAS_MARGIN[1])
    x1, y1 = _s(max(x for x, _ in local_pts) + pad + CANVAS_MARGIN[0]), _s(max(y for _, y in local_pts) + pad + CANVAS_MARGIN[1])
    local = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    prev, _SHIFT = _SHIFT, (x0, y0)
    try:
        _draw_noodle(blending_draw(local), local_pts, width, fill, highlight, turned=-degrees)
    finally:
        _SHIFT = prev
    pivot = _cv((ax, ay))
    SR.place(canvas, (local, (pivot[0] - x0, pivot[1] - y0)), pivot, degrees, name)
    if erase is not None:
        _draw_noodle(erase, pts, width, fill, highlight)


def _meatball_piece(r: float, squash: float, seed: int):
    return _piece(("meatball", r, squash, seed), (0.0, 0.0), (r * 1.4 + 4, r * 1.4 + 4), lambda d: _draw_meatball(d, (0.0, 0.0), r, squash, seed))


def _eye_piece(r: float, aim: float, style: str, lean: float):
    return _piece(("eye", r, aim, style, lean), (0.0, 0.0), (r * 1.8, r * 1.8), lambda d: _draw_eye(d, (0.0, 0.0), r, aim, style, lean))


@dataclass
class Tentacle:
    """One articulated noodle: a chain of `segments` equal links hanging from
    `rim` (degrees round the bell's underside, y down: 90 is straight below).

    Its shape is forward kinematics: every joint turns the chain by the sum
    of the pose's articulation terms (below), so a pose moves a noodle by
    bending its joints, never by redrawing its curve."""

    rim: float
    length: float
    phase: float
    curl: float  # signed tip curl, degrees per joint over the last third
    front: bool
    segments: int = 14


# Jellyfish-style: every noodle hangs from the underside of the bell. The
# rim runs 18°..162° (y down), so nothing points up out of the top.
TENTACLES: List[Tentacle] = [
    Tentacle(162, 100, 0.0, -11, False),
    Tentacle(146, 120, 1.3, 10, False),
    Tentacle(128, 138, 2.1, -9, True),
    Tentacle(112, 150, 0.6, 10, False),
    Tentacle(98, 158, 2.8, -10, True),
    Tentacle(84, 154, 1.9, 9, False),
    Tentacle(70, 144, 0.9, -10, True),
    Tentacle(54, 132, 2.4, 10, False),
    Tentacle(36, 118, 1.6, -9, True),
    Tentacle(18, 98, 0.4, 11, False),
]
# The noodle the whip and the grasp use: the front-right one.
LASH = 7
# The bell: its top is a dome, its underside a shallow skirt.
BELL_RX, BELL_TOP, BELL_SKIRT = 116.0, 76.0, 34.0


@dataclass
class Pose:
    root_x: float = 0.0
    root_y: float = 0.0
    bob: float = 0.0
    tilt: float = 0.0
    squash: float = 0.0  # >0 flattens and widens the bell (a jellyfish beat)
    time: float = 0.0  # drives the wave travelling down every noodle
    # Articulation, applied to every noodle's joints.
    trail: float = 0.0  # degrees the whole skirt swings back (-x) as it moves
    flare: float = 0.0  # 0..1: the skirt opens outward (the pulse's recoil)
    gather: float = 0.0  # 0..1: the noodles draw in under the bell (a dive)
    limp: float = 0.0  # 0..1: every noodle falls straight and stops waving
    wave: float = 1.0  # scale on the travelling wave
    reach: float = 1.0  # scale on noodle length (contract/extend)
    # One noodle articulated on its own: the lash.
    whip: float = 0.0  # 0..1: the lash snaps out ahead, taut
    whip_wind: float = 0.0  # 0..1: coiled back under the bell first
    grasp: float = 0.0  # 0..1: the lash reaches down and forward to grab
    volley_charge: float = 0.0
    volley_fire: float = 0.0
    beam: float = 0.0
    hurt: float = 0.0
    collapse: float = 0.0
    eye_aim: float = 20.0
    eyes: str = "open"  # open | angry | squeeze | dead | glow


def _ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 0.5 - 0.5 * math.cos(math.pi * t)


def _pose(anim: str, frame_idx: int, nframes: int) -> Pose:
    # Looping rows sample a whole cycle without repeating the first frame.
    loop = anim in LOOPING_ROWS
    t = frame_idx / float(nframes) if loop else frame_idx / float(max(1, nframes - 1))
    cyc = math.tau * t
    p = Pose(time=cyc)
    # A jellyfish beat: the bell squeezes, the skirt flares and pushes, then
    # the noodles trail as it glides. `beat` peaks once per cycle.
    beat = max(0.0, math.sin(cyc)) ** 2
    if anim == "idle":
        p.squash = 0.06 * beat - 0.02
        p.flare = 0.35 * beat
        p.bob = -7.0 * beat + 3.0
        p.trail = 4.0 * math.sin(cyc + 1.0)
        p.eye_aim = 20.0 + 30.0 * math.sin(cyc)
    elif anim == "drift":
        p.squash = 0.05 * beat
        p.flare = 0.25 * beat
        p.root_x = 8.0 * math.sin(cyc)
        p.bob = -5.0 * beat
        p.tilt = 7.0
        p.trail = 30.0 + 8.0 * math.cos(cyc)
        p.eye_aim = 5.0
    elif anim == "noodle_whip":
        wind = _ease(t / 0.35) * (1.0 - _ease((t - 0.35) / 0.2))
        lash = _ease((t - 0.35) / 0.3)
        p.whip_wind, p.whip = wind, lash
        p.root_x = -10.0 * wind + 10.0 * lash
        p.tilt = -7.0 * wind + 9.0 * lash
        p.trail = 18.0 * wind - 10.0 * lash
        p.eye_aim = 0.0
        p.eyes = "angry"
    elif anim == "meatball_volley":
        charge = _ease(t / 0.45)
        fire = _ease((t - 0.45) / 0.2)
        recover = _ease((t - 0.7) / 0.3)
        p.volley_charge = charge * (1.0 - fire)
        p.volley_fire = fire * (1.0 - 0.6 * recover)
        p.squash = 0.08 * p.volley_charge - 0.05 * p.volley_fire
        p.root_x = -6.0 * p.volley_charge - 10.0 * p.volley_fire
        p.tilt = -6.0 * p.volley_charge + 4.0 * p.volley_fire
        p.flare = 0.4 * p.volley_fire
        p.trail = 10.0 * p.volley_fire
        p.eye_aim = 5.0
        p.eyes = "angry"
    elif anim == "eye_beam":
        charge = _ease(t / 0.4)
        p.beam = _ease((t - 0.35) / 0.3)
        p.bob = -3.0 * charge
        p.tilt = -5.0 * charge
        p.gather = 0.25 * charge
        p.eye_aim = 0.0
        p.eyes = "glow" if charge > 0.35 else "angry"
    elif anim == "pulse":
        # The full-body pulse: a deep squeeze, then the whole skirt thrown
        # open in a ring.
        squeeze = _ease(t / 0.4) * (1.0 - _ease((t - 0.4) / 0.15))
        burst = _ease((t - 0.4) / 0.2) * (1.0 - 0.7 * _ease((t - 0.7) / 0.3))
        p.squash = 0.14 * burst - 0.1 * squeeze
        p.gather = 0.8 * squeeze
        p.flare = 1.0 * burst
        p.reach = 1.0 - 0.25 * squeeze + 0.1 * burst
        p.bob = 6.0 * squeeze - 8.0 * burst
        p.eyes = "angry"
        p.eye_aim = 90.0 * squeeze
    elif anim == "dive":
        # Noodles gather tight above a plunge, then splay on arrival.
        plunge = _ease(t / 0.5)
        land = _ease((t - 0.55) / 0.25)
        p.gather = 0.9 * plunge * (1.0 - land)
        p.flare = 0.9 * land
        p.squash = -0.08 * plunge * (1.0 - land) + 0.12 * land
        p.reach = 1.0 - 0.3 * land
        p.trail = -20.0 * plunge * (1.0 - land)
        p.tilt = 6.0 * plunge * (1.0 - land)
        p.eye_aim = 90.0
        p.eyes = "angry"
    elif anim == "grasp":
        reach = _ease(t / 0.45)
        pull = _ease((t - 0.6) / 0.4)
        p.grasp = reach * (1.0 - 0.6 * pull)
        p.tilt = 6.0 * reach - 4.0 * pull
        p.root_x = 8.0 * reach
        p.trail = 12.0 * reach
        p.eye_aim = 50.0
        p.eyes = "angry"
    elif anim == "summon":
        # Calling the lesser appendages: the god rises, its noodles beckon in
        # a slow wave and its eyes burn — then it lets go.
        # A tall, swaying silhouette, unlike the pulse's squeeze-and-burst.
        call = _ease(t / 0.5)
        release = _ease((t - 0.65) / 0.3)
        p.bob = -16.0 * call + 12.0 * release
        p.squash = -0.07 * call + 0.06 * release
        p.wave = 1.0 + 1.8 * call * (1.0 - release)
        p.gather = 0.35 * call * (1.0 - release)
        p.eye_aim = 90.0
        p.eyes = "glow" if 0.3 < call and release < 0.6 else "angry"
    elif anim == "hurt":
        hit = math.sin(math.pi * min(1.0, (frame_idx + 1) / float(nframes)))
        p.hurt = hit
        p.squash = 0.12 * hit
        p.root_x = -10.0 * hit
        p.tilt = -9.0 * hit
        p.flare = 0.7 * hit
        p.wave = 1.0 + 0.8 * hit
        p.eyes = "squeeze"
    elif anim == "death":
        c = _ease(t)
        p.collapse = c
        p.root_y = 40.0 * c
        p.tilt = 22.0 * c
        p.squash = 0.12 * c
        p.limp = c
        p.eye_aim = 90.0
        p.eyes = "dead" if c > 0.3 else "squeeze"
    return p


def _draw_noodle(
    draw: ImageDraw.ImageDraw,
    pts: Sequence[Point],
    width: float,
    fill: RGBA = NOODLE,
    highlight: bool = True,
    turned: float = 0.0,
) -> None:
    """``turned``: the degrees the points were turned (a noodle painted along
    its chord, ``_noodle``), so the highlight's up-left offset turns too."""
    _line(draw, pts, OUTLINE, width + 2.2)
    _line(draw, pts, fill, width)
    if highlight:
        ox, oy = _rot(-width * 0.14, -width * 0.16, turned)
        hi = [(x + ox, y + oy) for x, y in pts]
        _line(draw, hi, _mix(fill, NOODLE_HI, 0.8), max(0.9, width * 0.26))


def _smooth(pts: Sequence[Point], sub: int = 4) -> List[Point]:
    """Catmull-Rom through the chain's joints, so links draw as one noodle."""
    if len(pts) < 3:
        return list(pts)
    out: List[Point] = []
    ext = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for k in range(sub):
            t = k / sub
            t2, t3 = t * t, t * t * t
            out.append(
                tuple(
                    0.5
                    * (
                        2 * p1[j]
                        + (-p0[j] + p2[j]) * t
                        + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                        + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3
                    )
                    for j in range(2)
                )  # type: ignore[arg-type]
            )
    out.append(pts[-1])
    return out


def _chain(base: Point, heading: float, seg: float, turns: Sequence[float]) -> List[Point]:
    """Forward kinematics: from `base`, each link turns by `turns[j]` degrees."""
    pts = [base]
    a = heading
    x, y = base
    for d in turns:
        a += d
        x += math.cos(math.radians(a)) * seg
        y += math.sin(math.radians(a)) * seg
        pts.append((x, y))
    return pts


def _tentacle_joints(tn: Tentacle, i: int, p: Pose, lash: bool) -> Tuple[float, float, List[float]]:
    """The noodle's rest heading, link length, and per-joint turns under `p`."""
    n = tn.segments
    # Rest: hang down, splayed a little by where it leaves the rim.
    splay = (90.0 - tn.rim) * (0.8 + 0.8 * p.flare - 0.6 * p.gather)
    heading = 90.0 - splay + p.trail + p.tilt
    reach = p.reach * (1.0 + 0.12 * p.limp)
    seg = tn.length * reach / n
    turns: List[float] = []
    wave_amp = 8.5 * p.wave * (1.0 - p.limp)
    if p.limp > 0:
        # Dead, a noodle first slumps OUT from where it leaves the rim ...
        heading = _lerp(heading, max(-10.0, min(190.0, 90.0 - (90.0 - tn.rim) * 1.7)), p.limp)
    angle = heading
    for j in range(n):
        s = j / (n - 1)
        # A wave that travels down the noodle, stronger toward the tip.
        w = wave_amp * (0.45 + 0.55 * s) * math.sin(0.62 * j - p.time - tn.phase)
        # Flare curls the tips back up and out, like a bell's recoil.
        flare_curl = -math.copysign(1.0, 90.0 - tn.rim or 1.0) * 6.0 * p.flare * s
        tip_curl = tn.curl * max(0.0, (s - 0.66) / 0.34) * (1.0 - p.limp)
        # A drifting skirt: the trailing noodles bend back further along
        # their length.
        drag = p.trail * 0.05 * s
        turn = w + flare_curl + tip_curl + drag
        # ... then gravity bends each link a little further toward straight
        # down than the one before it, so the strand sags over its own
        # weight, with the small kinks cooked pasta keeps.
        droop = (90.0 - angle) * (0.05 + 0.14 * s) + 9.0 * math.sin(j * 1.3 + tn.phase * 3.0) * (1.0 - 0.5 * s)
        turn = _lerp(turn, droop, p.limp)
        turns.append(turn)
        angle += turn
    if lash:
        if p.whip > 0 or p.whip_wind > 0:
            # The lash: coiled back under the bell, then snapped out ahead.
            coil = p.whip_wind * (1.0 - p.whip)
            heading = _lerp(_lerp(heading, 150.0, coil), -6.0 + p.tilt, p.whip)
            seg *= 1.0 + 1.3 * p.whip - 0.2 * coil
            turns = [_lerp(_lerp(t, 14.0, coil), 0.25 * t, p.whip) for t in turns]
        if p.grasp > 0:
            # The grasp: reach down and forward, fingers curling at the end.
            heading = _lerp(heading, 42.0, p.grasp)
            seg *= 1.0 + 1.0 * p.grasp
            turns = [
                _lerp(t, (20.0 if j > n - 4 else -1.5), p.grasp) for j, t in enumerate(turns)
            ]
    return heading, seg, turns


def _swirl(center: Point, i: int, phase: float) -> List[Point]:
    """One strand of the bell: a loose loop inside the dome, fixed per strand."""
    a0 = _hash(i, 1) * math.tau
    sweep = 2.2 + 1.8 * _hash(i, 2)
    r0 = 0.35 + 0.5 * _hash(i, 3)
    wob = 0.18 + 0.2 * _hash(i, 4)
    freq = 1.5 + 2.0 * _hash(i, 5)
    jx = (_hash(i, 6) - 0.5) * BELL_RX * 0.5
    jy = (_hash(i, 8) - 0.5) * 22.0
    pts: List[Point] = []
    for k in range(29):
        s = k / 28
        a = a0 + sweep * s
        r = min(1.0, max(0.12, r0 + wob * math.sin(freq * a + phase + i)))
        ry = BELL_TOP if math.sin(a) < 0 else BELL_SKIRT
        pts.append((center[0] + jx + math.cos(a) * BELL_RX * r, center[1] + jy * r + math.sin(a) * ry * r))
    return pts


def _splat(draw: ImageDraw.ImageDraw, c: Point, r: float, seed: int, drip: float) -> None:
    """A marinara splatter: a lumpy blob, satellite drops, and a run."""
    pts = []
    for k in range(14):
        a = math.tau * k / 14
        rr = r * (0.7 + 0.5 * _hash(k, seed))
        pts.append((c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr * 0.8))
    _poly(draw, pts, SAUCE, None, 0)
    _circle(draw, (c[0] - r * 0.25, c[1] - r * 0.25), r * 0.25, SAUCE_HI, None, 0)
    for k in range(3):
        a = _hash(k, seed + 5) * math.tau
        d = r * (1.3 + 0.6 * _hash(k, seed + 6))
        _circle(draw, (c[0] + math.cos(a) * d, c[1] + math.sin(a) * d), r * 0.18, SAUCE, None, 0)
    if drip > 0:
        _line(draw, [c, (c[0] + r * 0.1, c[1] + r * (0.8 + 1.6 * drip))], SAUCE, r * 0.34)
        _circle(draw, (c[0] + r * 0.1, c[1] + r * (0.8 + 1.6 * drip)), r * 0.24, SAUCE, None, 0)


def _draw_meatball(
    draw: ImageDraw.ImageDraw,
    center: Point,
    r: float,
    squash: float,
    seed: int,
) -> None:
    cx, cy = center
    rx, ry = r * (1.0 + squash), r * (1.0 - squash)
    _ellipse(draw, cx, cy, rx, ry, MEATBALL, OUTLINE, 1.6)
    _ellipse(draw, cx + rx * 0.16, cy + ry * 0.2, rx * 0.8, ry * 0.74, MEATBALL_SHADE, None, 0)
    _ellipse(draw, cx - rx * 0.08, cy - ry * 0.06, rx * 0.8, ry * 0.76, MEATBALL, None, 0)
    _ellipse(draw, cx - rx * 0.3, cy - ry * 0.32, rx * 0.34, ry * 0.26, MEATBALL_HI, None, 0)
    for k in range(16):
        a = _hash(k, seed) * math.tau
        d = math.sqrt(_hash(k, seed + 7)) * 0.8
        px, py = cx + math.cos(a) * rx * d, cy + math.sin(a) * ry * d
        rr = r * (0.05 + 0.05 * _hash(k, seed + 3))
        col = MEATBALL_CRUMB if _hash(k, seed + 11) < 0.6 else MEATBALL_HI
        _circle(draw, (px, py), rr, col, None, 0)


def _meatball_sauce(
    draw: ImageDraw.ImageDraw,
    center: Point,
    r: float,
    squash: float,
    seed: int,
    sauce: float,
) -> None:
    cx, cy = center
    rx, ry = r * (1.0 + squash), r * (1.0 - squash)
    # Marinara grows with the damage taken: a cap that spreads down the ball,
    # and runs that lengthen.
    depth = 0.15 + 0.75 * sauce  # how far down the ball the cap reaches
    cap: List[Point] = []
    for k in range(19):
        a = math.pi + math.pi * k / 18
        cap.append((cx + math.cos(a) * rx * 0.97, cy + math.sin(a) * ry * 0.97))
    for k in range(18, -1, -1):
        a = math.pi + math.pi * k / 18
        lip = 1.0 - depth * (0.75 + 0.25 * math.sin(k * 1.9 + seed * 3))
        cap.append((cx + math.cos(a) * rx * 0.9, cy - ry * lip + math.sin(a) * ry * 0.12))
    _poly(draw, cap, SAUCE, None, 0)
    runs = [(-0.45, 0.2), (0.05, 0.4), (0.42, 0.15), (-0.15, 0.3)]
    for k, (ox, length) in enumerate(runs[: 1 + int(sauce * 3.99)]):
        x = cx + ox * rx
        y0 = cy - ry * (1.0 - depth) + ry * 0.05
        y1 = y0 + ry * length * (0.5 + sauce)
        _line(draw, [(x, y0), (x, y1)], SAUCE, r * 0.15)
        _circle(draw, (x, y1), r * 0.1, SAUCE, None, 0)
    _ellipse(draw, cx - rx * 0.34, cy - ry * 0.7, rx * 0.2, ry * 0.08, SAUCE_HI, None, 0)
    if sauce > 0.5:
        _ellipse(draw, cx + rx * 0.3, cy - ry * 0.74, rx * 0.1, ry * 0.05, (70, 120, 52, 255), None, 0)


def _draw_eye(
    draw: ImageDraw.ImageDraw,
    center: Point,
    r: float,
    aim: float,
    style: str,
    lean: float,
) -> None:
    ex, ey = center
    if style == "glow":
        _circle(draw, center, r * 1.6, (255, 236, 150, 70), None, 0)
        _circle(draw, center, r * 1.25, (255, 236, 150, 110), None, 0)
    _circle(draw, center, r, EYE_GLOW if style == "glow" else EYE, OUTLINE, 1.5)
    if style == "dead":
        k = r * 0.5
        _line(draw, [(ex - k, ey - k), (ex + k, ey + k)], OUTLINE, 2.4)
        _line(draw, [(ex - k, ey + k), (ex + k, ey - k)], OUTLINE, 2.4)
        return
    if style == "squeeze":
        # Screwed shut: `> <`, each chevron pointing in toward the other eye.
        k = r * 0.55
        s = -lean
        _line(draw, [(ex - k * s, ey - k * 0.6), (ex + k * 0.6 * s, ey), (ex - k * s, ey + k * 0.6)], OUTLINE, 2.4)
        return
    px = ex + math.cos(math.radians(aim)) * r * 0.36
    py = ey + math.sin(math.radians(aim)) * r * 0.36
    if style != "glow":
        _circle(draw, (px, py), r * 0.5, IRIS, None, 0)
    _circle(draw, (px, py), r * 0.28, PUPIL, None, 0)
    _circle(draw, (px - r * 0.12, py - r * 0.14), r * 0.1, (255, 255, 255, 230), None, 0)
    if style in ("angry", "glow"):
        # A heavy lid slanting down toward the middle: the god is displeased.
        # PIL angles run clockwise from 3 o'clock.
        inner, outer = 10.0, 42.0
        start, end = (180 + outer, 360 - inner) if lean < 0 else (180 + inner, 360 - outer)
        x0, y0 = _pt((ex - r, ey - r))
        x1, y1 = _pt((ex + r, ey + r))
        draw.chord((x0, y0, x1, y1), start, end, fill=MEATBALL_SHADE)
        a0, a1 = math.radians(start), math.radians(end)
        _line(draw, [(ex + math.cos(a0) * r, ey + math.sin(a0) * r), (ex + math.cos(a1) * r, ey + math.sin(a1) * r)], OUTLINE, 2.6)
    else:
        _line(
            draw,
            [(ex - r * 0.8, ey - r * 0.72), (ex, ey - r * 0.95), (ex + r * 0.8, ey - r * 0.72)],
            OUTLINE,
            1.4,
        )


def _body_transform(p: Pose):
    """The body's frame for pose `p`: its root, squash, and `P`, which takes a
    point in the body's own coordinates to the geometry frame."""
    root = (ROOT[0] + p.root_x, ROOT[1] + p.root_y + p.bob)
    sx, sy = 1.0 + p.squash, 1.0 - p.squash

    def P(x: float, y: float) -> Point:
        rx, ry = _rot(x * sx, y * sy, p.tilt)
        return (root[0] + rx, root[1] + ry)

    return root, sx, sy, P


def _hull(pts: Sequence[Point]) -> List[Point]:
    """Convex hull, counter-clockwise (monotone chain)."""
    pts = sorted(set(pts))
    if len(pts) < 3:
        return list(pts)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: List[Point] = []
    for q in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], q) <= 0:
            lower.pop()
        lower.append(q)
    upper: List[Point] = []
    for q in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], q) <= 0:
            upper.pop()
        upper.append(q)
    return lower[:-1] + upper[:-1]


def _to_frame_px(g: Point) -> Point:
    k = FRAME_SIZE[0] / WORK_FRAME_SIZE[0]
    return ((g[0] + CANVAS_MARGIN[0]) * k, (g[1] + CANVAS_MARGIN[1]) * k)


def _bell_outline(anim: str, frame_idx: int, nframes: int) -> List[Point]:
    """The god's BODY in one frame, in frame pixels: the bell of noodles and
    the two meatballs on it. The noodles hanging below are not body — they
    sting, and a blow has to find the bell."""
    p = _pose(anim, frame_idx, nframes)
    _root, _sx, _sy, P = _body_transform(p)
    pts: List[Point] = []
    for k in range(24):
        a = math.tau * k / 24
        ry = BELL_TOP if math.sin(a) < 0 else BELL_SKIRT
        pts.append(P(math.cos(a) * BELL_RX * 0.92, math.sin(a) * ry * 0.85 - 6))
    for cx, cy, r in ((-42, -30, 40.0), (42, -28, 42.0)):
        for k in range(12):
            a = math.tau * k / 12
            pts.append(P(cx + math.cos(a) * r, cy + math.sin(a) * r))
    return [_to_frame_px(q) for q in pts]


def _part(name: str, pts: Sequence[Point]) -> dict:
    hull = _hull([(round(x, 1), round(y, 1)) for x, y in pts])
    xs, ys = [q[0] for q in hull], [q[1] for q in hull]
    x0, y0 = int(math.floor(min(xs))), int(math.floor(min(ys)))
    return {
        "name": name,
        "x": x0,
        "y": y0,
        "w": int(math.ceil(max(xs))) - x0,
        "h": int(math.ceil(max(ys))) - y0,
        "poly": hull,
    }


def _hurtbox_parts() -> dict:
    """Per gameplay key, the bell's hull over every frame of that row. Death
    publishes none: the dying god is not a target."""
    out = {}
    for anim, n, _ms in ROWS:
        key = ANIMATION_KEY_MAP.get(anim)
        if key is None or anim == "death":
            continue
        pts: List[Point] = []
        for i in range(n):
            pts.extend(_bell_outline(anim, i, n))
        out[key] = {"parts": [_part("bell", pts)]}
    return out


def _body_metrics(fw: int, fh: int) -> dict:
    """The gameplay body is the bell at rest, not the noodles' reach."""
    part = _part("bell", _bell_outline("idle", 0, ROWS[0][1]))
    return {
        "body_pixel_bbox": {"x": part["x"], "y": part["y"], "w": part["w"], "h": part["h"]},
        "feet_pixel": {"x": part["x"] + part["w"] / 2.0, "y": float(part["y"] + part["h"])},
        "feet_anchor_norm": {"x": 0.0, "y": round(0.5 - (part["y"] + part["h"]) / fh, 6)},
    }


def _render_frame(anim: str, frame_idx: int, nframes: int, sauce: float = 0.0) -> Image.Image:
    """One frame as the fight shows it at `sauce` in [0, 1]: the clean art
    with the reveal map applied at that level (previews and review sheets)."""
    base, reveal = _render_layers(anim, frame_idx, nframes)
    return _apply_sauce(base, reveal, sauce)


def _apply_sauce(base: Image.Image, reveal: Image.Image, level: float) -> Image.Image:
    """What the game's overlay does: a reveal pixel shows once the damage
    fraction reaches its threshold (alpha = 1 - threshold)."""
    if level <= 0.0:
        return base
    cut = int(round(255 * (1.0 - level)))
    mask = reveal.getchannel("A").point(lambda v: 255 if v > 0 and v >= cut else 0)
    shown = reveal.copy()
    shown.putalpha(mask)
    return Image.alpha_composite(base, shown)


def _render_layers(anim: str, frame_idx: int, nframes: int) -> Tuple[Image.Image, Image.Image]:
    """The clean frame, and its SAUCE REVEAL MAP: where marinara sits on this
    frame and at what damage it appears. A pixel's alpha is `1 - threshold`,
    so the game shows it once `damage_fraction >= threshold`; 0 is never."""
    p = _pose(anim, frame_idx, nframes)
    size = CANVAS_SIZE
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    sauce_img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = _Paint(blending_draw(img), ImageDraw.Draw(sauce_img))  # raw-draw-ok: the reveal map is data, not art; a later threshold must REPLACE the one beneath it, never blend
    # A piece placed on the art still hides the sauce beneath it.
    erase = _Paint(_Nothing(), ImageDraw.Draw(sauce_img))  # raw-draw-ok: the reveal map, as above

    root, sx, sy, P = _body_transform(p)
    ph = p.time

    def tentacle_pts(i: int, tn: Tentacle) -> List[Point]:
        base = P(
            math.cos(math.radians(tn.rim)) * BELL_RX * 0.84,
            math.sin(math.radians(tn.rim)) * BELL_SKIRT * 0.9,
        )
        heading, seg, turns = _tentacle_joints(tn, i, p, i == LASH)
        return _smooth(_chain(base, heading, seg, turns))

    chains = {i: tentacle_pts(i, tn) for i, tn in enumerate(TENTACLES)}
    back = [i for i, tn in enumerate(TENTACLES) if not tn.front and i != LASH]
    front = [i for i, tn in enumerate(TENTACLES) if tn.front and i != LASH]

    for i in back:
        _noodle(img, erase, chains[i], 9.6, NOODLE_BACK, False, f"noodle{i}")

    # --- The bell: a heap of looping strands, back ones darker. One piece
    # per churn step, turned by the tilt about the root.
    bell_phase = SR.q(ph * 0.5, BELL_PHASE_STEP)
    SR.place(img, _bell_piece(0, 22, 6.0, bell_phase), _cv(root), p.tilt, "bell_back")

    # --- Eye stalks, rooted in the bell behind the meatballs.
    beam_rise = 14.0 * p.beam
    stalk_specs = [
        ((-24, -48), (-62, -96), (-50, -138 - beam_rise), -1.0),
        ((22, -48), (62, -92), (54, -136 - beam_rise), 1.0),
    ]
    eye_centres: List[Point] = []
    stalks: List[List[Point]] = []
    for (ax, ay), (bx, by), (cx, cy), side in stalk_specs:
        sway = math.sin(ph + side) * 5.0
        if p.collapse > 0:
            cx, cy = cx + side * 50 * p.collapse, cy + 80 * p.collapse
            bx, by = bx + side * 30 * p.collapse, by + 36 * p.collapse
        a = P(ax, ay)
        c = P(cx + sway, cy)
        b1 = P(bx + sway * 0.5, _lerp(ay, by, 0.5))
        b2 = P(_lerp(bx, cx, 0.3) - side * 18, by - 8)
        pts = []
        for k in range(25):
            s = k / 24
            u = 1 - s
            pts.append(
                (
                    u**3 * a[0] + 3 * u * u * s * b1[0] + 3 * u * s * s * b2[0] + s**3 * c[0],
                    u**3 * a[1] + 3 * u * u * s * b1[1] + 3 * u * s * s * b2[1] + s**3 * c[1],
                )
            )
        stalks.append(pts)
        eye_centres.append(c)
    for k, pts in enumerate(stalks):
        _noodle(img, erase, pts, 10.0, NOODLE, True, f"stalk{k}")

    SR.place(img, _bell_piece(22, 40, 4.0, bell_phase), _cv(root), p.tilt, "bell_front")

    # --- The two meatballs, sitting up on the dome. The right one pulls back
    # into the noodles to load a shot, then punches forward.
    charge, fire = p.volley_charge, p.volley_fire
    left = P(-42, -30 + 6 * p.collapse)
    right = P(42 - 8 * charge + 14 * fire, -28 + 3 * charge + 6 * p.collapse)
    balls = [
        (left, 40.0, 0.04 + p.squash * 0.5, 3),
        (right, 42.0 * (1.0 - 0.08 * charge), 0.04 + 0.16 * charge - 0.1 * fire, 9),
    ]
    balls = [(c, round(r, 1), SR.q(sq, 0.01), seed) for c, r, sq, seed in balls]
    for k, (c, r, sq, seed) in enumerate(balls):
        SR.place(img, _meatball_piece(r, sq, seed), _cv(c), 0.0, f"meatball{k}")
    for level in SAUCE_LEVELS:
        with draw.sauce(level):
            for c, r, sq, seed in balls:
                _meatball_sauce(draw, c, r, sq, seed, level)

    # Two strands draped over the meatballs' feet tie them into the bell.
    for i, (a, b, c) in enumerate([((-96, 2), (-40, 22), (14, 4)), ((-16, 10), (40, 26), (96, 0))]):
        wob = math.sin(ph + i * 2.0) * 3.0
        pa, pb, pc = P(*a), P(b[0], b[1] + wob), P(*c)
        pts = []
        for k in range(21):
            s = k / 20
            u = 1 - s
            pts.append((u * u * pa[0] + 2 * u * s * pb[0] + s * s * pc[0], u * u * pa[1] + 2 * u * s * pb[1] + s * s * pc[1]))
        _noodle(img, erase, pts, 9.4, NOODLE, True, f"drape{i}")

    for i in front:
        _noodle(img, erase, chains[i], 9.8, NOODLE, True, f"noodle{i}")
    _noodle(img, erase, chains[LASH], 10.4 if (p.whip or p.grasp) else 9.8, NOODLE, True, "lash")
    if p.whip > 0.35:
        tx, ty = chains[LASH][-1]
        for k, grow in enumerate([0.0, 12.0]):
            a = (1.0 - k * 0.45) * min(1.0, (p.whip - 0.35) * 2.0)
            col = (IMPACT[0], IMPACT[1], IMPACT[2], int(IMPACT[3] * a))
            x0, y0 = _pt((tx - 14 - grow, ty - 24 - grow))
            x1, y1 = _pt((tx + 18 + grow, ty + 24 + grow))
            draw.arc((x0, y0, x1, y1), 300, 60, fill=col, width=_s(3.0))

    # --- Marinara on the noodles: fixed splat sites, each appearing past its
    # own threshold, so more damage only ever adds sauce.
    def noodle_sauce(sauce: float) -> None:
        sites = [
            (P(-70, -8), 0.08, 13.0), (P(12, 18), 0.18, 12.0), (P(84, -18), 0.28, 14.0),
            (P(-8, -60), 0.38, 11.0), (P(-100, 14), 0.48, 13.0), (P(58, 22), 0.58, 15.0),
            (P(-60, -52), 0.68, 11.0), (P(-40, 26), 0.78, 12.0), (P(70, -56), 0.86, 11.0),
            (P(100, 6), 0.94, 12.0),
        ]
        for k, (c, thresh, r) in enumerate(sites):
            if sauce >= thresh:
                _splat(draw, c, r * (0.8 + 0.5 * sauce), 40 + k, min(1.0, (sauce - thresh) * 3.0))
        # Sauce runs down the noodles too, from the heaviest-hit side.
        for k, i in enumerate(front):
            thresh = 0.3 + 0.2 * k
            if sauce >= thresh:
                pts = chains[i]
                n = int(len(pts) * (0.2 + 0.4 * (sauce - thresh)))
                _line(draw, pts[2:2 + n], SAUCE, 6.5)

    for level in SAUCE_LEVELS:
        with draw.sauce(level):
            noodle_sauce(level)

    # The volley's muzzle: a burst of marinara off the loaded meatball. The
    # shot itself is the sim's projectile; the boss only shows the throw.
    if fire > 0.05:
        mx, my = right[0] + 44, right[1] - 4
        _circle(draw, (mx + 10 * fire, my), 22 * fire, SAUCE, OUTLINE, 1.4)
        _circle(draw, (mx + 6 * fire, my - 5 * fire), 10 * fire, SAUCE_HI, None, 0)
        for k in range(10):
            a = math.radians(-80 + k * 18)
            reach = (34 + 34 * _hash(k, 21)) * fire
            r = (6.0 + 5.0 * _hash(k, 22)) * (1.0 - 0.35 * fire)
            _circle(draw, (mx + math.cos(a) * reach, my + math.sin(a) * reach), r, SAUCE, OUTLINE, 1.2)
    if charge > 0.2:
        for k in range(3):
            a = math.radians(-40 + k * 40)
            _circle(draw, (right[0] + math.cos(a) * 50, right[1] + math.sin(a) * 50), 5.0 * charge, SAUCE, OUTLINE, 1.0)

    aim = SR.q(p.eye_aim, 5.0)
    for k, c in enumerate(eye_centres):
        lean = -1.0 if k == 0 else 1.0
        SR.place(img, _eye_piece(20.0, aim, p.eyes, lean), _cv(c), 0.0, f"eye{k}")
        _draw_eye(erase, c, 20.0, aim, p.eyes, lean)

    if p.beam > 0.05:
        for origin in eye_centres:
            length = 120 + 70 * p.beam
            tip = (origin[0] + length, origin[1] + 10)
            half = 14 * p.beam
            _poly(
                draw,
                [(origin[0], origin[1] - 8), (tip[0], tip[1] - half), (tip[0] + 14, tip[1]), (tip[0], tip[1] + half), (origin[0], origin[1] + 8)],
                BEAM2,
                None,
                0,
            )
            _poly(
                draw,
                [(origin[0], origin[1] - 4), (tip[0] - 6, tip[1] - half * 0.4), (tip[0] + 4, tip[1]), (tip[0] - 6, tip[1] + half * 0.4), (origin[0], origin[1] + 4)],
                BEAM,
                None,
                0,
            )

    if anim == "hurt" and frame_idx == 0:
        flash = Image.new("RGBA", img.size, (255, 255, 255, 0))
        flash.putalpha(img.getchannel("A").point(lambda v: v * 150 // 255))
        # Through rigdoc's seams: the body's shapes, then the flash as one picture.
        flashed = Image.new("RGBA", img.size, (0, 0, 0, 0))
        rigdoc.composite_canvas(flashed, img)
        rigdoc.composite_canvas(flashed, flash)
        img = flashed

    # The reveal map downsamples by averaging, and an edge pixel then carries
    # a higher threshold than the splat's middle: its edge arrives a little
    # after its body, which reads as the splat spreading.
    return _downsample(img), sauce_img.resize(FRAME_SIZE, Image.Resampling.BOX)


def render(out_dir: str | Path, **opts) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    reveals: dict = {}

    def frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
        base, reveal = _render_layers(anim, frame_idx, nframes)
        reveals[(anim, frame_idx)] = reveal
        return base

    # A fixed canvas (no auto-crop): the authored hulls are in its pixels.
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        auto_crop=False,
        actor_metadata=ACTOR_METADATA,
        animation_key_map=ANIMATION_KEY_MAP,
        hurtbox_parts=_hurtbox_parts(),
        body_metrics_fn=_body_metrics,
        pose_bodies="authored",
    )
    parts = publish_rig_flipbook(TARGET_NAME, ROWS, frame, outputs, frame_transform, out_dir)
    sauce = build_sheet(
        target=SAUCE_TARGET,
        rows=ROWS,
        render_fn=lambda anim, frame_idx, _n: reveals[(anim, frame_idx)],
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        auto_crop=False,
        pose_bodies="authored",
    )
    return [sauce["spritesheet"], sauce["yaml"], sauce["ron"]] + [
        outputs[k]
        for k in [
            "spritesheet",
            "yaml",
            "ron",
            "actor",
            "preview",
            "canonical",
            "canonical_transparent",
        ]
    ] + list(parts.values())


# The sauce reveal maps publish as a sheet of their own: the same rows and
# frames as the art, packed independently, so every quality tier repacks it
# like any sheet and the overlay finds a cell by (row, frame), never by a
# pixel rect shared with the art.
SAUCE_TARGET = f"{TARGET_NAME}_sauce"
SHEET_FILES = (
    f"{TARGET_NAME}_spritesheet.png",
    f"{TARGET_NAME}_spritesheet.yaml",
    f"{TARGET_NAME}_spritesheet.ron",
    f"{TARGET_NAME}_actor.ron",
    f"{SAUCE_TARGET}_spritesheet.png",
    f"{SAUCE_TARGET}_spritesheet.yaml",
    f"{SAUCE_TARGET}_spritesheet.ron",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render the standalone Flying Spaghetti Monster boss sprite sheet."
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "generated" / TARGET_NAME,
    )
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
