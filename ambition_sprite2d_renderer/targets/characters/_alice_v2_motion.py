"""Alice's motion: her own clips on the character generator's pose kit.

The motion library (``chargen.motion.build_library``) moves any generated
body. Alice is a fighter with a range pole, so the rows she fights in are her
own: the pole points along every thrust and sweep (``Kit.hand(item=)``), her
far fist closes on it for a two-handed blow (``two_hand``), and each strike
keys its effects (``fx.*``) for ``alice_v2.py`` to draw. Every other row (a
roll, a ledge, a ladder, a hit) is the library's, with her pole in her fist.

Her moves follow ``game/ambition_content/assets/data/movesets/alice.ron``:
she sends, so her kit is reach and recovery. A strike has a short wind-up,
a fast contact and a follow-through past the target; contact sits near the
part of the clip where the move's hitbox is active.

Channels a key may name (``Kit.pose(**extra)``):

* ``prop.staff`` (1: the pole in her right fist; 0: it is put away) and
  ``prop.letter`` (1: a sealed letter in her left fist);
* ``fx.trail``, ``fx.spark``, ``fx.shield``, ``fx.blink``, ``fx.charge``,
  ``fx.cast``, ``fx.aim``, ``fx.dart``, ``fx.speed``, ``fx.dust``,
  ``fx.whirl``, ``fx.compass``, ``fx.pin``, ``fx.key``, ``fx.burst``,
  ``fx.letter``: effect strengths.

``ROWS`` is the sheet: every row the first Alice sheet published (so the
game finds each one by name), then the rows her moveset asks for that the
first sheet did not have (``jab``, the smashes, her specials, the grab).
"""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Dict, List, Sequence, Tuple

from ...chargen.motion import Clip, Kit, build_library
from ...chargen.pose3d import Pose

R, L = "right", "left"
#: How far (cm) along the pole her far fist closes, for a two-handed grip.
TWO = 24.0

#: The rows of the first Alice sheet, in its order.
CONTRACT_ROWS: Tuple[str, ...] = (
    "idle", "walk", "run", "jump", "fall", "slash", "hit", "death", "blink_out", "blink_in", "dash", "crouch", "wall_slide",
    "wall_jump", "ledge_grab", "climb", "swim", "interact", "talk", "block", "land", "roll", "slide", "crouch_walk", "pickup",
    "throw", "aim", "shoot", "charge", "cast", "celebrate", "sit", "sleep", "hover", "stomp", "dash_startup", "land_hard",
    "land_recovery", "wall_grab", "ledge_climb", "ledge_getup", "ledge_roll", "ledge_getup_attack", "float_glide",
    "attack_side", "attack_up", "attack_down", "air_neutral", "air_forward", "air_back", "air_down", "air_up", "idle_front",
    "idle_side",
)
#: The rows her moveset names that the first sheet had not (it fell back).
MOVESET_ROWS: Tuple[str, ...] = (
    "jab", "dash_attack", "smash_forward", "smash_up", "smash_down", "taunt", "one_time_pad", "key_exchange", "elliptic_curve",
    "hash_collision", "collision_dive", "grab", "pummel", "throw_forward", "throw_back", "throw_up", "throw_down",
)
ROWS: Tuple[str, ...] = CONTRACT_ROWS + MOVESET_ROWS

#: Rows in which the pole is put away (both hands are busy).
POLE_AWAY = ("climb", "ledge_grab", "ledge_climb", "ledge_getup", "ledge_roll", "wall_grab", "wall_slide", "swim", "sleep")

#: An extra channel's value in a key that does not name it.
EXTRA_DEFAULTS = {"prop.staff": 1.0}


def _x(p: Pose, **ch: float) -> Pose:
    """``p`` with extra channels (``prop_staff`` names ``prop.staff``)."""
    return replace(p, extra={**p.extra, **{k.replace("_", ".", 1): float(v) for k, v in ch.items()}})


def _seq(name: str, frames: int, ms: int, loop: bool, keys: Sequence[Tuple[float, Pose]], view: str = "side", cat: str = "alice") -> Clip:
    """A clip whose keys all name the same extra channels: a channel one key
    names and another does not is that channel's default there, so a blend
    never fades the pole out by accident."""
    names = set()
    for _t, p in keys:
        names |= set(p.extra)
    filled = [(t, replace(p, extra={**{n: EXTRA_DEFAULTS.get(n, 0.0) for n in names}, **p.extra})) for t, p in keys]
    return Clip(name, frames, ms, loop, filled, view, cat)


def _cycle(poses: Sequence[Pose]) -> List[Tuple[float, Pose]]:
    n = len(poses)
    return [(i / n, p) for i, p in enumerate(poses)] + [(1.0, poses[0])]


def _even(poses: Sequence[Pose]) -> List[Tuple[float, Pose]]:
    n = len(poses)
    return [(i / max(1, n - 1), p) for i, p in enumerate(poses)]


def alice_library(fig) -> Dict[str, Clip]:
    """Every clip of her sheet: the library's (posed for a staff), with her
    own in place of the rows she fights and talks in."""
    lib = build_library(fig, "staff")
    k = Kit(fig)
    out: Dict[str, Clip] = dict(lib)

    def add(c: Clip) -> None:
        out[c.name] = c

    def pole(fwd, down, item, out_=0.06, two=TWO, pole_=(0.3, 0.6, -0.5), **kw):
        """Her right fist at (fwd, down) with the pole pointing ``item``."""
        return k.hand(R, fwd, down, out_, pole=pole_, item=item, two_hand=two, **kw)

    def carry(fwd, down, item, out_=0.2, **kw):
        return k.hand(R, fwd, down, out_, pole=(0.25, 0.2, -1.0), item=item, **kw)

    # ---- stance ------------------------------------------------------------------------------
    def ready(**kw) -> Pose:
        """Her guard: side on, knees soft, the pole held low and level like a
        spear in both hands, its point at the opponent's chest."""
        base = dict(root=(0.0, -0.035, 0.0), lean=7.0, head=(-3.0, 0.0), rh=pole(0.42, 0.62, 12.0),
                    lh=k.hand(L, 0.2, 0.7, 0.05, pole=(0.3, 0.6, -0.5)), rf=k.foot(R, 0.15, 0.0, 0.03), lf=k.foot(L, -0.15, 0.0, 0.03, toe=-6),
                    face="determined")
        base.update(kw)
        return k.pose(**base)

    guard = ready()

    def at_ease(lean=0.0, dy=0.0, head=(0.0, 0.0), item=86.0, fwd=-0.08, **kw) -> Pose:
        """Standing easy, the pole upright in her right fist, at her side."""
        base = dict(root=(0.0, dy, 0.0), lean=lean, head=head, rh=carry(fwd, 0.74, item, 0.27))
        base.update(kw)
        return k.pose(**base)

    def holding(lift: float = 0.0, **kw) -> Pose:
        """At ease with a sealed letter in her left hand (she carries
        messages), and a smile, as the first Alice stood."""
        kw.setdefault("face", "happy")
        return _x(at_ease(lh=k.hand(L, 0.24 + lift, 0.64 - lift, 0.16, pole=(0.3, 0.4, -0.8), item=64.0), **kw), prop_letter=1.0)

    idle_keys = _cycle([holding(), holding(0.01, lean=1.0, dy=-0.004, head=(1.5, 0.0), item=87.0),
                        holding(0.02, lean=1.4, dy=-0.006, head=(2.0, 1.0), item=88.0), holding(0.01, lean=0.6, dy=-0.003, head=(0.8, 0.5), item=87.0)])
    add(_seq("idle", 8, 120, True, idle_keys, view="front_3q", cat="idle"))
    add(_seq("idle_side", 8, 120, True, idle_keys, view="side", cat="idle"))
    add(_seq("idle_front", 8, 120, True, idle_keys, view="front", cat="idle"))
    add(_seq("idle_back", 8, 120, True, idle_keys, view="back_3q", cat="idle"))

    # ---- locomotion: the pole carried --------------------------------------------------------
    def walk_pose(ph: float) -> Pose:
        c, s = math.cos(ph), math.sin(ph)
        return k.pose(root=(0.0, -0.012 * abs(c) + 0.006, 0.0), lean=3.0, head=(-1.5, 0.0),
                      rf=k.foot(R, 0.13 * c, max(0.0, -s) * 0.12, 0.0, toe=18 * max(0.0, -s) - 10 * max(0.0, c)),
                      lf=k.foot(L, -0.13 * c, max(0.0, s) * 0.12, 0.0, toe=18 * max(0.0, s) - 10 * max(0.0, -c)),
                      rh=carry(0.16 - 0.1 * c, 0.74, 74.0 + 5.0 * c, 0.2), lh=k.hand(L, 0.12 + 0.3 * c, 0.88, 0.16, pole=(0.25, 0.2, -1.0)))

    walk = _cycle([walk_pose(2 * math.pi * i / 8) for i in range(8)])
    add(_seq("walk", 8, 95, True, walk, cat="locomotion"))
    add(_seq("walk_away", 8, 100, True, walk, view="back_3q", cat="locomotion"))
    add(_seq("walk_toward", 8, 100, True, walk, view="front_3q", cat="locomotion"))

    def run_pose(ph: float) -> Pose:
        c, s = math.cos(ph), math.sin(ph)
        return k.pose(root=(0.0, -0.035 + 0.03 * abs(s), 0.0), lean=17.0, head=(-11.0, 0.0),
                      rf=k.bfoot(R, 0.42 * c, 0.86 - 0.32 * max(0.0, -s), 0.04, toe=20 * max(0.0, -s)),
                      lf=k.bfoot(L, -0.42 * c, 0.86 - 0.32 * max(0.0, s), 0.04, toe=20 * max(0.0, s)),
                      rh=carry(0.3 - 0.08 * c, 0.62, 18.0 + 4.0 * c, 0.14), lh=k.hand(L, 0.3 + 0.45 * c, 0.6, 0.14, pole=(0.2, 0.4, -1.0)),
                      face="determined")

    run = _cycle([run_pose(2 * math.pi * i / 8) for i in range(8)])
    add(_seq("run", 8, 72, True, run, cat="locomotion"))
    add(_seq("dash", 6, 60, True, _cycle([_x(run_pose(2 * math.pi * i / 6), fx_speed=0.6) for i in range(6)]), cat="locomotion"))
    add(_seq("dash_startup", 4, 50, False, _even([at_ease(), _x(k.crouch(0.1, lean=26, rh=carry(-0.1, 0.6, 10.0), lh=k.hand(L, 0.45, 0.55)),
                                                                 fx_speed=0.3), _x(run_pose(0.0), fx_speed=0.6)]), cat="locomotion"))

    # ---- talk, interact, the letter ---------------------------------------------------------------
    def talk_keys() -> List[Tuple[float, Pose]]:
        vs = ("a", "rest", "e", "o", "m", "a")
        poses = []
        for i, v in enumerate(vs):
            g = (0.0, 0.5, 1.0, 0.75, 0.25, 0.0)[i]
            poses.append(_x(k.pose(lean=-1 + g, head=((-1) ** i * 2.0, 0.0), rh=carry(-0.08, 0.74, 86.0, 0.27),
                                   lh=k.hand(L, 0.18 + 0.35 * g, 0.85 - 0.5 * g, 0.12 + 0.05 * g, pole=(0.4, 0.4, -0.6), item=40.0 + 30.0 * g),
                                   face="neutral", vis=v), prop_letter=1.0))
        return _cycle(poses)

    add(_seq("talk", 8, 110, True, talk_keys(), view="front_3q", cat="social"))
    read = _x(k.pose(root=(0.0, -0.01, 0.0), lean=6, head=(14.0, -6.0), rh=carry(-0.08, 0.74, 86.0, 0.27),
                     lh=k.hand(L, 0.45, 0.2, 0.0, pole=(0.4, 0.6, -0.5), item=60.0), face="determined"), prop_letter=1.0)
    add(_seq("interact", 6, 90, False, _even([_x(at_ease(), prop_letter=1.0), read, _x(replace(read, head=(16.0, 4.0)), prop_letter=1.0),
                                              _x(at_ease(), prop_letter=1.0)]), view="front_3q", cat="social"))
    wind = _x(k.pose(lean=-12, side=4, rh=carry(0.2, 0.7, 70.0), lh=k.hand(L, -0.45, -0.55, 0.3, pole=(0.5, 0.2, -0.6), item=130.0),
                     rf=k.foot(R, 0.2), lf=k.foot(L, -0.22), face="determined"), prop_letter=1.0)
    release = _x(k.pose(root=(0.03, -0.03, 0.0), lean=18, rh=carry(0.1, 0.7, 60.0), lh=k.hand(L, 0.95, 0.15, 0.05, item=10.0),
                        rf=k.foot(R, 0.25), lf=k.foot(L, -0.2, toe=-12), face="determined", vis="a"), prop_letter=0.0, fx_letter=1.0)
    add(_seq("throw", 7, 72, False, [(0.0, _x(at_ease(), prop_letter=1.0)), (0.3, wind), (0.5, release),
                                     (0.75, _x(replace(release, lean=14), fx_letter=0.0)), (1.0, at_ease())], cat="item"))

    # ---- defence -------------------------------------------------------------------------------
    bar = ready(root=(0.0, -0.06, 0.0), lean=4.0, rh=pole(0.48, 0.4, 84.0, two=28.0), face="determined")
    add(_seq("block", 6, 85, True, _cycle([_x(bar, fx_shield=1.0), _x(replace(bar, lean=5.0), fx_shield=0.92)]), cat="defense"))
    add(_seq("shield_hold", 6, 85, True, out["block"].keys, cat="defense"))

    # ---- strikes with the pole -------------------------------------------------------------------
    def strike(name: str, wind_: Pose, hit: Pose, follow: Pose, frames: int = 8, ms: int = 65, start: Pose = guard, end=None,
               at=(0.28, 0.45, 0.62)) -> None:
        add(_seq(name, frames, ms, False, [(0.0, start), (at[0], wind_), (at[1], _x(hit, fx_trail=1.0, fx_spark=1.0)),
                                           (at[2], _x(follow, fx_spark=0.35)), (1.0, end or start)], cat="attack"))

    # The jab: a quick poke from the guard; a question, not an answer.
    strike("jab", ready(lean=4.0, rh=pole(0.22, 0.6, 14.0)),
           ready(root=(0.02, -0.04, 0.0), lean=13.0, rh=pole(0.98, 0.45, 4.0), face="angry"),
           ready(root=(0.02, -0.04, 0.0), lean=11.0, rh=pole(0.9, 0.48, 6.0)), frames=7, ms=40, at=(0.2, 0.36, 0.55))
    # The forward tilt: a lunge, the whole length of the pole.
    lunge = dict(root=(0.07, -0.07, 0.0), lean=20.0, rf=k.foot(R, 0.44, toe=-4), lf=k.foot(L, -0.3, toe=-22), face="angry")
    strike("attack_side", ready(root=(-0.02, -0.04, 0.0), lean=-4.0, rh=pole(0.12, 0.62, 18.0), rf=k.foot(R, 0.08)),
           ready(rh=pole(1.0, 0.36, 2.0), **lunge), ready(rh=pole(0.95, 0.42, -6.0), **lunge))
    # The slash: a diagonal chop from over her head.
    strike("slash", ready(lean=-8.0, head=(-8.0, 0.0), rh=pole(-0.05, -0.65, 125.0, pole_=(0.5, 0.2, -0.6))),
           ready(root=(0.04, -0.05, 0.0), lean=18.0, rh=pole(0.85, 0.35, -18.0), rf=k.foot(R, 0.3), face="angry"),
           ready(root=(0.04, -0.06, 0.0), lean=20.0, rh=pole(0.6, 0.72, -52.0), rf=k.foot(R, 0.3)), ms=66)
    # The up tilt: the point flicked straight up, a nonce thrown once.
    strike("attack_up", k.crouch(0.1, lean=10, rh=pole(0.5, 0.72, -15.0), face="angry"),
           k.pose(root=(0.01, 0.01, 0.0), lean=-8, head=(-20.0, 0.0), rh=pole(0.3, -0.78, 94.0, pole_=(0.5, 0.2, -0.6)),
                  rf=k.foot(R, 0.06, toe=18), lf=k.foot(L, -0.08), face="angry"),
           k.pose(lean=-13, head=(-24.0, 0.0), rh=pole(-0.05, -0.86, 122.0, pole_=(0.5, 0.2, -0.6))))
    # The down tilt: the pole along the floor, at the shins.
    low = k.crouch(0.2, lean=16, rh=pole(0.5, 0.72, 2.0))
    strike("attack_down", k.crouch(0.24, lean=18, rh=pole(0.12, 0.62, 30.0), face="angry"),
           _x(k.crouch(0.3, lean=26, head=(-6.0, 0.0), rh=pole(0.98, 0.86, -12.0), rf=k.foot(R, 0.3), lf=k.foot(L, -0.2, toe=-15), face="angry"),
              fx_dust=0.8),
           k.crouch(0.28, lean=24, rh=pole(0.82, 0.9, -20.0)), start=low)
    # The dash attack: a running lunge that keeps going.
    add(_seq("dash_attack", 10, 40, False, [(0.0, run_pose(0.0)),
                                            (0.18, _x(k.crouch(0.1, lean=26, rh=pole(0.2, 0.6, 14.0), face="angry"), fx_speed=0.8)),
                                            (0.32, _x(ready(root=(0.08, -0.09, 0.0), lean=28, rh=pole(1.0, 0.4, 0.0), rf=k.foot(R, 0.46, toe=-6),
                                                            lf=k.foot(L, -0.34, 0.08, toe=-30), face="angry"), fx_trail=1.0, fx_spark=1.0, fx_speed=1.0)),
                                            (0.55, _x(ready(root=(0.08, -0.08, 0.0), lean=24, rh=pole(0.95, 0.5, -10.0), rf=k.foot(R, 0.46)),
                                                      fx_spark=0.3, fx_dust=0.8)),
                                            (1.0, guard)], cat="attack"))

    # ---- smashes -------------------------------------------------------------------------------
    coil = _x(ready(root=(-0.03, -0.07, 0.0), lean=-14.0, side=-5.0, rh=pole(-0.38, 0.5, 10.0), rf=k.foot(R, 0.2), lf=k.foot(L, -0.26),
                    face="angry", vis="e"), fx_charge=0.7)
    drive = ready(root=(0.1, -0.1, 0.0), lean=28.0, rh=pole(1.0, 0.32, 0.0), rf=k.foot(R, 0.5, toe=-4), lf=k.foot(L, -0.32, toe=-24),
                  face="angry", vis="a")
    add(_seq("smash_forward", 10, 54, False, [(0.0, guard), (0.25, coil), (0.32, coil), (0.42, _x(drive, fx_trail=1.0, fx_spark=1.0, fx_burst=1.0)),
                                              (0.58, _x(replace(drive, lean=30.0), fx_spark=0.4)), (0.8, ready(root=(0.06, -0.08, 0.0), lean=20.0,
                                                                                                              rh=pole(0.85, 0.5, -10.0))),
                                              (1.0, guard)], cat="smash"))
    sup_wind = _x(k.crouch(0.26, lean=22, rh=pole(0.35, 0.8, 160.0, pole_=(0.4, 0.6, -0.5)), face="angry"), fx_charge=0.6)
    sup_hit = k.pose(root=(0.0, 0.04, 0.0), lean=-6, head=(-26.0, 0.0), rh=pole(0.15, -0.95, 92.0, pole_=(0.6, 0.2, -0.6)),
                     rf=k.foot(R, 0.0, 0.05, toe=30), lf=k.foot(L, -0.06, 0.08, toe=30), face="angry", vis="a")
    add(_seq("smash_up", 10, 54, False, [(0.0, guard), (0.28, sup_wind), (0.44, _x(sup_hit, fx_trail=1.0, fx_spark=1.0, fx_burst=1.0)),
                                         (0.62, _x(k.pose(lean=-12, head=(-22.0, 0.0), rh=pole(-0.2, -0.86, 128.0, pole_=(0.6, 0.2, -0.6))),
                                                   fx_spark=0.3)), (1.0, guard)], cat="smash"))
    sd_wind = _x(k.crouch(0.18, lean=8, rh=pole(0.25, 0.3, 75.0), face="angry"), fx_charge=0.6)
    sd_front = _x(k.crouch(0.32, lean=24, rh=pole(0.95, 0.86, -14.0), rf=k.foot(R, 0.3), lf=k.foot(L, -0.3), face="angry", vis="a"),
                  fx_trail=1.0, fx_spark=1.0, fx_dust=1.0)
    sd_back = _x(k.crouch(0.32, lean=6, side=-6, rh=pole(-0.7, 0.64, 186.0, pole_=(0.8, 0.4, -0.3)), rf=k.foot(R, 0.3), lf=k.foot(L, -0.3),
                          face="angry", vis="a"), fx_trail=1.0, fx_spark=1.0, fx_dust=1.0)
    add(_seq("smash_down", 11, 51, False, [(0.0, guard), (0.25, sd_wind), (0.4, sd_front), (0.58, sd_back),
                                           (0.75, _x(k.crouch(0.2, lean=10, rh=pole(-0.2, 0.7, 150.0)), fx_spark=0.2)), (1.0, guard)],
              cat="smash"))

    # ---- aerials -------------------------------------------------------------------------------
    def air(**kw) -> Pose:
        base = dict(lean=6.0, rh=pole(0.4, 0.55, 20.0), lh=k.hand(L, 0.15, 0.6, 0.2), rf=k.bfoot(R, 0.25, 0.72), lf=k.bfoot(L, -0.1, 0.82),
                    face="determined")
        base.update(kw)
        return k.air(**base)

    hang = air()
    # Neutral air: the pole swung all round her, noise in every direction.
    spin = []
    for i in range(9):
        th = 360.0 * i / 8.0
        r = math.radians(th)
        spin.append((0.08 + 0.84 * i / 8.0, _x(air(rh=pole(0.55 * math.cos(r), 0.25 - 0.55 * math.sin(r), th + 8.0, two=0.0,
                                                          pole_=(0.4, 0.5, -0.6)), rf=k.bfoot(R, 0.35, 0.55), lf=k.bfoot(L, 0.25, 0.6)),
                                                fx_compass=1.0 if 0 < i < 8 else 0.0)))
    add(_seq("air_neutral", 12, 40, False, [(0.0, hang)] + spin + [(1.0, hang)], cat="aerial"))
    strike("air_forward", air(lean=-6.0, rh=pole(-0.15, -0.6, 118.0, pole_=(0.5, 0.2, -0.6))),
           air(lean=14.0, rh=pole(0.95, 0.3, -12.0), face="angry"), air(lean=16.0, rh=pole(0.6, 0.75, -58.0)), frames=8, ms=48,
           start=hang, end=hang)
    strike("air_back", air(lean=8.0, rh=pole(0.55, 0.45, 8.0)),
           air(lean=-12.0, side=-8.0, head=(6.0, 0.0), rh=pole(-0.85, 0.35, 182.0, pole_=(0.8, 0.3, -0.3)), face="angry"),
           air(lean=-10.0, rh=pole(-0.6, 0.55, 205.0, pole_=(0.8, 0.3, -0.3))), frames=8, ms=50, start=hang, end=hang)
    strike("air_up", air(rh=pole(0.35, 0.6, -40.0)),
           air(lean=-8.0, head=(-24.0, 0.0), rh=pole(0.2, -0.95, 92.0, pole_=(0.6, 0.2, -0.6)), face="angry"),
           air(lean=-10.0, head=(-20.0, 0.0), rh=pole(-0.1, -0.88, 118.0, pole_=(0.6, 0.2, -0.6))), frames=8, ms=46, start=hang, end=hang)
    strike("air_down", air(lean=-4.0, rh=pole(0.3, -0.35, 70.0), rf=k.bfoot(R, 0.35, 0.5), lf=k.bfoot(L, 0.3, 0.55)),
           air(lean=10.0, head=(14.0, 0.0), rh=pole(0.3, 0.95, -88.0, pole_=(0.4, 0.5, -0.6)), rf=k.bfoot(R, 0.2, 0.62), lf=k.bfoot(L, 0.1, 0.68),
               face="angry"),
           air(lean=8.0, rh=pole(0.32, 0.92, -84.0)), frames=8, ms=50, start=hang, end=hang)

    # ---- specials ------------------------------------------------------------------------------
    # One-time pad: her hardest blow, used once. She takes a hit while she
    # raises the pole (armour), then brings it down with everything.
    high = _x(k.pose(root=(-0.02, -0.02, 0.0), lean=-10, head=(-12.0, 0.0), rh=pole(0.0, -0.85, 105.0, pole_=(0.6, 0.2, -0.6)),
                     rf=k.foot(R, 0.16), lf=k.foot(L, -0.22), face="angry", vis="e"), fx_charge=1.0)
    higher = _x(replace(high, lean=-14.0, hands={**high.hands, R: pole(-0.18, -0.9, 128.0, pole_=(0.6, 0.2, -0.6))}), fx_charge=1.0)
    pad_hit = _x(k.crouch(0.14, root=(0.07, -0.14, 0.0), lean=32, head=(-4.0, 0.0), rh=pole(0.95, 0.6, -34.0), rf=k.foot(R, 0.42, toe=-4),
                          lf=k.foot(L, -0.3, toe=-24), face="angry", vis="a"), fx_trail=1.0, fx_spark=1.0, fx_burst=1.0, fx_dust=1.0)
    add(_seq("one_time_pad", 11, 60, False, [(0.0, guard), (0.14, high), (0.26, higher), (0.34, pad_hit),
                                             (0.5, _x(k.crouch(0.16, lean=30, rh=pole(0.72, 0.88, -58.0)), fx_spark=0.3)),
                                             (0.78, k.crouch(0.1, lean=18, rh=pole(0.6, 0.7, -20.0))), (1.0, guard)], cat="special"))
    # Key exchange: she crosses the gap low and fast, and arrives agreed.
    cross = _x(ready(root=(0.09, -0.12, 0.0), lean=34, head=(-10.0, 0.0), rh=pole(1.0, 0.45, 2.0), rf=k.foot(R, 0.5, 0.04, toe=-8),
                     lf=k.foot(L, -0.42, 0.12, toe=-36), face="angry"), fx_speed=1.0, fx_trail=1.0)
    add(_seq("key_exchange", 10, 58, False, [(0.0, guard), (0.18, _x(k.crouch(0.14, lean=22, rh=pole(0.2, 0.62, 10.0), face="determined"),
                                                                     fx_speed=0.3)),
                                             (0.3, cross), (0.4, _x(cross, fx_spark=1.0, fx_key=1.0)),
                                             (0.62, _x(ready(root=(0.06, -0.08, 0.0), lean=18, rh=pole(0.9, 0.48, -4.0)), fx_key=0.6, fx_spark=0.0)),
                                             (1.0, guard)], cat="special"))
    # Elliptic curve: a rising cut, then she drops feet first into the
    # portal the game opens under her (the game draws the portal, never her
    # sheet).
    drop = k.air(lean=-4, head=(-6.0, 0.0), rh=pole(0.15, -0.9, 92.0, pole_=(0.6, 0.2, -0.6)), lh=k.hand(L, 0.0, -0.75, 0.3, pole=(0.6, 0.2, -0.6)),
                 rf=k.bfoot(R, 0.05, 0.98, toe=-20), lf=k.bfoot(L, -0.02, 0.98, toe=-20), face="determined")
    add(_seq("elliptic_curve", 9, 53, False, [(0.0, guard), (0.14, k.crouch(0.18, lean=14, rh=pole(0.5, 0.75, -20.0), face="angry")),
                                              (0.34, _x(k.pose(root=(0.0, 0.04, 0.0), lean=-8, head=(-22.0, 0.0),
                                                               rh=pole(0.25, -0.95, 100.0, pole_=(0.6, 0.2, -0.6)), rf=k.foot(R, 0.04, 0.06, toe=30),
                                                               lf=k.foot(L, -0.06, 0.1, toe=30), face="angry"), fx_trail=1.0, fx_spark=1.0)),
                                              (0.6, drop), (1.0, replace(drop, lean=-2.0))], cat="special"))
    # Hash collision: two pins driven into the floor, one either side of
    # her, then the one output: a rising blow that launches.
    lifted = k.pose(lean=-4, rh=pole(0.4, -0.2, 84.0, pole_=(0.5, 0.3, -0.6)), face="determined")
    pin_front = _x(k.crouch(0.16, lean=20, rh=pole(0.6, 0.8, -84.0, two=18.0)), fx_pin=1.0, fx_dust=0.8)
    pin_back = _x(k.crouch(0.16, lean=0, side=-4, rh=pole(-0.35, 0.78, -100.0, two=18.0, pole_=(0.8, 0.4, -0.3))), fx_pin=1.0, fx_dust=0.8)
    launch = _x(k.pose(root=(0.02, 0.02, 0.0), lean=-8, head=(-18.0, 0.0), rh=pole(0.3, -0.92, 96.0, pole_=(0.6, 0.2, -0.6)), face="angry",
                       vis="a"), fx_trail=1.0, fx_spark=1.0, fx_burst=1.0)
    add(_seq("hash_collision", 11, 60, False, [(0.0, guard), (0.14, lifted), (0.24, pin_front), (0.31, lifted), (0.38, pin_back),
                                               (0.46, k.crouch(0.2, lean=12, rh=pole(0.4, 0.8, -40.0), face="angry")), (0.55, launch),
                                               (0.72, _x(k.pose(lean=-10, rh=pole(-0.05, -0.86, 120.0, pole_=(0.6, 0.2, -0.6))), fx_spark=0.3)),
                                               (1.0, guard)], cat="special"))
    # Collision dive: in the air, she arrives at the output point first.
    dive = _x(air(spin=24.0, lean=18.0, head=(18.0, 0.0), rh=pole(0.35, 0.95, -86.0), rf=k.bfoot(R, -0.05, 0.95), lf=k.bfoot(L, -0.1, 0.92),
                  face="angry"), fx_speed=1.0, fx_trail=1.0)
    add(_seq("collision_dive", 8, 54, False, [(0.0, hang), (0.2, air(lean=-6.0, rh=pole(0.25, -0.55, 92.0, pole_=(0.6, 0.2, -0.6)),
                                                                     rf=k.bfoot(R, 0.35, 0.5), lf=k.bfoot(L, 0.3, 0.55))),
                                              (0.42, _x(dive, fx_spark=1.0)), (1.0, _x(replace(dive, spin=26.0), fx_spark=0.4))], cat="special"))

    # ---- ranged and gathering ----------------------------------------------------------------------
    sight = _x(ready(root=(0.0, -0.03, 0.0), lean=4.0, head=(2.0, 0.0), rh=pole(0.78, -0.02, 0.0, two=30.0)), fx_aim=1.0)
    add(_seq("aim", 6, 100, True, _cycle([sight, _x(replace(sight, lean=4.6), fx_aim=0.9)]), cat="ranged"))
    recoil = _x(ready(root=(-0.02, -0.03, 0.0), lean=-2.0, head=(0.0, 0.0), rh=pole(0.62, 0.0, 10.0, two=30.0), vis="o"), fx_dart=1.0, fx_aim=0.3)
    add(_seq("shoot", 6, 58, False, [(0.0, sight), (0.3, _x(sight, fx_dart=0.6)), (0.5, recoil), (1.0, sight)], cat="ranged"))
    gather = _x(k.pose(root=(0.0, -0.02, 0.0), lean=-4, head=(-6.0, 0.0), rh=pole(0.45, 0.25, 84.0, two=26.0), face="determined", vis="m"),
                fx_charge=1.0)
    add(_seq("charge", 8, 76, True, _cycle([gather, _x(replace(gather, lean=-6.0), fx_charge=0.8)]), cat="ranged"))
    add(_seq("cast", 8, 80, False, [(0.0, at_ease()), (0.35, gather),
                                    (0.55, _x(ready(root=(0.04, -0.04, 0.0), lean=14, rh=pole(0.95, 0.05, 30.0), face="angry", vis="a"), fx_cast=1.0)),
                                    (0.8, _x(ready(lean=10, rh=pole(0.85, 0.15, 24.0)), fx_cast=0.5)), (1.0, at_ease())], cat="ranged"))

    # ---- the blink: plain poses, the game takes her body apart --------------------------------------
    gone = _x(k.crouch(0.08, lean=16, head=(-8.0, 0.0), rh=carry(0.1, 0.65, 60.0), lh=k.hand(L, 0.35, 0.3, 0.1), face="determined"), fx_blink=1.0)
    add(_seq("blink_out", 6, 58, False, [(0.0, _x(at_ease(), fx_blink=0.0)), (0.45, _x(gone, fx_blink=0.6)), (1.0, gone)], cat="special"))
    add(_seq("blink_in", 6, 58, False, [(0.0, gone), (0.55, _x(gone, fx_blink=0.6)), (1.0, _x(at_ease(), fx_blink=0.0))], cat="special"))

    # ---- show ---------------------------------------------------------------------------------------
    hop = k.pose(root=(0.0, 0.05, 0.0), lean=-6, head=(-14.0, 0.0), rh=carry(0.2, -0.9, 90.0, 0.2), lh=k.hand(L, 0.3, 0.3, 0.4),
                 rf=k.foot(R, 0.05, 0.12, toe=30), lf=k.foot(L, -0.05, 0.1, toe=30), face="happy", vis="a")
    add(_seq("celebrate", 8, 92, False, [(0.0, at_ease()), (0.18, k.crouch(0.1, face="happy")), (0.38, hop),
                                         (0.6, replace(hop, root=(0.0, 0.0, 0.0), lean=-4.0)), (0.8, replace(hop, root=(0.0, 0.0, 0.0), lean=-3.0)),
                                         (1.0, k.pose(rh=carry(0.2, -0.85, 90.0, 0.2), face="happy", vis="e"))], view="front_3q", cat="social"))
    twirl = []
    for i in range(7):
        th = 90.0 + 360.0 * i / 6.0
        r = math.radians(th)
        twirl.append((0.1 + 0.55 * i / 6.0, _x(k.pose(lean=-2, rh=pole(0.45 + 0.25 * math.cos(r), 0.2 - 0.25 * math.sin(r), th, two=0.0,
                                                                         pole_=(0.4, 0.5, -0.6)), face="smug"), fx_whirl=0.8)))
    add(_seq("taunt", 10, 90, False, [(0.0, at_ease())] + twirl + [(0.82, k.pose(rh=carry(-0.08, 0.74, 88.0, 0.27), face="smug", vis="e")),
                                                                     (1.0, at_ease(face="smug"))], view="front_3q", cat="social"))

    # ---- the pole is put away where both hands are busy ---------------------------------------------
    for name in POLE_AWAY:
        c = out[name]
        out[name] = replace(c, keys=[(t, _x(p, prop_staff=0.0)) for t, p in c.keys])
    return out


__all__ = ["CONTRACT_ROWS", "MOVESET_ROWS", "POLE_AWAY", "ROWS", "alice_library"]
