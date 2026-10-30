"""Sprite generator for the Failed Prototype: what the lab of Godwin Castle
made before it made Wolfenstein.

The look (2026-10-15, Jon's pick of a baddie): a small stitched wolf-man,
about 130 cm if he stood up, but he does not: he goes hunched, and runs on
all fours. He comes in packs. Nothing of him matches: the head of a wolf,
smaller and madder than Wolfenstein's, with one ear torn and one eye larger
than the other; grey fur in patches and the grey-green skin of the monster
between them; one arm and one leg furred, the others bare skin; stitches
everywhere; one bolt in his neck. A torn hospital gown with a number on it,
and on one arm the red armband of the regime (``_evil_faction``: an invented
cog, not a real symbol). He is pitiful and he is dangerous; he is not cute.

He holds nothing. There is no drop shadow.

His attacks: a swipe of his claws (``slash``) and a pounce with his teeth
(``attack_side``). His taunt is a yip that wants to be a howl. ``notice``
jerks him up out of his hunch with the bolt in his neck sparking;
``windup`` rears him back on his haunches, claws up, to spring.

He is a person of ``_person_rig``: the bones and the frame are shared; the
build, the head, the gown and every pose are his.
"""

from __future__ import annotations

import math
from typing import List

from ._ai_era_kit import OUTLINE, WHITE, RGBA, Point, ease, lerp, mix, turned
from . import _evil_faction as F
from . import _person_rig as R
from ._person_rig import Build, Person, Stamp, loop, shot

TARGET_NAME = "evil_failed_prototype"
TARGET_BASENAME = TARGET_NAME
DISPLAY_NAME = "Failed Prototype"

TRAITS = ["story", "humanoid", "enemy", "combatant", "authoritarian", "monster", "wolf", "pack", "small"]

ACTOR_METADATA = {
    "actor": {"character_id": "npc_evil_failed_prototype", "display_name": DISPLAY_NAME},
    "body": {"body_plan": "HumanoidBiped", "body_kind": "Standard", "mass_class": "Light", "traits": TRAITS, "locomotion_hint": "Walk"},
    "capabilities": {
        "traversal": {"walk": True, "jump": True, "climb": None, "fly": None, "swim": None, "crawl": None, "use_lifts": None,
                      "door_access": []},
        "interactions": {"talk": False, "trade": None, "carry": None, "open_doors": []},
    },
    "brain": {"default_preset": "melee_brute_striker"},
    "actions": {"default_preset": "striker_swipe"},
    "visual": {"default_pose": "idle", "portrait": {"animation": "idle", "frame": 0}},
    "tags": TRAITS,
    "sockets": {},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "traversal.jump": {"animation": "jump", "events": []},
        "traversal.fall": {"animation": "fall", "events": []},
        "action.melee.primary": {
            "animation": "slash",
            "events": [
                {"t": 0.36, "event": "hitbox_active_start", "source": "explicit.profile.combat_humanoid"},
                {"t": 0.6, "event": "hitbox_active_end", "source": "explicit.profile.combat_humanoid"},
            ],
        },
        "combat.hurt": {"animation": "hit", "events": []},
        "combat.death": {"animation": "death", "events": []},
    },
    "authoring_description": (
        "A failed attempt at Wolfenstein from the castle lab: a small stitched wolf-man of "
        "mismatched parts in a torn hospital gown, with the regime's armband (an invented cog; "
        "no real symbol). He lopes hunched and runs on all fours; they come in packs."
    ),
    "gameplay_description": "A fast, weak pack enemy: a claw swipe and a pouncing bite. It yips before it comes.",
    "dialogue_hints": {"barks": ["Yip. YIP.", "*a howl that breaks in the middle*", "Ex-per-i-ment... seven."]},
}

GOWN: RGBA = (176, 194, 198, 255)
GOWN_DARK: RGBA = (124, 142, 150, 255)
GOWN_LIGHT: RGBA = (214, 226, 228, 255)
STAIN: RGBA = (168, 150, 108, 255)
SKIN: RGBA = (138, 162, 122, 255)
SKIN_SHADE: RGBA = (108, 130, 98, 255)
SKIN_DEEP: RGBA = (68, 86, 64, 255)
FUR: RGBA = (120, 120, 126, 255)
FUR_DARK: RGBA = (78, 76, 86, 255)
FUR_DEEP: RGBA = (50, 48, 58, 255)
FUR_LIGHT: RGBA = (186, 184, 182, 255)
STITCH: RGBA = (40, 30, 34, 255)
CLAW: RGBA = (46, 40, 38, 255)
NOSE: RGBA = (24, 22, 26, 255)
GUM: RGBA = (150, 44, 56, 255)
MOUTH: RGBA = (74, 18, 30, 255)
TONGUE: RGBA = (214, 96, 110, 255)
TOOTH: RGBA = (238, 228, 200, 255)
EYE_WHITE: RGBA = (252, 246, 220, 255)
VEIN: RGBA = (220, 70, 70, 255)
IRIS: RGBA = (226, 186, 60, 255)
EAR_INNER: RGBA = (170, 128, 132, 255)
BOLT: RGBA = (170, 172, 176, 255)
BOLT_DARK: RGBA = (96, 98, 106, 255)
SPARK: RGBA = (255, 238, 184, 255)
SPARK_DARK: RGBA = (214, 122, 58, 255)
SLASH: RGBA = (250, 246, 236, 255)
SLASH_DARK: RGBA = (150, 150, 170, 255)

#: About 130 cm if he stood up. He does not: ``height`` is the top of his
#: skull as he crouches (measured on the idle row); his ears stand a few
#: pixels over it.
BUILD = Build(hip_up=40.0, thigh=21.4, shin=20.4, neck=(1.0, -30.0), upper=18.0, fore=17.0, near_shoulder=(-4.4, -26.6), far_shoulder=(5.4, -26.2),
              near_hip=(-3.2, 0.0), far_hip=(3.2, 0.0), ankle_up=3.0, head_up=(6.0, -12.0), throat=(-1.0, 9.0), height=77.0, half_width=(16.0, 22.0))

X = Person(TARGET_NAME, BUILD, frame=(192, 144), ground=132.0, cx=84.0)
K = X.K
P = X.P
TOP = BUILD.neck[1] - 2.0


def stitches(d, pts, tick: float = 1.0, every: float = 1.8, width: float = 0.4) -> None:
    """A sewn line through ``pts`` (frame points), crossed by short ticks."""
    K.line(d, pts, STITCH, width)
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        length = math.hypot(bx - ax, by - ay)
        if length < 1e-3:
            continue
        nx, ny = -(by - ay) / length, (bx - ax) / length
        for k in range(max(1, int(length / every))):
            t = (k + 0.5) * every / length
            x, y = ax + (bx - ax) * t, ay + (by - ay) * t
            K.line(d, [(x - nx * tick, y - ny * tick), (x + nx * tick, y + ny * tick)], STITCH, width)


# ---- The gown ----------------------------------------------------------------


def _torso(hem_back: int, hem_front: int, drop=None):
    """His trunk in the gown, from his hips, his spine up: a round back, and
    a hem torn in points."""
    del drop
    hb, hf = float(hem_back), float(hem_front)

    def shape(d) -> None:
        K.poly(d, [K.at(-3.6, TOP), K.at(-8.6, TOP + 3.0), K.at(-10.0, -18.0), K.at(-9.4, -4.0), K.at(-10.4 - hb, 13.0), K.at(-7.6, 16.4),
                   K.at(-5.4, 12.6), K.at(-2.4, 17.6), K.at(0.6, 13.0), K.at(3.6, 16.8), K.at(6.4, 12.4), K.at(9.6 + hf, 14.8), K.at(9.2, -4.0),
                   K.at(8.8, -16.0), K.at(8.0, -24.0), K.at(7.0, TOP + 3.0), K.at(3.6, TOP - 0.4)], WHITE)
        K.oval(d, K.at(-4.4, -26.6), 4.8, 5.0, WHITE)
        K.oval(d, K.at(4.0, -26.2), 4.2, 4.6, WHITE)

    def detail(d) -> None:
        # The far side is in shade.
        K.poly(d, [K.at(6.0, TOP - 2.0), K.at(30.0, TOP - 2.0), K.at(30.0, 20.0), K.at(6.6 + hf * 0.5, 20.0), K.at(5.4, -6.0)], GOWN_DARK)
        # A tear, and the stitched skin under it.
        K.poly(d, [K.at(-7.0, -16.0), K.at(-2.6, -18.4), K.at(-1.4, -12.0), K.at(-4.0, -9.6), K.at(-7.4, -11.0)], SKIN_SHADE)
        stitches(d, [K.at(-6.6, -15.0), K.at(-3.4, -14.0), K.at(-2.4, -11.4)])
        K.line(d, [K.at(-7.0, -16.0), K.at(-2.6, -18.4), K.at(-1.4, -12.0), K.at(-4.0, -9.6), K.at(-7.4, -11.0), K.at(-7.0, -16.0)], GOWN_DARK, 0.5)
        # Stains.
        K.oval(d, K.at(2.0, -4.0), 2.6, 1.8, mix(GOWN, STAIN, 0.6))
        K.oval(d, K.at(-6.0, 6.0), 2.0, 2.8, mix(GOWN, STAIN, 0.5))
        # His number, stenciled: 07.
        for k, sym in enumerate("07"):
            for line in R.STROKES[sym]:
                K.line(d, [K.at(0.6 + k * 3.0 + x * 2.2, -24.0 + y * 4.0) for x, y in line], FUR_DEEP, 0.7)
        # The seam of the gown down his back, and its tie.
        K.line(d, [K.at(-8.6, TOP + 3.4), K.at(-9.6, -10.0)], GOWN_DARK, 0.5)
        K.line(d, [K.at(-9.4, -14.0), K.at(-12.4, -12.6)], GOWN_DARK, 0.6)
        K.line(d, [K.at(-30.0, 9.6), K.at(30.0, 9.6)], GOWN_LIGHT, 0.4)

    return K.solid(("gown", hem_back, hem_front), shape, GOWN, detail, outline=1.2, rim=0.3, shade=0.4, shade_colour=GOWN_DARK)


X.torso = _torso
X.neck = R.make_neck(K, SKIN_SHADE, 6.0)

# ---- The limbs: one of each is fur, the other bare skin ----------------------

X.upper_arm = lambda near: [(0.3, 1.0, 6.0, 5.2, FUR if near else SKIN_SHADE), (0.0, 0.42, 7.6, 7.0, GOWN if near else GOWN_DARK)]
X.forearm = lambda near: [(0.0, 1.0, 5.2, 4.4, FUR if near else SKIN_SHADE)]
X.thigh = lambda near: [(0.0, 1.0, 7.4, 6.0, FUR if near else SKIN_SHADE)]
X.shin = lambda near: [(0.0, 1.0, 6.0, 4.6, FUR if near else SKIN_SHADE)]


def _hand(mode: str, near: bool):
    """A hand along +x from its wrist: on the near arm a furred paw, on the
    far arm bare skin with a seam. Both have claws."""
    colour = FUR if near else SKIN_SHADE
    k = 0.62
    fingers = {
        "open": [((8.0, -4.6), (15.0, -8.6)), ((9.0, -1.6), (17.0, -3.0)), ((9.0, 1.6), (17.0, 2.6)), ((8.0, 4.6), (14.6, 7.6))],
        "flat": [((8.0, -3.6), (17.4, -4.0)), ((9.0, -1.2), (18.4, -1.2)), ((9.0, 1.2), (18.2, 1.4)), ((8.0, 3.6), (16.8, 4.0))],
        "soft": [((8.0, -3.6), (12.6, 1.0)), ((9.0, -1.2), (13.6, 3.4)), ((9.0, 1.2), (13.2, 5.4)), ((8.0, 3.6), (11.6, 7.0))],
    }.get(mode, [])

    def at(p: Point) -> Point:
        return K.at(p[0] * k, p[1] * k)

    def claw(a: Point, b: Point) -> List[Point]:
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        ux, uy = dx / length, dy / length
        return [at((b[0] - uy * 1.4, b[1] + ux * 1.4)), at((b[0] + ux * 5.0, b[1] + uy * 5.0)), at((b[0] + uy * 1.4, b[1] - ux * 1.4))]

    claws = [claw(a, b) for a, b in fingers] or [[at((8.6, y - 1.0)), at((12.0, y + 0.4)), at((8.6, y + 1.2))] for y in (-3.4, 0.0, 3.4)]

    def shape(d) -> None:
        K.oval(d, at((5.0, 0.0)), 6.2 * k, 6.0 * k, WHITE)
        K.rrect(d, K.home[0] - 1.2, K.home[1] - 3.0, K.home[0] + 2.0, K.home[1] + 3.0, 1.0, WHITE)
        for a, b in fingers:
            K.stroke(d, [at(a), at(b)], WHITE, 3.4 * k)
        for c in claws:
            K.poly(d, c, WHITE)

    def detail(d) -> None:
        for c in claws:
            K.poly(d, c, CLAW)
        if not near:
            stitches(d, [at((2.4, -5.4)), at((3.2, 0.0)), at((2.6, 5.4))], tick=0.7, every=1.4, width=0.35)

    return K.solid(("hand", mode, near), shape, colour, detail, outline=1.1, rim=0.3, shade=0.35, shade_colour=FUR_DEEP if near else SKIN_DEEP)


X.hand = _hand


def _paw(near: bool):
    """A foot from its ankle: a furred paw, or a bare foot with claws."""
    colour = FUR if near else SKIN_SHADE
    au = BUILD.ankle_up

    def shape(d) -> None:
        K.oval(d, K.at(1.4, 0.4), 3.4, 3.0, WHITE)
        K.oval(d, K.at(4.0, au - 1.6), 5.4, 2.0, WHITE)
        for x in (6.6, 8.4):
            K.oval(d, K.at(x, au - 1.4), 1.6, 1.4, WHITE)
        K.poly(d, [K.at(8.6, au - 2.2), K.at(11.6, au - 0.4), K.at(8.4, au - 0.2)], WHITE)

    def detail(d) -> None:
        K.poly(d, [K.at(8.6, au - 2.2), K.at(11.6, au - 0.4), K.at(8.4, au - 0.2)], CLAW)
        K.line(d, [K.at(6.2, au - 2.6), K.at(6.6, au - 0.6)], FUR_DEEP if near else SKIN_DEEP, 0.4)

    return K.solid(("paw", near), shape, colour, detail, outline=1.1, rim=0.3, shade=0.35, shade_colour=FUR_DEEP if near else SKIN_DEEP)


X.shoe = _paw

# ---- The head ----------------------------------------------------------------

NEAR_EYE = (3.4, -2.4)
FAR_EYE = (8.4, -3.2)
HINGE = (3.0, 3.4)
UPPER_LIP = [(4.0, 3.6), (8.0, 3.8), (12.0, 3.4)]


def _jaw_points(open_: float) -> List[Point]:
    pts = [(2.4, 3.6), (12.0, 4.2), (12.2, 5.4), (10.4, 7.6), (5.0, 8.4), (1.6, 6.8)]
    return [(HINGE[0] + p[0], HINGE[1] + p[1]) for p in (turned((x - HINGE[0], y - HINGE[1]), open_) for x, y in pts)]


def _jaw(open_: float, dx: float = 0.0):
    """His crooked lower jaw, open ``open_`` degrees; his tongue lolls out
    of it when it is open. ``dx``: that far forward (a head seen from the
    side)."""
    jaw = _jaw_points(open_)

    def at(p: Point) -> Point:
        return K.at(p[0] + dx, p[1])

    teeth = []
    for t, tall in ((0.35, 1.4), (0.7, 2.2)):
        x, y = lerp(jaw[0][0], jaw[1][0], t), lerp(jaw[0][1], jaw[1][1], t)
        up, side = turned((0.0, -tall), open_), turned((0.8, 0.0), open_)
        teeth.append([(x - side[0], y - side[1]), (x + up[0], y + up[1]), (x + side[0], y + side[1])])
    lolls = open_ > 12.0
    tongue = [jaw[1], (jaw[1][0] + 2.6, jaw[1][1] + 3.0), (jaw[1][0] + 1.0, jaw[1][1] + 6.0), (jaw[1][0] - 2.0, jaw[1][1] + 2.0)]

    def shape(d) -> None:
        K.poly(d, [at(p) for p in [HINGE] + UPPER_LIP[1:] + [jaw[1], jaw[0]]], WHITE)
        K.poly(d, [at(p) for p in jaw], WHITE)
        for tooth in teeth:
            K.poly(d, [at(p) for p in tooth], WHITE)
        if lolls:
            K.poly(d, [at(p) for p in tongue], WHITE)

    def detail(d) -> None:
        K.poly(d, [at(p) for p in [HINGE] + UPPER_LIP[1:] + [jaw[1], jaw[0]]], MOUTH)
        K.poly(d, [at(p) for p in jaw[2:]] + [at(jaw[0]), at(jaw[1])], FUR)
        K.line(d, [at(jaw[0]), at(jaw[1])], GUM, 0.7)
        for tooth in teeth:
            K.poly(d, [at(p) for p in tooth], TOOTH)
        if lolls:
            K.poly(d, [at(p) for p in tongue], TONGUE)

    return K.solid(("jaw", round(open_, 1)) + ((dx,) if dx else ()), shape, FUR, detail, outline=1.1, rim=0.2, shade=0.3, shade_colour=FUR_DEEP)


def _skull():
    """His head: a small skull with a bare stitched patch, a ruff in tufts,
    one ear torn, the muzzle with crooked teeth."""
    ruff = [(-6.0, -6.0), (-10.4, -4.4), (-8.6, -2.0), (-11.4, 0.6), (-8.4, 2.4), (-10.0, 6.4), (-5.6, 5.6), (-5.0, 9.6), (-1.6, 7.6), (1.4, 9.4),
            (3.0, 6.0), (1.0, 2.0)]
    torn_ear = [(-2.4, -6.0), (-6.6, -12.4), (-7.4, -9.6), (-9.6, -11.0), (-8.8, -5.6), (-5.0, -3.0)]
    far_ear = [(0.6, -7.4), (-1.6, -13.6), (-4.0, -7.6)]
    muzzle = [(2.0, -5.0), (7.0, -5.6), (11.0, -4.0), (14.6, -2.4), (15.6, -0.6), (15.0, 1.4), (13.0, 2.4), (12.2, 3.4), (4.0, 3.6), (2.0, 2.4)]
    upper_teeth = [[(x - 0.7, 3.4), (x, 3.4 + tall), (x + 0.7, 3.4)] for x, tall in ((5.2, 1.2), (7.0, 1.6), (10.6, 2.6), (12.0, 1.2))]

    def at(p: Point) -> Point:
        return K.at(*p)

    def shape(d) -> None:
        K.poly(d, [at(p) for p in far_ear], WHITE)
        K.oval(d, K.at(-1.0, -1.6), 7.4, 6.8, WHITE)
        K.oval(d, K.at(3.0, 1.0), 5.4, 4.6, WHITE)
        K.poly(d, [at(p) for p in ruff], WHITE)
        K.poly(d, [at(p) for p in muzzle], WHITE)
        K.poly(d, [at(p) for p in torn_ear], WHITE)
        for tooth in upper_teeth:
            K.poly(d, [at(p) for p in tooth], WHITE)

    def detail(d) -> None:
        K.poly(d, [at(p) for p in far_ear], FUR_DARK)
        K.poly(d, [at((-3.4, -5.6)), at((-6.0, -10.0)), at((-8.2, -6.0)), at((-5.6, -4.0))], EAR_INNER)
        # A bare patch of skin on his skull, sewn in.
        patch = [at((-5.6, -5.0)), at((-1.0, -6.6)), at((0.4, -3.0)), at((-3.0, -0.6)), at((-6.6, -1.8))]
        K.poly(d, patch, SKIN)
        stitches(d, patch + [patch[0]], tick=0.7, every=1.4, width=0.35)
        K.poly(d, [at((1.6, 0.0)), at((8.0, 1.0)), at((13.0, 2.0)), at((12.6, 4.0)), at((2.0, 4.6)), at((-1.0, 2.6))], FUR_LIGHT)
        K.oval(d, at(NEAR_EYE), 3.8, 3.4, FUR_DARK)
        for x in (8.0, 10.0):
            K.line(d, [at((x - 0.6, -4.6)), at((x + 0.3, -3.4)), at((x - 0.2, -2.2))], FUR_DEEP, 0.5)
        for a, b in (((-6.0, -2.0), (-8.6, 0.6)), ((-4.0, 4.0), (-6.4, 6.6)), ((-0.6, 6.0), (-1.4, 8.4))):
            K.line(d, [at(a), at(b)], FUR_DARK, 0.6)
        K.line(d, [at(p) for p in UPPER_LIP], GUM, 0.7)
        for tooth in upper_teeth:
            K.poly(d, [at(p) for p in tooth], TOOTH)
        K.oval(d, K.at(14.4, -0.8), 1.8, 1.6, NOSE)

    return K.solid(("skull",), shape, FUR, detail, outline=1.1, rim=0.3, shade=0.35, shade_colour=FUR_DEEP)


def _eyes(mode: str):
    """One eye larger than the other, both too wide; the pupils do not look
    the same way."""

    def paint(d) -> None:
        for (ex, ey), r, look in ((NEAR_EYE, 2.9, (-0.5, 0.3)), (FAR_EYE, 1.8, (0.4, -0.3))):
            c = K.at(ex, ey)
            if mode in ("closed", "dead"):
                q = r * 0.7
                for s in (-1.0, 1.0):
                    K.line(d, [(c[0] - q, c[1] - q * s), (c[0] + q, c[1] + q * s)], OUTLINE, 0.7)
                continue
            if mode == "wince":
                K.line(d, [(c[0] - r, c[1] - 1.2), (c[0] + r * 0.5, c[1]), (c[0] - r, c[1] + 1.2)], OUTLINE, 0.8)
                continue
            K.oval(d, c, r + 0.5, r + 0.5, OUTLINE)
            K.oval(d, c, r, r, EYE_WHITE)
            for ang in (200.0, 330.0, 110.0):
                a = math.radians(ang)
                K.line(d, [(c[0] + math.cos(a) * r * 0.95, c[1] + math.sin(a) * r * 0.95), (c[0] + math.cos(a) * r * 0.5, c[1] + math.sin(a) * r * 0.5)],
                       VEIN, 0.4)
            p = (c[0] + look[0] * r * 0.4, c[1] + look[1] * r * 0.4)
            K.oval(d, p, r * 0.3, r * 0.3, IRIS)
            K.oval(d, p, r * 0.17, r * 0.17, OUTLINE)

    return K.piece(("eyes", mode), paint)


def _brows(mood: int):
    """The brows do not match either: the near one is up, the far one set."""
    del mood

    def paint(d) -> None:
        K.stroke(d, [K.at(0.4, -6.6), K.at(3.0, -7.4), K.at(5.6, -6.6)], FUR_DEEP, 1.3)
        K.stroke(d, [K.at(6.8, -4.8), K.at(8.8, -5.8), K.at(10.6, -5.6)], FUR_DEEP, 1.2)

    return K.piece(("brows",), paint)


def _seam_and_bolt():
    """The seam round his neck, and his one bolt, from the middle of his
    head."""

    def paint(d) -> None:
        stitches(d, [K.at(-5.6, 9.2), K.at(-2.0, 10.4), K.at(1.6, 9.8), K.at(3.6, 8.4)], tick=1.0, every=1.6, width=0.45)
        K.rrect(d, K.at(-8.6, 0.0)[0], K.at(0.0, 12.0)[1], K.at(-4.0, 0.0)[0], K.at(0.0, 13.8)[1], 0.3, BOLT_DARK, OUTLINE, 0.4)
        hexagon = [K.at(-3.6 + 1.8 * math.cos(math.tau * k / 6.0 + 0.5), 12.9 + 1.8 * math.sin(math.tau * k / 6.0 + 0.5)) for k in range(6)]
        K.poly(d, hexagon, BOLT, OUTLINE, 0.4)

    return K.piece(("seam_and_bolt",), paint)


def _open(mouth: str) -> float:
    return {"big": 36.0, "open": 20.0, "o": 14.0}.get(mouth, 6.0)


X.head_layers = lambda pose: [(_jaw(_open(str(pose["mouth"]))), "jaw"), (_skull(), "skull"), (_eyes(str(pose["eyes"])), "eyes"), (_brows(0), "brows"),
                              (_seam_and_bolt(), "seam")]


def _armband(ctx) -> List[Stamp]:
    """The regime's band on his near arm, over the sleeve of his gown."""
    if ctx.pose["arm"] == "under":
        return []
    t = 0.3
    at = (lerp(ctx.shoulder[0], ctx.elbow[0], t), lerp(ctx.shoulder[1], ctx.elbow[1], t))
    turn = math.degrees(math.atan2(ctx.elbow[1] - ctx.shoulder[1], ctx.elbow[0] - ctx.shoulder[0]))
    return [(F.band(K, 8.6, 4.8), at, "armband", turn), (F.emblem(K, 2.2), at, "armband_emblem", 0.0)]


X.layers["front"].append(_armband)

# ---- How he stands -----------------------------------------------------------

# Crouched, hunched, his face forward and his long arms hanging in front.
X.set_rest(hip=(0.0, 6.0), lean=32.0, head=(1.0, 1.0, -12.0), na=(6.0, 24.0), fa=(8.0, 23.0), nh="soft", fh="soft", nf=(-7.0, 0.0, 0.0),
           ff=(8.0, 0.0, 0.0), mouth="flat")


@X.row
def idle(i: int, n: int):
    # He twitches: his head jerks round, and back.
    _, s, _c = loop(i, n)
    jerk = 14.0 if i in (3, 4) else 0.0
    return P(hip=(0.0, 6.0 + 0.8 * s), lean=32.0 + 1.5 * s, head=(1.0, 1.0, -12.0 + jerk), na=(6.0 + s, 24.0), fa=(8.0 - s, 23.0),
             mouth="open" if i == 4 else "flat")


@X.row
def walk(i: int, n: int):
    # A hunched shuffle, the knuckles low.
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 8.0, 3.6)
    return P(hip=(0.5, 6.0 + 1.4 * abs(math.cos(ph))), lean=34.0, head=(1.0, 1.0, -14.0 + 2.0 * s), na=(6.0 - 7.0 * c, 24.0), fa=(8.0 + 7.0 * c, 23.0),
             nf=nf, ff=ff, hem=(1.0, 1.0))


@X.row
def run(i: int, n: int):
    # On all fours: the hands reach the floor in turn, the legs push.
    ph, s, c = loop(i, n)
    # The wrist stops a hand's length over the floor: the paw is on it.
    reach = 12.0

    def hand(p: float) -> tuple:
        lift = max(0.0, -math.sin(p))
        return (10.0 * math.cos(p) + 6.0, reach - 5.0 * lift)

    nf, ff = R.stride(ph + 1.2, 11.0, 7.0, -4.0)
    return P(hip=(0.0, 16.0 + 1.6 * math.cos(2.0 * ph)), lean=75.0, head=(2.0, 0.0, -32.0), na=hand(ph), fa=hand(ph + 0.9), nab=1.0, fab=1.0, nh="open",
             fh="open", nf=nf, ff=ff, mouth="open", hem=(3.0, 0.0))


RISE = P(hip=(2.0, -2.0), lean=40.0, head=(2.0, 0.0, -24.0), na=(18.0, 6.0), fa=(20.0, 4.0), nh="open", fh="open", nf=(-10.0, -6.0, 40.0),
         ff=(-4.0, -10.0, 30.0), mouth="big", hem=(2.0, 2.0))
APEX = P(hip=(0.0, -2.0), lean=30.0, head=(2.0, 0.0, -18.0), na=(16.0, 10.0), fa=(18.0, 8.0), nh="open", fh="open", nf=(-4.0, -9.0, 20.0),
         ff=(6.0, -12.0, 6.0), mouth="open", hem=(3.0, 3.0))
FALL = P(hip=(0.0, -3.0), lean=10.0, head=(1.0, 0.0, -2.0), na=(-16.0, -4.0), nab=-1.0, fa=(20.0, -4.0), nh="open", fh="open", nf=(-8.0, -4.0, 22.0),
         ff=(8.0, -8.0, 8.0), mouth="big", hem=(4.0, 4.0))


@X.row
def jump(i: int, n: int):
    wind = P(hip=(-1.0, 14.0), lean=44.0, head=(2.0, 1.0, -26.0), na=(6.0, 22.0), fa=(8.0, 21.0), nf=(-8.0, 0.0, 0.0), ff=(8.0, 0.0, 0.0))
    return X.keys(shot(i, n), [(0.0, wind), (0.3, RISE), (0.6, RISE), (1.0, APEX)])


@X.row
def fall(i: int, n: int):
    _, s, c = loop(i, n)
    return dict(FALL, na=(-16.0 + 2.0 * s, -4.0 - 3.0 * c), fa=(20.0 - 2.0 * s, -4.0 + 3.0 * c), nf=(-8.0, -4.0 + 1.5 * s, 22.0), ff=(8.0, -8.0 - 1.5 * s, 8.0))


READY = P(hip=(-1.0, 8.0), lean=30.0, head=(1.0, 1.0, -12.0), na=(14.0, 8.0), fa=(16.0, 12.0), nh="open", fh="open", nf=(-9.0, 0.0, 0.0),
          ff=(9.0, 0.0, 0.0), mouth="open")


def _swing(u: float) -> float:
    return ease(max(0.0, min(1.0, (u - 0.2) / 0.42)))


@X.row
def slash(i: int, n: int):
    # A claw from high over his shoulder, down through you.
    u = shot(i, n)
    swing = _swing(u)
    a = math.radians(lerp(-140.0, 70.0, swing))
    hand = (29.0 * math.cos(a), 29.0 * math.sin(a))
    base = dict(READY, hip=(lerp(-2.0, 5.0, swing), 8.0), lean=lerp(18.0, 40.0, swing), na=hand, nab=-1.0 if hand[1] < -8.0 and hand[0] < 8.0 else 1.0,
                arm="under" if hand[1] < -6.0 and hand[0] > -16.0 else "over", fa=(lerp(16.0, -6.0, swing), 18.0), mouth="big" if 0.2 < u < 0.8 else "open")
    if u > 0.8:
        return X.blend(base, READY, ease((u - 0.8) / 0.2))
    return base


#: In the air, all of him at you behind his jaws.
POUNCE = P(hip=(4.0, -2.0), off=(10.0, -14.0), lean=62.0, head=(3.0, 0.0, -36.0), na=(26.0, 4.0), fa=(25.0, 8.0), nh="open", fh="open",
           nf=(-20.0, -10.0, 70.0), ff=(-16.0, -14.0, 60.0), mouth="big", hem=(4.0, 0.0))


@X.row
def attack_side(i: int, n: int):
    # Down low, then the pounce, the bite, and back down.
    coil = P(hip=(-3.0, 16.0), lean=46.0, head=(2.0, 1.0, -28.0), na=(10.0, 20.0), fa=(12.0, 19.0), nh="open", fh="open", nf=(-9.0, 0.0, 0.0),
             ff=(9.0, 0.0, 0.0), mouth="open")
    bite = dict(POUNCE, off=(16.0, -6.0), mouth="flat", head=(4.0, 1.0, -30.0))
    landed = dict(READY, off=(16.0, 0.0), hip=(0.0, 12.0), lean=40.0)
    return X.keys(shot(i, n), [(0.0, READY), (0.2, coil), (0.4, POUNCE), (0.55, bite), (0.75, landed), (1.0, dict(READY, off=(6.0, 0.0)))])


STRUCK = P(hip=(-4.0, 6.0), lean=4.0, head=(-2.0, -1.0, -6.0), na=(6.0, 18.0), fa=(12.0, 14.0), nh="open", fh="open", nf=(-8.0, 0.0, 0.0),
           ff=(8.0, -5.0, -22.0), eyes="wince", mouth="big", off=(-4.0, 0.0), hem=(0.0, 4.0))


@X.row
def hit(i: int, n: int):
    return X.keys(shot(i, n), [(0.0, X.full(P())), (0.25, STRUCK), (0.6, STRUCK), (1.0, X.full(P()))])


#: On his back, his paws up.
SUPINE = P(rot=-90.0, hip=(-2.0, 25.5), off=(13.0, 0.0), head=(0.0, 0.0, 10.0), lean=0.0, na=(14.0, 4.0), fa=(10.0, 2.0), nh="soft", fh="soft",
           nf=(-4.5, 22.0, 0.0), ff=(4.5, 20.0, -10.0), eyes="dead", mouth="big")


@X.row
def death(i: int, n: int):
    toppling = X.blend(STRUCK, SUPINE, 0.5)
    toppling = dict(toppling, off=(toppling["off"][0], toppling["off"][1] - 6.0))
    return X.keys(shot(i, n), [(0.0, STRUCK), (0.3, toppling), (0.5, SUPINE), (0.75, dict(SUPINE, na=(16.0, 0.0))), (1.0, SUPINE)])


#: His head thrown back for the howl that comes out as a yip.
YIP = P(hip=(0.0, 8.0), lean=10.0, head=(-1.0, -1.0, -50.0), na=(6.0, 22.0), fa=(8.0, 21.0), nh="soft", fh="soft", mouth="big")


@X.row
def taunt(i: int, n: int):
    down = dict(X.full(P()), mouth="flat")
    return X.keys(shot(i, n), [(0.0, down), (0.15, YIP), (0.3, dict(YIP, mouth="o", head=(0.0, 0.0, -30.0))), (0.45, YIP),
                               (0.6, dict(YIP, mouth="o", head=(0.0, 0.0, -30.0))), (0.8, YIP), (1.0, down)])


#: Startled: jerked up out of his hunch, his head snapped up to you, his
#: hands flung open, the bolt in his neck sparking.
STARTLE = P(hip=(-1.0, 3.0), lean=14.0, head=(0.0, -1.0, -26.0), na=(12.0, 10.0), fa=(14.0, 6.0), nh="open", fh="open", nf=(-8.0, 0.0, 0.0),
            ff=(8.0, 0.0, 0.0), mouth="o")


@X.row
def notice(i: int, n: int):
    # The game loops it, so every frame is the whole pose with a twitch.
    s = (0.0, 1.0, -1.0)[i % 3]
    return dict(STARTLE, head=(0.0, -1.0, -26.0 + 3.0 * s), na=(12.0 + s, 10.0 - s))


#: Reared back on his haunches to spring: his weight on his back foot, both
#: claws up and open in front of him, his jaws wide.
REARED = P(hip=(-5.0, 12.0), lean=12.0, head=(1.0, -1.0, -26.0), na=(26.0, 4.0), fa=(24.0, 10.0), nh="open", fh="open", nf=(-11.0, 0.0, 0.0),
           ff=(9.0, 0.0, 0.0), mouth="big", hem=(2.0, 2.0))


@X.row
def windup(i: int, n: int):
    # The pounce held back. The game loops it, so every frame is the whole
    # pose with a shiver.
    s = (0.0, 1.0, -1.0)[i % 3]
    return dict(REARED, lean=12.0 + 1.0 * s, na=(26.0 + s, 4.0 - s), fa=(24.0 - s, 10.0 + s))


X.rows = [("idle", 8, 120), ("walk", 8, 95), ("run", 8, 70), ("jump", 6, 90), ("fall", 6, 90), ("notice", 3, 110), ("windup", 3, 90),
          ("slash", 8, 75), ("attack_side", 10, 70), ("hit", 5, 90), ("death", 8, 110), ("taunt", 10, 90)]

# ---- What he does ------------------------------------------------------------


def _muzzle(ctx) -> Point:
    tip = turned((15.0, 0.0), ctx.turn)
    return (ctx.head[0] + tip[0], ctx.head[1] + tip[1])


def _effects(ctx) -> List[Stamp]:
    out: List[Stamp] = []
    anim, u = ctx.anim, ctx.u
    if anim == "slash" and 0.25 <= u <= 0.7:
        now = math.degrees(math.atan2(ctx.hand[1] - ctx.shoulder[1], ctx.hand[0] - ctx.shoulder[0]))
        old = max(-140.0, now - 90.0)
        if now - old >= 12.0:
            reach = math.dist(ctx.shoulder, ctx.hand) + 7.0
            for k, dr in enumerate((-3.6, 0.0, 3.6)):
                out.append((R.swoosh(K, round(reach + dr), int(round(old + 5.0 * k)), int(round(now)), 2.0, SLASH, SLASH_DARK), ctx.shoulder,
                            f"claw_trail_{k}", 0.0))
    elif anim == "attack_side" and 0.48 <= u <= 0.68:
        m = _muzzle(ctx)
        out.append((R.burst(K, 8.0, SPARK, SPARK_DARK, 8), (m[0] + 5.0, m[1] + 2.0), "bite", 0.0))
    elif anim == "taunt" and ctx.pose["mouth"] == "big" and 0.12 <= u <= 0.85:
        m = _muzzle(ctx)
        for k in range(1 + ctx.i % 2):
            out.append((R.swoosh(K, 6.0 + 6.0 * k, int(ctx.turn - 34), int(ctx.turn + 34), 1.8, SPARK, SPARK_DARK), (m[0] - 2.0, m[1]), f"yip_{k}", 0.0))
    elif anim == "notice" and ctx.i % 3 != 1:
        # The bolt in his neck sparks.
        bolt = turned((-3.6, 12.9), ctx.turn)
        out.append((R.burst(K, 5.0 if ctx.i % 3 == 0 else 4.0, SPARK, SPARK_DARK, 6), (ctx.head[0] + bolt[0], ctx.head[1] + bolt[1]), "bolt_spark", 0.0))
    elif anim == "hit" and u <= 0.5:
        out.append((R.burst(K, 8.0, SPARK, SPARK_DARK, 8), (ctx.head[0] + 9.0, ctx.head[1] - 2.0), "struck", 0.0))
    return out


X.effects = _effects

ROWS = X.rows
FRAME_SIZE = X.frame
_render_frame = X.render_frame
render, main, render_canonical = R.entry_points(X, ACTOR_METADATA, DISPLAY_NAME)


def render_portraits(out_dir, **opts):
    """His portraits are frames of this sheet."""
    del opts
    return X.portraits(out_dir, {"default": ("idle", (1,), 0, False), "talking": ("taunt", (1, 2, 3, 4, 5, 6), 90, True)}, view_width=40.0)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}

# ---- In the round (``_round_cast``) --------------------------------------------
#
# He is hunched at rest (``lean`` 32, his hips down), so in the round his
# trunk, neck and head lean forward about his hips as his rows lean them
# (``evil_zombie.LeaningBody``). His gown in 3D is written from the numbers
# of his own ``_torso`` (it keeps none). His head from the side and from the
# front is drawn as his own head is drawn (``_skull``, ``_jaw``, ``_eyes``),
# in the numbers of those views. Nothing of him matches, so no side of him
# is the mirror of the other: from the right his torn ear, his large eye, the
# sewn patch and the bolt; from the left a whole ear and a small eye. His
# rows do not use this.

import numpy as np  # noqa: E402

from . import _person_round as O  # noqa: E402
from . import _round_cast as C  # noqa: E402
from . import _round_wear as W  # noqa: E402
from .evil_zombie import LeaningBody  # noqa: E402


def _one_eye(c: Point, r: float, look: Point, mode: str, d) -> None:
    """One of his eyes at the frame point ``c``, as ``_eyes`` draws each."""
    if mode in ("closed", "dead"):
        q = r * 0.7
        for s_ in (-1.0, 1.0):
            K.line(d, [(c[0] - q, c[1] - q * s_), (c[0] + q, c[1] + q * s_)], OUTLINE, 0.7)
        return
    K.oval(d, c, r + 0.5, r + 0.5, OUTLINE)
    K.oval(d, c, r, r, EYE_WHITE)
    for ang in (200.0, 330.0, 110.0):
        a = math.radians(ang)
        K.line(d, [(c[0] + math.cos(a) * r * 0.95, c[1] + math.sin(a) * r * 0.95), (c[0] + math.cos(a) * r * 0.5, c[1] + math.sin(a) * r * 0.5)], VEIN, 0.4)
    p_ = (c[0] + look[0] * r * 0.4, c[1] + look[1] * r * 0.4)
    K.oval(d, p_, r * 0.3, r * 0.3, IRIS)
    K.oval(d, p_, r * 0.17, r * 0.17, OUTLINE)


def _side_skull(right: bool):
    """His head from the side, facing right, from its middle: the skull, the
    long muzzle with its teeth and nose, the ruff behind; from the right the
    torn ear and the sewn patch, from the left the whole ear."""
    ruff = [(-7.0, -6.0), (-11.4, -4.4), (-9.6, -2.0), (-12.4, 0.6), (-9.4, 2.4), (-11.0, 6.4), (-6.6, 5.6), (-6.0, 9.6), (-2.6, 7.6), (0.4, 9.4),
            (2.0, 6.0), (0.0, 2.0)]
    ear = ([(-3.4, -6.0), (-7.6, -12.4), (-8.4, -9.6), (-10.6, -11.0), (-9.8, -5.6), (-6.0, -3.0)] if right
           else [(-2.0, -6.2), (-4.4, -15.0), (-7.6, -5.4)])
    muzzle = [(3.0, -5.0), (8.4, -5.6), (12.6, -4.0), (16.2, -2.4), (17.2, -0.6), (16.6, 1.4), (14.6, 2.4), (13.8, 3.4), (5.6, 3.6), (3.6, 2.4)]
    lip = [(5.6, 3.6), (9.6, 3.8), (13.6, 3.4)]
    teeth = [[(x - 0.7, 3.4), (x, 3.4 + tall), (x + 0.7, 3.4)] for x, tall in ((6.8, 1.2), (8.6, 1.6), (12.2, 2.6), (13.6, 1.2))]

    def at(p_: Point) -> Point:
        return K.at(*p_)

    def shape(d) -> None:
        K.oval(d, K.at(-2.0, -1.6), 8.0, 6.8, WHITE)
        K.oval(d, K.at(4.0, 1.0), 5.6, 4.6, WHITE)
        K.poly(d, [at(p_) for p_ in ruff], WHITE)
        K.poly(d, [at(p_) for p_ in muzzle], WHITE)
        K.poly(d, [at(p_) for p_ in ear], WHITE)
        for tooth in teeth:
            K.poly(d, [at(p_) for p_ in tooth], WHITE)

    def detail(d) -> None:
        if right:
            K.poly(d, [at((-4.4, -5.6)), at((-7.0, -10.0)), at((-9.2, -6.0)), at((-6.6, -4.0))], EAR_INNER)
            patch = [at((-6.6, -5.0)), at((-2.0, -6.6)), at((-0.6, -3.0)), at((-4.0, -0.6)), at((-7.6, -1.8))]
            K.poly(d, patch, SKIN)
            stitches(d, patch + [patch[0]], tick=0.7, every=1.4, width=0.35)
        else:
            K.poly(d, [at((-3.0, -6.6)), at((-4.4, -12.6)), at((-6.4, -6.2))], EAR_INNER)
        K.poly(d, [at((3.2, 0.0)), at((9.6, 1.0)), at((14.6, 2.0)), at((14.2, 4.0)), at((3.6, 4.6)), at((0.6, 2.6))], FUR_LIGHT)
        K.oval(d, K.at(5.0, -2.4), 3.8 if right else 3.0, 3.4 if right else 2.8, FUR_DARK)
        for x in (9.6, 11.6):
            K.line(d, [K.at(x - 0.6, -4.6), K.at(x + 0.3, -3.4), K.at(x - 0.2, -2.2)], FUR_DEEP, 0.5)
        for a, b in (((-7.0, -2.0), (-9.6, 0.6)), ((-5.0, 4.0), (-7.4, 6.6)), ((-1.6, 6.0), (-2.4, 8.4))):
            K.line(d, [at(a), at(b)], FUR_DARK, 0.6)
        K.line(d, [at(p_) for p_ in lip], GUM, 0.7)
        for tooth in teeth:
            K.poly(d, [at(p_) for p_ in tooth], TOOTH)
        K.oval(d, K.at(16.0, -0.8), 1.8, 1.6, NOSE)

    return K.solid(("skull_side", right), shape, FUR, detail, outline=1.1, rim=0.3, shade=0.35, shade_colour=FUR_DEEP)


def _side_eye(right: bool):
    """His one eye seen from the side: the large one from the right, the small
    one from the left; and its brow."""

    def made(mode: str):
        def paint(d) -> None:
            _one_eye(K.at(5.0, -2.4), 2.9 if right else 1.8, (0.6, 0.2), mode, d)
            K.stroke(d, [K.at(2.6, -6.6), K.at(5.0, -7.4), K.at(7.4, -6.4)] if right else [K.at(3.4, -4.8), K.at(5.4, -5.8), K.at(7.2, -5.6)],
                     FUR_DEEP, 1.3)

        return K.piece(("side_eye", right, mode), paint)

    return made


def _side_layers(right: bool):
    eye = _side_eye(right)
    return lambda pose: ([(_jaw(_open(str(pose["mouth"])), 1.6), "jaw"), (_side_skull(right), "skull"), (eye(str(pose["eyes"])), "eyes")]
                         + ([(_seam_and_bolt(), "seam")] if right else []))


def _left_layers(pose):
    """His left three-quarter view, drawn facing right and mirrored: his own
    head, but the ear whole, the eyes the other way round, no patch and no
    bolt (they are on his right)."""
    return [(_jaw(_open(str(pose["mouth"]))), "jaw"), (_left_skull(), "skull"), (_left_eyes(str(pose["eyes"])), "eyes"), (_brows(0), "brows")]


def _left_skull():
    ruff = [(-6.0, -6.0), (-10.4, -4.4), (-8.6, -2.0), (-11.4, 0.6), (-8.4, 2.4), (-10.0, 6.4), (-5.6, 5.6), (-5.0, 9.6), (-1.6, 7.6), (1.4, 9.4),
            (3.0, 6.0), (1.0, 2.0)]
    ear = [(-1.6, -6.2), (-4.4, -14.6), (-7.0, -5.4)]
    far_ear = [(0.6, -7.4), (-1.6, -13.6), (-4.0, -7.6)]
    muzzle = [(2.0, -5.0), (7.0, -5.6), (11.0, -4.0), (14.6, -2.4), (15.6, -0.6), (15.0, 1.4), (13.0, 2.4), (12.2, 3.4), (4.0, 3.6), (2.0, 2.4)]
    teeth = [[(x - 0.7, 3.4), (x, 3.4 + tall), (x + 0.7, 3.4)] for x, tall in ((5.2, 1.2), (7.0, 1.6), (10.6, 2.6), (12.0, 1.2))]

    def at(p_: Point) -> Point:
        return K.at(*p_)

    def shape(d) -> None:
        K.poly(d, [at(p_) for p_ in far_ear], WHITE)
        K.oval(d, K.at(-1.0, -1.6), 7.4, 6.8, WHITE)
        K.oval(d, K.at(3.0, 1.0), 5.4, 4.6, WHITE)
        K.poly(d, [at(p_) for p_ in ruff], WHITE)
        K.poly(d, [at(p_) for p_ in muzzle], WHITE)
        K.poly(d, [at(p_) for p_ in ear], WHITE)
        for tooth in teeth:
            K.poly(d, [at(p_) for p_ in tooth], WHITE)

    def detail(d) -> None:
        K.poly(d, [at(p_) for p_ in far_ear], FUR_DARK)
        K.poly(d, [at((-2.6, -6.6)), at((-4.4, -12.4)), at((-6.0, -6.0))], EAR_INNER)
        K.poly(d, [at((1.6, 0.0)), at((8.0, 1.0)), at((13.0, 2.0)), at((12.6, 4.0)), at((2.0, 4.6)), at((-1.0, 2.6))], FUR_LIGHT)
        K.oval(d, at(NEAR_EYE), 3.0, 2.8, FUR_DARK)
        for a, b in (((-6.0, -2.0), (-8.6, 0.6)), ((-4.0, 4.0), (-6.4, 6.6)), ((-0.6, 6.0), (-1.4, 8.4))):
            K.line(d, [at(a), at(b)], FUR_DARK, 0.6)
        K.line(d, [at(p_) for p_ in UPPER_LIP], GUM, 0.7)
        for tooth in teeth:
            K.poly(d, [at(p_) for p_ in tooth], TOOTH)
        K.oval(d, K.at(14.4, -0.8), 1.8, 1.6, NOSE)

    return K.solid(("skull_left",), shape, FUR, detail, outline=1.1, rim=0.3, shade=0.35, shade_colour=FUR_DEEP)


def _left_eyes(mode: str):
    def paint(d) -> None:
        _one_eye(K.at(*NEAR_EYE), 1.8, (0.4, -0.3), mode, d)
        _one_eye(K.at(*FAR_EYE), 2.4, (-0.5, 0.3), mode, d)

    return K.piece(("left_eyes", mode), paint)


def _front_skull():
    """His head from the front: the skull and the ruff round it, his torn
    right ear (on the left as we look at him) and his whole left one, the
    muzzle toward us with its nose, the jaw hanging, the sewn patch."""

    def shape(d) -> None:
        K.oval(d, K.at(0.0, -1.6), 7.6, 6.8, WHITE)
        for sx in (-1.0, 1.0):
            K.poly(d, [K.at(5.0 * sx, -2.0), K.at(9.6 * sx, 0.0), K.at(8.4 * sx, 3.0), K.at(10.0 * sx, 6.0), K.at(5.6 * sx, 7.4), K.at(2.0 * sx, 6.0)], WHITE)
        K.poly(d, [K.at(-3.6, -5.6), K.at(-7.6, -11.6), K.at(-8.0, -9.0), K.at(-10.0, -10.0), K.at(-9.0, -4.6), K.at(-6.0, -3.0)], WHITE)
        K.poly(d, [K.at(3.0, -6.0), K.at(7.0, -14.4), K.at(8.6, -4.6)], WHITE)
        K.oval(d, K.at(0.0, 3.4), 4.4, 3.8, WHITE)
        K.poly(d, [K.at(-3.6, 5.4), K.at(3.6, 5.4), K.at(2.8, 9.6), K.at(-2.8, 9.6)], WHITE)

    def detail(d) -> None:
        K.poly(d, [K.at(-4.2, -5.6), K.at(-7.2, -9.6), K.at(-8.2, -5.4), K.at(-5.6, -4.0)], EAR_INNER)
        K.poly(d, [K.at(4.2, -6.0), K.at(6.6, -12.0), K.at(7.6, -5.4)], EAR_INNER)
        patch = [K.at(-5.6, -5.4), K.at(-1.4, -6.6), K.at(-0.6, -3.4), K.at(-3.6, -1.6), K.at(-6.4, -2.6)]
        K.poly(d, patch, SKIN)
        stitches(d, patch + [patch[0]], tick=0.7, every=1.4, width=0.35)
        K.oval(d, K.at(0.0, 3.4), 4.4, 3.8, FUR_LIGHT)
        K.oval(d, K.at(-3.4, -1.8), 3.8, 3.4, FUR_DARK)
        K.poly(d, [K.at(-3.6, 5.4), K.at(3.6, 5.4), K.at(2.8, 9.6), K.at(-2.8, 9.6)], MOUTH)
        for x, tall in ((-2.2, 1.4), (-0.8, 1.0), (0.8, 1.0), (2.2, 1.6)):
            K.poly(d, [K.at(x - 0.6, 5.4), K.at(x, 5.4 + tall), K.at(x + 0.6, 5.4)], TOOTH)
        K.line(d, [K.at(-3.6, 5.4), K.at(3.6, 5.4)], GUM, 0.7)
        K.oval(d, K.at(0.0, 1.8), 2.2, 1.7, NOSE)
        for a, b in (((-6.0, 2.0), (-8.6, 4.6)), ((6.0, 2.0), (8.6, 4.6))):
            K.line(d, [K.at(*a), K.at(*b)], FUR_DARK, 0.6)

    return K.solid(("skull_front",), shape, FUR, detail, outline=1.1, rim=0.3, shade=0.35, shade_colour=FUR_DEEP)


def _front_eyes(mode: str):
    """His eyes from the front: the large one on his right, the small one on
    his left, looking two ways; his brows that do not match."""

    def paint(d) -> None:
        _one_eye(K.at(-3.4, -1.8), 2.9, (-0.5, 0.3), mode, d)
        _one_eye(K.at(3.4, -2.4), 1.8, (0.4, -0.3), mode, d)
        K.stroke(d, [K.at(-6.0, -5.6), K.at(-3.4, -6.6), K.at(-0.8, -5.6)], FUR_DEEP, 1.3)
        K.stroke(d, [K.at(1.6, -4.4), K.at(3.4, -5.4), K.at(5.4, -5.0)], FUR_DEEP, 1.2)
        # His one bolt, out of the right of his neck.
        K.rrect(d, K.at(-9.4, 0.0)[0], K.at(0.0, 11.4)[1], K.at(-5.4, 0.0)[0], K.at(0.0, 13.2)[1], 0.3, BOLT_DARK, OUTLINE, 0.4)
        K.oval(d, K.at(-9.4, 12.3), 1.6, 1.6, BOLT, OUTLINE, 0.4)

    return K.piece(("front_eyes", mode), paint)


def _back_paw():
    """A paw seen from its heel, from its ankle: the heel pad and the toes
    either side of it, no lower than his paws stand."""
    au = BUILD.ankle_up

    def shape(d) -> None:
        K.oval(d, K.at(0.0, 0.4), 3.0, 2.8, WHITE)
        K.oval(d, K.at(0.0, au - 1.6), 4.4, 2.0, WHITE)

    def detail(d) -> None:
        K.oval(d, K.at(0.0, au - 1.2), 2.2, 1.2, FUR_DEEP)

    return K.solid(("back_paw",), shape, FUR, detail, outline=1.1, rim=0.3, shade=0.35, shade_colour=FUR_DEEP)


BODY = LeaningBody(X, _back_paw,
                   heads={"front": lambda pose: [(_front_skull(), "skull"), (_front_eyes(str(pose["eyes"])), "eyes")], "left": _left_layers,
                          "side": _side_layers(True), "side_left": _side_layers(False)},
                   mirror=())

#: His stance in the round: crouched, his long arms hanging in front of him,
#: as he rests.
STANCE = C.Stance(hands={"r": C.Hand(l=-4.0, pole=(-0.4, 0.4, -1.0), mode="soft"), "l": C.Hand(l=4.6, pole=(0.4, 0.4, -1.0), mode="soft")}, stagger=2.0)
_J = BODY.joints(STANCE.stagger)
_ELBOW, _ = O.two_bone(_J.shoulders["r"], _J.wrist(True, -4.0), BUILD.upper, BUILD.fore, (-0.4, 0.4, -1.0))
_SHOULDER = np.asarray(_J.shoulders["r"])
_BAND = tuple(_SHOULDER + 0.3 * (np.asarray(_ELBOW) - _SHOULDER))
_LEAN = float(X.full(X.rest)["lean"])

#: His gown, from the numbers of his own ``_torso``: level rings from his
#: neck to the torn hem, leaned as he is hunched.
GOWN_3D = W.Trunk(
    rings=BODY.leaned_rings([O.Ring(TOP - 0.5, 0.0, 0.2, 4.0, 3.6), O.Ring(TOP + 3.0, 0.0, 0.0, 8.0, 6.8), O.Ring(-18.0, 0.0, 0.0, 9.4, 7.6),
                             O.Ring(-4.0, 0.0, 0.0, 9.4, 7.6), O.Ring(14.0, 0.0, 0.0, 10.0, 8.2)]),
    garment=W.Garment(GOWN, GOWN_DARK, radius=9.0, features=[
        # The tear on his right side with his sewn skin in it, the stains,
        # his number, the seam and the tie down his back, the light line by
        # the hem, the hem torn in points.
        W.Patch(-50.0, -20.0, -18.4, -9.6, SKIN_SHADE), W.Across(-46.0, -24.0, -14.4, STITCH, width=0.35),
        W.Glow(5.0, -4.0, 2.6, 1.8, mix(GOWN, STAIN, 0.6)), W.Glow(-40.0, 6.0, 2.0, 2.8, mix(GOWN, STAIN, 0.5)),
        W.Path([(-4.0, -25.0), (-4.0, -21.0), (0.0, -21.0), (0.0, -25.0), (-4.0, -25.0)], FUR_DEEP, 0.35),
        W.Path([(4.0, -25.0), (8.0, -25.0), (5.0, -21.0)], FUR_DEEP, 0.35),
        W.Down(180.0, TOP + 3.4, 10.0, GOWN_DARK, width=0.5), W.Across(150.0, 180.0, -14.0, GOWN_DARK, width=0.6),
        W.Across(-180.0, 180.0, 9.6, GOWN_LIGHT, width=0.4), W.PointedHem(11.0, 14.6, 3.0, FUR_DEEP), W.Shade()]),
    shoulder=(tuple(np.asarray(BODY.tilt((-4.4, -26.6, 0.0), _LEAN)) + (0.0, BODY.drop(), 0.0)), (4.6, 5.0, 4.4)))

#: His wolf's head in 3D, for the views from behind: the skull and the long
#: muzzle, his torn ear and his whole one, the ruff round the back of his
#: neck, the sewn patch and the bolt on his right.
_SKULL = ((0.0, -1.6, -1.0), (7.0, 6.8, 7.0))
HEAD_3D = O.Head3D(
    skin=FUR, shade=FUR_DARK, deep=FUR_DEEP, skull=_SKULL, jaw=((0.0, 1.8, 5.0), (3.6, 3.4, 6.0)), nose=((0.0, -0.4, 10.6), (2.2, 2.0, 2.4)), ear=None,
    eye=(28.0, -2.4), eye_size=1.0, eye_white=EYE_WHITE, iris=IRIS, ink=OUTLINE,
    hair_colour=FUR, hair_shade=FUR_DARK, volumes=[((0.0, 3.4, -3.4), (8.0, 6.4, 6.0))],
    tufts=[((-4.0, -6.0, -1.0), (-5.6, -11.6, -1.8), 2.6), ((4.0, -6.0, -1.0), (5.4, -14.2, -1.6), 2.6)],
    lines=[O.circle((0.0, -0.6, 12.8), (0.0, 0.0, 1.0), 1.6, None, fill=NOSE, slack=1.2),
           O.circle(O.on_ellipsoid(*_SKULL, -40.0, -6.0, 0.2)[0], O.on_ellipsoid(*_SKULL, -40.0, -6.0)[1], 2.6, STITCH, 0.35, fill=SKIN, slack=1.0),
           O.circle((-6.6, 12.6, -1.0), (-1.0, 0.0, 0.0), 1.6, OUTLINE, 0.4, fill=BOLT, slack=1.0)])

ROUND = C.Round(
    DISPLAY_NAME, BODY,
    C.Look(
        HEAD_3D, GOWN_3D,
        back_pieces=[
            # The regime's band on his near arm.
            W.Prop("armband", _BAND, tuple(_ELBOW), lambda n: F.band(K, 8.6, 4.8), lead=5.0),
            W.Pinned("armband_emblem", _BAND, lambda: F.emblem(K, 2.2), lead=6.0),
        ]),
    STANCE)

if __name__ == "__main__":
    raise SystemExit(main())
