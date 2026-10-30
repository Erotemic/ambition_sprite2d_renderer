"""Sprite generator for the Fascist Enforcer: the soldier of the Evil
dimension, and the man you punch in Godwin Castle.

The look (2026-10-15, a full redraw: Jon, "We are going to need to redo the
art for the fascist enforcer"): a tall, heavy-set grown man of 183 cm, seen
three quarters from the front, facing right, about five heads tall. A peaked
cap with a black visor and a high crown; a square jaw, small eyes under set
brows, a straight nose, a thin mouth; hair cut short under the cap. A
grey-green tunic with a stand collar, four pockets and a black belt with a
cross strap; breeches that flare at the thigh; black jackboots to the knee;
black gloves. On his near (left) arm, a red armband.

The emblem of the faction is invented, and it is not a real symbol: a black
cog of eight teeth with a hole in its middle, on a white disc, on red. It is
on the armband and the badge of the cap, and the banners of the castle carry
the same mark.

He fights with his fists and his boots: a jab and a cross (``slash``), an
overhand (``punch``), a front kick with his boot (``attack_side``), an
uppercut (``attack_up``) and a stomp (``attack_down``). He holds nothing (the
runtime held-item system is authoritative). There is no drop shadow.

He is a person of ``_person_rig``: the bones and the frame are shared; the
head, the uniform, the stance and every pose are his.
"""

from __future__ import annotations

import math
from typing import List

from ._ai_era_kit import OUTLINE, WHITE, RGBA, lerp, mix
from . import _evil_faction as F
from . import _person_rig as R
from ._person_rig import Build, Person, Stamp, loop, shot

TARGET_NAME = "fascist_enforcer"
TARGET_BASENAME = TARGET_NAME
DISPLAY_NAME = "Fascist Enforcer"

TRAITS = ["story", "humanoid", "enemy", "combatant", "authoritarian", "soldier", "brawler"]

ACTOR_METADATA = {
    "actor": {"character_id": "npc_fascist_enforcer", "display_name": DISPLAY_NAME},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": TRAITS,
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {"walk": True, "jump": True, "climb": None, "fly": None, "swim": None, "crawl": None, "use_lifts": True,
                      "door_access": ["public"]},
        "interactions": {"talk": True, "trade": None, "carry": None, "open_doors": ["public"]},
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
        "interaction.talk": {"animation": "taunt", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "action.melee.primary": {
            "animation": "slash",
            "events": [
                {"t": 0.42, "event": "hitbox_active_start", "source": "explicit.profile.combat_humanoid"},
                {"t": 0.62, "event": "hitbox_active_end", "source": "explicit.profile.combat_humanoid"},
            ],
        },
        "action.defense.block": {"animation": "block", "events": []},
        "combat.hurt": {"animation": "hit", "events": []},
        "combat.death": {"animation": "death", "events": []},
    },
    "authoring_description": (
        "The rank-and-file soldier of the Evil dimension's fascist faction: a big man in a "
        "grey-green uniform, peaked cap, black jackboots and a red armband with the faction's "
        "cog. He is drawn to be punched, as in Wolfenstein. The emblem is invented; no real "
        "symbol is used."
    ),
    "gameplay_description": (
        "A melee brawler: a jab and cross, an overhand, a front kick with his boot, an uppercut "
        "and a stomp. Weapons, when he has them, are held items and not part of the sheet."
    ),
    "dialogue_hints": {"barks": ["Papers.", "The order authorizes itself.", "If it is wrong, I will have obeyed correctly."]},
}

UNIFORM: RGBA = (98, 110, 92, 255)
UNIFORM_DARK: RGBA = (66, 76, 64, 255)
UNIFORM_LIGHT: RGBA = (136, 148, 126, 255)
BREECHES: RGBA = (90, 100, 86, 255)
BREECHES_DARK: RGBA = (60, 68, 58, 255)
COLLAR: RGBA = (48, 62, 52, 255)
BOOT: RGBA = (50, 46, 54, 255)
BOOT_DARK: RGBA = (30, 28, 34, 255)
BOOT_SHINE: RGBA = (88, 86, 100, 255)
SOLE: RGBA = (22, 20, 24, 255)
GLOVE: RGBA = (56, 52, 58, 255)
GLOVE_SHADE: RGBA = (42, 38, 46, 255)
GLOVE_DEEP: RGBA = (22, 20, 26, 255)
BELT: RGBA = (36, 30, 30, 255)
METAL: RGBA = (196, 194, 186, 255)
METAL_DARK: RGBA = (118, 116, 112, 255)
RED, DISC = F.RED, F.DISC
SKIN: RGBA = (230, 196, 172, 255)
SKIN_SHADE: RGBA = (204, 164, 144, 255)
SKIN_DEEP: RGBA = (150, 100, 88, 255)
HAIR: RGBA = (74, 58, 46, 255)
HAIR_DARK: RGBA = (48, 38, 32, 255)
INK: RGBA = (26, 22, 28, 255)
MOUTH: RGBA = (118, 58, 58, 255)
IMPACT: RGBA = (255, 238, 184, 255)
IMPACT_DARK: RGBA = (214, 122, 58, 255)
DUST: RGBA = (196, 186, 170, 255)
DUST_DARK: RGBA = (122, 112, 102, 255)

#: Tall and heavy-set, 183 cm. ``height`` is the top of his head: the body
#: the game moves is the man, and his cap stands about 9 pixels over it.
BUILD = Build(hip_up=53.0, thigh=25.8, shin=24.6, neck=(0.4, -38.5), upper=20.0, fore=19.0, near_shoulder=(-5.4, -34.0), far_shoulder=(6.4, -33.6),
              near_hip=(-3.8, 0.0), far_hip=(3.8, 0.0), head_up=(1.2, -13.6), throat=(0.0, 4.0), height=117.0, half_width=(13.5, 15.5))

X = Person(TARGET_NAME, BUILD, frame=(224, 184), ground=172.0, cx=112.0)
K = X.K
P = X.P
TOP = BUILD.neck[1] - 2.0


# ---- The tunic ---------------------------------------------------------------


def _pocket(d, x0: float, x1: float, y0: float, y1: float) -> None:
    """A patch pocket with its flap and button."""
    K.rrect(d, x0, y0, x1, y1, 0.0, UNIFORM_DARK)
    K.rrect(d, x0 + 0.5, y0 + 0.5, x1 - 0.5, y1 - 0.5, 0.0, UNIFORM)
    flap = [(x0 - 0.2, y0), (x1 + 0.2, y0), (x1 + 0.2, y0 + 2.2), ((x0 + x1) / 2.0, y0 + 3.4), (x0 - 0.2, y0 + 2.2)]
    K.poly(d, [K.at(x, y) for x, y in flap], UNIFORM_LIGHT)
    K.line(d, [K.at(x, y) for x, y in flap[2:] + flap[:1]], UNIFORM_DARK, 0.5)
    K.oval(d, K.at((x0 + x1) / 2.0, y0 + 2.2), 0.7, 0.7, METAL, OUTLINE, 0.3)


def _front(d, hb: float, hf: float) -> None:
    """The front of his tunic: the pockets, the buttons, the belt and the
    cross strap."""
    del hb
    _pocket(d, -1.6, 4.4, -29.0, -21.0)
    _pocket(d, -2.2, 4.8, -1.4, 9.0)
    # The placket, along his front edge.
    K.line(d, [K.at(6.2, TOP + 3.0), K.at(6.8, -20.0), K.at(6.8 + hf * 0.4, 12.0)], UNIFORM_DARK, 0.6)
    for y in (-33.0, -26.0, -19.0, -12.0, 1.0):
        K.oval(d, K.at(6.0 + (0.4 if y > -20.0 else 0.2), y), 0.8, 0.8, METAL, OUTLINE, 0.3)
    # The cross strap, from over his far shoulder to his belt behind.
    K.line(d, [K.at(5.0, TOP - 1.0), K.at(-2.0, -22.0), K.at(-8.6, -7.0)], BELT, 1.7)
    # The belt, and its buckle in front.
    K.poly(d, [K.at(-30.0, -8.6), K.at(30.0, -8.6), K.at(30.0, -4.0), K.at(-30.0, -4.0)], BELT)
    K.line(d, [K.at(-30.0, -8.0), K.at(30.0, -8.0)], mix(BELT, WHITE, 0.25), 0.4)
    K.rrect(d, 5.2, -9.0, 9.4, -3.6, 0.6, METAL, OUTLINE, 0.4)
    K.rrect(d, 6.3, -7.9, 8.3, -4.7, 0.3, METAL_DARK)
    # The hem.
    K.line(d, [K.at(-30.0, 11.0), K.at(30.0, 11.0)], UNIFORM_DARK, 0.5)


# His chest is broad and flat: shoulder and chest are one width, and the
# front tapers to the belt (``make_torso``).
X.torso = R.make_torso(K, ("enforcer",), UNIFORM, UNIFORM_DARK, back=(10.8, 11.0, 9.6, 10.6), front=(10.6, 11.0, 10.0, 11.0), hem_y=12.0, top=TOP,
                       shoulders=((-5.4, -34.0), (6.4, -33.6)), shoulder_r=(6.6, 6.0), neck=(-5.4, 5.4), shade_from=8.4, detail=_front)


def _collar():
    """His stand collar, from the base of his neck, with its dark tab."""

    def shape(d) -> None:
        K.poly(d, [K.at(-5.4, 1.4), K.at(-5.0, -3.4), K.at(0.0, -4.4), K.at(5.6, -4.0), K.at(6.4, 1.4)], WHITE)

    def detail(d) -> None:
        K.poly(d, [K.at(1.6, -3.6), K.at(5.6, -3.8), K.at(6.0, 0.6), K.at(1.8, 0.8)], COLLAR)
        K.line(d, [K.at(2.4, -1.4), K.at(5.4, -1.6)], METAL, 0.4)

    return K.solid(("collar",), shape, UNIFORM, detail, outline=1.1, rim=0.3, shade=0.3, shade_colour=UNIFORM_DARK)


X.collar = _collar
X.neck = R.make_neck(K, SKIN_SHADE, 7.4)

# ---- The head ----------------------------------------------------------------

NEAR_EYE = (2.0, -0.4)
FAR_EYE = (7.2, -0.6)


def _hair(d) -> None:
    # Cropped short. Under the cap only the back of it and a short sideburn
    # show; with the cap off, all of it does.
    K.poly(d, [K.at(-20.0, -30.0), K.at(20.0, -30.0), K.at(20.0, -8.6), K.at(7.0, -8.6), K.at(3.6, -7.4), K.at(-1.8, -7.2), K.at(-2.0, -1.8), K.at(-3.2, -1.6),
               K.at(-4.2, -3.0), K.at(-5.8, 1.0), K.at(-6.6, 5.6), K.at(-4.6, 7.6), K.at(-20.0, 9.0)], HAIR)
    K.line(d, [K.at(-5.0, -10.4), K.at(0.0, -11.2), K.at(5.0, -10.0)], mix(HAIR, WHITE, 0.2), 0.5)
    K.line(d, [K.at(-8.6, -4.0), K.at(-8.0, 2.0), K.at(-6.8, 6.0)], HAIR_DARK, 0.5)


def _face(d) -> None:
    # The visor's shade on his brow, his cheekbone and the line of his jaw.
    K.poly(d, [K.at(-2.0, -7.0), K.at(20.0, -7.0), K.at(20.0, -3.4), K.at(8.0, -3.0), K.at(0.0, -3.6)], mix(SKIN, SKIN_DEEP, 0.32))
    K.line(d, [K.at(5.2, 2.6), K.at(4.4, 5.8)], mix(SKIN, SKIN_DEEP, 0.45), 0.5)
    K.line(d, [K.at(-3.4, 4.6), K.at(-1.4, 9.6), K.at(2.4, 11.4)], mix(SKIN, SKIN_DEEP, 0.5), 0.6)


_head = R.make_head(K, ("enforcer",), SKIN, SKIN_SHADE, SKIN_DEEP, skull=(0.0, -2.6, 8.0, 9.2), jaw=(2.4, 4.4, 6.8, 7.2),
                    nose=((7.0, -1.8), (10.4, 3.2), (9.6, 4.8), (7.0, 5.2)), ear=(-4.8, 1.2, 2.2, 3.3), under=_hair, over=_face)
_eyes = R.make_eyes(K, NEAR_EYE, FAR_EYE, ink=INK, white=None, lid=SKIN_DEEP, size=0.9)
_brows = R.make_brows(K, [(-0.4, -2.4), (2.2, -3.0), (4.8, -2.4)], [(6.0, -2.6), (7.4, -3.0), (8.8, -2.6)], HAIR_DARK, 1.4)
_mouth = R.make_mouth(K, (5.2, 7.8), MOUTH, wide=0.9)


def _cap():
    """His peaked cap, from the middle of his head: the crown, high in
    front; the band with its red piping; the black visor; the badge."""

    def shape(d) -> None:
        K.poly(d, [K.at(-9.4, -5.6), K.at(-10.0, -10.0), K.at(-12.8, -13.0), K.at(-9.0, -16.4), K.at(0.0, -17.8), K.at(8.0, -21.0), K.at(13.4, -20.0),
                   K.at(12.6, -15.4), K.at(9.0, -10.8), K.at(9.4, -6.6)], WHITE)
        K.oval(d, K.at(0.0, -15.6), 12.0, 3.8, WHITE)
        K.poly(d, [K.at(2.6, -6.8), K.at(9.4, -7.0), K.at(14.2, -4.4), K.at(12.6, -3.2), K.at(4.4, -4.2)], WHITE)

    def detail(d) -> None:
        # The band.
        K.poly(d, [K.at(-20.0, -10.0), K.at(9.2, -10.8), K.at(9.8, -6.2), K.at(-20.0, -5.0)], COLLAR)
        K.line(d, [K.at(-20.0, -10.2), K.at(9.2, -11.0)], RED, 0.7)
        # The top of the crown, lit, and its piping.
        K.line(d, [K.at(-12.2, -13.2), K.at(-8.6, -16.2), K.at(0.0, -17.4), K.at(8.0, -20.4), K.at(12.8, -19.6)], RED, 0.7)
        K.line(d, [K.at(-6.0, -14.8), K.at(2.0, -15.8), K.at(9.0, -18.4)], UNIFORM_LIGHT, 0.6)
        # The visor.
        K.poly(d, [K.at(2.6, -6.8), K.at(9.4, -7.0), K.at(14.2, -4.4), K.at(12.6, -3.2), K.at(4.4, -4.2)], BOOT)
        K.line(d, [K.at(5.0, -5.8), K.at(9.6, -6.0), K.at(12.8, -4.4)], BOOT_SHINE, 0.5)
        # The badge: the faction's cog on a white disc.
        K.oval(d, K.at(7.0, -14.6), 2.8, 2.8, OUTLINE)
        K.oval(d, K.at(7.0, -14.6), 2.4, 2.4, DISC)
        F.cog(K, d, K.at(7.0, -14.6), 1.9)

    return K.solid(("cap",), shape, UNIFORM, detail, outline=1.2, rim=0.3, shade=0.35, shade_colour=UNIFORM_DARK)


X.set_rest(cap=1.0)


def _head_layers(pose):
    out = [(_head(), "head"), (_eyes(str(pose["eyes"])), "eyes"), (_brows(R.brow_mood(pose)), "brows"), (_mouth(str(pose["mouth"])), "mouth")]
    if float(pose["cap"]) >= 0.5:
        out.append((_cap(), "cap"))
    return out


X.head_layers = _head_layers

# ---- The limbs ---------------------------------------------------------------

#: The part of his upper arm the armband is on.
BAND = (0.2, 0.46)
def _upper_arm(near: bool):
    return [(0.0, 1.0, 8.6, 7.4, UNIFORM if near else UNIFORM_DARK)]


X.upper_arm = _upper_arm
X.forearm = lambda near: [(0.0, 1.0, 7.4, 6.2, UNIFORM if near else UNIFORM_DARK)]
# Breeches: they flare out at the thigh.
X.thigh = lambda near: [(0.0, 0.5, 9.6, 11.0, BREECHES if near else BREECHES_DARK), (0.5, 1.0, 11.0, 7.4, BREECHES if near else BREECHES_DARK)]
# Jackboots to just under the knee, with a line of shine down the shaft.
X.shin = lambda near: [(0.0, 0.14, 7.4, 7.0, BREECHES if near else BREECHES_DARK), (0.12, 1.0, 8.4, 7.0, BOOT if near else BOOT_DARK),
                       (0.2, 0.9, 1.6, 1.2, BOOT_SHINE if near else BOOT)]
X.hand = R.make_hand(K, GLOVE, GLOVE_SHADE, GLOVE_DEEP, UNIFORM, UNIFORM_DARK, size=1.2)
X.shoe = R.make_shoe(K, BOOT, BOOT_DARK, BUILD.ankle_up, long=1.12, sole=SOLE, heel=0.8)


def _armband(ctx) -> List[Stamp]:
    """The band and its emblem, on the near arm. They turn with the arm."""
    if ctx.pose["arm"] == "under":
        return []
    t = (BAND[0] + BAND[1]) / 2.0
    at = (lerp(ctx.shoulder[0], ctx.elbow[0], t), lerp(ctx.shoulder[1], ctx.elbow[1], t))
    turn = math.degrees(math.atan2(ctx.elbow[1] - ctx.shoulder[1], ctx.elbow[0] - ctx.shoulder[0]))
    return [(F.band(K, lerp(8.6, 7.4, t) + 0.8), at, "armband", turn), (F.emblem(K, 2.3), at, "armband_emblem", 0.0)]


X.layers["front"].append(_armband)

# ---- How he stands -----------------------------------------------------------

# Square on his feet, his chest out, his fists closed at his sides and a
# little in front of him.
X.set_rest(lean=1.0, na=(3.0, 24.6), fa=(4.6, 24.2), nh="fist", fh="fist", nf=(-5.0, 0.0, 0.0), ff=(6.0, 0.0, 0.0), mouth="flat", brows=-1.0)


@X.row
def idle(i: int, n: int):
    # He breathes, and he looks down his nose at you.
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.5 + 0.5 * s), lean=1.0 + 0.6 * s, head=(0.2, -0.2 * s, -3.0 + 0.8 * c), na=(3.0, 24.6 - 0.6 * s), fa=(4.6, 24.2 - 0.6 * s))


@X.row
def walk(i: int, n: int):
    # A heavy, even march: the boots come down flat, the fists swing.
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 9.0, 5.0)
    swing = 9.0 * c
    return P(hip=(0.6, 1.1 * abs(math.cos(ph))), lean=3.0, head=(0.2, 0.0, -2.0 + 1.0 * s), nf=nf, ff=ff, hem=(1.0 + abs(c), 0.6 + abs(c)),
             na=(3.0 - swing, 24.0 - 1.4 * abs(c)), fa=(4.6 + swing, 23.6 - 1.4 * abs(c)))


@X.row
def run(i: int, n: int):
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 13.0, 10.0, 0.0)
    return P(hip=(2.0, 1.6 + 1.8 * math.cos(2.0 * ph)), lean=15.0, head=(0.6, 0.0, -9.0), na=(-1.0 - 11.0 * c, 15.0 + 2.0 * c), fa=(3.0 + 11.0 * c, 15.0 - 2.0 * c),
             nf=nf, ff=ff, mouth="grit", hem=(5.0, 1.0))


#: His shoulder first, low, at you.
CHARGE = P(hip=(2.0, 7.0), lean=28.0, head=(1.0, 0.0, -24.0), na=(9.0, 10.0), fa=(-14.0, 14.0), nf=(-13.0, -5.0, 36.0), ff=(9.0, 0.0, 0.0), mouth="grit",
           hem=(7.0, 0.0))


@X.row
def dash_startup(i: int, n: int):
    back = P(hip=(-3.0, 5.0), lean=-6.0, na=(8.0, 14.0), fa=(10.0, 13.0), nf=(-7.0, 0.0, 0.0), ff=(8.0, 0.0, -10.0))
    return X.keys(shot(i, n), [(0.0, back), (1.0, CHARGE)])


@X.row
def dash(i: int, n: int):
    _, s, _c = loop(i, n)
    return dict(CHARGE, hip=(2.0, 7.0 + 0.8 * s), nf=(-13.0 - s, -5.0 - s, 36.0))


#: He goes up with his knees up and his fists by his chest.
RISE = P(hip=(0.0, -2.0), lean=4.0, head=(0.0, 0.0, -6.0), na=(8.0, 6.0), fa=(10.0, 4.0), nf=(-3.0, -12.0, 26.0), ff=(7.0, -16.0, 10.0), mouth="grit",
         hem=(1.0, 2.0))
APEX = P(hip=(0.0, -2.0), lean=2.0, head=(0.0, 0.0, -2.0), na=(10.0, 8.0), fa=(12.0, 6.0), nf=(-4.0, -9.0, 20.0), ff=(8.0, -12.0, 6.0), hem=(2.0, 3.0))
FALL = P(hip=(0.0, -3.0), lean=-4.0, head=(0.0, 0.0, 4.0), na=(-12.0, 4.0), nab=-1.0, fa=(16.0, 2.0), nf=(-7.0, -4.0, 22.0), ff=(7.0, -8.0, 8.0),
         eyes="wide", mouth="grit", hem=(4.0, 4.0))


@X.row
def jump(i: int, n: int):
    wind = P(hip=(-1.0, 11.0), lean=14.0, head=(0.0, 0.0, -4.0), na=(-12.0, 16.0), fa=(-8.0, 18.0), nf=(-6.0, 0.0, 0.0), ff=(7.0, 0.0, 0.0))
    return X.keys(shot(i, n), [(0.0, wind), (0.3, RISE), (0.6, RISE), (1.0, APEX)])


@X.row
def fall(i: int, n: int):
    _, s, c = loop(i, n)
    return dict(FALL, na=(-12.0 + 2.0 * s, 4.0 - 2.0 * c), fa=(16.0 - 2.0 * s, 2.0 + 2.0 * c), nf=(-7.0, -4.0 + 1.5 * s, 22.0), ff=(7.0, -8.0 - 1.5 * s, 8.0))


LANDED = P(hip=(0.0, 17.0), lean=24.0, head=(2.0, 2.0, 4.0), na=(14.0, 20.0), fa=(17.0, 18.0), nf=(-9.0, 0.0, 0.0), ff=(9.0, 0.0, 0.0), mouth="grit",
           hem=(4.0, 3.0))
HALF_UP = P(hip=(0.0, 7.0), lean=10.0, na=(7.0, 21.0), fa=(9.0, 20.0), nf=(-6.0, 0.0, 0.0), ff=(7.0, 0.0, 0.0), hem=(1.0, 2.0))


@X.row
def land_hard(i: int, n: int):
    return X.keys(shot(i, n), [(0.0, FALL), (0.2, LANDED), (0.6, LANDED), (1.0, HALF_UP)])


#: Low, his fists up.
LOW = P(hip=(-1.5, 15.0), lean=16.0, head=(1.0, 0.0, -12.0), na=(10.0, 8.0), fa=(12.0, 5.0), nf=(-8.0, 0.0, 0.0), ff=(9.0, 0.0, 0.0), hem=(2.0, 3.0))


@X.row
def crouch(i: int, n: int):
    _, s, _c = loop(i, n)
    return dict(LOW, hip=(-1.5, 15.0 + 0.5 * s))


#: A boxer's guard: the lead fist at his chin, the rear fist at his cheek,
#: the elbows down.
GUARD = P(hip=(-1.0, 2.5), lean=3.0, head=(0.4, 0.4, 4.0), na=(11.0, 4.0), fa=(9.0, -1.0), nf=(-8.0, 0.0, 0.0), ff=(8.0, 0.0, 0.0), mouth="grit")


@X.row
def block(i: int, n: int):
    # Both forearms up in front of his face.
    _, s, _c = loop(i, n)
    return P(hip=(-2.0, 4.0 + 0.4 * s), lean=-4.0, head=(-0.6, 0.6, 8.0), na=(10.0, -4.0), fa=(9.0, -8.0), nf=(-8.0, 0.0, 0.0), ff=(8.0, 0.0, 0.0),
             eyes="wince", mouth="grit")


STRUCK = P(hip=(-4.0, 2.0), lean=-20.0, head=(-2.0, 0.0, -14.0), na=(6.0, 18.0), fa=(14.0, 10.0), nh="open", fh="open", nf=(-8.0, 0.0, 0.0),
           ff=(8.0, -5.0, -22.0), eyes="wince", mouth="big", brows=1.0, off=(-3.0, 0.0), hem=(0.0, 5.0))


@X.row
def hit(i: int, n: int):
    back = P(hip=(-2.0, 2.0), lean=-6.0, na=(5.0, 22.0), fa=(8.0, 21.0), eyes="wince", mouth="grit")
    return X.keys(shot(i, n), [(0.0, P(lean=-4.0, eyes="wide", mouth="o")), (0.25, STRUCK), (0.6, STRUCK), (1.0, back)])


#: On his back, his head behind and his boots up.
SUPINE = P(rot=-90.0, hip=(-2.0, 25.5), off=(13.0, 0.0), head=(0.0, 0.0, 0.0), na=(5.0, 14.0), fa=(2.0, 12.0), nh="open", fh="open",
           nf=(-4.5, 25.0, 0.0), ff=(4.5, 25.0, -10.0), eyes="closed", mouth="o", brows=0.0)


@X.row
def death(i: int, n: int):
    # The punch lifts him; his knees go; he falls flat on his back, and his
    # cap comes off.
    sag = P(hip=(-5.0, 13.0), lean=-18.0, head=(-2.0, 0.0, -10.0), na=(8.0, 18.0), fa=(13.0, 14.0), nh="open", fh="open", nf=(-4.0, 0.0, 0.0),
            ff=(10.0, 0.0, -10.0), eyes="wince", mouth="o", brows=1.0, off=(-3.0, 0.0), hem=(0.0, 3.0), cap=0.0)
    # Half way down he is in the air: his boots stay over the floor. His cap
    # stays off to the end: it lies on the floor (``lost_cap``), and the pose
    # he lands in is shared with rows that keep it on.
    down = dict(SUPINE, cap=0.0)
    toppling = X.blend(sag, down, 0.5)
    toppling = dict(toppling, off=(toppling["off"][0], toppling["off"][1] - 6.0), cap=0.0)
    return X.keys(shot(i, n), [(0.0, dict(STRUCK, cap=0.0)), (0.3, sag), (0.46, toppling), (0.62, down), (1.0, down)])


@X.row
def interact(i: int, n: int):
    # "Papers." His hand out, palm up.
    ask = P(hip=(1.0, 1.0), lean=6.0, head=(0.6, 0.0, 2.0), na=(18.0, 13.0), nh="open", mouth="open")
    return X.keys(shot(i, n), [(0.0, P()), (0.35, ask), (0.7, dict(ask, na=(18.0, 14.0), mouth="flat")), (1.0, P())])


@X.row
def taunt(i: int, n: int):
    # He beats his fist into his palm, twice.
    ready = P(hip=(0.0, 1.0), lean=4.0, head=(0.4, 0.0, 3.0), na=(13.0, 2.0), fa=(14.0, 10.0), fh="open", mouth="grit")
    hit_ = dict(ready, na=(14.0, 9.0), head=(0.4, 0.4, 6.0))
    return X.keys(shot(i, n), [(0.0, P()), (0.2, ready), (0.35, hit_), (0.5, ready), (0.68, hit_), (0.85, hit_), (1.0, P())])


# ---- His attacks -------------------------------------------------------------

#: The lead fist straight out.
JAB = dict(GUARD, hip=(2.0, 3.0), lean=9.0, na=(26.6, -1.0), fa=(10.0, -2.0), ff=(9.0, 0.0, 0.0), mouth="open")
#: The rear fist straight out, his weight behind it.
CROSS = dict(GUARD, hip=(5.0, 4.0), lean=16.0, head=(1.0, 0.0, 2.0), na=(7.0, 7.0), fa=(25.6, -2.0), nf=(-9.0, 0.0, 14.0), ff=(11.0, 0.0, 0.0),
             mouth="big", hem=(5.0, 1.0))


@X.row
def slash(i: int, n: int):
    # The one-two: a jab, back to guard, and the cross.
    return X.keys(shot(i, n), [(0.0, GUARD), (0.12, JAB), (0.25, JAB), (0.38, GUARD), (0.5, CROSS), (0.72, CROSS), (1.0, GUARD)])


@X.row
def punch(i: int, n: int):
    # An overhand: back and up, and down onto you.
    wind = dict(GUARD, hip=(-3.0, 2.0), lean=-9.0, head=(0.0, 0.0, -3.0), na=(-12.0, -8.0), nab=-1.0, fa=(10.0, 2.0))
    over = dict(GUARD, hip=(5.0, 6.0), lean=22.0, head=(1.0, 1.0, 6.0), na=(24.0, 9.0), fa=(-6.0, 14.0), nf=(-10.0, 0.0, 14.0), ff=(12.0, 0.0, 0.0),
                mouth="big", hem=(6.0, 1.0))
    return X.keys(shot(i, n), [(0.0, GUARD), (0.3, wind), (0.5, over), (0.75, over), (1.0, GUARD)])


@X.row
def attack_side(i: int, n: int):
    # A front kick with his boot: knee up, the boot straight out, sole first.
    chamber = dict(GUARD, hip=(-1.0, 0.0), lean=-6.0, leg="over", nf=(9.0, -22.0, -20.0), ff=(-2.0, 0.0, 0.0))
    kick = dict(GUARD, hip=(-3.0, 0.0), lean=-15.0, head=(0.0, 0.0, -6.0), leg="over", nf=(29.0, -29.0, -78.0), ff=(-4.0, 0.0, 0.0), na=(9.0, 8.0),
                fa=(4.0, 8.0), mouth="big", hem=(0.0, 4.0))
    return X.keys(shot(i, n), [(0.0, GUARD), (0.25, chamber), (0.45, kick), (0.72, kick), (0.86, chamber), (1.0, GUARD)])


@X.row
def attack_up(i: int, n: int):
    # The uppercut: down, and up through you.
    dip = dict(GUARD, hip=(0.0, 9.0), lean=12.0, na=(7.0, 15.0), head=(1.0, 0.0, -2.0))
    up = dict(GUARD, hip=(2.0, -1.0), lean=-6.0, head=(0.0, 0.0, -12.0), na=(13.0, -13.0), fa=(-4.0, 12.0), nf=(-7.0, 0.0, 10.0), ff=(8.0, -1.0, 12.0),
              mouth="big")
    return X.keys(shot(i, n), [(0.0, GUARD), (0.25, dip), (0.45, up), (0.75, up), (1.0, GUARD)])


@X.row
def attack_down(i: int, n: int):
    # The stomp: knee high, and the boot down hard in front of him.
    lift = dict(GUARD, hip=(-1.0, -1.0), lean=-5.0, leg="over", nf=(9.0, -24.0, -6.0), ff=(-3.0, 0.0, 0.0), head=(0.0, 0.0, 6.0))
    stomp = dict(GUARD, hip=(3.0, 6.0), lean=14.0, head=(1.0, 1.0, 12.0), leg="over", nf=(15.0, 0.0, 0.0), ff=(-5.0, 0.0, 6.0), na=(12.0, 10.0),
                 fa=(9.0, 8.0), mouth="big", hem=(4.0, 2.0))
    return X.keys(shot(i, n), [(0.0, GUARD), (0.3, lift), (0.5, stomp), (0.8, stomp), (1.0, GUARD)])


AIR = P(hip=(0.0, -3.0), nf=(-4.0, -8.0, 20.0), ff=(6.0, -12.0, 8.0), na=(10.0, 6.0), fa=(12.0, 3.0), hem=(3.0, 2.0))


@X.row
def air_forward(i: int, n: int):
    # A flying kick, the boot first.
    kick = dict(AIR, lean=-16.0, hip=(-1.0, -3.0), leg="over", nf=(30.0, -34.0, -80.0), ff=(-3.0, -16.0, 36.0), na=(-6.0, 10.0), fa=(10.0, 8.0),
                mouth="big", hem=(1.0, 5.0))
    return X.keys(shot(i, n), [(0.0, AIR), (0.35, kick), (0.7, kick), (1.0, AIR)])


@X.row
def air_down(i: int, n: int):
    # Both boots down, onto you.
    dive = dict(AIR, hip=(0.0, 0.0), off=(0.0, -12.0), nf=(-1.0, 0.0, 30.0), ff=(4.0, 0.0, 24.0), na=(-15.0, 3.0), nab=-1.0, fa=(17.0, 1.0), nh="fist",
                mouth="big", hem=(4.0, 4.0))
    return X.keys(shot(i, n), [(0.0, AIR), (0.3, dive), (0.8, dive), (1.0, AIR)])


@X.row
def notice(i: int, n: int):
    # He starts, his brows go up; then he squares up, his fists up.
    startled = P(hip=(-1.0, -1.0), lean=-6.0, head=(-0.6, -0.6, -8.0), na=(9.0, 14.0), fa=(10.0, 12.0), eyes="wide", mouth="o", brows=1.0)
    return X.keys(shot(i, n), [(0.0, P()), (0.2, startled, "snap"), (0.5, startled), (0.8, GUARD), (1.0, GUARD)])


@X.row
def windup(i: int, n: int):
    # The front kick made ready: his knee up, his weight back.
    _, s, _c = loop(i, n)
    return dict(GUARD, hip=(-1.0, 0.0), lean=-6.0 - 1.0 * s, leg="over", nf=(9.0, -22.0 - 0.8 * s, -20.0), ff=(-2.0, 0.0, 0.0))


X.rows = [("idle", 8, 150), ("walk", 8, 105), ("notice", 8, 85), ("windup", 4, 90), ("run", 8, 78), ("dash_startup", 4, 50), ("dash", 6, 65), ("jump", 6, 95), ("fall", 6, 95),
          ("land_hard", 6, 80), ("crouch", 6, 110), ("block", 6, 90), ("hit", 5, 90), ("death", 8, 115), ("interact", 8, 92), ("taunt", 10, 90),
          ("slash", 9, 76), ("punch", 8, 80), ("attack_side", 8, 75), ("attack_up", 8, 75), ("attack_down", 8, 75), ("air_forward", 7, 65),
          ("air_down", 7, 70)]

# ---- What his blows do -------------------------------------------------------


def _between(u: float, a: float, b: float) -> bool:
    return a <= u <= b


def _effects(ctx) -> List[Stamp]:
    out: List[Stamp] = []
    anim, u = ctx.anim, ctx.u
    if anim == "slash":
        if _between(u, 0.1, 0.26):
            out.append((R.burst(K, 7.0, IMPACT, IMPACT_DARK, 7), (ctx.hand[0] + 8.0, ctx.hand[1]), "jab_hit", 0.0))
        elif _between(u, 0.45, 0.7):
            out.append((R.burst(K, 10.0 if u < 0.6 else 7.0, IMPACT, IMPACT_DARK, 8), (ctx.far_hand[0] + 9.0, ctx.far_hand[1]), "cross_hit", 0.0))
    elif anim == "punch" and _between(u, 0.45, 0.72):
        out.append((R.burst(K, 11.0 if u < 0.6 else 8.0, IMPACT, IMPACT_DARK, 8), (ctx.hand[0] + 9.0, ctx.hand[1] + 2.0), "overhand_hit", 0.0))
    elif anim in ("attack_side", "air_forward") and _between(u, 0.4, 0.7):
        out.append((R.burst(K, 10.0, IMPACT, IMPACT_DARK, 8), (ctx.foot[0] + 12.0, ctx.foot[1] - 2.0), "kick_hit", 0.0))
    elif anim == "attack_up" and _between(u, 0.4, 0.7):
        out.append((R.burst(K, 9.0, IMPACT, IMPACT_DARK, 8), (ctx.hand[0] + 5.0, ctx.hand[1] - 8.0), "uppercut_hit", 0.0))
    elif anim == "attack_down" and _between(u, 0.45, 0.8):
        late = u > 0.62
        at = (ctx.foot[0] + 4.0, ctx.ground - 3.0)
        out.append((R.dust(K, 3.0 if late else 4.2, DUST, DUST_DARK), (at[0] + (13.0 if late else 9.0), at[1] - 2.0), "dust_ahead", 0.0))
        out.append((R.dust(K, 2.6 if late else 3.6, DUST, DUST_DARK), (at[0] - (12.0 if late else 8.0), at[1] - 1.0), "dust_behind", 0.0))
    elif anim == "taunt" and (_between(u, 0.33, 0.4) or _between(u, 0.66, 0.74)):
        out.append((R.burst(K, 6.0, IMPACT, IMPACT_DARK, 6), (ctx.hand[0] + 4.0, ctx.hand[1] - 4.0), "smack", 0.0))
    elif anim == "hit" and _between(u, 0.0, 0.5):
        out.append((R.burst(K, 9.0, IMPACT, IMPACT_DARK, 8), (ctx.head[0] + 8.0, ctx.head[1]), "struck", 0.0))
    elif anim == "death":
        # His cap goes up off his head, turns over behind him, and lies on
        # the ground past his head.
        t = min(1.0, u / 0.65)
        x = X.cx + lerp(-8.0, -80.0, t)
        y = lerp(X.ground - 108.0, X.ground - 7.0, t) - 30.0 * math.sin(math.pi * t)
        out.append((_cap(), (x, y), "lost_cap", lerp(-10.0, -340.0, t)))
    return out


X.effects = _effects

# ---- From the front ----------------------------------------------------------
#
# The row he turns through. He stands square to you, his fists at his sides.

X.front_span = (11.6, 5.2)


def _front_tunic(d) -> None:
    for sx in (-1.0, 1.0):
        x0, x1 = (1.6, 7.4) if sx > 0 else (-7.4, -1.6)
        _pocket(d, x0, x1, -29.0, -21.0)
        _pocket(d, x0, x1, -1.4, 9.0)
    K.line(d, [K.at(0.0, TOP + 3.0), K.at(0.0, 12.0)], UNIFORM_DARK, 0.6)
    for y in (-33.0, -26.0, -19.0, -12.0, 1.0):
        K.oval(d, K.at(0.0, y), 0.8, 0.8, METAL, OUTLINE, 0.3)
    K.line(d, [K.at(-8.0, TOP + 1.0), K.at(-1.0, -24.0), K.at(8.4, -8.0)], BELT, 1.7)
    K.poly(d, [K.at(-30.0, -8.6), K.at(30.0, -8.6), K.at(30.0, -4.0), K.at(-30.0, -4.0)], BELT)
    K.rrect(d, -2.2, -9.0, 2.2, -3.6, 0.6, METAL, OUTLINE, 0.4)
    K.rrect(d, -1.0, -7.9, 1.0, -4.7, 0.3, METAL_DARK)
    K.line(d, [K.at(-30.0, 11.0), K.at(30.0, 11.0)], UNIFORM_DARK, 0.5)
    # His collar, closed at his throat, and its two tabs.
    K.poly(d, [K.at(-5.6, TOP - 1.0), K.at(5.6, TOP - 1.0), K.at(6.2, TOP + 3.4), K.at(-6.2, TOP + 3.4)], UNIFORM_LIGHT)
    for sx in (-1.0, 1.0):
        K.poly(d, [K.at(1.0 * sx, TOP), K.at(5.4 * sx, TOP), K.at(5.8 * sx, TOP + 3.0), K.at(1.2 * sx, TOP + 3.0)], COLLAR)


X.front_torso = R.make_front_torso(K, ("enforcer",), UNIFORM, UNIFORM_DARK, [(TOP - 0.4, 6.2), (TOP + 4.0, 12.6), (-24.0, 12.2), (-8.0, 10.8), (2.0, 11.4),
                                                                           (12.0, 11.8)], shoulder=(11.4, -34.4, 6.2, 6.2), detail=_front_tunic)


def _front_hair(d) -> None:
    for sx in (-1.0, 1.0):
        K.poly(d, [K.at(6.0 * sx, -7.0), K.at(9.0 * sx, -7.0), K.at(8.8 * sx, -1.6), K.at(6.8 * sx, -2.0)], HAIR)
    K.poly(d, [K.at(-20.0, -7.0), K.at(20.0, -7.0), K.at(20.0, -3.2), K.at(-20.0, -3.2)], mix(SKIN, SKIN_DEEP, 0.32))


def _front_face(d) -> None:
    K.line(d, [K.at(-0.4, -1.4), K.at(-1.4, 4.0), K.at(0.0, 5.0), K.at(1.4, 4.0)], SKIN_DEEP, 0.7)
    K.line(d, [K.at(-3.0, 12.0), K.at(0.0, 12.8), K.at(3.0, 12.0)], mix(SKIN, SKIN_DEEP, 0.4), 0.5)


def _front_cap():
    def shape(d) -> None:
        K.oval(d, K.at(0.0, -15.4), 12.6, 5.0, WHITE)
        K.poly(d, [K.at(-9.6, -15.0), K.at(9.6, -15.0), K.at(9.2, -6.0), K.at(-9.2, -6.0)], WHITE)
        K.poly(d, [K.at(-8.6, -6.6), K.at(8.6, -6.6), K.at(7.4, -3.0), K.at(-7.4, -3.0)], WHITE)

    def detail(d) -> None:
        K.poly(d, [K.at(-20.0, -10.6), K.at(20.0, -10.6), K.at(20.0, -6.0), K.at(-20.0, -6.0)], COLLAR)
        K.line(d, [K.at(-20.0, -10.8), K.at(20.0, -10.8)], RED, 0.7)
        K.line(d, [K.at(-11.0, -17.4), K.at(0.0, -20.0), K.at(11.0, -17.4)], RED, 0.7)
        K.poly(d, [K.at(-8.6, -6.6), K.at(8.6, -6.6), K.at(7.4, -3.0), K.at(-7.4, -3.0)], BOOT)
        K.line(d, [K.at(-6.0, -5.6), K.at(6.0, -5.6)], BOOT_SHINE, 0.5)
        K.oval(d, K.at(0.0, -14.8), 2.9, 2.9, OUTLINE)
        K.oval(d, K.at(0.0, -14.8), 2.5, 2.5, DISC)
        F.cog(K, d, K.at(0.0, -14.8), 2.0)

    return K.solid(("front_cap",), shape, UNIFORM, detail, outline=1.2, rim=0.3, shade=0.35, shade_colour=UNIFORM_DARK)


_front_head = R.make_front_head(K, ("enforcer",), SKIN, SKIN_DEEP, wide=8.2, jaw=7.0, chin=4.6, ears=SKIN, hair=_front_hair, face=_front_face)
X.front_head_layers = R.front_face(_front_head, R.make_front_eyes(K, ("enforcer",), white=None, ink=INK, spread=3.4, y=-0.4, size=0.9),
                                   R.make_front_brows(K, ("enforcer",), HAIR_DARK, spread=3.4, y=-2.6, width=1.4),
                                   R.make_front_mouth(K, ("enforcer",), y=8.6, colour=MOUTH, wide=0.85), extra=[(_front_cap, "cap")])
X.front_shoe = R.make_front_shoe(K, BOOT, BOOT_DARK, BUILD.ankle_up, wide=1.05)


def _front_effects(ctx) -> List[Stamp]:
    """The band and its emblem, on his left arm: the right of the picture."""
    b = X.b
    shoulder = (ctx.hip[0] + X.front_span[0], ctx.hip[1] + b.neck[1] + 4.6)
    hand = ctx.right_hand
    t = (BAND[0] + BAND[1]) / 2.0 * b.upper / (b.upper + b.fore)
    at = (lerp(shoulder[0], hand[0], t), lerp(shoulder[1], hand[1], t))
    return [(F.band(K, 8.4), at, "front_armband", math.degrees(math.atan2(hand[1] - shoulder[1], hand[0] - shoulder[0]))),
            (F.emblem(K, 2.3), at, "front_armband_emblem", 0.0)]


X.front_effects = _front_effects


@X.front_row
def front(i: int, n: int):
    _, s, _c = loop(i, n)
    arms = dict(R.front_arms(X, "sides"), lh="fist", rh="fist")
    return R.FP(hip=(0.0, 0.5 + 0.5 * s), head=(0.0, 0.2 * s, 0.0), lf=(3.0, 0.0), rf=(3.0, 0.0), mouth="flat", brows=-1.0, **arms)


X.rows = list(X.rows) + [("front", 8, 150)]

ROWS = X.rows
FRAME_SIZE = X.frame
_render_frame = X.render_frame
render, main, render_canonical = R.entry_points(X, ACTOR_METADATA, DISPLAY_NAME)


def render_portraits(out_dir, **opts):
    """His portraits are frames of this sheet."""
    del opts
    return X.portraits(out_dir, {"default": ("idle", (1,), 0, False), "talking": ("taunt", (0, 2, 3, 4, 5, 6), 110, True)}, view_width=32.0)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}

# ---- In the round (``_round_cast``) --------------------------------------------
#
# His trunk and head in 3D come from the numbers of his own makers
# (``auto_trunk``, ``auto_head``); his head from the side is drawn by the
# cast's makers in the numbers of a profile; what the numbers do not say is
# here, as data. His rows do not use this.

import numpy as np  # noqa: E402

from . import _person_round as O  # noqa: E402
from . import _round_cast as C  # noqa: E402
from . import _round_wear as W  # noqa: E402


class _Body(C.PersonBody):
    """He as a body: his near (right) upper arm carries the red armband and
    its emblem, as his three-quarter rows draw it on the near arm."""

    def arm(self, name, shoulder, elbow, wrist, mode):
        piece = super().arm(name, shoulder, elbow, wrist, mode)
        if not name.startswith("r_"):
            return piece

        def band(img, pts, near):
            t = (BAND[0] + BAND[1]) / 2.0
            at = (lerp(pts[0][0], pts[1][0], t), lerp(pts[0][1], pts[1][1], t))
            K.place(img, F.band(K, lerp(8.6, 7.4, t) + 0.8), at, "armband", math.degrees(math.atan2(pts[1][1] - pts[0][1], pts[1][0] - pts[0][0])))
            if near:
                K.place(img, F.emblem(K, 2.3), at, "armband_emblem", 0.0)

        return C.limb_piece(K, name, [shoulder, elbow, wrist],
                            lambda pts, near: C.seg_bones(K, name, pts[0], pts[1], X.upper_arm(near)) + C.seg_bones(K, name, pts[1], pts[2], X.forearm(near)),
                            hand=lambda near: X.hand(mode, near), extra=band, lead=3.0)


def _side_cap():
    """His cap from the side: the crown high in front, the band and its red
    piping, the black visor out in front, the badge on its edge."""

    def shape(d) -> None:
        K.poly(d, [K.at(-9.8, -5.6), K.at(-10.6, -10.0), K.at(-12.6, -13.0), K.at(-9.0, -16.4), K.at(0.4, -17.8), K.at(8.6, -21.0), K.at(13.6, -20.0),
                   K.at(12.8, -15.4), K.at(9.6, -10.8), K.at(10.0, -6.6)], WHITE)
        K.poly(d, [K.at(3.4, -6.8), K.at(10.0, -7.0), K.at(15.2, -4.4), K.at(13.6, -3.2), K.at(5.2, -4.2)], WHITE)

    def detail(d) -> None:
        K.poly(d, [K.at(-20.0, -10.0), K.at(9.8, -10.8), K.at(10.4, -6.2), K.at(-20.0, -5.0)], COLLAR)
        K.line(d, [K.at(-20.0, -10.2), K.at(9.8, -11.0)], RED, 0.7)
        K.line(d, [K.at(-12.0, -13.2), K.at(-8.6, -16.2), K.at(0.4, -17.4), K.at(8.6, -20.4), K.at(13.0, -19.6)], RED, 0.7)
        K.line(d, [K.at(-6.0, -14.8), K.at(2.4, -15.8), K.at(9.4, -18.4)], UNIFORM_LIGHT, 0.6)
        K.poly(d, [K.at(3.4, -6.8), K.at(10.0, -7.0), K.at(15.2, -4.4), K.at(13.6, -3.2), K.at(5.2, -4.2)], BOOT)
        K.line(d, [K.at(5.8, -5.8), K.at(10.2, -6.0), K.at(13.8, -4.4)], BOOT_SHINE, 0.5)
        K.oval(d, K.at(10.6, -14.6), 1.2, 2.6, OUTLINE)
        K.oval(d, K.at(10.6, -14.6), 0.9, 2.2, DISC)

    return K.solid(("side_cap",), shape, UNIFORM, detail, outline=1.2, rim=0.3, shade=0.35, shade_colour=UNIFORM_DARK)


def _side_hair(d) -> None:
    K.poly(d, [K.at(20.0, -30.0), K.at(20.0, -8.6), K.at(8.0, -8.6), K.at(4.4, -7.4), K.at(1.2, -7.0), K.at(1.0, -1.6), K.at(-0.6, -1.8), K.at(-3.4, 1.0),
               K.at(-4.4, 5.6), K.at(-2.6, 7.6), K.at(-20.0, 9.0), K.at(-20.0, -30.0)], HAIR)
    K.line(d, [K.at(-7.6, -4.0), K.at(-7.0, 2.0), K.at(-5.8, 6.0)], HAIR_DARK, 0.5)


def _side_face(d) -> None:
    K.poly(d, [K.at(0.8, -7.0), K.at(20.0, -7.0), K.at(20.0, -3.4), K.at(8.8, -3.0), K.at(1.0, -3.6)], mix(SKIN, SKIN_DEEP, 0.32))
    K.line(d, [K.at(6.0, 2.6), K.at(5.2, 5.8)], mix(SKIN, SKIN_DEEP, 0.45), 0.5)


_side_head = R.make_head(K, ("enforcer_side",), SKIN, SKIN_SHADE, SKIN_DEEP, skull=(0.0, -2.6, 9.0, 9.2), jaw=(3.2, 4.4, 7.2, 7.2),
                         nose=((7.8, -1.8), (11.2, 3.2), (10.4, 4.8), (7.8, 5.2)), ear=(-1.6, 1.2, 2.2, 3.3), under=_side_hair, over=_side_face,
                         far_shade=False)
_side_eyes = R.make_eyes(K, (6.6, -0.4), None, ink=INK, white=None, lid=SKIN_DEEP, size=0.9)
_side_brows = R.make_brows(K, [(4.4, -2.4), (6.6, -3.0), (8.8, -2.4)], None, HAIR_DARK, 1.4)
_side_mouth = R.make_mouth(K, (8.2, 7.8), MOUTH, wide=0.55)


def _side_layers(pose):
    out = [(_side_head(), "head"), (_side_eyes(str(pose["eyes"])), "eyes"), (_side_brows(R.brow_mood(pose)), "brows"), (_side_mouth(str(pose["mouth"])), "mouth")]
    if float(pose["cap"]) >= 0.5:
        out.append((_side_cap(), "cap"))
    return out


#: His cap: the crown high in front, the band with its red piping, the badge;
#: the black visor in front only (its back is inside the crown).
CAP_3D = W.Hat(crown=[O.Ring(-6.4, 0.0, 0.6, 8.8, 8.8), O.Ring(-10.8, 0.0, 0.6, 9.0, 9.2), O.Ring(-14.6, 0.0, 0.6, 11.6, 11.8, droop=-2.4),
                      O.Ring(-16.0, 0.0, 0.8, 10.6, 11.0, droop=-3.2), O.Ring(-16.4, 0.0, 0.8, 0.0, 0.0, droop=-3.2)],
               brim=None, garment=W.Garment(UNIFORM, UNIFORM_DARK, [W.Band(-10.8, -6.2, COLLAR), W.Band(-11.3, -10.8, RED), W.Dot(0.0, -14.4, 2.4, DISC, ring=OUTLINE),
                                                                     W.Dot(0.0, -14.4, 1.2, F.COG), W.Shade(-0.4)]), under=UNIFORM_DARK)
VISOR_3D = W.Worn("visor", [O.Ring(-6.6, 0.0, 3.6, 7.8, 8.8, v=0.0), O.Ring(-4.6, 0.0, 4.8, 8.0, 9.8, droop=1.6, v=1.0), O.Ring(-6.0, 0.0, 3.6, 7.8, 8.8, v=3.0)],
                  W.Garment(BOOT, BOOT_DARK), on="head")

ROUND = C.Round(
    DISPLAY_NAME, _Body(X, heads={"side": _side_layers}),
    C.Look(
        # Hair cut short under his cap: at the back of it and a short sideburn.
        C.auto_head(X, _head, _eyes, hair=lambda u, v: (v < -6.4) | ((np.abs(u) > 72.0) & (v < 1.0)) | ((np.abs(u) > 100.0) & (v < 6.0)),
                    hair_colour=HAIR, hair_shade=HAIR_DARK),
        # His tunic: four pockets, the placket and its buttons, the cross
        # strap from his far shoulder, the black belt and its buckle.
        C.auto_trunk(X, [W.Patch(8.0, 40.0, -29.0, -21.0, UNIFORM_DARK), W.Patch(-40.0, -8.0, -29.0, -21.0, UNIFORM_DARK),
                         W.Patch(10.0, 42.0, -29.0, -26.0, UNIFORM_LIGHT), W.Patch(-42.0, -10.0, -29.0, -26.0, UNIFORM_LIGHT),
                         W.Patch(8.0, 42.0, -1.4, 9.0, UNIFORM_DARK), W.Patch(-42.0, -8.0, -1.4, 9.0, UNIFORM_DARK),
                         W.Patch(10.0, 44.0, -1.4, 1.4, UNIFORM_LIGHT), W.Patch(-44.0, -10.0, -1.4, 1.4, UNIFORM_LIGHT),
                         W.Down(0.0, TOP + 3.0, 12.0, UNIFORM_DARK, width=0.4), W.Buttons(0.0, -33.0, -12.0, 4, 0.8, METAL),
                         W.Path([(45.0, TOP - 1.0), (0.0, -22.0), (-60.0, -12.0), (-120.0, -7.0)], BELT, 0.9),
                         W.Band(-8.6, -4.0, BELT), W.Patch(-9.0, 9.0, -9.0, -3.6, METAL), W.Across(-180.0, 180.0, 11.0, UNIFORM_DARK, width=0.3),
                         W.Down(180.0, TOP + 3.0, -9.0, UNIFORM_DARK)]),
        head_pieces=[CAP_3D, VISOR_3D]),
    # Square on his feet, his chest out, his fists closed at his sides and a
    # little in front of him.
    C.Stance(hands={"r": C.Hand(l=-11.6, pole=(-0.4, 0.0, -1.0), mode="fist"), "l": C.Hand(l=11.6, pole=(0.4, 0.0, -1.0), mode="fist")}, stagger=2.0))

if __name__ == "__main__":
    raise SystemExit(main())
