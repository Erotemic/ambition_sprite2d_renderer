"""Sprite generator for Mami Marzakhani: the geometer who draws the surface on
the floor and then walks its shortest paths.

A warm parody of Maryam Mirzakhani.

The look (2026-10-13): a slight woman seen three quarters from the front,
facing right. Dark hair cut short and close to her head, as she wore it;
large calm eyes, a small smile that she keeps to herself. A long garnet
jacket with one side longer than the other, an ivory collar, dark trousers,
flat shoes. She is quick on her feet, and when she thinks she goes down on
one knee and draws on the floor.

She is drawn from the woman, and as herself, not as one shape that every
woman of the cast shares (Jon, 2026-10-13: "The women need to read more as
women, and there needs to be variation"; and, of another person of the cast:
"needs to read like paul erdos not bearnie sanders"). She is a grown woman,
not a mascot. She holds nothing; there is no drop shadow.

What she shows: a geodesic, bent by the surface it is on; a boundary that
folds shut; a surface with two handles that opens over her like a flower.

She is a person of ``_person_rig``: the bones, the poses and the frame are
shared; the head, the clothes, how she stands and what she draws are hers.
Her dialogue portraits are frames of this sheet (``Person.portraits``).
"""

from __future__ import annotations

import math
from typing import List

from ._ai_era_kit import OUTLINE, WHITE, RGBA, lerp, mix, pin
from . import _person_rig as R
from ._person_rig import Build, Person, Stamp, loop, shot

TARGET_NAME = "mami_marzakhani"
DISPLAY_NAME = "Mami Marzakhani"
USES_PROPS = False
USES_DROP_SHADOW = False

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_mami_marzakhani",
        "display_name": "Mami Marzakhani",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": [
            "story",
            "humanoid",
            "mathematician",
            "geometer",
            "boundary_walker",
            "playable_candidate",
        ],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": True,
            "climb": True,
            "fly": None,
            "swim": True,
            "crawl": True,
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
        "portrait": {
            "face_guide": {
                "center": {"x": 64.0, "y": 33.0},
                "size": {"w": 30.0, "h": 34.0},
                "source_size": {"w": 128.0, "h": 128.0},
            }
        },
    },
    "tags": [
        "story",
        "humanoid",
        "mathematician",
        "geometer",
        "boundary_walker",
        "playable_candidate",
    ],
    "sockets": {
        "head": {
            "source": "explicit.mami_marzakhani",
            "point": {"x": 64.0, "y": 31.0},
        },
        "chest": {
            "source": "explicit.mami_marzakhani",
            "point": {"x": 64.0, "y": 68.0},
        },
        "hand_l": {
            "source": "explicit.mami_marzakhani",
            "point": {"x": 43.0, "y": 78.0},
        },
        "hand_r": {
            "source": "explicit.mami_marzakhani",
            "point": {"x": 86.0, "y": 77.0},
        },
        "speech_bubble": {
            "source": "explicit.mami_marzakhani",
            "point": {"x": 64.0, "y": 4.0},
        },
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "traversal.jump": {"animation": "jump", "events": []},
        "traversal.fall": {"animation": "fall", "events": []},
        "action.melee.primary": {"animation": "geodesic_sweep", "events": []},
        "action.ranged.primary": {"animation": "boundary_fold", "events": []},
        "action.special.primary": {"animation": "moduli_bloom", "events": []},
        "action.defense.block": {"animation": "block", "events": []},
        "action.defense.roll": {"animation": "roll", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
    },
    "provenance": {
        "variant_family": TARGET_NAME,
        "variant_id": "gpt_5_6_thinking_original_2026_07_20",
        "lineage": [
            {
                "revision_id": "mami_marzakhani_name_and_direction",
                "creator_kind": "human",
                "creator": "Jon Crall",
                "contribution": "character_name_quality_bar_and_no_drop_shadow_direction",
            },
            {
                "revision_id": "mami_marzakhani_procedural_sprite_v1",
                "creator_kind": "model",
                "creator": "gpt-5.6-thinking",
                "parent_revision_id": "mami_marzakhani_name_and_direction",
                "contribution": "procedural_full_action_sprite_and_native_portrait_authoring",
            },
            {
                "revision_id": "mami_marzakhani_rename_from_mary",
                "creator_kind": "human",
                "creator": "Jon Crall",
                "parent_revision_id": "mami_marzakhani_procedural_sprite_v1",
                "contribution": "renamed_character_mary_to_mami_across_target_and_assets",
            },
        ],
    },
}


ACTOR_METADATA.update(
    {
        "authoring_description": (
            "Mami Marzakhani is a warm, energetic parody of Maryam Mirzakhani. She is a modern "
            "geometer who draws sprawling surfaces on the floor, follows geodesics through curved "
            "spaces, and treats loops, moduli, and route-finding as one continuous act of visual "
            "thought."
        ),
        "gameplay_description": (
            "Use as a geometer, route-finding guide, contour-based fighter, or playable traversal "
            "specialist. Her abilities should bend surfaces, expose cheap geodesics, count loops, and "
            "turn chalk-like drawings into paths or boundaries."
        ),
    }
)
ACTOR_METADATA.setdefault("dialogue_hints", {}).setdefault(
    "barks",
    [
        'Careful where you say straight line in here.',
        'You already solve this. You call it finding the route.',
        'Stop fighting the geometry and ask what it makes cheap.',
    ],
)

# A restrained, warm palette.  Hair and clothing use several close values so
# the sprite reads as dimensional without relying on blur, gradients, or a cast
# floor shadow.
JACKET: RGBA = (150, 46, 66, 255)
JACKET_DARK: RGBA = (98, 28, 50, 255)
JACKET_LIGHT: RGBA = (196, 82, 98, 255)
COLLAR: RGBA = (248, 240, 222, 255)
TROUSER: RGBA = (52, 50, 68, 255)
TROUSER_DARK: RGBA = (34, 32, 48, 255)
SHOE: RGBA = (60, 44, 48, 255)
SHOE_DARK: RGBA = (32, 24, 30, 255)
SKIN: RGBA = (226, 180, 146, 255)
SKIN_SHADE: RGBA = (192, 142, 116, 255)
SKIN_DEEP: RGBA = (142, 94, 84, 255)
HAIR: RGBA = (44, 36, 40, 255)
HAIR_LIGHT: RGBA = (96, 82, 88, 255)
INK: RGBA = (26, 22, 30, 255)
CURVE: RGBA = (252, 214, 120, 255)
CURVE_DARK: RGBA = (204, 128, 56, 255)
SURFACE: RGBA = (130, 220, 210, 255)
SURFACE_DARK: RGBA = (44, 124, 134, 255)
SURFACE_FILL: RGBA = (130, 220, 210, 80)
PAPER: RGBA = (250, 246, 232, 255)
PAPER_DARK: RGBA = (198, 190, 170, 255)

#: Slight and quick: 160 cm.
BUILD = Build(hip_up=45.0, thigh=22.0, shin=20.3, neck=(0.4, -34.0), upper=17.8, fore=16.8, near_shoulder=(-4.4, -29.8), far_shoulder=(5.4, -29.4),
              near_hip=(-3.6, 0.0), far_hip=(3.6, 0.0), head_up=(1.0, -12.2), height=102.0, half_width=(11.5, 13.0))

X = Person(TARGET_NAME, BUILD)
K = X.K
P = X.P
TOP = BUILD.neck[1] - 2.0
FRAME_W, FRAME_H = X.frame


def _front(d, hb: float, hf: float) -> None:
    """The ivory collar, the one line of the jacket's edge, and its long side
    down behind her."""
    K.poly(d, [K.at(0.4, TOP - 1.0), K.at(8.0, TOP - 1.0), K.at(7.0, TOP + 5.0), K.at(4.4, TOP + 8.0), K.at(1.4, TOP + 5.0)], COLLAR)
    K.poly(d, [K.at(2.6, TOP - 1.0), K.at(6.0, TOP - 1.0), K.at(4.4, TOP + 4.0)], SKIN_SHADE)
    K.line(d, [K.at(4.4, TOP + 8.0), K.at(5.0, -12.0), K.at(6.8 + hf * 0.6, 10.0)], JACKET_DARK, 0.8)
    K.poly(d, [K.at(-1.0, TOP + 1.0), K.at(2.0, TOP), K.at(4.4, TOP + 8.0), K.at(1.0, TOP + 10.0)], JACKET_LIGHT)
    K.oval(d, K.at(2.6, -8.0), 1.0, 1.0, COLLAR)


def _torso(hem_back: int, hem_front: int):
    """Her jacket: fitted, to her hip in front and longer behind."""
    hb, hf = float(hem_back), float(hem_front)

    def shape(d) -> None:
        K.poly(d, [K.at(-3.0, TOP), K.at(-7.0, TOP + 4.0), K.at(-7.2, TOP + 12.0), K.at(-5.2, -13.0), K.at(-7.8, -2.0), K.at(-10.4 - hb * 1.5, 19.0 - hb * 0.3),
                   K.at(-4.0 - hb, 20.0), K.at(0.0, 8.0), K.at(8.8 + hf, 7.0), K.at(8.6, -2.0), K.at(5.6, -13.0), K.at(8.0, TOP + 17.4), K.at(9.6, TOP + 13.4),
                   K.at(8.6, TOP + 9.0), K.at(6.4, TOP + 3.4), K.at(3.2, TOP - 0.4)], WHITE)
        K.oval(d, K.at(-4.4, -29.2), 4.2, 4.8, WHITE)
        K.oval(d, K.at(5.0, -29.0), 3.8, 4.4, WHITE)

    def paint(d) -> None:
        K.poly(d, [K.at(6.4, TOP - 2.0), K.at(40.0, TOP - 2.0), K.at(40.0, 24.0), K.at(7.6 + hf * 0.6, 24.0), K.at(5.6, -13.0)], JACKET_DARK)
        K.line(d, [K.at(3.6, TOP + 15.4), K.at(6.0, TOP + 16.6), K.at(7.6, TOP + 15.0)], JACKET_DARK, 0.7)
        _front(d, hb, hf)
        K.line(d, [K.at(-5.0, -2.0), K.at(-6.6 - hb, 17.0)], JACKET_DARK, 0.7)

    return K.solid(("mami_jacket", hem_back, hem_front), shape, JACKET, paint, outline=1.3, rim=0.3, shade=0.4, shade_colour=JACKET_DARK)


X.torso = _torso


def _hair_shape(d) -> None:
    # Short: soft over her brow, over her ear, and in to the back of her neck.
    K.oval(d, K.at(-0.8, -4.2), 9.0, 8.6, WHITE)
    K.poly(d, [K.at(2.0, -11.0), K.at(8.8, -9.6), K.at(9.8, -4.6), K.at(5.0, -6.0)], WHITE)
    K.poly(d, [K.at(-8.8, -4.0), K.at(-9.4, 3.0), K.at(-7.6, 6.6), K.at(-3.6, 5.6), K.at(-2.0, 0.0)], WHITE)


def _hair(d) -> None:
    K.poly(d, [K.at(20.0, -5.0), K.at(9.6, -5.0), K.at(7.4, -7.4), K.at(4.4, -6.0), K.at(1.6, -3.6), K.at(-0.6, -2.6), K.at(-1.8, 0.6), K.at(-2.6, 3.6),
               K.at(-3.4, 7.0), K.at(-20.0, 7.0), K.at(-20.0, -26.0), K.at(20.0, -26.0)], HAIR)
    for strand in ([(7.6, -8.6), (2.0, -10.0), (-4.0, -8.0)], [(3.0, -6.6), (-2.0, -7.0), (-6.4, -3.6)], [(-5.4, -0.6), (-7.2, 1.6)]):
        K.line(d, [K.at(x, y) for x, y in strand], HAIR_LIGHT, 0.6)


_head = R.make_head(K, ("mami",), SKIN, SKIN_SHADE, SKIN_DEEP, skull=(0.0, -2.2, 7.6, 8.6), jaw=(2.4, 3.6, 5.2, 6.8),
                    nose=((7.2, 0.9), (8.6, 3.0), (8.2, 3.8), (7.2, 4.0)), ear=None, shape=_hair_shape, under=_hair,
                    over=lambda d: K.oval(d, K.at(-1.6, 4.6), 0.9, 0.9, CURVE))
_eyes = R.make_eyes(K, (2.4, -0.2), (7.4, -0.4), ink=INK, white=None, lid=INK, size=1.0)
_brows = R.make_brows(K, [(-0.4, -3.8), (2.0, -4.6), (4.6, -4.2)], [(6.0, -4.3), (7.4, -4.6), (8.6, -4.2)], HAIR, 0.9)
_mouth = R.make_mouth(K, (5.6, 7.0), (130, 54, 66, 255), wide=0.8, lips=(206, 96, 104, 255))

X.head_layers = lambda pose: [(_head(), "head"), (_eyes(str(pose["eyes"])), "eyes"), (_brows(R.brow_mood(pose)), "brows"),
                              (_mouth(str(pose["mouth"])), "mouth")]
X.neck = R.make_neck(K, SKIN_SHADE, 3.6)
X.upper_arm = lambda near: [(0.0, 1.0, 5.8, 5.0, JACKET if near else JACKET_DARK)]
X.forearm = lambda near: [(0.0, 1.0, 5.0, 4.2, JACKET if near else JACKET_DARK)]
X.thigh = lambda near: [(0.0, 1.0, 6.6, 5.4, TROUSER if near else TROUSER_DARK)]
X.shin = lambda near: [(0.0, 1.0, 5.4, 4.4, TROUSER if near else TROUSER_DARK)]
X.hand = R.make_hand(K, SKIN, SKIN_SHADE, SKIN_DEEP, COLLAR, (206, 200, 190, 255), size=0.86)
X.shoe = R.make_shoe(K, SHOE, SHOE_DARK, BUILD.ankle_up, long=0.92)

# ---- How she holds herself ---------------------------------------------------

AT_CHIN = (8.5, 1.5)
X.set_rest(na=(-2.0, 24.5), fa=(2.0, 24.0), nf=(-3.6, 0.0, 0.0), ff=(4.6, 0.0, 0.0))


@X.row
def idle(i: int, n: int):
    # A hand at her chin; she is following a path that only she can see yet.
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.3 + 0.3 * s), lean=2.0, head=(0.3, 0.0, 3.0 + 3.0 * c), na=AT_CHIN, nh="fist", fa=(-1.0, 21.0), eyes="closed" if i == n - 2 else "open",
             mouth="smile" if c < 0.0 else "flat")


@X.row
def talk(i: int, n: int):
    # Her hands draw what she says.
    _, s, c = loop(i, n)
    return P(hip=(0.0, 0.3 * s), head=(0.3, 0.0, 2.5 * s), na=(14.0 + 4.0 * c, 4.0 - 5.0 * max(0.0, s)), nh="open", fa=(16.0 - 3.0 * c, 8.0 + 3.0 * min(0.0, s)), fh="open",
             mouth=("open", "smile", "big", "smile")[i % 4], brows=1.0 if s > 0.3 else 0.0)


@X.row
def geodesic_sweep(i: int, n: int):
    # One long line with her whole arm, from behind her to in front.
    u = shot(i, n)
    a = math.radians(lerp(-150.0, 30.0, R.ease(min(1.0, u / 0.7))))
    hand = (26.0 * math.cos(a), 26.0 * math.sin(a))
    return P(hip=(lerp(-2.0, 4.0, u), 3.0), lean=lerp(-6.0, 14.0, u), na=hand, nab=-1.0 if hand[1] < -6.0 and hand[0] < 6.0 else 1.0,
             arm="under" if hand[1] < -4.0 and hand[0] > -14.0 else "over", nh="point", fa=(-8.0, 14.0), nf=(-7.0, 0.0, 0.0), ff=(9.0, 0.0, 0.0), mouth="open",
             brows=-1.0, hem=(4.0 * u, 1.0))


@X.row
def boundary_fold(i: int, n: int):
    # Both hands, wide, and then they come together: the boundary is shut.
    wide = P(hip=(0.0, 2.0), lean=-2.0, na=(-14.0, -6.0), nab=-1.0, fa=(22.0, -6.0), nh="open", fh="open", brows=1.0, mouth="open")
    shut = P(hip=(2.0, 3.0), lean=8.0, na=(16.0, 2.0), fa=(17.0, 6.0), nh="flat", fh="flat", brows=-1.0)
    return X.keys(shot(i, n), [(0.0, P()), (0.25, wide), (0.6, shut), (0.85, shut), (1.0, P())])


@X.row
def moduli_bloom(i: int, n: int):
    # Her arms open up and out, and the surface opens over her.
    low = P(hip=(0.0, 6.0), lean=10.0, na=(8.0, 16.0), fa=(10.0, 15.0), nh="flat", fh="flat", eyes="closed")
    up = P(hip=(0.0, -1.0), lean=-4.0, head=(0.0, 0.0, -12.0), na=(-12.0, -22.0), nab=-1.0, fa=(18.0, -20.0), nh="open", fh="open", eyes="up", mouth="open", brows=1.0)
    return X.keys(shot(i, n), [(0.0, P()), (0.2, low), (0.5, up), (0.9, up), (1.0, P())])


#: On one knee, drawing on the floor.
DRAWING = P(hip=(-1.0, 17.0), lean=28.0, head=(1.0, 0.0, 6.0), na=(16.0, 23.0), nh="fist", fa=(4.0, 14.0), nf=(-11.0, 0.0, 34.0), ff=(9.0, 0.0, 0.0), hem=(3.0, 1.0))


@X.row
def taunt(i: int, n: int):
    # She goes down on one knee and draws it on the floor, as she does at home.
    _, s, c = loop(i, n)
    return X.keys(shot(i, n), [(0.0, P()), (0.25, DRAWING), (0.6, dict(DRAWING, na=(20.0 + 2.0 * c, 23.0))), (1.0, dict(DRAWING, na=(13.0, 23.0), mouth="smile", eyes="happy"))])


_fall = X.poses["death"]


@X.row
def death(i: int, n: int):
    # As she goes over, one frame is a little higher: its lowest pixels are
    # on the edge of the cell.
    pose = dict(X.full(_fall(i, n)))
    if i == 4:
        ox, oy = pose["off"]  # type: ignore[misc]
        pose["off"] = (ox, oy - 3.0)
    return pose


X.rows = [("idle", 8, 150), ("walk", 8, 104), ("run", 8, 78), ("crouch", 6, 96), ("crouch_walk", 8, 90), ("jump", 6, 88), ("fall", 6, 92), ("land_hard", 7, 82),
          ("dash_startup", 4, 52), ("dash", 6, 58), ("slide", 6, 70), ("roll", 8, 60), ("wall_grab", 6, 104), ("wall_jump", 6, 82), ("ledge_grab", 6, 98),
          ("ledge_climb", 6, 94), ("climb", 8, 98), ("swim", 8, 104), ("block", 6, 82), ("hit", 5, 84), ("death", 8, 106), ("talk", 8, 106), ("interact", 8, 94),
          ("geodesic_sweep", 8, 66), ("boundary_fold", 8, 72), ("moduli_bloom", 10, 78), ("celebrate", 8, 88), ("taunt", 8, 94)]

# ---- From the front ------------------------------------------------------------

def _front_garnet(d) -> None:
    """Her jacket from the front: the pale collar, the light on her bust and
    the shade under it, the buttons."""
    by = TOP + 12.5
    K.poly(d, [K.at(-3.0, TOP - 1.0), K.at(3.0, TOP - 1.0), K.at(0.0, TOP + 6.0)], SKIN_SHADE)
    for sx in (-1.0, 1.0):
        K.poly(d, [K.at(1.0 * sx, TOP + 3.0), K.at(4.6 * sx, TOP - 1.0), K.at(5.4 * sx, TOP + 3.0), K.at(2.0 * sx, TOP + 8.0)], COLLAR)
        K.oval(d, K.at(4.2 * sx, by + 0.2), 2.4, 1.9, JACKET_LIGHT)
        K.poly(d, [K.at(0.8 * sx, by + 4.2), K.at(4.2 * sx, by + 5.0), K.at(8.0 * sx, by + 3.2), K.at(7.2 * sx, by + 5.8), K.at(4.0 * sx, by + 6.6), K.at(0.8 * sx, by + 5.6)],
               JACKET_DARK)
    K.line(d, [K.at(0.0, TOP + 8.0), K.at(0.0, 6.0)], JACKET_DARK, 0.6)
    for y in (-14.0, -8.0, -2.0):
        K.oval(d, K.at(1.4, y), 0.8, 0.8, COLLAR)


def _front_hair_shape(d) -> None:
    # Short and soft: over her ears, to her jaw.
    K.oval(d, K.at(0.0, -5.4), 9.6, 7.8, WHITE)
    for sx in (-1.0, 1.0):
        K.poly(d, [K.at(7.0 * sx, -6.0), K.at(10.0 * sx, -1.0), K.at(9.6 * sx, 5.0), K.at(7.0 * sx, 7.6), K.at(5.8 * sx, 3.0)], WHITE)


def _front_hair(d) -> None:
    K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, 10.0), K.at(6.0, 10.0), K.at(6.4, 2.0), K.at(7.0, -3.0), K.at(4.6, -6.8), K.at(-1.0, -7.6), K.at(-5.0, -5.6),
               K.at(-7.0, -3.0), K.at(-6.4, 2.0), K.at(-6.0, 10.0), K.at(-20.0, 10.0)], HAIR)
    K.line(d, [K.at(2.6, -12.6), K.at(1.6, -7.4)], (30, 24, 28, 255), 0.5)
    for strand in ([(-6.0, -9.0), (-2.0, -11.0), (1.0, -10.6)], [(4.0, -10.6), (7.6, -6.0), (8.4, 0.0)], [(-8.4, -3.0), (-8.0, 3.0)]):
        K.line(d, [K.at(x, y) for x, y in strand], HAIR_LIGHT, 0.6)


def _front_marks(d) -> None:
    K.line(d, [K.at(-0.3, -0.2), K.at(-1.0, 3.2), K.at(0.0, 4.0), K.at(1.0, 3.2)], SKIN_DEEP, 0.6)
    for sx in (-1.0, 1.0):
        K.oval(d, K.at(7.2 * sx, 6.0), 0.9, 0.9, CURVE)


X.front_torso = R.make_front_torso(K, ("mami",), JACKET, JACKET_DARK, [(TOP, 3.4), (TOP + 3.6, 7.2), (TOP + 12.5, 8.6), (-12.0, 6.2), (0.0, 8.0), (6.0, 8.4)],
                                   shoulder=(5.8, -29.6, 3.8, 4.2), detail=_front_garnet)
X.front_head_layers = R.front_face(R.make_front_head(K, ("mami",), SKIN, SKIN_DEEP, wide=7.6, jaw=6.2, chin=3.6, shape=_front_hair_shape, hair=_front_hair,
                                                    face=_front_marks),
                                   R.make_front_eyes(K, ("mami",), white=None, ink=INK, spread=3.2, y=-0.4, lash=0.5), R.make_front_brows(K, ("mami",), HAIR, spread=3.2, y=-3.8,
                                                                                                                                 width=0.9),
                                   R.make_front_mouth(K, ("mami",), y=7.8, colour=(130, 54, 66, 255), lips=(206, 96, 104, 255), wide=0.8))
X.front_shoe = R.make_front_shoe(K, SHOE, SHOE_DARK, BUILD.ankle_up, wide=0.9)
X.front_span = (7.0, 4.4)
R.add_front_rows(X)

# ---- What she shows ----------------------------------------------------------


def _geodesic(length: int, bend: int):
    """A geodesic, along +x from ``home``: it bends as the surface under it
    bends."""

    def paint(d) -> None:
        pts = [K.at(float(x), bend * math.sin(x / max(1, length) * math.pi) * 0.5 - 0.004 * bend * x) for x in range(0, length + 1, 3)]
        K.stroke(d, pts, CURVE_DARK, 3.0)
        K.stroke(d, pts, CURVE, 1.4)
        K.oval(d, pts[-1], 2.2, 2.2, CURVE_DARK)
        K.oval(d, pts[-1], 1.3, 1.3, WHITE)

    return K.aligned(("geodesic", length, bend), paint)


def _loop(radius: int, pinch: int):
    """A boundary: a loop, ``pinch`` of 4 folded shut."""

    def paint(d) -> None:
        ry = radius * (1.0 - 0.2 * pinch)
        pts = [K.at(radius * math.cos(math.radians(a)), ry * math.sin(math.radians(a))) for a in range(0, 361, 12)]
        K.line(d, pts, SURFACE_DARK, 2.8)
        K.line(d, pts, SURFACE, 1.2)

    return K.aligned(("loop", radius, pinch), paint)


def _surface(open_: int):
    """A surface with two handles, ``open_`` of 4 unfolded."""
    k = 0.4 + 0.15 * open_

    def paint(d) -> None:
        K.oval(d, K.home, 22.0 * k, 11.0 * k, SURFACE_FILL)
        outer = [K.at(22.0 * k * math.cos(math.radians(a)), 11.0 * k * math.sin(math.radians(a)) * (1.0 - 0.18 * math.cos(math.radians(2 * a)))) for a in range(0, 361, 10)]
        K.line(d, outer, SURFACE_DARK, 2.8)
        K.line(d, outer, SURFACE, 1.2)
        for sx in (-1.0, 1.0):
            c = (K.home[0] + sx * 9.6 * k, K.home[1])
            hole = [(c[0] + 4.6 * k * math.cos(math.radians(a)), c[1] + 2.0 * k * math.sin(math.radians(a))) for a in range(0, 361, 20)]
            K.line(d, hole, SURFACE_DARK, 2.2)
            K.line(d, hole, CURVE, 0.9)

    return K.aligned(("surface", open_), paint)


def _paper():
    def shape(d) -> None:
        K.poly(d, [K.at(-14.0, -3.0), K.at(16.0, -3.6), K.at(20.0, 2.0), K.at(-18.0, 2.4)], WHITE)

    def detail(d) -> None:
        K.line(d, [K.at(-12.0, 0.6), K.at(-4.0, -2.0), K.at(4.0, 1.0), K.at(13.0, -1.6)], CURVE_DARK, 0.9)
        K.oval(d, K.at(-6.0, 0.0), 2.4, 1.2, None, SURFACE_DARK, 0.6)  # type: ignore[arg-type]

    return K.solid(("floor_paper",), shape, PAPER, detail, outline=1.0, rim=0.2, shade=0.3, shade_colour=PAPER_DARK)


def _effects(ctx) -> List[Stamp]:
    out: List[Stamp] = []
    anim, u = ctx.anim, ctx.u
    if anim == "geodesic_sweep" and u >= 0.25:
        length = 6 * int(round((14.0 + 30.0 * min(1.0, (u - 0.25) / 0.5)) / 6.0))
        out.append((_geodesic(length, 8), pin((ctx.hand[0] + 6.0, ctx.hand[1] - 2.0)), "geodesic", 0.0))
    elif anim == "boundary_fold" and 0.2 <= u <= 0.9:
        pinch = min(4, int((u - 0.2) / 0.12))
        mid = ((ctx.hand[0] + ctx.far_hand[0]) / 2.0 + (10.0 if pinch >= 3 else 0.0), min(ctx.hand[1], ctx.far_hand[1]) - 10.0)
        out.append((_loop(14 - 2 * min(3, pinch), pinch), pin(mid), "loop", 0.0))
    elif anim == "moduli_bloom" and 0.3 <= u <= 0.95:
        out.append((_surface(min(4, int((u - 0.3) / 0.1))), pin((ctx.head[0] + 2.0, ctx.head[1] - 30.0)), "surface", 0.0))
    elif anim == "taunt" and u >= 0.2:
        out.append((_paper(), (ctx.hip[0] + 30.0, ctx.ground - 2.4), "paper", 0.0))
    elif anim == "interact" and 0.35 <= u <= 0.7:
        out.append((R.tick(K, 4.0, CURVE, CURVE_DARK), (ctx.hand[0] + 16.0, ctx.hand[1] - 5.0), "tick", 0.0))
    elif anim == "celebrate":
        out.append((_loop(8, 0), pin((ctx.head[0] + 2.0, ctx.head[1] - 26.0)), "loop", 0.0))
    return out


X.effects = _effects

# Her dialogue portraits: the painted ones of the sheet before this.
PORTRAIT_W, PORTRAIT_H = 256, 320


def render_portraits(out_dir, **opts):
    """Her portraits are frames of this sheet."""
    del opts
    return X.portraits(out_dir, {
        "default": ("idle", (0,), 0, False),
        "explaining": ("talk", tuple(range(8)), 104, True),
        "thinking": ("idle", tuple(range(6)), 128, True),
        "delighted": ("celebrate", (4,), 0, False),
    }, view_width=27.0, size=(PORTRAIT_W, PORTRAIT_H))
render_frame = X.render_frame

ROWS = X.rows
_render_frame = X.render_frame
render, main, render_canonical = R.entry_points(X, ACTOR_METADATA, DISPLAY_NAME)
TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}


if __name__ == "__main__":
    raise SystemExit(main())
