"""Sprite generator for the Ninja Heavy: the mountain of the Shadow Dojo.

The look (2026-10-13, a redraw: Jon, "Please redo the art for ninja heavy"):
the largest person of the dojo, with the build of a wrestler of the ring, seen
three quarters from the front, facing right. He is 198 cm, and wide: a round
trunk, a neck as wide as his head, arms like the legs of other people.

What makes him a ninja: the hood of the dojo over his head and his face, and
a plate of iron on its brow; his eyes are two red lights in the dark slit of
the hood, as the eyes of the Shadow Duelist are (Jon, 2026-10-13: "I like the
new darker eyes. Do the same thing with the ninja heavy in terms of the
eyes"); and black from there down, with no skin (Jon, 2026-10-13: "Less skin,
I like the dark clad in black look"): a black gi shut to his neck, black sleeves and
gloves, black wraps on his shins. What makes him the heavy: the rope of a
champion round his middle, in red cord, with its white papers; iron on his
forearms and one shoulder; and the kanabo, a club of iron with studs, as long
as his leg. At rest it lies on his shoulder.

He is a grown man and not a mascot, and not a monster: the last drawing had
the mask of an oni, and so does the leader of the dojo. There is no drop
shadow.

The rows are the ones a brute of the game plays: ``idle``, ``walk``,
``slash`` (the club comes down from over his head with both hands), ``taunt``
(he points it at you), ``hurt``, ``death``, and ``front`` (he faces you: the
row he turns through).

He is a person of ``_person_rig``: the bones, the poses and the frame are
shared; the head, the clothes, the club and how he stands are his.

The other heavies of the dojo (Jon, 2026-10-23: "Also make ninja variants
that were like the originals you made where they had normal eyes and skin
showing. I like the red eye ninjas too, but I want a few variants"). Each is
a ``Look`` of this module, a sheet of its own, with his bones and his poses:

``ninja_heavy_eye_band`` (Ninja Bruiser)
    The heavy as he was first published (renderer ``19e7c0b``): a band of
    skin in the hood, his own eyes and set brows, and an old scar through
    the near brow. A red headband where the iron plate was, and a kanabo of
    oak with iron studs.
``ninja_heavy_bare_arms`` (Ninja Wrestler)
    His first draft: bare arms, and a gi open on a bare chest, a rope of
    straw with its white papers, bare hands, iron on the forearms; the band
    of skin and his eyes, and the iron plate.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Dict, List, Tuple

from ._ai_era_kit import OUTLINE, WHITE, RGBA
from . import _person_rig as R
from ._person_rig import Build, Person, Stamp, loop, shot

TARGET_NAME = "ninja_heavy"
TARGET_BASENAME = TARGET_NAME
DISPLAY_NAME = "Ninja Heavy"

ACTOR_METADATA = {
    "actor": {"character_id": "npc_ninja_heavy", "display_name": "Ninja Heavy"},
    "lineage": {
        "family": "npc_ninja_heavy",
        "variant": "mountain",
        "parents": ["npc_ninja_heavy/iron_lotus"],
        "creator": {
            "kind": "model",
            "model": "Claude Opus 5.5",
        },
        "method": "person_rig",
        "revision": "first_draft",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Wide",
        "mass_class": "Heavy",
        "traits": ["story", "humanoid", "enemy", "combatant", "ninja", "heavy"],
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
    "brain": {"default_preset": "melee_brute_brute"},
    "actions": {"default_preset": "brute_lunge"},
    "visual": {"default_pose": "idle"},
    "tags": ["story", "humanoid", "enemy", "combatant", "ninja", "heavy"],
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
        "interaction.talk": {"animation": "taunt", "events": []},
        "interaction.use": {"animation": "taunt", "events": []},
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


#: He is in black from his head to his feet (Jon, 2026-10-13: "Less skin, I
#: like the dark clad in black look"). The black has a little blue in it, so
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
LACQUER: RGBA = (176, 44, 48, 255)
LACQUER_DARK: RGBA = (112, 26, 34, 255)
ROPE: RGBA = (150, 36, 44, 255)
ROPE_DARK: RGBA = (92, 20, 30, 255)
PAPER: RGBA = (250, 248, 240, 255)
PAPER_DARK: RGBA = (196, 198, 210, 255)
IRON: RGBA = (86, 92, 110, 255)
IRON_DARK: RGBA = (46, 50, 66, 255)
IRON_LIGHT: RGBA = (150, 160, 180, 255)
BRASS: RGBA = (222, 176, 84, 255)
BRASS_DARK: RGBA = (150, 104, 44, 255)
WRAP: RGBA = (52, 55, 74, 255)
WRAP_DARK: RGBA = (30, 32, 46, 255)
GRIP: RGBA = (104, 60, 54, 255)
GRIP_DARK: RGBA = (62, 34, 36, 255)
#: The slit of his hood is in shadow, darker than its cloth, and his eyes are
#: red lights in it.
SLIT: RGBA = (8, 7, 12, 255)
EYE: RGBA = (232, 34, 40, 255)
EYE_HOT: RGBA = (255, 138, 110, 255)
INK: RGBA = (24, 22, 30, 255)
DUST: RGBA = (214, 200, 168, 255)
DUST_DARK: RGBA = (150, 132, 104, 255)
#: The skin of the heavies who show it (his first look, renderer ``19e7c0b``).
SKIN: RGBA = (218, 166, 126, 255)
SKIN_SHADE: RGBA = (182, 126, 96, 255)
SKIN_DEEP: RGBA = (132, 82, 70, 255)
IRIS: RGBA = (92, 60, 40, 255)
#: The rope of straw of his first draft.
STRAW: RGBA = (214, 186, 116, 255)
STRAW_DARK: RGBA = (150, 120, 64, 255)
#: A kanabo of oak, with iron studs.
OAK: RGBA = (132, 88, 54, 255)
OAK_DARK: RGBA = (82, 52, 34, 255)
OAK_LIGHT: RGBA = (184, 134, 86, 255)

#: 198 cm (168 cm is 108 pixels), and wide.
BUILD = Build(hip_up=55.0, thigh=27.0, shin=26.0, neck=(1.0, -42.0), upper=22.0, fore=20.5, near_shoulder=(-10.0, -36.6), far_shoulder=(10.6, -36.0),
              near_hip=(-5.4, 0.0), far_hip=(5.4, 0.0), head_up=(1.2, -12.4), height=127.0, half_width=(20.0, 22.0))
TOP = BUILD.neck[1] - 2.0
#: How long the club is past his hand, and how far its grip is behind it.
CLUB = 66.0
BUTT = 6.0


@dataclass(frozen=True)
class Look:
    """What one heavy of the dojo wears. His bones and his poses are the
    same for all of them.

    ``face``: ``"slit"``, two red lights in the dark slit of the hood; or
    ``"band"``, a band of skin in the hood with his own eyes, set brows and
    a scar. ``brow``: what is on the brow of the hood, ``"plate"`` (iron) or
    ``"headband"`` (red cloth). ``arms``: ``"sleeved"`` (black sleeves and
    gloves, the gi shut to his neck) or ``"bare"`` (bare arms and hands, the
    gi open on his chest). ``rope``: the colour of the rope and of its
    twist. ``club``: the body of the kanabo, its shade and its light."""

    target: str
    display_name: str
    variant: str
    parents: Tuple[str, ...]
    face: str = "slit"
    brow: str = "plate"
    arms: str = "sleeved"
    rope: Tuple[RGBA, RGBA] = (ROPE, ROPE_DARK)
    club: Tuple[RGBA, RGBA, RGBA] = (IRON, IRON_DARK, IRON_LIGHT)


LOOKS: Dict[str, Look] = {
    look.target: look
    for look in (
        Look(TARGET_NAME, DISPLAY_NAME, "mountain", ("npc_ninja_heavy/iron_lotus",)),
        Look("ninja_heavy_eye_band", "Ninja Bruiser", "bruiser", ("npc_ninja_heavy/mountain",), face="band", brow="headband",
             club=(OAK, OAK_DARK, OAK_LIGHT)),
        Look("ninja_heavy_bare_arms", "Ninja Wrestler", "wrestler", ("npc_ninja_heavy/mountain",), face="band", arms="bare",
             rope=(STRAW, STRAW_DARK)),
    )
}


def _metadata(look: Look) -> dict:
    """The actor metadata of ``look``: the heavy's, with its own name."""
    if look.target == TARGET_NAME:
        return ACTOR_METADATA
    lineage = dict(ACTOR_METADATA["lineage"], variant=look.variant, parents=list(look.parents))
    return dict(ACTOR_METADATA, actor={"character_id": f"npc_{look.target}", "display_name": look.display_name}, lineage=lineage)


def _make(look: Look) -> SimpleNamespace:
    """The person of ``look``, and the entry points of its sheet."""
    X = Person(look.target, BUILD, frame=(288, 240), ground=226.0, cx=132.0)
    K = X.K
    P = X.P
    band = look.face == "band"
    bare = look.arms == "bare"
    rope, rope_dark = look.rope
    club, club_dark, club_light = look.club

    def _front(d, hb: float, hf: float) -> None:
        """The cross of his gi and the red under it, the line of his belly, and
        the rope of a champion with its knot and its white papers."""
        if bare:
            # The gi is open: his chest is bare from his neck to the rope, and
            # its edge goes down from the back of his neck.
            K.poly(d, [K.at(-4.0, TOP), K.at(40.0, TOP - 10.0), K.at(40.0, -12.0), K.at(6.0, -13.6)], SKIN)
            K.line(d, [K.at(-4.0, TOP), K.at(6.0, -13.6)], GI_LIGHT, 1.0)
            # The line under his chest, and the middle of it.
            K.line(d, [K.at(5.0, -27.0), K.at(13.0, -25.6), K.at(22.0, -26.6)], SKIN_SHADE, 0.8)
            K.line(d, [K.at(9.0, -36.0), K.at(11.0, -27.6)], SKIN_SHADE, 0.6)
            K.line(d, [K.at(16.0, -21.0), K.at(19.0, -15.0)], SKIN_SHADE, 0.6)
        else:
            # The gi is shut to his neck: one side over the other, and a line of red
            # under its edge.
            K.poly(d, [K.at(-3.0, TOP), K.at(-0.4, TOP - 1.0), K.at(13.4, -15.0), K.at(10.6, -14.4)], LACQUER)
            K.poly(d, [K.at(-6.0, TOP + 1.0), K.at(-3.0, TOP), K.at(10.6, -14.4), K.at(8.0, -13.4)], GI_LIGHT)
            K.poly(d, [K.at(12.0, TOP + 1.0), K.at(14.4, TOP + 2.6), K.at(8.4, -24.0), K.at(6.4, -25.6)], GI_LIGHT)
        K.line(d, [K.at(-9.0, -22.0), K.at(-3.0, -8.0)], GI_DARK, 0.7)
        # The rope: thick, of twisted red cord, round the widest part of him.
        K.poly(d, [K.at(-40.0, -15.0), K.at(40.0, -12.0), K.at(40.0, -4.0), K.at(-40.0, -7.0)], rope)
        K.line(d, [K.at(-40.0, -15.0), K.at(40.0, -12.0)], rope_dark, 0.8)
        K.line(d, [K.at(-40.0, -7.0), K.at(40.0, -4.0)], rope_dark, 0.8)
        for k in range(-6, 9):
            x = k * 4.4
            K.line(d, [K.at(x, -14.4 + x * 0.04), K.at(x + 3.0, -5.6 + x * 0.04)], rope_dark, 0.7)
        # Its papers: two, each one zigzag of three steps.
        for x in (4.0, 14.0):
            K.poly(d, [K.at(x, -4.6), K.at(x + 4.0, -4.6), K.at(x + 4.0, 0.2), K.at(x + 5.8, 0.2), K.at(x + 5.8, 5.2), K.at(x + 4.0, 5.2), K.at(x + 4.0, 10.4),
                       K.at(x, 10.4), K.at(x, 5.0), K.at(x + 1.8, 5.0), K.at(x + 1.8, 0.4), K.at(x, 0.4)], PAPER, OUTLINE, 0.5)
        # The folds of the gi over his belly, and where it closes.
        K.line(d, [K.at(-12.0, -28.0), K.at(-9.0, -16.0)], GI_DARK, 0.7)
        if not bare:
            K.line(d, [K.at(15.0, -22.0), K.at(19.0, -15.0)], GI_DARK, 0.6)
        # The skirt of the gi under the rope, and its edge.
        K.line(d, [K.at(7.0, -1.0), K.at(9.0 + hf * 0.5, 14.0)], GI_DARK, 0.7)
        K.poly(d, [K.at(-40.0 - hb, 11.0), K.at(40.0 + hf, 11.0), K.at(40.0 + hf, 13.4), K.at(-40.0 - hb, 13.4)], GI_LIGHT)

    def _torso(hem_back: int, hem_front: int):
        """A round trunk: a back like a wall, a chest that goes into a belly,
        and the skirt of the gi under the rope."""
        hb, hf = float(hem_back), float(hem_front)

        def shape(d) -> None:
            K.poly(d, [K.at(-6.6, TOP), K.at(-14.0, TOP + 4.0), K.at(-18.0, -30.0), K.at(-19.6, -16.0), K.at(-18.6, -4.0), K.at(-16.0 - hb, 14.0), K.at(17.0 + hf, 14.0),
                       K.at(22.0, 2.0), K.at(25.6, -7.0), K.at(26.0, -15.0), K.at(24.0, -23.0), K.at(19.0, -31.0), K.at(13.6, TOP + 4.0), K.at(6.6, TOP - 0.4)], WHITE)
            K.oval(d, K.at(-9.6, -36.0), 9.6, 8.6, WHITE)
            K.oval(d, K.at(10.0, -35.6), 8.2, 7.6, WHITE)

        def paint(d) -> None:
            _front(d, hb, hf)

        return K.solid(("heavy_torso", hem_back, hem_front), shape, GI, paint, outline=1.3, rim=0.3, shade=0.4, shade_colour=GI_DARK)

    X.torso = _torso

    NEAR_EYE = (2.2, -0.4)
    FAR_EYE = (7.4, -0.6)

    def _hood_shape(d) -> None:
        # The hood is a little larger than his head, and its two tails are behind.
        K.oval(d, K.at(-0.6, -2.6), 9.6, 10.2, WHITE)
        K.oval(d, K.at(2.6, 4.4), 6.4, 8.0, WHITE)
        K.poly(d, [K.at(-8.6, -3.0), K.at(-16.0, 0.0), K.at(-17.6, 4.0), K.at(-10.0, 2.6)], WHITE)
        K.poly(d, [K.at(-8.6, -1.0), K.at(-13.6, 6.0), K.at(-12.6, 10.6), K.at(-8.0, 4.0)], WHITE)

    def _hood(d) -> None:
        # All of it is cloth but the slit at his eyes, and the slit is in shadow
        # (or, with ``band``, a band of his skin).
        K.poly(d, [K.at(-30.0, -30.0), K.at(30.0, -30.0), K.at(30.0, -4.0), K.at(9.6, -4.0), K.at(4.0, -4.4), K.at(-0.6, -3.4), K.at(-1.6, -0.6), K.at(-1.0, 2.2),
                   K.at(4.0, 2.8), K.at(10.6, 2.4), K.at(30.0, 2.4), K.at(30.0, 30.0), K.at(-30.0, 30.0)], HOOD)
        K.line(d, [K.at(9.6, -4.0), K.at(4.0, -4.4), K.at(-0.6, -3.4), K.at(-1.6, -0.6), K.at(-1.0, 2.2), K.at(4.0, 2.8), K.at(10.6, 2.4)], HOOD_DARK, 0.7)
        # The folds of it, the knot at the back, and the cloth over his nose and mouth.
        K.line(d, [K.at(-6.0, -9.0), K.at(-8.0, 0.0), K.at(-6.4, 8.0)], HOOD_DARK, 0.6)
        K.line(d, [K.at(0.0, 5.0), K.at(4.0, 7.6), K.at(8.6, 6.6)], HOOD_DARK, 0.6)
        K.line(d, [K.at(-1.0, 8.4), K.at(3.6, 11.0), K.at(7.4, 10.0)], HOOD_DARK, 0.5)
        K.oval(d, K.at(-8.6, -0.4), 2.2, 2.6, HOOD_DARK)
        K.line(d, [K.at(-10.0, 0.6), K.at(-16.0, 2.6)], HOOD_DARK, 0.6)
        if look.brow == "headband":
            # A red band round his brow, tied at the back of his head.
            K.poly(d, [K.at(-9.4, -9.0), K.at(9.4, -10.4), K.at(10.2, -6.2), K.at(-9.0, -5.0)], LACQUER, OUTLINE, 0.6)
            K.line(d, [K.at(-9.0, -8.0), K.at(9.6, -9.4)], (214, 84, 76, 255), 0.6)
            K.oval(d, K.at(-8.6, -7.0), 2.0, 2.2, LACQUER_DARK, OUTLINE, 0.5)
            return
        # The plate on his brow: iron, with a red bar and three brass rivets.
        K.poly(d, [K.at(-3.6, -10.6), K.at(9.0, -11.2), K.at(10.4, -5.6), K.at(-2.4, -5.0)], IRON, OUTLINE, 0.6)
        K.poly(d, [K.at(-3.0, -10.0), K.at(8.8, -10.6), K.at(9.0, -9.0), K.at(-2.8, -8.4)], IRON_LIGHT)
        K.poly(d, [K.at(2.4, -10.4), K.at(4.6, -10.5), K.at(5.2, -5.6), K.at(3.0, -5.4)], LACQUER)
        for x in (-1.0, 7.6):
            K.oval(d, K.at(x, -7.0), 0.8, 0.8, BRASS)

    def _scar(d) -> None:
        # An old cut through his near brow: he did not always win.
        K.line(d, [K.at(0.6, -3.6), K.at(2.0, 1.6)], SKIN_DEEP, 0.5)

    if band:
        _head = R.make_head(K, ("heavy",), SKIN, SKIN_SHADE, SKIN_DEEP, skull=(0.0, -2.4, 8.4, 9.2), jaw=(2.6, 4.2, 6.2, 7.8),
                            nose=((7.4, -0.6), (9.8, 2.8), (9.2, 4.4), (7.2, 4.8)), ear=None, shape=_hood_shape, under=_hood, over=_scar)
    else:
        _head = R.make_head(K, ("heavy",), SLIT, SLIT, SLIT, skull=(0.0, -2.4, 8.4, 9.2), jaw=(2.6, 4.2, 6.2, 7.8),
                            nose=((7.4, -0.6), (9.8, 2.8), (9.2, 4.4), (7.2, 4.8)), ear=None, shape=_hood_shape, under=_hood)

    def _eyes(mode: str):
        """His eyes: two red lights that slant down to his nose, in the dark slit
        of his hood. Shut, each is a thin red line; struck, they are wide."""

        def paint(d) -> None:
            for (ex, ey), k in ((NEAR_EYE, 1.0), (FAR_EYE, 0.8)):
                if mode in ("closed", "wince", "happy"):
                    K.line(d, [K.at(ex - 2.0 * k, ey - 0.4), K.at(ex + 1.9 * k, ey + 0.5)], EYE, 0.7)
                    continue
                tall = 2.0 if mode == "wide" else 1.4
                K.poly(d, [K.at(ex - 2.4 * k, ey - tall), K.at(ex + 2.3 * k, ey - 0.1), K.at(ex + 1.7 * k, ey + tall * 0.9), K.at(ex - 1.8 * k, ey + tall * 0.5)], EYE)
                K.oval(d, K.at(ex + 0.3 * k, ey + 0.1), 0.9 * k, 0.7, EYE_HOT)

        return K.piece(("heavy_eyes", mode), paint)

    if band:
        # His own eyes; his brows are always set, for the cloth is on them.
        _skin_eyes = R.make_eyes(K, NEAR_EYE, FAR_EYE, ink=INK, iris=IRIS, lid=SKIN_DEEP, size=0.9)
        _brows = R.make_brows(K, [(-0.4, -3.0), (2.2, -3.6), (4.6, -2.4)], [(6.0, -2.6), (7.6, -3.6), (9.0, -3.2)], INK, 1.5)
        X.head_layers = lambda pose: [(_head(), "head"), (_skin_eyes(str(pose["eyes"])), "eyes"), (_brows(min(0, R.brow_mood(pose))), "brows")]
    else:
        X.head_layers = lambda pose: [(_head(), "head"), (_eyes(str(pose["eyes"])), "eyes")]
    X.neck = R.make_neck(K, HOOD_DARK, 12.0)
    if bare:
        # Bare arms; iron from under the elbow to the wrist; bare hands.
        X.upper_arm = lambda near: [(0.0, 1.0, 16.0, 13.0, SKIN if near else SKIN_SHADE)]
        X.forearm = lambda near: [(0.0, 1.0, 13.0, 9.6, SKIN if near else SKIN_SHADE), (0.3, 0.92, 13.4, 10.6, IRON if near else IRON_DARK)]
        X.hand = R.make_hand(K, SKIN, SKIN_SHADE, SKIN_DEEP, size=1.4)
    else:
        # Black sleeves; iron from under the elbow to the wrist; black gloves.
        X.upper_arm = lambda near: [(0.0, 1.0, 16.0, 13.0, SLEEVE if near else SLEEVE_DARK)]
        X.forearm = lambda near: [(0.0, 1.0, 13.0, 9.6, SLEEVE if near else SLEEVE_DARK), (0.3, 0.92, 13.4, 10.6, IRON if near else IRON_DARK)]
        X.hand = R.make_hand(K, GLOVE, GLOVE_DARK, GLOVE_DARK, size=1.4)
    # Wide trousers, tied under the knee; wraps on his shins.
    X.thigh = lambda near: [(0.0, 1.0, 18.0, 15.0, GI if near else GI_DARK)]
    X.shin = lambda near: [(0.0, 0.36, 15.0, 13.6, GI if near else GI_DARK), (0.34, 1.0, 11.0, 8.6, WRAP if near else WRAP_DARK)]
    X.shoe = R.make_shoe(K, HOOD, HOOD_DARK, BUILD.ankle_up, long=1.2, sole=ROPE_DARK)

    def _pauldron(ctx) -> List[Stamp]:
        """The plate of iron on his near shoulder, with its red cord."""

        def shape(d) -> None:
            K.poly(d, [K.at(-9.0, -3.0), K.at(-4.0, -8.0), K.at(5.0, -8.6), K.at(10.0, -4.0), K.at(9.6, 4.6), K.at(0.0, 8.0), K.at(-9.4, 5.0)], WHITE)

        def detail(d) -> None:
            K.poly(d, [K.at(-9.0, -3.0), K.at(-4.0, -8.0), K.at(5.0, -8.6), K.at(10.0, -4.0), K.at(8.0, -3.0), K.at(-7.0, -2.0)], IRON_LIGHT)
            for y in (0.6, 4.0):
                K.line(d, [K.at(-9.4, y), K.at(0.0, y + 2.2), K.at(9.8, y - 0.6)], LACQUER, 0.9)
            for x in (-6.0, 0.0, 6.0):
                K.oval(d, K.at(x, -5.0), 0.8, 0.8, BRASS)

        part = K.solid(("heavy_pauldron",), shape, IRON, detail, outline=1.2, rim=0.3, shade=0.35, shade_colour=IRON_DARK)
        sh, el = ctx.shoulder, ctx.elbow
        return [(part, (sh[0], sh[1] + 1.0), "pauldron", math.degrees(math.atan2(el[1] - sh[1], el[0] - sh[0])) - 90.0)]

    X.layers["front"].append(_pauldron)

    # ---- The kanabo ----------------------------------------------------------------

    def _kanabo():
        """The club along +x from his hand: a grip in dark cord with a ring at
        its end, a brass collar, and a body of iron (or of oak) with eight
        sides and rows of iron studs, wider at its end."""

        def shape(d) -> None:
            K.rrect(d, K.home[0] - BUTT, K.home[1] - 2.0, K.home[0] + 16.0, K.home[1] + 2.0, 1.0, WHITE)
            K.oval(d, K.at(-BUTT - 1.2, 0.0), 2.2, 2.2, WHITE)
            K.poly(d, [K.at(15.0, -3.0), K.at(CLUB - 3.0, -6.4), K.at(CLUB, -4.0), K.at(CLUB, 4.0), K.at(CLUB - 3.0, 6.4), K.at(15.0, 3.0)], WHITE)
            for k in range(6):
                x = 22.0 + k * 7.4
                w = 3.6 + (x - 15.0) / (CLUB - 18.0) * 3.2
                K.oval(d, K.at(x, -w - 0.4), 1.5, 1.5, WHITE)
                K.oval(d, K.at(x, w + 0.4), 1.5, 1.5, WHITE)

        def detail(d) -> None:
            K.rrect(d, K.home[0] - BUTT, K.home[1] - 3.0, K.home[0] + 15.0, K.home[1] + 3.0, 0.0, GRIP)
            for k in range(6):
                x = -BUTT + 1.0 + k * 3.4
                K.line(d, [K.at(x, -2.4), K.at(x + 2.4, 2.4)], GRIP_DARK, 0.7)
            K.oval(d, K.at(-BUTT - 1.2, 0.0), 2.2, 2.2, BRASS_DARK)
            K.rrect(d, K.home[0] + 14.0, K.home[1] - 4.0, K.home[0] + 18.0, K.home[1] + 4.0, 0.0, BRASS)
            K.line(d, [K.at(18.0, -1.2), K.at(CLUB - 2.0, -2.0)], club_light, 0.9)
            K.line(d, [K.at(18.0, 1.6), K.at(CLUB - 2.0, 2.6)], club_dark, 0.8)
            for k in range(6):
                x = 22.0 + k * 7.4
                w = 3.6 + (x - 15.0) / (CLUB - 18.0) * 3.2
                for y in (-w - 0.4, 0.2, w + 0.4):
                    K.oval(d, K.at(x, y), 1.3, 1.3, IRON_LIGHT if y < 0.0 else BRASS if y == 0.2 else IRON_DARK, OUTLINE, 0.3)
            K.rrect(d, K.home[0] + CLUB - 3.0, K.home[1] - 7.0, K.home[0] + CLUB + 1.0, K.home[1] + 7.0, 0.0, IRON_DARK)

        return K.solid(("kanabo",), shape, club, detail, outline=1.3, rim=0.3, shade=0.35, shade_colour=club_dark)

    def _club(ctx) -> List[Stamp]:
        """The club in his near hand, at the turn the pose says (``club``: 0 is
        forward, -90 is up). When he is down it lies by him.

        It is in front of his arm and his shoulder, and his hand is round it
        (Jon, 2026-10-13: "should not be behind the upper arm. Should be in front
        of it. but probably behind the hand"): the club is painted over all of
        him, and then his near hand again, over the club."""
        if float(ctx.pose["held"]) < 0.5:
            return [(_kanabo(), (ctx.hip[0] + 30.0, ctx.ground - 5.0), "kanabo", 0.0)]
        hand, elbow = ctx.hand, ctx.elbow
        return [(_kanabo(), hand, "kanabo", float(ctx.pose["club"])),
                (X.hand(str(ctx.pose["nh"]), True), hand, "near_hand_on_club", math.degrees(math.atan2(hand[1] - elbow[1], hand[0] - elbow[0])))]

    X.layers["front"].append(_club)

    def _tip(ctx):
        a = math.radians(float(ctx.pose["club"]))
        return (ctx.hand[0] + CLUB * math.cos(a), ctx.hand[1] + CLUB * math.sin(a))

    # ---- How he holds himself ----------------------------------------------------

    #: The club on his near shoulder: his hand low on its grip, in front of him.
    CARRY = (14.0, 9.0)
    #: The turn of the club there: up, and well back, so its end is behind him and not behind his head.
    SLUNG = -142.0
    X.set_rest(lean=-2.0, hip=(0.0, 0.0), na=CARRY, nh="fist", fa=(3.0, 23.0), fh="fist", nf=(-7.0, 0.0, 0.0), ff=(8.0, 0.0, 0.0), brows=-1.0, club=SLUNG,
               held=1.0)

    @X.row
    def idle(i: int, n: int):
        # He does not move much. His chest does, and the club with it.
        _, s, c = loop(i, n)
        return P(hip=(0.0, 0.5 + 0.5 * s), head=(0.0, 0.2 * s, 1.0 * c), na=(CARRY[0], CARRY[1] + 0.5 * s), club=SLUNG + 1.5 * s,
                 eyes="closed" if i == n - 2 else "open")

    @X.row
    def walk(i: int, n: int):
        # Heavy: each foot comes down, and all of him with it.
        ph, s, c = loop(i, n)
        nf, ff = R.stride(ph, 7.0, 3.4)
        return P(hip=(0.5, 1.4 * abs(math.cos(ph))), lean=1.0 + 1.5 * c, head=(0.0, 0.0, 1.0 * s), na=(CARRY[0], CARRY[1] + 0.8 * abs(c)),
                 fa=(3.0 + 5.0 * c, 23.0), club=SLUNG + 3.0 * c, nf=nf, ff=ff, hem=(1.0 + 1.0 * abs(c), 0.5 + 1.0 * abs(c)))

    #: Both hands on the grip, the club over his head and back.
    RAISED = P(hip=(-1.5, 1.0), lean=-8.0, head=(0.0, 0.0, -6.0), na=(7.0, -24.0), nab=-1.0, arm="under", fa=(-4.0, -24.0), fab=-1.0, nh="fist", fh="fist",
               nf=(-9.0, 0.0, 0.0), ff=(9.0, 0.0, 0.0), club=-128.0, eyes="wide")
    #: It is down: in front of him, on the ground.
    DOWN = P(hip=(4.0, 7.0), lean=24.0, head=(1.0, 1.0, 10.0), na=(17.0, 15.0), fa=(7.0, 19.0), nh="fist", fh="fist", nf=(-10.0, 0.0, 0.0), ff=(13.0, 0.0, 0.0),
             club=15.0, eyes="open", hem=(5.0, 1.0))

    @X.row
    def slash(i: int, n: int):
        # Up over his head with both hands, a moment there, and down on you.
        ready = X.full(P())
        return X.keys(shot(i, n), [(0.0, ready), (0.3, RAISED), (0.42, dict(RAISED, lean=-10.0, club=-136.0)), (0.56, DOWN), (0.8, DOWN), (1.0, ready)])

    @X.row
    def taunt(i: int, n: int):
        # He takes it off his shoulder and points it at you. It does not shake.
        point = P(hip=(1.0, 1.0), lean=4.0, head=(0.4, 0.0, 4.0), na=(24.0, 3.0), fa=(1.0, 22.0), club=-4.0, eyes="open")
        lift = P(lean=-3.0, na=(15.0, 4.0), club=-70.0)
        return X.keys(shot(i, n), [(0.0, X.full(P())), (0.25, lift), (0.5, point), (0.85, point), (1.0, X.full(P()))])

    @X.row
    def hurt(i: int, n: int):
        struck = dict(X.full(R.STRUCK), lean=-14.0, hip=(-3.0, 2.0), na=(10.0, 16.0), nh="fist", club=-60.0, held=1.0, eyes="wince")
        back = P(hip=(-2.0, 2.0), lean=-6.0, club=-100.0, eyes="wince")
        return X.keys(shot(i, n), [(0.0, P(lean=-4.0, eyes="wide")), (0.3, struck), (0.65, struck), (1.0, back)])

    @X.row
    def death(i: int, n: int):
        back = dict(X.full(R.STRUCK), lean=-14.0, na=(10.0, 16.0), nh="open", club=-40.0, held=1.0, eyes="wince")
        down = dict(X.full(R.SUPINE), held=0.0, eyes="closed", off=(13.0, -8.0))
        return X.keys(shot(i, n), [(0.0, back), (0.2, dict(back, lean=-24.0, held=0.0)), (0.7, down), (1.0, down)])

    X.rows = [("idle", 6, 130), ("walk", 8, 95), ("slash", 7, 80), ("taunt", 6, 110), ("hurt", 4, 90), ("death", 8, 110)]

    # ---- What the club does ----------------------------------------------------------

    def _effects(ctx) -> List[Stamp]:
        out: List[Stamp] = []
        if ctx.anim == "slash" and 0.5 <= ctx.u <= 0.86:
            tip = _tip(ctx)
            at = (tip[0] + 2.0, ctx.ground - 12.0)
            late = ctx.u > 0.68
            out.append((R.burst(K, 9.0 if late else 13.0, DUST, DUST_DARK, 9), at, "ground_hit", 0.0))
            out.append((R.dust(K, 3.0 if late else 4.4, DUST, DUST_DARK), (at[0] + (14.0 if late else 9.0), at[1] - 3.0), "dust_ahead", 0.0))
            out.append((R.dust(K, 2.4 if late else 3.6, DUST, DUST_DARK), (at[0] - (12.0 if late else 8.0), at[1] - 2.0), "dust_behind", 0.0))
        return out

    X.effects = _effects

    # ---- From the front ------------------------------------------------------------
    #
    # The row he turns through (Jon, 2026-10-13: "We need front facing views for
    # the ninjas too"). He faces you with the club head down on the ground at his
    # right side (the left of the picture), his hand on its grip.

    X.front_span = (17.6, 8.0)

    def _front_gi(d) -> None:
        if bare:
            # The gi open on his bare chest, wider to the rope.
            K.poly(d, [K.at(-5.6, TOP + 1.0), K.at(5.6, TOP + 1.0), K.at(13.0, -15.0), K.at(-13.0, -15.0)], SKIN)
            K.line(d, [K.at(-5.6, TOP + 1.0), K.at(-13.0, -15.0)], GI_LIGHT, 1.2)
            K.line(d, [K.at(5.6, TOP + 1.0), K.at(13.0, -15.0)], GI_LIGHT, 1.2)
            K.line(d, [K.at(-9.6, -26.6), K.at(-1.0, -25.4)], SKIN_SHADE, 0.8)
            K.line(d, [K.at(9.6, -26.6), K.at(1.0, -25.4)], SKIN_SHADE, 0.8)
            K.line(d, [K.at(0.0, TOP + 5.0), K.at(0.0, -26.0)], SKIN_SHADE, 0.6)
        else:
            K.poly(d, [K.at(-3.0, TOP + 1.4), K.at(3.0, TOP + 1.4), K.at(0.8, -29.0)], LACQUER)
            K.line(d, [K.at(-5.0, TOP + 1.0), K.at(4.0, -15.6)], GI_LIGHT, 1.2)
            K.line(d, [K.at(5.0, TOP + 1.0), K.at(0.6, -25.0)], GI_LIGHT, 1.2)
        # The rope, with its twist and its two papers.
        K.poly(d, [K.at(-40.0, -15.0), K.at(40.0, -15.0), K.at(40.0, -6.0), K.at(-40.0, -6.0)], rope)
        K.line(d, [K.at(-40.0, -15.0), K.at(40.0, -15.0)], rope_dark, 0.8)
        K.line(d, [K.at(-40.0, -6.0), K.at(40.0, -6.0)], rope_dark, 0.8)
        for k in range(-6, 7):
            x = k * 4.4
            K.line(d, [K.at(x - 1.5, -14.4), K.at(x + 1.5, -6.6)], rope_dark, 0.7)
        for x in (-8.0, 3.0):
            K.poly(d, [K.at(x, -5.6), K.at(x + 4.0, -5.6), K.at(x + 4.0, -0.8), K.at(x + 5.8, -0.8), K.at(x + 5.8, 4.2), K.at(x + 4.0, 4.2), K.at(x + 4.0, 9.4),
                       K.at(x, 9.4), K.at(x, 4.0), K.at(x + 1.8, 4.0), K.at(x + 1.8, -0.6), K.at(x, -0.6)], PAPER, OUTLINE, 0.5)
        K.line(d, [K.at(-13.0, -28.0), K.at(-11.0, -17.0)], GI_DARK, 0.7)
        K.line(d, [K.at(13.0, -28.0), K.at(11.0, -17.0)], GI_DARK, 0.7)
        K.poly(d, [K.at(-40.0, 11.0), K.at(40.0, 11.0), K.at(40.0, 13.4), K.at(-40.0, 13.4)], GI_LIGHT)

    X.front_torso = R.make_front_torso(K, ("heavy",), GI, GI_DARK, [(TOP - 0.4, 6.4), (TOP + 4.0, 17.0), (-30.0, 21.6), (-16.0, 24.8), (-6.0, 25.2), (2.0, 23.0),
                                                                   (14.0, 21.0)], shoulder=(17.4, -35.6, 8.8, 8.4), detail=_front_gi)

    def _front_hood_shape(d) -> None:
        K.oval(d, K.at(0.0, -2.2), 10.4, 10.6, WHITE)
        K.oval(d, K.at(0.0, 4.4), 8.8, 8.6, WHITE)
        K.poly(d, [K.at(8.6, -3.0), K.at(13.4, -5.0), K.at(13.8, -0.6), K.at(9.0, 1.0)], WHITE)

    def _front_hood(d) -> None:
        # All of it is cloth but the slit at his eyes.
        K.poly(d, [K.at(-30.0, -30.0), K.at(30.0, -30.0), K.at(30.0, -0.6), K.at(7.8, -0.6), K.at(7.2, -4.0), K.at(-7.2, -4.0), K.at(-7.8, -0.6), K.at(-30.0, -0.6)],
               HOOD)
        K.poly(d, [K.at(-30.0, -0.6), K.at(-7.8, -0.6), K.at(-7.2, 2.6), K.at(0.0, 3.2), K.at(7.2, 2.6), K.at(7.8, -0.6), K.at(30.0, -0.6), K.at(30.0, 30.0),
                   K.at(-30.0, 30.0)], HOOD)
        K.line(d, [K.at(-7.8, -0.6), K.at(-7.2, 2.6), K.at(0.0, 3.2), K.at(7.2, 2.6), K.at(7.8, -0.6)], HOOD_DARK, 0.7)
        K.line(d, [K.at(-4.6, 6.0), K.at(0.0, 8.2), K.at(4.6, 6.0)], HOOD_DARK, 0.6)
        K.line(d, [K.at(-4.0, 10.0), K.at(0.0, 11.6), K.at(4.0, 10.0)], HOOD_DARK, 0.5)
        if look.brow == "headband":
            # The red band round his brow.
            K.poly(d, [K.at(-10.6, -10.6), K.at(10.6, -10.6), K.at(10.8, -6.4), K.at(-10.8, -6.4)], LACQUER, OUTLINE, 0.6)
            K.line(d, [K.at(-10.4, -9.4), K.at(10.4, -9.4)], (214, 84, 76, 255), 0.6)
            return
        # The plate on his brow: iron, with a red bar and brass rivets.
        K.poly(d, [K.at(-7.4, -11.0), K.at(7.4, -11.0), K.at(8.0, -4.8), K.at(-8.0, -4.8)], IRON, OUTLINE, 0.6)
        K.poly(d, [K.at(-7.0, -10.4), K.at(7.0, -10.4), K.at(7.2, -8.8), K.at(-7.2, -8.8)], IRON_LIGHT)
        K.poly(d, [K.at(-1.2, -10.8), K.at(1.2, -10.8), K.at(1.4, -5.2), K.at(-1.4, -5.2)], LACQUER)
        for x in (-5.4, 5.4):
            K.oval(d, K.at(x, -6.8), 0.8, 0.8, BRASS)

    def _front_scar(d) -> None:
        # The old cut through his right brow.
        K.line(d, [K.at(-4.6, -4.0), K.at(-3.4, 1.4)], SKIN_DEEP, 0.5)

    if band:
        _front_head = R.make_front_head(K, ("heavy",), SKIN, SKIN_DEEP, wide=9.6, jaw=8.0, chin=4.2, shape=_front_hood_shape, hair=_front_hood, face=_front_scar)
    else:
        _front_head = R.make_front_head(K, ("heavy",), SLIT, SLIT, wide=9.6, jaw=8.0, chin=4.2, shape=_front_hood_shape, hair=_front_hood)

    def _front_eyes(mode: str):
        """His eyes from the front: each slants down to the middle."""

        def paint(d) -> None:
            for sx in (-1.0, 1.0):
                ex, ey = 3.6 * sx, -0.8
                if mode in ("closed", "wince", "happy"):
                    K.line(d, [K.at(ex + 2.0 * sx, ey - 0.5), K.at(ex - 1.9 * sx, ey + 0.5)], EYE, 0.7)
                    continue
                tall = 2.0 if mode == "wide" else 1.4
                K.poly(d, [K.at(ex + 2.4 * sx, ey - tall), K.at(ex - 2.2 * sx, ey - 0.1), K.at(ex - 1.6 * sx, ey + tall * 0.9), K.at(ex + 1.9 * sx, ey + tall * 0.5)], EYE)
                K.oval(d, K.at(ex - 0.2 * sx, ey + 0.1), 0.9, 0.7, EYE_HOT)

        return K.piece(("heavy_front_eyes", mode), paint)

    if band:
        _front_skin_eyes = R.make_front_eyes(K, ("heavy",), spread=3.6, y=-0.8, ink=INK, iris=IRIS, size=0.9)
        _front_brows = R.make_front_brows(K, ("heavy",), INK, spread=3.6, y=-3.2, width=1.5)
        X.front_head_layers = lambda pose: [(_front_head(), "head"), (_front_skin_eyes(str(pose["eyes"])), "eyes"), (_front_brows(-1), "brows")]
    else:
        X.front_head_layers = lambda pose: [(_front_head(), "head"), (_front_eyes(str(pose["eyes"])), "eyes")]
    X.front_shoe = R.make_front_shoe(K, HOOD, HOOD_DARK, BUILD.ankle_up, wide=1.2)

    def _front_pauldron(d) -> None:
        K.poly(d, [K.at(-9.0, -3.0), K.at(-4.0, -8.0), K.at(5.0, -8.6), K.at(10.0, -4.0), K.at(8.0, -3.0), K.at(-7.0, -2.0)], IRON_LIGHT)
        for y in (0.6, 4.0):
            K.line(d, [K.at(-9.4, y), K.at(0.0, y + 2.2), K.at(9.8, y - 0.6)], LACQUER, 0.9)
        for x in (-6.0, 0.0, 6.0):
            K.oval(d, K.at(x, -5.0), 0.8, 0.8, BRASS)

    def _front_effects(ctx) -> List[Stamp]:
        hand = ctx.left_hand
        shoulder = (ctx.hip[0] - X.front_span[0] - 1.0, ctx.hip[1] + BUILD.neck[1] + 4.0)
        part = K.solid(("heavy_pauldron_front",), lambda d: K.poly(d, [K.at(-9.0, -3.0), K.at(-4.0, -8.0), K.at(5.0, -8.6), K.at(10.0, -4.0), K.at(9.6, 4.6), K.at(0.0, 8.0),
                                                                        K.at(-9.4, 5.0)], WHITE),
                       IRON, _front_pauldron, outline=1.2, rim=0.3, shade=0.35, shade_colour=IRON_DARK)
        return [(part, shoulder, "front_pauldron", -6.0), (_kanabo(), hand, "front_kanabo", 96.0), (X.hand("fist", True), hand, "front_hand_on_club", 84.0)]

    X.front_effects = _front_effects

    @X.front_row
    def front(i: int, n: int):
        _, s, _c = loop(i, n)
        arms = dict(R.front_arms(X, "sides"), la=(4.0, 17.0 + 0.3 * s), lz=0.15, lh="fist", rh="fist")
        return R.FP(hip=(0.0, 0.5 + 0.5 * s), head=(0.0, 0.2 * s, 0.0), eyes="closed" if i == n - 2 else "open", **arms)

    X.rows = list(X.rows) + [("front", 8, 145)]

    metadata = _metadata(look)
    render, main, render_canonical = R.entry_points(X, metadata, look.display_name)

    def render_portraits(out_dir, **opts):
        """His portraits are frames of this sheet."""
        del opts
        return X.portraits(out_dir, {"default": ("idle", (1,), 0, False), "talking": ("idle", (0, 1, 2, 3, 4, 5), 130, True)}, view_width=30.0)

    return SimpleNamespace(X=X, metadata=metadata, render=render, main=main, render_canonical=render_canonical, render_portraits=render_portraits)


MADE: Dict[str, SimpleNamespace] = {name: _make(look) for name, look in LOOKS.items()}

#: The Ninja Heavy himself, as the module's own names.
X = MADE[TARGET_NAME].X
K = X.K
P = X.P
FRAME_SIZE = X.frame
ROWS = X.rows
_render_frame = X.render_frame
render, main, render_canonical, render_portraits = (MADE[TARGET_NAME].render, MADE[TARGET_NAME].main, MADE[TARGET_NAME].render_canonical,
                                                    MADE[TARGET_NAME].render_portraits)

TARGETS = {name: {"render": made.render, "actor_metadata": made.metadata, "render_portraits": made.render_portraits} for name, made in MADE.items()}

if __name__ == "__main__":
    raise SystemExit(main())
