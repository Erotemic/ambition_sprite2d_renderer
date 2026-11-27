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

from .family import family_of
from .geometry import Loft, RingKey, gauss, lerp, smoothstep, wrap180
from .spec import SPECIES

#: A species' head height against a human's of the same build.
HEAD_SCALE = {"human": 1.0, "horse": 1.16, "dog": 1.05, "cat": 0.98, "bird": 1.0, "pigeon": 0.94, "sea_lion": 1.02, "alligator": 0.64, "finch": 0.94,
              "rabbit": 1.0, "bear": 1.12, "ram": 1.08, "owl": 1.05, "kangaroo": 1.03}
#: Coats: fur and feathers, by species.
COATS: Dict[str, Tuple[str, ...]] = {
    "horse": ("#7a4a2c", "#5c3a24", "#a8672f", "#2e2622", "#8d8a86", "#c9a26a", "#e6dfd2", "#4a3528"),
    "dog": ("#c08a4e", "#8a5a34", "#e4cfa6", "#3a3230", "#a9a39b", "#d7a45c", "#6e4a33", "#f0e8da"),
    "cat": ("#d68c4a", "#8b8580", "#3a3436", "#e8dcc8", "#b97a46", "#c9b9a4", "#5e5550", "#f2ece2"),
    "bird": ("#3f6f9e", "#c9473a", "#e3c24a", "#5b8f4f", "#ece6da", "#2e2c34", "#8a6a9e", "#d98a3e"),
    # Blue-bar grey, ash red, white, brown, black: the town pigeon's morphs.
    "pigeon": ("#8b94a3", "#7a8292", "#9aa2ae", "#5d6370", "#a77a68", "#e9e6e0", "#6b5a50", "#3c3d44"),
    "sea_lion": ("#c9a876", "#b8946a", "#d4b384", "#a9804f", "#4e3628", "#5c4232", "#3e3029", "#6b4a32"),
    # Dark olive to near black hides.
    "alligator": ("#3d4a2e", "#2f3a26", "#4a5434", "#2a2f24", "#424a30", "#55603a", "#33392a", "#262a20", "#efece3"),
    # A house finch's streaky brown, a goldfinch's yellow, a greenfinch's
    # olive, a zebra finch's grey, a bullfinch's rose, a chaffinch's chestnut.
    "finch": ("#8a6a50", "#e2bb32", "#7c8048", "#8c8c8e", "#c46a5a", "#9a5a3a", "#b8955e", "#6e6258"),
    # Wild agouti, white, grey, black, fawn, cream, chocolate.
    "rabbit": ("#b8916a", "#ece7de", "#8e8984", "#3a3432", "#c9a27a", "#dcc09a", "#6e5544", "#a08a74"),
    # Brown, dark, black, cinnamon, honey, polar white.
    "bear": ("#6a4a32", "#4a3628", "#2c2624", "#80583a", "#a47a50", "#eee8dc", "#5a4232", "#3a2e28"),
    # Wool white, cream, a black face, a brown goat, tan, grey.
    "ram": ("#ece4d2", "#ddd0b6", "#3a3230", "#8a6e52", "#b49a78", "#9a928a", "#c9bda8", "#6e6258"),
    # Tawny, a barn owl's buff, grey, snowy white, dark brown.
    "owl": ("#8a6a4a", "#c9a06a", "#9a9690", "#ece6da", "#6e5440", "#b88a56", "#7a7068", "#a88460"),
    "kangaroo": ("#af6546", "#bd8761", "#a3917d", "#7f7770", "#5f5450", "#c5ab8a"),
}
#: The alligator's albino coat: white to pale cream (its eyes are pink-red).
ALBINO = "#efece3"
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
    #: How far round from the front the muzzle's colour reaches (degrees).
    muzzle_alpha: float = 75.0
    #: The neck's front (the throat) is in the muzzle's colour too.
    throat: bool = False
    #: The neck is iridescent (a pigeon's): green over purple at its sides
    #: and front, from this ``f`` of the head down; 0 for none.
    sheen: float = 0.0
    #: How strong the sheen's green and purple are on the coat.
    sheen_strength: float = 1.0
    #: Where the neck enters the head (a fraction ``f``): the neck's top ring
    #: is fitted inside the head's ring there, and the head turns about its
    #: centre. ``None``: the human neck, which meets the head under the jaw.
    neck_f: float | None = None
    #: The skull that hair and hats sit on and the neck goes under, when it
    #: is not the whole head (a long snout runs forward of it).
    skull_keys: List[RingKey] | None = None


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
    F = family_of(s).face
    layout = {
        "eye_f": 0.475, "brow_f": 0.395, "eye_alpha": 23.5 * s.face.eye_spacing, "eye_w": 0.142 * s.face.eye_size * F.eye,
        "iris": 0.56 * F.iris,
        "nose_tip_f": {"long": 0.655, "button": 0.6, "upturned": 0.605}.get(nose, 0.63), "mouth_f": 0.77,
        "mouth_alpha": 16.5 * s.face.mouth_width * (0.95 if fig.female else 1.0) * F.mouth, "nose": "human", "pupil": "round",
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
    F = family_of(s).face
    length = {"straight": 0.105, "button": 0.08, "long": 0.13, "hooked": 0.12, "broad": 0.1, "upturned": 0.09}[nose] * size * F.nose
    curve = {"straight": 0.0, "button": -0.5, "long": 0.1, "hooked": 1.0, "broad": 0.0, "upturned": -0.7}[nose]
    width = {"broad": 1.35, "button": 1.1}.get(nose, 1.0) * (0.9 + 0.2 * size) * F.nose_width
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
    muzzle_f = 0.78
    length = fig.spec.head.face_length
    if length != 1.0:
        # Every height on the head moves as f ** length: the crown and the
        # chin stay, and the brow, the eyes and the muzzle's start climb (a
        # longer face) or drop (a shorter one).
        rows = [(f ** length, *rest) for f, *rest in rows]
        for key in ("eye_f", "brow_f", "nose_tip_f", "mouth_f"):
            layout[key] = layout[key] ** length
        muzzle_f = muzzle_f ** length

    def relief(alpha: float, y: float) -> float:
        f = (y - fig.crown) / hh
        if length != 1.0 and f > 0.0:
            f = f ** (1.0 / length)  # back to the height the bumps were placed at
        al = wrap180(alpha)
        v = 0.02 * gauss(f, 0.3, 0.05) * (gauss(al, 40.0, 16.0) + gauss(al, -40.0, 16.0))
        v += 0.03 * gauss(f, 0.92, 0.05) * (gauss(al, 18.0, 12.0) + gauss(al, -18.0, 12.0))
        v += 0.02 * gauss(f, 0.6, 0.12) * (gauss(al, 70.0, 22.0) + gauss(al, -70.0, 22.0))
        return hh * v

    return HeadModel("horse", _rows(fig.fy, hh, rows), [relief], layout, ears="horse", hair="mane", muzzle_f=muzzle_f, neck_f=0.56)


# ---- dog ------------------------------------------------------------------------------------


def _dog(fig) -> HeadModel:
    """A broad round skull with a clear STOP at the eyes: the muzzle steps
    forward from under the brow and runs out level, a boxy block with a big
    dark nose on its tip; the lower jaw is shorter and sits under it, and the
    upper lip hangs over it at the sides. The ears as the spec says (floppy
    flaps that hang past the cheeks, or pointed and upright). No hair: a
    human haircut on a dog reads as a toupee."""
    hh = fig.hh
    h = fig.spec.head
    m = h.muzzle
    mz = 0.36 * m
    # The stop: below 1 the forehead fills forward toward the muzzle's top,
    # above 1 the forehead domes and the step under the brow deepens.
    shallow = max(0.0, 1.0 - h.stop)
    deep = max(0.0, h.stop - 1.0)
    fill = 0.46 + mz - 0.5
    # The flews: the upper lip hangs down over the set-back jaw, filling the
    # step under the lip line and widening the muzzle's lower sides.
    fl = h.flews
    rows = [
        (0.00, 0.0, 0.0, 0.0, -0.06, 2.0),
        (0.08, 0.3, 0.3 + 0.04 * deep, 0.34, -0.06, 2.0),
        (0.18, 0.4, 0.39 + 0.1 * deep + 0.03 * shallow, 0.43, -0.05, 2.0),
        (0.3, 0.44, 0.43 + 0.14 * deep + 0.15 * shallow * fill, 0.46, -0.04, 2.1),
        (0.4, 0.43, 0.46 + 0.1 * deep + 0.45 * shallow * fill, 0.45, -0.03, 2.1),
        # The stop: the muzzle steps out from under the brow.
        (0.45, 0.39, 0.5 - 0.06 * deep + 0.75 * shallow * fill, 0.43, -0.03, 2.2),
        (0.5, 0.34, 0.46 + mz, 0.41, -0.02, 2.6),
        (0.6, 0.33, 0.48 + mz, 0.38, -0.02, 2.7),
        (0.69, 0.33 + 0.02 * fl, 0.48 + mz, 0.35, -0.02, 2.7),
        # Under the lip line the lower jaw is set back.
        (0.74, 0.29 + 0.06 * fl, 0.4 + 0.8 * mz + fl * (0.06 + 0.18 * mz), 0.32, -0.02, 2.6 + 0.1 * fl),
        (0.86, 0.25 + 0.06 * fl, 0.32 + 0.6 * mz + fl * (0.08 + 0.3 * mz), 0.28, -0.02, 2.3 + 0.2 * fl),
        (0.95, 0.2, 0.26 + 0.3 * mz, 0.24, -0.02, 2.1),
        (1.00, 0.1, 0.18, 0.18, -0.02, 2.0),
    ]
    # The skull's breadth: all of it across the cranium, less down the
    # muzzle, little at the jaw (where the neck goes in).
    sk = h.skull - 1.0
    rows = [(f, rx * (1.0 + sk * (1.0 - 0.75 * smoothstep(0.42, 0.74, f))), rzf, rzb * (1.0 + 0.4 * sk * (1.0 - smoothstep(0.4, 0.7, f))),
             cz, sq) for f, rx, rzf, rzb, cz, sq in rows]
    layout = {
        "eye_f": 0.395, "brow_f": 0.315, "eye_alpha": 31.0, "eye_w": 0.13, "iris": 0.78, "nose_tip_f": 0.535, "mouth_f": 0.705,
        "mouth_alpha": 62.0, "nose": "dog", "pupil": "round",
    }

    def relief(alpha: float, y: float) -> float:
        f = (y - fig.crown) / hh
        al = wrap180(alpha)
        # The brows over the stop, and the furrow between them.
        v = 0.03 * (1.0 + 1.2 * deep - 0.6 * shallow) * gauss(f, 0.36, 0.035) * (gauss(al, 24.0, 12.0) + gauss(al, -24.0, 12.0))
        # Full cheeks behind the muzzle, and the upper lip (the flews) hanging at its sides.
        v += 0.03 * gauss(f, 0.62, 0.08) * (gauss(al, 62.0, 16.0) + gauss(al, -62.0, 16.0))
        v += (0.02 + 0.03 * fl) * gauss(f, 0.69 + 0.04 * fl, 0.025 + 0.025 * fl) * (gauss(al, 50.0, 18.0) + gauss(al, -50.0, 18.0))
        return hh * v

    ears = "dog_floppy" if fig.spec.head.ears in ("default", "floppy") else "dog_pointed"
    return HeadModel("dog", _rows(fig.fy, hh, rows), [relief], layout, ears=ears, hair="none", muzzle_f=0.48, muzzle_alpha=70.0,
                     neck_f=0.72)


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
        # Cheek fluff: the fur stands out below and behind the eyes.
        fluff = fig.spec.head.cheek_fluff
        if fluff:
            v += 0.06 * fluff * gauss(f, 0.72, 0.09) * (gauss(al, 78.0, 20.0) + gauss(al, -78.0, 20.0))
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


# ---- pigeon ---------------------------------------------------------------------------------


def _pigeon(fig) -> HeadModel:
    """A town pigeon: a small round head that flows into a thick neck (no
    chin), the forehead sloping down into a short slim dark beak with the
    white cere puffed over its base; round orange eyes set on the sides; no
    crest, no ears; the neck iridescent green over purple."""
    hh = fig.hh
    h = fig.spec.head
    rows = [
        (0.00, 0.0, 0.0, 0.0, 0.0, 2.0),
        (0.08, 0.28, 0.3, 0.32, 0.0, 2.0),
        (0.22, 0.4, 0.43, 0.43, 0.0, 2.0),
        (0.38, 0.44, 0.48, 0.45, 0.02, 2.0),
        (0.54, 0.42, 0.46, 0.42, 0.02, 2.0),
        (0.68, 0.34, 0.37, 0.36, 0.0, 2.0),
        # The ball of the head narrows into the thick iridescent neck.
        (0.8, 0.28, 0.29, 0.32, -0.02, 2.0),
        (1.00, 0.27, 0.27, 0.32, -0.03, 2.0),
    ]
    layout = {
        "eye_f": 0.36, "brow_f": 0.28, "eye_alpha": 50.0, "eye_w": 0.135, "iris": 0.95, "nose_tip_f": 0.46, "mouth_f": 0.48,
        "mouth_alpha": 0.0, "nose": "pigeon", "pupil": "round", "beak": 0.23 * h.muzzle, "beak_w": 0.6, "beak_h": 0.85,
        "beak_col": "#3e3a3e", "cere": h.cere, "beak_droop": 0.035 * h.beak_curve, "eye_ring": h.eye_ring,
    }
    return HeadModel("pigeon", _rows(fig.fy, hh, rows), [], layout, ears="none", hair="none", neck_f=0.7, sheen=0.6 if h.sheen > 0.0 else 0.0,
                     sheen_strength=h.sheen)


# ---- finch ----------------------------------------------------------------------------------


def _finch(fig) -> HeadModel:
    """A finch: a round, full-cheeked head that sits on the shoulders with
    hardly a neck, the brow running straight into a short, deep, conical
    beak (a seed-cracker's: broad and deep at the base, coming to a point),
    dark round eyes set on the sides, no crest, no ears. Its plumage may have
    a dark cap and a red face (``head.cap``, ``head.face_patch``)."""
    hh = fig.hh
    h = fig.spec.head
    rows = [
        (0.00, 0.0, 0.0, 0.0, 0.0, 2.0),
        (0.1, 0.3, 0.32, 0.34, -0.02, 2.0),
        (0.24, 0.42, 0.45, 0.45, -0.01, 2.0),
        (0.42, 0.46, 0.49, 0.46, 0.0, 2.0),
        # Full cheeks down to the throat.
        (0.6, 0.45, 0.47, 0.42, 0.0, 2.0),
        (0.76, 0.39, 0.41, 0.37, 0.0, 2.0),
        (0.9, 0.31, 0.32, 0.32, -0.02, 2.0),
        (1.00, 0.27, 0.27, 0.3, -0.03, 2.0),
    ]
    layout = {
        "eye_f": 0.38, "brow_f": 0.3, "eye_alpha": 47.0, "eye_w": 0.14, "iris": 0.95, "nose_tip_f": 0.5, "mouth_f": 0.52,
        "mouth_alpha": 0.0, "nose": "finch", "pupil": "round", "beak": 0.16 * h.muzzle, "beak_w": 0.75 + 0.25 * h.beak_depth,
        "beak_h": 0.95 + 0.6 * h.beak_depth, "beak_col": "#cdb293", "cap": h.cap, "face_patch": h.face_patch,
    }
    return HeadModel("finch", _rows(fig.fy, hh, rows), [], layout, ears="none", hair="none", neck_f=0.74)


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
    pads = fig.spec.head.whisker_pads

    def relief(alpha: float, y: float) -> float:
        f = (y - fig.crown) / hh
        al = wrap180(alpha)
        return hh * 0.035 * pads * gauss(f, 0.72, 0.06) * (gauss(al, 16.0, 11.0) + gauss(al, -16.0, 11.0))

    return HeadModel("sea_lion", _rows(fig.fy, hh, rows), [relief], layout, ears="flap", hair="none", muzzle_f=0.56, neck_f=0.58)


# ---- alligator ------------------------------------------------------------------------------


def _alligator(fig) -> HeadModel:
    """A LOW, FLAT head (not a dinosaur's tall skull on a thin neck): the
    snout is most of its length, long, flat and broad, ending in a round,
    bulbous U (not a crocodile's narrow V). The top is almost a flat line
    from the tip back to the thick neck; only the eye bumps (drawn by
    ``headdraw``) rise above it, with the eyes high at the back looking
    forward over the snout. A nostril knob sits on the tip. The jaw line runs
    back along each side and curls up behind the eye (the smile), with the
    upper teeth showing when it is shut. The lower jaw and the throat are
    pale. A male's head is broader.

    The rings stay centred on the skull (``cz`` 0), so the neck goes in
    under the back of the head. Hair and hats sit on ``skull_keys``: the
    back part of the head, not the snout."""
    hh = fig.hh
    m = fig.spec.head.muzzle
    w = 0.94 if fig.female else 1.06
    # The snout's breadth widens the head's rings, not the skull's (hats and
    # hair fit the skull).
    sw = w * fig.spec.head.snout_width
    tip = 1.55 + 0.5 * m
    # (f, rx, rzf, rzb, cz, sq); the snout's rows are boxy (sq) for the U.
    rows = [
        (0.00, 0.0, 0.0, 0.0, 0.0, 2.0),
        # The back of the head slopes down into the thick neck.
        (0.07, 0.36 * sw, 0.5, 0.3, 0.0, 2.4),
        (0.15, 0.4 * sw, 0.66 * tip, 0.4, 0.0, 2.7),
        (0.24, 0.42 * sw, 0.83 * tip, 0.47, 0.0, 2.9),
        (0.33, 0.43 * sw, 0.96 * tip, 0.52, 0.0, 3.0),
        (0.44, 0.44 * sw, tip, 0.56, 0.0, 3.0),
        (0.58, 0.44 * sw, tip, 0.59, 0.0, 3.0),
        # The lower jaw is deep at the back and thin at the tip: its
        # underside rises toward the tip.
        (0.7, 0.43 * sw, tip - 0.1, 0.6, 0.0, 2.9),
        (0.8, 0.41 * sw, tip - 0.32, 0.6, 0.0, 2.8),
        (0.9, 0.37 * sw, tip - 0.68, 0.58, 0.0, 2.6),
        (1.00, 0.27 * sw, tip - 1.1, 0.5, 0.0, 2.3),
    ]
    # The skull that hair and hats sit on is behind the eye bumps (their
    # back edge is about 0.2 hh in front of the centre), so a wig or a hat
    # never covers the eyes.
    skull = [
        (0.00, 0.0, 0.0, 0.0, -0.17, 2.0),
        (0.07, 0.34 * w, 0.3, 0.42, -0.17, 2.2),
        (0.3, 0.4 * w, 0.34, 0.44, -0.15, 2.3),
        (0.6, 0.42 * w, 0.36, 0.44, -0.12, 2.3),
        (1.00, 0.24 * w, 0.26, 0.32, -0.06, 2.2),
    ]
    layout = {
        "eye_f": 0.13, "brow_f": 0.085, "eye_alpha": 50.0, "eye_w": 0.2, "iris": 0.9, "nose_tip_f": 0.38, "mouth_f": 0.6,
        "mouth_alpha": 104.0, "nose": "alligator", "pupil": "slit", "mouth_wave": 0.04, "tip": tip,
        # Hats fit the skull above this (the snout is not under them).
        "crown_f": 0.7, "hat_flat": 0.0,
    }
    tf = layout["nose_tip_f"]

    def relief(alpha: float, y: float) -> float:
        f = (y - fig.crown) / hh
        al = wrap180(alpha)
        # The bulbous end of the snout, a little wider than behind it.
        return hh * 0.06 * gauss(f, tf + 0.15, 0.16) * (gauss(al, 36.0, 14.0) + gauss(al, -36.0, 14.0))

    return HeadModel("alligator", _rows(fig.fy, hh, rows), [relief], layout, ears="none", hair="none", muzzle_f=0.68, muzzle_alpha=124.0,
                     throat=True, neck_f=0.62, skull_keys=_rows(fig.fy, hh, skull))


# ---- rabbit ---------------------------------------------------------------------------------


def _rabbit(fig) -> HeadModel:
    """A rounded head, a little taller than wide, with full cheeks and a
    short soft muzzle: whisker pads either side of a small nose and a split
    lip, buck teeth under it. Big dark eyes set out on the sides. Long ears
    upright from the crown, or lopped down beside the face
    (``head.ear_lop``)."""
    hh = fig.hh
    m = fig.spec.head.muzzle
    rows = [
        (0.00, 0.0, 0.0, 0.0, -0.04, 2.0),
        (0.14, 0.33, 0.36, 0.40, -0.04, 2.0),
        (0.30, 0.39, 0.42, 0.44, -0.03, 2.0),
        (0.48, 0.41, 0.45 + 0.03 * m, 0.41, -0.01, 2.1),
        (0.62, 0.41, 0.48 + 0.05 * m, 0.35, 0.0, 2.2),
        (0.76, 0.34, 0.45 + 0.05 * m, 0.29, 0.01, 2.1),
        (0.88, 0.24, 0.36, 0.23, 0.01, 2.0),
        (1.00, 0.10, 0.26, 0.17, 0.01, 2.0),
    ]
    layout = {
        "eye_f": 0.43, "brow_f": 0.35, "eye_alpha": 40.0, "eye_w": 0.15, "iris": 0.95, "nose_tip_f": 0.6, "mouth_f": 0.72,
        "mouth_alpha": 11.0, "nose": "rabbit", "pupil": "round",
    }

    def relief(alpha: float, y: float) -> float:
        f = (y - fig.crown) / hh
        al = wrap180(alpha)
        # The whisker pads, and the full cheeks behind them.
        v = 0.035 * m * gauss(f, 0.66, 0.05) * (gauss(al, 13.0, 10.0) + gauss(al, -13.0, 10.0))
        v += 0.03 * gauss(f, 0.64, 0.09) * (gauss(al, 64.0, 18.0) + gauss(al, -64.0, 18.0))
        return hh * v

    ears = "rabbit_lop" if fig.spec.head.ear_lop >= 0.5 else "rabbit"
    return HeadModel("rabbit", _rows(fig.fy, hh, rows), [relief], layout, ears=ears, hair="tuft", muzzle_f=0.58, muzzle_alpha=58.0,
                     neck_f=0.72)


# ---- bear -----------------------------------------------------------------------------------


def _bear(fig) -> HeadModel:
    """A big, broad, round skull with small round ears high at its corners;
    under a shallow stop a short deep muzzle in a lighter colour, a big dark
    nose on its tip. Small eyes set close to the muzzle. Heavy cheeks."""
    hh = fig.hh
    m = fig.spec.head.muzzle
    mz = 0.24 * m
    rows = [
        (0.00, 0.0, 0.0, 0.0, -0.05, 2.0),
        (0.10, 0.34, 0.32, 0.38, -0.05, 2.0),
        (0.22, 0.46, 0.42, 0.47, -0.04, 2.0),
        (0.36, 0.50, 0.47, 0.48, -0.03, 2.1),
        (0.46, 0.49, 0.50, 0.46, -0.02, 2.1),
        # The muzzle steps out under the brow.
        (0.52, 0.36, 0.50 + mz, 0.43, -0.02, 2.5),
        (0.62, 0.34, 0.52 + mz, 0.39, -0.02, 2.6),
        (0.70, 0.33, 0.50 + mz, 0.35, -0.02, 2.5),
        (0.80, 0.29, 0.40 + 0.6 * mz, 0.31, -0.02, 2.3),
        (0.90, 0.23, 0.32 + 0.3 * mz, 0.27, -0.02, 2.1),
        (1.00, 0.11, 0.20, 0.20, -0.02, 2.0),
    ]
    layout = {
        "eye_f": 0.4, "brow_f": 0.32, "eye_alpha": 30.0, "eye_w": 0.11, "iris": 0.92, "nose_tip_f": 0.55, "mouth_f": 0.71,
        "mouth_alpha": 48.0, "nose": "dog", "pupil": "round",
    }

    def relief(alpha: float, y: float) -> float:
        f = (y - fig.crown) / hh
        al = wrap180(alpha)
        v = 0.025 * gauss(f, 0.36, 0.04) * (gauss(al, 24.0, 13.0) + gauss(al, -24.0, 13.0))
        # Heavy cheeks: the fur stands out at the sides of the jaw.
        v += 0.05 * gauss(f, 0.62, 0.1) * (gauss(al, 74.0, 20.0) + gauss(al, -74.0, 20.0))
        return hh * v

    return HeadModel("bear", _rows(fig.fy, hh, rows), [relief], layout, ears="round", hair="tuft", muzzle_f=0.5, muzzle_alpha=62.0,
                     neck_f=0.72)


# ---- ram ------------------------------------------------------------------------------------


def _ram(fig) -> HeadModel:
    """A ram's (or a goat's) head: long and narrow, the face running down
    from a flat poll over a gently Roman nose to a narrow muzzle; the eyes
    set on the sides with horizontal pupils; ears held out sideways; horns
    (``head.horns``, ``head.horn_style``) and a goat's beard (``head.beard``)
    are drawn by ``headdraw``."""
    hh = fig.hh
    m = fig.spec.head.muzzle
    rows = [
        (0.00, 0.0, 0.0, 0.0, -0.06, 2.0),
        (0.10, 0.27, 0.30, 0.32, -0.06, 2.0),
        (0.24, 0.33, 0.36, 0.40, -0.05, 2.1),
        (0.38, 0.33, 0.40 + 0.03 * m, 0.40, -0.01, 2.2),
        (0.52, 0.30, 0.43 + 0.05 * m, 0.36, 0.03 * m, 2.3),
        (0.66, 0.26, 0.45 + 0.07 * m, 0.28, 0.08 * m, 2.3),
        (0.78, 0.23, 0.44 + 0.07 * m, 0.20, 0.13 * m, 2.3),
        (0.90, 0.21, 0.38 + 0.06 * m, 0.17, 0.17 * m, 2.2),
        (1.00, 0.15, 0.30 + 0.05 * m, 0.12, 0.18 * m, 2.1),
    ]
    layout = {
        "eye_f": 0.36, "brow_f": 0.29, "eye_alpha": 48.0, "eye_w": 0.14, "iris": 0.95, "nose_tip_f": 0.86, "mouth_f": 0.95,
        "mouth_alpha": 24.0, "nose": "ram", "pupil": "bar",
    }

    def relief(alpha: float, y: float) -> float:
        f = (y - fig.crown) / hh
        al = wrap180(alpha)
        # The Roman nose: a ridge down the face.
        v = 0.03 * m * gauss(f, 0.6, 0.12) * gauss(al, 0.0, 14.0)
        v += 0.02 * gauss(f, 0.34, 0.05) * (gauss(al, 42.0, 14.0) + gauss(al, -42.0, 14.0))
        return hh * v

    return HeadModel("ram", _rows(fig.fy, hh, rows), [relief], layout, ears="ram", hair="tuft", muzzle_f=0.8, muzzle_alpha=40.0,
                     neck_f=0.56)


# ---- owl ------------------------------------------------------------------------------------


def _owl(fig) -> HeadModel:
    """A broad round head with a FLAT face: the facial disc (two rounded
    dishes of pale feathers, rimmed dark, ``head.disc``) round big eyes that
    look forward; a small hooked beak low between them; feather tufts over
    the eyes (``head.ear_tufts``). No neck to speak of: the head sits on the
    shoulders."""
    hh = fig.hh
    h = fig.spec.head
    rows = [
        (0.00, 0.0, 0.0, 0.0, -0.02, 2.0),
        (0.12, 0.36, 0.30, 0.40, -0.04, 2.0),
        (0.28, 0.46, 0.34, 0.47, -0.05, 2.2),
        (0.45, 0.49, 0.36, 0.48, -0.05, 2.3),
        (0.62, 0.47, 0.35, 0.45, -0.05, 2.3),
        (0.78, 0.40, 0.33, 0.40, -0.04, 2.2),
        (0.90, 0.33, 0.29, 0.35, -0.03, 2.0),
        (1.00, 0.29, 0.27, 0.33, -0.03, 2.0),
    ]
    layout = {
        "eye_f": 0.44, "brow_f": 0.33, "eye_alpha": 25.0, "eye_w": 0.18, "iris": 0.96, "nose_tip_f": 0.54, "mouth_f": 0.58,
        "mouth_alpha": 0.0, "nose": "owl", "pupil": "round", "beak": 0.11 * h.muzzle, "beak_w": 0.55, "beak_h": 1.15,
        "beak_col": "#d6c49a", "beak_droop": 0.06, "disc": h.disc,
    }
    ears = "tufts" if h.ear_tufts > 0.0 else "none"
    return HeadModel("owl", _rows(fig.fy, hh, rows), [], layout, ears=ears, hair="none", neck_f=0.74)


def _kangaroo(fig) -> HeadModel:
    h = fig.spec.head
    snout = 0.31 * h.muzzle
    rows = [
        (0.00, 0.0, 0.0, 0.0, -0.10, 2.0),
        (0.11, 0.26, 0.29, 0.31, -0.10, 2.0),
        (0.25, 0.34, 0.36 + 0.12 * snout, 0.34, -0.09, 2.0),
        (0.39, 0.36, 0.40 + 0.35 * snout, 0.34, -0.06, 2.1),
        (0.52, 0.34, 0.44 + 0.62 * snout, 0.32, -0.035, 2.0),
        (0.65, 0.30, 0.47 + 0.88 * snout, 0.29, -0.015, 1.9),
        (0.74, 0.25, 0.47 + snout, 0.25, 0.00, 2.0),
        (0.81, 0.23, 0.44 + snout, 0.23, 0.01, 2.1),
        (0.90, 0.20, 0.35 + 0.76 * snout, 0.21, 0.01, 2.0),
        (1.00, 0.10, 0.18 + 0.30 * snout, 0.17, 0.01, 2.0),
    ]
    rows = [
        (f, rx * lerp(h.skull, 1.0, smoothstep(0.40, 0.81, f)), rzf, rzb, cz, sq)
        for f, rx, rzf, rzb, cz, sq in rows
    ]
    layout = {
        "eye_f": 0.40, "brow_f": 0.32, "eye_alpha": 41.0, "eye_w": 0.15, "iris": 0.9,
        "nose_tip_f": 0.75, "mouth_f": 0.85, "mouth_alpha": 43.0, "nose": "kangaroo", "pupil": "round",
    }
    return HeadModel("kangaroo", _rows(fig.fy, fig.hh, rows), [], layout, ears="kangaroo", hair="tuft", neck_f=0.74)


_BUILDERS = {"human": _human, "horse": _horse, "dog": _dog, "cat": _cat, "bird": _bird, "pigeon": _pigeon, "sea_lion": _sea_lion, "alligator": _alligator,
             "finch": _finch, "rabbit": _rabbit, "bear": _bear, "ram": _ram, "owl": _owl, "kangaroo": _kangaroo}


def head_model(fig) -> HeadModel:
    """The head of ``fig``'s species, made as wide and as deep as its family
    says (``Proportions.head_width``, ``head_depth``)."""
    from dataclasses import replace

    model = _BUILDERS[fig.spec.head.species](fig)
    P = family_of(fig.spec).body
    if P.head_width != 1.0 or P.head_depth != 1.0:
        model.keys = [replace(r, rx=r.rx * P.head_width, rzf=r.rzf * P.head_depth, rzb=r.rzb * P.head_depth, cz=r.cz * P.head_depth)
                      for r in model.keys]
        if model.skull_keys:
            model.skull_keys = [replace(r, rx=r.rx * P.head_width, rzf=r.rzf * P.head_depth, rzb=r.rzb * P.head_depth,
                                        cz=r.cz * P.head_depth) for r in model.skull_keys]
    return model


def skull_loft(model: HeadModel) -> Loft:
    return Loft(list(model.skull_keys or model.keys))


def head_loft(model: HeadModel) -> Loft:
    return Loft(list(model.keys), list(model.bumps))


__all__ = ["ALBINO", "COATS", "COATS_BY_SEX", "HEAD_SCALE", "HeadModel", "SPECIES", "head_loft", "head_model", "skull_loft"]
