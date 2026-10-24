"""Heads: the human head and anthropomorphic animal heads on the same body.

Jon, 2026-10-23: "characters can have different species heads for a bojack
horseman style flavor to the world ... A horse head seems like a good first
test", and: "every humanoid head needs the fresh anthropomorphic design."
Every head here is drawn fresh, from the same primitives as the rest of the
generator (a loft of rings, relief bumps, 3D points); none reuses, traces or
adapts an existing animal's art (the companion dog, the gnu, the birds).

A head is a :class:`HeadModel`: its loft (with the face's relief), its skull
(the loft without relief: what hair and hats sit on), and a face *layout*:
where the eyes, brows, nose and mouth are, as angles round the head and
fractions of its height. The expression system (``face``) draws on any
layout, so every species has the same brows, lids, gaze and visemes.

Fractions ``f`` run from the crown (0) to the chin (1); angles ``alpha`` from
the front (0) toward the character's left (+90).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .geometry import Loft, RingKey, gauss, smoothstep, wrap180

SPECIES = ("human", "horse", "dog", "cat", "bird", "sea_lion")
#: A species' head height against a human's of the same build.
HEAD_SCALE = {"human": 1.0, "horse": 1.16, "dog": 1.05, "cat": 0.98, "bird": 1.0, "sea_lion": 1.02}
#: Coats: fur and feathers, by species.
COATS: Dict[str, Tuple[str, ...]] = {
    "horse": ("#7a4a2c", "#5c3a24", "#a8672f", "#2e2622", "#8d8a86", "#c9a26a", "#e6dfd2", "#4a3528"),
    "dog": ("#c08a4e", "#8a5a34", "#e4cfa6", "#3a3230", "#a9a39b", "#d7a45c", "#6e4a33", "#f0e8da"),
    "cat": ("#d68c4a", "#8b8580", "#3a3436", "#e8dcc8", "#b97a46", "#c9b9a4", "#5e5550", "#f2ece2"),
    "bird": ("#3f6f9e", "#c9473a", "#e3c24a", "#5b8f4f", "#ece6da", "#2e2c34", "#8a6a9e", "#d98a3e"),
    "sea_lion": ("#c9a876", "#b8946a", "#d4b384", "#a9804f", "#4e3628", "#5c4232", "#3e3029", "#6b4a32"),
}
#: Coats where the sexes differ: a sea lion cow is blonde to tan, a bull dark brown.
COATS_BY_SEX: Dict[str, Dict[str, Tuple[str, ...]]] = {
    "sea_lion": {"female": ("#c9a876", "#b8946a", "#d4b384", "#a9804f", "#c2a27a", "#9a7a56"),
                 "male": ("#4e3628", "#5c4232", "#3e3029", "#6b4a32", "#584538", "#47382f")},
}


@dataclass
class HeadModel:
    species: str
    keys: List[RingKey]
    bumps: list
    #: Where the face's parts sit (see the module doc).
    layout: Dict[str, float] = field(default_factory=dict)
    #: The ear: ``human``, ``horse``, ``dog_floppy``, ``dog_pointed``, ``cat``,
    #: ``flap`` (a small rolled ear flap), ``none``.
    ears: str = "human"
    #: What the head's hair is: ``human`` (the spec's style), ``mane``,
    #: ``tuft``, ``crest``, ``none`` (a sleek coat).
    hair: str = "human"
    #: Below this ``f`` and in front, the muzzle (a second colour), or None.
    muzzle_f: float = 0.0
    #: Where the neck enters the head (a fraction ``f``): the neck's top ring
    #: is fitted inside the head's ring there, and the head turns about its
    #: centre. ``None``: the human neck, which meets the head under the jaw.
    neck_f: float | None = None


def _rows(fy, hh: float, rows) -> List[RingKey]:
    return [RingKey(fy(f), rx * hh, rzf * hh, rzb * hh, 0.0, cz * hh, sq) for f, rx, rzf, rzb, cz, sq in rows]


# ---- human ---------------------------------------------------------------------------------


def _human(fig) -> HeadModel:
    s = fig.spec
    hh = fig.hh
    jaw = s.face.jaw
    jw = s.face.jaw_width
    rows = [
        (0.00, 0.0, 0.0, 0.0, -0.04),
        (0.13, 0.355, 0.38, 0.44, -0.04),
        (0.24, 0.395, 0.425, 0.48, -0.035),
        (0.38, 0.405, 0.44, 0.47, -0.02),
        (0.50, 0.395, 0.43, 0.42, 0.0),
        (0.62, 0.375, 0.415, 0.33, 0.0),
        (0.74, 0.35, 0.39, 0.3, 0.01),
        (0.86, 0.3, 0.36, 0.27, 0.02),
        (0.95, 0.22, 0.32, 0.25, 0.03),
        (1.00, 0.1, 0.28, 0.22, 0.04),
    ]
    out = []
    for f, rx, rzf, rzb, cz in rows:
        if f >= 0.6:
            t = smoothstep(0.6, 0.86, f)
            if jaw == "square":
                rx += {0.62: 0.0, 0.74: 0.01, 0.86: 0.03, 0.95: 0.05, 1.0: 0.06}.get(f, 0.0)
            elif jaw == "pointed":
                rx -= {0.74: 0.02, 0.86: 0.05, 0.95: 0.06, 1.0: 0.05}.get(f, 0.0)
            elif jaw == "wide":
                rx += 0.03 * t
            rx *= 1.0 + (jw - 1.0) * (0.4 + 0.6 * t)
        if jaw == "long":
            rx *= 0.95
        if not fig.female and 0.3 < f < 0.95:
            rx *= 1.02
        out.append((f, rx, rzf, rzb, cz, 2.0))
    nose = s.face.nose
    layout = {
        "eye_f": 0.475, "brow_f": 0.395, "eye_alpha": 23.5 * s.face.eye_spacing, "eye_w": 0.142 * s.face.eye_size, "iris": 0.56,
        "nose_tip_f": {"long": 0.655, "button": 0.6, "upturned": 0.605}.get(nose, 0.63), "mouth_f": 0.77,
        "mouth_alpha": 16.5 * s.face.mouth_width * (0.95 if fig.female else 1.0), "nose": "human", "pupil": "round",
    }
    model = HeadModel("human", _rows(fig.fy, hh, out), [], layout)
    model.bumps = _human_bumps(fig, layout)
    return model


def _human_bumps(fig, a: Dict[str, float]) -> list:
    """The face's relief, as radial bumps: brow, nose, lips, chin, cheeks."""
    s = fig.spec
    hh = fig.hh
    male = not fig.female
    nose = s.face.nose
    size = s.face.nose_size
    tip_f = a["nose_tip_f"]
    base_f = tip_f + 0.045
    bridge_f = a["brow_f"] + 0.035
    length = {"straight": 0.105, "button": 0.08, "long": 0.13, "hooked": 0.12, "broad": 0.1, "upturned": 0.09}[nose] * size
    curve = {"straight": 0.0, "button": -0.5, "long": 0.1, "hooked": 1.0, "broad": 0.0, "upturned": -0.7}[nose]
    width = {"broad": 1.35, "button": 1.1}.get(nose, 1.0) * (0.9 + 0.2 * size)
    brow = (0.010 + (0.012 if male else 0.0)) * (0.8 + 0.4 * s.face.brow_weight)
    a["nose_width"] = width

    def f_of(y: float) -> float:
        return (y - fig.crown) / hh

    def nose_bump(alpha: float, y: float) -> float:
        f = f_of(y)
        al = wrap180(alpha)
        if abs(al) > 40.0 or f < bridge_f - 0.02 or f > base_f + 0.01:
            return 0.0
        if f <= tip_f:
            t = max(0.0, (f - bridge_f) / (tip_f - bridge_f))
            prof = length * (0.22 + 0.78 * t ** 1.25) + curve * 0.018 * math.sin(math.pi * t)
            if nose == "upturned":
                prof -= 0.012 * smoothstep(0.75, 1.0, t)
            sig = 6.5 + 4.0 * width * t
        else:
            t = (f - tip_f) / (base_f - tip_f)
            prof = length * (1.0 - 0.82 * smoothstep(0.0, 1.0, t))
            sig = 10.5 * width
        fade = smoothstep(bridge_f - 0.02, bridge_f + 0.02, f)
        wings = 0.035 * width * gauss(f, tip_f + 0.015, 0.03) * (gauss(al, 13.0 * width, 6.0) + gauss(al, -13.0 * width, 6.0))
        return hh * (fade * prof * gauss(al, 0.0, sig) + wings)

    def relief(alpha: float, y: float) -> float:
        f = f_of(y)
        al = wrap180(alpha)
        v = brow * gauss(f, a["brow_f"] + 0.005, 0.045) * gauss(al, 0.0, 42.0)
        mf = a["mouth_f"]
        lips = 0.6 + 0.6 * s.face.lips
        v += 0.016 * lips * gauss(f, mf - 0.022, 0.018) * gauss(al, 0.0, 17.0)
        v += 0.019 * lips * gauss(f, mf + 0.028, 0.02) * gauss(al, 0.0, 15.0)
        v += 0.026 * s.face.chin * gauss(f, 0.925, 0.045) * gauss(al, 0.0, 22.0)
        v += 0.010 * gauss(f, 0.55, 0.06) * (gauss(al, 48.0, 18.0) + gauss(al, -48.0, 18.0))
        return hh * v

    return [nose_bump, relief]


# ---- horse ----------------------------------------------------------------------------------


def _horse(fig) -> HeadModel:
    """A long head carried upright, the face running forward and down into
    a broad muzzle; eyes set wide on the sides; tall ears; a mane."""
    hh = fig.hh
    m = fig.spec.head.muzzle
    # In profile: a flat forehead running forward and down to a broad muzzle,
    # and behind it a deep round jowl that the neck goes into; the throat
    # line runs from the jowl forward to the chin.
    rows = [
        (0.00, 0.0, 0.0, 0.0, -0.08, 2.0),
        (0.10, 0.24, 0.27, 0.30, -0.08, 2.0),
        (0.24, 0.30, 0.33, 0.38, -0.06, 2.1),
        (0.38, 0.31, 0.38 + 0.03 * m, 0.42, -0.02, 2.2),
        (0.52, 0.30, 0.42 + 0.05 * m, 0.44, 0.02 * m, 2.3),
        (0.64, 0.27, 0.43 + 0.07 * m, 0.36, 0.08 * m, 2.4),
        (0.76, 0.24, 0.43 + 0.08 * m, 0.22, 0.15 * m, 2.4),
        (0.88, 0.235, 0.40 + 0.07 * m, 0.18, 0.21 * m, 2.3),
        (0.96, 0.23, 0.35 + 0.06 * m, 0.16, 0.24 * m, 2.2),
        (1.00, 0.17, 0.28 + 0.05 * m, 0.11, 0.25 * m, 2.1),
    ]
    layout = {
        "eye_f": 0.36, "brow_f": 0.29, "eye_alpha": 44.0, "eye_w": 0.155, "iris": 0.62, "nose_tip_f": 0.9, "mouth_f": 0.975,
        "mouth_alpha": 34.0, "nose": "horse", "pupil": "round",
    }

    def relief(alpha: float, y: float) -> float:
        f = (y - fig.crown) / hh
        al = wrap180(alpha)
        v = 0.02 * gauss(f, 0.3, 0.05) * (gauss(al, 40.0, 16.0) + gauss(al, -40.0, 16.0))
        v += 0.03 * gauss(f, 0.92, 0.05) * (gauss(al, 18.0, 12.0) + gauss(al, -18.0, 12.0))
        v += 0.02 * gauss(f, 0.6, 0.12) * (gauss(al, 70.0, 22.0) + gauss(al, -70.0, 22.0))
        return hh * v

    return HeadModel("horse", _rows(fig.fy, hh, rows), [relief], layout, ears="horse", hair="mane", muzzle_f=0.78, neck_f=0.56)


# ---- dog ------------------------------------------------------------------------------------


def _dog(fig) -> HeadModel:
    """A broad skull, a muzzle of middle length ending in a big dark nose,
    jowls; the ears as the spec says (floppy or pointed)."""
    hh = fig.hh
    m = fig.spec.head.muzzle
    rows = [
        (0.00, 0.0, 0.0, 0.0, -0.05, 2.0),
        (0.13, 0.35, 0.36, 0.42, -0.05, 2.0),
        (0.28, 0.4, 0.41, 0.45, -0.03, 2.0),
        (0.44, 0.38, 0.42 + 0.06 * m, 0.38, 0.0, 2.1),
        (0.58, 0.3, 0.5 + 0.12 * m, 0.3, 0.05 * m, 2.3),
        (0.7, 0.27, 0.52 + 0.14 * m, 0.27, 0.07 * m, 2.4),
        (0.82, 0.28, 0.44 + 0.1 * m, 0.25, 0.06 * m, 2.3),
        (0.93, 0.24, 0.36 + 0.06 * m, 0.22, 0.05 * m, 2.1),
        (1.00, 0.12, 0.28, 0.18, 0.05, 2.0),
    ]
    layout = {
        "eye_f": 0.42, "brow_f": 0.34, "eye_alpha": 28.0, "eye_w": 0.12, "iris": 0.72, "nose_tip_f": 0.6, "mouth_f": 0.84,
        "mouth_alpha": 30.0, "nose": "dog", "pupil": "round",
    }

    def relief(alpha: float, y: float) -> float:
        f = (y - fig.crown) / hh
        al = wrap180(alpha)
        v = 0.05 * m * gauss(f, 0.6, 0.05) * gauss(al, 0.0, 14.0)
        v += 0.018 * gauss(f, 0.33, 0.05) * (gauss(al, 26.0, 14.0) + gauss(al, -26.0, 14.0))
        v += 0.025 * gauss(f, 0.82, 0.07) * (gauss(al, 40.0, 20.0) + gauss(al, -40.0, 20.0))
        return hh * v

    ears = "dog_floppy" if fig.spec.head.ears in ("default", "floppy") else "dog_pointed"
    return HeadModel("dog", _rows(fig.fy, hh, rows), [relief], layout, ears=ears, hair="tuft", muzzle_f=0.55, neck_f=0.7)


# ---- cat ------------------------------------------------------------------------------------


def _cat(fig) -> HeadModel:
    """A round head, a short muzzle with a small nose, full cheeks,
    triangular ears; eyes with slit pupils."""
    hh = fig.hh
    m = fig.spec.head.muzzle
    rows = [
        (0.00, 0.0, 0.0, 0.0, -0.04, 2.0),
        (0.14, 0.37, 0.38, 0.42, -0.04, 2.0),
        (0.3, 0.42, 0.42, 0.45, -0.02, 2.0),
        (0.48, 0.43, 0.43 + 0.03 * m, 0.4, 0.0, 2.1),
        (0.64, 0.42, 0.44 + 0.05 * m, 0.33, 0.02, 2.2),
        (0.78, 0.33, 0.4 + 0.04 * m, 0.27, 0.03, 2.1),
        (0.9, 0.22, 0.33, 0.22, 0.03, 2.0),
        (1.00, 0.08, 0.26, 0.16, 0.03, 2.0),
    ]
    layout = {
        "eye_f": 0.46, "brow_f": 0.37, "eye_alpha": 26.0, "eye_w": 0.13, "iris": 0.85, "nose_tip_f": 0.62, "mouth_f": 0.73,
        "mouth_alpha": 15.0, "nose": "cat", "pupil": "slit",
    }

    def relief(alpha: float, y: float) -> float:
        f = (y - fig.crown) / hh
        al = wrap180(alpha)
        v = 0.03 * m * gauss(f, 0.64, 0.06) * (gauss(al, 12.0, 12.0) + gauss(al, -12.0, 12.0))
        v += 0.03 * gauss(f, 0.66, 0.08) * (gauss(al, 62.0, 18.0) + gauss(al, -62.0, 18.0))
        return hh * v

    return HeadModel("cat", _rows(fig.fy, hh, rows), [relief], layout, ears="cat", hair="tuft", muzzle_f=0.6, neck_f=0.72)


# ---- bird -----------------------------------------------------------------------------------


def _bird(fig) -> HeadModel:
    """A round head on which the beak is a separate cone, eyes set wide, a
    crest of feathers for hair, no ears."""
    hh = fig.hh
    rows = [
        (0.00, 0.0, 0.0, 0.0, -0.04, 2.0),
        (0.15, 0.36, 0.38, 0.42, -0.04, 2.0),
        (0.32, 0.41, 0.43, 0.45, -0.02, 2.0),
        (0.5, 0.41, 0.44, 0.42, 0.0, 2.0),
        (0.68, 0.36, 0.4, 0.34, 0.0, 2.0),
        (0.84, 0.27, 0.32, 0.27, 0.0, 2.0),
        (1.00, 0.12, 0.2, 0.18, 0.0, 2.0),
    ]
    layout = {
        "eye_f": 0.45, "brow_f": 0.37, "eye_alpha": 44.0, "eye_w": 0.12, "iris": 0.7, "nose_tip_f": 0.55, "mouth_f": 0.6,
        "mouth_alpha": 0.0, "nose": "bird", "pupil": "round", "beak": 0.34 * fig.spec.head.muzzle,
    }
    return HeadModel("bird", _rows(fig.fy, hh, rows), [], layout, ears="none", hair="crest", neck_f=0.72)


# ---- sea lion -------------------------------------------------------------------------------


def _sea_lion(fig) -> HeadModel:
    """A sleek round head on a thick neck, a tapered muzzle with full
    whisker pads and a small nose pad at its tip, big dark eyes, small ear
    flaps low behind the eyes, no hair. A male (a bull) has the sagittal
    crest: a tall narrow dome over the brow, above the skull's crown."""
    hh = fig.hh
    m = fig.spec.head.muzzle
    if fig.female:
        # The forehead slopes smoothly down into the muzzle.
        top = [
            (0.00, 0.0, 0.0, 0.0, -0.06, 2.0),
            (0.12, 0.3, 0.33, 0.36, -0.05, 2.0),
            (0.26, 0.35, 0.41, 0.42, -0.03, 2.0),
        ]
    else:
        # The crest rises steeply over the eyes, its top forward of the
        # skull's centre, and slopes down behind to the thick nape. It is
        # narrow across (a ridge), so from the front it is a raised dome.
        top = [
            (-0.17, 0.0, 0.0, 0.0, 0.08, 2.0),
            (-0.16, 0.13, 0.13, 0.14, 0.08, 2.0),
            (-0.13, 0.19, 0.2, 0.21, 0.075, 2.0),
            (-0.07, 0.24, 0.28, 0.29, 0.06, 2.0),
            (0.02, 0.28, 0.36, 0.35, 0.04, 2.0),
            (0.12, 0.31, 0.42, 0.4, 0.01, 2.0),
            (0.24, 0.34, 0.46, 0.43, -0.02, 2.0),
        ]
    # The back of the head stays deep down to the jaw: the head runs into
    # the neck with no step.
    rows = top + [
        (0.4, 0.36, 0.48 + 0.04 * m, 0.43, 0.01 * m, 2.1),
        (0.52, 0.35, 0.54 + 0.08 * m, 0.42, 0.04 * m, 2.2),
        (0.63, 0.33, 0.57 + 0.11 * m, 0.41, 0.07 * m, 2.3),
        (0.73, 0.31, 0.54 + 0.11 * m, 0.41, 0.08 * m, 2.3),
        (0.83, 0.29, 0.45 + 0.08 * m, 0.41, 0.07 * m, 2.1),
        (0.93, 0.25, 0.36 + 0.04 * m, 0.39, 0.04 * m, 2.0),
        (1.00, 0.19, 0.28, 0.35, 0.03, 2.0),
    ]
    layout = {
        "eye_f": 0.38, "brow_f": 0.3, "eye_alpha": 42.0, "eye_w": 0.185, "iris": 0.95, "nose_tip_f": 0.6, "mouth_f": 0.84,
        "mouth_alpha": 26.0, "nose": "sea_lion", "pupil": "round",
    }

    def relief(alpha: float, y: float) -> float:
        f = (y - fig.crown) / hh
        al = wrap180(alpha)
        return hh * 0.035 * gauss(f, 0.72, 0.06) * (gauss(al, 16.0, 11.0) + gauss(al, -16.0, 11.0))

    return HeadModel("sea_lion", _rows(fig.fy, hh, rows), [relief], layout, ears="flap", hair="none", muzzle_f=0.56, neck_f=0.58)


_BUILDERS = {"human": _human, "horse": _horse, "dog": _dog, "cat": _cat, "bird": _bird, "sea_lion": _sea_lion}


def head_model(fig) -> HeadModel:
    return _BUILDERS[fig.spec.head.species](fig)


def skull_loft(model: HeadModel) -> Loft:
    return Loft(list(model.keys))


def head_loft(model: HeadModel) -> Loft:
    return Loft(list(model.keys), list(model.bumps))


__all__ = ["COATS", "COATS_BY_SEX", "HEAD_SCALE", "HeadModel", "SPECIES", "head_loft", "head_model", "skull_loft"]
