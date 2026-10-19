"""Sprite generator for the Risen Conscript: a dead soldier of the regime,
raised in the lab of Castle Godwin. He is the first and the easiest enemy of
the castle.

The look (2026-10-18, Jon: "a Nazi Zombie enemy that is slow and lumbering
and a good easy enemy for the start"): a man of about 180 cm in the
grey-green uniform of the regime's rank and file, the same army as the
Fascist Enforcer, dead for a long time. Seen three quarters from the front
and facing right. He stoops; his head hangs forward and his jaw hangs open.
His skin is the grey of the dead, with bruises; his eyes are sunk in dark
sockets with a small dead glow in them; his near cheek is gone and his
teeth show through it. A dented steel helmet sits crooked on his head, its
strap loose. His tunic is torn and stained; the near sleeve is torn off at
the elbow and his thin bare forearm comes out of it. The regime's red
armband is still on his near arm (``_evil_faction``: an invented cog, not a
real symbol). Breeches and scuffed jackboots.

He reaches: his near arm is out in front of him, his far arm hangs. He
walks slowly and drags his far foot. He holds nothing. There is no drop
shadow.

His attacks are slow and easy to read: ``slash`` (both arms come up, then
down on you in a clumsy swipe) and ``attack_side`` (he lurches forward,
grabs and bites). ``taunt`` is a groan. ``emerge`` is how he gets up off the
floor.

He is a person of ``_person_rig``.
"""

from __future__ import annotations

import math
from typing import List

from ._ai_era_kit import OUTLINE, WHITE, RGBA, Point, lerp, mix
from . import _evil_faction as F
from . import _person_rig as R
from ._person_rig import Build, Person, Stamp, loop, shot

TARGET_NAME = "evil_zombie"
TARGET_BASENAME = TARGET_NAME
DISPLAY_NAME = "Risen Conscript"

TRAITS = ["story", "humanoid", "enemy", "combatant", "authoritarian", "soldier", "undead", "zombie", "slow"]

ACTOR_METADATA = {
    "actor": {"character_id": "npc_evil_zombie", "display_name": DISPLAY_NAME},
    "body": {"body_plan": "HumanoidBiped", "body_kind": "Standard", "mass_class": "Medium", "traits": TRAITS, "locomotion_hint": "Walk"},
    "capabilities": {
        "traversal": {"walk": True, "jump": None, "climb": None, "fly": None, "swim": None, "crawl": None, "use_lifts": None, "door_access": []},
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
                {"t": 0.5, "event": "hitbox_active_start", "source": "explicit.profile.combat_humanoid"},
                {"t": 0.7, "event": "hitbox_active_end", "source": "explicit.profile.combat_humanoid"},
            ],
        },
        "combat.hurt": {"animation": "hit", "events": []},
        "combat.death": {"animation": "death", "events": []},
        "ability.emerge": {"animation": "emerge", "events": []},
    },
    "authoring_description": (
        "A dead rank-and-file soldier of the Evil dimension's regime, raised in the castle lab: "
        "grey dead skin, sunk glowing eyes, a torn cheek, a dented steel helmet askew, a torn and "
        "stained grey-green tunic with the red armband (an invented cog; no real symbol), breeches "
        "and jackboots. He stoops, reaches with one arm and drags one foot."
    ),
    "gameplay_description": "A slow, weak shambler for the start of the castle: a clumsy two-arm swipe and a lunging bite, both telegraphed.",
    "dialogue_hints": {"barks": ["*a long, wet groan*", "Hhhrrr... or... ders...", "*teeth click*"]},
}

UNIFORM: RGBA = (98, 108, 90, 255)
UNIFORM_DARK: RGBA = (66, 74, 62, 255)
UNIFORM_LIGHT: RGBA = (128, 138, 118, 255)
BREECHES: RGBA = (88, 96, 82, 255)
BREECHES_DARK: RGBA = (58, 64, 56, 255)
COLLAR: RGBA = (48, 60, 50, 255)
STAIN: RGBA = (70, 52, 46, 255)
GRIME: RGBA = (84, 84, 70, 255)
BOOT: RGBA = (52, 48, 54, 255)
BOOT_DARK: RGBA = (30, 28, 34, 255)
SCUFF: RGBA = (98, 92, 92, 255)
SOLE: RGBA = (22, 20, 24, 255)
BELT: RGBA = (40, 34, 32, 255)
METAL: RGBA = (150, 148, 138, 255)
SKIN: RGBA = (178, 188, 184, 255)
SKIN_SHADE: RGBA = (138, 150, 150, 255)
SKIN_DEEP: RGBA = (74, 82, 90, 255)
BRUISE: RGBA = (118, 106, 128, 255)
SOCKET: RGBA = (34, 32, 40, 255)
GLOW: RGBA = (232, 236, 168, 255)
MOUTH: RGBA = (44, 26, 32, 255)
GUM: RGBA = (112, 70, 78, 255)
TOOTH: RGBA = (222, 214, 182, 255)
HELMET: RGBA = (92, 100, 92, 255)
HELMET_DARK: RGBA = (60, 66, 62, 255)
HELMET_LIGHT: RGBA = (140, 148, 138, 255)
RUST: RGBA = (130, 78, 52, 255)
STRAP: RGBA = (54, 42, 36, 255)
IMPACT: RGBA = (236, 240, 196, 255)
IMPACT_DARK: RGBA = (120, 132, 96, 255)
DUST: RGBA = (176, 170, 156, 255)
DUST_DARK: RGBA = (112, 106, 98, 255)

#: About 180 cm if he stood straight. He does not: ``height`` is the top of
#: his helmet as he stoops (measured on the idle row).
BUILD = Build(hip_up=52.0, thigh=25.4, shin=24.2, neck=(2.6, -37.4), upper=20.0, fore=19.4, near_shoulder=(-4.6, -33.4), far_shoulder=(6.6, -33.0),
              near_hip=(-3.8, 0.0), far_hip=(3.8, 0.0), head_up=(2.6, -12.4), throat=(-0.6, 4.2), height=110.0, half_width=(13.0, 16.0))

X = Person(TARGET_NAME, BUILD, frame=(224, 184), ground=172.0, cx=108.0)
K = X.K
P = X.P
TOP = BUILD.neck[1] - 2.0

# ---- The tunic ---------------------------------------------------------------


def _torso(hem_back: int, hem_front: int, drop=None):
    """His trunk in the torn tunic, from his hips, the spine up: a round
    back, a hem torn in points, holes with his dead skin in them."""
    del drop
    hb, hf = float(hem_back), float(hem_front)

    def shape(d) -> None:
        K.poly(d, [K.at(-4.6, TOP), K.at(-10.0, TOP + 4.0), K.at(-11.4, -22.0), K.at(-10.0, -4.0), K.at(-11.0 - hb, 11.6), K.at(-8.4, 13.4),
                   K.at(-6.2, 11.0), K.at(-3.4, 14.2), K.at(-0.4, 11.4), K.at(2.4, 13.0), K.at(5.0, 10.6), K.at(7.8, 13.6), K.at(10.6 + hf, 11.0),
                   K.at(10.4, -4.0), K.at(10.6, -16.0), K.at(10.6, -27.0), K.at(9.8, TOP + 3.0), K.at(5.0, TOP - 0.4)], WHITE)
        K.oval(d, K.at(-4.6, -33.4), 6.2, 6.6, WHITE)
        K.oval(d, K.at(4.4, -33.0), 5.6, 6.0, WHITE)

    def detail(d) -> None:
        # The far side is in shade.
        K.poly(d, [K.at(8.0, TOP - 2.0), K.at(30.0, TOP - 2.0), K.at(30.0, 20.0), K.at(8.6 + hf * 0.5, 20.0), K.at(7.4, -6.0)], UNIFORM_DARK)
        # A pocket, its flap hanging by one corner.
        K.rrect(d, -1.6, -29.0, 4.4, -21.6, 0.0, UNIFORM_DARK)
        K.rrect(d, -1.1, -28.5, 3.9, -22.1, 0.0, UNIFORM)
        K.poly(d, [K.at(-1.8, -29.0), K.at(1.0, -29.0), K.at(4.6, -25.6), K.at(3.6, -24.6), K.at(-1.8, -26.8)], UNIFORM_LIGHT)
        # The placket, buttons gone but two.
        K.line(d, [K.at(8.0, TOP + 3.0), K.at(8.6, -20.0), K.at(8.4 + hf * 0.4, 10.0)], UNIFORM_DARK, 0.6)
        for y in (-26.0, -12.0):
            K.oval(d, K.at(8.2, y), 0.75, 0.75, METAL, OUTLINE, 0.3)
        # A rip over his ribs: the dead skin and his ribs in it.
        rip = [K.at(-6.0, -20.0), K.at(-1.0, -19.0), K.at(2.4, -16.4), K.at(0.4, -12.6), K.at(-3.6, -13.4), K.at(-7.0, -15.0)]
        K.poly(d, rip, SKIN_SHADE)
        for y in (-17.6, -15.2):
            K.line(d, [K.at(-5.4, y), K.at(-2.0, y - 0.6), K.at(0.8, y + 0.2)], SKIN_DEEP, 0.55)
        K.line(d, rip + [rip[0]], UNIFORM_DARK, 0.5)
        # A hole lower down, and stains round it.
        K.oval(d, K.at(4.0, -1.2), 2.6, 1.8, STAIN)
        K.oval(d, K.at(3.6, -1.4), 1.3, 0.9, SOCKET)
        K.oval(d, K.at(-4.0, 6.0), 3.6, 2.4, mix(UNIFORM, STAIN, 0.45))
        K.oval(d, K.at(-7.0, -28.0), 2.6, 3.4, mix(UNIFORM, GRIME, 0.6))
        # The belt, slack: it sags in front, the buckle hangs.
        K.poly(d, [K.at(-30.0, -8.6), K.at(0.0, -8.0), K.at(30.0, -6.6), K.at(30.0, -2.4), K.at(0.0, -3.6), K.at(-30.0, -4.0)], BELT)
        K.rrect(d, 6.6, -7.8, 10.4, -2.6, 0.6, METAL, OUTLINE, 0.4)
        K.rrect(d, 7.6, -6.8, 9.4, -3.6, 0.3, mix(METAL, RUST, 0.5))
        # The seam down his back.
        K.line(d, [K.at(-10.0, TOP + 4.4), K.at(-11.0, -10.0)], UNIFORM_DARK, 0.5)

    return K.solid(("tunic", hem_back, hem_front), shape, UNIFORM, detail, outline=1.2, rim=0.25, shade=0.4, shade_colour=UNIFORM_DARK)


X.torso = _torso


def _collar():
    """His stand collar, open and bent, from the base of his neck."""

    def shape(d) -> None:
        K.poly(d, [K.at(-5.6, 1.4), K.at(-5.4, -3.4), K.at(-0.4, -4.4), K.at(3.6, -3.0), K.at(6.4, 1.6)], WHITE)

    def detail(d) -> None:
        K.poly(d, [K.at(0.6, -3.6), K.at(3.6, -3.0), K.at(5.2, 0.6), K.at(1.4, 0.6)], COLLAR)

    return K.solid(("collar",), shape, UNIFORM, detail, outline=1.1, rim=0.3, shade=0.3, shade_colour=UNIFORM_DARK)


X.collar = _collar
X.neck = R.make_neck(K, SKIN_SHADE, 6.6)

# ---- The head ----------------------------------------------------------------

NEAR_EYE = (2.4, -1.0)
FAR_EYE = (7.4, -1.2)


def _face(d) -> None:
    """The lines of a dead face: sunk cheeks, a bruise, the dark of the
    sockets, the hole in his near cheek and the teeth in it."""
    K.oval(d, K.at(-1.6, 3.4), 3.0, 2.4, mix(SKIN, BRUISE, 0.55))
    K.line(d, [K.at(4.8, 1.6), K.at(3.6, 5.0), K.at(4.6, 7.4)], SKIN_DEEP, 0.55)
    K.line(d, [K.at(-3.6, 5.0), K.at(-1.2, 9.8), K.at(2.2, 11.4)], mix(SKIN, SKIN_DEEP, 0.6), 0.6)
    # The sockets.
    K.oval(d, K.at(*NEAR_EYE), 3.0, 2.7, SOCKET)
    K.oval(d, K.at(FAR_EYE[0] + 0.2, FAR_EYE[1]), 2.2, 2.4, SOCKET)
    K.line(d, [K.at(-0.2, -3.4), K.at(2.6, -4.2), K.at(5.2, -3.0)], SKIN_DEEP, 0.7)
    # The torn cheek: gum and teeth, back to the hinge of the jaw.
    hole = [K.at(-0.6, 4.6), K.at(3.0, 4.0), K.at(4.4, 5.6), K.at(3.2, 8.2), K.at(-0.2, 7.6)]
    K.poly(d, hole, MOUTH)
    K.line(d, [K.at(-0.4, 5.4), K.at(4.0, 5.0)], GUM, 0.6)
    for x in (0.4, 1.6, 2.8):
        K.rrect(d, K.at(x, 0.0)[0] - 0.45, K.at(0.0, 5.2)[1], K.at(x, 0.0)[0] + 0.45, K.at(0.0, 6.6)[1], 0.2, TOOTH)
    K.line(d, hole + [hole[0]], SKIN_DEEP, 0.45)


_head = R.make_head(K, ("zombie",), SKIN, SKIN_SHADE, SKIN_DEEP, skull=(0.0, -2.6, 7.8, 9.0), jaw=(2.0, 4.8, 6.0, 6.8),
                    nose=((7.0, -1.6), (9.6, 2.8), (8.8, 4.0), (7.0, 4.4)), ear=(-4.8, 1.4, 2.0, 3.0), over=_face)


def _eyes(mode: str):
    """A small dead glow in each socket; none when he is down."""

    def paint(d) -> None:
        if mode in ("closed", "dead"):
            return
        for (ex, ey), r in ((NEAR_EYE, 1.0), (FAR_EYE, 0.8)):
            c = K.at(ex + 0.4, ey + 0.2)
            if mode == "wince":
                K.line(d, [(c[0] - 1.4 * r, c[1] - 0.3), (c[0] + 1.4 * r, c[1] + 0.3)], GLOW, 0.6)
                continue
            big = 1.3 if mode == "wide" else 1.0
            K.oval(d, c, 1.9 * r * big, 1.9 * r * big, mix(SOCKET, GLOW, 0.4))
            K.oval(d, c, 1.15 * r * big, 1.15 * r * big, GLOW)

    return K.piece(("eyes", mode), paint)


def _open(mouth: str) -> float:
    return {"big": 5.6, "open": 3.6, "o": 2.8, "grit": 0.6}.get(mouth, 2.2)


def _jaw(mouth: str):
    """His lower jaw, from the middle of his head: it hangs open, more for a
    groan or a bite."""
    drop = _open(mouth)

    def shape(d) -> None:
        K.poly(d, [K.at(0.6, 6.4), K.at(8.4, 5.6 + drop * 0.5), K.at(8.0, 8.0 + drop), K.at(5.0, 10.8 + drop), K.at(1.4, 10.2 + drop * 0.6),
                   K.at(-1.6, 7.8)], WHITE)

    def detail(d) -> None:
        # The mouth between the jaws, and his lower teeth.
        K.poly(d, [K.at(4.2, 5.0), K.at(9.0, 4.6), K.at(8.6, 5.8 + drop * 0.5), K.at(4.4, 6.6 + drop * 0.3)], MOUTH)
        for x in (5.4, 6.8):
            K.poly(d, [K.at(x - 0.5, 6.6 + drop * 0.4), K.at(x, 5.4 + drop * 0.4), K.at(x + 0.5, 6.5 + drop * 0.4)], TOOTH)
        K.line(d, [K.at(1.4, 9.0 + drop * 0.5), K.at(5.0, 9.8 + drop)], SKIN_DEEP, 0.5)

    return K.solid(("jaw", round(drop, 1)), shape, SKIN_SHADE, detail, outline=1.1, rim=0.2, shade=0.3, shade_colour=SKIN_DEEP)


def _upper_mouth():
    """The dark of his open mouth under his top lip, and his top teeth."""

    def paint(d) -> None:
        K.poly(d, [K.at(4.0, 4.6), K.at(8.8, 4.2), K.at(9.0, 5.6), K.at(4.4, 6.0)], MOUTH)
        for x in (5.6, 7.2):
            K.poly(d, [K.at(x - 0.5, 4.6), K.at(x, 5.8), K.at(x + 0.5, 4.6)], TOOTH)

    return K.piece(("upper_mouth",), paint)


#: The helmet sits back on his head, up off his brow, so his eyes show.
HELMET_AT = (-0.8, -1.8)


def H(x: float, y: float) -> Point:
    return K.at(x + HELMET_AT[0], y + HELMET_AT[1])


def _helmet():
    """His steel helmet, from the middle of his head: a deep dome, a short
    brim over his brow, a skirt that flares out over his ear and his neck. It
    sits crooked, back on his head; it is dented and its paint is gone in
    places. A loose chin strap hangs from it."""

    def shape(d) -> None:
        K.oval(d, H(-1.0, -8.0), 10.2, 7.6, WHITE)
        K.poly(d, [H(-11.2, -6.0), H(-10.6, 1.0), H(-13.4, 4.6), H(-8.6, 4.4), H(-5.4, -0.6), H(0.0, -2.6), H(6.4, -3.4),
                   H(10.6, -2.6), H(10.4, -6.0)], WHITE)

    def detail(d) -> None:
        # The rim, round the skirt and the brim.
        K.line(d, [H(-13.0, 4.0), H(-8.8, 3.8), H(-5.4, -1.2), H(0.0, -3.2), H(6.4, -4.0), H(10.4, -3.4)], HELMET_DARK, 0.9)
        K.line(d, [H(-11.0, 1.0), H(-8.0, -1.4), H(-6.0, -4.8)], HELMET_DARK, 0.6)
        # The light on the dome.
        K.line(d, [H(-7.4, -11.6), H(-2.6, -14.0), H(3.0, -13.6)], HELMET_LIGHT, 0.8)
        # A dent, and a scrape to the bare steel.
        K.line(d, [H(3.0, -11.6), H(5.2, -9.4), H(5.0, -7.0)], HELMET_DARK, 0.8)
        K.line(d, [H(3.8, -11.8), H(6.0, -9.6)], HELMET_LIGHT, 0.4)
        K.line(d, [H(-4.0, -8.0), H(-0.6, -9.6)], METAL, 0.5)
        K.oval(d, H(-8.4, -4.0), 1.6, 1.2, mix(HELMET, RUST, 0.6))
        K.oval(d, H(1.2, -5.2), 1.0, 0.8, mix(HELMET, RUST, 0.5))
        # The regime's mark on its side, faded.
        K.oval(d, H(-4.0, -7.4), 2.6, 2.6, mix(HELMET, F.DISC, 0.55))
        F.cog(K, d, H(-4.0, -7.4), 2.0, mix(HELMET, F.COG, 0.55), mix(HELMET, F.DISC, 0.55))

    return K.solid(("helmet",), shape, HELMET, detail, outline=1.2, rim=0.3, shade=0.35, shade_colour=HELMET_DARK)


def _strap():
    """The chin strap, loose: it hangs from the skirt by his ear."""

    def paint(d) -> None:
        K.line(d, [K.at(-6.6, 2.4), K.at(-5.4, 7.4), K.at(-3.0, 10.6)], OUTLINE, 1.3)
        K.line(d, [K.at(-6.6, 2.4), K.at(-5.4, 7.4), K.at(-3.0, 10.6)], STRAP, 0.7)
        K.oval(d, K.at(-3.0, 10.6), 0.8, 0.8, METAL, OUTLINE, 0.3)

    return K.piece(("strap",), paint)


def _head_layers(pose):
    mouth = str(pose["mouth"])
    return [(_strap(), "strap"), (_jaw(mouth), "jaw"), (_head(), "head"), (_upper_mouth(), "upper_mouth"), (_eyes(str(pose["eyes"])), "eyes"),
            (_helmet(), "helmet")]


X.head_layers = _head_layers

# ---- The limbs ---------------------------------------------------------------

#: The near sleeve is torn off at the elbow: the forearm under it is bare.
X.upper_arm = lambda near: [(0.0, 1.0, 8.2, 7.4, UNIFORM if near else UNIFORM_DARK)]
X.forearm = lambda near: ([(0.0, 1.0, 5.2, 4.6, SKIN_SHADE), (0.0, 0.16, 7.8, 6.6, UNIFORM)] if near
                          else [(0.0, 0.86, 7.2, 6.4, UNIFORM_DARK), (0.84, 1.0, 5.0, 4.6, SKIN_DEEP)])
X.thigh = lambda near: [(0.0, 0.5, 9.4, 10.4, BREECHES if near else BREECHES_DARK), (0.5, 1.0, 10.4, 7.4, BREECHES if near else BREECHES_DARK)]
X.shin = lambda near: [(0.0, 0.14, 7.4, 7.0, BREECHES if near else BREECHES_DARK), (0.12, 1.0, 8.2, 7.0, BOOT if near else BOOT_DARK),
                       (0.3, 0.6, 1.8, 1.4, SCUFF if near else BOOT)]
X.hand = R.make_hand(K, SKIN, SKIN_SHADE, SKIN_DEEP, size=1.1)
X.shoe = R.make_shoe(K, BOOT, BOOT_DARK, BUILD.ankle_up, long=1.1, sole=SOLE, heel=0.8)


def _armband(ctx) -> List[Stamp]:
    """The band and its emblem on his near arm; they turn with the arm."""
    if ctx.pose["arm"] == "under":
        return []
    t = 0.36
    at = (lerp(ctx.shoulder[0], ctx.elbow[0], t), lerp(ctx.shoulder[1], ctx.elbow[1], t))
    turn = math.degrees(math.atan2(ctx.elbow[1] - ctx.shoulder[1], ctx.elbow[0] - ctx.shoulder[0]))
    return [(F.band(K, 9.0), at, "armband", turn), (F.emblem(K, 2.3), at, "armband_emblem", 0.0)]


def _torn_cuff(ctx) -> List[Stamp]:
    """The torn end of his near sleeve, ragged round the elbow."""
    if ctx.pose["arm"] == "under":
        return []
    turn = math.degrees(math.atan2(ctx.hand[1] - ctx.elbow[1], ctx.hand[0] - ctx.elbow[0]))
    return [(_rag(), ctx.elbow, "torn_sleeve", turn)]


def _rag():
    def shape(d) -> None:
        K.poly(d, [K.at(-1.0, -4.4), K.at(3.0, -4.0), K.at(4.4, -2.4), K.at(2.8, -1.0), K.at(5.0, 0.6), K.at(3.0, 2.0), K.at(4.0, 3.8),
                   K.at(-1.0, 4.4)], WHITE)

    return K.solid(("rag",), shape, UNIFORM, None, outline=1.0, rim=0.2, shade=0.3, shade_colour=UNIFORM_DARK)


X.layers["front"] += [_torn_cuff, _armband]

# ---- How he stands -----------------------------------------------------------

#: Stooped, his head hanging forward, his near arm out in front of him and
#: his far arm hanging.
REACH = (21.0, 10.0)
HANG = (5.0, 25.0)
X.set_rest(hip=(0.0, 2.0), lean=14.0, head=(3.0, 2.0, 6.0), na=REACH, fa=HANG, nh="soft", fh="soft", nf=(-6.0, 0.0, 0.0), ff=(6.0, 0.0, 0.0),
           mouth="flat", shrug=(0.0, -1.2))


@X.row
def idle(i: int, n: int):
    # He sways on his feet; his head rolls and drops, and his reaching hand
    # sinks and comes up again.
    _, s, c = loop(i, n)
    return P(hip=(0.8 * s, 2.0 + 0.6 * c), lean=14.0 + 2.0 * s, head=(3.0, 2.0, 6.0 + 5.0 * c), na=(REACH[0] - 1.0 * s, REACH[1] + 2.0 * c),
             fa=(HANG[0] + 1.0 * s, HANG[1]), mouth="open" if i in (5, 6) else "flat")


def _lurch(ph: float):
    """One slow step of his: the near foot steps, the far foot drags up
    behind it with its toe down. All of him drops onto the near leg."""
    s, c = math.sin(ph), math.cos(ph)
    near_up = max(0.0, -s)
    near = (-1.0 + 7.0 * c, -5.0 * near_up, 18.0 * near_up * max(0.0, -c) - 10.0 * max(0.0, c) * (1.0 if s < 0.0 else 0.3))
    # The far foot slides: it never lifts more than a little, and its toe
    # drags along the floor.
    far = (1.0 - 7.0 * c, -0.8 * max(0.0, s), 16.0 * max(0.0, s))
    return near, far


@X.row
def walk(i: int, n: int):
    ph, s, c = loop(i, n)
    nf, ff = _lurch(ph)
    # He drops when his weight comes onto his near leg, and rocks forward.
    drop = 2.6 * max(0.0, c) + 0.6
    return P(
        hip=(0.6 * c, 2.0 + drop), lean=15.0 + 4.0 * max(0.0, c) - 2.0 * s, head=(3.0, 2.0, 6.0 + 5.0 * math.sin(ph - 0.9)),
        na=(REACH[0] - 2.0 * c, REACH[1] + 2.0 * math.sin(ph - 0.6)), fa=(HANG[0] + 3.0 * s, HANG[1]), nf=nf, ff=ff, hem=(1.0 + max(0.0, c), 0.5),
        mouth="open" if i == 3 else "flat")


@X.row
def run(i: int, n: int):
    # His "run" is a faster lurch, both arms up and out for you.
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 8.0, 3.0)
    return P(hip=(1.0, 3.0 + 1.6 * abs(math.cos(ph))), lean=18.0 + 2.0 * c, head=(1.6, 1.4, 6.0 + 4.0 * s), na=(REACH[0] + 2.0, 6.0 + 2.0 * s),
             fa=(REACH[0] - 2.0, 9.0 - 2.0 * s), nh="open", fh="open", nf=nf, ff=ff, hem=(2.0, 1.0), mouth="open")


RISE = P(hip=(0.0, -2.0), lean=6.0, head=(1.0, 1.0, 4.0), na=(14.0, -4.0), fa=(10.0, 4.0), nh="open", fh="open", nf=(-5.0, -8.0, 20.0),
         ff=(6.0, -6.0, 14.0), mouth="open")
FALL = P(hip=(0.0, -3.0), lean=-2.0, head=(0.0, 0.0, 8.0), na=(16.0, -6.0), fa=(12.0, -2.0), nh="open", fh="open", nf=(-6.0, -3.0, 18.0),
         ff=(6.0, -6.0, 12.0), mouth="big", hem=(3.0, 3.0))


@X.row
def jump(i: int, n: int):
    wind = P(hip=(0.0, 9.0), lean=20.0, head=(1.6, 1.4, 16.0), na=(18.0, 14.0), fa=(6.0, 22.0))
    return X.keys(shot(i, n), [(0.0, wind), (0.4, RISE), (1.0, RISE)])


@X.row
def fall(i: int, n: int):
    _, s, c = loop(i, n)
    return dict(FALL, na=(16.0 + s, -6.0 + 2.0 * c), fa=(12.0 - s, -2.0 - 2.0 * c))


#: Both arms up over his head, for the swipe.
ARMS_UP = P(hip=(-2.0, 1.0), lean=-4.0, head=(0.6, 0.6, -6.0), na=(8.0, -26.0), nab=-1.0, fa=(12.0, -24.0), fab=-1.0, arm="under", nh="open",
            fh="open", nf=(-8.0, 0.0, 0.0), ff=(7.0, 0.0, 0.0), mouth="big")
#: Both arms down through you, all of him falling after them.
ARMS_DOWN = P(hip=(5.0, 7.0), lean=36.0, head=(2.0, 1.0, 10.0), na=(18.0, 20.0), fa=(14.0, 22.0), nh="open", fh="open", nf=(-10.0, 0.0, 0.0),
              ff=(10.0, 0.0, 0.0), mouth="big", hem=(3.0, 1.0))


@X.row
def slash(i: int, n: int):
    # Slow to start (the tell): the arms come up, he holds, then they fall.
    return X.keys(shot(i, n), [(0.0, X.full(P())), (0.3, ARMS_UP), (0.45, dict(ARMS_UP, lean=-7.0)), (0.6, ARMS_DOWN, "out"), (0.8, ARMS_DOWN),
                               (1.0, X.full(P()))], drag={"head": 0.08})


#: Lunged forward, his arms round you, his teeth at you.
GRAB = P(hip=(8.0, 6.0), lean=30.0, head=(3.0, 1.0, -4.0), na=(24.0, 2.0), fa=(22.0, 6.0), nh="open", fh="open", nf=(-12.0, 0.0, 20.0),
         ff=(12.0, 0.0, 0.0), mouth="big", hem=(4.0, 0.0))


@X.row
def attack_side(i: int, n: int):
    # He leans back, lunges with both arms, and bites.
    back = P(hip=(-3.0, 3.0), lean=2.0, head=(0.6, 0.6, -8.0), na=(14.0, 0.0), fa=(10.0, 6.0), nh="open", fh="open", mouth="big")
    bite = dict(GRAB, head=(3.6, 1.6, 6.0), mouth="grit")
    return X.keys(shot(i, n), [(0.0, X.full(P())), (0.25, back), (0.45, GRAB, "out"), (0.6, bite), (0.72, GRAB), (0.84, bite), (1.0, X.full(P()))])


STRUCK = P(hip=(-4.0, 3.0), lean=-12.0, head=(-1.6, 0.0, -24.0), na=(12.0, -6.0), fa=(10.0, 16.0), nh="open", fh="soft", nf=(-8.0, 0.0, 0.0),
           ff=(8.0, -3.0, -14.0), eyes="wince", mouth="big", off=(-3.0, 0.0), hem=(0.0, 3.0))


@X.row
def hit(i: int, n: int):
    # His head snaps back and comes forward again, late.
    return X.keys(shot(i, n), [(0.0, X.full(P())), (0.25, STRUCK), (0.55, STRUCK), (1.0, X.full(P()))], drag={"head": 0.12})


#: Face down on the floor, his arms out past his head.
PRONE = P(rot=90.0, hip=(2.0, 24.5), off=(-16.0, 0.0), lean=0.0, head=(0.0, 0.0, -10.0), na=(-6.0, -24.0), nab=-1.0, fa=(-2.0, -25.0), fab=-1.0,
          arm="under", nh="flat", fh="flat",
          nf=(-4.5, 24.0, 0.0), ff=(4.5, 24.0, 10.0), eyes="dead", mouth="open")
#: On his knees, sagging forward.
KNEEL = P(hip=(1.0, 17.0), lean=28.0, head=(1.4, 1.4, 24.0), na=(8.0, 22.0), fa=(4.0, 24.0), nh="soft", fh="soft", nf=(-18.0, -4.0, 100.0),
          ff=(8.0, 0.0, 0.0), eyes="dead", mouth="open", hem=(1.0, 2.0))


@X.row
def death(i: int, n: int):
    # His knees go, and he falls on his face.
    falling = X.blend(KNEEL, PRONE, 0.5)
    # Half way over he is up off the floor: his knees take his weight.
    falling = dict(falling, eyes="dead", off=(falling["off"][0], falling["off"][1] - 13.0))
    return X.keys(shot(i, n), [(0.0, STRUCK), (0.3, KNEEL), (0.5, falling), (0.65, PRONE), (1.0, PRONE)])


@X.row
def emerge(i: int, n: int):
    # Up off the floor: on his knees, a hand on the floor, a hand reaching,
    # then he stands, and his head comes up last.
    low = P(hip=(1.0, 17.0), lean=48.0, head=(2.0, 1.0, 20.0), na=(16.0, 22.0), fa=(10.0, 28.0), nh="flat", fh="flat", nf=(-18.0, -4.0, 100.0),
            ff=(8.0, 0.0, 0.0), eyes="closed", mouth="flat", hem=(1.0, 2.0))
    push = dict(low, hip=(1.0, 14.0), lean=32.0, na=REACH, nh="soft", eyes="open", nf=(-14.0, -2.0, 60.0))
    return X.keys(shot(i, n), [(0.0, low), (0.3, push), (0.65, dict(X.full(P()), lean=20.0)), (1.0, X.full(P()))], drag={"head": 0.15})


#: His head back, his jaw open for the groan.
GROAN = P(hip=(0.0, 2.0), lean=4.0, head=(0.6, 0.0, -22.0), na=(16.0, 4.0), fa=(8.0, 20.0), nh="open", fh="soft", mouth="big", shrug=(0.0, -2.4))


@X.row
def taunt(i: int, n: int):
    return X.keys(shot(i, n), [(0.0, X.full(P())), (0.3, GROAN), (0.5, dict(GROAN, head=(0.6, 0.0, -26.0))), (0.7, GROAN), (1.0, X.full(P()))])


X.rows = [("idle", 8, 170), ("walk", 10, 135), ("run", 8, 100), ("jump", 6, 100), ("fall", 6, 100), ("slash", 10, 95), ("attack_side", 10, 85),
          ("hit", 5, 100), ("death", 8, 130), ("emerge", 10, 120), ("taunt", 10, 120)]

# ---- What his blows do -------------------------------------------------------


def _effects(ctx) -> List[Stamp]:
    out: List[Stamp] = []
    anim, u = ctx.anim, ctx.u
    if anim == "slash" and 0.5 <= u <= 0.72:
        now = math.degrees(math.atan2(ctx.hand[1] - ctx.shoulder[1], ctx.hand[0] - ctx.shoulder[0]))
        old = max(-100.0, now - 70.0)
        reach = math.dist(ctx.shoulder, ctx.hand) + 6.0
        out.append((R.swoosh(K, round(reach), int(round(old)), int(round(now)), 3.0, IMPACT, IMPACT_DARK), ctx.shoulder, "swipe_trail", 0.0))
    elif anim == "attack_side" and 0.56 <= u <= 0.88 and ctx.pose["mouth"] == "grit":
        tip: Point = (ctx.head[0] + 11.0, ctx.head[1] + 6.0)
        out.append((R.burst(K, 7.0, IMPACT, IMPACT_DARK, 8), tip, "bite", 0.0))
    elif anim == "death" and 0.6 <= u <= 0.9:
        out.append((R.dust(K, 4.0, DUST, DUST_DARK), (ctx.head[0] + 6.0, ctx.ground - 3.0), "dust_ahead", 0.0))
        out.append((R.dust(K, 3.4, DUST, DUST_DARK), (ctx.hip[0] - 4.0, ctx.ground - 3.0), "dust_behind", 0.0))
    elif anim == "hit" and u <= 0.5:
        out.append((R.burst(K, 9.0, IMPACT, IMPACT_DARK, 8), (ctx.head[0] + 10.0, ctx.head[1] - 2.0), "struck", 0.0))
    return out


X.effects = _effects

ROWS = X.rows
FRAME_SIZE = X.frame
_render_frame = X.render_frame
render, main, render_canonical = R.entry_points(X, ACTOR_METADATA, DISPLAY_NAME)


def render_portraits(out_dir, **opts):
    """His portraits are frames of this sheet."""
    del opts
    return X.portraits(out_dir, {"default": ("idle", (1,), 0, False), "talking": ("taunt", (2, 3, 4, 5, 6, 7), 120, True)}, view_width=38.0)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}

if __name__ == "__main__":
    raise SystemExit(main())
