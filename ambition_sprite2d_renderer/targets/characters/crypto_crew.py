"""Sprite generators for the cryptography crew: the roles of a protocol story,
as people.

Craig cracks, Eve listens, Judy judges, Mallory edits, Olivia answers, Peggy
proves, Sybil is many, Trent is trusted, Trudy intrudes, Victor verifies and
Walter reads every note. (Alice and Bob are their own modules.) None of them
is a real person: each is the name a paper gives a role, so each is drawn from
what the role DOES. See ``docs/concepts/cryptography-crew.md`` of the game.

Each was a jointed-puppet placeholder (three had a bespoke stiff painter).
Now (2026-10-13) each is a person of ``_person_rig``: the bones, the poses and
the frame are shared; the height, the head, the clothes, how the person stands
and what the person shows are their own. They are grown people, not mascots:
no big heads, no big eyes. There is no drop shadow, and nobody holds a thing
at rest (the runtime held-item system is authoritative); what a role is known
by is drawn over its hand in the rows that are its own.

One module, eleven sheets: ``TARGETS`` names each.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from ._ai_era_kit import OUTLINE, WHITE, RGBA, mix, pin
from . import _person_rig as R
from . import _person_round as O
from . import _round_cast as C
from . import _round_wear as W
from ._person_rig import Build, Person, Stamp, loop, shot

INK: RGBA = (26, 22, 30, 255)
PAPER: RGBA = (248, 242, 226, 255)
PAPER_DARK: RGBA = (196, 184, 160, 255)
GOLD: RGBA = (250, 210, 104, 255)
GOLD_DARK: RGBA = (196, 130, 52, 255)
SEAL: RGBA = (206, 62, 58, 255)

#: Skin: light, dark, and the line colour, for each tone the crew has.
PALE = ((238, 208, 186, 255), (208, 170, 150, 255), (164, 114, 102, 255))
TAN = ((214, 168, 130, 255), (180, 132, 102, 255), (136, 88, 72, 255))
BROWN = ((158, 106, 76, 255), (122, 78, 58, 255), (88, 52, 44, 255))
DEEP = ((112, 74, 56, 255), (86, 54, 44, 255), (58, 34, 32, 255))

ROWS: List[Tuple[str, int, int]] = [("idle", 8, 150), ("walk", 8, 104), ("talk", 8, 108), ("interact", 8, 92)]

PEOPLE: Dict[str, Person] = {}
META: Dict[str, dict] = {}
#: Each of the crew in the round (``_round_cast.Round``), by target: own art
#: where it exists, side heads drawn by the cast's makers, 3D for the rest.
#: The rows do not use this.
ROUNDS: Dict[str, "C.Round"] = {}


def _build(cm: float, *, girth: float = 0.0, stoop: float = 0.0, woman: bool = False, legs: float = 0.0) -> Build:
    """A person ``cm`` tall: 168 cm is 108 pixels. Most of a height is legs;
    a head is one size. ``girth`` is pixels wider than a slight person;
    ``stoop`` how far forward the neck is; ``legs`` moves that many pixels
    of the height from the trunk to the legs. A woman's shoulders are
    narrower than her hips, and a man's are wider."""
    height = cm * 108.0 / 168.0
    trunk = 36.0 + (height - 108.0) * 0.18 - legs
    hip_up = height - trunk - 24.0
    leg = hip_up - 3.0
    near, far = (-4.6, 5.6) if woman else (-5.8, 7.4)
    hip = 4.0 if woman else 3.6
    return Build(hip_up=hip_up, thigh=leg * 0.52 + 0.15, shin=leg * 0.48 + 0.15, neck=(0.4 + stoop, -trunk), upper=19.0 + (height - 108.0) * 0.12,
                 fore=18.0 + (height - 108.0) * 0.12, near_shoulder=(near - girth * 0.5, -trunk + 4.4), far_shoulder=(far + girth * 0.5, -trunk + 4.8),
                 near_hip=(-hip, 0.0), far_hip=(hip, 0.0), head_up=(0.9 + stoop * 0.3, -12.0), height=height,
                 half_width=(12.5 + girth, 14.0 + girth))


def _person(target: str, cm: float, *, girth: float = 0.0, stoop: float = 0.0, woman: bool = False, legs: float = 0.0) -> Person:
    p = Person(target, _build(cm, girth=girth, stoop=stoop, woman=woman, legs=legs))
    p.rows = list(ROWS)
    # The feet near to each other: a person who stands straight has straight legs.
    p.set_rest(nf=(-3.6, 0.0, 0.0), ff=(4.6, 0.0, 0.0))
    PEOPLE[target] = p
    return p


def _meta(target: str, name: str, traits: Sequence[str], authoring: str, gameplay: str, barks: Sequence[str]) -> None:
    p = PEOPLE[target]
    top = p.ground - p.b.height
    META[target] = {
        "actor": {"character_id": f"npc_{target}", "display_name": name},
        "visual": {"default_pose": "idle"},
        "body": {"body_plan": "HumanoidBiped", "body_kind": "Standard", "mass_class": "Medium", "traits": list(traits), "locomotion_hint": "Walk"},
        "capabilities": {
            "traversal": {"walk": True, "jump": None, "climb": None, "fly": None, "swim": None, "crawl": None, "use_lifts": True,
                          "door_access": ["public"]},
            "interactions": {"talk": True, "trade": None, "carry": None, "open_doors": ["public"]},
        },
        "brain": {"default_preset": "patrol_peaceful"},
        "actions": {"default_preset": "peaceful"},
        "tags": list(traits),
        "animation_bindings": {
            "default": {"animation": "idle", "events": []},
            "locomotion.walk": {"animation": "walk", "events": []},
            "interaction.talk": {"animation": "talk", "events": []},
            "interaction.use": {"animation": "interact", "events": []},
        },
        "sockets": {
            "head": {"source": "explicit.profile.humanoid", "point": {"x": p.cx + 2.0, "y": top + 13.0}},
            "chest": {"source": "explicit.profile.humanoid", "point": {"x": p.cx + 1.0, "y": top + 40.0}},
            "hand_l": {"source": "explicit.profile.humanoid", "point": {"x": p.cx - 9.0, "y": top + 62.0}},
            "hand_r": {"source": "explicit.profile.humanoid", "point": {"x": p.cx + 11.0, "y": top + 62.0}},
            "speech_bubble": {"source": "explicit.profile.humanoid", "point": {"x": p.cx + 2.0, "y": top - 16.0}},
        },
        "authoring_description": authoring,
        "gameplay_description": gameplay,
        "dialogue_hints": {"barks": list(barks)},
    }


def _dress(p: Person, skin, sleeve: RGBA, sleeve_dark: RGBA, leg: RGBA, leg_dark: RGBA, shoe: RGBA, shoe_dark: RGBA, *, cuff: Optional[RGBA] = None,
           arm: Tuple[float, float, float] = (6.8, 5.8, 5.0), legs: Tuple[float, float, float] = (7.4, 6.2, 5.4), hand: float = 1.0, bare_from: float = 1.0,
           heel: float = 0.0, long_shoe: float = 1.0, neck: float = 4.8, boot_from: float = 1.0) -> None:
    """Sleeves, trouser legs, hands, shoes and a neck. ``bare_from``: a
    sleeve stops this far down the forearm, and the rest is skin.
    ``boot_from``: a boot (the colour of the shoe) comes this far up the
    shin."""
    K = p.K
    p.upper_arm = lambda near: [(0.0, 1.0, arm[0], arm[1], sleeve if near else sleeve_dark)]
    if bare_from < 1.0:
        p.forearm = lambda near: [(bare_from, 1.0, arm[1] - 1.2, arm[2] - 0.6, skin[0] if near else skin[1]),
                                  (0.0, bare_from, arm[1], arm[1] - 0.4, sleeve if near else sleeve_dark)]
    else:
        p.forearm = lambda near: [(0.0, 1.0, arm[1], arm[2], sleeve if near else sleeve_dark)]
    p.thigh = lambda near: [(0.0, 1.0, legs[0], legs[1], leg if near else leg_dark)]
    if boot_from < 1.0:
        p.shin = lambda near: [(0.0, boot_from, legs[1], legs[1] - 0.3, leg if near else leg_dark),
                               (boot_from, 1.0, legs[1] + 0.6, legs[2] + 0.4, shoe if near else mix(shoe, shoe_dark, 0.6))]
    else:
        p.shin = lambda near: [(0.0, 1.0, legs[1], legs[2], leg if near else leg_dark)]
    p.hand = R.make_hand(K, skin[0], skin[1], skin[2], cuff, mix(cuff, INK, 0.25) if cuff else None, size=hand)
    p.shoe = R.make_shoe(K, shoe, shoe_dark, p.b.ankle_up, long=long_shoe, heel=heel)
    p.neck = R.make_neck(K, skin[1], neck)


def _face(p: Person, head, eyes, brows, mouth, *extra) -> None:
    """``extra``: pieces (no arguments) painted over the face: glasses, a hat."""
    p.head_layers = lambda pose: ([(head(), "head"), (eyes(str(pose["eyes"])), "eyes"), (brows(R.brow_mood(pose)), "brows"),
                                   (mouth(str(pose["mouth"])), "mouth")] + [(fn(), f"extra_{k}") for k, fn in enumerate(extra)])


def _walk(p: Person, near: Tuple[float, float], far: Tuple[float, float], *, reach: float = 8.0, lift: float = 4.6, lean: float = 2.0, swing: float = 0.0,
          nh: str = "soft", fh: str = "soft") -> None:
    """A walk of this person: where the hands are, and how far they swing."""

    def walk(i: int, n: int):
        ph, s, c = loop(i, n)
        nf, ff = R.stride(ph, reach, lift)
        return p.P(hip=(0.5, 0.8 * math.cos(2.0 * ph)), lean=lean, head=(0.0, 0.0, 1.2 * s), na=(near[0] - swing * c, near[1] - 0.15 * swing * abs(c)),
                   fa=(far[0] + swing * c, far[1] - 0.15 * swing * abs(c)), nh=nh, fh=fh, nf=nf, ff=ff, hem=(1.0 + 1.2 * abs(c), 0.4 + 1.2 * abs(c)))

    p.poses["walk"] = walk


# ---- Things the crew shows ---------------------------------------------------


def _padlock(K, open_: bool, size: float = 1.0):
    k = size

    def shape(d) -> None:
        K.rrect(d, K.home[0] - 4.0 * k, K.home[1] - 1.0 * k, K.home[0] + 4.0 * k, K.home[1] + 5.4 * k, 1.0, WHITE)
        x = 2.4 * k if open_ else 0.0
        K.stroke(d, [K.at(-2.4 * k + x, -1.0 * k), K.at(-2.4 * k + x, -4.4 * k), K.at(x, -6.0 * k), K.at(2.4 * k + x, -4.4 * k), K.at(2.4 * k + x, -2.6 * k if open_ else -1.0 * k)],
                 WHITE, 1.5 * k)

    def detail(d) -> None:
        K.oval(d, K.at(0.0, 1.6 * k), 1.1 * k, 1.1 * k, INK)
        K.line(d, [K.at(0.0, 1.6 * k), K.at(0.0, 3.6 * k)], INK, 0.8 * k)

    return K.solid(("padlock", open_, size), shape, GOLD, detail, outline=1.0, rim=0.3, shade=0.4, shade_colour=GOLD_DARK)


def _key(K, size: float = 1.0):
    k = size

    def shape(d) -> None:
        K.oval(d, K.home, 2.6 * k, 2.6 * k, WHITE)
        K.stroke(d, [K.at(2.0 * k, 0.0), K.at(9.0 * k, 0.0)], WHITE, 1.6 * k)
        for x in (6.4, 8.6):
            K.stroke(d, [K.at(x * k, 0.0), K.at(x * k, 2.6 * k)], WHITE, 1.3 * k)

    return K.solid(("key", size), shape, GOLD, lambda d: K.oval(d, K.home, 1.0 * k, 1.0 * k, GOLD_DARK), outline=1.0, rim=0.3, shade=0.4,
                   shade_colour=GOLD_DARK)


def _letter(K, sealed: Optional[RGBA] = SEAL, size: float = 1.0, mark: str = ""):
    """An envelope. ``mark``: ``tick`` or ``cross`` stamped on it."""
    k = size

    def shape(d) -> None:
        K.rrect(d, K.home[0] - 6.0 * k, K.home[1] - 4.0 * k, K.home[0] + 6.0 * k, K.home[1] + 4.0 * k, 0.6, WHITE)

    def detail(d) -> None:
        K.line(d, [K.at(-6.0 * k, -4.0 * k), K.at(0.0, 0.6 * k), K.at(6.0 * k, -4.0 * k)], PAPER_DARK, 0.7)
        if sealed is not None:
            K.oval(d, K.at(0.0, 0.8 * k), 1.7 * k, 1.7 * k, sealed)
        if mark == "tick":
            K.tick(d, K.at(2.4 * k, 1.0 * k), 2.6 * k, (60, 150, 90, 255), 1.2)
        elif mark == "cross":
            K.cross(d, K.at(2.4 * k, 1.0 * k), 2.2 * k, SEAL, 1.2)

    return K.solid(("letter", sealed, size, mark), shape, PAPER, detail, outline=1.0, rim=0.2, shade=0.35, shade_colour=PAPER_DARK)


def _waves(K, count: int, fill: RGBA, dark: RGBA, facing: float = 1.0):
    """Sound, as arcs that open away from ``home`` toward ``facing``."""

    def shape(d) -> None:
        for j in range(count):
            r = 4.0 + 3.6 * j
            pts = [K.at(facing * r * math.cos(math.radians(a)), r * math.sin(math.radians(a))) for a in range(-50, 51, 10)]
            K.stroke(d, pts, WHITE, 1.4)

    return R.chalk(K, ("waves", count, facing), shape, fill, dark)


def _spark(K, size: float, fill: RGBA):
    def paint(d) -> None:
        K.star4(d, K.home, size, fill)
        K.star4(d, K.home, size * 0.45, WHITE, None, 0.0, 0.4)

    return K.piece(("spark", size, fill), paint)


def _mask(K, fill: RGBA, dark: RGBA, smile: bool, size: float = 1.0):
    """A face that is not hers."""
    k = size

    def shape(d) -> None:
        K.oval(d, K.home, 4.6 * k, 5.6 * k, WHITE)

    def detail(d) -> None:
        for x in (-1.8, 1.8):
            K.oval(d, K.at(x * k, -1.2 * k), 1.0 * k, 1.3 * k, INK)
        y = 2.4 * k
        bend = 1.0 if smile else -1.0
        K.line(d, [K.at(-2.0 * k, y - 0.6 * bend), K.at(0.0, y + 0.8 * bend), K.at(2.0 * k, y - 0.6 * bend)], INK, 0.8)

    return K.solid(("mask", fill, smile, size), shape, fill, detail, outline=1.0, rim=0.3, shade=0.4, shade_colour=dark)


# =============================================================================
# Craig: the cracker. Laconic, patient, a ring of other people's keys.
# =============================================================================


def _craig() -> None:
    p = _person("craig", 180.0, girth=0.6)
    K, P = p.K, p.P
    skin = TAN
    JACKET, JACKET_DARK, JACKET_LIGHT = (176, 136, 76, 255), (128, 92, 56, 255), (212, 176, 112, 255)
    SHIRT, TROUSER, TROUSER_DARK = (62, 74, 92, 255), (70, 62, 62, 255), (46, 40, 44, 255)
    CAP, CAP_DARK, HAIR = (98, 82, 70, 255), (62, 50, 46, 255), (74, 52, 40, 255)
    top = p.b.neck[1] - 2.0

    def front(d, hb, hf) -> None:
        K.poly(d, [K.at(2.0, top - 1.0), K.at(12.0, top - 1.0), K.at(12.6 + hf, 14.0), K.at(5.0 + hf * 0.5, 14.0), K.at(4.0, -14.0)], SHIRT)
        K.poly(d, [K.at(9.8, top - 1.0), K.at(13.0, top - 1.0), K.at(13.4 + hf, 14.0), K.at(10.6 + hf, 14.0)], JACKET_DARK)
        K.poly(d, [K.at(-0.6, top), K.at(3.4, top), K.at(4.4, -22.0), K.at(0.2, -29.0)], JACKET_LIGHT)
        K.line(d, [K.at(0.2, -29.0), K.at(4.4, -22.0), K.at(4.0, -14.0), K.at(5.0 + hf * 0.5, 10.0)], JACKET_DARK, 0.7)
        # A pocket with a flap, and his belt with the ring of keys on it.
        K.rrect(d, K.home[0] - 7.4, K.home[1] - 24.0, K.home[0] - 2.4, K.home[1] - 19.0, 0.6, mix(JACKET, JACKET_DARK, 0.4))
        K.line(d, [K.at(-7.4, -22.4), K.at(-2.4, -22.0)], JACKET_DARK, 0.6)
        K.poly(d, [K.at(-12.0, 2.0), K.at(14.0, 2.6), K.at(14.0, 5.4), K.at(-12.0, 4.8)], TROUSER_DARK)
        K.oval(d, K.at(-4.0, 7.4), 2.6, 2.8, None, GOLD, 0.8)  # type: ignore[arg-type]
        for x, y in ((-5.6, 10.6), (-3.6, 11.4), (-2.0, 10.2)):
            K.line(d, [K.at(-4.0, 9.6), K.at(x, y + 1.6)], GOLD, 1.0)

    p.torso = R.make_torso(K, ("craig",), JACKET, JACKET_DARK, back=(9.8, 10.4, 9.4, 10.2), front=(8.8, 10.8, 10.4, 11.0), hem_y=11.0, top=top,
                           shoulders=((-6.0, p.b.near_shoulder[1] + 0.6), (7.0, p.b.far_shoulder[1] + 0.4)), shoulder_r=(5.8, 5.4), shade_from=40.0,
                           detail=front)
    _dress(p, skin, JACKET, JACKET_DARK, TROUSER, TROUSER_DARK, (86, 60, 44, 255), (52, 36, 30, 255), cuff=SHIRT, arm=(7.6, 6.4, 5.6), legs=(8.0, 6.6, 5.8),
           hand=1.08, long_shoe=1.08)

    def cap_shape(d) -> None:
        # A flat cap: low over his brow, its peak out in front.
        K.oval(d, K.at(-0.6, -8.4), 9.6, 4.8, WHITE)
        K.poly(d, [K.at(4.0, -7.6), K.at(12.6, -5.4), K.at(12.2, -3.8), K.at(4.0, -5.0)], WHITE)

    def hair(d) -> None:
        K.poly(d, [K.at(20.0, -6.0), K.at(-2.8, -6.0), K.at(-3.6, -2.4), K.at(-6.2, -2.0), K.at(-6.8, 3.4), K.at(-5.2, 4.6), K.at(-4.8, 6.6),
                   K.at(-20.0, 6.6), K.at(-20.0, -26.0), K.at(20.0, -26.0)], HAIR)
        K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, -5.4), K.at(4.0, -5.4), K.at(-10.0, -6.6), K.at(-20.0, -4.0)], CAP)
        K.poly(d, [K.at(4.0, -6.0), K.at(14.0, -4.0), K.at(14.0, -2.0), K.at(4.0, -4.6)], CAP_DARK)
        K.line(d, [K.at(-9.0, -7.0), K.at(4.0, -6.2)], CAP_DARK, 0.7)

    def face(d) -> None:
        # He has not shaved today.
        K.poly(d, [K.at(-1.0, 5.0), K.at(8.4, 6.0), K.at(7.6, 10.6), K.at(3.0, 11.8), K.at(-0.6, 9.0)], mix(skin[0], HAIR, 0.22))

    head = R.make_head(K, ("craig",), *skin, skull=(0.0, -2.4, 8.2, 9.0), jaw=(2.6, 4.2, 6.2, 7.6), nose=((7.2, -0.8), (10.4, 3.0), (9.8, 4.6), (7.2, 5.0)),
                       shape=cap_shape, under=hair, over=face)
    eyes = R.make_eyes(K, (1.2, -0.4), (7.0, -0.6), ink=INK, white=None, lid=skin[2])
    _face(p, head, eyes, R.make_brows(K, [(-1.2, -3.6), (1.4, -4.2), (4.0, -3.6)], [(5.6, -3.8), (7.2, -4.2), (8.6, -3.6)], HAIR, 1.3),
          R.make_mouth(K, (5.4, 8.2), (104, 52, 50, 255), wide=0.9))

    # ---- From the front: his jacket open on his shirt, his cap low, the
    # ring of keys at his belt.
    sy = p.b.near_shoulder[1] + 0.6

    def front_jacket(d) -> None:
        K.poly(d, [K.at(-4.0, top - 1.0), K.at(4.0, top - 1.0), K.at(5.4, 2.0), K.at(-5.4, 2.0)], SHIRT)
        K.poly(d, [K.at(-5.4, 2.0), K.at(5.4, 2.0), K.at(5.4, 14.0), K.at(-5.4, 14.0)], TROUSER)
        K.poly(d, [K.at(-5.4, 2.0), K.at(5.4, 2.0), K.at(5.4, 4.8), K.at(-5.4, 4.8)], TROUSER_DARK)
        for sx in (-1.0, 1.0):
            K.poly(d, [K.at(4.0 * sx, top), K.at(7.0 * sx, top + 1.0), K.at(4.6 * sx, -20.0)], JACKET_LIGHT)
            K.line(d, [K.at(4.6 * sx, -20.0), K.at(5.4 * sx, 11.0)], JACKET_DARK, 0.7)
        K.rrect(d, K.home[0] + 5.8, K.home[1] - 24.0, K.home[0] + 9.6, K.home[1] - 19.6, 0.6, mix(JACKET, JACKET_DARK, 0.4))
        K.line(d, [K.at(5.8, -22.6), K.at(9.6, -22.6)], JACKET_DARK, 0.6)
        K.oval(d, K.at(-3.2, 7.2), 2.0, 2.2, None, GOLD, 0.8)  # type: ignore[arg-type]
        for x, y in ((-4.6, 10.4), (-3.0, 11.2), (-1.6, 10.0)):
            K.line(d, [K.at(-3.2, 9.2), K.at(x, y + 1.4)], GOLD, 0.9)

    def front_cap_shape(d) -> None:
        K.oval(d, K.at(0.0, -8.6), 10.0, 5.0, WHITE)
        K.poly(d, [K.at(-8.6, -6.6), K.at(8.6, -6.6), K.at(9.0, -3.8), K.at(-9.0, -3.8)], WHITE)

    def front_cap(d) -> None:
        for sx in (-1.0, 1.0):
            K.poly(d, [K.at(6.4 * sx, -6.0), K.at(20.0 * sx, -6.0), K.at(20.0 * sx, 1.0), K.at(7.2 * sx, 1.0)], HAIR)
        K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, -5.6), K.at(-20.0, -5.6)], CAP)
        K.poly(d, [K.at(-20.0, -5.8), K.at(20.0, -5.8), K.at(20.0, -3.6), K.at(-20.0, -3.6)], CAP_DARK)
        K.line(d, [K.at(-9.0, -7.2), K.at(0.0, -6.6), K.at(9.0, -7.2)], CAP_DARK, 0.7)

    def front_stubble(d) -> None:
        # He has not shaved today.
        K.poly(d, [K.at(-6.4, 4.6), K.at(6.4, 4.6), K.at(5.2, 10.0), K.at(0.0, 12.6), K.at(-5.2, 10.0)], mix(skin[0], HAIR, 0.22))
        K.line(d, [K.at(-0.2, 0.8), K.at(-1.2, 3.4), K.at(0.0, 4.2), K.at(1.2, 3.4)], skin[2], 0.6)

    p.front_torso = R.make_front_torso(K, ("craig",), JACKET, JACKET_DARK, [(top, 4.4), (top + 3.6, 9.6), (-24.0, 10.2), (-8.0, 9.8), (11.0, 10.6)],
                                       shoulder=(7.6, sy, 5.0, 5.2), detail=front_jacket)
    p.front_head_layers = R.front_face(
        R.make_front_head(K, ("craig",), skin[0], skin[2], wide=8.0, jaw=6.6, chin=3.8, ears=skin[0], shape=front_cap_shape, hair=front_cap, face=front_stubble),
        R.make_front_eyes(K, ("craig",), white=None, ink=INK, spread=3.4, y=-0.2), R.make_front_brows(K, ("craig",), HAIR, spread=3.4, y=-2.6, width=1.3),
        R.make_front_mouth(K, ("craig",), y=8.2, colour=(104, 52, 50, 255), wide=0.8))
    p.front_shoe = R.make_front_shoe(K, (86, 60, 44, 255), (52, 36, 30, 255), p.b.ankle_up)
    p.front_span = (8.4, 4.8)
    R.add_front_rows(p, hands="sides")

    #: His thumbs in his belt.
    belt_near, belt_far = (1.5, 17.5), (-1.0, 18.0)
    p.set_rest(na=belt_near, fa=belt_far, nh="fist", fh="fist", mouth="flat")

    @p.row
    def idle(i: int, n: int):
        # He waits. Most locks open for a man who waits.
        _, s, _c = loop(i, n)
        return P(hip=(0.0, 0.4 + 0.4 * s), lean=-2.0, head=(0.0, -0.2 * s, 2.0 if i >= n - 3 else 0.0), eyes="closed" if i == n - 2 else "open")

    _walk(p, belt_near, belt_far, reach=8.5, lean=1.0)

    @p.row
    def talk(i: int, n: int):
        _, s, _c = loop(i, n)
        return P(hip=(0.0, 0.3 * s), lean=-2.0, head=(0.3, 0.0, 2.0 * s), na=(12.0, 9.0 - 2.0 * max(0.0, s)), nh="open" if s > 0.0 else "soft",
                 mouth=("open", "flat", "smile", "flat")[i % 4])

    @p.row
    def interact(i: int, n: int):
        # One of his keys fits. One of them always does.
        reach = P(hip=(1.5, 1.0), lean=7.0, na=(25.0, 2.0), nh="fist", brows=-1.0)
        return p.keys(shot(i, n), [(0.0, P()), (0.3, reach), (0.75, dict(reach, na=(25.0, 3.0))), (1.0, P(mouth="smile"))])

    def effects(ctx) -> List[Stamp]:
        out: List[Stamp] = []
        if ctx.anim == "interact" and 0.25 <= ctx.u <= 0.85:
            out.append((_key(K), (ctx.hand[0] + 3.0, ctx.hand[1] - 1.0), "key", 0.0))
            out.append((_padlock(K, ctx.u > 0.55), (ctx.hand[0] + 21.0, ctx.hand[1] - 1.0), "padlock", 0.0))
        return out

    p.effects = effects

    # ---- In the round: his cap (crown and peak), his jacket open on his
    # shirt and belt, the ring of keys at his belt, his head from the side
    # drawn by the cast's makers. The pocket and the keys are on one side,
    # so his trunk is not mirrored.
    def side_cap_shape(d) -> None:
        K.oval(d, K.at(-1.2, -8.4), 10.2, 4.8, WHITE)
        K.poly(d, [K.at(5.0, -7.6), K.at(13.6, -5.4), K.at(13.2, -3.8), K.at(5.0, -5.0)], WHITE)

    def side_hair(d) -> None:
        K.poly(d, [K.at(20.0, -6.0), K.at(0.6, -6.0), K.at(0.8, -2.4), K.at(1.2, 1.0), K.at(-1.2, 1.4), K.at(-3.8, 3.6), K.at(-4.4, 6.6),
                   K.at(-20.0, 6.6), K.at(-20.0, -26.0), K.at(20.0, -26.0)], HAIR)
        K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, -5.4), K.at(5.0, -5.4), K.at(-11.0, -6.0), K.at(-20.0, -4.0)], CAP)
        K.poly(d, [K.at(5.0, -6.0), K.at(15.0, -4.0), K.at(15.0, -2.0), K.at(5.0, -4.6)], CAP_DARK)
        K.line(d, [K.at(-10.0, -6.4), K.at(5.0, -6.2)], CAP_DARK, 0.7)

    def side_face(d) -> None:
        K.poly(d, [K.at(0.6, 5.0), K.at(9.4, 6.0), K.at(8.6, 10.6), K.at(4.0, 11.8), K.at(0.8, 9.0)], mix(skin[0], HAIR, 0.22))

    side_head = R.make_head(K, ("craig_side",), *skin, skull=(0.0, -2.4, 9.2, 9.0), jaw=(3.4, 4.2, 6.8, 7.6),
                            nose=((8.0, -0.8), (11.2, 3.0), (10.6, 4.6), (8.0, 5.0)), ear=(-1.6, 1.0, 2.2, 3.3), shape=side_cap_shape, under=side_hair,
                            over=side_face, far_shade=False)
    side_eyes = R.make_eyes(K, (6.2, -0.4), None, ink=INK, white=None, lid=skin[2])
    side_brows = R.make_brows(K, [(4.2, -3.6), (6.2, -4.2), (8.4, -3.6)], None, HAIR, 1.3)
    side_mouth = R.make_mouth(K, (8.0, 8.2), (104, 52, 50, 255), wide=0.6)
    crop = ((0.0, -4.0, -1.2), (8.6, 7.6, 8.8))
    cap = W.Hat(
        crown=[O.Ring(-5.4, 0.0, -0.4, 8.8, 9.0), O.Ring(-8.8, 0.0, -0.8, 9.6, 9.8), O.Ring(-11.4, 0.0, -1.0, 8.6, 8.8), O.Ring(-12.4, 0.0, -1.0, 0.0, 0.0)],
        # The peak: a brim whose ring is forward of the crown, so only its
        # front is out of it.
        brim=[O.Ring(-5.6, 0.0, 1.0, 6.0, 7.4, v=0.0), O.Ring(-5.2, 0.0, 4.6, 6.6, 8.6, droop=1.4, v=1.0), O.Ring(-4.6, 0.0, 4.6, 6.6, 8.6, droop=1.4, v=2.0),
              O.Ring(-5.0, 0.0, 1.0, 6.0, 7.4, v=3.0)],
        garment=W.Garment(CAP, CAP_DARK, features=[W.Shade(-0.4)]), under=CAP_DARK,
        lines=[O.curve([(-9.0, -7.0, 2.0), (0.0, -6.6, 8.6), (9.0, -7.0, 2.0)], CAP_DARK, 0.7)])
    ROUNDS["craig"] = C.Round(
        "Craig", C.PersonBody(p, mirror=("head",), heads={"side": lambda pose: [(side_head(), "head"), (side_eyes(str(pose["eyes"])), "eyes"),
                                                                                 (side_brows(R.brow_mood(pose)), "brows"), (side_mouth(str(pose["mouth"])), "mouth")]}),
        C.Look(
            C.auto_head(p, head, eyes, hair=lambda u, v: ((np.abs(u) > 60.0) & (v < 4.0)) | ((np.abs(u) > 100.0) & (v < 6.6)), hair_colour=HAIR,
                        hair_shade=mix(HAIR, INK, 0.3), volumes=[crop]),
            C.auto_trunk(p, [W.Opening(24.0, SHIRT, top=top - 1.0, bottom=2.0), W.Opening(24.0, TROUSER, top=2.0), W.Patch(-24.0, 24.0, 2.0, 4.8, TROUSER_DARK),
                             W.Lapels(24.0, top, -20.0, 12.0, JACKET_LIGHT, line=JACKET_DARK), W.Down(24.0, -20.0, 11.0, JACKET_DARK),
                             W.Down(-24.0, -20.0, 11.0, JACKET_DARK), W.Patch(33.0, 55.0, -24.0, -19.6, mix(JACKET, JACKET_DARK, 0.4)),
                             W.Across(33.0, 55.0, -22.6, JACKET_DARK), W.Dot(-18.0, 7.2, 2.0, TROUSER, GOLD), W.Down(180.0, top + 4.0, 11.0, JACKET_DARK)]),
            head_pieces=[cap]),
        # His thumbs in his belt.
        C.Stance(hands={"r": C.Hand(at=(-8.4, -2.0, 6.4), pole=(-1.0, -0.2, -0.3), mode="fist"), "l": C.Hand(at=(8.4, -2.0, 6.4), pole=(1.0, -0.2, -0.3), mode="fist")},
                 stagger=2.0))
    _meta("craig", "Craig", ["hub", "peaceful", "cryptography_crew", "cracker"],
          "Craig is the password-cracker role sometimes added to cryptographic casts. He is not a specific person: his ordinary name hides a "
          "specialist who attacks weak secrets by guessing, searching, and exploiting what users thought nobody would try.",
          "Use as a cracker, lock tester, puzzle rival, or tutorial for password entropy. He should be laconic, patient, and much more dangerous "
          "around reused patterns than around genuinely random secrets.",
          ["I'm Craig.", "Most secrets are shorter than their owners think.", "I only need the guess you reused."])


# =============================================================================
# Eve: the eavesdropper. She changes nothing. She listens.
# =============================================================================


def _eve() -> None:
    # A slight young woman: narrow, soft in the face, her hood up and her
    # long dark hair out of the front of it.
    p = _person("eve", 168.0, woman=True)
    K, P = p.K, p.P
    skin = PALE
    DRESS, DRESS_DARK, DRESS_LIGHT = (116, 80, 156, 255), (76, 48, 110, 255), (160, 124, 198, 255)
    CLOAK, CLOAK_DARK, HAIR, HAIR_LIGHT, STRAP = (72, 52, 104, 255), (46, 32, 72, 255), (58, 40, 54, 255), (112, 84, 104, 255), (140, 92, 60, 255)
    top = p.b.neck[1] - 2.0

    def front(d, hb, hf) -> None:
        # A belt at her waist, the strap of her satchel, a clasp at her neck.
        K.poly(d, [K.at(-9.0, -14.6), K.at(9.0, -13.8), K.at(9.0, -11.4), K.at(-9.0, -12.2)], DRESS_DARK)
        K.oval(d, K.at(3.6, -12.8), 1.4, 1.4, GOLD)
        K.line(d, [K.at(-7.6, top + 5.0), K.at(7.6, -6.0)], STRAP, 1.5)
        K.oval(d, K.at(4.4, top + 3.0), 1.4, 1.4, GOLD)
        for x in (-4.6, 0.6, 5.0):
            K.line(d, [K.at(x, -4.0), K.at(x * 1.5 - hb * 0.3, 30.0)], DRESS_DARK, 0.6)
        K.poly(d, [K.at(-20.0 - hb, 31.0), K.at(20.0 + hf, 31.0), K.at(20.0 + hf, 36.0), K.at(-20.0 - hb, 36.0)], DRESS_LIGHT)

    p.torso = R.make_figure(K, ("eve",), DRESS, DRESS_DARK, back=(7.0, 7.4, 5.6, 7.8, 11.4), front=(6.2, 8.6, 6.0, 8.4, 11.0), hem_y=34.0, top=top,
                            shoulders=((-4.6, p.b.near_shoulder[1] + 0.6), (5.2, p.b.far_shoulder[1] + 0.4)), shoulder_r=(4.2, 3.8), shade_from=6.2,
                            detail=front)
    _dress(p, skin, DRESS, DRESS_DARK, DRESS, DRESS_DARK, (84, 60, 70, 255), (50, 34, 46, 255), cuff=DRESS_LIGHT, arm=(5.6, 4.8, 4.2), legs=(6.2, 5.0, 4.2),
           hand=0.85, neck=3.8)

    def cloak(ctx) -> List[Stamp]:
        # Her cloak hangs behind her, from her shoulders to her calves.
        sway = int(round(float(ctx.pose["hem"][0]) * 1.6))  # type: ignore[index]

        def shape(d) -> None:
            K.poly(d, [K.at(-4.0, top + 1.0), K.at(-9.6, top + 6.0), K.at(-11.0, -10.0), K.at(-13.6 - sway, 30.0), K.at(-4.0, 32.0), K.at(4.0, 28.0),
                       K.at(3.0, top + 2.0)], WHITE)

        part = K.solid(("eve_cloak", sway), shape, CLOAK, lambda d: K.line(d, [K.at(-7.0, top + 8.0), K.at(-10.0 - sway * 0.6, 28.0)], CLOAK_DARK, 0.7),
                       outline=1.3, rim=0.2, shade=0.4, shade_colour=CLOAK_DARK)
        return [(part, ctx.hip, "cloak", ctx.lean)]

    p.layers["back"].append(cloak)

    def hood_shape(d) -> None:
        # Her hood: up, round, and a soft point behind her head.
        K.oval(d, K.at(-1.4, -3.6), 10.2, 10.6, WHITE)
        K.poly(d, [K.at(-9.0, -8.0), K.at(-13.6, -2.0), K.at(-9.6, 6.6), K.at(-4.0, 9.4), K.at(2.0, 8.4)], WHITE)

    def hood(d) -> None:
        K.poly(d, [K.at(20.0, -8.8), K.at(8.6, -8.8), K.at(4.6, -9.6), K.at(1.2, -8.2), K.at(-1.4, -5.0), K.at(-2.0, 0.0), K.at(-1.4, 5.0), K.at(0.4, 9.6),
                   K.at(3.0, 20.0), K.at(-20.0, 20.0), K.at(-20.0, -26.0), K.at(20.0, -26.0)], CLOAK)
        K.line(d, [K.at(8.6, -9.0), K.at(4.4, -9.8), K.at(1.0, -8.2), K.at(-1.6, -5.0), K.at(-2.2, 0.0), K.at(-1.6, 5.0), K.at(0.2, 9.6)], DRESS_LIGHT, 1.0)
        K.line(d, [K.at(-9.0, -6.0), K.at(-11.0, -2.0), K.at(-8.6, 4.6)], CLOAK_DARK, 0.7)
        # Her hair, parted in the middle, soft at each side of her face.
        K.poly(d, [K.at(1.2, -8.0), K.at(8.6, -8.6), K.at(9.6, -4.0), K.at(7.0, -6.6), K.at(3.6, -6.0), K.at(0.6, -2.0), K.at(-0.6, 4.6), K.at(-1.6, 0.0),
                   K.at(-1.2, -5.0)], HAIR)
        K.line(d, [K.at(4.6, -8.2), K.at(1.6, -5.0), K.at(0.0, 1.0)], HAIR_LIGHT, 0.5)

    head = R.make_head(K, ("eve",), *skin, skull=(0.0, -2.2, 7.6, 8.6), jaw=(2.4, 3.4, 5.0, 6.4), nose=((7.2, 1.0), (8.6, 3.0), (8.2, 3.8), (7.2, 4.0)),
                       ear=None, shape=hood_shape, under=hood)
    eyes = R.make_eyes(K, (2.6, -0.2), (7.4, -0.4), ink=INK, white=None, lid=INK, size=0.9)
    _face(p, head, eyes, R.make_brows(K, [(0.6, -3.6), (2.6, -4.3), (4.6, -4.0)], [(6.0, -4.1), (7.4, -4.4), (8.6, -4.0)], HAIR, 0.7),
          R.make_mouth(K, (5.6, 6.8), (140, 60, 76, 255), wide=0.7, lips=(206, 112, 124, 255)))

    def lock(ctx) -> List[Stamp]:
        # A long lock of it comes out of her hood and hangs in front of her shoulder.
        a = math.radians(ctx.turn)
        root = (ctx.head[0] + 0.5 * math.cos(a) - 7.0 * math.sin(a), ctx.head[1] + 0.5 * math.sin(a) + 7.0 * math.cos(a))
        at = pin(root)
        ch = R.chain((root[0] - at[0], root[1] - at[1]), 5, 4.2, 96.0, wave=7.0 if ctx.anim == "walk" else 3.0, curl=-4.0, phase=ctx.phase)
        return [(R.ribbon(K, ("eve_lock",), [ch], 3.6, HAIR, HAIR_LIGHT, taper=0.5), at, "lock", 0.0)]

    p.layers["over_torso"].append(lock)

    # ---- From the front: her hood round her face, a lock of hair down each
    # side of it, the strap of her satchel across her.
    sy = p.b.near_shoulder[1] + 0.6

    def front_dress(d) -> None:
        K.poly(d, [K.at(-9.0, -14.4), K.at(9.0, -14.4), K.at(9.0, -11.8), K.at(-9.0, -11.8)], DRESS_DARK)
        K.oval(d, K.at(0.0, -13.0), 1.4, 1.4, GOLD)
        K.line(d, [K.at(-7.0, top + 5.0), K.at(7.4, -6.0)], STRAP, 1.5)
        K.oval(d, K.at(0.0, top + 3.0), 1.4, 1.4, GOLD)
        for x in (-4.6, 0.0, 4.6):
            K.line(d, [K.at(x, -4.0), K.at(x * 1.6, 30.0)], DRESS_DARK, 0.6)
        K.poly(d, [K.at(-20.0, 31.0), K.at(20.0, 31.0), K.at(20.0, 36.0), K.at(-20.0, 36.0)], DRESS_LIGHT)

    def front_hood_shape(d) -> None:
        K.oval(d, K.at(0.0, -3.4), 10.2, 10.8, WHITE)
        K.poly(d, [K.at(-9.6, 0.0), K.at(-8.0, 9.6), K.at(8.0, 9.6), K.at(9.6, 0.0)], WHITE)

    def front_hood(d) -> None:
        K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, 20.0), K.at(-20.0, 20.0)], CLOAK)
        for sx in (-1.0, 1.0):
            K.poly(d, [K.at(7.4 * sx, -11.0), K.at(11.0 * sx, -3.0), K.at(9.6 * sx, 9.6), K.at(7.4 * sx, 9.6)], CLOAK_DARK)
        K.oval(d, K.at(0.0, 1.0), 6.4, 8.4, skin[0])
        ring = [K.at(6.6 * math.cos(math.radians(a)), 1.0 + 8.6 * math.sin(math.radians(a))) for a in range(-190, 11, 10)]
        K.line(d, ring, DRESS_LIGHT, 1.0)
        for sx in (-1.0, 1.0):
            K.poly(d, [K.at(0.0, -7.6), K.at(4.6 * sx, -6.4), K.at(6.2 * sx, -1.0), K.at(5.8 * sx, 7.0), K.at(4.4 * sx, 2.0), K.at(3.4 * sx, -3.6), K.at(0.6 * sx, -5.0)], HAIR)
            K.line(d, [K.at(3.0 * sx, -6.0), K.at(5.0 * sx, -1.0), K.at(5.2 * sx, 5.0)], HAIR_LIGHT, 0.5)

    def front_nose(d) -> None:
        K.line(d, [K.at(-0.2, 0.8), K.at(-0.8, 3.0), K.at(0.0, 3.6), K.at(0.8, 3.0)], skin[2], 0.5)

    p.front_torso = R.make_front_torso(K, ("eve",), DRESS, DRESS_DARK, [(top, 3.2), (top + 3.6, 6.8), (top + 12.5, 8.2), (-13.0, 5.8), (0.0, 8.0), (34.0, 11.4)],
                                       shoulder=(5.4, sy, 3.8, 4.2), detail=front_dress)
    p.front_head_layers = R.front_face(
        R.make_front_head(K, ("eve",), skin[0], skin[2], wide=7.4, jaw=5.8, chin=3.4, shape=front_hood_shape, hair=front_hood, face=front_nose),
        R.make_front_eyes(K, ("eve",), white=None, ink=INK, spread=3.0, y=-0.2, size=0.9, lash=0.5), R.make_front_brows(K, ("eve",), HAIR, spread=3.0, y=-3.4, width=0.7),
        R.make_front_mouth(K, ("eve",), y=7.4, colour=(140, 60, 76, 255), lips=(206, 112, 124, 255), wide=0.7))
    p.front_shoe = R.make_front_shoe(K, (84, 60, 70, 255), (50, 34, 46, 255), p.b.ankle_up, wide=0.85)
    p.front_span = (6.6, 4.2)
    R.add_front_rows(p)

    #: A hand cupped at the side of her hood; the other holds her elbow.
    at_ear, low = (4.6, -5.0), (2.0, 15.0)
    p.set_rest(na=low, fa=(-1.0, 22.0), mouth="smile")

    @p.row
    def idle(i: int, n: int):
        # She leans toward whoever is speaking, a hand at her ear, her weight on one hip.
        _, s, c = loop(i, n)
        return P(hip=(-0.8, 0.3 + 0.3 * s), lean=5.0 + 1.5 * c, head=(0.6, 0.0, 7.0 + 2.0 * c), na=at_ear, nh="flat", eyes="closed" if i == n - 2 else "open",
                 mouth="smile" if c > 0.3 else "flat", brows=1.0 if c > 0.6 else 0.0)

    _walk(p, low, (-1.0, 22.0), reach=7.0, lift=3.6, lean=3.0, swing=3.0)

    @p.row
    def talk(i: int, n: int):
        # She says little, and behind her hand.
        _, s, _c = loop(i, n)
        return P(hip=(0.0, 0.3 * s), lean=3.0, head=(0.4, 0.0, 3.0 * s), na=(10.0, -0.5 - 2.0 * max(0.0, s)), nh="flat", mouth=("open", "smile", "o", "smile")[i % 4],
                 brows=1.0 if s > 0.4 else 0.0)

    @p.row
    def interact(i: int, n: int):
        # She puts her ear to it.
        near = P(hip=(3.0, 2.0), lean=14.0, head=(1.0, 0.0, 16.0), na=(19.0, -2.0), nh="open", eyes="closed", brows=1.0)
        return p.keys(shot(i, n), [(0.0, P()), (0.3, near), (0.8, near), (1.0, P())])

    def effects(ctx) -> List[Stamp]:
        out: List[Stamp] = []
        if ctx.anim == "idle" or (ctx.anim == "interact" and 0.3 <= ctx.u <= 0.8):
            count = 1 + (ctx.i % 3)
            at = (ctx.head[0] + 30.0, ctx.head[1] - 1.0) if ctx.anim == "idle" else (ctx.hand[0] + 24.0, ctx.hand[1])
            out.append((_waves(K, count, DRESS_LIGHT, DRESS_DARK, -1.0), at, "waves", 0.0))
        return out

    p.effects = effects

    # ---- In the round: her hood up round her face, her cloak behind her,
    # the lock of hair in front of her near shoulder, the belt and strap of
    # her dress; her head in the hood from the side drawn by the cast's
    # makers.
    def side_hood_shape(d) -> None:
        K.oval(d, K.at(-2.0, -3.6), 10.8, 10.6, WHITE)
        K.poly(d, [K.at(-9.6, -8.0), K.at(-14.4, -2.0), K.at(-10.4, 6.6), K.at(-4.0, 9.4), K.at(2.4, 8.4)], WHITE)

    def side_hood(d) -> None:
        K.poly(d, [K.at(20.0, -8.8), K.at(9.4, -8.8), K.at(5.4, -9.6), K.at(2.0, -8.2), K.at(0.0, -5.0), K.at(-0.6, 0.0), K.at(0.0, 5.0), K.at(1.6, 9.6),
                   K.at(3.6, 20.0), K.at(-20.0, 20.0), K.at(-20.0, -26.0), K.at(20.0, -26.0)], CLOAK)
        K.line(d, [K.at(9.4, -9.0), K.at(5.2, -9.8), K.at(1.8, -8.2), K.at(-0.2, -5.0), K.at(-0.8, 0.0), K.at(-0.2, 5.0), K.at(1.4, 9.6)], DRESS_LIGHT, 1.0)
        K.line(d, [K.at(-9.6, -6.0), K.at(-11.6, -2.0), K.at(-9.2, 4.6)], CLOAK_DARK, 0.7)
        K.poly(d, [K.at(2.0, -8.0), K.at(9.4, -8.6), K.at(10.4, -4.0), K.at(7.8, -6.6), K.at(4.4, -6.0), K.at(1.6, -2.0), K.at(0.8, 4.6), K.at(0.0, 0.0),
                   K.at(0.4, -5.0)], HAIR)
        K.line(d, [K.at(5.4, -8.2), K.at(2.4, -5.0), K.at(1.0, 1.0)], HAIR_LIGHT, 0.5)

    side_head = R.make_head(K, ("eve_side",), *skin, skull=(0.0, -2.2, 8.6, 8.6), jaw=(3.2, 3.4, 5.6, 6.4), nose=((8.0, 1.0), (9.4, 3.0), (9.0, 3.8), (8.0, 4.0)),
                            ear=None, shape=side_hood_shape, under=side_hood, far_shade=False)
    side_eyes = R.make_eyes(K, (6.6, -0.2), None, ink=INK, white=None, lid=INK, size=0.9)
    side_brows = R.make_brows(K, [(4.6, -3.8), (6.6, -4.4), (8.4, -4.0)], None, HAIR, 0.7)
    side_mouth = R.make_mouth(K, (7.8, 6.8), (140, 60, 76, 255), wide=0.5, lips=(206, 112, 124, 255))
    hood_3d = ((0.0, -3.4, -2.2), (10.2, 10.8, 9.4))
    edge = O.curve([O.on_ellipsoid(*hood_3d, sx * 52.0, v, 0.3)[0] for sx, v in [(-1.0, 9.0), (-1.0, 4.0), (-1.0, -2.0), (-1.0, -7.0), (-0.5, -10.4), (0.0, -11.2),
                                                                                (0.5, -10.4), (1.0, -7.0), (1.0, -2.0), (1.0, 4.0), (1.0, 9.0)]], DRESS_LIGHT, 1.0)
    cloak_3d = W.Cloak(rings=[O.Ring(top + 1.0, 0.0, -0.6, 5.0, 4.4), O.Ring(top + 6.0, 0.0, -1.0, 9.6, 7.6), O.Ring(-10.0, 0.0, -1.4, 10.0, 8.0),
                              O.Ring(30.0, 0.0, -2.0, 12.4, 9.6)],
                       garment=W.Garment(CLOAK, CLOAK_DARK, radius=10.0, features=[W.Down(160.0, top + 8.0, 28.0, CLOAK_DARK), W.Down(-160.0, top + 8.0, 28.0, CLOAK_DARK)]),
                       turns=(115.0, 245.0))
    lock_3d = W.Mane([(-6.4, 7.0, -0.6), (-7.0, 12.0, 1.2), (-7.4, 17.0, 2.4), (-7.4, 22.0, 2.8)], 3.6, HAIR, HAIR_LIGHT, lead=0.5)
    # Her head from the front in the round: the hood as far back on her head
    # as her side views have it (Jon, 2026-10-25, of Furrier's hood and then
    # of hers: from the front it hid too much of the face). Her front rows
    # keep their own hood.
    def round_front_hood(d) -> None:
        K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, 20.0), K.at(-20.0, 20.0)], CLOAK)
        for sx in (-1.0, 1.0):
            K.poly(d, [K.at(8.6 * sx, -11.0), K.at(11.0 * sx, -3.0), K.at(9.6 * sx, 9.6), K.at(8.6 * sx, 9.6)], CLOAK_DARK)
        K.oval(d, K.at(0.0, 0.4), 7.6, 9.8, skin[0])
        ring = [K.at(7.8 * math.cos(math.radians(a)), 0.4 + 10.0 * math.sin(math.radians(a))) for a in range(-190, 11, 10)]
        K.line(d, ring, DRESS_LIGHT, 1.0)
        for sx in (-1.0, 1.0):
            K.poly(d, [K.at(x * 1.15 * sx, y - 1.4) for x, y in ((0.0, -7.6), (4.6, -6.4), (6.2, -1.0), (5.8, 7.0), (4.4, 2.0), (3.4, -3.6), (0.6, -5.0))], HAIR)
            K.line(d, [K.at(3.4 * sx, -7.4), K.at(5.8 * sx, -2.4), K.at(6.0 * sx, 5.0)], HAIR_LIGHT, 0.5)

    round_front = R.front_face(
        R.make_front_head(K, ("eve_round",), skin[0], skin[2], wide=7.4, jaw=5.8, chin=3.4, shape=front_hood_shape, hair=round_front_hood, face=front_nose),
        R.make_front_eyes(K, ("eve",), white=None, ink=INK, spread=3.0, y=-0.2, size=0.9, lash=0.5), R.make_front_brows(K, ("eve",), HAIR, spread=3.0, y=-3.4, width=0.7),
        R.make_front_mouth(K, ("eve",), y=7.4, colour=(140, 60, 76, 255), lips=(206, 112, 124, 255), wide=0.7))

    ROUNDS["eve"] = C.Round(
        "Eve", C.PersonBody(p, back_layers=("back",), mirror=("head",),
                            heads={"front": round_front, "side": lambda pose: [(side_head(), "head"), (side_eyes(str(pose["eyes"])), "eyes"), (side_brows(R.brow_mood(pose)), "brows"),
                                                         (side_mouth(str(pose["mouth"])), "mouth")]}),
        C.Look(
            # The hood: all of her head but her face, and a soft point behind.
            C.auto_head(p, head, eyes, hair=lambda u, v: ~((np.abs(u) < 50.0) & (v > -8.6)), hair_colour=CLOAK, hair_shade=CLOAK_DARK,
                        volumes=[hood_3d, ((0.0, -4.0, -9.6), (4.4, 5.0, 4.4))], lines=[edge]),
            C.auto_trunk(p, [W.Band(-14.6, -11.6, DRESS_DARK), W.Dot(0.0, -13.0, 1.4, GOLD), W.Dot(0.0, top + 3.0, 1.4, GOLD),
                             W.Path([(-40.0, top + 5.0), (0.0, -14.0), (40.0, -6.0)], STRAP, 0.75), W.Down(-25.0, -4.0, 30.0, DRESS_DARK, spread=8.0),
                             W.Down(0.0, -4.0, 30.0, DRESS_DARK), W.Down(25.0, -4.0, 30.0, DRESS_DARK, spread=8.0), W.Band(31.0, 36.0, DRESS_LIGHT)]),
            back_pieces=[cloak_3d], pieces=[("lock", lock_3d)]),
        # She listens: her near hand at her ear, as she stands in her idle
        # row (what she is); the other holds her elbow.
        C.Stance(hands={"r": C.Hand(at=(-10.2, -46.4, -0.6), pole=(-1.0, 0.3, 0.3), mode="flat"),
                        "l": C.Hand(at=(-2.0, -12.0, 7.0), pole=(1.0, 0.4, -0.4), mode="soft")},
                 stagger=1.6))
    _meta("eve", "Eve", ["hub", "peaceful", "cryptography_crew", "eavesdropper"],
          "Eve is the conventional passive eavesdropper in cryptography examples, turned into a quiet character who listens without changing the "
          "channel. Her name comes from eavesdropping, not from a specific historical woman; the characterization should make observation itself "
          "feel invasive.",
          "Use as a stealth observer, information broker, surveillance antagonist, or tutorial for confidentiality. Eve should learn from proximity "
          "and intercepted traffic while leaving little evidence that she was present.",
          ["I don't change anything — I only listen.", "A perfect eavesdropper leaves the conversation exactly as loud as she found it.",
           "The whole art of secrecy exists because of people like me."])


# =============================================================================
# Judy: the judge. Stories crack along their seams, and she finds the seam.
# =============================================================================


def _judy() -> None:
    # A stout woman, not young, short, with a round face: the weight of the
    # court is in how she stands.
    p = _person("judy", 163.0, girth=1.6, woman=True, legs=-2.0)
    K, P = p.K, p.P
    skin = BROWN
    ROBE, ROBE_DARK, ROBE_LIGHT = (48, 44, 62, 255), (28, 26, 40, 255), (92, 88, 114, 255)
    STOLE, STOLE_DARK, WIG, WIG_DARK, LACE = (178, 48, 58, 255), (118, 30, 44, 255), (242, 240, 232, 255), (176, 178, 190, 255), (250, 248, 242, 255)
    top = p.b.neck[1] - 2.0

    def front(d, hb, hf) -> None:
        # The red of her office down each side of her front, and lace at her neck.
        for x0, x1 in ((-3.4, 0.2), (8.0, 11.0)):
            K.poly(d, [K.at(x0, top + 1.0), K.at(x1, top + 1.0), K.at(x1 * 1.25 + hf * 0.5, 48.0), K.at(x0 * 1.25 + hf * 0.3, 48.0)], STOLE)
        K.poly(d, [K.at(0.8, top - 1.0), K.at(8.4, top - 1.0), K.at(7.4, top + 11.0), K.at(4.6, top + 13.0), K.at(1.8, top + 11.0)], LACE)
        for y in (top + 3.0, top + 6.5, top + 10.0):
            K.line(d, [K.at(1.6, y), K.at(4.6, y + 1.2), K.at(7.6, y)], WIG_DARK, 0.5)
        for x in (-8.6,):
            K.line(d, [K.at(x, 2.0), K.at(x - 2.0 - hb * 0.4, 40.0)], ROBE_LIGHT, 0.6)

    p.torso = R.make_figure(K, ("judy",), ROBE, ROBE_DARK, back=(9.2, 10.2, 9.4, 11.6, 14.6), front=(8.4, 12.6, 10.8, 12.4, 14.2), hem_y=p.b.hip_up - 5.0, top=top,
                            shoulders=((-5.8, p.b.near_shoulder[1] + 0.8), (6.4, p.b.far_shoulder[1] + 0.6)), shoulder_r=(5.4, 5.0), waist_y=-11.0,
                            neck=(-3.8, 4.0), shade_from=40.0, detail=front)
    _dress(p, skin, ROBE, ROBE_DARK, ROBE, ROBE_DARK, (44, 36, 44, 255), (22, 18, 26, 255), cuff=LACE, arm=(8.4, 8.2, 8.4), legs=(7.0, 5.8, 5.0), hand=0.95,
           neck=5.0)

    def wig_shape(d) -> None:
        # The wig of a court: rolls of white curl down to her shoulders.
        K.oval(d, K.at(-1.4, -4.6), 10.6, 9.8, WHITE)
        for x, y, r in ((-9.0, 2.0, 3.6), (-8.6, 7.2, 3.4), (-7.0, 12.0, 3.2), (-2.6, 11.4, 2.8)):
            K.oval(d, K.at(x, y), r, r * 0.9, WHITE)

    def wig(d) -> None:
        K.poly(d, [K.at(20.0, -8.0), K.at(8.8, -8.0), K.at(5.0, -8.8), K.at(1.4, -7.6), K.at(-1.6, -5.0), K.at(-2.6, -1.0), K.at(-2.2, 4.0), K.at(-1.0, 8.0),
                   K.at(-0.4, 20.0), K.at(-20.0, 20.0), K.at(-20.0, -26.0), K.at(20.0, -26.0)], WIG)
        for x, y, r in ((-9.0, 2.0, 2.6), (-8.6, 7.2, 2.4), (-7.0, 12.0, 2.2), (-2.8, 11.4, 1.9), (-6.4, -4.0, 2.6), (-2.2, -9.4, 2.4), (3.4, -10.8, 2.2)):
            K.oval(d, K.at(x, y), r, r * 0.85, None, WIG_DARK, 0.6)  # type: ignore[arg-type]

    def over(d) -> None:
        # A full cheek, and a second line under her chin.
        K.line(d, [K.at(-0.4, 3.0), K.at(0.8, 6.0)], mix(skin[0], skin[2], 0.45), 0.5)
        K.line(d, [K.at(1.0, 10.6), K.at(4.4, 11.6), K.at(7.4, 10.4)], mix(skin[0], skin[2], 0.5), 0.5)
        K.oval(d, K.at(-2.8, 5.6), 0.9, 1.1, GOLD)

    def glasses():
        def paint(d) -> None:
            for cx, rx in ((2.0, 2.6), (7.4, 2.0)):
                K.rrect(d, K.home[0] + cx - rx, K.home[1] - 2.2, K.home[0] + cx + rx, K.home[1] + 1.2, 0.8, (236, 244, 250, 120), GOLD_DARK, 0.6)
            K.line(d, [K.at(4.6, -0.8), K.at(5.4, -0.8)], GOLD_DARK, 0.6)

        return K.piece(("judy_glasses",), paint)

    head = R.make_head(K, ("judy",), *skin, skull=(0.0, -2.0, 8.2, 8.6), jaw=(2.2, 3.8, 6.6, 6.8), nose=((7.6, 0.6), (9.8, 3.0), (9.6, 4.2), (7.6, 4.4)),
                       ear=None, shape=wig_shape, under=wig, over=over)
    eyes = R.make_eyes(K, (2.0, -0.6), (7.4, -0.8), ink=INK, iris=(64, 38, 30, 255), size=0.9, lash=0.4)
    _face(p, head, eyes,
          R.make_brows(K, [(-0.2, -4.0), (2.0, -4.8), (4.4, -4.0)], [(5.8, -4.2), (7.4, -4.8), (8.8, -4.2)], (60, 50, 54, 255), 1.0),
          R.make_mouth(K, (5.8, 7.0), (110, 34, 44, 255), wide=0.85, lips=(168, 54, 62, 255)), glasses)

    # ---- From the front: the wig of the court round her face, the red of
    # her office down each side of her front, lace at her neck, her glasses.
    sy = p.b.near_shoulder[1] + 0.8
    hem = p.b.hip_up - 5.0

    def front_robe(d) -> None:
        for sx in (-1.0, 1.0):
            K.poly(d, [K.at(3.6 * sx, top + 1.0), K.at(6.8 * sx, top + 1.0), K.at(8.6 * sx, hem + 4.0), K.at(4.6 * sx, hem + 4.0)], STOLE)
            K.line(d, [K.at(6.8 * sx, top + 1.0), K.at(8.6 * sx, hem + 4.0)], STOLE_DARK, 0.6)
            K.line(d, [K.at(11.0 * sx, 2.0), K.at(12.6 * sx, hem - 4.0)], ROBE_LIGHT, 0.6)
        K.poly(d, [K.at(-3.6, top - 1.0), K.at(3.6, top - 1.0), K.at(2.8, top + 11.0), K.at(0.0, top + 13.0), K.at(-2.8, top + 11.0)], LACE)
        for y in (top + 3.0, top + 6.5, top + 10.0):
            K.line(d, [K.at(-2.8, y), K.at(0.0, y + 1.2), K.at(2.8, y)], WIG_DARK, 0.5)

    def front_wig_shape(d) -> None:
        K.oval(d, K.at(0.0, -4.6), 10.6, 9.6, WHITE)
        for sx in (-1.0, 1.0):
            for x, y, r in ((9.2, 2.0, 3.4), (9.0, 7.2, 3.2), (8.0, 12.0, 3.0)):
                K.oval(d, K.at(x * sx, y), r, r * 0.9, WHITE)

    def front_wig(d) -> None:
        K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, 20.0), K.at(6.6, 20.0), K.at(6.6, 3.0), K.at(7.0, -3.0), K.at(4.6, -6.8), K.at(0.0, -7.6), K.at(-4.6, -6.8),
                   K.at(-7.0, -3.0), K.at(-6.6, 3.0), K.at(-6.6, 20.0), K.at(-20.0, 20.0)], WIG)
        for sx in (-1.0, 1.0):
            for x, y, r in ((9.2, 2.0, 2.5), (9.0, 7.2, 2.3), (8.0, 12.0, 2.1), (6.6, -5.0, 2.5), (2.6, -9.6, 2.3)):
                K.oval(d, K.at(x * sx, y), r, r * 0.85, None, WIG_DARK, 0.6)  # type: ignore[arg-type]

    def front_judge(d) -> None:
        for sx in (-1.0, 1.0):
            K.rrect(d, K.home[0] + 3.4 * sx - 2.5, K.home[1] - 2.4, K.home[0] + 3.4 * sx + 2.5, K.home[1] + 1.0, 0.8, (236, 244, 250, 120), GOLD_DARK, 0.6)
        K.line(d, [K.at(-0.9, -1.0), K.at(0.9, -1.0)], GOLD_DARK, 0.6)
        K.line(d, [K.at(-0.3, 1.0), K.at(-1.4, 3.6), K.at(0.0, 4.4), K.at(1.4, 3.6)], skin[2], 0.6)
        K.line(d, [K.at(-3.6, 11.0), K.at(0.0, 11.8), K.at(3.6, 11.0)], mix(skin[0], skin[2], 0.5), 0.5)

    p.front_torso = R.make_front_torso(K, ("judy",), ROBE, ROBE_DARK, [(top, 4.2), (top + 3.6, 9.4), (top + 12.5, 11.6), (-11.0, 10.6), (0.0, 12.2), (hem, 14.6)],
                                       shoulder=(7.4, sy, 5.0, 5.2), detail=front_robe)
    p.front_head_layers = R.front_face(
        R.make_front_head(K, ("judy",), skin[0], skin[2], wide=8.0, jaw=7.2, chin=3.4, shape=front_wig_shape, hair=front_wig, face=front_judge),
        R.make_front_eyes(K, ("judy",), ink=INK, iris=(64, 38, 30, 255), spread=3.4, y=-0.8, size=0.85, lash=0.4),
        R.make_front_brows(K, ("judy",), (60, 50, 54, 255), spread=3.4, y=-4.2, width=1.0),
        R.make_front_mouth(K, ("judy",), y=7.6, colour=(110, 34, 44, 255), lips=(168, 54, 62, 255), wide=0.85))
    p.front_shoe = R.make_front_shoe(K, (44, 36, 44, 255), (22, 18, 26, 255), p.b.ankle_up)
    p.front_span = (9.0, 5.0)
    R.add_front_rows(p)

    #: Her hands one on the other, in front of her.
    held_near, held_far = (7.0, 13.0), (-1.0, 22.0)
    p.set_rest(na=held_near, fa=held_far, nh="flat", mouth="flat", brows=-1.0, lean=-2.0)

    @p.row
    def idle(i: int, n: int):
        # She hears both sides, and looks at each over her glasses.
        _, s, c = loop(i, n)
        return P(hip=(0.0, 0.3 + 0.3 * s), head=(0.3 * c, 0.0, 5.0 + 4.0 * c), eyes="closed" if i == n - 2 else "up" if c < -0.5 else "open",
                 brows=-1.0 if c > 0.0 else 1.0)

    _walk(p, held_near, held_far, reach=6.0, lift=3.0, lean=0.0, nh="flat")

    @p.row
    def talk(i: int, n: int):
        # One finger: this, and then this.
        _, s, _c = loop(i, n)
        return P(hip=(0.0, 0.3 * s), head=(0.3, 0.0, 2.0 * s), na=(13.0, 2.0 - 4.0 * max(0.0, s)), nh="point", mouth=("open", "flat", "o", "flat")[i % 4],
                 brows=-1.0 if s < 0.0 else 1.0)

    @p.row
    def interact(i: int, n: int):
        # The gavel comes down.
        up = P(lean=-4.0, na=(8.0, -20.0), nab=-1.0, arm="under", nh="fist", brows=-1.0)
        down = P(hip=(1.0, 2.0), lean=8.0, na=(21.0, 10.0), nh="fist", mouth="flat", brows=-1.0)
        return p.keys(shot(i, n), [(0.0, P()), (0.3, up), (0.5, down), (0.8, down), (1.0, P())])

    def gavel():
        def shape(d) -> None:
            K.stroke(d, [K.at(0.0, 0.0), K.at(0.0, -13.0)], WHITE, 1.8)
            K.rrect(d, K.home[0] - 5.4, K.home[1] - 17.6, K.home[0] + 5.4, K.home[1] - 11.4, 1.4, WHITE)

        return K.solid(("gavel",), shape, (150, 98, 58, 255), lambda d: K.line(d, [K.at(-3.0, -17.6), K.at(-3.0, -11.4)], GOLD, 0.8), outline=1.0, rim=0.3,
                       shade=0.4, shade_colour=(92, 56, 40, 255))

    def effects(ctx) -> List[Stamp]:
        out: List[Stamp] = []
        if ctx.anim == "interact" and 0.2 <= ctx.u <= 0.9:
            turn = math.degrees(math.atan2(ctx.hand[1] - ctx.elbow[1], ctx.hand[0] - ctx.elbow[0])) + 90.0
            out.append((gavel(), ctx.hand, "gavel", turn))
            if 0.5 <= ctx.u <= 0.7:
                out.append((R.burst(K, 8.0, GOLD, GOLD_DARK), (ctx.hand[0] + 15.0, ctx.hand[1] + 9.0), "burst", 0.0))
        return out

    p.effects = effects

    # ---- In the round: her head from the side drawn as the cast draws a
    # head in the numbers of a profile (the wig and its curls down behind,
    # one lens and its arm, the second line under her chin); the wig in 3D
    # as a mass and rolls of curl each side and behind; her robe from the
    # numbers of her makers, with the red of her office and the lace.
    def side_wig_shape(d) -> None:
        K.oval(d, K.at(-2.0, -4.6), 11.0, 9.8, WHITE)
        for x, y, r in ((-10.0, 2.0, 3.6), (-9.6, 7.2, 3.4), (-8.0, 12.0, 3.2), (-3.6, 11.4, 2.8)):
            K.oval(d, K.at(x, y), r, r * 0.9, WHITE)

    def side_wig(d) -> None:
        K.poly(d, [K.at(20.0, -8.0), K.at(9.6, -8.0), K.at(5.8, -8.8), K.at(2.2, -7.6), K.at(0.4, -5.0), K.at(-0.4, -1.0), K.at(0.0, 4.0), K.at(0.8, 8.0),
                   K.at(1.2, 20.0), K.at(-20.0, 20.0), K.at(-20.0, -26.0), K.at(20.0, -26.0)], WIG)
        for x, y, r in ((-10.0, 2.0, 2.6), (-9.6, 7.2, 2.4), (-8.0, 12.0, 2.2), (-3.8, 11.4, 1.9), (-7.4, -4.0, 2.6), (-3.0, -9.4, 2.4), (2.8, -10.8, 2.2),
                        (-3.2, 3.0, 2.2)):
            K.oval(d, K.at(x, y), r, r * 0.85, None, WIG_DARK, 0.6)  # type: ignore[arg-type]

    def side_over(d) -> None:
        K.line(d, [K.at(2.6, 10.6), K.at(5.6, 11.6), K.at(8.4, 10.4)], mix(skin[0], skin[2], 0.5), 0.5)
        K.line(d, [K.at(3.6, 3.0), K.at(4.8, 6.0)], mix(skin[0], skin[2], 0.45), 0.5)
        K.oval(d, K.at(1.4, 6.0), 0.9, 1.1, GOLD)

    def side_glasses():
        # One lens and the arm of her glasses back into her wig.
        def paint(d) -> None:
            K.rrect(d, K.home[0] + 5.0, K.home[1] - 2.2, K.home[0] + 8.4, K.home[1] + 1.2, 0.8, (236, 244, 250, 120), GOLD_DARK, 0.6)
            K.line(d, [K.at(5.0, -0.8), K.at(0.2, -1.2)], GOLD_DARK, 0.6)

        return K.piece(("judy_side_glasses",), paint)

    side_head = R.make_head(K, ("judy_side",), *skin, skull=(0.0, -2.0, 9.2, 8.6), jaw=(3.0, 3.8, 7.0, 6.8), nose=((8.2, 0.6), (10.4, 3.0), (10.2, 4.2), (8.2, 4.4)),
                            ear=None, shape=side_wig_shape, under=side_wig, over=side_over, far_shade=False)
    side_eyes = R.make_eyes(K, (6.6, -0.6), None, ink=INK, iris=(64, 38, 30, 255), size=0.9, lash=0.4)
    side_brows = R.make_brows(K, [(4.6, -4.2), (6.6, -4.8), (8.8, -4.2)], None, (60, 50, 54, 255), 1.0)
    side_mouth = R.make_mouth(K, (8.0, 7.0), (110, 34, 44, 255), wide=0.6, lips=(168, 54, 62, 255))

    wig_3d = ((0.0, -4.6, -1.4), (10.4, 9.6, 9.8))
    curls = ([((sx * x, y, -1.0), (r, r * 0.9, r)) for sx in (-1.0, 1.0) for x, y, r in ((9.4, 2.0, 3.6), (9.2, 7.2, 3.4), (8.2, 12.0, 3.2))]
             + [((x, y, -7.6), (3.6, 3.4, 3.2)) for x, y in ((-5.2, 3.0), (0.4, 2.2), (5.6, 3.4), (-2.6, 9.0), (3.0, 8.4))])

    def curl(centre, radii):
        # The dark ring of a curl, on its outside.
        out = np.array([centre[0], 0.0, centre[2] + 4.0])
        out /= np.linalg.norm(out)
        return O.circle(tuple(np.asarray(centre) + out * 0.8 * radii[0]), tuple(out), radii[0] * 0.55, WIG_DARK, 0.6, slack=1.0)

    # Her head from the front in the round: her glasses over her eyes, as
    # they are in her three-quarter view (her front rows paint the lenses
    # under her eyes, so her eyes look dark and wide there).
    def round_front_face(d) -> None:
        K.line(d, [K.at(-0.3, 1.0), K.at(-1.4, 3.6), K.at(0.0, 4.4), K.at(1.4, 3.6)], skin[2], 0.6)
        K.line(d, [K.at(-3.6, 11.0), K.at(0.0, 11.8), K.at(3.6, 11.0)], mix(skin[0], skin[2], 0.5), 0.5)

    def front_glasses():
        def paint(d) -> None:
            for sx in (-1.0, 1.0):
                K.rrect(d, K.home[0] + 3.4 * sx - 2.5, K.home[1] - 2.4, K.home[0] + 3.4 * sx + 2.5, K.home[1] + 1.0, 0.8, (236, 244, 250, 120), GOLD_DARK, 0.6)
            K.line(d, [K.at(-0.9, -1.0), K.at(0.9, -1.0)], GOLD_DARK, 0.6)

        return K.piece(("judy_front_glasses",), paint)

    round_front = R.front_face(
        R.make_front_head(K, ("judy_round",), skin[0], skin[2], wide=8.0, jaw=7.2, chin=3.4, shape=front_wig_shape, hair=front_wig, face=round_front_face),
        R.make_front_eyes(K, ("judy",), ink=INK, iris=(64, 38, 30, 255), spread=3.4, y=-0.8, size=0.85, lash=0.4),
        R.make_front_brows(K, ("judy",), (60, 50, 54, 255), spread=3.4, y=-4.2, width=1.0),
        R.make_front_mouth(K, ("judy",), y=7.6, colour=(110, 34, 44, 255), lips=(168, 54, 62, 255), wide=0.85), extra=[(front_glasses, "glasses")])

    ROUNDS["judy"] = C.Round(
        "Judy", C.PersonBody(p, heads={"front": round_front, "side": lambda pose: [(side_head(), "head"), (side_eyes(str(pose["eyes"])), "eyes"),
                                                             (side_brows(R.brow_mood(pose)), "brows"), (side_mouth(str(pose["mouth"])), "mouth"),
                                                             (side_glasses(), "glasses")]}),
        C.Look(
            C.auto_head(p, head, eyes, hair=lambda u, v: (v < -7.6 + 1.6 * np.clip(np.abs(u) / 60.0, 0.0, 1.0)) | (np.abs(u) > 58.0),
                        hair_colour=WIG, hair_shade=WIG_DARK, volumes=[wig_3d] + curls, lines=[curl(c, r) for c, r in curls]),
            C.auto_trunk(p, [W.Strip(27.0, top + 1.0, hem + 4.0, 1.6, STOLE, flare=0.9), W.Strip(-27.0, top + 1.0, hem + 4.0, 1.6, STOLE, flare=0.9),
                             W.Strip(0.0, top - 1.0, top + 13.0, 3.6, LACE, flare=-3.6), W.Down(60.0, 2.0, hem - 4.0, ROBE_LIGHT),
                             W.Down(-60.0, 2.0, hem - 4.0, ROBE_LIGHT), W.Down(180.0, top + 4.0, hem, ROBE_DARK)])),
        # Her hands one on the other, in front of her.
        C.Stance(hands={"r": C.Hand(l=-1.0, pole=(-0.8, 0.2, -0.6)), "l": C.Hand(l=2.0, pole=(0.8, 0.2, -0.6))}, stagger=1.4))

    _meta("judy", "Judy", ["hub", "peaceful", "cryptography_crew", "judge"],
          "Judy is the judge or adjudicator role used in cryptographic protocol stories. She personifies the neutral party asked to decide which "
          "claimant, signature, transcript, or story is authentic when other participants disagree.",
          "Use as an arbiter, courtroom NPC, dispute-resolution mechanic, or truth-testing boss. She should compare evidence, reveal contradictions, "
          "and force stories to expose the seams where they fail to agree.",
          ["Someone has to decide who's telling the truth.", "Stories crack along their seams.", "That's the difference between a judge and a critic."])


# =============================================================================
# Mallory: the one in the middle. Eve listens. Mallory edits.
# =============================================================================


def _mallory() -> None:
    # A tall, lean woman, and she is the villain of the crew: hard in the
    # face, plain in her dress. Jon, 2026-10-13: "very light lashes and no
    # lips. Just modest curves. She's a baddy." and "Not a Femme Fatale."
    # And, of the first draft of this one: her nose was too large, and she
    # "needs more steampunk accessories sort of like the original": so she has
    # the listening piece at her ear, the braid bound in brass like a cable,
    # the two crossed straps with a red clasp, rivets, and a buckled belt.
    p = _person("mallory", 175.0, woman=True, legs=1.5)
    K, P = p.K, p.P
    skin = PALE
    COAT, COAT_DARK, COAT_LIGHT = (44, 42, 56, 255), (24, 22, 34, 255), (84, 82, 106, 255)
    LINING, LINING_DARK, HAIR, HAIR_DARK = (190, 46, 54, 255), (124, 28, 44, 255), (164, 44, 50, 255), (104, 26, 40, 255)
    TEAL, BOOT, GLOVE = (58, 170, 176, 255), (30, 28, 38, 255), (30, 28, 38, 255)
    BRASS, BRASS_DARK, STEEL = (222, 176, 84, 255), (150, 104, 48, 255), (170, 176, 190, 255)
    top = p.b.neck[1] - 2.0

    def front(d, hb, hf) -> None:
        # A long coat, shut to its high collar; two straps cross on her chest
        # (one teal, one brass-yellow) under a red clasp; a belt with a brass
        # buckle and a pouch; rivets; and the red lining where the skirt of
        # the coat opens as she moves.
        K.line(d, [K.at(-7.0, top + 5.0), K.at(8.4, -15.0)], TEAL, 1.7)
        K.line(d, [K.at(8.0, top + 5.0), K.at(-6.4, -15.0)], BRASS, 1.5)
        K.oval(d, K.at(1.2, top + 14.6), 2.0, 2.0, LINING, OUTLINE, 0.5)
        K.oval(d, K.at(1.2, top + 14.6), 0.8, 0.8, BRASS)
        for x, y in ((-5.6, top + 9.0), (6.2, top + 9.6), (-5.0, -18.0), (6.4, -17.4)):
            K.oval(d, K.at(x, y), 0.7, 0.7, STEEL)
        K.poly(d, [K.at(-9.0, -14.8), K.at(9.0, -14.0), K.at(9.0, -11.2), K.at(-9.0, -12.0)], (60, 54, 62, 255))
        K.rrect(d, K.home[0] + 1.6, K.home[1] - 15.4, K.home[0] + 5.6, K.home[1] - 10.6, 0.5, BRASS, OUTLINE, 0.5)
        K.rrect(d, K.home[0] - 7.0, K.home[1] - 11.0, K.home[0] - 3.0, K.home[1] - 5.6, 0.8, (70, 60, 66, 255), OUTLINE, 0.5)
        K.oval(d, K.at(-5.0, -9.6), 0.6, 0.6, BRASS)
        K.poly(d, [K.at(4.6, -11.0), K.at(6.4 + hf * 0.9, 30.0), K.at(3.4 + hf * 0.4, 30.0)], LINING)
        K.line(d, [K.at(4.6, -11.0), K.at(3.4 + hf * 0.4, 28.0)], LINING_DARK, 0.6)
        K.poly(d, [K.at(0.6, top - 1.0), K.at(7.6, top - 1.0), K.at(7.2, top + 3.4), K.at(1.0, top + 3.4)], COAT_DARK)

    p.torso = R.make_figure(K, ("mallory",), COAT, COAT_DARK, back=(7.6, 7.6, 6.2, 7.8, 10.6), front=(6.8, 8.2, 6.4, 8.0, 10.2), hem_y=26.0, top=top,
                            shoulders=((-5.0, p.b.near_shoulder[1] + 0.6), (5.8, p.b.far_shoulder[1] + 0.4)), shoulder_r=(4.8, 4.4), shade_from=6.6,
                            detail=front)
    _dress(p, (GLOVE, (18, 16, 24, 255), (18, 16, 24, 255)), COAT, COAT_DARK, (56, 54, 70, 255), (36, 34, 50, 255), BOOT, (14, 12, 20, 255), cuff=LINING,
           arm=(6.0, 5.2, 4.6), legs=(6.6, 5.4, 4.8), hand=0.9, boot_from=0.35, neck=4.0)
    p.neck = R.make_neck(K, skin[1], 4.0)

    def hair_shape(d) -> None:
        K.oval(d, K.at(-1.0, -4.4), 8.8, 8.6, WHITE)
        # It stands up in a hard peak over her brow.
        K.poly(d, [K.at(-6.0, -9.0), K.at(-2.0, -14.6), K.at(7.6, -14.0), K.at(9.6, -10.0), K.at(6.0, -8.0)], WHITE)

    def hair(d) -> None:
        # Dark red, pulled back hard from her brow to the braid.
        K.poly(d, [K.at(20.0, -9.6), K.at(7.6, -9.6), K.at(3.6, -8.0), K.at(0.4, -5.6), K.at(-2.4, -3.4), K.at(-3.6, -1.6), K.at(-6.0, -1.4), K.at(-6.6, 3.4),
                   K.at(-5.0, 4.6), K.at(-4.6, 6.6), K.at(-20.0, 6.6), K.at(-20.0, -26.0), K.at(20.0, -26.0)], HAIR)
        for strand in ([(6.6, -10.4), (0.0, -8.6), (-6.0, -3.6)], [(3.0, -11.8), (-4.0, -9.6), (-8.0, -4.0)], [(-6.0, -1.0), (-8.4, 1.6)]):
            K.line(d, [K.at(x, y) for x, y in strand], HAIR_DARK, 0.6)

    def over(d) -> None:
        # A hard cheek, and the piece she listens with: brass, over her ear,
        # with a short arm toward her mouth.
        K.line(d, [K.at(0.4, 2.6), K.at(2.4, 6.4)], mix(skin[0], skin[2], 0.5), 0.5)
        K.line(d, [K.at(-4.6, 1.6), K.at(-1.0, 5.6), K.at(1.6, 6.4)], STEEL, 0.8)
        K.oval(d, K.at(-4.8, 1.0), 2.5, 2.9, BRASS, OUTLINE, 0.6)
        K.oval(d, K.at(-4.8, 1.0), 1.1, 1.3, BRASS_DARK)
        K.line(d, [K.at(-5.6, -1.8), K.at(-4.4, -6.4)], STEEL, 0.8)

    head = R.make_head(K, ("mallory",), *skin, skull=(0.0, -2.4, 7.6, 8.8), jaw=(2.6, 4.0, 5.0, 7.2), nose=((7.2, 0.8), (8.6, 3.0), (8.2, 3.8), (7.2, 4.0)),
                       ear=None, shape=hair_shape, under=hair, over=over)
    eyes = R.make_eyes(K, (1.6, -0.4), (7.2, -0.6), ink=INK, iris=(70, 140, 130, 255), size=0.85, lash=0.25)
    _face(p, head, eyes,
          R.make_brows(K, [(-0.8, -4.2), (1.8, -4.4), (4.6, -3.2)], [(5.8, -3.4), (7.2, -4.4), (8.6, -4.2)], (92, 40, 38, 255), 0.9),
          R.make_mouth(K, (5.6, 7.6), (120, 52, 56, 255), wide=0.8))

    def braid(ctx) -> List[Stamp]:
        # Her braid hangs in the world from the back of her head.
        a = math.radians(ctx.turn)
        back = (ctx.head[0] - 7.0 * math.cos(a) + 1.0 * math.sin(a), ctx.head[1] - 7.0 * math.sin(a) - 1.0 * math.cos(a))
        at = pin(back)
        moving = ctx.anim == "walk"
        ch = R.chain((back[0] - at[0], back[1] - at[1]), 8, 5.0, 112.0 if moving else 96.0, wave=9.0 if moving else 3.0, curl=-2.0, phase=ctx.phase)
        ch = tuple((round(x, 1), round(y, 1)) for x, y in ch)

        def paint(d) -> None:
            pts = [K.at(x, y) for x, y in ch]
            K.stroke(d, pts, OUTLINE, 5.0 + 2.4)
            K.stroke(d, pts, HAIR, 5.0)
            # A brass band at each second link, and a brass end.
            for k in range(1, len(pts), 2):
                K.oval(d, pts[k], 2.9, 2.9, BRASS_DARK)
                K.oval(d, pts[k], 2.0, 2.0, BRASS)
            K.oval(d, pts[-1], 3.2, 3.2, OUTLINE)
            K.oval(d, pts[-1], 2.2, 2.2, STEEL)

        return [(K.aligned(("mallory_braid", ch), paint), at, "braid", 0.0)]

    p.layers["back"].append(braid)

    # ---- From the front: the same coat, straps and clasp; the peak of her
    # hair is in the middle, and the listening piece is at one ear.
    sy = p.b.near_shoulder[1] + 0.6

    def front_coat(d) -> None:
        K.poly(d, [K.at(-3.6, top - 1.0), K.at(3.6, top - 1.0), K.at(3.4, top + 3.4), K.at(-3.4, top + 3.4)], COAT_DARK)
        K.line(d, [K.at(-7.0, top + 5.0), K.at(7.0, -15.0)], TEAL, 1.7)
        K.line(d, [K.at(7.0, top + 5.0), K.at(-7.0, -15.0)], BRASS, 1.5)
        K.oval(d, K.at(0.0, top + 14.6), 2.0, 2.0, LINING, OUTLINE, 0.5)
        K.oval(d, K.at(0.0, top + 14.6), 0.8, 0.8, BRASS)
        for x, y in ((-6.0, top + 9.0), (6.0, top + 9.0), (-5.6, -18.0), (5.6, -18.0)):
            K.oval(d, K.at(x, y), 0.7, 0.7, STEEL)
        K.poly(d, [K.at(-9.0, -14.6), K.at(9.0, -14.6), K.at(9.0, -11.6), K.at(-9.0, -11.6)], (60, 54, 62, 255))
        K.rrect(d, K.home[0] - 2.0, K.home[1] - 15.4, K.home[0] + 2.0, K.home[1] - 10.8, 0.5, BRASS, OUTLINE, 0.5)
        K.rrect(d, K.home[0] - 7.4, K.home[1] - 11.0, K.home[0] - 3.6, K.home[1] - 5.6, 0.8, (70, 60, 66, 255), OUTLINE, 0.5)
        K.poly(d, [K.at(-0.8, -10.6), K.at(0.8, -10.6), K.at(2.6, 26.0), K.at(-2.6, 26.0)], LINING)
        K.line(d, [K.at(0.0, -10.6), K.at(0.0, 26.0)], LINING_DARK, 0.6)

    # Her face from the front is the face of the side view (Jon, 2026-10-13:
    # "Her face looks weird and not like the side view"): her hair pulled back
    # hard from her brow, with its crest over it, and not a hood round her
    # face; her eyes under thin brows; one hard line in each cheek. It is as
    # wide as it was: a thinner face was worse (Jon, the same day).
    def front_hair_shape(d) -> None:
        # Wider than her head: it is thick, and it goes back over her ears.
        K.oval(d, K.at(0.0, -5.0), 9.6, 8.4, WHITE)
        K.poly(d, [K.at(-8.0, -9.6), K.at(-3.6, -15.6), K.at(4.4, -15.2), K.at(9.0, -11.0), K.at(8.2, -7.6)], WHITE)
        K.oval(d, K.at(-8.8, 0.8), 2.8, 3.2, WHITE)

    def front_hair(d) -> None:
        K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, 3.4), K.at(6.4, 3.4), K.at(6.6, -1.0), K.at(6.2, -4.8), K.at(3.6, -7.2), K.at(0.4, -7.8),
                   K.at(-3.4, -6.8), K.at(-6.2, -4.4), K.at(-6.6, -1.0), K.at(-6.4, 3.4), K.at(-20.0, 3.4)], HAIR)
        # It goes back and up from her brow: the lines of the comb.
        for strand in ([(-4.6, -6.4), (-2.6, -11.6), (2.6, -13.8)], [(-0.6, -7.8), (2.4, -11.4), (6.0, -11.6)], [(3.4, -7.4), (7.0, -8.8)], [(-7.4, -1.0), (-8.2, -6.6)],
                       [(7.4, -1.0), (8.4, -6.0)]):
            K.line(d, [K.at(x, y) for x, y in strand], HAIR_DARK, 0.6)

    def front_marks(d) -> None:
        K.line(d, [K.at(-0.2, 0.6), K.at(-0.7, 3.2), K.at(0.0, 3.8), K.at(0.7, 3.2)], skin[2], 0.5)
        for sx in (-1.0, 1.0):
            K.line(d, [K.at(5.0 * sx, 2.6), K.at(3.8 * sx, 6.6)], mix(skin[0], skin[2], 0.5), 0.5)
        # The piece she listens with, at one ear: brass, with its arm to her mouth.
        K.line(d, [K.at(-8.4, 1.8), K.at(-5.2, 6.8), K.at(-2.6, 7.8)], STEEL, 0.8)
        K.oval(d, K.at(-8.6, 0.8), 2.2, 2.7, BRASS, OUTLINE, 0.6)
        K.oval(d, K.at(-8.6, 0.8), 0.9, 1.2, BRASS_DARK)
        K.line(d, [K.at(-9.0, -1.8), K.at(-8.6, -6.6)], STEEL, 0.8)

    def front_braid(hip) -> List[Stamp]:
        """Her braid from the front. It is not right behind her, where it
        could not be seen: it comes off the back of her head to one side and
        lies out past her shoulder (Jon, 2026-10-13: a front view is not a
        strict face-on projection; "a few features (e.g. the ponytail) off to
        one side a bit" give the character depth). Her shoulder is in front
        of most of it."""
        head_y = p.b.neck[1] + p.b.head_up[1]
        # A little to one side, and not more: far out it was "unnatural".
        pts = [(4.0, head_y - 2.0), (8.0, head_y + 5.0), (9.6, head_y + 13.0), (10.4, head_y + 22.0), (9.8, head_y + 31.0), (10.6, head_y + 39.0)]

        def paint(d) -> None:
            line = [K.at(x, y) for x, y in pts]
            K.stroke(d, line, OUTLINE, 4.6 + 2.4)
            K.stroke(d, line, HAIR, 4.6)
            for k in (2, 3, 4):
                K.oval(d, line[k], 2.8, 2.8, BRASS_DARK)
                K.oval(d, line[k], 1.9, 1.9, BRASS)
            K.oval(d, line[-1], 3.1, 3.1, OUTLINE)
            K.oval(d, line[-1], 2.1, 2.1, STEEL)

        return [(K.piece(("mallory_front_braid",), paint), hip, "front_braid", 0.0)]

    p.front_behind = front_braid

    p.front_torso = R.make_front_torso(K, ("mallory",), COAT, COAT_DARK, [(top, 3.4), (top + 3.6, 7.4), (top + 12.5, 8.0), (-13.0, 6.2), (0.0, 7.8), (26.0, 10.4)],
                                       shoulder=(5.8, sy, 4.2, 4.6), detail=front_coat)
    p.front_head_layers = R.front_face(
        R.make_front_head(K, ("mallory",), skin[0], skin[2], wide=7.4, jaw=5.8, chin=4.2, shape=front_hair_shape, hair=front_hair, face=front_marks),
        R.make_front_eyes(K, ("mallory",), ink=INK, iris=(70, 140, 130, 255), spread=3.2, y=-0.4, size=0.85, lash=0.4),
        R.make_front_brows(K, ("mallory",), (92, 40, 38, 255), spread=3.2, y=-3.6, width=0.9), R.make_front_mouth(K, ("mallory",), y=8.0, colour=(128, 78, 78, 255), wide=0.6))
    p.front_shoe = R.make_front_shoe(K, BOOT, (14, 12, 20, 255), p.b.ankle_up, wide=0.9)
    # Her arms are out from her trunk a little (Jon: "too tucked into the torso").
    p.front_span = (8.6, 4.2)

    @p.front_row
    def front(i: int, n: int):
        # Her arms folded, and she looks at you from under her brows.
        _, s, c = loop(i, n)
        return R.FP(hip=(0.0, 0.3 + 0.3 * s), head=(0.3 * c, 0.0, 2.0 * c), la=(-9.0, 12.0), ra=(-9.0, 13.5), lz=0.5, rz=0.5, lh="fist", rh="fist",
                    eyes="closed" if i == n - 2 else "open", brows=-1.0, mouth="smile" if c > 0.7 else "flat")

    R.add_front_rows(p)

    #: Her arms folded. She is waiting for you to trust somebody.
    folded_near, folded_far = (8.0, 9.5), (-1.0, 22.0)
    p.set_rest(na=folded_near, fa=folded_far, nh="fist", mouth="flat", brows=-1.0, lean=-2.0)

    @p.row
    def idle(i: int, n: int):
        # Still, her arms folded, and her eyes go from one of you to the other.
        _, s, c = loop(i, n)
        return P(hip=(0.0, 0.3 + 0.3 * s), head=(0.3 * c, 0.0, 3.0 * c), eyes="closed" if i == n - 2 else "open", mouth="smile" if c > 0.7 else "flat")

    _walk(p, (-3.0, 24.5), (3.0, 24.0), reach=8.8, lean=3.0, swing=5.0, nh="fist", fh="fist")

    @p.row
    def talk(i: int, n: int):
        # She does not move much to talk. One hand turns over.
        _, s, _c = loop(i, n)
        return P(hip=(0.0, 0.3 * s), head=(0.3, 0.0, 2.0 * s), na=(13.0, 7.0 - 2.0 * max(0.0, s)), nh="open" if s > 0.0 else "flat",
                 mouth=("open", "flat", "smile", "flat")[i % 4], brows=-1.0)

    @p.row
    def interact(i: int, n: int):
        # She takes the letter, and the one she gives on is not the one she took.
        take = P(hip=(1.0, 1.0), lean=6.0, na=(24.0, 2.0), nh="soft", brows=-1.0)
        swap = P(lean=-2.0, na=(9.0, 12.0), nh="soft", fa=(-8.0, 20.0), eyes="closed", mouth="smile", brows=0.0)
        give = P(hip=(1.0, 1.0), lean=6.0, na=(24.0, 2.0), nh="soft", mouth="smile", brows=-1.0)
        return p.keys(shot(i, n), [(0.0, P()), (0.25, take), (0.5, swap), (0.75, give), (1.0, P())])

    def effects(ctx) -> List[Stamp]:
        out: List[Stamp] = []
        if ctx.anim == "interact" and 0.15 <= ctx.u <= 0.9:
            hers = ctx.u > 0.5
            out.append((_letter(K, LINING if hers else (70, 130, 200, 255)), (ctx.hand[0] + 6.0, ctx.hand[1] - 2.0), "letter", -8.0))
            if 0.45 <= ctx.u <= 0.6:
                out.append((_spark(K, 3.5, LINING), (ctx.hand[0] + 6.0, ctx.hand[1] - 13.0), "spark", 0.0))
        return out

    p.effects = effects

    # ---- In the round. The listening piece is at her right ear only, so her
    # head is not the same on both sides: her left three-quarter view and her
    # left side are her head without it, and her coat (straps, pouch, the
    # lining at the far side) is not mirrored. Her head from the side is
    # drawn as the cast draws a head in the numbers of a profile; her braid
    # hangs through 3D points, drawn as her own braid is.
    def no_piece(d) -> None:
        K.line(d, [K.at(0.4, 2.6), K.at(2.4, 6.4)], mix(skin[0], skin[2], 0.5), 0.5)

    left_head = R.make_head(K, ("mallory_left",), *skin, skull=(0.0, -2.4, 7.6, 8.8), jaw=(2.6, 4.0, 5.0, 7.2),
                            nose=((7.2, 0.8), (8.6, 3.0), (8.2, 3.8), (7.2, 4.0)), ear=None, shape=hair_shape, under=hair, over=no_piece)
    brows = R.make_brows(K, [(-0.8, -4.2), (1.8, -4.4), (4.6, -3.2)], [(5.8, -3.4), (7.2, -4.4), (8.6, -4.2)], (92, 40, 38, 255), 0.9)
    mouth = R.make_mouth(K, (5.6, 7.6), (120, 52, 56, 255), wide=0.8)

    def side_hair_shape(d) -> None:
        K.oval(d, K.at(-1.6, -4.4), 9.6, 8.6, WHITE)
        K.poly(d, [K.at(-6.4, -9.0), K.at(-2.4, -14.6), K.at(7.6, -14.0), K.at(9.8, -10.0), K.at(6.4, -8.0)], WHITE)

    def side_hair(d) -> None:
        K.poly(d, [K.at(20.0, -9.6), K.at(8.2, -9.6), K.at(4.4, -8.0), K.at(1.6, -5.6), K.at(0.6, -3.4), K.at(-0.6, -1.6), K.at(-3.0, -1.4), K.at(-3.6, 3.4),
                   K.at(-2.4, 4.6), K.at(-2.0, 6.6), K.at(-20.0, 6.6), K.at(-20.0, -26.0), K.at(20.0, -26.0)], HAIR)
        for strand in ([(7.0, -10.4), (0.4, -8.6), (-6.4, -3.6)], [(3.4, -11.8), (-3.6, -9.6), (-8.0, -4.0)], [(-5.0, -1.0), (-7.4, 1.6)]):
            K.line(d, [K.at(x, y) for x, y in strand], HAIR_DARK, 0.6)

    def side_piece(d) -> None:
        K.line(d, [K.at(3.0, 2.6), K.at(4.6, 6.4)], mix(skin[0], skin[2], 0.5), 0.5)
        K.line(d, [K.at(-1.4, 1.8), K.at(3.0, 5.8), K.at(5.8, 6.6)], STEEL, 0.8)
        K.oval(d, K.at(-1.6, 1.0), 2.5, 2.9, BRASS, OUTLINE, 0.6)
        K.oval(d, K.at(-1.6, 1.0), 1.1, 1.3, BRASS_DARK)
        K.line(d, [K.at(-2.4, -1.8), K.at(-1.2, -6.4)], STEEL, 0.8)

    def side_bare(d) -> None:
        K.line(d, [K.at(3.0, 2.6), K.at(4.6, 6.4)], mix(skin[0], skin[2], 0.5), 0.5)

    def side_head(piece: bool):
        made = R.make_head(K, ("mallory_side", piece), *skin, skull=(0.0, -2.4, 8.6, 8.8), jaw=(3.4, 4.0, 5.6, 7.2),
                           nose=((8.0, 0.8), (9.4, 3.0), (9.0, 3.8), (8.0, 4.0)), ear=None, shape=side_hair_shape, under=side_hair,
                           over=side_piece if piece else side_bare, far_shade=False)
        side_eyes = R.make_eyes(K, (6.2, -0.4), None, ink=INK, iris=(70, 140, 130, 255), size=0.85, lash=0.25)
        side_brows = R.make_brows(K, [(4.2, -4.0), (6.2, -4.4), (8.4, -3.6)], None, (92, 40, 38, 255), 0.9)
        side_mouth = R.make_mouth(K, (7.8, 7.6), (120, 52, 56, 255), wide=0.5)
        return lambda pose: [(made(), "head"), (side_eyes(str(pose["eyes"])), "eyes"), (side_brows(R.brow_mood(pose)), "brows"),
                             (side_mouth(str(pose["mouth"])), "mouth")]

    def braid_3d(chains):
        pts_rel = chains[0]

        def paint(d) -> None:
            pts = [K.at(x, y) for x, y in pts_rel]
            K.stroke(d, pts, OUTLINE, 5.0 + 2.4)
            K.stroke(d, pts, HAIR, 5.0)
            for k in range(1, len(pts), 2):
                K.oval(d, pts[k], 2.9, 2.9, BRASS_DARK)
                K.oval(d, pts[k], 2.0, 2.0, BRASS)
            K.oval(d, pts[-1], 3.2, 3.2, OUTLINE)
            K.oval(d, pts[-1], 2.2, 2.2, STEEL)

        return K.aligned(("mallory_braid_3d", tuple(tuple(round(c, 1) for c in q) for q in pts_rel)), paint)

    hy = p.b.neck[1] + p.b.head_up[1]
    # It hangs from the back of her head down her back, on her coat.
    braid_points = [(0.0, hy - 1.0, -7.4), (0.0, hy + 4.0, -8.6), (0.0, hy + 10.0, -9.2), (0.0, hy + 16.0, -9.4), (0.0, hy + 22.0, -9.4),
                    (0.0, hy + 28.0, -9.4), (0.0, hy + 33.0, -9.2), (0.0, hy + 38.0, -9.0)]

    class FrontBraid:
        """Her braid from the front, as her front rows draw it
        (``front_braid``): out to one side past her shoulder, behind it."""

        def piece(self, K_, J, head_at):
            def draw(view, far):
                if abs(O.facing(view)) > 10.0:
                    return None
                return front_braid((0.0, 0.0))[0][0], 0.0, False

            return O.Sprite("front_braid", (0.0, 0.0, 0.0), draw, lead=-12.0)

    radius = 8.0
    at = lambda x: math.degrees(x / radius)  # noqa: E731
    ROUNDS["mallory"] = C.Round(
        "Mallory", C.PersonBody(p, back_layers=("back",), mirror=(),
                                heads={"left": lambda pose: [(left_head(), "head"), (eyes(str(pose["eyes"])), "eyes"), (brows(R.brow_mood(pose)), "brows"),
                                                             (mouth(str(pose["mouth"])), "mouth")],
                                       "side": side_head(True), "side_left": side_head(False)}),
        C.Look(
            C.auto_head(p, head, eyes, hair=lambda u, v: (v < -5.6 - 2.0 * np.clip(np.abs(u) / 50.0, 0.0, 1.0)) | ((np.abs(u) > 72.0) & (v < 3.4))
                        | ((np.abs(u) > 100.0) & (v < 6.6)),
                        hair_colour=HAIR, hair_shade=HAIR_DARK, volumes=[((0.0, -4.8, -1.0), (8.2, 7.6, 8.4)), ((0.0, -10.4, 2.2), (5.6, 3.8, 6.4))],
                        lines=[O.curve([O.on_ellipsoid((0.0, -4.8, -1.0), (8.2, 7.6, 8.4), u, v, 0.2)[0] for v in (-11.6, -6.0, -1.0)], HAIR_DARK, 0.6)
                               for u in (-150.0, -110.0, 110.0, 150.0, 180.0)]
                        + [O.circle((-8.2, 1.0, -0.4), (-1.0, 0.0, 0.0), 2.4, OUTLINE, 0.6, fill=BRASS, slack=1.4)]),
            C.auto_trunk(p, [W.Band(top - 1.0, top + 3.4, COAT_DARK), W.Path([(at(-7.0), top + 5.0), (at(7.0), -15.0)], TEAL, 0.85),
                             W.Path([(at(7.0), top + 5.0), (at(-7.0), -15.0)], BRASS, 0.75), W.Dot(0.0, top + 14.6, 2.0, LINING, ring=OUTLINE),
                             W.Dot(0.0, top + 14.6, 0.8, BRASS), W.Dot(at(-6.0), top + 9.0, 0.7, STEEL), W.Dot(at(6.0), top + 9.0, 0.7, STEEL),
                             W.Dot(at(-5.6), -18.0, 0.7, STEEL), W.Dot(at(5.6), -18.0, 0.7, STEEL), W.Band(-14.6, -11.6, (60, 54, 62, 255)),
                             W.Patch(at(-2.0), at(2.0), -15.4, -10.8, BRASS), W.Patch(at(-7.4), at(-3.6), -11.0, -5.6, (70, 60, 66, 255)),
                             W.Strip(0.0, -10.6, 26.0, 0.8, LINING, flare=1.8), W.Down(0.0, -10.6, 26.0, LINING_DARK),
                             W.Down(180.0, top + 4.0, 26.0, COAT_DARK)], radius=radius),
            back_pieces=[W.Chains("braid", [braid_points], braid_3d, lead=1.0), FrontBraid()]),
        # Her arms folded.
        C.Stance(hands={"r": C.Hand(at=(4.0, -20.0, 7.6), pole=(-1.0, 0.2, -0.4), mode="fist"),
                        "l": C.Hand(at=(-4.0, -19.0, 7.0), pole=(1.0, 0.2, -0.4), mode="fist")}, stagger=1.8))

    _meta("mallory", "Mallory", ["hub", "peaceful", "cryptography_crew", "attacker"],
          "Mallory is the conventional malicious active attacker in security examples. Unlike Eve, she intercepts, edits, impersonates, and relays; "
          "the name is a mnemonic for malicious behavior rather than a parody of a real person.",
          "Use as a man-in-the-middle villain, saboteur, shapeshifter, or active network hazard. Her mechanics should replace messages, impersonate "
          "both endpoints, and exploit trust between characters who believe they are speaking directly.",
          ["Eve just listens. I edit.", "I sit between two people who trust each other and quietly become both of them.",
           "People built whole cathedrals of math just to ruin my afternoon."])


# =============================================================================
# Olivia: the oracle. She answers at once and she is right; ask the right thing.
# =============================================================================


def _olivia() -> None:
    # A willowy woman, long and narrow, and very still.
    p = _person("olivia", 165.0, woman=True, legs=2.0)
    K, P = p.K, p.P
    skin = TAN
    ROBE, ROBE_DARK, ROBE_LIGHT = (198, 186, 228, 255), (140, 126, 184, 255), (232, 226, 248, 255)
    VEIL, VEIL_DARK, SASH, HAIR = (236, 232, 250, 255), (178, 170, 214, 255), (120, 96, 176, 255), (92, 78, 104, 255)
    ASK, ASK_DARK = (176, 232, 255, 255), (80, 130, 196, 255)
    top = p.b.neck[1] - 2.0

    def front(d, hb, hf) -> None:
        # A band down her front with the three marks of a query, and a sash.
        K.poly(d, [K.at(3.6, top), K.at(8.4, top), K.at(9.8 + hf, 44.0), K.at(4.4 + hf * 0.4, 44.0)], ROBE_LIGHT)
        for y in (-22.0, -12.0, -2.0):
            K.oval(d, K.at(6.2, y), 1.2, 1.2, SASH)
        K.poly(d, [K.at(-12.0, -17.6), K.at(13.0, -16.6), K.at(13.0, -14.2), K.at(-12.0, -15.2)], SASH)
        for x in (-7.0, -2.6):
            K.line(d, [K.at(x, 4.0), K.at(x - 1.6 - hb * 0.4, 40.0)], ROBE_DARK, 0.6)

    p.torso = R.make_figure(K, ("olivia",), ROBE, ROBE_DARK, back=(6.8, 7.0, 5.4, 7.4, 12.6), front=(6.0, 8.0, 5.6, 7.8, 12.0), hem_y=p.b.hip_up - 5.0, top=top,
                            shoulders=((-4.4, p.b.near_shoulder[1] + 0.6), (5.0, p.b.far_shoulder[1] + 0.4)), shoulder_r=(4.0, 3.6), waist_y=-16.0,
                            shade_from=8.6, detail=front)
    _dress(p, skin, ROBE, ROBE_DARK, ROBE, ROBE_DARK, (150, 132, 180, 255), (98, 84, 132, 255), cuff=ROBE_LIGHT, arm=(5.6, 5.8, 6.6), legs=(6.0, 5.0, 4.4),
           hand=0.85, neck=3.6)

    def veil_shape(d) -> None:
        # Her veil: over her head, and down behind her shoulders.
        K.oval(d, K.at(-1.2, -4.0), 9.6, 9.8, WHITE)
        K.poly(d, [K.at(-9.6, -6.0), K.at(-12.6, 6.0), K.at(-11.0, 16.0), K.at(-3.0, 14.0), K.at(0.0, 6.0)], WHITE)

    def veil(d) -> None:
        K.poly(d, [K.at(20.0, -9.0), K.at(8.6, -9.0), K.at(4.6, -9.6), K.at(1.2, -8.0), K.at(-1.0, -4.6), K.at(-1.6, 1.0), K.at(-1.0, 6.0), K.at(0.0, 9.0),
                   K.at(0.0, 30.0), K.at(-20.0, 30.0), K.at(-20.0, -26.0), K.at(20.0, -26.0)], VEIL)
        K.line(d, [K.at(8.6, -9.2), K.at(4.6, -9.8), K.at(1.0, -8.0), K.at(-1.2, -4.6), K.at(-1.8, 1.0), K.at(-1.2, 6.0)], GOLD, 0.9)
        for x0, y0, x1, y1 in ((-5.0, -8.0, -9.0, 8.0), (-7.6, 2.0, -9.4, 14.0)):
            K.line(d, [K.at(x0, y0), K.at(x1, y1)], VEIL_DARK, 0.6)
        K.poly(d, [K.at(1.6, -8.0), K.at(8.0, -8.6), K.at(4.4, -6.4), K.at(0.4, -5.0)], HAIR)

    head = R.make_head(K, ("olivia",), *skin, skull=(0.0, -2.4, 7.4, 8.8), jaw=(2.6, 3.8, 4.8, 7.2), nose=((7.2, 0.6), (8.8, 3.2), (8.4, 4.0), (7.2, 4.2)),
                       ear=None, shape=veil_shape, under=veil)
    eyes = R.make_eyes(K, (2.4, -0.2), (7.4, -0.4), ink=INK, iris=(110, 96, 170, 255), size=0.9, lash=0.8)
    _face(p, head, eyes, R.make_brows(K, [(0.4, -3.8), (2.4, -4.6), (4.6, -4.2)], [(6.0, -4.3), (7.4, -4.6), (8.6, -4.2)], HAIR, 0.7),
          R.make_mouth(K, (5.6, 7.4), (140, 76, 96, 255), wide=0.7, lips=(190, 124, 150, 255)))

    # ---- From the front: her veil round her face and down each side of her
    # neck, the band and the sash of her robe.
    sy = p.b.near_shoulder[1] + 0.6
    hem = p.b.hip_up - 5.0

    def front_robe(d) -> None:
        K.poly(d, [K.at(-2.2, top), K.at(2.2, top), K.at(3.4, hem + 2.0), K.at(-3.4, hem + 2.0)], ROBE_LIGHT)
        for y in (-24.0, -10.0, -2.0):
            K.oval(d, K.at(0.0, y), 1.2, 1.2, SASH)
        K.poly(d, [K.at(-20.0, -17.4), K.at(20.0, -17.4), K.at(20.0, -15.0), K.at(-20.0, -15.0)], SASH)
        for x in (-5.4, 5.4):
            K.line(d, [K.at(x, 0.0), K.at(x * 1.7, hem - 2.0)], ROBE_DARK, 0.6)

    def front_veil_shape(d) -> None:
        K.oval(d, K.at(0.0, -3.6), 9.8, 10.2, WHITE)
        for sx in (-1.0, 1.0):
            K.poly(d, [K.at(9.4 * sx, -2.0), K.at(11.4 * sx, 15.0), K.at(5.2 * sx, 15.0), K.at(5.6 * sx, 6.0)], WHITE)

    def front_veil(d) -> None:
        K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, 20.0), K.at(-20.0, 20.0)], VEIL)
        for sx in (-1.0, 1.0):
            K.line(d, [K.at(7.6 * sx, 4.0), K.at(8.8 * sx, 14.0)], VEIL_DARK, 0.6)
        K.oval(d, K.at(0.0, 1.0), 6.2, 8.2, skin[0])
        ring = [K.at(6.4 * math.cos(math.radians(a)), 1.0 + 8.4 * math.sin(math.radians(a))) for a in range(-200, 21, 10)]
        K.line(d, ring, GOLD, 0.9)
        K.poly(d, [K.at(0.0, -7.4), K.at(4.2, -6.0), K.at(5.4, -2.6), K.at(3.0, -4.6), K.at(0.0, -5.4), K.at(-3.0, -4.6), K.at(-5.4, -2.6), K.at(-4.2, -6.0)], HAIR)

    def front_nose(d) -> None:
        K.line(d, [K.at(-0.2, 0.8), K.at(-0.8, 3.4), K.at(0.0, 4.2), K.at(0.8, 3.4)], skin[2], 0.5)

    p.front_torso = R.make_front_torso(K, ("olivia",), ROBE, ROBE_DARK, [(top, 3.2), (top + 3.6, 6.6), (top + 12.5, 7.6), (-16.0, 5.4), (0.0, 7.8), (hem, 12.4)],
                                       shoulder=(5.2, sy, 3.8, 4.0), detail=front_robe)
    p.front_head_layers = R.front_face(
        R.make_front_head(K, ("olivia",), skin[0], skin[2], wide=7.2, jaw=5.4, chin=3.4, shape=front_veil_shape, hair=front_veil, face=front_nose),
        R.make_front_eyes(K, ("olivia",), ink=INK, iris=(110, 96, 170, 255), spread=3.0, y=-0.2, size=0.9, lash=0.5),
        R.make_front_brows(K, ("olivia",), HAIR, spread=3.0, y=-3.6, width=0.7),
        R.make_front_mouth(K, ("olivia",), y=7.4, colour=(140, 76, 96, 255), lips=(190, 124, 150, 255), wide=0.7))
    p.front_shoe = R.make_front_shoe(K, (150, 132, 180, 255), (98, 84, 132, 255), p.b.ankle_up, wide=0.85)
    p.front_span = (6.4, 4.0)

    @p.front_row
    def front(i: int, n: int):
        # Very still, her eyes closed. She opens them one time to look at you.
        _, s, c = loop(i, n)
        return R.FP(hip=(0.0, 0.3 + 0.3 * s), head=(0.0, -0.2 * s, 0.0), eyes="open" if i in (n - 3, n - 2) else "closed", **R.front_arms(p, "clasped"))

    R.add_front_rows(p)

    #: Her hands one in the other, low in front of her.
    held_near, held_far = (5.0, 16.0), (-1.0, 22.0)
    p.set_rest(na=held_near, fa=held_far, nh="flat", eyes="closed")

    @p.row
    def idle(i: int, n: int):
        # She waits for a question, her eyes shut. She does not need them.
        _, s, _c = loop(i, n)
        return P(hip=(0.0, 0.3 + 0.3 * s), head=(0.0, -0.2 * s, -2.0 + s), eyes="open" if i in (n - 3, n - 2) else "closed")

    _walk(p, held_near, held_far, reach=6.4, lift=3.0, lean=0.0, nh="flat")
    p.poses["walk"] = (lambda base: (lambda i, n: dict(base(i, n), eyes="open")))(p.poses["walk"])

    @p.row
    def talk(i: int, n: int):
        # One open hand, and the answer in it.
        _, s, _c = loop(i, n)
        return P(hip=(0.0, 0.3 * s), head=(0.3, 0.0, 2.0 * s), na=(15.0, 6.0 - 2.0 * max(0.0, s)), nh="open", eyes="open",
                 mouth=("open", "smile", "o", "smile")[i % 4])

    @p.row
    def interact(i: int, n: int):
        ask = P(lean=2.0, head=(0.0, 0.0, 4.0), na=(12.0, 0.0), nh="point", eyes="closed")
        answer = P(lean=4.0, na=(22.0, -2.0), nh="open", eyes="open", mouth="smile", brows=1.0)
        return p.keys(shot(i, n), [(0.0, P()), (0.3, ask), (0.55, answer), (0.85, answer), (1.0, P())])

    def effects(ctx) -> List[Stamp]:
        out: List[Stamp] = []
        if ctx.anim == "talk" and ctx.i % 4 in (1, 2):
            out.append((R.tick(K, 3.6, ASK, ASK_DARK), (ctx.hand[0] + 8.0, ctx.hand[1] - 12.0), "tick", 0.0))
        elif ctx.anim == "interact" and 0.2 <= ctx.u <= 0.9:
            asked = ctx.u < 0.5
            at = (ctx.head[0] + 16.0, ctx.head[1] - 18.0) if asked else (ctx.hand[0] + 12.0, ctx.hand[1] - 12.0)
            out.append((R.glyph(K, "?", 9.0, ASK, ASK_DARK) if asked else R.tick(K, 5.0, GOLD, GOLD_DARK), at, "answer", 0.0))
        return out

    p.effects = effects

    # ---- In the round: her veil over her head and down behind her
    # shoulders, its gold edge round her face; her long robe with its band,
    # its three marks and its sash; her hands one in the other in front.
    def side_veil_shape(d) -> None:
        K.oval(d, K.at(-2.0, -4.0), 10.2, 9.8, WHITE)
        K.poly(d, [K.at(-10.4, -6.0), K.at(-13.4, 6.0), K.at(-11.8, 16.0), K.at(-3.8, 14.0), K.at(-0.8, 6.0)], WHITE)

    def side_veil(d) -> None:
        edge = [(9.4, -9.0), (5.4, -9.8), (2.0, -8.0), (0.4, -4.6), (-0.2, 1.0), (0.4, 6.0), (1.4, 9.0)]
        K.poly(d, [K.at(20.0, -9.0)] + [K.at(x, y) for x, y in edge] + [K.at(1.4, 30.0), K.at(-20.0, 30.0), K.at(-20.0, -26.0), K.at(20.0, -26.0)], VEIL)
        K.line(d, [K.at(x, y - 0.2) for x, y in edge[:-1]], GOLD, 0.9)
        for x0, y0, x1, y1 in ((-4.0, -8.0, -8.6, 8.0), (-7.0, 2.0, -9.8, 14.0)):
            K.line(d, [K.at(x0, y0), K.at(x1, y1)], VEIL_DARK, 0.6)
        K.poly(d, [K.at(2.6, -8.0), K.at(8.8, -8.6), K.at(5.2, -6.4), K.at(1.4, -5.0)], HAIR)

    side_head = R.make_head(K, ("olivia_side",), *skin, skull=(0.0, -2.4, 8.4, 8.8), jaw=(3.4, 3.8, 5.4, 7.2),
                            nose=((8.0, 0.6), (9.6, 3.2), (9.2, 4.0), (8.0, 4.2)), ear=None, shape=side_veil_shape, under=side_veil, far_shade=False)
    side_eyes = R.make_eyes(K, (6.4, -0.2), None, ink=INK, iris=(110, 96, 170, 255), size=0.9, lash=0.8)
    side_brows = R.make_brows(K, [(4.4, -3.8), (6.4, -4.6), (8.4, -4.2)], None, HAIR, 0.7)
    side_mouth = R.make_mouth(K, (7.8, 7.4), (140, 76, 96, 255), wide=0.5, lips=(190, 124, 150, 255))
    veil_3d = ((0.0, -3.4, -1.8), (9.6, 10.4, 9.0))
    ROUNDS["olivia"] = C.Round(
        "Olivia", C.PersonBody(p, heads={"side": lambda pose: [(side_head(), "head"), (side_eyes(str(pose["eyes"])), "eyes"),
                                                               (side_brows(R.brow_mood(pose)), "brows"), (side_mouth(str(pose["mouth"])), "mouth")]}),
        C.Look(
            C.auto_head(p, head, eyes, hair=lambda u, v: ~((np.abs(u) < 50.0) & (v > -8.6)), hair_colour=VEIL, hair_shade=VEIL_DARK, volumes=[veil_3d],
                        lines=[O.curve([O.on_ellipsoid(*veil_3d, u, -8.0 + 16.0 * max(0.0, (abs(u) - 40.0) / 20.0) if abs(u) > 40.0 else -9.2, 0.3)[0]
                                        for u in np.linspace(-58.0, 58.0, 13)], GOLD, 0.9)]),
            C.auto_trunk(p, [W.Strip(0.0, top, hem + 2.0, 2.2, ROBE_LIGHT, flare=1.2)] + [W.Dot(0.0, y, 1.2, SASH) for y in (-24.0, -10.0, -2.0)]
                         + [W.Band(-17.4, -15.0, SASH), W.Down(35.0, 0.0, hem - 2.0, ROBE_DARK, spread=10.0), W.Down(-35.0, 0.0, hem - 2.0, ROBE_DARK, spread=10.0),
                            W.Down(180.0, -14.0, hem - 2.0, ROBE_DARK)]),
            back_pieces=[W.Mane([(0.0, 3.0, -8.6), (0.0, 8.0, -9.4), (0.0, 12.0, -9.8), (0.0, 16.0, -9.6)], 5.0, VEIL, VEIL_DARK, back_width=15.0)]),
        C.Stance(hands={"r": C.Hand(at=(-1.0, 0.0, 8.0), pole=(-0.6, 0.3, -0.6), mode="flat"), "l": C.Hand(at=(1.6, 1.4, 7.6), pole=(0.6, 0.3, -0.6))},
                 stagger=1.2))
    _meta("olivia", "Olivia", ["hub", "peaceful", "cryptography_crew", "oracle"],
          "Olivia is the oracle role in cryptographic examples, personified as a character who answers a narrowly defined class of questions "
          "perfectly. The joke is that 'always correct' sounds omniscient until the player notices the exact interface and restrictions around "
          "what may be asked.",
          "Use as an oracle, query-limited hint system, puzzle device, or exploitable cryptographic service. She should answer exactly, instantly, "
          "and only within her contract, making question design more important than raw knowledge.",
          ["Ask me anything and I answer instantly, correctly, every time.", "People stop listening right before the important part.", "Define your query."])


# =============================================================================
# Peggy: the prover. She shows that she knows, and not what she knows.
# =============================================================================


def _peggy() -> None:
    # A short woman with a round figure, and never still.
    p = _person("peggy", 160.0, girth=0.6, woman=True, legs=-1.0)
    K, P = p.K, p.P
    skin = TAN
    COAT, COAT_DARK, COAT_LIGHT = (232, 124, 52, 255), (170, 78, 40, 255), (250, 172, 96, 255)
    VEST, SHIRT, TROUSER, TROUSER_DARK = (60, 54, 78, 255), (248, 244, 232, 255), (58, 52, 76, 255), (38, 34, 54, 255)
    HAIR, HAIR_LIGHT, HAT, HAT_DARK = (34, 28, 36, 255), (80, 70, 90, 255), (46, 42, 60, 255), (26, 24, 38, 255)
    top = p.b.neck[1] - 2.0

    def front(d, hb, hf) -> None:
        # A tailcoat cut away at the front: a dark waistcoat, a white shirt, a bow.
        K.poly(d, [K.at(2.4, top), K.at(12.0, top), K.at(12.4, 4.0), K.at(4.4, 4.0), K.at(3.6, -14.0)], VEST)
        K.poly(d, [K.at(4.0, top), K.at(9.0, top), K.at(6.8, top + 12.0)], SHIRT)
        K.poly(d, [K.at(4.0, top + 2.0), K.at(6.4, top + 3.4), K.at(4.0, top + 5.0)], COAT)
        K.poly(d, [K.at(9.0, top + 2.0), K.at(6.6, top + 3.4), K.at(9.0, top + 5.0)], COAT)
        K.poly(d, [K.at(9.6, top), K.at(13.0, top), K.at(13.0, 8.0), K.at(10.2, 8.0)], COAT_DARK)
        K.poly(d, [K.at(-0.4, top + 1.0), K.at(3.0, top), K.at(4.2, -16.0), K.at(0.4, -24.0)], COAT_LIGHT)
        for y in (-12.0, -6.0, 0.0):
            K.oval(d, K.at(7.4, y), 0.9, 0.9, GOLD)

    def torso(hem_back: int, hem_front: int):
        # The coat stops at her waist in front, and its two tails hang behind.
        hb = float(hem_back)

        def shape(d) -> None:
            K.poly(d, [K.at(-3.4, top), K.at(-7.8, top + 4.0), K.at(-8.4, top + 12.0), K.at(-7.0, -12.0), K.at(-9.4, -2.0), K.at(-11.6 - hb * 1.6, 24.0 - hb * 0.3),
                       K.at(-5.0 - hb, 25.0), K.at(-2.0, 7.0), K.at(10.2, 6.0), K.at(10.0, -2.0), K.at(7.6, -12.0), K.at(9.4, top + 17.0), K.at(10.6, top + 13.0),
                       K.at(9.6, top + 9.0), K.at(7.0, top + 3.0), K.at(3.6, top - 0.4)], WHITE)
            K.oval(d, K.at(-4.8, p.b.near_shoulder[1] + 0.6), 4.6, 5.2, WHITE)
            K.oval(d, K.at(5.4, p.b.far_shoulder[1] + 0.4), 4.2, 4.8, WHITE)

        def paint(d) -> None:
            front(d, hb, float(hem_front))
            K.line(d, [K.at(-6.4, 4.0), K.at(-7.4 - hb * 1.2, 22.0)], COAT_DARK, 0.7)

        return K.solid(("peggy_coat", hem_back, hem_front), shape, COAT, paint, outline=1.3, rim=0.3, shade=0.4, shade_colour=COAT_DARK)

    p.torso = torso
    _dress(p, skin, COAT, COAT_DARK, TROUSER, TROUSER_DARK, (40, 36, 52, 255), (20, 18, 30, 255), cuff=SHIRT, arm=(6.0, 5.2, 4.6), legs=(7.6, 6.0, 4.8), hand=0.88,
           heel=1.2, neck=4.0)

    def hair_shape(d) -> None:
        # A straight bob, cut at her jaw.
        K.oval(d, K.at(-1.2, -4.0), 9.4, 9.2, WHITE)
        K.poly(d, [K.at(-9.6, -4.0), K.at(-10.2, 7.0), K.at(-3.0, 7.6), K.at(-1.0, 0.0)], WHITE)

    def hair(d) -> None:
        K.poly(d, [K.at(20.0, -8.4), K.at(8.6, -8.4), K.at(6.0, -5.6), K.at(2.0, -5.0), K.at(-0.6, -3.0), K.at(-1.6, 1.0), K.at(-1.8, 8.0), K.at(-20.0, 8.0),
                   K.at(-20.0, -26.0), K.at(20.0, -26.0)], HAIR)
        K.line(d, [K.at(4.0, -10.0), K.at(-3.0, -8.6), K.at(-7.4, -2.0), K.at(-8.0, 5.0)], HAIR_LIGHT, 0.7)

    def hat():
        # A small top hat, worn at an angle. She is a little bit a conjurer.
        def shape(d) -> None:
            K.poly(d, [K.at(-6.6, -9.6), K.at(-5.6, -19.0), K.at(3.6, -20.4), K.at(4.6, -11.0)], WHITE)
            K.poly(d, [K.at(-10.0, -8.4), K.at(7.6, -11.0), K.at(7.8, -9.2), K.at(-9.8, -6.6)], WHITE)

        def detail(d) -> None:
            K.poly(d, [K.at(-6.8, -12.6), K.at(4.8, -14.2), K.at(4.8, -11.4), K.at(-6.6, -9.8)], COAT)

        return K.solid(("peggy_hat",), shape, HAT, detail, outline=1.2, rim=0.3, shade=0.4, shade_colour=HAT_DARK)

    head = R.make_head(K, ("peggy",), *skin, skull=(0.0, -2.0, 8.0, 8.6), jaw=(2.2, 3.6, 6.2, 6.6), nose=((7.4, 1.0), (9.0, 3.0), (8.6, 3.8), (7.4, 4.0)),
                       ear=None, shape=hair_shape, under=hair)
    eyes = R.make_eyes(K, (2.0, -0.2), (7.4, -0.4), ink=INK, iris=(80, 48, 30, 255), size=0.9, lash=0.6)
    _face(p, head, eyes, R.make_brows(K, [(-0.2, -4.0), (2.0, -4.8), (4.4, -4.2)], [(5.8, -4.4), (7.4, -4.8), (8.8, -4.2)], HAIR, 0.9),
          R.make_mouth(K, (5.8, 7.0), (130, 40, 56, 255), wide=0.9, lips=(214, 84, 96, 255)), hat)

    # ---- From the front: the cut of her coat open on her waistcoat, her
    # shirt and her bow; her bob, and her hat at its angle.
    sy = p.b.near_shoulder[1] + 0.6

    def front_coat(d) -> None:
        K.poly(d, [K.at(-4.6, top), K.at(4.6, top), K.at(6.4, -4.0), K.at(6.0, 8.0), K.at(-6.0, 8.0), K.at(-6.4, -4.0)], VEST)
        K.poly(d, [K.at(-2.8, top), K.at(2.8, top), K.at(0.0, top + 12.0)], SHIRT)
        for sx in (-1.0, 1.0):
            K.poly(d, [K.at(2.6 * sx, top + 2.0), K.at(0.2 * sx, top + 3.4), K.at(2.6 * sx, top + 5.0)], COAT)
            K.poly(d, [K.at(4.6 * sx, top), K.at(7.4 * sx, top + 1.0), K.at(5.4 * sx, -16.0)], COAT_LIGHT)
        for y in (-12.0, -6.0, 0.0):
            K.oval(d, K.at(0.0, y), 0.9, 0.9, GOLD)

    def front_hair_shape(d) -> None:
        K.oval(d, K.at(0.0, -4.2), 9.4, 9.0, WHITE)
        K.poly(d, [K.at(-9.4, -4.0), K.at(-9.8, 7.4), K.at(9.8, 7.4), K.at(9.4, -4.0)], WHITE)

    def front_hair(d) -> None:
        K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, -2.0), K.at(7.2, -2.0), K.at(6.6, -5.6), K.at(2.0, -5.0), K.at(-3.0, -7.0), K.at(-6.6, -5.0),
                   K.at(-7.2, -2.0), K.at(-20.0, -2.0)], HAIR)
        for sx in (-1.0, 1.0):
            K.poly(d, [K.at(7.2 * sx, -2.0), K.at(6.8 * sx, 3.0), K.at(5.6 * sx, 7.0), K.at(5.4 * sx, 30.0), K.at(30.0 * sx, 30.0), K.at(30.0 * sx, -2.0)], HAIR)
            K.line(d, [K.at(8.2 * sx, -3.0), K.at(8.4 * sx, 5.0)], HAIR_LIGHT, 0.7)

    def front_nose(d) -> None:
        K.line(d, [K.at(-0.2, 0.8), K.at(-0.8, 3.4), K.at(0.0, 4.2), K.at(0.8, 3.4)], skin[2], 0.5)

    p.front_torso = R.make_front_torso(K, ("peggy",), COAT, COAT_DARK, [(top, 3.6), (top + 3.6, 7.8), (top + 12.5, 9.2), (-12.0, 7.8), (0.0, 9.4), (8.0, 9.6)],
                                       shoulder=(6.2, sy, 4.4, 4.8), detail=front_coat)
    p.front_head_layers = R.front_face(
        R.make_front_head(K, ("peggy",), skin[0], skin[2], wide=7.8, jaw=6.2, chin=3.2, shape=front_hair_shape, hair=front_hair, face=front_nose),
        R.make_front_eyes(K, ("peggy",), ink=INK, iris=(80, 48, 30, 255), spread=3.3, y=-0.2, size=0.9, lash=0.4),
        R.make_front_brows(K, ("peggy",), HAIR, spread=3.3, y=-3.8, width=0.9),
        R.make_front_mouth(K, ("peggy",), y=7.0, colour=(130, 40, 56, 255), lips=(214, 84, 96, 255), wide=0.85), extra=[(hat, "hat")])
    p.front_shoe = R.make_front_shoe(K, (40, 36, 52, 255), (20, 18, 30, 255), p.b.ankle_up, wide=0.9)
    p.front_span = (7.4, 4.6)
    R.add_front_rows(p, hands="sides")

    #: One hand behind her back. Nothing in it. You will have to take her word.
    behind = (-6.0, 21.5)
    p.set_rest(na=(4.0, 24.0), fa=behind)

    @p.row
    def idle(i: int, n: int):
        # She turns her open hand over: nothing in it, and nothing behind it.
        _, s, c = loop(i, n)
        return P(hip=(0.0, 0.3 + 0.3 * s), lean=-1.0, head=(0.0, 0.0, 3.0 * c), na=(13.0, 6.0 + 1.5 * s), nh="open" if c > 0.0 else "flat",
                 eyes="closed" if i == n - 2 else "open", brows=1.0 if c > 0.5 else 0.0)

    _walk(p, (4.0, 24.0), behind, reach=7.6, lift=4.6, lean=1.0, swing=6.0)
    p.poses["walk"] = (lambda base: (lambda i, n: dict(base(i, n), fa=behind)))(p.poses["walk"])

    @p.row
    def talk(i: int, n: int):
        _, s, c = loop(i, n)
        return P(hip=(0.0, 0.4 * s), lean=-2.0, head=(0.3, 0.0, 3.0 * s), na=(15.0 + 3.0 * c, 2.0 - 5.0 * max(0.0, s)), nh="open",
                 mouth=("open", "smile", "big", "smile")[i % 4], brows=1.0)

    @p.row
    def interact(i: int, n: int):
        # A flourish, a bow, and the door is open. She will not say how.
        up = P(lean=-5.0, head=(0.0, 0.0, -8.0), na=(10.0, -24.0), nab=-1.0, arm="under", nh="open", mouth="big", brows=1.0)
        bow = P(hip=(-1.0, 2.0), lean=22.0, head=(1.0, 1.0, 8.0), na=(22.0, 10.0), nh="open", eyes="closed", hem=(4.0, 0.0))
        return p.keys(shot(i, n), [(0.0, P()), (0.3, up), (0.65, bow), (0.85, bow), (1.0, P(eyes="happy"))])

    def effects(ctx) -> List[Stamp]:
        out: List[Stamp] = []
        if ctx.anim == "interact" and 0.2 <= ctx.u <= 0.9:
            out.append((_spark(K, 4.0, GOLD), (ctx.hand[0] + 6.0, ctx.hand[1] - 10.0), "spark_0", 0.0))
            out.append((_spark(K, 2.5, COAT_LIGHT), (ctx.hand[0] + 15.0, ctx.hand[1] - 3.0), "spark_1", 0.0))
            if ctx.u > 0.55:
                out.append((R.tick(K, 4.5, GOLD, GOLD_DARK), (ctx.head[0] + 18.0, ctx.head[1] - 14.0), "tick", 0.0))
        elif ctx.anim == "idle" and ctx.i in (2, 3):
            out.append((_spark(K, 2.5, GOLD), (ctx.hand[0] + 8.0, ctx.hand[1] - 9.0), "spark_0", 0.0))
        return out

    p.effects = effects

    # ---- In the round: her bob and her small top hat; her coat cut away at
    # her waist in front, open on her waistcoat, her shirt and her bow, and
    # its two tails behind; one hand at her side, one behind her back. Her
    # coat is her own ``torso``, which keeps no numbers, so its rings are the
    # numbers of her front coat.
    def side_hair_shape(d) -> None:
        K.oval(d, K.at(-1.8, -4.0), 10.0, 9.2, WHITE)
        K.poly(d, [K.at(-10.4, -4.0), K.at(-11.0, 7.0), K.at(-2.0, 7.6), K.at(0.4, 0.0)], WHITE)

    def side_hair(d) -> None:
        K.poly(d, [K.at(20.0, -8.4), K.at(9.4, -8.4), K.at(7.2, -5.6), K.at(3.2, -5.0), K.at(1.4, -3.0), K.at(0.8, 1.0), K.at(1.0, 7.8), K.at(-20.0, 8.0),
                   K.at(-20.0, -26.0), K.at(20.0, -26.0)], HAIR)
        K.line(d, [K.at(4.0, -10.0), K.at(-3.6, -8.6), K.at(-8.2, -2.0), K.at(-8.8, 5.0)], HAIR_LIGHT, 0.7)

    side_head = R.make_head(K, ("peggy_side",), *skin, skull=(0.0, -2.0, 9.0, 8.6), jaw=(3.0, 3.6, 6.8, 6.6),
                            nose=((8.2, 1.0), (9.8, 3.0), (9.4, 3.8), (8.2, 4.0)), ear=None, shape=side_hair_shape, under=side_hair, far_shade=False)
    side_eyes = R.make_eyes(K, (6.6, -0.2), None, ink=INK, iris=(80, 48, 30, 255), size=0.9, lash=0.6)
    side_brows = R.make_brows(K, [(4.2, -4.0), (6.4, -4.8), (8.6, -4.2)], None, HAIR, 0.9)
    side_mouth = R.make_mouth(K, (8.0, 7.0), (130, 40, 56, 255), wide=0.6, lips=(214, 84, 96, 255))
    crop, bob = ((0.0, -4.0, -1.0), (8.6, 8.2, 8.6)), ((0.0, -0.4, -2.4), (9.4, 7.8, 7.6))
    coat = W.Trunk(
        rings=[O.Ring(top - 0.5, 0.0, 0.3, 3.6, 3.0), O.Ring(top + 3.6, 0.0, 0.4, 7.8, 5.8), O.Ring(top + 12.5, 0.0, 1.2, 9.2, 8.4),
               O.Ring(-12.0, 0.0, 0.4, 7.8, 6.4), O.Ring(0.0, 0.0, 0.0, 9.4, 8.2), O.Ring(8.0, 0.0, 0.0, 9.6, 8.4)],
        garment=W.Garment(COAT, COAT_DARK, radius=9.2, features=[
            W.Opening(36.0, VEST, top=top + 1.0), W.Lapels(36.0, top, -16.0, 12.0, COAT_LIGHT, line=COAT_DARK), W.Neckline(top, top + 12.0, 16.0, SHIRT),
            W.Glow(10.0, top + 3.4, 1.6, 1.4, COAT, both=True), W.Buttons(0.0, -12.0, 0.0, 3, 0.9, GOLD), W.Down(180.0, top + 4.0, 8.0, COAT_DARK),
            W.Shade()]),
        shoulder=((-6.0, sy, 0.2), (4.4, 4.8, 4.4)))
    tails = W.Cloak([O.Ring(0.0, 0.0, 0.0, 8.8, 7.6), O.Ring(8.0, 0.0, -0.4, 9.2, 8.0), O.Ring(25.0, 0.0, -2.0, 9.8, 8.6)],
                    W.Garment(COAT, COAT_DARK, [W.Down(180.0, 2.0, 25.0, COAT_DARK, width=0.6), W.Shade()], radius=9.0), turns=(118.0, 242.0))
    hat_3d = W.Hat(
        crown=[O.Ring(-9.4, 0.0, -1.0, 5.6, 5.0), O.Ring(-18.0, 0.0, -1.2, 5.0, 4.6), O.Ring(-19.8, 0.0, -1.2, 4.8, 4.4), O.Ring(-19.8, 0.0, -1.2, 0.0, 0.0)],
        brim=[O.Ring(-9.6, 0.0, -1.0, 5.6, 5.0, v=0.0), O.Ring(-9.6, 0.0, -1.0, 8.8, 7.6, droop=-1.6, v=1.0),
              O.Ring(-8.8, 0.0, -1.0, 8.8, 7.6, droop=-1.6, v=2.0), O.Ring(-9.0, 0.0, -1.0, 5.6, 5.0, v=3.0)],
        garment=W.Garment(HAT, HAT_DARK, features=[W.Band(-13.4, -10.6, COAT), W.Shade(-0.4)]), under=HAT_DARK)
    ROUNDS["peggy"] = C.Round(
        "Peggy", C.PersonBody(p, heads={"side": lambda pose: [(side_head(), "head"), (side_eyes(str(pose["eyes"])), "eyes"),
                                                              (side_brows(R.brow_mood(pose)), "brows"), (side_mouth(str(pose["mouth"])), "mouth"),
                                                              (hat(), "hat")]}),
        C.Look(
            C.auto_head(p, head, eyes, hair=lambda u, v: (v < -5.0) | ((np.abs(u) > 55.0) & (v < 7.6)), hair_colour=HAIR, hair_shade=HAIR_LIGHT,
                        volumes=[crop, bob],
                        lines=[O.curve([O.on_ellipsoid(*crop, u + 20.0 * t, -10.0 + 6.0 * t, 0.2)[0] for t in (0.0, 0.5, 1.0)], HAIR_LIGHT, 0.7)
                               for u in (-150.0, -90.0, 100.0)]),
            coat, head_pieces=[hat_3d], pieces=[("trunk", tails)]),
        C.Stance(hands={"r": C.Hand(l=-8.6, pole=(-0.4, 0.0, -1.0)), "l": C.Hand(at=(1.0, -2.0, -9.6), pole=(1.0, 0.2, 0.0))}, stagger=1.8))
    _meta("peggy", "Peggy", ["hub", "peaceful", "cryptography_crew", "prover"],
          "Peggy is the prover in zero-knowledge proof stories. She can convince Victor that she knows a secret without revealing the secret "
          "itself, turning an abstract protocol role into a confident performer whose best demonstrations teach the observer nothing except that "
          "she succeeded.",
          "Use as a prover, magician, authentication guide, or puzzle NPC. Her gameplay should demonstrate possession or access repeatedly while "
          "withholding the witness, route, password, or mechanism that makes the feat possible.",
          ["I can prove that I know the way without showing you the way.", "You'll learn nothing. That's the guarantee.", "Ask again; the secret stays mine."])


# =============================================================================
# Sybil: one who is many. How many of her did you count?
# =============================================================================


def _sybil() -> None:
    # A long-legged woman who stands square, in a short jacket and high trousers.
    p = _person("sybil", 170.0, woman=True, legs=3.0)
    K, P = p.K, p.P
    skin = DEEP
    JACKET, JACKET_DARK, JACKET_LIGHT = (124, 70, 170, 255), (82, 42, 122, 255), (170, 118, 214, 255)
    SHIRT, TROUSER, TROUSER_DARK, HAIR, HAIR_LIGHT = (250, 206, 96, 255), (60, 48, 84, 255), (40, 30, 60, 255), (30, 24, 30, 255), (74, 62, 78, 255)
    MASK_A, MASK_B = (250, 244, 232, 255), (160, 226, 214, 255)
    top = p.b.neck[1] - 2.0

    def front(d, hb, hf) -> None:
        K.poly(d, [K.at(2.0, top), K.at(12.0, top), K.at(12.4, -12.0), K.at(3.6, -12.0)], SHIRT)
        K.poly(d, [K.at(8.4, top), K.at(13.0, top), K.at(13.2, -12.0), K.at(9.2, -12.0)], JACKET_DARK)
        K.poly(d, [K.at(-0.6, top + 1.0), K.at(2.8, top), K.at(3.8, -16.0), K.at(0.2, -24.0)], JACKET_LIGHT)
        # Her jacket stops at her waist; under it her trousers come up high.
        K.poly(d, [K.at(-20.0, -12.0), K.at(20.0, -12.0), K.at(20.0, 12.0), K.at(-20.0, 12.0)], TROUSER)
        K.poly(d, [K.at(6.8, -12.0), K.at(20.0, -12.0), K.at(20.0, 12.0), K.at(7.8, 12.0)], TROUSER_DARK)
        K.poly(d, [K.at(-20.0, -12.0), K.at(20.0, -12.0), K.at(20.0, -9.6), K.at(-20.0, -9.6)], SHIRT)
        # Two more of her faces hang at her belt.
        K.oval(d, K.at(-5.6, 4.0), 2.6, 3.2, MASK_A, OUTLINE, 0.5)
        K.oval(d, K.at(-1.6, 5.0), 2.4, 3.0, MASK_B, OUTLINE, 0.5)
        for x, y in ((-6.4, 3.4), (-4.8, 3.4), (-2.4, 4.4), (-0.8, 4.4)):
            K.oval(d, K.at(x, y), 0.5, 0.6, INK)

    p.torso = R.make_figure(K, ("sybil",), JACKET, JACKET_DARK, back=(7.8, 8.0, 6.4, 8.4, 8.6), front=(7.0, 9.4, 6.8, 8.8, 9.0), hem_y=4.0, top=top,
                            shoulders=((-5.0, p.b.near_shoulder[1] + 0.6), (5.8, p.b.far_shoulder[1] + 0.4)), shoulder_r=(4.8, 4.4), shade_from=40.0,
                            detail=front)
    _dress(p, skin, JACKET, JACKET_DARK, TROUSER, TROUSER_DARK, (232, 180, 80, 255), (160, 110, 50, 255), cuff=SHIRT, arm=(6.0, 5.2, 4.6), legs=(7.8, 6.2, 5.0),
           hand=0.9, neck=4.0)

    def hair_shape(d) -> None:
        # A full round of hair, larger than her head.
        K.oval(d, K.at(-1.6, -6.0), 12.4, 11.6, WHITE)

    def hair(d) -> None:
        K.poly(d, [K.at(20.0, -7.6), K.at(8.6, -7.6), K.at(5.0, -8.4), K.at(1.6, -7.0), K.at(-1.2, -4.6), K.at(-2.4, -1.0), K.at(-4.6, 2.0), K.at(-5.6, 6.0),
                   K.at(-30.0, 6.0), K.at(-30.0, -30.0), K.at(20.0, -30.0)], HAIR)
        for k in range(14):
            a = math.radians(150.0 + k * 17.0)
            K.oval(d, K.at(-1.6 + 8.6 * math.cos(a) * (0.7 + 0.3 * (k % 2)), -7.0 + 8.0 * math.sin(a) * (0.7 + 0.3 * (k % 2))), 0.9, 0.7, HAIR_LIGHT)

    def hoop(d) -> None:
        K.oval(d, K.at(-4.4, 5.4), 1.9, 2.3, None, GOLD, 0.7)  # type: ignore[arg-type]

    head = R.make_head(K, ("sybil",), *skin, skull=(0.0, -2.2, 7.8, 8.8), jaw=(2.6, 3.8, 5.4, 7.0), nose=((7.4, 0.6), (9.4, 3.0), (9.2, 4.0), (7.4, 4.2)),
                       ear=(-4.6, 1.2, 1.9, 2.6), shape=hair_shape, under=hair, over=hoop)
    eyes = R.make_eyes(K, (2.0, -0.4), (7.4, -0.6), ink=INK, iris=(170, 110, 44, 255), size=0.95, lash=0.8)
    _face(p, head, eyes,
          R.make_brows(K, [(-0.2, -4.0), (2.0, -4.8), (4.4, -4.0)], [(5.8, -4.2), (7.4, -4.8), (8.8, -4.2)], HAIR, 1.0),
          R.make_mouth(K, (5.8, 7.4), (96, 30, 60, 255), wide=0.9, lips=(150, 60, 110, 255)))

    # ---- From the front: her jacket open on her shirt, her trousers high,
    # two of her faces at her belt; the round of her hair, a hoop at each ear.
    sy = p.b.near_shoulder[1] + 0.6

    def front_jacket(d) -> None:
        K.poly(d, [K.at(-3.8, top), K.at(3.8, top), K.at(4.6, -12.0), K.at(-4.6, -12.0)], SHIRT)
        for sx in (-1.0, 1.0):
            K.poly(d, [K.at(3.8 * sx, top), K.at(6.4 * sx, top + 1.0), K.at(4.4 * sx, -18.0)], JACKET_LIGHT)
        K.poly(d, [K.at(-20.0, -12.0), K.at(20.0, -12.0), K.at(20.0, 12.0), K.at(-20.0, 12.0)], TROUSER)
        K.poly(d, [K.at(-20.0, -12.0), K.at(20.0, -12.0), K.at(20.0, -9.6), K.at(-20.0, -9.6)], SHIRT)
        K.line(d, [K.at(0.0, -9.6), K.at(0.0, 12.0)], TROUSER_DARK, 0.7)
        K.oval(d, K.at(-5.6, -3.8), 2.2, 2.8, MASK_A, OUTLINE, 0.5)
        K.oval(d, K.at(-2.2, -3.0), 2.0, 2.6, MASK_B, OUTLINE, 0.5)
        for x, y in ((-6.3, -4.4), (-4.9, -4.4), (-2.9, -3.6), (-1.5, -3.6)):
            K.oval(d, K.at(x, y), 0.45, 0.55, INK)

    def front_hair_shape(d) -> None:
        K.oval(d, K.at(0.0, -6.4), 12.4, 11.6, WHITE)
        for sx in (-1.0, 1.0):
            K.oval(d, K.at(7.6 * sx, 5.6), 2.4, 2.8, WHITE)

    def front_hair(d) -> None:
        K.poly(d, [K.at(-30.0, -30.0), K.at(30.0, -30.0), K.at(30.0, -2.0), K.at(7.0, -2.0), K.at(6.2, -6.4), K.at(3.0, -8.2), K.at(0.0, -8.6), K.at(-3.0, -8.2),
                   K.at(-6.2, -6.4), K.at(-7.0, -2.0), K.at(-30.0, -2.0)], HAIR)
        for sx in (-1.0, 1.0):
            K.poly(d, [K.at(7.0 * sx, -2.0), K.at(6.8 * sx, 3.0), K.at(6.0 * sx, 9.0), K.at(30.0 * sx, 9.0), K.at(30.0 * sx, -2.0)], HAIR)
        for k in range(16):
            a = math.radians(170.0 + k * 13.4)
            K.oval(d, K.at(9.6 * math.cos(a) * (0.72 + 0.28 * (k % 2)), -6.6 + 9.0 * math.sin(a) * (0.72 + 0.28 * (k % 2))), 0.9, 0.7, HAIR_LIGHT)

    def front_hoops(d) -> None:
        K.line(d, [K.at(-0.2, 0.8), K.at(-0.9, 3.4), K.at(0.0, 4.2), K.at(0.9, 3.4)], skin[2], 0.5)
        for sx in (-1.0, 1.0):
            K.oval(d, K.at(7.6 * sx, 5.6), 1.6, 2.0, None, GOLD, 0.7)  # type: ignore[arg-type]

    p.front_torso = R.make_front_torso(K, ("sybil",), JACKET, JACKET_DARK, [(top, 3.4), (top + 3.6, 7.2), (top + 12.5, 8.2), (-13.0, 6.4), (0.0, 8.4), (4.0, 8.6)],
                                       shoulder=(5.8, sy, 4.4, 4.6), detail=front_jacket)
    p.front_head_layers = R.front_face(
        R.make_front_head(K, ("sybil",), skin[0], skin[2], wide=7.4, jaw=5.8, chin=3.4, shape=front_hair_shape, hair=front_hair, face=front_hoops),
        R.make_front_eyes(K, ("sybil",), ink=INK, iris=(170, 110, 44, 255), spread=3.2, y=-0.4, size=0.95, lash=0.5),
        R.make_front_brows(K, ("sybil",), HAIR, spread=3.2, y=-4.0, width=1.0),
        R.make_front_mouth(K, ("sybil",), y=7.4, colour=(96, 30, 60, 255), lips=(150, 60, 110, 255), wide=0.85))
    p.front_shoe = R.make_front_shoe(K, (232, 180, 80, 255), (160, 110, 50, 255), p.b.ankle_up, wide=0.9)
    p.front_span = (7.0, 4.4)
    R.add_front_rows(p, hands="sides")

    p.set_rest(na=(-3.0, 25.0), fa=(3.0, 24.5), mouth="smile")

    @p.row
    def idle(i: int, n: int):
        # She puts a face on, and takes it off, and it is still her.
        _, s, c = loop(i, n)
        on = i in (3, 4, 5)
        return P(hip=(0.0, 0.3 + 0.3 * s), head=(0.0, 0.0, 3.0 * c), na=(9.5, -7.0) if on else (9.0, 10.0), nh="fist", eyes="closed" if i == n - 2 else "open",
                 brows=1.0 if on else 0.0)

    _walk(p, (-3.0, 25.0), (3.0, 24.5), reach=8.4, lean=2.0, swing=7.0)

    @p.row
    def talk(i: int, n: int):
        _, s, c = loop(i, n)
        return P(hip=(0.0, 0.4 * s), head=(0.3, 0.0, 3.0 * s), na=(14.0 + 3.0 * c, 5.0 - 5.0 * max(0.0, s)), nh="open", fa=(17.0 - 3.0 * c, 8.0), fh="open",
                 mouth=("open", "smile", "big", "smile")[i % 4], brows=1.0 if s > 0.3 else 0.0)

    @p.row
    def interact(i: int, n: int):
        # One vote each. She brought a great many votes.
        cast_ = P(hip=(1.0, 1.0), lean=6.0, na=(24.0, 2.0), nh="flat", mouth="big", brows=1.0)
        return p.keys(shot(i, n), [(0.0, P()), (0.3, cast_), (0.5, dict(cast_, na=(22.0, 6.0))), (0.7, cast_), (0.9, dict(cast_, na=(22.0, 6.0))), (1.0, P())])

    def effects(ctx) -> List[Stamp]:
        out: List[Stamp] = []
        if ctx.anim == "idle" and ctx.i in (3, 4, 5):
            out.append((_mask(K, MASK_A, PAPER_DARK, True), (ctx.head[0] + 4.6, ctx.head[1] + 1.4), "mask", ctx.turn))
        elif ctx.anim == "talk":
            # The others of her, a little behind her and a little faint.
            for k, (dx, fill) in enumerate(((-22.0, MASK_B), (-34.0, MASK_A))):
                out.append((_mask(K, fill, PAPER_DARK, k == 0, 0.8), (ctx.head[0] + dx, ctx.head[1] + 3.0 * math.sin(ctx.phase + k * 2.0)), f"mask_{k}", 0.0))
        elif ctx.anim == "interact" and 0.25 <= ctx.u <= 0.95:
            count = 1 + int((ctx.u - 0.25) / 0.24)
            for k in range(min(3, count)):
                out.append((_letter(K, None, 0.7, "tick"), (ctx.hand[0] + 14.0 + 5.0 * k, ctx.hand[1] + 4.0 - 7.0 * k), f"vote_{k}", -10.0))
        return out

    p.effects = effects

    # ---- In the round: her head from the side, drawn by the cast's makers in
    # the numbers of a profile (the full round of her hair, a hoop under her
    # ear); 3D for the views her art does not draw.

    def side_hair_shape(d) -> None:
        K.oval(d, K.at(-2.6, -6.0), 12.4, 11.6, WHITE)

    def side_hair(d) -> None:
        K.poly(d, [K.at(20.0, -7.6), K.at(9.4, -7.6), K.at(5.8, -8.4), K.at(2.4, -7.0), K.at(0.8, -4.6), K.at(0.6, -1.0), K.at(-1.6, 2.0), K.at(-2.8, 6.0),
                   K.at(-30.0, 6.0), K.at(-30.0, -30.0), K.at(20.0, -30.0)], HAIR)
        for k in range(14):
            a = math.radians(150.0 + k * 17.0)
            K.oval(d, K.at(-2.6 + 8.6 * math.cos(a) * (0.7 + 0.3 * (k % 2)), -7.0 + 8.0 * math.sin(a) * (0.7 + 0.3 * (k % 2))), 0.9, 0.7, HAIR_LIGHT)

    def side_hoop(d) -> None:
        K.oval(d, K.at(-1.4, 5.6), 1.9, 2.3, None, GOLD, 0.7)  # type: ignore[arg-type]

    side_head = R.make_head(K, ("sybil_side",), *skin, skull=(0.0, -2.2, 8.8, 8.8), jaw=(3.4, 3.8, 6.0, 7.0),
                            nose=((8.2, 0.6), (10.2, 3.0), (10.0, 4.0), (8.2, 4.2)), ear=(-1.6, 1.2, 1.9, 2.6), shape=side_hair_shape, under=side_hair,
                            over=side_hoop, far_shade=False)
    side_eyes = R.make_eyes(K, (6.6, -0.4), None, ink=INK, iris=(170, 110, 44, 255), size=0.95, lash=0.8)
    side_brows = R.make_brows(K, [(4.4, -4.0), (6.6, -4.8), (8.8, -4.2)], None, HAIR, 1.0)
    side_mouth = R.make_mouth(K, (8.2, 7.4), (96, 30, 60, 255), wide=0.6, lips=(150, 60, 110, 255))
    afro = ((0.0, -6.0, -3.6), (12.0, 11.6, 10.4))
    ROUNDS["sybil"] = C.Round(
        "Sybil", C.PersonBody(p, heads={"side": lambda pose: [(side_head(), "head"), (side_eyes(str(pose["eyes"])), "eyes"),
                                                              (side_brows(R.brow_mood(pose)), "brows"), (side_mouth(str(pose["mouth"])), "mouth")]}),
        C.Look(
            # The full round of her hair, larger than her head, with its light;
            # a gold hoop at each ear.
            C.auto_head(p, head, eyes, hair=lambda u, v: (v < -7.0 + 1.4 * np.clip(np.abs(u) / 60.0, 0.0, 1.0)) | (np.abs(u) > 60.0),
                        hair_colour=HAIR, hair_shade=mix(HAIR, INK, 0.4), volumes=[afro],
                        lines=[O.circle(*O.on_ellipsoid(*afro, u, v, 0.2), 0.8, None, fill=HAIR_LIGHT, slack=1.0)
                               for u in range(-165, 180, 30) for v in (-14.0, -8.0, -2.0)]
                        + [O.circle((7.2 * sx, 5.6, 0.2), (sx, 0.0, 0.2), 2.0, GOLD, 0.7, slack=1.2) for sx in (-1.0, 1.0)]),
            # Her short jacket open on her shirt; under it her trousers come
            # up high; two more of her faces at her belt.
            C.auto_trunk(p, [W.Opening(24.0, SHIRT, top=top, bottom=-12.0), W.Lapels(24.0, top, -16.0, 12.0, JACKET_LIGHT),
                             W.Band(-12.0, 6.0, TROUSER), W.Band(-12.0, -9.6, SHIRT), W.Down(0.0, -9.6, 6.0, TROUSER_DARK),
                             W.Dot(-34.0, 4.0, 2.8, MASK_A), W.Dot(-12.0, 5.0, 2.6, MASK_B),
                             W.Dot(-38.0, 3.4, 0.5, INK), W.Dot(-30.0, 3.4, 0.5, INK), W.Dot(-16.0, 4.4, 0.5, INK), W.Dot(-8.0, 4.4, 0.5, INK)])),
        # She stands square, her arms down at her sides.
        C.Stance(hands={"r": C.Hand(l=-7.4, pole=(-0.4, 0.0, -1.0)), "l": C.Hand(l=7.4, pole=(0.4, 0.0, -1.0))}, stagger=1.8))
    _meta("sybil", "Sybil", ["hub", "peaceful", "cryptography_crew", "many_identities"],
          "Sybil personifies a Sybil attack: one actor presenting many apparently independent identities to overwhelm systems that count "
          "participants rather than establishing who they are. The name comes from the established security term, itself derived from the famous "
          "multiple-personality case and book.",
          "Use as a crowd impostor, vote manipulator, clone enemy, or identity-system tutorial. She should multiply faces cheaply, exploit "
          "one-entity-one-vote assumptions, and become weaker when identities require costly proof or persistent history.",
          ["How many of me did you count?", "One vote each. I brought a great many votes.", "Wrong is the entire trick."])


# =============================================================================
# Trent: the trusted third party. Everyone trusts him. That is the wound.
# =============================================================================


def _trent() -> None:
    p = _person("trent", 183.0, girth=0.8, stoop=1.6)
    K, P = p.K, p.P
    skin = PALE
    ROBE, ROBE_DARK, ROBE_LIGHT = (50, 110, 82, 255), (30, 72, 60, 255), (96, 156, 118, 255)
    TRIM, BEARD, BEARD_DARK, CAP = GOLD, (240, 238, 230, 255), (176, 180, 190, 255), (36, 84, 66, 255)
    top = p.b.neck[1] - 2.0

    def front(d, hb, hf) -> None:
        # Gold down the front and round the hem, and the chain of his office.
        K.poly(d, [K.at(4.0, top), K.at(7.6, top), K.at(9.4 + hf, 50.0), K.at(5.4 + hf * 0.5, 50.0)], TRIM)
        K.poly(d, [K.at(-20.0 - hb, p.b.hip_up - 9.0), K.at(20.0 + hf, p.b.hip_up - 9.0), K.at(20.0 + hf, p.b.hip_up), K.at(-20.0 - hb, p.b.hip_up)], TRIM)
        K.line(d, [K.at(-8.0, top + 6.0), K.at(0.0, -17.0), K.at(8.6, top + 7.0)], GOLD_DARK, 1.0)
        K.oval(d, K.at(0.4, -15.0), 2.6, 2.6, GOLD, OUTLINE, 0.5)
        K.tick(d, K.at(0.4, -15.0), 1.3, ROBE_DARK, 0.6)
        for x in (-7.4, -2.6):
            K.line(d, [K.at(x, 2.0), K.at(x - 1.8 - hb * 0.4, 42.0)], ROBE_LIGHT, 0.6)

    p.torso = R.make_torso(K, ("trent",), ROBE, ROBE_DARK, back=(10.6, 11.4, 11.0, 14.0), front=(9.4, 11.2, 11.4, 13.2), hem_y=p.b.hip_up - 5.0, top=top,
                           shoulders=((-6.4, p.b.near_shoulder[1] + 0.6), (7.2, p.b.far_shoulder[1] + 0.4)), shoulder_r=(6.2, 5.6), shade_from=11.0,
                           detail=front)
    _dress(p, skin, ROBE, ROBE_DARK, ROBE, ROBE_DARK, (92, 66, 48, 255), (56, 40, 32, 255), cuff=TRIM, arm=(8.8, 8.6, 8.8), legs=(6.6, 5.6, 4.8), hand=1.05)

    def shape(d) -> None:
        # A soft flat cap, and a white beard down to his chest.
        K.poly(d, [K.at(-9.4, -8.0), K.at(-8.0, -13.6), K.at(2.0, -15.0), K.at(9.4, -11.6), K.at(9.6, -8.0)], WHITE)
        K.poly(d, [K.at(-3.6, 4.0), K.at(9.4, 5.0), K.at(9.0, 12.0), K.at(6.4, 20.0), K.at(3.6, 25.0), K.at(0.0, 19.0), K.at(-2.6, 11.0)], WHITE)

    def under(d) -> None:
        K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, -7.6), K.at(-20.0, -7.0)], CAP)
        K.line(d, [K.at(-9.4, -7.4), K.at(10.0, -8.0)], GOLD, 1.0)
        K.poly(d, [K.at(-3.2, -6.8), K.at(-6.4, -6.6), K.at(-7.0, 3.0), K.at(-5.0, 5.0), K.at(-3.6, 1.0)], BEARD)

    def over(d) -> None:
        K.poly(d, [K.at(-3.8, 3.6), K.at(1.0, 5.0), K.at(5.0, 4.6), K.at(10.0, 5.4), K.at(10.0, 12.0), K.at(6.4, 20.0), K.at(3.6, 26.0), K.at(0.0, 19.0),
                   K.at(-2.8, 11.0)], BEARD)
        for x0, y0, x1, y1 in ((0.0, 8.0, 2.4, 19.0), (3.6, 9.0, 4.4, 21.0), (7.0, 8.0, 6.0, 17.0)):
            K.line(d, [K.at(x0, y0), K.at(x1, y1)], BEARD_DARK, 0.6)
        K.line(d, [K.at(3.4, 7.2), K.at(5.8, 7.9), K.at(8.0, 7.2)], (130, 80, 84, 255), 0.8)

    head = R.make_head(K, ("trent",), *skin, skull=(0.0, -2.4, 8.2, 9.0), jaw=(2.6, 4.2, 6.0, 7.4), nose=((7.2, -0.8), (10.6, 3.2), (10.0, 4.8), (7.2, 5.0)),
                       ear=(-5.0, 0.4, 2.2, 3.2), shape=shape, under=under, over=over)
    no_mouth = lambda mode: None  # noqa: E731  (his beard is over it)
    eyes = R.make_eyes(K, (1.4, -0.6), (7.0, -0.8), ink=INK, white=None, lid=skin[2])
    _face(p, head, eyes,
          R.make_brows(K, [(-1.4, -3.8), (1.4, -4.8), (4.2, -4.0)], [(5.8, -4.2), (7.2, -4.8), (8.8, -4.0)], BEARD, 1.5, under=BEARD_DARK), no_mouth)

    # ---- From the front: gold down his robe and round its hem, the chain of
    # his office, his cap, and his beard down to his chest.
    sy = p.b.near_shoulder[1] + 0.6
    hem = p.b.hip_up - 5.0

    def front_robe(d) -> None:
        K.poly(d, [K.at(-1.8, top), K.at(1.8, top), K.at(2.6, hem + 6.0), K.at(-2.6, hem + 6.0)], TRIM)
        K.poly(d, [K.at(-30.0, hem - 4.0), K.at(30.0, hem - 4.0), K.at(30.0, hem + 6.0), K.at(-30.0, hem + 6.0)], TRIM)
        K.line(d, [K.at(-8.4, top + 6.0), K.at(0.0, -15.0), K.at(8.4, top + 6.0)], GOLD_DARK, 1.0)
        K.oval(d, K.at(0.0, -13.0), 2.6, 2.6, GOLD, OUTLINE, 0.5)
        K.tick(d, K.at(0.0, -13.0), 1.3, ROBE_DARK, 0.6)
        for x in (-6.0, 6.0):
            K.line(d, [K.at(x, 2.0), K.at(x * 1.5, hem - 6.0)], ROBE_LIGHT, 0.6)

    def front_shape(d) -> None:
        K.poly(d, [K.at(-9.6, -7.6), K.at(-8.8, -13.6), K.at(0.0, -15.2), K.at(8.8, -13.6), K.at(9.6, -7.6)], WHITE)
        K.poly(d, [K.at(-7.4, 3.0), K.at(7.4, 3.0), K.at(6.4, 13.0), K.at(3.4, 22.0), K.at(0.0, 26.0), K.at(-3.4, 22.0), K.at(-6.4, 13.0)], WHITE)

    def front_cap(d) -> None:
        for sx in (-1.0, 1.0):
            K.poly(d, [K.at(6.2 * sx, -8.0), K.at(20.0 * sx, -8.0), K.at(20.0 * sx, 4.0), K.at(7.0 * sx, 4.0)], BEARD)
        K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, -7.2), K.at(-20.0, -7.2)], CAP)
        K.line(d, [K.at(-9.8, -7.6), K.at(9.8, -7.6)], GOLD, 1.0)

    def front_beard(d) -> None:
        K.line(d, [K.at(-0.3, 0.4), K.at(-1.5, 3.4), K.at(0.0, 4.2), K.at(1.5, 3.4)], skin[2], 0.7)
        K.poly(d, [K.at(-7.6, 2.4), K.at(-4.0, 5.6), K.at(0.0, 4.8), K.at(4.0, 5.6), K.at(7.6, 2.4), K.at(6.4, 13.0), K.at(3.4, 22.0), K.at(0.0, 26.0), K.at(-3.4, 22.0),
                   K.at(-6.4, 13.0)], BEARD)
        for x0, y0, x1, y1 in ((-3.4, 9.0, -2.4, 20.0), (0.0, 10.0, 0.0, 23.0), (3.4, 9.0, 2.4, 20.0)):
            K.line(d, [K.at(x0, y0), K.at(x1, y1)], BEARD_DARK, 0.6)
        K.line(d, [K.at(-2.4, 7.4), K.at(0.0, 8.0), K.at(2.4, 7.4)], (130, 80, 84, 255), 0.8)

    p.front_torso = R.make_front_torso(K, ("trent",), ROBE, ROBE_DARK, [(top, 4.6), (top + 3.6, 10.2), (-24.0, 11.0), (-8.0, 11.2), (hem, 14.0)],
                                       shoulder=(8.2, sy, 5.4, 5.6), detail=front_robe)
    p.front_head_layers = R.front_face(
        R.make_front_head(K, ("trent",), skin[0], skin[2], wide=8.0, jaw=6.4, chin=3.6, ears=skin[0], shape=front_shape, hair=front_cap, face=front_beard),
        R.make_front_eyes(K, ("trent",), white=None, ink=INK, spread=3.4, y=-0.6), R.make_front_brows(K, ("trent",), BEARD, spread=3.4, y=-4.0, width=1.5))
    p.front_shoe = R.make_front_shoe(K, (92, 66, 48, 255), (56, 40, 32, 255), p.b.ankle_up)
    p.front_span = (9.0, 5.0)
    R.add_front_rows(p)

    #: His hands in his sleeves, across him.
    held_near, held_far = (7.0, 14.0), (-1.0, 22.0)
    p.set_rest(na=held_near, fa=held_far, nh="flat")

    @p.row
    def idle(i: int, n: int):
        # He carries what everybody has given him to hold, and it is heavy.
        _, s, _c = loop(i, n)
        return P(hip=(0.0, 0.5 + 0.4 * s), lean=3.0, head=(0.3, 0.2 * s, 4.0 + 1.5 * s), eyes="closed" if i in (n - 2, n - 3) else "open")

    _walk(p, held_near, held_far, reach=6.6, lift=3.0, lean=4.0, nh="flat")

    @p.row
    def talk(i: int, n: int):
        _, s, _c = loop(i, n)
        return P(hip=(0.0, 0.3 * s), lean=3.0, head=(0.3, 0.0, 3.0 + 2.0 * s), na=(14.0, 6.0 - 3.0 * max(0.0, s)), nh="open", brows=1.0 if s > 0.3 else 0.0)

    @p.row
    def interact(i: int, n: int):
        # He sets his seal on it, and now it is true for everybody.
        up = P(lean=1.0, na=(12.0, -4.0), nh="fist", brows=-1.0)
        down = P(hip=(1.0, 2.0), lean=10.0, na=(21.0, 10.0), nh="fist")
        return p.keys(shot(i, n), [(0.0, P()), (0.3, up), (0.5, down), (0.8, down), (1.0, P())])

    def seal(size: float):
        def shape(d) -> None:
            for k in range(10):
                a = math.tau * k / 10.0
                K.oval(d, K.at(size * 0.86 * math.cos(a), size * 0.86 * math.sin(a)), size * 0.3, size * 0.3, WHITE)
            K.oval(d, K.home, size * 0.9, size * 0.9, WHITE)

        return K.solid(("seal", size), shape, SEAL, lambda d: K.tick(d, K.home, size * 0.42, GOLD, 0.9), outline=1.0, rim=0.3, shade=0.4,
                       shade_colour=(128, 30, 44, 255))

    def effects(ctx) -> List[Stamp]:
        out: List[Stamp] = []
        if ctx.anim == "interact" and ctx.u >= 0.5:
            out.append((_letter(K, None, 1.0), (ctx.hand[0] + 13.0, ctx.hand[1] + 9.0), "letter", 0.0))
            out.append((seal(3.4), (ctx.hand[0] + 13.0, ctx.hand[1] + 9.6), "seal", 0.0))
            if ctx.u < 0.75:
                out.append((R.burst(K, 9.0, GOLD, GOLD_DARK), (ctx.hand[0] + 13.0, ctx.hand[1] + 9.0), "burst", 0.0))
        return out

    p.effects = effects

    # ---- In the round: his head from the side, drawn by the cast's makers in
    # the numbers of a profile (his cap, the white hair under it behind his
    # ear, his beard down to his chest); 3D for the views his art does not
    # draw: the cap as a hat, the beard, his robe with its gold and the chain
    # of his office.

    def side_shape(d) -> None:
        K.poly(d, [K.at(-10.4, -8.0), K.at(-9.0, -13.6), K.at(1.0, -15.0), K.at(9.6, -11.6), K.at(9.8, -8.0)], WHITE)
        K.poly(d, [K.at(-0.4, 4.0), K.at(10.2, 5.0), K.at(9.8, 12.0), K.at(7.2, 20.0), K.at(4.4, 25.0), K.at(1.0, 19.0), K.at(-1.2, 11.0)], WHITE)

    def side_under(d) -> None:
        K.poly(d, [K.at(0.6, -7.2), K.at(-20.0, -7.2), K.at(-20.0, 5.0), K.at(-3.0, 5.0), K.at(-0.6, 1.4)], BEARD)
        K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, -7.6), K.at(-20.0, -7.0)], CAP)
        K.line(d, [K.at(-10.4, -7.2), K.at(10.0, -8.0)], GOLD, 1.0)

    def side_over(d) -> None:
        K.poly(d, [K.at(0.2, 3.6), K.at(4.4, 5.0), K.at(8.0, 4.6), K.at(11.0, 5.4), K.at(10.8, 12.0), K.at(7.2, 20.0), K.at(4.4, 26.0), K.at(1.0, 19.0),
                   K.at(-1.2, 11.0)], BEARD)
        for x0, y0, x1, y1 in ((2.0, 8.0, 3.4, 19.0), (5.0, 9.0, 5.4, 21.0), (8.0, 8.0, 7.0, 17.0)):
            K.line(d, [K.at(x0, y0), K.at(x1, y1)], BEARD_DARK, 0.6)
        K.line(d, [K.at(7.4, 7.4), K.at(9.0, 7.9), K.at(10.4, 7.4)], (130, 80, 84, 255), 0.8)

    side_head = R.make_head(K, ("trent_side",), *skin, skull=(0.0, -2.4, 9.2, 9.0), jaw=(3.4, 4.2, 6.6, 7.4),
                            nose=((8.0, -0.8), (11.4, 3.2), (10.8, 4.8), (8.0, 5.0)), ear=(-1.6, 0.4, 2.2, 3.2), shape=side_shape, under=side_under,
                            over=side_over, far_shade=False)
    side_eyes = R.make_eyes(K, (6.4, -0.6), None, ink=INK, white=None, lid=skin[2])
    side_brows = R.make_brows(K, [(4.0, -3.8), (6.4, -4.8), (8.8, -4.0)], None, BEARD, 1.5, under=BEARD_DARK)
    cap_3d = W.Hat(crown=[O.Ring(-7.0, 0.0, 0.0, 8.8, 8.8), O.Ring(-11.0, 0.0, -0.4, 9.4, 9.0), O.Ring(-14.0, 0.0, -0.4, 7.8, 7.4),
                          O.Ring(-15.2, 0.0, -0.4, 4.2, 4.0), O.Ring(-15.4, 0.0, -0.4, 0.0, 0.0)],
                   brim=None, garment=W.Garment(CAP, mix(CAP, INK, 0.4), [W.Band(-8.0, -6.6, GOLD), W.Shade()]), under=CAP)
    beard_3d = [O.Ring(4.0, 0.0, 3.0, 6.8, 4.8), O.Ring(9.0, 0.0, 4.4, 6.6, 4.2), O.Ring(14.0, 0.0, 5.2, 5.2, 3.6), O.Ring(20.0, 0.0, 5.6, 3.0, 2.4),
                O.Ring(25.0, 0.0, 5.4, 0.4, 0.4)]
    ROUNDS["trent"] = C.Round(
        "Trent", C.PersonBody(p, heads={"side": lambda pose: [(side_head(), "head"), (side_eyes(str(pose["eyes"])), "eyes"),
                                                              (side_brows(R.brow_mood(pose)), "brows")]}),
        C.Look(
            # White hair under his cap round the back of his head, and his
            # white beard to his chest.
            C.auto_head(p, head, eyes, hair=lambda u, v: (np.abs(u) > 62.0) & (v < 5.0), hair_colour=BEARD, hair_shade=BEARD_DARK,
                        volumes=[((0.0, -1.0, -2.6), (8.6, 6.4, 7.0))], beard=beard_3d,
                        lines=[O.curve([(x, 9.0, 6.4), (x * 0.9, 16.0, 6.0), (x * 0.6, 21.0, 5.6)], BEARD_DARK, 0.6) for x in (-2.4, 0.0, 2.4)]),
            # His long robe: gold down its front and round its hem, the chain
            # of his office and its seal on his chest, the folds of it.
            C.auto_trunk(p, [W.Strip(0.0, top, hem + 6.0, 1.8, TRIM, flare=0.8), W.Band(hem - 4.0, hem + 6.0, TRIM),
                             W.Swag(-42.0, 42.0, -15.0, (-15.0 - top - 6.0, -15.0 - top - 6.0), GOLD_DARK, width=0.5),
                             W.Dot(0.0, -13.0, 2.6, GOLD), W.Dot(0.0, -13.0, 1.0, ROBE_DARK),
                             W.Down(28.0, 2.0, hem - 6.0, ROBE_LIGHT, spread=6.0), W.Down(-28.0, 2.0, hem - 6.0, ROBE_LIGHT, spread=6.0),
                             W.Down(180.0, top + 4.0, hem - 4.0, ROBE_DARK)]),
            head_pieces=[cap_3d]),
        # His hands in his sleeves, across him.
        C.Stance(hands={"r": C.Hand(at=(2.4, -14.0, 11.0), pole=(-0.4, 1.0, -0.2), mode="flat"),
                        "l": C.Hand(at=(-1.6, -15.0, 11.0), pole=(0.4, 1.0, -0.2), mode="flat")}, stagger=1.6))
    _meta("trent", "Trent", ["hub", "peaceful", "cryptography_crew", "trusted_third_party"],
          "Trent is the trusted third party in security examples, personified as an elder whose authority is both useful and dangerously central. "
          "The character should embody the convenience and fragility of a system that works because everyone assumes one person will remain "
          "trustworthy.",
          "Use as a certificate authority, gatekeeper, elder, key distributor, or compromised-trust plot device. Games may let players rely on "
          "Trent, distribute trust around him, or confront the consequences of one central assumption failing.",
          ["Everyone trusts me. That's the job, and that's the wound.", "The whole web of trust is just people guessing about each other.",
           "Spread the trust around."])


# =============================================================================
# Trudy: the intruder. Every wall is a question about its door.
# =============================================================================


def _trudy() -> None:
    # A small wiry woman: all of her is close to the ground.
    p = _person("trudy", 157.0, woman=True)
    K, P = p.K, p.P
    skin = PALE
    SUIT, SUIT_DARK, SUIT_LIGHT = (58, 92, 76, 255), (36, 60, 54, 255), (96, 136, 112, 255)
    BELT, GLOVE, GLOVE_DARK, HAIR, HAIR_LIGHT = (176, 140, 84, 255), (44, 44, 54, 255), (26, 26, 34, 255), (30, 28, 38, 255), (78, 76, 98, 255)
    top = p.b.neck[1] - 2.0

    def front(d, hb, hf) -> None:
        # One suit from neck to ankle, zipped, with a belt of small tools.
        K.line(d, [K.at(5.4, top + 1.0), K.at(6.0, 6.0)], SUIT_LIGHT, 0.9)
        K.poly(d, [K.at(-12.0, -1.0), K.at(13.0, 0.0), K.at(13.0, 3.4), K.at(-12.0, 2.4)], BELT)
        for x in (-7.0, -3.4, 0.6):
            K.rrect(d, K.home[0] + x, K.home[1] + 1.0, K.home[0] + x + 2.6, K.home[1] + 6.0, 0.5, mix(BELT, INK, 0.3))
        K.poly(d, [K.at(2.6, top - 1.0), K.at(8.8, top - 1.0), K.at(8.4, top + 3.0), K.at(3.0, top + 3.0)], SUIT_DARK)

    p.torso = R.make_figure(K, ("trudy",), SUIT, SUIT_DARK, back=(6.8, 7.0, 5.6, 7.6, 7.8), front=(6.0, 8.0, 5.8, 7.8, 8.0), hem_y=5.0, top=top,
                            shoulders=((-4.4, p.b.near_shoulder[1] + 0.6), (5.0, p.b.far_shoulder[1] + 0.4)), shoulder_r=(4.2, 3.8), shade_from=6.0, detail=front)
    _dress(p, (GLOVE, GLOVE_DARK, GLOVE_DARK), SUIT, SUIT_DARK, SUIT, SUIT_DARK, (44, 44, 54, 255), (24, 24, 32, 255), arm=(5.6, 4.8, 4.2),
           legs=(7.4, 5.8, 4.6), hand=0.85)
    p.neck = R.make_neck(K, skin[1], 3.8)

    def hair_shape(d) -> None:
        K.oval(d, K.at(-1.2, -4.0), 9.2, 9.0, WHITE)
        K.poly(d, [K.at(-9.4, -4.0), K.at(-9.8, 5.6), K.at(-3.0, 6.4), K.at(-1.0, 0.0)], WHITE)

    def hair(d) -> None:
        # Black, cut short at her jaw, a fringe straight across.
        K.poly(d, [K.at(20.0, -5.6), K.at(1.4, -5.2), K.at(-0.8, -3.0), K.at(-1.6, 1.0), K.at(-1.8, 7.0), K.at(-20.0, 7.0), K.at(-20.0, -26.0),
                   K.at(20.0, -26.0)], HAIR)
        K.line(d, [K.at(5.0, -10.0), K.at(-3.0, -8.6), K.at(-7.4, -2.0), K.at(-7.8, 4.0)], HAIR_LIGHT, 0.7)

    def mask():
        # A strip of black cloth over her eyes. It hides nothing. She likes it.
        def paint(d) -> None:
            K.poly(d, [K.at(-1.6, -2.6), K.at(9.6, -3.0), K.at(9.8, 1.4), K.at(-1.4, 2.0)], GLOVE)
            for x in (1.8, 7.2):
                K.oval(d, K.at(x, -0.4), 1.5, 1.2, (240, 240, 236, 255))
                K.oval(d, K.at(x + 0.3, -0.3), 0.8, 0.9, INK)

        return K.piece(("trudy_mask",), paint)

    head = R.make_head(K, ("trudy",), *skin, skull=(0.0, -2.2, 7.6, 8.6), jaw=(2.4, 3.8, 5.2, 6.8), nose=((7.2, 0.6), (9.0, 3.2), (8.6, 4.2), (7.2, 4.6)),
                       ear=None, shape=hair_shape, under=hair)
    no_eyes = lambda mode: None  # noqa: E731  (her eyes are in her mask)
    _face(p, head, no_eyes, R.make_brows(K, [(-0.2, -4.6), (2.0, -5.2), (4.4, -4.8)], [(5.8, -4.9), (7.2, -5.2), (8.6, -4.8)], HAIR, 0.9),
          R.make_mouth(K, (5.4, 7.2), (140, 60, 76, 255), wide=0.75, lips=(204, 104, 116, 255)), mask)

    # ---- From the front: the zip of her suit, her belt of tools, her fringe
    # straight across, and the strip of cloth over her eyes.
    sy = p.b.near_shoulder[1] + 0.6

    def front_suit(d) -> None:
        K.poly(d, [K.at(-3.4, top - 1.0), K.at(3.4, top - 1.0), K.at(3.0, top + 3.0), K.at(-3.0, top + 3.0)], SUIT_DARK)
        K.line(d, [K.at(0.0, top + 3.0), K.at(0.0, 6.0)], SUIT_LIGHT, 0.9)
        K.poly(d, [K.at(-20.0, -1.0), K.at(20.0, -1.0), K.at(20.0, 2.6), K.at(-20.0, 2.6)], BELT)
        for x in (-6.4, -3.0, 3.4):
            K.rrect(d, K.home[0] + x, K.home[1] + 1.0, K.home[0] + x + 2.6, K.home[1] + 6.0, 0.5, mix(BELT, INK, 0.3))

    def front_hair_shape(d) -> None:
        K.oval(d, K.at(0.0, -4.2), 9.2, 8.8, WHITE)
        K.poly(d, [K.at(-9.2, -4.0), K.at(-9.6, 6.2), K.at(9.6, 6.2), K.at(9.2, -4.0)], WHITE)

    def front_hair(d) -> None:
        K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, -5.4), K.at(-20.0, -5.4)], HAIR)
        for sx in (-1.0, 1.0):
            K.poly(d, [K.at(6.8 * sx, -5.4), K.at(6.6 * sx, 3.0), K.at(5.6 * sx, 7.0), K.at(30.0 * sx, 7.0), K.at(30.0 * sx, -5.4)], HAIR)
            K.line(d, [K.at(8.0 * sx, -4.0), K.at(8.2 * sx, 4.0)], HAIR_LIGHT, 0.7)
        K.line(d, [K.at(-5.0, -9.6), K.at(0.0, -10.4), K.at(5.0, -9.6)], HAIR_LIGHT, 0.7)

    def front_nose(d) -> None:
        K.line(d, [K.at(-0.2, 0.8), K.at(-0.8, 3.4), K.at(0.0, 4.2), K.at(0.8, 3.4)], skin[2], 0.5)

    def front_mask():
        def paint(d) -> None:
            K.poly(d, [K.at(-7.0, -2.8), K.at(7.0, -2.8), K.at(6.8, 1.8), K.at(-6.8, 1.8)], GLOVE)
            for x in (-3.0, 3.0):
                K.oval(d, K.at(x, -0.5), 1.5, 1.2, (240, 240, 236, 255))
                K.oval(d, K.at(x, -0.4), 0.8, 0.9, INK)

        return K.piece(("trudy_front_mask",), paint)

    p.front_torso = R.make_front_torso(K, ("trudy",), SUIT, SUIT_DARK, [(top, 3.2), (top + 3.6, 6.6), (top + 12.5, 7.4), (-13.0, 5.8), (0.0, 7.6), (5.0, 7.8)],
                                       shoulder=(5.0, sy, 3.8, 4.0), detail=front_suit)
    p.front_head_layers = R.front_face(
        R.make_front_head(K, ("trudy",), skin[0], skin[2], wide=7.2, jaw=5.6, chin=3.2, shape=front_hair_shape, hair=front_hair, face=front_nose),
        mouth=R.make_front_mouth(K, ("trudy",), y=7.2, colour=(140, 60, 76, 255), lips=(204, 104, 116, 255), wide=0.7), extra=[(front_mask, "mask")])
    p.front_shoe = R.make_front_shoe(K, (44, 44, 54, 255), (24, 24, 32, 255), p.b.ankle_up, wide=0.85)
    p.front_span = (6.6, 4.2)
    R.add_front_rows(p, hands="sides")

    #: Low, and ready: her hands where a wall will be.
    ready_near, ready_far = (9.0, 12.0), (12.0, 9.0)
    p.set_rest(hip=(0.0, 3.0), lean=8.0, na=ready_near, fa=ready_far, nh="open", fh="open", nf=(-6.0, 0.0, 0.0), ff=(7.0, 0.0, 0.0), mouth="smile")

    @p.row
    def idle(i: int, n: int):
        # She looks at the room as a list of ways in.
        _, s, c = loop(i, n)
        return P(hip=(0.0, 3.0 + 0.5 * s), lean=8.0 + 2.0 * c, head=(0.4 * c, 0.0, 5.0 * c), brows=1.0 if c > 0.5 else 0.0)

    def walk(i: int, n: int):
        # On her toes.
        ph, s, c = loop(i, n)
        nf, ff = R.stride(ph, 7.6, 5.4)
        return P(hip=(0.5, 3.0 + 0.8 * math.cos(2.0 * ph)), lean=12.0, head=(0.0, 0.0, -4.0), na=(ready_near[0] - 2.0 * c, ready_near[1]),
                 fa=(ready_far[0] + 2.0 * c, ready_far[1]), nf=(nf[0], nf[1], nf[2] + 10.0), ff=(ff[0], ff[1], ff[2] + 10.0))

    p.poses["walk"] = walk

    @p.row
    def talk(i: int, n: int):
        _, s, _c = loop(i, n)
        return P(hip=(0.0, 1.0 + 0.3 * s), lean=2.0, head=(0.3, 0.0, 3.0 * s), na=(13.0, 4.0 - 3.0 * max(0.0, s)), nh="point", fa=(3.0, 24.0), fh="soft",
                 mouth=("open", "smile", "big", "smile")[i % 4], brows=1.0 if s > 0.3 else 0.0)

    @p.row
    def interact(i: int, n: int):
        # Both hands at the lock, and her ear close. It gives.
        work = P(hip=(2.0, 6.0), lean=16.0, head=(1.0, 0.0, 8.0), na=(22.0, 6.0), fa=(20.0, 9.0), nh="fist", fh="fist", brows=-1.0, mouth="flat")
        return p.keys(shot(i, n), [(0.0, P()), (0.25, work), (0.5, dict(work, na=(22.0, 7.5))), (0.75, dict(work, mouth="smile", brows=1.0)), (1.0, P())])

    def effects(ctx) -> List[Stamp]:
        out: List[Stamp] = []
        if ctx.anim == "interact" and 0.2 <= ctx.u <= 0.9:
            out.append((_padlock(K, ctx.u > 0.6), (ctx.hand[0] + 12.0, ctx.hand[1] + 1.0), "padlock", 0.0))
            if 0.6 < ctx.u < 0.8:
                out.append((_spark(K, 3.0, GOLD), (ctx.hand[0] + 17.0, ctx.hand[1] - 9.0), "spark", 0.0))
        return out

    p.effects = effects

    # ---- In the round. Her head from the side, drawn as the cast draws a
    # head in the numbers of a profile: her black hair cut at her jaw, the
    # fringe straight across, the strip of cloth over her eye.
    def side_hair_shape(d) -> None:
        K.oval(d, K.at(-1.8, -4.0), 9.8, 9.0, WHITE)
        K.poly(d, [K.at(-10.2, -4.0), K.at(-10.6, 5.6), K.at(-3.6, 6.6), K.at(-1.6, 0.0)], WHITE)

    def side_hair(d) -> None:
        K.poly(d, [K.at(20.0, -5.6), K.at(2.0, -5.2), K.at(0.8, -3.0), K.at(0.4, 1.0), K.at(0.2, 7.0), K.at(-20.0, 7.0), K.at(-20.0, -26.0),
                   K.at(20.0, -26.0)], HAIR)
        K.line(d, [K.at(5.4, -10.4), K.at(-3.6, -8.8), K.at(-8.2, -2.0), K.at(-8.6, 4.0)], HAIR_LIGHT, 0.7)

    def side_mask(d) -> None:
        K.poly(d, [K.at(-0.4, -2.8), K.at(10.2, -3.0), K.at(10.2, 1.6), K.at(-0.2, 2.0)], GLOVE)
        K.oval(d, K.at(6.6, -0.4), 1.5, 1.2, (240, 240, 236, 255))
        K.oval(d, K.at(6.9, -0.3), 0.8, 0.9, INK)

    side_head = R.make_head(K, ("trudy_side",), *skin, skull=(0.0, -2.2, 8.6, 8.6), jaw=(3.2, 3.8, 5.8, 6.8),
                            nose=((8.0, 0.6), (9.8, 3.2), (9.4, 4.2), (8.0, 4.6)), ear=None, shape=side_hair_shape, under=side_hair, over=side_mask,
                            far_shade=False)
    side_brows = R.make_brows(K, [(4.0, -4.6), (6.2, -5.2), (8.4, -4.8)], None, HAIR, 0.9)
    side_mouth = R.make_mouth(K, (7.8, 7.2), (140, 60, 76, 255), wide=0.55, lips=(204, 104, 116, 255))

    def side_layers(pose):
        return [(side_head(), "head"), (side_brows(R.brow_mood(pose)), "brows"), (side_mouth(str(pose["mouth"])), "mouth")]

    # Her hair: close on top, to her jaw at the sides and behind, the fringe
    # straight across; the strip of cloth round her head at her eyes.
    cap, bob = ((0.0, -4.2, -0.8), (8.4, 7.8, 8.4)), ((0.0, -0.6, -2.0), (9.0, 7.6, 7.6))
    head3 = C.auto_head(p, head, None, hair=lambda u, v: (v < -5.6) | ((np.abs(u) > 55.0) & (v < 7.0)), hair_colour=HAIR, hair_shade=HAIR_LIGHT,
                        volumes=[cap, bob],
                        lines=[O.curve([O.on_ellipsoid(*cap, u + 18.0 * t, -10.4 + 4.0 * t, 0.2)[0] for t in (0.0, 0.5, 1.0)], HAIR_LIGHT, 0.6)
                               for u in (-140.0, -70.0, 0.0, 70.0, 140.0)])
    from dataclasses import replace

    head3 = replace(head3, lines=list(head3.lines) + [O.curve([O.on_ellipsoid(*bob, u, -0.4, 0.3)[0] for u in range(-180, 181, 15)], GLOVE, 2.2)])
    # Her suit from neck to ankle: the zip, its dark collar, her belt with its
    # pouches.
    pouch = mix(BELT, INK, 0.3)
    trunk3 = C.auto_trunk(p, [W.Strip(0.0, top - 1.0, top + 3.0, 3.4, SUIT_DARK), W.Down(0.0, top + 3.0, 6.0, SUIT_LIGHT, width=0.45),
                              W.Band(-1.0, 2.6, BELT), W.Patch(-47.0, -28.0, 1.0, 6.0, pouch), W.Patch(-22.0, -3.0, 1.0, 6.0, pouch),
                              W.Patch(25.0, 44.0, 1.0, 6.0, pouch), W.Down(180.0, top + 3.0, 5.0, SUIT_DARK)])
    # Low and ready: her open hands in front of her, where a wall will be.
    ROUNDS["trudy"] = C.Round("Trudy", C.PersonBody(p, heads={"side": side_layers}), C.Look(head3, trunk3),
                              C.Stance(hands={"r": C.Hand(at=(-5.0, -17.0, 15.0), pole=(-1.0, 0.3, -0.3), mode="open"),
                                              "l": C.Hand(at=(5.0, -20.0, 15.0), pole=(1.0, 0.3, -0.3), mode="open")}, stagger=2.6))
    _meta("trudy", "Trudy", ["hub", "peaceful", "cryptography_crew", "intruder"],
          "Trudy is the intruder role in security examples; the pun is embedded in 'inTRUDer.' She represents unauthorized entry more generally "
          "than Mallory's active channel manipulation and approaches every boundary as a system waiting to be tested.",
          "Use as an infiltrator, red-team rival, lock bypasser, or security tutorial character. She should probe assumptions, find side doors, "
          "and narrate defenses in terms of how she would get through them.",
          ["Trudy intrudes.", "I've stopped apologizing for it.", "I'm thinking about how I'd get into the exhibit."])


# =============================================================================
# Victor: the verifier. He walks away sure, and he still does not know.
# =============================================================================


def _victor() -> None:
    p = _person("victor", 185.0, girth=0.4)
    K, P = p.K, p.P
    skin = BROWN
    COAT, COAT_DARK, COAT_LIGHT = (96, 118, 146, 255), (62, 78, 106, 255), (140, 162, 188, 255)
    SCARF, SCARF_DARK, SHIRT, TROUSER, TROUSER_DARK = (232, 190, 84, 255), (176, 124, 52, 255), (240, 238, 232, 255), (62, 64, 80, 255), (42, 42, 58, 255)
    HAIR, GLASS, GLASS_DARK = (34, 30, 34, 255), (190, 232, 250, 255), (70, 110, 150, 255)
    top = p.b.neck[1] - 2.0

    def front(d, hb, hf) -> None:
        # A long coat, buttoned, and a scarf with one end down his front.
        K.line(d, [K.at(6.0, top + 4.0), K.at(7.4 + hf * 0.6, 28.0)], COAT_DARK, 0.8)
        for y in (-20.0, -10.0, 0.0, 10.0):
            K.oval(d, K.at(4.2, y), 1.0, 1.0, COAT_DARK)
        K.poly(d, [K.at(0.6, top + 1.0), K.at(6.4, top + 1.0), K.at(6.0, -12.0), K.at(1.6, -11.4)], SCARF)
        for y in (-22.0, -17.0):
            K.line(d, [K.at(1.2, y), K.at(6.2, y - 0.4)], SCARF_DARK, 0.7)
        K.line(d, [K.at(-8.0, 6.0), K.at(-2.0, 6.6)], COAT_DARK, 0.7)

    p.torso = R.make_torso(K, ("victor",), COAT, COAT_DARK, back=(9.8, 10.2, 9.0, 11.4), front=(8.8, 10.4, 9.8, 11.2), hem_y=30.0, top=top,
                           shoulders=((-6.0, p.b.near_shoulder[1] + 0.6), (6.8, p.b.far_shoulder[1] + 0.4)), shoulder_r=(5.8, 5.2), shade_from=8.6, detail=front)
    _dress(p, skin, COAT, COAT_DARK, TROUSER, TROUSER_DARK, (70, 52, 44, 255), (42, 30, 28, 255), cuff=SHIRT, arm=(7.4, 6.2, 5.6), legs=(7.6, 6.4, 5.6),
           hand=1.05, long_shoe=1.08)

    def scarf():
        def shape(d) -> None:
            K.oval(d, K.at(0.8, 0.6), 8.0, 4.0, WHITE)

        return K.solid(("victor_scarf",), shape, SCARF, lambda d: K.line(d, [K.at(-6.0, 1.0), K.at(0.0, 2.2), K.at(7.0, 0.6)], SCARF_DARK, 0.7), outline=1.1,
                       rim=0.3, shade=0.4, shade_colour=SCARF_DARK)

    p.collar = scarf

    def hair_shape(d) -> None:
        K.oval(d, K.at(-0.6, -5.0), 8.8, 7.6, WHITE)

    def hair(d) -> None:
        # Short, and it is going back from his brow.
        K.poly(d, [K.at(20.0, -10.0), K.at(6.4, -10.0), K.at(2.0, -8.6), K.at(-1.4, -6.4), K.at(-3.0, -3.0), K.at(-6.0, -2.4), K.at(-6.4, 2.6), K.at(-5.0, 4.0),
                   K.at(-4.6, 6.0), K.at(-20.0, 6.0), K.at(-20.0, -26.0), K.at(20.0, -26.0)], HAIR)

    def over(d) -> None:
        K.line(d, [K.at(2.0, -6.6), K.at(5.0, -7.0), K.at(7.4, -6.6)], mix(skin[0], skin[2], 0.5), 0.5)

    head = R.make_head(K, ("victor",), *skin, skull=(0.0, -2.4, 8.2, 9.0), jaw=(2.6, 4.2, 6.0, 7.6), nose=((7.2, -0.6), (10.4, 3.0), (9.8, 4.8), (7.2, 5.0)),
                       shape=hair_shape, under=hair, over=over)
    eyes = R.make_eyes(K, (1.4, -0.6), (7.0, -0.8), ink=INK, iris=(50, 30, 24, 255))
    _face(p, head, eyes,
          R.make_brows(K, [(-1.4, -4.4), (1.4, -4.6), (4.2, -3.4)], [(5.6, -3.6), (7.2, -4.8), (8.8, -4.6)], HAIR, 1.3),
          R.make_mouth(K, (5.6, 8.4), (96, 42, 46, 255), wide=0.9))

    # ---- From the front: his coat buttoned, his scarf round his neck with
    # one end down, his arms folded.
    sy = p.b.near_shoulder[1] + 0.6

    def front_coat(d) -> None:
        K.line(d, [K.at(0.0, top + 4.0), K.at(0.0, 30.0)], COAT_DARK, 0.8)
        for y in (-20.0, -10.0, 0.0, 10.0):
            K.oval(d, K.at(-2.0, y), 1.0, 1.0, COAT_DARK)
        K.poly(d, [K.at(1.0, top + 1.0), K.at(6.0, top + 1.0), K.at(5.6, -12.0), K.at(1.6, -11.4)], SCARF)
        for y in (-22.0, -17.0):
            K.line(d, [K.at(1.2, y), K.at(5.8, y - 0.4)], SCARF_DARK, 0.7)
        K.oval(d, K.at(0.0, top + 1.6), 7.0, 3.0, SCARF, OUTLINE, 0.6)
        K.line(d, [K.at(-5.6, top + 2.0), K.at(0.0, top + 3.4), K.at(5.6, top + 2.0)], SCARF_DARK, 0.7)

    def front_hair_shape(d) -> None:
        K.oval(d, K.at(0.0, -5.2), 8.6, 7.4, WHITE)

    def front_hair(d) -> None:
        # Short, and it is going back from his brow.
        K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, -1.0), K.at(7.4, -1.0), K.at(6.8, -6.6), K.at(3.6, -9.8), K.at(0.0, -8.6), K.at(-3.6, -9.8),
                   K.at(-6.8, -6.6), K.at(-7.4, -1.0), K.at(-20.0, -1.0)], HAIR)

    def front_nose(d) -> None:
        K.line(d, [K.at(-3.0, -6.6), K.at(0.0, -7.0), K.at(3.0, -6.6)], mix(skin[0], skin[2], 0.5), 0.5)
        K.line(d, [K.at(-0.2, 0.8), K.at(-1.3, 3.4), K.at(0.0, 4.2), K.at(1.3, 3.4)], skin[2], 0.6)

    p.front_torso = R.make_front_torso(K, ("victor",), COAT, COAT_DARK, [(top, 4.4), (top + 3.6, 9.6), (-24.0, 10.2), (-8.0, 9.6), (30.0, 11.6)],
                                       shoulder=(7.6, sy, 5.0, 5.2), detail=front_coat)
    p.front_head_layers = R.front_face(
        R.make_front_head(K, ("victor",), skin[0], skin[2], wide=8.0, jaw=6.4, chin=3.8, ears=skin[0], shape=front_hair_shape, hair=front_hair, face=front_nose),
        R.make_front_eyes(K, ("victor",), ink=INK, iris=(50, 30, 24, 255), spread=3.4, y=-0.6), R.make_front_brows(K, ("victor",), HAIR, spread=3.4, y=-4.2, width=1.3),
        R.make_front_mouth(K, ("victor",), y=8.4, colour=(96, 42, 46, 255), wide=0.8))
    p.front_shoe = R.make_front_shoe(K, (70, 52, 44, 255), (42, 30, 28, 255), p.b.ankle_up)
    p.front_span = (8.2, 4.6)

    @p.front_row
    def front(i: int, n: int):
        _, s, c = loop(i, n)
        return R.FP(hip=(0.0, 0.3 + 0.3 * s), head=(0.3 * c, 0.0, 2.0 * c), la=(-9.0, 12.0), ra=(-9.0, 13.5), lz=0.5, rz=0.5, lh="fist", rh="fist",
                    eyes="closed" if i == n - 2 else "open", brows=1.0 if c > 0.6 else 0.0, mouth="flat")

    R.add_front_rows(p)

    #: His arms folded. He will be convinced, but not yet.
    folded_near, folded_far = (8.5, 9.5), (-1.0, 22.0)
    p.set_rest(na=folded_near, fa=folded_far, nh="fist", mouth="flat", lean=-2.0)

    @p.row
    def idle(i: int, n: int):
        # A hand at his chin while he thinks of the next thing to ask.
        _, s, c = loop(i, n)
        think = c < 0.0
        return P(hip=(0.0, 0.3 + 0.3 * s), head=(0.0, 0.0, 4.0 if think else 0.0), na=(9.5, 0.5) if think else folded_near, eyes="closed" if i == n - 2 else "open",
                 brows=-1.0 if think else 0.0)

    _walk(p, (-2.0, 25.0), (2.5, 24.5), reach=9.0, lean=1.0, swing=6.0)

    @p.row
    def talk(i: int, n: int):
        # He asks. One finger, and then another one.
        _, s, _c = loop(i, n)
        return P(hip=(0.0, 0.3 * s), head=(0.3, 0.0, 2.0 * s), na=(14.0, 1.0 - 4.0 * max(0.0, s)), nh="point", mouth=("open", "flat", "o", "flat")[i % 4],
                 brows=1.0 if s > 0.2 else -1.0)

    @p.row
    def interact(i: int, n: int):
        # He looks at it through his glass, close. It is as she said.
        look = P(hip=(2.0, 2.0), lean=14.0, head=(1.0, 0.0, 6.0), na=(21.0, 0.0), nh="fist", brows=-1.0)
        return p.keys(shot(i, n), [(0.0, P()), (0.3, look), (0.7, dict(look, na=(22.0, 1.5))), (0.85, dict(look, brows=1.0, mouth="smile")), (1.0, P())])

    def glass():
        def shape(d) -> None:
            K.oval(d, K.at(0.0, -9.0), 5.2, 5.2, WHITE)
            K.stroke(d, [K.at(0.0, -4.0), K.at(0.0, 3.0)], WHITE, 1.8)

        def detail(d) -> None:
            K.oval(d, K.at(0.0, -9.0), 3.8, 3.8, GLASS)
            K.line(d, [K.at(-1.8, -9.6), K.at(-0.4, -11.4)], WHITE, 0.7)

        return K.solid(("magnifier",), shape, GOLD, detail, outline=1.0, rim=0.3, shade=0.4, shade_colour=GOLD_DARK)

    def effects(ctx) -> List[Stamp]:
        out: List[Stamp] = []
        if ctx.anim == "interact" and 0.2 <= ctx.u <= 0.9:
            out.append((glass(), ctx.hand, "glass", 60.0))
            if ctx.u >= 0.7:
                out.append((R.tick(K, 4.5, (150, 232, 170, 255), (50, 130, 90, 255)), (ctx.head[0] + 17.0, ctx.head[1] - 15.0), "tick", 0.0))
        elif ctx.anim == "talk" and ctx.i % 4 in (1, 2):
            out.append((R.glyph(K, "?", 8.0, GLASS, GLASS_DARK), (ctx.hand[0] + 9.0, ctx.hand[1] - 13.0), "question", 0.0))
        return out

    p.effects = effects

    # ---- In the round. His head from the side, drawn as the cast draws a
    # head in the numbers of a profile: his short hair going back from his
    # brow, the line of his forehead, his ear at the middle of his head.
    def side_hair_shape(d) -> None:
        K.oval(d, K.at(-1.4, -5.0), 9.6, 7.6, WHITE)

    def side_hair(d) -> None:
        K.poly(d, [K.at(20.0, -10.0), K.at(7.2, -10.0), K.at(2.8, -8.6), K.at(1.0, -6.4), K.at(0.8, -3.0), K.at(1.0, 0.4), K.at(-1.0, 0.6), K.at(-3.6, 2.6),
                   K.at(-3.6, 6.0), K.at(-20.0, 6.0), K.at(-20.0, -26.0), K.at(20.0, -26.0)], HAIR)

    def side_over(d) -> None:
        K.line(d, [K.at(3.6, -6.6), K.at(6.2, -7.0), K.at(8.4, -6.6)], mix(skin[0], skin[2], 0.5), 0.5)

    side_head = R.make_head(K, ("victor_side",), *skin, skull=(0.0, -2.4, 9.2, 9.0), jaw=(3.4, 4.2, 6.6, 7.6),
                            nose=((8.0, -0.6), (11.2, 3.0), (10.6, 4.8), (8.0, 5.0)), ear=(-1.6, 1.0, 2.2, 3.3), shape=side_hair_shape, under=side_hair,
                            over=side_over, far_shade=False)
    side_eyes = R.make_eyes(K, (6.4, -0.4), None, ink=INK, iris=(50, 30, 24, 255))
    side_brows = R.make_brows(K, [(4.2, -4.4), (6.2, -4.8), (8.4, -4.2)], None, HAIR, 1.3)
    side_mouth = R.make_mouth(K, (8.0, 8.4), (96, 42, 46, 255), wide=0.55)

    def side_layers(pose):
        return [(side_head(), "head"), (side_eyes(str(pose["eyes"])), "eyes"), (side_brows(R.brow_mood(pose)), "brows"),
                (side_mouth(str(pose["mouth"])), "mouth")]

    # His short hair, going back from his brow.
    crop = ((0.0, -5.0, -0.8), (8.4, 7.4, 8.4))
    head3 = C.auto_head(p, head, eyes, hair=lambda u, v: (v < -8.6 + 2.0 * np.clip(np.abs(u) / 60.0, 0.0, 1.0)) | ((np.abs(u) > 70.0) & (v < 0.0))
                        | ((np.abs(u) > 100.0) & (v < 6.0)), hair_colour=HAIR, hair_shade=mix(HAIR, WHITE, 0.15), volumes=[crop])
    # His long coat, buttoned, a line down its front, a scarf end down it,
    # a pocket, the seam at his back.
    trunk3 = C.auto_trunk(p, [W.Down(0.0, top + 4.0, 30.0, COAT_DARK, width=0.4), W.Buttons(-11.0, -20.0, 10.0, 4, 1.0, COAT_DARK),
                              W.Strip(20.0, top + 1.0, -11.6, 2.4, SCARF), W.Across(8.0, 32.0, -22.0, SCARF_DARK, width=0.35),
                              W.Across(8.0, 32.0, -17.0, SCARF_DARK, width=0.35), W.Across(-50.0, -15.0, 6.0, COAT_DARK),
                              W.Down(180.0, top + 4.0, 30.0, COAT_DARK)])
    # His scarf round his neck: his own scarf in his three-quarter views (the
    # front art has it in its coat), a loft of it in the others.
    n = p.b.neck[1]
    neck3 = (0.0, n, O.lift(p.b.neck[0], 0.0))
    own_scarf = O.Sprite("own_scarf", neck3, lambda view, far: (scarf(), 0.0, O.facing(view) < 0.0) if 30.0 <= abs(O.facing(view)) <= 60.0 else None,
                         lead=9.5)
    scarf3 = W.Worn("scarf", [O.Ring(n - 1.6, 0.0, 0.6, 4.8, 4.4), O.Ring(n + 0.2, 0.0, 0.6, 7.6, 7.0), O.Ring(n + 2.0, 0.0, 0.6, 8.0, 7.4),
                              O.Ring(n + 3.6, 0.0, 0.4, 6.6, 6.0)],
                    W.Garment(SCARF, SCARF_DARK, features=[W.Across(-180.0, 180.0, n + 1.2, SCARF_DARK, width=0.3), W.Shade(-0.45)]), lead=6.0)

    class _Own:
        """His own scarf as a piece of the look: it says itself in which
        views it draws."""

        def piece(self, K_, J, head_):
            return own_scarf

    # His arms folded, as his front art has them. He will be convinced, but
    # not yet.
    ROUNDS["victor"] = C.Round("Victor", C.PersonBody(p, heads={"side": side_layers}),
                               C.Look(head3, trunk3, back_pieces=[_Own()], pieces=[("trunk", scarf3)]),
                               C.Stance(hands={"r": C.Hand(at=(5.0, -16.0, 8.5), pole=(-1.0, 0.6, 0.2), mode="fist"),
                                               "l": C.Hand(at=(-5.0, -14.5, 9.5), pole=(1.0, 0.6, 0.2), mode="fist")}, stagger=2.0))
    _meta("victor", "Victor", ["hub", "peaceful", "cryptography_crew", "verifier"],
          "Victor is the verifier paired with Peggy in zero-knowledge proof examples. He repeatedly becomes convinced that Peggy knows a secret "
          "while learning nothing about the secret itself, making skepticism and disciplined challenge-response his defining traits.",
          "Use as a verifier, examiner, skeptical ally, or protocol gatekeeper. He should issue unpredictable challenges, check responses, and "
          "accept proof without demanding that private knowledge be surrendered.",
          ["Peggy proves. I verify.", "I walk away convinced and still do not know the secret.", "That's not failure. It's the whole point."])


# =============================================================================
# Walter: the warden. Every note crosses his desk, and they still get past him.
# =============================================================================


def _walter() -> None:
    p = _person("walter", 173.0, girth=1.4)
    K, P = p.K, p.P
    skin = TAN
    COAT, COAT_DARK, COAT_LIGHT = (42, 56, 96, 255), (26, 34, 66, 255), (80, 98, 146, 255)
    BELT, HAIR, CAP, CAP_DARK = (38, 34, 44, 255), (92, 84, 84, 255), (36, 46, 82, 255), (20, 26, 52, 255)
    top = p.b.neck[1] - 2.0

    def front(d, hb, hf) -> None:
        # Two rows of brass buttons, a belt, and his keys on it.
        for y in (-26.0, -19.0, -12.0):
            for x in (1.4, 7.4):
                K.oval(d, K.at(x, y), 1.1, 1.1, GOLD)
        K.poly(d, [K.at(-13.0, -5.6), K.at(14.0, -4.6), K.at(14.0, -1.4), K.at(-13.0, -2.4)], BELT)
        K.rrect(d, K.home[0] + 2.6, K.home[1] - 6.0, K.home[0] + 7.0, K.home[1] - 1.2, 0.6, GOLD)
        K.oval(d, K.at(-5.4, 1.4), 2.4, 2.6, None, GOLD, 0.8)  # type: ignore[arg-type]
        for x, y in ((-6.8, 6.0), (-5.0, 6.8), (-3.6, 5.6)):
            K.line(d, [K.at(-5.4, 3.6), K.at(x, y)], GOLD, 1.0)
        K.poly(d, [K.at(2.4, top - 1.0), K.at(9.4, top - 1.0), K.at(9.0, top + 3.6), K.at(2.8, top + 3.6)], COAT_DARK)
        K.poly(d, [K.at(-9.6, top + 4.0), K.at(-4.0, top + 2.6), K.at(-3.6, top + 4.8), K.at(-9.4, top + 6.2)], GOLD)

    p.torso = R.make_torso(K, ("walter",), COAT, COAT_DARK, back=(10.4, 11.2, 10.8, 11.4), front=(9.4, 11.6, 12.0, 12.2), hem_y=12.0, top=top,
                           shoulders=((-6.6, p.b.near_shoulder[1] + 0.6), (7.4, p.b.far_shoulder[1] + 0.4)), shoulder_r=(6.2, 5.6), belly=1.6, shade_from=9.6,
                           detail=front)
    _dress(p, skin, COAT, COAT_DARK, COAT, COAT_DARK, (30, 28, 36, 255), (14, 12, 20, 255), cuff=GOLD, arm=(8.2, 7.0, 6.2), legs=(8.4, 7.0, 6.0), hand=1.1,
           long_shoe=1.1, neck=5.6)

    def cap_shape(d) -> None:
        # A peaked cap, its crown wide, its peak down over his eyes.
        K.poly(d, [K.at(-10.4, -8.6), K.at(-9.0, -15.0), K.at(6.0, -16.4), K.at(10.6, -12.4), K.at(9.6, -8.4)], WHITE)
        K.poly(d, [K.at(3.0, -7.0), K.at(12.6, -5.2), K.at(12.4, -3.6), K.at(3.0, -4.6)], WHITE)

    def under(d) -> None:
        K.poly(d, [K.at(20.0, -6.6), K.at(-3.0, -6.6), K.at(-3.6, -2.4), K.at(-6.2, -2.0), K.at(-6.8, 3.4), K.at(-5.2, 4.6), K.at(-4.8, 6.6), K.at(-20.0, 6.6),
                   K.at(-20.0, -26.0), K.at(20.0, -26.0)], HAIR)
        K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, -6.4), K.at(3.0, -6.4), K.at(-20.0, -7.4)], CAP)
        K.poly(d, [K.at(-20.0, -10.6), K.at(20.0, -9.4), K.at(20.0, -6.4), K.at(3.0, -6.4), K.at(-20.0, -7.4)], CAP_DARK)
        K.poly(d, [K.at(3.0, -6.6), K.at(14.0, -4.4), K.at(14.0, -2.6), K.at(3.0, -4.4)], BELT)
        K.oval(d, K.at(4.0, -11.0), 1.8, 1.8, GOLD)

    def over(d) -> None:
        # A grey moustache, wide.
        K.poly(d, [K.at(1.6, 5.6), K.at(5.2, 4.6), K.at(9.4, 5.4), K.at(10.2, 7.2), K.at(6.0, 6.6), K.at(1.2, 7.6)], HAIR)

    head = R.make_head(K, ("walter",), *skin, skull=(0.0, -2.2, 8.6, 9.0), jaw=(2.4, 4.4, 6.8, 7.4), nose=((7.4, -0.6), (10.6, 3.0), (10.2, 4.6), (7.2, 5.0)),
                       shape=cap_shape, under=under, over=over)
    eyes = R.make_eyes(K, (1.4, -0.4), (7.0, -0.6), ink=INK, white=None, lid=skin[2])
    _face(p, head, eyes, R.make_brows(K, [(-1.4, -3.4), (1.4, -4.0), (4.2, -3.4)], [(5.8, -3.6), (7.2, -4.0), (8.8, -3.4)], HAIR, 1.4),
          R.make_mouth(K, (5.6, 8.8), (104, 52, 50, 255), wide=0.85))

    # ---- From the front: two rows of brass buttons, his belt and his keys,
    # the peak of his cap, and his moustache.
    sy = p.b.near_shoulder[1] + 0.6

    def front_coat(d) -> None:
        for y in (-26.0, -19.0, -12.0):
            for x in (-3.0, 3.0):
                K.oval(d, K.at(x, y), 1.1, 1.1, GOLD)
        K.poly(d, [K.at(-20.0, -5.4), K.at(20.0, -5.4), K.at(20.0, -2.0), K.at(-20.0, -2.0)], BELT)
        K.rrect(d, K.home[0] - 2.2, K.home[1] - 6.0, K.home[0] + 2.2, K.home[1] - 1.4, 0.6, GOLD)
        K.oval(d, K.at(-6.4, 1.4), 2.2, 2.4, None, GOLD, 0.8)  # type: ignore[arg-type]
        for x, y in ((-7.8, 6.0), (-6.0, 6.8), (-4.6, 5.6)):
            K.line(d, [K.at(-6.4, 3.6), K.at(x, y)], GOLD, 1.0)
        K.poly(d, [K.at(-3.8, top - 1.0), K.at(3.8, top - 1.0), K.at(3.4, top + 3.6), K.at(-3.4, top + 3.6)], COAT_DARK)
        for sx in (-1.0, 1.0):
            K.poly(d, [K.at(5.0 * sx, top + 3.0), K.at(10.0 * sx, top + 4.0), K.at(10.0 * sx, top + 6.2), K.at(5.0 * sx, top + 5.2)], GOLD)

    def front_cap_shape(d) -> None:
        K.poly(d, [K.at(-10.8, -8.6), K.at(-9.8, -15.4), K.at(0.0, -16.8), K.at(9.8, -15.4), K.at(10.8, -8.6)], WHITE)
        K.poly(d, [K.at(-8.6, -7.6), K.at(8.6, -7.6), K.at(9.2, -4.2), K.at(-9.2, -4.2)], WHITE)

    def front_cap(d) -> None:
        for sx in (-1.0, 1.0):
            K.poly(d, [K.at(6.6 * sx, -7.0), K.at(20.0 * sx, -7.0), K.at(20.0 * sx, 1.4), K.at(7.6 * sx, 1.4)], HAIR)
        K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, -6.8), K.at(-20.0, -6.8)], CAP)
        K.poly(d, [K.at(-20.0, -10.6), K.at(20.0, -10.6), K.at(20.0, -6.8), K.at(-20.0, -6.8)], CAP_DARK)
        K.poly(d, [K.at(-20.0, -6.8), K.at(20.0, -6.8), K.at(20.0, -4.4), K.at(-20.0, -4.4)], BELT)
        K.oval(d, K.at(0.0, -12.6), 1.8, 1.8, GOLD)

    def front_moustache(d) -> None:
        K.line(d, [K.at(-0.2, 0.8), K.at(-1.4, 3.4), K.at(0.0, 4.2), K.at(1.4, 3.4)], skin[2], 0.7)
        # A grey moustache, wide.
        K.poly(d, [K.at(-6.0, 6.6), K.at(-2.6, 4.8), K.at(0.0, 5.6), K.at(2.6, 4.8), K.at(6.0, 6.6), K.at(5.2, 7.8), K.at(0.0, 6.8), K.at(-5.2, 7.8)], HAIR)

    p.front_torso = R.make_front_torso(K, ("walter",), COAT, COAT_DARK, [(top, 4.8), (top + 3.6, 10.4), (-24.0, 11.4), (-6.0, 12.4), (12.0, 12.2)],
                                       shoulder=(8.4, sy, 5.4, 5.6), detail=front_coat)
    p.front_head_layers = R.front_face(
        R.make_front_head(K, ("walter",), skin[0], skin[2], wide=8.4, jaw=7.2, chin=3.6, ears=skin[0], shape=front_cap_shape, hair=front_cap, face=front_moustache),
        R.make_front_eyes(K, ("walter",), white=None, ink=INK, spread=3.5, y=-0.4), R.make_front_brows(K, ("walter",), HAIR, spread=3.5, y=-2.8, width=1.4),
        R.make_front_mouth(K, ("walter",), y=9.0, colour=(104, 52, 50, 255), wide=0.75))
    p.front_shoe = R.make_front_shoe(K, (30, 28, 36, 255), (14, 12, 20, 255), p.b.ankle_up)
    p.front_span = (9.2, 5.2)
    R.add_front_rows(p, hands="sides")

    #: His hands on his belt.
    belt_near, belt_far = (4.5, 16.5), (-1.0, 22.0)
    p.set_rest(na=belt_near, fa=belt_far, nh="fist", mouth="flat", lean=-3.0)

    @p.row
    def idle(i: int, n: int):
        # He rocks on his heels, and he watches the door.
        _, s, c = loop(i, n)
        return P(hip=(0.5 * s, 0.3), lean=-3.0 + 2.0 * s, head=(0.0, 0.0, 3.0 * c), eyes="closed" if i == n - 2 else "open", brows=-1.0 if c > 0.3 else 0.0)

    _walk(p, belt_near, belt_far, reach=7.6, lift=4.0, lean=-1.0, nh="fist")

    @p.row
    def talk(i: int, n: int):
        _, s, _c = loop(i, n)
        return P(hip=(0.0, 0.3 * s), head=(0.3, 0.0, 2.0 * s), na=(13.0, 5.0 - 3.0 * max(0.0, s)), nh="point", mouth=("open", "flat", "open", "flat")[i % 4],
                 brows=-1.0)

    @p.row
    def interact(i: int, n: int):
        # He holds the note up to the light, and he finds nothing, and he lets it by.
        read = P(lean=-2.0, head=(0.0, 0.0, -8.0), na=(13.0, -8.0), nh="fist", brows=-1.0)
        give = P(hip=(1.0, 1.0), lean=6.0, na=(23.0, 4.0), nh="soft", mouth="flat")
        return p.keys(shot(i, n), [(0.0, P()), (0.25, read), (0.65, dict(read, head=(0.0, 0.0, -10.0))), (0.85, give), (1.0, P())])

    def effects(ctx) -> List[Stamp]:
        out: List[Stamp] = []
        if ctx.anim == "interact" and 0.15 <= ctx.u <= 0.9:
            out.append((_letter(K, (70, 130, 200, 255), 1.0, "tick" if ctx.u > 0.6 else ""), (ctx.hand[0] + 6.0, ctx.hand[1] - 3.0), "letter", -6.0))
        return out

    p.effects = effects

    # ---- In the round: his head from the side drawn by the cast's makers in
    # the numbers of a profile (the peaked cap, its badge and its peak, his
    # wide moustache); his cap, his head and his coat in 3D from the numbers
    # of his makers. His keys are on his right, so his coat is not mirrored.

    def side_cap_shape(d) -> None:
        K.poly(d, [K.at(-11.0, -8.6), K.at(-10.4, -15.0), K.at(5.0, -16.6), K.at(10.4, -12.6), K.at(9.6, -8.4)], WHITE)
        K.poly(d, [K.at(4.0, -7.0), K.at(13.2, -5.0), K.at(13.0, -3.4), K.at(4.0, -4.6)], WHITE)

    def side_under(d) -> None:
        K.poly(d, [K.at(20.0, -6.6), K.at(1.0, -6.6), K.at(1.2, -2.4), K.at(-1.0, -2.0), K.at(-3.6, 3.4), K.at(-3.4, 6.6), K.at(-20.0, 6.6),
                   K.at(-20.0, -26.0), K.at(20.0, -26.0)], HAIR)
        K.poly(d, [K.at(-20.0, -26.0), K.at(20.0, -26.0), K.at(20.0, -6.4), K.at(4.0, -6.4), K.at(-20.0, -7.4)], CAP)
        K.poly(d, [K.at(-20.0, -10.6), K.at(20.0, -9.4), K.at(20.0, -6.4), K.at(4.0, -6.4), K.at(-20.0, -7.4)], CAP_DARK)
        K.poly(d, [K.at(4.0, -6.6), K.at(14.0, -4.4), K.at(14.0, -2.6), K.at(4.0, -4.4)], BELT)
        K.oval(d, K.at(7.0, -11.4), 1.6, 1.8, GOLD)

    def side_over(d) -> None:
        K.poly(d, [K.at(4.6, 5.6), K.at(8.0, 4.6), K.at(11.2, 5.4), K.at(11.8, 7.2), K.at(8.4, 6.8), K.at(4.4, 7.6)], HAIR)

    side_head = R.make_head(K, ("walter_side",), *skin, skull=(0.0, -2.2, 9.6, 9.0), jaw=(3.2, 4.4, 7.4, 7.4),
                            nose=((8.2, -0.6), (11.4, 3.0), (11.0, 4.6), (8.0, 5.0)), ear=(-1.6, 1.0, 2.2, 3.2), shape=side_cap_shape, under=side_under,
                            over=side_over, far_shade=False)
    side_eyes = R.make_eyes(K, (6.6, -0.4), None, ink=INK, white=None, lid=skin[2])
    side_brows = R.make_brows(K, [(4.4, -3.4), (6.6, -4.0), (8.8, -3.4)], None, HAIR, 1.4)
    side_mouth = R.make_mouth(K, (8.2, 8.8), (104, 52, 50, 255), wide=0.55)
    #: His cap: a crown wide at the top, its dark band and its badge; its
    #: peak in front only (its back is inside the crown).
    cap = W.Hat(crown=[O.Ring(-6.4, 0.0, 0.6, 8.8, 8.8), O.Ring(-10.6, 0.0, 0.6, 9.2, 9.2), O.Ring(-14.6, 0.0, 1.2, 10.4, 10.8), O.Ring(-16.2, 0.0, 1.2, 9.6, 10.0),
                       O.Ring(-16.6, 0.0, 1.2, 0.0, 0.0)],
                brim=None, garment=W.Garment(CAP, CAP_DARK, [W.Band(-10.6, -6.4, CAP_DARK), W.Dot(0.0, -12.0, 1.8, GOLD), W.Shade(-0.4)]), under=CAP_DARK)
    peak = W.Worn("peak", [O.Ring(-6.6, 0.0, 3.6, 7.6, 8.8, v=0.0), O.Ring(-5.0, 0.0, 4.4, 7.8, 9.4, droop=1.4, v=1.0), O.Ring(-6.0, 0.0, 3.6, 7.6, 8.8, v=3.0)],
                  W.Garment(BELT, mix(BELT, INK, 0.5)), on="head")
    ROUNDS["walter"] = C.Round(
        "Walter", C.PersonBody(p, mirror=("head",), heads={"side": lambda pose: [(side_head(), "head"), (side_eyes(str(pose["eyes"])), "eyes"),
                                                                                 (side_brows(R.brow_mood(pose)), "brows"), (side_mouth(str(pose["mouth"])), "mouth")]}),
        C.Look(
            # Grey hair under his cap, at his temples and his nape; his wide grey moustache.
            C.auto_head(p, head, eyes, hair=lambda u, v: (v < -6.4) | ((np.abs(u) > 70.0) & (v < 3.4)) | ((np.abs(u) > 100.0) & (v < 6.6)),
                        hair_colour=HAIR, hair_shade=mix(HAIR, INK, 0.3), moustache=((0.0, 5.8, 7.8), (5.4, 1.1, 1.7))),
            # His coat: two rows of brass buttons, its dark collar, the gold at
            # his near shoulder, his belt and its buckle, his keys on his right.
            C.auto_trunk(p, [W.Band(top - 1.0, top + 3.6, COAT_DARK), W.Patch(-62.0, -32.0, top + 3.0, top + 6.0, GOLD),
                             W.Buttons(16.0, -26.0, -12.0, 3, 1.1, GOLD), W.Buttons(-16.0, -26.0, -12.0, 3, 1.1, GOLD), W.Band(-5.4, -2.0, BELT),
                             W.Patch(-10.0, 10.0, -6.0, -1.4, GOLD), W.Dot(-34.0, 1.4, 2.3, COAT, ring=GOLD), W.Down(180.0, 0.0, 12.0, COAT_DARK)]),
            head_pieces=[cap, peak]),
        # His near hand at his belt, his thumb in it; his far hand at his side.
        C.Stance(hands={"r": C.Hand(at=(-8.4, -3.6, 7.0), pole=(-1.0, 0.0, -0.6), mode="fist"), "l": C.Hand(l=9.8, pole=(0.4, 0.0, -1.0))}, stagger=1.8))
    _meta("walter", "Walter", ["hub", "peaceful", "cryptography_crew", "warden"],
          "Walter is the warden in cryptographic stories about prisoners communicating under surveillance. He reads every message crossing his "
          "desk yet still faces protocols that allow Alice and Bob to coordinate or exchange secrets without exposing their content.",
          "Use as a surveillance gatekeeper, prison administrator, censor, or communications puzzle antagonist. He should inspect every overt "
          "channel while remaining vulnerable to encodings, shared context, and protocols whose meaning is hidden in plain sight.",
          ["Every note crosses my desk first.", "They still get secrets past me.", "It keeps me humble. It keeps me up."])


_craig()
_eve()
_judy()
_mallory()
_olivia()
_peggy()
_sybil()
_trent()
_trudy()
_victor()
_walter()


# ---- Publishing ----------------------------------------------------------------


def _entry(target: str) -> dict:
    person = PEOPLE[target]

    def render(out_dir, **opts) -> List[Path]:
        del opts
        return person.render(out_dir, META[target])

    return {"render": render, "actor_metadata": META[target]}


def frame_of(target: str) -> Callable[[str, int, int], object]:
    """``_render_frame`` of one of the crew (for a contact sheet or a test)."""
    return PEOPLE[target].render_frame


TARGETS = {name: _entry(name) for name in PEOPLE}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render the cryptography crew's spritesheets.")
    parser.add_argument("targets", nargs="*", default=sorted(PEOPLE))
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parents[2] / "generated")
    args = parser.parse_args(argv)
    for name in args.targets:
        for path in TARGETS[name]["render"](args.out_dir / name):
            print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
