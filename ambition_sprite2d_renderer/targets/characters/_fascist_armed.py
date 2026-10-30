"""A Fascist Enforcer with a weapon drawn in his hand: the man of
``fascist_enforcer`` (his head, his cap, his uniform, his armband and his
build), and a weapon that is part of his sheet.

A module of an armed variant gives ``armed`` the weapon piece and draws its
own rows. The weapon is drawn from its grip along +x; a pose turns it with
two keys of its own:

``wa``
    The weapon's turn in the frame (degrees, +y down): 0 points it forward,
    -90 straight up.
``held``
    1 while it is in his hand. With 0 the hand is empty (he has dropped it).

The weapon is painted over the near arm, and the near hand is painted again
over its grip, so his fist closes round it. There is no drop shadow.
"""

from __future__ import annotations

from typing import Callable, List

from . import fascist_enforcer as E
from ._ai_era_kit import angle
from ._person_rig import Person, Stamp

#: Where a dropped weapon lies on the floor, from his middle (frame px).
DROPPED_AT = (-46.0, -3.0)


def armed(target: str, weapon: Callable[[], object], *, frame=(272, 184), cx: float = 118.0) -> Person:
    """A Person who wears the enforcer's pieces and holds ``weapon()`` in his
    near hand. ``frame`` is wider than the enforcer's: a weapon reaches."""
    X = Person(target, E.BUILD, frame=frame, ground=E.X.ground, cx=cx)
    assert X.K.scale == E.K.scale, "he wears the enforcer's pieces: one paint scale"
    X.torso, X.collar, X.neck, X.head_layers = E.X.torso, E.X.collar, E.X.neck, E.X.head_layers
    X.upper_arm, X.forearm, X.thigh, X.shin, X.hand, X.shoe = E.X.upper_arm, E.X.forearm, E.X.thigh, E.X.shin, E.X.hand, E.X.shoe
    for layer, fns in E.X.layers.items():
        X.layers[layer] += list(fns)
    X.set_rest(**E.X.rest)
    X.set_rest(wa=60.0, held=1.0)

    def in_hand(ctx) -> List[Stamp]:
        if float(ctx.pose["held"]) < 0.5:
            return []
        turn = float(ctx.pose["nht"]) + angle(ctx.elbow, ctx.hand)
        return [(weapon(), ctx.hand, "weapon", float(ctx.pose["wa"])), (X.hand(str(ctx.pose["nh"]), True), ctx.hand, "weapon_hand", turn)]

    X.layers["front"].append(in_hand)
    return X
