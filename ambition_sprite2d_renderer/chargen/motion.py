"""The motion library: every row the cast performs, for any generated body.

Each clip is a few 3D key poses (``pose3d.Pose``) with their timing, built
from the body's own lengths, so a tall slim person and a short heavy one
both reach their own hands to the same places. ``library_clips`` solves every
clip in a view into that view's rig channels, a key per frame, so the five
views perform the same motion.

Rows: the union of the hand-made cast's rows and the rows the game asks for
(``fighter_motion_vocabulary.yaml``, the runtime's ``CharacterAnim`` and state
chains, the moveset fallbacks), plus social rows. :data:`PUBLISH_VIEW` says
which view the sprite sheet draws each row from (fights from the side, a
ladder from behind, a chat at three-quarters); ``turnaround`` and
``turn_away`` pass through the back views.

Posing rules followed throughout: a strike has anticipation (a wind-up the
other way), contact, follow-through past the target and a recovery; weight
shows in the hips (they drop into a landing, rise on a push-off); and the
trunk leans along the line of the action. No pose is a T-pose.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Dict, List, Optional, Sequence, Tuple

from .body import Figure
from .face import brows_part, eyes_part, face_channels, mouth_part
from .geometry import View
from .pose3d import ITEM_REST, Foot, Hand, Pose, RestFrame, ViewSolver, blend

Vec = Tuple[float, float, float]


@dataclass
class Clip:
    name: str
    frames: int
    ms: int
    loop: bool
    keys: List[Tuple[float, Pose]]
    #: The view the sprite sheet draws this row from.
    view: str = "side"
    category: str = "misc"


# ---- the vocabulary of poses -----------------------------------------------------------------


class Kit:
    """Pose builders in the body's own units: arm reach ``A``, leg length
    ``L``, height ``H``. Hands are offsets from the shoulder in the trunk
    frame (``fwd``, ``down``, ``out`` as parts of ``A``); feet are offsets
    from their rest place on the ground (or, ``body=True``, from the hip),
    as parts of ``L``."""

    def __init__(self, fig: Figure) -> None:
        self.fig = fig
        self.rest = RestFrame(fig)
        self.A = self.rest.ua["right"] + self.rest.fa["right"]
        self.L = self.rest.th["right"] + self.rest.sh["right"]
        self.H = fig.H
        #: How far the figure stands above the ground (on geta).
        self.lift = -fig.sole_y
        r = self.rest.rest_hand("right").at
        self.rest_hand = (r[2] / self.A, r[1] / self.A, -r[0] / self.A)

    # hands and feet
    def hand(self, side: str, fwd: float, down: float, out: float = 0.15, *, pole: Vec = (0.25, 0.2, -1.0), wrist: float = 0.0,
             item: Optional[float] = None, item_out: float = 0.0, two_hand: float = 0.0) -> Hand:
        """``wrist``: the hand bent off its forearm's line, degrees (a held
        item runs across the fist, so it turns with it). ``item``: the angle
        above forward (degrees; 90 straight up, 180 back, -90 down) a held
        item points, which turns the wrist in its place; ``item_out`` tips it
        out to the side. ``two_hand``: the other hand closes on the item
        this many cm along it."""
        sgn = -1.0 if side == "right" else 1.0
        at = (sgn * out * self.A, down * self.A, fwd * self.A)
        p = (sgn * pole[0], pole[1], pole[2])
        it = None
        if item is not None:
            r = math.radians(item)
            it = (sgn * item_out, -math.sin(r), math.cos(r))
        return Hand(at, p, wrist, it, two_hand)

    def foot(self, side: str, fwd: float = 0.0, lift: float = 0.0, out: float = 0.0, toe: float = 0.0, *, pole: Vec = (0.0, 0.0, 1.0)) -> Foot:
        sgn = -1.0 if side == "right" else 1.0
        return Foot((sgn * out * self.L, -lift * self.L, fwd * self.L), toe, (sgn * pole[0], pole[1], pole[2]))

    def bfoot(self, side: str, fwd: float, down: float, out: float = 0.05, toe: float = 0.0, *, pole: Vec = (0.0, 0.0, 1.0)) -> Foot:
        sgn = -1.0 if side == "right" else 1.0
        return Foot((sgn * out * self.L, down * self.L, fwd * self.L), toe, (sgn * pole[0], pole[1], pole[2]), True)

    def relax(self, side: str) -> Hand:
        f, d, o = self.rest_hand
        return self.hand(side, f * 0.9, d * 0.95, o)

    # whole poses
    def pose(self, *, root=(0.0, 0.0, 0.0), spin=0.0, lean=0.0, side=0.0, head=(0.0, 0.0), rh=None, lh=None, rf=None, lf=None,
             face: str = "neutral", vis: str = "rest", blink: float = 0.0, ground: bool = False, **extra) -> Pose:
        """A pose. ``root`` is (forward, UP, out) in parts of ``H``.
        ``ground``: the body lies or sits on the ground, so a figure raised
        on geta is lowered by their height (its feet stand on nothing)."""
        hands = {"right": rh or self.relax("right"), "left": lh or self.relax("left")}
        feet = {}
        if rf is not None:
            feet["right"] = rf
        if lf is not None:
            feet["left"] = lf
        r = (root[2] * self.H, -root[1] * self.H, root[0] * self.H)
        if ground and self.lift:
            r = (r[0], r[1] + self.lift, r[2])
        return Pose(root=r, spin=spin, lean=lean, side=side, head=head, hands=hands, feet=feet,
                    face=face_channels(face, vis, blink=blink), extra=extra)

    def stand(self, **kw) -> Pose:
        return self.pose(**kw)

    def guard(self, **kw) -> Pose:
        """A ready stance: knees soft, weight forward, fists up."""
        base = dict(root=(0.0, -0.035, 0.0), lean=8.0, head=(-4.0, 0.0),
                    rh=self.hand("right", 0.45, 0.45, 0.08, pole=(0.4, 0.6, -0.4)),
                    lh=self.hand("left", 0.3, 0.5, 0.12, pole=(0.4, 0.6, -0.4)),
                    rf=self.foot("right", 0.12, 0.0, 0.03), lf=self.foot("left", -0.12, 0.0, 0.03), face="determined")
        base.update(kw)
        return self.pose(**base)

    def crouch(self, depth: float = 0.22, **kw) -> Pose:
        base = dict(root=(0.0, -depth, 0.0), lean=22.0 * depth / 0.22, head=(-14.0 * depth / 0.22, 0.0),
                    rh=self.hand("right", 0.5, 0.55, 0.15), lh=self.hand("left", 0.4, 0.6, 0.18),
                    rf=self.foot("right", 0.08, 0.0, 0.05), lf=self.foot("left", -0.08, 0.0, 0.05, toe=-8))
        base.update(kw)
        return self.pose(**base)

    def air(self, **kw) -> Pose:
        """In the air: knees tucked a little, arms out for balance."""
        base = dict(lean=6.0, rh=self.hand("right", 0.35, 0.55, 0.35, pole=(0.6, 0.4, -0.5)),
                    lh=self.hand("left", -0.1, 0.6, 0.4, pole=(0.6, 0.4, -0.5)),
                    rf=self.bfoot("right", 0.25, 0.75), lf=self.bfoot("left", -0.1, 0.85))
        base.update(kw)
        return self.pose(**base)

    def lying(self, *, face_up: bool = True, **kw) -> Pose:
        """Flat on the ground (on the back, or face down)."""
        s = -88.0 if face_up else 88.0
        base = dict(root=(-0.02 if face_up else 0.02, -0.4, 0.0), spin=s,
                    rh=self.hand("right", 0.05, 0.85, 0.35), lh=self.hand("left", -0.05, 0.85, 0.4),
                    rf=self.bfoot("right", 0.05, 0.98, 0.06), lf=self.bfoot("left", 0.0, 0.98, 0.1), ground=True)
        base.update(kw)
        return self.pose(**base)

    def sitting(self, **kw) -> Pose:
        base = dict(root=(-0.04, -0.21, 0.0), lean=4.0, rh=self.hand("right", 0.55, 0.62, 0.15), lh=self.hand("left", 0.5, 0.65, 0.2),
                    rf=self.foot("right", 0.42, 0.0, 0.02), lf=self.foot("left", 0.36, 0.0, 0.02))
        base.update(kw)
        return self.pose(**base)

    def hang(self, **kw) -> Pose:
        """Hanging by the hands from a ledge above and in front."""
        base = dict(root=(-0.03, -0.0, 0.0), lean=-4.0, head=(-12.0, 0.0),
                    rh=self.hand("right", 0.3, -0.85, 0.12, pole=(0.5, 0.0, -0.6)), lh=self.hand("left", 0.25, -0.88, 0.14, pole=(0.5, 0.0, -0.6)),
                    rf=self.bfoot("right", 0.12, 0.95), lf=self.bfoot("left", 0.02, 0.97), face="determined")
        base.update(kw)
        return self.pose(**base)


def _seq(name, frames, ms, loop, keys, view="side", cat="misc") -> Clip:
    return Clip(name, frames, ms, loop, keys, view, cat)


def _cycle(poses: Sequence[Pose]) -> List[Tuple[float, Pose]]:
    """Evenly spaced keys of a loop that ends where it began."""
    n = len(poses)
    return [(i / n, p) for i, p in enumerate(poses)] + [(1.0, poses[0])]


def _even(poses: Sequence[Pose]) -> List[Tuple[float, Pose]]:
    n = len(poses)
    return [(i / max(1, n - 1), p) for i, p in enumerate(poses)]


# ---- the library -----------------------------------------------------------------------------


#: How a held item is held: each grip class poses the item clips its own
#: way (a sword is raised, a gun aimed, a staff planted, a shield held up,
#: a heavy thing carried in both hands).
GRIPS = ("blade", "two_handed", "gun", "staff", "shield", "tool", "carried", "thrown")


def _grip_poses(k: "Kit", grip: str) -> Dict[str, object]:
    """The item poses of one grip class: ``ready`` (item_hold), ``crouch``,
    the ``throw_*`` keys and ``swings`` (name -> wind, hit, follow)."""
    R, Lf = "right", "left"
    two = 0.0
    if grip == "two_handed":
        two = 0.22 * k.A
    elif grip == "staff":
        two = 0.0

    def h(fwd, down, out=0.1, item=0.0, pole=(0.3, 0.6, -0.5), **kw):
        return k.hand(R, fwd, down, out, pole=pole, item=item, two_hand=two, **kw)

    def guard(**kw):
        return k.guard(face=kw.pop("face", "determined"), **kw)

    if grip in ("blade", "two_handed", "tool", "staff"):
        out = -0.02 if grip == "two_handed" else 0.1
        ready_item = {"blade": 62.0, "two_handed": 50.0, "tool": 28.0, "staff": 88.0}[grip]
        ready_at = {"blade": (0.45, 0.45), "two_handed": (0.42, 0.52), "tool": (0.32, 0.72), "staff": (0.3, 0.5)}[grip]
        ready = guard(lean=6, rh=h(*ready_at, out, item=ready_item))
        swings = {
            "item_swing": (guard(lean=-8, side=-4, rh=h(-0.3, -0.55, 0.25 if grip != "two_handed" else 0.05, item=150, pole=(0.6, -0.4, -0.5))),
                           guard(root=(0.04, -0.05, 0), lean=18, rh=h(0.9, 0.2, out, item=2, pole=(0.3, 0.8, -0.2)), face="angry"),
                           guard(root=(0.04, -0.05, 0), lean=20, rh=h(0.55, 0.75, out - 0.12, item=-55, pole=(0.3, 0.8, -0.2)))),
            "item_swing_up": (k.crouch(0.1, lean=10, rh=h(0.4, 0.75, out, item=-30), face="angry"),
                              k.pose(root=(0.01, 0.01, 0), lean=-8, head=(-20, 0), rh=h(0.3, -0.9, out, item=95, pole=(0.5, 0.2, -0.6)), face="angry"),
                              k.pose(lean=-12, head=(-22, 0), rh=h(-0.1, -0.88, out, item=125, pole=(0.5, 0.2, -0.6)))),
            "item_swing_down": (k.pose(lean=-8, rh=h(0.05, -0.92, out, item=115, pole=(0.5, 0.2, -0.6)), face="angry"),
                                k.crouch(0.14, lean=26, rh=h(0.9, 0.5, out, item=-25), face="angry"),
                                k.crouch(0.14, lean=28, rh=h(0.62, 0.82, out - 0.1, item=-70))),
            "item_swing_back": (guard(lean=10, rh=h(0.6, 0.25, out - 0.2, item=20)),
                                guard(lean=-16, side=-6, head=(8, 0), rh=h(-0.8, 0.25, 0.35, item=172), face="angry"),
                                guard(lean=-12, rh=h(-0.55, 0.55, 0.35, item=-150))),
        }
        crouch = k.crouch(0.2, rh=h(ready_at[0] + 0.1, ready_at[1] + 0.1, out, item=ready_item - 10))
    elif grip == "gun":
        ready = guard(lean=4, head=(2, 0), rh=h(0.95, 0.08, 0.02, item=0.0, pole=(0.5, 0.6, -0.3)))
        swings = {
            "item_swing": (guard(lean=-6, rh=h(0.6, 0.3, 0.05, item=30.0)), guard(lean=10, rh=h(0.97, 0.05, 0.02, item=-2.0), face="angry"),
                           guard(lean=4, rh=h(0.85, -0.1, 0.02, item=18.0))),
            "item_swing_up": (guard(lean=0, rh=h(0.8, 0.1, 0.02, item=10.0)), k.pose(lean=-10, head=(-24, 0), rh=h(0.5, -0.8, 0.05, item=62.0), face="angry"),
                              k.pose(lean=-10, head=(-24, 0), rh=h(0.48, -0.82, 0.05, item=66.0))),
            "item_swing_down": (guard(lean=6, rh=h(0.8, 0.1, 0.02, item=0.0)), guard(lean=16, head=(16, 0), rh=h(0.75, 0.65, 0.02, item=-42.0), face="angry"),
                                guard(lean=16, head=(16, 0), rh=h(0.72, 0.68, 0.02, item=-46.0))),
            "item_swing_back": (guard(lean=0, rh=h(0.8, 0.1, 0.02, item=0.0)), guard(lean=-10, side=-6, rh=h(-0.6, 0.2, 0.4, item=178.0), face="angry"),
                                guard(lean=-10, rh=h(-0.6, 0.25, 0.4, item=176.0))),
        }
        crouch = k.crouch(0.2, rh=h(0.95, 0.15, 0.02, item=0.0, pole=(0.5, 0.6, -0.3)))
    elif grip == "shield":
        ready = guard(lean=4, rh=h(0.42, 0.18, 0.02, item=88.0, pole=(0.6, 0.5, -0.3)))
        bash = guard(root=(0.04, -0.04, 0), lean=14, rh=h(0.8, 0.12, 0.0, item=86.0, pole=(0.6, 0.5, -0.3)), face="angry")
        swings = {name: (guard(lean=-4, rh=h(0.25, 0.25, 0.05, item=88.0)), bash, guard(lean=10, rh=h(0.6, 0.15, 0.0, item=88.0)))
                  for name in ("item_swing", "item_swing_up", "item_swing_down", "item_swing_back")}
        crouch = k.crouch(0.24, rh=h(0.45, 0.25, 0.02, item=88.0, pole=(0.6, 0.5, -0.3)))
    else:  # carried, thrown
        lift = grip == "carried"
        ready = guard(lean=2, rh=h(0.4, 0.5 if lift else 0.62, 0.05 if lift else 0.15, item=0.0 if lift else 35.0),
                      lh=k.hand(Lf, 0.38, 0.52, 0.05) if lift else None)
        swings = {name: (guard(lean=-6, rh=h(-0.2, 0.3, 0.2, item=120.0)), guard(lean=16, rh=h(0.9, 0.2, 0.05, item=10.0), face="angry"),
                         guard(lean=14, rh=h(0.5, 0.75, 0.0, item=-50.0)))
                  for name in ("item_swing", "item_swing_up", "item_swing_down", "item_swing_back")}
        crouch = k.crouch(0.2, rh=h(0.45, 0.6, 0.08, item=10.0))
    throw = {
        "throw_wind": guard(lean=-14, side=-4, rh=h(-0.45, -0.55, 0.3, item=140.0, pole=(0.5, 0.2, -0.6)), lh=k.hand(Lf, 0.6, 0.3, 0.2),
                            rf=k.foot(R, 0.2), lf=k.foot(Lf, -0.25)),
        "throw_release": guard(root=(0.04, -0.04, 0), lean=22, rh=h(0.95, 0.1, 0.05, item=10.0), lh=k.hand(Lf, -0.2, 0.6, 0.3),
                               rf=k.foot(R, 0.3), lf=k.foot(Lf, -0.25, toe=-15), face="angry", vis="a"),
        "throw_follow": guard(root=(0.04, -0.05, 0), lean=20, rh=h(0.55, 0.75, -0.1, item=-50.0), rf=k.foot(R, 0.28)),
    }
    return {"ready": ready, "crouch": crouch, "swings": swings, **throw}


def build_library(fig: Figure, grip: str = "blade") -> Dict[str, Clip]:
    """The clip union for ``fig``; the item clips (``item_*``) are posed for
    the grip class ``grip`` (one of :data:`GRIPS`)."""
    if grip not in GRIPS:
        raise KeyError(f"unknown grip {grip!r}; one of {GRIPS}")
    k = Kit(fig)
    R, Lf = "right", "left"
    out: Dict[str, Clip] = {}

    def add(c: Clip) -> None:
        out[c.name] = c

    stand = k.stand()
    guard = k.guard()

    # ---- stance and locomotion --------------------------------------------------------
    add(_seq("idle", 8, 120, True, _cycle([
        k.pose(root=(0, 0, 0), lean=0.0, head=(0, 0)),
        k.pose(root=(0, -0.004, 0), lean=1.0, head=(1.5, 0)),
        k.pose(root=(0, -0.006, 0), lean=1.4, head=(2.0, 1.0)),
        k.pose(root=(0, -0.003, 0), lean=0.6, head=(0.8, 0.5)),
    ]), view="front_3q", cat="idle"))
    add(_seq("idle_side", 8, 120, True, out["idle"].keys, view="side", cat="idle"))
    add(_seq("idle_back", 8, 120, True, out["idle"].keys, view="back_3q", cat="idle"))
    add(_seq("idle_look_up", 6, 90, False, _even([stand, k.pose(lean=-6, head=(-26, 0), face="surprised")]), view="front_3q", cat="idle"))

    def walk_pose(ph: float, stride: float = 0.26, bob: float = 0.012, lean: float = 3.0, arm: float = 0.28, face: str = "neutral") -> Pose:
        c, s = math.cos(ph), math.sin(ph)
        lift_r = max(0.0, -s) * 0.12
        lift_l = max(0.0, s) * 0.12
        return k.pose(root=(0.0, -bob * abs(c) + bob * 0.5, 0.0), lean=lean, head=(-lean * 0.5, 0.0),
                      rf=k.foot(R, stride * c * 0.5, lift_r, 0.0, toe=18 * max(0.0, -s) - 10 * max(0.0, c)),
                      lf=k.foot(Lf, -stride * c * 0.5, lift_l, 0.0, toe=18 * max(0.0, s) - 10 * max(0.0, -c)),
                      rh=k.hand(R, 0.12 - arm * c, 0.88, 0.16, pole=(0.25, 0.2, -1.0)),
                      lh=k.hand(Lf, 0.12 + arm * c, 0.88, 0.16, pole=(0.25, 0.2, -1.0)), face=face)

    add(_seq("walk", 8, 100, True, _cycle([walk_pose(2 * math.pi * i / 8) for i in range(8)]), cat="locomotion"))
    add(_seq("walk_away", 8, 100, True, out["walk"].keys, view="back_3q", cat="locomotion"))
    add(_seq("walk_toward", 8, 100, True, out["walk"].keys, view="front_3q", cat="locomotion"))
    add(_seq("walk_stop", 4, 70, False, _even([walk_pose(0.0), k.pose(root=(0.01, -0.01, 0), lean=-3), stand]), cat="locomotion"))

    def run_pose(ph: float) -> Pose:
        c, s = math.cos(ph), math.sin(ph)
        return k.pose(root=(0.0, -0.035 + 0.03 * abs(s), 0.0), lean=16.0, head=(-10.0, 0.0),
                      rf=k.bfoot(R, 0.42 * c, 0.86 - 0.32 * max(0.0, -s), 0.04, toe=20 * max(0.0, -s)),
                      lf=k.bfoot(Lf, -0.42 * c, 0.86 - 0.32 * max(0.0, s), 0.04, toe=20 * max(0.0, s)),
                      rh=k.hand(R, 0.3 - 0.45 * c, 0.6, 0.14, pole=(0.2, 0.4, -1.0)), lh=k.hand(Lf, 0.3 + 0.45 * c, 0.6, 0.14, pole=(0.2, 0.4, -1.0)),
                      face="determined")

    # A run's planted foot is under the body, so its feet ride the hips.
    add(_seq("run", 8, 75, True, _cycle([run_pose(2 * math.pi * i / 8) for i in range(8)]), cat="locomotion"))
    add(_seq("dash_startup", 4, 50, False, _even([stand, k.crouch(0.08, lean=24, rh=k.hand(R, -0.35, 0.6), lh=k.hand(Lf, 0.45, 0.55)),
                                                     run_pose(0.0)]), cat="locomotion"))
    add(_seq("dash", 6, 65, True, _cycle([run_pose(2 * math.pi * i / 6) for i in range(6)]), cat="locomotion"))
    skid = k.pose(root=(-0.02, -0.06, 0), lean=-14.0, head=(8, 0), rf=k.foot(R, 0.3, 0.0, 0.0, toe=-25), lf=k.foot(Lf, -0.12, 0.0),
                  rh=k.hand(R, 0.4, 0.4, 0.4), lh=k.hand(Lf, 0.0, 0.5, 0.45), face="surprised")
    add(_seq("skid", 4, 60, False, _even([run_pose(0.0), skid, skid]), cat="locomotion"))
    add(_seq("turnaround", 5, 60, False, _even([stand, stand]), cat="locomotion"))
    add(_seq("turn_away", 3, 80, False, _even([stand, stand]), view="back_3q", cat="locomotion"))
    add(_seq("stumble", 6, 70, False, _even([walk_pose(0.4), k.pose(root=(0.03, -0.05, 0), lean=28, head=(-20, 0), rf=k.foot(R, 0.25),
                                                                    lf=k.foot(Lf, -0.2, 0.1), rh=k.hand(R, 0.6, 0.3, 0.4), lh=k.hand(Lf, 0.5, 0.2, 0.45),
                                                                    face="afraid"), k.guard()]), cat="locomotion"))
    slide = k.pose(root=(0.0, -0.33, 0.0), spin=-28, lean=-10, rf=k.bfoot(R, 0.75, 0.55), lf=k.bfoot(Lf, 0.25, 0.75),
                   rh=k.hand(R, -0.3, 0.6, 0.3), lh=k.hand(Lf, -0.2, 0.75, 0.3), face="determined", ground=True)
    add(_seq("slide", 6, 70, False, _even([run_pose(0.0), slide, slide, k.crouch(0.15)]), cat="locomotion"))
    crouch = k.crouch()
    add(_seq("crouch_start", 3, 60, False, _even([stand, crouch]), cat="locomotion"))
    add(_seq("crouch", 5, 95, True, _cycle([crouch, k.crouch(0.225, lean=23)]), cat="locomotion"))
    add(_seq("crouch_end", 3, 60, False, _even([crouch, stand]), cat="locomotion"))

    def cwalk(ph: float) -> Pose:
        c, s = math.cos(ph), math.sin(ph)
        return k.crouch(0.24, rf=k.foot(R, 0.12 * c + 0.06, max(0.0, -s) * 0.05), lf=k.foot(Lf, -0.12 * c - 0.04, max(0.0, s) * 0.05),
                        rh=k.hand(R, 0.5 - 0.12 * c, 0.55), lh=k.hand(Lf, 0.4 + 0.12 * c, 0.6))

    add(_seq("crouch_walk", 8, 88, True, _cycle([cwalk(2 * math.pi * i / 8) for i in range(8)]), cat="locomotion"))

    def crawl(ph: float) -> Pose:
        c = math.cos(ph)
        return k.pose(root=(0.06, -0.33, 0.0), spin=72.0, lean=6.0, head=(-60, 0), ground=True,
                      rh=k.hand(R, 0.62 + 0.14 * c, 0.42, 0.2, pole=(0.3, 0.0, -1.0)), lh=k.hand(Lf, 0.62 - 0.14 * c, 0.42, 0.2, pole=(0.3, 0.0, -1.0)),
                      rf=k.bfoot(R, -0.25 - 0.1 * c, 0.55, 0.06, pole=(0.0, 1.0, 0.3)), lf=k.bfoot(Lf, -0.25 + 0.1 * c, 0.55, 0.06, pole=(0.0, 1.0, 0.3)))

    add(_seq("crawl_start", 4, 80, False, _even([crouch, crawl(0.0)]), cat="locomotion"))
    add(_seq("crawl", 8, 110, True, _cycle([crawl(2 * math.pi * i / 8) for i in range(8)]), cat="locomotion"))
    add(_seq("teeter_start", 3, 70, False, _even([stand, k.pose(lean=-14, side=6, rh=k.hand(R, 0.2, -0.2, 0.6, pole=(0.6, 0, -0.4)),
                                                            lh=k.hand(Lf, 0.0, -0.1, 0.65, pole=(0.6, 0, -0.4)), face="afraid")]), cat="footing"))

    def teeter(ph: float) -> Pose:
        s = math.sin(ph)
        return k.pose(lean=-10 + 10 * s, side=4 * s, head=(10 * s, 0), rf=k.foot(R, 0.0, 0.0, toe=-12), lf=k.foot(Lf, -0.1, 0.06 + 0.04 * s),
                      rh=k.hand(R, 0.2 + 0.2 * s, -0.25 + 0.15 * s, 0.6, pole=(0.6, 0, -0.4)),
                      lh=k.hand(Lf, 0.1 - 0.2 * s, -0.15 - 0.15 * s, 0.65, pole=(0.6, 0, -0.4)), face="afraid")

    add(_seq("teeter", 8, 90, True, _cycle([teeter(2 * math.pi * i / 8) for i in range(8)]), cat="footing"))
    add(_seq("platform_drop", 4, 60, False, _even([k.crouch(0.12), k.air(root=(0, -0.04, 0), face="surprised")]), cat="footing"))

    # ---- air ---------------------------------------------------------------------------
    squat = k.crouch(0.14, lean=14, rh=k.hand(R, -0.25, 0.75, 0.2), lh=k.hand(Lf, -0.3, 0.75, 0.22), face="determined")
    rise = k.pose(lean=-2, head=(-10, 0), rh=k.hand(R, 0.35, -0.6, 0.2, pole=(0.4, 0.2, -0.8)), lh=k.hand(Lf, 0.25, -0.5, 0.25, pole=(0.4, 0.2, -0.8)),
                  rf=k.bfoot(R, 0.05, 0.98, toe=25), lf=k.bfoot(Lf, -0.1, 0.96, toe=30))
    apex = k.air()
    falling = k.air(lean=-4, head=(6, 0), rh=k.hand(R, 0.25, -0.2, 0.55, pole=(0.7, 0.3, -0.3)), lh=k.hand(Lf, 0.0, -0.1, 0.6, pole=(0.7, 0.3, -0.3)),
                    rf=k.bfoot(R, 0.15, 0.88), lf=k.bfoot(Lf, -0.12, 0.93), face="surprised")
    add(_seq("jump_squat", 3, 50, False, _even([stand, squat]), cat="air"))
    swing = k.crouch(0.06, lean=8, rh=k.hand(R, 0.7, 0.45, 0.2, pole=(0.4, 0.4, -0.7)), lh=k.hand(Lf, 0.65, 0.5, 0.22, pole=(0.4, 0.4, -0.7)),
                     face="determined")
    add(_seq("jump", 6, 95, False, [(0.0, squat), (0.2, swing), (0.4, rise), (0.7, rise), (1.0, apex)], cat="air"))
    add(_seq("double_jump", 6, 70, False, _even([apex, k.air(spin=180.0, rf=k.bfoot(R, 0.3, 0.45), lf=k.bfoot(Lf, 0.25, 0.5),
                                                              rh=k.hand(R, 0.4, 0.5, 0.2), lh=k.hand(Lf, 0.4, 0.5, 0.25)),
                                                    k.air(spin=355.0), apex]), cat="air"))
    add(_seq("fall", 6, 95, True, _cycle([falling, k.air(lean=-2, head=(4, 0), rh=k.hand(R, 0.3, -0.1, 0.55, pole=(0.7, 0.3, -0.3)),
                                                          lh=k.hand(Lf, 0.05, -0.2, 0.6, pole=(0.7, 0.3, -0.3)), rf=k.bfoot(R, 0.12, 0.9),
                                                          lf=k.bfoot(Lf, -0.1, 0.92), face="surprised")]), cat="air"))
    add(_seq("fall_special", 6, 95, True, _cycle([k.air(lean=10, head=(14, 0), face="pained", rh=k.hand(R, 0.1, 0.7, 0.3),
                                                        lh=k.hand(Lf, 0.0, 0.75, 0.35)), k.air(lean=12, head=(16, 0), face="pained")]), cat="air"))
    land = k.crouch(0.16, lean=18, face="determined")
    add(_seq("land", 6, 72, False, _even([falling, land, k.crouch(0.08), stand]), cat="air"))
    add(_seq("land_light", 4, 60, False, _even([land, stand]), cat="air"))
    add(_seq("land_hard", 8, 95, False, _even([falling, k.crouch(0.3, lean=34, head=(-28, 0), face="pained"), k.crouch(0.28, lean=30),
                                              k.crouch(0.15), stand]), cat="air"))
    add(_seq("land_recovery", 6, 75, False, _even([k.crouch(0.2), k.crouch(0.08), stand]), cat="air"))
    add(_seq("air_land", 4, 60, False, _even([land, k.crouch(0.06), stand]), cat="air"))
    tumble_keys = [(i / 8, k.air(spin=45.0 * i, rf=k.bfoot(R, 0.35, 0.55), lf=k.bfoot(Lf, -0.1, 0.7), rh=k.hand(R, 0.3, -0.4, 0.5),
                                 lh=k.hand(Lf, -0.3, 0.3, 0.55), face="pained")) for i in range(8)]
    add(_seq("tumble", 8, 70, True, tumble_keys + [(1.0, replace(tumble_keys[0][1], spin=360.0))], cat="reaction"))
    add(_seq("float_glide", 8, 110, True, _cycle([k.air(lean=18, rh=k.hand(R, 0.2, 0.0, 0.75, pole=(0.7, 0.2, -0.2)),
                                                        lh=k.hand(Lf, 0.0, 0.0, 0.8, pole=(0.7, 0.2, -0.2))),
                                                  k.air(lean=16, rh=k.hand(R, 0.2, 0.08, 0.75, pole=(0.7, 0.2, -0.2)),
                                                        lh=k.hand(Lf, 0.0, 0.1, 0.8, pole=(0.7, 0.2, -0.2)))]), cat="air"))
    add(_seq("hover", 8, 78, True, out["float_glide"].keys, cat="air"))
    add(_seq("footstool_jump", 4, 70, False, _even([apex, rise]), cat="air"))

    # ---- walls, ledges and climbing ----------------------------------------------------------
    cling = k.pose(root=(0.05, 0.0, 0.0), lean=-6, head=(-8, 0), rh=k.hand(R, 0.45, -0.25, 0.25, pole=(0.5, 0.3, -0.6)),
                   lh=k.hand(Lf, 0.4, 0.15, 0.3, pole=(0.5, 0.3, -0.6)), rf=k.bfoot(R, 0.3, 0.75), lf=k.bfoot(Lf, 0.25, 0.92), face="determined")
    add(_seq("wall_grab", 6, 110, True, _cycle([cling, replace(cling, lean=-5)]), cat="wall"))
    add(_seq("wall_land", 4, 55, False, _even([apex, cling]), cat="wall"))
    add(_seq("wall_slide", 6, 95, True, _cycle([k.pose(root=(0.05, 0, 0), lean=-4, rh=k.hand(R, 0.45, -0.55, 0.25, pole=(0.5, 0.3, -0.6)),
                                                      lh=k.hand(Lf, 0.35, 0.35, 0.3), rf=k.bfoot(R, 0.32, 0.72), lf=k.bfoot(Lf, 0.1, 0.95),
                                                      face="pained"),
                                               k.pose(root=(0.05, 0, 0), lean=-4, rh=k.hand(R, 0.45, -0.5, 0.25, pole=(0.5, 0.3, -0.6)),
                                                      lh=k.hand(Lf, 0.35, 0.3, 0.3), rf=k.bfoot(R, 0.32, 0.7), lf=k.bfoot(Lf, 0.1, 0.95), face="pained")]),
              cat="wall"))

    def wclimb(ph: float) -> Pose:
        c = math.cos(ph)
        return k.pose(root=(0.05, 0.0, 0.0), lean=-6, rh=k.hand(R, 0.45, -0.35 - 0.3 * c, 0.2, pole=(0.5, 0.3, -0.6)),
                      lh=k.hand(Lf, 0.42, -0.35 + 0.3 * c, 0.24, pole=(0.5, 0.3, -0.6)),
                      rf=k.bfoot(R, 0.3, 0.85 + 0.12 * c), lf=k.bfoot(Lf, 0.3, 0.85 - 0.12 * c), face="determined")

    add(_seq("wall_climb", 8, 100, True, _cycle([wclimb(2 * math.pi * i / 8) for i in range(8)]), cat="wall"))
    add(_seq("wall_jump", 8, 70, False, [(0.0, cling), (0.25, k.crouch(0.1, lean=-10)), (0.45, swing), (0.7, rise), (1.0, apex)], cat="wall"))
    hang = k.hang()
    add(_seq("ledge_catch", 4, 60, False, _even([falling, hang]), cat="ledge"))
    add(_seq("ledge_grab", 6, 100, True, _cycle([hang, k.hang(lean=-6, rf=k.bfoot(R, 0.16, 0.94), lf=k.bfoot(Lf, -0.02, 0.97))]), cat="ledge"))
    add(_seq("ledge_hang", 6, 100, True, out["ledge_grab"].keys, cat="ledge"))
    pull = k.pose(root=(0.03, 0.12, 0.0), lean=24, head=(-14, 0), rh=k.hand(R, 0.35, 0.2, 0.18), lh=k.hand(Lf, 0.3, 0.25, 0.2),
                  rf=k.bfoot(R, 0.4, 0.6), lf=k.bfoot(Lf, 0.1, 0.8), face="determined")
    kneel = k.crouch(0.24, root=(0.02, -0.24, 0.0), rf=k.foot(R, 0.15), lf=k.foot(Lf, -0.1, 0.0, toe=-20))
    add(_seq("ledge_climb", 6, 100, False, _even([hang, pull, kneel, stand]), cat="ledge"))
    add(_seq("ledge_getup", 6, 40, False, _even([hang, pull, kneel, stand]), cat="ledge"))
    add(_seq("ledge_roll", 8, 37, False, _even([hang, pull, k.crouch(0.3, spin=120), k.crouch(0.3, spin=300), k.crouch(0.15, spin=360), stand]),
              cat="ledge"))
    add(_seq("ledge_jump", 6, 70, False, _even([hang, pull, rise, apex]), cat="ledge"))
    add(_seq("ledge_drop", 4, 70, False, _even([hang, falling]), cat="ledge"))
    sweep = k.crouch(0.28, lean=10, rf=k.bfoot(R, 0.85, 0.3), rh=k.hand(R, 0.3, 0.8, 0.3), lh=k.hand(Lf, -0.2, 0.8, 0.3), face="angry")
    add(_seq("ledge_attack", 8, 37, False, _even([hang, pull, kneel, sweep, kneel, stand]), cat="ledge"))
    add(_seq("ledge_getup_attack", 8, 37, False, out["ledge_attack"].keys, cat="ledge"))

    def ladder(ph: float) -> Pose:
        c = math.cos(ph)
        return k.pose(root=(0.03, 0.0, 0.0), lean=-2, head=(-10, 0),
                      rh=k.hand(R, 0.25, -0.5 - 0.35 * c, 0.2, pole=(0.7, 0.2, -0.4)), lh=k.hand(Lf, 0.25, -0.5 + 0.35 * c, 0.2, pole=(0.7, 0.2, -0.4)),
                      rf=k.bfoot(R, 0.2, 0.8 + 0.15 * c, 0.08), lf=k.bfoot(Lf, 0.2, 0.8 - 0.15 * c, 0.08))

    add(_seq("climb", 8, 100, True, _cycle([ladder(2 * math.pi * i / 8) for i in range(8)]), view="back", cat="climb"))
    add(_seq("ladder_climb", 8, 100, True, out["climb"].keys, view="back", cat="climb"))

    def swim(ph: float) -> Pose:
        c, s = math.cos(ph), math.sin(ph)
        return k.pose(root=(0.0, -0.25, 0.0), spin=70, head=(-55, 0),
                      rh=k.hand(R, 0.6 + 0.3 * c, 0.1 + 0.5 * s, 0.25, pole=(1.0, -0.3, -0.2)), lh=k.hand(Lf, 0.6 - 0.3 * c, 0.1 - 0.5 * s, 0.3, pole=(1.0, -0.3, -0.2)),
                      rf=k.bfoot(R, -0.05 + 0.1 * s, 0.9), lf=k.bfoot(Lf, -0.05 - 0.1 * s, 0.9))

    add(_seq("swim", 12, 80, True, _cycle([swim(2 * math.pi * i / 8) for i in range(8)]), cat="swim"))

    # ---- defence ------------------------------------------------------------------------------
    shield = k.guard(root=(0, -0.05, 0), lean=4, rh=k.hand(R, 0.38, 0.12, 0.05, pole=(0.6, 0.5, -0.3)),
                     lh=k.hand(Lf, 0.4, 0.18, 0.02, pole=(0.6, 0.5, -0.3)), face="determined")
    add(_seq("shield_raise", 3, 60, False, _even([stand, shield]), cat="defense"))
    add(_seq("block", 6, 85, True, _cycle([shield, k.guard(root=(0, -0.055, 0), lean=5, rh=shield.hands["right"], lh=shield.hands["left"],
                                                           face="determined")]), cat="defense"))
    add(_seq("shield_hold", 6, 85, True, out["block"].keys, cat="defense"))
    add(_seq("shield_release", 3, 60, False, _even([shield, stand]), cat="defense"))
    add(_seq("shield_hit", 4, 60, False, _even([replace(shield, root=(0, 0, -0.03 * k.H)), shield]), cat="defense"))
    parry = k.guard(lean=-4, rh=k.hand(R, 0.55, 0.0, 0.3, pole=(0.6, 0.5, -0.3)), lh=k.hand(Lf, 0.2, 0.4, 0.2), face="smug")
    add(_seq("parry", 6, 60, False, _even([stand, parry, parry, stand]), cat="defense"))
    dodge = k.crouch(0.08, lean=-14, side=10, head=(-6, 0), rh=k.hand(R, 0.1, 0.4, 0.4), lh=k.hand(Lf, -0.1, 0.4, 0.45), face="surprised")
    add(_seq("spot_dodge", 6, 55, False, _even([stand, dodge, dodge, stand]), cat="defense"))
    ball = k.crouch(0.32, lean=40, head=(-30, 0), rh=k.hand(R, 0.35, 0.45, 0.1), lh=k.hand(Lf, 0.3, 0.45, 0.12),
                    rf=k.bfoot(R, 0.55, 0.4), lf=k.bfoot(Lf, 0.5, 0.45))

    def roll(dirn: float) -> List[Tuple[float, Pose]]:
        return [(0.0, stand), (0.15, k.crouch(0.18)), *[(0.2 + 0.6 * i / 6, replace(ball, spin=dirn * 360.0 * i / 6,
                                                                                   root=(0.0, 0.0, dirn * 0.04 * k.H * i)))
                                                         for i in range(7)], (1.0, k.crouch(0.1))]

    add(_seq("roll", 8, 58, False, roll(1.0), cat="defense"))
    add(_seq("roll_forward", 8, 58, False, roll(1.0), cat="defense"))
    add(_seq("roll_back", 8, 58, False, roll(-1.0), cat="defense"))
    add(_seq("roll_backward", 8, 58, False, roll(-1.0), cat="defense"))
    add(_seq("air_dodge", 6, 60, False, _even([apex, k.air(spin=-20, rh=k.hand(R, 0.3, 0.3, 0.1), lh=k.hand(Lf, 0.25, 0.35, 0.12),
                                                          rf=k.bfoot(R, 0.45, 0.5), lf=k.bfoot(Lf, 0.4, 0.55), face="determined"), apex]), cat="defense"))

    # ---- strikes ------------------------------------------------------------------------------
    def strike(name: str, wind: Pose, hit: Pose, follow: Pose, frames: int = 8, ms: int = 60, cat: str = "attack", start: Pose = guard,
               end: Optional[Pose] = None) -> None:
        add(_seq(name, frames, ms, False, [(0.0, start), (0.28, wind), (0.45, hit), (0.62, follow), (1.0, end or start)], cat=cat))

    jab_hit = k.guard(root=(0.02, -0.04, 0), lean=12, rh=k.hand(R, 0.98, 0.0, 0.0, pole=(0.3, 0.8, -0.2), wrist=0), face="angry")
    strike("jab", k.guard(lean=4, rh=k.hand(R, 0.2, 0.35, 0.05, pole=(0.4, 0.7, -0.4))), jab_hit,
           k.guard(root=(0.02, -0.04, 0), lean=10, rh=k.hand(R, 0.85, 0.05, 0.0, pole=(0.3, 0.8, -0.2))), frames=6, ms=40)
    strike("jab_2", k.guard(lean=0, side=-4, lh=k.hand(Lf, 0.15, 0.4, 0.05)),
           k.guard(root=(0.03, -0.04, 0), lean=14, side=6, lh=k.hand(Lf, 0.98, 0.02, -0.1, pole=(0.3, 0.8, -0.2)), face="angry"),
           k.guard(root=(0.03, -0.04, 0), lean=12, lh=k.hand(Lf, 0.8, 0.1, -0.05)), frames=6, ms=40)
    kick_hit = k.guard(root=(0.0, -0.01, 0), lean=-14, rf=k.bfoot(R, 0.9, 0.3, 0.02, toe=-20), lf=k.foot(Lf, -0.1),
                       rh=k.hand(R, -0.1, 0.5, 0.3), lh=k.hand(Lf, 0.3, 0.4, 0.3), face="angry")
    strike("jab_3", k.guard(lean=4, rf=k.bfoot(R, 0.35, 0.55)), kick_hit, k.guard(lean=-6, rf=k.bfoot(R, 0.6, 0.55)), frames=8, ms=45)
    strike("punch", k.guard(lean=0, rh=k.hand(R, -0.1, 0.4, 0.15)), jab_hit, k.guard(lean=10, rh=k.hand(R, 0.8, 0.1, 0.0)), frames=6, ms=45)
    side_wind = k.guard(lean=-8, side=-4, head=(-2, 0), rh=k.hand(R, -0.45, 0.25, 0.3, pole=(0.9, -0.1, -0.3), wrist=-40),
                        rf=k.foot(R, 0.05), lf=k.foot(Lf, -0.2), face="angry")
    side_hit = k.guard(root=(0.04, -0.05, 0), lean=18, rh=k.hand(R, 0.9, 0.15, 0.1, pole=(0.3, 0.8, -0.2), wrist=3), rf=k.foot(R, 0.28),
                       lf=k.foot(Lf, -0.15, toe=-10), face="angry")
    side_follow = k.guard(root=(0.04, -0.05, 0), lean=20, rh=k.hand(R, 0.55, 0.55, -0.15, pole=(0.3, 0.8, -0.2), wrist=23), rf=k.foot(R, 0.28),
                          lf=k.foot(Lf, -0.15, toe=-10))
    strike("attack_side", side_wind, side_hit, side_follow)
    strike("attack", side_wind, side_hit, side_follow)
    strike("slash", side_wind, side_hit, side_follow, ms=75)
    up_wind = k.crouch(0.1, lean=10, rh=k.hand(R, 0.3, 0.8, 0.15, wrist=13), face="angry")
    up_hit = k.pose(root=(0.01, 0.01, 0), lean=-8, head=(-20, 0), rh=k.hand(R, 0.25, -0.95, 0.05, pole=(0.5, 0.2, -0.6), wrist=-32),
                    lh=k.hand(Lf, 0.1, 0.6, 0.3), rf=k.foot(R, 0.06, toe=20), lf=k.foot(Lf, -0.06), face="angry")
    up_follow = k.pose(lean=-14, head=(-24, 0), rh=k.hand(R, -0.25, -0.85, 0.05, pole=(0.5, 0.2, -0.6), wrist=-40), lh=k.hand(Lf, 0.1, 0.6, 0.3))
    strike("attack_up", up_wind, up_hit, up_follow)
    down_wind = k.crouch(0.24, lean=20, rh=k.hand(R, -0.3, 0.3, 0.3, wrist=-20), face="angry")
    down_hit = k.crouch(0.3, lean=28, head=(-6, 0), rh=k.hand(R, 0.85, 0.75, 0.1, pole=(0.3, 0.8, -0.2), wrist=10), lh=k.hand(Lf, 0.0, 0.7, 0.4),
                        rf=k.foot(R, 0.3), lf=k.foot(Lf, -0.2, toe=-15), face="angry")
    strike("attack_down", down_wind, down_hit, k.crouch(0.28, lean=26, rh=k.hand(R, 0.6, 0.8, -0.1, wrist=16)), start=k.crouch(0.18))
    add(_seq("smash_charge", 8, 70, True, _cycle([
        k.guard(root=(-0.02, -0.07, 0), lean=-12, side=-6, rh=k.hand(R, -0.6, 0.15, 0.35, wrist=-40), lh=k.hand(Lf, 0.45, 0.35, 0.2),
                rf=k.foot(R, 0.2), lf=k.foot(Lf, -0.25), face="angry", vis="e"),
        k.guard(root=(-0.02, -0.08, 0), lean=-13, side=-6, rh=k.hand(R, -0.62, 0.12, 0.36, wrist=-40), lh=k.hand(Lf, 0.45, 0.33, 0.2),
                rf=k.foot(R, 0.2), lf=k.foot(Lf, -0.25), face="angry", vis="e")]), cat="smash"))
    smash_wind = out["smash_charge"].keys[0][1]
    smash_hit = k.guard(root=(0.08, -0.08, 0), lean=26, side=6, head=(-8, 0), rh=k.hand(R, 0.98, 0.1, 0.0, pole=(0.3, 0.8, -0.2), wrist=1),
                        lh=k.hand(Lf, -0.3, 0.5, 0.3), rf=k.foot(R, 0.42, toe=-5), lf=k.foot(Lf, -0.25, toe=-20), face="angry", vis="a")
    smash_follow = replace(smash_hit, lean=30, hands={**smash_hit.hands, "right": k.hand(R, 0.6, 0.65, -0.2, wrist=26)})
    add(_seq("smash_forward", 10, 70, False, [(0.0, guard), (0.3, smash_wind), (0.45, smash_hit), (0.6, smash_follow), (0.8, smash_follow),
                                              (1.0, guard)], cat="smash"))
    sup_wind = k.crouch(0.26, lean=24, rh=k.hand(R, 0.4, 0.85, 0.2), lh=k.hand(Lf, 0.35, 0.85, 0.25), face="angry")
    sup_hit = k.pose(root=(0, 0.04, 0), lean=-6, head=(-26, 0), rh=k.hand(R, 0.15, -0.98, 0.15, pole=(0.6, 0.2, -0.6), wrist=-30),
                     lh=k.hand(Lf, 0.1, -0.95, 0.2, pole=(0.6, 0.2, -0.6)), rf=k.foot(R, 0.0, 0.05, toe=30), lf=k.foot(Lf, -0.05, 0.08, toe=30), face="angry",
                     vis="a")
    add(_seq("smash_up", 10, 67, False, [(0.0, guard), (0.3, sup_wind), (0.5, sup_hit), (0.7, sup_hit), (1.0, guard)], cat="smash"))
    sdn_wind = k.pose(root=(0, -0.02, 0), lean=-10, head=(-18, 0), rh=k.hand(R, 0.0, -0.95, 0.3, pole=(0.6, 0.2, -0.6)),
                      lh=k.hand(Lf, -0.05, -0.92, 0.32, pole=(0.6, 0.2, -0.6)), face="angry")
    sdn_hit = k.crouch(0.3, lean=40, head=(-10, 0), rh=k.hand(R, 0.75, 0.9, 0.35, wrist=20), lh=k.hand(Lf, 0.7, 0.9, 0.4),
                       rf=k.foot(R, 0.28), lf=k.foot(Lf, -0.28), face="angry", vis="a")
    add(_seq("smash_down", 10, 68, False, [(0.0, guard), (0.3, sdn_wind), (0.5, sdn_hit), (0.7, sdn_hit), (1.0, guard)], cat="smash"))
    for d in ("forward", "up", "down"):
        add(_seq(f"smash_charge_{d}", 8, 70, True, out["smash_charge"].keys, cat="smash"))
    dash_hit = k.guard(root=(0.1, -0.12, 0), lean=30, head=(-14, 0), rh=k.hand(R, 0.9, 0.3, 0.1, wrist=0), lh=k.hand(Lf, 0.8, 0.35, 0.15),
                       rf=k.foot(R, 0.45), lf=k.foot(Lf, -0.4, 0.15, toe=-20), face="angry", vis="a")
    add(_seq("dash_attack", 10, 42, False, _even([run_pose(0.0), dash_hit, dash_hit, k.crouch(0.12), guard]), cat="attack"))
    add(_seq("stomp", 6, 70, False, _even([k.pose(rf=k.bfoot(R, 0.3, 0.55), lean=-6, face="angry"),
                                           k.crouch(0.08, rf=k.foot(R, 0.3), face="angry"), guard]), cat="attack"))

    # ---- aerials ------------------------------------------------------------------------------
    nair_keys = [(0.0, apex), (0.2, k.air(spin=40, rf=k.bfoot(R, 0.45, 0.6), lf=k.bfoot(Lf, -0.45, 0.6), rh=k.hand(R, 0.6, 0.1, 0.4),
                                          lh=k.hand(Lf, -0.5, 0.1, 0.4), face="angry")),
                 (0.45, k.air(spin=200, rf=k.bfoot(R, 0.6, 0.5), lf=k.bfoot(Lf, -0.6, 0.5), rh=k.hand(R, 0.6, 0.0, 0.5), lh=k.hand(Lf, -0.6, 0.0, 0.5),
                              face="angry")), (0.75, k.air(spin=355)), (1.0, apex)]
    add(_seq("air_neutral", 8, 60, False, nair_keys, cat="aerial"))
    add(_seq("air_forward", 10, 44, False, [(0.0, apex), (0.15, k.air(lean=-6, rh=k.hand(R, 0.45, -0.55, 0.15, wrist=-20), face="angry")), (0.3, k.air(lean=-16, rh=k.hand(R, -0.3, -0.85, 0.15, pole=(0.5, 0.2, -0.6), wrist=-40),
                                                                    face="angry")),
                                            (0.5, k.air(lean=26, rh=k.hand(R, 0.95, 0.3, 0.05, wrist=8), face="angry")),
                                            (0.7, k.air(lean=24, rh=k.hand(R, 0.5, 0.75, -0.1, wrist=26))), (1.0, apex)], cat="aerial"))
    add(_seq("air_back", 7, 62, False, [(0.0, apex), (0.3, k.air(lean=20, rf=k.bfoot(R, 0.35, 0.4), face="angry")),
                                         (0.5, k.air(lean=34, head=(16, 0), rf=k.bfoot(R, -0.85, 0.35, toe=10), lf=k.bfoot(Lf, 0.2, 0.7), face="angry")),
                                         (0.7, k.air(lean=28, rf=k.bfoot(R, -0.6, 0.55))), (1.0, apex)], cat="aerial"))
    add(_seq("air_up", 7, 62, False, [(0.0, apex), (0.3, k.air(lean=20, face="angry")),
                                       (0.55, k.air(spin=-150, rf=k.bfoot(R, 0.7, -0.1), lf=k.bfoot(Lf, 0.0, 0.6), face="angry")),
                                       (0.8, k.air(spin=-330)), (1.0, apex)], cat="aerial"))
    add(_seq("air_down", 7, 70, False, [(0.0, apex), (0.3, k.air(lean=-12, rf=k.bfoot(R, 0.4, 0.4), lf=k.bfoot(Lf, 0.35, 0.45), face="angry")),
                                         (0.55, k.air(lean=6, rf=k.bfoot(R, 0.05, 1.0, toe=-35), lf=k.bfoot(Lf, -0.02, 1.0, toe=-35),
                                                      rh=k.hand(R, 0.2, -0.5, 0.45), lh=k.hand(Lf, 0.1, -0.5, 0.5), face="angry", vis="o")),
                                         (1.0, apex)], cat="aerial"))

    # ---- specials and ranged -----------------------------------------------------------
    gather = k.crouch(0.1, lean=-6, rh=k.hand(R, -0.05, 0.5, 0.05, pole=(0.4, 0.4, -0.6)), lh=k.hand(Lf, -0.05, 0.52, 0.0, pole=(0.4, 0.4, -0.6)),
                      face="determined")
    blast = k.guard(root=(0.03, -0.06, 0), lean=14, rh=k.hand(R, 0.98, 0.1, 0.02, pole=(0.3, 0.8, -0.2), wrist=0),
                    lh=k.hand(Lf, 0.95, 0.15, -0.05, pole=(0.3, 0.8, -0.2)), rf=k.foot(R, 0.25), lf=k.foot(Lf, -0.2), face="angry", vis="a")
    add(_seq("special", 8, 72, False, [(0.0, guard), (0.35, gather), (0.55, blast), (0.75, blast), (1.0, guard)], cat="special"))
    add(_seq("special_neutral", 8, 72, False, out["special"].keys, cat="special"))
    add(_seq("special_side", 10, 66, False, [(0.0, guard), (0.25, side_wind), (0.45, replace(dash_hit, root=(0.1 * k.H * 0, -0.12 * k.H * 0, 0.12 * k.H))),
                                              (0.7, dash_hit), (1.0, guard)], cat="special"))
    add(_seq("special_up", 12, 100, False, [(0.0, guard), (0.2, sup_wind), (0.4, replace(sup_hit, spin=0.0)),
                                            (0.6, k.air(spin=360, rh=k.hand(R, 0.1, -0.95, 0.2, wrist=-30))), (0.8, falling), (1.0, falling)], cat="special"))
    add(_seq("special_down", 10, 48, False, [(0.0, guard), (0.3, sdn_wind), (0.5, sdn_hit), (0.8, sdn_hit), (1.0, guard)], cat="special"))
    add(_seq("final_smash", 12, 90, False, [(0.0, guard), (0.25, k.pose(root=(0, 0.03, 0), lean=-10, head=(-24, 0),
                                                                        rh=k.hand(R, 0.1, -0.95, 0.45, pole=(0.6, 0.2, -0.6)),
                                                                        lh=k.hand(Lf, 0.1, -0.95, 0.5, pole=(0.6, 0.2, -0.6)), face="surprised", vis="o")),
                                            (0.5, blast), (0.75, replace(blast, lean=20)), (1.0, guard)], cat="special"))
    aim_pose = k.guard(lean=4, rh=k.hand(R, 0.97, 0.05, 0.02, pole=(0.3, 0.8, -0.2), wrist=0), lh=k.hand(Lf, 0.72, 0.12, -0.04), face="determined")
    add(_seq("aim", 6, 100, True, _cycle([aim_pose, replace(aim_pose, lean=4.5)]), cat="ranged"))
    recoil = replace(aim_pose, lean=-2, hands={**aim_pose.hands, "right": k.hand(R, 0.85, -0.05, 0.02, pole=(0.3, 0.8, -0.2), wrist=-5)})
    add(_seq("shoot", 6, 58, False, _even([aim_pose, aim_pose, recoil, aim_pose]), cat="ranged"))
    add(_seq("charge", 8, 76, True, _cycle([gather, replace(gather, lean=-7)]), cat="ranged"))
    add(_seq("cast", 8, 80, False, [(0.0, stand), (0.35, k.pose(lean=-6, rh=k.hand(R, 0.3, -0.6, 0.3, pole=(0.6, 0.2, -0.6)),
                                                                lh=k.hand(Lf, 0.2, -0.55, 0.35, pole=(0.6, 0.2, -0.6)), face="determined", vis="o")),
                                    (0.6, blast), (1.0, stand)], cat="ranged"))

    # ---- grabs and throws ----------------------------------------------------------------------
    reach = k.guard(root=(0.03, -0.05, 0), lean=18, rh=k.hand(R, 0.97, 0.25, 0.08), lh=k.hand(Lf, 0.95, 0.3, -0.05), face="determined")
    hold = k.guard(root=(0.02, -0.04, 0), lean=8, rh=k.hand(R, 0.72, 0.25, 0.08), lh=k.hand(Lf, 0.7, 0.3, -0.02), face="smug")
    add(_seq("grab", 6, 70, False, _even([guard, reach, hold]), cat="grab"))
    add(_seq("grab_hold", 6, 100, True, _cycle([hold, replace(hold, lean=9)]), cat="grab"))
    add(_seq("pummel", 4, 55, False, _even([hold, replace(hold, feet={"right": k.bfoot(R, 0.55, 0.5)}, face=face_channels("angry")), hold]), cat="grab"))
    add(_seq("grab_release", 4, 70, False, _even([hold, guard]), cat="grab"))
    toss_up = k.pose(lean=-12, head=(-20, 0), rh=k.hand(R, 0.3, -0.9, 0.15, pole=(0.6, 0.2, -0.6)), lh=k.hand(Lf, 0.25, -0.88, 0.2, pole=(0.6, 0.2, -0.6)),
                     face="angry", vis="a")
    add(_seq("throw_forward", 8, 60, False, _even([hold, replace(hold, lean=-6), k.guard(lean=22, rh=k.hand(R, 0.95, 0.2, 0.1),
                                                                                      lh=k.hand(Lf, 0.9, 0.25, -0.05), face="angry", vis="a"), guard]),
              cat="grab"))
    add(_seq("throw_back", 8, 60, False, _even([hold, k.pose(lean=-24, side=-8, head=(10, 0), rh=k.hand(R, -0.6, 0.0, 0.4), lh=k.hand(Lf, -0.55, 0.05, 0.45),
                                                             face="angry", vis="a"), guard]), cat="grab"))
    add(_seq("throw_up", 8, 60, False, _even([hold, k.crouch(0.12), toss_up, guard]), cat="grab"))
    add(_seq("throw_down", 8, 60, False, _even([hold, toss_up, k.crouch(0.25, lean=36, rh=k.hand(R, 0.8, 0.85), lh=k.hand(Lf, 0.75, 0.85), face="angry"),
                                                guard]), cat="grab"))
    add(_seq("throw", 7, 72, False, out["throw_forward"].keys, cat="grab"))
    grabbed = k.pose(root=(0, 0.04, 0), lean=-6, head=(10, 0), rh=k.hand(R, 0.4, -0.3, 0.3), lh=k.hand(Lf, 0.3, -0.25, 0.35),
                     rf=k.bfoot(R, 0.1, 0.95), lf=k.bfoot(Lf, -0.05, 0.97), face="afraid")
    add(_seq("grabbed", 6, 90, True, _cycle([grabbed, replace(grabbed, lean=-9)]), cat="grab"))
    add(_seq("grabbed_pummel", 4, 55, False, _even([grabbed, replace(grabbed, face=face_channels("pained")), grabbed]), cat="grab"))
    add(_seq("grab_escape", 6, 60, False, _even([grabbed, k.crouch(0.1, lean=-10), guard]), cat="grab"))

    # ---- reactions -------------------------------------------------------------------------
    hit = k.pose(root=(-0.02, -0.02, 0), lean=-18, head=(14, -4), rh=k.hand(R, 0.35, 0.35, 0.45, pole=(0.6, 0.3, -0.4)),
                 lh=k.hand(Lf, 0.0, 0.4, 0.5, pole=(0.6, 0.3, -0.4)), rf=k.foot(R, 0.05), lf=k.foot(Lf, -0.15, 0.03), face="pained")
    add(_seq("hit", 5, 90, False, _even([stand, hit, replace(hit, lean=-12), stand]), cat="reaction"))
    add(_seq("hurt", 5, 90, False, out["hit"].keys, cat="reaction"))
    launch = k.air(lean=-26, head=(22, 0), rh=k.hand(R, 0.2, -0.7, 0.55), lh=k.hand(Lf, -0.2, -0.6, 0.6), rf=k.bfoot(R, 0.3, 0.7),
                   lf=k.bfoot(Lf, -0.25, 0.8), face="pained")
    add(_seq("launch", 6, 70, False, _even([hit, launch, launch]), cat="reaction"))
    add(_seq("meteor", 6, 70, False, _even([hit, k.air(spin=40, face="pained"), k.air(spin=60, face="pained")]), cat="reaction"))
    down_back = k.lying(face_up=True, face="pained")
    add(_seq("knockdown", 8, 80, False, _even([hit, k.pose(root=(-0.05, -0.15, 0), spin=-40, face="pained"), down_back, down_back]), cat="reaction"))
    add(_seq("prone", 6, 120, True, _cycle([k.lying(face_up=True), k.lying(face_up=True, head=(-4, 0))]), cat="reaction"))
    add(_seq("prone_damage", 4, 70, False, _even([down_back, replace(down_back, root=(0.0, -0.03 * k.H, 0.0)), down_back]), cat="reaction"))
    sit_up = k.sitting(root=(-0.06, -0.36, 0.0), lean=-10, rf=k.foot(R, 0.4), lf=k.foot(Lf, 0.3), rh=k.hand(R, -0.1, 0.65, 0.3),
                       lh=k.hand(Lf, -0.15, 0.65, 0.35), ground=True)
    add(_seq("getup", 8, 70, False, _even([down_back, sit_up, k.crouch(0.22), stand]), cat="reaction"))
    add(_seq("getup_attack", 8, 55, False, _even([down_back, sit_up, sweep, k.crouch(0.18), guard]), cat="reaction"))
    add(_seq("getup_roll", 8, 55, False, _even([down_back, replace(ball, spin=-200), replace(ball, spin=-360), k.crouch(0.12)]), cat="reaction"))
    add(_seq("tech", 6, 55, False, _even([launch, k.crouch(0.2, spin=20), k.crouch(0.1)]), cat="reaction"))
    add(_seq("tech_roll", 8, 55, False, roll(1.0), cat="reaction"))
    for name in ("impact", "splat", "ground_bounce", "wall_tech", "wall_tech_jump", "ceiling_tech"):
        add(_seq(name, 6, 60, False, _even([hit, launch, hit]), cat="reaction"))

    def dizzy(ph: float) -> Pose:
        s, c = math.sin(ph), math.cos(ph)
        return k.pose(root=(0.0, -0.02, 0.0), lean=4 * s, side=6 * c, head=(8 * c, 10 * s), rh=k.hand(R, 0.25, -0.15, 0.4, pole=(0.6, 0.2, -0.5)),
                      lh=k.hand(Lf, 0.2, -0.1, 0.45, pole=(0.6, 0.2, -0.5)), rf=k.foot(R, 0.04 * s), lf=k.foot(Lf, -0.04 * s),
                      face="pained" if s > 0 else "afraid")

    add(_seq("dizzy", 8, 100, True, _cycle([dizzy(2 * math.pi * i / 8) for i in range(8)]), view="front_3q", cat="status"))
    asleep = k.lying(face_up=True, blink=1.0)
    add(_seq("sleep_start", 6, 110, False, _even([stand, k.sitting(face="sad", blink=0.0), k.sitting(lean=20, head=(30, 0), blink=1.0), asleep]),
              cat="status"))
    add(_seq("sleep", 8, 130, True, _cycle([asleep, replace(asleep, root=(asleep.root[0], asleep.root[1] - 0.004 * k.H, asleep.root[2]))]),
              cat="status"))
    add(_seq("wake", 6, 100, False, _even([asleep, sit_up, k.crouch(0.15), k.stand(face="surprised")]), cat="status"))
    for name in ("bury_start", "buried", "bury_escape"):
        add(_seq(name, 6, 90, name == "buried", _even([k.crouch(0.35, face="afraid"), k.crouch(0.36, face="afraid")]), cat="status"))
    for name in ("shield_break_launch", "shield_break_fall", "shield_break_collapse", "shield_break_recover"):
        add(_seq(name, 6, 80, False, _even([hit, launch if "launch" in name else (k.crouch(0.3, face="pained") if "collapse" in name else stand)]),
                 cat="status"))
    add(_seq("death", 8, 110, False, _even([hit, k.pose(root=(-0.03, -0.12, 0), spin=-35, head=(20, 0), face="pained"), down_back,
                                            k.lying(face_up=True, blink=1.0)]), cat="reaction"))
    add(_seq("death_idle", 4, 200, True, _cycle([k.lying(face_up=True, blink=1.0), k.lying(face_up=True, blink=1.0, head=(-2, 0))]), cat="reaction"))
    trip = k.lying(face_up=False, face="pained")
    add(_seq("trip_fall", 6, 80, False, _even([hit, trip]), cat="reaction"))
    add(_seq("trip_land", 6, 80, False, _even([trip, replace(trip, root=(trip.root[0], trip.root[1] - 0.004 * k.H, trip.root[2])), trip]), cat="reaction"))
    add(_seq("trip_idle", 6, 120, True, _cycle([trip, k.lying(face_up=False, face="pained", head=(-4, 0))]), cat="reaction"))
    for name in ("trip_getup", "trip_attack", "trip_roll"):
        add(_seq(name, 6, 80, False, _even([trip, sit_up, stand]), cat="reaction"))

    # ---- held items --------------------------------------------------------------------------
    g = _grip_poses(k, grip)
    item_ready = g["ready"]
    add(_seq("item_hold", 6, 110, True, _cycle([item_ready, replace(item_ready, lean=item_ready.lean + 0.6)]), cat="item"))
    add(_seq("item_grip", 4, 70, False, _even([stand, item_ready]), cat="item"))
    add(_seq("item_hold_crouch", 6, 110, True, _cycle([g["crouch"], replace(g["crouch"], lean=g["crouch"].lean + 0.6)]), cat="item"))
    pick_low = k.crouch(0.3, lean=40, head=(-20, 0), rh=k.hand(R, 0.75, 0.95, 0.15), lh=k.hand(Lf, 0.4, 0.8, 0.3))
    add(_seq("item_pickup", 7, 82, False, _even([stand, pick_low, pick_low, item_ready]), cat="item"))
    add(_seq("pickup", 7, 82, False, out["item_pickup"].keys, cat="item"))
    carry = k.pose(root=(0, -0.01, 0), lean=-6, head=(-6, 0), rh=k.hand(R, 0.4, -0.85, 0.2, pole=(0.6, 0.2, -0.6)),
                   lh=k.hand(Lf, 0.35, -0.83, 0.25, pole=(0.6, 0.2, -0.6)), face="pained")
    add(_seq("item_heavy_pickup", 8, 90, False, _even([stand, k.crouch(0.32, lean=30, rh=k.hand(R, 0.6, 0.95, 0.3), lh=k.hand(Lf, 0.55, 0.95, 0.35)),
                                                       k.crouch(0.15, rh=k.hand(R, 0.45, 0.2, 0.3), lh=k.hand(Lf, 0.4, 0.22, 0.35)), carry]), cat="item"))
    add(_seq("item_heavy_carry", 8, 100, True, _cycle([replace(walk_pose(2 * math.pi * i / 8), hands=carry.hands, lean=-6,
                                                              face=face_channels("pained")) for i in range(8)]), cat="item"))
    add(_seq("item_throw", 10, 54, False, [(0.0, item_ready), (0.35, g["throw_wind"]), (0.55, g["throw_release"]), (0.75, g["throw_follow"]),
                                          (1.0, guard)], cat="item"))
    add(_seq("item_drop", 5, 80, False, _even([item_ready, k.pose(rh=k.hand(R, 0.4, 0.75, 0.2, item=-60), face="surprised"), stand]), cat="item"))
    for name, (wind, hit, follow) in g["swings"].items():
        strike(name, wind, hit, follow, start=item_ready, end=item_ready, cat="item", frames=10, ms=50)

    # ---- talk, emotes and social -------------------------------------------------------------
    def talk_keys(face: str) -> List[Tuple[float, Pose]]:
        vs = ("a", "rest", "e", "o", "m", "a")
        poses = []
        for i, v in enumerate(vs):
            g = (0.0, 0.5, 1.0, 0.75, 0.25, 0.0)[i]
            poses.append(k.pose(lean=-1 + g, head=((-1) ** i * 2.0, 0), rh=k.hand(R, 0.12 + 0.4 * g, 0.88 - 0.55 * g, 0.12 + 0.05 * g,
                                                                                 pole=(0.4, 0.4, -0.6)),
                                face=face, vis=v))
        return _cycle(poses)

    add(_seq("talk", 6, 100, True, talk_keys("neutral"), view="front_3q", cat="social"))
    for emo in ("happy", "angry", "sad", "afraid", "surprised", "smug", "pained", "determined"):
        add(_seq(f"talk_{emo}", 6, 100, True, talk_keys(emo), view="front_3q", cat="social"))
    add(_seq("interact", 6, 90, False, _even([stand, k.pose(root=(0.02, -0.02, 0), lean=12, rh=k.hand(R, 0.9, 0.4, 0.1, pole=(0.3, 0.6, -0.4)),
                                                            face="neutral"), stand]), view="front_3q", cat="social"))
    hips = dict(rh=k.hand(R, 0.05, 0.42, 0.5, pole=(1.0, 0.0, 0.2)), lh=k.hand(Lf, 0.05, 0.42, 0.5, pole=(1.0, 0.0, 0.2)))
    add(_seq("taunt", 8, 100, False, _even([stand, k.pose(lean=-8, head=(-14, 0), face="happy", vis="a", **hips),
                                            k.pose(lean=-10, head=(-16, 0), face="smug", **hips), stand]), view="front_3q", cat="emote"))
    add(_seq("entrance", 8, 100, False, _even([k.pose(root=(-0.05, 0, 0), rf=k.foot(R, -0.2, 0.1)), walk_pose(0.0),
                                               k.pose(rh=k.hand(R, 0.3, -0.9, 0.35, pole=(0.7, 0, -0.4)), face="happy", vis="a")]),
              view="front_3q", cat="emote"))
    cheer = k.pose(root=(0, 0.06, 0), lean=-6, head=(-16, 0), rh=k.hand(R, 0.15, -0.97, 0.35, pole=(0.7, 0, -0.4)),
                   lh=k.hand(Lf, 0.1, -0.97, 0.4, pole=(0.7, 0, -0.4)), rf=k.bfoot(R, 0.05, 0.95, toe=30), lf=k.bfoot(Lf, -0.05, 0.95, toe=30),
                   face="happy", vis="a")
    lift = k.pose(lean=-2, head=(-8, 0), rh=k.hand(R, 0.75, 0.1, 0.3, pole=(0.6, 0.2, -0.6)), lh=k.hand(Lf, 0.7, 0.12, 0.35, pole=(0.6, 0.2, -0.6)),
                  face="happy", vis="e")
    add(_seq("celebrate", 10, 80, False, [(0.0, stand), (0.18, k.crouch(0.1, face="happy")), (0.34, lift), (0.5, cheer), (0.66, cheer), (0.82, lift),
                                          (1.0, stand)], view="front_3q", cat="emote"))
    fist = k.pose(lean=-4, rh=k.hand(R, 0.25, -0.95, 0.15, pole=(0.7, 0, -0.4)), face="happy", vis="e")
    add(_seq("victory", 8, 100, False, _even([stand, k.crouch(0.06, face="determined"), fist, fist]), view="front_3q", cat="emote"))
    add(_seq("victory_hold", 4, 150, True, _cycle([fist, replace(fist, lean=-5)]), view="front_3q", cat="emote"))
    slump = k.pose(root=(0, -0.01, 0), lean=12, head=(28, 0), rh=k.hand(R, 0.05, 0.95, 0.1), lh=k.hand(Lf, 0.05, 0.95, 0.12), face="sad")
    add(_seq("loss", 6, 140, True, _cycle([slump, replace(slump, lean=13)]), view="front_3q", cat="emote"))
    add(_seq("sit_down", 5, 120, False, _even([stand, k.crouch(0.14, lean=20), k.sitting()]), view="front_3q", cat="social"))
    add(_seq("sit_idle", 6, 140, True, _cycle([k.sitting(), k.sitting(lean=5, head=(3, 0))]), view="front_3q", cat="social"))
    add(_seq("sit", 5, 120, True, out["sit_idle"].keys, view="front_3q", cat="social"))
    add(_seq("stand_up", 5, 100, False, _even([k.sitting(), k.crouch(0.14, lean=24), stand]), view="front_3q", cat="social"))
    add(_seq("think", 6, 140, True, _cycle([k.pose(head=(8, 6), rh=k.hand(R, 0.38, -0.05, -0.1, pole=(0.5, 0.6, -0.4)),
                                                   lh=k.hand(Lf, 0.35, 0.45, -0.1), face="look_up"),
                                            k.pose(head=(9, 8), rh=k.hand(R, 0.38, -0.06, -0.1, pole=(0.5, 0.6, -0.4)),
                                                   lh=k.hand(Lf, 0.35, 0.45, -0.1), face="look_up")]), view="front_3q", cat="social"))

    def wave(ph: float) -> Pose:
        s = math.sin(ph)
        return k.pose(lean=-2, head=(-4, 0), rh=k.hand(R, 0.3, -0.75, 0.45 + 0.12 * s, pole=(0.8, 0.3, -0.3)), face="happy", vis="rest" if s < 0 else "e")

    add(_seq("wave", 8, 90, True, _cycle([wave(2 * math.pi * i / 8) for i in range(8)]), view="front_3q", cat="social"))
    add(_seq("point", 6, 90, False, _even([stand, k.pose(lean=4, rh=k.hand(R, 0.97, -0.15, 0.05, pole=(0.3, 0.8, -0.2), wrist=-3), face="determined",
                                                         vis="a"), k.pose(lean=4, rh=k.hand(R, 0.97, -0.15, 0.05, wrist=-3))]), view="front_3q", cat="social"))
    add(_seq("nod", 6, 90, False, _even([stand, k.pose(head=(16, 0), face="happy"), stand, k.pose(head=(12, 0), face="happy"), stand]),
              view="front_3q", cat="social"))
    shrug = k.pose(head=(-4, 8), rh=k.hand(R, 0.35, 0.35, 0.55, pole=(0.9, 0.4, -0.1)), lh=k.hand(Lf, 0.35, 0.35, 0.55, pole=(0.9, 0.4, -0.1)),
                   face="smug")
    add(_seq("shrug", 6, 100, False, _even([stand, shrug, shrug, stand]), view="front_3q", cat="social"))
    add(_seq("laugh", 8, 80, True, _cycle([k.pose(lean=-8, head=(-14, 0), face="happy", vis="a", **hips),
                                           k.pose(lean=6, head=(6, 0), face="happy", vis="e", **hips)]), view="front_3q", cat="emote"))
    add(_seq("cry", 8, 110, True, _cycle([k.pose(lean=14, head=(24, 0), rh=k.hand(R, 0.35, -0.12, -0.15, pole=(0.5, 0.6, -0.4)),
                                                 lh=k.hand(Lf, 0.35, -0.1, -0.12, pole=(0.5, 0.6, -0.4)), face="sad", vis="o"),
                                          k.pose(lean=15, head=(26, 0), rh=k.hand(R, 0.35, -0.12, -0.15, pole=(0.5, 0.6, -0.4)),
                                                 lh=k.hand(Lf, 0.35, -0.1, -0.12, pole=(0.5, 0.6, -0.4)), face="sad")]), view="front_3q", cat="emote"))
    add(_seq("angry", 6, 100, True, _cycle([k.pose(lean=6, head=(-6, 0), face="angry", vis="e", **hips),
                                            k.pose(lean=7, head=(-7, 0), face="angry", vis="a", **hips)]), view="front_3q", cat="emote"))
    add(_seq("scared", 6, 80, True, _cycle([k.crouch(0.08, lean=-10, rh=k.hand(R, 0.5, -0.1, 0.1, pole=(0.5, 0.6, -0.4)),
                                                     lh=k.hand(Lf, 0.45, 0.0, 0.05, pole=(0.5, 0.6, -0.4)), face="afraid"),
                                            k.crouch(0.09, lean=-11, rh=k.hand(R, 0.5, -0.12, 0.1, pole=(0.5, 0.6, -0.4)),
                                                     lh=k.hand(Lf, 0.45, -0.02, 0.05, pole=(0.5, 0.6, -0.4)), face="afraid")]), view="front_3q",
              cat="emote"))
    add(_seq("happy", 6, 100, True, _cycle([k.pose(root=(0, 0.01, 0), face="happy", vis="a"), k.pose(face="happy")]), view="front_3q", cat="emote"))
    pat = k.crouch(0.22, lean=24, rh=k.hand(R, 0.9, 0.75, 0.1), face="happy")
    add(_seq("pet", 8, 125, True, _cycle([pat, k.crouch(0.22, lean=24, rh=k.hand(R, 0.8, 0.72, 0.1), face="happy")]), view="front_3q", cat="social"))
    add(_seq("petted", 6, 120, True, _cycle([k.pose(head=(10, 8), face="happy"), k.pose(head=(12, 10), face="happy", blink=1.0)]), view="front_3q",
              cat="social"))
    add(_seq("bark", 4, 80, False, _even([stand, k.pose(lean=8, head=(-8, 0), face="angry", vis="a"), stand]), view="front_3q", cat="social"))
    return out


#: The view the sprite sheet draws a row from, when the clip does not say.
DEFAULT_VIEW = "side"


def _frame_times(clip: Clip) -> List[float]:
    n = clip.frames
    return [i / n for i in range(n)] if clip.loop else [i / max(1, n - 1) for i in range(n)]


def pose_at(clip: Clip, t: float, rest: RestFrame) -> Pose:
    """The pose at ``t`` (keys eased in and out)."""
    keys = clip.keys
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1:
            u = (t - t0) / max(1e-9, t1 - t0)
            u = u * u * (3 - 2 * u)
            return blend(a, b, u, rest)
    return keys[-1][1]


def _default_of(name: str) -> float:

    return 1.0 if name in (eyes_part("neutral") + "_vis", brows_part("neutral") + "_vis", mouth_part("neutral") + "_vis") else 0.0


#: The most a forearm may turn between two frames (degrees): past it a
#: motion pops instead of moving (``pose_audit``'s frame-pop rule).
MAX_TURN_PER_FRAME = 112.0


def _solve_frames(clip: Clip, solver: ViewSolver) -> List[dict]:
    solver.reset()
    frames = [solver.solve(pose_at(clip, t, solver.rest)) for t in _frame_times(clip)]
    # A leg keeps one bend through a clip (its knee does not flip sides as
    # the foot passes under the hip): the side most frames clearly want. An
    # arm's side is read from its drawn elbow, frame by frame.
    for pre, votes in solver.votes.items():
        if not pre.endswith("_foot"):
            continue
        weight = sum(m if b > 0 else -m for b, m in votes)
        side = 1.0 if weight >= 0 else -1.0
        for f in frames:
            if f"{pre}_bend" in f:
                f[f"{pre}_bend"] = side
    for pre in ("near_hand", "far_hand"):
        key, ikey = f"{pre}_wrist", f"{pre}_item"
        if any(f.get(key) or ikey in f for f in frames):
            rest = solver.rest_world[solver.chains[pre]["end"]].angle
            for f in frames:
                follow = _world(pre, f, solver)[0]
                if ikey in f:
                    # The hand turns so the item points where the pose says,
                    # as far as a wrist bends.
                    want = rest + f[ikey] + ITEM_REST
                    bend = max(-WRIST_LIMIT, min(WRIST_LIMIT, (want - follow + 180.0) % 360.0 - 180.0))
                    f[f"{pre}_pitch"] = follow + bend
                else:
                    f[f"{pre}_pitch"] = follow + f.get(key, 0.0)
        for f in frames:
            f.pop(key, None)
    for f in frames:
        if f.get("near_hand_two"):
            _close_other_hand(f, solver)
        for k in ("near_hand_item", "far_hand_item", "near_hand_two", "far_hand_two"):
            f.pop(k, None)
    return frames


#: How far a wrist turns a hand off its forearm's line (degrees). The game
#: holds every item ACROSS the fist (forward and 24 deg up with the arm
#: hanging), so a gun aimed down an outstretched arm needs the fist turned
#: about 110 deg; the limit allows it (inside ``pose_audit``'s 115). An item
#: class held along the forearm (a gun's barrel) would need a per-item rest
#: angle in the runtime instead.
WRIST_LIMIT = 112.0


def _close_other_hand(frame: dict, solver: ViewSolver) -> None:
    """A two-handed grip: the far hand closes on the item ``near_hand_two``
    px along it from the near grip, its fist turned as the near one is."""
    probe = {k: {"const": v} for k, v in frame.items() if not k.endswith(("_item", "_two"))}
    solver._probe.data["clips"]["probe"] = {"loop": False, "frames": 1, "duration_ms": 100, "channels": probe}
    world, _ = solver._probe.solve("probe", 0.0)
    rest = solver.rest_world
    near_end, far_end = solver.chains["near_hand"]["end"], solver.chains["far_hand"]["end"]
    turn = world[near_end].angle - rest[near_end].angle
    theta = math.radians(frame["near_hand_item"])
    d = (math.cos(theta), math.sin(theta))
    g = world["near_grip"].origin
    chain = solver.chains["far_hand"]
    shoulder = world[chain["upper"]].origin
    reach = 0.97 * (solver.bone_len[chain["upper"]] + solver.bone_len[chain["lower"]])
    # The far hand takes the handle where it comes nearest its shoulder,
    # behind the near hand (toward the pommel) when it can, a hand apart at
    # least and no further than the grip allows.
    span = frame["near_hand_two"]
    s = (shoulder[0] - g[0]) * d[0] + (shoulder[1] - g[1]) * d[1]
    s = max(-span, min(span, s))
    if abs(s) < 0.55 * span:
        s = -0.55 * span if s <= 0.0 else 0.55 * span
    target_grip = (g[0] + s * d[0], g[1] + s * d[1])
    off = (rest["far_grip"].origin[0] - rest[far_end].origin[0], rest["far_grip"].origin[1] - rest[far_end].origin[1])
    r = math.radians(turn)
    off = (off[0] * math.cos(r) - off[1] * math.sin(r), off[0] * math.sin(r) + off[1] * math.cos(r))
    wrist = (target_grip[0] - off[0], target_grip[1] - off[1])
    gap = math.dist(wrist, shoulder)
    if gap > reach:
        wrist = (shoulder[0] + (wrist[0] - shoulder[0]) * reach / gap, shoulder[1] + (wrist[1] - shoulder[1]) * reach / gap)
    cx, gy = float(solver.frame["center_x"]), float(solver.frame["ground_y"])
    frame["far_hand_x"] = wrist[0] - cx
    frame["far_hand_y"] = wrist[1] - gy
    # The far fist turns with the near one, as far as its own wrist allows
    # (its forearm read with the hand where it now is).
    follow = _world("far_hand", frame, solver)[0]
    want = rest[far_end].angle + turn
    frame["far_hand_pitch"] = follow + max(-WRIST_LIMIT, min(WRIST_LIMIT, (want - follow + 180.0) % 360.0 - 180.0))


def _largest_turn(clip: Clip, frames: List[dict], solver: ViewSolver) -> float:
    worst = 0.0
    for pre in ("near_hand", "far_hand"):
        angles = [_world(pre, f, solver)[1] for f in frames]
        pairs = list(zip(angles, angles[1:])) + ([(angles[-1], angles[0])] if clip.loop else [])
        for a, b in pairs:
            worst = max(worst, abs((b - a + 180.0) % 360.0 - 180.0))
    return worst


def solve_clip(clip: Clip, solver: ViewSolver) -> dict:
    """One clip as a ``RigDocument`` clip: a key per frame for every channel.

    A clip whose forearms would turn more than ``MAX_TURN_PER_FRAME`` between
    frames (a spin, a fast swing) is sampled with more frames over the same
    time, so it moves rather than pops."""
    from ..authoring.rig_clip_keys import const, keys as loop_keys, shot

    frames = _solve_frames(clip, solver)
    tries = 0
    worst = _largest_turn(clip, frames, solver)
    while worst > MAX_TURN_PER_FRAME and tries < 3:
        total = clip.frames * clip.ms
        n = clip.frames + max(2, clip.frames // 2)
        finer = replace(clip, frames=n, ms=max(16, int(round(total / n))))
        finer_frames = _solve_frames(finer, solver)
        finer_worst = _largest_turn(finer, finer_frames, solver)
        tries += 1
        if finer_worst < worst:
            clip, frames, worst = finer, finer_frames, finer_worst
    names = sorted(set().union(*frames))
    channels = {}
    for name in names:
        default = _default_of(name) if name.endswith("_vis") else None
        vals = [f.get(name, default) for f in frames]
        known = [v for v in vals if v is not None]
        vals = [v if v is not None else known[0] for v in vals]
        if max(vals) - min(vals) < 1e-6:
            channels[name] = const(vals[0])
        else:
            ease = "linear" if name.endswith(("_bend", "_vis")) else "smooth"
            channels[name] = (loop_keys(vals, ease=ease) if clip.loop else shot(vals, ease=ease))
    return {"loop": clip.loop, "frames": clip.frames, "duration_ms": clip.ms, "channels": channels}


def _world(pre: str, frame: dict, solver: ViewSolver) -> Tuple[float, float]:
    """(the world angle of the hand following its forearm, the forearm's
    world angle) in this frame."""
    chain = solver.chains[pre]
    bones = {b["name"]: b for b in solver.doc["bones"]}
    rel = float(bones[chain["end"]]["rest_angle"])
    probe = {k: {"const": v} for k, v in frame.items() if not k.endswith(("_wrist", "_pitch")) or "foot" in k}
    solver._probe.data["clips"]["probe"] = {"loop": False, "frames": 1, "duration_ms": 100, "channels": probe}
    world, _ = solver._probe.solve("probe", 0.0)
    a = world[chain["lower"]].angle
    return a + rel, a


def library_clips(fig: Figure, view: View, doc: dict, names: Optional[Sequence[str]] = None, *, grip: str = "blade") -> Dict[str, dict]:
    """Every clip of the library (or ``names``) solved for one view's rig,
    the item clips posed for ``grip``."""
    from .rig import PX_PER_CM

    lib = build_library(fig, grip)
    solver = ViewSolver(fig, view, doc, PX_PER_CM)
    return {name: solve_clip(c, solver) for name, c in lib.items() if names is None or name in names}


def publish_views(fig: Figure) -> Dict[str, str]:
    return {name: c.view for name, c in build_library(fig).items()}


__all__ = ["GRIPS", "Clip", "Kit", "build_library", "library_clips", "pose_at", "publish_views", "solve_clip"]
