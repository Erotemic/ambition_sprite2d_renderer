"""Shared drawing helpers for the side-view birds (the chicken, the owl).

⚠ REFERENCE, NOT AUTHORITY, like the scripts that use it (see ``README.md``).

A bird drawn with this kit has the joints ``rigbuild.bird`` reads: ``body``,
``neck``, ``beak_tip``, ``jaw``, ``tail1``, ``tail2``, ``tail_tip`` and, per
side, ``shoulder``, ``wrist``, ``wingtip``, ``hip``, ``knee`` and ``ankle``.
Its wing is a swap set: folded on the body (``wing.folded``) or spread in two
bones (``wing.open``).
"""
from __future__ import annotations

import math
from typing import Dict, Sequence, Tuple

import svgkit as svg
from svgkit import clipped, ellipse, line, part, path, smooth

Point = Tuple[float, float]


def outlined(sil, fill, items=(), cid=None, width=None):
    """A filled silhouette with shading clipped inside it and an ink edge."""
    body = [path(sil, fill)]
    if items:
        body = clipped(cid, sil, [path(sil, fill)] + list(items))
    return body + [path(sil, "none", svg.INK, width or 2 * svg.OW)]


def feather(base, angle, length, width, fill, tip=None, rib=None, sw=1.2, tip_frac=0.38):
    """One long feather from ``base`` toward ``angle`` (degrees, y down), with
    a ``tip`` colour over its last ``tip_frac`` and a ``rib`` down its middle."""
    a = math.radians(angle)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    bx, by = base

    def at(t, w):
        return (bx + ux * length * t + nx * w, by + uy * length * t + ny * w)

    pts = [at(0.0, width * 0.45), at(0.5, width * 0.55), at(0.9, width * 0.35), at(1.0, 0.0) + (True,),
           at(0.9, -width * 0.35), at(0.5, -width * 0.55), at(0.0, -width * 0.45)]
    out = [path(smooth(pts), fill, svg.INK, sw)]
    if tip:
        t0 = 1.0 - tip_frac
        tp = [at(t0, width * 0.52), at(0.9, width * 0.35), at(1.0, 0.0) + (True,), at(0.9, -width * 0.35),
              at(t0, -width * 0.52)]
        out.append(path(smooth(tp), tip))
        out.append(path(smooth(pts), "none", svg.INK, sw))
    if rib:
        out.append(line([at(0.05, 0.0), at(0.92, 0.0)], rib, 0.8))
    return out


def open_wing(J: Dict[str, Point], side: str, z: float, pal: Dict[str, str], *, secondaries: int = 6,
              sec_len: float = 70.0, sec_w: float = 22.0, primaries: int = 6, prim_w: float = 21.0,
              prim_spread: float = 7.5, prim_reach: float = 1.12) -> None:
    """The spread wing, drawn raised up and back: the arm (shoulder to wrist)
    with its coverts over a row of secondaries, and the hand (wrist to tip)
    with the fanned primaries. ``pal`` names ``arm``, ``arm_shade``,
    ``covert``, ``sec``, ``sec_tip``, ``prim``, ``prim_tip`` and ``rib``."""
    sh, wr, tip = J[f"{side}_shoulder"], J[f"{side}_wrist"], J[f"{side}_wingtip"]

    def lerp(a, b, u):
        return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)

    items = []
    for k in range(secondaries):
        u = k / max(1, secondaries - 1)
        base = lerp((wr[0] - 10, wr[1] + 16), (sh[0] - 30, sh[1] + 2), u)
        items += feather(base, 214.0 - 40.0 * u, sec_len - 14.0 * u, sec_w, pal["sec"], pal["sec_tip"], pal["rib"], sw=1.1)
    arm = smooth([(sh[0] + 4, sh[1] + 8), (sh[0] + 14, sh[1] - 44), (wr[0] + 12, wr[1] + 2), wr + (True,),
                  (wr[0] - 22, wr[1] + 26), (sh[0] - 40, sh[1] - 2), (sh[0] - 22, sh[1] + 16)])
    bands = [
        path(smooth([(wr[0] - 6, wr[1] + 14), (sh[0] - 6, sh[1] - 22), (sh[0] - 10, sh[1] + 4),
                     (sh[0] - 42, sh[1] + 2), (wr[0] - 24, wr[1] + 30)]), pal["covert"]),
        line([(sh[0] - 4, sh[1] - 8), (sh[0] - 6, sh[1] - 34), (wr[0] + 0, wr[1] + 18)], pal["arm_shade"], 1.0),
        line([(sh[0] - 18, sh[1] - 2), (sh[0] - 18, sh[1] - 26), (wr[0] - 12, wr[1] + 24)], pal["arm_shade"], 1.0),
    ]
    items += outlined(arm, pal["arm"], bands, f"clip-{side}-arm")
    part(f"{side}-wing-arm", f"Wing Arm - {side}", f"{side}_wing_arm", f"{side}_wing", z + 1, items,
         ' data-rig-opacity="wing.open"')
    hand = []
    ang0 = math.degrees(math.atan2(tip[1] - wr[1], tip[0] - wr[0]))
    reach = math.hypot(tip[0] - wr[0], tip[1] - wr[1])
    for k in range(primaries - 1, -1, -1):
        base = (wr[0] - 3.0 * k, wr[1] + 5.0 * k)
        hand += feather(base, ang0 - 4.0 + prim_spread * k, reach * (prim_reach - 0.07 * k), prim_w, pal["prim"],
                        pal["prim_tip"], pal["rib"])
    hand += outlined(smooth([(wr[0] + 8, wr[1] + 4), (wr[0] - 4, wr[1] - 12), (wr[0] - 30, wr[1] - 20),
                             (wr[0] - 34, wr[1] - 6), (wr[0] - 18, wr[1] + 16)]), pal["arm"],
                     [line([(wr[0] - 2, wr[1] - 4), (wr[0] - 26, wr[1] - 10)], pal["arm_shade"], 1.4)],
                     f"clip-{side}-alula")
    part(f"{side}-wing-hand", f"Wing Hand - {side}", f"{side}_wing_hand", f"{side}_hand", z, hand,
         ' data-rig-opacity="wing.open"')


def legs(J: Dict[str, Point], side: str, z: float, *, thigh: str, thigh_shade: str, shank: str, shank_dark: str,
         claw: str, toes: Sequence[Tuple[float, float]], thigh_r: Tuple[float, float] = (14.0, 10.0),
         shank_r: Tuple[float, float] = (6.0, 5.0), toe_r: Tuple[float, float] = (4.0, 3.0),
         claw_len: float = 4.0) -> None:
    """A feathered thigh, a scaled shank and a foot whose ``toes`` are offsets
    from the ankle."""
    hip, knee, ankle = J[f"{side}_hip"], J[f"{side}_knee"], J[f"{side}_ankle"]
    sil = svg.capsule(hip, knee, *thigh_r)
    part(f"{side}-leg-u", f"Thigh - {side}", f"{side}_leg_u", f"{side}_leg_u", z - 14 if side == "near" else z,
         outlined(sil, thigh, [line([(hip[0] - 6, hip[1] + 4), (knee[0] - 4, knee[1] - 2)], thigh_shade, 1.0)],
                  f"clip-{side}-thigh"))
    sil = svg.capsule(knee, ankle, *shank_r)
    scales = [line([(knee[0] - 5 + 0.2 * k, knee[1] + 4 + 4 * k), (knee[0] + 5 + 0.2 * k, knee[1] + 3 + 4 * k)],
                   shank_dark, 0.9) for k in range(4)]
    part(f"{side}-leg-l", f"Shank - {side}", f"{side}_leg_l", f"{side}_leg_l", z,
         outlined(sil, shank, scales, f"clip-{side}-shank"))
    ax, ay = ankle
    foot = []
    for dx, dy in toes:
        foot += outlined(svg.capsule((ax, ay), (ax + dx, ay + dy), *toe_r), shank)
        s = 1.0 if dx > 0 else -1.0
        foot.append(path(smooth([(ax + dx - s * 1, ay + dy - 2), (ax + dx + s * claw_len, ay + dy + 1),
                                 (ax + dx + s * 1, ay + dy + claw_len + 1)], closed=False), "none", claw, 2.0))
    part(f"{side}-foot", f"Foot - {side}", f"{side}_foot", f"{side}_foot", z + 2, foot)


def eye_states(prefix: str, bone: str, z: float, states: Dict[str, list]) -> None:
    """The eye swap set: ``states`` maps ``open`` / ``angry`` / ``shut`` /
    ``dead`` to what each draws."""
    for name, items in states.items():
        extra = f' data-rig-opacity="eye.{name}"' + (' data-rig-default="1"' if name == "open" else "")
        part(f"{prefix}-{name}", f"Eye - {name.title()}", f"{prefix.replace('-', '_')}_{name}", bone, z, items, extra)


__all__ = ("ellipse", "eye_states", "feather", "legs", "line", "open_wing", "outlined", "part", "path", "smooth")
