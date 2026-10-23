"""Sprite generator for the Shadow Duelist: the blade of the Shadow Dojo.

The look (2026-10-13, a redraw: Jon, "I also want to redo the shadow dualist
art"): a lean swordsman of 170 cm, seen three quarters from the front, facing
right. He is of the same dojo as the Ninja Heavy and he is its opposite: the
heavy is a wall, and he is a line.

He is black from his head to his feet, as the Ninja Heavy is (Jon,
2026-10-13, of the heavy: "Less skin, I like the dark clad in black look"),
and his eyes are those of the picture the ninjas of the game come from: two
red lights in the dark slit of his hood. He shows no skin. He was grey for
one draft, as the ninjas of that picture are; Jon: "Revert the shadow duelist
colors to the darker ones, but I like the new darker eyes."

What makes him the duelist: the long sword, which is the one bright thing he
has; its black scabbard at his far hip; and the long red scarf at his neck,
whose two ends say how fast he goes. There is no drop shadow.

A pose that is held keeps the sword off his face: in his guard his hands are
in front of his belly and the point is in front of him, at the height of his
throat.

The rows are the ones a striker of the game plays: ``idle`` (his guard),
``walk``, ``run`` (the sword behind him), ``jump``, ``fall``, ``slash`` (one
cut, from over his far shoulder to low in front of him), ``hit``, ``death``,
``dash``, ``front`` (he faces you: the row he turns through), and the two poses of a blink: ``blink_out`` (the sign of the hand
before he is gone) and ``blink_in`` (he comes back low). The warp of a blink
is the engine's; these two rows are only how he stands for it.

He is a person of ``_person_rig``: the bones, the poses and the frame are
shared; the head, the clothes, the sword and how he stands are his.

The other blades of the dojo (Jon, 2026-10-23: "Also make ninja variants
that were like the originals you made where they had normal eyes and skin
showing. I like the red eye ninjas too, but I want a few variants"). Each is
a ``Look`` of this module, a sheet of its own, with his bones and his poses:

``ninja_shadow_duelist_eye_band`` (Ninja Swordsman)
    The duelist's first black draft (renderer ``22e5258``): a band of skin
    in the hood, his own eyes and set brows, the red scarf and the katana.
``ninja_shadow_duelist_blue_scarf`` (Blue Scarf Duelist)
    The band of skin and his eyes; the scarf, the sash and the cords in
    blue where the dojo has red; a straight blade with a square guard.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Dict, List, Tuple

from ._ai_era_kit import OUTLINE, WHITE, RGBA, pin
from . import _person_rig as R
from ._person_rig import Build, Person, Stamp, loop, shot

TARGET_NAME = "ninja_shadow_duelist"
TARGET_BASENAME = TARGET_NAME
DISPLAY_NAME = "Shadow Duelist"

ACTOR_METADATA = {
    "actor": {"character_id": "npc_ninja_shadow_duelist", "display_name": "Shadow Duelist"},
    "lineage": {
        "family": "npc_ninja_shadow_duelist",
        "variant": "the_line",
        "parents": ["npc_ninja_shadow_duelist/moon_steel"],
        "creator": {
            "kind": "model",
            "model": "Claude Opus 5.5",
        },
        "method": "person_rig",
        "revision": "first_draft",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": ["story", "humanoid", "enemy", "combatant", "ninja", "duelist", "masked"],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": None,
            "climb": None,
            "fly": None,
            "swim": None,
            "crawl": None,
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
    "brain": {"default_preset": "melee_brute_striker"},
    "actions": {"default_preset": "striker_swipe"},
    "visual": {"default_pose": "idle"},
    "tags": ["story", "humanoid", "enemy", "combatant", "ninja", "duelist", "masked"],
    "sockets": {
        "head": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 64.0, "y": 24.0},
        },
        "chest": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 64.0, "y": 54.0},
        },
        "hand_l": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 48.0, "y": 64.0},
        },
        "hand_r": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 80.0, "y": 64.0},
        },
        "speech_bubble": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 64.0, "y": 8.0},
        },
        "weapon_grip": {
            "source": "explicit.profile.combat_humanoid",
            "point": {"x": 80.0, "y": 64.0},
        },
        "weapon_tip": {
            "source": "explicit.profile.combat_humanoid",
            "point": {"x": 104.0, "y": 60.0},
        },
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "action.melee.primary": {
            "animation": "slash",
            "events": [
                {
                    "t": 0.34,
                    "event": "hitbox_active_start",
                    "source": "explicit.profile.combat_humanoid",
                },
                {
                    "t": 0.58,
                    "event": "hitbox_active_end",
                    "source": "explicit.profile.combat_humanoid",
                },
            ],
        },
    },
}


#: The black of the dojo, as the Ninja Heavy has it: a little blue in it, so
#: its folds and its edges can be seen.
GI: RGBA = (32, 34, 48, 255)
GI_DARK: RGBA = (17, 18, 28, 255)
GI_LIGHT: RGBA = (64, 70, 98, 255)
HOOD: RGBA = (27, 29, 42, 255)
HOOD_DARK: RGBA = (14, 15, 24, 255)
SLEEVE: RGBA = (38, 41, 58, 255)
SLEEVE_DARK: RGBA = (22, 24, 36, 255)
GLOVE: RGBA = (44, 46, 62, 255)
GLOVE_DARK: RGBA = (20, 21, 32, 255)
WRAP: RGBA = (52, 55, 74, 255)
WRAP_DARK: RGBA = (30, 32, 46, 255)
#: The slit of his hood is in shadow, darker than its cloth, and his eyes are
#: red lights in it.
SLIT: RGBA = (8, 7, 12, 255)
EYE: RGBA = (232, 34, 40, 255)
EYE_HOT: RGBA = (255, 138, 110, 255)
#: The red of the dojo: his scarf, the cord of his scabbard, the wrap of his grip.
RED: RGBA = (176, 44, 48, 255)
RED_DARK: RGBA = (112, 26, 34, 255)
RED_LIGHT: RGBA = (214, 84, 76, 255)
STEEL: RGBA = (226, 232, 240, 255)
STEEL_DARK: RGBA = (150, 160, 180, 255)
STEEL_LIGHT: RGBA = (255, 255, 255, 255)
BRASS: RGBA = (222, 176, 84, 255)
BRASS_DARK: RGBA = (150, 104, 44, 255)
LACQUER: RGBA = (24, 24, 34, 255)
LACQUER_LIGHT: RGBA = (70, 76, 104, 255)
INK: RGBA = (24, 22, 30, 255)
CUT: RGBA = (236, 242, 250, 255)
CUT_DARK: RGBA = (150, 164, 190, 255)
DUST: RGBA = (196, 190, 196, 255)
DUST_DARK: RGBA = (120, 116, 132, 255)
#: The skin of the blades who show it (his first draft, renderer ``22e5258``).
SKIN: RGBA = (214, 164, 124, 255)
SKIN_SHADE: RGBA = (178, 124, 94, 255)
SKIN_DEEP: RGBA = (128, 80, 68, 255)
IRIS: RGBA = (70, 50, 44, 255)
#: The blue of the Blue Scarf Duelist, where the dojo has its red.
BLUE: RGBA = (58, 104, 176, 255)
BLUE_DARK: RGBA = (32, 58, 116, 255)
BLUE_LIGHT: RGBA = (112, 156, 220, 255)

#: 170 cm (168 cm is 108 pixels), and lean.
BUILD = Build(hip_up=48.6, thigh=23.7, shin=22.7, neck=(1.0, -36.4), near_shoulder=(-5.6, -32.4), far_shoulder=(7.0, -32.0), height=109.3,
              half_width=(12.0, 14.0))

#: How long the blade is past its guard, and how long the grip is: the guard
#: is ``GUARD_AT`` in front of his near hand, and the end of the grip is
#: ``BUTT`` behind it (his far hand is there in a hold of two hands).
BLADE = 47.0
GUARD_AT = 3.4
BUTT = 9.0


def lerp_(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


@dataclass(frozen=True)
class Look:
    """What one blade of the dojo wears. His bones and his poses are the
    same for all of them.

    ``face``: ``"slit"``, two red lights in the dark slit of the hood; or
    ``"band"``, a band of skin in the hood with his own eyes and set brows.
    ``accent``: the colour of the dojo on him (his scarf, his sash, the cords
    of his sword and its scabbard, his soles), its shade and its light.
    ``sword``: ``"katana"`` (a curved blade, a round guard) or ``"ninjato"``
    (a straight blade, a square guard)."""

    target: str
    display_name: str
    variant: str
    parents: Tuple[str, ...]
    face: str = "slit"
    accent: Tuple[RGBA, RGBA, RGBA] = (RED, RED_DARK, RED_LIGHT)
    sword: str = "katana"


LOOKS: Dict[str, Look] = {
    look.target: look
    for look in (
        Look(TARGET_NAME, DISPLAY_NAME, "the_line", ("npc_ninja_shadow_duelist/moon_steel",)),
        Look("ninja_shadow_duelist_eye_band", "Ninja Swordsman", "first_line", ("npc_ninja_shadow_duelist/the_line",), face="band"),
        Look("ninja_shadow_duelist_blue_scarf", "Blue Scarf Duelist", "blue_line", ("npc_ninja_shadow_duelist/the_line",), face="band",
             accent=(BLUE, BLUE_DARK, BLUE_LIGHT), sword="ninjato"),
    )
}


def _metadata(look: Look) -> dict:
    """The actor metadata of ``look``: the duelist's, with its own name."""
    if look.target == TARGET_NAME:
        return ACTOR_METADATA
    lineage = dict(ACTOR_METADATA["lineage"], variant=look.variant, parents=list(look.parents))
    return dict(ACTOR_METADATA, actor={"character_id": f"npc_{look.target}", "display_name": look.display_name}, lineage=lineage)


def _make(look: Look) -> SimpleNamespace:
    """The person of ``look``, and the entry points of its sheet."""
    X = Person(look.target, BUILD, frame=(240, 192), ground=180.0, cx=112.0)
    K = X.K
    P = X.P
    U = X.U
    band = look.face == "band"
    straight = look.sword == "ninjato"
    RED, RED_DARK, RED_LIGHT = look.accent

    def _front(d, hb: float, hf: float) -> None:
        """The cross of his gi and the red under it, his sash and its knot."""
        top = -38.0
        K.poly(d, [K.at(-2.4, top), K.at(0.0, top - 0.8), K.at(8.6, -19.0), K.at(6.4, -18.4)], RED)
        K.poly(d, [K.at(-4.6, top + 1.0), K.at(-2.4, top), K.at(6.4, -18.4), K.at(4.4, -17.6)], GI_LIGHT)
        K.poly(d, [K.at(7.0, top + 2.0), K.at(8.6, top + 3.6), K.at(5.6, -26.0), K.at(4.2, -27.2)], GI_LIGHT)
        # The sash: wide, in the dark red, round his middle; and the ends of its
        # knot at his near hip.
        K.poly(d, [K.at(-30.0, -13.0), K.at(30.0, -11.6), K.at(30.0, -5.6), K.at(-30.0, -7.0)], RED_DARK)
        K.line(d, [K.at(-30.0, -10.4), K.at(30.0, -9.0)], RED, 0.7)
        K.poly(d, [K.at(-3.6, -8.0), K.at(0.0, -8.4), K.at(0.6, 3.6), K.at(-2.6, 4.4)], RED_DARK, OUTLINE, 0.5)
        K.poly(d, [K.at(-6.6, -8.0), K.at(-3.4, -8.2), K.at(-4.6, 1.6), K.at(-7.4, 1.0)], RED, OUTLINE, 0.5)
        K.oval(d, K.at(-3.4, -8.8), 2.2, 2.0, RED, OUTLINE, 0.5)
        # The folds of the gi, and the edge of its short skirt.
        K.line(d, [K.at(-5.4, -29.0), K.at(-4.0, -16.0)], GI_DARK, 0.6)
        K.line(d, [K.at(4.4, -4.0), K.at(5.6 + hf * 0.5, 8.0)], GI_DARK, 0.6)
        K.poly(d, [K.at(-30.0 - hb, 6.6), K.at(30.0 + hf, 6.6), K.at(30.0 + hf, 8.6), K.at(-30.0 - hb, 8.6)], GI_LIGHT)

    X.torso = R.make_torso(K, ("duelist",), GI, GI_DARK, back=(8.2, 8.6, 6.8, 8.0), front=(7.2, 8.8, 7.4, 8.4), hem_y=9.0, shoulders=((-5.2, -31.6), (5.6, -31.2)),
                           shoulder_r=(4.8, 4.4), neck=(-3.6, 3.6), shade_from=6.6, detail=_front)

    NEAR_EYE = (1.8, -0.6)
    FAR_EYE = (6.8, -0.8)

    def _hood_shape(d) -> None:
        # The hood is close on his head; its knot is at the back.
        K.oval(d, K.at(-0.4, -2.6), 8.8, 9.6, WHITE)
        K.oval(d, K.at(2.4, 4.2), 6.0, 7.6, WHITE)
        K.poly(d, [K.at(-7.6, -2.0), K.at(-12.0, 0.6), K.at(-11.6, 3.6), K.at(-7.6, 2.0)], WHITE)

    def _hood(d) -> None:
        # All of it is cloth but the slit at his eyes, and the slit is in shadow.
        K.poly(d, [K.at(-30.0, -30.0), K.at(30.0, -30.0), K.at(30.0, -4.4), K.at(9.0, -4.4), K.at(3.6, -4.8), K.at(-0.8, -3.8), K.at(-1.8, -0.8), K.at(-1.2, 1.8),
                   K.at(3.6, 2.4), K.at(10.0, 2.0), K.at(30.0, 2.0), K.at(30.0, 30.0), K.at(-30.0, 30.0)], HOOD)
        K.line(d, [K.at(9.0, -4.4), K.at(3.6, -4.8), K.at(-0.8, -3.8), K.at(-1.8, -0.8), K.at(-1.2, 1.8), K.at(3.6, 2.4), K.at(10.0, 2.0)], HOOD_DARK, 0.7)
        # The folds of it, and the cloth over his nose and his mouth.
        K.line(d, [K.at(-5.6, -9.0), K.at(-7.4, -1.0), K.at(-6.0, 7.0)], HOOD_DARK, 0.6)
        K.line(d, [K.at(0.0, 4.6), K.at(3.8, 7.0), K.at(8.0, 6.0)], HOOD_DARK, 0.6)
        K.line(d, [K.at(-1.0, 8.0), K.at(3.2, 10.2), K.at(6.8, 9.2)], HOOD_DARK, 0.5)
        K.line(d, [K.at(-2.0, -8.6), K.at(4.0, -9.8), K.at(8.4, -8.4)], GI_LIGHT, 0.5)
        K.oval(d, K.at(-8.0, 0.2), 1.8, 2.2, HOOD_DARK)

    # With ``band`` the head is his skin, and the slit of the hood is a band of it.
    face = (SKIN, SKIN_SHADE, SKIN_DEEP) if band else (SLIT, SLIT, SLIT)
    _head = R.make_head(K, ("duelist",), *face, skull=(0.0, -2.4, 7.8, 8.8), jaw=(2.4, 4.0, 5.4, 7.2),
                        nose=((6.8, -0.8), (9.2, 2.8), (8.6, 4.2), (6.8, 4.6)), ear=None, shape=_hood_shape, under=_hood)

    def _eyes(mode: str):
        """His eyes: two red lights that slant down to his nose. Shut, each is a
        thin red line; struck, they are wide."""

        def paint(d) -> None:
            for (ex, ey), k in ((NEAR_EYE, 1.0), (FAR_EYE, 0.8)):
                if mode in ("closed", "wince", "happy"):
                    K.line(d, [K.at(ex - 2.0 * k, ey - 0.4), K.at(ex + 1.9 * k, ey + 0.5)], EYE, 0.7)
                    continue
                tall = 1.9 if mode == "wide" else 1.3
                K.poly(d, [K.at(ex - 2.3 * k, ey - tall), K.at(ex + 2.2 * k, ey - 0.1), K.at(ex + 1.6 * k, ey + tall * 0.9), K.at(ex - 1.7 * k, ey + tall * 0.5)], EYE)
                K.oval(d, K.at(ex + 0.3 * k, ey + 0.1), 0.8 * k, 0.6, EYE_HOT)

        return K.piece(("duelist_eyes", mode), paint)

    if band:
        # His own eyes; his brows are always set, for the cloth is on them.
        _skin_eyes = R.make_eyes(K, NEAR_EYE, FAR_EYE, ink=INK, iris=IRIS, lid=SKIN_DEEP, size=0.9)
        _brows = R.make_brows(K, [(-0.8, -2.6), (1.8, -3.6), (4.4, -2.6)], [(5.6, -2.8), (7.0, -3.8), (8.4, -3.4)], INK, 1.4)
        X.head_layers = lambda pose: [(_head(), "head"), (_skin_eyes(str(pose["eyes"])), "eyes"), (_brows(min(0, R.brow_mood(pose))), "brows")]
    else:
        X.head_layers = lambda pose: [(_head(), "head"), (_eyes(str(pose["eyes"])), "eyes")]
    X.neck = R.make_neck(K, HOOD_DARK, 6.0)
    # Close black sleeves, wraps from under the elbow to the wrist, black gloves.
    X.upper_arm = lambda near: [(0.0, 1.0, 8.6, 7.2, SLEEVE if near else SLEEVE_DARK)]
    X.forearm = lambda near: [(0.0, 1.0, 7.0, 5.4, SLEEVE if near else SLEEVE_DARK), (0.3, 0.94, 7.4, 6.0, WRAP if near else WRAP_DARK)]
    # Trousers that are tied under the knee; wraps on his shins.
    X.thigh = lambda near: [(0.0, 1.0, 11.0, 9.0, GI if near else GI_DARK)]
    X.shin = lambda near: [(0.0, 0.34, 9.4, 8.6, GI if near else GI_DARK), (0.3, 1.0, 7.4, 5.6, WRAP if near else WRAP_DARK)]
    X.hand = R.make_hand(K, GLOVE, GLOVE_DARK, GLOVE_DARK, size=1.0)
    X.shoe = R.make_shoe(K, HOOD, HOOD_DARK, BUILD.ankle_up, long=1.0, sole=RED_DARK)

    def _scarf_wrap():
        """The scarf round his neck: it covers his collar and his chin's edge."""

        def shape(d) -> None:
            K.poly(d, [K.at(-6.4, -3.4), K.at(0.0, -5.0), K.at(6.6, -3.6), K.at(7.4, 0.6), K.at(2.0, 3.4), K.at(-5.6, 2.2), K.at(-7.4, -0.6)], WHITE)

        def detail(d) -> None:
            K.line(d, [K.at(-6.0, -1.0), K.at(0.0, 0.6), K.at(7.0, -1.4)], RED_DARK, 0.7)
            K.line(d, [K.at(-5.0, -3.0), K.at(0.6, -3.4), K.at(6.0, -3.0)], RED_LIGHT, 0.5)

        return K.solid(("duelist_scarf",), shape, RED, detail, outline=1.1, rim=0.25, shade=0.3, shade_colour=RED_DARK)

    X.collar = _scarf_wrap

    def _tails(ctx) -> List[Stamp]:
        """The two ends of his scarf, from the back of his neck: they hang in the
        world, and when he goes they are out behind him."""
        a = math.radians(ctx.lean)
        root = (ctx.neck[0] - 6.4 * math.cos(a) + 1.6 * math.sin(a), ctx.neck[1] - 6.4 * math.sin(a) - 1.6 * math.cos(a))
        at = pin(root)
        fast = ctx.anim in ("run", "dash")
        heading, wave = {"run": (196.0, 9.0), "dash": (190.0, 6.0), "walk": (152.0, 7.0), "jump": (134.0, 6.0), "fall": (232.0, 8.0), "slash": (162.0, 8.0),
                         "hit": (30.0, 6.0), "blink_in": (200.0, 8.0), "blink_out": (136.0, 6.0)}.get(ctx.anim, (138.0, 4.0))
        if ctx.anim == "death":
            heading, wave = (lerp_(138.0, 176.0, ctx.u), 2.0)
        links = 7 if fast else 6
        phase = ctx.phase if ctx.anim in ("idle", "walk", "run", "fall", "dash") else math.tau * ctx.u
        chains = [R.chain((root[0] - at[0], root[1] - at[1] + dy), links - k, 4.4, heading + spread, wave=wave, curl=-2.0, phase=phase, lead=lead)
                  for k, (dy, spread, lead) in enumerate(((0.0, 0.0, 0.0), (1.6, 13.0, 1.3)))]
        return [(R.ribbon(K, ("duelist_tails",), chains, 3.0, RED, RED_DARK, taper=0.5), at, "scarf_tails", 0.0)]

    X.layers["back"].append(_tails)

    # ---- The sword and its scabbard -----------------------------------------------

    def _sword():
        """The sword along +x from his near hand: a grip in red cord with a brass
        end, a small round guard, and a long narrow blade with a little curve, its
        back up (a ninjato: a square guard and a straight blade)."""
        g = GUARD_AT
        # A katana bends up by 2.4 to its point; a ninjato is straight.
        bend = 0.0 if straight else 2.4

        def blade(up: float, down: float):
            # The back of the blade and its edge.
            top = [(g + t * BLADE, -up - bend * t * t) for t in (0.0, 0.25, 0.5, 0.75, 0.93)]
            bottom = [(g + t * BLADE, down - bend * t * t) for t in (0.86, 0.7, 0.5, 0.25, 0.0)]
            return [K.at(x, y) for x, y in top] + [K.at(g + BLADE, -bend - 0.2 - (0.9 if straight else 0.0))] + [K.at(x, y) for x, y in bottom]

        def guard(d, colour) -> None:
            if straight:
                K.rrect(d, K.home[0] + g - 1.4, K.home[1] - 3.4, K.home[0] + g + 1.4, K.home[1] + 3.4, 0.4, colour)
            else:
                K.oval(d, K.at(g, 0.0), 1.6, 3.4, colour)

        def shape(d) -> None:
            K.rrect(d, K.home[0] - BUTT, K.home[1] - 1.5, K.home[0] + g, K.home[1] + 1.5, 1.0, WHITE)
            guard(d, WHITE)
            K.poly(d, blade(1.5, 1.7), WHITE)

        def detail(d) -> None:
            K.rrect(d, K.home[0] - BUTT, K.home[1] - 2.4, K.home[0] + g, K.home[1] + 2.4, 0.0, RED_DARK)
            for k in range(5):
                x = -BUTT + 1.2 + k * 2.4
                K.line(d, [K.at(x, -2.0), K.at(x + 1.6, 2.0)], RED, 0.6)
            K.rrect(d, K.home[0] - BUTT - 0.6, K.home[1] - 2.4, K.home[0] - BUTT + 1.4, K.home[1] + 2.4, 0.0, BRASS_DARK)
            guard(d, BRASS)
            K.poly(d, blade(1.5, 1.7), STEEL)
            # The edge is bright, and the back of the blade is in shade.
            K.line(d, [K.at(g + t * BLADE, 1.0 - bend * t * t) for t in (0.04, 0.3, 0.55, 0.8)], STEEL_LIGHT, 0.6)
            K.line(d, [K.at(g + t * BLADE, -1.0 - bend * t * t) for t in (0.04, 0.3, 0.55, 0.86)], STEEL_DARK, 0.6)

        return K.solid(("duelist_sword",), shape, STEEL, detail, outline=1.1, rim=0.0, shade=0.0, shade_colour=STEEL_DARK)

    def _scabbard_part():
        """The scabbard along +x from its mouth: black lacquer, a brass mouth and
        end, and a red cord."""
        long = 40.0

        def shape(d) -> None:
            K.rrect(d, K.home[0], K.home[1] - 2.0, K.home[0] + long, K.home[1] + 2.0, 1.6, WHITE)

        def detail(d) -> None:
            K.rrect(d, K.home[0], K.home[1] - 3.0, K.home[0] + 2.6, K.home[1] + 3.0, 0.0, BRASS)
            K.rrect(d, K.home[0] + long - 3.0, K.home[1] - 3.0, K.home[0] + long + 1.0, K.home[1] + 3.0, 0.0, BRASS_DARK)
            K.line(d, [K.at(3.0, -1.0), K.at(long - 4.0, -1.0)], LACQUER_LIGHT, 0.5)
            K.rrect(d, K.home[0] + 8.0, K.home[1] - 3.0, K.home[0] + 11.0, K.home[1] + 3.0, 0.0, RED)

        return K.solid(("duelist_scabbard",), shape, LACQUER, detail, outline=1.1, rim=0.0, shade=0.0, shade_colour=GI_DARK)

    def _scabbard(ctx) -> List[Stamp]:
        """At his far hip, in his sash: its mouth is in front of him and its end is
        behind him and lower. It turns with his trunk."""
        return [(_scabbard_part(), ctx.trunk(8.6, -7.4), "scabbard", 161.0 + ctx.lean)]

    X.layers["back"].append(_scabbard)

    def _held(ctx) -> List[Stamp]:
        """The sword in his near hand, at the turn the pose says (``blade``: 0 is
        forward, -90 is up). When he is down it lies by him.

        It is in front of his arm, and his hand is round it (Jon, 2026-10-13, of
        the heavy's club: "should not be behind the upper arm. Should be in front
        of it. but probably behind the hand"): the sword is painted over all of
        him, and then his near hand again, over the sword."""
        hand, elbow = ctx.hand, ctx.elbow
        if float(ctx.pose["held"]) < 0.5:
            # It goes out of his hand, it turns once in the air, and it lies in
            # front of where he stood.
            lie = (X.cx + 58.0, ctx.ground - 2.6)
            t = min(1.0, max(0.0, (ctx.u - 0.12) / 0.3)) if ctx.anim == "death" else 1.0
            up = 18.0 * math.sin(math.pi * t)
            at = (lerp_(hand[0], lie[0], t), lerp_(hand[1], lie[1], t) - up)
            return [(_sword(), at, "sword", lerp_(float(ctx.pose["blade"]) - 360.0, 4.0, t) if t < 1.0 else 4.0)]
        return [(_sword(), hand, "sword", float(ctx.pose["blade"])),
                (X.hand(str(ctx.pose["nh"]), True), hand, "near_hand_on_sword", math.degrees(math.atan2(hand[1] - elbow[1], hand[0] - elbow[0])))]

    X.layers["front"].append(_held)

    def _tip(ctx):
        a = math.radians(float(ctx.pose["blade"]))
        return (ctx.hand[0] + (GUARD_AT + BLADE) * math.cos(a), ctx.hand[1] + (GUARD_AT + BLADE) * math.sin(a))

    def two(na, blade: float):
        """Where his far hand is (``fa``) when it is on the end of the grip: the
        near hand is at ``na`` and the sword is at the turn ``blade``."""
        a = math.radians(blade)
        dx = (BUILD.far_shoulder[0] - BUILD.near_shoulder[0]) / U
        dy = (BUILD.far_shoulder[1] - BUILD.near_shoulder[1]) / U
        back = (BUTT - 3.0) / U
        return (na[0] - dx - back * math.cos(a), na[1] - dy - back * math.sin(a))

    # ---- How he holds himself ----------------------------------------------------

    #: His guard: his hands in front of his belly, the point in front of him at
    #: the height of his throat. His face is clear.
    HANDS = (12.0, 15.5)
    POINT = -31.0
    X.set_rest(lean=4.0, hip=(0.0, 2.0), na=HANDS, nh="fist", fa=two(HANDS, POINT), fh="fist", nf=(-9.0, 0.0, 0.0), ff=(9.0, 0.0, 0.0), brows=-1.0, blade=POINT,
               held=1.0)

    def guard(na=HANDS, blade: float = POINT, **kw):
        """A pose with two hands on the sword."""
        return P(na=na, fa=two(na, blade), blade=blade, **kw)

    @X.row
    def idle(i: int, n: int):
        # He does not move. His chest does, and the point with it.
        _, s, c = loop(i, n)
        na = (HANDS[0], HANDS[1] + 0.4 * s)
        return guard(na, POINT + 1.2 * s, hip=(0.0, 2.0 + 0.4 * s), head=(0.0, 0.2 * s, 0.6 * c), eyes="closed" if i == n - 2 else "open")

    @X.row
    def walk(i: int, n: int):
        # He goes forward in his guard: short steps, and the point does not move.
        ph, s, c = loop(i, n)
        nf, ff = R.stride(ph, 7.0, 3.0)
        na = (HANDS[0] + 0.6 * c, HANDS[1] + 0.5 * abs(c))
        return guard(na, POINT + 1.5 * c, hip=(0.5, 2.6 + 0.7 * math.cos(2.0 * ph)), lean=6.0, head=(0.0, 0.0, 1.0 * s), nf=nf, ff=ff,
                     hem=(1.0 + 1.0 * abs(c), 0.5 + 1.0 * abs(c)))

    #: He runs low, and the sword is out behind him.
    BEHIND = 168.0

    @X.row
    def run(i: int, n: int):
        ph, s, c = loop(i, n)
        nf, ff = R.stride(ph, 12.5, 9.0, 0.0)
        return P(hip=(2.0, 3.0 + 1.6 * math.cos(2.0 * ph)), lean=18.0, head=(0.6, 0.0, -10.0), na=(-13.0 - 1.5 * c, 12.0 + 1.0 * s), nab=1.0,
                 fa=(-9.0 + 3.0 * c, 13.0), nh="fist", fh="flat", nf=nf, ff=ff, blade=BEHIND + 3.0 * s, hem=(5.0, 1.0))

    @X.row
    def dash(i: int, n: int):
        # Lower than his run, and one line from his head to the end of the sword.
        _, s, _c = loop(i, n)
        return P(hip=(4.0, 5.0 + 0.6 * s), lean=27.0, head=(1.0, 0.0, -18.0), na=(-15.0, 9.0), fa=(-11.0, 11.0), nh="fist", fh="flat",
                 nf=(-21.0 - s, -2.0 - s, 30.0), ff=(15.0, 0.0, 0.0), blade=BEHIND + 6.0, hem=(7.0, 0.0))

    @X.row
    def jump(i: int, n: int):
        wind = P(hip=(-1.0, 11.0), lean=14.0, na=(-10.0, 14.0), fa=(-6.0, 15.0), fh="flat", nf=(-7.0, 0.0, 0.0), ff=(8.0, 0.0, 0.0), blade=150.0)
        rise = P(hip=(0.0, -2.0), lean=6.0, head=(0.0, 0.0, -8.0), na=(-12.0, 12.0), fa=(10.0, 4.0), fh="flat", nf=(-6.0, -1.0, 34.0), ff=(6.0, -10.0, 12.0),
                 blade=140.0, hem=(1.0, 1.0))
        apex = P(hip=(0.0, -2.0), lean=2.0, head=(0.0, 0.0, -3.0), na=(-9.0, 4.0), fa=(13.0, 2.0), fh="flat", nf=(-5.0, -9.0, 22.0), ff=(8.0, -13.0, 4.0),
                 blade=214.0, hem=(3.0, 3.0))
        return X.keys(shot(i, n), [(0.0, wind), (0.3, rise), (0.6, rise), (1.0, apex)])

    @X.row
    def fall(i: int, n: int):
        # He comes down with the sword up behind him, for the cut when he lands.
        _, s, c = loop(i, n)
        return P(hip=(0.0, -3.0), lean=-4.0, head=(0.0, 0.0, 6.0), na=(-6.0 + 1.0 * s, -6.0 - 1.0 * c), fa=(14.0 - 1.5 * s, 2.0 + 1.5 * c), fh="flat",
                 nf=(-8.0, -3.0 + 1.5 * s, 28.0), ff=(7.0, -9.0 - 1.5 * s, 8.0), blade=232.0 + 3.0 * s, hem=(5.0, 5.0))

    #: The sword over his far shoulder, the two hands by his near ear's height
    #: and behind his face.
    WOUND_AT = (-2.0, -5.0)
    WOUND = guard(WOUND_AT, -142.0, hip=(-3.0, 3.0), lean=-7.0, head=(0.0, 0.0, -3.0), nab=-1.0, fab=-1.0, nf=(-10.0, 0.0, 0.0), ff=(8.0, 0.0, 0.0), eyes="wide")
    #: The cut is done: his hands low in front of him, the point at the ground.
    CUT_AT = (20.0, 17.0)
    DONE = guard(CUT_AT, 27.0, hip=(6.0, 7.0), lean=21.0, head=(1.0, 0.6, -8.0), nf=(-13.0, 0.0, 12.0), ff=(14.0, 0.0, 0.0), hem=(5.0, 1.0))

    @X.row
    def slash(i: int, n: int):
        # One cut: up over his far shoulder, down through you, and it stays there
        # for a moment.
        ready = X.full(P())
        mid = guard((21.0, 2.0), -14.0, hip=(3.0, 5.0), lean=12.0, nf=(-12.0, 0.0, 8.0), ff=(12.0, 0.0, 0.0), eyes="wide", hem=(3.0, 1.0))
        return X.keys(shot(i, n), [(0.0, ready), (0.2, WOUND), (0.3, WOUND), (0.4, mid), (0.5, DONE), (0.8, DONE), (1.0, ready)])

    @X.row
    def hit(i: int, n: int):
        struck = dict(X.full(R.STRUCK), lean=-18.0, hip=(-4.0, 3.0), na=(13.0, 8.0), fa=(17.0, -2.0), nh="fist", fh="open", blade=-64.0, held=1.0, eyes="wince")
        back = guard((10.0, 14.0), -44.0, hip=(-2.0, 3.0), lean=-4.0, eyes="wince")
        return X.keys(shot(i, n), [(0.0, P(lean=-3.0, eyes="wide")), (0.3, struck), (0.65, struck), (1.0, back)])

    @X.row
    def death(i: int, n: int):
        back = dict(X.full(R.STRUCK), lean=-18.0, na=(13.0, 8.0), nh="open", blade=-50.0, held=1.0, eyes="wince")
        sat = dict(X.full(R.SAT), held=0.0, eyes="closed")
        down = dict(X.full(R.SUPINE), held=0.0, eyes="closed")
        return X.keys(shot(i, n), [(0.0, back), (0.2, dict(back, lean=-26.0, held=0.0)), (0.5, sat), (0.75, down), (1.0, down)])

    #: The sign: his far hand in front of his chest with two fingers up, the
    #: sword down at his near side, its point behind him.
    SIGN = P(hip=(0.0, 5.0), lean=3.0, head=(0.0, 0.4, 4.0), na=(-3.0, 23.0), nh="fist", fa=(6.0, 3.0), fh="point", nf=(-8.0, 0.0, 0.0), ff=(8.0, 0.0, 0.0),
             blade=148.0, eyes="closed")
    #: He comes back low: a knee near the ground, the sword behind him.
    LOW = P(hip=(0.0, 17.0), lean=24.0, head=(1.0, 0.6, -14.0), na=(-12.0, 14.0), nh="fist", fa=(13.0, 20.0), fh="flat", nf=(-9.0, 0.0, 14.0), ff=(10.0, 0.0, 0.0),
            blade=172.0, hem=(3.0, 2.0))

    @X.row
    def blink_out(i: int, n: int):
        ready = X.full(P())
        return X.keys(shot(i, n), [(0.0, ready), (0.4, SIGN), (0.75, dict(SIGN, eyes="open")), (1.0, dict(SIGN, hip=(0.0, 8.0), lean=8.0, eyes="open"))])

    @X.row
    def blink_in(i: int, n: int):
        ready = X.full(P())
        return X.keys(shot(i, n), [(0.0, LOW), (0.35, LOW), (1.0, ready)])

    X.rows = [("idle", 8, 120), ("walk", 8, 95), ("run", 8, 75), ("jump", 6, 95), ("fall", 6, 95), ("slash", 8, 68), ("hit", 5, 90), ("death", 8, 110),
              ("blink_out", 6, 62), ("blink_in", 6, 62), ("dash", 6, 58)]

    # ---- What the sword does ----------------------------------------------------------

    def _trail(ctx):
        """The line of the cut: where the blade went from the last frame to this
        one, thin and clear where it started, wide and bright at the blade. It
        is light and not a thing: it has no outline. Nothing is in front of the
        blade, and a blade that does not move leaves nothing."""
        before = X.full(X.poses["slash"](ctx.i - 1, ctx.n))
        now = ctx.pose
        a0, a1 = float(before["blade"]), float(now["blade"])
        if a1 - a0 < 20.0:
            return None
        # No more than a quarter of a turn of it, and the hand's own way with it.
        a0 = max(a0, a1 - 80.0)
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
            r = reach * lerp_(0.98, 0.7, t * t)
            inner.append((round(ox + r * math.cos(a), 1), round(oy + r * math.sin(a), 1)))
        pts = (tuple(outer), tuple(inner))

        def paint(d) -> None:
            for k in range(steps):
                t = (k + 1) / steps
                K.poly(d, [K.at(*outer[k]), K.at(*outer[k + 1]), K.at(*inner[k + 1]), K.at(*inner[k])], CUT[:3] + (int(210 * t * t),))
            for k in range(steps):
                t = (k + 1) / steps
                K.line(d, [K.at(*outer[k]), K.at(*outer[k + 1])], STEEL_LIGHT[:3] + (int(255 * t),), 0.8)

        return K.aligned(("duelist_cut", pts), paint)

    def _effects(ctx) -> List[Stamp]:
        out: List[Stamp] = []
        if ctx.anim == "slash" and ctx.i > 0:
            trail = _trail(ctx)
            if trail is not None:
                out.append((trail, pin(ctx.hand), "cut", 0.0))
        if ctx.anim == "dash" and ctx.i % 2 == 0:
            out.append((R.dust(K, 2.6, DUST, DUST_DARK), (ctx.foot[0] - 10.0, ctx.ground - 3.0), "dust", 0.0))
        return out

    X.effects = _effects

    # ---- From the front ------------------------------------------------------------
    #
    # The row he turns through. He faces you with the sword low in his right hand
    # (the left of the picture), its point at the ground and out from him. The
    # scabbard and the ends of his scarf are behind him and come out at the other
    # side, where they can be seen.

    X.front_span = (8.4, 4.6)

    def _front_gi(d) -> None:
        top = -36.4
        K.poly(d, [K.at(-2.4, top + 1.2), K.at(2.4, top + 1.2), K.at(0.6, -27.0)], RED)
        K.line(d, [K.at(-3.8, top + 1.0), K.at(2.6, -16.0)], GI_LIGHT, 1.0)
        K.line(d, [K.at(3.8, top + 1.0), K.at(0.4, -23.6)], GI_LIGHT, 1.0)
        # The sash, and the ends of its knot at his right hip.
        K.poly(d, [K.at(-30.0, -13.0), K.at(30.0, -13.0), K.at(30.0, -7.0), K.at(-30.0, -7.0)], RED_DARK)
        K.line(d, [K.at(-30.0, -10.6), K.at(30.0, -10.6)], RED, 0.7)
        K.poly(d, [K.at(-4.4, -8.0), K.at(-1.4, -8.0), K.at(-1.0, 3.6), K.at(-3.6, 4.4)], RED_DARK, OUTLINE, 0.5)
        K.poly(d, [K.at(-7.0, -8.0), K.at(-4.2, -8.0), K.at(-5.6, 1.6), K.at(-8.0, 1.0)], RED, OUTLINE, 0.5)
        K.oval(d, K.at(-4.2, -8.8), 2.2, 2.0, RED, OUTLINE, 0.5)
        K.line(d, [K.at(4.6, -4.0), K.at(5.4, 7.0)], GI_DARK, 0.6)
        K.poly(d, [K.at(-30.0, 6.6), K.at(30.0, 6.6), K.at(30.0, 8.6), K.at(-30.0, 8.6)], GI_LIGHT)

    X.front_torso = R.make_front_torso(K, ("duelist",), GI, GI_DARK, [(-37.6, 3.4), (-34.6, 7.6), (-30.0, 8.6), (-22.0, 8.2), (-12.0, 7.0), (-6.0, 7.2), (0.0, 7.8),
                                                                     (8.8, 8.6)], shoulder=(7.6, -32.4, 3.6, 3.8), detail=_front_gi)

    def _front_hood_shape(d) -> None:
        K.oval(d, K.at(0.0, -2.0), 9.0, 9.8, WHITE)
        K.oval(d, K.at(0.0, 3.8), 7.4, 8.0, WHITE)
        # The knot of the hood: behind his head, and a little to one side.
        K.poly(d, [K.at(7.4, -3.0), K.at(11.4, -4.6), K.at(11.8, -1.0), K.at(7.8, 0.6)], WHITE)

    def _front_hood(d) -> None:
        # Cloth over all of it but the slit, and the slit is in shadow.
        K.poly(d, [K.at(-30.0, -30.0), K.at(30.0, -30.0), K.at(30.0, -1.0), K.at(7.0, -1.0), K.at(6.4, -3.6), K.at(0.0, -4.2), K.at(-6.4, -3.6), K.at(-7.0, -1.0),
                   K.at(-30.0, -1.0)], HOOD)
        K.poly(d, [K.at(-30.0, -1.0), K.at(-7.0, -1.0), K.at(-6.4, 1.6), K.at(0.0, 2.2), K.at(6.4, 1.6), K.at(7.0, -1.0), K.at(30.0, -1.0), K.at(30.0, 30.0),
                   K.at(-30.0, 30.0)], HOOD)
        K.line(d, [K.at(7.0, -1.0), K.at(6.4, -3.6), K.at(0.0, -4.2), K.at(-6.4, -3.6), K.at(-7.0, -1.0), K.at(-6.4, 1.6), K.at(0.0, 2.2), K.at(6.4, 1.6),
                   K.at(7.0, -1.0)], HOOD_DARK, 0.7)
        K.line(d, [K.at(-4.0, 5.0), K.at(0.0, 7.0), K.at(4.0, 5.0)], HOOD_DARK, 0.6)
        K.line(d, [K.at(-3.4, 8.6), K.at(0.0, 10.0), K.at(3.4, 8.6)], HOOD_DARK, 0.5)
        K.line(d, [K.at(-5.0, -8.6), K.at(0.0, -9.8), K.at(5.0, -8.6)], GI_LIGHT, 0.5)

    _front_head = R.make_front_head(K, ("duelist",), SKIN if band else SLIT, SKIN_DEEP if band else SLIT, wide=8.2, jaw=6.8, chin=3.4, shape=_front_hood_shape,
                                    hair=_front_hood)

    def _front_eyes(mode: str):
        """His eyes from the front: each slants down to the middle."""

        def paint(d) -> None:
            for sx in (-1.0, 1.0):
                ex, ey = 3.3 * sx, -1.0
                if mode in ("closed", "wince", "happy"):
                    K.line(d, [K.at(ex + 2.0 * sx, ey - 0.5), K.at(ex - 1.9 * sx, ey + 0.5)], EYE, 0.7)
                    continue
                tall = 1.9 if mode == "wide" else 1.3
                K.poly(d, [K.at(ex + 2.3 * sx, ey - tall), K.at(ex - 2.1 * sx, ey - 0.1), K.at(ex - 1.5 * sx, ey + tall * 0.9), K.at(ex + 1.8 * sx, ey + tall * 0.5)], EYE)
                K.oval(d, K.at(ex - 0.2 * sx, ey + 0.1), 0.8, 0.6, EYE_HOT)

        return K.piece(("duelist_front_eyes", mode), paint)

    if band:
        _front_skin_eyes = R.make_front_eyes(K, ("duelist",), spread=3.3, y=-1.0, ink=INK, iris=IRIS, size=0.85)
        _front_brows = R.make_front_brows(K, ("duelist",), INK, spread=3.3, y=-3.3, width=1.4)
        X.front_head_layers = lambda pose: [(_front_head(), "head"), (_front_skin_eyes(str(pose["eyes"])), "eyes"), (_front_brows(-1), "brows")]
    else:
        X.front_head_layers = lambda pose: [(_front_head(), "head"), (_front_eyes(str(pose["eyes"])), "eyes")]
    X.front_shoe = R.make_front_shoe(K, HOOD, HOOD_DARK, BUILD.ankle_up)

    def _front_behind(hip) -> List[Stamp]:
        # The ends of his scarf, out past his left shoulder; and the scabbard,
        # from his left hip down and out.
        root = (hip[0] + 5.0, hip[1] + BUILD.neck[1] + 1.0)
        at = pin(root)
        chains = [R.chain((root[0] - at[0], root[1] - at[1] + dy), 6 - k, 4.4, 46.0 + spread, curl=5.0) for k, (dy, spread) in enumerate(((0.0, 0.0), (1.6, 14.0)))]
        return [(R.ribbon(K, ("duelist_front_tails",), chains, 3.0, RED, RED_DARK, taper=0.5), at, "front_scarf_tails", 0.0),
                (_scabbard_part(), (hip[0] + 2.0, hip[1] - 7.0), "front_scabbard", 40.0)]

    X.front_behind = _front_behind

    def _front_effects(ctx) -> List[Stamp]:
        hand = ctx.left_hand
        return [(_scarf_wrap(), (ctx.neck[0], ctx.neck[1] + 0.6), "front_scarf", 0.0), (_sword(), hand, "front_sword", 118.0),
                (X.hand("fist", True), hand, "front_hand_on_sword", 92.0)]

    X.front_effects = _front_effects

    @X.front_row
    def front(i: int, n: int):
        _, s, _c = loop(i, n)
        arms = dict(R.front_arms(X, "sides"), lh="fist", rh="fist")
        return R.FP(hip=(0.0, 0.4 + 0.4 * s), head=(0.0, -0.3 * s, 0.0), eyes="closed" if i == n - 2 else "open", **arms)

    X.rows = list(X.rows) + [("front", 8, 145)]

    metadata = _metadata(look)
    render, main, render_canonical = R.entry_points(X, metadata, look.display_name)

    def render_portraits(out_dir, **opts):
        """His portraits are frames of this sheet."""
        del opts
        return X.portraits(out_dir, {"default": ("idle", (1,), 0, False), "talking": ("idle", (0, 1, 2, 3, 4, 5, 6, 7), 120, True)}, view_width=30.0)

    return SimpleNamespace(X=X, metadata=metadata, render=render, main=main, render_canonical=render_canonical, render_portraits=render_portraits)


MADE: Dict[str, SimpleNamespace] = {name: _make(look) for name, look in LOOKS.items()}

#: The Shadow Duelist himself, as the module's own names.
X = MADE[TARGET_NAME].X
K = X.K
P = X.P
U = X.U
FRAME_SIZE = X.frame
ROWS = X.rows
_render_frame = X.render_frame
render, main, render_canonical, render_portraits = (MADE[TARGET_NAME].render, MADE[TARGET_NAME].main, MADE[TARGET_NAME].render_canonical,
                                                    MADE[TARGET_NAME].render_portraits)

TARGETS = {name: {"render": made.render, "actor_metadata": made.metadata, "render_portraits": made.render_portraits} for name, made in MADE.items()}

if __name__ == "__main__":
    raise SystemExit(main())
