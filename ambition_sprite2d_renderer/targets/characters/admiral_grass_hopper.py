"""Sprite generator for Admiral Grass Hopper: a grasshopper, and an admiral.

An affectionate caricature of Rear Admiral Grace Hopper.

The look (2026-10-13): a small old lady who is a grasshopper, in the blue
uniform of an admiral, seen three quarters from the front, facing right. Her
skin is green. Her eyes are large and dark behind round glasses, and two long
feelers go back from under her cap. A white cap with a black peak and a gold
badge; a dark blue jacket with gold buttons and the gold rings of her rank
on each cuff, a white collar and a black tie, and a blue skirt to her knee.
Her legs are a grasshopper's: long, green, and the knee is behind her. Her
wings are folded down her back like the tails of a coat. She stands very
straight.

She is a grown woman (she is seventy), not a mascot. She holds nothing at
rest: her baton is in her hand only in the rows that are its own. There is
no drop shadow.

What she shows: the baton, which is also a pointer; the length of wire that
is a nanosecond; and the moth she found in the relay.

She is a person of ``_person_rig``: the bones, the poses and the frame are
shared; the head, the clothes, how she stands and what she shows are hers.
Her portraits are frames of this sheet.
"""

from __future__ import annotations

import math
from typing import List

from ._ai_era_kit import RGBA, mix, pin
from ._ai_era_kit import WHITE as _SOLID
from . import _person_rig as R
from ._person_rig import Build, Person, Stamp, loop, shot

TARGET_NAME = "admiral_grass_hopper"
TARGET_BASENAME = TARGET_NAME
DISPLAY_NAME = "Admiral Grass Hopper"

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_admiral_grass_hopper",
        "display_name": "Admiral Grass Hopper",
    },
    "authoring_description": {
        "parody_of": "Rear Admiral Grace Hopper",
        "core_joke": "A grasshopper admiral who literalizes the Hopper name while keeping Grace Hopper's naval-computing legacy at the center.",
        "visual_inspirations": [
            "Grace Hopper portraiture and U.S. Navy officer presentation",
            "storybook grasshopper silhouettes with long hind legs and antennae",
            "a compact metroidvania-friendly side profile rather than a realistic insect",
            "gold-trimmed admiral coat, cap badge, and a command baton that can also read as a debugging pointer",
        ],
        "design_notes": [
            "Keep the character likable and readable first, then let the entomology sell the pun.",
            "The coat, epaulettes, and hat should do most of the 'admiral' work; the abdomen, antennae, and hind legs should do most of the 'grasshopper' work.",
            "The baton can double as a compiler pointer, classroom stick, or melee flourish.",
            "The tone should celebrate Grace Hopper rather than mocking her: this is a tribute-parody character.",
        ],
        "reference_hooks": [
            "COBOL / compiler pioneer",
            "debugging lore and the famous moth anecdote",
            "naval command presence",
            "fast hopping movement and crisp lecture-energy dialog",
        ],
    },
    "gameplay_description": {
        "role": "mobile support-skirmisher / brilliant officer",
        "combat_identity": [
            "quick side-hops and sharp baton strikes",
            "commanding bark-based support fantasy",
            "can read as a mentor NPC, miniboss, or playable light fighter",
        ],
        "signature_moves": [
            "Bug Report: a precise baton jab or slash that 'flags' an enemy",
            "Compiler Directive: a command gesture that could buff allies or alter battlefield behavior",
            "Debug Hop: a springy reposition with exaggerated grasshopper leg compression",
        ],
        "authoring_notes": [
            "This sheet only includes a general-purpose slash, not a full projectile or support kit yet.",
            "Future expansion should probably add a pronounced hop / leap attack row and a dedicated command-point emote.",
            "Because Grace Hopper is a foundational computing figure, dialog should lean clever, direct, and impatient with sloppy thinking.",
        ],
    },
    "dialogue_hints": {
        "suggested_barks": [
            "Debug it at the source!",
            "Hop to it!",
            "Compiler says no!",
            "Mind your logic!",
            "That bug is now documented!",
            "Order from disorder!",
        ],
        "fallback_dialogue": [
            "I prefer clear thinking, clean systems, and decisive action.",
            "A bug ignored is a bug promoted.",
            "You can waste time arguing with reality, or you can measure it and move.",
            "The trick is to make complex work look disciplined.",
        ],
    },
    "body": {
        "body_plan": "InsectoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "locomotion_hint": "Walk",
        "traits": [
            "story",
            "combatant",
            "scientist_parody",
            "insectoid",
            "naval_officer",
            "computer_science",
            "mentor",
            "hopper",
        ],
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": {"height_px": None, "distance_px": None, "source": "grasshopper_hind_legs"},
            "climb": None,
            "crawl": None,
            "fly": None,
            "swim": None,
            "use_lifts": True,
            "door_access": ["public"],
        },
        "interactions": {
            "talk": True,
            "trade": None,
            "carry": None,
            "open_doors": ["public"],
        },
    },
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "peaceful"},
    "visual": {
        "default_pose": "idle",
        "portrait_style": "dialog_closeup",
        "portrait_source": TARGET_NAME,
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "action.melee.primary": {
            "animation": "slash",
            "events": [
                {"t": 0.34, "event": "hitbox_active_start", "source": "admiral_grass_hopper.slash"},
                {"t": 0.60, "event": "hitbox_active_end", "source": "admiral_grass_hopper.slash"},
            ],
        },
        "emote.taunt": {"animation": "taunt", "events": []},
        "damage.hit": {"animation": "hurt", "events": []},
        "lifecycle.death": {"animation": "death", "events": []},
    },
    "sockets": {
        "head": {"source": "admiral_grass_hopper.authored", "point": {"x": 72.0, "y": 26.0}},
        "chest": {"source": "admiral_grass_hopper.authored", "point": {"x": 64.0, "y": 54.0}},
        "hand_l": {"source": "admiral_grass_hopper.authored", "point": {"x": 58.0, "y": 64.0}},
        "hand_r": {"source": "admiral_grass_hopper.authored", "point": {"x": 84.0, "y": 62.0}},
        "weapon_grip": {"source": "admiral_grass_hopper.authored", "point": {"x": 86.0, "y": 60.0}},
        "weapon_tip": {"source": "admiral_grass_hopper.authored", "point": {"x": 106.0, "y": 54.0}},
        "speech_bubble": {"source": "admiral_grass_hopper.authored", "point": {"x": 72.0, "y": 8.0}},
    },
    "tags": [
        "story",
        "combatant",
        "scientist_parody",
        "insectoid",
        "naval_officer",
        "computer_science",
        "grace_hopper_parody",
        "mentor",
    ],
}

OUTLINE = (18, 22, 22, 255)
GREEN: RGBA = (112, 178, 104, 255)
GREEN_SHADE: RGBA = (72, 134, 80, 255)
GREEN_DEEP: RGBA = (42, 90, 58, 255)
GREEN_PALE: RGBA = (176, 226, 150, 255)
NAVY: RGBA = (40, 54, 104, 255)
NAVY_DARK: RGBA = (24, 32, 70, 255)
NAVY_LIGHT: RGBA = (78, 100, 166, 255)
GOLD: RGBA = (236, 198, 86, 255)
GOLD_DARK: RGBA = (170, 124, 50, 255)
CAP: RGBA = (240, 242, 246, 255)
CAP_SHADE: RGBA = (190, 198, 214, 255)
INK: RGBA = (26, 24, 30, 255)
LENS: RGBA = (226, 240, 248, 120)
WING: RGBA = (196, 232, 190, 230)
WING_DARK: RGBA = (120, 170, 130, 255)
WOOD: RGBA = (132, 90, 60, 255)
WOOD_DARK: RGBA = (80, 54, 42, 255)
MOTH: RGBA = (206, 190, 160, 255)
MOTH_DARK: RGBA = (130, 112, 96, 255)
COPPER: RGBA = (214, 132, 84, 255)

#: Small, 155 cm, with the legs of a grasshopper: they are longer than the
#: way to the floor, and the knee is behind her.
BUILD = Build(hip_up=42.0, thigh=22.0, shin=25.0, neck=(0.6, -30.0), upper=16.6, fore=15.6, near_shoulder=(-3.8, -26.6), far_shoulder=(4.8, -26.2),
              near_hip=(-3.0, 0.0), far_hip=(3.0, 0.0), head_up=(1.0, -12.0), height=98.0, half_width=(12.0, 13.0), knee=1.0)

X = Person(TARGET_NAME, BUILD)
K = X.K
P = X.P
TOP = BUILD.neck[1] - 2.0
#: How far under her hips the hem of her skirt is.
HEM = 15.0


def _front(d, hb: float, hf: float) -> None:
    """Her collar and tie, the buttons, her ribbons, the hem of the jacket
    and the skirt under it."""
    by = TOP + 12.5
    K.oval(d, K.at(5.8, by + 0.4), 2.4, 1.8, NAVY_LIGHT)
    K.poly(d, [K.at(0.6, by + 3.4), K.at(4.4, by + 4.8), K.at(9.6, by + 3.6), K.at(8.6, by + 6.0), K.at(4.2, by + 6.8), K.at(0.6, by + 5.0)], NAVY_DARK)
    # The collar and the tie.
    K.poly(d, [K.at(1.6, TOP - 1.0), K.at(8.6, TOP - 1.0), K.at(5.6, TOP + 7.0)], CAP)
    K.poly(d, [K.at(4.4, TOP + 0.6), K.at(6.4, TOP + 0.6), K.at(6.0, TOP + 6.4), K.at(5.2, TOP + 7.4), K.at(4.6, TOP + 6.2)], INK)
    K.line(d, [K.at(1.6, TOP - 1.0), K.at(5.6, TOP + 7.0), K.at(8.6, TOP - 1.0)], NAVY_DARK, 0.6)
    # Two rows of gold buttons, and the ribbons over her heart.
    for y in (-17.0, -12.6, -8.2):
        for x in (2.6, 6.6):
            K.oval(d, K.at(x, y), 0.9, 0.9, GOLD, GOLD_DARK, 0.3)
    for k, colour in enumerate(((206, 70, 70, 255), GOLD, (86, 150, 220, 255))):
        K.poly(d, [K.at(-3.6 + k * 1.8, -22.4), K.at(-2.0 + k * 1.8, -22.4), K.at(-2.0 + k * 1.8, -20.6), K.at(-3.6 + k * 1.8, -20.6)], colour)
    # The hem of the jacket, and the skirt.
    K.line(d, [K.at(-9.0, -3.0), K.at(10.0, -2.6)], NAVY_DARK, 0.8)
    for x in (-3.0, 3.0):
        K.line(d, [K.at(x, -2.0), K.at(x * 1.3 + (hf if x > 0 else -hb) * 0.3, HEM - 1.0)], NAVY_DARK, 0.6)


X.torso = R.make_figure(K, ("hopper",), NAVY, NAVY_DARK, back=(6.8, 7.0, 6.0, 8.0, 9.6), front=(6.0, 9.2, 6.0, 8.2, 9.4), hem_y=HEM, top=TOP,
                        shoulders=((-4.0, -26.2), (3.4, -26.2)), shoulder_r=(4.2, 3.4), waist_y=-10.0, shade_from=7.0, detail=_front)

NEAR_EYE = (2.0, -0.6)
FAR_EYE = (7.2, -0.8)


def _cap_shape(d) -> None:
    # The crown of her cap, wide and flat, and its peak.
    K.poly(d, [K.at(-9.6, -7.0), K.at(-10.6, -11.6), K.at(-4.0, -14.6), K.at(6.0, -14.6), K.at(10.6, -11.4), K.at(9.6, -7.0)], _SOLID)
    K.poly(d, [K.at(6.0, -7.4), K.at(13.0, -5.6), K.at(12.4, -4.2), K.at(5.0, -5.0)], _SOLID)


def _cap(d) -> None:
    K.poly(d, [K.at(-20.0, -30.0), K.at(20.0, -30.0), K.at(20.0, -7.6), K.at(9.6, -7.6), K.at(-9.6, -6.4), K.at(-20.0, -6.4)], CAP)
    K.poly(d, [K.at(-10.0, -8.8), K.at(10.0, -9.6), K.at(10.0, -6.8), K.at(-10.0, -5.8)], INK)
    K.line(d, [K.at(-9.6, -9.0), K.at(9.8, -9.8)], GOLD, 0.7)
    K.poly(d, [K.at(4.0, -7.6), K.at(14.0, -5.4), K.at(13.0, -3.6), K.at(4.0, -5.2)], INK)
    K.poly(d, [K.at(-9.0, -12.0), K.at(-4.0, -14.2), K.at(-2.0, -10.4), K.at(-9.6, -9.6)], CAP_SHADE)
    # The badge.
    K.oval(d, K.at(5.2, -11.4), 2.0, 2.2, GOLD, GOLD_DARK, 0.4)
    K.oval(d, K.at(5.2, -11.4), 0.8, 0.9, CAP)
    # Under the cap her head is a grasshopper's: no hair, and a plate at the back of it.
    K.poly(d, [K.at(-20.0, -6.4), K.at(-3.4, -6.4), K.at(-4.6, 1.0), K.at(-7.0, 4.0), K.at(-20.0, 4.0)], GREEN_SHADE)


def _face(d) -> None:
    # Her eyes are large and dark, and her glasses are round.
    for (cx, cy), r in ((NEAR_EYE, 3.3), (FAR_EYE, 2.3)):
        K.oval(d, K.at(cx, cy), r * 0.82, r, INK)
        K.oval(d, K.at(cx - r * 0.25, cy - r * 0.35), r * 0.26, r * 0.3, GREEN_PALE)
        K.oval(d, K.at(cx, cy), r + 0.4, r + 0.5, LENS, GOLD_DARK, 0.5)
    K.line(d, [K.at(NEAR_EYE[0] + 3.6, -0.8), K.at(FAR_EYE[0] - 2.6, -0.9)], GOLD_DARK, 0.5)
    K.line(d, [K.at(NEAR_EYE[0] - 3.6, -0.8), K.at(-4.6, -1.6)], GOLD_DARK, 0.5)
    # The lines of seventy years, and the plates of her jaw.
    K.line(d, [K.at(3.6, 4.6), K.at(2.4, 6.6)], GREEN_DEEP, 0.4)
    K.line(d, [K.at(-2.0, 2.0), K.at(0.4, 6.0), K.at(3.6, 8.6)], GREEN_DEEP, 0.4)


_head = R.make_head(K, ("hopper",), GREEN, GREEN_SHADE, GREEN_DEEP, skull=(0.0, -2.4, 7.8, 8.6), jaw=(2.8, 4.0, 5.0, 6.6), nose=None, ear=None,
                    shape=_cap_shape, under=_cap, over=_face)
_mouth = R.make_mouth(K, (6.0, 6.4), (150, 60, 66, 255), wide=0.7, lips=(170, 70, 80, 255))


def _lids(mode: str):
    """Her eyes are in the head; this is their lids, when they shut."""
    if mode != "closed":
        return None

    def paint(d) -> None:
        for (cx, cy), r in ((NEAR_EYE, 3.3), (FAR_EYE, 2.3)):
            K.oval(d, K.at(cx, cy), r * 0.82, r, GREEN_SHADE)
            K.line(d, [K.at(cx - r * 0.8, cy + 0.4), K.at(cx + r * 0.8, cy + 0.4)], GREEN_DEEP, 0.6)

    return K.piece(("hopper_lids",), paint)


X.head_layers = lambda pose: [(_head(), "head"), (_lids(str(pose["eyes"])), "lids"), (_mouth(str(pose["mouth"])), "mouth")]
X.neck = R.make_neck(K, GREEN_SHADE, 3.6)
# The rings of her rank are on each cuff: one wide, one narrow.
X.upper_arm = lambda near: [(0.0, 1.0, 6.0, 5.2, NAVY if near else NAVY_DARK)]
X.forearm = lambda near: [(0.0, 1.0, 5.2, 4.6, NAVY if near else NAVY_DARK), (0.62, 0.8, 4.8, 4.8, GOLD if near else GOLD_DARK), (0.86, 0.94, 4.6, 4.6, GOLD if near else GOLD_DARK)]
# Her legs: green, thin, and the shin has the spines of a grasshopper's.
X.thigh = lambda near: [(0.0, 1.0, 5.8, 3.8, GREEN if near else GREEN_SHADE)]
X.shin = lambda near: [(0.0, 1.0, 3.4, 2.6, GREEN_SHADE if near else GREEN_DEEP), (0.0, 0.14, 4.0, 4.0, GREEN if near else GREEN_SHADE)]
X.hand = R.make_hand(K, GREEN, GREEN_SHADE, GREEN_DEEP, size=0.82)
X.shoe = R.make_shoe(K, INK, (10, 10, 14, 255), BUILD.ankle_up, long=0.86, heel=1.0)


def _feelers(ctx) -> List[Stamp]:
    """Her two feelers, from under her cap, back and up; and her wings,
    folded down her back."""
    a = math.radians(ctx.turn)
    root = (ctx.head[0] + 3.0 * math.cos(a) + 12.6 * math.sin(a), ctx.head[1] + 3.0 * math.sin(a) - 12.6 * math.cos(a))
    at = pin(root)
    moving = ctx.anim in ("walk", "slash", "hurt")
    chains = [R.chain((root[0] - at[0] + dx, root[1] - at[1]), 5, 4.4, 250.0 - spread, wave=7.0 if moving else 3.0, curl=-14.0, phase=ctx.phase, lead=lead)
              for dx, spread, lead in ((0.0, 0.0, 0.0), (2.4, 16.0, 1.2))]
    out: List[Stamp] = [(R.ribbon(K, ("hopper_feelers",), chains, 1.3, GREEN_SHADE, GREEN, taper=0.3), at, "feelers", 0.0)]
    sway = int(round(float(ctx.pose["hem"][0])))

    def shape(d) -> None:
        K.poly(d, [K.at(-4.0, TOP + 5.0), K.at(-8.6, TOP + 9.0), K.at(-13.0 - sway, HEM + 3.0), K.at(-9.6 - sway, HEM + 8.0), K.at(-5.0, HEM - 2.0)], _SOLID)

    def detail(d) -> None:
        for k in range(3):
            K.line(d, [K.at(-6.0 - k * 1.0, TOP + 9.0), K.at(-10.4 - sway - k * 0.6, HEM + 5.0 - k * 3.0)], WING_DARK, 0.4)

    out.append((K.solid(("hopper_wings", sway), shape, WING, detail, outline=1.0, rim=0.0, shade=0.0), ctx.hip, "wings", ctx.lean))
    return out


X.layers["back"].append(_feelers)

# ---- How she holds herself -----------------------------------------------------

#: Her hands behind her back, as an officer stands.
X.set_rest(lean=-1.0, na=(-6.0, 20.0), fa=(-5.0, 20.0), nh="fist", fh="fist", nf=(-3.4, 0.0, 0.0), ff=(4.4, 0.0, 0.0))


@X.row
def idle(i: int, n: int):
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.3 + 0.3 * s), head=(0.3, 0.0, -2.0 + 2.0 * c), eyes="closed" if i == n - 2 else "open", mouth="smile" if c > 0.3 else "flat")


@X.row
def walk(i: int, n: int):
    # Quick, short steps, and a small hop in each.
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 7.0, 4.6)
    return P(hip=(0.4, -0.6 * abs(math.sin(ph))), lean=2.0, head=(0.2, 0.0, 1.5 * s), nf=nf, ff=ff, hem=(1.0 + abs(c), abs(c)))


@X.row
def talk(i: int, n: int):
    # She holds up a hand: the distance between finger and thumb is the lesson.
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.3 * s), lean=0.0, head=(0.4, 0.0, 2.0 * s), na=(12.0 + 1.5 * c, 0.0 - 3.0 * max(0.0, s)), nh="open", mouth=("open", "smile", "big")[i % 3],
             brows=1.0 if s > 0.3 else 0.0)


@X.row
def interact(i: int, n: int):
    reach = P(hip=(1.0, 1.0), lean=6.0, na=(20.0, 2.0), nh="point", mouth="o")
    return X.keys(shot(i, n), [(0.0, P()), (0.35, reach), (0.7, dict(reach, na=(20.0, 5.0))), (1.0, P())])


@X.row
def slash(i: int, n: int):
    # The baton: back over her shoulder, and down through.
    back = P(hip=(-1.0, 1.0), lean=-5.0, na=(-8.0, -12.0), nab=-1.0, nh="fist", mouth="flat", nf=(-5.0, 0.0, 0.0), ff=(5.0, 0.0, 0.0))
    through = P(hip=(2.5, 2.0), lean=10.0, head=(0.6, 0.0, 4.0), na=(22.0, 8.0), nh="fist", mouth="grit", nf=(-7.0, 0.0, 0.0), ff=(8.0, 0.0, 0.0), hem=(3.0, 2.0))
    return X.keys(shot(i, n), [(0.0, P()), (0.25, back), (0.45, through), (0.7, dict(through, na=(21.0, 11.0))), (1.0, P())])


@X.row
def taunt(i: int, n: int):
    # She shows the moth she found in the relay. It is in her hand, and it is why the word is "bug".
    show = P(lean=0.0, head=(0.5, 0.0, 6.0), na=(14.0, -2.0), nh="flat", eyes="open", mouth="smile")
    return X.keys(shot(i, n), [(0.0, P()), (0.25, show), (0.8, dict(show, na=(14.0, -3.0), mouth="big")), (1.0, P())])


_fall = X.poses["death"]


@X.row
def death(i: int, n: int):
    # As she goes over, her knees (which are behind her) are under her: that
    # frame is a little higher, so they are in the cell.
    pose = dict(X.full(_fall(i, n)))
    if i == 4:
        ox, oy = pose["off"]  # type: ignore[misc]
        pose["off"] = (ox, oy - 5.0)
    return pose


X.alias(hurt="hit")
X.rows = [("idle", 8, 140), ("walk", 8, 96), ("talk", 6, 112), ("interact", 6, 108), ("slash", 7, 84), ("taunt", 8, 92), ("hurt", 5, 92), ("death", 8, 112)]

# ---- From the front ------------------------------------------------------------

_FRONT_EYE = 3.0
_FRONT_FEELERS = [[(1.6 * sx, -14.0), (3.6 * sx, -19.0), (7.0 * sx, -22.4), (10.4 * sx, -22.0)] for sx in (-1.0, 1.0)]


def _front_jacket(d) -> None:
    """Her collar and tie, two rows of gold buttons, the ribbons over her
    heart, the hem of the jacket and the skirt under it."""
    K.poly(d, [K.at(-3.4, TOP - 1.0), K.at(3.4, TOP - 1.0), K.at(0.0, TOP + 7.0)], CAP)
    K.poly(d, [K.at(-1.0, TOP + 0.6), K.at(1.0, TOP + 0.6), K.at(0.7, TOP + 6.4), K.at(0.0, TOP + 7.6), K.at(-0.7, TOP + 6.2)], INK)
    K.line(d, [K.at(-3.4, TOP - 1.0), K.at(0.0, TOP + 7.0), K.at(3.4, TOP - 1.0)], NAVY_DARK, 0.6)
    for y in (-17.0, -12.6, -8.2):
        for x in (-2.2, 2.2):
            K.oval(d, K.at(x, y), 0.9, 0.9, GOLD, GOLD_DARK, 0.3)
    for k, colour in enumerate(((206, 70, 70, 255), GOLD, (86, 150, 220, 255))):
        K.poly(d, [K.at(2.4 + k * 1.6, -22.4), K.at(3.8 + k * 1.6, -22.4), K.at(3.8 + k * 1.6, -20.6), K.at(2.4 + k * 1.6, -20.6)], colour)
    K.line(d, [K.at(-9.0, -3.0), K.at(9.0, -3.0)], NAVY_DARK, 0.8)
    for x in (-3.0, 3.0):
        K.line(d, [K.at(x, -2.0), K.at(x * 1.3, HEM - 1.0)], NAVY_DARK, 0.6)


def _front_cap_shape(d) -> None:
    K.poly(d, [K.at(-10.4, -7.0), K.at(-11.0, -11.6), K.at(-5.0, -14.8), K.at(5.0, -14.8), K.at(11.0, -11.6), K.at(10.4, -7.0)], _SOLID)
    K.poly(d, [K.at(-7.4, -7.4), K.at(7.4, -7.4), K.at(8.0, -4.6), K.at(-8.0, -4.6)], _SOLID)
    for feeler in _FRONT_FEELERS:
        K.stroke(d, [K.at(x, y) for x, y in feeler], _SOLID, 1.5)


def _front_cap(d) -> None:
    K.poly(d, [K.at(-10.4, -7.0), K.at(-11.0, -11.6), K.at(-5.0, -14.8), K.at(5.0, -14.8), K.at(11.0, -11.6), K.at(10.4, -7.0)], CAP)
    K.poly(d, [K.at(-11.0, -9.6), K.at(11.0, -9.6), K.at(10.4, -6.8), K.at(-10.4, -6.8)], INK)
    K.line(d, [K.at(-10.8, -9.8), K.at(10.8, -9.8)], GOLD, 0.7)
    K.poly(d, [K.at(-7.4, -7.0), K.at(7.4, -7.0), K.at(8.0, -4.6), K.at(-8.0, -4.6)], INK)
    K.oval(d, K.at(0.0, -12.2), 2.0, 2.0, GOLD, GOLD_DARK, 0.4)
    K.oval(d, K.at(0.0, -12.2), 0.8, 0.8, CAP)


def _front_eyes_face(d) -> None:
    # Her eyes are large and dark, and her glasses are round.
    for sx in (-1.0, 1.0):
        cx, cy, r = 3.5 * sx, -0.4, _FRONT_EYE
        K.oval(d, K.at(cx, cy), r * 0.86, r, INK)
        K.oval(d, K.at(cx - r * 0.25, cy - r * 0.35), r * 0.26, r * 0.3, GREEN_PALE)
        K.oval(d, K.at(cx, cy), r + 0.4, r + 0.5, LENS, GOLD_DARK, 0.5)
        K.line(d, [K.at(2.0 * sx, 5.0), K.at(3.4 * sx, 7.4)], GREEN_DEEP, 0.4)
    K.line(d, [K.at(-0.5, -0.6), K.at(0.5, -0.6)], GOLD_DARK, 0.5)


def _front_lids(mode: str):
    if mode != "closed":
        return None

    def paint(d) -> None:
        for sx in (-1.0, 1.0):
            K.oval(d, K.at(3.5 * sx, -0.4), _FRONT_EYE * 0.86, _FRONT_EYE, GREEN_SHADE)
            K.line(d, [K.at(3.5 * sx - 2.4, 0.0), K.at(3.5 * sx + 2.4, 0.0)], GREEN_DEEP, 0.6)

    return K.piece(("hopper_front_lids",), paint)


X.front_torso = R.make_front_torso(K, ("hopper",), NAVY, NAVY_DARK, [(TOP, 3.2), (TOP + 3.6, 6.4), (TOP + 12.5, 7.6), (-10.0, 5.6), (0.0, 8.0), (HEM, 9.4)],
                                   shoulder=(4.8, -26.2, 3.8, 3.6), detail=_front_jacket)
X.front_head_layers = R.front_face(R.make_front_head(K, ("hopper",), GREEN, GREEN_DEEP, wide=7.4, jaw=5.2, chin=2.8, shape=_front_cap_shape, hair=_front_cap,
                                                    face=_front_eyes_face),
                                   _front_lids, None, R.make_front_mouth(K, ("hopper",), y=6.4, colour=(150, 60, 66, 255), lips=(170, 70, 80, 255), wide=0.6))
X.front_shoe = R.make_front_shoe(K, INK, (10, 10, 14, 255), BUILD.ankle_up, wide=0.8)
X.front_span = (5.8, 3.4)
R.add_front_rows(X)

# ---- What she shows ------------------------------------------------------------


def _baton():
    """Her baton, along +x from the hand that holds it: dark wood, with a
    gold cap at each end."""

    def shape(d) -> None:
        K.stroke(d, [K.at(-3.0, 0.0), K.at(17.0, 0.0)], _SOLID, 2.2)

    def detail(d) -> None:
        K.stroke(d, [K.at(-3.0, 0.0), K.at(-1.4, 0.0)], GOLD, 2.0)
        K.stroke(d, [K.at(15.4, 0.0), K.at(17.0, 0.0)], GOLD, 2.0)

    return K.solid(("baton",), shape, WOOD, detail, outline=0.9, rim=0.0, shade=0.3, shade_colour=WOOD_DARK)


def _wire():
    """A nanosecond: the length of wire that light goes in one."""

    def paint(d) -> None:
        pts = [K.at(x, 1.2 * math.sin(x * 0.7)) for x in [k * 0.5 for k in range(0, 25)]]
        K.line(d, pts, OUTLINE, 2.0)
        K.line(d, pts, COPPER, 0.9)

    return K.aligned(("wire",), paint)


def _moth(flap: int):
    def shape(d) -> None:
        K.oval(d, K.home, 1.0, 2.4, _SOLID)
        for sign in (-1.0, 1.0):
            K.poly(d, [K.at(0.0, -1.4), K.at(sign * (4.4 - flap), -3.0), K.at(sign * (4.0 - flap), 1.6), K.at(0.0, 1.4)], _SOLID)

    return K.solid(("moth", flap), shape, MOTH, None, outline=0.9, rim=0.0, shade=0.3, shade_colour=MOTH_DARK)


def _effects(ctx) -> List[Stamp]:
    out: List[Stamp] = []
    anim, i, u = ctx.anim, ctx.i, ctx.u
    grip = math.degrees(math.atan2(ctx.hand[1] - ctx.elbow[1], ctx.hand[0] - ctx.elbow[0]))
    if anim == "slash":
        if 0.15 <= u <= 0.85:
            out.append((_baton(), ctx.hand, "baton", grip - 30.0))
        if 0.4 <= u <= 0.65:
            out.append((R.swoosh(K, 22.0, -70, 30, 3.6, GOLD, GOLD_DARK), pin((ctx.shoulder[0] + 6.0, ctx.shoulder[1] + 6.0)), "cut", 0.0))
    elif anim == "talk":
        out.append((_wire(), pin((ctx.hand[0] + 1.0, ctx.hand[1] - 5.0)), "wire", 0.0))
    elif anim == "interact" and 0.35 <= u <= 0.7:
        out.append((R.tick(K, 3.6, GOLD, GOLD_DARK), (ctx.hand[0] + 12.0, ctx.hand[1] - 5.0), "tick", 0.0))
    elif anim == "taunt" and 0.2 <= u <= 0.9:
        out.append((_moth(i % 2), (ctx.hand[0] + 3.0, ctx.hand[1] - 5.0 - (2.0 if i % 2 else 0.0)), "moth", -10.0))
    return out


X.effects = _effects

ROWS = X.rows
FRAME_SIZE = X.frame
render_frame = X.render_frame
_render_frame = render_frame
render, main, render_canonical = R.entry_points(X, ACTOR_METADATA, DISPLAY_NAME)


def render_portraits(out_dir, **opts):
    """Her portraits are frames of this sheet."""
    del opts
    return X.portraits(out_dir, {
        "default": ("idle", (1,), 0, False),
        "talking": ("talk", tuple(range(6)), 112, True),
        "command": ("interact", (2, 3, 4), 140, True),
        "taunt": ("taunt", tuple(range(2, 7)), 110, True),
    }, view_width=38.0)


# ---- In the round (``_round_cast``) --------------------------------------------
#
# Her trunk and head in 3D come from the numbers of her own makers
# (``auto_trunk``, ``auto_head``); what they do not say is here, as data.
# Her rows do not use this.

from types import SimpleNamespace  # noqa: E402

import numpy as np  # noqa: E402

from . import _person_round as O  # noqa: E402
from . import _round_cast as C  # noqa: E402
from . import _round_wear as W  # noqa: E402


class _HopperBody(C.PersonBody):
    """Her body in the round: as any person's, but each knee is behind her,
    as a grasshopper's is."""

    def leg(self, name, hip, knee, ankle):
        knee, _ = O.two_bone(hip, ankle, self.thigh, self.shin, (0.0, 0.0, -1.0))
        return super().leg(name, hip, knee, ankle)


# Her head from the side, drawn as the cast draws a head in the numbers of a
# profile: the cap and its black peak, her feelers from under it, one large
# dark eye behind its round lens, the plate at the back of her head.

_SIDE_EYE = (6.4, -0.6)
_SIDE_FEELERS = [(2.6, -13.0), (0.6, -18.0), (-4.0, -21.6), (-9.6, -21.0)]


def _side_cap_shape(d) -> None:
    K.poly(d, [K.at(-9.6, -7.0), K.at(-10.6, -11.6), K.at(-5.0, -14.6), K.at(5.0, -14.6), K.at(10.0, -11.6), K.at(9.0, -7.0)], _SOLID)
    K.poly(d, [K.at(6.0, -7.4), K.at(13.6, -5.6), K.at(13.0, -4.2), K.at(5.0, -5.0)], _SOLID)
    K.stroke(d, [K.at(x, y) for x, y in _SIDE_FEELERS], _SOLID, 1.5)


def _side_cap(d) -> None:
    K.poly(d, [K.at(-20.0, -6.4), K.at(-1.4, -6.4), K.at(-2.6, 1.0), K.at(-5.0, 4.0), K.at(-20.0, 4.0)], GREEN_SHADE)
    K.poly(d, [K.at(-20.0, -30.0), K.at(20.0, -30.0), K.at(20.0, -7.2), K.at(-20.0, -7.2)], CAP)
    K.poly(d, [K.at(-10.0, -9.2), K.at(10.0, -9.2), K.at(10.0, -6.8), K.at(-10.0, -6.8)], INK)
    K.line(d, [K.at(-9.8, -9.4), K.at(9.8, -9.4)], GOLD, 0.7)
    K.poly(d, [K.at(4.0, -7.4), K.at(14.0, -5.4), K.at(13.0, -3.6), K.at(4.0, -5.2)], INK)
    K.poly(d, [K.at(-9.6, -12.0), K.at(-4.4, -14.2), K.at(-2.4, -10.4), K.at(-10.0, -9.6)], CAP_SHADE)
    K.oval(d, K.at(7.6, -11.4), 1.2, 2.2, GOLD, GOLD_DARK, 0.4)
    K.stroke(d, [K.at(x, y) for x, y in _SIDE_FEELERS], GREEN_SHADE, 1.3)


def _side_face(d) -> None:
    (cx, cy), r = _SIDE_EYE, 3.3
    K.oval(d, K.at(cx, cy), r * 0.82, r, INK)
    K.oval(d, K.at(cx - r * 0.25, cy - r * 0.35), r * 0.26, r * 0.3, GREEN_PALE)
    K.oval(d, K.at(cx, cy), r + 0.4, r + 0.5, LENS, GOLD_DARK, 0.5)
    K.line(d, [K.at(cx - 3.6, -0.9), K.at(-1.4, -1.6)], GOLD_DARK, 0.5)
    K.line(d, [K.at(5.2, 4.8), K.at(4.0, 6.8)], GREEN_DEEP, 0.4)
    K.line(d, [K.at(-0.4, 2.0), K.at(2.0, 6.0), K.at(5.0, 8.6)], GREEN_DEEP, 0.4)


_side_head = R.make_head(K, ("hopper_side",), GREEN, GREEN_SHADE, GREEN_DEEP, skull=(0.0, -2.4, 8.8, 8.6), jaw=(3.6, 4.0, 5.6, 6.6), nose=None, ear=None,
                         shape=_side_cap_shape, under=_side_cap, over=_side_face, far_shade=False)
_side_mouth = R.make_mouth(K, (8.0, 6.4), (150, 60, 66, 255), wide=0.5, lips=(170, 70, 80, 255))


def _side_lids(mode: str):
    if mode != "closed":
        return None

    def paint(d) -> None:
        (cx, cy), r = _SIDE_EYE, 3.3
        K.oval(d, K.at(cx, cy), r * 0.82, r, GREEN_SHADE)
        K.line(d, [K.at(cx - r * 0.8, cy + 0.4), K.at(cx + r * 0.8, cy + 0.4)], GREEN_DEEP, 0.6)

    return K.piece(("hopper_side_lids",), paint)


def _side_layers(pose):
    return [(_side_head(), "head"), (_side_lids(str(pose["eyes"])), "lids"), (_side_mouth(str(pose["mouth"])), "mouth")]


#: Her front head's numbers for ``auto_head``: its eyes are painted in the
#: head (and its lids have no numbers), so only the head and mouth count.
_FRONT_NUMBERS = SimpleNamespace(front_head_layers=SimpleNamespace(spec=SimpleNamespace(
    head=X.front_head_layers.spec.head, eyes=None, brows=None, mouth=X.front_head_layers.spec.mouth)))

#: Her cap: a white crown, wide and flat, its black band with the gold line
#: over it, the badge in front; the black peak is a part of its own (in
#: front only).
CAP_3D = W.Hat(
    crown=[O.Ring(-6.6, 0.0, 0.2, 8.4, 8.4), O.Ring(-9.6, 0.0, 0.2, 10.2, 10.0), O.Ring(-13.0, 0.0, 0.2, 10.6, 10.4), O.Ring(-14.6, 0.0, 0.2, 8.0, 7.8),
           O.Ring(-14.6, 0.0, 0.2, 0.0, 0.0)],
    brim=None, under=CAP_SHADE,
    garment=W.Garment(CAP, CAP_SHADE, [W.Band(-9.2, -6.4, INK), W.Band(-9.8, -9.2, GOLD), W.Dot(0.0, -11.4, 2.0, GOLD, GOLD_DARK), W.Shade(-0.4)], radius=10.0))


class _Peak:
    """The black peak of her cap: a loft round the front of her head only."""

    def piece(self, K, J, head):
        surface = O.loft([O.Ring(-6.8, 0.0, 0.4, 8.6, 8.6), O.Ring(-5.4, 0.0, 3.0, 9.6, 11.4)], O.flat(INK), cols=24, turns=(-62.0, 62.0)).moved(head)
        return O.Part("peak", [surface], base=INK, outline=1.0, shade=0.0, anchor=(head[0], head[1] - 6.0, head[2] + 10.0), lead=1.0)


#: Her feelers, from under her cap at the front, out, up and back.
FEELERS_3D = W.Antlers([[(s * 1.6, -13.0, 2.0), (s * 3.6, -18.0, 0.0), (s * 7.0, -21.4, -4.0), (s * 10.0, -21.0, -9.0)] for s in (-1.0, 1.0)], 1.3,
                       GREEN_SHADE, GREEN_DEEP, name="feelers", lead=0.5)
class _Feelers:
    """Her feelers in 3D, in the views no art of hers draws them: her own
    three-quarter view has them in its back layer, her front head and her
    head from the side in their cap."""

    def piece(self, K, J, head):
        drawn = FEELERS_3D.piece(K, J, head)
        draw = drawn.draw

        def only_where_not_drawn(view, far, at):
            turn = O.facing(view)
            if abs(turn) <= 10.0 or abs(turn - 45.0) <= 10.0 or abs(abs(turn) - 90.0) <= 10.0:
                return None
            return draw(view, far, at)

        drawn.draw = only_where_not_drawn
        return drawn


#: Her wings, folded down her back like the tails of a coat.
WINGS_3D = W.Cloak([O.Ring(TOP + 5.0, 0.0, -1.2, 5.0, 4.6), O.Ring(-20.0, 0.0, -1.6, 6.6, 6.0), O.Ring(0.0, 0.0, -2.4, 7.6, 7.0), O.Ring(HEM + 6.0, 0.0, -3.4, 8.0, 7.6)],
                   W.Garment((196, 232, 190, 255), WING_DARK, [W.Down(165.0, TOP + 9.0, HEM + 5.0, WING_DARK), W.Down(-165.0, TOP + 9.0, HEM + 5.0, WING_DARK),
                                                               W.Down(180.0, TOP + 9.0, HEM + 5.0, WING_DARK)], radius=7.0), turns=(150.0, 210.0))

ROUND = C.Round(
    DISPLAY_NAME, _HopperBody(X, back_layers=("back",), heads={"side": _side_layers}),
    C.Look(
        # Under her cap her head is a grasshopper's: green, no hair, and a
        # plate at the back of it; large dark eyes behind round glasses.
        C.auto_head(_FRONT_NUMBERS, _head, None, hair=lambda u, v: (np.abs(u) > 110.0) & (v < 4.0), hair_colour=GREEN_SHADE, hair_shade=GREEN_DEEP,
                    eye_size=2.6, ink=INK, glasses=O.Glasses("round", (3.4, 3.6), GOLD_DARK, LENS, 0.5)),
        # Her blue jacket: the white collar and the black tie, two rows of
        # gold buttons, the ribbons over her heart; the hem of the jacket and
        # the skirt under it.
        C.auto_trunk(X, [W.Neckline(TOP - 1.0, TOP + 7.0, 24.0, CAP), W.Strip(0.0, TOP + 0.6, TOP + 7.4, 1.0, INK, flare=-0.3),
                         W.Buttons(16.0, -17.0, -8.2, 3, 0.9, GOLD), W.Buttons(-16.0, -17.0, -8.2, 3, 0.9, GOLD),
                         W.Patch(17.0, 28.0, -22.4, -20.6, (206, 70, 70, 255)), W.Patch(28.0, 39.0, -22.4, -20.6, GOLD), W.Patch(39.0, 50.0, -22.4, -20.6, (86, 150, 220, 255)),
                         W.Across(-180.0, 180.0, -3.0, NAVY_DARK, width=0.4), W.Down(22.0, -2.0, HEM - 1.0, NAVY_DARK), W.Down(-22.0, -2.0, HEM - 1.0, NAVY_DARK),
                         W.Down(180.0, TOP + 4.0, -3.4, NAVY_DARK)]),
        head_pieces=[CAP_3D, _Peak()], back_pieces=[WINGS_3D], pieces=[("feelers", _Feelers())]),
    # Her hands behind her back, as an officer stands.
    C.Stance(hands={"r": C.Hand(at=(-2.0, -4.0, -9.0), pole=(-1.0, 0.3, -0.6), mode="fist"),
                    "l": C.Hand(at=(2.0, -4.6, -9.4), pole=(1.0, 0.3, -0.6), mode="fist")}, stagger=1.8))


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}

del mix

if __name__ == "__main__":
    raise SystemExit(main())
