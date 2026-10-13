"""Sprite generator for Galwah: twenty years old, the whole of a new algebra in
his head, and no time.

A parody of Evariste Galois (the name is how his is said).

The look (2026-10-13): a slight young man seen three quarters from the front,
facing right. Dark hair that he has had his hands in, a narrow face, dark
eyes with too little sleep under them, a mouth that is set. The dress of a
student of Paris in 1832: a dark green frock coat shut high, a black cravat,
a pale waistcoat, grey trousers. All of him leans forward: he is in a hurry.

He is drawn from the one portrait of the boy and from his last night, not
from a type (Jon, 2026-10-13, of another person of this cast: "needs to read
like paul erdos not bearnie sanders"). He is a grown man, though a young one,
and not a mascot. There is no drop shadow. At rest he holds nothing; the
watch, the pen and the pistol are drawn over his hand in the rows that are
theirs.

What he shows: the five roots of the quintic and the ways they change
places, written fast.

He is a person of ``_person_rig``: the bones, the poses and the frame are
shared; the head, the clothes, how he stands and what he writes are his.
"""

from __future__ import annotations

import math
from typing import List

from ._ai_era_kit import OUTLINE, WHITE, RGBA, mix, pin
from . import _person_rig as R
from ._person_rig import Build, Person, Stamp, loop, shot

TARGET_NAME = "galwah"
DISPLAY_NAME = "Galwah"

ACTOR_METADATA = {
    "actor": {"character_id": "npc_galwah", "display_name": "Galwah"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": ["story", "humanoid", "story", "mystic"],
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
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "peaceful"},
    "visual": {"default_pose": "idle"},
    "tags": ["story", "humanoid", "story", "mystic"],
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
    },
    "animation_bindings": {
        "default": {"animation": "turn", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
    },
}


ACTOR_METADATA.update(
    {
        "authoring_description": (
            "Galwah is a young, urgent parody of Evariste Galois, with the misspelled name echoing "
            "how 'Galois' is often pronounced. His characterization centers on group-theoretic "
            "symmetry, the impossibility of general quintic formulas, revolutionary intensity, and "
            "the final night spent writing before his fatal duel."
        ),
        "gameplay_description": (
            "Use as a brilliant but time-starved mathematician, duelist, quest giver, or fragile "
            "high-burst playable character. His abilities should reveal hidden symmetries, classify "
            "what can be solved, and trade safety for one decisive night of work."
        ),
    }
)
ACTOR_METADATA.setdefault("dialogue_hints", {}).setdefault(
    "barks",
    [
        'The structure of a problem decides what is permitted to solve it.',
        'I have no time.',
        'Speak quickly. The morning is not patient.',
    ],
)


COAT: RGBA = (46, 78, 70, 255)
COAT_DARK: RGBA = (28, 50, 50, 255)
COAT_LIGHT: RGBA = (84, 120, 104, 255)
VEST: RGBA = (226, 212, 176, 255)
SHIRT: RGBA = (248, 244, 234, 255)
CRAVAT: RGBA = (34, 30, 40, 255)
TROUSER: RGBA = (150, 150, 162, 255)
TROUSER_DARK: RGBA = (104, 104, 122, 255)
SHOE: RGBA = (46, 38, 40, 255)
SHOE_DARK: RGBA = (24, 20, 24, 255)
SKIN: RGBA = (240, 212, 190, 255)
SKIN_SHADE: RGBA = (210, 174, 154, 255)
SKIN_DEEP: RGBA = (164, 116, 106, 255)
HAIR: RGBA = (46, 36, 40, 255)
HAIR_LIGHT: RGBA = (94, 80, 88, 255)
INK: RGBA = (26, 22, 30, 255)
ALGEBRA: RGBA = (226, 208, 255, 255)
ALGEBRA_DARK: RGBA = (116, 86, 190, 255)
GOLD: RGBA = (250, 212, 110, 255)
GOLD_DARK: RGBA = (196, 132, 52, 255)
PAPER: RGBA = (250, 244, 228, 255)
PAPER_DARK: RGBA = (198, 186, 160, 255)
STEEL: RGBA = (150, 156, 172, 255)

#: Slight: 168 cm, narrow, long in the leg, his neck forward of his hips.
BUILD = Build(hip_up=49.0, thigh=23.8, shin=22.6, neck=(1.6, -35.0), upper=18.8, fore=17.8, near_shoulder=(-4.8, -31.0), far_shoulder=(7.0, -30.6),
              near_hip=(-3.2, 0.0), far_hip=(3.2, 0.0), head_up=(1.2, -12.2), height=108.0, half_width=(12.0, 14.0))

X = Person(TARGET_NAME, BUILD)
K = X.K
P = X.P
TOP = BUILD.neck[1] - 2.0


def _front(d, hb: float, hf: float) -> None:
    """Two rows of buttons, the pale waistcoat where the coat is cut away at
    his waist, and the black cravat at his throat."""
    K.poly(d, [K.at(2.6, TOP - 1.0), K.at(9.6, TOP - 1.0), K.at(8.4, TOP + 7.0), K.at(3.6, TOP + 7.0)], CRAVAT)
    K.poly(d, [K.at(4.0, TOP - 1.0), K.at(8.0, TOP - 1.0), K.at(7.4, TOP + 2.4), K.at(4.6, TOP + 2.4)], SHIRT)
    K.poly(d, [K.at(-0.6, TOP + 1.0), K.at(3.0, TOP), K.at(4.6, TOP + 12.0), K.at(0.6, TOP + 9.0)], COAT_LIGHT)
    for y in (-22.0, -16.0, -10.0):
        K.oval(d, K.at(2.4, y), 0.9, 0.9, GOLD)
        K.oval(d, K.at(7.0, y), 0.9, 0.9, GOLD)
    K.poly(d, [K.at(3.6, -6.0), K.at(10.6, -6.0), K.at(11.0, 3.0), K.at(5.0, 3.0)], VEST)
    K.line(d, [K.at(3.6, -6.0), K.at(5.0 + hf * 0.5, 16.0)], COAT_DARK, 0.7)


X.torso = R.make_torso(K, ("galwah",), COAT, COAT_DARK, back=(8.6, 9.0, 7.4, 10.6), front=(8.0, 9.4, 8.0, 9.4), hem_y=20.0, top=TOP,
                       shoulders=((-4.6, -30.4), (6.2, -30.2)), shoulder_r=(5.0, 4.6), shade_from=8.0, detail=_front)


def _hair_shape(d) -> None:
    # A great deal of it, and none of it lies down.
    K.oval(d, K.at(-1.0, -5.6), 9.8, 8.6, WHITE)
    K.poly(d, [K.at(-9.0, -8.0), K.at(-11.6, -12.6), K.at(-6.6, -12.0), K.at(-5.0, -16.0), K.at(-1.6, -13.0), K.at(2.0, -16.6), K.at(4.6, -13.0),
               K.at(8.6, -14.6), K.at(9.6, -9.0)], WHITE)
    K.poly(d, [K.at(-8.6, -2.0), K.at(-11.4, 2.0), K.at(-8.0, 3.4), K.at(-9.0, 7.0), K.at(-5.0, 6.0)], WHITE)


def _hair(d) -> None:
    K.poly(d, [K.at(20.0, -7.6), K.at(9.0, -7.6), K.at(7.0, -5.0), K.at(4.6, -8.0), K.at(2.4, -5.4), K.at(0.0, -7.0), K.at(-2.4, -3.6), K.at(-3.4, -1.0),
               K.at(-6.2, -1.2), K.at(-6.8, 3.6), K.at(-5.2, 4.8), K.at(-4.8, 6.6), K.at(-20.0, 6.6), K.at(-20.0, -26.0), K.at(20.0, -26.0)], HAIR)
    for strand in ([(6.0, -10.0), (2.0, -13.0), (-3.0, -11.0)], [(-2.0, -8.0), (-6.0, -8.6), (-9.0, -5.0)], [(-6.6, -1.0), (-9.0, 2.4)], [(4.0, -6.6), (5.0, -9.0)]):
        K.line(d, [K.at(x, y) for x, y in strand], HAIR_LIGHT, 0.6)


def _face(d) -> None:
    # He did not sleep.
    for x in (1.6, 7.0):
        K.line(d, [K.at(x - 1.4, 2.2), K.at(x + 1.6, 2.6)], mix(SKIN, ALGEBRA_DARK, 0.3), 0.6)


_head = R.make_head(K, ("galwah",), SKIN, SKIN_SHADE, SKIN_DEEP, skull=(0.0, -2.4, 7.6, 8.8), jaw=(2.4, 3.8, 5.0, 7.0),
                    nose=((7.2, -0.2), (9.4, 3.0), (8.8, 4.2), (7.2, 4.4)), ear=(-4.8, 1.0, 1.9, 2.8), shape=_hair_shape, under=_hair, over=_face)
_eyes = R.make_eyes(K, (1.6, -0.4), (7.0, -0.6), ink=INK, iris=(60, 44, 40, 255), size=1.0)
_brows = R.make_brows(K, [(-1.0, -4.0), (1.6, -4.2), (4.4, -3.2)], [(5.6, -3.4), (7.2, -4.2), (8.6, -4.0)], HAIR, 1.3)
_mouth = R.make_mouth(K, (5.4, 7.6), (118, 54, 58, 255), wide=0.8)

X.head_layers = lambda pose: [(_head(), "head"), (_eyes(str(pose["eyes"])), "eyes"), (_brows(R.brow_mood(pose)), "brows"),
                              (_mouth(str(pose["mouth"])), "mouth")]
X.neck = R.make_neck(K, SKIN_SHADE, 4.2)
X.upper_arm = lambda near: [(0.0, 1.0, 6.4, 5.4, COAT if near else COAT_DARK)]
X.forearm = lambda near: [(0.0, 1.0, 5.4, 4.6, COAT if near else COAT_DARK)]
X.thigh = lambda near: [(0.0, 1.0, 6.8, 5.6, TROUSER if near else TROUSER_DARK)]
X.shin = lambda near: [(0.0, 1.0, 5.6, 4.8, TROUSER if near else TROUSER_DARK)]
X.hand = R.make_hand(K, SKIN, SKIN_SHADE, SKIN_DEEP, SHIRT, (206, 204, 210, 255), size=0.95)
X.shoe = R.make_shoe(K, SHOE, SHOE_DARK, BUILD.ankle_up)

# ---- How he holds himself ----------------------------------------------------

#: His watch in his hand, held up where he can see it.
AT_WATCH = (11.0, 4.0)
X.set_rest(lean=4.0, na=(-2.0, 25.5), fa=(2.5, 25.0), mouth="flat", brows=-1.0, nf=(-4.0, 0.0, 0.0), ff=(5.0, 0.0, 0.0))


@X.row
def rest(i: int, n: int):
    # He looks at his watch. He puts a hand in his hair. He looks at his watch.
    _, s, c = loop(i, n)
    watch = i < n // 2
    return P(hip=(0.0, 0.3 + 0.3 * s), lean=4.0 + s, head=(0.4, 0.0, 10.0 if watch else -2.0), na=AT_WATCH if watch else (6.0, -13.0), nab=1.0 if watch else -1.0,
             arm="over" if watch else "under", nh="fist" if watch else "open", eyes="closed" if i == n - 1 else "open")


@X.row
def walk(i: int, n: int):
    # Fast, his head ahead of his feet, the tails of his coat behind him.
    ph, s, c = loop(i, n)
    nf, ff = R.stride(ph, 10.0, 5.4)
    return P(hip=(1.0, 0.9 * math.cos(2.0 * ph)), lean=10.0, head=(0.5, 0.0, -4.0), na=(-2.0 - 9.0 * c, 22.0), fa=(3.0 + 9.0 * c, 21.5), nh="fist", fh="fist",
             nf=nf, ff=ff, hem=(4.0 + 2.0 * abs(c), 0.0))


@X.row
def theorem(i: int, n: int):
    # He writes it in the air as fast as his hand goes, and it is all there.
    _, s, c = loop(i, n)
    return P(hip=(1.0, 0.5), lean=8.0, head=(0.6, 0.0, -6.0), na=(20.0 + 5.0 * c, -8.0 + 7.0 * s), nh="fist", fa=(10.0, 12.0), fh="flat", eyes="wide" if i % 4 == 0 else "open",
             mouth="open" if i % 2 else "flat", brows=-1.0 if i < n - 2 else 1.0)


@X.row
def duel(i: int, n: int):
    # Side on, his arm straight out. He did not want this.
    ready = P(lean=-2.0, head=(0.0, 0.0, 0.0), na=(-3.0, 24.0), nh="fist", fa=(2.0, 25.0))
    aim = P(hip=(-1.0, 1.0), lean=-4.0, head=(0.0, 0.0, 2.0), na=(27.0, -3.0), nh="fist", fa=(-7.0, 21.0), eyes="open")
    kick = dict(aim, lean=-9.0, na=(24.0, -9.0), eyes="wince", mouth="grit", off=(-2.0, 0.0))
    return X.keys(shot(i, n), [(0.0, ready), (0.3, aim), (0.55, aim), (0.65, kick), (1.0, dict(aim, na=(20.0, 8.0), eyes="closed"))])


@X.row
def death(i: int, n: int):
    hit = X.full(dict(R.STRUCK, na=(8.0, 6.0), nh="flat"))
    sag = P(hip=(-5.0, 13.0), lean=-16.0, head=(-2.0, 0.0, -8.0), na=(7.0, 10.0), fa=(12.0, 15.0), nh="flat", fh="open", nf=(-4.0, 0.0, 0.0), ff=(10.0, 0.0, -10.0),
            eyes="wince", mouth="o", off=(-3.0, 0.0))
    return X.keys(shot(i, n), [(0.0, hit), (0.25, sag), (0.5, R.SAT), (0.75, R.SUPINE), (1.0, R.SUPINE)])


X.rows = [("rest", 8, 130), ("walk", 8, 95), ("theorem", 8, 110), ("duel", 8, 85), ("death", 8, 115)]

# ---- From the front ------------------------------------------------------------

def _front_coat(d) -> None:
    """His coat from the front: open on the pale waistcoat, the high collar
    of his shirt and the black cravat, and two rows of buttons."""
    K.poly(d, [K.at(-4.4, TOP), K.at(4.4, TOP), K.at(5.0, 2.0), K.at(-5.0, 2.0)], VEST)
    K.poly(d, [K.at(-3.4, TOP - 2.0), K.at(3.4, TOP - 2.0), K.at(2.6, TOP + 3.0), K.at(-2.6, TOP + 3.0)], SHIRT)
    K.poly(d, [K.at(-2.4, TOP + 0.6), K.at(2.4, TOP + 0.6), K.at(1.6, TOP + 4.6), K.at(0.0, TOP + 6.0), K.at(-1.6, TOP + 4.6)], CRAVAT)
    for y in (-18.0, -12.0, -6.0):
        K.oval(d, K.at(0.0, y), 0.7, 0.7, (150, 132, 100, 255))
    for sx in (-1.0, 1.0):
        K.poly(d, [K.at(4.4 * sx, TOP), K.at(7.4 * sx, TOP + 1.0), K.at(5.0 * sx, -18.0)], COAT_LIGHT)
        K.line(d, [K.at(5.0 * sx, -18.0), K.at(5.4 * sx, 18.0)], COAT_DARK, 0.7)
        for y in (-14.0, -8.0):
            K.oval(d, K.at(7.4 * sx, y), 0.8, 0.8, GOLD, GOLD_DARK, 0.3)


def _front_hair_shape(d) -> None:
    # Thick, dark, and it does not lie down.
    K.oval(d, K.at(0.0, -6.2), 10.0, 7.8, WHITE)
    for x, y in ((-6.0, -13.0), (-1.0, -14.6), (4.6, -13.4), (8.6, -9.0), (-9.0, -8.0)):
        K.oval(d, K.at(x, y), 2.4, 2.2, WHITE)


def _front_hair(d) -> None:
    K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, 0.0), K.at(7.6, 0.0), K.at(7.2, -5.0), K.at(4.0, -7.6), K.at(1.0, -6.0), K.at(-2.6, -7.8),
               K.at(-6.4, -6.0), K.at(-7.6, 0.0), K.at(-20.0, 0.0)], HAIR)
    for strand in ([(-5.0, -12.0), (-1.0, -13.6), (3.6, -12.4)], [(-3.0, -9.6), (1.0, -10.0), (5.6, -8.6)], [(-8.6, -5.0), (-8.2, -1.0)], [(8.6, -5.0), (8.2, -1.0)]):
        K.line(d, [K.at(x, y) for x, y in strand], HAIR_LIGHT, 0.6)


def _front_nose(d) -> None:
    K.line(d, [K.at(-0.3, 0.4), K.at(-1.2, 3.6), K.at(0.0, 4.4), K.at(1.2, 3.6)], SKIN_DEEP, 0.6)


X.front_torso = R.make_front_torso(K, ("galwah",), COAT, COAT_DARK, [(TOP, 4.0), (TOP + 3.6, 8.6), (-24.0, 9.2), (-8.0, 8.6), (20.0, 10.6)],
                                   shoulder=(7.0, -30.8, 4.2, 4.6), detail=_front_coat)
X.front_head_layers = R.front_face(R.make_front_head(K, ("galwah",), SKIN, SKIN_DEEP, wide=7.8, jaw=6.0, chin=4.0, ears=SKIN, shape=_front_hair_shape, hair=_front_hair,
                                                    face=_front_nose),
                                   R.make_front_eyes(K, ("galwah",), ink=INK, iris=(60, 44, 40, 255), spread=3.4, y=-0.6, size=0.9),
                                   R.make_front_brows(K, ("galwah",), HAIR, spread=3.4, y=-4.0, width=1.3),
                                   R.make_front_mouth(K, ("galwah",), y=8.2, colour=(118, 54, 58, 255), wide=0.6))
X.front_shoe = R.make_front_shoe(K, SHOE, SHOE_DARK, BUILD.ankle_up)
X.front_span = (7.8, 4.4)
R.add_front_rows(X, hands="sides")

# ---- What he shows -----------------------------------------------------------


def _roots(count: int, turn: int, arrows: bool):
    """The five roots on a circle, ``count`` of them there, and the arrows by
    which they change places."""

    def where(k: int):
        a = math.radians(-90.0 + 72.0 * k + turn)
        return K.at(11.0 * math.cos(a), 11.0 * math.sin(a))

    def paint(d) -> None:
        if arrows and count == 5:
            order = [0, 2, 4, 1, 3, 0]
            for edge in (True, False):
                K.line(d, [where(k) for k in order], ALGEBRA_DARK if edge else ALGEBRA, 2.4 if edge else 0.9)
        for k in range(count):
            K.oval(d, where(k), 3.0, 3.0, OUTLINE)
            K.oval(d, where(k), 2.0, 2.0, GOLD if k == 0 else ALGEBRA)

    return K.aligned(("roots", count, turn, arrows), paint)


def _watch():
    def shape(d) -> None:
        K.oval(d, K.home, 3.6, 3.6, WHITE)
        K.stroke(d, [K.at(0.0, -3.4), K.at(0.0, -5.4)], WHITE, 1.4)

    def detail(d) -> None:
        K.oval(d, K.home, 2.5, 2.5, PAPER)
        K.line(d, [K.home, K.at(0.0, -1.9)], INK, 0.5)
        K.line(d, [K.home, K.at(1.4, 0.6)], INK, 0.5)

    return K.solid(("watch",), shape, GOLD, detail, outline=1.0, rim=0.3, shade=0.4, shade_colour=GOLD_DARK)


def _quill():
    def shape(d) -> None:
        K.poly(d, [K.at(-1.0, 1.0), K.at(2.0, -4.0), K.at(8.0, -13.0), K.at(10.0, -11.0), K.at(4.0, -2.4), K.at(0.4, 2.0)], WHITE)

    return K.solid(("quill",), shape, PAPER, lambda d: K.line(d, [K.at(0.0, 1.0), K.at(8.6, -11.6)], PAPER_DARK, 0.6), outline=1.0, rim=0.2, shade=0.3,
                   shade_colour=PAPER_DARK)


def _pistol():
    """A pistol of 1832, along +x from his hand."""

    def shape(d) -> None:
        K.rrect(d, K.home[0] - 1.0, K.home[1] - 3.4, K.home[0] + 13.0, K.home[1] - 0.8, 0.8, WHITE)
        K.poly(d, [K.at(-2.0, -3.0), K.at(2.6, -3.0), K.at(1.0, 4.0), K.at(-3.0, 3.4)], WHITE)

    def detail(d) -> None:
        K.rrect(d, K.home[0] + 3.0, K.home[1] - 3.6, K.home[0] + 14.0, K.home[1] - 0.6, 0.0, STEEL)

    return K.solid(("pistol",), shape, (112, 72, 50, 255), detail, outline=1.0, rim=0.3, shade=0.4, shade_colour=(64, 40, 34, 255))


def _page(turn: int):
    def shape(d) -> None:
        K.rrect(d, K.home[0] - 4.0, K.home[1] - 5.0, K.home[0] + 4.0, K.home[1] + 5.0, 0.4, WHITE)

    def detail(d) -> None:
        for y in (-3.0, -1.0, 1.0, 3.0):
            K.line(d, [K.at(-2.6, y), K.at(2.6 - (1.4 if y == 3.0 else 0.0), y)], ALGEBRA_DARK, 0.5)

    return K.solid(("page", turn), shape, PAPER, detail, outline=1.0, rim=0.2, shade=0.3, shade_colour=PAPER_DARK)


def _effects(ctx) -> List[Stamp]:
    out: List[Stamp] = []
    if ctx.anim == "rest" and ctx.i < ctx.n // 2:
        out.append((_watch(), (ctx.hand[0] + 3.0, ctx.hand[1] - 3.0), "watch", 0.0))
    elif ctx.anim == "theorem":
        turn = math.degrees(math.atan2(ctx.hand[1] - ctx.elbow[1], ctx.hand[0] - ctx.elbow[0]))
        out.append((_quill(), ctx.hand, "quill", turn * 0.3))
        count = min(5, 1 + ctx.i)
        out.append((_roots(count, 0 if ctx.i < 6 else 36 * (ctx.i - 5), ctx.i >= 5), pin((ctx.head[0] + 34.0, ctx.head[1] - 14.0)), "roots", 0.0))
    elif ctx.anim == "duel" and ctx.u >= 0.25:
        turn = math.degrees(math.atan2(ctx.hand[1] - ctx.elbow[1], ctx.hand[0] - ctx.elbow[0]))
        out.append((_pistol(), ctx.hand, "pistol", turn))
        if 0.55 <= ctx.u <= 0.7:
            a = math.radians(turn)
            out.append((R.burst(K, 8.0, GOLD, GOLD_DARK), (ctx.hand[0] + 20.0 * math.cos(a), ctx.hand[1] + 20.0 * math.sin(a) - 2.0), "flash", 0.0))
    elif ctx.anim == "death" and 0.1 <= ctx.u <= 0.9:
        # What he wrote that night goes up, and comes down after him.
        for k in range(3):
            t = ctx.u * 1.2 + k * 0.17
            x = ctx.hip[0] + 14.0 + 12.0 * k - 30.0 * ctx.u
            y = ctx.ground - 30.0 - 50.0 * math.sin(min(1.0, t) * math.pi) * (0.6 + 0.2 * k)
            out.append((_page(k), (x, min(y, ctx.ground - 8.0)), f"page_{k}", 40.0 * k + 200.0 * ctx.u))
    return out


X.effects = _effects

ROWS = X.rows
_render_frame = X.render_frame
render, main, render_canonical = R.entry_points(X, ACTOR_METADATA, DISPLAY_NAME)
TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}


if __name__ == "__main__":
    raise SystemExit(main())
