"""Sprite generator for the Shadow Oni Leader: the master of the Shadow Dojo.

The look (2026-10-13, a redraw: Jon, "the ninja oni leader also needs redone
artwork"; the picture the ninjas of the game come from has him in it): a tall
man of 183 cm in the armour of a warlord, seen three quarters from the front,
facing right. His ninjas are grey and bare of ornament. He is black and blue,
and all of him is plate and cord:

- a helmet with two great horns that go up and out, dark outside and red
  inside, and a guard for his neck behind;
- a mask the colour of bone, with the brow and the teeth of a skull, and two
  red lights where its eyes are (the eyes of his ninjas are his);
- a cuirass and a long skirt of small plates in rows, laced in dark blue, and
  a guard like them on each shoulder;
- sleeves of dark teal under plates on his forearms; plates on his shins;
- a great sword, longer than the sword of his duelist.

He shows no skin. He is a man in armour and not a demon: the oni is his mask.
There is no drop shadow.

His name is Zorlack 8. It is a secret (Jon, 2026-10-13: "that is a secret
name, just document it in his generator file so we can use it in gameplay.
Keep the current title for the nameplate"): his nameplate and his catalog row
say "Shadow Oni Leader", and no art and no label of this file shows the name.
``SECRET_NAME`` holds it for the day the game says it.

A pose that is held keeps the sword off his face. At rest he does not hold a
guard: the point of his sword is on the ground in front of him and his two
hands are on the end of its grip. He waits.

The rows are the ones a striker of the game plays, the eleven the old sheet
had: ``idle``, ``walk`` (the sword low at his side), ``run`` and ``dash`` (the
sword behind him), ``jump``, ``fall``, ``slash`` (one cut with two hands, from
over his far shoulder to the ground), ``hit``, ``death``, and the two poses of
a blink: ``blink_out`` (his open hand out: the order) and ``blink_in`` (he
comes back low). The warp of a blink is the engine's. ``front`` is the row he
turns through: he faces you, the sword planted in front of him.

He is a person of ``_person_rig``: the bones, the poses and the frame are
shared; the head, the armour, the sword and how he stands are his.
"""

from __future__ import annotations

import math
from typing import List

from ._ai_era_kit import OUTLINE, WHITE, RGBA, pin
from . import _person_rig as R
from ._person_rig import Build, Person, Stamp, loop, shot

TARGET_NAME = "ninja_shadow_oni_leader"
TARGET_BASENAME = TARGET_NAME
DISPLAY_NAME = "Shadow Oni Leader"
#: His own name. Not his nameplate: see the top of this file.
SECRET_NAME = "Zorlack 8"

ACTOR_METADATA = {
    "actor": {"character_id": "npc_ninja_shadow_oni_leader", "display_name": "Shadow Oni Leader"},
    "lineage": {
        "family": "npc_ninja_shadow_oni_leader",
        "variant": "the_warlord",
        "parents": ["npc_ninja_shadow_oni_leader/moon_steel"],
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
        "traits": ["story", "humanoid", "enemy", "combatant", "ninja", "leader", "oni", "oni_mask", "horned_silhouette"],
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
    "tags": ["story", "humanoid", "enemy", "combatant", "ninja", "leader", "oni", "oni_mask", "horned_silhouette"],
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


#: The black and blue of his armour: its plates are near black, and the rows
#: of its lacing are a dark blue that can be seen on them.
PLATE: RGBA = (30, 35, 56, 255)
PLATE_DARK: RGBA = (13, 15, 28, 255)
PLATE_LIGHT: RGBA = (70, 84, 124, 255)
LACE: RGBA = (48, 62, 104, 255)
HELM: RGBA = (24, 26, 40, 255)
HELM_DARK: RGBA = (11, 12, 22, 255)
HELM_LIGHT: RGBA = (74, 84, 116, 255)
#: His horns: dark outside, red inside.
HORN: RGBA = (40, 30, 36, 255)
HORN_DARK: RGBA = (20, 14, 20, 255)
RED: RGBA = (184, 40, 40, 255)
RED_DARK: RGBA = (112, 24, 32, 255)
RED_LIGHT: RGBA = (226, 92, 76, 255)
#: His mask is the colour of bone.
BONE: RGBA = (204, 204, 190, 255)
BONE_SHADE: RGBA = (148, 150, 144, 255)
BONE_DEEP: RGBA = (82, 84, 90, 255)
SOCKET: RGBA = (16, 14, 22, 255)
EYE: RGBA = (240, 36, 40, 255)
EYE_HOT: RGBA = (255, 150, 118, 255)
#: His sleeves: a dark teal.
TEAL: RGBA = (32, 76, 84, 255)
TEAL_DARK: RGBA = (15, 40, 50, 255)
IRON: RGBA = (62, 70, 92, 255)
IRON_DARK: RGBA = (30, 34, 50, 255)
GLOVE: RGBA = (36, 38, 54, 255)
GLOVE_DARK: RGBA = (16, 17, 28, 255)
BRASS: RGBA = (222, 176, 84, 255)
BRASS_DARK: RGBA = (150, 104, 44, 255)
STEEL: RGBA = (226, 232, 240, 255)
STEEL_DARK: RGBA = (150, 160, 180, 255)
STEEL_LIGHT: RGBA = (255, 255, 255, 255)
CUT: RGBA = (236, 242, 250, 255)
DUST: RGBA = (196, 190, 196, 255)
DUST_DARK: RGBA = (120, 116, 132, 255)

#: 183 cm (168 cm is 108 pixels), and wide at the shoulder.
BUILD = Build(hip_up=52.6, thigh=25.6, shin=24.6, neck=(1.0, -39.4), upper=20.6, fore=19.4, near_shoulder=(-8.6, -35.0), far_shoulder=(10.0, -34.6),
              near_hip=(-4.4, 0.0), far_hip=(4.4, 0.0), head_up=(1.4, -12.2), height=117.6, half_width=(16.0, 18.0))

X = Person(TARGET_NAME, BUILD, frame=(288, 224), ground=210.0, cx=132.0)
K = X.K
P = X.P
U = X.U
FRAME_SIZE = X.frame
TOP = BUILD.neck[1] - 2.0
#: How far under his hips the skirt of his armour goes.
SKIRT = 25.0
#: The sword: its blade past the guard, the guard in front of his near hand,
#: and the end of the grip behind it (his far hand is there).
BLADE = 60.0
GUARD_AT = 3.6
BUTT = 10.0


def _rows(d, x0: float, x1: float, y0: float, y1: float, step: float, slope: float = 0.0) -> None:
    """The rows of small plates: a line of lacing for each row."""
    y = y0
    while y < y1:
        K.line(d, [K.at(x0, y), K.at(x1, y + slope)], LACE, 0.8)
        y += step


def _front(d, hb: float, hf: float) -> None:
    """The cuirass and the skirt: rows of plates, the cord at his chest, his
    sash, and the mark of the dojo on the front plate of the skirt."""
    # The cuirass: its rows, a brighter edge at the top, the knot of red cord.
    _rows(d, -30.0, 30.0, -31.0, -13.0, 3.6, 0.6)
    K.poly(d, [K.at(-9.0, TOP + 2.4), K.at(11.0, TOP + 3.0), K.at(11.4, TOP + 5.2), K.at(-9.4, TOP + 4.6)], PLATE_LIGHT)
    K.line(d, [K.at(-1.0, -30.0), K.at(2.0, -25.0), K.at(5.0, -30.0)], RED, 0.9)
    K.oval(d, K.at(2.0, -25.0), 1.4, 1.4, RED, OUTLINE, 0.4)
    K.line(d, [K.at(1.2, -24.0), K.at(0.6, -19.6)], RED, 0.7)
    K.line(d, [K.at(2.8, -24.0), K.at(3.6, -19.6)], RED, 0.7)
    # His sash: dark red, with a brass clasp.
    K.poly(d, [K.at(-40.0, -12.6), K.at(40.0, -11.4), K.at(40.0, -6.6), K.at(-40.0, -7.8)], RED_DARK)
    K.line(d, [K.at(-40.0, -10.4), K.at(40.0, -9.2)], RED, 0.6)
    K.rrect(d, K.home[0] + 0.6, K.home[1] - 12.6, K.home[0] + 5.6, K.home[1] - 6.4, 0.6, BRASS, OUTLINE, 0.5)
    # The skirt: four hanging plates, each with its rows, and gaps between.
    _rows(d, -40.0 - hb, 40.0 + hf, -3.0, SKIRT - 1.0, 3.8, 0.4)
    for x in (-7.0, 1.6, 9.6):
        K.line(d, [K.at(x, -6.0), K.at(x * 1.14 + (hf if x > 0.0 else -hb) * 0.5, SKIRT)], PLATE_DARK, 1.1)
    K.poly(d, [K.at(-40.0 - hb, SKIRT - 2.6), K.at(40.0 + hf, SKIRT - 2.2), K.at(40.0 + hf, SKIRT + 2.0), K.at(-40.0 - hb, SKIRT + 2.0)], PLATE_LIGHT)
    # The mark of the dojo: a ring and a bar through it, in red.
    K.oval(d, K.at(5.4, 8.6), 3.0, 3.2, PLATE, RED, 0.8)
    K.line(d, [K.at(5.4, 4.6), K.at(5.6, 12.8)], RED, 0.8)


X.torso = R.make_torso(K, ("oni_leader",), PLATE, PLATE_DARK, back=(11.8, 12.2, 10.2, 12.8), front=(10.4, 12.4, 11.2, 13.4), hem_y=SKIRT, top=TOP,
                       shoulders=((-8.2, -34.2), (8.6, -33.8)), shoulder_r=(6.8, 6.0), neck=(-4.4, 4.4), shade_from=9.4, detail=_front)

NEAR_EYE = (2.2, -0.2)
FAR_EYE = (7.4, -0.4)


def _helmet_shape(d) -> None:
    # The bowl of the helmet, its peak in front, and the guard of his neck
    # behind: wide, and out from his head.
    K.oval(d, K.at(-0.2, -4.6), 10.0, 9.4, WHITE)
    K.poly(d, [K.at(6.0, -8.0), K.at(13.4, -5.0), K.at(12.6, -2.6), K.at(6.0, -3.6)], WHITE)
    K.poly(d, [K.at(-7.0, -6.0), K.at(-14.6, -1.0), K.at(-16.0, 6.4), K.at(-11.0, 9.6), K.at(-5.0, 6.0), K.at(-5.6, -2.0)], WHITE)
    # The jaw of the mask: square, lower than a face.
    K.poly(d, [K.at(-2.0, 3.0), K.at(9.4, 3.0), K.at(9.6, 9.6), K.at(6.4, 12.6), K.at(0.6, 12.2), K.at(-2.4, 8.6)], WHITE)


def _helmet(d) -> None:
    # The bowl, over all of the head down to the brow of the mask.
    K.poly(d, [K.at(-30.0, -30.0), K.at(30.0, -30.0), K.at(30.0, -3.8), K.at(11.0, -3.4), K.at(4.0, -4.6), K.at(-2.4, -3.4), K.at(-3.4, 2.0), K.at(-3.0, 10.0),
               K.at(-30.0, 12.0)], HELM)
    K.line(d, [K.at(11.0, -3.4), K.at(4.0, -4.6), K.at(-2.4, -3.4), K.at(-3.4, 2.0), K.at(-3.0, 9.0)], HELM_DARK, 0.8)
    # The ribs of the bowl, its band, and a brass stud on the band.
    for x, bend in ((-4.6, -2.0), (0.6, 0.0), (5.6, 1.6)):
        K.line(d, [K.at(x, -5.6), K.at(x + bend * 0.5, -10.0), K.at(x + bend, -13.6)], HELM_LIGHT, 0.5)
    K.poly(d, [K.at(-9.6, -6.4), K.at(12.6, -5.6), K.at(12.4, -3.8), K.at(-9.4, -4.4)], HELM_LIGHT)
    K.oval(d, K.at(4.6, -7.4), 1.3, 1.3, BRASS, OUTLINE, 0.4)
    # The guard of his neck: three rows, laced.
    for k in range(3):
        y = 0.0 + k * 3.0
        K.line(d, [K.at(-14.6 - k * 0.4, y), K.at(-5.4, y + 2.6)], LACE, 0.8)
    # The cheek of the mask is in shade under the helmet.
    K.poly(d, [K.at(-2.4, -3.4), K.at(1.0, -3.8), K.at(0.4, 4.0), K.at(-2.6, 8.0), K.at(-3.4, 2.0)], BONE_SHADE)


def _mask(d) -> None:
    # The sockets of a skull, the hole of its nose, and its teeth.
    K.poly(d, [K.at(-0.4, -3.0), K.at(4.8, -3.4), K.at(5.0, 1.0), K.at(2.0, 2.2), K.at(-0.6, 1.0)], SOCKET)
    K.poly(d, [K.at(5.8, -3.4), K.at(10.0, -3.0), K.at(9.8, 0.8), K.at(7.4, 1.8), K.at(5.8, 0.8)], SOCKET)
    K.poly(d, [K.at(6.0, 2.4), K.at(7.6, 2.0), K.at(8.0, 4.8), K.at(5.6, 4.6)], BONE_DEEP)
    K.line(d, [K.at(0.4, 7.0), K.at(5.0, 7.6), K.at(9.4, 6.8)], BONE_DEEP, 0.8)
    for x in (1.8, 3.8, 5.8, 7.8):
        K.line(d, [K.at(x, 5.6), K.at(x + 0.1, 8.8)], BONE_DEEP, 0.5)
    K.line(d, [K.at(0.0, 9.6), K.at(4.6, 10.6), K.at(9.0, 9.4)], BONE_SHADE, 0.6)
    # The line of the cheekbone, and a crack over the near brow.
    K.line(d, [K.at(-1.0, 2.6), K.at(1.4, 4.6), K.at(1.0, 7.0)], BONE_SHADE, 0.6)


_head = R.make_head(K, ("oni_leader",), BONE, BONE_SHADE, BONE_DEEP, skull=(0.2, -2.4, 8.4, 9.0), jaw=(3.0, 4.6, 6.0, 7.4),
                    nose=None, ear=None, shape=_helmet_shape, under=_helmet, over=_mask)


def _eyes(mode: str):
    """The two red lights in the sockets of his mask. Shut, each is a thin
    red line; struck, they are wide."""

    def paint(d) -> None:
        for (ex, ey), k in ((NEAR_EYE, 1.0), (FAR_EYE, 0.8)):
            if mode in ("closed", "wince", "happy"):
                K.line(d, [K.at(ex - 2.0 * k, ey - 0.4), K.at(ex + 1.9 * k, ey + 0.5)], EYE, 0.7)
                continue
            tall = 2.0 if mode == "wide" else 1.4
            K.poly(d, [K.at(ex - 2.3 * k, ey - tall), K.at(ex + 2.3 * k, ey - 0.2), K.at(ex + 1.6 * k, ey + tall * 0.9), K.at(ex - 1.8 * k, ey + tall * 0.5)], EYE)
            K.oval(d, K.at(ex + 0.3 * k, ey + 0.1), 0.9 * k, 0.7, EYE_HOT)

    return K.piece(("oni_leader_eyes", mode), paint)


#: A horn from its root, which goes out to -x: its outside edge from the root
#: to the point, its inside edge back, the red of its inside, and the rings of
#: its outside.
HORN_OUTSIDE = ((-3.6, 1.0), (-7.4, -4.0), (-9.6, -11.0), (-8.6, -18.0), (-5.0, -23.6))
HORN_INSIDE = ((-5.6, -18.0), (-5.0, -11.6), (-2.4, -6.0), (2.6, -2.4), (3.6, 1.4))
HORN_RED = ((-6.6, -20.6), (-5.0, -23.6), (-5.6, -18.0), (-5.0, -11.6), (-2.4, -6.0), (2.6, -2.4), (0.6, -1.6), (-4.0, -6.0), (-6.6, -12.0))
HORN_RINGS = (((-7.4, -4.6), (-5.6, -6.2)), ((-9.4, -10.6), (-7.2, -11.4)), ((-8.8, -16.6), (-6.8, -16.8)))


def _horn_shape(d, root, out: float, s: float) -> None:
    K.poly(d, [K.at(root[0] - out * x * s, root[1] + y * s) for x, y in HORN_OUTSIDE + HORN_INSIDE], WHITE)


def _horn_detail(d, root, out: float, s: float) -> None:
    K.poly(d, [K.at(root[0] - out * x * s, root[1] + y * s) for x, y in HORN_RED], RED)
    for a, b in HORN_RINGS:
        K.line(d, [K.at(root[0] - out * a[0] * s, root[1] + a[1] * s), K.at(root[0] - out * b[0] * s, root[1] + b[1] * s)], HORN_DARK, 0.5)


def _horn(near: bool):
    """A horn from its root at ``home``, on a side of the helmet: it goes out
    from the helmet and then up, and its point comes in again. The near horn
    goes out behind him and the far horn in front of him; the side of each
    that is toward the other is red."""
    out = -1.0 if near else 1.0
    s = 1.0 if near else 0.88
    return K.solid(("oni_leader_horn", near), lambda d: _horn_shape(d, (0.0, 0.0), out, s), HORN, lambda d: _horn_detail(d, (0.0, 0.0), out, s), outline=1.2,
                   rim=0.3, shade=0.3, shade_colour=HORN_DARK)


def _horn_at(ctx, x: float, y: float):
    a = math.radians(ctx.turn)
    return (ctx.head[0] + x * math.cos(a) - y * math.sin(a), ctx.head[1] + x * math.sin(a) + y * math.cos(a))


def _horns_back(ctx) -> List[Stamp]:
    """The far horn is behind his helmet."""
    return [(_horn(False), _horn_at(ctx, 7.6, -8.6), "far_horn", ctx.turn)]


X.layers["back"].append(_horns_back)
X.head_layers = lambda pose: [(_head(), "head"), (_eyes(str(pose["eyes"])), "eyes")]


def _horn_front(ctx) -> List[Stamp]:
    """The near horn, on the near side of his helmet, over all of his head."""
    return [(_horn(True), _horn_at(ctx, -6.6, -8.0), "near_horn", ctx.turn)]


X.neck = R.make_neck(K, HELM_DARK, 8.0)
# Sleeves of dark teal, plates on his forearms, dark gloves.
X.upper_arm = lambda near: [(0.0, 1.0, 12.0, 9.8, TEAL if near else TEAL_DARK)]
X.forearm = lambda near: [(0.0, 1.0, 9.6, 7.2, TEAL if near else TEAL_DARK), (0.22, 0.94, 10.8, 8.4, IRON if near else IRON_DARK)]
# Dark trousers under the skirt; plates on his shins.
X.thigh = lambda near: [(0.0, 1.0, 13.6, 11.4, PLATE if near else PLATE_DARK)]
X.shin = lambda near: [(0.0, 0.3, 11.4, 10.6, PLATE if near else PLATE_DARK), (0.2, 1.0, 11.4, 8.0, IRON if near else IRON_DARK)]
X.hand = R.make_hand(K, GLOVE, GLOVE_DARK, GLOVE_DARK, size=1.15)
X.shoe = R.make_shoe(K, HELM, HELM_DARK, BUILD.ankle_up, long=1.1, sole=RED_DARK)


def _sode_part(near: bool):
    """The guard of a shoulder: four rows of plates, wider at the bottom, a
    brass edge at the top."""

    def shape(d) -> None:
        K.poly(d, [K.at(-8.4, -5.6), K.at(8.4, -6.2), K.at(10.8, 13.0), K.at(-10.8, 13.6)], WHITE)

    def detail(d) -> None:
        K.poly(d, [K.at(-8.4, -5.6), K.at(8.4, -6.2), K.at(8.6, -3.6), K.at(-8.6, -3.0)], BRASS if near else BRASS_DARK)
        for k in range(4):
            y = 0.0 + k * 3.6
            K.line(d, [K.at(-9.4 - k * 0.3, y), K.at(9.4 + k * 0.3, y - 0.6)], LACE, 0.8)
        K.poly(d, [K.at(-10.8, 11.2), K.at(10.8, 10.6), K.at(10.8, 13.0), K.at(-10.8, 13.6)], RED_DARK)

    return K.solid(("oni_leader_sode", near), shape, PLATE if near else PLATE_DARK, detail, outline=1.2, rim=0.3, shade=0.3, shade_colour=PLATE_DARK)


def _sode(near: bool):
    def stamps(ctx) -> List[Stamp]:
        sh, el = (ctx.shoulder, ctx.elbow) if near else (ctx.far_shoulder, ctx.far_elbow)
        # It hangs from the shoulder and it goes half of the way with the arm.
        turn = (math.degrees(math.atan2(el[1] - sh[1], el[0] - sh[0])) - 90.0) * 0.5
        return [(_sode_part(near), (sh[0], sh[1] - 1.0), "near_sode" if near else "far_sode", turn)]

    return stamps


X.layers["under_torso"].append(_sode(False))
X.layers["front"].append(_sode(True))
X.layers["front"].append(_horn_front)

# ---- The great sword -------------------------------------------------------------


def _sword(long: float = BLADE):
    """The sword along +x from his near hand: a long grip in red cord with a
    brass end, a square guard of brass, and a long blade with a little curve,
    its back up. ``long``: the blade as long as a view of the round makes it."""
    g = GUARD_AT
    BLADE = long

    def blade(up: float, down: float):
        top = [(g + t * BLADE, -up - 3.0 * t * t) for t in (0.0, 0.25, 0.5, 0.75, 0.94)]
        bottom = [(g + t * BLADE, down - 3.0 * t * t) for t in (0.88, 0.7, 0.5, 0.25, 0.0)]
        return [K.at(x, y) for x, y in top] + [K.at(g + BLADE, -3.2)] + [K.at(x, y) for x, y in bottom]

    def shape(d) -> None:
        K.rrect(d, K.home[0] - BUTT, K.home[1] - 1.8, K.home[0] + g, K.home[1] + 1.8, 1.0, WHITE)
        K.rrect(d, K.home[0] + g - 1.4, K.home[1] - 4.2, K.home[0] + g + 1.4, K.home[1] + 4.2, 0.8, WHITE)
        K.poly(d, blade(1.9, 2.1), WHITE)

    def detail(d) -> None:
        K.rrect(d, K.home[0] - BUTT, K.home[1] - 2.8, K.home[0] + g, K.home[1] + 2.8, 0.0, RED_DARK)
        for k in range(6):
            x = -BUTT + 1.2 + k * 2.3
            K.line(d, [K.at(x, -2.2), K.at(x + 1.7, 2.2)], RED, 0.6)
        K.rrect(d, K.home[0] - BUTT - 0.8, K.home[1] - 2.8, K.home[0] - BUTT + 1.6, K.home[1] + 2.8, 0.0, BRASS_DARK)
        K.rrect(d, K.home[0] + g - 1.4, K.home[1] - 4.2, K.home[0] + g + 1.4, K.home[1] + 4.2, 0.0, BRASS)
        K.poly(d, blade(1.9, 2.1), STEEL)
        K.line(d, [K.at(g + t * BLADE, 1.2 - 3.0 * t * t) for t in (0.04, 0.3, 0.55, 0.82)], STEEL_LIGHT, 0.7)
        K.line(d, [K.at(g + t * BLADE, -1.2 - 3.0 * t * t) for t in (0.04, 0.3, 0.55, 0.88)], STEEL_DARK, 0.7)

    return K.solid(("oni_leader_sword",) + (() if long == globals()["BLADE"] else (round(long, 1),)), shape, STEEL, detail, outline=1.1, rim=0.0, shade=0.0,
                   shade_colour=STEEL_DARK)


def lerp_(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _held(ctx) -> List[Stamp]:
    """The sword in his near hand, at the turn the pose says (``blade``: 0 is
    forward, -90 is up, 90 is down). When he is down it lies by him.

    It is in front of his arm, and his hand is round it: the sword is painted
    over all of him, and then his near hand again, over the sword."""
    hand, elbow = ctx.hand, ctx.elbow
    if float(ctx.pose["held"]) < 0.5:
        lie = (X.cx + 62.0, ctx.ground - 3.2)
        t = min(1.0, max(0.0, (ctx.u - 0.12) / 0.3)) if ctx.anim == "death" else 1.0
        up = 20.0 * math.sin(math.pi * t)
        at = (lerp_(hand[0], lie[0], t), lerp_(hand[1], lie[1], t) - up)
        return [(_sword(), at, "sword", lerp_(float(ctx.pose["blade"]) - 360.0, 5.0, t) if t < 1.0 else 5.0)]
    return [(_sword(), hand, "sword", float(ctx.pose["blade"])),
            (X.hand(str(ctx.pose["nh"]), True), hand, "near_hand_on_sword", math.degrees(math.atan2(hand[1] - elbow[1], hand[0] - elbow[0])))]


X.layers["front"].append(_held)


def two(na, blade: float):
    """Where his far hand is (``fa``) when it is on the end of the grip: the
    near hand is at ``na`` and the sword is at the turn ``blade``."""
    a = math.radians(blade)
    dx = (BUILD.far_shoulder[0] - BUILD.near_shoulder[0]) / U
    dy = (BUILD.far_shoulder[1] - BUILD.near_shoulder[1]) / U
    back = (BUTT - 3.0) / U
    return (na[0] - dx - back * math.cos(a), na[1] - dy - back * math.sin(a))


# ---- How he holds himself ----------------------------------------------------

#: He waits: the point of the sword on the ground in front of him, his two
#: hands on the end of its grip, in front of his belly.
HANDS = (15.0, 11.4)
PLANTED = 86.0
X.set_rest(lean=0.0, hip=(0.0, 0.0), na=HANDS, nh="fist", fa=two(HANDS, PLANTED), fh="fist", nf=(-8.0, 0.0, 0.0), ff=(8.0, 0.0, 0.0), brows=-1.0,
           blade=PLANTED, held=1.0)


def hold(na, blade: float, **kw):
    """A pose with two hands on the sword."""
    return P(na=na, fa=two(na, blade), blade=blade, **kw)


@X.row
def idle(i: int, n: int):
    # He does not move. His chest does.
    _, s, c = loop(i, n)
    return hold(HANDS, PLANTED, hip=(0.0, 0.3 + 0.3 * s), head=(0.0, 0.2 * s, 0.8 * c), eyes="closed" if i == n - 2 else "open")


#: The sword low at his near side, its point behind him.
AT_SIDE = 156.0


@X.row
def walk(i: int, n: int):
    # He does not hurry: long slow steps, the sword low at his side.
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 8.0, 3.6)
    return P(hip=(0.5, 1.0 * abs(math.cos(ph))), lean=2.0, head=(0.0, 0.0, 0.8 * s), na=(-1.0 - 1.5 * c, 24.0), nh="fist", fa=(3.0 + 5.0 * c, 24.0), fh="fist",
             nf=nf, ff=ff, blade=AT_SIDE + 2.0 * c, hem=(1.0 + 1.5 * abs(c), 0.5 + 1.5 * abs(c)))


#: He runs with the sword out behind him.
BEHIND = 170.0


@X.row
def run(i: int, n: int):
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 12.0, 8.0, 0.0)
    return P(hip=(2.0, 2.6 + 1.6 * math.cos(2.0 * ph)), lean=15.0, head=(0.6, 0.0, -9.0), na=(-13.0 - 1.5 * c, 13.0 + 1.0 * s), fa=(-8.0 + 3.0 * c, 14.0),
             nh="fist", fh="fist", nf=nf, ff=ff, blade=BEHIND + 3.0 * s, hem=(6.0, 1.0))


@X.row
def dash(i: int, n: int):
    _, s, _c = loop(i, n)
    return P(hip=(4.0, 5.0 + 0.6 * s), lean=24.0, head=(1.0, 0.0, -16.0), na=(-15.0, 10.0), fa=(-10.0, 12.0), nh="fist", fh="fist",
             nf=(-20.0 - s, -2.0 - s, 30.0), ff=(15.0, 0.0, 0.0), blade=BEHIND + 6.0, hem=(8.0, 0.0))


@X.row
def jump(i: int, n: int):
    wind = P(hip=(-1.0, 10.0), lean=12.0, na=(-10.0, 15.0), fa=(-6.0, 16.0), nf=(-7.0, 0.0, 0.0), ff=(8.0, 0.0, 0.0), blade=150.0)
    rise = P(hip=(0.0, -2.0), lean=5.0, head=(0.0, 0.0, -7.0), na=(-12.0, 13.0), fa=(10.0, 5.0), nf=(-6.0, -1.0, 34.0), ff=(6.0, -10.0, 12.0), blade=142.0,
             hem=(2.0, 2.0))
    apex = P(hip=(0.0, -2.0), lean=2.0, head=(0.0, 0.0, -3.0), na=(-9.0, 4.0), fa=(13.0, 3.0), nf=(-5.0, -9.0, 22.0), ff=(8.0, -13.0, 4.0), blade=212.0,
             hem=(4.0, 4.0))
    return X.keys(shot(i, n), [(0.0, wind), (0.3, rise), (0.6, rise), (1.0, apex)])


@X.row
def fall(i: int, n: int):
    # He comes down with the sword up behind him, for the cut when he lands.
    _, s, c = loop(i, n)
    return P(hip=(0.0, -3.0), lean=-4.0, head=(0.0, 0.0, 6.0), na=(-6.0 + 1.0 * s, -6.0 - 1.0 * c), fa=(14.0 - 1.5 * s, 3.0 + 1.5 * c),
             nf=(-8.0, -3.0 + 1.5 * s, 28.0), ff=(7.0, -9.0 - 1.5 * s, 8.0), blade=230.0 + 3.0 * s, hem=(6.0, 6.0))


#: The sword over his far shoulder, his hands behind the line of his face.
WOUND = hold((-2.0, -6.0), -138.0, hip=(-3.0, 3.0), lean=-8.0, head=(0.0, 0.0, -3.0), nab=-1.0, fab=-1.0, nf=(-10.0, 0.0, 0.0), ff=(8.0, 0.0, 0.0), eyes="wide")
#: The cut is done: his hands low in front of him, the point at the ground.
DONE = hold((20.0, 17.0), 30.0, hip=(6.0, 7.0), lean=20.0, head=(1.0, 0.6, -8.0), nf=(-13.0, 0.0, 12.0), ff=(14.0, 0.0, 0.0), hem=(6.0, 1.0))


@X.row
def slash(i: int, n: int):
    # He takes the sword off the ground, up over his far shoulder, and down
    # through you; and it stays there for a moment.
    ready = X.full(P())
    lift = hold((12.0, 6.0), 20.0, hip=(-1.0, 1.0), lean=-3.0)
    mid = hold((21.0, 2.0), -12.0, hip=(3.0, 5.0), lean=12.0, nf=(-12.0, 0.0, 8.0), ff=(12.0, 0.0, 0.0), eyes="wide", hem=(4.0, 1.0))
    return X.keys(shot(i, n), [(0.0, ready), (0.1, lift), (0.22, WOUND), (0.3, WOUND), (0.4, mid), (0.5, DONE), (0.8, DONE), (1.0, ready)])


@X.row
def hit(i: int, n: int):
    struck = dict(X.full(R.STRUCK), lean=-16.0, hip=(-4.0, 3.0), na=(12.0, 12.0), fa=(17.0, -2.0), nh="fist", fh="open", blade=70.0, held=1.0, eyes="wince")
    back = hold((14.0, 12.0), 80.0, hip=(-2.0, 2.0), lean=-4.0, eyes="wince")
    return X.keys(shot(i, n), [(0.0, P(lean=-3.0, eyes="wide")), (0.3, struck), (0.65, struck), (1.0, back)])


@X.row
def death(i: int, n: int):
    back = dict(X.full(R.STRUCK), lean=-18.0, na=(13.0, 8.0), nh="open", blade=60.0, held=1.0, eyes="wince")
    sat = dict(X.full(R.SAT), held=0.0, eyes="closed")
    down = dict(X.full(R.SUPINE), held=0.0, eyes="closed")
    return X.keys(shot(i, n), [(0.0, back), (0.2, dict(back, lean=-26.0, held=0.0)), (0.5, sat), (0.75, down), (1.0, down)])


#: The order: his far hand out in front of him and open; the sword stays where it is.
ORDER = P(hip=(0.0, 1.0), lean=-2.0, head=(0.0, 0.0, -3.0), na=HANDS, nh="fist", fa=(22.0, 2.0), fh="open", blade=PLANTED, eyes="wide")
#: He comes back low: a knee near the ground, the sword behind him.
LOW = P(hip=(0.0, 17.0), lean=22.0, head=(1.0, 0.6, -12.0), na=(-12.0, 14.0), nh="fist", fa=(13.0, 20.0), fh="flat", nf=(-9.0, 0.0, 14.0), ff=(10.0, 0.0, 0.0),
        blade=172.0, hem=(4.0, 3.0))


@X.row
def blink_out(i: int, n: int):
    ready = X.full(P())
    return X.keys(shot(i, n), [(0.0, ready), (0.4, ORDER), (0.8, ORDER), (1.0, dict(ORDER, fa=(20.0, 6.0), eyes="closed"))])


@X.row
def blink_in(i: int, n: int):
    ready = X.full(P())
    rise = P(hip=(0.0, 6.0), lean=8.0, na=(4.0, 18.0), fa=(8.0, 18.0), blade=120.0)
    return X.keys(shot(i, n), [(0.0, LOW), (0.35, LOW), (0.7, rise), (1.0, ready)])


# ---- How he fights (the rows of his Smash moves) ---------------------------------
#
# Each move of his table (``data/movesets/ninja_shadow_oni_leader.ron``) plays
# a row of its own, slaved to the move: frame = progress x frames. So each row
# is keyed in the SECONDS of its move, and the blade is on the line of the
# move's hit volume through its live window. Before these every move fell back
# to ``slash``, whose cut comes at the middle of the row: the sword was still
# over his shoulder while the hit was live.

#: His fighting guard: the sword in two hands at his belly, the point up and
#: to the front at the eyes of whoever is there; the feet apart.
F_GUARD = hold((14.0, 8.0), -42.0, hip=(0.0, 3.0), lean=4.0, nf=(-10.0, 0.0, 0.0), ff=(12.0, 0.0, 0.0), brows=-1.0)
#: The point straight to the front at his chest, a step in.
F_THRUST = hold((27.0, 4.0), 0.0, hip=(5.0, 5.0), lean=14.0, nf=(-15.0, 0.0, 10.0), ff=(17.0, 0.0, 0.0), eyes="wide", hem=(4.0, 1.0))
#: The cut through the front, level, and gone on and down.
F_CUT = hold((24.0, 6.0), 8.0, hip=(4.0, 5.0), lean=14.0, nf=(-14.0, 0.0, 10.0), ff=(16.0, 0.0, 0.0), eyes="wide", hem=(5.0, 1.0))
F_CUT_ON = hold((22.0, 14.0), 36.0, hip=(5.0, 6.0), lean=18.0, nf=(-14.0, 0.0, 10.0), ff=(16.0, 0.0, 0.0), hem=(5.0, 1.0))
#: The arms up, the blade straight up; and gone over to the back.
F_UP = hold((9.0, -25.0), -92.0, hip=(0.0, -1.0), lean=-4.0, head=(0.0, 0.0, -10.0), nab=-1.0, fab=-1.0, arm="under", eyes="wide")
F_UP_FRONT = hold((15.0, -20.0), -62.0, hip=(1.0, 0.0), lean=0.0, head=(0.0, 0.0, -8.0), nab=-1.0, fab=-1.0, arm="under", eyes="wide")
F_UP_OVER = hold((2.0, -26.0), -134.0, hip=(-1.0, 0.0), lean=-8.0, head=(0.0, 0.0, -10.0), nab=-1.0, fab=-1.0, arm="under")
#: Low: a knee bent near the deck, the blade along it to the front.
F_LOW = hold((22.0, 24.0), 14.0, hip=(3.0, 13.0), lean=26.0, head=(1.0, 0.6, -10.0), nf=(-16.0, 0.0, 14.0), ff=(16.0, 0.0, 0.0), hem=(5.0, 2.0),
           eyes="wide")
#: Low, and round to the back: one hand on the sword, its point behind him.
F_LOW_BEHIND = P(na=(-18.0, 22.0), nab=-1.0, blade=172.0, fa=(14.0, 18.0), fh="open", hip=(-2.0, 13.0), lean=14.0, head=(0.0, 0.6, -6.0),
               nf=(-16.0, 0.0, 14.0), ff=(16.0, 0.0, 0.0), hem=(3.0, 4.0))
#: Behind him at the chest, the point back; his head turned to it.
F_BACK = P(na=(-24.0, 4.0), nab=-1.0, blade=182.0, fa=(16.0, 10.0), fh="open", lean=-8.0, head=(0.0, 0.0, 10.0), eyes="wide")
#: The point straight down, under his feet.
F_DOWN = hold((6.0, 24.0), 90.0, lean=4.0, eyes="wide")
#: His knees drawn up, as a body in the air holds them.
F_TUCK = dict(nf=(-8.0, -16.0, 24.0), ff=(9.0, -20.0, 12.0), hem=(5.0, 6.0))


def _air(pose):
    return dict(pose, **F_TUCK)


def _timed(duration: float, keys):
    """A row keyed in the seconds of its move, each frame drawn at the middle
    of the part of the move it is shown over."""
    frames = [(t / duration,) + tuple(k[1:]) for t, *rest in keys for k in [(t, *rest)]]

    def pose(i: int, n: int):
        return X.keys((i + 0.5) / max(1, n), frames)

    return pose


def _strike(duration, live, windup, hit, follow, hit_end=None, start=None):
    """From the guard to the windup, to the hit a little before the live
    window opens (the frame that shows its start shows the hit), held through
    it, the follow-through, and back to the guard."""
    a, b = live
    lead = min(a * 0.5, 0.025)
    start = start if start is not None else F_GUARD
    keys = [(0.0, start)]
    if a - lead > 0.02:
        keys.append(((a - lead) * 0.55, windup))
    keys += [(max(0.0, a - lead), hit), (b, hit_end or hit), (b + (duration - b) * 0.4, follow), (duration, start)]
    return _timed(duration, keys)


#: (row, frames, the pose function). Frames: about one for each 50 ms of the move.
FIGHT = [
    ("jab", 6, _strike(0.27, (0.03, 0.07), hold((10.0, 10.0), -20.0), F_THRUST, dict(F_THRUST, na=(22.0, 6.0), fa=two((22.0, 6.0), 4.0)))),
    ("attack_side", 6, _strike(0.30, (0.04, 0.08), WOUND, F_CUT, F_CUT_ON, hit_end=hold((25.0, 9.0), 20.0, hip=(4.0, 5.0), lean=15.0, nf=(-14.0, 0.0, 10.0),
                                                                                      ff=(16.0, 0.0, 0.0), eyes="wide", hem=(5.0, 1.0)))),
    ("attack_up", 7, _strike(0.33, (0.05, 0.09), hold((16.0, 18.0), 30.0, hip=(0.0, 8.0), lean=10.0), F_UP_FRONT, F_UP_OVER, hit_end=F_UP)),
    ("attack_down", 6, _strike(0.31, (0.05, 0.09), hold((10.0, 14.0), 120.0, hip=(0.0, 8.0), lean=16.0), F_LOW, dict(F_LOW, blade=34.0),
                               hit_end=dict(F_LOW, blade=22.0))),
    ("smash_forward", 13, _strike(0.69, (0.20, 0.25), dict(WOUND, blade=-150.0, lean=-10.0, hip=(-4.0, 4.0)),
                                  dict(F_CUT, hip=(9.0, 7.0), lean=20.0, nf=(-20.0, 0.0, 14.0), ff=(22.0, 0.0, 0.0)), F_CUT_ON,
                                  hit_end=dict(F_CUT, blade=18.0, hip=(9.0, 7.0), lean=22.0, nf=(-20.0, 0.0, 14.0), ff=(22.0, 0.0, 0.0)))),
    ("smash_up", 12, _strike(0.65, (0.18, 0.23), dict(F_LOW_BEHIND, hip=(-2.0, 14.0)), dict(F_UP, hip=(0.0, -4.0), blade=-86.0), F_UP_OVER,
                             hit_end=dict(F_UP, hip=(0.0, -4.0), blade=-100.0))),
    ("smash_down", 12, _timed(0.68, [(0.0, F_GUARD), (0.09, F_UP_OVER), (0.135, F_LOW), (0.155, dict(F_LOW, blade=20.0)), (0.19, F_LOW_BEHIND),
                                     (0.23, F_LOW_BEHIND), (0.38, dict(F_LOW_BEHIND, blade=160.0)), (0.68, F_GUARD)])),
    ("smash_charge", 4, _timed(0.32, [(0.0, dict(WOUND, blade=-150.0, lean=-10.0)), (0.1, dict(WOUND, blade=-156.0, lean=-11.0, shrug=(0.0, -0.6))),
                                      (0.2, dict(WOUND, blade=-147.0, lean=-9.0, shrug=(0.0, 0.4))), (0.32, dict(WOUND, blade=-150.0, lean=-10.0))])),
    ("air_neutral", 7, _timed(0.32, [(0.0, _air(F_GUARD)), (0.035, _air(F_CUT)), (0.06, _air(F_UP_OVER)), (0.08, _air(F_BACK)),
                                     (0.10, _air(dict(F_DOWN, blade=110.0))), (0.16, _air(F_CUT_ON)), (0.32, _air(F_GUARD))])),
    ("air_forward", 7, _strike(0.35, (0.06, 0.11), _air(WOUND), _air(F_CUT), _air(F_CUT_ON), hit_end=_air(dict(F_CUT, blade=22.0)), start=_air(F_GUARD))),
    ("air_back", 8, _strike(0.39, (0.07, 0.11), _air(dict(F_GUARD, blade=-80.0)), _air(F_BACK), _air(F_LOW_BEHIND), hit_end=_air(dict(F_BACK, blade=196.0)),
                            start=_air(F_GUARD))),
    ("air_up", 6, _strike(0.31, (0.04, 0.09), _air(hold((18.0, 4.0), -10.0)), _air(F_UP_FRONT), _air(F_UP_OVER), hit_end=_air(F_UP), start=_air(F_GUARD))),
    ("air_down", 9, _strike(0.43, (0.08, 0.13), _air(F_UP), _air(F_DOWN), _air(dict(F_DOWN, blade=86.0)), start=_air(F_GUARD))),
    ("dash_attack", 8, _strike(0.44, (0.05, 0.14), dict(F_THRUST, lean=24.0, na=(18.0, 8.0), fa=two((18.0, 8.0), 0.0)),
                               dict(F_THRUST, hip=(8.0, 6.0), lean=26.0, nf=(-22.0, -4.0, 30.0), ff=(20.0, 0.0, 0.0)), F_CUT_ON)),
    # The neutral special: he answers a blow with one cut of his own.
    ("shadow_answer", 10, _strike(0.62, (0.06, 0.10), F_GUARD, dict(F_CUT, hip=(6.0, 5.0)), F_CUT_ON)),
    # The forward special: the draw, a cut far out to the front.
    ("iaijutsu", 9, _strike(0.58, (0.05, 0.10), dict(F_LOW_BEHIND, hip=(0.0, 8.0)),
                            dict(F_CUT, hip=(10.0, 7.0), lean=22.0, nf=(-24.0, 0.0, 16.0), ff=(22.0, 0.0, 0.0)), F_CUT_ON)),
    # The up special: up in a fold of smoke, the blade up over him.
    ("smoke_fold", 9, _strike(0.52, (0.05, 0.10), dict(F_GUARD, hip=(0.0, 8.0)), _air(F_UP), _air(F_UP_OVER), hit_end=_air(dict(F_UP, blade=-104.0)))),
    # The air down special: the point down as he drops on the seal.
    ("falling_seal", 7, _strike(0.38, (0.05, 0.10), _air(F_UP), _air(F_DOWN), _air(dict(F_DOWN, blade=86.0)), start=_air(F_GUARD))),
    # The down special: he sets a seal: the point to the deck at his feet.
    ("special_down", 12, _strike(0.70, (0.06, 0.16), F_UP, dict(hold((14.0, 26.0), 84.0), hip=(2.0, 12.0), lean=22.0, nf=(-14.0, 0.0, 12.0),
                                                                ff=(14.0, 0.0, 0.0)), dict(hold((14.0, 24.0), 86.0), hip=(2.0, 10.0), lean=18.0))),
    # The grab: his far hand out to the front, the sword back in the near.
    ("grab", 6, _strike(0.35, (0.05, 0.09), dict(F_GUARD, fa=(8.0, 6.0), fh="open"),
                        P(na=(-12.0, 18.0), blade=150.0, fa=(28.0, 4.0), fh="open", hip=(4.0, 4.0), lean=12.0, nf=(-14.0, 0.0, 10.0), ff=(16.0, 0.0, 0.0)),
                        P(na=(-10.0, 18.0), blade=150.0, fa=(22.0, 8.0), fh="fist", lean=6.0))),
    ("pummel", 3, _timed(0.15, [(0.0, P(na=(-10.0, 18.0), blade=150.0, fa=(22.0, 8.0), fh="fist")),
                                (0.07, P(na=(16.0, 0.0), nab=-1.0, blade=200.0, fa=(22.0, 8.0), fh="fist", lean=8.0)),
                                (0.15, P(na=(-10.0, 18.0), blade=150.0, fa=(22.0, 8.0), fh="fist"))])),
]
_HOLDING = P(na=(-10.0, 18.0), blade=150.0, fa=(22.0, 8.0), fh="fist", lean=4.0)
FIGHT += [
    ("throw_forward", 5, _timed(0.25, [(0.0, _HOLDING), (0.06, dict(_HOLDING, fa=(6.0, 10.0), lean=-4.0)),
                                       (0.12, dict(F_CUT, hip=(5.0, 5.0))), (0.25, F_GUARD)])),
    ("throw_back", 5, _timed(0.27, [(0.0, _HOLDING), (0.07, dict(_HOLDING, lean=10.0)), (0.14, dict(F_BACK, fa=(-20.0, 0.0), fh="open")), (0.27, F_GUARD)])),
    ("throw_up", 5, _timed(0.26, [(0.0, _HOLDING), (0.06, dict(_HOLDING, hip=(0.0, 10.0), lean=12.0)),
                                  (0.13, dict(F_UP, fa=two((9.0, -25.0), -92.0))), (0.26, F_GUARD)])),
    ("throw_down", 5, _timed(0.28, [(0.0, _HOLDING), (0.07, dict(_HOLDING, fa=(16.0, -16.0), fh="open")),
                                    (0.14, dict(F_DOWN, hip=(2.0, 10.0), lean=20.0)), (0.28, F_GUARD)])),
]
for _name, _frames, _fn in FIGHT:
    X.poses[_name] = _fn


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
    if a1 - a0 < 20.0 or not 0.35 <= ctx.u <= 0.62:
        return None
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

    return K.aligned(("oni_leader_cut", pts), paint)


def _effects(ctx) -> List[Stamp]:
    out: List[Stamp] = []
    if ctx.anim == "slash" and ctx.i > 0:
        trail = _trail(ctx)
        if trail is not None:
            out.append((trail, pin(ctx.hand), "cut", 0.0))
    if ctx.anim == "dash" and ctx.i % 2 == 0:
        out.append((R.dust(K, 3.0, DUST, DUST_DARK), (ctx.foot[0] - 10.0, ctx.ground - 3.0), "dust", 0.0))
    return out


X.effects = _effects

# ---- From the front ------------------------------------------------------------
#
# The row he turns through (Jon, 2026-10-13: "We need front facing views for
# the ninjas too"). He faces you as he waits: the sword planted in front of
# him, his two hands on the end of its grip, a horn at each side of his helmet.

X.front_span = (11.0, 5.4)


def _front_armour(d) -> None:
    _rows(d, -30.0, 30.0, -31.0, -13.0, 3.6)
    K.poly(d, [K.at(-10.6, TOP + 2.6), K.at(10.6, TOP + 2.6), K.at(11.0, TOP + 4.8), K.at(-11.0, TOP + 4.8)], PLATE_LIGHT)
    K.line(d, [K.at(-3.0, -30.0), K.at(0.0, -25.0), K.at(3.0, -30.0)], RED, 0.9)
    K.oval(d, K.at(0.0, -25.0), 1.4, 1.4, RED, OUTLINE, 0.4)
    K.line(d, [K.at(-0.8, -24.0), K.at(-1.6, -19.6)], RED, 0.7)
    K.line(d, [K.at(0.8, -24.0), K.at(1.6, -19.6)], RED, 0.7)
    K.poly(d, [K.at(-40.0, -12.6), K.at(40.0, -12.6), K.at(40.0, -7.2), K.at(-40.0, -7.2)], RED_DARK)
    K.line(d, [K.at(-40.0, -10.4), K.at(40.0, -10.4)], RED, 0.6)
    K.rrect(d, K.home[0] - 2.6, K.home[1] - 13.0, K.home[0] + 2.6, K.home[1] - 6.8, 0.6, BRASS, OUTLINE, 0.5)
    # The skirt: three hanging plates and the gaps between them.
    _rows(d, -40.0, 40.0, -3.0, SKIRT - 1.0, 3.8)
    for x in (-4.8, 4.8):
        K.line(d, [K.at(x, -6.0), K.at(x * 1.3, SKIRT)], PLATE_DARK, 1.1)
    K.poly(d, [K.at(-40.0, SKIRT - 2.4), K.at(40.0, SKIRT - 2.4), K.at(40.0, SKIRT + 2.0), K.at(-40.0, SKIRT + 2.0)], PLATE_LIGHT)


X.front_torso = R.make_front_torso(K, ("oni_leader",), PLATE, PLATE_DARK, [(TOP - 0.4, 4.6), (TOP + 4.0, 11.6), (-30.0, 12.8), (-16.0, 10.8), (-9.0, 11.0),
                                                                           (0.0, 12.6), (SKIRT, 15.6)], shoulder=(10.4, -35.0, 5.6, 5.4), detail=_front_armour)

#: Where each horn is on the helmet, from the middle of his head.
FRONT_HORN = (7.6, -8.4)


def _front_helmet_shape(d) -> None:
    K.oval(d, K.at(0.0, -4.6), 10.4, 9.6, WHITE)
    K.poly(d, [K.at(-11.0, -6.6), K.at(11.0, -6.6), K.at(12.6, -3.0), K.at(-12.6, -3.0)], WHITE)
    for sx in (-1.0, 1.0):
        # The guard of his neck, out at each side; and the horn of that side.
        K.poly(d, [K.at(7.0 * sx, -4.0), K.at(14.6 * sx, 0.0), K.at(16.0 * sx, 7.0), K.at(11.0 * sx, 10.0), K.at(6.4 * sx, 6.0)], WHITE)
        _horn_shape(d, (FRONT_HORN[0] * sx, FRONT_HORN[1]), sx, 1.0)
    K.poly(d, [K.at(-6.6, 3.0), K.at(6.6, 3.0), K.at(6.8, 9.6), K.at(4.0, 12.8), K.at(-4.0, 12.8), K.at(-6.8, 9.6)], WHITE)


def _front_helmet(d) -> None:
    # The horns first: the bowl of the helmet is over their roots.
    for sx in (-1.0, 1.0):
        root = (FRONT_HORN[0] * sx, FRONT_HORN[1])
        K.poly(d, [K.at(root[0] - sx * x, root[1] + y) for x, y in HORN_OUTSIDE + HORN_INSIDE], HORN)
        _horn_detail(d, root, sx, 1.0)
    # The bowl and its peak: over all of the head down to the brow of the mask.
    K.poly(d, [K.at(-11.4, -30.0), K.at(11.4, -30.0), K.at(12.6, -3.4), K.at(-12.6, -3.4)], HELM)
    for x, bend in ((-5.4, -2.0), (0.0, 0.0), (5.4, 2.0)):
        K.line(d, [K.at(x, -6.6), K.at(x + bend * 0.5, -10.6), K.at(x + bend, -13.8)], HELM_LIGHT, 0.5)
    K.poly(d, [K.at(-11.6, -6.4), K.at(11.6, -6.4), K.at(12.4, -3.8), K.at(-12.4, -3.8)], HELM_LIGHT)
    K.oval(d, K.at(0.0, -8.4), 1.3, 1.3, BRASS, OUTLINE, 0.4)
    for sx in (-1.0, 1.0):
        K.poly(d, [K.at(7.2 * sx, -3.6), K.at(30.0 * sx, -3.6), K.at(30.0 * sx, 14.0), K.at(7.2 * sx, 9.0)], HELM)
        for k in range(3):
            y = 0.6 + k * 3.0
            K.line(d, [K.at(7.6 * sx, y), K.at((14.6 + k * 0.5) * sx, y + 0.6)], LACE, 0.8)


def _front_mask(d) -> None:
    for sx in (-1.0, 1.0):
        K.poly(d, [K.at(1.0 * sx, -2.8), K.at(6.0 * sx, -3.2), K.at(6.2 * sx, 0.8), K.at(3.6 * sx, 2.0), K.at(0.9 * sx, 0.8)], SOCKET)
        K.line(d, [K.at(6.4 * sx, 3.0), K.at(5.0 * sx, 5.4), K.at(5.6 * sx, 8.0)], BONE_SHADE, 0.6)
    K.poly(d, [K.at(-1.2, 2.4), K.at(0.0, 1.6), K.at(1.2, 2.4), K.at(1.5, 4.8), K.at(0.0, 4.0), K.at(-1.5, 4.8)], BONE_DEEP)
    K.line(d, [K.at(-4.8, 7.0), K.at(0.0, 7.6), K.at(4.8, 7.0)], BONE_DEEP, 0.8)
    for x in (-3.4, -1.1, 1.1, 3.4):
        K.line(d, [K.at(x, 5.8), K.at(x, 9.0)], BONE_DEEP, 0.5)
    K.line(d, [K.at(-4.2, 10.0), K.at(0.0, 10.8), K.at(4.2, 10.0)], BONE_SHADE, 0.6)


_front_head = R.make_front_head(K, ("oni_leader",), BONE, BONE_DEEP, wide=8.6, jaw=7.2, chin=4.6, shape=_front_helmet_shape, hair=_front_helmet, face=_front_mask)


def _front_eyes(mode: str):
    def paint(d) -> None:
        for sx in (-1.0, 1.0):
            ex, ey = 3.5 * sx, -0.4
            if mode in ("closed", "wince", "happy"):
                K.line(d, [K.at(ex + 2.0 * sx, ey - 0.5), K.at(ex - 1.9 * sx, ey + 0.5)], EYE, 0.7)
                continue
            tall = 2.0 if mode == "wide" else 1.4
            K.poly(d, [K.at(ex + 2.3 * sx, ey - tall), K.at(ex - 2.1 * sx, ey - 0.1), K.at(ex - 1.5 * sx, ey + tall * 0.9), K.at(ex + 1.8 * sx, ey + tall * 0.5)], EYE)
            K.oval(d, K.at(ex - 0.2 * sx, ey + 0.1), 0.9, 0.7, EYE_HOT)

    return K.piece(("oni_leader_front_eyes", mode), paint)


X.front_head_layers = lambda pose: [(_front_head(), "head"), (_front_eyes(str(pose["eyes"])), "eyes")]
X.front_shoe = R.make_front_shoe(K, HELM, HELM_DARK, BUILD.ankle_up, wide=1.1)


def _front_effects(ctx) -> List[Stamp]:
    out: List[Stamp] = []
    # The guard of each shoulder, over the top of the arm.
    for sx in (-1.0, 1.0):
        out.append((_sode_part(True), (ctx.hip[0] + sx * (X.front_span[0] + 6.0), ctx.hip[1] + BUILD.neck[1] + 3.6), f"front_sode_{'l' if sx < 0 else 'r'}", -7.0 * sx))
    # The sword, its point on the ground; and his two hands on its grip.
    lh, rh = ctx.left_hand, ctx.right_hand
    grip = ((lh[0] + rh[0]) / 2.0, (lh[1] + rh[1]) / 2.0)
    out.append((_sword(), grip, "front_sword", 90.0))
    out.append((X.hand("fist", True), (lh[0] - 1.0, lh[1]), "front_left_hand_on_sword", 24.0))
    out.append((X.hand("fist", True), (rh[0] + 1.0, rh[1] - 3.0), "front_right_hand_on_sword", 156.0))
    return out


X.front_effects = _front_effects


@X.front_row
def front(i: int, n: int):
    _, s, _c = loop(i, n)
    reach = -(X.front_span[0] - 5.4)
    return R.FP(hip=(0.0, 0.3 + 0.3 * s), head=(0.0, 0.2 * s, 0.0), la=(reach, 16.0), ra=(reach, 16.0), lz=0.35, rz=0.35, lh="fist", rh="fist",
                eyes="closed" if i == n - 2 else "open")


X.rows = list(X.rows) + [("front", 8, 145)] + [(name, frames, 50) for name, frames, _fn in FIGHT]


# ---- The telegraph ----------------------------------------------------------------
#
# The game holds ``notice`` while he first looks at his foe and ``windup`` over
# his cut's startup. Both loop on its clock, so every frame is the whole pose
# with a shiver.


@X.row
def notice(i: int, n: int):
    # He has seen you: the sword comes up off the ground in his near hand, its
    # point on you, and his far hand points you out; his head is up, his eyes
    # flare.
    s = (0.0, 1.0, -1.0)[i % 3]
    return P(hip=(-1.0, 0.0), lean=-3.0, head=(0.0, -0.3, -7.0 + s), na=(14.0, 10.0), nh="fist", fa=(22.0, -6.0 + 0.5 * s), fh="point", fht=40.0,
             nf=(-9.0, 0.0, 0.0), ff=(9.0, 0.0, 0.0), blade=-14.0 + 2.0 * s, eyes="wide", brows=-1.0, hem=(1.0, 1.0))


@X.row
def windup(i: int, n: int):
    # The great cut held back: down on bent knees, the sword high over his far
    # shoulder in both hands, its point behind him, his mask on you.
    s = (0.0, 1.0, -1.0)[i % 3]
    return hold((-4.0, -9.0 + 0.4 * s), -152.0 + 2.0 * s, hip=(-5.0, 7.0), lean=-12.0, head=(0.0, 0.0, -4.0 + s), nab=-1.0, fab=-1.0,
                nf=(-13.0, 0.0, 0.0), ff=(11.0, 0.0, 0.0), eyes="wide", hem=(5.0, 2.0))


X.rows = list(X.rows) + [("notice", 3, 110), ("windup", 3, 90)]

ROWS = X.rows
_render_frame = X.render_frame
render, main, render_canonical = R.entry_points(X, ACTOR_METADATA, DISPLAY_NAME)


def render_portraits(out_dir, **opts):
    """His portraits are frames of this sheet."""
    del opts
    return X.portraits(out_dir, {"default": ("idle", (1,), 0, False), "talking": ("idle", (0, 1, 2, 3, 4, 5, 6, 7), 120, True)}, view_width=36.0)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}

# ---- In the round (``_round_cast``) --------------------------------------------
#
# His own idle frame is his three-quarter view and his own front frame is his
# front, all of each (the sword planted in front of him, his shoulder guards,
# his horns). The other views are 3D: his head from the side drawn as the
# cast draws a head (the helmet, its peak and the guard of his neck, the near
# horn, the bone mask with its socket, teeth and red eye), his cuirass and
# skirt of plates from the numbers of his makers, his horns and shoulder
# guards drawn by their own makers at their places, and the sword planted in
# front of him, his two hands on the end of its grip. His rows do not use
# this.

import numpy as np  # noqa: E402

from . import _person_round as O  # noqa: E402
from . import _round_cast as C  # noqa: E402
from . import _round_wear as W  # noqa: E402
from .ninja_shadow_duelist import OwnFrames, big_frame, first_frame  # noqa: E402


def _side_helmet_shape(d) -> None:
    K.oval(d, K.at(-1.2, -4.6), 10.8, 9.4, WHITE)
    K.poly(d, [K.at(7.0, -8.0), K.at(14.4, -5.0), K.at(13.6, -2.6), K.at(7.0, -3.6)], WHITE)
    K.poly(d, [K.at(-8.0, -6.0), K.at(-15.6, -1.0), K.at(-17.0, 6.4), K.at(-12.0, 9.6), K.at(-6.0, 6.0), K.at(-6.6, -2.0)], WHITE)
    K.poly(d, [K.at(-1.0, 3.0), K.at(10.4, 3.0), K.at(10.6, 9.6), K.at(7.4, 12.6), K.at(1.6, 12.2), K.at(-1.4, 8.6)], WHITE)


def _side_helmet(d) -> None:
    K.poly(d, [K.at(-30.0, -30.0), K.at(30.0, -30.0), K.at(30.0, -3.8), K.at(12.0, -3.4), K.at(5.0, -4.6), K.at(0.6, -3.4), K.at(-0.4, 2.0), K.at(0.0, 10.0),
               K.at(-30.0, 12.0)], HELM)
    K.line(d, [K.at(12.0, -3.4), K.at(5.0, -4.6), K.at(0.6, -3.4), K.at(-0.4, 2.0), K.at(0.0, 9.0)], HELM_DARK, 0.8)
    for x, bend in ((-5.6, -2.0), (-0.4, 0.0), (5.0, 1.6)):
        K.line(d, [K.at(x, -5.6), K.at(x + bend * 0.5, -10.0), K.at(x + bend, -13.6)], HELM_LIGHT, 0.5)
    K.poly(d, [K.at(-11.6, -6.4), K.at(13.6, -5.6), K.at(13.4, -3.8), K.at(-11.4, -4.4)], HELM_LIGHT)
    K.oval(d, K.at(6.6, -7.4), 1.3, 1.3, BRASS, OUTLINE, 0.4)
    for k in range(3):
        y = 0.0 + k * 3.0
        K.line(d, [K.at(-15.6 - k * 0.4, y), K.at(-6.4, y + 2.6)], LACE, 0.8)
    K.poly(d, [K.at(0.6, -3.4), K.at(3.0, -3.8), K.at(2.4, 4.0), K.at(0.0, 8.0), K.at(-0.4, 2.0)], BONE_SHADE)


def _side_mask(d) -> None:
    # The socket of his near eye, the hole of the nose, the teeth.
    K.poly(d, [K.at(6.4, -3.2), K.at(10.6, -3.0), K.at(10.6, 1.0), K.at(8.4, 1.8), K.at(6.4, 0.8)], SOCKET)
    K.poly(d, [K.at(9.6, 2.4), K.at(11.0, 2.2), K.at(11.0, 4.8), K.at(9.4, 4.6)], BONE_DEEP)
    K.line(d, [K.at(4.0, 7.0), K.at(7.6, 7.6), K.at(10.6, 6.8)], BONE_DEEP, 0.8)
    for x in (5.4, 7.2, 9.0):
        K.line(d, [K.at(x, 5.6), K.at(x + 0.1, 8.8)], BONE_DEEP, 0.5)
    K.line(d, [K.at(3.6, 9.6), K.at(7.4, 10.6), K.at(10.4, 9.4)], BONE_SHADE, 0.6)
    K.line(d, [K.at(2.6, 2.6), K.at(4.6, 4.6), K.at(4.2, 7.0)], BONE_SHADE, 0.6)


_side_head = R.make_head(K, ("oni_leader_side",), BONE, BONE_SHADE, BONE_DEEP, skull=(0.2, -2.4, 9.4, 9.0), jaw=(3.8, 4.6, 6.6, 7.4), nose=None, ear=None,
                         shape=_side_helmet_shape, under=_side_helmet, over=_side_mask, far_shade=False)


def _side_eyes(mode: str):
    """The red light in the near socket of his mask."""

    def paint(d) -> None:
        ex, ey = 8.6, -0.8
        if mode in ("closed", "wince", "happy"):
            K.line(d, [K.at(ex - 1.6, ey - 0.4), K.at(ex + 1.6, ey + 0.5)], EYE, 0.7)
            return
        tall = 2.0 if mode == "wide" else 1.4
        K.poly(d, [K.at(ex - 1.7, ey - tall), K.at(ex + 1.8, ey - 0.2), K.at(ex + 1.2, ey + tall * 0.9), K.at(ex - 1.3, ey + tall * 0.5)], EYE)
        K.oval(d, K.at(ex + 0.3, ey + 0.1), 0.8, 0.7, EYE_HOT)

    return K.piece(("oni_leader_side_eyes", mode), paint)


def _side_horn():
    """The near horn from the side: it goes up from the helmet, and out
    toward whoever looks is not seen, so it is narrow."""
    return K.solid(("oni_leader_side_horn",), lambda d: _horn_shape(d, (-0.6, -8.6), -0.4, 1.0), HORN, lambda d: _horn_detail(d, (-0.6, -8.6), -0.4, 1.0),
                   outline=1.2, rim=0.3, shade=0.3, shade_colour=HORN_DARK)


#: Where each horn has its root (from the middle of his head) and each
#: shoulder guard its top (body space), for the views that are 3D.
HORN_ROOTS = {"r": (-7.6, -8.4, 0.6), "l": (7.6, -8.4, 0.6)}


def _outward(view: O.View, at, centre) -> float:
    """-1 when ``at`` is to the left of ``centre`` in ``view``, else 1."""
    ex = view.basis()[0]
    return -1.0 if float((np.asarray(at) - np.asarray(centre)) @ ex) < 0.0 else 1.0


class _Horns:
    """His horns in the views his own frames do not draw, but for the side
    views (his head from the side has its horn): each drawn by his own horn
    maker at its root, going out to the side it is on in that view. His
    three-quarter head from the left is the mirror of his own, which has no
    horns, so they are drawn there too."""

    def piece(self, K_, J, head):
        sprites = []
        for side, root in HORN_ROOTS.items():
            at = tuple(np.asarray(head) + root)

            def draw(view, far, at=at):
                if abs(abs(O.facing(view)) - 90.0) <= 10.0:
                    return None  # his head from the side has its horn
                out = _outward(view, at, head)
                return K.solid(("oni_leader_horn_round", out), lambda d: _horn_shape(d, (0.0, 0.0), out, 0.94), HORN,
                               lambda d: _horn_detail(d, (0.0, 0.0), out, 0.94), outline=1.2, rim=0.3, shade=0.3, shade_colour=HORN_DARK), 0.0, False

            sprites.append(O.Sprite(f"horn_{side}", at, draw, lead=2.0))
        return _Group(sprites)


class _Sodes:
    """His shoulder guards in the views that are 3D: drawn by their own maker,
    hanging from each shoulder over the top of the arm."""

    def piece(self, K_, J, head):
        sprites = []
        for side in ("r", "l"):
            sh = np.asarray(J.shoulders[side]) + np.array([0.0, -1.0, 0.0])
            sprites.append(O.Sprite(f"sode_{side}", tuple(sh), lambda view, far, near=(side == "r"): (_sode_part(near), 0.0, O.facing(view) < 0.0), lead=6.0))
        return _Group(sprites)


class _Group:
    """Pieces that go together (both horns, both shoulder guards): what a
    look gives as one piece. ``when`` is given to each of them."""

    def __init__(self, parts):
        self.parts = parts

    @property
    def when(self):
        return self.parts[0].when

    @when.setter
    def when(self, value):
        for part in self.parts:
            part.when = value


_BODY = C.PersonBody(X, mirror=("head",), heads={"side": lambda pose: [(_side_head(), "head"), (_side_eyes(str(pose["eyes"])), "eyes"), (_side_horn(), "horn")]})
_J = _BODY.joints(2.0)
#: He waits: the sword planted in front of him, its point on the ground, his
#: two hands on the end of its grip.
_WAY = np.array([0.0, math.sin(math.radians(PLANTED)), math.cos(math.radians(PLANTED))])
_NEAR = np.asarray(_J.wrist(True, -1.0))
_FAR = _NEAR - _WAY * (BUTT - 3.0) + np.array([2.4, 0.0, 0.0])


def _held_round(n: int):
    # The sword as long as the view makes it, and his near hand round it.
    return O.composed(K, [(_sword(max(8.0, n - GUARD_AT)), "sword"), (X.hand("fist", True), "near_hand")])


_ROWS_OF_PLATES = [W.Across(-180.0, 180.0, v, LACE, width=0.4) for v in np.arange(-31.0, -13.0, 3.6)] + \
    [W.Across(-180.0, 180.0, v, LACE, width=0.4) for v in np.arange(-3.0, SKIRT - 1.0, 3.8)]
ROUND = OwnFrames(
    DISPLAY_NAME, _BODY,
    C.Look(
        # The helmet over all of his head but the mask, and the guard of his
        # neck flared behind.
        C.auto_head(X, _head, hair=lambda u, v: ~((np.abs(u) < 52.0) & (v > -3.6)), hair_colour=HELM, hair_shade=HELM_DARK,
                    volumes=[((0.0, -4.6, -0.6), (10.6, 9.6, 10.2))], ink=EYE, eye_size=1.3),
        # The cuirass and the skirt: rows of plates laced in blue, the light
        # edge at the top, the red cord at the chest, the sash and its clasp,
        # the hanging plates of the skirt and their light hem, the mark of the
        # dojo.
        C.auto_trunk(X, _ROWS_OF_PLATES + [W.Band(TOP + 2.4, TOP + 5.2, PLATE_LIGHT), W.Dot(0.0, -25.0, 1.4, RED), W.Band(-12.6, -6.6, RED_DARK),
                                           W.Across(-180.0, 180.0, -9.8, RED, width=0.3), W.Dot(10.0, -9.6, 1.8, BRASS),
                                           W.Down(-30.0, -6.0, SKIRT, PLATE_DARK, width=0.55), W.Down(10.0, -6.0, SKIRT, PLATE_DARK, width=0.55),
                                           W.Down(50.0, -6.0, SKIRT, PLATE_DARK, width=0.55), W.Down(180.0, -6.0, SKIRT, PLATE_DARK, width=0.55),
                                           W.Band(SKIRT - 2.6, SKIRT + 2.0, PLATE_LIGHT), W.Glow(30.0, 8.6, 2.6, 2.8, RED)]),
        head_pieces=[W.Cloak([O.Ring(-49.0, 0.0, 1.6, 9.6, 9.0), O.Ring(-45.0, 0.0, 0.4, 13.6, 11.6), O.Ring(-41.4, 0.0, -0.6, 15.6, 13.0)],
                             W.Garment(HELM, HELM_DARK, [W.Across(-180.0, 180.0, v, LACE, width=0.4) for v in (-47.0, -44.0, -42.6)]), turns=(95.0, 265.0)),
                     ],
        pieces=[("horns", _Horns()), ("sode", _Sodes()), ("sword", W.Prop("sword", tuple(_NEAR), tuple(_NEAR + _WAY * (GUARD_AT + BLADE)), _held_round, lead=4.0))]),
    C.Stance(hands={"r": C.Hand(at=tuple(_NEAR), pole=(-0.8, 0.6, -0.2), mode="fist"), "l": C.Hand(at=tuple(_FAR), pole=(1.0, 0.6, -0.2), mode="fist")},
             stagger=2.0),
    frames={45.0: big_frame(X, "idle"), 0.0: first_frame(X, "front")}, big=(45.0,))

if __name__ == "__main__":
    raise SystemExit(main())
