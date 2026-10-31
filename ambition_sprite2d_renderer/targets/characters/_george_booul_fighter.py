"""George Boo'l's fighter body language: everything a platform fighter shows
that is not one of his moves (``fighter_motion_vocabulary.yaml``, scope
``fighter_core``).

Posed as cloth on his own sheet (``george_booul.Pose``): the dome leads, the
bell bends after it, the hem trails, and a fist under a sheet corner reaches.
A key is a dict of ``Pose`` fields; a field it leaves out is at rest. He
faces +x; a positive ``tilt`` turns him back (counter-clockwise), a negative
one forward. Two keys are this module's own:

- ``floor``: placed so the lowest paint of the sheet is on the floor line, the
  line his hem tips stand on at rest. A body lying, sitting or rolling is ON
  the floor, whatever part of it is lowest.
- ``lift``: with ``floor``, px over the floor line (a body bounced off it).
- ``sink``: may paint below the floor line (buried, dropping through it).
  Every other frame is lifted out of the floor if it reaches into it: a
  forward tilt or a squash never sinks the hem.
- ``phase``: the hem's flutter phase, when the frame's own (index / count)
  would repeat a neighbour's.

Rules every row keeps:

- a recoil (``hit_*``) ENDS on its settled pose, because the game holds a
  clip's last frame for the whole hitstun;
- ``turnaround`` ends facing his front (+x), because the game draws it in the
  new facing;
- no row draws exactly what another draws.

His logic shows where it means something: a dodge fades (NOT, intangible), a
tech catches the fall with a TRUE flash, a helpless fall greys, a loss turns
him FALSE.
"""

from __future__ import annotations

import math
from typing import Callable, Dict, List, Tuple

Key = Dict[str, object]
K = dict

TAU = math.tau

#: His airborne carriage: lifted, the bell a little open, the corners out.
_AIR = K(y=-12.0, hem_spread=1.06, flutter=1.6, near_x=6.0, near_y=-8.0, far_x=-6.0, far_y=-8.0)


def _cycle(count: int, key: Callable[[float], Key]) -> List[Key]:
    """A loop: ``key`` at each phase 0, 1/count, ..."""
    return [key(i / count) for i in range(count)]


#: The rest values of the ``Pose`` fields that are not 0 (a test holds them
#: to ``george_booul.Pose``; importing it here would be circular).
REST: Key = dict(state=1.0, hem_spread=1.0, flutter=1.0, eye_scale=1.0, opacity=1.0, squash_x=1.0,
                 squash_y=1.0, yaw=40.0, eyes="round")


def _toward(a: Key, b: Key, u: float) -> Key:
    """Key ``a`` toward ``b`` by ``u``; a field one leaves out is at rest."""
    out: Key = {}
    for name in sorted(set(a) | set(b)):
        va, vb = a.get(name, REST.get(name, 0.0)), b.get(name, REST.get(name, 0.0))
        if isinstance(va, float) and isinstance(vb, float):
            out[name] = va + (vb - va) * u
        else:
            out[name] = vb if u >= 0.5 else va
    return out


def _tuck(tilt: float, **kw) -> Key:
    """The sheet balled up and turned ``tilt`` degrees: the dome pulled down
    into the bell, the hem gathered, both fists wrapped in front. A roll, a
    tumble and a flip are this at a sequence of turns."""
    base = K(tilt=tilt, stretch=24.0, hem_spread=0.9, squash_y=0.86, flutter=1.8, near_x=-6.0, near_y=0.0,
             far_x=8.0, far_y=0.0, eyes="closed", mouth_open=0.2)
    base.update(kw)
    return base


# -- shared poses ----------------------------------------------------------

#: Crouched: the sheet sunk into itself, the bell wide, the fists low.
_CROUCH = K(squash_x=1.18, squash_y=0.74, hem_spread=1.12, near_x=-2.0, near_y=12.0, far_x=2.0, far_y=12.0,
            eyes="narrow")
#: The guard: hunched behind both fists crossed in front of the dome.
_BLOCK = K(lean=-3.0, stretch=4.0, squash_x=1.04, squash_y=0.92, near_x=8.0, near_y=-30.0, far_x=32.0,
           far_y=-24.0, eyes="narrow", hem_spread=1.06)
#: Lying on his back, head behind him, the face to the sky, a fist up off
#: his belly.
_FACE_UP = K(floor=True, tilt=90.0, yaw=75.0, squash_x=0.72, hem_spread=1.08, flutter=0.6, near_x=24.0,
             near_y=18.0, far_x=-14.0, far_y=14.0, eyes="round", eye_scale=0.9, mouth_open=0.45)
#: Lying on his front, head ahead of him, the back of the sheet up.
_FACE_DOWN = K(floor=True, tilt=-90.0, yaw=140.0, squash_x=0.7, hem_spread=1.1, flutter=0.6, near_x=-12.0,
               near_y=12.0, far_x=-8.0, far_y=16.0)
#: Sat on the floor, propped on the far fist behind him.
_SITTING = K(floor=True, squash_x=1.22, squash_y=0.66, lean=-6.0, tilt=12.0, hem_spread=1.24, hem_dx=6.0,
             near_x=-6.0, near_y=22.0, far_x=-24.0, far_y=24.0, eyes="round", mouth_open=0.3)
#: Hanging from a ledge above his front by both corners.
_HANG = K(y=-6.0, stretch=5.0, lean=4.0, hem_dx=-6.0, hem_spread=0.9, flutter=1.4, near_x=4.0, near_y=-54.0,
          far_x=10.0, far_y=-52.0, eyes="round")


def _walk(ph: float) -> Key:
    w = math.sin(ph * TAU)
    return K(y=-1.5 * abs(w), lean=3.0 + 0.8 * w, hem_dx=-4.0 - 1.5 * w, flutter=1.3, near_x=5.0 * w,
             near_y=2.0 - 2.0 * abs(w), far_x=-5.0 * w, far_y=2.0 - 2.0 * abs(w))


def _run(ph: float) -> Key:
    w = math.sin(ph * TAU)
    return K(y=-1.0 - 4.0 * abs(w), lean=13.0 + 1.5 * w, tilt=-6.0, hem_dx=-17.0 - 3.0 * w, hem_spread=0.92,
             flutter=2.4, stretch=1.0, near_x=-16.0 + 4.0 * w, near_y=4.0, far_x=-22.0 - 4.0 * w, far_y=2.0,
             eyes="narrow", mouth_open=0.2)


def _crouch_walk(ph: float) -> Key:
    w = math.sin(ph * TAU)
    out = dict(_CROUCH)
    out.update(lean=4.0 + w, hem_dx=-4.0 - 2.0 * w, near_x=-2.0 + 5.0 * w, far_x=2.0 - 5.0 * w, flutter=1.4)
    return out


def _teeter(ph: float) -> Key:
    w = math.sin(ph * TAU)
    return K(tilt=-12.0 - 4.0 * w, lean=6.0, hem_dx=-8.0, flutter=1.8, near_x=18.0 + 6.0 * w,
             near_y=-30.0 + 18.0 * w, far_x=-24.0 - 4.0 * w, far_y=-22.0 - 14.0 * w, eyes="wide",
             mouth_open=0.6)


def _tumble(ph: float) -> Key:
    return _tuck(360.0 * ph, y=-10.0, eyes="wide" if ph < 0.5 else "closed", mouth_open=0.5)


def _dizzy(ph: float) -> Key:
    w, w2 = math.sin(ph * TAU), math.cos(ph * TAU)
    return K(lean=6.0 * w, tilt=-4.0 * w2, hem_dx=-3.0 * w, stretch=2.0, near_x=-4.0, near_y=14.0 + 3.0 * w,
             far_x=4.0, far_y=14.0 - 3.0 * w, eyes="closed" if ph >= 0.5 else "wide", eye_scale=0.85,
             mouth_open=0.45)


#: (frame ms, keys). The frame count is the key count.
ROWS_SPEC: Dict[str, Tuple[int, List[Key]]] = {
    # -- movement ----------------------------------------------------------
    # Glancing up: back on the hem, the dome raised.
    "idle_look_up": (200, [K(tilt=7.0, lean=-3.0, stretch=-2.0, eye_scale=1.1, mouth_open=0.15, near_x=-2.0,
                             far_x=2.0)]),
    # His walk is a steady glide, the corners swinging like arms; `drift`
    # (the NPC's walk) leans further and trails them.
    "walk": (110, _cycle(6, _walk)),
    # The run streams: dome far ahead, hem and both corners pulled back.
    "run": (70, _cycle(6, _run)),
    # The burst: gathered back on the hem, then flung forward.
    "dash_startup": (55, [
        K(lean=-4.0, hem_dx=3.0, squash_x=1.08, squash_y=0.9, near_x=-8.0, near_y=6.0, far_x=-8.0, far_y=6.0,
          eyes="narrow"),
        K(x=4.0, lean=16.0, tilt=-8.0, hem_dx=-14.0, flutter=2.0, near_x=-18.0, near_y=2.0, far_x=-22.0,
          squash_x=0.96, squash_y=1.04, eyes="narrow", mouth_open=0.3),
    ]),
    "dash": (65, [
        K(y=-3.0, lean=18.0, tilt=-10.0, hem_dx=-20.0, hem_spread=0.88, flutter=2.6, near_x=-22.0, near_y=-2.0,
          far_x=-28.0, far_y=0.0, eyes="narrow", mouth_open=0.3),
        K(y=-5.0, lean=19.0, tilt=-11.0, hem_dx=-22.0, hem_spread=0.86, flutter=2.6, near_x=-24.0, near_y=2.0,
          far_x=-30.0, far_y=4.0, eyes="narrow", mouth_open=0.3),
        K(y=-3.0, lean=18.0, tilt=-10.0, hem_dx=-19.0, hem_spread=0.9, flutter=2.6, near_x=-20.0, near_y=4.0,
          far_x=-26.0, far_y=6.0, eyes="narrow", mouth_open=0.3),
    ]),
    # A hard slide, sunk low: the hem drags out ahead, the far fist out
    # behind for balance.
    "skid": (80, [
        K(lean=-6.0, tilt=6.0, hem_dx=14.0, hem_spread=1.2, squash_x=1.08, squash_y=0.9, flutter=2.2,
          near_x=16.0, near_y=10.0, far_x=-22.0, far_y=-14.0, eyes="wide", mouth_open=0.4),
        K(lean=-4.0, tilt=4.0, hem_dx=10.0, hem_spread=1.14, squash_x=1.05, squash_y=0.93, flutter=1.8,
          near_x=12.0, near_y=10.0, far_x=-18.0, far_y=-10.0, eyes="wide", mouth_open=0.3),
    ]),
    # Drawn in the NEW facing: he starts turned to the old side and comes
    # round to face +x.
    "turnaround": (70, [
        K(yaw=-40.0, lean=-3.0, hem_dx=3.0, near_x=-2.0, far_x=2.0),
        K(yaw=0.0, lean=0.0, hem_dx=1.0, flutter=1.4, near_x=4.0, near_y=-4.0, far_x=-4.0, far_y=-4.0),
        K(yaw=40.0, lean=2.0, hem_dx=-2.0),
    ]),
    # A glide settling: the hem swings on past him, then hangs.
    "walk_stop": (80, [
        K(lean=-2.0, hem_dx=4.0, flutter=1.2, near_x=4.0, far_x=-2.0),
        K(lean=-0.5, hem_dx=1.5, near_x=1.0),
    ]),
    # The run brake: the hem planted and flared out ahead, the dome thrown
    # back against the speed, the corners flung up.
    "run_stop": (70, [
        K(x=2.0, lean=-10.0, tilt=8.0, hem_dx=16.0, hem_spread=1.18, squash_x=1.06, squash_y=0.92, flutter=2.0,
          near_x=14.0, near_y=-16.0, far_x=8.0, far_y=-22.0, eyes="wide", mouth_open=0.5),
        K(x=1.0, lean=-7.0, tilt=5.0, hem_dx=11.0, hem_spread=1.12, squash_x=1.03, squash_y=0.96, flutter=1.6,
          near_x=10.0, near_y=-10.0, far_x=4.0, far_y=-14.0, eyes="wide", mouth_open=0.3),
        K(lean=-2.0, tilt=1.5, hem_dx=4.0, hem_spread=1.04, near_x=4.0, near_y=-2.0, far_x=0.0, far_y=-4.0),
    ]),
    # The beat a short hop is decided in: sunk into the bell.
    "jump_squat": (50, [
        K(squash_x=1.1, squash_y=0.86, hem_spread=1.06, near_x=-4.0, near_y=8.0, far_x=4.0, far_y=8.0),
        K(squash_x=1.16, squash_y=0.8, hem_spread=1.1, near_x=-6.0, near_y=12.0, far_x=6.0, far_y=12.0,
          eyes="narrow"),
    ]),
    # Up: drawn long, the hem gathered under him, then opening into the air.
    "jump": (70, [
        K(y=-8.0, squash_x=0.88, squash_y=1.1, hem_spread=0.8, flutter=2.0, near_x=6.0, near_y=-22.0,
          far_x=-6.0, far_y=-20.0, mouth_open=0.2),
        K(y=-12.0, squash_x=0.94, squash_y=1.05, hem_spread=0.9, flutter=1.8, near_x=8.0, near_y=-14.0,
          far_x=-8.0, far_y=-12.0),
        dict(_AIR),
    ]),
    # His second jump is a forward somersault into his air carriage.
    "double_jump": (60, [
        _tuck(-70.0, y=-14.0),
        _tuck(-160.0, y=-14.0),
        _tuck(-250.0, y=-14.0),
        _tuck(-330.0, y=-14.0, stretch=6.0, hem_spread=0.85),
        K(y=-14.0, hem_spread=0.95, flutter=2.0, near_x=10.0, near_y=-30.0, far_x=-10.0, far_y=-28.0,
          eyes="wide"),
    ]),
    # Falling: the bell billows open, both corners lifted.
    "fall": (120, [
        K(y=-12.0, stretch=2.0, hem_spread=1.25, flutter=-2.0, near_x=10.0, near_y=-22.0, far_x=-10.0,
          far_y=-20.0, eyes="wide", mouth_open=0.3),
        K(y=-12.0, stretch=2.5, hem_spread=1.28, flutter=-2.2, near_x=12.0, near_y=-24.0, far_x=-12.0,
          far_y=-22.0, eyes="wide", mouth_open=0.35, phase=0.25),
    ]),
    "land_light": (50, [
        K(squash_x=1.1, squash_y=0.88, hem_spread=1.08, near_y=4.0, far_y=4.0),
        K(squash_x=1.04, squash_y=0.96, hem_spread=1.03, near_y=1.0, far_y=1.0),
    ]),
    # A hard landing flattens the bell and throws the corners out.
    "land_hard": (60, [
        K(squash_x=1.3, squash_y=0.7, hem_spread=1.25, flutter=2.0, near_x=18.0, near_y=22.0, far_x=-18.0,
          far_y=22.0, eyes="closed", mouth_open=0.4),
        K(squash_x=1.18, squash_y=0.82, hem_spread=1.16, flutter=1.6, near_x=12.0, near_y=16.0, far_x=-12.0,
          far_y=16.0, eyes="narrow", mouth_open=0.2),
        K(squash_x=1.06, squash_y=0.94, hem_spread=1.05, near_x=4.0, near_y=6.0, far_x=-4.0, far_y=6.0),
    ]),
    # An aerial's landing lag: sunk, the fists out low.
    "air_land": (60, [
        K(squash_x=1.14, squash_y=0.84, hem_spread=1.14, lean=4.0, hem_dx=-3.0, near_x=12.0, near_y=14.0,
          far_x=-14.0, far_y=12.0, eyes="narrow", mouth_open=0.2),
        K(squash_x=1.06, squash_y=0.93, hem_spread=1.06, lean=2.0, near_x=6.0, near_y=6.0, far_x=-6.0,
          far_y=6.0),
    ]),
    "crouch": (160, [
        dict(_CROUCH),
        dict(_CROUCH, squash_y=0.76, eye_scale=0.95, phase=0.25),
    ]),
    "crouch_walk": (110, _cycle(4, _crouch_walk)),
    # A crouch that leaves the floor: balled low in the air.
    "crouch_jump": (90, [K(y=-16.0, stretch=8.0, squash_x=1.12, squash_y=0.78, hem_spread=0.8, flutter=2.0,
                           near_x=-8.0, near_y=14.0, far_x=8.0, far_y=14.0, eyes="narrow")]),
    # At an edge ahead of him: tipped over it, the hem planted behind, the
    # corners windmilling.
    "teeter_start": (70, [
        K(tilt=-18.0, lean=8.0, hem_dx=-6.0, flutter=2.0, near_x=10.0, near_y=-10.0, far_x=-14.0, far_y=-6.0,
          eyes="wide", mouth_open=0.7),
        K(tilt=-12.0, lean=6.0, hem_dx=-8.0, flutter=1.8, near_x=16.0, near_y=-24.0, far_x=-22.0, far_y=-18.0,
          eyes="wide", mouth_open=0.6),
    ]),
    "teeter": (110, _cycle(4, _teeter)),
    # Losing his footing: pitched forward, both fists out to catch himself.
    "stumble": (70, [
        K(tilt=-10.0, lean=8.0, hem_dx=-10.0, flutter=2.0, near_x=12.0, near_y=6.0, far_x=8.0, far_y=2.0,
          eyes="wide", mouth_open=0.5),
        K(tilt=-16.0, lean=12.0, hem_dx=-14.0, flutter=2.2, near_x=22.0, near_y=18.0, far_x=16.0, far_y=14.0,
          eyes="wide", mouth_open=0.7),
        K(tilt=-6.0, lean=5.0, hem_dx=-6.0, flutter=1.4, near_x=8.0, near_y=6.0, far_x=4.0, far_y=4.0,
          eyes="round", mouth_open=0.3),
    ]),
    # Through a thin floor: corners up, the sheet slipping down out of them.
    "platform_drop": (60, [
        K(squash_x=1.06, squash_y=0.92, near_x=6.0, near_y=-10.0, far_x=-6.0, far_y=-10.0),
        K(sink=True, y=6.0, hem_spread=0.85, flutter=1.8, near_x=8.0, near_y=-30.0, far_x=-8.0, far_y=-28.0,
          eyes="wide", mouth_open=0.4),
    ]),
    # Helpless after his recovery: spent and greyed, the corners hanging.
    "fall_special": (120, [
        K(state=0.7, y=-12.0, stretch=2.0, lean=-3.0, hem_spread=1.15, flutter=-2.4, near_x=-4.0, near_y=16.0,
          far_x=4.0, far_y=16.0, eyes="closed", mouth_open=0.5),
        K(state=0.7, y=-12.0, stretch=2.5, lean=-2.0, hem_spread=1.18, flutter=-2.4, near_x=-3.0, near_y=18.0,
          far_x=5.0, far_y=17.0, eyes="closed", mouth_open=0.55, phase=0.25),
    ]),
    # Off somebody's head: pressed down on them, then sprung tall.
    "footstool_jump": (60, [
        K(y=-10.0, squash_x=1.15, squash_y=0.82, hem_spread=1.12, near_x=4.0, near_y=14.0, far_x=-4.0,
          far_y=14.0, eyes="narrow"),
        K(y=-16.0, squash_x=0.9, squash_y=1.08, hem_spread=0.84, flutter=2.0, near_x=10.0, near_y=-34.0,
          far_x=-10.0, far_y=-32.0, eyes="happy", mouth_open=0.4),
    ]),
    # Stood on: the dome pressed down into the bell, the corners splayed.
    "footstooled": (70, [
        K(stretch=10.0, squash_x=1.2, squash_y=0.76, hem_spread=1.22, flutter=2.0, near_x=20.0, near_y=0.0,
          far_x=-20.0, far_y=0.0, eyes="closed", mouth_open=0.7),
        K(stretch=6.0, squash_x=1.1, squash_y=0.86, hem_spread=1.12, near_x=12.0, near_y=6.0, far_x=-12.0,
          far_y=6.0, eyes="wide", mouth_open=0.5),
    ]),
    # -- reactions ---------------------------------------------------------
    # Struck on the dome: it snaps back and up, the hem stays planted, the
    # corners fly up behind. Settles still thrown back.
    "hit_high": (60, [
        K(x=-3.0, lean=-14.0, tilt=5.0, stretch=-1.0, hem_dx=7.0, flutter=2.2, near_x=-8.0, near_y=-30.0,
          far_x=-12.0, far_y=-26.0, eyes="wide", mouth_open=0.9, fx="hit", fx_strength=0.8),
        K(x=-6.0, lean=-20.0, tilt=9.0, stretch=-2.0, hem_dx=10.0, flutter=2.0, near_x=-12.0, near_y=-36.0,
          far_x=-16.0, far_y=-30.0, eyes="closed", mouth_open=0.8),
        K(x=-5.0, lean=-18.0, tilt=8.0, stretch=-1.5, hem_dx=9.0, flutter=1.6, near_x=-10.0, near_y=-28.0,
          far_x=-14.0, far_y=-22.0, eyes="closed", mouth_open=0.6),
    ]),
    # Struck in the middle: he doubles over it, dome dropped forward, the
    # body driven back, both fists clutched in.
    "hit_mid": (60, [
        K(x=-5.0, lean=8.0, tilt=-6.0, stretch=6.0, hem_dx=6.0, squash_x=0.94, flutter=2.0, near_x=4.0,
          near_y=12.0, far_x=14.0, far_y=8.0, eyes="wide", mouth_open=0.9, fx="hit", fx_strength=0.8),
        K(x=-10.0, lean=17.0, tilt=-18.0, stretch=12.0, hem_dx=12.0, hem_spread=1.08, squash_x=0.94,
          squash_y=0.92, flutter=2.0, near_x=12.0, near_y=20.0, far_x=20.0, far_y=16.0, eyes="closed",
          mouth_open=0.8),
        K(x=-9.0, lean=16.0, tilt=-17.0, stretch=11.0, hem_dx=11.0, hem_spread=1.06, squash_x=0.94,
          squash_y=0.93, flutter=1.6, near_x=11.0, near_y=19.0, far_x=19.0, far_y=15.0, eyes="closed",
          mouth_open=0.7),
    ]),
    # Struck at the hem: it is swept out behind him, he pitches forward over
    # it, lifted, the corners thrown out to catch his balance.
    "hit_low": (60, [
        K(y=-2.0, lean=8.0, tilt=-8.0, hem_dx=-14.0, hem_spread=0.88, flutter=2.4, near_x=12.0, near_y=-20.0,
          far_x=-16.0, far_y=-18.0, eyes="wide", mouth_open=0.7, fx="hit", fx_strength=0.8),
        K(y=-5.0, lean=12.0, tilt=-14.0, hem_dx=-20.0, hem_spread=0.82, flutter=2.6, near_x=18.0, near_y=-32.0,
          far_x=-22.0, far_y=-26.0, eyes="wide", mouth_open=0.8),
        K(y=-4.0, lean=11.0, tilt=-12.0, hem_dx=-18.0, hem_spread=0.84, flutter=2.2, near_x=16.0, near_y=-28.0,
          far_x=-20.0, far_y=-22.0, eyes="wide", mouth_open=0.6),
    ]),
    # Struck in the air: thrown back, the bell flared, both corners flung
    # wide.
    "hit_air": (60, [
        K(y=-12.0, tilt=14.0, lean=-8.0, hem_dx=8.0, hem_spread=1.2, flutter=2.4, near_x=18.0, near_y=-22.0,
          far_x=-22.0, far_y=-18.0, eyes="wide", mouth_open=0.9, fx="hit", fx_strength=0.8),
        K(y=-12.0, tilt=20.0, lean=-10.0, hem_dx=10.0, hem_spread=1.26, flutter=2.4, near_x=22.0, near_y=-26.0,
          far_x=-26.0, far_y=-20.0, eyes="closed", mouth_open=0.8),
    ]),
    # Launches, by the direction he travels; what trails, trails opposite.
    # Up: drawn long and narrow, the hem gathered, the corners pulled down
    # along his sides.
    "launch_up": (70, [
        K(y=-6.0, tilt=6.0, squash_x=0.82, squash_y=1.1, hem_spread=0.7, flutter=2.6, near_x=6.0, near_y=30.0,
          far_x=-8.0, far_y=30.0, eyes="wide", mouth_open=0.6),
        K(y=-8.0, tilt=9.0, squash_x=0.8, squash_y=1.1, hem_spread=0.68, flutter=-2.6, near_x=8.0,
          near_y=34.0, far_x=-10.0, far_y=34.0, eyes="closed", mouth_open=0.5),
    ]),
    # Back across the stage: laid out flat, the dome leading, the hem and
    # both corners streaming forward behind him.
    "launch_horizontal": (70, [
        K(x=-6.0, y=-14.0, tilt=72.0, squash_x=0.86, squash_y=1.06, hem_spread=1.14, flutter=2.6, near_x=10.0,
          near_y=30.0, far_x=-14.0, far_y=30.0, eyes="wide", mouth_open=0.8),
        K(x=-6.0, y=-14.0, tilt=78.0, squash_x=0.84, squash_y=1.08, hem_spread=1.2, flutter=-2.6, near_x=12.0,
          near_y=34.0, far_x=-16.0, far_y=34.0, eyes="closed", mouth_open=0.7),
    ]),
    # Down: spiked dome first, the bell thrown open above him, the corners
    # trailing up.
    "launch_down": (70, [
        K(y=-6.0, tilt=145.0, squash_x=0.92, hem_spread=1.3, flutter=2.6, near_x=14.0, near_y=18.0, far_x=-14.0,
          far_y=18.0, eyes="wide", mouth_open=0.8),
        K(y=-6.0, tilt=152.0, squash_x=0.9, hem_spread=1.34, flutter=-2.6, near_x=16.0, near_y=22.0,
          far_x=-16.0, far_y=22.0, eyes="closed", mouth_open=0.7),
    ]),
    # The generic launch: up and back on a diagonal.
    "launch": (70, [
        K(y=-12.0, tilt=38.0, squash_x=0.86, squash_y=1.06, hem_spread=1.1, flutter=2.4, near_x=-2.0,
          near_y=20.0, far_x=4.0, far_y=22.0, eyes="wide", mouth_open=0.8),
        K(y=-12.0, tilt=44.0, squash_x=0.85, squash_y=1.07, hem_spread=1.14, flutter=-2.4, near_x=-4.0,
          near_y=24.0, far_x=6.0, far_y=24.0, eyes="closed", mouth_open=0.7),
    ]),
    # The meteor: driven straight down, crushed short, the bell blown open
    # over him and the corners straight up.
    "meteor": (60, [
        K(y=-4.0, tilt=180.0, squash_x=1.04, squash_y=0.86, hem_spread=1.4, flutter=2.8, near_x=20.0, near_y=6.0,
          far_x=-20.0, far_y=6.0, eyes="closed", mouth_open=0.9),
        K(y=-4.0, tilt=176.0, squash_x=1.06, squash_y=0.84, hem_spread=1.44, flutter=-2.8, near_x=22.0,
          near_y=8.0, far_x=-22.0, far_y=8.0, eyes="closed", mouth_open=0.8),
    ]),
    # Tumbling: balled up, turning over backward.
    "tumble": (80, _cycle(4, _tumble)),
    # Slapped onto the floor: laid out, then bounced flat on his back.
    "knockdown": (70, [
        dict(_FACE_UP, tilt=72.0, squash_x=0.62, hem_spread=1.18, flutter=2.0, near_x=-4.0, near_y=-16.0,
             far_x=-8.0, far_y=-12.0, eyes="wide", mouth_open=0.8),
        dict(_FACE_UP, phase=0.5),
    ]),
    "prone_face_up": (180, [dict(_FACE_UP), dict(_FACE_UP, phase=0.25, mouth_open=0.35)]),
    "prone_face_down": (180, [dict(_FACE_DOWN), dict(_FACE_DOWN, phase=0.25)]),
    # Prone in general: crumpled in a heap of laundry, the face peering out.
    "prone": (180, [K(floor=True, squash_x=1.34, squash_y=0.5, stretch=4.0, lean=6.0, hem_spread=1.3, flutter=0.5,
                      near_x=14.0, near_y=26.0, far_x=-14.0, far_y=26.0, eyes="closed", mouth_open=0.2,
                      collapse=0.6)]),
    # Hit while down: jolted off the floor on his back.
    "prone_damage": (60, [
        dict(_FACE_UP, lift=14.0, tilt=80.0, near_x=30.0, near_y=-6.0, far_x=26.0, far_y=6.0, eyes="wide",
             mouth_open=0.9, flutter=2.0),
        dict(_FACE_UP, phase=0.5, mouth_open=0.5),
    ]),
    # Up from his back: rolled up through a crouch onto the hem.
    "getup": (80, [
        K(floor=True, tilt=60.0, yaw=60.0, squash_x=0.82, hem_spread=1.1, near_x=-4.0, near_y=16.0, far_x=-14.0,
          far_y=20.0, eyes="round", mouth_open=0.3),
        K(floor=True, tilt=24.0, squash_x=1.06, squash_y=0.84, hem_spread=1.14, near_x=4.0, near_y=14.0,
          far_x=-12.0, far_y=18.0, eyes="narrow"),
        K(squash_x=1.04, squash_y=0.95, hem_spread=1.04, near_x=2.0, near_y=4.0, far_x=-4.0, far_y=4.0),
    ]),
    # Rolled up off his back, over his head and onto the hem.
    "getup_roll": (60, [
        _tuck(130.0, floor=True),
        _tuck(210.0, floor=True),
        _tuck(290.0, floor=True),
        K(squash_x=1.1, squash_y=0.88, hem_spread=1.1, near_x=-4.0, near_y=10.0, far_x=4.0, far_y=10.0,
          eyes="narrow"),
    ]),
    # Up from the floor swinging: both corners swept wide along it.
    "getup_attack": (60, [
        K(floor=True, tilt=50.0, yaw=60.0, squash_x=0.86, hem_spread=1.1, near_x=-6.0, near_y=10.0,
          far_x=-10.0, far_y=14.0, eyes="narrow"),
        K(squash_x=1.16, squash_y=0.82, hem_spread=1.18, near_x=-8.0, near_y=6.0, far_x=8.0, far_y=6.0,
          eyes="narrow", mouth_open=0.3),
        K(squash_x=1.18, squash_y=0.78, hem_spread=1.2, flutter=2.0, near_x=28.0, near_y=30.0, far_x=-26.0,
          far_y=30.0, eyes="narrow", mouth_open=0.7, fx="slam", fx_strength=0.7),
        K(squash_x=1.06, squash_y=0.94, hem_spread=1.06, near_x=8.0, near_y=6.0, far_x=-8.0, far_y=6.0),
    ]),
    # The tech: the landing caught on both fists, sunk low and braced, and
    # a TRUE flash.
    "tech": (60, [
        K(squash_x=1.22, squash_y=0.76, hem_spread=1.2, flutter=1.6, near_x=18.0, near_y=34.0, far_x=-18.0,
          far_y=34.0, eyes="narrow", fx="toggle", fx_strength=0.7),
        K(squash_x=1.12, squash_y=0.86, hem_spread=1.12, near_x=16.0, near_y=26.0, far_x=-16.0, far_y=26.0,
          eyes="narrow", fx="toggle", fx_strength=0.3),
    ]),
    # Teched into a roll along the floor, up into the brace.
    "tech_roll": (60, [
        _tuck(-60.0, floor=True, eyes="narrow"),
        _tuck(-180.0, floor=True, eyes="narrow"),
        _tuck(-300.0, floor=True, eyes="narrow"),
        K(squash_x=1.12, squash_y=0.86, hem_spread=1.12, near_x=16.0, near_y=24.0, far_x=-16.0, far_y=24.0,
          eyes="narrow"),
    ]),
    # Caught on a wall behind him: both fists flat on it.
    "wall_tech": (60, [
        K(y=-10.0, tilt=18.0, lean=-6.0, hem_dx=4.0, squash_x=0.92, near_x=-22.0, near_y=-12.0, far_x=-28.0,
          far_y=-18.0, eyes="narrow", fx="toggle", fx_strength=0.7),
        K(y=-10.0, tilt=12.0, lean=-4.0, hem_dx=3.0, near_x=-18.0, near_y=-10.0, far_x=-24.0, far_y=-14.0,
          eyes="narrow", fx="toggle", fx_strength=0.3),
    ]),
    # Kicked off it: sprung forward and up.
    "wall_tech_jump": (60, [
        K(y=-12.0, tilt=-6.0, lean=10.0, hem_dx=-10.0, squash_x=0.92, squash_y=1.06, flutter=2.0, near_x=-10.0,
          near_y=-4.0, far_x=-16.0, far_y=-2.0, eyes="narrow"),
        K(y=-14.0, tilt=-10.0, lean=12.0, hem_dx=-14.0, hem_spread=0.9, flutter=2.4, near_x=10.0, near_y=-28.0,
          far_x=-18.0, far_y=-6.0, eyes="happy", mouth_open=0.3),
    ]),
    # Caught on a ceiling: both fists up flat on it, crushed short.
    "ceiling_tech": (60, [
        K(y=-14.0, stretch=4.0, squash_y=0.88, squash_x=1.06, hem_spread=1.1, near_x=6.0, near_y=-54.0,
          far_x=-6.0, far_y=-52.0, eyes="narrow", fx="toggle", fx_strength=0.7),
        K(y=-12.0, stretch=3.0, squash_y=0.92, near_x=6.0, near_y=-48.0, far_x=-6.0, far_y=-46.0,
          eyes="narrow", fx="toggle", fx_strength=0.3),
    ]),
    # Slammed into a wall behind him: flattened against it, corners splayed.
    "impact": (60, [
        K(x=-6.0, lean=-8.0, hem_dx=-6.0, squash_x=0.72, squash_y=1.04, flutter=2.0, near_x=-10.0, near_y=-34.0,
          far_x=-16.0, far_y=-30.0, eyes="closed", mouth_open=0.9),
        K(x=-5.0, lean=-6.0, hem_dx=-4.0, squash_x=0.78, squash_y=1.02, flutter=1.6, near_x=-8.0, near_y=-26.0,
          far_x=-14.0, far_y=-22.0, eyes="closed", mouth_open=0.7),
    ]),
    # Splat: spread-eagled flat on the wall, face on, sliding down it.
    "splat": (80, [
        K(y=-8.0, yaw=0.0, squash_x=1.08, hem_spread=1.3, flutter=0.4, stretch=2.0, near_x=20.0, near_y=-40.0,
          far_x=-20.0, far_y=-40.0, eyes="closed", mouth_open=0.7),
        K(y=-4.0, yaw=0.0, squash_x=1.06, squash_y=0.96, hem_spread=1.32, flutter=0.4, stretch=4.0, near_x=22.0,
          near_y=-30.0, far_x=-22.0, far_y=-30.0, eyes="closed", mouth_open=0.5),
    ]),
    # Bounced off the floor: slapped flat, then sprung back up off it.
    "ground_bounce": (60, [
        dict(_FACE_UP, squash_x=0.56, hem_spread=1.24, flutter=2.4, near_x=-4.0, near_y=-10.0, far_x=-8.0,
             far_y=-6.0, eyes="wide", mouth_open=0.9),
        K(y=-14.0, tilt=64.0, yaw=75.0, squash_x=0.8, hem_spread=1.14, flutter=2.4, near_x=-2.0, near_y=20.0,
          far_x=4.0, far_y=22.0, eyes="closed", mouth_open=0.7),
    ]),
    # -- defence -----------------------------------------------------------
    "shield_raise": (50, [
        _toward({}, _BLOCK, 0.5),
        dict(_BLOCK, near_y=-34.0, far_y=-28.0),
    ]),
    "block": (150, [dict(_BLOCK), dict(_BLOCK, stretch=4.5, eye_scale=0.95, phase=0.25)]),
    # A blocked hit: shoved back behind the guard.
    "shield_hit": (60, [
        dict(_BLOCK, x=-5.0, lean=-8.0, tilt=4.0, hem_dx=6.0, flutter=2.0, near_x=4.0, far_x=26.0,
             eyes="closed"),
        dict(_BLOCK, x=-3.0, lean=-6.0, tilt=2.0, hem_dx=4.0, flutter=1.6, near_x=6.0, far_x=28.0),
    ]),
    "shield_release": (50, [
        _toward(_BLOCK, {}, 0.45),
        _toward(_BLOCK, {}, 0.8),
    ]),
    # The perfect guard: both fists thrown open at the hit, a TRUE flash.
    "parry": (60, [
        K(lean=4.0, hem_dx=-2.0, near_x=22.0, near_y=-20.0, far_x=34.0, far_y=-34.0, eyes="wide",
          mouth_open=0.4, fx="toggle", fx_strength=1.0),
        K(lean=2.0, near_x=18.0, near_y=-14.0, far_x=26.0, far_y=-26.0, eyes="narrow", fx="toggle",
          fx_strength=0.5),
    ]),
    # The spot dodge is NOT: he thins and fades where he stands.
    "spot_dodge": (50, [
        K(squash_x=0.9, squash_y=0.94, near_x=-6.0, near_y=6.0, far_x=6.0, far_y=6.0, opacity=0.6,
          eyes="closed"),
        K(squash_x=0.8, squash_y=0.9, stretch=3.0, hem_spread=0.8, near_x=-8.0, near_y=8.0, far_x=8.0,
          far_y=8.0, opacity=0.3, eyes="closed", fx="not", fx_strength=0.6),
        K(squash_x=0.94, squash_y=0.97, near_x=-3.0, near_y=3.0, far_x=3.0, far_y=3.0, opacity=0.75),
    ]),
    "roll": (50, [
        _tuck(-72.0, floor=True),
        _tuck(-144.0, floor=True, opacity=0.7),
        _tuck(-216.0, floor=True, opacity=0.7),
        _tuck(-288.0, floor=True),
        K(squash_x=1.08, squash_y=0.9, hem_spread=1.08, near_x=-2.0, near_y=8.0, far_x=2.0, far_y=8.0,
          eyes="narrow"),
    ]),
    "roll_back": (50, [
        _tuck(72.0, floor=True),
        _tuck(144.0, floor=True, opacity=0.7),
        _tuck(216.0, floor=True, opacity=0.7),
        _tuck(288.0, floor=True),
        K(squash_x=1.08, squash_y=0.9, hem_spread=1.08, lean=-3.0, near_x=-4.0, near_y=8.0, far_x=0.0,
          far_y=8.0, eyes="narrow"),
    ]),
    # The air dodge: NOT in the air, thinned to a sliver and faded.
    "air_dodge": (50, [
        K(y=-12.0, squash_x=0.86, hem_spread=0.85, near_x=-6.0, near_y=6.0, far_x=6.0, far_y=6.0, opacity=0.6,
          eyes="closed"),
        K(y=-12.0, squash_x=0.74, stretch=2.0, hem_spread=0.74, flutter=2.0, near_x=-8.0, near_y=8.0, far_x=8.0,
          far_y=8.0, opacity=0.3, eyes="closed", fx="not", fx_strength=0.6),
        K(y=-12.0, squash_x=0.92, hem_spread=0.95, near_x=-2.0, near_y=0.0, far_x=2.0, far_y=0.0, opacity=0.8),
    ]),
    # The guard breaks: popped up, falls limp, crumples, and shakes it off.
    "shield_break_launch": (70, [
        K(y=-8.0, tilt=8.0, stretch=-3.0, squash_x=0.9, squash_y=1.04, hem_spread=0.9, flutter=2.4,
          near_x=14.0, near_y=-36.0, far_x=-12.0, far_y=-34.0, eyes="wide", mouth_open=1.0),
        K(y=-10.0, tilt=12.0, stretch=-2.0, squash_x=0.9, squash_y=1.04, hem_spread=0.92, flutter=-2.4,
          near_x=16.0, near_y=-36.0, far_x=-14.0, far_y=-34.0, eyes="wide", mouth_open=0.9),
    ]),
    "shield_break_fall": (100, [
        K(y=-12.0, tilt=18.0, lean=-4.0, hem_spread=1.18, flutter=-2.2, near_x=6.0, near_y=-24.0, far_x=-10.0,
          far_y=-20.0, eyes="closed", mouth_open=0.6),
        K(y=-12.0, tilt=22.0, lean=-5.0, hem_spread=1.2, flutter=-2.2, near_x=8.0, near_y=-26.0, far_x=-12.0,
          far_y=-22.0, eyes="closed", mouth_open=0.6, phase=0.25),
    ]),
    "shield_break_collapse": (80, [
        K(lean=8.0, stretch=6.0, squash_x=1.12, squash_y=0.82, hem_spread=1.14, near_x=-2.0, near_y=20.0,
          far_x=2.0, far_y=20.0, eyes="closed", mouth_open=0.5),
        K(lean=12.0, stretch=8.0, squash_x=1.2, squash_y=0.72, hem_spread=1.2, near_x=-2.0, near_y=24.0,
          far_x=2.0, far_y=24.0, eyes="closed", mouth_open=0.4),
    ]),
    "shield_break_recover": (90, [
        K(x=-1.0, lean=5.0, stretch=4.0, squash_x=1.08, squash_y=0.9, near_x=-2.0, near_y=12.0, far_x=2.0,
          far_y=12.0, eyes="closed", mouth_open=0.3),
        K(x=1.0, lean=-2.0, stretch=-1.0, near_x=4.0, near_y=-6.0, far_x=-4.0, far_y=-6.0, eyes="wide",
          mouth_open=0.2),
    ]),
    "dizzy": (120, _cycle(4, _dizzy)),
    # Dozing off: the dome nods into the bell.
    "sleep_start": (100, [
        K(lean=3.0, stretch=3.0, near_x=-2.0, near_y=8.0, far_x=2.0, far_y=8.0, eye_scale=0.8, eyes="narrow"),
        K(lean=6.0, stretch=6.0, squash_x=1.04, squash_y=0.94, near_x=-2.0, near_y=12.0, far_x=2.0, far_y=12.0,
          eyes="closed", mouth_open=0.2),
    ]),
    "sleep": (250, [
        K(lean=6.0, stretch=6.0, squash_x=1.05, squash_y=0.93, near_x=-2.0, near_y=13.0, far_x=2.0, far_y=13.0,
          eyes="closed", mouth_open=0.25, flutter=0.5),
        K(lean=6.5, stretch=6.5, squash_x=1.03, squash_y=0.95, near_x=-2.0, near_y=12.0, far_x=2.0, far_y=12.0,
          eyes="closed", mouth_open=0.15, flutter=0.5, phase=0.25),
    ]),
    "wake": (80, [
        K(y=-3.0, stretch=-3.0, lean=-4.0, near_x=10.0, near_y=-20.0, far_x=-10.0, far_y=-18.0, eyes="wide",
          eye_scale=1.15, mouth_open=0.6),
        K(lean=-1.0, near_x=2.0, near_y=-4.0, far_x=-2.0, far_y=-4.0, eyes="round"),
    ]),
    # Driven into the floor up to the chest, the corners reaching out.
    "bury_start": (70, [
        K(sink=True, y=18.0, squash_x=1.1, squash_y=0.9, near_x=10.0, near_y=-20.0, far_x=-10.0, far_y=-18.0, eyes="wide",
          mouth_open=0.7),
        K(sink=True, y=34.0, near_x=12.0, near_y=-30.0, far_x=-12.0, far_y=-28.0, eyes="wide", mouth_open=0.8),
    ]),
    "buried": (150, [
        K(sink=True, y=40.0, lean=2.0, near_x=14.0, near_y=-34.0, far_x=-12.0, far_y=-24.0, eyes="narrow", mouth_open=0.3),
        K(sink=True, y=40.0, lean=-2.0, near_x=10.0, near_y=-24.0, far_x=-14.0, far_y=-34.0, eyes="narrow", mouth_open=0.3),
    ]),
    "bury_escape": (60, [
        K(sink=True, y=16.0, squash_x=0.9, squash_y=1.08, near_x=10.0, near_y=-40.0, far_x=-10.0, far_y=-38.0,
          eyes="wide", mouth_open=0.6),
        K(y=-10.0, squash_x=0.9, squash_y=1.08, hem_spread=0.85, flutter=2.4, near_x=12.0, near_y=-40.0,
          far_x=-12.0, far_y=-38.0, eyes="happy", mouth_open=0.4),
    ]),
    # -- ledge -------------------------------------------------------------
    "ledge_catch": (60, [
        dict(_HANG, y=-2.0, hem_dx=-12.0, flutter=2.4, near_y=-50.0, far_y=-48.0, eyes="wide", mouth_open=0.5),
        dict(_HANG),
    ]),
    "ledge_grab": (180, [dict(_HANG), dict(_HANG, hem_dx=-4.0, phase=0.25)]),
    # Up over the edge: hauled up on both corners, then onto the hem.
    "ledge_climb": (80, [
        dict(_HANG, y=-14.0, stretch=2.0, near_y=-40.0, far_y=-38.0, eyes="narrow"),
        K(y=-6.0, squash_x=1.1, squash_y=0.86, lean=6.0, near_x=12.0, near_y=-8.0, far_x=16.0, far_y=-6.0,
          eyes="narrow"),
        K(squash_x=1.04, squash_y=0.96, lean=2.0, near_x=4.0, near_y=2.0, far_x=2.0, far_y=2.0),
    ]),
    "ledge_getup": (70, [
        dict(_HANG, y=-16.0, stretch=0.0, near_y=-34.0, far_y=-32.0, eyes="narrow"),
        K(squash_x=1.06, squash_y=0.92, lean=4.0, near_x=8.0, near_y=4.0, far_x=6.0, far_y=4.0),
    ]),
    "ledge_roll": (55, [
        _tuck(-80.0, y=-10.0),
        _tuck(-170.0, y=-6.0),
        _tuck(-260.0, floor=True),
        _tuck(-340.0, floor=True, stretch=6.0, hem_spread=0.9),
    ]),
    "ledge_jump": (60, [
        dict(_HANG, y=-10.0, squash_x=1.08, squash_y=0.9, near_y=-44.0, far_y=-42.0, eyes="narrow"),
        K(y=-12.0, squash_x=0.9, squash_y=1.06, hem_spread=0.8, flutter=2.4, near_x=14.0, near_y=-30.0,
          far_x=-10.0, far_y=-28.0, eyes="happy", mouth_open=0.3),
    ]),
    # Up over the edge with the near corner swept along the floor.
    "ledge_attack": (60, [
        dict(_HANG, y=-14.0, near_y=-40.0, far_y=-38.0, eyes="narrow"),
        K(squash_x=1.1, squash_y=0.88, lean=8.0, hem_dx=-6.0, near_x=40.0, near_y=16.0, far_x=-12.0,
          far_y=6.0, eyes="narrow", mouth_open=0.6, fx="and", fx_strength=0.7),
        K(squash_x=1.04, squash_y=0.96, lean=3.0, near_x=10.0, near_y=6.0, far_x=-4.0, far_y=4.0),
    ]),
    "ledge_drop": (70, [
        dict(_HANG, y=-2.0, near_y=-40.0, far_y=-38.0, near_x=10.0, far_x=14.0),
        K(y=-10.0, hem_spread=1.18, flutter=-2.0, near_x=14.0, near_y=-28.0, far_x=-4.0, far_y=-26.0,
          eyes="wide", mouth_open=0.3),
    ]),
    # -- held --------------------------------------------------------------
    # The captor holds him at the front: corners close in on him.
    "grab_hold": (150, [
        K(lean=4.0, hem_dx=-3.0, near_x=22.0, near_y=-2.0, far_x=34.0, far_y=-4.0, eyes="narrow",
          mouth_open=0.2),
        K(lean=4.5, hem_dx=-3.0, near_x=23.0, near_y=-1.0, far_x=35.0, far_y=-3.0, eyes="narrow",
          mouth_open=0.25, phase=0.25),
    ]),
    "grab_release": (70, [
        K(lean=-4.0, hem_dx=3.0, near_x=26.0, near_y=-16.0, far_x=38.0, far_y=-20.0, eyes="wide",
          mouth_open=0.4),
        K(lean=-2.0, hem_dx=1.0, near_x=8.0, near_y=-4.0, far_x=8.0, far_y=-6.0),
    ]),
    # In somebody's grip: lifted, pinched at the dome, corners dangling.
    "grabbed": (110, [
        K(y=-6.0, tilt=-4.0, lean=8.0, hem_dx=-6.0, hem_spread=0.9, near_x=-4.0, near_y=16.0, far_x=4.0,
          far_y=16.0, eyes="wide", mouth_open=0.5),
        K(y=-6.0, tilt=-2.0, lean=6.0, hem_dx=-3.0, hem_spread=0.92, near_x=-2.0, near_y=12.0, far_x=8.0,
          far_y=18.0, eyes="wide", mouth_open=0.6, phase=0.25),
    ]),
    "grabbed_pummel": (60, [
        K(y=-6.0, tilt=6.0, lean=-10.0, hem_dx=6.0, hem_spread=0.94, flutter=2.0, near_x=-10.0, near_y=-10.0,
          far_x=-8.0, far_y=-6.0, eyes="closed", mouth_open=0.9),
        K(y=-6.0, tilt=-1.0, lean=4.0, hem_dx=-4.0, hem_spread=0.9, near_x=-4.0, near_y=14.0, far_x=4.0,
          far_y=14.0, eyes="closed", mouth_open=0.6),
    ]),
    # Wriggling out: thinned, slipping back out of the grip.
    "grab_escape": (60, [
        K(x=-4.0, lean=-8.0, squash_x=0.84, squash_y=1.04, hem_dx=2.0, near_x=-8.0, near_y=4.0, far_x=-2.0,
          far_y=2.0, eyes="narrow", mouth_open=0.3),
        K(x=-8.0, lean=-12.0, tilt=4.0, squash_x=0.86, hem_dx=6.0, flutter=2.0, near_x=-14.0, near_y=-4.0,
          far_x=-18.0, far_y=-2.0, eyes="narrow", mouth_open=0.2),
    ]),
    # -- trip --------------------------------------------------------------
    "trip_fall": (70, [
        K(tilt=24.0, lean=-8.0, hem_dx=12.0, flutter=2.4, near_x=14.0, near_y=-28.0, far_x=-14.0, far_y=-22.0,
          eyes="wide", mouth_open=0.8),
        dict(_SITTING, eyes="closed", mouth_open=0.6, near_x=6.0, near_y=-6.0),
    ]),
    "trip_idle": (200, [dict(_SITTING)]),
    "trip_getup": (80, [
        dict(_SITTING, far_y=20.0, near_x=4.0, near_y=16.0, eyes="narrow"),
        K(squash_x=1.12, squash_y=0.82, lean=4.0, hem_spread=1.14, near_x=4.0, near_y=12.0, far_x=-6.0,
          far_y=12.0, eyes="narrow"),
        K(squash_x=1.04, squash_y=0.96, lean=1.0, near_x=2.0, near_y=4.0, far_x=-2.0, far_y=4.0),
    ]),
    # From sitting: the near corner swept along the floor in front.
    "trip_attack": (60, [
        dict(_SITTING, near_x=-12.0, near_y=10.0, eyes="narrow"),
        dict(_SITTING, lean=2.0, tilt=6.0, near_x=16.0, near_y=22.0, eyes="narrow", mouth_open=0.6, fx="and",
             fx_strength=0.6),
        dict(_SITTING, near_x=8.0, near_y=20.0, eyes="narrow"),
    ]),
    "trip_roll": (60, [
        _tuck(60.0, floor=True),
        _tuck(150.0, floor=True),
        _tuck(240.0, floor=True),
        K(squash_x=1.08, squash_y=0.9, hem_spread=1.08, near_x=-2.0, near_y=8.0, far_x=2.0, far_y=8.0,
          eyes="narrow"),
    ]),
    # -- stage -------------------------------------------------------------
    # He rises out of an empty sheet on the floor (his death, run backward)
    # with a BOO.
    "entrance": (110, [
        K(floor=True, squash_x=1.5, squash_y=0.3, hem_spread=1.25, flutter=0.2, near_x=4.0, near_y=20.0,
          far_x=12.0, far_y=20.0, collapse=1.0, eyes="closed", opacity=0.5),
        K(squash_x=1.24, squash_y=0.62, hem_spread=1.14, flutter=0.8, near_x=0.0, near_y=12.0, far_x=4.0,
          far_y=12.0, eyes="closed", opacity=0.8),
        K(y=-6.0, stretch=-2.0, squash_x=0.94, squash_y=1.08, flutter=1.8, near_x=14.0, near_y=-46.0,
          far_x=-12.0, far_y=-44.0, eyes="wide", mouth_open=1.0),
        K(near_x=2.0, near_y=-2.0, far_x=-2.0, far_y=-2.0, eyes="happy", mouth_open=0.3),
    ]),
    # The proposition stands: the near corner points up, a TRUE flash.
    "victory": (110, [
        K(squash_x=1.1, squash_y=0.86, near_x=-4.0, near_y=8.0, far_x=4.0, far_y=8.0, eyes="narrow"),
        K(y=-6.0, stretch=-2.0, squash_x=0.94, squash_y=1.05, near_x=10.0, near_y=-48.0, far_x=-6.0,
          far_y=6.0, eyes="happy", mouth_open=0.6, fx="toggle", fx_strength=1.0),
        K(stretch=-2.0, lean=-2.0, near_x=10.0, near_y=-52.0, far_x=-4.0, far_y=4.0, eyes="happy",
          mouth_open=0.3),
    ]),
    "victory_hold": (200, [
        K(stretch=-2.0, lean=-2.0, near_x=10.0, near_y=-52.0, far_x=-4.0, far_y=4.0, eyes="happy",
          mouth_open=0.3),
        K(stretch=-2.5, lean=-1.0, near_x=11.0, near_y=-54.0, far_x=-4.0, far_y=5.0, eyes="happy",
          mouth_open=0.25, phase=0.25),
    ]),
    # The loss: proven FALSE, slumped, the corners hanging.
    "loss": (220, [
        K(state=0.0, lean=6.0, stretch=6.0, squash_y=0.92, near_x=-4.0, near_y=18.0, far_x=4.0, far_y=18.0,
          eyes="closed", mouth_open=0.1, flutter=0.5),
        K(state=0.0, lean=7.0, stretch=7.0, squash_y=0.91, near_x=-4.0, near_y=19.0, far_x=4.0, far_y=19.0,
          eyes="closed", mouth_open=0.05, flutter=0.5, phase=0.25),
    ]),
    # TRUE, NOT, AND: gathered, thrown open in gold, inverted, and both
    # corners driven forward as one.
    "final_smash": (90, [
        K(squash_x=1.16, squash_y=0.82, near_x=-6.0, near_y=8.0, far_x=6.0, far_y=8.0, eyes="narrow"),
        K(y=-8.0, stretch=-3.0, squash_x=0.92, squash_y=1.1, near_x=16.0, near_y=-50.0, far_x=-16.0,
          far_y=-48.0, eyes="wide", mouth_open=0.8, fx="toggle", fx_strength=1.0),
        K(state=0.0, y=-8.0, stretch=-3.0, squash_x=0.92, squash_y=1.1, near_x=18.0, near_y=-50.0, far_x=-18.0,
          far_y=-48.0, eyes="wide", mouth_open=0.9, fx="not", fx_strength=1.0),
        K(state=0.0, x=10.0, lean=16.0, tilt=-3.0, hem_dx=-14.0, near_x=40.0, near_y=-4.0, far_x=70.0,
          far_y=-2.0, squash_x=1.06, squash_y=0.96, eyes="wide", mouth_open=1.0, fx="and", fx_strength=1.0,
          flutter=2.0),
        K(lean=2.0, near_x=4.0, near_y=2.0, far_x=-2.0, far_y=2.0, eyes="happy", mouth_open=0.3),
    ]),
}

#: The crouch transitions, derived from the crouch so its depth is tuned in
#: one place.
ROWS_SPEC["crouch_start"] = (50, [_toward({}, _CROUCH, 0.45), _toward({}, _CROUCH, 0.8)])
ROWS_SPEC["crouch_end"] = (50, [_toward({}, _CROUCH, 0.7), _toward({}, _CROUCH, 0.3)])

#: His smash charges: each smash's wind-up, held and shivering
#: (``george_booul.ATTACK_POSES``). Drawn by the target, not keyed here.
SMASH_CHARGES = {"smash_charge_forward": "smash_forward", "smash_charge_up": "smash_up",
                 "smash_charge_down": "smash_down"}
SMASH_CHARGE_MS = 80


def fighter_rows() -> List[Tuple[str, int, int]]:
    """The rows this module adds, in sheet order."""
    rows = [(name, len(keys), ms) for name, (ms, keys) in ROWS_SPEC.items()]
    rows += [(name, 2, SMASH_CHARGE_MS) for name in SMASH_CHARGES]
    return rows


#: Every ``fighter_core`` category of ``fighter_motion_vocabulary.yaml``, and
#: the row of his that draws it. Several categories may share a row.
FIGHTER_MOTION_COVERAGE: Dict[str, str] = {
    "idle": "idle", "idle_look_up": "idle_look_up", "walk": "walk", "crouch_walk": "crouch_walk",
    "crouch_jump": "crouch_jump", "locomotion_stop": "run_stop", "turnaround": "turnaround",
    "dash_startup": "dash_startup", "run": "run", "stumble": "stumble", "crouch_start": "crouch_start",
    "crouch": "crouch", "crouch_end": "crouch_end", "land_light": "land_light", "land_hard": "land_hard",
    "jump_squat": "jump_squat", "jump": "jump", "double_jump": "double_jump", "fall": "fall",
    "fall_special": "fall_special", "land_special": "land_hard", "tumble": "tumble",
    "shield_raise": "shield_raise", "shield_hold": "block", "shield_release": "shield_release",
    "parry": "parry", "shield_hit": "shield_hit", "spot_dodge": "spot_dodge", "roll_forward": "roll",
    "roll_backward": "roll_back", "air_dodge": "air_dodge", "jab": "jab", "dash_attack": "dash_attack",
    "attack_side": "attack_side", "attack_up": "attack_up", "attack_down": "attack_down",
    "smash_charge_forward": "smash_charge_forward", "smash_forward": "smash_forward",
    "smash_charge_up": "smash_charge_up", "smash_up": "smash_up", "smash_charge_down": "smash_charge_down",
    "smash_down": "smash_down", "air_neutral": "air_neutral", "air_forward": "air_forward",
    "air_back": "air_back", "air_up": "air_up", "air_down": "air_down", "air_land": "air_land",
    "special_neutral": "special", "special_side": "special_side", "special_up": "special_up",
    "special_down": "special_down", "final_smash": "final_smash", "grab": "grab", "grab_hold": "grab_hold",
    "pummel": "pummel", "grab_release": "grab_release", "throw_forward": "throw_forward",
    "throw_back": "throw_back", "throw_up": "throw_up", "throw_down": "throw_down", "grabbed": "grabbed",
    "grabbed_pummel": "grabbed_pummel", "grab_escape": "grab_escape", "hit": "hit", "launch": "launch",
    "meteor": "meteor", "impact": "impact", "splat": "splat", "ground_bounce": "ground_bounce",
    "prone": "prone", "prone_damage": "prone_damage", "getup": "getup", "getup_attack": "getup_attack",
    "getup_roll": "getup_roll", "knockdown": "knockdown", "tech": "tech", "tech_roll": "tech_roll",
    "wall_tech": "wall_tech", "wall_tech_jump": "wall_tech_jump", "ceiling_tech": "ceiling_tech",
    "shield_break_launch": "shield_break_launch", "shield_break_fall": "shield_break_fall",
    "shield_break_collapse": "shield_break_collapse", "shield_break_recover": "shield_break_recover",
    "dizzy": "dizzy", "sleep_start": "sleep_start", "sleep": "sleep", "wake": "wake",
    "bury_start": "bury_start", "buried": "buried", "bury_escape": "bury_escape",
    "footstool_jump": "footstool_jump", "footstooled": "footstooled", "platform_drop": "platform_drop",
    "teeter_start": "teeter_start", "teeter": "teeter", "lose_footing": "stumble",
    "ledge_catch": "ledge_catch", "ledge_hang": "ledge_grab", "ledge_getup": "ledge_getup",
    "ledge_attack": "ledge_attack", "ledge_roll": "ledge_roll", "ledge_jump": "ledge_jump",
    "ledge_drop": "ledge_drop", "trip_fall": "trip_fall", "trip_land": "trip_fall", "trip_idle": "trip_idle",
    "trip_getup": "trip_getup", "trip_attack": "trip_attack", "trip_roll": "trip_roll", "taunt": "taunt",
    "entrance": "entrance", "victory": "victory", "victory_hold": "victory_hold", "loss": "loss",
}

APPLICABLE_MOTION_SCOPES = ("fighter_core",)

__all__ = ["APPLICABLE_MOTION_SCOPES", "FIGHTER_MOTION_COVERAGE", "REST", "ROWS_SPEC", "SMASH_CHARGES",
           "SMASH_CHARGE_MS", "fighter_rows"]
