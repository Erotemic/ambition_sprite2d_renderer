"""The Pirate Admiral's fighter body language: how he moves, takes a hit, lies
on the deck, gets up, guards, hangs from a ledge and is held.

His attack rows are ``_pirate_admiral_moves``. These are the rows a Smash
fighter shows between attacks (``data/fighter_motion_vocabulary.yaml``, scope
``fighter_core``), on his own pirate rig and in the same channels. He is a
heavy, proud commander: chin up, chest out, the cutlass always in his hand. A
hit knocks the hat askew and the dignity out of him for a moment.

A row is keyed over its own length (0 to 1) or is a function of the phase of
a loop. Each key names channels of ``_pirate_common.home_pose``; a channel a
key leaves out is at the guard. Two channels are this module's own:

- ``spin``: degrees the whole body is turned about a point ``pivot`` paint px
  over the root (clockwise is forward: a forward flip goes 0 to 360). The
  pose of a key is drawn upright; ``spin`` turns all of it, so a tumble or a
  roll keys the body once and the turn separately.
- ``lift``: paint px over the floor for a body that is placed on it.

Placement, after the turn:

- ``plant``: the lower foot on the ground (``_pirate_common.planted``), as
  every standing row of the family.
- ``floor``: the lowest paint of the body on the floor line, the line the
  soles of the guard stand on. A body lying, kneeling or rolling is ON the
  floor, whatever part of it is lowest.
- ``air``: the root where the guard has it (the attack rows' aerials do the
  same): the game puts an airborne body where its box is.

``feet`` names legs whose shin is then turned so the foot stands on the
ground too: a pose with both feet down keys only the thighs and one shin.

A recoil (``hit_*``) starts on the struck pose and ends on its settled pose:
the animator holds the last frame for the hitstun.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Dict, Final, List, Mapping, Tuple, Union

from ...authoring.sheet_build import BASE_FRAME, SCALE, transform
from . import _pirate_rig as rig

KIND: Final = "pirate_admiral"

Channels = Dict[str, float]
#: (time 0..1, ease into this key, channels).
Key = Tuple[float, str, Channels]

#: The limb channels a whole-body turn adds its angle to.
_LIMBS = (
    "left_thigh", "left_shin", "right_thigh", "right_shin",
    "sword_upper", "sword_fore", "off_upper", "off_fore", "weapon",
)

#: The face is a part painted once per look: the mouth snaps to the family's.
_MOUTHS = (0.0, 0.3, 0.6, 0.8)

_EASES: Dict[str, Callable[[float], float]] = {
    "smooth": lambda t: t * t * (3.0 - 2.0 * t),
    # An impact: fast off the mark, slow into the key.
    "out": lambda t: 1.0 - (1.0 - t) ** 3,
    # A gather: slow off the mark, fast into the key.
    "in": lambda t: t * t,
    "lin": lambda t: t,
}


def K(t: float, *parts: Mapping[str, float], ease: str = "smooth") -> Key:
    """A key at ``t``: the channels of ``parts``, merged in order."""
    out: Channels = {}
    for part in parts:
        out.update(part)
    return (t, ease, out)


def legs(back_thigh: float, back_shin: float, front_thigh: float, front_shin: float) -> Channels:
    """The two legs. The back leg is ``left`` in the rig, the front ``right``."""
    return {"left_thigh": back_thigh, "left_shin": back_shin,
            "right_thigh": front_thigh, "right_shin": front_shin}


def sword(upper: float, fore: float, weapon: float) -> Channels:
    """The sword arm (the front arm) and the blade's own angle (0 to the
    front, -90 up, 90 down)."""
    return {"sword_upper": upper, "sword_fore": fore, "weapon": weapon}


def off(upper: float, fore: float) -> Channels:
    """The free arm (the back arm)."""
    return {"off_upper": upper, "off_fore": fore}


def _merge(*parts: Mapping[str, float]) -> Channels:
    out: Channels = {}
    for part in parts:
        out.update(part)
    return out


@dataclass(frozen=True)
class Row:
    frames: int
    ms: int
    #: Keys over 0..1, or a function of the phase (0..1) to channels.
    keys: Union[Tuple[Key, ...], Callable[[float], Channels]]
    place: str = "plant"
    loop: bool = False
    #: Legs to stand on the ground after the placement: "left", "right".
    feet: Tuple[str, ...] = ()


# ── the poses the rows are made of ──────────────────────────────────────────

#: Crouched low: the front knee deep, the back knee near the deck, the cutlass
#: held forward and low over the front knee, the head down under the hat.
CROUCH = _merge(
    legs(40.0, 100.0, -88.0, 24.0),
    sword(-40.0, -100.0, -22.0), off(-30.0, -8.0),
    {"body_tilt": 28.0, "head_tilt": -12.0, "hat_tilt": 6.0, "coat_sway": 18.0, "shoulder_bounce": 2.0},
)

#: The block: a hanging guard. The sword hand high in front of the brow, the
#: blade down across the body, the free hand braced on the flat of it, the feet
#: wide and the head tucked in behind it.
BLOCK = _merge(
    legs(42.0, 70.0, -42.0, -6.0),
    sword(-128.0, -150.0, 104.0), off(-58.0, -118.0),
    {"body_tilt": -6.0, "root_x": -1.0, "head_tilt": 8.0, "hat_tilt": 4.0, "coat_sway": 6.0, "mouth_open": 0.3},
)

#: In the air, rising: the front knee drawn up, the back leg long under him,
#: the cutlass raised high to the front, the free arm swung down behind.
RISE = _merge(
    legs(20.0, 36.0, -78.0, -6.0),
    sword(-150.0, -168.0, -64.0), off(46.0, 30.0),
    {"body_tilt": -5.0, "head_tilt": -10.0, "hat_tilt": -4.0, "coat_sway": 10.0, "mouth_open": 0.3},
)

#: In the air, coming down: the legs a little apart and bent, the arms out
#: and up for balance, the coat flared, looking down at the deck.
DROP = _merge(
    legs(16.0, 36.0, -22.0, 2.0),
    sword(-104.0, -136.0, -58.0), off(112.0, 136.0),
    {"body_tilt": 0.0, "head_tilt": 6.0, "hat_tilt": -6.0, "coat_sway": 24.0},
)

#: A tight ball: the knees to the chest, the arms round them, the chin in.
TUCK = _merge(
    legs(-112.0, -6.0, -124.0, 4.0),
    sword(-40.0, -118.0, 10.0), off(-30.0, -110.0),
    {"body_tilt": 10.0, "head_tilt": 12.0, "hat_tilt": 4.0, "coat_sway": 20.0},
)

#: On his back on the deck, the head to the back: the front knee up, the sword
#: arm flung out over his head along the deck, the free hand on his belly.
#: Keyed standing and laid down by ``spin`` (-90: the head goes back).
FACE_UP = _merge(
    legs(4.0, 6.0, -52.0, 30.0),
    sword(-174.0, -182.0, -100.0), off(-20.0, -100.0),
    {"body_tilt": 0.0, "head_tilt": -6.0, "hat_tilt": -12.0, "coat_sway": -8.0, "mouth_open": 0.3,
     "spin": -90.0},
)

#: On his belly, the head to the front: the legs long behind him, one foot up,
#: the sword arm reaching on along the deck past his head, the face turned up
#: off the planks.
FACE_DOWN = _merge(
    legs(2.0, 4.0, 8.0, 84.0),
    sword(-172.0, -178.0, -88.0), off(-36.0, -150.0),
    {"body_tilt": 0.0, "head_tilt": -14.0, "hat_tilt": -6.0, "coat_sway": 10.0, "mouth_open": 0.3,
     "spin": 90.0},
)

#: Hanging from a ledge by both hands, the cutlass still in his fist and laid
#: flat along the top of the edge, the legs hanging, looking up at it.
HANG = _merge(
    legs(6.0, 14.0, -6.0, 2.0),
    sword(-160.0, -168.0, -8.0), off(-166.0, -172.0),
    {"body_tilt": -2.0, "head_tilt": -14.0, "hat_tilt": -4.0, "coat_sway": -2.0, "shoulder_bounce": -3.0},
)

#: Holding a foe at arm's length by the collar, the cutlass cocked back at the
#: shoulder with its point at him, chest out.
HOLD = _merge(
    legs(24.0, 30.0, -26.0, -10.0),
    sword(-36.0, -170.0, -14.0), off(-84.0, -90.0),
    {"body_tilt": -2.0, "head_tilt": -6.0, "hat_tilt": -2.0, "mouth_open": 0.3},
)

#: Held by a foe in front of him: leaning back from the grip, the free hand
#: pushing at the arm that holds him, the cutlass arm drawn back, the feet
#: braced.
HELD = _merge(
    legs(34.0, 44.0, -28.0, -20.0),
    sword(52.0, 20.0, 150.0), off(-70.0, -100.0),
    {"body_tilt": -12.0, "root_x": -2.0, "head_tilt": 10.0, "hat_tilt": -10.0, "coat_sway": 8.0,
     "mouth_open": 0.6},
)


# ── loops as functions of the phase ─────────────────────────────────────────

def _stride(p: float, *, lean: float, reach: float, bias: float, kick: float) -> Channels:
    """The legs of a run: each thigh swings ``reach`` about ``bias`` and the
    knee folds by ``kick`` while the leg comes through to the front."""
    a = p * math.tau
    out: Channels = {}
    for side, at in (("left", a), ("right", a + math.pi)):
        thigh = bias + reach * math.sin(at)
        out[f"{side}_thigh"] = thigh
        out[f"{side}_shin"] = thigh + 18.0 + kick * max(0.0, -math.cos(at))
    out["body_tilt"] = lean
    return out


def _run(p: float) -> Channels:
    """The run: the cutlass carried up in front, ready, the free arm pumping
    against the back leg, the coat swinging. Leaning in, chin up."""
    a = p * math.tau
    s, c2 = math.sin(a), math.cos(2.0 * a)
    out = _stride(p, lean=13.0, reach=38.0, bias=-10.0, kick=84.0)
    out.update(
        sword_upper=-38.0 + 22.0 * s, sword_fore=-112.0 + 12.0 * s, weapon=-74.0 + 6.0 * c2,
        off_upper=12.0 - 44.0 * s, off_fore=-58.0 - 40.0 * s,
        head_tilt=-9.0, hat_tilt=3.0 * s, coat_sway=12.0 * s + 6.0,
        shoulder_bounce=2.0 * c2, mouth_open=0.3,
    )
    return out


def _dash(p: float) -> Channels:
    """The dash: lower and longer than the run, the cutlass trailed low behind
    with its point back, the free arm driving, shouting."""
    a = p * math.tau
    s, c2 = math.sin(a), math.cos(2.0 * a)
    out = _stride(p, lean=21.0, reach=46.0, bias=-14.0, kick=100.0)
    out.update(
        sword_upper=44.0 + 8.0 * s, sword_fore=62.0 + 6.0 * s, weapon=164.0 + 4.0 * c2,
        off_upper=-20.0 - 56.0 * s, off_fore=-96.0 - 44.0 * s,
        head_tilt=-14.0, hat_tilt=-6.0, coat_sway=22.0 + 6.0 * s,
        shoulder_bounce=2.5 * c2, mouth_open=0.6,
    )
    return out


def _crouch_walk(p: float) -> Channels:
    """A low shuffle under the guard of the cutlass."""
    a = p * math.tau
    s, c = math.sin(a), math.cos(a)
    out = _merge(CROUCH)
    for side, at in (("left", a), ("right", a + math.pi)):
        thigh = -30.0 + 34.0 * math.sin(at)
        out[f"{side}_thigh"] = thigh
        out[f"{side}_shin"] = thigh + 62.0 + 30.0 * max(0.0, -math.cos(at))
    out.update(body_tilt=20.0 + 1.5 * c, sword_upper=-46.0 + 6.0 * s, coat_sway=16.0 + 6.0 * s,
               hat_tilt=6.0 + 2.0 * c)
    return out


def _skid(p: float) -> Channels:
    """Braking from a dash: leaning back hard, the front heel digging in ahead
    of him, the back knee bent under, the cutlass flung up behind for
    balance. The heel judders."""
    a = p * math.tau
    s, c = math.sin(a), math.cos(a)
    return _merge(
        legs(10.0 + 2.0 * s, 74.0, -50.0 + 1.5 * c, -42.0),
        sword(118.0 + 4.0 * s, 152.0 + 4.0 * c, -150.0), off(-74.0 + 4.0 * c, -104.0),
        {"body_tilt": -15.0 + 1.5 * s, "root_x": 2.0 + 0.6 * c, "head_tilt": -4.0, "hat_tilt": 9.0 + 2.0 * s,
         "coat_sway": -20.0 + 4.0 * c, "mouth_open": 0.6},
    )


def _teeter(p: float) -> Channels:
    """On the brink: pitched out over the edge in front, the back leg kicked up
    behind as a counterweight, both arms windmilling, gasping."""
    a = p * math.tau
    s, c = math.sin(a), math.cos(a)
    return _merge(
        legs(44.0 + 10.0 * s, 78.0 + 12.0 * s, -4.0, -2.0),
        sword(-150.0 + 46.0 * s, -176.0 + 40.0 * s, -70.0 + 40.0 * s),
        off(-120.0 + 50.0 * c, -150.0 + 50.0 * c),
        {"body_tilt": 13.0 + 5.0 * c, "root_x": 1.0 * s, "head_tilt": -12.0 + 2.0 * s,
         "hat_tilt": 7.0 * s, "coat_sway": 10.0 * c, "mouth_open": 0.6},
    )


def _hover(base: Channels, *, coat: float = 6.0, hat: float = 3.0, limb: float = 3.0) -> Callable[[float], Channels]:
    """A held air pose that flutters: the coat, the hat and the limbs a little."""
    def at(p: float) -> Channels:
        a = p * math.tau
        s, c = math.sin(a), math.cos(a)
        out = dict(base)
        out["coat_sway"] = base.get("coat_sway", 0.0) + coat * s
        out["hat_tilt"] = base.get("hat_tilt", 0.0) + hat * c
        for name, k in (("left_shin", 1.0), ("right_shin", -1.0), ("off_fore", 1.0), ("sword_fore", -1.0)):
            out[name] = base.get(name, 0.0) + limb * k * s
        out["shoulder_bounce"] = base.get("shoulder_bounce", 0.0) + 1.2 * c
        return out
    return at


def _breathe(base: Channels, *, blink_at: float = -1.0, chest: float = 2.0) -> Callable[[float], Channels]:
    """A held pose that breathes: the chest rises, the head and the coat move
    a little. ``blink_at`` is the phase of a blink."""
    def at(p: float) -> Channels:
        a = p * math.tau
        s, c = math.sin(a), math.cos(a)
        out = dict(base)
        out["shoulder_bounce"] = base.get("shoulder_bounce", 0.0) - chest * s
        out["head_tilt"] = base.get("head_tilt", 0.0) + 1.2 * c
        out["coat_sway"] = base.get("coat_sway", 0.0) + 2.0 * c
        out["off_fore"] = base.get("off_fore", 0.0) + 2.5 * s
        out["sword_fore"] = base.get("sword_fore", 0.0) - 1.5 * c
        if blink_at >= 0.0 and abs(p - blink_at) < 1e-6:
            out["blink"] = True
        return out
    return at


def _tumble(p: float) -> Channels:
    """Tumbling: a loose ball turned over and over, the limbs flailing."""
    a = p * math.tau
    s, c = math.sin(a), math.cos(a)
    return _merge(
        legs(-70.0 + 20.0 * s, 10.0 + 20.0 * c, -100.0 - 16.0 * c, -20.0 + 18.0 * s),
        sword(-150.0 + 24.0 * c, -190.0 + 20.0 * s, -150.0), off(60.0 + 30.0 * s, 100.0 + 20.0 * c),
        {"body_tilt": 6.0, "head_tilt": 10.0, "hat_tilt": -14.0, "coat_sway": 26.0 + 8.0 * s,
         "mouth_open": 0.6, "spin": -360.0 * p},
    )


def _dizzy(p: float) -> Channels:
    """Seeing stars: swaying on his heels in a circle, the head lolling, the
    cutlass drooping, the eye half shut."""
    a = p * math.tau
    s, c = math.sin(a), math.cos(a)
    return _merge(
        legs(22.0 + 4.0 * c, 34.0, -18.0 + 4.0 * c, -4.0),
        sword(4.0 + 6.0 * s, -20.0 + 8.0 * s, 16.0 + 10.0 * s), off(18.0 - 6.0 * s, 4.0 - 6.0 * c),
        {"body_tilt": 6.0 * s, "root_x": 2.0 * c, "head_tilt": 10.0 * s + 4.0, "hat_tilt": -10.0 + 8.0 * c,
         "coat_sway": 8.0 * s, "mouth_open": 0.3, "blink": s > 0.7},
    )


def _grab_hold(p: float) -> Channels:
    a = p * math.tau
    s, c = math.sin(a), math.cos(a)
    return _merge(HOLD, {"sword_fore": -170.0 + 4.0 * s, "weapon": -14.0 + 4.0 * c, "body_tilt": -2.0 + 1.0 * c,
                         "shoulder_bounce": -1.5 * s, "off_upper": -84.0 + 1.5 * s, "coat_sway": 3.0 * c})


def _grabbed(p: float) -> Channels:
    a = p * math.tau
    s, c = math.sin(a), math.cos(a)
    return _merge(HELD, {"off_upper": -70.0 + 10.0 * s, "off_fore": -100.0 + 12.0 * s,
                         "sword_upper": 52.0 + 10.0 * c, "body_tilt": -12.0 + 3.0 * c, "root_x": -2.0 + 1.0 * s,
                         "head_tilt": 10.0 - 3.0 * s, "coat_sway": 8.0 + 4.0 * c,
                         "left_thigh": 34.0 + 3.0 * s})


def _hang(p: float) -> Channels:
    """The hang, swinging a little from the hand, the legs kicking slowly."""
    a = p * math.tau
    s, c = math.sin(a), math.cos(a)
    return _merge(HANG, {"spin": 3.0 * s, "pivot": 250.0, "left_thigh": 6.0 + 6.0 * c,
                         "right_thigh": -6.0 - 6.0 * c, "left_shin": 14.0 + 8.0 * c, "right_shin": 2.0 - 4.0 * c,
                         "coat_sway": -2.0 + 4.0 * s, "head_tilt": -14.0 + 1.5 * c})


# ── the rows ─────────────────────────────────────────────────────────────────

#: The hit poses: struck at the head, the gut, the legs and in the air. Each
#: is the struck pose, its peak, and the pose it settles in for the hitstun.
_HIT_HIGH = _merge(
    legs(28.0, 58.0, -34.0, -30.0),
    sword(136.0, 170.0, -150.0), off(116.0, 150.0),
    {"body_tilt": -16.0, "root_x": 1.0, "head_tilt": -16.0, "hat_tilt": -24.0, "coat_sway": -10.0,
     "mouth_open": 0.8},
)
_HIT_MID = _merge(
    legs(30.0, 62.0, -24.0, 12.0),
    sword(46.0, 30.0, 140.0), off(-36.0, -126.0),
    {"body_tilt": 30.0, "root_x": -3.0, "head_tilt": 12.0, "hat_tilt": 12.0, "coat_sway": -18.0,
     "mouth_open": 0.8, "blink": True, "shoulder_bounce": 3.0},
)
_HIT_LOW = _merge(
    legs(30.0, 120.0, -60.0, 70.0),
    sword(136.0, 166.0, -140.0), off(-30.0, 10.0),
    {"body_tilt": 30.0, "root_x": 0.0, "head_tilt": 12.0, "hat_tilt": 14.0, "coat_sway": 22.0,
     "mouth_open": 0.6},
)
#: In the air he curls round the blow: the knees jerked up, the free arm over
#: his head, the cutlass flung out behind.
_HIT_AIR = _merge(
    legs(-70.0, 10.0, -100.0, -20.0),
    sword(110.0, 150.0, 170.0), off(-160.0, -230.0),
    {"body_tilt": 14.0, "head_tilt": 14.0, "hat_tilt": 16.0, "coat_sway": 34.0, "mouth_open": 0.8,
     "lift": 14.0},
)

ROWS_SPEC: Dict[str, Row] = {}


def _row(name: str, frames: int, ms: int, keys, place: str = "plant", loop: bool = False,
         feet: Tuple[str, ...] = ()) -> None:
    ROWS_SPEC[name] = Row(frames, ms, tuple(keys) if not callable(keys) else keys, place, loop, feet)


# 1. Movement.
_row("run", 8, 72, _run, loop=True)
_row("dash_startup", 4, 48, [
    K(0.0, legs(30.0, 62.0, -40.0, 12.0), sword(26.0, 8.0, 150.0), off(-40.0, -80.0),
      {"body_tilt": 8.0, "root_x": -2.0, "head_tilt": -8.0, "coat_sway": 8.0}),
    K(0.5, legs(46.0, 52.0, -78.0, -10.0), sword(40.0, 52.0, 160.0), off(-70.0, -120.0),
      {"body_tilt": 24.0, "head_tilt": -14.0, "hat_tilt": -6.0, "coat_sway": 20.0, "mouth_open": 0.6}, ease="out"),
    K(1.0, _dash(0.0)),
])
_row("dash", 6, 62, _dash, loop=True)
_row("skid", 6, 55, _skid, loop=True)
# Drawn in the NEW facing: it starts still looking back the way he came, the
# cutlass trailing behind, and ends square in the guard.
_row("turnaround", 5, 44, [
    K(0.0, legs(-16.0, 2.0, 18.0, 44.0), sword(64.0, 84.0, 172.0), off(-56.0, -86.0),
      {"body_tilt": -8.0, "root_x": -2.0, "head_tilt": 10.0, "hat_tilt": -8.0, "coat_sway": -18.0}),
    K(0.45, legs(4.0, 10.0, -4.0, 6.0), sword(-24.0, -150.0, -104.0), off(10.0, -10.0),
      {"body_tilt": -2.0, "head_tilt": 2.0, "coat_sway": 6.0}),
    K(1.0, {}),
])
_row("walk_stop", 5, 70, [
    K(0.0, legs(24.0, 40.0, -28.0, -12.0), sword(-14.0, -72.0, -34.0), off(-6.0, -28.0),
      {"body_tilt": 7.0, "coat_sway": -10.0}),
    K(0.4, legs(12.0, 34.0, -24.0, -8.0), sword(-20.0, -80.0, -40.0), off(-14.0, -36.0),
      {"body_tilt": 9.0, "root_x": 1.0, "coat_sway": -16.0, "hat_tilt": 3.0}, ease="out"),
    K(0.75, {"body_tilt": -1.0, "coat_sway": 6.0, "hat_tilt": -1.0}),
    K(1.0, {}),
])
# The hard stop: the front foot slammed down ahead, the hips shoved back over
# the bent back leg, and the top of him carried on forward over it, the coat
# and the hat with it, then rocking back up.
_STOP = _merge(
    legs(34.0, 84.0, -48.0, -40.0), sword(-74.0, -104.0, -18.0), off(-64.0, -92.0),
    {"body_tilt": 20.0, "root_x": -3.0, "head_tilt": -12.0, "hat_tilt": 10.0, "coat_sway": -26.0, "mouth_open": 0.6},
)
_row("run_stop", 6, 50, [
    K(0.0, _STOP),
    K(0.3, _STOP, {"body_tilt": 26.0, "coat_sway": -32.0, "hat_tilt": 14.0, "sword_upper": -86.0, "off_upper": -76.0,
                   "left_shin": 96.0}, ease="out"),
    K(0.7, legs(18.0, 34.0, -32.0, -16.0), sword(-20.0, -70.0, -44.0), off(16.0, -4.0),
      {"body_tilt": 0.0, "root_x": -1.0, "coat_sway": 8.0, "hat_tilt": -2.0}),
    K(1.0, {}),
])
_row("jump_squat", 3, 40, [
    K(0.0, legs(26.0, 48.0, -40.0, 4.0), sword(10.0, -30.0, -60.0), off(40.0, 20.0),
      {"body_tilt": 8.0, "coat_sway": 6.0}),
    K(1.0, legs(46.0, 0.0, -80.0, 24.0), sword(44.0, 24.0, -172.0), off(60.0, 40.0),
      {"body_tilt": 26.0, "head_tilt": -10.0, "hat_tilt": 6.0, "coat_sway": 14.0, "shoulder_bounce": 3.0}),
], feet=("left",))
_row("jump", 6, 95, _hover(RISE), place="air", loop=True)
# A forward flip out of a kick in the air: the coat wheels round him.
_row("double_jump", 6, 64, [
    K(0.0, legs(-30.0, 30.0, -84.0, -30.0), sword(-160.0, -184.0, -100.0), off(-150.0, -176.0),
      {"body_tilt": -6.0, "head_tilt": -10.0, "coat_sway": 10.0, "mouth_open": 0.6}),
    K(0.22, TUCK, {"spin": 80.0}, ease="lin"),
    K(0.5, TUCK, {"spin": 200.0}, ease="lin"),
    K(0.78, TUCK, legs(-80.0, 10.0, -90.0, 0.0), {"spin": 320.0, "coat_sway": 26.0}, ease="lin"),
    K(1.0, DROP, {"spin": 360.0}),
], place="air")
_row("fall", 6, 95, _hover(DROP, coat=8.0, hat=4.0, limb=5.0), place="air", loop=True)
_row("land_recovery", 4, 55, [
    K(0.0, legs(40.0, 70.0, -56.0, 20.0), sword(-30.0, -70.0, -10.0), off(50.0, 30.0),
      {"body_tilt": 14.0, "head_tilt": -6.0, "coat_sway": 16.0, "shoulder_bounce": 3.0}),
    K(0.6, legs(22.0, 30.0, -28.0, 0.0), {"body_tilt": 6.0, "coat_sway": 4.0}),
    K(1.0, {}),
], feet=("left",))
_LAND_HARD = _merge(
    legs(60.0, 116.0, -78.0, 26.0), sword(64.0, 96.0, 172.0), off(-6.0, 4.0),
    {"body_tilt": 34.0, "head_tilt": 4.0, "hat_tilt": 16.0, "coat_sway": 26.0, "mouth_open": 0.6,
     "shoulder_bounce": 4.0},
)
_row("land_hard", 6, 70, [
    K(0.0, _LAND_HARD),
    K(0.3, _LAND_HARD, {"body_tilt": 38.0, "hat_tilt": 18.0, "coat_sway": 30.0}, ease="out"),
    K(0.7, CROUCH, {"body_tilt": 14.0, "hat_tilt": 8.0}),
    K(1.0, legs(22.0, 32.0, -28.0, -2.0), {"body_tilt": 6.0}),
], place="floor")
_row("crouch_start", 3, 45, [
    K(0.0, legs(24.0, 40.0, -34.0, 2.0), {"body_tilt": 6.0, "coat_sway": 6.0}),
    K(1.0, CROUCH),
], place="floor")
_row("crouch", 6, 110, _breathe(CROUCH, chest=1.5), place="floor", loop=True)
_row("crouch_end", 3, 45, [
    K(0.0, CROUCH),
    K(1.0, legs(20.0, 28.0, -26.0, -4.0), {"body_tilt": 4.0}),
], place="floor")
_row("crouch_walk", 8, 90, _crouch_walk, place="floor", loop=True)
_row("teeter_start", 4, 60, [
    K(0.0, legs(20.0, 26.0, -10.0, -4.0), {"body_tilt": 6.0}),
    K(0.5, legs(36.0, 60.0, -6.0, -2.0), sword(-140.0, -150.0, -60.0), off(-160.0, -190.0),
      {"body_tilt": 18.0, "head_tilt": -14.0, "hat_tilt": 10.0, "coat_sway": -12.0, "mouth_open": 0.8}, ease="out"),
    K(1.0, _teeter(0.0)),
])
_row("teeter", 8, 90, _teeter, loop=True)
_row("idle_look_up", 4, 120, [
    K(0.0, off(-40.0, -100.0), {"body_tilt": -2.0, "head_tilt": -8.0}),
    K(0.5, off(-112.0, -40.0), {"body_tilt": -6.0, "head_tilt": -15.0, "hat_tilt": -6.0, "root_x": -1.0}),
    K(1.0, off(-118.0, -36.0), {"body_tilt": -7.0, "head_tilt": -16.0, "hat_tilt": -8.0, "root_x": -1.0,
                                "shoulder_bounce": -1.5}),
])

# 2. Reactions.
_row("hit", 5, 56, [
    K(0.0, legs(26.0, 40.0, -22.0, -2.0), sword(-60.0, -150.0, -120.0), off(-50.0, -150.0),
      {"body_tilt": 6.0, "root_x": -3.0, "head_tilt": 12.0, "hat_tilt": 8.0, "coat_sway": -8.0,
       "mouth_open": 0.6, "blink": True, "shoulder_bounce": 4.0}),
    K(0.35, legs(28.0, 44.0, -24.0, -4.0), sword(-64.0, -156.0, -124.0), off(-54.0, -156.0),
      {"body_tilt": 8.0, "root_x": -4.0, "head_tilt": 14.0, "hat_tilt": 10.0, "coat_sway": -12.0,
       "mouth_open": 0.6, "blink": True, "shoulder_bounce": 5.0}, ease="out"),
    K(1.0, legs(22.0, 32.0, -22.0, -4.0), sword(-36.0, -112.0, -86.0), off(-14.0, -90.0),
      {"body_tilt": 5.0, "root_x": -2.0, "head_tilt": 6.0, "hat_tilt": 4.0, "coat_sway": -4.0,
       "mouth_open": 0.3, "shoulder_bounce": 2.0}),
])
_row("hit_high", 5, 52, [
    K(0.0, _HIT_HIGH, {"body_tilt": -12.0, "head_tilt": -12.0}),
    K(0.35, _HIT_HIGH, {"body_tilt": -19.0, "hat_tilt": -28.0}, ease="out"),
    K(1.0, _HIT_HIGH, legs(26.0, 50.0, -30.0, -24.0), sword(120.0, 150.0, -160.0), off(100.0, 130.0),
      {"body_tilt": -12.0, "head_tilt": -10.0, "hat_tilt": -18.0, "coat_sway": -6.0, "mouth_open": 0.6}),
], feet=("right",))
_row("hit_mid", 5, 52, [
    K(0.0, _HIT_MID, {"body_tilt": 24.0}),
    K(0.35, _HIT_MID, {"body_tilt": 36.0, "root_x": -4.0, "coat_sway": -24.0}, ease="out"),
    K(1.0, _HIT_MID, {"body_tilt": 28.0, "root_x": -3.0, "coat_sway": -12.0, "mouth_open": 0.6, "blink": False}),
], feet=("right",))
_row("hit_low", 5, 52, [
    K(0.0, _HIT_LOW, {"body_tilt": 14.0, "right_shin": 60.0, "right_thigh": -30.0, "lift": 8.0}),
    K(0.35, _HIT_LOW, {"body_tilt": 30.0, "hat_tilt": 18.0}, ease="out"),
    K(1.0, _HIT_LOW, {"body_tilt": 26.0, "sword_upper": 124.0, "sword_fore": 150.0, "mouth_open": 0.6}),
], place="floor")
_row("hit_air", 5, 52, [
    K(0.0, _HIT_AIR, {"spin": -10.0}),
    K(0.35, _HIT_AIR, {"spin": -22.0, "coat_sway": 40.0}, ease="out"),
    K(1.0, _HIT_AIR, {"spin": -16.0, "left_thigh": -56.0, "right_thigh": -86.0, "coat_sway": 28.0,
                      "mouth_open": 0.6}),
], place="air")

# The launches: each its own shape, the limbs trailing against the travel.
# Up: stretched long, arched back, arms and legs streaming down under him.
_LAUNCH_UP = _merge(
    legs(8.0, 12.0, 0.0, 6.0), sword(14.0, 16.0, 98.0), off(10.0, 14.0),
    {"body_tilt": -6.0, "head_tilt": -15.0, "hat_tilt": -26.0, "coat_sway": -6.0, "mouth_open": 0.8,
     "lift": 26.0},
)
# Away (to his back): bent double at the hips, the seat of him first, the head
# and the feet trailing to the front, the arms flung forward after them.
_LAUNCH_SIDE = _merge(
    legs(-50.0, -54.0, -62.0, -68.0), sword(-84.0, -92.0, -8.0), off(-96.0, -104.0),
    {"body_tilt": 64.0, "head_tilt": -10.0, "hat_tilt": -18.0, "coat_sway": -24.0, "mouth_open": 0.8,
     "lift": 18.0},
)
# Down: hunched forward over the blow, every limb flung up over him, the coat
# blown open and up.
_LAUNCH_DOWN = _merge(
    legs(70.0, 130.0, 20.0, 100.0), sword(-172.0, -186.0, -110.0), off(-178.0, -196.0),
    {"body_tilt": 26.0, "head_tilt": 14.0, "hat_tilt": -20.0, "coat_sway": 40.0, "mouth_open": 0.8,
     "lift": 10.0},
)
_row("launch_up", 6, 66, [
    K(0.0, _LAUNCH_UP, {"spin": 4.0}),
    K(0.4, _LAUNCH_UP, {"spin": -4.0, "left_thigh": 14.0, "right_thigh": 4.0}, ease="out"),
    K(1.0, _LAUNCH_UP, {"spin": -12.0, "left_thigh": 20.0, "left_shin": 40.0, "sword_upper": 24.0,
                        "off_upper": 22.0, "hat_tilt": -20.0}),
], place="air")
_row("launch_horizontal", 6, 66, [
    K(0.0, _LAUNCH_SIDE, {"body_tilt": 40.0, "spin": -6.0}),
    K(0.4, _LAUNCH_SIDE, {"spin": -10.0}, ease="out"),
    K(1.0, _LAUNCH_SIDE, {"spin": -18.0, "body_tilt": 56.0, "sword_upper": -76.0, "off_upper": -90.0}),
], place="air")
_row("launch_down", 6, 66, [
    K(0.0, _LAUNCH_DOWN, {"spin": -6.0}),
    K(0.4, _LAUNCH_DOWN, {"spin": 4.0}, ease="out"),
    K(1.0, _LAUNCH_DOWN, {"spin": 12.0, "coat_sway": 34.0, "left_shin": 120.0}),
], place="air")
# The plain launch (a sheet without a direction asks for it): flung up and
# back at once, spread like a star.
_row("launch", 6, 66, [
    K(0.0, legs(30.0, 50.0, -40.0, -30.0), sword(-130.0, -150.0, -90.0), off(110.0, 140.0),
      {"body_tilt": -20.0, "head_tilt": -14.0, "hat_tilt": -22.0, "coat_sway": 30.0, "mouth_open": 0.8,
       "spin": -10.0}),
    K(1.0, legs(40.0, 60.0, -50.0, -40.0), sword(-140.0, -160.0, -100.0), off(120.0, 150.0),
      {"body_tilt": -24.0, "head_tilt": -14.0, "hat_tilt": -26.0, "coat_sway": 36.0, "mouth_open": 0.8,
       "spin": -40.0}),
], place="air")
# The meteor: driven head first down at the deck, the legs flung up behind.
_row("meteor", 6, 66, [
    K(0.0, _LAUNCH_DOWN, {"spin": 60.0}),
    K(0.4, _LAUNCH_DOWN, legs(40.0, 70.0, 10.0, 40.0), {"spin": 110.0}, ease="out"),
    K(1.0, _LAUNCH_DOWN, legs(30.0, 50.0, 4.0, 30.0), {"spin": 140.0, "head_tilt": 6.0}),
], place="air")
_row("tumble", 8, 70, _tumble, place="air", loop=True)
# Knocked down: falling back, the back hitting the deck, the legs kicked up,
# then flat on his back.
_row("knockdown", 6, 76, [
    K(0.0, legs(30.0, 40.0, -40.0, -20.0), sword(60.0, 90.0, 160.0), off(100.0, 120.0),
      {"head_tilt": -10.0, "hat_tilt": -18.0, "coat_sway": 16.0, "mouth_open": 0.8, "lift": 24.0, "spin": -40.0}),
    K(0.35, FACE_UP, legs(-80.0, -60.0, -100.0, -40.0), {"mouth_open": 0.8, "hat_tilt": -20.0}, ease="in"),
    K(0.6, FACE_UP, legs(-30.0, -10.0, -70.0, 0.0), {"lift": 6.0, "mouth_open": 0.6}, ease="out"),
    K(1.0, FACE_UP),
], place="floor")
_row("prone_face_up", 6, 110, _breathe(FACE_UP, blink_at=3 / 6, chest=2.5), place="floor", loop=True)
_row("prone_face_down", 6, 110, _breathe(FACE_DOWN, blink_at=3 / 6, chest=2.0), place="floor", loop=True)
# The plain prone (a sheet without the two asks for it): curled on his side,
# the knees drawn up, an arm over his head.
_SIDE = _merge(
    TUCK, legs(-90.0, 0.0, -104.0, 10.0), sword(-150.0, -200.0, -170.0),
    {"head_tilt": 8.0, "hat_tilt": -10.0, "coat_sway": -14.0, "spin": -80.0},
)
_row("prone", 6, 110, _breathe(_SIDE, blink_at=0.5, chest=2.0), place="floor", loop=True)
_row("prone_damage", 4, 70, [
    K(0.0, FACE_UP, legs(-20.0, 20.0, -60.0, 10.0), {"lift": 10.0, "mouth_open": 0.8, "blink": True,
                                                          "head_tilt": -12.0}),
    K(0.5, FACE_UP, {"lift": 3.0, "mouth_open": 0.6}, ease="out"),
    K(1.0, FACE_UP),
], place="floor")
# Up from the back: sitting up, onto a knee with a hand on the deck, up.
_SIT = _merge(
    legs(-86.0, -90.0, -120.0, -50.0), sword(-60.0, -100.0, -30.0), off(30.0, 10.0),
    {"body_tilt": -28.0, "root_x": 0.0, "head_tilt": 4.0, "hat_tilt": -8.0, "coat_sway": -8.0},
)
_KNEEL = _merge(
    legs(-8.0, 92.0, -82.0, 4.0), sword(-60.0, -110.0, -40.0), off(-10.0, 0.0),
    {"body_tilt": 14.0, "head_tilt": -6.0, "hat_tilt": 4.0, "coat_sway": 10.0},
)
_row("getup", 7, 72, [
    K(0.0, FACE_UP),
    K(0.35, _SIT),
    K(0.65, _KNEEL),
    K(1.0, {}),
], place="floor")
_row("getup_roll", 7, 58, [
    K(0.0, FACE_UP),
    K(0.25, TUCK, {"spin": -110.0}),
    K(0.55, TUCK, {"spin": -250.0}, ease="lin"),
    K(0.8, CROUCH, {"spin": -360.0}),
    K(1.0, {"spin": -360.0}),
], place="floor")
_row("getup_attack", 7, 60, [
    K(0.0, FACE_UP),
    K(0.25, _SIT, off(40.0, 30.0), {"body_tilt": -16.0}),
    K(0.5, _KNEEL, sword(-58.0, -66.0, 14.0), {"body_tilt": 24.0, "mouth_open": 0.8}),
    K(0.72, _KNEEL, sword(56.0, 70.0, 172.0), {"body_tilt": 8.0, "mouth_open": 0.6}),
    K(1.0, {}),
], place="floor")
# The tech: caught it. Down on the back knee with the free hand flat on the
# deck, the cutlass up and ready, eyes on the foe, then up.
_TECH = _merge(
    legs(10.0, 96.0, -82.0, 8.0), sword(-120.0, -150.0, -70.0), off(-30.0, 6.0),
    {"body_tilt": 26.0, "head_tilt": -14.0, "hat_tilt": 2.0, "coat_sway": 20.0},
)
_row("tech", 5, 52, [
    K(0.0, _TECH, {"body_tilt": 30.0}),
    K(0.4, _TECH, ease="out"),
    K(1.0, {}),
], place="floor")
_row("tech_roll", 7, 54, [
    K(0.0, _TECH),
    K(0.3, TUCK, {"spin": 120.0}),
    K(0.6, TUCK, {"spin": 270.0}, ease="lin"),
    K(0.82, CROUCH, {"spin": 360.0}),
    K(1.0, {"spin": 360.0}),
], place="floor")

# 3. Defence.
_row("shield_raise", 3, 50, [K(0.0, {"body_tilt": 0.0}), K(1.0, BLOCK)])
_row("block", 6, 85, _breathe(BLOCK, chest=1.2), loop=True)
_row("shield_hit", 4, 55, [
    K(0.0, BLOCK, legs(36.0, 52.0, -26.0, -6.0), {"body_tilt": -12.0, "root_x": -4.0, "sword_upper": -116.0,
                                                   "head_tilt": 12.0, "mouth_open": 0.6, "coat_sway": 14.0}),
    K(0.4, BLOCK, legs(34.0, 48.0, -28.0, -8.0), {"body_tilt": -9.0, "root_x": -3.0, "mouth_open": 0.6}, ease="out"),
    K(1.0, BLOCK),
])
_row("shield_release", 3, 50, [K(0.0, BLOCK), K(1.0, {})])
# The parry: the blow caught clean and flicked off, the blade snapped out and
# up, chin up.
_row("parry", 5, 55, [
    K(0.0, BLOCK),
    K(0.3, legs(26.0, 34.0, -34.0, -14.0), sword(-110.0, -120.0, -40.0), off(40.0, 10.0),
      {"body_tilt": -6.0, "head_tilt": -12.0, "hat_tilt": -4.0, "coat_sway": -8.0}, ease="out"),
    K(0.65, sword(-60.0, -90.0, -70.0), {"body_tilt": -3.0, "head_tilt": -12.0, "hat_tilt": -4.0}),
    K(1.0, {}),
])
_row("roll", 7, 56, [
    K(0.0, CROUCH),
    K(0.2, TUCK, {"spin": 60.0}),
    K(0.5, TUCK, {"spin": 200.0}, ease="lin"),
    K(0.78, TUCK, {"spin": 330.0}, ease="lin"),
    K(1.0, CROUCH, legs(30.0, 66.0, -60.0, 14.0), {"spin": 360.0, "body_tilt": 16.0, "coat_sway": 10.0}),
], place="floor")
_row("roll_back", 7, 56, [
    K(0.0, CROUCH),
    K(0.2, TUCK, {"spin": -60.0}),
    K(0.5, TUCK, {"spin": -200.0}, ease="lin"),
    K(0.78, TUCK, {"spin": -330.0}, ease="lin"),
    K(1.0, CROUCH, legs(30.0, 66.0, -60.0, 14.0), {"spin": -360.0, "body_tilt": 16.0, "coat_sway": 10.0}),
], place="floor")
# The spot dodge: a twist out of the way where he stands, ducked and drawn in,
# the cutlass flat up his front.
_row("spot_dodge", 6, 50, [
    K(0.0, {"body_tilt": 5.0, "root_x": 1.0, "coat_sway": 4.0}),
    K(0.3, legs(40.0, 90.0, -4.0, 40.0), sword(-120.0, -10.0, -92.0), off(-40.0, -150.0),
      {"body_tilt": -22.0, "root_x": -5.0, "head_tilt": 12.0, "hat_tilt": 10.0, "coat_sway": -16.0,
       "blink": True}, ease="out"),
    K(0.7, legs(38.0, 84.0, -6.0, 36.0), sword(-118.0, -12.0, -90.0), off(-42.0, -148.0),
      {"body_tilt": -20.0, "root_x": -4.0, "head_tilt": 12.0, "hat_tilt": 8.0, "coat_sway": -12.0, "blink": True}),
    K(1.0, {}),
])
_row("air_dodge", 6, 55, [
    K(0.0, DROP),
    K(0.3, TUCK, sword(-130.0, -200.0, -150.0), off(-120.0, -200.0), {"spin": -20.0, "blink": True}, ease="out"),
    K(0.7, TUCK, sword(-126.0, -196.0, -146.0), off(-118.0, -196.0), {"spin": -28.0, "blink": True}),
    K(1.0, DROP, {"coat_sway": 34.0, "spin": -4.0}),
], place="air")

# 4. Ledge, and the grab.
_row("ledge_catch", 4, 62, [
    K(0.0, HANG, legs(-40.0, -20.0, -60.0, -36.0), off(-170.0, -176.0),
      {"spin": -14.0, "pivot": 250.0, "coat_sway": 20.0, "mouth_open": 0.6}),
    K(0.5, HANG, legs(-10.0, 10.0, -26.0, -8.0), {"spin": 6.0, "pivot": 250.0}, ease="out"),
    K(1.0, _hang(0.0)),
], place="air")
_row("ledge_grab", 6, 100, _hang, place="air", loop=True)
_row("ledge_climb", 6, 92, [
    K(0.0, _hang(0.0)),
    K(0.35, off(-150.0, -30.0), legs(10.0, 20.0, -110.0, -20.0), sword(-10.0, -60.0, -40.0),
      {"body_tilt": 10.0, "head_tilt": -8.0, "mouth_open": 0.6}),
    K(0.7, _KNEEL),
    K(1.0, {}),
], place="floor")
_row("ledge_getup", 6, 80, [
    K(0.0, _hang(0.0)),
    K(0.4, off(-60.0, -20.0), legs(40.0, 80.0, -96.0, -10.0), sword(-110.0, -140.0, -60.0),
      {"body_tilt": 18.0, "head_tilt": -12.0, "coat_sway": 20.0, "mouth_open": 0.3}, ease="out"),
    K(1.0, {}),
], place="floor")
_row("ledge_roll", 7, 50, [
    K(0.0, _hang(0.0)),
    K(0.25, TUCK, {"spin": 80.0}),
    K(0.55, TUCK, {"spin": 230.0}, ease="lin"),
    K(0.8, CROUCH, {"spin": 360.0}),
    K(1.0, {"spin": 360.0}),
], place="floor")
_row("ledge_jump", 6, 66, [
    K(0.0, _hang(0.0)),
    K(0.4, legs(-20.0, 20.0, -90.0, -20.0), sword(-160.0, -176.0, -80.0), off(-170.0, -186.0),
      {"body_tilt": -6.0, "head_tilt": -14.0, "coat_sway": 14.0, "mouth_open": 0.8}, ease="out"),
    K(1.0, RISE),
], place="air")
_row("ledge_attack", 7, 62, [
    K(0.0, _hang(0.0)),
    K(0.3, _KNEEL, sword(-150.0, -170.0, -120.0), {"mouth_open": 0.6}),
    K(0.55, _KNEEL, sword(-58.0, -66.0, 14.0), {"body_tilt": 26.0, "mouth_open": 0.8}, ease="out"),
    K(0.75, _KNEEL, sword(-40.0, -40.0, 40.0), {"body_tilt": 22.0}),
    K(1.0, {}),
], place="floor")
_row("ledge_drop", 4, 60, [
    K(0.0, _hang(0.0)),
    K(0.5, HANG, off(-150.0, -170.0), {"body_tilt": 0.0, "head_tilt": -10.0}),
    K(1.0, DROP),
], place="air")
_row("grab_hold", 6, 90, _grab_hold, loop=True)
_row("grab_release", 4, 60, [
    K(0.0, HOLD),
    K(0.4, legs(36.0, 52.0, -18.0, -2.0), sword(-60.0, -120.0, -60.0), off(60.0, 40.0),
      {"body_tilt": -10.0, "root_x": -4.0, "head_tilt": -6.0, "coat_sway": 12.0, "mouth_open": 0.6}, ease="out"),
    K(1.0, {}),
])
_row("grabbed", 6, 88, _grabbed, loop=True)
_row("grabbed_pummel", 4, 60, [
    K(0.0, HELD, {"head_tilt": -14.0, "body_tilt": -18.0, "hat_tilt": -20.0, "mouth_open": 0.8, "blink": True}),
    K(0.5, HELD, {"head_tilt": -8.0, "body_tilt": -15.0, "hat_tilt": -14.0, "mouth_open": 0.8}, ease="out"),
    K(1.0, _grabbed(0.0)),
])
_row("grab_escape", 5, 64, [
    K(0.0, HELD),
    K(0.35, legs(40.0, 60.0, -10.0, 10.0), sword(-110.0, -160.0, -80.0), off(-110.0, -80.0),
      {"body_tilt": -8.0, "root_x": -5.0, "head_tilt": 6.0, "hat_tilt": -8.0, "coat_sway": 16.0,
       "mouth_open": 0.6}, ease="out"),
    K(0.7, legs(28.0, 40.0, -26.0, -8.0), {"body_tilt": -2.0, "root_x": -3.0}),
    K(1.0, {}),
])

# 5. The rest of the fighter's states the game asks for.
_row("dizzy", 8, 96, _dizzy, loop=True)
# Helpless after his up special: limp, the arms trailing up, the head down.
_row("fall_special", 6, 92, _hover(_merge(
    legs(10.0, 30.0, -10.0, 10.0), sword(-160.0, -150.0, -120.0), off(-170.0, -160.0),
    {"body_tilt": 8.0, "head_tilt": 14.0, "hat_tilt": -10.0, "coat_sway": 30.0, "mouth_open": 0.3},
), coat=10.0, hat=4.0, limb=6.0), place="air", loop=True)


#: Each category of ``data/fighter_motion_vocabulary.yaml`` that applies to
#: him (scope ``fighter_core``), and the row of his sheet that draws it.
#: Several categories share a row where he has no move of that kind.
FIGHTER_MOTION_COVERAGE: Final[Dict[str, str]] = {
    "idle": "idle", "idle_look_up": "idle_look_up", "walk": "walk", "locomotion_stop": "walk_stop",
    "turnaround": "turnaround", "dash_startup": "dash_startup", "run": "run", "stumble": "teeter_start",
    "crouch_start": "crouch_start", "crouch": "crouch", "crouch_walk": "crouch_walk", "crouch_jump": "jump",
    "crouch_end": "crouch_end", "land_light": "land_recovery", "land_hard": "land_hard",
    "jump_squat": "jump_squat", "jump": "jump", "double_jump": "double_jump", "fall": "fall",
    "fall_special": "fall_special", "land_special": "land_hard", "tumble": "tumble",
    "shield_raise": "shield_raise", "shield_hold": "block", "shield_release": "shield_release",
    "parry": "parry", "shield_hit": "shield_hit", "spot_dodge": "spot_dodge", "roll_forward": "roll",
    "roll_backward": "roll_back", "air_dodge": "air_dodge",
    "jab": "jab", "dash_attack": "dash_attack", "attack_side": "attack_side", "attack_up": "attack_up",
    "attack_down": "attack_down", "smash_charge_forward": "smash_charge", "smash_forward": "smash_forward",
    "smash_charge_up": "smash_charge", "smash_up": "smash_up", "smash_charge_down": "smash_charge",
    "smash_down": "smash_down", "air_neutral": "air_neutral", "air_forward": "air_forward",
    "air_back": "air_back", "air_up": "air_up", "air_down": "air_down", "air_land": "land_recovery",
    "special_neutral": "special", "special_side": "special", "special_up": "special_up",
    "special_down": "special_down", "final_smash": "special",
    "grab": "grab", "grab_hold": "grab_hold", "pummel": "pummel", "grab_release": "grab_release",
    "throw_forward": "throw_forward", "throw_back": "throw_back", "throw_up": "throw_up",
    "throw_down": "throw_down", "grabbed": "grabbed", "grabbed_pummel": "grabbed_pummel",
    "grab_escape": "grab_escape",
    "hit": "hit", "launch": "launch", "meteor": "meteor", "impact": "hit_high", "splat": "prone_face_down",
    "ground_bounce": "knockdown", "prone": "prone", "prone_damage": "prone_damage", "getup": "getup",
    "getup_attack": "getup_attack", "getup_roll": "getup_roll", "knockdown": "knockdown", "tech": "tech",
    "tech_roll": "tech_roll", "wall_tech": "tech", "wall_tech_jump": "double_jump", "ceiling_tech": "tech",
    "shield_break_launch": "launch_up", "shield_break_fall": "fall_special",
    "shield_break_collapse": "knockdown", "shield_break_recover": "dizzy", "dizzy": "dizzy",
    "sleep_start": "knockdown", "sleep": "prone_face_up", "wake": "getup", "bury_start": "hit_low",
    "buried": "crouch", "bury_escape": "jump_squat", "footstool_jump": "double_jump",
    "footstooled": "meteor", "platform_drop": "ledge_drop", "teeter_start": "teeter_start",
    "teeter": "teeter", "lose_footing": "teeter_start",
    "ledge_catch": "ledge_catch", "ledge_hang": "ledge_grab", "ledge_getup": "ledge_getup",
    "ledge_attack": "ledge_attack", "ledge_roll": "ledge_roll", "ledge_jump": "ledge_jump",
    "ledge_drop": "ledge_drop", "trip_fall": "knockdown", "trip_land": "knockdown",
    "trip_idle": "prone_face_down", "trip_getup": "getup", "trip_attack": "getup_attack",
    "trip_roll": "getup_roll", "taunt": "taunt", "entrance": "taunt", "victory": "taunt",
    "victory_hold": "taunt", "loss": "hurt",
}

APPLICABLE_MOTION_SCOPES: Final = ("fighter_core",)

#: (row, frames, ms a frame), in the order the sheet publishes them.
ROWS: Final[List[Tuple[str, int, int]]] = [(name, row.frames, row.ms) for name, row in ROWS_SPEC.items()]

#: Rows that repeat while their state holds.
LOOPS: Final[frozenset] = frozenset(name for name, row in ROWS_SPEC.items() if row.loop)


# ── sampling and placement ───────────────────────────────────────────────────

def _sample(keys: Tuple[Key, ...], u: float, home: Channels) -> Channels:
    base = {**home, "spin": 0.0, "pivot": 110.0, "lift": 0.0}
    full = [(t, ease, {**base, **k}) for t, ease, k in keys]
    if u <= full[0][0]:
        return dict(full[0][2])
    for (t0, _e0, k0), (t1, e1, k1) in zip(full, full[1:]):
        if u <= t1:
            w = _EASES[e1]((u - t0) / (t1 - t0)) if t1 > t0 else 1.0
            out: Channels = {}
            for name, a in k0.items():
                b = k1.get(name, a)
                if isinstance(a, bool) or isinstance(b, bool):
                    out[name] = a if w < 0.5 else b
                else:
                    out[name] = a + (b - a) * w
            return out
    return dict(full[-1][2])


#: The hip over the root, in paint px (``_pirate_rig``: the ``hip`` bone).
_HIP = 84.0


def _hinged(pose: Channels, home_tilt: float) -> Channels:
    """``pose`` with its body tilt turned about the hip, not the root: the rig
    turns the trunk about the root on the ground, so a lean moved the hips
    (and the legs under them) with it, a plank tipping over. Here the hips
    stay over the legs and the trunk bends at them."""
    dx = _HIP * (math.sin(math.radians(pose["body_tilt"])) - math.sin(math.radians(home_tilt)))
    pose["root_x"] -= dx / SCALE
    return pose


def _turned(pose: Channels, deg: float, pivot: float) -> Channels:
    """``pose`` turned ``deg`` (clockwise) about the point ``pivot`` paint px
    over its root: the root moves round the pivot, every limb turns with it."""
    if not deg:
        return pose
    r = math.radians(deg)
    px, py = 0.0, -pivot
    rx, ry = px * math.cos(r) - py * math.sin(r), px * math.sin(r) + py * math.cos(r)
    pose["root_x"] += (px - rx) / SCALE
    pose["bob"] += (py - ry) / SCALE
    # Kept in (-180, 180]: a boot half off the deck is turned by a fraction
    # of its shin's angle, so 384 is not 24 there.
    pose["body_tilt"] = _wrap(pose["body_tilt"] + deg)
    for name in _LIMBS:
        pose[name] = _wrap(pose[name] + deg)
    return pose


def _wrap(deg: float) -> float:
    return deg - 360.0 * math.ceil((deg - 180.0) / 360.0)


# The outlines of the parts a body can rest on, in each part's own frame, and
# the half width of the ink on them (``_pirate_common`` draws these shapes).
_B = 1.05
_TORSO = [(-42 * _B, -14), (-30 * _B, -29), (28 * _B, -29), (40 * _B, -14), (37 * _B, 34), (42 * _B, 68),
          (0, 76), (-44 * _B, 68), (-39 * _B, 34), (48 * _B, -11), (-48 * _B, -11)]
_TAIL_L = [(-44 * _B, -14), (-9, -14), (-11, 26), (-38 * _B, 34)]
_TAIL_R = [(9, -14), (42 * _B, -14), (38 * _B, 34), (10, 26)]
_SEAT = [(-29 * _B, -20), (29 * _B, -20), (29 * _B, 8), (0, 16), (-29 * _B, 8)]
_HEAD = [(-25, -8), (-23, -23), (-11, -32), (7, -33), (21, -25), (27, -9), (26, 8), (20, 23), (8, 32),
         (-7, 30), (-20, 18), (-29, -6), (-29, 8)]
_BRIM = [(-52, -18), (-36, -40), (-12, -56), (14, -56), (38, -42), (54, -20), (30, -25), (0, -29), (-28, -24)]
_BOOT = [(-14, -29), (12, -29), (13, -19), (-14, -19), (-12, -8), (11, -10), (24, -4), (27, 6), (-12, 6)]
_SOLE = [(-13, 3.5), (28, 3.5), (28, 7.5), (-13, 7.5)]
_BLADE = [(8.0, -3.5), (8.0, 6.5), (46.0, -4.8), (46.0, 9.4), (78.0, -5.0), (78.0, 11.0), (92.0, 5.0),
          (5.0, -10.0), (5.0, 10.0), (-11.0, 12.0)]

_W, _H = BASE_FRAME[0] * SCALE, BASE_FRAME[1] * SCALE


def _lowest(pose: Channels) -> float:
    """The lowest paint of ``pose`` (paint px, +y down), from the shapes of
    the parts the paint pass draws."""
    tilt = pose["body_tilt"]
    j = rig.evaluate(pose, KIND, _W, _H, tilt)
    ground = rig.ground_y(_H)
    low = -1e9

    def shape(points, origin, deg, ink):
        nonlocal low
        for p in points:
            low = max(low, transform(p, origin, deg)[1] + ink)

    shape(_TORSO, j["chest"].point, tilt, 2.5)
    shape(_TAIL_L, j["hip"].point, tilt + pose["coat_sway"], 2.0)
    shape(_TAIL_R, j["hip"].point, tilt - pose["coat_sway"], 2.0)
    shape(_SEAT, j["hip"].point, tilt, 2.0)
    face = j["head"].angle
    shape(_HEAD, j["head"].point, face, 1.5)
    shape(_BRIM, j["head"].point, face + pose["hat_tilt"], 2.0)
    for name, r in (("left_hip", 16.7), ("right_hip", 16.7), ("left_knee", 14.6), ("right_knee", 14.6),
                    ("back_shoulder", 13.5), ("front_shoulder", 14.6), ("back_elbow", 12.0),
                    ("front_elbow", 12.5), ("back_hand", 9.0), ("front_hand", 10.0)):
        low = max(low, j[name].point[1] + r)
    for side in ("left", "right"):
        foot = j[f"{side}_foot"].point
        lifted = max(0.0, min(1.0, (ground - foot[1] - 4.0) / 12.0))
        deg = pose[f"{side}_shin"] * max(lifted, pose["death_t"])
        shape(_BOOT, foot, deg, 1.5)
        shape(_SOLE, foot, deg, 0.0)
    shape(_BLADE, j["front_hand"].point, pose["weapon"], 1.5)
    return low


_FLOOR: List[float] = []


def floor_line() -> float:
    """The floor line: the lowest paint of the planted guard (the soles)."""
    if not _FLOOR:
        from . import _pirate_common as pc

        _FLOOR.append(_lowest(pc.planted(pc.home_pose())))
    return _FLOOR[0]


def _floored(pose: Channels, lift: float) -> Channels:
    """``pose`` moved up or down until its lowest paint is ``lift`` over the
    floor line. Twice: a boot turns with its shin once it is off the deck."""
    for _ in range(3):
        pose["bob"] += (floor_line() - lift - _lowest(pose)) / SCALE
    return pose


def _stand_on(pose: Channels, side: str) -> Channels:
    """The shin of ``side`` turned so its foot is on the ground, the turn
    nearest the authored one; left as it is if the foot cannot reach."""
    tilt = pose["body_tilt"]
    j = rig.evaluate(pose, KIND, _W, _H, tilt)
    knee = j[f"{side}_knee"].point
    c = (rig.ground_y(_H) - knee[1]) / rig.SHIN
    if not -1.0 <= c <= 1.0:
        return pose
    a = math.degrees(math.acos(c))
    shin = pose[f"{side}_shin"]
    pose[f"{side}_shin"] = min((a, -a), key=lambda v: abs(v - shin))
    return pose


def pose(anim: str, frame_idx: int, nframes: int) -> Channels:
    """The pose of one frame of a row of this module."""
    from . import _pirate_common as pc

    row = ROWS_SPEC[anim]
    n = max(1, nframes)
    home = pc.home_pose()
    if row.loop:
        u = frame_idx / n
    else:
        u = frame_idx / max(1, n - 1)
    if callable(row.keys):
        out = {**home, **row.keys(u)}
    else:
        out = _sample(row.keys, u, home)
    spin = out.pop("spin", 0.0)
    pivot = out.pop("pivot", 110.0)
    lift = out.pop("lift", 0.0)
    out = _hinged(out, home["body_tilt"])
    out = _turned(out, spin, pivot)
    out["blink"] = bool(out.get("blink", False))
    out["mouth_open"] = min(_MOUTHS, key=lambda m: abs(m - out["mouth_open"]))
    if row.place == "plant":
        out = pc.planted(out)
        for side in row.feet:
            out = _stand_on(out, side)
    elif row.place == "air":
        # Off the deck, but never through it: at least ``lift`` over it.
        if _lowest(out) > floor_line() - lift:
            out = _floored(out, lift)
    elif row.place == "floor":
        out = _floored(out, lift)
        if row.feet:
            for side in row.feet:
                out = _stand_on(out, side)
            out = _floored(out, lift)
    return out


__all__ = ["APPLICABLE_MOTION_SCOPES", "FIGHTER_MOTION_COVERAGE", "LOOPS", "ROWS", "ROWS_SPEC", "floor_line",
           "pose"]
