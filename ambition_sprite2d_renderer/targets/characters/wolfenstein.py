"""Sprite generator for Wolfenstein: the boss of Godwin Castle.

Jon (2026-10-15): "a boss character named Wolfenstein, that is a cross
between Frankenstein and a wolf. think Frankenstein with Insanity Wolf for a
head. this character is also a Nazi so he gets the armband."

The look: the body of Frankenstein's monster, seen three quarters from the
front and facing right. He is huge, about 240 cm: square heavy shoulders,
long arms, big grey-green hands with claws and stitches, bolts in his neck, a
black coat that is too short for him (its sleeves stop above his wrists),
dark trousers and heavy boots with thick soles. On his near (right) arm is the
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

from typing import Tuple

from ._ai_era_kit import OUTLINE, WHITE, RGBA, Kit, Point, ease, lerp, mix, turned
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
            "animation": "rake_a",
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
#: A physical blow's trail: a hot white core in red (electric ones are blue).
SLASH: RGBA = (255, 236, 232, 255)
SLASH_DARK: RGBA = (226, 70, 86, 255)
DUST: RGBA = (196, 186, 170, 255)
DUST_DARK: RGBA = (122, 112, 102, 255)

#: About 240 cm. ``height`` is the top of his skull as he stands, hunched
#: (measured from the idle row); his ears lie back a little over it. A huge
#: man (Jon, 2026-10-17: "think lurch from The Addams family, probably bigger
#: though"): a broad, deep trunk, round heavy shoulders, long thick arms,
#: heavy legs.
BUILD = Build(hip_up=64.0, thigh=32.0, shin=31.0, neck=(2.0, -54.0), upper=31.0, fore=29.0, near_shoulder=(-12.0, -49.0), far_shoulder=(13.0, -48.4),
              near_hip=(-7.0, 0.0), far_hip=(7.0, 0.0), ankle_up=5.0, head_up=(8.6, -36.0), throat=(-1.2, 15.0), height=165.0, half_width=(21.0, 24.0))

# The frame is as tall as it is wide, and the cell under his feet is empty:
# a boss placed by its data has the middle of its frame on the middle of its
# body box, so the middle of the box is the middle of the frame.
#
# He is published at the game's texel density (Jon, 2026-10-17: "make the
# final render of this boss slightly higher res"; "several characters are
# more blury than I want them to be"): his body box stands 100 units in the
# fight (his boss body; the hall's catalog row is 93), so the sheet's frame
# follows from it and is larger than his 320-pixel lengths.
X = Person(TARGET_NAME, BUILD, frame=(320, 320), ground=240.0, cx=150.0, world_height=100.0)
K = X.K
P = X.P
#: His head is a fifth larger than the body's lines would draw it: a kit of
#: its own paints it that much larger, so every line of it scales with it.
HEAD_SIZE = 1.2
KH = Kit((320, 320), K.reduce, out=K.out, zoom=HEAD_SIZE)
TOP = BUILD.neck[1] - 2.0


def stitches(d, pts, tick: float = 1.6, every: float = 2.6, width: float = 0.5, kit=None) -> None:
    """A sewn line through ``pts`` (frame points), crossed by short ticks."""
    kit = kit or K
    kit.line(d, pts, STITCH, width)
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        length = math.hypot(bx - ax, by - ay)
        if length < 1e-3:
            continue
        nx, ny = -(by - ay) / length, (bx - ax) / length
        for k in range(max(1, int(length / every))):
            t = (k + 0.5) * every / length
            x, y = ax + (bx - ax) * t, ay + (by - ay) * t
            kit.line(d, [(x - nx * tick, y - ny * tick), (x + nx * tick, y + ny * tick)], STITCH, width)


# ---- The coat ----------------------------------------------------------------


def _coat(d, hb: float, hf: float) -> None:
    """The front of his coat. It will not close over him: it is torn open
    to the waist over a chest and a belly sewn up the middle and across (Jon:
    "a full coat ... I'm okay with the coat being open or ripped to show chest
    and abs"). The shoulder seam has burst over his near shoulder. A strained
    button, a patch, the hem."""
    del hb
    # The burst seam of the near shoulder: his skin through the gap.
    K.poly(d, [K.at(-22.0, -50.0), K.at(-14.0, -57.0), K.at(-6.0, -58.0), K.at(-9.0, -54.0), K.at(-16.0, -51.6)], SKIN_SHADE)
    for k in range(5):
        x = lerp(-20.0, -8.0, k / 4.0)
        y = lerp(-51.0, -57.0, k / 4.0)
        K.line(d, [K.at(x, y - 1.2), K.at(x + 0.8, y + 1.6)], COAT_DARK, 0.8)
    # The torn opening: chest and belly.
    v = [K.at(-3.0, TOP + 1.0), K.at(14.0, TOP + 1.0), K.at(17.4, -34.0), K.at(14.0, -14.0), K.at(12.0, -4.0), K.at(2.0, -3.0),
         K.at(-0.6, -16.0), K.at(-2.0, -30.0)]
    K.poly(d, v, SKIN)
    # The far side of him in shade, a heavy pectoral line, and his belly in
    # six blocks.
    K.poly(d, [K.at(11.0, TOP + 1.0), K.at(14.0, TOP + 1.0), K.at(17.4, -34.0), K.at(14.0, -14.0), K.at(12.0, -4.0), K.at(9.6, -4.0), K.at(11.8, -16.0),
               K.at(12.6, -34.0)], SKIN_SHADE)
    K.line(d, [K.at(-1.4, -31.0), K.at(6.0, -27.4), K.at(14.4, -29.0)], SKIN_DEEP, 1.0)
    for y in (-21.0, -14.6, -8.4):
        K.line(d, [K.at(0.2, y), K.at(5.2, y + 0.6), K.at(11.6, y)], SKIN_DEEP, 0.7)
    K.line(d, [K.at(5.6, -26.0), K.at(5.4, -4.0)], SKIN_DEEP, 0.7)
    # Sewn across the chest, and once across the belly.
    stitches(d, [K.at(-0.6, -41.0), K.at(6.4, -39.4), K.at(14.0, -42.0)], tick=1.4, every=3.4, width=0.55)
    stitches(d, [K.at(2.0, -11.6), K.at(12.0, -13.0)], tick=1.2, every=3.4, width=0.5)
    # The torn lapels, pulled back over it.
    torn_l = [K.at(-3.0, TOP + 1.0), K.at(-2.0, -30.0), K.at(-0.6, -16.0), K.at(2.0, -3.0)]
    torn_r = [K.at(14.0, TOP + 1.0), K.at(17.4, -34.0), K.at(14.0, -14.0), K.at(12.0, -4.0)]
    K.line(d, torn_l, COAT_DARK, 1.4)
    K.line(d, torn_r, COAT_DARK, 1.4)
    for (ax, ay), (bx, by) in zip(torn_l, torn_l[1:]):
        for t in (0.3, 0.7):
            x, y = lerp(ax, bx, t), lerp(ay, by, t)
            K.line(d, [(x, y), (x + 3.0, y + 1.0)], COAT_DARK, 0.9)
    K.line(d, [K.at(-2.0, TOP + 3.0), K.at(-1.0, -30.0)], COAT_LIGHT, 0.6)
    # The one button left, straining across his belly.
    K.oval(d, K.at(7.0, -4.0), 2.0, 2.0, COAT_DARK, OUTLINE, 0.5)
    K.line(d, [K.at(2.4, -3.6), K.at(11.6, -3.6)], COAT_DARK, 0.9)
    # A patch, sewn on with big stitches.
    K.poly(d, [K.at(-15.0, -24.0), K.at(-6.0, -25.0), K.at(-5.4, -15.0), K.at(-14.4, -14.4)], (70, 64, 70, 255))
    stitches(d, [K.at(-15.0, -24.0), K.at(-6.0, -25.0), K.at(-5.4, -15.0), K.at(-14.4, -14.4), K.at(-15.0, -24.0)], tick=1.0, every=2.4, width=0.45)
    K.line(d, [K.at(-40.0, 12.0), K.at(40.0, 12.0)], COAT_DARK, 0.7)


# A huge trunk: broad and deep, the shoulders round and heavy.
X.torso = R.make_torso(K, ("wolfenstein", 3), COAT, COAT_DARK, back=(23.0, 23.0, 18.0, 18.6), front=(22.0, 23.4, 18.6, 19.0), hem_y=14.0, top=TOP,
                       shoulders=((-12.0, -47.0), (13.4, -46.4)), shoulder_r=(12.6, 11.4), neck=(-9.0, 9.0), shade_from=14.0, detail=_coat)
X.neck = R.make_neck(K, SKIN_SHADE, 19.0)

# ---- The limbs ---------------------------------------------------------------

# His sleeves are tight over huge arms and too short for them: they stop
# above his wrists, and a green forearm and a big hand come out of each.
X.upper_arm = lambda near: [(0.0, 1.0, 23.0, 19.0, COAT if near else COAT_DARK)]
X.forearm = lambda near: [(0.58, 1.0, 17.4, 14.4, SKIN if near else SKIN_SHADE), (0.0, 0.66, 21.0, 18.4, COAT if near else COAT_DARK)]
X.thigh = lambda near: [(0.0, 1.0, 19.0, 15.4, TROUSER if near else TROUSER_DARK)]
X.shin = lambda near: [(0.0, 1.0, 15.6, 12.6, TROUSER if near else TROUSER_DARK)]


def _arm_rips(ctx) -> List[Stamp]:
    """The coat gives way where his near arm is biggest: a rip over his
    elbow with his stitched skin in it, the ragged end of the sleeve, and a
    seam across his bare wrist."""
    if ctx.pose["arm"] == "under":
        return []
    out: List[Stamp] = []

    def turn(a: Point, b: Point) -> float:
        return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))

    def rip(d) -> None:
        # A long tear along the bicep, ragged at its edges.
        edge = [(-9.0, 0.0), (-5.0, -2.6), (-1.0, -1.8), (3.0, -3.4), (8.0, -1.4), (10.0, 0.4), (6.0, 2.4), (1.0, 1.8), (-4.0, 3.0)]
        K.poly(d, [K.at(x, y) for x, y in edge], SKIN_SHADE, OUTLINE, 0.6)
        K.line(d, [K.at(-7.0, 0.4), K.at(8.0, -0.4)], SKIN_DEEP, 0.6)

    def cuff(d) -> None:
        pts = [K.at(0.0 + (1.6 if k % 2 else 0.0), -10.4 + 3.5 * k) for k in range(7)]
        K.line(d, pts, COAT_DARK, 1.6)

    def wrist(d) -> None:
        stitches(d, [K.at(0.0, -7.6), K.at(0.8, 0.0), K.at(0.0, 7.6)], tick=1.2, every=2.2, width=0.5)

    sh, el, wr = ctx.shoulder, ctx.elbow, ctx.hand
    out.append((K.piece(("sleeve_rip", 2), rip), (lerp(sh[0], el[0], 0.74), lerp(sh[1], el[1], 0.74)), "sleeve_rip", turn(sh, el)))
    out.append((K.piece(("sleeve_cuff",), cuff), (lerp(el[0], wr[0], 0.66), lerp(el[1], wr[1], 0.66)), "sleeve_cuff", turn(el, wr)))
    out.append((K.piece(("wrist_seam",), wrist), (lerp(el[0], wr[0], 0.85), lerp(el[1], wr[1], 0.85)), "wrist_seam", turn(el, wr)))
    return out


X.layers["front"].append(_arm_rips)


# ---- The hands -----------------------------------------------------------------
#
# Jon: "give him big green hands", and "we can have different hand poses for
# different attacks". Each finger is two bones through a knuckle, with a claw
# on its end; the thumb is its own. A hand is drawn in hand units from its
# wrist along +x, the fingers curling toward +y.

#: His hands are this many times the size of a man's.
HAND = 1.55


def _h(x: float, y: float) -> Point:
    """A point of a hand, in hand units from its wrist, scaled to his size."""
    return K.at(x * HAND, y * HAND)


#: Where each finger starts on the palm (index first), how long its two bones
#: are, and how wide it is.
FINGERS = [((9.0, -4.6), 5.4, 4.4), ((9.8, -1.6), 6.0, 4.8), ((9.8, 1.6), 5.8, 4.6), ((9.0, 4.6), 4.8, 3.8)]
FINGER_W = 3.3
#: Each hand pose: the fingers' spread (degrees off +x), each finger's two
#: bends (toward the palm, degrees), the thumb's turn and bend, and whether
#: the claws are out.
HAND_POSES = {
    # Hanging, at rest: the fingers a little curled.
    "soft": ((-10.0, -3.0, 4.0, 11.0), ((22.0, 26.0),) * 4, (-50.0, 15.0), True),
    # Limp: his charge gone.
    "limp": ((-6.0, -2.0, 3.0, 8.0), ((34.0, 44.0),) * 4, (-38.0, 24.0), True),
    # The rake: every finger hooked, the claws out in front.
    "claw": ((-18.0, -6.0, 6.0, 17.0), ((26.0, 60.0), (28.0, 62.0), (28.0, 60.0), (26.0, 56.0)), (-66.0, 34.0), True),
    # The current in him: every finger stiff and spread, bent back.
    "splay": ((-40.0, -14.0, 12.0, 38.0), ((-12.0, -8.0),) * 4, (-84.0, -12.0), True),
    # Reaching: open, a little spread.
    "open": ((-20.0, -7.0, 7.0, 20.0), ((8.0, 12.0),) * 4, (-70.0, 0.0), True),
    # Flat on his knees.
    "flat": ((-5.0, -1.5, 1.5, 5.0), ((2.0, 4.0),) * 4, (-30.0, 0.0), False),
    # The hammer: a fist, the knuckles in front.
    "fist": ((-6.0, -2.0, 2.0, 6.0), ((94.0, 98.0),) * 4, (-24.0, 70.0), False),
    # The lash: the index finger out at you, the rest closed.
    "point": ((-3.0, -2.0, 4.0, 10.0), ((0.0, 0.0), (92.0, 96.0), (94.0, 96.0), (94.0, 96.0)), (-40.0, 40.0), True),
    # On his bolts: curled round them.
    "grip": ((-10.0, -3.0, 4.0, 11.0), ((58.0, 70.0),) * 4, (-36.0, 58.0), True),
}


def _finger(base: Point, l1: float, l2: float, a1: float, a2: float) -> Tuple[Point, Point, Point, float]:
    """A finger from ``base``: its knuckle, its tip, and the way its tip
    points."""
    k = (base[0] + l1 * math.cos(math.radians(a1)), base[1] + l1 * math.sin(math.radians(a1)))
    t = (k[0] + l2 * math.cos(math.radians(a2)), k[1] + l2 * math.sin(math.radians(a2)))
    return k, t, t, a2


def _hand(mode: str, near: bool):
    """A big hand along +x from its wrist at ``home``: a heavy palm, four
    fingers with knuckles and claws, a thumb, and a seam sewn across its
    back. ``near`` is his right hand; the far one is his left."""
    mode = mode if mode in HAND_POSES else "soft"
    # Facing canvas-right, his NEAR hand is his right hand and the far one his
    # left (Jon: "character-right is not canvas-right, in fact in this case it
    # is canvas-left"). The hand is drawn as a left hand; the near one is that
    # drawing mirrored across its own length, so its back is to the camera
    # and not its palm.
    m = -1.0 if near else 1.0

    def hp(x: float, y: float) -> Point:
        return _h(x, y * m)

    spread, bends, (thumb_a, thumb_b), claws_out = HAND_POSES[mode]
    skin = SKIN if near else SKIN_SHADE
    fingers = []
    for (base, l1, l2), sp, (b1, b2) in zip(FINGERS, spread, bends):
        a1 = sp + b1
        knuckle, tip, _, a2 = _finger(base, l1, l2, a1, a1 + b2)
        fingers.append((base, knuckle, tip, a2))
    thumb_base = (3.6, -5.4)
    tk, tt, _, ta = _finger(thumb_base, 4.6, 4.0, thumb_a, thumb_a + thumb_b)

    def claw(tip: Point, a: float, reach: float) -> List[Point]:
        ux, uy = math.cos(math.radians(a)), math.sin(math.radians(a))
        return [hp(tip[0] - uy * 1.3, tip[1] + ux * 1.3), hp(tip[0] + ux * reach, tip[1] + uy * reach), hp(tip[0] + uy * 1.3, tip[1] - ux * 1.3)]

    reach = 5.4 if mode == "claw" else 4.0
    claws = [claw(tip, a, reach) for _b, _k, tip, a in fingers if claws_out and (mode != "point" or _b == fingers[0][0])]
    if claws_out:
        claws.append(claw(tt, ta, 3.0))
    # Draw the far fingers first, so the near ones lie over them.
    order = list(reversed(fingers))

    def shape(d) -> None:
        K.rrect(d, K.home[0] - 2.4 * HAND, K.home[1] - 6.0 * HAND, K.home[0] + 10.0 * HAND, K.home[1] + 6.0 * HAND, 3.4 * HAND, WHITE)
        for base, knuckle, tip, _a in order:
            K.stroke(d, [hp(*base), hp(*knuckle), hp(*tip)], WHITE, FINGER_W * HAND)
        K.stroke(d, [hp(*thumb_base), hp(*tk), hp(*tt)], WHITE, (FINGER_W + 0.5) * HAND)
        for c in claws:
            K.poly(d, c, WHITE)

    def detail(d) -> None:
        # A line between each finger and the next: each one reads.
        for base, knuckle, tip, _a in order:
            K.stroke(d, [hp(*base), hp(*knuckle), hp(*tip)], SKIN_DEEP, FINGER_W * HAND)
            K.stroke(d, [hp(*base), hp(*knuckle), hp(*tip)], skin, (FINGER_W - 0.9) * HAND)
            K.oval(d, hp(*knuckle), 0.6 * HAND, 0.6 * HAND, SKIN_DEEP)
        K.stroke(d, [hp(*thumb_base), hp(*tk), hp(*tt)], SKIN_DEEP, (FINGER_W + 0.5) * HAND)
        K.stroke(d, [hp(*thumb_base), hp(*tk), hp(*tt)], skin, (FINGER_W - 0.4) * HAND)
        # The knuckles of the hand, and its back sewn on at the wrist.
        for base, *_ in fingers:
            K.oval(d, hp(base[0] - 0.6, base[1]), 0.9 * HAND, 0.8 * HAND, SKIN_DEEP if mode == "fist" else skin)
        stitches(d, [hp(2.0, -6.0), hp(3.0, 0.0), hp(2.2, 6.0)], tick=1.1, every=2.4, width=0.5)
        for c in claws:
            K.poly(d, c, CLAW)
            K.line(d, [c[1], ((c[0][0] + c[2][0]) / 2.0 * 0.4 + c[1][0] * 0.6, (c[0][1] + c[2][1]) / 2.0 * 0.4 + c[1][1] * 0.6)], CLAW_TIP, 0.6)

    return K.solid(("hand", mode, near, HAND, 2), shape, skin, detail, outline=1.3, rim=0.3, shade=0.35, shade_colour=SKIN_DEEP)


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
        return KH.at(*p)

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
        KH.poly(d, [at(p) for p in [HINGE] + UPPER_LIP[1:] + [jaw[1], jaw[0]]], WHITE)
        KH.poly(d, [at(p) for p in jaw], WHITE)
        for tooth in teeth:
            KH.poly(d, [at(p) for p in tooth], WHITE)

    def detail(d) -> None:
        KH.poly(d, [at(p) for p in [HINGE] + UPPER_LIP[1:] + [jaw[1], jaw[0]]], MOUTH)
        if open_ > 10.0:
            mid = ((UPPER_LIP[2][0] + jaw[1][0]) / 2.0 - 4.0, (UPPER_LIP[2][1] + jaw[1][1]) / 2.0 + 1.0)
            KH.oval(d, at(mid), 5.0, 1.8 + open_ * 0.05, TONGUE)
        KH.poly(d, [at(p) for p in jaw[2:]] + [at(jaw[0]), at(jaw[1])], FUR)
        KH.line(d, [at(jaw[0]), at(jaw[1])], GUM, 0.9)
        KH.poly(d, [at(jaw[5]), at(jaw[4]), at(jaw[3]), at((jaw[3][0] - 3.0, jaw[3][1] - 1.0)), at((jaw[5][0] + 2.0, jaw[5][1] - 1.0))], FUR_LIGHT)
        for tooth in teeth:
            KH.poly(d, [at(p) for p in tooth], TOOTH)

    return KH.solid(("jaw", round(open_, 1)), shape, FUR, detail, outline=1.3, rim=0.2, shade=0.3, shade_colour=FUR_DEEP)


def _skull():
    """His head: the skull, the ruff, the ears laid back, the muzzle with its
    upper teeth bared, the nose."""
    upper_teeth = []
    for x, tall in ((8.4, 2.0), (10.6, 2.2), (12.8, 2.0), (15.0, 2.2), (17.6, 4.4), (20.0, 2.6)):
        upper_teeth.append([(x - 1.0, 5.4), (x, 5.6 + tall), (x + 1.0, 5.4)])
    ruff = [(-9.0, -10.0), (-16.0, -9.0), (-13.4, -5.6), (-19.0, -2.4), (-14.6, 0.6), (-19.4, 4.6), (-13.6, 6.4), (-16.0, 11.4), (-9.4, 10.6),
            (-9.0, 15.6), (-4.0, 12.6), (-0.6, 16.4), (2.6, 12.8), (6.0, 14.6), (6.4, 9.0), (2.0, 4.0)]
    muzzle = [(3.0, -9.0), (10.0, -9.6), (17.0, -6.6), (22.6, -4.4), (25.4, -2.0), (25.2, 1.4), (22.6, 3.4), (21.4, 5.4), (7.0, 5.6), (3.0, 4.0)]

    def at(p: Point) -> Point:
        return KH.at(*p)

    def shape(d) -> None:
        KH.oval(d, KH.at(-1.6, -2.4), 12.0, 11.0, WHITE)
        KH.oval(d, KH.at(4.4, 2.0), 9.0, 7.6, WHITE)
        KH.poly(d, [at(p) for p in ruff], WHITE)
        KH.poly(d, [at(p) for p in muzzle], WHITE)
        for tooth in upper_teeth:
            KH.poly(d, [at(p) for p in tooth], WHITE)

    def detail(d) -> None:
        # The pale muzzle, cheeks and throat.
        KH.poly(d, [at((2.0, 0.0)), at((10.0, 1.4)), at((21.0, 3.0)), at((21.4, 6.0)), at((2.0, 7.0)), at((-2.0, 4.0))], FUR_LIGHT)
        KH.poly(d, [at((-6.0, 8.0)), at((4.0, 8.0)), at((6.0, 16.0)), at((-6.0, 16.0))], mix(FUR, FUR_LIGHT, 0.5))
        # The dark mask round his eyes, and the bridge of his nose.
        KH.oval(d, at(NEAR_EYE), 5.6, 5.0, FUR_DARK)
        KH.oval(d, at(FAR_EYE), 4.4, 4.2, FUR_DARK)
        KH.line(d, [at((9.0, -9.0)), at((16.6, -6.4)), at((22.0, -4.0))], FUR_LIGHT, 0.8)
        # The snarl: the skin of his muzzle is pulled up in folds.
        for x in (12.0, 14.6, 17.0):
            KH.line(d, [at((x - 1.0, -7.2)), at((x + 0.4, -5.2)), at((x - 0.4, -3.4))], FUR_DEEP, 0.6)
        # Fur on his skull and ruff.
        for a, b in (((-8.0, -6.0), (-12.0, -2.0)), ((-10.0, 2.0), (-14.0, 5.0)), ((-6.0, 6.0), (-10.0, 10.0)), ((-2.0, -11.0), (-6.0, -8.0)),
                     ((-1.0, 10.0), (-3.0, 14.0))):
            KH.line(d, [at(a), at(b)], FUR_DARK, 0.7)
        # His gums, his upper teeth, his nose.
        KH.line(d, [at(p) for p in UPPER_LIP], GUM, 1.0)
        for tooth in upper_teeth:
            KH.poly(d, [at(p) for p in tooth], TOOTH)
        KH.oval(d, KH.at(23.6, -1.4), 2.8, 2.4, NOSE)
        KH.oval(d, KH.at(22.8, -2.4), 0.9, 0.6, (120, 120, 130, 255))

    return KH.solid(("skull",), shape, FUR, detail, outline=1.3, rim=0.3, shade=0.35, shade_colour=FUR_DEEP)


#: His ears, laid back, from the middle of his head, and the root each turns
#: about.
NEAR_EAR = [(-5.0, -10.0), (-23.0, -12.6), (-16.0, -5.0), (-9.0, -3.0)]
NEAR_EAR_ROOT = (-7.0, -6.5)
NEAR_EAR_INNER = [(-7.0, -8.6), (-19.6, -11.6), (-14.4, -6.2), (-9.4, -4.8)]
FAR_EAR = [(0.0, -12.6), (-17.0, -17.4), (-11.0, -9.4), (-5.0, -8.0)]
FAR_EAR_ROOT = (-3.0, -10.0)


def _ear(near: bool, degrees: float):
    """An ear turned ``degrees`` about its root: up (perked) is positive, flat
    back is negative. The far ear is in shade; the near ear shows its
    inside."""
    degrees = round(degrees / 3.0) * 3.0
    root = NEAR_EAR_ROOT if near else FAR_EAR_ROOT

    def put(pts) -> List[Point]:
        out = []
        for x, y in pts:
            r = turned((x - root[0], y - root[1]), degrees)
            out.append(KH.at(root[0] + r[0], root[1] + r[1]))
        return out

    def shape(d) -> None:
        KH.poly(d, put(NEAR_EAR if near else FAR_EAR), WHITE)

    def detail(d) -> None:
        if near:
            KH.poly(d, put(NEAR_EAR_INNER), EAR_INNER)
            KH.line(d, put(NEAR_EAR[:3]), OUTLINE, 0.6)

    return KH.solid(("ear", near, degrees), shape, FUR if near else FUR_DARK, detail, outline=1.3, rim=0.3, shade=0.3, shade_colour=FUR_DEEP)


def _eyes(mode: str, look: Point = (0.0, 0.0)):
    """His eyes. Open, they are the eyes of the meme: white all round, small
    pupils that look at you, red veins."""

    def paint(d) -> None:
        for (ex, ey), rx, ry in ((NEAR_EYE, 4.6, 4.4), (FAR_EYE, 3.5, 3.7)):
            c = KH.at(ex, ey)
            if mode in ("closed", "dead"):
                r = rx * 0.7
                for s in (-1.0, 1.0):
                    KH.line(d, [(c[0] - r, c[1] - r * s), (c[0] + r, c[1] + r * s)], OUTLINE, 0.9)
                continue
            if mode == "wince":
                KH.line(d, [(c[0] - rx, c[1] - 1.8), (c[0] + rx * 0.5, c[1]), (c[0] - rx, c[1] + 1.8)], OUTLINE, 1.0)
                continue
            wide = 0.7 if mode == "pin" else 0.0
            KH.oval(d, c, rx + 0.6 + wide, ry + 0.6 + wide, OUTLINE)
            KH.oval(d, c, rx + wide, ry + wide, EYE_WHITE)
            for ang, length in ((200.0, 0.75), (330.0, 0.7), (110.0, 0.65), (20.0, 0.6)):
                a = math.radians(ang)
                KH.line(d, [(c[0] + math.cos(a) * rx * 0.95, c[1] + math.sin(a) * ry * 0.95),
                           (c[0] + math.cos(a) * rx * (0.95 - length * 0.5), c[1] + math.sin(a) * ry * (0.95 - length * 0.5) + 0.3)], VEIN, 0.55)
            if mode == "roll":
                # Rolled back: a sliver of iris under the top lid.
                KH.oval(d, (c[0], c[1] - ry * 0.95), rx * 0.3, rx * 0.16, IRIS)
                continue
            at_ = (c[0] - 0.4 * rx / 4.0 + look[0], c[1] + 0.2 + look[1])
            size = 0.15 if mode == "pin" else 0.26
            KH.oval(d, at_, rx * size, rx * size, IRIS)
            KH.oval(d, at_, rx * size * 0.58, rx * size * 0.58, OUTLINE)
            if mode == "squint":
                # The glare: the top lid down over half the eye.
                KH.poly(d, [(c[0] - rx - 1.0, c[1] - ry - 1.0), (c[0] + rx + 1.0, c[1] - ry - 1.0), (c[0] + rx + 1.0, c[1] - ry * 0.1),
                           (c[0] - rx - 1.0, c[1] + ry * 0.15)], FUR_DARK)
                KH.line(d, [(c[0] - rx - 0.6, c[1] + ry * 0.15), (c[0] + rx + 0.6, c[1] - ry * 0.1)], OUTLINE, 0.8)

    return KH.piece(("eyes", mode, round(look[0], 1), round(look[1], 1)), paint)


def _brows(mood: int):
    """Heavy dark fur over his eyes, the inner ends down."""
    lift = -1.4 if mood > 0 else 0.0

    def paint(d) -> None:
        KH.stroke(d, [KH.at(-0.4, -10.2 + lift), KH.at(4.0, -10.4 + lift), KH.at(8.6, -8.0 + lift + (0.0 if mood > 0 else 1.0))], FUR_DEEP, 2.0)
        KH.stroke(d, [KH.at(10.4, -9.6 + lift + (0.0 if mood > 0 else 1.2)), KH.at(13.6, -10.6 + lift), KH.at(16.0, -9.6 + lift)], FUR_DEEP, 1.7)

    return KH.piece(("brows", mood), paint)


def _seam():
    """The seam round his neck, where the fur stops and his own skin starts.
    From the middle of his head."""

    def paint(d) -> None:
        stitches(d, [KH.at(-8.0, 15.2), KH.at(-3.0, 16.6), KH.at(2.0, 16.0), KH.at(6.4, 14.4)], tick=1.4, every=2.2, width=0.55, kit=KH)

    return KH.piece(("seam",), paint)


#: The bolts in his neck are big: they are where his charge goes in and
#: comes out (Jon: lightning "that plays with the nodes in the neck").
BOLT_SIZE = 2.1


def _bolts(charge: int = 0):
    """The bolts through his neck, from a point on the line of his neck: +x
    is across his neck to its front, +y down it. The near bolt is a big nut
    on the side of his neck with its rod out behind; the far one comes out of
    the front of it. ``charge`` (0 to 2): how hot their ends glow."""
    S = BOLT_SIZE

    def at(x: float, y: float) -> Point:
        return K.at(x * S, y * S)

    hot = [BOLT, (190, 220, 255, 255), ARC_CORE][max(0, min(2, charge))]

    def paint(d) -> None:
        K.rrect(d, at(-8.4, 0.0)[0], at(0.0, -1.2)[1], at(-1.0, 0.0)[0], at(0.0, 1.2)[1], 0.4 * S, BOLT_DARK, OUTLINE, 0.6)
        K.rrect(d, at(-9.6, 0.0)[0], at(0.0, -1.9)[1], at(-7.6, 0.0)[0], at(0.0, 1.9)[1], 0.3 * S, hot, OUTLINE, 0.6)
        hexagon = [at(-1.4 + 2.8 * math.cos(math.tau * k / 6.0 + 0.5), 2.8 * math.sin(math.tau * k / 6.0 + 0.5)) for k in range(6)]
        K.poly(d, hexagon, BOLT, OUTLINE, 0.6)
        K.oval(d, at(-1.4, 0.0), 1.0 * S, 1.0 * S, BOLT_DARK)
        K.rrect(d, at(5.0, 0.0)[0], at(0.0, -1.2)[1], at(10.4, 0.0)[0], at(0.0, 1.2)[1], 0.4 * S, BOLT, OUTLINE, 0.6)
        K.rrect(d, at(10.0, 0.0)[0], at(0.0, -2.0)[1], at(11.8, 0.0)[0], at(0.0, 2.0)[1], 0.3 * S, hot, OUTLINE, 0.6)

    return K.piece(("bolts", S, charge), paint)


def _neck_bolts(ctx) -> List[Stamp]:
    """The bolts, on the part of his neck that shows."""
    top = turned(BUILD.throat, ctx.turn)
    top = (ctx.head[0] + top[0], ctx.head[1] + top[1])
    at = (lerp(ctx.neck[0], top[0], 0.55), lerp(ctx.neck[1], top[1], 0.55))
    charge = int(ctx.pose["charge"])  # type: ignore[arg-type]
    return [(_bolts(charge), at, "bolts", math.degrees(math.atan2(top[1] - ctx.neck[1], top[0] - ctx.neck[0])) + 90.0)]


X.layers["over_torso"].append(_neck_bolts)


def _open(mouth: str) -> float:
    return {"gape": 48.0, "big": 34.0, "open": 18.0, "o": 12.0, "grit": 1.0}.get(mouth, 5.0)


def _head_layers(pose):
    ears = float(pose["ears"])  # type: ignore[arg-type]
    look = pose["look"]
    # The far ear lags its pair a little: two ears are not one.
    return [(_ear(False, ears * 0.85), "far_ear"), (_jaw(_open(str(pose["mouth"]))), "jaw"), (_skull(), "skull"), (_ear(True, ears), "near_ear"),
            (_eyes(str(pose["eyes"]), look), "eyes"),  # type: ignore[arg-type]
            (_brows(R.brow_mood(pose)), "brows"), (_seam(), "seam")]


X.head_layers = _head_layers


def _armband(ctx) -> List[Stamp]:
    """The regime's band and its mark, on his near arm, over the sleeve."""
    if ctx.pose["arm"] == "under":
        return []
    t = 0.36
    at = (lerp(ctx.shoulder[0], ctx.elbow[0], t), lerp(ctx.shoulder[1], ctx.elbow[1], t))
    turn = math.degrees(math.atan2(ctx.elbow[1] - ctx.shoulder[1], ctx.elbow[0] - ctx.shoulder[0]))
    # Round his bare bicep now, as wide as it is (Jon: "he needs to have the
    # armband though").
    return [(F.band(K, 24.0, 11.0), at, "armband", turn), (F.emblem(K, 5.2), at, "armband_emblem", 0.0)]


X.layers["front"].append(_armband)

# ---- How he moves ------------------------------------------------------------
#
# Jon (2026-10-17): "far too stiff and not expressive. We need more
# articulation, more custom animation, more visual interest." So every move
# is acted, in phases that the fight draws one by one (`<move>_tell`, the
# strike, a hold or a recovery): a gather before it, a snap into it, a frame
# held at the contact, a follow-through past it and a settle. His body
# squashes into a blow and stretches out of a spring (``sq``); his head, his
# hands, his ears and his coat arrive after the body that moves them
# (``drag``). His face acts too: his ears go flat before he strikes, his
# pupils go to pinpoints, and the jaw opens with the effort.
#
# He is a biped the whole fight (Jon, 2026-10-17).

# Hunched, his head forward, his long arms hanging in front of him; his ears
# laid back. ``ears``: up (perked) positive, flat negative. ``look``: where
# his pupils are, in head pixels.
X.set_rest(lean=9.0, head=(1.0, 1.0, 4.0), na=(7.0, 30.0), fa=(9.0, 29.5), nh="soft", fh="soft", nf=(-6.0, 0.0, 0.0), ff=(7.0, 0.0, 0.0),
           mouth="flat", brows=-1.0, ears=0.0, look=(0.0, 0.0), charge=0.0)

# His hands swing in arcs round his shoulders.
X.polar = ("na", "fa")

#: What follows the body: the head a little late, the hands later, the ears
#: and the coat latest.
DRAG = {"head": 0.05, "na": 0.05, "fa": 0.07, "ears": 0.1, "hem": 0.12}
#: Slower for a big, heavy move.
HEAVY = {"head": 0.07, "na": 0.07, "fa": 0.09, "ears": 0.14, "hem": 0.16}


def jitter(i: int, amp: float, seed: float = 0.0) -> float:
    """A shake that does not repeat its pattern frame to frame: a body
    trembling with effort, or with current."""
    return amp * math.sin(i * 12.9898 + seed * 78.233) * math.cos(i * 4.1414 + seed)


def keyed(i: int, n: int, frames, drag=DRAG, loop_: bool = False):
    u = R.cycle(i, n) if loop_ else shot(i, n)
    return X.keys(u, frames, drag=drag, wrap=loop_)


# ---- Standing, walking -------------------------------------------------------

#: Breath out: low, heavy. Breath in: the chest and shoulders heave up.
EXHALE = P(hip=(0.0, 3.0), lean=13.0, sq=0.965, shrug=(0.6, 2.0), head=(1.6, 2.0, 8.0), na=(9.0, 30.0), fa=(11.0, 29.5), mouth="flat", ears=-2.0)
INHALE = P(hip=(0.0, -0.4), lean=5.0, sq=1.05, shrug=(-1.0, -4.0), head=(0.6, -0.6, -6.0), na=(5.0, 28.0), fa=(7.0, 27.5), mouth="open", ears=8.0)
#: The tic: a jerk of the head over and down, his eyes gone to pins, his
#: claws out, a jolt through his shoulders.
TIC = P(hip=(1.0, 2.0), lean=12.0, sq=0.99, shrug=(1.0, -2.0), head=(3.6, 1.6, 28.0), eyes="pin", mouth="grit", ears=-20.0, nh="claw", fh="claw",
        look=(0.8, 0.4), na=(12.0, 26.0), fa=(14.0, 27.0), charge=1.0)


@X.row
def idle(i: int, n: int):
    # He heaves for breath; half way through, a tic snaps his head over and
    # his claws out, and he shakes it off.
    return keyed(i, n, [(0.0, EXHALE), (0.12, dict(EXHALE, ears=10.0), "snap"), (0.3, INHALE, "out"), (0.52, EXHALE, "io"), (0.58, TIC, "snap"),
                        (0.68, TIC, "hold"), (0.8, dict(EXHALE, head=(1.0, 1.0, -6.0), ears=6.0, eyes="open"), "back"), (1.0, EXHALE)], loop_=True)


@X.row
def walk(i: int, n: int):
    # The monster's lurch: a stiff-kneed step that lands hard (the hips drop
    # and the trunk squashes on each heel), the whole of him rocking over the
    # planted foot, the arms out in front and bobbing after the body.
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 9.0, 4.0)
    land = max(0.0, math.cos(2.0 * ph))
    rock = math.sin(ph)
    pose = P(hip=(0.6 + 1.6 * rock, 4.2 * land - 1.0), lean=7.0 + 5.0 * land, sq=1.0 - 0.05 * land + 0.02 * (1.0 - land), rot=4.0 * rock,
             head=(1.4, 0.8 * land, 2.0 - 4.0 * land), na=(30.0, -2.0 + 2.6 * land), fa=(30.0, 0.5 + 2.6 * land), nh="claw", fh="claw",
             nf=nf, ff=ff, hem=(1.0 + 2.0 * land, 0.5 + 1.5 * land), shrug=(0.0, 1.2 * land), mouth="open" if land > 0.7 else "flat",
             ears=-3.0 * land)
    # The head and the arms lag: read them from a little earlier in the step.
    ph2 = ph - 0.5
    land2 = max(0.0, math.cos(2.0 * ph2))
    return dict(pose, head=(1.4, 0.8 * land2, 2.0 - 4.0 * land2), na=(30.0, -2.0 + 2.6 * land2), fa=(30.0, 0.5 + 2.6 * land2))


def planted(pose, near_up: float = 0.0, far_up: float = 0.0):
    """``pose`` with each hand's reach set so its wrist is this far (units)
    over the floor, as the rig solves the arm: a hand on the floor is ON it,
    whatever the trunk does."""
    pose = X.full(pose)
    for near, up in ((True, near_up), (False, far_up)):
        key = "na" if near else "fa"
        want = X.ground - (6.0 + up) * X.U
        lo, hi = -10.0, 40.0
        for _ in range(24):
            mid = (lo + hi) / 2.0
            wrist = X.arm_joints(dict(pose, **{key: (pose[key][0], mid)}), near)[2]
            if wrist[1] < want:
                lo = mid
            else:
                hi = mid
        pose = dict(pose, **{key: (pose[key][0], (lo + hi) / 2.0)})
    return pose


#: On all fours (Jon, 2026-10-17: "some of these all 4s concepts are good"):
#: the trunk long and low, both hands down on the floor ahead of him, the
#: head low and forward, the ears flat. The stalk before the pounce.
FOURS = P(hip=(2.0, 16.0), lean=66.0, sq=0.96, shrug=(2.0, 1.0), head=(5.0, 3.0, -22.0), na=(12.0, 34.0), fa=(18.0, 33.0), nh="claw", fh="claw",
          nf=(-10.0, 0.0, 0.0), ff=(6.0, 0.0, 0.0), mouth="big", eyes="pin", ears=-28.0, brows=-1.0, hem=(3.0, 0.0), look=(1.0, 0.4))


@X.row
def prowl(i: int, n: int):
    # Unleashed, he stalks on all fours: the hands and the feet step in turn,
    # the shoulders roll over each planted hand, and he pants.
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 10.0, 5.0)
    hand = lambda p: (math.cos(p), max(0.0, -math.sin(p)))
    (nc, nl), (fc, fl) = hand(ph + math.pi * 0.5), hand(ph + math.pi * 1.5)
    land = max(0.0, math.cos(2.0 * ph))
    pose = dict(FOURS, hip=(2.0, 16.0 + 1.6 * land), lean=66.0 + 3.0 * s, rot=1.4 * s, shrug=(2.0 + 1.0 * s, 1.0 - 1.4 * land),
                head=(5.0, 3.0 + land, -22.0 + 3.0 * c), na=(12.0 + 7.0 * nc, 30.0), fa=(18.0 + 7.0 * fc, 30.0), nf=nf, ff=ff,
                mouth="big" if i % 2 == 0 else "open", ears=-28.0 + 4.0 * land)
    return planted(pose, 6.0 * nl, 6.0 * fl)


@X.row
def run(i: int, n: int):
    # A lope: low and long, the wolf in him; the arms swing low.
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 15.0, 11.0, 0.0)
    return P(hip=(3.0, 3.0 + 2.2 * math.cos(2.0 * ph)), lean=30.0, head=(3.0, 2.0, -18.0), na=(4.0 - 14.0 * c, 24.0 + 3.0 * s), fa=(6.0 + 14.0 * c, 24.0 - 3.0 * s),
             nh="claw", fh="claw", nf=nf, ff=ff, mouth="open", hem=(3.0, 1.0), ears=-16.0, eyes="pin", sq=1.0 - 0.03 * math.cos(2.0 * ph))


RISE = P(hip=(0.0, -2.0), lean=6.0, head=(1.0, 0.0, -8.0), na=(-12.0, -16.0), nab=-1.0, fa=(21.0, -6.0), nh="splay", fh="splay", nf=(-4.0, -12.0, 26.0),
         ff=(7.0, -16.0, 10.0), mouth="big", hem=(2.0, 3.0), sq=1.06, ears=-10.0)
APEX = P(hip=(0.0, -2.0), lean=4.0, head=(1.0, 0.0, -2.0), na=(-16.0, -8.0), nab=-1.0, fa=(22.0, 0.0), nh="open", fh="open", nf=(-4.0, -9.0, 20.0),
         ff=(8.0, -12.0, 6.0), mouth="open", hem=(3.0, 3.0), ears=6.0)
FALL = P(hip=(0.0, -3.0), lean=-2.0, head=(0.0, 0.0, 6.0), na=(-22.0, -4.0), nab=-1.0, fa=(23.0, -3.0), nh="splay", fh="splay", nf=(-7.0, -4.0, 22.0),
         ff=(7.0, -8.0, 8.0), mouth="big", hem=(3.0, 5.0), ears=10.0, sq=1.03)
CROUCHED = P(hip=(-1.0, 14.0), lean=24.0, head=(2.0, 2.0, -6.0), na=(-8.0, 26.0), fa=(-4.0, 27.0), nf=(-7.0, 0.0, 0.0), ff=(8.0, 0.0, 0.0), sq=0.92,
             ears=-12.0, mouth="grit")


@X.row
def jump(i: int, n: int):
    return keyed(i, n, [(0.0, CROUCHED), (0.25, CROUCHED, "hold"), (0.5, RISE, "snap"), (1.0, APEX, "out")])


@X.row
def fall(i: int, n: int):
    _, s, c = loop(i, n)
    return dict(FALL, na=(-22.0 + 2.0 * s, -4.0 - 3.0 * c), fa=(23.0 - 2.0 * s, -3.0 + 3.0 * c), nf=(-7.0, -4.0 + 1.5 * s, 22.0), ff=(7.0, -8.0 - 1.5 * s, 8.0),
                ears=10.0 + 4.0 * s)


#: Down on his heels, a fist on the floor.
LANDED = P(hip=(0.0, 18.0), lean=32.0, head=(3.0, 3.0, -6.0), na=(16.0, 26.0), fa=(19.0, 22.0), nh="fist", fh="claw", nf=(-9.0, 0.0, 0.0), ff=(9.0, 0.0, 0.0),
           mouth="big", hem=(3.0, 3.0), sq=0.88, ears=-16.0)


@X.row
def land_hard(i: int, n: int):
    return keyed(i, n, [(0.0, FALL), (0.18, LANDED, "snap"), (0.55, dict(LANDED, sq=0.94), "out"), (1.0, X.full(P()), "back")], drag=HEAVY)


# ---- The rake: the claws across, a step on each blow -------------------------

#: Ready to rake: the near claw cocked high behind his head, the far one up in
#: guard, his weight back, his ears flat and his pupils to pins.
RAKE_COCK = P(hip=(-3.0, 3.0), lean=-6.0, sq=1.04, shrug=(-1.0, -2.0), head=(0.0, 0.0, -6.0), na=(-12.0, -22.0), nab=-1.0, arm="under",
              fa=(16.0, 6.0), nh="claw", fh="claw", nf=(-9.0, 0.0, 0.0), ff=(8.0, 0.0, 10.0), mouth="big", eyes="pin", ears=-22.0, brows=-1.0,
              hem=(1.0, 2.0), look=(0.8, 0.0))
#: Through: the near claw down across in front of him and low, the trunk
#: thrown after it, the front foot a stride on.
RAKE_THROUGH = P(hip=(8.0, 6.0), lean=28.0, sq=0.94, shrug=(1.0, 1.0), head=(3.0, 2.0, -12.0), na=(30.0, 16.0), fa=(-6.0, 20.0), nh="claw", fh="claw",
                 nf=(-12.0, 0.0, 0.0), ff=(15.0, 0.0, -6.0), mouth="gape", eyes="pin", ears=-24.0, hem=(3.0, 1.0))
#: Past it: the claw on down and behind, the shoulders turned with it.
RAKE_PAST = P(hip=(9.0, 7.0), lean=32.0, sq=0.96, head=(3.0, 2.0, -6.0), na=(10.0, 30.0), fa=(4.0, 18.0), nh="claw", fh="claw",
              nf=(-12.0, 0.0, 0.0), ff=(15.0, 0.0, 0.0), mouth="big", eyes="pin", ears=-20.0, hem=(3.0, 2.0))
#: The far claw cocked low, for the backhand up.
BACK_COCK = P(hip=(8.0, 7.0), lean=30.0, sq=0.96, head=(3.0, 2.0, -4.0), na=(4.0, 26.0), fa=(-8.0, 26.0), fab=1.0, nh="claw", fh="claw",
              nf=(-12.0, 0.0, 0.0), ff=(15.0, 0.0, 0.0), mouth="grit", eyes="pin", ears=-22.0, hem=(3.0, 2.0))
#: The backhand: the far claw up across in front of his face.
BACK_THROUGH = P(hip=(11.0, 2.0), lean=4.0, sq=1.05, shrug=(0.0, -2.0), head=(2.0, 0.0, -14.0), na=(2.0, 24.0), fa=(26.0, -14.0), fab=-1.0, nh="claw",
                 fh="claw", nf=(-6.0, 0.0, 0.0), ff=(17.0, 0.0, 0.0), mouth="gape", eyes="pin", ears=-24.0, hem=(3.0, 4.0))
#: The high blow, up: both claws over his head, stretched tall.
HIGH_UP = P(hip=(10.0, -3.0), lean=-14.0, sq=1.08, shrug=(0.0, -3.0), head=(3.0, 0.0, -6.0), na=(-9.0, -33.0), nab=-1.0, fa=(-5.0, -34.0), fab=-1.0,
            arm="under", nh="claw", fh="claw", nf=(-8.0, 0.0, 10.0), ff=(16.0, 0.0, 12.0), mouth="gape", eyes="pin", ears=-26.0, hem=(2.0, 3.0))
#: And down: both claws in front of him at your height, all his weight on
#: them.
HIGH_DOWN = P(hip=(16.0, 10.0), lean=40.0, sq=0.9, shrug=(1.0, 2.0), head=(4.0, 3.0, -4.0), na=(28.0, 14.0), fa=(26.0, 18.0), nh="claw", fh="claw",
              nf=(-8.0, 0.0, 0.0), ff=(22.0, 0.0, -8.0), mouth="big", eyes="pin", ears=-20.0, hem=(3.0, 0.0))


@X.row
def rake_tell(i: int, n: int):
    # The coil: back on his heels and up, the claw cocked. Then he holds it,
    # trembling, and the whole fight reads the hold.
    pose = keyed(i, n, [(0.0, X.full(P())), (0.55, RAKE_COCK, "out"), (1.0, RAKE_COCK)])
    if i >= n // 2:
        pose = dict(pose, na=(pose["na"][0] + jitter(i, 0.8), pose["na"][1] + jitter(i, 0.8, 1.0)), head=(pose["head"][0], pose["head"][1], pose["head"][2] + jitter(i, 2.0, 2.0)))
    return pose


@X.row
def rake_a(i: int, n: int):
    # Blow one: the near claw comes over and down across you, snaps through,
    # follows on past, and is caught low with the far claw cocked.
    return keyed(i, n, [(0.0, RAKE_COCK), (0.3, RAKE_THROUGH, "snap"), (0.55, RAKE_PAST, "out"), (1.0, BACK_COCK, "io")])


@X.row
def rake_b(i: int, n: int):
    # Blow two: the backhand, the far claw up across his face and yours.
    return keyed(i, n, [(0.0, BACK_COCK), (0.3, BACK_THROUGH, "snap"), (0.6, dict(BACK_THROUGH, fa=(20.0, -20.0), lean=0.0), "out"),
                        (1.0, dict(RAKE_COCK, hip=(11.0, 3.0), lean=-2.0), "io")])


@X.row
def rake_c(i: int, n: int):
    # Blow three (unleashed): up tall with both claws over his head, a held
    # frame at the top, and down on you with all his weight.
    return keyed(i, n, [(0.0, dict(RAKE_COCK, hip=(11.0, 3.0))), (0.3, HIGH_UP, "out"), (0.42, HIGH_UP, "hold"), (0.58, HIGH_DOWN, "snap"),
                        (1.0, dict(HIGH_DOWN, sq=0.94, head=(4.0, 3.0, 2.0)), "out")], drag=HEAVY)


@X.row
def rake_recover(i: int, n: int):
    # He comes up out of it, shakes his head, and is himself again.
    shaken = dict(X.full(P()), head=(1.0, 1.0, -10.0), ears=6.0, mouth="open")
    return keyed(i, n, [(0.0, RAKE_PAST), (0.5, dict(X.full(P()), sq=1.02), "out"), (0.75, shaken, "back"), (1.0, X.full(P()))])


# ---- The hammer: both fists into the floor -----------------------------------

#: Up on his toes, both fists clasped high over his head, his back arched.
HAMMER_UP = P(hip=(-1.0, -4.0), lean=-16.0, sq=1.09, shrug=(0.0, -3.0), head=(2.0, 0.0, -4.0), na=(-9.0, -34.0), nab=-1.0, fa=(-6.0, -35.0), fab=-1.0,
              arm="under", nh="fist", fh="fist", nf=(-8.0, -3.0, 22.0), ff=(9.0, -3.0, 22.0), mouth="grit", eyes="pin", ears=-18.0, hem=(1.0, 3.0))
#: Down: his fists in the floor in front of him, all of him on them, squashed.
HAMMER_DOWN = P(hip=(5.0, 18.0), lean=44.0, sq=0.86, shrug=(2.0, 3.0), head=(4.0, 4.0, -14.0), na=(25.0, 27.0), fa=(23.0, 29.0), nh="fist", fh="fist",
                nf=(-12.0, 0.0, 0.0), ff=(12.0, 0.0, 0.0), mouth="gape", eyes="wince", ears=-24.0, hem=(3.0, 5.0))


# His fists ON the floor, whatever the trunk does.
HAMMER_DOWN = planted(HAMMER_DOWN, 1.0, 0.0)


@X.row
def hammer_tell(i: int, n: int):
    # He rises: up on his toes, the fists up and together, higher, and the
    # held top shakes.
    pose = keyed(i, n, [(0.0, X.full(P())), (0.2, dict(CROUCHED, sq=0.94, na=(12.0, 20.0), fa=(14.0, 20.0), nh="fist", fh="fist"), "out"),
                        (0.65, HAMMER_UP, "out"), (1.0, HAMMER_UP)], drag=HEAVY)
    if i >= n * 2 // 3:
        pose = dict(pose, hip=(pose["hip"][0] + jitter(i, 0.6), pose["hip"][1]), na=(pose["na"][0] + jitter(i, 0.7, 3.0), pose["na"][1]))
    return pose


@X.row
def hammer_slam(i: int, n: int):
    # Down in one frame, a held contact, and the floor gives him a bounce.
    return keyed(i, n, [(0.0, HAMMER_UP), (0.2, HAMMER_DOWN, "snap"), (0.5, HAMMER_DOWN, "hold"),
                        (0.75, dict(HAMMER_DOWN, sq=0.92, hip=(5.0, 16.0)), "out"), (1.0, HAMMER_DOWN, "io")], drag=HEAVY)


@X.row
def hammer_stuck(i: int, n: int):
    # His fists are stuck in the floor: he tugs, one shoulder and then the
    # other, and snarls at it.
    ph, s, c = loop(i, n)
    return dict(HAMMER_DOWN, hip=(5.0 - 1.4 * s, 18.0 - 1.8 * abs(s)), lean=44.0 - 4.0 * abs(s), sq=0.88 + 0.03 * abs(s), shrug=(2.0, 3.0 - 2.4 * abs(s)),
                head=(4.0 - s, 4.0, -14.0 + 6.0 * s), na=(HAMMER_DOWN["na"][0], HAMMER_DOWN["na"][1] - 1.2 * abs(s)),
                fa=(HAMMER_DOWN["fa"][0], HAMMER_DOWN["fa"][1] - 1.2 * abs(s)), mouth="grit" if s > 0 else "big",
                eyes="wince" if s > 0 else "pin", ears=-24.0 + 6.0 * c)


@X.row
def hammer_pull(i: int, n: int):
    # He tears them out, rocks back and catches himself.
    torn = P(hip=(-4.0, 2.0), lean=-12.0, sq=1.05, head=(-1.0, -1.0, -16.0), na=(-6.0, 4.0), fa=(-2.0, 8.0), nh="claw", fh="claw",
             nf=(-14.0, 0.0, -6.0), ff=(6.0, 0.0, 10.0), mouth="big", eyes="open", ears=8.0, hem=(1.0, 6.0))
    return keyed(i, n, [(0.0, HAMMER_DOWN), (0.3, torn, "snap"), (0.65, dict(torn, lean=-4.0, sq=1.0), "out"), (1.0, X.full(P()), "back")])


# ---- The lunge and the bound ---------------------------------------------------

#: Down low and coiled, the arms back, the head low and forward, the ears
#: flat to his skull: a dog about to go.
LUNGE_COIL = P(hip=(-4.0, 16.0), lean=36.0, sq=0.9, shrug=(2.0, 2.0), head=(4.0, 3.0, 2.0), na=(-14.0, 22.0), fa=(-10.0, 21.0), nh="claw", fh="claw",
               nf=(-14.0, 0.0, 0.0), ff=(9.0, 0.0, 0.0), mouth="grit", eyes="pin", ears=-30.0, brows=-1.0, hem=(3.0, 0.0), look=(1.0, 0.0))
#: Flying: stretched out long behind his jaws, the claws reaching, the legs
#: trailing.
LUNGE_FLY = P(hip=(8.0, -2.0), lean=62.0, sq=1.08, shrug=(2.0, -1.0), head=(6.0, 1.0, -26.0), na=(30.0, -8.0), nab=-1.0, fa=(28.0, -2.0), fab=-1.0,
              nh="open", fh="open", nf=(-20.0, -12.0, 40.0), ff=(-10.0, -16.0, 30.0), mouth="gape", eyes="pin", ears=-34.0, hem=(3.0, 0.0), off=(0.0, -4.0))
#: The skid: heels dug in, leaning back against it, the arms thrown back.
SKID = P(hip=(-6.0, 10.0), lean=-18.0, sq=0.95, head=(-1.0, 1.0, -10.0), na=(-16.0, 6.0), nab=-1.0, fa=(-12.0, 2.0), fab=-1.0, nh="splay", fh="splay",
         nf=(-6.0, 0.0, -10.0), ff=(18.0, 0.0, -24.0), mouth="big", eyes="open", ears=10.0, hem=(0.0, 8.0))


#: The pounce gathered: down on all fours, the haunches high and the head
#: low, every claw in the floor.
POUNCE_COIL = dict(FOURS, hip=(-4.0, 10.0), lean=58.0, sq=0.9, head=(5.0, 4.0, -12.0), na=(16.0, 32.0), fa=(22.0, 31.0), nf=(-14.0, 0.0, 0.0),
                   ff=(2.0, 0.0, 0.0), mouth="grit", ears=-34.0)


@X.row
def lunge_tell(i: int, n: int):
    # He drops onto his hands, coils on all fours, and shivers on the spot
    # like a dog that has seen you.
    pose = keyed(i, n, [(0.0, X.full(P())), (0.3, dict(CROUCHED, na=(14.0, 28.0), fa=(18.0, 27.0)), "out"), (0.55, planted(POUNCE_COIL), "out"),
                        (1.0, planted(POUNCE_COIL))])
    if i >= n // 2:
        pose = dict(pose, hip=(pose["hip"][0] + jitter(i, 0.9), pose["hip"][1] + jitter(i, 0.5, 4.0)), ears=pose["ears"] + jitter(i, 4.0, 1.0))
    return pose


@X.row
def lunge(i: int, n: int):
    # In the air: long, the jaws snapping, the claws working.
    _, s, c = loop(i, n)
    return dict(LUNGE_FLY, na=(30.0 + 2.0 * s, -8.0 + 4.0 * c), fa=(28.0 - 2.0 * s, -2.0 - 4.0 * c), mouth="gape" if i % 3 != 2 else "grit",
                nf=(-20.0 + 2.0 * c, -12.0, 40.0), ff=(-10.0 - 2.0 * c, -16.0, 30.0))


@X.row
def lunge_skid(i: int, n: int):
    # He lands running and digs in: the heels plough, he leans back with his
    # arms flung behind him, and he stops.
    return keyed(i, n, [(0.0, dict(LUNGE_FLY, off=(0.0, 0.0))), (0.2, SKID, "snap"), (0.6, dict(SKID, lean=-10.0, hip=(-4.0, 8.0)), "out"),
                        (1.0, dict(CROUCHED, lean=14.0), "io")])


#: On the wall: crouched against it, turned to come back, gathered.
ON_WALL = P(hip=(-6.0, 6.0), lean=20.0, rot=-24.0, sq=0.9, head=(2.0, 2.0, 6.0), na=(14.0, 18.0), fa=(10.0, 22.0), nh="claw", fh="claw",
            nf=(-14.0, -10.0, 60.0), ff=(-8.0, -18.0, 50.0), mouth="grit", eyes="pin", ears=-28.0, hem=(2.0, 0.0))


@X.row
def bound_rise(i: int, n: int):
    # Up off the floor and long, toward the wall behind you.
    return keyed(i, n, [(0.0, POUNCE_COIL), (0.35, LUNGE_FLY, "snap"), (1.0, dict(LUNGE_FLY, lean=40.0, head=(4.0, 0.0, -16.0)), "out")])


@X.row
def bound_wall(i: int, n: int):
    # A held beat on the wall, squashed against it.
    return keyed(i, n, [(0.0, dict(ON_WALL, sq=0.86)), (0.5, ON_WALL, "out"), (1.0, dict(ON_WALL, sq=0.84, ears=-32.0), "in")])


@X.row
def bound_dive(i: int, n: int):
    _, s, c = loop(i, n)
    return dict(LUNGE_FLY, na=(30.0 + 2.0 * s, -6.0 + 3.0 * c), fa=(28.0 - 2.0 * s, -1.0 - 3.0 * c), mouth="gape")


@X.row
def winded(i: int, n: int):
    # Hands on his knees, his ribs heaving, his tongue out, his ears down.
    ph, s, c = loop(i, n)
    heave = 0.5 + 0.5 * s
    return P(hip=(-2.0, 12.0 - 1.5 * heave), lean=38.0 - 4.0 * heave, sq=0.94 + 0.05 * heave, shrug=(0.0, 2.0 - 3.0 * heave),
             head=(4.0, 4.0 - heave, 12.0 - 6.0 * heave), na=(12.0, 30.0 - heave), fa=(15.0, 29.0 - heave), nh="flat", fh="flat",
             nf=(-10.0, 0.0, 0.0), ff=(10.0, 0.0, 0.0), mouth="big", eyes="open" if i % 6 else "closed", ears=-8.0 - 6.0 * heave, brows=1.0,
             hem=(2.0, 1.0))


# ---- The howl ------------------------------------------------------------------

#: The breath before it: the chest swelling, the head going back, the fists
#: clenching low and out.
HOWL_DRAW = P(hip=(-1.0, -1.0), lean=-6.0, sq=1.07, shrug=(-1.0, -3.4), head=(-1.0, -1.0, -22.0), na=(12.0, 24.0), fa=(16.0, 22.0), nh="fist", fh="fist",
              mouth="o", eyes="closed", ears=-10.0, brows=1.0)
#: His head back, his chest up, his fists low and out: the howl.
HOWL = P(hip=(0.0, 1.0), lean=-12.0, sq=1.05, shrug=(-1.0, -2.0), head=(-2.0, -1.0, -48.0), na=(-14.0, 27.0), fa=(18.0, 26.0), nh="fist", fh="fist",
         nf=(-8.0, 0.0, 0.0), ff=(8.0, 0.0, 0.0), mouth="gape", eyes="roll", ears=-20.0, hem=(1.0, 1.0))


@X.row
def howl_tell(i: int, n: int):
    return keyed(i, n, [(0.0, X.full(P())), (0.25, dict(CROUCHED, sq=0.95, mouth="flat"), "out"), (0.8, HOWL_DRAW, "out"), (1.0, HOWL_DRAW)],
                 drag=HEAVY)


@X.row
def howl(i: int, n: int):
    # He shakes with it, and it goes on too long.
    _, s, c = loop(i, n)
    return dict(HOWL, hip=(jitter(i, 0.7), 1.0 + 0.6 * s), head=(-2.0 + jitter(i, 0.5, 2.0), -1.0, -48.0 + 3.0 * s), sq=1.05 + 0.02 * c,
                na=(-14.0 + jitter(i, 1.0, 3.0), 27.0), fa=(18.0 + jitter(i, 1.0, 5.0), 26.0))


@X.row
def taunt(i: int, n: int):
    # The hall's howl: the breath, then the howl.
    u = shot(i, n)
    return X.keys(u, [(0.0, X.full(P())), (0.25, HOWL_DRAW, "out"), (0.4, HOWL, "snap"), (0.85, HOWL), (1.0, X.full(P()), "io")], drag=DRAG)


# ---- The galvanize, the flatline, the charge ------------------------------------

#: His hands on the bolts in his neck, the elbows out and up.
ON_BOLTS = P(hip=(0.0, 0.0), lean=2.0, sq=1.03, shrug=(0.0, -2.0), head=(0.0, 0.0, -14.0), na=(12.0, -10.0), nab=-1.0, fa=(9.0, -9.0), fab=-1.0,
             arm="over", nh="grip", fh="grip", mouth="grit", eyes="pin", ears=-14.0, brows=-1.0, charge=2.0)
#: The discharge: thrown open, splayed, his head back, the current out of
#: him.
THROWN = P(hip=(0.0, -3.0), lean=-10.0, sq=1.1, shrug=(-1.0, -4.0), head=(1.0, -1.0, -20.0), na=(30.0, -10.0), nab=-1.0, fa=(-20.0, -14.0), fab=-1.0,
           arm="over", nh="splay", fh="splay", nf=(-9.0, 0.0, 8.0), ff=(9.0, 0.0, 8.0), mouth="gape", eyes="roll", ears=16.0, hem=(3.0, 4.0), charge=2.0)
#: Flat: his charge spent. Slumped where he stands, his head hung, his arms
#: dead, his jaw slack, his eyes gone.
SLUMP = P(hip=(1.0, 14.0), lean=56.0, sq=0.92, shrug=(2.0, 4.0), head=(4.0, 7.0, 28.0), na=(14.0, 33.0), fa=(19.0, 32.0), nh="flat", fh="limp",
          nf=(-10.0, 0.0, 0.0), ff=(6.0, 0.0, 0.0), mouth="big", eyes="roll", ears=-34.0, brows=1.0, hem=(0.0, 0.0))


@X.row
def galvanize_tell(i: int, n: int):
    # He takes hold of his bolts and the charge comes up through him: he
    # shakes with it, faster.
    pose = keyed(i, n, [(0.0, X.full(P())), (0.3, dict(ON_BOLTS, charge=1.0), "out"), (0.6, ON_BOLTS, "hold"), (1.0, ON_BOLTS)], loop_=False)
    if i >= 2:
        pose = dict(pose, hip=(jitter(i, 0.8), jitter(i, 0.6, 1.0)), head=(jitter(i, 0.6, 2.0), 0.0, -14.0 + jitter(i, 4.0, 3.0)),
                    na=(12.0 + jitter(i, 1.0, 4.0), -10.0 + jitter(i, 1.0, 5.0)), fa=(9.0 + jitter(i, 1.0, 6.0), -9.0), ears=-14.0 + jitter(i, 8.0, 7.0))
    return pose


@X.row
def galvanize(i: int, n: int):
    # The current goes out of him: thrown open, and shaking.
    pose = keyed(i, n, [(0.0, ON_BOLTS), (0.2, THROWN, "snap"), (1.0, dict(THROWN, sq=1.06, head=(-2.0, -1.0, -30.0)), "io")])
    return dict(pose, hip=(pose["hip"][0] + jitter(i, 1.0), pose["hip"][1]), rot=jitter(i, 2.0, 1.0))


#: The lash, gathered: his near hand on his bolt, the far arm out at you,
#: pointing, the claws splayed.
LASH_AIM = P(hip=(-2.0, 2.0), lean=-2.0, sq=1.03, shrug=(0.0, -1.6), head=(1.0, 0.0, -10.0), na=(11.0, -10.0), nab=-1.0, arm="over",
             fa=(30.0, -12.0), fab=-1.0, nh="grip", fh="point", nf=(-10.0, 0.0, 0.0), ff=(9.0, 0.0, 6.0), mouth="grit", eyes="pin", ears=-18.0,
             charge=2.0, look=(1.0, -0.4))
#: The lash: thrown at you down his arm, his body behind it.
LASH_THROW = P(hip=(6.0, 3.0), lean=16.0, sq=0.97, shrug=(1.0, 0.0), head=(3.0, 1.0, -12.0), na=(12.0, -8.0), nab=-1.0, arm="over",
               fa=(33.0, -10.0), fab=-1.0, nh="grip", fh="splay", nf=(-14.0, 0.0, 0.0), ff=(14.0, 0.0, -4.0), mouth="gape", eyes="pin", ears=-24.0,
               charge=2.0)


@X.row
def lash_tell(i: int, n: int):
    # He takes hold of his bolt and points at you; the charge climbs his arm.
    pose = keyed(i, n, [(0.0, X.full(P())), (0.4, LASH_AIM, "out"), (1.0, LASH_AIM)])
    if i >= 3:
        pose = dict(pose, fa=(pose["fa"][0] + jitter(i, 0.6), pose["fa"][1] + jitter(i, 0.6, 2.0)), hip=(pose["hip"][0] + jitter(i, 0.4, 3.0), pose["hip"][1]))
    return pose


@X.row
def lash(i: int, n: int):
    # It goes: a kick back through him, then held while it burns.
    pose = keyed(i, n, [(0.0, LASH_AIM), (0.2, LASH_THROW, "snap"), (1.0, dict(LASH_THROW, lean=10.0, sq=1.0), "out")])
    return dict(pose, hip=(pose["hip"][0] + jitter(i, 0.8), pose["hip"][1]))


@X.row
def flatline(i: int, n: int):
    # Out: he sways where he stands, his head hanging; twice his body jumps
    # with what is left in the bolts.
    ph, s, c = loop(i, n)
    pose = planted(dict(SLUMP, hip=(1.0 + 0.8 * s, 14.0 + 1.2 * c), lean=56.0 + 2.0 * s, shrug=(2.0, 4.0 - 2.0 * (0.5 + 0.5 * c)),
                        head=(4.0 + 0.6 * s, 7.0, 28.0 + 5.0 * c)), 0.0, 1.0)
    if i in (5, 12):
        pose = dict(pose, shrug=(1.0, 0.0), head=(3.0, 4.0, 16.0), fh="splay", fa=(22.0, 28.0), sq=0.95, ears=-24.0)
    return pose


@X.row
def recharge(i: int, n: int):
    # The coils find him: up in a jolt, splayed, and himself again.
    return keyed(i, n, [(0.0, planted(SLUMP)), (0.2, THROWN, "snap"), (0.45, dict(THROWN, sq=1.04), "hold"), (1.0, X.full(P()), "out")])


@X.row
def awaken(i: int, n: int):
    # The first charge: dead, then the jolt goes through him, his eyes snap
    # open to pins, and he stands up into himself.
    alive = dict(X.full(P()), eyes="pin", ears=8.0, head=(1.0, 0.0, -6.0), mouth="open")
    pose = keyed(i, n, [(0.0, planted(SLUMP)), (0.2, planted(SLUMP)), (0.32, THROWN, "snap"), (0.5, dict(SLUMP, eyes="pin", sq=0.97, head=(3.0, 4.0, 16.0)), "out"),
                        (0.6, dict(THROWN, eyes="pin", mouth="big"), "snap"), (1.0, alive, "out")])
    if 0.25 < shot(i, n) < 0.7:
        pose = dict(pose, rot=jitter(i, 4.0), hip=(pose["hip"][0] + jitter(i, 1.2, 1.0), pose["hip"][1]))
    return pose


@X.row
def shock(i: int, n: int):
    # The lightning between the phases: he convulses in it.
    k = i % 2
    pose = dict(THROWN if k == 0 else dict(THROWN, na=(8.0, -20.0), fa=(-2.0, -18.0), head=(-1.0, 0.0, -20.0), sq=1.04, mouth="big"))
    return dict(pose, rot=jitter(i, 6.0), hip=(jitter(i, 2.0, 1.0), -2.0 + jitter(i, 1.0, 2.0)), ears=12.0 + jitter(i, 10.0, 3.0))


# ---- Hurt and dead -------------------------------------------------------------

STRUCK = P(hip=(-5.0, 2.0), lean=-16.0, sq=0.96, head=(-3.0, -1.0, -24.0), na=(6.0, 24.0), fa=(16.0, 16.0), nh="splay", fh="splay", nf=(-8.0, 0.0, 0.0),
           ff=(8.0, -5.0, -22.0), eyes="wince", mouth="big", brows=1.0, off=(-3.0, 0.0), hem=(0.0, 6.0), ears=-26.0)


@X.row
def hit(i: int, n: int):
    return keyed(i, n, [(0.0, X.full(P(mouth="o"))), (0.2, STRUCK, "snap"), (0.5, STRUCK, "hold"), (1.0, X.full(P(lean=7.0)), "back")])


#: On his back, his boots up.
SUPINE = P(rot=-90.0, hip=(-2.0, 25.5), off=(13.0, 0.0), head=(0.0, 0.0, 6.0), na=(8.0, 24.0), fa=(4.0, 22.0), nh="splay", fh="soft",
           nf=(-4.5, 25.0, 0.0), ff=(4.5, 25.0, -10.0), eyes="dead", mouth="big", brows=0.0, lean=0.0, ears=-30.0)


@X.row
def death(i: int, n: int):
    # The charge goes out of him in a last spasm; he staggers, howls once,
    # and goes over backward like a tree. His boot twitches.
    last = P(hip=(-2.0, 0.0), lean=-14.0, head=(-1.0, -1.0, -42.0), na=(-6.0, 28.0), fa=(10.0, 26.0), nh="fist", fh="fist", eyes="roll", mouth="gape",
             sq=1.05, ears=-20.0)
    stagger = dict(STRUCK, hip=(-8.0, 6.0), lean=20.0, head=(2.0, 4.0, 24.0), eyes="roll", mouth="big", sq=0.94)
    toppling = X.blend(last, SUPINE, 0.5)
    toppling = dict(toppling, off=(toppling["off"][0], toppling["off"][1] - 8.0))
    pose = keyed(i, n, [(0.0, STRUCK), (0.12, THROWN, "snap"), (0.25, stagger, "out"), (0.42, last, "out"), (0.52, last, "hold"),
                        (0.62, toppling, "in"), (0.72, SUPINE, "snap"), (1.0, SUPINE)], drag=HEAVY)
    if i == n - 3:
        pose = dict(pose, ff=(4.5, 22.0, -30.0))
    return pose


X.rows = [("idle", 16, 90), ("walk", 12, 100), ("prowl", 12, 70), ("run", 8, 85), ("jump", 6, 100), ("fall", 6, 100), ("land_hard", 8, 70),
          ("rake_tell", 8, 80), ("rake_a", 6, 50), ("rake_b", 6, 50), ("rake_c", 8, 55), ("rake_recover", 6, 80),
          ("hammer_tell", 10, 100), ("hammer_slam", 6, 50), ("hammer_stuck", 8, 80), ("hammer_pull", 6, 60),
          ("lunge_tell", 8, 90), ("lunge", 6, 60), ("lunge_skid", 8, 50),
          ("bound_rise", 6, 60), ("bound_wall", 4, 70), ("bound_dive", 4, 60), ("winded", 12, 90),
          ("howl_tell", 8, 100), ("howl", 12, 70), ("taunt", 12, 100),
          ("galvanize_tell", 10, 60), ("galvanize", 8, 60), ("lash_tell", 8, 80), ("lash", 6, 60), ("flatline", 16, 110), ("recharge", 8, 50),
          ("awaken", 14, 70), ("shock", 8, 50), ("hit", 6, 60), ("death", 18, 90)]

# ---- What his blows do -------------------------------------------------------


def _muzzle(ctx) -> Point:
    """The tip of his nose, in the frame."""
    tip = turned((25.0 * HEAD_SIZE, 0.0), ctx.turn)
    return (ctx.head[0] + tip[0], ctx.head[1] + tip[1])


def claw_tips(pose, near: bool) -> List[Point]:
    """Where the claws of a hand are in ``pose``, in frame pixels: the tip
    of each finger's claw (index first), from the hand pose it is drawn in
    (``HAND_POSES``) at the wrist the rig solves, turned along the forearm.
    The claw trail is drawn from these, so a cut is where a claw went."""
    pose = X.full(pose)
    _shoulder, elbow, wrist = X.arm_joints(pose, near)
    turn = math.degrees(math.atan2(wrist[1] - elbow[1], wrist[0] - elbow[0]))
    mode = str(pose["nh" if near else "fh"])
    spread, bends, _thumb, claws_out = HAND_POSES.get(mode, HAND_POSES["soft"])
    reach = (5.4 if mode == "claw" else 4.0) if claws_out else 0.0
    out = []
    for (base, l1, l2), sp, (b1, b2) in zip(FINGERS, spread, bends):
        _k, tip, _t, a2 = _finger(base, l1, l2, sp + b1, sp + b1 + b2)
        end = (tip[0] + reach * math.cos(math.radians(a2)), tip[1] + reach * math.sin(math.radians(a2)))
        # The near hand is drawn mirrored (``_hand``).
        r = turned((end[0] * HAND, end[1] * HAND * (-1.0 if near else 1.0)), turn)
        out.append((wrist[0] + r[0], wrist[1] + r[1]))
    return out


def _claw_marks(anim: str, i: int, n: int, near: bool, span: float) -> List[Stamp]:
    """Three cuts in the air, each along the path ONE claw tip took over the
    last ``span`` frames (``claw_tips``): thick where the claw is, thin where
    it was. Nothing is ahead of the claws, and the cuts go on after they
    stop, shrinking from their tail."""
    # The pose is a function of time, so the paths are sampled between
    # frames: curves, not sticks.
    steps = int(16 * span)
    tracks = [claw_tips(X.poses[anim](max(0.0, i - span * k / steps), n), near)[:3] for k in range(steps, -1, -1)]
    paths = [[t[c] for t in tracks] for c in range(3)]
    length = sum(math.dist(a, b) for a, b in zip(paths[1], paths[1][1:]))
    if length < 14.0:
        return []
    head = paths[1][-1]
    cuts = tuple(tuple((round(x - head[0], 1), round(y - head[1], 1)) for x, y in path) for path in paths)

    def paint(d) -> None:
        # Each cut is thin and bright where its claw is, and thins to nothing
        # where it was: a pale edge, a white core. No dark outline.
        for edge, colour in ((True, SLASH_DARK), (False, SLASH)):
            for pts in cuts:
                for j in range(len(pts) - 1):
                    w = 3.4 * ((j + 1) / (len(pts) - 1)) ** 1.3
                    K.stroke(d, [K.at(*pts[j]), K.at(*pts[j + 1])], colour, w + (1.4 if edge else 0.0))

    return [(K.piece(("claw_cut", anim, i, near), paint), R.pin(head), "claw_cuts", 0.0)]


def _arc(key: tuple, a: Point, b: Point, seed: int, kinks: int = 6, width: float = 2.2):
    """A crooked line of current from ``a`` to ``b`` (frame points, painted
    from ``a``), with a fork or two off it: a white core in a blue glow, and
    no dark outline. Place it unturned at ``pin(a)``."""
    length = math.dist(a, b) or 1.0
    ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length

    def rnd(k: int) -> float:
        return math.sin(seed * 91.7 + k * 12.3)

    main = [(0.0, 0.0)]
    for k in range(1, kinks):
        t = k / kinks
        side = rnd(k) * min(8.0, length * 0.2)
        main.append((ux * length * t - uy * side, uy * length * t + ux * side))
    main.append((b[0] - a[0], b[1] - a[1]))
    forks = []
    for f in (2, kinks - 2):
        if 0 < f < len(main) - 1:
            x, y = main[f]
            ang = math.atan2(uy, ux) + (0.9 if rnd(f + 40) > 0 else -0.9)
            reach = length * 0.22
            forks.append([(x, y), (x + math.cos(ang) * reach * 0.5 + rnd(f + 50) * 2.0, y + math.sin(ang) * reach * 0.5),
                          (x + math.cos(ang) * reach, y + math.sin(ang) * reach)])
    lines = tuple(tuple((round(px, 1), round(py, 1)) for px, py in line) for line in [main] + forks)

    def paint(d) -> None:
        for glow, colour in ((True, ARC_GLOW), (False, ARC_CORE)):
            for k, line in enumerate(lines):
                w = width * (1.0 if k == 0 else 0.6)
                K.stroke(d, [K.at(*pt) for pt in line], colour, w * (2.4 if glow else 0.8))

    return K.piece(("arc", key, seed, lines), paint)


ARC_CORE: RGBA = (236, 246, 255, 255)
ARC_GLOW: RGBA = (110, 170, 255, 255)


def _bolt_point(ctx) -> Point:
    top = turned(BUILD.throat, ctx.turn)
    top = (ctx.head[0] + top[0], ctx.head[1] + top[1])
    return (lerp(ctx.neck[0], top[0], 0.55), lerp(ctx.neck[1], top[1], 0.55))


def _effects(ctx) -> List[Stamp]:
    out: List[Stamp] = []
    anim, u, i, n = ctx.anim, ctx.u, ctx.i, ctx.n
    bolt = _bolt_point(ctx)
    if anim == "rake_a" and i >= 1:
        out.extend(_claw_marks(anim, i, n, True, 1.3))
    elif anim == "rake_b" and i >= 1:
        out.extend(_claw_marks(anim, i, n, False, 1.3))
    elif anim == "rake_c" and u >= 0.45:
        out.extend(_claw_marks(anim, i, n, True, 1.3))
    elif anim == "lunge" and i % 3 != 2:
        out.append((R.burst(K, 12.0, SPARK, SPARK_DARK, 9), (_muzzle(ctx)[0] + 6.0, _muzzle(ctx)[1] + 4.0), "bite", 0.0))
    elif anim in ("hammer_slam",) and 0.2 <= u <= 0.8:
        late = u > 0.5
        at = ((ctx.hand[0] + ctx.far_hand[0]) / 2.0 + 6.0, ctx.ground - 12.0)
        out.append((R.burst(K, 13.0 if late else 18.0, DUST, DUST_DARK, 10), at, "ground_hit", 0.0))
        out.append((R.dust(K, 4.4 if late else 6.4, DUST, DUST_DARK), (at[0] + (28.0 if late else 18.0), ctx.ground - 5.0), "dust_ahead", 0.0))
        out.append((R.dust(K, 4.0 if late else 5.8, DUST, DUST_DARK), (at[0] - (26.0 if late else 16.0), ctx.ground - 4.0), "dust_behind", 0.0))
    elif anim == "hammer_stuck" and i % 4 == 0:
        out.append((R.dust(K, 3.0, DUST, DUST_DARK), ((ctx.hand[0] + ctx.far_hand[0]) / 2.0 + 10.0, ctx.ground - 4.0), "grit", 0.0))
    elif anim == "lunge_skid" and 0.15 <= u <= 0.7:
        out.append((R.dust(K, 6.0 if u < 0.4 else 4.0, DUST, DUST_DARK), (ctx.far_foot[0] + 14.0, ctx.ground - 5.0), "plough", 0.0))
        out.append((R.dust(K, 4.0, DUST, DUST_DARK), (ctx.foot[0] + 8.0, ctx.ground - 3.0), "plough_back", 0.0))
    elif anim in ("howl", "taunt") and str(ctx.pose["mouth"]) == "gape":
        # The howl: rings go out of his mouth, one more each frame.
        mouth = _muzzle(ctx)
        up = ctx.turn
        for k in range(1 + ctx.i % 3):
            r = 12.0 + 11.0 * k
            out.append((R.swoosh(K, r, int(up - 36), int(up + 36), 3.2, SPARK, SPARK_DARK), (mouth[0] - 4.0, mouth[1]), f"howl_{k}", 0.0))
    elif anim == "idle" and str(ctx.pose["eyes"]) == "pin":
        # The tic is the charge in him: a spark across his neck.
        out.append((R.burst(K, 6.0, ARC_CORE, ARC_GLOW, 6), bolt, "tic_spark", 0.0))
        out.append((_arc("tic", (bolt[0] - 9.0, bolt[1] + 2.0), (bolt[0] + 11.0, bolt[1] - 1.0), i, kinks=3, width=1.4),
                    R.pin((bolt[0] - 9.0, bolt[1] + 2.0)), "tic_arc", 0.0))
    elif anim == "lash_tell" and i >= 2:
        # The charge climbs from the bolt in his hand, across his chest, out
        # along the arm that points.
        out.append((_arc("lash_climb", bolt, ctx.far_elbow, i, kinks=4, width=1.6), R.pin(bolt), "arc_climb", 0.0))
        if i >= 4:
            out.append((_arc("lash_hand", ctx.far_elbow, ctx.far_hand, i + 3, kinks=3, width=1.4), R.pin(ctx.far_elbow), "arc_hand", 0.0))
        out.append((R.burst(K, 6.0 + i % 3, ARC_CORE, ARC_GLOW, 7), bolt, "bolt_spark", 0.0))
    elif anim == "lash":
        # It leaves his hand: the first reach of it, out of the frame's edge
        # (the fight carries it on).
        hand = ctx.far_hand
        out.append((_arc("lash_arm", bolt, hand, i, kinks=5, width=2.2), R.pin(bolt), "arc_arm", 0.0))
        to = (hand[0] + 70.0, hand[1] - 20.0 + 6.0 * math.sin(i * 1.7))
        out.append((_arc("lash_out", hand, to, i + 5, kinks=6, width=3.0), R.pin(hand), "arc_out", 0.0))
        out.append((R.burst(K, 12.0, ARC_CORE, ARC_GLOW, 9), hand, "lash_spark", 0.0))
    elif anim == "galvanize_tell" and i >= 2:
        # The current runs from his bolts down his arms to his hands.
        out.append((_arc("bolt_near", bolt, ctx.elbow, i), R.pin(bolt), "arc_arm", 0.0))
        if i % 2 == 0:
            out.append((_arc("bolt_far", bolt, ctx.far_elbow, i + 7), R.pin(bolt), "arc_far_arm", 0.0))
        out.append((R.burst(K, 7.0 + 2.0 * (i % 2), ARC_CORE, ARC_GLOW, 7), bolt, "bolt_spark", 0.0))
    elif anim in ("galvanize", "shock") or (anim == "recharge" and u < 0.55) or (anim == "awaken" and 0.25 < u < 0.7):
        # The discharge: out of his hands, and over all of him.
        for k, (hand, seed) in enumerate(((ctx.hand, i), (ctx.far_hand, i + 31))):
            to = (hand[0] + 18.0 * math.cos(seed), hand[1] - 34.0 - 8.0 * math.sin(seed * 1.7))
            out.append((_arc(f"hand_{k}", hand, to, seed, kinks=5), R.pin(hand), f"arc_hand_{k}", 0.0))
        hip = ctx.hip
        out.append((_arc("body", (hip[0] - 6.0, hip[1] - 10.0), (hip[0] + 10.0, hip[1] + 18.0), i + 13, kinks=4, width=1.6),
                    R.pin((hip[0] - 6.0, hip[1] - 10.0)), "arc_body", 0.0))
        out.append((R.burst(K, 10.0, ARC_CORE, ARC_GLOW, 8), bolt, "bolt_spark", 0.0))
        up = (bolt[0] + 6.0 * math.sin(i * 2.3), bolt[1] - 60.0)
        out.append((_arc("bolt_up", bolt, up, i + 21, kinks=6, width=2.4), R.pin(bolt), "arc_bolt_up", 0.0))
    elif anim == "flatline" and i in (5, 6, 12, 13):
        # What is left in the bolts: a sputter.
        out.append((R.burst(K, 6.0, SPARK, SPARK_DARK, 6), bolt, "sputter", 0.0))
        if i in (5, 12):
            out.append((_arc("sputter", bolt, ctx.hand, i, kinks=5, width=1.6), R.pin(bolt), "arc_sputter", 0.0))
    elif anim == "hit" and u <= 0.5:
        out.append((R.burst(K, 13.0, SPARK, SPARK_DARK, 9), (ctx.head[0] + 14.0, ctx.head[1] - 4.0), "struck", 0.0))
    elif anim == "death" and 0.08 <= u <= 0.3:
        out.append((_arc("death", bolt, ctx.hand, i, kinks=6), R.pin(bolt), "arc_death", 0.0))
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
