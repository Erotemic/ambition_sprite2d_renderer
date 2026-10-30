"""Sprite generator for the Fascist Clubman: a Fascist Enforcer with a heavy
club (Jon, 2026-10-30: "maybe we have a few facists with swords or clubs").

He is the enforcer (``fascist_enforcer``: the cap, the grey-green tunic, the
jackboots, the red armband with the faction's invented cog) and he carries a
long oak club bound in iron, which he calls "the persuader". He is slow, and
very sure of himself.

How he fights (notice, space, telegraph, attack):

* ``notice``: he starts, and then slaps the club into his palm.
* ``windup``: the club goes up high over his head and back, and he leans
  back under it. It is a long tell.
* ``attack_side``: he brings it down in front of him onto the floor, hard,
  and it stays there while he gets his breath (the long recovery).

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

TARGET_NAME = "fascist_clubman"
TARGET_BASENAME = TARGET_NAME
DISPLAY_NAME = "Fascist Clubman"

TRAITS = ["story", "humanoid", "enemy", "combatant", "authoritarian", "soldier", "brute"]

ACTOR_METADATA = {
    "actor": {"character_id": "npc_fascist_clubman", "display_name": DISPLAY_NAME},
    "body": {"body_plan": "HumanoidBiped", "body_kind": "Standard", "mass_class": "Medium", "traits": TRAITS, "locomotion_hint": "Walk"},
    "capabilities": {
        "traversal": {"walk": True, "jump": True, "climb": None, "fly": None, "swim": None, "crawl": None, "use_lifts": True, "door_access": ["public"]},
        "interactions": {"talk": True, "trade": None, "carry": None, "open_doors": ["public"]},
    },
    "brain": {"default_preset": "melee_brute_striker"},
    "actions": {"default_preset": "fascist_club_overhead"},
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
                {"t": 0.12, "event": "hitbox_active_start", "source": "explicit.profile.combat_humanoid"},
                {"t": 0.3, "event": "hitbox_active_end", "source": "explicit.profile.combat_humanoid"},
            ],
        },
        "combat.hurt": {"animation": "hit", "events": []},
        "combat.death": {"animation": "death", "events": []},
    },
    "authoring_description": (
        "A Fascist Enforcer with a long oak club bound in iron: the same peaked cap, grey-green "
        "tunic, jackboots and red armband (an invented cog; no real symbol). A slow, smug goon."
    ),
    "gameplay_description": "A slow overhead smash: the club goes up high (a long tell), comes down hard for two hearts, and stays down a while.",
    "dialogue_hints": {"barks": ["Meet the persuader.", "This is a dialogue. I am the club half.", "Hold still. It is for order."]},
}

OAK: RGBA = (138, 96, 58, 255)
OAK_DARK: RGBA = (92, 60, 36, 255)
OAK_LIGHT: RGBA = (176, 132, 86, 255)
IRON: RGBA = (86, 88, 96, 255)
IRON_LIGHT: RGBA = (150, 152, 160, 255)

#: The club, from his grip: a short handle behind, and a long head that
#: swells to its end, 36 px out.
LENGTH = 36.0


def _club():
    K = X.K

    def shape(d) -> None:
        K.poly(d, [K.at(-6.0, -1.8), K.at(8.0, -2.2), K.at(24.0, -4.0), K.at(LENGTH - 2.0, -5.0), K.at(LENGTH + 1.0, -3.0), K.at(LENGTH + 1.0, 3.0),
                   K.at(LENGTH - 2.0, 5.0), K.at(24.0, 4.0), K.at(8.0, 2.2), K.at(-6.0, 1.8)], WHITE)
        K.oval(d, K.at(-6.4, 0.0), 2.2, 2.4, WHITE)

    def detail(d) -> None:
        # The grain, the light along its top, the leather of the grip and
        # the two iron bands near its end, with studs.
        K.line(d, [K.at(6.0, -1.2), K.at(22.0, -2.6), K.at(LENGTH - 2.0, -3.6)], OAK_LIGHT, 0.6)
        K.line(d, [K.at(10.0, 0.8), K.at(20.0, 1.0), K.at(28.0, 2.0)], OAK_DARK, 0.4)
        K.rrect(d, -6.0, -2.0, 3.0, 2.0, 0.5, mix(OAK_DARK, (40, 30, 30, 255), 0.6))
        K.oval(d, K.at(-6.4, 0.0), 2.2, 2.4, IRON)
        for x in (25.0, 32.0):
            K.poly(d, [K.at(x - 1.2, -6.0), K.at(x + 1.2, -6.0), K.at(x + 1.2, 6.0), K.at(x - 1.2, 6.0)], IRON)
            K.line(d, [K.at(x - 0.6, -4.6), K.at(x - 0.6, 4.6)], IRON_LIGHT, 0.4)
            for y in (-3.0, 0.0, 3.0):
                K.oval(d, K.at(x, y), 0.5, 0.5, IRON_LIGHT)

    return K.solid(("club",), shape, OAK, detail, outline=1.0, rim=0.25, shade=0.3, shade_colour=OAK_DARK)


X = A.armed(TARGET_NAME, _club)
K = X.K
P = X.P

# ---- How he stands -----------------------------------------------------------

#: The club hanging from his fist at his side, its head by his boot.
X.set_rest(na=(4.0, 22.0), nh="fist", wa=78.0)


@X.row
def idle(i: int, n: int):
    _, s, _c = loop(i, n)
    return dict(E.idle(i, n), na=(4.0, 22.0 - 0.6 * s), nh="fist", wa=78.0 + 3.0 * s)


@X.row
def walk(i: int, n: int):
    # A heavy march: the club swings from his fist with his step.
    _, s, c = loop(i, n)
    return dict(E.walk(i, n), na=(4.0 - 3.0 * c, 21.0), nh="fist", wa=76.0 - 10.0 * c)


@X.row
def run(i: int, n: int):
    _, s, c = loop(i, n)
    return dict(E.run(i, n), na=(8.0 - 3.0 * c, 14.0), nh="fist", wa=40.0 - 10.0 * c)


#: Startled: up straight, brows up, the club off his shoulder.
STARTLED = X.P(hip=(-1.0, -1.0), lean=-6.0, head=(-0.6, -0.6, -8.0), na=(15.0, 10.0), nh="fist", wa=-40.0, eyes="wide", mouth="o", brows=1.0)
#: The club across him, its head in his far palm.
IN_PALM = X.P(hip=(0.0, 2.0), lean=4.0, head=(0.4, 0.4, 4.0), na=(4.0, 18.0), nh="fist", wa=-20.0, fa=(16.0, 8.0), fh="open", mouth="grit",
              brows=-1.0)


@X.row
def notice(i: int, n: int):
    # He starts; then he slaps the club into his palm, twice, and grins.
    lift = dict(IN_PALM, na=(6.0, 12.0), wa=-60.0)
    return X.keys(shot(i, n), [(0.0, X.full(X.rest)), (0.18, STARTLED, "snap"), (0.4, STARTLED), (0.55, IN_PALM, "in"), (0.7, lift), (0.85, IN_PALM, "in"),
                               (1.0, dict(IN_PALM, mouth="smile"))])


#: The club up high over his head and back, his weight back under it.
RAISED = X.P(hip=(-3.0, 3.0), lean=-12.0, head=(-0.4, 0.0, -6.0), na=(-3.0, -27.0), nab=-1.0, arm="under", nh="fist", wa=-158.0, fa=(10.0, 4.0),
             fh="fist", nf=(-9.0, 0.0, 0.0), ff=(10.0, 0.0, 0.0), mouth="grit", brows=-1.0, hem=(1.0, 2.0))


@X.row
def windup(i: int, n: int):
    _, s, _c = loop(i, n)
    return dict(RAISED, na=(-3.0, -27.0 + 0.6 * s), wa=-158.0 - 3.0 * s)


#: The club down on the floor in front of him, all his weight behind it.
DOWN = X.P(hip=(5.0, 11.0), lean=30.0, head=(1.0, 1.0, 10.0), na=(20.0, 15.0), nh="fist", wa=34.0, fa=(16.0, 12.0), fh="fist", nf=(-12.0, 0.0, 10.0),
           ff=(13.0, 0.0, 0.0), mouth="big", brows=-1.0, hem=(4.0, 1.0))
#: Bent over it, getting his breath.
WINDED = dict(DOWN, hip=(3.0, 9.0), lean=24.0, head=(1.0, 1.0, 16.0), na=(18.0, 17.0), wa=40.0, mouth="open", eyes="wince", brows=1.0)


@X.row
def attack_side(i: int, n: int):
    # Down hard from the raised tell, onto the floor; he stays bent over it.
    over = X.blend(RAISED, DOWN, 0.5)
    over = dict(over, wa=-60.0, arm="over")
    return X.keys(shot(i, n), [(0.0, RAISED), (0.08, over, "in"), (0.16, DOWN, "out"), (0.4, DOWN), (0.55, WINDED), (0.85, WINDED),
                               (1.0, X.full(X.rest))])


@X.row
def hit(i: int, n: int):
    return dict(E.hit(i, n), nh="fist", wa=40.0 if shot(i, n) < 0.25 else 70.0)


@X.row
def death(i: int, n: int):
    # The club drops out of his hand as he goes over (``_effects``).
    return dict(E.death(i, n), held=1.0 if shot(i, n) < 0.12 else 0.0, wa=40.0)


@X.row
def taunt(i: int, n: int):
    # He slaps the club into his palm, slowly, three times.
    lift = dict(IN_PALM, na=(6.0, 12.0), wa=-60.0)
    return X.keys(shot(i, n), [(0.0, X.full(X.rest)), (0.15, IN_PALM), (0.3, lift), (0.45, IN_PALM, "in"), (0.6, lift), (0.75, IN_PALM, "in"),
                               (1.0, X.full(X.rest))])


X.rows = [("idle", 8, 160), ("walk", 8, 115), ("run", 8, 85), ("notice", 10, 85), ("windup", 4, 110), ("attack_side", 12, 80), ("hit", 5, 90),
          ("death", 8, 115), ("taunt", 10, 100)]

# ---- What his club does ------------------------------------------------------


def _head(ctx):
    a = math.radians(float(ctx.pose["wa"]))
    return (ctx.hand[0] + math.cos(a) * (LENGTH - 2.0), ctx.hand[1] + math.sin(a) * (LENGTH - 2.0))


def _effects(ctx) -> List[Stamp]:
    out: List[Stamp] = []
    anim, u = ctx.anim, ctx.u
    if anim == "attack_side" and 0.14 <= u <= 0.4:
        at = _head(ctx)
        late = u > 0.26
        out.append((R.burst(K, 8.0 if late else 12.0, E.IMPACT, E.IMPACT_DARK, 8), (at[0] + 2.0, at[1] - 2.0), "smash", 0.0))
        out.append((R.dust(K, 3.4 if late else 4.6, E.DUST, E.DUST_DARK), (at[0] + 10.0, ctx.ground - 3.0), "dust_ahead", 0.0))
        out.append((R.dust(K, 3.0 if late else 4.0, E.DUST, E.DUST_DARK), (at[0] - 9.0, ctx.ground - 3.0), "dust_behind", 0.0))
    elif anim in ("notice", "taunt") and ctx.pose["wa"] > -25.0 and ctx.pose["fh"] == "open" and float(ctx.pose["na"][1]) > 17.0:
        out.append((R.burst(K, 5.0, E.IMPACT, E.IMPACT_DARK, 6), (ctx.far_hand[0] + 3.0, ctx.far_hand[1] - 3.0), "smack", 0.0))
    elif anim in ("hit", "death"):
        out += [stamp for stamp in E._effects(ctx) if stamp[2] in ("struck", "lost_cap")]
        if anim == "death" and u >= 0.12:
            t = min(1.0, (u - 0.12) / 0.4)
            at = (X.cx + lerp(14.0, 40.0, t), lerp(X.ground - 80.0, X.ground - 5.0, t) - 12.0 * math.sin(math.pi * t))
            out.append((_club(), at, "dropped_club", lerp(-100.0, 0.0, t)))
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
