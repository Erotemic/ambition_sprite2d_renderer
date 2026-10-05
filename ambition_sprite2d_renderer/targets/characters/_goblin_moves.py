"""The goblin's moveset, as key poses.

``pose(animation, t)`` is the goblin's pose at clip time ``t`` (``i / n`` for
a loop, ``i / (n - 1)`` for a one-shot) as a dict of the generator's pose
fields; ``goblin_side.SideGoblinGenerator`` lays the drawing out from it.
Nothing here draws.

⭐ THE POSE FIELDS, in the goblin's 128-unit frame (y down, the goblin faces
+x, a positive angle turns clockwise on screen):

``x``, ``y``          the whole goblin's offset (``y`` < 0 is up)
``spin``             the whole goblin turned about its body (a forward flip
                     runs positive)
``bx``, ``by``       the body's offset from where it sits on the hips' line
                     (``by`` > 0 squats it down, the legs folding under it)
``tilt``             the body egg's lean (positive: forward)
``hx``, ``hy``       the head's offset from its usual perch
``head``             the head's tilt (positive: chin down, forward)
``nu``, ``nl``       the near (weapon) arm's upper / lower WORLD angles
                     (0 forward, 90 hanging, -90 straight up, 180 back)
``fu``, ``fl``       the far arm's
``wa``               the weapon's world angle (it points along it from the
                     fist); ``wpn`` 0 stows it
``fz``               1 draws the far arm in front of the body (a grab)
``nleg``, ``fleg``   a leg: ``("g", x, lift)`` its foot planted at ``x``
                     from the frame's centre line, ``lift`` off the ground
                     (the knee found by IK), or ``("a", upper, lower)``
                     thigh and shin world angles (tucked in the air)
``blink``, ``squint``, ``dead``, ``mouth`` (0 shut .. 1 gaping)
``fx.*``             effect strengths (``trail``, ``spark``, ``dust``,
                     ``shock``, ``speed``, ``shield``, ``hit``, ``stars``,
                     ``zzz``, ``rock``, ``sand``, ``charge``, ``mound``)

A move is a list of ``(t, changes)`` keys (each snapped onto the nearest
drawn frame); each key says only what changes
(``"ease"``: ``io`` smooth, ``out`` fast-then-settle, ``in`` slow-then-snap,
``lin``, ``hold``). Swings are written like Bob's: anticipation, one snapping
frame, a held contact frame, follow-through, recovery. A goblin swings
wilder, recovers faster and cackles while it does it.
"""

from __future__ import annotations

import math
from functools import lru_cache
from typing import Callable, Dict, List, Sequence, Tuple, Union

from ._goblin_motion import GOBLIN_LOOPS, GOBLIN_ROWS

Leg = Tuple[str, float, float]
Value = Union[float, bool, Leg]
Pose = Dict[str, Value]
TAU = math.tau


def g(x: float, lift: float = 0.0) -> Leg:
    return ("g", float(x), float(lift))


def a(upper: float, lower: float) -> Leg:
    return ("a", float(upper), float(lower))


FX = ("trail", "spark", "dust", "shock", "speed", "shield", "hit", "stars", "zzz", "rock", "sand", "charge",
      "mound", "flash")

#: The goblin's fighting stance: hunched over its knees, weapon up and
#: forward, the far fist tucked at its belly.
STANCE: Pose = {
    "x": 0.0, "y": 0.0, "spin": 0.0, "bx": 0.0, "by": 3.0, "tilt": 8.0, "hx": 1.0, "hy": 1.0, "head": 4.0, "fz": 0.0,
    "nu": 22.0, "nl": -8.0, "wa": -38.0, "wpn": 1.0, "fu": 118.0, "fl": 64.0,
    "nleg": g(14.0), "fleg": g(-9.0),
    "blink": False, "squint": 0.12, "dead": False, "mouth": 0.0,
    **{f"fx.{k}": 0.0 for k in FX},
}


def S(**over) -> Pose:
    out = dict(STANCE)
    for k, v in over.items():
        out[k.replace("__", ".")] = v
    return out


#: Squatting low.
CROUCH = S(by=12.0, tilt=18.0, head=10.0, hy=3.0, nu=40.0, nl=0.0, wa=-12.0, nleg=g(16.0), fleg=g(-12.0))
#: In the air: knees up.
AIR = S(y=-4.0, by=0.0, tilt=4.0, head=0.0, nleg=a(10.0, 100.0), fleg=a(40.0, 130.0), nu=0.0, nl=-20.0, wa=-50.0,
        fu=150.0, fl=110.0)
#: Flat on its back (head toward -x).
ON_BACK = S(x=6.0, y=20.0, spin=-90.0, by=0.0, tilt=0.0, head=-80.0, hx=0.0, hy=0.0, nu=40.0, nl=30.0, wa=10.0,
            fu=20.0, fl=10.0, nleg=a(-10.0, 0.0), fleg=a(-20.0, -6.0), squint=0.6, mouth=0.6)
#: Flat on its face (head toward +x).
ON_FRONT = S(x=-8.0, y=6.0, spin=90.0, by=0.0, tilt=0.0, head=70.0, nu=110.0, nl=40.0, wa=10.0, fu=150.0,
             fl=140.0, nleg=a(170.0, 180.0), fleg=a(160.0, 170.0), squint=0.7, mouth=0.4)
#: Hanging off a ledge up ahead by both hands, weapon in its teeth... in its fist.
HANG = S(x=-6.0, y=8.0, by=0.0, tilt=-6.0, head=-10.0, nu=-70.0, nl=-60.0, wa=-10.0, fu=-80.0, fl=-70.0,
         nleg=a(100.0, 90.0), fleg=a(80.0, 100.0))
#: Guarding behind the weapon, low.
GUARD = S(by=8.0, tilt=-6.0, head=-6.0, nu=-10.0, nl=-70.0, wa=-95.0, fu=150.0, fl=-160.0, squint=0.3,
          nleg=g(15.0), fleg=g(-12.0), **{"fx__shield": 1.0})

EASES: Dict[str, Callable[[float], float]] = {
    "io": lambda u: u * u * (3.0 - 2.0 * u),
    "out": lambda u: 1.0 - (1.0 - u) ** 2.2,
    "in": lambda u: u ** 2.2,
    "lin": lambda u: u,
    "hold": lambda u: 1.0 if u >= 1.0 else 0.0,
}

Key = Tuple[float, Pose]


def _norm(k: Pose) -> Pose:
    return {name.replace("__", "."): v for name, v in k.items()}


def lerp_pose(p: Pose, q: Pose, u: float) -> Pose:
    out: Pose = {}
    for name in set(p) | set(q):
        va, vb = p.get(name, q.get(name)), q.get(name, p.get(name))
        if isinstance(va, tuple) and isinstance(vb, tuple):
            if va[0] == vb[0]:
                out[name] = (va[0],) + tuple(x + (y - x) * u for x, y in zip(va[1:], vb[1:]))
            else:
                # Mixed leg modes blend in the layout, which can place both.
                out[name] = ("mix", va, vb, u)
        elif isinstance(va, (bool, str)) or isinstance(vb, (bool, str)):
            out[name] = vb if u >= 1.0 else va
        else:
            out[name] = float(va) + (float(vb) - float(va)) * u
    return out


def keyed(keys: Sequence[Key], base: Pose = STANCE, extra=None) -> Callable[[float], Pose]:
    resolved: List[Tuple[float, Pose, str]] = []
    cur = dict(base)
    for t, k in keys:
        k = _norm(k)
        cur = {**cur, **{n: v for n, v in k.items() if n != "ease"}}
        resolved.append((t, dict(cur), str(k.get("ease", "io"))))

    def fn(t: float) -> Pose:
        if t <= resolved[0][0]:
            p = dict(resolved[0][1])
        else:
            p = dict(resolved[-1][1])
            for (t0, a0, _e), (t1, b1, ease) in zip(resolved, resolved[1:]):
                if t <= t1:
                    u = 0.0 if t1 <= t0 else (t - t0) / (t1 - t0)
                    p = lerp_pose(a0, b1, EASES[ease](u))
                    break
        if extra is not None:
            extra(t, p)
        return p

    return fn


def loop(fn: Callable[[float], Pose]) -> Callable[[float], Pose]:
    return fn


def step(phase: float, centre: float, stride: float, lift: float) -> Leg:
    """A planted-then-swinging foot at gait ``phase``."""
    p = phase % 1.0
    if p < 0.5:
        return g(centre + stride * (1.0 - 4.0 * p), 0.0)
    s = (p - 0.5) / 0.5
    return g(centre - stride + 2.0 * stride * (s * s * (3 - 2 * s)), lift * math.sin(math.pi * s))


def body_arms(t: float, p: Pose) -> None:
    """Arms (and the weapon) keyed in the body's frame: they turn with a spin."""
    for k in ("nu", "nl", "wa", "fu", "fl"):
        p[k] = float(p[k]) + float(p.get("spin", 0.0))


# --- loops --------------------------------------------------------------------------------

W = TAU


def idle(t: float) -> Pose:
    """Jittery: bouncing on its toes, head darting, the blade twitching."""
    w = W * t
    dart = 1.0 if 0.375 <= t < 0.625 else 0.0
    return S(by=3.0 + 1.6 * abs(math.sin(w)), tilt=8.0 + 2.0 * math.sin(w), head=4.0 - 8.0 * dart + 2.0 * math.sin(2 * w),
             hx=1.0 + 1.5 * dart, nu=22.0 + 4.0 * math.sin(w + 1.0), nl=-8.0 + 6.0 * math.sin(w + 1.4),
             wa=-38.0 + 10.0 * math.sin(w + 1.8), fu=118.0 + 4.0 * math.sin(w), blink=0.75 <= t < 0.875,
             squint=0.12 + 0.1 * dart)


def walk(t: float) -> Pose:
    """A sneaky, bow-legged creep with the blade held low and ready."""
    w = W * t
    p = S(by=2.0 + 1.6 * (1 - math.cos(2 * w)), tilt=12.0 + 2.0 * math.sin(w), head=6.0 - 2.0 * math.cos(2 * w),
          x=0.8 * math.sin(w), nu=30.0 - 10.0 * math.sin(w), nl=0.0 - 6.0 * math.sin(w), wa=-28.0 - 8.0 * math.sin(w),
          fu=120.0 + 14.0 * math.sin(w), fl=80.0 + 10.0 * math.sin(w), squint=0.18)
    p["nleg"] = step(t, 4.0, 10.0, 6.0)
    p["fleg"] = step(t + 0.5, 0.0, 10.0, 6.0)
    return p


def run(t: float) -> Pose:
    """Scampering on its toes, head down, blade trailing, far arm pumping."""
    w = W * t
    p = S(y=-1.5 * (1 - math.cos(2 * w)), by=4.0, tilt=24.0, head=14.0, hx=2.0, x=1.0 * math.sin(w),
          nu=150.0 + 12.0 * math.sin(w), nl=170.0, wa=176.0, fu=60.0 - 50.0 * math.sin(w), fl=-10.0 - 30.0 * math.sin(w),
          squint=0.3, mouth=0.3)
    p["nleg"] = step(t, 6.0, 14.0, 9.0)
    p["fleg"] = step(t + 0.5, 2.0, 14.0, 9.0)
    return p


def dash(t: float) -> Pose:
    w = W * t
    p = run(t)
    p.update({"tilt": 32.0, "head": 18.0, "y": -2.0 * (1 - math.cos(2 * w)), "fx.speed": 1.0, "mouth": 0.6})
    p["nleg"] = step(t, 8.0, 17.0, 10.0)
    p["fleg"] = step(t + 0.5, 4.0, 17.0, 10.0)
    return p


def talk(t: float) -> Pose:
    """Conspiratorial: hunched, rubbing its hands, jaw flapping."""
    w = W * t
    return S(by=4.0, tilt=12.0 + 2.0 * math.sin(w), head=-2.0 + 5.0 * math.sin(2 * w), nu=60.0 + 10.0 * math.sin(2 * w),
             nl=-30.0 + 20.0 * math.sin(2 * w), wa=-70.0, fu=60.0 - 10.0 * math.sin(2 * w), fl=0.0, wpn=1.0,
             mouth=0.6 if (t * 4.0) % 1.0 < 0.5 else 0.1, squint=0.3)


def interact(t: float) -> Pose:
    """Rummaging: poking at something on the ground with the blade."""
    w = W * t
    return S(by=8.0, tilt=26.0, head=16.0, hx=2.0, nu=60.0, nl=40.0 + 16.0 * math.sin(2 * w), wa=60.0 + 16.0 * math.sin(2 * w),
             fu=80.0, fl=50.0 + 10.0 * math.sin(w), squint=0.2, mouth=0.2 + 0.2 * max(0.0, math.sin(2 * w)))


def block(t: float) -> Pose:
    w = W * t
    return {**GUARD, "by": 8.0 + 0.8 * math.sin(w), "fx.shield": 0.92 + 0.08 * math.sin(2 * w)}


def crouch(t: float) -> Pose:
    w = W * t
    return {**CROUCH, "by": 12.0 + 0.8 * math.sin(w), "head": 10.0 + 2.0 * math.sin(w - 0.5),
            "blink": 0.65 <= t < 0.8}


def crouch_walk(t: float) -> Pose:
    w = W * t
    p = {**CROUCH, "tilt": 22.0, "by": 11.0 + 1.0 * (1 - math.cos(2 * w)), "x": 0.5 * math.sin(w)}
    p["nleg"] = step(t, 6.0, 7.0, 3.0)
    p["fleg"] = step(t + 0.5, -2.0, 7.0, 3.0)
    return p


def fall(t: float) -> Pose:
    """Flailing on the way down."""
    w = W * t
    return {**AIR, "y": -2.0, "tilt": -4.0, "head": -12.0, "nu": -60.0 + 20.0 * math.sin(w), "nl": -90.0 + 20.0 * math.sin(w),
            "wa": -110.0 + 20.0 * math.sin(w), "fu": -110.0 - 20.0 * math.sin(w + 1.5), "fl": -140.0 - 20.0 * math.sin(w + 1.5),
            "nleg": a(70.0 + 10.0 * math.sin(w), 120.0), "fleg": a(100.0 - 10.0 * math.sin(w), 70.0),
            "mouth": 0.7, "squint": 0.0}


def fall_special(t: float) -> Pose:
    w = W * t
    p = fall(t)
    p.update({"spin": 10.0 * math.sin(w), "head": -20.0, "dead": False, "squint": 0.6, "mouth": 0.9,
              "fx.stars": 0.7})
    return p


def tumble(t: float) -> Pose:
    s = -360.0 * t
    p = {**AIR, "spin": s, "nu": s - 120.0, "nl": s - 150.0, "wa": s - 160.0, "fu": s - 60.0, "fl": s - 40.0,
         "nleg": a(s + 40.0, s + 90.0), "fleg": a(s + 120.0, s + 160.0), "mouth": 0.8, "squint": 0.7}
    return p


def teeter(t: float) -> Pose:
    w = W * t
    return S(tilt=26.0 + 8.0 * math.sin(w), head=20.0, hx=3.0, nu=-80.0 + 60.0 * math.sin(2 * w), nl=-110.0 + 60.0 * math.sin(2 * w),
             wa=-120.0 + 60.0 * math.sin(2 * w), fu=-100.0 - 60.0 * math.sin(2 * w + 1.4), fl=-130.0 - 60.0 * math.sin(2 * w + 1.4),
             nleg=g(10.0, 4.0 + 3.0 * math.sin(w + 1.0)), fleg=g(-6.0), mouth=0.8, squint=0.0)


def prone(t: float) -> Pose:
    w = W * t
    return {**ON_BACK, "y": 20.0 - 0.6 * math.sin(w), "head": -80.0 + 3.0 * math.sin(w)}


def dizzy(t: float) -> Pose:
    w = W * t
    return S(x=2.0 * math.sin(w), by=3.0 + 1.5 * math.sin(2 * w), tilt=6.0 + 12.0 * math.sin(w), head=10.0 * math.sin(w + 1.0),
             nu=90.0, nl=100.0, wa=110.0, fu=100.0, fl=110.0, squint=0.5, mouth=0.6, **{"fx__stars": 1.0})


def sleep(t: float) -> Pose:
    w = W * t
    return S(by=14.0, tilt=36.0 + 2.0 * math.sin(w), head=30.0 + 3.0 * math.sin(w), hy=4.0, nu=80.0, nl=40.0, wa=20.0,
             fu=70.0, fl=40.0, blink=True, mouth=0.5 + 0.3 * math.sin(w), nleg=g(16.0), fleg=g(-12.0),
             **{"fx__zzz": t})


def buried(t: float) -> Pose:
    w = W * t
    return S(y=22.0, by=0.0, tilt=0.0, head=6.0 * math.sin(w), nu=-40.0 + 20.0 * math.sin(2 * w), nl=-80.0,
             wa=-100.0, fu=-130.0 - 20.0 * math.sin(2 * w), fl=-100.0, nleg=a(-60.0, 90.0), fleg=a(-40.0, 100.0),
             mouth=0.7, squint=0.5, **{"fx__mound": 1.0})


def smash_charge(t: float) -> Pose:
    """Coiled back with the weapon raised, quivering, a glint building."""
    w = W * t
    return S(x=-3.0 + 0.6 * math.sin(3 * w), by=7.0 + 0.6 * math.sin(5 * w), tilt=-12.0, head=-10.0, nu=-120.0, nl=-150.0,
             wa=-165.0 + 6.0 * math.sin(4 * w), fu=40.0, fl=20.0, nleg=g(18.0), fleg=g(-14.0), squint=0.6, mouth=0.5,
             **{"fx__charge": 0.7 + 0.3 * math.sin(2 * w)})


def grab_hold(t: float) -> Pose:
    w = W * t
    return {**GRAB_HOLD, "by": 5.0 + 0.8 * math.sin(w), "mouth": 0.4 + 0.3 * math.sin(2 * w)}


#: Clutching a grabbed foe in its far fist, blade cocked back.
GRAB_HOLD = S(by=5.0, tilt=14.0, head=8.0, fz=1.0, fu=0.0, fl=-6.0, nu=150.0, nl=-150.0, wa=-140.0, squint=0.4, mouth=0.4,
              nleg=g(16.0), fleg=g(-12.0))


def grabbed(t: float) -> Pose:
    w = W * t
    return S(y=-8.0, by=0.0, tilt=-14.0, head=-16.0, nu=-60.0 + 30.0 * math.sin(2 * w), nl=-100.0, wa=-120.0,
             fu=-90.0 - 30.0 * math.sin(2 * w), fl=-130.0, nleg=a(80.0 + 25.0 * math.sin(2 * w), 100.0),
             fleg=a(100.0 - 25.0 * math.sin(2 * w), 90.0), mouth=0.8, squint=0.6)


def ledge_grab(t: float) -> Pose:
    w = W * t
    return {**HANG, "nleg": a(100.0 + 10.0 * math.sin(w), 90.0), "fleg": a(80.0 - 10.0 * math.sin(w), 100.0)}


def item_hold(t: float) -> Pose:
    w = W * t
    return S(by=3.0 + 1.0 * math.sin(w), fz=1.0, fu=20.0, fl=-20.0, nu=150.0, nl=-150.0, wa=-140.0)


def item_heavy_carry(t: float) -> Pose:
    w = W * t
    p = S(by=6.0 + 1.5 * (1 - math.cos(2 * w)), tilt=-6.0, head=-6.0, nu=-80.0, nl=-60.0, wa=-90.0, wpn=0.0,
          fu=-90.0, fl=-70.0, mouth=0.5, squint=0.6)
    p["nleg"] = step(t, 6.0, 6.0, 3.0)
    p["fleg"] = step(t + 0.5, -2.0, 6.0, 3.0)
    return p


def victory_hold(t: float) -> Pose:
    w = W * t
    return S(by=1.0 + 1.0 * math.sin(w), tilt=-8.0, head=-14.0, nu=-80.0, nl=-90.0, wa=-90.0 + 6.0 * math.sin(2 * w),
             fu=150.0, fl=60.0, mouth=0.9, squint=0.4)


def loss(t: float) -> Pose:
    """Sulking: slumped, kicking at the dirt."""
    w = W * t
    return S(by=6.0, tilt=24.0, head=30.0, hy=3.0, nu=90.0, nl=60.0, wa=40.0, fu=95.0, fl=90.0, squint=0.5,
             nleg=g(14.0 + 4.0 * max(0.0, math.sin(w)), 3.0 * max(0.0, math.sin(w))), fleg=g(-9.0), mouth=0.0)


# --- one-shot moves ---------------------------------------------------------------------

HOME = S()

MOVES: Dict[str, Callable[[float], Pose]] = {}
_FRAMES: Dict[str, int] = {name: n for name, n, _ms in GOBLIN_ROWS}


def _snap(name: str, keys: Sequence[Key]) -> List[Key]:
    """Each key moved onto the nearest drawn frame (frame ``i`` of ``n`` is at
    ``i / (n - 1)``), keeping them in order, so a contact pose is drawn, not
    interpolated past."""
    n = _FRAMES[name]
    out: List[Key] = []
    last = -1
    for t, k in keys:
        i = max(last + 1, int(round(t * (n - 1))))
        last = i
        out.append((min(1.0, i / max(1, n - 1)), k))
    return out


def _move(name: str, keys: Sequence[Key], base: Pose = STANCE, extra=None) -> None:
    MOVES[name] = keyed(_snap(name, keys), base, extra)


# Legacy rows, re-authored.
_move("jump", [
    (0.0, {**CROUCH, "by": 12.0, "fx__dust": 1.0}),
    (0.2, {"y": -4.0, "by": -2.0, "tilt": -6.0, "head": -10.0, "nleg": a(100.0, 110.0), "fleg": a(110.0, 120.0),
           "nu": -40.0, "nl": -40.0, "wa": -70.0, "fu": -110.0, "fl": -120.0, "mouth": 0.6, "fx__dust": 0.3,
           "ease": "out"}),
    (0.6, {"y": -6.0, "by": 0.0, "tilt": 4.0, "head": -2.0, "nleg": a(10.0, 100.0), "fleg": a(40.0, 130.0),
           "nu": 0.0, "nl": -20.0, "wa": -50.0, "fu": 150.0, "fl": 110.0, "mouth": 0.2, "fx__dust": 0.0}),
    (1.0, AIR),
])
_move("slash", [
    (0.0, {}),
    (0.167, {"x": -2.0, "tilt": -10.0, "head": -6.0, "nu": -110.0, "nl": -150.0, "wa": -170.0, "fu": 60.0, "fl": 20.0,
             "squint": 0.4, "mouth": 0.4, "ease": "out"}),
    (0.333, {"x": 4.0, "by": 5.0, "tilt": 22.0, "head": 10.0, "nu": 30.0, "nl": 40.0, "wa": 55.0, "fu": 160.0,
             "fl": 120.0, "nleg": g(20.0), "mouth": 0.9, "fx__trail": 1.0, "fx__spark": 1.0, "ease": "in"}),
    (0.5, {"nu": 40.0, "nl": 55.0, "wa": 70.0, "fx__trail": 0.0, "fx__spark": 0.4, "ease": "out"}),
    (1.0, HOME),
])
_move("hit", [
    (0.0, {}),
    (0.25, {"x": -5.0, "by": 3.0, "tilt": -20.0, "head": -24.0, "hx": -2.0, "nu": -40.0, "nl": -90.0, "wa": -130.0,
            "fu": -120.0, "fl": -150.0, "nleg": g(18.0, 2.0), "squint": 0.8, "mouth": 1.0, "fx__hit": 1.0,
            "ease": "out"}),
    (0.5, {"x": -4.0, "tilt": -14.0, "head": -16.0, "fx__hit": 0.2}),
    (1.0, {**HOME, "x": -2.0}),
])
_move("death", [
    (0.0, {"fx__hit": 1.0}),
    (0.14, {"x": -5.0, "tilt": -20.0, "head": -26.0, "nu": -60.0, "nl": -100.0, "wa": -140.0, "fu": -120.0, "fl": -150.0,
            "squint": 0.9, "mouth": 1.0, "fx__hit": 0.4, "ease": "out"}),
    (0.43, {"x": -2.0, "by": 10.0, "tilt": 20.0, "head": 24.0, "nu": 90.0, "nl": 50.0, "wa": 30.0, "fu": 100.0,
            "fl": 110.0, "nleg": g(16.0), "fleg": g(-12.0), "fx__hit": 0.0, "dead": True}),
    (0.71, {**ON_FRONT, "y": 3.0, "dead": True, "fx__dust": 1.0, "ease": "in"}),
    (0.86, {**ON_FRONT, "y": 5.0, "head": 76.0, "dead": True, "fx__dust": 0.4}),
    (1.0, {**ON_FRONT, "dead": True, "wpn": 1.0}),
])
_move("blink_out", [
    (0.0, {}),
    (0.46, {"x": -2.0, "by": 8.0, "tilt": -15.0, "head": 11.0, "fu": 166.0, "fl": 170.0, "nu": -10.0, "nl": -20.0,
            "nleg": g(18.0), "fleg": g(-14.0), "squint": 0.4}),
    (1.0, {"x": -4.0, "y": -2.0, "by": 6.0, "tilt": -26.0, "head": 14.0, "fu": 186.0, "fl": 188.0, "nu": -16.0,
           "nl": -24.0, "squint": 0.5}),
])
_move("blink_in", [
    (0.0, {"x": 4.8, "y": 1.8, "by": 6.0, "tilt": 16.0, "head": -10.0, "fu": 184.0, "fl": 176.0, "nu": 34.0, "nl": 26.0,
           "squint": 0.46}),
    (0.6, {"x": 0.6, "y": 0.0, "by": 4.0, "tilt": 4.0, "head": 2.0, "squint": 0.3, "ease": "out"}),
    (1.0, HOME),
])
_move("celebrate", [
    (0.0, {}),
    (0.14, {**CROUCH, "mouth": 0.6}),
    (0.43, {"y": -4.0, "by": -2.0, "tilt": -10.0, "head": -16.0, "nu": -60.0, "nl": -40.0, "wa": -80.0, "fu": -100.0,
            "fl": -110.0, "nleg": a(110.0, 60.0), "fleg": a(70.0, 120.0), "mouth": 1.0, "squint": 0.5, "ease": "out"}),
    (0.71, {"y": 0.0, "by": 4.0, "tilt": 0.0, "head": -10.0, "nleg": g(14.0), "fleg": g(-9.0), "wa": -60.0,
            "fx__dust": 0.6, "ease": "in"}),
    (1.0, {**victory_hold(0.0), "fx__dust": 0.0}),
])

# Locomotion.
_move("walk_stop", [
    (0.0, {**walk(0.25)}),
    (0.25, {"x": 2.0, "by": 6.0, "tilt": -8.0, "head": -6.0, "nleg": g(18.0), "fleg": g(-12.0, 2.0), "fx__dust": 1.0,
            "ease": "out"}),
    (1.0, HOME),
])
_move("turnaround", [
    (0.0, {}),
    (0.25, {"by": 8.0, "tilt": -16.0, "head": -12.0, "nu": 160.0, "nl": 170.0, "wa": 175.0, "fu": 60.0, "fl": 30.0,
            "nleg": g(20.0, 0.0), "fleg": g(-6.0, 4.0), "ease": "out"}),
    (0.5, {"y": -4.0, "by": 2.0, "tilt": 0.0, "nleg": g(12.0, 4.0), "fleg": g(-6.0, 0.0), "fx__dust": 0.8}),
    (1.0, HOME),
])
_move("dash_startup", [
    (0.0, {}),
    (0.33, {"by": 10.0, "tilt": 14.0, "nleg": g(12.0), "fleg": g(-14.0), "ease": "out"}),
    (1.0, {**dash(0.0), "fx__dust": 1.0, "ease": "in"}),
])
_move("stumble", [
    (0.0, {}),
    (0.2, {"x": 3.0, "tilt": 30.0, "head": 20.0, "nu": -60.0, "nl": -90.0, "wa": -100.0, "fu": -80.0, "fl": -120.0,
           "nleg": g(24.0, 4.0), "fleg": g(-10.0, 3.0), "mouth": 1.0, "squint": 0.0}),
    (0.4, {"x": 5.0, "by": 6.0, "tilt": 40.0, "nu": 60.0, "nl": 20.0, "wa": 10.0, "fu": -140.0, "fl": -170.0,
           "nleg": g(28.0), "fleg": g(0.0, 6.0)}),
    (0.6, {"x": 3.0, "tilt": 16.0, "head": 4.0, "nleg": g(20.0), "fleg": g(-4.0), "nu": 30.0, "nl": 0.0, "wa": -20.0,
           "fu": 120.0, "fl": 70.0, "mouth": 0.3}),
    (1.0, HOME),
])
_move("crouch_start", [(0.0, {}), (0.5, {**CROUCH, "by": 14.0, "ease": "out"}), (1.0, CROUCH)])
_move("crouch_end", [(0.0, CROUCH), (0.5, {**CROUCH, "by": 8.0}), (1.0, HOME)])
_move("jump_squat", [(0.0, {}), (0.5, {**CROUCH, "by": 15.0, "tilt": 10.0, "ease": "out"}),
                     (1.0, {**CROUCH, "by": 13.0, "nu": -40.0, "nl": -60.0, "wa": -90.0})])
_move("double_jump", [
    (0.0, {**AIR}),
    (0.15, {"y": -6.0, "nleg": a(-20.0, 60.0), "fleg": a(10.0, 80.0), "nu": -10.0, "nl": 20.0, "wa": 0.0, "ease": "in"}),
    (0.7, {"spin": 330.0, "ease": "lin"}),
    (1.0, {"spin": 360.0, "nleg": a(10.0, 100.0), "fleg": a(40.0, 130.0), "nu": 0.0, "nl": -20.0, "wa": -50.0,
           "ease": "out"}),
], base=AIR, extra=lambda t, p: (body_arms(t, p), _spin_legs(p)))
_move("land", [
    (0.0, {**AIR}),
    (0.33, {**CROUCH, "by": 14.0, "fx__dust": 1.0, "ease": "out"}),
    (1.0, {**HOME, "fx__dust": 0.0}),
])
_move("land_hard", [
    (0.0, {**AIR}),
    (0.2, {**CROUCH, "by": 17.0, "tilt": 30.0, "head": 24.0, "nu": 90.0, "nl": 40.0, "wa": 30.0, "fu": 90.0, "fl": 80.0,
           "squint": 0.9, "mouth": 0.8, "fx__dust": 1.0, "fx__shock": 1.0, "ease": "out"}),
    (0.6, {"by": 13.0, "fx__shock": 0.0, "fx__dust": 0.3, "squint": 0.4}),
    (1.0, HOME),
])
_move("roll", [
    (0.0, {}),
    (0.15, {**CROUCH, "by": 14.0, "tilt": 30.0, "head": 20.0, "ease": "out"}),
    (0.75, {"x": 8.0, "spin": 320.0, "by": 8.0, "nleg": a(-30.0, 60.0), "fleg": a(-10.0, 80.0), "ease": "lin"}),
    (0.9, {"x": 4.0, "spin": 360.0, "by": 8.0, "nleg": g(18.0), "fleg": g(-6.0)}),
    (1.0, {**HOME, "spin": 360.0}),
], extra=lambda t, p: _spin_legs(p))
_move("roll_back", [
    (0.0, {}),
    (0.15, {**CROUCH, "by": 14.0, "tilt": 20.0, "ease": "out"}),
    (0.75, {"x": -8.0, "spin": -320.0, "by": 8.0, "nleg": a(-30.0, 60.0), "fleg": a(-10.0, 80.0), "ease": "lin"}),
    (0.9, {"x": -4.0, "spin": -360.0, "by": 8.0, "nleg": g(10.0), "fleg": g(-14.0)}),
    (1.0, {**HOME, "spin": -360.0}),
], extra=lambda t, p: _spin_legs(p))
_move("spot_dodge", [
    (0.0, {}),
    (0.2, {"by": 15.0, "tilt": -20.0, "head": -20.0, "x": -2.0, "nu": 150.0, "nl": 170.0, "wa": 170.0, "fu": 160.0,
           "fl": 170.0, "squint": 0.8, "mouth": 0.6, "ease": "out"}),
    (0.6, {"by": 13.0}),
    (1.0, HOME),
])
_move("air_dodge", [
    (0.0, AIR),
    (0.2, {"y": -6.0, "spin": -20.0, "tilt": 20.0, "head": 20.0, "nleg": a(-20.0, 60.0), "fleg": a(0.0, 80.0),
           "nu": 80.0, "nl": -40.0, "wa": -60.0, "fu": 60.0, "fl": -20.0, "squint": 0.9, "ease": "out"}),
    (0.7, {"spin": -10.0}),
    (1.0, AIR),
], base=AIR)
_move("platform_drop", [
    (0.0, {}),
    (0.33, {**CROUCH, "by": 12.0, "ease": "out"}),
    (1.0, {**fall(0.0), "y": 6.0}),
])
_move("footstool_jump", [
    (0.0, AIR),
    (0.25, {"y": 2.0, "nleg": a(90.0, 90.0), "fleg": a(95.0, 95.0), "tilt": 14.0, "fx__dust": 1.0, "ease": "out"}),
    (0.6, {"y": -8.0, "nleg": a(110.0, 120.0), "fleg": a(100.0, 120.0), "nu": -60.0, "nl": -80.0, "wa": -100.0,
           "tilt": -6.0, "head": -12.0, "mouth": 0.8, "fx__dust": 0.0}),
    (1.0, AIR),
], base=AIR)

# Defense.
_move("shield_raise", [(0.0, {}), (0.5, {**GUARD, "fx__shield": 0.9, "ease": "out"}), (1.0, GUARD)])
_move("shield_release", [(0.0, GUARD), (0.5, {**GUARD, "fx__shield": 0.3, "by": 6.0}), (1.0, HOME)])
_move("shield_hit", [
    (0.0, GUARD),
    (0.33, {**GUARD, "x": -4.0, "tilt": -16.0, "head": -14.0, "squint": 0.9, "fx__flash": 1.0, "ease": "out"}),
    (1.0, {**GUARD, "x": -2.0}),
], base=GUARD)
_move("parry", [
    (0.0, {}),
    (0.2, {"by": 6.0, "tilt": -6.0, "nu": 10.0, "nl": -60.0, "wa": -80.0, "squint": 0.4, "ease": "out"}),
    (0.4, {"x": -2.0, "tilt": -12.0, "nu": -40.0, "nl": -90.0, "wa": -130.0, "mouth": 0.8, "fx__flash": 1.0,
           "fx__spark": 0.8, "ease": "in"}),
    (0.7, {"fx__flash": 0.2, "fx__spark": 0.0, "mouth": 0.4}),
    (1.0, HOME),
])

# Damage.
_move("launch", [
    (0.0, {**AIR, "fx__hit": 1.0}),
    (0.2, {"spin": -30.0, "tilt": -10.0, "head": -30.0, "nu": -150.0, "nl": -170.0, "wa": -170.0, "fu": -110.0,
           "fl": -140.0, "nleg": a(40.0, 60.0), "fleg": a(20.0, 40.0), "mouth": 1.0, "squint": 0.9, "fx__hit": 0.4,
           "fx__speed": 0.8, "ease": "out"}),
    (1.0, {"spin": -50.0, "fx__hit": 0.0, "fx__speed": 0.5}),
], base=AIR)
_move("meteor", [
    (0.0, {**AIR, "fx__hit": 1.0}),
    (0.2, {"spin": 50.0, "tilt": 20.0, "head": 30.0, "nu": -100.0, "nl": -120.0, "wa": -120.0, "fu": -130.0,
           "fl": -150.0, "nleg": a(-60.0, -40.0), "fleg": a(-80.0, -50.0), "mouth": 1.0, "squint": 0.9,
           "fx__hit": 0.4, "ease": "out"}),
    (1.0, {"spin": 70.0, "fx__hit": 0.0}),
], base=AIR)
_move("splat", [
    (0.0, {**AIR, "spin": 40.0, "mouth": 1.0}),
    (0.33, {**ON_FRONT, "y": 8.0, "fx__dust": 1.0, "fx__shock": 0.8, "ease": "in"}),
    (0.6, {**ON_FRONT, "y": 5.0, "head": 60.0, "fx__shock": 0.0}),
    (1.0, {**ON_FRONT, "fx__stars": 0.8, "fx__dust": 0.2}),
])
_move("ground_bounce", [
    (0.0, {**AIR, "spin": -70.0, "mouth": 1.0}),
    (0.2, {**ON_BACK, "y": 22.0, "fx__dust": 1.0, "fx__shock": 1.0, "ease": "in"}),
    (0.6, {**ON_BACK, "y": 2.0, "spin": -60.0, "nu": -100.0, "nl": -120.0, "fu": -60.0, "fl": -90.0,
           "nleg": a(-50.0, -10.0), "fleg": a(-60.0, -30.0), "fx__shock": 0.0, "ease": "out"}),
    (1.0, {**ON_BACK, "y": 10.0, "spin": -70.0, "fx__dust": 0.0}),
])
_move("knockdown", [
    (0.0, {}),
    (0.25, {"x": -4.0, "tilt": -24.0, "head": -26.0, "nu": -90.0, "nl": -120.0, "wa": -140.0, "fu": -100.0, "fl": -130.0,
            "nleg": g(20.0, 6.0), "squint": 0.9, "mouth": 1.0}),
    (0.6, {**ON_BACK, "y": 14.0, "spin": -80.0, "ease": "in"}),
    (0.8, {**ON_BACK, "y": 22.0, "fx__dust": 1.0}),
    (1.0, {**ON_BACK, "fx__dust": 0.2}),
])
_move("prone_damage", [
    (0.0, ON_BACK),
    (0.33, {**ON_BACK, "y": 16.0, "spin": -84.0, "head": -60.0, "nu": -40.0, "fu": -60.0, "nleg": a(-50.0, -10.0),
            "fx__hit": 1.0, "squint": 1.0, "ease": "out"}),
    (1.0, {**ON_BACK, "fx__hit": 0.0}),
])
_move("getup", [
    (0.0, ON_BACK),
    (0.33, {**ON_BACK, "y": 12.0, "spin": -40.0, "head": -20.0, "nu": 120.0, "nl": 100.0, "wa": 170.0, "fu": 130.0,
            "fl": 100.0, "nleg": a(-30.0, 80.0), "fleg": a(-10.0, 90.0), "squint": 0.4, "mouth": 0.3}),
    (0.66, {**CROUCH, "x": -2.0, "by": 14.0}),
    (1.0, HOME),
])
_move("getup_attack", [
    (0.0, ON_BACK),
    (0.25, {**ON_BACK, "y": 10.0, "spin": -30.0, "head": -10.0, "nu": 170.0, "nl": 175.0, "wa": 178.0, "fu": 120.0,
            "fl": 90.0, "nleg": a(-20.0, 60.0), "fleg": a(0.0, 80.0), "mouth": 0.8, "squint": 0.6}),
    (0.375, {"spin": -10.0, "nu": 10.0, "nl": 20.0, "wa": 15.0, "fx__trail": 1.0, "fx__spark": 1.0, "ease": "in"}),
    (0.5, {"nu": 0.0, "nl": 10.0, "wa": 0.0, "fx__spark": 0.0}),
    (0.625, {"spin": 0.0, "nu": 170.0, "nl": 175.0, "wa": 178.0, "fx__trail": 1.0, "fx__spark": 1.0, "ease": "in"}),
    (0.75, {**CROUCH, "by": 12.0, "fx__trail": 0.0, "fx__spark": 0.0}),
    (1.0, HOME),
])
_move("getup_roll", [
    (0.0, ON_BACK),
    (0.25, {**ON_BACK, "spin": -120.0, "head": -100.0, "nleg": a(-150.0, -60.0), "fleg": a(-140.0, -50.0)}),
    (0.7, {"x": -4.0, "spin": -330.0, "ease": "lin"}),
    (0.85, {**CROUCH, "x": -4.0, "spin": -360.0, "by": 12.0}),
    (1.0, {**HOME, "spin": -360.0}),
], extra=lambda t, p: _spin_legs(p))
_move("tech", [
    (0.0, {**AIR, "spin": -40.0, "squint": 0.9}),
    (0.25, {**CROUCH, "by": 16.0, "tilt": 30.0, "fx__flash": 1.0, "fx__dust": 1.0, "ease": "out"}),
    (0.6, {**CROUCH, "fx__flash": 0.2}),
    (1.0, {**HOME, "fx__flash": 0.0}),
])
_move("wall_tech", [
    (0.0, {**AIR, "spin": -30.0}),
    (0.25, {"x": 8.0, "y": -6.0, "spin": -80.0, "nleg": a(-80.0, -70.0), "fleg": a(-60.0, -80.0), "nu": 170.0, "nl": 160.0,
            "wa": 160.0, "fu": 120.0, "fl": 140.0, "fx__flash": 1.0, "ease": "out"}),
    (0.6, {"fx__flash": 0.2}),
    (1.0, {**AIR, "fx__flash": 0.0}),
], base=AIR)
_move("wall_jump", [
    (0.0, {**AIR, "x": 8.0, "spin": -10.0, "nleg": a(-30.0, 30.0), "fleg": a(-10.0, 20.0)}),
    (0.25, {"x": 10.0, "spin": -20.0, "nleg": a(-10.0, -20.0), "fleg": a(0.0, -10.0), "fx__dust": 1.0, "ease": "out"}),
    (0.6, {"x": 0.0, "spin": -10.0, "tilt": -8.0, "head": -14.0, "nleg": a(150.0, 120.0), "fleg": a(140.0, 100.0),
           "nu": -60.0, "nl": -80.0, "wa": -100.0, "mouth": 0.8, "fx__dust": 0.0}),
    (1.0, AIR),
], base=AIR)
_move("wake", [
    (0.0, {**sleep(0.0)}),
    (0.25, {**sleep(0.0), "blink": False, "head": -10.0, "tilt": 0.0, "squint": 0.0, "mouth": 1.0, "fx__zzz": 0.0,
            "fx__flash": 0.6, "ease": "out"}),
    (1.0, {**HOME, "fx__flash": 0.0}),
])
_move("bury_start", [
    (0.0, {"fx__mound": 0.0, "mouth": 1.0}),
    (0.4, {**buried(0.0), "y": 16.0, "fx__dust": 1.0, "fx__mound": 0.6, "ease": "in"}),
    (1.0, {**buried(0.0), "fx__dust": 0.0}),
])
_move("bury_escape", [
    (0.0, buried(0.0)),
    (0.3, {**buried(0.0), "y": 24.0}),
    (0.6, {**AIR, "y": -4.0, "nu": -80.0, "nl": -90.0, "wa": -100.0, "fu": -100.0, "fl": -110.0, "mouth": 1.0,
           "fx__dust": 1.0, "fx__mound": 0.8, "ease": "out"}),
    (1.0, {**AIR, "fx__mound": 0.0, "fx__dust": 0.0}),
])

# Attacks.
_move("jab", [
    (0.0, {}),
    (0.2, {"x": -1.0, "nu": 60.0, "nl": 150.0, "wa": 10.0, "tilt": 4.0, "ease": "out"}),
    (0.4, {"x": 0.0, "tilt": 12.0, "head": 8.0, "nu": 6.0, "nl": 2.0, "wa": 0.0, "nleg": g(18.0), "mouth": 0.6,
           "fx__trail": 1.0, "fx__spark": 1.0, "ease": "in"}),
    (0.6, {"fx__trail": 0.0, "fx__spark": 0.3}),
    (1.0, {**HOME, "x": 1.0}),
])
_move("jab_2", [
    (0.0, {"x": 1.0}),
    (0.2, {"fz": 1.0, "fu": 40.0, "fl": 160.0, "tilt": 2.0, "nu": 150.0, "nl": -150.0, "wa": -140.0, "ease": "out"}),
    (0.4, {"x": 4.0, "tilt": 18.0, "fu": 4.0, "fl": 0.0, "nleg": g(19.0), "mouth": 0.8, "fx__spark": 1.0,
           "ease": "in"}),
    (0.6, {"fx__spark": 0.3}),
    (1.0, {**HOME, "x": 2.0}),
])
_move("jab_3", [
    # The flurry: a stab, a stab, a stab, then a wild overhead whack.
    (0.0, {"x": 2.0}),
    (0.11, {"x": 1.0, "tilt": 14.0, "nu": 0.0, "nl": 0.0, "wa": 4.0, "mouth": 1.0, "fx__trail": 1.0, "fx__spark": 0.8,
            "ease": "in"}),
    (0.22, {"nu": 50.0, "nl": 140.0, "wa": 20.0, "fx__trail": 0.0, "fx__spark": 0.0}),
    (0.33, {"x": 2.0, "nu": -6.0, "nl": -4.0, "wa": -6.0, "fx__trail": 1.0, "fx__spark": 0.8, "ease": "in"}),
    (0.44, {"nu": 60.0, "nl": 150.0, "wa": 30.0, "fx__trail": 0.0, "fx__spark": 0.0}),
    (0.56, {"x": 0.0, "y": -1.0, "tilt": -12.0, "head": -10.0, "nu": -120.0, "nl": -150.0, "wa": -175.0,
            "nleg": g(14.0, 3.0), "squint": 0.6, "ease": "out"}),
    (0.67, {"x": 2.0, "y": 0.0, "by": 7.0, "tilt": 28.0, "head": 14.0, "nu": 40.0, "nl": 60.0, "wa": 80.0,
            "nleg": g(22.0), "fx__trail": 1.0, "fx__spark": 1.0, "fx__shock": 0.8, "ease": "in"}),
    (0.78, {"fx__trail": 0.0, "fx__spark": 0.3, "fx__shock": 0.3}),
    (1.0, HOME),
])
_move("dash_attack", [
    # A tumbling headbutt: dives forward, rolls through, pops up.
    (0.0, {**run(0.25)}),
    (0.15, {"x": 2.0, "by": 8.0, "tilt": 40.0, "head": 30.0, "mouth": 1.0, "ease": "out"}),
    (0.29, {"x": 8.0, "y": -4.0, "spin": 70.0, "tilt": 0.0, "nleg": a(-60.0, -40.0), "fleg": a(-80.0, -50.0),
            "nu": 160.0, "nl": 170.0, "wa": 175.0, "fu": 150.0, "fl": 170.0, "fx__spark": 1.0, "fx__speed": 1.0,
            "fx__trail": 0.0, "ease": "in"}),
    (0.57, {"x": 10.0, "y": 0.0, "spin": 300.0, "fx__spark": 0.0, "fx__speed": 0.5, "ease": "lin"}),
    (0.71, {**CROUCH, "x": 8.0, "spin": 360.0, "fx__dust": 1.0, "fx__speed": 0.0}),
    (1.0, {**HOME, "spin": 360.0, "x": 2.0}),
], extra=lambda t, p: _spin_legs(p))
_move("attack_up", [
    # An upward jab with a hop: the blade straight up over its head.
    (0.0, {}),
    (0.14, {**CROUCH, "by": 12.0, "nu": 100.0, "nl": 60.0, "wa": 20.0, "ease": "out"}),
    (0.29, {"y": -2.0, "by": 0.0, "tilt": -10.0, "head": -20.0, "nu": -80.0, "nl": -90.0, "wa": -92.0,
            "nleg": g(14.0, 4.0), "fleg": g(-8.0, 6.0), "mouth": 1.0, "fx__trail": 1.0, "fx__spark": 1.0,
            "ease": "in"}),
    (0.43, {"nu": -95.0, "nl": -110.0, "wa": -120.0, "fx__trail": 1.0, "fx__spark": 0.4, "ease": "lin"}),
    (0.57, {"y": 0.0, "by": 4.0, "fx__trail": 0.0, "fx__spark": 0.0, "nleg": g(14.0), "fleg": g(-9.0)}),
    (1.0, HOME),
])
_move("attack_down", [
    # A low, mean ankle-kick from the crouch.
    (0.0, CROUCH),
    (0.17, {**CROUCH, "x": -2.0, "tilt": -6.0, "nleg": g(8.0, 4.0), "ease": "out"}),
    (0.33, {**CROUCH, "x": 0.0, "tilt": -12.0, "head": 0.0, "nleg": a(-6.0, 4.0), "mouth": 0.8, "fx__spark": 1.0,
            "fx__dust": 0.7, "ease": "in"}),
    (0.5, {"fx__spark": 0.3}),
    (1.0, CROUCH),
], base=CROUCH)
_move("smash_forward", [
    # A leaping two-handed overhead chop that buries the blade in the floor.
    (0.0, {}),
    (0.22, {**smash_charge(0.0), "fx__charge": 0.6, "ease": "out"}),
    (0.33, {"x": 2.0, "y": -4.0, "by": 0.0, "tilt": -6.0, "nu": -110.0, "nl": -140.0, "wa": -175.0, "fu": -100.0,
            "fl": -130.0, "nleg": a(70.0, 130.0), "fleg": a(120.0, 150.0), "fx__charge": 0.0, "mouth": 1.0,
            "ease": "out"}),
    (0.44, {"x": 5.0, "y": 0.0, "by": 9.0, "tilt": 34.0, "head": 18.0, "nu": 40.0, "nl": 50.0, "wa": 70.0, "fu": 40.0,
            "fl": 50.0, "nleg": g(26.0), "fleg": g(0.0), "fx__trail": 1.0, "fx__spark": 1.0, "fx__shock": 1.0,
            "fx__dust": 1.0, "ease": "in"}),
    (0.56, {"fx__trail": 0.0, "fx__spark": 0.5, "fx__shock": 0.5}),
    (0.78, {"x": 4.0, "by": 7.0, "tilt": 24.0, "fx__spark": 0.0, "fx__shock": 0.0, "fx__dust": 0.0}),
    (1.0, HOME),
])
_move("smash_up", [
    # A spinning uppercut leap.
    (0.0, {}),
    (0.22, {**CROUCH, "by": 15.0, "nu": 120.0, "nl": 150.0, "wa": 150.0, "squint": 0.6, "fx__charge": 0.5,
            "ease": "out"}),
    (0.33, {"y": -2.0, "by": -2.0, "tilt": -16.0, "head": -24.0, "nu": -30.0, "nl": -50.0, "wa": -60.0,
            "nleg": a(110.0, 120.0), "fleg": a(80.0, 110.0), "mouth": 1.0, "fx__charge": 0.0, "fx__trail": 1.0,
            "ease": "in"}),
    (0.44, {"y": 0.0, "spin": -40.0, "nu": -90.0, "nl": -70.0, "wa": -95.0, "fx__spark": 1.0, "fx__trail": 1.0,
            "ease": "lin"}),
    (0.56, {"y": -2.0, "spin": -10.0, "nu": -140.0, "nl": -160.0, "wa": -170.0, "fx__spark": 0.3, "fx__trail": 1.0}),
    (0.78, {**CROUCH, "y": 0.0, "spin": 0.0, "by": 10.0, "fx__trail": 0.0, "fx__spark": 0.0, "fx__dust": 0.8}),
    (1.0, {**HOME, "fx__dust": 0.0}),
])
_move("smash_down", [
    # A breakdance sweep: drops to its hands and scissors the blade round
    # in front and behind.
    (0.0, {}),
    (0.22, {**CROUCH, "by": 16.0, "tilt": 30.0, "nu": 60.0, "nl": 80.0, "wa": 90.0, "fu": 90.0, "fl": 90.0,
            "ease": "out"}),
    (0.33, {"by": 17.0, "tilt": 40.0, "nu": 10.0, "nl": 10.0, "wa": 8.0, "nleg": g(24.0, 0.0), "mouth": 0.9,
            "fx__trail": 1.0, "fx__spark": 1.0, "fx__dust": 1.0, "ease": "in"}),
    (0.44, {"fx__trail": 0.0, "fx__spark": 0.3}),
    (0.56, {"tilt": 20.0, "nu": 170.0, "nl": 172.0, "wa": 176.0, "nleg": g(14.0), "fleg": g(-22.0, 0.0),
            "fx__trail": 1.0, "fx__spark": 1.0, "ease": "in"}),
    (0.67, {"fx__trail": 0.0, "fx__spark": 0.3, "fx__dust": 0.3}),
    (1.0, {**HOME, "fx__dust": 0.0}),
])
_move("air_neutral", [
    # A spinning top: tucked, the blade held straight out, one full turn.
    (0.0, AIR),
    (0.14, {"nleg": a(-30.0, 60.0), "fleg": a(-10.0, 80.0), "nu": 0.0, "nl": 0.0, "wa": 0.0, "fu": 180.0, "fl": 180.0,
            "mouth": 0.8, "fx__trail": 1.0, "fx__spark": 1.0, "ease": "out"}),
    (0.71, {"spin": 360.0, "fx__trail": 1.0, "fx__spark": 0.5, "ease": "lin"}),
    (0.86, {"spin": 360.0, "fx__trail": 0.0, "fx__spark": 0.0}),
    (1.0, {**AIR, "spin": 360.0}),
], base=AIR, extra=lambda t, p: (body_arms(t, p), _spin_legs(p)))
_move("air_forward", [
    # An overhead chop in the air that spikes.
    (0.0, AIR),
    (0.25, {"tilt": -14.0, "head": -12.0, "nu": -120.0, "nl": -150.0, "wa": -170.0, "nleg": a(110.0, 80.0),
            "fleg": a(130.0, 100.0), "ease": "out"}),
    (0.375, {"tilt": 30.0, "head": 16.0, "nu": 50.0, "nl": 70.0, "wa": 95.0, "nleg": a(0.0, 90.0), "fleg": a(30.0, 120.0),
             "mouth": 1.0, "fx__trail": 1.0, "fx__spark": 1.0, "ease": "in"}),
    (0.5, {"fx__trail": 0.0, "fx__spark": 0.4}),
    (1.0, AIR),
], base=AIR)
_move("air_back", [
    # A mule kick behind it, both feet.
    (0.0, AIR),
    (0.17, {"tilt": 20.0, "head": 10.0, "nleg": a(30.0, 150.0), "fleg": a(50.0, 160.0), "ease": "out"}),
    (0.33, {"tilt": 36.0, "head": 20.0, "hx": 2.0, "nleg": a(170.0, 178.0), "fleg": a(160.0, 168.0), "mouth": 1.0,
            "fx__spark": 1.0, "ease": "in"}),
    (0.5, {"fx__spark": 0.3}),
    (1.0, AIR),
], base=AIR)
_move("air_up", [
    # A backflip slash, blade sweeping overhead from front to back.
    (0.0, AIR),
    (0.17, {"spin": 10.0, "nu": 20.0, "nl": 20.0, "wa": 10.0, "ease": "out"}),
    (0.33, {"spin": -20.0, "tilt": -10.0, "head": -24.0, "nu": -60.0, "nl": -70.0, "wa": -70.0, "fx__trail": 1.0,
            "ease": "in"}),
    (0.5, {"spin": -40.0, "nu": -110.0, "nl": -120.0, "wa": -120.0, "mouth": 1.0, "fx__trail": 1.0, "fx__spark": 1.0,
           "ease": "lin"}),
    (0.67, {"spin": -30.0, "nu": -160.0, "nl": -170.0, "wa": -178.0, "fx__trail": 1.0, "fx__spark": 0.3}),
    (0.83, {"fx__trail": 0.0, "fx__spark": 0.0}),
    (1.0, {**AIR, "spin": 0.0}),
], base=AIR)
_move("air_down", [
    # A feet-first stomp dive.
    (0.0, AIR),
    (0.29, {"y": -8.0, "tilt": -8.0, "nleg": a(-20.0, 60.0), "fleg": a(0.0, 80.0), "nu": -60.0, "nl": -80.0,
            "wa": -100.0, "fu": -100.0, "fl": -120.0, "ease": "out"}),
    (0.43, {"y": 2.0, "tilt": 4.0, "head": 10.0, "nleg": a(95.0, 92.0), "fleg": a(88.0, 86.0), "mouth": 1.0,
            "fx__spark": 1.0, "fx__speed": 1.0, "ease": "in"}),
    (0.86, {"y": 4.0, "fx__spark": 0.6, "fx__speed": 1.0}),
    (1.0, {**AIR, "fx__speed": 0.0, "fx__spark": 0.0}),
], base=AIR)
_move("air_land", [
    (0.0, {**AIR, "nu": 60.0, "nl": 80.0, "wa": 80.0}),
    (0.33, {**CROUCH, "by": 15.0, "fx__dust": 1.0, "ease": "out"}),
    (1.0, {**HOME, "fx__dust": 0.0}),
])

# Specials.
_move("rock_toss", [
    # Neutral special: snatches a rock off the floor and lobs it.
    (0.0, {}),
    (0.25, {**CROUCH, "by": 15.0, "tilt": 34.0, "head": 20.0, "fu": 80.0, "fl": 90.0, "ease": "out"}),
    (0.375, {"by": 6.0, "tilt": -10.0, "head": -10.0, "fz": 1.0, "fu": -140.0, "fl": -170.0, "fx__rock": 0.01, "mouth": 0.8,
             "ease": "out"}),
    (0.5, {"x": 3.0, "tilt": 20.0, "head": 8.0, "fu": 10.0, "fl": 0.0, "nleg": g(18.0), "mouth": 1.0, "ease": "in"}),
    (1.0, {**HOME, "mouth": 0.6}),
], extra=lambda t, p: p.update({"fx.rock": 0.0 if t < 0.36 else min(1.0, 0.001 + (t - 0.36) / 0.64)}))
_move("shiv_lunge", [
    # Side special: a darting lunge with the blade straight out.
    (0.0, {}),
    (0.22, {"x": -4.0, "by": 10.0, "tilt": 8.0, "nu": 150.0, "nl": 170.0, "wa": 175.0, "fu": 40.0, "fl": 20.0,
            "nleg": g(10.0), "fleg": g(-16.0), "squint": 0.6, "ease": "out"}),
    (0.33, {"x": 5.0, "by": 6.0, "tilt": 30.0, "head": 18.0, "nu": 2.0, "nl": 0.0, "wa": 0.0, "fu": 170.0, "fl": 175.0,
            "nleg": g(30.0, 4.0), "fleg": g(-6.0, 8.0), "mouth": 1.0, "fx__trail": 1.0, "fx__speed": 1.0,
            "fx__spark": 1.0, "ease": "in"}),
    (0.67, {"x": 7.0, "fx__trail": 0.0, "fx__speed": 1.0, "fx__spark": 0.6, "ease": "lin"}),
    (0.78, {"x": 6.0, "by": 9.0, "tilt": 10.0, "nleg": g(28.0), "fleg": g(4.0), "fx__speed": 0.0, "fx__spark": 0.0,
            "fx__dust": 1.0}),
    (1.0, {**HOME, "x": 3.0, "fx__dust": 0.0}),
])
_move("spring_pounce", [
    # Up special: a coiled spring of a jump, blade whirling over its head.
    (0.0, {}),
    (0.22, {**CROUCH, "by": 17.0, "tilt": 20.0, "nu": 80.0, "nl": 60.0, "wa": 40.0, "ease": "out"}),
    (0.33, {"y": -3.0, "by": -2.0, "tilt": -10.0, "head": -20.0, "nleg": a(100.0, 95.0), "fleg": a(95.0, 90.0),
            "nu": -80.0, "nl": -30.0, "wa": -60.0, "fu": -100.0, "fl": -110.0, "mouth": 1.0, "fx__dust": 1.0,
            "fx__speed": 1.0, "fx__trail": 1.0, "ease": "in"}),
    (0.78, {"y": -4.0, "spin": -360.0, "fx__trail": 1.0, "fx__spark": 0.6, "fx__dust": 0.0, "ease": "lin"}),
    (1.0, {**fall_special(0.0), "y": -3.0, "spin": -360.0, "fx__trail": 0.0, "fx__spark": 0.0, "fx__speed": 0.0}),
], extra=lambda t, p: (body_arms(t, p), _spin_legs(p)))
_move("play_dead", [
    # Down special: the counter. It keels over, tongue out... and waits.
    (0.0, {}),
    (0.2, {"x": -2.0, "tilt": -20.0, "head": -26.0, "nu": -60.0, "nl": -100.0, "wa": -140.0, "fu": -120.0, "fl": -150.0,
           "mouth": 1.0, "squint": 0.8, "ease": "out"}),
    (0.4, {**ON_BACK, "y": 22.0, "dead": True, "fx__dust": 0.8, "ease": "in"}),
    (0.6, {**ON_BACK, "dead": True, "fx__dust": 0.0, "squint": 0.0}),
    (0.8, {**ON_BACK, "dead": False, "squint": 0.0, "head": -70.0}),
    (1.0, {**CROUCH, "by": 14.0}),
])
_move("play_dead_strike", [
    # ...and springs up stabbing whoever fell for it.
    (0.0, {**ON_BACK, "dead": False, "squint": 0.0}),
    (0.14, {**CROUCH, "by": 15.0, "nu": 150.0, "nl": 170.0, "wa": 170.0, "squint": 0.6, "mouth": 1.0, "ease": "out"}),
    (0.29, {"x": 5.0, "y": -2.0, "by": 0.0, "tilt": 30.0, "head": 16.0, "nu": 4.0, "nl": 0.0, "wa": -4.0,
            "nleg": g(28.0, 6.0), "fleg": g(-2.0, 10.0), "fx__trail": 1.0, "fx__spark": 1.0, "fx__flash": 1.0,
            "ease": "in"}),
    (0.43, {"fx__trail": 0.0, "fx__spark": 0.4, "fx__flash": 0.3}),
    (0.71, {**HOME, "x": 3.0, "fx__spark": 0.0, "fx__flash": 0.0}),
    (1.0, {**HOME, "x": 2.0}),
])
_move("goblin_frenzy", [
    # Final smash: a cackling blur of stabs, then a leaping finisher.
    (0.0, {}),
    (0.08, {**CROUCH, "by": 15.0, "mouth": 1.0, "squint": 0.6, "fx__charge": 1.0}),
    *[(0.15 + k * 0.08, {"x": 2.0 + 2.0 * (k % 2), "tilt": 24.0 - 10.0 * (k % 2), "by": 6.0,
                         "nu": (4.0 if k % 2 == 0 else 60.0), "nl": (0.0 if k % 2 == 0 else 150.0),
                         "wa": (-4.0 + 10.0 * (k % 3) if k % 2 == 0 else 20.0), "fx__trail": float(k % 2 == 0),
                         "fx__spark": float(k % 2 == 0), "fx__speed": 1.0, "fx__charge": 0.0, "ease": "in"})
      for k in range(7)],
    (0.77, {"x": 2.0, "y": -4.0, "tilt": -12.0, "nu": -120.0, "nl": -150.0, "wa": -175.0, "fx__trail": 0.0,
            "fx__spark": 0.0, "nleg": a(70.0, 130.0), "fleg": a(120.0, 150.0), "ease": "out"}),
    (0.85, {"x": 2.0, "y": 0.0, "by": 9.0, "tilt": 34.0, "nu": 40.0, "nl": 50.0, "wa": 70.0, "nleg": g(24.0),
            "fleg": g(2.0), "fx__trail": 1.0, "fx__spark": 1.0, "fx__shock": 1.0, "fx__speed": 0.0, "ease": "in"}),
    (1.0, {**HOME, "x": 2.0, "mouth": 1.0, "fx__shock": 0.0}),
])

# Grabs: the far hand grabs, the near hand stabs.
_move("grab", [
    (0.0, {}),
    (0.33, {"x": 4.0, "by": 6.0, "tilt": 22.0, "head": 10.0, "fz": 1.0, "fu": 0.0, "fl": -4.0, "nu": 150.0, "nl": -150.0,
            "wa": -140.0, "nleg": g(20.0), "mouth": 0.8, "ease": "in"}),
    (1.0, GRAB_HOLD),
])
_move("pummel", [
    # A bite.
    (0.0, GRAB_HOLD),
    (0.25, {**GRAB_HOLD, "hx": 0.0, "head": -10.0, "mouth": 1.0, "ease": "out"}),
    (0.5, {**GRAB_HOLD, "hx": 5.0, "head": 20.0, "mouth": 0.0, "fx__spark": 0.8, "ease": "in"}),
    (1.0, GRAB_HOLD),
], base=GRAB_HOLD)
_move("grab_release", [(0.0, GRAB_HOLD), (0.5, {**GRAB_HOLD, "fu": -30.0, "fl": -60.0, "x": 2.0}), (1.0, HOME)],
      base=GRAB_HOLD)
_move("throw_forward", [
    (0.0, GRAB_HOLD),
    (0.25, {**GRAB_HOLD, "x": -3.0, "tilt": -6.0, "fu": 60.0, "fl": 100.0, "nu": -110.0, "nl": -140.0, "wa": -170.0,
            "ease": "out"}),
    (0.375, {"x": 6.0, "tilt": 30.0, "head": 16.0, "fu": 0.0, "fl": 0.0, "nu": 30.0, "nl": 50.0, "wa": 70.0,
             "nleg": g(22.0), "mouth": 1.0, "fx__trail": 1.0, "fx__spark": 1.0, "ease": "in"}),
    (0.5, {"fx__trail": 0.0, "fx__spark": 0.3}),
    (1.0, HOME),
], base=GRAB_HOLD)
_move("throw_back", [
    (0.0, GRAB_HOLD),
    (0.25, {**GRAB_HOLD, "fu": -60.0, "fl": -80.0, "tilt": 6.0, "ease": "out"}),
    (0.5, {"x": -4.0, "tilt": -26.0, "head": -20.0, "fu": -150.0, "fl": -170.0, "nu": 160.0, "nl": 170.0, "wa": 176.0,
           "nleg": g(18.0, 2.0), "fleg": g(-16.0), "mouth": 1.0, "ease": "in"}),
    (0.625, {"fu": 170.0, "fl": 175.0, "fx__trail": 1.0, "fx__spark": 1.0}),
    (0.75, {"fx__trail": 0.0, "fx__spark": 0.0}),
    (1.0, HOME),
], base=GRAB_HOLD)
_move("throw_up", [
    (0.0, GRAB_HOLD),
    (0.25, {**GRAB_HOLD, "by": 12.0, "tilt": 20.0, "fu": 40.0, "fl": 60.0, "ease": "out"}),
    (0.375, {"y": -1.0, "by": 0.0, "tilt": -10.0, "head": -20.0, "fu": -90.0, "fl": -95.0, "ease": "in"}),
    (0.5, {"nu": -80.0, "nl": -90.0, "wa": -95.0, "mouth": 1.0, "fx__trail": 1.0, "fx__spark": 1.0, "ease": "in"}),
    (0.625, {"y": 0.0, "fx__trail": 0.0, "fx__spark": 0.3}),
    (1.0, HOME),
], base=GRAB_HOLD)
_move("throw_down", [
    (0.0, GRAB_HOLD),
    (0.25, {**GRAB_HOLD, "y": -3.0, "tilt": 0.0, "fu": -60.0, "fl": -80.0, "ease": "out"}),
    (0.375, {"y": 0.0, "by": 12.0, "tilt": 36.0, "head": 20.0, "fu": 80.0, "fl": 90.0, "fx__shock": 1.0, "ease": "in"}),
    (0.5, {"nu": -100.0, "nl": -130.0, "wa": -150.0, "fx__shock": 0.3}),
    (0.625, {"y": -6.0, "by": 4.0, "nleg": a(90.0, 90.0), "fleg": a(95.0, 95.0), "mouth": 1.0, "ease": "out"}),
    (0.75, {"y": 0.0, "nleg": g(16.0), "fleg": g(-10.0), "fx__spark": 1.0, "fx__dust": 1.0, "fx__shock": 0.0,
            "ease": "in"}),
    (1.0, HOME),
], base=GRAB_HOLD)
_move("grabbed_pummel", [
    (0.0, grabbed(0.0)),
    (0.33, {**grabbed(0.0), "tilt": -24.0, "head": -30.0, "squint": 1.0, "fx__hit": 1.0, "ease": "out"}),
    (1.0, {**grabbed(0.0), "fx__hit": 0.0}),
])
_move("grab_escape", [
    (0.0, grabbed(0.0)),
    (0.4, {"x": -6.0, "y": -4.0, "tilt": -20.0, "nleg": a(-20.0, 40.0), "fleg": a(0.0, 60.0), "nu": 140.0, "nl": 160.0,
           "wa": 170.0, "fu": 140.0, "fl": 160.0, "mouth": 0.8, "ease": "out"}),
    (0.7, {**CROUCH, "x": -6.0}),
    (1.0, {**HOME, "x": -4.0}),
])

# Ledge.
_move("ledge_catch", [(0.0, {**fall(0.0)}), (0.5, {**HANG, "y": 12.0, "ease": "out"}), (1.0, HANG)])
_move("ledge_getup", [
    (0.0, HANG),
    (0.33, {**HANG, "y": -8.0, "tilt": 20.0, "nu": 60.0, "nl": 40.0, "wa": -20.0, "fu": 60.0, "fl": 40.0,
            "nleg": a(-20.0, 80.0), "fleg": a(0.0, 90.0), "ease": "out"}),
    (0.66, {**CROUCH, "y": -22.0, "nleg": g(18.0, 22.0), "fleg": g(4.0, 22.0)}),
    (1.0, {**HOME, "y": -26.0, "nleg": g(18.0, 26.0), "fleg": g(-4.0, 26.0)}),
])
_move("ledge_attack", [
    (0.0, HANG),
    (0.33, {**HANG, "y": -14.0, "tilt": 24.0, "nu": 160.0, "nl": 170.0, "wa": 176.0, "fu": 60.0, "fl": 40.0,
            "nleg": a(-20.0, 80.0), "fleg": a(0.0, 90.0), "ease": "out"}),
    (0.5, {**CROUCH, "y": -24.0, "x": 0.0, "nu": 10.0, "nl": 10.0, "wa": 6.0, "nleg": g(22.0, 26.0), "fleg": g(2.0, 26.0),
           "mouth": 1.0, "fx__trail": 1.0, "fx__spark": 1.0, "ease": "in"}),
    (0.67, {"fx__trail": 0.0, "fx__spark": 0.3}),
    (1.0, {**HOME, "y": -26.0, "nleg": g(18.0, 26.0), "fleg": g(-4.0, 26.0)}),
])
_move("ledge_roll", [
    (0.0, HANG),
    (0.25, {**HANG, "y": -12.0, "tilt": 30.0, "nleg": a(-30.0, 60.0), "fleg": a(-10.0, 80.0), "ease": "out"}),
    (0.75, {"x": 7.0, "y": -18.0, "spin": 320.0, "ease": "lin"}),
    (0.9, {**CROUCH, "x": 8.0, "y": -26.0, "spin": 360.0, "nleg": g(24.0, 26.0), "fleg": g(2.0, 26.0)}),
    (1.0, {**HOME, "x": 8.0, "y": -26.0, "spin": 360.0, "nleg": g(24.0, 26.0), "fleg": g(0.0, 26.0)}),
], extra=lambda t, p: _spin_legs(p))
_move("ledge_jump", [
    (0.0, HANG),
    (0.33, {**HANG, "y": 0.0, "nleg": a(-20.0, 60.0), "fleg": a(0.0, 70.0), "ease": "out"}),
    (0.66, {**AIR, "y": -10.0, "tilt": -6.0, "head": -16.0, "nu": -60.0, "nl": -40.0, "wa": -80.0, "fu": -100.0,
            "fl": -110.0, "nleg": a(100.0, 100.0), "fleg": a(90.0, 95.0), "mouth": 1.0, "ease": "out"}),
    (1.0, {**AIR, "y": -12.0}),
])
_move("ledge_drop", [(0.0, HANG), (0.5, {**fall(0.0), "y": 6.0, "ease": "out"}), (1.0, {**fall(0.25), "y": 10.0})])

# Items (the item rides the far hand).
_move("item_pickup", [
    (0.0, {}),
    (0.4, {**CROUCH, "by": 16.0, "tilt": 40.0, "head": 24.0, "fu": 80.0, "fl": 85.0, "ease": "out"}),
    (1.0, {**item_hold(0.0)}),
])
_move("item_heavy_pickup", [
    (0.0, {}),
    (0.3, {**CROUCH, "by": 17.0, "tilt": 30.0, "wpn": 0.0, "nu": 80.0, "nl": 90.0, "fu": 85.0, "fl": 95.0,
           "ease": "out"}),
    (0.6, {"by": 12.0, "tilt": 10.0, "nu": 20.0, "nl": -20.0, "fu": 10.0, "fl": -30.0, "mouth": 1.0, "squint": 0.8}),
    (1.0, {**item_heavy_carry(0.0)}),
])
_move("item_throw", [
    (0.0, {**item_hold(0.0)}),
    (0.33, {"x": -3.0, "tilt": -12.0, "head": -10.0, "fu": -150.0, "fl": -170.0, "ease": "out"}),
    (0.5, {"x": 3.0, "tilt": 22.0, "head": 10.0, "fu": 6.0, "fl": 0.0, "nleg": g(18.0), "mouth": 1.0, "ease": "in"}),
    (1.0, HOME),
])
_move("item_drop", [(0.0, {**item_hold(0.0)}), (0.5, {"fu": 70.0, "fl": 80.0, "by": 6.0, "ease": "out"}), (1.0, HOME)])
_move("item_swing", [
    (0.0, {**item_hold(0.0)}),
    (0.33, {"x": -2.0, "tilt": -8.0, "fu": -120.0, "fl": -150.0, "ease": "out"}),
    (0.5, {"x": 4.0, "tilt": 24.0, "fu": 20.0, "fl": 40.0, "nleg": g(20.0), "mouth": 1.0, "ease": "in"}),
    (0.67, {"fu": 40.0, "fl": 60.0}),
    (1.0, {**item_hold(0.0)}),
])

# Presentation.
_move("taunt", [
    # Cackling: doubled over, slapping its knee, then a tongue-out wiggle.
    (0.0, {}),
    (0.11, {"by": 5.0, "tilt": 30.0, "head": 20.0, "fu": 80.0, "fl": 70.0, "mouth": 1.0, "squint": 0.9, "ease": "out"}),
    (0.22, {"by": 8.0, "tilt": 36.0, "fu": 60.0, "fl": 110.0, "fx__flash": 0.4}),
    (0.33, {"by": 4.0, "tilt": 26.0, "fu": 90.0, "fl": 60.0, "fx__flash": 0.0}),
    (0.44, {"by": 8.0, "tilt": 36.0, "fu": 60.0, "fl": 110.0, "fx__flash": 0.4}),
    (0.56, {"by": 2.0, "tilt": -10.0, "head": -16.0, "nu": -70.0, "nl": -90.0, "wa": -90.0, "fu": -100.0, "fl": -80.0,
            "fx__flash": 0.0, "ease": "out"}),
    (0.67, {"x": -2.0, "tilt": -16.0, "head": -10.0}),
    (0.78, {"x": 2.0, "tilt": -4.0, "head": -22.0}),
    (0.89, {"x": -2.0, "tilt": -16.0, "head": -10.0}),
    (1.0, {**HOME, "mouth": 0.6}),
])
_move("entrance", [
    # Pops out of a hole in the ground.
    (0.0, {**buried(0.0), "y": 30.0, "fx__mound": 1.0, "mouth": 0.0}),
    (0.3, {**buried(0.0), "y": 18.0, "fx__dust": 1.0, "ease": "out"}),
    (0.5, {**AIR, "y": -5.0, "nu": -60.0, "nl": -40.0, "wa": -80.0, "fu": -100.0, "fl": -110.0, "mouth": 1.0,
           "fx__mound": 0.6, "ease": "out"}),
    (0.7, {**CROUCH, "y": 0.0, "by": 14.0, "fx__mound": 0.0, "fx__dust": 0.8, "ease": "in"}),
    (0.85, {**HOME, "wa": -60.0, "mouth": 1.0, "squint": 0.5, "fx__dust": 0.0}),
    (1.0, {**HOME, "mouth": 0.4}),
])


def _spin_legs(p: Pose) -> None:
    """Angle-mode legs keyed in the body's frame turn with a spin; planted
    legs stay planted."""
    s = float(p.get("spin", 0.0))
    for k in ("nleg", "fleg"):
        leg = p.get(k)
        if isinstance(leg, tuple) and leg[0] == "a":
            p[k] = ("a", leg[1] + s, leg[2] + s)


LOOPS: Dict[str, Callable[[float], Pose]] = {
    "idle": idle, "walk": walk, "run": run, "dash": dash, "talk": talk, "interact": interact, "block": block,
    "crouch": crouch, "crouch_walk": crouch_walk, "fall": fall, "fall_special": fall_special, "tumble": tumble,
    "teeter": teeter, "prone": prone, "dizzy": dizzy, "sleep": sleep, "buried": buried, "smash_charge": smash_charge,
    "grab_hold": grab_hold, "grabbed": grabbed, "ledge_grab": ledge_grab, "item_hold": item_hold,
    "item_heavy_carry": item_heavy_carry, "victory_hold": victory_hold, "loss": loss,
}

CLIPS: Dict[str, Callable[[float], Pose]] = {**LOOPS, **MOVES}
FRAMES: Dict[str, int] = {name: n for name, n, _ms in GOBLIN_ROWS}


def clip_time(animation: str, frame_index: int, frame_count: int) -> float:
    """Loops sample ``i / n``; one-shots ``i / (n - 1)``."""
    n = max(1, frame_count)
    if animation in GOBLIN_LOOPS:
        return (frame_index % n) / n
    return frame_index / max(1, n - 1)


@lru_cache(maxsize=4096)
def _cached(animation: str, t: float) -> Tuple[Tuple[str, Value], ...]:
    return tuple(CLIPS[animation](t).items())


def pose(animation: str, t: float) -> Pose:
    """The goblin's pose for ``animation`` at clip time ``t``."""
    return dict(_cached(animation, round(t, 6)))


__all__ = ["CLIPS", "STANCE", "clip_time", "pose"]
