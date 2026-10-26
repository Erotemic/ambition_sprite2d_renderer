"""A person of the cast in the round, as three things a generator can choose:
a ``Body``, a ``Look`` and a ``Stance``.

* A ``Body`` is what the round needs of a rig: where its joints are, and how
  it draws its own pieces (its sleeves and hands, its legs, neck and shoes;
  its head, trunk and back layers in the views it has art for). A
  ``_person_rig.Person`` is a body as it is (``PersonBody``); a rig drawn
  without ``Person`` (Erdish, Ramen-nujan) writes the few methods itself.
* A ``Look`` is what 3D draws in the views with no art: a head
  (``Head3D``), a trunk (``_round_wear.Trunk``), a hat, what is worn on the
  head (a circlet, antlers) and what hangs behind (a cloak, hair, a staff).
  It is data.
* A ``Stance`` is how the person stands: where each hand is, how far the
  feet are staggered.

``Round(body, look, stance)`` is a person in the round: ``figure()`` is its
``_person_round.Figure``, ``turnaround(path)`` its eight views over its own
art. A new person of the cast is a new choice of the three.

The rule of the round (Jon, 2026-10-25): the 3D only places things, orders
them and says how they turn; the cast's own drawings draw them. A character's
own art is drawn in every view it has, and 3D draws only the others.

Run ``python -m ambition_sprite2d_renderer.targets.characters._round_cast
MODULE OUT.png`` to draw the turnaround of a module that has ``ROUND``.
"""

from __future__ import annotations

import argparse
import importlib
import math
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Callable, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
from PIL import Image

from . import _person_round as O
from ._ai_era_kit import Kit

Vec = Tuple[float, float, float]
Point = Tuple[float, float]


# ---- What a body draws -------------------------------------------------------


def _between(a: Point, b: Point, t: float) -> Point:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def seg_bones(K: Kit, tag: str, a: Point, b: Point, segs) -> list:
    """The bones of a limb dressed in ``segs`` (``_person_rig.Seg``) from
    frame point ``a`` to ``b``, as ``Person.limb`` places them."""
    from ._person_rig import bone

    out = []
    for t0, t1, w0, w1, colour in segs:
        out.append((_between(a, b, t0), _between(a, b, t1),
                    lambda edge, length, w0=w0, w1=w1, colour=colour: bone(K, tag, length, w0, w1, colour, edge)))
    return out


def limb_piece(K: Kit, name: str, joints: Sequence[Vec], bones: Callable[[Sequence[Point], bool], list], *, hand: Optional[Callable[[bool], object]] = None,
               anchor: Optional[Vec] = None, lead: float = 0.0, extra: Optional[Callable] = None) -> O.Drawn:
    """A limb through 3D ``joints``, drawn as the cast draws one: ``bones(
    points, near)`` gives its bones between the projected joints (``(a, b,
    make)``, see ``place_bones``); ``hand(near)``, a piece placed at the last
    joint along the last bone; ``extra(img, points, near)`` paints what else
    is on it (a patch on an elbow). It is as near as ``anchor`` (default: the
    last joint)."""

    def draw(view: O.View, far: bool, at) -> Image.Image:
        pts = [at(p) for p in joints]
        near = not far
        img = K.new_frame()
        O.place_bones(K, img, name, bones(pts, near))
        if extra is not None:
            extra(img, pts, near)
        if hand is not None:
            K.place(img, hand(near), pts[-1], f"{name}_hand", O._angle(pts[-2], pts[-1]))
        return img

    return O.Drawn(name, tuple(anchor if anchor is not None else joints[-1]), draw, dims=True, lead=lead, joints=[tuple(j) for j in joints])


def shoes(name: str, ankle: Sequence[float], side: Callable[[bool], object], front: Callable[[], object], back: Callable[[], object]) -> O.Sprite:
    """A shoe in every view: ``front()`` seen from the toe, ``back()`` from
    the heel, ``side(near)`` from the side, its toe to the side the foot
    points (mirrored for the left)."""

    def draw(view: O.View, far: bool):
        turn = O.facing(view)
        toward = math.cos(math.radians(turn))
        if toward > 0.85:
            return front(), 0.0, False
        if toward < -0.85:
            return back(), 0.0, False
        return side(not far), 0.0, turn < 0.0

    return O.Sprite(name, tuple(ankle), draw, dims=True, lead=3.0)


def own_turns(front: bool, mirror: bool = True, side: bool = False) -> Callable[[O.View], bool]:
    """The views a character's own art is drawn for (``own_art``)."""
    turns = (45.0,) + ((-45.0,) if mirror else ()) + ((0.0,) if front else ()) + ((90.0,) + ((-90.0,) if mirror else ()) if side else ())
    return O.near_turn(*turns)


def own_art(name: str, anchor: Sequence[float], three_quarter: Optional[Callable[[], object]], front: Optional[Callable[[], object]] = None, *,
            side: Optional[Callable[[], object]] = None, degrees: float = 0.0, lead: float = 0.0, mirror: bool = True) -> O.Sprite:
    """A piece of a character's own art in the views it is drawn for: its
    three-quarter view, its mirror for the left (``mirror``: only a piece that
    is the same on both sides; a pocket on one side is not), its front view
    and its side view if it has them (a head made with the cast's front or
    side makers, for a character drawn in one view). Another piece draws the
    other views (``not_in(sprite.when)``)."""

    def draw(view: O.View, far: bool):
        turn = O.facing(view)
        if abs(turn) <= 10.0:
            return (front() if front is not None else None), 0.0, False
        if abs(abs(turn) - 90.0) <= 10.0:
            return (side() if side is not None else None), 0.0, turn < 0.0
        return three_quarter(), degrees, turn < 0.0  # type: ignore[misc]

    return O.Sprite(name, tuple(anchor), draw, when=own_turns(front is not None, mirror, side is not None), lead=lead)


def not_in(when: Optional[Callable[[O.View], bool]]) -> Optional[Callable[[O.View], bool]]:
    """The views ``when`` is not (all views when there is no ``when``)."""
    return None if when is None else (lambda view: not when(view))


# ---- Body --------------------------------------------------------------------


class Body:
    """What the round needs of a rig. A subclass gives:

    ``K``, ``frame``, ``cx``, ``ground``, ``hip_up``: its paint box and its
    sheet's frame; ``upper``, ``fore``, ``thigh``, ``shin``: its bones;
    ``joints(stagger)``: its joints at rest in 3D (``shoulders``, ``hips``,
    ``ankles`` by side ``"r"``/``"l"``; ``neck``, ``head``, ``throat``; and
    ``wrist(near, l)``, the wrist of its rest pose put ``l`` to the side);
    ``hand_mode(near)``; ``arm``, ``leg``, ``neck``, ``shoes``: its own
    pieces placed at 3D joints; ``own(J)``: its own art (``own_art``,
    ``own_layers``) by name: ``"head"``, ``"trunk"``, ``"back"`` and any
    other (a collar, a scarf), any of them missing."""

    K: Kit
    frame: Tuple[int, int]
    cx: float
    ground: float
    hip_up: float
    upper: float
    fore: float
    thigh: float
    shin: float

    def joints(self, stagger: float = 0.0) -> SimpleNamespace:
        raise NotImplementedError

    def hand_mode(self, near: bool) -> str:
        raise NotImplementedError

    def arm(self, name: str, shoulder: Vec, elbow: Vec, wrist: Vec, mode: str) -> O.Drawn:
        raise NotImplementedError

    def leg(self, name: str, hip: Vec, knee: Vec, ankle: Vec) -> O.Drawn:
        raise NotImplementedError

    def neck(self, base: Vec, top: Vec) -> O.Drawn:
        raise NotImplementedError

    def shoes(self, name: str, ankle: Vec) -> O.Sprite:
        raise NotImplementedError

    def own(self, J: SimpleNamespace) -> Dict[str, object]:
        return {}

    def own_frames(self) -> Dict[str, Image.Image]:
        """Its own art in the views it has (``view key -> frame``), for the
        turnaround to show under the views from 3D."""
        return {}


class PersonBody(Body):
    """A ``_person_rig.Person`` as a body: its joints lifted from its two
    views (``joints``), its pieces drawn by its own makers. ``back_shoe``:
    its shoe seen from the heel (``make_back_shoe`` in its colours).
    ``back_layers``:
    the layers of its own art behind it (a cloak, hair, a staff), drawn in
    its three-quarter view. ``mirror``: which of its head and trunk are the
    same on both sides, so their mirror is its left three-quarter view."""

    def __init__(self, person, back_shoe: Callable[[], object], *, back_layers: Sequence[str] = (), mirror: Sequence[str] = ("head", "trunk"),
                 anim: str = "idle") -> None:
        self.person = person
        self.K = person.K
        self.frame, self.cx, self.ground, self.hip_up = person.frame, person.cx, person.ground, person.b.hip_up
        self.upper, self.fore, self.thigh, self.shin = person.b.upper, person.b.fore, person.b.thigh, person.b.shin
        self.back_shoe = back_shoe
        self.back_layers = tuple(back_layers)
        self.mirror = tuple(mirror)
        self.anim = anim

    def joints(self, stagger: float = 0.0) -> SimpleNamespace:
        """The joints standing at rest, lifted from the person's two views:
        its three-quarter view (``Build``, the feet of its rest pose) says
        where each is drawn across, its front view (``front_span``, the feet
        of ``FRONT_REST``) how far to the side, and ``lift`` how far forward.
        ``stagger``: the near foot back and the far foot forward by this
        much, so a side view shows both."""
        from ._person_rig import FRONT_REST

        person = self.person
        b, U = person.b, person.U
        sw, hw = person.front_span
        rest = person.full(person.rest)
        foot = hw + FRONT_REST["lf"][0] * U
        up = b.hip_up - b.ankle_up
        head = (0.0, b.neck[1] + b.head_up[1], O.lift(b.neck[0] + b.head_up[0], 0.0))

        def wrist(near: bool, l: float) -> Vec:
            x, y = self.body_point(person.arm_joints(rest, near)[2])
            return (l, y, O.lift(x, l))

        return SimpleNamespace(
            shoulders={"r": (-sw, b.near_shoulder[1], O.lift(b.near_shoulder[0], -sw)), "l": (sw, b.far_shoulder[1], O.lift(b.far_shoulder[0], sw))},
            hips={"r": (-hw, 0.0, O.lift(b.near_hip[0], -hw)), "l": (hw, 0.0, O.lift(b.far_hip[0], hw))},
            ankles={"r": (-foot, up, O.lift(rest["nf"][0] * U, -foot) - stagger), "l": (foot, up, O.lift(rest["ff"][0] * U, foot) + stagger)},
            neck=(0.0, b.neck[1], O.lift(b.neck[0], 0.0)), head=head, throat=tuple(np.asarray(head) + [0.0, 4.0, -0.4]), rest=rest, wrist=wrist)

    def body_point(self, p: Sequence[float]) -> Point:
        """A frame point as ``(x, y)`` in body space (from the hips)."""
        return (p[0] - self.cx, p[1] - self.ground + self.hip_up)

    def hand_mode(self, near: bool) -> str:
        return str(self.person.full(self.person.rest)["nh" if near else "fh"])

    def arm(self, name, shoulder, elbow, wrist, mode):
        p, K = self.person, self.K
        return limb_piece(K, name, [shoulder, elbow, wrist],
                          lambda pts, near: seg_bones(K, name, pts[0], pts[1], p.upper_arm(near)) + seg_bones(K, name, pts[1], pts[2], p.forearm(near)),
                          hand=lambda near: p.hand(mode, near), lead=3.0)

    def leg(self, name, hip, knee, ankle):
        p, K = self.person, self.K
        # A leg goes under the trunk, as the cast paints a leg that does not kick.
        return limb_piece(K, name, [hip, knee, ankle],
                          lambda pts, near: seg_bones(K, name, pts[0], pts[1], p.thigh(near)) + seg_bones(K, name, pts[1], pts[2], p.shin(near)),
                          anchor=knee, lead=-12.0)

    def neck(self, base, top):
        p, K = self.person, self.K

        def draw(view, far, at):
            if p.neck is None:
                return None
            a, b = at(base), at(top)
            img = K.new_frame()
            K.place(img, p.neck(float(round(math.dist(a, b)))), a, "neck", O._angle(a, b))
            return img

        return O.Drawn("neck", tuple(base), draw)

    def shoes(self, name, ankle):
        return shoes(name, ankle, self.person.shoe, self.person.front_shoe, self.back_shoe)

    def own(self, J):
        from ._person_rig import FRONT_REST

        p, K = self.person, self.K
        has_front = bool(p.front_poses)
        out: Dict[str, object] = {
            "trunk": own_art("own_trunk", (0.0, 0.0, 0.0), lambda: p.torso(0, 0), p.front_torso if has_front else None, lead=0.4,
                             mirror="trunk" in self.mirror),
            "head": own_art("own_head", J.head, lambda: O.composed(K, p.head_layers(J.rest)),
                            (lambda: O.composed(K, p.front_head_layers(dict(FRONT_REST)))) if has_front else None, lead=9.0,
                            mirror="head" in self.mirror),
        }
        if self.back_layers:
            out["back"] = own_layers(p, self.back_layers, anim=self.anim)
        return out

    def own_frames(self):
        rows = {name: n for name, n, _ms in self.person.rows}
        out = {"front_3q": self.person.render_frame(self.anim, 0, rows[self.anim])}
        if "front" in rows:
            out["front"] = self.person.render_frame("front", 0, rows["front"])
        return out


@dataclass(eq=False)
class RigBody(Body):
    """A rig drawn by hand on ``_ai_era_kit`` (not a ``Person``: Erdish,
    Ramen-nujan) as a body, from its parts. ``rest_joints``: its joints at
    rest in 3D, as ``Body.joints`` returns them (the stagger is put on
    here); ``arm_bones(pts, near)`` and ``leg_bones(pts, near)``: its bones
    between the projected joints (shoulder, elbow, wrist; hip, knee, ankle;
    see ``place_bones``); ``hand(mode, near)``; ``arm_extra(side, img, pts,
    near)``: what else is on an arm (a patch on an elbow); ``neck(length)``:
    its neck, or none (a scarf hides it); its shoes; ``own(J)`` and
    ``own_frames()`` as ``Body`` has them."""

    K: Kit
    frame: Tuple[int, int]
    cx: float
    ground: float
    hip_up: float
    upper: float
    fore: float
    thigh: float
    shin: float
    rest_joints: SimpleNamespace
    hand_modes: Tuple[str, str]
    arm_bones: Callable
    leg_bones: Callable
    hand: Callable
    shoe: Callable
    front_shoe: Callable
    back_shoe: Callable
    own_pieces: Callable = lambda J: {}
    frames: Callable = lambda: {}
    neck_piece: Optional[Callable] = None
    arm_extra: Optional[Callable] = None

    def joints(self, stagger=0.0):
        J = self.rest_joints
        ankles = {"r": tuple(np.asarray(J.ankles["r"]) - [0.0, 0.0, stagger]), "l": tuple(np.asarray(J.ankles["l"]) + [0.0, 0.0, stagger])}
        return SimpleNamespace(**{**vars(J), "ankles": ankles})

    def hand_mode(self, near):
        return self.hand_modes[0 if near else 1]

    def arm(self, name, shoulder, elbow, wrist, mode):
        extra = None if self.arm_extra is None else (lambda img, pts, near: self.arm_extra(name[0], img, pts, near))
        return limb_piece(self.K, name, [shoulder, elbow, wrist], self.arm_bones, hand=lambda near: self.hand(mode, near), extra=extra, lead=3.0)

    def leg(self, name, hip, knee, ankle):
        # A leg goes under the trunk, as the cast paints a leg that does not kick.
        return limb_piece(self.K, name, [hip, knee, ankle], self.leg_bones, anchor=knee, lead=-12.0)

    def neck(self, base, top):
        K, make = self.K, self.neck_piece

        def draw(view, far, at):
            if make is None:
                return None
            a, b = at(base), at(top)
            img = K.new_frame()
            K.place(img, make(round(math.dist(a, b))), a, "neck", O._angle(a, b))
            return img

        return O.Drawn("neck", tuple(base), draw)

    def shoes(self, name, ankle):
        return shoes(name, ankle, self.shoe, self.front_shoe, self.back_shoe)

    def own(self, J):
        return self.own_pieces(J)

    def own_frames(self):
        return self.frames()


def lifted_joints(*, shoulders: Tuple[Point, Point], hips: Tuple[Point, Point], feet: Tuple[float, float], neck: Point, head: Point,
                  widths: Tuple[float, float, float], hip_up: float, ankle_up: float, wrists: Tuple[Point, Point], throat: Vec = (0.0, 4.0, -0.6)) -> SimpleNamespace:
    """The joints at rest of a rig with only a three-quarter view: each joint
    where that view draws it (``(x, y)`` from the hips; ``feet``: how far
    across each foot is), ``widths`` how far to the side the shoulders, the
    hips and the feet are from the front (read from the build: there is no
    front view), and ``lift`` how far forward. ``wrists``: where the view
    draws the near and the far wrist (``wrist(near, l)`` puts one ``l`` to the
    side)."""
    sw, hw, fw = widths

    def wrist(near: bool, l: float) -> Vec:
        x, y = wrists[0 if near else 1]
        return (l, y, O.lift(x, l))

    head3 = (0.0, head[1], O.lift(head[0], 0.0))
    return SimpleNamespace(
        shoulders={"r": (-sw, shoulders[0][1], O.lift(shoulders[0][0], -sw)), "l": (sw, shoulders[1][1], O.lift(shoulders[1][0], sw))},
        hips={"r": (-hw, 0.0, O.lift(hips[0][0], -hw)), "l": (hw, 0.0, O.lift(hips[1][0], hw))},
        ankles={"r": (-fw, hip_up - ankle_up, O.lift(feet[0], -fw)), "l": (fw, hip_up - ankle_up, O.lift(feet[1], fw))},
        neck=(0.0, neck[1], O.lift(neck[0], 0.0)), head=head3, throat=tuple(np.asarray(head3) + throat), wrist=wrist)


def own_layers(person, layers: Sequence[str], *, anim: str = "idle", lead: float = -12.0) -> O.Sprite:
    """What a ``Person`` paints in its own ``layers`` (``back``: a cloak,
    hair down the back, a staff across it) in the first frame of ``anim``,
    in its three-quarter view only: these are seldom the same on both sides,
    so a mirror would put them wrong. The look draws the other views."""
    K = person.K
    count = {name: n for name, n, _ms in person.rows}[anim]

    def draw(view: O.View, far: bool):
        ctx = person.frame_context(anim, 0, count)
        canvas = K.scratch()
        home = K.home
        for layer in layers:
            for fn in person.layers[layer]:
                for piece, at, name, degrees in fn(ctx):
                    K.place(canvas, piece, (home[0] + at[0] - person.cx, home[1] + at[1] - person.ground + person.b.hip_up), name, degrees)
        return K._cut(canvas), 0.0, False

    return O.Sprite("own_" + "_".join(layers), (0.0, 0.0, 0.0), draw, when=O.near_turn(45.0), lead=lead)


# ---- Look and stance ----------------------------------------------------------


@dataclass
class Look:
    """What 3D draws for the views a person has no art for. ``head_pieces``
    are worn on the head (a hat, a circlet, antlers; ``piece(K, J)``) and go
    with the head; ``back_pieces`` hang behind (a cloak, hair, a staff) and
    go with the back layers. See ``_round_wear``."""

    head: O.Head3D
    trunk: object
    head_pieces: Sequence[object] = ()
    back_pieces: Sequence[object] = ()
    #: ``(name, piece)``: drawn in the views where the body's own art has no
    #: piece of that name (``Body.own``: a scarf for its scarf, a collar for
    #: its collar), or in every view when it has none.
    pieces: Sequence[Tuple[str, object]] = ()
    #: Where the head is drawn, if not at the body's ``J.head``.
    head_at: Optional[Vec] = None


@dataclass(frozen=True)
class Hand:
    """Where a hand is in a stance: the wrist of the rest pose put ``l`` to
    the side (``at`` None), or the 3D point ``at``; its elbow goes toward
    ``pole``; ``mode`` is what the hand does (default: as at rest)."""

    l: float = 0.0
    pole: Vec = (0.0, 0.3, -1.0)
    at: Optional[Vec] = None
    mode: Optional[str] = None


@dataclass
class Stance:
    hands: Dict[str, Hand] = field(default_factory=dict)
    #: The near foot back and the far foot forward by this much.
    stagger: float = 0.0


@dataclass
class Round:
    """A person in the round."""

    title: str
    body: Body
    look: Look
    stance: Stance = field(default_factory=Stance)

    def figure(self) -> O.Figure:
        body, look, stance = self.body, self.look, self.stance
        J = body.joints(stance.stagger)
        own = body.own(J)
        def unless(name: str):
            return not_in(getattr(own.get(name), "when", None))

        head_when, back_when = unless("head"), unless("back")
        trunk = look.trunk.part()
        trunk.when = unless("trunk")
        head = O.head_part(look.head, look.head_at or J.head)
        head.when = head_when
        parts: List[object] = [trunk, head]
        for piece in look.head_pieces:
            made = piece.piece(body.K, J, look.head_at or J.head)
            made.when = head_when
            parts.append(made)
        for piece in look.back_pieces:
            made = piece.piece(body.K, J, look.head_at or J.head)
            made.when = back_when
            parts.append(made)
        for name, piece in look.pieces:
            made = piece.piece(body.K, J, look.head_at or J.head)
            made.when = unless(name)
            parts.append(made)
        parts += list(own.values())
        parts.append(body.neck(J.neck, J.throat))
        for side, near in (("r", True), ("l", False)):
            hand = stance.hands.get(side, Hand(l=-6.0 if near else 6.0))
            target = hand.at if hand.at is not None else J.wrist(near, hand.l)
            elbow, wrist = O.two_bone(J.shoulders[side], target, body.upper, body.fore, hand.pole)
            knee, ankle = O.two_bone(J.hips[side], J.ankles[side], body.thigh, body.shin, (0.0, 0.0, 1.0))
            parts += [body.arm(f"{side}_arm", J.shoulders[side], elbow, wrist, hand.mode or body.hand_mode(near)),
                      body.leg(f"{side}_leg", J.hips[side], knee, ankle), body.shoes(f"{side}_shoe", ankle)]
        return O.Figure(parts, body.frame, body.cx, body.ground, body.hip_up, trunk=(0.0, -20.0, 0.4))

    def draw(self, view: Union[str, O.View]) -> Image.Image:
        return O.draw(self.body.K, self.figure(), O.VIEW_BY_KEY[view] if isinstance(view, str) else view)

    def turnaround(self, path) -> Path:
        """Its eight views, with its own art under the views it draws."""
        return O.turnaround(self.body.K, self.figure(), path, title=f"{self.title} in the round", own=self.body.own_frames())


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Draw the turnaround of a person of the cast in the round.")
    parser.add_argument("module", help="a module of targets/characters that has ROUND (davy_hylbert, erdish, ...)")
    parser.add_argument("out", type=Path)
    args = parser.parse_args(argv)
    module = importlib.import_module(f"{__package__}.{args.module}")
    print(module.ROUND.turnaround(args.out))
    return 0


__all__ = ["RigBody", "lifted_joints", "Body", "Hand", "Look", "PersonBody", "Round", "Stance", "limb_piece", "not_in", "own_art", "own_layers", "own_turns", "seg_bones", "shoes"]


if __name__ == "__main__":
    raise SystemExit(main())
