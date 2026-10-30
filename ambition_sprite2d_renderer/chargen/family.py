"""Families: a look the generator draws a spec in.

A family is a proportion profile (``Proportions``, read by ``body.py``,
``species.py``, ``draw.py`` and ``wear.py``), a face profile (``FaceStyle``,
read by ``species.py`` and ``headdraw.py``) and a drawing style
(``svgout.Style``: ink, line weights, shading). A spec names its family
(``CharacterSpec.family``); the base and the seed still give the body numbers,
and the family changes how those numbers become a drawing. Every family draws
the same parts, in 3D, in all five views, with the same rig and motion.

``standard`` is the house look; its values are the constants the generator
had before families, so a standard spec draws byte-identical SVG. ``crew`` is
the look of the cryptography crew (``targets/characters/crypto_crew.py`` on
``_person_rig``), measured from their published sheets (2026-10-24): a
shorter leg, a longer neck, a wide round head with a large nose, a narrow
body, thick limbs with little taper, large fists, heavy shoes, a heavy
outline in a violet ink, and a cool violet shade with a light rim. They are
grown people, not mascots: the head is not larger than a standard head, and
the eyes are only a little larger.

To add a family, add one row to ``FAMILIES``: its proportions, face and
style. Do not fork a drawing module for it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from .svgout import STANDARD, Style


@dataclass(frozen=True)
class Proportions:
    """The body numbers of a family. A fraction of the height is ``H``; of
    the head's height, ``hh``. A multiplier of 1 keeps the standard size."""

    #: The hip joint's height, as a part of ``H``.
    hip: float = 0.45
    #: Where clothes are worn at the waist (a waistband, a belt, a tucked
    #: hem), as a part of the trunk from the shoulder line down to the hip
    #: joint. The body's narrowest line is at 0.62 of it.
    belt: float = 0.78
    #: The base of the neck and the shoulder line under the chin, as parts
    #: of ``hh``.
    neck_base: float = 0.17
    shoulder_drop: float = 0.4
    #: Multipliers: the head's height; its width and its depth (every
    #: species' head).
    head: float = 1.0
    head_width: float = 1.0
    head_depth: float = 1.0
    #: Multipliers: the neck's radius; the shoulders' half-width; the width
    #: of the chest, the waist and the hips.
    neck_r: float = 1.0
    shoulders: float = 1.0
    torso: float = 1.0
    #: Multipliers: the arm's radii (shoulder, elbow, wrist) and its length.
    arm_r: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    arms: float = 1.0
    #: How far a hanging arm goes out from the body, in degrees.
    arm_splay: float = 10.0
    #: Multipliers: the leg's radii (thigh, knee, calf, ankle).
    leg_r: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    #: Multipliers: the fist's size; a foot or a shoe's length, width and
    #: height.
    hand: float = 1.0
    foot: Tuple[float, float, float] = (1.0, 1.0, 1.0)


@dataclass(frozen=True)
class FaceStyle:
    """How a family draws a face. Multipliers of the standard sizes."""

    #: The eye's width, and its height as a part of its width.
    eye: float = 1.0
    eye_open: float = 1.0
    #: ``iris``: a coloured iris with a pupil, cut by the lids. ``dot``: a
    #: small dark pupil with a catch-light on the white (``iris`` is then the
    #: pupil's size).
    pupil: str = "iris"
    iris: float = 1.0
    #: The brows' weight; the nose's length and width (human).
    brow: float = 1.0
    nose: float = 1.0
    nose_width: float = 1.0
    #: The mouth's width, and the weight of its line.
    mouth: float = 1.0
    lip: float = 1.0
    #: A woman's upper lash line and its outer flick: a multiplier of their
    #: weight and length.
    lash: float = 1.0
    #: The colour of the mouth line (human), with a light line on the lower
    #: lip under it. ``None``: the standard lines.
    lip_color: Optional[str] = None
    #: ``outlined``: the eye has one thin line all round it, no outer flick,
    #: and a tall pupil in the iris. ``standard``: a lash line on top.
    eye_style: str = "standard"
    #: ``line``: the nose is one line down its shadow side and a short foot.
    nose_style: str = "standard"
    #: The ink of the head and the face (the skin's outline, the eye lines).
    #: ``None``: the style's ink.
    ink: Optional[str] = None


@dataclass(frozen=True)
class Family:
    key: str
    description: str
    body: Proportions = field(default_factory=Proportions)
    face: FaceStyle = field(default_factory=FaceStyle)
    style: Style = STANDARD


#: The ink of the crew (``_ai_era_kit.OUTLINE``, (34, 22, 48)).
CREW_INK = "#221630"

FAMILIES: Dict[str, Family] = {
    "standard": Family("standard", "The house look: about 6.5 heads, a thin outline, a warm shade."),
    "crew": Family(
        "crew",
        "The look of the cryptography crew: a shorter leg and a longer neck, a wide round head with a large nose, a narrow "
        "body, thick limbs, large fists and heavy shoes; a heavy violet outline, a cool shade and a light rim.",
        body=Proportions(
            # 168 cm is 108 px: the hips 48 px up, the neck 24 px under the crown.
            hip=0.448,
            neck_base=0.3,
            shoulder_drop=0.52,
            head=1.12,
            # A crew head is about as wide as it is high (front: 20 px of 121).
            head_width=1.22,
            head_depth=1.08,
            neck_r=0.95,
            # Front: 25 px across the arms of 121.
            shoulders=0.84,
            torso=0.9,
            # Sleeve 6.8 / 5.8 / 5.0 px; arm 37 px of 108.
            arm_r=(1.12, 1.25, 1.45),
            arms=1.05,
            arm_splay=5.0,
            # Trouser leg 7.4 / 6.2 / 5.4 px: a tube, no calf.
            leg_r=(0.8, 1.02, 0.95, 1.3),
            hand=1.28,
            foot=(0.98, 1.35, 1.3),
        ),
        # Large features, so that a face reads at game size (168 cm is 108 px).
        face=FaceStyle(eye=1.75, eye_open=1.6, pupil="dot", iris=0.72, brow=2.4, nose=2.2, nose_width=1.4, mouth=1.25, lip=1.3),
        style=Style(key="crew", ink=CREW_INK, outline=1.9, fine=2.5, shade_tint="#281446", shade_mix=1.16, shade_band=1.7, rim=0.12,
                    rim_mix=0.3),
    ),
    # Alice v2 (``targets/characters/alice_v2.py``) stands beside Bob, who is
    # drawn by hand (``data/characters/bob/bob.svg``): his warm near-black
    # ink at about his line weight, and a face as large as the first Alice's
    # at game size.
    "cast": Family(
        "cast",
        "The look of the hand-drawn cast beside Bob: a larger head with large features that read on a phone (an adult's, not a "
        "mascot's), a heavy warm near-black outline.",
        body=Proportions(head=1.22, head_width=0.95),
        face=FaceStyle(eye=1.7, eye_open=1.0, pupil="iris", iris=1.2, brow=0.95, nose=0.85, nose_width=0.8, mouth=1.1, lip=1.8, lash=1.25,
                       lip_color="#9e535a", eye_style="outlined", nose_style="line", ink="#5a3d44"),
        style=Style(key="cast", ink="#14110f", outline=1.1, fine=1.45),
    ),
}

DEFAULT = "standard"


def family_of(spec) -> Family:
    """The family of ``spec``."""
    return FAMILIES[getattr(spec, "family", DEFAULT) or DEFAULT]


def family_named(key: Optional[str]) -> Family:
    if key is None:
        return FAMILIES[DEFAULT]
    if key not in FAMILIES:
        raise ValueError(f"unknown family {key!r}; one of {sorted(FAMILIES)}")
    return FAMILIES[key]


__all__ = ["CREW_INK", "DEFAULT", "FAMILIES", "FaceStyle", "Family", "Proportions", "family_named", "family_of"]
