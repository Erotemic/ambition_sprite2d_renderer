#!/usr/bin/env python3
"""Build Bob's fighter rig document from his SVG.

The SVG ``data/characters/bob/bob.svg`` owns the art and says where every
joint is; ``rigbuild.creature_rig`` with the ``humanoid`` anatomy derives the
skeleton from it, binds every part to its bone, and refreshes the SVG's rig
catalog. This script supplies only what the drawing cannot state: the frame,
the rows (``targets/characters/_bob_motion.py``) and the moves, written as key
poses in ``rigbuild.humanoid``'s pose language. It never draws.

    uv run python scripts/build_bob_rig.py

⭐ HOW BOB MOVES. Bob is a mid-weight bruiser whose reach is a big adjustable
wrench, so every swing is written the same way: an anticipation that loads
the wrench behind him (the hips drop, the torso coils back), one fast frame
of travel (keyed ``"ease": "in"`` so it snaps), a held contact frame where the
hit lands (``fx.spark``), a follow-through that lets the wrench's weight carry
on past the target, and a recovery that settles back into ``STANCE``. Key
times sit on frame times (frame ``i`` of ``n`` is at ``i / (n - 1)``) so the
extremes are drawn, not interpolated past.

The ``fx.*`` channels key the effects ``targets/characters/bob.py`` draws
(the wrench smear, impact sparks, dust, the shield, the packet, the antenna
mast...); the target reads them back per frame.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Callable, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ambition_sprite2d_renderer.rigbuild import humanoid as H  # noqa: E402
from ambition_sprite2d_renderer.rigbuild.humanoid import Pose, Semantic  # noqa: E402
from ambition_sprite2d_renderer.targets.characters._bob_motion import (  # noqa: E402
    BOB_FRONT_ROWS,
    BOB_LOOPS,
    BOB_ROWS,
)

PKG = ROOT / "ambition_sprite2d_renderer"
SVG = PKG / "data" / "characters" / "bob" / "bob.svg"
CENTER_X, GROUND_Y = 340.0, 569.0
BODY = H.Body.from_svg(SVG, CENTER_X, GROUND_Y)
TAU = math.tau


def g(x: float, lift: float = 0.0, pitch: float = 0.0) -> H.Foot:
    """A foot planted (or lifted) in the world."""
    return ("g", x, lift, pitch)


def b(dx: float = 0.0, dy: float = 0.0, pitch: float = 0.0) -> H.Foot:
    """A foot carried with the hips (offset from its drawn place)."""
    return ("b", dx, dy, pitch)


# --- poses -------------------------------------------------------------------------

#: The fighting stance every move starts from and settles back to: knees
#: soft, feet apart, the wrench up and ready in the near hand, the far fist
#: up as a guard.
STANCE: Semantic = {
    "x": 0.0, "y": 12.0, "spin": 0.0, "lean": 7.0, "head": -2.0,
    "nu": 72.0, "ne": 98.0, "nw": -58.0,
    "fu": 58.0, "fe": 104.0, "fw": -84.0,
    "nf": g(34.0), "ff": g(-40.0),
    "eye": "open", "mouth": "closed", "nhand": "fist", "fhand": "fist",
    "wrench": 1.0, "analyzer": 0.0, "fz": 0.0,
}

#: Every effect a clip keys (``targets/characters/bob.py`` draws them). The
#: stance holds them all at zero, so a key that returns to a stance (or to
#: any pose built from it) also ends whatever effect was running; a partial
#: key carries the last strength forward like any other field.
FX = ("aim", "alert", "analyzer_charge", "blink", "bubbles", "bury", "charge", "counter", "dust", "dust_trail",
      "final", "glint", "hit", "launch", "mast", "meteor", "packet", "packet_hold", "parry", "shield",
      "shield_break", "shield_flash", "shock", "shock_back", "spark", "speed", "stars", "stomp", "tap", "tech",
      "toss", "trail", "verify", "wall_dust", "waves", "whirl", "zap", "zzz")
STANCE.update({f"fx.{name}": 0.0 for name in FX})

#: The far arm drawn across the chest (see ``fz``).
REACH = 55.0


def S(**over) -> Semantic:
    """The stance with some fields changed (also a full 'back to stance' key)."""
    return {**STANCE, **over}


#: Crouched low: hips dropped, torso folded over the knees, wrench tucked.
CROUCH = S(y=66.0, lean=26.0, head=-14.0, nf=g(44.0), ff=g(-52.0), nu=66.0, ne=112.0, nw=-30.0,
           fu=34.0, fe=118.0, fw=-60.0)
#: Airborne: knees drawn up (feet carried with the hips), the wrench ready.
AIR = S(y=-6.0, lean=6.0, head=-4.0, nf=b(34.0, -66.0, -20.0), ff=b(2.0, -40.0, 14.0), nu=58.0, ne=92.0,
        nw=-44.0, fu=36.0, fe=98.0, fw=-70.0)
#: Lying on his back, head toward -x, legs out along the ground.
ON_BACK = S(x=28.0, y=112.0, spin=-90.0, lean=0.0, head=-84.0, nu=14.0, ne=10.0, nw=-6.0, fu=-20.0, fe=20.0,
            fw=-40.0, nf=b(-10.0, -20.0, 0.0), ff=b(6.0, -6.0, 0.0), eye="shut", mouth="open")
#: Lying face down, head toward +x.
ON_FRONT = S(x=-28.0, y=122.0, spin=90.0, lean=0.0, head=84.0, nu=20.0, ne=10.0, nw=10.0, fu=40.0, fe=30.0,
             fw=40.0, nf=b(0.0, 0.0, 0.0), ff=b(-8.0, -10.0, 0.0), eye="shut", mouth="open")
#: Hanging from a ledge up and ahead: wrench jaw hooked over it, far hand on it.
HANG = S(x=-26.0, y=40.0, lean=-4.0, head=-14.0, nu=-62.0, ne=4.0, nw=-2.0, fu=-58.0, fe=10.0, fw=-30.0,
         fhand="open", nf=b(6.0, -6.0, 10.0), ff=b(-6.0, -2.0, 12.0))


def clip(keys, base: Semantic = STANCE, extra=None):
    return H.keyed(BODY, base, keys, extra)


def loop(fn: Callable[[float], Semantic]):
    def run(i: int, n: int, t: float) -> Pose:
        return BODY.channels(fn(t))
    return run


def body_arms(t: float, p: Semantic) -> None:
    """Arms keyed in the body's frame: they turn with a spin."""
    for k in ("nu", "nw", "fu", "fw"):
        p[k] = float(p[k]) + float(p.get("spin", 0.0))


def shake(amount: float, seed: float = 0.0):
    """A charge tremble on top of a held pose."""
    def fn(t: float, p: Semantic) -> None:
        p["x"] = float(p["x"]) + amount * math.sin(TAU * 3.0 * t + seed)
        p["y"] = float(p["y"]) + 0.5 * amount * math.sin(TAU * 5.0 * t + 1.3 + seed)
        p["nw"] = float(p["nw"]) + 2.5 * amount * math.sin(TAU * 4.0 * t + seed)
    return fn


def step(phase: float, centre: float, stride: float, lift: float):
    """A planted-then-swinging foot: ``(x, lift, pitch)``."""
    p = phase % 1.0
    if p < 0.5:
        return centre + stride * (1.0 - 4.0 * p), 0.0, 0.0
    s = (p - 0.5) / 0.5
    h = lift * H.pulse(s)
    return centre - stride + 2.0 * stride * H.smooth01(s), h, -0.5 * h


def gait(p: Semantic, t: float, centres=(6.0, -14.0), stride=32.0, lift=22.0) -> Semantic:
    for side, ph, cx in (("n", 0.0, centres[0]), ("f", 0.5, centres[1])):
        x, lf, pitch = step(t + ph, cx, stride, lift)
        p[f"{side}f"] = g(x, lf, pitch)
    return p


W = TAU  # one loop


# --- stance & locomotion -------------------------------------------------------------


def idle(t: float) -> Semantic:
    w = W * t
    return S(y=12.0 + 2.5 * math.sin(w), lean=7.0 + 1.5 * math.sin(w - 0.4), head=-2.0 + 1.2 * math.sin(w - 0.9),
             nu=72.0 + 3.0 * math.sin(w - 0.6), nw=-58.0 + 5.0 * math.sin(w - 1.0),
             fu=58.0 + 3.0 * math.sin(w - 0.3), eye="shut" if 0.55 < t < 0.68 else "open")


def idle_side(t: float) -> Semantic:
    """At ease: the wrench propped on his shoulder, the far fist on his hip."""
    w = W * t
    return S(y=6.0 + 1.8 * math.sin(w), lean=3.0 + 1.0 * math.sin(w - 0.5), head=-3.0 + 2.0 * math.sin(w - 1.0),
             nu=52.0 + 2.0 * math.sin(w - 0.7), ne=150.0, nw=-150.0 + 3.0 * math.sin(w - 1.1),
             fu=118.0, fe=60.0, fw=40.0, nf=g(22.0), ff=g(-30.0), eye="shut" if 0.3 < t < 0.42 else "open")


def idle_look_up(t: float) -> Semantic:
    w = W * t
    return S(y=8.0 + 1.5 * math.sin(w), lean=-6.0, head=-28.0 + 4.0 * math.sin(w - 0.5), fz=REACH,
             fu=-52.0, fe=128.0, fw=-150.0, fhand="open", nu=86.0, ne=30.0, nw=110.0,
             nf=g(24.0), ff=g(-34.0), mouth="open" if 0.4 < t < 0.8 else "closed")


def walk(t: float) -> Semantic:
    """A loose, confident walk: the wrench carried back over the shoulder."""
    w = W * t
    p = S(y=6.0 - 4.0 * math.cos(2 * w), lean=5.0 + 1.5 * math.cos(2 * w), head=-1.0,
          nu=48.0 + 6.0 * math.sin(w + math.pi), ne=150.0, nw=-150.0,
          fu=90.0 + 26.0 * math.sin(w), fe=26.0 + 12.0 * math.sin(w), fw=10.0 + 20.0 * math.sin(w))
    return gait(p, t)


def run(t: float) -> Semantic:
    """Head down, the wrench trailing low behind, the far arm pumping."""
    w = W * t
    p = S(y=2.0 - 8.0 * math.cos(2 * w), lean=20.0 + 3.0 * math.cos(2 * w), head=-10.0,
          nu=128.0 + 12.0 * math.sin(w + math.pi), ne=26.0, nw=152.0,
          fu=70.0 - 58.0 * math.sin(w), fe=96.0, fw=-60.0 - 40.0 * math.sin(w), mouth="grit")
    return gait(p, t, centres=(12.0, -8.0), stride=52.0, lift=42.0)


def dash(t: float) -> Semantic:
    """The initial dash: longer, lower strides than the run, dust kicking."""
    w = W * t
    p = S(y=8.0 - 9.0 * math.cos(2 * w), lean=27.0, head=-14.0,
          nu=140.0, ne=16.0, nw=165.0, fu=60.0 - 62.0 * math.sin(w), fe=90.0, fw=-50.0, mouth="grit")
    p["fx.dust_trail"] = 0.7 + 0.3 * math.cos(2 * w)
    p["fx.speed"] = 0.6
    return gait(p, t, centres=(16.0, -6.0), stride=60.0, lift=36.0)


def crouch(t: float) -> Semantic:
    w = W * t
    return {**CROUCH, "y": 66.0 + 2.0 * math.sin(w), "lean": 26.0 + 1.5 * math.sin(w - 0.5),
            "eye": "shut" if 0.6 < t < 0.75 else "open"}


def crouch_walk(t: float) -> Semantic:
    w = W * t
    p = {**CROUCH, "y": 62.0 - 3.0 * math.cos(2 * w), "lean": 30.0, "head": -16.0,
         "fu": 40.0 + 14.0 * math.sin(w), "nu": 70.0 - 8.0 * math.sin(w)}
    return gait(p, t, centres=(12.0, -24.0), stride=24.0, lift=12.0)


def fall(t: float) -> Semantic:
    w = W * t
    return {**AIR, "y": -2.0, "lean": 2.0, "head": -10.0, "nu": -40.0 + 8.0 * math.sin(w), "ne": 30.0, "nw": -70.0,
            "fu": -30.0 + 10.0 * math.sin(w + 1.4), "fe": 40.0, "fw": -60.0, "fhand": "open",
            "nf": b(16.0, -40.0 + 6.0 * math.sin(w), -10.0), "ff": b(-6.0, -14.0 - 6.0 * math.sin(w), 14.0),
            "mouth": "open"}


def fall_special(t: float) -> Semantic:
    """Helpless after the antenna launch: limp, arms up, slowly turning."""
    w = W * t
    return {**AIR, "y": -2.0, "spin": -8.0 + 6.0 * math.sin(w), "lean": -6.0, "head": -20.0,
            "nu": -110.0 + 10.0 * math.sin(w), "ne": 20.0, "nw": -120.0, "fu": -70.0 + 8.0 * math.sin(w + 1.0),
            "fe": 30.0, "fhand": "open", "nf": b(10.0, -8.0, 10.0), "ff": b(-12.0, 0.0, 20.0),
            "eye": "dizzy", "mouth": "open"}


def tumble(t: float) -> Semantic:
    """Launched and spinning end over end, limbs splayed."""
    a = -360.0 * t
    return {**AIR, "y": -10.0, "spin": a, "spin_about": 80.0, "lean": -10.0, "head": a - 20.0, "nu": a - 130.0, "ne": 20.0,
            "nw": a - 160.0, "fu": a - 40.0, "fe": 30.0, "fw": a - 60.0, "fhand": "open",
            "nf": b(14.0, -26.0, 0.0), "ff": b(-20.0, -8.0, 20.0), "eye": "shut", "mouth": "open"}


def teeter(t: float) -> Semantic:
    """On the brink: pitched forward over the edge, arms windmilling."""
    w = W * t
    return S(y=4.0, lean=22.0 + 6.0 * math.sin(w), head=6.0, nu=-40.0 + 55.0 * math.sin(2 * w), ne=16.0,
             nw=-70.0 + 70.0 * math.sin(2 * w), fu=-90.0 + 60.0 * math.sin(2 * w + 1.6), fe=16.0,
             fw=-110.0 + 60.0 * math.sin(2 * w + 1.6), fhand="open",
             nf=g(18.0, 16.0 + 6.0 * math.sin(w + 1.0), 30.0), ff=g(-20.0), mouth="open", eye="open")


def block(t: float) -> Semantic:
    w = W * t
    return {**SHIELD, "y": 30.0 + 1.5 * math.sin(w), "fx.shield": 0.94 + 0.06 * math.sin(2 * w)}


#: Shielding: low and braced behind the far forearm, the wrench across the
#: body as a second bar.
SHIELD = S(y=30.0, lean=14.0, head=-10.0, fu=10.0, fe=150.0, fw=-150.0, nu=60.0, ne=118.0, nw=-30.0,
           nf=g(36.0), ff=g(-48.0), eye="angry", mouth="grit", **{"fx.shield": 1.0})


def prone(t: float) -> Semantic:
    w = W * t
    return {**ON_BACK, "y": 112.0 - 1.5 * math.sin(w), "head": -84.0 + 2.0 * math.sin(w)}


def dizzy(t: float) -> Semantic:
    w = W * t
    return S(y=14.0 + 3.0 * math.sin(2 * w), x=6.0 * math.sin(w), lean=4.0 + 10.0 * math.sin(w),
             head=-6.0 + 14.0 * math.sin(w + 0.8), nu=96.0 + 10.0 * math.sin(w), ne=20.0, nw=110.0,
             fu=80.0 - 14.0 * math.sin(w), fe=20.0, fhand="open", nf=g(20.0), ff=g(-30.0),
             eye="dizzy", mouth="open", **{"fx.stars": 1.0})


#: Asleep sitting down, slumped over his knees, the wrench across his lap.
SLEEP = S(x=-30.0, y=112.0, spin=-14.0, lean=30.0, head=36.0, nu=60.0, ne=60.0, nw=30.0, fu=50.0, fe=60.0,
          fw=0.0, nf=g(70.0, 0.0, 0.0), ff=g(46.0, 0.0, 0.0), eye="shut", mouth="open")


def sleep(t: float) -> Semantic:
    w = W * t
    return {**SLEEP, "lean": 30.0 + 3.0 * math.sin(w), "head": 36.0 + 4.0 * math.sin(w - 0.5),
            "y": 112.0 + 1.5 * math.sin(w), "fx.zzz": t}


#: Buried to the chest: the hips sunk below the ground line (the target masks
#: what is under the ground and draws the mound).
BURIED = S(y=150.0, lean=0.0, head=-6.0, nu=40.0, ne=60.0, nw=-60.0, fu=30.0, fe=70.0, fw=-80.0,
           nf=b(40.0, -110.0, 0.0), ff=b(20.0, -110.0, 0.0), eye="angry", mouth="grit", **{"fx.bury": 1.0})


def buried(t: float) -> Semantic:
    w = W * t
    return {**BURIED, "lean": 6.0 * math.sin(w), "head": -6.0 + 6.0 * math.sin(w + 1.0),
            "nu": 40.0 + 20.0 * math.sin(2 * w), "fu": 30.0 - 20.0 * math.sin(2 * w)}


def grab_hold(t: float) -> Semantic:
    w = W * t
    return {**GRAB_HOLD, "y": 18.0 + 1.5 * math.sin(w), "lean": 12.0 + 1.5 * math.sin(w)}


#: Holding a grabbed opponent at arm's length in the far fist, the wrench
#: cocked to pummel.
GRAB_HOLD = S(y=18.0, lean=12.0, head=-4.0, fz=REACH, fu=8.0, fe=22.0, fw=-30.0, fhand="fist", nu=146.0, ne=118.0,
              nw=-128.0, nf=g(36.0), ff=g(-44.0), eye="angry")


def grabbed(t: float) -> Semantic:
    """Held up by the collar, kicking."""
    w = W * t
    return S(x=-6.0, y=-20.0, lean=-12.0 + 4.0 * math.sin(w), head=-16.0, nu=-30.0 + 20.0 * math.sin(w), ne=60.0,
             nw=-70.0, fu=-50.0 - 20.0 * math.sin(w + 1.0), fe=70.0, fhand="open",
             nf=b(8.0 + 10.0 * math.sin(2 * w), -10.0, 20.0), ff=b(-8.0 - 10.0 * math.sin(2 * w), -16.0, 20.0),
             eye="shut", mouth="grit")


def wall_grab(t: float) -> Semantic:
    """Clinging to a wall ahead: far hand flat on it, boots braced."""
    w = W * t
    return {**WALL, "y": -10.0 + 1.5 * math.sin(w), "head": -8.0 + 2.0 * math.sin(w - 0.8)}


#: Clinging to a wall ahead: far hand flat on it high up, boots braced
#: against it, the wrench ready.
WALL = S(x=10.0, y=-46.0, lean=-10.0, head=-10.0, fu=-46.0, fe=12.0, fw=-70.0, fhand="open", fz=REACH,
         nu=30.0, ne=80.0, nw=-50.0, nf=g(58.0, 44.0, -62.0), ff=g(44.0, 96.0, -50.0), mouth="grit")


def wall_slide(t: float) -> Semantic:
    w = W * t
    return {**WALL, "y": -4.0 + 1.0 * math.sin(2 * w), "lean": -10.0, "head": -12.0, "fu": -20.0,
            "eye": "angry", "fx.wall_dust": 0.8 + 0.2 * math.sin(2 * w)}


def ledge_hang(t: float) -> Semantic:
    w = W * t
    return {**HANG, "lean": -4.0 + 3.0 * math.sin(w), "nf": b(6.0 + 6.0 * math.sin(w), -6.0, 10.0),
            "ff": b(-6.0 - 6.0 * math.sin(w), -2.0, 12.0)}


def climb(t: float) -> Semantic:
    """Up a ladder (or a pipe run) ahead of him, hand over hand, the wrench
    stowed."""
    u = (t * 2.0) % 1.0
    up = H.smooth01(u)
    flip = t >= 0.5
    hi, lo = -70.0, -10.0
    a_n = (lo + (hi - lo) * up) if not flip else (hi + (lo - hi) * up)
    a_f = (hi + (lo - hi) * up) if not flip else (lo + (hi - lo) * up)
    fn_lift = 20.0 + 30.0 * (up if flip else 1.0 - up)
    ff_lift = 20.0 + 30.0 * (1.0 - up if flip else up)
    return S(x=-4.0, y=-10.0 - 6.0 * math.sin(W * 2 * t), lean=-4.0, head=-16.0, wrench=0.0, nhand="open",
             nu=a_n, ne=40.0, nw=a_n - 40.0, fu=a_f, fe=40.0, fw=a_f - 40.0, fhand="open",
             nf=g(34.0, fn_lift, -20.0), ff=g(30.0, ff_lift, -20.0))


def swim(t: float) -> Semantic:
    """Breaststroke, head up, the wrench stowed."""
    w = W * t
    s = math.sin(w)
    return S(y=-30.0, spin=64.0, lean=0.0, head=-10.0, wrench=0.0, nhand="open", fhand="open",
             nu=-10.0 + 60.0 * s, ne=20.0 + 30.0 * max(0.0, s), nw=-10.0 + 60.0 * s,
             fu=-20.0 + 60.0 * s, fe=30.0, fw=-20.0 + 60.0 * s,
             nf=b(0.0, -30.0 + 30.0 * s, 20.0), ff=b(0.0, -10.0 - 20.0 * s, 20.0), mouth="closed",
             **{"fx.bubbles": t})


def hover(t: float) -> Semantic:
    w = W * t
    return {**AIR, "y": -8.0 + 4.0 * math.sin(w), "lean": 4.0, "head": -6.0, "nu": 20.0 + 6.0 * math.sin(w),
            "ne": 40.0, "nw": -40.0, "fu": 0.0 + 8.0 * math.sin(w + 1.0), "fe": 20.0, "fhand": "open",
            "nf": b(4.0, -10.0 + 4.0 * math.sin(w), 20.0), "ff": b(-8.0, -4.0, 26.0)}


def float_glide(t: float) -> Semantic:
    """A long glide: arms out like wings, body pitched into the wind."""
    w = W * t
    return {**AIR, "y": -10.0, "spin": 18.0 + 3.0 * math.sin(w), "lean": 6.0, "head": -10.0,
            "nu": -8.0 + 6.0 * math.sin(w), "ne": 6.0, "nw": -30.0, "fu": -14.0 + 6.0 * math.sin(w + 0.7),
            "fe": 6.0, "fhand": "open", "fw": -10.0, "nf": b(-6.0, -6.0, 30.0), "ff": b(-16.0, -2.0, 34.0),
            "fx.speed": 0.4}


def item_hold(t: float) -> Semantic:
    w = W * t
    return S(y=12.0 + 2.0 * math.sin(w), lean=7.0 + 1.0 * math.sin(w - 0.5), fz=REACH, fu=40.0, fe=64.0 + 3.0 * math.sin(w),
             fw=-30.0, fhand="fist", nu=52.0, ne=150.0, nw=-150.0)


def item_hold_crouch(t: float) -> Semantic:
    w = W * t
    return {**CROUCH, "y": 66.0 + 2.0 * math.sin(w), "fu": 30.0, "fe": 40.0, "fw": -20.0, "fz": REACH,
            "nu": 110.0, "ne": 20.0, "nw": 150.0}


def item_heavy_carry(t: float) -> Semantic:
    """A heavy item hoisted overhead in both hands, staggering along."""
    w = W * t
    p = S(y=18.0 - 4.0 * math.cos(2 * w), lean=-4.0, head=-6.0, wrench=0.0, nhand="open", fhand="open",
          nu=-70.0, ne=50.0, nw=-150.0, fu=-80.0, fe=50.0, fw=-160.0, mouth="grit")
    return gait(p, t, centres=(4.0, -16.0), stride=18.0, lift=10.0)


def aim(t: float) -> Semantic:
    w = W * t
    return S(y=14.0, lean=4.0, head=-2.0 + 1.0 * math.sin(w), analyzer=1.0, fz=REACH, fu=-4.0 + 1.5 * math.sin(w), fe=6.0,
             fw=-90.0, nu=104.0, ne=14.0, nw=146.0, nf=g(36.0), ff=g(-44.0), eye="angry",
             **{"fx.aim": 1.0})


def charge(t: float) -> Semantic:
    w = W * t
    return S(y=18.0 + 1.0 * math.sin(4 * w), lean=10.0, head=-6.0, analyzer=1.0, fz=REACH, fu=20.0, fe=60.0, fw=-90.0,
             nu=96.0, ne=20.0, nw=100.0, eye="angry", mouth="grit",
             **{"fx.analyzer_charge": 0.6 + 0.4 * math.sin(2 * w)})


def victory_hold(t: float) -> Semantic:
    w = W * t
    return S(y=4.0 + 1.5 * math.sin(w), lean=-2.0, head=-6.0 + 2.0 * math.sin(w - 0.5), nu=52.0, ne=150.0,
             nw=-150.0, fu=118.0, fe=60.0, fw=40.0, nf=g(26.0), ff=g(-30.0), mouth="smile")


def loss(t: float) -> Semantic:
    """A good sport: polite applause, the wrench stowed."""
    c = math.sin(W * 2.0 * t)
    return S(y=8.0, lean=6.0, head=6.0, wrench=0.0, nhand="open", fhand="open", fz=REACH,
             nu=50.0, ne=70.0 + 16.0 * c, nw=-40.0 + 10.0 * c, fu=56.0, fe=70.0 - 16.0 * c, fw=-50.0 - 10.0 * c,
             nf=g(18.0), ff=g(-26.0), mouth="smile", eye="shut" if c > 0.6 else "open")


def talk(t: float) -> Semantic:
    w = W * t
    return S(y=6.0 + 1.5 * math.sin(w), lean=3.0, head=-4.0 + 3.0 * math.sin(2 * w), fz=REACH,
             nu=88.0, ne=12.0, nw=96.0, fu=40.0 + 16.0 * math.sin(w), fe=70.0 + 20.0 * math.sin(w + 0.8),
             fw=-40.0 + 30.0 * math.sin(w), fhand="open", nf=g(18.0), ff=g(-24.0),
             mouth="open" if (t * 4.0) % 1.0 < 0.5 else "closed")


def interact(t: float) -> Semantic:
    """Working a bolt in front of him: the wrench ratcheting in short arcs,
    the far hand steadying the work."""
    u = (t * 2.0) % 1.0
    r = 34.0 * (H.smooth01(u / 0.6) if u < 0.6 else 1.0 - H.smooth01((u - 0.6) / 0.4))
    return S(y=20.0, lean=16.0, head=6.0, fz=REACH, nu=30.0, ne=40.0 + r * 0.4, nw=-20.0 + r, fu=10.0, fe=40.0, fw=0.0,
             fhand="open", nf=g(30.0), ff=g(-40.0), mouth="grit" if u < 0.6 else "closed")


def sit(t: float) -> Semantic:
    w = W * t
    return {**SLEEP, "spin": -10.0, "lean": 16.0 + 2.0 * math.sin(w), "head": -2.0 + 3.0 * math.sin(w - 0.6),
            "nu": 50.0, "ne": 50.0, "nw": -40.0, "fu": 60.0, "fe": 50.0, "fw": 0.0, "fhand": "open",
            "eye": "shut" if 0.7 < t < 0.8 else "open", "mouth": "closed"}


def charge_hold(pose: Semantic, amount: float = 2.0):
    def fn(t: float) -> Semantic:
        p = dict(pose)
        shake(amount)(t, p)
        p["fx.charge"] = 0.7 + 0.3 * math.sin(TAU * 2.0 * t)
        return p
    return fn


# --- one-shot clips --------------------------------------------------------------------

#: Return to stance (a key that resets everything).
HOME = S()

LOCOMOTION = {
    "walk_stop": clip([
        (0.0, {**walk(0.25)}),
        (0.2, {"x": 6, "y": 18, "lean": -6, "head": -6, "nf": g(44), "ff": g(-34, 6, -10), "nu": 60, "ne": 140,
               "nw": -140, "fu": 40, "fe": 40, "fw": -40, "fx.dust": 1.0, "ease": "out"}),
        (0.6, {"x": 2, "y": 14, "lean": 10, "head": 0, "ff": g(-40), "fx.dust": 0.3}),
        (1.0, HOME),
    ]),
    "turnaround": clip([
        (0.0, {}),
        (0.2, {"y": 24, "lean": -12, "head": -14, "nu": 110, "ne": 60, "nw": 160, "fu": 100, "fe": 30,
               "nf": g(40, 0, -10), "ff": g(-34, 8, 10), "ease": "out"}),
        (0.4, {"y": 8, "lean": -2, "head": -4, "nu": 40, "ne": 130, "nw": -120, "fu": 40, "fe": 120,
               "nf": g(24, 14, 0), "ff": g(-22, 4), "fx.dust": 0.8}),
        (0.7, {"y": 16, "lean": 10, "nf": g(36), "ff": g(-42)}),
        (1.0, HOME),
    ]),
    "dash_startup": clip([
        (0.0, {}),
        (0.33, {"y": 30, "lean": 14, "head": -10, "nu": 110, "ne": 40, "nw": 150, "fu": 30, "fe": 80,
                "nf": g(30), "ff": g(-46), "ease": "out"}),
        (0.67, {"x": 10, "y": 10, "lean": 30, "head": -14, "nu": 140, "ne": 16, "nw": 165, "fu": -10, "fe": 90,
                "nf": g(60, 10, -10), "ff": g(-50, 0, 30), "fx.dust_trail": 1.0, "fx.speed": 0.5, "mouth": "grit",
                "ease": "in"}),
        (1.0, {**dash(0.0)}),
    ]),
    "stumble": clip([
        (0.0, {}),
        (0.17, {"x": 6, "y": 8, "lean": 30, "head": 10, "nu": -40, "ne": 10, "nw": -60, "fu": -60, "fe": 10,
                "fhand": "open", "nf": g(56, 10, 20), "ff": g(-40, 14, -10), "eye": "shut", "mouth": "open"}),
        (0.33, {"x": 14, "y": 22, "lean": 40, "nu": -120, "nw": -150, "fu": 20, "nf": g(66), "ff": g(-30, 22, 0)}),
        (0.5, {"x": 10, "y": 18, "lean": 28, "nu": 40, "nw": 20, "fu": -100, "ff": g(4, 0), "eye": "open"}),
        (0.67, {"x": 4, "y": 16, "lean": 14, "nu": 70, "ne": 90, "nw": -60, "fu": 40, "fe": 90, "fhand": "fist"}),
        (1.0, HOME),
    ]),
    "crouch_start": clip([(0.0, {}), (0.67, {**CROUCH, "y": 74, "lean": 30, "ease": "out"}), (1.0, CROUCH)]),
    "crouch_end": clip([(0.0, CROUCH), (0.33, {**CROUCH, "y": 50}), (1.0, HOME)]),
    "jump_squat": clip([(0.0, {}), (0.67, {**CROUCH, "y": 58, "lean": 16, "nu": 100, "ne": 50, "nw": 120,
                                            "fu": 90, "fe": 40, "ease": "out"}),
                        (1.0, {**CROUCH, "y": 50, "lean": 12, "nu": 110, "ne": 40, "nw": 140, "fu": 100,
                               "fe": 30})]),
    "jump": clip([
        (0.0, {"y": 8, "lean": 2, "head": -14, "nu": -40, "ne": 20, "nw": -80, "fu": -60, "fe": 20, "fhand": "open",
               "nf": b(10, 0, 30), "ff": b(-14, 0, 40), "fx.dust": 1.0}),
        (0.4, {"y": -4, "lean": 4, "head": -10, "nu": 0, "ne": 50, "nw": -60, "fu": -20, "fe": 50,
               "nf": b(16, -24, 0), "ff": b(-10, -10, 20), "fx.dust": 0.0}),
        (1.0, {**AIR}),
    ], base=AIR),
    "double_jump": clip([
        (0.0, {**AIR, "spin": 0, "spin_about": 70}),
        (0.14, {"spin": 30, "nf": b(30, -70, -20), "ff": b(16, -60, 0), "nu": 0, "ne": 80, "nw": 0, "fu": 0, "fe": 90,
                "ease": "in"}),
        (0.57, {"spin": 250, "ease": "lin"}),
        (0.86, {"spin": 350, "nf": b(18, -40, -20), "ff": b(-6, -22, 10), "ease": "out"}),
        (1.0, {"spin": 360, "nu": 58, "ne": 92, "nw": -44, "fu": 36, "fe": 98}),
    ], base=AIR, extra=body_arms),
    "land": clip([
        (0.0, {**AIR}),
        (0.25, {"y": 44, "lean": 22, "head": -8, "nf": g(40), "ff": g(-46), "nu": 90, "ne": 60, "nw": -10,
                "fu": 70, "fe": 60, "fx.dust": 1.0, "ease": "out"}),
        (1.0, HOME),
    ]),
    "land_hard": clip([
        (0.0, {**AIR}),
        (0.2, {"y": 72, "lean": 34, "head": 6, "nf": g(46), "ff": g(-56), "nu": 100, "ne": 30, "nw": 80,
               "fu": 100, "fe": 20, "fhand": "open", "eye": "shut", "mouth": "grit", "fx.dust": 1.0,
               "fx.shock": 1.0, "ease": "out"}),
        (0.6, {"y": 56, "lean": 26, "fx.shock": 0.0, "fx.dust": 0.4, "eye": "open"}),
        (1.0, HOME),
    ]),
    "land_recovery": clip([
        (0.0, {**AIR, "spin": -10}),
        (0.2, {"spin": 0, "y": 80, "lean": 40, "head": 10, "nf": g(48), "ff": g(-56), "nu": 110, "ne": 20, "nw": 120,
               "fu": 110, "fe": 20, "fhand": "open", "eye": "dizzy", "mouth": "open", "fx.dust": 1.0, "ease": "out"}),
        (0.6, {"y": 70, "lean": 32, "x": 4}),
        (1.0, {**HOME, "eye": "open"}),
    ]),
    "slide": clip([
        (0.0, {**run(0.25)}),
        (0.25, {"x": 10, "y": 96, "spin": -52, "lean": -6, "head": -40, "nu": -150, "ne": 10, "nw": -150,
                "fu": 150, "fe": 40, "fhand": "open", "nf": b(10, 0, 0), "ff": b(-30, -50, 10),
                "fx.dust_trail": 1.0, "fx.speed": 0.7, "mouth": "grit", "ease": "out"}),
        (0.75, {"x": 20, "y": 98, "fx.speed": 0.2}),
        (1.0, {"x": 12, "y": 70, "spin": -20, "lean": 20, "head": -10, "nu": 60, "ne": 90, "nw": -40, "fu": 60,
               "fe": 90, "fhand": "fist", "nf": g(46), "ff": g(-10, 0), "fx.dust_trail": 0.2}),
    ]),
    "roll": clip([
        (0.0, {"spin_about": 50}),
        (0.14, {"y": 60, "lean": 40, "head": 20, "nu": 60, "ne": 120, "nw": -10, "fu": 60, "fe": 120,
                "nf": g(40), "ff": g(-44), "eye": "shut", "ease": "out"}),
        (0.71, {"x": 18, "y": 70, "spin": 300, "nf": b(30, -80, 0), "ff": b(20, -70, 0), "ease": "lin"}),
        (0.86, {"x": 8, "y": 34, "spin": 360, "lean": 14, "nf": g(46), "ff": g(-30), "eye": "open"}),
        (1.0, {**HOME, "spin": 360}),
    ], extra=lambda t, p: p.update({"body_opacity": 0.55 if 0.1 < t < 0.8 else 1.0})),
    "roll_back": clip([
        (0.0, {"spin_about": 50}),
        (0.14, {"y": 60, "lean": 30, "head": 10, "nu": 60, "ne": 120, "nw": -10, "fu": 60, "fe": 120,
                "nf": g(40), "ff": g(-44), "eye": "shut", "ease": "out"}),
        (0.71, {"x": -18, "y": 70, "spin": -300, "nf": b(30, -80, 0), "ff": b(20, -70, 0), "ease": "lin"}),
        (0.86, {"x": -8, "y": 34, "spin": -360, "lean": 14, "nf": g(24), "ff": g(-50), "eye": "open"}),
        (1.0, {**HOME, "spin": -360}),
    ], extra=lambda t, p: p.update({"body_opacity": 0.55 if 0.1 < t < 0.8 else 1.0})),
    "spot_dodge": clip([
        (0.0, {}),
        (0.2, {"y": 70, "lean": -12, "head": -20, "spin": -10, "nu": 120, "ne": 30, "nw": 160, "fu": 110,
               "fe": 50, "nf": g(48), "ff": g(-56), "eye": "shut", "ease": "out"}),
        (0.6, {"y": 64, "lean": -8}),
        (1.0, HOME),
    ], extra=lambda t, p: p.update({"body_opacity": 0.55 if 0.12 < t < 0.75 else 1.0})),
    "air_dodge": clip([
        (0.0, {**AIR}),
        (0.17, {"y": -10, "spin": -18, "lean": 20, "head": 10, "nu": 90, "ne": 130, "nw": -10, "fu": 80, "fe": 130,
                "nf": b(30, -70, 0), "ff": b(20, -64, 0), "eye": "shut", "ease": "out"}),
        (0.67, {"spin": -10}),
        (1.0, {**AIR}),
    ], base=AIR, extra=lambda t, p: p.update({"body_opacity": 0.55 if 0.1 < t < 0.8 else 1.0})),
    "platform_drop": clip([
        (0.0, {}),
        (0.25, {**CROUCH, "y": 50, "ease": "out"}),
        (0.6, {**AIR, "y": 10, "nf": b(6, 0, 20), "ff": b(-8, 0, 24), "nu": -20, "ne": 40, "nw": -60, "fu": -10,
               "fe": 30, "fhand": "open"}),
        (1.0, {**AIR, "y": -2, "nf": b(10, -10, 10), "ff": b(-6, -4, 16)}),
    ]),
    "footstool_jump": clip([
        (0.0, {**AIR}),
        (0.2, {"y": 20, "lean": 20, "head": 10, "nf": b(10, 10, 30), "ff": b(-10, 10, 30), "nu": 40, "fu": 30,
               "fx.stomp": 1.0, "ease": "out"}),
        (0.5, {"y": -10, "lean": 0, "head": -16, "nf": b(14, -20, 0), "ff": b(-10, -10, 10), "nu": -50, "ne": 30,
               "nw": -80, "fu": -40, "fe": 30, "fhand": "open", "fx.stomp": 0.0}),
        (1.0, {**AIR}),
    ], base=AIR),
    "teeter_start": clip([
        (0.0, {}),
        (0.4, {"lean": 30, "head": 10, "nf": g(20, 20, 30), "ff": g(-22), "nu": -30, "ne": 10, "nw": -60, "fu": -90,
               "fe": 10, "fhand": "open", "eye": "open", "mouth": "open", "ease": "out"}),
        (1.0, {**teeter(0.0)}),
    ]),
}

DEFENSE = {
    "shield_raise": clip([(0.0, {}), (0.67, {**SHIELD, "fx.shield": 0.9, "ease": "out"}), (1.0, SHIELD)]),
    "shield_release": clip([(0.0, SHIELD), (0.5, {**SHIELD, "fx.shield": 0.3, "y": 24}), (1.0, {**HOME, "fx.shield": 0})]),
    "shield_hit": clip([
        (0.0, SHIELD),
        (0.25, {**SHIELD, "x": -12, "y": 34, "lean": 4, "head": -16, "eye": "shut", "fx.shield": 1.0,
                "fx.shield_flash": 1.0, "ease": "out"}),
        (0.75, {**SHIELD, "x": -8, "fx.shield_flash": 0.0}),
        (1.0, SHIELD),
    ]),
    "parry": clip([
        (0.0, {}),
        (0.17, {"y": 20, "lean": 4, "head": -6, "nu": 20, "ne": 120, "nw": -100, "fu": 70, "fe": 60, "fhand": "open",
                "eye": "angry", "ease": "out"}),
        (0.33, {"y": 22, "lean": -6, "nu": -10, "ne": 30, "nw": -40, "fu": 120, "fe": 20, "x": -4,
                "fx.parry": 1.0, "mouth": "grit", "ease": "in"}),
        (0.67, {"lean": 0, "nw": -30, "fx.parry": 0.3}),
        (1.0, {**HOME, "fx.parry": 0.0}),
    ]),
}

DAMAGE = {
    "hit": clip([
        (0.0, {}),
        (0.25, {"x": -10, "y": 18, "lean": -24, "head": -22, "nu": 150, "ne": 30, "nw": 170, "fu": -40, "fe": 30,
                "fhand": "open", "nf": g(40, 0, -10), "ff": g(-44), "eye": "shut", "mouth": "open",
                "fx.hit": 1.0, "ease": "out"}),
        (0.5, {"x": -8, "lean": -18, "head": -16, "fx.hit": 0.2}),
        (1.0, {**HOME, "x": -4, "fx.hit": 0.0}),
    ]),
    "launch": clip([
        (0.0, {**AIR, "fx.hit": 1.0}),
        (0.17, {"spin": -24, "lean": -20, "head": -30, "nu": -150, "ne": 20, "nw": -170, "fu": -100, "fe": 30,
                "fhand": "open", "nf": b(30, -10, 30), "ff": b(10, -30, 20), "eye": "shut", "mouth": "open",
                "fx.hit": 0.5, "fx.launch": 1.0, "ease": "out"}),
        (1.0, {"spin": -46, "lean": -14, "head": -40, "fx.hit": 0.0, "fx.launch": 0.6}),
    ], base=AIR),
    "meteor": clip([
        (0.0, {**AIR, "fx.hit": 1.0}),
        (0.17, {"y": 10, "spin": 30, "lean": 30, "head": 40, "nu": -110, "ne": 10, "nw": -120, "fu": -120, "fe": 10,
                "fhand": "open", "nf": b(-20, -40, 30), "ff": b(-30, -20, 30), "eye": "shut", "mouth": "open",
                "fx.hit": 0.5, "fx.meteor": 1.0, "ease": "out"}),
        (1.0, {"spin": 46, "fx.hit": 0.0, "fx.meteor": 0.6}),
    ], base=AIR),
    "impact": clip([
        (0.0, {**AIR, "spin": -40, "lean": -10}),
        (0.25, {"y": 40, "spin": -30, "lean": -20, "head": -30, "nu": 140, "ne": 10, "nw": 120, "fu": 150,
                "fe": 10, "fhand": "open", "nf": g(50, 20, -20), "ff": g(-20, 10, 0), "eye": "shut", "mouth": "open",
                "fx.shock": 1.0, "ease": "out"}),
        (1.0, {"y": 46, "spin": -28, "fx.shock": 0.0}),
    ], base=AIR),
    "splat": clip([
        (0.0, {**AIR, "spin": 50, "lean": 10, "eye": "shut", "mouth": "open"}),
        (0.33, {**ON_FRONT, "y": 128, "fx.dust": 1.0, "fx.shock": 0.8, "ease": "in"}),
        (0.5, {**ON_FRONT, "y": 126, "head": 70, "fx.shock": 0.0}),
        (1.0, {**ON_FRONT, "eye": "dizzy", "fx.dust": 0.2}),
    ]),
    "ground_bounce": clip([
        (0.0, {**AIR, "spin": -70, "eye": "shut", "mouth": "open"}),
        (0.17, {**ON_BACK, "y": 120, "fx.dust": 1.0, "fx.shock": 1.0, "ease": "in"}),
        (0.67, {**ON_BACK, "y": 40, "spin": -60, "head": -70, "nu": -100, "fu": -60, "fhand": "open",
                "nf": b(10, -40, 0), "ff": b(-10, -30, 0), "fx.shock": 0.0, "ease": "out"}),
        (1.0, {**ON_BACK, "y": 70, "spin": -66, "fx.dust": 0.0}),
    ]),
    "knockdown": clip([
        (0.0, {}),
        (0.2, {"x": -10, "y": 30, "lean": -30, "head": -30, "nu": 150, "ne": 20, "nw": 170, "fu": -60, "fe": 20,
               "fhand": "open", "nf": g(50, 20, -30), "ff": g(-30), "eye": "shut", "mouth": "open"}),
        (0.6, {**ON_BACK, "y": 104, "spin": -80, "ease": "in"}),
        (0.8, {**ON_BACK, "y": 120, "fx.dust": 1.0, "fx.shock": 0.6}),
        (1.0, {**ON_BACK, "fx.dust": 0.3, "fx.shock": 0.0}),
    ]),
    "prone_damage": clip([
        (0.0, ON_BACK),
        (0.25, {**ON_BACK, "y": 100, "spin": -84, "head": -70, "nu": -170, "fu": -140, "fhand": "open",
                "nf": b(10, -40, 0), "fx.hit": 1.0, "ease": "out"}),
        (1.0, {**ON_BACK, "fx.hit": 0.0}),
    ]),
    "getup": clip([
        (0.0, ON_BACK),
        (0.25, {**ON_BACK, "y": 110, "spin": -50, "head": -40, "lean": 20, "nu": 130, "ne": 20, "nw": -176,
                "fu": 120, "fe": 10, "fhand": "open", "nf": b(0, -60, 0), "ff": b(-4, -50, 0), "eye": "open",
                "mouth": "grit"}),
        (0.5, {"x": -10, "y": 80, "spin": -10, "lean": 30, "head": -10, "nf": g(40), "ff": g(-20, 0, 0),
               "nu": 100, "ne": 40, "nw": 140, "fu": 80, "fe": 30}),
        (0.75, {**CROUCH, "x": -4, "y": 40}),
        (1.0, HOME),
    ]),
    "getup_attack": clip([
        (0.0, ON_BACK),
        (0.25, {**ON_BACK, "y": 104, "spin": -40, "lean": 20, "head": -30, "nu": -175, "ne": 10, "nw": -175,
                "fu": 150, "fe": 20, "fhand": "open", "nf": g(20, 0, 0), "ff": g(-40, 0, 0), "eye": "angry",
                "mouth": "grit"}),
        (0.375, {"x": -10, "y": 88, "spin": -20, "lean": 30, "nu": 20, "ne": 0, "nw": 10, "fx.trail": 1.0,
                 "fx.spark": 1.0, "ease": "in"}),
        (0.5, {"nu": 0, "nw": -10, "fx.spark": 0.0}),
        (0.625, {"nu": 170, "nw": 175, "lean": 40, "fx.trail": 1.0, "fx.spark": 1.0, "ease": "in"}),
        (0.75, {**CROUCH, "x": -4, "y": 50, "fx.trail": 0.0, "fx.spark": 0.0}),
        (1.0, HOME),
    ]),
    # Back over the shoulders and up onto his feet.
    "getup_roll": clip([
        (0.0, ON_BACK),
        (0.25, {**ON_BACK, "y": 112, "spin": -120, "lean": 30, "head": -100, "nf": b(30, -90, 0),
                "ff": b(20, -80, 0), "nu": 60, "ne": 120, "nw": -10, "fu": 60, "fe": 120, "eye": "shut"}),
        (0.625, {"x": 0, "y": 20, "spin": -290, "head": -290, "ease": "lin"}),
        (0.75, {**CROUCH, "x": -6, "spin": -360, "y": 50, "eye": "open"}),
        (1.0, {**HOME, "x": -6, "spin": -360}),
    ], extra=lambda t, p: p.update({"body_opacity": 0.55 if 0.15 < t < 0.7 else 1.0})),
    "tech": clip([
        (0.0, {**AIR, "spin": -40, "eye": "shut"}),
        (0.2, {**CROUCH, "y": 76, "lean": 36, "eye": "angry", "fx.tech": 1.0, "fx.dust": 1.0, "ease": "out"}),
        (0.6, {**CROUCH, "y": 60, "fx.tech": 0.2}),
        (1.0, {**HOME, "fx.tech": 0.0}),
    ]),
    "tech_roll": clip([
        (0.0, {**AIR, "spin": -40, "eye": "shut"}),
        (0.17, {**CROUCH, "y": 76, "lean": 40, "fx.tech": 1.0, "fx.dust": 1.0, "ease": "out"}),
        (0.67, {"x": 16, "y": 70, "spin": 300, "nf": b(30, -80, 0), "ff": b(20, -70, 0), "fx.tech": 0.0,
                "ease": "lin"}),
        (0.83, {**CROUCH, "x": 8, "y": 40, "spin": 360}),
        (1.0, {**HOME, "spin": 360}),
    ], extra=lambda t, p: p.update({"body_opacity": 0.55 if 0.12 < t < 0.8 else 1.0})),
    "wall_tech": clip([
        (0.0, {**AIR, "spin": -20, "eye": "shut"}),
        (0.2, {**WALL, "x": 18, "y": -6, "lean": -20, "head": -20, "eye": "angry", "fx.tech": 1.0, "ease": "out"}),
        (0.6, {**WALL, "x": 14, "fx.tech": 0.2}),
        (1.0, {**AIR, "fx.tech": 0.0}),
    ]),
    "wall_tech_jump": clip([
        (0.0, {**AIR, "spin": -20}),
        (0.17, {**WALL, "x": 18, "lean": -20, "fx.tech": 1.0, "ease": "out"}),
        (0.5, {**AIR, "x": -10, "spin": -30, "lean": -10, "head": -20, "nf": b(30, -10, -40), "ff": b(16, -20, -30),
               "nu": -60, "fu": -40, "fe": 30, "fhand": "open", "fx.tech": 0.0, "ease": "out"}),
        (1.0, {**AIR, "x": -4}),
    ]),
    "ceiling_tech": clip([
        (0.0, {**AIR, "spin": 140, "eye": "shut", "spin_about": 80}),
        (0.2, {**AIR, "y": -10, "spin": 180, "head": 160, "nf": b(10, -10, 0), "ff": b(-10, -10, 0), "nu": -100,
               "fu": -100, "fhand": "open", "eye": "angry", "fx.tech": 1.0, "ease": "out"}),
        (0.6, {"spin": 200, "fx.tech": 0.2}),
        (1.0, {**AIR, "spin": 360, "fx.tech": 0.0}),
    ]),
    "shield_break_launch": clip([
        (0.0, {**SHIELD, "fx.shield_break": 1.0}),
        (0.33, {**AIR, "y": -30, "lean": -20, "head": -30, "nu": -130, "ne": 10, "nw": -150, "fu": -110, "fe": 10,
                "fhand": "open", "nf": b(10, 0, 30), "ff": b(-10, 0, 30), "eye": "dizzy", "mouth": "open",
                "fx.shield": 0.0, "fx.shield_break": 0.4, "ease": "out"}),
        (1.0, {**AIR, "y": -34, "lean": -14, "head": -40, "nu": -120, "nw": -140, "fu": -100, "fhand": "open",
               "nf": b(10, 0, 30), "ff": b(-10, 0, 30), "eye": "dizzy", "mouth": "open", "fx.shield_break": 0.0,
               "fx.stars": 1.0}),
    ]),
    "shield_break_fall": loop(lambda t: {**fall_special(t), "eye": "dizzy", "fx.stars": 1.0}),
    "shield_break_collapse": clip([
        (0.0, {**AIR, "y": -10, "eye": "dizzy", "mouth": "open", "fx.stars": 1.0}),
        (0.3, {**CROUCH, "y": 90, "lean": 40, "head": 40, "nu": 80, "ne": 10, "nw": 24, "fu": 100, "fe": 10,
               "fhand": "open", "eye": "dizzy", "fx.dust": 1.0, "ease": "in"}),
        (0.6, {"x": -30, "y": 112, "spin": -14, "lean": 10, "head": 30, "nf": g(70), "ff": g(46),
               "fx.dust": 0.2}),
        (1.0, {"x": -30, "y": 112, "spin": -14, "lean": 20, "head": 40}),
    ]),
    "shield_break_recover": clip([
        (0.0, {"x": -30, "y": 112, "spin": -14, "lean": 20, "head": 40, "nf": g(70), "ff": g(46), "nu": 80, "ne": 10,
               "nw": 24, "fu": 100, "fe": 10, "fhand": "open", "eye": "dizzy", "mouth": "open", "fx.stars": 1.0}),
        (0.4, {**CROUCH, "x": -10, "y": 60, "lean": 30, "head": 20, "fhand": "open", "eye": "dizzy"}),
        (1.0, {**dizzy(0.0)}),
    ]),
    "sleep_start": clip([
        (0.0, {}),
        (0.3, {"y": 14, "lean": -10, "head": -24, "nu": 80, "ne": 20, "nw": 100, "fu": -40, "fe": 140, "fhand": "open",
               "fw": -170, "mouth": "open", "eye": "shut"}),
        (0.6, {**SLEEP, "y": 90, "lean": 10, "head": 10, "ease": "in"}),
        (1.0, {**SLEEP, "fx.zzz": 0.0}),
    ]),
    "wake": clip([
        (0.0, SLEEP),
        (0.25, {**SLEEP, "lean": -6, "head": -20, "eye": "open", "mouth": "open", "fx.alert": 1.0, "ease": "out"}),
        (0.5, {**CROUCH, "x": -10, "y": 50, "fx.alert": 0.4}),
        (1.0, {**HOME, "fx.alert": 0.0}),
    ]),
    "bury_start": clip([
        (0.0, {**HOME, "fx.bury": 1.0, "eye": "shut", "mouth": "open"}),
        (0.4, {**BURIED, "y": 120, "lean": 6, "nu": -60, "fu": -50, "eye": "shut", "fx.dust": 1.0, "ease": "in"}),
        (1.0, BURIED),
    ]),
    "bury_escape": clip([
        (0.0, BURIED),
        (0.3, {**BURIED, "y": 140, "lean": 10, "nu": 80, "fu": 80, "ease": "out"}),
        (0.55, {**AIR, "y": -16, "lean": -4, "nu": -60, "ne": 30, "nw": -80, "fu": -50, "fe": 30, "fhand": "open",
                "fx.bury": 1.0, "fx.dust": 1.0, "ease": "out"}),
        (1.0, {**AIR, "fx.bury": 0.0, "fx.dust": 0.0}),
    ]),
    "death": clip([
        (0.0, {"fx.hit": 1.0}),
        (0.11, {"x": -10, "y": 20, "lean": -26, "head": -30, "nu": 150, "ne": 20, "nw": 170, "fu": -60, "fe": 20,
                "fhand": "open", "eye": "shut", "mouth": "open", "fx.hit": 0.6, "ease": "out"}),
        (0.33, {"x": -6, "y": 40, "lean": 20, "head": 20, "nu": 90, "ne": 10, "nw": 40, "fu": 90, "fe": 10,
                "nf": g(30, 0, 0), "ff": g(-30), "eye": "dizzy", "fx.hit": 0.0}),
        (0.56, {"x": -10, "y": 92, "lean": 30, "head": 30, "nf": g(48, 0, 0), "ff": g(-50), "eye": "dizzy"}),
        (0.78, {**ON_BACK, "y": 118, "spin": -84, "eye": "dead", "fx.dust": 1.0, "ease": "in"}),
        (1.0, {**ON_BACK, "eye": "dead", "fx.dust": 0.0}),
    ]),
}


# --- attacks ---------------------------------------------------------------------------

#: Where the first jab leaves the wrench, so the second starts from it.
JAB_END = S(x=6.0, lean=13.0, nu=20.0, ne=24.0, nw=28.0, nf=g(40.0), mouth="closed")
#: Where the second jab leaves it.
JAB2_END = S(x=8.0, lean=10.0, nu=-24.0, ne=40.0, nw=-70.0, nf=g(42.0))
#: The forward smash's loaded wind-up (also its charge pose).
FSMASH_WIND = S(x=-14.0, y=18.0, lean=-14.0, head=-6.0, nu=-150.0, ne=40.0, nw=-172.0, fu=30.0, fe=30.0, fw=-10.0,
                fhand="open", nf=g(42.0), ff=g(-50.0), mouth="grit", eye="angry")
#: Up smash coil: crouched with the wrench low and back.
USMASH_WIND = S(x=-4.0, y=44.0, lean=22.0, head=-14.0, nu=128.0, ne=10.0, nw=140.0, fu=40.0, fe=110.0, fw=-60.0,
                nf=g(40.0), ff=g(-48.0), mouth="grit", eye="angry")
#: Down smash: wrench raised overhead to hammer the floor.
DSMASH_WIND = S(x=-4.0, y=22.0, lean=-6.0, head=-10.0, nu=-104.0, ne=26.0, nw=-120.0, fu=60.0, fe=70.0, fw=-60.0,
                nf=g(40.0), ff=g(-48.0), mouth="grit", eye="angry")

ATTACKS = {
    # A quick forward swipe: the button players press first.
    "jab": clip([
        (0.0, {}),
        (0.167, {"x": -2, "nu": 92, "ne": 126, "nw": -112, "lean": 4, "ease": "out"}),
        (0.333, {"x": 8, "lean": 15, "nu": 12, "ne": 14, "nw": 8, "nf": g(42), "mouth": "grit",
                 "fx.trail": 1.0, "fx.spark": 1.0, "ease": "in"}),
        (0.5, {"nu": 18, "ne": 20, "nw": 22, "fx.spark": 0.4, "fx.trail": 0.0, "ease": "out"}),
        (0.667, {"fx.spark": 0.0}),
        (1.0, JAB_END),
    ]),
    # The backhand return.
    "jab_2": clip([
        (0.0, JAB_END),
        (0.167, {"nu": 40, "ne": 70, "nw": 70, "lean": 16, "ease": "out"}),
        (0.333, {"x": 10, "nu": -30, "ne": 34, "nw": -64, "lean": 9, "mouth": "grit", "fx.trail": 1.0,
                 "fx.spark": 1.0, "ease": "in"}),
        (0.5, {"nw": -76, "fx.spark": 0.4, "fx.trail": 0.0, "ease": "out"}),
        (0.667, {"fx.spark": 0.0}),
        (1.0, JAB2_END),
    ], base=JAB_END),
    # The finisher: up on his toes and a two-footed hammer blow.
    "jab_3": clip([
        (0.0, JAB2_END),
        (0.222, {"x": 0, "y": 4, "lean": -10, "head": -10, "nu": -128, "ne": 46, "nw": -168, "fu": 20, "fe": 60,
                 "nf": g(36, 6, 20), "ff": g(-40, 8, 20), "eye": "angry", "ease": "out"}),
        (0.333, {"x": 16, "y": 26, "lean": 30, "head": 4, "nu": 44, "ne": 0, "nw": 74, "fu": 110, "fe": 20,
                 "nf": g(58), "ff": g(-36), "mouth": "open", "fx.trail": 1.0, "fx.spark": 1.0, "fx.shock": 1.0,
                 "ease": "in"}),
        (0.556, {"y": 28, "nw": 80, "fx.trail": 0.0, "fx.spark": 0.3, "fx.shock": 0.3}),
        (1.0, {**HOME, "fx.shock": 0.0}),
    ], base=JAB2_END),
    # Running lunge into a low-to-high golf swing that pops the target up.
    "dash_attack": clip([
        (0.0, {**run(0.25)}),
        (0.25, {"x": 6, "y": 34, "lean": 30, "head": -10, "nu": 150, "ne": 10, "nw": 160, "fu": 20, "fe": 90,
                "nf": g(66), "ff": g(-56, 0, 30), "mouth": "grit", "fx.dust_trail": 1.0, "ease": "out"}),
        (0.375, {"x": 16, "y": 30, "lean": 18, "nu": 20, "ne": 0, "nw": 0, "fx.trail": 1.0, "fx.spark": 1.0,
                 "ease": "in"}),
        (0.5, {"x": 20, "y": 22, "lean": 6, "head": -16, "nu": -60, "ne": 20, "nw": -86, "fx.spark": 0.5,
               "fx.trail": 1.0, "ease": "out"}),
        (0.625, {"x": 18, "nu": -110, "ne": 60, "nw": -150, "fx.trail": 0.0, "fx.spark": 0.0, "fx.dust_trail": 0.0}),
        (1.0, {**HOME, "x": 8, "nf": g(44), "ff": g(-30)}),
    ]),
    # Forward tilt: a flat, waist-high sweep.
    "attack_side": clip([
        (0.0, {}),
        (0.286, {"x": -6, "lean": -6, "head": -6, "nu": 150, "ne": 36, "nw": 176, "fu": 40, "fe": 80,
                 "nf": g(34), "ff": g(-46), "eye": "angry", "ease": "out"}),
        (0.429, {"x": 12, "lean": 18, "head": 0, "nu": 2, "ne": 0, "nw": 2, "fu": 110, "fe": 40,
                 "nf": g(52), "mouth": "grit", "fx.trail": 1.0, "fx.spark": 1.0, "ease": "in"}),
        (0.571, {"nu": -8, "nw": -16, "fx.spark": 0.3, "fx.trail": 0.0, "ease": "out"}),
        (1.0, HOME),
    ]),
    # The old sheet's slash, now a diagonal downward chop.
    "slash": clip([
        (0.0, {}),
        (0.286, {"x": -6, "y": 6, "lean": -8, "head": -8, "nu": -112, "ne": 50, "nw": -152, "fu": 50, "fe": 60,
                 "eye": "angry", "ease": "out"}),
        (0.429, {"x": 12, "y": 18, "lean": 24, "head": 2, "nu": 46, "ne": 6, "nw": 56, "fu": 110, "fe": 30,
                 "nf": g(50), "mouth": "grit", "fx.trail": 1.0, "fx.spark": 1.0, "ease": "in"}),
        (0.571, {"nu": 56, "nw": 70, "fx.spark": 0.3, "fx.trail": 0.0, "ease": "out"}),
        (1.0, HOME),
    ]),
    # Up tilt: an arc from in front, over his head, to behind him.
    "attack_up": clip([
        (0.0, {}),
        (0.125, {"y": 24, "lean": 14, "nu": 54, "ne": 30, "nw": 28, "eye": "angry", "ease": "out"}),
        (0.25, {"y": 10, "lean": 2, "head": -14, "nu": -36, "ne": 10, "nw": -50, "fx.trail": 1.0, "ease": "in"}),
        (0.375, {"y": 6, "lean": -6, "head": -22, "nu": -92, "ne": 0, "nw": -96, "mouth": "grit", "fx.trail": 1.0,
                 "fx.spark": 1.0, "nf": g(34, 0, 10), "ease": "lin"}),
        (0.5, {"lean": -10, "nu": -140, "ne": 16, "nw": -156, "fx.spark": 0.3, "fx.trail": 1.0, "ease": "out"}),
        (0.625, {"fx.trail": 0.0, "fx.spark": 0.0}),
        (1.0, HOME),
    ]),
    # Down tilt: from the crouch, a quick sweep along the floor at the shins.
    "attack_down": clip([
        (0.0, CROUCH),
        (0.167, {**CROUCH, "nu": 130, "ne": 6, "nw": 156, "lean": 30, "ease": "out"}),
        (0.333, {**CROUCH, "x": 8, "nu": 44, "ne": -6, "nw": 12, "lean": 36, "head": -8, "nf": g(54), "mouth": "grit",
                 "fx.trail": 1.0, "fx.spark": 1.0, "fx.dust": 0.7, "ease": "in"}),
        (0.5, {"nu": 36, "nw": -2, "fx.spark": 0.3, "fx.trail": 0.0, "ease": "out"}),
        (1.0, CROUCH),
    ], base=CROUCH),
    "smash_forward": clip([
        (0.0, {}),
        (0.2, {**FSMASH_WIND, "ease": "out"}),
        (0.3, {**FSMASH_WIND, "x": -18, "lean": -18, "nu": -160, "nw": -178, "fx.charge": 0.6}),
        (0.4, {"x": 22, "y": 22, "lean": 34, "head": 6, "nu": 4, "ne": 0, "nw": 4, "fu": 150, "fe": 10, "fw": 160,
               "nf": g(78), "ff": g(-30, 0, 30), "mouth": "open", "fx.trail": 1.0, "fx.spark": 1.0, "fx.charge": 0.0,
               "fx.dust": 1.0, "ease": "in"}),
        (0.5, {"x": 26, "lean": 36, "nu": 14, "nw": 30, "fx.spark": 0.6, "fx.trail": 0.4, "ease": "out"}),
        (0.6, {"x": 24, "lean": 34, "nu": 60, "ne": 0, "nw": 84, "fx.spark": 0.0, "fx.trail": 0.0, "fx.dust": 0.3}),
        (1.0, HOME),
    ]),
    "smash_up": clip([
        (0.0, {}),
        (0.2, {**USMASH_WIND, "ease": "out"}),
        (0.3, {"x": 4, "y": 0, "lean": 4, "head": -24, "nu": 16, "ne": 0, "nw": -10, "fu": 60, "fe": 80,
               "nf": g(34, 10, 20), "ff": g(-40, 6, 30), "fx.trail": 1.0, "fx.dust": 1.0, "ease": "in"}),
        (0.4, {"x": 2, "y": -26, "lean": -6, "head": -30, "nu": -88, "ne": 0, "nw": -92, "fu": 90, "fe": 30,
               "nf": b(12, -20, 10), "ff": b(-10, -10, 20), "mouth": "open", "fx.trail": 1.0, "fx.spark": 1.0,
               "ease": "lin"}),
        (0.5, {"y": -30, "lean": -12, "nu": -132, "ne": 10, "nw": -150, "fx.spark": 0.4, "fx.trail": 1.0,
               "ease": "out"}),
        (0.7, {**HOME, "y": 30, "lean": 16, "nu": -140, "nw": -160, "nf": g(36), "ff": g(-44),
               "fx.trail": 0.0, "fx.spark": 0.0, "fx.dust": 0.6, "ease": "in"}),
        (1.0, {**HOME, "fx.dust": 0.0}),
    ]),
    "smash_down": clip([
        (0.0, {}),
        (0.2, {**DSMASH_WIND, "ease": "out"}),
        (0.3, {"x": 6, "y": 58, "lean": 44, "head": 4, "nu": 48, "ne": 0, "nw": 52, "fu": 110, "fe": 20,
               "nf": g(46), "ff": g(-52), "mouth": "open", "fx.trail": 1.0, "fx.spark": 1.0, "fx.shock": 1.0,
               "ease": "in"}),
        (0.4, {"nw": 56, "fx.trail": 0.0, "fx.spark": 0.3, "fx.shock": 0.4}),
        (0.5, {"x": 0, "y": 40, "lean": 10, "head": -10, "nu": -60, "ne": 40, "nw": -110, "fx.spark": 0.0,
               "fx.trail": 0.0, "fx.shock": 0.0, "ease": "out"}),
        (0.6, {"x": -8, "y": 62, "lean": 34, "head": 10, "nu": 166, "ne": 0, "nw": 172, "fu": 30, "fe": 60,
               "fx.trail": 1.0, "fx.spark": 1.0, "fx.shock_back": 1.0, "ease": "in"}),
        (0.7, {"nw": 168, "fx.trail": 0.0, "fx.spark": 0.3, "fx.shock_back": 0.4}),
        (1.0, {**HOME, "fx.shock_back": 0.0, "fx.spark": 0.0}),
    ]),
    "smash_forward_charge": loop(charge_hold(FSMASH_WIND)),
    "smash_up_charge": loop(charge_hold(USMASH_WIND)),
    "smash_down_charge": loop(charge_hold(DSMASH_WIND)),
    # Neutral air: the wrench held out at arm's length and the whole body
    # whirled once round it.
    "air_neutral": clip([
        (0.0, {**AIR, "nu": 58, "ne": 92, "nw": -44, "spin_about": 70}),
        (0.143, {"spin": 0, "nu": 0, "ne": 0, "nw": 0, "fu": 150, "fe": 20, "nf": b(14, -40, 0), "ff": b(-6, -30, 0),
                 "mouth": "grit", "fx.trail": 1.0, "fx.spark": 1.0, "ease": "out"}),
        (0.714, {"spin": 360, "fx.trail": 1.0, "fx.spark": 0.6, "ease": "lin"}),
        (0.857, {"spin": 360, "nu": 30, "ne": 40, "nw": -20, "fx.trail": 0.0, "fx.spark": 0.0, "ease": "out"}),
        (1.0, {**AIR, "spin": 360}),
    ], base=AIR, extra=body_arms),
    # Forward air: an overhead chop that spikes at the bottom of its arc.
    "air_forward": clip([
        (0.0, AIR),
        (0.25, {"lean": -16, "head": -16, "nu": -132, "ne": 42, "nw": -172, "nf": b(-6, -10, 30), "ff": b(-20, 0, 30),
                "eye": "angry", "ease": "out"}),
        (0.375, {"lean": 28, "head": 6, "nu": 58, "ne": 0, "nw": 88, "nf": b(30, -60, -10), "ff": b(10, -44, 10),
                 "mouth": "grit", "fx.trail": 1.0, "fx.spark": 1.0, "ease": "in"}),
        (0.5, {"nu": 66, "nw": 96, "fx.spark": 0.5, "fx.trail": 0.0, "ease": "out"}),
        (1.0, AIR),
    ], base=AIR),
    # Back air: the wrench flung out straight behind, body arched.
    "air_back": clip([
        (0.0, AIR),
        (0.143, {"lean": 16, "nu": 30, "ne": 80, "nw": -24, "head": 0, "ease": "out"}),
        (0.429, {"lean": -22, "head": -14, "nu": 176, "ne": 0, "nw": 180, "fu": 0, "fe": 40,
                 "nf": b(40, -50, -20), "ff": b(26, -30, -10), "mouth": "grit", "fx.trail": 1.0, "fx.spark": 1.0,
                 "ease": "in"}),
        (0.571, {"nw": 176, "fx.spark": 0.4, "fx.trail": 0.0, "ease": "out"}),
        (1.0, AIR),
    ], base=AIR),
    # Up air: a scissor-kick arc of the wrench from front to back overhead.
    "air_up": clip([
        (0.0, AIR),
        (0.143, {"spin": -10, "nu": 30, "ne": 20, "nw": 10, "ease": "out"}),
        (0.286, {"spin": -24, "lean": -10, "head": -30, "nu": -60, "ne": 0, "nw": -70, "nf": b(30, -20, -30),
                 "ff": b(0, 0, 0), "fx.trail": 1.0, "ease": "in"}),
        (0.429, {"spin": -34, "nu": -110, "nw": -112, "mouth": "grit", "fx.trail": 1.0, "fx.spark": 1.0,
                 "ease": "lin"}),
        (0.571, {"spin": -30, "nu": -160, "ne": 20, "nw": -176, "fx.spark": 0.3, "fx.trail": 1.0, "ease": "out"}),
        (0.714, {"fx.trail": 0.0, "fx.spark": 0.0}),
        (1.0, {**AIR, "spin": 0}),
    ], base=AIR),
    # Down air: a stall, then a plunge with the wrench driven straight down.
    "air_down": clip([
        (0.0, AIR),
        (0.25, {"y": -18, "lean": -4, "head": -10, "nu": -86, "ne": 10, "nw": -92, "fu": -40, "fe": 30,
                "nf": b(14, -50, 0), "ff": b(-6, -40, 0), "eye": "angry", "ease": "out"}),
        (0.375, {"y": 4, "lean": 12, "head": 20, "nu": 84, "ne": 0, "nw": 90, "fu": 100, "fe": 10,
                 "nf": b(0, 0, 20), "ff": b(-12, -4, 30), "mouth": "grit", "fx.trail": 1.0, "fx.spark": 1.0,
                 "fx.speed": 1.0, "ease": "in"}),
        (0.75, {"y": 8, "fx.trail": 0.0, "fx.spark": 0.6, "fx.speed": 1.0}),
        (1.0, {**AIR, "fx.speed": 0.0, "fx.spark": 0.0}),
    ], base=AIR),
    "air_land": clip([
        (0.0, {**AIR, "nu": 70, "nw": 60}),
        (0.25, {**CROUCH, "y": 50, "lean": 30, "fx.dust": 1.0, "ease": "out"}),
        (1.0, {**HOME, "fx.dust": 0.0}),
    ]),
    "stomp": clip([
        (0.0, {}),
        (0.333, {"y": 2, "lean": -4, "head": -10, "nf": g(40, 46, -20), "nu": 40, "ne": 120, "nw": -100, "fu": 30,
                 "fe": 30, "eye": "angry", "ease": "out"}),
        (0.5, {"y": 28, "lean": 20, "head": 6, "nf": g(48), "mouth": "grit", "fx.stomp": 1.0, "fx.shock": 1.0,
               "fx.dust": 1.0, "ease": "in"}),
        (0.667, {"fx.stomp": 0.4, "fx.shock": 0.3}),
        (1.0, {**HOME, "fx.stomp": 0.0, "fx.shock": 0.0, "fx.dust": 0.0}),
    ]),
}

SPECIALS = {
    # Neutral special: a sealed packet pulled from the satchel and thrown
    # overhand with the far arm (the projectile leaves at t=0.5).
    "packet_toss": clip([
        (0.0, {}),
        (0.222, {"x": -4, "lean": 0, "head": -6, "fu": 136, "fe": 8, "fw": 150, "fhand": "open", "fz": REACH, "nu": 60,
                 "ne": 110, "nw": -40, "ease": "out"}),
        (0.333, {"fu": 120, "fe": 30, "fhand": "fist", "fx.packet_hold": 1.0}),
        (0.444, {"x": -8, "y": 14, "lean": -12, "head": -10, "fu": -150, "fe": 70, "fw": 160, "nf": g(40, 6, 10),
                 "nu": 120, "ne": 20, "nw": 150, "eye": "angry", "ease": "out"}),
        (0.556, {"x": 10, "y": 18, "lean": 22, "head": 0, "fu": 6, "fe": 0, "fw": 10, "fhand": "open",
                 "nf": g(50), "mouth": "open", "fx.packet_hold": 0.0, "fx.packet": 0.0, "ease": "in"}),
        (1.0, {**HOME, "fx.packet": 1.0, "ease": "lin"}),
    ], extra=lambda t, p: p.update({"fx.packet": 0.0 if t < 0.55 else (t - 0.55) / 0.45})),
    # Side special: the wrench spun up like a drill and driven forward.
    "torque_rush": clip([
        (0.0, {}),
        (0.2, {"x": -10, "y": 34, "lean": 10, "head": -10, "nu": 150, "ne": 10, "nw": 170, "fu": 40, "fe": 110,
               "nf": g(30), "ff": g(-54), "eye": "angry", "mouth": "grit", "ease": "out"}),
        (0.3, {"x": 14, "y": 18, "lean": 34, "head": -6, "nu": 0, "ne": 0, "nw": 0, "fu": 150, "fe": 10,
               "nf": g(60, 20, -20), "ff": g(-40, 30, 30), "fx.whirl": 1.0, "fx.speed": 1.0, "fx.dust": 1.0,
               "ease": "in"}),
        (0.7, {"x": 24, "y": 14, "lean": 36, "nf": g(64, 26, -20), "ff": g(-30, 34, 30), "fx.whirl": 1.0,
               "fx.speed": 1.0, "fx.dust": 0.0, "ease": "lin"}),
        (0.8, {"x": 20, "y": 30, "lean": 20, "nu": 20, "nw": 30, "nf": g(66), "ff": g(-26), "fx.whirl": 0.3,
               "fx.speed": 0.0, "fx.dust_trail": 1.0, "ease": "out"}),
        (1.0, {**HOME, "x": 10, "fx.whirl": 0.0, "fx.dust_trail": 0.0, "nf": g(46), "ff": g(-30)}),
    ], extra=lambda t, p: p.update({"nw": float(p["nw"]) + (40.0 * math.sin(TAU * 4 * t) if p.get("fx.whirl", 0) > 0.5 else 0.0)})),
    # Up special: the wrench slams the floor, a telescoping antenna mast
    # punches up under his boots and launches him, wrench whirling overhead.
    "antenna_launch": clip([
        (0.0, {}),
        (0.2, {"y": 56, "lean": 36, "head": 0, "nu": 70, "ne": 0, "nw": 90, "fu": 80, "fe": 40, "nf": g(40),
               "ff": g(-50), "mouth": "grit", "fx.shock": 1.0, "fx.mast": 0.0, "ease": "in"}),
        (0.3, {"y": 30, "lean": 10, "head": -20, "fx.mast": 0.4, "fx.shock": 0.5, "nf": b(10, 0, 20),
               "ff": b(-10, 0, 20)}),
        (0.5, {"y": -60, "lean": -4, "head": -26, "nu": -40, "ne": 46, "nw": -90, "fu": -70, "fe": 30, "fhand": "open",
               "nf": b(8, -6, 20), "ff": b(-8, 0, 24), "mouth": "open", "fx.mast": 1.0, "fx.whirl": 1.0,
               "fx.speed": 1.0, "fx.shock": 0.0, "ease": "out"}),
        (0.8, {"y": -64, "fx.mast": 0.3, "fx.whirl": 1.0}),
        (1.0, {**fall_special(0.0), "fx.mast": 0.0, "fx.whirl": 0.0, "fx.speed": 0.0}),
    ], extra=lambda t, p: p.update({"nw": float(p["nw"]) + (360.0 * 2 * t if p.get("fx.whirl", 0) > 0.5 else 0.0)})),
    # Down special: receive. The analyzer comes up to check what's coming; a
    # hit during the window is verified and answered (receive_counter).
    "receive": clip([
        (0.0, {}),
        (0.222, {"y": 20, "lean": -2, "head": -6, "analyzer": 1.0, "fz": REACH, "fu": 4, "fe": 64, "fw": -90, "nu": 112,
                 "ne": 14, "nw": 150, "nf": g(30), "ff": g(-48), "eye": "angry", "ease": "out"}),
        (0.333, {"fx.verify": 1.0}),
        (0.778, {"fx.verify": 1.0, "head": -4}),
        (1.0, {**HOME, "analyzer": 0.0, "fx.verify": 0.0}),
    ], extra=lambda t, p: p.update({"analyzer": 1.0 if 0.15 < t < 0.95 else 0.0})),
    "receive_counter": clip([
        (0.0, {"y": 20, "lean": -2, "head": -6, "analyzer": 1.0, "fz": REACH, "fu": 4, "fe": 64, "fw": -90, "nu": 112, "ne": 14,
               "nw": 150, "nf": g(30), "ff": g(-48), "eye": "angry", "fx.counter": 1.0}),
        (0.125, {"x": -6, "lean": -14, "nu": -150, "ne": 40, "nw": -176, "mouth": "grit", "fx.counter": 0.7,
                 "ease": "out"}),
        (0.25, {"x": 22, "y": 22, "lean": 34, "head": 4, "nu": 6, "ne": 0, "nw": 8, "fu": 140, "fe": 30,
                "nf": g(70), "ff": g(-34, 0, 30), "mouth": "open", "fx.trail": 1.0, "fx.spark": 1.0,
                "fx.counter": 0.3, "ease": "in"}),
        (0.375, {"nu": 20, "nw": 40, "fx.spark": 0.6, "fx.trail": 0.0}),
        (0.5, {"nu": 60, "nw": 84, "fx.spark": 0.0, "fx.counter": 0.0}),
        (1.0, {**HOME, "analyzer": 0.0}),
    ], extra=lambda t, p: p.update({"analyzer": 1.0 if t < 0.6 else 0.0})),
    # Final smash: the full handshake. Analyzer and wrench crossed, a burst
    # of keys and a lock springing open.
    "full_handshake": clip([
        (0.0, {}),
        (0.133, {"y": 20, "lean": -6, "head": -14, "analyzer": 1.0, "fz": REACH, "fu": -80, "fe": 20, "fw": -90, "nu": -110,
                 "ne": 20, "nw": -120, "eye": "angry", "mouth": "grit", "fx.final": 0.05, "ease": "out"}),
        (0.267, {"y": 24, "lean": 0, "fu": -60, "nu": -80, "nw": -100, "fx.final": 0.15}),
        (0.333, {"x": 6, "y": 30, "lean": 16, "head": -4, "fu": 0, "fe": 30, "fw": -80, "nu": 4, "ne": 40, "nw": -40,
                 "mouth": "open", "fx.final": 0.3, "fx.spark": 1.0, "ease": "in"}),
        (0.533, {"x": 0, "y": 32, "lean": -12, "head": -18, "fx.final": 0.6, "fx.spark": 0.0}),
        (0.8, {"x": -6, "y": 30, "lean": -16, "head": -20, "fx.final": 0.95}),
        (0.933, {**HOME, "analyzer": 0.0, "mouth": "smile", "fx.final": 1.0}),
        (1.0, {**HOME, "mouth": "smile", "fx.final": 0.0}),
    ]),
}

#: Grabs use the far hand: the wrench stays cocked in the near one.
GRABS = {
    "grab": clip([
        (0.0, {}),
        (0.167, {"x": -4, "lean": 2, "fu": 100, "fe": 60, "fw": 20, "fhand": "open", "fz": REACH, "ease": "out"}),
        (0.5, {"x": 12, "y": 18, "lean": 22, "head": -2, "fu": 4, "fe": 0, "fw": -10, "fhand": "open",
               "nu": 146, "ne": 118, "nw": -128, "nf": g(50), "eye": "angry", "ease": "in"}),
        (0.667, {"fhand": "fist"}),
        (1.0, GRAB_HOLD),
    ]),
    "pummel": clip([
        (0.0, GRAB_HOLD),
        (0.25, {**GRAB_HOLD, "nu": -40, "ne": 60, "nw": -130, "lean": 6, "ease": "out"}),
        (0.5, {**GRAB_HOLD, "nu": 30, "ne": 50, "nw": 30, "lean": 16, "mouth": "grit", "fx.spark": 0.8,
               "ease": "in"}),
        (1.0, GRAB_HOLD),
    ], base=GRAB_HOLD),
    "grab_release": clip([
        (0.0, GRAB_HOLD),
        (0.5, {**GRAB_HOLD, "x": 6, "fu": -10, "fe": 0, "fw": -80, "fhand": "open", "lean": 18, "ease": "out"}),
        (1.0, HOME),
    ], base=GRAB_HOLD),
    "throw_forward": clip([
        (0.0, GRAB_HOLD),
        (0.25, {**GRAB_HOLD, "x": -6, "lean": -6, "fu": 40, "fe": 80, "nu": -140, "ne": 40, "nw": -170, "ease": "out"}),
        (0.375, {"x": 14, "lean": 30, "fu": -4, "fe": 0, "fw": -80, "fhand": "open", "nu": 0, "ne": 0, "nw": 0,
                 "nf": g(60), "mouth": "open", "fx.trail": 1.0, "fx.spark": 1.0, "ease": "in"}),
        (0.5, {"nu": 20, "nw": 40, "fx.spark": 0.4, "fx.trail": 0.0}),
        (1.0, HOME),
    ], base=GRAB_HOLD),
    "throw_back": clip([
        (0.0, GRAB_HOLD),
        (0.25, {**GRAB_HOLD, "lean": 10, "fu": -40, "fe": 20, "fw": -60, "ease": "out"}),
        (0.5, {"x": -8, "lean": -24, "head": -20, "spin": -16, "fu": -150, "fe": 10, "fw": -170, "nu": 150, "ne": 10,
               "nw": 170, "nf": g(40, 10, 0), "ff": g(-56), "mouth": "grit", "ease": "in"}),
        (0.625, {"fu": 160, "fe": 10, "fw": 170, "fhand": "open", "fx.trail": 1.0, "fx.spark": 1.0, "nw": 176}),
        (0.75, {"fx.spark": 0.0, "fx.trail": 0.0, "spin": -6}),
        (1.0, HOME),
    ], base=GRAB_HOLD),
    "throw_up": clip([
        (0.0, GRAB_HOLD),
        (0.25, {**GRAB_HOLD, "y": 36, "lean": 20, "fu": 30, "fe": 60, "nu": 130, "ne": 10, "nw": 150, "ease": "out"}),
        (0.375, {"y": 6, "lean": -4, "head": -24, "fu": -86, "fe": 0, "fw": -90, "fhand": "open", "ease": "in"}),
        (0.5, {"y": -2, "lean": -10, "head": -30, "nu": -84, "ne": 0, "nw": -90, "fx.trail": 1.0, "fx.spark": 1.0,
               "mouth": "open", "ease": "in"}),
        (0.625, {"nu": -110, "nw": -120, "fx.spark": 0.3, "fx.trail": 0.0}),
        (1.0, HOME),
    ], base=GRAB_HOLD),
    "throw_down": clip([
        (0.0, GRAB_HOLD),
        (0.25, {**GRAB_HOLD, "y": 6, "lean": 0, "fu": -40, "fe": 30, "ease": "out"}),
        (0.375, {"y": 40, "lean": 40, "head": 10, "fu": 80, "fe": 0, "fw": 90, "fhand": "open", "fx.shock": 1.0,
                 "ease": "in"}),
        (0.5, {"nu": -100, "ne": 30, "nw": -120, "fx.shock": 0.3}),
        (0.625, {"y": 52, "lean": 46, "nu": 46, "ne": 0, "nw": 50, "mouth": "grit", "fx.spark": 1.0, "fx.trail": 1.0,
                 "ease": "in"}),
        (0.75, {"fx.spark": 0.3, "fx.trail": 0.0, "fx.shock": 0.0}),
        (1.0, HOME),
    ], base=GRAB_HOLD),
    "grabbed_pummel": clip([
        (0.0, {**grabbed(0.0)}),
        (0.25, {**grabbed(0.0), "lean": -24, "head": -30, "eye": "shut", "mouth": "open", "fx.hit": 1.0,
                "ease": "out"}),
        (1.0, {**grabbed(0.0), "fx.hit": 0.0}),
    ]),
    "grab_escape": clip([
        (0.0, {**grabbed(0.0)}),
        (0.33, {"x": -14, "y": -14, "lean": -20, "head": -10, "nu": 120, "ne": 40, "nw": 150, "fu": 60, "fe": 30,
                "fhand": "open", "nf": b(30, -30, -30), "ff": b(10, -20, -20), "eye": "angry", "mouth": "grit",
                "ease": "out"}),
        (0.67, {**CROUCH, "x": -20, "y": 40}),
        (1.0, {**HOME, "x": -16}),
    ]),
}

LEDGE = {
    "wall_jump": clip([
        (0.0, WALL),
        (0.2, {**WALL, "x": 18, "y": 0, "lean": 0, "nf": b(40, -40, -60), "ff": b(26, -60, -50), "ease": "out"}),
        (0.5, {**AIR, "x": -10, "spin": -20, "lean": -14, "head": -20, "nf": b(20, -6, -40), "ff": b(10, -14, -30),
               "nu": -40, "ne": 40, "nw": -80, "fu": -50, "fe": 30, "fhand": "open", "fx.dust": 1.0, "ease": "out"}),
        (1.0, {**AIR, "x": -6, "fx.dust": 0.0}),
    ]),
    "ledge_catch": clip([
        (0.0, {**fall(0.0)}),
        (0.4, {**HANG, "y": 50, "lean": -10, "nf": b(20, -20, 0), "ff": b(0, -10, 0), "mouth": "grit",
               "ease": "out"}),
        (1.0, HANG),
    ]),
    "ledge_getup": clip([
        (0.0, HANG),
        (0.33, {**HANG, "y": -30, "lean": 20, "head": 0, "nu": 40, "ne": 100, "nw": -20, "fu": 50, "fe": 100,
                "fhand": "fist", "nf": b(30, -60, 0), "ff": b(10, -40, 0), "ease": "out"}),
        (0.67, {**CROUCH, "x": 0, "y": -120, "nf": g(40, 170, 0), "ff": g(-20, 170, 0)}),
        (1.0, {**HOME, "x": 10, "y": -150, "nf": g(44, 168), "ff": g(-30, 168)}),
    ]),
    "ledge_climb": clip([
        (0.0, HANG),
        (0.2, {**HANG, "y": 10, "lean": -2, "nu": -40, "fu": -40, "mouth": "grit"}),
        (0.5, {**HANG, "y": -60, "lean": 26, "head": 6, "nu": 50, "ne": 100, "nw": -10, "fu": 60, "fe": 90,
               "fhand": "fist", "nf": b(40, -70, 0), "ff": b(10, -30, 20), "ease": "in"}),
        (0.8, {**CROUCH, "x": 0, "y": -110, "nf": g(40, 170), "ff": g(-30, 170)}),
        (1.0, {**HOME, "x": 6, "y": -150, "nf": g(40, 168), "ff": g(-34, 168)}),
    ]),
    "ledge_getup_attack": clip([
        (0.0, HANG),
        (0.25, {**HANG, "y": -40, "lean": 24, "nu": -40, "ne": 30, "nw": -100, "fu": 50, "fe": 100, "fhand": "fist",
                "nf": b(30, -60, 0), "ff": b(10, -40, 0), "ease": "out"}),
        (0.375, {**CROUCH, "x": 6, "y": -112, "nf": g(44, 170), "ff": g(-30, 170), "nu": 160, "ne": 10, "nw": 170}),
        (0.5, {"x": 16, "lean": 34, "nu": 24, "ne": 0, "nw": 14, "mouth": "grit", "fx.trail": 1.0, "fx.spark": 1.0,
               "ease": "in"}),
        (0.625, {"nw": 4, "fx.spark": 0.3, "fx.trail": 0.0}),
        (1.0, {**HOME, "x": 10, "y": -150, "nf": g(44, 168), "ff": g(-30, 168)}),
    ]),
    "ledge_roll": clip([
        (0.0, {**HANG, "spin_about": 50}),
        (0.25, {**HANG, "y": -40, "lean": 30, "nu": 50, "ne": 110, "nw": -10, "fu": 50, "fe": 110, "fhand": "fist",
                "nf": b(30, -70, 0), "ff": b(20, -60, 0), "eye": "shut", "ease": "out"}),
        (0.75, {"x": 50, "y": -100, "spin": 300, "lean": 40, "ease": "lin"}),
        (0.875, {**CROUCH, "x": 54, "y": -116, "spin": 360, "nf": g(80, 170), "ff": g(30, 170), "eye": "open"}),
        (1.0, {**HOME, "x": 50, "y": -150, "spin": 360, "nf": g(84, 168), "ff": g(20, 168)}),
    ], extra=lambda t, p: p.update({"body_opacity": 0.55 if 0.2 < t < 0.85 else 1.0})),
    "ledge_jump": clip([
        (0.0, HANG),
        (0.29, {**HANG, "y": 0, "lean": 10, "nf": b(30, -50, 0), "ff": b(16, -40, 0), "ease": "out"}),
        (0.57, {**AIR, "x": 0, "y": -70, "lean": 0, "head": -20, "nu": -40, "ne": 40, "nw": -60, "fu": -70, "fe": 20,
                "fhand": "open", "nf": b(10, 0, 30), "ff": b(-10, 0, 30), "ease": "out"}),
        (1.0, {**AIR, "y": -80}),
    ]),
    "ledge_drop": clip([
        (0.0, HANG),
        (0.5, {**fall(0.0), "y": 30, "ease": "out"}),
        (1.0, {**fall(0.25), "y": 40}),
    ]),
}

ITEMS = {
    "pickup": clip([
        (0.0, {}),
        (0.33, {**CROUCH, "y": 80, "lean": 50, "head": 10, "fu": 80, "fe": 0, "fw": 90, "fhand": "open", "fz": REACH,
                "ease": "out"}),
        (0.5, {"fhand": "fist"}),
        (1.0, {**item_hold(0.0)}),
    ]),
    "item_heavy_pickup": clip([
        (0.0, {}),
        (0.25, {**CROUCH, "y": 84, "lean": 40, "head": 10, "wrench": 0.0, "nhand": "open", "fhand": "open",
                "nu": 80, "ne": 10, "nw": 90, "fu": 80, "fe": 10, "fw": 90, "ease": "out"}),
        (0.5, {"y": 60, "lean": 20, "nu": 20, "ne": 60, "nw": -60, "fu": 20, "fe": 60, "fw": -60, "mouth": "grit"}),
        (1.0, {**item_heavy_carry(0.0)}),
    ]),
    "throw": clip([
        (0.0, {**item_hold(0.0)}),
        (0.33, {"x": -8, "y": 14, "lean": -12, "head": -10, "fu": -150, "fe": 60, "fw": 160, "nf": g(40, 6, 10),
                "ease": "out"}),
        (0.5, {"x": 10, "y": 18, "lean": 24, "head": 0, "fu": 8, "fe": 0, "fw": 10, "fhand": "open", "nf": g(50),
               "mouth": "open", "fx.toss": 1.0, "ease": "in"}),
        (0.67, {"fx.toss": 0.0}),
        (1.0, HOME),
    ]),
    "item_drop": clip([
        (0.0, {**item_hold(0.0)}),
        (0.5, {"fu": 60, "fe": 20, "fw": 60, "fhand": "open", "y": 18, "lean": 14, "ease": "out"}),
        (1.0, HOME),
    ]),
    "item_swing": clip([
        (0.0, {**item_hold(0.0)}),
        (0.286, {"x": -6, "lean": -8, "fu": -140, "fe": 40, "fw": -170, "ease": "out"}),
        (0.429, {"x": 12, "lean": 22, "fu": 10, "fe": 0, "fw": 10, "nf": g(50), "mouth": "grit", "ease": "in"}),
        (0.571, {"fu": 40, "fw": 50}),
        (1.0, {**item_hold(0.0)}),
    ]),
}

GADGETS = {
    "shoot": clip([
        (0.0, {**aim(0.0)}),
        (0.333, {**aim(0.0), "x": -6, "lean": -6, "fu": -14, "head": -6, "fx.zap": 1.0, "fx.aim": 0.0,
                 "mouth": "grit", "ease": "out"}),
        (0.667, {"x": -4, "lean": 0, "fu": -6, "fx.zap": 0.3}),
        (1.0, {**aim(0.0), "fx.zap": 0.0}),
    ]),
    "cast": clip([
        (0.0, {}),
        (0.286, {"y": 16, "lean": -6, "head": -24, "analyzer": 1.0, "fz": REACH, "fu": -80, "fe": 10, "fw": -90, "nu": 100,
                 "ne": 10, "nw": 120, "eye": "angry", "ease": "out"}),
        (0.429, {"fx.waves": 1.0, "mouth": "open"}),
        (0.857, {"fx.waves": 1.0}),
        (1.0, {**HOME, "analyzer": 0.0, "fx.waves": 0.0}),
    ], extra=lambda t, p: p.update({"analyzer": 1.0 if 0.15 < t < 0.95 else 0.0})),
    "blink_out": clip([
        (0.0, {"fx.blink": 0.0}),
        (0.4, {"y": 30, "lean": 20, "nu": 60, "ne": 120, "nw": -20, "fu": 50, "fe": 120, "eye": "shut",
               "fx.blink": 0.5, "body_opacity": 0.8, "ease": "out"}),
        (1.0, {"y": 20, "lean": 10, "fx.blink": 1.0, "body_opacity": 0.0, "ease": "in"}),
    ], extra=lambda t, p: p.setdefault("body_opacity", 1.0)),
    "blink_in": clip([
        (0.0, {"y": 20, "lean": 10, "eye": "shut", "fx.blink": 1.0, "body_opacity": 0.0}),
        (0.6, {"y": 30, "lean": 20, "fx.blink": 0.5, "body_opacity": 0.85, "ease": "out"}),
        (1.0, {**HOME, "fx.blink": 0.0, "body_opacity": 1.0}),
    ]),
}

SHOW = {
    "entrance": clip([
        (0.0, {**CROUCH, "y": 80, "lean": 40, "head": 20, "eye": "shut", "fx.blink": 1.0, "body_opacity": 0.0}),
        (0.182, {"fx.blink": 0.7, "body_opacity": 1.0, "ease": "out"}),
        (0.364, {"y": 6, "lean": -4, "head": -12, "eye": "open", "fx.blink": 0.0, "nu": 52, "ne": 150, "nw": -150,
                 "fu": 60, "fe": 90, "fw": -90}),
        (0.545, {"head": -4, "nu": 30, "ne": 70, "nw": -60}),
        (0.636, {"nw": 120, "ease": "lin"}),
        (0.727, {"nw": 300, "ease": "lin"}),
        (0.818, {**HOME, "nw": 302, "mouth": "smile", "eye": "angry", "fx.glint": 1.0, "ease": "out"}),
        (1.0, {**HOME, "fx.glint": 0.0}),
    ], extra=lambda t, p: p.setdefault("body_opacity", 1.0)),
    "celebrate": clip([
        (0.0, {}),
        (0.111, {"y": 30, "lean": 14, "ease": "out"}),
        (0.333, {**AIR, "y": -40, "lean": -4, "head": -20, "nu": -80, "ne": 10, "nw": -90, "fu": -70, "fe": 20,
                 "fhand": "fist", "mouth": "open", "ease": "out"}),
        (0.444, {"nw": 90, "ease": "lin"}),
        (0.556, {"y": -30, "nw": 270, "ease": "lin"}),
        (0.667, {**HOME, "y": 18, "nw": 270, "nu": -70, "ne": 20, "fu": 120, "fe": 60, "fw": 40, "mouth": "smile",
                 "fx.dust": 1.0, "ease": "in"}),
        (0.778, {"y": 6, "nw": 268, "fx.dust": 0.0, "fx.glint": 1.0}),
        (1.0, {**victory_hold(0.0), "nw": 210, "fx.glint": 0.0}),
    ]),
    "taunt": clip([
        (0.0, {}),
        (0.111, {"y": 8, "lean": 0, "head": -6, "nu": 30, "ne": 60, "nw": -40, "fu": 40, "fe": 80, "fw": -60,
                 "fhand": "open", "mouth": "smile", "ease": "out"}),
        (0.333, {"nw": 320, "ease": "lin"}),
        (0.556, {"nw": 680, "ease": "lin"}),
        (0.667, {"nu": 40, "ne": 90, "nw": 720 + 20, "fu": 30, "fe": 90, "fw": -40, "ease": "out"}),
        (0.778, {"nw": 720 + 40, "fx.tap": 1.0}),
        (0.889, {"nw": 720 + 20, "fx.tap": 0.0, "eye": "shut"}),
        (1.0, {**HOME, "nw": 720 - 58, "mouth": "smile"}),
    ]),
}

LOOPS = {
    "idle": idle, "idle_side": idle_side, "idle_look_up": idle_look_up,
    "walk": walk, "dash": dash, "run": run, "crouch": crouch, "crouch_walk": crouch_walk,
    "fall": fall, "fall_special": fall_special, "tumble": tumble, "teeter": teeter, "block": block,
    "prone": prone, "dizzy": dizzy, "sleep": sleep, "buried": buried, "grab_hold": grab_hold, "grabbed": grabbed,
    "wall_grab": wall_grab, "wall_slide": wall_slide, "ledge_grab": ledge_hang, "climb": climb, "swim": swim,
    "hover": hover, "float_glide": float_glide, "item_hold": item_hold, "item_hold_crouch": item_hold_crouch,
    "item_heavy_carry": item_heavy_carry, "aim": aim, "charge": charge, "victory_hold": victory_hold, "loss": loss,
    "talk": talk, "interact": interact, "sit": sit,
}

CLIPS: Dict[str, Callable[[int, int, float], Pose]] = {name: loop(fn) for name, fn in LOOPS.items()}
for group in (LOCOMOTION, DEFENSE, DAMAGE, ATTACKS, SPECIALS, GRABS, LEDGE, ITEMS, GADGETS, SHOW):
    for name, fn in group.items():
        assert name not in CLIPS, name
        CLIPS[name] = fn

ROWS = [(name, frames, ms, name in BOB_LOOPS) for name, frames, ms in BOB_ROWS if name not in BOB_FRONT_ROWS]

def _substeps() -> Dict[str, int]:
    """Swing clips are keyed between frames too (``CreatureSpec.substeps``),
    so the smear and the hit volume ``bob.py`` measures follow the arc."""
    out = {}
    for name, frames, _ms, _loop in ROWS:
        fn = CLIPS[name]
        n = max(1, frames - 1)
        if any(fn(i, frames, i / n).get(k, 0.0) > 0.0 for i in range(frames) for k in SWING_FX):
            out[name] = 3
    return out


#: Effects that mark a frame as part of a swing.
SWING_FX = ("fx.trail", "fx.whirl", "fx.spark")

SPEC = H.humanoid_spec(
    name="bob",
    svg_path=SVG,
    rig_path=PKG / "targets" / "characters" / "rigged" / "bob" / "bob_side.rig.json",
    view_label="Bob - Side Right",
    # Drawn at 720x640 units, published at half: Bob stands ~188 px tall in a
    # 360x320 frame with room for a full overhead swing, a long reach and the
    # final smash's burst.
    scale=0.5,
    svg_center_x=CENTER_X,
    svg_ground_y=GROUND_Y,
    frame_size=(360, 320),
    rows=ROWS,
    clips=CLIPS,
    defaults={"body_opacity": 1.0},
    substeps=_substeps(),
    knee_bend=1.0,
)


# --- the front view ---------------------------------------------------------------------
#
# Bob facing the viewer, drawn on the same canvas (``bob_front.svg``). Its
# rows are few and quiet, so they are written straight in the pose language
# as offsets from the drawn stance.

FRONT_SVG = PKG / "data" / "characters" / "bob" / "bob_front.svg"
FRONT = H.Body.from_svg(FRONT_SVG, CENTER_X, GROUND_Y)


def _front_rest() -> Semantic:
    """The front drawing's own stance in pose-language fields."""
    pose: Semantic = {"nf": g(FRONT.rest_x("near")), "ff": g(FRONT.rest_x("far"))}
    for side in ("near", "far"):
        s = side[0]
        ru = FRONT._rest(f"{side}_shoulder", f"{side}_elbow")
        rl = FRONT._rest(f"{side}_elbow", f"{side}_wrist")
        pose.update({f"{s}u": ru, f"{s}e": ru - rl, f"{s}w": -90.0})
    return pose


FRONT_STANCE = _front_rest()


def idle_front(t: float) -> Semantic:
    """Facing the viewer at ease: breathing, his weight drifting from foot to
    foot, the head tipping as he listens, the wrench swinging a little from
    his fist, a blink, and a half smile."""
    w = W * t
    p = dict(FRONT_STANCE)
    p.update({
        "x": 2.5 * math.sin(w), "y": 1.5 + 1.5 * math.sin(2 * w), "lean": -1.5 * math.sin(w),
        "head": 3.0 * math.sin(w - 0.7),
        "nu": float(FRONT_STANCE["nu"]) - 2.0 + 2.5 * math.sin(w - 0.4),
        "nw": -90.0 + 4.0 * math.sin(w - 1.0),
        "fu": float(FRONT_STANCE["fu"]) + 2.0 - 2.0 * math.sin(w - 0.3),
        "eye": "shut" if 0.8 < t < 0.92 else "open",
        "mouth": "smile" if 0.35 < t < 0.75 else "closed",
    })
    return p


FRONT_CLIPS: Dict[str, Callable[[int, int, float], Pose]] = {
    "idle_front": lambda i, n, t: FRONT.channels(idle_front(t)),
}
FRONT_ROWS = [(name, frames, ms, name in BOB_LOOPS) for name, frames, ms in BOB_ROWS if name in BOB_FRONT_ROWS]

FRONT_SPEC = H.humanoid_spec(
    name="bob_front",
    svg_path=FRONT_SVG,
    rig_path=PKG / "targets" / "characters" / "rigged" / "bob" / "bob_front.rig.json",
    view_label="Bob - Front",
    scale=0.5,
    svg_center_x=CENTER_X,
    svg_ground_y=GROUND_Y,
    frame_size=(360, 320),
    rows=FRONT_ROWS,
    clips=FRONT_CLIPS,
    defaults={"body_opacity": 1.0},
    knee_bend=1.0,
    far_knee_bend=-1.0,
)


def main(argv: List[str] | None = None) -> int:
    del argv
    for spec in (SPEC, FRONT_SPEC):
        missing = sorted({name for name, *_ in spec.rows} - set(spec.clips))
        extra = sorted(set(spec.clips) - {name for name, *_ in spec.rows})
        if missing or extra:
            raise SystemExit(f"{spec.name}: rows without clips: {missing}; clips without rows: {extra}")
        for path in H.write(spec):
            print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
