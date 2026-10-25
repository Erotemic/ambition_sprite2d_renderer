"""A spec's body in 3D: its joints at rest, its lofts and its face anchors.

Everything is in centimetres in the body frame of ``geometry`` (``l`` is the
character's left, ``y`` is down from the ground, ``z`` is forward). The rest
pose stands straight with the arms hanging a little away from the body, the
elbows a little bent and the knees a little forward, so that every view's IK
branch (which way an elbow or a knee bends) is read from the drawing.

Proportions are adult (about 7.5 heads tall). Two rulings are structural here
(Jon, 2026-10-12/13): no big eyes on a human, and a man's chest never reads as
a bust; a man's chest is as wide as the shoulders and tapers to the waist, and
only a woman's torso carries the (modest) ``bust`` bump.

The spec's family (``family.py``) gives the proportions the body numbers
multiply (``Proportions``): the standard family's are the constants of this
module.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from .family import family_of
from .geometry import Loft, RingKey, Vec3, add3, gauss, norm3, scale3, wrap180
from .spec import CharacterSpec
from .species import HEAD_SCALE, HeadModel, head_loft, head_model, skull_loft

#: The reference height every width is scaled from.
REF_H = 172.0


@dataclass
class Figure:
    """The resolved body of one spec, at rest."""

    spec: CharacterSpec
    H: float
    hh: float
    k: float
    female: bool
    crown: float
    chin: float
    y_nb: float
    y_sh: float
    y_chest: float
    y_under: float
    y_waist: float
    y_hipw: float
    y_hip: float
    y_crotch: float
    #: The joints at rest. Sides are the character's ``right`` and ``left``.
    joints: Dict[str, Vec3] = field(default_factory=dict)
    torso: Loft = None  # type: ignore[assignment]
    neck: Loft = None  # type: ignore[assignment]
    #: The neck's top ring (where the head's turn is pivoted for a species).
    neck_top: Optional[RingKey] = None
    head: Loft = None  # type: ignore[assignment]
    #: The head without the face's bumps: what hair and hats sit on.
    skull: Loft = None  # type: ignore[assignment]
    #: Radii: shoulder, elbow, wrist; thigh top, knee, calf, ankle.
    arm_r: Tuple[float, float, float] = (4.0, 3.2, 2.5)
    leg_r: Tuple[float, float, float, float] = (7.0, 4.8, 5.0, 3.3)
    #: Face anchors, as heights on the head (``fy``) and angles: the head
    #: model's layout.
    face: Dict[str, float] = field(default_factory=dict)
    species: str = "human"
    model: Optional[HeadModel] = None

    def fy(self, f: float) -> float:
        """The height of fraction ``f`` of the head (0 the crown, 1 the chin)."""
        return self.crown + f * self.hh

    @property
    def T(self) -> float:
        return self.y_hip - self.y_sh


def build(spec: CharacterSpec) -> Figure:
    b = spec.body
    P = family_of(spec).body
    female = spec.sex == "female"
    H = b.height_cm
    species = spec.head.species
    hh = b.head * H * (1.05 if spec.face.jaw == "long" and species == "human" else 1.0) * HEAD_SCALE[species] * P.head
    k = H / REF_H
    crown = -H
    chin = crown + hh
    y_nb = chin + P.neck_base * hh * b.neck
    y_sh = chin + P.shoulder_drop * hh * b.neck
    hip_h = P.hip * H * b.legs
    y_hip = -hip_h
    T = y_hip - y_sh
    fig = Figure(
        spec=spec, H=H, hh=hh, k=k, female=female, crown=crown, chin=chin, y_nb=y_nb, y_sh=y_sh,
        y_chest=y_sh + 0.23 * T, y_under=y_sh + 0.42 * T, y_waist=y_sh + 0.62 * T, y_hipw=y_sh + 0.9 * T, y_hip=y_hip,
        y_crotch=y_hip + 0.036 * H,
    )
    fig.species = species
    fig.model = head_model(fig)
    fig.face = fig.model.layout

    # ---- torso --------------------------------------------------------------------------
    sx = 0.9 if female else 1.0
    limbs = b.limbs
    sh_hw = 17.2 * k * b.shoulders * sx * P.shoulders
    neck_r = (0.215 if female else 0.245) * b.head * H * (0.85 + 0.15 * limbs) * (1.0 + 0.25 * b.belly) * {"horse": 1.25, "dog": 1.1, "sea_lion": 1.55}.get(species, 1.0) * P.neck_r
    chest_rx = 15.2 * k * b.chest * (0.91 if female else 1.0) * P.torso
    chest_rx = min(chest_rx, sh_hw + 1.0 * k)
    chest_rzf = 10.2 * k * b.chest * (0.95 if female else 1.0)
    chest_rzb = 9.6 * k * b.chest
    waist_rx = (13.0 * k * b.waist * (0.86 if female else 1.0) + 2.0 * k * b.belly) * P.torso
    waist_rzf = 8.8 * k * b.waist + 4.5 * k * b.belly
    hip_rx = 15.6 * k * b.hips * (1.08 if female else 1.0) * P.torso
    hip_rzf = 9.4 * k * b.hips + 2.5 * k * b.belly
    hip_rzb = 10.4 * k * b.hips * (1.07 if female else 1.0)
    shoulder_cap = sh_hw + 2.2 * k * limbs
    torso_keys = [
        RingKey(y_nb - 0.5, neck_r + 1.2, neck_r + 0.4, neck_r + 1.2, 0.0, -1.0 * k, 2.0),
        RingKey(y_sh - 2.2 * k, sh_hw * 0.74, 7.4 * k, 7.9 * k, 0.0, -1.0 * k, 2.3),
        RingKey(y_sh + 0.6 * k, sh_hw * 0.98, 8.8 * k * b.chest, 8.6 * k * b.chest, 0.0, -0.7 * k, 2.8),
        RingKey(y_sh + 3.2 * k, shoulder_cap, 9.4 * k * b.chest, 9.0 * k * b.chest, 0.0, -0.5 * k, 2.8),
        RingKey(fig.y_chest, max(chest_rx, shoulder_cap - 2.8 * k), chest_rzf, chest_rzb, 0.0, 0.0, 2.6),
        RingKey(fig.y_under, (chest_rx + waist_rx) / 2, (chest_rzf + waist_rzf) / 2, (chest_rzb + 8.6 * k) / 2, 0.0, 0.0, 2.5),
        RingKey(fig.y_waist, waist_rx, waist_rzf, 8.6 * k + 0.8 * k * b.belly, 0.0, 0.2 * k * b.belly, 2.3),
        RingKey(fig.y_hipw, hip_rx, hip_rzf, hip_rzb, 0.0, 0.0, 2.4),
        RingKey(fig.y_crotch, hip_rx * 0.9, hip_rzf * 0.88, hip_rzb * 0.86, 0.0, 0.0, 2.2),
    ]
    bumps = []
    if b.belly > 0.0:
        def belly(alpha: float, y: float, _b=b.belly, _k=k, _y=fig.y_waist + 0.08 * T, _T=T) -> float:
            return 4.2 * _k * _b * gauss(y, _y, 0.22 * _T) * gauss(wrap180(alpha), 0.0, 55.0)
        bumps.append(belly)
    if female and b.bust > 0.0:
        def bust(alpha: float, y: float, _b=b.bust, _k=k, _y=fig.y_chest + 0.05 * T, _T=T) -> float:
            al = wrap180(alpha)
            return 3.0 * _k * _b * gauss(y, _y, 0.085 * _T) * (gauss(al, 30.0, 22.0) + gauss(al, -30.0, 22.0))
        bumps.append(bust)
    fig.torso = Loft(torso_keys, bumps)

    # ---- neck and head -----------------------------------------------------------------
    fig.skull = skull_loft(fig.model)
    fig.head = head_loft(fig.model)
    base = RingKey(y_nb + 1.5 * k, neck_r * 1.04, neck_r, neck_r * 1.2, 0.0, -0.05 * hh, 2.0)
    if fig.model.neck_f is None:
        top = RingKey(chin - 0.3 * hh, neck_r * 0.92, neck_r * 0.85, neck_r * 1.2, 0.0, -0.05 * hh, 2.0)
    else:
        # The neck goes INTO the head: its top ring sits inside the head's
        # ring where it enters, so from every side the head covers its end.
        y_t = fig.fy(fig.model.neck_f)
        hr = fig.skull.section(y_t)
        top = RingKey(y_t, min(neck_r * 0.95, 0.82 * hr.rx), min(neck_r * 0.9, 0.75 * hr.rzf), min(neck_r * 1.25, 0.85 * hr.rzb), 0.0,
                      hr.cz - 0.1 * hr.rzb, 2.0)
    mid = RingKey((top.y + base.y) / 2, (top.rx + base.rx) / 2 * 1.02, (top.rzf + base.rzf) / 2, (top.rzb + base.rzb) / 2, 0.0,
                  (top.cz + base.cz) / 2, 2.0)
    fig.neck = Loft([top, mid, base])
    fig.neck_top = top

    # ---- limbs --------------------------------------------------------------------------
    ma = 1.0 if female else 1.07
    ar, lr = P.arm_r, P.leg_r
    fig.arm_r = (4.5 * k * limbs * ma * ar[0], 3.5 * k * limbs * ma * ar[1], 2.5 * k * limbs * ma * ar[2])
    fig.leg_r = (7.4 * k * limbs * (1.04 if female else 1.0) * lr[0], 4.8 * k * limbs * lr[1], 5.1 * k * limbs * lr[2], 3.3 * k * limbs * lr[3])
    ua = 0.172 * H * b.arms * P.arms
    fa = 0.150 * H * b.arms * P.arms
    hand = 0.104 * H
    ankle_h = 0.045 * H
    hip_l = 8.4 * k * b.hips * (1.05 if female else 1.0)
    foot = 0.15 * H * P.foot[0]
    j: Dict[str, Vec3] = {
        "waist": (0.0, fig.y_waist, 0.0),
        # The head turns about where it meets the neck: under the jaw for a
        # human, the centre of the neck's top for a head the neck goes into.
        "neck": (0.0, chin - 0.06 * hh, -0.12 * hh) if fig.model.neck_f is None else (0.0, fig.neck_top.y, fig.neck_top.cz),
        "neck_base": (0.0, y_nb, -1.0 * k),
    }
    for side, sgn in (("right", -1.0), ("left", 1.0)):
        S = (sgn * sh_hw, y_sh + 2.6 * k, -0.6 * k)
        # The rest arm is bent a little in EVERY view: back and then forward
        # (seen from the side), out and then in (seen from the front). A
        # straight arm leaves the IK no elbow to bend.
        splay = math.radians(P.arm_splay + 3.0 * (b.belly + max(0.0, b.hips - 1.0)))
        du = norm3((sgn * math.sin(splay), 1.0, -0.09))
        E = add3(S, scale3(du, ua))
        df = norm3((sgn * math.sin(math.radians(-4.0)), 1.0, 0.42))
        W = add3(E, scale3(df, fa))
        dh = norm3((sgn * -0.04, 1.0, 0.34))
        Hp = (sgn * hip_l, y_hip, 0.3 * k)
        A = (sgn * (hip_l + 0.8 * k), -ankle_h, -0.6 * k)
        knee_y = -(ankle_h + 0.53 * (hip_h - ankle_h))
        K = ((Hp[0] + A[0]) / 2.0, knee_y, 1.6 * k)
        j.update({
            f"{side}_shoulder": S, f"{side}_elbow": E, f"{side}_wrist": W, f"{side}_handtip": add3(W, scale3(dh, hand)),
            f"{side}_hip": Hp, f"{side}_knee": K, f"{side}_ankle": A, f"{side}_toe": (A[0], 0.0, A[2] + foot * 0.7),
        })
    fig.joints = j
    return fig


__all__ = ["Figure", "build"]
