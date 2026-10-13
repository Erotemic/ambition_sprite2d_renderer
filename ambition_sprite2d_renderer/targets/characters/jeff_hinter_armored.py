"""Sprite generator for Jeff Hinter in his armor: the other side of
``jeff_hinter``.

He is one man with two looks (Jon, 2026-10-13: "We also need to make
Hinter's transformed variant and normal variant two sides of the same
character"). This sheet is the person of ``jeff_hinter``: the same build, the
same head, the same poses. Only what he wears is its own: the surface he
wraps round himself, closed on him and hard. Plates the blue-grey of slate,
cut where a body bends, and the seams between them are the light of the net.
His head is bare.

The row ``transform_armor`` is the change: he stands as he is, the surface
closes on him, and at the frame it locks he is in his armor. The frames
before that one are drawn by ``jeff_hinter`` itself, so the man who changes
is the man of the other sheet.

There is no drop shadow and he holds nothing.
"""

from __future__ import annotations

import math
from typing import List

from ._ai_era_kit import OUTLINE, WHITE, RGBA, mix, pin
from . import _person_rig as R
from . import jeff_hinter as base
from ._person_rig import Person, Stamp, loop, shot

TARGET_NAME = "jeff_hinter_armored"
TARGET_BASENAME = TARGET_NAME
DISPLAY_NAME = "Jeff Hinter (Armored)"

ACTOR_METADATA = {
    "actor": {"character_id": "npc_jeff_hinter_armored", "display_name": "Jeff Hinter (Armored)"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": ["story", "humanoid", "scholar", "hint_npc", "ai_history", "manifold_armor", "armored_variant"],
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
    "tags": ["story", "humanoid", "scholar", "hint_npc", "ai_history", "manifold_armor", "armored_variant"],
    "sockets": {
        "head": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 70.0, "y": 43.0},
        },
        "chest": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 72.0, "y": 91.0},
        },
        "hand_l": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 52.0, "y": 105.0},
        },
        "hand_r": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 94.0, "y": 101.0},
        },
        "speech_bubble": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 72.0, "y": 10.0},
        },
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "interaction.hint": {"animation": "hint", "events": []},
        "emote.visualize_2d": {"animation": "visualize_2d", "events": []},
        "emote.shout_14": {"animation": "shout_14", "events": []},
        "emote.shout_3": {"animation": "shout_3", "events": []},
        "ability.manifold_shrinkwrap": {"animation": "manifold_shrinkwrap", "events": []},
        "ability.transform_armor": {"animation": "transform_armor", "events": []},
        "defense.block": {"animation": "block", "events": []},
    },
}


ACTOR_METADATA.update(
    {
        "authoring_description": (
            "Armored Jeff Hinter is the converged combat form of the Geoffrey Hinton parody. His "
            "abstract manifold has shrink-wrapped into literal segmented armor, preserving the "
            "dark mop of hair, academic posture, and dimensional jokes beneath a body-sized optimization "
            "result."
        ),
        "gameplay_description": (
            "Use as a transformed ally, miniboss, or defensive playable form. The armor should feel "
            "mathematically fitted rather than forged: deploy it through convergence, let attacks "
            "follow learned surfaces, and retain Jeff's tendency to explain the representation while "
            "under fire."
        ),
    }
)
ACTOR_METADATA.setdefault("dialogue_hints", {}).setdefault(
    "barks",
    [
        'THREE! The armor has depth...',
        'Please attack conventionally.',
        'When everything glows, leave.',
    ],
)


ARMOR: RGBA = (50, 58, 82, 255)
ARMOR_DARK: RGBA = (30, 36, 56, 255)
ARMOR_LIGHT: RGBA = (112, 130, 166, 255)
ARMOR_DEEP: RGBA = (16, 20, 34, 255)
NET = base.NET
NET_DARK = base.NET_DARK
HOT = base.HOT
#: The mesh of the surface, still seen in the plates.
WIRE: RGBA = mix(ARMOR, NET, 0.3)

BUILD = base.BUILD
X = Person(TARGET_NAME, BUILD)
K = X.K
TOP = base.TOP

# He is the same person: how he stands and each pose of his rows.
X.rest = dict(base.X.rest)
X.poses = dict(base.X.poses)
P = X.P


def _trace(d, points, dot: bool = True) -> None:
    """A lit line of the circuit: straight runs and corners, and a node at
    its end."""
    pts = [K.at(x, y) for x, y in points]
    K.line(d, pts, NET_DARK, 1.2)
    K.line(d, pts, NET, 0.45)
    if dot:
        K.oval(d, K.at(*points[-1]), 1.0, 1.0, NET_DARK)
        K.oval(d, K.at(*points[-1]), 0.5, 0.5, NET)


def _plates(d, hb: float, hf: float) -> None:
    """Dark plates with cut corners, the mesh of the surface still in them,
    and the lit lines of a circuit from the core on his chest."""
    # The mesh: thin lines of the fit, under everything.
    for y in (-30.0, -23.0, -16.0, -9.0, -2.0):
        K.line(d, [K.at(-9.0, y), K.at(12.0 + hf, y + 0.4)], WIRE, 0.35)
    for x in (-5.0, 2.0, 9.0):
        K.line(d, [K.at(x, TOP + 4.0), K.at(x + 0.4, 4.0)], WIRE, 0.35)
    # The collar: high, with a cut corner.
    K.poly(d, [K.at(0.2, TOP - 2.0), K.at(10.6, TOP - 1.6), K.at(11.0, TOP + 1.6), K.at(9.0, TOP + 3.6), K.at(1.4, TOP + 3.2)], ARMOR_LIGHT)
    K.line(d, [K.at(1.4, TOP + 3.2), K.at(9.0, TOP + 3.6), K.at(11.0, TOP + 1.6)], ARMOR_DEEP, 0.6)
    # The plate of the chest: six corners.
    K.poly(d, [K.at(-2.6, TOP + 5.0), K.at(10.0, TOP + 5.2), K.at(12.6, TOP + 8.0), K.at(12.8, -20.4), K.at(10.0, -17.6), K.at(0.4, -17.8),
               K.at(-3.4, -21.0)], mix(ARMOR, ARMOR_LIGHT, 0.36))
    K.line(d, [K.at(-2.2, TOP + 5.6), K.at(9.6, TOP + 5.8)], ARMOR_LIGHT, 0.6)
    K.line(d, [K.at(-3.4, -21.0), K.at(0.4, -17.8), K.at(10.0, -17.6), K.at(12.8, -20.4)], ARMOR_DEEP, 1.2)
    # The plates of the belly: three, each with its corners cut.
    for y in (-15.4, -10.2, -5.0):
        K.poly(d, [K.at(0.4, y), K.at(8.0, y + 0.2), K.at(9.2 + hf * 0.5, y + 1.6), K.at(9.2 + hf * 0.5, y + 3.6), K.at(-0.8, y + 3.6), K.at(-0.8, y + 1.4)],
               mix(ARMOR, ARMOR_LIGHT, 0.14))
        K.line(d, [K.at(-0.8, y + 3.9), K.at(9.2 + hf * 0.5, y + 3.9)], ARMOR_DEEP, 0.55)
    # The unit on his back: flat to him, with three lit slits.
    K.poly(d, [K.at(-8.4, -29.0), K.at(-4.6, -29.4), K.at(-4.2, -13.0), K.at(-8.0, -12.0)], ARMOR_DARK)
    for y in (-26.0, -22.0, -18.0):
        K.line(d, [K.at(-7.4, y), K.at(-5.2, y - 0.2)], NET, 0.6)
    # The belt, and its lit lock.
    K.poly(d, [K.at(-9.0, 0.6), K.at(12.0 + hf, 1.0), K.at(12.0 + hf, 3.8), K.at(-9.0, 3.6)], ARMOR_DEEP)
    K.poly(d, [K.at(3.0, 1.2), K.at(7.0, 1.2), K.at(7.0, 3.4), K.at(3.0, 3.4)], NET_DARK)
    K.poly(d, [K.at(4.0, 1.8), K.at(6.0, 1.8), K.at(6.0, 2.8), K.at(4.0, 2.8)], NET)
    # The core, with six sides, and the circuit from it.
    core = [K.at(4.6 + 3.0 * math.cos(math.radians(a)), -25.0 + 3.0 * math.sin(math.radians(a))) for a in range(0, 360, 60)]
    K.poly(d, core, ARMOR_DEEP)
    core = [K.at(4.6 + 2.0 * math.cos(math.radians(a)), -25.0 + 2.0 * math.sin(math.radians(a))) for a in range(0, 360, 60)]
    K.poly(d, core, NET_DARK)
    K.oval(d, K.at(4.6, -25.0), 1.0, 1.0, NET)
    _trace(d, [(1.6, -25.0), (-0.6, -25.0), (-2.4, -23.0)])
    _trace(d, [(7.6, -25.0), (10.0, -25.0), (11.0, -27.0)])
    _trace(d, [(4.6, -22.0), (4.6, -19.0)], dot=False)
    _trace(d, [(-3.6, -8.0), (-3.6, -3.0), (-5.6, -1.0)])


# In armor his chest is defined: wide at the shoulder and the chest, and
# narrow at the waist. It is the chest of a man because the shoulder over it
# is as wide as it is (Jon, 2026-10-13: "I do want more of a defined male
# chest with the armor on").
X.torso = R.make_torso(K, ("hinter_armor",), ARMOR, ARMOR_DARK, back=(8.2, 8.6, 7.6, 9.0), front=(10.0, 10.5, 8.4, 9.2), hem_y=5.0, top=TOP,
                       shoulders=((-3.4, -32.4), (5.6, -32.6)), shoulder_r=(4.6, 4.4), shade_from=40.0, detail=_plates)


def _hud():
    """A unit over his ear, a line of light along his temple, and a pane of
    light at his eye. His face is his own."""

    def paint(d) -> None:
        ex, ey = base.NEAR_EYE
        K.rrect(d, K.home[0] - 7.0, K.home[1] - 1.4, K.home[0] - 3.2, K.home[1] + 3.4, 1.0, ARMOR_LIGHT, ARMOR_DEEP, 0.6)
        K.oval(d, K.at(-5.2, 1.0), 0.9, 0.9, NET)
        K.line(d, [K.at(-3.2, 0.2), K.at(ex - 3.4, ey - 0.4)], NET_DARK, 0.9)
        K.line(d, [K.at(-3.2, 0.2), K.at(ex - 3.4, ey - 0.4)], NET, 0.4)
        K.rrect(d, K.home[0] + ex - 3.2, K.home[1] + ey - 2.4, K.home[0] + ex + 3.0, K.home[1] + ey + 2.0, 0.6, (130, 236, 222, 70), NET, 0.45)

    return K.piece(("hinter_hud",), paint)


X.head_layers = lambda pose: base.X.head_layers(pose) + [(_hud(), "hud")]
X.neck = R.make_neck(K, ARMOR_DEEP, 5.0)


def _plate(near: bool, light: float = 0.0) -> RGBA:
    return mix(ARMOR if near else ARMOR_DARK, ARMOR_LIGHT, light if near else light * 0.5)


#: A joint: dark, with a small light in it. (A part of a bone has round ends
#: as wide as it is, so a light the width of the limb is a ball.)
def _joint(t0: float, w: float):
    return [(t0, t0 + 0.16, w, w, ARMOR_DEEP), (t0 + 0.06, t0 + 0.1, 2.6, 2.6, NET_DARK), (t0 + 0.07, t0 + 0.09, 1.4, 1.4, NET)]


# The pauldron is on the near arm only, and it is flat: it does not stand out
# of his back or his chest.
X.upper_arm = lambda near: ([(0.0, 0.3, 7.4, 7.0, _plate(near, 0.5))] if near else []) + [(0.0 if not near else 0.26, 0.86, 6.6, 6.0, _plate(near))] + _joint(0.84, 5.6)
X.forearm = lambda near: [(0.0, 0.14, 5.6, 5.6, ARMOR_DEEP), (0.12, 1.0, 6.8, 5.8, _plate(near)), (0.3, 0.6, 2.2, 2.2, NET_DARK), (0.32, 0.58, 0.9, 0.9, NET),
                          (0.74, 1.0, 6.2, 6.0, _plate(near, 0.5))]
X.thigh = lambda near: [(0.0, 0.84, 7.6, 6.6, _plate(near)), (0.24, 0.62, 2.2, 2.2, NET_DARK), (0.26, 0.6, 0.9, 0.9, NET), (0.78, 1.0, 7.2, 7.2, _plate(near, 0.5))]
X.shin = lambda near: _joint(0.0, 5.8) + [(0.14, 1.0, 6.8, 5.8, _plate(near)), (0.8, 1.0, 6.2, 6.0, _plate(near, 0.5))]
X.hand = R.make_hand(K, ARMOR_LIGHT, ARMOR, ARMOR_DEEP, ARMOR, ARMOR_DARK, size=1.12)
X.shoe = R.make_shoe(K, ARMOR, ARMOR_DEEP, BUILD.ankle_up, long=1.1)

# ---- The rows that are his own in armor ---------------------------------------

#: Set wide and low, his forearms up: what is thrown at him lands on plate.
BRACE = P(hip=(-1.0, 3.0), lean=-3.0, head=(0.0, 0.5, 4.0), na=(12.0, -5.0), fa=(14.0, 1.0), nh="fist", fh="fist", brows=-1.0, mouth="flat",
          nf=(-7.0, 0.0, 0.0), ff=(8.0, 0.0, 0.0))


@X.row
def block(i: int, n: int):
    return X.keys(shot(i, n), [(0.0, P()), (0.2, BRACE), (0.85, dict(BRACE, hip=(-1.0, 3.6))), (1.0, P())])


#: His arms out from him: the shape the surface is fitted to.
HELD = P(hip=(0.0, 0.6), lean=0.0, head=(0.0, 0.0, -6.0), na=(-12.0, 13.0), fa=(17.0, 11.0), nh="open", fh="open", eyes="closed", brows=1.0, mouth="flat",
         nf=(-5.0, 0.0, 0.0), ff=(6.0, 0.0, 0.0))
#: It has closed on him. He stands in it.
STOOD = P(hip=(0.0, -0.4), lean=0.0, head=(0.0, 0.0, -3.0), na=(-1.0, 22.0), fa=(4.0, 22.0), nh="fist", fh="fist", brows=-1.0, mouth="smile",
          nf=(-5.0, 0.0, 0.0), ff=(6.0, 0.0, 0.0))
#: The part of the row ``transform_armor`` at which the surface is on him:
#: before it he is the man of the other sheet, and from it he is in his armor.
LOCK = 0.56
GLOW = base.GLOW


def fit(u: float) -> float:
    """How near to his outline the surface is at ``u`` of ``transform_armor``."""
    return max(0.0, min(1.0, (u - 0.1) / (LOCK - 0.06 - 0.1)))


def shade(u: float) -> float:
    """How much of him is the light of the surface from the lock on: all of
    him, and then none. What he wears does not change piece by piece: the
    surface that fitted him is what he now wears (this is how Mary-O changes
    form: all of her goes to one light and comes back as the other)."""
    return 0.0 if u < LOCK else max(0.0, min(1.0, 1.0 - (u - LOCK - 0.04) / 0.24))


def transform_armor(i: int, n: int):
    return X.keys(shot(i, n), [(0.0, P()), (0.12, HELD), (0.74, HELD), (0.88, STOOD), (1.0, STOOD)])


X.poses["transform_armor"] = transform_armor
# The man of the other sheet makes the same moves: he is drawn for the frames
# before the lock.
base.X.poses["transform_armor"] = transform_armor
X.alias(taunt="shout_14")
X.rows = [("idle", 8, 145), ("walk", 8, 105), ("talk", 8, 108), ("interact", 10, 92), ("hint", 10, 92), ("visualize_2d", 12, 92), ("shout_14", 12, 78),
          ("shout_3", 12, 78), ("manifold_shrinkwrap", 16, 82), ("transform_armor", 18, 82), ("block", 10, 82), ("taunt", 12, 78)]

# ---- What he shows -------------------------------------------------------------


def _lock_flash(size: int):
    def paint(d) -> None:
        K.star4(d, K.at(0.0, 0.0), float(size), NET, NET_DARK)
        K.oval(d, K.at(0.0, 0.0), size * 0.3, size * 0.3, WHITE)

    return K.aligned(("lock_flash", size), paint)


def _effects(ctx) -> List[Stamp]:
    anim, i, u = ctx.anim, ctx.i, ctx.u
    if anim == "block":
        # A hit that lands on plate.
        if 0.3 <= u <= 0.7:
            return [(_lock_flash(4 + 2 * (i % 2)), pin((ctx.hand[0] + 5.0, ctx.hand[1] - 2.0)), "spark", 0.0)]
        return []
    if anim == "transform_armor":
        if base._BARE[0]:
            return []
        if u < LOCK:
            return base.manifold(ctx, fit(u)) if u >= 0.1 else []
        # It is on him: the mesh goes as the plates come.
        out: List[Stamp] = base.manifold(ctx, 1.0, show=shade(u), solid=0.0)
        if 0.82 <= u < 0.97:
            out.append((_lock_flash(14 - 4 * int((u - 0.82) / 0.06)), pin(ctx.trunk(4.6, -25.0)), "lock", 0.0))
        return out
    return base._effects(ctx)


X.effects = _effects
base.X.effects = lambda ctx, _own=base.X.effects: _effects(ctx) if ctx.anim == "transform_armor" else _own(ctx)

_armored_frame = X.render_frame


def _render_frame(anim: str, i: int, n: int):
    """Before the lock of ``transform_armor`` he is the man of the other
    sheet."""
    if anim != "transform_armor":
        return _armored_frame(anim, i, n)
    u = shot(i, n)
    person, frame = (base.X, base.X.render_frame) if u < LOCK else (X, _armored_frame)
    strength = shade(u)
    kit = person.K
    kit.tint = (GLOW, strength) if strength > 0.0 else None
    kit.tint_skip = ("manifold", "lock")
    try:
        return frame(anim, i, n)
    finally:
        kit.tint = None


X.render_frame = _render_frame  # type: ignore[method-assign]

ROWS = X.rows
_publish, main, render_canonical = R.entry_points(X, ACTOR_METADATA, DISPLAY_NAME)


def render(out_dir, **opts):
    # The outline of each frame the surface is fitted to, read before the
    # part flipbook records a frame.
    base.warm_outlines(X, ("manifold_shrinkwrap", "transform_armor"))
    base.warm_outlines(base.X, ())
    frames = dict((name, n) for name, n, _ms in X.rows)["transform_armor"]
    for i in range(frames):
        base.outline_of(base.X, "transform_armor", i, frames)
    return _publish(out_dir, **opts)



TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}

del loop, OUTLINE

if __name__ == "__main__":
    raise SystemExit(main())
