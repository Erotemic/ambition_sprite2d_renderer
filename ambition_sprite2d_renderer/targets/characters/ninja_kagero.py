"""Sprite generator for Kagero: the kunoichi who hunts the spirits of the regime.

The look (2026-10-21; Jon: "I also want a ninja to come to your aid in the
fight, appear on screen and do a few hits on the boss and then fly off the
screen (using flyline maybe). It should not be the Shadow Oni Leader, a
different ninja"): a slight woman of 165 cm, seen three quarters from the
front, facing right. She comes out of nowhere, cuts three times and is gone up
her line.

She is black from her head to her feet, as the ninjas of the game are (Jon,
2026-10-13: the ninjas are black, with red eyes in a dark slit, and show no
skin). What makes her not one of the dojo: the WHITE of a spirit hunter where
the dojo has red. Her long scarf is white, and so are the paper talismans
(ofuda) that hang from her sash, each with a red seal. Her hair comes out of
the back of her hood in a long tail tied with red cord. At her far hip she
carries the coil of her line and its iron hook: the line she leaves on. Her
blade is short and straight. There is no drop shadow.

The rows are the ones her visit plays: ``idle``, ``jump``, ``fall``,
``dash`` (she goes at it), three cuts that are one string (``slash``
forward, ``slash_up`` up through it, ``cleave`` down on it), ``hang`` (she
holds her line over her head; the engine draws the line), ``hit``,
``death``, the two poses of a blink: ``blink_out`` and ``blink_in``
(she comes in low, in her smoke), and ``cast`` (2026-10-24, Jon: "The ninja
uses a spell to dispel the blue flames protecting the boss"): she makes the
seal with her far hand, her talismans fan out of it, and she throws them.
The warp of a blink is the engine's.

She is a person of ``_person_rig``. Her trunk is a woman's
(``make_figure``); the head, the clothes, the blade and how she stands are
hers.
"""

from __future__ import annotations

import math
from typing import List

from ._ai_era_kit import OUTLINE, WHITE, RGBA, pin
from . import _person_rig as R
from ._person_rig import Build, Person, Stamp, loop, shot

TARGET_NAME = "ninja_kagero"
TARGET_BASENAME = TARGET_NAME
DISPLAY_NAME = "Kagero"

ACTOR_METADATA = {
    "actor": {"character_id": "npc_ninja_kagero", "display_name": "Kagero"},
    "lineage": {
        "family": "npc_ninja_kagero",
        "variant": "spirit_hunter",
        "parents": [],
        "creator": {
            "kind": "model",
            "model": "Claude Opus 5.5",
        },
        "method": "person_rig",
        "revision": "first_draft",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Floating",
        "mass_class": "Light",
        "traits": ["story", "humanoid", "ally", "combatant", "ninja", "masked"],
        "locomotion_hint": "Fly",
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": True,
            "climb": None,
            "fly": True,
            "swim": None,
            "crawl": None,
            "use_lifts": None,
            "door_access": [],
        },
        "interactions": {
            "talk": True,
            "trade": None,
            "carry": None,
            "open_doors": [],
        },
    },
    "brain": {"default_preset": "none"},
    "actions": {"default_preset": "none"},
    "visual": {"default_pose": "idle"},
    "tags": ["story", "humanoid", "ally", "combatant", "ninja", "masked"],
    "sockets": {
        "head": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 64.0, "y": 24.0},
        },
        "chest": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 64.0, "y": 54.0},
        },
        "speech_bubble": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 64.0, "y": 8.0},
        },
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "action.melee.primary": {"animation": "slash", "events": []},
    },
}


#: The black of the ninjas: a little blue in it, so its folds and its edges
#: can be seen.
GI: RGBA = (30, 32, 46, 255)
GI_DARK: RGBA = (16, 17, 27, 255)
GI_LIGHT: RGBA = (62, 68, 96, 255)
HOOD: RGBA = (26, 28, 41, 255)
HOOD_DARK: RGBA = (13, 14, 23, 255)
SLEEVE: RGBA = (36, 39, 56, 255)
SLEEVE_DARK: RGBA = (21, 23, 35, 255)
GLOVE: RGBA = (42, 44, 60, 255)
GLOVE_DARK: RGBA = (19, 20, 31, 255)
WRAP: RGBA = (50, 53, 72, 255)
WRAP_DARK: RGBA = (29, 31, 45, 255)
HAIR: RGBA = (20, 18, 26, 255)
HAIR_LIGHT: RGBA = (58, 56, 80, 255)
#: The slit of her hood is in shadow, and her eyes are red lights in it.
SLIT: RGBA = (8, 7, 12, 255)
EYE: RGBA = (232, 40, 46, 255)
EYE_HOT: RGBA = (255, 150, 120, 255)
#: The white of a spirit hunter: her scarf and her talismans.
PAPER: RGBA = (240, 236, 226, 255)
PAPER_DARK: RGBA = (184, 178, 170, 255)
SCARF: RGBA = (232, 232, 238, 255)
SCARF_DARK: RGBA = (164, 166, 184, 255)
SEAL: RGBA = (196, 36, 42, 255)
CORD: RGBA = (176, 40, 46, 255)
CORD_DARK: RGBA = (110, 24, 32, 255)
ROPE: RGBA = (150, 126, 92, 255)
ROPE_DARK: RGBA = (94, 76, 54, 255)
IRON: RGBA = (110, 116, 132, 255)
IRON_LIGHT: RGBA = (176, 184, 200, 255)
STEEL: RGBA = (226, 232, 240, 255)
STEEL_DARK: RGBA = (150, 160, 180, 255)
STEEL_LIGHT: RGBA = (255, 255, 255, 255)
CUT: RGBA = (236, 242, 250, 255)
SMOKE: RGBA = (196, 198, 214, 255)
SMOKE_DARK: RGBA = (120, 122, 146, 255)

#: 165 cm, and slight.
BUILD = Build(hip_up=47.0, thigh=22.9, shin=21.3, neck=(0.6, -35.0), upper=18.4, fore=17.4, near_shoulder=(-4.4, -30.6), far_shoulder=(5.0, -30.2),
              near_hip=(-3.8, 0.0), far_hip=(3.8, 0.0), head_up=(1.0, -12.2), height=106.0, half_width=(11.5, 13.0))

X = Person(TARGET_NAME, BUILD, frame=(240, 192), ground=180.0, cx=112.0)
K = X.K
P = X.P
U = X.U
FRAME_SIZE = X.frame
#: Her blade is short and straight: the guard is ``GUARD_AT`` in front of her
#: near hand, and the end of the grip is ``BUTT`` behind it.
BLADE = 34.0
GUARD_AT = 3.0
BUTT = 8.0
TOP = -36.6


def _front(d, hb: float, hf: float) -> None:
    """The cross of her jacket, her sash of black and its white knot, the
    folds of her short skirt."""
    K.poly(d, [K.at(-2.2, TOP), K.at(0.2, TOP - 0.6), K.at(7.0, -18.6), K.at(5.0, -18.0)], GI_LIGHT)
    K.line(d, [K.at(6.0, TOP + 2.4), K.at(4.4, -25.6)], GI_LIGHT, 0.8)
    # The sash: narrow, close at her waist.
    K.poly(d, [K.at(-30.0, -15.4), K.at(30.0, -14.4), K.at(30.0, -10.2), K.at(-30.0, -11.2)], HOOD_DARK)
    K.line(d, [K.at(-30.0, -13.2), K.at(30.0, -12.2)], SCARF_DARK, 0.6)
    K.oval(d, K.at(-2.6, -12.6), 2.0, 1.8, SCARF, OUTLINE, 0.5)
    K.line(d, [K.at(-5.0, -26.0), K.at(-3.6, -16.4)], GI_DARK, 0.6)
    K.line(d, [K.at(3.6, -8.0), K.at(4.4 + hf * 0.5, 4.0)], GI_DARK, 0.6)
    K.line(d, [K.at(-3.0, -8.0), K.at(-3.6 - hb * 0.5, 4.6)], GI_DARK, 0.6)


X.torso = R.make_figure(K, ("kagero",), GI, GI_DARK, back=(6.6, 7.0, 5.4, 7.6, 8.6), front=(5.8, 8.2, 5.6, 8.0, 8.8), hem_y=6.0, top=TOP,
                        shoulders=((-4.4, -30.0), (4.6, -29.8)), shoulder_r=(4.2, 3.6), shade_from=6.2, detail=_front)

NEAR_EYE = (1.8, -0.8)
FAR_EYE = (6.6, -1.0)


def _hood_shape(d) -> None:
    # The hood is close on her head; the tail of her hair comes out at the
    # back of it.
    K.oval(d, K.at(-0.4, -2.6), 8.4, 9.2, WHITE)
    K.oval(d, K.at(2.2, 3.8), 5.6, 7.0, WHITE)
    K.oval(d, K.at(-7.6, -4.6), 3.0, 2.6, WHITE)


def _hood(d) -> None:
    K.poly(d, [K.at(-30.0, -30.0), K.at(30.0, -30.0), K.at(30.0, -4.6), K.at(9.0, -4.6), K.at(3.6, -5.0), K.at(-0.6, -4.0), K.at(-1.6, -1.0), K.at(-1.0, 1.4),
               K.at(3.6, 1.8), K.at(10.0, 1.4), K.at(30.0, 1.4), K.at(30.0, 30.0), K.at(-30.0, 30.0)], HOOD)
    K.line(d, [K.at(9.0, -4.6), K.at(3.6, -5.0), K.at(-0.6, -4.0), K.at(-1.6, -1.0), K.at(-1.0, 1.4), K.at(3.6, 1.8), K.at(10.0, 1.4)], HOOD_DARK, 0.7)
    K.line(d, [K.at(-5.4, -9.0), K.at(-7.0, -1.0), K.at(-5.6, 6.6)], HOOD_DARK, 0.6)
    K.line(d, [K.at(0.2, 4.2), K.at(3.6, 6.4), K.at(7.4, 5.4)], HOOD_DARK, 0.6)
    K.line(d, [K.at(-2.0, -8.8), K.at(3.8, -10.0), K.at(8.0, -8.6)], GI_LIGHT, 0.5)
    # The red cord where her hair is tied, at the back of the hood.
    K.oval(d, K.at(-7.6, -4.6), 2.6, 2.2, HAIR)
    K.line(d, [K.at(-8.6, -6.6), K.at(-7.0, -2.8)], CORD, 1.0)


_head = R.make_head(K, ("kagero",), SLIT, SLIT, SLIT, skull=(0.0, -2.4, 7.4, 8.4), jaw=(2.2, 3.6, 5.0, 6.6),
                    nose=((6.4, -0.8), (8.6, 2.6), (8.0, 3.8), (6.4, 4.2)), ear=None, shape=_hood_shape, under=_hood)


def _eyes(mode: str):
    """Her eyes: two red lights in the slit, and a lash that flicks up at
    the outer end of each. Shut, each is a thin red line; struck, wide."""

    def paint(d) -> None:
        for (ex, ey), k in ((NEAR_EYE, 1.0), (FAR_EYE, 0.8)):
            if mode in ("closed", "wince", "happy"):
                K.line(d, [K.at(ex - 2.0 * k, ey - 0.2), K.at(ex + 1.9 * k, ey + 0.4)], EYE, 0.7)
                continue
            tall = 1.9 if mode == "wide" else 1.3
            K.poly(d, [K.at(ex - 2.2 * k, ey - tall * 0.6), K.at(ex + 2.2 * k, ey - tall * 0.4), K.at(ex + 1.4 * k, ey + tall * 0.8), K.at(ex - 1.6 * k, ey + tall * 0.5)], EYE)
            K.oval(d, K.at(ex + 0.3 * k, ey + 0.1), 0.8 * k, 0.6, EYE_HOT)
            K.line(d, [K.at(ex + 2.0 * k, ey - tall * 0.4), K.at(ex + 3.0 * k, ey - tall * 0.4 - 1.2)], SLIT, 0.6)

    return K.piece(("kagero_eyes", mode), paint)


X.head_layers = lambda pose: [(_head(), "head"), (_eyes(str(pose["eyes"])), "eyes")]
X.neck = R.make_neck(K, HOOD_DARK, 5.2)
X.upper_arm = lambda near: [(0.0, 1.0, 7.6, 6.4, SLEEVE if near else SLEEVE_DARK)]
X.forearm = lambda near: [(0.0, 1.0, 6.2, 4.8, SLEEVE if near else SLEEVE_DARK), (0.3, 0.94, 6.6, 5.4, WRAP if near else WRAP_DARK)]
X.thigh = lambda near: [(0.0, 1.0, 10.0, 8.2, GI if near else GI_DARK)]
X.shin = lambda near: [(0.0, 0.34, 8.6, 7.8, GI if near else GI_DARK), (0.3, 1.0, 6.8, 5.2, WRAP if near else WRAP_DARK)]
X.hand = R.make_hand(K, GLOVE, GLOVE_DARK, GLOVE_DARK, size=0.92)
X.shoe = R.make_shoe(K, HOOD, HOOD_DARK, BUILD.ankle_up, long=0.92, sole=HOOD_DARK)


def _scarf_wrap():
    """The white scarf round her neck, over her collar."""

    def shape(d) -> None:
        K.poly(d, [K.at(-6.0, -3.2), K.at(0.0, -4.6), K.at(6.2, -3.4), K.at(7.0, 0.6), K.at(2.0, 3.2), K.at(-5.2, 2.0), K.at(-7.0, -0.6)], WHITE)

    def detail(d) -> None:
        K.line(d, [K.at(-5.6, -1.0), K.at(0.0, 0.6), K.at(6.6, -1.4)], SCARF_DARK, 0.7)

    return K.solid(("kagero_scarf",), shape, SCARF, detail, outline=1.1, rim=0.25, shade=0.3, shade_colour=SCARF_DARK)


X.collar = _scarf_wrap

#: Where each row sends the ends of her scarf and the tail of her hair, and
#: how much they wave: 90 hangs, 180 is out behind her, 270 is up.
FLOW = {"cast": (150.0, 7.0), "dash": (188.0, 6.0), "jump": (128.0, 6.0), "fall": (236.0, 8.0), "slash": (166.0, 8.0), "slash_up": (120.0, 9.0), "cleave": (210.0, 9.0),
        "hang": (112.0, 10.0), "hit": (30.0, 6.0), "blink_in": (204.0, 8.0), "blink_out": (136.0, 6.0)}


def lerp_(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _flow(ctx):
    heading, wave = FLOW.get(ctx.anim, (132.0, 4.0))
    if ctx.anim == "death":
        heading, wave = (lerp_(132.0, 176.0, ctx.u), 2.0)
    return heading, wave


def _tails(ctx) -> List[Stamp]:
    """The two ends of her scarf, from the back of her neck: long, and out
    behind her when she goes."""
    a = math.radians(ctx.lean)
    root = (ctx.neck[0] - 6.0 * math.cos(a) + 1.4 * math.sin(a), ctx.neck[1] - 6.0 * math.sin(a) - 1.4 * math.cos(a))
    at = pin(root)
    heading, wave = _flow(ctx)
    phase = ctx.phase if ctx.anim in ("idle", "fall", "dash", "hang") else math.tau * ctx.u
    chains = [R.chain((root[0] - at[0], root[1] - at[1] + dy), 8 - k, 4.6, heading + spread, wave=wave, curl=-2.0, phase=phase, lead=lead)
              for k, (dy, spread, lead) in enumerate(((0.0, 0.0, 0.0), (1.4, 12.0, 1.3)))]
    return [(R.ribbon(K, ("kagero_tails",), chains, 2.8, SCARF, SCARF_DARK, taper=0.5), at, "scarf_tails", 0.0)]


def _hair(ctx) -> List[Stamp]:
    """The tail of her hair, from the back of her hood: it hangs in the world."""
    a = math.radians(ctx.turn)
    root = (ctx.head[0] - 7.6 * math.cos(a) + 4.6 * math.sin(a), ctx.head[1] - 7.6 * math.sin(a) - 4.6 * math.cos(a))
    at = pin(root)
    heading, wave = _flow(ctx)
    heading = lerp_(heading, 100.0, 0.25)
    chains = [R.chain((root[0] - at[0], root[1] - at[1]), 6, 4.2, heading, wave=wave * 0.8, curl=-3.0, phase=ctx.phase + 0.6)]
    return [(R.ribbon(K, ("kagero_hair",), chains, 3.4, HAIR, HAIR_LIGHT, taper=0.35), at, "hair", 0.0)]


X.layers["back"].append(_tails)
X.layers["back"].append(_hair)

# ---- What she carries ------------------------------------------------------


def _ofuda(spread: int):
    """Three paper talismans from one knot: long white slips, each with a red
    seal, fanned by ``spread`` degrees. They are one piece: drawn apart, the
    three small slips over each other did not replay."""
    slips = [(-2.6, -spread), (0.0, 0.0), (2.6, spread)]

    def slip(dx: float, a: float):
        r = math.radians(a)
        c, s_ = math.cos(r), math.sin(r)
        return lambda x, y: K.at(dx + x * c - y * s_, x * s_ + y * c)

    def shape(d) -> None:
        for dx, a in slips:
            at = slip(dx, a)
            K.poly(d, [at(-1.6, 0.0), at(1.6, 0.0), at(1.6, 9.0), at(-1.6, 9.0)], WHITE)

    def detail(d) -> None:
        for dx, a in slips:
            at = slip(dx, a)
            K.line(d, [at(0.0, 1.4), at(0.0, 4.4)], SEAL, 0.8)
            K.oval(d, at(0.0, 6.2), 0.9, 0.9, SEAL)

    return K.solid(("kagero_ofuda", spread), shape, PAPER, detail, outline=0.8, rim=0.0, shade=0.0, shade_colour=PAPER_DARK)


def _talismans(ctx) -> List[Stamp]:
    """The talismans from her sash at her near hip: they swing out behind
    her as her scarf does, and fan as they swing."""
    heading, _wave = _flow(ctx)
    swing = max(-50.0, min(50.0, (heading - 100.0) * 0.45))
    spread = int(round(6.0 + abs(swing) * 0.2))
    return [(_ofuda(spread), ctx.trunk(-4.0, -10.6), "ofuda", ctx.lean + swing + 3.0 * math.sin(ctx.phase))]


def _coil_part():
    """The coil of her line, with its iron hook, along +x from where it hangs."""

    def shape(d) -> None:
        K.oval(d, K.at(4.6, 0.0), 5.4, 4.2, WHITE)
        K.poly(d, [K.at(9.0, -1.4), K.at(13.6, -3.0), K.at(15.0, 0.6), K.at(11.0, 2.0)], WHITE)

    def detail(d) -> None:
        for r in (4.6, 3.4, 2.2):
            K.oval(d, K.at(4.6, 0.0), r + 0.6, r, None, ROPE_DARK, 0.6)  # type: ignore[arg-type]
        K.line(d, [K.at(9.6, -0.4), K.at(13.6, -2.2)], IRON, 1.2)
        K.line(d, [K.at(13.6, -2.2), K.at(14.4, 0.2), K.at(12.8, 1.2)], IRON_LIGHT, 0.8)

    return K.solid(("kagero_coil",), shape, ROPE, detail, outline=1.0, rim=0.0, shade=0.2, shade_colour=ROPE_DARK)


def _coil(ctx) -> List[Stamp]:
    # At her far hip. While she hangs, her line is out and the coil is gone.
    if ctx.anim == "hang":
        return []
    return [(_coil_part(), ctx.trunk(5.0, -8.6), "coil", 70.0 + ctx.lean)]


X.layers["back"].append(_coil)
X.layers["over_torso"].append(_talismans)


def _blade():
    """Her blade along +x from her near hand: a short straight edge, a square
    guard, a grip in red cord."""
    g = GUARD_AT

    def shape(d) -> None:
        K.rrect(d, K.home[0] - BUTT, K.home[1] - 1.4, K.home[0] + g, K.home[1] + 1.4, 0.8, WHITE)
        K.rrect(d, K.home[0] + g - 1.2, K.home[1] - 3.0, K.home[0] + g + 1.0, K.home[1] + 3.0, 0.4, WHITE)
        K.poly(d, [K.at(g, -1.4), K.at(g + BLADE - 4.0, -1.4), K.at(g + BLADE, 0.2), K.at(g + BLADE - 4.0, 1.6), K.at(g, 1.6)], WHITE)

    def detail(d) -> None:
        K.rrect(d, K.home[0] - BUTT, K.home[1] - 2.0, K.home[0] + g, K.home[1] + 2.0, 0.0, CORD_DARK)
        for k in range(4):
            x = -BUTT + 1.2 + k * 2.2
            K.line(d, [K.at(x, -1.8), K.at(x + 1.4, 1.8)], CORD, 0.6)
        K.rrect(d, K.home[0] + g - 1.2, K.home[1] - 3.0, K.home[0] + g + 1.0, K.home[1] + 3.0, 0.0, IRON)
        K.poly(d, [K.at(g + 1.0, -1.4), K.at(g + BLADE - 4.0, -1.4), K.at(g + BLADE, 0.2), K.at(g + BLADE - 4.0, 1.6), K.at(g + 1.0, 1.6)], STEEL)
        K.line(d, [K.at(g + 1.4, 0.9), K.at(g + BLADE - 3.0, 0.9)], STEEL_LIGHT, 0.6)
        K.line(d, [K.at(g + 1.4, -0.9), K.at(g + BLADE - 4.0, -0.9)], STEEL_DARK, 0.5)

    return K.solid(("kagero_blade",), shape, STEEL, detail, outline=1.0, rim=0.0, shade=0.0, shade_colour=STEEL_DARK)


def _held(ctx) -> List[Stamp]:
    """The blade in her near hand, at the turn the pose says (``blade``: 0 is
    forward, -90 is up). It is in front of her arm, and her hand is round it.
    When she is down it lies by her."""
    hand, elbow = ctx.hand, ctx.elbow
    if float(ctx.pose["held"]) < 0.5:
        lie = (X.cx + 46.0, ctx.ground - 2.4)
        t = min(1.0, max(0.0, (ctx.u - 0.12) / 0.3)) if ctx.anim == "death" else 1.0
        up = 16.0 * math.sin(math.pi * t)
        at = (lerp_(hand[0], lie[0], t), lerp_(hand[1], lie[1], t) - up)
        return [(_blade(), at, "blade", lerp_(float(ctx.pose["blade"]) - 360.0, 4.0, t) if t < 1.0 else 4.0)]
    return [(_blade(), hand, "blade", float(ctx.pose["blade"])),
            (X.hand(str(ctx.pose["nh"]), True), hand, "near_hand_on_blade", math.degrees(math.atan2(hand[1] - elbow[1], hand[0] - elbow[0])))]


X.layers["front"].append(_held)

# ---- How she holds herself -------------------------------------------------

#: Her guard: the blade in her near hand, low in front of her, its point
#: forward; her far hand open in front of her chest.
HAND = (13.0, 13.0)
POINT = -16.0
X.set_rest(lean=6.0, hip=(0.0, 2.0), na=HAND, nh="fist", fa=(9.0, 4.0), fh="flat", nf=(-9.0, 0.0, 0.0), ff=(9.0, 0.0, 0.0), brows=-1.0, blade=POINT,
           held=1.0)


@X.row
def idle(i: int, n: int):
    _, s, c = loop(i, n)
    return P(na=(HAND[0], HAND[1] + 0.5 * s), blade=POINT + 1.5 * s, hip=(0.0, 2.0 + 0.4 * s), head=(0.0, 0.2 * s, 0.6 * c),
             eyes="closed" if i == n - 2 else "open")


@X.row
def jump(i: int, n: int):
    wind = P(hip=(-1.0, 10.0), lean=14.0, na=(-10.0, 14.0), fa=(-6.0, 15.0), nf=(-7.0, 0.0, 0.0), ff=(8.0, 0.0, 0.0), blade=150.0)
    rise = P(hip=(0.0, -2.0), lean=6.0, head=(0.0, 0.0, -8.0), na=(-12.0, 12.0), fa=(10.0, 4.0), nf=(-6.0, -1.0, 34.0), ff=(6.0, -10.0, 12.0), blade=140.0,
             hem=(1.0, 1.0))
    apex = P(hip=(0.0, -2.0), lean=2.0, head=(0.0, 0.0, -3.0), na=(-9.0, 4.0), fa=(13.0, 2.0), nf=(-5.0, -9.0, 22.0), ff=(8.0, -13.0, 4.0), blade=200.0,
             hem=(3.0, 3.0))
    return X.keys(shot(i, n), [(0.0, wind), (0.3, rise), (0.6, rise), (1.0, apex)])


@X.row
def fall(i: int, n: int):
    _, s, c = loop(i, n)
    return P(hip=(0.0, -3.0), lean=-4.0, head=(0.0, 0.0, 6.0), na=(-6.0 + 1.0 * s, -4.0 - 1.0 * c), fa=(13.0 - 1.5 * s, 2.0 + 1.5 * c),
             nf=(-8.0, -3.0 + 1.5 * s, 28.0), ff=(7.0, -9.0 - 1.5 * s, 8.0), blade=226.0 + 3.0 * s, hem=(5.0, 5.0))


@X.row
def dash(i: int, n: int):
    # She goes at it flat out, the blade back along her near arm, her knees up.
    _, s, _c = loop(i, n)
    return P(hip=(4.0, -2.0 + 0.6 * s), lean=34.0, head=(1.0, 0.0, -24.0), na=(-14.0, 10.0), fa=(-10.0, 12.0), fh="flat", nf=(-18.0, -6.0 - s, 40.0),
             ff=(8.0, -14.0, 30.0), blade=176.0, hem=(7.0, 0.0))


#: The cut is wound: the blade back over her far shoulder.
WOUND = P(hip=(-2.0, 1.0), lean=-8.0, head=(0.0, 0.0, -4.0), na=(-2.0, -8.0), nab=-1.0, fa=(13.0, 6.0), fh="flat", nf=(-9.0, -2.0, 10.0), ff=(8.0, -6.0, 0.0),
          blade=-150.0, eyes="wide")
#: The cut is through: her near arm out in front, the point forward and down.
THROUGH = P(hip=(4.0, 3.0), lean=22.0, head=(1.0, 0.4, -10.0), na=(24.0, 8.0), fa=(-8.0, 10.0), fh="flat", nf=(-14.0, -3.0, 18.0), ff=(12.0, -4.0, 0.0),
            blade=22.0, hem=(5.0, 1.0))
#: Low behind her, for a cut that goes up.
LOW_BACK = P(hip=(-1.0, 5.0), lean=16.0, head=(0.0, 0.0, -8.0), na=(-12.0, 20.0), fa=(10.0, 8.0), fh="flat", nf=(-10.0, -2.0, 16.0), ff=(9.0, -4.0, 0.0),
             blade=150.0)
#: Up through it: the arm high in front, the point up.
HIGH = P(hip=(1.0, -5.0), lean=-10.0, head=(0.0, 0.0, -16.0), na=(14.0, -22.0), fa=(-6.0, 12.0), fh="flat", nf=(-6.0, -6.0, 30.0), ff=(6.0, -14.0, 10.0),
         blade=-70.0, eyes="wide", hem=(2.0, 4.0))
#: Two hands over her head, for the cut that comes down.
OVER = P(hip=(-1.0, -4.0), lean=-14.0, head=(0.0, 0.0, -10.0), na=(-1.0, -24.0), fa=(-4.0, -22.0), fh="fist", nf=(-8.0, -8.0, 24.0), ff=(7.0, -16.0, 8.0),
         blade=-120.0, eyes="wide", hem=(3.0, 5.0))
#: Down on it: the blade out and down, all of her behind it.
DOWN = P(hip=(5.0, 4.0), lean=34.0, head=(1.0, 0.6, -6.0), na=(20.0, 18.0), fa=(14.0, 16.0), fh="fist", nf=(-16.0, -4.0, 26.0), ff=(12.0, -2.0, 0.0),
         blade=58.0, hem=(6.0, 1.0))


@X.row
def slash(i: int, n: int):
    # The first cut: over her far shoulder and through, forward.
    return X.keys(shot(i, n), [(0.0, X.full(P())), (0.25, WOUND), (0.35, WOUND), (0.5, THROUGH), (0.85, THROUGH), (1.0, THROUGH)])


@X.row
def slash_up(i: int, n: int):
    # The second: from low behind her up through it.
    return X.keys(shot(i, n), [(0.0, THROUGH), (0.25, LOW_BACK), (0.35, LOW_BACK), (0.5, HIGH), (1.0, HIGH)])


@X.row
def cleave(i: int, n: int):
    # The last: both hands, from over her head down on it, and it stays.
    return X.keys(shot(i, n), [(0.0, HIGH), (0.3, OVER), (0.42, OVER), (0.56, DOWN), (1.0, DOWN)])


@X.row
def hang(i: int, n: int):
    # She holds her line over her head in her far hand and goes up it, the
    # blade back in her near hand and her knees up.
    _, s, c = loop(i, n)
    return P(hip=(0.0, -6.0), lean=-4.0 + 2.0 * s, head=(0.0, 0.0, -18.0), fa=(1.0, -27.0), fh="fist", na=(6.0, 8.0 + s), blade=118.0 + 4.0 * c,
             nf=(-6.0, -10.0 + 1.5 * s, 34.0), ff=(6.0, -15.0 - 1.5 * s, 14.0), hem=(2.0, 5.0))


@X.row
def hit(i: int, n: int):
    struck = dict(X.full(R.STRUCK), lean=-18.0, hip=(-4.0, 3.0), na=(12.0, 8.0), fa=(15.0, -2.0), nh="fist", fh="open", blade=-60.0, held=1.0, eyes="wince")
    return X.keys(shot(i, n), [(0.0, P(lean=-3.0, eyes="wide")), (0.3, struck), (0.65, struck), (1.0, X.full(P()))])


@X.row
def death(i: int, n: int):
    back = dict(X.full(R.STRUCK), lean=-18.0, na=(12.0, 8.0), nh="open", blade=-50.0, held=1.0, eyes="wince")
    sat = dict(X.full(R.SAT), held=0.0, eyes="closed")
    down = dict(X.full(R.SUPINE), held=0.0, eyes="closed")
    return X.keys(shot(i, n), [(0.0, back), (0.2, dict(back, lean=-26.0, held=0.0)), (0.5, sat), (0.75, down), (1.0, down)])


#: The sign: her far hand in front of her chest with two fingers up.
SIGN = P(hip=(0.0, 4.0), lean=3.0, head=(0.0, 0.4, 4.0), na=(-3.0, 21.0), fa=(6.0, 2.0), fh="point", nf=(-8.0, 0.0, 0.0), ff=(8.0, 0.0, 0.0), blade=150.0,
         eyes="closed")
#: She comes in low, a knee up, the blade behind her.
LOW = P(hip=(0.0, 14.0), lean=26.0, head=(1.0, 0.6, -14.0), na=(-12.0, 13.0), fa=(12.0, 18.0), fh="flat", nf=(-9.0, 0.0, 14.0), ff=(10.0, 0.0, 0.0),
        blade=172.0, hem=(3.0, 2.0))


#: Her spell: the seal at her face, eyes shut, the blade down at her side;
#: then her far arm flung out at it, and the talismans go.
SEAL_UP = P(hip=(0.0, 3.0), lean=-2.0, head=(0.0, 0.2, 6.0), na=(4.0, 18.0), fa=(7.0, -6.0), fh="point", nf=(-9.0, 0.0, 0.0), ff=(9.0, 0.0, 0.0),
            blade=100.0, eyes="closed")
THROW = P(hip=(3.0, 3.0), lean=16.0, head=(1.0, 0.2, -6.0), na=(-6.0, 16.0), fa=(25.0, -3.0), fh="flat", nf=(-12.0, 0.0, 0.0), ff=(10.0, 0.0, 0.0),
          blade=150.0, eyes="wide", hem=(3.0, 1.0))


@X.row
def cast(i: int, n: int):
    _, s, _c = loop(i, n)
    pose = X.keys(shot(i, n), [(0.0, X.full(P())), (0.2, SEAL_UP), (0.42, dict(SEAL_UP, head=(0.0, 0.4, 8.0))), (0.5, THROW), (0.8, THROW),
                               (1.0, dict(THROW, lean=8.0, fa=(18.0, 2.0), eyes="open"))])
    return dict(pose, hip=(pose["hip"][0], pose["hip"][1] + 0.4 * s))


@X.row
def blink_out(i: int, n: int):
    ready = X.full(P())
    return X.keys(shot(i, n), [(0.0, ready), (0.4, SIGN), (0.75, dict(SIGN, eyes="open")), (1.0, dict(SIGN, hip=(0.0, 7.0), lean=8.0, eyes="open"))])


@X.row
def blink_in(i: int, n: int):
    return X.keys(shot(i, n), [(0.0, LOW), (0.35, LOW), (1.0, X.full(P()))])


X.rows = [("idle", 8, 120), ("jump", 6, 95), ("fall", 6, 95), ("dash", 4, 60), ("slash", 8, 40), ("slash_up", 8, 40), ("cleave", 9, 46), ("hang", 8, 90),
          ("hit", 5, 90), ("death", 8, 110), ("blink_out", 6, 62), ("blink_in", 6, 62), ("cast", 16, 75)]

# ---- What the blade does, and her smoke --------------------------------------

#: The rows that cut.
CUTS = ("slash", "slash_up", "cleave")


def _trail(ctx):
    """The line of the cut: where the blade went from the last frame to this
    one, thin where it started and bright at the blade. It is light and not a
    thing: it has no outline. Nothing is in front of the blade, and a blade
    that does not move leaves nothing."""
    before = X.full(X.poses[ctx.anim](ctx.i - 1, ctx.n))
    now = ctx.pose
    a0, a1 = float(before["blade"]), float(now["blade"])
    if abs(a1 - a0) < 20.0:
        return None
    a0 = max(a0, a1 - 90.0) if a1 > a0 else min(a0, a1 + 90.0)
    dx = (float(before["na"][0]) - float(now["na"][0])) * U * 0.6
    dy = (float(before["na"][1]) - float(now["na"][1])) * U * 0.6
    reach = GUARD_AT + BLADE
    steps = 10
    outer, inner = [], []
    for k in range(steps + 1):
        t = k / steps
        a = math.radians(lerp_(a0, a1, t))
        ox, oy = dx * (1.0 - t), dy * (1.0 - t)
        outer.append((round(ox + reach * math.cos(a), 1), round(oy + reach * math.sin(a), 1)))
        r = reach * lerp_(0.98, 0.66, t * t)
        inner.append((round(ox + r * math.cos(a), 1), round(oy + r * math.sin(a), 1)))
    pts = (tuple(outer), tuple(inner))

    def paint(d) -> None:
        for k in range(steps):
            t = (k + 1) / steps
            K.poly(d, [K.at(*outer[k]), K.at(*outer[k + 1]), K.at(*inner[k + 1]), K.at(*inner[k])], CUT[:3] + (int(210 * t * t),))
        for k in range(steps):
            t = (k + 1) / steps
            K.line(d, [K.at(*outer[k]), K.at(*outer[k + 1])], STEEL_LIGHT[:3] + (int(255 * t),), 0.8)

    return K.aligned(("kagero_cut", pts), paint)


def _smoke(radius: float, alpha: int):
    def paint(d) -> None:
        K.oval(d, K.at(0.0, 0.0), radius, radius * 0.8, SMOKE_DARK[:3] + (int(alpha * 0.7),))
        K.oval(d, K.at(-radius * 0.2, -radius * 0.2), radius * 0.7, radius * 0.56, SMOKE[:3] + (alpha,))

    return K.piece(("kagero_smoke", round(radius, 1), alpha), paint)


def _slip(glow: int):
    """One talisman: a white slip with its red seal; charged (``glow`` over
    128), its edge is red. Along +y."""

    def shape(d) -> None:
        edge = SEAL if glow > 128 else OUTLINE
        K.poly(d, [K.at(-1.8, 0.0), K.at(1.8, 0.0), K.at(1.8, 9.0), K.at(-1.8, 9.0)], PAPER, edge, 0.6)
        K.line(d, [K.at(0.0, 1.4), K.at(0.0, 4.4)], SEAL, 0.8)
        K.oval(d, K.at(0.0, 6.2), 0.9, 0.9, SEAL)

    return K.piece(("kagero_slip", glow), shape)


#: Her talismans in the seal: a fan over her far hand. Five of them.
SPELL_SLIPS = 5


def _spell(ctx) -> List[Stamp]:
    """Her talismans: they fan out of her far hand in the seal and glow, and
    at the throw they fly out ahead of her (the game carries them on to the
    head)."""
    u, hand = ctx.u, ctx.far_hand
    out: List[Stamp] = []
    if 0.12 <= u < 0.5:
        f = min(1.0, (u - 0.12) / 0.2)
        glow = int(255 * min(1.0, max(0.0, (u - 0.25) / 0.2)))
        for k in range(SPELL_SLIPS):
            a = -90.0 + (k - (SPELL_SLIPS - 1) / 2.0) * 26.0 * f
            r = 5.0 + 9.0 * f
            at = (hand[0] + r * math.cos(math.radians(a)), hand[1] + r * math.sin(math.radians(a)))
            out.append((_slip(glow), pin(at), f"spell_{k}", a - 90.0))
    elif 0.5 <= u < 0.7:
        t = (u - 0.5) / 0.2
        for k in range(SPELL_SLIPS):
            spread = (k - (SPELL_SLIPS - 1) / 2.0) * 7.0 * (1.0 - 0.5 * t)
            at = (hand[0] + 8.0 + 34.0 * t + 3.0 * k * t, hand[1] + spread - 4.0 * math.sin(math.pi * t))
            out.append((_slip(220), pin(at), f"spell_{k}", -90.0 + spread * 2.0))
    return out


def _effects(ctx) -> List[Stamp]:
    out: List[Stamp] = []
    if ctx.anim == "cast":
        out += _spell(ctx)
    if ctx.anim in CUTS and ctx.i > 0:
        trail = _trail(ctx)
        if trail is not None:
            out.append((trail, pin(ctx.hand), "cut", 0.0))
    if ctx.anim in ("blink_in", "blink_out"):
        # Her smoke: thick at the blink, and gone as she stands (in) or is
        # gone (out).
        u = ctx.u if ctx.anim == "blink_in" else 1.0 - ctx.u
        alpha = int(220 * max(0.0, 1.0 - u * 1.3))
        if alpha > 8:
            for k, (dx, dy, r) in enumerate(((-16.0, -10.0, 12.0), (14.0, -22.0, 10.0), (-4.0, -40.0, 13.0), (10.0, -4.0, 9.0), (-14.0, -32.0, 8.0))):
                grow = 1.0 + 0.5 * u
                out.append((_smoke(r * grow, alpha), (ctx.hip[0] + dx * grow, ctx.hip[1] + dy), f"smoke_{k}", 0.0))
    return out


X.effects = _effects

ROWS = X.rows
_render_frame = X.render_frame
render, main, render_canonical = R.entry_points(X, ACTOR_METADATA, DISPLAY_NAME)


def render_portraits(out_dir, **opts):
    """Her portraits are frames of this sheet."""
    del opts
    return X.portraits(out_dir, {"default": ("idle", (1,), 0, False), "talking": ("idle", (0, 1, 2, 3, 4, 5, 6, 7), 120, True)}, view_width=30.0)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}

if __name__ == "__main__":
    raise SystemExit(main())
