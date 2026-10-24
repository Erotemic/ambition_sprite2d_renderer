"""Faces: a parameterized expression, emotion presets, visemes, composition.

An :class:`Expression` is a handful of numbers about the face's parts (the
brows, the lids, the gaze, the mouth), not a picture. A face is drawn from
one, on any species' head and in every view, by ``draw`` (through the head's
face layout). Presets:

* :data:`EMOTIONS`: neutral, happy, angry, afraid, sad, surprised, smug,
  pained, determined;
* :data:`LOOKS`: the neutral face looking left, right, up and down;
* :data:`VISEMES`: mouth shapes for talk (rest, a, e, o, m).

:func:`blend` mixes two expressions; :func:`compose` adds an expression's
change from neutral onto another (an afraid face that is also looking left),
and :func:`with_viseme` puts a talking mouth on any emotion, keeping its
corners. A clip asks for a face per frame with :func:`face_channels`.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from typing import Dict, Optional, Sequence, Tuple


@dataclass(frozen=True)
class Expression:
    #: The whole brow up (+) or down (-), in brow heights.
    brow_raise: float = 0.0
    #: The inner ends up (+, worry) or down and in (-, anger).
    brow_inner: float = 0.0
    brow_outer: float = 0.0
    #: The upper lid lowered over the eye, 0 open .. 1 shut; below 0 widens.
    lid: float = 0.0
    #: The lower lid raised (a squint, a smile's eyes), 0 .. 1.
    squint: float = 0.0
    #: Where the eyes look: (toward the character's left, up), -1 .. 1.
    gaze: Tuple[float, float] = (0.0, 0.0)
    #: The pupil's size.
    pupil: float = 1.0
    #: The mouth's corners up (+) or down (-).
    smile: float = 0.0
    #: The jaw open, 0 .. 1.
    open: float = 0.0
    #: The mouth wider (+) or narrower (-), as a fraction of its width.
    wide: float = 0.0
    #: The lips pushed round (an o, a pucker), 0 .. 1.
    round: float = 0.0
    #: One corner (the character's left) up more than the other.
    skew: float = 0.0
    #: Teeth showing, 0 .. 1.
    teeth: float = 0.0


NEUTRAL = Expression()

EMOTIONS: Dict[str, Expression] = {
    "neutral": NEUTRAL,
    "happy": Expression(brow_raise=0.35, brow_inner=0.1, squint=0.45, smile=1.0, open=0.18, wide=0.15, teeth=0.6),
    "angry": Expression(brow_raise=-0.5, brow_inner=-1.0, brow_outer=0.25, lid=0.2, squint=0.35, smile=-0.6, wide=0.05, teeth=0.4,
                        open=0.08),
    "afraid": Expression(brow_raise=0.7, brow_inner=0.9, lid=-0.35, pupil=0.7, smile=-0.45, open=0.35, wide=0.2, gaze=(0.35, 0.0)),
    "sad": Expression(brow_raise=0.1, brow_inner=0.85, brow_outer=-0.4, lid=0.35, smile=-0.8, gaze=(0.0, -0.45)),
    "surprised": Expression(brow_raise=1.0, brow_inner=0.3, lid=-0.45, pupil=0.85, open=0.75, round=0.55),
    "smug": Expression(brow_raise=0.15, brow_inner=-0.2, brow_outer=0.35, lid=0.45, smile=0.45, skew=0.55, gaze=(-0.25, 0.0)),
    "pained": Expression(brow_raise=-0.2, brow_inner=0.8, lid=0.35, squint=0.8, smile=-0.7, open=0.3, wide=0.35, teeth=0.8),
    "determined": Expression(brow_raise=-0.35, brow_inner=-0.55, lid=0.15, squint=0.2, smile=-0.15, wide=-0.1),
}
LOOKS: Dict[str, Expression] = {
    "look_left": Expression(gaze=(1.0, 0.0)),
    "look_right": Expression(gaze=(-1.0, 0.0)),
    "look_up": Expression(gaze=(0.0, 1.0), brow_raise=0.25),
    "look_down": Expression(gaze=(0.0, -1.0), lid=0.3),
}
#: Mouth shapes for talk: how far the jaw drops, how wide and how round.
VISEMES: Dict[str, Tuple[float, float, float, float]] = {
    # name: (open, wide, round, teeth)
    "rest": (0.0, 0.0, 0.0, 0.0),
    "a": (0.75, 0.1, 0.0, 0.3),
    "e": (0.35, 0.3, 0.0, 0.7),
    "o": (0.55, -0.25, 0.85, 0.0),
    "m": (0.0, -0.05, 0.0, 0.0),
}
#: Every face a generated head is drawn with: the emotions, then the looks.
FACES: Dict[str, Expression] = {**EMOTIONS, **LOOKS}
#: The faces that carry a full set of talking mouths.
TALKING = tuple(EMOTIONS)


def _num(e: Expression):
    for f in fields(Expression):
        v = getattr(e, f.name)
        yield f.name, v


def blend(a: Expression, b: Expression, t: float) -> Expression:
    """``t`` of the way from ``a`` to ``b``."""
    kw = {}
    for name, va in _num(a):
        vb = getattr(b, name)
        if isinstance(va, tuple):
            kw[name] = tuple(x + (y - x) * t for x, y in zip(va, vb))
        else:
            kw[name] = va + (vb - va) * t
    return Expression(**kw)


def compose(base: Expression, *layers: Expression, weights: Optional[Sequence[float]] = None) -> Expression:
    """``base`` with each layer's change from neutral added (weighted), and
    the result kept in range: an afraid face looking left, a happy face
    surprised."""
    weights = list(weights or [1.0] * len(layers))
    kw = {}
    for name, v in _num(base):
        if isinstance(v, tuple):
            acc = list(v)
            for layer, w in zip(layers, weights):
                d = getattr(layer, name)
                n = getattr(NEUTRAL, name)
                acc = [a + w * (x - y) for a, x, y in zip(acc, d, n)]
            kw[name] = tuple(max(-1.0, min(1.0, a)) for a in acc)
        else:
            acc = v
            for layer, w in zip(layers, weights):
                acc += w * (getattr(layer, name) - getattr(NEUTRAL, name))
            kw[name] = acc
    out = Expression(**kw)
    return clamp(out)


_RANGES = {"brow_raise": (-1.0, 1.2), "brow_inner": (-1.2, 1.2), "brow_outer": (-1.0, 1.0), "lid": (-0.6, 1.0), "squint": (0.0, 1.0),
           "pupil": (0.5, 1.4), "smile": (-1.2, 1.2), "open": (0.0, 1.0), "wide": (-0.4, 0.5), "round": (0.0, 1.0), "skew": (-1.0, 1.0),
           "teeth": (0.0, 1.0)}


def clamp(e: Expression) -> Expression:
    kw = {}
    for name, v in _num(e):
        if name in _RANGES:
            lo, hi = _RANGES[name]
            v = max(lo, min(hi, v))
        kw[name] = v
    return Expression(**kw)


def with_viseme(e: Expression, viseme: str) -> Expression:
    """The mouth of ``viseme`` on the face ``e``: the jaw and the lips' shape
    from the viseme, the corners (smile, skew) and the eyes from ``e``."""
    if viseme == "rest":
        return e
    o, w, r, t = VISEMES[viseme]
    return replace(e, open=max(o, e.open * 0.3), wide=e.wide * 0.4 + w, round=r, teeth=max(t, e.teeth * 0.5))


# ---- the rig's face channels ------------------------------------------------------------


def eyes_part(face: str) -> str:
    return f"face_eyes__{face}"


def brows_part(face: str) -> str:
    return f"face_brows__{face}"


def mouth_part(face: str, viseme: str = "rest") -> str:
    return f"face_mouth__{face}__{viseme}"


def mouth_face(face: str) -> str:
    """The face whose mouths a face uses: a look talks with the neutral mouth."""
    return face if face in TALKING else "neutral"


def face_channels(face: str = "neutral", viseme: str = "rest", *, blink: float = 0.0) -> Dict[str, float]:
    """The opacity channels that show ``face`` with the mouth ``viseme``:
    the neutral face is shown by default, so only what differs is named."""
    if face not in FACES:
        raise KeyError(f"unknown face {face!r}; one of {sorted(FACES)}")
    if viseme not in VISEMES:
        raise KeyError(f"unknown viseme {viseme!r}; one of {sorted(VISEMES)}")
    out: Dict[str, float] = {}
    if face != "neutral":
        out[eyes_part("neutral") + "_vis"] = 0.0
        out[brows_part("neutral") + "_vis"] = 0.0
        out[eyes_part(face) + "_vis"] = 1.0
        out[brows_part(face) + "_vis"] = 1.0
    mf = mouth_face(face)
    if (mf, viseme) != ("neutral", "rest"):
        out[mouth_part("neutral") + "_vis"] = 0.0
        out[mouth_part(mf, viseme) + "_vis"] = 1.0
    if blink:
        out["face_blink_vis"] = blink
    return out


def all_face_channel_names() -> Tuple[str, ...]:
    names = [eyes_part(f) + "_vis" for f in FACES] + [brows_part(f) + "_vis" for f in FACES]
    names += [mouth_part(f, v) + "_vis" for f in TALKING for v in VISEMES]
    return tuple(names) + ("face_blink_vis",)


__all__ = [
    "EMOTIONS", "Expression", "FACES", "LOOKS", "NEUTRAL", "TALKING", "VISEMES", "blend", "brows_part", "clamp", "compose", "eyes_part",
    "face_channels", "mouth_face", "mouth_part", "with_viseme",
]
