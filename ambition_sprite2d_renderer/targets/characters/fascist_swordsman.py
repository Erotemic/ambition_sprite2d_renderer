"""Sprite generator for the Fascist Swordsman: a Fascist Enforcer with a
drawn sabre (Jon, 2026-10-30: "maybe we have a few facists with swords or
clubs").

He is the enforcer (``fascist_enforcer``: the cap, the grey-green tunic, the
jackboots, the red armband with the faction's invented cog) and he holds a
straight officer's sabre with a brass guard in his near hand. He is a
pompous man who thinks the sabre makes him a duellist. It does not, but it
does reach.

How he fights (notice, space, telegraph, attack):

* ``notice``: he starts, his brows go up, and he comes on guard, the point
  at you.
* ``windup``: the thrust made ready: his weight back, his hand drawn back to
  his hip, the point level at you. Short, but it shows.
* ``attack_side``: a lunge: his front boot steps out and the point goes
  straight in, far; then he comes back on guard.

He is a person of ``_person_rig``; the weapon is drawn by ``_fascist_armed``.
"""

from __future__ import annotations

import math
from typing import List

from ._ai_era_kit import WHITE, RGBA, lerp, mix
from . import _fascist_armed as A
from . import _person_rig as R
from . import fascist_enforcer as E
from ._person_rig import Stamp, loop, shot

TARGET_NAME = "fascist_swordsman"
TARGET_BASENAME = TARGET_NAME
DISPLAY_NAME = "Fascist Swordsman"

TRAITS = ["story", "humanoid", "enemy", "combatant", "authoritarian", "soldier", "swordsman"]

ACTOR_METADATA = {
    "actor": {"character_id": "npc_fascist_swordsman", "display_name": DISPLAY_NAME},
    "body": {"body_plan": "HumanoidBiped", "body_kind": "Standard", "mass_class": "Medium", "traits": TRAITS, "locomotion_hint": "Walk"},
    "capabilities": {
        "traversal": {"walk": True, "jump": True, "climb": None, "fly": None, "swim": None, "crawl": None, "use_lifts": True, "door_access": ["public"]},
        "interactions": {"talk": True, "trade": None, "carry": None, "open_doors": ["public"]},
    },
    "brain": {"default_preset": "melee_brute_striker"},
    "actions": {"default_preset": "fascist_sabre_thrust"},
    "visual": {"default_pose": "idle", "portrait": {"animation": "idle", "frame": 0}},
    "tags": TRAITS,
    "sockets": {},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "interaction.talk": {"animation": "taunt", "events": []},
        "action.melee.primary": {
            "animation": "attack_side",
            "events": [
                {"t": 0.18, "event": "hitbox_active_start", "source": "explicit.profile.combat_humanoid"},
                {"t": 0.42, "event": "hitbox_active_end", "source": "explicit.profile.combat_humanoid"},
            ],
        },
        "combat.hurt": {"animation": "hit", "events": []},
        "combat.death": {"animation": "death", "events": []},
    },
    "authoring_description": (
        "A Fascist Enforcer with a drawn sabre: the same peaked cap, grey-green tunic, jackboots "
        "and red armband (an invented cog; no real symbol), and a straight sabre with a brass "
        "guard in his hand. A pompous goon who fancies himself a duellist."
    ),
    "gameplay_description": "A quick, long-reaching thrust from a short, readable windup; he holds just out of reach and lunges in.",
    "dialogue_hints": {"barks": ["En garde, citizen!", "I was trained by a correspondence course!", "The blade is regulation length."]},
}

STEEL: RGBA = (206, 212, 216, 255)
STEEL_DARK: RGBA = (124, 132, 140, 255)
STEEL_LIGHT: RGBA = (244, 248, 250, 255)
BRASS: RGBA = (214, 170, 72, 255)
BRASS_DARK: RGBA = (146, 104, 40, 255)
GRIP: RGBA = (40, 30, 30, 255)

#: The sabre, from his grip: the pommel behind, the brass guard, and a
#: straight blade 48 px long.
BLADE = 48.0


def _sabre():
    K = X.K

    def shape(d) -> None:
        K.poly(d, [K.at(4.0, -1.5), K.at(BLADE - 4.0, -1.3), K.at(BLADE + 2.0, 0.0), K.at(BLADE - 4.0, 1.3), K.at(4.0, 1.5)], WHITE)
        K.rrect(d, -5.0, -1.4, 4.0, 1.4, 0.6, WHITE)
        K.rrect(d, 2.4, -4.6, 4.6, 4.6, 0.8, WHITE)
        K.oval(d, K.at(-5.6, 0.0), 1.8, 1.8, WHITE)

    def detail(d) -> None:
        # The grip, bound in wire; the brass guard and pommel.
        K.rrect(d, -5.0, -1.4, 2.6, 1.4, 0.5, GRIP)
        for x in (-3.4, -1.4, 0.6):
            K.line(d, [K.at(x, -1.2), K.at(x + 0.8, 1.2)], mix(GRIP, WHITE, 0.3), 0.3)
        K.rrect(d, 2.4, -4.6, 4.6, 4.6, 0.8, BRASS)
        K.line(d, [K.at(2.9, -4.0), K.at(2.9, 4.0)], mix(BRASS, WHITE, 0.4), 0.4)
        K.oval(d, K.at(-5.6, 0.0), 1.8, 1.8, BRASS)
        # The blade: a fuller down its middle and the light along its back.
        K.line(d, [K.at(5.0, -1.0), K.at(BLADE - 2.0, -0.6)], STEEL_LIGHT, 0.6)
        K.line(d, [K.at(6.0, 0.3), K.at(BLADE - 8.0, 0.3)], STEEL_DARK, 0.4)

    return K.solid(("sabre",), shape, STEEL, detail, outline=0.9, rim=0.2, shade=0.25, shade_colour=STEEL_DARK)


X = A.armed(TARGET_NAME, _sabre)
K = X.K
P = X.P

# ---- How he stands -----------------------------------------------------------

#: Chest out, the sabre down at his side, its point forward and low.
X.set_rest(na=(5.0, 22.0), nh="fist", wa=62.0)


@X.row
def idle(i: int, n: int):
    _, s, c = loop(i, n)
    return dict(E.idle(i, n), na=(5.0, 22.0 - 0.6 * s), nh="fist", wa=62.0 + 2.0 * s)


@X.row
def walk(i: int, n: int):
    _, s, c = loop(i, n)
    pose = E.walk(i, n)
    return dict(pose, na=(5.0 - 3.0 * c, 21.0), nh="fist", wa=58.0 - 6.0 * c)


@X.row
def run(i: int, n: int):
    _, s, c = loop(i, n)
    return dict(E.run(i, n), na=(8.0 - 4.0 * c, 12.0), nh="fist", wa=20.0 - 8.0 * c)


#: On guard: side on, the sabre out in front, the point up a little at you.
ON_GUARD = X.P(hip=(-1.0, 3.0), lean=2.0, head=(0.4, 0.2, 2.0), na=(17.0, 7.0), nh="fist", wa=-24.0, fa=(-6.0, 14.0), nf=(-9.0, 0.0, 0.0),
               ff=(9.0, 0.0, 0.0), mouth="grit", brows=-1.0)
#: Startled: up straight, brows up.
STARTLED = X.P(hip=(-1.0, -1.0), lean=-6.0, head=(-0.6, -0.6, -8.0), na=(9.0, 14.0), nh="fist", wa=30.0, eyes="wide", mouth="o", brows=1.0)


@X.row
def notice(i: int, n: int):
    # He starts, and comes on guard with a flourish of the point.
    flourish = dict(ON_GUARD, na=(14.0, -2.0), wa=-70.0, mouth="open")
    return X.keys(shot(i, n), [(0.0, X.full(X.rest)), (0.2, STARTLED, "snap"), (0.45, STARTLED), (0.65, flourish), (0.85, ON_GUARD), (1.0, ON_GUARD)])


#: The thrust made ready: weight back on his rear boot, his hand drawn back to
#: his hip, the point level at you, his free hand up behind for balance.
READY = X.P(hip=(-4.0, 5.0), lean=-5.0, head=(0.0, 0.4, 4.0), na=(0.0, 13.0), nh="fist", wa=-3.0, fa=(-14.0, -4.0), fh="open",
            nf=(-11.0, 0.0, 0.0), ff=(10.0, 0.0, 0.0), mouth="grit", brows=-1.0, hem=(2.0, 0.0))


@X.row
def windup(i: int, n: int):
    _, s, _c = loop(i, n)
    return dict(READY, na=(0.0 - 0.6 * s, 13.0), wa=-3.0 + 1.0 * s)


#: The lunge: his front boot out, his arm and the sabre straight at you.
LUNGE = X.P(hip=(7.0, 7.0), lean=14.0, head=(1.0, 0.0, 0.0), na=(29.0, 0.0), nh="fist", wa=-1.0, fa=(-18.0, 2.0), fh="open",
            nf=(-14.0, 0.0, 10.0), ff=(17.0, 0.0, 0.0), mouth="big", brows=-1.0, hem=(4.0, 1.0))


@X.row
def attack_side(i: int, n: int):
    return X.keys(shot(i, n), [(0.0, READY), (0.14, LUNGE, "snap"), (0.42, LUNGE), (0.75, dict(ON_GUARD, hip=(2.0, 4.0))), (1.0, ON_GUARD)])


@X.row
def hit(i: int, n: int):
    pose = E.hit(i, n)
    return dict(pose, nh="fist", wa=40.0 if shot(i, n) < 0.2 else 70.0)


@X.row
def death(i: int, n: int):
    # The sabre flies out of his hand as he goes over (``_effects``).
    pose = E.death(i, n)
    return dict(pose, held=1.0 if shot(i, n) < 0.15 else 0.0, wa=40.0)


@X.row
def taunt(i: int, n: int):
    # A salute with the sabre: the hilt to his chin, the blade up.
    salute = X.P(hip=(0.0, 0.0), lean=-3.0, head=(-0.4, -0.4, -4.0), na=(8.0, -2.0), nh="fist", wa=-88.0, mouth="flat", brows=-1.0)
    down = dict(salute, na=(16.0, 14.0), wa=60.0)
    return X.keys(shot(i, n), [(0.0, X.full(X.rest)), (0.25, salute, "snap"), (0.6, salute), (0.85, down), (1.0, X.full(X.rest))])


X.rows = [("idle", 8, 150), ("walk", 8, 105), ("run", 8, 78), ("notice", 8, 85), ("windup", 4, 80), ("attack_side", 9, 60), ("hit", 5, 90),
          ("death", 8, 115), ("taunt", 8, 110)]

# ---- What his blade does -----------------------------------------------------


def _effects(ctx) -> List[Stamp]:
    out: List[Stamp] = []
    anim, u = ctx.anim, ctx.u
    if anim == "attack_side" and 0.12 <= u <= 0.45:
        # The point's streak.
        tip = (ctx.hand[0] + BLADE + 4.0, ctx.hand[1])
        out.append((R.burst(K, 6.0 if u < 0.3 else 4.0, E.IMPACT, E.IMPACT_DARK, 6), tip, "thrust_tip", 0.0))
    elif anim in ("hit", "death"):
        out += [stamp for stamp in E._effects(ctx) if stamp[2] in ("struck", "lost_cap")]
        if anim == "death" and u >= 0.15:
            # The sabre turns over in the air and falls on the floor in front.
            t = min(1.0, (u - 0.15) / 0.45)
            at = (X.cx + lerp(10.0, 52.0, t), lerp(X.ground - 90.0, X.ground - 3.0, t) - 26.0 * math.sin(math.pi * t))
            out.append((_sabre(), at, "dropped_sabre", lerp(-60.0, 180.0, t)))
    return out


X.effects = _effects

ROWS = X.rows
FRAME_SIZE = X.frame
_render_frame = X.render_frame
render, main, render_canonical = R.entry_points(X, ACTOR_METADATA, DISPLAY_NAME)


def render_portraits(out_dir, **opts):
    """His portraits are frames of this sheet."""
    del opts
    return X.portraits(out_dir, {"default": ("idle", (1,), 0, False), "talking": ("taunt", (0, 2, 3, 4, 5, 6), 110, True)}, view_width=32.0)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}

if __name__ == "__main__":
    raise SystemExit(main())
