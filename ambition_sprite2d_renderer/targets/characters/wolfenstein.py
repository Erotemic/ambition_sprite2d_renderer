"""Sprite generator for Wolfenstein: the boss of Godwin Castle.

Jon (2026-10-15): "a boss character named Wolfenstein, that is a cross
between Frankenstein and a wolf. think Frankenstein with Insanity Wolf for a
head. this character is also a Nazi so he gets the armband."

The look: the body of Frankenstein's monster, seen three quarters from the
front and facing right. He is huge, about 240 cm: square heavy shoulders,
long arms, big grey-green hands with claws and stitches, bolts in his neck, a
black coat that is too short for him (its sleeves stop above his wrists),
dark trousers and heavy boots with thick soles. On his near (left) arm is the
red armband of the regime with its mark (``_evil_faction``: an invented cog,
not a real symbol).

On his neck is the head of a wolf, sewn on: a stitched seam goes round his
neck where the fur meets his skin. It is the wolf of the Insanity Wolf meme:
a grey wolf with eyes that are open too wide (white all round, small
pupils, red veins) that stare at you even from the side, a snarl of bared
teeth, the ears flat back, and a ruff.

He is menacing and he is funny; he is not cute. He holds nothing; there is
no drop shadow.

His attacks: a swipe of his claws (``slash``), a lunge with his teeth
(``attack_side``), an uppercut with his claws (``attack_up``) and a smash
with both fists (``attack_down``). He howls to taunt.

He is a person of ``_person_rig``: the bones and the frame are shared; the
build, the head, the clothes and every pose are his.
"""

from __future__ import annotations

import math
from typing import List

from ._ai_era_kit import OUTLINE, WHITE, RGBA, Point, ease, lerp, mix, turned
from . import _evil_faction as F
from . import _person_rig as R
from ._person_rig import Build, Person, Stamp, loop, shot

TARGET_NAME = "wolfenstein"
TARGET_BASENAME = TARGET_NAME
DISPLAY_NAME = "Wolfenstein"

TRAITS = ["story", "humanoid", "enemy", "boss", "combatant", "authoritarian", "monster", "wolf", "brawler"]

ACTOR_METADATA = {
    "actor": {"character_id": "npc_wolfenstein_boss", "display_name": DISPLAY_NAME},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Heavy",
        "traits": TRAITS,
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {"walk": True, "jump": True, "climb": None, "fly": None, "swim": None, "crawl": None, "use_lifts": None,
                      "door_access": []},
        "interactions": {"talk": False, "trade": None, "carry": None, "open_doors": []},
    },
    "brain": {"default_preset": "melee_brute_brute"},
    "actions": {"default_preset": "brute_lunge"},
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
                {"t": 0.62, "event": "hitbox_active_end", "source": "explicit.profile.combat_humanoid"},
            ],
        },
        "combat.hurt": {"animation": "hit", "events": []},
        "combat.death": {"animation": "death", "events": []},
    },
    "authoring_description": (
        "Wolfenstein: the body of Frankenstein's monster with the head of Insanity Wolf sewn "
        "onto it, in a coat too short for him and the red armband of the Evil dimension's "
        "regime (an invented cog; no real symbol). The boss of Godwin Castle."
    ),
    "gameplay_description": (
        "A huge melee boss: a claw swipe, a lunging bite, a claw uppercut and a two-fisted "
        "smash into the floor. He howls to taunt. He holds nothing."
    ),
    "dialogue_hints": {"barks": ["AWOOOOO.", "SEWN TOGETHER. STILL BETTER THAN YOU.", "PAPERS. THEN I EAT THE PAPERS."]},
}

COAT: RGBA = (56, 54, 64, 255)
COAT_DARK: RGBA = (36, 34, 44, 255)
COAT_LIGHT: RGBA = (92, 90, 104, 255)
TROUSER: RGBA = (74, 70, 68, 255)
TROUSER_DARK: RGBA = (50, 48, 48, 255)
BOOT: RGBA = (44, 40, 44, 255)
BOOT_DARK: RGBA = (26, 24, 28, 255)
BOOT_LIGHT: RGBA = (86, 82, 90, 255)
SKIN: RGBA = (138, 162, 122, 255)
SKIN_SHADE: RGBA = (108, 130, 98, 255)
SKIN_DEEP: RGBA = (68, 86, 64, 255)
STITCH: RGBA = (40, 30, 34, 255)
CLAW: RGBA = (46, 40, 38, 255)
CLAW_TIP: RGBA = (214, 206, 186, 255)
BOLT: RGBA = (170, 172, 176, 255)
BOLT_DARK: RGBA = (96, 98, 106, 255)
FUR: RGBA = (128, 132, 140, 255)
FUR_DARK: RGBA = (80, 82, 94, 255)
FUR_DEEP: RGBA = (54, 54, 66, 255)
FUR_LIGHT: RGBA = (196, 196, 196, 255)
NOSE: RGBA = (24, 22, 26, 255)
GUM: RGBA = (150, 44, 56, 255)
MOUTH: RGBA = (74, 18, 30, 255)
TONGUE: RGBA = (214, 96, 110, 255)
TOOTH: RGBA = (246, 240, 220, 255)
EYE_WHITE: RGBA = (252, 250, 240, 255)
VEIN: RGBA = (220, 70, 70, 255)
IRIS: RGBA = (232, 196, 70, 255)
EAR_INNER: RGBA = (176, 136, 140, 255)
SPARK: RGBA = (255, 238, 184, 255)
SPARK_DARK: RGBA = (214, 122, 58, 255)
SLASH: RGBA = (250, 246, 236, 255)
SLASH_DARK: RGBA = (150, 150, 170, 255)
DUST: RGBA = (196, 186, 170, 255)
DUST_DARK: RGBA = (122, 112, 102, 255)

#: About 240 cm. ``height`` is the top of his skull as he stands, hunched
#: (measured from the idle row); his ears lie back a little over it. A long
#: trunk, long arms, heavy legs.
BUILD = Build(hip_up=64.0, thigh=32.0, shin=31.0, neck=(2.0, -54.0), upper=30.0, fore=28.0, near_shoulder=(-9.0, -49.0), far_shoulder=(10.0, -48.4),
              near_hip=(-6.0, 0.0), far_hip=(6.0, 0.0), ankle_up=5.0, head_up=(7.0, -30.0), throat=(-1.0, 12.0), height=159.0, half_width=(19.0, 22.0))

X = Person(TARGET_NAME, BUILD, frame=(320, 256), ground=240.0, cx=150.0)
K = X.K
P = X.P
TOP = BUILD.neck[1] - 2.0


def stitches(d, pts, tick: float = 1.6, every: float = 2.6, width: float = 0.5) -> None:
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


# ---- The coat ----------------------------------------------------------------


def _coat(d, hb: float, hf: float) -> None:
    """The front of his coat: a high collar, a lapel, big buttons, a patch
    sewn on, the hem."""
    del hb
    K.poly(d, [K.at(-6.0, TOP - 2.0), K.at(9.0, TOP - 2.0), K.at(12.0, TOP + 5.0), K.at(5.0, TOP + 9.0), K.at(-7.0, TOP + 5.0)], COAT_DARK)
    K.line(d, [K.at(6.0, TOP + 7.0), K.at(9.4, -30.0), K.at(10.0, -12.0), K.at(10.4 + hf * 0.5, 14.0)], COAT_DARK, 0.9)
    K.line(d, [K.at(5.0, TOP + 8.0), K.at(8.4, -30.0)], COAT_LIGHT, 0.6)
    for y in (-36.0, -24.0, -12.0):
        K.oval(d, K.at(11.6, y), 1.6, 1.6, COAT_DARK, OUTLINE, 0.4)
    # A patch, sewn on with big stitches.
    K.poly(d, [K.at(-11.0, -24.0), K.at(-2.0, -25.0), K.at(-1.4, -15.0), K.at(-10.4, -14.4)], (70, 64, 70, 255))
    stitches(d, [K.at(-11.0, -24.0), K.at(-2.0, -25.0), K.at(-1.4, -15.0), K.at(-10.4, -14.4), K.at(-11.0, -24.0)], tick=1.0, every=2.4, width=0.45)
    K.line(d, [K.at(-40.0, 12.0), K.at(40.0, 12.0)], COAT_DARK, 0.7)


# Square, heavy shoulders: the top of the trunk is flat from the neck out.
X.torso = R.make_torso(K, ("wolfenstein",), COAT, COAT_DARK, back=(17.0, 17.0, 14.4, 15.4), front=(16.6, 17.0, 15.0, 16.0), hem_y=14.0, top=TOP,
                       shoulders=((-9.0, -47.0), (10.0, -46.4)), shoulder_r=(9.4, 9.0), neck=(-7.0, 7.0), shade_from=11.0, detail=_coat)
X.neck = R.make_neck(K, SKIN_SHADE, 13.0)

# ---- The limbs ---------------------------------------------------------------

X.upper_arm = lambda near: [(0.0, 1.0, 15.0, 13.0, COAT if near else COAT_DARK)]
# The sleeve stops short of his wrist: the skin is painted first, so the end
# of the sleeve is over it.
X.forearm = lambda near: [(0.66, 1.0, 9.6, 9.0, SKIN if near else SKIN_SHADE), (0.0, 0.7, 13.0, 12.0, COAT if near else COAT_DARK)]
X.thigh = lambda near: [(0.0, 1.0, 16.0, 13.4, TROUSER if near else TROUSER_DARK)]
X.shin = lambda near: [(0.0, 1.0, 13.4, 11.4, TROUSER if near else TROUSER_DARK)]


def _hand(mode: str, near: bool):
    """A big hand along +x from its wrist at ``home``, with claws, and a
    seam sewn across its back."""
    skin = SKIN if near else SKIN_SHADE
    fingers = {
        "open": [((8.0, -4.6), (15.0, -8.6)), ((9.0, -1.6), (17.0, -3.0)), ((9.0, 1.6), (17.0, 2.6)), ((8.0, 4.6), (14.6, 7.6))],
        "flat": [((8.0, -3.6), (17.4, -4.0)), ((9.0, -1.2), (18.4, -1.2)), ((9.0, 1.2), (18.2, 1.4)), ((8.0, 3.6), (16.8, 4.0))],
        "soft": [((8.0, -3.6), (12.6, 1.0)), ((9.0, -1.2), (13.6, 3.4)), ((9.0, 1.2), (13.2, 5.4)), ((8.0, 3.6), (11.6, 7.0))],
        "fist": [],
    }[mode if mode in ("open", "flat", "soft") else "fist"]
    thumb = ((4.0, -5.0), (7.4, -9.4)) if mode == "open" else ((4.0, -5.0), (8.6, -6.6))

    def claw(a: Point, b: Point, reach: float) -> List[Point]:
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        ux, uy = dx / length, dy / length
        return [K.at(b[0] - uy * 1.3, b[1] + ux * 1.3), K.at(b[0] + ux * reach, b[1] + uy * reach), K.at(b[0] + uy * 1.3, b[1] - ux * 1.3)]

    claws = [claw(a, b, 4.2) for a, b in fingers] + ([claw(*thumb, 3.0)] if mode == "open" else [])
    if mode == "fist":
        claws = [[K.at(8.6, y - 1.0), K.at(11.6, y + 0.4), K.at(8.6, y + 1.2)] for y in (-3.4, 0.0, 3.4)]

    def shape(d) -> None:
        K.rrect(d, K.home[0] - 2.0, K.home[1] - 5.2, K.home[0] + 3.0, K.home[1] + 5.2, 1.6, WHITE)
        if mode == "fist":
            K.oval(d, K.at(5.6, 0.0), 6.4, 6.6, WHITE)
        else:
            K.oval(d, K.at(5.0, 0.0), 6.0, 6.0, WHITE)
        for a, b in fingers:
            K.stroke(d, [K.at(*a), K.at(*b)], WHITE, 3.4)
        K.stroke(d, [K.at(*thumb[0]), K.at(*thumb[1])], WHITE, 3.4)
        for c in claws:
            K.poly(d, c, WHITE)

    def detail(d) -> None:
        for c in claws:
            K.poly(d, c, CLAW)
            K.line(d, [c[1], ((c[0][0] + c[2][0]) / 2.0 * 0.4 + c[1][0] * 0.6, (c[0][1] + c[2][1]) / 2.0 * 0.4 + c[1][1] * 0.6)], CLAW_TIP, 0.6)
        if mode == "fist":
            K.line(d, [K.at(7.6, -4.6), K.at(9.4, -1.6), K.at(9.4, 1.6), K.at(7.6, 4.6)], SKIN_DEEP, 0.7)
        stitches(d, [K.at(2.4, -5.6), K.at(3.4, 0.0), K.at(2.6, 5.6)], tick=1.0, every=2.2, width=0.45)

    return K.solid(("hand", mode, near), shape, skin, detail, outline=1.3, rim=0.3, shade=0.35, shade_colour=SKIN_DEEP)


X.hand = _hand


def _boot(near: bool):
    """A heavy boot on a thick sole, from its ankle at ``home``."""
    colour = BOOT if near else mix(BOOT, BOOT_DARK, 0.6)
    au = BUILD.ankle_up

    def shape(d) -> None:
        K.rrect(d, K.home[0] - 7.0, K.home[1] - 5.0, K.home[0] + 9.0, K.home[1] + au - 2.0, 3.0, WHITE)
        K.oval(d, K.at(10.0, au - 4.6), 7.4, 4.8, WHITE)
        K.rrect(d, K.home[0] - 8.0, K.home[1] + au - 4.0, K.home[0] + 18.4, K.home[1] + au, 1.2, WHITE)

    def detail(d) -> None:
        K.rrect(d, K.home[0] - 9.0, K.home[1] + au - 4.0, K.home[0] + 20.0, K.home[1] + au + 1.0, 0.0, BOOT_DARK)
        K.line(d, [K.at(-9.0, au - 4.0), K.at(20.0, au - 4.0)], BOOT_LIGHT, 0.6)
        K.line(d, [K.at(4.0, -3.0), K.at(13.0, -1.4)], BOOT_LIGHT, 0.7)

    return K.solid(("boot", near), shape, colour, detail, outline=1.3, rim=0.25, shade=0.3, shade_colour=BOOT_DARK)


X.shoe = _boot

# ---- The head ----------------------------------------------------------------
#
# The head is in head pixels from its middle, facing right. It is the head of
# a wolf, larger than a man's.

NEAR_EYE = (5.0, -4.6)
FAR_EYE = (12.6, -5.8)
#: Where the lower jaw turns.
HINGE = (5.0, 5.4)
UPPER_LIP = [(7.0, 5.6), (12.0, 5.8), (17.0, 5.6), (21.4, 5.2)]


def _jaw_points(open_: float) -> List[Point]:
    """The lower jaw, open ``open_`` degrees about ``HINGE``."""
    pts = [(4.0, 5.6), (20.6, 6.4), (21.0, 8.2), (18.4, 11.6), (9.0, 12.8), (3.0, 10.6)]
    return [(HINGE[0] + p[0], HINGE[1] + p[1]) for p in (turned((x - HINGE[0], y - HINGE[1]), open_) for x, y in pts)]


def _jaw(open_: float):
    """His mouth, open ``open_`` degrees: its inside, his tongue, his lower
    jaw and its teeth. It is under his head."""
    jaw = _jaw_points(open_)

    def at(p: Point) -> Point:
        return K.at(*p)

    def lower_teeth() -> List[List[Point]]:
        out = []
        top = [jaw[0], jaw[1]]
        for k, (t, tall) in enumerate(((0.32, 2.0), (0.46, 1.8), (0.6, 2.0), (0.76, 3.4), (0.9, 2.2))):
            x, y = lerp(top[0][0], top[1][0], t), lerp(top[0][1], top[1][1], t)
            up = turned((0.0, -tall), open_)
            side = turned((1.0, 0.0), open_)
            out.append([(x - side[0], y - side[1]), (x + up[0], y + up[1]), (x + side[0], y + side[1])])
            del k
        return out

    teeth = lower_teeth()

    def shape(d) -> None:
        K.poly(d, [at(p) for p in [HINGE] + UPPER_LIP[1:] + [jaw[1], jaw[0]]], WHITE)
        K.poly(d, [at(p) for p in jaw], WHITE)
        for tooth in teeth:
            K.poly(d, [at(p) for p in tooth], WHITE)

    def detail(d) -> None:
        K.poly(d, [at(p) for p in [HINGE] + UPPER_LIP[1:] + [jaw[1], jaw[0]]], MOUTH)
        if open_ > 10.0:
            mid = ((UPPER_LIP[2][0] + jaw[1][0]) / 2.0 - 4.0, (UPPER_LIP[2][1] + jaw[1][1]) / 2.0 + 1.0)
            K.oval(d, at(mid), 5.0, 1.8 + open_ * 0.05, TONGUE)
        K.poly(d, [at(p) for p in jaw[2:]] + [at(jaw[0]), at(jaw[1])], FUR)
        K.line(d, [at(jaw[0]), at(jaw[1])], GUM, 0.9)
        K.poly(d, [at(jaw[5]), at(jaw[4]), at(jaw[3]), at((jaw[3][0] - 3.0, jaw[3][1] - 1.0)), at((jaw[5][0] + 2.0, jaw[5][1] - 1.0))], FUR_LIGHT)
        for tooth in teeth:
            K.poly(d, [at(p) for p in tooth], TOOTH)

    return K.solid(("jaw", round(open_, 1)), shape, FUR, detail, outline=1.3, rim=0.2, shade=0.3, shade_colour=FUR_DEEP)


def _skull():
    """His head: the skull, the ruff, the ears laid back, the muzzle with its
    upper teeth bared, the nose."""
    upper_teeth = []
    for x, tall in ((8.4, 2.0), (10.6, 2.2), (12.8, 2.0), (15.0, 2.2), (17.6, 4.4), (20.0, 2.6)):
        upper_teeth.append([(x - 1.0, 5.4), (x, 5.6 + tall), (x + 1.0, 5.4)])
    ruff = [(-9.0, -10.0), (-16.0, -9.0), (-13.4, -5.6), (-19.0, -2.4), (-14.6, 0.6), (-19.4, 4.6), (-13.6, 6.4), (-16.0, 11.4), (-9.4, 10.6),
            (-9.0, 15.6), (-4.0, 12.6), (-0.6, 16.4), (2.6, 12.8), (6.0, 14.6), (6.4, 9.0), (2.0, 4.0)]
    near_ear = [(-5.0, -10.0), (-23.0, -12.6), (-16.0, -5.0), (-9.0, -3.0)]
    far_ear = [(0.0, -12.6), (-17.0, -17.4), (-11.0, -9.4), (-5.0, -8.0)]
    muzzle = [(3.0, -9.0), (10.0, -9.6), (17.0, -6.6), (22.6, -4.4), (25.4, -2.0), (25.2, 1.4), (22.6, 3.4), (21.4, 5.4), (7.0, 5.6), (3.0, 4.0)]

    def at(p: Point) -> Point:
        return K.at(*p)

    def shape(d) -> None:
        K.poly(d, [at(p) for p in far_ear], WHITE)
        K.oval(d, K.at(-1.6, -2.4), 12.0, 11.0, WHITE)
        K.oval(d, K.at(4.4, 2.0), 9.0, 7.6, WHITE)
        K.poly(d, [at(p) for p in ruff], WHITE)
        K.poly(d, [at(p) for p in muzzle], WHITE)
        K.poly(d, [at(p) for p in near_ear], WHITE)
        for tooth in upper_teeth:
            K.poly(d, [at(p) for p in tooth], WHITE)

    def detail(d) -> None:
        # The far ear is in shade; the near ear shows its inside.
        K.poly(d, [at(p) for p in far_ear], FUR_DARK)
        K.poly(d, [at(p) for p in near_ear], FUR)
        K.poly(d, [at((-7.0, -8.6)), at((-19.6, -11.6)), at((-14.4, -6.2)), at((-9.4, -4.8))], EAR_INNER)
        K.line(d, [at((-5.0, -10.0)), at((-23.0, -12.6)), at((-16.0, -5.0))], OUTLINE, 0.6)
        # The pale muzzle, cheeks and throat.
        K.poly(d, [at((2.0, 0.0)), at((10.0, 1.4)), at((21.0, 3.0)), at((21.4, 6.0)), at((2.0, 7.0)), at((-2.0, 4.0))], FUR_LIGHT)
        K.poly(d, [at((-6.0, 8.0)), at((4.0, 8.0)), at((6.0, 16.0)), at((-6.0, 16.0))], mix(FUR, FUR_LIGHT, 0.5))
        # The dark mask round his eyes, and the bridge of his nose.
        K.oval(d, at(NEAR_EYE), 5.6, 5.0, FUR_DARK)
        K.oval(d, at(FAR_EYE), 4.4, 4.2, FUR_DARK)
        K.line(d, [at((9.0, -9.0)), at((16.6, -6.4)), at((22.0, -4.0))], FUR_LIGHT, 0.8)
        # The snarl: the skin of his muzzle is pulled up in folds.
        for x in (12.0, 14.6, 17.0):
            K.line(d, [at((x - 1.0, -7.2)), at((x + 0.4, -5.2)), at((x - 0.4, -3.4))], FUR_DEEP, 0.6)
        # Fur on his skull and ruff.
        for a, b in (((-8.0, -6.0), (-12.0, -2.0)), ((-10.0, 2.0), (-14.0, 5.0)), ((-6.0, 6.0), (-10.0, 10.0)), ((-2.0, -11.0), (-6.0, -8.0)),
                     ((-1.0, 10.0), (-3.0, 14.0))):
            K.line(d, [at(a), at(b)], FUR_DARK, 0.7)
        # His gums, his upper teeth, his nose.
        K.line(d, [at(p) for p in UPPER_LIP], GUM, 1.0)
        for tooth in upper_teeth:
            K.poly(d, [at(p) for p in tooth], TOOTH)
        K.oval(d, K.at(23.6, -1.4), 2.8, 2.4, NOSE)
        K.oval(d, K.at(22.8, -2.4), 0.9, 0.6, (120, 120, 130, 255))

    return K.solid(("skull",), shape, FUR, detail, outline=1.3, rim=0.3, shade=0.35, shade_colour=FUR_DEEP)


def _eyes(mode: str):
    """His eyes. Open, they are the eyes of the meme: white all round, small
    pupils that look at you, red veins."""

    def paint(d) -> None:
        for (ex, ey), rx, ry in ((NEAR_EYE, 4.6, 4.4), (FAR_EYE, 3.5, 3.7)):
            c = K.at(ex, ey)
            if mode in ("closed", "dead"):
                r = rx * 0.7
                for s in (-1.0, 1.0):
                    K.line(d, [(c[0] - r, c[1] - r * s), (c[0] + r, c[1] + r * s)], OUTLINE, 0.9)
                continue
            if mode == "wince":
                K.line(d, [(c[0] - rx, c[1] - 1.8), (c[0] + rx * 0.5, c[1]), (c[0] - rx, c[1] + 1.8)], OUTLINE, 1.0)
                continue
            K.oval(d, c, rx + 0.6, ry + 0.6, OUTLINE)
            K.oval(d, c, rx, ry, EYE_WHITE)
            for ang, length in ((200.0, 0.75), (330.0, 0.7), (110.0, 0.65), (20.0, 0.6)):
                a = math.radians(ang)
                K.line(d, [(c[0] + math.cos(a) * rx * 0.95, c[1] + math.sin(a) * ry * 0.95),
                           (c[0] + math.cos(a) * rx * (0.95 - length * 0.5), c[1] + math.sin(a) * ry * (0.95 - length * 0.5) + 0.3)], VEIN, 0.55)
            look = (c[0] - 0.4 * rx / 4.0, c[1] + 0.2)
            K.oval(d, look, rx * 0.26, rx * 0.26, IRIS)
            K.oval(d, look, rx * 0.15, rx * 0.15, OUTLINE)

    return K.piece(("eyes", mode), paint)


def _brows(mood: int):
    """Heavy dark fur over his eyes, the inner ends down."""
    lift = -1.4 if mood > 0 else 0.0

    def paint(d) -> None:
        K.stroke(d, [K.at(-0.4, -10.2 + lift), K.at(4.0, -10.4 + lift), K.at(8.6, -8.0 + lift + (0.0 if mood > 0 else 1.0))], FUR_DEEP, 2.0)
        K.stroke(d, [K.at(10.4, -9.6 + lift + (0.0 if mood > 0 else 1.2)), K.at(13.6, -10.6 + lift), K.at(16.0, -9.6 + lift)], FUR_DEEP, 1.7)

    return K.piece(("brows", mood), paint)


def _seam():
    """The seam round his neck, where the fur stops and his own skin starts.
    From the middle of his head."""

    def paint(d) -> None:
        stitches(d, [K.at(-8.0, 15.2), K.at(-3.0, 16.6), K.at(2.0, 16.0), K.at(6.4, 14.4)], tick=1.4, every=2.2, width=0.55)

    return K.piece(("seam",), paint)


def _bolts():
    """The bolts through his neck, from a point on the line of his neck: +x
    is across his neck to its front, +y down it. The near bolt is a nut on
    the side of his neck; the far one comes out of the front of it."""

    def paint(d) -> None:
        K.rrect(d, K.at(-6.4, 0.0)[0], K.at(0.0, -1.3)[1], K.at(-1.0, 0.0)[0], K.at(0.0, 1.3)[1], 0.4, BOLT_DARK, OUTLINE, 0.5)
        hexagon = [K.at(-1.4 + 2.8 * math.cos(math.tau * k / 6.0 + 0.5), 2.8 * math.sin(math.tau * k / 6.0 + 0.5)) for k in range(6)]
        K.poly(d, hexagon, BOLT, OUTLINE, 0.5)
        K.oval(d, K.at(-1.4, 0.0), 1.0, 1.0, BOLT_DARK)
        K.rrect(d, K.at(5.0, 0.0)[0], K.at(0.0, -1.3)[1], K.at(9.4, 0.0)[0], K.at(0.0, 1.3)[1], 0.4, BOLT, OUTLINE, 0.5)
        K.rrect(d, K.at(9.0, 0.0)[0], K.at(0.0, -2.2)[1], K.at(10.6, 0.0)[0], K.at(0.0, 2.2)[1], 0.3, BOLT, OUTLINE, 0.5)

    return K.piece(("bolts",), paint)


def _neck_bolts(ctx) -> List[Stamp]:
    """The bolts, on the part of his neck that shows."""
    top = turned(BUILD.throat, ctx.turn)
    top = (ctx.head[0] + top[0], ctx.head[1] + top[1])
    at = (lerp(ctx.neck[0], top[0], 0.55), lerp(ctx.neck[1], top[1], 0.55))
    return [(_bolts(), at, "bolts", math.degrees(math.atan2(top[1] - ctx.neck[1], top[0] - ctx.neck[0])) + 90.0)]


X.layers["over_torso"].append(_neck_bolts)


def _open(mouth: str) -> float:
    return {"big": 34.0, "open": 18.0, "o": 12.0}.get(mouth, 5.0)


def _head_layers(pose):
    return [(_jaw(_open(str(pose["mouth"]))), "jaw"), (_skull(), "skull"), (_eyes(str(pose["eyes"])), "eyes"), (_brows(R.brow_mood(pose)), "brows"),
            (_seam(), "seam")]


X.head_layers = _head_layers


def _armband(ctx) -> List[Stamp]:
    """The regime's band and its mark, on his near arm, over the sleeve."""
    if ctx.pose["arm"] == "under":
        return []
    t = 0.36
    at = (lerp(ctx.shoulder[0], ctx.elbow[0], t), lerp(ctx.shoulder[1], ctx.elbow[1], t))
    turn = math.degrees(math.atan2(ctx.elbow[1] - ctx.shoulder[1], ctx.elbow[0] - ctx.shoulder[0]))
    return [(F.band(K, 16.0, 9.0), at, "armband", turn), (F.emblem(K, 4.0), at, "armband_emblem", 0.0)]


X.layers["front"].append(_armband)

# ---- How he stands -----------------------------------------------------------

# Hunched, his head forward, his long arms hanging in front of him.
X.set_rest(lean=9.0, head=(1.0, 1.0, 4.0), na=(7.0, 30.0), fa=(9.0, 29.5), nh="soft", fh="soft", nf=(-6.0, 0.0, 0.0), ff=(7.0, 0.0, 0.0),
           mouth="flat", brows=-1.0)


@X.row
def idle(i: int, n: int):
    # He breathes hard, and the arms swing a little.
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.8 + 0.8 * s), lean=9.0 + 1.6 * s, head=(1.0, 1.0 - 0.6 * s, 4.0 + 2.0 * c), na=(7.0 + 1.2 * c, 30.0 - 0.8 * s),
             fa=(9.0 - 1.2 * c, 29.5 - 0.8 * s), mouth="open" if s > 0.5 else "flat")


@X.row
def walk(i: int, n: int):
    # Stiff: the legs hardly bend, he rocks from foot to foot, and his arms
    # are straight out in front of him.
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 7.0, 3.0)
    return P(hip=(0.5, 1.8 * abs(math.cos(ph))), lean=5.0 + 2.5 * c, head=(1.0, 0.0, 2.0 - 3.0 * c), na=(31.0, -1.0 + 1.5 * s), fa=(31.0, 1.0 - 1.5 * s),
             nh="soft", fh="soft", nf=nf, ff=ff, hem=(1.0 + abs(c), 0.5 + abs(c)))


@X.row
def run(i: int, n: int):
    # A lope: low and long, the wolf in him; the arms swing low.
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 15.0, 11.0, 0.0)
    return P(hip=(3.0, 3.0 + 2.2 * math.cos(2.0 * ph)), lean=30.0, head=(3.0, 2.0, -18.0), na=(4.0 - 14.0 * c, 24.0 + 3.0 * s), fa=(6.0 + 14.0 * c, 24.0 - 3.0 * s),
             nh="open", fh="open", nf=nf, ff=ff, mouth="open", hem=(6.0, 1.0))


RISE = P(hip=(0.0, -2.0), lean=6.0, head=(1.0, 0.0, -8.0), na=(-12.0, -16.0), nab=-1.0, fa=(21.0, -6.0), nh="open", fh="open", nf=(-4.0, -12.0, 26.0),
         ff=(7.0, -16.0, 10.0), mouth="big", hem=(2.0, 3.0))
APEX = P(hip=(0.0, -2.0), lean=4.0, head=(1.0, 0.0, -2.0), na=(-16.0, -8.0), nab=-1.0, fa=(22.0, 0.0), nh="open", fh="open", nf=(-4.0, -9.0, 20.0),
         ff=(8.0, -12.0, 6.0), mouth="open", hem=(3.0, 3.0))
FALL = P(hip=(0.0, -3.0), lean=-2.0, head=(0.0, 0.0, 6.0), na=(-22.0, -4.0), nab=-1.0, fa=(23.0, -3.0), nh="open", fh="open", nf=(-7.0, -4.0, 22.0),
         ff=(7.0, -8.0, 8.0), mouth="big", hem=(5.0, 5.0))


@X.row
def jump(i: int, n: int):
    wind = P(hip=(-1.0, 12.0), lean=22.0, head=(2.0, 2.0, -6.0), na=(-8.0, 26.0), fa=(-4.0, 27.0), nf=(-7.0, 0.0, 0.0), ff=(8.0, 0.0, 0.0))
    return X.keys(shot(i, n), [(0.0, wind), (0.3, RISE), (0.6, RISE), (1.0, APEX)])


@X.row
def fall(i: int, n: int):
    _, s, c = loop(i, n)
    return dict(FALL, na=(-22.0 + 2.0 * s, -4.0 - 3.0 * c), fa=(23.0 - 2.0 * s, -3.0 + 3.0 * c), nf=(-7.0, -4.0 + 1.5 * s, 22.0), ff=(7.0, -8.0 - 1.5 * s, 8.0))


#: Down on his heels, a fist on the floor.
LANDED = P(hip=(0.0, 17.0), lean=30.0, head=(3.0, 2.0, -6.0), na=(16.0, 26.0), fa=(19.0, 22.0), nh="fist", fh="open", nf=(-9.0, 0.0, 0.0), ff=(9.0, 0.0, 0.0),
           mouth="big", hem=(4.0, 3.0))


@X.row
def land_hard(i: int, n: int):
    return X.keys(shot(i, n), [(0.0, FALL), (0.2, LANDED), (0.6, LANDED), (1.0, X.full(P()))])


STRUCK = P(hip=(-4.0, 2.0), lean=-14.0, head=(-2.0, -1.0, -20.0), na=(4.0, 26.0), fa=(14.0, 18.0), nh="open", fh="open", nf=(-8.0, 0.0, 0.0),
           ff=(8.0, -5.0, -22.0), eyes="wince", mouth="big", brows=1.0, off=(-3.0, 0.0), hem=(0.0, 5.0))


@X.row
def hit(i: int, n: int):
    return X.keys(shot(i, n), [(0.0, P(lean=4.0, mouth="o")), (0.25, STRUCK), (0.6, STRUCK), (1.0, P(lean=6.0))])


#: On his back, his boots up.
SUPINE = P(rot=-90.0, hip=(-2.0, 25.5), off=(13.0, 0.0), head=(0.0, 0.0, 6.0), na=(8.0, 24.0), fa=(4.0, 22.0), nh="open", fh="open",
           nf=(-4.5, 25.0, 0.0), ff=(4.5, 25.0, -10.0), eyes="dead", mouth="open", brows=0.0, lean=0.0)


@X.row
def death(i: int, n: int):
    # He howls once, and goes over backward like a tree.
    last = P(hip=(-2.0, 0.0), lean=-14.0, head=(-1.0, -1.0, -36.0), na=(-6.0, 28.0), fa=(10.0, 26.0), nh="open", fh="open", eyes="wince", mouth="big")
    toppling = X.blend(last, SUPINE, 0.5)
    toppling = dict(toppling, off=(toppling["off"][0], toppling["off"][1] - 8.0))
    return X.keys(shot(i, n), [(0.0, STRUCK), (0.25, last), (0.45, toppling), (0.62, SUPINE), (1.0, SUPINE)])


#: His head back, his chest up, his fists low and out: the howl.
HOWL = P(hip=(0.0, 1.0), lean=-10.0, head=(-2.0, -1.0, -42.0), na=(-14.0, 27.0), fa=(18.0, 26.0), nh="fist", fh="fist", nf=(-8.0, 0.0, 0.0),
         ff=(8.0, 0.0, 0.0), mouth="big", hem=(1.0, 1.0))


@X.row
def taunt(i: int, n: int):
    _, s, _c = loop(i, n)
    breath = P(hip=(0.0, 4.0), lean=18.0, head=(2.0, 2.0, 10.0), na=(6.0, 30.0), fa=(8.0, 29.0), mouth="flat")
    held = dict(HOWL, head=(-2.0, -1.0, -42.0 + 2.0 * s))
    return X.keys(shot(i, n), [(0.0, X.full(P())), (0.15, breath), (0.35, HOWL), (0.85, held), (1.0, X.full(P()))])


# ---- His attacks -------------------------------------------------------------

#: Ready: crouched a little, claws open, the near hand high.
READY = P(hip=(-1.0, 4.0), lean=14.0, head=(2.0, 1.0, -2.0), na=(14.0, 4.0), fa=(18.0, 10.0), nh="open", fh="open", nf=(-9.0, 0.0, 0.0), ff=(9.0, 0.0, 0.0),
          mouth="open")


def _swing(u: float) -> float:
    """How far the claw swipe has gone, 0 to 1."""
    return ease(max(0.0, min(1.0, (u - 0.2) / 0.45)))


def _swipe_angle(u: float) -> float:
    return lerp(-150.0, 60.0, _swing(u))


@X.row
def slash(i: int, n: int):
    # His near claw comes over from behind his head and down through you.
    u = shot(i, n)
    swing = _swing(u)
    a = math.radians(_swipe_angle(u))
    hand = (31.0 * math.cos(a), 31.0 * math.sin(a))
    base = dict(READY, hip=(lerp(-3.0, 6.0, swing), 4.0), lean=lerp(-4.0, 24.0, swing), na=hand, nab=-1.0 if hand[1] < -8.0 and hand[0] < 8.0 else 1.0,
                arm="under" if hand[1] < -6.0 and hand[0] > -18.0 else "over", fa=(lerp(18.0, -8.0, swing), 16.0), nf=(-10.0, 0.0, 14.0 * swing),
                ff=(lerp(9.0, 13.0, swing), 0.0, 0.0), mouth="big" if 0.2 < u < 0.8 else "open", hem=(5.0 * swing, 1.0))
    if u > 0.8:
        return X.blend(base, READY, ease((u - 0.8) / 0.2))
    return base


#: The lunge: all of him forward behind his open jaws.
LUNGE = P(hip=(12.0, 8.0), lean=38.0, head=(6.0, 1.0, -14.0), na=(-10.0, 24.0), nab=-1.0, fa=(-6.0, 26.0), nh="open", fh="open", nf=(-14.0, 0.0, 30.0),
          ff=(14.0, 0.0, 0.0), mouth="big", hem=(8.0, 0.0))


@X.row
def attack_side(i: int, n: int):
    # A lunging bite: back, then the whole of him and his jaws at you.
    back = P(hip=(-4.0, 6.0), lean=-4.0, head=(-1.0, 0.0, -10.0), na=(12.0, 14.0), fa=(16.0, 12.0), nh="open", fh="open", nf=(-8.0, 0.0, 0.0),
             ff=(8.0, 0.0, -8.0), mouth="open")
    snap = dict(LUNGE, mouth="flat", head=(7.0, 1.5, -10.0))
    return X.keys(shot(i, n), [(0.0, READY), (0.25, back), (0.45, LUNGE), (0.6, snap), (0.78, snap), (1.0, READY)])


#: The uppercut: his claw high in front of him.
UPPER = P(hip=(3.0, -1.0), lean=-8.0, head=(0.0, 0.0, -16.0), na=(18.0, -24.0), nab=1.0, fa=(-4.0, 22.0), nh="open", fh="open", nf=(-8.0, 0.0, 12.0),
          ff=(9.0, -1.0, 14.0), mouth="big", hem=(2.0, 2.0))


@X.row
def attack_up(i: int, n: int):
    dip = dict(READY, hip=(0.0, 12.0), lean=24.0, na=(8.0, 26.0), head=(2.0, 1.0, 2.0))
    return X.keys(shot(i, n), [(0.0, READY), (0.25, dip), (0.45, UPPER), (0.75, UPPER), (1.0, READY)])


#: Both fists high over his head.
RAISED = P(hip=(-1.0, 0.0), lean=-12.0, head=(-1.0, 1.0, 8.0), na=(9.0, -32.0), nab=-1.0, fa=(6.0, -32.0), fab=-1.0, arm="over", nh="fist", fh="fist",
           nf=(-9.0, 0.0, 0.0), ff=(9.0, 0.0, 0.0), mouth="big")
#: Both fists in the floor in front of him.
SMASH = P(hip=(4.0, 16.0), lean=40.0, head=(3.0, 2.0, -16.0), na=(24.0, 26.0), fa=(22.0, 28.0), nh="fist", fh="fist", nf=(-11.0, 0.0, 0.0),
          ff=(11.0, 0.0, 0.0), mouth="big", hem=(5.0, 3.0))


@X.row
def attack_down(i: int, n: int):
    # The hammer: both fists up, together, and down into the floor.
    return X.keys(shot(i, n), [(0.0, READY), (0.3, RAISED), (0.42, dict(RAISED, lean=-15.0)), (0.55, SMASH), (0.82, SMASH), (1.0, READY)])


X.rows = [("idle", 8, 160), ("walk", 8, 125), ("run", 8, 85), ("jump", 6, 100), ("fall", 6, 100), ("land_hard", 6, 90), ("hit", 5, 95),
          ("death", 10, 120), ("taunt", 12, 100), ("slash", 9, 80), ("attack_side", 8, 80), ("attack_up", 8, 80), ("attack_down", 10, 85)]

# ---- What his blows do -------------------------------------------------------


def _muzzle(ctx) -> Point:
    """The tip of his nose, in the frame."""
    tip = turned((25.0, 0.0), ctx.turn)
    return (ctx.head[0] + tip[0], ctx.head[1] + tip[1])


def _claw_trail(ctx, a0: float, a1: float) -> List[Stamp]:
    """Three cuts in the air, from where his claws were to where they are.
    Nothing is ahead of the claws."""
    if abs(a1 - a0) < 12.0:
        return []
    back = 1.0 if a1 > a0 else -1.0
    reach = math.dist(ctx.shoulder, ctx.hand) + 12.0
    out: List[Stamp] = []
    for k, dr in enumerate((-6.0, 0.0, 6.0)):
        piece = R.swoosh(K, round(reach + dr), int(round(a0 + 6.0 * k * back)), int(round(a1)), 3.0, SLASH, SLASH_DARK)
        out.append((piece, ctx.shoulder, f"claw_trail_{k}", 0.0))
    return out


def _effects(ctx) -> List[Stamp]:
    out: List[Stamp] = []
    anim, u = ctx.anim, ctx.u
    if anim == "slash" and 0.25 <= u <= 0.75:
        now = math.degrees(math.atan2(ctx.hand[1] - ctx.shoulder[1], ctx.hand[0] - ctx.shoulder[0]))
        out.extend(_claw_trail(ctx, max(-150.0, now - 95.0), now))
    elif anim == "attack_up" and 0.3 <= u <= 0.7:
        now = math.degrees(math.atan2(ctx.hand[1] - ctx.shoulder[1], ctx.hand[0] - ctx.shoulder[0]))
        # Upward the angle gets less: the trail is from below the claw.
        out.extend(_claw_trail(ctx, now + 70.0, now))
    elif anim == "attack_side" and 0.5 <= u <= 0.8:
        out.append((R.burst(K, 13.0 if u < 0.7 else 9.0, SPARK, SPARK_DARK, 9), (_muzzle(ctx)[0] + 8.0, _muzzle(ctx)[1] + 4.0), "bite", 0.0))
    elif anim == "attack_down" and 0.5 <= u <= 0.88:
        late = u > 0.7
        at = ((ctx.hand[0] + ctx.far_hand[0]) / 2.0 + 6.0, ctx.ground - 12.0)
        out.append((R.burst(K, 11.0 if late else 15.0, DUST, DUST_DARK, 10), at, "ground_hit", 0.0))
        out.append((R.dust(K, 4.4 if late else 6.0, DUST, DUST_DARK), (at[0] + (24.0 if late else 16.0), ctx.ground - 5.0), "dust_ahead", 0.0))
        out.append((R.dust(K, 4.0 if late else 5.4, DUST, DUST_DARK), (at[0] - (22.0 if late else 14.0), ctx.ground - 4.0), "dust_behind", 0.0))
    elif anim in ("taunt", "death") and ctx.pose["mouth"] == "big" and (anim == "taunt" and 0.3 <= u <= 0.88 or anim == "death" and 0.2 <= u <= 0.35):
        # The howl: rings go out of his mouth, one more each frame.
        mouth = _muzzle(ctx)
        up = ctx.turn
        for k in range(1 + ctx.i % 3):
            r = 12.0 + 11.0 * k
            out.append((R.swoosh(K, r, int(up - 36), int(up + 36), 3.2, SPARK, SPARK_DARK), (mouth[0] - 4.0, mouth[1]), f"howl_{k}", 0.0))
    elif anim == "hit" and u <= 0.5:
        out.append((R.burst(K, 13.0, SPARK, SPARK_DARK, 9), (ctx.head[0] + 14.0, ctx.head[1] - 4.0), "struck", 0.0))
    return out


X.effects = _effects

ROWS = X.rows
FRAME_SIZE = X.frame
_render_frame = X.render_frame
render, main, render_canonical = R.entry_points(X, ACTOR_METADATA, DISPLAY_NAME)


def render_portraits(out_dir, **opts):
    """His portraits are frames of this sheet."""
    del opts
    return X.portraits(out_dir, {"default": ("idle", (1,), 0, False), "talking": ("taunt", (2, 4, 5, 6, 7, 8), 110, True)}, view_width=62.0)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}

if __name__ == "__main__":
    raise SystemExit(main())
